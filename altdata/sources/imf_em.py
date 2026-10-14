"""
IMF reserves, imports and CPI for the EM scorecard. (AQ-9a, 11 Oct 2026)

    python -m altdata.sources.imf_em         # one pull, summary to stdout

Three requests, one per dataflow, for the countries config/em_scorecard.yaml
names, monthly, every month each serves (the first pull is the backfill):

  em.ifs.reserves_usd.<iso3>  IMF.STA:IL  TRGMV_REVS, USD   total reserves, gold at
                                                           market value, month-end
  em.itg.imports_usd.<iso3>   IMF.STA:ITG MG, CIF_USD       goods imports, the month
  em.cpi.yoy.<iso3>           IMF.STA:CPI CPI, _T, YOY_PCH_PA_PT
                                                           headline CPI, % year on year

They are the inputs of the scorecard's reserves and inflation lenses
(altdata/sources/em_lenses.py). observed_at is the month-end; available_at each
response's own PUBLICATION_DATE / UPDATE_DATE (the later), `observed`; the
ingest instant where it carries none. The IMF revises: a changed value is a
second vintage, never an overwrite.

COVERAGE (11 Oct 2026). IL serves all thirteen; ITG has no row for the UAE or
South Africa, CPI none for Taiwan -- those countries' series are off the roster
and their lenses print "not tracked" with the candidate source
(config/em_scorecard.yaml `not_yet_sourced`).
"""

from __future__ import annotations

import logging
from typing import Optional

from .. import session
from . import _imf_sdmx as sdmx
from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "imf_em"
RESERVES = "em.ifs.reserves_usd."
IMPORTS = "em.itg.imports_usd."
CPI = "em.cpi.yoy."

# MIRRORED from config/em_scorecard.yaml; the gate fails if they differ.
COUNTRIES = ("CHN", "TWN", "IND", "KOR", "BRA", "SAU", "ZAF", "MEX", "ARE", "MYS",
             "IDN", "POL", "THA")
NO_IMPORTS = ("ARE", "ZAF")          # no IMF ITG row
NO_CPI = ("TWN",)                    # no IMF CPI row

KEYS = ([RESERVES + c.lower() for c in COUNTRIES]
        + [IMPORTS + c.lower() for c in COUNTRIES if c not in NO_IMPORTS]
        + [CPI + c.lower() for c in COUNTRIES if c not in NO_CPI])


def config() -> dict:
    from ..em_scorecard import config as cfg                    # noqa: PLC0415
    return cfg()


def requests(cfg: dict) -> list[tuple[str, str, str, dict]]:
    """(dataflow, key, store prefix, {dimension: required code})."""
    cs = "+".join(COUNTRIES)
    il, itg, cpi = cfg["il"], cfg["itg"], cfg["cpi"]
    return [
        (il["dataflow"], f"{cs}.{il['indicator']}.{il['unit']}.{il['frequency']}", RESERVES,
         {"INDICATOR": il["indicator"], "UNIT": il["unit"], "FREQUENCY": il["frequency"]}),
        (itg["dataflow"], f"{cs}.{itg['indicator']}.{itg['transformation']}.{itg['frequency']}",
         IMPORTS, {"INDICATOR": itg["indicator"],
                   "TYPE_OF_TRANSFORMATION": itg["transformation"],
                   "FREQUENCY": itg["frequency"]}),
        (cpi["dataflow"], f"{cs}.{cpi['index_type']}.{cpi['coicop']}."
                          f"{cpi['transformation']}.{cpi['frequency']}", CPI,
         {"INDEX_TYPE": cpi["index_type"], "COICOP_1999": cpi["coicop"],
          "TYPE_OF_TRANSFORMATION": cpi["transformation"],
          "FREQUENCY": cpi["frequency"]}),
    ]


def rows_from(parsed: dict, prefix: str, want: dict,
              now: Optional[str] = None) -> list[dict]:
    """One response's rows. A series whose dimensions are not the requested
    ones raises: the response is not what was asked for."""
    now = now or session.utc_iso(timespec="microseconds")
    av, kind = sdmx.availability(parsed.get("published"), now)
    today = session.session_date()
    rows = []
    for s in parsed["series"]:
        bad = {k: s["dims"].get(k) for k, v in want.items() if s["dims"].get(k) != v}
        if bad:
            raise ValueError(f"{prefix}: unexpected series {s['dims']}")
        c = s["dims"]["COUNTRY"]
        if c not in COUNTRIES:
            continue
        for p, v in s["obs"].items():
            day = sdmx.period_end(p)
            if day > today:
                continue
            rows.append({"registry_key": prefix + c.lower(), "instrument": None,
                         "observed_at": day, "available_at": av, "value": v,
                         "availability_kind": kind})
    return rows


def _produce(cfg: Optional[dict] = None) -> list[dict]:
    c = cfg or config()
    rows = []
    for flow, key, prefix, want in requests(c):
        parsed = sdmx.fetch(flow, key, c["imf"]["base"], c["imf"]["accept"],
                            get=http_get_response)
        got = {s["dims"].get("COUNTRY") for s in parsed["series"] if s["obs"]}
        if not got & set(COUNTRIES):
            raise ValueError(f"{flow}: none of the configured countries")
        rows += rows_from(parsed, prefix, want)
    return rows


def pull(run_id: Optional[str] = None, db=None) -> dict:
    """The three dataflows; STALE, never empty, on any failure."""
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, default=str))
