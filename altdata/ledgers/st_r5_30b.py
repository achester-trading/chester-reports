"""
ST-R5.30b -- the 10-year forward-return regression of investor equity allocation
(Batch 6 item 30, the amendment to SR-12; docs/change-order-signal-triage-batch-6-
2026-10-15.md).

THE ORDER: "equities (Z.1 household share, quarterly, with the 10-year
forward-return regression as its base rate) ... Equity-allocation extreme enters
the T&B overlay intake queue (top-side) after a calibration ledger ... Book A
modifier via the rule table." Work: "ST-R5.30b forward-return regression and
ledger." It names the study and states NO pass rule.

THE CONSTRUCT (verify item 7, answered on st-r5-index, 16 Oct): the published
predictor is the aggregate investor allocation (Livermore, 2013) -- the market
value of all corporate equities over that value plus the debt liabilities of the
real-economy borrowers -- every leg on FRED, millions of dollars, quarterly:
  equities  NCBEILQ027S + FBCELLQ027S
  debt      TCMILBSHNO + TCMILBSNNCB + TCMILBSNNB + FGTCMDODNS + SLGTCMDODNS
            + DODFFSWCMI
The household share (BOGZ1FL153064486Q, the live panel's series as ruled) is the
robustness row. A Z.1 level is the quarter's END: FRED dates it on the quarter's
first day, so the return starts at the quarter's last month.

THE RETURN: the S&P composite's nominal total return over the next 120 months,
annualised, from Shiller's monthly price and dividend (dividends reinvested
monthly at D/12). Quarterly observations overlap by 39 of 40 quarters: n counts
quarters, and the effective number of independent decades is about n/40.
"""

from __future__ import annotations

from . import NO_GATE, ordinal, Series, mean, ols, percentile_rank, quantile

ITEM = "ST-R5.30b"
TITLE = "investor equity allocation and the S&P's 10-year forward return"
EQUITY = ("NCBEILQ027S", "FBCELLQ027S")
DEBT = ("TCMILBSHNO", "TCMILBSNNCB", "TCMILBSNNB", "FGTCMDODNS", "SLGTCMDODNS",
        "DODFFSWCMI")
HOUSEHOLD = "BOGZ1FL153064486Q"
HORIZON_MONTHS = 120
RIGHTS = ("Book A modifier (the rule-table line drafted 16 Oct, 'inactive until "
          "ST-R5.30b's ledger is filed') and the T&B intake queue (ST-R5.30c, after "
          "this ledger and 'T&B full', part 2). With no gate in the order, neither is "
          "granted here: activating either is the operator's ruling.")


def quarter_end_month(d: str) -> str:
    y, m = int(d[:4]), int(d[5:7])
    return f"{y}-{m + 2:02d}-01"


def allocation(legs: dict[str, Series]) -> Series:
    """E / (E + D), percent, on the quarters every leg carries."""
    maps = {k: dict(v) for k, v in legs.items()}
    days = sorted(set.intersection(*(set(m) for m in maps.values())))
    out = []
    for d in days:
        e = sum(maps[k][d] for k in EQUITY)
        debt = sum(maps[k][d] for k in DEBT)
        out.append((d, 100.0 * e / (e + debt)))
    return out


def total_return_index(price: Series, dividend: Series) -> dict[str, float]:
    """Monthly total-return index from Shiller's price and annualised dividend."""
    dv = dict(dividend)
    tr, out, prev = 1.0, {}, None
    for d, p in price:
        if prev is not None and prev[1]:
            tr *= (p + dv.get(d, dv.get(prev[0], 0.0)) / 12.0) / prev[1]
        out[d[:7]] = tr
        prev = (d, p)
    return out


def forward_returns(tri: dict[str, float], months: int = HORIZON_MONTHS) -> dict[str, float]:
    """Annualised percent return over the next `months`, by start month."""
    keys = sorted(tri)
    idx = {k: i for i, k in enumerate(keys)}
    out = {}
    for k in keys:
        j = idx[k] + months
        if j < len(keys):
            out[k] = 100.0 * ((tri[keys[j]] / tri[k]) ** (12.0 / months) - 1.0)
    return out


def regress(alloc: Series, fwd: dict[str, float]) -> dict:
    pts = [(d, a, fwd[quarter_end_month(d)[:7]]) for d, a in alloc
           if quarter_end_month(d)[:7] in fwd]
    if len(pts) < 8:
        raise ValueError(f"only {len(pts)} quarters with a full forward decade")
    fit = ols([a for _, a, _ in pts], [r for _, _, r in pts])
    fit["points"] = pts
    return fit


