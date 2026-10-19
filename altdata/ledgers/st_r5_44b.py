"""
ST-R5.44b -- the drawdown-gap ledger (Batch 6 item 44; docs/
change-order-signal-triage-batch-6-2026-10-15.md).

    python -m altdata.ledgers.st_r5_44b [--source public|store] [--out DIR] [--db PATH]

THE ORDER: "add ... an average-member vs index drawdown gap ... from the box's own
constituent prices. Gap ledger of how past wide gaps resolved, entered into the
T&B overlay intake queue (top-side) after the ledger." The read (Raymond James
via Lemand, 3Q26): the average member 20.1% below its high with the index near
its own. "Wide gaps have resolved either by leaders falling or by a broadening
rally." Rights: "Report now; T&B via queue after ledger." The order states NO
pass rule.

OUR MEASURE is item 44a's: each member's distance from its 52-week (252-session)
closing high, averaged over the members with at least MIN_CLOSES closes in the
window, against the S&P 500's own distance from its 52-week high. The GAP is the
index's drawdown less the average member's, in points: positive when the average
stock is further below its high than the index. Today's members only
(survivorship, stated).

THE STUDY. A wide-gap episode is a run of sessions with the gap at or above WIDE
points (runs closer than MERGE_GAP sessions joined); its peak is the widest
session. Each is resolved over the HORIZON sessions after the peak:
  leaders fell   the index's drawdown deepened by DEEPEN points or more
  broadening     not that, and the average member's drawdown narrowed by
                 NARROW points or more
  unresolved     neither
An episode is COMPLETED only when HORIZON sessions follow its peak.

THE PASS RULE, PRE-REGISTERED BY THIS FIRST EDITION (ruled 17 Oct 2026: "the
rule as stated, else the first edition's"), written before any run:
  PASS if at least FLOOR episodes are completed and the leaders fell in at least
  60% of them -- a wide gap then reads as a top-side input. Fewer than FLOOR
  completed: INSUFFICIENT, and no rate prints. The floor is five, the same as
  item 31's.
"""

from __future__ import annotations

import argparse
import datetime as dt
import logging
import sys
from pathlib import Path
from typing import Optional

from . import Series, episodes, mean, write_ledger

ITEM = "ST-R5.44b"
TITLE = "how wide average-member vs index drawdown gaps resolved"
WINDOW = 252
MIN_CLOSES = 240
WIDE = 15.0
MERGE_GAP = 10
HORIZON = 126
DEEPEN = 5.0
NARROW = 5.0
FLOOR = 5
PASS_SHARE = 0.6
PASS_RULE = ("Pre-registered by this first edition (the order states none): PASS if "
             f"at least {FLOOR} wide-gap episodes (gap >= {WIDE:.0f} points) are "
             f"completed and the leaders fell (the index's drawdown deepened by "
             f"{DEEPEN:.0f} points or more within {HORIZON} sessions of the peak) in at "
             f"least {100 * PASS_SHARE:.0f}% of them; fewer than {FLOOR} completed: "
             "INSUFFICIENT, and no rate prints")
RIGHTS = ("Report now; T&B via queue after ledger (the order). A PASS would let the "
          "gap's queue entry (44c) be filed for the operator's ruling, one candidate "
          "at a time; INSUFFICIENT or FAIL keeps it report-only. This ledger grants "
          "nothing, and 44c is not filed (ruling 1 of 17 Oct 2026).")
SOURCED = ["Share of S&P members above their 50-day: about 70% to 21% in 3Q26",
           "40% of members 20% or more off their highs; 40% 10-20% off; 18% within "
           "10%; 2% at a record",
           "The average member 20.1% below its high (Raymond James via Lemand, 3Q26)"]


def drawdown_at(s: Series, i: int, window: int = WINDOW,
                min_closes: int = MIN_CLOSES) -> Optional[float]:
    """Percent below the highest close of the `window` sessions ending at i."""
    win = [v for _, v in s[max(0, i - window + 1):i + 1]]
    if len(win) < min_closes:
        return None
    hi = max(win)
    return 100.0 * (win[-1] / hi - 1.0) if hi > 0 else None


