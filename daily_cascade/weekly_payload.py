"""
The Weekly Tactical's payload. Sunday 05:00 ET. (Phase 4a; Audit #3 §I)

    python -m daily_cascade.weekly_payload --week-ending 2026-09-18

One anchor replacing the Friday Reflection and the Sunday Forward Plan. NO SLOT
COMPUTES: every block reads the object, the register, the grader, the probability
ledger and the store, and any figure it cannot read it reports absent with the
reason. The market-state object is read through regime.latest() exactly as the
other anchors read it -- a weekly that recomputed the week's regime could disagree
with the five close reports that already published it.

-----------------------------------------------------------------------------
THE FIVE BLOCKS, AND WHY THEY ARE IN THIS ORDER
-----------------------------------------------------------------------------

  THE WEEK IN STATE     Friday's object against the previous Friday's. What the
                        regime did over five sessions rather than overnight, which
                        is the horizon a weekly decision is taken on.
  GRADES                The learning loop. MOVED here from the close report,
                        which was its lodging until this slot existed -- the close
                        now carries one line and a pointer.
  REGISTER              What is open, what is pending, what broke. Before the
                        calendar, because a plan for next week that has not read
                        the open book is a plan for somebody else's book.
  THE WEEK AHEAD        Scheduled releases, earnings, session events, FOMC. Data
                        only: a date is a fact and what it means is the
                        paragraph's job.
  WEEKEND DEVELOPMENTS  Prints `not_yet_sourced` and says what would fill it. The
                        block exists so its absence is visible rather than
                        looking like a quiet weekend.

-----------------------------------------------------------------------------
WHAT A WEEK IS HERE
-----------------------------------------------------------------------------

A week ENDS ON A FRIDAY and is named by it. The Sunday run reports on the week
whose Friday has just passed, so `week_ending` is the last completed session on or
before that Friday -- on a Good Friday it is the Thursday, and the block says which
date it used rather than assuming the calendar.

The comparison is Friday against THE PREVIOUS FRIDAY's object, not against five
daily diffs added up. A dimension that flipped on Tuesday and flipped back on
Thursday did not change over the week, and a sum of daily diffs would report two
changes where a reader should see none. The intra-week churn is reported
separately, because "it moved twice and came back" is a different fact from
"nothing happened" and a weekly that could not tell them apart would be blind to
the most common shape of a noisy week.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
from typing import Any, Optional

from altdata import claims, observations, session

from . import precision

log = logging.getLogger("daily_cascade.weekly")

# The five blocks, in order. Declared so the validator can assert completeness
# against one list rather than against a shape it infers from a run.
BLOCKS = ("week_in_state", "grades", "register", "week_ahead",
          "weekend_developments")

# The instrument whose closes price a distance-to-invalidation. SPY, because that
# is what the register's open positions are denominated in today; a position on
# another underlying reports its distance absent rather than borrowing SPY's price.
PRICE_METRIC_PREFIX = "yfinance.mkt_"

# How many FRED series' release mappings to resolve per run. The map is stored and
# permanent -- a series' owning release does not change -- so it completes over a
# few Sundays rather than spending 59 calls on the first one.
RELEASE_MAP_PER_RUN = 20
RELEASE_MAP_KEY = "fred.series_release_map"

FRED_BASE = "https://api.stlouisfed.org/fred"


# ---------------------------------------------------------------------------
# What a week is
# ---------------------------------------------------------------------------
def week_ending(day: Optional[str] = None) -> str:
    """The Friday the reported week ended on, as a session date.

    Given any date, walks back to that week's Friday and then to the last session
    on or before it -- so a Good Friday resolves to the Thursday. The Sunday run
    passes nothing and gets the Friday two days behind it.
    """
    d = (dt.date.fromisoformat(day[:10]) if day
         else session.last_completed_session())
    # Sunday is weekday 6, Friday 4. From a Sunday, back two days.
    back = (d.weekday() - 4) % 7
    friday = d - dt.timedelta(days=back)
    if session.calendar_covers(friday) and not session.is_trading_session(friday):
        return session.previous_trading_session(friday).isoformat()
    return friday.isoformat()


def week_sessions(ending: str) -> list[str]:
    """Every session in the week ending on `ending`, Monday through Friday."""
    end = dt.date.fromisoformat(ending[:10])
    start = end - dt.timedelta(days=(end.weekday()))
    out = []
    d = start
    while d <= end:
        if (session.is_trading_session(d) if session.calendar_covers(d)
                else d.weekday() < 5):
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def previous_week_ending(ending: str) -> str:
    return week_ending((dt.date.fromisoformat(ending[:10])
                        - dt.timedelta(days=7)).isoformat())


# ---------------------------------------------------------------------------
# Block 1 -- the week in state
# ---------------------------------------------------------------------------
def week_in_state(ending: str, store: Optional[Any] = None) -> dict:
    """Friday's object against the previous Friday's, plus the week's churn."""
    out: dict[str, Any] = {"state": "absent", "week_ending": ending,
                           "previous_week_ending": previous_week_ending(ending)}
    try:
        import regime                                          # noqa: PLC0415
    except Exception as exc:                                   # noqa: BLE001
        out["reason"] = f"regime unavailable: {type(exc).__name__}: {exc}"
        return out
    try:
        now = regime.latest(session_day=ending, store=store)
        was = regime.latest(session_day=out["previous_week_ending"], store=store)
    except Exception as exc:                                   # noqa: BLE001
        out["reason"] = f"object unreadable: {type(exc).__name__}: {exc}"
        return out
    if now is None:
        out["reason"] = (f"no market-state object for {ending} -- the close pass "
                         f"computes it and this anchor reads it, so its absence "
                         f"means that Friday's close pass did not run")
        return out
    out["state"] = "ok"
    out["config_version"] = now.get("config_version")
    out["method_version"] = now.get("method_version")
    out["session_events"] = now.get("session_events")

    # --- dimensions, week over week -----------------------------------------
    cur = now.get("dimensions") or {}
    prev = (was or {}).get("dimensions") or {}
    changes, held = [], []
    for name, d in sorted(cur.items()):
        a = (prev.get(name) or {}).get("state")
        b = d.get("state")
        row = {"dimension": name, "from": a, "to": b,
               "percentile": d.get("percentile"),
               "direction": d.get("direction"),
               "confidence": d.get("confidence"),
               "last_changed": d.get("last_changed"),
               "absent_reason": d.get("absent_reason")}
        (changes if (was is not None and a != b) else held).append(row)
    out["dimension_changes"] = changes
    out["dimensions_held"] = [r["dimension"] for r in held]
    if was is None:
        out["comparison_note"] = (
            f"no object for {out['previous_week_ending']}, so nothing is reported "
            f"as changed rather than everything being reported as new")

    # --- dials ---------------------------------------------------------------
    dials_now = now.get("dials") or {}
    dials_was = (was or {}).get("dials") or {}
    out["dial_changes"] = [
        {"dial": n, "from": (dials_was.get(n) or {}).get("state"),
         "to": (v or {}).get("state"),
         "absent_reason": (v or {}).get("absent_reason")}
        for n, v in sorted(dials_now.items())
        if was is not None
        and (dials_was.get(n) or {}).get("state") != (v or {}).get("state")]
    out["dials_now"] = {n: (v or {}).get("state")
                        for n, v in sorted(dials_now.items())}

    # --- exceptions over the week -------------------------------------------
    # OPENED AND CLOSED ARE THE WEEK'S ENDPOINTS; CHURN IS EVERYTHING BETWEEN.
    # An exception that opened on Tuesday and closed on Thursday appears in
    # neither endpoint set and is the fact a weekly is most likely to miss.
    ids_now = set(regime.exception_ids(now))
    ids_was = set(regime.exception_ids(was)) if was else set()
    seen: dict[str, list[str]] = {}
    days = week_sessions(ending)
    for day in days:
        try:
            o = regime.latest(session_day=day, store=store)
        except Exception:                                      # noqa: BLE001
            continue
        for i in regime.exception_ids(o) if o else []:
            seen.setdefault(i, []).append(day)
    out["exceptions_opened"] = sorted(ids_now - ids_was)
    out["exceptions_closed"] = sorted(ids_was - ids_now)
    out["exceptions_open_now"] = sorted(ids_now)
    out["exceptions_intraweek_only"] = sorted(
        i for i in seen if i not in ids_now and i not in ids_was)
    out["exceptions_sessions_seen"] = {i: len(v) for i, v in sorted(seen.items())}
    out["sessions_in_week"] = days
    out["objects_found"] = sum(
        1 for day in days
        if (regime.latest(session_day=day, store=store) is not None))

    # --- contradictions, with persistence ------------------------------------
    out["contradictions"] = [
        {k: r.get(k) for k in ("id", "legs", "open_state", "magnitude",
                               "threshold_z", "since", "persistence_days",
                               "exception", "absent_reason")}
        for r in (now.get("contradictions") or [])]

    # --- THE VOL DIAL'S TWO LEGS, and the week's agreement count -------------
    # The dual run's whole question is a COUNT OF DISAGREEING SESSIONS, and this is
    # the block that counts them. Recorded per week rather than per quarter so the
    # answer accumulates in public instead of being computed once at the end by
    # whoever remembers.
    ts = ((dials_now.get("vol") or {}).get("term_structure") or {})
    agree = {"agreed": 0, "disagreed": 0, "not_comparable": 0}
    for day in days:
        try:
            o = regime.latest(session_day=day, store=store)
        except Exception:                                      # noqa: BLE001
            continue
        t = (((o or {}).get("dials") or {}).get("vol") or {}).get(
            "term_structure") or {}
        v = t.get("legs_agree")
        agree["agreed" if v is True else
              "disagreed" if v is False else "not_comparable"] += 1
    out["vol_term_structure"] = {
        "published_by": ts.get("published_by"),
        "published_state": ts.get("state"),
        "champion": {k: (ts.get("champion") or {}).get(k)
                     for k in ("metric", "state", "ratio", "percentile",
                               "absent_reason")},
        "challenger": {k: (ts.get("challenger") or {}).get(k)
                       for k in ("metric", "state", "ratio", "percentile",
                                 "absent_reason")},
        "basis": ts.get("basis"),
        "dual_run_until": ts.get("dual_run_until"),
        "week_agreement": agree,
    }
    return out


