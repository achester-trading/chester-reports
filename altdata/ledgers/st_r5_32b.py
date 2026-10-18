"""
ST-R5.32b -- the oil-shock classifier's ledger (Batch 6 item 32; docs/change-
order-signal-triage-batch-6-2026-10-15.md).

THE ORDER: "Two-condition oil-shock classifier (6-month rolling correlations:
Brent-SPX below its 20-year 20th percentile while Brent-10y is above its 80th) as
an inflation.driver sub-state ... feeding the item-25 quadrant (R28). Base-rate
ledger of SPX and 60/40 forward returns conditional on the regime." The
cautions: "use percentile thresholds, not sign, and ledger forward returns." It
states NO pass rule.

THE CLASSIFIER, as written: daily changes -- Brent and the S&P in log returns, the
10-year in bp -- on the days all three print; the 126-session (six-month) rolling
correlation of Brent with each; each placed against its own trailing 20 years
(5,040 sessions) of that correlation. Before 20 years of correlations exist the
window is every correlation so far, from ten years (2,520 sessions) -- printed as
the window's start. ON when Brent-SPX is at or below its 20th percentile and
Brent-10y at or above its 80th, the same day.

THE FORWARD RETURNS: the S&P's price return, and a 60/40 of the S&P and a
constant-duration 10-year (the bond's daily return approximated as y/252 less a
duration of 8 times the yield's change; stated, not a fund's NAV), over the next
63 and 126 sessions from each episode's first day, against the same horizons from
every day (the unconditional base).

THE QUADRANT: the order asks what item 25's quadrant did in the following two
quarters. The quadrant is not built (altdata/attribution.py quadrant_factors()
returns None), so that column prints "not built", never a stand-in.
"""

from __future__ import annotations

import math

from . import NO_GATE, ordinal, Series, align, corr, episodes, mean, percentile_rank

ITEM = "ST-R5.32b"
TITLE = "the oil-shock classifier: supply-shock episodes and what followed"
WINDOW = 126
LOOKBACK = 5040
MIN_LOOKBACK = 2520
LO_PCT, HI_PCT = 20.0, 80.0
DURATION = 8.0
HORIZONS = (63, 126)
RIGHTS = ("A sub-state (inflation.driver) and a Book A rule-table modifier: oil "
          "and commodities to the hedge sleeve while the regime is on. With no gate "
          "in the order, the sub-state stays as built in Tranche 1 and this ledger "
          "grants no modifier.")


def daily_changes(brent: Series, spx: Series, y10: Series) -> list[tuple]:
    rows = align(brent, spx, y10)
    out = []
    for (d0, b0, s0, y0), (d1, b1, s1, y1) in zip(rows, rows[1:]):
        if b0 > 0 and b1 > 0 and s0 > 0 and s1 > 0:
            out.append((d1, math.log(b1 / b0), math.log(s1 / s0), 100.0 * (y1 - y0),
                        s1, y1))
    return out


def classify(chg: list[tuple], window: int = WINDOW, lookback: int = LOOKBACK,
             min_lookback: int = MIN_LOOKBACK) -> list[dict]:
    """Per day from the first full lookback: both correlations, their
    percentiles against the trailing correlations, and ON/off."""
    cs, cy, out = [], [], []
    for i in range(window - 1, len(chg)):
        w = chg[i - window + 1:i + 1]
        c_s = corr([x[1] for x in w], [x[2] for x in w])
        c_y = corr([x[1] for x in w], [x[3] for x in w])
        if c_s is None or c_y is None:
            continue
        cs.append(c_s)
        cy.append(c_y)
        if len(cs) < min_lookback:
            continue
        hs, hy = cs[-lookback:], cy[-lookback:]
        ps, py = percentile_rank(hs, c_s), percentile_rank(hy, c_y)
        out.append({"date": chg[i][0], "corr_brent_spx": c_s, "corr_brent_10y": c_y,
                    "pct_spx": ps, "pct_10y": py,
                    "on": ps <= LO_PCT and py >= HI_PCT, "i": i})
    return out


def forward(chg: list[tuple], i: int, h: int) -> tuple:
    """(S&P %, 60/40 %) over the next h sessions from index i, or None."""
    if i + h >= len(chg):
        return None, None
    s = math.exp(sum(x[2] for x in chg[i + 1:i + h + 1])) - 1.0
    b = 1.0
    for x in chg[i + 1:i + h + 1]:
        y = x[5]
        b *= 1.0 + y / 100.0 / 252.0 - DURATION * x[3] / 10000.0
    b -= 1.0
    return 100.0 * s, 100.0 * (0.6 * s + 0.4 * b)


