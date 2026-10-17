"""
The volatility event flag and its attribution (Batch 9 item 52, ruled 17 Oct
2026; docs/change-order-signal-triage-batch-9-2026-10-17.md). The batch-1 10-year
attribution's pattern (altdata/rates_attribution.py), extended to volatility.

    python -m altdata.vol_event show [--date D]          # the session's read
    python -m altdata.vol_event seed --date 2026-10-16   # the ledger's first row
    python -m altdata.vol_event resolve                  # fill realised outcomes

ST-R6.52a THE TRIGGER, two-sided (config/vol_event.yaml): a one-day VIX change of
15% or 3 points either way; a five-day change beyond its own 95th percentile on a
20-year window (log terms); a crossing of an XIII regime band (the vol dial's
level bands, config/market_state.yaml); or compression to within 5% of the
trailing six-month low, held three sessions. Level and change are SEPARATE
fields, each with its five- and 20-year percentile.

ST-R6.52b THE NINE LENSES, one line each, eight computed: spot-vol, term
structure, tail and vol-of-vol, cross-asset, dealer positioning, realised
against implied, breadth, positioning; the ninth, the catalyst, from the Phase B
scan's stored press attributions -- "not established" is a permitted value. A
lens with no stored input says so ("awaiting ..." or a listed gap); none is
guessed. Units follow AUD-3a: the VIX in points and percent; VVIX, MOVE and SKEW
in log terms (the move screen's), each line stating its unit.

ST-R6.52c THE BLOCK (daily_cascade: the close's Mechanics, the next 07:00
anchor): the trigger line, the lenses, the regime consequence (the XIII band;
Book C's rule, the volatile-day protocol -- printed, never applied) and the base
rate. Compression prints the complacency read and stores the flag the
Concentration & Complacency overlay's VIX input reads (calc.vol_compression);
no new overlay. The 12:30 gate (upward only) is vol_gate below, registered in
daily_cascade/midday_gate.py.

ST-R6.52d THE BASE RATE from the box's history, never recalled: forward SPX and
VIX after prior moves of the same direction and size from the same level band,
with n. THE LEDGER: each fired event with its attribution and realised 5- and
20-day outcomes (vol.event_ledger), the calibration ledger for any later
modifier right -- none before 30 events.

RIGHTS: a flag and an alert gate only. No composite weight; nothing applied;
no register write; paper only.
"""

from __future__ import annotations

import datetime as dt
import json
import math
import sys
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parent.parent
EVENT_KEY = "vol.event_day"
LEDGER_KEY = "vol.event_ledger"
COMPRESSION_KEY = "calc.vol_compression"
LENS_ORDER = ("spot_vol", "term_structure", "tail", "cross_asset", "dealer",
              "realised", "breadth", "positioning", "catalyst")
LENS_TITLES = {"spot_vol": "Spot-vol", "term_structure": "Term structure",
               "tail": "Tail and vol-of-vol", "cross_asset": "Cross-asset",
               "dealer": "Dealer positioning", "realised": "Realised against implied",
               "breadth": "Breadth", "positioning": "Positioning",
               "catalyst": "Catalyst"}


def config() -> dict:
    import yaml                                                 # noqa: PLC0415
    return yaml.safe_load((REPO / "config" / "vol_event.yaml").read_text(encoding="utf-8"))


def level_bands() -> list[dict]:
    """The XIII regime bands: the vol dial's level bands, highest first."""
    import yaml                                                 # noqa: PLC0415
    ms = yaml.safe_load((REPO / "config" / "market_state.yaml").read_text(encoding="utf-8"))
    vol = (ms.get("dimensions") or {}).get("vol") or ms.get("vol") or {}
    if not vol:
        for v in ms.values():
            if isinstance(v, dict) and isinstance(v.get("vol"), dict):
                vol = v["vol"]
                break
    return sorted(vol.get("level_bands") or [], key=lambda b: -float(b["min_level"]))


def band_of(level: Optional[float], bands: list[dict]) -> Optional[str]:
    if level is None:
        return None
    for b in bands:
        if level >= float(b["min_level"]):
            return b["state"]
    return None


# ---------------------------------------------------------------------------
# Small arithmetic
# ---------------------------------------------------------------------------
def pctile(values: list[float], x: float) -> Optional[float]:
    if not values:
        return None
    return round(100.0 * sum(1 for v in values if v <= x) / len(values), 1)


def nearest_rank(values: list[float], q: float) -> Optional[float]:
    if not values:
        return None
    s = sorted(values)
    return s[max(0, math.ceil(q / 100.0 * len(s)) - 1)]


def realised(closes: list[float]) -> Optional[float]:
    rets = [math.log(b / a) for a, b in zip(closes, closes[1:]) if a and b]
    if len(rets) < 2:
        return None
    m = sum(rets) / len(rets)
    return math.sqrt(sum((r - m) ** 2 for r in rets) / (len(rets) - 1) * 252.0) * 100.0


