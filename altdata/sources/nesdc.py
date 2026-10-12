"""
NESDC (Thailand's Office of the National Economic and Social Development
Council) -- real GDP, quarterly, seasonally adjusted.

    python -m altdata.sources.nesdc          # one pull, summary to stdout

AQ-3 part 2 (11 Oct 2026; the Quarterly's Thailand chapter). ISOLATED:
namespace thailand, never trigger_eligible.

SOURCE. nesdc.go.th publishes the national accounts' tables as a ZIP OF CSVs
with each release; robots.txt disallows only /wp-admin/ (checked 11 Oct 2026).
The chain, each hop found by its text:
  /info/quarterly-gross-domestic-product-qgdp/feed/   an RSS feed; the item
      titled "... ผลิตภัณฑ์มวลรวมในประเทศ รายไตรมาส (CSV)" (the QGDP statistical
      tables, CSV) links a download page
  that page   links the file as /?p=<post>&ddl=<id>, which redirects (setting a
      cookie on the way, which the request keeps) to the release's .zip

READ BY CONTENT, never by file name. The CSV whose title row names "Gross
domestic product, chain volume measures" and "(Seasonally Adjusted)" (Table 6 in
the Q2 2026 release) whose unit row says "Million Baht" -- its twin of
percentage changes carries the same title and is passed over; the column whose
header names "Gross Domestic Product (CVM)". A data row is [year, quarter
("Q1", or "Q1r" when revised), values...], the values in quoted thousands.

  thai.gdp_real_sa       real GDP, chain volume (reference year 2002), SA,
                         MILLION BAHT a quarter; observed_at = the quarter's
                         first day
  thai.gdp_real_sa_qoq   its change on the previous quarter, percent (computed)

AVAILABILITY. The zip's Last-Modified (`observed`), else the write instant: an
upper bound for the history (from 1993 Q1) it carries. The whole table is read
each pull; a revised quarter is a new vintage.
"""

from __future__ import annotations

import csv
import io
import logging
import re
import zipfile
from typing import Optional
from urllib.parse import urljoin

from . import _publication as pub
from ._base import http_get_response, http_get_text

log = logging.getLogger(__name__)

SOURCE = "nesdc"
FEED_URL = "https://www.nesdc.go.th/info/quarterly-gross-domestic-product-qgdp/feed/"
FEED_ITEM = "รายไตรมาส (CSV)"
LEVEL, QOQ = "thai.gdp_real_sa", "thai.gdp_real_sa_qoq"
KEYS = [LEVEL, QOQ]
QUARTER_MONTH = {"Q1": 1, "Q2": 4, "Q3": 7, "Q4": 10}


def csv_page(feed: str) -> str:
    for item in re.findall(r"<item>(.*?)</item>", feed, re.S):
        title = re.search(r"<title>(.*?)</title>", item, re.S)
        link = re.search(r"<link>(.*?)</link>", item, re.S)
        if title and link and FEED_ITEM in title.group(1):
            return link.group(1).strip()
    raise ValueError("the NESDC feed lists no quarterly-GDP CSV tables")


def zip_link(page: str, base: str) -> str:
    m = re.search(r'href="([^"]*[?&;]ddl=\d+[^"]*)"', page)
    if not m:
        raise ValueError("the NESDC download page links no file")
    return urljoin(base, m.group(1).replace("&amp;", "&"))


def _num(text: str) -> Optional[float]:
    try:
        return float(str(text).replace(",", "").strip())
    except ValueError:
        return None


def series_from_zip(data: bytes) -> dict[str, float]:
    """{quarter start: million baht} from the SA chain-volume table."""
    z = zipfile.ZipFile(io.BytesIO(data))
    for name in z.namelist():
        if not name.lower().endswith(".csv"):
            continue
        rows = list(csv.reader(io.StringIO(z.read(name).decode("utf-8-sig"))))
        if len(rows) < 4:
            continue
        title = " ".join(rows[0]).lower()
        if not ("gross domestic product, chain volume measures" in title
                and "(seasonally adjusted)" in title):
            continue
        if "million baht" not in " ".join(rows[1]).lower():
            continue                     # its growth-rate twin (Table 6.1): percent
        col = next((i for i, h in enumerate(rows[2])
                    if "gross domestic product (cvm)" in h.lower()), None)
        if col is None:
            raise ValueError(f"{name}: no 'Gross Domestic Product (CVM)' column")
        out = {}
        for r in rows[3:]:
            if len(r) <= col or not re.fullmatch(r"\d{4}", r[0].strip()):
                continue
            q = r[1].strip()[:2].upper()
            v = _num(r[col])
            if q in QUARTER_MONTH and v is not None:
                out[pub.month_start(int(r[0]), QUARTER_MONTH[q])] = v
        if not out:
            raise ValueError(f"{name}: no quarters")
        return out
    raise ValueError("no CSV in the zip is the SA chain-volume GDP table")


def rows_from_series(series: dict[str, float], available: str, kind: str) -> list[dict]:
    out, prev = [], None
    for day in sorted(series):
        v = series[day]
        out.append({"registry_key": LEVEL, "instrument": None, "observed_at": day,
                    "available_at": available, "value": v, "availability_kind": kind})
        if prev:
            out.append({"registry_key": QOQ, "instrument": None, "observed_at": day,
                        "available_at": available,
                        "value": round(100.0 * (v / prev - 1.0), 6),
                        "availability_kind": kind})
        prev = v
    return out


def _produce() -> list[dict]:
    page_url = csv_page(http_get_text(FEED_URL, timeout=60))
    url = zip_link(http_get_text(page_url, timeout=60), page_url)
    data, headers = http_get_response(url, timeout=90)
    available, kind = pub.availability(headers)
    return rows_from_series(series_from_zip(data), available, kind)


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
