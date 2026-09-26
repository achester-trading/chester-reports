"""
University of Michigan Surveys of Consumers -- 5-to-10-year inflation expectations.

    python -m altdata.sources.umich          # one pull, summary to stdout

Signal-triage order ST-2 (SR-24): one of the three long-run expectation surveys
behind DEANCHOR (ST-4) -- with the Fed Board's CIE and the NY Fed SCE -- so that
de-anchoring cannot fire on the 5y5y breakeven alone.

SOURCE. https://www.sca.isr.umich.edu/files/tbmpx1px5.csv -- Table 32, monthly,
no key. Columns Month, YYYY, PX_MD (next-year median), PX5_MD (5-10 year median),
PERCENT. PX5_MD is sparse before 1990 (asked only in some months) and a blank is
skipped, not zeroed.

  umich.expect_5_10y   PX5_MD, observed_at = the survey month's first day (month_start)

PRELIMINARY, THEN FINAL. The survey publishes a preliminary reading mid-month and
the final at month-end, and this file carries whichever is current. The order asks
for the FINAL: a pull between the two stores the preliminary, and the final --
a different number for the same month -- arrives as a revision with the later
Last-Modified, so the as-of join returns the final once it exists and the
preliminary before it. Surveys are keyed on publication (§1.4): available_at is
the file's Last-Modified, `observed`. revision_policy: revised.
"""

from __future__ import annotations

import calendar
import csv
import io
import logging
from typing import Optional

from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "umich_sca"
URL = "https://www.sca.isr.umich.edu/files/tbmpx1px5.csv"
KEY = "umich.expect_5_10y"
KEYS = [KEY]
MONTHS = {m: i for i, m in enumerate(calendar.month_name) if m}


def rows_from_csv(text: str, available_at: str, kind: str) -> list[dict]:
    reader = csv.DictReader(io.StringIO(text.lstrip("﻿")))
    fields = [f.strip() for f in reader.fieldnames or []]
    if not {"Month", "YYYY", "PX5_MD"} <= set(fields):
        raise ValueError(f"UMich table 32 lacks Month/YYYY/PX5_MD ({fields})")
    out: list[dict] = []
    for rec in reader:
        rec = {(k or "").strip(): (v or "").strip() for k, v in rec.items()}
        month = MONTHS.get(rec.get("Month", ""))
        try:
            year = int(rec.get("YYYY", ""))
            v = float(rec.get("PX5_MD", ""))
        except ValueError:
            continue
        if not month:
            continue
        out.append({"registry_key": KEY, "instrument": None,
                    "observed_at": pub.month_start(year, month),
                    "available_at": available_at, "value": v,
                    "availability_kind": kind})
    return out


def _produce() -> list[dict]:
    data, headers = http_get_response(URL, timeout=60)
    return rows_from_csv(data.decode("utf-8", errors="replace"),
                         *pub.availability(headers))


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
