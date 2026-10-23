"""
OS-12c, the relative-volume ledger (signal-triage Batch 13, item 61, D3; a54, 20 Oct
2026). The pre-registration is docs/ledgers/relative-volume-preregistration-
2026-10.md, committed before this script and never edited; this script applies it.

    python tools/calibration/os12c_relative_volume.py [--box] [--out DIR] [--date D]
                                                      [--chains DIR]

WHAT IT READS. Our own chain captures on disk (altdata.chain_metrics.chain_dir(), the
box's data/chains, or --chains): each session's last capture per name gives the
session's total options volume and its front-month ATM IV (chain_metrics.
name_readings, OS-10's method); and Yahoo's daily closes per name (the one yfinance
import). It never opens the observation store (tools/calibration/README.md). On the
laptop, which holds no captures, the edition is INSUFFICIENT and says so.

THE RULE (registered): the 17 chain names; a name-day's ratio is its volume over the
mean of the 20 sessions before it (fewer than 20: provisional, not scored); flagged
at 1.5 or more. Each flagged name-day's excess is its next-5-session absolute move
(and IV change) less the mean over the same name's unflagged days; the statistic is
the mean excess with a one-sample t. INSUFFICIENT under 30 scored flagged or 30
unflagged name-days, or under 5 names with a scored flagged day; PASS when the mean
excess absolute move is above zero with t at least 2.0; FAIL otherwise. The IV change
prints beside it and decides nothing. This edition reads the captures sample only;
the flat-file sample (D5) is its own edition, read from the flat files themselves.
"""

from __future__ import annotations

import argparse
import bisect
import datetime as dt
import math
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import st7_common as C                                          # noqa: E402

ITEM = "OS-12c"
TITLE = "Relative options volume against the next five sessions' movement (item 61)"
PREREG = "docs/ledgers/relative-volume-preregistration-2026-10.md"
LAPTOP = "laptop run, our chain captures (none on the laptop) and public closes"
BOX = "box run, our chain captures and public closes"
WINDOW, THRESHOLD, HORIZON = 20, 1.5, 5
MIN_FLAGGED, MIN_UNFLAGGED, MIN_NAMES, T_PASS = 30, 30, 5, 2.0
PASS_RULE = ("Per sample: INSUFFICIENT under 30 scored flagged name-days, or under 30 "
             "scored unflagged, or under 5 names with a scored flagged day; PASS when the "
             "mean excess absolute 5-session move (each flagged name-day's move less the "
             "mean of the same name's unflagged days) is above zero with a one-sample t "
             "of at least 2.0; FAIL otherwise. The IV change prints beside it and decides "
             "nothing (" + PREREG + ")")


def load(base: Optional[Path] = None) -> dict:
    """{volume: {sym: [(day, v)]}, iv: {sym: {day: iv}}, closes: {sym: [(day, c)]}}."""
    from altdata import chain_metrics as cm, config as acfg     # noqa: PLC0415
    root = Path(base) if base else cm.chain_dir()
    days = sorted(p.name for p in root.iterdir() if p.is_dir()) if root.is_dir() else []
    vol: dict[str, list] = {}
    iv: dict[str, dict] = {}
    for day in days:
        for s in acfg.chain_universe():
            rd = cm.name_readings(day, s, root)
            if rd.get("volume"):
                vol.setdefault(s, []).append((day, float(rd["volume"])))
            f = rd.get("front") or {}
            if f.get("iv_pct") is not None:
                iv.setdefault(s, {})[day] = float(f["iv_pct"])
    closes: dict[str, list] = {}
    if vol:
        from altdata.ledgers import sources as S                # noqa: PLC0415
        for s in sorted(vol):
            closes[s] = S.yahoo(s)
    return {"volume": vol, "iv": iv, "closes": closes, "sessions": len(days),
            "retrieved": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}


def name_days(volume: list[tuple[str, float]]) -> list[dict]:
    """Every scorable name-day: its ratio over the 20 sessions before it."""
    out = []
    v = sorted(volume)
    for i in range(WINDOW, len(v)):
        prior = [x for _, x in v[i - WINDOW:i]]
        avg = sum(prior) / len(prior)
        if avg <= 0:
            continue
        r = v[i][1] / avg
        out.append({"day": v[i][0], "ratio": r, "flagged": r >= THRESHOLD})
    return out


def forward(closes: list[tuple[str, float]], day: str) -> Optional[float]:
    ds = [c[0] for c in closes]
    i = bisect.bisect_left(ds, day)
    if i >= len(closes) or ds[i] != day or i + HORIZON >= len(closes):
        return None
    return abs(closes[i + HORIZON][1] / closes[i][1] - 1.0) * 100.0


def iv_fwd(iv: dict[str, float], closes: list[tuple[str, float]], day: str) -> Optional[float]:
    ds = [c[0] for c in closes]
    i = bisect.bisect_left(ds, day)
    if i >= len(closes) or i + HORIZON >= len(closes):
        return None
    a, b = iv.get(day), iv.get(ds[i + HORIZON])
    return None if a is None or b is None else b - a


