"""
Batch 5 Tranche 1, part 2 (signal-triage round 4, part 2; filed 9 Oct 2026):
items 18, 19, 22 and 27. Config: config/batch5_tranche_1b.yaml. Printed by
daily_cascade/batch5b_block.py. Nothing here fetches, and nothing is a state.

    ST-R4.18a  dispersion      Cboe's DSPX, COR1M and COR3M with dual percentiles
                               (real window and n), the "dispersion regime: high
                               or low" flag, realized cross-sectional dispersion
                               as the fallback, and the by-hand FlashAlpha keys
    ST-R4.19a  vol_divergence  MOVE's and VIX's z on a one-year window, the
                               order's two tiers, percentile ranks beside z, and
                               the T&B conditioner (inactive: T&B is not built)
    ST-R4.22a  expansion_age   the expansion's age from the NBER dates and the
                               post-war conditional hazard
    ST-R4.22b  factor_i        BEA's contribution of information-processing
                               equipment and software to real GDP growth
    ST-R4.27a  overnight       TLT's and ZN=F's overnight (open less the prior
                               close) and session (close less open) legs, each
                               over 20 sessions; `cosignal` is SR-36's fifth
                               co-signal and the Japan slow-money set's

    python -m altdata.batch5b show [--as-of ISO] [--db PATH]

EVERY READ IS AS OF. Through ObservationStore.as_of: a value not knowable at the
cutoff is not used. A series that is missing is absent with its reason, by its
plain name (no store key reaches an edition).
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import math
import statistics
from pathlib import Path
from typing import Optional

import yaml

from . import derived, observations, session
from .batch3 import _pts, dual_percentiles

log = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "config" / "batch5_tranche_1b.yaml"

_NAMES = {
    "yfinance.mkt_dspx": "the Cboe S&P 500 Dispersion Index (DSPX)",
    "yfinance.mkt_cor1m": "the Cboe 1-month implied correlation (COR1M)",
    "yfinance.mkt_cor3m": "the Cboe 3-month implied correlation (COR3M)",
    "cboe.dspx": "the Cboe S&P 500 Dispersion Index (DSPX)",
    "cboe.cor1m": "the Cboe 1-month implied correlation (COR1M)",
    "cboe.cor3m": "the Cboe 3-month implied correlation (COR3M)",
    "yfinance.mkt_move": "the MOVE",
    "yfinance.mkt_vix": "the VIX",
    "yfinance.mkt_tlt": "TLT",
    "yfinance.mkt_zn_front": "ZN=F",
    "fred.contrib_info_equipment": "BEA's information-processing equipment contribution",
    "fred.contrib_software": "BEA's software contribution",
    "fred.real_gdp": "real GDP",
}


def _name(key) -> str:
    k = str(key or "")
    return _NAMES.get(k) or k.split(".")[-1].replace("_", " ")


def config(path: Optional[Path] = None) -> dict:
    with open(path or CONFIG_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _years_between(a: str, b: str) -> float:
    return round((dt.date.fromisoformat(b) - dt.date.fromisoformat(a)).days / 365.25, 1)


def _dual(ser: list, years) -> dict:
    """batch3.dual_percentiles, with each window's real span: a window the
    history does not fill says so ("short", the years it holds)."""
    out = dual_percentiles(ser, tuple(int(y) for y in years))
    for y, p in out.items():
        real = _years_between(p["from"], ser[-1][0]) if p.get("from") else 0.0
        p["window_years_real"] = real
        p["short"] = real < float(y) - 0.05
    return out


# ---------------------------------------------------------------------------
# ST-R4.18a -- the dispersion panel
# ---------------------------------------------------------------------------
def realized_dispersion(st, cutoff: str, c: dict) -> dict:
    """The 21-session mean of the daily cross-sectional standard deviation of
    constituent log returns, in percent a day. Reads the series session A's
    Batch 6 item 44 writer stores (one instrument per name); until its name is
    set in config and it has rows, "awaiting constituent prices"."""
    key = c.get("key")
    if not key:
        return {"absent": True, "reason": "awaiting constituent prices (Batch 6 item "
                "44's writer, held for D1c)"}
    names = st.instruments(key)
    if not names:
        return {"absent": True, "reason": "awaiting constituent prices (Batch 6 item "
                "44's writer, held for D1c, has stored none)"}
    closes = {n: dict(_pts(st, key, cutoff, n)) for n in names}
    rets: dict[str, list[float]] = {}
    for n, ser in closes.items():
        days = sorted(ser)
        for a, b in zip(days, days[1:]):
            if ser[a] > 0 and ser[b] > 0:
                rets.setdefault(b, []).append(math.log(ser[b] / ser[a]))
    need, k = int(c.get("min_names", 100)), int(c.get("sessions", 21))
    days = [d for d in sorted(rets) if len(rets[d]) >= need][-k:]
    if len(days) < k:
        return {"absent": True, "reason": f"{len(days)} sessions with {need} or more "
                f"names; {k} needed"}
    sd = [statistics.pstdev(rets[d]) * 100.0 for d in days]
    return {"value": round(statistics.fmean(sd), 3), "sessions": k, "to": days[-1],
            "names": min(len(rets[d]) for d in days)}


def _manual(st, key: Optional[str], cutoff: str) -> Optional[tuple[str, float]]:
    if not key:
        return None
    p = _pts(st, key, cutoff)
    return p[-1] if p else None


def dispersion(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    c = (cfg or config()).get("dispersion") or {}
    years = c.get("windows_years") or [1, 5]
    rows = {}
    for name in ("dspx", "cor1m", "cor3m"):
        keys = c.get(name)
        keys = [keys] if isinstance(keys, str) or keys is None else list(keys)
        key, ser = keys[0], []
        for k in keys:                     # the first key with rows; never spliced
            ser = _pts(st, k, cutoff)
            if ser:
                key = k
                break
        if not ser:
            rows[name] = {"absent": True, "reason": f"{_name(keys[0])}: not stored at "
                                                    f"{cutoff[:10]}"}
            continue
        rows[name] = {"level": ser[-1][1], "as_of": ser[-1][0], "n_total": len(ser),
                      "first": ser[0][0], "percentiles": _dual(ser, years),
                      "source": "Cboe" if str(key).startswith("cboe.") else "Yahoo"}
    flag = {"state": None, "why": "DSPX not stored"}
    d = rows["dspx"]
    if not d.get("absent"):
        long = d["percentiles"][max(int(y) for y in years)]
        need = int(c.get("min_n", 250))
        if long["n"] < need or long["pct"] is None:
            flag = {"state": None, "why": f"withheld: {long['n']} sessions of DSPX "
                                          f"stored, {need} needed"}
        elif long["pct"] >= float(c.get("high_pct", 80)):
            flag = {"state": "high", "pct": long["pct"], "n": long["n"]}
        elif long["pct"] <= float(c.get("low_pct", 20)):
            flag = {"state": "low", "pct": long["pct"], "n": long["n"]}
        else:
            flag = {"state": "none", "pct": long["pct"], "n": long["n"]}
    pair = False
    cor = rows["cor3m"]
    if flag.get("state") == "high" and not cor.get("absent"):
        cp = cor["percentiles"][max(int(y) for y in years)]
        pair = (cp["pct"] is not None and cp["n"] >= int(c.get("min_n", 250))
                and cp["pct"] <= float(c.get("cor_low_pct", 20)))
    man = c.get("manual") or {}
    return {"rows": rows, "flag": flag, "single_name_edge": pair,
            "realized": realized_dispersion(st, cutoff, c.get("realized") or {}),
            "flashalpha": {"implied": _manual(st, man.get("implied"), cutoff),
                           "realized": _manual(st, man.get("realized"), cutoff)},
            "thresholds": {k: c.get(k) for k in ("high_pct", "low_pct", "min_n",
                                                  "cor_low_pct")}}


# ---------------------------------------------------------------------------
# ST-R4.19a -- the cross-asset vol divergence flag
# ---------------------------------------------------------------------------
def _months_back(day: str, months: int) -> str:
    d = dt.date.fromisoformat(day)
    y, m = divmod(d.month - 1 - months, 12)
    y += d.year
    m += 1
    for k in range(4):
        try:
            return dt.date(y, m, d.day - k).isoformat()
        except ValueError:
            continue
    return dt.date(y, m, 28).isoformat()


def tier(move_z: float, vix_z: float, c: dict) -> Optional[str]:
    """The order's two tiers, strict inequalities as written: strong when MOVE's
    z > +1.0 and VIX's z < +0.4; watch when MOVE's z > +0.5 and VIX's z < +0.4."""
    if vix_z >= float(c.get("vix_z_below", 0.4)):
        return None
    if move_z > float(c.get("strong_move_z", 1.0)):
        return "strong"
    if move_z > float(c.get("watch_move_z", 0.5)):
        return "watch"
    return None


