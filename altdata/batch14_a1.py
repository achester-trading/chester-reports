"""
Signal triage Batch 14, Part A1 (session A, a56; the order is
docs/change-order-signal-triage-batch-14-2026-10-20.md, ruled 20 Oct 2026 with
filing amendments F1 to F8): items 64, 69 and 70, the 1 Nov Monthly candidates.

Every figure here is read at report time from series already stored, as of the
cutoff, and printed with DUAL PERCENTILES: the latest value's percentile over five
years and over its full stored history, each with its window and n
(st_r5_rates.lens, the metric-lens rule). Nothing is written to the store, nothing
enters a composite or the market-state object, and nothing is entered by hand.

  ITEM 64 (F3): THE EXCESS CAPE YIELD. The cyclically adjusted earnings yield,
      100 / Shiller's CAPE, less the real 10-year (FRED DFII10, fred.tips_10y) as
      the month's mean of daily closes, monthly from 2003 when DFII10 begins.
      Labelled as such: Shiller's own excess CAPE yield takes its real rate from
      the nominal 10-year less trailing inflation, so the two are not the same
      number. The forward-earnings-yield version is a listed gap (no keyless
      forward earnings yield; F3).
  ITEM 69 (F3, F6): THE HOUSING FOOTPRINT.
      * Freddie Mac's PMMS 30-year rate (fred.mortgage_30y, weekly) less the
        10-year (fred.yield_10y) on the same day, bp.
      * The current-coupon MBS yield less the 10-year: NOT TRACKED -- no keyless
        current-coupon series (Part 0, check 7).
      * GSE retained portfolios: NOT TRACKED -- the GSEs' monthly summaries are
        not keyless and simple (Part 0).
      * The real home price level (Shiller, shiller.real_home_price, 1890 = 100)
        as a percentile of its history from 1890, one point a year (the annual
        rows to 1952, each later year's mean of its months) with the latest
        month ranked against them, so the monthly era does not outweigh
        1890-1952 twelve to one.
  ITEM 70: THE NOMINAL-GROWTH ANCHOR. The 10-year (the quarter's mean of daily
      closes) less the 10-year and the 5-year CAGR of nominal GDP (BEA via FRED,
      fred.gdp_nominal), quarterly, bp: the US macro r-g. Printed beside the
      twin-deficit fit (SR-43, altdata/rates_anchors.py) as a fair-value range.
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any, Optional

from . import st_r5_rates as rt

log = logging.getLogger(__name__)

KEYS = {"cape": "shiller.cape", "tips": "fred.tips_10y", "ten": "fred.yield_10y",
        "pmms": "fred.mortgage_30y", "gdp": "fred.gdp_nominal",
        "home": "shiller.real_home_price"}
YEARS = 5                       # the short window of the dual percentiles
LABEL_ECY = ("Excess CAPE yield (100 / CAPE less the real 10-year, DFII10; not "
             "Shiller's own real rate)")
NOT_TRACKED = {
    "forward_ecy": ("the real 10-year against the S&P forward earnings yield: no "
                    "keyless source serves the forward earnings yield (F3)"),
    "mbs": ("the current-coupon MBS yield less the 10-year: no keyless current-"
            "coupon MBS series (FRED carries none; an ETF's published yield is a "
            "vendor value)"),
    "gse": ("GSE retained-portfolio holdings: the GSEs' monthly summaries are not "
            "keyless and simple (Freddie Mac's are font-encoded PDFs needing a parser "
            "the project does not carry; Fannie Mae's site refuses automated reads)"),
    "scorecard": ("the US macro r-g as a column in item 21's sovereign scorecard: the "
                  "scorecard is not built (ST-R4.21's gaps); the r-g prints in the "
                  "10-year's nominal-growth anchor instead"),
}


def _monthly_mean(pts: list[tuple[str, float]]) -> dict[str, float]:
    by: dict[str, list[float]] = {}
    for d, v in pts:
        by.setdefault(d[:7], []).append(v)
    return {m: sum(v) / len(v) for m, v in by.items()}


def _quarter(d: str) -> str:
    y, m = int(d[:4]), int(d[5:7])
    return f"{y:04d}-{(m - 1) // 3 * 3 + 1:02d}"


def _quarterly_mean(pts: list[tuple[str, float]]) -> dict[str, float]:
    by: dict[str, list[float]] = {}
    for d, v in pts:
        by.setdefault(_quarter(d), []).append(v)
    return {q: sum(v) / len(v) for q, v in by.items()}


def lens_cell(lz: dict) -> str:
    return rt.lens_text(lz)


# ---------------------------------------------------------------------------
# Item 64
# ---------------------------------------------------------------------------
def excess_cape_yield(st, cutoff: str) -> dict:
    cape = rt._pts(st, KEYS["cape"], cutoff)                    # noqa: SLF001
    tips = _monthly_mean(rt._pts(st, KEYS["tips"], cutoff))     # noqa: SLF001
    series = [(d, round(100.0 / v - tips[d[:7]], 4)) for d, v in cape
              if v and d[:7] in tips]
    if not series:
        why = ("Shiller's CAPE is not stored" if not cape else
               "no month holds both CAPE and DFII10")
        return {"label": LABEL_ECY, "absent": True, "reason": why}
    d, v = series[-1]
    cv = dict(cape)[d]
    return {"label": LABEL_ECY, "absent": False, "month": d[:7], "value_pp": v,
            "cape": cv, "cape_ey_pct": round(100.0 / cv, 4),
            "real_10y_pct": round(tips[d[:7]], 4), "lens": rt.lens(series, YEARS),
            "series_n": len(series)}


def ecy_line(e: dict) -> str:
    if e.get("absent"):
        return f"{e['label']}: not read -- {e['reason']}."
    return (f"{e['label']}: {e['value_pp']:+.2f} pp in {e['month']} (earnings yield "
            f"{e['cape_ey_pct']:.2f}% at CAPE {e['cape']:.1f}, real 10-year "
            f"{e['real_10y_pct']:.2f}% the month's mean); {lens_cell(e['lens'])}.")


# ---------------------------------------------------------------------------
# Item 69
# ---------------------------------------------------------------------------
def mortgage_spread(st, cutoff: str) -> dict:
    pm = rt._pts(st, KEYS["pmms"], cutoff)                      # noqa: SLF001
    ten = rt._pts(st, KEYS["ten"], cutoff)                      # noqa: SLF001
    series = rt.spread_bp(pm, ten)
    if not series:
        return {"absent": True, "reason": ("the PMMS rate is not stored" if not pm else
                                           "no PMMS week shares a day with the 10-year")}
    d, v = series[-1]
    return {"absent": False, "as_of": d, "spread_bp": v, "pmms_pct": dict(pm)[d],
            "ten_pct": dict(ten)[d], "lens": rt.lens(series, YEARS)}


def real_home_price(st, cutoff: str) -> dict:
    pts = rt._pts(st, KEYS["home"], cutoff)                     # noqa: SLF001
    if not pts:
        return {"absent": True, "reason": "Shiller's real home price index is not stored"}
    last_day, last = pts[-1]
    by: dict[int, list[float]] = {}
    for d, v in pts:
        by.setdefault(int(d[:4]), []).append(v)
    yrs = sorted(by)
    annual = [sum(by[y]) / len(by[y]) for y in yrs if y < int(last_day[:4])]
    ranked = annual + [last]
    from . import derived                                       # noqa: PLC0415
    return {"absent": False, "month": last_day[:7], "level": last,
            "percentile": derived.percentile_of(ranked, last), "n_years": len(ranked),
            "from": yrs[0], "max_year": yrs[annual.index(max(annual))] if annual else None,
            "max_annual": max(annual) if annual else None}


def footprint(st, cutoff: str) -> dict:
    return {"mortgage_spread": mortgage_spread(st, cutoff),
            "not_tracked": [NOT_TRACKED["mbs"], NOT_TRACKED["gse"]]}


def footprint_lines(f: dict) -> list[str]:
    m = f["mortgage_spread"]
    if m.get("absent"):
        out = [f"The mortgage spread over the 10-year: not read -- {m['reason']}."]
    else:
        out = [f"The mortgage spread over the 10-year (Freddie Mac PMMS less DGS10, "
               f"{m['as_of']}): {m['spread_bp']:.0f} bp ({m['pmms_pct']:.2f}% against "
               f"{m['ten_pct']:.2f}%); {lens_cell(m['lens'])}."]
    out.append("The current-coupon MBS spread over the 10-year: not tracked.")
    out.append("GSE retained-portfolio holdings: not tracked.")
    return out


def home_line(h: dict) -> str:
    if h.get("absent"):
        return f"Real home prices since 1890 (Shiller): not read -- {h['reason']}."
    return (f"Real home prices (Shiller's index, 1890 = 100), {h['month']}: "
            f"{h['level']:.1f}, the {rt.ordinal(h['percentile'])} percentile of its "
            f"history since {h['from']} (one point a year, n={h['n_years']}).")


# ---------------------------------------------------------------------------
# Item 70
# ---------------------------------------------------------------------------
def _cagr_series(gdp: list[tuple[str, float]], years: int) -> dict[str, float]:
    by = {_quarter(d): v for d, v in gdp}
    qs = sorted(by)
    out = {}
    for i, q in enumerate(qs):
        j = i - 4 * years
        if j >= 0 and qs[j] == _shift_q(q, -4 * years) and by[qs[j]] > 0:
            out[q] = ((by[q] / by[qs[j]]) ** (1.0 / years) - 1.0) * 100.0
    return out


def _shift_q(q: str, n: int) -> str:
    y, m = int(q[:4]), int(q[5:7])
    k = y * 4 + (m - 1) // 3 + n
    return f"{k // 4:04d}-{k % 4 * 3 + 1:02d}"


def nominal_growth_anchor(st, cutoff: str) -> dict:
    gdp = rt._pts(st, KEYS["gdp"], cutoff)                      # noqa: SLF001
    ten_pts = rt._pts(st, KEYS["ten"], cutoff)                  # noqa: SLF001
    if not gdp or not ten_pts:
        return {"absent": True, "reason": ("nominal GDP is not stored" if not gdp else
                                           "the 10-year is not stored")}
    ten_q = _quarterly_mean(ten_pts)
    out: dict[str, Any] = {"absent": False, "ten_now_pct": ten_pts[-1][1],
                           "ten_now_day": ten_pts[-1][0], "legs": {}}
    for yrs in (10, 5):
        cg = _cagr_series(gdp, yrs)
        series = [(q + "-01", round((ten_q[q] - c) * 100.0, 1))
                  for q, c in sorted(cg.items()) if q in ten_q]
        if not series:
            out["legs"][yrs] = {"absent": True, "reason": f"no quarter holds a {yrs}-year CAGR"}
            continue
        q, gap = series[-1]
        out["legs"][yrs] = {"absent": False, "quarter": q[:7], "cagr_pct": round(cg[q[:7]], 3),
                            "ten_q_pct": round(ten_q[q[:7]], 3), "gap_bp": gap,
                            "lens": rt.lens(series, YEARS)}
    return out


def fair_value_range(anchor: dict, fiscal: Optional[dict]) -> Optional[dict]:
    pts = []
    for yrs in (10, 5):
        leg = (anchor.get("legs") or {}).get(yrs) or {}
        if not leg.get("absent") and leg.get("cagr_pct") is not None:
            pts.append((f"nominal growth, {yrs}-year CAGR", leg["cagr_pct"]))
    if fiscal and fiscal.get("state") == "ok" and fiscal.get("us_fitted_pct") is not None:
        pts.append(("twin-deficit fit", float(fiscal["us_fitted_pct"])))
    if not pts:
        return None
    lo, hi = min(p[1] for p in pts), max(p[1] for p in pts)
    return {"low_pct": lo, "high_pct": hi, "anchors": pts}


def anchor_lines(a: dict, fiscal: Optional[dict]) -> list[str]:
    if a.get("absent"):
        return [f"The nominal-growth anchor: not read -- {a['reason']}."]
    out = []
    for yrs in (10, 5):
        leg = a["legs"][yrs]
        if leg.get("absent"):
            out.append(f"The 10-year less the {yrs}-year nominal GDP CAGR: not read -- "
                       f"{leg['reason']}.")
            continue
        out.append(f"The 10-year less the {yrs}-year nominal GDP CAGR (the US macro r-g, "
                   f"{leg['quarter']}): {leg['gap_bp']:+.0f} bp (the quarter's 10-year "
                   f"{leg['ten_q_pct']:.2f}% against growth of {leg['cagr_pct']:.2f}% a "
                   f"year); {lens_cell(leg['lens'])}.")
    fv = fair_value_range(a, fiscal)
    if fv:
        names = "; ".join(f"{n} {v:.2f}%" for n, v in fv["anchors"])
        out.append(f"Fair-value range for the 10-year: {fv['low_pct']:.2f}% to "
                   f"{fv['high_pct']:.2f}% ({names}), against {a['ten_now_pct']:.2f}% "
                   f"on {a['ten_now_day']}." + ("" if any(n == "twin-deficit fit"
                                                        for n, _ in fv["anchors"])
                                               else " The twin-deficit fit is absent."))
    return out


def fiscal_anchor(st, cutoff: str) -> Optional[dict]:
    try:
        from . import rates_anchors                             # noqa: PLC0415
        return rates_anchors.fiscal_anchor(st, cutoff, rates_anchors.load_config())
    except Exception:                                           # noqa: BLE001
        log.warning("batch 14: the twin-deficit fit faulted", exc_info=True)
        return None


def build(st, cutoff: str) -> dict:
    """Everything Part A1 prints, as of the cutoff."""
    anchor = nominal_growth_anchor(st, cutoff)
    fis = fiscal_anchor(st, cutoff)
    return {"ecy": excess_cape_yield(st, cutoff), "footprint": footprint(st, cutoff),
            "home": real_home_price(st, cutoff), "anchor": anchor, "fiscal": fis,
            "not_tracked": dict(NOT_TRACKED)}
