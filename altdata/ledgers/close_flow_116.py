"""
Item 116's calibration ledger (signal-triage Batch 22, the order's 98.2; SR-77,
provisional; A128, 6 Nov 2026), through the event-study utility
(altdata/event_study.py, Batch 16 item 91(a)).

    python -m altdata.ledgers run close-flow [--source public|store]

PRE-REGISTERED before this code: docs/ledgers/close-flow-preregistration-2026-11.md,
whose SHA-256 config/levered_etf.yaml and tools/validate_item_116.py hold. Read it
for the event, the measures and the absent pass rule; this module applies them
and changes none.

THE EVENT. A stored 16:45 session whose |total in % of ADV| is at or above the
90th percentile of the stored sessions' (the top decile). Below 20 stored
sessions: "accruing (n=k of 20)", and no event is defined.

THE ROWS. The two seed rows first (5 Jun and 5 Nov 2026, the order's dollar
figures, marked "seed, order's figure"; judgment drafts for the operator's
accept-all, rule 31), then the events. Each row measures the bucket's index ETF
and SPY: the last 30 minutes (5-minute bars), the gap at the next open, and the
1- and 5-session forward returns. A window not yet closed is "pending".

A public run holds no close-flow history (it is the box's store's alone), so it
defines no event and measures the seeds from Yahoo. Nothing here grants a right.
"""

from __future__ import annotations

import datetime as dt
from typing import Optional

from .. import event_study as es
from .. import session
from . import NO_GATE, fmt

ITEM = "close-flow"
TITLE = ("Item 116's levered-ETF close flow: the top decile by % of ADV, the last "
         "30 minutes, the next open, +1 and +5")
PREREG = "docs/ledgers/close-flow-preregistration-2026-11.md"
PASS_RULE = ("none stated -- the order names no pass rule; log-only until about 20 "
             "events (pre-registered: " + PREREG + ")")
RIGHTS = ("None: the ledger grants nothing. It enters no composite, flag table, the "
          "T&B intake queue or the market-state object, and changes neither the 15:00 "
          "flag nor the DTH-1 draft setup.")
MIN_STORED = 20
DECILE = 0.90
SLOT = "1645"
INDEX_ETF = {"semiconductors": "smh", "nasdaq_100": "qqq", "sp_500": "spy",
             "russell_2000": "iwm"}
ETFS = ("smh", "qqq", "spy", "iwm")
YAHOO = {"smh": "SMH", "qqq": "QQQ", "spy": "SPY", "iwm": "IWM"}
STORE_CLOSE = {e: f"yfinance.mkt_{e}" for e in ETFS}
BARS = ("spy", "qqq", "iwm")       # the bars table's equity instruments (SMH has none)
SEEDS = [
    {"day": "2026-06-05", "flow": -55e9, "index": "spy",
     "mark": "seed, order's figure",
     "note": "MS's estimate ('the $55bn sold on 5 Jun 2026'); the order gives no bucket split, so SPY"},
    {"day": "2026-11-05", "flow": -52e9, "index": "smh",
     "mark": "seed, order's figure; estimate, unconfirmed (V-98a open)",
     "note": "MS's estimate at the 1pm prices; the largest named bucket, semiconductors ($21bn), so SMH"},
]


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------
def _by_session(bars: list[dict]) -> dict[str, dict[str, dict]]:
    """{ET session date: {"HH:MM" ET bar start: bar}}."""
    tz = session._eastern_tz()                                  # noqa: SLF001
    out: dict[str, dict[str, dict]] = {}
    for b in bars:
        t = dt.datetime.fromisoformat(str(b["start"]).replace("Z", "+00:00"))
        t = (t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)).astimezone(tz)
        out.setdefault(t.date().isoformat(), {})[t.strftime("%H:%M")] = b
    return out


def load(source: str, db: Optional[str] = None) -> dict:
    from . import sources as src                                # noqa: PLC0415
    s: dict = {"mode": source, "closes": {}, "opens": {}, "bars": {}}
    if source == "public":
        for e in ETFS:
            o = src.yahoo_ohlc(YAHOO[e])
            s["closes"][e], s["opens"][e] = o["close"], o["open"]
            s["bars"][e] = _by_session(src.yahoo_5m(YAHOO[e]))
        s["pct"], s["total"], s["buckets"] = [], [], {}
        return s
    for e in ETFS:
        s["closes"][e] = src.store_or_empty(STORE_CLOSE[e], db=db)
    for e in BARS:
        bs = _by_session(src.bars_5m(e, db))
        s["bars"][e] = bs
        s["opens"][e] = sorted((d, b["09:30"]["open"]) for d, b in bs.items() if "09:30" in b)
    s["pct"] = src.store_or_empty("calc.close_flow.total_pct_adv", SLOT, db)
    s["total"] = src.store_or_empty("calc.close_flow.total", SLOT, db)
    s["buckets"] = {b: src.store_or_empty(f"calc.close_flow.{b}", SLOT, db)
                    for b in INDEX_ETF}
    return s


