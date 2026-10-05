"""
OHLC bars for the tape set: 5-minute for the session, daily for the frames.
(docs/briefs/reporting-stack-brief-2026-10-02.md 2.3, Tranche T1)

    python -m altdata.bars pull [--session 2026-10-01] [--dry-run]
    python -m altdata.bars status [--session 2026-10-01]
    python -m altdata.bars backfill --days 60 [--dry-run]   # one-time (T2.2)

A FEED, IN THE 16:10 EOD RUN (ruled 2 Oct 2026). Reports never fetch (30.4), so
the pull is the `bars` feed in altdata/feeds.py, which chester-eod runs; the 16:45
close reads the store only. Pulled after the close, Yahoo's delay does not matter;
a final bar not yet served is retried for up to five minutes (config bars.retry_*).
THE FEED CREATES AND OWNS THE TABLE: only `BarStore(create=True)`, which the pull
opens, runs the DDL. A reader opening a store with no bars table gets no rows,
and the close prints "bars incomplete (n=0 of ...)". 6b replaces the source; the
table and its three clocks stay.

THE THREE CLOCKS. `observed_at` is the bar's own start (UTC), `available_at` the
instant the bar was fetched -- an upper bound on when this system knew it, which
is what an as-of read needs -- and `ingested_at` the write. A bar is never
knowable before it was fetched, so a replay of an old session sees only the bars
that existed then.

A TABLE OF ITS OWN, not observation rows: a bar is five numbers and a volume, and
an observation is one. `bars` lives in the same database as the observations.
"""

from __future__ import annotations

import datetime as dt
import logging
import sqlite3
from pathlib import Path
from typing import Any, Iterable, Optional

import yaml

from . import observations, session

log = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "config" / "reporting_stack.yaml"

SCHEMA = """
CREATE TABLE IF NOT EXISTS bars (
    instrument   TEXT NOT NULL,      -- the tape id (spy, y10, ...)
    symbol       TEXT NOT NULL,      -- the source symbol (SPY, ^TNX, ...)
    interval     TEXT NOT NULL,      -- 5m | 1d
    observed_at  TEXT NOT NULL,      -- bar start, UTC ISO (a date for 1d)
    open REAL, high REAL, low REAL, close REAL, volume REAL,
    available_at TEXT NOT NULL,
    ingested_at  TEXT NOT NULL,
    source       TEXT NOT NULL,
    UNIQUE (instrument, interval, observed_at)
);
CREATE INDEX IF NOT EXISTS bars_by_time ON bars (instrument, interval, observed_at);
"""

# Regular hours a 5-minute bar is counted in, ET. Equity hours unless the
# instrument says otherwise; the yield indices print 08:00-15:00.
EQUITY_HOURS = ("09:30", "16:00")
HOURS = {"y10": ("08:00", "15:00"), "y30": ("08:00", "15:00")}


def load_config(path: Optional[Path] = None) -> dict:
    with open(path or CONFIG_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def tape() -> list[dict]:
    return list(load_config().get("tape") or [])


def intraday_instruments(cfg: Optional[dict] = None) -> list[dict]:
    """The tape set plus the intraday-only instruments (T2.3: ES=F)."""
    cfg = cfg or load_config()
    return list(cfg.get("tape") or []) + list(cfg.get("intraday_extra") or [])


def full_session(instrument: str) -> bool:
    """An instrument whose counted session is the futures day, 18:00 ET the
    evening before to 17:00 ET (T2.3)."""
    return any(t["id"] == instrument and t.get("session") == "full"
               for t in load_config().get("intraday_extra") or [])


class BarStore:
    """The bars table. `create=True` is the feed's (and a gate's seeding) only."""

    def __init__(self, path: Optional[str] = None, create: bool = False) -> None:
        self.path = Path(path or observations.DEFAULT_DB)
        self.create = create
        if create:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA busy_timeout = 5000")
        if create:
            self.conn.execute("PRAGMA journal_mode = WAL")
            self.conn.executescript(SCHEMA)
            self.conn.commit()

    def exists(self) -> bool:
        return self.conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                                 "AND name='bars'").fetchone() is not None

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "BarStore":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def write_many(self, rows: Iterable[dict]) -> int:
        if not self.create:
            raise RuntimeError("bars are written by the eod feed only -- open "
                               "BarStore(create=True)")
        now = session.utc_iso()
        cur = self.conn.executemany(
            "INSERT OR IGNORE INTO bars (instrument, symbol, interval, observed_at,"
            " open, high, low, close, volume, available_at, ingested_at, source)"
            " VALUES (:instrument, :symbol, :interval, :observed_at, :open, :high,"
            " :low, :close, :volume, :available_at, :ingested_at, :source)",
            [{"volume": None, "source": "yfinance", "ingested_at": now, **r}
             for r in rows])
        self.conn.commit()
        return cur.rowcount

    def read(self, instrument: str, interval: str, first: str = "",
             last: str = "9999", as_of: Optional[str] = None) -> list[dict]:
        """Bars in [first, last] by observed_at, knowable at `as_of`."""
        if not self.exists():
            return []
        q = ("SELECT * FROM bars WHERE instrument = ? AND interval = ?"
             " AND observed_at >= ? AND observed_at <= ?")
        args: list[Any] = [instrument, interval, first, last]
        if as_of:
            q += " AND available_at <= ?"
            args.append(as_of)
        return [dict(r) for r in self.conn.execute(q + " ORDER BY observed_at", args)]


