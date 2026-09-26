"""
What every published-file writer shares: the write rule, the STALE rule, the
publication instant, and an .xlsx reader that needs nothing outside the stdlib.

Signal-triage order, ST-1 (§1.10 repository bindings, 30.2(a), 30.4). The writers
that use this -- acm, sffed, dkw, treasury_auctions, fiscaldata -- are timer-driven:
they run inside `python -m altdata.feeds pull` (chester-eod 16:10 ET and the 06:45
overnight pass) and no report ever calls them.

-----------------------------------------------------------------------------
STALE, NOT EMPTY
-----------------------------------------------------------------------------

A fetch or parse failure WRITES NOTHING. The store keeps the last good vintage of
every key, the summary says STALE with the reason and the newest observed date per
key, and the freshness roster turns the age into an alarm once it passes the
series' own allowance. What a failure must never do is write an empty, null or
zero row -- that would be a reading, and the renderer would print it. The same
holds for a parse that "succeeds" with no rows or without its expected columns:
a file that changed shape is a failure, not a quiet day.

-----------------------------------------------------------------------------
THE WRITE WINDOW
-----------------------------------------------------------------------------

These files re-serve their whole history on every download, and three of them
are model outputs that RE-ESTIMATE history (ACM, SF Fed, DKW). drop_unchanged()
already refuses a vintage for an unchanged value; a re-estimated one is a real
revision and is kept. But a model that nudges 16,000 daily rows each night would
add 16,000 vintages a night. So a key's FIRST write takes the whole history (the
backfill) and every later write takes the last WRITE_WINDOW_DAYS only. Older
periods keep the vintage they were first stored with, and the calibration
scripts read full history from the source directly (§1.10), not from the store.

-----------------------------------------------------------------------------
IDENTITY AND TIME (30.2(a))
-----------------------------------------------------------------------------

Every row carries the run's run_id (session.new_run_id), available_at is
canonicalised by the store to microsecond UTC, and the run is filed under
session.session_date(). An observation dated after that session is refused: no
publication describes a day that has not happened, so one that appears to is a
parse error and is reported as such rather than stored.
"""

from __future__ import annotations

import datetime as dt
import email.utils
import io
import logging
import re
import zipfile
import xml.etree.ElementTree as ET
from typing import Any, Callable, Iterable, Optional

from .. import observations, session

log = logging.getLogger(__name__)

WRITE_WINDOW_DAYS = 400

STALE = "STALE"
OK = "OK"


# ---------------------------------------------------------------------------
# Publication instant
# ---------------------------------------------------------------------------
def last_modified(headers: Optional[dict]) -> Optional[str]:
    """The Last-Modified header as canonical UTC, or None when absent/unparseable."""
    raw = (headers or {}).get("last-modified")
    if not raw:
        return None
    try:
        parsed = email.utils.parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return observations.canonical_instant(parsed.isoformat())


def availability(headers: Optional[dict]) -> tuple[str, str]:
    """(available_at, availability_kind) for a republished file.

    Last-Modified, where the publisher sends one, is the instant THIS VINTAGE of
    the file appeared -- `observed`. Where it does not, the write instant stands
    in -- `ingest_instant`, an upper bound, which is safe for an as-of join and
    later than the truth.
    """
    lm = last_modified(headers)
    if lm:
        return lm, "observed"
    return session.utc_iso(timespec="microseconds"), "ingest_instant"


# ---------------------------------------------------------------------------
# Write, and the STALE summary
# ---------------------------------------------------------------------------
def newest_observed(db: observations.ObservationStore,
                    keys: Iterable[str]) -> dict[str, Optional[str]]:
    """The newest stored observed_at per key, across instruments."""
    out: dict[str, Optional[str]] = {}
    for k in keys:
        row = db.conn.execute(
            "SELECT MAX(observed_at) FROM observations WHERE registry_key = ?",
            (k,)).fetchone()
        out[k] = row[0] if row and row[0] else None
    return out


def stale(source: str, keys: Iterable[str], reason: str,
          db: Optional[observations.ObservationStore] = None,
          run_id: Optional[str] = None) -> dict:
    """The summary a failed run returns. Writes nothing; says what is kept."""
    keys = list(keys)
    log.warning("%s: STALE -- %s (nothing written; last stored vintage kept)",
                source, reason)
    held: dict[str, Optional[str]] = {}
    own = db is None
    try:
        store = db or observations.ObservationStore()
        try:
            held = newest_observed(store, keys)
        finally:
            if own:
                store.close()
    except Exception as exc:                                  # noqa: BLE001
        log.warning("%s: could not read the store for the STALE summary: %s",
                    source, exc)
    return {"source": source, "status": STALE, "reason": reason,
            "written": 0, "run_id": run_id, "session": session.session_date(),
            "last_observed": held}


