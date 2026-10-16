"""
Batch 5 Tranche 1, part 2: the print. (altdata/batch5b.py computes; this prints.)

    mechanics_subsections(st, now)  Mechanics: the dispersion panel (18a) and the
                        cross-asset vol divergence flag (19a).
    read_items(st, now)             The line Mechanics' read carries when the
                        vol divergence flag is active (19a), else nothing.
    slow_subsections(st, now)       The Monthly's slow layers: the expansion's
                        age with the post-war hazard (22a) and, under Factor I,
                        BEA's information-processing contribution (22b).
    positioning_subsection(st, now) Positioning & flows, under the CFTC table and
                        SR-36's line: Treasury moves split overnight and session
                        (27a), a co-signal of the Japan slow-money set and of
                        SR-36's unwind watch.

Tables and code-written lines only: no paragraph of their own, nothing a model
writes. A flag says it is a flag and names its threshold; nothing here is a state,
a modifier or a rule. A read that faults is left out and logged, never allowed to
take the section down.
"""

from __future__ import annotations

import logging
from typing import Optional

from altdata import batch5b
from altdata.numeral_audit import ordinal

log = logging.getLogger(__name__)

TITLE_DISP = "Dispersion and implied correlation: index against single names"
TITLE_VOL = "Cross-asset volatility: the MOVE against the VIX"
TITLE_EXP = "The expansion's age: a base rate, not a timing tool"
TITLE_F1 = "Factor I, the dependency: information processing in real GDP growth"
TITLE_ON = "Treasury moves by session: overnight against the US session"
TAG = "(descriptive; unvalidated)"


def _prose(sub: Optional[dict], now: str) -> Optional[dict]:
    """No ISO date outside a table (validate_readability)."""
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
    return ordinal(p)


def _pct_cell(p: dict) -> str:
    if not p or p.get("pct") is None:
        return "—"
    tail = f"n={p['n']}, from {p['from']}"
    if p.get("short"):
        tail += f"; {p['window_years_real']} years stored"
    return f"{_ord(p['pct'])} ({tail})"


def _safe(fn, what: str):
    try:
        return fn()
    except Exception:                                           # noqa: BLE001
        log.warning("batch 5 part 2: %s faulted", what, exc_info=True)
        return None


# ---------------------------------------------------------------------------
# ST-R4.18a -- the dispersion panel
# ---------------------------------------------------------------------------
LABELS = {"dspx": "S&P 500 Dispersion Index (Cboe DSPX)",
          "cor1m": "Implied correlation, 1 month (Cboe COR1M)",
          "cor3m": "Implied correlation, 3 months (Cboe COR3M)"}


