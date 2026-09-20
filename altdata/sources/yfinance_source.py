"""
yfinance market-data fetcher.

Daily closes for a fixed basket of 28 market symbols, plus the dividend and
split events beside them. No API key: yfinance reads Yahoo Finance's public
endpoints.

Failure philosophy, unchanged: one bad symbol never kills the run. Each symbol is
fetched independently and failures collect into the summary dict, the same way
FRED's do.

-----------------------------------------------------------------------------
WHICH CLOSE, AND WHY IT IS NOT THE ADJUSTED ONE
-----------------------------------------------------------------------------

This used to call `history(auto_adjust=True)`, which returns a close adjusted for
BOTH splits and dividends. That number is the right one for a total-return study
and the wrong one for everything this system does, for two reasons:

  IT IS NOT A PRICE THAT EVER TRADED. A dividend-adjusted close for 2022 changes
  every time a dividend is paid in 2026. The whole point of the point-in-time
  store is that a row is what was knowable then; a series that silently restates
  its own history four times a year cannot support an as-of join, a percentile
  against it, or a decision replay.

  IT DISAGREES WITH EVERY OTHER PRICE IN THE REPO. The pin log records settled
  closes, the exposure engine records spot, and a decision's reference price is a
  traded level. A dividend-adjusted SPY close sits a few percent below all three
  and the gap grows with time -- so a contradiction row comparing dealer gamma to
  "the trend" would be comparing two different SPY.

So: `auto_adjust=False`, and the stored value is `Close` -- SPLIT-ADJUSTED,
DIVIDEND-UNADJUSTED. Splits are a share-count relabelling of the same claim, so
adjusting for them keeps one continuous series; dividends are cash leaving the
company, and a price that pretends otherwise is not a price.

THE EVENTS ARE STORED BESIDE IT rather than folded in, as their own series
(`..._dividend`, `..._split`), and only when non-zero. Anything wanting total
return can compute it from the three; nothing has to un-adjust a number to
recover what traded. This is also why the price series' revision_policy is
`split_only` and not `never`: a split DOES restate the history, legitimately and
rarely, and that is exactly the property that makes a reconstructed availability
defensible for these series and not for FRED's.

-----------------------------------------------------------------------------
THE PARSER IS SEPARATE FROM THE FETCH, ON PURPOSE
-----------------------------------------------------------------------------

`parse_rows()` takes plain dicts and knows nothing about yfinance or the network.
`_fetch_symbol()` turns a DataFrame into those dicts. So the column semantics --
which field is the close, that a dividend of 0.0 is not an event, that a NaN is a
missing value and not a zero -- are testable against a saved fixture with no
network, which is what tools/validate_prices.py does in CI.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Iterable, Optional

from ..store import Store

log = logging.getLogger(__name__)

PACING_SECONDS = 0.5      # be polite to Yahoo; 28 symbols ~= 15s total
LOOKBACK_PERIOD = "2y"    # the routine pull; tools/backfill_prices.py does 5y

# WHAT A CLOSE IS AVAILABLE AT, for a live pull. The close is knowable at 16:00
# ET and the job runs at 16:10, so the write instant is the honest stand-in: it
# is an upper bound on when we knew, which is what an as-of join needs. The
# backfill cannot use a write instant -- see RECONSTRUCTED_LATENCY_MINUTES.
LIVE_AVAILABILITY_KIND = "ingest_instant"

# FOR THE BACKFILL ONLY. A session's close is published at 16:00 ET; 20 minutes
# is the declared allowance for it to be fetchable. Declared here rather than
# chosen per run so every reconstructed row in the store means the same thing.
RECONSTRUCTED_LATENCY_MINUTES = 20

# symbol -> store key. 28 symbols: broad indices, 11 SPDR sectors, equal weight,
# rates/credit, commodities, dollar, international, crypto.
SYMBOLS: dict[str, str] = {
    # Broad
    "SPY": "mkt_spy",
    "QQQ": "mkt_qqq",
    "IWM": "mkt_iwm",
    "DIA": "mkt_dia",
    # EQUAL WEIGHT. Added for the breadth dimension: RSP/SPY is the cleanest
    # participation read available from daily closes alone, and its absence was
    # one of the two reasons breadth could not be computed at all.
    "RSP": "mkt_rsp",
    # The eleven SPDR sectors
    "XLK": "mkt_xlk",
    "XLF": "mkt_xlf",
    "XLE": "mkt_xle",
    "XLV": "mkt_xlv",
    "XLI": "mkt_xli",
    "XLP": "mkt_xlp",
    "XLY": "mkt_xly",
    "XLU": "mkt_xlu",
    "XLB": "mkt_xlb",
    "XLRE": "mkt_xlre",
    "XLC": "mkt_xlc",
    # Rates and credit
    "TLT": "mkt_tlt",
    "IEF": "mkt_ief",
    "SHY": "mkt_shy",
    "HYG": "mkt_hyg",
    "LQD": "mkt_lqd",
    # Commodities and the dollar
    "GLD": "mkt_gld",
    "SLV": "mkt_slv",
    "USO": "mkt_uso",
    "UUP": "mkt_uup",
    # International
    "EFA": "mkt_efa",
    "EEM": "mkt_eem",
    # Crypto
    "BTC-USD": "mkt_btc_usd",
    # THE VOLATILITY INDICES, SAME DAY. FRED's VIXCLS arrives the NEXT morning, so
    # a 16:45 object computed from it is reading yesterday's volatility -- and the
    # vol dial is a statement about today by its own definition. yfinance serves
    # both of these at the close.
    #
    # ^VIX9D and ^VVIX are also served and are deliberately NOT here: the order
    # asked for these two, and a basket that grows on its own is a basket nobody
    # reviewed.
    "^VIX": "mkt_vix",
    "^VIX3M": "mkt_vix3m",
}

# The eleven sectors, in the order the breadth reading uses them. Named here
# because it is a property of this basket, and regime's config points at it.
SECTOR_KEYS: tuple[str, ...] = (
    "mkt_xlk", "mkt_xlf", "mkt_xle", "mkt_xlv", "mkt_xli", "mkt_xlp",
    "mkt_xly", "mkt_xlu", "mkt_xlb", "mkt_xlre", "mkt_xlc",
)

DIVIDEND_SUFFIX = "_dividend"
SPLIT_SUFFIX = "_split"

# INSTRUMENTS THAT TRADE WHEN THE US EQUITY MARKET DOES NOT. Declared, because the
# alternative is a filter that either drops two thirds of a crypto series or admits
# a holiday bar for an index that does not calculate on a holiday.
#
# Bitcoin trades every day of the year, so 528 of its 1,827 bars fall on a
# non-session date and every one of them is real. Nothing else in this basket does:
# an ETF and a volatility index exist only while the exchange is open.
CONTINUOUS_SYMBOLS: frozenset[str] = frozenset({"BTC-USD"})


def is_session_date(day: str) -> bool:
    """Whether a US equity session occurred on this date.

    THE CALENDAR ONLY COVERS 2026-2027, so outside those years this falls back to
    weekdays and cannot see a holiday. That is a real limit and it is why the filter
    below is described as removing what the calendar CAN see rather than as
    guaranteeing a clean series.
    """
    from .. import session as sess
    import datetime as _dt
    d = _dt.date.fromisoformat(str(day)[:10])
    if sess.calendar_covers(d):
        return sess.is_trading_session(d)
    return d.weekday() < 5


def drop_non_session_bars(symbol: str, rows: list[tuple[str, float]]
                          ) -> tuple[list[tuple[str, float]], list[str]]:
    """Bars on dates when the instrument's market was shut. Returns (kept, dropped).

    yfinance served VIX closes on 2026-05-25 and 2026-09-07 -- Memorial Day and
    Labor Day. The index is calculated from SPX option quotes and does not exist on
    a day the options market is shut, so those bars are artefacts: a carried-forward
    value or a vendor fill. Stored, they would each become a "session" in every
    percentile, every delta lookback and every staleness count that reads the
    series.

    A continuous instrument is exempt by declaration, not by guesswork.
    """
    if symbol in CONTINUOUS_SYMBOLS:
        return rows, []
    kept, dropped = [], []
    for day, value in rows:
        if is_session_date(day):
            kept.append((day, value))
        else:
            dropped.append(day)
    return kept, dropped


def _f(v: Any) -> Optional[float]:
    """A float, or None. A NaN is MISSING, not zero."""
    if v is None or v == "":
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if f != f else f          # NaN is the only value unequal to itself


def parse_rows(rows: Iterable[dict]) -> dict:
    """Split one symbol's history into closes, dividends and splits.

    Input is plain dicts with yfinance's own column names -- Date, Close,
    Dividends, Stock Splits -- so this function is testable against a saved
    fixture and never touches the network.

    Returns {"closes": [(day, value)], "dividends": [...], "splits": [...]}.

    A DIVIDEND OF 0.0 IS NOT AN EVENT. yfinance emits zero on every ordinary day,
    and storing those would be 250 rows a year per symbol asserting that nothing
    happened -- which is both noise and, worse, indistinguishable from a real
    zero. Only non-zero events are kept.
    """
    closes: list[tuple[str, float]] = []
    dividends: list[tuple[str, float]] = []
    splits: list[tuple[str, float]] = []
    for r in rows:
        day = str(r.get("Date") or r.get("date") or "")[:10]
        if not day:
            continue
        close = _f(r.get("Close"))
        if close is not None:
            closes.append((day, close))
        div = _f(r.get("Dividends"))
        if div:                                   # non-zero and not None
            dividends.append((day, div))
        spl = _f(r.get("Stock Splits") if "Stock Splits" in r
                 else r.get("Stock_Splits"))
        if spl:
            splits.append((day, spl))
    closes.sort()
    dividends.sort()
    splits.sort()
    return {"closes": closes, "dividends": dividends, "splits": splits}


def _fetch_symbol(symbol: str, period: Optional[str] = None) -> dict:
    """One symbol's history, through the same parser the fixture test uses.

    yfinance is imported lazily by design, so a missing dependency is a
    per-symbol failure rather than an import-time one that takes the pipeline
    down with it.
    """
    import yfinance as yf  # lazy import by design

    t = yf.Ticker(symbol)
    df = t.history(period=period or LOOKBACK_PERIOD, interval="1d",
                   auto_adjust=False, actions=True)
    if df is None or df.empty:
        raise RuntimeError(f"yfinance returned no rows for {symbol}")
    rows = []
    for idx, row in df.iterrows():
        d = {"Date": idx.date().isoformat()}
        for col in ("Close", "Dividends", "Stock Splits"):
            if col in df.columns:
                d[col] = row.get(col)
        rows.append(d)
    return parse_rows(rows)


def pull(store: Optional[Store] = None, symbols: Optional[dict[str, str]] = None,
         period: Optional[str] = None, run_id: Optional[str] = None) -> dict:
    """Pull every symbol into BOTH stores.

    Returns a summary dict shaped like the FRED source's:
        {"total": int, "success": int, "failed": [(key, err), ...],
         "series": {key: {"rows": n, "last_date": iso, "last_value": v,
                          "dividends": n, "splits": n}}}

    `store` is the CSV store and stays optional: the observation store is the one
    the market-state object reads, and a CSV write failing must not cost the
    observation write. When a CSV store is passed the closes go to both.
    """
    from .. import observations as obs
    from .. import session as sess

    basket = symbols or SYMBOLS
    summary: dict = {"total": len(basket), "success": 0, "failed": [],
                     "series": {}, "availability_kind": LIVE_AVAILABILITY_KIND}

    db = obs.ObservationStore()
    try:
        for symbol, key in basket.items():
            try:
                parsed = _fetch_symbol(symbol, period=period)
                closes, dropped = drop_non_session_bars(symbol, parsed["closes"])
                if dropped:
                    log.warning("yfinance %-8s dropped %d bar(s) on non-session "
                                "dates: %s", symbol, len(dropped), dropped[-3:])
                if not closes:
                    raise RuntimeError(f"no closes parsed for {symbol}")
                now = sess.utc_iso(timespec="microseconds")
                rows = [{"registry_key": f"yfinance.{key}", "instrument": None,
                         "observed_at": d, "available_at": now, "value": v,
                         "source": "yfinance", "run_id": run_id,
                         "availability_kind": LIVE_AVAILABILITY_KIND}
                        for d, v in closes]
                for suffix, events in ((DIVIDEND_SUFFIX, parsed["dividends"]),
                                       (SPLIT_SUFFIX, parsed["splits"])):
                    rows += [{"registry_key": f"yfinance.{key}{suffix}",
                              "instrument": None, "observed_at": d,
                              "available_at": now, "value": v,
                              "source": "yfinance", "run_id": run_id,
                              "availability_kind": LIVE_AVAILABILITY_KIND}
                             for d, v in events]
                # A RE-READ IS NOT A REVISION. Without this, two pulls a day
                # give every close a fresh vintage stamped with the pull instant,
                # which supersedes the reconstructed one and makes every historical
                # recompute blind to the last two years. See
                # observations.drop_unchanged().
                fresh = obs.drop_unchanged(db, rows)
                n = db.write_many(fresh)
                unchanged = len(rows) - len(fresh)

                # The CSV copy, when asked for. Guarded for the reason the dual
                # write in store.py is guarded, only the other way round: here
                # the observation store is the one on trial no longer, and the
                # CSV is the convenience.
                if store is not None:
                    try:
                        store.write_observations(
                            key, [(d, v) for d, v in closes], source="yfinance",
                            dual_write=False)
                    except Exception as exc:      # noqa: BLE001
                        log.warning("CSV write failed for %s: %s", key, exc)

                summary["series"][key] = {
                    "rows": n, "unchanged": unchanged, "closes": len(closes),
                    "last_date": closes[-1][0], "last_value": closes[-1][1],
                    "dividends": len(parsed["dividends"]),
                    "splits": len(parsed["splits"])}
                summary["success"] += 1
                log.info("yfinance %-8s -> %s (%d new rows, %d unchanged, "
                         "last %s = %s)", symbol, key, n, unchanged,
                         closes[-1][0], closes[-1][1])
            except Exception as e:  # noqa: BLE001 -- per-symbol isolation
                summary["failed"].append((key, str(e)))
                log.warning("yfinance %-8s FAILED: %s", symbol, e)
            time.sleep(PACING_SECONDS)
    finally:
        db.close()
    return summary