# ---------------------------------------------------------------------------
# Block 2 -- grades (moved here from the close report)
# ---------------------------------------------------------------------------
def grades(ending: str) -> dict:
    """The shadow grader's week, the running cuts, and the Brier ledger.

    THIS BLOCK'S HOME. payload.grades_block() carried it in the close report and
    said in its own docstring that it was a lodger until the Sunday anchor existed.
    It exists now, so the close report keeps one line and a pointer and the learning
    loop is read at the cadence it is written on.
    """
    out: dict[str, Any] = {"state": "absent", "reason": "", "week_ending": ending}
    days = week_sessions(ending)
    start = days[0] if days else ending
    try:
        # `cuts` lives in tools/, which is not a package and is not on the path
        # unless a caller put it there. The close report's grades block relied on
        # its entry point having done so, which is why this block reported the
        # grader "unavailable" on its first run from a plain module import.
        import sys as _sys                                     # noqa: PLC0415
        from pathlib import Path as _Path                       # noqa: PLC0415
        _tools = str(_Path(__file__).resolve().parent.parent / "tools")
        if _tools not in _sys.path:
            _sys.path.insert(0, _tools)
        from altdata import grader, probability_ledger          # noqa: PLC0415
        import cuts                                            # noqa: PLC0415
    except Exception as exc:                                   # noqa: BLE001
        out["reason"] = f"grader unavailable: {type(exc).__name__}: {exc}"
        return out
    try:
        with grader.GradeStore() as gs:
            rows = gs.all_grades()
        out["method_version"] = grader.METHOD_VERSION
        out["total_graded"] = len(rows)
        # THE WEEK'S OWN GRADES: everything that reached its horizon inside the
        # week, by graded_at. A grade written on Saturday belongs to the week it
        # was written in, which is this one.
        week = [g for g in rows
                if start <= str(g.get("graded_at") or "")[:10] <= ending]
        out["graded_this_week"] = [
            {k: g.get(k) for k in
             ("decision_id", "instrument", "horizon", "status",
              "operator_action", "return_pct", "r_multiple", "r_multiple_ruled",
              "invalidation_hit", "horizon_date", "graded_at",
              "mechanism_group")}
            for g in week]
        out["cuts"] = cuts.all_cuts()
        out["state"] = "ok" if rows else "empty"
        if not rows:
            out["reason"] = (
                "the grader is working and nothing has reached its horizon yet, "
                "which is the expected state of a register days old -- not an "
                "error, and said positively so an empty table is not read as a "
                "broken block")
    except Exception as exc:                                   # noqa: BLE001
        out["reason"] = f"grades unreadable: {type(exc).__name__}: {exc}"

    # --- Brier, for every probability emitted --------------------------------
    try:
        with probability_ledger.ProbabilityLedger() as pl:
            allr = pl.all_rows()
            out["brier"] = {
                "method_version": probability_ledger.METHOD_VERSION,
                "emitted": len(allr),
                "resolved": sum(1 for r in allr
                                if r.get("outcome") is not None),
                "by_source": pl.score_by_source(),
                "due_unresolved": [
                    {k: r.get(k) for k in ("probability_id", "source", "claim",
                                           "probability", "resolve_by")}
                    for r in pl.due()],
            }
            if not allr:
                out["brier"]["reason"] = (
                    "no probability has been emitted yet. The ledger is seeded "
                    "from the Monthly's scenario weights, and until one is "
                    "recorded a Brier score would be a number about nothing")
    except Exception as exc:                                   # noqa: BLE001
        out["brier"] = {"reason": f"ledger unreadable: "
                                 f"{type(exc).__name__}: {exc}"}
    return out


