"""
S&P Dow Jones Indices' S&P 500 EPS estimates -- the inbox reader. SR-38's forward
series (13 Oct 2026).

    python -m altdata.sources.spdji            # read the inbox, write, summary
    python -m altdata.sources.spdji --check F  # parse one workbook, write nothing

SOURCE. `sp-500-eps-est.xlsx`, S&P DJI's own workbook of S&P 500 earnings and
estimates. Its host answers any non-browser client with a 403, and a writer
never passes for a browser (the AAII ruling, altdata/sources/aaii.py), so this
writer FETCHES NOTHING. It reads the operator's monthly drop:

    Ari downloads the workbook in a browser and drops it into the Drive folder
    chester-vendor-checks/spdji; the box's nightly sweep (scripts/rclone_sync.sh)
    copies that one named file to ~/chester-data/inbox/spdji/sp-500-eps-est.xlsx,
    which this reads ($SPDJI_EPS_FILE overrides the path).

WHAT IT WRITES -- one vintage per drop, every row observed on the workbook's own
"as of" date:

  spdji.op_eps_est_q    the bottom-up operating EPS estimate for one quarter,
                        instrument = the quarter ("2027Q2"), one row a quarter
                        in the estimates block
  spdji.fwd12m_op_eps   the forward twelve months: the sum of the first four
                        estimated quarters ending after the as-of date
  spdji.eps_drop        the drop's record (text): file, sha256, as_of,
                        retrieved_at, the four quarters, the layout version

THE CLOCKS. available_at is the workbook's own "as of" date PLUS ONE BUSINESS
DAY (the next NYSE session), at the end of that day in New York, with
availability_kind `reconstructed` (ruled 13 Oct 2026): S&P DJI posts the
workbook a day or more after its as-of close, so the rule is stated, not read.
retrieved_at -- the drop time -- is the inbox file's modification time, which the
sweep's `rclone copyto` carries over from Drive, i.e. when the file was dropped.
The store has no retrieved_at column, so it is recorded in spdji.eps_drop, whose
own available_at is that drop time (ingest_instant). The store's ingested_at
stays the write instant.

NO HISTORY BEFORE THE FIRST DROP. A drop is one vintage; revisions are read
across stored drops (altdata/return_attribution.py), so the revision line starts
at the second drop and the twelve-month forward split once a drop a year old is
stored. Before the first drop both print "awaiting the first drop".

THE LAYOUT IS DECLARED (config/spdji_eps.yaml), written from the workbook's
documented layout without a file in hand. Every label is required; a missing
label, or a cell that is not what its label says, raises LayoutError naming the
sheet and the cell or range -- the writer goes STALE with that reason. It never
guesses a column. The first real drop is the acceptance.

BEFORE THE FIRST DROP IT IS PENDING (ruled 13 Oct 2026): no file and no drop
stored is a clean, empty run (_publication.PENDING), and the 08:30 heartbeat
lists the three keys under pending, "no file yet". Once a drop is stored, a
missing file is STALE again.

The xlsx is read with the standard library (zipfile and ElementTree): xlrd 2.x
reads only .xls, and a reader this small is not worth a dependency on the box.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import io
import json
import logging
import os
import re
import zipfile
from pathlib import Path
from typing import Any, Optional
from xml.etree import ElementTree as ET
from zoneinfo import ZoneInfo

from . import _publication as pub

log = logging.getLogger(__name__)

SOURCE = "spdji"
QUARTER_KEY = "spdji.op_eps_est_q"
FORWARD_KEY = "spdji.fwd12m_op_eps"
DROP_KEY = "spdji.eps_drop"
KEYS = ["spdji.op_eps_est_q", "spdji.fwd12m_op_eps", "spdji.eps_drop"]
FILE_VAR = "SPDJI_EPS_FILE"
INBOX_DIR = "~/chester-data/inbox/spdji"
DRIVE_FOLDER = "chester-vendor-checks/spdji"
REPO = Path(__file__).resolve().parents[2]
LAYOUT_PATH = REPO / "config" / "spdji_eps.yaml"
NY = ZoneInfo("America/New_York")
AWAITING = ("awaiting the first drop of S&P DJI's EPS workbook "
            "(sp-500-eps-est.xlsx, dropped monthly into "
            f"{DRIVE_FOLDER}; its host refuses non-browser clients)")

_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
       "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
       "rel": "http://schemas.openxmlformats.org/package/2006/relationships"}


class LayoutError(ValueError):
    """The workbook is not laid out as config/spdji_eps.yaml declares. The message
    names the sheet and the cell or range, so the fix is one config edit."""


def layout(path: Optional[Path] = None) -> dict:
    import yaml  # noqa: PLC0415
    return yaml.safe_load((path or LAYOUT_PATH).read_text(encoding="utf-8")) or {}


def inbox_path() -> Path:
    if os.environ.get(FILE_VAR):
        return Path(os.environ[FILE_VAR]).expanduser()
    return Path(INBOX_DIR).expanduser() / layout().get("file_name", "sp-500-eps-est.xlsx")


# ---------------------------------------------------------------------------
# Cells
# ---------------------------------------------------------------------------
def col_index(letters: str) -> int:
    n = 0
    for ch in letters.upper():
        n = n * 26 + (ord(ch) - 64)
    return n


def col_letters(n: int) -> str:
    out = ""
    while n:
        n, r = divmod(n - 1, 26)
        out = chr(65 + r) + out
    return out


def ref(row: int, col: int) -> str:
    return f"{col_letters(col)}{row}"


def parse_range(rng: str) -> tuple[int, int, int, int]:
    """'A1:L20' -> (row0, col0, row1, col1)."""
    m = re.fullmatch(r"([A-Z]+)(\d+):([A-Z]+)(\d+)", rng.strip().upper())
    if not m:
        raise ValueError(f"bad range {rng!r}")
    return (int(m.group(2)), col_index(m.group(1)),
            int(m.group(4)), col_index(m.group(3)))


def norm(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v if v is not None else "")).strip().lower()


def read_workbook(data: bytes) -> dict[str, dict[tuple[int, int], Any]]:
    """{sheet name: {(row, col): value}} -- numbers as float, text as str."""
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise LayoutError(f"not an xlsx workbook (no zip container): {exc}") from None
    names = set(z.namelist())
    shared: list[str] = []
    if "xl/sharedStrings.xml" in names:
        root = ET.fromstring(z.read("xl/sharedStrings.xml"))
        for si in root.findall("m:si", _NS):
            shared.append("".join(t.text or "" for t in si.iter(f"{{{_NS['m']}}}t")))
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    target = {r.get("Id"): r.get("Target") for r in rels.findall("rel:Relationship", _NS)}
    out: dict[str, dict[tuple[int, int], Any]] = {}
    for sh in wb.findall("m:sheets/m:sheet", _NS):
        t = target.get(sh.get(f"{{{_NS['r']}}}id")) or ""
        path = t.lstrip("/") if t.startswith("/") else f"xl/{t}"
        cells: dict[tuple[int, int], Any] = {}
        root = ET.fromstring(z.read(path))
        for c in root.iter(f"{{{_NS['m']}}}c"):
            m = re.fullmatch(r"([A-Z]+)(\d+)", c.get("r") or "")
            if not m:
                continue
            kind = c.get("t")
            v = c.find("m:v", _NS)
            if kind == "inlineStr":
                val: Any = "".join(x.text or "" for x in c.iter(f"{{{_NS['m']}}}t"))
            elif v is None or v.text is None:
                continue
            elif kind == "s":
                val = shared[int(v.text)]
            elif kind in ("str", "e"):
                val = v.text
            elif kind == "b":
                val = v.text == "1"
            else:
                try:
                    val = float(v.text)
                except ValueError:
                    val = v.text
            cells[(int(m.group(2)), col_index(m.group(1)))] = val
        out[sh.get("name")] = cells
    return out


def excel_date(v: Any) -> Optional[dt.date]:
    """A date from an Excel serial (1900 system) or a printed m/d/yyyy, with any
    trailing note ("12/31/2026 (prel.)"). None when it is neither."""
    if isinstance(v, (int, float)) and not isinstance(v, bool) and 20000 < v < 80000:
        return dt.date(1899, 12, 30) + dt.timedelta(days=int(v))
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", str(v or ""))
    if m:
        try:
            return dt.date(int(m.group(3)), int(m.group(1)), int(m.group(2)))
        except ValueError:
            return None
    return None


def quarter_label(d: dt.date) -> str:
    return f"{d.year}Q{(d.month - 1) // 3 + 1}"


# ---------------------------------------------------------------------------
# The parse
# ---------------------------------------------------------------------------
def _find(cells: dict, sheet: str, rng: str, label: str,
          exact: bool = True) -> list[tuple[int, int]]:
    r0, c0, r1, c1 = parse_range(rng)
    want = norm(label)
    return sorted((r, c) for (r, c), v in cells.items()
                  if r0 <= r <= r1 and c0 <= c <= c1 and isinstance(v, str)
                  and (norm(v) == want if exact else want in norm(v)))


def _one(cells: dict, sheet: str, rng: str, label: str, exact: bool = True
         ) -> tuple[int, int]:
    hits = _find(cells, sheet, rng, label, exact)
    if not hits:
        raise LayoutError(f"sheet {sheet!r}, range {rng}: no cell "
                          f"{'reads' if exact else 'contains'} {label!r}")
    if len(hits) > 1:
        raise LayoutError(f"sheet {sheet!r}, range {rng}: {len(hits)} cells "
                          f"{'read' if exact else 'contain'} {label!r} "
                          f"({', '.join(ref(*h) for h in hits[:4])}); the layout "
                          f"expects one")
    return hits[0]


def parse(data: bytes, lay: Optional[dict] = None) -> dict:
    """The drop: {as_of, quarters: [(label, end, eps)], forward: {...}, sheet}.
    Raises LayoutError naming the sheet and the cell it could not read."""
    lay = lay or layout()
    book = read_workbook(data)
    sheet = lay["sheet"]
    if sheet not in book:
        raise LayoutError(f"no sheet {sheet!r} (the workbook has "
                          f"{', '.join(repr(s) for s in book) or 'none'})")
    cells = book[sheet]

    # The as-of date: in the label's own cell, else the first non-empty cell to
    # its right on the same row.
    a = lay["as_of"]
    r, c = _one(cells, sheet, a["search"], a["label"], exact=False)
    as_of = excel_date(cells[(r, c)])
    where = ref(r, c)
    if as_of is None:
        right = sorted(cc for (rr, cc) in cells if rr == r and cc > c)
        if right:
            where = ref(r, right[0])
            as_of = excel_date(cells[(r, right[0])])
    if as_of is None:
        raise LayoutError(f"sheet {sheet!r}, cell {where}: the 'as of' date is not "
                          f"a date ({cells.get((r, c))!r} at {ref(r, c)})")

    t = lay["table"]
    qr, qc = _one(cells, sheet, t["search"], t["quarter_label"])
    er, ec = _one(cells, sheet, t["search"], t["operating_eps_label"])
    if er != qr:
        raise LayoutError(f"sheet {sheet!r}: the header labels sit on different rows "
                          f"({t['quarter_label']!r} at {ref(qr, qc)}, "
                          f"{t['operating_eps_label']!r} at {ref(er, ec)})")
    col_rows = sorted(rr for (rr, cc) in cells if cc == qc and rr > qr)
    start = next((rr for rr in col_rows
                  if norm(cells[(rr, qc)]) == norm(t["estimates_marker"])), None)
    if start is None:
        raise LayoutError(f"sheet {sheet!r}, column {col_letters(qc)} below "
                          f"{ref(qr, qc)}: no {t['estimates_marker']!r} marker")
    end = next((rr for rr in col_rows if rr > start
                and norm(cells[(rr, qc)]) == norm(t["actuals_marker"])), None)
    if end is None:
        raise LayoutError(f"sheet {sheet!r}, column {col_letters(qc)} below "
                          f"{ref(start, qc)}: no {t['actuals_marker']!r} marker "
                          f"closing the estimates block")
    b = lay["basis"]
    if not _find(cells, sheet, f"A1:{col_letters(max(c for _, c in cells))}{start}",
                 b["label"], exact=False):
        raise LayoutError(f"sheet {sheet!r}, range A1:"
                          f"{col_letters(max(c for _, c in cells))}{start}: no cell "
                          f"contains {b['label']!r} above the estimates block, so "
                          f"the basis is not stated; not assumed")

    quarters: list[tuple[str, str, float]] = []
    for rr in range(start + 1, end):
        qv = cells.get((rr, qc))
        if qv is None or norm(qv) == "":
            continue
        d = excel_date(qv)
        if d is None:
            raise LayoutError(f"sheet {sheet!r}, cell {ref(rr, qc)}: expected a "
                              f"quarter-end date under {t['quarter_label']!r}, "
                              f"found {qv!r}")
        ev = cells.get((rr, ec))
        if not isinstance(ev, float):
            raise LayoutError(f"sheet {sheet!r}, cell {ref(rr, ec)}: expected an "
                              f"operating EPS figure under "
                              f"{t['operating_eps_label']!r} for {quarter_label(d)}, "
                              f"found {ev!r}")
        quarters.append((quarter_label(d), d.isoformat(), ev))
    if not quarters:
        raise LayoutError(f"sheet {sheet!r}, rows {start + 1}-{end - 1}: the "
                          f"estimates block holds no quarter")
    n = int(lay.get("forward_quarters") or 4)
    ahead = sorted((q for q in quarters if q[1] > as_of.isoformat()), key=lambda q: q[1])
    if len(ahead) < n:
        raise LayoutError(f"sheet {sheet!r}, rows {start + 1}-{end - 1}: "
                          f"{len(ahead)} estimated quarter(s) end after the as-of "
                          f"date {as_of}; the forward twelve months need {n}")
    four = ahead[:n]
    return {"sheet": sheet, "as_of": as_of.isoformat(), "as_of_cell": where,
            "quarters": quarters,
            "forward": {"eps": sum(q[2] for q in four),
                        "quarters": [q[0] for q in four]},
            "layout_version": lay.get("version")}


def posted_on(as_of: str) -> dt.date:
    """The as-of date plus one business day: the next NYSE session after it."""
    from altdata import session                                # noqa: PLC0415
    d = dt.date.fromisoformat(as_of)
    for _ in range(10):
        d += dt.timedelta(days=1)
        if session.is_trading_session(d):
            return d
    raise RuntimeError(f"no business day in the 10 days after {as_of}")


def available_at(as_of: str) -> str:
    """The end of the as-of date PLUS ONE BUSINESS DAY in New York, as UTC
    (ruled 13 Oct 2026): S&P DJI posts the workbook a day or more after its
    as-of close, so the as-of evening would see a figure not yet public."""
    return (dt.datetime.combine(posted_on(as_of), dt.time(23, 59, 59), NY)
            .astimezone(dt.timezone.utc).isoformat(timespec="microseconds"))


def rows(parsed: dict, retrieved_at: str, file_name: str, sha256: str) -> list[dict]:
    av, day = available_at(parsed["as_of"]), parsed["as_of"]
    out = [{"registry_key": QUARTER_KEY, "instrument": q, "observed_at": day,
            "available_at": av, "value": eps,
            "availability_kind": "reconstructed"}
           for q, _, eps in parsed["quarters"]]
    out.append({"registry_key": FORWARD_KEY, "instrument": None, "observed_at": day,
                "available_at": av, "value": round(parsed["forward"]["eps"], 6),
                "availability_kind": "reconstructed"})
    out.append({"registry_key": DROP_KEY, "instrument": None, "observed_at": day,
                "available_at": retrieved_at, "availability_kind": "ingest_instant",
                "value": json.dumps({"file": file_name, "sha256": sha256,
                                     "as_of": day, "retrieved_at": retrieved_at,
                                     "as_of_cell": parsed["as_of_cell"],
                                     "forward_quarters": parsed["forward"]["quarters"],
                                     "quarters": len(parsed["quarters"]),
                                     "layout_version": parsed["layout_version"]},
                                    sort_keys=True)})
    return out


def read_drop(p: Path) -> list[dict]:
    data = p.read_bytes()
    when = dt.datetime.fromtimestamp(p.stat().st_mtime, dt.timezone.utc)
    try:
        parsed = parse(data)
    except LayoutError as exc:
        raise LayoutError(f"{p.name}: {exc}") from None
    return rows(parsed, when.isoformat(timespec="microseconds"), p.name,
                hashlib.sha256(data).hexdigest())


def _produce() -> list[dict]:
    p = inbox_path()
    if not p.is_file():
        raise FileNotFoundError(f"{AWAITING}; expected at {p} (or ${FILE_VAR})")
    return read_drop(p)


def ever_dropped(db=None) -> bool:
    """Is any drop stored? A store that cannot be read answers True, so the
    writer falls back to STALE rather than hiding a fault as pending."""
    from altdata import observations                           # noqa: PLC0415
    own = db is None
    try:
        store = db or observations.ObservationStore()
        try:
            return pub.newest_observed(store, [DROP_KEY])[DROP_KEY] is not None
        finally:
            if own:
                store.close()
    except Exception as exc:                                  # noqa: BLE001
        log.warning("%s: could not read the store for its drops: %s", SOURCE, exc)
        return True


def pull(run_id: Optional[str] = None, db=None) -> dict:
    """PENDING before the first drop (ruled 13 Oct 2026): no file and nothing
    stored is a clean, empty run, "no file yet". After a drop, a missing file or
    a layout fault is STALE, as before."""
    if not inbox_path().is_file() and not ever_dropped(db):
        return pub.pending(SOURCE, AWAITING, run_id=run_id)
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="S&P DJI EPS estimates (inbox)")
    ap.add_argument("--check", metavar="FILE",
                    help="parse one workbook and print it; write nothing")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    if a.check:
        print(json.dumps(parse(Path(a.check).read_bytes()), indent=2, default=str))
    else:
        print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
