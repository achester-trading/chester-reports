"""
Validation gate for Phase 3: the grader, the cuts and the probability ledger.

Every case is SEEDED. This is the one gate in the suite where that is the only
honest option: the register holds five decisions, none has reached its horizon, and
the earliest will not resolve until late September. A gate that waited for real
outcomes would validate nothing for a month, and the code it was meant to check
would be in production the whole time.

The six cases the change order names, each of which is a distinct failure mode:

  A taken decision that HIT its invalidation before the horizon. The case that
    separates the thesis R from the ruled R -- get this wrong and expectancy is
    computed on money nobody made.
  A declined decision that WOULD HAVE WON. The operator's filter, measured. If
    this is not graded, an inverted filter is undetectable by construction.
  A draft graded at its horizon. The cost of abstention: a DECISION_BLOCKED
    decision that would have won is the price of the freshness gate.
  An UNELAPSED horizon producing NO ROW. Not a partial, not nulls -- the single
    most dangerous object this module could emit, because a half-grade is counted
    by every cut and weighted equally with a settled one.
  A probability resolved RIGHT and one resolved WRONG, with the Brier arithmetic
    checked against hand-computed values rather than against itself.

Plus what the seeds cannot cover but the code must still get right: immutability,
the chain-root entry time, interval arithmetic, and the coin line.

    python tools/validate_grader.py
"""

from __future__ import annotations

import io
import math
import sqlite3
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

from altdata import grader                              # noqa: E402
from altdata import probability_ledger as pl            # noqa: E402
import cuts                                             # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = 0
FAIL = 0
LINE = "=" * 78

# A price path with everything the cases need: an entry, a dip through 685, and a
# recovery well above the entry by the horizon.
PIN_CSV = """date,symbol,close,net_gex
2026-08-03,SPY,700.0,-5.0e8
2026-08-05,SPY,690.0,-5.0e8
2026-08-07,SPY,680.0,-5.0e8
2026-08-12,SPY,695.0,-5.0e8
2026-08-24,SPY,735.0,-5.0e8
2026-08-26,SPY,740.0,-5.0e8
"""

ENTRY = "2026-08-03T20:00:00+00:00"
# swing = 21 days from 2026-08-03 -> 2026-08-24, which the series reaches.
AFTER = "2026-09-30T00:00:00+00:00"


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


def prices(d: Path) -> grader.PriceSeries:
    p = d / "pin.csv"
    p.write_text(PIN_CSV, encoding="utf-8")
    return grader.PriceSeries(str(p))


def decision(**over) -> dict:
    base = {
        "id": "seed0001", "horizon": "swing", "instrument": "SPY@ARCA.USD",
        "direction": "long", "status": "active", "operator_action": "TAKE",
        "thesis_state": None, "entry_decision_time": ENTRY,
        "decision_time": ENTRY, "size": "100 shares",
        "invalidation": "settled close below 685",
        "signals_used": '["exposure.gamma_flip"]',
    }
    base.update(over)
    return base


def group_a(d: Path) -> None:
    print(f"{LINE}\nA. A TAKEN DECISION THAT HIT ITS INVALIDATION\n{LINE}")
    ps = prices(d)
    res = grader.grade_one(decision(), ps, now=AFTER)
    check(res["graded"], f"it grades ({res.get('reason')})")
    g = res["grade"]

    check(g["reference_date"] == "2026-08-03" and g["reference_price"] == 700.0,
          f"reference is the entry session's close ({g['reference_date']} "
          f"{g['reference_price']})")
    check(g["horizon_date"] == "2026-08-24",
          f"horizon is entry + 21 days for swing ({g['horizon_date']})")
    check(g["horizon_price"] == 735.0, "horizon price is the close on that date")
    check(abs(g["return_points"] - 35.0) < 1e-9 and abs(g["return_pct"] - 5.0) < 1e-9,
          f"return is +35 points, +5.00% ({g['return_points']}, {g['return_pct']})")

    check(g["invalidation_hit"] == 1 and g["invalidation_date"] == "2026-08-07",
          f"THE INVALIDATION WAS HIT, on the day the close went through 685 "
          f"({g['invalidation_date']})")
    check(abs(g["mae_close_pct"] + 100 * 20 / 700) < 1e-9,
          f"MAE on closes is -2.857% -- the 680 close ({g['mae_close_pct']:.4f})")
    check(g["mae_close_date"] == "2026-08-07", "dated to that close")

    check(abs(g["risk_per_unit"] - 15.0) < 1e-9
          and abs(g["dollars_at_risk"] - 1500.0) < 1e-9,
          f"risk is (700 - 685) x 100 = $1500 ({g['dollars_at_risk']})")
    check(abs(g["r_multiple"] - 35 * 100 / 1500) < 1e-9,
          f"THESIS R is +2.33 -- held through the stop ({g['r_multiple']:.4f})")
    check(g["r_multiple_ruled"] == -1.0,
          f"RULED R is exactly -1 -- an operator who honoured his own "
          f"invalidation was out on 2026-08-07 ({g['r_multiple_ruled']})")
    check(g["r_multiple"] > 0 > g["r_multiple_ruled"],
          "and the two have OPPOSITE SIGNS, which is the entire reason both are "
          "stored: one column would have to lie about this decision")

    check(g["spy_gamma_sign"] == "negative",
          f"the regime variable is read off the same row ({g['spy_gamma_sign']})")
    check(g["mechanism_group"] == "dealer_chain_derived",
          f"and the mechanism group from the cited signal ({g['mechanism_group']})")


