"""
Kenneth French Data Library -- 49 industry portfolios and HML.

    python -m altdata.sources.french         # one pull, summary to stdout

Signal-triage order ST-2 (SR-1 Growth vs Value, SR-13 tech vs defensives): the
long-history reference behind ST-8's calibration and the Base Rates ledgers.
Calibration scripts read these files directly (§1.10); the store keeps them so a
live line can cite a stored, vintaged number.

SOURCE. mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/, zipped CSV, no key:
  F-F_Research_Data_Factors_CSV.zip   monthly factors from 1926-07; HML in PERCENT
  49_Industry_Portfolios_CSV.zip      one file, many sections; two are read:
     "Average Value Weighted Returns -- Monthly"  PERCENT per month
     "Sum of BE / Sum of ME"                     one row per year (the June
                                                 formation's book-to-market)
Missing values are -99.99 or -999 and are skipped.

STORED (instrument = the industry's short name as the file spells it, trimmed):
  french.hml                 monthly HML, percent, observed_at = month-end
  french.ind49_ret_vw        value-weighted monthly return, percent
  french.ind49_beme          annual Sum of BE / Sum of ME, ratio, observed_at =
                             that year's 30 June (the formation date)
  reference.file_vintage     instrument "french": "CRSP YYYYMM" from the file's
                             first line

VINTAGES. Every annual CRSP update restates the whole history. available_at is
the zip's Last-Modified (`observed`); a restated value inside the write window is
a new vintage, and the CRSP month is logged beside it. revision_policy: recomputed.
"""

from __future__ import annotations

import io
import logging
import re
import zipfile
from typing import Optional

from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "ken_french"
BASE = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
FACTORS = BASE + "F-F_Research_Data_Factors_CSV.zip"
INDUSTRIES = BASE + "49_Industry_Portfolios_CSV.zip"
KEYS = ["french.hml", "french.ind49_ret_vw", "french.ind49_beme"]
MISSING = (-99.99, -999.0)


def _unzip(data: bytes) -> str:
    z = zipfile.ZipFile(io.BytesIO(data))
    return z.read(z.namelist()[0]).decode("latin-1")


def _sections(text: str) -> dict[str, list[list[str]]]:
    """{section title: rows}; the untitled first table is keyed ''."""
    out: dict[str, list[list[str]]] = {}
    title = ""
    for ln in text.splitlines():
        cells = [c.strip() for c in ln.split(",")]
        if not ln.strip():
            continue
        # A header row starts with an empty cell (",Mkt-RF,SMB,..."), a data row
        # with a date. Anything else is prose or a section title -- including a
        # preamble line that happens to contain commas.
        if cells[0] and not re.match(r"^\d", cells[0]):
            title = ",".join(cells).strip(",")
            continue
        out.setdefault(title, []).append(cells)
    return out


def crsp_vintage(text: str) -> Optional[str]:
    m = re.search(r"created using the (\d{6}) CRSP", text)
    return f"CRSP {m.group(1)}" if m else None


def _monthly(rows: list[list[str]], key: str, available_at: str, kind: str,
             only: Optional[str] = None) -> list[dict]:
    header = rows[0]
    out = []
    for cells in rows[1:]:
        if not re.fullmatch(r"\d{6}", cells[0]):
            continue
        day = pub.month_end(int(cells[0][:4]), int(cells[0][4:]))
        for j, name in enumerate(header[1:], start=1):
            if only and name != only:
                continue
            try:
                v = float(cells[j])
            except (ValueError, IndexError):
                continue
            if v in MISSING:
                continue
            out.append({"registry_key": key,
                        "instrument": None if only else name, "observed_at": day,
                        "available_at": available_at, "value": v,
                        "availability_kind": kind})
    return out


def rows_from_factors(text: str, available_at: str, kind: str) -> list[dict]:
    # The monthly table is the first section headed with HML whose rows are
    # YYYYMM; the annual table that follows has YYYY rows.
    for rows in _sections(text).values():
        if len(rows) > 1 and "HML" in rows[0] and re.fullmatch(r"\d{6}", rows[1][0]):
            return _monthly(rows, "french.hml", available_at, kind, only="HML")
    raise ValueError("the factors file has no monthly table with an HML column")


def rows_from_industries(text: str, available_at: str, kind: str) -> list[dict]:
    secs = _sections(text)
    ret = next((v for k, v in secs.items()
                if k.startswith("Average Value Weighted Returns -- Monthly")), None)
    beme = next((v for k, v in secs.items() if k.startswith("Sum of BE / Sum of ME")),
                None)
    if not ret or not beme:
        raise ValueError("49-industry file lacks the VW monthly or BE/ME section")
    out = _monthly(ret, "french.ind49_ret_vw", available_at, kind)
    header = beme[0]
    for cells in beme[1:]:
        if not re.fullmatch(r"\d{4}", cells[0]):
            continue
        for j, name in enumerate(header[1:], start=1):
            try:
                v = float(cells[j])
            except (ValueError, IndexError):
                continue
            if v in MISSING:
                continue
            out.append({"registry_key": "french.ind49_beme", "instrument": name,
                        # The portfolios are formed at the end of June (the
                        # file's own statement), so year Y's BE/ME is dated at
                        # Y-06-30 -- never a future 31 December.
                        "observed_at": f"{cells[0]}-06-30",
                        "available_at": available_at, "value": v,
                        "availability_kind": kind})
    return out


def _produce() -> list[dict]:
    rows: list[dict] = []
    vintage = None
    for url, parse in ((FACTORS, rows_from_factors),
                       (INDUSTRIES, rows_from_industries)):
        data, headers = http_get_response(url, timeout=120)
        available_at, kind = pub.availability(headers)
        text = _unzip(data)
        rows.extend(parse(text, available_at, kind))
        vintage = vintage or (crsp_vintage(text), available_at, kind)
    if vintage and vintage[0]:
        rows.append(pub.vintage_row("french", vintage[0], vintage[1], vintage[2]))
    return rows


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