def ols_slope(xs: list[float], ys: list[float]) -> Optional[float]:
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx


def fmt_signed(v: Optional[float], dp: int = 2, unit: str = "") -> str:
    if v is None:
        return "n/a"
    return f"{'+' if v > 0 else '−' if v < 0 else ''}{abs(v):,.{dp}f}{unit}"


def _upto(series: list[tuple[str, float]], day: str) -> list[tuple[str, float]]:
    return [(d, v) for d, v in series if d <= day]


def _val(series: list[tuple[str, float]], day: str) -> tuple[Optional[float], Optional[float]]:
    """(the day's value, the previous stored value) -- None when the day has none."""
    s = _upto(series, day)
    if not s or s[-1][0] != day:
        return None, (s[-1][1] if s else None)
    return s[-1][1], (s[-2][1] if len(s) > 1 else None)


# ---------------------------------------------------------------------------
# ST-R6.52a -- the trigger
# ---------------------------------------------------------------------------
def trigger(vix: list[tuple[str, float]], day: str, cfg: dict,
            bands: list[dict]) -> dict:
    """The four arms on the VIX history up to `day`, and the level and change
    as separate fields with their five- and 20-year percentiles."""
    t = cfg["trigger"]
    s = _upto(vix, day)
    if not s or s[-1][0] != day or len(s) < 2:
        return {"day": day, "fired": False, "reason": "no VIX stored for the session",
                "arms": {}}
    vals = [v for _, v in s]
    v, v0 = vals[-1], vals[-2]
    pts, pct = v - v0, (v / v0 - 1.0) * 100.0 if v0 else None
    arms: dict[str, dict] = {}
    # At the threshold, not below: rounded to 9 decimals so 8.5 / 10 - 1 reads
    # as the -15% it is, not -14.9999999999.
    one = (round(abs(pct or 0), 9) >= float(t["one_day_pct"])
           or round(abs(pts), 9) >= float(t["one_day_points"]))
    arms["one_day"] = {"fired": one, "points": pts, "pct": pct}
    k = int(t["five_day_sessions"])
    yrs = int(t["five_day_window_years"])
    win = vals[-(252 * yrs + k):]
    ch5 = [math.log(b / a) for a, b in zip(win, win[k:]) if a and b]
    cur5 = math.log(v / vals[-1 - k]) if len(vals) > k and vals[-1 - k] else None
    hist5 = [abs(x) for x in ch5[:-1]]
    p95 = nearest_rank(hist5, float(t["five_day_percentile"]))
    arms["five_day"] = {"fired": bool(cur5 is not None and p95 is not None
                                      and abs(cur5) > p95),
                        "log_change": cur5, "threshold": p95, "n": len(hist5)}
    b1, b0 = band_of(v, bands), band_of(v0, bands)
    arms["band"] = {"fired": b1 != b0, "from": b0, "to": b1}
    w = int(t["compression_window_sessions"])
    held = int(t["compression_hold_sessions"])
    near = float(t["compression_within_pct"]) / 100.0
    comp_days = []
    for i in range(len(vals) - held, len(vals)):
        if i < w - 1:
            break
        lo = min(vals[i - w + 1:i + 1])
        comp_days.append(vals[i] <= lo * (1.0 + near))
    comp = len(comp_days) == held and all(comp_days)
    arms["compression"] = {"fired": comp,
                           "six_month_low": min(vals[-w:]) if len(vals) >= w else None}
    fired = any(a["fired"] for a in arms.values())
    direction = ("compression" if comp and not (one or arms["five_day"]["fired"]) else
                 "up" if pts > 0 else "down" if pts < 0 else "flat")
    pw = cfg["percentiles"]
    spy = int(pw["sessions_per_year"])
    level, change = {"value": v}, {"points": pts, "pct": pct}
    chg = [b - a for a, b in zip(vals, vals[1:])]
    for y in pw["windows_years"]:
        n = spy * int(y)
        level[f"pct_{y}y"] = pctile(vals[-n:], v)
        change[f"pct_{y}y"] = pctile(chg[-n:], pts)
        level[f"n_{y}y"] = len(vals[-n:])
    return {"day": day, "fired": fired, "direction": direction, "arms": arms,
            "level": level, "change": change, "band": b1, "prior_band": b0}


