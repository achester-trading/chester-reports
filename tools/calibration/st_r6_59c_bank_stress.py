"""
ST-R6.59c: the bank-stress base rate (signal-triage Batch 12, item 59, ruling 5;
a53, 20 Oct 2026). The pre-registration is docs/ledgers/bank-stress-
preregistration-2026-10.md, committed before this script and never edited; this
script applies it.

    python tools/calibration/st_r6_59c_bank_stress.py [--box] [--out DIR] [--date D]

THE EPISODES: KRE down 10% or more on its close 20 sessions earlier, one episode a
cluster (it ends after 60 sessions without the trigger). The named crises are the
episodes starting 2007-07-01 to 2009-03-31 and 2023-03-01 to 2023-05-31; every
other episode is a correction.

THE CLASSIFICATION, POINT IN TIME, on each episode's start and the 20 sessions after
it: the funding-stress flag (any two of SOFR less IORB, financial CP less the
3-month bill, the discount window's primary credit and FHLB advances above their
95th percentile over the five years before the session) and the deposit-flight flag
(small-bank H.8 deposits down over 4 weeks while retail money funds -- FRED's
WRMFNS, standing in for ICI -- are up). Neither: correction; one: funding watch;
both: banking stress. The episode's class is the most severe state it reaches. A
daily series counts from the next session, a weekly one from the first Friday
after its reference date, Z.1's FHLB advances from 75 days after the quarter-end.

THE PASS RULE (registered): at least 8 episodes with at least 2 crises, else
INSUFFICIENT; PASS when every crisis episode reaches funding watch or banking
stress AND at least two-thirds of the correction episodes stay correction; FAIL
otherwise. Forward S&P 500 returns (63 and 252 sessions) by class print beside it,
and the high-yield OAS change where FRED serves the spread.

Public sources only (the calibration rule): FRED's keyless graph CSV and Yahoo's
daily closes. study() is arithmetic over plain series, so a gate hands it a
fixture.
"""

from __future__ import annotations

import bisect
import datetime as dt
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import st7_common as C                                           # noqa: E402

from altdata import ledgers                                      # noqa: E402

ITEM = "ST-R6.59c"
TITLE = "The bank-stress base rate: the correction-vs-crisis classifier (item 59)"
PREREG = "docs/ledgers/bank-stress-preregistration-2026-10.md"
TRIGGER_PCT, TRIGGER_SESSIONS, CLUSTER_GAP = -10.0, 20, 60
LOOK_AHEAD = 20
CRISES = (("2007-07-01", "2009-03-31"), ("2023-03-01", "2023-05-31"))
IORB_FROM = "2021-07-29"
FHLB_LAG_DAYS = 75
MIN_EPISODES, MIN_CRISES = 8, 2
STATES = ("correction", "funding watch", "banking stress")
PASS_RULE = ("At least 8 episodes and at least 2 crisis episodes, else INSUFFICIENT; "
             "PASS when every crisis episode (a start in 2007-07-01 to 2009-03-31 or "
             "2023-03-01 to 2023-05-31) reaches funding watch or banking stress within "
             "20 sessions of its start AND at least two-thirds of the correction "
             "episodes stay correction; FAIL otherwise (" + PREREG + ")")
