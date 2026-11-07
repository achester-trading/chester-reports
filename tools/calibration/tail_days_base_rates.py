"""
The two-sided tail base-rate table (signal-triage Batch 23 item 124a, the
order's 106a; paste B133, 6 Nov 2026). A STUDY TOOL, not a gate: it recomputes
the table the Base Rates paper's dated appendix carries, so every figure there
is reproducible, and the Annual Structural Review re-runs it once a year.

    python tools/calibration/tail_days_base_rates.py [--source store|public]
        [--db PATH] [--through YYYY-MM-DD] [--out FILE]

--source store (the box): the store's yfinance.mkt_gspc and fred.vix, each the
newest vintage of each period, read through altdata.ledgers.sources.
--source public (the laptop's first edition): ^GSPC through the yfinance
writer's own reader and VIXCLS from FRED's public graph CSV, the same two
series the study (docs/studies/tail-days-2016-2026-data.md, branch
study/tail-days) read.

THE COMPUTATION is the text of COMPUTATION below, printed at the head of the
output with its SHA-256. A re-run applies it; changing it is a new computation
with a new hash, never an edit of an old table.

Nothing here writes the store, the register or a report. The output goes to
stdout, or to --out.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

SPX_KEY = "yfinance.mkt_gspc"
VIX_KEY = "fred.vix"
FIRST_DAY = "1950-01-03"
FIRST_GARCH_YEAR = 1955
VIX_FROM = "1990-01-02"
SHUFFLES = 1000
SEED = 20261105
BUCKETS = (("below 20", None, 20.0), ("20-30", 20.0, 30.0),
           ("30-45", 30.0, 45.0), ("above 45", 45.0, None))

COMPUTATION = """\
THE SERIES. The S&P 500's daily closes (price only), from 3 January 1950 to the
as-of session; r_T = close_T / close_(T-1) - 1. VIX is FRED's VIXCLS at the
prior session's close (carried at most three sessions over a gap), from
2 January 1990.

THE STANDARDISATIONS. GARCH(1,1), constant mean, normal errors (the arch
package), fitted on daily returns in percent from 3 January 1950 through each
year-end and applied, with those parameters fixed, to the following year:
sigma_T is the one-step-ahead forecast made at T-1's close, so no fit sees the
day it standardises. First applied year 1955. Beside it, RV20: sigma_T is the
sample standard deviation of the 20 returns ending T-1. z_T = r_T / sigma_T,
not demeaned. The matched sample is the sessions where both sigmas exist.

THE DECILES. Each series' own full-sample 10th and 90th percentiles: raw
returns for the raw rows, z for the standardised rows. Bottom decile at or
below the 10th, top decile at or above the 90th.

FOLLOW-THROUGH. P(a top-decile day in T+1..T+h | a bottom-decile day at T),
h = 1, 5, 10, over conditioning days with h sessions after them, against the
unconditional rate: the same event over every day with h sessions after it.

VIX BUCKETS. Bottom-decile days from 1990 split by VIX at T-1: below 20,
20 to 30, 30 to 45, 45 and above (each lower bound inclusive). Per bucket:
n and P(top-decile day within 5) on the raw deciles of the 1950 sample and on
the GARCH-z deciles of the matched sample, and the raw 20-session forward
return's 10th percentile after the raw bottom-decile days.

CLUSTERING. The share of top-decile days with a bottom-decile day within five
sessions either side (the day itself excluded), against the same statistic on
the series permuted 1,000 times (seed 20261105): the shuffled mean and its
2.5 to 97.5 percent range.

FORWARD RETURNS. After a bottom-decile day and over all days (the baseline),
h = 1, 5, 20: raw, close T to close T+h in percent; standardised, the h-session
log return over sigma_(T+1) * sqrt(h), sigma_(T+1) the forecast known at T's
close under the same definition, in sigma units. Each with n, mean, median,
10th and 90th percentiles and the share above zero. The 10th and 90th
percentiles are the dispersion columns item 124g reads.

