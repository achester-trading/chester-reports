"""
Signal-triage Batch 17, item 97 -- where the Capitulation Count and the sector
divergence line print (docs/change-order-signal-triage-batch-17-2026-10-26.md; B79).

    close_items(st, cutoff)        the close's Positioning & flows, ON EXCEPTION: the
                                   count when it changed from the prior session or
                                   reached the oversold band (2 or more), with each
                                   family ticked and table 3's caption; 97(c)'s line
                                   when the VXN-VIX spread is above its 90th
                                   percentile or SMH's drawdown is more than twice
                                   the S&P 500's
    weekly_subsection(st, now)     the Weekly's Positioning & flows, every Sunday the
                                   S&P 500 is more than 5% below its 52-week high:
                                   the count beside the T&B verdict, table 3's read
                                   as a one-line caption, and 97(c)'s line

The reads are altdata/capitulation_count.py's; this module only lays them out.
Every line is data (`paragraph_wanted: False`), and nothing here enters a
composite, the T&B verdict or the market-state object. A read that faults is
logged and the section stands without it.
"""

from __future__ import annotations

import logging
from typing import Optional

from altdata import capitulation_count as cc

log = logging.getLogger(__name__)

TITLE = "Capitulation Count"


def _item(key: str, text: str, priority: int = 2, value=None) -> dict:
    from .stack import item                                     # noqa: PLC0415
    return item(key, text, priority, value)


def close_items(st, cutoff: str, cfg: Optional[dict] = None) -> list[dict]:
    try:
        cfg = cfg or cc.config()
        c = cc.build(st, cutoff, cfg)
        v = cc.divergence(st, cutoff, cfg)
    except Exception:                                           # noqa: BLE001
        log.warning("capitulation count faulted", exc_info=True)
        return []
    out = []
    if cc.close_wanted(c, cfg):
        text = "; ".join([cc.count_line(c)] + cc.family_lines(c)
                         + [cc.table_3_caption(cc.tb_verdict(), c, cfg)])
        out.append(_item("pos:capitulation_count", text, 1, (c["count"], c["scorable"])))
    if v["exception"]:
        out.append(_item("pos:sector_divergence", cc.divergence_line(v), 2,
                         (v["spread_pct"], v["sector_dd"])))
    return out


def weekly_subsection(st, now: str, cfg: Optional[dict] = None) -> Optional[dict]:
    try:
        cfg = cfg or cc.config()
        dd = cc.weekly_wanted(st, now, cfg)
        if dd is None:
            return None
        c = cc.build(st, now, cfg)
        v = cc.divergence(st, now, cfg)
    except Exception:                                           # noqa: BLE001
        log.warning("capitulation count faulted", exc_info=True)
        return None
    lines = ([f"S&P 500 {dd['drawdown_pct']:.1f}% from its 52-week high ({dd['high'][0]})",
              cc.count_line(c)] + cc.family_lines(c)
             + [cc.table_3_caption(cc.tb_verdict(), c, cfg), cc.divergence_line(v)])
    return {"title": TITLE, "lines": lines, "paragraph_wanted": False,
            "data": {"capitulation_count": {"count": c["count"], "scorable": c["scorable"],
                                            "label": c["label"], "direction": c["direction"],
                                            "families": {f["id"]: f["state"] for f in c["families"]}},
                     "sector_divergence": {"exception": v["exception"]}}}
