"""
Leveraged-ETF assets -- ProShares' daily NAV history files.

    python -m altdata.sources.proshares      # one pull, summary to stdout

Signal-triage order ST-2 (SR-8 false-bottom audit, LEVETF_AUM; Market Structure's
leveraged-ETF rebalancing): the size of the daily-rebalanced leveraged book on the
S&P 500 and the Nasdaq-100.

SOURCE. https://accounts.profunds.com/etfdata/ByFund/<TICKER>-historical_nav.csv
-- the issuer's own file, no key, from each fund's inception, newest first:
  Date (MM/DD/YYYY), ProShares Name, Ticker, NAV, Prior NAV, NAV Change (%),
  NAV Change ($), Shares Outstanding (000), Assets Under Management
Republished around 00:20 GMT after each trading day, with Last-Modified.

FUNDS -- the largest ProShares leveraged and inverse products on the two indices:
  Nasdaq-100   TQQQ (3x), SQQQ (-3x), QLD (2x)
  S&P 500      UPRO (3x), SPXU (-3x), SSO (2x), SDS (-2x)

STORED, instrument = the ticker, observed_at = the NAV date:
  levetf.aum                 Assets Under Management, usd
  levetf.shares_outstanding  shares (the file's thousands x 1000)
  levetf.nav                 NAV per share, price. SPLIT-ADJUSTED in the file
                             (TQQQ's 2010 NAV reads 0.207) -- fine for a size
                             series, and the reason no price is derived from it

NOT COVERED: Direxion (SPXL, SPXS, TECL). Its holdings file carries only today's
shares outstanding and no NAV or history file exists (checked 26 Sep 2026), so
its AUM would be a forward-only product of two separately scraped numbers. Left
out rather than approximated; the ProShares set is the history.

AVAILABILITY. The file's Last-Modified, `observed`. NAVs are not revised
(revision_policy: never).
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

SOURCE = "proshares"
URL = "https://accounts.profunds.com/etfdata/ByFund/{ticker}-historical_nav.csv"
FUNDS = ("TQQQ", "SQQQ", "QLD", "UPRO", "SPXU", "SSO", "SDS")
KEYS = ["levetf.aum", "levetf.shares_outstanding", "levetf.nav"]


def rows_from_csv(text: str, ticker: str, available_at: str,
                  kind: str) -> list[dict]:
    reader = csv.DictReader(io.StringIO(text.lstrip("﻿")))
    fields = {f.strip() for f in reader.fieldnames or []}
    need = {"Date", "NAV", "Shares Outstanding (000)", "Assets Under Management"}
    if not need <= fields:
        raise ValueError(f"{ticker}: NAV file lacks {sorted(need - fields)}")
    out = []
    for rec in reader:
        rec = {(k or "").strip(): (v or "").strip() for k, v in rec.items()}
        try:
            day = dt.datetime.strptime(rec["Date"], "%m/%d/%Y").date().isoformat()
        except ValueError:
            continue
        vals = {}
        for key, col, scale in (("levetf.aum", "Assets Under Management", 1.0),
                                ("levetf.shares_outstanding",
                                 "Shares Outstanding (000)", 1000.0),
                                ("levetf.nav", "NAV", 1.0)):
            try:
                vals[key] = float(rec[col].replace(",", "")) * scale
            except (KeyError, ValueError):
                continue
        for key, v in vals.items():
            out.append({"registry_key": key, "instrument": ticker,
                        "observed_at": day, "available_at": available_at,
                        "value": v, "availability_kind": kind})
    return out


def _produce() -> list[dict]:
    rows: list[dict] = []
    for ticker in FUNDS:
        data, headers = http_get_response(URL.format(ticker=ticker), timeout=60)
        rows.extend(rows_from_csv(data.decode("utf-8", errors="replace"), ticker,
                                  *pub.availability(headers)))
    return rows


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
