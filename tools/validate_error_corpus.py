"""
Learning Loop v2, LL-3 (B73): the error corpus.

  A  A MISS BECOMES A ROW, A HIT DOES NOT. A ledger row past the coin's Brier
     and a grade with negative ruled R (or, with no R, a negative return) each
     write one row with what was said, what happened and the margin; a hit, an
     unresolved row, a dry-run source, a flat grade and a row resolved after the
     as-of write nothing.
  B  APPEND-ONLY. A second backfill writes nothing; UPDATE and DELETE are
     refused by trigger; a dry run creates nothing.
  C  MISSING INPUTS ROUND-TRIP. A row recorded with missing_inputs carries the
     same sorted list into the corpus; a row recorded without carries NULL ("not
     recorded"), and [] stays []; the ledger refuses a change to the field once
     written; the object held at emission supplies the absent dimensions and
     awaiting legs, and none held leaves them NULL.
  D  THE SOURCES. Every ledger write path passes missing_inputs at emission
     (the market-state rows their object's absent dimensions); the corpus
     module calls no model and imports no report writer; its key is registered
     and barred from the object.

Synthetic fixtures only: no live store, no network, no model.

    python tools/validate_error_corpus.py
"""

from __future__ import annotations

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

from altdata import error_corpus as ec  # noqa: E402
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


def fixture() -> tuple[str, dict]:
    db = str(Path(gate_tmp.mkdtemp("ec_")) / "chester.db")
    ids = {}
    with ProbabilityLedger(db) as led:
        def rec(name, src, p, o, mi, resolved="2026-10-01"):
            ids[name] = led.record(
                source=src, claim=f"claim {name}", probability=p,
                horizon_date="2026-09-30", resolution_criterion="fixture",
                emitted_at="2026-09-23T20:45:00+00:00", missing_inputs=mi)
            if o is not None:
                led.resolve(ids[name], o, resolved_at=f"{resolved}T21:00:00+00:00")
        rec("miss", "market_state", 0.8, 0, ["growth", "credit"])
        rec("hit", "market_state", 0.8, 1, [])
        rec("open", "daily_close_outlook", 0.9, None, [])
        rec("dry", "dryrun.weekly_stance", 0.9, 0, [])
        rec("null_mi", "weekly_stance", 0.2, 1, None)
        rec("empty_mi", "book_b_candidate", 0.7, 0, [])
        rec("late", "weekly_stance", 0.9, 0, [], resolved="2026-10-27")
    with grader.GradeStore(db) as gs:
        gs.conn.execute("CREATE TABLE decisions (id TEXT PRIMARY KEY, book TEXT)")
        for did, book, r, ret in (("L1", "B", -1.0, -3.0), ("W1", "B", 1.5, 2.0),
                                  ("N1", "C", None, -1.2), ("F1", "C", None, None)):
            gs.conn.execute("INSERT INTO decisions VALUES (?,?)", (did, book))
            gs.write({"decision_id": did, "horizon": "swing",
                      "graded_at": "2026-10-10T21:00:00+00:00",
                      "horizon_date": "2026-10-10", "operator_action": "TAKE",
                      "decision_time": "2026-09-19T14:00:00+00:00",
                      "r_multiple_ruled": r, "return_pct": ret,
                      "observations_json": "[]", "price_source": "fixture",
                      "method_version": grader.METHOD_VERSION})
        gs.conn.commit()
    return db, ids


OBJ = {"session": "2026-09-23", "absent_dimensions": ["breadth", "credit"],
       "absent_contradictions": ["c7_credit_vs_equity"]}


def objects(at: str):
    return OBJ if str(at) >= "2026-09-20" else None


def corpus(db: str) -> list[dict]:
    return ec.rows(db)


# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. A MISS BECOMES A ROW, A HIT DOES NOT")
    db, ids = fixture()
    out = ec.backfill(db, AS_OF, dry_run=False, objects=objects)
    rows = corpus(db)
    refs = {r["ref_id"] for r in rows}
    check(out["by_kind"] == {"probability": 3, "decision": 2} and out["written"] == 5,
          f"three ledger misses and two graded misses ({out['by_kind']})")
    check(ids["miss"] in refs and ids["empty_mi"] in refs and ids["null_mi"] in refs,
          "the ledger rows past the coin's Brier are in")
    check(not ({ids[k] for k in ("hit", "open", "dry", "late")} & refs),
          "a hit, an unresolved row, a dry-run source and a row resolved after the "
          "as-of are not")
    dec = {r["ref_id"].split("|")[0]: r for r in rows if r["kind"] == "decision"}
    check(set(dec) == {"L1", "N1"}, f"a negative ruled R and, with no R, a negative "
                                    f"return are misses; a win and a flat grade are not "
                                    f"({sorted(dec)})")
    m = next(r for r in rows if r["ref_id"] == ids["miss"])
    said, happened = json.loads(m["said_json"]), json.loads(m["happened_json"])
    check(said["claim"] == "claim miss" and said["probability"] == 0.8
          and happened["outcome"] == 0 and abs(happened["brier"] - 0.64) < 1e-12,
          "what was said and what happened are the stored row and its resolution")
    check(abs(m["margin"] - 0.39) < 1e-12 and m["margin_unit"] == "brier_over_coin"
          and dec["L1"]["margin"] == -1.0 and dec["L1"]["margin_unit"] == "r_ruled"
          and dec["N1"]["margin"] == -1.2 and dec["N1"]["margin_unit"] == "return_pct",
          "the margins: Brier over the coin, ruled R, or the return")
    check(dec["L1"]["source"] == "register:B" and m["source"] == "market_state"
          and m["emitted_at"] == "2026-09-23T20:45:00+00:00",
          "the source and the emission's as-of")


