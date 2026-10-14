"""
Japan's international reserves -- Ministry of Finance, monthly.

    python -m altdata.sources.mof_reserves   # one pull, summary to stdout

Signal-triage batch 3, ST-B3-05 (SR-34, Japan intervention funding and FIMA).
Placed in the `tic.*` family by ruling (6 Oct 2026, decision 4: official-sector
holdings stay one family; there is no `jp.official`). With the Fed's FIMA repo
line (altdata/sources/fedboard_h41.py) these are the fast tells ahead of TIC.

SOURCE. https://www.mof.go.jp/policy/international_policy/reference/
official_reserve_assets/historical.csv -- linked from the English "International
Reserves/Foreign Currency Liquidity" page; no key. www.mof.go.jp answers
robots.txt with 404 (no rules; checked 13 Oct 2026). Shift-JIS (cp932), a
bilingual title block, then one row per month from April 2000:

  col 0  the Japanese era year, on a year's first row only (carried forward):
         Heisei (平成) N is 1988+N, Reiwa (令和) N is 2018+N, 元 is year 1
  col 2  the Western year -- on a year's first row until 2022 only; from 2023
         the file prints the era year alone, so the era year is what is read
  col 3  the month in English ("August")
  col 4  I.A  Official reserve assets, total
  col 6  I.A.1(1)(a)  Foreign currency reserves: securities

US$ MILLIONS, stored in DOLLARS (x1e6): the registry's `usd`, and the tic.*
family's unit. The header rows are checked by content -- "Official reserve
assets" and "Securities" must head their columns -- so a file that moved its
columns fails rather than storing the wrong line.

  tic.jp_reserves_total            official reserve assets, month-end
  tic.jp_reserves_fx_securities    the foreign-securities line, month-end

observed_at = the month's last day. The release is about the 7th of the
following month at 08:50 JST.

AVAILABILITY. The file's Last-Modified (`observed`): the instant this vintage was
published. The ministry revises (a June 2026 revision note is on the page), and a
changed past month is a new vintage (revision_policy: revised).
"""

from __future__ import annotations

import calendar
import csv
import datetime as dt
import io
import logging
from typing import Optional

from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "mof_reserves"
URL = ("https://www.mof.go.jp/policy/international_policy/reference/"
       "official_reserve_assets/historical.csv")
MILLIONS = 1_000_000.0
TOTAL_KEY = "tic.jp_reserves_total"
SECURITIES_KEY = "tic.jp_reserves_fx_securities"
KEYS = ["tic.jp_reserves_total", "tic.jp_reserves_fx_securities"]
COL_ERA, COL_YEAR, COL_MONTH, COL_TOTAL, COL_SECURITIES = 0, 2, 3, 4, 6
ERAS = {"平成": 1988, "令和": 2018}


def era_year(text: str) -> Optional[int]:
    """'令和8年' -> 2026; '令和元年' -> 2019; None for anything else."""
    import re                                                   # noqa: PLC0415
    m = re.match(r"\s*(平成|令和)(元|\d+)年", text or "")
    if not m:
        return None
    return ERAS[m.group(1)] + (1 if m.group(2) == "元" else int(m.group(2)))
MONTHS = {m: i for i, m in enumerate(calendar.month_name) if m}
MONTHS.update({m: i for i, m in enumerate(calendar.month_abbr) if m})


def _num(v: str) -> Optional[float]:
    try:
        return float(str(v).replace(",", "").strip())
    except ValueError:
        return None


def rows_from_csv(text: str, available_at: str, kind: str) -> list[dict]:
    """Rows from the ministry's CSV. Raises when the columns are not where the
    header says they are."""
    rows = list(csv.reader(io.StringIO(text.lstrip("﻿"))))
    head = [" ".join(r[c] for r in rows[:20] if len(r) > c) for c in
            (COL_TOTAL, COL_SECURITIES)]
    if "Official reserve assets" not in head[0] or "Securities" not in head[1]:
        raise ValueError("the MoF reserves file's columns moved: col 4 is not "
                         "'Official reserve assets' or col 6 not 'Securities'")
    out: list[dict] = []
    year = None
    for r in rows:
        if len(r) <= COL_SECURITIES:
            continue
        y = era_year(r[COL_ERA]) or (int(r[COL_YEAR].strip())
                                     if r[COL_YEAR].strip().isdigit() else None)
        if y:
            year = y
        month = MONTHS.get(r[COL_MONTH].strip().rstrip("."))
        if year is None or not month:
            continue
        day = dt.date(year, month, calendar.monthrange(year, month)[1]).isoformat()
        for key, col in ((TOTAL_KEY, COL_TOTAL), (SECURITIES_KEY, COL_SECURITIES)):
            v = _num(r[col])
            if v is None:
                continue
            out.append({"registry_key": key, "instrument": None, "observed_at": day,
                        "available_at": available_at, "value": v * MILLIONS,
                        "availability_kind": kind})
    if not out:
        raise ValueError("no month parsed from the MoF reserves file")
    return out


def _produce() -> list[dict]:
    data, headers = http_get_response(URL, timeout=90)
    return rows_from_csv(data.decode("cp932", errors="replace"),
                         *pub.availability(headers))


def pull(run_id: Optional[str] = None, db=None) -> dict:
    # The ministry restates history (window wide enough for its revisions).
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db,
                   window_days=pub.WRITE_WINDOW_DAYS * 3)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
