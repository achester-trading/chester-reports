"""
Pin log -- did price finish near the levels the gamma profile pointed at?

One row per symbol per day, written whether the level was hit or missed. The
misses are the point: a pin log that only records hits is a highlight reel, and
the hit *rate* is the only thing that makes any of these levels actionable.

Three levels are scored independently, as separate columns:

    max_pain          strike minimising total ITM payout
    peak_gex_strike   strike carrying the largest |GEX|
    call_wall         strike carrying the largest positive GEX

Distance is signed, in basis points of the close:

    dist_bps = (close - level) / close x 10_000

so a negative distance means the close printed below the level. A hit is
|dist_bps| <= config.PIN_TOLERANCE_BPS (25bps), declared in config so this
logger and any later backfill cannot drift apart.

CLOSE PRICE. The EOD run takes its chain snapshot after the bell, so the spot
carried on that snapshot is the close. `close_source` records which it was, so
a mid-session run is never silently scored as an end-of-day result.

EXPIRY TYPE. `expiry_type` classifies the peak-GEX reference strike by the
expiry bucket contributing the most |GEX| *at that strike*; `max_pain_expiry_type`
classifies the max-pain strike by the bucket holding the most OI there, since max
pain is an OI construct rather than a gamma one. Symbol-level bucket shares do
not answer this -- what matters is which expiry drives the level being scored.

UNITS. `shares_per_1pct` is the stored primary (change in dealer delta, in
shares, per 1% move); `dollar_gamma_per_1pct` is derived from it, and raw
notional (`net_gex`) is kept as the underlying quantity.

FORWARD COMPATIBILITY. The schema carries columns for data this tier cannot
serve yet -- vendor OI, per-strike arrays, dealer polarity. They are written
empty today and populate themselves when the tier changes, so no migration is
needed and old rows stay directly comparable to new ones.

Usage:
    python tools/pin_log.py                  # score today's computed snapshots
    python tools/pin_log.py --date 2026-09-04
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import logging
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from altdata import config  # noqa: E402

log = logging.getLogger(__name__)

# Column order is the file format. Append-only: never reorder or remove, so
# that a file written months apart still parses as one table.
PIN_COLUMNS = [
    "date", "symbol", "close", "close_source", "tolerance_bps",
    "max_pain", "max_pain_dist_bps", "max_pain_hit",
    "peak_gex_strike", "peak_gex_dist_bps", "peak_gex_hit",
    "call_wall", "call_wall_dist_bps", "call_wall_hit",
    "put_wall", "put_wall_dist_bps", "put_wall_hit",
    "gamma_flip", "flip_dist_bps", "spot_above_flip",
    "expiry_type", "max_pain_expiry_type",
    "net_gex", "shares_per_1pct", "dollar_gamma_per_1pct",
    "share_0dte", "share_weekly", "share_monthly", "share_quarterly",
    "convention_version", "gamma_source", "strikes_used", "rows_in",
    # --- reserved for a paid tier; empty today, no migration when they fill --
    "vendor_oi_total", "vendor_gamma_flip", "vendor_call_wall",
    "vendor_put_wall", "vendor_source",
]


def dist_bps(close: float, level: Optional[float]) -> Optional[float]:
    """Signed distance from level to close, in bps of close."""
    if not close or level is None:
        return None
    return round((close - level) / close * 10_000.0, 2)


def is_hit(d: Optional[float], tolerance_bps: float) -> Optional[bool]:
    return None if d is None else abs(d) <= tolerance_bps


def row_for(computed: dict, close: Optional[float] = None,
            close_source: str = "chain_snapshot_spot",
            tolerance_bps: Optional[float] = None) -> dict:
    """Build one pin-log row from one computed GEX snapshot."""
    tol = config.PIN_TOLERANCE_BPS if tolerance_bps is None else tolerance_bps
    o = computed.get("overall") or {}
    b = computed.get("buckets") or {}
    q = computed.get("quality") or {}
    close = close if close is not None else computed.get("spot")

    levels = {
        "max_pain": computed.get("max_pain"),
        "peak_gex_strike": o.get("peak_abs_gex_strike"),
        "call_wall": o.get("call_wall"),
        "put_wall": o.get("put_wall"),
    }
    row: dict = {
        "date": (computed.get("computed_at") or "")[:10] or dt.date.today().isoformat(),
        "symbol": computed.get("symbol"),
        "close": close,
        "close_source": close_source,
        "tolerance_bps": tol,
        "gamma_flip": o.get("gamma_flip"),
        "flip_dist_bps": dist_bps(close, o.get("gamma_flip")),
        "spot_above_flip": (None if not (close and o.get("gamma_flip"))
                            else close > o["gamma_flip"]),
        # Expiry that dominates each reference level -- lets the pin rate be
        # segmented by expiry type, which is the whole point of logging it.
        "expiry_type": computed.get("expiry_type"),
        "max_pain_expiry_type": computed.get("max_pain_expiry_type"),
        "net_gex": o.get("net_gex"),
        # Shares is the stored primary; dollars is derived from it upstream.
        "shares_per_1pct": o.get("shares_per_1pct"),
        "dollar_gamma_per_1pct": o.get("dollar_gamma_per_1pct"),
        "convention_version": computed.get("convention_version"),
        "gamma_source": computed.get("gamma_source"),
        "strikes_used": o.get("strikes"),
        "rows_in": q.get("rows_in"),
    }
    for name, level in levels.items():
        d = dist_bps(close, level)
        row[name] = level
        row[f"{name.replace('_strike', '')}_dist_bps" if name == "peak_gex_strike"
            else f"{name}_dist_bps"] = d
        row[f"{name.replace('_strike', '')}_hit" if name == "peak_gex_strike"
            else f"{name}_hit"] = is_hit(d, tol)
    for bucket in ("0dte", "weekly", "monthly", "quarterly"):
        row[f"share_{bucket}"] = (b.get(bucket) or {}).get("share_of_total_abs_gex")
    for reserved in ("vendor_oi_total", "vendor_gamma_flip", "vendor_call_wall",
                     "vendor_put_wall", "vendor_source"):
        row.setdefault(reserved, None)
    return {k: row.get(k) for k in PIN_COLUMNS}


def append_rows(rows: list[dict], path: Optional[str] = None) -> Path:
    """Append rows, replacing any existing (date, symbol) pair.

    Re-running the EOD job must not double-count a day -- the hit rate is the
    output, and duplicate rows would quietly inflate it.
    """
    p = Path(path or config.PIN_LOG_PATH)
    p.parent.mkdir(parents=True, exist_ok=True)

    existing: list[dict] = []
    if p.exists():
        with p.open(encoding="utf-8", newline="") as fp:
            existing = [r for r in csv.DictReader(fp)]

    replacing = {(r["date"], r["symbol"]) for r in rows}
    kept = [r for r in existing if (r.get("date"), r.get("symbol")) not in replacing]
    merged = kept + [{k: ("" if v is None else v) for k, v in r.items()} for r in rows]
    merged.sort(key=lambda r: (str(r.get("date")), str(r.get("symbol"))))

    with p.open("w", encoding="utf-8", newline="") as fp:
        w = csv.DictWriter(fp, fieldnames=PIN_COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(merged)
    return p


def load_computed(date: Optional[str] = None, symbols: Optional[list[str]] = None,
                  base_dir: Optional[str] = None) -> dict[str, dict]:
    """Newest computed snapshot per symbol for a date (default: latest day)."""
    root = Path(base_dir or config.COMPUTED_DIR)
    if not root.exists():
        return {}
    days = sorted(p for p in root.iterdir() if p.is_dir())
    if not days:
        return {}
    day = (root / date) if date else days[-1]
    if not day.exists():
        return {}
    out: dict[str, dict] = {}
    for p in sorted(day.glob("*_gex.json"), key=lambda q: q.stat().st_mtime):
        sym = p.name.split("_")[0]
        if symbols and sym not in symbols:
            continue
        try:
            out[sym] = json.loads(p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            log.warning("unreadable computed snapshot: %s", p)
    return out


def run(date: Optional[str] = None, symbols: Optional[list[str]] = None,
        computed_dir: Optional[str] = None, log_path: Optional[str] = None,
        close_source: str = "chain_snapshot_spot") -> list[dict]:
    computed = load_computed(date, symbols, computed_dir)
    rows = [row_for(c, close_source=close_source)
            for c in computed.values() if not c.get("error")]
    if rows:
        append_rows(rows, log_path)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="Score pin levels into the pin log")
    ap.add_argument("--date", default=None)
    ap.add_argument("--symbols", nargs="*")
    ap.add_argument("--computed-dir", default=None)
    ap.add_argument("--log-path", default=None)
    ap.add_argument("--close-source", default="chain_snapshot_spot")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s",
                        datefmt="%H:%M:%S")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    rows = run(args.date, args.symbols, args.computed_dir, args.log_path,
               args.close_source)
    if not rows:
        print("No computed snapshots to score. Run tools/gex_compute.py first.")
        return 1

    tol = config.PIN_TOLERANCE_BPS
    print(f"\nPin log -- tolerance {tol}bps, hit or miss recorded either way")
    print(f"{'sym':<6} {'close':>9} {'maxpain':>9} {'bps':>8} {'hit':>4}  "
          f"{'peakGEX':>9} {'bps':>8} {'hit':>4}  {'callwall':>9} {'bps':>8} {'hit':>4}")
    for r in rows:
        f = lambda v, w=9: (f"{v:>{w},.2f}" if isinstance(v, (int, float)) else f"{'-':>{w}}")
        h = lambda v: ("Y" if v is True else "n" if v is False else "-")
        print(f"{r['symbol']:<6} {f(r['close'])} "
              f"{f(r['max_pain'])} {f(r['max_pain_dist_bps'], 8)} {h(r['max_pain_hit']):>4}  "
              f"{f(r['peak_gex_strike'])} {f(r['peak_gex_dist_bps'], 8)} {h(r['peak_gex_hit']):>4}  "
              f"{f(r['call_wall'])} {f(r['call_wall_dist_bps'], 8)} {h(r['call_wall_hit']):>4}")
    hits = sum(1 for r in rows if r["max_pain_hit"])
    print(f"\n  max-pain hits today: {hits}/{len(rows)} at {tol}bps")
    print(f"  written: {args.log_path or config.PIN_LOG_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
