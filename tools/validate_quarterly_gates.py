"""
AQ-10: the Quarterly's validators (change order of 10 Oct 2026, section 11 row
AQ-10; sections 3, 4.1, 5, 6, 9, 4.10 and 4.11).

Five gates, each a set of rules written once as functions over an edition (or a
ledger's rows) that return the faults they find. Every rule is shown both ways
on a synthetic fixture -- one that passes and one that fails for that rule --
and then the five gates are run over the Quarterly's own dry run on the Monthly
stack gate's synthetic store (the fixture validate_quarterly_stack.py seeds).
Fixtures only; it never reads the live store.

  1 STACK      every front-matter section and every chapter item renders or
               prints its not-yet reason; the chart cap (40) holds, and a chart
               over it is named on the page, never dropped silently; the read's
               time is computed (250 words a minute, 20 seconds a drawn lead
               chart -- the Monthly's rule), printed, and warned on over 90
               minutes; the reference is unbudgeted.
  2 THESES     every alt_asset ledger entry has a family, a horizon, a
               measurable, a grade date and a Brier slot; no entry, and no
               measurable's series, is trigger_eligible; before Doctrine #2 the
               seed and graded views print "not yet" cleanly.
  3 CORR       the correlation item's rows name registered keys; the former
               report's 30-day against 120-day break prints its state; a shift
               flag never fires without both windows (60 and 252 days) present.
  4 KILL       every section 5 analysis a chapter lists prints its kill state
               (holds / strained / killed / not measured -- <reason>) beside its
               reading; an analysis with no kill condition in config fails.
  5 DRAFTS     at most one draft per family per horizon; every draft carries
               the cost row and the portfolio role; the no-draft line prints
               where a horizon has none; Thailand prints no draft ever;
               agriculture's thin or poorly understood contracts print no draft.

THE HOOKS. AQ-5 (altdata.correlation), AQ-6 (altdata.thesis_register), AQ-8a
(altdata.attribution, altdata.paper_bid) and c1-move-screen (altdata.move_screen)
are other branches. Where a gate needs their code it is shown against a fixture
module built from their documented outputs (their notes files); the checks that
run their REAL code are marked "activates when <branch> merges" and print SKIP
until the module is importable.

    python tools/validate_quarterly_gates.py
"""

from __future__ import annotations

import copy
import datetime as dt
import importlib
import json
import math
import os
import re
import sqlite3
import sys
import types
from pathlib import Path
from typing import Optional

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

# The Quarterly stack gate's fixture (and through it the Monthly's): importing it
# points every store at its own temporary directory before anything opens one.
import validate_quarterly_stack as vqs                         # noqa: E402
import gate_tmp                                                # noqa: E402

vms = vqs.vms

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LINE = "=" * 78
PASS = FAIL = SKIP = 0
COUNTS: dict = {}
GATE = ["-"]


def check(c, m: str) -> None:
    global PASS, FAIL
    COUNTS.setdefault(GATE[0], [0, 0, 0])
    if c:
        PASS += 1
        COUNTS[GATE[0]][0] += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        COUNTS[GATE[0]][1] += 1
        print(f"  FAIL  {m}")


def skip(branch: str, m: str) -> None:
    global SKIP
    COUNTS.setdefault(GATE[0], [0, 0, 0])
    SKIP += 1
    COUNTS[GATE[0]][2] += 1
    print(f"  SKIP  {m} -- activates when {branch} merges")


def head(n: str, title: str) -> None:
    GATE[0] = n
    print(f"\n{LINE}\n{n}. {title}\n{LINE}")


def present(mod: str):
    try:
        return importlib.import_module(mod)
    except ImportError:
        return None


def fails_on(faults: list[str], tag: str) -> bool:
    """The fixture fails, and for THIS rule (each fault names its rule)."""
    return any(f.startswith(tag) for f in faults)


# ===========================================================================
# GATE 1 -- THE QUARTERLY STACK
# ===========================================================================
CONTENT_FIELDS = ("claim", "paragraphs", "paragraph", "items", "table", "tables",
                  "lines", "charts_rendered", "not_tracked", "notes", "phase_a")
OVER_CAP = "over the edition's chart cap"


def has_content(x: dict) -> bool:
    if any(x.get(k) for k in CONTENT_FIELDS):
        return True
    return any(has_content(ss) for ss in x.get("subsections") or []
               if not ss.get("divider"))


def render_faults(ed: dict) -> list[str]:
    """[render] every front-matter section and every chapter item renders, or
    prints its not-yet reason -- never a blank."""
    out = []
    for s in ed.get("sections") or []:
        if s.get("chapter"):
            for ss in s.get("subsections") or []:
                if not ss.get("divider") and not has_content(ss):
                    out.append(f"render: {s['id']}:{ss.get('item') or ss.get('title')} "
                               f"is blank")
        elif not has_content(s):
            out.append(f"render: front matter {s['id']} is blank")
    return out


def cap_faults(ed: dict, charts: dict, markdown: str, html: str,
               cap: int) -> list[str]:
    """[cap] at most `cap` charts drawn; every chart a section names exists
    (none dropped silently); a chart over the cap is listed in
    charts_over_cap and named on the page in its place."""
    out = []
    drawn = [k for k, c in charts.items() if not c.get("unavailable")]
    if len(drawn) > cap:
        out.append(f"cap: {len(drawn)} charts drawn against a cap of {cap}")
    named = set()
    for s in ed.get("sections") or []:
        named |= set(s.get("charts_rendered") or [])
        for ss in s.get("subsections") or []:
            named |= set(ss.get("charts_rendered") or [])
    gone = sorted(named - set(charts))
    if gone:
        out.append(f"cap: dropped silently -- {gone[:4]} named by a section, absent "
                   f"from the edition's charts")
    over = [k for k, c in charts.items()
            if str(c.get("unavailable") or "").startswith(OVER_CAP)]
    if sorted(over) != sorted(ed.get("charts_over_cap") or []):
        out.append(f"cap: charts_over_cap {sorted(ed.get('charts_over_cap') or [])} "
                   f"is not the charts held over the cap {sorted(over)}")
    for k in over:
        c = charts[k]
        name = c.get("caption") or c.get("title")
        msg = str(c["unavailable"])
        if not name or name not in msg:
            out.append(f"cap: {k} is held over the cap without its name")
        elif msg not in markdown or msg not in html.replace("&#x27;", "'") \
                .replace("&amp;", "&"):
            out.append(f"cap: {k}'s over-cap line is not on the page")
    return out


def read_faults(ed: dict, markdown: str, html: str, q, target: int) -> list[str]:
    """[read] the read's time is the summary's and the lead items' prose at the
    house rate plus 20 seconds a drawn lead chart, printed in the header beside
    the whole edition's; over the target it is warned on and nothing is cut."""
    out = []
    got = q.read_minutes(ed)
    if ed.get("read_minutes") != got:
        out.append(f"read: the edition says {ed.get('read_minutes')} min, the rule "
                   f"computes {got}")
    if ed.get("reading_target_minutes") != target:
        out.append(f"read: the target is {ed.get('reading_target_minutes')}, not {target}")
    line = (f"the read: {ed.get('read_minutes')} min; the whole edition: "
            f"{ed.get('reading_minutes')} min")
    if line not in markdown or line not in html:
        out.append("read: the header does not print the read's time")
    if (ed.get("read_minutes") or 0) > target and not ed.get("read_warning"):
        out.append(f"read: {ed.get('read_minutes')} min over a {target}-minute target, "
                   f"and no warning")
    for c in ed.get("sections") or []:
        for ss in c.get("subsections") or []:
            if ss.get("tier") == "lead" and ss.get("trimmed"):
                out.append(f"read: {c['id']}:{ss.get('item')} was cut")
    return out


