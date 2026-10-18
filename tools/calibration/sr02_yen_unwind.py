"""
SR-2 -- the yen carry unwind's anatomy at ST-5's thresholds (signal-triage ST-8;
st-t3-calib, 18 Oct 2026).

    python tools/calibration/sr02_yen_unwind.py [--box] [--out DIR] [--date D]

THE REGISTER'S GATE (docs/signal-triage-register.md, SR-2). "Anatomy check on Oct
1998, 2007-08, Jan-Feb 2016, Aug 2024 (narrowing differential + crowded shorts +
vol spike). Pass: all four flagged with <=2 false positives 1998-2026 at the
chosen thresholds. Offline (ST-8); thresholds then set in
config/market_state.yaml."

THE THRESHOLDS ARE ST-5'S (config/funding_currency.yaml, session-set), read from
that file, never chosen here:
  * the differential: US 2-year less the JGB 2-year, its change over
    `front_change_sessions` (60) observations; NARROWING is a change below zero.
  * the vol spike: the unwind tell, USDJPY's `unwind_sessions` (5) change at or
    below `unwind_move_pct` (-3%) while its `vol_sessions` (20) realized vol is
    at least `vol_spike_ratio` (1.5x) its trailing `vol_median_sessions` (250)
    median.
  * crowded shorts: the CFTC yen net non-commercial position's z over
    `pos_z_weeks` (156) reports (`pos_z_min_weeks`, 52, before the first). ST-5
    set no crowding level, so THIS FIRST EDITION PRE-REGISTERS ONE: crowded when
    the lowest z among the reports released in the previous 91 days is at or
    below -1.0 (the fuel is built before the spark, so the read looks back a
    quarter). A report is released the Friday after its Tuesday.

THE FLAG is all three on one session. Flag sessions within 63 sessions of the
previous one are one episode. A window is FLAGGED when an episode has a flag
session inside it; an episode with no flag session inside any window is a FALSE
POSITIVE. The windows, pre-registered: 1998-09-01..1998-11-30, 2007-07-01..
2008-12-31, 2016-01-01..2016-02-29, 2024-07-01..2024-08-31; the false-positive
count runs 1998-01-01 to the data's end.

ON A FAIL the thresholds stay session-set in config/funding_currency.yaml and the
ledger says what each would need: each threshold alone is loosened along a
pre-registered grid, the others held at ST-5's, and the windows flagged and the
false positives at each step are printed.

Sources, keyless: FRED DGS2 and DEXJPUS (the noon New York yen rate, from 1971,
where Yahoo's JPY=X begins in Oct 1996), MoF's JGB 2-year (historical CSV, from
1974), the CFTC's legacy futures-only report through altdata.sources.cftc (yen,
from 1986). None is revised.
"""

from __future__ import annotations

import bisect
import datetime as dt
import math
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import st8_common as C                                           # noqa: E402

ITEM = "SR-2"
WINDOWS = {"Oct 1998": ("1998-09-01", "1998-11-30"),
           "2007-08": ("2007-07-01", "2008-12-31"),
           "Jan-Feb 2016": ("2016-01-01", "2016-02-29"),
           "Aug 2024": ("2024-07-01", "2024-08-31")}
FP_FROM = "1998-01-01"
MAX_FP = 2
CROWD_Z = -1.0
CROWD_DAYS = 91
MERGE = 63
GRID = {"narrow_bp": [0.0, 10.0, 25.0, 50.0, 100.0],
        "crowd_z": [-1.0, -0.5, 0.0, 0.5, 1.0],
        "move_pct": [-3.0, -2.5, -2.0, -1.5, -1.0],
        "vol_ratio": [1.5, 1.3, 1.2, 1.1, 1.0]}


def settings() -> dict:
    from altdata import funding_currency as F
    y = F.config()["yen"]
    return {"front": int(y["front_change_sessions"]), "pos_w": int(y["pos_z_weeks"]),
            "pos_min": int(y["pos_z_min_weeks"]), "move_n": int(y["unwind_sessions"]),
            "move_pct": float(y["unwind_move_pct"]), "vol_n": int(y["vol_sessions"]),
            "vol_med": int(y["vol_median_sessions"]), "vol_ratio": float(y["vol_spike_ratio"]),
            "narrow_bp": 0.0, "crowd_z": CROWD_Z}


def load_public() -> dict:
    from altdata.ledgers import sources as S
    from altdata.sources import cftc, mof
    from altdata.sources._base import http_get_response
    data, _ = http_get_response(mof.URL_HISTORY, timeout=90)
    jgb = sorted((r["observed_at"], float(r["value"])) for r in
                 mof.rows_from_csv(data.decode("utf-8", "replace"), "x", "observed")
                 if r["registry_key"] == "mof.jgb_2y")
    recs = cftc.fetch_records(cftc.URL, {"097741": "JPY"})
    pos = sorted((r["observed_at"][:10], float(r["value"])) for r in
                 cftc.rows_from_records(recs)
                 if r["registry_key"] == "cftc.noncomm_net" and r.get("instrument") == "JPY")
    return {"dgs2": S.fred("DGS2"), "jgb2": jgb, "usdjpy": S.fred("DEXJPUS"), "pos": pos}


