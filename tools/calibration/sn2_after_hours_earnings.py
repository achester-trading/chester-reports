"""
SN-2: after-hours earnings -- continuation or fade (the secondary-notes order,
section 4.2, ruled 19 Oct 2026). Report-only.

THE PRE-REGISTRATION IS docs/ledgers/after-hours-earnings-preregistration-2026-10.md,
committed before this script and never edited (its SHA-256 is pinned by
tools/validate_secondary_notes.py). This script applies it and may not change it.

WHAT THE FIRST EDITION READS (laptop, public sources), the labelled proxy:
  - the names: the options universe (altdata.config.chain_universe()) less SPY,
    QQQ and IWM, and less any restricted name (the Brookfield blocklist);
  - the prints: Yahoo's earnings calendar (get_earnings_dates, the one yfinance
    import); after the close means a stated time at or after 16:00 ET, and a print
    whose time is unknown (a bare date) is not scored and counted;
  - five years of daily bars: the first move is the report day's close to the
    next open, the follow-through the next open to the next close.
It never opens the observation store. The evening note's own readings
(calc.after_hours_move, 16:00 to 21:30 against 21:30 to the next close) are the
second sample and are never pooled with this one.

    python tools/calibration/sn2_after_hours_earnings.py [--box] [--out DIR] [--date D]
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import st7_common as C                                          # noqa: E402

ITEM = "SN-2"
TITLE = "After-hours earnings: continuation or fade (secondary notes, 4.2)"
PREREG = "docs/ledgers/after-hours-earnings-preregistration-2026-10.md"
MIN_N = 30
INDEX_FUNDS = {"SPY", "QQQ", "IWM"}
PASS_RULE = ("A sample passes when the continuation share over all its scored prints has "
             "a Wilson 95% interval that excludes 50%, with 30 scored prints at least; "
             "INSUFFICIENT under 30, FAIL otherwise. Per-name shares are descriptive; no "
             "per-name test is made.")


def names() -> list[str]:
    from altdata import config as acfg                          # noqa: PLC0415
    out = []
    for s in acfg.chain_universe():
        if s in INDEX_FUNDS:
            continue
        try:
            from register import instruments                    # noqa: PLC0415
            if instruments.restrictions().is_restricted(s):
                continue
        except Exception:                                       # noqa: BLE001
            pass
        out.append(s)
    return out


def load() -> dict:
    from altdata import import_yfinance                         # noqa: PLC0415
    yf = import_yfinance()
    prints, bars, rep = {}, {}, {}
    for sym in names():
        t = yf.Ticker(sym)
        try:
            ed = t.get_earnings_dates(limit=28)
        except Exception as exc:                                # noqa: BLE001
            rep[sym] = f"no earnings calendar ({type(exc).__name__})"
            continue
        if ed is None or len(ed) == 0:
            rep[sym] = "no earnings calendar (a fund, or none served)"
            continue
        rows = []
        for idx in ed.index:
            ts = idx.tz_convert("America/New_York")
            rows.append({"day": ts.date().isoformat(), "time": ts.strftime("%H:%M")})
        prints[sym] = rows
        h = t.history(period="5y", interval="1d", auto_adjust=False)
        bars[sym] = [(i.date().isoformat(), float(r["Open"]), float(r["Close"]))
                     for i, r in h.iterrows()]
        rep[sym] = f"{len(rows)} dated prints, {len(bars[sym])} daily bars"
    return {"prints": prints, "bars": bars, "report": rep,
            "retrieved": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}


def score_print(day: str, bars: list[tuple[str, float, float]]) -> tuple[Optional[str], dict]:
    days = [b[0] for b in bars]
    if day not in days:
        return None, {"why": "the report day's bar is missing"}
    i = days.index(day)
    if i + 1 >= len(bars):
        return None, {"why": "no next session yet"}
    c0, (_, o1, c1) = bars[i][2], bars[i + 1]
    if not (c0 and o1 and c1):
        return None, {"why": "a price is missing"}
    m1, m2 = 100.0 * (o1 / c0 - 1.0), 100.0 * (c1 / o1 - 1.0)
    if m1 == 0:
        return None, {"why": "the first move is zero"}
    return ("continues" if (m1 > 0) == (m2 > 0) and m2 != 0 else "fades"), \
        {"m1": round(m1, 3), "m2": round(m2, 3)}


def study(d: dict, mode: str, today: Optional[str] = None) -> dict:
    from altdata.dealer_scorecard import wilson                 # noqa: PLC0415
    today = today or dt.date.today().isoformat()
    first = (dt.date.fromisoformat(today) - dt.timedelta(days=5 * 365)).isoformat()
    eps, per = [], {}
    unknown = before = 0
    for sym, rows in sorted(d["prints"].items()):
        for r in rows:
            if not (first <= r["day"] < today):
                continue
            if r["time"] == "00:00":
                unknown += 1
                eps.append({"symbol": sym, "day": r["day"], "time": "unknown",
                            "outcome": "", "m1": "", "m2": "",
                            "not_scored": "the print's time is unknown"})
                continue
            if r["time"] < "16:00":
                before += 1
                continue
            out, mv = score_print(r["day"], d["bars"].get(sym) or [])
            eps.append({"symbol": sym, "day": r["day"], "time": r["time"],
                        "outcome": out or "", "m1": mv.get("m1", ""), "m2": mv.get("m2", ""),
                        "not_scored": mv.get("why", "")})
            if out:
                p = per.setdefault(sym, [0, 0, [], []])
                p[0] += 1
                p[1] += out == "continues"
                (p[2] if out == "continues" else p[3]).append(mv["m2"])
    n = sum(p[0] for p in per.values())
    k = sum(p[1] for p in per.values())
    ci = wilson(k, n) if n else None
    body = ["- " + "; ".join(f"{s}: {v}" for s, v in sorted(d["report"].items())) + ".",
            f"- {n} after-the-close prints scored; {unknown} with an unknown time not "
            f"scored; {before} before 16:00 left out (not after the close).",
            "- The proxy: the report day's close to the next open (the first move), "
            "against the next open to the next close (the follow-through). Daily bars, "
            "Yahoo.", "",
            "| Name | Scored | Continues | Share | Mean follow-through after continuing | "
            "after fading |", "|---|---|---|---|---|---|"]
    for sym, (m, kk, cont, fade) in sorted(per.items()):
        mc = f"{sum(cont) / len(cont):+.2f}% (n {len(cont)})" if cont else "n/a"
        mf = f"{sum(fade) / len(fade):+.2f}% (n {len(fade)})" if fade else "n/a"
        body.append(f"| {sym} | {m} | {kk} | {kk / m * 100:.0f}% | {mc} | {mf} |")
    allc = [x for p in per.values() for x in p[2]]
    allf = [x for p in per.values() for x in p[3]]
    body += ["", f"- All names: continuation share {k}/{n}"
             + (f" = {k / n * 100:.0f}%, Wilson 95% {ci[0] * 100:.0f}-{ci[1] * 100:.0f}%"
                if ci else "")
             + "; mean follow-through after continuing "
             + (f"{sum(allc) / len(allc):+.2f}% (n {len(allc)})" if allc else "n/a")
             + ", after fading "
             + (f"{sum(allf) / len(allf):+.2f}% (n {len(allf)})." if allf else "n/a.")]
    if n < MIN_N:
        verdict = f"{C.INSUFFICIENT} ({n} scored prints; the floor is {MIN_N})"
    elif ci and (ci[1] < 0.5 or ci[0] > 0.5):
        verdict = (f"{C.PASS} (continuation {k}/{n}, Wilson 95% "
                   f"{ci[0] * 100:.0f}-{ci[1] * 100:.0f}% excludes 50%)")
    else:
        verdict = (f"{C.FAIL} (continuation {k}/{n}, Wilson 95% "
                   f"{ci[0] * 100:.0f}-{ci[1] * 100:.0f}% includes 50%)")
    return {"item": ITEM, "title": TITLE, "as_of": today,
            "window": f"prints {first} to {today} (five years of daily bars)", "n": n,
            "statistic": "the share of after-the-close prints whose first move (close to "
                         "next open) continued over the next session (next open to next "
                         "close)",
            "pass_rule": PASS_RULE, "verdict": verdict,
            "rights": ("None. A PASS is reported and reaches the register only as a "
                       "rule-31 draft; the evening note prints the move against the "
                       "implied move, never this verdict. " + C.RIGHTS_NOTE),
            "sources": [f"The pre-registration, {PREREG}",
                        "Yahoo Finance earnings dates and daily bars (the one yfinance "
                        f"import), retrieved {d['retrieved']}"],
            "source_mode": mode, "body": body, "episodes": eps,
            "caveats": [
                "A labelled proxy: the close to the next open includes the after-hours "
                "and pre-market sessions whole, not the 16:00 to 21:30 window the note "
                "reads.",
                "The window is filled only as far back as Yahoo's earnings calendar "
                "reaches for each name (the per-name counts are above); prints before "
                "the five years are dropped.",
                "Two samples are never pooled: the evening note's own readings accrue "
                "from its first live edition."]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="SN-2, after-hours earnings")
    ap.add_argument("--box", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--date")
    a = ap.parse_args(argv)
    r = study(load(), C.BOX if a.box else C.LAPTOP)
    C.publish(r, a.out, a.date or dt.date.today().isoformat())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
