"""
Treasury yield premiums -- Federal Reserve Bank of San Francisco term-structure model.

    python -m altdata.sources.sffed          # one pull, summary to stdout

Signal-triage order ST-1, feed row "SF Fed Treasury Yield Premiums (sffed.*)";
used by SR-6 (the Runkevicius decomposition of the move to a 5% 10-year) and by
the rates driver (ST-3) as one of four term-premium models.

SOURCE. https://www.frbsf.org/research-and-insights/data-and-indicators/treasury-yield-premiums/
links "FRBSF_Term_Model_Data.xlsx", the complete model output. Sheets used:
"Fit Term Premium" (FTERMPnnYR), "Fit Avg Expected Rate" (FEXPTRnnYR) and "Fit
Treasury Yields" (FYIELDnnYR), nn = 01..10. DATE is an Excel serial day. Values are
FRACTIONS (0.0107 = 1.07%) and are stored in PERCENT, multiplied by 100 at write,
so every term premium in the store -- ACM, Kim-Wright, DKW, this -- is in one unit.
The "Observed" sheets are the inputs the model was fitted to, not its output, and
are not stored.

Read with the stdlib .xlsx reader in _publication.py, so no new dependency.

AVAILABILITY. The SF Fed republishes the file in place "per publication" and sends
Last-Modified, which is stored as available_at (`observed`) -- the instant this
vintage of the file appeared. The model is re-estimated, so revised history is
written as new vintages inside the write window (revision_policy: recomputed).
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "frbsf_term_premium"
URL = "https://www.frbsf.org/wp-content/uploads/FRBSF_Term_Model_Data.xlsx"

# registry key -> (sheet, column). Fractions in the file; percent in the store.
COLUMNS: dict[str, tuple[str, str]] = {
    "sffed.term_premium_5y": ("Fit Term Premium", "FTERMP05YR"),
    "sffed.term_premium_10y": ("Fit Term Premium", "FTERMP10YR"),
    "sffed.expected_rate_10y": ("Fit Avg Expected Rate", "FEXPTR10YR"),
    "sffed.fitted_yield_10y": ("Fit Treasury Yields", "FYIELD10YR"),
}
KEYS = list(COLUMNS)
TO_PERCENT = 100.0


def rows_from_workbook(book: dict[str, list[list[Any]]], available_at: str,
                       kind: str) -> list[dict]:
    """Observation rows from the workbook's fitted sheets. Raises on a changed shape."""
    out: list[dict] = []
    for key, (sheet, col) in COLUMNS.items():
        table = book.get(sheet)
        if not table:
            raise ValueError(f"workbook has no sheet {sheet!r}")
        header = [str(h).strip() if h is not None else "" for h in table[0]]
        if "DATE" not in header or col not in header:
            raise ValueError(f"sheet {sheet!r} lacks DATE or {col}")
        di, ci = header.index("DATE"), header.index(col)
        for row in table[1:]:
            day = pub.excel_serial_date(row[di] if di < len(row) else None)
            v = row[ci] if ci < len(row) else None
            if not day or not isinstance(v, float):
                continue
            out.append({"registry_key": key, "instrument": None,
                        "observed_at": day, "available_at": available_at,
                        "value": round(v * TO_PERCENT, 8),
                        "availability_kind": kind})
    return out


def _produce() -> list[dict]:
    data, headers = http_get_response(URL, timeout=120)
    available_at, kind = pub.availability(headers)
    return rows_from_workbook(pub.read_xlsx(data), available_at, kind)


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
