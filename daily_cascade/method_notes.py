"""
Method notes: one line an edition prints about how earlier editions were made.

    from daily_cascade.method_notes import for_edition
    for_edition("daily_close", "2026-09-28")     # -> [line, ...]

H-1 item 4. A note is DECLARED WITH THE EDITION IT BELONGS TO, not consumed by
whichever run happens to go first: a dry run or a failed attempt does not use it
up, a re-render of that edition still carries it, and every other edition never
does. "Once each" is therefore a property of the declaration, checkable by
reading it, rather than of a state file on one box.
"""

from __future__ import annotations

# (report, edition key, line). The edition key is the close's session date and
# the Weekly's week-ending Friday -- the identities each report already uses.
NOTES: tuple[tuple[str, str, str], ...] = (
    # INC-2 (docs/incidents.md): every close since 23 Sep and the first Weekly
    # were written from a prompt cut at 6,000/12,000 characters. The first
    # whole-brief close is session 2026-09-28; the first whole-brief Weekly is
    # the 4 Oct edition, week ending 2026-10-02.
    ("daily_close", "2026-09-28",
     "Editions before 28 Sep were written from a truncated brief — see INC-2 in "
     "docs/incidents.md."),
    ("weekly", "2026-10-02",
     "Editions before 28 Sep were written from a truncated brief — see INC-2 in "
     "docs/incidents.md."),
)


def for_edition(report: str, key: str | None) -> list[str]:
    """The notes declared for exactly this edition, in declaration order."""
    k = str(key or "")[:10]
    return [line for r, e, line in NOTES if r == report and e == k]
