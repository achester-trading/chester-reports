"""
The close narrative — one paragraph, and only if the numeral audit passes.

-----------------------------------------------------------------------------
WHY THIS MODULE IS ALLOWED TO EXIST NOW AND WAS NOT BEFORE
-----------------------------------------------------------------------------
Architecture 32.5 kept the Daily Cascade data-only until something could FAIL a
block for containing a number that is not in its payload. altdata/numeral_audit.py
is that something (D3), so prose becomes publishable — not trusted. The audit gates
it on every run, and a failure withholds the paragraph rather than correcting it.
Correcting would be worse: a model that can be nudged into agreement produces a
paragraph nobody checked, and the whole point is that something did.

THE PAYLOAD IS STRUCTURED AND SMALL, ON PURPOSE. The model is handed the figures
it may use and nothing else — no chain, no raw profile, no store access. Two
reasons. A narrow payload is a narrow attack surface for invention: a figure that
is not in front of the model is a figure it has to fabricate to print, and the
audit will catch it. And the audit's own reference set IS this payload, so
anything the model was shown is matchable and anything it was not shown is not.

NOTHING HERE DECIDES ANYTHING. The paragraph states the rule and the distance; it
never says buy, sell, add or trim. That is a style rule in
docs/narrative-template-close.md and a system-prompt instruction here, and it is
also structurally true: this module is not in the decision path, writes nothing to
the register, and its output is a string that gets escaped into HTML.

-----------------------------------------------------------------------------
DEGRADATION, IN LAYERS, BECAUSE A REPORT MUST NOT DEPEND ON A MODEL
-----------------------------------------------------------------------------
    anthropic package missing  -> no paragraph, reason recorded
    no API key                 -> no paragraph, reason recorded
    call fails or times out    -> no paragraph, reason recorded
    empty or over-long reply   -> no paragraph, reason recorded
    numeral audit fails        -> no paragraph, reason recorded, figures named

Every one of those is the data-only edition, which is a complete report. None of
them raises. The close report has no try around its render, so an exception here
would cost the whole run including the archive — and a missing paragraph is
strictly better than a missing report.
"""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from altdata import numeral_audit  # noqa: E402

from . import precision  # noqa: E402

log = logging.getLogger("daily_cascade.narrative")

# PINNED, and pinned deliberately rather than tracking a floating alias. The
# paragraph is graded over time against what it said, so the writer has to be
# identifiable: a silent model change would break the comparison without
# breaking anything visible. The version is recorded on the artifact.
DEFAULT_MODEL = os.environ.get("CLOSE_NARRATIVE_MODEL", "claude-sonnet-5")

# One call per report. Not a budget to spend — a bound, so a retry loop cannot
# turn one report into a bill.
MAX_CALLS = 1
# THE BUDGET HAS TO COVER THINKING AS WELL AS THE PARAGRAPH, and 700 did not.
#
# Tuesday 22 September's close withheld its narrative with "the model returned no
# text". The call was made and returned HTTP 200; the diagnosis was
# `stop_reason: max_tokens` with all 700 output tokens spent as thinking_tokens and
# a single EMPTY thinking block in the reply. The model was cut off before it
# emitted its first text token, and the extraction below correctly found nothing.
#
# 700 was sized for one paragraph -- MAX_CHARS is 2600, which is about 650 tokens --
# at a time when a reply was text and only text. It left no room for a reasoning
# budget the model takes by default, and the whole budget went there.
#
# Two changes, each for its own reason. THINKING IS DISABLED below, because this
# brief is a mechanical rewrite of a payload into one paragraph with a numeral audit
# behind it: the reasoning buys nothing the audit does not check, and it cost 3,711
# output tokens against 308 on the same payload -- twelve times, measured. And the
# cap is raised anyway, so that a model or an SDK which thinks regardless still
# reaches the text. Only what is used is billed, so the headroom is free.
MAX_TOKENS = 2000

# A paragraph. The cap is generous against the template's "length: what the
# coverage needs" and tight enough that an essay is a failure rather than a
# publication.
MAX_CHARS = 2600

TEMPLATE_PATH = REPO / "docs" / "narrative-template-close.md"

