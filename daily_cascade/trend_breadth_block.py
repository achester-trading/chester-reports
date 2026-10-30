"""
Signal-triage Batch 16 item 89(b) (B76): where trend breadth prints.

    positioning_subsection(st, now)    the Weekly's and the Monthly's Positioning
                                       & flows: each market's four signs and its
                                       state, the week's flips, the reversing
                                       share, the window and n

Report only. A table and code-written lines: no paragraph, no chart, nothing in
the daily close. It reads the stored trend.* rows (altdata/trend_breadth.read)
and computes no signal. A fault costs the sub-section, never the section.
"""

from __future__ import annotations

import logging
from typing import Optional

log = logging.getLogger(__name__)

TITLE = "Trend breadth: our own cross-asset signal"


def positioning_subsection(st, now: str) -> Optional[dict]:
    from altdata import trend_breadth as tb                     # noqa: PLC0415
    try:
        r = tb.read(st, now)
    except Exception:                                           # noqa: BLE001
        log.warning("the trend-breadth read faulted", exc_info=True)
        return None
    return {"title": TITLE, "table": tb.table(r), "lines": tb.lines(r),
            "paragraph_wanted": False, "table_note": tb.NOTE,
            "data": {"trend_breadth": {"held": r["held"], "named": r["named"],
                                       "with_state": r["with_state"],
                                       "share": r["share"], "flips": r["flips"]}}}
