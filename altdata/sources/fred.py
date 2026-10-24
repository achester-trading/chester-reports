"""
FRED (Federal Reserve Economic Data) fetcher.

API docs: https://fred.stlouisfed.org/docs/api/fred/

Auth:    API key required. Set FRED_API_KEY env var.
Limits:  120 requests per 60 seconds (FRED's published limit). The pull pauses
         PACING_SECONDS between calls, so it alone stays at or under 100 a
         minute; the ALFRED history (altdata/fred_history.py) paces the same and
         reads through the same fetch.

A BODY THAT IS NOT JSON (the feed repair of 24 Oct 2026, a61b). On 24 Oct about
fifteen series failed on one run with "Expecting value: line 1 column 1": FRED
answered 200-or-not with a body that was not JSON (an error or rate-limit page),
on the day the 1.9m-row ALFRED history ran beside the 16:10 pull. `get_json`
records the HTTP status and the first 120 characters of the body, retries with
backoff (at most RETRY_ATTEMPTS attempts, honouring Retry-After up to
RETRY_AFTER_CAP seconds), and then raises a FetchError whose text carries the
status; the pull marks that series STALE with it (altdata/feeds.py) and logs ONE
summary line per run, never a traceback per series.
Format:  Each series returns observations with 'date' and 'value' (string,
         '.' for missing). We coerce '.' to None.

This module pulls every series in altdata.config.FRED_PULL_SERIES into the store:
the Monthly's 59 (FRED_SERIES) and the signal-triage additions
(FRED_SIGNAL_SERIES, ST-1). ONE FRED PATH -- a second fetcher for the new series
would be a second answer to "which series does FRED feed and when".

INCREMENTAL PULLS (audit-leftovers-1, the 14 Oct audit's collection finding).
The scheduled pull used to re-read 1,500 days of every series every session.
aud-1's drop_unchanged stopped the re-read from writing (about 33,000 duplicate
rows a day), but the fetch was still the whole window. Now each series asks
FRED only for what it lacks: from its newest stored observation LESS A REVISION
WINDOW, by its release frequency (SESSION-SET; the reason beside each):

  daily      30 days    a daily series is restated within days, if at all
  weekly    120 days    H.4.1 and claims revise the prior weeks; a quarter is ample
  monthly   400 days    the release month plus the annual revisions (payrolls'
  quarterly 400 days    benchmark, GDP's annual update) reach about a year back

A series the store holds nothing for gets its FULL history (no observation_start).
The newest stored day is read from the series' CSV copy, which this pull merges
into and dual-writes beside the observation store. What a 400-day window does not catch -- a
seasonal-factor restatement five years back (CPI each February) -- is the FRED
history run's to take (`pull(..., full=True)`), a by-hand command, not a daily
cost. A caller that passes `lookback_days` keeps the old fixed window (the
Monthly's `--lookback-days`). The CSV copy is MERGED, not rewritten, so a narrow
fetch never truncates it (store.write_observations(merge=True)).
"""

from __future__ import annotations
import os
import time
import logging
import traceback
from typing import Callable, Optional

from ._base import FetchError, RETRY_BACKOFF, DEFAULT_TIMEOUT, USER_AGENT
from .. import config
from .. import session
from .. import secrets
from ..store import Store

log = logging.getLogger(__name__)

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"
PACING_SECONDS = 0.6  # pause between requests: at most 100 a minute, under FRED's 120
# The non-JSON path (24 Oct 2026): attempts in all, and the longest Retry-After
# honoured (SESSION-SET: a longer ask is capped, not ignored).
RETRY_ATTEMPTS = 3
RETRY_AFTER_CAP = 60.0
SNIPPET_CHARS = 120
# The revision window by release frequency, in days (SESSION-SET; the docstring
# gives the reasons). An unknown frequency takes the widest.
REVISION_WINDOW_DAYS = {"daily": 30, "weekly": 120, "monthly": 400, "quarterly": 400}
REVISION_WINDOW_DEFAULT = 400


def _get_key() -> str:
    # THROUGH THE ONE LOADER, which reads .env in-process when the variable is
    # not already in the environment. os.environ alone is why a by-hand run of this
    # module reported no key on a box whose systemd units had one: EnvironmentFile
    # populates the environment for a unit and for nothing else.
    key = secrets.get("FRED_API_KEY")
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


def fetch_start(spec, newest: Optional[str]) -> Optional[str]:
    """The observation_start one series asks for: its newest stored day less the
    revision window for its frequency, or None -- the full history -- when the
    store holds nothing for it."""
    from datetime import date, timedelta
    if not newest:
        return None
    days = REVISION_WINDOW_DAYS.get(str(getattr(spec, "freq", "")).lower(),
                                    REVISION_WINDOW_DEFAULT)
    return (date.fromisoformat(str(newest)[:10]) - timedelta(days=days)).isoformat()


def newest_stored(store: Store, key: str) -> Optional[str]:
    """The newest day with a value in the series' CSV copy -- the file this pull
    MERGES into, written in the same call as the observation store (the dual
    write), so the two hold the same newest day. None when there is no file, so
    a series new to this machine takes its full history. Reading the CSV opens no
    database, which keeps the pull's gates off the live store."""
    try:
        rows = store.read(key)
        days = [str(r["date"])[:10] for r in rows
                if isinstance(r, dict) and r.get("value") is not None and r.get("date")]
    except Exception as exc:                                    # noqa: BLE001
        log.warning("FRED: could not read the stored %s (%s); full history", key, exc)
        return None
    return max(days) if days else None


