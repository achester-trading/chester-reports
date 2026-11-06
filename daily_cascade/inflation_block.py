"""
THE INFLATION BLOCK of Plumbing & rates (6e, the rest, 16 Oct 2026): the CPI lead
composite and the core CPI less core PCE gap, as tables and lines only. The
Weekly's (weekly cadence); the figures are altdata/cpi_lead.py's and
altdata/derived.py's, nothing is computed here.

THE BLOCK IS A LIST OF PANELS, so a later paste attaches without rearranging it.

  "decomposition"  Batch 7 item 46 (ST-R6.46a/b; 6e-releases, 16 Oct 2026): the
                   five contributions to the month's CPI, the Cleveland Fed median
                   and 16% trimmed mean, the diffusion, and the pass-through flag
                   with item 32's printed state. altdata/releases.py's figures; the
                   close's CPI-day line reads the same decomposition.
  "cpi_lenses"     Batch 7 item 48 lenses 7-11: the shelter lead, supercore,
                   sticky against flexible and goods against services, the base-
                   effect ladder, the CPI-PCE wedge with its weights.
  "ppi"            Batch 7 Group B, lenses 12-14 (ST-R6.48d; lenses-group-b, 18
                   Oct 2026): the intermediate-demand pipeline against final
                   demand, the PCE-relevant components, trade services apart --
                   one table, each row in the lens form (two percentiles with
                   their n, the disagreement). altdata/releases_b.py's figures.

Item 48's employment lenses (1-6) are NOT a panel here: they are the labour block,
daily_cascade/labour_block.py, the Monthly's own section after Plumbing.

A builder takes (st, cutoff) and returns a sub-section dict or None; a reserved
slot is None and is skipped. Every panel is tables and code-written lines: no
paragraph is asked for, so none adds a prose word to any budget.
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


TITLE_DECOMP = "What moved CPI: the decomposition, the median and the breadth"
TITLE_LENSES = "CPI lenses: shelter's lead, supercore, sticky and flexible, base effects"


def _pp(v: Optional[float], dp: int = 2) -> str:
    return "—" if v is None else f"{v:+.{dp}f}"


def decomposition_panel(st, cutoff: str) -> Optional[dict]:
    """Item 46a and 46b, one sub-section: the contributions as a table, the
    median, trimmed mean and diffusion, the pass-through flag and item 32's
    printed state, each a line."""
    from altdata import releases                                 # noqa: PLC0415
    cfg = releases.config()
    dc = releases.decomposition(st, cutoff, cfg)
    if dc.get("state") != "read":
        return None
    rows = [[p["name"], f"{100 * float(p['weight']):.1f}%", _pp(p["mm_pct"]),
             _pp(p["contribution_pp"]) if p["contribution_pp"] is not None
             else (p["reason"] or "—")] for p in dc["pieces"]]
    rows.append(["CPI, all items", "100%", _pp(dc["headline_mm_pct"]),
                 _pp(dc["headline_mm_pct"])])
    m = releases.month_name(dc["month"])
    lines = []
    if dc.get("residual_pp") is not None:
        lines.append(f"The five pieces sum to {_pp(dc['sum_pp'])} pp against the "
                     f"headline's {_pp(dc['headline_mm_pct'])}%: a residual of "
                     f"{_pp(dc['residual_pp'])} pp, the drift of the fixed December 2025 "
                     f"weights from this month's relative importance.")
    lines.append(f"Core CPI {_pp(dc['core_mm_pct'])}% on the month, "
                 f"{_pp(dc['core_yoy_pct'], 1)}% on the year.")
    med, tm = dc.get("median") or {}, dc.get("trimmed_mean") or {}
    if med.get("ann_pct") is not None and tm.get("ann_pct") is not None:
        lines.append(f"The middle of the distribution (Cleveland Fed): median CPI "
                     f"{med['ann_pct']:.1f}% annualised for {m}"
                     + (f" ({med['avg_3m_ann_pct']:.1f}% over three months)"
                        if med.get("avg_3m_ann_pct") is not None else "")
                     + f"; the 16% trimmed mean {tm['ann_pct']:.1f}%"
                     + (f" ({tm['avg_3m_ann_pct']:.1f}%)"
                        if tm.get("avg_3m_ann_pct") is not None else "") + ".")
    else:
        lines.append("The Cleveland Fed median and trimmed mean: "
                     + (med.get("reason") or tm.get("reason") or "not stored") + ".")
    dif = dc["diffusion"]
    if dif.get("share_pct") is not None:
        lines.append(f"Breadth: {dif['hot']} of {dif['n']} categories "
                     f"({dif['share_pct']:.0f}%) rose faster than "
                     f"{dif['threshold_pct']:.0f}% annualised on the month (unweighted).")
    else:
        lines.append(f"Breadth: {dif.get('reason')}.")
    pt = releases.pass_through(st, cutoff, cfg)
    lines.append(pass_through_line(pt))
    i32 = releases.item32_read(st, cutoff)
    state = releases.item32_state(i32.get("supply_shock"), pt, cfg)
    if state:
        lines.append(f"Item 32's read: {state} (the supply-shock signature is on; the "
                     f"pass-through flag {'has' if pt.get('flag') else 'has not'} fired).")
    elif i32["state"] == "absent":
        lines.append(f"Item 32's printed state: {i32['reason']}.")
    return {"title": TITLE_DECOMP, "paragraph_wanted": False,
            "table": {"columns": ["Piece", "Weight", "Month on month, %",
                                  "Contribution, pp"], "rows": rows},
            "table_note": f"{m}. Contribution = basket weight (BLS relative importance, "
                          f"December 2025) x the piece's own month-on-month change. Core "
                          f"services ex shelter is built from core services less shelter "
                          f"at their weights.",
            "lines": lines, "data": {"decomposition": dc, "pass_through": pt,
                                     "item32": {"read": i32, "state": state}}}


def pass_through_line(pt: dict) -> str:
    from altdata import releases                                 # noqa: PLC0415
    if pt.get("state") != "read":
        return f"The pass-through basket: {pt.get('reason')}."
    head = (f"The pass-through basket (airline fares, transportation services, the "
            f"truck-freight PPI): {_pp(pt['basket_3m_ann_pct'], 1)}% annualised over "
            f"three months to {releases.month_name(pt['month'])}")
    if pt.get("flag") is True:
        f = pt["fired"]
        return (f"{head}. FLAG: it accelerated {_pp(f['acceleration_pp'], 1)} points "
                f"by {releases.month_name(f['month'])} after the "
                f"{releases.month_name(f['spike'])} energy spike (threshold "
                f"{pt['acceleration_threshold_pp']:.1f}).")
    if pt.get("flag") is None:
        return f"{head}. The flag is withheld: {pt['withheld']}."
    return f"{head}. No flag: {pt.get('reason')}."


def cpi_lenses_panel(st, cutoff: str) -> Optional[dict]:
    """Item 48 lenses 7-11, as lines and the ladder's table."""
    from altdata import releases                                 # noqa: PLC0415
    c = releases.cpi_lenses(st, cutoff)
    lines = []
    sl = c["shelter_lead"]
    got = [x for x in sl["leads"] if x.get("month")]
    if got:
        lead_txt = "; ".join(
            f"{x['name']} {_pp(x['yoy_pct'], 1)}% on the year to "
            f"{releases.month_name(x['month'])} ({_pp(x['yoy_lag_ago_pct'], 1)}% "
            f"{sl['lag_months']} months earlier)" for x in got)
        cpi_txt = ", ".join(f"{SHELTER_NAMES.get(k['key'], k['key'])} "
                            f"{_pp(k['yoy_pct'], 1)}%" for k in sl["cpi"])
        lines.append(f"Shelter's lead (new leases reach CPI about {sl['lag_months']} "
                     f"months later): {lead_txt}. CPI on the year: {cpi_txt}.")
    else:
        lines.append("Shelter's lead: "
                     + "; ".join(x.get("reason") or "" for x in sl["leads"]) + ".")
    lines.append(f"Not read: {sl['gap']}.")
    sc = c.get("supercore")
    if sc:
        lines.append(f"Supercore (core services ex shelter): {_pp(sc['ann_3m_pct'], 1)}% "
                     f"annualised over three months, {_pp(sc['ann_6m_pct'], 1)}% over six, "
                     f"{_pp(sc['yoy_pct'], 1)}% on the year "
                     f"({releases.month_name(sc['month'])}).")
    if c.get("sticky") and c.get("flexible"):
        lines.append(f"Sticky-price CPI (Atlanta Fed) {c['sticky']['ann_pct']:.1f}% "
                     f"annualised, flexible {c['flexible']['ann_pct']:.1f}% "
                     f"({releases.month_name(c['sticky']['month'])}).")
    if c.get("goods") and c.get("services"):
        g, s_ = c["goods"], c["services"]
        lines.append(f"Goods {_pp(g['yoy_pct'], 1)}% on the year "
                     f"({_pp(g['ann_3m_pct'], 1)}% annualised over three months); services "
                     f"{_pp(s_['yoy_pct'], 1)}% ({_pp(s_['ann_3m_pct'], 1)}%).")
    w = c["wedge"]
    if w.get("gap_pp") is not None:
        names = "; ".join(f"{x['component']}: CPI {x['cpi']}, PCE {x['pce']}"
                          for x in w["weights"])
        lines.append(f"The CPI-PCE wedge: core CPI less core PCE {_pp(w['gap_pp'])} pp "
                     f"({releases.month_name(w['month'])}). The weights that make it: "
                     f"{names}.")
    rows = []
    for key, lad in c["ladder"].items():
        name = "CPI" if key == "fred.cpi" else "Core CPI"
        for rung in lad["rungs"]:
            rows.append([name, releases.month_name(rung["month"]),
                         _pp(rung["drops_out_mm_pct"]), _pp(rung["yoy_pct"])])
    sub = {"title": TITLE_LENSES, "paragraph_wanted": False, "lines": lines,
           "data": {"cpi_lenses": c}}
    if rows:
        paces = "; ".join(f"{'CPI' if k == 'fred.cpi' else 'core'} "
                          f"{_pp(v['pace_mm_pct'])}% a month, {_pp(v['yoy_now_pct'], 2)}% "
                          f"on the year now" for k, v in c["ladder"].items())
        sub["table"] = {"columns": ["Series", "Month", "Month dropping out, %",
                                    "Year over year at the pace, %"], "rows": rows}
        sub["table_note"] = (f"The base-effect ladder: the mechanical path of year over "
                             f"year if month on month runs at its trailing three-month "
                             f"average ({paces}).")
    return sub


