"""
Signal-triage Batch 14, item 63 (written as 56) -- where the AI capex chain prints
(b52-batch14-a2). The reads are altdata/capex_chain.py's; this module lays them out.

    slow_subsection()             the Monthly's slow layers, Factor I: BNP Paribas's
                                  $100 of AI capex, the standing dated table
    priced_subsection(st, now)    the Monthly's what's priced: the capex-chain
                                  relative-performance line

Report only. Tables and code-written lines: no paragraph, no chart.
"""

from __future__ import annotations

import logging
from typing import Optional

from altdata import capex_chain as cc

log = logging.getLogger(__name__)

TITLE_TABLE = "Factor I, the AI capex chain: who gets paid (BNP Paribas, August 2026)"
TITLE_LINE = "The AI capex chain: which bucket leads"


def slow_subsection(cfg: Optional[dict] = None) -> Optional[dict]:
    try:
        ref = cc.reference(cfg)
    except Exception:                                           # noqa: BLE001
        log.warning("the capex-chain reference table faulted", exc_info=True)
        return None
    return {"title": TITLE_TABLE, "table": cc.reference_table(ref),
            "lines": [f"A standing reference table, dated {ref['dated']}: {ref['caveat']}"],
            "paragraph_wanted": False,
            "table_note": f"Source: {ref['source']}. The proxies the relative line reads "
                          f"are config/capex_chain.yaml's, each with its reason.",
            "data": {"capex_chain_reference": ref}}


def priced_subsection(st, now: str, cfg: Optional[dict] = None) -> Optional[dict]:
    try:
        r = cc.relative(st, now, cfg)
    except Exception:                                           # noqa: BLE001
        log.warning("the capex-chain relative line faulted", exc_info=True)
        return None
    return {"title": TITLE_LINE, "lines": cc.relative_lines(r), "paragraph_wanted": False,
            "data": {"capex_chain_relative": r}}