def trigger_line(tr: dict) -> str:
    if not tr.get("arms"):
        return f"Volatility: {tr.get('reason')}."
    lv, ch = tr["level"], tr["change"]
    why = [n for n, lab in (("one_day", "the one-day move"),
                            ("five_day", "the five-day move past its 95th percentile"),
                            ("band", "a band crossing"),
                            ("compression", "compression to the six-month floor"))
           if tr["arms"][n]["fired"]]
    names = {"one_day": "the one-day move", "five_day": "the five-day move past its "
             "95th percentile (20 years)", "band": f"a band crossing ({tr['prior_band']} "
             f"to {tr['band']})", "compression": "compression to the six-month floor"}
    return (f"VIX {lv['value']:.2f} ({fmt_signed(ch['points'])} points, "
            f"{fmt_signed(ch['pct'], 1, '%')}). Level: {lv.get('pct_5y')} percentile "
            f"(5y), {lv.get('pct_20y')} (20y). Change: {ch.get('pct_5y')} percentile "
            f"(5y), {ch.get('pct_20y')} (20y). "
            + ("Event: " + "; ".join(names[w] for w in why) + "." if why
               else "No event."))


# ---------------------------------------------------------------------------
# ST-R6.52b -- the lenses
# ---------------------------------------------------------------------------
def lens_spot_vol(vix, spx, day, cfg) -> dict:
    n = int(cfg["lenses"]["beta_sessions"])
    vd = dict(vix)
    sd = dict(spx)
    days = [d for d in sorted(sd) if d in vd and d <= day]
    if len(days) < n + 2 or days[-1] != day:
        return {"line": f"awaiting: {n} sessions of SPX and VIX before the session",
                "state": "awaiting"}
    pairs = [((sd[b] / sd[a] - 1.0) * 100.0, vd[b] - vd[a])
             for a, b in zip(days, days[1:])]
    hist, (s_pct, v_pts) = pairs[-(n + 1):-1], pairs[-1]
    beta = ols_slope([x for x, _ in hist], [y for _, y in hist])
    if beta is None:
        return {"line": "awaiting: the beta has no variance", "state": "awaiting"}
    expl = beta * s_pct
    share = (expl / v_pts) if v_pts else None
    resid = v_pts - expl
    return {"beta": beta, "spx_pct": s_pct, "vix_points": v_pts, "explained": expl,
            "share": share, "residual": resid, "state": "computed",
            "line": (f"SPX {fmt_signed(s_pct, 2, '%')} at the trailing {n}-day beta of "
                     f"{beta:.2f} VIX points per 1% explains {fmt_signed(expl)} of the "
                     f"{fmt_signed(v_pts)}-point VIX move "
                     f"({'n/a' if share is None else f'{share * 100:.0f}%'}); the residual "
                     f"{fmt_signed(resid)} points is the vol bid beyond spot")}


def lens_term(series, day, cfg) -> dict:
    names = (("vix9d", "VIX9D"), ("vix", "VIX"), ("vix3m", "VIX3M"), ("vix6m", "VIX6M"))
    vals = {k: _val(series.get(k) or [], day) for k, _ in names}
    if any(vals[k][0] is None for k, _ in names):
        miss = [lab for k, lab in names if vals[k][0] is None]
        return {"line": f"awaiting: {', '.join(miss)} not stored for the session "
                        f"(the basket adds ^VIX9D and ^VIX6M; their history needs the "
                        f"backfill)", "state": "awaiting"}
    ch = {k: (v - p if p is not None else None) for k, (v, p) in vals.items()}
    lc = cfg["lenses"]
    d9, d6 = ch["vix9d"], ch["vix6m"]
    front = (d9 is not None and d6 is not None
             and d9 - d6 >= float(lc["front_led_points"]))
    whole = (d9 and d6 is not None and d9 * d6 > 0
             and abs(d6) >= float(lc["whole_curve_share"]) * abs(d9))
    ratio = vals["vix3m"][0] / vals["vix"][0]
    pr = (vals["vix3m"][1] / vals["vix"][1]
          if vals["vix3m"][1] and vals["vix"][1] else None)
    state = "contango" if ratio > 1.0 else "backwardation" if ratio < 1.0 else "flat"
    shape = ("front-led" if front and not whole else "whole-curve" if whole else
             "mixed")
    curve = ", ".join(f"{lab} {vals[k][0]:.2f} ({fmt_signed(ch[k])})" for k, lab in names)
    return {"levels": {k: v[0] for k, v in vals.items()}, "changes": ch, "shape": shape,
            "ratio_3m": ratio, "ratio_3m_prior": pr, "contango": state, "state": "computed",
            "line": (f"{curve}: {shape}; VIX3M/VIX {ratio:.3f}"
                     + (f" from {pr:.3f}" if pr else "") + f", {state}")}


def lens_tail(series, day, cfg) -> dict:
    v, v0 = _val(series.get("vix") or [], day)
    vv, vv0 = _val(series.get("vvix") or [], day)
    sk, sk0 = _val(series.get("skew") or [], day)
    if None in (v, v0, vv, vv0, sk, sk0):
        return {"line": "awaiting: VVIX or SKEW not stored for the session",
                "state": "awaiting"}
    lv, lvv, lsk = (math.log(v / v0) * 100, math.log(vv / vv0) * 100,
                    math.log(sk / sk0) * 100)
    return {"vix_log": lv, "vvix_log": lvv, "skew_log": lsk, "vvix_over_vix": vv / v,
            "state": "computed",
            "line": (f"VVIX {vv:.1f} ({fmt_signed(lvv, 1, '%')} log) and SKEW {sk:.1f} "
                     f"({fmt_signed(lsk, 1, '%')} log) against the VIX's "
                     f"{fmt_signed(lv, 1, '%')} log; VVIX/VIX {vv / v:.2f}")}


