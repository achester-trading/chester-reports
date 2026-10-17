"""
THE RELEASE LENSES (Batch 7 items 46 and 48, Group A, with the cross-cutting
lenses 21-24; docs/change-order-signal-triage-batch-7-2026-10-16.md on
docs-batch-7; 6e-releases, 16 Oct 2026, session B). Config: config/releases.yaml.

Everything is read from the observation store AS OF the cutoff, so every figure
and every flag is the one the vintages knowable then support (lens 22). Nothing is
written: these are report panels, recomputed at render time from stored series.

  decomposition(st, cutoff)   item 46a: the five contributions to the month's
                              CPI, the Cleveland Fed median and trimmed mean, and
                              the diffusion (the share of 24 categories above 4%
                              annualised month on month)
  pass_through(st, cutoff)    item 46b: the energy spike, the basket's
                              acceleration, the flag
  item32_state(...)           the printed state the flag switches (ruling (d))
  employment(st, cutoff)      item 48 lenses 1-6, with the flags of lenses 2-4
  cpi_lenses(st, cutoff)      item 48 lenses 7-11
  release_day_lines(st, cutoff)  lens 24: one "what moved the print" line per
                              release whose print arrived on the cutoff's ET day

    python -m altdata.releases show [--as-of ISO] [--db PATH]   # read-only

RIGHTS. Flags only where the order names them: lens 2 (diffusion under 50 for
three months), lens 3 (persistent negative revisions), lens 4 (permanent job
losers rising year over year) and item 46's pass-through flag. Each flag is
True, False or None; None carries `withheld` with the reason -- THE VINTAGE RULE:
a flag that needs a print not yet published at the cutoff is withheld, never
evaluated on what happens to be there (lens 22).

No figure here is a market-state input (R28). trigger_eligible false throughout.
"""

from __future__ import annotations

import datetime as dt
import statistics
from pathlib import Path
from typing import Any, Optional

import yaml

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / "config" / "releases.yaml"


def config(path: Optional[Path] = None) -> dict:
    return yaml.safe_load((path or CONFIG).read_text(encoding="utf-8")) or {}


# ---------------------------------------------------------------------------
# Months and series
# ---------------------------------------------------------------------------
def shift(month: str, n: int) -> str:
    y, m = divmod(int(month[:4]) * 12 + int(month[5:7]) - 1 + n, 12)
    return f"{y:04d}-{m + 1:02d}"


def month_name(month: Optional[str]) -> str:
    if not month:
        return "n/a"
    return dt.date(int(month[:4]), int(month[5:7]), 1).strftime("%b %Y")


def monthly(st, key: str, cutoff: str) -> dict[str, float]:
    """{YYYY-MM: value} of every period knowable at the cutoff."""
    return {str(r["observed_at"])[:7]: float(r["value_num"])
            for r in st.as_of(key, cutoff) if r.get("value_num") is not None}


def dated(st, key: str, cutoff: str) -> list[tuple[str, float, str]]:
    """[(observed_at, value, available_at)] knowable at the cutoff, in order."""
    return [(str(r["observed_at"])[:10], float(r["value_num"]), str(r["available_at"]))
            for r in st.as_of(key, cutoff) if r.get("value_num") is not None]


def mm(s: dict[str, float], month: str) -> Optional[float]:
    """Month-on-month change, percent."""
    a, b = s.get(month), s.get(shift(month, -1))
    return None if a is None or not b else 100.0 * (a / b - 1.0)


def annualised(s: dict[str, float], month: str, n: int) -> Optional[float]:
    """The n-month change, compounded to an annual rate, percent."""
    a, b = s.get(month), s.get(shift(month, -n))
    return None if a is None or not b or a <= 0 or b <= 0 else \
        100.0 * ((a / b) ** (12.0 / n) - 1.0)


def yoy(s: dict[str, float], month: str) -> Optional[float]:
    return annualised(s, month, 12)


def ann_mm(x: Optional[float]) -> Optional[float]:
    """A month-on-month percent change, annualised."""
    return None if x is None else 100.0 * ((1.0 + x / 100.0) ** 12 - 1.0)


