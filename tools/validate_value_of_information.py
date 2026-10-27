"""
Learning Loop v2, LL-2 (A80): value of information.

  A  THE FIXTURE RANKS THE COSTLY INPUT FIRST. A seeded ledger where one missing
     input (credit) carries all the error: it ranks first, its Brier difference
     is the closed-form figure, and its bootstrap interval excludes zero; an
     input whose rows forecast as well as the rest ranks below it with a
     negative difference; an input under the floor of 30 affected rows accrues
     and is not ranked; a row with nothing recorded enters no comparison.
  B  THE METHOD IS DECLARED. The seed, the resamples and the level are
     constants; two builds give the same intervals, and so does the same set of
     rows in another order; an input that costs nothing has an interval holding
     zero; the share is the rows missing over the cell's recorded rows.
  C  WHAT WAS MISSING AT EMISSION. The row's own missing_inputs united with the
     object held at the instant (its absent dimensions, its legs as "leg:");
     NULL with no object is unrecorded, never "nothing missing"; the error
     corpus's misses are counted per input.
  D  WHERE IT PRINTS, AND WHAT IT MAY NOT DO. The Monthly's Lab report hook
     appends it after decision quality's (and stands alone without a lab); the
     pack command prints it; the build leaves the database byte for byte; no
     model is imported; the key is registered and barred from the object; the
     catalogue names the command; Book B's candidate rows record the legs they
     could not read.

Synthetic fixtures only: no live store, no network, no model.

    python tools/validate_value_of_information.py
"""

from __future__ import annotations

import ast
import hashlib
import random
import re
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
from altdata import value_of_information as voi  # noqa: E402
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


# 40 rows missing credit, all wrong (Brier 0.64); 40 missing growth and 60
# missing nothing, all right (0.04); 29 missing breadth, wrong (under the floor);
# 10 weekly-stance rows recording nothing.
SPEC = (("credit", 40, 0), ("growth", 40, 1), (None, 60, 1), ("breadth", 29, 0))


def fixture() -> str:
    db = str(Path(gate_tmp.mkdtemp("voi_")) / "chester.db")
    with ProbabilityLedger(db) as led:
        i = 0
        for name, n, o in SPEC:
            for _ in range(n):
                i += 1
                pid = led.record(
                    source="market_state", claim=f"claim {i}", probability=0.8,
                    horizon_date="2026-09-30", resolution_criterion="fixture",
                    emitted_at="2026-09-24T20:45:00+00:00",
                    missing_inputs=[name] if name else [])
                led.resolve(pid, o, resolved_at="2026-10-01T21:00:00+00:00")
        for j in range(10):
            pid = led.record(
                source="weekly_stance", claim=f"stance {j}", probability=0.8,
                horizon_date="2026-10-02", resolution_criterion="fixture",
                emitted_at="2026-09-25T20:45:00+00:00", missing_inputs=None)
            led.resolve(pid, 0, resolved_at="2026-10-02T21:00:00+00:00")
    return db


