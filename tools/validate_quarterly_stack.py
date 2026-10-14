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
  G CHAPTERS   (AQ-2 parts 1 and 2) all eleven chapters filled item by item:
               every item renders or prints its not-yet reason; every series is
               registered or absent with its reason; the measurables name
               registered keys; the tests and the ten questions are the papers'
               verbatim, and "no owning paper -- not stated" where none owns
               the chapter; each item's figure budget holds at the frame; the
               tests computed by code; the template per weight; the hooks to
               other branches named and degrading; China's quote-only political
               sub-section; crypto's coin pages in one fixed shape; Thailand's
               isolation; the transmission map; the eleven chapters end to end
               with the executive summary.

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
    check([t["n"] for t in tpl if t["tier"] == "lead"] == ["1", "2", "3"],
          "the lead page: last quarter's theses graded, the new theses, the "
          "quarter (AQ-2: the falsification tests are reference)")
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
    # Since AQ-2 part 2 every chapter is filled; the shell is still the
    # fallback for a chapter config/quarterly_chapters.yaml does not fill, so it
    # is built here from a configuration that fills nothing.
    scfg = stack_mod.config()
    shell = q.build_chapter(scfg["quarterly_chapters"][-1], scfg,
                            {"quarter": "2026q3", "now": AS_OF, "db_path": vms.DB,
                             "store": None, "qcfg": {"families": {}}})
    plain = [x for x in shell["subsections"] if not x.get("divider")
             and not x.get("hook")]
    check(plain and all(x["not_tracked"] == [q.NOT_BUILT] for x in plain),
          f"a chapter the config does not fill stays on the shell: every item "
          f"prints \"{q.NOT_BUILT}\" in the not-yet-tracked form ({len(plain)} in "
          f"{shell['title']})")
    check("Not yet tracked: " in out["markdown"]
          and "Not yet tracked: " in out["html_email"]
          and q.REFERENCE_DIVIDER in out["markdown"],
          "and the renderer prints the not-yet-tracked form, and the divider, on "
          "the page and in the Markdown")
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
    import math as _m
    from daily_cascade import readability as _rd
    check(ed["read_minutes"] == max(1, _m.ceil(words / 250 + q.lead_charts(ed)
                                                * _rd.SECONDS_PER_CHART / 60.0))
          and ed["reading_minutes"] >= ed["read_minutes"],
          f"the read's time is the summary and the lead items' prose at 250 words "
          f"a minute and 20 seconds a drawn lead chart ({ed['read_minutes']} min; the whole edition "
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
                                 q.chapter_context(ed, cfg, vms.DB, st))
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


FAM_SERIES = {
    # key: (start level, daily drift, wobble)
    "yfinance.mkt_gold_front": (2000.0, 0.0011, 0.004),
    "fred.tips_10y": (1.9, 0.0, 0.03),
    "fred.dxy": (120.0, -0.0001, 0.002),
    "yfinance.mkt_slv": (22.0, 0.0010, 0.006),
    "yfinance.mkt_copper_front": (3.9, 0.0004, 0.006),
    "fred.brent": (80.0, -0.0002, 0.01),
    "fred.wti": (76.0, -0.0002, 0.01),
    "oil.prompt_spread": (0.4, 0.0, 0.05),
    "fred.natgas": (2.6, 0.0003, 0.02),
    "fred.breakeven_10y": (2.3, 0.0, 0.01),
    "yfinance.mkt_dxy": (103.0, -0.0001, 0.002),
    "yfinance.mkt_eurusd": (1.09, 0.0001, 0.003),
    "yfinance.mkt_usdjpy": (148.0, 0.0, 0.004),
    "yfinance.mkt_usdcny": (7.2, 0.0, 0.001),
    "fred.yield_2y": (4.3, -0.0005, 0.02),
    "fred.yield_10y": (4.2, 0.0, 0.02),
    "mof.jgb_10y": (0.8, 0.0008, 0.01),
    "cfets.cny_fix": (7.1, 0.0, 0.001),
    # AQ-2 part 2: the other eight chapters' daily series. Where the Monthly
    # gate's fixture seeds a key on its month-ends and the year-start (SPY, XLRE,
    # XLU, IWM, HY OAS, the GTM-14 proxies), these fill the days around them at
    # levels that meet them (PART2_SKIP); QQQ, EEM and net liquidity stay as it
    # seeds them, sparse, and their rows degrade by name.
    "yfinance.mkt_spy": (88.0, 0.0002, 0.006),
    "fred.hy_oas": (3.1, 0.0, 0.02),
    "yfinance.mkt_emxc": (52.0, 0.0002, 0.006),
    "yfinance.mkt_efa": (74.0, 0.0002, 0.005),
    "fred.usd_mxn": (17.2, 0.0001, 0.004),
    "cfets.cgb_10y": (2.5, -0.0003, 0.01),
    "yfinance.mkt_btc_usd": (42000.0, 0.0012, 0.05),
    "zec.price_usd": (25.0, 0.0015, 0.06),
    "crypto.total_market_cap_usd": (1.6e12, 0.0011, 0.04),
    "zec.btc_ratio": (0.0006, 0.0003, 0.03),
    "yfinance.mkt_xlre": (93.0, 0.0001, 0.006),
    "yfinance.mkt_xlu": (88.0, 0.0002, 0.005),
    "yfinance.mkt_iwm": (88.0, 0.0002, 0.008),
    "fred.mortgage_30y": (6.8, -0.0001, 0.01),
    "fred.ccc_oas": (9.0, -0.0002, 0.02),
    "fred.bb_oas": (2.2, -0.0001, 0.02),
    "fred.ig_oas": (1.0, -0.0001, 0.02),
    "yfinance.mkt_hyg": (77.0, 0.0001, 0.003),
    "yfinance.mkt_lqd": (108.0, 0.0, 0.003),
    "yfinance.mkt_acwx": (52.0, 0.0002, 0.005),
    "yfinance.mkt_vwo": (41.0, 0.0002, 0.006),
}
PART1_KEYS = ("yfinance.mkt_gold_front", "fred.tips_10y", "fred.dxy",
              "yfinance.mkt_slv", "yfinance.mkt_copper_front", "fred.brent",
              "fred.wti", "oil.prompt_spread", "fred.natgas", "fred.breakeven_10y",
              "yfinance.mkt_dxy", "yfinance.mkt_eurusd", "yfinance.mkt_usdjpy",
              "yfinance.mkt_usdcny", "fred.yield_2y", "fred.yield_10y",
              "mof.jgb_10y", "cfets.cny_fix")
