"""
THE INFLATION BLOCK of Plumbing & rates (6e, the rest, 16 Oct 2026): the CPI lead
composite and the core CPI less core PCE gap, as tables and lines only. The
Weekly's (weekly cadence); the figures are altdata/cpi_lead.py's and
altdata/derived.py's, nothing is computed here.

THE BLOCK IS A LIST OF PANELS, so the next 6e paste attaches without rearranging
it. Two slots are reserved and print nothing until filled:

  "decomposition"  Batch 7 item 46 (ST-R6.46a/b): the CPI decomposition panel --
                   contributions from energy, food, core goods, shelter and core
                   services ex shelter; the Cleveland Fed median and 16% trimmed
                   mean; diffusion; and the pass-through flag. It attaches as a
                   builder returning one sub-section; the close's CPI-day line
                   reads the same builder's data.
  "labour"         Batch 7 item 48, group A (employment lenses 1-6 and the
                   cross-cutting 21-24): the labour block, its own sub-section
                   after the decomposition.

A builder takes (st, cutoff) and returns a sub-section dict or None; a reserved
slot is None and is skipped.
"""

from __future__ import annotations

import logging
from typing import Callable, Optional

log = logging.getLogger(__name__)

TITLE_LEAD = "The CPI lead composite: implied CPI three to nine months ahead"
TITLE_GAP = "Core CPI against core PCE"
TAG = "(stated lags, unvalidated)"


def _pct(v: Optional[float]) -> str:
    return "—" if v is None else f"{v:+.2f}%" if v < 0 else f"{v:.2f}%"


def lead_panel(st, cutoff: str) -> Optional[dict]:
    from altdata import cpi_lead                                 # noqa: PLC0415
    r = cpi_lead.read(st, cutoff)
    rows = []
    for h in r["horizons"]:
        val = "—" if r["withheld"] else _pct(h.get("value"))
        comps = ", ".join(f"{c['name']} ({c['lag']} months)" for c in h.get("components") or [])
        rows.append([f"{h['horizon']} months", val,
                     f"{100 * (h.get('covered_share') or 0):.0f}%",
                     comps or (h.get("reason") or "—")])
    lines = []
    kt = r["kill_test"]
    if r["withheld"]:
        lines.append(f"The composite is withheld: {kt['reason']}.")
    elif kt["state"] == "untested":
        lines.append(f"Kill test not yet run: {kt['reason']}.")
    else:
        lines.append(f"Kill test passed: correlation {kt['corr']:.2f} over {kt['n']} months.")
    missing = {m["name"]: m["reason"] for h in r["horizons"] for m in h.get("missing") or []
               if "lag" not in m["reason"]}
    if missing:
        lines.append("Not covered: " + "; ".join(f"{k}, {v}" for k, v in missing.items()) + ".")
    c, ro = r.get("conditioner"), r.get("rolloff")
    if c:
        lines.append(f"Realized ten-year CPI less the 10-year breakeven: "
                     f"{c['value']:+.2f} pp.")
    if ro and ro.get("paths"):
        lines.append("Roll-off: trailing ten-year CPI "
                     f"{ro['now']:.2f}% now; "
                     + "; ".join(f"{x['trailing_10y']:.2f}% after {x['months']} months "
                                 f"at {x['path_pct']}%" for x in ro["paths"]) + ".")
    return {"title": TITLE_LEAD, "paragraph_wanted": False,
            "table": {"columns": ["Horizon", "Implied CPI, year over year",
                                  "Basket covered", "Components (stated lag)"],
                      "rows": rows},
            "table_note": f"Each horizon reads only components whose stated lag "
                          f"reaches it, weighted by CPI basket share over the share "
                          f"covered {TAG}.",
            "lines": lines, "data": {"cpi_lead": r}}


def gap_panel(st, cutoff: str) -> Optional[dict]:
    from altdata import derived                                  # noqa: PLC0415
    lens = derived.lens_forms("calc.core_cpi_pce_gap", cutoff, store=st)
    if lens.get("level") is None:
        return None
    f, fl = lens["forms"], lens["flags"]
    line = (f"Core CPI less core PCE, year over year: {lens['level']:+.2f} pp, "
            f"the {f.get('pctile_5y_ordinal') or 'n/a'} percentile of five years.")
    if fl.get("sign_flipped"):
        line += (" The sign has flipped: core PCE runs above core CPI, where it "
                 "normally runs below on its smaller shelter weight.")
    return {"title": TITLE_GAP, "paragraph_wanted": False, "lines": [line],
            "data": {"core_cpi_pce_gap": {"level": lens["level"], "forms": f,
                                          "flags": fl}}}


# The panels in print order. None is a reserved slot (see the module docstring).
PANELS: list[tuple[str, Optional[Callable]]] = [
    ("lead", lead_panel),
    ("gap", gap_panel),
    ("decomposition", None),      # Batch 7 item 46 attaches here
    ("labour", None),             # Batch 7 item 48, group A, attaches here
]


def subsections(st, cutoff: str) -> list[dict]:
    out = []
    for name, build in PANELS:
        if build is None:
            continue
        try:
            sub = build(st, cutoff)
        except Exception:                                        # noqa: BLE001
            log.warning("inflation panel %s faulted", name, exc_info=True)
            continue
        if sub:
            out.append(sub)
    return out