# ---------------------------------------------------------------------------
# The session window and the completeness rule
# ---------------------------------------------------------------------------
def session_window(instrument: str, day: str) -> tuple[str, str, int]:
    """(first, last) UTC instants of the counted hours, and the expected bars."""
    d = dt.date.fromisoformat(day)
    if full_session(instrument):
        # THE FUTURES DAY (T2.3): 18:00 ET on the previous calendar day to 17:00
        # ET on the session's date -- 23 hours, 276 five-minute bars.
        tz = session._eastern_tz()
        a = dt.datetime.combine(d - dt.timedelta(days=1), dt.time(18, 0), tzinfo=tz)
        b = dt.datetime.combine(d, dt.time(17, 0), tzinfo=tz)
        n = int((b - a).total_seconds() // 300)
        fmt = lambda x: x.astimezone(dt.timezone.utc).isoformat()   # noqa: E731
        return fmt(a), fmt(b - dt.timedelta(minutes=5)), n
    start_s, end_s = HOURS.get(instrument, EQUITY_HOURS)
    if instrument not in HOURS and session.calendar_covers(d) and \
            session.is_early_close(d):
        end_s = "13:00"
    tz = session._eastern_tz()
    a = dt.datetime.combine(d, dt.time.fromisoformat(start_s), tzinfo=tz)
    b = dt.datetime.combine(d, dt.time.fromisoformat(end_s), tzinfo=tz)
    n = int((b - a).total_seconds() // 300)
    fmt = lambda x: x.astimezone(dt.timezone.utc).isoformat()   # noqa: E731
    # The last counted bar STARTS five minutes before the close.
    return fmt(a), fmt(b - dt.timedelta(minutes=5)), n


def intraday(store: BarStore, instrument: str, day: str,
             as_of: Optional[str] = None, complete_share: float = 0.9) -> dict:
    """The session's counted 5-minute bars and the completeness verdict."""
    first, last, expected = session_window(instrument, day)
    rows = store.read(instrument, "5m", first, last, as_of)
    share = (len(rows) / expected) if expected else 0.0
    return {"bars": rows, "n": len(rows), "expected": expected,
            "complete": share >= complete_share,
            "reason": (None if share >= complete_share else
                       f"bars incomplete (n={len(rows)} of {expected})")}




# ---------------------------------------------------------------------------
# The pull
# ---------------------------------------------------------------------------
def _frame_rows(df, instrument: str, symbol: str, interval: str,
                fetched_at: str) -> list[dict]:
    out = []
    for idx, r in df.iterrows():
        try:
            o, h, l, c = (float(r["Open"]), float(r["High"]), float(r["Low"]),
                          float(r["Close"]))
        except (TypeError, ValueError, KeyError):
            continue
        if any(x != x for x in (o, h, l, c)):          # NaN
            continue
        if interval == "1d":
            when = idx.date().isoformat()
        else:
            when = idx.tz_convert("UTC").isoformat() if idx.tzinfo else \
                idx.tz_localize("UTC").isoformat()
        v = r.get("Volume")
        out.append({"instrument": instrument, "symbol": symbol, "interval": interval,
                    "observed_at": when, "open": o, "high": h, "low": l,
                    "close": c, "volume": None if v is None or v != v else float(v),
                    "available_at": fetched_at})
    return out


def _final_bar_present(rows: list[dict], instrument: str, day: str) -> bool:
    _, last, _ = session_window(instrument, day)
    return any(r["observed_at"] >= last for r in rows)


def pull(day: Optional[str] = None, store: Optional[BarStore] = None,
         dry_run: bool = False, fetcher=None, sleep=None, clock=None) -> dict:
    """5-minute bars for `day` and recent daily bars, for every tape instrument.

    Never raises: a symbol that fails is reported and the rest are pulled. An
    instrument whose FINAL counted bar is not yet served is fetched again every
    `retry_interval_seconds` until `retry_seconds` have passed since the pull
    began; what is stored is the last fetch, short or not. `fetcher(symbol,
    **kw)`, `sleep` and `clock` are injectable (the gate passes fixtures).
    """
    import time as _time                                        # noqa: PLC0415
    sleep = sleep or _time.sleep
    clock = clock or _time.monotonic
    day = day or session.last_trading_session().isoformat()
    cfg = load_config()
    bcfg = cfg.get("bars") or {}
    retry_s = float(bcfg.get("retry_seconds", 300))
    every_s = float(bcfg.get("retry_interval_seconds", 30))
    started = clock()
    if fetcher is None:
        import yfinance as yf                                   # noqa: PLC0415

        def fetcher(symbol, **kw):
            return yf.Ticker(symbol).history(auto_adjust=False, **kw)
    own = store is None
    st = store or BarStore(create=True)
    report: dict[str, Any] = {"session": day, "instruments": {}}
    try:
        d = dt.date.fromisoformat(day)
        for t in intraday_instruments(cfg):
            iid, sym = t["id"], t["bars"]
            got: dict[str, Any] = {}
            try:
                attempts = 0
                while True:
                    attempts += 1
                    fetched = session.utc_iso()
                    full = t.get("session") == "full"
                    intra = fetcher(sym, start=(d - dt.timedelta(days=1 if full else 0)
                                                ).isoformat(),
                                    end=(d + dt.timedelta(days=1)).isoformat(),
                                    interval="5m", prepost=False)
                    rows = _frame_rows(intra, iid, sym, "5m", fetched)
                    if (_final_bar_present(rows, iid, day)
                            or clock() - started + every_s > retry_s):
                        break
                    sleep(every_s)
                # INTRADAY ONLY (T2.1, 4 Oct 2026): the session's 5-minute bars.
                # Daily frames read the price feed's daily OHLC in the store.
                got = {"5m": len(rows), "attempts": attempts,
                       "final_bar": _final_bar_present(rows, iid, day)}
                if not dry_run:
                    got["written"] = st.write_many(rows)
            except Exception as exc:                            # noqa: BLE001
                got = {"error": f"{type(exc).__name__}: {exc}"[:200]}
            report["instruments"][iid] = got
        return report
    finally:
        if own:
            st.close()


def backfill(days: int = 60, store: Optional[BarStore] = None,
             dry_run: bool = False, fetcher=None) -> dict:
    """ONE-TIME: the last `days` calendar days of 5-minute bars for every tape
    instrument (T2.2, 4 Oct 2026: W7 needs ten sessions of 65-minute bars, built
    from the 5-minute table). Yahoo serves 5-minute bars for the last 60 days
    only. One request per symbol; INSERT OR IGNORE, so a re-run and the nightly
    pull never duplicate a bar. available_at is the fetch instant -- a backfilled
    bar was not knowable before it was fetched, so an as-of read of an earlier
    session will not see it, which is the honest answer."""
    if fetcher is None:
        import yfinance as yf                                   # noqa: PLC0415

        def fetcher(symbol, **kw):
            return yf.Ticker(symbol).history(auto_adjust=False, **kw)
    own = store is None and not dry_run
    st = store or (BarStore(create=True) if not dry_run else None)
    report: dict[str, Any] = {"days": days, "dry_run": dry_run, "instruments": {}}
    try:
        for t in intraday_instruments():
            iid, sym = t["id"], t["bars"]
            try:
                fetched = session.utc_iso()
                df = fetcher(sym, period=f"{int(days)}d", interval="5m",
                             prepost=False)
                rows = _frame_rows(df, iid, sym, "5m", fetched)
                got: dict[str, Any] = {"bars": len(rows),
                                       "first": rows[0]["observed_at"] if rows else None,
                                       "last": rows[-1]["observed_at"] if rows else None}
                if not dry_run:
                    got["written"] = st.write_many(rows)
            except Exception as exc:                            # noqa: BLE001
                got = {"error": f"{type(exc).__name__}: {exc}"[:200]}
            report["instruments"][iid] = got
        return report
    finally:
        if own and st is not None:
            st.close()


def _main(argv: list[str]) -> int:
    import argparse
    import json
    p = argparse.ArgumentParser(description="Tape-set bars.")
    sub = p.add_subparsers(dest="cmd", required=True)
    for c in ("pull", "status"):
        s = sub.add_parser(c)
        s.add_argument("--session", default=None)
        s.add_argument("--dry-run", action="store_true")
    bf = sub.add_parser("backfill", help="one-time: the last N days of 5-minute "
                                         "bars for the tape set (Yahoo serves 60)")
    bf.add_argument("--days", type=int, default=60)
    bf.add_argument("--dry-run", action="store_true")
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO)
    if a.cmd == "backfill":
        print(json.dumps(backfill(a.days, dry_run=a.dry_run), indent=2))
        return 0
    day = a.session or session.last_trading_session().isoformat()
    if a.cmd == "pull":
        print(json.dumps(pull(day, dry_run=a.dry_run), indent=2))
        return 0
    with BarStore() as st:
        if not st.exists():
            print("no bars table -- the eod feed has not run against this store")
            return 1
        for t in tape():
            i = intraday(st, t["id"], day)
            print(f"{t['id']:<5} 5m {i['n']}/{i['expected']} "
                  f"{'complete' if i['complete'] else i['reason']}  "
                  )
    return 0


if __name__ == "__main__":                                      # pragma: no cover
    import sys
    raise SystemExit(_main(sys.argv[1:]))
