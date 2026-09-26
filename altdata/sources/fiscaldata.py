"""
Monthly Statement of the Public Debt -- US Treasury Fiscal Data API.

    python -m altdata.sources.fiscaldata     # one pull, summary to stdout

Signal-triage order ST-1, feed row "MSPD net marketable issuance (fiscaldata.*)";
the supply leg of SR-23 (net duration supply to price-sensitive private hands)
and the input to ST-4's calc.net_supply_* features.

SOURCE. https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/debt/
mspd/mspd_table_1 -- no key. One row per (record_date, security class); record
dates are month-ends. Amounts are in MILLIONS and are stored in DOLLARS (x1e6):
the registry's `usd` unit, and the net-liquidity lesson in CLAUDE.md -- a units
field that has to be remembered is a units field that will be remembered wrong.

STORED, all "debt held by the public" (debt_held_public_mil_amt), monthly:

  fiscaldata.mspd_marketable_total        line "Total Marketable"
  fiscaldata.mspd_bills / _notes / _bonds / _tips / _frn
                                          the Marketable class rows; an older
                                          vintage's inflation-indexed notes and
                                          bonds are summed into _tips
  fiscaldata.mspd_net_marketable_issuance month-on-month change in
                                          mspd_marketable_total

-----------------------------------------------------------------------------
G-14 -- THE FIELD MAPPING FOR "NET MARKETABLE ISSUANCE", DECIDED 26 SEP 2026
-----------------------------------------------------------------------------

DECISION. Net marketable issuance for month m = Total Marketable debt held by the
public at the end of m minus the same at the end of m-1, from MSPD Table I. Held
by the public, not total outstanding: intragovernmental holdings are the
government lending to itself and are not supply to anyone. Marketable only:
nonmarketable debt (savings bonds, SLGS, the Government Account Series) is not
sold into the market.

WHAT IT IS NOT: THE REFUNDING'S HEADLINE. The quarterly refunding's "privately-held
net marketable borrowing" "excludes rollovers (auction 'add-ons') of Treasury
securities held in the SOMA but includes financing required due to SOMA
redemptions" (press release sb0584, 3 Aug 2026). MSPD's held-by-the-public counts
the Fed as public, so this series INCLUDES SOMA add-ons. It is also at par, or
accreted principal for TIPS, rather than cash raised, so it includes TIPS inflation
accrual, which raises no cash.

CHECKED AGAINST THE REFUNDING TABLES, April-June 2026:
    MSPD: 30,825.7bn (31 Mar) -> 31,065.3bn (30 Jun)  =  +239.6bn
    Refunding, privately-held net marketable borrowing  =  +190bn
    Gap ~50bn = SOMA auction add-ons beyond redemptions + TIPS accrual (non-cash).
Subtracting the change in SOMA Treasury holdings (fred.soma_treasuries, about
+104bn over the quarter) does NOT reproduce the refunding figure -- it gives about
136bn -- because TREAST also moves with the Fed's SECONDARY-market purchases, which
the refunding counts as privately held (the Fed bought from a private seller).

WHAT FOLLOWS FOR ST-4. SR-23's variable is "issuance minus central-bank net
purchases" -- what private hands had to absorb by ANY channel -- so ST-4's
calc.net_supply_* should be this series minus the change in fred.soma_treasuries,
and should NOT be compared with the refunding's privately-held figure as if the two
measured the same thing. Excluding TIPS accrual needs the TIPS auction amounts, not
the fiscaldata.mspd_tips level change (which mixes issuance and accrual); that is
ST-4's call. Recorded in docs/signal-triage-register.md under SR-23.

AVAILABILITY. MSPD is published around the fourth business day of the following
month; Fiscal Data serves no publication timestamp per row, so available_at is the
write instant (`ingest_instant`), an upper bound. The first pull backfills from
BACKFILL_START with every row stamped that day, which is late but never early.
"""

from __future__ import annotations

import datetime as dt
import logging
from collections import defaultdict
from typing import Optional

from .. import observations, session
from . import _publication as pub
from ._base import http_get_json

log = logging.getLogger(__name__)

SOURCE = "fiscaldata"
URL = ("https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/"
       "debt/mspd/mspd_table_1")
