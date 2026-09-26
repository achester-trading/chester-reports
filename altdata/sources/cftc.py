"""
CFTC Commitments of Traders -- legacy futures-only report, Socrata API.

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
CONTRACTS = {"097741": "JPY", "098662": "USD_INDEX"}
RELEASE_ET = dt.time(15, 30)
PAGE = 5000

KEYS = ["cftc.noncomm_long", "cftc.noncomm_short", "cftc.noncomm_net",
        "cftc.open_interest"]


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


def fetch_records() -> list[dict]:
    records: list[dict] = []
    for code in CONTRACTS:
        offset = 0
        while True:
            page = http_get_json(URL, params={
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
    return rows_from_records(fetch_records())


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
