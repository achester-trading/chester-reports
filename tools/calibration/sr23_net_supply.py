"""
SR-23 -- the net-supply regression, with subsamples and a funds-rate control
(signal-triage ST-7; st-t2-rates, 18 Oct 2026).

    python tools/calibration/sr23_net_supply.py [--box] [--out DIR] [--date D]

THE REGISTER'S GATE (docs/signal-triage-register.md, SR-23). "2003-2026 monthly;
regress the 12m change in ACM term premium (and fred.tips_10y) on the 12m change
in net supply/GDP with a funds-rate-path control. Pass: positive, significant
coefficient in both pre- and post-2008 subsamples. If only post-2008 ->
descriptive, no modifier. Falsifier: 2010-13 consistent; 2018-19 inconsistent
without the Fed control."

NET SUPPLY is ST-4's: MSPD's month-on-month change in total marketable debt held
by the public (G-14; through altdata/sources/fiscaldata.py's reader) less the
month-end change in the Fed's Treasuries (TREAST, millions), summed over twelve
months and divided by the latest nominal GDP published by then (SAAR,
billions). "The 12m change in net supply/GDP" is read as that ratio: twelve
months of net supply is the twelve-month change in the privately held stock, so
the regression is of a change on a change, as the preferred-habitat argument
states it. The ratio's own twelve-month change is printed as a robustness row.

WHAT THE FIRST EDITION PRE-REGISTERS, where the register is silent:
  * THE CONTROL: the twelve-month change in the effective funds rate (FEDFUNDS,
    monthly average).
  * THE TARGETS: month-end ACM 10-year term premium (the verdict) and DFII10
    (printed beside it), twelve-month changes in bp.
  * SUBSAMPLES: pre-2008 is every month through 2007-12, post-2008 every month
    from 2009-01 (2008 itself is the break and in neither).
  * SIGNIFICANT: the supply coefficient's Newey-West t at 12 lags is at least
    1.96 (twelve-month changes overlap, so plain errors overstate every t).
  * GDP is used from the second month after its quarter ends (the advance
    estimate's timing); its current vintage is read (GDP is revised).
  * The falsifier windows: 2010-01 to 2013-12 and 2018-01 to 2019-12, with and
    without the control.

Point in time: MSPD, TREAST, FEDFUNDS and DFII10 are not revised; GDP is (the
current vintage, with the publication lag above); ACM's model is re-estimated
each month, so its history is today's estimate, not what was printed then.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import st7_common as C                                           # noqa: E402

ITEM = "SR-23"
NW_LAGS = 12
T_CRIT = 1.96
PRE_END, POST_START = "2007-12", "2009-01"
GDP_LAG = 2
MIN_N = 24
WINDOWS = (("2010-13", "2010-01", "2013-12"), ("2018-19", "2018-01", "2019-12"))


def load_public() -> dict:
    from altdata.ledgers import sources as S
    from altdata.sources import acm, fiscaldata as fd
    recs = fd.fetch_records(fd.BACKFILL_START)
    rows = fd.rows_from_records(recs, "1970-01-01T00:00:00+00:00")
    issu = {r["observed_at"][:7]: float(r["value"]) for r in rows
            if r["registry_key"] == fd.NET_KEY}
    tp = [(r["observed_at"][:10], float(r["value"])) for r in acm._produce()
          if r["registry_key"] == "acm.term_premium_10y"]
    return {"issuance": issu, "soma": C.monthly_last(S.fred("TREAST")),
            "gdp": C.monthly_last(S.fred("GDP")),
            "ff": C.monthly_mean(S.fred("FEDFUNDS")),
            "acm": C.monthly_last(sorted(tp)),
            "tips": C.monthly_last(S.fred("DFII10"))}


def gdp_known(gdp: dict, m: str):
    """Nominal GDP (SAAR, $bn) of the latest quarter published by month m: a
    quarter dated its first month ends two months later and is used from
    GDP_LAG months after that."""
    ok = [q for q in gdp if C.madd(q, 2 + GDP_LAG) <= m]
    return gdp[max(ok)] if ok else None


def supply_ratio(d: dict) -> dict[str, float]:
    """{month: twelve months of net supply / GDP, percent}."""
    soma = d["soma"]
    net = {}
    for m, v in d["issuance"].items():
        p = C.madd(m, -1)
        if m in soma and p in soma:
            net[m] = v - (soma[m] - soma[p]) * 1e6
    out = {}
    for m in sorted(net):
        ms = [C.madd(m, -k) for k in range(12)]
        g = gdp_known(d["gdp"], m)
        if all(x in net for x in ms) and g:
            out[m] = 100.0 * sum(net[x] for x in ms) / (g * 1e9)
    return out


def ch12(s: dict, scale: float = 1.0) -> dict[str, float]:
    return {m: scale * (v - s[C.madd(m, -12)]) for m, v in s.items()
            if C.madd(m, -12) in s}


def fit(y: dict, x: dict, z: dict, a: str, b: str, control: bool) -> dict:
    ms = [m for m in sorted(y) if a <= m <= b and m in x and (m in z or not control)]
    if len(ms) < MIN_N:
        return {"n": len(ms), "b": None, "t": None, "from": ms[0] if ms else None,
                "to": ms[-1] if ms else None}
    xs = [[x[m] for m in ms]] + ([[z[m] for m in ms]] if control else [])
    r = C.ols_nw([y[m] for m in ms], xs, NW_LAGS)
    return {"n": r["n"], "b": r["b"][1], "t": r["t"][1], "r2": r["r2"],
            "from": ms[0], "to": ms[-1],
            "b_ff": r["b"][2] if control else None, "t_ff": r["t"][2] if control else None}


def judge(pre: dict, post: dict) -> str:
    """The register's rule over the two subsample fits; the verdict carries its
    inputs."""
    def sig(r):
        return r["b"] is not None and r["b"] > 0 and r["t"] >= T_CRIT

    if pre["b"] is None or post["b"] is None:
        return (f"{C.INSUFFICIENT} -- pre-2008 n {pre['n']}, post-2008 n "
                f"{post['n']}, below {MIN_N} months; no coefficient prints")
    fig = (f" (pre-2008 b {C.f2(pre['b'], 1)}, t {C.f2(pre['t'])}; post-2008 b "
           f"{C.f2(post['b'], 1)}, t {C.f2(post['t'])}; rule b > 0, t >= {T_CRIT})")
    if sig(pre) and sig(post):
        return f"{C.PASS} -- positive and significant in both subsamples" + fig
    if sig(post):
        return f"{C.FAIL} -- post-2008 only: descriptive, no modifier" + fig
    return f"{C.FAIL} -- not significant post-2008: descriptive, no modifier" + fig


def study(d: dict, mode: str) -> dict:
    sr = supply_ratio(d)
    dsr = ch12(sr)
    tp, tips = ch12(d["acm"], 100.0), ch12(d["tips"], 100.0)
    ff = ch12(d["ff"], 100.0)
    last = max(set(sr) & set(tp)) if set(sr) & set(tp) else None
    first = min(set(sr) & set(tp)) if set(sr) & set(tp) else None
    samples = (("pre-2008", "2000-01", PRE_END), ("post-2008", POST_START, last or "9999-12"),
               ("full", "2000-01", last or "9999-12"))
    res = {}
    for tname, y in (("ACM 10y term premium", tp), ("DFII10", tips)):
        for xname, x in (("12m supply / GDP", sr), ("its 12m change", dsr)):
            for sname, a, b in samples:
                res[(tname, xname, sname)] = fit(y, x, ff, a, b, True)
    win = {}
    for wname, a, b in WINDOWS:
        for ctl in (False, True):
            win[(wname, ctl)] = fit(tp, sr, ff, a, b, ctl)

    pre = res[("ACM 10y term premium", "12m supply / GDP", "pre-2008")]
    post = res[("ACM 10y term premium", "12m supply / GDP", "post-2008")]
    verdict = judge(pre, post)

    body = [f"Net supply / GDP (twelve months), latest {last}: {C.f2(sr.get(last), 2, '%')}.",
            "",
            "Coefficients on supply (bp of the target per pp of GDP), Newey-West t "
            f"at {NW_LAGS} lags, all with the funds-rate control:",
            "",
            "| Target | Supply measure | Sample | Months | b | t | b (funds rate) | t | R2 |",
            "|---|---|---|---|---|---|---|---|---|"]
    for (tn, xn, sn), r in res.items():
        body.append(f"| {tn} | {xn} | {sn} ({r['from']} to {r['to']}) | {r['n']} | "
                    f"{C.f2(r['b'], 1)} | {C.f2(r['t'])} | {C.f2(r.get('b_ff'), 2)} | "
                    f"{C.f2(r.get('t_ff'))} | "
                    f"{'n/a' if r.get('r2') is None else format(r['r2'], '.2f')} |")
    body += ["", "The falsifier windows (ACM, twelve-month supply / GDP):", "",
             "| Window | Control | Months | b | t |", "|---|---|---|---|---|"]
    for (wn, ctl), r in win.items():
        body.append(f"| {wn} | {'funds rate' if ctl else 'none'} | {r['n']} | "
                    f"{C.f2(r['b'], 1)} | {C.f2(r['t'])} |")
    episodes = [{"month": m, "supply_12m_gdp_pct": round(sr[m], 4),
                 "supply_ch12_pp": None if m not in dsr else round(dsr[m], 4),
                 "acm_tp_ch12_bp": None if m not in tp else round(tp[m], 2),
                 "dfii10_ch12_bp": None if m not in tips else round(tips[m], 2),
                 "fedfunds_ch12_bp": None if m not in ff else round(ff[m], 2)}
                for m in sorted(sr)]
    return {
        "item": ITEM, "title": "net Treasury supply against the term premium",
        "as_of": f"{last} (latest month with supply and ACM)",
        "window": f"{first} to {last}; pre-2008 to {PRE_END}, post-2008 from {POST_START}",
        "n": (pre["n"] or 0) + (post["n"] or 0),
        "statistic": "the supply coefficient and its Newey-West t, by subsample, "
                     "with the funds-rate control",
        "pass_rule": ("the register's: positive, significant coefficient in both pre- "
                      "and post-2008 subsamples; post-2008 only -> descriptive. "
                      f"Pre-registered by this first edition: |t| >= {T_CRIT} at "
                      f"{NW_LAGS} Newey-West lags; control = 12m change in FEDFUNDS; "
                      "2008 in neither subsample"),
        "verdict": verdict,
        "rights": ("PASS: a confidence modifier on the rates-cell assignment (no cell "
                   "is live: the driver stays withdrawn, so it waits for one), the "
                   "Factor IV panel input, and Book A's duration-timing modifier via "
                   "the projection (not tracked: CBO). FAIL: descriptive, no "
                   "modifier. " + C.RIGHTS_NOTE),
        "sources": ["Fiscal Data MSPD through altdata/sources/fiscaldata.py (no key), "
                    f"from {d.get('mspd_start', '2001-01')}",
                    "NY Fed ACM workbook through altdata/sources/acm.py (re-estimated "
                    "monthly)",
                    "FRED graph CSV (no key): TREAST, GDP (revised), FEDFUNDS, DFII10"],
        "source_mode": mode, "body": body, "episodes": episodes,
        "caveats": ["The box re-run reads the same public sources (the calibration "
                    "rule), not the store.",
                    "The pre-2008 subsample is short: supply starts when TREAST does "
                    "(Dec 2002), so its twelve-month sums start in late 2003."]}


if __name__ == "__main__":
    raise SystemExit(C.cli(ITEM, load_public, study))
