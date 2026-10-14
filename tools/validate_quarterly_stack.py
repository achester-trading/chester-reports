"""
Validation gate for AQ-1: the quarterly cadence (change order of 10 Oct 2026,
sections 3 and 4.1), modelled on validate_monthly_stack.py.

Fixtures only -- the Monthly stack gate's synthetic store, seeded in a temporary
directory, with the clock pinned at Sat 10 Oct 2026 so the Quarterly covers 3Q26.
It never reads the live store.

  A CONFIG     the cadence present and complete beside the other three; the two
               budgets; the chart cap; every section tiered; the eleven chapters
               and the section 4.1 template, light and country chapters' items.
  B WINDOW     the payload's quarter window and label; the Monthly's unchanged.
  C DRY RUN    the front matter from the stack and eleven chapter shells, end to
               end: order, tiers, lead before reference, "not yet built -- AQ-2",
               the executive summary's paragraph count equal to the chapter
               count, the read's time from lead items only, the 90-minute target
               warned on and never withheld, both reading times in the header.
  D HOOKS      AQ-6's and AQ-5's hooks degrade to "not yet" when their modules
               are absent, fill their items when present, and never raise.
  E STATE      `alt_asset` in state/emit.py; the run records under it, and a
               dry run records nothing.
  F TIMER      the unit and timer, second Saturday after quarter-end at 06:00
               ET, shipped disabled (not in DEPLOY_TIMERS).

    python tools/validate_quarterly_stack.py
"""

from __future__ import annotations

import copy
import datetime as dt
import io
import os
import re
import sys
import types
from contextlib import redirect_stdout
from pathlib import Path

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

# The Monthly stack gate's fixtures. Importing it points every store at its own
# temporary directory before anything opens one.
import validate_monthly_stack as vms                           # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LINE = "=" * 78
PASS = FAIL = WARN = 0
REPORT_DATE = "2026-10-10"
AS_OF = "2026-10-10T10:00:00+00:00"


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def warn(m: str) -> None:
    global WARN
    WARN += 1
    print(f"  WARN  {m}")


def pinned(fn):
    """Run `fn` with the session clock at the fixture's report date."""
    from altdata import session
    from monthly_macro import payload
    saved = (session.session_date, session.session_date_obj, payload.previous_monthly)
    session.session_date = lambda *a, **k: REPORT_DATE
    session.session_date_obj = lambda *a, **k: dt.date.fromisoformat(REPORT_DATE)
    payload.previous_monthly = lambda as_of=None: None
    try:
        return fn()
    finally:
        session.session_date, session.session_date_obj, payload.previous_monthly = saved


def build_payload() -> dict:
    from monthly_macro import payload
    return pinned(lambda: payload.build(AS_OF, run_id="q-fixture", period="quarter"))