def _snippet(text: str) -> str:
    """The first SNIPPET_CHARS characters of a body, whitespace folded, redacted."""
    return secrets.redact(" ".join(str(text or "")[:SNIPPET_CHARS].split()))


def _retry_after(value) -> Optional[float]:
    """Retry-After in seconds (the delta form; an HTTP date is not honoured)."""
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        return None


def get_json(url: str, params: dict, get: Optional[Callable] = None,
             sleep: Callable = time.sleep) -> dict:
    """One FRED (or ALFRED) JSON read. A 4xx other than 429 is not retried; a
    429, a 5xx, a connection error or a body that is not JSON is retried up to
    RETRY_ATTEMPTS attempts in all, waiting Retry-After (capped) or a doubling
    backoff. The final FetchError names the HTTP status and the body's start."""
    import requests                                             # noqa: PLC0415
    get = get or requests.get
    last, wait = "no response", RETRY_BACKOFF
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        ra = None
        try:
            resp = get(url, params=params, timeout=DEFAULT_TIMEOUT,
                       headers={"User-Agent": USER_AGENT})
        except (requests.ConnectionError, requests.Timeout) as exc:
            last = f"{type(exc).__name__}"
        else:
            status = resp.status_code
            if 400 <= status < 500 and status != 429:
                raise FetchError(f"HTTP {status}: {_snippet(resp.text)}")
            if status < 300:
                try:
                    return resp.json()
                except ValueError:
                    last = f"HTTP {status}, body not JSON: {_snippet(resp.text)}"
            else:
                last = f"HTTP {status}: {_snippet(resp.text)}"
            ra = _retry_after((resp.headers or {}).get("Retry-After"))
        if attempt < RETRY_ATTEMPTS:
            sleep(min(RETRY_AFTER_CAP, ra) if ra is not None else wait)
            wait *= 2
    raise FetchError(f"{last} (after {RETRY_ATTEMPTS} attempts)")


def _fetch_series(fred_id: str, api_key: str, lookback_days: Optional[int] = None,
                  start: Optional[str] = None) -> list[tuple[str, Optional[float]]]:
    """Fetch one FRED series and return list of (date, value): from `start`, or
    `lookback_days` back, or -- with neither -- its whole history."""
    from datetime import date, timedelta
    if start is None and lookback_days is not None:
        start = (session.session_date_obj() - timedelta(days=lookback_days)).isoformat()
    params = {
        "series_id": fred_id,
        "api_key": api_key,
        "file_type": "json",
        "sort_order": "asc",
    }
    if start:
        params["observation_start"] = start
    data = get_json(FRED_BASE, params=params)
    obs = data.get("observations", [])
    return [(o["date"], _parse_value(o.get("value"))) for o in obs]


def summary_line(failed: list, total: int) -> str:
    """ONE line for the run: the count, and each failed key with its reason's
    first words."""
    parts = [f"{k} ({' '.join(str(r).split())[:60]})" for k, r in failed[:20]]
    more = f"; and {len(failed) - 20} more" if len(failed) > 20 else ""
    return f"fred: {len(failed)} of {total} series failed: " + "; ".join(parts) + more


def pull(store: Store, lookback_days: Optional[int] = None,
         series: Optional[list] = None, full: bool = False) -> dict:
    """
    Pull every series defined in config.FRED_PULL_SERIES into the store.

    `series` narrows the pull to a subset of SeriesSpec entries -- for a first
    pull of newly registered series without re-reading the other 59. The
    scheduled pull never passes it.

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

    specs = list(series) if series is not None else list(config.FRED_PULL_SERIES)
    total = len(specs)
    log.info("Pulling %d FRED series, %s", total,
             f"lookback={lookback_days} days" if lookback_days is not None else
             "the full history" if full else "incremental (newest stored less the "
                                             "revision window)")
    windows: dict[str, Optional[str]] = {}

    for i, spec in enumerate(specs, start=1):
        log.info("[%d/%d] %s (%s)", i, total, spec.key, spec.fred_id)
        try:
            start = (None if full or lookback_days is not None else
                     fetch_start(spec, newest_stored(store, spec.key)))
            windows[spec.key] = start
            obs = _fetch_series(spec.fred_id, api_key, None if full else lookback_days,
                                start=start)
            # MERGED into the CSV copy: a narrow fetch must never truncate it.
            n = store.write_observations(spec.key, obs, source="fred",
                                         merge=start is not None)
            latest = next((o for o in reversed(obs) if o[1] is not None), None)
            series_info[spec.key] = {
                "rows": n,
                "latest_date": latest[0] if latest else None,
                "latest_value": latest[1] if latest else None,
            }
            success += 1
        except FetchError as e:
            log.debug("  FAIL %s: %s", spec.key, secrets.redact(str(e)))
            failed.append((spec.key, secrets.redact(str(e))))
        except Exception as e:
            # AUD-1 2b: the traceback carries the exception's text, and a
            # requests error's text carries the URL with its api_key. At DEBUG
            # only (24 Oct 2026): the run's summary line below names it.
            log.debug("  unexpected error on %s: %s", spec.key,
                      secrets.redact(traceback.format_exc()))
            failed.append((spec.key, secrets.redact(f"unexpected: {type(e).__name__}: {e}")))

        # Be polite to FRED
        time.sleep(PACING_SECONDS)

    if failed:
        log.warning("%s", summary_line(failed, total))
    return {
        "total": total,
        "success": success,
        "failed": failed,
        "series": series_info,
        "windows": windows,
    }