def t_one(xs: list[float]) -> Optional[float]:
    if len(xs) < 2:
        return None
    m = sum(xs) / len(xs)
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))
    return None if sd == 0 else m / (sd / math.sqrt(len(xs)))


def study(d: dict, mode: str) -> dict:
    move_ex, iv_ex, rows, names_flagged, n_unf = [], [], [], set(), 0
    for s, vol in sorted(d["volume"].items()):
        closes = d["closes"].get(s) or []
        iv = d["iv"].get(s) or {}
        nd = name_days(vol)
        for x in nd:
            x["move"] = forward(closes, x["day"])
            x["iv_chg"] = iv_fwd(iv, closes, x["day"])
        unf_m = [x["move"] for x in nd if not x["flagged"] and x["move"] is not None]
        unf_i = [x["iv_chg"] for x in nd if not x["flagged"] and x["iv_chg"] is not None]
        n_unf += len(unf_m)
        mu_m = sum(unf_m) / len(unf_m) if unf_m else None
        mu_i = sum(unf_i) / len(unf_i) if unf_i else None
        for x in nd:
            if not x["flagged"] or x["move"] is None or mu_m is None:
                continue
            names_flagged.add(s)
            ex = x["move"] - mu_m
            move_ex.append(ex)
            ivx = (x["iv_chg"] - mu_i) if (x["iv_chg"] is not None and mu_i is not None) else None
            if ivx is not None:
                iv_ex.append(ivx)
            rows.append({"symbol": s, "day": x["day"], "ratio": round(x["ratio"], 2),
                         "move_5s_pct": round(x["move"], 2), "excess_pct": round(ex, 2),
                         "iv_change_5s_pts": None if x["iv_chg"] is None else round(x["iv_chg"], 2)})
    t_m, t_i = t_one(move_ex), t_one(iv_ex)
    mean_m = sum(move_ex) / len(move_ex) if move_ex else None
    if len(move_ex) < MIN_FLAGGED or n_unf < MIN_UNFLAGGED or len(names_flagged) < MIN_NAMES:
        verdict = (f"{C.INSUFFICIENT} ({len(move_ex)} scored flagged name-days, {n_unf} "
                   f"unflagged, {len(names_flagged)} names; the rule needs {MIN_FLAGGED}, "
                   f"{MIN_UNFLAGGED} and {MIN_NAMES}; {d.get('sessions', 0)} capture "
                   f"sessions read)")
    elif mean_m is not None and mean_m > 0 and t_m is not None and t_m >= T_PASS:
        verdict = f"{C.PASS} (mean excess {mean_m:+.2f} pts, t {t_m:.2f})"
    else:
        verdict = (f"{C.FAIL} (mean excess "
                   + ("n/a" if mean_m is None else f"{mean_m:+.2f} pts")
                   + f", t {'n/a' if t_m is None else f'{t_m:.2f}'}; the rule needs t >= 2.0)")
    body = [f"- Capture sessions read: {d.get('sessions', 0)}; names with stored volume: "
            f"{len(d['volume'])}.",
            f"- Flagged name-days scored: {len(move_ex)} across {len(names_flagged)} names; "
            f"unflagged scored: {n_unf}.",
            "- Mean excess absolute 5-session move: "
            + ("n/a" if mean_m is None else f"{mean_m:+.2f} points, t "
               + ("n/a" if t_m is None else f"{t_m:.2f}")) + ".",
            "- Mean excess front-month IV change (beside it, decides nothing): "
            + ("n/a" if not iv_ex else f"{sum(iv_ex) / len(iv_ex):+.2f} points, t "
               + ("n/a" if t_i is None else f"{t_i:.2f}")) + "."]
    return {"item": ITEM, "title": TITLE, "as_of": dt.date.today().isoformat(),
            "window": (f"the captures sample: every stored capture session "
                       f"({d.get('sessions', 0)}); ratio over the 20 sessions before"),
            "n": len(move_ex),
            "statistic": ("the mean excess absolute 5-session move of flagged name-days "
                          "over the same name's unflagged days, one-sample t"),
            "pass_rule": PASS_RULE, "verdict": verdict,
            "rights": ("Would grant: a place for the flag in a score, only if the operator "
                       "so rules; the flag stays report-only, 'volume, no side'. "
                       + C.RIGHTS_NOTE),
            "sources": ["our chain captures on disk (altdata.chain_metrics.name_readings)",
                        f"Yahoo daily closes per name; retrieved {d.get('retrieved', '—')}"],
            "source_mode": mode, "body": body, "episodes": rows,
            "caveats": ["The flat-file sample (D5) is its own edition, read apart from "
                        "the captures and never pooled with them.",
                        "SPX and SPCX are flagged in the reports but not scored here: "
                        "their closes are not in the public sample."]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="OS-12c, the relative-volume ledger (item 61)")
    ap.add_argument("--box", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--date")
    ap.add_argument("--chains", help="the capture directory (default: chain_metrics.chain_dir())")
    a = ap.parse_args(argv)
    d = load(Path(a.chains) if a.chains else None)
    r = study(d, BOX if a.box else LAPTOP)
    C.publish(r, a.out, a.date or dt.date.today().isoformat())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