# ---------------------------------------------------------------------------
# Block 3 -- the register
# ---------------------------------------------------------------------------
def _latest_close(db: observations.ObservationStore, instrument: str,
                  as_of: Optional[str] = None) -> Optional[float]:
    sym = (instrument or "").split("@")[0].strip().lower()
    if not sym:
        return None
    rows = db.as_of(f"{PRICE_METRIC_PREFIX}{sym}", as_of=as_of)
    return float(rows[-1]["value_num"]) if rows and rows[-1]["value_num"] else None


def register_week(ending: str, store: Optional[Any] = None) -> dict:
    """Open decisions with their distance and age, drafts, and what broke."""
    out: dict[str, Any] = {"state": "absent", "reason": "", "week_ending": ending}
    days = week_sessions(ending)
    start = days[0] if days else ending
    try:
        from register.store import Register                     # noqa: PLC0415
    except Exception as exc:                                    # noqa: BLE001
        out["reason"] = f"register unavailable: {type(exc).__name__}: {exc}"
        return out
    own = store is None
    db = store or observations.ObservationStore()
    try:
        reg = Register()
        try:
            rows = reg.all()
            attempts = reg.blocked_attempts()
        finally:
            reg.close()
    except Exception as exc:                                    # noqa: BLE001
        out["reason"] = f"register unreadable: {type(exc).__name__}: {exc}"
        if own:
            db.close()
        return out
    try:
        end_dt = dt.date.fromisoformat(ending[:10])
        open_rows, drafts = [], []
        for r in rows:
            d = dict(r)
            if d.get("superseded_by"):
                continue
            status = d.get("status")
            if status not in ("active", "draft"):
                continue
            level = d.get("invalidation_level")
            px = _latest_close(db, d.get("instrument") or "")
            dist_pts = dist_pct = None
            if isinstance(level, (int, float)) and px:
                dist_pts = round(px - float(level), 2)
                dist_pct = round(100.0 * (px - float(level)) / float(level), 2)
            try:
                age = (end_dt - dt.date.fromisoformat(
                    str(d.get("decision_time"))[:10])).days
            except (TypeError, ValueError):
                age = None
            item = {
                "id": d.get("id"), "instrument": d.get("instrument"),
                "direction": d.get("direction"), "status": status,
                "thesis_state": d.get("thesis_state"),
                "edge_type": d.get("edge_type"), "horizon": d.get("horizon"),
                "expression_family": d.get("expression_family"),
                "leverage_form": d.get("leverage_form"),
                "base_rate_cited": d.get("base_rate_cited"),
                "invalidation": d.get("invalidation"),
                "invalidation_level": level,
                "mark": px,
                "distance_points": dist_pts,
                "distance_pct": dist_pct,
                "age_days": age,
                "blocked_reason": d.get("blocked_reason"),
            }
            if dist_pts is None:
                item["distance_absent_reason"] = (
                    "no invalidation_level recorded" if not level else
                    f"no stored close for {d.get('instrument')}")
            (drafts if status == "draft" else open_rows).append(item)
        out["open"] = open_rows
        out["drafts"] = drafts
        out["open_count"] = len(open_rows)
        out["drafts_count"] = len(drafts)
        out["state"] = "ok"

        # --- WHAT BROKE. Two things the register can count, and three it cannot.
        week_attempts = [dict(a) for a in attempts
                         if start <= str(a.get("attempted_at") or "")[:10]
                         <= ending]
        out["rule_breaks"] = {
            "restricted_instrument_attempts_this_week": len(week_attempts),
            "restricted_instrument_attempts_total": len(attempts),
            "decision_blocked_this_week": sum(
                1 for r in rows if dict(r).get("blocked_reason")
                and start <= str(dict(r).get("created_at"))[:10] <= ending),
            "running_total_note": (
                "the Doctrine's Book D gate trends this to zero, so the running "
                "total is the figure that matters and the week's count is how it "
                "moved"),
            # THE DOCTRINE'S POSITION RULE BREAKS ARE NOT SOURCED, and saying so is
            # the point of the block. Each needs something the register does not
            # carry, named rather than left as a silent zero: a zero here would
            # read as "no rule was broken this week", which is a claim this system
            # cannot currently make.
            "not_yet_sourced": {
                "allocation_floor_breach": {
                    "needs": ["a band-weighted stance per book",
                              "the current band from the Macro dial"],
                    "why": "a stance below the floor of the current band is a rule "
                           "break, and nothing computes the stance yet"},
                "book_b_conversion": {
                    "needs": ["a book label on each decision",
                              "the reason a position was closed"],
                    "why": "a Book B position closed inside two sessions for a "
                           "reason other than its invalidation level is a rule "
                           "break; the register records neither the book nor the "
                           "closing reason"},
                "time_stop_passed": {
                    "needs": ["a time stop per decision"],
                    "why": "a Book B position past its time stop is closed "
                           "regardless of thesis, and no time stop is recorded"},
            },
        }
    finally:
        if own:
            db.close()
    return out


