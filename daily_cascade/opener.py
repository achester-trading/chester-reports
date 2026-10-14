"""
THE SECTION OPENER (W-1.3a item 3.0; change order of 11 Oct 2026, section 4, as
amended 12 Oct on the operator's reading of the storyline rewrite).

    from daily_cascade import opener
    opener.band(cad, "deep")                 # (120, 220), or None off the Weekly
    opener.faults(text, cad, "deep")         # the shape audit, [] when it holds
    opener.commentary(s)                     # the printed paragraph, or None

THE SHAPE. Every section's commentary prints FIRST, before any table or chart,
as ONE paragraph in the storyline voice:

  1. the relevance sentence (W-1.2's item 2.3, emitted by the précis) -- why the
     section matters to the week's tension;
  2. the writer's claim line and body: each system concept explained in plain
     words where a new reader first meets it, then what the data says;
  3. exactly one sentence beginning "Takeaway" -- the implication, never a
     restatement of the data. It is the paragraph's last sentence and the
     renderer bolds the word.

THE BANDS are the writer's words (claim, body and Takeaway): deep 120-220,
medium 80-150, the précis 150-250 (config `cadences.weekly.opener`). A cadence
with no `opener` -- the close, the Monthly -- is untouched.

WHAT THE AUDIT CAN SEE. The Takeaway's position and its word; the band; and
"never a restatement" in the one form code can check -- the Takeaway carries no
figure. Whether it states a real implication is the reader's to judge.
"""

from __future__ import annotations

import re
from typing import Optional

TAKEAWAY = "Takeaway"
# The Takeaway sentence: the word, then a colon, a dash or a space.
_TAKEAWAY_HEAD = re.compile(r"^\W*Takeaway\b[:\s—–-]*", re.I)
_SENT = re.compile(r"(?<=[.!?])\s+(?=[\"“‘(]?[A-Z0-9])")


def band(cad: dict, depth: Optional[str]) -> Optional[tuple[int, int]]:
    """The writer's word band at `depth` on this cadence, or None when the
    cadence carries no opener (or the depth none)."""
    b = (cad.get("opener") or {}).get(depth or "")
    return (int(b[0]), int(b[1])) if b else None


def precis_band(cad: dict) -> Optional[tuple[int, int]]:
    return band(cad, "precis")


def words(text: Optional[str]) -> int:
    return len(re.findall(r"\S+", text or ""))


# A period that ends an abbreviation or an initialism ("U.S.", "vs.") is not a
# sentence boundary; it is masked while splitting.
_ABBREV = re.compile(r"\b(?:[A-Z]\.){2,}|\b(?:vs|e\.g|i\.e|St|Jr|No|Mr|Ms|Dr|Inc|"
                     r"Corp|Co|approx)\.")
_MASK = "․"                    # one-dot leader, never in the prose


def sentences(text: Optional[str]) -> list[str]:
    t = re.sub(r"\s+", " ", text or "").strip()
    if not t:
        return []
    t = _ABBREV.sub(lambda m: m.group(0).replace(".", _MASK), t)
    return [s.replace(_MASK, ".") for s in _SENT.split(t) if s]


def is_takeaway(sentence: Optional[str]) -> bool:
    return bool(_TAKEAWAY_HEAD.match(sentence or ""))


def takeaway(text: Optional[str]) -> Optional[str]:
    """The paragraph's last sentence when it is a Takeaway, else None."""
    ss = sentences(text)
    return ss[-1] if ss and is_takeaway(ss[-1]) else None


def _figures(text: str) -> list[str]:
    from . import readability                                   # noqa: PLC0415
    return [f for f in readability.figures(text or "") if re.search(r"\d", f)]


