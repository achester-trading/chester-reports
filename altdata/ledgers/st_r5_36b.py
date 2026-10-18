"""
ST-R5.36b -- the housing months-of-supply flag's ledger (Batch 6 item 36; docs/
change-order-signal-triage-batch-6-2026-10-15.md).

THE ORDER: "Flag: months of supply above the balanced-market line (~6 months,
existing homes) while mortgage rates rise -- a house-price-decline watch leading
the T&B Reinhart-Rogoff input. Base-rate ledger: real house-price change 12
months after months-of-supply crossings." It states NO pass rule.

A CROSSING: a month whose months of supply is above the line when the month
before was not, while the 30-year mortgage rate (MORTGAGE30US, its month's mean)
is higher than six months earlier -- the flag's own two conditions. THE STATISTIC:
the real house price's change over the next 12 months, the Case-Shiller national
index (CSUSHPINSA) over CPI (CPIAUCSL), against every month's 12-month change.

THE OPEN RULING (st-r5-rates notes, needs-you 4): Redfin's months of supply is its
own (inventory over the month's sales), not NAR's existing-home figure the
order's ~6-month line is drawn on, and Redfin's history begins January 2012. So the
ledger runs three rows, each labelled, none substituted for another:
  A  the order's line (6.0 months) on Redfin's series -- the item's named source;
  B  Redfin against its own 80th percentile (the ruling's first option);
  C  the Census Bureau's new-home months' supply (MSACSR, from 1963) at 6.0 -- new
     homes, not existing; the long history, for an n that means something.
Redfin's start is printed, and what its n allows is said.
"""

from __future__ import annotations

from . import NO_GATE, ordinal, Series, align, mean, percentile_rank, quantile, to_monthly_last

ITEM = "ST-R5.36b"
TITLE = "months-of-supply crossings and the real house price 12 months on"
LINE = 6.0
HORIZON = 12
RIGHTS = ("Flag only (the house-price-decline watch leading the T&B Reinhart-Rogoff "
          "input). Which months-of-supply series and line the flag uses is a ruling "
          "still open; this ledger grants nothing.")


def monthly_mean(s: Series) -> Series:
    acc: dict[str, list] = {}
    for d, v in s:
        acc.setdefault(d[:7] + "-01", []).append(v)
    return sorted((k, mean(v)) for k, v in acc.items())


def real_hpi(hpi: Series, cpi: Series) -> Series:
    return [(d, h / c) for d, h, c in align(to_monthly_last(hpi), to_monthly_last(cpi))]


def crossings(mos: Series, mort: Series, line: float) -> list[str]:
    m = dict(mort)
    keys = sorted(m)
    idx = {k: i for i, k in enumerate(keys)}
    out = []
    for (d0, v0), (d1, v1) in zip(mos, mos[1:]):
        if not (v0 <= line < v1):
            continue
        i = idx.get(d1)
        if i is None or i < 6:
            continue
        if m[keys[i]] > m[keys[i - 6]]:
            out.append(d1)
    return out


def change_after(real: Series, day: str, h: int = HORIZON):
    r = dict(real)
    keys = sorted(r)
    if day not in r:
        return None
    i = keys.index(day)
    if i + h >= len(keys):
        return None
    return 100.0 * (r[keys[i + h]] / r[day] - 1.0)


def row_for(label: str, mos: Series, mort: Series, real: Series, line: float) -> dict:
    xs = crossings(mos, mort, line)
    after = [(d, change_after(real, d)) for d in xs]
    done = [v for _, v in after if v is not None]
    keys = sorted(dict(real))
    rd = dict(real)
    base = [100.0 * (rd[keys[i + HORIZON]] / rd[keys[i]] - 1.0)
            for i in range(len(keys) - HORIZON) if keys[i] >= mos[0][0]]
    return {"label": label, "line": line, "start": mos[0][0][:7], "end": mos[-1][0][:7],
            "crossings": after, "n": len(done),
            "mean_after": mean(done) if done else None,
            "falling": sum(v < 0 for v in done),
            "base": mean(base) if base else None, "n_base": len(base)}


