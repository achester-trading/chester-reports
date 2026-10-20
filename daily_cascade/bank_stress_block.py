"""
Signal-triage Batch 12, item 59 -- where the bank-stress panel prints (ruled 20 Oct
2026; the order's Placement).

    close_items(st, cutoff)          the close's Plumbing & rates, beside item 34's
                                     cluster: the two flags in one line, and the
                                     classifier's status
    read_items(st, cutoff)           The read: the classifier's line, only when it
                                     prints (KRE down more than 10% over 20 sessions)
    weekly_subsection(st, now)       the Weekly's one-line panel status
    monthly_subsection(st, now)      the Monthly's full panel: every series with its
                                     dual percentiles, the flags, the classifier,
                                     the unrealised losses beside the 10-year, and
                                     the listed gaps

The reads are altdata/bank_stress.py's; this module only lays them out. Every
sub-section is data (`paragraph_wanted: False`), and nothing here enters a
composite, a trigger or the market-state object. A read that faults is logged and
the section stands without it.
"""

from __future__ import annotations

import logging
from typing import Optional

from altdata import bank_stress as bs
from altdata import st_r5_rates as rt

log = logging.getLogger(__name__)

TITLE = "Bank stress"
COLUMNS = ["Series", "Latest", "As of", "Percentiles (five years; long window)", "Source"]


def _item(key: str, text: str, priority: int = 2, value=None) -> dict:
    from .stack import item                                     # noqa: PLC0415
    return item(key, text, priority, value)


def _build(st, cutoff: str, cfg: Optional[dict] = None) -> Optional[dict]:
    try:
        return bs.build(st, cutoff, cfg)
    except Exception:                                           # noqa: BLE001
        log.warning("bank-stress block faulted", exc_info=True)
        return None


def close_items(st, cutoff: str, cfg: Optional[dict] = None) -> list[dict]:
    b = _build(st, cutoff, cfg)
    if b is None:
        return []
    on = b["funding"].get("on") or b["deposit"].get("on")
    return [_item("plumb:bank_stress", bs.status_line(b), 1 if on else 2,
                  (b["funding"]["state"], b["deposit"]["state"],
                   b["classifier"]["state"]))]


def read_items(st, cutoff: str, cfg: Optional[dict] = None) -> list[dict]:
    b = _build(st, cutoff, cfg)
    line = bs.classifier_line(b["classifier"]) if b else None
    if not line:
        return []
    return [_item("read:bank_stress", line, 1, b["classifier"]["state"])]


def weekly_subsection(st, now: str, cfg: Optional[dict] = None) -> Optional[dict]:
    b = _build(st, now, cfg)
    if b is None:
        return None
    return {"title": TITLE, "lines": [bs.status_line(b)], "paragraph_wanted": False,
            "data": {"bank_stress": {k: b[k] for k in ("funding", "deposit", "classifier")}}}


def panel_rows(b: dict) -> list[list[str]]:
    out = []
    for r in b["panel"]:
        if r["state"] != "ok":
            out.append([r["label"], "—", "—", r.get("reason") or "—", r["source"]])
            continue
        out.append([r["label"], bs.fmt(r["value"], r["unit"]), r["as_of"],
                    rt.lens_text(r["lens"]), r["source"]])
    return out


def monthly_subsection(st, now: str, cfg: Optional[dict] = None) -> Optional[dict]:
    cfg = cfg or bs.config()
    b = _build(st, now, cfg)
    if b is None:
        return None
    windows = "; ".join(f"{k.replace('_', ' ')}: {v}"
                        for k, v in (cfg.get("long_windows") or {}).items())
    note = ("Item 59 (Batch 12, ruled 20 Oct 2026). Each series prints its five-year "
            "percentile and its family's long window, with each window's n. The long "
            f"windows: {windows}. Listed gaps: " + "; ".join(b["gaps"]) + ". Flags and "
            "the classifier only: no composite, trigger or dial reads them, and their "
            "base rate is the ST-R6.59c ledger's.")
    return {"title": TITLE, "table": {"columns": COLUMNS, "rows": panel_rows(b)},
            "lines": bs.lines(b), "paragraph_wanted": False, "table_note": note,
            "data": {"bank_stress": b}}
