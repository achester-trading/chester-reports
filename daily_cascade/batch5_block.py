"""
Batch 5 Tranche 1, part 1: the print. (altdata/batch5.py computes; this prints.)

    plumbing_subsections(st, now, then, cadence)  Plumbing & rates: the 10-year
                        attribution's extensions (the term premium with its dual
                        percentiles, the fiscal-bark flag) and net liquidity
                        attributed. Greece-Bund rides batch 3's EU table.
    mechanics_subsection(st, now)  Mechanics: the stock-bond correlation, SR-9
                        amended, with its conditioned flag and its companions.
    slow_subsection(st, now)       The Monthly's slow layers, under Factor I:
                        construction spending, real.

Tables and code-written lines only: no paragraph of their own, nothing a model
writes. Every flag says it is a flag and what its threshold is; nothing here is
a state, a modifier or a rule. A read that faults is left out and logged, never
allowed to take the section down.
"""

from __future__ import annotations

import logging
from typing import Optional

from altdata import batch5

log = logging.getLogger(__name__)

TITLE_ATTR = "The 10-year attribution: the term premium and the fiscal-bark flag"
TITLE_NL = "Net liquidity: Fed assets less the TGA less the reverse repo, attributed"
TITLE_SB = "The stock-bond correlation (SR-9, amended): 60 days beside two years"
TITLE_CON = "Factor I, the real economy: construction spending, real"


def _prose(sub: Optional[dict], now: str) -> Optional[dict]:
    """No ISO date outside a table (validate_readability): every line and note a
    sub-section prints carries its dates as "28 Sep"."""
    if not sub:
        return sub
    from .es_read import prose_dates                            # noqa: PLC0415
    year = int(now[:4])
    sub["lines"] = [prose_dates(x, year) for x in sub.get("lines") or []]
    if sub.get("table_note"):
        sub["table_note"] = prose_dates(sub["table_note"], year)
    return sub


def _ord(p: Optional[float]) -> str:
    if p is None:
        return "—"
    n = int(round(p))
    suf = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def _bp(v: Optional[float]) -> str:
    return "—" if v is None else f"{v:+.0f} bp"


def _pct_cell(p: dict) -> str:
    if not p or p.get("pct") is None:
        return "—"
    tail = f"n={p['n']}, from {p['from']}"
    if p.get("short"):
        tail += f"; {p['window_years_real']} years stored"
    return f"{_ord(p['pct'])} ({tail})"


def _usd_bn(v: Optional[float]) -> str:
    return "—" if v is None else f"{v / 1e9:+,.0f}bn"


# ---------------------------------------------------------------------------
def attribution_subsection(st, now: str, cfg: Optional[dict] = None) -> dict:
    return _prose(_attribution(st, now, cfg), now)


def _attribution(st, now: str, cfg: Optional[dict] = None) -> dict:
    """ST-R4.21b and ST-R4.26a, where the attribution prints."""
    cfg = cfg or batch5.config()
    tp = batch5.term_premium(st, now, cfg)
    fb = batch5.fiscal_bark(st, now, cfg)
    rows, lines = [], []
    years = [int(y) for y in (cfg.get("term_premium") or {}).get("windows_years") or (5, 20)]
    if tp.get("absent"):
        lines.append(f"{tp.get('label')}: {tp['reason']}.")
    else:
        rows.append([tp["label"], f"{tp['level']:.2f}%", _bp(tp["change_bp"])]
                    + [_pct_cell(tp["percentiles"].get(y)) for y in years]
                    + [tp["as_of"]])
    if fb.get("absent"):
        lines.append(f"Fiscal-bark flag not assessable: {fb['reason']}.")
    else:
        rows.append([f"ACM fitted 10-year, {fb['months']} months",
                     f"{fb['fitted_bp']:+.0f} bp",
                     f"term premium {fb['tp_bp']:+.0f} bp; expected short rate "
                     f"{fb['path_bp']:+.0f} bp"]
                    + ["share " + (f"{fb['tp_share']:.2f}" if fb["tp_share"] is not None
                                   else "—")] + ["—"] * (len(years) - 1)
                    + [f"{fb['from']} to {fb['to']}"])
        if fb["fiscal_bark"]:
            lines.append(f"FISCAL-BARK FLAG: the term premium carried {fb['tp_share']:.2f} "
                         f"of the {fb['months']}-month {fb['fitted_bp']:+.0f} bp rise in "
                         f"ACM's fitted 10-year (flag at a rise of at least "
                         f"{fb['move_min_bp']:.0f} bp with a share of at least "
                         f"{fb['share_min']:.2f}). A flag, not a state.")
        else:
            why = fb.get("share_reason") or (
                f"the term premium carried {fb['tp_share']:.2f} of a "
                f"{fb['fitted_bp']:+.0f} bp move")
            lines.append(f"Fiscal-bark flag not raised: {why}.")
        if fb["divergence"]:
            lines.append(f"DIVERGENCE: the term premium rose {fb['tp_bp']:+.0f} bp while "
                         f"the expected short rate fell {fb['path_bp']:+.0f} bp over "
                         f"{fb['months']} months (each past {fb['divergence_bp']:.0f} bp).")
        if fb.get("quoted_bp") is not None:
            lines.append(f"The quoted 10-year (FRED DGS10) moved {fb['quoted_bp']:+.0f} bp "
                         f"over the same months; the split is ACM's of its own fitted "
                         f"yield.")
    return {"title": TITLE_ATTR,
            "table": {"columns": ["Series", "Level or move", "Change or legs"]
                      + [f"{y}-year percentile" for y in years] + ["As of"],
                      "rows": rows} if rows else None,
            "lines": lines, "paragraph_wanted": False,
            "table_note": ("The term premium's percentiles rank the latest print "
                           "against the store's own history in each window, with its "
                           "n and first date; a window the store does not fill says "
                           "how many years it holds. The fiscal-bark flag (Batch 5 "
                           "item 26) is ACM's split of its own fitted 10-year: "
                           "descriptive, unvalidated."),
            "data": {"term_premium": tp, "fiscal_bark": fb}}


