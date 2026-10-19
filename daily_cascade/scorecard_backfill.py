"""
The dealer scorecard's backfill (Batch 11 item 54, ruled 19 Oct 2026).

    python -m daily_cascade.scorecard_backfill run --dry-run     # what it would write
    python -m daily_cascade.scorecard_backfill run               # write
    python -m daily_cascade.scorecard_backfill run --from 2026-09-15 --to 2026-10-16

WHAT IT DOES. Rebuilds `dealer.scorecard_day` rows for SPY from the 16:10 settled
captures on disk, back to the first, for every session that has no row yet. POINT
IN TIME: each row's morning profile is the prior session's settled capture (as
the close reads it), its session profile is the session's own settled capture,
its bars, closes and SPY's 30-day IV are the session's own, read from the store,
and the row's available_at is the LATEST of its inputs' -- the capture's
`fetched_at` and each stored input's available_at -- so a row is never knowable
before the data it is made of (the market_features rule).

LABELLED. Every row carries `"backfilled": true` and the source
`daily_close:backfill`. A backfilled row never enters the test sample: the H1-H5
rates print the test sample (live rows from the registration date, 17 Oct 2026)
with the rest beside it, "before registration, descriptive"
(altdata/dealer_scorecard.from_store). The registration file is not edited.

IDEMPOTENT. A session that already has a row (live or backfilled) is skipped, so
a second run writes nothing, and a live row is never replaced.

WHAT IT CANNOT REBUILD. The close's pin flags (`pin_max_pain_hit`,
`pin_peak_gex_hit`) come from the close's payload and are left None; nothing
reads them for H1-H5. The put/call volume ratio is left None.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import math
import sys
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger("daily_cascade.scorecard_backfill")
KEY = "dealer.scorecard_day"
SOURCE = "daily_close:backfill"
IV_KEY = "chain.spy_atm_iv_30d"


def _settled(day: str, base_dir: Optional[str]) -> Optional[dict]:
    from . import dealer_block                                  # noqa: PLC0415
    return dealer_block.newest_settled(day, "SPY", base_dir, lookback_days=0)


def capture_days(base_dir: Optional[str] = None) -> list[str]:
    """Every session directory under the computed dir, oldest first."""
    from altdata import config as acfg                          # noqa: PLC0415
    root = Path(base_dir or acfg.COMPUTED_DIR)
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir() and len(p.name) == 10)


def _last(st, key: str, as_of: str, inst=None, on_or_before: Optional[str] = None,
          strictly_before: Optional[str] = None) -> Optional[tuple[str, float, str]]:
    best = None
    for r in st.as_of(key, as_of, inst):
        d = str(r["observed_at"])[:10]
        if r.get("value_num") is None:
            continue
        if on_or_before and d > on_or_before:
            continue
        if strictly_before and d >= strictly_before:
            continue
        if best is None or d > best[0]:
            best = (d, float(r["value_num"]), str(r.get("available_at") or ""))
    return best


def build_row(day: str, morning: dict, cur: dict, bars: dict, close: Optional[float],
              prior_close: Optional[float], iv_pct: Optional[float],
              cfg_flags: Optional[dict] = None, ntg_min: float = 0.10) -> dict:
    """The row, by stack_close.scorecard_row's fields, from captures and stored
    series only. Pure: the gate builds one by hand."""
    from altdata import dealer_scorecard as dsc                 # noqa: PLC0415
    from .stack_close import _carried_0dte, _within_pct         # noqa: PLC0415
    o = (cur.get("overall") or {})
    b = bars.get("bars") or []
    hi = max((x["high"] for x in b), default=None)
    lo = min((x["low"] for x in b), default=None)
    flip = morning.get("gamma_flip")
    rets = [math.log(b[i]["close"] / b[i - 1]["close"]) for i in range(1, len(b))
            if b[i - 1]["close"]]
    rv = (math.sqrt(sum(r * r for r in rets) / len(rets)) * math.sqrt(78 * 252) * 100
          if len(rets) > 10 else None)
    net_close = o.get("net_gex")
    wall_pct = float((cfg_flags or {}).get("wall_pct", 0.25))
    ntg_m = morning.get("net_to_gross")
    return {
        "session": day, "symbol": "SPY",
        "gamma_regime": (None if net_close is None else
                         "positive" if net_close > 0 else "negative"),
        "net_gex_close": net_close, "net_gex_morning": morning.get("net_gex"),
        "flip_morning": flip,
        "flip_crossed": (bool(lo <= flip <= hi) if None not in (lo, hi, flip) else None),
        "session_high": hi, "session_low": lo,
        "session_range_pct": (round(100 * (hi - lo) / prior_close, 3)
                              if None not in (hi, lo) and prior_close else None),
        "session_return_pct": (round(100 * (close / prior_close - 1), 3)
                               if close is not None and prior_close else None),
        "pin_max_pain_hit": None, "pin_peak_gex_hit": None,
        "realized_vol_5m_ann_pct": round(rv, 2) if rv else None,
        "bars_complete": bars.get("complete"), "bars_n": bars.get("n"),
        "close": close, "prior_close": prior_close,
        "dex_close": o.get("dex_notional"),
        "call_wall": o.get("call_wall"), "put_wall": o.get("put_wall"),
        "max_pain": o.get("max_pain"), "flip_close": o.get("gamma_flip"),
        "call_wall_morning": morning.get("call_wall"),
        "put_wall_morning": morning.get("put_wall"),
        "is_expiry_session": dsc.is_monthly_expiry(day),
        "carried_0dte": _carried_0dte(cur),
        "call_wall_otm_morning": morning.get("call_wall_otm"),
        "put_wall_otm_morning": morning.get("put_wall_otm"),
        "wall_approached_call": _within_pct(hi, morning.get("call_wall_otm"), wall_pct),
        "wall_approached_put": _within_pct(lo, morning.get("put_wall_otm"), wall_pct),
        "flip_in_range": (bool(lo <= flip <= hi) if None not in (lo, hi, flip) else None),
        "regime_eligible": (None if ntg_m is None else ntg_m >= ntg_min),
        "peak_gex_strike_morning": morning.get("peak_abs_gex_strike"),
        "net_to_gross_morning": ntg_m,
        "net_to_gross_close": o.get("net_to_gross"),
        "atm_iv_30d": iv_pct, "put_call_volume": None,
        "backfilled": True,
    }


def plan(db_path: Optional[str] = None, base_dir: Optional[str] = None,
         first: Optional[str] = None, last: Optional[str] = None) -> dict:
    """{rows, skipped}: the rows a run would write, nothing written."""
    from altdata import bars as bars_mod, observations          # noqa: PLC0415
    from altdata import session                                 # noqa: PLC0415
    from . import stack                                         # noqa: PLC0415
    flags = bars_mod.load_config().get("dealer_flags") or {}
    ntg_min = float((stack.config().get("dealer_block") or {}).get("net_to_gross_min", 0.10))
    rows, skipped = [], []
    days = capture_days(base_dir)
    with observations.ObservationStore(db_path) as st, bars_mod.BarStore(db_path) as bst:
        have = {str(r["observed_at"])[:10] for r in st.as_of(KEY, "9999", "SPY")}
        for day in days:
            if (first and day < first) or (last and day > last):
                continue
            if day in have:
                skipped.append((day, "a row exists"))
                continue
            cur = _settled(day, base_dir)
            if not cur or cur.get("error"):
                skipped.append((day, "no settled 16:10 capture"))
                continue
            prev = session.previous_trading_session(day).isoformat()
            morning_cap = _settled(prev, base_dir)
            if not morning_cap or morning_cap.get("error"):
                skipped.append((day, f"no settled capture for the prior session {prev}"))
                continue
            cap_at = str(cur.get("fetched_at") or f"{day}T20:15:00+00:00")
            # The session's own inputs, as stored by the end of its day (UTC).
            eod = f"{(dt.date.fromisoformat(day) + dt.timedelta(days=1)).isoformat()}T03:59:59+00:00"
            close = _last(st, "yfinance.mkt_spy", eod, on_or_before=day)
            prior = _last(st, "yfinance.mkt_spy", eod, strictly_before=day)
            iv = _last(st, IV_KEY, eod, on_or_before=day)
            bars = bars_mod.intraday(bst, "spy", day, as_of=eod)
            used = [cap_at] + [x[2] for x in (close, prior, iv) if x and x[2]]
            used += [str(b.get("available_at")) for b in bars.get("bars") or []
                     if b.get("available_at")]
            at = max(used)
            row = build_row(day, morning_cap.get("overall") or {}, cur, bars,
                            close[1] if close and close[0] == day else None,
                            prior[1] if prior else None,
                            iv[1] if iv and iv[0] == day else None, flags, ntg_min)
            rows.append({"registry_key": KEY, "instrument": "SPY", "observed_at": day,
                         "available_at": at,
                         "value": json.dumps(row, sort_keys=True, default=str),
                         "source": SOURCE})
    return {"rows": rows, "skipped": skipped}


def run(db_path: Optional[str] = None, base_dir: Optional[str] = None,
        dry_run: bool = True, **kw) -> dict:
    from altdata import observations                            # noqa: PLC0415
    p = plan(db_path, base_dir, **kw)
    if not dry_run and p["rows"]:
        with observations.open_writer(__name__, db_path) as st:
            st.write_many(p["rows"])
    p["written"] = 0 if dry_run else len(p["rows"])
    return p


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m daily_cascade.scorecard_backfill")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--dry-run", action="store_true")
    r.add_argument("--from", dest="first")
    r.add_argument("--to", dest="last")
    r.add_argument("--db")
    r.add_argument("--computed-dir")
    a = ap.parse_args(argv)
    res = run(a.db, a.computed_dir, dry_run=a.dry_run, first=a.first, last=a.last)
    for row in res["rows"]:
        print(f"{'would write' if a.dry_run else 'wrote'} {row['observed_at']} "
              f"(available {row['available_at']})")
    for day, why in res["skipped"]:
        print(f"skipped {day}: {why}")
    print(f"{len(res['rows'])} rows {'planned' if a.dry_run else 'written'}; "
          f"{len(res['skipped'])} sessions skipped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