def faults(text: Optional[str], cad: dict, depth: Optional[str],
           what: str = "the commentary") -> list[str]:
    """The opener's shape: in band, exactly one Takeaway, last, with no
    figure. [] off a cadence with an opener."""
    b = band(cad, depth) if depth != "precis" else precis_band(cad)
    if not b:
        return []
    out = []
    n = words(text)
    if not b[0] <= n <= b[1]:
        out.append(f"{what} runs {n} words; its band is {b[0]} to {b[1]} -- "
                   f"write {'more' if n < b[0] else 'less'}, in one paragraph")
    ss = sentences(text)
    tk = [s for s in ss if is_takeaway(s)]
    if not tk:
        out.append(f"{what} does not end with a sentence beginning \"Takeaway:\" "
                   f"stating the implication")
    elif len(tk) > 1:
        out.append(f"{what} carries {len(tk)} Takeaway sentences; exactly one, last")
    elif not is_takeaway(ss[-1]):
        out.append(f"the Takeaway is not {what}'s last sentence")
    else:
        figs = _figures(_TAKEAWAY_HEAD.sub("", tk[0]))
        if figs:
            out.append("the Takeaway restates figures (" + ", ".join(figs[:3])
                       + "); it states the implication, with no figure")
    if "\n\n" in (text or "").strip():
        out.append(f"{what} is more than one paragraph")
    return out


def body_text(s: dict) -> str:
    """The writer's text as it will print: claim line, then the kept paragraph."""
    return " ".join(x for x in [s.get("claim")] + list(s.get("paragraphs") or []) if x)


def commentary(s: dict) -> Optional[dict]:
    """The printed opener of one section: {relevance, claim, body, takeaway}, or
    None when it has no published commentary."""
    if not s.get("claim") and not s.get("paragraphs"):
        return None
    rest = " ".join(s.get("paragraphs") or [])
    tk = takeaway(rest)
    body = rest[: len(rest) - len(tk)].rstrip() if tk and rest.endswith(tk) else rest
    return {"relevance": s.get("relevance"), "claim": s.get("claim"),
            "body": body or None,
            "takeaway": _TAKEAWAY_HEAD.sub("", tk).strip() if tk else None}


def withheld_line(s: dict) -> Optional[str]:
    """Where a withheld commentary would have been: one line, its reason."""
    if not s.get("withheld") or s.get("claim") or s.get("paragraphs"):
        return None
    why = re.sub(r"^(?:narrative\s+)?withheld:\s*", "", str(s["withheld"]), flags=re.I)
    return "Commentary withheld by the audit: " + why


# ---------------------------------------------------------------------------
# The frame: the shape as instruction and as a worked example
# ---------------------------------------------------------------------------
# The worked example takes the 9 Oct storyline paragraphs' SHAPE -- explain,
# describe, Takeaway -- and none of their figures: every figure is a placeholder
# in angle brackets, so it cannot be copied into a section it does not belong to.
EXAMPLE = (
    "Dealer gamma is the options market's hedging effect: above the flip level, the "
    "dealers who sold the options hedge by selling into rallies and buying dips, "
    "which damps the index's moves; below it their hedging chases the move. SPY "
    "spent <n> of <n> sessions above its flip at <level>, and its realized "
    "volatility of <figure> ran under the VIX at <figure>. The week's largest "
    "session came on the one day the index closed below the flip. Takeaway: while "
    "the index holds above the flip, dealers are a brake on the tape, so a break "
    "below it is the condition under which this calm stops being self-reinforcing.")

FRAME = """

THE OPENER SHAPE (this overrides any length or paragraph instruction above). Your
reply is ONE paragraph of {lo} to {hi} words, your first sentence (the claim line)
included. It is read FIRST, before the section's tables, by a reader who may not
know the system's terms. In order:
  - EXPLAIN each system concept in plain words the first time it appears (a
    clause is enough: "the flip, the level where dealers' hedging turns from
    damping moves to amplifying them");
  - DESCRIBE what the data says, with your figures;
  - END with exactly one sentence that begins "Takeaway:" and states the
    IMPLICATION -- what it means for the week ahead or for the book -- never a
    restatement of the data. The Takeaway carries no figure.
Worked example of the shape (its figures are placeholders; never copy them):
"{example}"
"""


def frame_note(cad: dict, depth: Optional[str]) -> str:
    b = band(cad, depth)
    if not b:
        return ""
    return FRAME.format(lo=b[0], hi=b[1], example=EXAMPLE)
