"""
EIA's buffer series for the Alternative Assets Quarterly's oil-and-energy chapter
(b69-quarterly-readers-1; D34 of 24 Oct 2026; B67 section 1-4).

    python -m altdata.sources.eia_buffers        # one pull, summary to stdout

TERMS (re-read 25 Oct 2026, https://www.eia.gov/about/copyrights_reuse.php): "U.S.
government publications are in the public domain and are not subject to copyright
protection", with an acknowledgment asked for. robots.txt (www.eia.gov) allows
/dnav/. The same keyless history workbooks altdata/sources/eia.py reads, sheet
"Data 1", rows of (Excel serial date, value) under three header rows.

  eia.spr_stocks       WCSSTUS1 (weekly)  the Strategic Petroleum Reserve, BARRELS
                                          (thousand barrels in the file, x1000)
  eia.refinery_util    WPULEUS3 (weekly)  refinery operable utilisation, percent
  eia.gas_storage      NW2_EPG0_SWO_R48_BCF (weekly)  working gas in storage,
                                          Lower 48, billion cubic feet
  eia.lng_exports      N9133US2 (monthly) US LNG exports, million cubic feet.
                                          B67: EIA's files carry monthly EXPORTS,
                                          not daily feedgas; the chapter's row
                                          reads "LNG exports (monthly)" and
                                          feedgas stays not tracked.

AVAILABILITY, reconstructed, each by the release's own rule:
  - the WPSR series (SPR, utilisation): the Wednesday 10:30 ET after the
    week-ending Friday (eia.available_at; a holiday week's Thursday release makes
    it a day early, the same imprecision eia.py states);
  - gas storage: the Thursday 10:30 ET after the week-ending Friday (the Weekly
    Natural Gas Storage Report);
  - LNG exports: the end of the SECOND month after the reference month, 16:00 ET
    (the Natural Gas Monthly publishes about two months after the month; session-
    set, its bound in config/publication_lags.yaml).
"""
from __future__ import annotations

import datetime as dt
import logging
from typing import Optional

from .. import config
from . import _publication as pub
from . import _quarterly_common as qc
from ._base import http_get_response, http_get_text
from . import eia

log = logging.getLogger(__name__)

SOURCE = "eia"
PET = "https://www.eia.gov/dnav/pet/hist_xls/{sid}.xls"
NG = "https://www.eia.gov/dnav/ng/hist_xls/{sid}.xls"
SERIES = {
    "eia.spr_stocks": (PET, "WCSSTUS1w", 1000.0, "wpsr"),
    "eia.refinery_util": (PET, "WPULEUS3w", 1.0, "wpsr"),
    "eia.gas_storage": (NG, "NW2_EPG0_SWO_R48_BCFw", 1.0, "storage"),
    "eia.lng_exports": (NG, "N9133US2m", 1.0, "monthly"),
}
KEYS = ["eia.spr_stocks", "eia.refinery_util", "eia.gas_storage", "eia.lng_exports"]
ATTRIBUTION = "Source: U.S. Energy Information Administration"


def _fetch(url: str, **kw):
    """Every request through THIS module's helpers (patchable by the gates)."""
    return qc.fetch(url, get=lambda u, **k: http_get_response(u, **k),
                    get_text=lambda u: http_get_text(u, timeout=30), **kw)


def _robots(url: str) -> str:
    return qc.robots_check(url, get_text=lambda u: http_get_text(u, timeout=30))


def available_at(rule: str, day: str) -> str:
    if rule == "wpsr":
        return eia.available_at(day)
    if rule == "storage":
        return qc.et_instant((dt.date.fromisoformat(day) + dt.timedelta(days=6)).isoformat(),
                             "10:30")
    if rule == "monthly":
        d = dt.date.fromisoformat(day)
        y, m = d.year + (d.month + 1) // 12, (d.month + 1) % 12 + 1
        return qc.et_instant(pub.month_end(y, m), "16:00")
    raise ValueError(f"unknown availability rule {rule!r}")


def series_from_table(table: list[list], scale: float) -> dict[str, float]:
    """{period date: value} from the 'Data 1' sheet's cells, scaled."""
    out: dict[str, float] = {}
    for row in table[3:]:
        day = pub.excel_serial_date(row[0] if row else None)
        v = row[1] if len(row) > 1 else None
        if day and isinstance(v, (int, float)) and not isinstance(v, bool):
            out[day] = float(v) * scale
    if not out:
        raise ValueError("no dated rows in the EIA 'Data 1' sheet")
    return out


def rows_for(key: str, by_day: dict[str, float]) -> list[dict]:
    rule = SERIES[key][3]
    return [{"registry_key": key, "instrument": None, "observed_at": day,
             "available_at": available_at(rule, day), "value": v,
             "availability_kind": "reconstructed"} for day, v in sorted(by_day.items())]


def _produce() -> list[dict]:
    if not config.ENABLED_SOURCES.get("eia"):
        raise RuntimeError("the eia switch in config.ENABLED_SOURCES is off")
    import xlrd  # noqa: PLC0415 -- requirements.txt, as eia.py
    rows: list[dict] = []
    for key, (pattern, sid, scale, _rule) in SERIES.items():
        data, _h = _fetch(pattern.format(sid=sid))
        sheet = xlrd.open_workbook(file_contents=data).sheet_by_name("Data 1")
        rows += rows_for(key, series_from_table(
            [sheet.row_values(r) for r in range(sheet.nrows)], scale))
    return rows


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    raise SystemExit(qc.main(pull))
