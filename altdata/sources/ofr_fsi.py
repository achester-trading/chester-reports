"""
The Office of Financial Research's Financial Stress Index (the bank-stress panel's
second composite; signal-triage Batch 12, item 59, ST-R6.59a; a53, 20 Oct 2026).

    python -m altdata.sources.ofr_fsi              # one pull (the last year)
    python -m altdata.sources.ofr_fsi --backfill   # the whole file, from 2000

SOURCE (checked 20 Oct 2026, F6). https://www.financialresearch.gov/financial-
stress-index/data/fsi.csv, keyless, daily from 2000-01-03, with columns Date, OFR
FSI, Credit, Equity valuation, Safe assets, Funding, Volatility and three regional
columns. robots.txt disallows /error/, /test/, /this-page-has-moved/ and
/about/introduction/ only; the check runs on every pull, and a refusal writes
nothing.

STORED, one row per day, observed_at the date, available_at the file's
Last-Modified (observed) or the write instant:
  ofr.fsi           the headline index (zero is average stress; positive above)
  ofr.fsi_funding   the funding category's contribution
  ofr.fsi_credit    the credit category's contribution
Columns are found by name. A new OFFICIAL writer.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import logging
from typing import Optional

from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "ofr_fsi"
SITE = "https://www.financialresearch.gov"
URL = SITE + "/financial-stress-index/data/fsi.csv"
# A literal list: feeds.static_keys() reads it from source.
KEYS = ["ofr.fsi", "ofr.fsi_funding", "ofr.fsi_credit"]
COLUMNS = {"ofr fsi": "ofr.fsi", "funding": "ofr.fsi_funding", "credit": "ofr.fsi_credit"}


def rows_from_csv(text: str, available: str, kind: str) -> list[dict]:
    reader = csv.reader(io.StringIO(text.lstrip("﻿")))
    head = [h.strip().lower() for h in next(reader, [])]
    if "date" not in head or "ofr fsi" not in head:
        raise ValueError(f"OFR FSI: expected Date and OFR FSI columns, got {head[:4]}")
    di = head.index("date")
    idx = {COLUMNS[c]: head.index(c) for c in COLUMNS if c in head}
    out = []
    for r in reader:
        try:
            day = r[di].strip()[:10]
        except IndexError:
            continue
        for key, i in idx.items():
            try:
                v = float(r[i])
            except (ValueError, IndexError):
                continue
            out.append({"registry_key": key, "instrument": None, "observed_at": day,
                        "available_at": available, "value": v,
                        "availability_kind": kind})
    if not out:
        raise ValueError("OFR FSI: no dated row")
    return out


def fetch_rows() -> list[dict]:
    ok, why = pub.robots_allows(SITE, URL)
    if not ok:
        raise PermissionError(f"robots.txt refuses {URL} ({why})")
    data, headers = http_get_response(URL, timeout=60)
    available, kind = pub.availability(headers)
    return rows_from_csv(data.decode("utf-8", errors="replace"), available, kind)


def pull(run_id: Optional[str] = None, db=None, backfill: bool = False) -> dict:
    return pub.run(SOURCE, KEYS, fetch_rows, run_id=run_id, db=db,
                   **({"window_days": 40 * 366} if backfill else {}))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(prog="python -m altdata.sources.ofr_fsi")
    ap.add_argument("--backfill", action="store_true")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(backfill=a.backfill), indent=2, sort_keys=True, default=str))
