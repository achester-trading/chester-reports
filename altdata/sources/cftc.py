"""
CFTC Commitments of Traders -- legacy, disaggregated and TFF futures-only
reports, Socrata API.

    python -m altdata.sources.cftc           # one pull, summary to stdout

Signal-triage order ST-2 (§2.2.2, SR-2): speculative positioning in the yen and
the dollar index, the input to calc.jpy_pos_z (ST-5) and to the candidate
`carry_vs_vol` contradiction row. This is the source behind the `cftc` switch in
config.ENABLED_SOURCES, which ST-2 turns on; the switch is honoured here -- off
means STALE with that reason, never a silent skip.

SOURCE. https://publicreporting.cftc.gov/resource/6dca-aqww.json -- no key.
One record per contract per report week, back to 1986:
  097741  JAPANESE YEN - CHICAGO MERCANTILE EXCHANGE
  098662  USD INDEX - ICE FUTURES U.S.

STORED, per contract (instrument = "JPY" or "USD_INDEX"), observed_at = the
TUESDAY the positions are as of:
  cftc.noncomm_long, cftc.noncomm_short   contracts
  cftc.noncomm_net                         long minus short, the report's own
                                           two columns -- an identity within one
                                           record, not a feature
  cftc.open_interest                       contracts

THE DISAGGREGATED AND TFF REPORTS (AQ-3 part 1, 11 Oct 2026; the change
order's flows-and-positioning standard, section 10A). The legacy non-commercial
series above are untouched. Beside them, from the same Socrata host, no key:
  72hh-3qpy  Disaggregated, futures only -- GOLD, SILVER, COPPER, WTI, NATGAS:
             producer/merchant, swap dealer, managed money, other reportables
  gpe5-46if  Traders in Financial Futures, futures only -- the six currency
             futures EUR, JPY, GBP, CHF, CAD, AUD and (SR-36) the six Treasury
             futures TU, FV, TY, TN, US, WN: dealer, asset manager, leveraged
             funds, other reportables
Each category is stored long, short and net (contracts), and each of the three
ALSO as a share of the record's open interest, in percent (`_oi` keys) --
positions scaled to OI, the standard's rule, so a category's weight compares
across contracts and across years of different OI. Spread positions are not
stored. Both datasets start 13 Jun 2006 and each pull reads a contract's whole
history from the API, so the first pull is the backfill; the CFTC's annual
historical files carry the same records and are not needed.

AVAILABILITY. The report is released on the FRIDAY after the Tuesday, 15:30 ET.
available_at = that Friday 15:30 ET, `reconstructed`. A federal holiday pushes the
release to the next business day; on those weeks the stamp is early by a day or
more. The date is the order's rule; the holiday shift is not modelled because the
release calendar is not in the repo -- the one known imprecision. Positions are
not revised once published (revision_policy: never).
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Optional

from .. import config, observations, session
from . import _publication as pub
from ._base import http_get_json

log = logging.getLogger(__name__)

SOURCE = "cftc"
URL = "https://publicreporting.cftc.gov/resource/6dca-aqww.json"
# Contract market code -> instrument. The S&P 500 consolidated, the 10-year note
# and VIX futures were added 3 Oct 2026 (T2 ruling 4), codes read from the
# CFTC's own Legacy Futures Only dataset that day: 13874+ "S&P 500 Consolidated
# - CHICAGO MERCANTILE EXCHANGE", 043602 "UST 10Y NOTE - CHICAGO BOARD OF
# TRADE", 1170E1 "VIX FUTURES - CBOE FUTURES EXCHANGE". Each pull reads a
# contract's whole history, so a contract added here arrives complete.
CONTRACTS = {"097741": "JPY", "098662": "USD_INDEX", "13874+": "SP500",
             "043602": "UST10Y", "1170E1": "VIX",
             # T2.2 (4 Oct 2026, item 13): the W4 panel's other five, codes read
             # from the CFTC API's market names that day. Russell has no
             # consolidated contract; the E-mini is the benchmark one.
             "20974+": "NDX100",     # NASDAQ-100 Consolidated
             "239742": "RUSSELL2000",  # RUSSELL E-MINI
             "020601": "UST30Y",     # UST BOND (CBOT)
             "088691": "GOLD",       # GOLD (COMEX)
             "067651": "WTI"}        # WTI-PHYSICAL (NYMEX)
RELEASE_ET = dt.time(15, 30)
PAGE = 5000

LEGACY_KEYS = ["cftc.noncomm_long", "cftc.noncomm_short", "cftc.noncomm_net",
               "cftc.open_interest"]

# THE DISAGGREGATED AND TFF REPORTS. Codes read from each dataset on 11 Oct 2026
# (GOLD / SILVER / COPPER- #1 - COMMODITY EXCHANGE INC.; WTI-PHYSICAL and NAT GAS
# NYME - NEW YORK MERCANTILE EXCHANGE; EURO FX, JAPANESE YEN, BRITISH POUND,
# SWISS FRANC, CANADIAN DOLLAR, AUSTRALIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE).
DISAGG_URL = "https://publicreporting.cftc.gov/resource/72hh-3qpy.json"
TFF_URL = "https://publicreporting.cftc.gov/resource/gpe5-46if.json"
DISAGG_CONTRACTS = {"088691": "GOLD", "084691": "SILVER", "085692": "COPPER",
                    "067651": "WTI", "023651": "NATGAS"}
TFF_CONTRACTS = {"099741": "EUR", "097741": "JPY", "096742": "GBP",
                 "092741": "CHF", "090741": "CAD", "232741": "AUD",
                 # SR-36 (ST-B3-12, 11 Oct 2026): the six CBOT Treasury futures
                 # for the basis-trade proxy (altdata/basis_proxy.py), codes read
                 # from gpe5-46if that day. Instrument = the CME ticker. 020604
                 # is the Ultra bond, named "LONG-TERM U.S. TREASURY BONDS" from
                 # its first report (2 Mar 2010) to 7 Jun 2016; 043607, the
                 # Ultra 10-year, starts 8 Mar 2016.
                 "042601": "TU", "044601": "FV", "043602": "TY",
                 "043607": "TN", "020601": "US", "020604": "WN"}
# category -> (long column, short column), the dataset's own names. The
# disaggregated swap-short column is spelled with two underscores at source.
DISAGG_CATEGORIES = {
    "prod_merc": ("prod_merc_positions_long", "prod_merc_positions_short"),
    "swap": ("swap_positions_long_all", "swap__positions_short_all"),
    "managed_money": ("m_money_positions_long_all", "m_money_positions_short_all"),
    "other_rept": ("other_rept_positions_long", "other_rept_positions_short")}
TFF_CATEGORIES = {
    "dealer": ("dealer_positions_long_all", "dealer_positions_short_all"),
    "asset_mgr": ("asset_mgr_positions_long", "asset_mgr_positions_short"),
    "lev_money": ("lev_money_positions_long", "lev_money_positions_short"),
    "other_rept": ("other_rept_positions_long", "other_rept_positions_short")}
SIDES = ("long", "short", "net")


def category_keys(report: str, categories) -> list:
    """cftc.<report>_<category>_<side>, its _oi share, and the report's OI."""
    return ([f"cftc.{report}_{c}_{s}" for c in categories for s in SIDES]
            + [f"cftc.{report}_{c}_{s}_oi" for c in categories for s in SIDES]
            + [f"cftc.{report}_open_interest"])


