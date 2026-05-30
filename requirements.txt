"""
Derived metric computations.

These are values the Monthly Macro Report cites but that are not direct FRED
series. They're computed from underlying series the store already has.

Every function takes the Store and returns a small dict with:
- value:     the computed value (float or None if inputs missing)
- inputs:    dict naming the upstream values used (for provenance + debugging)
- as_of:     date the computation is anchored to (typically latest input date)

Errors are caught and logged, not raised, so a missing upstream doesn't break
the whole report generation.
"""

from __future__ import annotations
import logging
from typing import Optional
from datetime import date, datetime, timedelta

from altdata.store import Store

log = logging.getLogger(__name__)


def _safe_latest(store: Store, key: str) -> Optional[dict]:
    try:
        return store.latest(key)
    except Exception as e:
        log.warning("Failed reading latest %s: %s", key, e)
        return None


def _result(value, inputs, as_of) -> dict:
    return {"value": value, "inputs": inputs, "as_of": as_of}


# ---------------------------------------------------------------------------

def sahm_rule(store: Store) -> dict:
    """
    Sahm Rule: 3-month moving average of U-3 minus the trailing 12-month low.
    Trigger: >= 0.50 percentage points => recession signal.

    Returns the current Sahm value in percentage points.
    """
    rows = [r for r in store.read("u3_rate") if r["value"] is not None]
    if len(rows) < 13:
        return _result(None, {"reason": "insufficient u3_rate history"}, None)

    rows.sort(key=lambda r: r["date"])
    last_3 = rows[-3:]
    avg_3m = sum(r["value"] for r in last_3) / 3.0
    # Trailing 12-month low (months -3 through -14)
    trailing_12 = rows[-15:-3] if len(rows) >= 15 else rows[:-3]
    if not trailing_12:
        return _result(None, {"reason": "insufficient trailing window"}, None)
    low_12m = min(r["value"] for r in trailing_12)
    sahm = avg_3m - low_12m

    return _result(
        round(sahm, 3),
        {
            "u3_3mo_avg": round(avg_3m, 3),
            "u3_12mo_low": round(low_12m, 3),
            "u3_latest": last_3[-1]["value"],
        },
        last_3[-1]["date"],
    )


def m2_yoy(store: Store) -> dict:
    """M2 year-over-year growth, %."""
    rows = [r for r in store.read("m2") if r["value"] is not None]
    if len(rows) < 13:
        return _result(None, {"reason": "insufficient m2 history"}, None)
    rows.sort(key=lambda r: r["date"])
    latest = rows[-1]
    # find the observation closest to 12 months prior
    target = datetime.fromisoformat(latest["date"]).date() - timedelta(days=365)
    prior = min(rows, key=lambda r: abs((datetime.fromisoformat(r["date"]).date() - target).days))
    if not prior or prior["value"] in (None, 0):
        return _result(None, {"reason": "no comparable prior obs"}, None)
    yoy = (latest["value"] / prior["value"] - 1.0) * 100.0
    return _result(
        round(yoy, 2),
        {
            "m2_latest": latest["value"],
            "m2_latest_date": latest["date"],
            "m2_prior_yr": prior["value"],
            "m2_prior_date": prior["date"],
        },
        latest["date"],
    )


def real_wages_yoy(store: Store) -> dict:
    """
    Real wages year-over-year = AHE YoY growth minus CPI YoY growth.
    Negative value => real wages declining.
    """
    ahe_rows = [r for r in store.read("ahe_yoy") if r["value"] is not None]
    cpi_rows = [r for r in store.read("cpi") if r["value"] is not None]
    if len(ahe_rows) < 13 or len(cpi_rows) < 13:
        return _result(None, {"reason": "insufficient history"}, None)

    ahe_rows.sort(key=lambda r: r["date"])
    cpi_rows.sort(key=lambda r: r["date"])

    def _yoy(rows):
        latest = rows[-1]
        target = datetime.fromisoformat(latest["date"]).date() - timedelta(days=365)
        prior = min(rows, key=lambda r: abs((datetime.fromisoformat(r["date"]).date() - target).days))
        if not prior or prior["value"] in (None, 0):
            return None, latest["date"]
        return (latest["value"] / prior["value"] - 1.0) * 100.0, latest["date"]

    ahe_yoy, ahe_date = _yoy(ahe_rows)
    cpi_yoy, cpi_date = _yoy(cpi_rows)
    if ahe_yoy is None or cpi_yoy is None:
        return _result(None, {"reason": "yoy computation failed"}, None)

    real = ahe_yoy - cpi_yoy
    return _result(
        round(real, 2),
        {
            "ahe_yoy_pct": round(ahe_yoy, 2),
            "cpi_yoy_pct": round(cpi_yoy, 2),
            "ahe_date": ahe_date,
            "cpi_date": cpi_date,
        },
        ahe_date,
    )


