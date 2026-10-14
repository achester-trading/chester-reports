"""
THE SELLOFF-SHAPE AXIS AND THE SELLOFF'S COMPOSITION (SR-49; signal-triage batch
4, ST4-15), and the four voices adjudicated by the measures. Ruled 6 Oct 2026,
section 4.2.

    python -m altdata.rates_shape show [--as-of ISO]

Config: config/rates_anchors.yaml (`shape`, `selloff`, `voices`). Nothing fetches.

THE SHAPE AXIS
  correlated  every DM yield rising together -- 1994's reaction-function
              repricing: the weekly panel's mean pairwise correlation of weekly
              10-year changes over 13 weeks at or above `correlated_min_corr`,
              and every panel member up over the 13 weeks;
  divergent   the focal sovereign rising while core falls -- 2011's fiscal
              crisis: a focal 10-year up at least `divergent_focal_rise_bp` over
              `focal_months` while the Bund's change is at or below
              `divergent_core_max_bp`;
  mixed       otherwise.
The weekly panel is the daily-filled 10-years (the US, the Bund, the JGB); the
focal test reads the monthly OECD series, which carry no weekly change.

THE COMPOSITION of each 10-year selloff (a rise of at least `min_rise_bp` over
`window_sessions` sessions): what moved -- the 10-year breakeven, the 10-year real
(TIPS) yield, the ACM term premium -- each as its change and its share of the
10-year's, and the label of the largest: breakeven-led, real-yield-led or
term-premium-led. Breakeven plus real is the 10-year (near enough); the term
premium is a different cut of the same move, printed beside them, not added.

THE FOUR VOICES. Each dated claim (batch-4 Appendix B) is read against the measure
that tests it, by a declared rule, and given a verdict: consistent, not
consistent, not settled, not testable yet, or outside these measures. The
disagreement is adjudicated by the axis, not narrated.

NOT THE MARKET-STATE OBJECT. The rates `driver` sub-state was withdrawn on 30 Sep
2026 after failing its calibration gate twice; regime.py does not import this
module and this module writes nothing to the object. Report-only; every line
carries "(descriptive; unvalidated, n=0)".
"""

from __future__ import annotations

import datetime as dt
import json
import statistics
import sys
from itertools import combinations
from typing import Optional

from .rates_anchors import _points, load_config

SHAPES = ("correlated", "divergent", "mixed")
LEADS = {"breakeven": "breakeven-led", "real": "real-yield-led",
         "term_premium": "term-premium-led"}
VERDICTS = ("consistent", "not consistent", "not settled", "not testable yet",
            "outside these measures")


def _weekly(points: list[tuple[str, float]], end: dt.date, weeks: int) -> list[float]:
    """The last value on or before each of `weeks + 1` Fridays to `end`."""
    out = []
    for k in range(weeks, -1, -1):
        d = (end - dt.timedelta(days=7 * k)).isoformat()
        v = [x for day, x in points if day <= d]
        out.append(v[-1] if v else None)
    return out


def _corr(a: list[float], b: list[float]) -> Optional[float]:
    if len(a) < 3 or statistics.pstdev(a) == 0 or statistics.pstdev(b) == 0:
        return None
    ma, mb = statistics.fmean(a), statistics.fmean(b)
    cov = statistics.fmean((x - ma) * (y - mb) for x, y in zip(a, b))
    return cov / (statistics.pstdev(a) * statistics.pstdev(b))


