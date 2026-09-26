"""
EIA Weekly Petroleum Status Report -- US crude and product stocks.

    python -m altdata.sources.eia            # one pull, summary to stdout

Signal-triage order ST-2 (§2.5, SR-18): the US leg of the oil-buffer variable
(calc.oil_buffer_state, ST-4). This is the source behind the `eia` switch in
config.ENABLED_SOURCES, which ST-2 turns on; off means STALE with that reason.

SOURCE. EIA's per-series history workbooks, no key (the v2 API needs one; these
do not): https://www.eia.gov/dnav/pet/hist_xls/<SERIES>w.xls, sheet "Data 1",
rows of (Excel serial date, value) under three header rows. THOUSAND BARRELS in
the file, stored in BARRELS (x1000) -- the registry has no thousand-barrel unit,
and a scale that has to be remembered is one that will be remembered wrong.

  eia.crude_stocks     WCESTUS1  US ending stocks of crude oil EXCLUDING the SPR
  eia.total_stocks     WTESTUS1  US ending stocks of crude oil AND petroleum
                                 products, excluding the SPR
  eia.product_stocks   total minus crude for the same week -- the products leg,
                       one subtraction of two series from the same weekly report
                       (the report prints the total and the crude line; a
                       products-only history file was not found)

observed_at = the week-ending Friday. available_at = the following WEDNESDAY 10:30
ET, the WPSR release, `reconstructed` (the order's rule). A federal holiday moves
the release to Thursday; on those weeks the stamp is a day early -- the release
calendar is not in the repo, the same known imprecision as CFTC's.

-----------------------------------------------------------------------------
G-11 -- PROMPT TIME-SPREADS: NOT SOURCED
-----------------------------------------------------------------------------

The prompt spread needs the second-month contract. The one free history of it
was EIA's own NYMEX futures files (RCLC1/RCLC2, "Cushing, OK crude oil future
contract 1/2"); both END ON 5 APRIL 2024 -- measured 26 Sep 2026, last row
2024-04-05, still republished but no longer extended. yfinance's CL=F is the
front contract only, and CME settlement files are licensed. Brent has no free
second-month history at all. So `oil.prompt_spread` is registered
not_yet_sourced and is NOT written. Brent-WTI is computable from the held
fred.brent and fred.wti and is ST-4's feature, not a feed. Nothing in the repo
computes either today (G-11's other half: checked 26 Sep 2026, no prompt-spread
or Brent-WTI in daily_cascade/ or market_features).
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Optional

from .. import config, observations, session
from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "eia"
URL = "https://www.eia.gov/dnav/pet/hist_xls/{sid}w.xls"
SERIES = {"eia.crude_stocks": "WCESTUS1", "eia.total_stocks": "WTESTUS1"}
PRODUCT_KEY = "eia.product_stocks"
KEYS = list(SERIES) + [PRODUCT_KEY]
THOUSAND = 1000.0
NOT_SOURCED = ["oil.prompt_spread"]
RELEASE_ET = dt.time(10, 30)


def available_at(week_ending: str) -> str:
    """Wednesday 10:30 ET after the week-ending Friday, as canonical UTC."""
    wed = dt.date.fromisoformat(week_ending) + dt.timedelta(days=5)
    local = dt.datetime.combine(wed, RELEASE_ET, tzinfo=session._eastern_tz())
    return observations.canonical_instant(
        local.astimezone(dt.timezone.utc).isoformat())


def series_from_table(table: list[list]) -> dict[str, float]:
    """{week-ending date: value} from the 'Data 1' sheet's cells."""
    out: dict[str, float] = {}
    for row in table[3:]:
        day = pub.excel_serial_date(row[0] if row else None)
        v = row[1] if len(row) > 1 else None
        if day and isinstance(v, (int, float)) and not isinstance(v, bool):
            out[day] = float(v) * THOUSAND
    if not out:
        raise ValueError("no dated rows in the EIA 'Data 1' sheet")
    return out


def rows_from_series(series: dict[str, dict[str, float]]) -> list[dict]:
    rows: list[dict] = []

    def add(key, day, v):
        rows.append({"registry_key": key, "instrument": None, "observed_at": day,
                     "available_at": available_at(day), "value": v,
                     "availability_kind": "reconstructed"})
    for key, by_day in series.items():
        for day, v in by_day.items():
            add(key, day, v)
    crude, total = series.get("eia.crude_stocks", {}), series.get(
        "eia.total_stocks", {})
    for day in sorted(set(crude) & set(total)):
        add(PRODUCT_KEY, day, total[day] - crude[day])
    return rows


def _produce() -> list[dict]:
    if not config.ENABLED_SOURCES.get("eia"):
        raise RuntimeError("the eia switch in config.ENABLED_SOURCES is off")
    import xlrd  # noqa: PLC0415 -- requirements.txt, see acm.py
    series: dict[str, dict[str, float]] = {}
    for key, sid in SERIES.items():
        data, _h = http_get_response(URL.format(sid=sid), timeout=60)
        sheet = xlrd.open_workbook(file_contents=data).sheet_by_name("Data 1")
        series[key] = series_from_table(
            [sheet.row_values(r) for r in range(sheet.nrows)])
    return rows_from_series(series)


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
