"""
The SET index (Stock Exchange of Thailand), daily close -- FORWARD-ONLY.

    python -m altdata.sources.thai_set       # one pull, summary to stdout

AQ-3 part 2 (11 Oct 2026; the Quarterly's Thailand chapter: "SET index
(yfinance ^SET.BK)", the operator's named source). ISOLATED: namespace
thailand, never trigger_eligible.

WHAT YAHOO SERVES. Measured 11 Oct 2026: ^SET.BK answers ONE bar whatever the
period asked -- "max", a start date, a month -- the latest session's (9 Oct,
1,577.65); ^SET50.BK and ^SET100.BK the same. So there is no history to read,
and this writer stores the one bar each run: the series grows forward from
the first pull, a close a session. No free alternative was found: set.or.th's
data endpoints answer a JavaScript challenge, and stooq's robots.txt is
Disallow: / (see the notes, "No free source", for SET history).

ROBOTS. Yahoo's query hosts, which yfinance reads, carry robots.txt
"User-agent: * / Disallow: /" (query1 and query2, checked 11 Oct 2026). That
is true of every yfinance pull this repo makes, the price basket included; it
is named in the notes for the operator's ruling rather than decided here.

  thai.set_index   the SET index close, points; observed_at = the session date

AVAILABILITY. The SET closes at 16:30 Bangkok; a bar is stamped 17:00 Bangkok on
its date, `reconstructed`, never after the write instant. A bar dated today is
stored only once that hour has passed.
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Iterable, Optional
from zoneinfo import ZoneInfo

from .. import observations, session
from . import _publication as pub

log = logging.getLogger(__name__)

SOURCE = "yahoo_set"
SYMBOL = "^SET.BK"
KEY = "thai.set_index"
KEYS = [KEY]
BANGKOK = ZoneInfo("Asia/Bangkok")
FINAL = dt.time(17, 0)


def rows_from_bars(bars: Iterable[tuple[dt.date, float]], now: dt.datetime) -> list[dict]:
    out = []
    for day, close in bars:
        if close is None or not close == close or close <= 0:
            continue
        t = dt.datetime.combine(day, FINAL, tzinfo=BANGKOK).astimezone(dt.timezone.utc)
        if t > now:
            continue                                   # the session is not final
        out.append({"registry_key": KEY, "instrument": None,
                    "observed_at": day.isoformat(),
                    "available_at": observations.canonical_instant(t.isoformat()),
                    "value": round(float(close), 4),
                    "availability_kind": "reconstructed"})
    return out


def fetch_frames(period: str = "5d") -> list[tuple[dt.date, float]]:
    from .. import import_yfinance  # noqa: PLC0415 -- never a bare yfinance import
    yf = import_yfinance()
    h = yf.Ticker(SYMBOL).history(period=period, interval="1d", auto_adjust=False)
    return [(ts.to_pydatetime().astimezone(BANGKOK).date(), float(v))
            for ts, v in h["Close"].items()]


def pull(run_id: Optional[str] = None, db=None) -> dict:
    def produce() -> list[dict]:
        rows = rows_from_bars(fetch_frames(),
                              dt.datetime.fromisoformat(session.utc_iso()))
        if not rows:
            raise RuntimeError(f"Yahoo served no final bar for {SYMBOL}")
        return rows
    return pub.run(SOURCE, KEYS, produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