THE OPENERS. From 2 January 1990: a session in the bottom 1 percent of that
sample's returns, with VIX below 20 at T-1 and no session of |r| >= 2 percent
among the 20 before T. Each with its date, return, VIX at T-1, the next
session's return and the five-session return (close T to close T+5), "pending"
where those sessions have not happened.
"""


def computation_sha256(text: str = COMPUTATION) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------- data
def _series(pairs) -> pd.Series:
    s = pd.Series({pd.Timestamp(d): float(v) for d, v in pairs if v is not None},
                  dtype=float).sort_index()
    return s[~s.index.duplicated(keep="last")]


def load(source: str, db: Optional[str]) -> tuple[pd.Series, pd.Series, str]:
    if source == "store":
        from altdata.ledgers import sources as S                # noqa: PLC0415
        spx, vix = _series(S.store(SPX_KEY, db=db)), _series(S.store(VIX_KEY, db=db))
        via = f"the store's {SPX_KEY} and {VIX_KEY}"
    else:
        from altdata.ledgers import sources as S                # noqa: PLC0415
        from altdata.sources import yfinance_source as yfs      # noqa: PLC0415
        parsed = yfs._fetch_symbol("^GSPC", period="max")       # noqa: SLF001
        spx = _series(parsed["closes"])
        vix = _series(S.fred("VIXCLS"))
        via = ("^GSPC through the yfinance writer's reader (Yahoo Finance, price "
               "return); VIXCLS from FRED's public graph CSV")
    spx = spx[spx > 0]
    return spx, vix, via


# ------------------------------------------------------------------- helpers
def _near(flag: np.ndarray, before: int, after: int) -> np.ndarray:
    n = len(flag)
    f = flag.astype(np.int64)
    c = np.concatenate([[0], np.cumsum(f)])
    i = np.arange(n)
    lo = np.clip(i - before, 0, n)
    hi = np.clip(i + after + 1, 0, n)
    return (c[hi] - c[lo] - f) > 0


def follow(src: np.ndarray, tgt: np.ndarray, h: int, mask=None) -> tuple[float, int, float]:
    n = len(src)
    ok = np.arange(n) < n - h
    if mask is not None:
        ok = ok & mask
    fw = _near(tgt, 0, h)
    sel = src & ok
    k = int(sel.sum())
    return (fw[sel].mean() * 100 if k else np.nan), k, fw[ok].mean() * 100


def tail_stats(x: pd.Series) -> dict:
    v = x.values
    q10, q90 = np.quantile(v, 0.10), np.quantile(v, 0.90)
    bot, top = v <= q10, v >= q90
    out = {"q10": q10, "q90": q90, "bot": bot, "top": top, "n_top": int(top.sum())}
    for h in (1, 5, 10):
        out[h] = follow(bot, top, h)
    clus = lambda b, t: _near(b, 5, 5)[t].mean() * 100           # noqa: E731
    out["clus"] = clus(bot, top)
    rng = np.random.default_rng(SEED)
    sh = np.empty(SHUFFLES)
    for k in range(SHUFFLES):
        p = rng.permutation(v)
        sh[k] = clus(p <= q10, p >= q90)
    out["shuf"] = (sh.mean(), np.quantile(sh, 0.025), np.quantile(sh, 0.975))
    return out


def garch_sigma(r: pd.Series, first_year: int) -> tuple[pd.Series, tuple]:
    from arch import arch_model                                 # noqa: PLC0415
    y = r * 100
    sig = pd.Series(np.nan, index=r.index)
    last = None
    for yr in range(first_year, r.index[-1].year + 1):
        train = y.loc[: f"{yr - 1}-12-31"]
        res = arch_model(train, mean="Constant", vol="GARCH", p=1, q=1,
                         dist="normal", rescale=False).fit(disp="off")
        fixed = arch_model(y.loc[: f"{yr}-12-31"], mean="Constant", vol="GARCH",
                           p=1, q=1, dist="normal", rescale=False).fix(res.params)
        cv = fixed.conditional_volatility.loc[f"{yr}-01-01":] / 100
        sig.loc[cv.index] = cv.values
        last = (yr, res.params)
    return sig, last


def dist(x: pd.Series) -> dict:
    x = x.dropna()
    if x.empty:
        return {"n": 0}
    return {"n": len(x), "mean": x.mean(), "median": x.median(),
            "p10": x.quantile(0.1), "p90": x.quantile(0.9), "up": (x > 0).mean() * 100}


# ---------------------------------------------------------------- compute
def compute(spx: pd.Series, vix: pd.Series, through: Optional[str]) -> dict:
    if through:
        spx = spx.loc[:through]
        vix = vix.loc[:through]
    allr = spx / spx.shift(1) - 1
    r = allr.loc[FIRST_DAY:].dropna()
    c = spx.loc[r.index]
    sig_g, (fit_yr, fit) = garch_sigma(r, FIRST_GARCH_YEAR)
    sig_rv = r.rolling(20, min_periods=20).std(ddof=1).shift(1)
    idx = r.index[sig_g.notna() & sig_rv.notna()]
    series = {"garch": (r / sig_g).loc[idx], "rv20": (r / sig_rv).loc[idx],
              "raw": r.loc[idx] * 100, "raw1950": r * 100}
    st = {k: tail_stats(v) for k, v in series.items()}

    # forward returns
    fwd_raw = {h: (c.shift(-h) / c - 1) * 100 for h in (1, 5, 20)}
    lfwd = {h: np.log(c.shift(-h) / c) for h in (1, 5, 20)}
    sig_next = {"garch": sig_g.shift(-1), "rv20": sig_rv.shift(-1)}
    fwd = {}
    for k in ("garch", "rv20", "raw"):
        x = series[k]
        bmask = pd.Series(st[k]["bot"], index=x.index)
        for cond, sel in (("all", x.index), ("bottom", bmask[bmask].index)):
            for h in (1, 5, 20):
                fwd[(k, cond, h, "raw")] = dist(fwd_raw[h].reindex(sel))
                if k in sig_next:
                    z = (lfwd[h] / (sig_next[k] * np.sqrt(h))).reindex(sel)
                    fwd[(k, cond, h, "std")] = dist(z)

    # VIX buckets, from 1990: raw rows on the 1950 sample's deciles (the study's
    # Part 2.3), GARCH rows on the matched sample's z deciles
    def vmask(index, lo, hi):
        v1 = vix.reindex(spx.index).ffill(limit=3).shift(1).reindex(index)
        m = (index >= pd.Timestamp(VIX_FROM)) & v1.notna().values
        if lo is not None:
            m &= (v1 >= lo).values
        if hi is not None:
            m &= (v1 < hi).values
        return m
    s50, sg = st["raw1950"], st["garch"]
    vb = []
    for lbl, lo, hi in BUCKETS:
        m50, mg = vmask(r.index, lo, hi), vmask(idx, lo, hi)
        pr, n_raw, _ = follow(s50["bot"], s50["top"], 5, mask=m50)
        pg, n_g, _ = follow(sg["bot"], sg["top"], 5, mask=mg)
        d20 = dist(fwd_raw[20].reindex(r.index[s50["bot"] & m50]))
        vb.append({"label": lbl, "n_raw": n_raw, "p_raw": pr, "n_g": n_g, "p_g": pg,
                   "p10_20": d20.get("p10", np.nan)})
    vb_base = {"raw": follow(s50["bot"], s50["top"], 5, mask=vmask(r.index, None, None))[2],
               "garch": follow(sg["bot"], sg["top"], 5, mask=vmask(idx, None, None))[2]}

    # openers
    gi = spx.index
    r90 = allr.loc[VIX_FROM:].dropna()
    q01 = r90.quantile(0.01)
    vt1 = vix.reindex(gi).ffill(limit=3).shift(1).reindex(r90.index)
    prior = allr.abs().rolling(20, min_periods=20).max().shift(1).reindex(r90.index)
    bot1 = r90 <= q01
    op = r90[bot1 & (vt1 < 20) & (prior < 0.02)]
    openers = []
    for t, v in op.items():
        i = gi.get_loc(t)
        nxt = (spx.iloc[i + 1] / spx.iloc[i] - 1) * 100 if i + 1 < len(gi) else None
        five = (spx.iloc[i + 5] / spx.iloc[i] - 1) * 100 if i + 5 < len(gi) else None
        openers.append({"date": t.date(), "ret": v * 100, "vix": float(vt1.loc[t]),
                        "prior_max": float(prior.loc[t]) * 100, "next": nxt, "five": five})

    return {"first": r.index[0].date(), "as_of": r.index[-1].date(), "n": len(r),
            "matched_first": idx[0].date(), "n_matched": len(idx),
            "vix_last": vix.index[-1].date() if len(vix) else None,
            "fit_yr": fit_yr, "fit": fit, "st": st, "fwd": fwd, "vb": vb,
            "vb_base": vb_base, "openers": openers, "q01": q01 * 100,
            "n_bot1": int(bot1.sum()), "n_1990": len(r90)}


# ----------------------------------------------------------------- render
def _p(v, nd=1):
    return "n/a" if v is None or (isinstance(v, float) and np.isnan(v)) else f"{v:.{nd}f}%"


def _s(v, unit="%", nd=2):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "pending"
    return f"{v:+.{nd}f}{unit}"


def render(R: dict, via: str, source: str) -> str:
    st, fwd = R["st"], R["fwd"]
    f = R["fit"]
    L = ["# Two-sided tail base rates (item 124a), recomputed",
         "",
         f"Generated {dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')} "
         f"by `tools/calibration/tail_days_base_rates.py --source {source}`.",
         "",
         "| | |", "|---|---|",
         f"| As of | {R['as_of']} (the last S&P 500 close read); VIX through {R['vix_last']} |",
         f"| Sources | {via} |",
         f"| Sample | {R['first']} to {R['as_of']}, n = {R['n']:,}; matched (both sigmas) "
         f"{R['matched_first']} to {R['as_of']}, n = {R['n_matched']:,} |",
         f"| Latest GARCH fit | through {R['fit_yr'] - 1}-12-31, applied to {R['fit_yr']}: "
         f"omega {f['omega']:.4f}, alpha {f['alpha[1]']:.4f}, beta {f['beta[1]']:.4f}, "
         f"alpha+beta {f['alpha[1]'] + f['beta[1]']:.4f} |",
         f"| Computation SHA-256 | `{computation_sha256()}` |",
         "",
         "## The computation",
         "",
         "```text", COMPUTATION.rstrip("\n"), "```",
         "",
         "## 1. Follow-through: P(top-decile day within h | bottom-decile day)",
         "",
         "| Series | bottom-decile threshold | n | h=1 | h=5 | h=10 | any day h=1 | any day h=5 | any day h=10 |",
         "|---|---|---|---|---|---|---|---|---|"]
    names = {"garch": "GARCH-standardised", "rv20": "RV20-standardised",
             "raw": "raw, matched sample", "raw1950": "raw, from 1950"}
    for k in ("garch", "rv20", "raw", "raw1950"):
        s = st[k]
        unit = "σ" if k in ("garch", "rv20") else "%"
        L.append(f"| {names[k]} | ≤ {s['q10']:.2f}{unit} | {s[1][1]:,} | "
                 + " | ".join(_p(s[h][0]) for h in (1, 5, 10)) + " | "
                 + " | ".join(_p(s[h][2]) for h in (1, 5, 10)) + " |")
    L += ["", "## 2. VIX at T-1 (bottom-decile days from 1990)", "",
          "| VIX at T-1 | n (raw, 1950 deciles) | P(top ≤5), raw | n (GARCH deciles) | "
          "P(top ≤5), GARCH | 20-session 10th pct, raw |",
          "|---|---|---|---|---|---|"]
    for b in R["vb"]:
        L.append(f"| {b['label']} | {b['n_raw']:,} | {_p(b['p_raw'])} | {b['n_g']:,} | "
                 f"{_p(b['p_g'])} | {_s(b['p10_20'])} |")
    L.append(f"| any day from 1990 | | {_p(R['vb_base']['raw'])} | | "
             f"{_p(R['vb_base']['garch'])} | |")
    L += ["", "## 3. Clustering against the shuffled baseline", "",
          "| Series | top-decile days | share near a bottom-decile day | shuffled mean | "
          "shuffled 95% range | excess |", "|---|---|---|---|---|---|"]
    for k in ("garch", "rv20", "raw", "raw1950"):
        s = st[k]
        m, lo, hi = s["shuf"]
        L.append(f"| {names[k]} | {s['n_top']:,} | {s['clus']:.1f}% | {m:.1f}% | "
                 f"{lo:.1f}–{hi:.1f}% | {s['clus'] - m:+.1f}pp |")
    L += ["", "## 4. Forward returns after a bottom-decile day", "",
          "| Series | conditioning | h | n | mean | median | 10th pct | 90th pct | >0 |",
          "|---|---|---|---|---|---|---|---|---|"]
    for k in ("garch", "rv20", "raw"):
        kind = "std" if k != "raw" else "raw"
        unit = "σ" if kind == "std" else "%"
        for cond in ("bottom", "all"):
            for h in (1, 5, 20):
                d = fwd[(k, cond, h, kind)]
                L.append(f"| {names[k]} | {'bottom decile' if cond == 'bottom' else 'all days'} "
                         f"| {h} | {d['n']:,} | {_s(d['mean'], unit)} | {_s(d['median'], unit)} | "
                         f"{_s(d['p10'], unit)} | {_s(d['p90'], unit)} | {d['up']:.0f}% |")
    for k in ("garch", "rv20"):
        for cond in ("bottom", "all"):
            for h in (1, 5, 20):
                d = fwd[(k, cond, h, "raw")]
                L.append(f"| {names[k]} deciles, in % | "
                         f"{'bottom decile' if cond == 'bottom' else 'all days'} | {h} | "
                         f"{d['n']:,} | {_s(d['mean'])} | {_s(d['median'])} | "
                         f"{_s(d['p10'])} | {_s(d['p90'])} | {d['up']:.0f}% |")
    L += ["", "## 5. The openers, from 1990", "",
          f"Bottom 1% of {R['n_1990']:,} sessions from 1990 (≤ {R['q01']:.2f}%): "
          f"{R['n_bot1']} days; {len(R['openers'])} with VIX below 20 at T-1 and no "
          f"2% day in the prior 20; "
          f"{sum(1 for o in R['openers'] if o['ret'] <= -4)} at −4% or worse.", "",
          "| # | Date | Return | VIX at T-1 | largest abs. return, prior 20 | next session | five sessions |",
          "|---|---|---|---|---|---|---|"]
    for i, o in enumerate(R["openers"], 1):
        L.append(f"| {i} | {o['date']} | {o['ret']:+.2f}% | {o['vix']:.2f} | "
                 f"{o['prior_max']:.2f}% | {_s(o['next'])} | {_s(o['five'])} |")
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="item 124a's two-sided tail table")
    ap.add_argument("--source", choices=("store", "public"), default="store")
    ap.add_argument("--db", help="the observation store (default the package's)")
    ap.add_argument("--through", help="last session to read (default: all read)")
    ap.add_argument("--out", help="write here instead of stdout")
    a = ap.parse_args(argv)
    spx, vix, via = load(a.source, a.db)
    text = render(compute(spx, vix, a.through), via, a.source)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8", newline="\n")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
