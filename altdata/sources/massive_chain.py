"""
Option chain fetcher (Massive, ex-Polygon) -- the symbols yfinance cannot serve.

yfinance has no SPX index options and no SPCX, so those two have sat in
config.PENDING_VENDOR_SYMBOLS since the universe was built. This closes that
gap for INGESTION ONLY. It writes chains in exactly the schema
altdata.sources.options_chain writes, into the same directory, so everything
downstream reads them without knowing which vendor produced them.

-----------------------------------------------------------------------------
WHY INGESTION ONLY, AND WHY THAT IS STILL URGENT
-----------------------------------------------------------------------------

The capability probe (5 Sep) established what Massive Starter serves for index
underlyings, near the money, 250 contracts sampled:

    open_interest   250/250     served
    implied_vol       0/250     NOT served
    greeks            0/250     NOT served
    I:SPX level         403     not entitled

So every Greek for these symbols would have to come from solved IV, and
tools/validate_iv_solver.py currently reports FAIL. Its verdict line -- written
before any of this -- reads "SPX stays out until the failing checks are
resolved". Computing SPX gamma today would mean overriding a gate the repo
already declared. So every row this module writes carries

    greeks_status = pending_solver_gate

and exposure_compute REFUSES such rows rather than quietly computing anyway.
The deferral lives in the data, not only in a TODO entry.

Ingestion cannot wait for the same reason the yfinance chains cannot: the probe
also established that Massive serves open interest from the LIVE SNAPSHOT ONLY.
Bars go back two years; OI has no history at all -- `?date=` is ignored, the
daily aggregates carry no OI field, and the point-in-time contract reference
returns terms without it. Every day not captured is a day of SPX open interest
that no subscription will ever sell back. Bars can wait; OI cannot. Greeks can
be recomputed from stored chains the day the gate goes green.

-----------------------------------------------------------------------------
THREE THINGS THIS HAS TO GET RIGHT THAT THE YFINANCE PATH DOES NOT
-----------------------------------------------------------------------------

SPOT WITHOUT AN INDEX ENTITLEMENT. `I:SPX` aggregates are 403, and the option
snapshot's `underlying_asset` carries a ticker but no price. The chain does not
need one: put-call parity recovers the forward from the option prices
themselves, which iv_solver.implied_forward already does, and discounting that
forward gives a usable spot. `spot_source` records which path was taken so a
parity-derived spot is never mistaken for a printed index level.

SPCX IS A REUSED TICKER. Reference data returns SPCX contracts expiring
2021-01-15 and 2026-01-16 at strikes 16-35. Those belong to the PREVIOUS SPCX,
a SPAC/new-issue ETF; the current underlying is Space Exploration Technologies
Corp Class A, listed 2026-06-12, whose options first traded 2026-06-16 and
trade at 70-145+. A date-ranged query blends two unrelated companies under one
symbol. Every SPCX row therefore carries `underlying_verified_from` and any
contract expiring before that fence is dropped, counted, and named in the
manifest rather than silently mixed in.

AN EMPTY SUCCESS IS NOT A FAILURE ON A NON-SESSION DAY. The probe asked for
SPY's close on 2026-06-19 and got HTTP 200 with zero bars -- Juneteenth. The
vendor returns market holidays as empty successes, so "no data" has to be
distinguished from "no market" before anything alarms. altdata.session already
owns the NYSE calendar; this asks it rather than guessing from the shape of the
response.

Usage:
    python -m altdata.sources.massive_chain                 # SPX + SPCX
    python -m altdata.sources.massive_chain --symbols SPX
"""

from __future__ import annotations

import argparse
import csv as csvmod
import datetime as dt
import json
import logging
import math
import os
import sys
import time
from pathlib import Path
from typing import Optional

from .. import config
from .. import session
from .options_chain import CHAIN_COLUMNS, _expiry_quality

log = logging.getLogger(__name__)

DEFAULT_BASE = "https://api.massive.com"
SNAPSHOT_PATH = "/v3/snapshot/options/{underlying}"
PREV_CLOSE_PATH = "/v2/aggs/ticker/{ticker}/prev"
PAGE_LIMIT = 250                 # the vendor's maximum per page
PACING_SECONDS = 0.2             # Starter is unlimited; be polite anyway
MAX_PAGES = 400                  # 100k contracts; a runaway cursor stops here
TIMEOUT = 30
SNAPSHOT_FMT = "%H%M%SZ"

