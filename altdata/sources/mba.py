"""
MBA Weekly Mortgage Applications Survey -- the purchase index's headline
changes, weekly, from the MBA's press release.

    python -m altdata.sources.mba            # one pull

ST-R5.37a (16 Oct 2026; Batch 6 item 37, an amendment to item 36): the housing
block's weekly line, printed in the Wednesday close and the Weekly. Read by
altdata/st_r5_rates.py's mba().

LIFTED 16 Oct 2026. The ruling: WAL and the busy timeout (f98fec4) satisfy D1c
for an append-only writer in the scheduled pulls; the repo-wide write-lock helper
is a separate item, later. HELD_FOR_D1C is False and the module is on
altdata/feeds.py EXTERNAL_WRITERS, so the external pull runs it
(docs/briefs/st-r5-fixes-notes.md). The flag stays, so the hold can be put back
by one edit.

VERIFY ITEM 3, ANSWERED 16 Oct 2026 FROM THE LAPTOP (the box is the operator's
to check: docs/briefs/st-r5-rates-notes.md prints the command).
  - robots.txt at www.mba.org: the `*` group disallows /Sitefinity, /sandbox,
    /search-results and one convention schedule; the newsroom is allowed. This
    module reads it with the wildcard-aware reader (aaii.robots_verdict) on
    every pull and stops on a disallow.
  - The site answers this repo's own agent, "chester-reports/1.0" (200); it
    refuses "python-requests" (403). The module never names itself as a
    browser.
  - The newsroom (/news-and-research/newsroom) links the latest release as
    .../newsroom/news/YYYY/MM/DD/mortgage-applications-<increase|decrease>-in-
    latest-mba-weekly-survey. Older releases are not paged from the newsroom
    (?page=N returns the same list), so there is NO history to backfill here:
    the series is forward-only from the first pull.
  - THE RELEASE NEVER PRINTS THE INDEX LEVEL. It prints the seasonally
    adjusted purchase index's change on the week and the unadjusted index's
    change on the year, both in whole percent. The level (the order's ~139, the
    2023 floor ~127) is member-only. No by-hand level is kept (ruled 16 Oct
    2026): altdata/st_r5_rates.py chains a level from the weekly changes since
    the first pull instead.

  mba.purchase_sa_wow   percent change on the week, seasonally adjusted
  mba.purchase_nsa_yoy  percent change on the year, unadjusted
observed_at = the survey's week-ending date (a Friday); available_at = the
page's Last-Modified where sent, else the write instant.

READ BY PHRASE, never position: a release whose sentences do not match is
refused rather than stored half-read.
"""

from __future__ import annotations

import datetime as dt
import html
import logging
import re
from typing import Optional

from . import _publication as pub
from ._base import http_get_response, http_get_text

log = logging.getLogger(__name__)

SOURCE = "mba"
SITE = "https://www.mba.org"
ROBOTS_URL = SITE + "/robots.txt"
NEWSROOM_URL = SITE + "/news-and-research/newsroom"
AGENT = "chester-reports"
WOW_KEY = "mba.purchase_sa_wow"
YOY_KEY = "mba.purchase_nsa_yoy"
KEYS = [WOW_KEY, YOY_KEY]

HELD_FOR_D1C = False
HOLD_REASON = ("held for D1c: a new store writer waits for the repo-wide write "
               "lock (Track D precondition; TODO.md D1c)")

LINK = re.compile(r'href="((?:https://www\.mba\.org)?/news-and-research/newsroom/news/'
                  r'(\d{4})/(\d{2})/(\d{2})/mortgage-applications-[a-z0-9-]*'
                  r'weekly-survey)"', re.I)
WEEK = re.compile(r"for the week ending ([A-Z][a-z]+ \d{1,2}, \d{4})")
SA = re.compile(r"The seasonally adjusted Purchase Index (increased|decreased|"
                r"remained unchanged)(?: by)?(?: ([\d.]+) percent)?", re.I)
YOY = re.compile(r"The unadjusted Purchase Index [^.]*?was ([\d.]+) percent "
                 r"(higher|lower) than the same week one year ago", re.I)


def text_of(page: str) -> str:
    page = re.sub(r"(?s)<script.*?</script>|<style.*?</style>", " ", page)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", page)))


def latest_link(newsroom: str) -> Optional[str]:
    """The newest weekly-survey release linked from the newsroom page."""
    found = sorted({(m.group(2) + m.group(3) + m.group(4), m.group(1))
                    for m in LINK.finditer(newsroom)})
    if not found:
        return None
    url = found[-1][1]
    return url if url.startswith("http") else SITE + url


def parse_release(page: str) -> dict:
    """{week, wow, yoy} from one release. Raises ValueError when a phrase is
    missing, so a changed template is a STALE run, not a wrong number."""
    t = text_of(page)
    w, sa, yy = WEEK.search(t), SA.search(t), YOY.search(t)
    if not (w and sa and yy):
        raise ValueError("the MBA release does not carry the week, the SA purchase "
                         "change and the NSA year-on-year sentence")
    week = dt.datetime.strptime(w.group(1), "%B %d, %Y").date().isoformat()
    verb = sa.group(1).lower()
    if verb == "remained unchanged":
        wow = 0.0
    elif sa.group(2) is None:
        raise ValueError("the SA purchase sentence carries no figure")
    else:
        wow = float(sa.group(2)) * (1 if verb == "increased" else -1)
    yoy = float(yy.group(1)) * (1 if yy.group(2).lower() == "higher" else -1)
    return {"week": week, "wow": wow, "yoy": yoy}


def rows_from_release(page: str, available: str, kind: str) -> list[dict]:
    r = parse_release(page)
    return [{"registry_key": k, "instrument": None, "observed_at": r["week"],
             "available_at": available, "value": v, "availability_kind": kind}
            for k, v in ((WOW_KEY, r["wow"]), (YOY_KEY, r["yoy"]))]


def robots_ok(text: str, url: str) -> bool:
    from .aaii import robots_verdict                          # noqa: PLC0415
    ok, _rule = robots_verdict(text, url, AGENT)
    return ok


def fetch_rows() -> list[dict]:
    robots = http_get_text(ROBOTS_URL, timeout=30)
    if not robots_ok(robots, NEWSROOM_URL):
        raise PermissionError("mba.org robots.txt disallows the newsroom")
    news, _h = http_get_response(NEWSROOM_URL, timeout=60)
    url = latest_link(news.decode("utf-8", errors="replace"))
    if not url:
        raise ValueError("no weekly-survey release linked from the MBA newsroom")
    if not robots_ok(robots, url):
        raise PermissionError(f"mba.org robots.txt disallows {url}")
    page, headers = http_get_response(url, timeout=60)
    available, kind = pub.availability(headers)
    return rows_from_release(page.decode("utf-8", errors="replace"), available, kind)


def pull(run_id: Optional[str] = None, db=None) -> dict:
    # REFUSED (the feed repair of 24 Oct 2026): www.mba.org answers HTTP 403 to
    # its own robots.txt; the source registry declares it and nothing is asked.
    r = pub.refused(SOURCE, run_id)
    if r:
        return r
    if HELD_FOR_D1C:
        return {"source": SOURCE, "status": "HELD", "written": 0,
                "reason": HOLD_REASON, "keys": KEYS}
    return pub.run(SOURCE, KEYS, fetch_rows, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