# The Monthly fixture's own dates, left to it for part 2's keys.
PART2_SKIP = {vms.M_START, vms.M_END, "2025-12-31"}
# Monthly series for part 2: (start level, monthly step). SAFE's gold at market
# value against its total reserves gives a gold share near 6% (the "<10%" of the
# change order's China sub-chapter).
FAM_MONTHLY = {
    "safe.official_reserves_total": (3.30e12, 2.0e9),
    "safe.fx_reserves": (3.20e12, 1.5e9),
    "safe.gold_reserves_usd": (1.60e11, 1.6e9),
    "safe.gold_reserves_oz": (7.20e7, 1.0e5),
    "worldbank.cmo_nonenergy": (110.0, 0.2),
    "worldbank.cmo_energy": (120.0, -0.3),
}
OPERATOR_NOTE = ("The Fourth Plenum's personnel list is the quarter's signal; the "
                 "property measures are announced, not yet funded.")


def seed_aq2(db: str) -> None:
    """Two and a half years of the three chapters' series, a weekly crude-stock
    series, the monthly official-gold and policy series, and two voices on gold
    -- one each way -- so every filled item has something to read. The values
    are synthetic; the Fed-fighting test is built to fail (the funds rate falls
    through the quarter with CPI above 3%) and the official floor to hold."""
    import math as _m
    from altdata import observations, voices as vmod
    obs = []
    start = dt.date(2024, 1, 1)
    days = [start + dt.timedelta(days=i) for i in range((dt.date(2026, 10, 9)
                                                         - start).days + 1)]
    wk = [d for d in days if d.weekday() < 5]
    for key, (lv, drift, wob) in FAM_SERIES.items():
        for i, d in enumerate(wk):
            if key not in PART1_KEYS and d.isoformat() in PART2_SKIP:
                continue
            v = lv * (1 + drift) ** i * (1 + wob * _m.sin(i * 0.7 + len(key)))
            obs.append({"registry_key": key, "instrument": None,
                        "observed_at": d.isoformat(),
                        "available_at": f"{d.isoformat()}T20:00:00+00:00",
                        "value": round(v, 6), "source": "synthetic"})
    for i, d in enumerate([x for x in days if x.weekday() == 4]):
        obs.append({"registry_key": "eia.crude_stocks", "instrument": None,
                    "observed_at": d.isoformat(),
                    "available_at": f"{d.isoformat()}T20:00:00+00:00",
                    "value": 430000 - 300 * i, "source": "synthetic"})
    months = sorted({d.replace(day=1) for d in days})
    for i, m in enumerate(months):
        av = f"{m.isoformat()}T20:00:00+00:00"
        late = m >= dt.date(2026, 7, 1)
        for key, v in (("wgc.cb_gold_holdings_t", 36000 + 80 * i),
                       ("wgc.cb_net_purchases_t", 80.0),
                       ("fred.fed_funds", 5.33 - (0.25 * (m.month - 6) if late else 0)),
                       ("calc.yoy_cpi", 3.2)):
            obs.append({"registry_key": key, "instrument": None,
                        "observed_at": m.isoformat(), "available_at": av,
                        "value": v, "source": "synthetic"})
    for i, m in enumerate(months):
        av = f"{m.isoformat()}T20:00:00+00:00"
        for key, (lv, step) in FAM_MONTHLY.items():
            obs.append({"registry_key": key, "instrument": None,
                        "observed_at": m.isoformat(), "available_at": av,
                        "value": lv + step * i, "source": "synthetic"})
        obs.append({"registry_key": "tic.holdings_by_country",
                    "instrument": "China, Mainland", "observed_at": m.isoformat(),
                    "available_at": av, "value": 7.7e11 - 1.0e9 * i,
                    "source": "synthetic"})
    with observations.ObservationStore(db) as st:
        st.write_many(obs)
    with vmod.VoicesStore(db) as vs:
        # China's politics: the operator's note (an operator voices row) and one
        # authoritative release, both quoted -- never characterised.
        vs.write({"voice": "The operator", "affiliation": "Chester (operator)",
                  "kind": "independent", "outlet": "Operator's political note",
                  "source_url": "https://example.org/operator/china-note-3q26",
                  "title": "China political note, 3Q26", "tier": 1,
                  "published_at": "2026-09-20",
                  "retrieved_at": "2026-09-20T12:00:00+00:00",
                  "view": OPERATOR_NOTE, "directions": [], "origin": "operator",
                  "source_id": "operator.china_political_note"})
        vs.write({"voice": "People's Bank of China", "affiliation": "PBOC",
                  "kind": "official", "outlet": "People's Bank of China",
                  "source_url": "https://example.org/pboc/rrr-2026-09",
                  "title": "RRR announcement", "tier": 1,
                  "published_at": "2026-09-15",
                  "retrieved_at": "2026-09-15T12:00:00+00:00",
                  "view": "The PBOC announced a cut in the reserve requirement ratio.",
                  "directions": [], "source_id": "china.pboc"})
        for i, (name, d) in enumerate((("Fixture Desk A", "bullish"),
                                       ("Fixture Desk B", "bullish"),
                                       ("Fixture Strategist C", "bearish"))):
            vs.write({"voice": name, "affiliation": f"Fixture House {i}",
                      "kind": "sell_side", "outlet": "Fixture Wire",
                      "source_url": f"https://example.org/fixture/gold/{i}",
                      "title": f"Gold view {i}", "tier": 2,
                      "published_at": f"2026-08-{10 + i:02d}",
                      "retrieved_at": f"2026-08-{10 + i:02d}T12:00:00+00:00",
                      "view": f"Gold to {2500 + 100 * i} by year end on the official bid.",
                      "directions": [{"subject": "gold", "direction": d}]})


