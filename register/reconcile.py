"""
The order gate at entry, enforced by reconciliation -- and the Doctrine's position
rule breaks. (Phase 5a; Audit #3 §N Phase 5)

    python -m register.reconcile run [--session YYYY-MM-DD]

-----------------------------------------------------------------------------
WHY RECONCILIATION IS THE GATE AT THE PAPER STAGE
-----------------------------------------------------------------------------
Nothing in this repository places an order: every IBKR service connects read-only,
tools/validate_ibkr_portfolio.py proves the source holds no order call, and Gate 3
is denied in .claude/settings.json before it exists. So "an order that contradicts
the register cannot be placed without an override recorded" cannot mean a check in
an order path -- there is none. It means the operator's orders are held to the
register after the fact, every time, with nothing absorbed silently:

    every fill the hourly IBKR sync reads must match an ACCEPTED decision
    (active, unsuperseded, or the head of a chain that was) in instrument, side,
    size and expression. A fill that does not is written to the register's
    rule_breaks table with its reason, printed in the close, counted in the
    Weekly and read by the grader.

An override is an operator record: `tools/decide.py record ... --override-gate
"<reason>"`. A session prints that command and never runs it.

-----------------------------------------------------------------------------
THE THREE POSITION RULES (Operating Doctrine)
-----------------------------------------------------------------------------
    time_stop_passed         an active decision past its recorded time stop
    book_b_conversion        a Book B position closed inside two sessions of entry
                             for a reason other than its invalidation
    allocation_floor_breach  Book A's beta-adjusted stance below the floor of the
                             band the Macro dial sets (config/risk_limits.yaml)

Idempotent: every rule break carries a dedupe key, so the hourly sync and the close
pass can both run this and each fact is written once.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from altdata import session
from register import instruments

log = logging.getLogger("register.reconcile")

SOURCE = "register.reconcile"
# Sec types, as IBKR reports them, grouped by the shape they can express.
STOCK_TYPES = ("STK", "ETF")
OPTION_TYPES = ("OPT", "FOP")
FUTURE_TYPES = ("FUT", "CONTFUT")
# Families that hold stock as one of their legs, so a stock fill is part of them.
STOCK_LEG_FAMILIES = ("covered_call", "collar", "put_spread_collar",
                      "protective_put")


def _chains(rows: list[dict]) -> list[list[dict]]:
    """Decision chains, oldest first, by superseded_by."""
    by_id = {r["id"]: r for r in rows}
    pointed = {r["superseded_by"] for r in rows if r.get("superseded_by")}
    chains = []
    for r in rows:
        if r["id"] in pointed:
            continue                               # not a chain start
        chain, cur = [r], r
        while cur.get("superseded_by") and cur["superseded_by"] in by_id:
            cur = by_id[cur["superseded_by"]]
            chain.append(cur)
        chains.append(chain)
    return chains


def expression_mismatch(dec: dict, sec_type: Optional[str]) -> Optional[str]:
    """Why an executed sec_type contradicts the decision's recorded shape."""
    from register.heat import OPTION_FAMILIES  # noqa: PLC0415
    fam = dec.get("expression_family")
    lev = dec.get("leverage_form")
    st = str(sec_type or "").upper()
    if st in FUTURE_TYPES and lev != "futures":
        return (f"filled in futures ({st}) but the decision records leverage_form "
                f"{lev!r}, not 'futures'")
    if lev == "futures" and st and st not in FUTURE_TYPES:
        return f"the decision records futures leverage but filled as {st}"
    if st in OPTION_TYPES:
        if fam is None:
            return ("filled in options but the decision records no "
                    "expression_family -- an options expression must be named")
        if fam not in OPTION_FAMILIES:
            return f"filled in options but the decision records {fam!r}"
    if st in STOCK_TYPES and fam in OPTION_FAMILIES and fam not in STOCK_LEG_FAMILIES:
        return (f"filled in stock but the decision records the options "
                f"expression {fam!r}")
    return None


