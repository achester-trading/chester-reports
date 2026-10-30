"""
The Monthly's Top & Bottom harness lines and the Quarterly's credit row (6i-4; A79,
26 Oct 2026; the 6i brief's section 2.5, decision 3 as recommended: no stored
composite).

The Monthly joins it through config/stack_hooks/monthly-slow-tb-harness.yaml, a
slow sub-section of three lines:

  1. the overlays' states as of the edition's cutoff, each with its trigger counts
     (Part 23's three, and the credit leg's Baa proxy beside HY Spread
     Acceleration), read through altdata/tb_harness.py from the store as of;
  2. the harness's episode record, k of n per class, from the newest calibration
     ledger (docs/ledgers/tb-harness-<date>-episodes.csv);
  3. the continuous false-positive rate per overlay with n, from the newest FPR
     ledger (docs/ledgers/tb-harness-fpr-<date>.csv).

It never prints or computes a composite: decision 3 stores none, and the
Monthly's own top_bottom_block keeps its absence line. Report-only: nothing here
enters a composite, the market-state object, a dial, a band or a packet.
"""

from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

from altdata import tb_harness as tb

log = logging.getLogger(__name__)
ET = ZoneInfo("America/New_York")
TITLE = "Top & Bottom: the harness's overlays and record"


def _day(now: str) -> str:
    return dt.datetime.fromisoformat(str(now).replace("Z", "+00:00")).astimezone(ET).date().isoformat()


def overlay_line(st, now: str, day: Optional[str] = None, cfg: Optional[dict] = None) -> str:
    cfg = cfg or tb.config()
    day = day or _day(now)
    ovs = tb.overlays_at(st, cfg, day, now)
    return (f"Overlays as of {day} (state, triggers fired of triggers, how many read; "
            f"each fires at {cfg['overlays'][0]['fires_at']} or more): "
            + "; ".join(f"{o['title']} {tb.state_text(o)}" for o in ovs) + ".")


def record_line(rec: Optional[dict]) -> str:
    if not rec:
        return "The harness's episode record: no calibration ledger is committed."

    def unread(r: dict) -> str:
        return f" ({r['unread']} unread)" if r["unread"] else ""

    t, c = rec["top"], rec["control"]
    return (f"The harness's episode record ({rec['ledger']}): tops {t['k']} of {t['n']} "
            f"called{unread(t)}, controls {c['k']} of {c['n']} refused{unread(c)}, "
            f"bottoms not scored ({rec['bottom']['n']}; the overlays are top-side).")


def fpr_line(fpr: Optional[dict], cfg: dict) -> str:
    if not fpr:
        return "The false-positive rate: no FPR ledger is committed."
    titles = {o["id"]: o["title"] for o in cfg["overlays"]}
    if not fpr["rows"]:
        return f"The false-positive rate ({fpr['ledger']}): pre-registered, not yet run."
    parts = []
    for r in fpr["rows"]:
        name = titles.get(r["overlay"], r["overlay"])
        parts.append(f"{name} " + (f"{100 * r['rate']:.1f}% (n={r['n']:,}, {r['runs']} runs)"
                                   if r["rate"] is not None else
                                   f"— (n=0; {r['scored']:,} of {r['sessions']:,} sessions scored)"))
    return (f"The false-positive rate per overlay ({fpr['ledger']}; a fire with no top "
            f"inside {cfg['fpr']['window_days']} days): " + "; ".join(parts) + ".")


def slow_subsection(st, now: str, ledger_dir: Optional[Path] = None) -> Optional[dict]:
    try:
        cfg = tb.config()
        rec, fpr = tb.latest_record(ledger_dir), tb.latest_fpr(ledger_dir)
        lines = [overlay_line(st, now, cfg=cfg), record_line(rec), fpr_line(fpr, cfg)]
    except Exception:                                           # noqa: BLE001
        log.warning("the T&B harness lines faulted", exc_info=True)
        return None
    return {"title": TITLE, "lines": lines, "paragraph_wanted": False,
            "table_note": ("Report-only: no composite is stored or printed (decision 3 "
                           "of 25 Oct 2026); nothing here enters a dial, a band or a "
                           "packet. The rules are config/tb_episodes.yaml's."),
            "data": {"tb_record": rec, "tb_fpr": fpr}}


def quarterly_row(st, overlay_id: str, ctx: dict) -> tuple[Optional[str], Optional[str], str]:
    """(text, as of, why-not) for a Quarterly row naming a harness overlay: its
    state at the quarter's end, with any proxy of it beside."""
    try:
        cfg = tb.config()
        day = str(ctx["end"])[:10]
        ovs = tb.overlays_at(st, cfg, day, ctx["now"])
    except Exception as exc:                                    # noqa: BLE001
        return None, None, f"the harness faulted ({type(exc).__name__})"
    mine = [o for o in ovs if o["id"] == overlay_id or o.get("proxy_of") == overlay_id]
    if not mine:
        return None, None, f"no overlay {overlay_id} in config/tb_episodes.yaml"
    return "; ".join(f"{o['title']} {tb.state_text(o)}" for o in mine), day, ""
