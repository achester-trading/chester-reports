"""
World Bank Quarterly External Debt Statistics for the EM scorecard. (AQ-9a)

    python -m altdata.sources.wb_qeds        # one pull, summary to stdout

The World Bank's QEDS (SDDS, API source 22), quarterly, in US dollars, read from
the free v2 API (api.worldbank.org/v2), no key. TWO requests -- gross external
debt and its short-term part -- for the scorecard's countries
(config/em_scorecard.yaml), every quarter each serves (the first pull is the
backfill):

  em.qeds.ext_debt_usd.<iso3>  DT.DOD.DECT.CD.AR.US  gross external debt position,
                                                    all sectors, all maturities
  em.qeds.st_debt_usd.<iso3>   DT.DOD.DSTC.CD.US     the short-term part (original
                                                    maturity)

They are the denominators of reserves against short-term debt and the numerator
of external debt against GDP (altdata/sources/em_lenses.py). observed_at is the
quarter-end. available_at is the response's own `lastupdated` (the date the
World Bank updated the source), taken as the end of that day, `observed`, and
never later than now; the ingest instant where absent. The tables are revised: a
changed value is a second vintage.

COVERAGE (11 Oct 2026): eleven of the thirteen; Taiwan is outside the World
Bank's tables and the UAE files no QEDS row -- off the roster, their lenses "not
tracked" with the candidate (config/em_scorecard.yaml `not_yet_sourced`).
"""

from __future__ import annotations

import datetime as dt
import json
import logging
from typing import Optional

from .. import session
from . import _imf_sdmx as sdmx
from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "wb_qeds"
EXT = "em.qeds.ext_debt_usd."
ST = "em.qeds.st_debt_usd."
INDICATORS = {"DT.DOD.DECT.CD.AR.US": EXT, "DT.DOD.DSTC.CD.US": ST}

# MIRRORED from config/em_scorecard.yaml; Taiwan and the UAE have no QEDS row.
COUNTRIES = ("CHN", "IND", "KOR", "BRA", "SAU", "ZAF", "MEX", "MYS", "IDN", "POL", "THA")

KEYS = [EXT + c.lower() for c in COUNTRIES] + [ST + c.lower() for c in COUNTRIES]


def config() -> dict:
    from ..em_scorecard import config as cfg                    # noqa: PLC0415
    return cfg()


def url(cfg: dict, indicator: str) -> tuple[str, dict]:
    q = cfg["qeds"]
    return (f"{q['url']}/country/{';'.join(COUNTRIES)}/indicator/{indicator}",
            {"source": q["source"], "format": "json", "per_page": 20000})


def parse(payload, indicator: str) -> dict:
    """{published, series: {iso3: {quarter_end: usd}}} from one v2 response. The
    v2 API answers an error as a one-element list carrying `message`; that, or
    any other shape, raises."""
    if not isinstance(payload, list) or len(payload) < 2 or not isinstance(payload[0], dict):
        raise ValueError(f"QEDS {indicator}: unexpected response {str(payload)[:200]}")
    meta, rows = payload[0], payload[1] or []
    if meta.get("message"):
        raise ValueError(f"QEDS {indicator}: {meta['message']}")
    if int(meta.get("pages") or 1) > 1:
        raise ValueError(f"QEDS {indicator}: {meta['pages']} pages -- raise per_page")
    out: dict[str, dict[str, float]] = {}
    for r in rows:
        if (r.get("indicator") or {}).get("id") != indicator:
            raise ValueError(f"QEDS: a row of {r.get('indicator')} in the {indicator} response")
        v = r.get("value")
        c = r.get("countryiso3code") or (r.get("country") or {}).get("id")
        if v is None or c not in COUNTRIES:
            continue
        out.setdefault(c, {})[sdmx.period_end(r["date"])] = float(v)
    lu = meta.get("lastupdated")
    published = None
    if lu:
        d = dt.date.fromisoformat(str(lu)[:10]) + dt.timedelta(days=1)
        published = f"{d.isoformat()}T00:00:00Z"
    return {"published": published, "series": out}


def rows_from(parsed: dict, prefix: str, now: Optional[str] = None) -> list[dict]:
    now = now or session.utc_iso(timespec="microseconds")
    av, kind = sdmx.availability(parsed.get("published"), now)
    today = session.session_date()
    return [{"registry_key": prefix + c.lower(), "instrument": None, "observed_at": d,
             "available_at": av, "value": v, "availability_kind": kind}
            for c in COUNTRIES for d, v in sorted((parsed["series"].get(c) or {}).items())
            if d <= today]


def _produce(cfg: Optional[dict] = None) -> list[dict]:
    c = cfg or config()
    rows = []
    for ind, prefix in INDICATORS.items():
        u, params = url(c, ind)
        body, _h = http_get_response(u, params=params, timeout=120)
        parsed = parse(json.loads(body.decode("utf-8")), ind)
        if not parsed["series"]:
            raise ValueError(f"QEDS {ind}: none of the configured countries")
        rows += rows_from(parsed, prefix)
    return rows


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, default=str))