def shape(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg if cfg is not None else load_config()
    sh = cfg.get("shape") or {}
    weeks = int(sh.get("weeks") or 13)
    end = dt.date.fromisoformat(cutoff[:10])
    panel = {}
    for m in sh.get("weekly_panel") or []:
        lv = _weekly(_points(st, m["key"], cutoff), end, weeks)
        if None in lv:
            continue
        panel[m["name"]] = {"changes": [100.0 * (b - a) for a, b in zip(lv, lv[1:])],
                            "total_bp": 100.0 * (lv[-1] - lv[0])}
    corrs = [c for x, y in combinations(sorted(panel), 2)
             if (c := _corr(panel[x]["changes"], panel[y]["changes"])) is not None]
    mean_corr = statistics.fmean(corrs) if corrs else None
    disp = (statistics.pstdev([p["total_bp"] for p in panel.values()])
            if len(panel) >= 2 else None)
    months = int(sh.get("focal_months") or 3)

    def mchange(key: str) -> Optional[float]:
        pts = _points(st, key, cutoff)
        if len(pts) <= months:
            return None
        return 100.0 * (pts[-1][1] - pts[-1 - months][1])
    core = sh.get("core") or {}
    core_ch = mchange(core.get("key", "")) if core else None
    focal = []
    for f in sh.get("focal") or []:
        ch = mchange(f["key"])
        if ch is not None:
            focal.append({"name": f["name"], "change_bp": ch})
    rise = float(sh.get("divergent_focal_rise_bp") or 25)
    core_max = float(sh.get("divergent_core_max_bp") or 0)
    lead = max(focal, key=lambda f: f["change_bp"]) if focal else None
    if lead and core_ch is not None and lead["change_bp"] >= rise and core_ch <= core_max:
        state, why = "divergent", (f"{lead['name']} {lead['change_bp']:+.0f} bp over "
                                   f"{months} months while the Bund moved "
                                   f"{core_ch:+.0f} bp")
    elif len(panel) >= 2 and mean_corr is not None and \
            mean_corr >= float(sh.get("correlated_min_corr") or 0.5) and \
            all(p["total_bp"] > 0 for p in panel.values()):
        state, why = "correlated", (f"weekly changes correlated {mean_corr:.2f} on "
                                    f"average across {len(panel)} markets over "
                                    f"{weeks} weeks, every one higher")
    elif len(panel) < 2 and not focal:
        state, why = None, "too few 10-year series stored to read the shape"
    else:
        state, why = "mixed", ("neither every market rising together nor a focal "
                               "sovereign rising against a falling Bund")
    return {"state": state, "why": why, "mean_corr": mean_corr, "dispersion_bp": disp,
            "panel": {k: round(v["total_bp"], 1) for k, v in panel.items()},
            "focal": focal, "core_change_bp": core_ch, "weeks": weeks}


# ---------------------------------------------------------------------------
# The composition of each selloff
# ---------------------------------------------------------------------------
def selloffs(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    """Every non-overlapping `window_sessions` 10-year rise of at least
    `min_rise_bp` in the last `history_years`, each with what moved."""
    cfg = cfg if cfg is not None else load_config()
    so = cfg.get("selloff") or {}
    w = int(so.get("window_sessions") or 20)
    th = float(so.get("min_rise_bp") or 25)
    since = (dt.date.fromisoformat(cutoff[:10])
             - dt.timedelta(days=365 * int(so.get("history_years") or 5))).isoformat()
    ten = [p for p in _points(st, so["ten_year"], cutoff) if p[0] >= since]
    legs = {k: dict(_points(st, so[k], cutoff))
            for k in ("breakeven", "real", "term_premium")}

    def at(series: dict, day: str) -> Optional[float]:
        ks = [d for d in series if d <= day]
        return series[max(ks)] if ks else None
    out, i = [], w
    while i < len(ten):
        d0, v0 = ten[i - w]
        d1, v1 = ten[i]
        rise = 100.0 * (v1 - v0)
        if rise >= th:
            comp = {}
            for k, s in legs.items():
                a, b = at(s, d0), at(s, d1)
                comp[k] = None if a is None or b is None else 100.0 * (b - a)
            known = {k: v for k, v in comp.items() if v is not None}
            lead = max(known, key=lambda k: known[k]) if known else None
            out.append({"start": d0, "end": d1, "rise_bp": rise,
                        "moves_bp": comp,
                        "shares": {k: (v / rise if v is not None else None)
                                   for k, v in comp.items()},
                        "label": LEADS.get(lead) if lead else "composition not stored"})
            i += w
        else:
            i += 1
    counts = {lab: sum(1 for x in out if x["label"] == lab) for lab in LEADS.values()}
    cur = out[-1] if out and out[-1]["end"] == (ten[-1][0] if ten else None) else None
    return {"episodes": out, "counts": counts, "latest": out[-1] if out else None,
            "current": cur, "window_sessions": w, "min_rise_bp": th}


# ---------------------------------------------------------------------------
# The four voices, adjudicated
# ---------------------------------------------------------------------------
def adjudicate(sh: dict, so: dict, anchors: dict, cfg: Optional[dict] = None
               ) -> list[dict]:
    cfg = cfg if cfg is not None else load_config()
    ten = (anchors.get("inflation") or {}).get("ten_year_pct")
    fis = anchors.get("fiscal") or {}
    out = []
    for v in cfg.get("voices") or []:
        t = v.get("test")
        if t == "shape_correlated":
            m = f"shape axis: {sh.get('state') or 'unread'}"
            verdict = ("not testable yet" if sh.get("state") is None else
                       "consistent" if sh["state"] == "correlated" else
                       "not consistent" if sh["state"] == "divergent" else
                       "not settled")
        elif t == "fiscal_gap_positive":
            if fis.get("state") != "ok" or fis.get("gap_bp") is None:
                m, verdict = "twin-deficit fit: absent", "not testable yet"
            else:
                g = fis["gap_bp"]
                m = f"twin-deficit fit: fitted less paid {g:+.0f} bp"
                verdict = ("consistent" if g >= float(v.get("min_gap_bp") or 25) else
                           "not consistent" if g <= 0 else "not settled")
        elif t == "level_band":
            lo, hi = v.get("band") or [5.0, 5.5]
            led = ((so.get("current") or {}).get("label"))
            if ten is None:
                m, verdict = "10-year: not stored", "not testable yet"
            else:
                m = f"10-year {ten:.2f}%" + (f"; the current selloff {led}" if led else
                                             "; no selloff under way")
                verdict = ("consistent" if lo <= ten <= hi else
                           "consistent" if ten > float(v.get("spiral_above") or hi)
                           and led == "term-premium-led" else
                           "not settled" if ten > hi else "not consistent")
        else:
            m, verdict = "the fed funds path is What's priced's measure", \
                "outside these measures"
        out.append({"voice": v["voice"], "claim": v["claim"], "measure": m,
                    "verdict": verdict})
    return out


def read(st, cutoff: str, anchors: Optional[dict] = None,
         cfg: Optional[dict] = None) -> dict:
    cfg = cfg if cfg is not None else load_config()
    if anchors is None:
        from . import rates_anchors                             # noqa: PLC0415
        anchors = rates_anchors.read(st, cutoff, cfg)
    sh = shape(st, cutoff, cfg)
    so = selloffs(st, cutoff, cfg)
    return {"shape": sh, "selloffs": so, "voices": adjudicate(sh, so, anchors, cfg),
            "tag": cfg.get("tag")}


def shape_line(r: dict) -> str:
    sh, so = r["shape"], r["selloffs"]
    s = (f"Selloff shape: {sh['state']} -- {sh['why']}" if sh.get("state") else
         f"Selloff shape not read: {sh['why']}")
    lt = so.get("latest")
    if lt:
        mv = lt["moves_bp"]
        parts = [f"{k.replace('_', ' ')} {mv[k]:+.0f} bp" for k in
                 ("breakeven", "real", "term_premium") if mv.get(k) is not None]
        s += (f". Latest 10-year selloff ({lt['start']} to {lt['end']}, "
              f"{lt['rise_bp']:+.0f} bp): {lt['label']}"
              + (f" -- {', '.join(parts)}" if parts else ""))
        s += (f"; over the stored five years, {so['counts']['breakeven-led']} "
              f"breakeven-led, {so['counts']['real-yield-led']} real-yield-led, "
              f"{so['counts']['term-premium-led']} term-premium-led")
    else:
        s += ". No 10-year selloff in the stored window"
    return s + f". {r.get('tag') or ''}".rstrip()


def voices_table(r: dict) -> dict:
    return {"columns": ["Voice", "Claim (6 Oct 2026)", "The measure", "Verdict"],
            "rows": [[v["voice"], v["claim"], v["measure"], v["verdict"]]
                     for v in r["voices"]]}


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    from . import observations, session                         # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.rates_shape")
    ap.add_argument("cmd", choices=["show"])
    ap.add_argument("--as-of", default=None)
    a = ap.parse_args(argv)
    with observations.ObservationStore() as st:
        r = read(st, a.as_of or session.utc_iso())
    print(shape_line(r))
    print(json.dumps(r["voices"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
