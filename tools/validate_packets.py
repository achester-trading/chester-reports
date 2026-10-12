"""
Validation gate for EL-1: the Decision Packet as a decision object, Red Team v0,
the setup catalogue, and the write-time refusal (docs/change-order-enterprise-
layer-2026-09-27.md §3.1, R-5 and §3.6; docs/briefs/enterprise-layer-spec-
2026-09-27.md §VII and §XI).

Fixtures only: every register here is a temporary database. It never opens the
live register and never records a decision anywhere but its own scratch file.

  A COMPLETE    a complete packet is DECISION_OK, every field on the row, the
                outcome slot empty
  B MISSING     each entry field removed in turn refuses DECISION_OK, names the
                field, and logs the refusal; a draft may be incomplete
  C RED TEAM    the Red Team line's two parts -- the cheapest way the thesis
                could be wrong, and the review time to check it -- are each
                required, and the refusal quotes the rule (R-5)
  D FALSIFIER   the falsifier is measurable and dated, the date not before the
                decision
  E BLOCKLIST   a Brookfield-complex instrument is refused before anything else,
                in Python and by the SQLite trigger, and the attempt logged
  F SETUP       an unknown setup_id refuses and is logged; the catalogue: every
                family an experiment with mechanism, base rate, edge, target N
                and the order's fixed kill criterion; the Weekly's tells seeded
                as stubs; no family the register knew has been removed
  G CLI         decide.py record and set-status refuse with the reason and log
                it -- never an argparse error that leaves no record
  H MIGRATION   a register written before these columns opens, its rows
                readable, every new field NULL ("not recorded"); the refusal log
                is immutable

    python tools/validate_packets.py
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import sqlite3
import sys
from pathlib import Path

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import gate_tmp                                                # noqa: E402

TD = Path(gate_tmp.mkdtemp("packets_"))
os.environ["CHESTER_DB"] = str(TD / "never_the_live_register.db")

import yaml                                                    # noqa: E402

from packet_fixture import PACKET                              # noqa: E402
from register import store as rs                               # noqa: E402
from register.store import (PacketIncompleteError,             # noqa: E402
                            PacketRefusedError, Register,
                            RestrictedInstrumentError)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LINE = "=" * 78
PASS = FAIL = 0


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


def refused(fn, exc=PacketRefusedError) -> str | None:
    """The refusal's message, or None when nothing was refused."""
    try:
        fn()
    except exc as e:
        return str(e)
    return None


# A complete DECISION_OK packet.
BASE = dict(instrument="SPY@ARCA.USD", direction="long", edge_type="positioning",
            book="B", expression_family="outright", leverage_form="none",
            expression_currency="USD")
COMPLETE = dict(
    thesis="Dealers are long gamma into the pin; SPY mean-reverts toward 760.",
    falsifiers=["SPY settles below 745 before 2099-12-31"],
    setup_id="c_pin_fade", invalidation="a settled close below 745",
    size="100 shares", horizon="swing",
    counter_thesis="A macro print can flip dealer gamma and the pin will not hold.",
    **PACKET)


def reg_at(name: str) -> Register:
    return Register(str(TD / f"{name}.db"))


# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. A COMPLETE PACKET IS DECISION_OK")
    with reg_at("a") as reg:
        did = reg.record(status="active", **BASE, **COMPLETE)
        row = reg.get(did)
    want = {k: v for k, v in COMPLETE.items() if k != "falsifiers"}
    check(row["status"] == "active"
          and all(str(row[k]) == str(v) for k, v in want.items())
          and json.loads(row["falsifiers"]) == COMPLETE["falsifiers"],
          "a complete packet is recorded active, every field on the row as written")
    check(row["outcome"] is None and row["outcome_at"] is None
          and row["decision_time"] and row["review_changed"] is None,
          "the outcome slot is empty at entry, the decision timestamp set, the "
          "review_changed slot present")
    names = {c for c, _ in rs.ENTRY_FIELDS}
    check(names == {"thesis", "mechanism", "falsifiers", "falsifier_date",
                    "setup_id", "expected_return", "expected_downside",
                    "entry_condition", "invalidation", "size", "risk_budget",
                    "horizon", "benchmark", "red_team", "red_team_review_minutes",
                    "counter_thesis"},
          f"the entry fields are the brief's list and §3.1's ({len(names)})")