def reference_faults(ed: dict, cad: dict, q) -> list[str]:
    """[reference] the reference tier has no budget: none in config, nothing
    trimmed, and its words never reach the read's time."""
    out = []
    if (cad.get("reference_budget") or {}).get("words") is not None \
            or cad.get("trim_to_budget") is not False:
        out.append("reference: the cadence budgets or trims the reference")
    for s in ed.get("sections") or []:
        if s.get("tier") == "reference" and s.get("trimmed"):
            out.append(f"reference: front matter {s['id']} was trimmed")
        for ss in s.get("subsections") or []:
            if ss.get("tier") == "reference" and ss.get("trimmed"):
                out.append(f"reference: {s['id']}:{ss.get('item')} was trimmed")
    bare = copy.deepcopy(ed)
    for s in bare.get("sections") or []:
        for ss in s.get("subsections") or []:
            if ss.get("tier") == "reference":
                ss["paragraphs"] = ["word " * 5000]
    if q.read_minutes(bare) != q.read_minutes(ed):
        out.append("reference: the reference's words move the read's time")
    return out


def stack_faults(ed, charts, md, html, q, cad) -> list[str]:
    return (render_faults(ed) + cap_faults(ed, charts, md, html,
                                           int(cad["budget"]["charts"]))
            + read_faults(ed, md, html, q, int(cad["reading_target_minutes"]))
            + reference_faults(ed, cad, q))


def fixture_edition(q, cap: int = 40) -> tuple[dict, dict, str, str]:
    """A small Quarterly: the read, one reference front-matter section, one
    chapter (lead, divider, reference), cap + 1 charts of which one is held
    over the cap; its Markdown and HTML as the renderer prints the lines the
    gate reads."""
    charts = {f"Q{i}": {"id": f"Q{i}", "caption": f"Chart {i}"} for i in range(cap + 1)}
    ed = {"reading_target_minutes": 90, "budget": {"charts": cap},
          "summary": [{"id": "metals", "text": "word " * 200}],
          "sections": [
              {"id": "read", "tier": "lead", "paragraphs": ["word " * 300],
               "charts_rendered": ["Q0"]},
              {"id": "tape", "tier": "reference", "not_tracked": ["not yet — AQ-4"]},
              {"id": "metals", "chapter": True, "tier": "chapter", "subsections": [
                  {"item": "quarter", "tier": "lead", "paragraphs": ["word " * 400],
                   "charts_rendered": [f"Q{i}" for i in range(1, 4)]},
                  {"divider": "The reference", "tier": "reference"},
                  {"item": "structure", "tier": "reference",
                   "paragraphs": ["word " * 2000],
                   "charts_rendered": [f"Q{i}" for i in range(4, cap + 1)]}]}]}
    over = q.hold_cap(ed, charts, cap)
    ed["charts_over_cap"] = over
    ed["read_minutes"] = q.read_minutes(ed)
    ed["reading_minutes"] = ed["read_minutes"] + 9
    ed["read_warning"] = q.read_warning(ed)
    hdr = (f"the read: {ed['read_minutes']} min; the whole edition: "
           f"{ed['reading_minutes']} min")
    unav = " ".join(f"Chart unavailable: {charts[k]['unavailable']}" for k in over)
    md = f"{hdr} (target 90 minutes for the read)\n{unav}\n"
    return ed, charts, md, md


def gate_1(r: dict) -> None:
    from daily_cascade import cadence
    from monthly_macro import quarterly as q
    head("1", "THE QUARTERLY STACK GATE")
    cad = cadence.get("quarterly")
    check(cad["budget"]["charts"] == 40 and cad["reading_target_minutes"] == 90
          and (cad.get("reference_budget") or {}).get("words") is None
          and cad.get("trim_to_budget") is False,
          "the cadence: chart cap 40, the read at 90 minutes, the reference "
          "unbudgeted and never trimmed")
    ed, charts, md, html = fixture_edition(q)
    check(not stack_faults(ed, charts, md, html, q, cad),
          f"the passing fixture: {len(charts)} charts, one held over the cap and "
          f"named; the read {ed['read_minutes']} min ({stack_faults(ed, charts, md, html, q, cad)[:2]})")
    check(ed["charts_over_cap"] == ["Q40"] and "Chart 40" in charts["Q40"]["unavailable"],
          f"hold_cap names the chart it holds: \"{charts['Q40']['unavailable']}\"")

    # -- render ---------------------------------------------------------------
    e2 = copy.deepcopy(ed)
    e2["sections"][1] = {"id": "tape", "tier": "reference"}
    check(fails_on(render_faults(e2), "render: front matter tape"),
          "render fails: a front-matter section with neither content nor a reason")
    e2 = copy.deepcopy(ed)
    e2["sections"][2]["subsections"][2] = {"item": "structure", "tier": "reference"}
    check(fails_on(render_faults(e2), "render: metals:structure"),
          "render fails: a chapter item printed blank")
    # -- cap ------------------------------------------------------------------
    c2 = copy.deepcopy(charts)
    c2["Q40"] = {"id": "Q40", "caption": "Chart 40"}
    check(fails_on(cap_faults(ed, c2, md, html, 40), "cap: 41 charts drawn"),
          "cap fails: 41 charts drawn against 40")
    c2 = copy.deepcopy(charts)
    del c2["Q40"]
    check(fails_on(cap_faults(ed, c2, md, html, 40), "cap: dropped silently"),
          "cap fails: a chart a section names is missing from the edition -- "
          "dropped silently")
    c2 = copy.deepcopy(charts)
    c2["Q40"] = {"id": "Q40", "unavailable": f"{OVER_CAP} (40)"}
    check(fails_on(cap_faults(ed, c2, md, html, 40), "cap: Q40 is held over the cap "
                                                     "without its name"),
          "cap fails: a chart held over the cap with no name (the AQ-1 form)")
    check(fails_on(cap_faults(ed, charts, "", "", 40), "cap: Q40's over-cap line"),
          "cap fails: the over-cap line is not on the page")
    e2 = copy.deepcopy(ed)
    e2["charts_over_cap"] = []
    check(fails_on(cap_faults(e2, charts, md, html, 40), "cap: charts_over_cap"),
          "cap fails: a chart held over the cap and not listed in charts_over_cap")
    # -- read -----------------------------------------------------------------
    e2 = copy.deepcopy(ed)
    e2["read_minutes"] += 3
    check(fails_on(read_faults(e2, md, html, q, 90), "read: the edition says"),
          "read fails: a read time the rule does not compute")
    check(fails_on(read_faults(ed, "", "", q, 90), "read: the header"),
          "read fails: the header does not print it")
    e2 = copy.deepcopy(ed)
    e2["sections"][2]["subsections"][0]["paragraphs"] = ["word " * 25000]
    e2["read_minutes"] = q.read_minutes(e2)
    e2["read_warning"] = None
    md2 = (f"the read: {e2['read_minutes']} min; the whole edition: "
           f"{e2['reading_minutes']} min")
    check(e2["read_minutes"] > 90
          and fails_on(read_faults(e2, md2, md2, q, 90), "read: ")
          and any("no warning" in f for f in read_faults(e2, md2, md2, q, 90)),
          f"read fails: {e2['read_minutes']} min over the 90-minute target with no "
          f"warning")
    e2["read_warning"] = q.read_warning(e2)
    check(not read_faults(e2, md2, md2, q, 90) and "90-minute target" in e2["read_warning"],
          f"and passes warned, nothing cut ({e2['read_warning']})")
    e2 = copy.deepcopy(ed)
    e2["sections"][2]["subsections"][0]["trimmed"] = True
    check(fails_on(read_faults(e2, md, html, q, 90), "read: metals:quarter was cut"),
          "read fails: a lead item cut to fit")
    # -- reference ------------------------------------------------------------
    check(fails_on(reference_faults(ed, {**cad, "trim_to_budget": True}, q),
                   "reference: the cadence"),
          "reference fails: a cadence that trims the reference")
    e2 = copy.deepcopy(ed)
    e2["sections"][2]["subsections"][2]["trimmed"] = True
    check(fails_on(reference_faults(e2, cad, q), "reference: metals:structure"),
          "reference fails: a reference item trimmed")
    from daily_cascade import stack as stack_mod
    whole = types.SimpleNamespace(read_minutes=lambda e: max(1, math.ceil(sum(
        stack_mod.section_words(s) for s in e.get("sections") or []) / 250)))
    check(fails_on(reference_faults(ed, cad, whole), "reference: the reference's words"),
          "reference fails: a read rule that counts the reference's words")

    # -- the dry run ----------------------------------------------------------
    f = stack_faults(r["ed"], r["out"]["charts"], r["out"]["markdown"],
                     r["out"]["html_email"], q, cad)
    check(not f, f"the Quarterly's dry run passes the stack gate: {len(r['ed']['sections'])} "
                 f"sections, {r['ed']['chart_count']} charts against 40, the read "
                 f"{r['ed']['read_minutes']} min of {r['ed']['reading_minutes']} ({f[:3]})")
    print(f"        the read: {r['ed']['read_minutes']} min against the 90-minute "
          f"target; the whole edition {r['ed']['reading_minutes']} min")


