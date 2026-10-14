"""
THE 10-YEAR ANCHORS LENS (SR-43; signal-triage batch 4, ST4-08 and ST4-09) and the
adjudication of the four voices on the 10-year top. Ruled 6 Oct 2026, section 4.1.

    python -m altdata.rates_anchors show [--as-of ISO]

Config: config/rates_anchors.yaml. Nothing here fetches.

THREE ANCHORS, ONE LINE: the 10-year against each, the gap in basis points with
its sign.

  INFLATION   the trailing ten-year average of CPI year on year -- a transparent
              stand-in for Topdown Charts' unpublished "10-Year Inflation Rate
              Model", labelled so. The FIT regresses the monthly 10-year on the
              anchor over the stored history; the printed RESIDUAL is the 10-year
              minus the fitted yield.
  FISCAL      the twin balance (general government balance plus current account,
              % of GDP, IMF WEO) against the 10-year across 14 developed markets,
              refit from whatever the store holds as of the cutoff. The US reading
              is the fitted yield minus the market's. Needs the WEO writer's keys
              for the 14; with fewer than `min_countries` it says so and fits
              nothing. A 14-point cross-section is fragile: refit, never
              extrapolated.
  TERM PREMIUM  the ACM series, unchanged.

RIGHTS: report-only modifiers on the Plumbing & rates read. Every line printed
carries "(descriptive; unvalidated, n=0)". Nothing enters the market-state object.
"""

from __future__ import annotations

import datetime as dt
import json
import statistics
import sys
from pathlib import Path
from typing import Any, Optional

import yaml

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "config" / "rates_anchors.yaml"


