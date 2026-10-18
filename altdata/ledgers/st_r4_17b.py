"""
ST-R4.17b -- the net-liquidity calibration ledger against the S&P (Batch 5 item 17;
docs/change-order-signal-triage-batch-5-2026-10-09.md).

THE ORDER: "Net liquidity as a derived series (or extended if present) with 4- and
13-week change and a component-attribution line ... Modifier rights only after a
calibration ledger vs SPX (popular correlation with a mixed 2022-23 record)."
Rights: "Report-only until the ledger; modifier after." It states NO pass rule
for the ledger.

THE SERIES IS 17a's (st-r4-tranche-1): Fed assets less the TGA less the ON RRP,
in dollars -- WALCL and WTREGEN in millions, RRPONTSYD in billions (CLAUDE.md's
units trap) -- at each H.4.1 Wednesday, with its 4- and 13-week changes split
into legs that sum to the change: + Fed assets, - TGA, - RRP. The leading leg is
the largest in size. RRPONTSYD prints only on days the facility operated; a
Wednesday with no print in the week before it reads 0 (before the daily facility
of September 2013 the operations were small tests).

POINT IN TIME. The H.4.1 is published Thursday at 16:30 ET for the Wednesday, so
each week's change is set against the S&P from the first close AFTER that
Thursday (the Friday's) -- never the Wednesday's. FRED's current vintage is read:
the H.4.1 legs are rarely revised and ALFRED's vintages are not used here; RRP is
not revised. The S&P is Yahoo's ^GSPC price index, which is not revised.

THE STATISTICS: the correlation of the 13-week change with the S&P's NEXT 13
weeks (63 sessions), all weeks and non-overlapping (every 13th); the popular
read, the correlation with the SAME 13 weeks; both again over 2022-2023, the
order's mixed record; the next 13 weeks by quintile of the 13-week change; and
the top quintile's next 13 weeks by its leading leg (TGA transient, RRP little
left, balance sheet durable -- 17a's meanings).
"""

from __future__ import annotations

import bisect
import datetime as dt

from . import NO_GATE, Series, corr, mean, quantile

ITEM = "ST-R4.17b"
TITLE = "net liquidity's 13-week change against the S&P"
WEEKS = (4, 13)
FWD = {4: 20, 13: 63}                # sessions
SUBPERIOD = ("2022-01-01", "2023-12-31")
RIGHTS = ("Report-only until the ledger; modifier after (the order). The order "
          "states no pass rule, so this ledger grants no modifier: the series stays "
          "report-only in Plumbing until the operator rules a gate.")
LEG_MEANING = {"fed": "balance sheet (durable)", "tga": "TGA (transient)",
               "rrp": "RRP (little left)"}


def rrp_on(rrp: Series, day: str) -> float:
    """RRP (billions) on `day`, else its last print in the 7 days before, else 0."""
    days = [d for d, _ in rrp]
    i = bisect.bisect_right(days, day) - 1
    if i >= 0:
        lo = (dt.date.fromisoformat(day) - dt.timedelta(days=7)).isoformat()
        if days[i] >= lo:
            return rrp[i][1]
    return 0.0


def weekly(walcl: Series, tga: Series, rrp: Series) -> list[dict]:
    t = dict(tga)
    out = []
    for d, w in walcl:
        if d not in t:
            continue
        r = rrp_on(rrp, d)
        out.append({"date": d, "fed": w * 1e6, "tga": t[d] * 1e6, "rrp": r * 1e9,
                    "nl": w * 1e6 - t[d] * 1e6 - r * 1e9})
    return out


def change(wk: list[dict], i: int, k: int) -> dict:
    """The k-week change at i and its legs, in dollars; the legs sum to it."""
    a, b = wk[i - k], wk[i]
    legs = {"fed": b["fed"] - a["fed"], "tga": -(b["tga"] - a["tga"]),
            "rrp": -(b["rrp"] - a["rrp"])}
    lead = max(legs, key=lambda x: abs(legs[x]))
    return {"total": b["nl"] - a["nl"], **legs, "lead": lead}


