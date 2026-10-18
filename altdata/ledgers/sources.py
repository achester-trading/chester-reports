"""
The two providers the ledgers read through (altdata/ledgers/__init__.py).

public  -- full history from the sources, through the writers' own readers where
           one exists, FRED's public graph CSV for FRED series. Network; the
           laptop's first edition and the box's re-run under §1.10 both use it.
store   -- the observation store's newest vintage per period of a mapped key.
           Never used by a gate (the gates hand the studies fixture series).
"""

from __future__ import annotations

import csv
import io
import logging
from typing import Optional

from . import Series

log = logging.getLogger(__name__)

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv"
BIS_CBPOL = "https://stats.bis.org/api/v2/data/dataflow/BIS/WS_CBPOL/1.0"
OECD_CLI = ("https://sdmx.oecd.org/public/rest/data/"
            "OECD.SDD.STES,DSD_STES@DF_CLI,4.1/{area}.M.LI...AA...H")
REDFIN_COUNTRY = ("https://redfin-public-data.s3.us-west-2.amazonaws.com/"
                  "redfin_data_center/housing_market/monthly/country.csv")


def _text(url: str, params: Optional[dict] = None, timeout: int = 120) -> str:
    from ..sources._base import http_get_text                    # noqa: PLC0415
    return http_get_text(url, params=params, timeout=timeout)


def fred(series_id: str) -> Series:
    """FRED's public graph CSV (no key): the whole history, current vintage."""
    rows = csv.reader(io.StringIO(_text(FRED_CSV, {"id": series_id})))
    next(rows, None)
    out = []
    for r in rows:
        if len(r) < 2 or r[1] in ("", "."):
            continue
        try:
            out.append((r[0][:10], float(r[1])))
        except ValueError:
            continue
    if not out:
        raise ValueError(f"FRED {series_id}: no observations")
    return out


def shiller() -> dict[str, Series]:
    """Shiller's monthly S&P data, through the writer's own reader."""
    from ..sources import shiller as sh                         # noqa: PLC0415
    out: dict[str, list] = {}
    for r in sh._produce():                                     # noqa: SLF001
        if r["registry_key"] in sh.KEYS:
            out.setdefault(r["registry_key"], []).append((r["observed_at"][:10],
                                                          float(r["value"])))
    return {k: sorted(v) for k, v in out.items()}


def yahoo(symbol: str) -> Series:
    """Daily closes, the whole history, through the one yfinance import."""
    from .. import import_yfinance                              # noqa: PLC0415
    yf = import_yfinance()
    h = yf.Ticker(symbol).history(period="max", interval="1d", auto_adjust=False)
    return [(i.strftime("%Y-%m-%d"), float(c)) for i, c in zip(h.index, h["Close"])
            if c == c]


def bis_policy_rates() -> dict[str, Series]:
    """Every central bank in the BIS policy-rate table, monthly, end of period."""
    rd = csv.DictReader(io.StringIO(_text(f"{BIS_CBPOL}/M.", {"format": "csv"})))
    out: dict[str, list] = {}
    for r in rd:
        if r.get("FREQ") != "M" or r.get("OBS_VALUE") in ("", "NaN", None):
            continue
        out.setdefault(r["REF_AREA"], []).append((r["TIME_PERIOD"][:7] + "-01",
                                                  float(r["OBS_VALUE"])))
    return {k: sorted(v) for k, v in out.items()}


def oecd_cli(area: str = "G20") -> Series:
    """The OECD composite leading indicator, amplitude adjusted, monthly."""
    rd = csv.DictReader(io.StringIO(_text(OECD_CLI.format(area=area),
                                          {"startPeriod": "1960-01",
                                           "dimensionAtObservation": "AllDimensions",
                                           "format": "csvfile"})))
    out = [(r["TIME_PERIOD"][:7] + "-01", float(r["OBS_VALUE"])) for r in rd
           if r.get("REF_AREA") == area and r.get("OBS_VALUE") not in ("", None)]
    if not out:
        raise ValueError(f"OECD CLI {area}: no observations")
    return sorted(out)


def redfin_country(column: str) -> Series:
    """One column of Redfin's monthly national file (its data center)."""
    rd = csv.DictReader(io.StringIO(_text(REDFIN_COUNTRY)))
    out = []
    for r in rd:
        v = (r.get(column) or "").replace(",", "").strip()
        if not v:
            continue
        try:
            out.append((r["PERIOD BEGIN"][:7] + "-01", float(v)))
        except (ValueError, KeyError):
            continue
    if not out:
        raise ValueError(f"Redfin country.csv: no {column!r}")
    return sorted(set(out))


def store(key: str, instrument: Optional[str] = None, db: Optional[str] = None) -> Series:
    """The store's newest vintage of each period of `key`."""
    from .. import observations                                 # noqa: PLC0415
    st = observations.ObservationStore(db)
    try:
        rows = st.as_of(key, instrument=instrument)
    finally:
        st.close()
    out = sorted((str(r["observed_at"])[:10], float(r["value_num"])) for r in rows
                 if r.get("value_num") is not None)
    if not out:
        raise LookupError(f"the store holds no {key}")
    return out
