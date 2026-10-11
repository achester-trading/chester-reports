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
  G CHAPTERS   (AQ-2 part 1) metals, oil and energy, currency filled item by
               item: every item renders or prints its not-yet reason; the
               falsification config's measurables name registered keys, its
               statements and the ten questions are the papers' verbatim; each
               item's figure budget holds at the frame; the tests computed by
               code; the transmission map; the three chapters end to end with
               the executive summary.

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
    shell = next(c for c in chs if not c["data"].get("filled"))
    plain = [x for x in shell["subsections"] if not x.get("divider")
             and not x.get("hook")]
    check(plain and all(x["not_tracked"] == [q.NOT_BUILT] for x in plain),
          f"every item AQ-2 has not filled yet prints \"{q.NOT_BUILT}\" in the "
          f"not-yet-tracked form ({len(plain)} in {shell['title']})")
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
}


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
    with observations.ObservationStore(db) as st:
        st.write_many(obs)
    with vmod.VoicesStore(db) as vs:
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


def group_g(r: dict) -> None:
    import json as _json
    from altdata import derived
    from daily_cascade import readability as rd
    from monthly_macro import prose as prose_mod, quarterly as q
    from monthly_macro import quarterly_items as qi
    print(f"\n{LINE}\nG. AQ-2 PART 1 -- THE FIRST THREE DEEP CHAPTERS\n{LINE}")
    qc = qi.load_config()
    fams = {k: v for k, v in (qc.get("families") or {}).items() if v.get("filled")}
    check(sorted(fams) == ["currency", "metals", "oil_energy"],
          "metals, oil and energy, and currency are filled; the other eight stay on "
          "the shell for part 2")
    reg = derived.registry_entry
    keys, bad = [], []
    for fid, f in fams.items():
        for s_ in (f.get("five_lines") or []) + (f.get("structure") or []) + (
                (f.get("second_half") or {}).get("structure") or []):
            if s_.get("key"):
                keys.append(s_["key"])
            elif not s_.get("absent"):
                bad.append(f"{fid}: {s_.get('label')} has neither a key nor absent")
        for c in f.get("structure_charts") or []:
            keys += [x["key"] for x in c["series"]]
        for qn in f.get("ten_questions") or []:
            keys += list(qn.get("series") or [])
        for a in f.get("analyses") or []:
            keys += list(a.get("series") or [])
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
    counts = {fid: len(f["falsification"]) for fid, f in fams.items()}
    check(counts == {"metals": 7, "oil_energy": 7, "currency": 6},
          f"the papers' own tests: Metals 7, Energy 7, Currencies 6 ({counts})")

    def norm(t: str) -> str:
        return " ".join(t.replace("\\$", "$").replace("**", "").split())
    miss = []
    for fid, f in fams.items():
        paper = norm((REPO / f["paper_file"]).read_text(encoding="utf-8"))
        for t in f["falsification"]:
            if norm(t["statement"]) not in paper:
                miss.append(t["id"])
        for qn in f["ten_questions"]:
            if f"{qn['n']}. {norm(qn['text'])}" not in paper:
                miss.append(f"{fid} Q{qn['n']}")
    check(not miss and all(len(f["ten_questions"]) == 10 for f in fams.values()),
          f"every test's statement and every one of the ten questions is the "
          f"paper's own wording, verbatim ({miss[:4]})")
    from daily_cascade import cadence
    cap = cadence.figure_cap(cadence.get("quarterly"))
    check(all(0 <= int(v) <= cap for f in fams.values()
              for v in (f.get("figure_budget") or {}).values())
          and all({"quarter", "supply", "questions"} <= set(f.get("figure_budget") or {})
                  for f in fams.values()),
          f"each filled chapter declares a figure budget per written item, none above "
          f"the cadence's cap ({cap})")

    ed, out = r["ed"], r["out"]
    chs = {c["id"]: c for c in q.chapters(ed)}
    filled = [chs[f] for f in ("metals", "oil_energy", "currency")]
    check(all(c["data"].get("filled") for c in filled)
          and not any(c["data"].get("filled") for k, c in chs.items()
                      if k not in fams),
          "the dry run renders the three filled chapters and leaves eight on the shell")
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
    check(all(x == ["lead_lines", "graded", "theses", "quarter"] for x in lead_items),
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
    check(len(drawn_) == 2 and "AQ-4" in str(lf.get("unavailable")),
          "the two structure charts are drawn; the long frame says it waits for AQ-4")
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
          "name) and the scan tier (fifteen, from H.10, not yet pulled)")
    an = met["analyses"]["table"]["rows"]
    check(all(len(x) == 3 and x[2] for x in an)
          and any("AQ-8a" in x[1] for x in an) and any("AQ-5" in x[1] for x in an),
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
          "the synthetic-store dry run renders the three filled chapters end to end "
          "with the executive summary")


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
