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
    """A source fetch ultimately failed after retries.

    ITS TEXT IS REDACTED AT CONSTRUCTION (AUD-1 item 2b). The text names the URL
    and the underlying error, and requests' own exception text carries the full
    query string -- FRED's `?api_key=` included -- so every FetchError message
    passes through secrets.redact() before anything can log or store it."""

    def __init__(self, *args) -> None:
        from .. import secrets                                  # noqa: PLC0415
        super().__init__(*[secrets.redact(str(a)) for a in args])


# A DESCRIPTIVE USER-AGENT, AND NO PERSONAL DATA IN IT.
#
# Probed, because the agencies disagree and both of them 403 rather than
# explaining:
#
#   bls.gov      200 for "chester-reports/1.0" and for a parenthetical comment;
#                403 for a UA containing a URL, and 403 for the default
#                python-requests agent.
#   sec.gov      403 for every form of this string. EDGAR's access policy requires
#                a CONTACT ADDRESS in the agent and enforces it, which is why
#                altdata/sources/edgar.py composes its own from an operator-set
#                variable and stays dormant until one exists -- rather than this
#                module carrying somebody's email address into every request it
#                makes to anybody.
#
# So: the default agent identifies the software and nothing else. A source that
# needs more says so in its own module.
#
# Ruled 17 Oct 2026: the default is the generic project string, which names the
# repository too (altdata/sources/user_agent.py). Re-probed that day from the
# laptop: api.bls.gov 200 for both the bare token and the string with the URL;
# www.bls.gov/feed 403 for every form, the bare token included, so the 25 Sep
# finding about a URL could not be re-tested from here.
from .user_agent import generic as _generic_ua                 # noqa: E402
# The project and its repository, never a person (ruled 17 Oct 2026).
USER_AGENT = _generic_ua()


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


def http_get_bytes(
    url: str,
    params: "Optional[dict]" = None,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = MAX_RETRIES,
    headers: "Optional[dict]" = None,
) -> bytes:
    """GET the RAW BODY. For XML, this is the only correct fetch.

    WHY NOT .text. `requests` guesses an encoding from the Content-Type header, and
    for `text/xml` WITHOUT a charset -- which is exactly what federalreserve.gov
    sends -- the HTTP standard's fallback is ISO-8859-1. So the UTF-8 BOM arrives
    as three Latin-1 characters, every smart quote in the feed becomes mojibake,
    and the XML parser reports "not well-formed (invalid token): line 1, column 1",
    which reads like a broken feed rather than a decoding guess.

    An XML document DECLARES its own encoding in its first line. Handing the parser
    the bytes lets it read that declaration and be right; handing it a string means
    somebody has already guessed. Both Fed feeds failed this way while BLS's worked,
    for no reason other than one of them states a charset in its headers.
    """
    last_err: "Optional[Exception]" = None
    backoff = RETRY_BACKOFF
    hdrs = {"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate"}
    hdrs.update(headers or {})
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params=params, timeout=timeout,
                                headers=hdrs)
            if 400 <= resp.status_code < 500:
                raise FetchError(
                    f"HTTP {resp.status_code} from {url}: {resp.text[:200]}")
            resp.raise_for_status()
            return resp.content
        except FetchError:
            raise
        except (requests.ConnectionError, requests.Timeout,
                requests.HTTPError) as e:
            last_err = e
            if attempt < max_retries - 1:
                time.sleep(backoff)
                backoff *= 2
            continue
    raise FetchError(f"Giving up on {url} after {max_retries} retries: {last_err}")


def http_get_response(
    url: str,
    params: "Optional[dict]" = None,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = MAX_RETRIES,
    headers: "Optional[dict]" = None,
) -> "tuple[bytes, dict]":
    """GET the raw body AND the response headers. Same retry policy.

    For a file whose PUBLICATION INSTANT is only in its headers. The Fed Board and
    the SF Fed republish a data file in place and the only statement of when this
    vintage appeared is Last-Modified; http_get_bytes throws it away. Headers are
    returned as a plain dict with lower-cased names.
    """
    last_err: "Optional[Exception]" = None
    backoff = RETRY_BACKOFF
    hdrs = {"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate"}
    hdrs.update(headers or {})
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params=params, timeout=timeout,
                                headers=hdrs)
            if 400 <= resp.status_code < 500:
                raise FetchError(
                    f"HTTP {resp.status_code} from {url}: {resp.text[:200]}")
            resp.raise_for_status()
            return resp.content, {k.lower(): v for k, v in resp.headers.items()}
        except FetchError:
            raise
        except (requests.ConnectionError, requests.Timeout,
                requests.HTTPError) as e:
            last_err = e
            if attempt < max_retries - 1:
                time.sleep(backoff)
                backoff *= 2
            continue
    raise FetchError(f"Giving up on {url} after {max_retries} retries: {last_err}")


