"""
USDA NASS's weekly Crop Progress, through the release service (ESMIS): the share
of the crop rated good or excellent, for the Alternative Assets Quarterly's
agriculture section (b69-quarterly-readers-1; D34 of 24 Oct 2026; B67 section 26).

    python -m altdata.sources.esmis_crop_progress            # the newest report
    python -m altdata.sources.esmis_crop_progress --reports 12

TERMS. As esmis_wasde: robots.txt (esmis.nal.usda.gov) allows the publication
page and the release files; ESMIS posts no terms page; Crop Progress is a US
Government work (17 U.S.C. 105). Re-read 25 Oct 2026.

SOURCE. Each report's text file (progWWYY.txt), linked from the publication page.
The reader takes the "<Crop> Condition - Selected States: Week Ending <date>"
tables and, in each, the all-states row ("18 States ......:  5  12  27  43  13"):
very poor, poor, fair, good, excellent, percent. Good plus excellent is stored.

  usda.crop_progress.corn       Corn Condition
  usda.crop_progress.soybeans   Soybean Condition
  usda.crop_progress.wheat      Winter Wheat Condition (Spring Wheat Condition
                                when the report carries no winter wheat table)

A crop out of season has no table that week, and nothing is written for it -- a
season's end is not a reading. observed_at = the week-ending date. available_at =
the release date at 16:00 ET ("released after 4:00 pm ET on the first business
day of the week", the report's own words), reconstructed.
"""
from __future__ import annotations

import datetime as dt
import logging
import re
from typing import Optional

from . import _publication as pub
from . import _quarterly_common as qc
from ._base import http_get_response, http_get_text

log = logging.getLogger(__name__)

SOURCE = "usda_esmis"
LISTING = "https://esmis.nal.usda.gov/publication/crop-progress"
KEYS = ["usda.crop_progress.corn", "usda.crop_progress.soybeans",
        "usda.crop_progress.wheat"]
TABLES = {"corn": ("Corn",), "soybeans": ("Soybean",),
          "wheat": ("Winter Wheat", "Spring Wheat")}
RELEASE_ET = "16:00"


def _fetch(url: str, **kw):
    """Every request through THIS module's helpers (patchable by the gates)."""
    return qc.fetch(url, get=lambda u, **k: http_get_response(u, **k),
                    get_text=lambda u: http_get_text(u, timeout=30), **kw)


def _robots(url: str) -> str:
    return qc.robots_check(url, get_text=lambda u: http_get_text(u, timeout=30))

_HEAD = re.compile(r"^(?P<crop>[A-Z][A-Za-z ]+?) Condition - Selected States: "
                   r"Week Ending (?P<date>[A-Z][a-z]+ \d{1,2}, \d{4})", re.M)
_ALL = re.compile(r"^\s*\d+ States\s*\.*:\s*([\d\s-]+)$", re.M)
_RELEASED = re.compile(r"Released (?P<date>[A-Z][a-z]+ \d{1,2}, \d{4})")


def _date(s: str) -> str:
    return dt.datetime.strptime(s, "%B %d, %Y").date().isoformat()


def good_excellent(text: str) -> dict[str, tuple[str, float]]:
    """{table crop name: (week-ending date, good + excellent percent)}."""
    out: dict[str, tuple[str, float]] = {}
    heads = list(_HEAD.finditer(text))
    for i, h in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        m = _ALL.search(text, h.end(), end)
        if not m:
            continue
        cells = [c for c in m.group(1).split()]
        if len(cells) != 5:
            continue
        vals = [0.0 if c == "-" else float(c) for c in cells]
        out[h.group("crop").strip()] = (_date(h.group("date")), vals[3] + vals[4])
    return out


def rows_from_text(text: str) -> list[dict]:
    rel = _RELEASED.search(text)
    if not rel:
        raise ValueError("no 'Released <date>' line -- the report changed shape")
    available = qc.et_instant(_date(rel.group("date")), RELEASE_ET)
    found = good_excellent(text)
    rows = []
    for crop, names in TABLES.items():
        hit = next((found[n] for n in names if n in found), None)
        if hit:
            rows.append({"registry_key": f"usda.crop_progress.{crop}",
                         "instrument": None, "observed_at": hit[0],
                         "available_at": available, "value": hit[1],
                         "availability_kind": "reconstructed"})
    if not found:
        raise ValueError("no condition table in the Crop Progress text")
    return rows


def release_links(html: str) -> list[str]:
    return list(dict.fromkeys(re.findall(
        r'href="([^"]*/release-files/\d+/prog\d{4}\.txt)"', html)))


def _produce(reports: int = 1) -> list[dict]:
    from urllib.parse import urljoin
    page, _h = _fetch(LISTING)
    links = release_links(page.decode("utf-8", "replace"))[:reports]
    if not links:
        raise ValueError("no Crop Progress text linked on the ESMIS publication page")
    rows: list[dict] = []
    for href in links:
        data, _h = _fetch(urljoin(LISTING, href))
        rows += rows_from_text(data.decode("utf-8", "replace"))
    return rows


def pull(run_id: Optional[str] = None, db=None, reports: int = 1) -> dict:
    return pub.run(SOURCE, KEYS, lambda: _produce(reports), run_id=run_id, db=db)


if __name__ == "__main__":
    raise SystemExit(qc.main(pull, reports=(1, "Crop Progress reports to read, newest first")))
