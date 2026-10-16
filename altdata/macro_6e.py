"""
6e, THE REST: MACRO COMPLETENESS (16 Oct 2026, session B, branch 6e-rest).

    python -m altdata.macro_6e show [--as-of ISO]

The calc.* series of the architecture's Session 3 (docs/chester-reports-architecture-
v3.md, lines 422-697) that the free sources can carry, computed from the store and
written in the market_features pass (`rows()` rides compute_rows, after the AQ-3
rows). Nothing here fetches; every series is trigger_eligible false and reaches a
reader only through its lens (altdata/derived.py lens_forms) and the inflation
block. The CPI lead composite is altdata/cpi_lead.py's; its rows are written here
so the one pass writes every calc.

  S3a  path-aware sampling: calc.path_divergence_usdjpy, the close against the
       noon fixing, with its flag (path_divergence_flag(), config's sigma).
  S3b  rates and policy: 2y less EFFR, SOFR less IORB and less EFFR, CCC less BB,
       the real policy rate, and the overnight differentials against the euro
       area (EURSTR) and the UK (SONIA).
  S3c  fiscal and demand: the twelve-month deficit against nominal GDP, interest
       against receipts, the federal effective rate, R less G on both bases
       (marginal: the 10-year; average: the effective rate; both against nominal
       growth), the TGA's 13-week range and volatility, and debt against GDP by
       sector (federal, nonfinancial corporate, household).
  The two lenses other orders bind to 6e that are series: the core CPI less core
  PCE gap (JPM GTM change order, 3 Oct 2026) and the CPI lead composite's
  conditioner, realized ten-year inflation against the breakeven.

UNITS (Gotcha 2, each read off its FRED page on 16 Oct 2026): MTS flows, GFDEBTN,
BCNSDODNS, CMDEBT and WTREGEN in MILLIONS; GDP, A091RC1Q027SBEA and FGRECPT in
BILLIONS at an annual rate. Every ratio converts both legs to millions first.

Every row's availability is the latest of its inputs' (market_features' rule).
"""

from __future__ import annotations

import datetime as dt
import math
import statistics
import sys
from pathlib import Path
from typing import Optional

import yaml

from . import observations

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "config" / "macro_6e.yaml"

KEYS = [
    "calc.path_divergence_usdjpy",
    "calc.policy_2y_minus_effr_bp", "calc.sofr_iorb_bp", "calc.sofr_effr_bp",
    "calc.ccc_bb_oas_bp", "calc.real_policy_rate", "calc.policy_diff_us_ea_bp",
    "calc.policy_diff_us_uk_bp",
    "calc.deficit_ttm_pct_gdp", "calc.interest_to_receipts",
    "calc.federal_effective_rate", "calc.r_minus_g_marginal",
    "calc.r_minus_g_average", "calc.tga_range_13w", "calc.tga_vol_13w",
    "calc.fed_debt_total_pct_gdp", "calc.nonfin_corp_debt_pct_gdp",
    "calc.household_debt_pct_gdp",
    "calc.core_cpi_pce_gap", "calc.realized_10y_vs_expected_10y",
    "calc.cpi_lead_3m", "calc.cpi_lead_6m", "calc.cpi_lead_9m",
]


