"""
Prediction markets, read: forms, attention shocks, disagreements, the gate. (6d)

    from altdata import prediction_markets as pm
    blk = pm.block(as_of, session_day, fed_path=..., store=st)

READS ONLY. The pull is altdata/sources/prediction_markets.py; this turns what is
stored into the figures the reports print, under the spec's rules as recorded on
2 Oct 2026 (config/prediction_markets.yaml):

  FORMS        probability; its 1-, 5- and 20-session changes in points
               (derived.probability_points); volume; the bias-zone flag
               (p < 10% or > 90%: use changes, distrust levels -- Part 27).
  SHOCK        |1-session change| >= 10 points. CONFIRMED when the other venue's
               market on the same question moved the same way by at least half as
               much, or the market's volume is at or above the threshold;
               otherwise UNCONFIRMED (Part 27's quarantine).
  DISAGREEMENT venue vs the fed-funds-implied probability >= 15 points on the
               same meeting; venue vs our scenario weight >= 20 points where a
               market is mapped to one in config (none is, yet).
  OUTAGE       a venue with nothing stored at this session prints "as of <date>".
  GATE         the calibration-archive gate's progress, for the Monthly.

NO RIGHT BEYOND THESE. Nothing here writes a scenario weight, a narrative, a theme
or a book, and nothing is a trigger; the What's-priced depth rule reads the
shock count to decide how DEEP a section prints, which is a reading rule.
"""

from __future__ import annotations

import datetime as dt
import json
import re
from typing import Any, Optional

from . import derived, observations, session
from .sources import prediction_markets as src


def _close_cutoff(day: dt.date) -> str:
    """16:15 ET on `day`, in UTC: a session's pulls are the ones at or before it."""
    tz = session._eastern_tz()
    t = dt.datetime.combine(day, dt.time(16, 15), tzinfo=tz)
    # In the store's canonical form (microseconds), so a string comparison with
    # a stored available_at is a comparison of instants.
    return observations.canonical_instant(t.astimezone(dt.timezone.utc).isoformat())


def _back_sessions(day: dt.date, n: int) -> dt.date:
    d = day
    for _ in range(n):
        d = session.previous_trading_session(d)
    return d


def _value_at(rows: list[dict], cutoff: str) -> Optional[float]:
    v = None
    for r in rows:
        if str(r["available_at"]) <= cutoff and r.get("value_num") is not None:
            v = r["value_num"]
    return v


def _live(r: dict) -> bool:
    return "backfill" not in str(r.get("source") or "") and \
        r.get("availability_kind") != "reconstructed"


def classify_fomc(question: str, outcome: str) -> Optional[str]:
    """hike / hold / cut for a decision market's outcome, from its own words."""
    t = f"{question} {outcome}".lower()
    if re.search(r"\bno change\b|\bhold\b|\bmaintain|\bunchanged|\b0 ?bps\b|hike rates by 0bps",
                 t):
        return "hold"
    if re.search(r"\bhike|\bincrease|\braise", t):
        return "hike"
    if re.search(r"\bcut|\bdecrease|\blower", t):
        return "cut"
    return None


def load(st: observations.ObservationStore, as_of: Optional[str]) -> list[dict]:
    """Every stored market: its description and its probability history."""
    out = []
    for inst in st.instruments("pm.market"):
        m = st.latest_as_of("pm.market", as_of, inst)
        if not m:
            continue
        try:
            meta = json.loads(m["value_text"])
        except (TypeError, ValueError):
            continue
        hist = sorted(st.as_of("pm.probability", as_of, inst),
                      key=lambda r: str(r["available_at"]))
        vol = st.latest_as_of("pm.volume", as_of, inst)
        out.append({"instrument": inst, **meta, "history": hist,
                    "volume": vol.get("value_num") if vol else None})
    return out


