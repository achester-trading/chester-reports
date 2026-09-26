"""
ACM Treasury term premium -- New York Fed (Adrian, Crump and Moench, 2013).

    python -m altdata.sources.acm            # one pull, summary to stdout

Signal-triage order ST-1, feed row "ACM term premium (acm.*)"; used by SR-6, 15
and 23 and by the rates driver (ST-3), where it is one of the four term-premium
models whose SIGN DISAGREEMENT is surfaced and never averaged.

SOURCE. https://www.newyorkfed.org/research/data_indicators/term-premia-tabs
publishes the model output as ONE legacy Excel workbook (BIFF .xls, ~10 MB),
sheets "ACM Daily" and "ACM Monthly". There is no CSV: the change order says
"CSV" and the page offers none, so this reads the workbook's daily sheet. Columns
are DATE (dd-Mon-yyyy), ACMYnn (fitted zero-coupon yield), ACMTPnn (term premium)
and ACMRNYnn (risk-neutral yield) for nn = 01..10 years, all in PERCENT.

THE ONE DEPENDENCY. A BIFF .xls cannot be read by the standard library, so this
module needs `xlrd` (requirements.txt). `make deploy` does not pip install; until
the box's venv has it, the import fails inside the run and the writer reports
STALE with that reason -- it never takes the feed step down with it.

AVAILABILITY. The NY Fed serves no Last-Modified on this file, so available_at is
the write instant (`ingest_instant`), an upper bound. The model is re-estimated,
so a changed historical value is a real revision (revision_policy: recomputed)
and is written as a new vintage inside the write window -- see _publication.py.
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any, Optional

from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "nyfed_acm"
URL = ("https://www.newyorkfed.org/medialibrary/media/research/"
       "data_indicators/ACMTermPremium.xls")
SHEET = "ACM Daily"

# registry key -> workbook column. Percent, as published.
COLUMNS: dict[str, str] = {
    "acm.term_premium_2y": "ACMTP02",
    "acm.term_premium_5y": "ACMTP05",
    "acm.term_premium_10y": "ACMTP10",
    "acm.risk_neutral_yield_10y": "ACMRNY10",
    "acm.fitted_yield_10y": "ACMY10",
}
KEYS = list(COLUMNS)


def _date(raw: Any) -> Optional[str]:
    text = str(raw or "").strip()
    for fmt in ("%d-%b-%Y", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return dt.datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def rows_from_table(table: list[list[Any]], available_at: str,
                    kind: str) -> list[dict]:
    """Observation rows from the daily sheet's cells. Raises on a changed shape."""
    if not table:
        raise ValueError(f"sheet {SHEET!r} is empty")
    header = [str(h).strip() for h in table[0]]
    missing = [c for c in COLUMNS.values() if c not in header]
    if "DATE" not in header or missing:
        raise ValueError(f"sheet {SHEET!r} lacks columns "
                         f"{(['DATE'] if 'DATE' not in header else []) + missing}")
    di = header.index("DATE")
    idx = {k: header.index(c) for k, c in COLUMNS.items()}
    out: list[dict] = []
    for row in table[1:]:
        day = _date(row[di] if di < len(row) else None)
        if not day:
            continue
        for key, i in idx.items():
            v = row[i] if i < len(row) else None
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                out.append({"registry_key": key, "instrument": None,
                            "observed_at": day, "available_at": available_at,
                            "value": float(v), "availability_kind": kind})
    return out


def _produce() -> list[dict]:
    import xlrd  # noqa: PLC0415 -- see THE ONE DEPENDENCY above
    data, headers = http_get_response(URL, timeout=120)
    available_at, kind = pub.availability(headers)
    book = xlrd.open_workbook(file_contents=data)
    sheet = book.sheet_by_name(SHEET)
    table = [sheet.row_values(r) for r in range(sheet.nrows)]
    return rows_from_table(table, available_at, kind)


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