def first_close_after(closes: list[tuple[str, float]], day: str) -> int:
    """Index of the first close strictly after the H.4.1's Thursday release."""
    thu = (dt.date.fromisoformat(day) + dt.timedelta(days=1)).isoformat()
    return bisect.bisect_right([d for d, _ in closes], thu)


def last_close_on(closes: list[tuple[str, float]], day: str) -> int:
    return bisect.bisect_right([d for d, _ in closes], day) - 1


def table(series: dict) -> list[dict]:
    wk = weekly(series["walcl"], series["tga"], series["rrp"])
    spx = series["spx"]
    rows = []
    for i in range(13, len(wk)):
        d = wk[i]["date"]
        c4, c13 = change(wk, i, 4), change(wk, i, 13)
        j = first_close_after(spx, d)
        row = {"date": d, "net_liquidity_bn": round(wk[i]["nl"] / 1e9, 1),
               "chg4_bn": round(c4["total"] / 1e9, 1), "chg13_bn": round(c13["total"] / 1e9, 1),
               "chg13_fed_bn": round(c13["fed"] / 1e9, 1),
               "chg13_tga_bn": round(c13["tga"] / 1e9, 1),
               "chg13_rrp_bn": round(c13["rrp"] / 1e9, 1), "lead13": c13["lead"],
               "spx_from": spx[j][0] if j < len(spx) else None}
        for k, n in FWD.items():
            row[f"spx_next{k}w_pct"] = (round(100.0 * (spx[j + n][1] / spx[j][1] - 1), 3)
                                        if j + n < len(spx) else None)
        e, s = last_close_on(spx, d), last_close_on(spx, wk[i - 13]["date"])
        row["spx_same13w_pct"] = (round(100.0 * (spx[e][1] / spx[s][1] - 1), 3)
                                  if e >= 0 and s >= 0 else None)
        rows.append(row)
    return rows


def _pairs(rows, x, y, lo=None, hi=None, step=1):
    sel = [r for r in rows if r[x] is not None and r[y] is not None
           and (lo is None or r["date"] >= lo) and (hi is None or r["date"] <= hi)]
    sel = sel[::step]
    return [r[x] for r in sel], [r[y] for r in sel]


def stats(rows: list[dict]) -> dict:
    out = {}
    for name, y, step, lo, hi in (
            ("next_all", "spx_next13w_pct", 1, None, None),
            ("next_nonoverlap", "spx_next13w_pct", 13, None, None),
            ("same_all", "spx_same13w_pct", 1, None, None),
            ("next_2022_23", "spx_next13w_pct", 1, *SUBPERIOD),
            ("same_2022_23", "spx_same13w_pct", 1, *SUBPERIOD)):
        x, yy = _pairs(rows, "chg13_bn", y, lo, hi, step)
        out[name] = (corr(x, yy), len(x))
    done = [r for r in rows if r["spx_next13w_pct"] is not None]
    cuts = [quantile([r["chg13_bn"] for r in done], q) for q in (0.2, 0.4, 0.6, 0.8)]
    quint = {q: [] for q in range(5)}
    for r in done:
        quint[bisect.bisect_right(cuts, r["chg13_bn"])].append(r["spx_next13w_pct"])
    out["quintiles"] = {q: (mean(v) if v else None, len(v)) for q, v in quint.items()}
    out["cuts"] = cuts
    top = [r for r in done if r["chg13_bn"] > cuts[3]]
    out["top_by_lead"] = {lg: (mean(v) if v else None, len(v)) for lg in LEG_MEANING
                          for v in [[r["spx_next13w_pct"] for r in top if r["lead13"] == lg]]}
    out["all_next13"] = (mean([r["spx_next13w_pct"] for r in done]), len(done))
    return out


def _r(t) -> str:
    return "n/a" if t[0] is None else f"r {t[0]:+.2f} (n {t[1]})"


