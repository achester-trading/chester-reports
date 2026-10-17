"""
Validation gate for W-1.2 -- the Weekly's storyline tranche (change order of 11 Oct
2026, section 3, items 2.1-2.8; ruling 5). On the Weekly's fixture payload
(tools/validate_weekly_stack.py's synthetic week), with a scripted writer; no
network, no box.

  A  THE PRÉCIS, WRITTEN LAST. Its call comes after every section's; it opens
     the edition, before section 1. Its figures are contained in the
     commentaries' cited set: a draft citing another is withheld and the retry
     publishes. Six verdicts in the fixed vocabulary; a confidence line naming
     evidence; three or four what-would-change items, each a series and a
     window; the outlook line ("first edition with a précis" with no prior, and
     required when a prior précis exists).
  B  THE STANCE. Written at publication to the probability ledger -- a dry run
     under its own namespace, never the live source -- with graded_source
     weekly_stance and the horizon a week on; printed "n=k, unvalidated"; graded
     by Brier when the next Weekly runs.
  C  THE RELEVANCE SENTENCE at the head of every present commentary.
  D  THE CONTRADICTION STATUS LINES. Every open contradiction carries one from
     the vocabulary; resolved (linked to its section), stale and carried each
     reached.
  E  THE BOOK'S TERMS. Section 10 ends with the band, the book's position and
     the précis's observables.
  F  COLLAPSE AND THE TERMS BOX. Silent and unreachable voices, a family of
     resolutions and an extreme the tape prints each collapse to one line, the
     rows to the reference tables; the terms box prints in full, verbatim.
  G  TAPE AND MECHANICS. The daily session tables print in one section only,
     Mechanics; the tape's named levels in the reference tables.
  H  PRESENTATION. No two-line chart title on the small multiples; every table
     row in the read path carries its unit.

    python tools/validate_weekly_storyline.py
"""

from __future__ import annotations

import os
import re
import sys
import types
from pathlib import Path

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import validate_weekly_stack as W                              # noqa: E402

LINE = "=" * 78
PASS = FAIL = 0


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


CHANGES = [("Initial jobless claims", "Thursday", "a jump would test the equities verdict"),
           ("CPI", "the coming Wednesday", "a hot print would test the rates verdict"),
           ("High-yield OAS", "through Friday", "a wider spread would confirm credit's "
                                                "side of the tension")]


# The précis's WEEK paragraph (W-1.3a item 3.0): inside the 150-250 band, no
# figure, ending in its Takeaway.
PRECIS_WEEK = (
    "The week's tension sat between two markets that usually agree. Equities held "
    "near their highs and kept their trend, while credit spreads, the extra yield "
    "investors demand to lend to riskier companies over the government, widened "
    "alongside them. When spreads widen, lenders are asking to be paid more for "
    "default risk, which is usually a warning that equity holders have not yet "
    "heard. On one side, the tape kept its trend through every session and the "
    "options market's hedging, which damps moves while the index sits above the "
    "level where dealers switch from selling rallies to chasing them, kept the "
    "swings small. On the other, the widening came from the lowest-rated borrowers "
    "first, which is where stress tends to show before it reaches the rest of the "
    "market. Neither side settled the question by the week's close, and the "
    "scheduled releases ahead fall on exactly the series that would. Takeaway: the "
    "equity trend deserves the benefit of the doubt only while credit stops "
    "widening, so the coming week's releases matter more for spreads than for "
    "stocks.")


