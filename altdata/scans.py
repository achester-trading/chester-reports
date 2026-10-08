"""
The scans ingest -- a scan's reference table stored as SOURCED FIGURES.

    python -m altdata.scans ingest            # every docs/scans/*.md, idempotent
    python -m altdata.scans list [--as-of 2026-10-31]

Ruled 3 Oct 2026 with the J.P. Morgan GTM change order ("Also ruled from the
scan": a scans ingest, T3) and narrowed 8 Oct 2026: a sourced figure carries the
URL, THE SCAN'S OWN SECTION REFERENCE and the as-of date; the slide number is
stored when the scan recorded one and omitted otherwise. Without the ingest no
LOG item and no by-hand figure from a scan can reach a report.

-----------------------------------------------------------------------------
NO STORED SOURCE, NOT PRINTED
-----------------------------------------------------------------------------
The rule the voices register holds (altdata/voices.py), applied to figures. A
row without a source URL, a section reference or an as-of date is REFUSED AT
WRITE (`ScanError`), and the schema refuses it again underneath. A report prints
a scan's figure only from this table, never from the scan's Markdown, so a
figure that never reached the store cannot reach a reader.

-----------------------------------------------------------------------------
ONLY THE REFERENCE TABLE, AND NEVER A RECOMMENDATION
-----------------------------------------------------------------------------
A scan carries the publisher's figures and, around them, our read and the
publisher's own advice. Only the section whose heading names the REFERENCE
TABLE is ingested: the read, the borrow list and the voices entry are ours and
stay in the scan. The Guide's recommendations never print (change order,
Precedence row), so a reference-table row whose text reads as advice --
overweight, underweight, buy, sell, recommend, favor, prefer -- is refused and
named in the ingest's summary rather than stored.

-----------------------------------------------------------------------------
WHEN A FIGURE IS KNOWABLE
-----------------------------------------------------------------------------
Two dates, and they are different clocks. `as_of` is the publisher's data date
(30 September for the 4Q Guide) and is what a reader is told. `read_on` is the
day the scan was produced -- when WE could first have known the figure -- and is
what a report's cutoff filters on, so an edition rebuilt for a cutoff before the
read does not print a figure it could not have had. A report prints the newest
edition of each scan family (`jpm-gtm` for jpm-gtm-2026q4) readable at its
cutoff.

A stored figure is the record: rows are never edited or deleted. A corrected
scan re-ingested writes new rows for the rows that changed, and the reader takes
the newest ingest of each metric.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sqlite3
import sys
from pathlib import Path
from typing import Iterable, Optional

from . import observations, session

REPO = Path(__file__).resolve().parent.parent
SCANS_DIR = REPO / "docs" / "scans"

SCHEMA = """
CREATE TABLE IF NOT EXISTS scan_figures (
    id            INTEGER PRIMARY KEY,
    scan_id       TEXT NOT NULL,
    family        TEXT NOT NULL,
    title         TEXT NOT NULL,
    edition       TEXT,
    metric        TEXT NOT NULL CHECK (length(metric) > 0),
    value         TEXT NOT NULL CHECK (length(value) > 0),
    comparison    TEXT,
    source_url    TEXT NOT NULL CHECK (length(source_url) > 10
                                      AND source_url LIKE 'http%'),
    section_ref   TEXT NOT NULL CHECK (length(section_ref) > 0),
    slide         INTEGER CHECK (slide IS NULL OR slide > 0),
    as_of         TEXT NOT NULL CHECK (length(as_of) = 10),
    read_on       TEXT NOT NULL CHECK (length(read_on) = 10),
    scan_path     TEXT NOT NULL,
    ingested_at   TEXT NOT NULL
);
-- An EXPRESSION index, as observations.obs_vintage: SQLite treats NULLs as
-- distinct in a UNIQUE, and comparison and slide are often NULL, so a plain
-- UNIQUE would let every re-ingest double the table.
CREATE UNIQUE INDEX IF NOT EXISTS scan_figures_once
    ON scan_figures (scan_id, metric, value, COALESCE(comparison, ''),
                     COALESCE(slide, 0), source_url, as_of);
