"""
Calculated features: breadth, trend, realized volatility -- and the macro
transforms the Monthly used to compute privately.

The market-state object works by taking a percentile of a member metric, so
`breadth` and `trend` need to BE metrics -- series with a history, not expressions
evaluated once at read time. This module computes them from the stored closes and
writes them back as `calc.*` observations, which makes them first-class: they have
registry entries, delta semantics, percentiles, extreme flags and a replayable
availability like anything else.

    python -m altdata.market_features compute
    python -m altdata.market_features compute --from 2021-09-20
    python -m altdata.market_features show --as-of 2026-09-18T21:30:00+00:00

-----------------------------------------------------------------------------
WHAT `breadth` IS, AND WHAT IT IS NOT
-----------------------------------------------------------------------------

It is the share of the ELEVEN SPDR SECTOR ETFs trading above their own 50-day and
200-day averages, plus the RSP/SPY ratio. It is NOT market-wide breadth, and the
registry flags it `sample: sector_etf_proxy` so nothing downstream can quietly
promote it.

The difference is not pedantry. Real breadth is an advance/decline line or a count
over ~500 constituents; eleven cap-weighted sector funds are eleven portfolios, and
in a market led by four megacaps XLK can sit above its average while most of its
own holdings sit below theirs. The proxy moves with breadth and understates
narrowness, which is exactly the direction that matters -- so it is worth having,
and worth labelling. A reader told "breadth is broad" by a sector proxy in a
narrow tape is worse off than one told nothing.

RSP/SPY is the honest half: equal weight against cap weight IS a participation
measure, and its ratio needs no constituent data.

-----------------------------------------------------------------------------
AVAILABILITY: A COMPUTED SERIES IS NEVER KNOWABLE BEFORE ITS INPUTS
-----------------------------------------------------------------------------

Every row's `available_at` is the MAXIMUM of the availabilities of the observations
it read, not the session's own close. A 200-day average of closes through Friday is
knowable when the last of those closes was, and if one input arrived late the
average arrived late with it. Getting this wrong would put a feature in the store
as knowable before the data it is made of -- a leak that the as-of join cannot
catch, because the join would be doing its job on a row that lies.

`availability_kind` follows the same rule: reconstructed if any input was
reconstructed, because a feature is only as observed as its least observed input.

-----------------------------------------------------------------------------
THE MACRO TRANSFORMS, AND WHY THEY ARE HERE RATHER THAN IN A REPORT
-----------------------------------------------------------------------------

Sahm, the year-over-year transforms, 2s10s, r-vs-g and net liquidity were
`monthly_macro/compute.py`: functions the Monthly called over the CSV store, at
read time, returning one number each with no history behind it. That made five
derived macro series the private arithmetic of one report -- so no dimension
could read them, no percentile existed for them, and a second report wanting net
liquidity would have computed its own.

They are series the OBJECT owns. Registered here they get what every other
metric has: a registry entry, delta semantics from their units, a percentile over
their own history, an extreme flag, a staleness allowance from their cadence, and
an `available_at` that cannot precede their inputs.

THE BOUNDARY AGAINST derived.py, because it is easy to put a transform on the
wrong side of it. `derived.py` computes the standard FORMS OF a metric -- its
delta at 1, 5 and 20 sessions, its percentile, its z, its staleness -- and is the
only place those are computed. This module computes a NEW METRIC from other
metrics' histories: a year-over-year rate is not the 252-session delta of CPI,
it is a series in its own right with its own distribution, and the same is true
of a 20-session realized volatility. If a transform can be expressed as one of
derived.py's forms it belongs there; if it needs its own history, it belongs
here.

THE UNITS TRAP IS THE REASON ONE OF THESE IS NOT A ONE-LINER. WALCL is in
MILLIONS while RRP and TGA are in BILLIONS, so a raw `bs - rrp - tga` returns a
number three orders of magnitude wrong that still looks like a balance sheet.
`calc.net_liquidity` normalises every leg to DOLLARS before subtracting and
carries the arithmetic in one place; `tools/validate_regime.py` group I asserts
the result is inside a declared plausible band AND that the un-normalised form
falls outside it, so the guard is shown to fire rather than assumed to.
"""

