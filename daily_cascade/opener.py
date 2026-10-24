"""
THE SECTION OPENER (W-1.3a item 3.0; change order of 11 Oct 2026, section 4, as
amended 12 Oct on the operator's reading of the storyline rewrite; polished by
W-1.3c from dry run #6).

    from daily_cascade import opener
    opener.band(cad, "deep")                 # (120, 220), or None off the Weekly
    opener.faults(text, cad, "deep")         # the shape audit, [] when it holds
    opener.finding_faults(text)              # a section as the first subject
    opener.terms_faults(text)                # a sentence restating the terms box
    opener.retry_note(reason, 2, 3)          # what a retry is told
    opener.commentary(s)                     # the printed paragraph, or None

THE SHAPE. Every section's commentary prints FIRST, before any table or chart,
as ONE paragraph in the storyline voice:

  1. the relevance sentence (W-1.2's item 2.3, emitted by the précis) -- the
     section's finding as it bears on the week's tension, never the section
     as its own subject (W-1.3c item 5);
  2. the writer's claim line and body: the finding first, then why it matters
     -- never a term the terms box already defines (W-1.3c item 2) -- then what
     the data says;
  3. exactly one sentence beginning "Takeaway" -- the implication, never a
     restatement of the data. It is the paragraph's last sentence, and its
     label is the opener's one bold run (W-1.3c item 4).

THE BANDS are the writer's words (claim, body and Takeaway): deep 120-220,
medium 80-150, the précis 150-250 (config `cadences.weekly.opener`). A cadence
with no `opener` -- the close, the Monthly -- is untouched.

WHAT THE AUDIT CAN SEE. The Takeaway's position and its word; the band; "never a
restatement" in the one form code can check -- the Takeaway carries no figure;
a first sentence whose subject is a section's name; a sentence that shares most
of its words with a terms-box entry. Whether the Takeaway states a real
implication is the reader's to judge.
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
    """The opener's shape: at least the band's floor, exactly one Takeaway, last,
    with no figure. [] off a cadence with an opener. The band's top is a TARGET
    since D19/D20 (24 Oct 2026): a commentary over it prints in full, never
    withheld for length; one under the floor is still sent back (too thin to
    carry its Takeaway is a shape fault, not a length cut)."""
    b = band(cad, depth) if depth != "precis" else precis_band(cad)
    if not b:
        return []
    out = []
    n = words(text)
    if n < b[0]:
        out.append(f"{what} runs {n} words; its band is {b[0]} to {b[1]} -- "
                   f"write more, in one paragraph")
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
# The worked example takes the 9 Oct storyline paragraphs' SHAPE -- finding,
# explanation, description, Takeaway -- and none of their figures: every figure is
# a placeholder in angle brackets, so it cannot be copied into a section it does
# not belong to.
#
# IT EXPLAINS ITS OWN FINDING, NOT A TERM (W-1.3c item 2). Until dry run #6 the
# example opened on a definition of dealer gamma, and three sections -- The read,
# the tape, Mechanics -- copied that definition into their openers although the
# terms box prints it above them, and the email subject took the sentence. The
# example now opens on the finding and explains why it matters.
EXAMPLE = (
    "Credit and equities parted company this week, and the gap between them "
    "widened rather than closed. Stocks finished within <figure> of their high on "
    "<n> of <n> sessions, while the extra yield lenders demand from the weakest "
    "borrowers rose by <figure>. The two can diverge for a while because they "
    "answer to different buyers: the index is carried by its largest companies, "
    "which fund themselves cheaply, while the weakest borrowers feel tighter money "
    "first, so strain shows up in their costs before it shows up in the index. "
    "Takeaway: the index's calm rests on its largest names, so another week of "
    "rising costs at the bottom of the credit ladder is the condition under which "
    "that calm is tested.")

FRAME = """

THE OPENER SHAPE (this overrides any length or paragraph instruction above). Your
reply is ONE paragraph of {lo} to {hi} words, your first sentence (the claim line)
included. It is read FIRST, before the section's tables. In order:
  - THE FIRST SENTENCE IS THE FINDING: what the data shows this week, stated as
    a claim about markets. Never make this section or the report its subject --
    never "The tape shows...", "Mechanics locates...", "This section...";
  - EXPLAIN THE FINDING: why it matters and how its pieces connect. The terms box
    printed above the sections already defines {terms}: never define any of
    them again -- use the word and move on. Explain in plain words only a concept
    the terms box does not cover;
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
    return FRAME.format(lo=b[0], hi=b[1], example=EXAMPLE, terms=terms_named())


