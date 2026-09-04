"""
Per-strike gamma exposure from a raw chain snapshot.

Reads the newest chain CSV per symbol written by altdata.sources.options_chain
and produces the exposure profile the logger records nightly.

SIGN CONVENTION -- read this before trusting any number below.

    Dealers are assumed long calls (+gamma) and short puts (-gamma).

        GEX_strike = gamma_call x OI_call x 100 x spot
                   - gamma_put  x OI_put  x 100 x spot

    This is the standard street convention and it is an *assumption*, not an
    observation. Real dealer inventory is unobservable from public chains: a
    call that a dealer sold looks identical to one they bought. Every output
    carries convention_version and a caveat field so a later reader cannot
    mistake a convention for a measurement. Under the opposite (customer-hand)
    reading, every sign here inverts.

GREEKS. yfinance ships no greeks, so gamma is computed Black-Scholes from the
chain's own implied vol:

    d1    = (ln(S/K) + (r + sigma^2/2) T) / (sigma sqrt(T))
    gamma = phi(d1) / (S sigma sqrt(T))

with r from config.RISK_FREE_RATE. If a future vendor supplies gamma directly,
a `gamma` column in the chain is used as-is and gamma_source records which path
each row took -- no code change needed when the tier changes.

PRIMARY SERIES. `dollar_gamma_per_1pct` is the headline number: the dollar
change in dealer delta for a 1% move in spot, i.e. GEX_strike x spot x 0.01.
Net GEX is reported alongside it in the units of the formula above.

Usage:
    python tools/gex_compute.py                    # newest snapshot, all symbols
    python tools/gex_compute.py --symbols SPY QQQ
    python tools/gex_compute.py --date 2026-09-04
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import logging
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from altdata import config  # noqa: E402

log = logging.getLogger(__name__)

SQRT_2PI = math.sqrt(2.0 * math.pi)
MIN_T = 1.0 / (365.0 * 24.0)     # 1 hour, so 0DTE gamma stays finite
MAX_SANE_IV = 5.0                # 500% vol; above this the quote is garbage


# ---------------------------------------------------------------------------
# Black-Scholes gamma
# ---------------------------------------------------------------------------

def norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / SQRT_2PI


def bs_gamma(spot: float, strike: float, iv: float, t_years: float,
             r: float) -> Optional[float]:
    """Black-Scholes gamma. Identical for calls and puts.

    Returns None when inputs cannot produce a meaningful number rather than
    letting a divide-by-zero or a log of a negative propagate into the profile.
    """
    if not (spot and strike and iv) or spot <= 0 or strike <= 0 or iv <= 0:
        return None
    t = max(t_years, MIN_T)
    denom = iv * math.sqrt(t)
    if denom <= 0:
        return None
    try:
        d1 = (math.log(spot / strike) + (r + 0.5 * iv * iv) * t) / denom
    except ValueError:
        return None
    g = norm_pdf(d1) / (spot * denom)
    return g if math.isfinite(g) else None


# ---------------------------------------------------------------------------
# Expiry bucketing
# ---------------------------------------------------------------------------

def _third_friday(d: dt.date) -> dt.date:
    first = d.replace(day=1)
    # weekday(): Mon=0 .. Fri=4
    offset = (4 - first.weekday()) % 7
    return first + dt.timedelta(days=offset + 14)


def bucket_for(expiry: str, dte: int) -> str:
    """Exactly one bucket per expiry. Order matters and is deliberate:
    0DTE wins over everything, then quarterly, monthly, weekly, then the rest."""
    try:
        d = dt.date.fromisoformat(expiry)
    except ValueError:
        return "other"
    if dte <= 0:
        return "0dte"
    is_third_friday = d == _third_friday(d)
    if is_third_friday and d.month in (3, 6, 9, 12):
        return "quarterly"
    if is_third_friday:
        return "monthly"
    if dte <= 7:
        return "weekly"
    return "other"


BUCKETS = ["0dte", "weekly", "monthly", "quarterly", "other"]


# ---------------------------------------------------------------------------
# Profile construction
# ---------------------------------------------------------------------------

def gamma_flip_all(strike_gex: list[tuple[float, float]]) -> list[float]:
    """Every zero crossing of cumulative GEX, walking strikes upward.

    Linearly interpolated between the bracketing strikes. A real book crosses
    zero more than once: far-OTM strikes carry tiny GEX that oscillates around
    zero, so the *first* crossing is usually noise a long way from spot.
    """
    crossings: list[float] = []
    cum = 0.0
    prev_strike = prev_cum = None
    for strike, gex in sorted(strike_gex):
        cum += gex
        if prev_cum is not None and (prev_cum < 0 <= cum or prev_cum > 0 >= cum):
            span = cum - prev_cum
            crossings.append(strike if span == 0
                             else prev_strike + (-prev_cum / span) * (strike - prev_strike))
        prev_strike, prev_cum = strike, cum
    return crossings


def gamma_flip(strike_gex: list[tuple[float, float]],
               spot: Optional[float] = None) -> Optional[float]:
    """The flip level: the zero crossing nearest spot.

    Returns None when the cumulative curve never changes sign -- a book that
    is positive or negative all the way up has no flip, and inventing one
    would be worse than reporting none.
    """
    crossings = gamma_flip_all(strike_gex)
    if not crossings:
        return None
    if spot is None:
        return crossings[0]
    return min(crossings, key=lambda c: abs(c - spot))


def max_pain(rows: list[dict]) -> Optional[float]:
    """Strike at which total in-the-money payout to option holders is smallest.

    Evaluated at every listed strike: for candidate settle S,
        payout(S) = sum_calls OI x max(0, S - K) + sum_puts OI x max(0, K - S)
    """
    strikes = sorted({r["strike"] for r in rows if r["strike"]})
    if not strikes:
        return None
    best_s, best_pay = None, None
    for s in strikes:
        pay = 0.0
        for r in rows:
            oi, k = r["open_interest"] or 0.0, r["strike"]
            if not oi or not k:
                continue
            if r["right"] == "C" and s > k:
                pay += oi * (s - k)
            elif r["right"] == "P" and k > s:
                pay += oi * (k - s)
        if best_pay is None or pay < best_pay:
            best_s, best_pay = s, pay
    return best_s


def _profile(rows: list[dict], spot: float) -> dict:
    """Aggregate per-strike GEX and the levels derived from it."""
    by_strike: dict[float, float] = defaultdict(float)
    call_gex: dict[float, float] = defaultdict(float)
    put_gex: dict[float, float] = defaultdict(float)

    for r in rows:
        g, oi, k = r.get("gamma"), r.get("open_interest") or 0.0, r.get("strike")
        if g is None or not k or oi <= 0:
            continue
        notional = g * oi * 100.0 * spot
        if r["right"] == "C":
            by_strike[k] += notional          # dealers long calls -> +gamma
            call_gex[k] += notional
        else:
            by_strike[k] -= notional          # dealers short puts -> -gamma
            put_gex[k] += notional

    if not by_strike:
        return {"net_gex": None, "dollar_gamma_per_1pct": None,
                "gamma_flip": None, "call_wall": None, "put_wall": None,
                "strikes": 0}

    pairs = sorted(by_strike.items())
    net = sum(v for _, v in pairs)
    positives = [(k, v) for k, v in pairs if v > 0]
    negatives = [(k, v) for k, v in pairs if v < 0]
    return {
        "net_gex": net,
        "dollar_gamma_per_1pct": net * spot * 0.01,
        "gamma_flip": gamma_flip(pairs, spot),
        "gamma_flip_all": gamma_flip_all(pairs),
        "call_wall": max(positives, key=lambda kv: kv[1])[0] if positives else None,
        "put_wall": min(negatives, key=lambda kv: kv[1])[0] if negatives else None,
        "peak_abs_gex_strike": max(pairs, key=lambda kv: abs(kv[1]))[0],
        "strikes": len(pairs),
        "per_strike": [{"strike": k, "gex": v,
                        "call_gex": call_gex.get(k, 0.0),
                        "put_gex": -put_gex.get(k, 0.0)} for k, v in pairs],
    }


def compute_symbol(rows: list[dict], symbol: str) -> dict:
    """Full computed output for one symbol's chain snapshot."""
    spot = next((r["spot"] for r in rows if r.get("spot")), None)
    fetched_at = next((r["fetched_at"] for r in rows if r.get("fetched_at")), None)

    quality = {"rows_in": len(rows), "gamma_computed": 0, "gamma_supplied": 0,
               "skipped_no_iv": 0, "skipped_insane_iv": 0, "skipped_no_oi": 0}
    if not spot:
        return {"symbol": symbol, "error": "no spot in snapshot", "quality": quality}

    usable: list[dict] = []
    for r in rows:
        oi = r.get("open_interest") or 0.0
        if oi <= 0:
            quality["skipped_no_oi"] += 1
            continue
        # Forward-compatible: a vendor-supplied gamma column wins if present.
        if r.get("gamma") is not None:
            quality["gamma_supplied"] += 1
            usable.append(r)
            continue
        iv = r.get("implied_vol")
        if iv is None or iv <= 0:
            quality["skipped_no_iv"] += 1
            continue
        if iv >= MAX_SANE_IV:
            quality["skipped_insane_iv"] += 1
            continue
        g = bs_gamma(spot, r["strike"], iv, max(r.get("dte") or 0, 0) / 365.0,
                     config.RISK_FREE_RATE)
        if g is None:
            quality["skipped_no_iv"] += 1
            continue
        r = {**r, "gamma": g}
        quality["gamma_computed"] += 1
        usable.append(r)

    overall = _profile(usable, spot)

    buckets: dict[str, dict] = {}
    total_abs = sum(abs(s["gex"]) for s in overall.get("per_strike", [])) or 0.0
    for b in BUCKETS:
        brows = [r for r in usable if bucket_for(r["expiry"], r.get("dte") or 0) == b]
        if not brows:
            continue
        p = _profile(brows, spot)
        b_abs = sum(abs(s["gex"]) for s in p.get("per_strike", []))
        p.pop("per_strike", None)
        p["share_of_total_abs_gex"] = round(b_abs / total_abs, 4) if total_abs else None
        p["expiries"] = sorted({r["expiry"] for r in brows})
        buckets[b] = p

    per_strike = overall.pop("per_strike", [])
    return {
        "symbol": symbol,
        "computed_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "fetched_at": fetched_at,
        "spot": spot,
        "convention_version": config.CONVENTION_VERSION,
        "convention_caveat": config.CONVENTION_CAVEAT,
        "gamma_source": ("vendor" if quality["gamma_supplied"] else "computed_bs_from_iv"),
        "risk_free_rate": config.RISK_FREE_RATE,
        "overall": overall,
        "max_pain": max_pain(usable),
        "buckets": buckets,
        "quality": quality,
        "per_strike": per_strike,
    }


