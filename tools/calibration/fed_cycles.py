"""
The hiking-cycle table, 1955 on (signal-triage Tranche H, SR-7's row: "Adopt
table; reject unconditional average"; library-st-l, 19 Oct 2026). COMPUTED, never
typed: the cycles are found by the pre-registered rule below from the policy
rate's own history, so a re-run reproduces them and a new cycle appears without
anyone writing it down.

    python tools/calibration/fed_cycles.py [--box] [--out DIR] [--date D]

writes docs/ledgers/fed-cycles-ledger-<date>.md and its episodes CSV through
altdata.ledgers (the order named data/reference/fed_cycles.csv, which is
gitignored; the ledger directory is where a dated table lives).

THE POLICY RATE, monthly. From October 1982 the funds-rate target at each
month's end: DFEDTAR to 15 Dec 2008, then the midpoint of DFEDTARL and DFEDTARU
(the target SR-21's study reads). Before it, the effective rate's monthly average
(FEDFUNDS, from July 1954): the Fed announced no target until 1994 and published
none as a series before 1982, so the effective rate is the honest stand-in, and
the rule's reversal threshold is wide enough to ride through its month-to-month
noise.

THE RULE, pre-registered by this first edition (a zigzag on the monthly rate):
  - a turn is CONFIRMED when the rate moves REVERSAL_BP (75 bp) or more against
    the running extreme since the last confirmed turn;
  - a hiking cycle runs from a confirmed trough to the next confirmed peak: it
    STARTS in the first month after the trough month whose rate is above the
    trough, and ENDS in the first month the rate stood at the peak;
  - it counts only if the rise, peak less trough, is at least MIN_RISE_BP (100
    bp);
  - a rise not yet confirmed by a 75 bp fall is OPEN, listed and not completed.

WHAT EACH ROW CARRIES: the start and end months, the trough and peak rates, the
rise in bp, the months from start to end; the 10-year yield's change over the
cycle (GS10, the month before the first hike to the peak month); the S&P 500's
price return over the cycle (the same months) and over the 12 months after its end (^GSPC month-end closes); whether an
NBER recession (USREC) began within 24 months of the end, and after how many;
and SR-21's divergence episodes that started inside the cycle, conceded and
refused, read from the SR-21 ledger's episodes CSV.

THE CONDITIONAL TABLE (the row's point: no unconditional average). Completed
cycles split by whether a recession began within 24 months of the end, each
group's n with its medians; no all-cycle average is printed.

No pass rule: the order adopts the table as a base rate and states no gate, so
the verdict is NO GATE IN THE ORDER, as the ST-R ledgers say it.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import st7_common as C                                           # noqa: E402

ITEM = "FED-CYCLES"
REVERSAL_BP = 75.0
MIN_RISE_BP = 100.0
RECESSION_MONTHS = 24
AFTER_MONTHS = 12
TARGET_FROM = "1982-10"
SR21_CSV = C.REPO / "docs" / "ledgers" / "sr-21-ledger-2026-10-18-episodes.csv"
NO_GATE = ("NO GATE IN THE ORDER -- base rate recorded. The order adopts the table "
           "and states no pass rule; none is supplied here.")


def load_public() -> dict:
    from altdata.ledgers import sources as S
    return {"ff": S.fred("FEDFUNDS"), "tar": S.fred("DFEDTAR"),
            "tar_l": S.fred("DFEDTARL"), "tar_u": S.fred("DFEDTARU"),
            "gs10": S.fred("GS10"), "usrec": S.fred("USREC"),
            "spx": S.yahoo("^GSPC"), "sr21": read_sr21(SR21_CSV)}


def read_sr21(path: Path) -> list[dict]:
    if not Path(path).is_file():
        return []
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def policy_rate(d: dict) -> C.Monthly:
    """The monthly policy rate, percent: the effective rate's monthly average to
    September 1982, the target at each month's end from October 1982."""
    tar = dict(d["tar"])
    lo = dict(d["tar_l"])
    for day, u in d["tar_u"]:
        if day in lo:
            tar[day] = (u + lo[day]) / 2.0
    out = {m: v for m, v in C.monthly_mean(d["ff"]).items() if m < TARGET_FROM}
    out.update({m: v for m, v in C.monthly_last(sorted(tar.items())).items()
                if m >= TARGET_FROM})
    return dict(sorted(out.items()))