from __future__ import annotations

import datetime as dt
import logging
import math
import statistics
from typing import Any, Optional

from . import observations, session
from .sources import yfinance_source as yf_src

log = logging.getLogger(__name__)

SPY = "yfinance.mkt_spy"
RSP = "yfinance.mkt_rsp"
# Consumer discretionary over consumer staples: what the equity market is paying
# for growth, as a ratio of two funds that move on the same tape. The
# growth_vs_cyclicals contradiction row is the growth DIMENSION against this.
CYCLICAL = "yfinance.mkt_xly"
DEFENSIVE = "yfinance.mkt_xlp"
# The two volatility indices, for the term-structure PROXY. Not the futures curve --
# see the registry entry for why the distinction is kept in the name.
VIX = "yfinance.mkt_vix"
VIX3M = "yfinance.mkt_vix3m"

# The declared windows. Named here because the registry entries and
# config/market_state.yaml both refer to them by name, and three numbers in three
# files is how they stop agreeing.
MA_SHORT = 50
MA_LONG = 200
SLOPE_WINDOW = 20
VOL_WINDOW = 20
# ONE TRADING YEAR, for the distance-from-high reading. 252 rather than 200 because
# this one is about "has the index made a new high recently", and a year is the span
# a reader means by that.
HIGH_WINDOW = 252

TRADING_DAYS_YEAR = 252

# metric id -> what it means. The keys are what the state object's config names.
FEATURES = {
    "calc.breadth_sector_above_50d":
        f"share of the 11 SPDR sector ETFs above their own {MA_SHORT}-day average",
    "calc.breadth_sector_above_200d":
        f"share of the 11 SPDR sector ETFs above their own {MA_LONG}-day average",
    "calc.breadth_rsp_over_spy":
        "RSP/SPY -- equal weight over cap weight, a participation ratio",
    "calc.trend_spy_vs_50d":
        f"SPY's close against its own {MA_SHORT}-day average, in percent",
    "calc.trend_spy_vs_200d":
        f"SPY's close against its own {MA_LONG}-day average, in percent",
    "calc.trend_spy_ma20_slope":
        f"percent change in SPY's {SLOPE_WINDOW}-day average over "
        f"{SLOPE_WINDOW} sessions",
    "calc.spy_vs_252d_high":
        f"SPY's close against its own {HIGH_WINDOW}-session high, in percent "
        f"(0 at the high, negative below)",
    "calc.vix3m_over_vix":
        "VIX3M / VIX -- a PROXY for the VX futures curve's slope, not the curve",
    "calc.cyclical_over_defensive":
        "XLY/XLP -- discretionary over staples, what the tape pays for growth",
    "calc.vol_spy_realized_20d":
        f"annualised realized volatility of SPY's {VOL_WINDOW}-session log "
        f"returns, in percent",
}

# ---------------------------------------------------------------------------
# THE MACRO TRANSFORMS. Ported from monthly_macro/compute.py, which read the CSV
# store at report time; these read the observation store and leave a history.
# ---------------------------------------------------------------------------
YOY_TOLERANCE_DAYS = 45      # how far from 365 a "a year ago" observation may sit
YOY_MIN_MONTHS = 12          # how much history a first YoY reading needs
SAHM_AVG_MONTHS = 3          # the 3-month average Sahm is defined on
SAHM_LOOKBACK_MONTHS = 12    # and the trailing window its low is taken over

