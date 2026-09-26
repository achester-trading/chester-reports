"""
JGB constant-maturity yields -- Japan Ministry of Finance.

    python -m altdata.sources.mof            # one pull, summary to stdout

Signal-triage order ST-2 (§2.2.2, SR-2): the yen leg of the funding-currency
stack -- the JGB side of calc.jp_front_diff and calc.jp_hedged_carry (ST-5). The
monthly OECD series on FRED (fred.jp_10y, fred.jp_3m) are the long history; this
is the daily curve.

SOURCE. Two CSVs, no key:
  historical/jgbcme_all.csv   1974 to the end of the previous month, republished
                              monthly
  jgbcme.csv                  the current month, republished daily
Both open with a title line, then "Date,1Y,2Y,...,40Y". Dates are YYYY/M/D;
values are PERCENT; a tenor not yet issued on a date is "-" and is skipped.

STORED: mof.jgb_2y, mof.jgb_5y, mof.jgb_10y, mof.jgb_30y.

AVAILABILITY. Each file's Last-Modified, `observed`. For the current-month file
that is the evening the latest row was added -- the instant it became public. For
older rows re-served in the same file it is an upper bound, which is safe for an
as-of join. The yields are not revised (revision_policy: never).
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import logging
from typing import Optional

from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "mof_japan"
URL_HISTORY = ("https://www.mof.go.jp/english/policy/jgbs/reference/"
               "interest_rate/historical/jgbcme_all.csv")
URL_CURRENT = ("https://www.mof.go.jp/english/policy/jgbs/reference/"
               "interest_rate/jgbcme.csv")

COLUMNS = {"mof.jgb_2y": "2Y", "mof.jgb_5y": "5Y", "mof.jgb_10y": "10Y",
           "mof.jgb_30y": "30Y"}
KEYS = list(COLUMNS)


def _date(text: str) -> Optional[str]:
    try:
        y, m, d = (int(x) for x in text.strip().split("/"))
        return dt.date(y, m, d).isoformat()
    except (ValueError, TypeError):
        return None


def rows_from_csv(text: str, available_at: str, kind: str) -> list[dict]:
    """Rows from one MoF CSV. Raises when the header or a tenor is missing."""
    lines = text.lstrip("﻿").splitlines()
    start = next((i for i, ln in enumerate(lines)
                  if ln.lower().startswith("date,")), None)
    if start is None:
        raise ValueError("no 'Date,' header in the MoF file")
    reader = csv.DictReader(io.StringIO("\n".join(lines[start:])))
    fields = [f.strip() for f in reader.fieldnames or []]
    missing = [c for c in COLUMNS.values() if c not in fields]
    if missing:
        raise ValueError(f"MoF file lacks tenors {missing}")
    out: list[dict] = []
    for rec in reader:
        rec = {(k or "").strip(): (v or "").strip() for k, v in rec.items()}
        day = _date(rec.get("Date", ""))
        if not day:
            continue
        for key, col in COLUMNS.items():
            try:
                v = float(rec.get(col, ""))
            except ValueError:
                continue                   # "-": the tenor did not exist yet
            out.append({"registry_key": key, "instrument": None,
                        "observed_at": day, "available_at": available_at,
                        "value": v, "availability_kind": kind})
    return out


def _produce() -> list[dict]:
    rows: list[dict] = []
    for url in (URL_HISTORY, URL_CURRENT):
        data, headers = http_get_response(url, timeout=90)
        available_at, kind = pub.availability(headers)
        rows.extend(rows_from_csv(data.decode("utf-8", errors="replace"),
                                  available_at, kind))
    return rows


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