# ---------------------------------------------------------------------------
# Block 4 -- the week ahead
# ---------------------------------------------------------------------------
def _fred_get(path: str, params: dict) -> Any:
    import urllib.parse                                        # noqa: PLC0415
    import urllib.request                                      # noqa: PLC0415
    url = f"{FRED_BASE}/{path}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "chester-reports"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def release_map(db: observations.ObservationStore, api_key: str,
                limit: int = RELEASE_MAP_PER_RUN) -> dict:
    """{series key -> release id and name}, stored and extended a little each run.

    A series' owning release does not change, so the map is written once per series
    and kept -- `revision_policy: never`. Resolving all 59 on one Sunday would be
    59 calls for a table that is then permanent; `limit` spreads it over a few
    weeks, and the block reports how complete it is rather than implying the whole
    calendar.
    """
    from altdata import config                                 # noqa: PLC0415
    rows = db.as_of(RELEASE_MAP_KEY)
    known: dict[str, Any] = {}
    if rows:
        try:
            known = json.loads(rows[-1]["value_text"]) or {}
        except Exception:                                      # noqa: BLE001
            known = {}
    want = [s for s in config.FRED_SERIES if s.key not in known]
    added = 0
    for spec in want[:limit]:
        try:
            got = _fred_get("series/release",
                            {"series_id": spec.fred_id, "api_key": api_key,
                             "file_type": "json"})
            rel = (got.get("releases") or [{}])[0]
            known[spec.key] = {"release_id": rel.get("id"),
                               "release_name": rel.get("name"),
                               "fred_id": spec.fred_id}
            added += 1
        except Exception as exc:                               # noqa: BLE001
            log.info("release map: %s unresolved (%s)", spec.key,
                     type(exc).__name__)
    if added:
        db.write(RELEASE_MAP_KEY, None,
                 session.last_completed_session().isoformat(),
                 session.utc_iso(timespec="microseconds"),
                 json.dumps(known, sort_keys=True), source="fred",
                 availability_kind="ingest_instant")
    return {"map": known, "resolved": len(known),
            "of": len(list(config.FRED_SERIES)), "added_this_run": added}


