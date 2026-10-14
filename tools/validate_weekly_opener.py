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
        return W.Resp(W.OPENER_TEXT)
    return types.SimpleNamespace(messages=types.SimpleNamespace(create=create))


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

    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
