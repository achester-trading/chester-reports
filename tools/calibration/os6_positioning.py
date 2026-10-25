"""
OS-6's calibration ledger: the positioning components, tested rather than weighted
(signal-triage Batch 11 item 53, ruled 19 Oct 2026; OS-6's DIP WATCH, generalised).

THE ORDER. Inputs: the OS-3 lenses (VIX less RV20 with its percentiles, VIX9D/VIX,
VIX3M/VIX and VIX6M/VIX), VVIX, SKEW, and OS-4's put-volume share. Outcomes: the
forward 5- and 10-session SPX returns, maximum drawdown and realised volatility.
The first edition from public sources for the VIX family (2007 on), labelled
"laptop run, public sources"; the put-volume component joins in the box edition,
once its history allows, or from D4's backfill. The pass rule is pre-registered in
this first edition. Its rights are stated and nothing is granted. NO COMPOSITE
NUMBER AND NO WEIGHTS ARE PRINTED.

WHAT THE FIRST EDITION PRE-REGISTERS (ruling 2 of 17 Oct: a re-run applies it and
may not change it):
  - each component's reading on a session is its POINT-IN-TIME percentile over
    the trailing 1,260 sessions (five years; 252 at least), so no extreme is
    judged with history it did not have;
  - VIX less RV20 is the VIX less SPX's 20-session close-to-close realised
    volatility (annualised, percent); the ratios are close over close;
  - the two tails of each component are its top decile (>= 90th) and its bottom
    decile (<= 10th): twelve tests over six components;
  - to keep outcomes from overlapping, only every 10th session is sampled (the
    sessions whose index from the start is a multiple of 10);
  - each test compares the forward 10-session SPX return after the tail's
    sampled sessions with every sampled session's (Welch t), the 5-session
    return, the 10-session maximum drawdown and the 10-session realised
    volatility printed beside it;
  - a test needs 20 sampled sessions in its tail; under that it is not judged;
  - PASS: at least one test's p-value (two-sided, normal) survives a
    Benjamini-Hochberg control at q = 0.10 across the tests judged, with 6 tests
    judged at least; INSUFFICIENT under 6; FAIL otherwise.

THE RIGHTS IT WOULD GRANT, STATED AND NOT GRANTED: a narrow, report-only flag in
OS-3's lines for a component whose test passes (the DIP WATCH idea), never a
composite or a weight, and only after the operator's ruling. A PASS reaches the register
only as a rule-31 draft.

Public sources only (tools/calibration/README.md): Yahoo's ^VIX, ^VIX9D, ^VIX3M,
^VIX6M, ^VVIX, ^SKEW and ^GSPC through the one yfinance import. Never the store.

    python tools/calibration/os6_positioning.py [--box] [--out DIR] [--date D]
"""

from __future__ import annotations

import datetime as dt
import math
import statistics
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import st7_common as C                                          # noqa: E402

ITEM = "OS-6"
TITLE = "The positioning components against SPX's forward path (item 53)"
FROM = "2007-01-01"
WINDOW, MIN_HIST = 1260, 252
SPACING = 10
MIN_TAIL = 20
Q = 0.10
MIN_TESTS = 6
SYMBOLS = {"vix": "^VIX", "vix9d": "^VIX9D", "vix3m": "^VIX3M", "vix6m": "^VIX6M",
           "vvix": "^VVIX", "skew": "^SKEW", "spx": "^GSPC"}
COMPONENTS = ("vix_less_rv20", "vix9d_over_vix", "vix3m_over_vix", "vix6m_over_vix",
              "vvix", "skew")
PASS_RULE = ("Each component's point-in-time five-year percentile; its top (>= 90th) and "
             "bottom (<= 10th) deciles against SPX's forward 10-session return on every "
             "10th session (Welch t), the 5-session return, drawdown and realised vol "
             "beside it; 20 sampled sessions a tail at least; PASS when a test survives "
             "Benjamini-Hochberg at q = 0.10 across the tests judged (6 at least), "
             "INSUFFICIENT under 6, FAIL otherwise. No composite, no weights.")


