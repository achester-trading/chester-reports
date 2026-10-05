#!/usr/bin/env python3
"""
Remove daily price bars that were stored before they were finished. (PB-1)

    python tools/remove_partial_bars.py --session 2026-10-05 --dry-run
    python tools/remove_partial_bars.py --session 2026-10-05

On 5 Oct 2026 the 06:45 pass wrote bars dated that day for VIX, DXY, gold, oil
and BTC -- quotes for a session that had not opened, stored as closes. The price
writer now refuses an unfinished bar (yfinance_source.bar_complete); this removes
the ones already stored. A row goes when its available_at is EARLIER than the
instant its bar was complete under the same rule: the session's close for a
session-bound symbol, the end of the UTC day for a 24-hour one. A later, complete
vintage of the same bar is kept.

ONE SESSION AT A TIME, ON PURPOSE. Earlier dates also carry rows stored before
their bar was complete -- a pre-open VIX quote most mornings, and every intraday
BTC vintage -- but for some of those dates no later, complete vintage was ever
written (an unchanged re-read is not stored), so removing them would remove the
bar. Only the session named is touched.

Operator-run, once, with the dry run first: it deletes rows from the store.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))


def complete_at(symbol: str, day: str) -> str:
    """The UTC instant the bar dated `day` became complete."""
    from altdata import session
    from altdata.sources import yfinance_source as yf
    d = dt.date.fromisoformat(day[:10])
    if symbol in yf.CONTINUOUS_SYMBOLS:
        return dt.datetime.combine(d + dt.timedelta(days=1), dt.time(0, 0),
                                   tzinfo=dt.timezone.utc).isoformat()
    close = dt.datetime.combine(d, session.close_time_et(d),
                                tzinfo=session._eastern_tz())
    return close.astimezone(dt.timezone.utc).isoformat()


def candidates(conn: sqlite3.Connection, day: str) -> list[tuple]:
    from altdata.sources import yfinance_source as yf
    out = []
    for symbol, key in yf.SYMBOLS.items():
        for suffix in ("", "_open", "_high", "_low"):
            rk = f"yfinance.{key}{suffix}"
            for rid, obs, avail, val in conn.execute(
                    "SELECT rowid, observed_at, available_at, value_num FROM "
                    "observations WHERE registry_key = ? AND "
                    "substr(observed_at, 1, 10) = ?", (rk, day)):
                if str(avail) < complete_at(symbol, str(obs)):
                    out.append((rid, rk, str(obs)[:10], str(avail), val))
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--session", required=True, help="the bar date to clean")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--db", default=None)
    a = ap.parse_args(argv)
    from altdata import observations
    db = a.db or observations.DEFAULT_DB
    conn = sqlite3.connect(db)
    try:
        rows = candidates(conn, a.session)
        for _, rk, obs, avail, val in rows:
            print(f"  {'would remove' if a.dry_run else 'removing'}  {rk:<32} "
                  f"{obs}  stored {avail[:19]}  value {val}")
        if not a.dry_run and rows:
            conn.executemany("DELETE FROM observations WHERE rowid = ?",
                             [(r[0],) for r in rows])
            conn.commit()
        print(f"{len(rows)} unfinished bar row(s) "
              f"{'found (dry run: nothing removed)' if a.dry_run else 'removed'}")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
