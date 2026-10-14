"""
BIS central-bank policy rates for the EM scorecard. (AQ-9a, 11 Oct 2026)

    python -m altdata.sources.bis_cbpol      # one pull, summary to stdout

The BIS's policy-rate table (dataflow WS_CBPOL), monthly, end of period, in
percent, read as CSV from the BIS SDMX API (stats.bis.org/api/v2), anonymous and
free. ONE request for the scorecard's countries (config/em_scorecard.yaml), the
whole history each serves -- so the first pull is the backfill:

  em.bis.policy_rate.<iso3>   percent, the month-end policy rate

It is the real-policy-rate lens's first term (altdata/sources/em_lenses.py: the
policy rate less IMF CPI inflation). observed_at is the month-end; available_at
the response's Last-Modified where the API sends one (`observed`), else the
ingest instant (`ingest_instant`). The table restates a series' definition across
regimes (Brazil's rediscount rate before the Selic target); the BIS documents
each break in the row's COMPILATION field, and the series is stored as the BIS
publishes it.

COVERAGE (11 Oct 2026): eleven of the thirteen. The table has no row for Taiwan
or the UAE -- both off the roster, their lens "not tracked" with the candidate
(config/em_scorecard.yaml `not_yet_sourced`).
"""

from __future__ import annotations

import csv
import io
import logging
from typing import Optional

from .. import session
from . import _imf_sdmx as sdmx
from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "bis_cbpol"
PREFIX = "em.bis.policy_rate."

# MIRRORED from config/em_scorecard.yaml (iso3 -> the BIS's iso2); the gate
# fails if they differ. Taiwan and the UAE have no BIS row.
ISO2 = {"CHN": "CN", "IND": "IN", "KOR": "KR", "BRA": "BR", "SAU": "SA", "ZAF": "ZA",
        "MEX": "MX", "MYS": "MY", "IDN": "ID", "POL": "PL", "THA": "TH"}
COUNTRIES = ("CHN", "IND", "KOR", "BRA", "SAU", "ZAF", "MEX", "MYS", "IDN", "POL", "THA")

KEYS = [PREFIX + c.lower() for c in COUNTRIES]


def config() -> dict:
    from ..em_scorecard import config as cfg                    # noqa: PLC0415
    return cfg()


def url(cfg: dict) -> tuple[str, dict]:
    b = cfg["bis"]
    return (f"{b['url']}/{b['frequency']}.{'+'.join(ISO2[c] for c in COUNTRIES)}",
            {"format": "csv"})


def parse(text: str) -> dict[str, dict[str, float]]:
    """{iso3: {month_end: percent}} from the BIS CSV. A CSV without the columns
    it should carry raises."""
    rd = csv.DictReader(io.StringIO(text))
    need = {"FREQ", "REF_AREA", "TIME_PERIOD", "OBS_VALUE"}
    if not rd.fieldnames or not need <= set(rd.fieldnames):
        raise ValueError(f"BIS CSV: missing columns {sorted(need - set(rd.fieldnames or []))}")
    back = {v: k for k, v in ISO2.items()}
    out: dict[str, dict[str, float]] = {}
    for r in rd:
        c = back.get(r["REF_AREA"])
        if c is None or r["FREQ"] != "M" or r["OBS_VALUE"] in ("", "NaN", None):
            continue
        out.setdefault(c, {})[sdmx.period_end(r["TIME_PERIOD"])] = float(r["OBS_VALUE"])
    return out


def rows_from(series: dict, available: tuple[str, str]) -> list[dict]:
    av, kind = available
    today = session.session_date()
    return [{"registry_key": PREFIX + c.lower(), "instrument": None, "observed_at": d,
             "available_at": av, "value": v, "availability_kind": kind}
            for c in COUNTRIES for d, v in sorted((series.get(c) or {}).items())
            if d <= today]


def _produce(cfg: Optional[dict] = None) -> list[dict]:
    c = cfg or config()
    u, params = url(c)
    body, headers = http_get_response(u, params=params, timeout=120,
                                      headers={"Accept": "text/csv"})
    series = parse(body.decode("utf-8"))
    if not series:
        raise ValueError("BIS CSV carried none of the configured countries")
    missing = sorted(set(COUNTRIES) - set(series))
    if missing:
        log.warning("bis_cbpol: no rows for %s", ", ".join(missing))
    return rows_from(series, pub.availability(headers))


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, default=str))
