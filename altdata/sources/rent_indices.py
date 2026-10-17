"""
The market rent indices: Zillow's observed rent index (ZORI) and Apartment List's
national rent estimate, each the United States' monthly level in dollars.

    python -m altdata.sources.rent_indices    # one pull

BATCH 7, ITEM 48 LENS 7 (6e-releases, 16 Oct 2026): the shelter lead. New leases
reach CPI shelter about four quarters later (architecture Part 17: BLS samples
each unit every six months and most leases reset annually), so these two are the
lead that CPI's own rent and OER lag. Zillow's is also the shelter component's
lead in the CPI lead composite (config/macro_6e.yaml), closing 6e-rest's gap
(ruling (a)3 of 16 Oct 2026). The BLS new-tenant rent index is the third series
the order names; it stays a listed gap (docs/briefs/6e-releases-notes.md).

A new writer, NOT held (the D1c ruling of 16 Oct 2026). On altdata/feeds.py
EXTERNAL_WRITERS. No key.

SOURCES (checked 16 Oct 2026; robots on every pull, through aaii.robots_verdict,
the wildcard-aware reader; a refusal writes nothing):
  ZILLOW  https://files.zillowstatic.com/research/public_csvs/zori/
          Metro_zori_uc_sfrcondomfr_sm_month.csv -- the smoothed, all-homes-plus-
          multifamily ZORI by metro, whose "United States" row (RegionType
          country) is the national index, monthly from Jan 2015, one column per
          month-end date. The file host's robots.txt carries no rule.
  APARTMENT LIST  the research page
          https://www.apartmentlist.com/research/category/data-rent-estimates
          (robots: Allow /, a few account paths disallowed) links the month's
          file, Apartment_List_Rent_Estimates_<YYYY>_<MM>.csv, on
          assets.ctfassets.net (robots.txt 404: no rules, RFC 9309 2.3.1.3). The
          link changes each month, so it is found on the page
          (_publication.find_link). The "United States" / "National" / "overall"
          row, monthly from Jan 2017, columns "YYYY_MM".

observed_at is the month's first day (the FRED convention, so a monthly read
lines up with CPI). Every row of a download carries the file's Last-Modified
(observed), or the write instant where none is sent: the history is knowable from
the first pull and not before. A blank cell is skipped, never zero.
"""

from __future__ import annotations

import csv
import io
import logging
import re
from typing import Callable, Optional

from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "rent_indices"
AGENT = "chester-reports"
ZILLOW_URL = ("https://files.zillowstatic.com/research/public_csvs/zori/"
              "Metro_zori_uc_sfrcondomfr_sm_month.csv")
APTLIST_PAGE = "https://www.apartmentlist.com/research/category/data-rent-estimates"
APTLIST_PATTERN = r"Apartment_List_Rent_Estimates_\d{4}_\d{2}\.csv"
# (robots.txt, a path the pull touches on that host)
ROBOTS = (("https://files.zillowstatic.com/robots.txt", ZILLOW_URL),
          ("https://www.apartmentlist.com/robots.txt", APTLIST_PAGE),
          ("https://assets.ctfassets.net/robots.txt",
           "https://assets.ctfassets.net/x/Apartment_List_Rent_Estimates_2026_09.csv"))
# A literal list: feeds.static_keys() reads it from source.
KEYS = ["zillow.zori_us", "aptlist.rent_us"]


def _row_dict(text: str) -> tuple[list[str], csv.reader]:
    reader = csv.reader(io.StringIO(text.lstrip("﻿")))
    head = [h.strip() for h in next(reader, [])]
    return head, reader


def zillow_rows(text: str, available: str, kind: str) -> list[dict]:
    head, reader = _row_dict(text)
    if "RegionName" not in head:
        raise ValueError(f"ZORI: no RegionName column, got {head[:6]}")
    ni = head.index("RegionName")
    ti = head.index("RegionType") if "RegionType" in head else None
    dates = [(i, h) for i, h in enumerate(head) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", h)]
    for r in reader:
        if len(r) <= ni or r[ni].strip() != "United States":
            continue
        if ti is not None and r[ti].strip().lower() not in ("country", ""):
            continue
        out = []
        for i, h in dates:
            try:
                x = float(r[i])
            except (ValueError, IndexError):
                continue
            out.append({"registry_key": "zillow.zori_us", "instrument": None,
                        "observed_at": f"{h[:7]}-01", "available_at": available,
                        "value": x, "availability_kind": kind})
        if out:
            return out
    raise ValueError("ZORI: no United States row with a value")


def aptlist_rows(text: str, available: str, kind: str) -> list[dict]:
    head, reader = _row_dict(text)
    need = ("location_name", "location_type", "bed_size")
    if any(c not in head for c in need):
        raise ValueError(f"Apartment List: expected {need}, got {head[:8]}")
    ni, li, bi = (head.index(c) for c in need)
    months = [(i, h) for i, h in enumerate(head) if re.fullmatch(r"\d{4}_\d{2}", h)]
    for r in reader:
        if len(r) <= max(ni, li, bi):
            continue
        if (r[ni].strip(), r[li].strip(), r[bi].strip()) != (
                "United States", "National", "overall"):
            continue
        out = []
        for i, h in months:
            try:
                x = float(r[i])
            except (ValueError, IndexError):
                continue
            out.append({"registry_key": "aptlist.rent_us", "instrument": None,
                        "observed_at": f"{h[:4]}-{h[5:7]}-01", "available_at": available,
                        "value": x, "availability_kind": kind})
        if out:
            return out
    raise ValueError("Apartment List: no United States / National / overall row")


def _robots_text(robots_url: str) -> str:
    import requests                                             # noqa: PLC0415
    r = requests.get(robots_url, timeout=30, headers={"User-Agent": AGENT})
    if 400 <= r.status_code < 500:
        return ""                    # unavailable: no rules (RFC 9309, 2.3.1.3)
    r.raise_for_status()
    return r.text


def robots_ok(get: Optional[Callable[[str], str]] = None) -> tuple[bool, str]:
    """Every host the pull touches, by the wildcard-aware reader."""
    from .aaii import robots_verdict                            # noqa: PLC0415
    get = get or _robots_text
    for ru, path in ROBOTS:
        ok, rule = robots_verdict(get(ru), path, AGENT)
        if not ok:
            return False, f"{ru} refuses {path} ({rule})"
    return True, ""


def fetch_rows() -> list[dict]:
    ok, why = robots_ok()
    if not ok:
        raise PermissionError(f"robots.txt: {why}")
    rows: list[dict] = []
    data, headers = http_get_response(ZILLOW_URL, timeout=120)
    available, kind = pub.availability(headers)
    rows += zillow_rows(data.decode("utf-8", errors="replace"), available, kind)
    link = pub.find_link(APTLIST_PAGE, APTLIST_PATTERN)
    data, headers = http_get_response(link, timeout=120)
    available, kind = pub.availability(headers)
    rows += aptlist_rows(data.decode("utf-8", errors="replace"), available, kind)
    return rows


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, fetch_rows, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