def http_post_json(
    url: str,
    body: dict,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = MAX_RETRIES,
    headers: "Optional[dict]" = None,
):
    """POST a JSON body and return the parsed JSON response. Same retry policy.

    For a public query endpoint that takes its filter as a POST body (TPSO's CPI
    query, AQ-3 part 2). A read, not a write: nothing is submitted but the query.
    """
    last_err: "Optional[Exception]" = None
    backoff = RETRY_BACKOFF
    hdrs = {"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate"}
    hdrs.update(headers or {})
    for attempt in range(max_retries):
        try:
            resp = requests.post(url, json=body, timeout=timeout, headers=hdrs)
            if 400 <= resp.status_code < 500:
                raise FetchError(
                    f"HTTP {resp.status_code} from {url}: {resp.text[:200]}")
            resp.raise_for_status()
            return resp.json()
        except FetchError:
            raise
        except (requests.ConnectionError, requests.Timeout,
                requests.HTTPError) as e:
            last_err = e
            if attempt < max_retries - 1:
                time.sleep(backoff)
                backoff *= 2
            continue
    raise FetchError(f"Giving up on {url} after {max_retries} retries: {last_err}")


def http_get_text(
    url: str,
    params: Optional[dict] = None,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = MAX_RETRIES,
    headers: Optional[dict] = None,
) -> str:
    """GET a text endpoint -- RSS, Atom, anything not JSON. Same retry policy.

    Separate from http_get_json rather than a flag on it, because the two differ in
    what a SUCCESSFUL response means: json() raising is a broken payload, while text
    always succeeds and the parse comes later. Folding them would hide that.

    A 404 IS NOT RETRIED AND IS NOT AN OUTAGE. Three of the feeds probed for this
    (Treasury's press feeds, one BLS path) return 404 permanently, and a retry loop
    against a URL that does not exist wastes thirty seconds per pass to learn what
    the first request said.
    """
    last_err: Optional[Exception] = None
    backoff = RETRY_BACKOFF
    hdrs = {"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate"}
    hdrs.update(headers or {})
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params=params, timeout=timeout,
                                headers=hdrs)
            if 400 <= resp.status_code < 500:
                raise FetchError(
                    f"HTTP {resp.status_code} from {url}: {resp.text[:200]}")
            resp.raise_for_status()
            return resp.text
        except FetchError:
            raise
        except (requests.ConnectionError, requests.Timeout,
                requests.HTTPError) as e:
            last_err = e
            if attempt < max_retries - 1:
                time.sleep(backoff)
                backoff *= 2
            continue
    raise FetchError(f"Giving up on {url} after {max_retries} retries: {last_err}")


# THE CHAIN AND PRICE CALLS RETRY (AUD-1 item 5b, the audit of 14 Oct 2026). A
# Yahoo call that raises, or that returns an EMPTY frame -- which Yahoo does on a
# bad night without saying why -- was a missed capture, and a chain night is
# never served again. Three tries, the wait doubling from RETRY_BACKOFF.
RETRY_TRIES = 3


def retry_call(fn, *, tries: int = RETRY_TRIES, backoff: float = RETRY_BACKOFF,
               empty=None, sleep=time.sleep, label: str = ""):
    """fn() until it returns something `empty` does not call empty, up to
    `tries` times; an exception counts as a failed try. Returns the last result
    (which may be empty) or re-raises the last exception."""
    last_exc: Optional[BaseException] = None
    result = None
    wait = backoff
    for attempt in range(tries):
        try:
            result = fn()
            last_exc = None
            if empty is None or not empty(result):
                return result
        except Exception as exc:                              # noqa: BLE001
            last_exc = exc
        if attempt < tries - 1:
            sleep(wait)
            wait *= 2
    if last_exc is not None:
        raise last_exc
    return result
