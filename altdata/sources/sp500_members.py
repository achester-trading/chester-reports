"""
S&P 500 constituents -- membership and weights from SPY's daily holdings file,
and each member's daily close from Yahoo.

    python -m altdata.sources.sp500_members          # one pull

ST-R5.44a and ST-R5.31a (16 Oct 2026; Batch 6 items 44 and 31, filing note 4:
"the box stores no constituent prices"). Read by altdata/st_r5_t1_rest.py's
breadth() (the drawdown histogram and the average-member gap) and
concentration() (the top-10 share). Session B's dispersion panel (Batch 5 item
18) reads the same closes for its fallback, which is why they are one key with
the ticker as instrument:

  sp500.member_weight   % of SPY's net assets, per member (instrument = ticker),
                        observed_at = the file's "As of" day
  sp500.member_close    the member's daily close, USD, split-adjusted and
                        dividend-UNADJUSTED -- the same close yfinance_source
                        stores, for the same reasons (instrument = ticker in
                        Yahoo's form: BRK-B, BF-B)

LIFTED 16 Oct 2026. The ruling: WAL and the busy timeout (f98fec4) satisfy D1c
for an append-only writer in the scheduled pulls; the repo-wide write-lock helper
is a separate item, later. HELD_FOR_D1C is False and the module is on
altdata/feeds.py EXTERNAL_WRITERS, so the external pull runs it
(docs/briefs/st-r5-fixes-notes.md). The flag stays, so the hold can be put back
by one edit.

SOURCES (checked 16 Oct 2026).
  * Membership: https://www.ssga.com/us/en/intermediary/library-content/products/
    fund-data/etfs/us/holdings-daily-us-en-spy.xlsx (it redirects to
    /library-content/...), the same host and path family as the GLD reader's
    navhist workbook. www.ssga.com's robots.txt is read each run with the
    wildcard-aware reader and the fetch stops on a disallow; on 16 Oct its `*`
    group disallows /library-content/assets/pdf/documents and nothing on this
    path. One sheet, "holdings": three header lines (fund, ticker, "As of
    15-Oct-2026"), then Name, Ticker, Identifier, SEDOL, Weight, Sector, Shares
    Held, Local Currency -- read by column NAME. 505 lines on 15 Oct; the cash
    line ("-") and a non-equity line (a CVR's numeric ticker) are skipped.
  * Closes: Yahoo through yfinance, under the operator-sanctioned yfinance
    exception, imported through altdata.import_yfinance() as every yfinance
    reader is (Gate L). It never passes for a browser. The first pull reads two
    years for any member whose closes are not yet stored (so each holds a 52-week
    high, a member added to the index included); later pulls read ten days.

AVAILABILITY. The holdings rows carry the file's Last-Modified where SSGA sends
one (`observed`), else the write instant. Closes carry the write instant
(`ingest_instant`), as yfinance_source's live pull does: an upper bound on when
the close was known, safe for an as-of join.
"""

from __future__ import annotations

import datetime as dt
import logging
import re
from typing import Callable, Optional

from .. import session
from . import _publication as pub
from ._base import http_get_response, http_get_text
from .aaii import robots_verdict

log = logging.getLogger(__name__)

SOURCE = "sp500_members"
HOLDINGS_URL = ("https://www.ssga.com/us/en/intermediary/library-content/products/"
                "fund-data/etfs/us/holdings-daily-us-en-spy.xlsx")
ROBOTS_URL = "https://www.ssga.com/robots.txt"
WEIGHT_KEY = "sp500.member_weight"
CLOSE_KEY = "sp500.member_close"
KEYS = [WEIGHT_KEY, CLOSE_KEY]

HELD_FOR_D1C = False
HOLD_REASON = ("held for D1c: a new store writer waits for the repo-wide write "
               "lock (Track D precondition; TODO.md D1c)")

REQUIRED = ("Name", "Ticker", "Weight")
FIRST_PERIOD, LATER_PERIOD = "2y", "10d"
_TICKER = re.compile(r"^[A-Z]{1,5}(\.[A-Z])?$")


def yahoo_symbol(ticker: str) -> str:
    """SSGA's class-share dot to Yahoo's hyphen: BRK.B -> BRK-B."""
    return ticker.replace(".", "-")


def _as_of(cell) -> Optional[str]:
    m = re.search(r"(\d{1,2})-([A-Za-z]{3})-(\d{4})", str(cell or ""))
    if not m:
        return None
    return dt.datetime.strptime("-".join(m.groups()), "%d-%b-%Y").date().isoformat()


