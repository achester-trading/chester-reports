"""
The Investment Company Institute's weekly money-market fund assets (the
deposit-flight flag's other side; signal-triage Batch 12, item 59, ST-R6.59a; a53,
20 Oct 2026).

    python -m altdata.sources.ici_mmf      # one pull

SOURCE (checked 20 Oct 2026, F6). https://www.ici.org/mm_summary_data_<year>.xls,
linked from https://www.ici.org/research/stats/mmf, keyless: "Weekly Total Net
Assets (TNA) and Number of Money Market Mutual Funds", MILLIONS of dollars, one row
a Wednesday, the current year's file carrying its recent weeks (about twenty). The
TNA column is found under the "TOTAL - ALL MONEY MARKET" heading, the date in the
first column. robots.txt disallows the site's admin, search and user paths only;
the check runs on every pull, and a refusal writes nothing. The file is .xls, read
with xlrd (as altdata/sources/aaii.py reads its .xls).

STORED, one row a week, in DOLLARS, observed_at the Wednesday, available_at the
file's Last-Modified (observed) or the write instant:
  ici.mmf_total     total money-market fund assets
The deposit-flight ledger's longer history reads FRED's retail series
(fred.mmf_retail) in its place, labelled. UNSCHEDULED (20 Oct 2026). ici.org answers HTTP 403 to every client that names
itself, robots.txt included, and a writer never passes for a browser (the AAII
rule, CLAUDE.md). So ICI is a listed gap and this module is on no roster: its parser
stays for the day the file answers an identified client (LBMA's precedent,
altdata/feeds.py). The deposit-flight flag reads FRED's retail series meanwhile.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import re
from typing import Optional

from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "ici_mmf"
SITE = "https://www.ici.org"
URL = SITE + "/mm_summary_data_{year}.xls"
KEYS = ["ici.mmf_total"]
DATE_RE = re.compile(r"^\s*(\d{2})/(\d{2})/(\d{4})\s*$")


def rows_from_sheet(cells: list[list], available: str, kind: str) -> list[dict]:
    """`cells`: the sheet as rows of values. The TNA column is the first 'TNA'
    under the 'TOTAL - ALL MONEY MARKET' heading's column."""
    col = None
    for r in cells:
        for j, v in enumerate(r):
            if str(v).strip().upper().startswith("TOTAL - ALL MONEY MARK"):
                col = j
                break
        if col is not None:
            break
    if col is None:
        raise ValueError("ICI: no 'TOTAL - ALL MONEY MARKET' heading")
    tna = None
    for r in cells:
        for j in range(col, min(col + 3, len(r))):
            if str(r[j]).strip().upper() == "TNA":
                tna = j
                break
        if tna is not None:
            break
    if tna is None:
        raise ValueError("ICI: no TNA column under the total")
    out = []
    for r in cells:
        m = DATE_RE.match(str(r[0])) if r else None
        if not m or len(r) <= tna:
            continue
        try:
            v = float(r[tna])
        except (TypeError, ValueError):
            continue
        day = dt.date(int(m.group(3)), int(m.group(1)), int(m.group(2))).isoformat()
        out.append({"registry_key": "ici.mmf_total", "instrument": None,
                    "observed_at": day, "available_at": available,
                    "value": round(v * 1e6, 0), "availability_kind": kind})
    if not out:
        raise ValueError("ICI: no dated week")
    return out


def sheet_cells(data: bytes) -> list[list]:
    import xlrd                                                 # noqa: PLC0415
    sh = xlrd.open_workbook(file_contents=data).sheet_by_index(0)
    return [[sh.cell_value(i, j) for j in range(sh.ncols)] for i in range(sh.nrows)]


def fetch_rows(year: Optional[int] = None) -> list[dict]:
    from .. import session                                      # noqa: PLC0415
    url = URL.format(year=year or dt.date.fromisoformat(session.session_date()).year)
    ok, why = pub.robots_allows(SITE, url)
    if not ok:
        raise PermissionError(f"robots.txt refuses {url} ({why})")
    data, headers = http_get_response(url, timeout=60)
    available, kind = pub.availability(headers)
    return rows_from_sheet(sheet_cells(data), available, kind)


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, fetch_rows, run_id=run_id, db=db)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