def net_liquidity_subsection(st, now: str, cfg: Optional[dict] = None) -> dict:
    return _prose(_net_liquidity(st, now, cfg), now)


def _net_liquidity(st, now: str, cfg: Optional[dict] = None) -> dict:
    """ST-R4.17a. Report only: the modifier waits for the 17b ledger."""
    nl = batch5.net_liquidity(st, now, cfg)
    if nl.get("absent"):
        return {"title": TITLE_NL, "lines": [f"Net liquidity: {nl['reason']}."],
                "paragraph_wanted": False, "data": {"net_liquidity": nl}}
    rows, lines = [], []
    for w, x in nl["windows"].items():
        if x.get("absent"):
            lines.append(f"{w} weeks: {x['absent']}.")
            continue
        c = x["contributions"]
        rows.append([f"{w} weeks", _usd_bn(x["change"]), _usd_bn(c.get("fed_assets")),
                     _usd_bn(c.get("tga")), _usd_bn(c.get("rrp")),
                     f"{x['from']} to {x['to']}"])
        if x.get("led_by"):
            lines.append(f"Over {w} weeks, {_usd_bn(x['change'])}, led by "
                         f"{x['meaning']}.")
    return {"title": TITLE_NL,
            "table": {"columns": ["Window", "Net liquidity", "Fed assets", "Less the TGA",
                                  "Less the RRP", "From and to"], "rows": rows},
            "lines": [f"Net liquidity ${nl['level'] / 1e12:,.2f}tn as of {nl['as_of']}."]
            + lines + ["Report only: the modifier waits for its calibration ledger "
                       "(ST-R4.17b)."],
            "paragraph_wanted": False,
            "table_note": ("Each leg's contribution in dollars: a TGA or RRP that FELL "
                           "adds to net liquidity. The legs sum to the change."),
            "data": {"net_liquidity": nl}}


def plumbing_subsections(st, now: str, then: str, cadence: str = "weekly",
                         cfg: Optional[dict] = None) -> list[dict]:
    cfg = cfg or batch5.config()
    out = []
    for fn in (lambda: attribution_subsection(st, now, cfg),
               lambda: net_liquidity_subsection(st, now, cfg)):
        try:
            out.append(fn())
        except Exception:                                       # noqa: BLE001
            log.warning("batch 5 plumbing block faulted", exc_info=True)
    return out


def mechanics_subsection(st, now: str, cfg: Optional[dict] = None) -> Optional[dict]:
    return _prose(_mechanics(st, now, cfg), now)


