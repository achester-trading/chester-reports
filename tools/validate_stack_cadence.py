#!/usr/bin/env python3
"""
Validation gate for T2.6: the stack serves two cadences, and the week's small
items. (8 Oct 2026)

    python tools/validate_stack_cadence.py

No network, no box, no live store -- every store here is a temporary one:

  A CADENCES    config `cadences:` resolves daily, weekly and monthly: period,
                column, budget, reading target, depth allowances, paragraph rule;
                every period phrase derives from the noun.
  B BUILDERS    the four builders the Monthly reuses (What doesn't fit,
                Plumbing, Positioning, What's priced), at cadence "monthly" over
                an empty store, print no "week" phrase; at "weekly" they print the
                Weekly's own.
  C RENDER      stack_render.section_html at "monthly" prints sub-section
                paragraphs and footnotes and every kept paragraph; at "weekly" one
                paragraph and no sub-section paragraph; details_html prints the
                detail blocks under one heading.
  D GUARD       finalize / section_words / edition_words / reading_minutes per
                cadence: the Weekly's one paragraph of 120 words; the Monthly's
                paragraphs kept and cut at the section's depth allowance.
  E PROSE       section_prompt / read_prompt carry the cadence's report, period
                and frames; a failed API call (call_failed) is NOT retried, an
                audit failure is retried once (Reader's Guide 5.3).
  F CLOSE       the stacked close's state and contradiction tables, read from the
                stored object (never recomputed), after section 10 and before the
                glossary; absent rows carry their reason; no object says so.
  G SCRIPTS     a wrapper's captured output is logged with its newline (the 7 Oct
                "491 rows written2026-10-07T10:47" join).
  H CI          every workflow job runs on a pinned image, never `-latest`.
  J GLOSSARY    Slow layers, the dealer flags, the IV check and hit rates are in
                the glossary, quoting config's thresholds.
  I REGISTRY    the gate is in the Makefile's list.

T2.7 (8 Oct 2026): what the shared renderer carries for the Monthly.

  K ENTRIES     a Reading entry's title line is hyperlinked and its stored
                summary prints escaped and otherwise verbatim: never polished or
                trimmed, outside the prose words, inside the reading time.
  L CHARTS      at "monthly" a sub-section's charts print under it; at "weekly"
                every chart at section level as before; page_html and markdown
                print the edition in one order, each chart's line in place.
  M BUDGET      trim_to_budget (the Monthly's): the appendix first, then the
                last of several paragraphs, back to front; never a claim or item.
  N CONFIG      a section declared at one cadence only (Reading) is skipped at
                the others; the ten always; B's Monthly keys are present.
  O TICKS       dated ticks: first and last always, none within half a step.
  P NAMES       the helper names the Monthly imports stay.
"""

from __future__ import annotations

import os
import re
import sys
import types
from pathlib import Path
import os as _gt_os                                            # noqa: E402
import sys as _gt_sys                                          # noqa: E402
_gt_dir = _gt_os.path.dirname(_gt_os.path.abspath(__file__))
_gt_sys.path.insert(0, _gt_dir if _gt_os.path.basename(_gt_dir) == "tools"
                    else _gt_os.path.join(_gt_dir, "tools"))
from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LINE = "=" * 78
PASS = FAIL = 0

TD = gate_mkdtemp(prefix="validate_stack_cadence_")
DB = str(Path(TD) / "cadence.db")
os.environ["CHESTER_DB"] = DB


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def strings(v) -> list[str]:
    """Every string a built block would print: values and column heads, never
    keys (a data key like `week_mean` is not printed)."""
    if isinstance(v, str):
        return [v]
    if isinstance(v, dict):
        return [s for k, x in v.items() if k not in ("key", "fingerprint")
                for s in strings(x)]
    if isinstance(v, (list, tuple)):
        return [s for x in v for s in strings(x)]
    return []


# Phrases that are about a week whatever the cadence: the retail-sentiment
# comparison window, a five-session change, a weekly source, the 52-week range.
WEEK_OK = re.compile(r"the week before the month|Week change|weekly|52-week", re.I)


