"""
FINRA margin statistics -- customer debit balances in margin accounts, monthly.

    python -m altdata.sources.finra          # one pull, summary to stdout

Signal-triage order ST-2 (SR-8, the false-bottom audit's MARGIN_z): leverage in
the retail and institutional margin book. Not the `finra.*` short-interest family
already in the registry -- those come from the short-interest loggers; this is
the margin-statistics release, keyed finra.margin_*.

SOURCE. https://www.finra.org/rules-guidance/key-topics/margin-accounts/
margin-statistics links "margin-statistics.xlsx"; the link is found on the page
each run. Stdlib .xlsx reader, sheet "Customer Margin Balances": Year-Month
("2026-08"), then MILLIONS OF DOLLARS, newest first, back to 1997.

STORED in DOLLARS (millions x 1e6), observed_at = the month's end:
  finra.margin_debit              Debit Balances in Customers' Securities Margin
                                  Accounts
  finra.margin_free_credit_cash   Free Credit Balances in Customers' Cash Accounts
  finra.margin_free_credit_margin Free Credit Balances in Customers' Securities
                                  Margin Accounts
Columns are matched by header text.

AVAILABILITY. Published about three weeks after month-end; available_at is the
file's Last-Modified when sent, else the write instant. FINRA restates recent
months occasionally; revision_policy: revised.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Optional

from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "finra_margin"
PAGE = ("https://www.finra.org/rules-guidance/key-topics/margin-accounts/"
        "margin-statistics")
LINK = r"margin-statistics\.xlsx"
SHEET = "Customer Margin Balances"
MILLIONS = 1e6
MATCH = {"finra.margin_debit": ("debit balances",),
         "finra.margin_free_credit_cash": ("free credit", "cash account"),
         "finra.margin_free_credit_margin": ("free credit", "margin account")}
KEYS = list(MATCH)


def rows_from_table(table: list[list[Any]], available_at: str,
                    kind: str) -> list[dict]:
    if not table:
        raise ValueError(f"sheet {SHEET!r} is empty")
    header = [str(h or "").lower() for h in table[0]]
    cols = {}
    for key, needles in MATCH.items():
        hit = [j for j, h in enumerate(header) if all(n in h for n in needles)]
        if not hit:
            raise ValueError(f"no column for {key} in {header}")
        cols[key] = hit[0]
    out = []
    for row in table[1:]:
        m = re.fullmatch(r"(\d{4})-(\d{2})", str(row[0] or "").strip()) if row else None
        if not m:
            continue
        day = pub.month_end(int(m.group(1)), int(m.group(2)))
        for key, j in cols.items():
            v = row[j] if j < len(row) else None
            if isinstance(v, float):
                out.append({"registry_key": key, "instrument": None,
                            "observed_at": day, "available_at": available_at,
                            "value": v * MILLIONS, "availability_kind": kind})
    return out


def _produce() -> list[dict]:
    url = pub.find_link(PAGE, LINK)
    data, headers = http_get_response(url, timeout=90)
    return rows_from_table(pub.read_xlsx(data)[SHEET], *pub.availability(headers))


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
