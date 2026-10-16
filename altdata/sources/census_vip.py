"""
Census Bureau construction spending (VIP, value put in place) -- data centers,
private nonresidential, power and total construction, monthly, SAAR.

    python -m altdata.sources.census_vip      # one pull (HELD: writes nothing)

ST-R4.23a (16 Oct 2026; Batch 5 item 23, Factor I's real-economy twin). Read by
altdata/batch5.py's construction(), deflated by FRED's PPIDCS
(fred.ppi_construction), printed in the Monthly's slow layers under Factor I.
No rights until the Disruptive Themes refresh rules on it.

HELD FOR D1c. This is a NEW store writer, and the 25 Sep order's Track D
precondition is "D1c before any new writer"; the repo-wide write lock has not
landed (TODO.md D1c). So, on the pattern of altdata/sources/redfin.py (branch
st-r5-rates): the module is built and gated on fixtures, `HELD_FOR_D1C` is True,
pull() fetches nothing, writes nothing and says why, and the module is on no
feeds roster. Lifting the hold is the operator's ruling plus two edits:
HELD_FOR_D1C = False and the module name in altdata/feeds.py EXTERNAL_WRITERS.

SOURCE (verify item 8, checked 16 Oct 2026). The Census time-series API
(api.census.gov/data/timeseries/eits/vip) now refuses a request without a key,
and a session creates no keys, so this reads the two keyless workbooks the
historical-data page links (census.gov/construction/c30/historical_data.html):
  /construction/c30/xlsx/privsatime.xlsx   private, by type, SAAR, Jan 1993 on
  /construction/c30/xlsx/totsatime.xlsx    total (private + public), SAAR
both millions of dollars, seasonally adjusted annual rate, Last-Modified sent
(1 Oct 2026 for August 2026). "Data center" is its own column under Office from
JANUARY 2014 -- 152 months to August 2026 (84,950 SAAR, preliminary) -- and blank
before: a blank is skipped, never zero. Read with the standard library (an xlsx
is a zip of XML): no new dependency.

THE FIELDS, by column name, never position:
  census.vip_data_center              private "Data center"
  census.vip_private_nonresidential   private "Nonresidential"
  census.vip_total                    "Total Construction" (private + public)
  census.vip_power                    "Total Power" (private + public; the XII
                                      disagreement note's line)
observed_at is the month's first day. Census revises the two latest months
("p" preliminary, "r" revised) and benchmarks annually: revision_policy revised,
a restated value is a new vintage row.
"""

from __future__ import annotations

import io
import logging
import re
import zipfile
import xml.etree.ElementTree as ET
from typing import Optional

from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "census_vip"
BASE = "https://www.census.gov/construction/c30/xlsx/"
PRIVATE_URL = BASE + "privsatime.xlsx"
TOTAL_URL = BASE + "totsatime.xlsx"

PRIVATE = {"Data center": "census.vip_data_center",
           "Nonresidential": "census.vip_private_nonresidential"}
TOTAL = {"Total Construction": "census.vip_total",
         "Total Power": "census.vip_power"}
KEYS = list(PRIVATE.values()) + list(TOTAL.values())
# THE TOTAL WORKBOOK'S FOOTNOTE 1: "Detailed types of construction not available
# prior to 2002" -- and the cells before then print 0. A 0 there is ABSENT, not
# zero spending, so a detailed type is read from 2002 only.
FIRST_MONTH = {"census.vip_power": "2002-01-01"}

HELD_FOR_D1C = True
HOLD_REASON = ("held for D1c: a new store writer waits for the repo-wide write "
               "lock (Track D precondition; TODO.md D1c)")

_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
_MONTH = re.compile(r"^([A-Z][a-z]{2})-(\d\d)[pr]?$")
_MONTHS = {m: i for i, m in enumerate(
    ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov",
     "Dec"), 1)}


def _clean(h: Optional[str]) -> str:
    """'Total\\n_x000D_Construction1' -> 'Total Construction'."""
    s = (h or "").replace("_x000D_", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return re.sub(r"\d+$", "", s).strip()


def sheet_rows(data: bytes) -> list[list[Optional[str]]]:
    """The first worksheet's rows as strings, shared strings resolved."""
    z = zipfile.ZipFile(io.BytesIO(data))
    try:
        ss = ["".join(t.itertext()) for t in
              ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", _NS)]
    except KeyError:
        ss = []
    root = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    out = []
    for r in root.findall(".//m:sheetData/m:row", _NS):
        row: list[Optional[str]] = []
        for c in r.findall("m:c", _NS):
            # A cell's column letter places it: a skipped blank cell must not
            # shift the row (read by name, so the index has to be the column's).
            ref = c.get("r") or ""
            col = 0
            for ch in re.sub(r"\d", "", ref):
                col = col * 26 + (ord(ch) - 64)
            while col and len(row) < col - 1:
                row.append(None)
            v = c.find("m:v", _NS)
            if v is None:
                t = c.find("m:is", _NS)
                row.append("".join(t.itertext()) if t is not None else None)
            else:
                row.append(ss[int(v.text)] if c.get("t") == "s" else v.text)
        out.append(row)
    return out


def _month(s: Optional[str]) -> Optional[str]:
    m = _MONTH.match(str(s or "").strip())
    if not m:
        return None
    yy = int(m.group(2))
    year = 1900 + yy if yy >= 90 else 2000 + yy
    return f"{year:04d}-{_MONTHS[m.group(1)]:02d}-01"


def rows_from_xlsx(data: bytes, columns: dict, available: str, kind: str) -> list[dict]:
    rows = sheet_rows(data)
    hi = next((k for k, r in enumerate(rows) if r and str(r[0] or "").strip() == "Date"),
              None)
    if hi is None:
        raise ValueError("the Census workbook has no 'Date' header row")
    head = [_clean(h) for h in rows[hi]]
    idx = {}
    for name, key in columns.items():
        if name not in head:
            raise ValueError(f"the Census workbook has no {name!r} column")
        idx[key] = head.index(name)
    out = []
    for r in rows[hi + 1:]:
        day = _month(r[0] if r else None)
        if not day:
            continue
        for key, i in idx.items():
            if day < FIRST_MONTH.get(key, ""):
                continue
            v = r[i] if i < len(r) else None
            try:
                x = float(str(v).replace(",", ""))
            except (TypeError, ValueError):
                continue                       # blank, (NA), (S): skipped, never zero
            out.append({"registry_key": key, "instrument": None, "observed_at": day,
                        "available_at": available, "value": x,
                        "availability_kind": kind})
    if not out:
        raise ValueError("no monthly rows in the Census workbook")
    return out


def fetch_rows() -> list[dict]:
    rows: list[dict] = []
    for url, cols in ((PRIVATE_URL, PRIVATE), (TOTAL_URL, TOTAL)):
        data, headers = http_get_response(url, timeout=120)
        available, kind = pub.availability(headers)
        rows.extend(rows_from_xlsx(data, cols, available, kind))
    return rows


def pull(run_id: Optional[str] = None, db=None) -> dict:
    if HELD_FOR_D1C:
        return {"source": SOURCE, "status": "HELD", "written": 0,
                "reason": HOLD_REASON, "keys": KEYS}
    return pub.run(SOURCE, KEYS, fetch_rows, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
