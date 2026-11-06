"""
Statistics Canada -- the CPI, change on a year earlier, headline and core, from
the agency's keyless Web Data Service.

    python -m altdata.sources.statcan_cpi    # one pull

The by-hand audit (st-r5-audit, 16 Oct 2026; Batch 6 item 39's gap): FRED's
OECD CPI for Canada stopped at March 2025, so the real-yield panel's Canada row
was a gap. Read by altdata/st_r5_t1_rest.py's real_yields() through
config/st_r5_t1_rest.yaml.

  ca.cpi_yoy        All-items (table 18-10-0004-01, vector v41690973), % on a
                    year earlier
  ca.cpi_core_yoy   All-items excluding food and energy (vector v41691233), the
                    aggregate closest to the US core

SOURCE (checked 16 Oct 2026). https://www150.statcan.gc.ca/t1/wds/rest/
getDataFromVectorByReferencePeriodRange, one GET for both vectors, JSON; no key.
The robots.txt of www150.statcan.gc.ca has no rule over /t1/wds/; it is read
each run and the fetch stops on a disallow.

READ BY CONTENT. Each vector's block must say SUCCESS and carry its own
vectorId; a block for another vector, or a vector with no point, is refused.
Each point carries refPer (the month), value (the index, 2002=100) and
releaseTime (local Ottawa time).

THE CHANGE ON THE YEAR is computed from the published index (the month and the
same month a year earlier), to one decimal, as the agency rounds its own.

A BODY THAT IS NOT JSON (the feed repair of 24 Oct 2026, a61b). The box logged
"statcan_cpi: STALE -- JSONDecodeError: Expecting value: line 1 column 1" on
every run in the extract, while the laptop's one probe of the same URL that day
(robots.txt allowing /t1/wds/) answered 200 application/json with both vectors.
The cause on the box is not reproducible from the laptop, so the writer now
refuses such a body by name -- its Content-Type and its first 120 characters --
and the next run's STALE reason says what the box was sent.

AVAILABILITY. Each point's releaseTime is the instant that month was first
released (or, for history loaded before 2007, the database's load day, later
than the truth and safe), `observed`. A year-on-year row is available at the
later of its two months' releases. observed_at is the month's first day.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
from typing import Optional
from zoneinfo import ZoneInfo

from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "statcan_cpi"
SITE = "https://www150.statcan.gc.ca"
VECTORS = {41690973: "ca.cpi_yoy", 41691233: "ca.cpi_core_yoy"}
KEYS = list(VECTORS.values())
START = "1990-01-01"
OTTAWA = ZoneInfo("America/Toronto")


def url_of(end: str) -> str:
    ids = ",".join(f"%22{v}%22" for v in VECTORS)
    return (f"{SITE}/t1/wds/rest/getDataFromVectorByReferencePeriodRange?"
            f"vectorIds={ids}&startRefPeriod={START}&endReferencePeriod={end}")


def _instant(local: str) -> str:
    t = dt.datetime.fromisoformat(local).replace(tzinfo=OTTAWA)
    return t.astimezone(dt.timezone.utc).isoformat(timespec="microseconds")


class NotJSON(ValueError):
    """The service answered with a body that is not JSON."""


def load(data: bytes, content_type: Optional[str] = None) -> list:
    """The response's JSON, or NotJSON naming the Content-Type and the body's
    first 120 characters (whitespace folded)."""
    try:
        return json.loads(data)
    except ValueError:
        head = " ".join(data[:120].decode("utf-8", "replace").split())
        raise NotJSON(f"body not JSON (Content-Type {content_type or 'not stated'}): "
                      f"{head!r}") from None


def parse(data: bytes, content_type: Optional[str] = None
          ) -> dict[int, dict[str, tuple[float, str]]]:
    """{vector id: {YYYY-MM: (index, release instant UTC)}}. Refuses a response
    that is not JSON, missing a vector, carrying a failed block, or with no point."""
    out: dict[int, dict[str, tuple[float, str]]] = {}
    for block in load(data, content_type):
        obj = block.get("object") or {}
        vid = obj.get("vectorId")
        if block.get("status") != "SUCCESS" or vid not in VECTORS:
            raise ValueError(f"Statistics Canada answered {block.get('status')!r} "
                             f"for vector {vid!r}")
        pts = {}
        for p in obj.get("vectorDataPoint") or []:
            if p.get("value") is None or not p.get("releaseTime"):
                continue
            pts[str(p["refPer"])[:7]] = (float(p["value"]), _instant(p["releaseTime"]))
        if not pts:
            raise ValueError(f"Statistics Canada vector {vid} carries no point")
        out[vid] = pts
    missing = set(VECTORS) - set(out)
    if missing:
        raise ValueError(f"Statistics Canada's response lacks vector(s) {sorted(missing)}")
    return out


def rows_from(data: bytes, content_type: Optional[str] = None) -> list[dict]:
    rows = []
    for vid, pts in parse(data, content_type).items():
        for m, (v, released) in sorted(pts.items()):
            prior = pts.get(f"{int(m[:4]) - 1}{m[4:]}")
            if not prior or not prior[0]:
                continue
            rows.append({"registry_key": VECTORS[vid], "instrument": None,
                         "observed_at": f"{m}-01",
                         "available_at": max(released, prior[1]),
                         "value": round((v / prior[0] - 1) * 100, 1),
                         "availability_kind": "observed"})
    return rows


def fetch_rows() -> list[dict]:
    end = dt.date.today().replace(day=1).isoformat()
    url = url_of(end)
    allowed, rule = pub.robots_allows(SITE, url)
    if not allowed:
        raise PermissionError(f"www150.statcan.gc.ca robots.txt disallows {url} ({rule})")
    body, headers = http_get_response(url, timeout=60,
                                      headers={"Accept": "application/json"})
    return rows_from(body, headers.get("content-type"))


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, fetch_rows, run_id=run_id, db=db)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
