"""
The Federal Reserve's excess bond premium and GZ spread (item 124, Tranche 0, step 5;
D60, 6 Nov 2026; A126).

    python -m altdata.sources.fed_ebp              # one pull (the write window)
    python -m altdata.sources.fed_ebp --backfill   # once: the whole file, from 1973

SOURCE (read 6 Nov 2026). The FEDS Notes monthly CSV,
https://www.federalreserve.gov/econres/notes/feds-notes/ebp_csv.csv, keyless,
monthly from January 1973, columns date, gz_spread, ebp, est_prob (Gilchrist and
Zakrajsek's credit spread and its excess bond premium, the Board's update). Both
values are in percentage points. www.federalreserve.gov answers robots.txt with
404, which is no rules; the check runs on every pull, and a refusal writes nothing.

STORED, one row per month, observed_at the month's first day:
  fed.ebp         the excess bond premium, percentage points
  fed.gz_spread   the GZ credit spread, percentage points
est_prob (the Board's recession probability) is not stored: the order names two
series. Columns are found by name. A new OFFICIAL writer, on the freshness roster.

THE BACKFILL IS FLAGGED (AUD-3d's convention for a series without vintages): the
file is revised in place and the Board keeps no vintages, so the history's first
pull is stored under source `fed:backfill` with available_at the pull instant
(availability_kind ingest_instant) -- an upper bound, never a claim about when the
Board first published a month. Later pulls write under `fed` at the file's
Last-Modified (or the write instant), the last 400 days only.

Report only: no flag, no composite, no overlay, and barred from the market-state
object. The Monthly prints EBP as one slow-read line (daily_cascade/credit_long_block.py).
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import logging
from typing import Optional

from .. import session
from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "fed"
BACKFILL_SOURCE = "fed:backfill"
SITE = "https://www.federalreserve.gov"
URL = SITE + "/econres/notes/feds-notes/ebp_csv.csv"
# A literal list: feeds.static_keys() reads it from source.
KEYS = ["fed.ebp", "fed.gz_spread"]
COLUMNS = {"ebp": "fed.ebp", "gz_spread": "fed.gz_spread"}


def rows_from_csv(text: str, available: str, kind: str,
                  source: Optional[str] = None) -> list[dict]:
    reader = csv.reader(io.StringIO(text.lstrip("﻿")))
    head = [h.strip().lower() for h in next(reader, [])]
    if "date" not in head or not all(c in head for c in COLUMNS):
        raise ValueError(f"FEDS Notes EBP: expected date, gz_spread and ebp columns, "
                         f"got {head[:4]}")
    di = head.index("date")
    idx = {COLUMNS[c]: head.index(c) for c in COLUMNS}
    out = []
    for r in reader:
        try:
            day = r[di].strip()[:10]
        except IndexError:
            continue
        if len(day) != 10:
            continue
        for key, i in idx.items():
            try:
                v = float(r[i])
            except (ValueError, IndexError):
                continue
            row = {"registry_key": key, "instrument": None, "observed_at": day,
                   "available_at": available, "value": v, "availability_kind": kind}
            if source:
                row["source"] = source
            out.append(row)
    if not out:
        raise ValueError("FEDS Notes EBP: no dated row")
    return out


def fetch_text() -> tuple[str, dict]:
    ok, why = pub.robots_allows(SITE, URL)
    if not ok:
        raise PermissionError(f"robots.txt refuses {URL} ({why})")
    data, headers = http_get_response(URL, timeout=60)
    return data.decode("utf-8", errors="replace"), headers


def fetch_rows(backfill: bool = False) -> list[dict]:
    text, headers = fetch_text()
    if backfill:
        return rows_from_csv(text, session.utc_iso(), "ingest_instant",
                             source=BACKFILL_SOURCE)
    available, kind = pub.availability(headers)
    return rows_from_csv(text, available, kind)


def pull(run_id: Optional[str] = None, db=None, backfill: bool = False) -> dict:
    return pub.run(SOURCE, KEYS, lambda: fetch_rows(backfill), run_id=run_id, db=db,
                   **({"window_days": 60 * 366} if backfill else {}))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(prog="python -m altdata.sources.fed_ebp")
    ap.add_argument("--backfill", action="store_true",
                    help="once: the whole file under source fed:backfill")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(backfill=a.backfill), indent=2, sort_keys=True, default=str))