# ===========================================================================
# GATE 2 -- THE THESIS REGISTER
# ===========================================================================
# AQ-6's documented families (thesis_register.FAMILIES) and horizons.
FAMILIES = ("metals", "oil", "currency", "em", "china", "crypto", "real_estate",
            "credit", "intl_equities", "thailand", "agriculture")
HORIZONS = ("3m", "12m")
COMPARATORS = (">=", ">", "<=", "<", "between")


def ledger_faults(rows: list[dict], registry) -> list[str]:
    """Every alt_asset ledger entry (AQ-6's theses(): the ledger's row joined to
    alt_asset_theses) has a family, a horizon, a measurable, a grade date and a
    Brier slot; neither it nor its measurable's series is trigger_eligible."""
    out = []
    for r in rows:
        pid = str(r.get("probability_id") or "?")[:8]
        if r.get("family") not in FAMILIES:
            out.append(f"family: {pid} has family {r.get('family')!r}")
        if r.get("horizon_kind") not in HORIZONS:
            out.append(f"horizon: {pid} has horizon {r.get('horizon_kind')!r}")
        m = r.get("measurable")
        if not (isinstance(m, dict) and m.get("series") and m.get("comparator")
                in COMPARATORS and m.get("level") is not None and m.get("date")):
            out.append(f"measurable: {pid} has no measurable "
                       f"{{series, comparator, level, date}}")
        try:
            dt.date.fromisoformat(str(r.get("horizon_date"))[:10])
        except ValueError:
            out.append(f"grade date: {pid} has no grade date")
        if "brier" not in r:
            out.append(f"brier: {pid} has no Brier slot")
        elif r["brier"] is not None and not 0.0 <= float(r["brier"]) <= 1.0:
            out.append(f"brier: {pid} Brier {r['brier']} outside [0, 1]")
        if r.get("trigger_eligible"):
            out.append(f"trigger: {pid} is trigger_eligible")
        if isinstance(m, dict) and m.get("series"):
            e = registry(m["series"]) or {}
            if e.get("trigger_eligible"):
                out.append(f"trigger: {pid}'s series {m['series']} is trigger_eligible")
    return out


NOT_YET_RE = re.compile(r"not yet|no .*theses.* yet|no theses .* to grade", re.I)
UNCLEAN = ("FAULT", "Traceback", "None", "nan", "{", "}")


def not_yet_faults(sub: dict, item: str) -> list[str]:
    """[not yet] before Doctrine #2 an item reading the ledger prints its
    not-yet line cleanly: no rows, one plain line, no fault, no None."""
    out = []
    t = sub.get("table") or {}
    if t.get("rows"):
        out.append(f"not yet: {item} prints {len(t['rows'])} rows with nothing seeded")
    text = " ".join(list(sub.get("lines") or []) + list(sub.get("not_tracked") or [])
                    + list(sub.get("notes") or []))
    if not NOT_YET_RE.search(text):
        out.append(f"not yet: {item} does not say \"not yet\" ({text[:60]!r})")
    bad = [u for u in UNCLEAN if u in text]
    if bad:
        out.append(f"not yet: {item} is not clean ({bad})")
    return out


def seed_line_faults(t: dict) -> list[str]:
    """[seed] AQ-6's seed_table with an empty ledger: no rows and the "no
    theses ... yet" line."""
    out = []
    if t.get("rows"):
        out.append(f"seed: {len(t['rows'])} rows from an empty ledger")
    line = str(t.get("line") or "")
    if not re.search(r"holds no theses for \dQ\d\d yet", line):
        out.append(f"seed: the line does not say not yet ({line[:60]!r})")
    if any(u in line for u in UNCLEAN):
        out.append("seed: the line is not clean")
    return out


def ledger_row(**over) -> dict:
    """One row as AQ-6's theses() returns it (its notes: the ledger's row joined
    to alt_asset_theses, the measurable parsed)."""
    r = {"probability_id": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6", "source": "alt_asset:metals",
         "scenario_set": "metals-2027q1-3m", "claim": "GLD closes 1Q27 above 360",
         "probability": 0.6, "emitted_at": "2026-11-07T15:00:00+00:00",
         "horizon_date": "2027-03-31", "resolution_criterion": "yfinance.mkt_gld > 360",
         "resolved_at": None, "outcome": None, "brier": None, "emitted_by": "operator",
         "family": "metals", "quarter": "2027q1", "horizon_kind": "3m",
         "label": "GLD closes 1Q27 above 360",
         "measurable": {"series": "yfinance.mkt_gld", "comparator": ">", "level": 360,
                        "date": "2027-03-31"},
         "falsifier": {"series": "yfinance.mkt_gld", "comparator": "<", "level": 320,
                       "date": "2027-02-26"}}
    r.update(over)
    return r