def week_ahead(ending: str, store: Optional[Any] = None,
               fetch: bool = True) -> dict:
    """Releases, earnings, session events and the dated claims for next week."""
    out: dict[str, Any] = {"state": "ok", "week_ending": ending}
    start = (dt.date.fromisoformat(ending[:10]) + dt.timedelta(days=3))
    end = start + dt.timedelta(days=6)
    out["window"] = [start.isoformat(), end.isoformat()]

    # --- session events, from the calendar we already own --------------------
    evs = {}
    d = start
    while d <= end:
        if session.is_trading_session(d) if session.calendar_covers(d) \
                else d.weekday() < 5:
            evs[d.isoformat()] = session.auction_event_classes(d)
        d += dt.timedelta(days=1)
    out["session_events"] = evs
    out["session_events_note"] = (
        "from the committed holiday and expiry table. INDEX_REBALANCE and "
        "ETF_REBALANCE are declared tables and empty, so a rebalance date nobody "
        "entered reads as an ordinary session -- which is why the class list is "
        "printed per day rather than only the exceptions")

    # --- the dated claims: FOMC and the midterm ------------------------------
    dated = []
    # ONLY THE IDS THAT EXIST. An unknown id raises by design, and a block that
    # cited a year whose calendar has not been entered would report an absent claim
    # every Sunday until somebody noticed. cal.fomc_2026's review_date is 1 December
    # 2026, which is when 2027 has to be entered -- so the heartbeat asks for it
    # instead of this block failing quietly all year.
    for cid in ("cal.fomc_2026", "cal.midterm_election_2026"):
        try:
            dated.append(claims.cite(cid))
        except Exception as exc:                               # noqa: BLE001
            dated.append({"id": cid, "absent_reason": str(exc)[:120]})
    out["dated_claims"] = dated

    own = store is None
    db = store or observations.ObservationStore()
    try:
        # --- FRED release dates ---------------------------------------------
        from altdata import secrets                            # noqa: PLC0415
        key = secrets.get("FRED" + "_API_KEY")
        if not key:
            out["releases"] = {"state": "absent", "reason":
                               "no FRED key in the environment or .env, so the "
                               "release calendar cannot be fetched. The series "
                               "themselves are unaffected; only next week's dates "
                               "are missing"}
        elif not fetch:
            out["releases"] = {"state": "skipped",
                               "reason": "--no-fetch"}
        else:
            try:
                rm = release_map(db, key)
                got = _fred_get("releases/dates",
                                {"api_key": key, "file_type": "json",
                                 "realtime_start": start.isoformat(),
                                 "realtime_end": end.isoformat(),
                                 "include_release_dates_with_no_data": "true",
                                 "limit": 1000})
                tracked = {v.get("release_id"): k
                           for k, v in (rm["map"] or {}).items()}
                rows = []
                for r in got.get("release_dates") or []:
                    rid = r.get("release_id")
                    rows.append({"date": r.get("date"),
                                 "release_id": rid,
                                 "release_name": r.get("release_name"),
                                 "tracked_series": sorted(
                                     k for k, v in (rm["map"] or {}).items()
                                     if v.get("release_id") == rid)})
                out["releases"] = {
                    "state": "ok",
                    "count": len(rows),
                    "tracked_count": sum(1 for r in rows if r["tracked_series"]),
                    "map_resolved": rm["resolved"], "map_of": rm["of"],
                    "map_added_this_run": rm["added_this_run"],
                    "rows": rows,
                    "note": ("every release FRED publishes in the window, with the "
                             "tracked series each one carries. A release with no "
                             "tracked series is listed because the calendar is a "
                             "fact and what matters is the operator's judgement")
                    if rows else "FRED returned no release dates in the window",
                }
            except Exception as exc:                           # noqa: BLE001
                out["releases"] = {"state": "error",
                                   "reason": f"{type(exc).__name__}: "
                                             f"{str(exc)[:140]}"}

        # --- earnings dates for the universe ---------------------------------
        if not fetch:
            out["earnings"] = {"state": "skipped", "reason": "--no-fetch"}
        else:
            out["earnings"] = earnings_dates(start, end)
    finally:
        if own:
            db.close()
    return out


