"""
THE AUDIT RETRY (W8-1, weekly-fixes-8, 18 Oct 2026).

The first live Weekly (18 Oct) withheld three of its ten commentaries -- the
précis, Plumbing ("filler: a bare figure with nothing to read it against: 'EM
high-yield OAS widened +5 bp'") and Narratives ("runs 159 words; its band is 80
to 150") -- each on something a second draft fixes in one pass. The retry they
had was told the reason and the rule and asked to write the section AGAIN, from
the data alone, so it wrote a new draft with new faults instead of mending the
old one.

So the retry is a REVISION, and there is one of it:

  - the same data block, unchanged (the user message is the first call's,
    byte for byte; only the system prompt grows);
  - the draft the audit withheld, whole;
  - the failing rule's text and the failing span -- the quoted fragment the
    audit named, or the sentence holding the figure it named, or the draft as a
    whole when the fault is its length or shape;
  - the instruction to fix that and change nothing else.

The revision is audited exactly as the draft was. A second failure withholds,
printing the SECOND reason, as the withheld line always has. A fault that is not
the prose's -- no client, a failed call, a payload past its guard, an empty
reply, a runaway length -- is never retried. Both attempts are logged to the run
log (the EL-6 withheld-drafts log takes them once it merges; it is not built
here). The cost is one extra model call per failed audit, bounded to one.

Every report that uses the loop goes through here: the stacked close, the
Weekly and the stacked Monthly (daily_cascade/stack_prose.py), the précis
(daily_cascade/precis.py), the classic close (close_report.py) and the morning
anchor (morning_anchor.py).
"""

from __future__ import annotations

import logging
import re
from typing import Any, Callable, Optional

log = logging.getLogger(__name__)

# One retry, never more (W8-1): the draft, then one revision.
ATTEMPTS = 2

# narrative.generate's states that are an AUDIT's refusal of the prose, and so
# the prose's to fix. Everything else (unavailable, prompt_too_large,
# call_failed, empty, too_long) is not retried.
NARRATIVE_RETRIED = ("audit_failed", "untraceable", "miscited", "state_misstated",
                     "presence_misstated", "markdown_found", "not_one_paragraph")

REVISE = ("Revise THAT draft: fix exactly the failing span under the rule above and "
          "change nothing else -- every other sentence, figure and word stays as "
          "it is. The data block is the one you were given; it has not changed.")

_QUOTED = re.compile(r"(?<![A-Za-z])'(.+?)'(?![A-Za-z])")
_FIGURE_LIST = re.compile(r"failed on \d+ figure\(s\): (.+?)(?:;\s*\d+ of them|$)")
_BOUND = re.compile(r"([-+−]?\d[\d,.]*\s?%?) is bound to")
_SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'(])")


def _sentences(text: str) -> list[str]:
    return [s for s in _SENT.split((text or "").strip()) if s.strip()]


def failing_spans(reason: Optional[str], draft: Optional[str]) -> list[str]:
    """The spans of the draft the audit named: each quoted fragment, and the
    sentence holding each figure the numeral audit refused. Empty when the
    fault is the draft's length or shape, which no span carries."""
    r, d = str(reason or ""), str(draft or "")
    out: list[str] = []
    for q in _QUOTED.findall(r):
        q = q.strip().rstrip(".")
        if len(q) < 3:
            continue
        hit = next((s for s in _sentences(d) if q[:40] in s), None)
        out.append(hit or q)
    figs = [m.group(1).strip() for m in _BOUND.finditer(r)]
    for m in _FIGURE_LIST.finditer(r):
        figs += [x.split(" (")[0].strip() for x in re.split(r",\s+(?![^()]*\))", m.group(1))]
    for fig in figs:
        hit = next((s for s in _sentences(d) if fig and fig in s), None)
        if hit:
            out.append(hit)
    return list(dict.fromkeys(out))


def revision_note(reason: Optional[str], draft: Optional[str]) -> str:
    """What the one retry is told, appended to the section's own system prompt:
    the withhold message and the rule behind each fault (opener.retry_note's
    wording, which every gate reads), the failing span, the draft, and the
    instruction to revise it and change nothing else."""
    from . import opener                                        # noqa: PLC0415
    note = opener.retry_note(reason, 2, ATTEMPTS)
    if not draft:
        return note
    spans = failing_spans(reason, draft)
    span = ("\nTHE FAILING SPAN" + ("S" if len(spans) > 1 else "") + ":\n- "
            + "\n- ".join(spans) if spans else
            "\nTHE FAILING SPAN: the draft as a whole (the fault is its length or "
            "shape, so shorten or reshape it and keep its sentences' content).")
    return (note + span + "\nYOUR DRAFT:\n<<<\n" + str(draft).strip() + "\n>>>\n"
            + REVISE)


def log_attempt(report: str, section: str, attempt: int, published: bool,
                reason: Optional[str], draft: Optional[str]) -> None:
    """One attempt in the run log: published or withheld, the reason, and the
    draft the audit read (logged, never rendered)."""
    if published:
        log.warning("audit retry: %s/%s attempt %d of %d published", report, section,
                    attempt, ATTEMPTS)
        return
    log.warning("audit retry: %s/%s attempt %d of %d withheld: %s", report, section,
                attempt, ATTEMPTS, reason)
    if draft:
        log.warning("audit retry: %s/%s attempt %d draft (NOT published): %s",
                    report, section, attempt, draft)


def generate(payload: dict, *, report: str, section: str = "narrative",
             **kw: Any):
    """narrative.generate() with the one revision: when the audit withholds the
    draft, the same payload goes back once with the revision note appended to the
    system prompt. Returns the second result when there is one, carrying
    `attempts` and `first_reason`. Never raises."""
    from . import narrative                                     # noqa: PLC0415
    first = narrative.generate(payload, **kw)
    _record(report, section, 1, first)
    first.attempts = 1
    if first.published or first.state not in NARRATIVE_RETRIED:
        return first
    system = kw.pop("system_prompt", None) or narrative.SYSTEM_PROMPT
    second = narrative.generate(
        payload, system_prompt=system + revision_note(
            first.withheld_note() if first.state != "audit_failed" else first.reason,
            first.rejected_text), **kw)
    _record(report, section, 2, second)
    second.attempts = 2
    second.first_reason = first.reason
    return second


def _record(report: str, section: str, attempt: int, r) -> None:
    log_attempt(report, section, attempt, bool(r.published),
                None if r.published else r.reason, None if r.published
                else getattr(r, "rejected_text", None))


def run(call: Callable[[Optional[str]], dict], *, report: str, section: str,
        retryable: Callable[[dict], bool]) -> dict:
    """The stack's and the précis's shape: `call(None)` drafts; when the audit
    withholds the draft and `retryable` says the fault is the prose's,
    `call(note)` revises it once with the revision note. Returns the last result
    with `attempts` (and `first_reason` when withheld twice)."""
    first = call(None)
    log_attempt(report, section, 1, bool(first.get("published")),
                first.get("reason"), first.get("rejected_text"))
    if first.get("published") or not retryable(first):
        return {**first, "attempts": 1}
    note = revision_note(first.get("retry_reason") or first.get("reason"),
                         first.get("rejected_text"))
    res = call(note)
    log_attempt(report, section, 2, bool(res.get("published")),
                res.get("reason"), res.get("rejected_text"))
    res = {**res, "attempts": 2}
    if not res.get("published"):
        res["first_reason"] = first.get("reason")
    return res
