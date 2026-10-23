"""
Signal-triage Batch 14, item 66 (written as 59) -- where the loosening leg and the
net-transmission line print (b52-batch14-a2): the Monthly's Plumbing & rates, after
the rates-transmission sub-section. The reads are altdata/transmission.py's.

    subsection(st, now)   "Rates transmission: the loosening leg" -- the
                          wealth-effect impulse and the four legs side by side

Report only. Lines only: no paragraph, no chart.
"""

from __future__ import annotations

import logging
from typing import Optional

from altdata import transmission as tr

log = logging.getLogger(__name__)

TITLE = "Rates transmission: the loosening leg"


def subsection(st, now: str, cfg: Optional[dict] = None) -> Optional[dict]:
    try:
        b = tr.net(st, now, cfg)
    except Exception:                                           # noqa: BLE001
        log.warning("the net-transmission line faulted", exc_info=True)
        return None
    w = b["impulse"]
    note = ("The impulse is Z.1's household equity share of financial assets times "
            "SPX's year-on-year return, monthly. Between Z.1 releases the share is "
            "marked to SPX from its quarter's end, labelled where it stands in. "
            f"{w.get('ici_gap', '')[0:1].upper()}{w.get('ici_gap', '')[1:]}. Report only: "
            "the calibration ledger against real consumption grants nothing by itself.")
    return {"title": TITLE, "lines": tr.net_lines(b), "paragraph_wanted": False,
            "table_note": note, "not_tracked": [b["k_shape_gap"]],
            "data": {"transmission": {k: v for k, v in b.items() if k != "impulse"},
                     "wealth_impulse": {k: v for k, v in w.items() if k != "series"}}}
