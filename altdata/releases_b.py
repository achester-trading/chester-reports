"""
THE RELEASE LENSES, GROUP B (Batch 7 item 48, lenses 12-20: ST-R6.48d, the PPI
lenses, and ST-R6.48e, the GDP lenses; lenses-group-b, 18 Oct 2026, session B).
The order: docs/change-order-signal-triage-batch-7-2026-10-16.md on docs-batch-7.
Config: config/releases.yaml `ppi_lenses:` and `gdp_lenses:`. Group A's module,
altdata/releases.py, holds the month arithmetic both share.

Everything is read from the observation store AS OF the cutoff (lens 22's vintage
rule, as 48c built it): a quarterly series is keyed by its quarter's first month,
so a quarter on quarter change is the three-month step, annualised by the fourth
power, and a vintage not yet published at the cutoff does not exist here. Nothing
is written: these are report panels, recomputed at render time.

  ppi_lenses(st, cutoff)      lenses 12-14: the intermediate-demand pipeline, the
                              PCE-relevant components, trade services apart
  gdp_lenses(st, cutoff)      lenses 15-20: final sales to private domestic
                              purchasers and the contributions, the investment
                              split, GDI less GDP, NIPA profits against S&P EPS,
                              income and saving, the GDPNow path and the print
  ppi_line / gdp_line         lens 24's release-day lines for the two releases

    python -m altdata.releases_b show [--as-of ISO] [--db PATH]   # read-only

EVERY LENS FIGURE CARRIES ITS FORM (the metric-lenses brief): its family, its
long window, two percentiles over its OWN history -- five years and the long
window -- each with its n, and the disagreement flag when they differ by 30
points or more (derived.DISAGREEMENT_POINTS). An input that is absent prints
"not stored" with its key. REPORT-ONLY: the order's flags are lenses 2-4 (Group
A); nothing here is a flag, a market-state input (R28) or a composite's.
"""

from __future__ import annotations

import datetime as dt
import statistics
from typing import Any, Callable, Optional

from . import derived, observations
from .releases import (annualised, config, mm, month_name, monthly, r, shift,
                       yoy)

NOT_STORED = "not stored"
FAMILY = "release"


def not_stored(key: str) -> str:
    return f"{NOT_STORED} ({key})"


def printable(reason: Optional[str]) -> str:
    """A reason as printed: the internal key in brackets dropped (a renderer
    never prints a store id)."""
    import re                                                   # noqa: PLC0415
    return re.sub(r" \([a-z_]+\.[a-z0-9_.]+\)", "", str(reason or ""))


def quarter_name(month: Optional[str]) -> str:
    if not month:
        return "n/a"
    return f"Q{(int(month[5:7]) - 1) // 3 + 1} {month[:4]}"


def history(s: dict[str, float], f: Callable[[dict, str], Optional[float]]
            ) -> list[tuple[str, float]]:
    """[(YYYY-MM-01, f(s, month))] for every month f can compute, in order."""
    out = []
    for m in sorted(s):
        v = f(s, m)
        if v is not None:
            out.append((f"{m}-01", float(v)))
    return out


def lens_stat(key: str, series: list[tuple[str, float]], cutoff: str) -> dict:
    """The lens form of one figure: its latest value, family, long window, the
    two percentiles over its own history with their n, and the disagreement
    flag. `key` is the figure's source series, whose long window it takes."""
    lw, lw_why = derived.long_window_of(key, FAMILY)
    out: dict[str, Any] = {"family": FAMILY, "long_window": lw,
                           "long_window_basis": lw_why, "reasons": {}}
    if not series:
        out.update(period=None, value=None)
        out["reasons"]["value"] = not_stored(key)
        return out
    period, value = series[-1]
    as_of = derived._as_date(cutoff)
    p5 = derived._pct_in_window(series, value, as_of, 5)
    pl = derived._pct_in_window(series, value, as_of, lw)
    out.update(period=period[:7], value=r(value, 4),
               pctile_5y=p5["pct"], pctile_5y_n=p5["n"], pctile_5y_window=p5["window"],
               pctile_long=pl["pct"], pctile_long_n=pl["n"],
               pctile_long_window=pl["window"])
    for tag, p in (("pctile_5y", p5), ("pctile_long", pl)):
        if p["pct"] is None:
            out["reasons"][tag] = p["reason"]
    if p5["pct"] is not None and pl["pct"] is not None:
        out["disagree"] = abs(p5["pct"] - pl["pct"]) >= derived.DISAGREEMENT_POINTS
    else:
        out["disagree"] = None
        out["reasons"]["disagree"] = "needs both percentiles"
    return out


