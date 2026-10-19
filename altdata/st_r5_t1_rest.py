"""
The rest of signal-triage Batch 6's Tranche 1: items 31, 32, 38, 39, 42, 43 and 44.

    python -m altdata.st_r5_t1_rest show [--as-of ISO] [--json]   # the seven reads

docs/change-order-signal-triage-batch-6-2026-10-15.md; section 4 rulings 3
(concentration and breadth: 30, 31, 44), 4 (inflation regime: 32, 42) and 5 (the
growth lead: 43). Tranche 1 only:

  ST-R5.31a  concentration()   the top-10 share of the S&P 500's float-adjusted
                               capitalisation, from SPY's holdings, against the
                               40-44% historical peak band; BofA's basket mapped
                               once against the same file (verify item 8)
  ST-R5.44a  breadth()         the drawdown histogram (members by distance from
                               their 52-week closing high, four buckets) and the
                               average-member against index drawdown gap
  ST-R5.32a  oil_shock()       6-month rolling correlations of daily changes:
                               Brent-SPX at or below its 20-year 20th percentile
                               while Brent-10y is at or above its 80th
  ST-R5.42a  expectations()    the composite z of four expectation measures; it
                               refuses a composite on fewer than three
  ST-R5.39a  real_yields()     the G10 and the EM screen: nominal 10-year, real on
                               core CPI with headline beside it, linker where one
                               is stored; the US-DE and US-JP differentials
  ST-R5.38a  gold_equity()     the WGC above-ground stock at the gold price over
                               ACWI's capitalisation (by hand), dual percentiles
  ST-R5.43a  diffusion()       the net share of central banks whose last move was
                               a cut, monthly, from the BIS table; the G7 CLI and
                               the global PMI (by hand) beside it

REPORT-ONLY, EVERY ONE. No read here enters the market-state object, a composite
weight, a trigger, a book rule or the register. Item 32 is ruled an
`inflation.driver` sub-state, and the object has no driver on inflation: adding
one is a rules change (v1.13) behind a pre-registered calibration, so the read is
computed here and the pre-registration is listed (the notes), as item 34's flag
was. Every threshold the order does not give is config/st_r5_t1_rest.yaml's,
session-set, with its reason.

Reads only. Every function takes the store and a cutoff and reads as of it; none
fetches, writes or calls a model.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
from pathlib import Path
from typing import Any, Optional

import yaml

from . import derived
from .st_r5_rates import _back, _on_or_before, _pts, _years_back, lens, lens_text, ordinal

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "config" / "st_r5_t1_rest.yaml"


def config(path: Optional[Path] = None) -> dict:
    with open(path or CONFIG_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def _day(cutoff: str) -> str:
    return str(cutoff)[:10]


def _month(day: str) -> str:
    return str(day)[:7]


def _month_index(m: str) -> int:
    return int(m[:4]) * 12 + int(m[5:7]) - 1


def _month_of(k: int) -> str:
    return f"{k // 12:04d}-{k % 12 + 1:02d}"


def month_name(m: str) -> str:
    return dt.date(int(m[:4]), int(m[5:7]), 1).strftime("%b %Y")


def monthly(pts: list[tuple[str, float]], how: str = "last") -> list[tuple[str, float]]:
    """[(YYYY-MM, value)]: each month's last observation, or its average."""
    by: dict[str, list[float]] = {}
    for d, v in pts:
        by.setdefault(_month(d), []).append(v)
    if how == "mean":
        return [(m, sum(v) / len(v)) for m, v in sorted(by.items())]
    return [(m, v[-1]) for m, v in sorted(by.items())]


def yoy(series: list[tuple[str, float]]) -> list[tuple[str, float]]:
    """Monthly index -> % change on the same month a year earlier."""
    d = dict(series)
    out = []
    for m, v in series:
        prev = d.get(_month_of(_month_index(m) - 12))
        if prev:
            out.append((m, round(100.0 * (v / prev - 1.0), 4)))
    return out


def _mean_sd(xs: list[float]) -> tuple[float, float]:
    n = len(xs)
    mu = sum(xs) / n
    var = sum((x - mu) ** 2 for x in xs) / (n - 1) if n > 1 else 0.0
    return mu, math.sqrt(var)


def _signed_pp(v: float) -> str:
    v = 0.0 if round(v, 1) == 0 else v
    return f"{v:+.1f} pp"


# ---------------------------------------------------------------------------
# The constituent store (sp500.member_*): what both 31a and 44a read
# ---------------------------------------------------------------------------
def holdings(st, cutoff: str, key: str) -> dict:
    """The newest holdings day knowable at the cutoff: {day, weights{ticker: %}}."""
    day = st.newest_observed_any(key, cutoff)
    if not day:
        return {"day": None, "weights_pct": {}}
    w = {}
    for tk in st.instruments(key):
        r = st.latest_as_of(key, cutoff, tk)
        if r and str(r["observed_at"])[:10] == day and r.get("value_num") is not None:
            w[tk] = float(r["value_num"])
    return {"day": day, "weights_pct": w}