def load_config(path: Optional[Path] = None) -> dict:
    with open(path or CONFIG_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _points(st, key: str, cutoff: str) -> list[tuple[str, float]]:
    rows = [(str(r["observed_at"])[:10], float(r["value_num"]))
            for r in st.as_of(key, cutoff) if r.get("value_num") is not None]
    return sorted(dict(rows).items())


def ols(xs: list[float], ys: list[float]) -> Optional[dict]:
    """Ordinary least squares y = a + b x, with R squared."""
    n = len(xs)
    if n < 3 or len(set(xs)) < 2:
        return None
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    a = my - b * mx
    ss_res = sum((y - (a + b * x)) ** 2 for x, y in zip(xs, ys))
    ss_tot = sum((y - my) ** 2 for y in ys)
    return {"a": a, "b": b, "r2": 1.0 - ss_res / ss_tot if ss_tot else None, "n": n}


def _monthly(points: list[tuple[str, float]]) -> dict[str, float]:
    """The month-end value of each month (the last observation in it)."""
    out: dict[str, float] = {}
    for d, v in points:
        out[d[:7]] = v
    return out


# ---------------------------------------------------------------------------
# (1) the inflation anchor
# ---------------------------------------------------------------------------
def inflation_anchor(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg if cfg is not None else load_config()
    ia = cfg.get("inflation_anchor") or {}
    years = int(ia.get("trailing_years") or 10)
    cpi = _monthly(_points(st, ia.get("cpi", "fred.cpi"), cutoff))
    y10 = _monthly(_points(st, ia.get("ten_year", "fred.yield_10y"), cutoff))
    months = sorted(cpi)
    yoy = {m: 100.0 * (cpi[m] / cpi[p] - 1.0) for i, m in enumerate(months)
           if i >= 12 and (p := months[i - 12])}
    ym = sorted(yoy)
    anchor = {}
    n = 12 * years
    for i in range(n - 1, len(ym)):
        anchor[ym[i]] = statistics.fmean(yoy[m] for m in ym[i - n + 1: i + 1])
    if not anchor or not y10:
        return {"state": "absent", "reason": "CPI or the 10-year not stored for the "
                                             f"trailing {years} years"}
    both = [m for m in sorted(anchor) if m in y10]
    last_anchor_m = max(anchor)
    ten_now = _points(st, ia.get("ten_year", "fred.yield_10y"), cutoff)[-1]
    out = {"state": "ok", "anchor_pct": anchor[last_anchor_m],
           "anchor_month": last_anchor_m, "ten_year_pct": ten_now[1],
           "ten_year_as_of": ten_now[0],
           "gap_bp": 100.0 * (ten_now[1] - anchor[last_anchor_m])}
    if len(both) >= int(ia.get("fit_min_months") or 120):
        f = ols([anchor[m] for m in both], [y10[m] for m in both])
        if f:
            fitted = f["a"] + f["b"] * anchor[last_anchor_m]
            out.update({"fit": {k: round(v, 4) if isinstance(v, float) else v
                                for k, v in f.items()},
                        "fitted_pct": fitted,
                        "residual_bp": 100.0 * (ten_now[1] - fitted),
                        "fit_span": [both[0], both[-1]]})
    else:
        out["fit_note"] = (f"fit needs {ia.get('fit_min_months') or 120} months; "
                           f"{len(both)} stored")
    return out


# ---------------------------------------------------------------------------
# (2) the fiscal anchor: the twin-deficit fit
# ---------------------------------------------------------------------------
def _latest(st, key: str, cutoff: str) -> Optional[tuple[str, float]]:
    p = _points(st, key, cutoff)
    return p[-1] if p else None


def fiscal_anchor(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    """The cross-section: each country's latest twin balance (balance plus
    current account, the same WEO year for both) against its latest 10-year,
    as of the cutoff; OLS; the US fitted yield minus its market yield."""
    cfg = cfg if cfg is not None else load_config()
    fa = cfg.get("fiscal_anchor") or {}
    pts, missing = [], []
    for c in fa.get("countries") or []:
        bal = _latest(st, fa["weo_balance"].format(iso3=c["iso3"]), cutoff)
        ca = _latest(st, fa["weo_current_account"].format(iso3=c["iso3"]), cutoff)
        y = _latest(st, c["yield"], cutoff)
        if not (bal and ca and y) or bal[0] != ca[0]:
            missing.append(c["name"])
            continue
        pts.append({"iso3": c["iso3"], "name": c["name"], "twin": bal[1] + ca[1],
                    "weo_year": bal[0][:4], "yield": y[1], "yield_as_of": y[0]})
    need = int(fa.get("min_countries") or 10)
    if len(pts) < need:
        return {"state": "absent", "n": len(pts), "missing": missing,
                "reason": f"the twin-deficit fit needs {need} countries with WEO "
                          f"balances and a 10-year; {len(pts)} of "
                          f"{len(fa.get('countries') or [])} carry them"}
    f = ols([p["twin"] for p in pts], [p["yield"] for p in pts])
    us = next((p for p in pts if p["iso3"] == "usa"), None)
    out = {"state": "ok", "n": len(pts), "missing": missing, "points": pts,
           "fit": f}
    if us and f:
        fitted = f["a"] + f["b"] * us["twin"]
        out.update({"us_twin_pct_gdp": us["twin"], "us_fitted_pct": fitted,
                    "us_market_pct": us["yield"], "us_as_of": us["yield_as_of"],
                    "gap_bp": 100.0 * (fitted - us["yield"])})
    return out


def term_premium(st, cutoff: str, cfg: Optional[dict] = None) -> Optional[dict]:
    cfg = cfg if cfg is not None else load_config()
    x = _latest(st, cfg.get("term_premium") or "acm.term_premium_10y", cutoff)
    return {"pct": x[1], "as_of": x[0]} if x else None


# ---------------------------------------------------------------------------
# The one line, and the read
# ---------------------------------------------------------------------------
def _bp(v: float) -> str:
    return f"{v:+.0f} bp"


def read(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg if cfg is not None else load_config()
    return {"inflation": inflation_anchor(st, cutoff, cfg),
            "fiscal": fiscal_anchor(st, cutoff, cfg),
            "term_premium": term_premium(st, cutoff, cfg),
            "tag": cfg.get("tag")}


def line(r: dict) -> str:
    """'10-year 4.25% against its anchors: ...' -- each anchor with the gap in
    bp and its sign, the absent ones named."""
    inf, fis, tp = r["inflation"], r["fiscal"], r["term_premium"]
    parts = []
    if inf.get("state") == "ok":
        s = (f"inflation anchor {inf['anchor_pct']:.2f}% "
             f"(10-year less anchor {_bp(inf['gap_bp'])})")
        if inf.get("fitted_pct") is not None:
            s += (f", fitted {inf['fitted_pct']:.2f}% on the anchor, residual "
                  f"{_bp(inf['residual_bp'])}")
        parts.append(s)
    else:
        parts.append(f"inflation anchor absent ({inf.get('reason')})")
    if fis.get("state") == "ok" and fis.get("us_fitted_pct") is not None:
        parts.append(f"twin-deficit fit {fis['us_fitted_pct']:.2f}% against "
                     f"{fis['us_market_pct']:.2f}% paid (fitted less paid "
                     f"{_bp(fis['gap_bp'])}; n={fis['n']}, R² {fis['fit']['r2']:.2f})")
    else:
        parts.append(f"twin-deficit fit absent ({fis.get('reason')})")
    parts.append(f"ACM term premium {tp['pct']:.2f}% (as of {tp['as_of']})" if tp
                 else "ACM term premium not stored")
    ten = inf.get("ten_year_pct")
    head = f"10-year {ten:.2f}% against its anchors: " if ten is not None else \
        "The 10-year's anchors: "
    return head + "; ".join(parts) + f". {r.get('tag') or ''}".rstrip()


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    from . import observations, session                         # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.rates_anchors")
    ap.add_argument("cmd", choices=["show"])
    ap.add_argument("--as-of", default=None)
    a = ap.parse_args(argv)
    cut = a.as_of or session.utc_iso()
    with observations.ObservationStore() as st:
        r = read(st, cut)
    print(line(r))
    print(json.dumps({k: v for k, v in r.items() if k != "tag"}, indent=2,
                     default=str)[:4000])
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
