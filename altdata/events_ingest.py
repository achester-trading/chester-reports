"""
The ingest pass: every source into the events table, once.

    python -m altdata.events_ingest pull
    python -m altdata.events_ingest pull --only news,session
    python -m altdata.events_ingest probe

-----------------------------------------------------------------------------
SEVEN SOURCES, TWO OF THEM LOCAL
-----------------------------------------------------------------------------

  news            Fed, BLS and BEA press feeds (releases) + the declared story
                  queries (headlines). Free, no key.
  edgar           SEC filings for the universe. DORMANT until CHESTER_SEC_CONTACT
                  is set -- EDGAR 403s a User-Agent without a contact address.
  earnings        yfinance: the next date with its analyst consensus, and the
                  reported history with the real surprise (needs lxml).
  fred_releases   the release calendar. DORMANT without FRED_API_KEY.
  session         OPEX, triple witching, month- and quarter-end, the rebalances --
                  from altdata/session.py, which is the one place the calendar
                  rules live. No network.
  claims          FOMC meeting dates and the midterm, from config/claims.yaml. No
                  network. These are CLAIMS rather than observations because they
                  are dates somebody published, and the registry is where such a
                  thing already lives.

EVERY SOURCE REPORTS ITS OWN STATE and none of them can fail the pass. A feed that
404s, a key that is unset and a dependency that is missing are three different
absences, each named, and the ingest returns a report rather than an exception --
because the pass runs unattended at 06:45 and 16:10 and a traceback there is a
silent hole in the record the next morning's anchor reads.

-----------------------------------------------------------------------------
IDEMPOTENT BY CONSTRUCTION
-----------------------------------------------------------------------------

Every source is polled and every row is content-hashed, so running this twice in a
minute inserts nothing the second time. That is what makes the cadence a choice
rather than a risk: an hourly RSS pull costs a request and no rows, and a missed
pass costs nothing a later one cannot recover (except for a feed that has already
rolled its window -- which is why the ingest runs twice a day rather than once).
"""

from __future__ import annotations

import datetime as dt
import logging
import re
from typing import Any, Iterable, Optional

from . import claims as claims_mod
from . import events as ev_mod
from . import session

log = logging.getLogger(__name__)

SOURCES = ("news", "edgar", "earnings", "fred_releases", "session", "claims")

# How far ahead the local calendars are written. Three months of session events and
# the FOMC dates a quarter out is what a weekly and a monthly can both read; going
# further would fill the table with rows nothing reads.
FORWARD_DAYS = 95
BACK_DAYS = 10

MONTHS = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct",
     "Nov", "Dec"], start=1)}


# ---------------------------------------------------------------------------
# Local source 1: the session's own event classes
# ---------------------------------------------------------------------------
def session_events(first: Optional[str] = None,
                   last: Optional[str] = None) -> tuple[list[ev_mod.Event], dict]:
    """OPEX, triple witching, month- and quarter-end, the rebalances.

    READ FROM altdata/session.py, never re-derived. The object already carries
    these classes per session and the calendar rules are declared there; a second
    implementation here would be a second answer about whether a Friday is triple
    witching.
    """
    today = dt.date.fromisoformat(session.session_date())
    lo = dt.date.fromisoformat(first) if first else today - dt.timedelta(
        days=BACK_DAYS)
    hi = dt.date.fromisoformat(last) if last else today + dt.timedelta(
        days=FORWARD_DAYS)
    out: list[ev_mod.Event] = []
    day = lo
    n_sessions = 0
    while day <= hi:
        if session.is_trading_session(day):
            n_sessions += 1
            classes = [c for c in session.auction_event_classes(day)
                       if c != "NORMAL"]
            # `NORMAL` IS NOT AN EVENT. auction_event_classes returns ['NORMAL']
            # for an ordinary session, and storing that wrote a calendar entry for
            # every trading day -- 65 rows saying nothing happened, which is how a
            # table of events becomes a table of days. What stays: OPEX, triple
            # witching, month- and quarter-end, the two rebalances.
            if classes:
                # 20:00 UTC is the 16:00 ET close: an OPEX day's property is about
                # that session, and stamping it at midnight would file it under the
                # day before.
                when = f"{day.isoformat()}T20:00:00+00:00"
                forward = day > today
                out.append(ev_mod.Event(
                    type="scheduled" if forward else "session_event",
                    observed_at=when, source="session_calendar",
                    title=f"{day.isoformat()}: {', '.join(classes)}",
                    entities=[], key=f"session-{day.isoformat()}",
                    payload={"classes": list(classes), "forward": forward,
                             "session": day.isoformat()}))
        day += dt.timedelta(days=1)
    return out, {"state": "ok", "window": [lo.isoformat(), hi.isoformat()],
                 "sessions_scanned": n_sessions, "events": len(out)}


# ---------------------------------------------------------------------------
# Local source 2: the claims registry's calendar
# ---------------------------------------------------------------------------
def _fomc_dates(text: str, year: int) -> list[dt.date]:
    """The decision days out of "Jan 27-28, Mar 17-18, ...".

    THE DECISION LANDS ON THE SECOND DAY, which the claim's own `unit` field
    states. So a two-day meeting produces ONE event, dated the day the statement is
    released -- because that is the day the market cares about and the day a
    "what is ahead" block should name.
    """
    out = []
    for mon, d1, d2 in re.findall(r"([A-Z][a-z]{2})\s+(\d{1,2})(?:-(\d{1,2}))?",
                                  text):
        m = MONTHS.get(mon)
        if not m:
            continue
        day = int(d2 or d1)
        try:
            out.append(dt.date(year, m, day))
        except ValueError:
            continue
    return out


