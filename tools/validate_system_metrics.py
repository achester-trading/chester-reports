"""
THE SYSTEM-METRICS BLOCK (EL-6) AND THE DATED APPENDICES (EL-4), on fixtures.

  A  THE FIVE FIGURES. Uptime from a fixture heartbeat log (the share of
     verdict=ok lines in the window, a line without a verdict ignored); feed
     completeness from a fixture freshness roster, by family; the incidents of a
     fixture month counted by hand (entries outside it and nested lines left
     out); model cost by report from fixture model_calls rows, "recorded from"
     its first call; withheld drafts from a fixture log, duplicates counted once.
  B  NOT RECORDED. Each source absent prints "not recorded", never zero: no
     heartbeat log, no roster, no incidents file, no model_calls table (usage
     not recorded), no withheld log.
  C  THE BASELINE (ruling 5, 17 Oct 2026). The agenda's feeds line and the
     audit's measured figures of 14 Oct, each labelled "by hand, Audit #4,
     14 Oct"; days up, session hours and model cost "not recorded".
  D  THE READERS. gather() reads a fixture log directory, a temporary
     model_calls table and a fixture incidents file -- never the live store, no
     fetch, no model; the withheld-drafts log is written and read back.
  E  THE BUDGET. The block is data: appended to an edition, it adds no words
     to the budget and no chart; the Quarterly's opening prints it before
     section 1 in the page and the Markdown.
  F  THE DATED APPENDIX (EL-4). check_library's dated_appendix_faults on
     fixtures: the as-of heading, an entry heading dated after it, a figure in a
     lesson entry, a ruled entry not quoted verbatim; and the Doctrine itself
     passes, with its abstention reason one the register knows.

    python tools/validate_system_metrics.py
"""

from __future__ import annotations

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

from gate_tmp import mkdtemp  # noqa: E402

from altdata import system_metrics as sm  # noqa: E402
from altdata import withheld_log  # noqa: E402

FIX = REPO / "tests" / "fixtures" / "system_metrics"
LINE = "=" * 78
PASS = FAIL = 0
TD = Path(mkdtemp("validate_system_metrics_"))
OCT = ("2026-10-01", "2026-10-31")


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


FRESH = {"session": "2026-10-30", "feeds": {
    "prices": {"expected": 108, "fresh": 106, "stale": 1, "pending": 1},
    "official": {"expected": 96, "fresh": 96, "stale": 0, "pending": 0},
    "vendor": {"expected": 4, "fresh": 0, "stale": 0, "pending": 4}}}
ROWS = [("daily_close", 1000, 200, "2026-10-19T20:40:00+00:00"),
        ("daily_close", 1500, 300, "2026-10-20T20:40:00+00:00"),
        ("weekly_tactical", 9000, 2500, "2026-10-25T09:01:00+00:00")]


def _src(**over) -> dict:
    s = {"heartbeat": (FIX / "heartbeat_check-2026-10.txt").read_text(
            encoding="utf-8").splitlines(),
         "freshness": FRESH,
         "incidents": (FIX / "incidents.md").read_text(encoding="utf-8"),
         "model_rows": ROWS, "first_call": "2026-10-14T13:00:00+00:00",
         "withheld": (FIX / "withheld_drafts.jsonl").read_text(
            encoding="utf-8").splitlines()}
    s.update(over)
    return s


def _row(b: dict, metric: str) -> list:
    return next(r for r in b["tables"][0]["rows"] if r[0] == metric)


