"""
Validation gate for W-1.3a item 3.0 -- THE SECTION OPENER (change order of 11 Oct
2026, section 4, amended 12 Oct). On the Weekly's fixture payload
(tools/validate_weekly_stack.py's synthetic week) with a scripted writer; no
network, no box.

  A  EVERY PRESENT COMMENTARY OPENS ITS SECTION. In the rendered Weekly, each
     section's commentary paragraph precedes its first table and its first
     chart; it starts with the précis's relevance sentence and ends with one
     sentence beginning "Takeaway", the word bolded; the writer's text sits in
     its depth's band (deep 120-220, medium 80-150).
  B  THE PRÉCIS LIKEWISE. Its WEEK paragraph opens the edition, sits in
     150-250 and ends in its Takeaway; a draft without one is withheld and the
     retry publishes.
  C  THE AUDIT. Out of band, no Takeaway, a Takeaway that is not last, two of
     them and a Takeaway carrying a figure are each refused; a section whose
     first draft lacks the Takeaway is retried and publishes.
  D  A WITHHELD COMMENTARY leaves the section's data in place, with the
     withholding line where the paragraph would be -- before the first table.
  E  THE FRAME carries the shape as instruction and as a worked example (no
     figures of its own); the tables are said to print BELOW; the close's and
     the Monthly's frames are untouched; the paragraph guard's cap is the band's
     top, so it never cuts a Takeaway.
  F  W-1.3c, THE POLISH FROM DRY RUN #6 (tests/fixtures/weekly_run6_2026-10-13.json):
     (2) an opener sentence that restates the terms box is withheld -- run 6's
     read opener fails, one that explains the week's own finding passes, and a
     draft that re-explains is retried with the reason and publishes; (5) a
     first sentence with its own section as subject is withheld -- run 6's eight
     fail, in the section and in the précis's relevance sentence, and the
     pipeline retries with the reason; (4) only "Takeaway:" is bold in an
     opener; (8) the précis's first sentence carries at most one figure -- run
     6's fails, the tension-first rewrite passes; (6) the précis retries up to
     three times with the reason and the rule; (10) the précis's page: no
     forced break before the terms box, the stance line directly under "What
     changed in the outlook".

    python tools/validate_weekly_opener.py
"""

from __future__ import annotations

import html as html_mod
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
import validate_weekly_storyline as S                          # noqa: E402

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


NO_TAKEAWAY = ("The week left this section where it was, and nothing in it changed "
               "how the readings fit together.")
WITHHELD_SECTION = "Plumbing & rates"
RETRIED_SECTION = "Mechanics"
# The read's own paragraph: worded apart from the sections', so the duplicate
# guard (a section sentence that repeats The read is withheld there) keeps theirs.
READ_TEXT = (
    "Equities held their trend while credit spreads drifted wider. The read is the "
    "week in brief: each later section takes one corner of the market and says what "
    "it showed, while this opening says which of those corners mattered most and "
    "how they hung together. Prices kept to a narrow path through all five sessions, "
    "with no day breaking the pattern set on Monday. Lenders to the weakest "
    "companies asked for a little more yield as the week went on, which is the "
    "corner of the market that usually notices strain before stocks do. Dealers' "
    "hedging kept daily swings small throughout. Takeaway: the calm in stocks is "
    "real but borrowed from a credit market that has started to ask questions, so "
    "the coming week is a test of which of the two gives way first.")


def client(calls: list):
    n = {"precis": 0}

    def create(**k):
        sysp = k["system"]
        calls.append(sysp)
        if sysp.startswith("You write the PRÉCIS"):
            n["precis"] += 1
            reply = S.precis_reply(sysp)
            if n["precis"] == 1:          # first draft: no WEEK paragraph
                reply = "\n".join(x for x in reply.splitlines()
                                  if not x.startswith("WEEK:"))
            return W.Resp(reply)
        if "Write THE READ" in sysp:
            return W.Resp(READ_TEXT)
        if f"THE SECTION: {WITHHELD_SECTION}." in sysp:
            return W.Resp(NO_TAKEAWAY)
        if f"THE SECTION: {RETRIED_SECTION}." in sysp and \
                "WITHHELD BY THE AUDIT" not in sysp:
            return W.Resp(NO_TAKEAWAY)
        # W-1.3c items 5 and 2: a first draft that names its own section as
        # subject, and one that re-explains the terms box; each retry, told why
        # and the rule, publishes the shaped paragraph.
        if "THE SECTION: Narratives." in sysp and "WITHHELD BY THE AUDIT" not in sysp:
            return W.Resp(R6["self_subject_openers"]["narratives"] + " "
                          + W.OPENER_TEXT)
        if "THE SECTION: Positioning & flows." in sysp \
                and "WITHHELD BY THE AUDIT" not in sysp:
            return W.Resp(W.OPENER_TEXT.replace(
                "The week left this section where it was.",
                "The week left this section where it was. "
                + R6["terms_explainers"]["positioning"]))
        return W.Resp(W.OPENER_TEXT)
    return types.SimpleNamespace(messages=types.SimpleNamespace(create=create))