def group_b() -> None:
    head("B. EACH MISSING FIELD REFUSES, NAMED AND LOGGED")
    bad = []
    with reg_at("b") as reg:
        for col, _ in rs.ENTRY_FIELDS:
            kw = dict(COMPLETE)
            if col == "horizon":
                kw["horizon"] = "swing"      # a NOT NULL column: test blank text
                continue
            if col in ("thesis", "invalidation"):
                kw[col] = "   "
            else:
                kw.pop(col)
            n0 = len(reg.packet_refusals())
            msg = refused(lambda kw=kw: reg.record(status="active", **BASE, **kw),
                          PacketIncompleteError)
            logged = reg.packet_refusals()[n0:]
            if not (msg and f"{col} (" in msg and len(logged) == 1
                    and logged[0]["rule"] == "incomplete_packet"
                    and logged[0]["reason"] == msg):
                bad.append(col)
        check(not bad, f"each of the {len(rs.ENTRY_FIELDS) - 1} removable fields, "
                       f"removed in turn, refuses DECISION_OK, names itself and "
                       f"logs one refusal ({bad})")
        msg = refused(lambda: reg.record(status="active", **BASE,
                                         **{**COMPLETE, "horizon": " "}),
                      (PacketIncompleteError, ValueError, sqlite3.IntegrityError))
        check(msg is not None, "a blank horizon is refused (a closed vocabulary)")
        kw = {k: v for k, v in COMPLETE.items() if k != "size"}
        ok_q = reg.record(status="active", quantity=100, **BASE, **kw)
        check(reg.get(ok_q)["status"] == "active",
              "the size may be given as a quantity (or a notional)")
        empty = reg.record(status="draft", instrument="SPY@ARCA.USD",
                           direction="long", thesis="t", edge_type="e",
                           horizon="swing", invalidation="x")
        check(reg.get(empty)["status"] == "draft",
              "a DRAFT may be incomplete -- the rule binds at DECISION_OK")
        n0 = len(reg.packet_refusals())
        msg = refused(lambda: reg.set_status(empty, "active"), PacketIncompleteError)
        check(msg and "cannot be made active" in msg
              and len(reg.packet_refusals()) == n0 + 1
              and reg.packet_refusals()[-1]["source"] == "set_status",
              "the in-place writer cannot promote it, and the refusal is logged")
        held = reg.record(status="active", gate_outcome="resize", **BASE,
                          thesis="t", horizon="swing", invalidation="x")
        check(reg.get(held)["status"] == "draft",
              "a gate-held request lands as draft (not DECISION_OK), unrefused")


