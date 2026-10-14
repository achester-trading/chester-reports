"""
AAII Sentiment Survey -- the weekly bull-bear spread of individual investors.

    python -m altdata.sources.aaii            # one pull, summary to stdout
    python -m altdata.sources.aaii --history  # the one-time history load

T2.2 (ruled 4 Oct 2026, item 16): one of the Weekly's positioning-and-sentiment
gauges (W9). An external writer: KEYS and pull(run_id), STALE-not-empty on failure.

SOURCE. https://www.aaii.com/files/surveys/sentiment.xls -- the survey's own
spreadsheet. One row per weekly survey: Reported Date, Bullish, Neutral, Bearish
(fractions of respondents), the 8-week bullish average and the Bull-Bear spread.
As of 10 Oct 2026 AAII serves it as a CSV, `sentiment(SENTIMENT).csv`: an
address line, a two-row column header, then the data, in the same columns. The
format is detected by CONTENT, never by name: the legacy .xls's OLE2 magic bytes
go to xlrd, anything else is read as that CSV layout.

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

THE INBOX (10 Oct 2026). ~/chester-data/inbox/aaii/ holds two files:

  sentiment.csv (or sentiment.xls)  THE HISTORY, loaded once. Downloaded in a
      browser and placed by the operator, then loaded with `--history`, which
      lifts the publication write window so the whole series back to 1987 is
      written even when the store already holds some rows. Later runs re-read
      it harmlessly (an unchanged value is not a new vintage). Where both names
      are present the newer file is read.
  aaii-weekly.csv  THE WEEKLY ROW, from the chat-side scheduled task "AAII
      weekly read -- Thursday" (docs/scheduled-tasks.md), which appends one row
      a week to chester-vendor-checks/aaii/aaii-weekly.csv in the operator's
      Drive; the box's nightly sweep (scripts/rclone_sync.sh) copies that one
      file here. Header: week_ending,bullish,neutral,bearish,spread,
      source_url,retrieved_at,crosscheck.

The manual weekly drop of the spreadsheet is DISCONTINUED from 10 Oct 2026; the
weekly file replaces it.

THE WEEKLY FILE'S RULES.
  Date. week_ending is the survey's Wednesday. The history's Reported Date is
      the Thursday release, so week_ending maps to the Thursday ON OR AFTER it:
      the following day for the Wednesday the task writes, and the same day if
      the task ever writes the Thursday itself (never a week late).
  Value. Bullish minus Bearish, in percentage points, as the history computes
      it. The shares may be percents (38.5) or fractions (0.385), decided per
      row by whether the three sum to about 100 or about 1; a row that sums to
      neither is skipped with a log line. The file's `spread` is a check, not
      the value: a disagreement over 0.05pp is logged.
  Union. By Reported Date with the history; a date present in both keeps the
      history's row.
  Time. available_at is the row's own retrieved_at (UTC), and
      availability_kind is ingest_instant -- the kind this writer uses for a
      fetched value without a Last-Modified: the retrieval instant is an upper
      bound on when the number was public, safe for an as-of join.
  Cross-check. A row whose crosscheck reads "disagrees: ..." is still written;
      the flag is logged as a warning.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
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
INBOX_DIR = "~/chester-data/inbox/aaii"
INBOX = f"{INBOX_DIR}/sentiment.xls"
INBOX_NAMES = ("sentiment.csv", "sentiment.xls")
WEEKLY_VAR = "AAII_WEEKLY_FILE"
WEEKLY = f"{INBOX_DIR}/aaii-weekly.csv"
WEEKLY_HEADER = ("week_ending", "bullish", "neutral", "bearish", "spread",
                 "source_url", "retrieved_at", "crosscheck")
# The legacy .xls is an OLE2 compound file; these eight bytes open every one.
OLE2_MAGIC = bytes.fromhex("D0CF11E0A1B11AE1")
# Wide enough for the whole series (1987 on): the history load lifts the
# publication write window, which otherwise keeps a held key to 400 days.
HISTORY_WINDOW_DAYS = 365 * 60
AGENT = "chester-reports"


def rows_from_xls(data: bytes, available_at: str, kind: str) -> list[dict]:
    """One row per dated survey. The header row is found by its 'Bullish' and
    'Bearish' columns rather than by position, so an added column does not shift
    the read silently."""
    import xlrd  # noqa: PLC0415
    book = xlrd.open_workbook(file_contents=data)
    return rows_from_sheet(book.sheet_by_index(0), book.datemode, available_at,
                           kind)


def rows_from_bytes(data: bytes, available_at: str, kind: str) -> list[dict]:
    """The history file, whatever it is named: xls by its magic bytes, else CSV."""
    if data[:8] == OLE2_MAGIC:
        return rows_from_xls(data, available_at, kind)
    return rows_from_csv(data, available_at, kind)


_DATE_FORMATS = ("%m-%d-%y", "%m/%d/%y", "%m-%d-%Y", "%m/%d/%Y", "%Y-%m-%d",
                 "%b %d, %Y", "%B %d, %Y", "%d-%b-%y", "%d-%b-%Y")


def parse_date(text: str) -> Optional[dt.date]:
    """A Reported Date in AAII's text forms; None for anything else."""
    t = (text or "").strip()
    for fmt in _DATE_FORMATS:
        try:
            return dt.datetime.strptime(t, fmt).date()
        except ValueError:
            continue
    return None


