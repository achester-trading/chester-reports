"""
Office for National Statistics -- the UK CPI, 12-month rate, headline and core,
from the ONS's own keyless time-series CSV.

    python -m altdata.sources.ons_cpi    # one pull

The by-hand audit (st-r5-audit, 16 Oct 2026; Batch 6 item 39's gap): FRED's
OECD CPI for the UK stopped at March 2025 and Eurostat's HICP at November 2020,
so the real-yield panel's UK row was a gap. Read by
altdata/st_r5_t1_rest.py's real_yields() through config/st_r5_t1_rest.yaml.

  uk.cpi_yoy        CPI ANNUAL RATE 00: ALL ITEMS (CDID D7G7), %
  uk.cpi_core_yoy   CPI 12-month rate excluding energy, food, alcoholic
                    beverages and tobacco (CDID DKO8), %: the ONS's core

SOURCE (checked 16 Oct 2026). https://www.ons.gov.uk/generator?format=csv&uri=
/economy/inflationandpriceindices/timeseries/<cdid>/mm23, the download link on
each series page; dataset MM23, monthly from 1989. No key. www.ons.gov.uk's
robots.txt answers 404, which is no rules (RFC 9309); it is read each run and
the fetch stops on a disallow (altdata/sources/_publication.robots_allows).

READ BY CONTENT. The file opens with labelled header rows (Title, CDID, Source
dataset ID, Unit, Release date, ...) and then annual ("1989"), quarterly
("1989 Q1") and monthly ("1989 JAN") rows. The CDID row must name the series
asked for and the Unit row must be "%", or the file is refused; only the
monthly rows are read. The rates are the ONS's own, to one decimal.

AVAILABILITY. The file states its release date ("Release date","16-09-2026"):
the newest month was first published then, at 07:00 UK time (the ONS's release
time for the CPI), so every row of that file is stamped at that instant,
`observed`. On the first pull the history takes the same instant, later than
its true first publication, which is safe for an as-of join. A release date
in the future, or none, is refused. observed_at is the month's first day.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import logging
from typing import Optional
from zoneinfo import ZoneInfo

from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "ons_cpi"
SITE = "https://www.ons.gov.uk"
SERIES = {"D7G7": "uk.cpi_yoy", "DKO8": "uk.cpi_core_yoy"}
KEYS = list(SERIES.values())
MONTHS = {m: i for i, m in enumerate(
    ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV",
     "DEC"), start=1)}
RELEASE_HOUR = 7                          # 07:00 UK, the CPI's release time
LONDON = ZoneInfo("Europe/London")


def url_of(cdid: str) -> str:
    return (f"{SITE}/generator?format=csv&uri=/economy/inflationandpriceindices/"
            f"timeseries/{cdid.lower()}/mm23")


def parse(text: str, cdid: str) -> tuple[str, dict[str, float]]:
    """(release instant UTC, {YYYY-MM: rate}). Refuses a file for another
    series, in another unit, with no release date, or with no monthly row."""
    head: dict[str, str] = {}
    months: dict[str, float] = {}
    for row in csv.reader(io.StringIO(text.lstrip("﻿"))):
        if len(row) < 2:
            continue
        label, value = row[0].strip(), row[1].strip()
        parts = label.split()
        if len(parts) == 2 and parts[0].isdigit() and parts[1] in MONTHS:
            if value:
                months[f"{parts[0]}-{MONTHS[parts[1]]:02d}"] = float(value)
        elif not label[:4].isdigit():
            head[label] = value
    if head.get("CDID", "").upper() != cdid.upper():
        raise ValueError(f"the ONS file is not series {cdid} "
                         f"(CDID {head.get('CDID')!r})")
    if head.get("Unit") != "%":
        raise ValueError(f"the ONS file for {cdid} is not in % (Unit "
                         f"{head.get('Unit')!r})")
    if not months:
        raise ValueError(f"the ONS file for {cdid} carries no monthly row")
    try:
        day = dt.datetime.strptime(head.get("Release date", ""), "%d-%m-%Y")
    except ValueError:
        raise ValueError(f"the ONS file for {cdid} states no release date "
                         f"({head.get('Release date')!r})") from None
    released = day.replace(hour=RELEASE_HOUR, tzinfo=LONDON).astimezone(dt.timezone.utc)
    if released > dt.datetime.now(dt.timezone.utc):
        raise ValueError(f"the ONS file for {cdid} states a release in the future "
                         f"({head['Release date']})")
    return released.isoformat(timespec="microseconds"), months


def rows_from(files: dict[str, str]) -> list[dict]:
    """files: {cdid: csv text}."""
    rows = []
    for cdid, key in SERIES.items():
        released, months = parse(files[cdid], cdid)
        rows += [{"registry_key": key, "instrument": None, "observed_at": f"{m}-01",
                  "available_at": released, "value": v, "availability_kind": "observed"}
                 for m, v in sorted(months.items())]
    return rows


def fetch_rows() -> list[dict]:
    files = {}
    for cdid in SERIES:
        url = url_of(cdid)
        allowed, rule = pub.robots_allows(SITE, url)
        if not allowed:
            raise PermissionError(f"www.ons.gov.uk robots.txt disallows {url} ({rule})")
        body, _ = http_get_response(url, timeout=60)
        files[cdid] = body.decode("utf-8")
    return rows_from(files)


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, fetch_rows, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