def gate_2(r: dict) -> None:
    from altdata import derived
    from monthly_macro import quarterly as q
    head("2", "THE THESIS-REGISTER GATE")
    reg = derived.registry_entry
    good = [ledger_row(), ledger_row(probability_id="b" * 32, horizon_kind="12m",
                                     scenario_set="metals-2027q1-12m", probability=0.45,
                                     horizon_date="2027-12-31", brier=0.3025,
                                     measurable={"series": "yfinance.mkt_gld",
                                                 "comparator": "between",
                                                 "level": [330, 400],
                                                 "date": "2027-12-31"})]
    check(not ledger_faults(good, reg),
          f"the passing fixture: a 3-month thesis (Brier pending) and a graded "
          f"12-month weight, in AQ-6's row shape ({ledger_faults(good, reg)[:2]})")
    cases = [
        ("family", {"family": None}, "an entry with no family"),
        ("family", {"family": "oil_energy"}, "an entry under the chapter's id, not "
                                             "the register's family (oil)"),
        ("horizon", {"horizon_kind": "6m"}, "a horizon that is neither 3m nor 12m"),
        ("measurable", {"measurable": "GLD goes up"}, "a prose measurable"),
        ("measurable", {"measurable": {"series": "yfinance.mkt_gld", "comparator": "~",
                                       "level": 1, "date": "2027-03-31"}},
         "a comparator outside >= > <= < between"),
        ("grade date", {"horizon_date": None}, "an entry with no grade date"),
        ("brier", {"brier": 1.7}, "a Brier outside [0, 1]"),
        ("trigger", {"trigger_eligible": True}, "an entry marked trigger_eligible"),
    ]
    for tag, over, why in cases:
        check(fails_on(ledger_faults([ledger_row(**over)], reg), f"{tag}:"),
              f"{tag} fails: {why}")
    nob = ledger_row()
    del nob["brier"]
    check(fails_on(ledger_faults([nob], reg), "brier:"),
          "brier fails: an entry with no Brier slot")
    fake_reg = lambda k: {"key": k, "trigger_eligible": True}       # noqa: E731
    check(fails_on(ledger_faults([ledger_row()], fake_reg), "trigger:"),
          "trigger fails: a measurable on a trigger-eligible series")
    allreg = derived._load_registry()
    hot = sorted(k for k, v in allreg.items() if (v or {}).get("trigger_eligible"))
    check(not hot, f"and no registry key is trigger-eligible, so no measurable can "
                   f"name one ({hot[:3]})")

    # -- before Doctrine #2: "not yet", cleanly ------------------------------
    for item, sub in (("graded", {"not_tracked": [q.NOT_YET["thesis"]]}),
                      ("theses", {"lines": ["The ledger holds no 1Q27 theses for this "
                                            "chapter yet."]}),
                      ("graded", {"lines": ["The ledger holds no theses for 4Q26 to "
                                            "grade."]})):
        check(not not_yet_faults(sub, item),
              f"not yet passes: {item} -- \"{(sub.get('lines') or sub.get('not_tracked'))[0]}\"")
    check(fails_on(not_yet_faults({"lines": ["The ledger holds no theses."],
                                   "table": {"rows": [["metals", "3-month", "x", "0.60",
                                                       "2027-03-31", "pending"]]}},
                                  "theses"), "not yet: theses prints 1 rows"),
          "not yet fails: rows printed with nothing seeded")
    check(fails_on(not_yet_faults({"lines": ["Theses: None"]}, "theses"),
                   "not yet: theses does not say"),
          "not yet fails: a line that does not say not yet")
    check(fails_on(not_yet_faults({"notes": ["FAULT (code, not data) -- the thesis "
                                             "register: not yet"]}, "graded"),
                   "not yet: graded is not clean"),
          "not yet fails: a fault where the not-yet line belongs")
    empty_seed = {"quarter": "2027q1", "label": "1Q27", "columns": [], "rows": [],
                  "line": "The ledger holds no theses for 1Q27 yet; the set is the "
                          "operator's, seeded from config/alt_asset_theses/2027q1.yaml.",
                  "count": 0, "weights": 0}
    check(not seed_line_faults(empty_seed),
          "seed passes: AQ-6's documented empty-ledger line")
    check(fails_on(seed_line_faults({**empty_seed, "line": "The ledger holds 0 theses "
                                     "for 1Q27; 0 twelve-month scenario sets"}), "seed:"),
          "seed fails: a zero-count sentence where \"not yet\" belongs")

    # -- the dry run ---------------------------------------------------------
    bad = []
    for c in q.chapters(r["ed"]):
        by = {x.get("item"): x for x in c["subsections"]}
        for item in ("graded", "theses"):
            if item in by:
                bad += [f"{c['id']}: {x}" for x in not_yet_faults(by[item], item)]
    check(not bad, f"the dry run: every chapter's items 1 and 2 print \"not yet\" "
                   f"cleanly before Doctrine #2 ({bad[:2]})")

    # -- AQ-6's real code ----------------------------------------------------
    tr = present("altdata.thesis_register")
    if tr is None:
        skip("aq-6-thesis-register", "AQ-6's seed_table on an empty ledger prints "
                                     "\"not yet\"; its theses() rows pass the ledger rule")
        skip("aq-6-thesis-register", "AQ-6's family list is the gate's")
        return
    db = str(Path(gate_tmp.mkdtemp("aq10_tr_")) / "empty.db")
    sqlite3.connect(db).close()
    t = tr.seed_table("2026-12-01T12:00:00+00:00", db, quarter="2027q1")
    check(not seed_line_faults(t), f"AQ-6's seed_table on an empty ledger: "
                                   f"\"{t.get('line')}\"")
    check(tuple(tr.FAMILIES) == FAMILIES and tuple(tr.HORIZON_KINDS) == HORIZONS,
          "AQ-6's family list and horizons are the gate's")
    rows = tr.theses(vms.DB)
    check(not ledger_faults(rows, reg),
          f"every alt_asset entry the fixture store's ledger holds passes "
          f"({len(rows)} entries)")


# ===========================================================================
# GATE 3 -- THE CORRELATION BLOCK
# ===========================================================================
BREAK_HEAD = "30-day against 120-day break"
SHIFT_RE = re.compile(r"^Shift: .+ \(60d [+\-]\d\.\d\d against 252d [+\-]\d\.\d\d, .+\)\.$")


def corr_key_faults(sub: dict, registry) -> list[str]:
    """[keys] every row of the correlation item names its keys, and each key
    is registered."""
    out = []
    t = sub.get("table") or {}
    keyed = {x["row"]: x.get("keys") or [] for x in (sub.get("data") or {}).get("rows") or []}
    for row in t.get("rows") or []:
        ks = keyed.get(row[0])
        if not ks:
            out.append(f"keys: the row {row[0]!r} names no key")
            continue
        for k in ks:
            if not registry(k):
                out.append(f"keys: {row[0]!r} names {k}, which is not registered")
    return out


def break_faults(sub: dict, delta: float = 0.30) -> list[str]:
    """[break] where the chapter carries break assets the item prints the
    30-day against 120-day state; every break printed meets |delta| >= 0.30,
    its direction is its sign's, and it is on the page."""
    out = []
    d = sub.get("data") or {}
    if "break_assets" not in d:
        return out
    lines = [x for x in sub.get("lines") or [] if x.startswith(BREAK_HEAD)]
    if len(lines) != 1:
        out.append(f"break: {len(lines)} break-state lines, one wanted")
        return out
    for b in d.get("breaks") or []:
        v = float(b["delta"])
        if abs(v) < delta:
            out.append(f"break: {b['asset']} printed at {v:+.2f}, under {delta}")
        if b["direction"] != ("toward" if v > 0 else "away"):
            out.append(f"break: {b['asset']} {b['direction']} against a delta of {v:+.2f}")
        if f"({v:+.2f}, {b['day']})" not in lines[0]:
            out.append(f"break: {b['asset']} is not on the page")
    if not d.get("breaks") and d.get("break_assets") and "none fired" not in lines[0]:
        out.append("break: no break and no \"none fired\"")
    return out


def analysis_break_faults(text: str, delta: float = 0.30) -> list[str]:
    """[break] an item 6 break-logic row's state: "no break fired this quarter",
    "not yet: <branch>", or the breaks, each at |delta| >= 0.30."""
    if text == "no break fired this quarter" or text.startswith("not yet"):
        return []
    got = re.findall(r"(\w+) against (\w+) (toward|away) \(([+\-]\d+\.\d+), ", text)
    if not got:
        return [f"break: the state {text[:50]!r} is none of the three forms"]
    out = []
    for a, _, way, v in got:
        if abs(float(v)) < delta:
            out.append(f"break: {a} at {v}, under {delta}")
        if way != ("toward" if float(v) > 0 else "away"):
            out.append(f"break: {a} {way} at {v}")
    return out


def shift_faults(sub: dict) -> list[str]:
    """[shift] a shift never fires without both windows: every record carries a
    numeric 60-day and 252-day value, and every printed shift line shows both."""
    out = []
    for s in (sub.get("data") or {}).get("shifts") or []:
        for w in ("c60", "c252"):
            v = s.get(w)
            if not isinstance(v, (int, float)) or isinstance(v, bool) or math.isnan(v):
                out.append(f"shift: {'-'.join(s.get('pair') or [])} fired without its "
                           f"{w[1:]}-day window")
    for x in sub.get("lines") or []:
        if x.startswith("Shift:") and not SHIFT_RE.match(x):
            out.append(f"shift: the line {x[:50]!r} does not show both windows")
    return out