def dispersion_subsection(st, now: str, cfg: Optional[dict] = None) -> dict:
    d = batch5b.dispersion(st, now, cfg)
    rows, gaps = [], []
    for k, label in LABELS.items():
        r = d["rows"][k]
        if r.get("absent"):
            gaps.append(label)
            continue
        p = r["percentiles"]
        ys = sorted(p)
        rows.append([label, f"{r['level']:.2f}", _pct_cell(p[ys[0]]), _pct_cell(p[ys[-1]]),
                     r["as_of"]])
    rz = d["realized"]
    rows.append(["Realized cross-sectional dispersion, S&P 500 names, 21 sessions",
                 "awaiting constituent prices" if rz.get("absent") else
                 f"{rz['value']:.2f}% a day", "—", "—",
                 "—" if rz.get("absent") else rz["to"]])
    fa = d["flashalpha"]
    if fa["implied"] or fa["realized"]:
        rows.append(["FlashAlpha implied / realized correlation (by hand, Wednesday)",
                     " / ".join("—" if x is None else f"{x[1]:.2f}"
                                for x in (fa["implied"], fa["realized"])), "—", "—",
                     max(x[0] for x in (fa["implied"], fa["realized"]) if x)])
    t, f = d["thresholds"], d["flag"]
    lines = []
    if f.get("state") in ("high", "low"):
        lines.append(f"DISPERSION REGIME: {f['state'].upper()} -- DSPX at the "
                     f"{_ord(f['pct'])} percentile (n={f['n']}); the flag is high at or "
                     f"above the {ordinal(t['high_pct'])} and low at or below the "
                     f"{ordinal(t['low_pct'])}. A flag only {TAG}.")
    elif f.get("state") == "none":
        lines.append(f"Dispersion regime: no flag -- DSPX at the {_ord(f['pct'])} "
                     f"percentile (n={f['n']}), between the {ordinal(t['low_pct'])} and the "
                     f"{ordinal(t['high_pct'])}.")
    else:
        lines.append(f"Dispersion regime flag {f['why']}.")
    if d["single_name_edge"]:
        lines.append("High dispersion with low implied correlation: the setting in which "
                     "single names and long-short carry the edge over index expression, "
                     f"and index volatility looks cheap against its constituents {TAG}.")
    if gaps:
        lines.append("Not stored: " + "; ".join(gaps) + ". Yahoo serves the two "
                     "implied-correlation indices as a daily quote without history, so "
                     "their history starts at the first pull.")
    if rz.get("absent"):
        lines.append(f"Realized dispersion: {rz['reason']}.")
    return {"title": TITLE_DISP,
            "table": {"columns": ["Series", "Level", "Percentile, 1 year",
                                  "Percentile, 5 years", "As of"], "rows": rows},
            "lines": lines, "paragraph_wanted": False,
            "table_note": ("Each percentile prints its n and the first date of the "
                           "window; a window the history does not fill says how many "
                           "years it holds. DSPX's history on Yahoo starts 22 May 2024."),
            "data": {"dispersion": d}}


# ---------------------------------------------------------------------------
# ST-R4.19a -- the cross-asset vol divergence flag
# ---------------------------------------------------------------------------
def _vol_line(v: dict) -> str:
    t = v["thresholds"]
    cond = v["conditioner"]
    if v["tier"]:
        return (f"CROSS-ASSET VOL DIVERGENCE, {v['tier'].upper()} TIER: the MOVE's z is "
                f"{v['move']['z']:+.2f} and the VIX's {v['vix']['z']:+.2f} on one year "
                f"(watch: the MOVE above {t['watch_move_z']:+.1f} with the VIX below "
                f"{t['vix_z_below']:+.1f}; strong: the MOVE above "
                f"{t['strong_move_z']:+.1f}). Rates volatility is rising while equity "
                f"volatility stays quiet, a top-side tell; {cond['why']} {TAG}.")
    return (f"Cross-asset vol divergence: no tier -- the MOVE's z {v['move']['z']:+.2f}, "
            f"the VIX's {v['vix']['z']:+.2f} (watch needs the MOVE above "
            f"{t['watch_move_z']:+.1f} with the VIX below {t['vix_z_below']:+.1f}); "
            f"{cond['why']}.")


def vol_subsection(st, now: str, cfg: Optional[dict] = None) -> dict:
    v = batch5b.vol_divergence(st, now, cfg)
    if v.get("absent"):
        return {"title": TITLE_VOL, "lines": [f"Cross-asset vol divergence: "
                                              f"{v['reason']}."],
                "paragraph_wanted": False, "data": {"vol_divergence": v}}
    rows = [[name, f"{v[k]['level']:.2f}", f"{v[k]['z']:+.2f}", _ord(v[k]["pct"]),
             v["as_of"]] for k, name in (("move", "The MOVE (Treasury implied vol)"),
                                         ("vix", "The VIX (S&P 500 implied vol)"))]
    rows.append(["The MOVE's z less the VIX's", f"{v['spread_z']:+.2f}", "—", "—",
                 v["as_of"]])
    return {"title": TITLE_VOL,
            "table": {"columns": ["Series", "Level", "z, one year",
                                  "Percentile, one year", "As of"], "rows": rows},
            "lines": [_vol_line(v)], "paragraph_wanted": False,
            "table_note": (f"z and percentile rank over the trailing {v['n']} sessions "
                           f"from {v['from']}; the percentile is printed beside z because "
                           f"the VIX is right-skewed. The tiers are the order's; the "
                           f"calibration ledger (ST-R4.19b) is not yet written, so the "
                           f"flag has no overlay rights."),
            "data": {"vol_divergence": v}}