def group_b(d: Path) -> None:
    print(f"\n{LINE}\nB. A DECLINED DECISION THAT WOULD HAVE WON\n{LINE}")
    ps = prices(d)
    # Same path, but the invalidation is placed below the dip so the thesis runs.
    dec = decision(id="seed0002", operator_action="DECLINE", status="declined",
                   invalidation="settled close below 670")
    res = grader.grade_one(dec, ps, now=AFTER)
    check(res["graded"], "a DECLINED decision is graded at all -- the operator's "
                         "filter cannot be measured otherwise")
    g = res["grade"]
    check(g["invalidation_hit"] == 0,
          "its invalidation was never touched (670 is below the 680 dip)")
    check(g["r_multiple_ruled"] is not None and g["r_multiple_ruled"] > 0,
          f"and it WOULD HAVE WON: ruled R {g['r_multiple_ruled']:.3f}")
    check(abs(g["r_multiple_ruled"] - g["r_multiple"]) < 1e-9,
          "with thesis and ruled R equal, because nothing stopped it out")
    check(cuts.status_of(g) == "declined",
          f"and it cuts as 'declined' ({cuts.status_of(g)})")


def group_c(d: Path) -> None:
    print(f"\n{LINE}\nC. A DRAFT GRADED AT ITS HORIZON\n{LINE}")
    ps = prices(d)
    dec = decision(id="seed0003", status="draft", operator_action=None,
                   invalidation="settled close below 670")
    res = grader.grade_one(dec, ps, now=AFTER)
    check(res["graded"],
          "a DRAFT is graded -- this is the cost of abstention, and a blocked "
          "decision that would have won is the price of the freshness gate")
    g = res["grade"]
    check(g["status"] == "draft" and g["operator_action"] is None,
          "the draft's status is carried onto the grade as-is")
    check(cuts.status_of(g).startswith("draft"),
          f"and it cuts as a draft ({cuts.status_of(g)})")
    check(g["r_multiple_ruled"] is not None,
          f"with a real R ({g['r_multiple_ruled']:.3f}) -- the abstention has a "
          f"measurable price")


def group_d(d: Path) -> None:
    print(f"\n{LINE}\nD. AN UNELAPSED HORIZON PRODUCES NO ROW\n{LINE}")
    ps = prices(d)

    # Before the horizon date: nothing, and it says which date it is waiting for.
    res = grader.grade_one(decision(id="seed0004"), ps,
                           now="2026-08-10T00:00:00+00:00")
    check(not res["graded"], "an unelapsed horizon is not graded")
    check(res.get("grade") is None,
          "and produces NO GRADE OBJECT -- not a partial, not nulls")
    check("has not elapsed" in res["reason"],
          f"with the reason naming it ({res['reason']})")

    # THE SECOND CONDITION, which matters as much: the calendar has passed the
    # horizon but the stored series has not reached it. Grading here would take a
    # price from BEFORE the horizon and call it the horizon price.
    short = d / "short.csv"
    short.write_text("date,symbol,close,net_gex\n"
                     "2026-08-03,SPY,700.0,-5.0e8\n"
                     "2026-08-07,SPY,680.0,-5.0e8\n", encoding="utf-8")
    res = grader.grade_one(decision(id="seed0005"),
                           grader.PriceSeries(str(short)), now=AFTER)
    check(not res["graded"] and "stop at" in res["reason"],
          f"a series that stops short of an ELAPSED horizon is also refused "
          f"({res['reason'][:72]})")

    # And nothing reaches the table.
    db = str(d / "none.db")
    with grader.GradeStore(db) as st:
        res = grader.grade_one(decision(id="seed0006"), ps,
                               now="2026-08-10T00:00:00+00:00")
        if res["graded"]:
            st.write(res["grade"])
        check(len(st.all_grades()) == 0,
              "so the grades table stays empty rather than holding a placeholder")


