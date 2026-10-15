"""
A synthetic observation store for the Alpha Lab's Tranche 2 gates.

Seven-odd years of session-day series, deterministic from a seed, with the
episodes the first batch's rules look for PLANTED so each fires and the harness
has trades to judge -- none of it real data, none of it a figure from the box:

  * prices (yfinance.*): SPY with its open, high, low and volume; RSP; the
    eleven SPDR sectors (XLRE from 2015-10 and XLC from 2018-06, as stored);
    HYG, IEF, LQD, TLT; QQQ, IWM, GLD, UUP, EFA as a trend basket. Available
    20 minutes after the close, as the backfill declares.
  * FRED (fred.*): the CCC, BB and IG OAS and the 10-year yield, each knowable
    the next morning; ACM's 10-year term premium (acm.term_premium_10y), too.
  * the market-state object per session, its gamma dial alternating by month.
  * CPI release events (the events table), scheduled a month ahead.
  * the dealer series the VRP engine's coverage check reads, for 60 sessions.
  * a prediction-market contract and the fed-funds-implied probability for
    one meeting, for the prediction-market engine.

The planted episodes:
  H-002  every fourth ISO week after the warm-up is a "defensive up week" (SPY
         up, XLU and XLP leading), followed by a soft week; RSP/SPY drifts down
         throughout, so it sits low in its five-year range.
  H-004  every 110 sessions, CCC OAS widens 2.5 bp a day for 20 days while BB
         and IG stay flat, and HYG lags IEF for the next 20.
  H-005  the 10-year yield trends up, so its five-year percentile is high.
"""

from __future__ import annotations

import datetime as dt
import json
import math
import random
import sqlite3

from altdata import observations, session

SECTORS = ["XLK", "XLF", "XLE", "XLV", "XLI", "XLP", "XLY", "XLU", "XLB", "XLRE", "XLC"]
STARTS = {"XLRE": "2015-10-08", "XLC": "2018-06-19"}
TREND = ["QQQ", "IWM", "GLD", "UUP", "EFA"]


def sessions(first: str, last: str) -> list[str]:
    d, d1, out = dt.date.fromisoformat(first), dt.date.fromisoformat(last), []
    while d <= d1:
        if session.is_trading_session(d):
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def _next_day(day: str) -> str:
    return (dt.date.fromisoformat(day) + dt.timedelta(days=1)).isoformat()


