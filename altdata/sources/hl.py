"""
Hyperliquid -- the `hl.*` family (DS-43; CD-2 of the crypto data-sources order,
Batch 4 Tranche A part 1, pulled forward by Batch 8; crypto-tranche-a-1, 17 Oct
2026). Config: config/crypto_sources.yaml.

    python -m altdata.sources.hl                      # the daily pull
    python -m altdata.sources.hl backfill [--dry-run] # funding from launch, bounded

POST https://api.hyperliquid.xyz/info, JSON body, no key. api.hyperliquid.xyz
publishes no robots.txt (404: no rules).

    hl.funding  (instrument BTC, ETH)  the day's funding, annualised percent: the
                sum of the day's hourly prints x 365 (fundingHistory), complete
                UTC days only; history from 12 May 2023
    hl.oi       (instrument BTC, ETH)  open interest in USD, openInterest (coins)
                x markPx from metaAndAssetCtxs: a snapshot, the pull's UTC day;
                Hyperliquid serves no OI history, so it is FORWARD-ONLY

THE WEIGHT GUARD. Hyperliquid's documented limit (read 17 Oct 2026): 1,200 weight
a minute per IP across REST; metaAndAssetCtxs and fundingHistory weigh 20, and
fundingHistory adds 1 per 20 items returned. Every request is charged before it
is sent at its worst case (20 + 500/20 for a funding page); the guard keeps a
rolling minute and spends at most the configured budget (600). A request that
would overrun waits for the window to clear -- or, with no wait allowed, is
REFUSED with WeightExceeded, never sent.
"""

from __future__ import annotations

import collections
import logging
import time
from typing import Any, Callable, Optional

from . import _crypto as C
from . import _publication as pub
from ._base import http_post_json

log = logging.getLogger(__name__)

URL = "https://api.hyperliquid.xyz/info"
SOURCE = "hyperliquid"
KEYS = ["hl.funding", "hl.oi"]
HOUR_MS = 3_600_000


class WeightExceeded(RuntimeError):
    """A request the guard refused: it would overrun the minute's budget."""


class WeightGuard:
    """A rolling one-minute budget of request weight. `clock` and `sleep` are
    injectable so a gate can drive it without waiting."""

    def __init__(self, budget: int = 600, limit: int = 1200,
                 clock: Callable[[], float] = time.monotonic,
                 sleep: Callable[[float], None] = time.sleep,
                 max_wait: float = 65.0) -> None:
        if budget > limit:
            raise ValueError(f"budget {budget} above Hyperliquid's limit {limit}")
        self.budget, self.limit = budget, limit
        self.clock, self.sleep, self.max_wait = clock, sleep, max_wait
        self.spent: collections.deque = collections.deque()   # (t, weight)
        self.total = 0

    def _used(self, now: float) -> int:
        while self.spent and now - self.spent[0][0] >= 60.0:
            self.spent.popleft()
        return sum(w for _, w in self.spent)

    def charge(self, weight: int) -> None:
        if weight > self.budget:
            raise WeightExceeded(f"one request of weight {weight} exceeds the "
                                 f"minute's budget {self.budget}")
        waited = 0.0
        while True:
            now = self.clock()
            if self._used(now) + weight <= self.budget:
                self.spent.append((now, weight))
                self.total += weight
                return
            pause = 60.0 - (now - self.spent[0][0]) + 0.05
            if waited + pause > self.max_wait:
                raise WeightExceeded(f"weight {weight} would overrun the budget "
                                     f"{self.budget}/min ({self._used(now)} spent)")
            self.sleep(pause)
            waited += pause


def guard_from_config(cfg: Optional[dict] = None, **kw) -> WeightGuard:
    h = (cfg or C.config()).get("hyperliquid") or {}
    return WeightGuard(budget=int(h.get("budget_per_min") or 600),
                       limit=int(h.get("limit_per_min") or 1200), **kw)


