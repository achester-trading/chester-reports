"""
World Bank Commodity Price Data ("Pink Sheet") -- monthly commodity indices.

    python -m altdata.sources.worldbank      # one pull, summary to stdout

Signal-triage order ST-2 (SR-15 commodity z-score, SR-24 producers vs spot).

SOURCE. https://www.worldbank.org/en/research/commodity-markets links
"CMO-Historical-Data-Monthly.xlsx" under a PER-RELEASE document id, so the link is
found on the page each run. Stdlib .xlsx reader, sheet "Monthly Indices": a
multi-row header (Total Index / Energy / Non-energy / ... / Metals & Minerals /
Precious Metals), then rows "1960M01" onward. NOMINAL US dollars, 2010 = 100.

STORED, observed_at = the month's first day (monthly averages), units idx (2010 = 100):
  worldbank.cmo_total, worldbank.cmo_energy, worldbank.cmo_nonenergy,
  worldbank.cmo_metals (Metals & Minerals), worldbank.cmo_precious (Precious
  Metals)
  reference.file_vintage   instrument "worldbank": the sheet's "Updated on" line

Columns are found by their header label, not their position. Revised month to
month as prices are finalised; available_at is Last-Modified when sent, else the
write instant. revision_policy: revised.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Optional

from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "worldbank_cmo"
PAGE = "https://www.worldbank.org/en/research/commodity-markets"
LINK = r"CMO-Historical-Data-Monthly\.xlsx"
SHEET = "Monthly Indices"
LABELS = {"worldbank.cmo_total": "total index", "worldbank.cmo_energy": "energy",
          "worldbank.cmo_nonenergy": "non-energy",
          "worldbank.cmo_metals": "metals & minerals",
          "worldbank.cmo_precious": "precious metals"}
KEYS = list(LABELS)


def _clean(cell: Any) -> str:
    # "Metals  & Minerals" carries a double space in the September 2026 edition.
    return re.sub(r"\s+", " ", re.sub(r"[*\s]+$", "", str(cell or ""))).strip().lower()


def rows_from_table(table: list[list[Any]], available_at: str,
                    kind: str) -> tuple[list[dict], Optional[str]]:
    first = next((i for i, r in enumerate(table)
                  if r and re.fullmatch(r"\d{4}M\d{2}", str(r[0] or ""))), None)
    if first is None:
        raise ValueError("no YYYYMmm rows in 'Monthly Indices'")
    cols: dict[str, int] = {}
    for r in table[:first]:
        for j, cell in enumerate(r):
            label = _clean(cell)
            for key, want in LABELS.items():
                if label == want and key not in cols:
                    cols[key] = j
    missing = [k for k in LABELS if k not in cols]
    if missing:
        raise ValueError(f"'Monthly Indices' header lacks {missing}")
    updated = next((str(r[0]) for r in table[:first]
                    if r and str(r[0] or "").startswith("Updated on")), None)
    out = []
    for r in table[first:]:
        m = re.fullmatch(r"(\d{4})M(\d{2})", str(r[0] or "")) if r else None
        if not m:
            continue
        day = pub.month_start(int(m.group(1)), int(m.group(2)))
        for key, j in cols.items():
            v = r[j] if j < len(r) else None
            if isinstance(v, float):
                out.append({"registry_key": key, "instrument": None,
                            "observed_at": day, "available_at": available_at,
                            "value": round(v, 6), "availability_kind": kind})
    return out, updated


def _produce() -> list[dict]:
    url = pub.find_link(PAGE, LINK)
    data, headers = http_get_response(url, timeout=120)
    available_at, kind = pub.availability(headers)
    rows, updated = rows_from_table(pub.read_xlsx(data)[SHEET], available_at, kind)
    if updated:
        rows.append(pub.vintage_row("worldbank", updated, available_at, kind))
    return rows


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
