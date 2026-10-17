"""
TPSO (Thailand's Trade Policy and Strategy Office, Ministry of Commerce) --
headline CPI, monthly.

    python -m altdata.sources.tpso           # one pull, summary to stdout

AQ-3 part 2 (11 Oct 2026; the Quarterly's Thailand chapter). ISOLATED:
namespace thailand, never trigger_eligible.

WHY NOT FRED. FRED carries Thai CPI only annually (FPCPITOTLZGTHA, World Bank);
the OECD monthly series it once mirrored (THACPIALLMINMEI) answers 404 (checked
11 Oct 2026). The Commerce Ministry's own index service is keyless:
  POST https://index.tpso.go.th/api/cpig/filter   (JSON body; robots.txt on
       index.tpso.go.th allows every agent but Googlebot's listed paths)
The api host behind it (index-api.tpso.go.th/api/*) answers 403 directly and is
not used.

READ BY CONTENT. The response is a list of commodities; the one with
commodityCode "00000" (ALL COMMODITIES) is read, and within it each month whose
type is "TG" (the whole kingdom). Years are BUDDHIST ERA (less 543). The base is
the one asked for, 2023 = 100 (YearBase 2566); the series runs from January 1976.

  thai.cpi       headline CPI, index 2023 = 100
  thai.cpi_yoy   its change on a year earlier, percent, as TPSO computes it

AVAILABILITY. The service sends no Last-Modified and TPSO releases the month's
CPI in the first week of the next, so each month is stamped the 10th of the
following month at 10:30 Bangkok by rule, `reconstructed` -- an upper bound --
and never after the write instant. The first pull reads the whole history;
later pulls the last REFRESH_MONTHS (TPSO revises nothing but the latest).
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Optional
from zoneinfo import ZoneInfo

from .. import observations, session
from . import _publication as pub
from ._base import http_post_json

log = logging.getLogger(__name__)

SOURCE = "tpso"
URL = "https://index.tpso.go.th/api/cpig/filter"
YEAR_BASE = 2566                     # 2023 = 100, in the Buddhist Era
ALL_ITEMS = "00000"
WHOLE_KINGDOM = "TG"
BE_OFFSET = 543
FIRST = (1976, 1)
REFRESH_MONTHS = 24
BANGKOK = ZoneInfo("Asia/Bangkok")
KEYS = ["thai.cpi", "thai.cpi_yoy"]


def available_at(year: int, month: int, now: dt.datetime) -> str:
    y, m = (year + 1, 1) if month == 12 else (year, month + 1)
    t = dt.datetime(y, m, 10, 10, 30, tzinfo=BANGKOK).astimezone(dt.timezone.utc)
    return observations.canonical_instant(min(t, now).isoformat())


def body(start: tuple[int, int], end: tuple[int, int]) -> dict:
    return {"YearBase": YEAR_BASE, "Categories": [ALL_ITEMS], "TimeOption": True,
            "Period": {"StartYear": start[0] + BE_OFFSET, "StartMonth": start[1],
                       "EndYear": end[0] + BE_OFFSET, "EndMonth": end[1]},
            "Types": [WHOLE_KINGDOM]}


def rows_from_payload(payload, now: dt.datetime) -> list[dict]:
    items = [c for c in (payload or []) if isinstance(c, dict)
             and c.get("commodityCode") == ALL_ITEMS]
    if not items:
        raise ValueError("the TPSO response carries no ALL COMMODITIES (00000) series")
    out = []
    for y in items[0].get("years") or []:
        year = int(y["year"]) - BE_OFFSET
        for m in y.get("months") or []:
            if m.get("type") != WHOLE_KINGDOM:
                continue
            month = int(m["month"])
            obs = pub.month_start(year, month)
            av = available_at(year, month, now)
            for key, field in (("thai.cpi", "index"), ("thai.cpi_yoy", "changeYear")):
                v = m.get(field)
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    out.append({"registry_key": key, "instrument": None,
                                "observed_at": obs, "available_at": av,
                                "value": float(v), "availability_kind": "reconstructed"})
    if not any(r["registry_key"] == "thai.cpi" for r in out):
        raise ValueError("the TPSO response has no whole-kingdom index values")
    return out


def _start(db) -> tuple[int, int]:
    own = db is None
    store = db or observations.ObservationStore()
    try:
        held = pub.newest_observed(store, KEYS).get("thai.cpi")
    finally:
        if own:
            store.close()
    if not held:
        return FIRST
    d = session.session_date_obj()
    n = d.year * 12 + d.month - 1 - REFRESH_MONTHS
    return n // 12, n % 12 + 1


def pull(run_id: Optional[str] = None, db=None) -> dict:
    def produce() -> list[dict]:
        today = session.session_date_obj()
        payload = http_post_json(URL, body(_start(db), (today.year, today.month)),
                                 timeout=60)
        return rows_from_payload(payload, dt.datetime.fromisoformat(session.utc_iso()))
    return pub.run(SOURCE, KEYS, produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
