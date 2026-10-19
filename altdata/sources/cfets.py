"""
CFETS / China Money -- the USD/CNY central parity and the CGB 10-year and 2-year
yields.

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
  cfets.cgb_2y      CGB 2-year closing yield, the 2.0-year point of the same
                    curve, same rules (forward-only). ST-R5.34b (16 Oct 2026;
                    Batch 6 item 34): China's leg of the G8 2-year panel. The
                    curve was checked live on 16 Oct 2026 and carries a 2.0 term.

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
from .user_agent import browser_like

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
CGB_2Y_KEY = "cfets.cgb_2y"
KEYS = [FIX_KEY, CGB_KEY, CGB_2Y_KEY]
CGB_TERMS = ((10.0, CGB_KEY), (2.0, CGB_2Y_KEY))


# THE BAND (AQ-3 part 1, 11 Oct 2026). Onshore USD/CNY may trade at most 2% either
# side of the day's central parity (the PBoC's rule since March 2014). The fix
# this writer stores is the band's centre, so the band arithmetic lives beside it
# and every reader computes the gap one way: altdata/market_features.py writes
# calc.cny_fix_gap_bp, calc.cny_band_position and the CNH rows from these.
BAND_PCT = 2.0


def gap_bp(spot: float, fix: float) -> float:
    """Spot against the fix, in basis points of the fix: + is spot weaker (more
    yuan per dollar) than the fix."""
    return 1e4 * (spot / fix - 1.0)


def band_position(spot: float, fix: float, band_pct: float = BAND_PCT) -> float:
    """Where spot sits in the trading band: 0 at the fix, +1 at the weak edge
    (fix x 1.02), -1 at the strong edge (fix x 0.98). Beyond +/-1 is outside the
    band -- possible for CNH, which the band does not bind."""
    return (spot / fix - 1.0) * 100.0 / band_pct


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
    """One row per CGB_TERMS point the curve carries; a term absent or
    unparseable is simply not stored."""
    out: list[dict] = []
    for want, key in CGB_TERMS:
        for rec in payload.get("records") or []:
            try:
                term = float(rec.get("yearTermStr"))
            except (TypeError, ValueError):
                continue
            if abs(term - want) < 1e-9:
                day = str(rec.get("newDateValueCN") or "")[:10]
                try:
                    v = float(rec.get("maturityYieldStr"))
                except (TypeError, ValueError):
                    break
                out.append({"registry_key": key, "instrument": None,
                            "observed_at": day, "available_at": available,
                            "value": v, "availability_kind": "ingest_instant"})
                break
    return out


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
HEADERS = {"User-Agent": browser_like(),
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
