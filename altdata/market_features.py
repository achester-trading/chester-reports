"""
Calculated market features: breadth, trend and realized volatility.

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
    "calc.cyclical_over_defensive":
        "XLY/XLP -- discretionary over staples, what the tape pays for growth",
    "calc.vol_spy_realized_20d":
        f"annualised realized volatility of SPY's {VOL_WINDOW}-session log "
        f"returns, in percent",
}


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
def compute_rows(db: observations.ObservationStore,
                 as_of: Optional[str] = None,
                 first_day: Optional[str] = None) -> list[dict]:
    """Every feature, for every session the inputs can support."""
    sectors = {k: _load(db, f"yfinance.{k}", as_of) for k in yf_src.SECTOR_KEYS}
    spy = _load(db, SPY, as_of)
    rsp = _load(db, RSP, as_of)
    cyc = _load(db, CYCLICAL, as_of)
    dfn = _load(db, DEFENSIVE, as_of)
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

        if day in cyc and day in dfn and dfn[day][0]:
            emit("calc.cyclical_over_defensive", day, cyc[day][0] / dfn[day][0],
                 [(cyc[day][1], cyc[day][2]), (dfn[day][1], dfn[day][2])])

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

    for key in sorted(FEATURES):
        d = derived.derived_forms(key, a.as_of)
        print(f"  {key:36} level={d['level']}  pct={d['percentile']}  "
              f"n={d['n']}  conf={d['confidence']}")
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