def study(series: dict) -> dict:
    chg = daily_changes(series["brent"], series["spx"], series["y10"])
    days = classify(chg)
    if not days:
        raise ValueError("too little history for the classifier's lookback")
    eps = episodes([(d["date"], d["on"]) for d in days], merge_gap=21)
    by_date = {d["date"]: d for d in days}
    rows, cond = [], {h: ([], []) for h in HORIZONS}
    for a, b in eps:
        i = by_date[a]["i"]
        row = {"start": a, "end": b,
               "sessions": sum(1 for d in days if a <= d["date"] <= b),
               "corr_brent_spx": round(by_date[a]["corr_brent_spx"], 3),
               "corr_brent_10y": round(by_date[a]["corr_brent_10y"], 3)}
        for h in HORIZONS:
            s, p = forward(chg, i, h)
            row[f"spx_{h}d_pct"] = None if s is None else round(s, 2)
            row[f"6040_{h}d_pct"] = None if p is None else round(p, 2)
            if s is not None:
                cond[h][0].append(s)
                cond[h][1].append(p)
        row["item25_quadrant_next_2q"] = "not built"
        rows.append(row)
    base = {}
    for h in HORIZONS:
        fw = [forward(chg, d["i"], h) for d in days]
        fw = [x for x in fw if x[0] is not None]
        base[h] = (mean([x[0] for x in fw]), mean([x[1] for x in fw]), len(fw))
    now = days[-1]
    body = [
        f"The classifier ran on {len(days):,} sessions ({days[0]['date']} to "
        f"{now['date']}): **{len(eps)} episodes**, merging runs fewer than 22 "
        f"sessions apart. The regime is **{'ON' if now['on'] else 'off'}** on "
        f"{now['date']}: Brent-SPX {now['corr_brent_spx']:+.2f} (the "
        f"{ordinal(now['pct_spx'])} percentile), Brent-10y {now['corr_brent_10y']:+.2f} "
        f"(the {ordinal(now['pct_10y'])}).",
        "",
        "| Horizon | S&P after an episode start (mean, n) | S&P, every day | 60/40 after a start | 60/40, every day |",
        "|---|---|---|---|---|"]
    for h in HORIZONS:
        s_c, p_c = cond[h]
        body.append(
            f"| {h} sessions | "
            + (f"{mean(s_c):+.2f}% (n={len(s_c)})" if s_c else "n/a (n=0)")
            + f" | {base[h][0]:+.2f}% (n={base[h][2]:,}) | "
            + (f"{mean(p_c):+.2f}%" if p_c else "n/a")
            + f" | {base[h][1]:+.2f}% |")
    body += ["", "What item 25's quadrant did in the two quarters after each episode: "
                 "not built (the quadrant does not exist yet; no stand-in is used)."]
    return {"item": ITEM, "title": TITLE, "as_of": now["date"],
            "window": f"{days[0]['date']} to {now['date']} (classifier); trailing "
                      f"{LOOKBACK:,} sessions for the percentiles, from "
                      f"{MIN_LOOKBACK:,} until 20 years exist",
            "n": len(eps),
            "statistic": "episodes of the two-condition regime; mean S&P and 60/40 "
                         "returns 63 and 126 sessions after each start against every "
                         "day's",
            "pass_rule": "none stated (item 32 asks for a 'base-rate ledger of SPX and "
                         "60/40 forward returns conditional on the regime')",
            "verdict": NO_GATE, "rights": RIGHTS, "body": body, "episodes": rows,
            "result": {"episodes": len(eps), "on_now": now["on"], "base": base,
                       "cond": {h: (mean(cond[h][0]) if cond[h][0] else None,
                                    len(cond[h][0])) for h in HORIZONS}},
            "caveats": [
                "Six-month windows of daily changes are noisy, as the order warns; "
                "episodes are few and overlapping horizons are not independent.",
                "The 60/40's bond leg is a constant-duration approximation, stated.",
                "Brent's daily history begins May 1987, so 20-year percentiles exist "
                "only from about 2007; earlier days use every correlation from ten years.",
            ]}


SERIES_PUBLIC = {"brent": ("fred", "DCOILBRENTEU"), "spx": ("yahoo", "^GSPC"),
                 "y10": ("fred", "DGS10")}
SERIES_STORE = {"brent": "fred.brent", "spx": "yfinance.mkt_gspc",
                "y10": "fred.yield_10y"}
