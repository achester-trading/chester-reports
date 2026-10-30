"""
Federal Reserve Board -- Index of Common Inflation Expectations (CIE), quarterly.

    python -m altdata.sources.fedboard       # one pull, summary to stdout

Signal-triage order ST-2 (SR-24): the Board's summary of long-run expectations
across surveys and market measures (Ahn and Fulton), the first of the three
DEANCHOR cross-checks beside UMich 5-10y and the NY Fed SCE.

SOURCE. https://www.federalreserve.gov/econres/notes/feds-notes/
FEDS-Note-2873-cie-data.csv -- linked from the "Research Data Series: Index of
Common Inflation Expectations" note (not from the 2020 FEDS note, which carries
no data link). No key. "period,CIE_spf,CIE_mich"; periods are quarter-ends from
1999Q1; PERCENT. Updated at noon ET on the third Friday of January, April, July
and October.

THE PERIOD'S FORMAT CHANGED (writer-fixes-1, 17 Oct 2026). Until the October 2026
update the file was UTF-8 with a BOM and dated M/D/YYYY ("6/30/2026"); the update
of 16 Oct 2026 (Last-Modified 16:00 GMT) dropped the BOM and dates YYYY-M-D
("2026-9-30"). Every row failed the old parse, so the first full pull on the box
read "the source parsed to zero rows". Both forms are read; a file with rows
but no readable period raises, naming the first period it could not read. The
series continues -- the Board has not withdrawn it.

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

from .. import observations
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
    out, bad = [], []
    for rec in reader:
        rec = {(k or "").strip(): (v or "").strip() for k, v in rec.items()}
        day = _cie_period(rec.get("period", ""))
        if day is None:
            bad.append(rec.get("period", ""))
            continue
        for col, inst in COLUMNS.items():
            try:
                v = float(rec.get(col, ""))
            except ValueError:
                continue
            out.append({"registry_key": KEY, "instrument": inst,
                        "observed_at": day, "available_at": available_at,
                        "value": v, "availability_kind": kind})
    if not out and bad:
        raise ValueError(f"CIE file: no period read; the first was {bad[0]!r} "
                         f"(expected M/D/YYYY or YYYY-M-D)")
    return out


def _cie_period(s: str) -> Optional[str]:
    """A CIE period as an ISO date: "6/30/2026" (to Sep 2026) or "2026-9-30"
    (from the 16 Oct 2026 update)."""
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(str(s).strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return None


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
# THE QUERY (writer-fixes-1, 17 Oct 2026). The first full pull on the box failed
# "H.4.1 package lacks ['tic.fima_repo', 'tic.fima_repo_weekavg']". The package
# still carries both columns under the same identifiers (read 17 Oct 2026); the
# fault was the URL's empty `lastobs=`, which the Data Download Program now
# answers with an EMPTY body (HTTP 200, text/html), so no identifier row was
# there to find. `lastobs=520` (SESSION-SET: ten years of Wednesdays, which
# covers the FIMA facility from its 2020 start; the program serves 1,000 and
# refuses 1,200) returns the package; a date range (`from`/`to`) returns nothing.
#
# ONE MISSING KEY NEVER FAILS THE PACKAGE: what parsed is written, each missing
# key is logged with its reason and returned in the summary's `absent`, and the
# roster shows it absent (write_rows' keys_without_rows). Only a body with no
# identifier row, or no FIMA column at all, fails the run.
#
#   tic.fima_repo          Wednesday level     (placed in tic.* by ruling,
#   tic.fima_repo_weekavg  week average         decision 4, 6 Oct 2026)
SOURCE_H41 = "frb_h41"
H41_LASTOBS = 520
# INCREMENTAL ONCE HELD (A71, the audit's leftovers; audit-leftovers-1's one-line
# follow-up): with the FIMA keys already stored, the package is asked for its
# last H41_HELD_LASTOBS Wednesdays -- the newest week and seven before it, the
# stated overlap, which covers the releases' own restatements of recent weeks.
# The full ten years only when nothing is held. SESSION-SET.
H41_HELD_LASTOBS = 8
URL_H41_FMT = ("https://www.federalreserve.gov/datadownload/Output.aspx?rel=H41&"
               "series=f52e72511be65e16f71d4f5858951312&lastobs={lastobs}&from=&to=&"
               "filetype=csv&label=include&layout=seriescolumn&type=package")
URL_H41 = URL_H41_FMT.format(lastobs=H41_LASTOBS)


def h41_url(held: bool) -> str:
    """The package's URL: the stated overlap once the keys are held, else the full
    window."""
    return URL_H41_FMT.format(lastobs=H41_HELD_LASTOBS if held else H41_LASTOBS)
H41_COLUMNS = {"H41/H41/RESPPALGTRF_N.WW": "tic.fima_repo",
               "H41/H41/RESPPALGTRF_XAW_N.WW": "tic.fima_repo_weekavg"}
KEYS_H41 = ["tic.fima_repo", "tic.fima_repo_weekavg"]


def h41_rows_from_csv(text: str, available_at: str, kind: str,
                      absent: Optional[dict] = None) -> list[dict]:
    """Rows from the H.4.1 package. A FIMA column the package does not carry is
    recorded in `absent` (key -> reason) and logged, and the rest is written;
    raises only when the body carries no identifier row, no FIMA column at all,
    or a multiplier this reader does not expect."""
    rows = list(csv.reader(io.StringIO(text.lstrip("﻿"))))
    meta = {(r[0] or "").strip().rstrip(":"): r for r in rows[:8] if r}
    ids = meta.get("Unique Identifier") or []
    if not ids:
        raise ValueError(f"H.4.1: the response carries no Unique Identifier row "
                         f"({len(text)} bytes) -- an empty or non-CSV body, so the "
                         f"query is wrong, not the package")
    mult = meta.get("Multiplier") or []
    cols = {}
    for i, ident in enumerate(ids):
        key = H41_COLUMNS.get(ident.strip())
        if key:
            if (mult[i] if i < len(mult) else "").strip() != "1000000":
                raise ValueError(f"H.4.1 {ident}: multiplier {mult[i]!r}, expected 1000000")
            cols[key] = i
    if not cols:
        raise ValueError(f"H.4.1 package carries none of {sorted(H41_COLUMNS)}")
    for ident, key in H41_COLUMNS.items():
        if key not in cols:
            why = f"the H.4.1 package carries no column {ident}"
            log.warning("%s: %s; %s marked absent, the rest written",
                        SOURCE_H41, why, key)
            if absent is not None:
                absent[key] = why
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


def _h41_held(db=None) -> bool:
    """Whether every FIMA key already has a stored row."""
    own = db is None
    try:
        store = db or observations.open_writer(__name__)
    except Exception:                                           # noqa: BLE001
        return False
    try:
        newest = pub.newest_observed(store, KEYS_H41)
        return all(newest.get(k) for k in KEYS_H41)
    finally:
        if own:
            store.close()


def _produce_h41(absent: Optional[dict] = None, db=None) -> list[dict]:
    data, headers = http_get_response(h41_url(_h41_held(db)), timeout=90)
    return h41_rows_from_csv(data.decode("utf-8", errors="replace"),
                             *pub.availability(headers), absent=absent)


def pull_h41(run_id: Optional[str] = None, db=None) -> dict:
    absent: dict = {}
    out = pub.run(SOURCE_H41, KEYS_H41, lambda: _produce_h41(absent, db),
                  run_id=run_id, db=db)
    if absent:
        out["absent"] = absent
    return out


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
