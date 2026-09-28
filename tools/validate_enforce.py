#!/usr/bin/env python3
"""
Validation gate for Phase 5a: the register enforced by reconciliation, and the
cross-book heat/factor view.

    python tools/validate_enforce.py

Against a TEMPORARY database with synthetic prices, a synthetic market-state
history and synthetic fills. No network, no Gateway.

  A  THE FOUR-PACKET ACCEPTANCE TEST (EL-2, change order §3.2): long NVDA (Book C),
     long QQQ (Book B), long NVDA (Book A), short Nasdaq vol (options). Each is
     sensible alone; the gate must name the technology and the vega concentration
     they sum to, and answer approve, approve, resize, restructure.
  B  EVERY GATE OUTCOME is reachable, and each by its stated rule: delay on a
     missing input, hedge on net beta with no useful size, reject on a sector with
     no useful size. The regime band follows the Doctrine's crossing rule.
  C  THE REGISTER ENFORCES THE GATE: an active decision names its book; a gate
     verdict other than approve holds it at draft unless the operator's override
     is recorded; rule breaks are immutable and written once.
  D  RECONCILIATION: every fill matches an accepted decision in instrument, side,
     size and expression, or is a rule break with its reason.
  E  THE DOCTRINE'S POSITION RULES: time stop, Book B conversion, Book A's floor.
  F  BINDING EXPRESSION AT ENTRY, through the operator's CLI in dry run.
  G  THE BREAKS REACH THE CLOSE, THE WEEKLY AND THE GRADER.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import random
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_TMP = tempfile.mkdtemp(prefix="validate_enforce_")
DB = os.path.join(_TMP, "enforce.sqlite")
os.environ["CHESTER_DB"] = DB
os.environ.setdefault("CHESTER_STATE_DIR", _TMP)

import regime  # noqa: E402
from altdata import executions, observations  # noqa: E402
from register import heat, reconcile  # noqa: E402
from register.store import Register  # noqa: E402

PASS = 0
FAIL = 0
LINE = "=" * 78


def ok(m: str) -> None:
    global PASS
    PASS += 1
    print(f"  PASS  {m}")


def bad(m: str) -> None:
    global FAIL
    FAIL += 1
    print(f"  FAIL  {m}")


def check(c: bool, m: str) -> None:
    ok(m) if c else bad(m)


END = dt.date(2026, 9, 25)


def weekdays(n: int, end: dt.date = END) -> list[str]:
    out, d = [], end
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d -= dt.timedelta(days=1)
    return list(reversed(out))


def seed_prices(store) -> None:
    """SPY a random walk; QQQ 1.2x and NVDA 2x its returns, plus noise."""
    rnd = random.Random(7)
    days = weekdays(300)
    px = {"spy": 600.0, "qqq": 500.0, "nvda": 180.0}
    rows = []
    for d in days:
        r = rnd.gauss(0.0004, 0.01)
        px["spy"] *= 1 + r
        px["qqq"] *= 1 + 1.2 * r + rnd.gauss(0, 0.002)
        px["nvda"] *= 1 + 2.0 * r + rnd.gauss(0, 0.004)
        for k, v in px.items():
            rows.append({"registry_key": f"yfinance.mkt_{k}", "instrument": None,
                         "observed_at": d, "available_at": f"{d}T21:00:00+00:00",
                         "value": round(v, 4), "source": "synthetic"})
    store.write_many(rows)


def seed_objects(store, states: list[str]) -> None:
    """One market-state object per session with the given Macro dial states."""
    days = weekdays(len(states))
    for d, s in zip(days, states):
        obj = {"object": "market_state", "session": d,
               "computed_at": f"{d}T20:50:00+00:00",
               "dials": {"macro": {"state": s}}, "dimensions": {},
               "contradictions": []}
        store.write(regime.STORE_KEY, None, d, obj["computed_at"],
                    json.dumps(obj), source="derived_state")


def pkt(i, root, book, direction, notional, fam="outright", vega=None):
    return {"id": f"p{i}", "instrument": root, "book": book,
            "direction": direction, "notional_usd": notional,
            "vega_usd": vega, "expression_family": fam, "leverage_form": "none"}


# ---------------------------------------------------------------------------
def group_a(store) -> None:
    print(f"{LINE}\nA. THE FOUR-PACKET ACCEPTANCE TEST (EL-2 §3.2)\n{LINE}")
    lim = heat.load_limits()
    check((lim["capital_usd"]["value"] == 300000
           and lim["limits"]["net_beta_over_band_top_pct"]["source"] == "doctrine"
           and all(lim["limits"][k].get("proposed")
                   for k in ("sector_max_pct", "vega_max_pct_per_vol_pt",
                             "duration_max_pct_per_100bp"))),
          "config/risk_limits.yaml: the Doctrine's net-beta cap, and every other "
          "limit marked proposed until the operator rules")
    b = heat.beta_vs_spy("NVDA", store)
    check(b["beta"] is not None and 1.8 < b["beta"] < 2.2,
          f"NVDA's beta is COMPUTED from stored returns (~2 by construction; "
          f"got {b['beta']} on {b['n']} returns)")

    book: list[dict] = []
    outcomes = []
    packets = [pkt(1, "NVDA", "C", "long", 30000),
               pkt(2, "QQQ", "B", "long", 50000),
               pkt(3, "NVDA", "A", "long", 30000),
               pkt(4, "QQQ", "D", "short", 0.0, fam="iron_condor", vega=-2500)]
    last = None
    for p in packets:
        g = heat.gate(p, book, store)
        outcomes.append(g["outcome"])
        accepted = dict(p)
        if g["outcome"] == "resize":
            accepted["notional_usd"] = p["notional_usd"] * g["resize_factor"]
        if g["outcome"] in ("approve", "resize"):
            book.append(accepted)
        last = g
        print(f"        {p['instrument']:<5} book {p['book']} -> {g['outcome']}"
              + (f" ({g['resize_factor']:.0%})" if g.get("resize_factor") else "")
              + f": {g['reasons'][0]}")
    check(outcomes == ["approve", "approve", "resize", "restructure"],
          f"the gate answers approve, approve, resize, restructure ({outcomes})")
    v = last["view_after"]
    conc = " | ".join(v["concentrations"])
    check("technology" in conc,
          f"the view NAMES the technology concentration ({conc})")
    check("vega" in conc and "QQQ" in conc,
          "and the vega concentration, in the underlying that carries it")
    check(set(v["beta_by_book_usd"]) >= {"A", "B", "C"},
          f"summed across books ({', '.join(sorted(v['beta_by_book_usd']))})")
    third = heat.gate(packets[2], book[:2], store)
    check(third["resize_factor"] == 0.5
          and any("technology" in r for r in third["reasons"]),
          "the third packet fits at 50%: the room left under the technology "
          "limit, and the reason says so")
    print("\n" + "\n".join("        " + ln for ln in
                           heat.format_view(v).splitlines()))


def group_b(store) -> None:
    print(f"{LINE}\nB. EVERY OUTCOME, BY ITS RULE\n{LINE}")
    g = heat.gate(pkt(9, "NVDA", "B", "long", None), [], store)
    check(g["outcome"] == "delay" and "notional" in g["reasons"][0],
          "no structured size -> delay")
    g = heat.gate(pkt(9, "QQQ", "D", "short", 0.0, fam="iron_condor"), [], store)
    check(g["outcome"] == "delay" and "vega" in g["reasons"][0],
          "an options expression with no vega -> delay, not a guess")
    g = heat.gate(pkt(9, "AAPL", "B", "long", 10000), [], store)
    check(g["outcome"] == "delay" and "price basket" in g["reasons"][0],
          "a name the store does not carry has no beta -> delay")
    # Net beta: expansion band 60-80, cap 95% = $285,000 beta-adjusted.
    big = [pkt(20, "SPY", "A", "long", 280000)]
    g = heat.gate(pkt(21, "SPY", "B", "long", 20000), big, store)
    check(g["outcome"] == "hedge",
          f"net beta past the Doctrine cap with no useful size -> hedge "
          f"({g['outcome']}: {g['reasons'][0][:60]})")
    g = heat.gate(pkt(22, "NVDA", "B", "long", 5000),
                  [pkt(23, "NVDA", "C", "long", 74000)], store)
    check(g["outcome"] == "reject",
          f"a sector past its limit with no useful size -> reject "
          f"({g['outcome']})")
    g = heat.gate(pkt(24, "SPY", "B", "long", 10000), [], store)
    check(g["outcome"] == "approve", "inside every limit -> approve")

    rb = heat.regime_band(store)
    check(rb["regime"] == "Expansion" and rb["band"] == [60, 80]
          and rb["cap_pct"] == 95 and rb["mapping_proposed"],
          f"expansion -> Expansion, band 60-80, cap 95%, mapping marked proposed "
          f"({rb.get('regime')}, {rb.get('band')}, {rb.get('cap_pct')})")
    with tempfile.TemporaryDirectory() as td:
        st2 = observations.ObservationStore(os.path.join(td, "t.db"))
        try:
            seed_objects(st2, ["late_cycle"] * 8 + ["expansion"] * 4)
            t = heat.regime_band(st2)
            check(t["regime"] == "Transition" and t["departing"] == "Overheat"
                  and t["band"] == [40, 50] and t["cap_pct"] == 65,
                  f"a dial that changed 4 sessions ago is Transition: the lower "
                  f"half of the band it left (Overheat 40-60 -> 40-50, cap 65%) "
                  f"({t.get('regime')}, {t.get('band')})")
        finally:
            st2.close()


def group_c() -> None:
    print(f"{LINE}\nC. THE REGISTER ENFORCES THE GATE\n{LINE}")
    base = dict(instrument="SPY", direction="long", thesis="t", edge_type="e",
                horizon="swing", invalidation="x", expression_family="outright",
                leverage_form="none")
    with Register(DB) as reg:
        try:
            reg.record(status="active", **base)
            bad("an active decision with no book was accepted")
        except ValueError:
            ok("an active decision with no book is refused")
        d = reg.record(status="active", book="B", gate_outcome="resize", **base)
        r = reg.get(d)
        check(r["status"] == "draft" and "gate at entry: resize" in
              (r["blocked_reason"] or ""),
              "a gate verdict other than approve holds it at draft, with the reason")
        d2 = reg.record(status="active", book="B", gate_outcome="reject",
                        gate_override="operator: hedged elsewhere", **base)
        r2 = reg.get(d2)
        check(r2["status"] == "active" and r2["gate_override"],
              "with the operator's override it is active -- and the override is "
              "on the row")
        new = reg.write_rule_break(kind="time_stop_passed", session_day="2026-09-25",
                                   reason="x", dedupe_key="k1", source="t")
        again = reg.write_rule_break(kind="time_stop_passed",
                                     session_day="2026-09-25", reason="x",
                                     dedupe_key="k1", source="t")
        check(new and not again, "a rule break is written once per dedupe key")
        try:
            reg.conn.execute("UPDATE rule_breaks SET reason='edited'")
            bad("a rule break was editable")
        except Exception:                                      # noqa: BLE001
            ok("rule_breaks is immutable by trigger")


def group_d() -> None:
    print(f"{LINE}\nD. RECONCILIATION: EVERY FILL AGAINST AN ACCEPTED DECISION\n{LINE}")
    t0 = "2026-09-24T14:00:00+00:00"
    with Register(DB) as reg:
        acc = reg.record(instrument="XLE", direction="long", thesis="t",
                         edge_type="e", horizon="swing", invalidation="x",
                         status="active", book="B", quantity=100,
                         expression_family="outright", leverage_form="none",
                         decision_time=t0)
        reg.record(instrument="XLU", direction="long", thesis="t", edge_type="e",
                   horizon="swing", invalidation="x", status="draft",
                   decision_time=t0)
        reg.record(instrument="XLF", direction="long", thesis="t", edge_type="e",
                   horizon="swing", invalidation="x", status="active", book="C",
                   expression_family="vertical_spread", leverage_form="call_spread",
                   decision_time=t0)

    def fill(eid, inst, side, qty, sec="STK", when="2026-09-25T15:00:00+00:00"):
        return {"exec_id": eid, "instrument": inst, "symbol": inst.split("@")[0],
                "side": side, "qty": qty, "sec_type": sec, "exec_time": when,
                "price": 10.0}

    # Portfolio Truth's snapshot before the fills: flat in XLE and XLF, and an
    # XLP long of 100 whose opening fills predate the executions table.
    snap = "2026-09-25T13:30:00+00:00"
    st = observations.ObservationStore(DB)
    try:
        st.write_many([{"registry_key": "portfolio.nav", "instrument": "DU1",
                        "observed_at": snap, "available_at": snap,
                        "value": 300000.0, "source": "ibkr"},
                       {"registry_key": "portfolio.position_qty",
                        "instrument": "XLP@ARCA.USD", "observed_at": snap,
                        "available_at": snap, "value": 100.0, "source": "ibkr"}])
    finally:
        st.close()
    with Register(DB) as reg:
        reg.record(instrument="XLP", direction="long", thesis="t", edge_type="e",
                   horizon="swing", invalidation="x", status="active", book="B",
                   quantity=100, expression_family="outright",
                   leverage_form="none", decision_time=t0)
    with executions.ExecutionStore(DB) as xs:
        xs.write_many([
            fill("e0", "XLP@ARCA.USD", "SLD", 100),        # the exit of a held long
            fill("e1", "XLE@ARCA.USD", "BOT", 60),
            fill("e2", "XLE@ARCA.USD", "BOT", 60),           # past quantity 100
            fill("e3", "XLV@ARCA.USD", "BOT", 10),           # no decision
            fill("e4", "XLU@ARCA.USD", "BOT", 10),           # draft only
            fill("e5", "XLF@ARCA.USD", "BOT", 10, "STK"),    # spread filled as stock
        ])
    out = reconcile.run("2026-09-25", DB)
    kinds = {b["exec_id"]: b["kind"] for b in out["executions"]["breaks"]}
    check("e1" not in kinds, "a fill inside an accepted decision matches")
    check("e0" not in kinds,
          "an exit of a position opened before the executions table is an exit, "
          "not a side mismatch: the count starts from Portfolio Truth's snapshot "
          "(the 24 Sep SPY case)")
    check(kinds.get("e2") == "size_exceeded",
          "fills past the recorded quantity -> size_exceeded")
    check(kinds.get("e3") == "unregistered_execution",
          "a fill with no decision -> unregistered_execution")
    check(kinds.get("e4") == "execution_against_unaccepted",
          "a fill against a draft -> execution_against_unaccepted")
    check(kinds.get("e5") == "expression_mismatch",
          "a vertical spread filled as stock -> expression_mismatch")
    with executions.ExecutionStore(DB) as xs:
        xs.write_many([fill("e6", "XLE@ARCA.USD", "SLD", 200,
                            when="2026-09-25T16:00:00+00:00")])
    out2 = reconcile.run("2026-09-25", DB)
    k2 = {b["exec_id"]: b["kind"] for b in out2["executions"]["breaks"]}
    check(k2.get("e6") == "side_mismatch",
          "selling past flat on a long decision -> side_mismatch")
    with Register(DB) as reg:
        n_before = len(reg.rule_breaks())
    reconcile.run("2026-09-25", DB)
    with Register(DB) as reg:
        check(len(reg.rule_breaks()) == n_before,
              "a second run writes nothing new -- the sync and the close both run it")
    check(reconcile.expression_mismatch({"expression_family": "outright",
                                         "leverage_form": "none"}, "OPT")
          and reconcile.expression_mismatch({"expression_family": "outright",
                                             "leverage_form": "none"}, "FUT")
          and not reconcile.expression_mismatch(
              {"expression_family": "covered_call", "leverage_form": "none"}, "STK"),
          "options on an outright and futures without futures leverage mismatch; "
          "stock inside a covered call does not")


def group_e(store) -> None:
    print(f"{LINE}\nE. THE DOCTRINE'S POSITION RULES\n{LINE}")
    with Register(DB) as reg:
        r = reconcile.allocation_floor(reg, store, "2026-09-25")
        check(r["state"] == "not_yet_sourced",
              "with no Book A decision the floor is not_yet_sourced, not a zero")
        reg.record(instrument="SPY", direction="long", thesis="t", edge_type="e",
                   horizon="strategic", invalidation="x", status="active",
                   book="A", notional_usd=60000, expression_family="outright",
                   leverage_form="none")
        r = reconcile.allocation_floor(reg, store, "2026-09-25")
        check(r.get("breach") and r["stance_pct"] == 20.0 and r["floor_pct"] == 60,
              f"Book A at 20% of capital under an Expansion floor of 60% is a "
              f"breach ({r.get('stance_pct')} vs {r.get('floor_pct')})")
        ts = reg.record(instrument="XLI", direction="long", thesis="t",
                        edge_type="e", horizon="swing", invalidation="x",
                        status="active", book="B", time_stop="2026-09-20",
                        expression_family="outright", leverage_form="none")
        hit = reconcile.time_stops(reg, "2026-09-25")
        check(any(h["decision_id"] == ts for h in hit),
              "an active decision past its time stop -> time_stop_passed")
        entry = reg.record(instrument="XLB", direction="long", thesis="t",
                           edge_type="e", horizon="swing", invalidation="x",
                           status="active", book="B",
                           expression_family="outright", leverage_form="none",
                           decision_time="2026-09-23T14:00:00+00:00")
        reg.supersede(entry, instrument="XLB", direction="long", thesis="t",
                      edge_type="e", horizon="swing", invalidation="x",
                      status="closed", book="B", close_reason="bored",
                      decision_time="2026-09-24T14:00:00+00:00")
        e2 = reg.record(instrument="XLRE", direction="long", thesis="t",
                        edge_type="e", horizon="swing", invalidation="x",
                        status="active", book="B",
                        expression_family="outright", leverage_form="none",
                        decision_time="2026-09-23T14:00:00+00:00")
        reg.supersede(e2, instrument="XLRE", direction="long", thesis="t",
                      edge_type="e", horizon="swing", invalidation="x",
                      status="closed", book="B", close_reason="invalidation",
                      decision_time="2026-09-24T14:00:00+00:00")
        conv = reconcile.book_b_conversions(reg, "2026-09-25")
        insts = {reg.get(c["decision_id"])["instrument"] for c in conv}
        check(insts == {"XLB"},
              f"a Book B close one session in for 'bored' is a conversion; one for "
              f"its invalidation is not ({sorted(insts)})")


def group_f() -> None:
    print(f"{LINE}\nF. BINDING EXPRESSION AT ENTRY (decide.py, dry run)\n{LINE}")
    base = ["record", "--instrument", "SPY", "--direction", "long",
            "--thesis", "t", "--edge-type", "positioning", "--horizon", "swing",
            "--invalidation", "x", "--signals-used", "yfinance.mkt_spy",
            "--status", "active", "--dry-run"]

    # IN-PROCESS, with the signal check answered "fresh": the binding rules sit
    # behind 26.2 #7's freshness gate (a blocked request is recorded as an
    # abstention, never refused), so they are exercised on a fresh request.
    import contextlib
    import io
    sys.path.insert(0, str(REPO / "tools"))
    import decide

    def fresh(signals, instrument):
        return {"verdicts": [], "blocked": False, "blocked_reason": None,
                "stale": []}
    decide.freshness.check_signals = fresh

    class R:
        def __init__(self, rc, out):
            self.returncode, self.stdout = rc, out

    def cli(*extra):
        buf = io.StringIO()
        argv = sys.argv
        sys.argv = ["decide.py", "--db", DB, *base, *extra]
        try:
            with contextlib.redirect_stdout(buf):
                rc = decide.main()
        finally:
            sys.argv = argv
        return R(rc, buf.getvalue())
    r = cli()
    check(r.returncode == 2 and "names its book" in r.stdout,
          "active with no --book is refused")
    r = cli("--book", "B")
    check(r.returncode == 2 and "expression-family" in r.stdout,
          "active with no --expression-family is refused -- the check is binding")
    r = cli("--book", "B", "--expression-family", "outright",
            "--leverage-form", "none", "--sec-type", "OPT")
    check(r.returncode == 2 and "not an options family" in r.stdout,
          "--sec-type OPT with an outright family is refused")
    r = cli("--book", "B", "--expression-family", "outright",
            "--leverage-form", "none", "--notional", "10000")
    check("order gate at entry" in r.stdout and "GATE:" in r.stdout,
          "a complete decision reaches the gate, which prints the cross-book view")
    check("--override-gate" not in r.stdout or "OPERATOR" in r.stdout,
          "an override is offered to the operator, never taken by the tool")


def group_g(store) -> None:
    print(f"{LINE}\nG. THE BREAKS REACH THE CLOSE, THE WEEKLY AND THE GRADER\n{LINE}")
    from altdata import grader
    from daily_cascade import payload as close_payload
    from daily_cascade import render as close_render
    from daily_cascade import weekly_payload as wp
    e = close_payload.enforcement_block("2026-09-25")
    html = close_render.enforcement_block({"enforcement": e})
    check(e["state"] == "ok" and len(e["rule_breaks"]) >= 5
          and "unregistered_execution" in html and "HEAT / FACTOR VIEW" in html,
          f"the close prints this session's rule breaks and the view "
          f"({len(e.get('rule_breaks') or [])} breaks)")
    wk = wp._rule_breaks_week("2026-09-21", "2026-09-25")
    check(wk["rule_breaks_this_week"]["size_exceeded"] >= 1
          and not wk["not_yet_sourced"],
          "the Weekly counts them by kind, and the floor is sourced once Book A "
          "exists")
    with Register(DB) as reg:
        xle = next(r for r in reg.all() if r["instrument"] == "XLE")
    rbs = grader.rule_breaks_for(xle["id"], DB)
    check({b["kind"] for b in rbs} >= {"size_exceeded", "side_mismatch"},
          f"the grader reads the breaks against the decision's chain "
          f"({sorted({b['kind'] for b in rbs})})")


def main() -> int:
    print(f"{LINE}\nPhase 5a -- the register enforced; the heat view cross-book\n{LINE}")
    store = observations.ObservationStore(DB)
    try:
        seed_prices(store)
        seed_objects(store, ["expansion"] * 12)
        for g in (lambda: group_a(store), lambda: group_b(store), group_c,
                  group_d, lambda: group_e(store), group_f,
                  lambda: group_g(store)):
            try:
                g()
            except Exception as exc:                           # noqa: BLE001
                import traceback
                traceback.print_exc()
                bad(f"a group raised {type(exc).__name__}: {exc}")
    finally:
        store.close()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
