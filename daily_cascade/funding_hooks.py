"""
ST-10's 12:30 hooks for ST-5's two tells (the signal-triage order's section 7,
"Daily 12:30 alert-only"; a43-render, 18 Oct 2026), registered in
daily_cascade/midday_gate.py's GATES.

    yen_unwind(ctx)   SR-2's unwind tell on the 12:30 USDJPY quote
    deval_trip(ctx)   SR-4's tell's two tracked legs on today's fix and the 12:30
                      CNH and CNY quotes
    context(quotes)   the stored series both read, as of now (the capture's)

EACH GATE is a pure function of ctx, closed with its reason when it cannot be
read, open only on its declared trigger (config/st10_lines.yaml; ST-5's
thresholds in config/funding_currency.yaml, session-set). A closed gate writes
nothing; the slot calls no model either way. Display and modifier only.

THE DEVALUATION LINE PRINTS ITS TWO TRACKED LEGS AND NO VERDICT WORD while the
third leg is not tracked (ruling 6 of 18 Oct 2026): it opens when both tracked
legs hold, and says so leg by leg.
"""

from __future__ import annotations

import logging
import statistics
from typing import Optional

log = logging.getLogger(__name__)


def _q(ctx: dict, sym: str) -> Optional[float]:
    v = (ctx.get("quotes") or {}).get(sym)
    return float(v) if v else None


def yen_unwind(ctx: dict) -> dict:
    from altdata import funding_currency as fc                  # noqa: PLC0415
    gid = "yen_unwind"
    f = ctx.get("funding") or {}
    q = _q(ctx, "JPY=X")
    px, rv = f.get("usdjpy") or [], f.get("rvol") or []
    y = fc.config()["yen"]
    n, med = int(y["unwind_sessions"]), int(y["vol_median_sessions"])
    if not q:
        return {"id": gid, "open": False, "line": None, "why": "no 12:30 USDJPY quote"}
    if len(px) < n or len(rv) < med + 1:
        return {"id": gid, "open": False, "line": None,
                "why": "too little stored USDJPY history"}
    base_day, base = px[-n]
    move = 100.0 * (q / base - 1.0)
    vol_day, vol = rv[-1]
    m = statistics.median(v for _, v in rv[-med - 1:-1])
    ratio = vol / m if m else None
    if move > float(y["unwind_move_pct"]) or ratio is None \
            or ratio < float(y["vol_spike_ratio"]):
        return {"id": gid, "open": False, "line": None,
                "why": f"USDJPY {move:+.2f}% against {base_day}; vol {ratio or 0:.2f}x"}
    line = (f"USDJPY at 12:30: {q:,.2f}, {move:+.1f}% against the close {n} sessions "
            f"back ({base_day}); its 20-session vol {vol:.1f}% at the {vol_day} close, "
            f"{ratio:.1f}x its {med}-session median. The yen unwind tell on the 12:30 "
            f"quote; display only (SR-2's gate failed).")
    return {"id": gid, "open": True, "line": line, "why": "the declared trigger",
            "values": {"quote": q, "move_pct": move, "base_day": base_day, "vol": vol,
                       "vol_day": vol_day, "ratio": ratio, "sessions": n, "median": med}}


def deval_trip(ctx: dict) -> dict:
    from altdata import funding_currency as fc                  # noqa: PLC0415
    from altdata.sources import cfets                           # noqa: PLC0415
    gid = "deval_trip"
    f = ctx.get("funding") or {}
    day = ctx.get("day")
    cnh, cny = _q(ctx, "CNH=X"), _q(ctx, "CNY=X")
    fix, dev, gap = f.get("fix_today"), list(f.get("dev") or []), list(f.get("gap") or [])
    prev_cny = f.get("cny_prev_close")
    if not (cnh and cny):
        return {"id": gid, "open": False, "line": None, "why": "no 12:30 CNH or CNY quote"}
    if not fix or not prev_cny:
        return {"id": gid, "open": False, "line": None,
                "why": "no fix stored for the session, or no previous onshore close"}
    dev.append((day, cfets.gap_bp(fix, prev_cny), day))
    gap.append((day, cfets.gap_bp(cnh, cny), day))
    cfg = fc.config()
    legs = fc.tell_legs(dev, gap, cfg["yuan"])
    lg = legs[-1] if legs else None
    if not lg or lg["day"] != day:
        return {"id": gid, "open": False, "line": None,
                "why": "too few observations to read the legs"}
    if not (lg["leg1"] and lg["leg2"]):
        return {"id": gid, "open": False, "line": None,
                "why": f"leg 1 {'held' if lg['leg1'] else 'not held'}, leg 2 "
                       f"{'held' if lg['leg2'] else 'not held'}"}
    y = cfg["yuan"]
    line = (f"Devaluation tell at 12:30: {fc.legs_tracked(cfg)} of {fc.LEGS_TOTAL} legs "
            f"tracked, both held. Leg 1, the fix's lean gone: 5-observation mean "
            f"{lg['lean_bp']:+.0f} bp (held at or above {y['lean_gone_bp']:+.0f} bp). "
            f"Leg 2, the CNH-CNY gap wide and widening: {lg['gap_bp']:+.0f} bp, "
            f"{lg['widen_bp']:+.0f} bp over {y['gap_widen_obs']} observations (held at "
            f"{y['gap_weak_bp']:+.0f} and {y['gap_widen_bp']:+.0f} bp). Leg 3, state banks "
            f"selling dollars: NOT TRACKED (rule 30; by-hand key {fc.THIRD_LEG_KEY}). No "
            f"verdict prints while a leg is not tracked.")
    return {"id": gid, "open": True, "line": line, "why": "the declared trigger",
            "values": {"lean_bp": lg["lean_bp"], "gap_bp": lg["gap_bp"],
                       "widen_bp": lg["widen_bp"], "tracked": fc.legs_tracked(cfg),
                       "total": fc.LEGS_TOTAL, "obs": y["gap_widen_obs"],
                       "lean_gone": y["lean_gone_bp"], "gap_weak": y["gap_weak_bp"],
                       "gap_widen": y["gap_widen_bp"], "lean_obs": y["lean_obs"],
                       "rule": 30}}


def context(day: str, now: str, db_path: Optional[str] = None) -> dict:
    """The stored inputs: USDJPY closes and realized vol, the yuan's stored fix
    deviations and offshore gaps, today's fix, the previous onshore close."""
    from altdata import observations                            # noqa: PLC0415
    from altdata.absorption import series                       # noqa: PLC0415
    out: dict = {}
    try:
        with observations.ObservationStore(db_path) as st:
            px = [(d, v) for d, v, _ in series(st, "yfinance.mkt_usdjpy", now) if d < day]
            rv = [(d, v) for d, v, _ in series(st, "calc.usdjpy_rvol_20d", now) if d < day]
            dev = [(d, v, a) for d, v, a in series(st, "calc.cny_fix_dev", now) if d < day]
            gap = [(d, v, a) for d, v, a in series(st, "calc.cnh_cny_bp", now) if d < day]
            fix = [(d, v) for d, v, _ in series(st, "cfets.cny_fix", now) if d == day]
            cny = [(d, v) for d, v, _ in series(st, "yfinance.mkt_usdcny", now) if d < day]
        out = {"usdjpy": px[-300:], "rvol": rv[-300:], "dev": dev[-60:], "gap": gap[-60:],
               "fix_today": fix[-1][1] if fix else None,
               "cny_prev_close": cny[-1][1] if cny else None}
    except Exception:                                           # noqa: BLE001
        log.warning("the 12:30 funding context faulted", exc_info=True)
    return {"funding": out}
