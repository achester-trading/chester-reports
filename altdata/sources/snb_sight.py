"""
The Swiss National Bank's sight deposits, weekly, for the Alternative Assets
Quarterly's currencies chapter (the intervention-footprint row: SNB sight deposits
beside MoF's monthly record) (b69-quarterly-readers-1; D34 of 24 Oct 2026; B67
section 11).

    python -m altdata.sources.snb_sight          # one pull, summary to stdout

TERMS (re-read 25 Oct 2026). data.snb.ch's robots.txt is "User-agent: *" with no
disallow. The portal's own terms page (data.snb.ch/en/terms) is a JavaScript shell
whose text no reader can fetch; the SNB's datasets, as Switzerland's open-data
catalogue lists them, read "Open use. Must provide the source. Use for commercial
purposes requires permission of the data owner." THE CONDITION, IN CODE: every row
carries the attribution "Swiss National Bank" in its source field
(`snb:Swiss National Bank`), and the source's registry entry records own,
non-commercial use. The terms text itself is a needs-you for the operator (notes).

SOURCE. https://data.snb.ch/api/cube/snbgwdchfsgw/data/csv/en, keyless: a
semicolon CSV, "CubeId", "PublishingDate", then "Date";"D0";"Value" rows, one per
day and item, values on the week's reporting day only. Probed 25 Oct 2026:
HTTP 200, 415 KB, from 2009-01-09; PublishingDate "2026-10-19 10:00".

  snb.sight_deposits_total      TG, total sight deposits in Swiss francs at the
                                SNB, CHF MILLIONS
  snb.sight_deposits_domestic   GI, sight deposits of domestic banks, CHF MILLIONS

observed_at = the reporting day. available_at = three days after it, 10:00
Zurich (the Monday release the newest PublishingDate shows), reconstructed; the
newest row takes the file's PublishingDate, observed.
"""
from __future__ import annotations

import datetime as dt
import logging
import re
from typing import Optional
from zoneinfo import ZoneInfo

from .. import observations
from . import _publication as pub
from . import _quarterly_common as qc
from ._base import http_get_response, http_get_text

log = logging.getLogger(__name__)

SOURCE = "snb"
ATTRIBUTION = "Swiss National Bank"
ROW_SOURCE = f"{SOURCE}:{ATTRIBUTION}"
URL = "https://data.snb.ch/api/cube/snbgwdchfsgw/data/csv/en"
ITEMS = {"TG": "snb.sight_deposits_total", "GI": "snb.sight_deposits_domestic"}
KEYS = ["snb.sight_deposits_total", "snb.sight_deposits_domestic"]
ZURICH = ZoneInfo("Europe/Zurich")


def _fetch(url: str, **kw):
    """Every request through THIS module's helpers (patchable by the gates)."""
    return qc.fetch(url, get=lambda u, **k: http_get_response(u, **k),
                    get_text=lambda u: http_get_text(u, timeout=30), **kw)


def _robots(url: str) -> str:
    return qc.robots_check(url, get_text=lambda u: http_get_text(u, timeout=30))


def _zurich(day: str, hhmm: str) -> str:
    h, m = (int(x) for x in hhmm.split(":"))
    local = dt.datetime.combine(dt.date.fromisoformat(day), dt.time(h, m), tzinfo=ZURICH)
    return observations.canonical_instant(local.astimezone(dt.timezone.utc).isoformat())


def rows_from_csv(text: str) -> list[dict]:
    text = text.lstrip("﻿")
    pubd = re.search(r'"PublishingDate";"(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2})"', text)
    rows = []
    for m in re.finditer(r'^"(\d{4}-\d{2}-\d{2})";"([A-Z]+)";"([-\d.]+)"\s*$', text, re.M):
        key = ITEMS.get(m.group(2))
        if not key:
            continue
        day = m.group(1)
        rel = (dt.date.fromisoformat(day) + dt.timedelta(days=3)).isoformat()
        rows.append({"registry_key": key, "instrument": None, "observed_at": day,
                     "available_at": _zurich(rel, "10:00"), "value": float(m.group(3)),
                     "availability_kind": "reconstructed", "source": ROW_SOURCE})
    if not rows:
        raise ValueError("no sight-deposit rows in the SNB cube's CSV")
    if pubd:
        newest = max(r["observed_at"] for r in rows)
        stamp = _zurich(pubd.group(1), pubd.group(2))
        for r in rows:
            if r["observed_at"] == newest:
                r["available_at"], r["availability_kind"] = stamp, "observed"
    return rows


def _produce() -> list[dict]:
    data, _h = _fetch(URL)
    return rows_from_csv(data.decode("utf-8", "replace"))


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    raise SystemExit(qc.main(pull))
