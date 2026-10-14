"""
US rotary rigs in operation -- Baker Hughes' count, as the EIA republishes it.

    python -m altdata.sources.eia_rigs       # one pull, summary to stdout

AQ-3 part 1 (11 Oct 2026; the Quarterly's oil chapter, change order section 4.3,
"Supply response: rigs, frac spreads, DUCs"). The supply response's slowest
witness: rigs lead production by two to three quarters.

WHY THE EIA AND NOT BAKER HUGHES. rigcount.bakerhughes.com answers every
scripted request with an Akamai "Access Denied" -- its robots.txt included --
whatever the user agent (measured 11 Oct 2026), and this writer does not pass for
a browser. The EIA carries the same count, sourced to Baker Hughes, as no-key
history workbooks in the format altdata/sources/eia.py already reads:
  https://www.eia.gov/dnav/pet/hist_xls/<SERIES>m.xls, sheet "Data 1"
  E_ERTRRO_XR0_NUS_C   U.S. crude oil rotary rigs in operation (count)
  E_ERTRRG_XR0_NUS_C   U.S. natural gas rotary rigs in operation (count)
  E_ERTRR0_XR0_NUS_C   U.S. crude oil and natural gas rotary rigs (count)
MONTHLY, not weekly: the EIA publishes Baker Hughes' monthly averages, dated the
15th of the month, from 1973 (oil and gas split from 1987). The weekly count has
no free scriptable source; the notes name it under "No free source".

STORED, observed_at = the series' own date (the 15th of the month):
  eia.rigs_oil     crude oil rigs, count
  eia.rigs_gas     natural gas rigs, count
  eia.rigs_total   oil and gas rigs, count -- the EIA's own total series, never
                   the sum of the other two (miscellaneous rigs sit in neither)

AVAILABILITY. The workbook is republished in place; Last-Modified is the instant
this vintage appeared (`observed`), the write instant without it
(`ingest_instant`). Either is an upper bound for the history it carries.

The `eia` switch in config.ENABLED_SOURCES governs this writer too: the same
publisher, one switch.
"""

from __future__ import annotations

import logging
from typing import Optional

from .. import config
from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "eia_rigs"
URL = "https://www.eia.gov/dnav/pet/hist_xls/{sid}m.xls"
SERIES = {"eia.rigs_oil": "E_ERTRRO_XR0_NUS_C",
          "eia.rigs_gas": "E_ERTRRG_XR0_NUS_C",
          "eia.rigs_total": "E_ERTRR0_XR0_NUS_C"}
KEYS = list(SERIES)


def series_from_table(table: list[list], sid: str) -> dict[str, float]:
    """{date: count} from the 'Data 1' sheet. The sheet must name its series --
    the 'Sourcekey' row -- so a workbook for another series is refused rather
    than stored under this key; undated and blank rows are skipped."""
    named = any(len(r) > 1 and str(r[0]).strip() == "Sourcekey"
                and str(r[1]).strip() == sid for r in table[:4])
    if not named:
        raise ValueError(f"the EIA workbook does not name {sid} in its Sourcekey row")
    out: dict[str, float] = {}
    for row in table[3:]:
        day = pub.excel_serial_date(row[0] if row else None)
        v = row[1] if len(row) > 1 else None
        if day and isinstance(v, (int, float)) and not isinstance(v, bool):
            out[day] = float(v)
    if not out:
        raise ValueError(f"no dated rows in the EIA 'Data 1' sheet for {sid}")
    return out


def rows_from_series(series: dict[str, dict[str, float]], available: str,
                     kind: str) -> list[dict]:
    return [{"registry_key": key, "instrument": None, "observed_at": day,
             "available_at": available, "value": v, "availability_kind": kind}
            for key, by_day in series.items() for day, v in sorted(by_day.items())]


def _produce() -> list[dict]:
    if not config.ENABLED_SOURCES.get("eia"):
        raise RuntimeError("the eia switch in config.ENABLED_SOURCES is off")
    import xlrd  # noqa: PLC0415 -- requirements.txt, as eia.py
    series: dict[str, dict[str, float]] = {}
    newest = None
    for key, sid in SERIES.items():
        data, headers = http_get_response(URL.format(sid=sid), timeout=60)
        sheet = xlrd.open_workbook(file_contents=data).sheet_by_name("Data 1")
        series[key] = series_from_table(
            [sheet.row_values(r) for r in range(sheet.nrows)], sid)
        av = pub.availability(headers)
        newest = av if newest is None or av[0] > newest[0] else newest
    return rows_from_series(series, newest[0], newest[1])


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
