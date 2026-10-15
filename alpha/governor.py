"""
The risk governor (X-1.8): the only hand on the wheel, and its numbers are the
constitution's.

  engine     at governor.engine.halve_at (-10%) from its own high-water mark the
             engine HALVES: status `halved`, frozen; at stop_at (-20%) it STOPS:
             status `validation`, frozen, its open positions exited at the next
             stored bar's open, no new signals.
  portfolio  at governor.portfolio.stop_at (-15%) from the lab's high-water mark
             the whole lab HALTS for the operator's review: every open position
             exited at the next stored bar's open, no new signals from any
             engine, until an operator event (`lab_resume`, source operator).

THE RESUME IS THE OPERATOR'S (ruling 6, 14 Oct 2026). Only
`python -m alpha.governor resume --reason "..."` lifts a halt: it writes the
lab_resume event with source=operator and the reason, and nothing else does --
not a recovery of the equity, not a new high-water mark, not a lab_resume row a
loop writes. The command is denied to sessions (.claude/settings.json, CLAUDE.md)
as the register writes are. On the resume the lab's high-water mark is re-based
to its equity at that moment, so the next night does not re-halt on the same
drawdown the operator has just reviewed; a fresh -15% from there halts again.
A resume never hides a loss (15 Oct): the event records the high-water mark and
the drawdown it replaced, and the Weekly's lab line prints the drawdown since
inception -- from the all-time high, which no resume moves -- beside the current
one (alpha/lab_line.py).

FROZEN MEANS FROZEN. A halved or stopped engine carries frozen=1 and no loop
re-fits it (alpha/validate.refit_allowed; the constitution's
refit.frozen_in_drawdown). A halved engine is restored to `live` -- and unfrozen
-- only when its equity makes a new high-water mark; a stopped engine returns
only through validation.

THE EQUITY. Each engine's equity is an index (1.0 at its first day) compounding
its daily net P&L over the capital the allocator gave it that day; the lab's is
in lab dollars, its notional plus every engine's net P&L. Both are written to
alpha.db's `equity` table with the high-water mark and the drawdown, and every
transition is a loop_events row.
"""

from __future__ import annotations

from typing import Optional

from . import config as acfg
from .ledger import LAB


def lab_status(ledger) -> str:
    """`halted` from a lab_halt event until a later OPERATOR lab_resume. A
    lab_resume with any other source does not count."""
    rows = ledger.q("SELECT kind FROM loop_events WHERE kind='lab_halt' OR "
                    "(kind='lab_resume' AND source='operator') ORDER BY id DESC LIMIT 1")
    return "halted" if rows and rows[0]["kind"] == "lab_halt" else "running"


def _last_resume(ledger) -> Optional[dict]:
    return ledger.one("SELECT * FROM loop_events WHERE kind='lab_resume' AND "
                      "source='operator' ORDER BY id DESC LIMIT 1")


def resume(ledger, as_of: str, reason: str) -> int:
    """The operator lifts the lab's halt (ruling 6): one lab_resume event,
    source operator, quoting the reason. Refuses an empty reason, and a lab
    that is not halted."""
    if not (reason or "").strip():
        raise ValueError("a resume quotes the operator's reason")
    if lab_status(ledger) != "halted":
        raise RuntimeError("the lab is not halted: nothing to resume")
    eq = ledger.one("SELECT equity, hwm, drawdown FROM equity WHERE engine_id=? "
                    "ORDER BY day DESC LIMIT 1", (LAB,))
    return ledger.event("operator", "lab_resume", as_of, None,
                        before={"status": "halted",
                                "hwm": eq["hwm"] if eq else None,
                                "drawdown": eq["drawdown"] if eq else None},
                        after={"status": "running", "reason": reason.strip(),
                               "hwm_replaced": eq["hwm"] if eq else None,
                               "drawdown_replaced": eq["drawdown"] if eq else None,
                               "hwm_rebased_to": eq["equity"] if eq else None},
                        counterfactual={"status": "halted"}, source="operator")


def _last(ledger, engine_id: str, before_day: str) -> Optional[dict]:
    return ledger.one("SELECT * FROM equity WHERE engine_id=? AND day<? "
                      "ORDER BY day DESC LIMIT 1", (engine_id, before_day))