# key -> (upstream fred key, description). One entry per transform, so adding a
# series is a line rather than a function.
YOY_SERIES: dict[str, tuple[str, str]] = {
    "calc.yoy_cpi": ("cpi", "CPI, all items -- year-over-year, percent"),
    "calc.yoy_core_cpi": ("core_cpi", "Core CPI -- year-over-year, percent"),
    "calc.yoy_pce": ("pce", "PCE price index -- year-over-year, percent"),
    "calc.yoy_core_pce": ("core_pce", "Core PCE -- year-over-year, percent"),
    "calc.yoy_m2": ("m2", "M2 money stock -- year-over-year, percent"),
    "calc.yoy_real_gdp": ("real_gdp", "Real GDP -- year-over-year, percent. "
                                      "This is the G in r-vs-g"),
    "calc.yoy_housing_starts": ("housing_starts",
                                "Housing starts -- year-over-year, percent"),
    "calc.yoy_ahe": ("ahe_yoy",
                     "Average hourly earnings -- year-over-year, percent. The "
                     "upstream KEY is misleadingly named `ahe_yoy` and holds "
                     "CES0500000003, a LEVEL in dollars per hour; the "
                     "year-over-year is computed here"),
}

MACRO_FEATURES = {
    "calc.net_liquidity":
        "Fed balance sheet less the reverse repo facility less the Treasury "
        "General Account, in DOLLARS. Every leg normalised before subtraction",
    "calc.sahm_rule":
        f"the {SAHM_AVG_MONTHS}-month average of U-3 less the lowest "
        f"{SAHM_AVG_MONTHS}-month average of the trailing "
        f"{SAHM_LOOKBACK_MONTHS} months, in percentage points",
    "calc.yield_curve_2s10s":
        "the 10-year yield less the 2-year, in basis points",
    "calc.real_wages_yoy":
        "average hourly earnings year-over-year less CPI year-over-year, in "
        "percentage points. Negative means real wages are falling",
    "calc.r_real_10y_core_pce":
        "the 10-year yield less core PCE year-over-year -- R on the core-PCE "
        "basis, in percentage points",
    "calc.r_real_10y_cpi":
        "the 10-year yield less CPI year-over-year -- R on the CPI basis",
    "calc.r_minus_g":
        "R (core-PCE basis) less G (real GDP year-over-year), in percentage "
        "points. POSITIVE is r > g: debt compounds faster than the economy",
}
MACRO_FEATURES.update({k: v[1] for k, v in YOY_SERIES.items()})

# THE PLAUSIBLE BAND FOR NET LIQUIDITY, declared rather than asserted in a test.
# The quantity is the Fed's balance sheet net of two drains: it has run between
# roughly $3tn and $9tn across this store's history and cannot leave that range
# without either a new regime or an arithmetic error. The un-normalised
# subtraction lands near 6.9 MILLION, six orders below the floor -- which is the
# error this band exists to make impossible to ship.
NET_LIQUIDITY_BAND = (2.5e12, 1.0e13)


# ---------------------------------------------------------------------------
# Reading the inputs, availabilities included
# ---------------------------------------------------------------------------
def _load(db: observations.ObservationStore, key: str,
          as_of: Optional[str] = None) -> dict[str, tuple[float, str, Optional[str]]]:
    """day -> (value, available_at, availability_kind) for one series."""
    out: dict[str, tuple[float, str, Optional[str]]] = {}
    for r in db.as_of(key, as_of=as_of):
        v = r.get("value_num")
        if v is None:
            continue
        out[str(r["observed_at"])[:10]] = (
            float(v), str(r["available_at"]),
            r["availability_kind"] if "availability_kind" in r.keys() else None)
    return out


def _mean(xs: list[float]) -> Optional[float]:
    return statistics.fmean(xs) if xs else None


def _availability(parts: list[tuple[str, Optional[str]]]) -> tuple[str, Optional[str]]:
    """The max availability across inputs, and the weakest kind among them."""
    latest = max(a for a, _ in parts)
    kinds = {k for _, k in parts}
    # Weakest first: a feature is only as observed as its least observed input.
    for weak in ("reconstructed", "ingest_instant", "observed"):
        if weak in kinds:
            return latest, weak
    return latest, None


