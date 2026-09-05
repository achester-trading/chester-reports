"""
State emission — the producer half of the system-state contract.

Every report pushes a small state record to the Cloudflare Worker at the end of
its run. The dashboard reads the assembled view from the Worker. This is what
lets one glance replace composing system state from five separate places.

Two rules, both learned from Session 1:

1. **Never raise.** A failed state POST must not fail a report run. The report
   is the product; state emission is telemetry. Same failure philosophy as the
   narrative step — log it and continue.

2. **Producers report `as_of`, not freshness.** The Worker computes staleness at
   read time, so a producer that stopped running cannot claim to be fresh. If
   this module reported its own freshness, a dead pipeline would look healthy.

Configuration (both optional — absent means emission is skipped, not failed):
    CHESTER_STATE_URL    e.g. https://chester-state.<subdomain>.workers.dev
    CHESTER_STATE_TOKEN  shared secret, must match the Worker's secret
"""

from __future__ import annotations
import datetime as dt
import json
import logging
import os
import urllib.error
import urllib.request
from typing import Optional

from altdata import session

log = logging.getLogger(__name__)

VALID_KEYS = {
    "monthly_macro",
    "top_bottom",
    "disruptive_themes",
    "alt_asset",
    "daily_cascade",
    "gamma_weekly",
}

TIMEOUT_SECONDS = 10


def emit(report_key: str,
         status: str,
         headline: str = "",
         detail: Optional[dict] = None,
         as_of: Optional[dt.date] = None) -> bool:
    """POST one report's state to the Worker. Returns True on success.

    Never raises. Returns False on any failure, including missing config.
    """
    if report_key not in VALID_KEYS:
        log.warning("emit: unknown report key %r (known: %s)",
                    report_key, ", ".join(sorted(VALID_KEYS)))
        return False

    base = os.environ.get("CHESTER_STATE_URL", "").rstrip("/")
    token = os.environ.get("CHESTER_STATE_TOKEN", "")
    if not base or not token:
        log.info("emit: CHESTER_STATE_URL/TOKEN not set — state emission skipped")
        return False

    payload = {
        "status": status,
        "as_of": (as_of.isoformat() if as_of else session.session_date()),
        "headline": headline,
        "detail": detail or {},
    }

    req = urllib.request.Request(
        url=f"{base}/state/{report_key}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Chester-Token": token},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            if 200 <= resp.status < 300:
                log.info("emit: %s state posted (%s)", report_key, status)
                return True
            log.warning("emit: %s returned HTTP %s", report_key, resp.status)
            return False
    except urllib.error.HTTPError as e:
        # 401 is the common one — token mismatch between repo and Worker secrets.
        log.warning("emit: %s failed HTTP %s (%s)", report_key, e.code,
                    "check CHESTER_STATE_TOKEN matches the Worker secret"
                    if e.code == 401 else e.reason)
        return False
    except Exception as e:  # noqa: BLE001 — telemetry must never break the run
        log.warning("emit: %s failed (%s: %s)", report_key, type(e).__name__, e)
        return False