def group_a() -> None:
    head("A. THE FIVE FIGURES, FROM FIXTURES")
    b = sm.block(*OCT, _src(), title="October 2026")
    up = b["data"]["uptime"]
    check(up["ok"] == 5 and up["total"] == 7 and _row(b, "Uptime")[1]
          == "71.4% (5 of 7 checks verdict=ok)" and _row(b, "Uptime")[2] == "1–31 Oct 2026",
          f"uptime: 5 of the 7 October checks verdict=ok, by hand; the September line "
          f"and the line without a verdict left out ({_row(b, 'Uptime')[1]})")
    fr = _row(b, "Feed completeness")
    fam = b["tables"][1]
    check(fr[1] == "202 of 208 fresh (97.1%)" and fr[2] == "at the 30 Oct close"
          and [r[0] for r in fam["rows"]] == ["official", "prices", "vendor"]
          and fam["rows"][1][1:] == [106, 108, 1, 1],
          f"feed completeness: fresh over expected, by family, from the roster ({fr[1]})")
    inc = _row(b, "Incidents")
    check(inc[1] == "3 (INC-2 to INC-4)" and b["lines"] == [
              "INC-2 2026-10-01 — a paper position held without an accepted decision.",
              "INC-3 2026-10-01 — the second entry the same day.",
              "INC-4 2026-10-15 — a mid-month finding, not a blocker."],
          f"incidents: the hand count of the fixture month is 3, listed with dates; "
          f"September, November and a nested line left out ({inc[1]})")
    mc = _row(b, "Model cost")
    tok = b["tables"][2]
    check(mc[1] == "11,500 input / 3,000 output tokens, 3 calls"
          and mc[2] == "14–31 Oct 2026 (recorded from 14 Oct 2026)"
          and tok["rows"] == [["daily_close", "2", "2,500", "500"],
                              ["weekly_tactical", "1", "9,000", "2,500"]],
          f"model cost: tokens per report, recorded from the meter's first call ({mc[1]})")
    wh = _row(b, "Withheld drafts")
    later = sm.block(*OCT, _src(withheld=[ln for ln in _src()["withheld"]
                                          if '"2026-09' not in ln]), title="October 2026")
    check(wh[1] == "2" and wh[2] == "1–31 Oct 2026"
          and _row(later, "Withheld drafts")[2] == "19–31 Oct 2026 (recorded from 19 Oct 2026)",
          "withheld drafts: two in October (a duplicate line counted once); a log that "
          "begins mid-month says recorded from")
    cols = b["tables"][0]["columns"]
    check(cols == ["Metric", "October 2026", "Window", "Source",
                   "Baseline, by hand, Audit #4"]
          and all(r[2] and r[3] for r in b["tables"][0]["rows"]),
          "every figure carries its window and its source")


def group_b() -> None:
    head("B. A SOURCE THAT DOES NOT EXIST PRINTS 'NOT RECORDED'")
    b = sm.block(*OCT, {"heartbeat": None, "freshness": None, "incidents": None,
                        "model_rows": None, "first_call": None, "withheld": None})
    vals = {r[0]: r[1] for r in b["tables"][0]["rows"]}
    check(all(v == "not recorded" for v in vals.values()) and len(vals) == 5
          and len(b["tables"]) == 1 and not b["lines"],
          f"no log, no roster, no incidents file, no model_calls table, no withheld log: "
          f"every figure 'not recorded', never zero ({sorted(set(vals.values()))})")
    z = sm.block(*OCT, _src(model_rows=[]))
    check(_row(z, "Model cost")[1] == "0 calls",
          "a model_calls table with no call in the window is 0 calls, not 'not recorded'")


def group_c() -> None:
    head("C. THE AUDIT #4 BASELINE, WHERE THE AGENDA RECORDED IT")
    bl = sm.baseline()
    b = sm.block(*OCT, _src(), bl, title="October 2026")
    col = {r[0]: r[4] for r in b["tables"][0]["rows"]}
    agenda = (REPO / "docs" / "briefs" / "audit-4-agenda.md").read_text(encoding="utf-8")
    lab = "by hand, Audit #4, 14 Oct"
    check(col["Feed completeness"] == ("official 96/96; external 52 of 5x, one stale "
                                       "(AAII, the operator's drop); the 9 Oct line "
                                       f"({lab})")
          and col["Uptime"] == col["Model cost"] == col["Incidents"]
          == col["Withheld drafts"] == "not recorded"
          and "official 96/96, external 52/5x, one stale" in agenda,
          "ruling 5: the agenda's feeds line prints, labelled; uptime, model cost, "
          "incidents and withheld drafts print 'not recorded' for the baseline")
    mt = [t for t in b["tables"] if t["columns"][0] == "Audit #4 baseline"]
    rows = {r[0]: (r[1], r[2]) for r in (mt[0]["rows"] if mt else [])}
    want = {"Store rows": "2.33 million, 688,000 of them FRED",
            "Store growth": "about 86,000 rows a weekday",
            "Disk free": "14 GB of 38 GB", "Backup zip": "about 115 MB",
            "Drive backup folder": "7.6 GB"}
    check(all(rows.get(k) == (v, lab) for k, v in want.items())
          and all(rows.get(k) == ("not recorded", "")
                  for k in ("Days up", "Session hours", "Model cost"))
          and len(rows) == 8,
          f"ruling 5: the audit's five measured figures of 14 Oct, each labelled "
          f"'{lab}'; days up, session hours and model cost 'not recorded' "
          f"({len(rows)} rows)")


