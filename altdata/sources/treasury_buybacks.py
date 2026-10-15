"""
Treasury buyback operations -- US Treasury Fiscal Data API.

    python -m altdata.sources.treasury_buybacks   # one pull, summary to stdout

Signal-triage batch 3, ST-B3-04 (SR-33, Treasury long-end buybacks as a
yield-management lever). Each operation's result: date, sector, maximum, amount
accepted -- from which the bought/max ratio and the 30-year's next-session change
are computed at read time (altdata/batch3.py), never stored.

SOURCE. https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/
accounting/od/buybacks_operations -- no key. The API host answers robots.txt with
404 (no rules) and fiscaldata.treasury.gov's robots.txt is `Allow: /` (checked 13
Oct 2026). TreasuryDirect's own results pages are NOT read: its robots.txt
disallows every agent but `usasearch`. One row per operation, history from 9 March
2000; amounts in DOLLARS (par), as served:

  operation_date          the operation's date
  operation_type          "Liquidity Support" | "Cash Management"
  security_type           "Nominal Coupons" | "TIPS"
  maturity_bucket         "10Y to 20Y", "20Y to 30Y", ...
  max_par_amt_redeemed    the announced maximum
  total_par_amt_accepted  the amount bought
  total_par_amt_offered   the amount dealers offered

STORED, instrument = "<operation type> | <security type> | <maturity bucket>",
observed_at = the operation date, DOLLARS:

  treasury.buyback_max        the maximum
  treasury.buyback_accepted   the amount bought
  treasury.buyback_offered    the amount offered

A ROW THAT LACKS ITS MAXIMUM OR ITS AMOUNT IS SKIPPED, and a response with no
usable row is a failure (STALE), never an empty reading.

AVAILABILITY. Fiscal Data serves no publication timestamp, so available_at is the
write instant (`ingest_instant`): an upper bound, late but never early. The
results are announced shortly after the 14:00 ET close of the operation and the
16:10 pass reads them the same day.
"""

from __future__ import annotations

import logging
from typing import Optional

from . import _publication as pub
from ._base import http_get_json

log = logging.getLogger(__name__)

SOURCE = "treasury_buybacks"
URL = ("https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/"
       "accounting/od/buybacks_operations")
PAGE = 10000
FIELDS = ("operation_date", "operation_type", "security_type", "maturity_bucket",
          "max_par_amt_redeemed", "total_par_amt_accepted", "total_par_amt_offered")
MAX_KEY = "treasury.buyback_max"
ACCEPTED_KEY = "treasury.buyback_accepted"
OFFERED_KEY = "treasury.buyback_offered"
KEYS = ["treasury.buyback_max", "treasury.buyback_accepted",
        "treasury.buyback_offered"]


def instrument_of(rec: dict) -> str:
    return " | ".join(str(rec.get(k) or "").strip()
                      for k in ("operation_type", "security_type", "maturity_bucket"))


def _num(v) -> Optional[float]:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if f != f else f


def rows_from_records(records: list[dict], available_at: str,
                      kind: str = "ingest_instant") -> list[dict]:
    """Observation rows from the operations records. Raises when the records
    lack the fields this writer reads (a changed shape is a failure)."""
    if records and not set(FIELDS) <= set(records[0]):
        raise ValueError(f"buyback records lack {sorted(set(FIELDS) - set(records[0]))}")
    out: list[dict] = []
    for rec in records:
        day = str(rec.get("operation_date") or "")[:10]
        mx, acc = _num(rec.get("max_par_amt_redeemed")), _num(rec.get("total_par_amt_accepted"))
        if len(day) != 10 or mx is None or acc is None:
            continue
        inst = instrument_of(rec)
        for key, v in ((MAX_KEY, mx), (ACCEPTED_KEY, acc),
                       (OFFERED_KEY, _num(rec.get("total_par_amt_offered")))):
            if v is None:
                continue
            out.append({"registry_key": key, "instrument": inst, "observed_at": day,
                        "available_at": available_at, "value": v,
                        "availability_kind": kind})
    if not out:
        raise ValueError("no buyback operation with a maximum and an amount")
    return out


def _produce() -> list[dict]:
    from .. import session                                      # noqa: PLC0415
    recs: list[dict] = []
    page = 1
    while True:
        j = http_get_json(URL, params={"fields": ",".join(FIELDS),
                                       "sort": "operation_date",
                                       "page[size]": PAGE, "page[number]": page},
                          timeout=90)
        recs += j.get("data") or []
        if page >= int(((j.get("meta") or {}).get("total-pages")) or 1):
            break
        page += 1
    return rows_from_records(recs, session.utc_iso(timespec="microseconds"))


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