def lens_cross(series, day, cfg) -> dict:
    lc = cfg["lenses"]
    mv, mv0 = _val(series.get("move") or [], day)
    hy, hy0 = _val(series.get("hy_oas") or [], day)
    dv = _val(series.get("dvol_btc") or [], day)[0]
    parts, sysm = [], False
    if mv is not None and mv0:
        lm = math.log(mv / mv0) * 100
        parts.append(f"MOVE {mv:.1f} ({fmt_signed(lm, 1, '%')} log)")
        sysm |= lm >= float(lc["systemic_move_log_pct"])
    else:
        parts.append("MOVE not stored for the session")
    if hy is not None and hy0 is not None:
        bp = (hy - hy0) * 100
        parts.append(f"HY OAS {hy:.2f}% ({fmt_signed(bp, 0, ' bp')})")
        sysm |= bp >= float(lc["systemic_hy_bp"])
    else:
        parts.append("HY OAS not stored for the session")
    parts.append(f"crypto DVOL {dv:.1f}" if dv is not None
                 else "crypto DVOL awaiting (Tranche A, deribit.dvol_btc)")
    parts.append("G10 FX vol: a listed gap")
    return {"systemic": sysm, "state": "computed",
            "line": "; ".join(parts) + f": {'systemic' if sysm else 'equity-specific'}"}


def lens_dealer(profile: Optional[dict], cfg_block: Optional[dict] = None) -> dict:
    from daily_cascade import dealer_block as db                # noqa: PLC0415
    if not profile or profile.get("error"):
        return {"line": "no computed dealer profile for the session", "state": "absent"}
    c = cfg_block if cfg_block is not None else db.config()
    o, spot = profile.get("overall") or {}, profile.get("spot")
    reg = db.regime(o.get("net_gex"), o.get("net_to_gross"), c)
    flip = o.get("gamma_flip")
    side = ("below" if flip and spot < flip else "above") if flip else None
    z = (profile.get("buckets") or {}).get("0dte") or {}
    zline = ("0DTE settled, excluded" if z.get("excluded_from_exposure_aggregates")
             else f"0DTE {db.pct(z.get('share_of_total_abs_gex'))} of |GEX|" if z
             else "no 0DTE bucket")
    vex, chex = o.get("vex_notional_per_volpt"), o.get("chex_notional_per_day")
    return {"state": "computed", "regime": reg,
            "line": (f"{profile.get('symbol')} {db.price(spot)} "
                     + (f"{side} the zero-gamma level {db.price(flip)} "
                        f"({db.dist(flip, spot)})" if flip else "(no zero-gamma level)")
                     + f"; net GEX {db.usd(o.get('dollar_gamma_per_1pct'), True)} per 1%, "
                     f"{reg}; vanna {db.usd(vex)} per vol point and charm "
                     f"{db.usd(chex)} per day (sizes); {zline}. Inferred, not observed")}


def lens_realised(vix, spx, day, cfg) -> dict:
    sd = sorted((d, v) for d, v in spx if d <= day)
    if not sd or sd[-1][0] != day:
        return {"line": "awaiting: no SPX close for the session", "state": "awaiting"}
    closes = [v for _, v in sd]
    v, v0 = _val(vix, day)
    out = {"state": "computed"}
    parts = []
    for w in cfg["lenses"]["realized_windows"]:
        rv = realised(closes[-(w + 1):]) if len(closes) > w else None
        out[f"rv{w}"] = rv
        parts.append(f"{w}-day realised {rv:.1f}%" if rv is not None
                     else f"{w}-day realised n/a")
    rv20 = out.get("rv20")
    rv20p = realised(closes[-22:-1]) if len(closes) > 21 else None
    vrp = (v - rv20) if v is not None and rv20 is not None else None
    vrp0 = (v0 - rv20p) if v0 is not None and rv20p is not None else None
    dv = (vrp - vrp0) if None not in (vrp, vrp0) else None
    read = ("implied running ahead of realised (a fear premium)" if dv is not None and dv > 0
            else "realised catching up with implied" if dv is not None and dv < 0 else "")
    out.update(vrp=vrp, vrp_change=dv,
               line=(", ".join(parts) + f" against the VIX {v:.2f}" if v else ", ".join(parts))
               + (f"; VRP {vrp:.1f} points ({fmt_signed(dv, 1)})" if vrp is not None else "")
               + (f": {read}" if read else ""))
    return out