def mechanics_subsections(st, now: str, cfg: Optional[dict] = None) -> list[dict]:
    cfg = cfg or batch5b.config()
    out = []
    for fn, what in ((lambda: dispersion_subsection(st, now, cfg), "dispersion"),
                     (lambda: vol_subsection(st, now, cfg), "vol divergence")):
        sub = _safe(fn, what)
        if sub:
            out.append(_prose(sub, now))
    return out


def read_items(st, now: str, cfg: Optional[dict] = None) -> list[tuple[str, str, tuple]]:
    """(id, text, value) for Mechanics' read: one line when the vol divergence
    flag is active, else none."""
    v = _safe(lambda: batch5b.vol_divergence(st, now, cfg), "vol divergence read")
    if not v or v.get("absent") or not v.get("tier"):
        return []
    from .es_read import prose_dates                            # noqa: PLC0415
    return [("mech:vol_divergence", prose_dates(_vol_line(v), int(now[:4])),
             (v["tier"], v["move"]["z"], v["vix"]["z"]))]


# ---------------------------------------------------------------------------
# ST-R4.22a / 22b -- the slow layers and Factor I
# ---------------------------------------------------------------------------
_MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August",
           "September", "October", "November", "December")


def _ym(ym: str) -> str:
    return f"{_MONTHS[int(ym[5:7]) - 1]} {ym[:4]}"


def expansion_subsection(now: str, cfg: Optional[dict] = None) -> dict:
    e = batch5b.expansion_age(now, cfg)
    if e.get("absent"):
        return {"title": TITLE_EXP, "lines": [f"Expansion age: {e['reason']}."],
                "paragraph_wanted": False, "data": {"expansion_age": e}}
    h = e["hazard"]
    base = (f"of the {e['n']} post-war expansions, {h['of']} lasted {e['age_months']} "
            f"months or more, and {h['ended']} of those {h['of']} ended within the next "
            f"12 months" if h["of"] else
            f"no post-war expansion lasted {e['age_months']} months, so there is no "
            f"base rate past the longest ({e['longest']} months)")
    line = (f"The expansion from the {_ym(e['trough'])} trough is {e['age_months']} months "
            f"old (NBER dates; no peak announced): {base}. Post-war mean "
            f"{e['mean']:.0f} months, median {e['median']:.0f}"
            + (f"; against the {e['modern']['n']} expansions since 1982 (mean "
               f"{e['modern']['mean']:.0f} months) its age is "
               + ("ordinary." if e["age_months"] <= e["modern"]["mean"] else "long.")
               if e["modern"]["n"] else ".")
            + " Expansions end from shocks, tightening or fragilities, not from age: "
              "a base rate, not a timing tool.")
    return {"title": TITLE_EXP, "lines": [line], "paragraph_wanted": False,
            "data": {"expansion_age": e}}