def earnings_dates(start: dt.date, end: dt.date) -> dict:
    """Earnings dates in the window for the chain-capture universe.

    yfinance is the source and it is the weak link: `calendar` carries a date for
    some names and nothing for others, and it offers no as-of history at all. So
    this is a FORWARD READ with no memory -- the block says which names answered
    and which did not, rather than presenting a partial list as the calendar.
    """
    out: dict[str, Any] = {"state": "absent", "in_window": [], "no_date": [],
                           "failed": []}
    try:
        from altdata import config                             # noqa: PLC0415
        import yfinance as yf                                  # noqa: PLC0415
    except Exception as exc:                                    # noqa: BLE001
        out["reason"] = f"unavailable: {type(exc).__name__}: {exc}"
        return out
    # THE INDEX ETFs HAVE NO EARNINGS, and asking yfinance for their fundamentals
    # logs an HTTP 404 per name per Sunday. It is the same fact the consensus logger
    # recorded about forward estimates: no analyst covers a wrapper. Excluded by
    # DECLARATION rather than by swallowing the error, so a reader can tell "has no
    # earnings" from "the lookup failed".
    no_earnings = {"SPY", "QQQ", "IWM", "DIA", "RSP"}
    out["excluded_no_earnings"] = sorted(no_earnings)
    for sym in config.options_universe():
        if sym in no_earnings:
            continue
        try:
            cal = yf.Ticker(sym).calendar or {}
            dates = cal.get("Earnings Date") or []
            if not isinstance(dates, (list, tuple)):
                dates = [dates]
            hits = []
            for v in dates:
                try:
                    d = v if isinstance(v, dt.date) else dt.date.fromisoformat(
                        str(v)[:10])
                except (TypeError, ValueError):
                    continue
                if start <= d <= end:
                    hits.append(d.isoformat())
            if hits:
                out["in_window"].append({"symbol": sym, "dates": sorted(hits)})
            elif not dates:
                out["no_date"].append(sym)
        except Exception as exc:                                # noqa: BLE001
            out["failed"].append({"symbol": sym,
                                  "error": f"{type(exc).__name__}"})
    out["state"] = "ok"
    out["note"] = (f"{len(out['in_window'])} name(s) report in the window; "
                   f"{len(out['no_date'])} carry no date and "
                   f"{len(out['failed'])} could not be read. yfinance offers no "
                   f"as-of history for this field, so it is a forward read with "
                   f"no memory and no vintage")
    return out


