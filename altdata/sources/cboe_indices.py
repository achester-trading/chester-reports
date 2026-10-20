"""
Cboe's daily history files for three indices: the 1- and 3-month implied
correlation indices (COR1M, COR3M) and the S&P 500 dispersion index (DSPX).

    python -m altdata.sources.cboe_indices    # one pull

ST-R4.18a, its history (16 Oct 2026 ruling (e): "the COR1M and COR3M history is
wanted"). Yahoo serves ^COR1M and ^COR3M as a quote without history, so the
dispersion panel's percentiles would fill from the first pull; Cboe publishes the
whole daily history as one CSV per index, so they have their window from the first
run. DSPX rides the same reader: Yahoo's ^DSPX starts 22 May 2024, Cboe's file 19
Jun 2014. Read by altdata/batch5b.py's dispersion(), which takes the Cboe key
first and Yahoo's as the fallback (config/batch5_tranche_1b.yaml).

A new writer, NOT held: the D1c ruling of 16 Oct 2026 ("WAL and the busy timeout
satisfy D1c for an append-only writer in the scheduled pulls"). On
altdata/feeds.py EXTERNAL_WRITERS.

SOURCE (checked 16 Oct 2026). The index dashboards on www.cboe.com link
  https://cdn.cboe.com/api/global/us_indices/daily_prices/<SYM>_History.csv
which answers 307 to the same path on cdn-api.cboe.com; both hosts answer
robots.txt with 403, which RFC 9309 (2.3.1.3) reads as no rules -- the reading
altdata/listings.py takes for Nasdaq Trader. www.cboe.com's own robots.txt
disallows /book/ and the volume reports only. The robots check runs on every
pull, on both hosts, through aaii.robots_verdict (the wildcard-aware reader),
and a refusal writes nothing. No key; Last-Modified sent (16 Oct 2026 21:31 GMT
for that day's close).

THE FILES. COR1M and COR3M: DATE,OPEN,HIGH,LOW,CLOSE, from 3 Jan 2006, the
CLOSE column read (the intraday OPEN/HIGH/LOW of an index computed from option
quotes are not stored). DSPX: DATE,DSPX, from 19 Jun 2014. DATE is MM/DD/YYYY.
Columns are found by name, never position; a blank or non-numeric value is
skipped, never zero. observed_at is the session date. Every row of a download
carries the file's Last-Modified (observed), so the deep history is knowable
from the first pull and not before: an as-of read before then sees nothing.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import logging
from typing import Callable, Optional

from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "cboe_indices"
BASE = "https://cdn.cboe.com/api/global/us_indices/daily_prices/"
ROBOTS = ("https://cdn.cboe.com/robots.txt", "https://cdn-api.cboe.com/robots.txt")
AGENT = "chester-reports"

# symbol -> (store key, the value column's name)
FILES = {"COR1M": ("cboe.cor1m", "CLOSE"),
         "COR3M": ("cboe.cor3m", "CLOSE"),
         "DSPX": ("cboe.dspx", "DSPX")}
# A literal list: feeds.static_keys() reads it from source.
KEYS = ["cboe.cor1m", "cboe.cor3m", "cboe.dspx"]
assert KEYS == [k for k, _ in FILES.values()]


def url(sym: str) -> str:
    return f"{BASE}{sym}_History.csv"


def rows_from_csv(text: str, sym: str, available: str, kind: str) -> list[dict]:
    key, col = FILES[sym]
    reader = csv.reader(io.StringIO(text.lstrip("﻿")))
    head = [h.strip().upper() for h in next(reader, [])]
    if "DATE" not in head or col not in head:
        raise ValueError(f"{sym}: expected DATE and {col} columns, got {head}")
    di, vi = head.index("DATE"), head.index(col)
    out = []
    for r in reader:
        if len(r) <= max(di, vi):
            continue
        try:
            day = dt.datetime.strptime(r[di].strip(), "%m/%d/%Y").date().isoformat()
            x = float(r[vi])
        except ValueError:
            continue                           # blank or malformed: skipped, never zero
        out.append({"registry_key": key, "instrument": None, "observed_at": day,
                    "available_at": available, "value": x,
                    "availability_kind": kind})
    if not out:
        raise ValueError(f"{sym}: no daily rows in Cboe's history file")
    return out


def _robots_text(robots_url: str) -> str:
    import requests                                             # noqa: PLC0415
    r = requests.get(robots_url, timeout=30, headers={"User-Agent": AGENT})
    if 400 <= r.status_code < 500:
        return ""                    # unavailable: no rules (RFC 9309, 2.3.1.3)
    r.raise_for_status()
    return r.text


def robots_ok(get: Optional[Callable[[str], str]] = None) -> tuple[bool, str]:
    """Both hosts the download touches, by the wildcard-aware reader."""
    from .aaii import robots_verdict                            # noqa: PLC0415
    get = get or _robots_text
    for ru in ROBOTS:
        host = ru.rsplit("/", 1)[0]
        ok, rule = robots_verdict(get(ru), f"{host}/api/global/us_indices/daily_prices/"
                                  f"COR1M_History.csv", AGENT)
        if not ok:
            return False, f"{ru} refuses it ({rule})"
    return True, ""


def fetch_rows() -> list[dict]:
    ok, why = robots_ok()
    if not ok:
        raise PermissionError(f"robots.txt: {why}")
    rows: list[dict] = []
    for sym in FILES:
        data, headers = http_get_response(url(sym), timeout=60)
        available, kind = pub.availability(headers)
        rows.extend(rows_from_csv(data.decode("utf-8", errors="replace"), sym,
                                  available, kind))
    return rows


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, fetch_rows, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