def _leaves(m):
    if not m:
        return []
    if "all" in m or "any" in m:
        return [x for y in (m.get("all") or m.get("any")) for x in _leaves(y)]
    (kind, p), = m.items()
    return [(kind, p)]


def stack_cfg() -> dict:
    from daily_cascade import stack as stack_mod
    return stack_mod.config()


def group_g(r: dict) -> None:
    import json as _json
    from altdata import derived
    from daily_cascade import readability as rd
    from monthly_macro import prose as prose_mod, quarterly as q
    from monthly_macro import quarterly_items as qi
    print(f"\n{LINE}\nG. AQ-2 -- THE ELEVEN CHAPTERS\n{LINE}")
    qc = qi.load_config()
    fams = {k: v for k, v in (qc.get("families") or {}).items() if v.get("filled")}
    all_ids = [c_["id"] for c_ in stack_cfg()["quarterly_chapters"]]
    check(sorted(fams) == sorted(all_ids),
          f"all eleven chapters are filled: part 1's three and part 2's eight "
          f"({len(fams)})")
    reg = derived.registry_entry
    keys, bad = [], []
    for fid, f in fams.items():
        rows_ = ((f.get("five_lines") or []) + (f.get("structure") or [])
                 + ((f.get("second_half") or {}).get("structure") or []))
        for p_ in f.get("panels") or []:
            if p_["kind"] == "series":
                rows_ += p_.get("rows") or []
            keys += [x["key"] for x in p_.get("proxies") or []]
            for coin in p_.get("coins") or []:
                for fld in (coin.get("fields") or {}).values():
                    keys += list(fld.get("keys") or [])
        for s_ in rows_:
            got = qi.spec_keys(s_)
            if got:
                keys += got
            elif not (s_.get("absent") or (s_.get("hook_key") and s_.get("branch"))):
                bad.append(f"{fid}: {s_.get('label')} has neither a key nor absent")
        for c in f.get("structure_charts") or []:
            keys += [x["key"] for x in c["series"] if x.get("key")]
            bad += [f"{fid}: chart leg {x.get('label')}" for x in c["series"]
                    if not x.get("key") and not x.get("absent")
                    and not (x.get("hook_key") and x.get("branch"))]
        for qn in f.get("ten_questions") or []:
            keys += list(qn.get("series") or [])
        for a in f.get("analyses") or []:
            keys += list(a.get("series") or [])
            if not a.get("module"):
                keys += qi.spec_keys(a)
        for p_ in (f.get("pairs") or {}).get("deep") or []:
            if p_.get("key"):
                keys.append(p_["key"])
    unreg = sorted({k for k in keys if not reg(k)})
    check(not unreg and not bad, f"every series the chapters read is a registered "
                                 f"key, or listed absent with its reason ({len(set(keys))} "
                                 f"keys; unregistered {unreg[:3]}; {bad[:2]})")
    leaves, lbad = 0, []
    for fid, f in fams.items():
        for t in f.get("falsification") or []:
            if t.get("measurable") is None and not t.get("not_measured"):
                lbad.append(f"{t['id']}: null with no reason")
            for kind, p_ in _leaves(t.get("measurable")):
                leaves += 1
                for k in ("series", "a", "b"):
                    if k in p_ and not reg(p_[k]):
                        lbad.append(f"{t['id']}: {p_[k]}")
    check(leaves >= 6 and not lbad,
          f"the falsification measurables reference real registry keys ({leaves} "
          f"rules; a null measurable names its reason) {lbad[:3]}")
    counts = {fid: len(f["falsification"]) for fid, f in fams.items()
              if f.get("paper_file")}
    check(counts == {"metals": 7, "oil_energy": 7, "currency": 6, "crypto": 7,
                     "credit": 7, "intl_equities": 4},
          f"the papers' own tests: Metals 7, Energy 7, Currencies 6, Digital Assets "
          f"7, Credit 7, International Equities 4 (15.7) ({counts})")
    nopaper = sorted(fid for fid, f in fams.items() if not f.get("paper_file"))
    check(nopaper == ["agriculture", "china", "em", "real_estate", "thailand"]
          and all(fams[x]["falsification"] == [] and not fams[x].get("paper")
                  and fams[x]["falsification_note"].startswith(qi.NO_PAPER)
                  and fams[x]["ten_questions"] == []
                  and fams[x]["questions_note"].startswith(qi.NO_PAPER)
                  for x in nopaper),
          f"where no paper owns the chapter ({', '.join(nopaper)}) the tests and the "
          f"questions say \"{qi.NO_PAPER}\": none is invented")

    def norm(t: str) -> str:
        # Bold and italic markers out (International Equities 15.7 italicises
        # each scenario's name); the words themselves are compared verbatim.
        return " ".join(t.replace("\\$", "$").replace("**", "").replace("*", "")
                        .split())
    miss = []
    for fid, f in fams.items():
        paper = (norm((REPO / f["paper_file"]).read_text(encoding="utf-8"))
                 if f.get("paper_file") else "")
        for t in f["falsification"]:
            if norm(t["statement"]) not in paper:
                miss.append(t["id"])
        for qn in f["ten_questions"]:
            if f"{qn['n']}. {norm(qn['text'])}" not in paper:
                miss.append(f"{fid} Q{qn['n']}")
        for t in f.get("related_tests") or []:
            src = next(x for x in fams.values() if x.get("paper") == t["paper"])
            if norm(t["statement"]) not in norm(
                    (REPO / src["paper_file"]).read_text(encoding="utf-8")):
                miss.append(f"{fid} related")
    with_q = sorted(fid for fid, f in fams.items() if f["ten_questions"])
    check(not miss and with_q == ["credit", "crypto", "currency", "metals",
                                  "oil_energy"]
          and all(len(fams[x]["ten_questions"]) == 10 for x in with_q)
          and "no ten questions" in fams["intl_equities"]["questions_note"],
          f"every test's statement, every related test and every one of the ten "
          f"questions is the paper's own wording, verbatim; the five papers with an "
          f"Appendix D carry ten, International Equities says it has none ({miss[:4]})")
    from daily_cascade import cadence
    cap = cadence.figure_cap(cadence.get("quarterly"))
    check(all(0 <= int(v) <= cap for f in fams.values()
              for v in (f.get("figure_budget") or {}).values())
          and all({"quarter", "supply", "questions", "summary"}
                  <= set(f.get("figure_budget") or {}) for f in fams.values()),
          f"each of the eleven declares a figure budget per written item, none above "
          f"the cadence's cap ({cap})")

    ed, out = r["ed"], r["out"]
    chs = {c["id"]: c for c in q.chapters(ed)}
    filled = [chs[f] for f in all_ids]
    check(all(c["data"].get("filled") for c in filled),
          "the dry run renders all eleven chapters filled, item by item")
    empty = []
    for c in filled:
        for ss in c["subsections"]:
            if ss.get("divider"):
                continue
            if not (ss.get("table") or ss.get("lines") or ss.get("not_tracked")
                    or ss.get("notes") or ss.get("charts_rendered")
                    or ss.get("paragraphs")):
                empty.append(f"{c['id']}:{ss.get('item')}")
    check(not empty, f"every item renders, or prints its not-yet reason -- never a "
                     f"blank ({empty[:4]})")
    lead_items = [[ss.get("item") for ss in c["subsections"] if ss.get("tier") == "lead"]
                  for c in filled]
    check(all(x == ["lead_lines", "graded", "theses", "quarter"] for x in lead_items)
          and all(len([ss for ss in c["subsections"] if ss.get("item") == "quarter"]
                      [0]["charts_rendered"]) == 3 for c in filled),
          f"the lead page: the confidence and what-changed lines, items 1, 2 and 3 "
          f"(the five lines and its three charts); everything else reference "
          f"({lead_items[0]})")
    met = {ss.get("item"): ss for ss in chs["metals"]["subsections"]}
    cur = {ss.get("item"): ss for ss in chs["currency"]["subsections"]}
    oil = {ss.get("item"): ss for ss in chs["oil_energy"]["subsections"]}
    conf, changed = met["lead_lines"]["lines"]
    check(conf.startswith("Weakest link: ") and "Brier to date:" in conf
          and "Standing dissent: Fixture Strategist C" in conf and "bearish" in conf
          and changed.startswith("What changed: the first Quarterly"),
          f"the confidence line: the weakest link, the Brier to date, the standing "
          f"dissent named from the stored voices; the what-changed line "
          f"({conf[:90]}...)")
    check(len(met["quarter"]["lines"]) == 5
          and all("on the quarter" in x for x in met["quarter"]["lines"])
          and len(met["quarter"]["charts_rendered"]) == 3,
          f"item 3: five lines over the quarter window, and three lead charts "
          f"({met['quarter']['lines'][0]})")
    drawn_ = [k for k in met["quarter"]["charts_rendered"]
              if not out["charts"][k].get("unavailable")]
    lf = out["charts"][met["quarter"]["charts_rendered"][0]]
    # Where AQ-4's horizon charts are on the branch the long frame is drawn too
    # (Friday stitching, 13 Oct); else it says it waits for AQ-4.
    from monthly_macro import quarterly_items as qi_            # noqa: PLC0415
    check(len(drawn_) == 3 if qi_.module("horizon") is not None
          else len(drawn_) == 2 and "AQ-4" in str(lf.get("unavailable")),
          "the two structure charts are drawn; the long frame too where AQ-4 is on "
          "the branch, else it says it waits for AQ-4")
    st_rows = met["structure"]["table"]["rows"]
    check(st_rows and all(r_[4] == "until the lenses" for r_ in st_rows)
          and all(re.search(r"\d+(st|nd|rd|th) \(n=", r_[3]) for r_ in st_rows
                  if not r_[3].startswith("—"))
          and any("absent" not in x and "not stored" in x
                  for x in met["structure"]["not_tracked"]),
          f"item 4: the structure table with dual percentiles, the five-year column "
          f"\"until the lenses\"; absent series print by name as not tracked "
          f"({len(st_rows)} rows)")
    fz = {row[0][:40]: row[1] for row in met["falsify"]["table"]["rows"]}
    fc = {row[0][:40]: row[1] for row in cur["falsify"]["table"]["rows"]}
    check(any(v == "holds" for v in fz.values())
          and any(v == "failed" for v in fc.values())
          and all(v in ("holds", "strained", "failed") or v.startswith("not measured — ")
                  for v in list(fz.values()) + list(fc.values())),
          f"item 7: holds / strained / failed computed by code where a measurable "
          f"exists, \"not measured — <reason>\" where it does not (metals "
          f"{sorted(set(fz.values()))[:3]}; currency has a failed test)")
    fed = next(row for row in cur["falsify"]["table"]["rows"]
               if row[0].startswith('"The Fed is fighting'))
    check(fed[1] == "failed" and "fred.fed_funds" in fed[2]
          and "calc.yoy_cpi" in fed[2],
          f"the Fed-fighting test fails on the seeded easing with CPI above 3% "
          f"({fed[2][:80]})")
    check(oil.get("second_half") and "gas, power and uranium" in
          oil["second_half"]["title"] and oil["second_half"].get("table")
          and len(oil["second_half"]["lines"]) == 5,
          "oil and energy's second half -- gas, power, uranium -- is a sub-chapter "
          "with its structure and its five tests")
    pairs = cur.get("pairs") or {}
    check(pairs and len(pairs["table"]["rows"]) == 3
          and len(pairs["tables"][0]["rows"]) == 15
          and any("USD/CNH" in x for x in pairs["not_tracked"]),
          "currency names its pair universe: the deep basket (three stored, six by "
          "name) and the scan tier (fifteen; H.10's legs wait for aq-3-series-1)")
    an = met["analyses"]["table"]["rows"]
    # A hook whose branch is on this one reads its store instead of naming the
    # branch it waits for (Friday stitching, 13 Oct).
    check(all(len(x) == 3 and x[2] for x in an)
          and (qi_.module("attribution") is not None or any("AQ-8a" in x[1] for x in an))
          and (qi_.module("correlation") is not None or any("AQ-5" in x[1] for x in an)),
          "item 6: each analysis's state and its kill condition; the hooks name the "
          "branch they wait for")
    pr = met["priced"]
    check(any("6b" in x for x in pr["not_tracked"])
          and any("GLD" in x for x in pr["not_tracked"])
          and any("AQ-7" in x for x in pr["not_tracked"]),
          "item 3a: the curve waits for 6b, the implied range says no chain was "
          "logged, the consensus waits for AQ-7")
    sup = met["supply"]
    sup_plan = [x for x in prose_mod.block_plan(ed)
                if x["key"] == "block:quarterly:metals:supply"]
    cite = (sup.get("data") or {}).get("figures_you_may_cite") or []
    views = " ".join(v["view"] for v in (sup.get("data") or {}).get("voices") or [])
    budget = fams["metals"]["figure_budget"]
    check(sup.get("prose") and sup_plan and len(cite) <= budget["supply"]
          and not re.search(r"\d", views)
          and re.search(rf"cite at most\s+{cadence.figure_word(budget['supply'])}"
                        rf"\s+figures", sup_plan[0]["system"], re.I),
          f"item 5: a written read only where stored voices exist; its frame offers "
          f"{len(cite)} figures against a budget of {budget['supply']}, the voices' "
          f"views with their numbers masked")
    check("no stored source, not printed" in " ".join(oil["supply"]["lines"]),
          "with no stored voice on the family, item 5 prints \"no stored source, "
          "not printed\"")
    qs = met["questions"]["lines"]
    check(len(qs) == 10 and qs[1].endswith("Not answered: no stored source.")
          and not qs[0].endswith("no stored source.") and qs[0].startswith("1. "),
          "item 11: ten lines; an answerable question gets one audited line, the "
          "rest \"Not answered: no stored source\"")
    over = []
    for fid, f in fams.items():
        c = chs[fid]
        for ss in c["subsections"]:
            if ss.get("item") == "quarter":
                n = sum(rd.figure_count(str(m.get("change_display") or ""))
                        for m in (ss.get("data") or {}).get("moves") or [])
                if n > 5:
                    over.append(f"{fid} quarter {n}")
    qframes = [x for x in out["written"] if x.startswith("q11:")]
    check(not over and qframes,
          f"the figure budget per item: the five lines carry at most five moves; "
          f"each question's frame at most its budget ({len(qframes)} question "
          f"calls)")
    check("Q0" in out["charts"] and not out["charts"]["Q0"].get("unavailable")
          and "Q0" in next(s_ for s_ in ed["sections"] if s_["id"] == "read")
          .get("charts_rendered", [])
          and ed["chart_count"] >= 7 and ed["chart_count"] <= ed["budget"]["charts"]
          and "transmission map" in out["html_email"].lower(),
          f"the transmission map opens the front matter, drawn and counted in the "
          f"cap ({ed['chart_count']} charts against {ed['budget']['charts']})")
    check(len(ed["summary"]) == 11 and all(e.get("text") for e in ed["summary"])
          and "Metals" in out["markdown"] and "Standing dissent" in out["markdown"],
          "the synthetic-store dry run renders the eleven chapters end to end "
          "with the executive summary")
    group_g2(r, fams, chs)



