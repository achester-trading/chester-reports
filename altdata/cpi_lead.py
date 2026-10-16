"""
THE CPI LEAD COMPOSITE (architecture Part 17, docs/chester-reports-architecture-
v3.md lines 3386-3516; 6e, the rest, 16 Oct 2026). Config: config/macro_6e.yaml
`cpi_lead`.

"Weighted implied CPI three to nine months forward, built from each component with
its lag applied and weighted by CPI basket share." Each component is ONE leading
series for one basket component (the correlation guard: nothing counted twice),
with its stated lag. A component with lag L supports a horizon h only when L >= h:
the projection h months ahead reads the component as it stood L - h months before
the latest month, so nothing forward is read. Each horizon prints the basket share
it covers; a horizon no component reaches is absent with that reason.

STATUS: UNVALIDATED (stated lags). The architecture says the composite cannot be
built before Session 6's backfill and lag fit; so the lags are parameters, the
printed figure says "stated lags, unvalidated", and the KILL CONDITION is coded:
the 6-month composite against realized CPI six months later, over the history the
store holds. Below `kill_min_months` pairs the test says so; at or above it, a
correlation under `kill_min_corr` withholds the composite and prints why.

Rights: none. trigger_eligible false; report-only, in the inflation block.
"""

from __future__ import annotations

import math
import statistics
from typing import Any, Optional


def _months(series: dict) -> dict[str, tuple[float, str, Optional[str]]]:
    out: dict[str, tuple[float, str, Optional[str]]] = {}
    for day in sorted(series):
        v, a, k = series[day]
        out[day[:7]] = (v, a, k)
    return out


def _shift(month: str, n: int) -> str:
    y, m = int(month[:4]), int(month[5:7])
    y, m = divmod(y * 12 + (m - 1) + n, 12)
    return f"{y:04d}-{m + 1:02d}"


def component_value(comp: dict, mo: dict, month: str) -> Optional[tuple[float, list]]:
    """The component's implied inflation at `month` of its own data: scale x
    (year over year, or the level) + offset; with the inputs' availability."""
    cur = mo.get(month)
    if cur is None:
        return None
    if comp.get("transform", "yoy") == "yoy":
        prev = mo.get(_shift(month, -12))
        if prev is None or not prev[0]:
            return None
        raw = 100.0 * (cur[0] / prev[0] - 1.0)
        parts = [(cur[1], cur[2]), (prev[1], prev[2])]
    else:
        raw, parts = cur[0], [(cur[1], cur[2])]
    return float(comp.get("scale", 1.0)) * raw + float(comp.get("offset", 0.0)), parts


def project(series_by_key: dict, cfg: dict, month: str, h: int) -> dict:
    """The composite h months ahead of `month`: each covering component's value
    lag - h months back, weighted by basket share over the covered share."""
    used, num, wsum, parts, missing = [], 0.0, 0.0, [], []
    for comp in cfg.get("components") or []:
        if not comp.get("lead"):
            missing.append({"name": comp["name"], "weight": comp["weight"],
                            "reason": comp.get("absent_reason") or "no lead series"})
            continue
        lag = int(comp.get("lag_months", 0))
        if lag < h:
            missing.append({"name": comp["name"], "weight": comp["weight"],
                            "reason": f"its stated lag ({lag} months) is shorter "
                                      f"than the horizon"})
            continue
        mo = _months(series_by_key.get(comp["lead"]) or {})
        got = component_value(comp, mo, _shift(month, h - lag))
        if got is None:
            missing.append({"name": comp["name"], "weight": comp["weight"],
                            "reason": "its lead is not stored for that month"})
            continue
        val, pp = got
        used.append({"name": comp["name"], "weight": comp["weight"], "lag": lag,
                     "value": round(val, 4)})
        num += comp["weight"] * val
        wsum += comp["weight"]
        parts += pp
    total = sum(float(c["weight"]) for c in cfg.get("components") or [])
    return {"horizon": h, "value": round(num / wsum, 4) if wsum else None,
            "covered_share": round(wsum / total, 4) if total else 0.0,
            "components": used, "missing": missing, "parts": parts}


def composite_rows(series_by_key: dict, cfg: dict) -> list[dict]:
    """calc.cpi_lead_<h>m for every month the components support, stamped the
    month's first day: the implied CPI year over year h months later."""
    months = sorted({m for s in series_by_key.values() for m in _months(s)})
    out = []
    for m in months:
        for h in cfg.get("horizons_months") or [3, 6, 9]:
            r = project(series_by_key, cfg, m, int(h))
            if r["value"] is not None and r["parts"]:
                out.append({"key": f"calc.cpi_lead_{int(h)}m", "day": f"{m}-01",
                            "value": r["value"], "parts": r["parts"]})
    return out