# Written on every row this module produces. exposure_compute refuses to
# compute Greeks for a chain carrying it -- see the module docstring.
GREEKS_STATUS = "pending_solver_gate"

# Appended to the shared chain schema. Append-only, exactly as everywhere else:
# the yfinance path writes CHAIN_COLUMNS and stops, and a reader that knows
# only those columns still parses these files.
MASSIVE_CHAIN_COLUMNS = CHAIN_COLUMNS + [
    "greeks_status", "spot_source", "underlying_verified_from", "vendor",
]

_SECRETS: list[str] = []


def _redact(text: str) -> str:
    for s in _SECRETS:
        if s:
            text = text.replace(s, "***REDACTED***")
    return text


def credentials() -> tuple[Optional[str], str]:
    """Key and base URL from the environment, falling back to .env.

    Deliberately NOT imported from tools/probe_massive.py: altdata is the
    library and tools/ are scripts that consume it, so the dependency would
    point the wrong way. The duplication is ten lines and keeps the layering
    honest.
    """
    env: dict[str, str] = {}
    dotenv = Path(__file__).resolve().parents[2] / ".env"
    if dotenv.exists():
        for line in dotenv.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    key = os.environ.get("MASSIVE_API_KEY") or env.get("MASSIVE_API_KEY")
    base = (os.environ.get("MASSIVE_BASE_URL") or env.get("MASSIVE_BASE_URL")
            or DEFAULT_BASE).rstrip("/")
    if key and key != "PLACEHOLDER":
        _SECRETS.append(key)
        return key, base
    return None, base


def _get(url: str, key: str, params: Optional[dict] = None) -> dict:
    """One request. Never raises; a dead call becomes a recorded error."""
    import requests

    out: dict = {"url": _redact(url), "status": None, "body": None}
    try:
        r = requests.get(url, headers={"Authorization": f"Bearer {key}",
                                       "Accept": "application/json"},
                         params=params, timeout=TIMEOUT)
        out["status"] = r.status_code
        if r.status_code == 429:
            wait = float(r.headers.get("Retry-After") or 20)
            log.warning("  429 -- waiting %.0fs", wait)
            time.sleep(wait)
            r = requests.get(url, headers={"Authorization": f"Bearer {key}",
                                           "Accept": "application/json"},
                             params=params, timeout=TIMEOUT)
            out["status"] = r.status_code
        try:
            out["body"] = r.json()
        except ValueError:
            out["body"] = {"__non_json__": r.text[:500]}
    except Exception as e:  # noqa: BLE001 -- a dead call is data, not a crash
        out["error"] = f"{type(e).__name__}: {e}"
    return out


def empty_is_expected(day: Optional[str] = None) -> tuple[bool, str]:
    """Is an empty-but-successful response explained by the market being shut?

    The vendor returns holidays as HTTP 200 with no rows, so without this an
    NYSE holiday looks exactly like a broken fetch. altdata.session owns the
    calendar; this does not keep a second copy of it.
    """
    if session.is_trading_session(day):
        return False, "session day -- an empty response is a fault"
    return True, session.session_reason(day)


def _num(v) -> Optional[float]:
    try:
        f = float(v)
        return None if f != f else f
    except (TypeError, ValueError):
        return None