# ---------------------------------------------------------------------------
def components(d: dict, s: dict) -> list[dict]:
    """One row per USDJPY session: the 60-session differential change, the
    crowding read, the 5-session move and the vol ratio."""
    jg = dict(d["jgb2"])
    fd = [(day, 100.0 * (v - jg[day])) for day, v in d["dgs2"] if day in jg]
    fd60 = [(fd[i][0], fd[i][1] - fd[i - s["front"]][1]) for i in range(s["front"], len(fd))]
    fdd = [x for x, _ in fd60]
    pos = d["pos"]
    z = []
    for i in range(len(pos)):
        win = [v for _, v in pos[max(0, i - s["pos_w"] + 1):i + 1]]
        if len(win) >= s["pos_min"]:
            sd = statistics.stdev(win)
            if sd:
                rel = (dt.date.fromisoformat(pos[i][0]) + dt.timedelta(days=3)).isoformat()
                z.append((rel, (win[-1] - statistics.fmean(win)) / sd))
    zd = [x for x, _ in z]
    px = d["usdjpy"]
    rv = [None] * len(px)
    for i in range(s["vol_n"], len(px)):
        r = [math.log(b / a) for (_, a), (_, b) in zip(px[i - s["vol_n"]:i], px[i - s["vol_n"] + 1:i + 1])]
        rv[i] = 100.0 * statistics.stdev(r) * math.sqrt(252)
    out = []
    for i in range(len(px)):
        day = px[i][0]
        if i < s["move_n"] or rv[i] is None:
            continue
        prior = [v for v in rv[max(0, i - s["vol_med"]):i] if v is not None]
        if len(prior) < s["vol_med"]:
            continue
        j = bisect.bisect_right(fdd, day) - 1
        lo = (dt.date.fromisoformat(day) - dt.timedelta(days=CROWD_DAYS)).isoformat()
        a, b = bisect.bisect_left(zd, lo), bisect.bisect_right(zd, day)
        out.append({"day": day,
                    "front_60d_bp": fd60[j][1] if j >= 0 else None,
                    "crowd_min_z": min(v for _, v in z[a:b]) if b > a else None,
                    "move_pct": 100.0 * (px[i][1] / px[i - s["move_n"]][1] - 1.0),
                    "vol_ratio": rv[i] / statistics.median(prior)})
    return out


def flagged(r: dict, s: dict) -> bool:
    return (r["front_60d_bp"] is not None and r["front_60d_bp"] < s["narrow_bp"]
            and r["crowd_min_z"] is not None and r["crowd_min_z"] <= s["crowd_z"]
            and r["move_pct"] <= s["move_pct"] and r["vol_ratio"] >= s["vol_ratio"])


def evaluate(rows: list[dict], s: dict) -> dict:
    days = [r["day"] for r in rows]
    on = [i for i, r in enumerate(rows) if r["day"] >= FP_FROM and flagged(r, s)]
    eps: list[list[int]] = []
    for i in on:
        if eps and i - eps[-1][-1] <= MERGE:
            eps[-1].append(i)
        else:
            eps.append([i])
    hit = {w: False for w in WINDOWS}
    fps = []
    for e in eps:
        inside = [w for w, (a, b) in WINDOWS.items()
                  if any(a <= days[i] <= b for i in e)]
        for w in inside:
            hit[w] = True
        if not inside:
            fps.append(days[e[0]])
    word = C.PASS if all(hit.values()) and len(fps) <= MAX_FP else C.FAIL
    return {"episodes": [(days[e[0]], days[e[-1]], len(e)) for e in eps], "hit": hit,
            "fps": fps, "word": word}


def window_reads(rows: list[dict]) -> dict:
    """Each window's most extreme read of each component (the anatomy)."""
    out = {}
    for w, (a, b) in WINDOWS.items():
        rs = [r for r in rows if a <= r["day"] <= b]
        out[w] = {"front_60d_bp": min((r["front_60d_bp"] for r in rs
                                       if r["front_60d_bp"] is not None), default=None),
                  "crowd_min_z": min((r["crowd_min_z"] for r in rs
                                      if r["crowd_min_z"] is not None), default=None),
                  "move_pct": min((r["move_pct"] for r in rs), default=None),
                  "vol_ratio": max((r["vol_ratio"] for r in rs), default=None)}
    return out