def group_a() -> None:
    print(f"\n{LINE}\nA. THE CADENCES, FROM CONFIG\n{LINE}")
    from daily_cascade import cadence
    cads = {n: cadence.get(n) for n in cadence.NAMES}
    check([c["period"] for c in cads.values()] == ["session", "week", "month"],
          "daily, weekly and monthly resolve to session, week and month")
    check(cads["weekly"]["budget"] == {"words": 3500, "charts": 10}
          and cads["monthly"]["budget"] == {"words": 10000, "charts": 12}
          and [cads[n]["reading_target_minutes"] for n in cadence.NAMES] == [5, 20, 55],
          "each carries its budget and reading target from the ratified config")
    check(cads["monthly"]["depth_words"]["deep"] == 450
          and cads["weekly"]["depth_words"]["deep"] == 420
          and cads["daily"]["depth_words"]["deep"] == 150,
          "each reads its own depth allowances")
    check(cadence.paragraph_cap(cads["weekly"], "deep") == 120
          and cadence.paragraph_cap(cads["monthly"], "deep") == 450
          and cadence.paragraph_cap(cads["monthly"], "medium") == 220,
          "the Weekly's paragraph is 120 words; the Monthly's is its depth allowance")
    w, m = cadence.Period.of("weekly"), cadence.Period.of("monthly")
    check((w.on, w.This, w.end, w.col, w.or_prior, w.mean, w.since_report)
          == ("on the week", "This week", "at the week's end", "Week",
              "Week or prior", "week mean", "since the prior report"),
          "the weekly phrases are the Weekly's own strings")
    check((m.on, m.This, m.End, m.col, m.or_prior, m.mean, m.since_report,
           m.week_before)
          == ("on the month", "This month", "At the month's end", "The month",
              "Month or prior", "month mean", "on the month",
              "the week before the month"),
          "and the monthly ones derive from the noun")
    try:
        cadence.get("quarterly")
        check(False, "an undeclared cadence is refused")
    except KeyError:
        check(True, "an undeclared cadence is refused (KeyError, a code fault)")


def group_b() -> None:
    print(f"\n{LINE}\nB. THE SHARED BUILDERS AT THE MONTHLY'S CADENCE\n{LINE}")
    from altdata import observations
    from daily_cascade import stack as stack_mod, weekly_stack as ws
    now, then = "2026-09-30T21:00:00+00:00", "2026-08-31T21:00:00+00:00"
    wis = {"exceptions_opened": ["extreme:fred.hy_oas"],
           "exceptions_open_now": ["extreme:fred.hy_oas"],
           "exceptions_intraweek_only": ["extreme:fred.yield_10y"]}
    cfg = stack_mod.config()
    with observations.ObservationStore(DB) as st:
        built = {
            "misfit": lambda c: ws.misfit_week(wis, None, {}, cadence=c),
            "plumbing": lambda c: ws.plumbing_week(st, now, then, None, cadence=c),
            "positioning": lambda c: ws.positioning_week(st, now, then, cadence=c),
            "priced": lambda c: ws.priced_week(st, now, then, cfg, None, None, None,
                                               cadence=c),
        }
        for sid, f in built.items():
            mon = [s for s in strings(f("monthly")) if "week" in s.lower()
                   and not WEEK_OK.search(s)]
            check(not mon, f"{sid} at 'monthly' prints no week phrase"
                  + (f" ({mon[:3]})" if mon else ""))
            wk = strings(f("weekly"))
            check(any("week" in s.lower() for s in wk) and
                  not any(re.search(r"\bmonth\b", s) and "One month" not in s
                          and "TIC" not in s and "Month" != s for s in wk
                          if "on the month" in s or "this month" in s.lower()),
                  f"{sid} at 'weekly' keeps the Weekly's phrases")
        mis = ws.misfit_week(wis, None, {}, cadence="monthly")
        txt = " ".join(strings(mis))
        check("Opened and closed inside the month" in txt
              and "Exceptions open at the month's end" in txt,
              "the misfit phrases the Monthly's old word swap missed now derive "
              "('inside the month')")


def _sec(sid="positioning", depth="deep", paragraphs=None, subs=None, **kw):
    s = {"id": sid, "title": "Positioning & flows", "subtitle": "who holds what",
         "depth": depth, "items": [], "table": {"columns": ["A", "B"],
                                                 "rows": [["x", "1.0"]]},
         "subsections": subs or [], "paragraphs": paragraphs or [], "claim": "Claim.",
         "empty": False, "not_tracked": ["section gap"], "trimmed": False}
    s.update(kw)
    return s