def _share(text: str) -> Optional[float]:
    """A share as a fraction: '38.5%' -> 0.385, '0.385' -> 0.385."""
    t = (text or "").strip().replace(",", "")
    if not t:
        return None
    pct = t.endswith("%")
    try:
        v = float(t.rstrip("%"))
    except ValueError:
        return None
    return v / 100.0 if pct or v > 1.0 else v


def rows_from_csv(data: bytes, available_at: str, kind: str) -> list[dict]:
    """The CSV history: an address line, a two-row header, then the data. The
    header is found by its 'Bullish' and 'Bearish' cells, as in the xls, so an
    added line or column does not shift the read silently."""
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = data.decode("latin-1")
    lines = list(csv.reader(io.StringIO(text)))
    bull = bear = None
    start = 0
    for r, row in enumerate(lines[:20]):
        vals = [str(v).strip().lower() for v in row]
        if "bullish" in vals and "bearish" in vals:
            bull, bear = vals.index("bullish"), vals.index("bearish")
            start = r + 1
            break
    if bull is None:
        raise ValueError("AAII CSV has no Bullish/Bearish header row")
    out: list[dict] = []
    for row in lines[start:]:
        if len(row) <= max(bull, bear):
            continue
        day = parse_date(row[0])
        b, e = _share(row[bull]), _share(row[bear])
        if day is None or b is None or e is None:
            continue
        if day.year < 1987 or day > dt.date.today() + dt.timedelta(days=7):
            continue
        out.append({"registry_key": KEY, "instrument": None,
                    "observed_at": day.isoformat(), "available_at": available_at,
                    "value": round(100.0 * (b - e), 2),
                    "availability_kind": kind})
    return out


def reported_date(week_ending: dt.date) -> dt.date:
    """The survey's Wednesday -> the Thursday release on or after it."""
    return week_ending + dt.timedelta(days=(3 - week_ending.weekday()) % 7)


def _num(text: str) -> Optional[float]:
    try:
        return float((text or "").strip().rstrip("%"))
    except ValueError:
        return None


