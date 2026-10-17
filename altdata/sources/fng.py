"""
alternative.me's Crypto Fear & Greed Index -- the `fng.*` family (DS-44; CD-5 of
the crypto data-sources order, Batch 4 Tranche A part 1; crypto-tranche-a-1, 17 Oct
2026).

    python -m altdata.sources.fng        # one pull: the whole history

https://api.alternative.me/fng/?limit=0&format=json, no key; full history (from
1 Feb 2018) in one call, so every pull is its own backfill. api.alternative.me
publishes no robots.txt (404: no rules).

    fng.value    the day's index, 0 (extreme fear) to 100 (extreme greed); filed
                 under the UTC day of its timestamp (the index is set at 00:00 UTC
                 for the day). The classification ("Fear", "Greed") is the
                 publisher's banding of the value and is not stored.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Optional

from . import _crypto as C
from . import _publication as pub
from ._base import http_get_json

log = logging.getLogger(__name__)

SOURCE = "alternative_me"
URL = "https://api.alternative.me/fng/"
KEYS = ["fng.value"]


def _get() -> Any:
    return http_get_json(URL, params={"limit": "0", "format": "json"}, timeout=60)


def parse(doc: dict, today: str) -> list[tuple[str, float]]:
    if (doc or {}).get("metadata", {}).get("error"):
        raise ValueError(f"alternative.me: {doc['metadata']['error']}")
    out: dict[str, float] = {}
    for r in (doc or {}).get("data") or []:
        v, ts = C.num(r.get("value")), r.get("timestamp")
        if v is None or ts is None:
            continue
        d = C.utc_day(ts)
        if d <= today:
            out[d] = v
    return sorted(out.items())


def collect(get: Callable[[], Any] = _get, today: Optional[str] = None,
            now: Optional[str] = None) -> list[dict]:
    today = today or C.today_utc()
    now = now or C.now_iso()
    return [C.row("fng.value", d, v, now, SOURCE) for d, v in parse(get(), today)]


def pull(run_id: Optional[str] = None, db=None, **kw) -> dict:
    return pub.run(SOURCE, KEYS, lambda: collect(**kw), run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