# ---------------------------------------------------------------------------
# Block 5 -- weekend developments
# ---------------------------------------------------------------------------
def weekend_developments() -> dict:
    """Declared absent, on purpose, so the hole is visible in the document.

    An anchor that simply omitted the weekend would read identically on a quiet
    weekend and on a weekend nobody instrumented. This block is the difference.
    """
    return {
        "state": "not_yet_sourced",
        "reason": "not yet sourced -- events ingest (6c)",
        "needs": ["an events ingest with consensus/actual/surprise (6c, S8)",
                  "the forward calendar (S9)",
                  "the 07:00 narrative scan over stored events"],
        "why_the_block_exists": (
            "so the absence is visible. Without it a quiet weekend and an "
            "uninstrumented one are the same document, and the second is the one "
            "that costs something"),
    }


# ---------------------------------------------------------------------------
# The payload
# ---------------------------------------------------------------------------
def build(ending: Optional[str] = None, as_of: Optional[str] = None,
          run_id: Optional[str] = None, fetch: bool = True) -> dict:
    """Every block. Reads only; never raises on a missing one."""
    end = week_ending(ending)
    db = observations.ObservationStore()
    try:
        out: dict[str, Any] = {
            "report": "weekly_tactical",
            "week_ending": end,
            "previous_week_ending": previous_week_ending(end),
            "sessions_in_week": week_sessions(end),
            "generated_at": session.utc_iso(),
            "as_of": as_of or session.utc_iso(timespec="microseconds"),
            "run_id": run_id,
            "blocks": list(BLOCKS),
        }
        out["week_in_state"] = week_in_state(end, store=db)
        out["grades"] = grades(end)
        out["register"] = register_week(end, store=db)
        out["week_ahead"] = week_ahead(end, store=db, fetch=fetch)
        out["weekend_developments"] = weekend_developments()
        warnings = []
        for name in BLOCKS:
            b = out.get(name) or {}
            # `empty` IS AN EXPECTED STATE, NOT AN ABSENCE. The grader working
            # with nothing yet at its horizon is the normal condition of a young
            # register, and listing it as an absence every Sunday would teach the
            # reader to skip the absences list -- which is where a real one has to
            # be seen.
            if b.get("state") not in ("ok", "empty", "not_yet_sourced"):
                warnings.append(f"{name}: {b.get('state')} -- "
                                f"{b.get('reason') or 'no reason recorded'}")
        out["warnings"] = warnings
        return out
    finally:
        db.close()


