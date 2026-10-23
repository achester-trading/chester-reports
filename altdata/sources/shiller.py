"""
Robert Shiller's stock market data -- CAPE and its inputs, monthly from 1871.

    python -m altdata.sources.shiller        # one pull, summary to stdout

Signal-triage order ST-2 (SR-7, SR-15): the valuation leg of the cross-asset
z-scores and the ERP input.

SOURCE. https://shillerdata.com/ links "ie_data.xls"; THE URL CHANGES WITH EACH
EDITION (a new storage path and a ?ver= token), so the link is found on the page
every run (_publication.find_link). Legacy .xls (xlrd), sheet "Data", eight header
rows, then Date as YYYY.MM -- and October is written 2026.1, so the month is
round((date - year) * 100), never the decimal read as a fraction.

STORED, observed_at = the month's first day (month_start -- monthly averages):
  shiller.sp_price      P, S&P Composite (monthly average of daily closes; the
                        latest month is the first-of-month close -- the sheet's
                        own note)
  shiller.sp_dividend   D     shiller.sp_earnings   E   (both lag the price by
                        months; recent rows are blank and are skipped)
  shiller.cpi           CPI   shiller.gs10          the long rate, percent
  shiller.cape          P/E10, column 12
  reference.file_vintage   instrument "shiller": the latest dated row

THE HOUSING FILE (Batch 14 item 69, a56, 21 Oct 2026). The same page links
"Fig3-1.xls", the data for Figure 3.1 of Irrational Exuberance as updated by the
author: the real home price index, 1890 = 100, ANNUAL from 1890 to 1952 and
MONTHLY from January 1953 (Date YYYY + (m - 0.5)/12, so May 2026 is 2026.375).
  shiller.real_home_price   observed_at the year's first day (annual rows) or the
                            month's first day (monthly rows)
Its failure never stops the stock-market pull: the key is then absent with its
reason and CAPE is written as before.

The sheet is revised as earnings arrive and CPI is estimated then replaced;
available_at is the file's Last-Modified (`observed`). revision_policy: revised.
"""

from __future__ import annotations

import logging
from typing import Optional

from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "shiller"
PAGE = "https://shillerdata.com/"
LINK = r"ie_data\.xls"
HOUSING_LINK = r"Fig3-1"
HOUSING_KEY = "shiller.real_home_price"
# registry key -> column index in the "Data" sheet
COLUMNS = {"shiller.sp_price": 1, "shiller.sp_dividend": 2,
           "shiller.sp_earnings": 3, "shiller.cpi": 4, "shiller.gs10": 6,
           "shiller.cape": 12}
KEYS = list(COLUMNS) + [HOUSING_KEY]


def _month(v) -> Optional[str]:
    if not isinstance(v, float):
        return None
    year = int(v)
    month = int(round((v - year) * 100))
    if not (1 <= month <= 12 and 1800 < year < 2200):
        return None
    return pub.month_start(year, month)


def rows_from_table(table: list[list], available_at: str, kind: str) -> list[dict]:
    hdr = next((i for i, r in enumerate(table[:15])
                if r and str(r[0]).strip() == "Date"), None)
    if hdr is None:
        raise ValueError("no 'Date' header row in Shiller's Data sheet")
    labels = " ".join(str(c) for r in table[hdr - 3:hdr + 1] for c in r[12:13])
    if "CAPE" not in labels and "P/E10" not in labels:
        raise ValueError(f"column 12 is not CAPE ({labels!r}) -- layout changed")
    out = []
    for row in table[hdr + 1:]:
        day = _month(row[0] if row else None)
        if not day:
            continue
        for key, j in COLUMNS.items():
            v = row[j] if j < len(row) else None
            if isinstance(v, float):
                out.append({"registry_key": key, "instrument": None,
                            "observed_at": day, "available_at": available_at,
                            "value": round(v, 8), "availability_kind": kind})
    return out


def _housing_date(v) -> Optional[str]:
    """1890.0 -> the year's first day; 2026.375 -> May 2026's first day."""
    if not isinstance(v, float):
        return None
    year = int(v)
    frac = v - year
    if not 1800 < year < 2200:
        return None
    if abs(frac) < 1e-6:
        return pub.month_start(year, 1)
    month = int(round(frac * 12 - 0.5)) + 1
    return pub.month_start(year, month) if 1 <= month <= 12 else None


def housing_rows(table: list[list], available_at: str, kind: str) -> list[dict]:
    hdr = next((i for i, r in enumerate(table[:15])
                if r and str(r[0]).strip() == "Date"), None)
    if hdr is None:
        raise ValueError("no 'Date' header row in Shiller's housing sheet")
    labels = " ".join(str(r[1]) for r in table[max(0, hdr - 4):hdr + 1] if len(r) > 1)
    if "Real" not in labels or "Price" not in labels:
        raise ValueError(f"column 1 is not the real home price index ({labels!r})")
    out = []
    for row in table[hdr + 1:]:
        day = _housing_date(row[0] if row else None)
        v = row[1] if len(row) > 1 else None
        if day and isinstance(v, float):
            out.append({"registry_key": HOUSING_KEY, "instrument": None,
                        "observed_at": day, "available_at": available_at,
                        "value": round(v, 8), "availability_kind": kind})
    return out


def _produce_housing() -> list[dict]:
    import xlrd  # noqa: PLC0415 -- requirements.txt
    url = pub.find_link(PAGE, HOUSING_LINK)
    data, headers = http_get_response(url, timeout=120)
    available_at, kind = pub.availability(headers)
    sheet = xlrd.open_workbook(file_contents=data).sheet_by_name("Data")
    return housing_rows([sheet.row_values(r) for r in range(sheet.nrows)],
                        available_at, kind)


def _produce() -> list[dict]:
    import xlrd  # noqa: PLC0415 -- requirements.txt
    url = pub.find_link(PAGE, LINK)
    data, headers = http_get_response(url, timeout=120)
    available_at, kind = pub.availability(headers)
    sheet = xlrd.open_workbook(file_contents=data).sheet_by_name("Data")
    rows = rows_from_table([sheet.row_values(r) for r in range(sheet.nrows)],
                           available_at, kind)
    last = max((r["observed_at"] for r in rows), default=None)
    if last:
        rows.append(pub.vintage_row("shiller", f"data to {last[:7]}", available_at,
                                    kind, observed_at=last))
    try:
        rows.extend(_produce_housing())
    except Exception as exc:                                    # noqa: BLE001
        log.warning("shiller: the housing file was not read (%s); CAPE is written "
                    "without it", exc)
    return rows


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