def build(path: str, first: str = "2018-01-02", last: str = "2026-10-09",
          seed: int = 11) -> dict:
    rng = random.Random(seed)
    days = sessions(first, last)
    warm = 1260
    rows: list[dict] = []

    def put(key: str, day: str, value, avail: str, instrument=None) -> None:
        rows.append({"registry_key": key, "instrument": instrument,
                     "observed_at": day, "available_at": avail, "value": value,
                     "source": "synthetic"})

    px = {s: 100.0 for s in ["SPY", "RSP", "HYG", "IEF", "LQD", "TLT"] + SECTORS + TREND}
    px["SPY"] = 250.0
    y10, ccc, bb, ig, tp = 2.4, 9.0, 3.2, 1.1, 0.2
    credit_left = 0
    week_kind: dict[tuple, str] = {}
    prev_week = None
    for i, d in enumerate(days):
        date = dt.date.fromisoformat(d)
        wk = date.isocalendar()[:2]
        if wk not in week_kind:
            n = len(week_kind)
            kind = "normal"
            if i > warm and n % 4 == 0:
                kind = "defensive_up"
            elif prev_week and week_kind.get(prev_week) == "defensive_up":
                kind = "soft"
            week_kind[wk] = kind
            prev_week = wk
        kind = week_kind[wk]
        mkt = rng.gauss(0.0003, 0.008)
        if kind == "defensive_up":
            mkt = 0.004
        elif kind == "soft":
            mkt = -0.003
        prev = px["SPY"]
        px["SPY"] *= 1 + mkt
        o = prev * (1 + rng.gauss(0, 0.002))
        hi = max(o, px["SPY"]) * (1 + abs(rng.gauss(0, 0.003)))
        lo = min(o, px["SPY"]) * (1 - abs(rng.gauss(0, 0.003)))
        avail = f"{d}T20:20:00+00:00"
        for suf, v in (("", px["SPY"]), ("_open", o), ("_high", hi), ("_low", lo),
                       ("_volume", 8.0e7)):
            put(f"yfinance.mkt_spy{suf}", d, v, avail)
        px["RSP"] *= 1 + mkt - 0.0004 + rng.gauss(0, 0.002)
        put("yfinance.mkt_rsp", d, px["RSP"], avail)
        for s in SECTORS:
            if s in STARTS and d < STARTS[s]:
                continue
            r = mkt + rng.gauss(0, 0.006)
            if kind == "defensive_up":
                r = 0.009 if s in ("XLU", "XLP") else 0.001 + rng.gauss(0, 0.001)
            px[s] *= 1 + r
            put(f"yfinance.mkt_{s.lower()}", d, px[s], avail)
        for s in TREND:
            drift = {"QQQ": 0.0006, "IWM": 0.0001, "GLD": 0.0004, "UUP": -0.0001,
                     "EFA": 0.0002}[s]
            px[s] *= 1 + drift + rng.gauss(0, 0.009)
            put(f"yfinance.mkt_{s.lower()}", d, px[s], avail)
            put(f"yfinance.mkt_{s.lower()}_volume", d, 2.0e7, avail)
        # credit and rates
        if i % 110 == 60 and i > 80:
            credit_left = 20
        if credit_left:
            ccc += 0.025
            credit_left -= 1
            hyg_r, ief_r = -0.0002, 0.0006
            if credit_left == 0:
                credit_left = -20
        elif credit_left < 0:
            ccc -= 0.02
            hyg_r, ief_r = -0.0025, 0.0010
            credit_left += 1
        else:
            ccc += rng.gauss(0, 0.01)
            hyg_r, ief_r = 0.0002 + rng.gauss(0, 0.003), rng.gauss(0, 0.003)
        bb += rng.gauss(0, 0.004)
        ig += rng.gauss(0, 0.002)
        y10 = max(0.5, y10 + 0.0012 + rng.gauss(0, 0.03))
        tp += rng.gauss(0, 0.02)
        px["HYG"] *= 1 + hyg_r
        px["IEF"] *= 1 + ief_r - (y10 - 2.4) * 0.00001
        px["LQD"] *= 1 + 0.6 * ief_r + 0.3 * hyg_r
        px["TLT"] *= 1 - 0.0012 * 16 / 10 + rng.gauss(0, 0.007) + 0.0019
        for s in ("HYG", "IEF", "LQD", "TLT"):
            put(f"yfinance.mkt_{s.lower()}", d, px[s], avail)
        nxt = f"{_next_day(d)}T14:00:00+00:00"
        put("fred.ccc_oas", d, round(ccc, 4), nxt)
        put("fred.bb_oas", d, round(bb, 4), nxt)
        put("fred.ig_oas", d, round(ig, 4), nxt)
        put("fred.yield_10y", d, round(y10, 4), nxt)
        put("acm.term_premium_10y", d, round(tp, 4), nxt)
        gamma = "positive" if date.month % 2 else "negative"
        obj = {"object": "market_state", "session": d,
               "dials": {"macro": {"state": "Expansion"},
                         "vol": {"state": "calm" if i % 3 else "elevated"},
                         "gamma": {"state": gamma}},
               "session_events": []}
        put("market_state", d, json.dumps(obj), f"{d}T21:00:00+00:00")
    # the dealer series (the VRP engine's coverage check) for the last 60 sessions
    for d in days[-60:]:
        put("exposure.net_gex", d, 1.5e9, f"{d}T20:30:00+00:00", "SPY")
    # one prediction-market contract against the fed-funds-implied probability
    for k, d in enumerate(days[-30:]):
        a = f"{d}T21:30:00+00:00"
        put("pm.bid", d, 0.52 + 0.002 * k, a, "KX-FED-TEST")
        put("pm.ask", d, 0.55 + 0.002 * k, a, "KX-FED-TEST")
    st = observations.ObservationStore(path)
    st.write_many(rows)
    st.close()
    # CPI release events, each scheduled (knowable) a month ahead
    from altdata import events                                  # noqa: PLC0415
    con = sqlite3.connect(path)
    con.executescript(events.SCHEMA)
    y, m = int(first[:4]), int(first[5:7])
    n_ev = 0
    while f"{y:04d}-{m:02d}" <= last[:7]:
        rel = dt.date(y, m, 12)
        while not session.is_trading_session(rel):
            rel += dt.timedelta(days=1)
        known = (rel - dt.timedelta(days=30)).isoformat() + "T12:00:00+00:00"
        con.execute("INSERT INTO events (content_hash, type, observed_at, available_at,"
                    " ingested_at, source, title) VALUES (?,?,?,?,?,?,?)",
                    (f"cpi-{rel}", "scheduled", rel.isoformat(),
                     observations.canonical_instant(known),
                     observations.canonical_instant(known), "synthetic",
                     "Consumer Price Index"))
        n_ev += 1
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    con.commit()
    con.close()
    return {"sessions": len(days), "rows": len(rows), "cpi_events": n_ev,
            "first": days[0], "last": days[-1]}


if __name__ == "__main__":                                      # pragma: no cover
    import sys
    print(build(sys.argv[1]))
