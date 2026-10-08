"""
AAII Sentiment Survey -- the weekly bull-bear spread of individual investors.

    python -m altdata.sources.aaii          # one pull, summary to stdout

T2.2 (ruled 4 Oct 2026, item 16): one of the Weekly's positioning-and-sentiment
gauges (W9). An external writer: KEYS and pull(run_id), STALE-not-empty on failure.

SOURCE. https://www.aaii.com/files/surveys/sentiment.xls -- the survey's own
spreadsheet. One row per weekly survey: Reported Date, Bullish, Neutral, Bearish
(fractions of respondents), the 8-week bullish average and the Bull-Bear spread.
Read with xlrd (the file is the legacy .xls format).

  aaii.bull_bear_spread   Bullish minus Bearish, in percentage points,
                          observed_at = the survey's reported date (a Thursday)

WHY IT WROTE NOTHING (T2.7, 8 Oct 2026). The 4 Oct note "no robots.txt rule
against it" was wrong: aaii.com/robots.txt carries `Disallow: /files/*` for every
user agent, and the server answers any client that names itself -- ours, or a
browser string carrying our name -- with an HTTP 403 block page. Python's
urllib.robotparser does not read `*` inside a path, which is how the rule was
missed. The box's 403 was the site refusing an automated fetch it forbids.

So the writer does not fetch a disallowed path, and does not pass for a browser
to get round the block. It reads, in order:

  1. THE OPERATOR'S FILE, when present: the spreadsheet as downloaded in a
     browser, at $AAII_SENTIMENT_FILE (default INBOX below). available_at is the
     file's modification time (ingest_instant: an upper bound, later than the
     truth, safe for an as-of join).
  2. The published URL, only while robots.txt allows it -- read each run, so
     the writer starts fetching by itself if AAII lifts the rule.
     While the site refuses robots.txt itself (a 403 to our name), the 8 Oct
     reading stands.

With neither, the writer fails with the reason and writes nothing; the feeds
check names the key STALE with that reason.
"""

from __future__ import annotations

import datetime as dt
import logging
import os
import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlsplit

from . import _publication as pub
from ._base import http_get_response, http_get_text

log = logging.getLogger(__name__)

SOURCE = "aaii"
URL = "https://www.aaii.com/files/surveys/sentiment.xls"
ROBOTS_URL = "https://www.aaii.com/robots.txt"
KEY = "aaii.bull_bear_spread"
KEYS = [KEY]
FILE_VAR = "AAII_SENTIMENT_FILE"
INBOX = "~/chester-data/inbox/aaii/sentiment.xls"
AGENT = "chester-reports"


def rows_from_xls(data: bytes, available_at: str, kind: str) -> list[dict]:
    """One row per dated survey. The header row is found by its 'Bullish' and
    'Bearish' columns rather than by position, so an added column does not shift
    the read silently."""
    import xlrd  # noqa: PLC0415
    book = xlrd.open_workbook(file_contents=data)
    return rows_from_sheet(book.sheet_by_index(0), book.datemode, available_at,
                           kind)


def rows_from_sheet(sh, datemode: int, available_at: str, kind: str) -> list[dict]:
    """rows_from_xls over an open sheet (anything with nrows and row_values)."""
    import xlrd  # noqa: PLC0415
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
            day = xlrd.xldate_as_datetime(d, datemode).date()
        except (ValueError, OverflowError):
            continue
        if day.year < 1987 or day > dt.date.today() + dt.timedelta(days=7):
            continue
        out.append({"registry_key": KEY, "instrument": None,
                    "observed_at": day.isoformat(), "available_at": available_at,
                    "value": round(100.0 * (b - e), 2),
                    "availability_kind": kind})
    return out


# ---------------------------------------------------------------------------
# robots.txt, with the wildcards urllib.robotparser ignores
# ---------------------------------------------------------------------------
def _pattern(path: str) -> re.Pattern:
    """A robots path rule as a regex: `*` any run, a trailing `$` the end."""
    end = path.endswith("$")
    body = re.escape(path[:-1] if end else path).replace(r"\*", ".*")
    return re.compile(body + ("$" if end else ""))


def robots_verdict(text: str, url: str, agent: str = AGENT) -> tuple[bool, Optional[str]]:
    """(allowed, the deciding rule) for `url` under robots.txt `text`, by the
    REP's own reading (RFC 9309): the group naming `agent`, else `*`; the
    longest matching rule wins, Allow on a tie; no matching rule allows."""
    groups: list[tuple[list[str], list[tuple[str, str]]]] = []
    agents: list[str] = []
    rules: list[tuple[str, str]] = []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        field, value = (x.strip() for x in line.split(":", 1))
        field = field.lower()
        if field == "user-agent":
            if rules:
                groups.append((agents, rules))
                agents, rules = [], []
            agents.append(value.lower())
        elif field in ("allow", "disallow") and agents:
            rules.append((field, value))
    if agents:
        groups.append((agents, rules))
    mine = [r for a, r in groups if agent.lower() in a]
    chosen = [x for r in (mine or [r for a, r in groups if "*" in a]) for x in r]
    parts = urlsplit(url)
    path = (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
    best: Optional[tuple[int, bool, str]] = None
    for field, value in chosen:
        if not value or not _pattern(value).match(path):
            continue
        cand = (len(value), field == "allow", f"{field.capitalize()}: {value}")
        if best is None or cand[:2] > best[:2]:
            best = cand
    if best is None:
        return True, None
    return best[1], best[2]


def inbox_path() -> Path:
    return Path(os.environ.get(FILE_VAR) or INBOX).expanduser()


def _from_file(p: Path) -> list[dict]:
    when = dt.datetime.fromtimestamp(p.stat().st_mtime, dt.timezone.utc)
    return rows_from_xls(p.read_bytes(), when.isoformat(timespec="microseconds"),
                         "ingest_instant")


def _produce() -> list[dict]:
    p = inbox_path()
    if p.is_file():
        return _from_file(p)
    try:
        allowed, rule = robots_verdict(http_get_text(ROBOTS_URL, timeout=30), URL)
    except Exception as exc:                                    # noqa: BLE001
        # The site answers our name with a 403 on robots.txt too. Its rule, read
        # in a browser on 8 Oct 2026, disallows the file: absent a readable
        # robots.txt saying otherwise, that reading stands.
        raise PermissionError(
            f"aaii.com refused robots.txt ({str(exc)[:60]}); its rule as last read "
            f"(8 Oct 2026, Disallow: /files/*, every user agent) forbids the file; "
            f"not fetched. Place the spreadsheet, downloaded in a browser, at {p} "
            f"(or ${FILE_VAR})") from None
    if not allowed:
        raise PermissionError(
            f"aaii.com robots.txt disallows the file ({rule}, every user agent); "
            f"not fetched. Place the spreadsheet, downloaded in a browser, at "
            f"{p} (or ${FILE_VAR})")
    data, headers = http_get_response(URL, timeout=60)
    return rows_from_xls(data, *pub.availability(headers))


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
