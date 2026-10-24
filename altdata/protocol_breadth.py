"""
Signal-triage Batch 15, item 78 (written as 71; ST-R6.78a): DefiLlama's
active-protocol count, the free automated breadth proxy for crypto's supply side.
Report only.

    python -m altdata.protocol_breadth daily [--dry-run]     # the crypto basket's run
    python -m altdata.protocol_breadth show [--as-of D]

THE SOURCE (the check of 23 Oct 2026). api.llama.fi/protocols, no key, serves
TODAY'S list only: 8,813 protocols that day, each with fields such as `deadFrom`,
`deprecated`, `listedAt` and `tvl`. Its `deadFrom` and `listedAt` dates are
today's vintage, written after the fact, and a protocol DefiLlama removes
disappears from the list -- so no point-in-time history can be rebuilt from it.
The count is therefore a DAILY SNAPSHOT from the first pull on, and every line
names the day its history starts.

STORED (source `defillama`, the registered id; observed_at the UTC day of the
pull, available_at the pull instant):
  defillama.protocols_listed   protocols neither marked dead (`deadFrom`) nor
                               `deprecated`
  defillama.protocols_active   those of them with a TVL above zero

The monthly hand count of shutdowns from compiled lists is a listed gap (G3).
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parent.parent
ROSTER = "protocols"
URL = "https://api.llama.fi/protocols"
LISTED_KEY = "defillama.protocols_listed"
ACTIVE_KEY = "defillama.protocols_active"
ROSTER_KEYS = [LISTED_KEY, ACTIVE_KEY]
SOURCE = "defillama"
HAND_COUNT_GAP = ("The monthly count of protocol shutdowns from compiled lists: a "
                  "listed gap (G3: no recurring by-hand line without the operator's "
                  "yes)")


def counts(protocols: list[dict]) -> dict[str, int]:
    listed = [p for p in protocols if not p.get("deadFrom") and not p.get("deprecated")]
    active = [p for p in listed
              if isinstance(p.get("tvl"), (int, float)) and p["tvl"] > 0]
    return {"total": len(protocols), "listed": len(listed), "active": len(active)}


def rows(c: dict[str, int], at: str) -> list[dict]:
    day = at[:10]
    return [{"registry_key": k, "instrument": None, "observed_at": day,
             "available_at": at, "value": c[f], "source": SOURCE,
             "availability_kind": "ingest_instant"}
            for k, f in ((LISTED_KEY, "listed"), (ACTIVE_KEY, "active"))]


def _get() -> list[dict]:
    from .sources._base import http_get_bytes                   # noqa: PLC0415
    return json.loads(http_get_bytes(URL, timeout=120))


def daily(dry_run: bool = False, record: bool = True, fetch=None, db=None,
          at: Optional[str] = None) -> dict:
    from . import observations, session                         # noqa: PLC0415
    at = at or session.utc_iso(timespec="microseconds")
    try:
        c = counts((fetch or _get)())
    except Exception as exc:                                    # noqa: BLE001
        reason = f"defillama: {type(exc).__name__}: {str(exc)[:120]}"
        if record and not dry_run:
            from . import feeds                                 # noqa: PLC0415
            feeds.record_attempted(ROSTER, ROSTER_KEYS, merge=True,
                                   failed={k: reason for k in ROSTER_KEYS})
        return {"step": "daily", "error": reason}
    r = rows(c, at)
    if dry_run:
        return {"step": "daily", "dry_run": True, "counts": c, "rows": r}
    own = db is None
    st = db or observations.open_writer(__name__)
    try:
        n = st.write_many(r)
    finally:
        if own:
            st.close()
    if record:
        from . import feeds                                     # noqa: PLC0415
        feeds.record_attempted(ROSTER, ROSTER_KEYS, merge=True)
    return {"step": "daily", "counts": c, "written": n}


def read(st, cutoff: str) -> dict:
    from . import st_r5_rates as rt                             # noqa: PLC0415
    act = rt._pts(st, ACTIVE_KEY, cutoff)                       # noqa: SLF001
    lst = rt._pts(st, LISTED_KEY, cutoff)                       # noqa: SLF001
    if not act:
        return {"state": "absent"}
    day, n = act[-1]
    prior = rt._on_or_before(act, rt._back(day, 30))            # noqa: SLF001
    return {"state": "computed", "day": day, "active": int(n),
            "listed": int(dict(lst).get(day)) if dict(lst).get(day) is not None else None,
            "start": act[0][0], "days": len(act),
            "change_30d": None if prior is None or prior[0] == day else int(n - prior[1]),
            "prior_day": None if prior is None else prior[0]}


def line(r: dict) -> str:
    if r.get("state") != "computed":
        return ("DefiLlama active protocols: not read (the daily snapshot has not run; "
                "DefiLlama serves today's list only, so the history starts at the first "
                "pull).")
    ch = ("" if r["change_30d"] is None else
          f", {r['change_30d']:+,} since {r['prior_day']}")
    lst = "" if r["listed"] is None else f" of {r['listed']:,} listed and not marked dead"
    return (f"DefiLlama active protocols (TVL above zero): {r['active']:,}{lst} on "
            f"{r['day']}{ch}. History from {r['start']} ({r['days']} daily snapshots): "
            f"DefiLlama serves today's list only.")


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415

    from . import observations, session                         # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.protocol_breadth")
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("daily")
    d.add_argument("--dry-run", action="store_true")
    s = sub.add_parser("show")
    s.add_argument("--as-of")
    a = ap.parse_args(argv)
    if a.cmd == "daily":
        out: Any = daily(dry_run=a.dry_run)
        print(json.dumps({k: v for k, v in out.items() if k != "rows"},
                         indent=2, default=str))
        return 0
    with observations.ObservationStore() as st:
        print(line(read(st, a.as_of or session.utc_iso())))
    print(HAND_COUNT_GAP + ".")
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