# ---------------------------------------------------------------------------
# The features
# ---------------------------------------------------------------------------
def _at_or_before(series: dict, day: str) -> Optional[str]:
    """The latest observation day in `series` at or before `day`.

    Needed because a monthly series is stamped on the FIRST of the month and the
    first is often not a trading day: core PCE for April sits on 2026-04-01 and
    the 10-year yield does not. Reaching BACK is not a leak -- the yield known on
    the 1st is the previous session's close, and `available_at` carries the clock
    -- while reaching forward would be one.
    """
    days = [d for d in series if d <= day]
    return max(days) if days else None


def _yoy(series: dict, day: str) -> Optional[tuple[float, list[str]]]:
    """Year-over-year percent at `day`, with the two days it used.

    The prior observation is the one CLOSEST TO 365 days back, within
    YOY_TOLERANCE_DAYS. A tolerance rather than an exact match because monthly
    series are stamped on the first and quarterly ones on the quarter's first
    day, so "a year ago" is 365 days back give or take a month's shape; and a
    tolerance rather than no check because without one a series with a hole in it
    would silently compare against whatever survived.
    """
    if day not in series:
        return None
    target = dt.date.fromisoformat(day) - dt.timedelta(days=365)
    prior = min(series, key=lambda d: abs(
        (dt.date.fromisoformat(d) - target).days))
    gap = abs((dt.date.fromisoformat(prior) - target).days)
    if gap > YOY_TOLERANCE_DAYS or prior >= day:
        return None
    base = series[prior][0]
    if not base:
        return None
    return 100.0 * (series[day][0] / base - 1.0), [prior, day]


