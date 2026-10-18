"""
The listings logger (AUD-3b item 5): Nasdaq Trader's two symbol directories,
one reference snapshot a day, and the day's changes. The work is
altdata/listings.py; this is its place in the 06:45 loggers step
(`feeds pull --only loggers`, scripts/fetch_overnight.sh).

It writes NO registry key and no observation -- listings are reference data
under data/reference/listings/ -- so its keys are empty and the freshness
roster, which watches registry keys, does not watch it (in_freshness False).
A failed day is the summary's `error`, logged by the step like any logger's.
"""

from __future__ import annotations

from typing import Optional

from . import LoggerSpec, register


def run(run_id: Optional[str] = None) -> dict:
    from altdata import listings                                # noqa: PLC0415
    r = listings.pull()
    return {**r, "written": 0, "listings": r.get("written", 0)}


SPEC = register(LoggerSpec(
    name="listings",
    description="Every US listing's symbol, name, exchange and ETF flag, from "
                "Nasdaq Trader's nasdaqlisted.txt and otherlisted.txt, as a daily "
                "reference snapshot with its change file (added, removed, renamed).",
    keys=lambda: [],
    run=run,
    requires_key=None,
    min_history=0,
    in_freshness=False,
    notes="AUD-3b. Reference data for the Security Master and chester-meme's scan; "
          "no registry key by ruling.",
))