def reconcile_executions(reg: Any, xs: Any, session_day: str) -> dict:
    """Every execution against the decisions on its instrument. Returns counts."""
    rows = reg.all()
    chains = _chains(rows)
    by_root: dict[str, list[list[dict]]] = {}
    for ch in chains:
        by_root.setdefault(ch[-1]["instrument_norm"], []).append(ch)
    execs = xs.all() if hasattr(xs, "all") else xs
    out = {"executions": 0, "written": 0, "matched": 0, "breaks": []}
    # Net filled quantity per decision chain, to check side and size.
    filled: dict[str, float] = {}
    for e in sorted(execs, key=lambda x: str(x.get("exec_time") or "")):
        out["executions"] += 1
        root = instruments.normalise(e.get("instrument") or e.get("symbol"))
        eid = e.get("exec_id")
        when = str(e.get("exec_time") or "")
        # The decision in force when the fill happened: chains on the root whose
        # first row predates the fill, latest first.
        cands = [ch for ch in by_root.get(root, [])
                 if str(ch[0]["decision_time"]) <= when or not when]

        def brk(kind: str, reason: str, dec: Optional[dict] = None,
                **detail) -> None:
            new = reg.write_rule_break(
                kind=kind, session_day=session_day, reason=reason,
                dedupe_key=f"{kind}:{eid}", source=SOURCE,
                decision_id=(dec or {}).get("id"),
                instrument=e.get("instrument"), exec_ids=[eid],
                detail={"side": e.get("side"), "qty": e.get("qty"),
                        "sec_type": e.get("sec_type"), "exec_time": when,
                        **detail})
            out["breaks"].append({"kind": kind, "exec_id": eid, "reason": reason})
            out["written"] += int(new)

        if not cands:
            brk("unregistered_execution",
                f"{e.get('side')} {e.get('qty')} {e.get('instrument')} has no "
                f"decision on the register for {root}")
            continue
        # Prefer a chain that was accepted (reached active) at any point.
        accepted = [ch for ch in cands if any(r["status"] == "active" for r in ch)]
        if not accepted:
            head = cands[-1][-1]
            brk("execution_against_unaccepted",
                f"{e.get('side')} {e.get('qty')} {e.get('instrument')} filled "
                f"against a decision never accepted (status {head['status']}"
                + (f", blocked: {head['blocked_reason']}" if head.get("blocked_reason")
                   else "") + ")", head)
            continue
        chain = accepted[-1]
        dec = next(r for r in reversed(chain) if r["status"] in ("active", "closed"))
        why = expression_mismatch(dec, e.get("sec_type"))
        if why:
            brk("expression_mismatch", why, dec,
                expression_family=dec.get("expression_family"),
                leverage_form=dec.get("leverage_form"))
            continue
        sgn = {"BOT": 1, "SLD": -1}.get(str(e.get("side")).upper(), 0)
        want = {"long": 1, "short": -1}.get(dec.get("direction"), 0)
        key = chain[0]["id"]
        net = filled.get(key, 0.0) + sgn * float(e.get("qty") or 0) * (want or 1)
        filled[key] = net
        if want and net < -1e-9:
            brk("side_mismatch",
                f"{e.get('side')} takes the position past flat against a "
                f"{dec['direction']} decision -- net {net:+g} in the decision's "
                f"direction", dec, net_in_direction=net)
            continue
        qmax = dec.get("quantity")
        if qmax is not None and net > float(qmax) + 1e-9:
            brk("size_exceeded",
                f"filled {net:g} against a recorded quantity of {qmax:g}",
                dec, net_in_direction=net, quantity=qmax)
            continue
        out["matched"] += 1
    return out


def time_stops(reg: Any, session_day: str) -> list[dict]:
    out = []
    for d in reg.open_decisions():
        ts = d.get("time_stop")
        if ts and str(ts) < session_day:
            new = reg.write_rule_break(
                kind="time_stop_passed", session_day=session_day,
                reason=f"{d['instrument']} {d['direction']} (book "
                       f"{d.get('book') or 'unassigned'}) is still active past "
                       f"its time stop {ts}",
                dedupe_key=f"time_stop_passed:{d['id']}", source=SOURCE,
                decision_id=d["id"], instrument=d["instrument"],
                detail={"time_stop": ts})
            out.append({"decision_id": d["id"], "new": new})
    return out


def book_b_conversions(reg: Any, session_day: str, sessions: int = 2) -> list[dict]:
    from altdata import derived  # noqa: PLC0415
    out = []
    for ch in _chains(reg.all()):
        head = ch[-1]
        if head["status"] != "closed" or (head.get("book") or
                                          next((r.get("book") for r in ch
                                                if r.get("book")), None)) != "B":
            continue
        entry = next((r for r in ch if r["status"] == "active"), None)
        if entry is None:
            continue
        n, _ = derived.sessions_between(str(entry["decision_time"])[:10],
                                        str(head["decision_time"])[:10])
        reason_given = str(head.get("close_reason") or "").strip().lower()
        if n <= sessions and reason_given != "invalidation":
            new = reg.write_rule_break(
                kind="book_b_conversion", session_day=session_day,
                reason=f"Book B {head['instrument']} closed {n} session(s) after "
                       f"entry for "
                       + (f"'{head.get('close_reason')}'" if reason_given
                          else "no recorded reason")
                       + " -- not its invalidation",
                dedupe_key=f"book_b_conversion:{head['id']}", source=SOURCE,
                decision_id=head["id"], instrument=head["instrument"],
                detail={"entry": entry["decision_time"],
                        "closed": head["decision_time"], "sessions": n,
                        "close_reason": head.get("close_reason")})
            out.append({"decision_id": head["id"], "new": new})
    return out