def precis_reply(system: str, bad: bool = False) -> str:
    ids = re.findall(r"^RELEVANCE (\w+):", system, re.M)
    lines = ["WEEK: " + PRECIS_WEEK,
             "TENSION: Equities held near their highs alongside wider credit spreads.",
             "FOR: The tape kept its trend through the week.",
             "AGAINST: Credit spreads widened"
             + (" by +9.9%" if bad else "") + " alongside it.",
             "VERDICT equities: up", "VERDICT rates: chop", "VERDICT credit: transition",
             "VERDICT dollar: down", "VERDICT commodities: chop",
             "VERDICT volatility: up",
             "CONFIDENCE: The verdicts rest on the tape's trend, the credit spread and "
             "the dealer flip."]
    lines += [f"CHANGE: {a} | {b} | {c}" for a, b, c in CHANGES]
    if "OUTLOOK:" in system:
        lines.append("OUTLOOK: The view moved from steady to watchful.")
    lines.append("STANCE: p = 0.58")
    lines += [f"RELEVANCE {i}: This section bears on whether equities or credit has "
              f"the week right." for i in ids]
    return "\n".join(lines)


def client(calls: list):
    n = {"precis": 0}

    def create(**k):
        sysp = k["system"]
        calls.append(sysp)
        if sysp.startswith("You write the PRÉCIS"):
            n["precis"] += 1
            return W.Resp(precis_reply(sysp, bad=n["precis"] == 1))
        return W.Resp(W.OPENER_TEXT)
    return types.SimpleNamespace(messages=types.SimpleNamespace(create=create))