# ---------------------------------------------------------------------------
def group_a(cfg: dict) -> None:
    from daily_cascade import cadence
    from monthly_macro import quarterly as q
    print(f"\n{LINE}\nA. THE CADENCE IN CONFIG\n{LINE}")
    cads = cfg.get("cadences") or {}
    base = set(cads.get("monthly") or {})
    qc = cads.get("quarterly") or {}
    check("quarterly" in cadence.NAMES and qc and base <= set(qc),
          f"the quarterly cadence is the fourth, with every key the Monthly's "
          f"carries (missing: {sorted(base - set(qc)) or 'none'})")
    c = cadence.get("quarterly")
    check(c["period"] == "quarter" and c["column"] == "The quarter"
          and c["report"] == "the Quarterly" and c["depth_words"]
          and cadence.Period.of("quarterly").on == "on the quarter",
          "its period noun, column head, report name and depth allowances")
    check(c["budget"] == {"words": None, "charts": 40}
          and c["reading_target_minutes"] == 90
          and (c.get("read_budget") or {}).get("target_minutes") == 90
          and (c.get("read_budget") or {}).get("on_over") == "warn"
          and (c.get("reference_budget") or {}).get("words") is None
          and c.get("trim_to_budget") is False,
          "two budgets: the read at 90 minutes, warned on; the reference "
          "unbudgeted; chart cap 40; nothing trimmed")
    secs = [s for s in cfg["sections"] if s["id"] != "reading"]
    check(all(s.get("quarterly") and s.get("quarterly_tier") in q.TIERS for s in secs)
          and not next(s for s in cfg["sections"] if s["id"] == "reading").get(
              "quarterly"),
          "every front-matter section has a quarterly depth and a tier; Reading is "
          "the Monthly's only")
    check([s["id"] for s in secs if s["quarterly_tier"] == "lead"] == ["read"],
          "the read section is lead; the rest of the front matter is reference")
    ids = [c_["id"] for c_ in cfg.get("quarterly_chapters") or []]
    check(ids == ["metals", "oil_energy", "currency", "em", "china", "crypto",
                  "real_estate", "credit", "intl_equities", "thailand",
                  "agriculture"], f"the eleven chapters in order ({len(ids)})")
    tpl = cfg.get("quarterly_template") or []
    check([t["n"] for t in tpl] == ["1", "2", "3", "3a", "4", "5", "6", "7", "8",
                                    "9", "10", "11"]
          and all(t.get("tier") in q.TIERS for t in tpl),
          "the section 4.1 template: items 1 to 11 (with 3a), each tiered")
    check([t["n"] for t in tpl if t["tier"] == "lead"] == ["1", "2", "3", "7"],
          "the lead page: last quarter's theses graded, the new theses, the "
          "quarter, the falsification tests")
    chs = {c_["id"]: c_ for c_ in cfg["quarterly_chapters"]}
    light = [t["n"] for t in q.chapter_items(chs["credit"], cfg)]
    thai = [t["n"] for t in q.chapter_items(chs["thailand"], cfg)]
    deep = [t["n"] for t in q.chapter_items(chs["metals"], cfg)]
    check(light == ["1", "2", "3", "3a", "4", "7", "8", "10"]
          and thai == [t["n"] for t in tpl if t["n"] != "11"] and len(deep) == 12,
          "light chapters carry items 1-4, 7, 8, 10; Thailand all but 11; a deep "
          "chapter the whole template")


def group_b() -> None:
    from monthly_macro import v2
    print(f"\n{LINE}\nB. THE QUARTER'S WINDOW\n{LINE}")
    check(v2.month_bounds({"report_date": "2027-01-09", "period": "quarter"})
          == (dt.date(2026, 9, 30), dt.date(2026, 12, 31))
          and v2.period_label({"period": "quarter"}, dt.date(2026, 12, 31)) == "4Q26",
          "the 9 Jan 2027 edition reads 30 Sep against 31 Dec, labelled 4Q26")
    check(v2.month_bounds({"report_date": "2026-10-01"})
          == (dt.date(2026, 8, 31), dt.date(2026, 9, 30)),
          "the Monthly's window is unchanged")


