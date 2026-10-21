"""
Batch 14 Part A1's slow-layer sub-section (a56): item 64's excess CAPE yield and
item 69's real home price percentile since 1890, in the Monthly's slow layers.

The order places the excess CAPE yield in the valuation quad of what's priced,
amending GTM-2; GTM-2's quad is not built in this repo, so it prints here, beside
the slow layers' Valuation table that stands in for it. The real home price sits
"beside the Reinhart-Rogoff input", which is the Top & Bottom model's and not in
this repo, so it prints on its own line here. Item 69's two spreads print in the
housing block (rates_transmission_block) and item 70's anchor in the 10-year
attribution (batch5_block). Report only.
"""

from __future__ import annotations

import logging
from typing import Optional

from altdata import batch14_a1 as b14

log = logging.getLogger(__name__)

TITLE = "The excess CAPE yield and real home prices since 1890 (Batch 14)"


def slow_subsection(st, now: str) -> Optional[dict]:
    try:
        ecy = b14.excess_cape_yield(st, now)
        home = b14.real_home_price(st, now)
    except Exception:                                           # noqa: BLE001
        log.warning("batch 14 slow sub-section faulted", exc_info=True)
        return None
    return {"title": TITLE, "lines": [b14.ecy_line(ecy), b14.home_line(home)],
            "paragraph_wanted": False,
            "not_tracked": [b14.NOT_TRACKED["forward_ecy"], b14.NOT_TRACKED["scorecard"]],
            "table_note": ("Each percentile ranks the latest value against the store's "
                           "own history, over five years and in full, with its n and "
                           "first date. The excess CAPE yield here is the cyclically "
                           "adjusted earnings yield less DFII10, labelled so: Shiller's "
                           "own measure uses a different real rate. Real home prices are "
                           "ranked one point a year. Descriptive; no flag, state or "
                           "composite reads them."),
            "data": {"batch14_a1": {"ecy": ecy, "home": home}}}
