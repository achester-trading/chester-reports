"""
The treasury companies -- the `treasury.*` family: the inputs of item 49's mNAV
(ST-R6.49a) and treasury net purchases (ST-R6.49b) (Batch 8, docs/change-order-
signal-triage-batch-8-2026-10-17.md; digital-49-51b, 17 Oct 2026). The derived
series (calc.mnav, calc.treasury_net_purchases) are altdata/sources/
crypto_derived.py's. Config: config/crypto_sources.yaml `treasury`.

    python -m altdata.sources.treasury        # one pull
    python -m altdata.sources.treasury show   # READ ONLY: the latest mNAV and inputs

THE SOURCES, keyless and within robots (Batch 8 filing note 4; the standing rule
of 16 Oct: no registration is pursued):

  HOLDINGS   https://treasuries.bitbo.io/ (BitcoinTreasuries.com) -- the "Public
             Companies that Own Bitcoin" table: entity, Symbol:Exchange, # of BTC.
             robots.txt allows it (only /private/ and /junk/ are disallowed, and
             all of it for GPTBot); the site publishes no terms page.
               treasury.btc_holdings   BTC held, instrument = the ticker (the part
                                       of Symbol:Exchange before the colon), the
                                       top companies by holdings (config `top`),
                                       filed under the pull's UTC day
  SHARES     Strategy's filings' stated share count, from SEC EDGAR's XBRL API
             (data.sec.gov/api/xbrl/companyconcept/CIK0001050446/dei/
             EntityCommonStockSharesOutstanding.json), read with the repo's EDGAR
             contact (CHESTER_SEC_CONTACT; altdata/sources/edgar.py) -- EDGAR
             refuses any User-Agent without one. Without it the share count is a
             listed gap and mNAV prints "not tracked".
               treasury.mstr_shares    shares outstanding as the latest filing
                                       states them, filed under the fact's `end`
                                       date
  PRICE      MSTR's spot from the session's newest captured option chain (MSTR is
             a watched name, altdata/config.py SINGLE_NAMES; data/chains/<day>/
             MSTR_*.csv). Read from local files, nothing fetched. The capture's
             spot, not the official close.
               treasury.mstr_spot      instrument MSTR, filed under the session

REFUSED, AND WHY: www.strategy.com answers this client 403 (robots.txt included);
bitcointreasuries.net's terms of service forbid scraping or extracting its data
by automated systems, so its pages are not read, robots.txt notwithstanding.

Nothing here is typed in by hand: a figure a source does not serve is a gap.
"""

from __future__ import annotations

import datetime as dt
import io
import logging
import re
from pathlib import Path
from typing import Any, Callable, Optional

from . import _crypto as C
from . import _publication as pub
from ._base import FetchError, http_get_json, http_get_text

log = logging.getLogger(__name__)

SOURCE = "treasury_companies"
KEYS = ["treasury.btc_holdings", "treasury.mstr_shares", "treasury.mstr_spot"]
BITBO = "https://treasuries.bitbo.io/"
AGENT = "chester-reports"
MSTR_CIK = "0001050446"
SHARES_URL = ("https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/dei/"
              "EntityCommonStockSharesOutstanding.json")


def _robots(url: str) -> str:
    try:
        return http_get_text(url, timeout=30)
    except FetchError as exc:
        if "HTTP 4" in str(exc):
            return ""
        raise


def robots_ok(get: Callable[[str], str] = _robots) -> tuple[bool, str]:
    from .aaii import robots_verdict                             # noqa: PLC0415
    ok, rule = robots_verdict(get("https://treasuries.bitbo.io/robots.txt"), "/", AGENT)
    return ok, ("" if ok else f"treasuries.bitbo.io robots.txt refuses / ({rule})")


# ---------------------------------------------------------------------------
# Parsers -- pure, on tests/fixtures/treasury/
# ---------------------------------------------------------------------------
def parse_holdings(html: str, top: int = 20) -> list[dict]:
    """The table carrying 'Symbol:Exchange' and '# of BTC' -> [{ticker, entity,
    btc}], largest first, the first `top`."""
    import pandas as pd                                          # noqa: PLC0415
    for t in pd.read_html(io.StringIO(html)):
        cols = [str(c).strip() for c in t.columns]
        if "Symbol:Exchange" in cols and "# of BTC" in cols:
            out = []
            for _, r in t.iterrows():
                sym = str(r["Symbol:Exchange"] or "").split(":")[0].strip()
                btc = C.num(str(r["# of BTC"]).replace(",", ""))
                if sym and sym.lower() != "nan" and btc is not None:
                    out.append({"ticker": sym, "entity": str(r.get("Entity")), "btc": btc})
            out.sort(key=lambda x: -x["btc"])
            return out[:top]
    raise ValueError("bitbo: no table with Symbol:Exchange and # of BTC")


def parse_shares(doc: dict) -> Optional[tuple[str, float, str]]:
    """companyconcept: units.shares [{end, val, filed, form, accn}] -> the fact of
    the latest filing (end date, shares, filed)."""
    facts = ((doc or {}).get("units") or {}).get("shares") or []
    facts = [f for f in facts if f.get("end") and C.num(f.get("val")) is not None]
    if not facts:
        return None
    f = max(facts, key=lambda f: (str(f.get("filed")), str(f.get("end"))))
    return str(f["end"])[:10], float(f["val"]), str(f.get("filed"))


