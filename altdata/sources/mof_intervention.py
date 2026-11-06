"""
Japan's foreign-exchange intervention record, monthly, from the Ministry of
Finance, for the Alternative Assets Quarterly's currencies chapter (the
intervention-footprint row) and SR-34's block (b69-quarterly-readers-1; D34 of
24 Oct 2026; B67 section 12).

    python -m altdata.sources.mof_intervention               # the newest release
    python -m altdata.sources.mof_intervention --pages 44    # the index's releases

TERMS (re-read 25 Oct 2026, https://www.mof.go.jp/english/notice.htm, the page B67
could not locate): "The copyright for information posted or published on this
website ... belongs to the Ministry of Finance unless otherwise provided, and
Public Data License (Version 1.0; PDL 1.0) ... applies unless any rights are
indicated." PDL 1.0 permits reuse with the source cited; the page's exclusions
name the Geospatial Information Authority's maps, which this reader does not
touch. THE CONDITION, IN CODE: every row's source field cites the Ministry
(`mof_intervention:Ministry of Finance, Japan`). robots.txt (www.mof.go.jp)
answers 404: no rules.

SOURCE. The English monthly releases, one page per period, linked from
.../reference/feio/monthly/index.html (44 pages on 25 Oct 2026, from January
2023). Each page states "Total amount of foreign exchange intervention operations
for the period from <date> through <date> ... ¥ <amount>".

  jp.mof.intervention_jpy   the period's total, YEN (a figure printed with a unit
                            word -- million, billion, trillion, hundred million --
                            is scaled to yen; "¥ 0" is zero)

observed_at = the period's last day. available_at = the page's release date (the
date in its file name) at 19:00 Tokyo, reconstructed: the Ministry publishes the
monthly figure at the end of the month's last business day.
"""
from __future__ import annotations

import datetime as dt
import html as _html
import logging
import re
import time
from typing import Optional
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

from .. import observations
from . import _publication as pub
from . import _quarterly_common as qc
from ._base import http_get_response, http_get_text

log = logging.getLogger(__name__)

SOURCE = "mof_intervention"
ATTRIBUTION = "Ministry of Finance, Japan"
ROW_SOURCE = f"{SOURCE}:{ATTRIBUTION}"
INDEX = ("https://www.mof.go.jp/english/policy/international_policy/reference/"
         "feio/monthly/index.html")
KEYS = ["jp.mof.intervention_jpy"]
TOKYO = ZoneInfo("Asia/Tokyo")
SCALE = {"": 1.0, "million": 1e6, "billion": 1e9, "trillion": 1e12,
         "hundred million": 1e8}
PACING_SECONDS = 1.0


def _fetch(url: str, **kw):
    """Every request through THIS module's helpers (patchable by the gates)."""
    return qc.fetch(url, get=lambda u, **k: http_get_response(u, **k),
                    get_text=lambda u: http_get_text(u, timeout=30), **kw)


def _robots(url: str) -> str:
    return qc.robots_check(url, get_text=lambda u: http_get_text(u, timeout=30))


def page_links(index_html: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r'href="(\d{8}e?\.html)"', index_html)))


def _text(page: str) -> str:
    page = re.sub(r"(?is)<(script|style).*?</\1>", " ", page)
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", page)))


def row_from_page(name: str, page: str) -> dict:
    t = _text(page)
    m = re.search(r"Total amount of foreign exchange intervention operations for the "
                  r"period from ([A-Z][a-z]+ \d{1,2}, \d{4}) through "
                  r"([A-Z][a-z]+ \d{1,2}, \d{4})\s*[¥\\]\s*([\d,]+(?:\.\d+)?)\s*"
                  r"(hundred million|million|billion|trillion)?", t)
    if not m:
        raise ValueError(f"{name}: no 'Total amount ... ¥' sentence -- the page changed")
    end = dt.datetime.strptime(m.group(2), "%B %d, %Y").date().isoformat()
    value = float(m.group(3).replace(",", "")) * SCALE[(m.group(4) or "").lower()]
    rel = re.match(r"(\d{4})(\d{2})(\d{2})", name)
    local = dt.datetime(int(rel.group(1)), int(rel.group(2)), int(rel.group(3)),
                        19, 0, tzinfo=TOKYO)
    return {"registry_key": "jp.mof.intervention_jpy", "instrument": None,
            "observed_at": end,
            "available_at": observations.canonical_instant(
                local.astimezone(dt.timezone.utc).isoformat()),
            "value": value, "availability_kind": "reconstructed",
            "source": ROW_SOURCE}


def _produce(pages: int = 1) -> list[dict]:
    index, _h = _fetch(INDEX)
    names = page_links(index.decode("utf-8", "replace"))[:pages]
    if not names:
        raise ValueError("no monthly release linked on the MoF index page")
    rows = []
    for i, name in enumerate(names):
        if i:
            time.sleep(PACING_SECONDS)
        data, _h = _fetch(urljoin(INDEX, name), robots=False)
        rows.append(row_from_page(name, data.decode("utf-8", "replace")))
    return rows


def pull(run_id: Optional[str] = None, db=None, pages: int = 1) -> dict:
    return pub.run(SOURCE, KEYS, lambda: _produce(pages), run_id=run_id, db=db)


if __name__ == "__main__":
    raise SystemExit(qc.main(pull, pages=(1, "monthly release pages to read, newest first")))
