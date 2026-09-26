"""
DKW TIPS-based decomposition -- Federal Reserve Board (D'Amico, Kim and Wei 2018;
updated by Kim, Walsh and Wei 2019).

    python -m altdata.sources.dkw            # one pull, summary to stdout

Signal-triage order ST-1, feed row "DKW TIPS decomposition (dkw.*)"; used by SR-6
and SR-17 (a real-yield-led selloff with breakevens falling) and by §2.1.1 of the
rates driver: it is the one model of the four that separates the REAL term premium
and the TIPS liquidity premium, which is what SR-17's reading turns on.

SOURCE. The FEDS note "Tips from TIPS: Update and Discussions" links
https://www.federalreserve.gov/econres/notes/feds-notes/DKW_updates.csv
-- A CSV, not the Excel file the change order names: the Board publishes the
update as CSV and nothing else. It opens with ~15 quoted preamble lines (source,
notes, the re-estimation date), then a header row beginning "date". Columns are
<component>.<maturity>, maturities 5, 10 and 5-to-10 forward; all in PERCENTAGE
POINTS. Stored: the expected real short rate, the real term premium and the TIPS
liquidity premium at 5 and 10 years.

The file says of itself: "not an official Federal Reserve statistical release ...
subject to delay, revision, or methodological changes without advance notice."
So the model is re-estimated (revision_policy: recomputed) and the preamble's
re-estimation date moves when it is.

AVAILABILITY. Updated monthly and republished in place. The Board sends
Last-Modified, stored as available_at (`observed`); absent, the write instant.
"""

from __future__ import annotations

import csv
import io
import logging
from typing import Optional

from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "frb_dkw"
URL = "https://www.federalreserve.gov/econres/notes/feds-notes/DKW_updates.csv"

# registry key -> CSV column. Percentage points, as published.
COLUMNS: dict[str, str] = {
    "dkw.exp_real_short_rate_5y": "exp.real.short.rate.5",
    "dkw.real_term_premium_5y": "real.term.prem.5",
    "dkw.tips_liquidity_premium_5y": "tips.liq.prem.5",
    "dkw.exp_real_short_rate_10y": "exp.real.short.rate.10",
    "dkw.real_term_premium_10y": "real.term.prem.10",
    "dkw.tips_liquidity_premium_10y": "tips.liq.prem.10",
}
KEYS = list(COLUMNS)


def rows_from_csv(text: str, available_at: str, kind: str) -> list[dict]:
    """Observation rows from the CSV body. Raises on a changed shape."""
    lines = text.lstrip("﻿").splitlines()
    start = next((i for i, ln in enumerate(lines)
                  if ln.strip().strip('"').lower().startswith("date")
                  and "," in ln), None)
    if start is None:
        raise ValueError("no header row beginning 'date' in the DKW file")
    reader = csv.DictReader(io.StringIO("\n".join(lines[start:])))
    fields = [f.strip() for f in (reader.fieldnames or [])]
    missing = [c for c in COLUMNS.values() if c not in fields]
    if missing:
        raise ValueError(f"DKW file lacks columns {missing}")
    out: list[dict] = []
    for rec in reader:
        rec = {(k or "").strip(): v for k, v in rec.items()}
        day = (rec.get(fields[0]) or "").strip()[:10]
        if len(day) != 10 or day[4] != "-":
            continue
        for key, col in COLUMNS.items():
            try:
                v = float(rec.get(col) or "")
            except ValueError:
                continue
            out.append({"registry_key": key, "instrument": None,
                        "observed_at": day, "available_at": available_at,
                        "value": v, "availability_kind": kind})
    return out


def _produce() -> list[dict]:
    data, headers = http_get_response(URL, timeout=60)
    available_at, kind = pub.availability(headers)
    return rows_from_csv(data.decode("utf-8", errors="replace"), available_at,
                         kind)


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