SYSTEM_PROMPT = """\
You write one paragraph for a market close report, for a single reader who is the \
operator of the system that produced the figures.

ABSOLUTE RULES, in order of importance:

1. EVERY NUMBER YOU WRITE MUST APPEAR IN THE PAYLOAD YOU ARE GIVEN. Do not \
compute, infer, annualise, convert or estimate any figure. If you want to state a \
change, the payload contains the change. An automated audit extracts every numeral \
from your paragraph and matches it against the payload; anything unmatched causes \
your entire paragraph to be discarded. Rounding to the precision you print is \
fine and expected.

2. NO RECOMMENDATION. Never write buy, sell, add, trim, hold, or any synonym. The \
position sentence states the rule that was already written and the distance to the \
invalidation level. It does not say what to do.

3. ONE PARAGRAPH. Plain declarative sentences. No headings, no bullets, no line \
breaks, no markdown.

4. NAME THE MECHANISM, NOT THE MOOD. "Dealers must sell X per 1% decline", not \
"the market feels heavy".

5. END ON THE SYSTEM, not the market: what today's data tested and what it will \
test next.

You may write a number as words ("ten and a half billion") only when the same \
value is also printed in the tables below your paragraph. When in doubt, use the \
numeral.

A SIGN IS PART OF THE NUMERAL, NEVER A WORD -- AND THE SIGNED FORM IS IN THE \
PAYLOAD. Every change, move, delta or return has a sibling ending in _signed: \
"change_pct": -6.75 sits beside "change_pct_signed": "−6.75%", "change_bps": \
12 beside "+12 bp". Copy that string verbatim whenever you cite the move: "gold \
fell −6.75%", never "gold fell 6.75%". The audit matches the sign exactly, so \
a fall written as a word with an unsigned magnitude does not match the negative \
value and the whole paragraph is discarded over a phrasing. Say "fell" in the \
sentence if you like; the figure still carries its own sign.

A LARGE FIGURE IS ALSO COPIED, NEVER RESCALED. A level or change stored in \
millions, thousands or dollars has a sibling ending in _display -- \
"latest_level": 7510123 beside "latest_level_display": "$7.51tn", payrolls \
beside "159.33 million". Write that string as it stands; never convert a stored \
number to billions or trillions yourself ("373 billion" from a series in \
millions is a guess at the unit, and it discards the paragraph).

A PERCENTILE IN PROSE IS THE PAYLOAD'S OWN ORDINAL, COPIED VERBATIM. Every \
percentile field has a sibling ending in _ordinal -- "percentile": 51.7 sits \
beside "percentile_ordinal": "52nd" -- already rounded to the nearest whole \
number. Write exactly that string: "the 52nd percentile". Never round, truncate \
or re-suffix a percentile yourself ("51st" for 51.7 is wrong), and never put an \
ordinal on a decimal ("96.1th"): any percentile ordinal that is not one of the \
payload's _ordinal strings discards the paragraph.

DO NOT RESTATE A TABLE ROW BY ROW. The eight dimensions, the six contradiction \
rows and the pin tally are all printed in full below your paragraph, and reciting \
them adds nothing a reader could not read there -- it also crowds out the only \
thing prose can do, which is say what the configuration MEANS. Name a dimension \
when it changed, when it sits at an extreme, or when it disagrees with another; \
otherwise say what the set of them amounts to. A sentence listing every percentile \
in order is a failed paragraph even when every figure in it is correct. The \
reference paragraph in the template is the register: it names four figures and \
spends the rest of its length on what they imply.\

Cover, in this order, only what the payload supports: WHAT CHANGED since the \
previous session (`what_changed`: dimension state changes, extreme flags set or \
cleared, dial moves, contradictions opened, closed or persisting -- cite the \
percentile beside every one, never the label alone); the market state as the \
object records it (`market_state`: the three dials and the eight dimensions with \
their states, directions and percentiles, and the dimensions it reports ABSENT, \
which you must name as absent rather than passing over); any open row in \
`contradictions`, with its z and how many sessions it has been open; the dealer \
regime (spot versus the flip, and how long on that side); the hedge flow and its \
change; the corridor \
(walls, their movement, where gamma concentrates); what the vol complex says and \
what it does not; the position (fill, close, distance to invalidation in points \
and percent, and the rule); and the system's scorecard (the pin tally, the \
cross-check when present, and what the day put at stake). Omit anything the \
payload does not contain rather than reaching for it.

DO NOT CHARACTERISE THE REGIME YOURSELF. `market_state` is the system's only \
regime, computed by regime.py from declared rules in config/market_state.yaml. \
Read its states; do not infer a state from the levels, do not average the \
dimensions into an overall view, and do not describe a dimension the object \
reports absent as though it had a state. A paragraph that derives its own regime \
is a second regime, and then nothing can say which one a decision was made under.
"""


# ---------------------------------------------------------------------------
# THE 07:00 NARRATIVE SCAN (6c-2) -- the anchor's first model call
# ---------------------------------------------------------------------------
MORNING_MODEL = os.environ.get("MORNING_NARRATIVE_MODEL", "claude-sonnet-5")
MORNING_TEMPLATE_PATH = REPO / "docs" / "narrative-template-morning.md"
# A RUNAWAY GUARD, not a word count -- the Weekly's argument. The block runs as long
# as the analysis warrants; this is the point at which a reply has lost the thread.
MORNING_MAX_CHARS = 12000
PROPOSALS_MARKER = "PROPOSALS:"