FRED_IDS = {"kre": None, "sofr": "SOFR", "iorb": "IORB", "ioer": "IOER", "cp": "DCPF3M",
            "bill": "DTB3", "dw": "WLCFLPCL", "fhlb": "BOGZ1FL403069330Q",
            "dep_small": "DPSSCBW027SBOG", "mmf": "WRMFNS", "hy": "BAMLH0A0HYM2"}


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------
def load_public() -> dict:
    from altdata.ledgers import sources as S                    # noqa: PLC0415
    out = {k: S.fred(v) for k, v in FRED_IDS.items() if v}
    out["kre"] = S.yahoo("KRE")
    out["spx"] = S.yahoo("^GSPC")
    out["retrieved"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    return out


# ---------------------------------------------------------------------------
# Point in time
# ---------------------------------------------------------------------------
def _d(s: str) -> dt.date:
    return dt.date.fromisoformat(s[:10])


def next_friday(day: str) -> str:
    d = _d(day)
    return (d + dt.timedelta(days=(4 - d.weekday()) % 7 or 7)).isoformat()


def knowable(series: list, rule: str) -> list[tuple[str, str, float]]:
    """[(available_day, observed_day, value)] sorted by availability."""
    out = []
    for d, v in series:
        if rule == "daily":
            a = (_d(d) + dt.timedelta(days=1)).isoformat()
        elif rule == "weekly":
            a = next_friday(d)
        else:                                   # quarterly Z.1, dated the quarter's start
            q0 = _d(d)
            m = q0.month + 3
            qe = (dt.date(q0.year + (m > 12), (m - 1) % 12 + 1, 1) - dt.timedelta(days=1))
            a = (qe + dt.timedelta(days=FHLB_LAG_DAYS)).isoformat()
        out.append((a, d, v))
    return sorted(out)


class PIT:
    """One series as knowable: the values available on or before a session."""

    def __init__(self, series: list, rule: str):
        self.rows = knowable(series, rule)
        self.avail = [r[0] for r in self.rows]

    def upto(self, day: str) -> list[tuple[str, float]]:
        i = bisect.bisect_right(self.avail, day)
        return sorted((o, v) for _, o, v in self.rows[:i])


def policy(iorb: list, ioer: list) -> list[tuple[str, float]]:
    out = {d: v for d, v in ioer if d < IORB_FROM}
    out.update({d: v for d, v in iorb if d >= IORB_FROM})
    return sorted(out.items())


def spread(a: list, b: list) -> list[tuple[str, float]]:
    """a less b in bp, on a's days, b carried forward."""
    bd, bv = [x[0] for x in b], [x[1] for x in b]
    out = []
    for d, v in a:
        i = bisect.bisect_right(bd, d) - 1
        if i >= 0:
            out.append((d, round((v - bv[i]) * 100.0, 2)))
    return out


def years_back(day: str, n: int) -> str:
    d = _d(day)
    try:
        return d.replace(year=d.year - n).isoformat()
    except ValueError:
        return d.replace(year=d.year - n, day=28).isoformat()


def pct5(pts: list[tuple[str, float]], day: str) -> Optional[float]:
    """The latest knowable value's percentile over the five years before `day`."""
    if not pts:
        return None
    lo = years_back(day, 5)
    win = [v for d, v in pts if d > lo]
    if not win:
        return None
    return ledgers.percentile_rank(win, pts[-1][1])


def change_4w(pts: list[tuple[str, float]]) -> Optional[float]:
    if not pts:
        return None
    d1, v1 = pts[-1]
    lo = (_d(d1) - dt.timedelta(days=28)).isoformat()
    base = [v for d, v in pts if d <= lo]
    return (v1 - base[-1]) if base else None


def state_on(day: str, pit: dict) -> dict:
    above, read = [], []
    for m in ("sofr_iorb", "fin_cp", "dw", "fhlb"):
        p = pct5(pit[m].upto(day), day)
        if p is None:
            continue
        read.append(m)
        if p > 95.0:
            above.append(m)
    fund = len(above) >= 2
    ds, dm = change_4w(pit["dep_small"].upto(day)), change_4w(pit["mmf"].upto(day))
    dep = ds is not None and dm is not None and ds < 0 and dm > 0
    return {"state": int(fund) + int(dep), "funding": fund, "deposit": dep,
            "above": above, "read": read}


# ---------------------------------------------------------------------------
# The study
# ---------------------------------------------------------------------------
def episodes(kre: list[tuple[str, float]]) -> list[dict]:
    out, last_hit = [], None
    for i in range(TRIGGER_SESSIONS, len(kre)):
        ch = (kre[i][1] / kre[i - TRIGGER_SESSIONS][1] - 1) * 100.0
        if ch > TRIGGER_PCT:
            continue
        if last_hit is None or i - last_hit > CLUSTER_GAP:
            out.append({"start": kre[i][0], "i": i, "kre_20s_pct": round(ch, 1)})
        last_hit = i
    return out


def _p(v: Optional[float]) -> str:
    """A figure already in percent."""
    return "n/a" if v is None else f"{v:+.1f}%"


def crisis(day: str) -> bool:
    return any(a <= day <= b for a, b in CRISES)


def fwd(series: list[tuple[str, float]], day: str, k: int) -> Optional[float]:
    ds = [x[0] for x in series]
    i = bisect.bisect_left(ds, day)
    if i >= len(series) or i + k >= len(series):
        return None
    return (series[i + k][1] / series[i][1] - 1) * 100.0


def hy_change(hy: list[tuple[str, float]], spx: list, day: str, k: int) -> Optional[float]:
    ds = [x[0] for x in spx]
    i = bisect.bisect_left(ds, day)
    if i + k >= len(spx):
        return None
    hd = dict(hy)
    a, b = hd.get(spx[i][0]), hd.get(spx[i + k][0])
    return None if a is None or b is None else round((b - a) * 100.0, 0)


def study(data: dict, mode: str) -> dict:
    pit = {"sofr_iorb": PIT(spread(data["sofr"], policy(data["iorb"], data["ioer"])), "daily"),
           "fin_cp": PIT(spread(data["cp"], data["bill"]), "daily"),
           "dw": PIT(data["dw"], "weekly"), "fhlb": PIT(data["fhlb"], "quarterly"),
           "dep_small": PIT(data["dep_small"], "weekly"), "mmf": PIT(data["mmf"], "weekly")}
    kre = data["kre"]
    eps = episodes(kre)
    rows = []
    for e in eps:
        days = [kre[j][0] for j in range(e["i"], min(e["i"] + LOOK_AHEAD + 1, len(kre)))]
        reads = [(d, state_on(d, pit)) for d in days]
        top = max(reads, key=lambda x: x[1]["state"])
        rows.append({"start": e["start"], "kre_20s_pct": e["kre_20s_pct"],
                     "label": "crisis" if crisis(e["start"]) else "correction",
                     "class": STATES[top[1]["state"]],
                     "reached_on": top[0] if top[1]["state"] else "",
                     "funding_members_above": "+".join(top[1]["above"]),
                     "funding_members_read": len(top[1]["read"]),
                     "deposit_flag": top[1]["deposit"],
                     "spx_63s_pct": None if (x := fwd(data["spx"], e["start"], 63)) is None else round(x, 1),
                     "spx_252s_pct": None if (x := fwd(data["spx"], e["start"], 252)) is None else round(x, 1),
                     "hy_63s_bp": hy_change(data.get("hy") or [], data["spx"], e["start"], 63)})
    cr = [r for r in rows if r["label"] == "crisis"]
    co = [r for r in rows if r["label"] == "correction"]
    caught = [r for r in cr if r["class"] != "correction"]
    stayed = [r for r in co if r["class"] == "correction"]
    if len(rows) < MIN_EPISODES or len(cr) < MIN_CRISES:
        verdict = (f"{C.INSUFFICIENT} ({len(rows)} episodes, {len(cr)} crises; the rule "
                   f"needs {MIN_EPISODES} and {MIN_CRISES})")
    elif len(caught) == len(cr) and 3 * len(stayed) >= 2 * len(co):
        verdict = (f"{C.PASS} (every crisis caught, {len(caught)} of {len(cr)}; "
                   f"{len(stayed)} of {len(co)} corrections stayed correction)")
    else:
        verdict = (f"{C.FAIL} (crises caught {len(caught)} of {len(cr)}; corrections "
                   f"stayed correction {len(stayed)} of {len(co)}, the rule needs "
                   f"two-thirds)")
    body = ["| Start | KRE, 20 sessions | Label | Class | Reached on | Funding above (read) "
            "| Deposit flag | SPX +63s | SPX +252s | HY OAS +63s |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        hy = "not served" if r["hy_63s_bp"] is None else f"{r['hy_63s_bp']:+.0f} bp"
        body.append(f"| {r['start']} | {r['kre_20s_pct']:+.1f}% | {r['label']} | {r['class']} | "
                    f"{r['reached_on'] or '—'} | {r['funding_members_above'] or 'none'} "
                    f"({r['funding_members_read']}) | {'on' if r['deposit_flag'] else 'off'} | "
                    f"{_p(r['spx_63s_pct'])} | {_p(r['spx_252s_pct'])} | {hy} |")
    body += ["", "**Forward S&P 500 by class** (not part of the pass rule):", ""]
    for s in STATES:
        xs = [r for r in rows if r["class"] == s]
        m63 = C.median([r["spx_63s_pct"] for r in xs if r["spx_63s_pct"] is not None])
        m252 = C.median([r["spx_252s_pct"] for r in xs if r["spx_252s_pct"] is not None])
        body.append(f"- {s}: n {len(xs)}; median +63 sessions {_p(m63)}, +252 sessions "
                    f"{_p(m252)}.")
    for r in rows:
        r["hy_63s_bp"] = "not served" if r["hy_63s_bp"] is None else r["hy_63s_bp"]
    first = kre[0][0] if kre else "—"
    return {"item": ITEM, "title": TITLE, "as_of": kre[-1][0] if kre else "—",
            "window": f"KRE {first} to {kre[-1][0] if kre else '—'}; each percentile over "
                      f"the five years before its session",
            "n": len(rows),
            "statistic": ("the classifier's most severe state within 20 sessions of each "
                          "episode's start, against its crisis or correction label"),
            "pass_rule": PASS_RULE, "verdict": verdict,
            "rights": ("Would grant: a T&B overlay intake-queue entry (ST-R6.59d, the "
                       "Liquidity & Funding Stress family), only after \"T&B full\" and "
                       "its place in the queue. The flags and the classifier stay "
                       "report-only either way. " + C.RIGHTS_NOTE),
            "sources": [f"FRED graph CSV (no key): {', '.join(v for v in FRED_IDS.values() if v)}; "
                        f"Yahoo daily closes: KRE, ^GSPC; retrieved {data.get('retrieved', '—')}",
                        "WRMFNS (retail money funds) stands in for ICI's total: ICI's file "
                        "refuses an identified client"],
            "source_mode": mode, "body": body, "episodes": rows,
            "caveats": ["SOFR starts in April 2018: before it the funding flag reads at "
                        "most three members and still needs two.",
                        "FRED serves the ICE BofA HY OAS for recent years only; earlier "
                        "episodes print 'not served' on that leg.",
                        "A weekly series counts from the first Friday after its "
                        "reference date, as registered; H.8's real lag is longer, so the "
                        "deposit leg is read a little early."]}


if __name__ == "__main__":
    sys.exit(C.cli(ITEM, load_public, study))
