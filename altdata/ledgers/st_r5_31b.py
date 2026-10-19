"""
ST-R5.31b -- the post-peak concentration ledger (Batch 6 item 31; docs/
change-order-signal-triage-batch-6-2026-10-15.md).

    python -m altdata.ledgers.st_r5_31b [--source public|store] [--out DIR] [--db PATH]

THE ORDER: "Base-rate ledger of post-peak paths (leaders' relative drawdown, time
to trough, breadth behaviour) for the five episodes." The read is BofA's: the
top basket's share of US market cap at bubble peaks -- railroads 63%, the 1920s
36%, the Nifty Fifty 40%, Japan 44% (of MSCI ACWI), TMT 41%. Rights:
"Calibration of an existing overlay input; no new weight." The order states NO
pass rule.

OUR MEASURE is the box's own (the ruling: "the box's own top-10 series is the
measure"): the ten largest issuers' share of the S&P 500 by SPY's holdings, a
second share class with its issuer (item 31's). History before the stored
holdings is BACK-CAST from one holdings day: each member's capitalisation moves
with its own close (cap_i(t) = w_i x P_i(t) / P_i(D0)), so share counts are held
at D0's and only today's members are in it. That is survivorship, stated, and
it is why the ledger's own n is small. BofA's five episodes are SOURCED
COMPARISONS from the order, labelled, never episodes of ours.

THE STUDY, per episode (a run of sessions with the share at or above the band's
low end, 40%, runs closer than MERGE_GAP sessions joined):
  the peak            the session of the run's highest share
  leaders' path       the peak-day top ten, cap-weighted, against the rest of the
                      members, cap-weighted: their relative value from the peak,
                      its low within HORIZON sessions (the relative drawdown) and
                      the sessions to that low (time to trough)
  breadth             the share of members above their 50-day average, at the
                      peak and at the trough
An episode is COMPLETED only when HORIZON sessions follow its peak.

THE PASS RULE, PRE-REGISTERED BY THIS FIRST EDITION (ruled 17 Oct 2026: "the
rule as stated, else the first edition's"), written before any run:
  PASS if at least FLOOR episodes are completed and, in at least 4 of every 5 of
  them, the peak-day top ten fell 10% or more against the rest within 24 months
  (504 sessions) of the peak. Fewer than FLOOR completed episodes: INSUFFICIENT,
  and no rate prints.
The floor is the order's own count, five episodes. Below it the ledger prints the
episodes and their paths, never a share of them.
"""

from __future__ import annotations

import argparse
import datetime as dt
import logging
import sys
from pathlib import Path
from typing import Optional

from . import Series, episodes, write_ledger

ITEM = "ST-R5.31b"
TITLE = "post-peak paths of top-10 concentration at the 40-44% band"
BAND_LOW = 40.0
TOP_N = 10
MERGE_GAP = 20
HORIZON = 504
FLOOR = 5
FALL = -10.0
PASS_SHARE = 0.8
MIN_COVERAGE = 0.9
PASS_RULE = ("Pre-registered by this first edition (the order states none): PASS if "
             f"at least {FLOOR} episodes are completed and in at least 4 of every 5 "
             f"the peak-day top ten fell {abs(FALL):.0f}% or more against the rest "
             f"within {HORIZON} sessions (24 months) of the peak; fewer than {FLOOR} "
             "completed: INSUFFICIENT, and no rate prints")
RIGHTS = ("Calibration of an existing overlay input; no new weight (the order). A "
          "PASS would let the peak-band flag be proposed as the Concentration & "
          "Complacency overlay's calibrated ceiling, for the operator to grant; "
          "INSUFFICIENT or FAIL keeps it report-only. This ledger grants nothing, "
          "and the queue entry (31c) is not filed.")
SOURCED = [("Railroads", "63%"), ("1920s utilities, telco, industrials", "36%"),
           ("Nifty Fifty", "40%"), ("Japan (of MSCI ACWI)", "44%"), ("TMT", "41%"),
           ("'AI Big 10' (Mag 7 + Broadcom, AMD, Micron)", "42%")]


