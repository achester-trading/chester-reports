"""
The vol-state read's prints (signal-triage Batch 23 item 124c(i); B134, 6 Nov
2026). altdata/vol_state.py reads and lays out; this module places:

- the close: one Mechanics sub-section after item 52's block (and after item
  65's speed attribution, which sits directly after it), every session;
- the Weekly: one row, the week's deciles, in Mechanics.

Read from stored rows only; nothing here computes a state or writes the store.
A fault costs the block, never the report.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

log = logging.getLogger(__name__)

TITLE = "Vol state"
AFTER = ("Volatility event",)


def _item(key: str, text: str, priority: int, value: Any = None) -> dict:
    from .stack import item                                     # noqa: PLC0415
    return item(key, text, priority, value)


def close_extras(built: dict, st, cutoff: str) -> None:
    """The close: the block after item 52's (or first), and its decile line."""
    mech = built.get("mechanics")
    if mech is None or st is None:
        return
    try:
        from altdata import vol_state as vs                     # noqa: PLC0415
        from altdata import speed_attribution as sa             # noqa: PLC0415
        r = vs.read(st, cutoff)
        sub = vs.block(r)
    except Exception:                                           # noqa: BLE001
        log.warning("the vol-state block faulted", exc_info=True)
        return
    subs = mech.setdefault("subsections", [])
    titles = set(AFTER) | {getattr(sa, "TITLE", "")}
    at = max((i for i, x in enumerate(subs) if x.get("title") in titles), default=-1)
    subs.insert(at + 1, sub)
    mech.setdefault("items", []).append(
        _item("mech:vol_state", sub["lines"][0], 2, r.get("decile")))
    mech.setdefault("data", {})["vol_state"] = {
        "decile": r.get("decile"), "day": r.get("day"), "k": r.get("k")}


def weekly_subsection(st, cutoff: str, sessions: Optional[list[str]]) -> list[dict]:
    """The Weekly's one row; no paragraph."""
    try:
        from altdata import vol_state as vs                     # noqa: PLC0415
        line = vs.week_row(st, cutoff, list(sessions or []))
    except Exception:                                           # noqa: BLE001
        log.warning("the vol-state row faulted", exc_info=True)
        return []
    return [{"title": TITLE, "table": None, "paragraph_wanted": False, "lines": [line]}]
