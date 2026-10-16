"""
World Gold Council -- the above-ground stock of gold, in tonnes, as the WGC
publishes it on its "how much gold" page.

    python -m altdata.sources.wgc_stock          # one pull (HELD: writes nothing)

ST-R5.38a (16 Oct 2026; Batch 6 item 38): the numerator of the gold/equity
market-cap ratio, under Factor V. Read by altdata/st_r5_t1_rest.py's
gold_equity().

  wgc.above_ground_t   tonnes, observed_at = the quarter-end the page names
                       ("Total above-ground stock (end-Q2 2026): 222,600 tonnes")

HELD FOR D1c. A NEW store writer, and the 25 Sep order's Track D precondition is
"D1c before any new writer": the repo-wide write lock has not landed (TODO.md,
D1c). So the module is built and gated on fixtures, `HELD_FOR_D1C` is True, pull()
fetches nothing, writes nothing and says why, and the module is on no feeds
roster. Lifting the hold is the operator's ruling plus two edits: HELD_FOR_D1C =
False here, and the module name in altdata/feeds.py EXTERNAL_WRITERS
(docs/briefs/st-r5-t1-rest-notes.md).

SOURCE (checked 16 Oct 2026). https://www.gold.org/goldhub/data/how-much-gold;
www.gold.org's robots.txt (read each run, wildcard-aware) allows it. The figure
sits in one sentence of the page body, read by phrase, never by position: a
page whose sentence changed is refused, not half-read. The WGC revises the
stock when it re-estimates mine supply, so a restated figure for the same
quarter is a new vintage row. The page's Last-Modified is the serving instant
(16 Oct: the fetch time), so the write instant stands in (`ingest_instant`).
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from .. import session
from . import _publication as pub
from ._base import http_get_response, http_get_text
from .aaii import robots_verdict

log = logging.getLogger(__name__)

SOURCE = "wgc_stock"
URL = "https://www.gold.org/goldhub/data/how-much-gold"
ROBOTS_URL = "https://www.gold.org/robots.txt"
KEY = "wgc.above_ground_t"
KEYS = [KEY]

HELD_FOR_D1C = True
HOLD_REASON = ("held for D1c: a new store writer waits for the repo-wide write "
               "lock (Track D precondition; TODO.md D1c)")

_STOCK = re.compile(r"Total above-ground stock\s*\(end-Q([1-4])\s+(\d{4})\)\s*:?\s*"
                    r"(?:<[^>]+>\s*)*([\d,]+)\s*tonnes", re.I)
_QUARTER_END = {"1": "03-31", "2": "06-30", "3": "09-30", "4": "12-31"}


def parse(html: str) -> tuple[str, float]:
    """(quarter-end day, tonnes). Raises on a page without the sentence."""
    m = _STOCK.search(html)
    if not m:
        raise ValueError("the WGC page carries no 'Total above-ground stock (end-Qn "
                         "YYYY): N tonnes' sentence")
    q, year, t = m.groups()
    return f"{year}-{_QUARTER_END[q]}", float(t.replace(",", ""))


def fetch_rows() -> list[dict]:
    allowed, rule = robots_verdict(http_get_text(ROBOTS_URL, timeout=30), URL)
    if not allowed:
        raise PermissionError(f"www.gold.org robots.txt disallows the page ({rule})")
    body, _h = http_get_response(URL, timeout=60)
    day, tonnes = parse(body.decode("utf-8", errors="replace"))
    return [{"registry_key": KEY, "instrument": None, "observed_at": day,
             "available_at": session.utc_iso(timespec="microseconds"),
             "value": tonnes, "availability_kind": "ingest_instant"}]


def pull(run_id: Optional[str] = None, db=None) -> dict:
    if HELD_FOR_D1C:
        return {"source": SOURCE, "status": "HELD", "written": 0,
                "reason": HOLD_REASON, "keys": KEYS}
    return pub.run(SOURCE, KEYS, fetch_rows, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
