"""
The froth gauge's inputs -- the `gt.*` family (DS-19, S-5; CD-7 of the crypto
data-sources order, D-5 ruled build now; Batch 4 Tranche A part 2; crypto-
tranche-a-2, 17 Oct 2026). Config: config/crypto_sources.yaml `gt`.

    python -m altdata.sources.gt          # one sample (daily; no backfill exists)

    gt.new_pools_24h     pools created in the last 24 hours on one network
                         (instrument solana or base), counted from
                         /networks/{network}/new_pools, up to ten pages of 20;
                         200 or more is saturated and stored as 200 (censored)
    gt.trending_vol_24h  the 24-hour USD volume of the top 20 trending pools on
                         one network (/networks/{network}/trending_pools)

GECKOTERMINAL'S API IS NOT READ: api.geckoterminal.com's robots.txt allows only
/docs/ and disallows / for every agent (read 17 Oct 2026). The writer reads
robots.txt with the wildcard-aware reader before any request and stops when it
refuses -- so the day GeckoTerminal opens its API path, the writer starts. Its
parsers are tested on the response shape GeckoTerminal documents in its own
swagger spec (api.geckoterminal.com/docs/v2/swagger.json, which robots allows).

THE FALLBACK (the order: DexScreener as backup, used only when GeckoTerminal
fails): https://api.dexscreener.com/latest/dex/search?q=<network> (no key; no
robots.txt). It is a SEARCH, not a census, so its rows carry source
`dexscreener:fallback` in the store, and S-5's z-score reads GeckoTerminal's rows
only: a fallback row is a day sampled, never a day scored.

THE GUARD: GeckoTerminal publishes 30 calls a minute; the writer spends at most 20
(hl.WeightGuard, weight 1 a call). A burst past it is refused, never sent.

No backfill exists (the source has no history), so S-5's z-scores need 90 days of
GeckoTerminal store: from mid-January 2027 at the earliest, and only once its
robots.txt admits the API.
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any, Callable, Optional

from . import _crypto as C
from . import _publication as pub
from ._base import FetchError, http_get_json, http_get_text
from .hl import WeightGuard

log = logging.getLogger(__name__)

SOURCE = "geckoterminal"
AGENT = "chester-reports"
KEYS = ["gt.new_pools_24h", "gt.trending_vol_24h"]
CENSOR = 200


def _robots_text(url: str) -> str:
    try:
        return http_get_text(url, timeout=30)
    except FetchError as exc:
        if "HTTP 4" in str(exc):
            return ""
        raise


def robots_ok(get: Callable[[str], str] = _robots_text) -> tuple[bool, str]:
    from .aaii import robots_verdict                             # noqa: PLC0415
    ok, rule = robots_verdict(get("https://api.geckoterminal.com/robots.txt"),
                              "/api/v2/networks/solana/new_pools", AGENT)
    return ok, ("" if ok else f"api.geckoterminal.com robots.txt refuses /api/v2/ "
                              f"({rule})")


def _get(url: str, params: Optional[dict] = None) -> Any:
    accept = (C.config().get("gt") or {}).get("accept") or "application/json"
    return http_get_json(url, params=params, timeout=60, headers={"Accept": accept})


def _dex_get(url: str, params: Optional[dict] = None) -> Any:
    return http_get_json(url, params=params, timeout=60)


# ---------------------------------------------------------------------------
# Parsers -- pure, on tests/fixtures/gt/
# ---------------------------------------------------------------------------
def _ts(s: Any) -> Optional[dt.datetime]:
    try:
        return dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None


def count_new(pages: list[dict], now_dt: dt.datetime) -> tuple[int, bool]:
    """Pools created within 24 hours of `now_dt`, across the pages; (count,
    saturated). Pages are newest first; counting stops at the first older pool."""
    n, cut = 0, now_dt - dt.timedelta(hours=24)
    for page in pages:
        for p in (page or {}).get("data") or []:
            t = _ts(((p or {}).get("attributes") or {}).get("pool_created_at"))
            if t is None:
                continue
            if t < cut:
                return min(n, CENSOR), n >= CENSOR
            n += 1
    return min(n, CENSOR), n >= CENSOR


def trending_volume(doc: dict, top: int = 20) -> Optional[float]:
    vols = []
    for p in ((doc or {}).get("data") or [])[:top]:
        v = C.num((((p or {}).get("attributes") or {}).get("volume_usd") or {}).get("h24"))
        if v is not None:
            vols.append(v)
    return sum(vols) if vols else None


def dexscreener_volume(doc: dict, network: str, top: int = 20) -> Optional[float]:
    """The fallback: the search's pairs on `network`, the top `top` by 24-hour
    volume, summed."""
    vols = sorted((C.num(((p or {}).get("volume") or {}).get("h24")) or 0.0
                   for p in (doc or {}).get("pairs") or []
                   if (p or {}).get("chainId") == network), reverse=True)[:top]
    return sum(vols) if vols else None


# ---------------------------------------------------------------------------
def collect(get: Callable[..., Any] = _get, dex_get: Callable[..., Any] = _dex_get,
            *, robots: Optional[Callable[[], tuple]] = None,
            guard: Optional[WeightGuard] = None, today: Optional[str] = None,
            now: Optional[str] = None) -> tuple[list[dict], dict]:
    cfg = C.config().get("gt") or {}
    today = today or C.today_utc()
    now = now or C.now_iso()
    now_dt = dt.datetime.fromisoformat(now.replace("Z", "+00:00"))
    guard = guard or WeightGuard(budget=int(cfg.get("budget_per_min") or 20),
                                 limit=int(cfg.get("per_min") or 30))
    rows: list[dict] = []
    summary: dict = {"series": {}, "failed": [], "fallback": []}
    ok, why = (robots or robots_ok)()
    if not ok:
        summary["failed"].append(("geckoterminal", why))
    base = cfg.get("base") or "https://api.geckoterminal.com/api/v2"
    for net in cfg.get("networks") or ["solana", "base"]:
        if ok:
            try:
                pages = []
                for page in range(1, int(cfg.get("new_pool_pages") or 10) + 1):
                    guard.charge(1)
                    doc = get(f"{base}/networks/{net}/new_pools", {"page": page})
                    pages.append(doc)
                    data = (doc or {}).get("data") or []
                    last = _ts(((data[-1] if data else {}).get("attributes") or {})
                               .get("pool_created_at"))
                    # Newest first: a page ending past 24 hours is the last one read.
                    if not data or (last is not None
                                    and last < now_dt - dt.timedelta(hours=24)):
                        break
                n, sat = count_new(pages, now_dt)
                rows.append(C.row("gt.new_pools_24h", today, float(n), now, SOURCE, net))
                guard.charge(1)
                v = trending_volume(get(f"{base}/networks/{net}/trending_pools"),
                                    int(cfg.get("trending_top") or 20))
                if v is not None:
                    rows.append(C.row("gt.trending_vol_24h", today, round(v, 2), now,
                                      SOURCE, net))
                summary["series"][net] = {"new_pools": n, "saturated": sat,
                                          "trending_vol": v}
                continue
            except Exception as exc:                            # noqa: BLE001
                summary["failed"].append((net, f"{type(exc).__name__}: {exc}"[:240]))
        # THE FALLBACK: GeckoTerminal failed or is refused. Trending volume only
        # (a search counts no new pools), marked in the row's source.
        try:
            v = dexscreener_volume(dex_get(cfg.get("dexscreener")
                                           or "https://api.dexscreener.com/latest/dex/search",
                                           {"q": net}), net,
                                   int(cfg.get("trending_top") or 20))
            if v is not None:
                r = C.row("gt.trending_vol_24h", today, round(v, 2), now,
                          cfg.get("fallback_source") or "dexscreener:fallback", net)
                rows.append(r)
                summary["fallback"].append(net)
        except Exception as exc:                                # noqa: BLE001
            summary["failed"].append((f"{net}:dexscreener", f"{type(exc).__name__}: {exc}"[:240]))
    return rows, summary


def pull(run_id: Optional[str] = None, db=None, **kw) -> dict:
    state: dict = {}

    def produce() -> list[dict]:
        rows, s = collect(**kw)
        state.update(s)
        if not rows and s["failed"]:
            raise RuntimeError("; ".join(f"{k}: {v}" for k, v in s["failed"])[:400])
        return rows
    out = pub.run(SOURCE, KEYS, produce, run_id=run_id, db=db)
    out["failed_series"] = state.get("failed") or []
    out["fallback_networks"] = state.get("fallback") or []
    return out


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