def fetch_snapshot(symbol: str, key: str, base: str,
                   max_pages: int = MAX_PAGES) -> tuple[list[dict], dict]:
    """Every contract in one underlying's snapshot, following next_url.

    The vendor caps a page at 250 and hands back a cursor; SPX runs to tens of
    thousands of contracts, so paging is not optional. max_pages bounds a
    cursor that never terminates -- an infinite loop against a paid API is a
    worse failure than a truncated capture, and the manifest records when the
    cap was hit so a truncation is never silent.
    """
    url = f"{base}{SNAPSHOT_PATH.format(underlying=symbol)}"
    params: Optional[dict] = {"limit": PAGE_LIMIT}
    results: list[dict] = []
    info: dict = {"pages": 0, "truncated": False, "errors": []}

    for page in range(max_pages):
        res = _get(url, key, params)
        info["pages"] = page + 1
        body = res.get("body") or {}
        if res.get("status") != 200:
            msg = (body.get("message") if isinstance(body, dict) else None) or res.get("error")
            info["errors"].append(f"page {page + 1}: HTTP {res.get('status')} {msg}")
            break
        batch = body.get("results") or []
        results.extend(r for r in batch if isinstance(r, dict))
        nxt = body.get("next_url")
        if not nxt or not batch:
            break
        # next_url already carries the cursor; passing params again would
        # re-send limit and, on some builds, reset the cursor.
        url, params = nxt, None
        time.sleep(PACING_SECONDS)
    else:
        info["truncated"] = True
        info["errors"].append(f"stopped at the {max_pages}-page cap")
    return results, info


def parity_forward(rows: list[dict], t_years: float, r: float) -> Optional[dict]:
    """Forward from put-call parity, via the shared IV-solver implementation.

    Imported lazily and from tools/ because that is where iv_solver lives; if
    it cannot be imported the caller falls back rather than failing the fetch.
    """
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
        import iv_solver  # noqa: PLC0415
        return iv_solver.implied_forward(rows, t_years, r)
    except Exception:  # noqa: BLE001
        return None


def derive_spot(rows: list[dict], r: float) -> tuple[Optional[float], str]:
    """Spot for an underlying whose level this tier will not sell us.

    Uses the nearest expiry that has enough two-sided strikes for parity, and
    discounts its forward back to today: S = F x exp(-rT), no dividend yield,
    the same q = 0 simplification the Greeks already make.

    Returns (spot, spot_source). The source string matters more than usual
    here: a parity-derived spot is an inference from option prices, not a
    printed index level, and anything reading it downstream is entitled to
    know that.
    """
    by_expiry: dict[str, list[dict]] = {}
    for row in rows:
        by_expiry.setdefault(row.get("expiry"), []).append(row)
    for expiry in sorted(x for x in by_expiry if x):
        erows = by_expiry[expiry]
        dte = max(erows[0].get("dte") or 0, 0)
        t = max(dte / 365.0, 1.0 / (365.0 * 24.0))
        fwd = parity_forward(erows, t, r)
        if fwd and fwd.get("forward"):
            spot = fwd["forward"] * math.exp(-r * t)
            return round(spot, 4), f"parity_forward_discounted:{expiry}"
    return None, "unavailable"


def equity_prev_close(symbol: str, key: str, base: str) -> tuple[Optional[float], str]:
    """Previous close for an equity underlying, which this tier does serve."""
    res = _get(f"{base}{PREV_CLOSE_PATH.format(ticker=symbol)}", key,
               {"adjusted": "true"})
    body = res.get("body") or {}
    rows = body.get("results") or []
    if res.get("status") == 200 and rows:
        return _num(rows[0].get("c")), "vendor_prev_close"
    return None, "unavailable"


def _to_rows(results: list[dict], symbol: str, fetched_at: str,
             today: dt.date, verified_from: Optional[str]) -> tuple[list[dict], dict]:
    """Vendor snapshot records -> the shared chain schema.

    Applies the SPCX reuse fence: a contract expiring before `verified_from`
    cannot belong to the current underlying, so it is dropped and counted.
    """
    rows: list[dict] = []
    fenced = 0
    for rec in results:
        det = rec.get("details") or {}
        expiry = det.get("expiration_date")
        if not expiry:
            continue
        if verified_from and expiry < verified_from:
            fenced += 1
            continue
        try:
            dte = (dt.date.fromisoformat(expiry) - today).days
        except ValueError:
            dte = -1
        q = rec.get("last_quote") or {}
        d = rec.get("day") or {}
        ctype = (det.get("contract_type") or "").lower()
        rows.append({
            "symbol": symbol,
            "fetched_at": fetched_at,
            "spot": None,                      # filled once parity resolves it
            "expiry": expiry,
            "dte": dte,
            "right": "C" if ctype.startswith("c") else "P",
            "strike": _num(det.get("strike_price")),
            "bid": _num(q.get("bid")),
            "ask": _num(q.get("ask")),
            "last_price": _num(d.get("close")) if d.get("close") is not None
                          else _num(q.get("midpoint")),
            "volume": _num(d.get("volume")),
            "open_interest": _num(rec.get("open_interest")),
            # Served as null for index underlyings on this tier. Written as
            # empty rather than zero: absent and zero are different facts, and
            # a zero here would be solved into an infinite gamma.
            "implied_vol": _num(rec.get("implied_volatility")),
            "in_the_money": None,
            "contract_symbol": det.get("ticker"),
            "last_trade_date": (d.get("last_updated") or q.get("last_updated")),
            "greeks_status": GREEKS_STATUS,
            "spot_source": None,               # filled below
            "underlying_verified_from": verified_from,
            "vendor": "massive",
        })
    return rows, {"fenced_pre_verification": fenced}


