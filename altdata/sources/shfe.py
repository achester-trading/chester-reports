"""
SHFE weekly warehouse stocks -- copper, aluminium and zinc.

    python -m altdata.sources.shfe           # one pull, summary to stdout

AQ-3 part 1 (11 Oct 2026; the Quarterly's metals chapter, change order section
4.2: "LME + COMEX + SHFE inventories read together -- concurrent decline =
signal, divergence = relocation"). The SHFE leg is the one of the three with a
free, scriptable publication: COMEX's warehouse reports refuse scripted access
under CME's terms of use, and LME's stocks are licensed (docs/briefs/aq-3-series-
1-notes.md, "No free source").

SOURCE. The Shanghai Futures Exchange's weekly stock report, one HTML page a week,
no key, no robots.txt on the host (it serves its HTML front page at that path):
  https://www.shfe.com.cn/data/tradedata/future/stockdata/weeklystock_<YYYYMMDD>/ZH/all.html
One table: a title row carrying the report date ("2026-10-09 2026年 第(39)期"),
then one block per commodity -- a header row naming it and its unit (铜 copper,
铝 aluminium, 锌 zinc, each 单位：吨, tonnes), warehouse rows, and a grand-total row
(总计) whose cells are last week's 小计 (deliverable-grade stock) and 期货
(warranted, i.e. registered against futures), this week's two, and the changes.
The page is read BY CONTENT: the date from the title row, each commodity's block
from its header row, the total from the first 总计 after it -- never by position
on the page, so a block added or reordered does not shift the read.

STORED, instrument = COPPER | ALUMINIUM | ZINC, observed_at = the report date:
  shfe.stocks_t     this week's total deliverable-grade stock (小计), tonnes
  shfe.warrants_t   this week's warranted stock (期货), tonnes

AVAILABILITY. The page carries no Last-Modified. The report is published after
Friday's close, so available_at is the report date at 16:00 Beijing,
`reconstructed` -- the same rule-stamp as the CFETS fix, and like it a stamp the
publication calendar could correct by a day on a holiday week.

REACHABILITY. Measured from a US address on 11 Oct 2026: the host answers
intermittently -- of eight recent weeks requested two seconds apart, one page was
served and the rest reset the connection, while a single request to the
current week succeeded. Pages before roughly mid-2026 answer 404. So each run
reads only the last REFRESH_WEEKS reports, pausing between requests; a 404 is a
week with no page (a holiday Friday is tried as the Thursday before); a reset is
not retried, and after two unanswered requests the run stops (the 16:10 pull's
budget, below). A run that reads no page at all is STALE with the reason and
writes nothing.
"""

from __future__ import annotations

import datetime as dt
import html as _html
import logging
import re
import time
from typing import Optional
from zoneinfo import ZoneInfo

from .. import observations, session
from . import _publication as pub
from ._base import FetchError, http_get_response

log = logging.getLogger(__name__)

SOURCE = "shfe"
URL = ("https://www.shfe.com.cn/data/tradedata/future/stockdata/"
       "weeklystock_{ymd}/ZH/all.html")
STOCKS_KEY = "shfe.stocks_t"
WARRANTS_KEY = "shfe.warrants_t"
KEYS = [STOCKS_KEY, WARRANTS_KEY]
# The block's header word -> instrument. 铜(BC) (bonded copper, a separate
# contract) is a different header and is not read.
METALS = {"铜": "COPPER", "铝": "ALUMINIUM", "锌": "ZINC"}
REFRESH_WEEKS = 4
PAUSE_SECONDS = 2.0
PUBLISH_TIME = dt.time(16, 0)
BEIJING = ZoneInfo("Asia/Shanghai")

_TITLE_DATE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def available_at(day: str) -> str:
    local = dt.datetime.combine(dt.date.fromisoformat(day), PUBLISH_TIME,
                                tzinfo=BEIJING)
    return observations.canonical_instant(
        local.astimezone(dt.timezone.utc).isoformat())