R6 = __import__("json").loads((REPO / "tests" / "fixtures" /
                               "weekly_run6_2026-10-13.json").read_text(encoding="utf-8"))


def segments(html: str) -> dict:
    """Each section's slice of the rendered page, by its anchor."""
    out = {}
    for m in re.finditer(r'<h2[^>]*id="sec-([\w-]+)"', html):
        start = m.start()
        nxt = html.find("<h2", m.end())
        out[m.group(1)] = html[start: nxt if nxt > 0 else len(html)]
    return out


def text_of(fragment: str) -> str:
    return html_mod.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


def main() -> int:
    from altdata import config
    from daily_cascade import cadence, opener, stack_prose, weekly_stack as ws
    print(f"{LINE}\nW-1.3a 3.0 -- THE SECTION OPENER (synthetic week ending "
          f"{W.ENDING})\n{LINE}")
    td = W.gate_mkdtemp(prefix="validate_weekly_opener_")
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
    cad = cadence.get("weekly")
    segs = segments(html)
    by = {s["id"]: s for s in ed["sections"]}

    # --- A ------------------------------------------------------------------
    print(f"\n{LINE}\nA. EVERY PRESENT COMMENTARY OPENS ITS SECTION\n{LINE}")
    present = [s for s in ed["sections"] if s.get("claim") and not s.get("empty")]
    check(len(present) >= 8, f"{len(present)} sections publish a commentary on "
                             f"the fixture")
    order_bad, shape_bad, band_bad, rel_bad = [], [], [], []
    for s in present:
        seg = segs.get(s["id"], "")
        i_op = seg.find('class="opener"')
        firsts = [i for i in (seg.find("<table"), seg.find("<img"),
                              seg.find("<figure")) if i >= 0]
        if i_op < 0 or (firsts and i_op > min(firsts)):
            order_bad.append(s["id"])
        para = re.search(r'<p[^>]*class="opener"[^>]*>(.*?)</p>', seg, re.S)
        ptxt = text_of(para.group(1)) if para else ""
        last = opener.sentences(ptxt)[-1:] or [""]
        if not (opener.is_takeaway(last[0]) and para
                and "<b>Takeaway:</b>" in para.group(1)):
            shape_bad.append(s["id"])
        b = opener.band(cad, "deep" if s["id"] == "read" else s["depth"])
        n = opener.words(opener.body_text(s))
        if not b or not b[0] <= n <= b[1]:
            band_bad.append(f"{s['id']}={n}")
        if s.get("relevance") and not ptxt.startswith(s["relevance"]):
            rel_bad.append(s["id"])
    check(not order_bad, "every present commentary precedes its section's first "
                         "table and chart" + (f" -- not: {order_bad}" if order_bad
                                              else ""))
    check(not shape_bad, "every present commentary ends with one sentence "
                         "beginning \"Takeaway\", the word bolded"
          + (f" -- not: {shape_bad}" if shape_bad else ""))
    check(not band_bad, "every present commentary sits within its band (deep "
                        "120-220, medium 80-150)" + (f" -- not: {band_bad}"
                                                     if band_bad else ""))
    check(any(s.get("relevance") for s in present) and not rel_bad,
          "the relevance sentence is the paragraph's first sentence"
          + (f" -- not: {rel_bad}" if rel_bad else ""))
    check(all(not re.search(r'class="opener".*?</p>.*?<p[^>]*style="[^"]*"'
                            r'>\s*' + re.escape(html_mod.escape(
                                (s.get("paragraphs") or ["\x00"])[0][:40])),
                            segs.get(s["id"], ""), re.S) for s in present),
          "the paragraph prints once -- in the opener, never again after the "
          "tables")

    # --- B ------------------------------------------------------------------
    print(f"\n{LINE}\nB. THE PRÉCIS\n{LINE}")
    pr = ed.get("precis") or {}
    week = ((pr.get("parsed") or {}).get("week")) or ""
    pb = opener.precis_band(cad)
    check(pr.get("published") and pr.get("attempts") == 2
          and "no WEEK paragraph" in str(pr.get("first_reason")),
          "a précis draft without its WEEK paragraph is withheld; the retry "
          "publishes")
    check(pb == (150, 250) and pb[0] <= opener.words(week) <= pb[1],
          f"the WEEK paragraph sits in 150-250 ({opener.words(week)} words)")
    check(opener.takeaway(week) is not None,
          "the WEEK paragraph ends with its Takeaway")
    i_w, i_1 = html.find('class="opener precis"'), html.find('id="sec-read"')
    check(0 <= i_w < i_1 and 'class="opener precis"' in html
          and "<b>Takeaway:</b>" in html[i_w:i_1],
          "it opens the edition, before section 1, its Takeaway in bold")

    # --- C ------------------------------------------------------------------
    print(f"\n{LINE}\nC. THE AUDIT\n{LINE}")
    ok = W.OPENER_TEXT
    check(opener.faults(ok, cad, "deep") == [] and opener.faults(ok, cad, "medium")
          == [], "the fixture's paragraph passes at both depths")
    check(any("band" in f for f in opener.faults(NO_TAKEAWAY + " Takeaway: hold.",
                                                 cad, "deep")),
          "a paragraph under its band is refused")
    check(any("does not end" in f for f in opener.faults(
        ok.replace("Takeaway:", "In short,"), cad, "deep")),
          "a paragraph without a Takeaway is refused")
    moved = ok.replace("The week left this section where it was.",
                       "The week left this section where it was. Takeaway: wait.")
    check(any("Takeaway sentences" in f for f in opener.faults(moved, cad, "deep")),
          "two Takeaway sentences are refused")
    notlast = ok + " The rest is in the tables."
    check(any("not the commentary's last" in f
              for f in opener.faults(notlast, cad, "deep")),
          "a Takeaway that is not last is refused")
    fig = ok.replace("from drift.", "from drift of 2.5%.")
    check(any("restates figures" in f for f in opener.faults(fig, cad, "deep")),
          "a Takeaway that carries a figure is refused (a restatement)")
    check(opener.faults("One sentence.", cadence.get("daily"), "deep") == []
          and opener.faults("One sentence.", cadence.get("monthly"), "deep") == [],
          "the close and the Monthly carry no opener audit")
    m = by.get("mechanics") or {}
    pm = (ed.get("prose") or {}).get("mechanics") or {}
    retry = [c for c in calls if f"THE SECTION: {RETRIED_SECTION}." in c
             and "WITHHELD BY THE AUDIT" in c]
    check(m.get("claim") and pm.get("attempts") == 2 and retry
          and "Takeaway" in retry[0].split("WITHHELD BY THE AUDIT")[1],
          "a section whose first draft lacks its Takeaway is retried and publishes")

    # --- D ------------------------------------------------------------------
    print(f"\n{LINE}\nD. A WITHHELD COMMENTARY\n{LINE}")
    wid = next((s["id"] for s in ed["sections"] if s["title"] == WITHHELD_SECTION),
               None)
    seg = segs.get(wid or "", "")
    i_w = seg.find('class="opener withheld"')
    i_t = seg.find("<table")
    check(wid and not by[wid].get("claim") and by[wid].get("withheld"),
          f"{WITHHELD_SECTION}'s commentary is withheld after its retry")
    check(0 <= i_w < i_t, "the withholding line prints where the paragraph would "
                          "be, before the first table")
    check(i_t >= 0 and "Commentary withheld by the audit" in text_of(seg)
          and text_of(seg).count("Commentary withheld by the audit") == 1,
          "the section's data stays in place and the withholding line prints once")

    # --- E ------------------------------------------------------------------
    print(f"\n{LINE}\nE. THE FRAME\n{LINE}")
    wk = [c for c in calls if "THE SECTION: Positioning & flows." in c]
    check(wk and "THE OPENER SHAPE" in wk[0] and "120 to 220 words" in wk[0]
          and '"Takeaway:"' in wk[0] and "Worked example" in wk[0],
          "a deep section's frame carries the shape, its band and the worked example")
    md = [c for c in calls if "THE SECTION: Narratives." in c]
    check(md and "80 to 150 words" in md[0], "a medium section's frame carries 80-150")
    check(wk and "printed BELOW your paragraph" in wk[0],
          "the frame says the tables print below the paragraph")
    check(not re.search(r"\d", opener.EXAMPLE.replace("<n>", "")),
          "the worked example carries no figure of its own")
    rd = [c for c in calls if "Write THE READ" in c]
    check(rd and "THE OPENER SHAPE" in rd[0], "The read's frame carries the shape")
    sec = {"id": "positioning", "title": "Positioning & flows", "depth": "deep"}
    check("THE OPENER SHAPE" not in stack_prose.section_prompt(sec, "daily")
          and "THE OPENER SHAPE" not in stack_prose.section_prompt(sec, "monthly")
          and "printed ABOVE" in stack_prose.section_prompt(sec, "daily"),
          "the close's and the Monthly's frames are untouched")
    check(cadence.paragraph_cap(cad, "deep") == 220
          and cadence.paragraph_cap(cad, "medium") == 150
          and cadence.paragraph_cap(cadence.get("daily"), "deep") == 120,
          "the paragraph guard's cap is the band's top on the Weekly only")

    group_f(ed, html, calls, segs)

    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    return 1 if FAIL else 0