def factor_i_subsection(st, now: str, cfg: Optional[dict] = None) -> dict:
    f = batch5b.factor_i(st, now, cfg)
    if f.get("absent"):
        return {"title": TITLE_F1, "lines": [f"Information-processing contribution: "
                                             f"{f['reason']}."],
                "paragraph_wanted": False, "data": {"factor_i": f}}

    def pp(v):
        return "—" if v is None else f"{v:+.2f} pp"
    rows = [[r["quarter"], pp(r["equipment"]), pp(r["software"]), pp(r["total"]),
             "—" if r["gdp_growth"] is None else f"{r['gdp_growth']:+.1f}%",
             "—" if r["share_pct"] is None else f"{r['share_pct']}%"]
            for r in f["rows"]]
    lt = f["latest"]
    line = (f"Information-processing equipment and software added {pp(lt['total'])} "
            f"to real GDP growth in {lt['quarter']}"
            + (f", against growth of {lt['gdp_growth']:+.1f}% annualized"
               if lt["gdp_growth"] is not None else "")
            + f"; over the {len(f['rows'])} quarters shown, {pp(f['avg_total'])} on "
              f"average"
            + (f" against {f['avg_gdp']:+.1f}%." if f["avg_gdp"] is not None else ".")
            + " A Factor I dependency line: what the expansion leans on, carried into the "
              "next Disruptive Themes refresh; no rights until then.")
    return {"title": TITLE_F1,
            "table": {"columns": ["Quarter", "Information-processing equipment",
                                  "Software", "Together", "Real GDP growth, annualized",
                                  "Share of growth"], "rows": rows},
            "lines": [line], "paragraph_wanted": False,
            "table_note": ("BEA's contributions to the percent change in real GDP (NIPA "
                           "table 1.1.2), percentage points at an annual rate, via FRED; "
                           "growth is real GDP's (GDPC1) annualized quarter on quarter. "
                           "The share is left blank where growth is under 0.5% either "
                           "way. A broad proxy for AI investment: the equipment line "
                           "includes all computers and the software line all software."),
            "data": {"factor_i": f}}


def slow_subsections(st, now: str, cfg: Optional[dict] = None) -> list[dict]:
    cfg = cfg or batch5b.config()
    out = []
    for fn, what in ((lambda: expansion_subsection(now, cfg), "expansion age"),
                     (lambda: factor_i_subsection(st, now, cfg), "factor I")):
        sub = _safe(fn, what)
        if sub:
            out.append(_prose(sub, now))
    return out


# ---------------------------------------------------------------------------
# ST-R4.27a -- overnight vs session
# ---------------------------------------------------------------------------
def positioning_subsection(st, now: str, cfg: Optional[dict] = None) -> Optional[dict]:
    o = _safe(lambda: batch5b.overnight(st, now, cfg), "overnight split")
    if o is None:
        return None
    rows, lines = [], []
    for r in o["rows"]:
        if r.get("absent"):
            lines.append(f"{r['label']}: {r['reason']}.")
            continue
        rows.append([r["label"], f"{r['overnight']:+.2f}%", f"{r['session']:+.2f}%",
                     f"{r['total']:+.2f}%", r["from"], r["to"]])
        if r["foreign_hours"]:
            carried = ({"overnight": "the overnight leg carried it",
                        "session": "the US session carried it"}.get(r["carried_by"])
                       or "the two legs pulled against each other")
            lines.append(f"{r['label'].split(' (')[0]} over {r['sessions']} sessions: "
                         f"{r['total']:+.2f}% (yields {r['yields']}); {carried}. A rising-"
                         f"yield move carried mostly overnight is the foreign-hours-"
                         f"selling signature.")
    co = o["cosignal"]
    lines.append("Co-signal, not a flag: in the Japan slow-money set (SR-32) and in "
                 "SR-36's unwind watch, where it counts at 2 sigma: "
                 + ("ON -- " if co.get("state") else "off -- " if co.get("state") is False
                    else "")
                 + f"{co['why']} {TAG}.")
    lines.append("The Asia-hours split waits for intraday data; the overnight leg holds "
                 "Asia and Europe together.")
    return _prose({"title": TITLE_ON,
                   "table": {"columns": ["Instrument", "Overnight", "US session",
                                         "Together", "From", "To"], "rows": rows},
                   "lines": lines, "paragraph_wanted": False,
                   "table_note": ("Overnight is the open against the prior close, the "
                                  "session the close against the open, each a log "
                                  "change summed over the sessions; the two sum to the "
                                  "move. A price falling is a yield rising. "
                                  + (o.get("zn_note") or "")),
                   "data": {"overnight": o}}, now)