def _pts(st, key: str, cutoff: str) -> dict[str, float]:
    return {str(r["observed_at"])[:7]: float(r["value_num"])
            for r in st.as_of(key, cutoff) if r.get("value_num") is not None}


def kill_test(st, cutoff: str, cfg: dict) -> dict:
    """The 6-month composite against realized CPI year over year six months on."""
    comp = _pts(st, "calc.cpi_lead_6m", cutoff)
    cpi = _pts(st, cfg.get("target", "fred.cpi"), cutoff)
    pairs = []
    for m, v in sorted(comp.items()):
        t, base = cpi.get(_shift(m, 6)), cpi.get(_shift(m, -6))
        if t is not None and base:
            pairs.append((v, 100.0 * (t / base - 1.0)))
    need = int(cfg.get("kill_min_months", 60))
    if len(pairs) < need:
        return {"state": "untested", "n": len(pairs),
                "reason": f"{len(pairs)} months of composite against realized CPI; "
                          f"{need} needed for the kill test"}
    xs, ys = zip(*pairs)
    try:
        r = statistics.correlation(xs, ys)
    except statistics.StatisticsError:
        r = float("nan")
    floor = float(cfg.get("kill_min_corr", 0.3))
    if not math.isfinite(r) or r < floor:
        return {"state": "killed", "n": len(pairs), "corr": r,
                "reason": f"the 6-month composite's correlation with realized CPI "
                          f"is {r:.2f} over {len(pairs)} months, under {floor:.2f}: "
                          f"fix the lags or drop it"}
    return {"state": "passed", "n": len(pairs), "corr": round(r, 3)}


def rolloff(st, cutoff: str, cfg: dict) -> Optional[dict]:
    """The conditioner's roll-off calendar: trailing ten-year annualized CPI if
    monthly CPI runs at each flat path for the next k months."""
    cond = cfg.get("conditioner") or {}
    cpi = _pts(st, cond.get("cpi", "fred.cpi"), cutoff)
    if not cpi:
        return None
    m = max(cpi)
    base = cpi.get(_shift(m, -120))
    if not base:
        return None
    out = {"as_of": m, "now": round(100.0 * ((cpi[m] / base) ** 0.1 - 1.0), 3),
           "paths": []}
    for path in cond.get("rolloff_paths_pct") or []:
        for k in cond.get("rolloff_months") or []:
            b = cpi.get(_shift(m, -120 + int(k)))
            if not b:
                continue
            fut = cpi[m] * (1.0 + float(path) / 100.0) ** (int(k) / 12.0)
            out["paths"].append({"path_pct": path, "months": int(k),
                                 "trailing_10y": round(100.0 * ((fut / b) ** 0.1 - 1.0), 3)})
    return out


def read(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    """The composite as of the cutoff: each horizon with its covered share and
    components, the kill test, the conditioner and its roll-off calendar."""
    if cfg is None:
        from .macro_6e import config                             # noqa: PLC0415
        cfg = config().get("cpi_lead") or {}
    keys = [c["lead"] for c in cfg.get("components") or [] if c.get("lead")]
    series = {k: {str(r["observed_at"])[:10]: (float(r["value_num"]),
                                              str(r["available_at"]), None)
                  for r in st.as_of(k, cutoff) if r.get("value_num") is not None}
              for k in keys}
    months = sorted({m for s in series.values() for m in _months(s)})
    latest = months[-1] if months else None
    horizons = []
    for h in cfg.get("horizons_months") or [3, 6, 9]:
        if latest is None:
            horizons.append({"horizon": int(h), "value": None, "covered_share": 0.0,
                             "reason": "no component's lead is stored"})
            continue
        r = project(series, cfg, latest, int(h))
        r.pop("parts", None)
        if r["value"] is None:
            r["reason"] = ("no component's stated lag reaches this horizon"
                           if not r["components"] else "no covering component stored")
        horizons.append(r)
    kt = kill_test(st, cutoff, cfg)
    cond = cfg.get("conditioner") or {}
    cv = _pts(st, cond.get("key", "calc.realized_10y_vs_expected_10y"), cutoff)
    return {"status": cfg.get("status", "unvalidated"), "as_of_month": latest,
            "horizons": horizons, "kill_test": kt,
            "withheld": kt["state"] == "killed",
            "conditioner": ({"month": max(cv), "value": cv[max(cv)]} if cv else None),
            "rolloff": rolloff(st, cutoff, cfg)}


def summary(r: dict) -> dict[str, Any]:
    """The figures a renderer prints, nothing else."""
    return {h["horizon"]: (h.get("value"), h.get("covered_share"))
            for h in r.get("horizons") or []}
