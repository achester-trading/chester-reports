#!/usr/bin/env python3
"""
Validation gate: the Weekly's readability order (W10-1 to W10-3; D46, 31 Oct
2026, decisions 1-4 as recommended). Fixtures only: synthetic drafts, a fake
model, a temporary store. No network, no live store.

  A  THE FALLBACK (W10-1)  a twice-withheld draft publishes without each sentence
                           that carries a failed figure, the marker in its place;
                           more than a third failing, or the first sentence, or
                           the Précis / "Our read", or a fault that is not a
                           figure's, withholds whole; no figure is edited; the
                           remainder is re-checked; the status line, the run log
                           and the withheld log's partial kind
"""

from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import gate_tmp                                                # noqa: E402
from daily_cascade import audit_retry as ar                    # noqa: E402

LINE = "=" * 78
PASS = FAIL = 0
TD = Path(gate_tmp.mkdtemp("a97_"))


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


# A synthetic nine-sentence draft (no real market level; every figure invented).
NINE = ["Synthetic index A rose 1.10% on the week to 101.10.",
        "Synthetic index B fell 0.20% to 52.20.",
        "The spread between them widened to 48.90 points.",
        "Synthetic yield C closed at 3.30%, up 4 bp.",
        "Synthetic yield D held at 3.90%.",
        "The curve between them sat at 60 bp.",
        "Synthetic credit E tightened 2 bp to 1.40%.",
        "Synthetic dollar F slipped 0.30% to 96.60.",
        "Synthetic gold G gained 0.70% to 2,707.70."]


def note(figs: list[str]) -> str:
    """The withheld note's form: "numeral audit failed on n figures (a, b)"."""
    n = len(figs)
    return (f"narrative withheld: numeral audit failed on {n} figure"
            f"{'' if n == 1 else 's'} ({', '.join(figs[:6])})")


def withheld(draft: list[str], figs: list[str], **kw) -> dict:
    return {"published": False, "state": "audit_failed", "attempts": 2,
            "reason": note(figs), "rejected_text": " ".join(draft),
            "unmatched_figures": list(figs), **kw}


