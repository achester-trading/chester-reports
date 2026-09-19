"""
The 06:45 ET overnight fetch — the only thing in the morning chain that opens a
socket.

REPORTS NEVER FETCH (30.4), so the split is the same one the close run uses: the
EOD pass computes at 16:10 and the 16:45 report reads the store. Here the fetch
runs at 06:45 and the 07:00 render reads the store. Fifteen minutes is enough for
a slow Yahoo response and short enough that the numbers are still the morning's.
A render that fetched would fail for transport reasons and report them as market
facts.

WHAT IT WRITES, AND WHY THE PRIOR SETTLEMENT IS PART OF IT
----------------------------------------------------------
Per symbol, three rows: the current level, the prior US settlement, and the
change between them. The change is stored rather than derived at render time
because the render reads ONLY the store and must not compute: a number in the
report has to be a number in the payload, which is the same rule D3's numeral
audit will enforce on prose. Deriving it in the renderer would put arithmetic
downstream of the audit boundary.

"Prior US settlement" is the 16:00 ET close of the previous *US* session, not
the previous calendar day and not the instrument's own last close. For ^N225 the
previous close is a Tokyo close hours old; comparing this morning's level to it
would measure a different interval per instrument and the overnight block would
be silently comparing apples to clocks.

THE ATTRIBUTION IS A FIRST PASS AND SAYS SO
-------------------------------------------
The overnight move is split across three windows, in ET, from 5-minute bars:

    tokyo   19:00 -> 03:00     Tokyo cash session, 09:00-15:00 JST
    europe  03:00 -> 06:45     London open onward
    other   the remainder      the 18:00 reopen, and anything between windows

It is a FIRST PASS because a window is not a cause. A move inside the Tokyo
window may be a US headline that landed at 21:00 ET, and the windows overlap
real events at their edges. The block is labelled accordingly and rights are
Backdrop context only: per 31.3(a) an attribution line may not generate a Book C
setup. What it is good for is the question the 07:00 reader actually has --
"where did this happen while I was asleep" -- which a single gap number cannot
answer.

Bars, not ticks. Yahoo serves 5-minute intraday for recent sessions; a missing
window yields no row rather than a zero, because "no bars" and "no move" are
different facts and a zero would assert the second.

    python -m altdata.sources.overnight              # fetch and write
    python -m altdata.sources.overnight --dry-run    # fetch, write nothing
"""

from __future__ import annotations

import argparse
import datetime as dt
import logging
import sys
import time
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

from altdata import observations, session  # noqa: E402

log = logging.getLogger("altdata.overnight")

ET = ZoneInfo("America/New_York")
SOURCE = "yfinance"
PACING_SECONDS = 0.4

# symbol -> registry slug. Ten instruments: the two US index futures the session
# is read from, volatility, the dollar, the long rate, the yen, the three cash
# indices whose sessions precede New York, and crypto as the one market that
# never closed.
SYMBOLS: dict[str, str] = {
    "ES=F":        "es",
    "NQ=F":        "nq",
    "^VIX":        "vix",
    "DX-Y.NYB":    "dxy",
    "^TNX":        "tnx",
    "JPY=X":       "usdjpy",
    "^N225":       "n225",
    "^STOXX50E":   "sx5e",
    "^FTSE":       "ftse",
    "BTC-USD":     "btcusd",
}

# The instruments that trade continuously through all three windows, and are
# therefore the only ones an attribution can be computed for. A cash index is
# closed during two of the three windows; splitting its move across them would
# be arithmetic on hours when it was not trading.
CONTINUOUS = ("ES=F", "NQ=F")

# Window edges in ET, as (name, start_hour, end_hour). tokyo wraps midnight.
WINDOWS = (("tokyo", 19, 3), ("europe", 3, 7))


def registry_key(slug: str, field: str) -> str:
    return f"overnight.{slug}_{field}"