def narrative_payload(full: dict) -> dict:
    """The figures the weekly paragraph may cite, at print precision.

    Narrower than the document: the cuts' full breakdowns and every release row
    would put hundreds of figures in front of the model, most of them intermediate,
    and a paragraph given all of them can cite an intermediate as a headline. What
    travels is what the template's coverage asks for.
    """
    st = full.get("week_in_state") or {}
    gr = full.get("grades") or {}
    rg = full.get("register") or {}
    wa = full.get("week_ahead") or {}
    out = {
        "week_ending": full.get("week_ending"),
        "previous_week_ending": full.get("previous_week_ending"),
        "sessions_in_week": len(full.get("sessions_in_week") or []),
        "state": {
            "dimension_changes": st.get("dimension_changes"),
            "dimensions_held": st.get("dimensions_held"),
            "dial_changes": st.get("dial_changes"),
            "dials_now": st.get("dials_now"),
            "exceptions_opened": st.get("exceptions_opened"),
            "exceptions_closed": st.get("exceptions_closed"),
            "exceptions_open_now": st.get("exceptions_open_now"),
            "exceptions_intraweek_only": st.get("exceptions_intraweek_only"),
            "contradictions": [r for r in (st.get("contradictions") or [])
                               if r.get("open_state") != "absent"],
            "vol_term_structure": st.get("vol_term_structure"),
            "session_events": st.get("session_events"),
            "absent_reason": st.get("reason"),
        },
        "grades": {
            "total_graded": gr.get("total_graded"),
            "graded_this_week": gr.get("graded_this_week"),
            "overall": (gr.get("cuts") or {}).get("overall"),
            "by_status": (gr.get("cuts") or {}).get("by_status"),
            "brier": {k: v for k, v in (gr.get("brier") or {}).items()
                      if k in ("emitted", "resolved", "by_source", "reason")},
            "absent_reason": gr.get("reason"),
        },
        "register": {
            "open_count": rg.get("open_count"),
            "drafts_count": rg.get("drafts_count"),
            "open": rg.get("open"),
            "rule_breaks": rg.get("rule_breaks"),
            "absent_reason": rg.get("reason"),
        },
        "week_ahead": {
            "window": wa.get("window"),
            "session_events": wa.get("session_events"),
            "releases_tracked_count": (wa.get("releases") or {}).get(
                "tracked_count"),
            "releases_state": (wa.get("releases") or {}).get("state"),
            "earnings_in_window": (wa.get("earnings") or {}).get("in_window"),
            "dated_claims": [
                {k: c.get(k) for k in ("id", "value", "source", "as_of")}
                for c in (wa.get("dated_claims") or [])],
        },
        "weekend_developments": (full.get("weekend_developments")
                                 or {}).get("reason"),
        "absences": full.get("warnings"),
    }
    return precision.apply(out)


def _main(argv: list[str]) -> int:
    import argparse
    p = argparse.ArgumentParser(description="The Weekly Tactical's payload.")
    p.add_argument("--week-ending", default=None)
    p.add_argument("--no-fetch", action="store_true")
    p.add_argument("--narrative", action="store_true",
                   help="print the narrative subset instead of the whole payload")
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    full = build(a.week_ending, fetch=not a.no_fetch)
    print(json.dumps(narrative_payload(full) if a.narrative else full,
                     indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
