"""
Learning Loop v2, LL-1 (B73): decision quality, "is it getting better".

  A  THE DECOMPOSITION IN CLOSED FORM. A seeded ledger of 100 resolved rows, 50
     at 0.2 (10 resolved 1) and 50 at 0.8 (30 resolved 1): by hand REL 0.0200,
     RES 0.0400, UNC 0.2400, Brier 0.2200 and a zero within-bin term, each
     checked to four decimals; and the terms add to the Brier on a fixture whose
     bins are not constant.
  B  THE FLOOR. A cell of 99 prints "accruing (n=99 of 100)" and no figure; the
     cell of 100 prints its terms; dry-run sources are never counted; a row
     resolved after the as-of is not read.
  C  THE TREND WINDOWS. The 13- and 52-week windows and the windows before them
     count the rows resolved in each, and the expectancy in ruled R counts only
     the taken decisions' latest grades in each.
  D  THE COUNTERFACTUAL LEDGER. Taken, declined and draft per book, one grade a
     decision (its latest), each with n and its mean ruled R, "accruing" below
     the floor; the Weekly stance's implied book against Book Z's three ledgers
     over the same weeks, by hand.
  E  WHERE IT PRINTS. The Monthly's Lab report hook appends the line and the
     tables (and stands alone with no lab ledger) and never raises; the pack
     command prints the same line; the Weekly imports nothing of it.
  F  HYGIENE. No model call or model import; read-only on the store; the keys
     registered and barred from the market-state object.

Synthetic fixtures only: no live store, no network, no model.

    python tools/validate_decision_quality.py
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import ast
import json
import re
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import gate_tmp  # noqa: E402
import yaml  # noqa: E402

from altdata import decision_quality as dq  # noqa: E402
from altdata import grader  # noqa: E402
from altdata.probability_ledger import ProbabilityLedger  # noqa: E402

PASS = FAIL = 0
LINE = "=" * 78
AS_OF = "2026-10-26T20:00:00+00:00"


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


def scratch(prefix: str) -> str:
    return str(Path(gate_tmp.mkdtemp(prefix)) / "chester.db")


def seed(led: ProbabilityLedger, source: str, p: float, outcome: int, i: int,
         resolved: str, emitted: str = "2026-09-01", horizon: str = "2026-09-05"
         ) -> None:
    pid = led.record(source=source, claim=f"{source} claim {i}", probability=p,
                     horizon_date=horizon, resolution_criterion="fixture",
                     emitted_at=f"{emitted}T20:{i // 60:02d}:{i % 60:02d}+00:00",
                     missing_inputs=[])
    led.resolve(pid, outcome, resolved_at=f"{resolved}T21:00:00+00:00")


def closed_form_db() -> str:
    db = scratch("dq_a_")
    with ProbabilityLedger(db) as led:
        i = 0
        for p, ones in ((0.2, 10), (0.8, 30)):
            for k in range(50):
                seed(led, "fixture_src", p, 1 if k < ones else 0, i, "2026-10-01")
                i += 1
        for k in range(99):                     # a cell one short of the floor
            seed(led, "thin:fam", 0.6, k % 2, k, "2026-10-02",
                 emitted="2026-08-01", horizon="2026-08-20")
        for k in range(40):                     # resolved in the 13 weeks before
            seed(led, "older_src", 0.7, 1, k, "2026-06-01",
                 emitted="2026-05-01", horizon="2026-05-05")
        for k in range(5):
            seed(led, "dryrun.fixture_src", 0.9, 0, k, "2026-10-01")
        seed(led, "fixture_src", 0.5, 1, 999, "2026-10-27")   # after the as-of
    return db


# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. THE DECOMPOSITION IN CLOSED FORM")
    db = closed_form_db()
    rows = [r for r in dq.resolved_rows(AS_OF, db) if r["source"] == "fixture_src"]
    c = dq.murphy([(r["probability"], r["outcome"]) for r in rows])
    check(c["n"] == 100, f"the fixture cell holds 100 resolved rows (n={c['n']})")
    for k, want in (("rel", 0.02), ("res", 0.04), ("unc", 0.24), ("brier", 0.22),
                    ("within", 0.0)):
        check(round(c[k], 4) == round(want, 4),
              f"{k.upper()} = {want:.4f} by hand (computed {c[k]:.4f})")
    check(abs(c["rel"] - c["res"] + c["unc"] + c["within"] - c["brier"]) < 1e-12,
          "REL - RES + UNC + W is the Brier")
    mixed = [(0.12, 1), (0.18, 0), (0.15, 0), (0.71, 1), (0.79, 1), (0.74, 0)]
    m = dq.murphy(mixed, floor=1)
    bs = sum((p - o) ** 2 for p, o in mixed) / len(mixed)
    check(abs(m["brier"] - bs) < 1e-12 and m["within"] != 0.0
          and abs(m["rel"] - m["res"] + m["unc"] + m["within"] - bs) < 1e-12,
          "with forecasts spread inside a bin, W is non-zero and the terms still "
          "add to the Brier")
    check([b["bin"] for b in m["bins"]] == [1, 7] and dq._bin(1.0) == 9
          and dq._bin(0.0) == 0 and dq._bin(0.1) == 1,
          "ten bins of width 0.1, 1.0 in the top bin")


def group_b() -> None:
    head("B. THE FLOOR")
    db = closed_form_db()
    b = dq.build(AS_OF, db, min_n=10, marks=lambda ld, d: None)
    cells = b["decomposition"]["cells"]
    fx = cells.get(("fixture_src", "1-7d"))
    thin = cells.get(("thin", "8-31d"))
    check(fx and dq.cell_text(fx).startswith("Brier 0.2200 = REL 0.0200 - RES 0.0400 "
                                             "+ UNC 0.2400"),
          f"the cell at the floor prints its terms ({dq.cell_text(fx) if fx else None})")
    check(thin and dq.cell_text(thin) == "accruing (n=99 of 100)",
          f"a cell of 99 prints accruing and no figure "
          f"({dq.cell_text(thin) if thin else None})")
    check(not any(k[0].startswith("dryrun") for k in cells),
          "the dry-run namespace is never counted")
    check(b["rows"] == 239, f"a row resolved after the as-of is not read "
                            f"(rows {b['rows']} = 100 + 99 + 40)")
    check(dq.family("alt_asset:gold") == "alt_asset"
          and dq.bucket("2026-10-01", "2026-10-08") == "1-7d"
          and dq.bucket("2026-10-01", "2026-11-01") == "8-31d"
          and dq.bucket("2026-10-01", "2026-12-31") == "32-92d"
          and dq.bucket("2026-10-01", "2027-06-01") == ">92d",
          "the family is the source to its first colon; the horizon buckets are "
          "a week, a month, a quarter, longer")


def _grades_db(db: str) -> None:
    with grader.GradeStore(db) as gs:
        conn = gs.conn
        conn.execute("CREATE TABLE IF NOT EXISTS decisions (id TEXT PRIMARY KEY, "
                     "book TEXT, status TEXT, operator_action TEXT)")

        def add(did, book, status, act, r, graded_at, ret=1.0):
            conn.execute("INSERT INTO decisions VALUES (?,?,?,?)",
                         (did, book, status, act))
            gs.write({"decision_id": did, "horizon": "swing", "graded_at": graded_at,
                      "horizon_date": graded_at[:10], "status": status,
                      "operator_action": act, "r_multiple_ruled": r,
                      "return_pct": ret, "decision_time": "2026-09-01T14:00:00+00:00",
                      "observations_json": "[]", "price_source": "fixture",
                      "method_version": grader.METHOD_VERSION})
        for k in range(10):
            add(f"T{k}", "B", "closed", "TAKE", 1.0, "2026-10-10T21:00:00+00:00")
        for k in range(4):
            add(f"O{k}", "B", "closed", "MODIFY", -1.0, "2026-06-10T21:00:00+00:00")
        for k in range(3):
            add(f"X{k}", "B", "declined", "DECLINE", -0.5, "2026-10-10T21:00:00+00:00",
                ret=-2.0)
        for k in range(2):
            add(f"D{k}", "C", "draft", None, 2.0, "2026-10-10T21:00:00+00:00")
        # a re-grade of T0, later: its latest grade counts, once
        gs.write({"decision_id": "T0", "horizon": "swing",
                  "graded_at": "2026-10-11T21:00:00+00:00", "horizon_date": "2026-10-11",
                  "status": "closed", "operator_action": "TAKE",
                  "r_multiple_ruled": 3.0, "return_pct": 1.0,
                  "observations_json": "[]", "price_source": "fixture",
                  "method_version": grader.METHOD_VERSION})
        conn.commit()


def group_c() -> None:
    head("C. THE TREND WINDOWS")
    db = closed_form_db()
    _grades_db(db)
    b = dq.build(AS_OF, db, min_n=10, marks=lambda ld, d: None)
    t = b["trend"]
    check(t["13w_now"]["window"] == ("2026-07-27", "2026-10-26")
          and t["13w_before"]["window"] == ("2026-04-27", "2026-07-27")
          and t["52w_now"]["window"] == ("2025-10-27", "2026-10-26")
          and t["52w_before"]["window"] == ("2024-10-28", "2025-10-27"),
          "the windows are 13 and 52 weeks to the as-of and the same lengths before")
    n = {k: v["brier"]["n"] for k, v in t.items()}
    check(n == {"13w_now": 199, "13w_before": 40, "52w_now": 239, "52w_before": 0},
          f"each window counts the rows resolved in it ({n})")
    r = {k: (v["r"]["n"], v["r"]["mean"]) for k, v in t.items()}
    check(r["13w_now"] == (10, 1.2) and r["13w_before"] == (4, -1.0)
          and r["52w_now"][0] == 14 and r["52w_before"] == (0, None),
          f"the expectancy counts only taken decisions' latest grades ({r})")
    ln = dq.line(b)
    check("last 13 weeks accruing (n=199 of 100)" not in ln
          and "last 13 weeks 0." in ln and "against accruing (n=40 of 100) the 13 before" in ln
          and "+1.20R (n=10)" in ln and "accruing (n=4 of 10) the 13 before" in ln,
          "the line prints each window's figure or accruing, with its n")
    check("never written by a model" in ln and ln.startswith("Is it getting better"),
          "the line says what it is")


def group_d() -> None:
    head("D. THE COUNTERFACTUAL LEDGER")
    db = closed_form_db()
    _grades_db(db)
    cf = dq.build(AS_OF, db, min_n=3, marks=lambda ld, d: None)["counterfactual"]
    check(cf["B"]["taken"]["n"] == 14 and cf["B"]["declined"]["n"] == 3
          and cf["B"]["draft"]["n"] == 0 and cf["C"]["draft"]["n"] == 2,
          "taken, declined and draft per book, one grade a decision")
    check(abs(cf["B"]["taken"]["mean_r"] - (12.0 - 4.0) / 14) < 1e-12
          and cf["B"]["declined"]["mean_r"] == -0.5 and cf["C"]["draft"]["mean_r"] == 2.0
          and cf["B"]["declined"]["mean_return_pct"] == -2.0,
          "each class's mean ruled R and mean return, the re-grade counted once")
    check(dq._cf_text(cf["C"]["draft"], 3) == "accruing (n=2)"
          and dq._cf_text(cf["B"]["declined"], 3).startswith("n=3, -0.50R"),
          "accruing below the floor, n and the figure at it")
    marks = {"spy": {"2026-09-04": 100.0, "2026-09-11": 102.0, "2026-09-18": 101.0},
             "cash": {"2026-09-04": 100.0, "2026-09-11": 100.1, "2026-09-18": 100.2},
             "sixty_forty": {"2026-09-04": 100.0, "2026-09-11": 101.0,
                             "2026-09-18": 100.5}}
    rows = [{"source": "weekly_stance", "probability": 0.7,
             "emitted_at": "2026-09-04T21:00:00+00:00", "horizon_date": "2026-09-11"},
            {"source": "weekly_stance", "probability": 0.3,
             "emitted_at": "2026-09-11T21:00:00+00:00", "horizon_date": "2026-09-18"},
            {"source": "weekly_stance", "probability": 0.5,
             "emitted_at": "2026-09-18T21:00:00+00:00", "horizon_date": "2026-09-25"},
            {"source": "daily_close_outlook", "probability": 0.9,
             "emitted_at": "2026-09-04T21:00:00+00:00", "horizon_date": "2026-09-11"}]
    s = dq.stance_vs_book_z(rows, AS_OF, marks=lambda ld, d: marks[ld].get(d))
    want = (2.0 + 100.0 * (100.2 / 100.1 - 1.0)) / 2
    check(s["n"] == 2 and abs(s["stance_mean_pct"] - want) < 1e-9
          and abs(s["spy_mean_pct"] - (2.0 + 100.0 * (101 / 102 - 1)) / 2) < 1e-9,
          f"long SPY above 0.5, cash below, 0.5 skipped, by hand "
          f"({s['stance_mean_pct']:.4f} = {want:.4f})")
    s2 = dq.stance_vs_book_z(rows[:1], AS_OF, marks=lambda ld, d: None)
    check(s2["n"] == 0 and s2["unmarked"] == 1,
          "a week without Book Z marks at both ends is counted unmarked, not guessed")


def group_e() -> None:
    head("E. WHERE IT PRINTS")
    db = closed_form_db()
    lab = ("alpha_lab_report_2026-11.md", "# Alpha Lab\n\nbody\n", "markdown")
    got = dq.with_lab_report(lab, "2026-11-01", db)
    check(got[0] == lab[0] and got[1].startswith("# Alpha Lab")
          and "## Decision quality (Learning Loop v2, LL-1)" in got[1]
          and "Is it getting better" in got[1]
          and "### The counterfactual ledger, by book" in got[1]
          and "### The Brier decomposition, by source family and horizon" in got[1],
          "the Lab report gains the line and the two tables")
    alone = dq.with_lab_report(None, "2026-11-01", db)
    check(alone is None,
          "with no Lab report the edition gains no attachment (the Monthly's two stay two; B80)")
    run = (REPO / "monthly_macro" / "run.py").read_text(encoding="utf-8")
    check("with_lab_report(lab, stamp)" in run, "the Monthly calls the hook")
    try:
        dq.with_lab_report(lab, "2026-11-01", db=str(REPO / "no" / "such" / "x.db"))
        ok = True
    except Exception:                                         # noqa: BLE001
        ok = False
    check(ok, "the hook never raises")
    pk = dq.pack_md(AS_OF, db)
    check(pk.startswith("## Decision quality: is it getting better (LL-1)")
          and "**The line.** Is it getting better" in pk,
          "the Doctrine pack's command prints the line and the tables")
    weekly = [p for p in (REPO / "daily_cascade").glob("weekly*.py")]
    check(weekly and not any("decision_quality" in p.read_text(encoding="utf-8")
                             for p in weekly),
          "the Weekly imports nothing of it (its budget is ruled)")


def group_f() -> None:
    head("F. HYGIENE")
    src = (REPO / "altdata" / "decision_quality.py").read_text(encoding="utf-8")
    mods = set()
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Import):
            mods |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            mods.add(n.module or "")
    banned = {"anthropic", "altdata.model_meter", "daily_cascade.narrative", "requests",
              "urllib.request", "regime"}
    check(not (mods & banned) and "model_meter" not in src and "anthropic" not in src,
          f"no model, network or regime import ({sorted(mods)})")
    check("mode=ro" in src and "INSERT" not in src and "UPDATE " not in src,
          "the store is opened read-only and nothing is written")
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    keys = ("brier.decomposition", "grade.counterfactual")
    check(all(k in reg["metrics"] and reg["metrics"][k]["trigger_eligible"] is False
              for k in keys), "the keys are registered, trigger_eligible false")
    barred = {k for b in reg.get("market_state_barred") or [] for k in b["keys"]}
    check(set(keys) <= barred, "and barred from the market-state object")
    ms = (REPO / "config" / "market_state.yaml").read_text(encoding="utf-8")
    check(not re.search(r"brier\.decomposition|grade\.counterfactual", ms),
          "and the object's config names neither")


def main() -> int:
    for g in (group_a, group_b, group_c, group_d, group_e, group_f):
        try:
            g()
        except Exception as exc:                                # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{PASS} passed, {FAIL} failed")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
