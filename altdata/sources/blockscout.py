"""
Blockscout's Ethereum explorer -- the `blockscout.*` family: Ethereum's gas and
activity, KEYLESS (CD-5's Ethereum pieces under the 16 Oct rule (b); crypto-
tranche-a-1, 17 Oct 2026). Config: config/crypto_sources.yaml.

    python -m altdata.sources.blockscout     # one pull

WHY NOT ETHERSCAN. The order's DS-11 is Etherscan (ethsupply2 and the gas
oracle), whose key (ETHERSCAN_API_KEY) is a registration Ari has not made. Under
rule (b) of 16 Oct the Ethereum pieces take a keyless path within robots where one
exists: https://eth.blockscout.com/api/v2 (robots.txt: Allow /, account and auth
paths disallowed). What it does not serve -- ETH supply, staked and burnt
(ethsupply2) -- is a listed gap, with the key's name.

    blockscout.gas_gwei       the gas oracle, gwei; instrument slow, average,
                              fast (/stats), a snapshot
    blockscout.utilization    network utilisation, % of block gas used (/stats),
                              a snapshot
    blockscout.tx_count       transactions a day (/stats/charts/transactions,
                              the last 30 days; complete UTC days)

NOT STORED: /stats's coin_price and market_cap. They are CoinGecko's, and
CoinGecko's terms bar storing its data (ruled 13 Oct 2026).
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Optional

from . import _crypto as C
from . import _publication as pub
from ._base import http_get_json

log = logging.getLogger(__name__)

SOURCE = "blockscout"
BASE = "https://eth.blockscout.com/api/v2"
KEYS = ["blockscout.gas_gwei", "blockscout.utilization", "blockscout.tx_count"]


def _get(path: str) -> Any:
    return http_get_json(f"{BASE}{path}", timeout=60)


def parse_stats(doc: dict) -> dict:
    g = (doc or {}).get("gas_prices") or {}
    return {"gas": {k: C.num(g.get(k)) for k in ("slow", "average", "fast")
                    if C.num(g.get(k)) is not None},
            "utilization": C.num((doc or {}).get("network_utilization_percentage"))}


def parse_tx_chart(doc: dict, today: str) -> list[tuple[str, float]]:
    out = {}
    for r in (doc or {}).get("chart_data") or []:
        v, d = C.num(r.get("transactions_count")), str(r.get("date") or "")[:10]
        if v is not None and d and d < today:
            out[d] = v
    return sorted(out.items())


def collect(get: Callable[[str], Any] = _get, today: Optional[str] = None,
            now: Optional[str] = None) -> tuple[list[dict], dict]:
    today = today or C.today_utc()
    now = now or C.now_iso()
    rows: list[dict] = []
    summary: dict = {"failed": []}
    try:
        s = parse_stats(get("/stats"))
        rows += [C.row("blockscout.gas_gwei", today, v, now, SOURCE, k)
                 for k, v in s["gas"].items()]
        if s["utilization"] is not None:
            rows.append(C.row("blockscout.utilization", today,
                              round(s["utilization"], 4), now, SOURCE))
    except Exception as exc:                                    # noqa: BLE001
        summary["failed"].append(("stats", f"{type(exc).__name__}: {exc}"[:240]))
    try:
        rows += [C.row("blockscout.tx_count", d, v, now, SOURCE)
                 for d, v in parse_tx_chart(get("/stats/charts/transactions"), today)]
    except Exception as exc:                                    # noqa: BLE001
        summary["failed"].append(("tx_count", f"{type(exc).__name__}: {exc}"[:240]))
    return rows, summary


def pull(run_id: Optional[str] = None, db=None, **kw) -> dict:
    state: dict = {}

    def produce() -> list[dict]:
        rows, s = collect(**kw)
        state.update(s)
        if not rows and s["failed"]:
            raise RuntimeError("; ".join(f"{k}: {v}" for k, v in s["failed"])[:300])
        return rows
    out = pub.run(SOURCE, KEYS, produce, run_id=run_id, db=db)
    out["failed_series"] = state.get("failed") or []
    return out


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