def _mechanics(st, now: str, cfg: Optional[dict] = None) -> Optional[dict]:
    """ST-R4.24a/b, in Mechanics, with its two companions named."""
    try:
        sb = batch5.stock_bond(st, now, cfg)
    except Exception:                                           # noqa: BLE001
        log.warning("batch 5 stock-bond block faulted", exc_info=True)
        return None
    if sb.get("absent"):
        return {"title": TITLE_SB, "lines": [f"Stock-bond correlation: {sb['reason']}."],
                "paragraph_wanted": False, "data": {"stock_bond": sb}}
    two = sb["two_year"]
    rows = [["SPY-TLT, 60 days (daily)", f"{sb['corr_60d']:+.2f}", sb["corr_60d_as_of"]],
            ["SPY-TLT, two years (weekly)",
             "—" if two.get("absent") else f"{two['value']:+.2f} (n={two['n_weeks']} weeks)",
             two.get("to") or "—"]]
    lines = []
    if two.get("absent"):
        lines.append(f"Two-year window absent: {two['absent']}.")
    if sb["live"]:
        lines.append(f"STOCK-BOND FLAG LIVE ({sb['strength']}): the 60-day correlation "
                     f"{sb['corr_60d']:+.2f} is above {sb['live_above']:+.2f}, so "
                     f"Treasury duration is not hedging equities; {sb['why']}."
                     + (" The two-year window agrees: persistent." if sb["persistent"]
                        else ""))
    else:
        lines.append(f"Stock-bond flag not live: the 60-day correlation "
                     f"{sb['corr_60d']:+.2f} is at or below {sb['live_above']:+.2f}.")
    if sb.get("ten_year") is not None:
        lines.append(f"The 10-year at {sb['ten_year']:.2f}% ({sb['ten_year_as_of']}) is "
                     + ("above" if sb["above_prior"] else "below")
                     + f" SR-9's {sb['level_prior_pct']:.2f}% prior"
                     + (": a positive reading is treated as persistent." if sb["above_prior"]
                        else "."))
    lines.append(sb["companions"])
    return {"title": TITLE_SB,
            "table": {"columns": ["Correlation", "Reading", "As of"], "rows": rows},
            "lines": lines, "paragraph_wanted": False,
            "table_note": ("Pearson correlation of SPY and TLT log returns: positive is "
                           "stocks and Treasuries moving together. The flag's strength "
                           "reads the 10-year attribution's 60-session split: strongest "
                           "when breakeven-led, weaker when real-yield- or term-premium-"
                           "led with inflation anchored. Descriptive; no rule-table "
                           "consequence is wired."),
            "data": {"stock_bond": sb}}


def _pc(v: Optional[float]) -> str:
    return "—" if v is None else f"{v:+.1f}%"


def slow_subsection(st, now: str, cfg: Optional[dict] = None) -> Optional[dict]:
    return _prose(_slow(st, now, cfg), now)


def _slow(st, now: str, cfg: Optional[dict] = None) -> Optional[dict]:
    """ST-R4.23a, the Monthly's slow layers under Factor I. No rights until the
    Disruptive Themes refresh rules."""
    try:
        # No renderer imports a writer (validate_official_sources): the Census
        # writer is live since the D1c ruling, so there is no hold to read here.
        con = batch5.construction(st, now, cfg)
    except Exception:                                           # noqa: BLE001
        log.warning("batch 5 construction block faulted", exc_info=True)
        return None
    if con.get("absent"):
        return {"title": TITLE_CON, "lines": [f"Construction spending: {con['reason']}."],
                "paragraph_wanted": False, "data": {"construction": con}}
    b = con["base_year"]
    rows = []
    for key, label in (("data_center", "Data centers"),
                       ("ex_data_center", "Total construction ex data centers"),
                       ("power", "Power (the XII buildout)")):
        f = con.get(key)
        if not f:
            continue
        rows.append([label, f"{f['nominal'] / 1e3:,.1f}bn" if f.get("nominal") else "—",
                     _pc(f["real_yoy_pct"]), _pc(f["nominal_yoy_pct"]),
                     _pc(f["vs_base_pct"])])
    dc = con["data_center"]
    lines = []
    if dc.get("share_of_private_nonres_pct") is not None:
        lines.append(f"Data centers are {dc['share_of_private_nonres_pct']:.1f}% of private "
                     f"nonresidential construction ({con['as_of']}).")
    lines.append(f"Real is deflated by PPI final demand construction (FRED PPIDCS); the "
                 f"level against {b} is the real level against {b}'s monthly average, "
                 f"printed beside the year-over-year because a base effect (the fab "
                 f"boom rolling off) can make a year-over-year fall read as a collapse.")
    lines.append("No rights until the Disruptive Themes refresh rules on these series.")
    return {"title": TITLE_CON,
            "table": {"columns": ["Census VIP, SAAR", "Level", "Real year over year",
                                  "Nominal year over year", f"Real level against {b}"],
                      "rows": rows},
            "lines": lines, "paragraph_wanted": False,
            "data": {"construction": con}}