def sources_list(source: str) -> list[str]:
    if source == "public":
        return ["the close-flow history: the box's store only (calc.close_flow.*, "
                "instrument 1645); a public run holds none",
                "daily opens and closes: Yahoo SMH, QQQ, SPY, IWM through the one "
                "yfinance import",
                "5-minute bars: Yahoo, the last 60 days only"]
    return [f"calc.close_flow.total_pct_adv, .total and the index buckets, instrument {SLOT}",
            "daily closes: " + ", ".join(STORE_CLOSE.values()),
            "5-minute bars (opens and the last 30 minutes): the bars table's "
            + ", ".join(BARS) + "; SMH has none"]


# ---------------------------------------------------------------------------
# The measures
# ---------------------------------------------------------------------------
def last30(bars: dict, day: str) -> Optional[float]:
    """The last 5-minute bar's close against the open of the bar 30 minutes
    before the close (15:30-16:00 ET; 12:30-13:00 on an early close)."""
    b = (bars or {}).get(day) or {}
    close = dt.datetime.combine(dt.date.fromisoformat(day), session.close_time_et(day))
    first = (close - dt.timedelta(minutes=30)).strftime("%H:%M")
    last = (close - dt.timedelta(minutes=5)).strftime("%H:%M")
    if first not in b or last not in b or not b[first]["open"]:
        return None
    return b[last]["close"] / b[first]["open"] - 1.0


def gap(closes: list, opens: list, day: str) -> Optional[float]:
    """The next session's open against the event session's close."""
    i = es.position(closes, day)
    if i is None or i + 1 >= len(closes):
        return None
    nxt = closes[i + 1][0]
    o = dict(opens).get(nxt)
    return None if o is None or not closes[i][1] else o / closes[i][1] - 1.0


def measures(s: dict, etf: str, day: str) -> dict:
    c = s["closes"].get(etf) or []
    return {"last30": last30(s["bars"].get(etf), day),
            "gap": gap(c, s["opens"].get(etf) or [], day),
            "fwd1": es.forward(c, day, 1), "fwd5": es.forward(c, day, 5),
            "in_series": es.position(c, day) is not None}


def events(pct: list) -> tuple[Optional[float], list[str], int]:
    """(the cut, the event sessions, the stored count): below MIN_STORED, no cut and
    no events."""
    k = len(pct)
    if k < MIN_STORED:
        return None, [], k
    from . import quantile                                      # noqa: PLC0415
    cut = quantile([abs(v) for _, v in pct], DECILE)
    return cut, [d for d, v in pct if abs(v) >= cut], k


def dominant(buckets: dict, day: str) -> str:
    best, etf = None, "spy"
    for b, ser in buckets.items():
        v = dict(ser).get(day)
        if v is not None and (best is None or abs(v) > best):
            best, etf = abs(v), INDEX_ETF[b]
    return etf


def _cell(v: Optional[float], in_series: bool, pending: bool) -> str:
    if v is not None:
        return fmt(100.0 * v, 2, pct=True)
    if not in_series:
        return "not stored"
    return "pending" if pending else "not available"


