"""
Batch 5 Tranche 1, part 1 (signal-triage round 4, part 2; filed 9 Oct 2026):
items 17, 21, 23, 24 and 26, built on the 10-year attribution first (cross-item
ruling 1). Config: config/batch5_tranche_1.yaml. Printed by
daily_cascade/batch5_block.py. Nothing here fetches, and nothing is a state.

    ST-R4.21b  term_premium   ACM's 10-year term premium, dual percentiles with
                              their real window and n
    ST-R4.26a  fiscal_bark    the term premium's share of the six-month move, and
                              term premium up with the expected short rate down
    ST-R4.24a  stock_bond     SR-9's 60-day correlation beside a 2-year window of
    ST-R4.24b                 weekly changes; the flag conditioned on the
                              attribution (strongest when breakeven-led)
    ST-R4.17a  net_liquidity  calc.net_liquidity's 4- and 13-week changes and
                              the component attribution
    ST-R4.21a  (batch3.py)    Greece-Bund beside OAT-Bund, untiered
    ST-R4.23a  construction   Census VIP data centers and construction ex data
                              centers, real, with the level against 2019

    python -m altdata.batch5 show [--as-of ISO] [--json]
    python -m altdata.batch5 verify     # verify items 2 and 5, from the store

EVERY READ IS AS OF. Through ObservationStore.as_of: a value not knowable at the
cutoff is not used. A series that is missing is absent with its reason; nothing
is carried silently.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import math
from pathlib import Path
from typing import Any, Optional

import yaml

from . import observations, session
from .batch3 import _on_or_before, _pts, dual_percentiles

log = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "config" / "batch5_tranche_1.yaml"


def config(path: Optional[Path] = None) -> dict:
    with open(path or CONFIG_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _months_back(day: str, months: int) -> str:
    d = dt.date.fromisoformat(day)
    y, m = d.year, d.month - months
    while m < 1:
        m += 12
        y -= 1
    for k in (0, 1, 2, 3):
        try:
            return dt.date(y, m, d.day - k).isoformat()
        except ValueError:
            continue
    return dt.date(y, m, 28).isoformat()


def _bp(a: float, b: float) -> float:
    return round((a - b) * 100.0, 1)


# ---------------------------------------------------------------------------
# ST-R4.21b -- the term premium, printed
# ---------------------------------------------------------------------------

# Plain names for an absence reason: a reason prints in the edition, and no
# internal id may reach a rendered edition (validate_weekly_edits, B).
_NAMES = {
    "acm.term_premium_10y": "ACM's 10-year term premium",
    "acm.fitted_yield_10y": "ACM's fitted 10-year yield",
    "acm.risk_neutral_yield_10y": "ACM's expected short-rate path",
    "fred.yield_10y": "the 10-year Treasury yield",
    "fred.breakeven_10y": "the 10-year breakeven",
    "calc.corr_spy_tlt_60d": "the 60-day SPY-TLT correlation",
    "calc.net_liquidity": "net liquidity",
    "fred.ppi_construction": "the construction PPI (PPIDCS)",
    "census.vip_data_center": "Census data-center construction",
    "census.vip_total": "Census total construction",
}


def _name(key) -> str:
    """The plain name of a store key, else its last part in words."""
    k = str(key or "")
    return _NAMES.get(k) or k.split(".")[-1].replace("_", " ")


def term_premium(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    """ACM's 10-year term premium: its level, its change on the prior print, and
    its percentile against each trailing window, with that window's n and first
    date -- the store's real history, so a short one says so."""
    c = (cfg or config()).get("term_premium") or {}
    key = c.get("key", "acm.term_premium_10y")
    ser = _pts(st, key, cutoff)
    if not ser:
        return {"key": key, "label": c.get("label"), "absent": True,
                "reason": f"no {_name(key)} observation knowable at {cutoff[:10]}"}
    day, lvl = ser[-1]
    prior = ser[-2] if len(ser) > 1 else None
    years = tuple(int(y) for y in c.get("windows_years") or (5, 20))
    pcts = dual_percentiles(ser, years)
    for y, p in pcts.items():
        first = p.get("from")
        p["window_years_real"] = (None if not first else round(
            (dt.date.fromisoformat(day) - dt.date.fromisoformat(first)).days / 365.25, 1))
        p["short"] = bool(p["window_years_real"] is not None
                          and p["window_years_real"] < y - 0.25)
    return {"key": key, "label": c.get("label"), "level": lvl, "as_of": day,
            "change_bp": None if not prior else _bp(lvl, prior[1]),
            "prior_as_of": prior[0] if prior else None, "percentiles": pcts}


