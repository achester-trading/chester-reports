"""
FRED (Federal Reserve Economic Data) fetcher.

API docs: https://fred.stlouisfed.org/docs/api/fred/

Auth:    API key required. Set FRED_API_KEY env var.
Limits:  Generous (~120 requests per 60s). We pause briefly between calls.
Format:  Each series returns observations with 'date' and 'value' (string,
         '.' for missing). We coerce '.' to None.

This module pulls every series in altdata.config.FRED_SERIES into the store.
"""

from __future__ import annotations
import os
import time
import logging
from typing import Optional

from ._base import http_get_json, FetchError
from .. import config
from .. import session
from ..store import Store

log = logging.getLogger(__name__)

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"
PACING_SECONDS = 0.4  # pause between requests; well under FRED limit


def _get_key() -> str:
    key = os.environ.get("FRED_API_KEY")
    if not key:
        raise FetchError(
            "FRED_API_KEY environment variable is not set. "
            "Get a key at https://fredaccount.stlouisfed.org/apikeys "
            "and add it to your environment or GitHub secrets."
        )
    return key.strip()


def _parse_value(raw: str) -> Optional[float]:
    """FRED uses '.' for missing values."""
    if raw is None or raw == "." or raw == "":
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _fetch_series(fred_id: str, api_key: str, lookback_days: int) -> list[tuple[str, Optional[float]]]:
    """Fetch one FRED series and return list of (date, value)."""
    from datetime import date, timedelta
    start = (session.session_date_obj() - timedelta(days=lookback_days)).isoformat()
    params = {
        "series_id": fred_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": start,
        "sort_order": "asc",
    }
    data = http_get_json(FRED_BASE, params=params)
    obs = data.get("observations", [])
    return [(o["date"], _parse_value(o.get("value"))) for o in obs]


def pull(store: Store, lookback_days: int = 1500) -> dict:
    """
    Pull every series defined in config.FRED_SERIES into the store.

    Returns a summary dict:
        {
          'total': int,
          'success': int,
          'failed': list[(key, reason)],
          'series': {key: {'rows': int, 'latest_date': str, 'latest_value': float}},
        }
    """
    api_key = _get_key()

    success = 0
    failed: list[tuple[str, str]] = []
    series_info: dict[str, dict] = {}

    total = len(config.FRED_SERIES)
    log.info("Pulling %d FRED series, lookback=%d days", total, lookback_days)

    for i, spec in enumerate(config.FRED_SERIES, start=1):
        log.info("[%d/%d] %s (%s)", i, total, spec.key, spec.fred_id)
        try:
            obs = _fetch_series(spec.fred_id, api_key, lookback_days)
            n = store.write_observations(spec.key, obs, source="fred")
            latest = next((o for o in reversed(obs) if o[1] is not None), None)
            series_info[spec.key] = {
                "rows": n,
                "latest_date": latest[0] if latest else None,
                "latest_value": latest[1] if latest else None,
            }
            success += 1
        except FetchError as e:
            log.warning("  FAIL %s: %s", spec.key, e)
            failed.append((spec.key, str(e)))
        except Exception as e:
            log.exception("  unexpected error on %s", spec.key)
            failed.append((spec.key, f"unexpected: {e}"))

        # Be polite to FRED
        time.sleep(PACING_SECONDS)

    return {
        "total": total,
        "success": success,
        "failed": failed,
        "series": series_info,
    }
