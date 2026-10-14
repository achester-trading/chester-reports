"""
Bank of Thailand -- the policy rate, decision by decision.

    python -m altdata.sources.bot            # one pull, summary to stdout

AQ-3 part 2 (11 Oct 2026; the Quarterly's Thailand chapter, change order
section 4.10). ISOLATED: namespace thailand, never trigger_eligible -- the
chapter informs a private decision and nothing in the trading system.

TWO SOURCES, ONE KEY, verified 11 Oct 2026:
  1. THE MPC TABLE (keyless; always read). bot.or.th's policy-interest-rate page
     links a workbook of every decision since 23 May 2000, its filename changing
     with each meeting (.../policy-interest-rate/table-mpc-<year>-<n>-<tag>.xlsx),
     so the link is found on the page, never assumed. robots.txt disallows only
     /_layouts/, /_vti_bin/ and /_catalogs/. READ BY CONTENT: the header row is
     the one naming "Date" and "Policy rate"; a data row is a dated row with a
     numeric rate; the trailing remarks are not.
  2. THE BOT API (only with a key). gateway.api.bot.or.th/PolicyRate/v3/
     policy_rate/ answers 401 without an Authorization header. Its key is free
     but personal -- a SECRET: the operator puts it in .env as BOT_API_KEY, and
     this writer reads it from the environment and never prints it. With no key
     the writer logs "no key" and reads the table alone; the API adds only a
     decision the table has not caught up with.

  thai.bot_policy_rate   percent; observed_at = the decision date

AVAILABILITY. The BoT's release schedule is 14:05 Bangkok on the meeting date,
so each decision is stamped then, `reconstructed`, never after the write instant.
"""

from __future__ import annotations

import datetime as dt
import logging
import os
import re
from typing import Optional
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

from .. import observations, session
from . import _publication as pub
from ._base import http_get_response, http_get_text

log = logging.getLogger(__name__)

SOURCE = "bot"
PAGE_URL = ("https://www.bot.or.th/en/our-roles/monetary-policy/mpc-publication/"
            "policy-interest-rate.html")
TABLE_LINK = re.compile(r'href="([^"]*policy-interest-rate/table-mpc-[^"]*\.xlsx)"', re.I)
API_URL = "https://gateway.api.bot.or.th/PolicyRate/v3/policy_rate/"
KEY_ENV = "BOT_API_KEY"
KEY = "thai.bot_policy_rate"
KEYS = [KEY]
BANGKOK = ZoneInfo("Asia/Bangkok")
RELEASED = dt.time(14, 5)


def available_at(day: str, now: dt.datetime) -> str:
    t = dt.datetime.combine(dt.date.fromisoformat(day), RELEASED,
                            tzinfo=BANGKOK).astimezone(dt.timezone.utc)
    return observations.canonical_instant(min(t, now).isoformat())


def _row(day: str, rate: float, now: dt.datetime) -> dict:
    return {"registry_key": KEY, "instrument": None, "observed_at": day,
            "available_at": available_at(day, now), "value": rate,
            "availability_kind": "reconstructed"}


def decision_date(*cells) -> Optional[str]:
    """A decision's date from the first cell that carries one: an Excel serial,
    or text as the table writes it before 2019 -- "8-Feb-2017", or a two-day
    meeting "28-29 May 2013", dated its last day (when the decision was made)."""
    for c in cells:
        day = pub.excel_serial_date(c)
        if day:
            return day
        m = re.match(r"^\s*(?:\d{1,2}\s*-\s*)?(\d{1,2})[\s-]+([A-Za-z]{3})[A-Za-z]*\.?[\s-]+(\d{4})\s*$",
                     str(c or ""))
        if m:
            try:
                return dt.datetime.strptime(f"{m.group(1)} {m.group(2).title()} "
                                            f"{m.group(3)}", "%d %b %Y").date().isoformat()
            except ValueError:
                continue
    return None


def rows_from_table(table: list[list], now: dt.datetime) -> list[dict]:
    """The MPC workbook's sheet -> one row per decision."""
    head_i = next((i for i, r in enumerate(table[:10])
                   if any(str(c or "").strip() == "Date" for c in r)
                   and any("policy rate" in str(c or "").lower() for c in r)), None)
    if head_i is None:
        raise ValueError("the MPC table has no header naming 'Date' and 'Policy rate'")
    head = [str(c or "") for c in table[head_i]]
    di = next(i for i, c in enumerate(head) if c.strip() == "Date")
    ri = next(i for i, c in enumerate(head) if "policy rate" in c.lower())
    out = []
    for r in table[head_i + 1:]:
        if len(r) <= max(di, ri):
            continue
        day = decision_date(r[di], r[di - 1] if di else None)
        rate = r[ri]
        if day and isinstance(rate, (int, float)) and not isinstance(rate, bool):
            out.append(_row(day, float(rate), now))
    if not out:
        raise ValueError("no decisions in the MPC table")
    return out


def row_from_api(payload: dict, now: dt.datetime) -> Optional[dict]:
    res = payload.get("result") or {}
    day = str(res.get("announcement_date") or "")[:10]
    try:
        rate = float(res.get("data"))
    except (TypeError, ValueError):
        return None
    return _row(day, rate, now) if len(day) == 10 else None


def _produce() -> list[dict]:
    now = dt.datetime.fromisoformat(session.utc_iso())
    page = http_get_text(PAGE_URL, timeout=60)
    m = TABLE_LINK.search(page)
    if not m:
        raise ValueError("the policy-rate page links no MPC table")
    data, _h = http_get_response(urljoin(PAGE_URL, m.group(1)), timeout=60)
    sheets = pub.read_xlsx(data)
    rows: list[dict] = []
    for table in sheets.values():
        try:
            rows = rows_from_table(table, now)
            break
        except ValueError:
            continue
    if not rows:
        raise ValueError("no sheet of the MPC workbook carries the decision table")
    key = os.environ.get(KEY_ENV, "").strip()
    if not key:
        log.info("BoT API: no key (%s unset); the policy rate is read from the "
                 "MPC table alone", KEY_ENV)
    else:
        try:
            import json  # noqa: PLC0415
            body, _h = http_get_response(API_URL, headers={"Authorization": key},
                                         timeout=30, max_retries=1)
            got = row_from_api(json.loads(body.decode("utf-8")), now)
        except Exception as exc:                                # noqa: BLE001
            log.warning("BoT API: %s; the MPC table stands", type(exc).__name__)
            got = None
        if got and got["observed_at"] not in {r["observed_at"] for r in rows}:
            rows.append(got)
    return rows


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    if not os.environ.get(KEY_ENV, "").strip():
        print("no key")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