# ---------------------------------------------------------------------------
# ST-R4.26a -- the fiscal-bark flag
# ---------------------------------------------------------------------------
def _move(ser: list, start: str) -> Optional[dict]:
    if not ser:
        return None
    a = _on_or_before(ser, start)
    if a is None:
        return None
    return {"from": a[0], "to": ser[-1][0], "bp": _bp(ser[-1][1], a[1])}


def fiscal_bark(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    """The term premium's share of the trailing six-month move in ACM's fitted
    10-year, and its divergence from the expected short rate. FLAG ONLY."""
    c = (cfg or config()).get("fiscal_bark") or {}
    months = int(c.get("months", 6))
    tp, fit, path = (_pts(st, c.get(k), cutoff) for k in ("tp", "fitted", "path"))
    q = _pts(st, c.get("quoted", "fred.yield_10y"), cutoff)
    if not (tp and fit and path):
        miss = [_name(c.get(k)) for k, s in (("tp", tp), ("fitted", fit), ("path", path)) if not s]
        return {"absent": True, "months": months,
                "reason": f"{', '.join(miss)} not knowable at {cutoff[:10]}"}
    end = min(tp[-1][0], fit[-1][0], path[-1][0])
    tp_, fit_, path_ = ([x for x in s if x[0] <= end] for s in (tp, fit, path))
    start = _months_back(end, months)
    m_tp, m_fit, m_path = _move(tp_, start), _move(fit_, start), _move(path_, start)
    m_q = _move([x for x in q if x[0] <= end], start) if q else None
    if not (m_tp and m_fit and m_path):
        return {"absent": True, "months": months,
                "reason": f"ACM's history does not reach {start}"}
    move_min = float(c.get("move_min_bp", 25))
    share = (round(m_tp["bp"] / m_fit["bp"], 3)
             if abs(m_fit["bp"]) >= move_min else None)
    bark = bool(share is not None and m_fit["bp"] >= move_min
                and share >= float(c.get("share_min", 0.5)))
    div_bp = float(c.get("divergence_bp", 10))
    divergence = bool(m_tp["bp"] >= div_bp and m_path["bp"] <= -div_bp)
    return {"months": months, "from": m_fit["from"], "to": m_fit["to"],
            "fitted_bp": m_fit["bp"], "tp_bp": m_tp["bp"], "path_bp": m_path["bp"],
            "quoted_bp": m_q["bp"] if m_q else None, "tp_share": share,
            "share_reason": (None if share is not None else
                             f"the fitted 10-year moved {m_fit['bp']:+.0f}bp, under "
                             f"{move_min:.0f}bp: no share"),
            "fiscal_bark": bark, "divergence": divergence,
            "move_min_bp": move_min, "share_min": float(c.get("share_min", 0.5)),
            "divergence_bp": div_bp}


def capex_guidance_revisions(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    """Item 26's "hyperscaler capex-guidance revisions" (A66): for each
    hyperscaler, the change in its filed capex guidance between its two newest
    10-Q or 10-K filings, where both carry a figure for the same fiscal year
    (altdata/sources/edgar_guidance.py). Beside the fiscal-bark flag; report only,
    and the flag does not read it."""
    from .sources import edgar_guidance as eg                   # noqa: PLC0415
    rows = eg.revisions(st, cutoff, eg.tickers())
    return {"rows": rows, "lines": [eg.revision_text(r) for r in rows],
            "compared": sum(1 for r in rows if not r.get("reason"))}


# ---------------------------------------------------------------------------
# ST-R4.24a/b -- the stock-bond correlation, SR-9 amended
# ---------------------------------------------------------------------------
def weekly_closes(ser: list) -> list[tuple[str, float]]:
    """The last close of each ISO week."""
    out: dict[tuple, tuple] = {}
    for d, v in ser:
        k = dt.date.fromisoformat(d).isocalendar()[:2]
        out[k] = (d, v)
    return [out[k] for k in sorted(out)]


def pearson(a: list[float], b: list[float]) -> Optional[float]:
    n = len(a)
    if n < 3:
        return None
    ma, mb = sum(a) / n, sum(b) / n
    sa = math.sqrt(sum((x - ma) ** 2 for x in a))
    sb = math.sqrt(sum((y - mb) ** 2 for y in b))
    if not sa or not sb:
        return None
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (sa * sb)


def corr_weekly(spy: list, tlt: list, weeks: int) -> dict:
    """Pearson correlation of weekly log returns over the last `weeks` common
    weeks."""
    a, b = dict(weekly_closes(spy)), dict(weekly_closes(tlt))
    days = sorted(set(a) & set(b))
    ra, rb = [], []
    for p, d in zip(days, days[1:]):
        if a[p] > 0 and b[p] > 0 and a[d] > 0 and b[d] > 0:
            ra.append(math.log(a[d] / a[p]))
            rb.append(math.log(b[d] / b[p]))
    ra, rb = ra[-weeks:], rb[-weeks:]
    return {"value": pearson(ra, rb), "n_weeks": len(ra),
            "from": days[-len(ra) - 1] if ra else None, "to": days[-1] if days else None}


def strength(live: bool, real_share: Optional[float], tp_share: Optional[float],
             be_bp: Optional[float], c: dict) -> tuple[Optional[str], str]:
    """THE CONDITIONING (24b): (strength, why). Strongest when the move is
    breakeven-led; weaker when real-yield- or term-premium-led with inflation
    anchored; moderate otherwise."""
    if not live:
        return None, "the flag is not live"
    cut = float(c.get("led_cut", 0.5))
    if real_share is None:
        return "unconditioned", "no attribution share knowable at the cutoff"
    if real_share < cut:
        return "strong", (f"breakeven-led: the real yield carried {real_share:.2f} of "
                          f"the 60-session move, breakevens the rest")
    anchored = be_bp is not None and abs(be_bp) < float(c.get("anchored_bp", 15))
    led = "real-yield-led" + (" and term-premium-led" if tp_share is not None
                              and tp_share >= cut else "")
    if anchored:
        return "weak", (f"{led} with inflation anchored (the 10-year breakeven "
                        f"moved {be_bp:+.0f}bp over 60 sessions)")
    return "moderate", (f"{led}, inflation not anchored (the 10-year breakeven "
                        + (f"moved {be_bp:+.0f}bp" if be_bp is not None else
                           "is not knowable") + ")")


def _latest(st, key: str, cutoff: str) -> Optional[tuple[str, float]]:
    s = _pts(st, key, cutoff)
    return s[-1] if s else None


def stock_bond(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    c = (cfg or config()).get("stock_bond") or {}
    c60 = _latest(st, c.get("corr_60d", "calc.corr_spy_tlt_60d"), cutoff)
    w = corr_weekly(_pts(st, c.get("spy", "yfinance.mkt_spy"), cutoff),
                    _pts(st, c.get("tlt", "yfinance.mkt_tlt"), cutoff),
                    int(c.get("weeks", 104)))
    two = (w if w["value"] is not None and w["n_weeks"] >= int(c.get("min_weeks", 78))
           else {**w, "absent": f"{w['n_weeks']} weeks of SPY and TLT stored; the "
                                f"2-year window needs {int(c.get('min_weeks', 78))}"})
    y10 = _latest(st, c.get("ten_year", "fred.yield_10y"), cutoff)
    rs = _latest(st, c.get("real_share", "calc.attr_real_share_60d"), cutoff)
    ts = _latest(st, c.get("tp_share", "calc.attr_acm_tp_share_60d"), cutoff)
    be = _pts(st, c.get("breakeven", "fred.breakeven_10y"), cutoff)
    n = int(c.get("breakeven_sessions", 60))
    be_bp = _bp(be[-1][1], be[-n - 1][1]) if len(be) > n else None
    if c60 is None:
        return {"absent": True, "reason": f"{_name(c.get('corr_60d'))} not knowable at "
                f"{cutoff[:10]}", "two_year": two}
    live = c60[1] > float(c.get("live_above", 0.2))
    s, why = strength(live, rs[1] if rs else None, ts[1] if ts else None, be_bp, c)
    prior = float(c.get("level_prior_pct", 5.25))
    return {"corr_60d": round(c60[1], 3), "corr_60d_as_of": c60[0],
            "two_year": {k: (round(v, 3) if isinstance(v, float) else v)
                         for k, v in two.items()},
            "live": live, "live_above": float(c.get("live_above", 0.2)),
            "persistent": bool(live and two.get("value") is not None
                               and not two.get("absent") and two["value"] > 0),
            "ten_year": y10[1] if y10 else None, "ten_year_as_of": y10[0] if y10 else None,
            "above_prior": bool(y10 and y10[1] >= prior), "level_prior_pct": prior,
            "real_share": rs[1] if rs else None, "tp_share": ts[1] if ts else None,
            "breakeven_bp": be_bp, "strength": s, "why": why,
            "companions": " ".join(str(c.get("companions") or "").split())}


# ---------------------------------------------------------------------------
# ST-R4.17a -- net liquidity, attributed
# ---------------------------------------------------------------------------
def net_liquidity(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    """calc.net_liquidity (dollars) with its 4- and 13-week changes, and each
    change split into its legs: + Fed assets, - TGA, - RRP, every leg in dollars."""
    c = (cfg or config()).get("net_liquidity") or {}
    ser = _pts(st, c.get("key", "calc.net_liquidity"), cutoff)
    if len(ser) < 2:
        return {"absent": True, "reason": f"net liquidity has {len(ser)} "
                f"observation(s) knowable at {cutoff[:10]}"}
    legs = {name: (dict(_pts(st, k, cutoff)), float(mult))
            for name, (k, mult) in (c.get("legs") or {}).items()}
    meaning = c.get("meaning") or {}
    out = {"level": ser[-1][1], "as_of": ser[-1][0], "windows": {}}
    for w in c.get("weeks") or (4, 13):
        w = int(w)
        if len(ser) <= w:
            out["windows"][str(w)] = {"absent": f"{len(ser)} weekly observations; "
                                                f"{w} weeks need {w + 1}"}
            continue
        (d0, v0), (d1, v1) = ser[-w - 1], ser[-1]
        contrib = {}
        for name, (pts, mult) in legs.items():
            if d0 in pts and d1 in pts:
                sign = 1.0 if name == "fed_assets" else -1.0
                contrib[name] = sign * (pts[d1] - pts[d0]) * mult
        lead = max(contrib, key=lambda k: abs(contrib[k])) if contrib else None
        out["windows"][str(w)] = {
            "from": d0, "to": d1, "change": v1 - v0, "contributions": contrib,
            "residual": (v1 - v0) - sum(contrib.values()) if len(contrib) == len(legs)
            else None,
            "led_by": lead, "meaning": meaning.get(lead) if lead else None}
    return out


# ---------------------------------------------------------------------------
# ST-R4.23a -- construction spending, real
# ---------------------------------------------------------------------------
def _yoy(ser: dict, day: str) -> Optional[float]:
    d = dt.date.fromisoformat(day)
    back = d.replace(year=d.year - 1).isoformat()
    if back not in ser or not ser[back]:
        return None
    return ser[day] / ser[back]


def construction(st, cutoff: str, cfg: Optional[dict] = None,
                 held_reason: Optional[str] = None) -> dict:
    """Data-center construction (real year over year, its share of private
    nonresidential) and total construction ex data centers (real year over year),
    each with its real level against the base year's average."""
    c = (cfg or config()).get("construction") or {}
    dc, nonres, tot, pwr, ppi = (dict(_pts(st, c.get(k), cutoff)) for k in
                                 ("data_center", "private_nonresidential", "total",
                                  "power", "deflator"))
    if not dc or not tot:
        return {"absent": True,
                "reason": held_reason or (f"{_name(c.get('data_center'))} / {_name(c.get('total'))} "
                                          f"not knowable at {cutoff[:10]}")}
    if not ppi:
        return {"absent": True, "reason": f"{_name(c.get('deflator'))} not knowable at "
                f"{cutoff[:10]}, so nothing to deflate by"}
    exdc = {d: tot[d] - dc[d] for d in tot if d in dc}
    base = str(int(c.get("base_year", 2019)))
    common = sorted(set(dc) & set(ppi) & set(exdc))
    if not common:
        return {"absent": True, "reason": "no month carries both the spending and PPIDCS"}
    day = common[-1]

    def real(series: dict) -> dict:
        return {d: series[d] / ppi[d] for d in series if d in ppi and ppi[d]}

    def forms(series: dict) -> dict:
        r = real(series)
        yoy = _yoy(r, day)
        b = [v for d, v in r.items() if d.startswith(base)]
        lvl = (r[day] / (sum(b) / len(b)) - 1) * 100 if len(b) == 12 and day in r else None
        nom = _yoy(series, day)
        return {"nominal": series.get(day), "real_yoy_pct": None if yoy is None
                else round((yoy - 1) * 100, 1),
                "nominal_yoy_pct": None if nom is None else round((nom - 1) * 100, 1),
                "vs_base_pct": None if lvl is None else round(lvl, 1),
                "base_months": len(b)}
    out = {"as_of": day, "base_year": int(base), "units": "millions of dollars, SAAR",
           "data_center": forms(dc), "ex_data_center": forms(exdc)}
    if nonres.get(day):
        out["data_center"]["share_of_private_nonres_pct"] = round(
            dc[day] / nonres[day] * 100, 1)
    if pwr:
        out["power"] = forms(pwr)
    return out


# ---------------------------------------------------------------------------
# Verify items 2 and 5, from the store (read only)
# ---------------------------------------------------------------------------
def verify(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    y10 = [p for p in _pts(st, "fred.yield_10y", cutoff)
           if "2026-09-25" <= p[0] <= "2026-10-16"]
    nl = net_liquidity(st, cutoff, cfg)
    sept = None
    ser = _pts(st, "calc.net_liquidity", cutoff)
    sep = [p for p in ser if "2026-08-26" <= p[0] <= "2026-10-08"]
    if len(sep) >= 2:
        legs = {n: dict(_pts(st, k, cutoff)) for n, (k, _) in
                (cfg["net_liquidity"]["legs"]).items()}
        d0, d1 = sep[0][0], sep[-1][0]
        mult = {n: float(m) for n, (_, m) in cfg["net_liquidity"]["legs"].items()}
        sept = {"from": d0, "to": d1, "change": sep[-1][1] - sep[0][1],
                "legs": {n: (1 if n == "fed_assets" else -1) * (p[d1] - p[d0]) * mult[n]
                         for n, p in legs.items() if d0 in p and d1 in p}}
    return {"item_5_dgs10": y10,
            "item_5_crossed": [p for p in y10 if p[1] >= 5.25],
            "item_2_september": sept, "net_liquidity_now": nl}


def build(as_of: Optional[str] = None, store=None) -> dict:
    cutoff = as_of or session.utc_iso(timespec="microseconds")
    own = store is None
    st = store or observations.ObservationStore()
    try:
        cfg = config()
        out = {"as_of": cutoff}
        for name, fn in (("term_premium", term_premium), ("fiscal_bark", fiscal_bark),
                         ("capex_guidance_revisions", capex_guidance_revisions),
                         ("stock_bond", stock_bond), ("net_liquidity", net_liquidity),
                         ("construction", construction)):
            try:
                out[name] = fn(st, cutoff, cfg)
            except Exception as exc:                            # noqa: BLE001
                out[name] = {"absent": True, "reason": f"FAULT {type(exc).__name__}: {exc}"}
        return out
    finally:
        if own:
            st.close()


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    p = argparse.ArgumentParser(prog="python -m altdata.batch5")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("show", "verify"):
        s = sub.add_parser(name)
        s.add_argument("--as-of", default=None)
        s.add_argument("--db", default=None)
    a = p.parse_args(argv)
    cutoff = a.as_of or session.utc_iso(timespec="microseconds")
    with observations.ObservationStore(a.db) as st:
        res = build(cutoff, st) if a.cmd == "show" else verify(st, cutoff)
    print(json.dumps(res, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