def lens_breadth(series, day) -> dict:
    ic = _val(series.get("implied_corr") or [], day)[0]
    ds = _val(series.get("dispersion") or [], day)[0]
    if ic is None and ds is None:
        return {"line": "awaiting: item 18's dispersion panel (cboe.cor3m, cboe.dspx; "
                        "session B, st-r4-tranche-1b)", "state": "awaiting"}
    return {"state": "computed",
            "line": (f"implied correlation (COR3M) {ic:.1f}" if ic is not None
                     else "implied correlation awaiting")
            + (f"; dispersion (DSPX) {ds:.1f}" if ds is not None else "; dispersion awaiting")}


def lens_positioning(series, day, cfg) -> dict:
    rows = [(d, v) for d, v in (series.get("cftc_net") or []) if d <= day]
    gap = cfg["lenses"]["gaps"]["etp_vega"]
    if not rows:
        return {"line": f"CFTC VIX futures not stored; {gap}", "state": "awaiting"}
    d, v = rows[-1]
    ch = (v - rows[-2][1]) if len(rows) > 1 else None
    return {"state": "computed", "net": v, "as_of": d,
            "line": (f"CFTC VIX futures, non-commercial net {v:,.0f} contracts (as of {d}, "
                     f"weekly; {fmt_signed(ch, 0)} on the week); {gap}")}


def lens_catalyst(attributions: list[dict], cfg) -> dict:
    mk = {m.lower() for m in cfg["lenses"]["catalyst_markets"]}
    hits = [a for a in attributions if str(a.get("market", "")).lower() in mk]
    if not hits:
        return {"line": "not established", "state": "not established"}
    a = hits[0]
    return {"state": "attributed", "outlet": a["outlet"], "url": a["source_url"],
            "line": f"{a['outlet']} attributed the move to: {a['claim']} (its attribution, "
                    f"not ours)"}


def lenses(series: dict, day: str, cfg: dict, profile: Optional[dict] = None,
           attributions: Optional[list[dict]] = None) -> dict:
    vix, spx = series.get("vix") or [], series.get("spx") or []
    return {"spot_vol": lens_spot_vol(vix, spx, day, cfg),
            "term_structure": lens_term(series, day, cfg),
            "tail": lens_tail(series, day, cfg),
            "cross_asset": lens_cross(series, day, cfg),
            "dealer": lens_dealer(profile),
            "realised": lens_realised(vix, spx, day, cfg),
            "breadth": lens_breadth(series, day),
            "positioning": lens_positioning(series, day, cfg),
            "catalyst": lens_catalyst(attributions or [], cfg)}


def lens_table(ls: dict) -> dict:
    return {"columns": ["Lens (inferred where dealer)", "Reading"],
            "rows": [[LENS_TITLES[k], ls[k]["line"]] for k in LENS_ORDER]}


# ---------------------------------------------------------------------------
# ST-R6.52d -- the base rate
# ---------------------------------------------------------------------------
def _bucket(tr: dict, cfg: dict) -> Optional[tuple]:
    b = cfg["base_rate"]
    pct, pts = tr["change"]["pct"], tr["change"]["points"]
    t = cfg["trigger"]
    if pct is not None and abs(pct) >= float(t["one_day_pct"]):
        edges = list(b["pct_buckets"]) + [float("inf")]
        for lo, hi in zip(edges, edges[1:]):
            if lo <= abs(pct) < hi:
                return ("pct", lo, hi)
    if abs(pts) >= float(t["one_day_points"]):
        edges = list(b["points_buckets"]) + [float("inf")]
        for lo, hi in zip(edges, edges[1:]):
            if lo <= abs(pts) < hi:
                return ("pts", lo, hi)
    return None


