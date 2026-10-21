"""
The banking system's unrealised securities gains and losses, from the FDIC's
BankFind Suite API (the bank-stress panel's balance-sheet line; signal-triage
Batch 12, item 59, ST-R6.59a; a53, 20 Oct 2026). The Quarterly Banking Profile's
figure, rebuilt from the same call reports.

    python -m altdata.sources.fdic_qbp                       # the last 8 quarters
    python -m altdata.sources.fdic_qbp --since 2007-03-31    # the history

SOURCE (checked 20 Oct 2026, F6). https://api.fdic.gov/banks/financials, keyless,
one call a quarter: filters=REPDTE:<yyyymmdd>, agg_by=REPDTE and
agg_sum_fields=SCAF,SCAA,SCHF,SCHA sums every insured institution's available-for-
sale securities at fair value (SCAF) and amortised cost (SCAA) and its
held-to-maturity securities at fair value (SCHF) and amortised cost (SCHA), in
THOUSANDS of dollars. api.fdic.gov answers robots.txt 404 (no rules); the check
runs on every pull.

STORED, one row a quarter-end, in DOLLARS, observed_at the quarter-end, available_at
the write instant (ingest_instant: the API carries no publication time per quarter):
  fdic.unrealised_afs     SCAF less SCAA
  fdic.unrealised_htm     SCHF less SCHA
  fdic.unrealised_total   the two together (the 2023 mechanism; the panel's line)
A new OFFICIAL writer.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
from typing import Callable, Optional

from . import _publication as pub
from ._base import http_get_json

log = logging.getLogger(__name__)

SOURCE = "fdic_qbp"
SITE = "https://api.fdic.gov"
URL = SITE + "/banks/financials"
KEYS = ["fdic.unrealised_afs", "fdic.unrealised_htm", "fdic.unrealised_total"]
FIELDS = ("SCAF", "SCAA", "SCHF", "SCHA")
QUARTERS = 8


def quarter_ends(since: str, until: str) -> list[str]:
    """Quarter-end dates (yyyy-mm-dd) from `since` to `until`, both inclusive."""
    out = []
    s, u = dt.date.fromisoformat(since), dt.date.fromisoformat(until)
    for y in range(s.year, u.year + 1):
        for m, d in ((3, 31), (6, 30), (9, 30), (12, 31)):
            q = dt.date(y, m, d)
            if s <= q <= u:
                out.append(q.isoformat())
    return out


def params(quarter: str) -> dict:
    return {"filters": f"REPDTE:{quarter.replace('-', '')}",
            "fields": "REPDTE," + ",".join(FIELDS), "agg_by": "REPDTE",
            "agg_sum_fields": ",".join(FIELDS), "limit": 1}


def rows_from_json(body: dict, quarter: str, available: str) -> list[dict]:
    """The quarter's three rows, or [] when the API holds none for it yet."""
    data = (body or {}).get("data") or []
    if not data:
        return []
    agg = data[0].get("data") or {}
    try:
        afs = (float(agg["sum_SCAF"]) - float(agg["sum_SCAA"])) * 1000.0
        htm = (float(agg["sum_SCHF"]) - float(agg["sum_SCHA"])) * 1000.0
    except (KeyError, TypeError, ValueError):
        return []

    def row(key: str, v: float) -> dict:
        return {"registry_key": key, "instrument": None, "observed_at": quarter,
                "available_at": available, "value": round(v, 0),
                "availability_kind": "ingest_instant"}
    return [row("fdic.unrealised_afs", afs), row("fdic.unrealised_htm", htm),
            row("fdic.unrealised_total", afs + htm)]


def fetch_rows(since: Optional[str] = None, get: Optional[Callable] = None,
               today: Optional[str] = None) -> list[dict]:
    from .. import session                                      # noqa: PLC0415
    ok, why = pub.robots_allows(SITE, URL)
    if not ok:
        raise PermissionError(f"robots.txt refuses {URL} ({why})")
    today = today or session.session_date()
    qs = quarter_ends(since or "1900-01-01", today)
    if not since:
        qs = qs[-QUARTERS:]
    get = get or (lambda q: http_get_json(URL, params=params(q), timeout=90))
    available = session.utc_iso()
    out = []
    for q in qs:
        out += rows_from_json(get(q), q, available)
    return out


def pull(run_id: Optional[str] = None, db=None, since: Optional[str] = None) -> dict:
    return pub.run(SOURCE, KEYS, lambda: fetch_rows(since), run_id=run_id, db=db,
                   **({"window_days": 40 * 366} if since else {}))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(prog="python -m altdata.sources.fdic_qbp")
    ap.add_argument("--since")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(since=a.since), indent=2, sort_keys=True, default=str))