def _yoy(s: dict, m: str) -> Optional[float]:
    return yoy(s, m)


def _ann3(s: dict, m: str) -> Optional[float]:
    return annualised(s, m, 3)


def _mm(s: dict, m: str) -> Optional[float]:
    return mm(s, m)


def index_row(st, key: str, name: str, cutoff: str, sa: bool = True) -> dict:
    """A price index's month: the month's change, three months annualised (SA
    only), the year; the lens form on the year."""
    s = monthly(st, key, cutoff)
    if not s:
        return {"key": key, "name": name, "month": None, "reason": not_stored(key),
                "lens": lens_stat(key, [], cutoff)}
    M = max(s)
    row = {"key": key, "name": name, "month": M, "sa": sa, "mm_pct": r(mm(s, M)),
           "ann_3m_pct": r(annualised(s, M, 3), 2) if sa else None,
           "yoy_pct": r(yoy(s, M), 2), "lens": lens_stat(key, history(s, _yoy), cutoff)}
    return row


# ---------------------------------------------------------------------------
# ST-R6.48d -- LENSES 12-14, PPI
# ---------------------------------------------------------------------------
def ppi_lenses(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    c = (cfg or config())["ppi_lenses"]
    fd = index_row(st, c["final_demand"]["key"], c["final_demand"]["name"], cutoff)
    stages = [index_row(st, x["key"], x["name"], cutoff) for x in c["stages"]]
    # 12. The pipeline: each stage's year less final demand's, the same month
    fds = monthly(st, c["final_demand"]["key"], cutoff)
    for row in stages:
        M = row.get("month")
        if M is None or not fds:
            row["gap_to_final_pp"] = None
            continue
        a, b = yoy(monthly(st, row["key"], cutoff), M), yoy(fds, M)
        row["gap_to_final_pp"] = r(a - b, 2) if a is not None and b is not None else None
    pce = [index_row(st, x["key"], x["name"], cutoff, sa=False) for x in c["pce_relevant"]]
    trade = index_row(st, c["trade_services"]["key"], c["trade_services"]["name"], cutoff)
    core = index_row(st, c["core_ex_trade"]["key"], c["core_ex_trade"]["name"], cutoff)
    return {"final_demand": fd, "pipeline": stages, "pce_relevant": pce,
            "trade_services": trade, "core_ex_trade": core,
            "month": fd.get("month")}


# ---------------------------------------------------------------------------
# ST-R6.48e -- LENSES 15-20, GDP
# ---------------------------------------------------------------------------
def level_row(st, key: str, name: str, cutoff: str) -> dict:
    """A level in percent (a growth rate, a contribution, a share): the
    quarter's or month's value; the lens form on the level itself."""
    s = monthly(st, key, cutoff)
    if not s:
        return {"key": key, "name": name, "month": None, "value": None,
                "reason": not_stored(key), "lens": lens_stat(key, [], cutoff)}
    M = max(s)
    return {"key": key, "name": name, "month": M, "value": r(s[M], 2),
            "lens": lens_stat(key, history(s, lambda x, m: x[m]), cutoff)}


def growth_row(st, key: str, name: str, cutoff: str) -> dict:
    """A quarterly level: quarter on quarter annualised and the year; the lens
    form on the annualised quarter."""
    s = monthly(st, key, cutoff)
    if not s:
        return {"key": key, "name": name, "month": None, "reason": not_stored(key),
                "lens": lens_stat(key, [], cutoff)}
    M = max(s)
    return {"key": key, "name": name, "month": M, "level": r(s[M], 1),
            "qq_ann_pct": r(annualised(s, M, 3), 2), "yoy_pct": r(yoy(s, M), 2),
            "lens": lens_stat(key, history(s, _ann3), cutoff)}


def _quarterly_mean(s: dict[str, float]) -> dict[str, float]:
    """{quarter's first month: the mean of its three months} for whole quarters."""
    out = {}
    for m in sorted(s):
        if int(m[5:7]) % 3 == 1:
            xs = [s.get(shift(m, i)) for i in range(3)]
            if None not in xs:
                out[m] = statistics.fmean(xs)
    return out


def nowcast_path(st, cutoff: str, key: str, print_key: str) -> dict:
    """Lens 20: GDPNow's updates for the newest quarter it covers at the cutoff
    (each a vintage, dated by its availability), and the newest quarter whose
    first print is knowable read against the last nowcast before it."""
    cut = observations.canonical_instant(cutoff)
    rows = st.as_of(key, cutoff)
    if not rows:
        return {"state": "absent", "reason": not_stored(key)}

    def path(observed_at: str) -> list[dict]:
        return [{"at": str(v["available_at"]), "value": float(v["value_num"])}
                for v in st.vintages(key, observed_at)
                if str(v["available_at"]) <= cut and v.get("value_num") is not None]

    cur = rows[-1]
    p = path(cur["observed_at"])
    out: dict[str, Any] = {"state": "read", "quarter": str(cur["observed_at"])[:7],
                           "path": p, "updates": len(p),
                           "first": r(p[0]["value"], 2) if p else None,
                           "latest": r(p[-1]["value"], 2) if p else None,
                           "change_pp": r(p[-1]["value"] - p[0]["value"], 2) if p else None}
    # The print against the nowcast, newest quarter first; the misses' history
    # is the lens's (each quarter's first print less the last nowcast before it)
    misses = []
    prints = {str(x["observed_at"])[:7]: x for x in st.as_of(print_key, cutoff)}
    for x in rows:
        q = str(x["observed_at"])[:7]
        pr = prints.get(q)
        if not pr:
            continue
        first = next((v for v in st.vintages(print_key, pr["observed_at"])
                      if str(v["available_at"]) <= cut and v.get("value_num") is not None),
                     None)
        if first is None:
            continue
        before = [v for v in path(x["observed_at"]) if v["at"] < str(first["available_at"])]
        if not before:
            continue
        misses.append({"quarter": q, "first_print": float(first["value_num"]),
                       "last_nowcast": before[-1]["value"],
                       "miss_pp": float(first["value_num"]) - before[-1]["value"]})
    if misses:
        m = misses[-1]
        out["print"] = {"quarter": m["quarter"], "first_print": r(m["first_print"], 2),
                        "last_nowcast": r(m["last_nowcast"], 2),
                        "miss_pp": r(m["miss_pp"], 2)}
    else:
        out["print"] = None
        out["print_reason"] = ("no quarter has both a first print and a nowcast "
                               "knowable before it at the cutoff")
    out["lens"] = lens_stat(print_key, [(f"{x['quarter']}-01", x["miss_pp"])
                                        for x in misses], cutoff)
    return out


def gdp_lenses(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    c = (cfg or config())["gdp_lenses"]
    out: dict[str, Any] = {}
    # 15. The core and the pieces outside it
    gr = level_row(st, c["real_growth"], "Real GDP, annualised", cutoff)
    fs = growth_row(st, c["final_sales_pdp"], "Final sales to private domestic "
                    "purchasers", cutoff)
    contribs = [level_row(st, x["key"], x["name"], cutoff) for x in c["contributions"]]
    q = gr.get("month")
    same = [x for x in contribs if x.get("month") == q and x.get("value") is not None]
    total = sum(x["value"] for x in same) if q and len(same) == len(contribs) else None
    out["core"] = {"quarter": q, "real_growth": gr, "final_sales": fs,
                   "contributions": contribs, "sum_pp": r(total, 2),
                   "residual_pp": (r(gr["value"] - total, 2)
                                   if total is not None and gr.get("value") is not None
                                   else None),
                   "deflator": growth_row(st, c["deflator"], "GDP deflator", cutoff)}
    # 16. The investment split
    parts = [monthly(st, k, cutoff) for k in c["ai_related"]]
    if all(parts):
        ai = {m: sum(p[m] for p in parts) for m in set.intersection(*[set(p) for p in parts])}
        M = max(ai)
        ai_row = {"keys": c["ai_related"], "month": M, "level_bn": r(ai[M], 1),
                  "qq_ann_pct": r(annualised(ai, M, 3), 2), "yoy_pct": r(yoy(ai, M), 2),
                  "lens": lens_stat(c["ai_related"][0], history(ai, _yoy), cutoff)}
    else:
        miss = [k for k, p in zip(c["ai_related"], parts) if not p]
        ai_row = {"keys": c["ai_related"], "month": None,
                  "reason": "; ".join(not_stored(k) for k in miss),
                  "lens": lens_stat(c["ai_related"][0], [], cutoff)}
    stx = monthly(st, c["structures"], cutoff)
    dc = _quarterly_mean(monthly(st, c["data_center"], cutoff))
    scale = float(c["data_center_to_billions"])
    if stx:
        M = max(stx)
        srow = {"key": c["structures"], "month": M, "level_bn": r(stx[M], 1),
                "yoy_pct": r(yoy(stx, M), 2)}
        if dc:
            ex = {m: stx[m] - dc[m] * scale for m in stx if m in dc}
            if M in ex:
                srow.update(ex_dc_bn=r(ex[M], 1), ex_dc_yoy_pct=r(yoy(ex, M), 2),
                            dc_bn=r(dc[M] * scale, 1),
                            lens=lens_stat(c["structures"], history(ex, _yoy), cutoff))
            else:
                srow["ex_dc_reason"] = (f"the data-center quarter {quarter_name(M)} is "
                                        f"not complete at the cutoff")
        else:
            srow["ex_dc_reason"] = not_stored(c["data_center"])
        if "lens" not in srow:
            srow["lens"] = lens_stat(c["structures"], history(stx, _yoy), cutoff)
    else:
        srow = {"key": c["structures"], "month": None, "reason": not_stored(c["structures"]),
                "lens": lens_stat(c["structures"], [], cutoff)}
    out["investment"] = {"ai_related": ai_row, "structures": srow,
                         "residential": growth_row(st, c["residential"],
                                                   "Real residential investment", cutoff)}
    # 17. GDI less GDP, percent of GDP
    gdi, gdp = monthly(st, c["gdi"], cutoff), monthly(st, c["gdp_nominal"], cutoff)
    both = sorted(set(gdi) & set(gdp))
    if both:
        gap = {m: 100.0 * (gdi[m] - gdp[m]) / gdp[m] for m in both if gdp[m]}
        M = both[-1]
        out["gdi_gap"] = {"quarter": M, "gdi_bn": r(gdi[M], 1), "gdp_bn": r(gdp[M], 1),
                          "gap_pct_gdp": r(gap[M], 2),
                          "change_4q_pp": (r(gap[M] - gap[shift(M, -12)], 2)
                                           if shift(M, -12) in gap else None),
                          "lens": lens_stat(c["gdi"], [(f"{m}-01", gap[m])
                                                       for m in sorted(gap)], cutoff)}
    else:
        out["gdi_gap"] = {"quarter": None, "reason": "; ".join(
            not_stored(k) for k, s in ((c["gdi"], gdi), (c["gdp_nominal"], gdp)) if not s)
            or "no quarter carries both", "lens": lens_stat(c["gdi"], [], cutoff)}
    # 18. NIPA profits against S&P EPS, each on the year
    pf, eps = monthly(st, c["profits"], cutoff), monthly(st, c["sp_eps"], cutoff)
    if pf:
        M = max(pf)
        row = {"quarter": M, "profits_bn": r(pf[M], 1), "profits_yoy_pct": r(yoy(pf, M), 2),
               "lens": lens_stat(c["profits"], history(pf, _yoy), cutoff)}
        em = shift(M, 2)                         # the quarter's last month
        if eps and em in eps and yoy(eps, em) is not None:
            row["eps_month"] = em
            row["eps_yoy_pct"] = r(yoy(eps, em), 2)
            if row["profits_yoy_pct"] is not None:
                row["divergence_pp"] = r(row["profits_yoy_pct"] - row["eps_yoy_pct"], 2)
        else:
            row["eps_reason"] = (not_stored(c["sp_eps"]) if not eps else
                                 f"S&P EPS for {month_name(em)} and a year earlier not "
                                 f"both stored at the cutoff")
        out["profits"] = row
    else:
        out["profits"] = {"quarter": None, "reason": not_stored(c["profits"]),
                          "lens": lens_stat(c["profits"], [], cutoff)}
    # 19. Income and saving
    inc: dict[str, Any] = {}
    for tag, key, name in (("disp_income", c["disp_income"], "Real disposable income"),
                           ("ex_transfers", c["income_ex_transfers"],
                            "Real personal income ex transfers")):
        s = monthly(st, key, cutoff)
        if s:
            M = max(s)
            inc[tag] = {"key": key, "name": name, "month": M, "yoy_pct": r(yoy(s, M), 2),
                        "ann_3m_pct": r(annualised(s, M, 3), 2),
                        "lens": lens_stat(key, history(s, _yoy), cutoff)}
        else:
            inc[tag] = {"key": key, "name": name, "month": None, "reason": not_stored(key),
                        "lens": lens_stat(key, [], cutoff)}
    sv = level_row(st, c["saving_rate"], "The saving rate", cutoff)
    if sv.get("month"):
        s = monthly(st, c["saving_rate"], cutoff)
        sv["change_12m_pp"] = (r(s[sv["month"]] - s[shift(sv["month"], -12)], 2)
                               if shift(sv["month"], -12) in s else None)
    inc["saving_rate"] = sv
    inc["k_shape_gap"] = c["k_shape_gap"]
    out["income"] = inc
    # 20. The nowcast path
    out["nowcast"] = nowcast_path(st, cutoff, c["gdpnow"], c["real_growth"])
    out["nowcast"]["nyfed_gap"] = c["nyfed_gap"]
    return out


# ---------------------------------------------------------------------------
# THE LENS CELLS -- one format for every panel row's form
# ---------------------------------------------------------------------------
LENS_COLUMNS = ["5-year percentile (n)", "Long percentile (window, n)",
                "Percentiles disagree"]


def lens_cells(lens: dict) -> list[str]:
    """The three form cells of a row: each percentile with its n, the long one
    with its window, and the 30-point disagreement ("yes", "no", or the dash)."""
    def one(p, n, w=None):
        if p is None:
            return "—"
        return f"{derived._ord(p)} ({w + ', ' if w else ''}n={n})"
    d = lens.get("disagree")
    return [one(lens.get("pctile_5y"), lens.get("pctile_5y_n")),
            one(lens.get("pctile_long"), lens.get("pctile_long_n"),
                lens.get("pctile_long_window")),
            "yes" if d is True else ("no" if d is False else "—")]


# ---------------------------------------------------------------------------
# LENS 24 -- THE RELEASE-DAY LINES FOR PPI AND GDP
# ---------------------------------------------------------------------------
def _s(x: Optional[float], dp: int = 1, unit: str = "") -> str:
    return "n/a" if x is None else f"{x:+.{dp}f}{unit}"


def _pctile(lens: dict) -> str:
    p = lens.get("pctile_long")
    return "" if p is None else f", {derived._ord(p)} percentile of its history"


def ppi_line(pp: dict, surprise: str) -> str:
    fd, tr, co = pp["final_demand"], pp["trade_services"], pp["core_ex_trade"]
    st4 = next((x for x in pp["pipeline"] if x["key"].endswith("stage4")), {})
    bits = [f"less foods, energy and trade {_s(co.get('mm_pct'), 1, '%')} "
            f"({_s(co.get('yoy_pct'), 1, '%')} on the year)",
            f"trade services {_s(tr.get('mm_pct'), 1, '%')}"]
    if st4.get("month"):
        bits.append(f"stage 4 intermediate demand {_s(st4.get('yoy_pct'), 1, '%')} on "
                    f"the year ({_s(st4.get('gap_to_final_pp'), 1, ' pp')} against final "
                    f"demand)")
    return (f"PPI for {month_name(fd.get('month'))}: final demand "
            f"{_s(fd.get('mm_pct'), 1, '%')} on the month ({_s(fd.get('yoy_pct'), 1, '%')} "
            f"on the year{_pctile(fd.get('lens') or {})}); what moved it: "
            f"{'; '.join(bits)} ({surprise}).")


def gdp_line(gd: dict, surprise: str) -> str:
    core = gd["core"]
    gr, fs = core["real_growth"], core["final_sales"]
    named = "; ".join(f"{x['name'].split(' (')[0].lower()} {_s(x['value'], 2, ' pp')}"
                      for x in core["contributions"] if x.get("value") is not None)
    nc = gd.get("nowcast") or {}
    tail = ""
    pr = nc.get("print")
    if pr and pr["quarter"] == core.get("quarter"):
        tail = (f"; against GDPNow's last {_s(pr['last_nowcast'], 1, '%')}, "
                f"{_s(pr['miss_pp'], 1, ' pp')}")
    return (f"GDP for {quarter_name(core.get('quarter'))}: {_s(gr.get('value'), 1, '%')} "
            f"annualised{_pctile(gr.get('lens') or {})}; final sales to private domestic "
            f"purchasers {_s(fs.get('qq_ann_pct'), 1, '%')}; what moved it: {named}"
            f"{tail} ({surprise}).")


def _main(argv: list[str]) -> int:
    """`show`: lenses 12-20 as of the cutoff, as JSON. Reads only."""
    import argparse
    import json

    from . import session
    ap = argparse.ArgumentParser(prog="python -m altdata.releases_b")
    ap.add_argument("cmd", choices=["show"])
    ap.add_argument("--as-of", default=None)
    ap.add_argument("--db", default=None)
    a = ap.parse_args(argv)
    cutoff = a.as_of or session.utc_iso(timespec="microseconds")
    with observations.ObservationStore(a.db) as st:
        out = {"as_of": cutoff, "ppi_lenses": ppi_lenses(st, cutoff),
               "gdp_lenses": gdp_lenses(st, cutoff)}
    print(json.dumps(out, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(_main(sys.argv[1:]))