def base_rate(vix: list[tuple[str, float]], spx: list[tuple[str, float]], tr: dict,
              cfg: dict, bands: list[dict]) -> dict:
    """Forward SPX and VIX after prior one-day moves of the same direction and
    size from the same level band, from the stored history up to the event."""
    day = tr["day"]
    bk = _bucket(tr, cfg) if tr.get("arms") else None
    if bk is None:
        return {"n": 0, "line": "base rate: the event is not a one-day move of the "
                                "registered size (the other arms carry no base rate in v1)"}
    sd = dict(spx)
    vs = [(d, v) for d, v in vix if d <= day]
    days = [d for d, _ in vs]
    vals = [v for _, v in vs]
    up = tr["change"]["points"] > 0
    band = tr["band"]
    fwd = [int(x) for x in cfg["base_rate"]["forward_sessions"]]
    out = {f: {"spx": [], "vix": []} for f in fwd}
    n = 0
    for i in range(1, len(vals) - max(fwd)):
        if days[i] >= day:
            break
        pts, pct = vals[i] - vals[i - 1], (vals[i] / vals[i - 1] - 1) * 100
        if (pts > 0) != up or band_of(vals[i], bands) != band:
            continue
        kind, lo, hi = bk
        x = abs(pct) if kind == "pct" else abs(pts)
        if not (lo <= x < hi):
            continue
        if days[i] not in sd:
            continue
        n += 1
        for f in fwd:
            j = i + f
            if days[j] in sd:
                out[f]["spx"].append((sd[days[j]] / sd[days[i]] - 1) * 100)
            out[f]["vix"].append(vals[j] - vals[i])

    def med(xs):
        s = sorted(xs)
        return None if not s else (s[len(s) // 2] if len(s) % 2 else
                                   (s[len(s) // 2 - 1] + s[len(s) // 2]) / 2)
    res = {"n": n, "bucket": bk, "band": band, "direction": "up" if up else "down",
           "forward": {f: {"spx_median_pct": med(v["spx"]), "vix_median_points": med(v["vix"]),
                           "spx_up_share": (sum(1 for x in v["spx"] if x > 0) / len(v["spx"])
                                            if v["spx"] else None)}
                       for f, v in out.items()}}
    unit = "%" if bk[0] == "pct" else " points"
    hi_s = "+" if bk[2] == float("inf") else f"–{bk[2]:g}"
    head = (f"base rate (the box's history, {vs[0][0] if vs else '—'} to the day before): "
            f"{n} prior {res['direction']} moves of {bk[1]:g}{hi_s}{unit} in the "
            f"{band} band")
    if n < int(cfg["base_rate"]["min_n"]):
        res["line"] = head + f"; n={n}, too few to read."
        return res
    parts = [f"{f} sessions on, SPX median {fmt_signed(r['spx_median_pct'], 2, '%')} "
             f"(up in {r['spx_up_share'] * 100:.0f}%), VIX median "
             f"{fmt_signed(r['vix_median_points'])} points"
             for f, r in res["forward"].items() if r["spx_median_pct"] is not None]
    res["line"] = head + f" (n={n}): " + "; ".join(parts) + "."
    return res


# ---------------------------------------------------------------------------
# ST-R6.52c -- the block
# ---------------------------------------------------------------------------
def consequence(tr: dict, cfg: dict) -> str:
    bc = cfg["book_c"]
    v = tr["level"]["value"]
    pct = tr["change"]["pct"] or 0.0
    holds = v >= float(bc["vix_level"]) or pct >= float(bc["vix_up_pct"])
    return (f"Regime: the XIII band is {tr['band']}"
            + (f" (from {tr['prior_band']})" if tr["prior_band"] != tr["band"] else "")
            + ". Book C: " + (f"the protocol's VIX condition holds (VIX {v:.2f}, "
                              f"{fmt_signed(pct, 1, '%')}): {bc['rule']}" if holds else
                              f"the protocol's VIX condition does not hold (VIX "
                              f"{v:.2f} under {bc['vix_level']:g}, "
                              f"{fmt_signed(pct, 1, '%')} under +{bc['vix_up_pct']:g}%)")
            + ". Printed, not applied.")


def complacency_line(tr: dict) -> str:
    low = tr["arms"]["compression"]["six_month_low"]
    return (f"Complacency: the VIX has held within 5% of its six-month low "
            f"({low:.2f}) for three sessions -- the condition the Concentration & "
            f"Complacency overlay's VIX input reads; the overlay is designed, not built.")


def evaluate(series: dict, day: str, cfg: Optional[dict] = None,
             profile: Optional[dict] = None, attributions: Optional[list] = None,
             bands: Optional[list] = None) -> dict:
    """The session's full read: the trigger, and when it fires the lenses, the
    consequence, the base rate and (compression) the complacency line."""
    cfg = cfg or config()
    bands = bands if bands is not None else level_bands()
    tr = trigger(series.get("vix") or [], day, cfg, bands)
    out: dict[str, Any] = {"day": day, "trigger": tr, "fired": tr["fired"],
                           "trigger_line": trigger_line(tr)}
    if not tr["fired"]:
        return out
    ls = lenses(series, day, cfg, profile, attributions)
    out.update(lenses=ls, table=lens_table(ls), consequence=consequence(tr, cfg),
               base_rate=base_rate(series.get("vix") or [], series.get("spx") or [],
                                   tr, cfg, bands))
    if tr["arms"]["compression"]["fired"]:
        out["complacency"] = complacency_line(tr)
    return out


def block(ev: dict) -> Optional[dict]:
    """The Mechanics sub-section for a fired event, or None (silent)."""
    if not ev.get("fired"):
        return None
    lines = [ev["trigger_line"], ev["consequence"], ev["base_rate"]["line"]]
    if ev.get("complacency"):
        lines.append(ev["complacency"])
    return {"title": "Volatility event", "table": ev["table"], "lines": lines}


def facts(ev: dict) -> dict:
    """What the paragraph may cite (the existing narrative step, its audits)."""
    if not ev.get("fired"):
        return {}
    return {"trigger": ev["trigger_line"], "lenses": {LENS_TITLES[k]: ev["lenses"][k]["line"]
                                                      for k in LENS_ORDER},
            "consequence": ev["consequence"], "base_rate": ev["base_rate"]["line"]}


# ---------------------------------------------------------------------------
# The 12:30 gate (upward only), for daily_cascade/midday_gate.py
# ---------------------------------------------------------------------------
def vol_gate(ctx: dict) -> dict:
    """A one-day VIX rise of 15% or 3 points by 12:30 opens the alert-only slot
    with the trigger line and the lenses computable intraday: spot-vol, term
    structure, dealer positioning. `ctx["quotes"]` holds the 12:30 quotes
    (^VIX, ^VIX9D, ^VIX3M, ^VIX6M, ^GSPC); `ctx["vol_series"]` the stored
    history to the prior close. Upward only (RULED)."""
    cfg = ctx.get("vol_cfg") or config()
    q = ctx.get("quotes") or {}
    ser = ctx.get("vol_series") or {}
    gid = "vol_event_up"
    now = q.get("^VIX")
    prior = (ser.get("vix") or [(None, None)])[-1][1]
    if now is None or not prior:
        return {"id": gid, "open": False, "line": None,
                "why": "no 12:30 VIX quote" if now is None else "no prior VIX close"}
    pts, pct = now - prior, (now / prior - 1) * 100
    m = cfg["midday"]
    if not (round(pct, 9) >= float(m["up_pct"]) or round(pts, 9) >= float(m["up_points"])):
        return {"id": gid, "open": False, "line": None,
                "why": f"VIX {fmt_signed(pts)} points ({fmt_signed(pct, 1, '%')}) by 12:30"}
    day = ctx.get("day") or "intraday"
    intr = {k: list(v) for k, v in ser.items()}
    for key, sym in (("vix", "^VIX"), ("vix9d", "^VIX9D"), ("vix3m", "^VIX3M"),
                     ("vix6m", "^VIX6M"), ("spx", "^GSPC")):
        if q.get(sym) is not None:
            intr.setdefault(key, []).append((day, float(q[sym])))
    sv = lens_spot_vol(intr.get("vix") or [], intr.get("spx") or [], day, cfg)
    ts = lens_term(intr, day, cfg)
    dl = lens_dealer(ctx.get("midday"))
    line = (f"VIX {now:.2f} at 12:30, {fmt_signed(pts)} points ({fmt_signed(pct, 1, '%')}) "
            f"on the prior close {prior:.2f}: the 12:30 vol gate opens; the full block "
            f"follows at 16:45. Spot-vol: {sv['line']}. Term structure: {ts['line']}. "
            f"Dealer positioning: {dl['line']}.")
    return {"id": gid, "open": True, "line": line, "why": "threshold crossing"}


# ---------------------------------------------------------------------------
# The store: read the series; the event day, the compression flag, the ledger
# ---------------------------------------------------------------------------
def _series(st, key: str, cutoff: str, instrument: Optional[str] = None) -> list:
    by: dict[str, float] = {}
    for r in st.as_of(key, cutoff, instrument):
        if r.get("value_num") is not None:
            by[str(r["observed_at"])[:10]] = float(r["value_num"])
    return sorted(by.items())


def read_series(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    k = cfg["keys"]
    vix = dict(_series(st, k["vix_history"], cutoff))
    vix.update(dict(_series(st, k["vix"], cutoff)))
    out = {"vix": sorted(vix.items())}
    for name in ("vix9d", "vix3m", "vix6m", "vvix", "skew", "move", "hy_oas", "spx",
                 "implied_corr", "dispersion", "dvol_btc"):
        out[name] = _series(st, k[name], cutoff)
    out["cftc_net"] = _series(st, k["cftc_net"], cutoff, "VIX")
    return out


def attributions_for(day: str, cutoff: str, path: Optional[str] = None) -> list[dict]:
    """The scan's stored press attributions published on the session (ET)."""
    try:
        from . import voices                                    # noqa: PLC0415
        nxt = (dt.date.fromisoformat(day) + dt.timedelta(days=1)).isoformat()
        with voices.VoicesStore(path, readonly=True) as vs:
            return vs.attributions(as_of=cutoff, since=day, until=nxt)
    except Exception:                                           # noqa: BLE001
        return []


def event_rows(ev: dict, now: str) -> list[dict]:
    """The event day (every session, fired or not), the compression flag, and a
    ledger row for a fired event -- each observed on the session, available now."""
    day = ev["day"]
    rows = [{"registry_key": EVENT_KEY, "instrument": None, "observed_at": day,
             "available_at": now, "value": json.dumps(_slim(ev), sort_keys=True,
                                                      default=str),
             "source": "vol_event"}]
    comp = ((ev["trigger"].get("arms") or {}).get("compression") or {}).get("fired")
    if comp is not None:
        rows.append({"registry_key": COMPRESSION_KEY, "instrument": None,
                     "observed_at": day, "available_at": now,
                     "value": 1.0 if comp else 0.0, "source": "vol_event"})
    if ev.get("fired"):
        rows.append(ledger_row(ev, now, None))
    return rows


def _slim(ev: dict) -> dict:
    return {k: ev.get(k) for k in ("day", "fired", "trigger_line", "consequence",
                                   "complacency")} | {
        "table": ev.get("table"), "base_rate": (ev.get("base_rate") or {}).get("line"),
        "arms": {k: v.get("fired") for k, v in (ev["trigger"].get("arms") or {}).items()},
        "direction": ev["trigger"].get("direction")}


def ledger_row(ev: dict, now: str, outcomes: Optional[dict]) -> dict:
    body = {"day": ev["day"], "direction": ev["trigger"].get("direction"),
            "arms": {k: v.get("fired") for k, v in (ev["trigger"].get("arms") or {}).items()},
            "vix": ev["trigger"]["level"]["value"],
            "attribution": {LENS_TITLES[k]: ev["lenses"][k]["line"] for k in LENS_ORDER},
            "outcomes": outcomes}
    return {"registry_key": LEDGER_KEY, "instrument": ev["day"], "observed_at": ev["day"],
            "available_at": now, "value": json.dumps(body, sort_keys=True, default=str),
            "source": "vol_event"}


def outcomes(day: str, vix: list, spx: list, cfg: Optional[dict] = None) -> dict:
    """The realised 5- and 20-session SPX and VIX outcomes after `day`; a
    horizon not yet stored is None (unresolved)."""
    cfg = cfg or config()
    sd, vd = dict(spx), dict(vix)
    days = sorted(d for d in sd if d >= day)
    out: dict[str, Optional[float]] = {}
    for f in cfg["base_rate"]["forward_sessions"]:
        f = int(f)
        if len(days) > f and day in sd and days[f] in vd and day in vd:
            out[f"spx_{f}d_pct"] = round((sd[days[f]] / sd[day] - 1) * 100, 3)
            out[f"vix_{f}d_points"] = round(vd[days[f]] - vd[day], 3)
        else:
            out[f"spx_{f}d_pct"] = out[f"vix_{f}d_points"] = None
    out["resolved"] = all(v is not None for v in out.values())
    return out


def ledger_status(rows: list[dict], cfg: Optional[dict] = None) -> str:
    cfg = cfg or config()
    n = len(rows)
    res = sum(1 for r in rows if (r.get("outcomes") or {}).get("resolved"))
    need = int(cfg["ledger"]["rights_after_events"])
    return (f"event ledger: {n} events, {res} resolved; no modifier right before "
            f"{need} events")


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    from . import observations, session                         # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.vol_event")
    ap.add_argument("cmd", choices=["show", "seed", "resolve"])
    ap.add_argument("--date", default=None)
    a = ap.parse_args(argv)
    cfg = config()
    now = session.utc_iso()
    day = a.date or session.session_date()
    if a.cmd == "resolve":
        with observations.ObservationStore() as st:
            ser = read_series(st, now, cfg)
            wrote = []
            for r in st.as_of(LEDGER_KEY, now):
                body = json.loads(r["value_text"])
                if (body.get("outcomes") or {}).get("resolved"):
                    continue
                oc = outcomes(body["day"], ser["vix"], ser["spx"], cfg)
                if oc != body.get("outcomes"):
                    body["outcomes"] = oc
                    wrote.append({"registry_key": LEDGER_KEY, "instrument": body["day"],
                                  "observed_at": body["day"], "available_at": now,
                                  "value": json.dumps(body, sort_keys=True),
                                  "source": "vol_event"})
            if wrote:
                st.write_many(wrote)
        print(f"resolved rows written: {len(wrote)}")
        return 0
    # Both read the store as of NOW and every lens stops at the day itself: the
    # seed is a one-off written today from stored data (Batch 9, the placement
    # block), so rows backfilled since -- ^VIX9D, ^VIX6M -- count, and the row is
    # stamped available when written, never earlier.
    with observations.ObservationStore() as st:
        ser = read_series(st, now, cfg)
    ev = evaluate(ser, day, cfg, attributions=attributions_for(day, now))
    print(ev["trigger_line"])
    if ev.get("fired"):
        for row in ev["table"]["rows"]:
            print(f"  {row[0]}: {row[1]}")
        print(ev["consequence"])
        print(ev["base_rate"]["line"])
    if a.cmd == "seed":
        if not ev.get("fired"):
            print("no event fired on that session: nothing seeded")
            return 1
        row = ledger_row(ev, now, outcomes(day, ser["vix"], ser["spx"], cfg))
        with observations.ObservationStore() as st:
            st.write_many([row])
        print(f"seeded {LEDGER_KEY} for {day}")
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