def group_c() -> None:
    print(f"\n{LINE}\nC. ONE RENDERER, THREE CADENCES\n{LINE}")
    from daily_cascade import stack_render as sr
    subs = [{"title": "Theme one", "table": {"columns": ["T", "V"], "rows": [["t", "2"]]},
             "paragraphs": ["Sub paragraph one.", "Sub paragraph two."],
             "not_tracked": ["sub gap"]}]
    s = _sec(paragraphs=["First paragraph.", "Second paragraph."], subs=subs,
             period="month")
    m = sr.section_html(s, 6, {}, "email", "monthly")
    check("Sub paragraph one." in m and "Sub paragraph two." in m,
          "at 'monthly' a sub-section's paragraphs print")
    check(m.index("Sub paragraph two.") < m.index("Not yet tracked: sub gap")
          < m.index("First paragraph."),
          "each sub-section carries its own footnote, before the section's prose")
    check("First paragraph." in m and "Second paragraph." in m
          and "Not yet tracked: section gap." in m and "sub gap; " not in m,
          "every kept section paragraph prints, and the section's footnote keeps "
          "its own gaps")
    s["period"] = "week"
    w = sr.section_html(s, 6, {}, "email", "weekly")
    check("Sub paragraph one." not in w and "Second paragraph." not in w
          and "First paragraph." in w
          and "Not yet tracked: section gap; sub gap." in w,
          "at 'weekly' one paragraph, no sub-section paragraph, and the "
          "sub-sections' gaps fold into the section's footnote")
    s.update(trimmed=True)
    check("(trimmed)" in sr.section_html(s, 6, {}, "email", "monthly")
          and "Commentary trimmed to one paragraph." in
          sr.section_html(s, 6, {}, "email", "weekly"),
          "the trimmed note is the cadence's")
    det = [{"title": "The regime", "table": {"columns": ["Read", "State"],
                                             "rows": [["dealer gamma", "positive"]]},
            "notes": ["A detail note."]}]
    d = sr.details_html(det, "monthly")
    check(d.startswith(f'<h2 style="{sr.SECTION}">Detail tables</h2>')
          and "The regime" in d and "A detail note." in d,
          "details_html prints the detail blocks under one heading")
    check(sr.details_html([], "daily") == "" and sr.details_html(None) == "",
          "and nothing when the edition carries none")


