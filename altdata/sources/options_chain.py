"""
Option chain fetcher (yfinance).

Pulls the full listed option chain -- every expiry, calls and puts -- for the
options universe and writes one raw CSV snapshot per symbol, plus a data-quality
manifest describing what arrived.

Why raw-first: the GEX computation downstream is a *model*, and models get
revised. Keeping the untouched chain means every past snapshot can be recomputed
under a new convention without re-fetching data that no longer exists. Chains
are not retrievable historically from yfinance, so a missed night is gone.

What yfinance does and does not give:
    gives     strike, bid/ask/last, volume, openInterest, impliedVolatility,
              inTheMoney, contractSymbol, per expiry, calls and puts separately
    does NOT  any greeks. Gamma is computed downstream from the chain's own IV
              (see tools/exposure_compute.py). The quality manifest records this as
              greeks_present=False rather than leaving it implicit.

Known coverage gap: yfinance has no SPX index options. The universe is built
from ETF proxies (SPY/QQQ/IWM) for that reason; Part B evaluates vendors that
would close it.

Failure philosophy matches the rest of the repo: one bad expiry never kills a
symbol, one bad symbol never kills the run. Everything degrades into the
quality manifest.

Usage:
    python -m altdata.sources.options_chain                  # full universe
    python -m altdata.sources.options_chain --symbols SPY QQQ
    python -m altdata.sources.options_chain --max-expiries 12
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import sys
import time
from pathlib import Path
from typing import Optional

from .. import config
from .. import session

log = logging.getLogger(__name__)

PACING_SECONDS = 0.25          # be polite; a busy symbol has 40+ expiries
SNAPSHOT_FMT = "%H%M%SZ"

# Columns kept from the yfinance frame, in written order.
CHAIN_COLUMNS = [
    "symbol", "fetched_at", "spot", "expiry", "dte", "right", "strike",
    "bid", "ask", "last_price", "volume", "open_interest", "implied_vol",
    "in_the_money", "contract_symbol", "last_trade_date",
]


def _spot_for(ticker) -> Optional[float]:
    """Last price. fast_info first, history as fallback -- fast_info is
    occasionally empty for thin names."""
    try:
        fi = getattr(ticker, "fast_info", None)
        if fi:
            for key in ("last_price", "lastPrice", "regularMarketPrice"):
                try:
                    v = fi[key] if not hasattr(fi, "get") else fi.get(key)
                except Exception:
                    v = None
                if v:
                    return float(v)
    except Exception:
        pass
    try:
        h = ticker.history(period="5d", interval="1d")
        if h is not None and not h.empty:
            return float(h["Close"].dropna().iloc[-1])
    except Exception:
        log.warning("  no spot available")
    return None


def _frame_to_rows(df, symbol: str, fetched_at: str, spot: Optional[float],
                   expiry: str, dte: int, right: str) -> list[dict]:
    """Normalise one yfinance calls/puts frame into plain dicts."""
    rows = []
    if df is None or df.empty:
        return rows
    for rec in df.to_dict("records"):
        def num(key):
            v = rec.get(key)
            try:
                f = float(v)
                return None if f != f else f      # drop NaN
            except (TypeError, ValueError):
                return None
        rows.append({
            "symbol": symbol,
            "fetched_at": fetched_at,
            "spot": spot,
            "expiry": expiry,
            "dte": dte,
            "right": right,
            "strike": num("strike"),
            "bid": num("bid"),
            "ask": num("ask"),
            "last_price": num("lastPrice"),
            "volume": num("volume"),
            "open_interest": num("openInterest"),
            "implied_vol": num("impliedVolatility"),
            "in_the_money": bool(rec.get("inTheMoney")) if rec.get("inTheMoney") is not None else None,
            "contract_symbol": rec.get("contractSymbol"),
            # Feeds the IV solver's staleness gate; absent on chains captured
            # before this column existed, which degrades to "age unknown".
            "last_trade_date": (str(rec.get("lastTradeDate"))
                                if rec.get("lastTradeDate") is not None else None),
        })
    return rows


def _expiry_quality(rows: list[dict]) -> dict:
    """Per-expiry data-quality note. This is the record of what the free feed
    actually delivered on the night, which is what makes a stale or thin
    snapshot detectable later instead of silently skewing a computation."""
    n = len(rows)
    if not n:
        return {"rows": 0, "usable": False, "reason": "no rows"}
    oi_present = sum(1 for r in rows if r["open_interest"] is not None)
    oi_nonzero = sum(1 for r in rows if (r["open_interest"] or 0) > 0)
    iv_present = sum(1 for r in rows if r["implied_vol"] is not None)
    iv_sane = sum(1 for r in rows
                  if r["implied_vol"] is not None and 0.0 < r["implied_vol"] < 5.0)
    return {
        "rows": n,
        "calls": sum(1 for r in rows if r["right"] == "C"),
        "puts": sum(1 for r in rows if r["right"] == "P"),
        "oi_present_frac": round(oi_present / n, 4),
        "oi_nonzero_frac": round(oi_nonzero / n, 4),
        "iv_present_frac": round(iv_present / n, 4),
        "iv_sane_frac": round(iv_sane / n, 4),
        "greeks_present": False,          # yfinance never ships greeks
        "gamma_source": "computed_bs_from_iv",
        # Usable for GEX only if there is OI to weight and IV to imply gamma.
        "usable": oi_nonzero > 0 and iv_sane > 0,
    }


def fetch_symbol(symbol: str, max_expiries: Optional[int] = None) -> tuple[list[dict], dict]:
    """Fetch every listed expiry for one symbol.

    Returns (rows, manifest). Never raises -- a total failure returns an empty
    row list and a manifest saying why.
    """
    import yfinance as yf   # lazy, same pattern as yfinance_source

    fetched_at = session.utc_iso()
    manifest: dict = {
        "symbol": symbol,
        "fetched_at": fetched_at,
        "source": "yfinance",
        "spot": None,
        "expiries": {},
        "errors": [],
    }
    rows: list[dict] = []

    try:
        t = yf.Ticker(symbol)
        spot = _spot_for(t)
        manifest["spot"] = spot
        expiries = list(t.options or [])
    except Exception as e:  # noqa: BLE001
        manifest["errors"].append(f"ticker init failed: {type(e).__name__}: {e}")
        log.warning("%s: ticker init failed: %s", symbol, e)
        return rows, manifest

    if not expiries:
        manifest["errors"].append("no expiries listed")
        log.warning("%s: no expiries listed", symbol)
        return rows, manifest

    manifest["expiries_listed"] = len(expiries)
    if max_expiries:
        expiries = expiries[:max_expiries]
    manifest["expiries_fetched"] = len(expiries)

    today = session.session_date_obj()
    for exp in expiries:
        try:
            exp_date = dt.date.fromisoformat(exp)
            dte = (exp_date - today).days
        except ValueError:
            dte = -1
        try:
            chain = t.option_chain(exp)
            exp_rows = (_frame_to_rows(chain.calls, symbol, fetched_at, spot, exp, dte, "C")
                        + _frame_to_rows(chain.puts, symbol, fetched_at, spot, exp, dte, "P"))
            rows.extend(exp_rows)
            manifest["expiries"][exp] = {"dte": dte, **_expiry_quality(exp_rows)}
        except Exception as e:  # noqa: BLE001 -- one bad expiry is not fatal
            manifest["expiries"][exp] = {"dte": dte, "rows": 0, "usable": False,
                                         "reason": f"{type(e).__name__}: {e}"}
            manifest["errors"].append(f"{exp}: {type(e).__name__}: {e}")
            log.warning("  %s %s failed: %s", symbol, exp, e)
        time.sleep(PACING_SECONDS)

    usable = sum(1 for q in manifest["expiries"].values() if q.get("usable"))
    manifest["expiries_usable"] = usable
    manifest["total_rows"] = len(rows)
    return rows, manifest


def write_snapshot(symbol: str, rows: list[dict], manifest: dict,
                   base_dir: Optional[str] = None) -> tuple[Optional[Path], Path]:
    """Write one symbol's raw chain + quality manifest. Returns (csv, json)."""
    import csv as csvmod

    day_dir = Path(base_dir or config.CHAIN_DIR) / session.session_date()
    day_dir.mkdir(parents=True, exist_ok=True)
    tag = f"{symbol}_{session.utc_stamp(SNAPSHOT_FMT)}"

    csv_path: Optional[Path] = None
    if rows:
        csv_path = day_dir / f"{tag}.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as fp:
            w = csvmod.DictWriter(fp, fieldnames=CHAIN_COLUMNS)
            w.writeheader()
            w.writerows(rows)

    json_path = day_dir / f"{tag}_quality.json"
    json_path.write_text(json.dumps(manifest, indent=2, default=str),
                         encoding="utf-8")
    return csv_path, json_path


