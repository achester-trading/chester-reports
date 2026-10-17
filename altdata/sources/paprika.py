"""
CoinPaprika's global figures -- the `paprika.*` family: total crypto market cap
and bitcoin's dominance (ruling 2 of 17 Oct 2026 on the Tranche A part 1 report;
crypto-tranche-a-2). Config: config/crypto_sources.yaml `paprika`.

    python -m altdata.sources.paprika     # one pull

WHY NOT COINGECKO. The order put /global on the ST-13 CoinGecko fetcher. No such
fetcher exists, and CoinGecko's terms bar storing its data (ruled 13 Oct 2026).
Ruling 2: a keyless source within robots instead, CoinPaprika's tested first.
GET https://api.coinpaprika.com/v1/global: no key on the free plan (its API terms,
read 17 Oct 2026: keyless free plan, personal and non-commercial use, attribution
"Powered by Coinpaprika" where the figures are displayed, no redistribution; no
clause on storage). api.coinpaprika.com publishes no robots.txt (404: no rules).

    paprika.total_mcap_usd     total crypto market capitalisation, USD
    paprika.btc_dominance      bitcoin's share of it, percent

Both are SNAPSHOTS filed under the pull's UTC day (altdata/sources/_crypto.py):
the endpoint serves the current figure only, so the series are FORWARD-ONLY.

RULING 3 of 17 Oct 2026: the series may be stored. The terms as read carry no
storage clause; the 13 Oct note in altdata/loggers/shielded.py applies to
CoinGecko's terms, not to this source. The terms URL and the date read are in
source_registry.yaml `coinpaprika` (`catalogue show` prints them); re-read
quarterly.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Optional

from . import _crypto as C
from . import _publication as pub
from ._base import http_get_json

log = logging.getLogger(__name__)

SOURCE = "coinpaprika"
URL = "https://api.coinpaprika.com/v1/global"
KEYS = ["paprika.total_mcap_usd", "paprika.btc_dominance"]


def _get() -> Any:
    return http_get_json(URL, timeout=60)


def parse(doc: dict) -> dict:
    cap = C.num((doc or {}).get("market_cap_usd"))
    dom = C.num((doc or {}).get("bitcoin_dominance_percentage"))
    if cap is None and dom is None:
        raise ValueError("CoinPaprika /global: neither market_cap_usd nor "
                         "bitcoin_dominance_percentage in the answer")
    return {"total_mcap_usd": cap, "btc_dominance": dom,
            "last_updated": (doc or {}).get("last_updated")}


def collect(get: Callable[[], Any] = _get, today: Optional[str] = None,
            now: Optional[str] = None) -> list[dict]:
    today = today or C.today_utc()
    now = now or C.now_iso()
    g = parse(get())
    return [C.row(f"paprika.{k}", today, g[k], now, SOURCE)
            for k in ("total_mcap_usd", "btc_dominance") if g[k] is not None]


def pull(run_id: Optional[str] = None, db=None, **kw) -> dict:
    return pub.run(SOURCE, KEYS, lambda: collect(**kw), run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