def macro_rows(db: observations.ObservationStore,
               as_of: Optional[str] = None,
               first_day: Optional[str] = None) -> list[dict]:
    """Sahm, the YoY transforms, 2s10s, r-vs-g and net liquidity.

    Every row's availability is the maximum across the observations it read, the
    same rule the tape features use -- a year-over-year rate is knowable when the
    later of its two prints was, not when the month it is stamped with began.
    """
    rows: list[dict] = []

    def emit(key: str, day: str, value: Optional[float],
             parts: list[tuple[str, Optional[str]]]) -> None:
        if value is None or not math.isfinite(value) or not parts:
            return
        if first_day and day < first_day:
            return
        avail, kind = _availability(parts)
        rows.append({"registry_key": key, "instrument": None, "observed_at": day,
                     "available_at": avail, "value": round(value, 6),
                     "source": "calc", "availability_kind": kind})

    def load(key: str) -> dict:
        return _load(db, f"fred.{key}", as_of)

    # --- NET LIQUIDITY, and the units trap ----------------------------------
    #
    # WALCL AND WTREGEN ARE IN MILLIONS; RRPONTSYD IS IN BILLIONS. Every leg is
    # normalised to DOLLARS before the subtraction, which is the whole point of
    # the metric living in one place.
    #
    # THIS IS WHERE THE PORT EARNED ITS KEEP. compute.py -- and
    # altdata/config.py's units field, and CLAUDE.md's own Gotchas section --
    # all had TGA in billions. It is millions: 830,296 is $830bn, and divided as
    # billions it is $830 TRILLION. So `fed_net_liquidity` returned -823.6 for
    # every run it ever made, and the Monthly printed that as a liquidity figure
    # in trillions. A metric whose sign is wrong and whose magnitude is out by
    # six orders was surviving because nobody could check one report's private
    # arithmetic against anything. NET_LIQUIDITY_BAND below is what makes that
    # impossible to ship again.
    #
    # SAME-DAY ONLY, no carry-forward. All three land on Wednesdays, so the
    # intersection is the weekly series the slowest leg supports; carrying an
    # older RRP forward onto a newer WALCL would date the result to neither.
    bs, rrp, tga = load("fed_balance"), load("rrp"), load("tga")
    for day in sorted(bs):
        if day not in rrp or day not in tga:
            continue
        net = (bs[day][0] * 1e6) - (rrp[day][0] * 1e9) - (tga[day][0] * 1e6)
        emit("calc.net_liquidity", day, net,
             [(bs[day][1], bs[day][2]), (rrp[day][1], rrp[day][2]),
              (tga[day][1], tga[day][2])])

    # --- SAHM ---------------------------------------------------------------
    #
    # The published definition: the 3-month average of U-3 against the LOWEST
    # 3-MONTH AVERAGE of the trailing 12 months. compute.py took the low of the
    # raw monthly levels instead, which is never higher than the low of the
    # averages, so its reading was biased toward the 0.50 trigger. The difference
    # is reported by the reconciliation in tools/validate_regime.py rather than
    # tolerated silently.
    u3 = load("u3_rate")
    u3_days = sorted(u3)
    for i, day in enumerate(u3_days):
        need = SAHM_AVG_MONTHS + SAHM_LOOKBACK_MONTHS
        if i + 1 < need:
            continue
        window = u3_days[i + 1 - need:i + 1]

        def avg3(end: int) -> float:
            return _mean([u3[d][0] for d in window[end - SAHM_AVG_MONTHS:end]])

        now = avg3(len(window))
        prior = [avg3(e) for e in range(SAHM_AVG_MONTHS, len(window))]
        if now is None or not prior:
            continue
        emit("calc.sahm_rule", day, now - min(prior),
             [(u3[d][1], u3[d][2]) for d in window])

    # --- 2s10s --------------------------------------------------------------
    y2, y10 = load("yield_2y"), load("yield_10y")
    for day in sorted(y10):
        if day not in y2:
            continue
        emit("calc.yield_curve_2s10s", day,
             (y10[day][0] - y2[day][0]) * 100.0,
             [(y10[day][1], y10[day][2]), (y2[day][1], y2[day][2])])

    # --- THE YEAR-OVER-YEAR FAMILY -----------------------------------------
    yoy_cache: dict[str, dict[str, float]] = {}
    for key, (upstream, _why) in YOY_SERIES.items():
        series = load(upstream)
        vals: dict[str, float] = {}
        for day in sorted(series):
            got = _yoy(series, day)
            if got is None:
                continue
            value, used = got
            vals[day] = value
            emit(key, day, value,
                 [(series[d][1], series[d][2]) for d in used])
        yoy_cache[key] = vals

    # --- REAL WAGES, and R VS G --------------------------------------------
    #
    # Each of these reads two series that are already computed above, so they are
    # taken from the cache rather than recomputed -- a second YoY implementation
    # would be a second answer to the same question. Their availability is
    # reconstructed from the upstream prints, which is why the raw series are
    # reloaded here rather than carried through the cache.
    ahe, cpi = load("ahe_yoy"), load("cpi")
    for day, ahe_v in sorted(yoy_cache.get("calc.yoy_ahe", {}).items()):
        cpi_v = yoy_cache.get("calc.yoy_cpi", {}).get(day)
        if cpi_v is None:
            continue
        parts = [(ahe[day][1], ahe[day][2]), (cpi[day][1], cpi[day][2])]
        emit("calc.real_wages_yoy", day, ahe_v - cpi_v, parts)

    core_pce, gdp = load("core_pce"), load("real_gdp")
    r_core: dict[str, float] = {}
    for key, inflation_key, raw in (
            ("calc.r_real_10y_core_pce", "calc.yoy_core_pce", core_pce),
            ("calc.r_real_10y_cpi", "calc.yoy_cpi", cpi)):
        for day, infl in sorted(yoy_cache.get(inflation_key, {}).items()):
            yday = _at_or_before(y10, day)
            if yday is None:
                continue
            value = y10[yday][0] - infl
            if key == "calc.r_real_10y_core_pce":
                r_core[day] = value
            emit(key, day, value,
                 [(y10[yday][1], y10[yday][2]), (raw[day][1], raw[day][2])])

    # R MINUS G IS QUARTERLY, because G is. The r leg is taken at or before the
    # quarter's own date rather than interpolated: the real rate known at the
    # quarter's start is the one a decision at the quarter's start could use.
    for day, g in sorted(yoy_cache.get("calc.yoy_real_gdp", {}).items()):
        rday = _at_or_before(r_core, day)
        if rday is None:
            continue
        pday = _at_or_before(core_pce, rday)
        yday = _at_or_before(y10, rday)
        if pday is None or yday is None:
            continue
        emit("calc.r_minus_g", day, r_core[rday] - g,
             [(y10[yday][1], y10[yday][2]), (core_pce[pday][1], core_pce[pday][2]),
              (gdp[day][1], gdp[day][2])])

    return rows