def forms(mk: dict, day: dt.date, cfg: dict, as_of: Optional[str] = None) -> dict:
    """TODAY is the newest value knowable at the run's cutoff (the 16:45 close
    sees the 16:10 pull; a later run the same day sees a later pull); each PRIOR
    session is its own 16:15 close, so a change is always session to session."""
    hist = mk["history"]
    now_cut = observations.canonical_instant(as_of) if as_of else \
        observations.canonical_instant(session.utc_iso(timespec="microseconds"))
    p = _value_at(hist, now_cut)
    last = next((r for r in reversed(hist) if str(r["available_at"]) <= now_cut), None)
    out = {"instrument": mk["instrument"], "venue": mk.get("venue"),
           "watch_id": mk.get("watch_id"), "event_id": mk.get("event_id"),
           "event_title": mk.get("event_title"), "question": mk.get("question"),
           "outcome": mk.get("outcome"), "decision_date": mk.get("decision_date"),
           "close_at": mk.get("close_at"),
           "probability": p, "volume": mk.get("volume"),
           "as_of": str(last["available_at"])[:10] if last else None}
    for n in (cfg.get("rules") or {}).get("change_sessions") or [1, 5, 20]:
        past = _value_at(hist, _close_cutoff(_back_sessions(day, n)))
        out[f"change_{n}s_points"] = derived.probability_points(p, past)
    lo, hi = (cfg.get("rules") or {}).get("bias_zone") or [0.1, 0.9]
    out["bias_zone"] = p is not None and (p < lo or p > hi)
    out["stale"] = out["as_of"] is not None and out["as_of"] < day.isoformat()
    return out


def shocks(rows: list[dict], cfg: dict) -> list[dict]:
    r = cfg.get("rules") or {}
    th = float(r.get("attention_shock_points") or 10)
    share = float(r.get("shock_confirm_cross_venue_share") or 0.5)
    vmin = float(r.get("shock_confirm_min_volume_usd") or 1e6)
    out = []
    for x in rows:
        c = x.get("change_1s_points")
        if c is None or abs(c) < th or x.get("stale"):
            continue
        peers = [y for y in rows if y["venue"] != x["venue"]
                 and y.get("watch_id") == x.get("watch_id")
                 and y.get("decision_date") == x.get("decision_date")
                 and _same_side(x, y)]
        cross = any((y.get("change_1s_points") or 0) * c > 0
                    and abs(y["change_1s_points"]) >= share * abs(c) for y in peers)
        deep = (x.get("volume") or 0) >= vmin
        out.append({**{k: x.get(k) for k in ("instrument", "venue", "watch_id",
                                             "event_id", "event_title", "question",
                                             "outcome", "probability",
                                             "change_1s_points", "volume",
                                             "decision_date", "close_at")},
                    "state": "CONFIRMED" if (cross or deep) else "UNCONFIRMED",
                    "confirmed_by": ("the other venue" if cross else
                                     "volume" if deep else None)})
    # ONE SHOCK PER VENUE EVENT. A decision event's outcomes are one belief split
    # across legs: hold -12 and hike +12 are the same move said twice, so the
    # event's largest leg stands for it.
    best: dict = {}
    for sh in out:
        k = (sh["venue"], sh.get("event_id") or sh["instrument"])
        if k not in best or abs(sh["change_1s_points"]) > abs(best[k]["change_1s_points"]):
            best[k] = sh
    return list(best.values())


def _same_side(a: dict, b: dict) -> bool:
    if a.get("watch_id") == "fomc_decision":
        return classify_fomc(a.get("question") or "", a.get("outcome") or "") == \
            classify_fomc(b.get("question") or "", b.get("outcome") or "")
    return True


def _snap_meeting(day: str, meetings: list) -> str:
    """A venue's date to the FOMC decision day it means. Polymarket dates a
    decision market by its end (the day after); Kalshi by the decision itself.
    Snapped within two days to the claims registry's decision days, so one
    meeting is one row; a date near no meeting is left as the venue gave it."""
    d = dt.date.fromisoformat(day[:10])
    near = [m for m in meetings if abs((m - d).days) <= 2]
    return min(near, key=lambda m: abs((m - d).days)).isoformat() if near else day[:10]