def study(series: dict) -> dict:
    rows = table(series)
    s = stats(rows)
    done = [r for r in rows if r["spx_next13w_pct"] is not None]
    now = rows[-1]
    q = s["quintiles"]
    body = [
        f"**Now ({now['date']}):** net liquidity ${now['net_liquidity_bn']:,.0f}bn; "
        f"13 weeks {now['chg13_bn']:+,.0f}bn (Fed {now['chg13_fed_bn']:+,.0f}, TGA "
        f"{now['chg13_tga_bn']:+,.0f}, RRP {now['chg13_rrp_bn']:+,.0f}; led by "
        f"{LEG_MEANING[now['lead13']]}), 4 weeks {now['chg4_bn']:+,.0f}bn.",
        "",
        "| Correlation of the 13-week change with | All weeks | 2022-2023 |",
        "|---|---|---|",
        f"| the S&P's NEXT 13 weeks (from the Friday after the release) | "
        f"{_r(s['next_all'])}; non-overlapping {_r(s['next_nonoverlap'])} | "
        f"{_r(s['next_2022_23'])} |",
        f"| the S&P over the SAME 13 weeks (the popular read) | {_r(s['same_all'])} | "
        f"{_r(s['same_2022_23'])} |",
        "",
        "The S&P's next 13 weeks by quintile of the 13-week change (every week "
        f"{s['all_next13'][0]:+.2f}%, n {s['all_next13'][1]}):",
        "",
        "| Quintile of the change | Bounds ($bn) | Next 13 weeks (mean) | n |",
        "|---|---|---|---|"]
    bounds = [None, *s["cuts"], None]
    for k in range(5):
        lo = "" if bounds[k] is None else f"{bounds[k]:+,.0f}"
        hi = "" if bounds[k + 1] is None else f"{bounds[k + 1]:+,.0f}"
        m, n = q[k]
        body.append(f"| {k + 1} | {lo or 'below'} to {hi or 'above'} | "
                    f"{'n/a' if m is None else f'{m:+.2f}%'} | {n} |")
    body += ["", "The top quintile's next 13 weeks by its leading leg:", ""]
    for lg, (m, n) in s["top_by_lead"].items():
        body.append(f"- {LEG_MEANING[lg]}: " + ("n/a" if m is None else f"{m:+.2f}%")
                    + f" (n {n})")
    return {"item": ITEM, "title": TITLE, "as_of": now["date"],
            "window": f"{rows[0]['date']} to {done[-1]['date']} (weeks with a full next "
                      f"13 weeks); the series to {now['date']}",
            "n": len(done),
            "statistic": "correlation of net liquidity's 13-week change with the S&P's "
                         "next and same 13 weeks, all weeks and 2022-2023; the next 13 "
                         "weeks by quintile and by leading leg",
            "pass_rule": "none stated (item 17: 'modifier rights only after a "
                         "calibration ledger vs SPX')",
            "verdict": NO_GATE, "rights": RIGHTS, "body": body, "episodes": rows,
            "result": {k: v for k, v in s.items()},
            "caveats": [
                f"Weekly observations overlap by 12 of 13 weeks: n {len(done)} weeks is "
                f"about {len(done) // 13} independent quarters, the non-overlapping row's n.",
                "FRED's current vintage of the H.4.1 legs, not ALFRED's: revisions to "
                "WALCL and WTREGEN are rare and small.",
                "RRPONTSYD prints only when the facility operated; a week with no print "
                "in the seven days before reads 0.",
            ]}


SERIES_PUBLIC = {"walcl": ("fred", "WALCL"), "tga": ("fred", "WTREGEN"),
                 "rrp": ("fred", "RRPONTSYD"), "spx": ("yahoo", "^GSPC")}
SERIES_STORE = {"walcl": "fred.fed_balance", "tga": "fred.tga", "rrp": "fred.rrp",
                "spx": "yfinance.mkt_gspc"}