def compute_rows(db: observations.ObservationStore,
                 as_of: Optional[str] = None,
                 first_day: Optional[str] = None) -> list[dict]:
    """Every feature, for every session the inputs can support."""
    sectors = {k: _load(db, f"yfinance.{k}", as_of) for k in yf_src.SECTOR_KEYS}
    spy = _load(db, SPY, as_of)
    rsp = _load(db, RSP, as_of)
    cyc = _load(db, CYCLICAL, as_of)
    dfn = _load(db, DEFENSIVE, as_of)
    vix = _load(db, VIX, as_of)
    vix3m = _load(db, VIX3M, as_of)
    if not spy:
        log.warning("no SPY closes in the store; no features computed")
        return []

    spy_days = sorted(spy)
    rows: list[dict] = []

    def emit(key: str, day: str, value: Optional[float],
             parts: list[tuple[str, Optional[str]]]) -> None:
        if value is None or not math.isfinite(value) or not parts:
            return
        avail, kind = _availability(parts)
        rows.append({"registry_key": key, "instrument": None, "observed_at": day,
                     "available_at": avail, "value": round(value, 6),
                     "source": "calc", "availability_kind": kind})

    for i, day in enumerate(spy_days):
        if first_day and day < first_day:
            continue

        # --- trend: SPY against its own averages, and the slope of the short one
        for window, key in ((MA_SHORT, "calc.trend_spy_vs_50d"),
                            (MA_LONG, "calc.trend_spy_vs_200d")):
            if i + 1 < window:
                continue
            hist = spy_days[i + 1 - window:i + 1]
            ma = _mean([spy[d][0] for d in hist])
            if ma:
                emit(key, day, 100.0 * (spy[day][0] / ma - 1.0),
                     [(spy[d][1], spy[d][2]) for d in hist])

        if i + 1 >= SLOPE_WINDOW * 2:
            now_hist = spy_days[i + 1 - SLOPE_WINDOW:i + 1]
            then_hist = spy_days[i + 1 - SLOPE_WINDOW * 2:i + 1 - SLOPE_WINDOW]
            ma_now = _mean([spy[d][0] for d in now_hist])
            ma_then = _mean([spy[d][0] for d in then_hist])
            if ma_now and ma_then:
                emit("calc.trend_spy_ma20_slope", day,
                     100.0 * (ma_now / ma_then - 1.0),
                     [(spy[d][1], spy[d][2]) for d in now_hist + then_hist])

        # --- DISTANCE FROM THE ONE-YEAR HIGH.
        #
        # This exists because SPY's LEVEL percentile is the wrong price leg for the
        # price-vs-breadth row: in any uptrend the level sits near the top of its
        # own five-year distribution almost every day, so the leg is close to
        # constant and the divergence it is supposed to measure barely moves. The
        # distance from the running high is not: it is ~0 at a new high and falls
        # away immediately, which is the thing "making new highs while
        # participation narrows" is actually about.
        if i + 1 >= HIGH_WINDOW:
            hist = spy_days[i + 1 - HIGH_WINDOW:i + 1]
            high = max(spy[d][0] for d in hist)
            if high:
                emit("calc.spy_vs_252d_high", day,
                     100.0 * (spy[day][0] / high - 1.0),
                     [(spy[d][1], spy[d][2]) for d in hist])

        # --- realized volatility, annualised
        if i + 1 >= VOL_WINDOW + 1:
            hist = spy_days[i - VOL_WINDOW:i + 1]
            rets = []
            for a, b in zip(hist, hist[1:]):
                pa, pb = spy[a][0], spy[b][0]
                if pa > 0 and pb > 0:
                    rets.append(math.log(pb / pa))
            if len(rets) >= 2:
                sd = statistics.stdev(rets)
                emit("calc.vol_spy_realized_20d", day,
                     100.0 * sd * math.sqrt(TRADING_DAYS_YEAR),
                     [(spy[d][1], spy[d][2]) for d in hist])

        # --- breadth: the sector proxy, and the honest ratio
        for window, key in ((MA_SHORT, "calc.breadth_sector_above_50d"),
                            (MA_LONG, "calc.breadth_sector_above_200d")):
            above, total, parts = 0, 0, []
            for skey, series in sectors.items():
                days = sorted(d for d in series if d <= day)
                if len(days) < window:
                    continue
                hist = days[-window:]
                ma = _mean([series[d][0] for d in hist])
                if not ma or days[-1] != day:
                    # ONLY A SECTOR THAT TRADED TODAY COUNTS. Carrying a stale
                    # close forward would put a fund on the wrong side of its own
                    # average and quietly change the share.
                    continue
                total += 1
                if series[day][0] > ma:
                    above += 1
                parts += [(series[d][1], series[d][2]) for d in hist]
            # A PARTIAL SAMPLE IS NOT A SHARE. Eight of eleven sectors reporting
            # would make the denominator the finding, not the numerator.
            if total == len(yf_src.SECTOR_KEYS):
                emit(key, day, 100.0 * above / total, parts)

        if day in rsp and day in spy and spy[day][0]:
            emit("calc.breadth_rsp_over_spy", day, rsp[day][0] / spy[day][0],
                 [(rsp[day][1], rsp[day][2]), (spy[day][1], spy[day][2])])

        if day in vix and day in vix3m and vix[day][0]:
            emit("calc.vix3m_over_vix", day, vix3m[day][0] / vix[day][0],
                 [(vix[day][1], vix[day][2]), (vix3m[day][1], vix3m[day][2])])

        if day in cyc and day in dfn and dfn[day][0]:
            emit("calc.cyclical_over_defensive", day, cyc[day][0] / dfn[day][0],
                 [(cyc[day][1], cyc[day][2]), (dfn[day][1], dfn[day][2])])

    # ONE PASS WRITES BOTH HALVES. The macro transforms do not depend on SPY and
    # could run separately, but a second entry point would be a second thing to
    # schedule -- and the pass that already runs after every price fetch is the
    # one whose inputs have just changed.
    rows += macro_rows(db, as_of=as_of, first_day=first_day)
    return rows