def claims_events() -> tuple[list[ev_mod.Event], dict]:
    """FOMC meetings and the midterm, from the claims registry."""
    try:
        reg = (claims_mod.load() or {}).get("claims") or {}
    except Exception as exc:                                   # noqa: BLE001
        return [], {"state": "failed",
                    "reason": f"{type(exc).__name__}: {exc}"[:160]}
    out: list[ev_mod.Event] = []
    report: dict[str, Any] = {"state": "ok", "claims_read": []}

    for cid, claim in reg.items():
        if not cid.startswith("cal."):
            continue
        value = str(claim.get("value") or "")
        report["claims_read"].append(cid)
        year_m = re.search(r"(20\d\d)", cid + " " + value)
        year = int(year_m.group(1)) if year_m else dt.date.today().year
        if "fomc" in cid:
            for d in _fomc_dates(value, year):
                # 18:00 UTC = 14:00 ET, the statement release.
                out.append(ev_mod.Event(
                    type="scheduled",
                    observed_at=f"{d.isoformat()}T18:00:00+00:00",
                    source="claims_registry",
                    title=f"FOMC statement -- {d.isoformat()}",
                    entities=["fred.fed_funds"], key=f"fomc-{d.isoformat()}",
                    payload={"claim_id": cid, "kind": "fomc",
                             "cited_as": cid,
                             "note": claim.get("unit")}))
            continue
        iso = re.fullmatch(r"\d{4}-\d{2}-\d{2}", value.strip())
        if iso:
            out.append(ev_mod.Event(
                type="scheduled", observed_at=f"{value.strip()}T13:30:00+00:00",
                source="claims_registry",
                title=str(claim.get("unit") or cid),
                entities=[], key=cid,
                payload={"claim_id": cid, "cited_as": cid,
                         "note": (claim.get("detail") or {}).get("note")
                         if isinstance(claim.get("detail"), dict) else None}))
    report["events"] = len(out)
    return out, report


# ---------------------------------------------------------------------------
# The pass
# ---------------------------------------------------------------------------
def pull(only: Optional[Iterable[str]] = None, dry_run: bool = False,
         store: Optional[ev_mod.EventStore] = None) -> dict:
    """Every source, or the named ones. Never raises."""
    wanted = set(only) if only else set(SOURCES)
    own = store is None
    ev = store or ev_mod.EventStore()
    report: dict[str, Any] = {"at": session.utc_iso(), "dry_run": dry_run,
                              "sources": {}}
    total = {"seen": 0, "inserted": 0, "duplicates": 0}
    try:
        for name in SOURCES:
            if name not in wanted:
                continue
            try:
                if name == "news":
                    from .sources import news
                    press, prep = news.press_events()
                    stories, srep = news.story_events()
                    events, rep = press + stories, {"press": prep,
                                                    "stories": srep}
                elif name == "edgar":
                    from .sources import edgar
                    events, rep = edgar.filing_events()
                elif name == "earnings":
                    from .sources import earnings
                    events, rep = earnings.earnings_events()
                elif name == "fred_releases":
                    from .sources import fred_releases
                    events, rep = fred_releases.calendar_events()
                elif name == "session":
                    events, rep = session_events()
                else:
                    events, rep = claims_events()
            except Exception as exc:                           # noqa: BLE001
                # A SOURCE MAY NOT FAIL THE PASS. This runs unattended twice a day
                # and a traceback here is a hole in tomorrow's anchor.
                log.exception("%s raised", name)
                report["sources"][name] = {
                    "state": "raised",
                    "reason": f"{type(exc).__name__}: {exc}"[:200]}
                continue
            wrote = ({"seen": len(events), "inserted": 0, "duplicates": 0}
                     if dry_run else ev.write_many(events))
            for k in total:
                total[k] += wrote[k]
            report["sources"][name] = {"report": rep, "written": wrote}
        report["total"] = total
        report["counts"] = ev.counts()
        return report
    finally:
        if own:
            ev.close()


def _main(argv: list[str]) -> int:
    import argparse
    import json
    p = argparse.ArgumentParser(description="Ingest every event source.")
    sub = p.add_subparsers(dest="cmd", required=True)
    for cmd in ("pull", "probe"):
        c = sub.add_parser(cmd)
        c.add_argument("--only", default=None,
                       help=f"comma-separated subset of {','.join(SOURCES)}")
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    only = [s.strip() for s in a.only.split(",")] if a.only else None
    r = pull(only=only, dry_run=(a.cmd == "probe"))

    print(f"{'source':<16}{'state':<14}{'seen':>7}{'new':>7}{'dup':>7}")
    for name, got in r["sources"].items():
        w = got.get("written") or {}
        rep = got.get("report") or {}
        state = got.get("state") or (
            rep.get("state") if isinstance(rep, dict) else None) or "ok"
        print(f"{name:<16}{str(state):<14}{w.get('seen', 0):>7}"
              f"{w.get('inserted', 0):>7}{w.get('duplicates', 0):>7}")
        reason = got.get("reason") or (rep.get("reason")
                                       if isinstance(rep, dict) else None)
        if reason:
            print(f"    {str(reason)[:150]}")
    print(f"\ntotal: {r['total']}")
    print("by type: " + json.dumps({k: v["n"] for k, v in
                                    (r.get("counts") or {}).items()}))
    return 0


if __name__ == "__main__":                                     # pragma: no cover
    import sys
    raise SystemExit(_main(sys.argv[1:]))
