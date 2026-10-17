"""
Deribit's DVOL -- the `deribit.*` family (DS-41; CD-3 of the crypto data-sources
order, Batch 4 Tranche A part 2; crypto-tranche-a-2, 17 Oct 2026). Config:
config/crypto_sources.yaml `deribit`.

    python -m altdata.sources.deribit                      # the daily pull
    python -m altdata.sources.deribit backfill [--dry-run] # from 24 Mar 2021

GET https://www.deribit.com/api/v2/public/get_volatility_index_data, no key
(www.deribit.com publishes no robots.txt: no rules). D-4 ruled DVOL now and
strike-level open interest later, with EL-12: nothing here fetches a book.

    deribit.dvol_btc   BTC DVOL, the UTC day's close (the 1D candle's close),
                       complete days only; history from 24 Mar 2021
    deribit.dvol_eth   the same for ETH

S-4's derived series (percentiles, DVOL less realised) are
altdata/sources/crypto_derived.py's.
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any, Callable, Optional

from . import _crypto as C
from . import _publication as pub
from ._base import http_get_json

log = logging.getLogger(__name__)

SOURCE = "deribit"
KEYS = ["deribit.dvol_btc", "deribit.dvol_eth"]
DAY_MS = 86_400_000


def _get(url: str, params: Optional[dict] = None) -> Any:
    return http_get_json(url, params=params, timeout=60)


def parse_dvol(doc: dict, today: str) -> list[tuple[str, float]]:
    """result.data [[ts, open, high, low, close], ...] -> [(UTC day, close)]."""
    res = (doc or {}).get("result")
    if res is None:
        raise ValueError(f"Deribit: no result ({(doc or {}).get('error')})")
    out = {}
    for r in res.get("data") or []:
        if isinstance(r, list) and len(r) >= 5 and C.num(r[4]) is not None:
            d = C.utc_day(r[0])
            if d < today:
                out[d] = C.num(r[4])
    return sorted(out.items())


def _ms(day: str) -> int:
    return int(dt.datetime.fromisoformat(day + "T00:00:00+00:00").timestamp() * 1000)


def collect(get: Callable[..., Any] = _get, *, first: Optional[str] = None,
            today: Optional[str] = None, now: Optional[str] = None
            ) -> tuple[list[dict], dict]:
    cfg = C.config()
    d = cfg.get("deribit") or {}
    today = today or C.today_utc()
    now = now or C.now_iso()
    first = first or (dt.date.fromisoformat(today)
                      - dt.timedelta(days=int(cfg.get("daily_window_days") or 14))
                      ).isoformat()
    win = int(d.get("window_days") or 900)
    rows: list[dict] = []
    summary: dict = {"series": {}, "failed": [], "calls": 0}
    for cur in d.get("currencies") or ["BTC", "ETH"]:
        key = f"deribit.dvol_{cur.lower()}"
        try:
            pts: dict[str, float] = {}
            t, end = _ms(first), _ms(today)
            while t < end:
                e = min(end, t + win * DAY_MS)
                summary["calls"] += 1
                pts.update(dict(parse_dvol(get(
                    f"{d.get('base') or 'https://www.deribit.com/api/v2'}"
                    f"/public/get_volatility_index_data",
                    {"currency": cur, "start_timestamp": t, "end_timestamp": e,
                     "resolution": "1D"}), today)))
                t = e
            got = sorted(pts.items())
            rows += [C.row(key, day, v, now, SOURCE) for day, v in got]
            summary["series"][key] = {"rows": len(got),
                                      "first": got[0][0] if got else None,
                                      "last": got[-1][0] if got else None}
        except Exception as exc:                                # noqa: BLE001
            summary["failed"].append((key, f"{type(exc).__name__}: {exc}"[:240]))
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


def backfill(run_id: Optional[str] = None, db=None, dry_run: bool = False,
             **kw) -> dict:
    """DVOL from its first print (config `deribit.dvol_from`), point in time."""
    first = str((C.config().get("deribit") or {}).get("dvol_from") or "2021-03-24")
    rows, s = collect(first=first, **kw)
    if dry_run:
        return {"status": "DRY_RUN", "parsed": len(rows), **s}
    out = pub.write_rows(SOURCE, rows, KEYS, run_id or "deribit_backfill", db=db,
                         window_days=100_000)
    return {**out, "failed_series": s["failed"], "calls": s["calls"]}


if __name__ == "__main__":
    import json
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    if sys.argv[1:2] == ["backfill"]:
        print(json.dumps(backfill(dry_run="--dry-run" in sys.argv), indent=2, default=str))
    else:
        print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
