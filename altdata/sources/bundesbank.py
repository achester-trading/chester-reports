"""
Bundesbank -- the 10-year Bund yield, daily, from the Bundesbank's open data API.

    python -m altdata.sources.bundesbank     # one pull, summary to stdout

AQ-3 part 2 (11 Oct 2026; the Quarterly's global-rates rows, change order
section 4.9): the Bund leg of calc.bund_hedged_yield and its spread
(altdata/market_features.py). The OAT and BTP are monthly, from the ECB
(altdata/sources/ecb_irs.py); the Bund is the one euro yield published daily
and free, so it is read here.

SOURCE. api.statistiken.bundesbank.de, SDMX REST, no key; robots.txt answers
404 (no rules), checked 11 Oct 2026. The series is the Bundesbank's term-structure
estimate (the Svensson method) for listed Federal securities at 10.0 years'
residual maturity, daily:
  BBSIS.D.I.ZST.ZI.EUR.S1311.B.A604.R10XX.R.A.A._Z._Z.A
It is a fitted ZERO-COUPON yield from the curve, not the on-the-run benchmark's
quoted yield -- a few basis points from the screen Bund, and labelled so in the
registry. CSV is served only to an Accept header naming it (406 otherwise).

READ BY CONTENT. The response must carry TIME_PERIOD and OBS_VALUE columns and
name this series in its BBK_ID column; another series is refused rather than
stored under this key. A non-trading day carries "." and is skipped.

  bbk.bund_10y   percent, observed_at = the trading date

AVAILABILITY. The API sends no Last-Modified, so the stamp is by rule: the
next weekday at 12:00 Frankfurt (the curve is estimated after the close and
published the following morning), `reconstructed`, and never later than the
write instant. The first pull reads the whole history (daily from August 1997);
later pulls the last REFRESH_DAYS.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import logging
from typing import Optional
from zoneinfo import ZoneInfo

from .. import observations, session
from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "bundesbank"
SERIES_ID = "BBSIS.D.I.ZST.ZI.EUR.S1311.B.A604.R10XX.R.A.A._Z._Z.A"
URL = "https://api.statistiken.bundesbank.de/rest/data/BBSIS/" + SERIES_ID.split(".", 1)[1]
ACCEPT = "application/vnd.sdmx.data+csv;version=1.0.0"
KEY = "bbk.bund_10y"
KEYS = [KEY]
FRANKFURT = ZoneInfo("Europe/Berlin")
PUBLISHED = dt.time(12, 0)
REFRESH_DAYS = 60


def available_at(day: str, now: dt.datetime) -> str:
    d = dt.date.fromisoformat(day) + dt.timedelta(days=1)
    while d.weekday() >= 5:
        d += dt.timedelta(days=1)
    t = dt.datetime.combine(d, PUBLISHED, tzinfo=FRANKFURT).astimezone(dt.timezone.utc)
    return observations.canonical_instant(min(t, now).isoformat())


def rows_from_csv(text: str, now: dt.datetime) -> list[dict]:
    """The Bundesbank's SDMX CSV (semicolon-separated, a BOM) -> rows."""
    reader = csv.reader(io.StringIO(text.lstrip("﻿")), delimiter=";")
    head = next(reader, [])
    if "TIME_PERIOD" not in head or "OBS_VALUE" not in head:
        raise ValueError("the Bundesbank response has no TIME_PERIOD/OBS_VALUE columns")
    ti, vi = head.index("TIME_PERIOD"), head.index("OBS_VALUE")
    ii = head.index("BBK_ID") if "BBK_ID" in head else None
    out = []
    for r in reader:
        if len(r) <= max(ti, vi):
            continue
        if ii is not None and r[ii] != SERIES_ID:
            raise ValueError(f"the Bundesbank response names {r[ii]}, not {SERIES_ID}")
        try:
            v = float(r[vi].replace(",", "."))
        except ValueError:
            continue                                   # "." -- no trading
        day = r[ti][:10]
        out.append({"registry_key": KEY, "instrument": None, "observed_at": day,
                    "available_at": available_at(day, now), "value": v,
                    "availability_kind": "reconstructed"})
    if not out:
        raise ValueError("no observations in the Bundesbank response")
    return out


def _start(db) -> Optional[str]:
    own = db is None
    store = db or observations.open_writer(__name__)
    try:
        held = pub.newest_observed(store, KEYS).get(KEY)
    finally:
        if own:
            store.close()
    if not held:
        return None
    return (session.session_date_obj() - dt.timedelta(days=REFRESH_DAYS)).isoformat()


def pull(run_id: Optional[str] = None, db=None) -> dict:
    def produce() -> list[dict]:
        start = _start(db)
        data, _headers = http_get_response(
            URL, params={"startPeriod": start} if start else None, timeout=90,
            headers={"Accept": ACCEPT})
        return rows_from_csv(data.decode("utf-8"),
                             dt.datetime.fromisoformat(session.utc_iso()))
    return pub.run(SOURCE, KEYS, produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