BACKFILL_START = "2001-01-01"
REFRESH_MONTHS = 14
MILLIONS = 1_000_000.0
PAGE = 10000

TOTAL_KEY = "fiscaldata.mspd_marketable_total"
NET_KEY = "fiscaldata.mspd_net_marketable_issuance"
CLASS_KEYS = {"bills": "fiscaldata.mspd_bills",
              "notes": "fiscaldata.mspd_notes",
              "bonds": "fiscaldata.mspd_bonds",
              "tips": "fiscaldata.mspd_tips",
              "frn": "fiscaldata.mspd_frn"}
KEYS = [TOTAL_KEY, *CLASS_KEYS.values(), NET_KEY]


def _bucket(cls: str) -> Optional[str]:
    c = cls.lower()
    if "inflation" in c:
        return "tips"
    if "floating" in c:
        return "frn"
    if "bill" in c:
        return "bills"
    if "note" in c:
        return "notes"
    if "bond" in c:
        return "bonds"
    return None           # Federal Financing Bank and anything new: not a class


def rows_from_records(records: list[dict], available: str) -> list[dict]:
    """Observation rows from MSPD Table I records. Raises if no total is present."""
    totals: dict[str, float] = {}
    classes: dict[str, dict[str, float]] = defaultdict(dict)
    for rec in records:
        day = str(rec.get("record_date") or "")[:10]
        typ = str(rec.get("security_type_desc") or "").strip()
        try:
            amt = float(rec.get("debt_held_public_mil_amt"))
        except (TypeError, ValueError):
            continue
        if len(day) != 10:
            continue
        if typ == "Total Marketable":
            totals[day] = amt * MILLIONS
        elif typ == "Marketable":
            b = _bucket(str(rec.get("security_class_desc") or ""))
            if b:
                classes[day][b] = classes[day].get(b, 0.0) + amt * MILLIONS
    if not totals:
        raise ValueError("no 'Total Marketable' rows in the MSPD response")
    base = {"instrument": None, "available_at": available,
            "availability_kind": "ingest_instant"}
    out: list[dict] = []
    days = sorted(totals)
    for i, day in enumerate(days):
        out.append(dict(base, registry_key=TOTAL_KEY, observed_at=day,
                        value=totals[day]))
        for b, v in classes.get(day, {}).items():
            out.append(dict(base, registry_key=CLASS_KEYS[b], observed_at=day,
                            value=v))
        if i:
            prev = dt.date.fromisoformat(days[i - 1])
            cur = dt.date.fromisoformat(day)
            # CONSECUTIVE MONTH-ENDS ONLY. A gap in the response would otherwise
            # turn two months' issuance into one month's.
            if (cur.year * 12 + cur.month) - (prev.year * 12 + prev.month) == 1:
                out.append(dict(base, registry_key=NET_KEY, observed_at=day,
                                value=totals[day] - totals[days[i - 1]]))
    return out


def _start(db: Optional[observations.ObservationStore]) -> str:
    own = db is None
    store = db or observations.ObservationStore()
    try:
        held = pub.newest_observed(store, [TOTAL_KEY])
    finally:
        if own:
            store.close()
    if not held.get(TOTAL_KEY):
        return BACKFILL_START
    today = session.session_date_obj()
    m = today.year * 12 + today.month - 1 - REFRESH_MONTHS
    return dt.date(m // 12, m % 12 + 1, 1).isoformat()


def fetch_records(start: str) -> list[dict]:
    records: list[dict] = []
    page = 1
    while True:
        data = http_get_json(URL, params={
            "filter": (f"record_date:gte:{start},"
                       f"security_type_desc:in:(Marketable,Total Marketable)"),
            "fields": ("record_date,security_type_desc,security_class_desc,"
                       "debt_held_public_mil_amt"),
            "sort": "record_date",
            "page[size]": PAGE, "page[number]": page}, timeout=60)
        records.extend(data.get("data") or [])
        total_pages = int(((data.get("meta") or {}).get("total-pages")) or 1)
        if page >= total_pages:
            return records
        page += 1


def pull(run_id: Optional[str] = None, db=None) -> dict:
    def produce() -> list[dict]:
        return rows_from_records(fetch_records(_start(db)),
                                 session.utc_iso(timespec="microseconds"))
    return pub.run(SOURCE, KEYS, produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