def drawdowns(s: Series, window: int = WINDOW,
              min_closes: int = MIN_CLOSES) -> dict[str, float]:
    """{day: drawdown_at(s, i)} for every session, in one pass (a monotonic
    deque holds the window's running high)."""
    from collections import deque                               # noqa: PLC0415
    out, dq = {}, deque()
    for i, (d, v) in enumerate(s):
        while dq and dq[0] <= i - window:
            dq.popleft()
        while dq and s[dq[-1]][1] <= v:
            dq.pop()
        dq.append(i)
        if min(i + 1, window) >= min_closes:
            hi = s[dq[0]][1]
            if hi > 0:
                out[d] = 100.0 * (v / hi - 1.0)
    return out


def gap_series(closes: dict[str, Series], index: Series) -> list[tuple]:
    """[(day, index drawdown, average member drawdown, gap, members)] on the
    index's sessions where at least half the members have a drawdown."""
    mdd = [drawdowns(s) for s in closes.values()]
    idx = drawdowns(index)
    out = []
    for d, _ in index:
        idd = idx.get(d)
        if idd is None:
            continue
        dds = [m[d] for m in mdd if d in m]
        if len(dds) >= max(1, len(closes) // 2):
            avg = mean(dds)
            out.append((d, round(idd, 4), round(avg, 4), round(idd - avg, 4), len(dds)))
    return out


def resolve(gs: list[tuple], k: int, horizon: int = HORIZON) -> dict:
    """The episode peaking at gs[k], resolved over the next `horizon` sessions."""
    d, idd, avg, gap, _ = gs[k]
    after = gs[k + 1:k + 1 + horizon]
    completed = len(after) == horizon
    deepest_index = min((x[1] for x in after), default=idd)
    best_member = max((x[2] for x in after), default=avg)
    if deepest_index <= idd - DEEPEN:
        how = "leaders fell"
    elif best_member >= avg + NARROW:
        how = "broadening"
    else:
        how = "unresolved"
    return {"peak": d, "gap_at_peak": gap, "index_dd_at_peak": idd,
            "member_dd_at_peak": avg, "deepest_index_dd": round(deepest_index, 4),
            "best_member_dd": round(best_member, 4), "resolution": how,
            "completed": completed}


def verdict(eps: list[dict]) -> tuple[str, Optional[float]]:
    done = [e for e in eps if e["completed"]]
    if len(done) < FLOOR:
        return (f"INSUFFICIENT -- {len(done)} completed episode(s), below the floor of "
                f"{FLOOR}; no rate prints"), None
    rate = sum(1 for e in done if e["resolution"] == "leaders fell") / len(done)
    return ("PASS" if rate >= PASS_SHARE else "FAIL"), rate


def study(series: dict) -> dict:
    gs = gap_series(series["closes"], series["index"])
    runs = episodes([(x[0], x[3] >= WIDE) for x in gs], MERGE_GAP)
    idx = {x[0]: i for i, x in enumerate(gs)}
    eps = []
    for a, b in runs:
        ks = [idx[d] for d in idx if a <= d <= b]
        k = max(ks, key=lambda i: gs[i][3])
        eps.append({"start": a, "end": b, **resolve(gs, k)})
    v, rate = verdict(eps)
    last = gs[-1] if gs else None
    body = [(f"The gap (the index's drawdown from its 52-week high less the average "
             f"member's) runs {gs[0][0]} to {last[0]}: **{last[3]:+.1f} points now** "
             f"(index {last[1]:+.1f}%, average member {last[2]:+.1f}%, "
             f"{last[4]} members)") if last else "No session carries enough members.",
            "",
            f"Wide-gap episodes (>= {WIDE:.0f} points): **{len(eps)}**, of which "
            f"**{sum(e['completed'] for e in eps)} completed** ({HORIZON} sessions "
            f"after the peak). " + (f"No rate prints below the floor of {FLOOR} "
                                    "completed episodes." if rate is None else
                                    f"Resolved by the leaders falling: "
                                    f"{100 * rate:.0f}%."),
            "",
            "| Peak | Gap | Index / average member at peak | Deepest index after "
            "| Best member after | Resolution | Completed |",
            "|---|---|---|---|---|---|---|"]
    for e in eps:
        body.append(f"| {e['peak']} | {e['gap_at_peak']:+.1f} | "
                    f"{e['index_dd_at_peak']:+.1f}% / {e['member_dd_at_peak']:+.1f}% | "
                    f"{e['deepest_index_dd']:+.1f}% | {e['best_member_dd']:+.1f}% | "
                    f"{e['resolution']} | {'yes' if e['completed'] else 'no'} |")
    body += ["", "**Sourced comparisons (the order's read, item 44; never episodes of "
                 "ours):**", ""] + [f"- {x}" for x in SOURCED]
    return {"item": ITEM, "title": TITLE, "as_of": last[0] if last else "-",
            "window": (f"{gs[0][0]} to {last[0]}; 52-week highs, horizon {HORIZON} "
                       f"sessions after each peak") if last else "-",
            "n": sum(1 for e in eps if e["completed"]),
            "statistic": ("the index's drawdown less the average member's (points); "
                          "for each wide-gap episode, whether the index's drawdown "
                          "deepened (leaders fell) or the average member's narrowed "
                          "(broadening) within six months"),
            "pass_rule": PASS_RULE, "verdict": v, "rights": RIGHTS, "body": body,
            "episodes": eps,
            "result": {"gap_now": last[3] if last else None, "episodes": len(eps),
                       "rate": rate,
                       "completed": sum(1 for e in eps if e["completed"])},
            "caveats": [
                "Today's members only: a member that fell out of the index is not in "
                "the history, so past gaps read narrower than a point-in-time list "
                "would show (survivorship).",
                "Price closes, not total return; an index drawdown is the S&P 500's "
                "own, not the members' cap-weighted average.",
                "The store's member closes reach two years back; a box re-run reads "
                "them, so its first 52-week window starts a year in.",
            ]}


MODE = {"public": "laptop run, public sources",
        "store": "box run, the observation store's newest vintages"}


def load_public(period: str = "5y") -> dict:
    from ..sources import sp500_members as m                    # noqa: PLC0415
    from . import sources as src                                # noqa: PLC0415
    data, _ = m.fetch_holdings()
    day0, rows = m.parse_holdings(data)
    tickers = sorted({m.yahoo_symbol(t) for t, _ in rows})
    closes = m.yahoo_closes(tickers, period)
    index = [x for x in src.yahoo("^GSPC")
             if x[0] >= min((s[0][0] for s in closes.values() if s), default="")]
    return {"closes": closes, "index": index,
            "sources": [f"SSGA's SPY holdings file, as of {day0} (membership; the "
                        f"constituent writer's reader)",
                        f"Yahoo daily closes, {period}, for its {len(tickers)} members "
                        f"(the same reader)", "Yahoo ^GSPC daily closes"]}


def load_store(db: Optional[str] = None) -> dict:
    from .. import observations, session                         # noqa: PLC0415
    from .. import st_r5_t1_rest as tr                           # noqa: PLC0415
    cut = session.utc_iso(timespec="microseconds")
    with observations.ObservationStore(db) as st:
        h = tr.holdings(st, cut, "sp500.member_weight")
        if not h["weights_pct"]:
            raise LookupError("the store holds no sp500.member_weight")
        closes = {}
        for tk in h["weights_pct"]:
            closes[tk] = sorted((str(r["observed_at"])[:10], float(r["value_num"]))
                                for r in st.as_of("sp500.member_close", cut, tk)
                                if r.get("value_num") is not None)
        index = sorted((str(r["observed_at"])[:10], float(r["value_num"]))
                       for r in st.as_of("yfinance.mkt_gspc", cut)
                       if r.get("value_num") is not None)
    return {"closes": closes, "index": index,
            "sources": [f"store sp500.member_weight (membership, {h['day']})",
                        "store sp500.member_close", "store yfinance.mkt_gspc"]}


def run(source: str = "public", out=None, db=None, run_date=None) -> tuple:
    series = load_public() if source == "public" else load_store(db)
    r = study(series)
    r["source_mode"] = MODE[source]
    r["sources"] = series["sources"] + [
        f"read {dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}"]
    return write_ledger(r, out, run_date), r


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog=f"python -m {__name__}")
    ap.add_argument("--source", choices=list(MODE), default="public")
    ap.add_argument("--out", default=None)
    ap.add_argument("--db", default=None)
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.WARNING)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    (md, csv_path), r = run(a.source, Path(a.out) if a.out else None, a.db)
    print(f"{ITEM}: {md} -- n {r['n']}, as of {r['as_of']}, {r['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