# ---------------------------------------------------------------------------
# ST-R5.31a -- the peak-band flag
# ---------------------------------------------------------------------------
def concentration(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    c = cfg.get("concentration") or {}
    h = holdings(st, cutoff, c.get("weight_key", "sp500.member_weight"))
    out = {"band_low_pct": c["band_low_pct"], "band_high_pct": c["band_high_pct"],
           "overlay": c.get("overlay"), "overlay_built": bool(c.get("overlay_built")),
           "overlay_input_pct": c.get("overlay_input_pct")}
    if not h["weights_pct"]:
        b = (cfg.get("breadth") or {}).get("awaiting", "awaiting constituent prices")
        return dict(out, state="absent",
                    reason=b.replace("prices", "holdings") + " (SPY's holdings file, "
                    "from the constituent writer)")
    age = (dt.date.fromisoformat(_day(cutoff)) - dt.date.fromisoformat(h["day"])).days
    if age > int(c.get("max_age_days", 7)):
        return dict(out, state="absent",
                    reason=f"the newest holdings are of {h['day']}, {age} days old")
    classes = c.get("share_classes") or {}
    issuers: dict[str, float] = {}
    for tk, v in h["weights_pct"].items():
        issuers[classes.get(tk, tk)] = issuers.get(classes.get(tk, tk), 0.0) + v
    w = sorted(issuers.items(), key=lambda kv: -kv[1])
    n = int(c.get("top_n", 10))
    top = w[:n]
    share = round(sum(v for _, v in top), 2)
    basket = [t for t in (c.get("bofa_basket") or []) if t in h["weights_pct"]]
    basket_share = round(sum(h["weights_pct"][t] for t in basket), 2)
    lo, hi = float(c["band_low_pct"]), float(c["band_high_pct"])
    where = ("above the band" if share > hi else
             "inside the band" if share >= lo else "below the band")
    return dict(out, state="read", day=h["day"], top_share_pct=share,
                top_names=[t for t, _ in top], members_n=len(w),
                basket_share_pct=basket_share,
                basket_missing=[t for t in (c.get("bofa_basket") or [])
                                if t not in h["weights_pct"]],
                flag=share >= lo, where=where)


def concentration_line(c: dict) -> str:
    if c["state"] != "read":
        return f"Top-10 share of the S&P 500: {c['reason']}."
    band = f"{c['band_low_pct']:.0f}–{c['band_high_pct']:.0f}%"
    s = (f"The ten largest issuers' share of the S&P 500's float-adjusted capitalisation, "
         f"{c['top_share_pct']:.1f}% "
         f"on {c['day']} (SPY's holdings): {c['where']} of past bubble peaks "
         f"({band}, BofA)")
    if c["flag"]:
        s += "; the peak-band flag is on"
    s += (f". BofA's basket (the Magnificent 7, Broadcom, AMD, Micron) holds "
          f"{c['basket_share_pct']:.1f}% of the same file.")
    if not c["overlay_built"]:
        s += (f" A calibration of the {c['overlay']} overlay's top-10 input "
              f"(designed at {c['overlay_input_pct']:.0f}%; the overlay is not built), "
              f"with no weight.")
    return s


# ---------------------------------------------------------------------------
# ST-R5.44a -- the drawdown histogram and the gap
# ---------------------------------------------------------------------------
def _drawdown_pct(pts: list[tuple[str, float]], day: str, start: str,
                  min_closes: int) -> Optional[float]:
    win = [v for d, v in pts if start < d <= day]
    if len(win) < min_closes:
        return None
    hi = max(win)
    return round(100.0 * (win[-1] / hi - 1.0), 4) if hi > 0 else None


def breadth(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    b = cfg.get("breadth") or {}
    awaiting = b.get("awaiting", "awaiting constituent prices")
    idx = _pts(st, b.get("index_key", "yfinance.mkt_gspc"), cutoff)
    if not idx:
        return {"state": "absent", "reason": "no S&P 500 close is stored"}
    day = idx[-1][0]
    start = _back(day, int(b.get("window_days", 365)))
    min_closes = int(b.get("min_closes", 240))
    h = holdings(st, cutoff, b.get("weight_key", "sp500.member_weight"))
    members = sorted(h["weights_pct"])
    if not members:
        return {"state": "absent", "reason": f"{awaiting} (no constituent holdings stored)"}
    lag_start = _back(day, int(b.get("max_lag_days", 4)))
    dds: dict[str, float] = {}
    key = b.get("close_key", "sp500.member_close")
    for tk in members:
        pts = _pts(st, key, cutoff, tk)
        if not pts or pts[-1][0] < lag_start:
            continue
        dd = _drawdown_pct(pts, pts[-1][0], start, min_closes)
        if dd is not None:
            dds[tk] = dd
    cov = round(100.0 * len(dds) / len(members), 1)
    if cov < float(b.get("min_coverage_pct", 95.0)):
        return {"state": "absent", "members_n": len(members), "counted_n": len(dds),
                "reason": f"{awaiting} ({len(dds)} of {len(members)} members hold a "
                          f"year of closes)"}
    idx_dd = _drawdown_pct(idx, day, start, min_closes)
    if idx_dd is None:
        return {"state": "absent", "reason": "the S&P 500 does not hold a year of closes"}
    e1, e2 = (float(x) for x in b.get("buckets_pct", [10.0, 20.0]))
    n = len(dds)
    counts = {"record_n": sum(1 for v in dds.values() if v >= 0.0),
              "within_10_n": sum(1 for v in dds.values() if -e1 < v < 0.0),
              "off_10_20_n": sum(1 for v in dds.values() if -e2 < v <= -e1),
              "off_20_plus_n": sum(1 for v in dds.values() if v <= -e2)}
    avg = round(sum(dds.values()) / n, 2)
    return {"state": "read", "day": day, "members_n": len(members), "counted_n": n,
            "coverage_pct": cov, "bucket_counts": counts,
            "bucket_shares": {k[:-2] + "_pct": round(100.0 * v / n, 1)
                              for k, v in counts.items()},
            "avg_member_dd_pct": avg, "index_dd_pct": round(idx_dd, 2),
            "gap_pct": round(avg - idx_dd, 2)}


BUCKET_LABELS = (("record", "At a 52-week closing high"),
                 ("within_10", "Within 10% of it"),
                 ("off_10_20", "10–20% below"),
                 ("off_20_plus", "20% or more below"))


def breadth_rows(b: dict) -> list[list[str]]:
    if b["state"] != "read":
        return []
    return [[lab, str(b["bucket_counts"][k + "_n"]),
             f"{b['bucket_shares'][k + '_pct']:.0f}%"]
            for k, lab in BUCKET_LABELS]


def breadth_line(b: dict) -> str:
    if b["state"] != "read":
        return f"The drawdown histogram and the average-member gap: {b['reason']}."
    return (f"The average S&P 500 member closed {abs(b['avg_member_dd_pct']):.1f}% below "
            f"its 52-week closing high on {b['day']}, the index "
            f"{abs(b['index_dd_pct']):.1f}% below its own: a gap of "
            f"{_signed_pp(b['gap_pct'])} ({b['counted_n']} of {b['members_n']} members "
            f"counted).")


# ---------------------------------------------------------------------------
# ST-R5.32a -- the oil-shock classifier
# ---------------------------------------------------------------------------
def _changes(pts: list[tuple[str, float]], log_ret: bool) -> dict[str, float]:
    out = {}
    for (d0, v0), (d1, v1) in zip(pts, pts[1:]):
        if log_ret:
            if v0 > 0 and v1 > 0:
                out[d1] = math.log(v1 / v0)
        else:
            out[d1] = v1 - v0
    return out


def rolling_corr(a: dict[str, float], b: dict[str, float], days: list[str],
                 window: int, min_obs: int) -> list[tuple[str, float]]:
    """Pearson correlation over each trailing `window` of `days` (the sessions
    where every series printed), kept where the window holds `min_obs`."""
    out = []
    xs = [a[d] for d in days]
    ys = [b[d] for d in days]
    for i in range(len(days)):
        lo = max(0, i - window + 1)
        x, y = xs[lo:i + 1], ys[lo:i + 1]
        if len(x) < min_obs:
            continue
        mx, my = sum(x) / len(x), sum(y) / len(y)
        sxy = sum((p - mx) * (q - my) for p, q in zip(x, y))
        sxx = sum((p - mx) ** 2 for p in x)
        syy = sum((q - my) ** 2 for q in y)
        if sxx > 0 and syy > 0:
            out.append((days[i], sxy / math.sqrt(sxx * syy)))
    return out


def oil_shock(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    c = cfg.get("oil_shock") or {}
    years = int(c.get("history_years", 20))
    window, min_obs = int(c.get("window_sessions", 126)), int(c.get("min_obs", 120))
    brent = _pts(st, c.get("brent_key", "fred.brent"), cutoff)
    spx = _pts(st, c.get("spx_key", "yfinance.mkt_gspc"), cutoff)
    ten = _pts(st, c.get("ten_year_key", "fred.yield_10y"), cutoff)
    out = {"substate_built": bool(c.get("substate_built")), "history_years_n": years,
           "spx_below_percentile": c["spx_below_pct"],
           "ten_year_above_percentile": c["ten_year_above_pct"]}
    if not (brent and spx and ten):
        miss = [n for n, p in (("Brent", brent), ("the S&P 500", spx), ("the 10-year", ten))
                if not p]
        return dict(out, state="absent", reason=f"{', '.join(miss)} not stored")
    last = min(brent[-1][0], spx[-1][0], ten[-1][0])
    start = _years_back(last, years)
    # Changes from a year before the history window, so the first window in it
    # is a whole one.
    pre = _years_back(start, 1)
    db = _changes([p for p in brent if pre <= p[0] <= last], True)
    ds = _changes([p for p in spx if pre <= p[0] <= last], True)
    dt_ = _changes([p for p in ten if pre <= p[0] <= last], False)
    days = sorted(set(db) & set(ds) & set(dt_))
    c_spx = rolling_corr(db, ds, days, window, min_obs)
    c_ten = rolling_corr(db, dt_, days, window, min_obs)
    c_spx = [p for p in c_spx if p[0] > start]
    c_ten = [p for p in c_ten if p[0] > start]
    if not c_spx or not c_ten or c_spx[-1][0] != c_ten[-1][0]:
        return dict(out, state="absent",
                    reason=f"fewer than {min_obs} sessions with Brent, the S&P 500 "
                           f"and the 10-year all printed")
    now_s, now_t = c_spx[-1][1], c_ten[-1][1]
    p_s = derived.percentile_of([v for _, v in c_spx], now_s)
    p_t = derived.percentile_of([v for _, v in c_ten], now_t)
    first = c_spx[0][0]
    full = first <= _years_back(last, years - 1)
    on_s = p_s <= float(c["spx_below_pct"])
    on_t = p_t >= float(c["ten_year_above_pct"])
    return dict(out, state="read", day=c_spx[-1][0],
                brent_spx_corr_ratio=round(now_s, 3), brent_10y_corr_ratio=round(now_t, 3),
                percentile_brent_spx=p_s, percentile_brent_10y=p_t,
                n_windows=len(c_spx), history_from=first, history_full=full,
                spx_leg=on_s, ten_year_leg=on_t, supply_shock=on_s and on_t)


def oil_shock_line(o: dict) -> str:
    if o["state"] != "read":
        return f"The oil-shock signature: {o['reason']}."
    yrs = o["history_years_n"]
    hist = (f"{yrs} years" if o["history_full"] else
            f"its stored history since {o['history_from']}, shorter than {yrs} years")
    read = ("the supply-shock signature is ON: oil trades as the hedge"
            if o["supply_shock"] else
            "no supply-shock signature (demand-driven or mixed)")
    return (f"Brent against the S&P 500, six-month correlation of daily changes "
            f"{o['brent_spx_corr_ratio']:+.2f} ({ordinal(o['percentile_brent_spx'])} "
            f"percentile); Brent against the 10-year {o['brent_10y_corr_ratio']:+.2f} "
            f"({ordinal(o['percentile_brent_10y'])}); over {hist} (n={o['n_windows']:,} "
            f"windows), on {o['day']}: {read}. The order's rule: the first at or below "
            f"its {ordinal(o['spx_below_percentile'])} percentile while the second is at or "
            f"above its {ordinal(o['ten_year_above_percentile'])}.")


# ---------------------------------------------------------------------------
# ST-R5.42a -- the composite inflation-expectations z-score
# ---------------------------------------------------------------------------
def _input_z(series: list[tuple[str, float]], month: str, window: int, min_n: int,
             max_lag: int) -> dict:
    s = [(m, v) for m, v in series if m <= month]
    if not s:
        return {"present": False, "reason": "not stored"}
    m_last, v_last = s[-1]
    lag = _month_index(month) - _month_index(m_last)
    if lag > max_lag:
        return {"present": False, "reason": f"its latest month is {month_name(m_last)}, "
                                            f"{lag} months old"}
    lo = _month_index(m_last) - window
    win = [v for m, v in s if _month_index(m) > lo]
    if len(win) < min_n:
        return {"present": False, "reason": f"{len(win)} months stored, fewer than {min_n}"}
    mu, sd = _mean_sd(win)
    if sd <= 0:
        return {"present": False, "reason": "no variation in its window"}
    return {"present": True, "month": m_last, "value_pct": round(v_last, 3),
            "z_score": round((v_last - mu) / sd, 2), "months_n": len(win),
            "from": [m for m, _ in s if _month_index(m) > lo][0]}


def expectations_at(st, cutoff: str, month: str, cfg: dict) -> dict:
    c = cfg.get("expectations") or {}
    rows = []
    for inp in c.get("inputs") or []:
        pts = _pts(st, inp["key"], cutoff)
        series = monthly(pts, "last")
        z = _input_z(series, month, int(c.get("window_months", 120)),
                     int(c.get("min_months", 36)), int(c.get("max_lag_months", 3)))
        rows.append({"id": inp["id"], "label": inp["label"], **z})
    present = [r for r in rows if r["present"]]
    need = int(c.get("min_inputs", 3))
    comp = (round(sum(r["z_score"] for r in present) / len(present), 2)
            if len(present) >= need else None)
    return {"month": month, "inputs": rows, "n_present": len(present),
            "n_inputs": len(rows), "min_inputs_n": need, "composite_z_score": comp}


def expectations(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    c = cfg.get("expectations") or {}
    month = _month(_day(cutoff))
    now = expectations_at(st, cutoff, month, cfg)
    back = _month_of(_month_index(month) - int(c.get("change_months", 3)))
    then = expectations_at(st, cutoff, back, cfg)
    flag_z = float(c.get("flag_z", 1.0))
    out = {**now, "flag_threshold_z": flag_z,
           "composite_then_z_score": then["composite_z_score"], "then_month": back,
           "flag": (now["composite_z_score"] is not None
                    and now["composite_z_score"] >= flag_z)}
    # DEANCHOR's definition (SR-24), printed as a comparison, never a state.
    be = _pts(st, (c.get("inputs") or [{}])[0].get("key", "fred.breakeven_5y5y"), cutoff)
    yr = str(c.get("deanchor_year", 2022))
    hi = [v for d, v in be if d.startswith(yr)]
    out["deanchor"] = ({"high_pct": round(max(hi), 2), "now_pct": round(be[-1][1], 2),
                        "day": be[-1][0], "year": yr} if hi and be else None)
    return out


def expectations_rows(e: dict) -> list[list[str]]:
    rows = []
    for r in e["inputs"]:
        if not r["present"]:
            continue
        rows.append([r["label"], f"{r['value_pct']:.2f}%", month_name(r["month"]),
                     f"{r['z_score']:+.2f}", f"since {month_name(r['from'])} (n={r['months_n']})"])
    return rows


def expectations_absent(e: dict) -> list[str]:
    return [f"{r['label']}: {r['reason']}" for r in e["inputs"] if not r["present"]]


def expectations_lines(e: dict) -> list[str]:
    if e["composite_z_score"] is None:
        lines = [f"The composite: not printed -- {e['n_present']} of {e['n_inputs']} "
                 f"inputs present, fewer than {e['min_inputs_n']}."]
    else:
        s = (f"The composite inflation-expectations z: {e['composite_z_score']:+.2f}, the mean "
             f"of {e['n_present']} of {e['n_inputs']} inputs' own ten-year z")
        if e["composite_then_z_score"] is not None:
            s += f" ({e['composite_then_z_score']:+.2f} in {month_name(e['then_month'])})"
        s += (f"; the flag (z at or above {e['flag_threshold_z']:+.1f}) is "
              f"{'on' if e['flag'] else 'off'}.")
        lines = [s]
    d = e.get("deanchor")
    if d:
        rel = "above" if d["now_pct"] > d["high_pct"] else "below"
        lines.append(f"The 5y5y breakeven at {d['now_pct']:.2f}% on {d['day']}, {rel} its "
                     f"{d['year']} high of {d['high_pct']:.2f}% (DEANCHOR's first leg; the "
                     f"flag itself is a definition, not built).")
    return lines


# ---------------------------------------------------------------------------
# ST-R5.39a -- the real-yield panel
# ---------------------------------------------------------------------------
def _latest_month(series: list[tuple[str, float]], month: str) -> Optional[tuple[str, float]]:
    s = [(m, v) for m, v in series if m <= month]
    return s[-1] if s else None


def _cpi(st, cutoff: str, key: Optional[str], is_yoy: bool) -> list[tuple[str, float]]:
    if not key:
        return []
    m = monthly(_pts(st, key, cutoff), "last")
    return m if is_yoy else yoy(m)


def real_yields(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    c = cfg.get("real_yields") or {}
    lag_max = int(c.get("max_cpi_lag_months", 3))
    rows = []
    for ctry in c.get("countries") or []:
        r: dict[str, Any] = {"id": ctry["id"], "name": ctry["name"], "gaps": []}
        if ctry.get("gap_nominal"):
            r["gaps"].append(ctry["gap_nominal"])
        nom = monthly(_pts(st, ctry["nominal"], cutoff), "mean") if ctry.get("nominal") else []
        if ctry.get("nominal") and not nom:
            r["gaps"].append("its 10-year is not stored yet")
        if nom:
            r["month"], r["nominal_pct"] = nom[-1][0], round(nom[-1][1], 2)
        for leg, key, is_yoy in (("core", ctry.get("core"), False),
                                 ("core", ctry.get("core_yoy"), True),
                                 ("headline", ctry.get("headline"), False),
                                 ("headline", ctry.get("headline_yoy"), True)):
            if not key or f"{leg}_cpi_pct" in r:
                continue
            s = _cpi(st, cutoff, key, is_yoy)
            if not s:
                r["gaps"].append(f"its {leg} CPI is not stored yet")
                continue
            if not nom:
                continue
            cm = _latest_month(s, r["month"])
            if cm is None or _month_index(r["month"]) - _month_index(cm[0]) > lag_max:
                r["gaps"].append(f"its {leg} CPI is stale against the yield")
                continue
            r[f"{leg}_cpi_month"] = cm[0]
            r[f"{leg}_cpi_pct"] = round(cm[1], 2)
            r[f"real_{leg}_pct"] = round(r["nominal_pct"] - cm[1], 2)
        if ctry.get("gap_cpi"):
            r["gaps"].append(ctry["gap_cpi"])
        if not ctry.get("core") and not ctry.get("core_yoy") and ctry.get("headline_yoy"):
            r["em_core_gap"] = True
        if ctry.get("linker") and nom:
            lk = monthly(_pts(st, ctry["linker"], cutoff), "mean")
            lm = _latest_month(lk, r["month"])
            if lm and lm[0] == r["month"]:
                r["linker_pct"] = round(lm[1], 2)
        elif ctry.get("gap_linker"):
            r["linker_gap"] = ctry["gap_linker"]
        rows.append(r)
    by = {r["id"]: r for r in rows}
    diffs = []
    for a, b in c.get("differentials") or []:
        ra, rb = by.get(a) or {}, by.get(b) or {}
        if "real_core_pct" in ra and "real_core_pct" in rb:
            diffs.append({"pair": f"{a}-{b}", "spread_bp": round((ra["real_core_pct"]
                                                           - rb["real_core_pct"]) * 100),
                          "month": min(ra["month"], rb["month"])})
        else:
            miss = rb.get("name", b) if "real_core_pct" in ra else ra.get("name", a)
            diffs.append({"pair": f"{a}-{b}", "spread_bp": None,
                          "reason": f"{miss}'s real yield on core CPI is a gap"})
    return {"rows": rows, "differentials": diffs,
            "em_core_gap": c.get("em_core_gap", "no core CPI stored")}


def _pct(v: Optional[float]) -> str:
    return "—" if v is None else f"{v:.2f}%"


def real_yield_rows(ry: dict) -> list[list[str]]:
    out = []
    for r in ry["rows"]:
        if "nominal_pct" not in r:
            continue
        out.append([r["name"], _pct(r.get("nominal_pct")), month_name(r["month"]),
                    _pct(r.get("real_core_pct")), _pct(r.get("real_headline_pct")),
                    _pct(r.get("linker_pct"))])
    return out


def real_yield_absent(ry: dict) -> list[str]:
    out = []
    for r in ry["rows"]:
        if "nominal_pct" not in r:
            out.append(f"{r['name']}: " + "; ".join(r["gaps"] or ["not stored"]))
        elif r["gaps"]:
            out.append(f"{r['name']} (partly): " + "; ".join(r["gaps"]))
    # Two gaps shared by many rows print once each.
    lk = [r["name"] for r in ry["rows"] if r.get("linker_gap")]
    if lk:
        out.append("Linker real yields: the US's only; none on FRED for "
                   + ", ".join(lk))
    em = [r["name"] for r in ry["rows"] if r.get("em_core_gap")]
    if em:
        out.append(f"Core CPI for {', '.join(em)}: {ry.get('em_core_gap')} "
                   f"(their real yields are on headline)")
    return out


def differential_lines(ry: dict) -> list[str]:
    out = []
    for d in ry["differentials"]:
        a, b = d["pair"].split("-")
        if d["spread_bp"] is None:
            out.append(f"Real 10-year differential, {a} less {b}: a gap ({d['reason']}).")
        else:
            out.append(f"Real 10-year differential, {a} less {b}, on core CPI: "
                       f"{d['spread_bp']:+d} bp ({month_name(d['month'])}).")
    return out


# ---------------------------------------------------------------------------
# ST-R5.38a -- the gold/equity market-cap ratio
# ---------------------------------------------------------------------------
def gold_equity(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    c = cfg.get("gold_equity") or {}
    stock = _pts(st, c.get("stock_key", "wgc.above_ground_t"), cutoff)
    gold = _pts(st, c.get("gold_key", "yfinance.mkt_gold_front"), cutoff)
    out = {"wfe_gap": c.get("wfe_gap")}
    cap_key = c.get("cap_key")
    if not cap_key:
        return dict(out, state="not_tracked",
                    reason=c.get("no_cap_reason", "not tracked: no free source for "
                                                  "world equity capitalisation"))
    cap = _pts(st, cap_key, cutoff)
    miss = [lab for lab, p in (("the WGC above-ground stock", stock),
                               ("the gold price", gold),
                               ("world equity capitalisation", cap)) if not p]
    if miss:
        return dict(out, state="absent", reason="; ".join(miss) + " not stored yet")
    oz = float(c.get("oz_per_tonne", 32150.7466))
    lag = int(c.get("max_gold_lag_days", 5))
    series = []
    for d, cap_bn in cap:
        s = _on_or_before(stock, d)
        g = _on_or_before(gold, d)
        if not s or not g or g[0] < _back(d, lag) or cap_bn <= 0:
            continue
        series.append((d, round(100.0 * s[1] * oz * g[1] / (cap_bn * 1e9), 3),
                       s[0], g[1]))
    if not series:
        return dict(out, state="absent",
                    reason="no month where the stock, the gold price and the cap meet")
    d, ratio, stock_day, gold_px = series[-1]
    years = int((c.get("windows_years") or [10])[0])
    return dict(out, state="read", day=d, ratio_pct=ratio, stock_as_of=stock_day,
                gold_price=round(gold_px, 2),
                lens=lens([(x[0], x[1]) for x in series], years))


def gold_equity_line(g: dict) -> str:
    if g["state"] == "not_tracked":
        return f"Gold against world equities — {g['reason']}."
    if g["state"] != "read":
        return f"Gold against world equities: {g['reason']}."
    return (f"Gold's above-ground stock at ${g['gold_price']:,.0f}/oz is {g['ratio_pct']:.1f}% "
            f"of world equity capitalisation on {g['day']} (stock as of {g['stock_as_of']}); "
            f"{lens_text(g['lens'])}.")


# ---------------------------------------------------------------------------
# ST-R5.43a -- the global policy diffusion index
# ---------------------------------------------------------------------------
def diffusion_series(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    """{month: {net_pct, cuts, hikes, areas}} for every month with enough areas."""
    cfg = cfg or config()
    c = cfg.get("diffusion") or {}
    key = c.get("rate_key", "bis.policy_rate")
    lag, eps = int(c.get("max_lag_months", 3)), float(c.get("min_move_pp", 0.01))
    per: dict[str, dict[str, float]] = {}
    for area in st.instruments(key):
        m = dict(monthly(_pts(st, key, cutoff, area), "last"))
        if m:
            per[area] = m
    if not per:
        return {"areas_n": 0, "months": {}}
    # Each area's moves: {month: +1 hike / -1 cut}.
    moves: dict[str, list[tuple[int, int]]] = {}
    spans: dict[str, tuple[int, int]] = {}
    for area, m in per.items():
        ks = sorted(_month_index(x) for x in m)
        spans[area] = (ks[0], ks[-1])
        mv = []
        vals = {_month_index(x): v for x, v in m.items()}
        prev = None
        for k in ks:
            v = vals[k]
            if prev is not None and abs(v - prev) >= eps:
                mv.append((k, 1 if v > prev else -1))
            prev = v
        moves[area] = mv
    lo = min(s[0] for s in spans.values())
    hi = max(s[1] for s in spans.values())
    out = {}
    for k in range(lo + 1, hi + 1):
        cuts = hikes = n = 0
        for area, (a0, a1) in spans.items():
            if a0 > k or a1 < k - lag:
                continue
            n += 1
            last = [s for mk, s in moves[area] if mk <= k]
            if last:
                cuts += last[-1] < 0
                hikes += last[-1] > 0
        if n >= int(c.get("min_areas", 20)):
            out[_month_of(k)] = {"net_pct": round(100.0 * (cuts - hikes) / n, 1),
                                 "cuts_n": cuts, "hikes_n": hikes, "areas_n": n}
    return {"areas_n": len(per), "months": out}


def diffusion(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    c = cfg.get("diffusion") or {}
    ds = diffusion_series(st, cutoff, cfg)
    lead = int(c.get("lead_months", 8))
    out: dict[str, Any] = {"lead_months_n": lead}
    if not ds["months"]:
        out.update(state="absent", reason=(
            "the BIS policy-rate table is not stored yet (the extended pull)"
            if not ds["areas_n"] else
            f"fewer than {c.get('min_areas', 20)} central banks counted in any month"))
    else:
        months = sorted(ds["months"])
        m = months[-1]
        cur = ds["months"][m]
        series = [(x, ds["months"][x]["net_pct"]) for x in months]
        years = int((c.get("windows_years") or [10])[0])
        ago = {n: ds["months"].get(_month_of(_month_index(m) - n)) for n in (6, 12)}
        out.update(state="read", month=m, **cur,
                   net_6m_ago_pct=(ago[6] or {}).get("net_pct"),
                   net_12m_ago_pct=(ago[12] or {}).get("net_pct"),
                   reaches=_month_of(_month_index(m) + lead),
                   lens=lens([(x + "-01", v) for x, v in series], years))
        lead_from = _month_of(_month_index(m) - lead)
        out["net_at_lead_pct"] = (ds["months"].get(lead_from) or {}).get("net_pct")
        out["lead_from"] = lead_from
    cli = monthly(_pts(st, c.get("cli_key", "fred.oecd_cli_g7"), cutoff), "last")
    out["cli"] = {"month": cli[-1][0], "level": round(cli[-1][1], 2)} if cli else None
    pmi = st.latest_as_of(c.get("pmi_key", "manual.global_pmi"), cutoff)
    out["pmi"] = ({"level": float(pmi["value_num"]), "as_of": str(pmi["observed_at"])[:10]}
                  if pmi and pmi.get("value_num") is not None else None)
    return out


def diffusion_lines(d: dict) -> list[str]:
    if d["state"] != "read":
        lines = [f"Global policy diffusion: {d['reason']}."]
    else:
        s = (f"Global policy diffusion, {month_name(d['month'])}: net {d['net_pct']:+.0f}% of "
             f"{d['areas_n']} central banks last moved by cutting ({d['cuts_n']} cut, "
             f"{d['hikes_n']} hiked)")
        ago = [f"{v:+.0f}% {n}" for v, n in ((d["net_6m_ago_pct"], "six months earlier"),
                                              (d["net_12m_ago_pct"], "a year earlier"))
               if v is not None]
        if ago:
            s += "; " + ", ".join(ago)
        s += f"; {lens_text(d['lens'])}."
        lines = [s]
    cli, pmi = d.get("cli"), d.get("pmi")
    lead = d.get("lead_months_n", 8)
    if d["state"] == "read" and d.get("net_at_lead_pct") is not None:
        lines.append(f"At the lead: diffusion {lead} months back ({month_name(d['lead_from'])}) "
                     f"was {d['net_at_lead_pct']:+.0f}%; "
                     + (f"the OECD G7 leading indicator is {cli['level']:.2f} "
                        f"({month_name(cli['month'])})" if cli else
                        "the OECD G7 leading indicator is not stored yet")
                     + "; " + (f"the global manufacturing PMI {pmi['level']:.1f} "
                               f"(by hand, {pmi['as_of']})" if pmi else
                               "the global manufacturing PMI not entered (by hand)")
                     + ". Report-only until its lead is ledgered.")
    return lines


def ahead_line(d: dict) -> Optional[str]:
    if d["state"] != "read":
        return None
    return (f"Policy diffusion at {d['net_pct']:+.0f}% ({month_name(d['month'])}); on "
            f"Topdown's {d['lead_months_n']}-month lead it bears on growth into "
            f"{month_name(d['reaches'])}. The lead is unvalidated until its own ledger "
            f"is written.")


# ---------------------------------------------------------------------------
def public(d: dict) -> dict:
    """A read for a section's `data`: the lens replaced by its printed text, so
    every number left carries a typed field name (the numeral audit types a
    field by its name, and an untyped one accepts any unit)."""
    out = {k: v for k, v in d.items() if k != "lens"}
    if "lens" in d:
        out["lens_text"] = lens_text(d["lens"])
    return out


# ---------------------------------------------------------------------------
def build(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    return {"concentration": concentration(st, cutoff, cfg),
            "breadth": breadth(st, cutoff, cfg),
            "oil_shock": oil_shock(st, cutoff, cfg),
            "expectations": expectations(st, cutoff, cfg),
            "real_yields": real_yields(st, cutoff, cfg),
            "gold_equity": gold_equity(st, cutoff, cfg),
            "diffusion": diffusion(st, cutoff, cfg)}


def lines(b: dict) -> list[str]:
    """Every code-written line, in the order the report prints them."""
    return ([concentration_line(b["concentration"]), breadth_line(b["breadth"]),
             oil_shock_line(b["oil_shock"])] + expectations_lines(b["expectations"])
            + differential_lines(b["real_yields"]) + [gold_equity_line(b["gold_equity"])]
            + diffusion_lines(b["diffusion"]))


def main(argv: Optional[list[str]] = None) -> int:
    from . import observations, session                          # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.st_r5_t1_rest")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("show", help="print the seven reads as of a cutoff")
    s.add_argument("--as-of", default=None)
    s.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    cutoff = a.as_of or session.utc_iso()
    with observations.ObservationStore() as st:
        b = build(st, cutoff)
    if a.json:
        print(json.dumps(b, indent=2, default=str))
        return 0
    for ln in lines(b):
        print(ln)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
