"""
The observation store, READ-ONLY (X-1.2).

The lab reads the store through the same point-in-time reader the reports use --
altdata.observations.ObservationStore's as_of() join, `as_of` being the store's
available_at -- and opens it so that no write is possible:

  * the connection is `file:<store>?mode=ro`, so SQLite itself refuses a write;
  * nothing on the read path runs DDL or a pragma that writes: ObservationStore's
    own __init__ (CREATE TABLE, journal_mode=WAL, the column migration) is not
    called, and the subclass refuses write() and write_many() before SQL does;
  * the bars table is read through the same connection, never BarStore, whose
    `create=True` is the feed's.

tools/validate_alpha.py holds it: the store file's sha256 is unchanged after a
full nightly run on the fixture.

A store that does not exist is not created: the open raises, and the loop
records its failure in loop_events and touches nothing else.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Optional

from altdata import observations


class ReadOnlyStoreError(PermissionError):
    """Something tried to write the observation store from the lab."""


class ReadOnlyStore(observations.ObservationStore):
    """ObservationStore's readers over a `mode=ro` connection."""

    def __init__(self, path: Optional[str | Path] = None) -> None:   # noqa: D107
        # NOT super().__init__: that creates the file's directory, runs the
        # schema and switches the journal mode -- three writes.
        self.path = Path(path or observations.DEFAULT_DB)
        if not self.path.is_file():
            raise FileNotFoundError(f"no observation store at {self.path}")
        self.conn = sqlite3.connect(f"file:{self.path.resolve().as_posix()}?mode=ro",
                                    uri=True)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA busy_timeout = 5000")
        self.conn.execute("PRAGMA query_only = ON")

    def write(self, *a: Any, **k: Any) -> int:                  # noqa: D102
        raise ReadOnlyStoreError("the Alpha Lab never writes the observation store")

    def write_many(self, *a: Any, **k: Any) -> int:             # noqa: D102
        raise ReadOnlyStoreError("the Alpha Lab never writes the observation store")

    # -- the lab's reads ------------------------------------------------------
    def value(self, key: str, as_of: str, instrument: Optional[str] = None,
              day: Optional[str] = None) -> Optional[float]:
        """The latest knowable value (for `day`'s period when given)."""
        rows = self.as_of(key, as_of, instrument)
        if day is not None:
            rows = [r for r in rows if str(r["observed_at"])[:10] == day]
        for r in reversed(rows):
            if r.get("value_num") is not None:
                return float(r["value_num"])
        return None

    def daily_bars(self, key: str, as_of: str, first: str = "",
                   last: str = "9999") -> list[dict]:
        """Daily OHLC for a store price key (`yfinance.mkt_spy` and its
        `_open`/`_high`/`_low` members), knowable at `as_of`, ascending. A day
        missing its open is not a bar: a fill there would have no price."""
        def by_day(k: str) -> dict[str, float]:
            return {str(r["observed_at"])[:10]: float(r["value_num"])
                    for r in self.as_of(k, as_of)
                    if r.get("value_num") is not None
                    and first <= str(r["observed_at"])[:10] <= last}
        close, opn = by_day(key), by_day(f"{key}_open")
        high, low = by_day(f"{key}_high"), by_day(f"{key}_low")
        vol = by_day(f"{key}_volume")
        out = []
        for d in sorted(close):
            if d not in opn:
                continue
            c, o = close[d], opn[d]
            out.append({"day": d, "open": o, "close": c,
                        "high": high.get(d, max(o, c)), "low": low.get(d, min(o, c)),
                        "volume": vol.get(d)})
        return out

    def daily_closes(self, key: str, as_of: str, first: str = "",
                     last: str = "9999", instrument: Optional[str] = None) -> list[dict]:
        """For a CLOSE-ONLY instrument (most of the basket stores no open, high
        or low): each stored close as a bar whose open, high and low are the
        close. A fill on one is at a close and an exit is checked on closes --
        the grammar's backtest reads such an instrument the same way (X-2.6)."""
        by_day: dict[str, float] = {}
        for r in self.as_of(key, as_of, instrument):
            d = str(r["observed_at"])[:10]
            if r.get("value_num") is None or not (first <= d <= last):
                continue
            by_day[d] = float(r["value_num"])     # the day's last stored value
        return [{"day": d, "open": c, "close": c, "high": c, "low": c, "volume": None}
                for d, c in sorted(by_day.items())]

    def intraday_bars(self, instrument: str, interval: str, first: str,
                      last: str, as_of: str) -> list[dict]:
        """The bars table (5-minute), read on this connection, as-of."""
        have = self.conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                                 "AND name='bars'").fetchone()
        if not have:
            return []
        cur = self.conn.execute(
            "SELECT * FROM bars WHERE instrument=? AND interval=? AND observed_at>=?"
            " AND observed_at<=? AND available_at<=? ORDER BY observed_at",
            (instrument, interval, first, last, observations.canonical_instant(as_of)))
        return [dict(r) for r in cur.fetchall()]

    def quote(self, bid_key: str, ask_key: str, instrument: Optional[str],
              as_of: str) -> Optional[dict]:
        """The latest stored bid/ask pair knowable at `as_of` (pm.bid/pm.ask for
        a prediction-market contract), or None where no quote is stored."""
        b = self.latest_as_of(bid_key, as_of, instrument)
        a = self.latest_as_of(ask_key, as_of, instrument)
        if not b or not a or b.get("value_num") is None or a.get("value_num") is None:
            return None
        if str(b["observed_at"])[:10] != str(a["observed_at"])[:10]:
            return None
        bid, ask = float(b["value_num"]), float(a["value_num"])
        if ask < bid:
            return None
        return {"bid": bid, "ask": ask, "observed_at": str(b["observed_at"]),
                "available_at": max(str(b["available_at"]), str(a["available_at"]))}

    def market_state(self, as_of: str, day: Optional[str] = None) -> Optional[dict]:
        """The stored market-state object (regime.STORE_KEY), read, never
        recomputed: the dials and the session's events for the regime key."""
        import json                                             # noqa: PLC0415
        rows = self.as_of("market_state", as_of)
        if day is not None:
            rows = [r for r in rows if str(r["observed_at"])[:10] == day]
        for r in reversed(rows):
            if r.get("value_text"):
                try:
                    return json.loads(r["value_text"])
                except ValueError:
                    return None
        return None


    def regime_key(self, as_of: str, day: str) -> str:
        """The attribution key for a day (X-1.9): the three dials' stored states
        -- macro, the volatility regime, the dealer (gamma) regime -- and whether
        the session carried a scheduled event. From the stored object only; a
        day with no object is `unknown`, never a guess."""
        obj = self.market_state(as_of, day=day)
        if not obj:
            return "unknown"
        dials = obj.get("dials") or {}

        def st(name: str) -> str:
            return str((dials.get(name) or {}).get("state") or "none")
        event = 1 if obj.get("session_events") else 0
        return f"macro={st('macro')}|vol={st('vol')}|gamma={st('gamma')}|event={event}"


def open_store(path: Optional[str | Path] = None) -> ReadOnlyStore:
    return ReadOnlyStore(path)