def yoy_growth(store: Store, key: str) -> dict:
    """Generic YoY % growth for any series."""
    rows = [r for r in store.read(key) if r["value"] is not None]
    if len(rows) < 13:
        return _result(None, {"reason": f"insufficient {key} history"}, None)
    rows.sort(key=lambda r: r["date"])
    latest = rows[-1]
    target = datetime.fromisoformat(latest["date"]).date() - timedelta(days=365)
    prior = min(rows, key=lambda r: abs((datetime.fromisoformat(r["date"]).date() - target).days))
    if not prior or prior["value"] in (None, 0):
        return _result(None, {"reason": "no comparable prior obs"}, None)
    yoy_val = (latest["value"] / prior["value"] - 1.0) * 100.0
    return _result(
        round(yoy_val, 2),
        {"latest": latest["value"], "latest_date": latest["date"],
         "prior_yr": prior["value"], "prior_date": prior["date"]},
        latest["date"],
    )


def r_vs_g(store: Store) -> dict:
    """
    R vs G debt-cycle math:
      R (Core PCE basis) = 10Y yield - Core PCE YoY
      R (CPI basis)      = 10Y yield - CPI YoY
      G                  = Real GDP YoY (from latest GDPC1 quarter)
    Returns dict with all three plus the R>G flag.
    """
    yr10 = _safe_latest(store, "yield_10y")
    if not yr10:
        return _result(None, {"reason": "no 10Y yield"}, None)

    cpi_yoy = yoy_growth(store, "cpi")
    core_pce_yoy = yoy_growth(store, "core_pce")
    gdp_yoy = yoy_growth(store, "real_gdp")

    r_cpi = (yr10["value"] - cpi_yoy["value"]) if cpi_yoy["value"] is not None else None
    r_core_pce = (yr10["value"] - core_pce_yoy["value"]) if core_pce_yoy["value"] is not None else None
    g = gdp_yoy["value"]
    r_gt_g = None
    if r_core_pce is not None and g is not None:
        r_gt_g = r_core_pce > g

    return _result(
        {
            "yield_10y": yr10["value"],
            "r_cpi_basis": round(r_cpi, 2) if r_cpi is not None else None,
            "r_core_pce_basis": round(r_core_pce, 2) if r_core_pce is not None else None,
            "g_real_gdp_yoy": round(g, 2) if g is not None else None,
            "r_greater_than_g": r_gt_g,
        },
        {
            "yield_10y_date": yr10["date"],
            "cpi_yoy_date": cpi_yoy.get("as_of"),
            "core_pce_yoy_date": core_pce_yoy.get("as_of"),
            "gdp_yoy_date": gdp_yoy.get("as_of"),
        },
        yr10["date"],
    )


def yield_curve_2s10s(store: Store) -> dict:
    """2s10s curve spread in basis points."""
    y2 = _safe_latest(store, "yield_2y")
    y10 = _safe_latest(store, "yield_10y")
    if not y2 or not y10:
        return _result(None, {"reason": "missing yields"}, None)
    spread_bp = round((y10["value"] - y2["value"]) * 100.0, 1)
    return _result(spread_bp, {"y2": y2["value"], "y10": y10["value"]}, y10["date"])


def fed_net_liquidity(store: Store) -> dict:
    """
    Fed Net Liquidity (rough) = Fed balance sheet - RRP - TGA.
    All in same units; returns in trillions.
    """
    bs = _safe_latest(store, "fed_balance")
    rrp = _safe_latest(store, "rrp")
    tga = _safe_latest(store, "tga")
    if not bs:
        return _result(None, {"reason": "no fed balance"}, None)

    # WALCL is in millions, RRP in billions, TGA in billions — normalize to T
    bs_t = bs["value"] / 1_000_000.0  # M -> T
    rrp_t = (rrp["value"] / 1_000.0) if rrp else 0.0  # B -> T
    tga_t = (tga["value"] / 1_000.0) if tga else 0.0  # B -> T
    net = bs_t - rrp_t - tga_t

    return _result(
        round(net, 3),
        {
            "fed_balance_T": round(bs_t, 3),
            "rrp_T": round(rrp_t, 3),
            "tga_T": round(tga_t, 3),
        },
        bs["date"],
    )


# ---------------------------------------------------------------------------

def compute_all(store: Store) -> dict:
    """Run every derived computation and return a dict by name."""
    return {
        "sahm_rule":         sahm_rule(store),
        "m2_yoy":            m2_yoy(store),
        "real_wages_yoy":    real_wages_yoy(store),
        "cpi_yoy":           yoy_growth(store, "cpi"),
        "core_cpi_yoy":      yoy_growth(store, "core_cpi"),
        "pce_yoy":           yoy_growth(store, "pce"),
        "core_pce_yoy":      yoy_growth(store, "core_pce"),
        "gdp_yoy":           yoy_growth(store, "real_gdp"),
        "r_vs_g":            r_vs_g(store),
        "yield_curve_2s10s": yield_curve_2s10s(store),
        "fed_net_liquidity": fed_net_liquidity(store),
        "housing_starts_yoy": yoy_growth(store, "housing_starts"),
    }