def fake_correlation(breaks=None, shifts=None, peers=None, named=None):
    """AQ-5's readers as its notes document them: peer_table rows, the named
    rows' triples, breaks_between / shifts_between records, shift_record."""
    co = types.ModuleType("aq10_fake_correlation")
    order = ["gold", "silver", "copper", "oil", "dxy", "spy", "tlt", "em", "china"]
    co.assets = lambda cfg=None: [{"id": x} for x in order]
    co.pair_key = lambda a, b, w: f"corr.{a}__{b}.{w}d"
    co.stored_key = lambda k, cfg=None: k
    co.pairs = lambda cfg=None: [(a, b) for i, a in enumerate(order) for b in order[i + 1:]]
    co.break_assets = lambda cfg=None: [x for x in order if x not in ("spy", "tlt")]
    co.label = lambda a, cfg=None: a.upper()
    co.peer_table = lambda st, now, cfg=None: peers if peers is not None else [
        {"asset": "gold", "peer": "dxy", "latest": -0.41, "median": -0.30,
         "divergence": -0.11, "as_of": "2026-09-30", "n": 900}]
    co.config = lambda: {"named": named if named is not None else [
        {"key": "corr.gold__spy.252d", "a": "gold", "b": "spy",
         "label": "Gold-SPY, one year"}]}
    co.triple = lambda st, key, now: {"latest": 0.2, "mean": 0.1, "percentile": 70.0,
                                      "as_of": "2026-09-30"}
    co.breaks_between = lambda st, start, now, cfg=None: list(breaks or [])
    co.shifts_between = lambda st, start, now, cfg=None, only=None: list(shifts or [])
    co.shift_record = lambda s: {"pair": list(s["pair"]), "day": s["day"],
                                 "rule": s["rule"], "c60": s["c60"], "c252": s["c252"]}
    return co


def corr_item(co, assets=("gold", "silver", "copper")) -> dict:
    from monthly_macro import quarterly as q
    saved = dict(q.HOOK_MODULES)
    sys.modules["aq10_fake_correlation"] = co
    q.HOOK_MODULES["correlation"] = "aq10_fake_correlation"
    try:
        return q.correlation_rows({"correlation_assets": list(assets)},
                                  {"store": object(), "now": vqs.AS_OF,
                                   "start": "2026-06-30"})
    finally:
        q.HOOK_MODULES.clear()
        q.HOOK_MODULES.update(saved)
        sys.modules.pop("aq10_fake_correlation", None)


def gate_3(r: dict) -> None:
    from monthly_macro import quarterly as q
    from monthly_macro import quarterly_items as qi
    head("3", "THE CORRELATION GATE")
    regd = {"corr.gold__dxy.60d", "corr.gold__spy.252d"}
    reg = lambda k: {"key": k} if k in regd else None             # noqa: E731
    brk = [{"asset": "gold", "benchmark": "spy", "delta": 0.36, "direction": "toward",
            "day": "2026-08-14"}]
    sh = [{"pair": ("gold", "dxy"), "day": "2026-09-02", "rule": "sign held",
           "c60": 0.12, "c252": -0.18, "gap": 0.30, "iqr": 0.2, "score": 1.5}]
    good = corr_item(fake_correlation(breaks=brk, shifts=sh))
    f = corr_key_faults(good, reg) + break_faults(good) + shift_faults(good)
    check(not f and good["table"]["rows"] and any(x.startswith(BREAK_HEAD)
                                                  for x in good["lines"])
          and any(x.startswith("Shift:") for x in good["lines"]),
          f"the passing fixture (AQ-5's documented records): two keyed rows, a break "
          f"at +0.36 and a sign-held shift with both windows ({f[:2]})")
    print("        " + " | ".join(good["lines"]))
    quiet = corr_item(fake_correlation(breaks=[], shifts=[]))
    check(not break_faults(quiet) and "none fired for GOLD, SILVER, COPPER" in
          " ".join(quiet["lines"]) and "No shift flag fired" in " ".join(quiet["lines"]),
          "a quiet quarter prints the break's state anyway: none fired, by asset")
    # -- keys -----------------------------------------------------------------
    check(fails_on(corr_key_faults(good, lambda k: None), "keys: "),
          "keys fail: a row naming an unregistered key")
    nokey = copy.deepcopy(good)
    nokey["data"]["rows"][0]["keys"] = []
    check(fails_on(corr_key_faults(nokey, reg), "keys: the row"),
          "keys fail: a row naming no key")
    # -- break ----------------------------------------------------------------
    weak = copy.deepcopy(good)
    weak["data"]["breaks"][0]["delta"] = 0.21
    check(fails_on(break_faults(weak), "break: gold printed at +0.21"),
          "break fails: a break printed under the 0.30 threshold")
    wrong = copy.deepcopy(good)
    wrong["data"]["breaks"][0]["direction"] = "away"
    check(fails_on(break_faults(wrong), "break: gold away"),
          "break fails: a positive delta called \"away\"")
    gone = copy.deepcopy(good)
    gone["lines"] = [x for x in gone["lines"] if not x.startswith(BREAK_HEAD)]
    check(fails_on(break_faults(gone), "break: 0 break-state lines"),
          "break fails: a chapter with break assets that prints no break state")
    check(not analysis_break_faults("no break fired this quarter")
          and not analysis_break_faults("not yet: aq-5-correlation-layer")
          and not analysis_break_faults("em against spy away (-0.42, 2026-09-03)"),
          "item 6's break-logic row: \"no break fired\", \"not yet: <branch>\", or "
          "the breaks at |delta| >= 0.30")
    check(fails_on(analysis_break_faults("em against spy away (-0.12, 2026-09-03)"),
                   "break: em at -0.12")
          and fails_on(analysis_break_faults("em against spy toward (-0.42, 2026-09-03)"),
                       "break: em toward")
          and fails_on(analysis_break_faults("computed"), "break: the state"),
          "and fails under the threshold, against its sign, or in no form at all")
    # -- shift ----------------------------------------------------------------
    for w, val in (("c252", None), ("c60", float("nan"))):
        s2 = [dict(sh[0], **{w: val})]
        bad = corr_item(fake_correlation(breaks=brk, shifts=s2))
        check(fails_on(shift_faults(bad), "shift: gold-dxy fired without"),
              f"shift fails: a flag fired with the {w[1:]}-day window "
              f"{'absent' if val is None else 'not a number'}")
    lone = {"lines": ["Shift: GOLD-DXY (60d +0.12, sign held, 2026-09-02)."], "data": {}}
    check(fails_on(shift_faults(lone), "shift: the line"),
          "shift fails: a printed shift showing one window")

    # -- the dry run ----------------------------------------------------------
    from altdata import derived
    bad = []
    for c in q.chapters(r["ed"]):
        by = {x.get("item"): x for x in c["subsections"]}
        if "correlation" in by:
            bad += corr_key_faults(by["correlation"], derived.registry_entry)
            bad += break_faults(by["correlation"]) + shift_faults(by["correlation"])
        for row in ((by.get("analyses") or {}).get("table") or {}).get("rows") or []:
            if "break logic" in row[0]:
                bad += analysis_break_faults(row[1])
    check(not bad, f"the dry run: every correlation item and every break-logic row "
                   f"passes ({bad[:2]})")

    # -- AQ-5's real code ----------------------------------------------------
    co = present("altdata.correlation")
    if co is None:
        for m in ("AQ-5's shift_eval never flags a day the 252-day window lacks",
                  "AQ-5's is_break and direction are the gate's threshold and sign",
                  "every key AQ-5's readers name for the Quarterly is registered"):
            skip("aq-5-correlation-layer", m)
        return
    days = [(dt.date(2020, 1, 1) + dt.timedelta(days=i)).isoformat() for i in range(400)]
    c60 = {d: ((-0.5 if i < 200 else 0.5), f"{d}T20:00:00+00:00", None)
           for i, d in enumerate(days)}
    c252 = {d: (0.0, f"{d}T20:00:00+00:00", None) for d in days[:150]}
    ev = co.shift_eval(c60, c252)
    check(ev and all(d in c252 for d in ev) and not co.shift_eval(c60, {}),
          f"AQ-5's shift_eval reads only days both windows hold ({len(ev)} of "
          f"{len(days)}), and nothing with the 252-day absent")
    check(co.is_break(0.30) and not co.is_break(0.29) and co.direction(0.4) == "toward"
          and co.direction(-0.4) == "away",
          "AQ-5's is_break and direction are the gate's threshold and sign")
    keys = [co.stored_key(n["key"]) for n in co.config().get("named") or []]
    unreg = [k for k in keys if not derived.registry_entry(k)]
    check(not unreg, f"every named row AQ-5 offers the Quarterly is registered "
                     f"({len(keys)}; {unreg[:3]})")


