"""
ETH burn and issuance from Blockscout's public API -- a FIELD CHECK, for the
Alternative Assets Quarterly's crypto chapter (the supply line)
(b70-quarterly-readers-2; D34 of 24 Oct 2026; B67 section 15).

    python -m altdata.sources.blockscout_supply [--dry-run]

B67 asked the build to confirm the fields exist. They do not: Blockscout's
/api/v2/stats (probed 25 Oct 2026, HTTP 200) carries average_block_time,
coin_price, gas_prices, gas_used_today, market_cap, network_utilization_
percentage, total_addresses, total_blocks, total_transactions,
transactions_today and tvl -- no burnt fees and no issuance. Etherscan's key is
not registered (CLAUDE.md, Tranche A part 1).

So the three keys are registered not_yet_sourced, and this reader only CHECKS:
each pull reads the stats once and, finding none of BURN_FIELDS, returns PENDING
with the field list, writing nothing. If one appears, it returns STALE naming it:
a field's meaning is never guessed, and its parser is the operator's ruling.

  eth.burn_daily       ETH burnt in the UTC day           (not yet sourced)
  eth.issuance_daily   ETH issued in the UTC day          (not yet sourced)
  eth.net_issuance     issuance less burn                 (not yet sourced)

TERMS. The existing `blockscout` source ("public explorer API, no key"); robots.txt
(eth.blockscout.com) allows / (re-read 25 Oct 2026).
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from . import _publication as pub
from . import _quarterly_common as qc
from ._base import http_get_response, http_get_text

log = logging.getLogger(__name__)

SOURCE = "blockscout"
URL = "https://eth.blockscout.com/api/v2/stats"
KEYS = ["eth.burn_daily", "eth.issuance_daily", "eth.net_issuance"]
BURN_FIELDS = ("burnt_fees", "burnt_fees_today", "total_burnt", "burnt",
               "issuance", "eth_issuance", "emission")


def _fetch(url: str, **kw):
    return qc.fetch(url, get=lambda u, **k: http_get_response(u, **k),
                    get_text=lambda u: http_get_text(u, timeout=30), **kw)


def field_check(stats: dict) -> tuple[str, str]:
    """(status, reason): PENDING with the fields when none is a burn field, else
    STALE naming the one that appeared."""
    if not isinstance(stats, dict):
        return pub.STALE, "the stats response is not an object"
    found = sorted(f for f in stats if any(b in f.lower() for b in BURN_FIELDS))
    if found:
        return pub.STALE, (f"a supply field appeared ({', '.join(found)}); its parser "
                           f"is not built -- the operator rules on its meaning")
    return pub.PENDING, ("Blockscout's /api/v2/stats carries no burn or issuance field "
                         f"(fields: {', '.join(sorted(stats))}); not tracked")


def pull(run_id: Optional[str] = None, db=None) -> dict:
    try:
        data, _h = _fetch(URL)
        status, reason = field_check(json.loads(data.decode("utf-8")))
    except Exception as exc:                                  # noqa: BLE001
        return pub.stale(SOURCE, KEYS, f"{type(exc).__name__}: {exc}", db=db,
                         run_id=run_id)
    if status == pub.PENDING:
        return pub.pending(SOURCE, reason, run_id)
    return pub.stale(SOURCE, KEYS, reason, db=db, run_id=run_id)


if __name__ == "__main__":
    raise SystemExit(qc.main(pull))
