"""
Point-in-time reads for the X-3 engines and base rates: one stored series held
in memory by period with every vintage, so a walk over hundreds of events asks
the read-only store once per key rather than once per event.

    s = pit.Series(store, "yfinance.mkt_spy")
    s.at("2026-10-14", cutoff)      # that period's newest vintage knowable at cutoff
    s.latest("2026-10-14")          # its newest vintage, whenever it came
    s.first_vintage("2026-09-01")   # (value, available_at) of the first vintage
    s.known(cutoff, n)              # the last n periods knowable at cutoff

The decision clock is the lab's: a nightly loop at config/alpha_rules.yaml's
decision time (17:40 ET) on a session day. nightly_after() is the first such
instant at or after a row became knowable, so a backtest never trades on a
figure before the loop that could have read it.
"""

from __future__ import annotations

import datetime as dt
from typing import Optional

from altdata import observations, session


def canon(ts: str) -> str:
    return observations.canonical_instant(str(ts))


def et_date(instant: str) -> str:
    """The ET calendar date of an instant (a bare date is its own date)."""
    s = str(instant)
    if len(s) <= 10:
        return s[:10]
    from zoneinfo import ZoneInfo                               # noqa: PLC0415
    d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    if d.tzinfo is None:
        return s[:10]
    return d.astimezone(ZoneInfo("America/New_York")).date().isoformat()


def next_session(day: str, n: int = 1) -> str:
    d, k = dt.date.fromisoformat(day[:10]), 0
    while k < n:
        d += dt.timedelta(days=1)
        if session.is_trading_session(d):
            k += 1
    return d.isoformat()


def prev_session(day: str) -> str:
    d = dt.date.fromisoformat(day[:10]) - dt.timedelta(days=1)
    while not session.is_trading_session(d):
        d -= dt.timedelta(days=1)
    return d.isoformat()


def on_or_after_session(day: str) -> str:
    d = dt.date.fromisoformat(day[:10])
    while not session.is_trading_session(d):
        d += dt.timedelta(days=1)
    return d.isoformat()


def decision_instant(day: str) -> str:
    from . import rules                                         # noqa: PLC0415
    return rules.decision_instant(day, "next_open")


def nightly_after(instant: str) -> tuple[str, str]:
    """(session day, decided_at): the first nightly decision at or after the
    instant."""
    c = canon(instant)
    day = on_or_after_session(et_date(c))
    t = decision_instant(day)
    if t < c:
        day = next_session(day)
        t = decision_instant(day)
    return day, t


class Series:
    """Every vintage of one key (and instrument), by period."""

    def __init__(self, store, key: str, instrument: Optional[str] = None) -> None:
        self.key, self.instrument = key, instrument
        self.by: dict[str, list[tuple[str, float, Optional[str]]]] = {}
        if store is not None:
            for r in store.all_vintages(key, instrument):
                if r.get("value_num") is None:
                    continue
                self.by.setdefault(str(r["observed_at"])[:10], []).append(
                    (canon(r["available_at"]), float(r["value_num"]),
                     r.get("availability_kind")))
        for v in self.by.values():
            v.sort(key=lambda x: x[0])
        self.days = sorted(self.by)

    def __bool__(self) -> bool:
        return bool(self.days)

    def at(self, day: str, cutoff: str) -> Optional[float]:
        c = canon(cutoff)
        ok = [x for x in self.by.get(day, []) if x[0] <= c]
        return ok[-1][1] if ok else None

    def latest(self, day: str) -> Optional[float]:
        v = self.by.get(day)
        return v[-1][1] if v else None

    def avail(self, day: str) -> Optional[str]:
        v = self.by.get(day)
        return v[0][0] if v else None

    def first_vintage(self, day: str) -> Optional[tuple[float, str, Optional[str]]]:
        v = self.by.get(day)
        return (v[0][1], v[0][0], v[0][2]) if v else None

    def known(self, cutoff: str, n: Optional[int] = None,
              since: Optional[str] = None) -> list[tuple[str, float]]:
        c = canon(cutoff)
        out = []
        for d in self.days:
            if since and d < since:
                continue
            ok = [x for x in self.by[d] if x[0] <= c]
            if ok:
                out.append((d, ok[-1][1]))
        return out[-n:] if n else out