CREATE INDEX IF NOT EXISTS scan_figures_family ON scan_figures (family, read_on);
CREATE TRIGGER IF NOT EXISTS scan_figures_immutable
BEFORE UPDATE ON scan_figures
BEGIN SELECT RAISE(ABORT, 'a stored figure is the record; it is never edited'); END;
CREATE TRIGGER IF NOT EXISTS scan_figures_no_delete
BEFORE DELETE ON scan_figures
BEGIN SELECT RAISE(ABORT, 'a stored figure is the record; it is never deleted'); END;
"""

# Advice, not a figure. Whole words, case-insensitive.
ADVICE = re.compile(r"\b(overweight|underweight|buy|sell|recommend\w*|favou?r\w*|"
                    r"prefer\w*|we like|add exposure|reduce exposure)\b", re.I)
REFERENCE_HEADING = re.compile(r"^##\s+(\d+)\.\s+Reference table\b(.*)$", re.I)
SLIDE = re.compile(r"\bslides?\s+(\d{1,3})\b", re.I)
FAMILY_SUFFIX = re.compile(r"-\d{4}q[1-4]$", re.I)
MONTHS = {m: i for i, m in enumerate(
    ("january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"), 1)}


class ScanError(ValueError):
    """A figure the ingest refuses to store, with its reason."""


def _date(text: str) -> Optional[str]:
    """'30 September 2026' / '30 Sep 2026' / '2026-09-30' -> '2026-09-30'."""
    m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", text)
    if m:
        return m.group(0)
    m = re.search(r"\b(\d{1,2})\s+([A-Za-z]{3,9})\.?\s+(\d{4})\b", text)
    if not m:
        return None
    name = m.group(2).lower()
    mon = next((n for k, n in MONTHS.items() if k.startswith(name[:3])), None)
    if not mon:
        return None
    try:
        return dt.date(int(m.group(3)), mon, int(m.group(1))).isoformat()
    except ValueError:
        return None


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse(path: Path) -> dict:
    """The scan's header and its reference table, with a refusal list. Reads the
    Markdown only; writes nothing."""
    text = Path(path).read_text(encoding="utf-8")
    lines = text.splitlines()
    head = {"scan_id": Path(path).stem, "scan_path": Path(path).as_posix(),
            "title": None, "edition": None, "source_url": None, "as_of": None,
            "read_on": None}
    head["family"] = FAMILY_SUFFIX.sub("", head["scan_id"])
    for ln in lines[:20]:
        if ln.startswith("# ") and not head["title"]:
            head["title"] = ln[2:].strip()
        if ln.startswith("**Edition:**"):
            body = ln.split("**Edition:**", 1)[1].strip()
            head["edition"] = re.split(r"\s+[—-]+\s+data as of", body)[0].strip()
            m = re.search(r"data as of\s+([^(.;]+)", body, re.I)
            head["as_of"] = _date(m.group(1)) if m else None
        if "**Read on:**" in ln:
            head["read_on"] = _date(ln.split("**Read on:**", 1)[1])
        if "**Source:**" in ln:
            m = re.search(r"https?://\S+", ln.split("**Source:**", 1)[1])
            head["source_url"] = m.group(0).rstrip(").,") if m else None
    figures, refused = [], []
    section = None
    columns: list[str] = []
    for ln in lines:
        m = REFERENCE_HEADING.match(ln)
        if m:
            section = f"§{m.group(1)}"
            # "Reference table -- 4Q 2026 (as of 30 Sep 2026)": the table's own
            # as-of wins over the header's when it names one.
            own = _date(m.group(2))
            if own:
                head["as_of"] = own
            columns = []
            continue
        if section and ln.startswith("## "):
            break
        if not section or not ln.lstrip().startswith("|"):
            continue
        cells = _cells(ln)
        if not columns:
            columns = [c.lower() for c in cells]
            continue
        if all(set(c) <= set("-: ") for c in cells):
            continue
        row = dict(zip(columns, cells))
        metric = row.get("metric") or cells[0]
        value = row.get("value") or (cells[1] if len(cells) > 1 else "")
        comparison = next((v for k, v in row.items()
                           if k.startswith("long-run") or k == "comparison"), None)
        if comparison in ("—", "-", ""):
            comparison = None
        slide = row.get("slide")
        if not slide:
            sm = SLIDE.search(" ".join(cells))
            slide = sm.group(1) if sm else None
        fig = {**head, "metric": metric, "value": value, "comparison": comparison,
               "section_ref": section,
               "slide": int(slide) if slide and str(slide).isdigit() else None}
        why = refusal(fig)
        if why:
            refused.append({"metric": metric, "reason": why})
        else:
            figures.append(fig)
    if not section:
        refused.append({"metric": None, "reason": "no reference-table section"})
    return {**head, "figures": figures, "refused": refused}


def refusal(fig: dict) -> Optional[str]:
    """Why a figure cannot be stored, or None."""
    url = str(fig.get("source_url") or "")
    if not url.startswith("http") or len(url) <= 10:
        return "no source URL"
    if not fig.get("section_ref"):
        return "no section reference"
    if not fig.get("as_of"):
        return "no as-of date"
    if not fig.get("read_on"):
        return "no read-on date"
    if not str(fig.get("metric") or "").strip() or not str(fig.get("value") or "").strip():
        return "no metric or no value"
    hit = ADVICE.search(" ".join(str(fig.get(k) or "") for k in
                                 ("metric", "value", "comparison")))
    if hit:
        return f"reads as a recommendation ('{hit.group(0)}'); never stored"
    return None


def _connect(db_path: Optional[str], readonly: bool) -> sqlite3.Connection:
    path = Path(db_path or observations.DEFAULT_DB)
    if readonly:
        if not path.exists():
            conn = sqlite3.connect(":memory:")
        else:
            conn = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        have = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'")}
        if "scan_figures" not in have:
            # Before the first ingest every read is empty, never a fault, and a
            # report writes nothing.
            conn.close()
            conn = sqlite3.connect(":memory:")
            conn.row_factory = sqlite3.Row
            conn.executescript(SCHEMA)
        return conn
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def write(conn: sqlite3.Connection, fig: dict) -> bool:
    """One figure. Raises ScanError on a refusal; True when a row was added."""
    why = refusal(fig)
    if why:
        raise ScanError(f"{fig.get('metric')}: {why}")
    cur = conn.execute(
        "INSERT OR IGNORE INTO scan_figures (scan_id, family, title, edition, "
        " metric, value, comparison, source_url, section_ref, slide, as_of, "
        " read_on, scan_path, ingested_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (fig["scan_id"], fig["family"], fig.get("title") or fig["scan_id"],
         fig.get("edition"), fig["metric"].strip(), fig["value"].strip(),
         fig.get("comparison"), fig["source_url"], fig["section_ref"],
         fig.get("slide"), fig["as_of"], fig["read_on"], fig["scan_path"],
         session.utc_iso()))
    return bool(cur.rowcount)


def ingest(paths: Optional[Iterable[Path]] = None,
           db_path: Optional[str] = None) -> dict:
    """Every scan's reference table into the store. Idempotent: a re-ingest of an
    unchanged scan adds nothing."""
    paths = sorted(paths if paths is not None else SCANS_DIR.glob("*.md"))
    out = {"scans": [], "added": 0, "refused": []}
    conn = _connect(db_path, readonly=False)
    try:
        for p in paths:
            parsed = parse(Path(p))
            added = sum(write(conn, f) for f in parsed["figures"])
            conn.commit()
            out["scans"].append({"scan_id": parsed["scan_id"],
                                 "figures": len(parsed["figures"]), "added": added})
            out["added"] += added
            out["refused"] += [{"scan_id": parsed["scan_id"], **r}
                               for r in parsed["refused"]]
    finally:
        conn.close()
    return out


def latest(as_of: Optional[str] = None, db_path: Optional[str] = None) -> list[dict]:
    """The newest edition of each scan family readable at `as_of` (a date or an
    instant; read_on <= its date), one row per metric, in table order. Reads only."""
    cut = str(as_of or session.utc_iso())[:10]
    conn = _connect(db_path, readonly=True)
    try:
        rows = [dict(r) for r in conn.execute(
            "SELECT * FROM scan_figures WHERE read_on <= ? ORDER BY id", (cut,))]
    finally:
        conn.close()
    newest: dict[str, tuple] = {}
    for r in rows:
        k = (r["as_of"], r["read_on"])
        if r["family"] not in newest or k > newest[r["family"]]:
            newest[r["family"]] = k
    keep: dict[tuple, dict] = {}
    for r in rows:                       # ordered by id: the newest ingest wins
        if (r["as_of"], r["read_on"]) == newest[r["family"]]:
            keep[(r["family"], r["metric"])] = r
    out = sorted(keep.values(), key=lambda r: (r["family"], r["id"]))
    for r in out:
        r["source_ref"] = source_ref(r)
    return out


def source_ref(r: dict) -> str:
    """'§6' or '§6, slide 12' -- the scan's own reference, the slide when stored."""
    return r["section_ref"] + (f", slide {r['slide']}" if r.get("slide") else "")


def _main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m altdata.scans")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ingest")
    ls = sub.add_parser("list")
    ls.add_argument("--as-of")
    args = ap.parse_args(argv)
    if args.cmd == "ingest":
        out = ingest()
        for s in out["scans"]:
            print(f"{s['scan_id']}: {s['figures']} figures, {s['added']} added")
        for r in out["refused"]:
            print(f"  refused {r['scan_id']} {r['metric']}: {r['reason']}")
        return 0
    for r in latest(args.as_of):
        print(f"{r['family']:<10} {r['metric'][:40]:<40} {r['value'][:50]:<50} "
              f"{r['source_ref']} as of {r['as_of']}")
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
