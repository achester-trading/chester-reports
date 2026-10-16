"""
"What's carrying the index" and the allocation block -- where they print.

    priced_subsection(st, now, cadence, margin=True)
        What's priced: one "What's carrying the index" sub-section (Batch 6,
        section 4 ruling 2): the decomposition table at the cadence's anchors --
        the Weekly's twelve months and year to date, the Monthly's three with
        the log-share split -- then the read, r-g and the revisions-turn flag,
        the price-ULC gap, and (when the edition has no earnings block to carry
        it) the margin-source line. Its chart is W11 / M11.
    margin_line(st, now)
        the margin-source line, for the earnings block when it is in season
    positioning_subsection(st, now)
        Positioning & flows: the three-panel allocation block (item 30, ruling 3)
    close_items(st, cutoff)
        the close's What's priced: the one-line read only (item 40)

The reads are altdata/st_r5_index.py's; this module only lays them out, asks
no paragraph of either sub-section (`paragraph_wanted: False`), and never lets a
fault take a section down.
"""

from __future__ import annotations

import logging
from typing import Optional

from altdata import st_r5_index as ix

log = logging.getLogger(__name__)

TITLE = "What's carrying the index"
ALLOC_TITLE = "Investor allocation: equities, bonds and cash"
ANCHORS = {"weekly": ("twelve_months", "ytd"),
           "monthly": ("cycle_low", "twelve_months", "ytd")}
COLUMNS = ["Anchor", "EPS basis", "From", "S&P 500", "EPS change", "P/E", "EPS share (log)",
           "P/E share (log)"]
ALLOC_COLUMNS = ["Panel", "Share", "Quarter", "Change on the quarter",
                 "Percentile (window, n)"]


def _item(key: str, text: str, priority: int = 2, value=None) -> dict:
    from .stack import item                                     # noqa: PLC0415
    return item(key, text, priority, value)


def _share(v: Optional[float]) -> str:
    return "—" if v is None else f"{v:.0f}%"


def decomposition_rows(d: dict, anchors: tuple) -> list[list[str]]:
    rows = []
    if d.get("absent"):
        return rows
    for ver in ("forward", "trailing"):
        v = d["versions"].get(ver) or {}
        if v.get("state") != "read":
            rows.append(["All anchors", ver, v.get("reason") or "not read",
                         "—", "—", "—", "—", "—"])
            continue
        for aid in anchors:
            a = v["anchors"].get(aid) or {}
            lab = ix.ANCHOR_LABELS.get(aid, aid)
            if a.get("absent") or not a:
                rows.append([lab, ver, a.get("reason", "—"), "—", "—", "—", "—", "—"])
                continue
            rows.append([lab, ver, a["start_day"], f"{a['price_pct']:+.1f}%",
                         f"{a['eps_pct']:+.1f}%",
                         f"{a['pe_start']:.1f} to {a['pe_end']:.1f}",
                         _share(a["eps_share_pct"]), _share(a["pe_share_pct"])])
    return rows


def priced_subsection(st, now: str, cadence: str = "weekly", margin: bool = True,
                      cfg: Optional[dict] = None) -> Optional[dict]:
    try:
        cfg = cfg or ix.config()
        b = ix.build(st, now, cfg)
    except Exception:                                           # noqa: BLE001
        log.warning("what's carrying the index faulted", exc_info=True)
        return None
    anchors = ANCHORS.get(cadence, ANCHORS["weekly"])
    d = b["decomposition"]
    lines = [ix.read_line(d)]
    lines += ix.r_minus_g_lines(b["r_minus_g"])
    lines += ix.price_ulc_lines(b["price_ulc"])
    if margin:
        lines.append(ix.margin_line(b["price_ulc"]))
    note = ("Price = EPS × P/E, so the log change of the S&P 500 splits exactly "
            "into the log change of EPS and of the P/E; each share is that leg's "
            "part of the move, printed when the move is at least 1% in logs. "
            "Forward EPS is S&P DJI's bottom-up operating estimate for the next "
            "twelve months, from the operator's drop of its workbook; it carries the "
            "revisions caveat, so the trailing version (Shiller's trailing twelve "
            "months, monthly) runs beside it. g is the estimates' growth into the "
            "second forward year. Flags are descriptive and unvalidated.")
    return {"title": b.get("header") or TITLE,
            "table": {"columns": COLUMNS,
                      "rows": decomposition_rows(d, anchors)},
            "lines": lines, "paragraph_wanted": False, "table_note": note,
            "data": {"index_carry": {k: b[k] for k in
                                     ("decomposition", "r_minus_g", "price_ulc")}}}


def margin_line(st, now: str, cfg: Optional[dict] = None) -> Optional[str]:
    try:
        return ix.margin_line(ix.price_ulc(st, now, cfg or ix.config()))
    except Exception:                                           # noqa: BLE001
        log.warning("margin-source line faulted", exc_info=True)
        return None


def positioning_subsection(st, now: str, cfg: Optional[dict] = None) -> Optional[dict]:
    try:
        a = ix.allocation(st, now, cfg or ix.config())
    except Exception:                                           # noqa: BLE001
        log.warning("allocation block faulted", exc_info=True)
        return None
    return {"title": ALLOC_TITLE,
            "table": {"columns": ALLOC_COLUMNS, "rows": ix.allocation_rows(a)},
            "lines": ix.allocation_lines(a), "paragraph_wanted": False,
            "not_tracked": ix.allocation_absent(a),
            "table_note": ("Federal Reserve Z.1 (Financial Accounts), households and "
                           "nonprofits, via FRED, quarterly with about a ten-week lag. "
                           "Equities are the Fed's published share, directly and "
                           "indirectly held; bonds are debt securities directly held "
                           "(Z.1 does not split fund shares by type); cash is "
                           "currency, deposits and money funds. Amends SR-12."),
            "data": {"allocation": a}}


def close_items(st, cutoff: str, cfg: Optional[dict] = None) -> list[dict]:
    """The close carries the one-line read only (item 40)."""
    try:
        cfg = cfg or ix.config()
        d = ix.decomposition(st, cutoff, cfg)
        anchor = (cfg.get("decomposition") or {}).get("close_anchor", "twelve_months")
        line = ix.read_line(d, anchor)
    except Exception:                                           # noqa: BLE001
        log.warning("what's carrying the index (close) faulted", exc_info=True)
        return []
    return [_item("priced:index_carry", line, 2, line)]
