"""
LBMA Gold Price PM -- the daily London auction benchmark, via LBMA's own JSON.

    python -m altdata.sources.lbma           # one pull, summary to stdout

Signal-triage order ST-2 (SR-15 gold valuation, SR-24): gold in dollars, daily,
from the benchmark administrator rather than an ETF (GLD is on the price pass for
the tradable proxy).

SOURCE. https://prices.lbma.org.uk/json/gold_pm.json -- no key. One record per
auction day since 1968-04-01: {"d": date, "v": [USD, GBP, EUR]}; the USD leg is
stored. Sends Last-Modified.

  lbma.gold_pm_usd   USD per troy ounce, observed_at = the auction date

AVAILABILITY. The PM auction settles around 15:00 London; available_at is the
file's Last-Modified (`observed`), an upper bound for older rows. The benchmark is
not revised (revision_policy: never).

LICENCE. LBMA publishes these prices free to view; redistribution is licensed.
Stored for this system's own use and cited, never republished -- recorded in
source_registry.yaml.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "lbma"
URL = "https://prices.lbma.org.uk/json/gold_pm.json"
KEY = "lbma.gold_pm_usd"
KEYS = [KEY]


def rows_from_json(records: list, available_at: str, kind: str) -> list[dict]:
    if not isinstance(records, list):
        raise ValueError("LBMA gold_pm.json is not a list")
    out = []
    for rec in records:
        day = str((rec or {}).get("d") or "")[:10]
        vals = (rec or {}).get("v") or []
        usd = vals[0] if vals else None
        if len(day) == 10 and isinstance(usd, (int, float)) and usd > 0:
            out.append({"registry_key": KEY, "instrument": None,
                        "observed_at": day, "available_at": available_at,
                        "value": float(usd), "availability_kind": kind})
    return out


def _produce() -> list[dict]:
    data, headers = http_get_response(URL, timeout=90)
    return rows_from_json(json.loads(data.decode("utf-8")),
                          *pub.availability(headers))


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
