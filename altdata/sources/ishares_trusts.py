"""
iShares Gold (IAU), Silver (SLV) and Bitcoin (IBIT) trusts -- metal held, shares
outstanding, and the share flow.

    python -m altdata.sources.ishares_trusts     # one pull, summary to stdout

AQ-3 part 1 (11 Oct 2026; change order sections 4.2 and 4.6, and section 10A's
standard: ETF flows from share counts, never from AUM). The other half of gold's
ETF tonnage beside GLD (altdata/sources/spdr_gld.py), silver's, and the share
count the crypto chapter's "ETF flows read against float" needs for IBIT.

SOURCE. Each trust's product page on ishares.com, no key. The page embeds the
fund's key facts as JSON (HTML-escaped) -- objects with a label, a formatted
value, an as-of date and a name -- and the writer reads three by NAME:
  sharesOutstanding   "Shares Outstanding"        every trust
  ounces              "Ounces in Trust"           IAU, SLV
  tonnes              "Tonnes in Trust"           IAU, SLV
ishares.com's robots.txt (read 11 Oct 2026) disallows search, sign-on and
"?truepdf"-style paths, not product pages. IBIT publishes no bitcoin-held
figure on the page beyond the per-basket amount, so it carries shares only.

FORWARD-ONLY. The page serves today's facts, not a history: each run stores the
as-of date it shows, and the series begins with the first run. (iShares' fund
downloads carry holdings, not a shares-outstanding history.)

STORED, observed_at = the page's as-of date ("Oct 09, 2026"):
  etf.iau_oz, etf.iau_tonnes, etf.iau_shares, etf.iau_share_flow
  etf.slv_oz, etf.slv_tonnes, etf.slv_shares, etf.slv_share_flow
  etf.ibit_shares, etf.ibit_share_flow
The flow is the change in shares outstanding from the last stored count before
this as-of date -- a share count, never dollars -- and is not written for a
trust's first stored day.

AVAILABILITY. The write instant (`ingest_instant`): the page carries no
publication time. One trust whose page fails to read fails the run -- the three
are one publisher and one shape, and a partial run would hide which key went
stale.
"""

from __future__ import annotations

import datetime as dt
import html as _html
import logging
import re
from typing import Optional

from .. import observations, session
from . import _publication as pub
from ._base import http_get_text
from .user_agent import browser_like

log = logging.getLogger(__name__)

SOURCE = "ishares_trusts"
TRUSTS = {
    "iau": ("https://www.ishares.com/us/products/239561/ishares-gold-trust-fund",
            ("oz", "tonnes", "shares")),
    "slv": ("https://www.ishares.com/us/products/239855/ishares-silver-trust-fund",
            ("oz", "tonnes", "shares")),
    "ibit": ("https://www.ishares.com/us/products/333011/ishares-bitcoin-trust-etf",
             ("shares",)),
}
FIELD_NAMES = {"oz": "ounces", "tonnes": "tonnes", "shares": "sharesOutstanding"}
KEYS = [f"etf.{t}_{f}" for t, (_u, fields) in TRUSTS.items() for f in fields] + [
    f"etf.{t}_share_flow" for t in TRUSTS]
HEADERS = {"User-Agent": browser_like()}


def fact(page: str, name: str) -> tuple[float, str]:
    """(value, ISO as-of date) of the key-fact object named `name`. Raises when
    the page has no such object -- a page that changed shape."""
    text = _html.unescape(page)
    m = re.search(r'"formattedValue":"([^"]*)"(?:(?!"formattedValue").)*?'
                  r'"formattedAsOfDate":"([^"]*)","name":"' + re.escape(name) + '"',
                  text, re.S)
    if not m:
        raise ValueError(f"the page has no '{name}' key fact")
    value = float(m.group(1).replace(",", ""))
    day = dt.datetime.strptime(m.group(2).strip(), "%b %d, %Y").date().isoformat()
    return value, day


def rows_from_page(trust: str, page: str, available_at: str,
                   prior_shares: Optional[float]) -> list[dict]:
    fields = TRUSTS[trust][1]
    out: list[dict] = []
    shares_day = None
    for f in fields:
        v, day = fact(page, FIELD_NAMES[f])
        out.append({"registry_key": f"etf.{trust}_{f}", "instrument": None,
                    "observed_at": day, "available_at": available_at, "value": v,
                    "availability_kind": "ingest_instant"})
        if f == "shares":
            shares_day, shares = day, v
    if shares_day and prior_shares is not None:
        out.append({"registry_key": f"etf.{trust}_share_flow", "instrument": None,
                    "observed_at": shares_day, "available_at": available_at,
                    "value": shares - prior_shares,
                    "availability_kind": "ingest_instant"})
    return out


def prior_shares(db, trust: str, before: str) -> Optional[float]:
    """The last stored share count dated before `before`."""
    row = db.conn.execute(
        "SELECT value_num FROM observations WHERE registry_key = ? AND observed_at < ?"
        " ORDER BY observed_at DESC, available_at DESC LIMIT 1",
        (f"etf.{trust}_shares", before)).fetchone()
    return float(row[0]) if row and row[0] is not None else None


def pull(run_id: Optional[str] = None, db=None) -> dict:
    def produce() -> list[dict]:
        now = session.utc_iso(timespec="microseconds")
        pages = {t: http_get_text(url, timeout=60, headers=HEADERS)
                 for t, (url, _f) in TRUSTS.items()}
        own = db is None
        store = db or observations.open_writer(__name__)
        try:
            rows: list[dict] = []
            for t, page in pages.items():
                _v, day = fact(page, FIELD_NAMES["shares"])
                rows += rows_from_page(t, page, now, prior_shares(store, t, day))
            return rows
        finally:
            if own:
                store.close()
    return pub.run(SOURCE, KEYS, produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