# ===========================================================================
# GATE 4 -- THE KILL CONDITIONS
# ===========================================================================
KILL_RE = re.compile(r"^(holds|strained|killed)( — .+)?$|^not measured — \S.+$")


def kill_config_faults(families: dict) -> list[str]:
    """[config] every analysis a chapter lists carries a kill condition: its
    section 5 text, or "none ruled" where the ruling gave none."""
    return [f"config: {fid}:{a.get('id')} has no kill condition"
            for fid, f in families.items() for a in f.get("analyses") or []
            if not str(a.get("kill") or "").strip()]


def kill_render_faults(fid: str, sub: Optional[dict], fam: dict) -> list[str]:
    """[render] item 6 prints every listed analysis, each with a reading and its
    kill state in the four words."""
    want = fam.get("analyses") or []
    if not want:
        return []
    if not sub:
        return [f"render: {fid} lists analyses and prints no item 6"]
    t = sub.get("table") or {}
    cols = t.get("columns") or []
    if "Kill state" not in cols:
        return [f"render: {fid}'s item 6 has no kill-state column"]
    ks, st = cols.index("Kill state"), cols.index("State")
    out = []
    if len(t.get("rows") or []) != len(want):
        out.append(f"render: {fid} lists {len(want)} analyses and prints "
                   f"{len(t.get('rows') or [])}")
    for row in t.get("rows") or []:
        if not str(row[st]).strip():
            out.append(f"render: {fid}:{row[0][:30]} prints no reading")
        if not KILL_RE.match(str(row[ks])):
            out.append(f"state: {fid}:{row[0][:30]} kill state {row[ks]!r}")
    return out


def gate_4(r: dict) -> None:
    from altdata import observations
    from monthly_macro import quarterly as q
    from monthly_macro import quarterly_items as qi
    head("4", "THE KILL-CONDITION GATE")
    qc = qi.load_config()
    fams = {k: v for k, v in (qc.get("families") or {}).items() if v.get("filled")}
    n = sum(len(f.get("analyses") or []) for f in fams.values())
    check(not kill_config_faults(fams),
          f"config: all {n} analyses across the chapters carry a kill condition "
          f"({kill_config_faults(fams)[:2]})")
    gone = copy.deepcopy(fams)
    gone["metals"]["analyses"][0].pop("kill")
    gone["crypto"]["analyses"][0]["kill"] = "  "
    f = kill_config_faults(gone)
    check(len(f) == 2 and fails_on(f, "config: metals:gold_residual"),
          "config fails: an analysis with its kill condition removed, or blank")
    # -- the state, computed ------------------------------------------------
    ctx = {"now": vqs.AS_OF, "end": "2026-09-30", "start": "2026-06-30"}
    with observations.ObservationStore(vms.DB) as st:
        got = {
            "none": qi.kill_state(st, {"kill": "none ruled (section 5)"}, ctx),
            "waits": qi.kill_state(st, {"kill": "only above a market-cap floor",
                                        "waits": "not built (AQ-8)"}, ctx),
            "absent": qi.kill_state(st, {"kill": ""}, ctx),
            "killed": qi.kill_state(st, {"kill": "x", "kill_measurable": {
                "change_below": {"series": "yfinance.mkt_gold_front", "below": 1000}}},
                ctx),
            "holds": qi.kill_state(st, {"kill": "x", "kill_measurable": {
                "change_below": {"series": "yfinance.mkt_gold_front", "below": -1000}}},
                ctx),
            "unread": qi.kill_state(st, {"kill": "x", "kill_measurable": {
                "change_below": {"series": "fred.not_a_series", "below": 0}}}, ctx),
            "nomeas": qi.kill_state(st, {"kill": "lead under 2 months"}, ctx),
        }
    print("        " + json.dumps(got, ensure_ascii=False)[:400])
    check(got["none"] == qi.KILL_NONE_RULED and got["waits"].startswith(
        "not measured — the analysis waits: not built")
          and got["absent"] == "not measured — no kill condition in config"
          and got["nomeas"].startswith("not measured — the kill condition has no "
                                       "measurable"),
          "kill_state: none ruled, waiting, absent and unmeasured each print \"not "
          "measured\" with the reason")
    check(got["killed"].startswith("killed") and got["holds"].startswith("holds")
          and got["unread"].startswith("not measured — "),
          f"kill_state from a kill measurable: met is killed, not met holds, an "
          f"unreadable series not measured ({got['killed'][:40]}; {got['holds'][:30]})")
    check(all(KILL_RE.match(v) for v in got.values()),
          "every computed state is in the four words")
    check(qi.kill_vocab("no stable sign (kill condition met; not acted on)")
          .startswith("killed — ")
          and qi.kill_vocab("stable").startswith("holds — ")
          and qi.kill_vocab("kill test waits: 4 of 12 months of call-put OI")
          == "not measured — kill test waits: 4 of 12 months of call-put OI"
          and qi.kill_vocab("strained — two quarters").startswith("strained"),
          "AQ-8a's own wordings map into the four: no stable sign is killed, stable "
          "holds, a waiting test is not measured with its count")
    fake = types.ModuleType("aq10_fake_bid")
    fake.oi_kill_state = lambda st, sym, now: f"kill test waits: 3 of 12 months ({sym})"
    sys.modules["aq10_fake_bid"] = fake
    try:
        rd = qi.kill_state(None, {"kill": "drop call-put OI ...",
                                  "module": "aq10_fake_bid", "branch": "aq-8a-gold-residual",
                                  "kill_reader": "oi_kill_state", "kill_args": ["GLD"]},
                           ctx)
    finally:
        sys.modules.pop("aq10_fake_bid", None)
    nr = qi.kill_state(None, {"kill": "drop call-put OI ...", "module": "aq10_no_module",
                              "branch": "aq-8a-gold-residual",
                              "kill_reader": "oi_kill_state", "kill_args": ["GLD"]}, ctx)
    check(rd == "not measured — kill test waits: 3 of 12 months (GLD)"
          and nr == "not measured — not yet: aq-8a-gold-residual",
          f"a kill reader on the analysis's own module (AQ-8a's documented "
          f"oi_kill_state) is read, and degrades to \"not yet: <branch>\" ({nr})")
    # -- render ---------------------------------------------------------------
    fam = {"analyses": [{"id": "a", "kill": "none ruled"}, {"id": "b", "kill": "x"}]}
    row = lambda s, k: ["An analysis", s, "x", k]                   # noqa: E731
    good = {"table": {"columns": list(qi.ANALYSIS_COLUMNS),
                      "rows": [row("0.42 (2026-09-30)", qi.KILL_NONE_RULED),
                               row("not yet — AQ-8", "not measured — the analysis waits: AQ-8")]}}
    check(not kill_render_faults("x", good, fam), "render passes: two analyses, each "
                                                  "with a reading and a kill state")
    for tag, mut, why in (
            ("state:", lambda t: t["rows"][0].__setitem__(3, "fine"),
             "a kill state outside the four words"),
            ("state:", lambda t: t["rows"][0].__setitem__(3, "not measured"),
             "\"not measured\" with no reason"),
            ("state:", lambda t: t["rows"][0].__setitem__(3, "dead"),
             "\"dead\" for killed"),
            ("render: x:An analysis prints no reading",
             lambda t: t["rows"][0].__setitem__(1, " "), "a row with no reading"),
            ("render: x lists 2", lambda t: t["rows"].pop(), "an analysis not printed"),
            ("render: x's item 6 has no kill-state",
             lambda t: (t["columns"].pop(), [x.pop() for x in t["rows"]]),
             "the AQ-2 table, kill condition but no kill state")):
        g2 = copy.deepcopy(good)
        mut(g2["table"])
        check(fails_on(kill_render_faults("x", g2, fam), tag), f"render fails: {why}")
    check(fails_on(kill_render_faults("x", None, fam), "render: x lists analyses"),
          "render fails: a chapter that lists analyses and prints no item 6")
    # -- the dry run ----------------------------------------------------------
    bad, n_rows, states = [], 0, {}
    for c in q.chapters(r["ed"]):
        by = {x.get("item"): x for x in c["subsections"]}
        if c["id"] in fams:
            bad += kill_render_faults(c["id"], by.get("analyses"), fams[c["id"]])
        for row_ in ((by.get("analyses") or {}).get("table") or {}).get("rows") or []:
            n_rows += 1
            w = row_[-1].split(" — ")[0]
            states[w] = states.get(w, 0) + 1
    check(not bad and n_rows == n,
          f"the dry run: all {n_rows} analyses print a reading and a kill state "
          f"({states}) ({bad[:2]})")
    # -- AQ-8a's real code ---------------------------------------------------
    att, pb = present("altdata.attribution"), present("altdata.paper_bid")
    if att is None or pb is None:
        skip("aq-8a-gold-residual", "AQ-8a's gold, yields-up/dollar-down and call-put "
                                    "OI kill readers map into the four words")
        return
    with observations.ObservationStore(vms.DB) as st:
        outs = [att.gold_kill_state(), att.yudd_kill_state(),
                pb.oi_kill_state(st, "GLD", vqs.AS_OF), pb.rr_kill_state()]
    check(all(KILL_RE.match(qi.kill_vocab(x)) for x in outs),
          f"AQ-8a's kill readers map into the four words ({outs[2]})")