def weight_of(body: dict, cfg: Optional[dict] = None) -> int:
    """The request's worst-case weight, charged before it is sent."""
    h = (cfg or C.config()).get("hyperliquid") or {}
    w = int(h.get("weight_info") or 20)
    per = (h.get("weight_per_items") or {}).get(body.get("type"))
    if per:
        w += -(-int(h.get("max_items") or 500) // int(per))
    return w


def _post(body: dict) -> Any:
    """The shared POST helper (a 4xx, 429 included, raises at once; 5xx retries)."""
    return http_post_json(URL, body, timeout=60)


class Client:
    def __init__(self, guard: Optional[WeightGuard] = None,
                 post: Optional[Callable[[dict], Any]] = None,
                 cfg: Optional[dict] = None) -> None:
        self.cfg = cfg or C.config()
        self.guard = guard or guard_from_config(self.cfg)
        self.post = post or (lambda body: _post(body))

    def info(self, body: dict) -> Any:
        self.guard.charge(weight_of(body, self.cfg))
        return self.post(body)


# ---------------------------------------------------------------------------
# Parsers -- pure, on tests/fixtures/hl/
# ---------------------------------------------------------------------------
def parse_ctxs(doc: list, coins: list[str]) -> dict[str, dict]:
    """metaAndAssetCtxs: [meta{universe:[{name}]}, [ctx]] aligned by index ->
    coin -> {funding (hourly rate), oi_coins, mark, oi_usd}."""
    uni = ((doc or [{}])[0] or {}).get("universe") or []
    ctxs = (doc or [{}, []])[1] if len(doc or []) > 1 else []
    out = {}
    for i, u in enumerate(uni):
        name = u.get("name")
        if name not in coins or i >= len(ctxs):
            continue
        c = ctxs[i] or {}
        oi, mark = C.num(c.get("openInterest")), C.num(c.get("markPx"))
        out[name] = {"funding": C.num(c.get("funding")), "oi_coins": oi, "mark": mark,
                     "oi_usd": oi * mark if oi is not None and mark else None}
    return out


def parse_funding(rows: list) -> list[tuple[int, float]]:
    """fundingHistory: [{coin, fundingRate, premium, time}] -> [(ms, hourly rate)]."""
    out = []
    for r in rows or []:
        v = C.num((r or {}).get("fundingRate"))
        t = (r or {}).get("time")
        if v is not None and t is not None:
            out.append((int(t), v))
    return sorted(out)


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------
def funding_history(client: Client, coin: str, start_ms: int, end_ms: int,
                    max_pages: int) -> list[tuple[int, float]]:
    """Paged by time: each page at most 500 hourly prints; bounded by `max_pages`."""
    pts: list[tuple[int, float]] = []
    t = start_ms
    for _ in range(max_pages):
        page = parse_funding(client.info({"type": "fundingHistory", "coin": coin,
                                          "startTime": int(t), "endTime": int(end_ms)}))
        if not page:
            break
        pts += page
        nxt = page[-1][0] + 1
        if nxt <= t or nxt >= end_ms or len(page) < 2:
            break
        t = nxt
    return sorted(set(pts))


def collect(client: Optional[Client] = None, *, days: Optional[int] = None,
            start_day: Optional[str] = None, today: Optional[str] = None,
            now: Optional[str] = None) -> tuple[list[dict], dict]:
    """(rows, summary). Funding from `start_day` (else `days` back); OI now."""
    import datetime as dt  # noqa: PLC0415
    client = client or Client()
    cfg = client.cfg
    coins = list(cfg.get("coins") or ["BTC", "ETH"])
    today = today or C.today_utc()
    now = now or C.now_iso()
    rows: list[dict] = []
    summary: dict = {"series": {}, "failed": [], "weight": 0}
    first = start_day or (dt.date.fromisoformat(today)
                          - dt.timedelta(days=int(days or cfg.get("daily_window_days")
                                                   or 14))).isoformat()
    start_ms = int(dt.datetime.fromisoformat(first + "T00:00:00+00:00").timestamp() * 1000)
    end_ms = int(dt.datetime.fromisoformat(today + "T00:00:00+00:00").timestamp() * 1000)
    pages = int((cfg.get("backfill") or {}).get("max_pages") or 200)
    for coin in coins:
        try:
            pts = funding_history(client, coin, start_ms, end_ms, pages)
            daily = C.daily_funding(pts, today, expected=24)
            rows += [C.row("hl.funding", d, round(v, 6), now, SOURCE, coin)
                     for d, v in daily]
            summary["series"][f"hl.funding[{coin}]"] = {
                "rows": len(daily), "first": daily[0][0] if daily else None,
                "last": daily[-1][0] if daily else None}
        except Exception as exc:                                # noqa: BLE001
            summary["failed"].append((f"hl.funding[{coin}]", f"{type(exc).__name__}: {exc}"))
    try:
        ctx = parse_ctxs(client.info({"type": "metaAndAssetCtxs"}), coins)
        for coin in coins:
            c = ctx.get(coin)
            if c and c["oi_usd"] is not None:
                rows.append(C.row("hl.oi", today, round(c["oi_usd"], 2), now, SOURCE, coin))
                summary["series"][f"hl.oi[{coin}]"] = {"rows": 1, "first": today,
                                                       "last": today}
            else:
                summary["failed"].append((f"hl.oi[{coin}]", "not in metaAndAssetCtxs"))
    except Exception as exc:                                    # noqa: BLE001
        summary["failed"].append(("hl.oi", f"{type(exc).__name__}: {exc}"))
    summary["weight"] = client.guard.total
    return rows, summary


def pull(run_id: Optional[str] = None, db=None, client: Optional[Client] = None,
         **kw) -> dict:
    """The writer step (feeds.EXTERNAL_WRITERS): STALE-not-empty on failure."""
    state: dict = {}

    def produce() -> list[dict]:
        rows, s = collect(client, **kw)
        state.update(s)
        if not rows and s["failed"]:
            raise RuntimeError("; ".join(f"{k}: {v}" for k, v in s["failed"])[:300])
        return rows
    out = pub.run(SOURCE, KEYS, produce, run_id=run_id, db=db)
    out["failed_series"] = state.get("failed") or []
    out["weight_spent"] = state.get("weight")
    return out


def backfill(run_id: Optional[str] = None, db=None, client: Optional[Client] = None,
             dry_run: bool = False) -> dict:
    """Funding from Hyperliquid's first print (config backfill bound), point in
    time: written with the pull instant as available_at, inside a widened window."""
    client = client or Client()
    start = str((client.cfg.get("backfill") or {}).get("hyperliquid_funding_from")
                or "2023-05-12")
    rows, s = collect(client, start_day=start)
    rows = [r for r in rows if r["registry_key"] == "hl.funding"]
    if dry_run:
        return {"status": "DRY_RUN", "parsed": len(rows), **s}
    out = pub.write_rows(SOURCE, rows, KEYS, run_id or "hl_backfill", db=db,
                         window_days=100_000)
    return {**out, "weight_spent": s["weight"], "failed_series": s["failed"]}


if __name__ == "__main__":
    import json
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    if sys.argv[1:2] == ["backfill"]:
        print(json.dumps(backfill(dry_run="--dry-run" in sys.argv), indent=2,
                         default=str))
    else:
        print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
