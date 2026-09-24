"""
The Base Rates paper's Part I tables, computed from the store. (31.1)

    python tools/base_rates.py compute --dry-run
    python tools/base_rates.py compute
    python tools/base_rates.py maybe-recompute        # for the overnight job
    python tools/base_rates.py show baserate.returns_by_frequency
    python tools/base_rates.py paper                  # computed beside the paper

-----------------------------------------------------------------------------
WHY THE PAPER'S TABLES BECOME OBSERVATIONS
-----------------------------------------------------------------------------

A base rate cited in a decision packet has to be replayable AS OF the date it was
cited, or the packet's replay guarantee dies the first time a table is updated. A
paper's table is prose: it has no available_at, so a packet that cites "the p75
intra-year drawdown is -18%" cannot later prove which -18% it meant. Stored as an
observation, the table has the same three clocks as every other reading and the
as-of join answers the question for free.

So each table here is ONE observation whose value is the table as JSON:

    registry_key      baserate.<table>
    observation_type  calculated
    native_horizon    strategic
    half_life         permanent
    revision_policy   recomputed
    trigger_eligible  false          -- a base rate is a DENOMINATOR, never a signal

`trigger_eligible: false` is the load-bearing one. A base rate says what usually
happens; it cannot say that anything is happening now, and 31.6 holds the Part 26
freeze over every one of these.

-----------------------------------------------------------------------------
WHAT IS COMPUTED, AND WHAT IS HONESTLY ABSENT
-----------------------------------------------------------------------------

Computed from ^GSPC (24,797 daily closes from 1927-12-30) and ^VIX (1990-):

    baserate.returns_by_frequency    daily/weekly/monthly/annual distributions
    baserate.intra_year_drawdown     the worst decline inside each calendar year
    baserate.drawdown_by_depth       episode frequency, duration, recovery by band
    baserate.streaks_and_gaps        run lengths, direction memory -- gaps absent
    baserate.correlation_by_regime   stock/bond and pairwise, by volatility band
    baserate.vix_distribution        the VIX's own quantiles and move counts

ABSENT WITH A REASON, not approximated:

  * GAP STATISTICS. A gap is the open against the prior close, and the store holds
    CLOSES ONLY -- yfinance_source.py parses `Close` and stores that. So the
    paper's gap-fill rows and its overnight-versus-intraday row are reported
    `not_yet_sourced` with the series they would need. A "gap" computed from
    closes alone would be a two-day return wearing the wrong name.

  * THE STOCK/BOND CORRELATION BEFORE THE STORE'S BOND HISTORY. The long-run table
    in the paper spans the 1970s; the store's 10-year yield history reaches back
    about four years and its bond ETFs five. Each regime row states its own window
    and its n, and a row with fewer than MIN_CORRELATION_OBS observations reports
    absent rather than a correlation computed on a fortnight.

  * PRICE RETURN, NOT TOTAL RETURN. The store holds split-adjusted,
    dividend-unadjusted closes on purpose (yfinance_source.py explains why), and
    an index level is not a total-return series. The annual row is therefore the
    PRICE return, around 8%, not the ~10% total return the paper quotes -- the
    same number measured without the dividend. Both are named where the paper
    gives both, so the comparison is never between two different things.

-----------------------------------------------------------------------------
THE DRIFT FLAG -- A CHANGING BASE RATE IS ITSELF INFORMATION
-----------------------------------------------------------------------------

On every recompute each table's headline scalars are compared against the stored
version. A field that moves more than its declared tolerance writes a
`baserate.review_flag` observation naming the field, both values and the
tolerance. That is not an error path: a drawdown distribution that has genuinely
shifted is the most interesting thing this module can report, and the flag exists
so it reaches a human instead of being absorbed into the next quarter's numbers.

The tolerances are in REVIEW_TOLERANCE and they are deliberately tight enough that
a year of new data trips nothing and a methodology slip trips immediately.

-----------------------------------------------------------------------------
WHEN IT RECOMPUTES, AND WHY THERE IS NO NEW UNIT
-----------------------------------------------------------------------------

`maybe-recompute` is called by the overnight pass and answers three questions:
nothing stored yet, the stored METHOD_VERSION is not this one, or this is the
first session of a calendar year. Otherwise it exits 0 having done nothing and
said so. A base rate over a century does not move because a Tuesday happened, and
a second timer for a job that runs once a year is a unit to maintain for nothing.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any, Callable, Optional

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from altdata import observations, session                     # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# What it reads
# ---------------------------------------------------------------------------
GSPC = "yfinance.mkt_gspc"
VIX = "yfinance.mkt_vix"
BOND_YIELD = "fred.yield_10y"
BOND_ETF = "yfinance.mkt_ief"
SECTOR_PREFIX = "yfinance."

KEY_PREFIX = "baserate."
REVIEW_KEY = "baserate.review_flag"
SOURCE = "derived_base_rate"

# BUMPED WHEN THE COMPUTATION CHANGES, which is one of the three triggers for a
# recompute. A stored table records the version it was computed under, so a table
# from method-1 and a table from method-2 are never compared field by field and
# then flagged as drift -- a deliberate change is not a moving base rate.
METHOD_VERSION = "base-rates-method-1"

# THE DEPTH LADDER, which is the paper's own table to memorize. Declared here
# because every row of that table is one of these thresholds.
DEPTH_BANDS = (5.0, 10.0, 15.0, 20.0, 30.0, 50.0)

# The post-war subsample, reported beside the full one because the paper says the
# post-1950 figures run one to two points higher and a single number would hide it.
POSTWAR_FROM = "1950-01-01"

# A correlation on fewer than this many paired observations is not reported. One
# quarter of sessions: below it the standard error swamps the difference between
# the regimes the table exists to separate.
MIN_CORRELATION_OBS = 60

# The grid stored so a live move can be placed in the distribution without
# carrying 24,797 returns around. Dense in the tails, because that is where a
# daily move becomes interesting and where a linear interpolation over deciles
# would be worst.
PERCENTILE_GRID = (0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 20.0, 25.0, 30.0, 40.0,
                   50.0, 60.0, 70.0, 75.0, 80.0, 90.0, 95.0, 97.5, 99.0,
                   99.5, 99.9)


# ---------------------------------------------------------------------------
# Small statistics, written out rather than imported
# ---------------------------------------------------------------------------
def pctile(values: list[float], q: float) -> Optional[float]:
    """The q-th percentile by linear interpolation between order statistics.

    Written out rather than taken from numpy for one reason: the gate requires a
    recompute to be IDENTICAL, and a percentile is the one place a library change
    silently redefines an answer. numpy's default interpolation is this one today;
    pinning the definition here means it stays this one.
    """
    if not values:
        return None
    s = sorted(values)
    if len(s) == 1:
        return float(s[0])
    pos = (q / 100.0) * (len(s) - 1)
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return float(s[int(pos)])
    return float(s[lo] + (s[hi] - s[lo]) * (pos - lo))


def by_depth_percentiles(drawdowns: list[float], nd: int = 4) -> dict:
    """The paper's convention: p75 is the DEEP quartile, not the shallow one.

    A drawdown is a negative number, so the 75th percentile of the signed
    distribution is the SHALLOWEST quartile -- -7.7% on this sample -- while the
    paper's "p75 intra-year drawdown -18%" means the deep end. Both are correct and
    they are not the same field, so both are stored under names that say which is
    which. Comparing one against the other is how a -18% base rate becomes a -7.7%
    one in a packet.
    """
    if not drawdowns:
        return {"n": 0, "absent_reason": "no observations"}
    mags = [abs(v) for v in drawdowns]
    return {
        "n": len(mags),
        "convention": "percentiles of DEPTH, reported as negative numbers, so "
                      "p75 is deeper than p25 -- the paper's ordering",
        "p25": round(-pctile(mags, 25), nd),
        "median": round(-pctile(mags, 50), nd),
        "p75": round(-pctile(mags, 75), nd),
        "p90": round(-pctile(mags, 90), nd),
        "mean": round(-statistics.fmean(mags), nd),
        "deepest": round(-max(mags), nd),
    }


def summarise(values: list[float], nd: int = 4) -> dict:
    """n, the quartiles, mean, extremes and the positive share.

    The mean is reported BESIDE the median everywhere, because the gap between
    them is the paper's own point about skew rather than a redundancy.
    """
    if not values:
        return {"n": 0, "absent_reason": "no observations"}
    return {
        "n": len(values),
        "p25": round(pctile(values, 25), nd),
        "median": round(pctile(values, 50), nd),
        "p75": round(pctile(values, 75), nd),
        "mean": round(statistics.fmean(values), nd),
        "min": round(min(values), nd),
        "max": round(max(values), nd),
        "positive_share": round(
            sum(1 for v in values if v > 0) / len(values), 4),
    }


def grid_of(values: list[float], nd: int = 4) -> dict:
    return {str(q): (None if not values else round(pctile(values, q), nd))
            for q in PERCENTILE_GRID}


def correlation(xs: list[float], ys: list[float]) -> Optional[float]:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    mx = statistics.fmean(xs)
    my = statistics.fmean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return None
    return num / (dx * dy)


# ---------------------------------------------------------------------------
# Reading the inputs
# ---------------------------------------------------------------------------
def series(db: observations.ObservationStore, key: str,
           as_of: Optional[str] = None) -> list[tuple[str, float]]:
    """(date, value) for one metric, oldest first, one row per date.

    The store can hold several vintages of a date; as_of() returns them in
    availability order, so taking the LAST value seen for each date is taking the
    newest vintage knowable at the cutoff -- which is what a reference
    distribution wants.
    """
    latest: dict[str, float] = {}
    for r in db.as_of(key, as_of=as_of):
        v = r.get("value_num")
        if v is None:
            continue
        latest[str(r["observed_at"])[:10]] = float(v)
    return sorted(latest.items())


def returns_of(closes: list[tuple[str, float]]) -> list[tuple[str, float]]:
    """Simple percentage returns, in percent, dated by the LATER close."""
    out = []
    for (d0, p0), (d1, p1) in zip(closes, closes[1:]):
        if p0 > 0:
            out.append((d1, 100.0 * (p1 / p0 - 1.0)))
    return out


def period_last(closes: list[tuple[str, float]], key: Callable[[str], Any]
                ) -> list[tuple[str, float]]:
    """The last close of each period, for weekly/monthly/annual resampling."""
    seen: dict[Any, tuple[str, float]] = {}
    for d, p in closes:
        seen[key(d)] = (d, p)
    return [seen[k] for k in sorted(seen)]


def _iso_week(day: str) -> tuple[int, int]:
    d = dt.date.fromisoformat(day)
    y, w, _ = d.isocalendar()
    return (y, w)


# ---------------------------------------------------------------------------
# Table 1 -- the distribution at four frequencies
# ---------------------------------------------------------------------------
def table_returns_by_frequency(data: dict) -> dict:
    closes = data["gspc"]
    out: dict[str, Any] = {
        "series": GSPC,
        "first_close": closes[0][0] if closes else None,
        "last_close": closes[-1][0] if closes else None,
        "return_kind": "price",
        "return_note": (
            "SIMPLE PERCENTAGE PRICE RETURNS of the index level. Not total "
            "return: the store holds dividend-unadjusted closes, so the annual "
            "row is the paper's ~8% price figure and not its ~10% total return."),
        "frequencies": {},
    }
    frames = {
        "daily": closes,
        "weekly": period_last(closes, _iso_week),
        "monthly": period_last(closes, lambda d: d[:7]),
        "annual": period_last(closes, lambda d: d[:4]),
    }
    for name, frame in frames.items():
        rets = [v for _, v in returns_of(frame)]
        row = summarise(rets)
        row["percentile_grid"] = grid_of(rets)
        row["first"] = frame[0][0] if frame else None
        row["last"] = frame[-1][0] if frame else None
        post = [v for d, v in returns_of(frame) if d >= POSTWAR_FROM]
        row["postwar"] = summarise(post)
        out["frequencies"][name] = row
    return out


# ---------------------------------------------------------------------------
# Table 2 -- the worst decline inside a calendar year
# ---------------------------------------------------------------------------
def table_intra_year_drawdown(data: dict) -> dict:
    closes = data["gspc"]
    by_year: dict[str, list[tuple[str, float]]] = {}
    for d, p in closes:
        by_year.setdefault(d[:4], []).append((d, p))
    years: dict[str, dict] = {}
    for year, rows in sorted(by_year.items()):
        if len(rows) < 20:
            continue
        peak = rows[0][1]
        worst = 0.0
        worst_on = None
        for d, p in rows:
            peak = max(peak, p)
            dd = 100.0 * (p / peak - 1.0)
            if dd < worst:
                worst, worst_on = dd, d
        full = 100.0 * (rows[-1][1] / rows[0][1] - 1.0)
        years[year] = {"max_drawdown_pct": round(worst, 4),
                       "trough_on": worst_on,
                       "year_return_pct": round(full, 4),
                       "sessions": len(rows)}
    dds = [y["max_drawdown_pct"] for y in years.values()]
    rets = [y["year_return_pct"] for y in years.values()]
    deep = [y for y in years.values() if y["max_drawdown_pct"] <= -10.0]
    post_years = {y: v for y, v in years.items() if y >= POSTWAR_FROM[:4]}
    post_dds = [v["max_drawdown_pct"] for v in post_years.values()]
    post_rets = [v["year_return_pct"] for v in post_years.values()]
    out = {
        "series": GSPC,
        "definition": (
            "the worst close-to-close decline from the RUNNING PEAK WITHIN THE "
            "CALENDAR YEAR, the peak seeded at the year's first close. A year is "
            "included once it carries 20 sessions. CLOSING PRICES ONLY: an "
            "intraday drawdown is systematically deeper, by a point or more in a "
            "volatile year, and the store holds no intraday extremes."),
        "years": len(years),
        "distribution": summarise(dds),
        "by_depth": by_depth_percentiles(dds),
        "postwar": {"from": POSTWAR_FROM, "years": len(post_years),
                    "distribution": summarise(post_dds),
                    "by_depth": by_depth_percentiles(post_dds),
                    "annual_return_distribution": summarise(post_rets),
                    "share_of_years_positive": round(
                        sum(1 for r in post_rets if r > 0) / len(post_rets), 4)
                    if post_rets else None},
        "percentile_grid": grid_of(dds),
        "annual_return_distribution": summarise(rets),
        "share_of_years_positive": round(
            sum(1 for r in rets if r > 0) / len(rets), 4) if rets else None,
        "share_of_years_with_10pct_drawdown": round(
            len(deep) / len(years), 4) if years else None,
        "share_positive_despite_10pct_drawdown": round(
            sum(1 for y in deep if y["year_return_pct"] > 0) / len(deep), 4)
        if deep else None,
        "by_year": years,
    }
    return out


# ---------------------------------------------------------------------------
# Table 3 -- episodes by depth band
# ---------------------------------------------------------------------------
def drawdown_episodes(closes: list[tuple[str, float]]) -> list[dict]:
    """Peak-to-trough-to-recovery episodes measured from the RUNNING MAXIMUM.

    ONE DEFINITION, STATED, because the paper's ladder can be produced by two
    incompatible ones. An episode opens when the close falls below the running
    maximum, deepens while it keeps falling, and CLOSES when the prior maximum is
    recovered. A dip inside a larger decline is therefore not a second episode:
    1929-1932 is one -86% event and not two hundred -5% ones.

    The consequence to keep in view: during a long unrecovered decline no new
    episode can open, so the -5% frequency over 1929-1954 is structurally lower
    than it is post-war. That is why every band reports the post-1950 subsample
    beside the full one rather than one blended number.

    The largest counter-trend rally is measured inside the peak-to-trough window
    as the largest rise from any interim low to any later close before the trough
    -- the rally a short campaign has to survive, which is what the paper's row
    is for.
    """
    episodes: list[dict] = []
    if not closes:
        return episodes
    peak_i, peak = 0, closes[0][1]
    trough_i, trough = 0, closes[0][1]
    in_dd = False
    for i in range(1, len(closes)):
        p = closes[i][1]
        if p >= peak:
            if in_dd:
                episodes.append({"peak_i": peak_i, "trough_i": trough_i,
                                 "recovered_i": i})
            peak_i, peak = i, p
            trough_i, trough = i, p
            in_dd = False
            continue
        in_dd = True
        if p < trough:
            trough_i, trough = i, p
    if in_dd:
        episodes.append({"peak_i": peak_i, "trough_i": trough_i,
                         "recovered_i": None})

    # THE SECOND PASS, AND WHY IT IS A SECOND PASS. The largest counter-trend
    # rally lives strictly inside the peak-to-trough window, and that window is
    # not known until the trough is. Measuring it in one pass -- max gain from the
    # running low as the loop walks to RECOVERY -- silently includes the recovery
    # leg itself, which for a -50% decline is a +100% "rally". That produced a
    # median of +50% against the paper's +10%, and the number was not a different
    # convention: it was the wrong window.
    out: list[dict] = []
    for e in episodes:
        a, t, r = e["peak_i"], e["trough_i"], e["recovered_i"]
        pk, tr = closes[a][1], closes[t][1]
        best, low = 0.0, closes[a][1]
        for j in range(a, t + 1):
            p = closes[j][1]
            low = min(low, p)
            if low > 0:
                best = max(best, p / low - 1.0)
        out.append({
            "peak_on": closes[a][0], "peak": round(pk, 4),
            "trough_on": closes[t][0], "trough": round(tr, 4),
            "depth_pct": round(100.0 * (tr / pk - 1.0), 4),
            "recovered_on": closes[r][0] if r is not None else None,
            "sessions_peak_to_trough": t - a,
            "sessions_trough_to_recovery": (None if r is None else r - t),
            "largest_rally_pct": round(100.0 * best, 4),
            **({"open": True} if r is None else {}),
        })
    return out


def threshold_declines(closes: list[tuple[str, float]],
                       depth_pct: float) -> list[dict]:
    """Declines of `depth_pct` counted the way the paper's frequency row counts.

    TWO DEFINITIONS OF "A -5% DECLINE" EXIST AND THEY DIFFER BY A FACTOR OF FOUR.

    drawdown_episodes() measures from the RUNNING MAXIMUM and closes an episode
    only when that maximum is recovered. That is the right definition for a
    portfolio -- it is the loss from the high-water mark, and a dip inside a larger
    decline is not a second event. It produces 0.88 -5% episodes a year post-war,
    because during a long unrecovered decline no new episode can open at all.

    The paper says -5% happens three to four times a year, and no all-time-high
    definition yields that. Its row is counting SWINGS: a decline of X% from a
    local high, where the local high need not be an all-time one. That is the
    question an operator asks -- "how often do I sit through a 5% drop" -- and it
    is a different question from "how far below my high-water mark do I get".

    Both are stored, each named for the question it answers, because citing one
    where the other was meant is how "-5% is a three-times-a-year event" becomes
    "-5% is a once-every-fourteen-months event" in a packet.

    THE SWING DEFINITION NEEDS NO SECOND PARAMETER, which is why it is this one
    and not a local-peak rule with a lookback. The same X confirms both turns: a
    peak is confirmed when price falls X% from it, and the trough is confirmed when
    price rises X% from the low. `time_to_recover_sessions` is measured separately
    as the first close at or above the prior peak, which is the paper's own column
    and is not the same instant as the swing's confirmation.
    """
    out: list[dict] = []
    if not closes:
        return out
    thr = depth_pct / 100.0
    hi_i, hi = 0, closes[0][1]
    lo_i, lo = 0, closes[0][1]
    looking_for_peak = True
    for i in range(1, len(closes)):
        p = closes[i][1]
        if looking_for_peak:
            if p > hi:
                hi_i, hi = i, p
            elif hi > 0 and p <= hi * (1.0 - thr):
                looking_for_peak = False
                lo_i, lo = i, p
        else:
            if p < lo:
                lo_i, lo = i, p
            elif lo > 0 and p >= lo * (1.0 + thr):
                out.append({"peak_i": hi_i, "trough_i": lo_i, "confirmed_i": i})
                looking_for_peak = True
                hi_i, hi = i, p
    if not looking_for_peak:
        out.append({"peak_i": hi_i, "trough_i": lo_i, "confirmed_i": None})

    rows: list[dict] = []
    for e in out:
        a, t = e["peak_i"], e["trough_i"]
        pk, tr = closes[a][1], closes[t][1]
        recover = None
        for j in range(t + 1, len(closes)):
            if closes[j][1] >= pk:
                recover = j - t
                break
        rows.append({
            "peak_on": closes[a][0], "trough_on": closes[t][0],
            "depth_pct": round(100.0 * (tr / pk - 1.0), 4),
            "sessions_peak_to_trough": t - a,
            "time_to_recover_sessions": recover,
            **({"open": True} if e["confirmed_i"] is None else {}),
        })
    return rows


def _months(sessions: Optional[int]) -> Optional[float]:
    """Sessions as months, at the declared 21 sessions to a month."""
    return None if sessions is None else round(sessions / 21.0, 2)


def table_drawdown_by_depth(data: dict) -> dict:
    closes = data["gspc"]
    episodes = drawdown_episodes(closes)
    first_year = int(closes[0][0][:4]) if closes else 0
    last_year = int(closes[-1][0][:4]) if closes else 0
    years_full = max(1, last_year - first_year)
    years_post = max(1, last_year - 1950)

    def band(threshold: float, episodes_in: list[dict], years: float) -> dict:
        hit = [e for e in episodes_in if e["depth_pct"] <= -threshold]
        durs = [e["sessions_peak_to_trough"] for e in hit
                if e["sessions_peak_to_trough"] is not None]
        recs = [e["sessions_trough_to_recovery"] for e in hit
                if e["sessions_trough_to_recovery"] is not None]
        return {
            "episodes": len(hit),
            "per_year": round(len(hit) / years, 3),
            "years_between": round(years / len(hit), 2) if hit else None,
            "median_sessions_peak_to_trough": (
                round(pctile([float(x) for x in durs], 50), 1) if durs else None),
            "median_months_peak_to_trough": _months(
                pctile([float(x) for x in durs], 50) if durs else None),
            "median_sessions_trough_to_recovery": (
                round(pctile([float(x) for x in recs], 50), 1) if recs else None),
            "median_months_trough_to_recovery": _months(
                pctile([float(x) for x in recs], 50) if recs else None),
            "unrecovered": sum(1 for e in hit if e.get("open")),
        }

    def swing_band(threshold: float, rows: list[dict], years: float) -> dict:
        durs = [float(e["sessions_peak_to_trough"]) for e in rows]
        recs = [float(e["time_to_recover_sessions"]) for e in rows
                if e["time_to_recover_sessions"] is not None]
        depths = [e["depth_pct"] for e in rows]
        return {
            "declines": len(rows),
            "per_year": round(len(rows) / years, 3),
            "years_between": round(years / len(rows), 2) if rows else None,
            "median_depth_pct": (round(pctile(depths, 50), 2) if depths else None),
            "median_sessions_peak_to_trough": (
                round(pctile(durs, 50), 1) if durs else None),
            "median_months_peak_to_trough": _months(
                pctile(durs, 50) if durs else None),
            "median_sessions_to_recover_peak": (
                round(pctile(recs, 50), 1) if recs else None),
            "median_months_to_recover_peak": _months(
                pctile(recs, 50) if recs else None),
            "never_recovered": sum(
                1 for e in rows if e["time_to_recover_sessions"] is None),
        }

    swings = {t: threshold_declines(closes, t) for t in DEPTH_BANDS}
    post = [e for e in episodes if e["peak_on"] >= POSTWAR_FROM]
    bears = [e for e in episodes if e["depth_pct"] <= -20.0]
    out = {
        "series": GSPC,
        "definition": drawdown_episodes.__doc__.strip().split("\n")[0],
        "sessions_per_month": 21,
        "sample": {"first": closes[0][0] if closes else None,
                   "last": closes[-1][0] if closes else None,
                   "episodes": len(episodes),
                   "years_full": years_full,
                   "years_postwar": years_post},
        "definitions": {
            "from_running_max": (
                "loss from the high-water mark: an episode opens below the running "
                "maximum and closes when that maximum is recovered. The portfolio "
                "question."),
            "threshold_swings": (
                "a decline of X% from a LOCAL high, both turns confirmed by the "
                "same X. The operator's question -- how often a drop of this size "
                "is sat through -- and the definition the paper's frequency "
                "column counts."),
            "which_the_paper_uses": "threshold_swings for frequency and duration; "
                                    "from_running_max for the bear-property "
                                    "distribution",
        },
        "bands": {f"-{int(t)}%": {
            "from_running_max": {"full_sample": band(t, episodes, years_full),
                                 "postwar": band(t, post, years_post)},
            "threshold_swings": {
                "full_sample": swing_band(t, swings[t], years_full),
                "postwar": swing_band(
                    t, [e for e in swings[t] if e["peak_on"] >= POSTWAR_FROM],
                    years_post)},
        } for t in DEPTH_BANDS},
        "bear_properties": {
            "definition": "episodes at or beyond -20% from the running maximum",
            "n": len(bears),
            "depth_pct": summarise([e["depth_pct"] for e in bears]),
            "depth_by_depth": by_depth_percentiles(
                [e["depth_pct"] for e in bears], nd=2),
            "months_peak_to_trough": summarise(
                [e["sessions_peak_to_trough"] / 21.0 for e in bears
                 if e["sessions_peak_to_trough"] is not None], nd=2),
            "months_trough_to_recovery": summarise(
                [e["sessions_trough_to_recovery"] / 21.0 for e in bears
                 if e["sessions_trough_to_recovery"] is not None], nd=2),
            "largest_counter_trend_rally_pct": summarise(
                [e["largest_rally_pct"] for e in bears]),
            # NO SLICE. This was `[:12]`, which happened to equal the count
            # today and would silently print twelve rows under `n: 13` the first
            # time a thirteenth bear qualified -- a table disagreeing with its own
            # count, in the one figure the Base Rates erratum of 23 September 2026
            # exists to keep single-valued.
            "episodes": sorted(bears, key=lambda e: e["depth_pct"]),
        },
    }
    return out


# ---------------------------------------------------------------------------
# Table 4 -- streaks, direction memory, and the gaps that are not sourced
# ---------------------------------------------------------------------------
def table_streaks_and_gaps(data: dict) -> dict:
    rets = returns_of(data["gspc"])
    signs = [1 if v > 0 else (-1 if v < 0 else 0) for _, v in rets]
    n = len(signs)
    runs: dict[str, Any] = {}
    for k in (2, 3, 5):
        up = sum(1 for i in range(n - k + 1)
                 if all(s > 0 for s in signs[i:i + k]))
        down = sum(1 for i in range(n - k + 1)
                   if all(s < 0 for s in signs[i:i + k]))
        runs[f"p_{k}_consecutive_up"] = round(up / max(1, n - k + 1), 4)
        runs[f"p_{k}_consecutive_down"] = round(down / max(1, n - k + 1), 4)

    longest_up = longest_down = cur = 0
    cur_sign = 0
    for s in signs:
        if s == cur_sign and s != 0:
            cur += 1
        else:
            cur_sign, cur = s, 1
        if cur_sign > 0:
            longest_up = max(longest_up, cur)
        elif cur_sign < 0:
            longest_down = max(longest_down, cur)

    ups = sum(1 for s in signs if s > 0)
    up_then_up = sum(1 for a, b in zip(signs, signs[1:]) if a > 0 and b > 0)
    down_then_up = sum(1 for a, b in zip(signs, signs[1:]) if a < 0 and b > 0)
    vals = [v for _, v in rets]
    lag1 = correlation(vals[:-1], vals[1:])

    return {
        "series": GSPC,
        "n_sessions": n,
        "p_up": round(ups / n, 4) if n else None,
        "runs": runs,
        "longest_up_run": longest_up,
        "longest_down_run": longest_down,
        "p_up_given_up": round(up_then_up / ups, 4) if ups else None,
        "p_up_given_down": round(
            down_then_up / max(1, sum(1 for s in signs if s < 0)), 4),
        "lag1_autocorrelation": round(lag1, 5) if lag1 is not None else None,
        "memory_note": (
            "p_up_given_up against p_up is the paper's point: the difference is "
            "the whole of daily direction's memory, and it is small."),
        "gaps": {
            "state": "not_yet_sourced",
            "needs": ["an Open series per symbol, e.g. yfinance.mkt_spy_open"],
            "reason": (
                "a gap is the OPEN against the prior close, and the store holds "
                "closes only -- yfinance_source.py parses Close and stores that. "
                "A gap computed from closes alone is a two-day return wearing "
                "the wrong name, and the gap-fill base rate the Daily's fade "
                "setup is sized against would be measuring something else."),
        },
        "overnight_vs_intraday": {
            "state": "not_yet_sourced",
            "needs": ["an Open series per symbol"],
            "reason": (
                "the split needs the open: overnight is prior close to open and "
                "intraday is open to close. Same missing series as the gaps."),
        },
    }


# ---------------------------------------------------------------------------
# Table 5 -- correlation, by the vol dial's own bands
# ---------------------------------------------------------------------------
def vol_bands() -> list[dict]:
    """The vol dial's level bands, read from config rather than redeclared.

    The regimes this table splits on ARE the dial's states. Writing a second
    threshold table here would mean a calm regime in the base rates and a
    different calm regime in the object, and a reader would have no way to know
    which one a sentence meant.
    """
    try:
        import yaml                                            # noqa: PLC0415
        with (REPO / "config" / "market_state.yaml").open(encoding="utf-8") as fp:
            cfg = yaml.safe_load(fp) or {}
        bands = (((cfg.get("dials") or {}).get("vol") or {}).get("level_bands")
                 or [])
        return [{"state": str(b.get("state")),
                 "min_level": float(b.get("min_level", 0))} for b in bands]
    except Exception:                                          # noqa: BLE001
        return []


def table_correlation_by_regime(data: dict) -> dict:
    gspc_r = dict(returns_of(data["gspc"]))
    vix = dict(data["vix"])
    bands = vol_bands()
    yield_chg = {d: v for d, v in _diffs(data["bond_yield"])}
    ief_r = dict(returns_of(data["bond_etf"]))
    sector_r = {k: dict(returns_of(v)) for k, v in data["sectors"].items()}

    def band_of(level: float) -> Optional[str]:
        for b in bands:
            if level >= b["min_level"]:
                return b["state"]
        return None

    rows: dict[str, Any] = {}
    for b in bands:
        rows[b["state"]] = {"vix_min_level": b["min_level"], "sessions": 0}
    rows["all"] = {"vix_min_level": None, "sessions": 0}

    buckets: dict[str, list[str]] = {k: [] for k in rows}
    for d, level in vix.items():
        st = band_of(level)
        if st in buckets:
            buckets[st].append(d)
        buckets["all"].append(d)

    for name, days in buckets.items():
        days = sorted(days)
        rows[name]["sessions"] = len(days)
        rows[name]["window"] = (days[0], days[-1]) if days else None
        # stock against the 10-year YIELD change: a positive number here means
        # equities and yields moved together, which is the NEGATIVE of the
        # stock/bond-price correlation the paper tabulates. Both signs are
        # reported so nobody has to remember the inversion.
        pairs = [(gspc_r[d], yield_chg[d]) for d in days
                 if d in gspc_r and d in yield_chg]
        rows[name]["n_stock_yield"] = len(pairs)
        if len(pairs) >= MIN_CORRELATION_OBS:
            c = correlation([a for a, _ in pairs], [b2 for _, b2 in pairs])
            rows[name]["corr_stock_vs_10y_yield_change"] = (
                round(c, 4) if c is not None else None)
            rows[name]["corr_stock_vs_bond_price_implied"] = (
                round(-c, 4) if c is not None else None)
        else:
            rows[name]["corr_stock_vs_10y_yield_change"] = None
            rows[name]["absent_reason_stock_bond"] = (
                f"{len(pairs)} paired sessions, below the declared minimum of "
                f"{MIN_CORRELATION_OBS} -- {BOND_YIELD}'s history in the store "
                f"is about four years, not the paper's five decades")
        pairs2 = [(gspc_r[d], ief_r[d]) for d in days
                  if d in gspc_r and d in ief_r]
        rows[name]["n_stock_bond_etf"] = len(pairs2)
        if len(pairs2) >= MIN_CORRELATION_OBS:
            c2 = correlation([a for a, _ in pairs2], [b2 for _, b2 in pairs2])
            rows[name]["corr_stock_vs_ief"] = round(c2, 4) if c2 else None
        else:
            rows[name]["corr_stock_vs_ief"] = None
        # average pairwise correlation across the eleven sector funds, which is a
        # DECLARED PROXY for the paper's average pairwise STOCK correlation: the
        # sectors are eleven portfolios, and a portfolio of portfolios is more
        # correlated at the top than its members are. The proxy therefore
        # OVERSTATES pairwise correlation, which is the opposite direction from
        # the breadth proxy's understatement, and it is labelled either way.
        keys = sorted(sector_r)
        cs = []
        for i, k1 in enumerate(keys):
            for k2 in keys[i + 1:]:
                common = [d for d in days if d in sector_r[k1] and d in sector_r[k2]]
                if len(common) < MIN_CORRELATION_OBS:
                    continue
                c3 = correlation([sector_r[k1][d] for d in common],
                                 [sector_r[k2][d] for d in common])
                if c3 is not None:
                    cs.append(c3)
        rows[name]["avg_pairwise_sector_correlation"] = (
            round(statistics.fmean(cs), 4) if cs else None)
        rows[name]["n_sector_pairs"] = len(cs)
        if not cs:
            rows[name]["absent_reason_pairwise"] = (
                f"no sector pair has {MIN_CORRELATION_OBS} sessions in this band")

    return {
        "regime_definition": (
            "the vol dial's own VIX level bands, read from "
            "config/market_state.yaml so a calm regime here and a calm dial "
            "state are the same thing"),
        "bands": bands,
        "proxies": {
            "avg_pairwise_sector_correlation": {
                "proxy_for": "average pairwise single-stock correlation",
                "sample": "sector_etf_proxy",
                "direction": "OVERSTATES -- eleven cap-weighted funds are more "
                             "correlated with each other than their holdings are",
            },
        },
        "rows": rows,
    }


def _diffs(rows: list[tuple[str, float]]) -> list[tuple[str, float]]:
    """First differences, dated by the later observation."""
    return [(d1, v1 - v0) for (d0, v0), (d1, v1) in zip(rows, rows[1:])]


# ---------------------------------------------------------------------------
# Table 6 -- the VIX's own distribution, and the move counts
# ---------------------------------------------------------------------------
def table_vix_distribution(data: dict) -> dict:
    vix = data["vix"]
    levels = [v for _, v in vix]
    rets = returns_of(data["gspc"])
    by_year: dict[str, list[float]] = {}
    for d, v in rets:
        by_year.setdefault(d[:4], []).append(v)
    one_pct = [sum(1 for v in vs if abs(v) >= 1.0) for vs in by_year.values()]
    two_pct = [sum(1 for v in vs if abs(v) >= 2.0) for vs in by_year.values()]
    worst_day = [min(vs) for vs in by_year.values() if vs]
    vix_year: dict[str, list[float]] = {}
    for d, v in vix:
        vix_year.setdefault(d[:4], []).append(v)
    return {
        "series": VIX,
        "sample": {"first": vix[0][0] if vix else None,
                   "last": vix[-1][0] if vix else None, "n": len(levels)},
        "level_distribution": summarise(levels, nd=2),
        "percentile_grid": grid_of(levels, nd=2),
        "annual_median": {y: round(pctile(vs, 50), 2)
                          for y, vs in sorted(vix_year.items())},
        "move_counts_per_year": {
            "series": GSPC,
            "definition": "sessions per calendar year with an absolute close-to-"
                          "close move at or beyond the threshold",
            "abs_1pct": summarise([float(x) for x in one_pct], nd=1),
            "abs_2pct": summarise([float(x) for x in two_pct], nd=1),
        },
        "largest_single_day_decline_per_year": summarise(worst_day, nd=3),
    }


# ---------------------------------------------------------------------------
# The roster
# ---------------------------------------------------------------------------
TABLE_BUILDERS: dict[str, Callable[[dict], dict]] = {
    "baserate.returns_by_frequency": table_returns_by_frequency,
    "baserate.intra_year_drawdown": table_intra_year_drawdown,
    "baserate.drawdown_by_depth": table_drawdown_by_depth,
    "baserate.streaks_and_gaps": table_streaks_and_gaps,
    "baserate.correlation_by_regime": table_correlation_by_regime,
    "baserate.vix_distribution": table_vix_distribution,
}
TABLE_KEYS: tuple[str, ...] = tuple(sorted(TABLE_BUILDERS))


# THE HEADLINE FIELDS WATCHED FOR DRIFT, with the tolerance each is allowed to
# move on a recompute. A field not listed here is recomputed and stored without a
# comparison: the point is to watch the numbers a decision would cite, not to
# alarm on the twelfth decimal of a percentile grid.
#
# Tolerances are in the field's own units -- percentage points for a return or a
# drawdown, a share for a share, months for a duration. Tight enough that one more
# year of data trips nothing (a year is ~1% of a 99-year sample) and a changed
# definition trips at once.
REVIEW_TOLERANCE: dict[str, float] = {
    "baserate.returns_by_frequency|frequencies.daily.median": 0.02,
    "baserate.returns_by_frequency|frequencies.daily.positive_share": 0.01,
    "baserate.returns_by_frequency|frequencies.annual.median": 1.5,
    "baserate.returns_by_frequency|frequencies.annual.positive_share": 0.03,
    "baserate.intra_year_drawdown|distribution.median": 1.0,
    "baserate.intra_year_drawdown|distribution.p75": 1.5,
    "baserate.intra_year_drawdown|distribution.mean": 1.0,
    "baserate.intra_year_drawdown|share_of_years_positive": 0.03,
    "baserate.drawdown_by_depth|bear_properties.depth_pct.median": 2.0,
    "baserate.drawdown_by_depth|bear_properties.largest_counter_trend_rally_pct.median": 2.0,
    "baserate.streaks_and_gaps|p_up": 0.01,
    "baserate.streaks_and_gaps|p_up_given_up": 0.01,
    "baserate.vix_distribution|level_distribution.median": 0.5,
    "baserate.vix_distribution|level_distribution.p75": 1.0,
}

# WHAT THE PAPER SAYS, so the gate can print both columns. Each entry is the
# paper's figure, the tolerance it must land inside, and the field to compare.
#
# WHICH SAMPLE EACH ROW USES IS PART OF THE COMPARISON, and working that out was
# the substance of building this table. The paper's source notes say "1928-2026"
# throughout, but its numbers do not all come from that sample:
#
#   * The FREQUENCY ladder matches the full sample almost exactly on the swing
#     definition -- -5% 3.4 a year against its 3-4, -10% 1.04 against its ~1,
#     -20% every 3.7 years against its 4-5, -30% every 7.6 against its decade.
#   * The INTRA-YEAR DRAWDOWN quartiles match the POST-1950 subsample and not the
#     full one: post-war gives -7.6 / -10.3 / -17.2 with a mean of -13.6 against
#     the paper's -6 / -10 / -18 and -14, while the full sample runs three points
#     deeper at every quartile because it contains the Depression. The paper's
#     figures are a modern-sample statement whatever its source note says, and
#     this is recorded here rather than resolved by widening a tolerance until
#     the full sample fits.
#   * The ANNUAL POSITIVE SHARE is compared post-war AND as a price return, so it
#     is two adjustments away from the paper's ~74%: 0.68 full-sample price, 0.73
#     post-war price, and the paper's figure is total return. The dividend is
#     worth the difference between them.
#
# Tolerances are wider than REVIEW_TOLERANCE on purpose: the paper rounds, states
# several figures as ranges, and quotes total return where this computes price.
PAPER_FIGURES: tuple[tuple[str, str, float, float, str], ...] = (
    ("baserate.returns_by_frequency", "frequencies.daily.positive_share",
     0.54, 0.02, "Ch 1.1 daily positive share ~54% [full]"),
    ("baserate.returns_by_frequency", "frequencies.daily.median",
     0.05, 0.03, "Ch 1.3 daily median +0.05% [full]"),
    ("baserate.returns_by_frequency", "frequencies.daily.p25",
     -0.50, 0.15, "Ch 1.3 daily p25 -0.50% [full]"),
    ("baserate.returns_by_frequency", "frequencies.daily.p75",
     0.58, 0.15, "Ch 1.3 daily p75 +0.58% [full]"),
    ("baserate.returns_by_frequency", "frequencies.monthly.positive_share",
     0.625, 0.03, "Ch 1.1 monthly positive share ~62-63% [full]"),
    ("baserate.returns_by_frequency", "frequencies.monthly.median",
     1.1, 0.4, "Ch 1.3 monthly median +1.1% [full]"),
    ("baserate.returns_by_frequency", "frequencies.annual.postwar.positive_share",
     0.74, 0.05, "Ch 1.1 annual positive share ~73-75% [postwar, price]"),
    # THE MEAN, NOT THE MEDIAN, because the paper's "+8% price" is an average and
    # this table carries both. Comparing its median (+11.8%) against the paper's
    # mean would be the exact error the module's own docstring warns about.
    ("baserate.returns_by_frequency", "frequencies.annual.mean",
     8.0, 3.0, "Ch 1.1 annual ~+8% price return, MEAN [full, price]"),
    ("baserate.intra_year_drawdown", "postwar.by_depth.median",
     -10.0, 2.0, "Ch 1.3 intra-year drawdown median -10% [postwar]"),
    ("baserate.intra_year_drawdown", "postwar.by_depth.p75",
     -18.0, 3.0, "Ch 1.3 intra-year drawdown p75 -18% [postwar, depth]"),
    ("baserate.intra_year_drawdown", "postwar.by_depth.p25",
     -6.0, 2.5, "Ch 1.3 intra-year drawdown p25 -6% [postwar, depth]"),
    ("baserate.intra_year_drawdown", "postwar.by_depth.mean",
     -14.0, 2.0, "Ch 2.2 average intra-year drawdown ~-14% [postwar]"),
    ("baserate.intra_year_drawdown", "postwar.share_of_years_positive",
     0.74, 0.06, "Ch 2.2 positive in ~3 years in 4 [postwar, price]"),
    ("baserate.drawdown_by_depth", "bands.-5%.threshold_swings.full_sample.per_year",
     3.5, 1.0, "Ch 2.1 -5% three to four times a year [full, swings]"),
    ("baserate.drawdown_by_depth", "bands.-10%.threshold_swings.full_sample.per_year",
     1.0, 0.4, "Ch 2.1 -10% about once a year [full, swings]"),
    ("baserate.drawdown_by_depth", "bands.-15%.threshold_swings.full_sample.per_year",
     0.5, 0.2, "Ch 2.1 -15% about every 2 years [full, swings]"),
    ("baserate.drawdown_by_depth", "bands.-20%.threshold_swings.full_sample.years_between",
     4.5, 2.0, "Ch 2.1 -20% every 4-5 years [full, swings]"),
    ("baserate.drawdown_by_depth", "bands.-30%.threshold_swings.full_sample.years_between",
     10.0, 4.0, "Ch 2.1 -30% about every decade [full, swings]"),
    ("baserate.drawdown_by_depth", "bear_properties.depth_by_depth.median",
     -30.0, 5.0, "Ch 2.1 bear depth median -30% [full, running max]"),
    ("baserate.drawdown_by_depth", "bear_properties.depth_by_depth.p75",
     -48.0, 5.0, "Ch 2.1 bear depth p75 -48% [full, depth]"),
    ("baserate.drawdown_by_depth", "bear_properties.depth_by_depth.deepest",
     -86.0, 2.0, "Ch 2.1 deepest in sample -86% (1929-32) [full]"),
    ("baserate.drawdown_by_depth",
     "bear_properties.largest_counter_trend_rally_pct.median",
     10.0, 5.0, "Ch 2.1 largest counter-trend rally median +10% [full]"),
    ("baserate.drawdown_by_depth",
     "bear_properties.largest_counter_trend_rally_pct.p75",
     16.0, 5.0, "Ch 2.1 largest counter-trend rally p75 +16% [full]"),
    ("baserate.drawdown_by_depth",
     "bear_properties.largest_counter_trend_rally_pct.max",
     46.0, 3.0, "Ch 2.1 largest rally in sample +46% (Nov29-Apr30) [full]"),
    ("baserate.streaks_and_gaps", "runs.p_2_consecutive_up",
     0.29, 0.03, "Ch 4 two up days in a row ~29% [full]"),
    ("baserate.streaks_and_gaps", "runs.p_3_consecutive_up",
     0.16, 0.03, "Ch 4 three in a row ~16% [full]"),
    ("baserate.streaks_and_gaps", "runs.p_5_consecutive_up",
     0.05, 0.02, "Ch 4 five in a row ~5% [full]"),
    ("baserate.streaks_and_gaps", "p_up_given_up",
     0.54, 0.03, "Ch 4 P(up | up) ~54%, essentially unconditional [full]"),
    ("baserate.vix_distribution", "level_distribution.median",
     17.6, 1.5, "Ch 1.3 VIX median ~17.6 [1990-]"),
    ("baserate.vix_distribution", "level_distribution.p25",
     13.5, 1.5, "Ch 1.3 VIX p25 ~13.5 [1990-]"),
    ("baserate.vix_distribution", "level_distribution.p75",
     22.5, 2.0, "Ch 1.3 VIX p75 ~22.5 [1990-]"),
    ("baserate.vix_distribution", "percentile_grid.95.0",
     33.0, 4.0, "Ch 1.3 VIX p95 near 33 [1990-]"),
    ("baserate.vix_distribution", "move_counts_per_year.abs_1pct.median",
     55.0, 20.0, "Ch 1.2 ~50-60 sessions a year move +/-1% [full]"),
    ("baserate.vix_distribution", "move_counts_per_year.abs_2pct.median",
     11.0, 6.0, "Ch 1.2 ~10-12 sessions a year move +/-2% [full]"),
)


def dig(table: dict, path: str) -> Any:
    """A dotted path into a table.

    GREEDY ON THE LONGEST KEY at each step, because two of the keys worth citing
    contain dots themselves: the percentile grid is keyed "95.0" and the depth
    bands are keyed "-5%". Splitting naively on "." would walk into "95" and find
    nothing, which would report a present figure as absent -- the one failure mode
    a comparison against the paper must not have.
    """
    cur: Any = table
    rest = path
    while rest:
        if not isinstance(cur, dict):
            return None
        for part in sorted((k for k in cur if rest == k or rest.startswith(k + ".")),
                           key=len, reverse=True):
            cur = cur[part]
            rest = rest[len(part):].lstrip(".")
            break
        else:
            return None
    return cur


# ---------------------------------------------------------------------------
# Computing, storing, and the drift comparison
# ---------------------------------------------------------------------------
def load_inputs(db: observations.ObservationStore,
                as_of: Optional[str] = None) -> dict:
    from altdata.sources import yfinance_source as yf_src
    sectors = {k: series(db, f"{SECTOR_PREFIX}{k}", as_of)
               for k in yf_src.SECTOR_KEYS}
    return {
        "gspc": series(db, GSPC, as_of),
        "vix": series(db, VIX, as_of),
        "bond_yield": series(db, BOND_YIELD, as_of),
        "bond_etf": series(db, BOND_ETF, as_of),
        "sectors": {k: v for k, v in sectors.items() if v},
    }


def compute(as_of: Optional[str] = None,
            store: Optional[observations.ObservationStore] = None) -> dict:
    """Every table, keyed by registry key. Never raises on a missing input."""
    own = store is None
    db = store or observations.ObservationStore()
    try:
        data = load_inputs(db, as_of)
        stamp = session.utc_iso(timespec="microseconds")
        observed = session.last_completed_session().isoformat()
        out: dict[str, dict] = {}
        for key, fn in sorted(TABLE_BUILDERS.items()):
            if not data["gspc"]:
                out[key] = {"state": "absent",
                            "absent_reason": f"{GSPC} has no observations in the "
                                             f"store; run tools/backfill_prices.py "
                                             f"--period max --symbols ^GSPC"}
            else:
                try:
                    out[key] = fn(data)
                except Exception as exc:                       # noqa: BLE001
                    out[key] = {"state": "error",
                                "absent_reason": f"{type(exc).__name__}: {exc}"}
            out[key]["method_version"] = METHOD_VERSION
            out[key]["computed_at"] = stamp
            out[key]["session"] = observed
            out[key]["as_of"] = as_of
        return out
    finally:
        if own:
            db.close()


def latest(key: str, as_of: Optional[str] = None,
           store: Optional[observations.ObservationStore] = None
           ) -> Optional[dict]:
    """The stored table. Reads; never computes -- the same rule as regime.latest."""
    own = store is None
    db = store or observations.ObservationStore()
    try:
        rows = db.as_of(key, as_of=as_of)
        if not rows:
            return None
        return json.loads(rows[-1]["value_text"])
    finally:
        if own:
            db.close()


def drift(previous: Optional[dict], current: dict, key: str) -> list[dict]:
    """Fields that moved more than their tolerance. Empty when there is nothing."""
    if not previous:
        return []
    if previous.get("method_version") != current.get("method_version"):
        return [{"field": "method_version", "previous": previous.get(
            "method_version"), "current": current.get("method_version"),
            "tolerance": None,
            "note": "a deliberate method change, not drift -- fields are not "
                    "compared across methods"}]
    out = []
    for spec, tol in sorted(REVIEW_TOLERANCE.items()):
        k, path = spec.split("|", 1)
        if k != key:
            continue
        was, now = dig(previous, path), dig(current, path)
        if was is None or now is None:
            continue
        if abs(float(now) - float(was)) > tol:
            out.append({"field": path, "previous": was, "current": now,
                        "tolerance": tol,
                        "moved": round(float(now) - float(was), 6)})
    return out


def store_tables(tables: dict, dry_run: bool = False,
                 store: Optional[observations.ObservationStore] = None) -> dict:
    own = store is None
    db = store or observations.ObservationStore()
    try:
        written = 0
        flags: list[dict] = []
        for key, table in sorted(tables.items()):
            moved = drift(latest(key, store=db), table, key)
            if moved:
                flags.append({"table": key, "fields": moved})
            if dry_run:
                continue
            written += db.write(
                key, None, table["session"], table["computed_at"],
                json.dumps(table, sort_keys=True), source=SOURCE,
                availability_kind="ingest_instant")
        if flags and not dry_run:
            written += db.write(
                REVIEW_KEY, None,
                (tables[sorted(tables)[0]].get("session") if tables
                 else session.last_completed_session().isoformat()),
                session.utc_iso(timespec="microseconds"),
                json.dumps({"method_version": METHOD_VERSION, "flags": flags},
                           sort_keys=True),
                source=SOURCE, availability_kind="ingest_instant")
        return {"written": written, "tables": len(tables), "flags": flags,
                "dry_run": dry_run}
    finally:
        if own:
            db.close()


def should_recompute(store: Optional[observations.ObservationStore] = None,
                     today: Optional[str] = None) -> tuple[bool, str]:
    """Nothing stored, a new method, or the first session of a calendar year."""
    own = store is None
    db = store or observations.ObservationStore()
    try:
        have = {k: latest(k, store=db) for k in TABLE_KEYS}
        missing = [k for k, v in have.items() if not v]
        if missing:
            return True, f"{len(missing)} table(s) not stored: {missing[:3]}"
        stale = [k for k, v in have.items()
                 if (v or {}).get("method_version") != METHOD_VERSION]
        if stale:
            return True, (f"{len(stale)} table(s) computed under an earlier "
                          f"method than {METHOD_VERSION}")
        day = dt.date.fromisoformat(today) if today else \
            session.last_completed_session()
        first = session.first_session_of_year(day.year)
        if first is not None and day == first:
            return True, (f"{day.isoformat()} is the first session of "
                          f"{day.year}, and these are annual tables")
        return False, (f"tables are current at {METHOD_VERSION} and "
                       f"{day.isoformat()} is not the first session of the year")
    finally:
        if own:
            db.close()


# ---------------------------------------------------------------------------
# The reading the close report does
# ---------------------------------------------------------------------------
def percentile_of_move(move_pct: float, frequency: str = "daily",
                       table: Optional[dict] = None,
                       store: Optional[observations.ObservationStore] = None
                       ) -> Optional[dict]:
    """Where a move sits in the LONG-RUN distribution, from the stored grid.

    Interpolated inside the stored percentile grid and clamped at its ends: a move
    beyond the 99.9th percentile reports 99.9 with `beyond_grid`, because the grid
    cannot say whether it is the 99.95th or the 99.99th and pretending otherwise
    would invent precision at exactly the moment a reader would act on it.
    """
    t = table if table is not None else latest(
        "baserate.returns_by_frequency", store=store)
    if not t:
        return None
    grid = dig(t, f"frequencies.{frequency}.percentile_grid") or {}
    pts = sorted(((float(q), float(v)) for q, v in grid.items()
                  if v is not None), key=lambda p: p[1])
    if len(pts) < 2:
        return None
    out = {"move_pct": round(float(move_pct), 4), "frequency": frequency,
           "series": t.get("series"), "n": dig(t, f"frequencies.{frequency}.n"),
           "sample_first": dig(t, f"frequencies.{frequency}.first"),
           "sample_last": dig(t, f"frequencies.{frequency}.last"),
           "method_version": t.get("method_version")}
    if move_pct <= pts[0][1]:
        out.update({"percentile": pts[0][0], "beyond_grid": "below"})
        return out
    if move_pct >= pts[-1][1]:
        out.update({"percentile": pts[-1][0], "beyond_grid": "above"})
        return out
    for (q0, v0), (q1, v1) in zip(pts, pts[1:]):
        if v0 <= move_pct <= v1:
            span = v1 - v0
            frac = 0.0 if span == 0 else (move_pct - v0) / span
            out["percentile"] = round(q0 + (q1 - q0) * frac, 2)
            return out
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _print_paper(tables: dict) -> int:
    worst = 0
    print(f"{'figure':<58} {'computed':>10} {'paper':>10} {'tol':>7}  verdict")
    for key, path, paper, tol, note in PAPER_FIGURES:
        got = dig(tables.get(key) or {}, path)
        if got is None:
            print(f"{note:<58} {'absent':>10} {paper:>10.3f} {tol:>7.3f}  ABSENT")
            worst = max(worst, 1)
            continue
        ok = abs(float(got) - paper) <= tol
        worst = max(worst, 0 if ok else 1)
        print(f"{note:<58} {float(got):>10.3f} {paper:>10.3f} {tol:>7.3f}  "
              f"{'ok' if ok else 'OUTSIDE'}")
    return worst


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Base-rate tables from the store.")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compute")
    c.add_argument("--dry-run", action="store_true")
    c.add_argument("--as-of", default=None)
    m = sub.add_parser("maybe-recompute")
    m.add_argument("--today", default=None)
    s = sub.add_parser("show")
    s.add_argument("key")
    sub.add_parser("paper")
    sub.add_parser("keys")
    pm = sub.add_parser("percentile")
    pm.add_argument("move", type=float)
    pm.add_argument("--frequency", default="daily")
    a = p.parse_args(argv)

    if a.cmd == "keys":
        for k in TABLE_KEYS:
            print(k)
        return 0

    if a.cmd == "show":
        t = latest(a.key)
        if t is None:
            print(f"no stored table for {a.key}")
            return 1
        print(json.dumps(t, indent=2, sort_keys=True))
        return 0

    if a.cmd == "percentile":
        r = percentile_of_move(a.move, a.frequency)
        print(json.dumps(r, indent=2, sort_keys=True))
        return 0 if r else 1

    if a.cmd == "paper":
        return _print_paper(compute())

    if a.cmd == "maybe-recompute":
        go, why = should_recompute(today=a.today)
        print(f"recompute={'yes' if go else 'no'}  {why}")
        if not go:
            return 0
        tables = compute()
        r = store_tables(tables)
        print(f"{r['written']} row(s) written for {r['tables']} table(s)")
        for f in r["flags"]:
            print(f"  REVIEW {f['table']}: {f['fields']}")
        return 0

    tables = compute(as_of=a.as_of)
    r = store_tables(tables, dry_run=a.dry_run)
    for key in TABLE_KEYS:
        t = tables[key]
        note = t.get("absent_reason") or ""
        print(f"  {key:<38} {'ABSENT ' + note[:40] if note else 'ok'}")
    print(f"\n{r['written']} row(s) written for {r['tables']} table(s)"
          + ("  (dry run)" if a.dry_run else ""))
    for f in r["flags"]:
        print(f"  REVIEW {f['table']}: {f['fields']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
