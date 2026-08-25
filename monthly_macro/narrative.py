"""
Phase 5 — Narrative LLM step.

Takes the data-populated markdown report (containing *[NARRATIVE PLACEHOLDER —
...]* markers) and replaces each marker with a Claude-generated synthesis
paragraph grounded in that section's data tables.

Architecture decisions:

1. **Per-placeholder prompts.** Each placeholder gets its own API call with
   its own section's markdown as context plus the Pillar Snapshot for
   cross-pillar awareness. Higher quality than one mega-prompt.

2. **Opus for the monthly.** Model comes from $NARRATIVE_MODEL, defaulting to
   claude-opus-4-8 — monthly cadence means the cost delta is trivial and the
   synthesis quality matters. (The daily pathway, when built, uses Sonnet.)

3. **Graceful degradation, three layers:**
   - No ANTHROPIC_API_KEY -> step is skipped entirely, report ships with
     placeholders intact, workflow does not fail.
   - One API call fails -> that placeholder stays, everything else proceeds.
   - anthropic package missing -> same as no key.

4. **Cost guard.** Hard cap on calls per run (MAX_CALLS) so a renderer bug
   that emits 400 placeholders can't produce a surprise bill.
"""

from __future__ import annotations
import logging
import os
import re
from typing import Optional

log = logging.getLogger(__name__)

DEFAULT_MODEL = os.environ.get("NARRATIVE_MODEL", "claude-opus-4-8")
MAX_TOKENS_PER_CALL = 1200
MAX_CALLS = 25  # cost guard; report currently has ~14 placeholders

# Matches the exact marker style render_md.py emits, e.g.:
#   *[NARRATIVE PLACEHOLDER — 4-paragraph synthesis]*
# Tolerates em-dash or hyphen and any hint text.
PLACEHOLDER_RE = re.compile(r"^\*\[NARRATIVE PLACEHOLDER\s*[—-]\s*(?P<hint>[^\]]*)\]\*\s*$", re.MULTILINE)

SYSTEM_PROMPT = """You are the narrative engine for a monthly macro report written for a single sophisticated reader with institutional-markets fluency (actuarial and reinsurance background, decade of trading experience). Write in a McKinsey/Goldman institutional research register: synthesis-first, declarative, no hedging boilerplate, no exclamation points, no bullet lists — flowing analytical prose only.

Rules:
- Ground every claim in the data provided in the section context. Never invent numbers. If a series is missing or stale, say so plainly.
- Lead with the regime read, then the data story, then cross-pillar connections, then what would change the view.
- Do not use headers or markdown formatting; return only paragraph text.
- Do not restate the tables; interpret them.
- Match the length the placeholder hint requests (e.g. "4-paragraph synthesis" means four paragraphs; "regime characterization paragraph" means one)."""


def _get_client():
    """Return an Anthropic client, or None if the key or package is absent."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        log.info("ANTHROPIC_API_KEY not set — narrative step skipped, placeholders remain")
        return None
    try:
        import anthropic  # lazy import
    except ImportError:
        log.warning("anthropic package not installed — narrative step skipped")
        return None
    return anthropic.Anthropic()


def _split_sections(md: str) -> list[tuple[int, int, str]]:
    """Return (start, end, text) spans for each `## `-headed section."""
    heads = [m.start() for m in re.finditer(r"^## ", md, re.MULTILINE)]
    if not heads:
        return [(0, len(md), md)]
    spans = []
    for i, start in enumerate(heads):
        end = heads[i + 1] if i + 1 < len(heads) else len(md)
        spans.append((start, end, md[start:end]))
    return spans


def _section_for(pos: int, sections: list[tuple[int, int, str]], full_md: str) -> str:
    for start, end, text in sections:
        if start <= pos < end:
            return text
    return full_md[:4000]


def _snapshot_context(md: str) -> str:
    """Pull the Pillar Snapshot table (if present) as cross-pillar context."""
    m = re.search(r"^## Pillar Snapshot.*?(?=^## )", md, re.MULTILINE | re.DOTALL)
    return m.group(0) if m else ""


def _generate(client, model: str, hint: str, section_md: str, snapshot_md: str) -> str:
    prompt = (
        f"Placeholder instruction: {hint or 'synthesis paragraph'}\n\n"
        f"=== THIS SECTION (write the synthesis for this) ===\n{section_md[:8000]}\n\n"
        f"=== CROSS-PILLAR SNAPSHOT (context only) ===\n{snapshot_md[:4000]}"
    )
    resp = client.messages.create(
        model=model,
        max_tokens=MAX_TOKENS_PER_CALL,
        messages=[{"role": "user", "content": prompt}],
        system=SYSTEM_PROMPT,
    )
    text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip()
    if not text:
        raise RuntimeError("empty narrative response")
    return text


def add_narratives(md: str, model: Optional[str] = None) -> str:
    """Replace every narrative placeholder in `md` with generated prose.

    Never raises: on any failure the original marker is left in place and an
    annotation is appended, so the pipeline always produces a report.
    """
    client = _get_client()
    if client is None:
        return md

    model = model or DEFAULT_MODEL
    sections = _split_sections(md)
    snapshot = _snapshot_context(md)

    matches = list(PLACEHOLDER_RE.finditer(md))
    if not matches:
        log.info("No narrative placeholders found — nothing to do")
        return md
    if len(matches) > MAX_CALLS:
        log.warning("%d placeholders exceeds MAX_CALLS=%d; generating first %d only",
                    len(matches), MAX_CALLS, MAX_CALLS)
        matches = matches[:MAX_CALLS]

    log.info("Narrative step: %d placeholders, model=%s", len(matches), model)
    replacements: list[tuple[int, int, str]] = []
    failures = 0
    for m in matches:
        hint = (m.group("hint") or "").strip()
        section_md = _section_for(m.start(), sections, md)
        try:
            prose = _generate(client, model, hint, section_md, snapshot)
            replacements.append((m.start(), m.end(), prose))
            log.info("  generated: %s (%d chars)", hint[:60] or "(no hint)", len(prose))
        except Exception as e:  # noqa: BLE001 — per-placeholder isolation
            failures += 1
            log.warning("  FAILED for '%s': %s", hint[:60], e)

    # Apply replacements back-to-front so earlier offsets stay valid.
    for start, end, prose in sorted(replacements, reverse=True):
        md = md[:start] + prose + md[end:]

    if failures:
        md += (f"\n\n---\n*Narrative generation: {failures} of {len(matches)} "
               f"section(s) failed and retain placeholder markers.*\n")
    return md
