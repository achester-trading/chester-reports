"""
MOTS (Thailand's Ministry of Tourism and Sports) -- international tourist
arrivals, monthly.

    python -m altdata.sources.mots           # one pull, summary to stdout

AQ-3 part 2 (11 Oct 2026; the Quarterly's Thailand chapter). ISOLATED:
namespace thailand, never trigger_eligible.

SOURCE. mots.go.th publishes a workbook a release, under a category a year;
robots.txt disallows /web-api/ and paths containing "api", so the chain below
reads only /news/category/ pages and /images/ files (checked 11 Oct 2026):
  /news/category/411       the tourism-statistics index: one link a year,
                           "... (Tourism Statistics <year>)"
  that year's category     links "... International Tourist Arrivals to
                           Thailand <year> ..." (2026's: 816 -> 817)
  that category            links the workbook, /images/v2022_<uuid>.xlsx (the
                           uuid changes with each release)
Every hop is found by its text, never by an id.

READ BY CONTENT. The sheet whose header row names "Nationality" and the month
abbreviations; the year groups are read from the row above it ("2026p",
"2025p"); the row whose first cell is "Grand Total" carries the arrivals. A
workbook carries the current year to date AND the prior year's same months, so
the prior year's months are re-read from it (a revision, where they differ).

  thai.tourist_arrivals   international arrivals, persons, monthly

AVAILABILITY. The workbook's Last-Modified (`observed`), else the write
instant. Each pull reads this year's release, or last year's while this year's
category is not up (January). HISTORY: the store starts with the first
release read -- this year to date and the prior year's same months. The 2008-
2025 year categories exist, but 2025's carries no arrivals sub-category
(checked 11 Oct 2026) and older workbooks are other layouts, so they are not
read (a choice for the operator, in the notes).
"""

from __future__ import annotations

import html as _html
import logging
import re
from typing import Optional
from urllib.parse import urljoin

from .. import session
from . import _publication as pub
from ._base import http_get_response, http_get_text

log = logging.getLogger(__name__)

SOURCE = "mots"
INDEX_URL = "https://www.mots.go.th/news/category/411"
KEY = "thai.tourist_arrivals"
KEYS = [KEY]
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct",
          "nov", "dec"]


def links(page: str, base: str) -> list[tuple[str, str]]:
    """(text, absolute URL) for every link on a page, text normalised."""
    out = []
    for href, body in re.findall(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', page, re.S | re.I):
        text = re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", body))).strip()
        out.append((text, urljoin(base, href)))
    return out


def year_category(index_page: str, year: int) -> Optional[str]:
    for text, url in links(index_page, INDEX_URL):
        if f"(Tourism Statistics {year})" in text and "/news/category/" in url:
            return url
    return None


def arrivals_category(year_page: str, base: str) -> Optional[str]:
    for text, url in links(year_page, base):
        if "International Tourist Arrivals" in text and "/news/category/" in url:
            return url
    return None


def workbook_link(page: str, base: str) -> Optional[str]:
    m = re.search(r'href="([^"]*/images/v2022_[^"]+\.xlsx)"', page, re.I)
    return urljoin(base, m.group(1)) if m else None


def rows_from_sheet(table: list[list], available: str, kind: str) -> list[dict]:
    """One row per (year, month) of the Grand Total line."""
    hi = next((i for i, r in enumerate(table[:15]) if r and str(r[0] or "").strip()
               .lower() == "nationality"), None)
    if hi is None or hi == 0:
        raise ValueError("no header row naming 'Nationality'")
    head = [str(c or "").strip().lower()[:3] for c in table[hi]]
    years = table[hi - 1]
    total = next((r for r in table[hi + 1:] if r and str(r[0] or "").strip().lower()
                  == "grand total"), None)
    if total is None:
        raise ValueError("no 'Grand Total' row")
    out, year = [], None
    for i, h in enumerate(head):
        y = re.match(r"^\s*((?:19|20)\d\d)", str(years[i] if i < len(years) else "") or "")
        if y:
            year = int(y.group(1))
        if str(table[hi][i] or "").strip().lower() == "nationality" and i > 0:
            break                                  # the %-change block starts
        if year is None or h not in MONTHS or i >= len(total):
            continue
        v = total[i]
        if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0:
            out.append({"registry_key": KEY, "instrument": None,
                        "observed_at": pub.month_start(year, MONTHS.index(h) + 1),
                        "available_at": available, "value": float(v),
                        "availability_kind": kind})
    if not out:
        raise ValueError("no monthly arrivals on the Grand Total row")
    return out


def _produce() -> list[dict]:
    """This year's release; last year's only when this year's chain is not up
    yet (January). The workbook carries the prior year's same months too."""
    index = http_get_text(INDEX_URL, timeout=60)
    year = session.session_date_obj().year
    for y in (year, year - 1):
        cat = year_category(index, y)
        arr = cat and arrivals_category(http_get_text(cat, timeout=60), cat)
        wb = arr and workbook_link(http_get_text(arr, timeout=60), arr)
        if not wb:
            log.info("mots: no arrivals workbook under %s's category", y)
            continue
        data, headers = http_get_response(wb, timeout=60)
        available, kind = pub.availability(headers)
        for table in pub.read_xlsx(data).values():
            try:
                return rows_from_sheet(table, available, kind)
            except ValueError:
                continue
        raise ValueError(f"no sheet of {wb} carries the Grand Total arrivals")
    raise RuntimeError("no arrivals workbook was found for this year or last")


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
