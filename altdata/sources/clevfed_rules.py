"""
The Cleveland Fed's simple monetary policy rules: the path of the federal funds
rate the rules prescribe, quarter by quarter, as the median, quartiles and range
across the rules.

    python -m altdata.sources.clevfed_rules    # one pull

6E-RELEASES, RULING (a)5 OF 16 OCT 2026: "a keyless path is built where one reads
within robots (the Cleveland Fed's rate path ...)". The architecture's Session 3b
asks for "the Cleveland Fed expected rate path" and its width (path dispersion).
What the Cleveland Fed publishes keylessly is THIS: the rules' prescribed path,
not a market-implied one. It is stored and printed as the rules' path and never
as market pricing; the market path (the ZQ strip) stays a listed gap.

SOURCE (checked 16 Oct 2026). The indicator page
https://www.clevelandfed.org/indicators-and-data/simple-monetary-policy-rules
draws its chart from
  https://www.clevelandfed.org/-/media/files/webcharts/policyrules/chartdata.csv
with columns Date,Maximum,75th Percentile,Median,25th Percentile,Minimum and one
row a quarter (M/D/YYYY): the first row is the starting quarter, where every
column carries the same rate, then the prescriptions about two and a half years
out. robots.txt disallows /errors/* only; the check runs on every pull, through
aaii.robots_verdict, and a refusal writes nothing. No key.

STORED, one row per publication, observed_at the starting quarter's date and
available_at the file's Last-Modified (observed) or the write instant:
  clevfed.rules_start        the starting rate, percent
  clevfed.rules_median_4q    the rules' median four quarters on, percent
  clevfed.rules_median_8q    eight quarters on
  clevfed.rules_iqr_4q       75th less 25th percentile four quarters on, percent
                             (the path's width: the architecture's dispersion)
Columns are found by name; a file with fewer quarters writes what it has.

A new OFFICIAL writer, not held (the D1c ruling of 16 Oct 2026).
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import logging
from typing import Callable, Optional

from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "clevfed_rules"
AGENT = "chester-reports"
URL = "https://www.clevelandfed.org/-/media/files/webcharts/policyrules/chartdata.csv"
ROBOTS = "https://www.clevelandfed.org/robots.txt"
# A literal list: feeds.static_keys() reads it from source.
KEYS = ["clevfed.rules_start", "clevfed.rules_median_4q", "clevfed.rules_median_8q",
        "clevfed.rules_iqr_4q"]


def rows_from_csv(text: str, available: str, kind: str) -> list[dict]:
    reader = csv.reader(io.StringIO(text.lstrip("﻿")))
    head = [h.strip().lower() for h in next(reader, [])]
    need = ("date", "median", "75th percentile", "25th percentile")
    if any(c not in head for c in need):
        raise ValueError(f"policy rules: expected {need}, got {head}")
    di, mi, hi, li = (head.index(c) for c in need)
    path = []
    for r in reader:
        try:
            day = dt.datetime.strptime(r[di].strip(), "%m/%d/%Y").date().isoformat()
            path.append((day, float(r[mi]), float(r[hi]), float(r[li])))
        except (ValueError, IndexError):
            continue
    if not path:
        raise ValueError("policy rules: no dated row")
    start = path[0][0]

    def row(key: str, value: float) -> dict:
        return {"registry_key": key, "instrument": None, "observed_at": start,
                "available_at": available, "value": round(value, 6),
                "availability_kind": kind}

    out = [row("clevfed.rules_start", path[0][1])]
    if len(path) > 4:
        out.append(row("clevfed.rules_median_4q", path[4][1]))
        out.append(row("clevfed.rules_iqr_4q", path[4][2] - path[4][3]))
    if len(path) > 8:
        out.append(row("clevfed.rules_median_8q", path[8][1]))
    return out


def _robots_text(robots_url: str) -> str:
    import requests                                             # noqa: PLC0415
    r = requests.get(robots_url, timeout=30, headers={"User-Agent": AGENT})
    if 400 <= r.status_code < 500:
        return ""                    # unavailable: no rules (RFC 9309, 2.3.1.3)
    r.raise_for_status()
    return r.text


def robots_ok(get: Optional[Callable[[str], str]] = None) -> tuple[bool, str]:
    from .aaii import robots_verdict                            # noqa: PLC0415
    ok, rule = robots_verdict((get or _robots_text)(ROBOTS), URL, AGENT)
    return (True, "") if ok else (False, f"{ROBOTS} refuses it ({rule})")


def fetch_rows() -> list[dict]:
    ok, why = robots_ok()
    if not ok:
        raise PermissionError(f"robots.txt: {why}")
    data, headers = http_get_response(URL, timeout=60)
    available, kind = pub.availability(headers)
    return rows_from_csv(data.decode("utf-8", errors="replace"), available, kind)


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, fetch_rows, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