# ===========================================================================
# GATE 5 -- DRAFT PER HORIZON
# ===========================================================================
PORTFOLIO_ROLES = ("structural", "proxy", "direct", "convex", "carry", "growth",
                   "tactical")
THIN = "thin or poorly understood contract"


def draft_faults(cid: str, sub: Optional[dict], weight: str,
                 rule: Optional[dict] = None) -> list[str]:
    """The rule over a rendered item 10."""
    out = []
    rule = rule or {}
    if sub is None:
        return [f"render: {cid} prints no item 10"]
    t = sub.get("table") or {}
    rows = t.get("rows") or []
    cols = t.get("columns") or []
    lines = " ".join(sub.get("lines") or [])
    if cid == "thailand":
        if any(r[1] == "draft" for r in rows):
            out.append("thailand: a draft printed")
        if not lines.startswith("No draft, by rule"):
            out.append("thailand: the no-draft rule line is missing")
        return out
    if cid == "agriculture" and "thin or poorly understood contracts" not in lines:
        out.append("agriculture: the thin-contract rule line is missing")
    if not rows:
        return out
    for need in ("Horizon", "Line", "Portfolio role", "Cost row", "Decision or reason"):
        if need not in cols:
            out.append(f"cost: {cid}'s book has no {need!r} column")
    if out:
        return out
    ix = {c: cols.index(c) for c in cols}
    per: dict = {}
    for r in rows:
        h = r[ix["Horizon"]]
        if r[ix["Line"]] == "draft":
            per[h] = per.get(h, 0) + 1
            role = r[ix["Portfolio role"]]
            if role not in PORTFOLIO_ROLES:
                out.append(f"role: {cid} {h} draft has portfolio role {role!r}")
            if not str(r[ix["Cost row"]]).strip() or r[ix["Cost row"]] == "—":
                out.append(f"cost: {cid} {h} draft carries no cost row")
            if cid == "agriculture":
                inst = str(r[ix["Decision or reason"]]).split(" · ")[0]
                if inst not in (rule.get("understood_instruments") or []):
                    out.append(f"agriculture: a draft on {inst}, which is not named "
                               f"understood")
        elif not str(r[ix["Decision or reason"]]).strip() or \
                r[ix["Decision or reason"]] == "—":
            out.append(f"no draft: {cid} {h} no-draft line without its reason")
    for h, k in per.items():
        if k > 1:
            out.append(f"one draft: {cid} prints {k} drafts for {h}")
    if weight == "deep":
        for h in ("3m", "12m"):
            if h not in {r[ix["Horizon"]] for r in rows}:
                out.append(f"no draft: {cid} {h} has neither a draft nor a no-draft line")
    return out


BOOKS_SCHEMA = """CREATE TABLE alt_asset_books (
    family TEXT NOT NULL, quarter TEXT NOT NULL, horizon_kind TEXT NOT NULL,
    kind TEXT NOT NULL, decision_id TEXT, reason TEXT, portfolio_role TEXT,
    cost_json TEXT, file_sha256 TEXT NOT NULL, written_at TEXT NOT NULL,
    seeded_at TEXT NOT NULL)"""
COST = {"instrument": "GLD", "spread": "not priced", "roll": "not priced",
        "borrow": "not priced", "fx_hedge": "not priced", "available": True,
        "commission": 1.0, "is_floor_not_all_in": True}


def books_db(rows: list[tuple]) -> str:
    """A ledger database holding AQ-6's alt_asset_books (its documented schema,
    less the triggers) with these rows: (family, horizon, kind, decision_id,
    reason, role, cost)."""
    p = str(Path(gate_tmp.mkdtemp("aq10_books_")) / "ledger.db")
    con = sqlite3.connect(p)
    con.execute(BOOKS_SCHEMA)
    for i, (fam, h, kind, did, why, role, cost) in enumerate(rows):
        con.execute("INSERT INTO alt_asset_books VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (fam, "2027q1", h, kind, did, why, role,
                     json.dumps(cost) if cost else None, "f" * 64,
                     f"2026-11-07T15:00:0{i}+00:00", "2026-11-08T12:00:00+00:00"))
    con.commit()
    con.close()
    return p


def book_item(cid: str, rows: list[tuple], understood=None) -> tuple[dict, str, dict]:
    """item 10 built by the real builder over a fixture books table, with a
    stand-in thesis module so the book reads (AQ-6's module is the gate)."""
    from daily_cascade import stack as stack_mod
    from monthly_macro import quarterly_items as qi
    ch = next(c for c in stack_mod.config()["quarterly_chapters"] if c["id"] == cid)
    fam = copy.deepcopy(qi.family_config(cid) or {})
    if understood is not None:
        fam.setdefault("book_rule", {})["understood_instruments"] = understood
    saved = qi.ITEM_MODULES["thesis"]
    sys.modules["aq10_fake_thesis"] = types.ModuleType("aq10_fake_thesis")
    qi.ITEM_MODULES["thesis"] = "aq10_fake_thesis"
    try:
        sub = qi.item_book(ch, {"next_quarter": "2027q1", "db_path": books_db(rows)},
                           fam)
    finally:
        qi.ITEM_MODULES["thesis"] = saved
        sys.modules.pop("aq10_fake_thesis", None)
    return sub, ch.get("weight"), fam.get("book_rule") or {}


