"""
USD/CNH -- the offshore yuan's daily New York close, from Yahoo's hourly bars.

    python -m altdata.sources.cnh            # one pull, summary to stdout

AQ-3 part 1 (11 Oct 2026; the Quarterly's China and currency chapters, change
order sections 4.4 and 4.5: "CNY/CNH with the fixing gap and the +/-2% band",
"USD/CNY and USD/CNH kept separate"). The offshore leg of calc.cnh_fix_gap_bp
and calc.cnh_cny_bp (altdata/market_features.py), beside the onshore CNY=X close
and the CFETS fix the store already holds.

WHY HOURLY BARS. The price basket carried CNH=X until 5 Oct 2026, when it was
replaced by CNY=X (PB-1): Yahoo serves ONE daily bar for CNH=X whatever the
period asked, and on 5 Oct none at all. Re-measured 11 Oct 2026: still one daily
bar for a month's request -- but the HOURLY bars are served, 1,416 for 60 days
and 17,107 for 730 days (back to 25 Dec 2023). So the daily close is built here
from them, by one rule:

  THE CLOSE of a New York date is the last hourly bar that OPENS before 17:00
  New York on that date -- the FX day's conventional New York cut. A weekend
  date is skipped. A date is written only once its 17:00 has passed, so a
  session in progress is never stored as a close.

No other free daily CNH history was found: FRED carries no CNH series (H.10 quotes
the onshore DEXCHUS only), and the HKMA and TMA publish fixings, not a close.

STORED, observed_at = the New York date:
  cnh.usdcnh   USD/CNH, yuan per dollar, the New York close as above

AVAILABILITY. The close bar's end (its open plus an hour), `reconstructed`: a
bar is final once its hour has passed, so the stamp is when it was knowable.
The first pull reads 730 days of bars; later pulls read the last 60.
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Iterable, Optional
from zoneinfo import ZoneInfo

from .. import observations, session
from . import _publication as pub

log = logging.getLogger(__name__)

SOURCE = "yahoo_cnh"
SYMBOL = "CNH=X"
KEY = "cnh.usdcnh"
KEYS = [KEY]
NEW_YORK = ZoneInfo("America/New_York")
CUT = dt.time(17, 0)
BACKFILL_PERIOD = "730d"
REFRESH_PERIOD = "60d"


def closes_from_bars(bars: Iterable[tuple[dt.datetime, float]],
                     now: dt.datetime) -> list[dict]:
    """(bar open, close) pairs, any timezone -> one row per completed New York
    date: the last bar opening before 17:00 New York on that date."""
    last: dict[dt.date, tuple[dt.datetime, float]] = {}
    for opened, close in bars:
        if close is None or not close == close or close <= 0:   # NaN or nonsense
            continue
        ny = opened.astimezone(NEW_YORK)
        if ny.weekday() >= 5 or ny.time() >= CUT:
            continue
        d = ny.date()
        if d not in last or ny > last[d][0]:
            last[d] = (ny, float(close))
    now_ny = now.astimezone(NEW_YORK)
    out = []
    for d, (opened, close) in sorted(last.items()):
        cut = dt.datetime.combine(d, CUT, tzinfo=NEW_YORK)
        if now_ny < cut:
            continue
        end = (opened + dt.timedelta(hours=1)).astimezone(dt.timezone.utc)
        out.append({"registry_key": KEY, "instrument": None,
                    "observed_at": d.isoformat(),
                    "available_at": observations.canonical_instant(end.isoformat()),
                    "value": round(close, 6),
                    "availability_kind": "reconstructed"})
    return out


def fetch_frames(period: str) -> list[tuple[dt.datetime, float]]:
    from .. import import_yfinance  # noqa: PLC0415 -- never a bare yfinance import
    yf = import_yfinance()
    h = yf.Ticker(SYMBOL).history(period=period, interval="1h", auto_adjust=False)
    return [(ts.to_pydatetime(), float(v)) for ts, v in h["Close"].items()]


def pull(run_id: Optional[str] = None, db=None) -> dict:
    def produce() -> list[dict]:
        own = db is None
        store = db or observations.open_writer(__name__)
        try:
            held = pub.newest_observed(store, KEYS).get(KEY)
        finally:
            if own:
                store.close()
        bars = fetch_frames(REFRESH_PERIOD if held else BACKFILL_PERIOD)
        if not bars:
            raise RuntimeError(f"Yahoo served no hourly bars for {SYMBOL}")
        return closes_from_bars(bars, dt.datetime.fromisoformat(session.utc_iso()))
    return pub.run(SOURCE, KEYS, produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