def write_rows(source: str, rows: list[dict], keys: Iterable[str],
               run_id: str,
               db: Optional[observations.ObservationStore] = None,
               window_days: int = WRITE_WINDOW_DAYS) -> dict:
    """Stamp, window, de-duplicate and write. Returns the OK summary.

    `rows` carry registry_key, instrument, observed_at, available_at, value,
    availability_kind. `keys` is every key this writer owns, so a parse that
    produced nothing for one of them is visible in the summary.
    """
    keys = list(keys)
    today = session.session_date()
    future = [r for r in rows if str(r["observed_at"])[:10] > today]
    if future:
        return stale(source, keys,
                     f"{len(future)} row(s) dated after session {today} "
                     f"(first {future[0]['registry_key']} "
                     f"{future[0]['observed_at']}) -- a parse error, not data",
                     db=db, run_id=run_id)
    own = db is None
    store = db or observations.ObservationStore()
    try:
        held = newest_observed(store, keys)
        cutoff = (session.session_date_obj()
                  - dt.timedelta(days=window_days)).isoformat()
        kept = []
        for r in rows:
            if held.get(r["registry_key"]) and str(r["observed_at"])[:10] < cutoff:
                continue          # backfilled already; outside the write window
            kept.append(dict(r, source=r.get("source") or source, run_id=run_id))
        fresh = observations.drop_unchanged(store, kept)
        n = store.write_many(fresh)
        newest = newest_observed(store, keys)
    finally:
        if own:
            store.close()
    empty = sorted(k for k in keys if not newest.get(k))
    log.info("%s: %d row(s) parsed, %d written (run %s)", source, len(rows), n,
             run_id)
    return {"source": source, "status": OK, "written": n, "parsed": len(rows),
            "run_id": run_id, "session": today, "last_observed": newest,
            "keys_without_rows": empty}


def run(source: str, keys: list[str], produce: Callable[[], list[dict]],
        run_id: Optional[str] = None,
        db: Optional[observations.ObservationStore] = None) -> dict:
    """The whole writer step: produce rows, or return STALE. Never raises."""
    run_id = run_id or session.new_run_id(source)
    try:
        rows = produce()
    except Exception as exc:                                  # noqa: BLE001
        return stale(source, keys, f"{type(exc).__name__}: {exc}", db=db,
                     run_id=run_id)
    if not rows:
        return stale(source, keys, "the source parsed to zero rows", db=db,
                     run_id=run_id)
    try:
        return write_rows(source, rows, keys, run_id, db=db)
    except Exception as exc:                                  # noqa: BLE001
        log.exception("%s: write failed", source)
        return stale(source, keys, f"write failed: {type(exc).__name__}: {exc}",
                     db=db, run_id=run_id)


# ---------------------------------------------------------------------------
# A minimal .xlsx reader
# ---------------------------------------------------------------------------
# WHY NOT openpyxl. `make deploy` does not pip install, so a new dependency does
# not reach the box until somebody installs it by hand -- and a writer that
# cannot import is a writer that goes STALE on its first night. An .xlsx is a zip
# of XML; reading values out of it takes forty lines and the standard library.
# Values only: no styles, formulas are read as their cached results.
_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
       "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"


def _col_index(ref: str) -> int:
    letters = re.match(r"[A-Z]+", ref).group(0)
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def read_xlsx(data: bytes) -> dict[str, list[list[Any]]]:
    """{sheet name: rows}, each row a list of cell values (str, float or None)."""
    z = zipfile.ZipFile(io.BytesIO(data))
    shared: list[str] = []
    if "xl/sharedStrings.xml" in z.namelist():
        root = ET.fromstring(z.read("xl/sharedStrings.xml"))
        for si in root.findall("m:si", _NS):
            shared.append("".join(t.text or ""
                                  for t in si.iter(f"{{{_NS['m']}}}t")))
    rels = {}
    rels_root = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    for rel in rels_root:
        rels[rel.get("Id")] = rel.get("Target")
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    out: dict[str, list[list[Any]]] = {}
    for sheet in wb.find("m:sheets", _NS):
        target = rels.get(sheet.get(_REL), "")
        path = target.lstrip("/") if target.startswith("/") else f"xl/{target}"
        root = ET.fromstring(z.read(path))
        rows: list[list[Any]] = []
        for r in root.find("m:sheetData", _NS):
            vals: list[Any] = []
            for c in r:
                idx = _col_index(c.get("r")) if c.get("r") else len(vals)
                while len(vals) < idx:
                    vals.append(None)
                t = c.get("t")
                v = c.find("m:v", _NS)
                x: Any = None if v is None else v.text
                if t == "s" and x is not None:
                    x = shared[int(x)]
                elif t == "inlineStr":
                    x = "".join(tt.text or "" for tt in c.iter(f"{{{_NS['m']}}}t"))
                elif t in (None, "n") and x is not None:
                    try:
                        x = float(x)
                    except ValueError:
                        pass
                vals.append(x)
            rows.append(vals)
        out[sheet.get("name")] = rows
    return out


def excel_serial_date(value: Any) -> Optional[str]:
    """An Excel 1900-system serial day as YYYY-MM-DD, or None."""
    try:
        n = float(value)
    except (TypeError, ValueError):
        return None
    if n < 1:
        return None
    return (dt.date(1899, 12, 30) + dt.timedelta(days=int(n))).isoformat()