DISAGG_KEYS = category_keys("dis", DISAGG_CATEGORIES)
TFF_KEYS = category_keys("tff", TFF_CATEGORIES)
KEYS = LEGACY_KEYS + DISAGG_KEYS + TFF_KEYS


def available_at(tuesday: str) -> str:
    """The Friday after the report Tuesday, 15:30 America/New_York, as UTC."""
    friday = dt.date.fromisoformat(tuesday) + dt.timedelta(days=3)
    local = dt.datetime.combine(friday, RELEASE_ET, tzinfo=session._eastern_tz())
    return observations.canonical_instant(
        local.astimezone(dt.timezone.utc).isoformat())


def _int(v) -> Optional[int]:
    try:
        return int(float(str(v).strip()))
    except (TypeError, ValueError):
        return None


def rows_from_records(records: list[dict]) -> list[dict]:
    out: list[dict] = []
    for rec in records:
        inst = CONTRACTS.get(str(rec.get("cftc_contract_market_code", "")).strip())
        day = str(rec.get("report_date_as_yyyy_mm_dd") or "")[:10]
        if not inst or len(day) != 10:
            continue
        lo = _int(rec.get("noncomm_positions_long_all"))
        sh = _int(rec.get("noncomm_positions_short_all"))
        oi = _int(rec.get("open_interest_all"))
        base = {"instrument": inst, "observed_at": day,
                "available_at": available_at(day),
                "availability_kind": "reconstructed"}
        vals = {"cftc.noncomm_long": lo, "cftc.noncomm_short": sh,
                "cftc.open_interest": oi,
                "cftc.noncomm_net": (lo - sh) if lo is not None and sh is not None
                else None}
        for key, v in vals.items():
            if v is not None:
                out.append(dict(base, registry_key=key, value=v))
    return out


