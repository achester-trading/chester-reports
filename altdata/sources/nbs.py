"""
NBS -- China's property: the 70-city new-home prices, starts and sales, from the
National Bureau of Statistics' English press releases.

    python -m altdata.sources.nbs            # one pull, summary to stdout

AQ-3 part 2 (11 Oct 2026; the Quarterly's China chapter, change order section
4.5, "Property: starts" and the 70-city read). Verified 11 Oct 2026 from a US
address: stats.gov.cn's robots.txt answers 404 (no rules); the English release
index and both releases answered 200 within seven seconds. data.stats.gov.cn,
the query database, answers 403 and is not used.

FOUND BY TITLE, READ BY CONTENT. The index (PressRelease/, and index_1.html for
its second page) lists each release as <a title="FULL TITLE" href=...>; the
visible text is truncated, so the title attribute is matched, whitespace
normalised (the pages carry U+2002 and U+202F) and curly quotes straightened:
  "Sales Prices of Commercial Residential Buildings in 70 Medium and Large-sized
   Cities in <Month> <Year>"                                 (09:30 Beijing)
  "Investment in Real Estate Development from January to <Month> <Year>"
                                                             (10:00 Beijing)
In a release a table is found by the caption printed before it, never by its
position:
  70-city, Table I "Sales Price Indices of Newly Constructed Commercial
    Residential Buildings in 70 Large and Medium-Sized Cities": two cities a row,
    [city, M/M, Y/Y, year-to-date average] twice, indices with 100 = no change.
    It must hold exactly 70 cities or the release is refused. THE ENGLISH
    EDITION PRINTS NO 70-CITY AGGREGATE, so the summary is computed here:
  nbs.city70_new_mm_down / _mm_up   cities whose new-home index fell / rose on
                                    the month (count; = 100 is neither)
  nbs.city70_new_yy_down            cities below a year earlier (count)
  nbs.city70_new_mm_avg / _yy_avg   the unweighted mean of the 70 indices less
                                    100, percent -- NOT the NBS's own aggregate,
                                    which it does not publish in English
  Investment release, "Table 1 Real Estate Development and Sales from January
    to <Month>": [indicator, absolute value, growth y/y %], the parent row of
    each indicator (never its "Of which" sub-rows), all YEAR-TO-DATE:
  nbs.re_starts_ytd, _yoy           floor space newly started (10,000 sq m; y/y %)
  nbs.re_sold_area_ytd, _yoy        new commercial floor space sold (10,000 sq m)
  nbs.re_sales_ytd, _yoy            sales of new commercial buildings (100 mn yuan)

observed_at = the reference month's first day. AVAILABILITY: the release date
(from the release's URL, tYYYYMMDD) at its stated hour, Beijing,
`reconstructed`. The index carries about fifteen releases a page, so the store
holds the releases still listed at the first pull and grows forward from there:
NO HISTORY BEFORE THE FIRST RUN (the query database that has it refuses
scripts).
"""

from __future__ import annotations

import datetime as dt
import html as _html
import logging
import re
from typing import Optional
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

from .. import observations
from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "nbs"
INDEX_URLS = ["https://www.stats.gov.cn/english/PressRelease/",
              "https://www.stats.gov.cn/english/PressRelease/index_1.html"]
BEIJING = ZoneInfo("Asia/Shanghai")
MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August",
     "September", "October", "November", "December"], start=1)}

CITY70_TITLE = re.compile(r"^Sales Prices of Commercial Residential Buildings in 70 "
                          r"Medium and Large-sized Cities in (\w+),? (\d{4})$", re.I)
REDEV_TITLE = re.compile(r"^Investment in Real Estate Development from January to "
                         r"(\w+),? (\d{4})$", re.I)
CITY70_CAPTION = ("Sales Price Indices of Newly Constructed Commercial Residential "
                  "Buildings in 70 Large and Medium-Sized Cities")
REDEV_CAPTION = "Real Estate Development and Sales"
CITY70_HOUR, REDEV_HOUR = dt.time(9, 30), dt.time(10, 0)

CITY70_KEYS = ["nbs.city70_new_mm_down", "nbs.city70_new_mm_up",
               "nbs.city70_new_yy_down", "nbs.city70_new_mm_avg",
               "nbs.city70_new_yy_avg"]
REDEV_ROWS = {   # label prefix (normalised) -> key
    "Floor space of buildings newly started": "nbs.re_starts_ytd",
    "Floor space of newly built commercial buildings sold": "nbs.re_sold_area_ytd",
    "Sales of newly built commercial buildings": "nbs.re_sales_ytd",
}
REDEV_KEYS = [k for v in REDEV_ROWS.values() for k in (v, v + "_yoy")]
KEYS = CITY70_KEYS + REDEV_KEYS


def norm(text: str) -> str:
    """Tags stripped, entities decoded, every space-like character one space,
    curly quotes straightened."""
    t = _html.unescape(re.sub(r"<[^>]+>", " ", text))
    t = t.replace("’", "'").replace("‘", "'")
    return re.sub(r"[\s     ]+", " ", t).strip()