def group_f(ed: dict, html: str, calls: list, segs: dict) -> None:
    from daily_cascade import cadence, opener, precis, stack_render
    cad = cadence.get("weekly")
    print(f"\n{LINE}\nF. W-1.3c -- THE POLISH FROM DRY RUN #6\n{LINE}")

    # --- item 2 ---------------------------------------------------------------
    check(opener.terms_faults(R6["read_opener"])
          and all(opener.terms_faults(s) for s in R6["terms_explainers"].values()),
          "(2) run 6's read opener fails the terms-box check, and so do all five "
          "of its dealer-gamma explainers")
    check(opener.terms_faults(R6["finding_opener"]) == []
          and opener.faults(R6["finding_opener"], cad, "deep") == []
          and opener.finding_faults(R6["finding_opener"]) == [],
          "(2) an opener that explains the week's own finding passes")
    check(opener.terms_faults(opener.EXAMPLE) == []
          and "dealer gamma" not in opener.EXAMPLE.lower()
          and "never define any of" in opener.frame_note(cad, "deep")
          and "dealer gamma" in opener.frame_note(cad, "deep"),
          "(2) the worked example explains a finding, and the frame names the "
          "terms the box defines")
    pos = (ed.get("prose") or {}).get("positioning") or {}
    rp = [c for c in calls if "THE SECTION: Positioning & flows." in c
          and "WITHHELD BY THE AUDIT" in c]
    check(pos.get("published") and pos.get("attempts") == 2 and rp
          and "re-explains the terms box" in rp[0] and "THE TERMS RULE" in rp[0],
          "(2) a draft that re-explains the box is withheld, retried with the "
          "reason and the rule, and publishes")

    # --- item 5 ---------------------------------------------------------------
    bad5 = {k: opener.finding_faults(v) for k, v in R6["self_subject_openers"].items()}
    check(all(bad5.values()) and len(bad5) == 8,
          "(5) all eight run-6 first sentences fail (The read, the tape, "
          "Mechanics, What doesn't fit, Positioning, What's priced, Narratives, "
          "the book)" + (f" -- not: {[k for k, v in bad5.items() if not v]}"
                         if not all(bad5.values()) else ""))
    check(not opener.finding_faults("Credit and equities parted company this week.")
          and not opener.finding_faults("The tape rallied, and the book shows it.")
          and not opener.finding_faults("Narratives about deficits gathered support."),
          "(5) a first sentence about markets passes, even naming a section later")
    nr = (ed.get("prose") or {}).get("narratives") or {}
    rn = [c for c in calls if "THE SECTION: Narratives." in c
          and "WITHHELD BY THE AUDIT" in c]
    check(nr.get("published") and nr.get("attempts") == 2 and rn
          and "makes a section its subject" in rn[0] and "THE FINDING FIRST" in rn[0],
          "(5) the pipeline withholds it and the retry hears the reason and the rule")
    import validate_weekly_storyline as S2
    fr = {"figures_you_may_cite": [], "commentaries": [
        {"id": k, "section": k, "state": "published", "commentary": "x"}
        for k in R6["self_subject_openers"]], "previous_precis": None}
    pp = precis.parse(S2.precis_reply("\n".join(
        f"RELEVANCE {k}: <x>" for k in R6["self_subject_openers"])))
    pp["relevance"] = dict(R6["self_subject_openers"])
    rel = [f for f in precis.audit(pp, fr) if "makes a section its subject" in f]
    check(len(rel) == 8, f"(5) the précis's RELEVANCE sentence -- the opener's "
                         f"first printed sentence -- is held to it: {len(rel)} of 8")
    check("never with the section or" in precis.RELEVANCE_LINE,
          "(5) the précis frame asks for the finding")

    # --- item 4 ---------------------------------------------------------------
    paras = re.findall(r'<p[^>]*class="opener"[^>]*>(.*?)</p>', html, re.S)
    bolds = [b for para in paras for b in re.findall(r"<b[^>]*>(.*?)</b>", para, re.S)]
    check(paras and bolds and all(b == "Takeaway:" for b in bolds)
          and 'class="claim"' in html and '<b class="claim">' not in html,
          f"(4) in the rendered openers the only bold run is \"Takeaway:\" "
          f"({len(bolds)} bold runs over {len(paras)} openers)")
    md = stack_render.markdown(ed, "weekly", "Weekly")
    claims = [s["claim"] for s in ed["sections"] if s.get("claim")]
    check(claims and not any(f"**{c}**" in md for c in claims),
          "(4) and in the Markdown edition")

    # --- item 8 ---------------------------------------------------------------
    fr8 = {"figures_you_may_cite": [], "commentaries": [], "previous_precis": None}
    def first_faults(week: str) -> list:
        p8 = precis.parse(S2.precis_reply(""))
        p8["week"] = week
        return [f for f in precis.audit(p8, fr8) if "first sentence carries" in f]
    check(first_faults(R6["precis"]["week"])
          and not first_faults(R6["precis"]["tension_first"]),
          "(8) run 6's précis, which led with SPY's figures, fails; the "
          "tension-first rewrite passes")
    check("FIRST sentence states the week's tension" in precis.WEEK_LINE,
          "(8) the précis frame asks for the tension first")
    w = opener.words(R6["precis"]["tension_first"])
    check(150 <= w <= 250, f"(8) the rewrite sits in the ruled 150-250 ({w})")

    # --- item 6 (the précis) ---------------------------------------------------
    import types
    n = {"k": 0}
    prompts: list = []

    def create(**k):
        n["k"] += 1
        prompts.append(k["system"])
        reply = S2.precis_reply(k["system"])
        if "first sentence carries" not in k["system"]:
            reply = "\n".join(("WEEK: " + R6["precis"]["week"]) if x.startswith(
                "WEEK:") else x for x in reply.splitlines())
        return W.Resp(reply)
    cl = types.SimpleNamespace(messages=types.SimpleNamespace(create=create))
    edp = {"week_ending": "2026-10-09", "sections": [
        {"id": "tape", "title": "The tape", "claim": "Stocks held.",
         "paragraphs": ["Run 6's figures: " + " ".join(
             f for f in precis._figs(R6["precis"]["week"]))]}]}
    res = precis.write(edp, None, client=cl)
    check(res.get("published") and res.get("attempts") == 2
          and "THE TENSION FIRST" in prompts[1] and "attempt 1 of 2" in prompts[1],
          f"(6) the précis retries with the reason and the rule; a model that "
          f"obeys on attempt 2 publishes ({res.get('attempts')}; "
          f"{str(res.get('first_reason'))[:80]})")
    check(precis.ATTEMPTS == 2, "(6) the précis has one draft and one revision (W8-1)")

    # --- item 10 (structure; the PDF check is validate_readability's) ----------
    i_p, i_t = html.find('id="precis"'), html.find('id="terms"')
    between = html[i_p:i_t]
    check(0 <= i_p < i_t and "page-break-before" not in between
          and "break-before" not in html[i_t - 200:i_t + 200],
          "(10) no page break between the précis and the terms box")
    ped = {"precis": {"published": True, "stance_line": R6["precis"]["stance_line"],
                      "parsed": {**{k: R6["precis"][k] for k in (
                          "week", "tension", "for", "against", "verdicts",
                          "confidence", "change", "outlook")}}}}
    ph = precis.precis_html(ped)
    m = re.search(r'id="outlook"[^>]*>What changed in the outlook</h3>\s*'
                  r'<p[^>]*id="stance"[^>]*><b>([^<]*)</b>', ph)
    check(m and m.group(1) == R6["precis"]["stance_line"]
          and ph.find('id="verdicts"') < ph.find('id="change"') < ph.find('id="stance"'),
          "(10) the stance line prints directly under \"What changed in the "
          "outlook\", after the verdicts and what would change our mind")



if __name__ == "__main__":
    sys.exit(main())