def group_c(p: dict) -> dict:
    from daily_cascade import stack as stack_mod
    from monthly_macro import quarterly as q
    print(f"\n{LINE}\nC. THE DRY RUN, END TO END, ON A SYNTHETIC STORE\n{LINE}")
    check(p.get("period") == "quarter" and p["month_in_markets"]["month"] == "3Q26"
          and p["month_in_markets"]["start"] == "2026-06-30",
          f"the payload covers 3Q26 ({p['month_in_markets'].get('start')} to "
          f"{p['month_in_markets'].get('end')})")
    calls: list = []
    out = q.produce(p, archive_dir=str(Path(vms.TD) / "q"),
                    client=vms.client(calls, {}), db_path=vms.DB)
    ed = out["edition"]
    ids = [s["id"] for s in ed["sections"]]
    chs = q.chapters(ed)
    check(ids[:10] == list(stack_mod.SECTION_ORDER) and len(chs) == 11
          and ids[10:] == [c["id"] for c in chs],
          "the stack's ten sections as the front matter, then the eleven chapters")
    check(all(s.get("period") == "quarter" for s in ed["sections"])
          and ed["reading_target_minutes"] == 90 and ed["budget"]["charts"] == 40,
          "every section speaks of the quarter; the edition carries the read's "
          "target and the chart cap")
    fm_text = out["markdown"].split(f"## 11 · {chs[0]['title']}")[0]
    check("## 1 · The read" in fm_text and "this month" not in fm_text
          and "on the month" not in fm_text and "This month" not in fm_text,
          "no printed front-matter line speaks of the month")
    check(not q.tier_faults(ed), f"every section and chapter item is tiered "
                                 f"({q.tier_faults(ed)[:3]})")
    order_ok = True
    for c in chs:
        tiers = [x.get("tier") for x in c["subsections"]]
        div = [i for i, x in enumerate(c["subsections"]) if x.get("divider")]
        if not div or any(t != "lead" for t in tiers[:div[0]]) \
                or any(t != "reference" for t in tiers[div[0]:]):
            order_ok = False
    check(order_ok, "each chapter prints its lead items, then the reference "
                    "divider, then its reference items")
    met = chs[0]
    plain = [x for x in met["subsections"] if not x.get("divider") and not x.get("hook")]
    check(plain and all(x["not_tracked"] == [q.NOT_BUILT] for x in plain),
          f"every item AQ-2 fills prints \"{q.NOT_BUILT}\" in the not-yet-tracked "
          f"form ({len(plain)} in Metals)")
    check(f"Not yet tracked: {q.NOT_BUILT}." in out["markdown"]
          and f"Not yet tracked: {q.NOT_BUILT}." in out["html_email"]
          and q.REFERENCE_DIVIDER in out["markdown"],
          "and the renderer prints it, and the divider, on the page and in the "
          "Markdown")
    summ = ed.get("summary") or []
    check(len(summ) == len(chs) == 11 and all(e.get("text") for e in summ)
          and [e["id"] for e in summ] == [c["id"] for c in chs],
          f"the executive summary: one paragraph per chapter ({len(summ)} for "
          f"{len(chs)}), built last from the finished chapters")
    sums = [x for x in calls if "A reader" in x or "summary" in x.lower()]
    check(any('"Metals"' in x or "Metals" in x for x in calls)
          and all("the Monthly" not in x for x in calls)
          and any("the Quarterly" in x for x in calls),
          f"by the Monthly's machinery in the Quarterly's voice ({len(calls)} "
          f"calls, {len(sums)} summary frames)")
    # The read's time: lead items only.
    v = q.lead_view(ed)
    words = (sum(stack_mod.words(e.get("text")) for e in v["summary"])
             + sum(stack_mod.section_words(s) for s in v["sections"]))
    check(ed["read_minutes"] == max(1, -(-words // 250))
          and ed["reading_minutes"] >= ed["read_minutes"],
          f"the read's time is the summary and the lead items' prose at 250 words "
          f"a minute ({ed['read_minutes']} min; the whole edition "
          f"{ed['reading_minutes']} min)")
    ed2 = copy.deepcopy(ed)
    c2 = q.chapters(ed2)[0]
    ref = next(x for x in c2["subsections"] if x.get("tier") == "reference"
               and not x.get("divider"))
    ref["paragraphs"] = ["word " * 3000]
    lead = next(x for x in c2["subsections"] if x.get("tier") == "lead")
    check(q.read_minutes(ed2) == ed["read_minutes"],
          "3,000 words in a reference item leave the read's time unchanged")
    lead["paragraphs"] = ["word " * 3000]
    check(q.read_minutes(ed2) >= ed["read_minutes"] + 12,
          "the same words in a lead item add twelve minutes to it")
    big = copy.deepcopy(ed)
    for c in q.chapters(big):
        for x in c["subsections"]:
            if x.get("tier") == "lead" and not x.get("divider"):
                x["paragraphs"] = ["word " * 2200]
    big["read_minutes"] = q.read_minutes(big)
    w = q.read_warning(big)
    check(big["read_minutes"] > 90 and w and "90-minute target" in w
          and all(x.get("paragraphs") for c in q.chapters(big)
                  for x in c["subsections"] if x.get("tier") == "lead"
                  and not x.get("divider")),
          f"over 90 minutes the read is WARNED on ({w}) and nothing is withheld "
          f"or cut")
    if ed.get("read_warning"):
        warn(f"the fixture edition's read: {ed['read_warning']}")
    line = (f"the read: {ed['read_minutes']} min; the whole edition: "
            f"{ed['reading_minutes']} min")
    check(line in out["html_email"] and line in out["markdown"]
          and "target 90 minutes for the read" in out["markdown"],
          f"the header prints both: \"{line}\"")
    return {"ed": ed, "out": out}


def fake_modules(fault: bool = False):
    tr = types.ModuleType("fake_thesis_register")

    def graded_table(quarter, db_path=None, now=None, family=None, conn=None):
        if fault:
            raise RuntimeError("fixture fault")
        return {"columns": ["Family", "Horizon", "Thesis", "Probability", "Grade",
                            "Brier (coin 0.25)", "Why"],
                "rows": [[family, "3-month", "GLD above 360", "0.60", "hit",
                          "0.1600", "read 372 against > 360"]],
                "lines": []}

    def seed_table(cutoff, db_path=None, quarter=None, conn=None):
        return {"columns": ["Family", "Horizon", "Thesis", "Weight", "Resolves",
                            "Brier"],
                "rows": [["metals", "12-month", "bid holds", "0.45", "2027-12-31",
                          "pending"],
                         ["oil", "3-month", "WTI above 70", "0.55", "2027-03-31",
                          "pending"]]}
    tr.graded_table, tr.seed_table = graded_table, seed_table
    co = types.ModuleType("fake_correlation")
    co.peer_table = lambda st, now, cfg=None: [
        {"asset": "gold", "peer": "dxy", "latest": -0.41, "median": -0.30,
         "divergence": -0.11, "as_of": "2026-09-30", "n": 900},
        {"asset": "btc", "peer": "qqq", "absent_reason": "no 60-day correlation"}]
    co.config = lambda: {"named": [{"key": "corr.x", "a": ["copper", "gold"],
                                    "b": "y10", "label": "Copper/gold against "
                                                         "the 10-year, 60 days"}]}
    co.triple = lambda st, key, now: {"latest": 0.2, "mean": 0.1,
                                      "percentile": 70.0, "as_of": "2026-09-30"}
    co.label = lambda aid, cfg=None: aid.upper()
    return tr, co


def group_d(ed: dict) -> None:
    from altdata import observations
    from daily_cascade import stack as stack_mod
    from monthly_macro import quarterly as q
    print(f"\n{LINE}\nD. THE NAMED HOOKS: AQ-6 AND AQ-5\n{LINE}")
    cfg = stack_mod.config()
    met = q.chapters(ed)[0]
    by = {x.get("item"): x for x in met["subsections"]}
    present = {k: q._module(k) is not None for k in q.HOOK_MODULES}
    for kind, items in (("thesis", ("graded", "theses")), ("correlation",
                                                           ("correlation",))):
        if present[kind]:
            check(all(q.NOT_YET[kind] not in str(by[i].get("not_tracked"))
                      for i in items),
                  f"{kind}: its module is on this build, so its items are filled")
        else:
            check(all(by[i]["not_tracked"] == [q.NOT_YET[kind]] for i in items),
                  f"{kind}: its module is absent on this build, and its items say "
                  f"\"{q.NOT_YET[kind]}\"")
    saved = dict(q.HOOK_MODULES)
    try:
        q.HOOK_MODULES.update({"thesis": "altdata.no_such_thesis_module",
                               "correlation": "altdata.no_such_correlation"})
        ch = q.build_chapter(cfg["quarterly_chapters"][0], cfg,
                             {"quarter": "2026q3", "now": AS_OF, "db_path": vms.DB,
                              "store": None})
        by2 = {x.get("item"): x for x in ch["subsections"]}
        check(by2["graded"]["not_tracked"] == [q.NOT_YET["thesis"]]
              and by2["theses"]["not_tracked"] == [q.NOT_YET["thesis"]]
              and by2["correlation"]["not_tracked"] == [q.NOT_YET["correlation"]],
              "with both modules absent, the hooks degrade cleanly to \"not yet\"")
        tr, co = fake_modules()
        sys.modules["fake_thesis_register"] = tr
        sys.modules["fake_correlation"] = co
        q.HOOK_MODULES.update({"thesis": "fake_thesis_register",
                               "correlation": "fake_correlation"})
        with observations.ObservationStore(vms.DB) as st:
            ch = q.build_chapter(cfg["quarterly_chapters"][0], cfg,
                                 {"quarter": "2026q3", "now": AS_OF,
                                  "db_path": vms.DB, "store": st})
        by3 = {x.get("item"): x for x in ch["subsections"]}
        check(by3["graded"]["table"]["rows"][0][4] == "hit"
              and by3["graded"]["tier"] == "lead",
              "present, AQ-6's graded table opens the chapter (item 1, lead)")
        check(len(by3["theses"]["table"]["rows"]) == 1
              and by3["theses"]["table"]["rows"][0][0] == "metals",
              "the seed view carries this chapter's family only (item 2)")
        rows = by3["correlation"]["table"]["rows"]
        check(len(rows) == 2 and rows[0][0].startswith("GOLD-DXY")
              and any("Copper/gold" in r[0] for r in rows)
              and by3["correlation"]["tier"] == "reference",
              "AQ-5's peer pair and named row print for the chapter's assets "
              "(item 8, reference)")
        tr_f, _ = fake_modules(fault=True)
        sys.modules["fake_thesis_register"] = tr_f
        ch = q.build_chapter(cfg["quarterly_chapters"][0], cfg,
                             {"quarter": "2026q3", "now": AS_OF, "db_path": vms.DB,
                              "store": None})
        by4 = {x.get("item"): x for x in ch["subsections"]}
        check("FAULT (code, not data)" in str(by4["graded"].get("notes")),
              "a hook whose module faults prints the fault and never raises")
    finally:
        q.HOOK_MODULES.clear()
        q.HOOK_MODULES.update(saved)
        sys.modules.pop("fake_thesis_register", None)
        sys.modules.pop("fake_correlation", None)


def run_main(argv: list[str], emitted: list) -> int:
    from monthly_macro import run
    saved_emit, saved_argv = run.emit, sys.argv
    run.emit = lambda **k: emitted.append(k)
    sys.argv = ["monthly_macro.run"] + argv
    try:
        buf = io.StringIO()
        with redirect_stdout(buf):
            return pinned(run.main)
    finally:
        run.emit, sys.argv = saved_emit, saved_argv


def group_e() -> None:
    from state import emit as emit_mod
    from monthly_macro import quarterly as q
    print(f"\n{LINE}\nE. THE STATE KEY\n{LINE}")
    check(q.STATE_KEY == "alt_asset" and "alt_asset" in emit_mod.VALID_KEYS,
          "the Quarterly records under alt_asset, the key state/emit.py reserves")
    out = Path(vms.TD) / "run_out"
    emitted: list = []
    rc = run_main(["--cadence", "quarterly", "--dry-run", "--skip-narrative",
                   "--out-dir", str(out), "--as-of", AS_OF], emitted)
    dry = sorted(x.name for x in (out / "dryrun").glob("alt_asset_*"))
    check(rc == 0 and not emitted and dry and not list(out.glob("alt_asset_*")),
          f"--cadence quarterly --dry-run builds end to end, writes only to "
          f"dryrun/ ({len(dry)} files) and records nothing")
    emitted = []
    rc = run_main(["--cadence", "quarterly", "--no-deliver", "--skip-narrative",
                   "--out-dir", str(out), "--as-of", AS_OF], emitted)
    check(rc == 0 and len(emitted) == 1 and emitted[0]["report_key"] == "alt_asset"
          and emitted[0]["detail"]["chapters"] == 11,
          "a live run records one state under alt_asset, with its chapter count")


def group_f() -> None:
    print(f"\n{LINE}\nF. THE UNIT AND THE TIMER\n{LINE}")
    units = REPO / "deploy" / "systemd"
    t = (units / "chester-quarterly.timer").read_text(encoding="utf-8")
    s = (units / "chester-quarterly.service").read_text(encoding="utf-8")
    w = (REPO / "scripts" / "run_quarterly.sh").read_text(encoding="utf-8")
    check("OnCalendar=Sat *-01,04,07,10-08..14 06:00 America/New_York" in t
          and "Persistent=true" in t,
          "the timer fires the second Saturday after quarter-end at 06:00 ET (first "
          "fire Sat 9 Jan 2027)")
    check("ExecStart=%h/chester-reports/scripts/run_quarterly.sh" in s
          and "--cadence quarterly" in w and "quarterly_heartbeat" in w,
          "the unit runs the wrapper, which runs the one runner at the quarterly "
          "cadence with its own status and heartbeat")
    dep = (REPO / "scripts" / "deploy_remote.sh").read_text(encoding="utf-8")
    block = re.search(r'DEPLOY_TIMERS="(.*?)"', dep, re.S)
    check(block and "chester-quarterly.timer" not in block.group(1)
          and "systemctl --user enable --now chester-quarterly.timer" in t,
          "shipped disabled: not in DEPLOY_TIMERS; the enable command is printed "
          "for the operator")
    mk = (REPO / "Makefile").read_text(encoding="utf-8")
    check("tools/validate_quarterly_stack.py" in mk, "this gate is in the "
                                                     "Makefile's list")


def main() -> int:
    vms.seed(vms.DB, dealer_sessions=21)
    from daily_cascade import stack as stack_mod
    print(f"{LINE}\nAQ-1 -- the quarterly cadence (synthetic 3Q26)\n{LINE}")
    cfg = stack_mod.config()
    group_a(cfg)
    group_b()
    p = build_payload()
    r = group_c(p)
    group_d(r["ed"])
    group_e()
    group_f()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed, {WARN} warned\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
