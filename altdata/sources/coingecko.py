"""
CoinGecko for PRL (pearl-2) -- the `coingecko.prl_*` family (ST-13, signal-triage
Tranche 5, MW-4; st-t5-prl, 18 Oct 2026).

    python -m altdata.sources.coingecko --dry-run     # fetch and parse; write nothing
    python -m altdata.sources.coingecko               # write (only with the switch on)

G-25. No CoinGecko fetcher existed on this line -- only the switch,
`altdata.config.ENABLED_SOURCES["coingecko"]` (off) -- so there was nothing to
extend; this is the fetcher the order names, and the switch stays its gate.

THE SWITCH STAYS OFF. On 13 Oct 2026 CoinGecko was retired as a source for this
store: its terms (coingecko.com/en/api_terms, read again 18 Oct 2026) say "We do
not encourage caching or storage of Data" (6.1), ask for a cache refresh at least
every 24 hours (6.1.1), and "you are not allowed to duplicate, reproduce, copy,
store, derive from or translate any Data" (6.2). A store of point-in-time vintages
and the calc.prl_* figures derived from them sit against both. ST-13 asks for the
fetcher; storing is Ari's ruling to reconcile with 13 Oct's. Until the switch is
turned on, `pull` fetches and parses (so `--dry-run` shows what would be stored)
and WRITES NOTHING. source_registry.yaml `coingecko` stays retired, with the
caveat. Meanwhile the derived layer (altdata/prl.py) reads PRL's price and cap
from the crypto basket's permitted series (config/prl.yaml `derived`).

THE READ (MW-4). Keyless first, through the public endpoints:

    GET {base}/coins/pearl-2?localization=false&tickers=false&community_data=false
        &developer_data=false          market_data: price, cap, 24h volume,
                                       circulating supply, last_updated
    GET {base}/coins/pearl-2/tickers   per venue: market, converted_volume.usd

The Demo key is optional and read only when the environment carries it: its name
is COINGECKO_DEMO_API_KEY, sent as the x-cg-demo-api-key header. No session
creates or writes it; .env is Ari's.

THE BUDGET. Two calls a pull, `spacing_seconds` (6) apart; a weekly pull plus one
daily close is 16 calls a week -- far inside the public limit (of the order of
5-15 calls a minute) and the Demo plan's (30 a minute, 10,000 a month).

POINT IN TIME. CoinGecko serves current values: observed_at is the UTC day of
the coin's `last_updated`, available_at the pull instant. Each venue's volume is
a row under its market's name (`coingecko.prl_venue_volume`, instrument = the
venue), and the venue count beside it.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Callable, Optional

from . import _crypto as C

log = logging.getLogger(__name__)

SOURCE = "coingecko"
KEYS = ["coingecko.prl_price", "coingecko.prl_market_cap", "coingecko.prl_volume_24h",
        "coingecko.prl_circulating", "coingecko.prl_venue_volume",
        "coingecko.prl_venues"]


def _cfg() -> dict:
    from .. import prl                                          # noqa: PLC0415
    return prl.config()["coingecko"]


def enabled() -> bool:
    from .. import config                                       # noqa: PLC0415
    return bool((getattr(config, "ENABLED_SOURCES", {}) or {}).get("coingecko"))


def headers(env: Optional[dict] = None) -> dict:
    """The request headers: the User-Agent, and the Demo key only if present."""
    c = _cfg()
    h = {"User-Agent": c["user_agent"], "Accept": "application/json"}
    key = (os.environ if env is None else env).get(c["key_env"])
    if key:
        h[c["key_header"]] = key
    return h


def _get(path: str, params: Optional[dict] = None) -> Any:
    import json                                                 # noqa: PLC0415
    from ._base import http_get_text                            # noqa: PLC0415
    c = _cfg()
    return json.loads(http_get_text(c["base"] + path, params=params, timeout=30,
                                    headers=headers()))


def parse_coin(doc: dict, now: str) -> list[dict]:
    """/coins/pearl-2 -> the four market rows. A field the response lacks is
    left out, never zero."""
    if (doc or {}).get("id") != "pearl-2":
        raise ValueError(f"coingecko: the response is for {doc.get('id')!r}, not pearl-2")
    md = doc.get("market_data") or {}
    day = (str(md.get("last_updated") or doc.get("last_updated") or now))[:10]
    out = []
    for key, v in (("coingecko.prl_price", (md.get("current_price") or {}).get("usd")),
                   ("coingecko.prl_market_cap", (md.get("market_cap") or {}).get("usd")),
                   ("coingecko.prl_volume_24h", (md.get("total_volume") or {}).get("usd")),
                   ("coingecko.prl_circulating", md.get("circulating_supply"))):
        n = C.num(v)
        if n is not None:
            out.append(C.row(key, day, n, now, SOURCE))
    return out


def parse_tickers(doc: dict, now: str) -> list[dict]:
    """/coins/pearl-2/tickers -> one row per venue (its converted USD volume) and
    the venue count. Venues with no USD volume are counted, not summed."""
    tk = (doc or {}).get("tickers") or []
    by: dict[str, float] = {}
    day = now[:10]
    for t in tk:
        name = str(((t.get("market") or {}).get("name")) or "").strip()
        if not name:
            continue
        day = str(t.get("last_fetch_at") or t.get("timestamp") or now)[:10]
        v = C.num((t.get("converted_volume") or {}).get("usd"))
        by[name] = by.get(name, 0.0) + (v or 0.0)
    out = [dict(C.row("coingecko.prl_venue_volume", day, v, now, SOURCE), instrument=n)
           for n, v in sorted(by.items())]
    if by:
        out.append(C.row("coingecko.prl_venues", day, float(len(by)), now, SOURCE))
    return out


def collect(get: Callable[..., Any] = _get, now: Optional[str] = None,
            sleep: Callable[[float], None] = time.sleep) -> list[dict]:
    now = now or C.now_iso()
    c = _cfg()
    rows = parse_coin(get(c["endpoints"]["coin"], {
        "localization": "false", "tickers": "false", "community_data": "false",
        "developer_data": "false"}), now)
    sleep(float(c.get("spacing_seconds") or 6))
    rows += parse_tickers(get(c["endpoints"]["tickers"]), now)
    return rows


def pull(dry_run: bool = False, run_id: Optional[str] = None, db=None, **kw) -> dict:
    """Fetch and parse; write only when the switch is on and not a dry run."""
    if dry_run or not enabled():
        try:
            rows = collect(**kw)
        except Exception as exc:                                # noqa: BLE001
            return {"source": SOURCE, "state": "failed", "written": 0,
                    "reason": f"{type(exc).__name__}: {exc}"}
        return {"source": SOURCE, "written": 0, "rows": len(rows),
                "state": "dry_run" if dry_run else "disabled",
                "reason": None if dry_run else
                "ENABLED_SOURCES['coingecko'] is off: CoinGecko's terms and the 13 Oct "
                "ruling; storing is Ari's to rule", "preview": rows}
    from . import _publication as pub                           # noqa: PLC0415
    return pub.run(SOURCE, KEYS, lambda: collect(**kw), run_id=run_id, db=db)


if __name__ == "__main__":
    import argparse
    import json
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    ap = argparse.ArgumentParser(prog="python -m altdata.sources.coingecko")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(sys.argv[1:])
    print(json.dumps(pull(dry_run=a.dry_run), indent=2, sort_keys=True, default=str))