def study(series: dict) -> dict:
    alloc = allocation({k: series[k] for k in EQUITY + DEBT})
    hh = series[HOUSEHOLD]
    tri = total_return_index(series["shiller.sp_price"], series["shiller.sp_dividend"])
    fwd = forward_returns(tri)
    fit = regress(alloc, fwd)
    rob = regress(hh, fwd)
    now_d, now_a = alloc[-1]
    hist = [a for _, a in alloc]
    fitted_now = fit["a"] + fit["b"] * now_a
    res = fit["residuals"]
    lo, mid, hi = quantile(res, 0.10), quantile(res, 0.50), quantile(res, 0.90)
    last_res = res[-1]
    pts = fit["points"]
    episodes = [{"quarter": d[:7], "allocation_pct": round(a, 3),
                 "fwd10y_return_pct": round(r, 3),
                 "fitted_pct": round(fit["a"] + fit["b"] * a, 3),
                 "residual_pp": round(r - (fit["a"] + fit["b"] * a), 3)}
                for d, a, r in pts]
    body = [
        f"Regression of the S&P's annualised 10-year forward total return on the "
        f"aggregate allocation, quarterly: **forward return = {fit['a']:.2f} "
        f"{fit['b']:+.3f} x allocation (pp)**, R2 {fit['r2']:.2f}, n {fit['n']} "
        f"quarters ({pts[0][0][:7]} to {pts[-1][0][:7]}; about {fit['n'] / 40:.1f} "
        f"independent decades).",
        f"Robustness, the household share ({HOUSEHOLD}): forward return = "
        f"{rob['a']:.2f} {rob['b']:+.3f} x share, R2 {rob['r2']:.2f}, n {rob['n']}.",
        f"**The current reading** ({now_d[:7]}, Z.1's latest quarter): allocation "
        f"{now_a:.1f}%, the {ordinal(percentile_rank(hist, now_a))} percentile of "
        f"{len(hist)} quarters since {alloc[0][0][:7]}. On the fitted line it implies "
        f"{fitted_now:+.1f}% a year over the next decade; the residuals' 10th-90th "
        f"percentile band puts it between {fitted_now + lo:+.1f}% and "
        f"{fitted_now + hi:+.1f}% (median residual {mid:+.1f} pp).",
        f"The latest observed residual ({pts[-1][0][:7]}, the last quarter with a "
        f"full forward decade) is {last_res:+.1f} pp, the "
        f"{ordinal(percentile_rank(res, last_res))} percentile of the residuals.",
    ]
    return {"item": ITEM, "title": TITLE, "as_of": now_d[:7],
            "window": f"{pts[0][0][:7]} to {pts[-1][0][:7]} (forward decades); "
                      f"allocation history {alloc[0][0][:7]} to {now_d[:7]}",
            "n": fit["n"],
            "statistic": "OLS of the 10-year forward annualised total return on the "
                         "aggregate equity allocation; R2; the current reading's "
                         "fitted value and residual band",
            "pass_rule": "none stated (item 30 names the regression as the base rate; "
                         "the queue entry follows 'after a calibration ledger')",
            "verdict": NO_GATE, "rights": RIGHTS, "body": body,
            "episodes": episodes,
            "result": {"a": fit["a"], "b": fit["b"], "r2": fit["r2"], "n": fit["n"],
                       "now": now_a, "fitted_now": fitted_now, "band": (lo, hi),
                       "household": {"a": rob["a"], "b": rob["b"], "r2": rob["r2"]}},
            "caveats": [
                "Overlapping decades: the R2 and the band are descriptive, not a test.",
                "DODFFSWCMI's FRED page says 'Seasonally Adjusted Annual Rate' though "
                "its title says Level (flagged on st-r5-index); it enters as a level.",
                "The construct follows the paper's published description; its own "
                "values were not re-fetched to compare.",
            ]}


SERIES_PUBLIC = {**{k: ("fred", k) for k in EQUITY + DEBT + (HOUSEHOLD,)},
                 "shiller.sp_price": ("shiller", "shiller.sp_price"),
                 "shiller.sp_dividend": ("shiller", "shiller.sp_dividend")}
SERIES_STORE = {HOUSEHOLD: "fred.z1_household_equity_share",
                "shiller.sp_price": "shiller.sp_price",
                "shiller.sp_dividend": "shiller.sp_dividend",
                **{k: None for k in EQUITY + DEBT}}