def load_public() -> dict:
    from altdata.ledgers import sources as S                    # noqa: PLC0415
    out = {k: S.yahoo(v) for k, v in SYMBOLS.items()}
    out["retrieved"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    return out


def rv(closes: list[float]) -> Optional[float]:
    rets = [math.log(b / a) for a, b in zip(closes, closes[1:]) if a and b]
    if len(rets) < 2:
        return None
    m = sum(rets) / len(rets)
    return math.sqrt(sum((r - m) ** 2 for r in rets) / (len(rets) - 1) * 252) * 100


def components(d: dict) -> tuple[list[str], dict[str, dict[str, float]], dict[str, float]]:
    """(SPX sessions from FROM, {component: {day: value}}, {day: SPX close})."""
    # The retrieval day's close is not final: left out.
    today = str(d.get("retrieved") or dt.date.today().isoformat())[:10]
    spx = {k: v for k, v in d["spx"] if "2006-01-01" <= k < today}
    days = sorted(spx)
    ser = {k: dict(d[k]) for k in ("vix", "vix9d", "vix3m", "vix6m", "vvix", "skew")}
    comp: dict[str, dict[str, float]] = {c: {} for c in COMPONENTS}
    for i, day in enumerate(days):
        if day < FROM:
            continue
        v = ser["vix"].get(day)
        if v and i >= 20:
            r = rv([spx[x] for x in days[i - 20:i + 1]])
            if r is not None:
                comp["vix_less_rv20"][day] = v - r
        for c, k in (("vix9d_over_vix", "vix9d"), ("vix3m_over_vix", "vix3m"),
                     ("vix6m_over_vix", "vix6m")):
            x = ser[k].get(day)
            if v and x:
                comp[c][day] = x / v
        for c in ("vvix", "skew"):
            if ser[c].get(day):
                comp[c][day] = ser[c][day]
    return [x for x in days if x >= FROM], comp, spx


def pit_percentiles(days: list[str], vals: dict[str, float]) -> dict[str, float]:
    out, hist = {}, []
    for day in days:
        if day not in vals:
            continue
        hist.append(vals[day])
        h = hist[-WINDOW:]
        if len(h) >= MIN_HIST:
            out[day] = 100.0 * sum(1 for x in h if x <= vals[day]) / len(h)
    return out


def forward(days: list[str], spx: dict[str, float], i: int, n: int) -> Optional[dict]:
    if i + n >= len(days):
        return None
    path = [spx[days[j]] for j in range(i, i + n + 1)]
    peak, mdd = path[0], 0.0
    for p in path:
        peak = max(peak, p)
        mdd = min(mdd, p / peak - 1.0)
    return {"ret": path[-1] / path[0] - 1.0, "mdd": mdd, "rv": rv(path)}


def welch(a: list[float], b: list[float]) -> Optional[float]:
    if len(a) < 2 or len(b) < 2:
        return None
    se = math.sqrt(statistics.variance(a) / len(a) + statistics.variance(b) / len(b))
    return None if se == 0 else (statistics.mean(a) - statistics.mean(b)) / se


def p_two_sided(t: float) -> float:
    return math.erfc(abs(t) / math.sqrt(2.0))


def bh(ps: list[float], q: float) -> list[bool]:
    """Benjamini-Hochberg: which hypotheses are rejected at q."""
    m = len(ps)
    order = sorted(range(m), key=lambda i: ps[i])
    k = 0
    for rank, i in enumerate(order, 1):
        if ps[i] <= rank / m * q:
            k = rank
    keep = set(order[:k])
    return [i in keep for i in range(m)]


def study(d: dict, mode: str) -> dict:
    days, comp, spx = components(d)
    idx = {day: i for i, day in enumerate(days)}
    sampled = [day for k, day in enumerate(days) if k % SPACING == 0]
    fw = {day: (forward(days, spx, idx[day], 5), forward(days, spx, idx[day], 10))
          for day in sampled}
    allf = [fw[x][1]["ret"] for x in sampled if fw[x][1]]
    tests, eps = [], []
    for c in COMPONENTS:
        pct = pit_percentiles(days, comp[c])
        for tail in ("top", "bottom"):
            sel = [x for x in sampled if x in pct and fw[x][1]
                   and ((pct[x] >= 90.0) if tail == "top" else (pct[x] <= 10.0))]
            r10 = [fw[x][1]["ret"] for x in sel]
            row = {"component": c, "tail": tail, "n": len(sel)}
            if len(sel) >= MIN_TAIL:
                t = welch(r10, allf)
                row.update(t=t, p=None if t is None else p_two_sided(t),
                           mean10=statistics.mean(r10), uncond10=statistics.mean(allf),
                           mean5=statistics.mean([fw[x][0]["ret"] for x in sel if fw[x][0]]),
                           mdd10=statistics.mean([fw[x][1]["mdd"] for x in sel]),
                           rv10=statistics.mean([fw[x][1]["rv"] for x in sel
                                                 if fw[x][1]["rv"] is not None]))
            tests.append(row)
            for x in sel:
                eps.append({"component": c, "tail": tail, "session": x,
                            "percentile": round(pct[x], 1),
                            "fwd5": None if not fw[x][0] else round(fw[x][0]["ret"], 4),
                            "fwd10": round(fw[x][1]["ret"], 4),
                            "mdd10": round(fw[x][1]["mdd"], 4),
                            "rv10": None if fw[x][1]["rv"] is None else round(fw[x][1]["rv"], 2)})
    judged = [t for t in tests if t.get("p") is not None]
    rej = bh([t["p"] for t in judged], Q) if judged else []
    for t, r in zip(judged, rej):
        t["survives"] = r
    n_pass = sum(1 for t in judged if t.get("survives"))
    line = (f"{len(judged)} of {len(tests)} tests judged on {len(sampled)} sampled sessions; "
            f"{n_pass} survive Benjamini-Hochberg at q = 0.10")
    verdict = (f"{C.INSUFFICIENT} ({line})" if len(judged) < MIN_TESTS else
               f"{C.PASS} ({line})" if n_pass else f"{C.FAIL} ({line})")
    as_of = days[-11] if len(days) > 11 else "none"
    body = [f"- SPX sessions {days[0]} to {days[-1]}; every {SPACING}th sampled "
            f"({len(sampled)}); the unconditional forward 10-session return "
            f"{C.pct(statistics.mean(allf))} (n={len(allf)}).",
            f"- {line}.", "",
            "| Component | Tail | n | 10-session mean | Welch t | p | Survives | 5-session mean "
            "| 10-session drawdown | 10-session RV |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for t in tests:
        if t.get("p") is None:
            body.append(f"| {t['component']} | {t['tail']} | {t['n']} | under the floor of "
                        f"{MIN_TAIL} | | | | | | |")
            continue
        body.append(f"| {t['component']} | {t['tail']} | {t['n']} | {C.pct(t['mean10'])} | "
                    f"{t['t']:+.2f} | {t['p']:.3f} | {'yes' if t.get('survives') else 'no'} | "
                    f"{C.pct(t['mean5'])} | {C.pct(t['mdd10'])} | {t['rv10']:.1f} |")
    body += ["", "No composite and no weights are printed (item 53)."]
    return {"item": ITEM, "title": TITLE, "as_of": as_of,
            "window": f"{FROM} to {as_of} (each percentile over the trailing five years)",
            "n": len(sampled),
            "statistic": "per component and tail, SPX's mean forward 10-session return "
                         "against the unconditional (Welch t), Benjamini-Hochberg across "
                         "the tests",
            "pass_rule": PASS_RULE, "verdict": verdict,
            "rights": ("Would grant: a narrow, report-only flag in OS-3's lines for a "
                       "component whose test survives (the DIP WATCH idea), never a "
                       "composite or a weight, and only after the operator's ruling. This ledger "
                       "grants nothing. " + C.RIGHTS_NOTE),
            "sources": [f"Yahoo Finance daily closes: {', '.join(SYMBOLS.values())} (the "
                        f"one yfinance import), retrieved {d.get('retrieved', '-')}"],
            "source_mode": mode, "body": body, "episodes": eps,
            "caveats": ["The put-volume share (OS-4) is not in this edition: its history "
                        "is the box's captures (from late September 2026) or D4's "
                        "backfill; it joins in the box edition once a five-year percentile "
                        "is possible, and is listed until then.",
                        "VIX9D starts in 2011 and VIX6M in 2008; each component is judged "
                        "on the sessions it has.",
                        "SPX's realised volatility stands for SPY's in VIX less RV20."]}


if __name__ == "__main__":
    raise SystemExit(C.cli(ITEM, load_public, study))
