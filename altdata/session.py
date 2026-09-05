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

WHAT session_date IS NOT. It is a calendar date in US/Eastern, and it is not a
verdict about whether the market was open: a Saturday run still returns
Saturday. That is correct for its job -- filing a record under the ET day it
was observed -- and it must stay that way, because a function that silently
rolled a Saturday observation back to Friday would file weekend data under a
session that never saw it.

    "which ET day is this record filed under?"   -> session_date()
    "would the exchange have been open?"         -> is_trading_session()
    "which session actually traded before this?" -> previous_trading_session()

The trading calendar promised by the earlier version of this docstring now
lives at the bottom of this module: a hand-kept table of NYSE holidays and
early closes with its source and its expiry documented. It is here, next to
session_date(), for the same reason everything else is -- one table, one place,
every call site picking it up at once. The shell wrappers reach it through
`python -m altdata.session is-session`, so scripts/ holds no second copy.
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


def new_run_id(producer: str) -> str:
    """A run's identity: '<producer>-<utc stamp>'.

    ONE convention, defined here rather than per-producer, because the whole
    value of a run_id is that rows from different producers can be traced to
    the run that made them. Two producers inventing two formats gives you two
    opaque strings instead of a lineage.

    An INSTANT, not a session date -- a run is a thing that happened at a
    moment, and two runs for the same trading session must be distinguishable.

    MICROSECONDS, not the seconds the output filenames use. A run id whose
    resolution is coarser than the rate at which runs can start is not an
    identity: two syncs in the same second would share one, and rows from two
    different runs would be indistinguishable in the store -- which is the
    precise failure a run_id exists to prevent. The date-time prefix still
    sorts and reads alongside the filenames; only the tail is finer.
    """
    return f"{producer}-{utc_stamp('%Y%m%dT%H%M%S.%fZ')}"


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


# ---------------------------------------------------------------------------
# The trading calendar -- which ET dates the exchange is actually open.
#
# The module docstring above promised that if a real trading calendar ever
# arrived it would live here so every call site picks it up at once. This is
# that calendar. session_date() is deliberately unchanged: it still answers
# "which ET date is this instant filed under", which is the right question for
# a filename or a pin-log key even on a Saturday. is_trading_session() answers
# the separate question "would the exchange have been open", which is what a
# scheduler needs before it burns a run.
#
# SOURCE. Transcribed 2026-09-05 from the NYSE holiday and hours calendar,
# https://www.nyse.com/markets/hours-calendars. The exchange publishes these
# roughly three years ahead and does not move them retroactively, so a
# hand-kept table is honest for the horizon it covers -- but it is a
# transcription, and the two observation rules below are what let a reader
# re-derive it rather than trust it:
#
#   * A holiday falling on a Saturday closes the exchange the preceding Friday
#     (2026-07-03 for July 4th; 2027-06-18 for Juneteenth; 2027-12-24 for
#     Christmas).
#   * A holiday falling on a Sunday closes it the following Monday
#     (2027-07-05 for July 4th).
#
# Good Friday is a market holiday although it is not a federal one, and it
# moves with Easter: 2026-04-03 and 2027-03-26.
#
# MAINTENANCE. This table ends 2027-12-31, and CALENDAR_YEARS records that.
# Extend it in the last quarter of 2027 at the latest; see is_trading_session()
# for what happens past the edge, which is deliberately not "skip the run".
# ---------------------------------------------------------------------------

CALENDAR_YEARS = (2026, 2027)

# Full closures. The exchange is shut; there is no session and no data.
NYSE_HOLIDAYS = {
    "2026-01-01": "New Year's Day",
    "2026-01-19": "Martin Luther King, Jr. Day",
    "2026-02-16": "Washington's Birthday",
    "2026-04-03": "Good Friday",
    "2026-05-25": "Memorial Day",
    "2026-06-19": "Juneteenth National Independence Day",
    "2026-07-03": "Independence Day (observed; July 4 is a Saturday)",
    "2026-09-07": "Labor Day",
    "2026-11-26": "Thanksgiving Day",
    "2026-12-25": "Christmas Day",

    "2027-01-01": "New Year's Day",
    "2027-01-18": "Martin Luther King, Jr. Day",
    "2027-02-15": "Washington's Birthday",
    "2027-03-26": "Good Friday",
    "2027-05-31": "Memorial Day",
    "2027-06-18": "Juneteenth (observed; June 19 is a Saturday)",
    "2027-07-05": "Independence Day (observed; July 4 is a Sunday)",
    "2027-09-06": "Labor Day",
    "2027-11-25": "Thanksgiving Day",
    "2027-12-24": "Christmas Day (observed; December 25 is a Saturday)",
}

# Early closes: the exchange shuts at 13:00 ET instead of 16:00.
#
# THESE ARE SESSIONS. They trade, they settle, they produce a chain, and the
# EOD pass must run on them -- the 16:10 ET timer simply fires three hours
# after the close instead of ten minutes after it, which is harmless for
# settled-OI chain data. They are tabulated because "why is the 16:10 snapshot
# three hours stale" is a question somebody will eventually ask of the record,
# and because an intraday sampler would need them. Nothing here makes them
# non-sessions.
#
# Note the asymmetry a reader might otherwise flag as a missing entry: when a
# holiday is observed on an adjacent weekday, the exchange does not also close
# early on the day before it. Hence no 2026-07-02 and no 2027-12-23.
NYSE_EARLY_CLOSES = {
    "2026-11-27": "Day after Thanksgiving (13:00 ET close)",
    "2026-12-24": "Christmas Eve (13:00 ET close)",

    "2027-11-26": "Day after Thanksgiving (13:00 ET close)",
}

