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
        # A95: a published attempt is news, not a warning (the 1 Nov Monthly's
        # log carried thirteen WARNING lines for paragraphs that published).
        log.info("audit retry: %s/%s attempt %d of %d published", report, section,
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


# ---------------------------------------------------------------------------
# W10-1: THE FALLBACK -- WITHHOLD THE SENTENCE, NOT THE SECTION (D46, 31 Oct 2026)
# ---------------------------------------------------------------------------
# On 28 Oct the Monthly's dry run withheld 20 of 61 sections whole, most of them
# right but for one figure's binding. After the second attempt fails on the FIGURE
# audit alone, the sentences that carry a failed figure are removed and the rest
# published, a marker in each removed sentence's place. It only removes: no figure
# is edited, and the audit's verdicts are the audit's. The limits (D46 1):
#   - more than a third of the sentences fail, or the first does -> whole, as today;
#   - the Précis and "Our read" (and the stack's read, the same synthesis) always
#     withhold whole: their sentences lean on each other;
#   - any fault that is not a figure's (filler, a misstated state, the length, the
#     shape, the vocabulary) -> whole: removing a sentence does not cure it;
#   - a failed figure the fallback cannot place in a sentence -> whole.
# The caller re-runs its own post-audit checks on what remains and withholds
# whole if any fires: the remainder is held to every rule a draft is.
MARKER = "[one sentence withheld: figure audit]"
WHOLE_ONLY = ("precis", "our_read", "read")
# The figure audits' clause heads; a clause that opens otherwise is not a figure's.
_FIGURE_HEAD = re.compile(r"^(?:numeral audit failed on|role audit failed on|"
                          r"a change of 10,000 or more printed without its unit)", re.I)
# What may follow a figure clause inside it: a role audit's item, a count tail,
# the role rule's sentence, the bare delta's instruction or hint.
_CONTINUATION = re.compile(r"^(?:'[^']+':\s|\d+ of them\b|write\s|'closed at'|"
                           r"copy its\s)", re.I)
_PREFIX = re.compile(r"^(?:narrative\s+)?withheld:\s*", re.I)
# The two forms the numeral audit's figures are listed in: the withheld note's
# "failed on 4 figures (a, b)" (cut at six) and reason()'s "failed on 4 figure(s):
# a (why), b (+2 more)".
_NOTE_FIGS = re.compile(r"numeral audit failed on (\d+) figures? \(([^()]*)\)")
_REASON_FIGS = re.compile(r"numeral audit failed on (\d+) figure\(s\): (.+?)"
                          r"(?=;\s*\d+ of them|$)")
_BARE_FIGS = re.compile(r"without its unit or scale \(([^()]*)\)")
_LIST_SPLIT = re.compile(r",\s+(?![^()]*\))")
# A role audit's item: 'closes ... 1st': -- the span is followed by its colon.
_ROLE_SPAN = re.compile(r"'([^']+? \.\.\. [^']+?)':")


def _clauses(reason: str) -> list[str]:
    r = _PREFIX.sub("", str(reason or "").strip())
    r = re.sub(r"\s+--\s+", "; ", r)
    return [c.strip() for c in r.split("; ") if c.strip()]


def figure_only(reason: Optional[str]) -> bool:
    """Every fault the reason names is a figure audit's (numeral, role, bare
    delta): the faults that removing a sentence cures."""
    cl = _clauses(reason or "")
    if not cl or not _FIGURE_HEAD.match(cl[0]):
        return False
    return all(_FIGURE_HEAD.match(c) or _CONTINUATION.match(c) for c in cl[1:])


def failed_figures(reason: Optional[str],
                   unmatched: Optional[list] = None) -> tuple[Optional[list], list]:
    """(figures, spans): each failed figure's text, and each quoted span ("closes
    ... 1st") the role audit names. `unmatched`, the audit's own full list, stands
    in for the numeral audit's listed figures, which the reason cuts at six; a cut
    list with no `unmatched` gives (None, spans): not every failed figure is known."""
    r = str(reason or "")
    spans = _ROLE_SPAN.findall(r)
    figs = [q.split(" ... ")[-1].strip() for q in spans]
    for m in _BARE_FIGS.finditer(r):
        figs += [x.strip() for x in _LIST_SPLIT.split(m.group(1))]
    if unmatched is not None:
        figs += [str(getattr(f, "text", f)) for f in unmatched]
    else:
        for rx in (_NOTE_FIGS, _REASON_FIGS):
            for m in rx.finditer(r):
                listed = [x.split(" (")[0].strip()
                          for x in _LIST_SPLIT.split(re.sub(r"\s*\(\+\d+ more\)", "",
                                                            m.group(2)))]
                if len([x for x in listed if x]) < int(m.group(1)):
                    return None, spans
                figs += listed
    return [f for f in dict.fromkeys(figs) if f], spans


def _hits(sentence: str, fig: str) -> bool:
    """The figure's text in the sentence as a whole token: "5.2" is not in
    "15.29"."""
    return bool(re.search(r"(?<![\d.,])" + re.escape(fig) + r"(?![\d])", sentence))


def partial(draft: Optional[str], reason: Optional[str], *, section: str = "",
            unmatched: Optional[list] = None) -> dict:
    """The fallback's verdict over a twice-withheld draft: {"ok": True, "text":
    the published text with markers, "clean": the remainder without them (what
    the caller's post-checks read), "withheld": [{"sentence", "reason"}], "k",
    "n"}, or {"ok": False, "why": the reason it stays withheld whole}."""
    sec = str(section or "").split(":")[-1]
    if sec in WHOLE_ONLY:
        return {"ok": False, "why": "withheld whole: its sentences depend on each other"}
    if not draft:
        return {"ok": False, "why": "no draft"}
    if not figure_only(reason):
        return {"ok": False, "why": "a fault that is not a figure's"}
    figs, spans = failed_figures(reason, unmatched)
    if figs is None or not figs:
        return {"ok": False, "why": "a failed figure the reason does not list"}
    paras = [_sentences(p) for p in str(draft).strip().split("\n\n") if p.strip()]
    flat = [s for p in paras for s in p]
    bad: dict[int, list[str]] = {}
    for q in spans:
        parts = [x.strip() for x in q.split(" ... ") if x.strip()]
        idx = [i for i, s in enumerate(flat)
               if all(p.lower() in s.lower() for p in parts[:-1]) and _hits(s, parts[-1])]
        if not idx:
            return {"ok": False, "why": f"span '{q}' not placed in a sentence"}
        for i in idx:
            bad.setdefault(i, []).append(parts[-1])
    span_figs = {q.split(" ... ")[-1].strip() for q in spans}
    for fig in figs:
        if fig in span_figs:
            continue
        # Every sentence carrying the figure goes: the published text never
        # holds a figure the audit failed.
        idx = [i for i, s in enumerate(flat) if _hits(s, fig)]
        if not idx:
            return {"ok": False, "why": f"figure {fig} not placed in a sentence"}
        for i in idx:
            bad.setdefault(i, []).append(fig)
    n, k = len(flat), len(bad)
    if 0 in bad:
        return {"ok": False, "why": "its first sentence fails", "k": k, "n": n}
    if 3 * k > n:
        return {"ok": False, "why": f"{k} of {n} sentences fail (more than a third)",
                "k": k, "n": n}
    out, clean, i = [], [], 0
    for p in paras:
        kept, shown = [], []
        for s in p:
            shown.append(MARKER if i in bad else s)
            if i not in bad:
                kept.append(s)
            i += 1
        out.append(" ".join(shown))
        if kept:
            clean.append(" ".join(kept))
    withheld = [{"sentence": flat[j], "reason": "figure audit: " + ", ".join(
        dict.fromkeys(bad[j]))} for j in sorted(bad)]
    return {"ok": True, "text": "\n\n".join(out), "clean": "\n\n".join(clean),
            "withheld": withheld, "k": k, "n": n}


def status(k: int) -> str:
    """The section's status for a partial publication."""
    return f"published, {k} sentence{'' if k == 1 else 's'} withheld"


def apply_fallback(res: dict, *, report: str, section: str,
                   recheck: Optional[Callable[[str], list]] = None) -> dict:
    """A twice-withheld result through the fallback: published with markers
    (state "published_partial", `partial` k, `withheld_sentences`, `status`), or
    unchanged with `fallback` saying why it stays whole. `recheck(clean)` is the
    caller's own post-audit checks over the remainder; any fault keeps it whole.
    Each withheld sentence and its reason go to the run log."""
    if res.get("published") or int(res.get("attempts") or 0) < ATTEMPTS:
        return res
    p = partial(res.get("rejected_text"), res.get("retry_reason") or res.get("reason"),
                section=section, unmatched=res.get("unmatched_figures"))
    if not p["ok"]:
        return {**res, "fallback": p["why"]}
    faults = list(recheck(p["clean"]) if recheck else [])
    if faults:
        return {**res, "fallback": "the remainder fails: " + "; ".join(map(str, faults[:3]))}
    for w in p["withheld"]:
        log.warning("audit fallback: %s/%s sentence withheld (%s): %s", report,
                    section, w["reason"], w["sentence"])
    log.warning("audit fallback: %s/%s %s", report, section, status(p["k"]))
    return {**res, "published": True, "state": "published_partial", "text": p["text"],
            "partial": p["k"], "sentences": p["n"], "withheld_sentences": p["withheld"],
            "status": status(p["k"])}


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
