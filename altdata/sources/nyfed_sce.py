"""
NY Fed Survey of Consumer Expectations -- 3-year and 5-year inflation expectations.

    python -m altdata.sources.nyfed_sce      # one pull, summary to stdout

Signal-triage order ST-2 (SR-24): the third long-run expectations survey beside
UMich 5-10y and the Fed Board's CIE.

SOURCE. https://www.newyorkfed.org/medialibrary/interactives/sce/sce/downloads/
data/frbny-sce-data.xlsx -- one workbook, no key, read with the stdlib .xlsx reader.
Dates are YYYYMM numbers; values are PERCENT.

THE SHEETS ARE FOUND BY PATTERN (writer-fixes-1, 17 Oct 2026). The first full
pull on the box failed "SCE workbook has no sheet 'Five-year ahead Infl Exp'":
the NY Fed reshaped the workbook, and the five-year median is now a column of
the "Inflation expectations" sheet beside the one- and three-year (read 17 Oct
2026; tests/fixtures/nyfed_sce/workbook_2026-10.json holds every sheet name and
that sheet's header). So each key names a pattern for its sheet and one for its
column, and takes the first sheet that carries a matching column:

  nyfed.sce_3y   "Median three-year ahead expected inflation rate", monthly from
                 June 2013 (the key the report already prints, unchanged)
  nyfed.sce_5y   "Median five-year ahead expected inflation rate"; the older
                 "Five-year ahead Infl Exp" sheet still matches if it returns

The demographic, distribution and uncertainty sheets never match. A key whose
column is found nowhere is logged with the sheet list and left absent; the rest
is written. No sheet matching at all raises, with the sheet list.

  nyfed.sce_3y, nyfed.sce_5y   observed_at = the survey month's first day (month_start)

AVAILABILITY. The workbook is served without Last-Modified, so available_at is the
write instant (`ingest_instant`) -- an upper bound, the publication-keyed stamp
§1.4 asks for, late by however long after release the first pull ran. The survey
is revised only rarely; revision_policy: revised, so a restatement is a vintage.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Optional

from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "nyfed_sce"
URL = ("https://www.newyorkfed.org/medialibrary/interactives/sce/sce/downloads/"
       "data/frbny-sce-data.xlsx")
# key -> (sheet-name pattern, column-header pattern), case-insensitive. A sheet
# whose name says Demo, distr or uncertainty is never read.
SHEETS = {"nyfed.sce_3y": (r"^inflation exp(ectations)?$|three-year ahead infl",
                           r"^median three-year ahead expected inflation"),
          "nyfed.sce_5y": (r"^inflation exp(ectations)?$|five-year ahead infl",
                           r"^median five-year ahead expected inflation|^median$")}
NEVER = re.compile(r"demo|distr|uncertain", re.I)
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


def find_column(book: dict[str, list[list[Any]]], sheet_rx: str, col_rx: str
                ) -> Optional[tuple[str, int, int]]:
    """(sheet, header row, column) of the first sheet whose name matches
    `sheet_rx` and whose first twelve rows carry a header matching `col_rx`."""
    for name, table in book.items():
        if NEVER.search(name) or not re.search(sheet_rx, name.strip(), re.I):
            continue
        for i, row in enumerate(table[:12]):
            for j, cell in enumerate(row):
                if isinstance(cell, str) and re.search(col_rx, cell.strip(), re.I):
                    return name, i, j
    return None


def rows_from_workbook(book: dict[str, list[list[Any]]], available_at: str,
                       kind: str, absent: Optional[dict] = None) -> list[dict]:
    out: list[dict] = []
    if not any(re.search(sx, n.strip(), re.I) and not NEVER.search(n)
               for sx, _ in SHEETS.values() for n in book):
        raise ValueError(f"SCE workbook: no inflation-expectations sheet among "
                         f"{list(book)}")
    for key, (sheet_rx, col_rx) in SHEETS.items():
        hit = find_column(book, sheet_rx, col_rx)
        if hit is None:
            why = f"no sheet carries a column matching {col_rx!r}"
            log.warning("%s: %s; %s absent, the rest written. Sheets: %s",
                        SOURCE, why, key, list(book))
            if absent is not None:
                absent[key] = why
            continue
        sheet, hdr, col = hit
        table = book[sheet]
        for row in table[hdr + 1:]:
            day = _yyyymm(row[0] if row else None)
            v = row[col] if col < len(row) else None
            if day and isinstance(v, float):
                out.append({"registry_key": key, "instrument": None,
                            "observed_at": day, "available_at": available_at,
                            "value": round(v, 6), "availability_kind": kind})
    return out


def _produce(absent: Optional[dict] = None) -> list[dict]:
    data, headers = http_get_response(URL, timeout=120)
    return rows_from_workbook(pub.read_xlsx(data), *pub.availability(headers),
                              absent=absent)


def pull(run_id: Optional[str] = None, db=None) -> dict:
    absent: dict = {}
    out = pub.run(SOURCE, KEYS, lambda: _produce(absent), run_id=run_id, db=db)
    if absent:
        out["absent"] = absent
    return out


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
