"""
The Monthly's paragraph: the brief and the template path. (Phase 4b piece 3)

    from monthly_macro.narrative import monthly_system_prompt, TEMPLATE_PATH

THE MACHINERY IS THE CLOSE REPORT'S, and that is the point: print precision at the
model boundary, the numeral audit, the model pin, thinking off, the rejected text
kept, markdown refused. A report may vary its coverage and its length; it may not
vary whether a figure it prints exists.

-----------------------------------------------------------------------------
WHAT THIS REPLACES, AND WHY THE PLACEHOLDER HAD TO GO
-----------------------------------------------------------------------------

This module used to walk the rendered Markdown replacing markers of the form
`*[NARRATIVE PLACEHOLDER — 4-paragraph synthesis: regime, data story, cross-pillar,
matrix implication]*`, one API call per pillar, with a MAX_CALLS cost guard.

Ten of those markers asked a model to CHARACTERISE THE REGIME FROM THE PILLARS --
once per pillar, with no shared state, each call seeing one pillar's levels. That is
the defect Audit #3 section G names from the other end: the regime lived nowhere, so
the report asked prose to supply it ten times over, and the ten answers had no
obligation to agree with each other or with anything the close report had published.

The regime now comes from the object, the pillars are inputs printed beneath the
dial each one feeds, and there is ONE paragraph over ONE payload with the audit
behind it. The placeholder is deleted rather than repointed: a marker that asked for
a regime is a marker with nowhere left to point.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = REPO / "docs" / "narrative-template-monthly.md"

# THE RUNAWAY GUARD, not a word count -- the same distinction the weekly draws. A
# month with a dial change, a scenario table and a register section needs room; a
# reply past this has lost the thread rather than run long.
MAX_CHARS = 14000


def monthly_system_prompt() -> str:
    """The Monthly's brief, on top of the shared rules."""
    from daily_cascade import narrative as base
    return base.SYSTEM_PROMPT + (
        "\n\nTHIS IS THE MONTHLY REGIME & ALLOCATION REPORT. Five differences from "
        "the close report:\n"
        "\n1. LENGTH IS WHATEVER THE MONTH NEEDS. No word count. Several "
        "paragraphs are right when the month had several things in it.\n"
        "\n2. THE HORIZON IS THE MONTH, and the comparison is against THE PREVIOUS "
        "MONTHLY, which the payload names. Do not write about a session.\n"
        "\n3. THE REGIME COMES FROM THE OBJECT AND YOU DO NOT CHARACTERISE IT FROM "
        "THE PILLARS. The dials and dimensions in the payload were computed by the "
        "close pass; the pillars are INPUTS to them, with declared weights. Say "
        "what the dials read, what changed since the previous Monthly, and which "
        "pillars a reader should look at because of it. Never infer a regime of "
        "your own from the pillar series -- a second regime is the defect this "
        "report was restructured to remove.\n"
        "\n4. COVER, in this order: the regime and what changed; the scenario "
        "weights WITH THEIR BRIER SCORES, and what an unresolved weight permits "
        "you to say (nothing, about accuracy); the Top & Bottom verdict with the "
        "bear-rally base rate on any top-side language; the alternative-asset "
        "families that have data and the ones that do not; the register's month "
        "with its expectancy INTERVAL READ BEFORE THE POINT. Say what is not "
        "sourced where the payload says so.\n"
        "\n5. NO RECOMMENDATION and NO ALLOCATION ADVICE. The report is named for "
        "allocation and the register's rules decide it: state the bands' inputs, "
        "never a stance.\n")