# ---------------------------------------------------------------------------
# W-1.3c item 2: NO RE-EXPLAINING THE TERMS BOX
# ---------------------------------------------------------------------------
# Each opener sentence is compared with each terms-box entry (a sentence or a
# semicolon clause of precis.TERMS_BOX) by the share of its content words --
# lower-cased, stop words out, crudely stemmed -- that the entry also carries.
# THE THRESHOLD IS SET FROM THE RUN-6 TEXT: the five definitions dry run #6
# printed (The read, the tape, Mechanics, Positioning, What's priced) shared 7 to
# 11 stems with the dealer-gamma entry, an overlap of 0.29 to 0.48; the run's
# other opener sentences topped out at 4 shared stems and 0.20. A sentence is a
# re-explanation at 5 or more shared stems AND an overlap of 0.25 or more.
TERMS_MIN_SHARED = 5
TERMS_MIN_OVERLAP = 0.25
_STOP = frozenset(
    "a an the and or of to in on at by for with from as is are was were be been "
    "it its this that these those their there they them which who whom what when "
    "where while than then so but not no nor if into over under above below about "
    "against between through during before after up down out off same each every "
    "any all both either more most less such own just also very can could would "
    "should will may might do does did has have had his her our your we you he "
    "she one two".split())


def _stem(w: str) -> str:
    w = re.sub(r"['’]s?$", "", w)
    for suf, rep in (("ies", "y"), ("ing", ""), ("es", ""), ("ed", ""), ("s", ""),
                     ("er", ""), ("ly", "")):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[:-len(suf)] + rep
    return w


def stems(text: Optional[str]) -> set:
    return {_stem(w) for w in re.findall(r"[a-z][a-z'’-]*", (text or "").lower())
            if w not in _STOP and len(w) > 2}


def terms_entries() -> list[str]:
    from .precis import TERMS_BOX                               # noqa: PLC0415
    return [e.strip() for e in re.split(r"(?<=[.;])\s+", TERMS_BOX) if e.strip()]


def terms_named() -> str:
    from .precis import TERM_NAMES                              # noqa: PLC0415
    return ", ".join(TERM_NAMES[:-1]) + " and " + TERM_NAMES[-1]


def terms_overlap(sentence: str, entry: str) -> tuple[int, float]:
    s = stems(sentence)
    shared = len(s & stems(entry))
    return shared, (shared / len(s) if s else 0.0)


def terms_faults(text: Optional[str]) -> list[str]:
    """Each sentence of the opener that restates a terms-box entry, by the
    run-6 threshold; [] when none does."""
    out = []
    entries = terms_entries()
    for s in sentences(text):
        best = max(((terms_overlap(s, e), e) for e in entries),
                   key=lambda x: (x[0][1], x[0][0]), default=None)
        if best and best[0][0] >= TERMS_MIN_SHARED and best[0][1] >= TERMS_MIN_OVERLAP:
            out.append(f"re-explains the terms box ('{best[1][:40]}...') in "
                       f"'{s[:90]}'; the box defines it -- explain this "
                       f"section's own finding instead")
    return out


# ---------------------------------------------------------------------------
# W-1.3c item 5: THE FINDING FIRST
# ---------------------------------------------------------------------------
# Dry run #6 opened eight sections on their own name: "The read frames...", "The
# tape shows...", "Mechanics locates...", "What doesn't fit names...",
# "Positioning shows...", "What's priced shows...", "Narratives shows...", "The
# book's shortfall ... shows". A first sentence whose subject is a section name
# as printed (or "This section"), followed -- within twelve words and before any
# comma, colon, semicolon or dash -- by a reporting verb is withheld.
SECTION_NAMES = (r"the read", r"the tape", r"mechanics", r"what (?:doesn['’]t|does not) fit",
                 r"plumbing(?: (?:&|and) rates)?", r"positioning(?: (?:&|and) flows)?",
                 r"what['’]s priced", r"narratives", r"ahead", r"the book",
                 r"this section", r"the section")
REPORTING_VERBS = (r"shows?", r"frames?", r"locates?", r"names?", r"describes?",
                   r"notes?", r"finds?", r"tracks?", r"covers?", r"captures?",
                   r"highlights?", r"pinpoints?", r"sets out", r"lays out",
                   r"presents?", r"summari[sz]es?", r"explains?", r"maps?",
                   r"documents?", r"lists?", r"examines?", r"looks at", r"reviews?",
                   r"outlines?", r"traces?", r"reports?", r"identifies",
                   r"points to", r"turns to")
