"""
The Bank of Canada's two-year benchmark yield, for the Alternative Assets
Quarterly's currencies chapter (the policy-divergence table and the DXY-weighted
two-year spread) (b69-quarterly-readers-1; D34 of 24 Oct 2026; B67 section 9).

    python -m altdata.sources.boc_valet          # one pull, summary to stdout

TERMS (re-read 25 Oct 2026, https://www.bankofcanada.ca/terms/): "the Bank permits
you to freely use, copy, distribute and transmit its website content under the
following terms", the first being "You must attribute the Bank of Canada as the
source of the content, and indicate if changes were made". The Valet response
carries the terms link itself. robots.txt (www.bankofcanada.ca) allows /valet/.

SOURCE. https://www.bankofcanada.ca/valet/observations/BD.CDN.2YR.DQ.YLD/json,
keyless: {"observations": [{"d": "2026-10-22", "BD.CDN.2YR.DQ.YLD": {"v": "3.22"}}]}.

  boc.yield_2y   the Government of Canada 2-year benchmark bond yield, percent

observed_at = the business day. available_at = that day at 18:00 ET,
reconstructed: the Bank posts the day's benchmark yields after the close (session-
set; the newest row's lag is in config/publication_lags.yaml). A first pull takes
the history from 2000; later pulls the last 30 observations.
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from . import _publication as pub
from . import _quarterly_common as qc
from ._base import http_get_response, http_get_text

log = logging.getLogger(__name__)

SOURCE = "boc"
SERIES = "BD.CDN.2YR.DQ.YLD"
URL = f"https://www.bankofcanada.ca/valet/observations/{SERIES}/json"
KEYS = ["boc.yield_2y"]
ATTRIBUTION = "Bank of Canada"
POSTED_ET = "18:00"


def _fetch(url: str, **kw):
    """Every request through THIS module's helpers (patchable by the gates)."""
    return qc.fetch(url, get=lambda u, **k: http_get_response(u, **k),
                    get_text=lambda u: http_get_text(u, timeout=30), **kw)


def _robots(url: str) -> str:
    return qc.robots_check(url, get_text=lambda u: http_get_text(u, timeout=30))


def rows_from_payload(payload: dict) -> list[dict]:
    obs = payload.get("observations")
    if not isinstance(obs, list):
        raise ValueError("the Valet response has no observations")
    rows = []
    for o in obs:
        day = str(o.get("d") or "")[:10]
        v = ((o.get(SERIES) or {}).get("v"))
        try:
            val = float(v)
        except (TypeError, ValueError):
            continue
        if len(day) == 10:
            rows.append({"registry_key": "boc.yield_2y", "instrument": None,
                         "observed_at": day,
                         "available_at": qc.et_instant(day, POSTED_ET),
                         "value": val, "availability_kind": "reconstructed"})
    if obs and not rows:
        raise ValueError(f"the Valet response carried no {SERIES} values")
    return rows


def _produce(first: bool) -> list[dict]:
    url = URL + ("?start_date=2000-01-01" if first else "?recent=30")
    data, _h = _fetch(url)
    return rows_from_payload(json.loads(data.decode("utf-8")))


def pull(run_id: Optional[str] = None, db=None) -> dict:
    first = pub.since(KEYS, 30, db=db) is None
    return pub.run(SOURCE, KEYS, lambda: _produce(first), run_id=run_id, db=db)


if __name__ == "__main__":
    raise SystemExit(qc.main(pull))