def group_c() -> None:
    head("C. RED TEAM v0: BOTH PARTS, THE RULE QUOTED")
    with reg_at("c") as reg:
        for drop, why in (("red_team", "the cheapest way the thesis could be wrong"),
                          ("red_team_review_minutes", "the review time")):
            kw = {k: v for k, v in COMPLETE.items() if k != drop}
            msg = refused(lambda kw=kw: reg.record(status="active", **BASE, **kw),
                          PacketIncompleteError)
            check(msg and f"{drop} (" in msg and rs.RED_TEAM_RULE in msg,
                  f"without {why}: refused, and the message quotes the rule "
                  f"(\"{rs.RED_TEAM_RULE[:48]}...\")")
        for val in (0, -5, "fifteen", 7.5):
            msg = refused(lambda val=val: reg.record(
                status="active", **BASE, **{**COMPLETE, "red_team_review_minutes": val}),
                PacketIncompleteError)
            check(msg and "red_team_review_minutes (" in msg,
                  f"a review time of {val!r} is not a positive whole number of "
                  f"minutes -- refused")
        msg = refused(lambda: reg.record(status="active", **BASE,
                                         **{**COMPLETE, "red_team": "  "}),
                      PacketIncompleteError)
        check(msg and "red_team (" in msg, "a blank Red Team line is no line")
    check(rs.RED_TEAM_RULE.startswith("Red Team v0 (R-5)")
          and "cheapest way the conclusion could be wrong" in rs.RED_TEAM_RULE
          and "stated cost in review time" in rs.RED_TEAM_RULE,
          "the rule is R-5's objective in the order's own words")
    order = (REPO / "docs" / "change-order-enterprise-layer-2026-09-27.md").read_text(
        encoding="utf-8")
    check("the cheapest way the conclusion could be wrong, at a stated cost in "
          "review time" in order,
          "and those words are R-5's, in the filed order")


def group_d() -> None:
    head("D. THE FALSIFIER: MEASURABLE AND DATED")
    with reg_at("d") as reg:
        msg = refused(lambda: reg.record(
            status="active", **BASE, **{**COMPLETE, "falsifiers": ["the thesis fails"]}),
            PacketIncompleteError)
        check(msg and "none is measurable" in msg,
              "a falsifier naming no level, count or date is refused")
        for val, why in (("31 Dec 2099", "not YYYY-MM-DD"),
                         ("2001-01-01", "before the decision")):
            msg = refused(lambda val=val: reg.record(
                status="active", **BASE, **{**COMPLETE, "falsifier_date": val}),
                PacketIncompleteError)
            check(msg and why in msg, f"a falsifier date {val!r} is refused: {why}")


def group_e() -> None:
    head("E. THE BLOCKLIST, FIRST")
    with reg_at("e") as reg:
        n0 = len(reg.blocked_attempts())
        msg = refused(lambda: reg.record(status="active",
                                         **{**BASE, "instrument": "BN"}, **COMPLETE),
                      RestrictedInstrumentError)
        check(msg and "No recommendation may be written" in msg
              and len(reg.blocked_attempts()) == n0 + 1,
              "a complete packet on BN (the Brookfield complex) is refused and the "
              "attempt logged to blocked_attempts")
        msg = refused(lambda: reg.record(status="draft", **{**BASE, "instrument": "BAM"},
                                         thesis="t", horizon="swing", invalidation="x",
                                         setup_id="no_such_setup"),
                      RestrictedInstrumentError)
        check(msg is not None, "the blocklist speaks before any other refusal (an "
                               "unknown setup on BAM is refused as BAM)")
        with contextlib.suppress(Exception):
            reg.conn.execute(
                "INSERT INTO decisions (id, created_at, decision_time, instrument,"
                " instrument_norm, direction, thesis, edge_type, horizon,"
                " invalidation, status) VALUES ('raw','x','x','BEP','BEP','long',"
                "'t','e','swing','x','draft')")
        check(reg.get("raw") is None,
              "a raw SQLite insert of BEP, bypassing Python, is refused by the "
              "trigger")