def allocation_floor(reg: Any, store: Any, session_day: str,
                     as_of: Optional[str] = None) -> dict:
    """Book A's stance against its band's floor, or why it cannot be read."""
    from register import heat  # noqa: PLC0415
    ever_a = [r for r in reg.all() if r.get("book") == "A"]
    if not ever_a:
        return {"state": "not_yet_sourced",
                "reason": "no Book A decision has ever been recorded, so there is "
                          "no stance to hold to the floor -- a zero here would be "
                          "an assumption, not a reading"}
    open_a = [d for d in reg.open_decisions() if d.get("book") == "A"]
    v = heat.view(open_a, store, as_of)
    rb = v["regime"]
    if rb.get("floor_pct") is None:
        return {"state": "absent", "reason": rb.get("reason") or "no band"}
    stance = v["net_beta_pct"] or 0.0
    out = {"state": "ok", "stance_pct": stance, "floor_pct": rb["floor_pct"],
           "regime": rb.get("regime"), "mapping_proposed": rb.get("mapping_proposed")}
    if v["missing"]:
        out["state"] = "incomplete"
        out["missing"] = v["missing"]
        return out
    if stance < rb["floor_pct"]:
        new = reg.write_rule_break(
            kind="allocation_floor_breach", session_day=session_day,
            reason=f"Book A stance {stance:.1f}% of capital is below the "
                   f"{rb['regime']} band's floor of {rb['floor_pct']:g}%"
                   + (" (mapping proposed, unratified)"
                      if rb.get("mapping_proposed") else ""),
            dedupe_key=f"allocation_floor_breach:{session_day}", source=SOURCE,
            detail={"stance_pct": stance, "band": rb.get("band"),
                    "regime": rb.get("regime"),
                    "mapping_version": rb.get("mapping_version")})
        out["breach"] = True
        out["new"] = new
    return out


def run(session_day: Optional[str] = None, db_path: Optional[str] = None) -> dict:
    """Every source, once. Never raises past a source: each reports its own."""
    from altdata import executions, observations  # noqa: PLC0415
    from register.store import Register  # noqa: PLC0415
    day = session_day or session.last_trading_session().isoformat()
    out: dict[str, Any] = {"session": day}
    def _fills() -> dict:
        with executions.ExecutionStore(db_path) as xs:
            return reconcile_executions(reg, xs, day)

    with Register(db_path) as reg:
        for name, fn in (
                ("executions", _fills),
                ("time_stop_passed", lambda: time_stops(reg, day)),
                ("book_b_conversion", lambda: book_b_conversions(reg, day))):
            try:
                out[name] = fn()
            except Exception as exc:                          # noqa: BLE001
                log.exception("%s failed", name)
                out[name] = {"fault": f"{type(exc).__name__}: {exc}"}
        st = observations.ObservationStore(db_path)
        try:
            out["allocation_floor_breach"] = allocation_floor(reg, st, day)
        except Exception as exc:                              # noqa: BLE001
            log.exception("allocation floor failed")
            out["allocation_floor_breach"] = {"fault": f"{type(exc).__name__}: {exc}"}
        finally:
            st.close()
        out["breaks_this_session"] = reg.rule_breaks(since=day)
    return out


def _main(argv: list[str]) -> int:
    import argparse  # noqa: PLC0415
    import sys  # noqa: PLC0415
    ap = argparse.ArgumentParser(description="Reconcile fills and position rules.")
    ap.add_argument("--db", default=None)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--session", default=None)
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    out = run(a.session, a.db)
    ex = out.get("executions") or {}
    print(f"reconcile session {out['session']}: {ex.get('executions', 0)} fill(s), "
          f"{ex.get('matched', 0)} matched, {len(ex.get('breaks') or [])} break(s)")
    af = out.get("allocation_floor_breach") or {}
    print(f"  allocation floor : {af.get('state')}"
          + (f" -- {af.get('reason')}" if af.get("reason") else "")
          + (f" stance {af.get('stance_pct')}% floor {af.get('floor_pct')}%"
             if af.get("stance_pct") is not None else ""))
    for b in out["breaks_this_session"]:
        print(f"  RULE BREAK {b['kind']:<28} {b['reason']}")
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