def morning_system_prompt() -> str:
    """The morning scan's brief: the close rules, the scan's coverage."""
    return SYSTEM_PROMPT + (
        "\n\nTHIS IS THE 07:00 NARRATIVE SCAN, not the close report. It reads the "
        "stories the market is trading, from STORED events and the narrative "
        "register. Differences:\n"
        "\n1. LENGTH IS WHAT THE ANALYSIS NEEDS. No word count; several paragraphs "
        "are correct when there is several things to say. The first sentences "
        "answer what changed overnight and whether it matters; the depth follows. "
        "Ignore the one-paragraph rule above.\n"
        "\n2. COVER, in this order: which stories gained or lost force overnight "
        "(`register.transitions_overnight`, and attention); which are consensus "
        "and which contested (`register.stories[].state` -- NEVER assign a state "
        "yourself: the declared rules set it); where the market's story and the "
        "data disagree (every open `narrative_vs_data.*` row in `contradictions`, "
        "naming the linked dimension that points the other way); what happened "
        "since the previous close (`events`); and what would change each story "
        "under the rules (`register.rules` states them).\n"
        "\n3. EVERY CLAIM TRACES TO AN EVENT ID OR AN OBSERVATION. Cite a stored "
        "event as `event 257` -- the word event, then the id, exactly as in "
        "`citable_event_ids`. An id not in that list withholds the whole block.\n"
        "\n3a. CITED EVENTS ARE QUOTED, NOT DESCRIBED. `citable_events` carries "
        "each id's STORED `type` and `source`. Name them verbatim beside the "
        "citation -- `a headline from google_news (event 134)`, `a release from "
        "fed_press (event 1)` -- and give what it says as its title in double "
        "quotes, not a paraphrase of what kind of thing it is. A type or source "
        "word beside a citation that differs from the stored one withholds the "
        "block.\n"
        "\n3b. ABSENT IS A FIELD, NOT A GAP. An item carrying `absent: true` IS "
        "IN THE PAYLOAD and says why it has no reading (`reason`), or that its "
        "reader failed (`fault`). Say it is absent and give the reason. Never "
        "write that a row or a field is missing from, or absent from, the object: "
        "every declared row is present, and such a sentence withholds the "
        "block.\n"
        "\n3c. STATES ARE THE OBJECT'S WORDS. `market_states` carries every dial's "
        "and dimension's stored state (and `previous` where it changed). When you "
        "name a state beside a dial or dimension -- `gamma is positive`, `a flat "
        "trend`, `gamma flipped from negative to positive`, `gamma-vs-trend at "
        "positive/flat` -- use exactly those words. A state word that is not the "
        "stored one, or any state for one that is absent, withholds the block.\n"
        "\n4. A RELEASE'S SURPRISE IS AGAINST A NAIVE EXPECTATION, never a "
        "consensus; an earnings surprise is against the analyst mean. Say which.\n"
        "\n5. PROPOSALS, ONLY IF WARRANTED. If the events show a story the register "
        "does not hold, append after the prose a line reading exactly "
        f"`{PROPOSALS_MARKER}` and then a JSON array, per the template. Each "
        "proposal needs id, name, direction, linked_dimensions, implied_outcome "
        "(claim, metrics, comparison, quorum, horizon_days) and basis_events from "
        "citable_event_ids. A proposal waits for the operator; it is never "
        "evaluated before. Emit no block when there is nothing to propose.\n"
        "\n6. NO RECOMMENDATION. Stories are what the market believes. This block "
        "never touches a position.\n")


def split_proposals(text: str) -> tuple[str, dict]:
    """(prose, {"proposals": [...]} or {"parse_error": ...}). Never raises."""
    idx = text.find(PROPOSALS_MARKER)
    if idx < 0:
        return text, {"proposals": []}
    prose, tail = text[:idx].rstrip(), text[idx + len(PROPOSALS_MARKER):].strip()
    import json as _json  # noqa: PLC0415
    tail = tail.strip("`").removeprefix("json").strip()
    try:
        items = _json.loads(tail)
    except ValueError as exc:
        return prose, {"proposals": [], "parse_error": f"not JSON: {exc}"}
    if not isinstance(items, list):
        return prose, {"proposals": [], "parse_error": "not a JSON array"}
    return prose, {"proposals": [x for x in items if isinstance(x, dict)]}


@dataclass
class NarrativeResult:
    """What happened, in enough detail for the footer and the state row."""
    text: Optional[str] = None
    model: Optional[str] = None
    state: str = "not_attempted"
    reason: str = ""
    audit: Optional[numeral_audit.AuditResult] = None
    figures_checked: int = 0
    unmatched: list[str] = field(default_factory=list)
    # WHAT THE MODEL WROTE WHEN IT WAS NOT PUBLISHED. Never rendered, never
    # delivered; logged, so a human can see the sentence the audit rejected.
    #
    # Without it the withheld line says "3 figures failed" and the evidence is
    # gone -- and the question an operator actually has is whether the audit was
    # RIGHT, which cannot be answered from the figure list alone. A rejected
    # paragraph naming a level the payload holds at a different precision and one
    # inventing a ratio out of two payload numbers produce identical withheld
    # lines and need opposite fixes.
    rejected_text: Optional[str] = None
    # WHAT A BRIEF'S `split` HOOK TOOK OUT OF THE REPLY BEFORE THE AUDIT -- the
    # morning scan's structured PROPOSALS block. Never audited as prose and never
    # rendered; the caller validates it on its own terms.
    extra: Any = None
    # The event ids the prose cited, and any that the payload does not carry.
    cited_ids: list[int] = field(default_factory=list)
    untraceable: list[int] = field(default_factory=list)
    # 6c-3: citations whose adjacent type/source words contradict the stored
    # ones, and sentences that call a present row missing from the object.
    miscited: list[str] = field(default_factory=list)
    presence: list[str] = field(default_factory=list)
    citation_checked: bool = False
    misstated: list[str] = field(default_factory=list)
    states_checked: bool = False

    @property
    def published(self) -> bool:
        return bool(self.text) and self.state == "published"

    def verdicts(self) -> dict:
        """The two audits, reported apart. (6c-2)

        ONE AUDIT, TWO QUESTIONS. altdata/numeral_audit.audit() answers both in one
        pass and folds them into one pass/fail: does every numeral exist in the
        payload (the NUMERAL audit), and does the unit word beside it agree with
        what that value is (the TYPE audit). A withheld paragraph needs the two
        apart, because they are fixed in different places -- a missing figure is a
        payload or a model problem, a type conflict is a sentence calling a true
        number the wrong kind of thing.
        """
        if self.audit is None:
            return {"numeral": "not_run", "type": "not_run",
                    "traceability": "not_run"}
        missing = [f.text for f in self.audit.unmatched if not f.type_conflict]
        typed = [f"{f.text} ({f.type_conflict})" for f in self.audit.unmatched
                 if f.type_conflict]
        return {
            "numeral": (f"pass ({len(self.audit.figures)} figures)" if not missing
                        else f"fail ({len(missing)}: {', '.join(missing[:6])})"),
            "type": ("pass" if not typed
                     else f"fail ({len(typed)}: {'; '.join(typed[:4])})"),
            "traceability": ("pass" if not self.untraceable else
                             f"fail (event ids not in the payload: "
                             f"{self.untraceable[:8]})"),
            "citation": ("not_run" if not self.citation_checked else
                         "pass" if not self.miscited else
                         f"fail ({len(self.miscited)}: "
                         f"{'; '.join(self.miscited[:4])})"),
            "presence": ("not_run" if not self.citation_checked else
                         "pass" if not self.presence else
                         f"fail ({'; '.join(self.presence[:3])})"),
            "state": ("not_run" if not self.states_checked else
                      "pass" if not self.misstated else
                      f"fail ({len(self.misstated)}: "
                      f"{'; '.join(self.misstated[:4])})"),
        }

    def withheld_note(self) -> str:
        """The one line the data-only edition carries in place of the prose."""
        if self.state == "untraceable":
            return (f"narrative withheld: it cites event ids the payload does not "
                    f"carry ({', '.join(str(i) for i in self.untraceable[:6])})")
        if self.state == "miscited":
            return (f"narrative withheld: a citation's type or source contradicts "
                    f"the stored event ({'; '.join(self.miscited[:3])})")
        if self.state == "state_misstated":
            return (f"narrative withheld: a state named beside a dial or "
                    f"dimension is not the stored one "
                    f"({'; '.join(self.misstated[:3])})")
        if self.state == "presence_misstated":
            return (f"narrative withheld: it calls a present row missing from the "
                    f"object ({'; '.join(self.presence[:2])})")
        if self.state == "audit_failed":
            n = len(self.unmatched)
            return (f"narrative withheld: numeral audit failed on {n} "
                    f"figure{'' if n == 1 else 's'} "
                    f"({', '.join(self.unmatched[:6])})")
        return f"narrative withheld: {self.reason or self.state}"


