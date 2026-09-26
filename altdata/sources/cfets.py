"""
CFETS / China Money -- the USD/CNY central parity and the CGB 10-year yield.

    python -m altdata.sources.cfets          # one pull, summary to stdout

Signal-triage order ST-2 (§2.2.2-2.2.3, SR-3, SR-4): the fix is the first leg of
calc.cny_fix_dev and of the deliberate-devaluation tell (ST-5); the CGB 10-year is
the China leg of calc.uscn_10y_spread.

SOURCE. www.chinamoney.com.cn, the CFETS publication site, JSON, no key:
  /ags/ms/cm-u-bk-ccpr/CcprHisNew          central-parity history, by date range
  /ags/ms/cm-u-bk-currency/ClsYldCurvHis   CFETS closing government-bond yield
                                           curve (bondType CYCC000)

  cfets.cny_fix     USD/CNY central parity, CNY per USD. available_at = 09:15
                    Beijing on the fix date (the order's rule; the fix is
                    announced at 09:15 CST), `reconstructed`. A fix is never
                    revised. First pull backfills from BACKFILL_START a year per
                    request; later pulls read the last REFRESH_DAYS.
  cfets.cgb_10y     CGB 10-year closing yield, percent, observed_at = the curve
                    date. THE ENDPOINT IGNORES ITS DATE PARAMETERS and serves only
                    the latest curve (probed 26 Sep 2026: a request for 10 Sep
                    returned 24 Sep), so this is FORWARD-ONLY from the first run:
                    no history can be backfilled from here. available_at = the
                    write instant (`ingest_instant`).

WHY NOT FRED FOR CHINA 10Y. The order named IRLTLT01CNM156N; FRED returns 404 for
it, and FRED's China interest-rate series are 3-month rates only (checked 26 Sep
2026). Long history for the spread's China leg is therefore a calibration-script
problem (§1.10), not a store one.
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Optional
from zoneinfo import ZoneInfo

from .. import observations, session
from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "cfets"
FIX_URL = "https://www.chinamoney.com.cn/ags/ms/cm-u-bk-ccpr/CcprHisNew"
CURVE_URL = "https://www.chinamoney.com.cn/ags/ms/cm-u-bk-currency/ClsYldCurvHis"
BACKFILL_START = dt.date(2015, 1, 1)
REFRESH_DAYS = 30
FIX_TIME = dt.time(9, 15)
BEIJING = ZoneInfo("Asia/Shanghai")

FIX_KEY = "cfets.cny_fix"
CGB_KEY = "cfets.cgb_10y"
KEYS = [FIX_KEY, CGB_KEY]


def fix_available_at(day: str) -> str:
    local = dt.datetime.combine(dt.date.fromisoformat(day), FIX_TIME,
                                tzinfo=BEIJING)
    return observations.canonical_instant(
        local.astimezone(dt.timezone.utc).isoformat())


def fix_rows(payload: dict) -> list[dict]:
    head = (payload.get("data") or {}).get("head") or []
    if "USD/CNY" not in head and payload.get("records"):
        raise ValueError("central-parity response has no USD/CNY column")
    col = head.index("USD/CNY") if "USD/CNY" in head else 0
    out: list[dict] = []
    for rec in payload.get("records") or []:
        day = str(rec.get("date") or "")[:10]
        vals = rec.get("values") or []
        try:
            v = float(str(vals[col]).replace(",", ""))
        except (IndexError, ValueError):
            continue
        if len(day) == 10:
            out.append({"registry_key": FIX_KEY, "instrument": None,
                        "observed_at": day, "available_at": fix_available_at(day),
                        "value": v, "availability_kind": "reconstructed"})
    return out


def cgb_rows(payload: dict, available: str) -> list[dict]:
    for rec in payload.get("records") or []:
        try:
            term = float(rec.get("yearTermStr"))
        except (TypeError, ValueError):
            continue
        if abs(term - 10.0) < 1e-9:
            day = str(rec.get("newDateValueCN") or "")[:10]
            try:
                v = float(rec.get("maturityYieldStr"))
            except (TypeError, ValueError):
                return []
            return [{"registry_key": CGB_KEY, "instrument": None,
                     "observed_at": day, "available_at": available, "value": v,
                     "availability_kind": "ingest_instant"}]
    return []


def _fix_ranges(db) -> list[tuple[str, str]]:
    today = session.session_date_obj()
    own = db is None
    store = db or observations.ObservationStore()
    try:
        held = pub.newest_observed(store, [FIX_KEY]).get(FIX_KEY)
    finally:
        if own:
            store.close()
    start = (today - dt.timedelta(days=REFRESH_DAYS)) if held else BACKFILL_START
    out = []
    while start <= today:
        end = min(start + dt.timedelta(days=360), today)
        out.append((start.isoformat(), end.isoformat()))
        start = end + dt.timedelta(days=1)
    return out


# chinamoney refuses the bare python-requests agent (403), so a browser-style
# User-Agent and a Referer on its own site are sent.
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; chester-reports)",
           "Referer": "https://www.chinamoney.com.cn/english/"}
# AND IT REFUSES A PAGE LARGER THAN ITS OWN. Measured 26 Sep 2026: pageSize=20
# is served for any date range; pageSize=500 over the same range is 403. So the
# backfill pages through at the site's size, pausing between requests.
PAGE_SIZE = 20
PAGE_PAUSE_SECONDS = 0.5


def _get(url: str, params: dict) -> dict:
    import json
    data, _headers = http_get_response(url, params=params, timeout=60,
                                       headers=HEADERS)
    return json.loads(data.decode("utf-8"))


def pull(run_id: Optional[str] = None, db=None) -> dict:
    import time

    def produce() -> list[dict]:
        rows: list[dict] = []
        for start, end in _fix_ranges(db):
            page = 1
            while True:
                payload = _get(FIX_URL, {"startDate": start, "endDate": end,
                                         "currency": "USD/CNY",
                                         "pageNum": page,
                                         "pageSize": PAGE_SIZE})
                rows.extend(fix_rows(payload))
                total = int(((payload.get("data") or {}).get("pageTotal")) or 1)
                if page >= total:
                    break
                page += 1
                time.sleep(PAGE_PAUSE_SECONDS)
        curve = _get(CURVE_URL, {"lang": "EN", "reference": "1",
                                 "bondType": "CYCC000", "pageNum": 1,
                                 "pageSize": 50})
        rows.extend(cgb_rows(curve, session.utc_iso(timespec="microseconds")))
        return rows
    return pub.run(SOURCE, KEYS, produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