def gate_5(r: dict) -> None:
    from monthly_macro import quarterly as q
    from monthly_macro import quarterly_items as qi
    head("5", "THE DRAFT-PER-HORIZON GATE")
    two = [("metals", "3m", "draft", "d" * 36, None, "proxy", COST),
           ("metals", "12m", "no_draft", None, "no edge beyond the strategic "
                                               "allocation", None, None)]
    sub, w, rule = book_item("metals", two)
    check(not draft_faults("metals", sub, w, rule) and sub["table"]["rows"][0][3]
          .startswith("commission $1.00 (rate card, a floor); spread, roll, borrow, "
                      "FX hedge not priced"),
          f"the passing fixture: a 3-month draft with its role and cost row, a "
          f"12-month no draft with its reason ({sub['table']['rows'][0][3][:60]}...)")
    print("        " + " | ".join(" / ".join(map(str, x)) for x in sub["table"]["rows"]))
    one = [two[0]]
    sub1, w, rule = book_item("metals", one)
    check(not draft_faults("metals", sub1, w, rule)
          and sub1["table"]["rows"][-1][:2] == ["12m", "no draft"]
          and "no book line was written" in sub1["table"]["rows"][-1][4],
          "a deep chapter with no line for a horizon prints the no-draft line for it")
    # -- at most one ----------------------------------------------------------
    dup = two + [("metals", "3m", "draft", "e" * 36, None, "tactical", COST)]
    s, w, rule = book_item("metals", dup)
    check(fails_on(draft_faults("metals", s, w, rule), "one draft: metals prints 2"),
          "one draft fails: two drafts for one family's 3-month horizon")
    # -- cost and role -------------------------------------------------------
    s, w, rule = book_item("metals", [("metals", "3m", "draft", "d" * 36, None,
                                       "proxy", None), two[1]])
    check(fails_on(draft_faults("metals", s, w, rule), "cost: metals 3m"),
          "cost fails: a draft whose book line carries no cost row")
    s, w, rule = book_item("metals", [("metals", "3m", "draft", "d" * 36, None, None,
                                       COST), two[1]])
    check(fails_on(draft_faults("metals", s, w, rule), "role: metals 3m"),
          "role fails: a draft with no portfolio role")
    s, w, rule = book_item("metals", [("metals", "3m", "draft", "d" * 36, None,
                                       "speculative", COST), two[1]])
    check(fails_on(draft_faults("metals", s, w, rule), "role: "),
          "role fails: a role outside XVII's words")
    old = copy.deepcopy(sub)
    old["table"]["columns"].remove("Cost row")
    for x in old["table"]["rows"]:
        del x[3]
    check(fails_on(draft_faults("metals", old, "deep"), "cost: metals's book has no"),
          "cost fails: the AQ-2 book table, which has no cost column")
    unpriced = dict(COST, available=False, commission=None,
                    reason="no quantity on the draft")
    s, w, rule = book_item("metals", [("metals", "3m", "draft", "d" * 36, None, "proxy",
                                       unpriced), two[1]])
    check(not draft_faults("metals", s, w, rule)
          and s["table"]["rows"][0][3].startswith("commission not priced: no quantity"),
          "a draft whose commission is unpriced still carries its cost row, with "
          "the reason")
    # -- the no-draft line ---------------------------------------------------
    nr = copy.deepcopy(sub)
    nr["table"]["rows"][1][4] = "—"
    check(fails_on(draft_faults("metals", nr, "deep"), "no draft: metals 12m no-draft"),
          "no draft fails: a no-draft line without its reason")
    miss = copy.deepcopy(sub1)
    miss["table"]["rows"].pop()
    check(fails_on(draft_faults("metals", miss, "deep"), "no draft: metals 12m has"),
          "no draft fails: a deep chapter's horizon with neither line")
    # -- Thailand -------------------------------------------------------------
    s, w, rule = book_item("thailand", [("thailand", "3m", "draft", "t" * 36, None,
                                         "tactical", COST)])
    check(not draft_faults("thailand", s, w, rule) and not s.get("table"),
          f"Thailand prints no draft even with one in the books table: "
          f"\"{s['lines'][0][:60]}...\"")
    bad = {"lines": ["No draft, by rule: isolated"],
           "table": {"columns": list(qi.BOOK_COLUMNS),
                     "rows": [["3m", "draft", "tactical", "commission $1.00",
                               "THB · tttttttt"]]}}
    check(fails_on(draft_faults("thailand", bad, "country"), "thailand: a draft"),
          "thailand fails: a draft printed in the Thailand chapter")
    check(fails_on(draft_faults("thailand", {"lines": ["The book."]}, "country"),
                   "thailand: the no-draft rule line"),
          "thailand fails: the rule line missing")
    # -- agriculture ---------------------------------------------------------
    ag = [("agriculture", "3m", "draft", "a" * 36, None, "tactical",
           dict(COST, instrument="ZC"))]
    s, w, rule = book_item("agriculture", ag)
    check(not draft_faults("agriculture", s, w, rule)
          and s["table"]["rows"][0][1] == "no draft" and THIN in s["table"]["rows"][0][4],
          f"agriculture: a draft on a contract not named understood prints as a no "
          f"draft ({s['table']['rows'][0][4][:70]})")
    s, w, rule = book_item("agriculture", [ag[0][:6] + (dict(COST, instrument="DBA"),)],
                           understood=["DBA"])
    check(not draft_faults("agriculture", s, w, rule) and s["table"]["rows"][0][1] == "draft",
          "agriculture: a draft on an instrument the operator names understood prints")
    agbad = {"lines": [l for l in s["lines"]],
             "table": {"columns": list(qi.BOOK_COLUMNS),
                       "rows": [["3m", "draft", "tactical", "commission $1.00",
                                 "ZC · aaaaaaaa"]]}}
    check(fails_on(draft_faults("agriculture", agbad, "light", {"understood_instruments":
                                                                ["DBA"]}),
                   "agriculture: a draft on ZC"),
          "agriculture fails: a draft printed on a thin contract")
    check(fails_on(draft_faults("agriculture", {"lines": ["By rule: names a fund"]},
                                "light"), "agriculture: the thin-contract rule"),
          "agriculture fails: the thin-contract rule line missing")
    # -- the dry run ----------------------------------------------------------
    from daily_cascade import stack as stack_mod
    weights = {c["id"]: c.get("weight") for c in stack_mod.config()["quarterly_chapters"]}
    qc = qi.load_config()["families"]
    bad = []
    for c in q.chapters(r["ed"]):
        by = {x.get("item"): x for x in c["subsections"]}
        if "book" in by or c["id"] in ("thailand", "agriculture"):
            bad += draft_faults(c["id"], by.get("book"), weights[c["id"]],
                                (qc.get(c["id"]) or {}).get("book_rule"))
    check(not bad, f"the dry run: every chapter's item 10 passes; Thailand and "
                   f"agriculture print their rules ({bad[:2]})")
    tr = present("altdata.thesis_register")
    if tr is None:
        skip("aq-6-thesis-register", "AQ-6's draft_rule_faults and its portfolio roles "
                                     "are the gate's")
        return
    check(tuple(tr.PORTFOLIO_ROLES) == PORTFOLIO_ROLES
          and tr.draft_rule_faults({"families": {}}) != [],
          "AQ-6's portfolio roles are the gate's, and its load-time rule refuses a "
          "file with no deep family")


# ===========================================================================
def dry_run() -> dict:
    """The Quarterly's dry run on the Quarterly stack gate's synthetic store."""
    from monthly_macro import quarterly as q
    vms.seed(vms.DB, dealer_sessions=21)
    vqs.seed_aq2(vms.DB)
    p = vqs.build_payload()
    calls: list = []
    out = q.produce(p, archive_dir=str(Path(vms.TD) / "q10"),
                    client=vms.client(calls, {}), db_path=vms.DB)
    return {"ed": out["edition"], "out": out}


def main() -> int:
    print(f"{LINE}\nAQ-10 -- the Quarterly's validators (synthetic 3Q26)\n{LINE}")
    print("building the Quarterly's dry run on the synthetic store ...")
    r = dry_run()
    for g in (gate_1, gate_2, gate_3, gate_4, gate_5):
        g(r)
    print(f"\n{LINE}")
    for g, (p, f, s) in COUNTS.items():
        print(f"  gate {g}: {p} passed, {f} failed, {s} waiting on a branch")
    print(f"{PASS} passed, {FAIL} failed, {SKIP} skipped (activate on merge)\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
