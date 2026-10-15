"""
THE STORE-WIDE MOVE SCREEN, AND THE EM SCREEN ON TOP OF IT.
(Audit #4 Part III, Category 1 items 1 and 5; SR-46 b-d, ruled 6 Oct 2026.)

    python -m altdata.move_screen compute [--day 2026-10-09]   # print, write nothing
    python -m altdata.move_screen write   [--day 2026-10-09]   # store the session's result
    python -m altdata.move_screen skipped                      # the series too short to screen

Config: config/move_screen.yaml. The calendar template: config/em_calendar.yaml.

THE SCREEN. Every daily series the registry declares and the store holds is
screened -- no list of series lives here. For each, the 1-day and 5-day change,
in the unit its registry entry gives it, as a z against the series' own
five-year history of such changes; past 2.5 sigma, two-sided, it is a flag.

  THE UNIT RULE. A price moves by its log change; a rate, a spread, a
  percentage or a probability by its simple difference. Read from the
  registry's delta unit (altdata/derived.py): "percent" is a price, "bps" and
  "pp" are rates and spreads, a fraction is a probability, and every other raw
  unit (a count, a balance, a ratio) moves by its difference. A key in config's
  `basis_pins` keeps its pinned basis whatever its units: the volatility
  indexes and SKEW move in points and are screened on log changes.

  THE FALSE-FLAG BASE RATE. Among the series' own past prints past 2.5 sigma
  over the five years -- of the horizon that flagged today -- the share whose
  move was at least half reversed within five sessions, printed "false flag
  k/N". The past prints are identified against the same five-year window's
  spread (in-sample); the stored daily result is what accrues point-in-time.

  SKIPPED. A series with fewer than 500 observations is not screened; the
  result names it.

WHAT IT SUBSUMES (no separate code path for any of these):
  SR-35        the 10-year's two-week and one-month change as a z on a twenty-
               year window, printed as the 10-year row's companion at 2 sigma
  SR-46(a)     the EM basket's members are store series like any other
  PM shock     a prediction-market contract's 5-day move past 2.5 sigma, against
               its family's pooled 5-day moves, printed with its family name

THE EM SCREEN (SR-46 b-d), over config's twenty members (ten currencies, ten
country ETFs), each move read in STRESS terms (a currency per dollar rising, an
ETF falling):
  (b) DISPERSION AGAINST CO-MOVEMENT. One country alone past 2.5 sigma is
      idiosyncratic -- "a candidate for the narrative register", printed only;
      the register write is the operator's. The basket moving together is
      systemic -- "dollar/risk-off; Factor IV's business".
  (c) EM SPREADS. ICE BofA EM corporate and EM high-yield OAS with their
      percentiles over the stored history and five years (FRED serves three
      years of each, so the "five-year" window prints what it really is). A
      report-only "EM leg" line; no overlay wiring (the HY Spread Acceleration
      overlay is not built in this repo).
  (d) THE CONTAGION RULE. A single-country shock is a state: its shock date and
      a five-session window. It earns a Weekly or Monthly line only if it passes
      to the basket (a systemic session) or to EM spreads (a 5-day widening at
      2 sigma) inside the window; until then it is a daily-close line only.

STORED, so the base rates accrue point-in-time and the scorecard can grade the
flag later: `screen.move` (one row per flagged series, instrument = the series),
`screen.move_summary`, `screen.em` and `screen.em_contagion` (instrument = the
country), each observed_at = the session, available_at = the compute instant.
The reports READ the stored result; with none stored (CI, a laptop) they compute
it in memory and write nothing.
"""

from __future__ import annotations

import datetime as dt
import json
import math
import statistics
from pathlib import Path
from typing import Any, Optional

import yaml

from . import derived, observations, session

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "config" / "move_screen.yaml"
CALENDAR_PATH = REPO / "config" / "em_calendar.yaml"
KEYS = ("screen.move", "screen.move_summary", "screen.em", "screen.em_contagion")