def main() -> int:
    from altdata import config, probability_ledger as pl
    from daily_cascade import charts as charts_mod, precis, storyline
    from daily_cascade import stack as stack_mod, stack_render, weekly_stack as ws
    print(f"{LINE}\nW-1.2 -- THE WEEKLY'S STORYLINE (synthetic week ending {W.ENDING})\n{LINE}")
    td = W.gate_mkdtemp(prefix="validate_weekly_storyline_")
    config.COMPUTED_DIR = str(Path(td) / "computed")
    db = str(Path(td) / "weekly.db")
    arch = str(Path(td) / "reports")
    logp = Path(td) / "attention-log.md"
    logp.write_text("| date | kind | minutes | note |\n|---|---|---|---|\n",
                    encoding="utf-8")
    seeded = W.seed(db)
    p = W.payload(seeded)
    calls: list = []
    out = ws.produce(p, archive_dir=arch, client=client(calls), db_path=db,
                     log_path=logp, dry_run=True)
    ed = out["edition"]
    html = out["html_email"]
    sec = {s["id"]: s for s in ed["sections"]}
    pr = ed.get("precis") or {}
    pp = pr.get("parsed") or {}

    # --- A ------------------------------------------------------------------
    print(f"\n{LINE}\nA. THE PRÉCIS, WRITTEN LAST\n{LINE}")
    first = next((i for i, c in enumerate(calls) if c.startswith("You write the PRÉCIS")),
                 None)
    check(first is not None and first == len(calls) - 2
          and all(not c.startswith("You write the PRÉCIS") for c in calls[:first]),
          f"the précis's calls come after every section's ({first} of {len(calls)})")
    i_p, i_1 = html.find('id="precis"'), html.find('id="sec-read"')
    check(pr.get("published") and 0 <= i_p < i_1,
          "it opens the edition, before section 1 (The read stays section 1)")
    fr = precis.frame(ed, None)
    allowed = {precis._norm(f) for f in fr["figures_you_may_cite"]}
    used = {precis._norm(f) for t in precis.prose_fields(pp) for f in precis._figs(t)}
    check(pr.get("attempts") == 2 and "figures no commentary cites"
          in str(pr.get("first_reason")) and used <= allowed,
          f"a draft citing a figure no commentary cites is withheld and the retry "
          f"publishes; its figures {sorted(used)} are within the commentaries' set")
    check(set(pp.get("verdicts") or {}) == {a for a, _, _ in precis.VERDICT_ASSETS}
          and all(v in precis.VERDICTS for v in pp["verdicts"].values()),
          f"six verdicts in the fixed vocabulary: {pp.get('verdicts')}")
    check(pp.get("confidence") and "rest on" in pp["confidence"],
          "a confidence line naming the evidence")
    ch = pp.get("change") or []
    check(3 <= len(ch) <= 4 and all(c["series"] and c["window"] for c in ch),
          f"{len(ch)} what-would-change items, each a series and a window")
    check(pp.get("outlook") == precis.FIRST_EDITION and precis.FIRST_EDITION in html,
          "with no prior précis: \"First archived edition with a précis.\"")
    prior = {"precis": {"parsed": dict(pp)}}
    fr2 = precis.frame(ed, prior)
    sys2 = precis.system_prompt(fr2)
    no_outlook = precis.parse(precis_reply(precis.system_prompt(fr)))
    check("OUTLOOK:" in sys2 and any("OUTLOOK" in f for f in precis.audit(no_outlook, fr2)),
          "with a prior précis the outlook line is asked for, and its absence withheld")
    bad = precis.parse(precis_reply(precis.system_prompt(fr)).replace(
        "VERDICT rates: chop", "VERDICT rates: sideways"))
    check(any("verdict for rates" in f for f in precis.audit(bad, fr)),
          "a verdict outside up / down / chop / transition is withheld")
    few = precis.parse("\n".join(l for l in precis_reply(precis.system_prompt(fr))
                                 .splitlines() if not l.startswith("CHANGE: CPI")
                                 and not l.startswith("CHANGE: High")))
    check(any("CHANGE lines" in f for f in precis.audit(few, fr)),
          "fewer than three what-would-change items is withheld")

    # --- B ------------------------------------------------------------------
    print(f"\n{LINE}\nB. THE STANCE\n{LINE}")
    with pl.ProbabilityLedger(db) as led:
        rows = led.all_rows()
    st_rows = [r for r in rows if r["source"].endswith(precis.STANCE_SOURCE)]
    check(len(st_rows) == 1 and st_rows[0]["source"] == "dryrun.weekly_stance"
          and st_rows[0]["horizon_date"] == precis.horizon(W.ENDING)
          and abs(st_rows[0]["probability"] - 0.58) < 1e-9,
          f"the dry run's stance is in its own namespace ({st_rows[0]['source'] if st_rows else None}),"
          f" horizon {precis.horizon(W.ENDING)}, p 0.58; the live source untouched")
    check(pr.get("stance_line") == "SPY higher at the next Weekly: p = 0.58 (n=0, "
          "unvalidated)." and pr["stance_line"] in html.replace("&#x27;", "'"),
          f"printed: {pr.get('stance_line')}")
    from altdata import observations
    with observations.ObservationStore(db) as st:
        hz = precis.horizon(W.ENDING)
        base = precis.spy_close(st, W.ENDING)
        st.write_many([{"registry_key": "yfinance.mkt_spy", "instrument": None,
                        "observed_at": hz, "available_at": f"{hz}T21:00:00+00:00",
                        "value": (base[1] if base else 600.0) + 5.0,
                        "source": "fixture"}])
        graded = precis.grade_stances(db, hz, st, True)
    check(len(graded) == 1 and graded[0]["outcome"] == 1
          and abs(graded[0]["brier"] - (1 - 0.58) ** 2) < 1e-9
          and precis.graded_n(db, True) == 1 and precis.graded_n(db, False) == 0,
          f"graded by Brier at the next Weekly: SPY higher, Brier "
          f"{graded[0]['brier'] if graded else None:.4f}; n counts its namespace only")

    # --- C ------------------------------------------------------------------
    print(f"\n{LINE}\nC. THE RELEVANCE SENTENCE\n{LINE}")
    present = [s for s in ed["sections"] if s.get("claim")]
    check(present and all(s.get("relevance") for s in present),
          f"every present commentary carries one ({len(present)} sections)")
    ok = True
    for n, s in enumerate(ed["sections"], start=1):
        if not s.get("claim"):
            continue
        h = html.find(f'id="sec-{s["id"]}"')
        r = html.find('class="relevance"', h)
        c = html.find(stack_render.esc(s["claim"]), h)
        nxt = html.find('id="sec-', h + 5)
        ok &= 0 <= h < r < c and (nxt == -1 or r < nxt)
    check(ok, "and it prints at the head of each, before the claim")

    # --- D ------------------------------------------------------------------
    print(f"\n{LINE}\nD. CONTRADICTION STATUS LINES\n{LINE}")
    gt = sec["misfit"].get("table") or {}
    stat = [r[-1] for r in gt.get("rows") or []]
    check(gt.get("columns", [""])[-1] == "Status" and stat
          and all(str(x).startswith(storyline.STATUSES) for x in stat),
          f"every open contradiction carries a status: {stat}")
    cfg = stack_mod.config()
    fake = {"sections": [{"id": "plumbing", "title": "Plumbing & rates", "claim": "x",
                          "table": {"columns": ["Series"], "rows": [
                              ["CCC OAS"], ["Investment-grade OAS"],
                              ["High-yield OAS"]]}}]}
    r1 = storyline.status_for({"id": "equities_vs_credit"}, {"sessions_open": 3,
                                                             "direction": "rising"},
                              fake, cfg)
    r2 = storyline.status_for({"id": "price_vs_breadth"}, {"sessions_open": 25,
                                                           "direction": "falling"},
                              fake, cfg)
    r3 = storyline.status_for({"id": "price_vs_breadth"}, {"sessions_open": 4,
                                                           "direction": "rising"},
                              fake, cfg)
    check(r1 == ("read in Plumbing & rates", "#sec-plumbing") and r2[0] == "stale"
          and r3[0].startswith("carried — resolves when"),
          f"resolved (linked), stale and carried: {r1[0]}; {r2[0]}; {r3[0][:50]}")
    t = {"columns": ["Gap", "Status"], "rows": [["x", r1[0]]],
         "cell_links": [[0, 1, "#sec-plumbing"]]}
    check('href="#sec-plumbing"' in stack_render._table(t),
          "the renderer links the evidence")

    # --- E ------------------------------------------------------------------
    print(f"\n{LINE}\nE. THE BOOK'S TERMS\n{LINE}")
    tl = (sec["book"].get("closing_lines") or [""])[0]
    check(tl.startswith("Stance:") and "regime band" in tl and "positioned" in tl
          and all(a in tl for a, _, _ in CHANGES), f"{tl[:160]}")
    enf = {"view": {"net_beta_pct": 30.0, "regime": {"regime": "Expansion",
                                                      "band": [40, 80]}}}
    tl2 = precis.terms_line(ed, enf)
    check("permits Book A a net beta of 40% to 80%" in tl2 and "30% net beta" in tl2
          and "cautious" in tl2, f"with a stored band: {tl2[:150]}")
    check(tl in html.replace("&#x27;", "'").replace("&quot;", '"'),
          "and section 10 prints it last")

    # --- F ------------------------------------------------------------------
    print(f"\n{LINE}\nF. COLLAPSE BY DEFAULT; THE TERMS BOX\n{LINE}")
    check(stack_render.esc(precis.TERMS_BOX) in html
          and html.find('id="terms"') < html.find('id="sec-read"'),
          "the terms box prints in full, verbatim, as page 2 before the sections")
    ved = {"sections": [{"id": "narratives", "table": {
        "columns": ["Voice", "View", "Status", "Source", "Horizon"],
        "rows": [["A", "v", "NEW", "s", "h"], ["B", "v", "SILENT", "s", "h"],
                 ["C", "v", "SILENT", "s", "h"], ["D", "v", "UNREACHABLE (x)", "s", "h"]]}}]}
    storyline.collapse_voices(ved)
    check(ved["sections"][0]["summarised"] == ["Voices: 2 silent, 1 unreachable."]
          and len(ved["sections"][0]["table"]["rows"]) == 1
          and len(ved["detail"][0]["table"]["rows"]) == 3,
          "silent and unreachable voices: one line, the rows in reference")
    cpi = [["Wed 14 Oct", "08:30", f"Prediction market resolves: Core CPI m/m above "
            f"{x}%?", 3, f"last {p_}%"] for x, p_ in (("0.1", 80), ("0.2", 55),
                                                      ("0.3", 20))]
    aed = {"sections": [{"id": "ahead", "table": {
        "columns": ["Day", "Time (ET)", "Event", "Importance", "Consensus / prior"],
        "rows": [["Tue 13 Oct", "10:00", "JOLTS", 2, "no consensus stored"]] + cpi}}]}
    storyline.collapse_families(aed, cfg)
    rows_a = aed["sections"][0]["table"]["rows"]
    check(len(rows_a) == 2 and "3 outcomes; modal: Core CPI m/m above 0.1%?" in rows_a[1][2]
          and "80%" in rows_a[1][4] and len(aed["detail"][0]["table"]["rows"]) == 3,
          f"a family of resolutions: one row, its modal outcome and probability "
          f"({rows_a[-1][2]}; {rows_a[-1][4]})")
    from altdata import labels
    lab = labels.exception("extreme:yfinance.mkt_spy")
    eed = {"sections": [{"id": "misfit", "data": {"_exception_ids": [
        "extreme:yfinance.mkt_spy", "extreme:fred.rrp"]}, "subsections": [
        {"title": "Exceptions open at week's end", "table": {
            "columns": ["Open", "What it is", "Opened", "Since"],
            "rows": [[lab, "extreme", "", "—"],
                     [labels.exception("extreme:fred.rrp"), "extreme", "", "—"]]}}]}]}
    storyline.collapse_exceptions(eed)
    check(eed["sections"][0]["summarised"] == [f"{lab} -- the tape prints it."]
          and len(eed["sections"][0]["subsections"][0]["table"]["rows"]) == 1,
          "an extreme the tape already prints: one line; the other stays a row")

    # --- G ------------------------------------------------------------------
    print(f"\n{LINE}\nG. TAPE AND MECHANICS\n{LINE}")
    check(storyline.daily_table_sections(ed) == ["mechanics"],
          f"the daily session tables print in one section only: "
          f"{storyline.daily_table_sections(ed)}")
    check(not any(ss.get("title") == "Levels" for ss in sec["tape"].get("subsections") or [])
          and any(d["title"] == "The tape: named levels" for d in ed.get("detail") or []),
          "the tape's named levels are in the reference tables")

    # --- H ------------------------------------------------------------------
    print(f"\n{LINE}\nH. PRESENTATION\n{LINE}")
    days = [f"2026-{m:02d}-{d:02d}" for m in range(1, 10) for d in (5, 12, 19, 26)]
    z = {"A long series name": [(d, float(i % 7)) for i, d in enumerate(days)],
         "B": [(d, float(i % 5)) for i, d in enumerate(days)]}
    bars = [{"observed_at": d, "close": 100 + i % 9} for i, d in enumerate(days * 7)]
    made = [charts_mod.z_panel("W4", z, "Speculative positioning (CFTC), z-scores",
                               "zp", None, subtitle="two years"),
            charts_mod.w8({k: bars for k in ("Bitcoin", "Gold", "DXY", "WTI",
                                             "10-year yield", "30-year yield")},
                          "w8", None),
            charts_mod.w3_panel({"10-year": [(d, 4.0) for d in days]},
                                [(d, 3.0) for d in days], "w3", None, "2026-09-30"),
            charts_mod.w10({"x": [(d, 0.5) for d in days]}, None, None, None,
                           "w10", None)]
    titles = [t for c in made for t in c.get("titles") or []]
    sup = [c["titles"][0] for c in made if c.get("titles")]
    check(len(made) == len([c for c in made if c.get("titles")])
          and all("\n" not in t for t in titles)
          and all(len(t) <= charts_mod.MAX_TITLE_CHARS for t in sup)
          and all(len(t) <= charts_mod.MAX_PANEL_TITLE_CHARS for t in titles
                  if t not in sup),
          f"no two-line chart title on the small multiples ({len(titles)} titles)")
    check("two years" in made[0]["caption"] and "126 sessions" in made[1]["caption"],
          "the subtitle is in the caption")
    miss = storyline.unitless_rows(ed)
    check(not miss, f"every table row in the read path carries its unit {miss[:4]}")
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