def fomc_venue_odds(rows: list[dict], meetings: Optional[list] = None) -> dict:
    """{meeting date: {venue: {hike, hold, cut}}} in 0..1, summed per side.

    Each side is the SUM of the venue's prices for that side's outcomes, read as
    the venue quotes them -- last trades on separate contracts, not normalised,
    so a venue's three sides need not sum to one."""
    if meetings is None:
        try:
            from . import fed_funds                            # noqa: PLC0415
            meetings = fed_funds.meeting_days()
        except Exception:                                     # noqa: BLE001
            meetings = []
    out: dict[str, dict] = {}
    for x in rows:
        if x.get("watch_id") != "fomc_decision" or x.get("probability") is None:
            continue
        side = classify_fomc(x.get("question") or "", x.get("outcome") or "")
        day = x.get("decision_date")
        if not side or not day:
            continue
        day = _snap_meeting(day, meetings)
        v = out.setdefault(day, {}).setdefault(x["venue"], {"hike": 0.0, "hold": 0.0,
                                                           "cut": 0.0})
        v[side] += x["probability"]
    return out


def _near(day_a: str, day_b: str, slack: int = 2) -> bool:
    return abs((dt.date.fromisoformat(day_a[:10]) -
                dt.date.fromisoformat(day_b[:10])).days) <= slack


def disagreements(rows: list[dict], fed_path: Optional[dict], cfg: dict,
                  scenario_weights: Optional[dict] = None) -> dict:
    r = (cfg.get("rules") or {}).get("disagreement_points") or {}
    th_ff = float(r.get("venue_vs_fed_funds_implied") or 15)
    th_sc = float(r.get("venue_vs_scenario_weight") or 20)
    out: dict[str, Any] = {"fed_funds": [], "scenario": [], "notes": []}
    odds = fomc_venue_odds(rows)
    if not fed_path or not fed_path.get("meetings"):
        out["notes"].append("venue vs fed funds: no rate path stored")
    else:
        for m in fed_path["meetings"]:
            implied = {"hike": 0.0, "hold": 0.0, "cut": 0.0}
            implied[m["direction"]] = m["move_probability_25bp"]
            implied["hold"] = 1.0 - m["move_probability_25bp"] if m["direction"] != \
                "hold" else 1.0
            for day, by_venue in odds.items():
                if not _near(day, m["meeting"]):
                    continue
                for venue, v in by_venue.items():
                    # LEGS NORMALISED TO 100% (T2.1 ruling): separate contracts'
                    # last prices need not sum to one; the rule compares the
                    # venue's odds as a distribution. The printed figures stay
                    # as quoted, with the sum noted beside them.
                    # Only a BOOK can be normalised: the hold leg and at least one
                    # move leg quoted. A lone leg (a venue listing only "25 bps
                    # increase") is compared as quoted -- scaling 5% of a one-leg
                    # book to 100% would invent a distribution.
                    tot = v["hike"] + v["hold"] + v["cut"]
                    is_book = v["hold"] > 0 and (v["hike"] > 0 or v["cut"] > 0)
                    norm = {k: (v[k] / tot if is_book and tot > 0 else v[k])
                            for k in v}
                    for side in ("hike", "cut"):
                        gap = derived.probability_points(norm[side], implied[side])
                        if gap is not None and abs(gap) >= th_ff:
                            out["fed_funds"].append({
                                "meeting": m["meeting"], "venue": venue, "side": side,
                                "venue_probability": round(norm[side], 3),
                                "venue_quoted": round(v[side], 3),
                                "legs_sum": round(tot, 3),
                                "fed_funds_implied": round(implied[side], 3),
                                "gap_points": gap, "threshold_points": th_ff})
    smap = cfg.get("scenario_map") or {}
    if not smap:
        out["notes"].append("venue vs scenario weight: no venue market is mapped to "
                            "a scenario in config/prediction_markets.yaml")
    for inst, claim in smap.items():
        x = next((y for y in rows if y["instrument"] == inst), None)
        w = (scenario_weights or {}).get(claim)
        gap = derived.probability_points(x.get("probability") if x else None, w)
        if gap is not None and abs(gap) >= th_sc:
            out["scenario"].append({"instrument": inst, "scenario": claim,
                                    "venue_probability": x["probability"],
                                    "scenario_weight": w, "gap_points": gap,
                                    "threshold_points": th_sc})
    return out