DateLike = Union[dt.date, dt.datetime, str, None]


def _as_date(value: DateLike = None) -> dt.date:
    """Coerce a date, datetime, ISO string, or None into an ET calendar date.

    None and datetimes go through session_date_obj(), so an instant is resolved
    in Eastern rather than in whatever the box's clock says. A bare date is
    already a calendar date and is taken as given.
    """
    if value is None:
        return session_date_obj()
    if isinstance(value, dt.datetime):
        return session_date_obj(value)
    if isinstance(value, dt.date):
        return value
    text = str(value).strip()
    try:
        return dt.date.fromisoformat(text[:10])
    except ValueError:
        # An unparseable string is a caller bug, not a market condition. Say so
        # rather than quietly answering for today and having the wrong day get
        # filed or skipped.
        raise ValueError(f"not an ISO date or instant: {value!r}") from None


def calendar_covers(day: DateLike = None) -> bool:
    """Is this date inside the years the holiday table actually enumerates?"""
    return _as_date(day).year in CALENDAR_YEARS


def is_weekend(day: DateLike = None) -> bool:
    """Saturday or Sunday in ET."""
    return _as_date(day).weekday() >= 5


def holiday_name(day: DateLike = None) -> Optional[str]:
    """The NYSE holiday this date is, or None. Weekends are not holidays."""
    return NYSE_HOLIDAYS.get(_as_date(day).isoformat())


def is_market_holiday(day: DateLike = None) -> bool:
    """Is the exchange fully closed for a holiday on this date?"""
    return holiday_name(day) is not None


def early_close_name(day: DateLike = None) -> Optional[str]:
    """The early-close label for this date, or None. Early closes are sessions."""
    return NYSE_EARLY_CLOSES.get(_as_date(day).isoformat())


def is_early_close(day: DateLike = None) -> bool:
    """Does the exchange close at 13:00 ET on this date? Still a session."""
    return early_close_name(day) is not None


def is_trading_session(day: DateLike = None) -> bool:
    """Would the NYSE have been open on this ET date?

    False on weekends and on the full closures in NYSE_HOLIDAYS. True on early
    closes -- a half day is a day.

    FAIL OPEN PAST THE TABLE'S EDGE. A weekday in a year the table does not
    cover answers True. The asymmetry is deliberate: a spurious run on a
    holiday costs one wasted fetch against a closed-market chain, while a
    skipped real session loses data that yfinance will never serve again. When
    this table goes stale the pipeline must degrade toward running, not toward
    silence. Callers that want to say so in a log can ask calendar_covers().
    """
    d = _as_date(day)
    if d.weekday() >= 5:
        return False
    return d.isoformat() not in NYSE_HOLIDAYS


def session_reason(day: DateLike = None) -> str:
    """One line saying why a date is or is not a session, for a log record.

    The log is the only artifact left behind by a run that decided not to run,
    so it has to carry the reason and not merely the verdict.
    """
    d = _as_date(day)
    iso = d.isoformat()
    if d.weekday() >= 5:
        return f"{iso} non_session weekend ({d.strftime('%A')})"
    name = NYSE_HOLIDAYS.get(iso)
    if name:
        return f"{iso} non_session holiday: {name}"
    early = NYSE_EARLY_CLOSES.get(iso)
    if early:
        return f"{iso} session early_close: {early}"
    if not calendar_covers(d):
        return (f"{iso} session weekday "
                f"(WARNING past the {CALENDAR_YEARS[-1]} holiday table -- "
                f"holidays are no longer checked, extend NYSE_HOLIDAYS)")
    return f"{iso} session weekday"


def previous_trading_session(day: DateLike = None) -> dt.date:
    """The latest trading session strictly before this date.

    Bounded at 10 days: the longest real gap is a holiday-extended weekend, so
    a walk that runs longer means the table is wrong, and an unbounded loop
    would hide that instead of reporting it.
    """
    start = _as_date(day)
    d = start
    for _ in range(10):
        d -= dt.timedelta(days=1)
        if is_trading_session(d):
            return d
    raise RuntimeError(f"no trading session in the 10 days before {start}")


def last_trading_session(day: DateLike = None) -> dt.date:
    """This date if it is a session, else the latest session before it."""
    d = _as_date(day)
    return d if is_trading_session(d) else previous_trading_session(d)


def _main(argv) -> int:
    """Calendar queries for the shell wrappers, so scripts/*.sh never keeps a
    second copy of the holiday table. A duplicated table is the same defect
    this module exists to kill, one layer down.

        python -m altdata.session is-session [DATE]    exit 0 session, 1 not
        python -m altdata.session prev-session [DATE]  print the prior session
        python -m altdata.session last-session [DATE]  print DATE or the prior
        python -m altdata.session describe             print both clocks

    DATE defaults to today in ET. Every subcommand prints one line; is-session
    carries its verdict in the exit code too, so a wrapper can branch on it
    without parsing anything.
    """
    args = list(argv)
    cmd = args[0] if args else "describe"
    arg = args[1] if len(args) > 1 and args[1] else None

    try:
        if cmd == "is-session":
            print(session_reason(arg))
            return 0 if is_trading_session(arg) else 1
        if cmd == "prev-session":
            print(previous_trading_session(arg).isoformat())
            return 0
        if cmd == "last-session":
            print(last_trading_session(arg).isoformat())
            return 0
        if cmd == "describe":
            print(describe())
            return 0
    except Exception as exc:  # noqa: BLE001 -- the caller is a shell script
        print(f"error {cmd}: {exc}")
        return 2

    print(f"unknown subcommand: {cmd!r}")
    return 2


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
