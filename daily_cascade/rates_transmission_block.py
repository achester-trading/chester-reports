"""
Signal-triage Batch 6, the rates-transmission cluster -- where it prints.

    close_items(st, cutoff, session_day)  the close's Plumbing & rates (light):
                                          the tightening flag, the quality tail's
                                          headline and co-signal, and on a
                                          Wednesday the MBA line
    subsection(st, now, cadence)          the Weekly's and the Monthly's Plumbing
                                          & rates: one "Rates transmission"
                                          sub-section, the G8 2-year panel as its
                                          table and the four items' lines

Section 4's cross-item ruling 1: items 34, 36, 37 and 41 are one mechanism and
print together under one header in Plumbing & rates. Item 37's weekly line prints
"in the Wednesday daily close and the Weekly"; the monthly housing block prints
in the Weekly and the Monthly (its figures carry their month). The reads are
altdata/st_r5_rates.py's; this module only lays them out, and asks no paragraph
of the sub-section (`paragraph_wanted: False`).
"""

from __future__ import annotations

import logging
from typing import Optional

from altdata import st_r5_rates as rt

log = logging.getLogger(__name__)

TITLE = "Rates transmission"
COLUMNS = ["Country", "2-year", "2-year, 28 days", "10-year, 28 days", "Read",
           "Source, as of"]


def _item(key: str, text: str, priority: int = 2, value=None) -> dict:
    from .stack import item                                     # noqa: PLC0415
    return item(key, text, priority, value)


def _bp(v: Optional[float]) -> str:
    return "—" if v is None else f"{v:+.0f} bp"


def panel_rows(rows: list[dict]) -> list[list[str]]:
    out = []
    for r in rows:
        if r["state"] == "gap":
            out.append([r["label"], "gap", "—", "—", r["reason"], "—"])
        elif r["state"] == "absent":
            out.append([r["label"], "—", "—", "—", r["reason"], r.get("source") or "—"])
        else:
            read = {"tightening": "10-year up, 2-year down: the market tightening",
                    "not": "—", "short": r.get("reason", "—")}[r["state"]]
            out.append([r["label"], f"{r['level']:.2f}%", _bp(r.get("two_bp")),
                        _bp(r.get("ten_bp")), read, f"{r['source']}, {r['as_of']}"])
    return out


def lines(b: dict) -> list[str]:
    out = [rt.tightening_line(b["tightening"])]
    out += rt.housing_lines(b["housing"])
    out.append(rt.mba_line(b["mba"]))
    out += rt.quality_tail_lines(b["quality_tail"])
    return out


def subsection(st, now: str, cadence: str = "weekly",
               cfg: Optional[dict] = None) -> Optional[dict]:
    """The one sub-section, or None if the read faults (logged; the section
    stands without it)."""
    try:
        cfg = cfg or rt.config()
        b = rt.build(st, now, cfg)
    except Exception:                                           # noqa: BLE001
        log.warning("rates transmission block faulted", exc_info=True)
        return None
    gaps = [r["label"] for r in b["panel"] if r["state"] == "gap"]
    note = (f"Item 34's 2-year panel stands in for 12-month swaps pricing, which is "
            f"proprietary; the US leg of the flag reads 100 less the fed funds future "
            f"twelve months ahead. Gaps, each with its reason in the table: "
            f"{', '.join(gaps) or 'none'}. The euro area's 2-year is Germany's, from "
            f"the Bundesbank's fitted curve. FRED serves the ICE BofA spreads from "
            f"October 2023 only, so each percentile names the window it covers and "
            f"its n. Housing is monthly (Redfin) with the MBA purchase index as its "
            f"weekly line; the MBA level and NAR's index are entered by hand. Flags "
            f"are descriptive and unvalidated: no state, trigger or overlay reads "
            f"them.")
    return {"title": b.get("header") or TITLE,
            "table": {"columns": COLUMNS, "rows": panel_rows(b["panel"])},
            "lines": lines(b), "paragraph_wanted": False,
            "table_note": note, "data": {"rates_transmission": b}}


def close_items(st, cutoff: str, session_day: str,
                cfg: Optional[dict] = None) -> list[dict]:
    """The close prints light: the flag, the quality tail's headline and its
    co-signal, and the MBA line on the release Wednesday."""
    try:
        cfg = cfg or rt.config()
        t = rt.tightening(st, cutoff, cfg)
        q = rt.quality_tail(st, cutoff, cfg)
        m = rt.mba(st, cutoff, cfg)
    except Exception:                                           # noqa: BLE001
        log.warning("rates transmission close items faulted", exc_info=True)
        return []
    out = [_item("plumb:rt_tightening", rt.tightening_line(t),
                 1 if t["state"] == "on" else 2, (t["state"], t.get("ten_bp"),
                                                   t.get("policy_bp")))]
    ql = rt.quality_tail_lines(q)
    out.append(_item("plumb:rt_quality_tail", " ".join(ql[:2]),
                     1 if q.get("cosignal") == "on" else 2,
                     (q.get("ccc_bb"), q.get("cosignal"))))
    if rt.mba_prints_on(session_day, m, cfg):
        out.append(_item("plumb:rt_mba", rt.mba_line(m), 2,
                         (m.get("week"), m.get("yoy_pct"))))
    return out