# ---------------------------------------------------------------------------
# The study
# ---------------------------------------------------------------------------
def study(s: dict) -> dict:
    cut, evs, k = events(s.get("pct") or [])
    pct, total = dict(s.get("pct") or []), dict(s.get("total") or [])
    rows = []
    for n, sd in enumerate(SEEDS, 1):
        rows.append({"row": n, "day": sd["day"], "flow": sd["flow"], "pct_adv": None,
                     "mark": sd["mark"], "index": sd["index"], "note": sd["note"]})
    for d in evs:
        rows.append({"row": len(rows) + 1, "day": d, "flow": total.get(d),
                     "pct_adv": pct.get(d), "mark": "event (top decile)",
                     "index": dominant(s.get("buckets") or {}, d), "note": ""})
    spy_dates = [d for d, _ in s["closes"].get("spy") or []]
    as_of = spy_dates[-1] if spy_dates else dt.date.today().isoformat()
    episodes, table = [], []
    for r in rows:
        mi, ms = measures(s, r["index"], r["day"]), measures(s, "spy", r["day"])
        sign = 1.0 if (r["flow"] or 0) > 0 else -1.0
        pend = lambda m, h: m["in_series"] and m[h] is None    # noqa: E731
        ep = {"row": r["row"], "session": r["day"], "mark": r["mark"],
              "flow_usd": r["flow"], "pct_adv": r["pct_adv"], "index": r["index"].upper()}
        for tag, m in (("index", mi), ("spy", ms)):
            for h in ("last30", "gap", "fwd1", "fwd5"):
                ep[f"{tag}_{h}"] = m[h]
        ep["gap_against_flow"] = (None if mi["gap"] is None
                                  else bool(mi["gap"] * sign < 0))
        episodes.append(ep)
        flow_s = ("n/a" if r["flow"] is None else
                  f"{'-' if r['flow'] < 0 else '+'}${abs(r['flow']) / 1e9:,.1f}bn")
        pa = "n/a" if r["pct_adv"] is None else f"{r['pct_adv']:+.2f}%"
        table.append(
            f"| {r['row']} | {r['day']} | {flow_s} | {pa} | {r['mark']} | "
            f"{r['index'].upper()} | {_cell(mi['last30'], mi['in_series'], False)} | "
            f"{_cell(mi['gap'], mi['in_series'], pend(mi, 'gap'))} | "
            f"{_cell(mi['fwd1'], mi['in_series'], pend(mi, 'fwd1'))} | "
            f"{_cell(mi['fwd5'], mi['in_series'], pend(mi, 'fwd5'))} | "
            f"{_cell(ms['last30'], ms['in_series'], False)} | "
            f"{_cell(ms['gap'], ms['in_series'], pend(ms, 'gap'))} | "
            f"{_cell(ms['fwd1'], ms['in_series'], pend(ms, 'fwd1'))} | "
            f"{_cell(ms['fwd5'], ms['in_series'], pend(ms, 'fwd5'))} |")
    body = []
    if cut is None:
        body.append(f"**Accruing (n={k} of {MIN_STORED}).** {k} stored 16:45 session(s); "
                    f"below {MIN_STORED} no decile, and so no event, is defined. "
                    + ("A public run holds no close-flow history: it is the box's "
                       "store's alone, from the first live run (6 Nov 2026)."
                       if s.get("mode") == "public" else ""))
    else:
        body.append(f"**The cut:** |% of ADV| at or above {cut:.2f}% (the 90th percentile "
                    f"of {k} stored 16:45 sessions). **Events:** {len(evs)}.")
    body += ["", "| Row | Session | Flow | % of ADV | Marked | Index | Last 30 min | "
                 "Next open | +1 | +5 | SPY last 30 | SPY next open | SPY +1 | SPY +5 |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"] + table
    body += ["", "The seed rows' flows are the order's figures (MS's estimates), entered "
                 "as judgment drafts for the operator's accept-all (rule 31). Every return "
                 "comes from the series named under Sources; nothing else in a seed row is "
                 "entered by hand."]
    ev_eps = [e for e in episodes if e["mark"].startswith("event")]
    if ev_eps:
        body += ["", "| Measure (the bucket's index, over the events) | n | Mean | Median "
                     "| Mean with the flow |", "|---|---|---|---|---|"]
        for h, lab in (("last30", "Last 30 minutes"), ("gap", "Gap at the next open"),
                       ("fwd1", "+1 session"), ("fwd5", "+5 sessions")):
            a = es.average(e[f"index_{h}"] for e in ev_eps)
            w = es.average(None if e[f"index_{h}"] is None or e["flow_usd"] is None
                           else e[f"index_{h}"] * (1 if e["flow_usd"] > 0 else -1)
                           for e in ev_eps)
            body.append(f"| {lab} | {a['n']} | {fmt(None if a['mean'] is None else 100 * a['mean'], 2, True)} "
                        f"| {fmt(None if a['median'] is None else 100 * a['median'], 2, True)} "
                        f"| {fmt(None if w['mean'] is None else 100 * w['mean'], 2, True)} |")
        g = [e["gap_against_flow"] for e in ev_eps if e["gap_against_flow"] is not None]
        body.append("")
        body.append(f"Gap at the next open against the flow (the DTH-1 reversal): "
                    f"{sum(g)} of {len(g)}." if g else
                    "Gap at the next open against the flow: no event with a next open yet.")
    window = (f"stored 16:45 sessions from the first live run (6 Nov 2026) to {as_of}: "
              f"{k} stored" if s.get("mode") != "public" else
              f"the close-flow history is the box's store's alone; a public run holds "
              f"none (k = 0); the seeds' returns to {as_of}")
    verdict = (f"ACCRUING (n={k} of {MIN_STORED}). " if cut is None else "") + NO_GATE
    return {"item": ITEM, "title": TITLE, "as_of": as_of, "window": window,
            "n": len(evs), "statistic": ("per measure over the events: n, the mean, the "
                                         "median and the mean with the flow; the share "
                                         "of next-open gaps against the flow"),
            "pass_rule": PASS_RULE, "verdict": verdict, "rights": RIGHTS,
            "body": body, "episodes": episodes,
            "caveats": ["V-98a (the 5 Nov tally against MS's $52bn) is open: row 2 is an "
                        "estimate, unconfirmed.",
                        "The decile is recomputed at every edition, so a session can "
                        "enter or leave the set as the history grows.",
                        "SMH has no 5-minute bars in the store; a semiconductors-led "
                        "event's last 30 minutes print 'not stored' (SPY's beside it)."]}
