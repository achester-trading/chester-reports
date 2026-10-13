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
            "subsections": [], "data": {"book_z": b["book_z"]}}


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
    ed2, seen = run_write([book_section()], [b["paragraph"]])
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
                         [d["plumbing_paragraph"], d["firmed_paragraph"]])
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
                      ["Plumbing turned on the long end. The 2-year fell -11 bp against a steady "
                       "long end."])
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


def main() -> int:
    print(f"{LINE}\nW-1.1a: THE AUDIT FIXES FROM THE 12 OCT DRY RUN\n{LINE}")
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g):
        g()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