def turns(p: C.Monthly) -> list[tuple[str, str]]:
    """[(month, 'trough'|'peak')] confirmed by the 75 bp reversal, in order; the
    month is the first month the extreme was reached."""
    ms = sorted(p)
    if not ms:
        return []
    out: list[tuple[str, str]] = []
    hi_m = lo_m = ms[0]
    trend = 0                                  # 0 unknown, +1 rising, -1 falling
    for m in ms[1:]:
        v = p[m]
        if trend >= 0 and v > p[hi_m]:
            hi_m = m
        if trend <= 0 and v < p[lo_m]:
            lo_m = m
        if trend >= 0 and 100.0 * (p[hi_m] - v) >= REVERSAL_BP:
            if trend == 0 and lo_m < hi_m:
                out.append((lo_m, "trough"))
            out.append((hi_m, "peak"))
            trend, lo_m = -1, m
        elif trend <= 0 and 100.0 * (v - p[lo_m]) >= REVERSAL_BP:
            if trend == 0 and hi_m < lo_m:
                out.append((hi_m, "peak"))
            out.append((lo_m, "trough"))
            trend, hi_m = 1, m
    return out


def cycles(p: C.Monthly) -> list[dict]:
    """Each hiking cycle by the rule, completed or open."""
    ms = sorted(p)
    tt = turns(p)
    out = []
    for i, (m, kind) in enumerate(tt):
        if kind != "trough":
            continue
        peak = next((x for x, k in tt[i + 1:] if k == "peak"), None)
        if peak is None:                       # an open rise: the running high
            after = [x for x in ms if x > m]
            if not after:
                continue
            top = max(after, key=lambda x: (p[x], -ms.index(x)))
            peak, done = top, False
        else:
            done = True
        rise = 100.0 * (p[peak] - p[m])
        if rise < MIN_RISE_BP:
            continue
        start = next((x for x in ms if x > m and p[x] > p[m]), None)
        if start is None:
            continue
        out.append({"trough_month": m, "start": start, "end": peak,
                    "from_pct": round(p[m], 4), "to_pct": round(p[peak], 4),
                    "rise_bp": round(rise, 1),
                    "months": len([x for x in ms if start <= x <= peak]),
                    "completed": done})
    return out


def _n(v: Optional[float]) -> str:
    return "n/a" if v is None else f"{v:.0f}"


def _ret(s: C.Monthly, a: str, b: str) -> Optional[float]:
    return None if a not in s or b not in s or not s[a] else s[b] / s[a] - 1.0