TITLE_PPI = "PPI: the pipeline, the PCE-relevant lines and trade margins"


def ppi_panel(st, cutoff: str) -> Optional[dict]:
    """Item 48 lenses 12-14 as one table and two lines."""
    from altdata import releases, releases_b                     # noqa: PLC0415
    pp = releases_b.ppi_lenses(st, cutoff)
    rows, missing = [], []
    groups = ([("Final demand", pp["final_demand"])]
              + [("12 pipeline", x) for x in pp["pipeline"]]
              + [("13 PCE-relevant (NSA)", x) for x in pp["pce_relevant"]]
              + [("14 margins", pp["trade_services"]), ("14 margins", pp["core_ex_trade"])])
    for lens_no, x in groups:
        if not x.get("month"):
            missing.append(f"{x['name']}: {releases_b.printable(x['reason'])}")
            continue
        three = _pp(x.get("ann_3m_pct"), 1) if x.get("sa") else "NSA"
        rows.append([lens_no, x["name"], releases.month_name(x["month"]),
                     _pp(x.get("mm_pct"), 1), three, _pp(x.get("yoy_pct"), 1)]
                    + releases_b.lens_cells(x["lens"]))
    if not rows:
        return None                     # no PPI series stored: the slot prints nothing
    lines = []
    gaps = [f"{x['name'].split(' intermediate')[0].lower()} {_pp(x['gap_to_final_pp'], 1)} pp"
            for x in pp["pipeline"] if x.get("gap_to_final_pp") is not None]
    if gaps:
        lines.append("The pipeline against final demand, on the year: "
                     + "; ".join(gaps) + ".")
    if missing:
        lines.append("Not read: " + "; ".join(missing) + ".")
    return {"title": TITLE_PPI, "paragraph_wanted": False, "lines": lines,
            "table": {"columns": ["Lens", "Series", "Month", "Month, %",
                                  "3m annualised, %", "On the year, %"]
                      + releases_b.LENS_COLUMNS, "rows": rows},
            "table_note": ("Report-only (the order's flags are lenses 2-4). Each "
                           "percentile ranks the year-on-year change against its own "
                           "history; the long window is the release family's."),
            "data": {"ppi_lenses": pp}}


