"""
Learning Loop v2, LL-4 (A80): code-built post-mortems and the shadow Red Team.

  A  A MISS YIELDS A FILE, A HIT NONE. The week's ledger miss and graded miss
     each get docs/postmortems/<saturday>/<id>.md, built from the corpus row:
     what was said, what happened, the margin, what was missing, the decision
     it fed (the register's thesis for a grade). A hit, and a miss outside the
     week, get none. The Doctrine's six questions, the seventh field and the
     note are blank; the six are 9.2's own words. A second run rewrites
     nothing; a dry run writes nothing.
  B  THE SHORTENING. Off by default (no call is made); on, an output that names
     a cause is refused, so is one carrying a figure the record does not hold,
     and a clean one prints under its own heading; the call goes through
     model_meter.
  C  THE SHADOW RED TEAM. One blinded call per material packet: the prompt
     carries the evidence and none of the thesis, counter-thesis, falsifiers or
     mechanism; the one file lands at docs/redteam/shadow/<date>-<packet>.md and
     nothing else is written under the root; the register's file is byte for
     byte unchanged (review_changed and red_team stay NULL); a second run makes
     no call; shadow_path refuses any other target; the module carries no SQL
     write and no register writer, opens the store mode=ro, and calls through
     model_meter.
  D  THE WIRING. Both commands have catalogue lines; neither module imports a
     report writer.

Synthetic fixtures only: no live store, no network, no model.

    python tools/validate_postmortems.py
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import ast
import datetime as dt
import hashlib
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
from altdata import grader, session  # noqa: E402
from altdata import postmortem as pm  # noqa: E402
from altdata import redteam_shadow as rt  # noqa: E402
from altdata.probability_ledger import ProbabilityLedger  # noqa: E402
from register.store import Register  # noqa: E402

PASS = FAIL = 0
LINE = "=" * 78
SAT = dt.date(2026, 10, 31)
AS_OF = "2026-11-01T12:00:00+00:00"
SECRET = ("SECRET-THESIS credit tightens into the print",
          "SECRET-COUNTER the tape disagrees",
          "SECRET-FALSIFIER a close above the wall")


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


def sha(p: str) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def tree(root: Path) -> list[str]:
    return sorted(str(p.relative_to(root)).replace("\\", "/")
                  for p in root.rglob("*") if p.is_file())


def fixture() -> tuple[str, dict]:
    db = str(Path(gate_tmp.mkdtemp("pm_")) / "chester.db")
    ids = {}
    reg = Register(db)
    did = reg.record(instrument="IWM", direction="short", thesis=SECRET[0],
                     edge_type="pivot", horizon="swing", invalidation="above 230",
                     book="B", decision_time="2026-10-20T14:00:00+00:00",
                     counter_thesis=SECRET[1], falsifiers=[SECRET[2]])
    ids["decision"] = did
    ids["packet"] = reg.attach_packet(did, {
        "run_id": "r1", "decision_time": "2026-10-20T14:00:00+00:00",
        "available_at_cutoff": "2026-10-20T13:59:00+00:00", "git_sha": "abc",
        "code_dirty": 0, "data_manifest_hash": "h",
        "data_manifest": {"files": [{"path": "data/x.csv", "sha256": "s", "bytes": 1}]},
        "metrics_registry_version": "1", "source_registry_version": "1",
        "output_hash": "o", "volatile_fields": ["computed_at"]})
    reg.conn.close()
    with ProbabilityLedger(db) as led:
        def rec(name, p, o, resolved):
            ids[name] = led.record(
                source="market_state", claim=f"claim {name}", probability=p,
                horizon_date="2026-10-28", resolution_criterion="fixture",
                emitted_at="2026-10-21T20:45:00+00:00", missing_inputs=["credit"])
            led.resolve(ids[name], o, resolved_at=f"{resolved}T21:00:00+00:00")
        rec("miss", 0.8, 0, "2026-10-29")
        rec("hit", 0.8, 1, "2026-10-29")
        rec("old", 0.8, 0, "2026-10-20")
    with grader.GradeStore(db) as gs:
        gs.write({"decision_id": did, "horizon": "swing",
                  "graded_at": "2026-10-30T21:00:00+00:00",
                  "horizon_date": "2026-10-30", "operator_action": "TAKE",
                  "decision_time": "2026-10-20T14:00:00+00:00",
                  "r_multiple_ruled": -1.0, "return_pct": -2.5,
                  "observations_json": "[]", "price_source": "fixture",
                  "method_version": grader.METHOD_VERSION})
        gs.conn.commit()
    ec.backfill(db, AS_OF, dry_run=False, objects=lambda at: None)
    return db, ids


# ---------------------------------------------------------------------------
def group_a(db: str, ids: dict) -> None:
    head("A. A MISS YIELDS A FILE, A HIT NONE")
    root = Path(gate_tmp.mkdtemp("pm_out_"))
    dry = pm.run_week(SAT, db, root, dry_run=True)
    check(len(dry["written"]) == 2 and tree(root) == [],
          "a dry run names two files and writes none")
    out = pm.run_week(SAT, db, root)
    rows = {r["ref_id"]: r for r in ec.rows(db)}
    cid = {k: ec.corpus_id("probability", ids[k]) for k in ("miss", "hit", "old")}
    dec = next(r for r in rows.values() if r["kind"] == "decision")
    d = root / "docs" / "postmortems" / "2026-10-31"
    check(sorted(out["written"]) == sorted([f"{cid['miss']}.md", f"{dec['corpus_id']}.md"])
          and tree(root) == sorted(f"docs/postmortems/2026-10-31/{n}"
                                   for n in out["written"]),
          "the week's ledger miss and graded miss each get one file, and only those")
    check(not (d / f"{cid['hit']}.md").exists() and not (d / f"{cid['old']}.md").exists(),
          "a hit gets none; a miss resolved outside the week gets none")
    md = (d / f"{cid['miss']}.md").read_text(encoding="utf-8")
    check("- **claim:** claim miss" in md and "- **probability:** 0.8" in md
          and "- **outcome:** 0" in md and "(brier_over_coin)" in md,
          "what was said, what happened and the margin are the stored rows")
    check("- **the source's missing inputs:** credit" in md
          and "- **the object's absent dimensions:** not recorded" in md,
          "what was missing: the source's inputs, and NULL as not recorded")
    check(pm.blank_fields(md) == [k for k, _ in pm.QUESTIONS] + ["rule_broken", "note"],
          "the six questions, the seventh field and the note are blank")
    doc = (REPO / "docs" / "whitepapers" / "operating-doctrine-whitepaper.md"
           ).read_text(encoding="utf-8")
    sec = doc[doc.find("### 9.2 The six questions"):doc.find("### 9.3")]
    check(all(q.split(" (")[0].rstrip("?") in sec for _, q in pm.QUESTIONS[:5])
          and "Was the signal itself degraded" in sec and len(pm.QUESTIONS) == 6,
          "the six are the Doctrine's 9.2 questions, in its words")
    check(not re.search(r"(?im)^\s*[-*|]*\s*\**\s*(?:root\s+)?cause\b", md)
          and "Shortened" not in md,
          "the code-built file carries no cause field and no model paragraph")
    dmd = (d / f"{dec['corpus_id']}.md").read_text(encoding="utf-8")
    check(f"- **thesis:** {SECRET[0]}" in dmd and "- **book:** B" in dmd
          and "(r_ruled)" in dmd,
          "a graded miss carries the decision it fed, as recorded at entry")
    (d / f"{cid['miss']}.md").write_text(md + "\nSTAMPED\n", encoding="utf-8")
    again = pm.run_week(SAT, db, root)
    check(not again["written"] and len(again["kept"]) == 2
          and (d / f"{cid['miss']}.md").read_text(encoding="utf-8").endswith("STAMPED\n"),
          "a second run rewrites nothing: a stamped file stands")
    check(pm.saturday_before(dt.date(2026, 11, 1)) == SAT
          and pm.saturday_before(SAT) == SAT
          and pm.saturday_before(dt.date(2026, 11, 6)) == SAT,
          "the week ends the Saturday on or before the run")


def group_b(db: str, ids: dict) -> None:
    head("B. THE SHORTENING")
    root = Path(gate_tmp.mkdtemp("pm_short_"))

    def boom(prompt: str) -> str:
        raise AssertionError("called")
    out = pm.run_week(SAT, db, root, call=boom)
    check(len(out["written"]) == 2 and not out["withheld"],
          "off by default: no call is made")
    row = next(r for r in ec.rows(db) if r["ref_id"] == ids["miss"])
    md = pm.build(row, None, SAT)
    for bad in ("The forecast missed because credit widened.",
                "Cause: the credit dimension was absent.",
                "The miss was driven by an absent credit read."):
        t, why = pm.shorten(md, row, None, call=lambda p, b=bad: b)
        check(t is None and "names a cause" in why, f"refused, a cause: {bad!r}")
    t, why = pm.shorten(md, row, None,
                        call=lambda p: "The forecast stood at 0.93 and resolved the other way.")
    check(t is None and "figure" in why, f"refused, a figure not in the record ({why})")
    good = "The market-state forecast stood at 0.8 and resolved the other way; credit was not read."
    t, why = pm.shorten(md, row, None, call=lambda p: good)
    check(t == good and not why, f"a clean paragraph passes ({why or 'no fault'})")
    seen = []
    t, _ = pm.shorten(md, row, None, call=lambda p: seen.append(p) or good)
    check(seen and "## The operator's stamp" not in seen[0]
          and pm.SHORTEN_PROMPT in seen[0],
          "the model sees parts 1 to 4 and the declared prompt, never the stamp")
    w = pm.with_short(md, good, "")
    check(w.index("## Shortened") < w.index("## The operator's stamp")
          and pm.blank_fields(w) == pm.blank_fields(md),
          "it prints above the stamp, which stays blank")
    root2 = Path(gate_tmp.mkdtemp("pm_short2_"))
    on = pm.run_week(SAT, db, root2, shorten_on=True,
                     call=lambda p: "It failed because of credit.")
    check(len(on["withheld"]) == 2 and all("Withheld: names a cause" in
          (Path(on["dir"]) / n).read_text(encoding="utf-8") for n in on["written"]),
          "on, a refused paragraph leaves the code-built parts and the reason")
    src = (REPO / "altdata" / "postmortem.py").read_text(encoding="utf-8")
    check("model_meter.create(" in src and "anthropic" not in src
          and "DEFAULT_MODEL" in src, "the call goes through model_meter, the narrative's model")


def group_c(db: str, ids: dict) -> None:
    head("C. THE SHADOW RED TEAM")
    root = Path(gate_tmp.mkdtemp("rt_out_"))
    day = session.utc_iso()[:10]
    before = sha(db)
    prompts = []
    out = rt.run(day, db, root, call=lambda p: prompts.append(p) or
                 "The case against: the tape is extended.")
    name = f"{day}-{ids['packet']}.md"
    check(out["packets"] == 1 and out["written"] == [name] and len(prompts) == 1,
          "one material packet, one call, one file")
    check(tree(root) == [f"docs/redteam/shadow/{name}"],
          "nothing is written under the root but the shadow file")
    check(sha(db) == before, "the register's database is byte for byte unchanged")
    import sqlite3
    c = sqlite3.connect(db)
    rc = c.execute("SELECT review_changed, red_team FROM decisions WHERE id=?",
                   (ids["decision"],)).fetchone()
    c.close()
    check(rc == (None, None), "review_changed and red_team stay NULL")
    p = prompts[0]
    check(not any(s in p for s in SECRET) and "SECRET" not in p,
          "blinded: no thesis, counter-thesis or falsifier reaches the prompt")
    check('"instrument": "IWM"' in p and '"invalidation": "above 230"' in p
          and "data/x.csv" in p and p.startswith(rt.SHADOW_PROMPT),
          "the evidence does: the instrument, the invalidation, the packet's inputs")
    f = (root / "docs" / "redteam" / "shadow" / name).read_text(encoding="utf-8")
    check("never to review_changed" in f and "The case against" in f,
          "the file records the read, the prompt and its shadow status")
    again = rt.run(day, db, root, call=lambda p: prompts.append(p) or "x")
    check(len(prompts) == 1 and again["kept"] == [name], "a second run makes no call")
    none = rt.run("2026-01-02", db, root, call=lambda p: prompts.append(p) or "x")
    check(none["packets"] == 0 and len(prompts) == 1, "another day's packets are not read")
    try:
        bad = rt.shadow_path(root, day, "../../../etc/passwd")
        ok = bad.parent == (root / "docs" / "redteam" / "shadow").resolve()
    except rt.ShadowPathError:
        ok = True
    check(ok, "shadow_path keeps a hostile packet id inside the shadow directory")
    try:
        rt.shadow_path(root, "../../x", "p")
        ok = False
    except (rt.ShadowPathError, ValueError):
        ok = True
    check(ok, "and refuses a target that is not a dated shadow file")
    src = (REPO / "altdata" / "redteam_shadow.py").read_text(encoding="utf-8")
    code = "\n".join(line for line in src.splitlines()
                     if not line.lstrip().startswith(("#", '"', "'")))
    check(not re.search(r"\b(INSERT|UPDATE|DELETE|CREATE|ALTER)\b", code)
          and "register.store" not in src and "Register(" not in src
          and "attach_packet" not in src and "supersede" not in src,
          "no SQL write and no register writer in the module")
    check(src.count("sqlite3.connect(") == 1 and "?mode=ro" in src
          and "model_meter.create(" in src and "anthropic" not in src,
          "the register is opened mode=ro; the call goes through model_meter")


def group_d() -> None:
    head("D. THE WIRING")
    cat = yaml.safe_load((REPO / "config" / "catalogue_commands.yaml")
                         .read_text(encoding="utf-8"))
    cmds = cat.get("commands") or cat
    check("altdata.postmortem" in cmds and "altdata.redteam_shadow" in cmds,
          "both commands have catalogue lines")
    for f in ("postmortem.py", "redteam_shadow.py"):
        src = (REPO / "altdata" / f).read_text(encoding="utf-8")
        mods = set()
        for n in ast.walk(ast.parse(src)):
            if isinstance(n, ast.Import):
                mods |= {a.name for a in n.names}
            elif isinstance(n, ast.ImportFrom):
                mods.add(n.module or "")
        check(not any(m.startswith(("monthly_macro", "register", "alpha"))
                      or m in ("daily_cascade.stack_render", "state.emit") for m in mods),
              f"{f} imports no report writer, register or lab")


def main() -> int:
    db, ids = fixture()
    for g in (group_a, group_b, group_c):
        try:
            g(db, ids)
        except Exception as exc:                                # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    try:
        group_d()
    except Exception as exc:                                    # noqa: BLE001
        import traceback
        traceback.print_exc()
        check(False, f"group_d raised {type(exc).__name__}: {exc}")
    print(f"\n{PASS} passed, {FAIL} failed")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
