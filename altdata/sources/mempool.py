"""
mempool.space -- the `mempool.*` family: Bitcoin's network state (DS-38; CD-5 of
the crypto data-sources order, Batch 4 Tranche A part 1; crypto-tranche-a-1, 17
Oct 2026). Config: config/crypto_sources.yaml.

    python -m altdata.sources.mempool                      # the daily pull
    python -m altdata.sources.mempool backfill [--dry-run] # hashrate and
                                                           # difficulty from 2009

https://mempool.space/api, no key. mempool.space answers /robots.txt with its
single-page app (200, an HTML page, no robots rules): read as no rules.

    mempool.hashrate               the day's average hashrate, hashes a second
                                   (/v1/mining/hashrate/3m daily; /all for the
                                   backfill, from 3 Jan 2009); complete UTC days
    mempool.difficulty             the difficulty set at each adjustment, filed
                                   under the adjustment's UTC day (same endpoint)
    mempool.difficulty_change_est  the next adjustment's estimated change, %
                                   (/v1/difficulty-adjustment), a snapshot
    mempool.fee_rate               recommended fee, sat/vB; instrument fastest,
                                   half_hour, hour, economy, minimum
                                   (/v1/fees/recommended), a snapshot
    mempool.mempool_vsize          the projected mempool blocks' total virtual
                                   size, vbytes (/v1/fees/mempool-blocks), a snapshot
    mempool.tip_height             the chain tip (/blocks/tip/height), a snapshot
    mempool.pool_share             a pool's share of the last week's blocks, %;
                                   instrument = the pool's slug, the top ten
                                   (/v1/mining/pools/1w), a snapshot

A snapshot is the pull's UTC day (altdata/sources/_crypto.py).
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Optional

from . import _crypto as C
from . import _publication as pub
from ._base import http_get_json, http_get_text

log = logging.getLogger(__name__)

SOURCE = "mempool_space"
BASE = "https://mempool.space/api"
KEYS = ["mempool.hashrate", "mempool.difficulty", "mempool.difficulty_change_est",
        "mempool.fee_rate", "mempool.mempool_vsize", "mempool.tip_height",
        "mempool.pool_share"]
FEE_TIERS = {"fastestFee": "fastest", "halfHourFee": "half_hour", "hourFee": "hour",
             "economyFee": "economy", "minimumFee": "minimum"}


def _get(path: str) -> Any:
    return http_get_json(f"{BASE}{path}", timeout=60)


def _get_text(path: str) -> str:
    return str(http_get_text(f"{BASE}{path}", timeout=60)).strip()


# ---------------------------------------------------------------------------
# Parsers -- pure, on tests/fixtures/mempool/
# ---------------------------------------------------------------------------
def parse_hashrate(doc: dict, today: str) -> tuple[list[tuple[str, float]],
                                                   list[tuple[str, float]]]:
    """(hashrate by day, difficulty by adjustment day); complete days only."""
    hr: dict[str, float] = {}
    for r in (doc or {}).get("hashrates") or []:
        v, d = C.num(r.get("avgHashrate")), C.utc_day(r.get("timestamp"))
        if v is not None and d < today:
            hr[d] = v
    df: dict[str, float] = {}
    for r in (doc or {}).get("difficulty") or []:
        v, d = C.num(r.get("difficulty")), C.utc_day(r.get("time"))
        if v is not None and d < today:
            df[d] = v
    return sorted(hr.items()), sorted(df.items())


def parse_adjustment(doc: dict) -> Optional[float]:
    return C.num((doc or {}).get("difficultyChange"))


def parse_fees(doc: dict) -> dict[str, float]:
    return {tier: C.num(doc[k]) for k, tier in FEE_TIERS.items()
            if C.num((doc or {}).get(k)) is not None}


def parse_mempool_vsize(blocks: list) -> Optional[float]:
    vs = [C.num(b.get("blockVSize")) for b in blocks or []]
    vs = [v for v in vs if v is not None]
    return sum(vs) if vs else None


def parse_pools(doc: dict, top: int = 10) -> dict[str, float]:
    total = C.num((doc or {}).get("blockCount"))
    if not total:
        return {}
    pools = sorted((doc or {}).get("pools") or [],
                   key=lambda p: -(C.num(p.get("blockCount")) or 0))[:top]
    return {p["slug"]: 100.0 * (C.num(p.get("blockCount")) or 0) / total
            for p in pools if p.get("slug")}


# ---------------------------------------------------------------------------
# Collect
# ---------------------------------------------------------------------------
def collect(get: Optional[Callable[[str], Any]] = None,
            get_text: Optional[Callable[[str], str]] = None,
            *, period: str = "3m", today: Optional[str] = None,
            now: Optional[str] = None, history_only: bool = False
            ) -> tuple[list[dict], dict]:
    cfg = C.config()
    get = get or (lambda p: _get(p))
    get_text = get_text or (lambda p: _get_text(p))
    today = today or C.today_utc()
    now = now or C.now_iso()
    rows: list[dict] = []
    summary: dict = {"series": {}, "failed": []}

    def guard(label: str, fn: Callable[[], list[dict]]) -> None:
        try:
            got = fn()
            rows.extend(got)
            summary["series"][label] = len(got)
        except Exception as exc:                                # noqa: BLE001
            summary["failed"].append((label, f"{type(exc).__name__}: {exc}"[:240]))

    def history() -> list[dict]:
        hr, df = parse_hashrate(get(f"/v1/mining/hashrate/{period}"), today)
        return ([C.row("mempool.hashrate", d, v, now, SOURCE) for d, v in hr]
                + [C.row("mempool.difficulty", d, v, now, SOURCE) for d, v in df])
    guard("hashrate_difficulty", history)
    if history_only:
        return rows, summary
    guard("difficulty_change_est", lambda: [
        C.row("mempool.difficulty_change_est", today,
              round(parse_adjustment(get("/v1/difficulty-adjustment")), 4), now, SOURCE)])
    guard("fee_rate", lambda: [C.row("mempool.fee_rate", today, v, now, SOURCE, t)
                               for t, v in parse_fees(get("/v1/fees/recommended")).items()])
    guard("mempool_vsize", lambda: [
        C.row("mempool.mempool_vsize", today,
              parse_mempool_vsize(get("/v1/fees/mempool-blocks")), now, SOURCE)])
    guard("tip_height", lambda: [C.row("mempool.tip_height", today,
                                       float(int(get_text("/blocks/tip/height"))), now,
                                       SOURCE)])
    top = int((cfg.get("mempool") or {}).get("pools_top") or 10)
    guard("pool_share", lambda: [
        C.row("mempool.pool_share", today, round(v, 4), now, SOURCE, slug)
        for slug, v in parse_pools(get("/v1/mining/pools/1w"), top).items()])
    rows = [r for r in rows if r["value"] is not None]
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


def backfill(run_id: Optional[str] = None, db=None, dry_run: bool = False, **kw) -> dict:
    """Hashrate and difficulty from the genesis block (/hashrate/all: one call),
    point in time."""
    rows, s = collect(period="all", history_only=True, **kw)
    if dry_run:
        return {"status": "DRY_RUN", "parsed": len(rows), **s}
    out = pub.write_rows(SOURCE, rows, KEYS, run_id or "mempool_backfill", db=db,
                         window_days=100_000)
    return {**out, "failed_series": s["failed"]}


if __name__ == "__main__":
    import json
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    if sys.argv[1:2] == ["backfill"]:
        print(json.dumps(backfill(dry_run="--dry-run" in sys.argv), indent=2, default=str))
    else:
        print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