def chain(changes: dict[str, float], base: float = 100.0) -> dict[str, float]:
    """An index from month-on-month percent changes, over the longest unbroken
    run of months ending at the latest."""
    if not changes:
        return {}
    ms = sorted(changes)
    run = [ms[-1]]
    for m in reversed(ms[:-1]):
        if shift(m, 1) != run[-1]:
            break
        run.append(m)
    run.reverse()
    out = {shift(run[0], -1): base}
    v = base
    for m in run:
        v *= 1.0 + changes[m] / 100.0
        out[m] = v
    return out


def r(x: Optional[float], dp: int = 3) -> Optional[float]:
    return None if x is None else round(float(x), dp)


def not_published(what: str, month: str) -> str:
    return f"{what} for {month_name(month)} is not published at the cutoff"


# ---------------------------------------------------------------------------
# ITEM 46a -- THE DECOMPOSITION
# ---------------------------------------------------------------------------
def supercore(st, cutoff: str, cfg: Optional[dict] = None) -> dict[str, float]:
    """Core services ex shelter as an index, chained from its month-on-month
    change: (w_cs x core services m/m - w_sh x shelter m/m) / (w_cs - w_sh)."""
    c = (cfg or config())["decomposition"]["supercore"]
    cs, sh = monthly(st, c["core_services"], cutoff), monthly(st, c["shelter"], cutoff)
    wcs, wsh = float(c["core_services_weight"]), float(c["shelter_weight"])
    ch = {}
    for m in cs:
        a, b = mm(cs, m), mm(sh, m)
        if a is not None and b is not None:
            ch[m] = (wcs * a - wsh * b) / (wcs - wsh)
    return chain(ch)