# ---------------------------------------------------------------------------
# Snapshot IO
# ---------------------------------------------------------------------------

def _to_float(v):
    try:
        f = float(v)
        return None if f != f else f
    except (TypeError, ValueError):
        return None


def load_chain(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as fp:
        for rec in csv.DictReader(fp):
            rows.append({
                "symbol": rec.get("symbol"),
                "fetched_at": rec.get("fetched_at"),
                "spot": _to_float(rec.get("spot")),
                "expiry": rec.get("expiry"),
                "dte": int(_to_float(rec.get("dte")) or 0),
                "right": rec.get("right"),
                "strike": _to_float(rec.get("strike")),
                "open_interest": _to_float(rec.get("open_interest")),
                "implied_vol": _to_float(rec.get("implied_vol")),
                "gamma": _to_float(rec.get("gamma")),   # absent today, vendor later
            })
    return rows


def newest_chains(date: Optional[str] = None,
                  symbols: Optional[list[str]] = None,
                  base_dir: Optional[str] = None) -> dict[str, Path]:
    """Newest chain CSV per symbol for a given date (default: latest day dir)."""
    root = Path(base_dir or config.CHAIN_DIR)
    if not root.exists():
        return {}
    days = sorted(p for p in root.iterdir() if p.is_dir())
    if not days:
        return {}
    day = (root / date) if date else days[-1]
    if not day.exists():
        return {}
    out: dict[str, Path] = {}
    for p in sorted(day.glob("*.csv"), key=lambda q: q.stat().st_mtime):
        sym = p.name.split("_")[0]
        if symbols and sym not in symbols:
            continue
        out[sym] = p          # later file wins -> newest snapshot
    return out


def write_computed(result: dict, base_dir: Optional[str] = None) -> Path:
    day = (result.get("computed_at") or "")[:10] or dt.date.today().isoformat()
    out_dir = Path(base_dir or config.COMPUTED_DIR) / day
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%H%M%SZ")
    path = out_dir / f"{result['symbol']}_{stamp}_gex.json"
    path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    return path


def run(symbols: Optional[list[str]] = None, date: Optional[str] = None,
        base_dir: Optional[str] = None, out_dir: Optional[str] = None) -> dict:
    chains = newest_chains(date, symbols, base_dir)
    if not chains:
        log.warning("No chain snapshots found under %s", base_dir or config.CHAIN_DIR)
        return {}
    results: dict[str, dict] = {}
    for sym, path in chains.items():
        try:
            res = compute_symbol(load_chain(path), sym)
            res["source_chain"] = str(path)
            res["computed_path"] = str(write_computed(res, out_dir))
            results[sym] = res
        except Exception:  # noqa: BLE001 -- one bad symbol must not end the run
            log.exception("compute failed for %s", sym)
    return results


def main() -> int:
    ap = argparse.ArgumentParser(description="Compute per-strike GEX from chains")
    ap.add_argument("--symbols", nargs="*")
    ap.add_argument("--date", default=None, help="Chain date (YYYY-MM-DD)")
    ap.add_argument("--base-dir", default=None)
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s",
                        datefmt="%H:%M:%S")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    res = run(args.symbols, args.date, args.base_dir, args.out_dir)
    if not res:
        print("No chains to compute. Run altdata.sources.options_chain first.")
        return 1

    print(f"\nconvention: {config.CONVENTION_VERSION}")
    print(f"{'sym':<6} {'spot':>9} {'$gamma/1%':>16} {'flip':>9} "
          f"{'call wall':>9} {'put wall':>9} {'max pain':>9}")
    for sym, r in res.items():
        if r.get("error"):
            print(f"{sym:<6} ERROR: {r['error']}")
            continue
        o = r["overall"]
        fmt = lambda v, w=9, p=2: (f"{v:>{w},.{p}f}" if isinstance(v, (int, float)) else f"{'-':>{w}}")
        print(f"{sym:<6} {fmt(r['spot'])} {fmt(o['dollar_gamma_per_1pct'], 16, 0)} "
              f"{fmt(o['gamma_flip'])} {fmt(o['call_wall'])} {fmt(o['put_wall'])} "
              f"{fmt(r['max_pain'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