def study(series: dict) -> dict:
    mort = monthly_mean(series["mortgage"])
    real = real_hpi(series["hpi"], series["cpi"])
    redfin, census = series["redfin_mos"], series["census_mos"]
    p80 = quantile([v for _, v in redfin], 0.80)
    rows = [row_for("A. Redfin, the order's 6-month line", redfin, mort, real, LINE),
            row_for(f"B. Redfin, its own 80th percentile ({p80:.2f} months)",
                    redfin, mort, real, p80),
            row_for("C. Census new homes (MSACSR), 6 months", census, mort, real, LINE)]
    body = ["| Row | Window | Crossings (with 12 months after) | Real HPI 12m after (mean) | Falling | Every month (mean, n) |",
            "|---|---|---|---|---|---|"]
    for r in rows:
        body.append(f"| {r['label']} | {r['start']} to {r['end']} | {len(r['crossings'])} "
                    f"({r['n']}) | "
                    + (f"{r['mean_after']:+.2f}%" if r["mean_after"] is not None else "n/a")
                    + f" | {r['falling']} of {r['n']} | "
                    + (f"{r['base']:+.2f}% ({r['n_base']})" if r["base"] is not None else "n/a")
                    + " |")
    now_d, now_v = redfin[-1]
    body += ["",
             f"**Redfin's series begins {redfin[0][0][:7]}**: {len(redfin)} months. "
             f"Row A's n is {rows[0]['n']}; an n under 5 allows a description of the "
             f"episodes and no inference about the rule. Redfin's latest "
             f"({now_d[:7]}): {now_v:.1f} months, the "
             f"{ordinal(percentile_rank([v for _, v in redfin], now_v))} percentile of its "
             f"own history; the order's line is {LINE:.0f}."]
    episodes = [{"row": r["label"], "crossing_month": d[:7],
                 "real_hpi_12m_after_pct": None if v is None else round(v, 2)}
                for r in rows for d, v in r["crossings"]]
    return {"item": ITEM, "title": TITLE, "as_of": now_d[:7],
            "window": "; ".join(f"{r['label'][:2]} {r['start']} to {r['end']}" for r in rows),
            "n": rows[0]["n"],
            "statistic": "the real house price's change 12 months after each months-of-"
                         "supply crossing (with the mortgage rate rising), against every "
                         "month's",
            "pass_rule": "none stated (item 36: 'base-rate ledger: real house-price "
                         "change 12 months after months-of-supply crossings')",
            "verdict": NO_GATE, "rights": RIGHTS, "body": body, "episodes": episodes,
            "result": {r["label"][:1]: {"n": r["n"], "mean_after": r["mean_after"],
                                        "crossings": len(r["crossings"])} for r in rows},
            "caveats": [
                "n (the table's first number in brackets, row A) counts crossings with a "
                "full 12 months after them; the headline n is row A's.",
                "Rows B and C answer the open ruling's two options; neither is the order's "
                "flag until it is ruled.",
                "Redfin's months of supply is not seasonally adjusted.",
                "The real house price (Case-Shiller national over CPI) begins in 1987, "
                "so row C's crossings before then have no 12-month figure: its n "
                "counts only those after.",
            ]}


SERIES_PUBLIC = {"redfin_mos": ("redfin", "MONTHS OF SUPPLY"),
                 "census_mos": ("fred", "MSACSR"),
                 "mortgage": ("fred", "MORTGAGE30US"),
                 "hpi": ("fred", "CSUSHPINSA"), "cpi": ("fred", "CPIAUCSL")}
SERIES_STORE = {"redfin_mos": "redfin.months_of_supply", "census_mos": None,
                "mortgage": "fred.mortgage_30y", "hpi": "fred.case_shiller_national",
                "cpi": "fred.cpi"}
