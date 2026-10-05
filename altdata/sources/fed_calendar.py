"""
The Federal Reserve Board's calendar: speeches, testimony and meetings, with times.

    python -m altdata.sources.fed_calendar probe

T2.2 (ruled 4 Oct 2026, item 10): the speaker feed the Weekly's day-by-day
calendar reads for "Fed speakers with times". An events source for
altdata/events_ingest.py: `calendar_events()` returns `scheduled` events and a
report, and never raises.

SOURCE. https://www.federalreserve.gov/json/calendar.json -- the Board's own
calendar, public, no key; federalreserve.gov publishes no robots.txt rule against
it. Each entry: title ("Speech - Governor Christopher J. Waller"), description,
location, type (Speeches, Testimony, FOMC Meetings, ...), month ("2026-10"), days
("8", or a range), time ("4:30 a.m."). Times are US Eastern, as the Board's
calendar page states them. An entry with no time is stored with its day only and
prints "time not stated".
"""

from __future__ import annotations

import datetime as dt
import html
import json
import logging
import re
from typing import Any, Optional

from .. import events as ev_mod
from .. import session
from ._base import http_get_bytes

log = logging.getLogger(__name__)

URL = "https://www.federalreserve.gov/json/calendar.json"
# The kinds the Weekly prints. The rest (Beige Book, statistical releases) reach
# the calendar from their own sources.
TYPES = ("Speeches", "Testimony", "FOMC Meetings")
FORWARD_DAYS = 21


def parse_time(raw: str) -> Optional[dt.time]:
    m = re.match(r"\s*(\d{1,2}):(\d{2})\s*([ap])\.?m\.?", str(raw or ""), re.I)
    if not m:
        return None
    h, mi = int(m.group(1)) % 12, int(m.group(2))
    if m.group(3).lower() == "p":
        h += 12
    return dt.time(h, mi)


def events_from_json(doc: dict, today: Optional[dt.date] = None) -> list[ev_mod.Event]:
    today = today or dt.date.today()
    out: list[ev_mod.Event] = []
    for e in doc.get("events") or []:
        if e.get("type") not in TYPES:
            continue
        try:
            y, mo = (int(x) for x in str(e.get("month") or "").split("-")[:2])
            day = int(re.match(r"\d+", str(e.get("days") or "")).group(0))
            d = dt.date(y, mo, day)
        except (ValueError, AttributeError, TypeError):
            continue
        if not (today - dt.timedelta(days=7) <= d <= today + dt.timedelta(days=FORWARD_DAYS)):
            continue
        t = parse_time(e.get("time"))
        when = (dt.datetime.combine(d, t, tzinfo=session._eastern_tz())
                .astimezone(dt.timezone.utc).isoformat() if t else
                f"{d.isoformat()}T12:00:00+00:00")
        title = html.unescape(re.sub(r"\s+", " ", str(e.get("title") or ""))).strip()
        speaker = title.split(" - ", 1)[-1].strip() if " - " in title else None
        out.append(ev_mod.Event(
            type="scheduled", observed_at=when, source="fed_calendar",
            title=f"{title} -- {html.unescape(str(e.get('description') or '')).strip()}",
            url="https://www.federalreserve.gov/newsevents/calendar.htm",
            key=f"fedcal:{d.isoformat()}:{title}:{e.get('time')}",
            payload={"kind": e.get("type"), "speaker": speaker,
                     "time_et": t.strftime("%H:%M") if t else None,
                     "time_raw": e.get("time"),
                     "location": html.unescape(str(e.get("location") or "")).strip(),
                     "date": d.isoformat()}))
    return out


def calendar_events(now: Optional[str] = None) -> tuple[list[ev_mod.Event], dict]:
    try:
        raw = http_get_bytes(URL)
        doc = json.loads(raw.decode("utf-8-sig", "replace"))
    except Exception as exc:                                    # noqa: BLE001
        return [], {"state": "failed", "reason": f"{type(exc).__name__}: {exc}"[:200]}
    evs = events_from_json(doc)
    return evs, {"state": "ok", "entries": len(doc.get("events") or []),
                 "kept": len(evs)}


if __name__ == "__main__":                                     # pragma: no cover
    evs, rep = calendar_events()
    print(rep)
    for e in evs[:12]:
        print(e.observed_at, e.title[:90], e.payload.get("time_et"))