def study(d: dict, mode: str) -> dict:
    s = settings()
    rows = components(d, s)
    ev = evaluate(rows, s)
    nwin = sum(ev["hit"].values())
    verdict = (f"{ev['word']} -- {nwin} of 4 windows flagged "
               f"({', '.join(w for w, h in ev['hit'].items() if h) or 'none'}), "
               f"{len(ev['fps'])} false positives 1998-{rows[-1]['day'][:4]} "
               f"(rule: all four, <= {MAX_FP})")
    wr = window_reads(rows)
    body = ["**The thresholds read** (ST-5's, config/funding_currency.yaml; crowding "
            "pre-registered here): differential 60-session change < 0 bp; crowding: the "
            f"lowest positioning z released in the prior {CROWD_DAYS} days <= {CROWD_Z}; "
            f"USDJPY 5-session move <= {s['move_pct']}%; 20-session vol >= "
            f"{s['vol_ratio']}x its 250-session median.", "",
            "**The anatomy** (each window's most extreme read of each component):", "",
            "| Window | Differential, 60 sessions (bp, min) | Crowding z (min) | "
            "5-session move (min) | Vol ratio (max) | Flagged |",
            "|---|---|---|---|---|---|"]
    for w, x in wr.items():
        body.append(f"| {w} | {C.f2(x['front_60d_bp'], 0)} | {C.f2(x['crowd_min_z'])} | "
                    f"{C.f2(x['move_pct'], 1, '%')} | {C.f2(x['vol_ratio'])} | "
                    f"{'yes' if ev['hit'][w] else 'no'} |")
    body += ["", f"**Episodes at ST-5's thresholds** ({len(ev['episodes'])}): "
             + ("; ".join(f"{a} to {b} ({n} sessions)" for a, b, n in ev["episodes"]) or "none")
             + ".", ""]
    sens = []
    if ev["word"] != C.PASS:
        body += ["**What each threshold would need** (each loosened alone along the "
                 "pre-registered grid, the others at ST-5's):", "",
                 "| Threshold | Value | Windows flagged | False positives | Rule |",
                 "|---|---|---|---|---|"]
        for k, vals in GRID.items():
            for v in vals:
                e = evaluate(rows, dict(s, **{k: v}))
                sens.append({"threshold": k, "value": v, "windows": sum(e["hit"].values()),
                             "false_positives": len(e["fps"]), "rule": e["word"]})
                body.append(f"| {k} | {v:+g} | {sum(e['hit'].values())} of 4 "
                            f"({', '.join(w for w, h in e['hit'].items() if h) or 'none'}) | "
                            f"{len(e['fps'])} | {e['word']} |")
        body += ["", "A loosening that reaches all four windows within two false "
                 "positives would be a candidate for the operator, not a pass of this "
                 "gate: the gate is at the chosen thresholds."]
    eps_rows = [{"start": a, "end": b, "sessions": n,
                 "window": next((w for w, (x, y) in WINDOWS.items() if x <= b and a <= y), "")}
                for a, b, n in ev["episodes"]]
    allr = eps_rows + sens
    cols = list(dict.fromkeys(k for r in allr for k in r))
    allr = [{k: r.get(k) for k in cols} for r in allr]
    return {
        "item": ITEM, "title": "the yen carry unwind: four episodes at ST-5's thresholds",
        "as_of": f"USDJPY {rows[-1]['day']}; CFTC {d['pos'][-1][0]}; JGB {d['jgb2'][-1][0]}",
        "window": f"{FP_FROM} to {rows[-1]['day']} (flags); history from {rows[0]['day']}",
        "n": len(ev["episodes"]),
        "statistic": "episodes of the three-part flag (narrowing differential, crowded "
                     "shorts, vol spike), the four windows flagged and the false positives",
        "pass_rule": (f"the register's: all four windows flagged with <= {MAX_FP} false "
                      f"positives 1998-2026 at the chosen thresholds (ST-5's; crowding at "
                      f"z <= {CROWD_Z} over {CROWD_DAYS} days pre-registered by this first "
                      f"edition; episodes merged within {MERGE} sessions)"),
        "verdict": verdict,
        "rights": ("PASS: the thresholds enter config/market_state.yaml with this ledger "
                   "named beside them, and the flag becomes the T&B overlay input at queue "
                   "position #1 after the gate. FAIL: the thresholds stay session-set in "
                   "config/funding_currency.yaml; the flag stays narrow, display only. "
                   + C.RIGHTS_NOTE),
        "sources": ["FRED graph CSV (no key): DGS2, DEXJPUS (not revised)",
                    "Japan MoF historical JGB yields, jgbcme_all.csv (no key), through "
                    "altdata/sources/mof.py",
                    "CFTC Public Reporting, legacy futures only (no key), yen 097741, "
                    "through altdata/sources/cftc.py; released the Friday after"],
        "source_mode": mode, "body": body, "episodes": allr,
        "caveats": ["DEXJPUS is the noon New York rate, where the live tell reads Yahoo's "
                    "JPY=X close; the two differ intraday, not in a 5-session move.",
                    "The 2007-08 window is long (two unwinds, Aug 2007 and Oct 2008), so "
                    "flagging it is easier than flagging the two-month windows.",
                    C.CONFIG_NOTE]}


if __name__ == "__main__":
    raise SystemExit(C.cli(ITEM, load_public, study))