class Capture(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.lines: list[str] = []

    def emit(self, rec) -> None:
        self.lines.append(rec.getMessage())


def group_a() -> None:
    head("A. THE FALLBACK (W10-1)")
    cap = Capture()
    logging.getLogger("daily_cascade.audit_retry").addHandler(cap)
    logging.getLogger("daily_cascade.audit_retry").setLevel(logging.WARNING)

    r = ar.apply_fallback(withheld(NINE, ["0.30%"]), report="weekly", section="tape")
    text = r.get("text") or ""
    check(r.get("published") and r.get("state") == "published_partial"
          and r.get("partial") == 1 and text.count(ar.MARKER) == 1
          and ar.MARKER == "[one sentence withheld: figure audit]",
          "nine sentences, one bad: published with one marker")
    check(r.get("status") == "published, 1 sentence withheld",
          f"its status reads '{r.get('status')}'")
    check("0.30%" not in text and "96.60" not in text,
          "the published text holds no figure the audit failed (the whole sentence goes)")
    kept = [s for s in NINE if s != NINE[7]]
    check(all(s in text for s in kept) and text.replace(ar.MARKER, NINE[7]) == " ".join(NINE),
          "no figure is edited: every other sentence is the draft's, byte for byte")
    check(any("sentence withheld (figure audit: 0.30%)" in ln and NINE[7] in ln
              for ln in cap.lines)
          and any("weekly/tape published, 1 sentence withheld" in ln for ln in cap.lines),
          "the run log names the withheld sentence, its reason and the status")

    r4 = ar.apply_fallback(withheld(NINE, ["0.20%", "3.30%", "60 bp", "1.40%"]),
                           report="weekly", section="tape")
    check(not r4.get("published") and "4 of 9 sentences fail" in (r4.get("fallback") or ""),
          f"four bad of nine withholds whole ({r4.get('fallback')})")
    r3 = ar.apply_fallback(withheld(NINE, ["0.20%", "3.30%", "1.40%"]),
                           report="weekly", section="tape")
    check(r3.get("published") and r3.get("partial") == 3,
          "three of nine (a third, not more) still publishes, with three markers")
    rf = ar.apply_fallback(withheld(NINE, ["1.10%"]), report="weekly", section="tape")
    check(not rf.get("published") and rf.get("fallback") == "its first sentence fails",
          "a bad first sentence withholds whole")
    for sec in ("precis", "our_read", "read", "stack:read"):
        rp = ar.apply_fallback(withheld(NINE, ["0.30%"]), report="weekly", section=sec)
        check(not rp.get("published") and "depend on each other" in rp.get("fallback", ""),
              f"{sec}: withheld whole on one bad sentence")
    filler = {**withheld(NINE, ["0.30%"]), "reason": "withheld: filler: a bare figure "
              "with nothing to read it against: 'Synthetic dollar F slipped 0.30% to 96.60.'"}
    rr = ar.apply_fallback(filler, report="weekly", section="tape")
    check(not rr.get("published") and "not a figure's" in rr.get("fallback", ""),
          "a fault that is not a figure's (filler) withholds whole")
    once = {**withheld(NINE, ["0.30%"]), "attempts": 1}
    check(ar.apply_fallback(once, report="weekly", section="tape") == once,
          "a first failure is the retry's, never the fallback's")
    rc = ar.apply_fallback(withheld(NINE, ["0.30%"]), report="weekly", section="tape",
                           recheck=lambda clean: ["direction: a stub fault"])
    check(not rc.get("published") and rc.get("fallback", "").startswith("the remainder fails"),
          "the remainder is re-checked: a fault there withholds whole")
    seen = []
    ar.apply_fallback(withheld(NINE, ["0.30%"]), report="weekly", section="tape",
                      recheck=lambda clean: seen.append(clean) or [])
    check(seen and ar.MARKER not in seen[0] and NINE[7] not in seen[0],
          "the re-check reads the remainder without its markers")

    # The reason's forms, as the dry runs printed them (figures synthetic).
    cut = ("narrative withheld: numeral audit failed on 8 figures "
           "(+39, 5.64%, +12.6, 0.89%, -68.53%, -$21.56bn)")
    check(ar.failed_figures(cut)[0] is None
          and ar.failed_figures(cut, ["+39", "x"])[0] == ["+39", "x"],
          "a list cut at six is not every figure: whole, unless the audit's list is given")
    role = ("withheld: role audit failed on 1 figure -- 'closed at' and 'the close' "
            "bind to a close, never to an average: 'closed ... 3.30%': 3.30% is "
            "yield C (sat/vB)'s 40-week average, an average, not a close")
    p = ar.partial(" ".join(NINE), role, section="tape")
    check(ar.figure_only(role) and p["ok"] and p["k"] == 1 and NINE[3] not in p["text"],
          "the role audit's span places its sentence (a possessive in the reason is not a quote)")
    bare = ("withheld: a change of 10,000 or more printed without its unit or scale "
            "(+29,000) -- copy its change_display or latest_level_display verbatim; "
            "write '+29,000 jobs' for +29,000")
    p2 = ar.partial(NINE[0] + " Payrolls rose +29,000 in the month. " + " ".join(NINE[1:]),
                    bare, section="plumbing")
    check(ar.figure_only(bare) and p2["ok"] and "+29,000" not in p2["text"],
          "the bare-delta audit's figure places its sentence")
    check(not ar.partial(" ".join(NINE), note(["5.2"]), section="tape")["ok"]
          and ar._hits("rose 5.2 points", "5.2") and not ar._hits("at 15.29", "5.2"),
          "a figure is matched as a whole token ('5.2' is not in '15.29'); unplaced -> whole")

    # The wiring: the Weekly's stack and the Monthly's sections go through it,
    # each re-checking with its own post-audit checks; the close does not.
    from daily_cascade import stack_prose as sp                 # noqa: PLC0415
    sps = (REPO / "daily_cascade" / "stack_prose.py").read_text(encoding="utf-8")
    mps = (REPO / "monthly_macro" / "prose.py").read_text(encoding="utf-8")
    check(sp.FALLBACK_CADENCES == ("weekly", "monthly")
          and re.search(r"apply_fallback\(\s*res, report=cadence, section=sid,\s*"
                        r"recheck=lambda clean: checks\(sid, clean, payload, True\)\)", sps)
          and "faults = checks(sid, text, payload, dup_ok) if text else []" in sps,
          "the Weekly's run() falls back, re-checking with the draft's own checks; "
          "the close keeps the whole-section rule")
    check(re.search(r"apply_fallback\(\s*\{\*\*res, \"unmatched_figures\": "
                    r"res.get\(\"unmatched\"\)\}, report=\"monthly\",\s*section=sec\[\"key\"\], "
                    r"recheck=lambda clean, sec=sec: post_faults\(sec, clean\)\)", mps),
          "the Monthly's write_all falls back after its retry, re-checking with post_faults")

    # The status line and the withheld log's own kind.
    from daily_cascade import stack_render as sr                # noqa: PLC0415
    from altdata import system_metrics as sm, withheld_log      # noqa: PLC0415
    foot = sr.foot_parts({"partial_withheld": 2})
    check("Commentary published, 2 sentences withheld by the figure audit." in foot,
          "the section's footnote carries the status line")
    ed = {"sections": [{"id": "tape", "partial_withheld": 1},
                       {"id": "plumbing", "withheld": "narrative withheld: numeral audit"},
                       {"id": "slow", "subsections": [{"id": "metals", "partial_withheld": 2}]}]}
    arch = TD / "archive"
    n = withheld_log.record_edition("weekly_tactical", "weekly_2026-11-08.json", ed,
                                    str(arch), now="2026-11-08T10:00:00+00:00")
    rows = [json.loads(x) for x in withheld_log.read(str(arch)) or []]
    kinds = sorted((x["section"], x["kind"]) for x in rows)
    check(n == 3 and kinds == [("plumbing", "whole"), ("slow/metals", "partial"),
                               ("tape", "partial")]
          and next(x for x in rows if x["section"] == "tape")["reason"]
          == "published, 1 sentence withheld (figure audit)",
          "the withheld log records a partial as its own kind, beside the whole one")
    lines = withheld_log.read(str(arch))
    check(sm.withheld(lines, "2026-11-01", "2026-11-30")["count"] == 1
          and sm.partials(lines, "2026-11-01", "2026-11-30")["count"] == 2,
          "system metrics counts withheld drafts and partials apart")

    # The Monthly: its status lines on a stack section and a sub-section.
    from monthly_macro import stack as mstack                   # noqa: PLC0415
    med = {"sections": [{"id": "tape", "depth": "deep"},
                        {"id": "themes", "subsections": [{"id": "t1", "phase": "theme:x"}]}],
           "detail": []}
    txt = " ".join(NINE[:7]) + " " + ar.MARKER
    mstack.apply_prose(med, {"stack:tape": {"published": True, "text": txt, "partial": 1},
                             "theme:x": {"published": True, "text": txt, "partial": 1}})
    tape, sub = med["sections"][0], med["sections"][1]["subsections"][0]
    check(tape.get("partial_withheld") == 1 and sub.get("partial_withheld") == 1
          and "Commentary published, 1 sentence withheld by the figure audit." in sub.get("notes", [])
          and med["prose"]["stack:tape"]["partial"] == 1,
          "the Monthly marks the section and the sub-section, and archives the count")


def main() -> int:
    for g in (group_a,):
        g()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
