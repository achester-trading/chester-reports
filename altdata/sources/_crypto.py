"""
What the Tranche A crypto writers share (crypto-tranche-a-1, 17 Oct 2026): the
config, the UTC day, the complete-day rule, a row's point-in-time stamp and the
funding annualisation. config/crypto_sources.yaml.

POINT IN TIME, as altdata/sources/llama.py writes it (the crypto basket's
conventions; the ST-13 fetcher the order names was never built):
  observed_at   the UTC day the figure describes (crypto trades every day);
  available_at  the pull instant, availability_kind `ingest_instant` -- never
                backdated, so a backfilled day is knowable from the pull, not before;
  history       a UTC day is written only once it has ended;
  a snapshot    (a venue's current open interest, the mempool now) is the pull's
                own UTC day, and a later pull the same day writes a new vintage.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO / "config" / "crypto_sources.yaml"
DAYS_PER_YEAR = 365.0


def config(path: Optional[Path] = None) -> dict:
    import yaml  # noqa: PLC0415
    return yaml.safe_load((path or CONFIG_PATH).read_text(encoding="utf-8")) or {}


def utc_day(ms_or_s: Any) -> str:
    """A UTC date from epoch milliseconds or seconds."""
    v = float(ms_or_s)
    if v > 1e11:
        v /= 1000.0
    return dt.datetime.fromtimestamp(v, dt.timezone.utc).date().isoformat()


def today_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


def now_iso() -> str:
    from .. import session  # noqa: PLC0415
    return session.utc_iso(timespec="microseconds")


def num(v: Any) -> Optional[float]:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if f != f else f


def row(key: str, day: str, value: Any, now: str, source: str,
        instrument: Optional[str] = None) -> dict:
    return {"registry_key": key, "instrument": instrument, "observed_at": day,
            "available_at": now, "value": value, "source": source,
            "availability_kind": "ingest_instant"}


def per_day(points: list[tuple[int, float]]) -> int:
    """Prints a day, from the median spacing of the prints themselves: 24 for
    an hourly venue, 3 for an eight-hourly one, 6 for a four-hourly contract."""
    ts = sorted(int(ms) for ms, _ in points)
    gaps = sorted(b - a for a, b in zip(ts, ts[1:]) if b > a)
    if not gaps:
        return 0
    med = gaps[len(gaps) // 2]
    return max(1, round(86_400_000 / med))


def daily_funding(points: list[tuple[int, float]], today: str,
                  expected: int | None = None) -> list[tuple[str, float]]:
    """Funding prints [(epoch ms, rate per period)] -> [(UTC day, annualised %)].

    A venue pays every hour (Hyperliquid, Deribit's interest_1h) or every eight
    (OKX, Bybit), and some contracts move to four. The day's annualised rate is
    the SUM of the day's prints times 365, so the interval never has to be
    assumed: 24 hourly prints and 3 eight-hourly prints at the same per-hour rate
    give the same figure. Only complete UTC days (before `today`), and only days
    carrying every print the venue's spacing implies (`expected`, else per_day()):
    a day short of a settlement is not written rather than understated."""
    need = expected or per_day(points)
    by: dict[str, list[float]] = {}
    for ms, rate in points:
        if rate is None:
            continue
        by.setdefault(utc_day(ms), []).append(rate)
    out = []
    for day in sorted(by):
        if day >= today or not need or len(by[day]) < need:
            continue
        out.append((day, 100.0 * DAYS_PER_YEAR * sum(by[day])))
    return out