def gate_progress(st: observations.ObservationStore, as_of: Optional[str],
                  cfg: dict) -> dict:
    """The calibration-archive gate (spec v1.1 as recorded), condition by condition."""
    g = cfg.get("calibration_gate") or {}
    days, shocks_n = set(), 0
    pts = float(g.get("qualifying_shock_points") or 10)
    for inst in st.instruments("pm.probability"):
        rows = [r for r in st.as_of("pm.probability", as_of, inst) if _live(r)]
        per_day: dict[str, float] = {}
        for r in sorted(rows, key=lambda r: str(r["available_at"])):
            per_day[str(r["available_at"])[:10]] = r["value_num"]
            days.add(str(r["available_at"])[:10])
        vals = [per_day[k] for k in sorted(per_day)]
        shocks_n += sum(1 for a, b in zip(vals, vals[1:])
                        if abs(derived.probability_points(b, a) or 0) >= pts)
    conds = [
        {"condition": "live snapshot days", "have": len(days),
         "need": int(g.get("live_snapshot_days") or 90)},
        {"condition": f"qualifying shocks (>= {pts:g} points, live rows)",
         "have": shocks_n, "need": int(g.get("qualifying_shocks") or 20)},
        {"condition": "venue shown to lead asset prices net of costs",
         "have": "not evaluated (the study is not built)", "need": "shown"},
        {"condition": "consecutive Monthly calibration parts",
         "have": 0, "need": int(g.get("consecutive_monthly_calibration_parts") or 2)},
    ]
    for c in conds:
        c["met"] = isinstance(c["have"], int) and c["have"] >= c["need"]
    return {"conditions": conds, "met": all(c["met"] for c in conds),
            "right": "confidence-modification: NOT BUILT, and may not be proposed "
                     "until every condition is met"}


def block(session_day: str, as_of: Optional[str] = None,
          fed_path: Optional[dict] = None, store=None,
          scenario_weights: Optional[dict] = None) -> dict:
    """Everything the close prints about the venues, from the store."""
    cfg = src.load_config()
    day = dt.date.fromisoformat(session_day)
    own = store is None
    st = store or observations.ObservationStore()
    try:
        mks = load(st, as_of)
        rows = [forms(m, day, cfg, as_of) for m in mks]
    finally:
        if own:
            st.close()
    rows = [r for r in rows if r["probability"] is not None]
    venues = {}
    for v in ("kalshi", "polymarket"):
        vr = [r for r in rows if r["venue"] == v]
        newest = max((r["as_of"] for r in vr if r["as_of"]), default=None)
        venues[v] = {"markets": len(vr), "as_of": newest,
                     "outage": newest is None or newest < session_day}
    return {"session": session_day, "config_version": cfg.get("version"),
            "legs_sum_band": (cfg.get("rules") or {}).get("legs_sum_band"),
            "markets": rows, "venues": venues,
            "watch": {w["id"]: [r for r in rows if r.get("watch_id") == w["id"]]
                      for w in cfg.get("watch_list") or []},
            "discovery": [r for r in rows if str(r.get("watch_id") or "")
                          .startswith("discovery:")],
            "shocks": shocks(rows, cfg),
            "disagreements": disagreements(rows, fed_path, cfg, scenario_weights),
            "fomc_odds": fomc_venue_odds(rows)}