def fetch_symbol(symbol: str, key: str, base: str,
                 max_pages: int = MAX_PAGES) -> tuple[list[dict], dict]:
    """One symbol's full chain plus a quality manifest. Never raises."""
    fetched_at = session.utc_iso()
    verified_from = config.UNDERLYING_VERIFIED_FROM.get(symbol)
    manifest: dict = {
        "symbol": symbol, "fetched_at": fetched_at, "source": "massive",
        "vendor_tier": "starter", "greeks_status": GREEKS_STATUS,
        "greeks_deferred_reason":
            "Massive Starter serves no IV or greeks for index underlyings "
            "(0/250 near the money on the 5 Sep probe); solved IV is gated on "
            "tools/validate_iv_solver.py, which currently FAILS.",
        "underlying_verified_from": verified_from,
        "spot": None, "spot_source": None, "expiries": {}, "errors": [],
    }

    results, info = fetch_snapshot(symbol, key, base, max_pages)
    manifest["pages"] = info["pages"]
    manifest["truncated"] = info["truncated"]
    manifest["errors"].extend(info["errors"])
    manifest["contracts_returned"] = len(results)

    if not results:
        expected, why = empty_is_expected()
        manifest["empty_response"] = True
        manifest["empty_expected"] = expected
        manifest["empty_reason"] = why
        if not expected:
            manifest["errors"].append("empty snapshot on a session day")
        return [], manifest

    today = session.session_date_obj()
    rows, fence = _to_rows(results, symbol, fetched_at, today, verified_from)
    manifest.update(fence)
    if fence["fenced_pre_verification"]:
        log.info("  %s: fenced %d contract(s) expiring before %s (ticker reuse)",
                 symbol, fence["fenced_pre_verification"], verified_from)

    # Spot: an equity has a close we are entitled to; an index does not.
    if config.MASSIVE_SPOT_FROM_PARITY.get(symbol, True):
        spot, src = derive_spot(rows, config.RISK_FREE_RATE)
    else:
        spot, src = equity_prev_close(symbol, key, base)
        if spot is None:
            spot, src = derive_spot(rows, config.RISK_FREE_RATE)
    for row in rows:
        row["spot"], row["spot_source"] = spot, src
    manifest["spot"], manifest["spot_source"] = spot, src

    for expiry in sorted({r["expiry"] for r in rows}):
        erows = [r for r in rows if r["expiry"] == expiry]
        q = _expiry_quality(erows)
        q["greeks_present"] = False
        q["gamma_source"] = "deferred_pending_solver_gate"
        # The shared helper calls a chain usable when it has OI and sane IV.
        # This tier serves no IV for these symbols, so it would call every
        # expiry unusable. For an ingestion-only capture the bar is OI.
        q["usable_for_ingestion"] = sum(1 for r in erows
                                        if (r["open_interest"] or 0) > 0) > 0
        manifest["expiries"][expiry] = {"dte": erows[0]["dte"], **q}

    manifest["expiries_listed"] = len(manifest["expiries"])
    manifest["expiries_fetched"] = len(manifest["expiries"])
    manifest["expiries_usable"] = sum(
        1 for q in manifest["expiries"].values() if q.get("usable_for_ingestion"))
    manifest["total_rows"] = len(rows)
    manifest["oi_nonzero_rows"] = sum(1 for r in rows if (r["open_interest"] or 0) > 0)
    return rows, manifest