def backcast(weights: dict[str, float], closes: dict[str, Series],
             day0: str) -> dict[str, dict[str, float]]:
    """{day: {ticker: cap}}: each member's D0 weight moved with its own close,
    on every session a member has a close and a D0 close exists."""
    out: dict[str, dict[str, float]] = {}
    for tk, w in weights.items():
        s = closes.get(tk) or []
        base = next((v for d, v in reversed(s) if d <= day0), None)
        if not base:
            continue
        for d, v in s:
            if d <= day0:
                out.setdefault(d, {})[tk] = w * v / base
    return out


def top_share(caps: dict[str, float], classes: dict, n: int = TOP_N
              ) -> tuple[float, list[str]]:
    """(the n largest issuers' share in percent, their tickers)."""
    by: dict[str, list] = {}
    for tk, c in caps.items():
        e = by.setdefault(classes.get(tk, tk), [0.0, []])
        e[0] += c
        e[1].append(tk)
    total = sum(caps.values())
    top = sorted(by.values(), key=lambda e: -e[0])[:n]
    return 100.0 * sum(e[0] for e in top) / total, sorted(t for e in top for t in e[1])


def share_series(caps_by_day: dict[str, dict[str, float]], classes: dict,
                 members: int) -> list[tuple[str, float, list[str]]]:
    """[(day, share, top tickers)] on the days at least MIN_COVERAGE of the
    members carry a cap."""
    out = []
    for d in sorted(caps_by_day):
        caps = caps_by_day[d]
        if len(caps) >= MIN_COVERAGE * members:
            s, top = top_share(caps, classes)
            out.append((d, s, top))
    return out


def above_50d(closes: dict[str, Series], day: str) -> Optional[float]:
    """The share of members whose close on `day` is above their 50-session mean."""
    up = n = 0
    for s in closes.values():
        win = [v for d, v in s if d <= day][-50:]
        if len(win) == 50 and any(d == day for d, _ in s[-len(s):]):
            n += 1
            up += win[-1] > sum(win) / 50
    return round(100.0 * up / n, 2) if n else None


def post_peak(caps_by_day: dict[str, dict[str, float]], days: list[str], peak: str,
              leaders: list[str], horizon: int = HORIZON) -> dict:
    """The leaders' value against the rest's from the peak: the low within the
    horizon (percent) and the sessions to it; completed if the horizon is in."""
    i0 = days.index(peak)
    after = days[i0:i0 + horizon + 1]

    def rel(d: str) -> Optional[float]:
        c = caps_by_day[d]
        lead = sum(c.get(t, 0.0) for t in leaders)
        rest = sum(v for t, v in c.items() if t not in leaders)
        return lead / rest if rest else None
    base = rel(peak)
    path = [(d, 100.0 * (rel(d) / base - 1.0)) for d in after if rel(d) is not None]
    low = min(path, key=lambda p: p[1])
    return {"relative_low_pct": round(low[1], 4), "trough": low[0],
            "sessions_to_trough": after.index(low[0]),
            "completed": len(after) == horizon + 1}


def verdict(eps: list[dict]) -> tuple[str, Optional[float]]:
    done = [e for e in eps if e["completed"]]
    if len(done) < FLOOR:
        return (f"INSUFFICIENT -- {len(done)} completed episode(s), below the floor of "
                f"{FLOOR}; no rate prints"), None
    hit = sum(1 for e in done if e["relative_low_pct"] <= FALL) / len(done)
    return ("PASS" if hit >= PASS_SHARE else "FAIL"), hit