def _client():
    """The Anthropic client, or None with the reason logged.

    Imported lazily so the whole report pipeline runs on a box that has never
    installed the package — which is most of them, and all of CI.
    """
    # THROUGH THE ONE LOADER, not os.environ directly.
    #
    # Under systemd this module worked either way: the unit carries
    # EnvironmentFile=.env, so the variable is in the process environment before
    # Python starts. A MANUAL run is a different environment -- .env is not sourced
    # by an interactive shell -- so reading os.environ alone reported the key
    # missing for every run that was not the timer's, which is the first line in
    # Tuesday's log and is exactly the reading that misdirects a diagnosis. It
    # misdirected mine for one command.
    #
    # altdata.secrets is the single loader Step 0(a) established: environment
    # always wins over .env, values are never logged, and both callers now resolve
    # the key identically.
    from altdata import secrets  # noqa: PLC0415
    key_name = "ANTHROPIC" + "_API_KEY"
    if not secrets.present(key_name):
        return None, f"{key_name} is not set (checked environment, then .env)"
    try:
        import anthropic  # noqa: PLC0415
    except ImportError:
        return None, "the anthropic package is not installed"
    try:
        return anthropic.Anthropic(), ""
    except Exception as exc:  # noqa: BLE001
        return None, f"client construction failed: {type(exc).__name__}: {exc}"


def style_guide(path=None) -> str:
    """The committed template, which is the style contract.

    Read from docs/ rather than embedded so the operator edits one file and both
    the model and the human reading the spec see the same thing. Absent, the
    system prompt above still carries the rules that matter.
    """
    p = path or TEMPLATE_PATH
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        log.warning("%s unreadable; relying on the system prompt alone", p)
        return ""


# RUNAWAY GUARDS, NOT BUDGETS -- and never a silent cut. Until the Weekly of
# 27 September this function sent guide[:6000] and payload[:12000]: three of the
# four templates are longer than 6,000 characters, so no model had ever read the
# end of its own brief, and the Weekly's payload is 18,500, so everything
# alphabetically after `week_ahead` was cut mid-JSON. The model then wrote,
# truthfully about what it saw, that the payload "cuts off before further
# releases" and that weekend developments were unsourced. A prompt that does not
# fit now WITHHOLDS the paragraph with its size as the reason.
MAX_GUIDE_CHARS = 30000
MAX_PAYLOAD_CHARS = 60000


class PromptTooLarge(ValueError):
    """The brief or the payload is past its runaway guard; nothing was cut."""


def build_prompt(payload: dict, guide_path=None) -> str:
    """The user turn: the style guide, then the figures, and nothing else.

    Whole or not at all: raises PromptTooLarge rather than truncating.
    """
    import json  # noqa: PLC0415
    guide = style_guide(guide_path)
    # ensure_ascii=False: the model must see "−6.75%" as the characters it
    # is told to copy, not as a JSON escape it might reproduce literally.
    body = json.dumps(payload, indent=2, default=str, sort_keys=True,
                      ensure_ascii=False)
    if guide and len(guide) > MAX_GUIDE_CHARS:
        raise PromptTooLarge(f"the style guide is {len(guide)} characters, past "
                             f"the {MAX_GUIDE_CHARS} guard")
    if len(body) > MAX_PAYLOAD_CHARS:
        raise PromptTooLarge(f"the payload is {len(body)} characters, past the "
                             f"{MAX_PAYLOAD_CHARS} guard")
    return (
        (f"=== STYLE AND COVERAGE SPECIFICATION ===\n{guide}\n\n"
         if guide else "")
        + "=== THE PAYLOAD. Every number you write must come from here. ===\n"
        + body
        + "\n\nWrite the paragraph."
    )