def group_e(d: Path) -> None:
    print(f"\n{LINE}\nE. THE GRADE IS IMMUTABLE, AND THE CHAIN ROOT IS THE ENTRY\n{LINE}")
    ps = prices(d)
    db = str(d / "imm.db")
    with grader.GradeStore(db) as st:
        st.write(grader.grade_one(decision(id="seedimm"), ps, now=AFTER)["grade"])
        for sql, label in (
                ("UPDATE grades SET r_multiple = 99 WHERE decision_id='seedimm'",
                 "edit a grade"),
                ("DELETE FROM grades WHERE decision_id='seedimm'",
                 "delete a grade")):
            try:
                st.conn.execute(sql)
                bad(f"a grade could be changed: {label} succeeded")
            except sqlite3.IntegrityError as e:
                ok(f"refused ({label}): {e}")

        # A re-grade under a NEW graded_at is a new row, not an edit.
        g2 = grader.grade_one(decision(id="seedimm"), ps, now=AFTER)["grade"]
        g2["graded_at"] = "2026-10-01T00:00:00+00:00"
        st.write(g2)
        check(len(st.all_grades()) == 2,
              "a re-grade writes a SECOND row, so a method change is visible "
              "rather than overwriting the evidence")

    # The chain-root entry time, in a real register.
    reg_db = str(d / "chain.db")
    from register.store import Register  # noqa: PLC0415
    reg = Register(reg_db)
    a = reg.record(instrument="SPY", direction="long", thesis="t",
                   edge_type="positioning", horizon="swing",
                   invalidation="settled close below 685", status="draft",
                   decision_time=ENTRY)
    b = reg.supersede(a, instrument="SPY", direction="long", thesis="t",
                      edge_type="positioning", horizon="swing",
                      invalidation="settled close below 685", status="active",
                      operator_action="TAKE",
                      decision_time="2026-09-19T00:00:00+00:00")
    reg.close()
    rows = grader.decisions_to_grade(reg_db)
    check(len(rows) == 1, f"a two-link chain yields ONE row to grade ({len(rows)})")
    r = rows[0]
    check(r["id"] == b and r["chain_root_id"] == a,
          "the head is graded and the root is identified")
    check(r["entry_decision_time"] == ENTRY,
          f"THE ENTRY IS THE ROOT'S CLOCK ({r['entry_decision_time']}) and not "
          f"the head's ({r['decision_time']}) -- grading from the head would take "
          f"the reference price six weeks after entry")