def group_f() -> None:
    head("F. THE SETUP CATALOGUE")
    with reg_at("f") as reg:
        n0 = len(reg.packet_refusals())
        msg = refused(lambda: reg.record(status="draft", **BASE,
                                         **{**COMPLETE, "setup_id": "no_such_setup"}))
        log = reg.packet_refusals()[n0:]
        check(msg and "not in the catalogue" in msg and len(log) == 1
              and log[0]["rule"] == "unknown_setup"
              and log[0]["setup_id"] == "no_such_setup",
              "an unknown setup_id is refused -- even on a draft -- and logged")
        ok = reg.record(status="active", **BASE, **{**COMPLETE,
                                                    "setup_id": "unclassified"})
        check(reg.get(ok)["status"] == "active", "`unclassified` is allowed")
    cat = yaml.safe_load((REPO / "config" / "setups.yaml").read_text(encoding="utf-8"))
    sp = cat["setups"]
    order = (REPO / "docs" / "change-order-enterprise-layer-2026-09-27.md").read_text(
        encoding="utf-8")
    kill = " ".join(cat["kill_criterion"].split())
    check(kill.replace(">=", "≥").replace("<=", "≤").lower().rstrip(".")
          in " ".join(order.split()).lower(),
          f"the kill criterion is the order's, fixed (§3.6): \"{kill}\"")
    exp = [k for k in sp if k != "unclassified"]
    bad = [k for k in exp
           if not (sp[k].get("mechanism") and sp[k].get("claimed_edge")
                   and (sp[k].get("base_rate") == "not yet"
                        or str(sp[k].get("base_rate")).startswith(("baserate.",
                                                                    "claim:")))
                   and int(sp[k].get("target_n") or 0) >= cat["min_target_n"] >= 40
                   and sp[k].get("kill") == "fixed"
                   and sp[k].get("status") in ("stub", "complete")
                   and sp[k].get("book") in ("A", "B", "C", "D"))]
    check(not bad, f"every one of the {len(exp)} families is an experiment: "
                   f"mechanism, base rate (cited by id or 'not yet'), claimed edge, "
                   f"target N >= 40, the fixed kill criterion, a status ({bad})")
    stubs = [k for k in exp if sp[k]["status"] == "stub"]
    check({"b_style_regime_pair", "b_consumer_rs_tell", "c_pin_fade",
           "c_negative_gamma_continuation"} <= set(stubs)
          and all(sp[k]["mechanism"].startswith("STUB") for k in stubs),
          f"the Weekly's tells -- the style-regime pair, the consumer RS tell, the "
          f"dealer-regime setups -- are seeded, and every entry is marked stub for "
          f"Doctrine #2 ({len(stubs)} stubs)")
    known = {"a_stance_rebalance", "a_tb_override", "b_breakout", "b_reclaim",
             "b_failed_breakdown", "c_pin_fade", "c_negative_gamma_continuation",
             "c_event_reaction", "d_behavioral_alert", "d_forced_flow",
             "d_prediction_market_divergence", "d_squeeze_exhaustion",
             "d_tail_hedge", "unclassified"}
    check(known <= set(sp) and set(rs.setup_ids()) == set(sp),
          "no family the register knew is removed (packets citing it still "
          "resolve), and the register reads the same catalogue")


def group_g() -> None:
    head("G. decide.py REFUSES WITH THE REASON, AND LOGS IT")
    import decide
    db = str(TD / "cli.db")
    decide.freshness.check_signals = lambda s, i: {
        "verdicts": [], "blocked": False, "blocked_reason": None, "stale": []}

    def cli(*argv) -> tuple[int, str]:
        buf = io.StringIO()
        saved = sys.argv
        sys.argv = ["decide.py", "--db", db, *argv]
        try:
            with contextlib.redirect_stdout(buf):
                rc = decide.main()
        finally:
            sys.argv = saved
        return rc, buf.getvalue()
    base = ["record", "--instrument", "SPY@ARCA.USD", "--direction", "long",
            "--thesis", "t", "--edge-type", "positioning", "--horizon", "swing",
            "--invalidation", "a close below 745", "--signals-used", "yfinance.mkt_spy",
            "--status", "active", "--book", "B", "--expression-family", "outright",
            "--leverage-form", "none"]
    rc, out = cli(*base, "--setup", "no_such_setup")
    with Register(db) as reg:
        log = reg.packet_refusals()
    check(rc == 2 and "not in the catalogue" in out and log
          and log[-1]["rule"] == "unknown_setup" and log[-1]["source"] == "decide.py",
          "decide.py record with an unknown --setup: refused with the reason, "
          "logged -- not an argparse error")
    rc, out = cli(*base, "--falsifier", "SPY settles below 745",
                  "--counter-thesis", "c", "--setup", "c_pin_fade")
    with Register(db) as reg:
        log2 = reg.packet_refusals()
    check(rc == 2 and "DECISION_OK refused: the packet lacks mechanism (" in out
          and len(log2) == len(log) + 1 and log2[-1]["rule"] == "incomplete_packet",
          "an incomplete active packet: refused, every missing field named, logged")
    rc, out = cli(*base, "--falsifier", "SPY settles below 745", "--counter-thesis",
                  "c", "--setup", "c_pin_fade", "--dry-run")
    with Register(db) as reg:
        log3 = reg.packet_refusals()
    check(rc == 2 and "REFUSED" in out and len(log3) == len(log2),
          "a dry run says the same and logs nothing -- it writes nothing")


