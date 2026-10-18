"""
ST-R5.35b -- the corporate-price/ULC gap's ledger (Batch 6 item 35; docs/change-
order-signal-triage-batch-6-2026-10-15.md).

THE ORDER: "Corporate-price/ULC gap as a derived series (PPI final demand less
foods, energy and trade services; ULC nonfarm business, quarterly, PPI leg
monthly) ... with a margin-source attribution line (pricing vs cost) ... Flag: gap
closing from above as a leading input to the item-29 revisions-turn flag ...
Base-rate ledger of margin behaviour after gap peaks." It states NO pass rule.

THE GAP: PPI's change on the year (WPSFD49116, monthly, its quarter's mean) less
unit labor costs' (ULCNFB, nonfarm business, quarterly), in pp -- ST-R5.35a's
definition. MARGIN SOURCE per quarter: "price" when the gap is positive (prices
rising faster than unit labor costs), "cost" when negative.

THE MARGIN: nonfinancial corporate profits after tax, with inventory valuation
and capital consumption adjustments (NFCPATAX), over nonfinancial corporate gross
value added (A455RC1Q027SBEA), percent -- a profit share, quarterly.

A GAP PEAK: a quarter whose gap is positive and higher than the two quarters on
each side (a local maximum over five quarters). The statistic: the margin's change
in pp over the next 4 and 8 quarters after each peak, against every quarter's.

THE SHORT LEG: the order's PPI series begins in 2013 (its index base August 2013),
so n is small. A LONGER ROBUSTNESS ROW uses PPI finished goods less foods and
energy (WPSFD4131, from 1974) -- a different index, labelled as such, never
substituted for the order's.
"""

from __future__ import annotations

from . import NO_GATE, Series, align, mean, to_quarterly_mean, yoy

ITEM = "ST-R5.35b"
TITLE = "the corporate-price/ULC gap and margins after its peaks"
HORIZONS = (4, 8)
RIGHTS = ("Flag only: the gap closing from above as a leading input to item 29's "
          "revisions-turn flag (built in Tranche 1). This ledger grants nothing new.")


def gap_series(ppi_monthly: Series, ulc_q: Series) -> list[tuple]:
    ppi_q = to_quarterly_mean(ppi_monthly)
    rows = align(yoy(ppi_q, 4), yoy(ulc_q, 4))
    return [(d, p, u, p - u) for d, p, u in rows]


def margins(profits: Series, gva: Series) -> Series:
    return [(d, 100.0 * p / g) for d, p, g in align(profits, gva) if g]


def peaks(gap: list[tuple]) -> list[int]:
    out = []
    for i in range(2, len(gap) - 2):
        g = gap[i][3]
        if g > 0 and all(g > gap[j][3] for j in (i - 2, i - 1, i + 1, i + 2)):
            out.append(i)
    return out


def after_peaks(gap: list[tuple], margin: Series) -> tuple[list[dict], dict]:
    m = dict(margin)
    days = [d for d, *_ in gap]
    mdays = sorted(m)
    idx = {d: i for i, d in enumerate(mdays)}
    rows = []
    for i in peaks(gap):
        d = days[i]
        row = {"peak_quarter": d[:7], "gap_pp": round(gap[i][3], 2),
               "ppi_yoy_pct": round(gap[i][1], 2), "ulc_yoy_pct": round(gap[i][2], 2),
               "margin_pct": round(m[d], 2) if d in m else None}
        for h in HORIZONS:
            j = idx.get(d)
            row[f"margin_change_{h}q_pp"] = (round(m[mdays[j + h]] - m[d], 2)
                                            if j is not None and j + h < len(mdays) else None)
        rows.append(row)
    base = {}
    for h in HORIZONS:
        ch = [m[mdays[i + h]] - m[mdays[i]] for i in range(len(mdays) - h)
              if mdays[i] >= days[0]]
        base[h] = (mean(ch) if ch else None, len(ch))
    return rows, base


def summarise(rows: list[dict], base: dict, label: str) -> list[str]:
    out = [f"**{label}:** {len(rows)} gap peak(s)."]
    for h in HORIZONS:
        vals = [r[f"margin_change_{h}q_pp"] for r in rows
                if r[f"margin_change_{h}q_pp"] is not None]
        b, nb = base[h]
        out.append(f"- Margin change over the next {h} quarters after a peak: "
                   + (f"mean {mean(vals):+.2f} pp, falling after {sum(v < 0 for v in vals)} "
                      f"of {len(vals)}" if vals else "n/a (no peak with that much "
                                                     "history after it)")
                   + (f"; every quarter's mean {b:+.2f} pp (n={nb})" if b is not None else ""))
    return out


def study(series: dict) -> dict:
    margin = margins(series["profits"], series["gva"])
    gap = gap_series(series["ppi"], series["ulc"])
    rows, base = after_peaks(gap, margin)
    gap_l = gap_series(series["ppi_long"], series["ulc"])
    rows_l, base_l = after_peaks(gap_l, margin)
    last = gap[-1]
    source = "price" if last[3] > 0 else "cost"
    body = [f"**The latest quarter** ({last[0][:7]}): PPI {last[1]:+.1f}% on the year "
            f"against unit labor costs {last[2]:+.1f}%, a gap of {last[3]:+.1f} pp: the "
            f"margin's source is **{source}**. Of {len(gap)} quarters since "
            f"{gap[0][0][:7]}, the source was price in "
            f"{sum(1 for g in gap if g[3] > 0)}.", ""]
    body += summarise(rows, base, f"The order's PPI leg (WPSFD49116, from {gap[0][0][:7]})")
    body += [""] + summarise(rows_l, base_l, "Robustness, PPI finished goods less foods "
                                             f"and energy (WPSFD4131, from {gap_l[0][0][:7]})")
    for r in rows:
        r["series"] = "WPSFD49116"
    for r in rows_l:
        r["series"] = "WPSFD4131 (robustness)"
    return {"item": ITEM, "title": TITLE, "as_of": last[0][:7],
            "window": f"{gap[0][0][:7]} to {last[0][:7]} (the order's leg); "
                      f"{gap_l[0][0][:7]} to {gap_l[-1][0][:7]} (robustness)",
            "n": len(rows),
            "statistic": "the nonfinancial corporate profit share's change 4 and 8 "
                         "quarters after each gap peak, against every quarter's; the "
                         "margin-source attribution (price vs cost) by quarter",
            "pass_rule": "none stated (item 35 asks for a 'base-rate ledger of margin "
                         "behaviour after gap peaks')",
            "verdict": NO_GATE, "rights": RIGHTS, "body": body,
            "episodes": rows + rows_l,
            "result": {"peaks": len(rows), "peaks_long": len(rows_l),
                       "gap_now": last[3], "source_now": source},
            "caveats": [
                f"n is {len(rows)} on the order's series: the PPI leg begins in "
                f"{gap[0][0][:4]}. The long row is a different index.",
                "The profit share is a margin proxy at the national-accounts level, "
                "not the S&P's margin.",
            ]}


SERIES_PUBLIC = {"ppi": ("fred", "WPSFD49116"), "ppi_long": ("fred", "WPSFD4131"),
                 "ulc": ("fred", "ULCNFB"), "profits": ("fred", "NFCPATAX"),
                 "gva": ("fred", "A455RC1Q027SBEA")}
SERIES_STORE = {"ppi": "fred.ppi_fd_core_ex_trade", "ppi_long": None,
                "ulc": "fred.ulc_nfb", "profits": None, "gva": None}
