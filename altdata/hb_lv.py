"""
The crowding family's high-beta / low-vol member and its divergence flag
(signal-triage Batch 22 item 118, the order's 100; A128, 6 Nov 2026). Settings:
config/crowding.yaml `members.hb_lv`.

    python -m altdata.hb_lv compute [--as-of T] [--full] [--dry-run]
    python -m altdata.hb_lv show [--date D]

THE MEMBER. calc.hb_lv_ratio is SPHB's close over SPLV's on the session both
carry, and calc.hb_lv_ratio_chg_1d its change against the previous common session,
in percent. Each row is available at the later of its two closes' available_at,
so the ratio is never knowable before the prices it is made of. The
market-features pass computes the recent sessions; `compute --full` writes the
history.

THE FLAG (the order's 100). The S&P 500 up 0.5% or more on the day while
SPHB/SPLV is down 2% or more. It is read from the stored closes as of the cutoff,
so the close needs no features pass to have run. It prints one line in the
close's "what doesn't fit" on a fired day only, with both figures and "no rights
until the backtest". Its ledger, docs/ledgers/hb-lv-divergence-*, is that
backtest (altdata/ledgers/hb_lv_118.py), pre-registered before this code.

Report-only: nothing here enters a composite, the market-state object, the T&B
intake queue or a regime.
"""

from __future__ import annotations

import datetime as dt
import logging
import sys
from pathlib import Path
from typing import Any, Optional

import yaml

from . import observations, session

log = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / "config" / "crowding.yaml"
SOURCE = "hb_lv"
RATIO_KEY = "calc.hb_lv_ratio"
CHG_KEY = "calc.hb_lv_ratio_chg_1d"
RECENT_DAYS = 14


def config(path: Optional[Path] = None) -> dict:
    with open(path or CONFIG, encoding="utf-8") as fh:
        return yaml.safe_load(fh)["members"]["hb_lv"]


def flag(index_chg_pct: Optional[float], ratio_chg_pct: Optional[float],
         cfg: Optional[dict] = None) -> Optional[bool]:
    """THE RULE, in one place (the close and the ledger both call it): the index up
    at least `index_up_pct` while the ratio is down at least `ratio_down_pct`, both
    in percent. None when either figure is missing."""
    f = (cfg or config())["flag"]
    if index_chg_pct is None or ratio_chg_pct is None:
        return None
    return (index_chg_pct >= float(f["index_up_pct"])
            and ratio_chg_pct <= -float(f["ratio_down_pct"]))


def _closes(st, key: str, as_of: Optional[str]) -> dict[str, tuple[float, str]]:
    out: dict[str, tuple[float, str]] = {}
    for r in st.as_of(key, as_of):
        if r.get("value_num") is None:
            continue
        out[str(r["observed_at"])[:10]] = (float(r["value_num"]), str(r.get("available_at") or ""))
    return out


def ratio_rows(st, as_of: Optional[str] = None) -> list[dict]:
    """[{day, ratio, chg_pct, avail}] over the sessions both ETFs carry."""
    cfg = config()
    a = _closes(st, cfg["numerator"]["key"], as_of)
    b = _closes(st, cfg["denominator"]["key"], as_of)
    out, prev = [], None
    for d in sorted(set(a) & set(b)):
        if not b[d][0]:
            continue
        v = a[d][0] / b[d][0]
        out.append({"day": d, "ratio": v, "avail": max(a[d][1], b[d][1]),
                    "chg_pct": None if prev is None else 100.0 * (v / prev - 1.0)})
        prev = v
    return out


def compute_rows(st, as_of: Optional[str] = None,
                 first_day: Optional[str] = None) -> list[dict]:
    rows = []
    for r in ratio_rows(st, as_of):
        if first_day and r["day"] < first_day:
            continue
        rows.append({"registry_key": RATIO_KEY, "instrument": None, "observed_at": r["day"],
                     "available_at": r["avail"], "value": round(r["ratio"], 8),
                     "source": SOURCE})
        if r["chg_pct"] is not None:
            rows.append({"registry_key": CHG_KEY, "instrument": None,
                         "observed_at": r["day"], "available_at": r["avail"],
                         "value": round(r["chg_pct"], 6), "source": SOURCE})
    return rows


def default_first_day(st, as_of: Optional[str] = None) -> Optional[str]:
    """The recent sessions, or None (the whole history) when nothing is stored."""
    if not st.latest_as_of(RATIO_KEY, as_of or session.utc_iso()):
        return None
    end = dt.date.fromisoformat((as_of or session.utc_iso())[:10])
    return (end - dt.timedelta(days=RECENT_DAYS)).isoformat()


def compute(as_of: Optional[str] = None, first_day: Optional[str] = None,
            store: Optional[observations.ObservationStore] = None,
            dry_run: bool = False, full: bool = False) -> dict:
    own = store is None
    db = store or observations.open_writer(__name__)
    try:
        if not full and first_day is None:
            first_day = default_first_day(db, as_of)
        rows = compute_rows(db, as_of, first_day)
        written = 0 if dry_run else db.write_many(observations.drop_unchanged(db, rows))
        return {"computed": len(rows), "written": written, "dry_run": dry_run,
                "first_day": first_day}
    finally:
        if own:
            db.close()


def _pct(v: float) -> str:
    return f"{v:+.1f}%"


def for_session(st, day: str, cutoff: str) -> dict:
    """The flag for `day` from the stored closes as of `cutoff`: {fired, index_chg,
    ratio_chg, ratio, line}. Never raises on a missing series: fired is None."""
    cfg = config()
    idx = _closes(st, cfg["flag"]["index"]["key"], cutoff)
    days = sorted(d for d in idx if d <= day)
    ichg = (100.0 * (idx[day][0] / idx[days[-2]][0] - 1.0)
            if day in idx and len(days) >= 2 and idx[days[-2]][0] else None)
    rr = [r for r in ratio_rows(st, cutoff) if r["day"] <= day]
    rchg = rr[-1]["chg_pct"] if rr and rr[-1]["day"] == day else None
    fired = flag(ichg, rchg, cfg)
    out: dict[str, Any] = {"fired": fired, "index_chg": ichg, "ratio_chg": rchg,
                           "ratio": rr[-1]["ratio"] if rr and rr[-1]["day"] == day else None,
                           "line": None}
    if fired:
        f = cfg["flag"]
        out["line"] = (f"High beta against low volatility: the S&P 500 {_pct(ichg)} on the "
                       f"day while SPHB/SPLV {_pct(rchg)} (the flag: the index up "
                       f"{f['index_up_pct']:g}% or more with the ratio down "
                       f"{f['ratio_down_pct']:g}% or more; item 118). {f['rights'].capitalize()}.")
    return out


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    import json                                                 # noqa: PLC0415
    ap = argparse.ArgumentParser(description="the high-beta / low-vol member and flag")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compute")
    c.add_argument("--as-of", default=None)
    c.add_argument("--full", action="store_true")
    c.add_argument("--dry-run", action="store_true")
    s = sub.add_parser("show")
    s.add_argument("--date", default=None)
    a = ap.parse_args(argv)
    if a.cmd == "compute":
        print(json.dumps(compute(as_of=a.as_of, dry_run=a.dry_run, full=a.full), indent=1))
        return 0
    day = a.date or session.last_completed_session().isoformat()
    with observations.ObservationStore() as st:
        print(json.dumps(for_session(st, day, session.utc_iso()), indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