# THE REGISTRY READS THESE TWO LISTS RATHER THAN ENUMERATING 46 KEYS BY HAND.
# metrics_registry.yaml declares two bulk blocks pointing here, so the keys this
# module can write and the keys the registry knows about are one list. A symbol
# added to SYMBOLS therefore fails check_registry.py on the member count until
# the block's expected_members is updated, which is the intended friction.
#
# Split by unit and not by symbol: a level, a settlement and a point change are
# all prices in the instrument's own quote, while the percent change is not, and
# one block cannot declare two units.
PRICE_FIELDS = ("last", "prior_settle", "chg")
PERCENT_FIELDS = ("chg_pct",)
ATTRIB_FIELDS = tuple(f"attrib_{n}" for n, _, _ in WINDOWS) + ("attrib_other",)

PRICE_KEYS = (
    [registry_key(slug, f) for slug in SYMBOLS.values() for f in PRICE_FIELDS]
    + [registry_key(SYMBOLS[sym], f)
       for sym in CONTINUOUS for f in ATTRIB_FIELDS]
)
PERCENT_KEYS = [registry_key(slug, f)
                for slug in SYMBOLS.values() for f in PERCENT_FIELDS]


def _yf():
    """Imported lazily so the rest of the pipeline works without yfinance."""
    try:
        import yfinance  # noqa: PLC0415
    except ImportError:
        return None
    return yfinance


def prior_us_settlement(now_et: dt.datetime) -> dt.datetime:
    """16:00 ET of the previous US weekday.

    Holidays are not consulted here on purpose. The session calendar is the
    authority for whether a session happened, and duplicating its table in a
    fetcher is how two copies come to disagree; a holiday simply yields bars
    whose last value is the prior real close, which is the right answer anyway.
    """
    d = now_et.date()
    prev = d - dt.timedelta(days=1)
    while prev.weekday() >= 5:            # Sat=5, Sun=6
        prev -= dt.timedelta(days=1)
    return dt.datetime.combine(prev, dt.time(16, 0), tzinfo=ET)


def _bars(yf, symbol: str, days: int = 5):
    """5-minute bars, indexed in ET. Empty frame on any failure."""
    try:
        t = yf.Ticker(symbol)
        df = t.history(period=f"{days}d", interval="5m", auto_adjust=False)
    except Exception as e:  # noqa: BLE001 -- one bad symbol never kills the run
        log.warning("%s: bars unavailable: %s: %s", symbol, type(e).__name__, e)
        return None
    if df is None or df.empty or "Close" not in df:
        log.warning("%s: no bars returned", symbol)
        return None
    try:
        df = df.tz_convert(ET)
    except (TypeError, AttributeError):
        try:
            df = df.tz_localize("UTC").tz_convert(ET)
        except Exception:  # noqa: BLE001
            log.warning("%s: bar index carries no usable timezone", symbol)
            return None
    return df.dropna(subset=["Close"])


def _at_or_before(df, when: dt.datetime) -> Optional[tuple[dt.datetime, float]]:
    """The last bar close at or before `when`."""
    if df is None or df.empty:
        return None
    upto = df[df.index <= when]
    if upto.empty:
        return None
    return upto.index[-1].to_pydatetime(), float(upto["Close"].iloc[-1])


def attribution(df, settle_at: dt.datetime,
                now_et: dt.datetime) -> dict[str, float]:
    """Per-window point moves between the prior settlement and now.

    Returns only the windows bars were actually found for. A window with no
    bars is omitted, never zeroed: no data and no move are different claims and
    the report must not make the second on the evidence of the first.
    """
    out: dict[str, float] = {}
    if df is None or df.empty:
        return out

    edges: list[tuple[str, dt.datetime, dt.datetime]] = []
    for name, start_h, end_h in WINDOWS:
        # Anchor each window to the calendar day it ENDS on, so the Tokyo window
        # that began yesterday evening is bounded correctly this morning.
        end = now_et.replace(hour=end_h, minute=0, second=0, microsecond=0)
        start = now_et.replace(hour=start_h, minute=0, second=0, microsecond=0)
        if start >= end:                       # wrapped midnight
            start -= dt.timedelta(days=1)
        start = max(start, settle_at)
        end = min(end, now_et)
        if start < end:
            edges.append((name, start, end))

    accounted = 0.0
    for name, start, end in edges:
        a = _at_or_before(df, start)
        b = _at_or_before(df, end)
        if a is None or b is None:
            continue
        move = b[1] - a[1]
        out[name] = move
        accounted += move

    # Whatever the windows did not cover: the 18:00 reopen, gaps between
    # windows, and the minutes since the last window closed. Reported as a
    # residual rather than folded into a neighbour, so the three numbers add up
    # to the move a reader can verify against the level.
    first = _at_or_before(df, settle_at)
    last = _at_or_before(df, now_et)
    if first is not None and last is not None:
        total = last[1] - first[1]
        out["other"] = total - accounted
        out["total"] = total
    return out