def _ai_ppi_panel(st, cutoff: str) -> Optional[dict]:
    """Batch 14 item 65 (ST-R6.65b; a57): the AI-bottleneck PPI line."""
    from . import batch14_b1_block                               # noqa: PLC0415
    return batch14_b1_block.ai_ppi_panel(st, cutoff)


SHELTER_NAMES = {"fred.cpi_shelter": "shelter", "fred.cpi_rent": "rent",
                 "fred.cpi_oer": "owners' equivalent rent"}


# The panels in print order. None is a reserved slot (see the module docstring).
PANELS: list[tuple[str, Optional[Callable]]] = [
    ("lead", lead_panel),
    ("gap", gap_panel),
    ("decomposition", decomposition_panel),   # Batch 7 item 46
    ("cpi_lenses", cpi_lenses_panel),         # Batch 7 item 48, lenses 7-11
    ("ppi", ppi_panel),                       # Batch 7 Group B, lenses 12-14
    ("ai_ppi", _ai_ppi_panel),                # Batch 14 item 65, the AI bottleneck
]
# Panels the Monthly prints and the Weekly does not (ruling 5 of 18 Oct 2026: the
# PPI panel is Monthly-only; the close keeps its release-day read line). Item 65's
# PPI line is monthly as ruled.
MONTHLY_ONLY = frozenset({"ppi", "ai_ppi"})


def subsections(st, cutoff: str, cadence: str = "monthly") -> list[dict]:
    out = []
    for name, build in PANELS:
        if build is None or (name in MONTHLY_ONLY and cadence != "monthly"):
            continue
        try:
            sub = build(st, cutoff)
        except Exception:                                        # noqa: BLE001
            log.warning("inflation panel %s faulted", name, exc_info=True)
            continue
        if sub:
            out.append(sub)
    return out
