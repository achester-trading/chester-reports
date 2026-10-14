"""
ECB data portal -- the euro-area long-term interest rates: Bund, OAT, BTP, monthly.

    python -m altdata.sources.ecb_irs        # one pull, summary to stdout

AQ-3 part 2 (11 Oct 2026; the Quarterly's global-rates rows, change order
section 4.9): the legs of calc.oat_bund_bp and calc.btp_bund_bp
(altdata/market_features.py). One method for all three, so the spreads compare
like with like -- which a daily Bund from the Bundesbank against a monthly OAT
from somewhere else would not.

SOURCE. data-api.ecb.europa.eu, SDMX REST, no key. Its robots.txt redirects to
data.ecb.europa.eu's, whose `*` group disallows only the portal's own Drupal
paths (checked 11 Oct 2026). Dataset IRS, the long-term interest rates for
convergence purposes: 10-year government bond yields, secondary market, monthly
average, per country:
  IRS.M.{DE,FR,IT}.L.L40.CI.0000.EUR.N.Z
Banque de France's own Webstat API needs a registered key, and neither it nor
the Bundesbank publishes a daily OAT or BTP keyless, so these are monthly.

READ BY CONTENT. The CSV must carry KEY, REF_AREA, TIME_PERIOD and OBS_VALUE;
each row is stored by its REF_AREA, and a country not asked for is refused.

  ecb.irs_10y_de, ecb.irs_10y_fr, ecb.irs_10y_it   percent; observed_at = the
                  month's first day (a monthly average)

AVAILABILITY. Last-Modified, which the API sends, is this vintage's instant
(`observed`); without it the write instant (`ingest_instant`). Either is an upper
bound. Every pull reads the whole history (FR from 1986, DE 1990, IT 1991):
about 1,400 rows across the three.
"""

from __future__ import annotations

import csv
import io
import logging
from typing import Optional

from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "ecb"
COUNTRIES = {"DE": "ecb.irs_10y_de", "FR": "ecb.irs_10y_fr", "IT": "ecb.irs_10y_it"}
URL = ("https://data-api.ecb.europa.eu/service/data/IRS/M."
       + "+".join(COUNTRIES) + ".L.L40.CI.0000.EUR.N.Z")
KEYS = list(COUNTRIES.values())


def rows_from_csv(text: str, available: str, kind: str) -> list[dict]:
    reader = csv.DictReader(io.StringIO(text.lstrip("﻿")))
    need = {"KEY", "REF_AREA", "TIME_PERIOD", "OBS_VALUE"}
    if not need <= set(reader.fieldnames or []):
        raise ValueError(f"the ECB response lacks {sorted(need - set(reader.fieldnames or []))}")
    out = []
    for r in reader:
        if not r["KEY"].startswith("IRS.M."):
            raise ValueError(f"the ECB response carries {r['KEY']}, not an IRS monthly series")
        key = COUNTRIES.get(r["REF_AREA"])
        if key is None:
            raise ValueError(f"the ECB response carries {r['REF_AREA']}, not asked for")
        try:
            v = float(r["OBS_VALUE"])
        except (TypeError, ValueError):
            continue
        out.append({"registry_key": key, "instrument": None,
                    "observed_at": r["TIME_PERIOD"][:7] + "-01",
                    "available_at": available, "value": v,
                    "availability_kind": kind})
    missing = set(KEYS) - {r["registry_key"] for r in out}
    if missing:
        raise ValueError(f"the ECB response has no rows for {sorted(missing)}")
    return out


def pull(run_id: Optional[str] = None, db=None) -> dict:
    def produce() -> list[dict]:
        data, headers = http_get_response(URL, params={"format": "csvdata"},
                                          timeout=60)
        available, kind = pub.availability(headers)
        return rows_from_csv(data.decode("utf-8"), available, kind)
    return pub.run(SOURCE, KEYS, produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