def fetch(symbols: Optional[dict[str, str]] = None,
          now_et: Optional[dt.datetime] = None) -> dict:
    """Read every symbol. Returns rows ready for the store, plus a summary."""
    symbols = symbols or SYMBOLS
    now_et = now_et or dt.datetime.now(ET)
    settle_at = prior_us_settlement(now_et)
    # A live quote is knowable at the instant it is read -- there is no release
    # lag -- so available_at is the fetch instant. That is the same reasoning
    # Portfolio Truth uses, and it is why `fetched_at` and `available_at` are
    # one value here rather than two columns disagreeing by milliseconds.
    fetched_at = session.utc_iso(timespec="microseconds")

    yf = _yf()
    rows: list[dict] = []
    got: list[str] = []
    missing: list[str] = []

    if yf is None:
        log.error("yfinance is not installed; nothing fetched")
        return {"rows": [], "fetched_at": fetched_at, "got": [],
                "missing": sorted(symbols), "settle_at": settle_at.isoformat(),
                "reason": "yfinance not installed"}

    for symbol, slug in symbols.items():
        df = _bars(yf, symbol)
        last = _at_or_before(df, now_et)
        prior = _at_or_before(df, settle_at)
        if last is None:
            missing.append(symbol)
            continue
        got.append(symbol)

        def row(field: str, value, observed: dt.datetime):
            rows.append({"registry_key": registry_key(slug, field),
                         "instrument": symbol,
                         "observed_at": observed.isoformat(),
                         "available_at": fetched_at,
                         "value": value, "source": SOURCE})

        row("last", last[1], last[0])
        if prior is not None:
            row("prior_settle", prior[1], settle_at)
            row("chg", last[1] - prior[1], last[0])
            if prior[1]:
                row("chg_pct", 100.0 * (last[1] - prior[1]) / abs(prior[1]),
                    last[0])

        if symbol in CONTINUOUS and prior is not None:
            for name, move in attribution(df, settle_at, now_et).items():
                if name == "total":
                    continue
                row(f"attrib_{name}", move, last[0])

        time.sleep(PACING_SECONDS)

    return {"rows": rows, "fetched_at": fetched_at, "got": got,
            "missing": missing, "settle_at": settle_at.isoformat()}


def pull(db_path: Optional[str] = None, dry_run: bool = False,
         symbols: Optional[dict[str, str]] = None,
         now_et: Optional[dt.datetime] = None,
         run_id: Optional[str] = None) -> dict:
    """Fetch and write. Never raises: a fetch failure is a reported hole."""
    run_id = run_id or session.new_run_id("overnight")
    res = fetch(symbols, now_et)
    for r in res["rows"]:
        r["run_id"] = run_id
    written = 0
    if not dry_run and res["rows"]:
        store = observations.ObservationStore(db_path)
        try:
            written = store.write_many(res["rows"])
        finally:
            store.close()
    res.update({"run_id": run_id, "written": written,
                "observations": len(res["rows"])})
    return res


def main() -> int:
    ap = argparse.ArgumentParser(description="The 06:45 ET overnight fetch")
    ap.add_argument("--db", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    res = pull(args.db, dry_run=args.dry_run)
    print(f"overnight fetch -- run {res['run_id']}")
    print(f"  fetched at : {res['fetched_at']}")
    print(f"  vs settle  : {res['settle_at']}")
    print(f"  got        : {len(res['got'])}/{len(SYMBOLS)} symbols")
    if res["missing"]:
        print(f"  MISSING    : {', '.join(res['missing'])}")
    print(f"  observations: {res['observations']}, {res['written']} written")

    # No symbols at all is a failed fetch; some symbols is a reported hole. The
    # 07:00 render is the thing that decides what to publish from either.
    return 0 if res["got"] else 1


if __name__ == "__main__":
    sys.exit(main())
