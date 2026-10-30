"""
Validation gate for W-1.1a, the audit fixes from the Weekly dry run of 12 Oct
2026 (run weekly-20261013T021911).

Six of ten sections commented; four were withheld by the audits' own faults, and
six printed sentences the audits let through. The fixtures are the dry run's own
figures, as quoted (tests/fixtures/weekly_run5_2026-10-12.json); no live store,
no network, no model:

  A  UNIT KINDS. The four run-5 figures -- the implied daily move 0.93%, the
     implied rate 3.92%, the hike probability 19%, the increment 25 bp -- pass,
     in the frames as built now (each under a key naming its unit) and in the
     frames as they were (a unit written beside a figure wins over its field's
     name). A row whose registry key declares a yield may be written as a
     percent; a price written as a percent still fails, and the message names
     the series kind it used.
  B  THE BOOK'S BUDGET. The book has a budgeted frame whose cap is the
     section's computed cap and is stated; the Book Z line is one group, so the
     run-5 paragraph (nine figures by the dry run's count, eight of them the
     Book Z line's) comments. "60-40" is a name, not two figures.
  C  THE DIRECTION AUDIT. The run-5 Plumbing paragraph is withheld on "the
     dollar softened" against DXY +0.27%, in the message's own words; "firmed"
     passes; "EUR/USD fell 0.43%, the dollar firmer" passes; a verb against its
     figure's sign fails; the pipeline withholds and the retry hears why.
  D  READABILITY. A signed figure after an agreeing lexicon verb prints unsigned
     and is counted; "bullish on inflation" and "marked broke" are flagged; the
     frames carry both rules.
  E  A CEILING, NOT A QUOTA. Every frame says so; "Real Estate added +1.96%." is
     filler, and the same figure with something to read it against is not.
  F  DERIVED SERIES AND ALIASES. A derived series reads both legs on the latest
     date both have and prints it; the frames say "the front" is the 2-year;
     the run-5 10-year figures (5.244% on 9 Oct, 5.28% on 7 Oct) pass as
     different dates, the same date with a 4 bp gap fails, and a chart caption
     without its source fails.
  G  THE MONTHLY'S PROSE PATH (W-1.1b). monthly_macro/prose.py runs the
     direction audit, the stance check and the sign rewrite as stack_prose.write
     does: a Monthly paragraph saying "the dollar softened" against DXY +0.27%
     is withheld on the Weekly's message and retried; "bullish on inflation" is
     withheld, in a stack frame and a v2 section; "fell -3 bp" prints "fell 3 bp".
  H  W-1.3c ITEM 1, from dry run #6 (tests/fixtures/weekly_run6_2026-10-13.json):
     a sign before a currency symbol is the figure's. Run 6's "fell −$1bn" passes
     against its own Plumbing rows (it was withheld as "'fell' with a rise"), with
     a hyphen too; "rose −$1bn" fails; "+$82bn" reads as a rise; the euro, pound
     and yen signs read alike.
  I  W-1.3c ITEM 6: a retry carries the whole withhold message and the rule
     behind each fault; three attempts on the Weekly. A fake model that obeys
     the reason on attempt 2 publishes; one that never does is withheld after
     three; a fifth fault (run 6's Ahead Takeaway) still reaches the retry.
  J  THE MONTHLY POLISH FROM DRY RUN #5 (T3.6; tests/fixtures/monthly_run5_
     2026-10-13.json). M1 the role audit: "closed at" bound to a 40-week average
     is withheld, the long frame names its columns' roles; M2 one direction per
     instrument across the executive summary; M3 the one page against the
     summary and itself, at most five paragraphs; M4 a derived change from
     aligned legs, withheld with its legs when it is not theirs; M5 each gap's
     direction over the month, the summary held to it; M6 forecasts and
     decisions summarised; M7 small counts in words; M8 too long retried once
     tighter, the narratives' sources; M9 the display form of a large figure;
     M10 the two dollar series by name.

    python tools/validate_audit_fixes.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

from altdata import numeral_audit as na  # noqa: E402
from daily_cascade import consistency as cons  # noqa: E402
from daily_cascade import direction  # noqa: E402
from daily_cascade import figure_budget as fb  # noqa: E402
from daily_cascade import readability  # noqa: E402
from daily_cascade import stack_prose as sp  # noqa: E402
try:
    from daily_cascade import opener  # noqa: E402  (W-1.3a)
except ImportError:                                         # before W-1.3a merges
    opener = None

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FIX = json.loads((REPO / "tests" / "fixtures" / "weekly_run5_2026-10-12.json")
                 .read_text(encoding="utf-8"))
DAY = "2026-10-09"
PASS = 0
FAIL = 0
LINE = "=" * 78


def check(c: bool, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


class Reply:
    def __init__(self, text):
        self.published, self.text, self.model = True, text, "fixture"
        self.state, self.reason = "published", None

    def withheld_note(self):
        return None


# THE OPENER'S SHAPE (W-1.3a item 3.0) holds every Weekly section to a word band
# and a closing Takeaway. These checks are about other faults, so each draft is
# brought into shape with sentences that carry no figure and no directional word,
# and closes on a Takeaway -- neither rule is loosened to let a draft through.
_PAD = ("The section's tables carry the levels and the dates behind each figure "
        "cited here, so the paragraph names only what the story needs. The desk "
        "reads the week through the funding markets first and the curve second, "
        "and holds each reading against the prior week's record before anything is "
        "said about it. ")
_TAKEAWAY = ("Takeaway: the week's record leaves the standing read intact, and the "
             "coming auctions are its test.")


def shaped(text: str, depth: str) -> str:
    """`text` in the opener's band at `depth`, ending on one Takeaway; unchanged
    on a branch without the opener."""
    if opener is None:
        return text
    from daily_cascade import cadence as cad_mod
    lo = (opener.band(cad_mod.get("weekly"), depth) or (0, 0))[0]
    body = text.rstrip() + " "
    while opener.words(body + _TAKEAWAY) < lo:
        body += _PAD
    return body + _TAKEAWAY


def run_write(sections: list, drafts: list, cadence: str = "weekly") -> tuple:
    """sp.write over `sections` with the model replaced by `drafts`, in order."""
    from daily_cascade import narrative as base
    seen: list = []
    real = base.generate

    def fake(payload, **kw):
        seen.append(kw.get("system_prompt") or "")
        return Reply(drafts[min(len(seen) - 1, len(drafts) - 1)])
    base.generate = fake
    try:
        tape = {"id": "tape", "title": "The tape", "depth": "deep", "items": [],
                "table": None, "subsections": [], "data": {}, "empty": True}
        read = {"id": "read", "title": "The read", "depth": "deep", "items": [],
                "table": None, "subsections": [], "data": {}, "empty": True}
        ed = {"session": DAY, "sections": [read, tape] + sections}
        sp.write(ed, client=object(), cadence=cadence)
    finally:
        base.generate = real
    return ed, seen


def group_a() -> None:
    print(f"\n{LINE}\nA. UNIT KINDS (the four run-5 figures)\n{LINE}")
    u = FIX["unit_kinds"]
    vol = {"title": "Volatility", "table": {
        "columns": ["Measure", "Priced", "Realized", "Week"],
        "rows": [u["mechanics_volatility_row"]]}}
    mech = {"id": "mechanics", "title": "Mechanics", "depth": "deep", "items": [],
            "table": None, "subsections": [vol], "data": {}}
    mf = fb.mechanics_frame(mech, {"session": DAY}, 6, "the week")
    cite = mf["figures_you_may_cite"][0]
    check("implied_daily_move_pct" in cite and "priced" not in cite,
          f"Mechanics' daily move sits under a key naming its unit ({sorted(cite)})")
    r = na.audit(u["mechanics_text"], mf)
    check(r.passed, f"0.93% passes against the frame as built now ({r.reason()[:80]})")
    old = {"figures_you_may_cite": [{"series": u["mechanics_volatility_row"][0],
                                     "priced": u["mechanics_volatility_row"][1],
                                     "realized": u["mechanics_volatility_row"][2]}]}
    r = na.audit(u["mechanics_text"], old)
    check(r.passed, f"and against the frame as it was: the % written beside 0.93 "
                    f"wins over the key `priced` ({r.reason()[:60]})")
    fc = fb.fomc_cite(u["fomc_row"])
    check(fc.get("implied_rate_pct") == "3.92%" and fc.get("move_probability_pct") ==
          "19%" and fc.get("move_increment_bp") == "25 bp" and fc.get("direction") ==
          "hike", f"Ahead's FOMC cite carries each figure in its unit ({fc})")
    r = na.audit(u["ahead_text"], {"figures_you_may_cite": [fc]})
    check(r.passed, f"3.92%, 19% and 25 bp pass against the new cite ({r.reason()[:70]})")
    oldA = {"figures_you_may_cite": [{"series": u["fomc_row"][0], "level": u["fomc_row"][1],
                                      "priced": u["fomc_row"][2]}]}
    r = na.audit(u["ahead_text"], oldA)
    check(r.passed, f"and against the old `level`/`priced` keys ({r.reason()[:60]})")
    r = na.audit(u["price_as_percent_text"], u["price_payload"])
    check(not r.passed and "series kind: price" in r.reason(),
          f"a price written as a percent still fails, naming the kind ({r.reason()[:110]})")
    r = na.audit("The 10-year closed at 4.05%.", {"key": "fred.yield_10y", "level": 4.05})
    check(r.passed and r.matched and r.matched[0][0].series_kind == "yield",
          "a yield the payload types as a price (field `level`) may be written as a "
          "percent: its registry key declares the kind")
    r = na.audit("The 10-year closed at 4.05%.", {"level": 4.05})
    check(not r.passed and "series kind: none declared" in r.reason(),
          "with no kind declared, the strict path holds and says so")
    r = na.audit("SOFR rose 3 bp.", {"key": "fred.sofr", "level": 3})
    check(r.passed, "a rate's change may be written in bp")
    r = na.audit("Kalshi's odds rose 12 pts.", {"series_kind": "probability", "mark": 12})
    check(r.passed, "a probability's change may be written in points")
    kinds = na.registry_kinds()
    check(kinds.get("yfinance.mkt_tnx") == "yield" and kinds.get("pm.probability")
          == "probability" and kinds.get("yfinance.mkt_spy") == "price",
          f"metrics_registry.yaml declares the kinds ({len(kinds)} series)")


def book_section() -> dict:
    b = FIX["book"]
    return {"id": "book", "title": "The book", "depth": "medium",
            "items": [{"key": "book:open", "text": "0 open decision(s), 0 draft(s).",
                       "priority": 1},
                      {"key": "book:breaks", "text": "2 rule break(s) this week; 3 on "
                       "the register to date.", "priority": 2},
                      {"key": "book:z", "text": f"Against Book Z, {b['book_z']}.",
                       "priority": 2}],
            "table": {"columns": ["Count", "This week", "Budget"],
                      "rows": [["Packets approved", 2, 3],
                               ["Sitting time", "22 minutes", "120 minutes"]]},
            # weekly-fixes-7 item 6: the week's window beside since-inception, as
            # the pipeline now prints it, so "on the week" has its figure.
            "subsections": [], "data": {"book_z": "on the week (2026-10-02 to "
                                        "2026-10-09): the book +0.11%; "
                                        + b["book_z"]}}


def group_b() -> None:
    print(f"\n{LINE}\nB. THE BOOK'S BUDGET\n{LINE}")
    b = FIX["book"]
    bk = book_section()
    ed = {"session": DAY, "sections": [bk]}
    cap = sp.section_figure_cap("book", "weekly")
    check("book" in sp.BUDGETED_FRAMES["weekly"],
          "the book is a budgeted frame on the Weekly, as the read, Mechanics, What "
          "doesn't fit and Ahead are")
    fr = sp.section_slice(bk, ed, "weekly")
    check(fr.get("figures_you_may_cite") and fr["figures_you_may_cite"][0]["series"]
          == fb.BOOK_GROUP and f"at most {cap}" in (fr.get("cap_note") or "")
          and "tables carry the rest" in fr["cap_note"],
          f"the frame offers the Book Z line first, as one group, and states its cap "
          f"({fr.get('cap_note')})")
    check(fb.frame_figures(fr) <= cap,
          f"the frame offers {fb.frame_figures(fr)} figures with the group as one "
          f"(cap {cap}, computed by section_cap)")
    check("THE BOOK'S CAP" in sp.section_prompt(bk, "weekly"),
          "the book's prompt states its cap and the group")
    groups = fb.book_groups(ed)
    old_count = len(readability._FIG.findall(b["paragraph"].split(". ", 1)[1]))  # noqa: SLF001
    check(old_count >= b["figures_before"],
          f"the run-5 paragraph cites {old_count} figures by the dry run's count "
          f"(60-40 read as two)")
    raw = sp.figure_faults(b["paragraph"], cap)
    grp = sp.figure_faults(b["paragraph"], cap, groups)
    check(raw and not grp,
          f"ungrouped it is withheld ({(raw or ['-'])[0][:60]}); with the Book Z line as "
          f"one group it comments ({sp.figures_cited(b['paragraph'], groups)} of {cap})")
    check(readability.figures("60-40 and 60/40") == [],
          "'60-40' is the benchmark's name, never two figures")
    ed2, seen = run_write([book_section()], [shaped(b["paragraph"], "medium")])
    check(ed2["prose"]["book"]["published"],
          f"through the pipeline, the run-5 book paragraph publishes "
          f"({ed2['prose']['book'].get('reason')})")


def plumbing_section() -> dict:
    mv = FIX["direction"]["moves"]
    rows = [[n, "—", v[1], DAY] for n, v in mv.items()]
    return {"id": "plumbing", "title": "Plumbing & rates", "depth": "deep", "items": [],
            "table": {"columns": ["Series", "Level", "Week", "As of"], "rows": rows},
            "subsections": [], "data": {}}


def group_c() -> None:
    print(f"\n{LINE}\nC. THE DIRECTION AUDIT\n{LINE}")
    d = FIX["direction"]
    mv = {k: tuple(v) for k, v in d["moves"].items()}
    f = direction.faults(d["plumbing_paragraph"], mv)
    check(f == [d["expected_fault"]], f"the run-5 paragraph fails: {f}")
    check(direction.faults(d["firmed_paragraph"], mv) == [],
          "the same paragraph with 'firmed' passes")
    check(direction.faults(d["pair_text"], mv) == [],
          f"'{d['pair_text']}' passes: EUR/USD down is the dollar firmer")
    check(direction.faults("EUR/USD rose 0.43%.", mv)
          and direction.faults("The 2-year rose -11 bp.", mv),
          "a verb against its figure's sign fails, signed or not")
    check(direction.faults("The dollar softened.",
                           {"EUR/USD (dollars per euro)": (-0.43, "-0.43%", "%")}),
          "with no DXY row, the dollar is read through EUR/USD's quote convention")
    check(not direction.faults("The yen weakened.",
                               {"USD/JPY (yen per dollar)": (0.8, "+0.80%", "%")}),
          "USD/JPY up is the yen weaker")
    check(not direction.faults("The 10-year closed at 4.05%, unchanged on the week.",
                               mv), "a clause with no directional word is not checked")
    check(not direction.faults("The curve fell to 10 bp.", mv),
          "a figure after 'to' is a level, not a change, and is not read")
    ed, seen = run_write([plumbing_section()],
                         [shaped(d["plumbing_paragraph"], "deep"),
                          shaped(d["firmed_paragraph"], "deep")])
    pr = ed["prose"]["plumbing"]
    check(pr.get("attempts") == 2 and pr.get("published")
          and d["expected_fault"] in (seen[1] if len(seen) > 1 else ""),
          f"the pipeline withholds the first draft and the retry hears the fault "
          f"({pr.get('attempts')} attempts)")
    reg = (REPO / "metrics_registry.yaml").read_text(encoding="utf-8")
    check("quote_conventions:" in reg and direction.conventions().get("eur/usd", {})
          .get("rises") == "base", "the sign conventions are the registry's")


def group_d() -> None:
    print(f"\n{LINE}\nD. READABILITY\n{LINE}")
    r = FIX["readability"]
    out, n = readability.unsign_after_verbs(r["signed_after_verbs"])
    check(out == r["unsigned"] and n == r["rewrites"],
          f"'fell -3 bp' prints 'fell 3 bp', and the rewrites are counted ({n})")
    out, n = readability.unsign_after_verbs("EUR/USD rose -0.43%.")
    check(n == 0 and out == "EUR/USD rose -0.43%.",
          "a verb that disagrees is left for the direction audit")
    check(readability.stance_faults(r["stance"]),
          "'bullish on inflation' is flagged")
    check(not readability.stance_faults("Desks expect inflation to stay above target; "
                                        "SPY's net GEX is positive."),
          "'expects inflation to stay above target' passes")
    check(readability.stance_faults(r["marked_broke"]), "'marked broke' is flagged")
    check("never \"fell -3 bp\"" in sp.RULES and "marked broke" in sp.RULES
          and "bullish" in sp.RULES,
          "the frames carry the verb rule, the level rule and the stance rule")
    r2 = na.audit("The 2-year fell 11 bp.", na.with_signed({"week_change_bp": -11}))
    check(r2.passed, "the numeral audit accepts the size after a falling verb")
    ed, _ = run_write([plumbing_section()],
                      [shaped("Plumbing turned on the long end. The 2-year fell -11 bp "
                              "against a steady long end.", "deep")])
    pr = ed["prose"]["plumbing"]
    para = " ".join(next(s for s in ed["sections"] if s["id"] == "plumbing")
                    .get("paragraphs") or [])
    check(pr.get("published") and "fell 11 bp" in para
          and pr.get("unsigned_rewrites") == 1
          and ed.get("unsigned_rewrites") == sum(int(x.get("unsigned_rewrites") or 0)
                                                  for x in ed["prose"].values()),
          f"the pipeline prints the rewrite and counts it ({para[:60]})")


def group_e() -> None:
    print(f"\n{LINE}\nE. A CEILING, NOT A QUOTA\n{LINE}")
    f = FIX["filler"]
    check(sp.CEILING_RULE.strip() in sp.RULES and sp.CEILING_RULE.strip()
          in sp.READ_RULES, "every section frame and The read's carry the rule")
    check("never join two unrelated figures" in sp.CEILING_RULE,
          "the rule names the run-5 fault: two unrelated figures in one sentence")
    check(bool(sp.filler_faults(f["bare"])), f"'{f['bare']}' is filler")
    check(not sp.filler_faults(f["read"]), f"'{f['read'][:50]}...' passes")
    check(not sp.filler_faults("SPY rose 1.2% against a flat 10-year.")
          and not sp.filler_faults("The curve steepened."),
          "a comparison word, or no figure at all, is not the bare-figure fault")


def group_f() -> None:
    print(f"\n{LINE}\nF. DERIVED SERIES AND ALIASES\n{LINE}")
    import gate_tmp
    from altdata import observations
    from daily_cascade import weekly_sections as wsec
    td = gate_tmp.mkdtemp("validate_audit_fixes_")
    db = str(Path(td) / "fx.db")
    rows = []

    def put(k, d, v):
        rows.append({"registry_key": k, "instrument": None, "observed_at": d,
                     "available_at": f"{d}T22:00:00+00:00", "value": v,
                     "source": "synthetic"})
    for d, c in (("2026-10-01", 9.20), ("2026-10-02", 9.23), ("2026-10-07", 9.50),
                 ("2026-10-08", 9.55), ("2026-10-09", 9.60)):
        put("fred.ccc_oas", d, c)
    for d, b in (("2026-10-01", 2.10), ("2026-10-02", 2.11), ("2026-10-07", 2.20),
                 ("2026-10-08", 2.21)):
        put("fred.bb_oas", d, b)
    with observations.ObservationStore(db) as st:
        st.write_many(rows)
        cur, prior, day = wsec.aligned_legs(st, "fred.ccc_oas", "fred.bb_oas",
                                            "2026-10-10T00:00:00+00:00",
                                            "2026-10-03T00:00:00+00:00")
    check(day == "2026-10-08" and cur == (9.55, 2.21) and prior == (9.23, 2.11),
          f"CCC less BB reads both legs on the latest date both have ({day}), never "
          f"CCC's 9 Oct against BB's 8 Oct")
    check("\"The front\" and \"the front end\" mean the 2-year" in sp.RULES
          and "give each its date" in sp.RULES,
          "the frames say the front is the 2-year and date figures that differ")
    t = {"columns": ["Series", "Level", "Week", "As of"],
         "rows": [["2s10s", "0.43%", "+10 bp", "2026-10-07"]]}
    m = fb.table_moves(t, "Plumbing", "Week")[0]
    check(fb.cite(m).get("as_of") == "2026-10-07",
          "a frame's figure carries its row's date")
    a = FIX["aliases"]

    def ed(tape_day):
        tt = {"columns": ["Market", "Last"],
              "rows": [["10-year yield", a["tape_10y"]["printed"]]]}
        cons.tag(tt, 0, 1, cons.fact_key("y10", tape_day, "level"), True)
        return {"sections": [{"id": "tape", "title": "The tape", "table": tt}]}
    c10 = a["chart_10y"]
    chart = {"W3": {"caption": f"Treasury yields; 10-year {c10['printed']} "
                               f"({c10['source']}, {c10['as_of']})",
                    "levels": [{"series": "fred.yield_10y", "as_of": c10["as_of"],
                                "value": c10["value"], "printed": c10["printed"],
                                "source": c10["source"]}]}}
    log = cons.reconcile_aliases(ed(a["tape_10y"]["as_of"]), chart)
    check(any(e["verdict"] == "different dates" for e in log),
          "5.244% (9 Oct) and 5.28% (FRED, 7 Oct): different dates, not compared")
    gap = {"W3": {**chart["W3"], "levels": [{**chart["W3"]["levels"][0],
                                             "value": a["same_date_gap"]["value"],
                                             "printed": a["same_date_gap"]["printed"]}]}}
    gap["W3"]["levels"][0]["as_of"] = a["tape_10y"]["as_of"]
    gap["W3"]["caption"] = (f"Treasury yields; 10-year {a['same_date_gap']['printed']} "
                            f"(FRED, {a['tape_10y']['as_of']})")
    try:
        cons.reconcile_aliases(ed(a["tape_10y"]["as_of"]), gap)
        raised = False
    except cons.EditionInconsistent:
        raised = True
    check(raised, "the same date with a 4 bp gap fails the run")
    near = {"W3": {**gap["W3"], "levels": [{**gap["W3"]["levels"][0], "value": 5.26,
                                            "printed": "5.26%"}]}}
    check(not [e for e in cons.reconcile_aliases(ed(a["tape_10y"]["as_of"]), near,
                                                 fail=False) if e["verdict"] == "beyond"],
          "a 2 bp gap at one date is two measurements of one instrument, inside "
          "the 3 bp tolerance")
    bare = {"W3": {**chart["W3"], "caption": "Treasury yields; 10-year 5.28% (7 Oct)"}}
    try:
        cons.reconcile_aliases(ed(a["tape_10y"]["as_of"]), bare)
        raised = False
    except cons.EditionInconsistent:
        raised = True
    check(raised, "a chart caption without its source fails")
    from daily_cascade import charts as charts_mod
    src = Path(charts_mod.__file__).read_text(encoding="utf-8")
    check("(FRED, {v[-1][0]})" in src, "W3's caption names FRED beside each yield's date")


# ---------------------------------------------------------------------------
# G. THE MONTHLY'S PROSE PATH (W-1.1b)
# ---------------------------------------------------------------------------
def run_monthly(sections: list, drafts: list, kind: str = "stack") -> tuple:
    """monthly_macro.prose.write_all over one frame of the first section, with
    the model replaced by `drafts` in order; no store, no network, no model."""
    from daily_cascade import narrative as base
    from monthly_macro import prose as mp
    seen: list = []
    real, real_states = base.generate, mp._market_states

    def fake(payload, **kw):
        seen.append(kw.get("system_prompt") or "")
        return Reply(drafts[min(len(seen) - 1, len(drafts) - 1)])
    base.generate, mp._market_states = fake, (lambda p: None)
    try:
        ed = {"month": "September 2026", "sections": sections}
        s = sections[0]
        sec = {"key": f"stack:{s['id']}", "title": s["title"], "kind": kind,
               "sid": s["id"], "system": "fixture frame", "slice": {},
               "max_chars": 4000, "scope": "", "paragraphs": "2"}
        out = mp.write_all({}, client=object(), ed=ed, secs=[sec])
    finally:
        base.generate, mp._market_states = real, real_states
    return out[sec["key"]], seen


def monthly_plumbing() -> dict:
    from monthly_macro import prose as mp
    mv = FIX["direction"]["moves"]
    rows = [[n, "—", v[1], DAY] for n, v in mv.items()]
    return {"id": "plumbing", "title": "Plumbing & rates", "depth": "deep", "items": [],
            "table": {"columns": ["Series", "Level", mp.MONTH_COLUMN, "As of"],
                      "rows": rows},
            "subsections": [], "data": {}}


def group_g() -> None:
    print(f"\n{LINE}\nG. THE MONTHLY'S PROSE PATH (W-1.1b)\n{LINE}")
    from monthly_macro import prose as mp
    d, r = FIX["direction"], FIX["readability"]
    sec = monthly_plumbing()
    moves = direction.edition_moves({"sections": [sec]}, "plumbing", mp.MONTH_COLUMN)
    check(moves.get("DXY", (None,))[0] == 0.27 and len(moves) == 4,
          f"the Monthly's moves are read from its month column "
          f"({mp.MONTH_COLUMN!r}: {sorted(moves)})")
    # 1. A paragraph that fails the direction audit: withheld on the Weekly's
    # message, retried with it, and the corrected draft prints.
    res, seen = run_monthly([sec], [d["plumbing_paragraph"], d["firmed_paragraph"]])
    check(res.get("attempts") == 2 and res.get("published")
          and d["expected_fault"] in (seen[1] if len(seen) > 1 else ""),
          f"a Monthly paragraph saying 'the dollar softened' against DXY +0.27% is "
          f"withheld on the same message, and the retry hears it "
          f"({res.get('attempts')} attempts)")
    res, _ = run_monthly([sec], [d["plumbing_paragraph"]])
    check(not res.get("published") and res.get("state") == "tape_rules"
          and res.get("attempts") == mp.ATTEMPTS and res.get("text") is None
          and d["expected_fault"] in str(res.get("reason")),
          f"a draft that fails every attempt is withheld, nothing printed "
          f"({res.get('attempts')} attempts)")
    # 2. "Bullish on inflation", in a stack frame and in a v2 section.
    stance_para = r["stance"] + " The dollar firmed against the euro."
    res, seen = run_monthly([sec], [stance_para, "Desks expect inflation to stay "
                                                 "above target as the curve repriced."])
    check(res.get("attempts") == 2 and res.get("published")
          and "bullish on inflation" in (seen[1] if len(seen) > 1 else "")
          and "stay above target" in str(res.get("text")),
          "'bullish on inflation' is withheld and the retry writes what is expected")
    res, _ = run_monthly([sec], [stance_para], kind="v2")
    check(not res.get("published")
          and "'bullish on inflation' -- a stance on a macro variable"
          in str(res.get("reason")),
          "a v2 section is held to the stance check too")
    # 3. "fell -3 bp" prints "fell 3 bp", after the audits, counted.
    three = {"2-year": (-3, "-3 bp", "bp"), "Real Estate": (3.36, "+3.36%", "%"),
             "CCC OAS": (37, "+37 bp", "bp")}
    sec3 = {**sec, "table": {"columns": ["Series", "Level", mp.MONTH_COLUMN, "As of"],
                             "rows": [[n, "—", v[1], DAY] for n, v in three.items()]}}
    res, _ = run_monthly([sec3], [r["signed_after_verbs"]])
    check(res.get("published") and res.get("text") == r["unsigned"]
          and res.get("unsigned_rewrites") == r["rewrites"],
          f"'fell -3 bp' prints 'fell 3 bp' and the rewrites are counted "
          f"({res.get('unsigned_rewrites')}): {str(res.get('text'))[:50]}")
    res, _ = run_monthly([sec3], [r["signed_after_verbs"]], kind="v2")
    check(res.get("published") and res.get("text") == r["unsigned"],
          "a v2 section's signs are rewritten the same way")
    # Every Monthly frame that has a section is held to its moves: a block's and
    # a summary's are their parent section's.
    blk = {"sid": "plumbing", "key": "block:plumbing:x"}
    check(mp.direction_faults("The dollar softened.", blk, {"sections": [sec]})
          and not mp.direction_faults("The dollar softened.", blk, {}),
          "a block frame reads its parent section's moves; no edition, no audit")


RUN6 = json.loads((REPO / "tests" / "fixtures" / "weekly_run6_2026-10-13.json")
                  .read_text(encoding="utf-8"))


def run6_moves() -> dict:
    return {n: (direction._parse(c)[0], c, direction._parse(c)[1])
            for n, c in RUN6["plumbing"]["moves"]}


def run6_plumbing() -> dict:
    rows = [[n, "—", c, DAY] for n, c in RUN6["plumbing"]["moves"]]
    return {"id": "plumbing", "title": "Plumbing & rates", "depth": "deep", "items": [],
            "table": {"columns": ["Series", "Level", "Week", "As of"], "rows": rows},
            "subsections": [], "data": {}}


def group_h() -> None:
    print(f"\n{LINE}\nH. W-1.3c ITEM 1: A SIGN BEFORE A CURRENCY SYMBOL (dry run #6)\n{LINE}")
    mv = run6_moves()
    check(mv["Reverse repo (RRP)"][:1] == (-1e9,) and mv["Reverse repo (RRP)"][2] == "$",
          "the run-6 table's '−$1bn' reads as -1e9 in dollars")
    cl = RUN6["plumbing"]["clause"]
    check(direction.faults(cl, mv) == [],
          f"'{cl}' passes (run 6 withheld it: {RUN6['plumbing']['withheld']})")
    check(direction.faults(cl.replace("−", "-"), mv) == [],
          "and with a hyphen for the minus")
    check(direction.faults(cl.replace("fell", "rose"), mv),
          "'rose −$1bn' fails: a rise word with a fall")
    check(direction.faults("Bank reserves rose +$82bn.", mv) == []
          and direction.faults("Bank reserves fell +$82bn.", mv),
          "'+$82bn' reads as a rise: 'rose' passes, 'fell' fails")
    eu = {"ECB deposits (euro)": (-2e9, "−€2bn", "€"), "BoE reserves": (5e9, "+£5bn", "£"),
          "BoJ current accounts": (-3e12, "−¥3tn", "¥")}
    check(direction.faults("ECB deposits fell −€2bn.", eu) == []
          and direction.faults("ECB deposits rose −€2bn.", eu)
          and direction.faults("BoE reserves rose +£5bn.", eu) == []
          and direction.faults("BoE reserves fell +£5bn.", eu)
          and direction.faults("BoJ current accounts fell -¥3tn.", eu) == []
          and direction.faults("BoJ current accounts rose −¥3tn.", eu),
          "the euro, pound and yen signs read the same way")
    check(fb.parse_figure("−€1bn") == (-1e9, "€") and fb.parse_figure("+£2m") == (2e6, "£")
          and fb.parse_figure("−$68bn") == (-68e9, "$"),
          "figure_budget.parse_figure keeps each currency as its unit")
    check(readability.figures("fell −€1bn and +$82bn") == ["-€1bn", "+$82bn"],
          "the figure counter reads a sign before any of the four symbols")
    ed, seen = run_write([run6_plumbing()], [shaped(cl, "deep")])
    pr = ed["prose"]["plumbing"]
    check(pr.get("published") and pr.get("attempts") == 1,
          f"through the pipeline the run-6 clause publishes first time "
          f"({pr.get('reason')})")

    print(f"\n{LINE}\nI. W-1.3c ITEM 6: A RETRY CARRIES THE REASON AND THE RULE\n{LINE}")
    bad = shaped("Reverse repo fell −$1bn the same day.", "deep").replace(
        "the coming auctions are its test.", "the coming auctions are its 2.5% test.")
    good = shaped("Reverse repo fell −$1bn the same day.", "deep")

    def obeying(after: int):
        """A fake model that writes the faulty draft until a prompt carries the
        Takeaway fault AND its rule, from attempt `after` on."""
        from daily_cascade import narrative as base
        seen2: list = []
        real = base.generate

        def fake(payload, **kw):
            sysp = kw.get("system_prompt") or ""
            if "THE SECTION: Plumbing" not in sysp:
                return Reply(good)                  # The read's own call
            seen2.append(sysp)
            heard = ("restates figures" in sysp and "THE TAKEAWAY RULE" in sysp)
            return Reply(good if heard and len(seen2) >= after else bad)
        return real, fake, seen2

    from daily_cascade import narrative as base
    for after, want in ((2, (True, 2)), (99, (False, 2))):
        real, fake, seen2 = obeying(after)
        base.generate = fake
        try:
            ed = {"session": DAY, "sections": [
                {"id": "read", "title": "The read", "depth": "deep", "items": [],
                 "table": None, "subsections": [], "data": {}, "empty": True},
                {"id": "tape", "title": "The tape", "depth": "deep", "items": [],
                 "table": None, "subsections": [], "data": {}, "empty": True},
                run6_plumbing()]}
            sp.write(ed, client=object(), cadence="weekly")
        finally:
            base.generate = real
        pr = ed["prose"]["plumbing"]
        if want[0]:
            check(pr.get("published") and pr.get("attempts") == 2 and len(seen2) == 2
                  and "restates figures" in seen2[1] and "THE TAKEAWAY RULE" in seen2[1],
                  f"a model that obeys the reason on attempt 2 publishes "
                  f"({pr.get('attempts')} attempts)")
        else:
            # W8-1: one revision, told the draft, then withheld.
            check(not pr.get("published") and pr.get("attempts") == 2
                  and len(seen2) == 2 and "attempt 1 of 2" in seen2[1]
                  and "YOUR DRAFT:" in seen2[1]
                  and ed["sections"][2].get("withheld"),
                  f"one that never does is withheld after its one revision "
                  f"({pr.get('attempts')})")
    late = ("withheld: filler sentence: 'a'; filler sentence: 'b'; the paragraph "
            "cites 9 figures; at most 6 -- the tables carry the rest; direction "
            "audit failed on 1 clause: 'x'; " + RUN6["ahead_withheld"])
    rp = sp.retry_prompt("SYS", late, 2, 3)
    check(RUN6["ahead_withheld"] in rp and "THE TAKEAWAY RULE" in rp
          and "THE FILLER RULE" in rp and "THE FIGURE BUDGET" in rp
          and "THE DIRECTION RULE" in rp and "WITHHELD BY THE AUDIT" in rp,
          "a fifth fault (run 6's Ahead Takeaway) reaches the retry whole, with "
          "the rule behind each kind of fault")
    check(any(k in sp.retry_prompt("S", "narrative withheld: numeral audit failed "
                                   "on 1 figure (9.9%)") for k in ("THE NUMERAL RULE",)),
          "a numeral-audit withhold carries the numeral rule")
    from daily_cascade import cadence as cad_mod
    check(sp.attempts_of(cad_mod.get("weekly")) == 2
          and sp.attempts_of(cad_mod.get("daily")) == 2,
          "one draft and one revision at every cadence (W8-1; the Weekly's three "
          "withdrawn)")


# ---------------------------------------------------------------------------
# J. THE MONTHLY POLISH FROM DRY RUN #5 (T3.6)
# ---------------------------------------------------------------------------
M5 = json.loads((REPO / "tests" / "fixtures" / "monthly_run5_2026-10-13.json")
                .read_text(encoding="utf-8"))


class TooLong:
    """A reply the length guard refused, as narrative.generate returns it."""
    def __init__(self, text):
        self.published, self.text, self.model = False, None, "fixture"
        self.state, self.reason = "too_long", f"ran past the cap ({len(text)} chars)"
        self.rejected_text = text

    def withheld_note(self):
        return f"narrative withheld: {self.reason}"


def run_frame(sec_def: dict, drafts: list, ed: dict, kind: str = "stack",
              max_chars: int = 4000) -> tuple:
    """monthly_macro.prose.write_all over ONE frame, the model replaced by
    `drafts` (a str is a published reply, a TooLong a refused one)."""
    from daily_cascade import narrative as base
    from monthly_macro import prose as mp
    seen: list = []
    real, real_states = base.generate, mp._market_states

    def fake(payload, **kw):
        seen.append(kw.get("system_prompt") or "")
        d = drafts[min(len(seen) - 1, len(drafts) - 1)]
        return d if isinstance(d, TooLong) else Reply(d)
    base.generate, mp._market_states = fake, (lambda p: None)
    try:
        sec = {"kind": kind, "system": "fixture frame", "max_chars": max_chars,
               "scope": "", "paragraphs": "2", **sec_def}
        out = mp.write_all({}, client=object(), ed=ed, secs=[sec])
    finally:
        base.generate, mp._market_states = real, real_states
    return out[sec["key"]], seen


def group_j() -> None:
    print(f"\n{LINE}\nJ. THE MONTHLY POLISH FROM DRY RUN #5 (T3.6)\n{LINE}")
    from monthly_macro import prose as mp
    from monthly_macro import stack as ms
    col = mp.MONTH_COLUMN

    # M1 -- the role audit -------------------------------------------------
    m1 = M5["m1_roles"]
    pay = {"long_frame": m1["long_frame"]}
    for k in ("summary_quoted", "section2_quoted"):
        f = na.role_faults(m1[k], pay)
        check(f and "40-week average, an average, not a close" in f[0]
              and f[0].count("an average, not a close") == 3,
              f"M1: run 5's '{m1[k][:46]}...' is withheld: three averages cited as "
              f"closes")
    check(not na.role_faults(m1["correct"], pay)
          and not na.role_faults(m1["average_named"], pay),
          "M1: the close as a close, and an average named as one, pass")
    tbl = {"columns": ["Market", "Month-end close", "40-week (≈200-day) average"],
           "rows": [["Gold", "4,640.10", "4,554.56"]]}
    check(na.role_faults(m1["summary_quoted"], {"table": tbl}),
          "M1: a table cell takes its column's role")
    tape = {"id": "tape", "title": "The tape", "depth": "deep", "items": [],
            "subsections": [], "data": pay, "table": None}
    res, seen = run_frame({"key": "summary:tape", "title": "Summary: The tape",
                           "sid": "tape", "slice": pay},
                          [m1["summary_quoted"], m1["correct"]], {"sections": [tape]})
    check(res.get("published") and res.get("attempts") == 2
          and "role audit failed" in (seen[1] if len(seen) > 1 else ""),
          "M1: the summary paragraph is withheld, the retry hears which average it "
          "was, and the corrected draft prints")
    lf = ms.tape_section({"month_in_markets": {"rows": [], "end": "2026-09-30"}},
                         {"instruments": [{"label": "Gold", "frame": {"last": 4640.1},
                                           "row": {"drawdown_52w_pct": -1.4},
                                           "levels": [{"type": "ma_40w", "value": 4554.56,
                                                       "label": "40-week"}]}]})
    roles = lf["data"].get("long_frame_columns") or {}
    check("AVERAGE" in roles.get("ma_40w", "") and "close" in roles.get("close", "")
          and "AVERAGES" in mp.MONTHLY_NOTES.get("tape", ""),
          "M1: the long frame names each column's role, and the tape's frame says so")
    check(mp.ROLE_RULE in mp.T36_RULES and mp.system_prompt("x", "y").count(
        "bind ONLY to a close") == 1,
          "M1: every Monthly frame carries the role rule")
    # B84 (the 28 Oct dry run) -- looking_ahead: a day of the month is not a close.
    avg = {"slice": {"long_frame": [{"market": "10-year yield", "close": None,
                                     "ma_40w": 4.48},
                                    {"market": "SPY", "close": None,
                                     "ma_40w": 721.82}],
                     "fees": [{"label": "Bitcoin fee, one-hour tier (sat/vB)",
                               "long_run_average": 1.2}]}}
    ahead = ("December closes the quarter with its own concentration of risk: ISM "
             "Manufacturing on the 1st, ISM Services on the 3rd, payrolls on the "
             "4th, AVGO earnings and the FOMC statement both on the 9th.")
    # A91 (D42.8): A88 ended the role audit's span at a colon and taught it to
    # skip a date's numerals, so the role audit ALONE no longer binds these
    # ordinals either; B84's mask in the Monthly's wiring is now belt and braces.
    # The audit still flags a real average written as a close.
    check(not mp.t36_faults(ahead, avg, {})
          and not na.role_faults(ahead, avg["slice"])
          and na.role_faults("SPY closed the month at 721.82.", avg["slice"]),
          "B84 with A88: looking_ahead's calendar ('closes the quarter ... on the 1st "
          "... the 4th') passes the Monthly's role check and the role audit alone; "
          "SPY's 40-week average written as its close is still withheld")
    check(mp.t36_faults("SPY closed September 2026 at 721.82, with the 10-year "
                        "yield at 4.48.", avg, {})
          and mp.t36_faults("The tape closed the 4th week with SPY at 721.82.",
                            avg, {}),
          "B84: an average written as a close is still withheld, beside a masked "
          "ordinal too (stack:tape's dry-run sentence)")
    # B84 -- stack:tape: no close held, so the row says so and the frame says what
    # to do; a held close is unchanged.
    lf2 = ms.tape_section({"month_in_markets": {"rows": [], "end": "2026-09-30"}},
                          {"instruments": [
                              {"label": "SPY", "frame": {"last": None}, "row": {},
                               "levels": [{"type": "ma_40w", "value": 721.82,
                                           "label": "40-week"}]},
                              {"label": "Gold", "frame": {"last": 4640.1}, "row": {},
                               "levels": [{"type": "ma_40w", "value": 4554.56,
                                           "label": "40-week"}]}]})
    rows = {r["market"]: r for r in lf2["data"]["long_frame"]}
    check("close_absent" in rows["SPY"] and "close_absent" not in rows["Gold"]
          and "close_absent" in mp.MONTHLY_NOTES.get("tape", ""),
          "B84: a market with no month-end close says so in the long frame's data, "
          "and the tape's frame tells the writer to write no close for it")

    # M2 -- one direction per instrument across the summary ------------------
    m2 = M5["m2_consistency"]
    t2 = {"id": "tape", "title": "The tape", "depth": "deep", "items": [],
          "subsections": [], "data": {},
          "table": {"columns": ["Market", "Close", col],
                    "rows": [["Gold", "4,640.10", m2["moves"]["Gold"][1]],
                             ["DXY", "101.45", m2["moves"]["DXY"][1]]]}}
    p2 = {"id": "plumbing", "title": "Plumbing & rates", "depth": "deep", "items": [],
          "subsections": [], "data": {},
          "table": {"columns": ["Series", "Level", col], "rows": [["10-year", "4.59%",
                                                                    "+54 bp"]]}}
    ed2 = {"month": "September 2026", "sections": [t2, p2]}
    w = {"summary:tape": {"published": True, "text": m2["paragraph_a"]},
         "summary:plumbing": {"published": True, "text": m2["paragraph_b"]}}
    bad = mp.summary_conflicts(w, ed2)
    check(list(bad) == ["summary:plumbing"] and "'holding' (flat)" in bad["summary:plumbing"]
          and "Gold -1.20%" in bad["summary:plumbing"]
          and "'held its gains' (flat)" in bad["summary:plumbing"],
          "M2: gold 'pulling back' and 'holding its level', the dollar 'firmed' and "
          "'held': the paragraph against the month's signs is the one rewritten")
    from daily_cascade import narrative as base
    real, real_st = base.generate, mp._market_states
    try:
        mp._market_states = lambda p: None
        base.generate = lambda payload, **kw: Reply(m2["paragraph_b_fixed"])
        out = mp.reconcile_summary({}, w, ed2, client=object())
        ok_fix = (out["summary:plumbing"].get("published")
                  and out["summary:plumbing"].get("consistency_retry"))
        base.generate = lambda payload, **kw: Reply(m2["paragraph_b"])
        out2 = mp.reconcile_summary({}, w, ed2, client=object())
    finally:
        base.generate, mp._market_states = real, real_st
    check(ok_fix and out["summary:tape"]["text"] == m2["paragraph_a"],
          "M2: rewritten once with the reason, the agreeing paragraph prints")
    check(not out2["summary:plumbing"].get("published")
          and out2["summary:plumbing"].get("state") == "inconsistent",
          "M2: a paragraph still in conflict is withheld")

    # M3 -- the one page, de-duplicated and capped ---------------------------
    m3 = M5["m3_duplication"]
    page = {"title": "The month in one page", "phase": "month_in_one_page",
            "paragraphs": list(m3["one_page"])}
    ed3 = {"sections": [{"id": "read", "title": "The read", "subsections": [page]}],
           "summary": [{"id": "read", "text": " ".join(m3["summary"])}]}
    ms.dedup_one_page(ed3)
    got = page["paragraphs"]
    check(got == m3["one_page"][2:5] and ed3["one_page_dedup"]["summary"] >= 2
          and ed3["one_page_dedup"]["itself"] >= 1,
          f"M3: the one page drops what the summary says and what it says twice "
          f"({ed3['one_page_dedup']}): {len(got)} paragraphs left")
    page2 = {"phase": "month_in_one_page", "paragraphs": [
        "Gold rallied on central-bank buying through the month.",
        "Payrolls disappointed and the front end repriced cuts.",
        "Oil slid as OPEC added barrels into a soft market.",
        "Volatility sellers returned once the auctions cleared.",
        "Credit issuance hit a record as spreads stayed tight.",
        "Emerging currencies weakened against a firmer yen."]}
    ed3b = {"sections": [{"id": "read", "subsections": [page2]}], "summary": []}
    ms.dedup_one_page(ed3b)
    check(len(page2["paragraphs"]) == ms.ONE_PAGE_MAX == 5
          and any("Cut to 5 paragraphs" in n for n in page2.get("notes") or []),
          "M3: the one page is capped at five paragraphs (decision 8), and says so")
    one = next(x for x in mp.plan({}) if x["key"] == "month_in_one_page")
    check(one["paragraphs"] == "exactly 5" and "Five takeaways" in one["scope"]
          and "Say each thing once" in one["scope"],
          "M3: its frame asks for five takeaways, each said once")

    # M4 -- a derived change equals its legs' --------------------------------
    m4 = M5["m4_derived"]
    legs = {k: round((v["now"] - v["then"]) * 100, 1) for k, v in m4["legs"].items()}
    ok, ch, diff = ms.derived_check(m4["stored"]["now"], m4["stored"]["then"],
                                    {"10-year": legs["10-year"], "2-year": legs["2-year"]})
    check(not ok and round(ch) == 83 and diff == 0,
          f"M4: run 5's 2s10s +{ch:.0f} bp against legs of +54 bp each fails the check")
    import gate_tmp
    from altdata import observations
    db = str(Path(gate_tmp.mkdtemp("validate_audit_fixes_h_")) / "h.db")
    rows = []
    for key, v in (("fred.yield_10y", m4["legs"]["10-year"]),
                   ("fred.yield_2y", m4["legs"]["2-year"])):
        for d, x in (("2026-08-31", v["then"]), ("2026-09-30", v["now"])):
            rows.append({"registry_key": key, "instrument": None, "observed_at": d,
                         "available_at": f"{d}T22:00:00+00:00", "value": x,
                         "source": "synthetic"})
    with observations.ObservationStore(db) as st:
        st.write_many(rows)
        b = {"table": {"rows": [["2s10s", "47 bp", "+83 bp", "2026-09-30"]]},
             "data": {"series": {"2s10s": {"change": 83}}}, "items": []}
        ms.derived_rows(b, st, "2026-10-01T12:00:00+00:00", "2026-08-31T23:59:59+00:00")
    r = b["table"]["rows"][0]
    check(r[1] == "47 bp" and "+83" not in r[2] and r[3] == "2026-09-30"
          and b["data"]["series"]["2s10s"]["change_bp"] == 0.0,
          f"M4: built from aligned legs and a same-date prior, 2s10s reads its legs' "
          f"change: {r}")
    with observations.ObservationStore(db) as st:
        st.write_many([{"registry_key": "fred.yield_2y", "instrument": None,
                        "observed_at": "2026-09-30", "value": 4.30,
                        "available_at": "2026-09-30T23:00:00+00:00",
                        "source": "synthetic"}])
    import daily_cascade.weekly_sections as wsec
    real_al = wsec.aligned_legs
    try:
        wsec.aligned_legs = lambda st_, a, b_, n, t: ((4.59, 4.12), (4.05, 3.58),
                                                      "2026-09-30")
        with observations.ObservationStore(db) as st:
            b2 = {"table": {"rows": [["2s10s", "47 bp", "+83 bp", "2026-09-30"]]},
                  "data": {"series": {"2s10s": {}}}, "items": []}
            ms.derived_rows(b2, st, "2026-10-01T12:00:00+00:00",
                            "2026-08-31T23:59:59+00:00")
    finally:
        wsec.aligned_legs = real_al
    r2 = b2["table"]["rows"][0]
    check(r2[1] == "withheld" and "10-year +54" in r2[2] and "2-year +72" in r2[2]
          and "2s10s" not in b2["data"]["series"],
          f"M4: a change that is not its legs' is withheld with the legs printed: {r2[2]}")

    # M5 -- each gap's direction over the month ------------------------------
    m5 = M5["m5_gaps"]
    for g in m5["gaps"]:
        h = [("2026-08-29", g["z_month_start"]), ("2026-09-15", g["z_month_start"]),
             ("2026-09-29", g["z"] + (0.1 if g["z"] > 0 else -0.1)), ("2026-09-30", g["z"])]
        md = ms.month_direction(h, "2026-08-31T23:59:59+00:00")
        check(md and md[0] == "rising",
              f"M5: {g['gap']} reads 'rising' over the month (|z| {abs(g['z_month_start'])} "
              f"-> {abs(g['z'])}), though its last session fell")
    mis = {"id": "misfit", "title": "What doesn't fit", "depth": "deep", "items": [],
           "subsections": [], "table": None,
           "data": {"gaps": [{"gap": g["gap"], "z": g["z"], "direction": "rising"}
                             for g in m5["gaps"]]}}
    res, seen = run_frame({"key": "summary:misfit", "title": "Summary: misfit",
                           "sid": "misfit", "slice": {}},
                          [m5["summary_quoted_shape"], m5["fixed"]], {"sections": [mis]})
    check(res.get("published") and res.get("attempts") == 2
          and "direction audit failed on the gaps" in (seen[1] if len(seen) > 1 else ""),
          "M5: 'falling' against two gaps whose z rose is withheld; the retry prints")

    # M6 -- Changed since last Monthly, summarised ----------------------------
    m6 = M5["m6_changed"]
    rws = [dict(r, source=None) for r in m6["keep"]]
    rws += [{"what": "forecast emitted", "to": f"p 0.6: claim {i}"}
            for i in range(m6["forecasts_emitted"])]
    rws += [{"what": "forecast resolved", "probability": pr, "outcome": oc,
             "to": f"outcome {oc}"} for pr, oc in m6["forecasts_resolved"]]
    rws += [{"what": f"decision {i} {d}", "to": st_} for i, d, st_ in m6["decisions"]]
    lines, ids = ms.changed_since({"looking_back": {"what_changed": {"rows": rws}}})
    check(len(lines) == 5 and m6["expected_forecast_line"] in lines
          and m6["expected_decision_line"] in lines
          and all(any(k["what"] in ln for ln in lines) for k in m6["keep"])
          and len(ids) == len(rws),
          f"M6: {len(rws)} rows print as 5 lines -- the dial, dimension and exception "
          f"kept; '{m6['expected_forecast_line']}' '{m6['expected_decision_line']}'")

    # M7 -- a small count in words --------------------------------------------
    m7 = M5["m7_counts"]
    payload = {"meetings": [{"meeting": "2026-10-28", "p_cut": 0.6}] * 4,
               "watched": 4}
    check(not na.audit(m7["bare"], payload).passed and na.audit(m7["words"], payload).passed,
          "M7: '2 of the next four meetings' fails the numeral audit; 'two' is exempt")
    check(mp.COUNT_RULE in mp.T36_RULES and "in words" in mp.COUNT_RULE,
          "M7: the frames ask for small counts in words")

    # M8 -- too long, retried tighter; the narratives' sources ----------------
    m8 = M5["m8_length"]
    res, seen = run_frame({"key": "summary:ahead", "title": "Summary: Ahead",
                           "sid": "ahead", "slice": {}, "max_chars": 1400},
                          [TooLong("x" * m8["long_draft_chars"]), m8["short_draft"]],
                          {"sections": []})
    check(res.get("published") and res.get("attempts") == 2
          and "at most 980 characters" in (seen[1] if len(seen) > 1 else ""),
          "M8: a 'too_long' summary is retried once, told a tighter cap (980 of 1,400)")
    res, seen = run_frame({"key": "summary:ahead", "title": "Summary: Ahead",
                           "sid": "ahead", "slice": {}, "max_chars": 1400},
                          [TooLong("x" * 1600)], {"sections": []})
    check(not res.get("published") and res.get("attempts") == 2 and len(seen) == 2,
          "M8: and only once")
    nar = {"id": "narratives", "title": "Narratives", "depth": "deep", "items": [],
           "subsections": [], "data": {}, "table": None}
    plan = {x["key"]: x for x in mp.summary_plan({"sections": [nar, t2]})}
    check(mp.SOURCE_RULE in plan["summary:narratives"]["system"]
          and mp.SOURCE_RULE not in plan["summary:tape"]["system"],
          "M8: the narratives' summary frame requires the source beside every delta")

    # M9 -- the display form ---------------------------------------------------
    m9 = M5["m9_display"]
    res, seen = run_frame({"key": "theme:crypto", "title": "Crypto", "sid": "x",
                           "slice": {"bitcoin": {"level": 83553.85,
                                                 "latest_level_display": "83,553.85"},
                                     "index": {"level": 7651.54}}},
                          [m9["text"], m9["fixed"]], None, kind="v2")
    check(res.get("published") and res.get("attempts") == 2
          and "'83553.85' (write '83,553.85'" in (seen[1] if len(seen) > 1 else "")
          and "'7651.54' (write '7,651.54'" in (seen[1] if len(seen) > 1 else ""),
          "M9: '83553.85' and '7651.54' are withheld and the retry hears the table's "
          "form; '83,553.85' prints")
    check(not na.separator_faults("Payrolls in 2026 rose 120,000; 2s10s at 47 bp."),
          "M9: a year and a name with digits are not figures")

    # M10 -- two dollar series, each by its name --------------------------------
    m10 = M5["m10_dollar"]
    lfd = {"long_frame": [{"market": "DXY", "close": 101.45, "ma_40w": 99.35}]}
    ttd = {"table": {"columns": ["Market", "Close, 2026-09-30", "Move"],
                     "rows": [["Dollar (FRED broad index)", "120.97", "+0.40%"]]}}
    both = [lfd, ttd]
    check(mp.dollar_label_faults(m10["bare_a"], both)
          and mp.dollar_label_faults(m10["bare_b"], both),
          "M10: 'the dollar' beside DXY's 101.45 or the broad index's 120.97 is withheld "
          "where both print")
    check(not mp.dollar_label_faults(m10["named_a"], both)
          and not mp.dollar_label_faults(m10["named_b"], both)
          and not mp.dollar_label_faults(m10["bare_a"], [lfd]),
          "M10: each named passes, and with one dollar series 'the dollar' is its alias")
    res, seen = run_frame({"key": "summary:read", "title": "Summary: The read",
                           "sid": "read", "slice": {}, "audit_extra": both},
                          [m10["bare_a"], m10["named_a"]],
                          {"sections": [{"id": "tape", "title": "The tape",
                                         "data": lfd, "table": ttd["table"]}]})
    check(res.get("published") and res.get("attempts") == 2
          and "name the series" in (seen[1] if len(seen) > 1 else ""),
          "M10: the summary is withheld and retried until the series is named")


# ---------------------------------------------------------------------------
# K. THE MONTHLY'S BINDING FROM THE 28 OCT DRY RUN (A88)
# ---------------------------------------------------------------------------
# Every withheld draft A88 owns, as a sentence over a block in the rows' real
# labels (tests/fixtures/monthly_dryrun_2026-10-28.json): each passes now, and
# each must-fail case -- a wrong figure in its own clause, under a derived name,
# in its own tag, or an average called a close -- still fails.
M28 = json.loads((REPO / "tests" / "fixtures" / "monthly_dryrun_2026-10-28.json")
                 .read_text(encoding="utf-8"))


def group_k() -> None:
    print(f"\n{LINE}\nK. THE MONTHLY'S BINDING FROM THE 28 OCT DRY RUN (A88)\n{LINE}")
    for c in M28["binding_pass"]:
        a = na.audit(c["text"], c["block"])
        check(a.passed, f"passes: {c['case']} ({a.reason()[:120]})")
    for c in M28["binding_fail"]:
        a = na.audit(c["text"], c["block"])
        check(not a.passed and "is bound to" in a.reason(),
              f"still fails: {c['case']} ({a.reason()[:120]})")
    for c in M28["role_pass"]:
        f = na.role_faults(c["text"], M28["role_payload"])
        check(not f, f"the role audit passes: {c['case']} ({(f or [''])[0][:120]})")
    for c in M28["role_fail"]:
        check(bool(na.role_faults(c["text"], M28["role_payload"])),
              f"the role audit still fails: {c['case']}")


# ---------------------------------------------------------------------------
# L. THE MONTHLY'S BINDING FROM THE 29 OCT DRY RUN (A90)
# ---------------------------------------------------------------------------
# Dry run #2's false positives, as sentences over blocks in the rows' real
# labels (tests/fixtures/monthly_dryrun_2026-10-29.json): each passes, each
# must-fail case beside it fails, and summary:tape -- averages written as closes
# -- passes the binding only to be withheld by the role audit.
M29 = json.loads((REPO / "tests" / "fixtures" / "monthly_dryrun_2026-10-29.json")
                 .read_text(encoding="utf-8"))


def group_l() -> None:
    print(f"\n{LINE}\nL. THE MONTHLY'S BINDING FROM THE 29 OCT DRY RUN (A90)\n{LINE}")
    for c in M29["binding_pass"]:
        a = na.audit(c["text"], c["block"])
        check(a.passed, f"passes: {c['case']} ({a.reason()[:120]})")
    for c in M29["binding_fail"]:
        a = na.audit(c["text"], c["block"])
        check(not a.passed and "is bound to" in a.reason(),
              f"still fails: {c['case']} ({a.reason()[:120]})")
    t = M29["tape"]
    check(na.audit(t["text"], t["block"]).passed and na.role_faults(t["text"], t["block"]),
          "summary:tape's averages written as closes: the binding passes them, the "
          "role audit withholds them")


def main() -> int:
    print(f"{LINE}\nW-1.1a: THE AUDIT FIXES FROM THE 12 OCT DRY RUN\n{LINE}")
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g, group_h,
              group_j, group_k, group_l):
        g()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