def group_d() -> None:
    print(f"\n{LINE}\nD. THE PARAGRAPH GUARD AND THE WORD COUNT, PER CADENCE\n{LINE}")
    from daily_cascade import readability as rd, stack as stack_mod
    long = " ".join(f"Sentence number {i} runs on for nine words here." for i in range(80))
    wk = {"sections": [_sec(paragraphs=[long, "A second paragraph."],
                            subs=[{"title": "s", "paragraph": "gone"}])]}
    rd.finalize(wk, "weekly")
    s = wk["sections"][0]
    check(len(s["paragraphs"]) == 1 and stack_mod.words(s["paragraphs"][0]) <= 120
          and s["trimmed"] and "paragraph" not in s["subsections"][0],
          "the Weekly keeps one paragraph cut to 120 words at a sentence, and "
          "drops a sub-section's")
    mo = {"sections": [_sec(paragraphs=[long, "A second paragraph."],
                            subs=[{"title": "s", "paragraphs": [long, "Kept."]}])],
          "detail": [{"title": "d", "paragraphs": ["Detail prose here."]}]}
    rd.finalize(mo, "monthly")
    s = mo["sections"][0]
    ss = s["subsections"][0]
    check(len(s["paragraphs"]) == 2 and stack_mod.words(s["paragraphs"][0]) <= 450
          and stack_mod.words(s["paragraphs"][0]) > 120 and s["trimmed"],
          "the Monthly keeps its paragraphs, each cut at the deep allowance (450)")
    check(len(ss["paragraphs"]) == 2 and stack_mod.words(ss["paragraphs"][0]) <= 450
          and ss.get("trimmed"),
          "and a sub-section keeps its own, under the same cap")
    total = (stack_mod.words(s["claim"]) + sum(stack_mod.words(p) for p in s["paragraphs"])
             + sum(stack_mod.words(p) for p in ss["paragraphs"]) + 3)
    check(stack_mod.edition_words(mo) == total == mo["words"],
          f"edition_words counts the claim, the paragraphs, the sub-sections' "
          f"paragraphs and the detail's ({mo['words']})")
    mo["chart_count"] = 3
    want = max(1, -(-int((total / 250 + 3 * 20 / 60.0) * 1e9) // int(1e9)))
    check(rd.reading_minutes(mo) == want == rd.reading_minutes(mo, 3),
          f"reading_minutes: 250 words a minute plus 20 seconds a chart, over the "
          f"whole edition ({rd.reading_minutes(mo)})")
    check(rd.reading_target("monthly") == 55 and rd.reading_target("weekly") == 20,
          "reading_target reads the cadence's")


class _Resp:
    def __init__(self, t):
        self.content = [types.SimpleNamespace(type="text", text=t)]
        self.model = "fixture-model"
        self.stop_reason = "end_turn"


def group_e() -> None:
    print(f"\n{LINE}\nE. THE PROSE HOOK, AND THE ONE RETRY\n{LINE}")
    from daily_cascade import stack_prose as sp
    s = _sec(sid="plumbing", depth="deep")
    s["title"] = "Plumbing & rates"
    for cad, rep, per in (("daily", "the daily close", "session"),
                          ("weekly", "the Weekly", "week"),
                          ("monthly", "the Monthly", "month")):
        p = sp.section_prompt(s, cad)
        check(f"ONE SECTION of\n{rep}" in p or f"ONE SECTION of {rep}" in p,
              f"section_prompt at '{cad}' names {rep}")
        check(f"says about the {per}" in p, f"and writes about the {per}")
    check("at most 450 words" in sp.section_prompt(s, "monthly")
          and "at most 120 words" in sp.section_prompt(s, "weekly"),
          "the paragraph allowance is the cadence's")
    check("Write ONLY that one sentence." in sp.section_prompt(s, "monthly",
                                                               claim_only=True),
          "claim_only asks for the claim line alone")
    check(sp.section_prompt(s, "monthly", extra_notes={"plumbing": "\n\nEXTRA NOTE."})
          .endswith("EXTRA NOTE."), "a report's own notes are appended last")
    check(sp.section_max_chars(s, "monthly") == int(sp.MAX_CHARS["deep"] * 2.5)
          and sp.section_max_chars(s, "daily") == sp.MAX_CHARS["deep"],
          "the runaway guard scales by the cadence's chars_scale")
    check("the month" in sp.read_prompt("monthly") and "THE WEEK BY DAY" in
          sp.read_prompt("weekly") and "THE WEEK BY DAY" not in sp.read_prompt("daily"),
          "read_prompt carries the period, and the Weekly's own note")
    check(all(sp.not_retried({"state": x}) for x in
              ("fault", "unavailable", "call_failed", "prompt_too_large",
               "payload_too_large", "empty", "too_long"))
          and not sp.not_retried({"state": "audit_failed"})
          and not sp.not_retried({"state": "tape_rules"}),
          "faults are not retried; audit refusals are")

    # The write() loop itself: a client whose every call raises.
    calls = []

    def boom(**k):
        calls.append(k["system"])
        raise RuntimeError("fixture API outage")
    ed = {"session": "2026-10-02", "sections": [
        {**_sec(sid="read", depth="deep"), "title": "The read", "items": []},
        {**_sec(sid="tape", depth="deep"), "title": "The tape", "items": [],
         "data": {"level_status": {}, "levels": []}},
        {**_sec(sid="plumbing", depth="deep"), "title": "Plumbing & rates",
         "items": []}]}
    cli = types.SimpleNamespace(messages=types.SimpleNamespace(create=boom))
    sp.write(ed, client=cli, outlooks=[], cadence="weekly")
    pr = ed["prose"]
    check(all(v["state"] == "call_failed" and v["attempts"] == 1 for v in pr.values())
          and len(calls) == len(pr),
          f"a failed API call is made ONCE per section, never retried "
          f"({len(calls)} calls for {len(pr)} sections)")

    # An audit failure IS retried once.
    seq = []

    def audit_then_clean(**k):
        seq.append(k["system"])
        if "THE SECTION: Plumbing" in k["system"] and len(
                [x for x in seq if "THE SECTION: Plumbing" in x]) == 1:
            return _Resp("Yields rose because of supply.")
        return _Resp("The curve held its shape.")
    ed2 = {"session": "2026-10-02", "sections": [dict(x) for x in ed["sections"]]}
    for x in ed2["sections"]:
        x.pop("withheld", None)
    sp.write(ed2, client=types.SimpleNamespace(
        messages=types.SimpleNamespace(create=audit_then_clean)), outlooks=[],
        cadence="weekly")
    pl = ed2["prose"]["plumbing"]
    plumb = [x for x in seq if "THE SECTION: Plumbing" in x]
    check(pl["attempts"] == 2 and pl["published"] and len(plumb) == 2
          and "WITHHELD BY THE AUDIT: withheld: motive" in plumb[1],
          f"an audit refusal (a motive word) is retried once with its reason "
          f"({pl['state']}, {pl['attempts']} attempts)")


def _obj() -> dict:
    return {"schema_version": "market-state-v2", "session": "2026-10-02",
            "config_version": "v1.12", "computed_at": "2026-10-02T20:50:00+00:00",
            "dials": {"gamma": {"state": "positive", "level": 1.234567},
                      "vol": {"state": None, "absent_reason": "VIX not stored"},
                      "macro": {"state": "mixed"}},
            "dimensions": {"credit": {"state": "stressed", "percentile": 4.04,
                                      "direction": "widening", "confidence": "high",
                                      "contradicting": ["equities"]},
                           "liquidity": {"state": None, "fault": "KeyError: 'tga'"}},
            "contradictions": [
                {"id": "equities_vs_credit", "open_state": "open", "magnitude": 2.71,
                 "persistence_days": 6, "since": "2026-09-25", "exception": True},
                {"id": "long_bond_vs_hy", "open_state": "absent",
                 "absent_reason": "the 30-year is stale"}]}


def group_f() -> None:
    print(f"\n{LINE}\nF. THE CLOSE'S STATE AND CONTRADICTION TABLES\n{LINE}")
    import inspect
    from daily_cascade import state_block, stack_render as sr, stack_close
    obj = _obj()
    det = state_block.detail_tables({"market_state": obj})
    st, ct = det
    rows = {r[0]: r for r in st["table"]["rows"]}
    check(rows["Dealer gamma"] == ["Dealer gamma", "positive", "1.23"]
          and rows["Volatility regime"][1] == "absent",
          "the dials in the market's words, levels at two decimals, absent as absent")
    dims = {r[0]: r for r in st["tables"][0]["rows"]}
    check(dims["Credit"] == ["Credit", "stressed", "4.0", "widening", "high",
                             "equities"] and dims["Liquidity"][1] == "absent",
          "each dimension's state, percentile, direction, confidence and "
          "contradictions are the object's own fields")
    notes = " ".join(st["notes"])
    check("VIX not stored" in notes and "FAULT (code, not data) -- KeyError" in notes
          and "read from the store, not recomputed" in notes,
          "an absence carries its reason, a fault is labelled a fault, and the "
          "block says it was read, not recomputed")
    crow = {r[0]: r for r in ct["table"]["rows"]}
    check(crow.get("Equities against credit", crow.get(next(iter(crow))))[1:]
          == ["open (exception)", "+2.7", "6", "2026-09-25"]
          and any(r[1] == "absent" for r in ct["table"]["rows"])
          and "the 30-year is stale" in " ".join(ct["notes"]),
          f"the contradiction table: state, gap z, days, since; an absent pair "
          f"with its reason ({list(crow)})")
    check(len(st["table"]["columns"]) <= 6 and len(st["tables"][0]["columns"]) <= 6
          and len(ct["table"]["columns"]) <= 6, "no table wider than six columns")
    none = state_block.detail_tables({})
    check(len(none) == 1 and "No market-state object" in none[0]["notes"][0],
          "no object: one block saying so, never a recomputed one")
    src = inspect.getsource(state_block.detail_tables)
    check("import regime" not in src and "compute(" not in src,
          "detail_tables reads the object and computes nothing")
    check("state_block.detail_tables(p)" in inspect.getsource(stack_close.produce),
          "the stacked close attaches them from the payload's stored object")
    secs = [{**_sec(sid=f"s{i}"), "title": f"Section {i}"} for i in range(1, 11)]
    ed = {"sections": secs, "detail": det, "as_of": "2026-10-02T21:00:00+00:00",
          "words": 10, "chart_count": 0, "config_version": "reporting-stack-v1"}
    html = sr.render({"session": "2026-10-02", "market_state": obj}, ed, {}, "email")
    i10 = html.index("10 &middot; Section 10")
    idt = html.index(">Detail tables</h2>")
    igl = html.index(">Glossary</h2>") if ">Glossary</h2>" in html else len(html)
    check(i10 < idt < igl, "they print after section 10 and before the glossary")


def group_g() -> None:
    print(f"\n{LINE}\nG. A WRAPPER'S CAPTURED OUTPUT KEEPS ITS NEWLINE\n{LINE}")
    bad = []
    for f in sorted((REPO / "scripts").glob("*.sh")):
        for n, ln in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"printf '%s' \"\$[A-Z_]+\"\s*\|.*>>\s*\"?\$LOG", ln):
                bad.append(f"{f.name}:{n}")
    check(not bad, "no captured block is logged without its trailing newline "
                   "(printf '%s\\n')" + (f"; at {bad}" if bad else ""))


def group_h() -> None:
    print(f"\n{LINE}\nH. CI RUNS ON A PINNED IMAGE\n{LINE}")
    runs = []
    for f in sorted((REPO / ".github" / "workflows").glob("*.yml")):
        for n, ln in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            m = re.match(r"\s*runs-on:\s*(\S+)", ln)
            if m:
                runs.append((f"{f.name}:{n}", m.group(1)))
    floating = [w for w, v in runs if "latest" in v]
    check(runs and not floating and all(v == "ubuntu-24.04" for _, v in runs),
          f"every job pins ubuntu-24.04 ({len(runs)} jobs)"
          + (f"; floating at {floating}" if floating else ""))


def group_glossary() -> None:
    print(f"\n{LINE}\nJ. THE GLOSSARY'S MONTHLY TERMS MATCH THE CONFIG\n{LINE}")
    from altdata import labels
    from daily_cascade import stack as stack_mod
    g = {e["term"]: e["text"] for e in labels.glossary()}
    check(all(t in g for t in ("Slow layers", "pinned, held, amplified", "IV check",
                               "hit rate")),
          "the glossary carries Slow layers, the dealer flags, the IV check and "
          "hit rates")
    fc = stack_mod.config().get("dealer_flags") or {}
    floor = stack_mod.config().get("dealer_retrospective_min_sessions")
    fl = g.get("pinned, held, amplified", "")

    def pct(v) -> str:
        return f"{float(v):g}%"
    check(f"within {pct(fc.get('pinned_pct'))} of max pain" in fl
          and f"within {pct(fc.get('wall_pct'))} of the morning's call wall" in fl
          and f"at least {float(fc.get('amplified_range_ratio')):g} times" in fl,
          "the flag thresholds quoted are config's dealer_flags")
    check(f"more than {float(fc.get('iv_vix_check_points')):g} volatility points"
          in g.get("IV check", "")
          and f"below {floor} scored sessions" in g.get("hit rate", ""),
          "and the IV check's gap and the retrospective's floor")


def group_i() -> None:
    print(f"\n{LINE}\nI. THE GATE IS REGISTERED\n{LINE}")
    mk = (REPO / "Makefile").read_text(encoding="utf-8")
    check("tools/validate_stack_cadence.py" in mk, "the Makefile's list carries it")


def _chart(cid: str, caption: str) -> dict:
    return {"id": cid, "caption": caption, "svg_path": f"/tmp/x/{cid.lower()}.svg"}


def group_k() -> None:
    print(f"\n{LINE}\nK. READING ENTRIES: STORED TEXT, VERBATIM (T2.7)\n{LINE}")
    from daily_cascade import readability as rd
    from daily_cascade import stack as stack_mod
    from daily_cascade import stack_render as sr
    raw = "Fed's  \"path\" -- <b>2026-10-01</b> & 3 week(s) rise."
    entries = [{"publication": "Desk note [Oct]", "url": "https://ex.com/a?x=1&y=2",
                "meta": "Publisher · 1 Oct 2026", "scan_url": "https://ex.com/scan",
                "summary": raw, "line": None},
               {"publication": "Listed paper", "url": None, "meta": None,
                "summary": None, "line": "one stored line"}]
    s = _sec("reading", "deep", subs=[{"title": "Desks", "entries": entries}],
             period="month", claim="Two shelf editions this month.")
    h = sr.section_html(s, 9, {}, "email", "monthly")
    check('<a href="https://ex.com/a?x=1&amp;y=2"' in h
          and "Desk note [Oct]</a></strong>" in h
          and f'<p style="{sr.PARA}">{sr.esc(raw)}</p>' in h,
          "the title line is hyperlinked and the summary prints HTML-escaped and "
          "otherwise exactly as stored")
    check("<strong>Listed paper</strong>" in h and " — one stored line" in h
          and h.index("Desks") < h.index("Desk note"),
          "a list item without a URL prints its name unlinked, its line on the "
          "title line, under its sub-section's heading")
    ed = {"sections": [s], "session": "2026-10-01", "detail": []}
    rd.polish_edition(ed)
    check(entries[0]["summary"] == raw and entries[1]["line"] == "one stored line",
          "the formatting pass never touches a stored summary (no date rewrite, "
          "no (s) plural, no minus sign)")
    ed2 = {"sections": [dict(s, paragraphs=["word " * 50])], "detail": []}
    before = stack_mod.edition_words(ed2)
    stored = len(raw.split()) + 3
    check(rd.stored_words(ed2) == stored
          and before == stack_mod.edition_words({"sections": [dict(
              s, paragraphs=["word " * 50], subsections=[])], "detail": []}),
          f"stored text counts in stored_words ({rd.stored_words(ed2)}) and never "
          f"in the prose words")
    import math
    check(rd.reading_minutes(ed2, 0) == max(1, math.ceil(
        (before + stored) / rd.WORDS_PER_MINUTE)),
          "the reading time counts the stored words")
    stack_mod.trim_to_budget(ed2, 1)
    check(ed2["sections"][0]["subsections"][0]["entries"][0]["summary"] == raw,
          "the budget cut never trims a stored summary")
    md = sr.markdown({"sections": [s], "detail": []}, "monthly", "Monthly — x")
    check("**[Desk note (Oct)](https://ex.com/a?x=1&y=2)** — Publisher · 1 Oct 2026"
          in md and f"\n{raw}\n" in md,
          "the Markdown carries the linked title line and the summary verbatim")
    check(sr.entries_html({}) == "" and sr.md_entries({}) == [],
          "a block without entries prints nothing for them")


def group_l() -> None:
    print(f"\n{LINE}\nL. CHARTS UNDER SUB-SECTIONS; THE PAGE AND ITS MARKDOWN (T2.7)\n{LINE}")
    from daily_cascade import cadence as cadence_mod
    from daily_cascade import stack_render as sr
    check([cadence_mod.get(c).get("subsection_charts") for c in cadence_mod.NAMES]
          == [False, False, True],
          "config: only the Monthly's sub-sections carry their own charts")
    charts = {"M6": _chart("M6", "CFTC z-scores"), "M1": _chart("M1", "SPY weekly"),
              "M9": {"id": "M9", "unavailable": "no NAV stored"}}
    subs = [{"title": "Futures", "table": {"columns": ["C", "Z"], "rows": [["ES", "1.2"]]},
             "charts_rendered": ["M6"], "paragraphs": ["Futures paragraph."],
             "notes": ["A sub-section note."]},
            {"title": "Book", "lines": ["a line"], "charts_rendered": ["M9"]}]
    s = _sec(paragraphs=["Section paragraph."], subs=subs, period="month",
             claim="The claim.", charts_rendered=["M1"])
    m = sr.section_html(s, 6, charts, "email", "monthly")
    check(m.index("Futures") < m.index("cid:m6@chester") < m.index("Futures paragraph.")
          < m.index("A sub-section note.") < m.index("Book")
          < m.index("Chart unavailable: no NAV stored") < m.index("cid:m1@chester")
          < m.index("Section paragraph."),
          "at 'monthly' a sub-section's chart prints under it, before its "
          "paragraphs and its notes; the section's own chart after the sub-sections")
    s["period"] = "week"
    w = sr.section_html(s, 6, charts, "email", "weekly")
    check(w.index("cid:m1@chester") < w.index("cid:m6@chester")
          and w.index("Book") < w.index("cid:m1@chester")
          and "A sub-section note." not in w,
          "at 'weekly' every chart prints at section level, the section's first "
          "(unchanged)")
    s["period"] = "month"
    a = sr.section_html(s, 6, charts, "archive", "monthly")
    check('src="m6.svg"' in a and "cid:" not in a,
          "the archive edition references each SVG by file name")
    ed = {"sections": [s], "detail": [{"title": "The regime", "lines": ["x"],
                                       "subsections": [{"title": "Appendix",
                                                        "paragraphs": ["App para."]}]}],
          "as_of": "2026-10-01T20:00:00+00:00", "session": "2026-09-30",
          "changed_since": ["one change"], "reading_target_minutes": 40,
          "reading_minutes": 7, "config_version": "v1", "words": 10,
          "chart_count": 2, "run_id": "r1", "prior_session": "2026-09-01"}
    p = sr.page_html(ed, "monthly", "Monthly — September 2026", "email", charts,
                     "Changed since last Monthly", "Monthly")
    check("Monthly — September 2026</h1>" in p and "about 7 minutes to read" in p
          and "target 40 minutes" in p and "Changed since last Monthly" in p
          and p.index("Section paragraph.") < p.index("Detail tables")
          < p.index("App para.") < p.index("Glossary")
          and "since the Monthly of" in p,
          "page_html: the header with reading time and target, the sections, the "
          "detail tables, the glossary, the footer naming the prior Monthly")
    md = sr.markdown(ed, "monthly", "Monthly — September 2026",
                     "Changed since last Monthly", "Monthly", charts=charts)
    check(md.index("### Futures") < md.index("![CFTC z-scores](m6.svg)")
          < md.index("Futures paragraph.") < md.index("*Chart unavailable: no NAV stored*")
          < md.index("![SPY weekly](m1.svg)") < md.index("Section paragraph.")
          < md.index("## Detail tables") < md.index("#### Appendix"),
          "the Markdown: each chart's line where the HTML places it, sub-section "
          "and section, then the detail tables")
    check("about 7 minutes to read · target 40 minutes" in md
          and "since the Monthly of" in md,
          "and the Markdown's header and footer say what the page's do")


def group_m() -> None:
    print(f"\n{LINE}\nM. THE BUDGET CUT (T2.7)\n{LINE}")
    from daily_cascade import cadence as cadence_mod
    from daily_cascade import stack as stack_mod
    check([cadence_mod.get(c).get("trim_to_budget") for c in cadence_mod.NAMES]
          == [False, False, True],
          "config: only the Monthly trims to its budget; the close and the Weekly "
          "fit by construction")
    para = "word " * 100
    ed = {"sections": [
        {"id": "a", "claim": "Claim a.", "paragraphs": [para, para], "trimmed": False,
         "items": [{"text": "item"}],
         "subsections": [{"title": "s", "paragraphs": [para]}]},
        {"id": "b", "claim": "Claim b.", "paragraphs": [para], "trimmed": False,
         "subsections": []}],
        "detail": [{"title": "Appendix", "trimmed": False,
                    "subsections": [{"title": "p", "paragraphs": [para, para]}]}]}
    stack_mod.trim_to_budget(ed, 350)
    a, b = ed["sections"]
    check(ed["detail"][0]["subsections"][0]["paragraphs"] == []
          and ed["detail"][0]["trimmed"],
          "the appendix's paragraphs go first")
    check(len(a["paragraphs"]) == 1 and a["trimmed"] and b["paragraphs"] == [para]
          and stack_mod.edition_words(ed) <= 350,
          f"then the last paragraph of a block that keeps several, until it fits "
          f"({stack_mod.edition_words(ed)} words)")
    check(a["claim"] == "Claim a." and a["items"] == [{"text": "item"}],
          "a claim and an item are never cut")
    w = {"sections": [{"id": "x", "claim": "c", "paragraphs": [para] * 5,
                       "subsections": [], "trimmed": False}], "detail": []}
    stack_mod.trim_to_budget(w, 0)
    check(len(w["sections"][0]["paragraphs"]) == 5,
          "no budget, no cut")


def group_n() -> None:
    print(f"\n{LINE}\nN. A SECTION AT ONE CADENCE ONLY (T2.7)\n{LINE}")
    from daily_cascade import stack as stack_mod
    cfg = stack_mod.config()
    specs = {s["id"]: s for s in cfg["sections"]}
    check("reading" in specs and specs["reading"].get("monthly")
          and not specs["reading"].get("weekly") and not specs["reading"].get("daily"),
          "config declares the Reading chapter at the Monthly's depth only")
    check(cfg.get("monthly_slow_triple", {}).get("percentile_window_days") == 1825
          and cfg.get("monthly_reading", {}).get("repo_blob_url", "").startswith("https://"),
          "B's monthly_slow_triple and monthly_reading keys are in config")
    ten = list(stack_mod.SECTION_ORDER)
    check(stack_mod.section_ids(cfg, "daily", {}) == ten
          and stack_mod.section_ids(cfg, "weekly", {}) == ten
          and stack_mod.section_ids(cfg, "monthly", {}) == ten,
          "the close, the Weekly and an unbuilt Reading lay out the ten")
    got = stack_mod.section_ids(cfg, "monthly", {"reading": {}})
    check(got == ten[:8] + ["reading"] + ten[8:],
          "a built Reading is laid out in its config place, after Narratives")
    built = {sid: {"items": [stack_mod.item(f"{sid}:x", f"{sid} fact")]} for sid in ten}
    secs = stack_mod.assemble(built, cfg, None, "weekly")
    check([s["id"] for s in secs] == ten,
          "assemble at 'weekly' over the ten: no KeyError for a Monthly-only section")
    bad = {"sections": [s for s in cfg["sections"] if s["id"] != "tape"]}
    try:
        stack_mod.section_ids(bad, "weekly", {})
        raised = False
    except KeyError:
        raised = True
    check(raised, "one of the ten missing from config is a code fault")


def group_o() -> None:
    print(f"\n{LINE}\nO. DATED TICKS NEVER OVERLAP AT THE END (T2.7)\n{LINE}")
    from daily_cascade import charts
    old = lambda n, k: sorted({0, n - 1} | set(range(0, n, max(1, n // k))))  # noqa: E731
    check(old(22, 4)[-2:] == [20, 21] and charts.dated_tick_index(22, 4) == [0, 5, 10, 15, 21],
          f"22 points, 4 ticks: the spaced tick one point before the last is "
          f"dropped ({old(22, 4)} -> {charts.dated_tick_index(22, 4)})")
    ok = True
    for n in range(1, 300):
        for k in (2, 3, 4, 5):
            idx = charts.dated_tick_index(n, k)
            step = max(1, n // k)
            ok &= idx[0] == 0 and idx[-1] == n - 1 and idx == sorted(set(idx))
            ok &= all(b - a >= step / 2 for a, b in zip(idx, idx[1:])) or n <= 2
    check(ok, "for every length and tick count: first and last always, no two "
              "ticks within half a step")

    class Ax:
        def set_xticks(self, i):
            self.i = i

        def set_xticklabels(self, labels):
            self.labels = labels
    ax = Ax()
    charts._dated_ticks(ax, [f"2026-09-{d:02d}" for d in range(1, 23)])
    check(ax.i == [0, 5, 10, 15, 21] and ax.labels[-1] == "26-09-22",
          "_dated_ticks (the Weekly's) uses it")


def group_p() -> None:
    print(f"\n{LINE}\nP. THE NAMES B IMPORTS STAY (T2.7)\n{LINE}")
    from daily_cascade import charts, deliver, stack_render, weekly_stack
    names = ("_base", "_levels_of", "span_title", "z_panel", "caption", "_candles",
             "_draw_levels", "_finish", "_plt", "_untracked", "lines_chart",
             "weekly_bars", "CHART_W", "DOWN", "LEVEL_COLOURS", "MAX_PNG_BYTES",
             "MIN_PX_AT_400")
    gone = [n for n in names if not hasattr(charts, n)]
    check(not gone, f"daily_cascade.charts keeps {', '.join(names)} ({gone or 'all'})")
    check(len(weekly_stack.CFTC_CONTRACTS) >= 2
          and all(len(x) == 2 for x in weekly_stack.CFTC_CONTRACTS),
          "weekly_stack.CFTC_CONTRACTS stays (instrument, label) pairs")
    check(stack_render.cid("M6") == "m6@chester" and callable(deliver.send_html),
          "stack_render.cid and deliver.send_html stay")
    for n in ("page_html", "markdown", "section_html", "subsection_html",
              "details_html", "entries_html", "charts_html", "md_block", "md_table"):
        check(callable(getattr(stack_render, n, None)), f"stack_render.{n}")


def main() -> int:
    print(f"{LINE}\nT2.6 -- the stack's cadences, the close's detail tables, and the "
          f"week's small items\n{LINE}")
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g,
              group_h, group_glossary, group_k, group_l, group_m, group_n,
              group_o, group_p, group_i):
        try:
            g()
        except Exception as exc:                                # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