def conditioner(st, day: str, cutoff: str, c: dict) -> dict:
    """Discounted when the T&B bottom signal fired within the prior 12 months.
    T&B is not built: with no series named the path reports itself inactive."""
    t = c.get("tb_bottom") or {}
    if not t.get("key"):
        return {"active": False, "discounted": False,
                "why": "T&B not built; conditioner inactive"}
    lo = _months_back(day, int(t.get("months", 12)))
    fired = [d for d, v in _pts(st, t["key"], cutoff) if lo < d <= day and v >= 1]
    if fired:
        return {"active": True, "discounted": True, "fired": fired[-1],
                "why": f"discounted: the T&B bottom signal fired on {fired[-1]}, within "
                       f"{t.get('months', 12)} months (the study's misses, 2003 and "
                       f"2009, both came within a year of a major equity low)"}
    return {"active": True, "discounted": False,
            "why": f"the T&B bottom signal has not fired since {lo}"}


def vol_divergence(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    c = (cfg or config()).get("vol_divergence") or {}
    mv, vx = dict(_pts(st, c.get("move"), cutoff)), dict(_pts(st, c.get("vix"), cutoff))
    days = sorted(set(mv) & set(vx))
    w, need = int(c.get("window_sessions", 252)), int(c.get("min_sessions", 227))
    win = days[-w:]
    if len(win) < need:
        miss = [_name(c.get(k)) for k, s in (("move", mv), ("vix", vx)) if not s]
        return {"absent": True, "reason": (f"not stored: {', '.join(miss)}" if miss else
                f"{len(win)} common sessions of the MOVE and the VIX; {need} needed")}
    out = {"as_of": win[-1], "n": len(win), "from": win[0]}
    for name, ser in (("move", mv), ("vix", vx)):
        vals = [ser[d] for d in win]
        z = derived.z_of(vals, vals[-1])
        if z is None:
            return {"absent": True, "reason": f"{_name(c.get(name))} did not move over "
                                              f"the window: no z"}
        out[name] = {"level": vals[-1], "z": round(z, 2),
                     "pct": derived.percentile_of(vals, vals[-1])}
    out["spread_z"] = round(out["move"]["z"] - out["vix"]["z"], 2)
    out["tier"] = tier(out["move"]["z"], out["vix"]["z"], c)
    out["conditioner"] = conditioner(st, win[-1], cutoff, c)
    out["thresholds"] = {k: c.get(k) for k in ("watch_move_z", "strong_move_z",
                                                "vix_z_below", "window_sessions")}
    return out


# ---------------------------------------------------------------------------
# ST-R4.22a -- the expansion's age and the post-war hazard
# ---------------------------------------------------------------------------
def load_expansions(cfg: Optional[dict] = None) -> dict:
    c = (cfg or config()).get("expansion") or {}
    with open(REPO / c.get("fixture", "config/nber_expansions.yaml"), encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _month_index(ym: str) -> int:
    y, m = ym[:7].split("-")
    return int(y) * 12 + int(m) - 1


def hazard(durations: list[int], age: int, horizon: int = 12) -> dict:
    """Of the completed expansions that lasted `age` months or more, how many
    peaked before `age + horizon` (age <= months < age + horizon)."""
    at_risk = [d for d in durations if d >= age]
    ended = [d for d in at_risk if d < age + horizon]
    return {"age": age, "of": len(at_risk), "ended": len(ended),
            "share": (len(ended) / len(at_risk)) if at_risk else None}


def expansion_age(cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    fx = load_expansions(cfg)
    exps = fx.get("expansions") or []
    done = [int(e["months"]) for e in exps if e.get("peak")]
    cur = [e for e in exps if not e.get("peak")]
    if not cur:
        return {"absent": True, "reason": "the NBER fixture holds no current expansion "
                "(a peak was announced): update config/nber_expansions.yaml"}
    trough = cur[-1]["trough"]
    age = _month_index(cutoff[:7]) - _month_index(trough)
    h = hazard(done, age, int((cfg.get("expansion") or {}).get("horizon_months", 12)))
    modern = [int(e["months"]) for e in exps if e.get("peak")
              and e["trough"] >= str(fx.get("modern_from", "1982-11"))]
    return {"trough": trough, "age_months": age, "hazard": h,
            "n": len(done), "mean": round(statistics.fmean(done), 1),
            "median": statistics.median(done), "longest": max(done),
            "rank": 1 + sum(1 for d in done if d > age),
            "modern": {"n": len(modern), "mean": round(statistics.fmean(modern), 1)
                       if modern else None},
            "source": fx.get("source")}


# ---------------------------------------------------------------------------
# ST-R4.22b -- Factor I's dependency line
# ---------------------------------------------------------------------------
def _quarter(day: str) -> str:
    return f"Q{(int(day[5:7]) - 1) // 3 + 1} {day[:4]}"


def factor_i(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    c = (cfg or config()).get("factor_i") or {}
    eq = dict(_pts(st, c.get("info_equipment"), cutoff))
    sw = dict(_pts(st, c.get("software"), cutoff))
    gdp = _pts(st, c.get("real_gdp", "fred.real_gdp"), cutoff)
    days = sorted(set(eq) & set(sw))
    if not days:
        miss = [_name(c.get(k)) for k, s in (("info_equipment", eq), ("software", sw))
                if not s]
        return {"absent": True, "reason": ", ".join(
            miss or ["no quarter carries both contributions"])
            + f" not stored at {cutoff[:10]}"}
    growth = {}
    for (d0, g0), (d1, g1) in zip(gdp, gdp[1:]):
        if g0 > 0:
            growth[d1] = round(((g1 / g0) ** 4 - 1) * 100.0, 2)
    rows = []
    for d in days[-int(c.get("quarters", 4)):]:
        tot = round(eq[d] + sw[d], 2)
        g = growth.get(d)
        rows.append({"quarter": _quarter(d), "observed_at": d, "equipment": eq[d],
                     "software": sw[d], "total": tot, "gdp_growth": g,
                     "share_pct": (round(100.0 * tot / g) if g is not None and abs(g) >= 0.5
                                   else None)})
    avg = round(statistics.fmean(r["total"] for r in rows), 2)
    gs = [r["gdp_growth"] for r in rows if r["gdp_growth"] is not None]
    return {"rows": rows, "latest": rows[-1], "avg_total": avg,
            "avg_gdp": round(statistics.fmean(gs), 2) if len(gs) == len(rows) else None}


# ---------------------------------------------------------------------------
# ST-R4.27a -- overnight vs session
# ---------------------------------------------------------------------------
def legs(closes: dict, opens: dict) -> list[dict]:
    """Per session with an open and a prior close: the overnight leg ln(open /
    prior close), the session leg ln(close / open) and the day's change ln(close
    / prior close), in percent. The two legs sum to the day's change exactly."""
    days = sorted(closes)
    out = []
    for a, b in zip(days, days[1:]):
        o, pc, cl = opens.get(b), closes[a], closes[b]
        if not (o and pc and cl) or min(o, pc, cl) <= 0:
            continue
        out.append({"day": b, "overnight": math.log(o / pc) * 100.0,
                    "session": math.log(cl / o) * 100.0,
                    "change": math.log(cl / pc) * 100.0})
    return out


def split(st, cutoff: str, inst: dict, n: int) -> dict:
    cl = dict(_pts(st, inst["close"], cutoff))
    op = dict(_pts(st, inst["open"], cutoff))
    lg = legs(cl, op)
    if len(lg) < n:
        return {"label": inst["label"], "absent": True,
                "reason": f"{len(lg)} sessions with an open stored; {n} needed"
                if cl else f"{_name(inst['close'])} not stored"}
    last = lg[-n:]
    on = sum(x["overnight"] for x in last)
    se = sum(x["session"] for x in last)
    tot = sum(x["change"] for x in last)
    carried = None
    if abs(tot) > 1e-9 and (on > 0) == (tot > 0) and abs(on) >= abs(se):
        carried = "overnight"
    elif abs(tot) > 1e-9 and (se > 0) == (tot > 0) and abs(se) > abs(on):
        carried = "session"
    return {"label": inst["label"], "from": last[0]["day"], "to": last[-1]["day"],
            "sessions": n, "overnight": round(on, 2), "session": round(se, 2),
            "total": round(tot, 2), "carried_by": carried,
            "yields": "up" if tot < 0 else "down" if tot > 0 else "flat",
            "foreign_hours": bool(inst.get("foreign_hours")), "_legs": lg}


def overnight(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    c = (cfg or config()).get("overnight") or {}
    n = int(c.get("sessions", 20))
    rows = [split(st, cutoff, i, n) for i in c.get("instruments") or []]
    co = _cosignal_from(rows, c)
    for r in rows:
        r.pop("_legs", None)
    return {"rows": rows, "cosignal": co, "zn_note": c.get("zn_note")}


def _cosignal_from(rows: list[dict], c: dict) -> dict:
    """TLT's 20-session overnight leg as a z on five years of 20-session
    overnight legs (basis_proxy.change_z on the cumulated leg), on when at or
    below -2 sigma: falling prices, rising yields, carried overnight."""
    from .basis_proxy import change_z                            # noqa: PLC0415
    ref = next((r for r in rows if r.get("foreign_hours")), None)
    if not ref or ref.get("absent"):
        return {"state": None, "why": "absent: TLT's open not stored for the window"}
    cum, acc = [], 0.0
    for x in ref["_legs"]:
        acc += x["overnight"]
        cum.append((x["day"], acc))
    z = change_z(cum, int(c.get("sessions", 20)), int(c.get("history_days", 1826)))
    if z is None:
        return {"state": None, "why": "absent: TLT's overnight history is too short"}
    sig = float(c.get("sigma", 2.0))
    return {"state": z <= -sig, "z": round(z, 2), "as_of": ref["to"],
            "why": f"TLT's 20-session overnight leg {z:+.1f} sigma"}


def cosignal(st, day: str, cutoff: Optional[str], cfg: Optional[dict] = None) -> dict:
    """SR-36's unwind watch calls this by name (config/basis_proxy.yaml
    unwind_watch.overnight): the co-signal as of the watch's report day."""
    cut = cutoff or session.utc_iso(timespec="microseconds")
    c = (cfg or config()).get("overnight") or {}
    n = int(c.get("sessions", 20))
    rows = []
    for i in c.get("instruments") or []:
        cl = {d: v for d, v in _pts(st, i["close"], cut) if d <= day}
        op = {d: v for d, v in _pts(st, i["open"], cut) if d <= day}
        lg = legs(cl, op)
        rows.append({"foreign_hours": bool(i.get("foreign_hours")),
                     "absent": len(lg) < n, "_legs": lg,
                     "to": lg[-1]["day"] if lg else None})
    return _cosignal_from(rows, c)


# ---------------------------------------------------------------------------
def build(as_of: Optional[str] = None, store=None) -> dict:
    cutoff = as_of or session.utc_iso(timespec="microseconds")
    own = store is None
    st = store or observations.ObservationStore()
    try:
        cfg = config()
        out = {"as_of": cutoff}
        for name, fn in (("dispersion", dispersion), ("vol_divergence", vol_divergence),
                         ("factor_i", factor_i), ("overnight", overnight)):
            try:
                out[name] = fn(st, cutoff, cfg)
            except Exception as exc:                            # noqa: BLE001
                out[name] = {"absent": True, "reason": f"FAULT {type(exc).__name__}: {exc}"}
        out["expansion_age"] = expansion_age(cutoff, cfg)
        return out
    finally:
        if own:
            st.close()


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    p = argparse.ArgumentParser(prog="python -m altdata.batch5b")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("show")
    s.add_argument("--as-of", default=None)
    s.add_argument("--db", default=None)
    a = p.parse_args(argv)
    cutoff = a.as_of or session.utc_iso(timespec="microseconds")
    with observations.ObservationStore(a.db) as st:
        res = build(cutoff, st)
    print(json.dumps(res, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
