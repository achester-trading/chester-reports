"""
The calendar's own events -- the ones config/release_calendar.yaml dates
(`scheduled`) or sets a rule for (`recurring`), for the Weekly's day-by-day
calendar beside the stored events (signal-triage batch 3, §5; Tranche A).

    rows(cal, monday, saturday) -> [{date, time, event, tier, consensus}]

A recurring row on a day the session calendar closes is skipped (a holiday
week's H.4.1 moves, and its move is the Board's to announce, not this file's to
guess). Nothing is fetched.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from altdata import session

WEEKDAYS = {d: i for i, d in enumerate(("Monday", "Tuesday", "Wednesday", "Thursday",
                                        "Friday", "Saturday", "Sunday"))}


def _open(d: dt.date) -> bool:
    return session.is_trading_session(d) if session.calendar_covers(d) \
        else d.weekday() < 5


def _row(d: dt.date, r: dict) -> dict:
    return {"date": d.isoformat(), "time": str(r.get("time") or "time not stated"),
            "event": str(r["label"]), "tier": int(r.get("tier") or 3),
            "consensus": str(r.get("note") or "—"),
            # The Ahead class: its tier and its channel (config/weekly_ahead.yaml).
            **({"cls": str(r["cls"])} if r.get("cls") else {})}


def rows(cal: dict, monday: Any, saturday: Any) -> list[dict]:
    """The config's events dated in [monday, saturday)."""
    mon = dt.date.fromisoformat(str(monday)[:10])
    sat = dt.date.fromisoformat(str(saturday)[:10])
    out = []
    for r in cal.get("scheduled") or []:
        d = dt.date.fromisoformat(str(r["date"])[:10])
        if mon <= d < sat:
            out.append(_row(d, r))
    for r in cal.get("recurring") or []:
        d = mon
        while d < sat:
            if "weekday" in r and d.weekday() == WEEKDAYS[r["weekday"]] and _open(d):
                out.append(_row(d, r))
            if "monthly_day" in r:
                first = d.replace(day=int(r["monthly_day"]))
                while first.weekday() >= 5:
                    first += dt.timedelta(days=1)
                if first == d:
                    out.append(_row(d, r))
            d += dt.timedelta(days=1)
    return out
