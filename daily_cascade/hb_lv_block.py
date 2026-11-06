"""
The high-beta / low-vol divergence flag in the close's "what doesn't fit"
(signal-triage Batch 22 item 118, the order's 100; A128, 6 Nov 2026). The figures
are altdata/hb_lv.py's; this module lays out one line on a fired day and
computes nothing of its own. No line on a quiet day, and none at the 07:00
anchor.
"""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)


def close_extras(built: dict, st, day: str, cutoff: str) -> None:
    """On a fired day: one item in What doesn't fit, with both figures and "no
    rights until the backtest". Never raises."""
    from altdata import hb_lv                                   # noqa: PLC0415
    mis = built.get("misfit")
    if mis is None:
        return
    try:
        f = hb_lv.for_session(st, day, cutoff)
    except Exception:                                           # noqa: BLE001
        log.warning("the high-beta / low-vol flag faulted", exc_info=True)
        return
    mis.setdefault("data", {})["hb_lv_divergence"] = {
        "fired": f.get("fired"), "index_chg_pct": f.get("index_chg"),
        "ratio_chg_pct": f.get("ratio_chg")}
    if not f.get("fired"):
        return
    from .stack import item                                     # noqa: PLC0415
    mis["items"] = [i for i in mis.get("items") or [] if i.get("key") != "misfit:none"]
    mis["items"].append(item("misfit:hb_lv_divergence", f["line"], 1,
                             (round(f["index_chg"], 1), round(f["ratio_chg"], 1))))