def group_b() -> None:
    head("B. APPEND-ONLY")
    db, _ = fixture()
    dry = ec.backfill(db, AS_OF, dry_run=True, objects=objects)
    conn = sqlite3.connect(db)
    has = conn.execute("SELECT 1 FROM sqlite_master WHERE name='error_corpus'").fetchone()
    conn.close()
    check(dry["misses"] == 5 and dry["written"] == 0 and has is None,
          "a dry run counts the misses and creates nothing")
    ec.backfill(db, AS_OF, dry_run=False, objects=objects)
    again = ec.backfill(db, AS_OF, dry_run=False, objects=objects)
    check(again["written"] == 0 and again["already"] == 5 and ec.count(db) == 5,
          "a second backfill writes nothing")
    conn = sqlite3.connect(db)
    for sql, what in (("UPDATE error_corpus SET margin = 0", "UPDATE"),
                      ("DELETE FROM error_corpus", "DELETE")):
        try:
            conn.execute(sql)
            refused = False
        except sqlite3.DatabaseError as exc:
            refused = "append-only" in str(exc)
        check(refused, f"{what} is refused by trigger")
    conn.close()


def group_c() -> None:
    head("C. MISSING INPUTS ROUND-TRIP")
    db, ids = fixture()
    ec.backfill(db, AS_OF, dry_run=False, objects=objects)
    by = {r["ref_id"]: r for r in corpus(db)}
    check(json.loads(by[ids["miss"]]["missing_inputs"]) == ["credit", "growth"],
          "a list written at emission arrives sorted and whole")
    check(by[ids["empty_mi"]]["missing_inputs"] == "[]",
          "[] (none recorded missing) stays []")
    conn = sqlite3.connect(db)
    raw = conn.execute("SELECT missing_inputs FROM probabilities WHERE probability_id=?",
                       (ids["null_mi"],)).fetchone()[0]
    check(raw is None and by[ids["null_mi"]]["missing_inputs"] is None,
          "a write without the field stores NULL, 'not recorded', and the corpus "
          "carries the NULL")
    try:
        conn.execute("UPDATE probabilities SET missing_inputs='[\"x\"]' "
                     "WHERE probability_id=?", (ids["miss"],))
        refused = False
    except sqlite3.DatabaseError as exc:
        refused = "written once" in str(exc)
    conn.close()
    check(refused, "the ledger refuses a change to missing_inputs once written")
    dec = [r for r in corpus(db) if r["kind"] == "decision"]
    m = by[ids["miss"]]
    check(json.loads(m["absent_dimensions"]) == ["breadth", "credit"]
          and json.loads(m["awaiting_legs"]) == ["c7_credit_vs_equity"]
          and m["object_session"] == "2026-09-23",
          "the object held at emission supplies the absent dimensions and legs")
    check(all(r["absent_dimensions"] is None and r["object_session"] is None
              and r["missing_inputs"] is None for r in dec),
          "an emission before any held object leaves them NULL; a grade has no "
          "missing_inputs")


def group_d() -> None:
    head("D. THE SOURCES")
    sites = {"altdata/book_b_scanner.py": 1, "altdata/narratives.py": 2,
             "altdata/state_calibration.py": 1, "altdata/thesis_register.py": 1,
             "daily_cascade/outlooks.py": 1, "daily_cascade/precis.py": 1,
             "altdata/probability_ledger.py": 1}
    for f, n in sites.items():
        src = (REPO / f).read_text(encoding="utf-8")
        calls = [c for c in ast.walk(ast.parse(src)) if isinstance(c, ast.Call)
                 and isinstance(c.func, ast.Attribute) and c.func.attr == "record"
                 and any(k.arg == "resolution_criterion" for k in c.keywords)]
        with_mi = [c for c in calls if any(k.arg == "missing_inputs" for k in c.keywords)]
        # the operator's by-hand `record` command is the one write left NULL
        want = n + (1 if f.endswith("probability_ledger.py") else 0)
        check(len(calls) == want and len(with_mi) == n,
              f"{f}: {len(with_mi)} of {len(calls)} ledger writes pass missing_inputs")
    sc = (REPO / "altdata" / "state_calibration.py").read_text(encoding="utf-8")
    check('missing_inputs=obj.get("absent_dimensions")' in sc,
          "the market-state rows carry their object's absent dimensions")
    src = (REPO / "altdata" / "error_corpus.py").read_text(encoding="utf-8")
    mods = set()
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Import):
            mods |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            mods.add(n.module or "")
    check(not (mods & {"anthropic", "altdata.model_meter", "daily_cascade.narrative",
                       "requests", "urllib.request"})
          and "model_meter" not in src and "anthropic" not in src,
          "the corpus builder calls no model (R-4)")
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    barred = {k for b in reg.get("market_state_barred") or [] for k in b["keys"]}
    check("learning.error_corpus" in reg["metrics"] and "learning.error_corpus" in barred,
          "its key is registered and barred from the object")
    check(not re.search(r"error_corpus", "".join(
        p.read_text(encoding="utf-8") for p in (REPO / "daily_cascade").glob("*.py"))),
          "it prints nowhere yet: no report module reads it")


def main() -> int:
    for g in (group_a, group_b, group_c, group_d):
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