def study(series: dict) -> dict:
    w, closes, day0 = series["weights"], series["closes"], series["holdings_day"]
    classes = series.get("classes") or {}
    caps = backcast(w, closes, day0)
    ss = share_series(caps, classes, len(w))
    days = [d for d, _, _ in ss]
    runs = episodes([(d, s >= BAND_LOW) for d, s, _ in ss], MERGE_GAP)
    eps = []
    by = {d: (s, top) for d, s, top in ss}
    for a, b in runs:
        inside = [d for d in days if a <= d <= b]
        peak = max(inside, key=lambda d: by[d][0])
        pp = post_peak(caps, days, peak, by[peak][1])
        eps.append({"start": a, "end": b, "peak": peak,
                    "peak_share_pct": round(by[peak][0], 2),
                    "leaders": " ".join(by[peak][1]), **pp,
                    "breadth_at_peak_pct": above_50d(closes, peak),
                    "breadth_at_trough_pct": above_50d(closes, pp["trough"])})
    v, rate = verdict(eps)
    now_d, now_s, now_top = ss[-1] if ss else (day0, None, [])
    body = [f"Our top-10 share (back-cast from SPY's holdings of {day0}; {len(w)} "
            f"members) runs {days[0] if days else '-'} to {now_d}: **{now_s:.1f}% now**"
            if now_s is not None else "No session carries enough members.",
            "",
            f"Episodes at or above {BAND_LOW:.0f}%: **{len(eps)}**, of which "
            f"**{sum(e['completed'] for e in eps)} completed** ({HORIZON} sessions "
            f"after the peak). " + ("No rate prints below the floor of "
                                    f"{FLOOR} completed episodes." if rate is None else
                                    f"Share with the leaders down {abs(FALL):.0f}% "
                                    f"or more against the rest: {100 * rate:.0f}%."),
            "",
            "| Peak | Share at peak | Leaders' low against the rest | Sessions to it "
            "| Completed | Above 50-day, peak / trough |",
            "|---|---|---|---|---|---|"]
    for e in eps:
        body.append(f"| {e['peak']} | {e['peak_share_pct']:.1f}% | "
                    f"{e['relative_low_pct']:+.1f}% | {e['sessions_to_trough']} | "
                    f"{'yes' if e['completed'] else 'no'} | "
                    f"{e['breadth_at_peak_pct']} / {e['breadth_at_trough_pct']} |")
    body += ["", "**Sourced comparisons (BofA via the order, item 31; never episodes "
                 "of ours):**", ""]
    body += [f"- {name}: {share} at the peak" for name, share in SOURCED]
    return {"item": ITEM, "title": TITLE, "as_of": now_d,
            "window": f"{days[0] if days else day0} to {now_d} (back-cast from "
                      f"{day0}); horizon {HORIZON} sessions after each peak",
            "n": sum(1 for e in eps if e["completed"]),
            "statistic": ("the peak-day top ten's value against the rest of the "
                          "members: its low within 24 months of the peak, the sessions "
                          "to it, and breadth (share above the 50-day) at peak and "
                          "trough"),
            "pass_rule": PASS_RULE, "verdict": v, "rights": RIGHTS, "body": body,
            "episodes": eps,
            "result": {"share_now": now_s, "episodes": len(eps), "rate": rate,
                       "completed": sum(1 for e in eps if e["completed"])},
            "caveats": [
                "Back-cast from one holdings day: today's members only, share counts "
                "held at that day's, so buybacks, issuance and index changes are not "
                "in the history (survivorship).",
                "BofA's baskets are defined ex post and its measures differ (Japan is "
                "a country share of ACWI); they are comparisons, not a sample.",
                "The store's own holdings begin 16 Oct 2026; the box's re-run "
                "back-casts from the store's newest holdings day the same way.",
            ]}


# ---------------------------------------------------------------------------
# The providers (the package's runner names neither 31b nor 44b; each runs here)
# ---------------------------------------------------------------------------
MODE = {"public": "laptop run, public sources",
        "store": "box run, the observation store's newest vintages"}


def load_public(period: str = "5y") -> dict:
    from ..sources import sp500_members as m                    # noqa: PLC0415
    from .. import st_r5_t1_rest as tr                           # noqa: PLC0415
    data, _ = m.fetch_holdings()
    day0, rows = m.parse_holdings(data)
    weights = {m.yahoo_symbol(t): w for t, w in rows}
    closes = m.yahoo_closes(sorted(weights), period)
    return {"weights": weights, "holdings_day": day0, "closes": closes,
            "classes": (tr.config().get("concentration") or {}).get("share_classes"),
            "sources": [f"SSGA's SPY holdings file, as of {day0} (the constituent "
                        f"writer's reader, altdata/sources/sp500_members.py)",
                        f"Yahoo daily closes, {period}, for its {len(weights)} members "
                        f"(the same reader)"]}


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
            rows = st.as_of("sp500.member_close", cut, tk)
            closes[tk] = sorted((str(r["observed_at"])[:10], float(r["value_num"]))
                                for r in rows if r.get("value_num") is not None)
    return {"weights": h["weights_pct"], "holdings_day": h["day"], "closes": closes,
            "classes": (tr.config().get("concentration") or {}).get("share_classes"),
            "sources": [f"store sp500.member_weight, holdings of {h['day']}",
                        "store sp500.member_close, each member's stored closes"]}


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
