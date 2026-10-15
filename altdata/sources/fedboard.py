"""
Federal Reserve Board -- Index of Common Inflation Expectations (CIE), quarterly.

    python -m altdata.sources.fedboard       # one pull, summary to stdout

Signal-triage order ST-2 (SR-24): the Board's summary of long-run expectations
across surveys and market measures (Ahn and Fulton), the first of the three
DEANCHOR cross-checks beside UMich 5-10y and the NY Fed SCE.

SOURCE. https://www.federalreserve.gov/econres/notes/feds-notes/
FEDS-Note-2873-cie-data.csv -- linked from the "Research Data Series: Index of
Common Inflation Expectations" note (not from the 2020 FEDS note, which carries
no data link). No key. UTF-8 with a BOM; "period,CIE_spf,CIE_mich"; periods are
M/D/YYYY quarter-ends from 1999Q1; PERCENT. Updated at noon ET on the third
Friday of January, April, July and October.

  fedboard.cie   instrument "spf"  -- the index estimated with the SPF's
                                      long-run expectation
                 instrument "mich" -- the variant with Michigan's
                 observed_at = the quarter-end

THE WHOLE HISTORY IS RE-ESTIMATED at every update (it is a common factor over
the full sample), so a changed past quarter is a new vintage, not an error;
revision_policy: recomputed. available_at is the file's Last-Modified (`observed`).
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import logging
from typing import Optional

from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "frb_cie"
URL = ("https://www.federalreserve.gov/econres/notes/feds-notes/"
       "FEDS-Note-2873-cie-data.csv")
KEY = "fedboard.cie"
KEYS = [KEY]
COLUMNS = {"CIE_spf": "spf", "CIE_mich": "mich"}


def rows_from_csv(text: str, available_at: str, kind: str) -> list[dict]:
    reader = csv.DictReader(io.StringIO(text.lstrip("﻿")))
    fields = [f.strip() for f in reader.fieldnames or []]
    if "period" not in fields or not set(COLUMNS) <= set(fields):
        raise ValueError(f"CIE file lacks period/CIE_spf/CIE_mich ({fields})")
    out = []
    for rec in reader:
        rec = {(k or "").strip(): (v or "").strip() for k, v in rec.items()}
        try:
            day = dt.datetime.strptime(rec["period"], "%m/%d/%Y").date().isoformat()
        except (KeyError, ValueError):
            continue
        for col, inst in COLUMNS.items():
            try:
                v = float(rec.get(col, ""))
            except ValueError:
                continue
            out.append({"registry_key": KEY, "instrument": inst,
                        "observed_at": day, "available_at": available_at,
                        "value": v, "availability_kind": kind})
    return out


def _produce() -> list[dict]:
    data, headers = http_get_response(URL, timeout=60)
    return rows_from_csv(data.decode("utf-8", errors="replace"),
                         *pub.availability(headers))


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


# ---------------------------------------------------------------------------
# H.4.1: the FIMA repo line (signal-triage batch 3, ST-B3-05; SR-34)
# ---------------------------------------------------------------------------
# The Board's Data Download Program serves the H.4.1 tables as fixed CSV
# packages; the package below (the factors-supplying and -absorbing reserve
# balances table) carries "Assets: Other: Repurchase agreements - Foreign
# official", the FIMA repo facility's usage. federalreserve.gov answers
# robots.txt with 404 (no rules; checked 13 Oct 2026). No key.
#
# THE PACKAGE: six header rows -- Series Description, Unit, Multiplier,
# Currency, Unique Identifier, Time Period -- then one row per week (the
# Wednesday). A column is found by its UNIQUE IDENTIFIER, never by position:
#   H41/H41/RESPPALGTRF_N.WW       Wednesday level
#   H41/H41/RESPPALGTRF_XAW_N.WW   week average
# MILLIONS of dollars (the Multiplier row says 1000000 and is checked), stored
# in DOLLARS. Published Thursdays at 16:30 ET; available_at is Last-Modified
# where sent, else the write instant.
#
#   tic.fima_repo          Wednesday level     (placed in tic.* by ruling,
#   tic.fima_repo_weekavg  week average         decision 4, 6 Oct 2026)
SOURCE_H41 = "frb_h41"
URL_H41 = ("https://www.federalreserve.gov/datadownload/Output.aspx?rel=H41&"
           "series=f52e72511be65e16f71d4f5858951312&lastobs=&from=&to=&"
           "filetype=csv&label=include&layout=seriescolumn&type=package")
H41_COLUMNS = {"H41/H41/RESPPALGTRF_N.WW": "tic.fima_repo",
               "H41/H41/RESPPALGTRF_XAW_N.WW": "tic.fima_repo_weekavg"}
KEYS_H41 = ["tic.fima_repo", "tic.fima_repo_weekavg"]


def h41_rows_from_csv(text: str, available_at: str, kind: str) -> list[dict]:
    """Rows from the H.4.1 package. Raises when a FIMA column or its
    multiplier is not what this reader expects."""
    rows = list(csv.reader(io.StringIO(text.lstrip("﻿"))))
    meta = {(r[0] or "").strip().rstrip(":"): r for r in rows[:8] if r}
    ids = meta.get("Unique Identifier") or []
    mult = meta.get("Multiplier") or []
    cols = {}
    for i, ident in enumerate(ids):
        key = H41_COLUMNS.get(ident.strip())
        if key:
            if (mult[i] if i < len(mult) else "").strip() != "1000000":
                raise ValueError(f"H.4.1 {ident}: multiplier {mult[i]!r}, expected 1000000")
            cols[key] = i
    if set(cols) != set(KEYS_H41):
        raise ValueError(f"H.4.1 package lacks {sorted(set(KEYS_H41) - set(cols))}")
    out = []
    for r in rows:
        day = (r[0] if r else "").strip()
        if len(day) != 10 or day[4] != "-":
            continue
        for key, i in cols.items():
            try:
                v = float(r[i])
            except (ValueError, IndexError):
                continue                        # "ND": no data that week
            out.append({"registry_key": key, "instrument": None, "observed_at": day,
                        "available_at": available_at, "value": v * 1_000_000.0,
                        "availability_kind": kind})
    if not out:
        raise ValueError("no week parsed from the H.4.1 package")
    return out


def _produce_h41() -> list[dict]:
    data, headers = http_get_response(URL_H41, timeout=90)
    return h41_rows_from_csv(data.decode("utf-8", errors="replace"),
                             *pub.availability(headers))


def pull_h41(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE_H41, KEYS_H41, _produce_h41, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