# ---------------------------------------------------------------------------
# 6c-3 -- CITED EVENTS ARE QUOTED; ABSENT IS A FIELD
# ---------------------------------------------------------------------------
# The stored event types and the words that name each. A word from one type's
# list beside a citation of an event of another type is a contradiction.
EVENT_TYPE_WORDS = {
    "release": ("release", "releases", "data release"),
    "earnings": ("earnings report", "earnings"),
    "filing": ("filing", "8-k", "10-k", "10-q"),
    "headline": ("headline", "headlines"),
    "scheduled": ("scheduled", "calendar entry"),
    "session_event": ("session event", "session_event"),
}
# Stored source names, beyond whatever the payload itself carries.
KNOWN_SOURCES = ("fed_press", "fed_monetary", "bls_cpi", "bls_empsit", "bea_news",
                 "google_news", "yfinance", "sec_edgar", "claims_registry",
                 "session_calendar", "fred")
CITATION_LEFT, CITATION_RIGHT = 60, 30
_QUOTED = r'"[^"]*"|“[^”]*”'
PRESENCE_PATTERN = (
    r"(?i)\b(?:absent|missing)\s+(?:entirely\s+)?(?:from|in)\s+the\s+"
    r"(?:object|table|payload)\b|\babsent\s+entirely\b|\bnot\s+(?:in|on)\s+the\s+"
    r"object\b")


def citation_contradictions(text: str, citable_events: list,
                            cite_word: str = "event") -> list[str]:
    """Citations whose adjacent type or source words differ from the stored ones.

    The window is the clause around the citation: at most CITATION_LEFT
    characters before and CITATION_RIGHT after, stopped at a sentence end or at
    a neighbouring citation, with quoted titles removed -- a title may say
    anything; the words OUTSIDE the quotes are the prose's claim about what
    the event is. Only a contradiction fails: a citation with no type or
    source word beside it is untyped, not wrong.
    """
    import re as _re  # noqa: PLC0415
    stored = {int(e["event_id"]): e for e in citable_events or []
              if e.get("event_id") is not None}
    sources = {str(e.get("source")) for e in stored.values() if e.get("source")}
    sources |= set(KNOWN_SOURCES)
    cites = list(_re.finditer(rf"\b{_re.escape(cite_word)}s?\s+(\d+)", text,
                              flags=_re.I))
    masked = _re.sub(_QUOTED, lambda q: " " * len(q.group(0)), text)
    out = []
    for i, m in enumerate(cites):
        ev = stored.get(int(m.group(1)))
        if not ev:
            continue
        lo = max(m.start() - CITATION_LEFT, cites[i - 1].end() if i else 0)
        hi = min(m.end() + CITATION_RIGHT,
                 cites[i + 1].start() if i + 1 < len(cites) else len(text))
        # QUOTED TITLES ARE MASKED FIRST, position for position, so no clause
        # split below can cut a title open and expose its words.
        left, right = masked[lo:m.start()], masked[m.end():hi]
        for stop in (". ", "\n"):
            if stop in left:
                left = left[left.rindex(stop) + len(stop):]
        # The words AFTER a citation belong to it only up to the clause break:
        # past a comma or an "and", they are the next citation's description.
        # EXCEPT AN APPOSITIVE -- "event 1, a Fed approval notice" -- which is a
        # description of this citation and the exact form of the 28 September
        # draft's mislabel; it runs to its own clause end.
        appos = _re.match(r"\)?,\s+(?:a|an|the)\s+[^,;:.\n]*", right)
        brk = _re.search(r"[,;:.\n]|\s(?:and|but|against|while)\s", right)
        if appos:
            right = appos.group(0)
        elif brk:
            right = right[:brk.start()]
        for sep in (",", ";", " and ", " against ", " but "):
            if sep in left:
                left = left[left.rindex(sep) + len(sep):]
        window = f"{left} {right}".lower()
        words_t = {t for t, ws in EVENT_TYPE_WORDS.items()
                   if any(_re.search(rf"(?<![\w-]){_re.escape(w)}(?![\w-])", window)
                          for w in ws)}
        words_s = {s for s in sources
                   if _re.search(rf"(?<![\w-]){_re.escape(s.lower())}(?![\w-])",
                                 window)}
        bad_t = words_t - {ev.get("type")}
        bad_s = words_s - {ev.get("source")}
        if bad_t:
            out.append(f"event {m.group(1)} called {'/'.join(sorted(bad_t))}, "
                       f"stored {ev.get('type')}")
        if bad_s:
            out.append(f"event {m.group(1)} attributed to "
                       f"{'/'.join(sorted(bad_s))}, stored {ev.get('source')}")
    return out


# ---------------------------------------------------------------------------
# 6c-3 -- STATE WORDS: a state named beside a dial or dimension is the stored one
# ---------------------------------------------------------------------------
# The 28 September re-render wrote "gamma-vs-trend ... its positive/flat state
# pair", and no audit could say whether that was the object's pair. This one can.
# The same adjacency discipline as types and sources: only a word from THAT
# name's declared vocabulary counts, and only in four tight forms --
#   after      the name, past filler words:        "gamma is positive"
#   before     the name, immediately:              "a flat trend"
#   transition "gamma flipped from negative to positive" -- `to` is checked
#              against the stored state, `from` against the stored previous
#   pair       "gamma-vs-trend ... positive/flat", positionally
# A state word in any other position is not read as a claim -- "volatility
# turning up" says nothing about the volatility state, whose words are
# elevated, normal and subdued.
STATE_FILLERS = ("dial", "dimension", "dimension's", "dial's", "state", "reading",
                 "is", "was", "reads", "read", "remains", "remained", "stays",
                 "stayed", "still", "now", "at", "currently", "sits", "sat", "in",
                 "of", "the", "its", "on", "as", "being", "held", "holds", "a")
