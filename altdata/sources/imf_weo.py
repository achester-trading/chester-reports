"""
IMF World Economic Outlook: the EM scorecard's annual lenses, every vintage.

    python -m altdata.sources.imf_weo        # one pull, summary to stdout

AQ-9a (change order "Alternative Assets Quarterly", 10 Oct 2026, section 4.5).
For the scorecard's thirteen countries (config/em_scorecard.yaml), four WEO
indicators, annual:

  em.weo.ca_gdp.<iso3>      BCA_NGDPD    current account, % of GDP
  em.weo.fiscal_gdp.<iso3>  GGXCNL_NGDP  general government net lending/borrowing, % of GDP
  em.weo.debt_gdp.<iso3>    GGXWDG_NGDP  general government gross debt, % of GDP
  em.weo.gdp_usd.<iso3>     NGDPD        GDP, current US dollars -- the external-
                                         debt lens's denominator. The API serves it
                                         in dollars (Brazil 2025: 2279917849000);
                                         the series' SCALE attribute ("9") is a
                                         display hint, not a multiplier

VINTAGES, NEVER AN OVERWRITE. The WEO is published in April and October. The IMF
serves the current edition (dataflow IMF.RES:WEO) and each past edition as its
own dataflow (WEO_2025_OCT_VINTAGE, WEO_2026_APR_VINTAGE, ...), each response
carrying its own PUBLICATION_DATE and UPDATE_DATE. Every configured flow is read
on every pull and each row is stamped with ITS flow's instant (the later of the
two), so the October 2025 numbers are knowable from November 2025 and the April
2026 revision from April 2026: an as-of read before April sees October's. A value
unchanged between editions is one vintage, not two (_publication's first-vintage
rule and drop_unchanged).

THE PROJECTIONS ARE NOT STORED. The WEO carries staff projections to five years
out; a row dated after today is a parse error to the store (_publication), and a
projection is not an observation. A year is stored from its year-end; the latest
year is the IMF's estimate, revised in the next edition (a new vintage).

The WEO revises history, so the write window is wide (WINDOW_DAYS) -- a revision
to 2021 in a new edition is kept as that year's new vintage.
"""

from __future__ import annotations

import logging
from typing import Optional

from .. import session
from . import _imf_sdmx as sdmx
from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "imf_weo"
PREFIX = "em.weo."
FIELDS = ("ca_gdp", "fiscal_gdp", "debt_gdp", "gdp_usd")
INDICATORS = {"BCA_NGDPD": "ca_gdp", "GGXCNL_NGDP": "fiscal_gdp",
              "GGXWDG_NGDP": "debt_gdp", "NGDPD": "gdp_usd"}
WINDOW_DAYS = 365 * 30

# MIRRORED from config/em_scorecard.yaml (the feeds roster reads KEYS without
# importing this module); the gate fails if the two differ. All thirteen report.
COUNTRIES = ("CHN", "TWN", "IND", "KOR", "BRA", "SAU", "ZAF", "MEX", "ARE", "MYS",
             "IDN", "POL", "THA")

KEYS = [PREFIX + f + "." + c.lower() for f in FIELDS for c in COUNTRIES]


def config() -> dict:
    from ..em_scorecard import config as cfg                    # noqa: PLC0415
    return cfg()


def rows_from(parsed: dict, now: Optional[str] = None) -> list[dict]:
    """One flow's rows, each at the flow's own publication instant; projections
    (a year-end after today) dropped."""
    now = now or session.utc_iso(timespec="microseconds")
    av, kind = sdmx.availability(parsed.get("published"), now)
    today = session.session_date()
    rows = []
    for s in parsed["series"]:
        field = INDICATORS.get(s["dims"].get("INDICATOR"))
        c = s["dims"].get("COUNTRY")
        if field is None or c not in COUNTRIES or s["dims"].get("FREQUENCY") not in (None, "A"):
            continue
        for p, v in s["obs"].items():
            day = sdmx.period_end(p)
            if day > today:
                continue                       # a projection, not an observation
            rows.append({"registry_key": f"{PREFIX}{field}.{c.lower()}",
                         "instrument": None, "observed_at": day,
                         "available_at": av, "value": v,
                         "availability_kind": kind})
    return rows


def _produce(cfg: Optional[dict] = None) -> list[dict]:
    c = cfg or config()
    key = f"{'+'.join(COUNTRIES)}.{'+'.join(INDICATORS)}.A"
    rows, seen = [], []
    for flow in c["weo"]["dataflows"]:
        parsed = sdmx.fetch(flow, key, c["imf"]["base"], c["imf"]["accept"],
                            get=http_get_response)
        got = {s["dims"].get("COUNTRY") for s in parsed["series"] if s["obs"]}
        if not got & set(COUNTRIES):
            raise ValueError(f"WEO flow {flow}: none of the configured countries")
        seen.append(f"{flow} published {parsed.get('published')}")
        rows += rows_from(parsed)
    log.info("imf_weo: %s", "; ".join(seen))
    return rows


def pull(run_id: Optional[str] = None, db=None) -> dict:
    """Every configured WEO flow; the first pull writes every year each serves.
    STALE, never empty, on any failure."""
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db,
                   window_days=WINDOW_DAYS)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, default=str))
