"""
Sweden's two-year government bond yield, from the Riksbank's SWEA API, for the
Alternative Assets Quarterly's currencies chapter (the policy-divergence table and
the DXY-weighted two-year spread) (b69-quarterly-readers-1; D34 of 24 Oct 2026;
B67 section 10).

    python -m altdata.sources.riksbank           # one pull, summary to stdout

TERMS (re-read 25 Oct 2026, the Riksbank's FAQ on its interest-rate API): "The
Riksbank's API is freely available without charge and the data may be freely
adapted and used without any particular permission or agreement being required."
Its unregistered use is rate-limited per IP; THE LIMIT IS HONOURED BY ONE REQUEST
A DAY (qc.DailyGuard), with no retry. api.riksbank.se's robots.txt answers 404: no
rules.

SOURCE. https://api.riksbank.se/swea/v1/Observations/SEGVB2YC/<from>, keyless:
[{"date": "2026-10-01", "value": 2.735}, ...]. One request returns the range.

  riksbank.yield_2y   SEGVB2YC, the Swedish government bond, 2 years, percent

observed_at = the day. available_at = that day at 12:00 ET (18:00 Stockholm),
reconstructed: the Riksbank publishes the day's rates in the evening, Swedish time
(session-set; the lag row is in config/publication_lags.yaml). A first pull asks
from 2000-01-01; later pulls from 30 days before the newest stored day.
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from . import _publication as pub
from . import _quarterly_common as qc
from ._base import http_get_response, http_get_text

log = logging.getLogger(__name__)

SOURCE = "riksbank"
SERIES = "SEGVB2YC"
URL = "https://api.riksbank.se/swea/v1/Observations/" + SERIES + "/{start}"
KEYS = ["riksbank.yield_2y"]
POSTED_ET = "12:00"


def _fetch(url: str, **kw):
    """Every request through THIS module's helpers (patchable by the gates)."""
    return qc.fetch(url, get=lambda u, **k: http_get_response(u, **k),
                    get_text=lambda u: http_get_text(u, timeout=30), **kw)


def _robots(url: str) -> str:
    return qc.robots_check(url, get_text=lambda u: http_get_text(u, timeout=30))
_guard = qc.DailyGuard(SOURCE)


def rows_from_payload(payload) -> list[dict]:
    if not isinstance(payload, list):
        raise ValueError(f"the SWEA response is not a list ({str(payload)[:120]})")
    rows = []
    for o in payload:
        day = str((o or {}).get("date") or "")[:10]
        v = (o or {}).get("value")
        if len(day) == 10 and isinstance(v, (int, float)) and not isinstance(v, bool):
            rows.append({"registry_key": "riksbank.yield_2y", "instrument": None,
                         "observed_at": day,
                         "available_at": qc.et_instant(day, POSTED_ET),
                         "value": float(v), "availability_kind": "reconstructed"})
    return rows


def _produce(start: str) -> list[dict]:
    url = URL.format(start=start)
    _robots(url)
    _guard.charge()                       # counted BEFORE the request is sent
    data, _h = _fetch(url, once=True, robots=False)
    return rows_from_payload(json.loads(data.decode("utf-8")))


def pull(run_id: Optional[str] = None, db=None) -> dict:
    start = pub.since(KEYS, 30, db=db) or "2000-01-01"
    return pub.run(SOURCE, KEYS, lambda: _produce(start), run_id=run_id, db=db)


if __name__ == "__main__":
    raise SystemExit(qc.main(pull))