def group_h() -> None:
    head("H. THE MIGRATION LEAVES EXISTING ROWS READABLE")
    db = str(TD / "legacy.db")
    ddl = rs.SCHEMA[rs.SCHEMA.index("CREATE TABLE IF NOT EXISTS decisions"):]
    ddl = ddl[:ddl.index(");") + 2]
    for c in rs.EL1_PACKET_NAMES:
        ddl = "\n".join(ln for ln in ddl.split("\n")
                        if not ln.strip().startswith(c + " "))
    ddl = ddl.replace("counter_thesis   TEXT,", "counter_thesis   TEXT")
    ddl = "\n".join(ln for ln in ddl.split("\n") if not ln.strip().startswith("--"))
    con = sqlite3.connect(db)
    con.execute(ddl)
    con.execute("INSERT INTO decisions (id, created_at, decision_time, instrument,"
                " instrument_norm, direction, thesis, edge_type, horizon,"
                " invalidation, status, falsifiers, counter_thesis, setup_id) VALUES"
                " ('old','2026-09-01T00:00:00+00:00','2026-09-01T00:00:00+00:00',"
                "'SPY','SPY','long','an old thesis','e','swing','x','active',"
                "'[\"below 700\"]','c','b_breakout')")
    con.commit()
    cols0 = {r[1] for r in con.execute("PRAGMA table_info(decisions)")}
    con.close()
    check(not (set(rs.EL1_PACKET_NAMES) & cols0),
          "the fixture register predates the columns")
    with Register(db) as reg:
        row = reg.get("old")
        cols = set(row)
        n_legacy = len(reg.all())
    check(set(rs.EL1_PACKET_NAMES) <= cols and row["thesis"] == "an old thesis"
          and row["status"] == "active" and n_legacy == 1
          and all(row[c] is None for c in rs.EL1_PACKET_NAMES),
          "opened by the register, the row is intact and readable; every new "
          "field is NULL -- not recorded, never a default it did not have")
    import decide
    buf = io.StringIO()
    saved = sys.argv
    sys.argv = ["decide.py", "--db", db, "show", "old"]
    try:
        with contextlib.redirect_stdout(buf):
            decide.main()
    finally:
        sys.argv = saved
    out = buf.getvalue()
    check(all(f"{c:<22} not recorded" in out for c in rs.EL1_PACKET_NAMES),
          "`decide.py show` reads 'not recorded' for each new field on the old row")
    with Register(db) as reg:
        reg.log_refusal("SPY", None, "incomplete_packet", "fixture", "gate", {})
        try:
            reg.conn.execute("UPDATE packet_refusals SET reason = 'edited'")
            edited = True
        except sqlite3.DatabaseError:
            edited = False
        try:
            reg.conn.execute("DELETE FROM packet_refusals")
            deleted = True
        except sqlite3.DatabaseError:
            deleted = False
    check(not edited and not deleted, "the refusal log is immutable: no edit, no delete")


def main() -> int:
    print(f"{LINE}\nEL-1 -- the packet, Red Team v0, the setup catalogue, the "
          f"refusal\n{LINE}")
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g,
              group_h):
        g()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