def write_snapshot(symbol: str, rows: list[dict], manifest: dict,
                   base_dir: Optional[str] = None) -> tuple[Optional[Path], Path]:
    """Same directory and naming as the yfinance path, wider column set."""
    day_dir = Path(base_dir or config.CHAIN_DIR) / session.session_date()
    day_dir.mkdir(parents=True, exist_ok=True)
    tag = f"{symbol}_{session.utc_stamp(SNAPSHOT_FMT)}"

    csv_path: Optional[Path] = None
    if rows:
        csv_path = day_dir / f"{tag}.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as fp:
            w = csvmod.DictWriter(fp, fieldnames=MASSIVE_CHAIN_COLUMNS,
                                  extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)

    json_path = day_dir / f"{tag}_quality.json"
    json_path.write_text(json.dumps(manifest, indent=2, default=str),
                         encoding="utf-8")
    return csv_path, json_path


def pull(symbols: Optional[list[str]] = None,
         base_dir: Optional[str] = None,
         max_pages: int = MAX_PAGES) -> dict:
    """Snapshot the vendor-only symbols. Returns a run summary."""
    universe = symbols or config.massive_universe()
    summary: dict = {"total": len(universe), "success": 0, "failed": [],
                     "symbols": {}}

    key, base = credentials()
    if not key:
        summary["failed"] = [(s, "MASSIVE_API_KEY unset or PLACEHOLDER")
                             for s in universe]
        log.warning("MASSIVE_API_KEY unset -- vendor symbols not captured")
        return summary

    for i, sym in enumerate(universe, 1):
        log.info("[%d/%d] %s (massive)", i, len(universe), sym)
        rows, manifest = fetch_symbol(sym, key, base, max_pages)
        csv_path, json_path = write_snapshot(sym, rows, manifest, base_dir)
        summary["symbols"][sym] = {
            "rows": len(rows),
            "oi_nonzero_rows": manifest.get("oi_nonzero_rows", 0),
            "expiries_fetched": manifest.get("expiries_fetched", 0),
            "expiries_usable": manifest.get("expiries_usable", 0),
            "spot": manifest.get("spot"), "spot_source": manifest.get("spot_source"),
            "pages": manifest.get("pages"), "truncated": manifest.get("truncated"),
            "fenced": manifest.get("fenced_pre_verification", 0),
            "csv": str(csv_path) if csv_path else None,
            "quality": str(json_path),
            "errors": len(manifest.get("errors", [])),
        }
        if rows:
            summary["success"] += 1
            log.info("  %s: %d rows, %d with OI, %d expiries, spot=%s (%s)",
                     sym, len(rows), manifest.get("oi_nonzero_rows", 0),
                     manifest.get("expiries_fetched", 0),
                     manifest.get("spot"), manifest.get("spot_source"))
        else:
            summary["failed"].append(
                (sym, "; ".join(manifest.get("errors", []))[:200]
                 or manifest.get("empty_reason", "no rows")))
            log.warning("  %s: no rows", sym)
    return summary


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Fetch SPX/SPCX option chains via Massive (ingestion only)")
    ap.add_argument("--symbols", nargs="*")
    ap.add_argument("--base-dir", default=None)
    ap.add_argument("--max-pages", type=int, default=MAX_PAGES)
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s",
                        datefmt="%H:%M:%S")
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    s = pull(symbols=args.symbols, base_dir=args.base_dir,
             max_pages=args.max_pages)
    print(f"\nVendor chains captured: {s['success']}/{s['total']} symbols "
          f"(greeks_status={GREEKS_STATUS})")
    for sym, e in s["symbols"].items():
        print(f"  {sym:6} {e['rows']:>7,} rows  {e['oi_nonzero_rows']:>7,} with OI  "
              f"{e['expiries_fetched']:>3} expiries  {e['pages']:>3} pages  "
              f"spot={e['spot']} ({e['spot_source']})"
              + (f"  fenced={e['fenced']}" if e["fenced"] else "")
              + ("  TRUNCATED" if e["truncated"] else ""))
    if s["failed"]:
        for sym, why in s["failed"]:
            print(f"  FAILED {sym}: {why}")
    return 0 if s["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