def parse_holdings(data: bytes) -> tuple[str, list[tuple[str, float]]]:
    """(as-of day, [(yahoo ticker, weight %)]) from the workbook. Refuses a file
    without its columns or its date rather than half-reading it."""
    tables = pub.read_xlsx(data)
    if not tables:
        raise ValueError("the SPY holdings workbook has no sheet")
    rows = next(iter(tables.values()))
    day = next((_as_of(r[1]) for r in rows[:6]
                if r and str(r[0] or "").startswith("Holdings")), None)
    if not day:
        raise ValueError("the SPY holdings workbook carries no 'As of' date")
    hdr = next((i for i, r in enumerate(rows[:12])
                if r and all(c in [str(x or "").strip() for x in r] for c in REQUIRED)),
               None)
    if hdr is None:
        raise ValueError(f"the SPY holdings workbook has no {list(REQUIRED)} header")
    cols = {str(x or "").strip(): j for j, x in enumerate(rows[hdr])}
    out = []
    for r in rows[hdr + 1:]:
        if not r or len(r) <= max(cols.values()):
            continue
        tk, w = str(r[cols["Ticker"]] or "").strip(), r[cols["Weight"]]
        if not _TICKER.match(tk) or not isinstance(w, (int, float)):
            continue
        out.append((yahoo_symbol(tk), float(w)))
    if len(out) < 400:
        raise ValueError(f"the SPY holdings workbook parsed to {len(out)} members")
    return day, out


def holdings_rows(data: bytes, available: str, kind: str) -> list[dict]:
    day, members = parse_holdings(data)
    return [{"registry_key": WEIGHT_KEY, "instrument": tk, "observed_at": day,
             "available_at": available, "value": w, "availability_kind": kind}
            for tk, w in members]


def fetch_holdings() -> tuple[bytes, dict]:
    allowed, rule = robots_verdict(http_get_text(ROBOTS_URL, timeout=30), HOLDINGS_URL)
    if not allowed:
        raise PermissionError(f"www.ssga.com robots.txt disallows the SPY holdings "
                              f"file ({rule}); not fetched")
    return http_get_response(HOLDINGS_URL, timeout=60)


def yahoo_closes(tickers: list[str], period: str) -> dict[str, list[tuple[str, float]]]:
    """{ticker: [(day, close)]} from Yahoo, split-adjusted, dividend-unadjusted."""
    from .. import import_yfinance                              # noqa: PLC0415
    yf = import_yfinance()
    df = yf.download(tickers, period=period, interval="1d", auto_adjust=False,
                     group_by="ticker", progress=False, threads=True)
    out: dict[str, list[tuple[str, float]]] = {}
    for tk in tickers:
        try:
            s = df[tk]["Close"].dropna()
        except (KeyError, TypeError):
            continue
        out[tk] = [(i.date().isoformat(), float(v)) for i, v in s.items()]
    return out


def close_rows(closes: dict[str, list[tuple[str, float]]], now: str) -> list[dict]:
    from .yfinance_source import drop_incomplete_bars, drop_non_session_bars  # noqa: PLC0415
    rows = []
    for tk, pts in closes.items():
        pts, _ = drop_non_session_bars(tk, pts)
        pts, _ = drop_incomplete_bars(tk, pts)
        rows += [{"registry_key": CLOSE_KEY, "instrument": tk, "observed_at": d,
                  "available_at": now, "value": v, "availability_kind": "ingest_instant"}
                 for d, v in pts if v > 0]
    return rows


def held_members(db=None) -> set[str]:
    """The members whose closes are already stored. The feeds pull passes no
    store, so the default one is opened to ask."""
    from .. import observations                                 # noqa: PLC0415
    st = db or observations.ObservationStore()
    try:
        return set(st.instruments(CLOSE_KEY))
    finally:
        if db is None:
            st.close()


def produce(db=None, closes_fn: Optional[Callable] = None) -> list[dict]:
    """The holdings, then closes: two years for a member not yet held (the first
    pull, and every member added to the index since), ten days for the rest."""
    closes_fn = closes_fn or yahoo_closes
    data, headers = fetch_holdings()
    available, kind = pub.availability(headers)
    rows = holdings_rows(data, available, kind)
    tickers = sorted({r["instrument"] for r in rows})
    have = held_members(db)
    new = [t for t in tickers if t not in have]
    old = [t for t in tickers if t in have]
    closes: dict = {}
    for group, period in ((new, FIRST_PERIOD), (old, LATER_PERIOD)):
        if group:
            closes.update(closes_fn(group, period))
    missing = sorted(set(tickers) - set(closes))
    if missing:
        log.warning("sp500_members: no closes for %d member(s): %s", len(missing),
                    ", ".join(missing[:10]))
    return rows + close_rows(closes, session.utc_iso(timespec="microseconds"))


def pull(run_id: Optional[str] = None, db=None) -> dict:
    if HELD_FOR_D1C:
        return {"source": SOURCE, "status": "HELD", "written": 0,
                "reason": HOLD_REASON, "keys": KEYS}
    return pub.run(SOURCE, KEYS, lambda: produce(db), run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