_SELF_SUBJECT = re.compile(
    r"^\W*(?P<name>" + "|".join(SECTION_NAMES) + r")(?:['’]s)?\b"
    r"(?P<gap>(?:\s+[^\s,;:—–]+){0,12}?)\s+(?P<verb>"
    + "|".join(REPORTING_VERBS) + r")\b", re.I)


def self_subject(sentence: Optional[str]) -> Optional[str]:
    """'<name> ... <verb>' when `sentence` makes a section its subject."""
    m = _SELF_SUBJECT.match(sentence or "")
    if not m or re.search(r"\s-\s", m.group("gap") or ""):
        return None
    return f"{m.group('name')} ... {m.group('verb')}"


def finding_faults(text: Optional[str], what: str = "the commentary") -> list[str]:
    ss = sentences(text)
    hit = self_subject(ss[0]) if ss else None
    if not hit:
        return []
    return [f"{what}'s first sentence makes a section its subject ('{hit}': "
            f"'{ss[0][:90]}'); the first sentence is the finding -- state what "
            f"the data shows, about markets"]


# ---------------------------------------------------------------------------
# W-1.3c item 6: A RETRY CARRIES THE REASON AND THE RULE
# ---------------------------------------------------------------------------
# Dry run #6 withheld the Ahead after retries that never heard why: the reason
# was cut to its first four faults and 600 characters, and the opener's faults
# come late in the list. Every withhold now feeds back its whole message and,
# for each kind of fault in it, the rule that fault breaks.
RULES = (
    (r"band is|Takeaway sentences|does not end with|not the commentary's last|"
     r"not the WEEK paragraph's last|more than one paragraph|no WEEK paragraph",
     "THE OPENER SHAPE: one paragraph inside the word band, ending in exactly one "
     "sentence that begins \"Takeaway:\"."),
    (r"restates figures",
     "THE TAKEAWAY RULE: the sentence beginning \"Takeaway:\" states the "
     "implication in words and carries NO figure -- no number, percentage, level "
     "or count. Move every figure into the sentences before it."),
    (r"is bound to",
     "THE BINDING RULE: a figure in a sentence that names a series is that "
     "series' own figure, from its own row, in the unit its column states -- "
     "never another series' figure and never another column's (a z is not points "
     "of open interest)."),
    (r"numeral audit|figures no commentary cites|figures in no block",
     "THE NUMERAL RULE: every figure you print is one your data carries, copied "
     "exactly as printed there -- its sign, decimals and unit. Never derive, "
     "round, convert or recall a figure."),
    (r"direction audit",
     "THE DIRECTION RULE: the directional word beside a figure agrees with its "
     "sign -- \"fell\", \"narrowed\", \"softened\" with a fall; \"rose\", "
     "\"widened\", \"firmed\" with a rise -- and a currency's word agrees with "
     "its index or the pair it is quoted in."),
    (r"filler",
     "THE FILLER RULE: never write a sentence that only says other series moved, "
     "a list of three or more series without a figure, or a bare figure with "
     "nothing to read it against."),
    (r"the paragraph cites \d+ figures",
     "THE FIGURE BUDGET: cite at most the figures your frame allows; the tables "
     "carry the rest."),
    (r"re-explains the terms box",
     "THE TERMS RULE: the terms box defines the system's terms; never define "
     "one again. Explain this section's own finding: why it matters."),
    (r"makes a section its subject",
     "THE FINDING FIRST: the first sentence is the finding -- what the data "
     "shows about markets -- never this section or the report as its subject."),
    (r"first sentence carries \d+ figures",
     "THE TENSION FIRST: the WEEK paragraph's first sentence states the week's "
     "tension in words, with at most one figure; the two or three figures that "
     "carry it follow."),
)


def rules_for(reason: Optional[str]) -> list[str]:
    """The rule behind each kind of fault the withhold message names."""
    return [rule for rx, rule in RULES if re.search(rx, reason or "", re.I)]


def retry_note(reason: Optional[str], attempt: int, attempts: int) -> str:
    """What retry `attempt` (2 or 3 of `attempts`) is told: the previous
    attempt's whole withhold message and the rule behind each of its faults."""
    rules = rules_for(reason)
    # The first line keeps the wording every gate reads ("WITHHELD BY THE
    # AUDIT: <the message as the audit wrote it>"); the count follows it.
    return ("\n\nYOUR PREVIOUS DRAFT WAS WITHHELD BY THE AUDIT: " + str(reason)
            + f"\nThat draft was attempt {attempt - 1} of {attempts}."
            + ("\nTHE RULE" + ("S" if len(rules) > 1 else "") + " IT BROKE:\n- "
               + "\n- ".join(rules) if rules else "")
            + "\nWrite it again from the same data, fixing exactly that and "
              "changing nothing else.")