def pull(symbols: Optional[list[str]] = None,
         max_expiries: Optional[int] = None,
         base_dir: Optional[str] = None) -> dict:
    """Snapshot the whole universe. Returns a run summary."""
    universe = symbols or config.options_universe()
    summary: dict = {"total": len(universe), "success": 0, "failed": [],
                     "symbols": {}}

    for i, sym in enumerate(universe, 1):
        log.info("[%d/%d] %s", i, len(universe), sym)
        rows, manifest = fetch_symbol(sym, max_expiries=max_expiries)
        csv_path, json_path = write_snapshot(sym, rows, manifest, base_dir)
        entry = {
            "rows": len(rows),
            "expiries_listed": manifest.get("expiries_listed", 0),
            "expiries_fetched": manifest.get("expiries_fetched", 0),
            "expiries_usable": manifest.get("expiries_usable", 0),
            "spot": manifest.get("spot"),
            "csv": str(csv_path) if csv_path else None,
            "quality": str(json_path),
            "errors": len(manifest.get("errors", [])),
        }
        summary["symbols"][sym] = entry
        if rows:
            summary["success"] += 1
            log.info("  %s: %d rows, %d/%d expiries usable, spot=%s",
                     sym, len(rows), entry["expiries_usable"],
                     entry["expiries_fetched"], entry["spot"])
        else:
            summary["failed"].append((sym, "; ".join(manifest.get("errors", []))[:200]))
            log.warning("  %s: no rows", sym)
    return summary


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch option chains via yfinance")
    ap.add_argument("--symbols", nargs="*", help="Override the configured universe")
    ap.add_argument("--max-expiries", type=int, default=None,
                    help="Cap expiries per symbol (default: all listed)")
    ap.add_argument("--base-dir", default=None, help="Override data/chains")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    s = pull(symbols=args.symbols, max_expiries=args.max_expiries,
             base_dir=args.base_dir)
    print(f"\nChains captured: {s['success']}/{s['total']} symbols")
    for sym, e in s["symbols"].items():
        print(f"  {sym:6} {e['rows']:>7,} rows  "
              f"{e['expiries_usable']:>3}/{e['expiries_fetched']:<3} usable expiries  "
              f"spot={e['spot']}")
    if s["failed"]:
        print(f"  failed: {[f[0] for f in s['failed']]}")
    return 0 if s["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
