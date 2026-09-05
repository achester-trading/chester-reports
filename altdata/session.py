"""
One source of truth for "what time is it" and "what day is this".

THE BUG FAMILY THIS EXISTS TO KILL. Three separate defects, all the same shape:

    1. pin_log       keyed rows on the UTC compute date, so a Friday EOD run
                     after 20:00 ET filed the session under Saturday and failed
                     to replace the existing Friday rows.
    2. run_eod       stage 4 looked for data/chains/<UTC date>/ and reported
                     "no chain directory" for a directory that never existed.
    3. options_chain wrote chains under the UTC date while run_eod read the ET
                     session date. The 16:10 ET run worked only by coincidence
                     -- 16:10 ET is 20:10 UTC, still the same calendar day. Any
                     run after 20:00 ET broke.

All three are the same mistake: a US trading session was keyed by a UTC
calendar date. The two coincide for most of the day and diverge exactly in the
evening, which is when an EOD pipeline runs.

THE FIX IS THE NAMING, not the arithmetic. Two kinds of value get confused
because both come from "now":

    an INSTANT   when something happened -- fetched_at, computed_at, a log
                 line, a filename stamp. UTC is correct and always has been.
                 Use utc_now() / utc_iso() / utc_stamp().

    a SESSION    which trading day a record belongs to -- a directory name, a
                 pin-log key, a backup key. This is a US market concept and
                 must be ET. Use session_date().

Naming them differently is the point. `dt.date.today()` looks equally right for
both, which is why this happened three times; `session_date()` next to
`utc_iso()` makes the choice visible at the call site.

WHAT session_date IS NOT. It is a calendar date in US/Eastern, not a trading
calendar: it does not know about weekends or market holidays, and a Saturday
run returns Saturday. Callers that need "the last session that actually traded"
must ask a calendar, not this module. Naming it session_date rather than
et_date is a deliberate bet that trading-session semantics are what callers
want; if a real trading calendar arrives, it belongs here and every call site
picks it up at once.
"""

from __future__ import annotations

import datetime as dt
from typing import Optional, Union

# The exchange timezone for every US market session in this system. Not the
# box's timezone: the VPS runs UTC by design, and nothing here may depend on
# what `date` prints locally.
EASTERN = "America/New_York"


def _eastern_tz():
    """ZoneInfo for the exchange, imported lazily so a missing tzdata degrades
    to UTC rather than breaking a data capture at the import line."""
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(EASTERN)
    except Exception:  # noqa: BLE001 -- see docstring
        return dt.timezone.utc


# ---------------------------------------------------------------------------
# Instants -- when something happened. Always UTC.
# ---------------------------------------------------------------------------

def utc_now() -> dt.datetime:
    """Timezone-aware current UTC instant.

    Use instead of datetime.utcnow(), which returns a NAIVE datetime and is
    deprecated from Python 3.12. A naive UTC timestamp compared against an
    aware one raises; worse, it silently mislabels when written to a file.
    """
    return dt.datetime.now(dt.timezone.utc)


def utc_iso(timespec: str = "seconds") -> str:
    """Current UTC instant as an ISO-8601 string, for provenance fields."""
    return utc_now().isoformat(timespec=timespec)


def utc_stamp(fmt: str = "%Y%m%dT%H%M%SZ") -> str:
    """Current UTC instant formatted for a filename."""
    return utc_now().strftime(fmt)


# ---------------------------------------------------------------------------
# Sessions -- which trading day a record belongs to. Always ET.
# ---------------------------------------------------------------------------

def to_eastern(ts: Union[dt.datetime, str, None] = None) -> dt.datetime:
    """Convert an instant to Eastern. Naive input is assumed UTC.

    Assuming UTC for naive input is the safe reading here: every naive
    timestamp this system produces came from a UTC clock.
    """
    if ts is None:
        ts = utc_now()
    elif isinstance(ts, str):
        try:
            ts = dt.datetime.fromisoformat(ts)
        except ValueError:
            ts = utc_now()
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=dt.timezone.utc)
    return ts.astimezone(_eastern_tz())


def session_date(ts: Union[dt.datetime, str, None] = None) -> str:
    """The US trading-session date (YYYY-MM-DD, Eastern) for an instant.

    Pass the instant the data was observed -- a chain's fetched_at, say -- so a
    record is filed under the session it belongs to rather than the session it
    happened to be processed in. With no argument it uses now, which is correct
    for a live capture and wrong for reprocessing history; prefer passing the
    observation time whenever one exists.
    """
    return to_eastern(ts).date().isoformat()


def session_date_obj(ts: Union[dt.datetime, str, None] = None) -> dt.date:
    """session_date() as a date object, for arithmetic such as DTE."""
    return to_eastern(ts).date()


def is_same_session(a: Union[dt.datetime, str],
                    b: Union[dt.datetime, str]) -> bool:
    """Do two instants fall in the same ET trading session?"""
    return session_date(a) == session_date(b)


def describe() -> str:
    """One line for logs: both clocks, so a mismatch is visible in the record."""
    now = utc_now()
    return (f"utc={now.isoformat(timespec='seconds')} "
            f"session={session_date(now)} ({EASTERN})")
