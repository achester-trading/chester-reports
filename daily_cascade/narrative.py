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

log = logging.getLogger("daily_cascade.narrative")

# PINNED, and pinned deliberately rather than tracking a floating alias. The
# paragraph is graded over time against what it said, so the writer has to be
# identifiable: a silent model change would break the comparison without
# breaking anything visible. The version is recorded on the artifact.
DEFAULT_MODEL = os.environ.get("CLOSE_NARRATIVE_MODEL", "claude-sonnet-5")

# One call per report. Not a budget to spend — a bound, so a retry loop cannot
# turn one report into a bill.
MAX_CALLS = 1
MAX_TOKENS = 700

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

Cover, in this order, only what the payload supports: the regime (spot versus the \
flip, and how long on that side); the hedge flow and its change; the corridor \
(walls, their movement, where gamma concentrates); what the vol complex says and \
what it does not; the position (fill, close, distance to invalidation in points \
and percent, and the rule); and the system's scorecard (the pin tally, the \
cross-check when present, and what the day put at stake). Omit anything the \
payload does not contain rather than reaching for it.
"""


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

    @property
    def published(self) -> bool:
        return bool(self.text) and self.state == "published"

    def withheld_note(self) -> str:
        """The one line the data-only edition carries in place of the prose."""
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
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None, "ANTHROPIC_API_KEY is not set"
    try:
        import anthropic  # noqa: PLC0415
    except ImportError:
        return None, "the anthropic package is not installed"
    try:
        return anthropic.Anthropic(), ""
    except Exception as exc:  # noqa: BLE001
        return None, f"client construction failed: {type(exc).__name__}: {exc}"


def style_guide() -> str:
    """The committed template, which is the style contract.

    Read from docs/ rather than embedded so the operator edits one file and both
    the model and the human reading the spec see the same thing. Absent, the
    system prompt above still carries the rules that matter.
    """
    try:
        return TEMPLATE_PATH.read_text(encoding="utf-8")
    except OSError:
        log.warning("%s unreadable; relying on the system prompt alone",
                    TEMPLATE_PATH)
        return ""


def build_prompt(payload: dict) -> str:
    """The user turn: the style guide, then the figures, and nothing else."""
    import json  # noqa: PLC0415
    guide = style_guide()
    return (
        (f"=== STYLE AND COVERAGE SPECIFICATION ===\n{guide[:6000]}\n\n"
         if guide else "")
        + "=== THE PAYLOAD. Every number you write must come from here. ===\n"
        + json.dumps(payload, indent=2, default=str, sort_keys=True)[:12000]
        + "\n\nWrite the paragraph."
    )


def generate(payload: dict, *, model: Optional[str] = None,
             unit_constants: Optional[list] = None,
             client=None) -> NarrativeResult:
    """One paragraph over `payload`, audited, or an honest refusal.

    Never raises. `client` is injectable so the validation gate can exercise
    every branch — including a model that lies — without a network call or a key.
    """
    model = model or DEFAULT_MODEL
    res = NarrativeResult(model=model)

    if client is None:
        client, why = _client()
        if client is None:
            res.state = "unavailable"
            res.reason = why
            log.info("narrative skipped: %s", why)
            return res

    try:
        resp = client.messages.create(
            model=model,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": build_prompt(payload)}],
        )
        text = "".join(b.text for b in resp.content
                       if getattr(b, "type", None) == "text").strip()
    except Exception as exc:  # noqa: BLE001 -- transport, quota, timeout, all one case here
        res.state = "call_failed"
        res.reason = f"{type(exc).__name__}: {exc}"
        log.warning("narrative call failed: %s", res.reason)
        return res

    # A model that records its own id is preferred over the one we asked for:
    # they are the same today and an alias that resolved elsewhere is exactly
    # what the pin exists to make visible.
    res.model = getattr(resp, "model", None) or model

    if not text:
        res.state = "empty"
        res.reason = "the model returned no text"
        return res
    if len(text) > MAX_CHARS:
        # Not truncated. A paragraph that overran its brief has not followed the
        # brief, and publishing half of one would publish a sentence nobody wrote.
        res.state = "too_long"
        res.reason = (f"{len(text)} characters against a {MAX_CHARS} limit -- "
                      f"the brief is one paragraph")
        return res
    if "\n\n" in text.strip():
        res.state = "not_one_paragraph"
        res.reason = "the reply contains a blank line; the brief is one paragraph"
        return res

    # THE GATE. Every numeral in the prose against the payload it was given.
    result = numeral_audit.audit(text, payload, extra_values=unit_constants)
    res.audit = result
    res.figures_checked = len(result.figures)
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