def sha(p: str) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
def group_a(db: str) -> dict:
    head("A. THE FIXTURE RANKS THE COSTLY INPUT FIRST")
    b = voi.build(AS_OF, db, objects=False, corpus=[])
    r = b["ranked"]
    top = r[0] if r else {}
    check(top.get("input") == "credit" and top.get("family") == "market_state"
          and top.get("horizon") == "1-7d",
          f"credit ranks first ({[e['input'] for e in r]})")
    had = (40 * 0.04 + 60 * 0.04 + 29 * 0.64) / 129
    check(abs(top.get("diff", 0) - (0.64 - had)) < 1e-9
          and top.get("n_missing") == 40 and top.get("n_had") == 129,
          f"its difference is 0.64 less the had-rows' mean, {0.64 - had:.4f} "
          f"(n 40 against 129)")
    check(top.get("lo") is not None and top["lo"] > 0 and top["hi"] >= top["lo"],
          f"its interval excludes zero [{top.get('lo', 0):+.4f}, {top.get('hi', 0):+.4f}]")
    g = next((e for e in r if e["input"] == "growth"), None)
    check(g is not None and g["diff"] < 0 and r.index(g) > 0,
          "growth, whose rows forecast well, ranks below with a negative difference")
    br = next((e for e in b["entries"] if e["input"] == "breadth"), None)
    check(br is not None and br["accruing"] and br not in r and br["lo"] is None,
          "breadth, 29 affected rows, accrues under the floor of 30 and is not ranked")
    check(b["unrecorded"] == 10 and b["recorded"] == 169
          and not any(e["family"] == "weekly_stance" for e in b["entries"]),
          "the ten rows recording nothing enter no comparison")
    txt = "\n".join(voi.tables_md(b))
    check("| 1 | credit | market_state | 1-7d | 40 | 129 |" in txt
          and "breadth in market_state 1-7d (accruing, n=29 of 30)" in txt,
          "the table prints the rank and the accruing input")
    return b


def group_b(db: str, b: dict) -> None:
    head("B. THE METHOD IS DECLARED")
    check(voi.SEED == 20261025 and voi.RESAMPLES == 2000 and voi.LEVEL == 0.95
          and voi.FLOOR == 30, "seed 20261025, 2,000 resamples, 95%, floor 30")
    b2 = voi.build(AS_OF, db, objects=False, corpus=[])
    check([(e["input"], e["lo"], e["hi"]) for e in b["ranked"]]
          == [(e["input"], e["lo"], e["hi"]) for e in b2["ranked"]],
          "a second build gives the same intervals")
    from altdata import decision_quality as dq
    rows = dq.resolved_rows(AS_OF, db)
    random.Random(7).shuffle(rows)
    sh = voi.entries(rows)
    k = {e["input"]: (e["lo"], e["hi"]) for e in b["entries"]}
    check(all(k[e["input"]] == (e["lo"], e["hi"]) for e in sh["entries"]),
          "the same rows in another order give the same intervals")
    flat = []
    for i in range(100):
        bad = i % 2 == 0
        flat.append({"source": "x", "emitted_at": "2026-09-01", "horizon_date":
                     "2026-09-05", "probability": 0.8, "outcome": 0 if bad else 1,
                     "missing_inputs": '["x"]' if i < 40 else "[]"})
    e = voi.entries(flat)["entries"][0]
    check(abs(e["diff"]) < 1e-12 and e["lo"] < 0 < e["hi"],
          f"an input that costs nothing has an interval holding zero "
          f"[{e['lo']:+.4f}, {e['hi']:+.4f}]")
    check(abs(e["share"] - 0.4) < 1e-12 and abs(b["ranked"][0]["share"] - 40 / 169) < 1e-12,
          "the share is the rows missing over the cell's recorded rows")


def group_c(db: str) -> None:
    head("C. WHAT WAS MISSING AT EMISSION")
    obj = {"absent_dimensions": ["credit", "breadth"],
           "absent_contradictions": ["c7_credit_vs_equity"]}
    r = {"emitted_at": "2026-09-24", "missing_inputs": '["credit", "volume"]'}
    check(voi.missing_at_emission(r, lambda at: obj)
          == {"credit", "volume", "breadth", "leg:c7_credit_vs_equity"},
          "the row's own inputs united with the object's dimensions and legs, once each")
    check(voi.missing_at_emission({"emitted_at": "x", "missing_inputs": None}) is None
          and voi.missing_at_emission({"emitted_at": "x", "missing_inputs": None},
                                      lambda at: None) is None,
          "NULL with no object held is unrecorded")
    check(voi.missing_at_emission({"emitted_at": "x", "missing_inputs": "[]"}) == set(),
          "[] is recorded as nothing missing")
    check(voi.missing_at_emission({"emitted_at": "x", "missing_inputs": None},
                                  lambda at: obj) == {"credit", "breadth",
                                                      "leg:c7_credit_vs_equity"},
          "a row written before the field still reads the object held then")
    ec.backfill(db, AS_OF, dry_run=False, objects=lambda at: None)
    b = voi.build(AS_OF, db, objects=False)
    cm = {e["input"]: e["corpus_misses"] for e in b["entries"]}
    check(cm.get("credit") == 40 and cm.get("breadth") == 29 and cm.get("growth") == 0
          and b["corpus_rows"] == 79,
          f"the corpus's misses are counted per input ({cm}; {b['corpus_rows']} rows)")


