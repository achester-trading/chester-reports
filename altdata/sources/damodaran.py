"""
Damodaran industry multiples (NYU Stern) -- US industries, annual.

    python -m altdata.sources.damodaran      # one pull, summary to stdout

Signal-triage order ST-2 (SR-13, tech vs defensives relative valuation): the
cross-sectional multiple beside Ken French's BE/ME.

SOURCE. pages.stern.nyu.edu/~adamodar/pc/datasets/, legacy .xls (xlrd), no key:
  pedata.xls    sheet "Industry Averages": Current / Trailing / Forward PE
  vebitda.xls   sheet "Industry Averages": EV/EBITDA, two blocks -- "Only positive
                EBITDA firms" and "All firms"; the ALL-FIRMS block is stored
Each carries "Date updated:" (an Excel serial) at the top; that date is the
edition, and it is observed_at.

STORED (instrument = the industry name as the table spells it, including the
"Total Market" rows):
  damodaran.pe_trailing, damodaran.pe_forward, damodaran.ev_ebitda   ratio
  reference.file_vintage   instrument "damodaran": "updated YYYY-MM-DD"

FORWARD-ONLY. Only the current edition is read: Damodaran's archive holds prior
years under different file names and layouts, and ST-8's calibration reads those
directly (§1.10). The table is replaced each January; available_at is the file's
Last-Modified (`observed`). revision_policy: recomputed.
"""

from __future__ import annotations

import logging
from typing import Optional

from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "damodaran"
BASE = "https://pages.stern.nyu.edu/~adamodar/pc/datasets/"
# file -> {registry key: (header text, which occurrence -- 0 first, -1 last)}
FILES = {
    "pedata.xls": {"damodaran.pe_trailing": ("Trailing PE", 0),
                   "damodaran.pe_forward": ("Forward PE", 0)},
    "vebitda.xls": {"damodaran.ev_ebitda": ("EV/EBITDA", -1)},
}
KEYS = [k for spec in FILES.values() for k in spec]
SHEET = "Industry Averages"


def rows_from_table(table: list[list], spec: dict, available_at: str,
                    kind: str) -> tuple[list[dict], str]:
    """(rows, edition date) from one 'Industry Averages' sheet."""
    edition = None
    hdr_i = None
    for i, row in enumerate(table[:20]):
        if row and str(row[0]).strip().lower().startswith("date updated"):
            edition = pub.excel_serial_date(row[1] if len(row) > 1 else None)
        if row and str(row[0]).strip() == "Industry Name":
            hdr_i = i
            break
    if hdr_i is None or not edition:
        raise ValueError("no 'Industry Name' header or 'Date updated' in the sheet")
    header = [str(h).strip() for h in table[hdr_i]]
    cols = {}
    for key, (label, which) in spec.items():
        hits = [j for j, h in enumerate(header) if h == label]
        if not hits:
            raise ValueError(f"column {label!r} not found ({header})")
        cols[key] = hits[which]
    out = []
    for row in table[hdr_i + 1:]:
        name = str(row[0]).strip() if row else ""
        if not name:
            continue
        for key, j in cols.items():
            v = row[j] if j < len(row) else None
            if isinstance(v, float):
                out.append({"registry_key": key, "instrument": name,
                            "observed_at": edition, "available_at": available_at,
                            "value": round(v, 6), "availability_kind": kind})
    return out, edition


def _produce() -> list[dict]:
    import xlrd  # noqa: PLC0415 -- requirements.txt
    rows: list[dict] = []
    edition = avail = None
    for fname, spec in FILES.items():
        data, headers = http_get_response(BASE + fname, timeout=90)
        available_at, kind = pub.availability(headers)
        sheet = xlrd.open_workbook(file_contents=data).sheet_by_name(SHEET)
        got, edition = rows_from_table(
            [sheet.row_values(r) for r in range(sheet.nrows)], spec,
            available_at, kind)
        rows.extend(got)
        avail = (available_at, kind)
    if edition and avail:
        rows.append(pub.vintage_row("damodaran", f"updated {edition}", *avail,
                                    observed_at=edition))
    return rows


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