STATE_VERBS = ("flipped", "flipping", "flips", "moved", "moving", "moves", "turned",
               "turning", "turns", "went", "changed", "changing", "shifted",
               "shifting", "swung", "swinging", "fell", "rose")
STATE_AUX = ("did", "does", "has", "had", "also", "then", "move", "moved",
             "again", "back", "firmly")
# Names a dial is written under. The vol dial is only ever "vol dial": bare "vol"
# is the volatility dimension's word in every other sentence.
STATE_ALIASES = {"gamma": ("dealer gamma", "gamma dial", "gamma"),
                 "vol": ("vol dial",), "macro": ("macro dial",)}


def _name_re(name: str) -> str:
    import re as _re  # noqa: PLC0415
    names = STATE_ALIASES.get(name, (name,))
    return "(?:" + "|".join(_re.escape(n).replace(r"\ ", r"[\s_-]+")
                            for n in names) + ")"


def state_contradictions(text: str, market_states: dict) -> list[str]:
    """State words beside a dial or dimension name that are not its stored state."""
    import re as _re  # noqa: PLC0415
    if not market_states:
        return []
    masked = _re.sub(_QUOTED, lambda q: " " * len(q.group(0)), text).lower()
    # Filler, auxiliaries and change verbs may sit between a name and its state
    # word -- "the gamma dial did move, flipping from negative to positive" --
    # so a transition written with a pause in it is still checked.
    fill = r"(?:[\s,:]+(?:%s))*" % "|".join(
        map(_re.escape, STATE_FILLERS + STATE_VERBS + STATE_AUX))
    verb = ""
    out: list[str] = []
    seen: set = set()

    def claim(name: str, word: str, which: str = "state") -> None:
        ms = market_states.get(name) or {}
        want = ms.get("previous") if which == "previous" else ms.get("state")
        if which == "previous" and "previous" not in ms:
            return                      # no stored previous to hold it to
        if word != (str(want).lower() if want is not None else None):
            key = (name, which, word)
            if key not in seen:
                seen.add(key)
                out.append(f"{name} {'was' if which == 'previous' else 'is'} "
                           f"called {word}, stored "
                           f"{want if want is not None else 'absent'}")

    vocab = {n: [str(w).lower() for w in (m.get("vocabulary") or [])]
             for n, m in market_states.items()}
    names = sorted(vocab, key=len, reverse=True)
    for name in names:
        words = vocab[name]
        if not words:
            continue
        W = "(" + "|".join(map(_re.escape, sorted(words, key=len,
                                                     reverse=True))) + ")"
        N = r"(?<![\w-])" + _name_re(name) + r"(?![\w])"
        # transition
        for m in _re.finditer(N + fill + verb + r"\s+from\s+" + W + r"\s+to\s+" + W
                              + r"(?![\w-])", masked):
            claim(name, m.group(1), "previous")
            claim(name, m.group(2))
        # after (not when it is the start of a transition, handled above)
        for m in _re.finditer(N + fill + r"\s+" + W + r"(?![\w/-])", masked):
            claim(name, m.group(1))
        # before
        for m in _re.finditer(r"(?<![\w-])" + W + r"\s+" + _name_re(name)
                              + r"(?![\w-])", masked):
            claim(name, m.group(1))
    # pairs: "<a>-vs-<b> ... w1/w2" within one clause of 90 characters
    for a in names:
        for b in names:
            if a == b:
                continue
            P = (r"(?<![\w])" + _name_re(a) + r"[\s_-]+(?:vs\.?|versus)[\s_-]+"
                 + _name_re(b) + r"(?![\w])")
            for m in _re.finditer(P, masked):
                tail = masked[m.end():m.end() + 90].split(". ")[0]
                pm = _re.search(r"(?<![\w-])([a-z_]+)\s*/\s*([a-z_]+)(?![\w-])",
                                tail)
                if pm and pm.group(1) in vocab[a] and pm.group(2) in vocab[b]:
                    claim(a, pm.group(1))
                    claim(b, pm.group(2))
    return out


def presence_misstatements(text: str) -> list[str]:
    """Sentences that call something missing from the object.

    Every declared row is in the object -- an absent one carries `absent:
    true` and its reason -- so the claim is never true of anything the payload
    holds. The 28 September draft said narrative_vs_data was "absent from the
    object entirely" while the row sat in the payload with its reason.
    """
    import re as _re  # noqa: PLC0415
    return [m.group(0) for m in _re.finditer(PRESENCE_PATTERN, text)]