def releases(index_page: str, base: str) -> list[tuple[str, str]]:
    """(normalised title, absolute URL) for every release the index lists."""
    out = []
    for attrs in re.findall(r"<a\s([^>]*)>", index_page, re.I):
        t = re.search(r'title="([^"]*)"', attrs)
        h = re.search(r'href="([^"]*)"', attrs)
        if t and h and re.search(r"t\d{8}_\d+\.html?$", h.group(1)):
            out.append((norm(t.group(1)), urljoin(base, h.group(1))))
    return out


def release_month(title: str) -> Optional[tuple[str, str]]:
    """('city70' | 'redev', observed_at) for a release this writer reads."""
    for kind, pat in (("city70", CITY70_TITLE), ("redev", REDEV_TITLE)):
        m = pat.match(title)
        if m and m.group(1).capitalize() in MONTHS:
            return kind, pub.month_start(int(m.group(2)), MONTHS[m.group(1).capitalize()])
    return None


def release_available(url: str, hour: dt.time) -> str:
    m = re.search(r"t(\d{4})(\d{2})(\d{2})_\d+\.html?$", url)
    if not m:
        raise ValueError(f"no release date in {url}")
    local = dt.datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)),
                        hour.hour, hour.minute, tzinfo=BEIJING)
    return observations.canonical_instant(local.astimezone(dt.timezone.utc).isoformat())


def captioned_table(page: str, caption: str) -> list[list[str]]:
    """The rows of the first table whose preceding text carries `caption`."""
    want = norm(caption).lower()
    for m in re.finditer(r"<table\b.*?</table>", page, re.S | re.I):
        before = norm(page[max(0, m.start() - 1500):m.start()]).lower()
        if want in before[-600:]:
            rows = []
            for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", m.group(0), re.S | re.I):
                rows.append([norm(c) for c in
                             re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S | re.I)])
            return rows
    raise ValueError(f"no table captioned {caption!r}")


def _num(text: str) -> Optional[float]:
    try:
        return float(text.replace(",", "").replace("−", "-").strip())
    except (AttributeError, ValueError):
        return None


def city70_rows(page: str, observed: str, available: str) -> list[dict]:
    cities: dict[str, tuple[float, float]] = {}
    for r in captioned_table(page, CITY70_CAPTION):
        for i in (0, 4):
            if len(r) >= i + 3:
                mm, yy = _num(r[i + 1]), _num(r[i + 2])
                if r[i] and mm is not None and yy is not None:
                    cities[r[i]] = (mm, yy)
    if len(cities) != 70:
        raise ValueError(f"the 70-city table holds {len(cities)} cities, not 70")
    mms, yys = [v[0] for v in cities.values()], [v[1] for v in cities.values()]
    vals = {"nbs.city70_new_mm_down": sum(x < 100 for x in mms),
            "nbs.city70_new_mm_up": sum(x > 100 for x in mms),
            "nbs.city70_new_yy_down": sum(x < 100 for x in yys),
            "nbs.city70_new_mm_avg": sum(mms) / 70.0 - 100.0,
            "nbs.city70_new_yy_avg": sum(yys) / 70.0 - 100.0}
    return [{"registry_key": k, "instrument": None, "observed_at": observed,
             "available_at": available, "value": round(float(v), 4),
             "availability_kind": "reconstructed"} for k, v in vals.items()]


def redev_rows(page: str, observed: str, available: str) -> list[dict]:
    out, seen = [], set()
    for r in captioned_table(page, REDEV_CAPTION):
        if len(r) < 3:
            continue
        for label, key in REDEV_ROWS.items():
            if r[0].startswith(label) and key not in seen:
                level, yoy = _num(r[1]), _num(r[2])
                if level is None or yoy is None:
                    raise ValueError(f"{label}: unreadable {r[1:3]}")
                seen.add(key)
                for k, v in ((key, level), (key + "_yoy", yoy)):
                    out.append({"registry_key": k, "instrument": None,
                                "observed_at": observed, "available_at": available,
                                "value": v, "availability_kind": "reconstructed"})
    missing = set(REDEV_ROWS.values()) - seen
    if missing:
        raise ValueError(f"the real-estate table lacks {sorted(missing)}")
    return out


def _get(url: str) -> str:
    data, _h = http_get_response(url, timeout=60, max_retries=2)
    return data.decode("utf-8", errors="replace")


def _produce() -> list[dict]:
    listed: dict[str, str] = {}
    for idx in INDEX_URLS:
        for title, url in releases(_get(idx), idx):
            listed.setdefault(url, title)
    rows: list[dict] = []
    for url, title in listed.items():
        got = release_month(title)
        if got is None:
            continue
        kind, observed = got
        page = _get(url)
        if kind == "city70":
            rows += city70_rows(page, observed, release_available(url, CITY70_HOUR))
        else:
            rows += redev_rows(page, observed, release_available(url, REDEV_HOUR))
    if not rows:
        raise RuntimeError("no 70-city or real-estate release on the NBS index")
    return rows


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
