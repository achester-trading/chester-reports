"""
The perp venues besides Hyperliquid -- the `fut.*` family, venue in the key (DS-42;
CD-2 of the crypto data-sources order, Batch 4 Tranche A part 1; crypto-tranche-a-1,
17 Oct 2026). Config: config/crypto_sources.yaml.

    python -m altdata.sources.fut                      # the daily pull
    python -m altdata.sources.fut backfill [--dry-run] # bounded history

THE VENUES. The order's are Hyperliquid (altdata/sources/hl.py), Bybit and OKX;
Binance was dropped by D-2 because it answers 451 from US addresses. On 17 Oct
2026 Bybit answered the laptop 403, "The Amazon CloudFront distribution is
configured to block access from your country": the same condition. Under the 16
Oct rule (friction becomes a keyless alternative or a gap) the third venue is
DERIBIT's perpetuals, keyless and reachable from both machines (DS-41 already
adopts Deribit). Bybit's reader is here, tested on its documented response shape,
and OFF in config (`venues.bybit.enabled: false`) until Ari rules on it; its keys
are not registered while it is off.

    fut.funding_okx      (BTC, ETH)  the day's funding annualised %, from
                         /api/v5/public/funding-rate-history (realizedRate,
                         eight-hourly; OKX serves about three months)
    fut.oi_okx           (BTC, ETH)  open interest in USD: history from
                         /api/v5/rubik/stat/contracts/open-interest-history
                         (period 1D; OKX's day is stamped 16:00 UTC, the Hong Kong
                         midnight, and is filed under that UTC date), today from
                         /api/v5/public/open-interest (oiUsd)
    fut.ls_account_okx   (BTC, ETH)  the account long/short ratio, OKX's
                         /api/v5/rubik/stat/contracts/long-short-account-ratio
                         (period 1D, the currency's contracts; stored, never a
                         direction call -- the order: a retail-skew measure)
    fut.funding_deribit  (BTC, ETH)  the day's funding annualised %, the sum of the
                         day's interest_1h from /public/get_funding_rate_history
    fut.oi_deribit       (BTC, ETH)  open interest in USD (an inverse perpetual's
                         open_interest is in USD), /public/get_book_summary_by_
                         instrument; a snapshot, FORWARD-ONLY (no OI history)

Robots: www.okx.com's robots.txt disallows account and internal paths, none under
/api/v5/; www.deribit.com and api.bybit.com publish none (4xx: no rules).

EACH VENUE IS ISOLATED: one that fails is named in the summary and the others
still land.
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any, Callable, Optional

from . import _crypto as C
from . import _publication as pub
from ._base import http_get_json

log = logging.getLogger(__name__)

SOURCE = "perp_venues"
OKX = "https://www.okx.com"
DERIBIT = "https://www.deribit.com/api/v2"
BYBIT = "https://api.bybit.com"
KEYS = ["fut.funding_okx", "fut.oi_okx", "fut.ls_account_okx",
        "fut.funding_deribit", "fut.oi_deribit"]
# Bybit's, registered only if Ari switches the venue on.
BYBIT_KEYS = ["fut.funding_bybit", "fut.oi_bybit", "fut.ls_account_bybit"]
DAY_MS = 86_400_000


def _get(url: str, params: Optional[dict] = None) -> Any:
    return http_get_json(url, params=params, timeout=60)


# ---------------------------------------------------------------------------
# Parsers -- pure, on tests/fixtures/fut/
# ---------------------------------------------------------------------------
def _okx_data(doc: dict) -> list:
    if str((doc or {}).get("code")) not in ("0", ""):
        raise ValueError(f"OKX code {doc.get('code')}: {doc.get('msg')}")
    return (doc or {}).get("data") or []


def okx_funding(doc: dict) -> list[tuple[int, float]]:
    out = []
    for r in _okx_data(doc):
        v = C.num(r.get("realizedRate")) if r.get("realizedRate") not in (None, "") \
            else C.num(r.get("fundingRate"))
        if v is not None and r.get("fundingTime"):
            out.append((int(r["fundingTime"]), v))
    return sorted(out)


def okx_oi_now(doc: dict) -> Optional[float]:
    d = _okx_data(doc)
    return C.num(d[0].get("oiUsd")) if d else None


def okx_oi_history(doc: dict) -> list[tuple[int, float]]:
    """[[ts, oi, oiCcy, oiUsd], ...] -> [(ms, USD)]."""
    out = []
    for r in _okx_data(doc):
        if isinstance(r, list) and len(r) >= 4 and C.num(r[3]) is not None:
            out.append((int(r[0]), C.num(r[3])))
    return sorted(out)


def okx_ratio(doc: dict) -> list[tuple[int, float]]:
    out = []
    for r in _okx_data(doc):
        if isinstance(r, list) and len(r) >= 2 and C.num(r[1]) is not None:
            out.append((int(r[0]), C.num(r[1])))
    return sorted(out)


def deribit_funding(doc: dict) -> list[tuple[int, float]]:
    out = []
    for r in (doc or {}).get("result") or []:
        v = C.num(r.get("interest_1h"))
        if v is not None and r.get("timestamp") is not None:
            out.append((int(r["timestamp"]), v))
    return sorted(out)


def deribit_oi(doc: dict) -> Optional[float]:
    res = (doc or {}).get("result") or []
    return C.num(res[0].get("open_interest")) if res else None


def bybit_list(doc: dict) -> list:
    if int((doc or {}).get("retCode", -1)) != 0:
        raise ValueError(f"Bybit retCode {doc.get('retCode')}: {doc.get('retMsg')}")
    return ((doc or {}).get("result") or {}).get("list") or []


def bybit_funding(doc: dict) -> list[tuple[int, float]]:
    return sorted((int(r["fundingRateTimestamp"]), C.num(r["fundingRate"]))
                  for r in bybit_list(doc) if C.num(r.get("fundingRate")) is not None)


def bybit_oi_now(doc: dict) -> Optional[float]:
    lst = bybit_list(doc)
    return C.num(lst[0].get("openInterestValue")) if lst else None


def bybit_ratio(doc: dict) -> list[tuple[int, float]]:
    out = []
    for r in bybit_list(doc):
        b, s = C.num(r.get("buyRatio")), C.num(r.get("sellRatio"))
        if b is not None and s:
            out.append((int(r["timestamp"]), b / s))
    return sorted(out)


# ---------------------------------------------------------------------------
# The venues
# ---------------------------------------------------------------------------
def _ms(day: str) -> int:
    return int(dt.datetime.fromisoformat(day + "T00:00:00+00:00").timestamp() * 1000)


def okx(coin: str, inst: str, first: str, today: str, now: str, get, cfg: dict,
        backfill: bool = False) -> list[dict]:
    rows: list[dict] = []
    pages = int((cfg.get("backfill") or {}).get("max_pages") or 200)
    # Funding: newest first, paged back with `after`.
    pts: list[tuple[int, float]] = []
    after = None
    for _ in range(pages):
        p = {"instId": inst, "limit": "100"}
        if after:
            p["after"] = str(after)
        page = okx_funding(get(f"{OKX}/api/v5/public/funding-rate-history", p))
        if not page:
            break
        pts += page
        if page[0][0] < _ms(first) or (after and page[0][0] >= after):
            break
        after = page[0][0]
    rows += [C.row("fut.funding_okx", d, round(v, 6), now, SOURCE, coin)
             for d, v in C.daily_funding([x for x in pts if x[0] >= _ms(first)], today)]
    # OI: history (days before today) and today's snapshot.
    hist: list[tuple[int, float]] = []
    end = None
    for _ in range(pages):
        p = {"instId": inst, "period": "1D", "limit": "100"}
        if end:
            p["end"] = str(end)
        page = okx_oi_history(get(f"{OKX}/api/v5/rubik/stat/contracts/open-interest-history", p))
        if not page:
            break
        hist += page
        if page[0][0] < _ms(first) or (end and page[0][0] >= end):
            break
        end = page[0][0]
    seen: dict[str, float] = {}
    for ms, v in sorted(set(hist)):
        d = C.utc_day(ms)
        if first <= d < today:
            seen[d] = v
    rows += [C.row("fut.oi_okx", d, round(v, 2), now, SOURCE, coin) for d, v in seen.items()]
    if not backfill:
        oi = okx_oi_now(get(f"{OKX}/api/v5/public/open-interest",
                            {"instType": "SWAP", "instId": inst}))
        if oi is not None:
            rows.append(C.row("fut.oi_okx", today, round(oi, 2), now, SOURCE, coin))
    # The account long/short ratio (the currency's contracts), daily.
    rat = okx_ratio(get(f"{OKX}/api/v5/rubik/stat/contracts/long-short-account-ratio",
                        {"ccy": coin, "period": "1D"}))
    rows += [C.row("fut.ls_account_okx", C.utc_day(ms), v, now, SOURCE, coin)
             for ms, v in rat if first <= C.utc_day(ms) < today]
    return rows


def deribit(coin: str, inst: str, first: str, today: str, now: str, get, cfg: dict,
            backfill: bool = False) -> list[dict]:
    rows: list[dict] = []
    pts: list[tuple[int, float]] = []
    t, end = _ms(first), _ms(today)
    while t < end:                       # 30 days a call (744 hourly prints max)
        e = min(end, t + 30 * DAY_MS)
        pts += deribit_funding(get(f"{DERIBIT}/public/get_funding_rate_history",
                                   {"instrument_name": inst, "start_timestamp": t,
                                    "end_timestamp": e}))
        t = e
    rows += [C.row("fut.funding_deribit", d, round(v, 6), now, SOURCE, coin)
             for d, v in C.daily_funding(sorted(set(pts)), today, expected=24)]
    if not backfill:
        oi = deribit_oi(get(f"{DERIBIT}/public/get_book_summary_by_instrument",
                            {"instrument_name": inst}))
        if oi is not None:
            rows.append(C.row("fut.oi_deribit", today, round(oi, 2), now, SOURCE, coin))
    return rows


def bybit(coin: str, inst: str, first: str, today: str, now: str, get, cfg: dict,
          backfill: bool = False) -> list[dict]:
    rows: list[dict] = []
    pts = bybit_funding(get(f"{BYBIT}/v5/market/funding/history",
                            {"category": "linear", "symbol": inst, "limit": "200"}))
    rows += [C.row("fut.funding_bybit", d, round(v, 6), now, SOURCE, coin)
             for d, v in C.daily_funding([x for x in pts if x[0] >= _ms(first)], today)]
    if not backfill:
        oi = bybit_oi_now(get(f"{BYBIT}/v5/market/tickers",
                              {"category": "linear", "symbol": inst}))
        if oi is not None:
            rows.append(C.row("fut.oi_bybit", today, round(oi, 2), now, SOURCE, coin))
    rat = bybit_ratio(get(f"{BYBIT}/v5/market/account-ratio",
                          {"category": "linear", "symbol": inst, "period": "1d"}))
    rows += [C.row("fut.ls_account_bybit", C.utc_day(ms), v, now, SOURCE, coin)
             for ms, v in rat if first <= C.utc_day(ms) < today]
    return rows


# BYBIT HAS NO CALL PATH (ruling 1 of 17 Oct 2026): it blocks the box's country
# as well as the laptop's, so it is as untestable as Binance was under D-2. Its
# reader stays in the tree, switched off in config, and is NOT in this table: a
# config flipped to enabled still calls nothing (collect() reports it off).
VENUES: dict[str, Callable[..., list[dict]]] = {"okx": okx, "deribit": deribit}


def collect(get: Callable[..., Any] = _get, *, cfg: Optional[dict] = None,
            first: Optional[dict] = None, today: Optional[str] = None,
            now: Optional[str] = None, backfill: bool = False
            ) -> tuple[list[dict], dict]:
    """(rows, summary). `first` maps a venue to its first day (default: the
    daily window). Each venue and coin isolated."""
    cfg = cfg or C.config()
    today = today or C.today_utc()
    now = now or C.now_iso()
    win = int(cfg.get("daily_window_days") or 14)
    default = (dt.date.fromisoformat(today) - dt.timedelta(days=win)).isoformat()
    rows: list[dict] = []
    summary: dict = {"venues": {}, "failed": [], "off": {}}
    for venue, spec in (cfg.get("venues") or {}).items():
        if venue not in VENUES or not spec.get("enabled"):
            summary["off"][venue] = spec.get("off") or "switched off"
            continue
        for coin, inst in (spec.get("inst") or {}).items():
            try:
                got = VENUES[venue](coin, inst, (first or {}).get(venue) or default,
                                    today, now, get, cfg, backfill)
                rows += got
                summary["venues"][f"{venue}[{coin}]"] = len(got)
            except Exception as exc:                            # noqa: BLE001
                summary["failed"].append((f"{venue}[{coin}]",
                                          f"{type(exc).__name__}: {exc}"[:240]))
                log.warning("fut: %s %s failed -- %s", venue, coin, exc)
    return rows, summary


def pull(run_id: Optional[str] = None, db=None, get: Callable[..., Any] = _get,
         **kw) -> dict:
    """The writer step (feeds.EXTERNAL_WRITERS): STALE-not-empty when every venue
    failed; a partial failure lands what it has and names the rest."""
    state: dict = {}

    def produce() -> list[dict]:
        rows, s = collect(get, **kw)
        state.update(s)
        if not rows and s["failed"]:
            raise RuntimeError("; ".join(f"{k}: {v}" for k, v in s["failed"])[:300])
        return rows
    out = pub.run(SOURCE, KEYS, produce, run_id=run_id, db=db)
    out["failed_series"] = state.get("failed") or []
    out["venues_off"] = state.get("off") or {}
    return out


def backfill(run_id: Optional[str] = None, db=None, get: Callable[..., Any] = _get,
             dry_run: bool = False, today: Optional[str] = None) -> dict:
    """Bounded history, point in time (config `backfill`): OKX funding about
    three months and OI a year; Deribit funding from 2019."""
    cfg = C.config()
    b = cfg.get("backfill") or {}
    today = today or C.today_utc()
    d0 = dt.date.fromisoformat(today)
    first = {"okx": (d0 - dt.timedelta(days=int(b.get("okx_oi_days") or 365))).isoformat(),
             "deribit": str(b.get("deribit_funding_from") or "2019-01-01"),
             "bybit": (d0 - dt.timedelta(days=60)).isoformat()}
    rows, s = collect(get, cfg=cfg, first=first, today=today, backfill=True)
    if dry_run:
        return {"status": "DRY_RUN", "parsed": len(rows), **s}
    out = pub.write_rows(SOURCE, rows, KEYS, run_id or "fut_backfill", db=db,
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
