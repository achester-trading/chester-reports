"""
Validation gate for the filler audit (W-1.1 item 1.0d, ruled 11 Oct 2026).

The 9 Oct Weekly's dry run turned the frame's also-moved names into sentences
that say nothing: "the 10-year, 30-year and 2-year all moved alongside...",
"futures across the S&P 500, Nasdaq-100, Russell 2000 ... moved through the
week". The frame now carries those names under "In the tables (do not
enumerate)" and bans the form; daily_cascade/stack_prose.filler_faults withholds
a paragraph that uses it, and the retry names the offending sentence.

  A  THE PATTERN. "(also|all) mov(ed|ing)", "moved alongside", "moved through the
     week" are withheld wherever they appear, each with its sentence quoted.
  B  THE LIST. Three or more of the frame's series names joined by commas with no
     figure among them are withheld; the same names with a figure pass, and two
     names pass.
  C  THE FAULT REACHES THE RETRY. A section whose draft is filler is withheld on
     the first attempt with the sentence in its reason, and the retry prompt
     carries that reason.
  D  NO FALSE ALARM. Ordinary market prose -- "moved", "the move", a level list
     with figures -- passes.

    python tools/validate_no_filler.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from daily_cascade import figure_budget as fb  # noqa: E402
from daily_cascade import stack_prose as sp  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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


NAMES = ["2-year", "10-year", "30-year", "CFTC S&P 500 futures", "CFTC Nasdaq-100 futures",
         "CFTC Russell 2000 futures", "Investment-grade OAS", "CCC OAS"]


def group_a() -> None:
    print(f"\n{LINE}\nA. THE PATTERN\n{LINE}")
    for text in ("The 10-year, 30-year and 2-year all moved alongside the curve.",
                 "Gold rose +2.10%; silver and platinum also moved.",
                 "Futures across the index complex moved through the week.",
                 "Breakevens were all moving higher."):
        f = sp.filler_faults(text, NAMES)
        check(f and text[:40] in f[0], f"withheld, sentence quoted: '{text[:60]}'")


def group_b() -> None:
    print(f"\n{LINE}\nB. THREE OR MORE NAMES WITH NO FIGURE\n{LINE}")
    bad = "Positioning shifted in S&P 500, Nasdaq-100 and Russell 2000 futures."
    check(bool(sp.filler_faults(bad, NAMES)), "three CFTC contracts, no figure: withheld")
    check(bool(sp.filler_faults("The 2-year, the 10-year and the 30-year rose.", NAMES)),
          "three tenors, no figure: withheld")
    check(not sp.filler_faults("The 2-year, the 10-year and the 30-year rose, the long "
                               "end +9 bp.", NAMES),
          "the same list with a figure among them passes")
    check(not sp.filler_faults("The 2-year and the 10-year rose.", NAMES),
          "two names pass")
    frame = {"figures_you_may_cite": [{"series": "CCC OAS", "change": "+37 bp"}],
             fb.IN_TABLES: ["Investment-grade OAS", "2-year", "10-year"]}
    check(set(sp.filler_names(frame)) == {"CCC OAS", "Investment-grade OAS", "2-year",
                                          "10-year"},
          "the names come from the frame: its cited series and its in-the-tables list")


def group_c() -> None:
    print(f"\n{LINE}\nC. THE FAULT REACHES THE RETRY\n{LINE}")
    from daily_cascade import narrative as base

    class Reply:
        def __init__(self, text):
            self.published, self.text, self.model = True, text, "fixture"
            self.state, self.reason = "published", None

        def withheld_note(self):
            return None
    drafts = ["The curve steepened, the 30-year +9 bp. The 10-year, 30-year and 2-year "
              "all moved alongside it.",
              "The curve steepened, the 30-year +9 bp."]
    seen = []
    real = base.generate

    def fake(payload, **kw):
        seen.append(kw.get("system_prompt") or "")
        return Reply(drafts[min(len(seen) - 1, 1)])
    base.generate = fake
    try:
        tape = {"id": "tape", "title": "The tape", "depth": "deep", "items": [],
                "table": None, "subsections": [], "data": {}}
        sec = {"id": "narratives", "title": "Narratives", "depth": "medium",
               "items": [{"key": "n", "text": "x", "priority": 1}], "table": None,
               "subsections": [], "data": {}}
        read = {"id": "read", "title": "The read", "depth": "deep", "items": [],
                "table": None, "subsections": [], "data": {}}
        ed = {"session": "2026-10-09", "sections": [read, tape, sec]}
        sp.write(ed, client=object(), cadence="daily")
    finally:
        base.generate = real
    # The tape is written first: the first draft the fake returns is its.
    pr = ed["prose"]["tape"]
    check(pr.get("attempts") == 2 and pr.get("published"),
          f"the first draft withheld, the second published ({pr.get('attempts')} attempts)")
    check(len(seen) >= 2 and "all moved alongside it" in seen[1]
          and "filler sentence" in seen[1],
          "the retry prompt names the offending sentence")


def group_d() -> None:
    print(f"\n{LINE}\nD. NO FALSE ALARM\n{LINE}")
    for text in ("SPY moved +1.16% on the week, the 10-year +6 bp.",
                 "The move came on Wednesday, alongside the CPI release.",
                 "Credit split: CCC OAS +37 bp, IG OAS −4 bp, high yield +12 bp."):
        check(not sp.filler_faults(text, NAMES), f"passes: '{text[:60]}'")


def main() -> int:
    print(f"{LINE}\nTHE FILLER AUDIT (W-1.1 item 1.0d)\n{LINE}")
    group_a()
    group_b()
    group_c()
    group_d()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
