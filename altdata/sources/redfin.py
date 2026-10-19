"""
Redfin data center -- national pending sales, active listings, inventory and
months of supply, and the top-50 metros' pending sales, monthly.

    python -m altdata.sources.redfin         # one pull (HELD: writes nothing)

ST-R5.36a (16 Oct 2026; Batch 6 item 36, the housing-transmission block). Read
by altdata/st_r5_rates.py's housing(); printed under "Rates transmission".

HELD FOR D1c. This is a NEW store writer, and the 25 Sep order's Track D
precondition is "D1c before any new writer": WAL and a busy timeout landed on
6 Sep (f98fec4), the repo-wide write lock has not (TODO.md, D1c). So the module
is built and gated on fixtures, `HELD_FOR_D1C` is True, pull() writes nothing and
says why, and the module is on no feeds roster. Lifting the hold is the
operator's ruling plus two edits: HELD_FOR_D1C = False and the module name in
altdata/feeds.py EXTERNAL_WRITERS (docs/briefs/st-r5-rates-notes.md).

SOURCE (verify item 5, checked 16 Oct 2026). The data center's downloads page
(www.redfin.com/news/data-center/downloads/, allowed by robots.txt's `*` group)
serves its files from the public bucket redfin-public-data.s3.us-west-2:
  redfin_data_center/housing_market/monthly/country.csv        ~55 KB
  redfin_data_center/housing_market/monthly/top_50_metros.csv  ~2.8 MB
Both monthly from January 2012, updated monthly (Last-Modified 12 Oct 2026 for
September 2026). The bucket answers robots.txt with 403, which RFC 9309 reads as
no rules. The older redfin_market_tracker/*.tsv000.gz files stopped at May 2026
(Last-Modified 2 Jun 2026) and are not read.

THE FIELDS, read by column name, never position:
  redfin.pending_sales       PENDING SALES, national (September 2026: 316,652,
                             the figure the order's read quotes)
  redfin.active_listings     ACTIVE LISTINGS, national
  redfin.inventory           INVENTORY, national
  redfin.months_of_supply    MONTHS OF SUPPLY, national, months (Redfin's own
                             definition, inventory over the month's sales -- not
                             NAR's, so not comparable to NAR's six-month line
                             without saying so)
  redfin.metro_pending_sales PENDING SALES per metro, instrument = REGION ID
"NA" is skipped, never zero.

AVAILABILITY. The bucket sends Last-Modified, so each file's rows are stamped
with it, `observed`. Redfin restates recent months, so the registry says
`revised` and a restated value is a new vintage row.
"""

from __future__ import annotations

import csv
import io
import logging
from typing import Optional

from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "redfin"
BASE = ("https://redfin-public-data.s3.us-west-2.amazonaws.com/"
        "redfin_data_center/housing_market/monthly/")
COUNTRY_URL = BASE + "country.csv"
METROS_URL = BASE + "top_50_metros.csv"

NATIONAL = {"PENDING SALES": "redfin.pending_sales",
            "ACTIVE LISTINGS": "redfin.active_listings",
            "INVENTORY": "redfin.inventory",
            "MONTHS OF SUPPLY": "redfin.months_of_supply"}
METRO_KEY = "redfin.metro_pending_sales"
KEYS = list(NATIONAL.values()) + [METRO_KEY]

HELD_FOR_D1C = True
HOLD_REASON = ("held for D1c: a new store writer waits for the repo-wide write "
               "lock (Track D precondition; TODO.md D1c)")

REQUIRED = ("PERIOD BEGIN", "REGION TYPE", "REGION ID", "PENDING SALES")


def _num(s: Optional[str]) -> Optional[float]:
    if s is None:
        return None
    s = s.strip().replace(",", "")
    if not s or s.upper() == "NA":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _reader(text: str) -> csv.DictReader:
    rd = csv.DictReader(io.StringIO(text.lstrip("﻿")))
    missing = [c for c in REQUIRED if c not in (rd.fieldnames or [])]
    if missing:
        raise ValueError(f"the Redfin file has no {missing} column(s)")
    return rd


def country_rows(text: str, available: str, kind: str) -> list[dict]:
    out = []
    for r in _reader(text):
        if (r.get("REGION TYPE") or "").strip().lower() != "country":
            continue
        day = (r.get("PERIOD BEGIN") or "")[:10]
        for col, key in NATIONAL.items():
            v = _num(r.get(col))
            if v is not None and len(day) == 10:
                out.append({"registry_key": key, "instrument": None,
                            "observed_at": day, "available_at": available,
                            "value": v, "availability_kind": kind})
    if not out:
        raise ValueError("no national rows in the Redfin country file")
    return out


def metro_rows(text: str, available: str, kind: str) -> list[dict]:
    out = []
    for r in _reader(text):
        if (r.get("REGION TYPE") or "").strip().lower() != "metro":
            continue
        day = (r.get("PERIOD BEGIN") or "")[:10]
        rid = (r.get("REGION ID") or "").strip()
        v = _num(r.get("PENDING SALES"))
        if v is not None and rid and len(day) == 10:
            out.append({"registry_key": METRO_KEY, "instrument": rid,
                        "observed_at": day, "available_at": available,
                        "value": v, "availability_kind": kind})
    if not out:
        raise ValueError("no metro rows in the Redfin top-50 file")
    return out


def fetch_rows() -> list[dict]:
    rows: list[dict] = []
    for url, fn in ((COUNTRY_URL, country_rows), (METROS_URL, metro_rows)):
        data, headers = http_get_response(url, timeout=120)
        available, kind = pub.availability(headers)
        rows.extend(fn(data.decode("utf-8"), available, kind))
    return rows


def pull(run_id: Optional[str] = None, db=None) -> dict:
    if HELD_FOR_D1C:
        return {"source": SOURCE, "status": "HELD", "written": 0,
                "reason": HOLD_REASON, "keys": KEYS}
    return pub.run(SOURCE, KEYS, fetch_rows, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