def group_d(db: str) -> None:
    head("D. WHERE IT PRINTS, AND WHAT IT MAY NOT DO")
    before = sha(db)
    voi.build(AS_OF, db, objects=True)
    voi.pack_md(AS_OF, db, objects=True)
    check(sha(db) == before, "a build reading the objects leaves the database byte for byte")
    lab = voi.with_lab_report(("lab_2026-11.md", "# Lab report\n", "markdown"),
                              "2026-11-01", db)
    alone = voi.with_lab_report(None, "2026-11-01", db)
    check(lab[0] == "lab_2026-11.md" and "## Value of information" in lab[1]
          and lab[1].startswith("# Lab report"),
          "the hook appends the section to the Lab report")
    check(alone is None,
          "with no Lab report the edition gains no attachment (the Monthly's two stay two; B80)")
    run = (REPO / "monthly_macro" / "run.py").read_text(encoding="utf-8")
    check(run.find("voi.with_lab_report") > run.find("lab = with_lab_report(lab, stamp)") > 0,
          "the Monthly calls it after decision quality's hook")
    pack = voi.pack_md(AS_OF, db, objects=False)
    check(pack.startswith("## Value of information: the search order (LL-2)")
          and "1. credit" in pack, "the pack command prints the section and the order")
    src = (REPO / "altdata" / "value_of_information.py").read_text(encoding="utf-8")
    mods = set()
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Import):
            mods |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            mods.add(n.module or "")
    check(not (mods & {"anthropic", "altdata.model_meter", "daily_cascade.narrative"})
          and "model_meter" not in src and "anthropic" not in src,
          "no model is imported (computed, never written by a model)")
    check(not re.search(r"\b(INSERT|UPDATE|DELETE|CREATE)\b", src),
          "the module carries no write statement")
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    barred = {k for x in reg.get("market_state_barred") or [] for k in x["keys"]}
    key = "learning.value_of_information"
    check(key in reg["metrics"] and key in barred
          and reg["metrics"][key].get("trigger_eligible") is False,
          "its key is registered, not trigger-eligible, and barred from the object")
    cat = yaml.safe_load((REPO / "config" / "catalogue_commands.yaml")
                         .read_text(encoding="utf-8"))
    check("altdata.value_of_information" in (cat.get("commands") or cat),
          "the catalogue names the command")
    from altdata import book_b_scanner as bb
    confs = [{"family": "relative strength", "met": True},
             {"family": "positioning", "met": None}]
    check(bb.missing_inputs_of(confs, {"volume_unconfirmed": True}, None)
          == ["confirmation:positioning", "dollar_adv", "volume"]
          and bb.missing_inputs_of(confs[:1], {}, 1e6) == [],
          "Book B's candidates record the legs they could not read")
    bsrc = (REPO / "altdata" / "book_b_scanner.py").read_text(encoding="utf-8")
    check('missing_inputs=c.get("missing_inputs", [])' in bsrc
          and '"missing_inputs": missing_inputs_of(confs, pv, adv)' in bsrc,
          "and their ledger rows carry it at emission")


def main() -> int:
    db = fixture()
    b = None
    for g in (group_a, group_b, group_c, group_d):
        try:
            if g is group_a:
                b = g(db)
            elif g is group_b:
                g(db, b)
            else:
                g(db)
        except Exception as exc:                                # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{PASS} passed, {FAIL} failed")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