def chain_spot(day: str, base: Optional[Path] = None, symbol: str = "MSTR"
               ) -> Optional[tuple[float, str]]:
    """(spot, fetched_at) from the session's newest captured chain of `symbol`."""
    from altdata import chain_metrics                            # noqa: PLC0415
    d = (base or chain_metrics.chain_dir()) / day
    files = sorted(p for p in d.glob(f"{symbol}_*.csv") if "_quality" not in p.name) \
        if d.is_dir() else []
    if not files:
        return None
    rows = chain_metrics.load_rows(files[-1])
    spot = next((r["spot"] for r in rows if r.get("spot")), None)
    return (spot, next((r["fetched_at"] for r in rows if r.get("fetched_at")), "")) \
        if spot else None


# ---------------------------------------------------------------------------
def collect(get_html: Callable[[str], str] = None, get_json: Callable[..., Any] = None,
            *, robots: Optional[Callable[[], tuple]] = None,
            user_agent: Optional[Callable[[], Optional[str]]] = None,
            chain_base: Optional[Path] = None, days: int = 7,
            today: Optional[str] = None, now: Optional[str] = None
            ) -> tuple[list[dict], dict]:
    cfg = C.config().get("treasury") or {}
    get_html = get_html or (lambda u: http_get_text(u, timeout=60))
    get_json = get_json or (lambda u, h: http_get_json(u, timeout=60, headers=h))
    today = today or C.today_utc()
    now = now or C.now_iso()
    rows: list[dict] = []
    summary: dict = {"series": {}, "failed": [], "gaps": []}
    # 1. holdings
    try:
        ok, why = (robots or robots_ok)()
        if not ok:
            raise PermissionError(why)
        hold = parse_holdings(get_html(cfg.get("holdings_url") or BITBO),
                              int(cfg.get("top") or 20))
        rows += [C.row("treasury.btc_holdings", today, h["btc"], now, SOURCE, h["ticker"])
                 for h in hold]
        summary["series"]["holdings"] = len(hold)
    except Exception as exc:                                    # noqa: BLE001
        summary["failed"].append(("holdings", f"{type(exc).__name__}: {exc}"[:240]))
    # 2. Strategy's share count, from its filings (EDGAR, the operator's contact)
    if user_agent is None:
        from . import edgar                                      # noqa: PLC0415
        user_agent = edgar.user_agent
    ua = user_agent()
    if not ua:
        summary["gaps"].append(("treasury.mstr_shares", "EDGAR needs CHESTER_SEC_CONTACT "
                                "(not set here); mNAV prints \"not tracked\""))
    else:
        try:
            sh = parse_shares(get_json(SHARES_URL.format(cik=MSTR_CIK), {"User-Agent": ua}))
            if sh is None:
                summary["gaps"].append(("treasury.mstr_shares",
                                        "no dimensionless share-count fact in EDGAR"))
            else:
                rows.append(C.row("treasury.mstr_shares", sh[0], sh[1], now, SOURCE))
                summary["series"]["shares"] = {"end": sh[0], "filed": sh[2]}
        except Exception as exc:                                # noqa: BLE001
            summary["failed"].append(("shares", f"{type(exc).__name__}: {exc}"[:240]))
    # 3. MSTR's spot from the captured chains (local files)
    n = 0
    for k in range(days):
        day = (dt.date.fromisoformat(today) - dt.timedelta(days=k)).isoformat()
        sp = chain_spot(day, chain_base)
        if sp:
            rows.append(C.row("treasury.mstr_spot", day, sp[0], now, SOURCE, "MSTR"))
            n += 1
    summary["series"]["mstr_spot"] = n
    if not n:
        summary["gaps"].append(("treasury.mstr_spot", "no MSTR chain captured in the "
                                f"last {days} days"))
    return rows, summary


def pull(run_id: Optional[str] = None, db=None, **kw) -> dict:
    state: dict = {}

    def produce() -> list[dict]:
        rows, s = collect(**kw)
        state.update(s)
        if not rows and s["failed"]:
            raise RuntimeError("; ".join(f"{k}: {v}" for k, v in s["failed"])[:300])
        return rows
    out = pub.run(SOURCE, KEYS, produce, run_id=run_id, db=db)
    out["failed_series"] = state.get("failed") or []
    out["gaps"] = state.get("gaps") or []
    return out


def show(db_path: Optional[str] = None, as_of: Optional[str] = None) -> dict:
    """READ ONLY: the latest mNAV and its inputs, for the MSTR/MSCI event watch
    (Batch 8, 17 Oct 2026: the watch reads mNAV from the box's store). Opens the
    store, writes nothing."""
    from .. import observations as obs                          # noqa: PLC0415
    out: dict = {}
    with obs.open_writer(__name__, db_path) as st:
        for key, inst in (("calc.mnav", "MSTR"), ("treasury.mstr_spot", "MSTR"),
                          ("treasury.mstr_shares", None), ("treasury.btc_holdings", "MSTR"),
                          ("yfinance.mkt_btc_usd", None),
                          ("calc.treasury_net_purchases", None)):
            r = st.latest_as_of(key, as_of, inst)
            out[key] = ({"observed_at": str(r["observed_at"])[:10], "value": r["value_num"],
                         "available_at": r["available_at"]} if r else None)
    m = out.get("calc.mnav")
    if m:
        out["lines"] = {"watch_1_2": m["value"] <= 1.2, "flag_1_0": m["value"] <= 1.0}
    return out


if __name__ == "__main__":
    import json
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    if sys.argv[1:2] == ["show"]:
        print(json.dumps(show(), indent=2, sort_keys=True, default=str))
    else:
        print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
