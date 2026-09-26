"""
Federal Reserve Board -- Index of Common Inflation Expectations (CIE), quarterly.

    python -m altdata.sources.fedboard       # one pull, summary to stdout

Signal-triage order ST-2 (SR-24): the Board's summary of long-run expectations
across surveys and market measures (Ahn and Fulton), the first of the three
DEANCHOR cross-checks beside UMich 5-10y and the NY Fed SCE.

SOURCE. https://www.federalreserve.gov/econres/notes/feds-notes/
FEDS-Note-2873-cie-data.csv -- linked from the "Research Data Series: Index of
Common Inflation Expectations" note (not from the 2020 FEDS note, which carries
no data link). No key. UTF-8 with a BOM; "period,CIE_spf,CIE_mich"; periods are
M/D/YYYY quarter-ends from 1999Q1; PERCENT. Updated at noon ET on the third
Friday of January, April, July and October.

  fedboard.cie   instrument "spf"  -- the index estimated with the SPF's
                                      long-run expectation
                 instrument "mich" -- the variant with Michigan's
                 observed_at = the quarter-end

THE WHOLE HISTORY IS RE-ESTIMATED at every update (it is a common factor over
the full sample), so a changed past quarter is a new vintage, not an error;
revision_policy: recomputed. available_at is the file's Last-Modified (`observed`).
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

SOURCE = "frb_cie"
URL = ("https://www.federalreserve.gov/econres/notes/feds-notes/"
       "FEDS-Note-2873-cie-data.csv")
KEY = "fedboard.cie"
KEYS = [KEY]
COLUMNS = {"CIE_spf": "spf", "CIE_mich": "mich"}


def rows_from_csv(text: str, available_at: str, kind: str) -> list[dict]:
    reader = csv.DictReader(io.StringIO(text.lstrip("﻿")))
    fields = [f.strip() for f in reader.fieldnames or []]
    if "period" not in fields or not set(COLUMNS) <= set(fields):
        raise ValueError(f"CIE file lacks period/CIE_spf/CIE_mich ({fields})")
    out = []
    for rec in reader:
        rec = {(k or "").strip(): (v or "").strip() for k, v in rec.items()}
        try:
            day = dt.datetime.strptime(rec["period"], "%m/%d/%Y").date().isoformat()
        except (KeyError, ValueError):
            continue
        for col, inst in COLUMNS.items():
            try:
                v = float(rec.get(col, ""))
            except ValueError:
                continue
            out.append({"registry_key": KEY, "instrument": inst,
                        "observed_at": day, "available_at": available_at,
                        "value": v, "availability_kind": kind})
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