def table_rows(page: str) -> list[list[str]]:
    """Every table row's cells as text."""
    out = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", page, re.S | re.I):
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S | re.I)
        out.append([_html.unescape(re.sub(r"<[^>]+>", "", c)).strip()
                    for c in cells])
    return out


def _num(text: str) -> Optional[float]:
    try:
        return float(str(text).replace(",", "").strip())
    except ValueError:
        return None


def rows_from_page(page: str) -> list[dict]:
    """One report's rows. Raises on a page that is not the weekly stock table:
    no dated title row, or any of the three metals missing its block or total."""
    cells = table_rows(page)
    day = None
    for r in cells[:3]:
        m = _TITLE_DATE.search(" ".join(r))
        if m:
            day = m.group(1)
            break
    if day is None:
        raise ValueError("SHFE weekly stock page has no dated title row")
    found: dict[str, tuple[float, float]] = {}
    current = None
    for r in cells:
        if len(r) <= 3 and any("单位" in c for c in r):
            current = METALS.get(r[0])
            continue
        if current and r and r[0] == "总计" and current not in found:
            # 总计, last 小计, last 期货, this 小计, this 期货, ...
            stock, warr = (_num(r[3]), _num(r[4])) if len(r) >= 5 else (None, None)
            if stock is None or warr is None:
                raise ValueError(f"SHFE {current} total row is not numeric: {r}")
            found[current] = (stock, warr)
            current = None
    missing = sorted(set(METALS.values()) - set(found))
    if missing:
        raise ValueError(f"SHFE page {day} has no total for {', '.join(missing)}")
    out = []
    for inst, (stock, warr) in found.items():
        base = {"instrument": inst, "observed_at": day,
                "available_at": available_at(day),
                "availability_kind": "reconstructed"}
        out.append(dict(base, registry_key=STOCKS_KEY, value=stock))
        out.append(dict(base, registry_key=WARRANTS_KEY, value=warr))
    return out


def report_days(today: dt.date, weeks: int = REFRESH_WEEKS) -> list[list[dt.date]]:
    """The last `weeks` report weeks, newest first: each the Friday on or before
    today, then the Thursday before it (a holiday Friday)."""
    fri = today - dt.timedelta(days=(today.weekday() - 4) % 7)
    return [[fri - dt.timedelta(weeks=w), fri - dt.timedelta(weeks=w, days=1)]
            for w in range(weeks)]


def _get(day: dt.date) -> str:
    data, _h = http_get_response(URL.format(ymd=day.strftime("%Y%m%d")),
                                 timeout=TIMEOUT_SECONDS, max_retries=1)
    return data.decode("utf-8", errors="replace")


# THE RUN'S BUDGET. This writer rides the 16:10 pull, whose unit has a deadline
# and whose overrun once killed the pass that followed it (INC-9). One try per
# page at TIMEOUT_SECONDS, and after MAX_FAILURES unanswered requests the host
# is taken as unreachable for this run: worst case well under a minute.
TIMEOUT_SECONDS = 20
MAX_FAILURES = 2


def _produce() -> list[dict]:
    rows: list[dict] = []
    errors: list[str] = []
    first = True
    for candidates in report_days(session.session_date_obj()):
        if len(errors) >= MAX_FAILURES:
            break
        for day in candidates:
            if not first:
                time.sleep(PAUSE_SECONDS)
            first = False
            try:
                rows += rows_from_page(_get(day))
                break
            except FetchError as exc:
                if "HTTP 404" in str(exc):
                    continue
                errors.append(f"{day}: {exc}")
                break
    if not rows:
        raise RuntimeError("no SHFE weekly page was read"
                           + (f" ({'; '.join(errors[:2])})" if errors else
                              " (every week answered 404)"))
    if errors:
        log.warning("shfe: %d week(s) unread, kept from earlier runs: %s",
                    len(errors), "; ".join(errors[:2]))
    return rows


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