def compute(as_of: Optional[str] = None, first_day: Optional[str] = None,
            store: Optional[observations.ObservationStore] = None,
            dry_run: bool = False) -> dict:
    own = store is None
    db = store or observations.ObservationStore()
    try:
        rows = compute_rows(db, as_of=as_of, first_day=first_day)
        written = 0 if dry_run else db.write_many(rows)
        by_key: dict[str, int] = {}
        for r in rows:
            by_key[r["registry_key"]] = by_key.get(r["registry_key"], 0) + 1
        return {"computed": len(rows), "written": written, "by_key": by_key,
                "dry_run": dry_run}
    finally:
        if own:
            db.close()


def _main(argv: list[str]) -> int:
    import argparse
    import json
    from . import derived
    p = argparse.ArgumentParser(description="Calculated market features.")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compute")
    c.add_argument("--as-of", default=None)
    c.add_argument("--from", dest="first", default=None)
    c.add_argument("--dry-run", action="store_true")
    sh = sub.add_parser("show")
    sh.add_argument("--as-of", default=None)
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")

    if a.cmd == "compute":
        r = compute(as_of=a.as_of, first_day=a.first, dry_run=a.dry_run)
        print(f"{r['computed']} rows computed, {r['written']} written"
              + ("  (dry run)" if r["dry_run"] else ""))
        for k in sorted(r["by_key"]):
            print(f"  {k:36} {r['by_key'][k]:>6}")
        return 0

    for key in sorted({**FEATURES, **MACRO_FEATURES}):
        d = derived.derived_forms(key, a.as_of)
        print(f"  {key:36} level={d['level']}  pct={d['percentile']}  "
              f"n={d['n']}  conf={d['confidence']}")
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
