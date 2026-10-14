"""
The weekly loop (the brief's section 8, loop 2) -- in Tranche 1, its first duty
only: THE ALLOCATOR'S REBALANCE (X-1.7, "rebalanced by the weekly loop, never by
hand").

    python -m alpha.loops.weekly [--as-of ISO] [--ledger PATH]

Sunday after the Weekly's run (chester-alpha-weekly.timer, 06:00 ET). It applies
the nightly loop's latest proposed weights: one `applied` allocation per engine
and one loop_events row, `rebalance`, carrying the weights before and after. The
walk-forward extension, the bounded re-fit and the research agenda are X-2.4's.
It reads alpha.db and writes alpha.db; it does not open the observation store.
"""

from __future__ import annotations

import argparse
import logging
import sys
import traceback
from typing import Optional

from altdata import session

from .. import governor
from ..ledger import Ledger

log = logging.getLogger(__name__)
LOOP = "weekly"


def rebalance(ledger: Ledger, as_of: str) -> dict:
    day = session.session_date(as_of)
    if governor.lab_status(ledger) == "halted":
        ledger.event(LOOP, "rebalance_skipped", as_of, None,
                     after={"why": "the lab is halted for the operator's review"})
        return {"day": day, "applied": {}, "skipped": "lab halted"}
    last = ledger.one("SELECT MAX(day) AS d FROM allocations WHERE kind='proposed' "
                      "AND day<=?", (day,))
    if not last or not last["d"]:
        return {"day": day, "applied": {}, "skipped": "nothing proposed"}
    proposed = ledger.q("SELECT * FROM allocations WHERE kind='proposed' AND day=?",
                        (last["d"],))
    before = {}
    for p in proposed:
        r = ledger.one("SELECT weight FROM allocations WHERE engine_id=? AND "
                       "kind='applied' AND day<? ORDER BY day DESC LIMIT 1",
                       (p["engine_id"], day))
        before[p["engine_id"]] = r["weight"] if r else None
    applied = {}
    for p in proposed:
        ledger.put("allocations", {"engine_id": p["engine_id"], "day": day,
                                   "kind": "applied", "weight": p["weight"],
                                   "cluster": p["cluster"],
                                   "detail": f"applied from the {last['d']} proposal",
                                   "as_of": as_of})
        applied[p["engine_id"]] = p["weight"]
    ledger.event(LOOP, "rebalance", as_of, None, before=before,
                 after={"weights": applied, "proposed_on": last["d"]},
                 counterfactual={"weights": before})
    return {"day": day, "applied": applied, "proposed_on": last["d"]}


def run(as_of: Optional[str] = None, ledger_path=None) -> dict:
    as_of = as_of or session.utc_iso(timespec="microseconds")
    with Ledger(ledger_path) as lg:
        try:
            out = rebalance(lg, as_of)
        except Exception as exc:                              # noqa: BLE001
            log.exception("weekly: rebalance failed")
            lg.event(LOOP, "failure", as_of, None,
                     after={"step": "rebalance", "error": f"{type(exc).__name__}: {exc}",
                            "trace": traceback.format_exc()[-1500:]})
            return {"failures": ["rebalance"]}
        lg.event(LOOP, "run", as_of, None, after=out)
        return {**out, "failures": []}


def _main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="The Alpha Lab's weekly loop")
    ap.add_argument("--as-of")
    ap.add_argument("--ledger")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    out = run(a.as_of, a.ledger)
    print(f"alpha weekly {out.get('day', '')}: applied={out.get('applied')} "
          f"failures={out.get('failures')}")
    return 1 if out.get("failures") else 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