def group_f(d: Path) -> None:
    print(f"\n{LINE}\nF. A PROBABILITY RESOLVED RIGHT, AND ONE RESOLVED WRONG\n{LINE}")
    db = str(d / "prob.db")
    crit = ("Two consecutive negative real GDP quarters in the BEA advance "
            "estimates published on or before the horizon date.")
    with pl.ProbabilityLedger(db) as led:
        right = led.record(source="monthly_macro", scenario_set="m:2026-05",
                           claim="Soft landing", probability=0.80,
                           horizon_date="2026-08-30",
                           resolution_criterion=crit,
                           emitted_at="2026-05-30T00:00:00+00:00")
        wrong = led.record(source="monthly_macro", scenario_set="m:2026-05",
                           claim="Recession", probability=0.20,
                           horizon_date="2026-08-30",
                           resolution_criterion=crit,
                           emitted_at="2026-05-30T00:00:00+00:00")

        # RESOLVED RIGHT: said 0.80, it happened.
        a = led.resolve(right, 1, note="BEA advance: two positive quarters")
        check(abs(a["brier"] - 0.04) < 1e-12,
              f"p=0.80 and it HAPPENED -> brier 0.04, hand-checked as "
              f"(0.80-1)^2 ({a['brier']:.6f})")

        # RESOLVED WRONG: said 0.20, it happened anyway.
        b = led.resolve(wrong, 1, note="counterfactual seed: it happened")
        check(abs(b["brier"] - 0.64) < 1e-12,
              f"p=0.20 and it HAPPENED -> brier 0.64, hand-checked as "
              f"(0.20-1)^2 ({b['brier']:.6f})")
        check(b["brier"] > pl.COIN_BRIER > a["brier"],
              "the wrong one is worse than a coin and the right one better, which "
              "is the only unambiguous reading a Brier score gives")

        scores = led.score_by_source()
        m = scores["monthly_macro"]
        check(m["n"] == 2 and abs(m["brier"] - 0.34) < 1e-12,
              f"the running score is their mean, 0.34 ({m['brier']:.6f}) on n=2")
        check(m["brier"] > pl.COIN_BRIER and "worse than" in m["verdict"],
              f"and is reported as worse than a coin ({m['verdict']})")

        check(not led.coherence(),
              "a set summing to 1.00 is coherent")
        led.record(source="operator", scenario_set="bad:set", claim="A",
                   probability=0.7, horizon_date="2026-12-31",
                   resolution_criterion=crit)
        led.record(source="operator", scenario_set="bad:set", claim="B",
                   probability=0.7, horizon_date="2026-12-31",
                   resolution_criterion=crit)
        inc = led.coherence()
        check(len(inc) == 1 and abs(inc[0]["total"] - 1.4) < 1e-9,
              f"a set summing to 1.40 is REPORTED, not normalised ({inc})")

        # The criterion is not optional.
        try:
            led.record(source="x", claim="y", probability=0.5,
                       horizon_date="2026-12-31", resolution_criterion="  ")
            bad("a forecast with no resolution criterion was accepted")
        except ValueError as e:
            ok(f"a forecast with no resolution criterion is refused: {str(e)[:56]}")

        check(len(led.due(as_of="2026-12-31T00:00:00+00:00")) == 2,
              "the two unresolved December forecasts appear in the due queue")


def group_g(d: Path) -> None:
    print(f"\n{LINE}\nG. THE INTERVAL, AND WHAT IT REFUSES TO CLAIM\n{LINE}")
    iv = cuts.interval([1.0, -1.0, 1.0, -1.0])
    check(iv["n"] == 4 and abs(iv["mean"]) < 1e-12,
          f"n=4 mean 0 ({iv['mean']})")
    check(abs(iv["sigma"] - math.sqrt(4 / 3)) < 1e-9,
          f"sigma is the SAMPLE stdev ({iv['sigma']:.6f})")
    check(abs(iv["se"] - iv["sigma"] / 2.0) < 1e-12,
          "se is sigma / sqrt(n), per Evidence and Inference Ch. 1")
    check(abs(iv["hi"] - 1.96 * iv["se"]) < 1e-9,
          "and the 95% band is +/- 1.96 se")
    check(abs(iv["paper_se_1r"] - 0.5) < 1e-12,
          "the paper's own 1/sqrt(n) yardstick is reported alongside the "
          "measured one, so an unusual spread is visible")

    one = cuts.interval([0.4])
    check(one["n"] == 1 and one["mean"] == 0.4 and one["lo"] is None,
          "n=1 reports the mean but NO interval")
    check("no spread" in one["note"],
          f"and says why rather than substituting the paper's constant "
          f"({one['note']})")
    none = cuts.interval([])
    check(none["n"] == 0 and none["mean"] is None,
          "n=0 claims nothing at all")

    # Expectancy is on the ruled column. A cut that used the thesis column would
    # report this set as profitable when the operator lost money on every one.
    rows = [{"r_multiple": 2.0, "r_multiple_ruled": -1.0, "invalidation_hit": 1,
             "operator_action": "TAKE", "status": "active"} for _ in range(3)]
    s = cuts.summarise(rows)
    check(abs(s["expectancy_ruled"]["mean"] + 1.0) < 1e-12,
          f"three stopped-out decisions have expectancy -1R "
          f"({s['expectancy_ruled']['mean']})")
    check(abs(s["thesis_r"]["mean"] - 2.0) < 1e-12,
          "while the thesis R reads +2R -- both true, and only one is the money")
    check(abs(s["rule_cost_r"]["mean"] - 3.0) < 1e-12,
          f"and the cost of the rule is the 3R gap ({s['rule_cost_r']['mean']})")
    check(s["invalidation_hit_rate"] == 1.0, "with a 100% invalidation hit rate")


def main() -> int:
    print(f"{LINE}\nPhase 3 -- grader, cuts and probability ledger (seeded)\n{LINE}")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        d = Path(td)
        group_a(d)
        group_b(d)
        group_c(d)
        group_d(d)
        group_e(d)
        group_f(d)
        group_g(d)
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
