"""
Shared HTTP helpers.

Wraps requests.get with:
- Sensible timeout
- A small retry loop for transient 5xx/connection errors
- Optional rate-limit pacing (FRED is generous; we still pause briefly)
"""

from __future__ import annotations
import time
import requests
from typing import Optional


DEFAULT_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0  # seconds; doubles each retry


class FetchError(RuntimeError):
    """A source fetch ultimately failed after retries."""


def http_get_json(
    url: str,
    params: Optional[dict] = None,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = MAX_RETRIES,
) -> dict:
    """GET a JSON endpoint. Retries on 5xx and connection errors.
    Raises FetchError on final failure or non-2xx after retries."""
    last_err: Optional[Exception] = None
    backoff = RETRY_BACKOFF
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params=params, timeout=timeout)
            # 4xx (auth, bad request) — don't retry, surface immediately
            if 400 <= resp.status_code < 500:
                raise FetchError(
                    f"HTTP {resp.status_code} from {url}: {resp.text[:200]}"
                )
            resp.raise_for_status()
            return resp.json()
        except FetchError:
            raise
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
            last_err = e
            if attempt < max_retries - 1:
                time.sleep(backoff)
                backoff *= 2
            continue
    raise FetchError(f"Giving up on {url} after {max_retries} retries: {last_err}")