# The configs that can move a decision: a key or a name in any of them is
# reachable from a trigger. Thailand must appear in none but as pillar 11's
# relocation record (dial null, weight 0, no metrics).
TRIGGER_CONFIGS = ("market_state.yaml", "setups.yaml", "risk_limits.yaml",
                   "claims.yaml", "narratives.yaml", "monthly_themes.yaml",
                   "naive_expectations.yaml", "tracked_entities.yaml",
                   "story_queries.yaml")
THAI_TOKENS = ("thailand", "thb", "dexthus", "thailand_political_calendar")
PRIVATE_COLUMNS = ("convert", "stage", "defer", "budget", "payment", "remaining",
                   "tranche")


def group_g2(r: dict, fams: dict, chs: dict) -> None:
    """AQ-2 part 2: the other eight chapters, item by item."""
    import json as _json
    import yaml as _yaml
    from altdata import derived, observations
    from monthly_macro import quarterly as q
    from monthly_macro import quarterly_items as qi
    print(f"\n{LINE}\nG (part 2). EM, CHINA, CRYPTO, REAL ESTATE, CREDIT, INTERNATIONAL "
          f"EQUITIES, THAILAND, AGRICULTURE\n{LINE}")
    ed, out = r["ed"], r["out"]
    by = {cid: {ss.get("item"): ss for ss in c["subsections"]} for cid, c in chs.items()}
    weights = {c_["id"]: c_.get("weight") for c_ in stack_cfg()["quarterly_chapters"]}

    # -- the template per weight -------------------------------------------
    bad = []
    for cid, items in by.items():
        w = weights[cid]
        if w == "light" and set(items) & {"supply", "analyses", "stories", "questions"}:
            bad.append(f"{cid} carries a deep item")
        if w == "deep" and not {"priced", "structure", "supply", "analyses", "falsify",
                                "stories", "book", "questions"} <= set(items):
            bad.append(f"{cid} lacks a deep item")
        if w == "country" and ("questions" in items or not {"supply", "analyses",
                                                             "stories"} <= set(items)):
            bad.append(f"{cid} is not the country template")
    check(not bad, f"each chapter carries its weight's items: light 1-4, 7, 8, 10; "
                   f"Thailand all but 11; deep all ({bad[:3]})")

    # -- EM: the frame reads a paper not yet filed ---------------------------
    em = by["em"]
    fl = em["frame"]["lines"]
    check(fl[0] == "frame: Emerging Markets — A Structural Framework, Draft 1, not yet "
                   "filed" and "dollar-cycle instrument with a commodity overlay" in fl[1]
          and "(II S15)" in fl[1] and "International Equities, Chapters 10 and 12" in fl[2],
          "EM's frame item prints the EM paper as not yet filed and carries section "
          "4.5's frame paragraph as the interim, with its paper citations")
    check(any("The EM twelve-month set" in x and "not yet — the EM paper" in x
              for x in em["scenarios"]["lines"]),
          "EM's twelve-month scenario set is the paper's: \"not yet\", none written here")
    sc = [row for row in by["china"]["scenarios"]["table"]["rows"]]
    check([x[2] for x in sc] == ["~20%", "~40%", "~25%", "~15%"]
          and sc[0][1] == "Reform and discipline" and sc[3][1] == "Rupture",
          "China's ten-year set is International Equities 10.7's, rewritten here: "
          "20 / 40 / 25 / 15")
    nop = [cid for cid in ("em", "china", "real_estate", "thailand", "agriculture")
           if not any(x.startswith(f"Falsification tests: {qi.NO_PAPER}")
                      for x in by[cid]["falsify"]["lines"])]
    nopq = [cid for cid in ("em", "china")
            if not by[cid]["questions"]["lines"][0].startswith(
                f"The ten questions: {qi.NO_PAPER}")]
    check(not nop and not nopq and not by["em"]["falsify"].get("table"),
          f"where no paper owns the chapter, item 7 (and a deep chapter's item 11) "
          f"prints \"{qi.NO_PAPER}\" and no test ({nop + nopq})")
    rel = by["real_estate"]["falsify"]["lines"]
    check(any(x.startswith("Credit, §21") and "rising foreclosure share" in x
              for x in rel),
          "real estate reads the Credit paper's own words beside it, marked as "
          "another paper's and not graded")

    # -- the hooks named by branch ------------------------------------------
    def present(mod: str) -> bool:
        return qi.branch_module({"module": mod}) is not None
    nt = lambda ss: " ".join(ss.get("not_tracked") or [])          # noqa: E731
    checks_ = [
        ("aq-9a-em-scorecard", "altdata.em_scorecard", nt(em["em_scorecard"])),
        ("c1-move-screen", "altdata.move_screen", nt(em["em_episodes"])),
        ("imf-ifs-gold", None, nt(by["china"]["structure"])),
        ("aq-5-correlation-layer", "altdata.correlation",
         " ".join(row[1] for row in em["analyses"]["table"]["rows"])),
    ]
    miss = [b for b, mod, text in checks_
            if (mod is None or not present(mod)) and f"not yet: {b}" not in text]
    check(not miss, f"the hooks to other branches are named and degrade to \"not yet: "
                    f"<branch>\": AQ-9a's scorecard, c1's episode list, IMF IFS gold, "
                    f"AQ-5's break logic ({miss})")
    fake = types.ModuleType("fake_em_scorecard")
    fake.quarterly_block = lambda st, now: {
        "title": "The EM vulnerability scorecard",
        "table": {"columns": ["Country", "Current account"], "rows": [["Brazil", "−2.1%"]]},
        "notes": ["A table of lenses, never a composite."]}
    sys.modules["fake_em_scorecard"] = fake
    try:
        with observations.ObservationStore(vms.DB) as st:
            got = qi.panel_hook(st, {"id": "x", "n": "4d", "title": "The EM vulnerability "
                                     "scorecard", "kind": "hook", "module":
                                     "fake_em_scorecard", "reader": "quarterly_block",
                                     "branch": "aq-9a-em-scorecard"}, {"now": AS_OF})
    finally:
        sys.modules.pop("fake_em_scorecard", None)
    check(got.get("table", {}).get("rows") == [["Brazil", "−2.1%"]] and got.get("notes")
          and not got["not_tracked"],
          "with the branch's module present, the hook prints its block in the chapter")

    # -- China: computed rows and the quote-only rule ------------------------
    ch = by["china"]
    srows = {row[0]: row for row in ch["structure"]["table"]["rows"]}
    gap = srows.get("The fixing gap: spot against the fixing (the band is ±2%)")
    share = srows.get("Gold's share of official reserves (SAFE, market value)")
    check(gap and re.match(r"[+−-]?\d+\.\d\d%", gap[1]) and share
          and 0 < float(share[1].split("%")[0]) < 10,
          f"China's structure computes the fixing gap against the band and gold's "
          f"share of reserves from SAFE (under 10%: {share and share[1]})")
    pol, rpt = ch["china_political"], ch["china_political_reporting"]
    note_line = [x for x in pol["lines"] if x.startswith("The operator's political note")]
    check(all(x.get("quote_only") and "prose" not in x and "phase" not in x
              for x in (pol, rpt))
          and note_line and f"\"{OPERATOR_NOTE}\"" in note_line[0]
          and any(row[2] == "authoritative release" and "People's Bank" in row[1]
                  for row in rpt["table"]["rows"])
          and any(x.startswith("Rule: QUOTE ONLY") for x in pol["lines"])
          and any("announced → authorised → funded → implemented" in x
                  for x in pol["lines"])
          and any("Article IV" in x for x in pol["not_tracked"]),
          "China's political sub-section quotes the operator's note verbatim and the "
          "stored reporting (an authoritative release told from commentary), carries "
          "the ladder and the Article IV read, and has no prose frame")
    rule = fams["china"]["words"]["rules"][0]
    secs = q.summary_secs(ed)
    csum = next(x for x in secs if x["sid"] == "china")
    check("Write no political judgment" in rule and rule in qi.banned_note(fams["china"])
          and rule in csum["system"]
          and OPERATOR_NOTE not in _json.dumps(csum["slice"], ensure_ascii=False)
          and not any("china_political" in k for k in out["written"])
          and not any("china_political" in x["key"]
                      for x in __import__("monthly_macro.prose", fromlist=["x"])
                      .block_plan(ed)),
          "the quote-only rule is a banned behaviour in China's frames; the summary is "
          "never handed the note, and no model call is made for the political "
          "sub-section")
    calc = _yaml.safe_load((REPO / "config" / "china_political_calendar.yaml")
                           .read_text(encoding="utf-8"))
    check(calc.get("entries") == [] and calc.get("version") == "template"
          and any("maintained by hand" in x for x in pol["lines"]),
          "the China political calendar is a hand-seeded template with no entries, "
          "and the chapter says so")

    # -- Crypto: the coin pages, the tiers, the plumbing ---------------------
    cr = by["crypto"]
    labels = [lab for _, lab in qi.COIN_FIELDS]
    pages = [cr.get(f"coin_{c}") for c in ("btc", "eth", "sol", "zec", "prl")]
    check(all(pg and [row[0] for row in pg["table"]["rows"]] == labels for pg in pages)
          and len(labels) == 12,
          "five deep-tier coin pages, BTC, ETH, SOL, ZEC, PRL, each the same twelve "
          "fields in section 4.6's order")
    btc = {row[0]: row[1] for row in pages[0]["table"]["rows"]}
    prl = {row[0]: row[1] for row in pages[4]["table"]["rows"]}
    eth = {row[0]: row[1] for row in pages[1]["table"]["rows"]}
    check(btc["Bull / base / bear"].startswith("bull: ")
          and "cases_and_positioning.py" in btc["Bull / base / bear"]
          and "yfinance.mkt_btc_usd" in btc["Market structure and liquidity by venue"]
          and "observed" in btc["Source and vintage log"]
          and prl["Bull / base / bear"].startswith("not yet — ")
          and eth["Market structure and liquidity by venue"].startswith("not yet — ")
          and "MW-7" in prl["Measurable falsifiers"]
          and all(v for v in list(btc.values()) + list(prl.values())),
          "every field reads a stored series, the vendored case file or the tests -- "
          "or prints its not-yet reason (BTC from the store; ETH and PRL not yet)")
    lt = cr["light_tier"]["table"]["rows"]
    cfg_lt = next(p_ for p_ in fams["crypto"]["panels"] if p_["id"] == "light_tier")
    check([x[0].split()[0] for x in lt] == ["HYPE", "TAO", "LINK", "AAVE"]
          and all(x[2] == "pending MW-6 promotion" for x in lt)
          and all(c_["light_tier_pending_promotion"] is True for c_ in cfg_lt["coins"]),
          "the light tier HYPE, TAO, LINK, AAVE: light_tier_pending_promotion: true, "
          "printed \"pending MW-6 promotion\" until the operator's register write")
    pl = cr["stablecoin_plumbing"]["table"]
    check([x[0] for x in pl["rows"]] == ["USDT", "USDC", "DAI/USDS", "USDe"]
          and len(pl["columns"]) == 6
          and any("Developer activity: a named gap" in x
                  for x in cr["deck_items"]["not_tracked"])
          and any("Scan-tier only" in x for x in cr["crypto_scan"]["lines"])
          and any("MW-7" in x for x in cr["crypto_scan"]["lines"]),
          "the stablecoin plumbing table by issuer, the deck items with developer "
          "activity a named gap, and the scanning sub-chapter with MW-7 and the "
          "scan-only names")
    fz = {row[0][:30]: row[1] for row in cr["falsify"]["table"]["rows"]}
    sov = next(v for k, v in fz.items() if k.startswith('"Bitcoin is a store'))
    vol = next(v for k, v in fz.items() if k.startswith('"Institutional adoption'))
    check(sov in ("holds", "strained") and vol in ("holds", "strained", "failed")
          and sum(v.startswith("not measured — ") for v in fz.values()) == 5,
          f"Digital Assets' seven tests: the store-of-value band and the 70% drawdown "
          f"computed by code ({sov}; {vol}), five not measured with their reasons")
    csc = cr["scenarios"]["table"]["rows"]
    check([x[2] for x in csc] == ["~45%", "~30%", "~25%", "~20%", "~35%", "~30%", "~15%"],
          "crypto's scenario sets: 2026-29 at 45 / 30 / 25 and the ten-year four")

    # -- Credit, real estate, international equities, agriculture -----------
    crd = by["credit"]
    cf = {row[0][:35]: row for row in crd["falsify"]["table"]["rows"]}
    ls = next(v for k, v in cf.items() if k.startswith('"The credit cycle is a'))
    bbc = next((row for row in crd["structure"]["table"]["rows"]
                if row[0].startswith("BB-CCC")), None)
    check(ls[1] == "holds" and "SLOOS" in ls[2] and bbc and " bp" in bbc[2],
          f"credit: the lending-standards test holds with no 200 bp widening "
          f"({ls[2][:60]}...); BB-CCC computed from the two OAS series ({bbc and bbc[2]})")
    # SLOOS is the lending-standards leg (the operator's ruling on part 2's
    # choice 6); the HY OAS reading is labelled a proxy until it is stored.
    crd_nt = " ".join(crd["structure"].get("not_tracked") or [])
    check("proxy until SLOOS" in ls[2]
          and crd_nt.count("not yet: aq-3-series-2") == 3,
          "credit: SLOOS (C&I large and small, CRE) is the lending-standards "
          "measurable, named \"not yet: aq-3-series-2\" until registered; the HY "
          "OAS reading is labelled \"proxy until SLOOS\"")
    from monthly_macro import quarterly_items as qi_
    real_reg, real_rows = qi_.derived.registry_entry, qi_.rows
    try:
        qi_.derived.registry_entry = lambda k: ({"key": k} if k.startswith(
            "fred.sloos") else real_reg(k))
        qi_.rows = lambda st_, k, now, inst=None, end=None: [
            ("2025-10-01", -2.0), ("2026-01-01", 0.0), ("2026-04-01", -1.5),
            ("2026-07-01", 3.1 if k.endswith("small") else -0.4)]
        ctx_ = {"end": "2026-09-30", "now": "2026-10-11T00:00:00+00:00"}
        eased = qi_._leaf(None, "not_tightened", {"hook_series": "fred.sloos_ci_large",
                                                  "branch": "x", "quarters": 4}, ctx_)
        tight = qi_._leaf(None, "not_tightened", {"hook_series": "fred.sloos_ci_small",
                                                  "branch": "x", "quarters": 4}, ctx_)
        hooked, _ = qi_.resolve_hook({"hook_key": "fred.sloos_ci_large",
                                      "branch": "x", "label": "y"})
    finally:
        qi_.derived.registry_entry, qi_.rows = real_reg, real_rows
    unhooked, why = qi_.resolve_hook({"hook_key": "nobody.key", "branch": "b-1",
                                      "label": "y"})
    check(eased["met"] is True and tight["met"] is False
          and hooked and hooked["key"] == "fred.sloos_ci_large"
          and unhooked is None and why == "not yet: b-1",
          "a hook reads its key once registered and says \"not yet: <branch>\" "
          "before; SLOOS with no print above zero in four quarters is \"not "
          "tightened\", one print above zero is tightened")
    cur_ = {ss.get("item"): ss for ss in chs["currency"]["subsections"]}
    cnt = " ".join(cur_["structure"].get("not_tracked") or [])
    check("CNH-CNY, bp: not yet: aq-3-series-1" in cnt
          and "TFF" in cnt and cnt.count("not yet: aq-3-series-1") >= 11,
          "the rows AQ-3 part 1's writers fill name aq-3-series-1 until it merges "
          "(CNH-CNY, the TFF positioning)")
    re_rows = {row[0]: row for row in by["real_estate"]["structure"]["table"]["rows"]}
    msp = re_rows.get("The mortgage spread over the 10-year")
    check(msp and " bp" in msp[2]
          and [x[2] for x in by["real_estate"]["scenarios"]["table"]["rows"]]
          == ["~55%", "~30%", "~15%"],
          "real estate: the mortgage spread computed; the CRE ten-year families "
          "55 / 30 / 15")
    intl = by["intl_equities"]
    rd_ = intl["return_decomp"]["table"]
    ir = {row[0]: row for row in intl["structure"]["table"]["rows"]}
    t10 = next((v for k, v in ir.items() if k.startswith("Trailing ten-year")), None)
    c3 = next((v for k, v in ir.items() if k.startswith("The three-year rolling")), None)
    check(len(rd_["rows"]) >= 4 and all(x[4:] == ["not stored"] * 4 for x in rd_["rows"])
          and any("currency term" in x for x in intl["return_decomp"]["not_tracked"])
          and t10 and "pp a year" in t10[1] and c3 and "months" in c3[1],
          f"international equities: GTM-19's decomposition from ETF proxies (price and "
          f"dividends; currency, multiple, earnings named as lacking), the ten-year US "
          f"gap and the three-year correlation ({c3 and c3[1][:40]})")
    ag = by["agriculture"]
    check(any("thin or poorly understood contracts" in x for x in ag["book"]["lines"])
          and [x[0] for x in ag["softs"]["table"]["rows"]]
          == ["Sugar", "Coffee", "Cocoa", "Cotton"]
          and any(x.startswith("Corn (front month)") for x in ag["quarter"]["not_tracked"])
          and any("WASDE corn" in x for x in ag["structure"]["not_tracked"]),
          "agriculture: the WASDE balances wait for AQ-3's writer by name; the softs as "
          "one table; \"thin or poorly understood contracts\" a no draft by rule")

    # -- Thailand: the isolation ---------------------------------------------
    th = fams["thailand"]
    iso = th.get("isolation") or {}
    own = [s_ for s_ in (th.get("five_lines") or []) + (th.get("structure") or [])
           if s_.get("namespace") == "thailand"]
    leak = [s_["label"] for s_ in own if s_.get("key") and not (
        (derived.registry_entry(s_["key"]) or {}).get("namespace") == "thailand"
        and (derived.registry_entry(s_["key"]) or {}).get("trigger_eligible") is False)]
    reg_all = derived._load_registry()
    reg_leak = [k for k, v in reg_all.items() if (v or {}).get("namespace") == "thailand"
                and (v or {}).get("trigger_eligible")]
    cfg_leak = [n for n in TRIGGER_CONFIGS if (REPO / "config" / n).exists() and any(
        t in (REPO / "config" / n).read_text(encoding="utf-8").lower() for t in THAI_TOKENS)]
    pil = _yaml.safe_load((REPO / "config" / "pillars.yaml").read_text(encoding="utf-8"))
    p11 = (pil.get("pillars") or pil).get("11") or {}
    code_leak = [str(x.relative_to(REPO)) for d in ("altdata", "daily_cascade",
                                                     "monthly_macro", "register")
                 for x in (REPO / d).rglob("*.py")
                 if "thailand_political_calendar" in x.read_text(encoding="utf-8",
                                                                  errors="replace")]
    check(iso == {"namespace": "thailand", "trigger_eligible": False, "feeds": [],
                  "note": iso.get("note")} and own and not leak and not reg_leak
          and not cfg_leak and p11.get("dial") is None and not p11.get("weight")
          and not p11.get("metrics") and not code_leak
          and next(c_ for c_ in stack_cfg()["quarterly_chapters"]
                   if c_["id"] == "thailand")["correlation_assets"] == [],
          f"Thailand's isolation: namespace thailand, trigger_eligible false, feeds "
          f"nothing; no Thai row is a trigger-eligible key, no trigger config names it, "
          f"pillar 11 has no dial or weight, no code but the chapter reads its calendar "
          f"({leak or reg_leak or cfg_leak or code_leak})")
    tb = by["thailand"]
    cols = [c_.lower() for ss in tb.values() for t_ in ([ss.get("table")]
                                                       + list(ss.get("tables") or []))
            if t_ for c_ in t_.get("columns") or []]
    check(tb["book"]["lines"][0].startswith("No draft, by rule: the Thailand chapter is "
                                            "isolated")
          and not any(w in c_ for c_ in cols for w in PRIVATE_COLUMNS)
          and any(x.startswith("Isolation: namespace: thailand, trigger_eligible: false")
                  for x in tb["frame"]["lines"])
          and any("BoT, MoF, NESDC" in x for x in tb["thai_scan"]["lines"]),
          "Thailand writes no register draft, prints no column of the private core "
          "(conversion, budget, payments), states its isolation in its frame and "
          "carries the Thai source hierarchy")

    # -- The executive summary over the eleven -------------------------------
    check(len(secs) == 11 and [x["sid"] for x in secs] == all_ids_of(chs)
          and all(qi.banned_note(fams[x["sid"]]) in x["system"] for x in secs),
          "the executive summary is one frame per chapter over all eleven, each "
          "carrying its chapter's permitted and banned words and rules")


def all_ids_of(chs: dict) -> list[str]:
    return list(chs)


def main() -> int:
    vms.seed(vms.DB, dealer_sessions=21)
    seed_aq2(vms.DB)
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
    group_g(r)
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed, {WARN} warned\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