def step(ledger, as_of: str, day: str, pnl: dict[str, float],
         capital: dict[str, float], con: Optional[dict] = None,
         cfg: Optional[dict] = None) -> dict:
    """Write today's equity for each engine in `capital` and for the lab, apply
    the thresholds, and return what the paper book must do:
    {"stop": {engine: reason}, "lab_halt": bool, "transitions": [...]}."""
    con = con or acfg.constitution()
    cfg = cfg or acfg.settings()
    halve = float(con["governor"]["engine"]["halve_at"])
    stop = float(con["governor"]["engine"]["stop_at"])
    lab_stop = float(con["governor"]["portfolio"]["stop_at"])
    out: dict = {"stop": {}, "lab_halt": False, "transitions": [], "equity": {}}
    for eid, cap in sorted(capital.items()):
        prev = _last(ledger, eid, day)
        idx0, hwm0 = (float(prev["equity"]), float(prev["hwm"])) if prev else (1.0, 1.0)
        r = (pnl.get(eid, 0.0) / cap) if cap > 0 else 0.0
        idx = idx0 * (1.0 + r)
        hwm = max(hwm0, idx)
        dd = idx / hwm - 1.0
        ledger.put("equity", {"engine_id": eid, "day": day, "equity": idx,
                              "hwm": hwm, "drawdown": dd, "as_of": as_of})
        out["equity"][eid] = {"equity": idx, "hwm": hwm, "drawdown": dd}
        e = ledger.engine(eid)
        if not e:
            continue
        before = {"status": e["status"], "frozen": bool(e["frozen"]), "drawdown": dd}
        if dd <= stop and e["status"] in ("live", "halved"):
            ledger.set_engine(eid, as_of, status="validation", frozen=True)
            ledger.event("governor", "stop", as_of, eid, before=before,
                         after={"status": "validation", "frozen": True,
                                "threshold": stop},
                         counterfactual={"status": e["status"]})
            out["stop"][eid] = "governor_stop"
            out["transitions"].append((eid, "stop"))
        elif dd <= halve and e["status"] == "live":
            ledger.set_engine(eid, as_of, status="halved", frozen=True)
            ledger.event("governor", "halve", as_of, eid, before=before,
                         after={"status": "halved", "frozen": True,
                                "threshold": halve},
                         counterfactual={"status": "live"})
            out["transitions"].append((eid, "halve"))
        elif e["status"] == "halved" and dd >= 0.0 and prev is not None:
            ledger.set_engine(eid, as_of, status="live", frozen=False)
            ledger.event("governor", "restore", as_of, eid, before=before,
                         after={"status": "live", "frozen": False,
                                "why": "a new high-water mark"},
                         counterfactual={"status": "halved"})
            out["transitions"].append((eid, "restore"))
    notional = float(cfg.get("notional_capital") or 0)
    prev = _last(ledger, LAB, day)
    eq0, hwm0 = (float(prev["equity"]), float(prev["hwm"])) if prev else (notional, notional)
    res = _last_resume(ledger)
    if prev and res and not ledger.one(
            "SELECT 1 FROM equity WHERE engine_id=? AND written_at > ?",
            (LAB, res["written_at"])):
        hwm0 = eq0                       # the first night after the resume re-bases
    eq = eq0 + sum(pnl.values())
    hwm = max(hwm0, eq)
    dd = eq / hwm - 1.0 if hwm > 0 else 0.0
    ledger.put("equity", {"engine_id": LAB, "day": day, "equity": eq, "hwm": hwm,
                          "drawdown": dd, "as_of": as_of})
    out["equity"][LAB] = {"equity": eq, "hwm": hwm, "drawdown": dd}
    if dd <= lab_stop and lab_status(ledger) != "halted":
        ledger.event("governor", "lab_halt", as_of, None,
                     before={"drawdown": dd, "status": "running"},
                     after={"status": "halted", "threshold": lab_stop,
                            "review": "the operator's"},
                     counterfactual={"status": "running"})
        out["transitions"].append((LAB, "lab_halt"))
    out["lab_halt"] = lab_status(ledger) == "halted"
    return out


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    from altdata import session                                 # noqa: PLC0415
    from .ledger import Ledger                                  # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m alpha.governor",
                                 description="The operator's resume of a halted lab")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("resume", help="lift the -15% halt (operator only)")
    r.add_argument("--reason", required=True)
    sub.add_parser("status")
    ap.add_argument("--ledger")
    a = ap.parse_args(argv)
    with Ledger(a.ledger) as lg:
        if a.cmd == "status":
            print(lab_status(lg))
            return 0
        resume(lg, session.utc_iso(timespec="microseconds"), a.reason)
    print("the lab: resumed by the operator")
    return 0


if __name__ == "__main__":
    import sys as _sys
    raise SystemExit(_main(_sys.argv[1:]))