def load_config(path: Optional[Path] = None) -> dict:
    with open(path or CONFIG_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


# ---------------------------------------------------------------------------
# Units and series
# ---------------------------------------------------------------------------
def unit_rule(key: str, cfg: Optional[dict] = None) -> str:
    """"log" for a price, "diff" for everything else (rates, spreads,
    percentages, probabilities, counts) -- the registry's delta unit decides,
    unless config's `basis_pins` names the key: the volatility indexes and SKEW
    print their change in points and are screened on log changes (ruled 15 Oct
    2026), so a unit change cannot move the screen's basis."""
    pins = (cfg if cfg is not None else load_config()).get("basis_pins") or {}
    if key in pins:
        return str(pins[key])
    return "log" if derived.delta_unit_for(key)[0] == "percent" else "diff"


def change(a: float, b: float, rule: str) -> Optional[float]:
    """b against a: a log change, or a difference."""
    if rule == "log":
        return math.log(b / a) if a and b and a > 0 and b > 0 else None
    return b - a


def daily_points(rows: list[dict], cutoff: Optional[str] = None) -> list[tuple[str, float]]:
    """One value per observed day -- the latest revision knowable -- oldest first."""
    by: dict[str, float] = {}
    for r in sorted(rows, key=lambda r: (str(r.get("observed_at")),
                                         str(r.get("available_at") or ""))):
        v = r.get("value_num")
        if v is None or (isinstance(v, float) and not math.isfinite(v)):
            continue
        if cutoff and str(r.get("available_at") or "") > cutoff \
                and r.get("available_at") is not None:
            continue
        by[str(r["observed_at"])[:10]] = float(v)
    return sorted(by.items())


def is_daily(key: str) -> bool:
    e = derived.registry_entry(key)
    return (e.get("freq") == "daily"
            or (e.get("freq") is None and e.get("native_horizon") == "daily"))


def screened_series(st, cfg: dict) -> list[tuple[str, Optional[str]]]:
    """(key, instrument) for every daily registry series the store holds."""
    pre = tuple(cfg.get("exclude_prefixes") or ())
    suf = tuple(cfg.get("exclude_suffixes") or ())
    out = []
    for key in sorted(st.keys()):
        if key.startswith(pre) or key.endswith(suf) or not is_daily(key):
            continue
        if str(derived.registry_entry(key).get("units") or "") in ("label", "text"):
            continue
        insts = st.instruments(key)
        if insts:
            out += [(key, i) for i in insts]
        else:
            out.append((key, None))
    return out


def series_id(key: str, inst: Optional[str]) -> str:
    return f"{key}@{inst}" if inst else key


def label_of(key: str, inst: Optional[str] = None) -> str:
    try:
        from . import labels                                    # noqa: PLC0415
        lab = labels.metric(key)
    except Exception:                                           # noqa: BLE001
        lab = key
    return f"{lab} ({inst})" if inst else lab


# ---------------------------------------------------------------------------
# One series
# ---------------------------------------------------------------------------
def _stats(xs: list[float]) -> Optional[tuple[float, float]]:
    if len(xs) < 2:
        return None
    sd = statistics.pstdev(xs)
    return (statistics.fmean(xs), sd) if sd > 0 else None


def screen_points(pts: list[tuple[str, float]], rule: str, cfg: dict,
                  history_days: Optional[int] = None,
                  horizons: Optional[list] = None) -> Optional[dict]:
    """The screen for one series whose last point is today: per horizon, the
    change, its z against the window's changes of that horizon (today's
    excluded), and the false-flag base rate of the window's past prints.
    None when the series is too short (`min_observations`)."""
    if len(pts) < int(cfg.get("min_observations") or 500):
        return None
    sig = float(cfg.get("sigma") or 2.5)
    share = float(cfg.get("reversal_share") or 0.5)
    rev = int(cfg.get("reversal_sessions") or 5)
    end = dt.date.fromisoformat(pts[-1][0])
    lo = (end - dt.timedelta(days=int(history_days or cfg.get("history_days") or 1826))
          ).isoformat()
    vals = [v for _, v in pts]
    days = [d for d, _ in pts]
    out: dict[str, Any] = {"day": days[-1], "level": vals[-1], "n": len(pts),
                           "rule": rule}
    for h in horizons or cfg.get("horizons") or [1, 5]:
        h = int(h)
        hist = []                                   # (index of the end, change)
        for i in range(h, len(vals) - 1):
            if days[i - h] < lo:
                continue
            c = change(vals[i - h], vals[i], rule)
            if c is not None:
                hist.append((i, c))
        now = change(vals[-1 - h], vals[-1], rule) if len(vals) > h else None
        st_ = _stats([c for _, c in hist])
        if now is None or st_ is None:
            out[f"z{h}"] = None
            continue
        mu, sd = st_
        z = (now - mu) / sd
        # The false-flag base rate: past prints past sigma, each with `rev`
        # sessions after it known by today; reversed when, within them, the level
        # came back at least `share` of the move.
        k = n = 0
        for i, c in hist:
            if abs((c - mu) / sd) < sig or i + rev > len(vals) - 2:
                continue
            n += 1
            for j in range(1, rev + 1):
                back = change(vals[i + j], vals[i], rule)
                if back is not None and math.copysign(1, c) * back >= share * abs(c):
                    k += 1
                    break
        out[f"z{h}"] = round(z, 2)
        out[f"change{h}"] = now
        out[f"false_flag{h}"] = {"k": k, "n": n}
        out[f"n_changes{h}"] = len(hist)
    zs = [abs(out.get(f"z{h}") or 0) for h in (1, 5)]
    out["max_abs_z"] = max(zs)
    out["flagged"] = out["max_abs_z"] >= sig
    lead = 1 if abs(out.get("z1") or 0) >= abs(out.get("z5") or 0) else 5
    out["lead_horizon"] = lead
    out["false_flag"] = out.get(f"false_flag{lead}") or {"k": 0, "n": 0}
    return out


def flag_line(f: dict) -> str:
    """"<series> <+x.x>σ 1-day / <+x.x>σ 5-day · false flag k/N"."""
    def z(v):
        return "n/a" if v is None else f"{v:+.1f}σ"
    ff = f.get("false_flag") or {}
    return (f"{f['label']} {z(f.get('z1'))} 1-day / {z(f.get('z5'))} 5-day · "
            f"false flag {ff.get('k', 0)}/{ff.get('n', 0)}")


# ---------------------------------------------------------------------------
# The whole store
# ---------------------------------------------------------------------------
def _points(st, key: str, inst: Optional[str], cutoff: Optional[str],
            day: str) -> list[tuple[str, float]]:
    return [p for p in daily_points(st.as_of(key, cutoff, inst)) if p[0] <= day]


def companion_10y(st, day: str, cutoff: Optional[str], cfg: dict) -> Optional[dict]:
    """SR-35: the 10-year's two-week and one-month change as a z on a twenty-
    year window, in basis points; printed at `sigma` or more."""
    c = cfg.get("companion_10y") or {}
    pts = _points(st, c.get("key") or "fred.yield_10y", None, cutoff, day)
    if len(pts) < 30:
        return None
    sessions = c.get("sessions") or {"two-week": 10, "one-month": 21}
    res = screen_points(pts, "diff", {**cfg, "min_observations": 30,
                                      "sigma": c.get("sigma") or 2.0},
                        history_days=int(c.get("history_days") or 7305),
                        horizons=list(sessions.values()))
    if not res:
        return None
    parts, hit = [], False
    for name, h in sessions.items():
        z = res.get(f"z{h}")
        if z is None:
            continue
        hit |= abs(z) >= float(c.get("sigma") or 2.0)
        parts.append(f"{name} {res[f'change{h}'] * 100:+.0f} bp ({z:+.1f}σ)")
    if not parts:
        return None
    return {"label": c.get("label") or "10-year Treasury", "printed": hit,
            "line": (f"{c.get('label') or '10-year Treasury'}, the speed of the move: "
                     + "; ".join(parts) + " on a twenty-year window"),
            **{f"z{h}": res.get(f"z{h}") for h in sessions.values()}}


def pm_flags(st, day: str, cutoff: Optional[str], cfg: dict) -> tuple[list, list]:
    """The prediction-market shock flag: each live contract's 5-day move in
    points, as a z against its family's pooled 5-day moves. (flags, families
    too short to pool)."""
    pc = cfg.get("prediction_markets") or {}
    key, h = pc.get("key") or "pm.probability", int(pc.get("horizon") or 5)
    fams: dict[str, list] = {}
    meta: dict[str, dict] = {}
    for inst in st.instruments(key):
        m = st.latest_as_of("pm.market", cutoff, inst)
        try:
            mm = json.loads(m["value_text"]) if m else {}
        except (TypeError, ValueError):
            mm = {}
        meta[inst] = mm
        fams.setdefault(str(mm.get("watch_id") or "unlisted"), []).append(inst)
    flags, short = [], []
    sig = float(cfg.get("sigma") or 2.5)
    for fam, insts in sorted(fams.items()):
        pooled, latest = [], []
        for inst in insts:
            pts = _points(st, key, inst, cutoff, day)
            vals = [v * 100.0 for _, v in pts]
            pooled += [vals[i] - vals[i - h] for i in range(h, len(vals) - 1)]
            if pts and pts[-1][0] == day and len(vals) > h:
                latest.append((inst, vals[-1] - vals[-1 - h]))
        if len(pooled) < int(pc.get("min_pooled") or 500):
            short.append(f"{fam} ({len(pooled)} pooled 5-day moves)")
            continue
        s = _stats(pooled)
        if not s:
            continue
        for inst, c in latest:
            z = (c - s[0]) / s[1]
            if abs(z) >= sig:
                mm = meta.get(inst) or {}
                flags.append({"series": f"{key}@{inst}", "kind": "prediction_market",
                              "label": f"{mm.get('event_title') or fam}: "
                                       f"{mm.get('question') or inst}",
                              "family": fam, "z1": None, "z5": round(z, 2),
                              "change5": c, "max_abs_z": abs(z), "flagged": True,
                              "false_flag": {"k": 0, "n": 0}, "lead_horizon": 5})
    return flags, short


def screen(st, day: str, cutoff: Optional[str] = None,
           cfg: Optional[dict] = None) -> dict:
    """The session's screen, in memory: every flag ranked by |z|, the series
    skipped, the 10-year companion, and the EM layer."""
    cfg = cfg or load_config()
    flags, skipped, n = [], [], 0
    for key, inst in screened_series(st, cfg):
        pts = _points(st, key, inst, cutoff, day)
        if not pts or pts[-1][0] != day and pts[-1][0] < _prior_session(day):
            # Not updated for the session (a lagging or retired series): nothing to
            # screen today, and not a skip.
            continue
        res = screen_points(pts, unit_rule(key, cfg), cfg)
        if res is None:
            skipped.append({"series": series_id(key, inst), "n": len(pts)})
            continue
        n += 1
        if res["flagged"]:
            flags.append({"series": series_id(key, inst), "label": label_of(key, inst),
                          "kind": "series", **res})
    pmf, pm_short = pm_flags(st, day, cutoff, cfg)
    flags += pmf
    flags.sort(key=lambda f: -f["max_abs_z"])
    em = em_screen(st, day, cutoff, cfg, flags)
    return {"day": day, "config_version": cfg.get("version"), "screened": n,
            "flags": flags, "skipped": skipped, "pm_families_too_short": pm_short,
            "companion_10y": companion_10y(st, day, cutoff, cfg), "em": em,
            "contagion": contagion(st, day, cutoff, cfg, em)}


def _prior_session(day: str) -> str:
    try:
        return session.previous_trading_session(day).isoformat()
    except Exception:                                           # noqa: BLE001
        return (dt.date.fromisoformat(day) - dt.timedelta(days=4)).isoformat()


# ---------------------------------------------------------------------------
# The EM screen (SR-46 b-d)
# ---------------------------------------------------------------------------
def em_member_moves(st, day: str, cutoff: Optional[str], cfg: dict) -> list[dict]:
    """Each member's 1- and 5-day z, in stress terms (FX up = stress; ETF down =
    stress)."""
    out = []
    for m in (cfg.get("em") or {}).get("members") or []:
        pts = _points(st, m["key"], None, cutoff, day)
        res = screen_points(pts, unit_rule(m["key"], cfg), cfg) if pts else None
        # FRED's H.10 currencies post weekly, a week of dailies at a time: a
        # member is read on its latest point within `member_max_lag_days`, and
        # carries that date.
        lag = int((cfg.get("em") or {}).get("member_max_lag_days") or 7)
        fresh = bool(pts) and pts[-1][0] >= (dt.date.fromisoformat(day)
                                             - dt.timedelta(days=lag)).isoformat()
        if not res or not fresh:
            out.append({**m, "available": False, "n": len(pts),
                        "as_of": pts[-1][0] if pts else None})
            continue
        sign = 1.0 if m.get("kind") == "fx" else -1.0
        out.append({**m, "available": True, "as_of": pts[-1][0],
                    "z1": res.get("z1"), "z5": res.get("z5"),
                    "stress1": None if res.get("z1") is None else sign * res["z1"],
                    "stress5": None if res.get("z5") is None else sign * res["z5"],
                    "flagged": res["flagged"], "false_flag": res["false_flag"]})
    return out


def classify(members: list[dict], cfg: dict) -> dict:
    """(b): dispersion against co-movement. Systemic when the basket moves
    together; idiosyncratic when one country alone is past sigma."""
    e = cfg.get("em") or {}
    live = [m for m in members if m.get("available") and m.get("stress5") is not None]
    if len(live) < 4:
        return {"state": "insufficient", "members": len(live)}
    zs = [m["stress5"] for m in live]
    med = statistics.median(zs)
    same = sum(1 for z in zs if z * med > 0) / len(zs) if med else 0.0
    disp = statistics.pstdev(zs)
    countries = sorted({m["country"] for m in live if m.get("flagged")})
    systemic = (same >= float(e.get("co_movement_share") or 0.8)
                and abs(med) >= float(e.get("systemic_median_z") or 1.0))
    if systemic:
        state = "systemic"
    elif len(countries) == 1:
        state = "idiosyncratic"
    elif countries:
        state = "mixed"
    else:
        state = "quiet"
    return {"state": state, "members": len(live), "median_stress_z5": round(med, 2),
            "co_movement": round(same, 2), "dispersion": round(disp, 2),
            "countries_flagged": countries,
            "direction": "stress" if med > 0 else "relief"}


def em_line(c: dict) -> Optional[str]:
    """The EM line in What doesn't fit, or None on a quiet session."""
    if c.get("state") == "systemic":
        return (f"EM basket moving together ({round(100 * c['co_movement'])}% of members "
                f"the same way, median {c['median_stress_z5']:+.1f}σ 5-day in "
                f"{c['direction']} terms): systemic -- dollar/risk-off; Factor IV's "
                f"business.")
    if c.get("state") == "idiosyncratic":
        return (f"{c['countries_flagged'][0]} alone past 2.5σ while the EM basket did "
                f"not move with it: idiosyncratic -- a candidate for the narrative "
                f"register.")
    if c.get("state") == "mixed":
        return (f"{len(c['countries_flagged'])} EM countries past 2.5σ "
                f"({', '.join(c['countries_flagged'])}) without the basket moving "
                f"together.")
    return None


def em_spreads(st, day: str, cutoff: Optional[str], cfg: dict) -> list[dict]:
    """(c): each EM spread's level, its 5-day change and its percentiles over
    the stored history and over five years -- each window as it really is."""
    e = cfg.get("em") or {}
    out = []
    for s in e.get("spreads") or []:
        pts = _points(st, s["key"], None, cutoff, day)
        if not pts:
            out.append({**s, "available": False})
            continue
        vals = [v for _, v in pts]
        lo = (dt.date.fromisoformat(pts[-1][0])
              - dt.timedelta(days=int(e.get("spread_percentile_days") or 1826))).isoformat()
        five = [v for d, v in pts if d >= lo]
        res = screen_points(pts, "diff", {**cfg, "min_observations": 60},
                            horizons=[5])
        out.append({**s, "available": True, "level": vals[-1], "as_of": pts[-1][0],
                    "first": pts[0][0], "n": len(vals),
                    "pct_full": derived.percentile_of(vals, vals[-1]),
                    "pct_5y": derived.percentile_of(five, vals[-1]),
                    "five_year_complete": pts[0][0] <= lo,
                    "change5_bp": None if len(vals) < 6 else (vals[-1] - vals[-6]) * 100,
                    "z5": (res or {}).get("z5")})
    return out


def em_leg_line(spreads: list[dict]) -> Optional[str]:
    """The report-only "EM leg" line for Plumbing & rates."""
    parts = []
    for s in spreads:
        if not s.get("available"):
            continue
        win = ("five years" if s.get("five_year_complete")
               else f"since {s['first']}, the history FRED serves")
        parts.append(f"{s['label']} {s['level']:.2f}% ({_ord(s['pct_full'])} percentile "
                     f"{win}"
                     + (f"; {_ord(s['pct_5y'])} of five years" if s.get("five_year_complete")
                        else "") + ")")
    return ("EM leg: " + "; ".join(parts) + ".") if parts else None


def _ord(p: Optional[float]) -> str:
    if p is None:
        return "n/a"
    n = int(round(p))
    suf = "th" if 11 <= n % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def em_screen(st, day: str, cutoff: Optional[str], cfg: dict,
              flags: Optional[list] = None) -> dict:
    members = em_member_moves(st, day, cutoff, cfg)
    c = classify(members, cfg)
    spreads = em_spreads(st, day, cutoff, cfg)
    return {**c, "line": em_line(c), "members_detail": members, "spreads": spreads,
            "em_leg_line": em_leg_line(spreads),
            "missing": [m["key"] for m in members if not m.get("available")]}


# ---------------------------------------------------------------------------
# (d) The contagion rule
# ---------------------------------------------------------------------------
def sessions_back(day: str, n: int) -> list[str]:
    """`day` and the n sessions before it, oldest first."""
    out, d = [day], dt.date.fromisoformat(day)
    for _ in range(n):
        try:
            d = session.previous_trading_session(d)
        except Exception:                                       # noqa: BLE001
            d = d - dt.timedelta(days=1)
            while d.weekday() >= 5:
                d -= dt.timedelta(days=1)
        out.append(d.isoformat())
    return sorted(out)


def contagion_states(days: list[dict], window: int) -> list[dict]:
    """From each session's EM classification and spread z's, oldest first --
    [{day, state, countries_flagged, spread_widening}] -- the shocks and where
    each stands: `watching` inside its window, `passed` (and when) once the
    basket goes systemic or a spread widens, `lapsed` when the window closes
    without either."""
    out = []
    for i, d in enumerate(days):
        if d.get("state") != "idiosyncratic":
            continue
        country = d["countries_flagged"][0]
        after = days[i + 1:i + 1 + window]
        passed = next((a for a in after if a.get("state") == "systemic"
                       or a.get("spread_widening")), None)
        st_ = ("passed" if passed else
               "watching" if len(after) < window else "lapsed")
        out.append({"country": country, "shock_date": d["day"],
                    "window_sessions": window,
                    "window_end": after[-1]["day"] if len(after) == window else None,
                    "status": st_, "passed_on": passed["day"] if passed else None,
                    "passed_to": (None if not passed else
                                  "the basket" if passed.get("state") == "systemic"
                                  else "EM spreads")})
    return out


def contagion(st, day: str, cutoff: Optional[str], cfg: dict,
              today: Optional[dict] = None) -> list[dict]:
    """The states over the last window's sessions, recomputed from the store as
    of `cutoff` -- the shocks still in a window and those that passed or
    lapsed in it."""
    e = cfg.get("em") or {}
    w = int(e.get("contagion_sessions") or 5)
    th = float(e.get("spread_sigma") or 2.0)
    out = []
    for d in sessions_back(day, 2 * w):
        if d == day and today is not None:
            c, sp = today, today.get("spreads") or []
        else:
            c = classify(em_member_moves(st, d, cutoff, cfg), cfg)
            sp = em_spreads(st, d, cutoff, cfg)
        widen = any((s.get("z5") or 0) >= th for s in sp if s.get("available"))
        out.append({"day": d, "state": c.get("state"),
                    "countries_flagged": c.get("countries_flagged") or [],
                    "spread_widening": widen})
    return contagion_states(out, w)


def contagion_line(s: dict, weekly: bool = False) -> Optional[str]:
    """The close prints every shock; the Weekly and Monthly only one that passed."""
    if s["status"] == "passed":
        return (f"{s['country']}: the shock of {s['shock_date']} passed to "
                f"{s['passed_to']} on {s['passed_on']}, inside five sessions -- contagion.")
    if weekly:
        return None
    if s["status"] == "watching":
        return (f"{s['country']}: a single-country shock on {s['shock_date']}; "
                f"watching five sessions for it to pass to the basket or EM spreads.")
    return None


# ---------------------------------------------------------------------------
# The Quarterly's hook (AQ-2): the quarter's EM episodes
# ---------------------------------------------------------------------------
def _quarter_start(day: str) -> str:
    """Three calendar months before `day` (exclusive bound), the day clamped to
    the month's length: the quarter ending at `day`."""
    d = dt.date.fromisoformat(day)
    y, m = (d.year, d.month - 3) if d.month > 3 else (d.year - 1, d.month + 9)
    for dd in range(d.day, 27, -1):
        try:
            return dt.date(y, m, dd).isoformat()
        except ValueError:
            continue
    return dt.date(y, m, min(d.day, 28)).isoformat()


def quarter_episodes(st, now, cfg: Optional[dict] = None) -> list[dict]:
    """The EM basket's episodes past sigma in the quarter ending at `now`, oldest
    first; [] when none. The Quarterly calls this by name (AQ-2 part 2 config).

    Two kinds of row, each {date, series, horizon, z, false_flag,
    classification, contagion_passed} (plus `country`, `kind`):
      member  -- a basket member's store-wide screen flag (|z| >= sigma on its
                 lead horizon), from the stored session result where one exists,
                 else recomputed from the store as of `now`. `date` is the
                 member's own observation date, so a weekly-posted FRED
                 currency is counted once, not on each session that reads it.
                 `classification` is the basket's state that session (systemic,
                 idiosyncratic, mixed); `contagion_passed` is True only for an
                 idiosyncratic shock that passed to the basket or to EM spreads
                 inside its window.
      spread  -- an EM-spread contagion event: the session a single-country
                 shock passed to EM spreads, the spread that widened most, its
                 5-day z. `false_flag` is None (the contagion rule has no base
                 rate); `contagion_passed` is True.
    """
    cfg = cfg or load_config()
    now_s = now.isoformat() if hasattr(now, "isoformat") else str(now)
    day = now_s[:10]
    cutoff = now_s if "T" in now_s else None
    start = _quarter_start(day)
    e = cfg.get("em") or {}
    w = int(e.get("contagion_sessions") or 5)
    th = float(e.get("spread_sigma") or 2.0)
    members = {m["key"]: m for m in e.get("members") or []}
    days = [d for d in sessions_back(day, 70) if d > start]

    hits: dict[str, dict] = {}          # series -> {date: flag row}
    per_day = []
    for d in days:
        stored = read(st, d, cutoff)
        if stored is not None:
            em = stored.get("em") or {}
            flags = [{**f, "country": members[f["series"]]["country"]}
                     for f in stored.get("flags") or [] if f.get("series") in members]
            spreads = em.get("spreads") or []
            state, countries = em.get("state"), em.get("countries_flagged") or []
        else:
            moves = em_member_moves(st, d, cutoff, cfg)
            c = classify(moves, cfg)
            flags = [{"series": m["key"], "day": m["as_of"], "country": m["country"],
                      "z1": m.get("z1"), "z5": m.get("z5"),
                      "false_flag": m.get("false_flag")}
                     for m in moves if m.get("available") and m.get("flagged")]
            spreads = em_spreads(st, d, cutoff, cfg)
            state, countries = c.get("state"), c.get("countries_flagged") or []
        wide = [s for s in spreads
                if s.get("available") and (s.get("z5") or 0) >= th]
        per_day.append({"day": d, "state": state, "countries_flagged": countries,
                        "spread_widening": bool(wide), "widest": max(
                            wide, key=lambda s: s["z5"]) if wide else None})
        for f in flags:
            date = str(f.get("day") or d)[:10]
            if date > start:
                hits.setdefault(f["series"], {}).setdefault(
                    date, {**f, "_session": d, "_state": state})

    # One episode per run of consecutive flagged observations of a series (a
    # shock's 5-day z stays past sigma for the sessions after it): dated at the
    # run's first observation, carrying the run's largest |z|.
    states = contagion_states(per_day, w)
    passed = {(s["country"], s["shock_date"]): s for s in states
              if s["status"] == "passed"}
    out, starts = [], set()
    for series, by_date in hits.items():
        obs = [d for d, _ in daily_points(st.as_of(series, cutoff)) if start < d <= day]
        pos = {d: i for i, d in enumerate(obs)}
        run: list[dict] = []
        for date in sorted(by_date) + [None]:
            f = by_date.get(date) if date else None
            if run and (f is None or pos.get(date, -9) - pos.get(run[-1]["_date"], -9) != 1):
                first = run[0]
                peak = max(((abs(r.get(f"z{h}") or 0), h, r) for r in run for h in (1, 5)),
                           key=lambda t: t[0])
                ep_state = first["_state"]
                starts.add((first["country"], first["_session"]))
                out.append({
                    "date": first["_date"], "series": series, "horizon": peak[1],
                    "z": peak[2].get(f"z{peak[1]}"),
                    "false_flag": peak[2].get("false_flag"),
                    "classification": ep_state,
                    "contagion_passed": (ep_state == "idiosyncratic" and
                                         (first["country"], first["_session"]) in passed),
                    "country": first["country"], "kind": "member"})
                run = []
            if f is not None:
                run.append({**f, "_date": date})
    by_day = {p["day"]: p for p in per_day}
    # One contagion event per episode: the sessions after a shock that its own
    # 5-day run keeps idiosyncratic are not new shocks.
    for key, s in passed.items():
        if s["passed_to"] != "EM spreads" or key not in starts:
            continue
        p = by_day.get(s["passed_on"]) or {}
        top = p.get("widest") or {}
        out.append({"date": s["passed_on"], "series": top.get("key"), "horizon": 5,
                    "z": top.get("z5"), "false_flag": None,
                    "classification": p.get("state"), "contagion_passed": True,
                    "country": s["country"], "kind": "spread",
                    "shock_date": s["shock_date"]})
    out.sort(key=lambda r: (r["date"], r["kind"], str(r["series"])))
    return out


# ---------------------------------------------------------------------------
# The EM calendar (by hand)
# ---------------------------------------------------------------------------
def em_calendar(day: str, path: Optional[Path] = None) -> list[dict]:
    """The quarter's hand-seeded entries, on or after `day`, oldest first."""
    try:
        with open(path or CALENDAR_PATH, encoding="utf-8") as fh:
            cal = yaml.safe_load(fh) or {}
    except OSError:
        return []
    d = dt.date.fromisoformat(day[:10])
    q0 = dt.date(d.year, 3 * ((d.month - 1) // 3) + 1, 1)
    q1 = dt.date(d.year + (q0.month == 10), (q0.month + 2) % 12 + 1, 1)
    out = []
    for e in cal.get("entries") or []:
        try:
            ed = dt.date.fromisoformat(str(e.get("date"))[:10])
        except ValueError:
            continue
        if q0 <= ed < q1 and ed >= d:
            out.append(e)
    return sorted(out, key=lambda e: str(e.get("date")))


def calendar_line(e: dict, pm_prob: Optional[float] = None) -> str:
    return (f"{e['date']}: {e.get('country')} -- {e.get('event')}"
            + (f" (prediction market {round(100 * pm_prob):.0f}%)"
               if pm_prob is not None else "")
            + (f" [{e['source']}]" if e.get("source") else "") + ".")


# ---------------------------------------------------------------------------
# The reports' view: lines, counts, the reference tier
# ---------------------------------------------------------------------------
def report_lines(res: dict, cadence: str = "daily", cfg: Optional[dict] = None) -> dict:
    """{lines, more, reference} for What doesn't fit: the top flags by |z| (the
    10-year's companion beside its row), "n more past 2.5σ -- in the tables",
    and every flag for the reference tier."""
    cfg = cfg or load_config()
    k = int((cfg.get("print_lines") or {}).get(cadence) or 3)
    flags = res.get("flags") or []
    lines = [flag_line(f) for f in flags[:k]]
    comp = res.get("companion_10y") or {}
    if comp.get("printed"):
        at = next((i for i, f in enumerate(flags[:k])
                   if str(f.get("series")).startswith(("fred.yield_10y",
                                                       "yfinance.mkt_tnx"))), None)
        lines.insert(len(lines) if at is None else at + 1, comp["line"] + ".")
    more = max(0, len(flags) - k)
    ref = {"columns": ["Series", "1-day", "5-day", "False flag", "Observations"],
           "rows": [[f["label"],
                     "n/a" if f.get("z1") is None else f"{f['z1']:+.1f}σ",
                     "n/a" if f.get("z5") is None else f"{f['z5']:+.1f}σ",
                     f"{f['false_flag']['k']}/{f['false_flag']['n']}",
                     f.get("n") or "pooled"] for f in flags]}
    return {"lines": lines,
            "more": (f"{more} more past 2.5σ -- in the tables." if more else None),
            "reference": ref}


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------
def to_rows(res: dict, now: str) -> list[dict]:
    day = res["day"]
    base = {"observed_at": day, "available_at": now, "source": "derived_state"}
    rows = []
    for f in res.get("flags") or []:
        keep = {k: v for k, v in f.items() if k not in ("level",)}
        rows.append({**base, "registry_key": "screen.move", "instrument": f["series"],
                     "value": json.dumps(keep, sort_keys=True, default=str)})
    rows.append({**base, "registry_key": "screen.move_summary", "instrument": None,
                 "value": json.dumps({"screened": res["screened"],
                                      "flagged": len(res.get("flags") or []),
                                      "skipped": res.get("skipped") or [],
                                      "pm_families_too_short":
                                          res.get("pm_families_too_short") or [],
                                      "companion_10y": res.get("companion_10y"),
                                      "config_version": res.get("config_version")},
                                     sort_keys=True, default=str)})
    em = {k: v for k, v in (res.get("em") or {}).items() if k != "members_detail"}
    rows.append({**base, "registry_key": "screen.em", "instrument": None,
                 "value": json.dumps(em, sort_keys=True, default=str)})
    for s in res.get("contagion") or []:
        rows.append({**base, "registry_key": "screen.em_contagion",
                     "instrument": f"{s['country']}:{s['shock_date']}",
                     "value": json.dumps(s, sort_keys=True)})
    return rows


def write(st, day: str, cutoff: Optional[str] = None) -> dict:
    res = screen(st, day, cutoff)
    n = st.write_many(to_rows(res, session.utc_iso(timespec="microseconds")))
    return {"day": day, "written": n, "flags": len(res["flags"]),
            "screened": res["screened"], "skipped": len(res["skipped"])}


def read(st, day: str, cutoff: Optional[str] = None) -> Optional[dict]:
    """The stored result for `day` as knowable at `cutoff`, or None."""
    summ = [r for r in st.as_of("screen.move_summary", cutoff)
            if str(r["observed_at"])[:10] == day]
    if not summ:
        return None
    s = json.loads(summ[-1]["value_text"])
    flags = []
    for inst in st.instruments("screen.move"):
        rows = [r for r in st.as_of("screen.move", cutoff, inst)
                if str(r["observed_at"])[:10] == day]
        if rows:
            flags.append(json.loads(rows[-1]["value_text"]))
    flags.sort(key=lambda f: -float(f.get("max_abs_z") or 0))
    em = [r for r in st.as_of("screen.em", cutoff) if str(r["observed_at"])[:10] == day]
    cont = []
    for inst in st.instruments("screen.em_contagion"):
        rows = [r for r in st.as_of("screen.em_contagion", cutoff, inst)
                if str(r["observed_at"])[:10] == day]
        if rows:
            cont.append(json.loads(rows[-1]["value_text"]))
    return {"day": day, "screened": s.get("screened"), "flags": flags,
            "skipped": s.get("skipped") or [],
            "pm_families_too_short": s.get("pm_families_too_short") or [],
            "companion_10y": s.get("companion_10y"),
            "em": json.loads(em[-1]["value_text"]) if em else {},
            "contagion": cont, "stored": True}


def result_for(st, day: str, cutoff: Optional[str] = None) -> Optional[dict]:
    """What a report prints from: the stored result, else computed in memory
    (written by no report). None if both fail -- the report prints without it."""
    try:
        return read(st, day, cutoff) or screen(st, day, cutoff)
    except Exception:                                           # noqa: BLE001
        return None


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    ap = argparse.ArgumentParser(description="The store-wide move screen.")
    ap.add_argument("cmd", choices=("compute", "write", "skipped"))
    ap.add_argument("--day", default=None)
    a = ap.parse_args(argv)
    # The close runs at 16:45, inside the hour last_completed_session() still
    # gives to yesterday: the session is today's, or the last one on the calendar.
    day = a.day or session.last_trading_session(session.session_date()).isoformat()
    with observations.ObservationStore() as st:
        if a.cmd == "write":
            print(json.dumps(write(st, day), indent=2))
            return 0
        res = screen(st, day)
    if a.cmd == "skipped":
        for s in res["skipped"]:
            print(f"{s['series']}: {s['n']} observations")
        for f in res["pm_families_too_short"]:
            print(f"prediction-market family {f}")
        return 0
    for ln in report_lines(res, "weekly")["lines"]:
        print(ln)
    print(f"screened {res['screened']}, flagged {len(res['flags'])}, "
          f"skipped {len(res['skipped'])}; EM: {res['em'].get('state')}")
    return 0


if __name__ == "__main__":                                      # pragma: no cover
    import sys
    raise SystemExit(_main(sys.argv[1:]))
