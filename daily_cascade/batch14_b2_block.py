"""
Signal-triage Batch 14, Part B2 (b55): where item 62's table prints.

    slow_subsection(now, db_path)   the Monthly's slow layers: the cross-house
                                    capital-market-assumptions table, its read
                                    first (a lead), then the table, then each
                                    house's edition line
    book_a_line(st, now)            item 30's Book A long-horizon expected-return
                                    line, for the allocation block

Item 67's PEG/LTEG gap line rides item 60's lines (altdata/eps_overshoot.py) and
item 68's per-household line rides item 36's housing lines
(altdata/st_r5_rates.py); neither needs a block of its own.

Report only. Tables and code-written lines: no paragraph, no chart.
"""

from __future__ import annotations

import logging
from typing import Optional

log = logging.getLogger(__name__)


def slow_subsection(now: Optional[str], db_path: Optional[str] = None,
                    cfg: Optional[dict] = None) -> Optional[dict]:
    from altdata import cma_table as cma                        # noqa: PLC0415
    try:
        cfg = cfg or cma.config()
        r = cma.read(now, db_path, cfg)
    except Exception:                                           # noqa: BLE001
        log.warning("the cross-house CMA table faulted", exc_info=True)
        return None
    return {"title": cfg.get("title") or "Capital market assumptions across houses",
            "lead": cma.lead(r), "table": cma.table(r),
            "lines": cma.edition_lines(r), "paragraph_wanted": False,
            "table_note": ("Each figure is the house's own, as its edition published "
                           "it, stored from the reading shelf's publication watch "
                           "with its URL (the scans ingest); none is entered by hand. "
                           f"An edition older than {r['stale_months']} months is "
                           "dropped and counted. Report only: item 30's Book A line "
                           "prints the US-equity median; nothing enters a composite."),
            "data": {"cma_table": r}}


def book_a_line(st, now: Optional[str]) -> str:
    """The line, from the store the allocation block was given (its own path, so
    a gate's temporary store is the one read)."""
    from altdata import cma_table as cma                        # noqa: PLC0415
    path = getattr(st, "path", None)
    if path is None or not now:
        # No store named: nothing is read, never the default database.
        return cma.book_a_line(None)
    try:
        return cma.book_a_line(cma.read(now, str(path)))
    except Exception:                                           # noqa: BLE001
        log.warning("the Book A CMA line faulted", exc_info=True)
        return cma.book_a_line(None)