def group_d() -> None:
    head("D. THE READERS: FIXTURE FILES AND A TEMPORARY TABLE, NOTHING LIVE")
    logs = TD / "logs"
    logs.mkdir(exist_ok=True)
    (logs / "heartbeat_check-2026-10.log").write_text(
        (FIX / "heartbeat_check-2026-10.txt").read_text(encoding="utf-8"), encoding="utf-8")
    db = TD / "chester.db"
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE model_calls (run_id TEXT, report TEXT, section TEXT, "
                "attempt INTEGER, model TEXT, input_tokens INTEGER, output_tokens "
                "INTEGER, called_at TEXT)")
    con.executemany("INSERT INTO model_calls VALUES (?,?,?,?,?,?,?,?)",
                    [("r", r, "s", 1, "m", i, o, at) for r, i, o, at in ROWS]
                    + [("r", "daily_close", "s", 1, "m", 5, 5, "2026-09-30T20:00:00+00:00")])
    con.commit()
    con.close()
    arch = TD / "archive"
    ed = {"sections": [{"id": "read", "withheld": "narrative withheld: numeral audit"},
                       {"id": "tape"},
                       {"id": "mechanics", "subsections": [
                           {"id": "dealer", "withheld": "flag word"}]}]}
    n = withheld_log.record_edition("daily_close", "daily_close_2026-10-19_stack.json",
                                    ed, str(arch), now="2026-10-19T20:45:00+00:00")
    src = sm.gather(*OCT, db_path=str(db), log_dir=str(logs), archive_dir=str(arch),
                    incidents_path=FIX / "incidents.md")
    b = sm.block(*OCT, src)
    check(n == 2 and _row(b, "Withheld drafts")[1] == "2"
          and all('"reason"' in x and "draft" not in json.loads(x) for x in src["withheld"]),
          "the withheld-drafts log: one line per withheld section and sub-section, "
          "written at archive time and read back; the reason, never the draft")
    check(_row(b, "Uptime")[1].startswith("71.4%") and _row(b, "Incidents")[1].startswith("3")
          and _row(b, "Model cost")[1] == "11,500 input / 3,000 output tokens, 3 calls"
          and src["first_call"].startswith("2026-09-30") and src["freshness"] is None,
          "gather() reads the fixture log directory, the temporary model_calls table "
          "(the window in ET) and the fixture incidents file; no store, no roster")
    check(withheld_log.read(str(TD / "none")) is None
          and withheld_log.record_edition("x", "y", {"sections": [{"id": "a"}]}, str(arch)) == 0,
          "no log is None; an edition with nothing withheld writes nothing")
    # RULING 4 OF 17 OCT 2026: every edition writes the log.
    writers = {"morning_anchor": "daily_cascade/morning_anchor.py",
               "daily_close": "daily_cascade/stack_close.py",
               "weekly_tactical": "daily_cascade/weekly_stack.py",
               "monthly_macro": "monthly_macro/stack.py",
               "alt_asset_quarterly": "monthly_macro/quarterly.py",
               "midday_alert": "daily_cascade/midday_gate.py"}
    missing = [r for r, f in writers.items()
               if not re.search(r"withheld_log\.record(_edition)?\(\s*\"" + r + "\"",
                                (REPO / f).read_text(encoding="utf-8"))]
    check(set(writers) == set(withheld_log.REPORTS) and not missing,
          f"ruling 4: the anchor, the close, the Weekly, the Monthly, the Quarterly "
          f"and the 12:30 slot each write the withheld-drafts log (missing: {missing})")
    arch2 = TD / "archive_anchor"
    k = withheld_log.record("morning_anchor", "morning_anchor_2026-10-19.html",
                            [("narrative", "audit_failed: numeral audit")], str(arch2),
                            now="2026-10-19T11:00:00+00:00")
    w = sm.withheld(withheld_log.read(str(arch2)), *OCT)
    check(k == 1 and w == {"recorded": True, "count": 1, "first": "2026-10-19"}
          and withheld_log.record("midday_alert", "midday_2026-10-19_1230.json", [],
                                  str(arch2)) == 0,
          "an anchor's withheld draft is one line the block counts; an unnarrated "
          "12:30 alert writes nothing")


