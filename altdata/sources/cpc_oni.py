"""
NOAA CPC's Oceanic Nino Index, the ENSO state, for the Alternative Assets
Quarterly's agriculture section beside the degree-day lines
(b69-quarterly-readers-1; D34 of 24 Oct 2026; B67 section 27). Context only,
never extrapolated to a price.

    python -m altdata.sources.cpc_oni            # one pull, summary to stdout

TERMS (re-read 25 Oct 2026, https://www.weather.gov/disclaimer): NWS material is
"not subject to copyright protection", and "Permission is not required to display
unaltered NWS products". robots.txt (www.cpc.ncep.noaa.gov) answers 404: no rules.
The same source as altdata/sources/cpc_degree_days.py (B59's NOAA reader).

SOURCE. https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt, keyless: rows
"SEAS YR TOTAL ANOM", one per overlapping three-month season from DJF 1950.

  noaa.oni   the season's anomaly (degrees C against the centred 30-year base);
             +0.5 or above is El Nino conditions, -0.5 or below La Nina, CPC's
             own thresholds, printed as CPC states them

observed_at = the first day of the season's CENTRE month (DJF -> January of YR;
NDJ -> December of YR). available_at = the 15th of the month after the season's
last month, 12:00 ET, reconstructed: CPC issues its ENSO diagnostic discussion on
the second Thursday of each month, and the 15th bounds it (session-set, its bound
in config/publication_lags.yaml). CPC recomputes recent seasons as the sea-
surface record updates, so a changed value is a revision, kept as a vintage.
"""
from __future__ import annotations

import logging
import re
from typing import Optional

from . import _publication as pub
from . import _quarterly_common as qc
from ._base import http_get_response, http_get_text

log = logging.getLogger(__name__)

SOURCE = "noaa_cpc"
URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
KEYS = ["noaa.oni"]
SEASONS = ("DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ", "JJA", "JAS", "ASO", "SON",
           "OND", "NDJ")


def _fetch(url: str, **kw):
    """Every request through THIS module's helpers (patchable by the gates)."""
    return qc.fetch(url, get=lambda u, **k: http_get_response(u, **k),
                    get_text=lambda u: http_get_text(u, timeout=30), **kw)


def _robots(url: str) -> str:
    return qc.robots_check(url, get_text=lambda u: http_get_text(u, timeout=30))


def season_dates(season: str, year: int) -> tuple[str, str]:
    """(observed_at, available_at) for a season and its YR column."""
    i = SEASONS.index(season)          # 0 = DJF, centred on January
    centre = i + 1                     # 1..12, the centre month of YR
    last_y, last_m = (year + (1 if centre == 12 else 0), (centre % 12) + 1)
    rel_y, rel_m = (last_y + (1 if last_m == 12 else 0), (last_m % 12) + 1)
    return (f"{year}-{centre:02d}-01",
            qc.et_instant(f"{rel_y}-{rel_m:02d}-15", "12:00"))


def rows_from_text(text: str) -> list[dict]:
    rows = []
    for m in re.finditer(r"^\s*([A-Z]{3})\s+(\d{4})\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s*$",
                         text, re.M):
        if m.group(1) not in SEASONS:
            continue
        obs, avail = season_dates(m.group(1), int(m.group(2)))
        rows.append({"registry_key": "noaa.oni", "instrument": None,
                     "observed_at": obs, "available_at": avail,
                     "value": float(m.group(4)),
                     "availability_kind": "reconstructed"})
    if not rows:
        raise ValueError("no SEAS YR TOTAL ANOM rows in the ONI file")
    return rows


def _produce() -> list[dict]:
    data, _h = _fetch(URL)
    return rows_from_text(data.decode("utf-8", "replace"))


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db,
                   window_days=36500)


if __name__ == "__main__":
    raise SystemExit(qc.main(pull))