def oi_share(position: Optional[int], oi: Optional[int]) -> Optional[float]:
    """A position as a percent of the record's open interest; None without OI."""
    if position is None or not oi:
        return None
    return round(100.0 * position / oi, 6)


def category_rows(records: list[dict], report: str, contracts: dict,
                  categories: dict) -> list[dict]:
    """The disaggregated or TFF rows: per category long, short and net, each also
    as a share of open interest, and the open interest itself. A response with
    none of the report's category columns is a changed shape and raises."""
    out: list[dict] = []
    seen_cols = False
    for rec in records:
        inst = contracts.get(str(rec.get("cftc_contract_market_code", "")).strip())
        day = str(rec.get("report_date_as_yyyy_mm_dd") or "")[:10]
        if not inst or len(day) != 10:
            continue
        oi = _int(rec.get("open_interest_all"))
        base = {"instrument": inst, "observed_at": day,
                "available_at": available_at(day),
                "availability_kind": "reconstructed"}
        vals: dict = {f"cftc.{report}_open_interest": oi}
        for cat, (lf, sf) in categories.items():
            lo, sh = _int(rec.get(lf)), _int(rec.get(sf))
            if lo is not None or sh is not None:
                seen_cols = True
            net = lo - sh if lo is not None and sh is not None else None
            for side, v in (("long", lo), ("short", sh), ("net", net)):
                vals[f"cftc.{report}_{cat}_{side}"] = v
                vals[f"cftc.{report}_{cat}_{side}_oi"] = oi_share(v, oi)
        for key, v in vals.items():
            if v is not None:
                out.append(dict(base, registry_key=key, value=v))
    if records and not seen_cols:
        raise ValueError(f"the {report} response carries none of its category "
                         f"columns -- the report changed shape")
    return out


def fetch_records(url: str = URL, contracts: Optional[dict] = None) -> list[dict]:
    records: list[dict] = []
    for code in (contracts if contracts is not None else CONTRACTS):
        offset = 0
        while True:
            page = http_get_json(url, params={
                "cftc_contract_market_code": code,
                "$order": "report_date_as_yyyy_mm_dd",
                "$limit": PAGE, "$offset": offset}, timeout=60)
            records.extend(page)
            if len(page) < PAGE:
                break
            offset += PAGE
    return records


def _produce() -> list[dict]:
    if not config.ENABLED_SOURCES.get("cftc"):
        raise RuntimeError("the cftc switch in config.ENABLED_SOURCES is off")
    return (rows_from_records(fetch_records())
            + category_rows(fetch_records(DISAGG_URL, DISAGG_CONTRACTS), "dis",
                            DISAGG_CONTRACTS, DISAGG_CATEGORIES)
            + category_rows(fetch_records(TFF_URL, TFF_CONTRACTS), "tff",
                            TFF_CONTRACTS, TFF_CATEGORIES))


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
