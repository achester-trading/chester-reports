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
    """`halted` from a lab_halt event until a later operator lab_resume."""
    rows = ledger.q("SELECT kind FROM loop_events WHERE kind IN ('lab_halt','lab_resume')"
                    " ORDER BY id DESC LIMIT 1")
    return "halted" if rows and rows[0]["kind"] == "lab_halt" else "running"


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