def group_e() -> None:
    head("E. THE BUDGET HOLDS; THE QUARTERLY OPENS ON IT")
    from daily_cascade import stack, stack_render  # noqa: PLC0415
    b = sm.block(*OCT, _src(), sm.baseline(), title="October 2026")
    ed = {"sections": [{"id": "read", "title": "The read", "claim": "One claim.",
                        "paragraphs": ["A paragraph of prose words here."]}],
          "detail": [], "summary": [], "chart_count": 2, "as_of": "2026-11-01T12:00:00Z"}
    before = stack.edition_words(ed)
    ed2 = dict(ed, detail=[b])
    check(stack.edition_words(ed2) == before and stack.section_words(b) == 0
          and ed2["chart_count"] == 2,
          f"appended as a detail table the block adds no words to the budget "
          f"({before} before and after) and no chart: it displaces nothing")
    q = dict(ed, opening=[sm.block("2026-07-01", "2026-09-30", _src(), title="Q3 2026")])
    html = stack_render.page_html(q, "quarterly", "Quarterly")
    md = stack_render.markdown(q, "quarterly", "Quarterly")
    check(html.index("System metrics, Q3 2026") < html.index("The read")
          and md.index("## System metrics, Q3 2026") < md.index("The read"),
          "the Quarterly's opening table prints before section 1, in the page and the "
          "Markdown")


def group_f() -> None:
    head("F. THE DATED APPENDIX (EL-4): check_library 14 on fixtures")
    import check_library as cl  # noqa: PLC0415
    good = ("## Part I — x\n\n## Appendix D — Dated: Rulings (as of 17 October 2026)\n\n"
            "### D.1 The sitting of 2 October 2026\n\nThe band is 60–70%.\n\n"
            "### D.2 Incidents and their lessons\n\n| INC-6 | 1 Oct 2026 | A lesson, "
            "ruled 2 October, item 8 |\n")
    check(not cl.dated_appendix_faults(good),
          "a dated appendix with its as-of, dated entries, and a lesson entry carrying "
          "ids and dates only, passes (a figure in a ruling's entry is allowed)")
    bad_head = good.replace(" (as of 17 October 2026)", "")
    later = good.replace("### D.1 The sitting of 2 October 2026",
                         "### D.1 The sitting of 2 November 2026")
    fig = good.replace("A lesson, ruled", "A loss of 8,951 USD, ruled")
    check(cl.dated_appendix_faults(bad_head) and cl.dated_appendix_faults(later)
          and any("figure in a lesson" in f for f in cl.dated_appendix_faults(fig)),
          "no as-of in the heading, an entry dated after it, and a figure in a lesson "
          "entry each fail")
    minutes = (REPO / "docs" / "briefs" / "doctrine-monthly-2026-10-minutes.md").read_text(
        encoding="utf-8")
    doc = (REPO / "docs" / "whitepapers" / "operating-doctrine-whitepaper.md").read_text(
        encoding="utf-8")
    tampered = doc.replace("and `expression_currency` is a required field",
                           "and the currency is a required field")
    check(not cl.dated_appendix_faults(doc, minutes)
          and any("not quoted as ruled" in f
                  for f in cl.dated_appendix_faults(tampered, minutes)),
          "the Doctrine's Appendix D passes and quotes item 8's three entries verbatim; "
          "a reworded entry fails")
    check("## Part X — Change, Attention and the Intraday Rung" in doc
          and "At least **20** graded outcomes" in doc and "**Seven packet approvals"
          in doc and "at least 40 graded paper trades" in doc
          and "abstention with the reason `attention_budget`" in doc,
          "the Doctrine's Part X carries the ladder (N = 20), the budget (seven; the "
          "attention_budget abstention) and the rung (the kill criterion at 40)")


def main() -> int:
    print(f"{LINE}\nTHE SYSTEM-METRICS BLOCK (EL-6) AND THE DATED APPENDICES (EL-4)\n{LINE}")
    for g in (group_a, group_b, group_c, group_d, group_e, group_f):
        try:
            g()
        except Exception as exc:                                # noqa: BLE001
            import traceback                                    # noqa: PLC0415
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
