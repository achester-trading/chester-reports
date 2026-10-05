"""
Treasury's announced and tentative auctions, as scheduled events.

    python -m altdata.sources.upcoming_auctions

T2.2 (ruled 4 Oct 2026, item 10): the auctions in the Weekly's day-by-day
calendar. An events source for altdata/events_ingest.py; never raises.

SOURCE. Fiscal Data's upcoming_auctions dataset, public, no key:
https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/upcoming_auctions
One row per auction: security_type (Bill, Note, Bond, TIPS, FRN), security_term,
announcement, auction and issue dates. Each becomes a `scheduled` event titled
"<Type>:<Term> auction" -- the same instrument naming the auction results use
(auction.high_yield's instrument, e.g. "Note:10-Year"), so the calendar can print
the prior auction of the same security beside it. The time of day is the
calendar's standard time (config/release_calendar.yaml), not the dataset's.
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Optional

from .. import events as ev_mod
from ._base import http_get_json

log = logging.getLogger(__name__)

URL = ("https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/"
       "accounting/od/upcoming_auctions")


def events_from_rows(rows: list[dict]) -> list[ev_mod.Event]:
    out = []
    seen = set()
    for r in rows:
        day = str(r.get("auction_date") or "")[:10]
        typ, term = str(r.get("security_type") or ""), str(r.get("security_term") or "")
        if not day or not typ or not term:
            continue
        inst = f"{typ}:{term}"
        if (day, inst, r.get("cusip")) in seen:
            continue
        seen.add((day, inst, r.get("cusip")))
        out.append(ev_mod.Event(
            type="scheduled", observed_at=f"{day}T17:00:00+00:00",
            source="treasury_upcoming", title=f"{inst} auction",
            url="https://www.treasurydirect.gov/auctions/upcoming/",
            key=f"auction:{day}:{inst}:{r.get('cusip')}",
            payload={"instrument": inst, "cusip": r.get("cusip"),
                     "reopening": r.get("reopening"),
                     "offering_amt": r.get("offering_amt"),
                     "announced": r.get("announcemt_date"),
                     "record_date": r.get("record_date")}))
    return out


def calendar_events(now: Optional[str] = None) -> tuple[list[ev_mod.Event], dict]:
    since = (dt.date.today() - dt.timedelta(days=7)).isoformat()
    try:
        j = http_get_json(URL, params={"filter": f"auction_date:gte:{since}",
                                       "sort": "auction_date",
                                       "page[size]": "200"}, timeout=60)
    except Exception as exc:                                    # noqa: BLE001
        return [], {"state": "failed", "reason": f"{type(exc).__name__}: {exc}"[:200]}
    evs = events_from_rows(j.get("data") or [])
    return evs, {"state": "ok", "rows": len(j.get("data") or []), "kept": len(evs)}


if __name__ == "__main__":                                     # pragma: no cover
    evs, rep = calendar_events()
    print(rep)
    for e in evs[:12]:
        print(e.observed_at[:10], e.title)