def study(d: dict, mode: str) -> dict:
    p = policy_rate(d)
    gs10 = C.monthly_last(d["gs10"]) if d.get("gs10") else {}
    spx = C.monthly_last(d["spx"]) if d.get("spx") else {}
    rec = C.monthly_last(d["usrec"]) if d.get("usrec") else {}
    rows = cycles(p)
    for r in rows:
        tm, end = C.madd(r["start"], -1), r["end"]      # the month before the first hike
        r["d10_bp"] = (None if tm not in gs10 or end not in gs10
                       else round(100.0 * (gs10[end] - gs10[tm]), 1))
        r["spx_cycle"] = _ret(spx, tm, end)
        aft = C.madd(end, AFTER_MONTHS)
        r["spx_12m_after"] = _ret(spx, end, aft) if r["completed"] else None
        began = None
        for k in range(1, RECESSION_MONTHS + 1):
            m = C.madd(end, k)
            if rec.get(m) == 1.0 and rec.get(C.madd(m, -1)) != 1.0:
                began = k
                break
        last_rec = max(rec) if rec else None
        known = last_rec is not None and C.madd(end, RECESSION_MONTHS) <= last_rec
        r["recession_within_24m"] = (True if began else (False if known else None))
        r["months_to_recession"] = began
        inside = [e for e in d.get("sr21") or []
                  if r["start"] <= e["start"][:7] <= end]
        r["sr21_conceded"] = sum(1 for e in inside if e.get("outcome") == "conceded")
        r["sr21_refused"] = sum(1 for e in inside if e.get("outcome") == "refused")
        r["sr21_starts"] = "; ".join(f"{e['start']} {e.get('outcome') or 'open'}"
                                     for e in inside)
    done = [r for r in rows if r["completed"]]
    yes = [r for r in done if r["recession_within_24m"] is True]
    no = [r for r in done if r["recession_within_24m"] is False]

    def med(rs, k):
        return C.median([r[k] for r in rs if r[k] is not None])
    body = ["| Start | End | From | To | Rise (bp) | Months | 10y over the cycle (bp) | "
            "S&P over the cycle | S&P 12m after | Recession within 24m | SR-21 inside "
            "(conceded / refused) |",
            "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        rec_s = ("open" if not r["completed"] else
                 "unknown yet" if r["recession_within_24m"] is None else
                 f"yes, after {r['months_to_recession']}m" if r["recession_within_24m"]
                 else "no")
        body.append(f"| {r['start']} | {r['end']}{'' if r['completed'] else ' (open)'} | "
                    f"{r['from_pct']:.2f}% | {r['to_pct']:.2f}% | {r['rise_bp']:+.0f} | "
                    f"{r['months']} | {C.f2(r['d10_bp'], 0)} | {C.pct(r['spx_cycle'])} | "
                    f"{C.pct(r['spx_12m_after'])} | {rec_s} | "
                    f"{r['sr21_conceded']} / {r['sr21_refused']} |")
    body += ["",
             "The conditional table (completed cycles; no all-cycle average is printed, "
             "as the row rejects it):",
             "",
             "| Recession began within 24 months of the last hike | n | Median rise (bp) "
             "| Median months | Median S&P 12m after |",
             "|---|---|---|---|---|",
             f"| yes | {len(yes)} | {C.f2(med(yes, 'rise_bp'), 0)} | "
             f"{_n(med(yes, 'months'))} | {C.pct(med(yes, 'spx_12m_after'))} |",
             f"| no | {len(no)} | {C.f2(med(no, 'rise_bp'), 0)} | "
             f"{_n(med(no, 'months'))} | {C.pct(med(no, 'spx_12m_after'))} |",
             "",
             f"SR-21's rows inside the cycles: {sum(r['sr21_conceded'] for r in rows)} "
             f"conceded and {sum(r['sr21_refused'] for r in rows)} refused, read from "
             f"{SR21_CSV.relative_to(C.REPO).as_posix()} (its episodes begin in 1983, "
             "so cycles before then carry none)."]
    first = min(p) if p else "n/a"
    last = max(p) if p else "n/a"
    return {
        "item": ITEM, "title": "the hiking-cycle table, computed by rule",
        "as_of": f"{last} (latest month of the policy rate)",
        "window": f"{first} to {last}",
        "n": len(done),
        "statistic": "each hiking cycle's rise, length, the 10-year's change, the S&P "
                     "500 over and after it, and whether a recession followed within "
                     "24 months; split by that, never averaged across all cycles",
        "pass_rule": ("none in the order (Tranche H adopts the table). The cycle rule, "
                      "pre-registered by this first edition: the monthly policy rate "
                      "(FEDFUNDS' monthly average to 1982-09, the target at month-end "
                      "from 1982-10, the range's midpoint from 2008-12); a turn is "
                      "confirmed by a 75 bp reversal against the running extreme; a "
                      "cycle runs from the first month above a confirmed trough to the "
                      "first month at the next confirmed peak, and counts if the rise is "
                      "at least 100 bp"),
        "verdict": NO_GATE,
        "rights": ("None: a base-rate table (SR-7's row grants no right). It is quoted "
                   "beside the Warsh matrix and in the Base Rates paper's dated appendix "
                   "as a table, never as a forecast. " + C.RIGHTS_NOTE),
        "sources": ["FRED graph CSV (no key): FEDFUNDS, DFEDTAR, DFEDTARL, DFEDTARU, "
                    "GS10, USREC",
                    "Yahoo ^GSPC daily closes through altdata.import_yfinance",
                    f"SR-21's episodes: {SR21_CSV.relative_to(C.REPO).as_posix()}"],
        "source_mode": mode, "body": body, "episodes": rows,
        "caveats": ["Before October 1982 the rate is the effective rate's monthly "
                    "average, not a target, so those cycles' start and end months can "
                    "differ by a month or two from a narrative history.",
                    "The S&P 500 is its price, not its total return.",
                    "USREC is NBER's dating, published long after the fact: the "
                    "recession column is a historical label, not something knowable "
                    "at the last hike."]}


if __name__ == "__main__":
    raise SystemExit(C.cli(ITEM, load_public, study))
