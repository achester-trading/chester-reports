"""
iShares' bitcoin and ether trusts, AUM and shares outstanding, daily, for the
Alternative Assets Quarterly's crypto chapter (the ETF line) (b70-quarterly-
readers-2; D34 of 24 Oct 2026; B67 section 17).

    python -m altdata.sources.ishares_holdings [--dry-run]

LEVEL, NOT FLOW. These are the funds' net assets and shares outstanding as their
product pages state them. Farside's flow tables remain the flow source where they
are read, and a level is never printed as a flow: the registry descriptions and
the Quarterly's labels say "level". The float (bitcoin or ether held against the
supply) stays a listed gap: the pages carry a per-basket amount only (AQ-3).

TERMS. The existing source `ishares_trusts` ("public product pages, no key"),
re-read 25 Oct 2026: robots.txt (www.ishares.com) allows the product pages. The
same key-fact parser as altdata/sources/ishares_trusts.py (`fact`), and the same
browser-shaped project identity those pages require.

  ishares.ibit.aum      totalNetAssetsFundLevel, USD   (product 333011, IBIT)
  ishares.ibit.shares   sharesOutstanding             (IBIT)
  ishares.etha.aum      totalNetAssetsFundLevel, USD   (product 337614, ETHA)
  ishares.etha.shares   sharesOutstanding             (ETHA)

observed_at = the fact's own as-of date. available_at = the read instant
(ingest_instant). Probed 25 Oct 2026: both pages 200, both facts present.
"""
from __future__ import annotations

import logging
from typing import Optional

from .. import session
from . import _publication as pub
from . import _quarterly_common as qc
from ._base import http_get_response, http_get_text
from .ishares_trusts import HEADERS, fact

log = logging.getLogger(__name__)

SOURCE = "ishares_trusts"
FUNDS = {"ibit": "https://www.ishares.com/us/products/333011/ishares-bitcoin-trust-etf",
         "etha": "https://www.ishares.com/us/products/337614/ishares-ethereum-trust-etf"}
FACTS = {"aum": "totalNetAssetsFundLevel", "shares": "sharesOutstanding"}
KEYS = ["ishares.ibit.aum", "ishares.ibit.shares", "ishares.etha.aum",
        "ishares.etha.shares"]
LABEL = "level, not flow"


def _fetch(url: str, **kw):
    """Every request through THIS module's helpers (patchable by the gates)."""
    return qc.fetch(url, get=lambda u, **k: http_get_response(u, headers=HEADERS, **k),
                    get_text=lambda u: http_get_text(u, timeout=30), **kw)


def rows_from_page(fund: str, page: str, available_at: str) -> list[dict]:
    rows = []
    for field, name in FACTS.items():
        v, day = fact(page, name)
        rows.append({"registry_key": f"ishares.{fund}.{field}", "instrument": None,
                     "observed_at": day, "available_at": available_at, "value": v,
                     "availability_kind": "ingest_instant"})
    return rows


def _produce() -> list[dict]:
    rows: list[dict] = []
    for fund, url in FUNDS.items():
        data, _h = _fetch(url)
        rows += rows_from_page(fund, data.decode("utf-8", "replace"),
                               session.utc_iso(timespec="microseconds"))
    return rows


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    raise SystemExit(qc.main(pull))
