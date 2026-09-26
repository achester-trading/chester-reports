"""
NY Fed Survey of Consumer Expectations -- 3-year and 5-year inflation expectations.

    python -m altdata.sources.nyfed_sce      # one pull, summary to stdout

Signal-triage order ST-2 (SR-24): the third long-run expectations survey beside
UMich 5-10y and the Fed Board's CIE.

SOURCE. https://www.newyorkfed.org/medialibrary/interactives/sce/sce/downloads/
data/frbny-sce-data.xlsx -- one workbook, no key, read with the stdlib .xlsx reader.
  "Inflation expectations"     column "Median three-year ahead expected inflation
                               rate", monthly from June 2013
  "Five-year ahead Infl Exp"   the five-year median, a shorter history (added to
                               the survey in 2022)
Dates are YYYYMM numbers; values are PERCENT.

  nyfed.sce_3y, nyfed.sce_5y   observed_at = the survey month's first day (month_start)

AVAILABILITY. The workbook is served without Last-Modified, so available_at is the
write instant (`ingest_instant`) -- an upper bound, the publication-keyed stamp
§1.4 asks for, late by however long after release the first pull ran. The survey
is revised only rarely; revision_policy: revised, so a restatement is a vintage.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "nyfed_sce"
URL = ("https://www.newyorkfed.org/medialibrary/interactives/sce/sce/downloads/"
       "data/frbny-sce-data.xlsx")
SHEETS = {"nyfed.sce_3y": ("Inflation expectations", "median three-year"),
          "nyfed.sce_5y": ("Five-year ahead Infl Exp", "median")}
KEYS = list(SHEETS)


def _yyyymm(v: Any) -> Optional[str]:
    try:
        n = int(float(v))
    except (TypeError, ValueError):
        return None
    y, m = divmod(n, 100)
    if not (1900 < y < 2200 and 1 <= m <= 12):
        return None
    return pub.month_start(y, m)


def rows_from_workbook(book: dict[str, list[list[Any]]], available_at: str,
                       kind: str) -> list[dict]:
    out: list[dict] = []
    for key, (sheet, needle) in SHEETS.items():
        table = book.get(sheet)
        if not table:
            raise ValueError(f"SCE workbook has no sheet {sheet!r}")
        col = hdr = None
        for i, row in enumerate(table[:12]):
            for j, cell in enumerate(row):
                if isinstance(cell, str) and needle in cell.lower():
                    col, hdr = j, i
                    break
            if col is not None:
                break
        if col is None:
            raise ValueError(f"SCE sheet {sheet!r} has no column matching {needle!r}")
        for row in table[hdr + 1:]:
            day = _yyyymm(row[0] if row else None)
            v = row[col] if col < len(row) else None
            if day and isinstance(v, float):
                out.append({"registry_key": key, "instrument": None,
                            "observed_at": day, "available_at": available_at,
                            "value": round(v, 6), "availability_kind": kind})
    return out


def _produce() -> list[dict]:
    data, headers = http_get_response(URL, timeout=120)
    return rows_from_workbook(pub.read_xlsx(data), *pub.availability(headers))


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