def rows_from_weekly(data: bytes) -> list[dict]:
    """The scheduled task's file, one row a week. See THE WEEKLY FILE'S RULES."""
    rdr = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    missing = [c for c in WEEKLY_HEADER if c not in (rdr.fieldnames or [])]
    if missing:
        raise ValueError(f"aaii-weekly.csv lacks columns {missing}")
    out: list[dict] = []
    for i, r in enumerate(rdr, start=2):
        text = (r["week_ending"] or "").strip()
        try:
            week: Optional[dt.date] = dt.date.fromisoformat(text)
        except ValueError:
            week = parse_date(text)
        b, n, e = _num(r["bullish"]), _num(r["neutral"]), _num(r["bearish"])
        if week is None or None in (b, n, e):
            log.warning("aaii-weekly.csv line %d skipped: unreadable date or shares", i)
            continue
        total = b + n + e
        scale = (100.0 if 0.9 <= total <= 1.1 else
                 1.0 if 90.0 <= total <= 110.0 else None)
        if scale is None:
            log.warning("aaii-weekly.csv line %d skipped: shares sum to %s, neither "
                        "about 1 nor about 100", i, total)
            continue
        try:
            got = dt.datetime.fromisoformat(
                (r["retrieved_at"] or "").strip().replace("Z", "+00:00"))
        except ValueError:
            log.warning("aaii-weekly.csv line %d skipped: retrieved_at %r is not "
                        "ISO 8601", i, r["retrieved_at"])
            continue
        if got.tzinfo is None:
            got = got.replace(tzinfo=dt.timezone.utc)
        value = round(scale * (b - e), 2)
        sp = _num(r["spread"])
        if sp is not None and abs(scale * sp - value) > 0.05:
            log.warning("aaii-weekly.csv %s: spread column %s disagrees with "
                        "bullish - bearish (%s pp); the shares are used",
                        week, sp, value)
        cc = (r["crosscheck"] or "").strip()
        if cc.lower().startswith("disagrees"):
            log.warning("aaii-weekly.csv %s: cross-check flag -- %s (written anyway)",
                        week, cc)
        out.append({"registry_key": KEY, "instrument": None,
                    "observed_at": reported_date(week).isoformat(),
                    "available_at": got.astimezone(dt.timezone.utc).isoformat(
                        timespec="microseconds"),
                    "value": value, "availability_kind": "ingest_instant"})
    return out


def union(history: list[dict], weekly: list[dict]) -> list[dict]:
    """By Reported Date; a date present in both keeps the history's row."""
    have = {r["observed_at"] for r in history}
    return history + [r for r in weekly if r["observed_at"] not in have]


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
    """$AAII_SENTIMENT_FILE, else the newer of the inbox's sentiment.csv and
    sentiment.xls, else the .xls name (absent; the robots path follows)."""
    if os.environ.get(FILE_VAR):
        return Path(os.environ[FILE_VAR]).expanduser()
    found = [q for q in (Path(INBOX_DIR).expanduser() / n for n in INBOX_NAMES)
             if q.is_file()]
    if found:
        return max(found, key=lambda q: q.stat().st_mtime)
    return Path(INBOX).expanduser()


def weekly_path() -> Path:
    return Path(os.environ.get(WEEKLY_VAR) or WEEKLY).expanduser()


def _from_file(p: Path) -> list[dict]:
    when = dt.datetime.fromtimestamp(p.stat().st_mtime, dt.timezone.utc)
    return rows_from_bytes(p.read_bytes(), when.isoformat(timespec="microseconds"),
                           "ingest_instant")


def _produce() -> list[dict]:
    p, w = inbox_path(), weekly_path()
    if p.is_file() or w.is_file():
        history = _from_file(p) if p.is_file() else []
        weekly = rows_from_weekly(w.read_bytes()) if w.is_file() else []
        return union(history, weekly)
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


def pull(run_id: Optional[str] = None, db=None, history: bool = False) -> dict:
    """One pull. `history` lifts the write window for the one-time load."""
    kw = {"window_days": HISTORY_WINDOW_DAYS} if history else {}
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db, **kw)


if __name__ == "__main__":
    import argparse
    import json
    ap = argparse.ArgumentParser(description="AAII bull-bear spread")
    ap.add_argument("--history", action="store_true",
                    help="the one-time history load: write the whole series from "
                         "the inbox's history file, past the 400-day write window")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(history=a.history), indent=2, sort_keys=True, default=str))