def config(path: Optional[Path] = None) -> dict:
    with open(path or CONFIG_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _month(day: str) -> str:
    return day[:7]


def _monthly(series: dict) -> dict[str, tuple[float, str, Optional[str], str]]:
    """month -> (value, available_at, kind, day) for the last observation in it."""
    out: dict[str, tuple[float, str, Optional[str], str]] = {}
    for day in sorted(series):
        v, a, k = series[day]
        out[_month(day)] = (v, a, k, day)
    return out


def _shift(month: str, n: int) -> str:
    y, m = int(month[:4]), int(month[5:7])
    y, m = divmod(y * 12 + (m - 1) + n, 12)
    return f"{y:04d}-{m + 1:02d}"


def yoy_monthly(series: dict) -> dict[str, tuple[float, list]]:
    """month -> (year-over-year percent, the two inputs' (available, kind)),
    each month against the same month a year before."""
    mo = _monthly(series)
    out = {}
    for m, (v, a, k, _d) in mo.items():
        p = mo.get(_shift(m, -12))
        if p and p[0]:
            out[m] = (100.0 * (v / p[0] - 1.0), [(a, k), (p[1], p[2])])
    return out


def rows(db: observations.ObservationStore, as_of: Optional[str] = None,
         first_day: Optional[str] = None, cfg: Optional[dict] = None) -> list[dict]:
    """Every series above, for every date the inputs support."""
    from .market_features import _at_or_before, _availability, _load, _yoy
    c = cfg if cfg is not None else config()
    out: list[dict] = []

    def emit(key: str, day: str, value: Optional[float], parts: list) -> None:
        if value is None or not math.isfinite(value) or not parts:
            return
        if first_day and day < first_day:
            return
        avail, kind = _availability(parts)
        out.append({"registry_key": key, "instrument": None, "observed_at": day,
                    "available_at": avail, "value": round(value, 6),
                    "source": "calc", "availability_kind": kind})

    def load(key: str) -> dict:
        return _load(db, key, as_of)

    def p(s: dict, d: str) -> tuple:
        return (s[d][1], s[d][2])

    def same_day(key: str, a: dict, b: dict, f) -> None:
        for d in sorted(a):
            if d in b:
                emit(key, d, f(a[d][0], b[d][0]), [p(a, d), p(b, d)])

    # --- S3a: the close against the noon fixing -----------------------------
    for pair in (c.get("path_divergence") or {}).get("pairs") or []:
        fx, cl = load(pair["fixing"]), load(pair["close"])
        same_day(pair["key"], cl, fx,
                 lambda close, fix: 100.0 * (close / fix - 1.0) if fix else None)

    # --- S3b: rates and policy (bp) ------------------------------------------
    y2, y10, effr = load("fred.yield_2y"), load("fred.yield_10y"), load("fred.effr")
    sofr, iorb = load("fred.sofr"), load("fred.iorb")
    same_day("calc.policy_2y_minus_effr_bp", y2, effr, lambda a, b: (a - b) * 100.0)
    same_day("calc.sofr_iorb_bp", sofr, iorb, lambda a, b: (a - b) * 100.0)
    same_day("calc.sofr_effr_bp", sofr, effr, lambda a, b: (a - b) * 100.0)
    same_day("calc.ccc_bb_oas_bp", load("fred.ccc_oas"), load("fred.bb_oas"),
             lambda a, b: (a - b) * 100.0)
    same_day("calc.policy_diff_us_ea_bp", effr, load("fred.estr"),
             lambda a, b: (a - b) * 100.0)
    same_day("calc.policy_diff_us_uk_bp", effr, load("fred.sonia"),
             lambda a, b: (a - b) * 100.0)
    core_pce = load("fred.core_pce")
    for d in sorted(core_pce):
        got = _yoy(core_pce, d)
        ed = _at_or_before(effr, d)
        if got is None or ed is None:
            continue
        # The policy rate known at the month's first day, less that month's core
        # PCE inflation: the real policy rate, in percent.
        emit("calc.real_policy_rate", d, effr[ed][0] - got[0],
             [p(effr, ed)] + [p(core_pce, x) for x in got[1]])

    # --- S3c: fiscal and demand ----------------------------------------------
    gdp = load("fred.gdp_nominal")              # BILLIONS, SAAR, quarterly
    mts = load("fred.mts_deficit")              # MILLIONS, monthly
    mdays = sorted(mts)
    for i, d in enumerate(mdays):
        if i < 11:
            continue
        win = mdays[i - 11:i + 1]
        if _month(win[0]) != _shift(_month(d), -11):
            continue                            # a hole in the twelve months
        gd = _at_or_before(gdp, d)
        if gd is None or not gdp[gd][0]:
            continue
        ttm = sum(mts[x][0] for x in win)
        emit("calc.deficit_ttm_pct_gdp", d, 100.0 * ttm / (gdp[gd][0] * 1000.0),
             [p(mts, x) for x in win] + [p(gdp, gd)])
    intr, rec = load("fred.fed_interest_payments"), load("fred.fed_current_receipts")
    same_day("calc.interest_to_receipts", intr, rec,
             lambda a, b: 100.0 * a / b if b else None)
    debt = load("fred.fed_debt_total")          # MILLIONS
    eff: dict[str, float] = {}
    for d in sorted(intr):
        if d in debt and debt[d][0]:
            v = 100.0 * intr[d][0] * 1000.0 / debt[d][0]
            eff[d] = v
            emit("calc.federal_effective_rate", d, v, [p(intr, d), p(debt, d)])
    for d in sorted(gdp):
        g = _yoy(gdp, d)
        if g is None:
            continue
        gp = [p(gdp, x) for x in g[1]]
        yd = _at_or_before(y10, d)
        if yd is not None:
            emit("calc.r_minus_g_marginal", d, y10[yd][0] - g[0], [p(y10, yd)] + gp)
        if d in eff:
            emit("calc.r_minus_g_average", d, eff[d] - g[0],
                 [p(intr, d), p(debt, d)] + gp)
    for key, src in (("calc.fed_debt_total_pct_gdp", debt),
                     ("calc.nonfin_corp_debt_pct_gdp", load("fred.nonfin_corp_debt")),
                     ("calc.household_debt_pct_gdp", load("fred.total_hh_debt"))):
        for d in sorted(src):
            if d in gdp and gdp[d][0]:
                emit(key, d, 100.0 * src[d][0] / (gdp[d][0] * 1000.0),
                     [p(src, d), p(gdp, d)])
    tga = load("fred.tga")                      # MILLIONS, weekly
    weeks = int((c.get("tga") or {}).get("weeks", 13))
    tdays = sorted(tga)
    for i in range(weeks - 1, len(tdays)):
        win = tdays[i - weeks + 1:i + 1]
        vals = [tga[x][0] * 1e6 for x in win]
        parts = [p(tga, x) for x in win]
        emit("calc.tga_range_13w", win[-1], max(vals) - min(vals), parts)
        ch = [b - a for a, b in zip(vals, vals[1:])]
        if len(ch) >= 2:
            emit("calc.tga_vol_13w", win[-1], statistics.stdev(ch), parts)

    # --- the bound lenses that are series ------------------------------------
    ccpi, cpce = yoy_monthly(load("fred.core_cpi")), yoy_monthly(core_pce)
    for m in sorted(ccpi):
        if m in cpce:
            emit("calc.core_cpi_pce_gap", f"{m}-01", ccpi[m][0] - cpce[m][0],
                 ccpi[m][1] + cpce[m][1])
    from . import cpi_lead                                       # noqa: PLC0415
    lc = (c.get("cpi_lead") or {})
    cond = lc.get("conditioner") or {}
    cpi_m = _monthly(load(cond.get("cpi", "fred.cpi")))
    be = load(cond.get("breakeven", "fred.breakeven_10y"))
    for m, (v, a, k, d) in sorted(cpi_m.items()):
        base = cpi_m.get(_shift(m, -120))
        if not base or not base[0]:
            continue
        month_end = (dt.date.fromisoformat(_shift(m, 1) + "-01")
                     - dt.timedelta(days=1)).isoformat()
        bd = _at_or_before(be, month_end)
        if bd is None:
            continue
        realized = 100.0 * ((v / base[0]) ** 0.1 - 1.0)
        emit(cond.get("key", "calc.realized_10y_vs_expected_10y"), f"{m}-01",
             realized - be[bd][0], [(a, k), (base[1], base[2]), p(be, bd)])
    for r in cpi_lead.composite_rows({x["lead"]: load(x["lead"])
                                      for x in lc.get("components") or []
                                      if x.get("lead")}, lc):
        emit(r["key"], r["day"], r["value"], r["parts"])
    return out


def path_divergence_flag(st, cutoff: str, cfg: Optional[dict] = None) -> list[dict]:
    """Each pair's latest divergence against its own trailing year: flagged at
    or beyond `sigma` standard deviations (S3a's "JPY flags path_divergence")."""
    c = (cfg if cfg is not None else config()).get("path_divergence") or {}
    out = []
    for pair in c.get("pairs") or []:
        pts = sorted((str(r["observed_at"])[:10], float(r["value_num"]))
                     for r in st.as_of(pair["key"], cutoff)
                     if r.get("value_num") is not None)
        res = {"label": pair["label"], "key": pair["key"]}
        if not pts:
            res.update(flag=None, reason="no divergence stored")
            out.append(res)
            continue
        last_d, last = pts[-1]
        lo = (dt.date.fromisoformat(last_d)
              - dt.timedelta(days=int(c.get("window_days", 365)))).isoformat()
        hist = [v for d, v in pts[:-1] if d >= lo]
        if len(hist) < int(c.get("min_days", 120)):
            res.update(flag=None, level=last, as_of=last_d,
                       reason=f"{len(hist)} days in the trailing year; "
                              f"{c.get('min_days', 120)} needed")
        else:
            mu, sd = statistics.fmean(hist), statistics.pstdev(hist)
            z = (last - mu) / sd if sd else 0.0
            res.update(level=last, as_of=last_d, z=round(z, 2), n=len(hist),
                       flag=abs(z) >= float(c.get("sigma", 3.0)))
        out.append(res)
    return out


def _main(argv: list[str]) -> int:
    import argparse
    import json
    ap = argparse.ArgumentParser(description="6e's macro-completeness series.")
    ap.add_argument("cmd", choices=["show"])
    ap.add_argument("--as-of", default=None)
    a = ap.parse_args(argv)
    from . import session                                        # noqa: PLC0415
    cutoff = a.as_of or session.utc_iso(timespec="microseconds")
    with observations.ObservationStore() as st:
        latest = {}
        for k in KEYS:
            r = st.as_of(k, cutoff)
            if r:
                x = max(r, key=lambda z: str(z["observed_at"]))
                latest[k] = (str(x["observed_at"])[:10], x.get("value_num"))
            else:
                latest[k] = None
        from . import cpi_lead                                   # noqa: PLC0415
        print(json.dumps({"series": latest,
                          "path_divergence": path_divergence_flag(st, cutoff),
                          "cpi_lead": cpi_lead.read(st, cutoff)},
                         indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
