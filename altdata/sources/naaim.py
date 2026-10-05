"""
NAAIM Exposure Index -- retried once a week, never a feed whose absence alarms.

    python -m altdata.sources.naaim pull [--force] [--dry-run]

T2.2 rulings of 5 Oct 2026 (item 4): "NAAIM retried at each weekly pull". One of
the W9 gauges.

WHAT CHANGED AT NAAIM, AND WHY THIS IS NOT IN THE FRESHNESS ROSTER. naaim.org
states that from 1 August 2026 the index moved to a subscription-based access
model. Its page still embeds a public widget, https://index.naaim.org/embeddable/
number, which is the only thing this module reads: no login, no subscription
content, robots.txt obeyed (a host whose robots.txt cannot be read is treated as
disallowing, as the voices scan does). On 4 and 5 Oct 2026 index.naaim.org did
not answer at all. So the retry is weekly (Thursdays, the day after members
report), and the module is NOT an external writer: a source expected to be
unavailable would otherwise mark the feeds stale every morning and raise the
heartbeat's FEED STALE alert. The W9 panel prints "not yet tracked" until a
reading is stored.

  naaim.exposure   the week's NAAIM number (members' average equity exposure, %),
                   observed_at = the date the widget states

The parser is deliberately strict: a number and a date it can both read, or
nothing stored and the reason printed.
"""

from __future__ import annotations

import datetime as dt
import logging
import re
from typing import Optional

from .. import observations, session

log = logging.getLogger(__name__)

URL = "https://index.naaim.org/embeddable/number"
KEY = "naaim.exposure"
SOURCE = "naaim"
DUE_WEEKDAY = 3                                   # Thursday, US Eastern


def parse_widget(html: str) -> Optional[dict]:
    """{'date', 'value'} from the widget's text, or None."""
    text = re.sub(r"<[^>]+>", " ", html or "")
    text = re.sub(r"\s+", " ", text)
    v = re.search(r"(?<![\d.])(-?\d{1,3}\.\d{1,2})(?![\d.])", text)
    d = (re.search(r"\b(\d{1,2})/(\d{1,2})/(20\d\d)\b", text)
         or re.search(r"\b(20\d\d)-(\d{2})-(\d{2})\b", text))
    if not v or not d:
        return None
    try:
        if "/" in d.group(0):
            day = dt.date(int(d.group(3)), int(d.group(1)), int(d.group(2)))
        else:
            day = dt.date(int(d.group(1)), int(d.group(2)), int(d.group(3)))
    except ValueError:
        return None
    val = float(v.group(1))
    if not -200.0 <= val <= 200.0:
        return None
    return {"date": day.isoformat(), "value": val}


def pull(db=None, *, force: bool = False, dry_run: bool = False,
         fetcher=None, today: Optional[dt.date] = None) -> dict:
    today = today or session.to_eastern(dt.datetime.now(dt.timezone.utc)).date()
    if not force and today.weekday() != DUE_WEEKDAY:
        return {"state": "not_due", "reason": "NAAIM is retried on Thursdays"}
    from .voices_scan import Fetcher, user_agent                # noqa: PLC0415
    ua = user_agent()
    if not ua and fetcher is None:
        return {"state": "not_configured", "reason": "CHESTER_SEC_CONTACT is unset"}
    f = fetcher or Fetcher(ua, 1.0)
    if not f.allowed(URL):
        return {"state": "unreachable",
                "reason": "robots.txt unreadable or disallowing the widget"}
    try:
        html = f.get(URL).decode("utf-8", "replace")
    except Exception as exc:                                    # noqa: BLE001
        return {"state": "unreachable", "reason": f"{type(exc).__name__}: {exc}"[:160]}
    got = parse_widget(html)
    if not got:
        return {"state": "unparsed",
                "reason": "the widget served no number and date the parser reads"}
    row = {"registry_key": KEY, "instrument": None, "observed_at": got["date"],
           "available_at": session.utc_iso(), "value": got["value"], "source": SOURCE}
    if dry_run:
        return {"state": "ok", "dry_run": True, **got}
    own = db is None
    st = db or observations.ObservationStore()
    try:
        st.write_many([row])
    finally:
        if own:
            st.close()
    return {"state": "ok", **got}


if __name__ == "__main__":                                     # pragma: no cover
    import argparse
    import json
    ap = argparse.ArgumentParser(description="NAAIM, retried weekly.")
    ap.add_argument("cmd", choices=["pull"])
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    print(json.dumps(pull(force=a.force, dry_run=a.dry_run), indent=2))