def generate(payload: dict, *, model: Optional[str] = None,
             unit_constants: Optional[list] = None,
             client=None, system_prompt: Optional[str] = None,
             guide_path=None, max_chars: Optional[int] = None,
             one_paragraph: bool = True, split=None,
             citable_ids: Optional[Any] = None,
             cite_word: str = "event",
             citable_events: Optional[list] = None,
             market_states: Optional[dict] = None) -> NarrativeResult:
    """One paragraph over `payload`, audited, or an honest refusal.

    Never raises. `client` is injectable so the validation gate can exercise
    every branch -- including a model that lies -- without a network call or a key.

    `system_prompt` and `guide_path` let a SECOND report use this machinery with
    its own brief. The Weekly Tactical passes both, and everything that makes the
    machinery worth reusing stays fixed: print precision at the boundary, the
    numeral audit, the model pin, thinking off, the rejected text kept. What a
    report may vary is its coverage and its length; what it may not vary is whether
    a figure it prints exists.
    """
    model = model or DEFAULT_MODEL
    res = NarrativeResult(model=model)

    # THE MODEL NEVER SEES A FIGURE THE REPORT WOULD NOT PRINT. Applied here, at
    # the boundary the rule is about, rather than trusting every caller to have
    # done it: the transform is idempotent, so a payload that already conforms
    # passes through unchanged and one that does not cannot reach the prompt.
    #
    # The audit then compares the prose against THE SAME rounded payload, which is
    # the other half of the rule -- a percentile the model could not see is a
    # percentile it cannot print, and the reader never finds the paragraph and the
    # table beside it disagreeing in the fourth decimal.
    payload = precision.apply(payload)
    # EVERY PERCENTILE CARRIES ITS ORDINAL, already rounded half up (1 Oct 2026):
    # the model truncated 51.7 to "51st" and the audit withheld the paragraph.
    # Done here, the one funnel the close, the anchor, the Weekly and the Monthly
    # all pass through, so no report's payload can reach the model without it --
    # and the audit below reads the same augmented payload.
    payload = numeral_audit.with_ordinals(payload)
    # AND EVERY MOVE ITS SIGNED DISPLAY FORM, the same way (1 Oct 2026): "fell
    # 6.75%" for -6.75 withheld the Monthly's fiscal section twice. The model
    # copies `<field>_signed`; the sign rule is unchanged.
    payload = numeral_audit.with_signed(payload)

    if client is None:
        client, why = _client()
        if client is None:
            res.state = "unavailable"
            res.reason = why
            log.info("narrative skipped: %s", why)
            return res

    try:
        prompt = build_prompt(payload, guide_path)
    except PromptTooLarge as exc:
        res.state = "prompt_too_large"
        res.reason = str(exc)
        log.warning("narrative withheld: %s", res.reason)
        return res
    kwargs: dict = {
        "model": model,
        "max_tokens": MAX_TOKENS,
        "system": system_prompt or SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": prompt}],
        # SEE MAX_TOKENS. Disabled deliberately and not by omission: it was
        # ON by default here, and it consumed the entire budget.
        "thinking": {"type": "disabled"},
    }
    try:
        try:
            resp = client.messages.create(**kwargs)
        except TypeError:
            # AN SDK THAT DOES NOT KNOW THE PARAMETER MUST NOT COST THE PARAGRAPH.
            # The raised cap alone is enough to reach the text when thinking stays
            # on, so falling back is a degradation in cost and not in outcome --
            # and the fallback is recorded on the result rather than silent.
            kwargs.pop("thinking")
            resp = client.messages.create(**kwargs)
            res.reason = "thinking parameter unsupported by this SDK; cap alone"
        text = "".join(b.text for b in resp.content
                       if getattr(b, "type", None) == "text").strip()
    except Exception as exc:  # noqa: BLE001 -- transport, quota, timeout, all one case here
        # AN OUTAGE MUST NEVER READ LIKE A REFUSAL. The class is in the reason, so
        # a withheld line says "model call failed: RateLimitError" and not
        # something a reader could mistake for the model declining to answer or
        # for the audit rejecting a figure.
        res.state = "call_failed"
        res.reason = f"model call failed: {type(exc).__name__}: {exc}"
        log.warning("narrative call failed: %s", res.reason)
        return res

    # A model that records its own id is preferred over the one we asked for:
    # they are the same today and an alias that resolved elsewhere is exactly
    # what the pin exists to make visible.
    res.model = getattr(resp, "model", None) or model

    if not text:
        # "THE MODEL RETURNED NO TEXT" IS TRUE AND USELESS. It was the withheld
        # reason on Tuesday, and it cannot distinguish a reply cut off at the cap
        # from a model that answered with an empty string -- which are a
        # configuration fault and a model fault, fixed in different places. The
        # reply's own account of itself goes in the reason: why it stopped, which
        # block types came back, and how many output tokens were spent.
        stop = getattr(resp, "stop_reason", None)
        kinds = [getattr(b, "type", None) for b in (resp.content or [])] or ["none"]
        usage = getattr(resp, "usage", None)
        spent = getattr(usage, "output_tokens", None)
        thinking = getattr(getattr(usage, "output_tokens_details", None),
                           "thinking_tokens", None)
        res.state = "empty"
        if stop == "max_tokens":
            res.reason = (
                f"the reply hit the {MAX_TOKENS}-token cap before emitting any "
                f"text (stop_reason=max_tokens, blocks={kinds}, "
                f"output_tokens={spent}"
                + (f" of which {thinking} thinking" if thinking else "")
                + ") -- a budget fault, not a refusal")
        else:
            res.reason = (f"the model returned no text (stop_reason={stop}, "
                          f"blocks={kinds}, output_tokens={spent})")
        log.warning("narrative withheld: %s", res.reason)
        return res
    # A BRIEF MAY CARRY A STRUCTURED TAIL (6c-2: the morning scan's PROPOSALS
    # block). It is taken off BEFORE any prose rule runs -- length, markdown, the
    # audit -- because it is not prose: a proposal's horizon_days is not a figure
    # the paragraph claims, and auditing it as one would withhold every morning
    # that proposed anything. The caller validates what was split off.
    if split is not None:
        try:
            text, res.extra = split(text)
        except Exception as exc:                               # noqa: BLE001
            res.extra = {"split_error": f"{type(exc).__name__}: {exc}"}
        text = (text or "").strip()
        if not text:
            res.state = "empty"
            res.reason = "the reply held a structured block and no prose"
            return res
    # SET BEFORE EVERY REJECTION BELOW, so no branch can forget it. It is not
    # `text`: that field is what gets published, and a rejected paragraph must be
    # impossible to publish by accident.
    res.rejected_text = text

    # THE LENGTH RULES BELONG TO A BRIEF, NOT TO THIS MACHINERY, and the first
    # weekly run proved it: a 2,961-character reflection was withheld as "too_long
    # -- the brief is one paragraph" against a brief that explicitly permits long
    # form and states no word count. The limit was the close report's, applied to a
    # report that does not have it.
    #
    # So both are parameters. For the close they are unchanged: 2,600 characters
    # and one paragraph. For the weekly the ceiling is a RUNAWAY GUARD rather than
    # a style rule -- it exists so a model that lost the thread produces a refusal
    # instead of forty pages -- and blank lines are permitted, because several
    # paragraphs are correct when the week had several things in it.
    ceiling = MAX_CHARS if max_chars is None else max_chars
    if len(text) > ceiling:
        # Not truncated. A paragraph that overran its brief has not followed the
        # brief, and publishing half of one would publish a sentence nobody wrote.
        res.state = "too_long"
        res.reason = (f"{len(text)} characters against a {ceiling} limit"
                      + (" -- the brief is one paragraph" if one_paragraph
                         else " -- the ceiling is a runaway guard, not a style "
                              "rule, so this reply lost the thread rather than "
                              "merely running long"))
        return res
    if one_paragraph and "\n\n" in text.strip():
        res.state = "not_one_paragraph"
        res.reason = "the reply contains a blank line; the brief is one paragraph"
        return res

    # MARKDOWN IS BANNED BY THE BRIEF AND WAS ENFORCED BY NOTHING.
    #
    # The weekly's first published paragraph opened with `**Week ending Friday 18
    # September.**` and the reader would have seen the asterisks: these reports are
    # HTML, the renderer escapes what it is given, and it must -- a renderer that
    # interpreted markdown would be a renderer deciding what the prose meant.
    #
    # So the rule the prompt already states is now checked. Withheld rather than
    # stripped: stripping would publish a sentence the model did not write, and the
    # difference between "the brief says no markdown" and "we quietly remove it" is
    # the difference between a rule and a preference.
    marks = [m for m in ("**", "##", "\n- ", "\n* ", "__") if m in text]
    if marks:
        res.state = "markdown_found"
        res.reason = (f"the reply contains markdown ({', '.join(marks)!r}) and "
                      f"these reports are HTML -- the renderer escapes what it is "
                      f"given, so a reader would see the characters")
        log.warning("narrative withheld: %s", res.reason)
        return res

    # THE GATE. Every numeral in the prose against the payload it was given.
    result = numeral_audit.audit(text, payload, extra_values=unit_constants)
    res.audit = result
    res.figures_checked = len(result.figures)

    # TRACEABILITY (6c-2). Where a brief lets the prose cite stored events, every
    # cited id must be one the payload carries. The numeral audit alone would pass
    # "event 48" whenever 48 appeared anywhere in the payload -- as a count, say --
    # so the citation is checked against the ID SET, not against the numbers.
    if citable_ids is not None:
        import re as _re  # noqa: PLC0415
        allowed = {int(i) for i in citable_ids}
        cited = [int(m) for m in _re.findall(
            rf"\b{_re.escape(cite_word)}s?\s+(\d+)", text, flags=_re.I)]
        res.cited_ids = sorted(set(cited))
        res.untraceable = sorted(set(c for c in cited if c not in allowed))
        # 6c-3: quoted, not described; and absent is a field, not a gap.
        if citable_events is not None:
            res.citation_checked = True
            res.miscited = citation_contradictions(text, citable_events, cite_word)
            res.presence = presence_misstatements(text)
        if market_states is not None:
            res.states_checked = True
            res.misstated = state_contradictions(text, market_states)
        if res.untraceable:
            res.state = "untraceable"
            res.reason = (f"the prose cites event ids the payload does not carry: "
                          f"{res.untraceable[:8]}")
            log.warning("narrative withheld: %s", res.reason)
            return res
        if res.miscited:
            res.state = "miscited"
            res.reason = (f"a citation's adjacent type or source contradicts the "
                          f"stored event: {res.miscited[:4]}")
            log.warning("narrative withheld: %s", res.reason)
            return res
        if res.misstated:
            res.state = "state_misstated"
            res.reason = (f"a state named beside a dial or dimension is not the "
                          f"stored one: {res.misstated[:4]}")
            log.warning("narrative withheld: %s", res.reason)
            return res
        if res.presence:
            res.state = "presence_misstated"
            res.reason = (f"the prose calls a present row missing from the "
                          f"object: {res.presence[:3]}")
            log.warning("narrative withheld: %s", res.reason)
            return res

    if not result.passed:
        res.state = "audit_failed"
        res.unmatched = [f.text for f in result.unmatched]
        res.reason = result.reason()
        log.warning("narrative withheld: %s", res.reason)
        return res

    res.text = text
    res.state = "published"
    res.reason = result.reason()
    return res
