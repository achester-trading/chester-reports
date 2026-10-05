"""
AAII Sentiment Survey -- the weekly bull-bear spread of individual investors.

    python -m altdata.sources.aaii          # one pull, summary to stdout

T2.2 (ruled 4 Oct 2026, item 16): one of the Weekly's positioning-and-sentiment
gauges (W9). An external writer: KEYS and pull(run_id), STALE-not-empty on failure.

SOURCE. https://www.aaii.com/files/surveys/sentiment.xls -- the survey's own
spreadsheet, public, no key; aaii.com publishes no robots.txt rule against it
(read 4 Oct 2026). One row per weekly survey: Reported Date, Bullish, Neutral,
Bearish (fractions of respondents), the 8-week bullish average and the Bull-Bear
spread. Read with xlrd (the file is the legacy .xls format).

  aaii.bull_bear_spread   Bullish minus Bearish, in percentage points,
                          observed_at = the survey's reported date (a Thursday)

Keyed on publication (§1.4): available_at is the file's Last-Modified.
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Optional

from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "aaii"
URL = "https://www.aaii.com/files/surveys/sentiment.xls"
KEY = "aaii.bull_bear_spread"
KEYS = [KEY]


def rows_from_xls(data: bytes, available_at: str, kind: str) -> list[dict]:
    """One row per dated survey. The header row is found by its 'Bullish' and
    'Bearish' columns rather than by position, so an added column does not shift
    the read silently."""
    import xlrd  # noqa: PLC0415
    book = xlrd.open_workbook(file_contents=data)
    sh = book.sheet_by_index(0)
    bull = bear = None
    start = 0
    for r in range(min(sh.nrows, 20)):
        vals = [str(v).strip().lower() for v in sh.row_values(r)]
        if "bullish" in vals and "bearish" in vals:
            bull, bear = vals.index("bullish"), vals.index("bearish")
            start = r + 1
            break
    if bull is None:
        raise ValueError("AAII sheet has no Bullish/Bearish header row")
    out: list[dict] = []
    for r in range(start, sh.nrows):
        row = sh.row_values(r)
        d, b, e = row[0], row[bull], row[bear]
        if not isinstance(d, float) or not isinstance(b, float) or \
                not isinstance(e, float):
            continue
        try:
            day = xlrd.xldate_as_datetime(d, book.datemode).date()
        except (ValueError, OverflowError):
            continue
        if day.year < 1987 or day > dt.date.today() + dt.timedelta(days=7):
            continue
        out.append({"registry_key": KEY, "instrument": None,
                    "observed_at": day.isoformat(), "available_at": available_at,
                    "value": round(100.0 * (b - e), 2),
                    "availability_kind": kind})
    return out


def _produce() -> list[dict]:
    data, headers = http_get_response(URL, timeout=60)
    return rows_from_xls(data, *pub.availability(headers))


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
