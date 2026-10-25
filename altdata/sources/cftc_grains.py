"""
CFTC disaggregated Commitments of Traders for the grains: managed money's net
position in corn, wheat and soybeans, for the Alternative Assets Quarterly's
positioning-and-flows commodity line (b69-quarterly-readers-1; D34 of 24 Oct
2026; B67 section 28).

    python -m altdata.sources.cftc_grains         # one pull, summary to stdout

TERMS. The existing CFTC source ("public, no key (Socrata)", source_registry.yaml
`cftc`); publicreporting.cftc.gov's robots.txt allows /resource/ (re-read 25 Oct
2026). The existing client does the paging (cftc.fetch_records), against the
disaggregated futures-only dataset 72hh-3qpy that cftc.py already reads for the
metals and energy.

  cftc.disagg.corn.managed_money_net       CBOT corn, 002602
  cftc.disagg.wheat.managed_money_net      CBOT wheat (SRW), 001602
  cftc.disagg.soybeans.managed_money_net   CBOT soybeans, 005602

Each managed money long less short, CONTRACTS; `_oi` beside it is the net as a
percent of open interest, which the dual percentiles are read on.

AVAILABILITY. cftc.available_at: the Friday after the report Tuesday, 15:30 ET,
reconstructed (a federal holiday pushes the release; the same known imprecision).
"""
from __future__ import annotations

import logging
from typing import Optional

from .. import config
from . import _publication as pub
from . import _quarterly_common as qc
from ._base import http_get_response, http_get_text
from . import cftc

log = logging.getLogger(__name__)

SOURCE = "cftc"
CONTRACTS = {"002602": "corn", "001602": "wheat", "005602": "soybeans"}
KEYS = ["cftc.disagg.corn.managed_money_net", "cftc.disagg.wheat.managed_money_net",
        "cftc.disagg.soybeans.managed_money_net",
        "cftc.disagg.corn.managed_money_net_oi", "cftc.disagg.wheat.managed_money_net_oi",
        "cftc.disagg.soybeans.managed_money_net_oi"]

_records = cftc.fetch_records


def _robots(url: str) -> str:
    return qc.robots_check(url, get_text=lambda u: http_get_text(u, timeout=30))


def rows_from_records(records: list[dict]) -> list[dict]:
    out: list[dict] = []
    seen = False
    for rec in records:
        crop = CONTRACTS.get(str(rec.get("cftc_contract_market_code", "")).strip())
        day = str(rec.get("report_date_as_yyyy_mm_dd") or "")[:10]
        if not crop or len(day) != 10:
            continue
        lo = cftc._int(rec.get("m_money_positions_long_all"))
        sh = cftc._int(rec.get("m_money_positions_short_all"))
        oi = cftc._int(rec.get("open_interest_all"))
        if lo is None or sh is None:
            continue
        seen = True
        base = {"instrument": None, "observed_at": day,
                "available_at": cftc.available_at(day),
                "availability_kind": "reconstructed"}
        net = lo - sh
        out.append(dict(base, registry_key=f"cftc.disagg.{crop}.managed_money_net",
                        value=float(net)))
        share = cftc.oi_share(net, oi)
        if share is not None:
            out.append(dict(base, registry_key=f"cftc.disagg.{crop}.managed_money_net_oi",
                            value=share))
    if records and not seen:
        raise ValueError("the disaggregated response carries no managed-money "
                         "columns for the grains -- the report changed shape")
    return out


def _produce() -> list[dict]:
    if not config.ENABLED_SOURCES.get("cftc"):
        raise RuntimeError("the cftc switch in config.ENABLED_SOURCES is off")
    _robots(cftc.DISAGG_URL)
    return rows_from_records(_records(cftc.DISAGG_URL, CONTRACTS))


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    raise SystemExit(qc.main(pull))