def decomposition(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    d = cfg["decomposition"]
    head = monthly(st, d["headline"], cutoff)
    if not head:
        return {"state": "absent", "reason": "CPI is not stored"}
    M = max(head)
    sc = supercore(st, cutoff, cfg)
    pieces, total = [], 0.0
    for p in d["pieces"]:
        s = sc if p["key"] == "supercore" else monthly(st, p["key"], cutoff)
        x = mm(s, M)
        c = None if x is None else float(p["weight"]) * x
        pieces.append({"name": p["name"], "weight": p["weight"], "mm_pct": r(x),
                       "contribution_pp": r(c),
                       "reason": None if x is not None else
                       not_published(p["name"], M)})
        total += c or 0.0
    h = mm(head, M)
    complete = all(p["contribution_pp"] is not None for p in pieces)
    core = monthly(st, d["core"], cutoff)
    out = {"state": "read", "month": M, "headline_mm_pct": r(h),
           "headline_yoy_pct": r(yoy(head, M)), "core_mm_pct": r(mm(core, M)),
           "core_yoy_pct": r(yoy(core, M)), "pieces": pieces,
           "sum_pp": r(total) if complete else None,
           "residual_pp": r(h - total) if complete and h is not None else None}
    for name in ("median", "trimmed_mean"):
        s = monthly(st, d[name], cutoff)
        if M in s:
            avg3 = [s.get(shift(M, -i)) for i in range(3)]
            out[name] = {"month": M, "ann_pct": r(s[M], 2),
                         "avg_3m_ann_pct": (r(statistics.fmean(avg3), 2)
                                            if None not in avg3 else None)}
        else:
            out[name] = {"month": M, "ann_pct": None,
                         "reason": not_published(f"the Cleveland Fed {name.replace('_', ' ')}", M)}
    out["diffusion"] = diffusion(st, cutoff, M, cfg)
    return out


def diffusion(st, cutoff: str, month: str, cfg: Optional[dict] = None) -> dict:
    c = (cfg or config())["diffusion"]
    th = float(c["threshold_annualised_pct"])
    hot, n, absent = [], 0, []
    for k in c["categories"]:
        a = ann_mm(mm(monthly(st, k, cutoff), month))
        if a is None:
            absent.append(k)
            continue
        n += 1
        if a > th:
            hot.append(k)
    out = {"month": month, "n": n, "of": len(c["categories"]), "hot": len(hot),
           "threshold_pct": th, "absent": absent}
    if n < int(c.get("min_categories", 1)):
        out["share_pct"] = None
        out["reason"] = (f"{n} of {len(c['categories'])} categories printed for "
                         f"{month_name(month)}; {c.get('min_categories')} needed")
    else:
        out["share_pct"] = round(100.0 * len(hot) / n, 1)
    return out


# ---------------------------------------------------------------------------
# ITEM 46b -- THE PASS-THROUGH BASKET AND FLAG
# ---------------------------------------------------------------------------
def basket_index(st, cutoff: str, cfg: Optional[dict] = None) -> tuple[dict, dict]:
    """(the basket's chained index over months all three legs printed; each
    leg's latest month). Equal weights: the mean of the legs' m/m."""
    c = (cfg or config())["pass_through"]
    legs = {k: monthly(st, k, cutoff) for k in c["basket"]}
    months_ = set.intersection(*(set(s) for s in legs.values())) if legs else set()
    ch = {}
    for m in months_:
        xs = [mm(s, m) for s in legs.values()]
        if None not in xs:
            ch[m] = statistics.fmean(xs)
    return chain(ch), {k: (max(s) if s else None) for k, s in legs.items()}


LEG_NAMES = {"fred.cpi_airline_fares": "airline fares",
             "fred.cpi_transport_services": "transportation services",
             "fred.ppi_truck_freight": "the truck-freight PPI"}


def pass_through(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    c = cfg["pass_through"]
    energy = monthly(st, c["energy"], cutoff)
    if not energy:
        return {"state": "absent", "flag": None, "reason": "CPI energy is not stored"}
    E = max(energy)
    lo, hi = (int(x) for x in c["window_months"])
    spike_at = float(c["energy_spike_mm_pct"])
    need = float(c["acceleration_pp"])
    spikes = [m for m in (shift(E, -i) for i in range(0, hi + 1))
              if (mm(energy, m) or 0.0) >= spike_at]
    idx, last_leg = basket_index(st, cutoff, cfg)
    acc = lambda m: annualised(idx, m, 3)                        # noqa: E731
    out = {"state": "read", "month": E, "energy_mm_pct": r(mm(energy, E)),
           "spike_threshold_pct": spike_at, "acceleration_threshold_pp": need,
           "spikes": [{"month": s, "energy_mm_pct": r(mm(energy, s))} for s in spikes],
           "basket_3m_ann_pct": r(acc(E)), "legs_latest": last_leg,
           "flag": False, "withheld": None, "fired": None}
    if not spikes:
        out["reason"] = (f"no energy spike (CPI energy up {spike_at:.1f}% or more in a "
                         f"month) in the {hi} months to {month_name(E)}")
        return out
    unevaluable, evaluated = [], 0
    for s in sorted(spikes):
        base = acc(s)
        for k in range(lo, hi + 1):
            m = shift(s, k)
            if m > E:
                break
            now = acc(m)
            evaluated += 1
            if base is None or now is None:
                missing = [LEG_NAMES.get(lk, lk) for lk, lm in last_leg.items()
                           if lm is None or lm < m]
                unevaluable.append((m, missing))
                continue
            if now - base >= need:
                out["flag"] = True
                out["fired"] = {"spike": s, "month": m, "basket_3m_ann_pct": r(now),
                                "at_spike_pct": r(base), "acceleration_pp": r(now - base)}
                return out
    if unevaluable:
        m, missing = unevaluable[-1]
        out["flag"] = None
        out["withheld"] = (
            f"the basket for {month_name(m)} is not complete at the cutoff "
            f"({', '.join(missing) or 'a leg'} not yet published): the flag waits for "
            f"that vintage rather than reading the legs that are in")
        return out
    out["reason"] = (f"the basket has not accelerated {need:.1f} points within "
                     f"{hi} months of the spike" if evaluated else
                     f"the spike is {month_name(E)}'s own: the basket's window is the "
                     f"{lo} to {hi} months after it")
    return out


def item32_state(supply_shock: Optional[bool], pt: dict,
                 cfg: Optional[dict] = None) -> Optional[str]:
    """Item 32's printed state with item 46's switch (ruling (d), 16 Oct 2026):
    while item 32 reads a supply shock, "contained" until the pass-through flag
    fires, "propagating" after. None when item 32 reads no supply shock (its own
    line stands) or has no read."""
    st = (cfg or config())["pass_through"]["states"]
    if not supply_shock:
        return None
    return st["propagating"] if pt.get("flag") is True else st["contained"]


def item32_read(st, cutoff: str) -> dict:
    """Item 32's classifier where it is on the branch (session A's st-r5-t1-rest,
    altdata/st_r5_t1_rest.py oil_shock), else its absence and why."""
    try:
        from . import st_r5_t1_rest as t1                       # noqa: PLC0415
    except ImportError:
        return {"state": "absent", "supply_shock": None,
                "reason": "item 32's classifier (st-r5-t1-rest) is not on this branch; "
                          "the switch attaches when the two are stitched"}
    try:
        o = t1.oil_shock(st, cutoff)
    except Exception as exc:                                    # noqa: BLE001
        return {"state": "absent", "supply_shock": None,
                "reason": f"item 32's classifier faulted ({type(exc).__name__})"}
    if o.get("state") != "read":
        return {"state": "absent", "supply_shock": None, "reason": o.get("reason")}
    return {"state": "read", "supply_shock": bool(o.get("supply_shock")), "day": o.get("day")}


# ---------------------------------------------------------------------------
# ITEM 48, LENSES 1-6 -- EMPLOYMENT
# ---------------------------------------------------------------------------
def _vintage_value(rows: list[dict], month: str, instant: str) -> Optional[float]:
    """The value of `month` in the latest vintage at or before `instant`."""
    best = None
    for x in rows:
        if str(x["observed_at"])[:7] == month and str(x["available_at"]) <= instant:
            best = x
    return None if best is None else best.get("value_num")


def net_revisions(st, key: str, cutoff: str) -> list[dict]:
    """The two-month net revision at each release knowable at the cutoff: the
    change over the two months before the release's newest month, as this
    release prints it, less as the previous vintage printed it."""
    from .observations import canonical_instant                 # noqa: PLC0415
    cut = canonical_instant(cutoff)
    rows = [x for x in st.all_vintages(key) if str(x["available_at"]) <= cut
            and x.get("value_num") is not None]
    rows.sort(key=lambda x: str(x["available_at"]))
    first: dict[str, str] = {}
    for x in rows:
        first.setdefault(str(x["observed_at"])[:7], str(x["available_at"]))
    out = []
    for t, inst in sorted(first.items()):
        prior = [str(x["available_at"]) for x in rows if str(x["available_at"]) < inst]
        if not prior:
            continue
        before = max(prior)
        a, b = shift(t, -1), shift(t, -3)
        new = [_vintage_value(rows, a, inst), _vintage_value(rows, b, inst)]
        old = [_vintage_value(rows, a, before), _vintage_value(rows, b, before)]
        if None in new or None in old:
            continue
        out.append({"month": t, "released": inst[:10],
                    "net_revision": r((new[0] - new[1]) - (old[0] - old[1]), 1)})
    return out


def _avg(s: dict[str, float], month: str, n: int) -> Optional[float]:
    xs = [s.get(shift(month, -i)) for i in range(n)]
    return None if None in xs else statistics.fmean(xs)


def _weekly_avg(pts: list[tuple[str, float, str]], end: int, n: int = 4) -> Optional[float]:
    xs = [v for _, v, _ in pts[max(0, end - n + 1): end + 1]]
    return statistics.fmean(xs) if len(xs) == n else None


def employment(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    e = cfg["employment"]
    out: dict[str, Any] = {}
    # 1. Cyclical core payrolls
    nfp, prv, eh = (monthly(st, e[k], cutoff) for k in ("payrolls", "private", "edu_health"))
    core = {m: prv[m] - eh[m] for m in prv if m in eh}
    ch = lambda s, m: (s[m] - s[shift(m, -1)]) if m in s and shift(m, -1) in s else None  # noqa: E731
    H = max(nfp) if nfp else None
    out["cyclical"] = {"headline_month": H,
                       "headline_change_k": r(ch(nfp, H), 1) if H else None}
    if core:
        M = max(core)
        c3 = [ch(core, shift(M, -i)) for i in range(3)]
        out["cyclical"].update(
            month=M, core_change_k=r(ch(core, M), 1),
            core_3m_avg_k=r(statistics.fmean(c3), 1) if None not in c3 else None,
            headline_change_k=r(ch(nfp, M), 1) if M in nfp else
            out["cyclical"]["headline_change_k"])
    else:
        out["cyclical"].update(month=None, reason="private or education-and-health "
                                                  "payrolls are not stored")
    # 2. Diffusion, with its flag
    d1, d3 = monthly(st, e["diffusion_1m"], cutoff), monthly(st, e["diffusion_3m"], cutoff)
    n_months, below = int(e["diffusion_flag_months"]), float(e["diffusion_flag_below"])
    dif: dict[str, Any] = {"source": "FRED State and Metro: the share of states adding "
                                     "jobs (the CES industry indexes are a gap)",
                           "threshold": below, "months_needed": n_months}
    if d1:
        M = max(d1)
        run = [d1.get(shift(M, -i)) for i in range(n_months)]
        dif.update({"month": M, "one_month": r(d1[M], 1), "three_month": r(d3.get(M), 1)})
        if None in run:
            gap = [shift(M, -i) for i, v in enumerate(run) if v is None]
            dif.update(flag=None, withheld=f"needs {n_months} consecutive months; "
                       f"{', '.join(month_name(g) for g in gap)} not stored at the cutoff")
        else:
            dif.update(flag=all(v < below for v in run), run=[r(v, 1) for v in run])
    else:
        dif.update(month=None, flag=None, withheld="the diffusion index is not stored")
    out["diffusion"] = dif
    # 3. Revisions, with the flag
    revs = net_revisions(st, e["payrolls"], cutoff)
    k = int(e["revision_flag_releases"])
    rv: dict[str, Any] = {"releases": revs[-6:], "releases_needed": k,
                          "birth_death": "a listed gap: the BLS publishes it on "
                                         "www.bls.gov, which refuses a client that "
                                         "will not send a personal contact"}
    if len(revs) < k:
        rv.update(flag=None, withheld=f"{len(revs)} release(s) with a prior vintage at "
                                      f"the cutoff; {k} needed (the vintages come from "
                                      f"ALFRED's backfill and each later pull)")
    else:
        rv["flag"] = all(x["net_revision"] < 0 for x in revs[-k:])
    out["revisions"] = rv
    # 4. Unemployment by flow
    pl = monthly(st, e["permanent_losers"], cutoff)
    fl: dict[str, Any] = {"threshold_pct": float(e["permanent_losers_yoy_rise_pct"])}
    if pl:
        M = max(pl)
        now, then = _avg(pl, M, 3), _avg(pl, shift(M, -12), 3)
        fl["month"] = M
        if now is None or not then:
            fl.update(flag=None, withheld="needs the three latest months and the same "
                                          "three a year earlier; not all stored at the cutoff")
        else:
            rise = 100.0 * (now / then - 1.0)
            fl.update(level_3m_avg_k=r(now, 1), year_earlier_k=r(then, 1),
                      yoy_pct=r(rise, 2), flag=rise >= fl["threshold_pct"])
    else:
        fl.update(month=None, flag=None, withheld="permanent job losers are not stored")
    out["permanent_losers"] = fl
    lf = monthly(st, e["lfpr_prime_age"], cutoff)
    if lf:
        M = max(lf)
        out["lfpr_prime_age"] = {"month": M, "level_pct": r(lf[M], 1),
                                 "change_12m_pp": r(lf[M] - lf[shift(M, -12)], 1)
                                 if shift(M, -12) in lf else None}
    sahm = monthly(st, e["sahm"], cutoff)
    if sahm:
        M = max(sahm)
        out["sahm"] = {"month": M, "value_pp": r(sahm[M], 2)}
    ini, con = dated(st, e["claims_initial"], cutoff), dated(st, e["claims_continuing"], cutoff)
    w = int(e["claims_weeks"])
    if len(ini) > w + 4 and len(con) > w + 4:
        ci = (_weekly_avg(ini, len(ini) - 1), _weekly_avg(ini, len(ini) - 1 - w))
        cc = (_weekly_avg(con, len(con) - 1), _weekly_avg(con, len(con) - 1 - w))
        ich, cch = 100.0 * (ci[0] / ci[1] - 1.0), 100.0 * (cc[0] / cc[1] - 1.0)
        freeze = cch >= float(e["claims_rising_pct"]) and abs(ich) <= float(e["claims_flat_pct"])
        out["claims"] = {"initial_week": ini[-1][0], "continuing_week": con[-1][0],
                         "initial_4wk": r(ci[0], 0), "continuing_4wk": r(cc[0], 0),
                         "initial_change_pct": r(ich, 1), "continuing_change_pct": r(cch, 1),
                         "weeks": w, "hiring_freeze_read": freeze}
    else:
        out["claims"] = {"reason": f"fewer than {w + 5} weeks of initial and continuing "
                                   f"claims stored"}
    # 5. Leading pieces
    th, hrs = monthly(st, e["temp_help"], cutoff), monthly(st, e["agg_hours"], cutoff)
    qr = monthly(st, e["quits_rate"], cutoff)
    op, un = monthly(st, e["openings"], cutoff), monthly(st, e["unemployed"], cutoff)
    lead: dict[str, Any] = {}
    if th:
        M = max(th)
        lead["temp_help"] = {"month": M, "change_3m_k": r(th[M] - th[shift(M, -3)], 1)
                             if shift(M, -3) in th else None,
                             "yoy_pct": r(yoy(th, M), 1)}
    if hrs:
        M = max(hrs)
        lead["agg_hours"] = {"month": M, "ann_3m_pct": r(annualised(hrs, M, 3), 1),
                             "yoy_pct": r(yoy(hrs, M), 1)}
    if qr:
        M = max(qr)
        lead["quits_rate"] = {"month": M, "level_pct": r(qr[M], 1),
                              "change_12m_pp": r(qr[M] - qr[shift(M, -12)], 1)
                              if shift(M, -12) in qr else None}
    if op and un:
        both = sorted(set(op) & set(un))
        if both:
            M = both[-1]
            lead["openings_per_unemployed"] = {"month": M, "ratio": r(op[M] / un[M], 2)}
    out["leading"] = lead
    # 6. Wages
    eci, atl = monthly(st, e["eci"], cutoff), monthly(st, e["atl_wage"], cutoff)
    ahe = monthly(st, e["ahe"], cutoff)
    sw, sy = monthly(st, e["switchers"], cutoff), monthly(st, e["stayers"], cutoff)
    wg: dict[str, Any] = {}
    if eci:
        M = max(eci)
        wg["eci"] = {"quarter_month": M, "yoy_pct": r(yoy(eci, M), 1)}
    if atl:
        M = max(atl)
        wg["atlanta"] = {"month": M, "pct": r(atl[M], 1)}
    if ahe:
        M = max(ahe)
        wg["ahe"] = {"month": M, "yoy_pct": r(yoy(ahe, M), 1),
                     "ann_3m_pct": r(annualised(ahe, M, 3), 1)}
    both = sorted(set(sw) & set(sy))
    if both:
        M = both[-1]
        wg["switcher_premium"] = {"month": M, "switchers_pct": r(sw[M], 1),
                                  "stayers_pct": r(sy[M], 1),
                                  "premium_pp": r(sw[M] - sy[M], 1)}
    out["wages"] = wg
    out["flags"] = {"diffusion": dif.get("flag"), "revisions": rv.get("flag"),
                    "permanent_losers": fl.get("flag")}
    return out


# ---------------------------------------------------------------------------
# ITEM 48, LENSES 7-11 -- CPI
# ---------------------------------------------------------------------------
def ladder(s: dict[str, float], n: int = 3) -> Optional[dict]:
    """Lens 10: year over year for each of the next n months if month on month
    runs at the trailing three-month average, given the months dropping out."""
    if not s:
        return None
    M = max(s)
    pace = [mm(s, shift(M, -i)) for i in range(3)]
    if None in pace or yoy(s, M) is None:
        return None
    g = statistics.fmean(pace)
    rungs = []
    for k in range(1, n + 1):
        base = s.get(shift(M, k - 12))
        if not base:
            break
        rungs.append({"month": shift(M, k),
                      "drops_out_mm_pct": r(mm(s, shift(M, k - 12))),
                      "yoy_pct": r(100.0 * (s[M] * (1.0 + g / 100.0) ** k / base - 1.0))})
    return {"month": M, "yoy_now_pct": r(yoy(s, M)), "pace_mm_pct": r(g), "rungs": rungs}


def cpi_lenses(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    c = cfg["cpi_lenses"]
    out: dict[str, Any] = {}
    # 7. The shelter lead
    lag = int(c["shelter_lead_months"])
    leads = []
    for x in c["shelter_leads"]:
        s = monthly(st, x["key"], cutoff)
        if not s:
            leads.append({"name": x["name"], "key": x["key"], "month": None,
                          "reason": f"{x['name']} is not stored"})
            continue
        M = max(s)
        leads.append({"name": x["name"], "key": x["key"], "month": M,
                      "yoy_pct": r(yoy(s, M), 1),
                      "yoy_lag_ago_pct": r(yoy(s, shift(M, -lag)), 1)})
    cpi_sh = []
    for k in c["shelter_cpi"]:
        s = monthly(st, k, cutoff)
        if s:
            M = max(s)
            cpi_sh.append({"key": k, "month": M, "yoy_pct": r(yoy(s, M), 1)})
    out["shelter_lead"] = {"lag_months": lag, "leads": leads, "cpi": cpi_sh,
                           "gap": "the BLS new-tenant rent index: a listed gap (its "
                                  "files are on www.bls.gov, which refuses a client "
                                  "that will not send a personal contact)"}
    # 8. Supercore
    sc = supercore(st, cutoff, cfg)
    if sc:
        M = max(sc)
        out["supercore"] = {"month": M, "ann_3m_pct": r(annualised(sc, M, 3), 2),
                            "ann_6m_pct": r(annualised(sc, M, 6), 2),
                            "yoy_pct": r(yoy(sc, M), 2), "mm_pct": r(mm(sc, M))}
    # 9. Sticky against flexible; goods against services
    for name in ("sticky", "flexible"):
        s = monthly(st, c[name], cutoff)
        if s:
            M = max(s)
            out[name] = {"month": M, "ann_pct": r(s[M], 2),
                         "avg_3m_pct": r(_avg(s, M, 3), 2)}
    for name in ("goods", "services"):
        s = monthly(st, c[name], cutoff)
        if s:
            M = max(s)
            out[name] = {"month": M, "yoy_pct": r(yoy(s, M), 2),
                         "ann_3m_pct": r(annualised(s, M, 3), 2)}
    # 10. The base-effect ladder
    out["ladder"] = {}
    for k in c["ladder_series"]:
        lad = ladder(monthly(st, k, cutoff), int(c["ladder_months"]))
        if lad:
            out["ladder"][k] = lad
    # 11. The CPI-PCE wedge
    wg = monthly(st, c["wedge"], cutoff)
    out["wedge"] = {"month": max(wg) if wg else None,
                    "gap_pp": r(wg[max(wg)], 2) if wg else None,
                    "weights": c.get("wedge_weights") or []}
    return out


# ---------------------------------------------------------------------------
# LENS 24 -- THE RELEASE-DAY LINES
# ---------------------------------------------------------------------------
def et_date(instant: str) -> str:
    from zoneinfo import ZoneInfo                               # noqa: PLC0415
    t = dt.datetime.fromisoformat(str(instant).replace("Z", "+00:00"))
    if t.tzinfo is None:
        t = t.replace(tzinfo=dt.timezone.utc)
    return t.astimezone(ZoneInfo("America/New_York")).date().isoformat()


def released_today(st, key: str, cutoff: str) -> Optional[str]:
    """The month whose first print of `key` arrived on the cutoff's ET date."""
    rows = st.as_of(key, cutoff)
    if not rows:
        return None
    newest = rows[-1]
    first = (st.vintages(key, newest["observed_at"]) or [{}])[0].get("available_at")
    if first and et_date(first) == et_date(cutoff):
        return str(newest["observed_at"])[:7]
    return None


def _s(x: Optional[float], dp: int = 1, unit: str = "") -> str:
    return "n/a" if x is None else f"{x:+.{dp}f}{unit}"


def consensus_note() -> str:
    from . import derived                                       # noqa: PLC0415
    sc = derived.lens_config().get("surprise") or {}
    return f"surprise: {sc.get('state', 'no consensus')}"


def cpi_line(dc: dict, pt: dict) -> str:
    p = {x["name"]: x for x in dc["pieces"]}
    parts = "; ".join(f"{n} {_s(p[n]['contribution_pp'], 2)} pp" for n in
                      ("energy", "food", "core goods", "shelter", "core services ex shelter")
                      if n in p and p[n]["contribution_pp"] is not None)
    med, dif = dc.get("median") or {}, dc.get("diffusion") or {}
    tail = []
    if med.get("ann_pct") is not None:
        tail.append(f"median CPI {med['ann_pct']:.1f}% annualised")
    if dif.get("share_pct") is not None:
        tail.append(f"{dif['share_pct']:.0f}% of {dif['n']} categories above "
                    f"{dif['threshold_pct']:.0f}% annualised")
    if pt.get("flag") is True:
        tail.append("the pass-through basket has accelerated since the energy spike")
    elif pt.get("spikes"):
        tail.append("an energy spike, the pass-through basket not yet accelerating"
                    if pt.get("flag") is False else "the pass-through flag waits on a vintage")
    t = "; ".join(tail)
    t = f". {t[0].upper()}{t[1:]}" if t else ""
    return (f"CPI for {month_name(dc['month'])}: {_s(dc['headline_mm_pct'], 1, '%')} on the "
            f"month ({_s(dc['headline_yoy_pct'], 1, '%')} on the year); what moved it: "
            f"{parts}{t} ({consensus_note()}).")


def employment_line(em: dict, month: str) -> str:
    cy, rv, dif = em.get("cyclical") or {}, em.get("revisions") or {}, em.get("diffusion") or {}
    bits = [f"payrolls {_s(cy.get('headline_change_k'), 0, 'k')}",
            f"cyclical core {_s(cy.get('core_change_k'), 0, 'k')}"]
    if rv.get("releases"):
        bits.append(f"two-month net revision {_s(rv['releases'][-1]['net_revision'], 0, 'k')}")
    if dif.get("one_month") is not None:
        bits.append(f"{dif['one_month']:.0f}% of states adding jobs")
    flags = [n for n, v in (em.get("flags") or {}).items() if v is True]
    tail = f"; flag{'s' if len(flags) > 1 else ''}: {', '.join(flags)}" if flags else ""
    return (f"The employment report for {month_name(month)}: {'; '.join(bits)}{tail} "
            f"({consensus_note()}).")


def release_day_lines(st, cutoff: str, cfg: Optional[dict] = None) -> list[dict]:
    """Lens 24: one line per release whose print arrived on the cutoff's ET day,
    code-written from the release's own lens figures (no model call)."""
    cfg = cfg or config()
    out = []
    for rel in cfg.get("releases") or []:
        month = released_today(st, rel["headline"], cutoff)
        if not month:
            continue
        if rel["id"] == "cpi":
            dc = decomposition(st, cutoff, cfg)
            if dc.get("state") != "read":
                continue
            line = cpi_line(dc, pass_through(st, cutoff, cfg))
        elif rel["id"] == "employment":
            line = employment_line(employment(st, cutoff, cfg), month)
        elif rel["id"] == "jolts":
            le = employment(st, cutoff, cfg)["leading"]
            q, o = le.get("quits_rate") or {}, le.get("openings_per_unemployed") or {}
            line = (f"JOLTS for {month_name(month)}: quits rate "
                    f"{q.get('level_pct', 'n/a')}% ({_s(q.get('change_12m_pp'), 1, ' pp')} "
                    f"on the year); openings per unemployed {o.get('ratio', 'n/a')} "
                    f"({consensus_note()}).")
        else:
            wg = employment(st, cutoff, cfg)["wages"]
            e = wg.get("eci") or {}
            line = (f"The employment cost index (wages and salaries, private) for the "
                    f"quarter to {month_name(month)}: {_s(e.get('yoy_pct'), 1, '%')} on "
                    f"the year ({consensus_note()}).")
        out.append({"release": rel["id"], "name": rel["name"], "month": month,
                    "line": line})
    return out


def _main(argv: list[str]) -> int:
    """`show`: every lens as of the cutoff, as JSON. Opens the store read-only in
    effect (it only reads) and writes nothing."""
    import argparse
    import json

    from . import observations, session
    ap = argparse.ArgumentParser(prog="python -m altdata.releases")
    ap.add_argument("cmd", choices=["show"])
    ap.add_argument("--as-of", default=None)
    ap.add_argument("--db", default=None)
    a = ap.parse_args(argv)
    cutoff = a.as_of or session.utc_iso(timespec="microseconds")
    with observations.ObservationStore(a.db) as st:
        out = {"as_of": cutoff, "decomposition": decomposition(st, cutoff),
               "pass_through": pass_through(st, cutoff),
               "item32": item32_read(st, cutoff), "employment": employment(st, cutoff),
               "cpi_lenses": cpi_lenses(st, cutoff),
               "release_day_lines": release_day_lines(st, cutoff)}
    print(json.dumps(out, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(_main(sys.argv[1:]))
