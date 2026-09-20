"""
RTAT10 -- Nasdaq's Retail Trading Activity Tracker, top ten. (Part 29.3)

Daily retail activity share and a sentiment score for the ten tickers with the most
retail activity. Logging only: what this writes is history, and the analysis that
reads it is 6h and gated.

    python -m altdata.loggers.rtat probe
    python -m altdata.loggers.rtat pull                 # the nightly step
    python -m altdata.loggers.rtat backfill --since 2016-01-01
    python -m altdata.loggers.rtat derived

-----------------------------------------------------------------------------
THE SAMPLE IS CENSORED AND EVERY DERIVED METRIC SAYS SO
-----------------------------------------------------------------------------

This table contains ten rows a day and the universe is thousands of tickers. A
ticker's absence means "not in the top ten", NOT "no retail activity" -- and the two
are only the same if you forget which table you are reading.

Every derived metric carries `sample: top10_censored` in the registry, because each
of them is systematically wrong in a knowable direction:

  CONCENTRATION is computed over the visible ten, so it is an upper bound on the
  concentration of the whole market's retail activity -- the invisible tail is
  flatter than anything here.
  PERSISTENCE counts consecutive days IN THE TOP TEN, so a ticker that drops to
  eleventh reads as a break in a run that did not break.
  NEW-ENTRANT SHOCK counts arrivals into the visible set, which is a measure of
  turnover at the boundary rather than of new retail interest.

None of these is a reason not to log it. All three are a reason not to let the
label "retail concentration" travel without the qualifier.

-----------------------------------------------------------------------------
AVAILABILITY: ingest_instant, INCLUDING FOR THE BACKFILL
-----------------------------------------------------------------------------

The reconstruction rule permits a reconstructed availability for a series whose
revision_policy is `never`, and RTAT is never revised. It is NOT used here, because
permitted is not the same as knowable: the API response carries no publication
timestamp and the vendor's release lag is not documented in anything this code can
read. Reconstructing "available at the close plus X" would be inventing X.

So every row -- live and backfilled -- is stamped with the write instant and
flagged `ingest_instant`, which is an upper bound and therefore safe for an as-of
join. The consequence, stated plainly: the backfilled history is invisible to a
cutoff before today, exactly like the migrated FRED series. It is there so the
derived metrics have a distribution to stand on, not so a 2019 decision can be
replayed against it.
"""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional

from .. import observations, secrets, session
from . import INSUFFICIENT, LoggerSpec, guarded, register

log = logging.getLogger(__name__)

KEY_NAME = "NASDAQ_DATA_LINK_API_KEY"
BASE = "https://data.nasdaq.com/api/v3/datatables/NDAQ/RTAT10"

ACTIVITY_KEY = "ndl.rtat10_activity"
SENTIMENT_KEY = "ndl.rtat10_sentiment"
CONCENTRATION_KEY = "ndl.rtat10_concentration"
PERSISTENCE_KEY = "ndl.rtat10_persistence"
ENTRANT_KEY = "ndl.rtat10_new_entrants"

# FREE-TIER THROTTLE. The documented limit for a registered key is generous and the
# backfill is a one-off over ten years; pacing at two seconds a page keeps a decade
# under a few hundred calls and well inside any published ceiling. Chosen to be
# obviously polite rather than tuned to a limit that can change without notice.
PAGE_PAUSE_SECONDS = 2.0
MAX_PAGES = 400
TIMEOUT = 45

# Derived metrics need a distribution. Sixty sessions is a quarter -- enough for a
# percentile to mean something and short enough that the metrics come alive within
# the first quarter of logging rather than after a year.
MIN_HISTORY = 60

# The top ten is the sample, so a day with fewer rows is a partial day and not a
# smaller top ten.
EXPECTED_PER_DAY = 10


def _fetch_page(cursor: Optional[str] = None,
                date_gte: Optional[str] = None) -> dict:
    key = secrets.require(KEY_NAME)
    params = {"api_key": key, "qopts.per_page": "10000"}
    if cursor:
        params["qopts.cursor_id"] = cursor
    if date_gte:
        params["date.gte"] = date_gte
    url = f"{BASE}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read(400).decode("utf-8", "replace")
        # redact(): a 4xx body echoes the request URL, and the key is in it.
        raise RuntimeError(
            f"HTTP {exc.code}: {secrets.redact(body)}") from None
    except Exception as exc:                                  # noqa: BLE001
        raise RuntimeError(secrets.redact(f"{type(exc).__name__}: {exc}")) from None


def parse_page(payload: dict) -> tuple[list[dict], Optional[str]]:
    """(rows, next_cursor). Column order is READ, not assumed.

    The datatable declares its own columns in the response, and taking them by
    position would break silently the day Nasdaq adds one.
    """
    dt = (payload or {}).get("datatable") or {}
    cols = [c.get("name") for c in (dt.get("columns") or [])]
    out = []
    for raw in dt.get("data") or []:
        row = dict(zip(cols, raw))
        day = str(row.get("date") or "")[:10]
        ticker = row.get("ticker")
        if not day or not ticker:
            continue
        out.append({"date": day, "ticker": str(ticker),
                    "activity": row.get("activity"),
                    "sentiment": row.get("sentiment")})
    cursor = ((payload or {}).get("meta") or {}).get("next_cursor_id")
    return out, cursor


def probe() -> dict:
    """Ask, and record the answer either way."""
    if not secrets.present(KEY_NAME):
        return {"ok": False, "reason": f"{KEY_NAME} is not configured",
                "checked_at": session.utc_iso()}
    try:
        payload = _fetch_page()
        rows, cursor = parse_page(payload)
        days = sorted({r["date"] for r in rows})
        return {"ok": True, "rows": len(rows),
                "first_date": days[0] if days else None,
                "last_date": days[-1] if days else None,
                "paged": bool(cursor), "checked_at": session.utc_iso()}
    except Exception as exc:                                  # noqa: BLE001
        return {"ok": False, "reason": secrets.redact(str(exc)),
                "checked_at": session.utc_iso()}


def _write(rows: list[dict], store: observations.ObservationStore,
           run_id: Optional[str] = None) -> int:
    now = session.utc_iso(timespec="microseconds")
    out = []
    for r in rows:
        for key, value in ((ACTIVITY_KEY, r.get("activity")),
                           (SENTIMENT_KEY, r.get("sentiment"))):
            if value is None:
                continue
            out.append({"registry_key": key, "instrument": r["ticker"],
                        "observed_at": r["date"], "available_at": now,
                        "value": float(value), "source": "nasdaq_data_link",
                        "run_id": run_id,
                        "availability_kind": "ingest_instant"})
    return store.write_many(observations.drop_unchanged(store, out))


def pull(since: Optional[str] = None, run_id: Optional[str] = None,
         store: Optional[observations.ObservationStore] = None,
         max_pages: int = MAX_PAGES) -> dict:
    """The nightly step, and the backfill, which differ only in `since`."""
    if not secrets.present(KEY_NAME):
        # BUILT, DORMANT, AND SAYING SO. Not an error: the freshness roster is
        # what reports it, as the series going stale.
        log.warning("rtat: %s is not configured -- nothing pulled. The series "
                    "will go stale and the heartbeat will say so.", KEY_NAME)
        return {"skipped": "key not configured", "rows": 0, "written": 0}

    own = store is None
    db = store or observations.ObservationStore()
    try:
        cursor, pages, seen, written = None, 0, 0, 0
        first_day = last_day = None
        while pages < max_pages:
            payload = _fetch_page(cursor=cursor, date_gte=since)
            rows, cursor = parse_page(payload)
            pages += 1
            if rows:
                seen += len(rows)
                days = sorted({r["date"] for r in rows})
                first_day = min(first_day or days[0], days[0])
                last_day = max(last_day or days[-1], days[-1])
                written += _write(rows, db, run_id)
            if not cursor:
                break
            time.sleep(PAGE_PAUSE_SECONDS)
        return {"pages": pages, "rows": seen, "written": written,
                "first_date": first_day, "last_date": last_day,
                "truncated": bool(cursor)}
    except Exception as exc:                                  # noqa: BLE001
        log.warning("rtat: pull failed -- %s", secrets.redact(str(exc)))
        return {"error": secrets.redact(str(exc)), "rows": 0, "written": 0}
    finally:
        if own:
            db.close()


# ---------------------------------------------------------------------------
# Derived -- every one of them reads insufficient_history until MIN_HISTORY
# ---------------------------------------------------------------------------
def _by_day(db: observations.ObservationStore, as_of: Optional[str] = None
            ) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for inst in db.instruments(ACTIVITY_KEY):
        for r in db.as_of(ACTIVITY_KEY, as_of=as_of, instrument=inst):
            v = r.get("value_num")
            if v is None:
                continue
            out.setdefault(str(r["observed_at"])[:10], {})[inst] = float(v)
    return out


def derived(as_of: Optional[str] = None,
            store: Optional[observations.ObservationStore] = None) -> dict:
    """Concentration, persistence and new-entrant shock, for the latest day."""
    own = store is None
    db = store or observations.ObservationStore()
    try:
        def compute() -> dict:
            by_day = _by_day(db, as_of)
            days = sorted(by_day)
            if not days:
                return {"state": "no_data"}
            today = by_day[days[-1]]
            total = sum(today.values()) or 1.0

            # CONCENTRATION: the top name's share OF THE VISIBLE TEN, plus a
            # Herfindahl over the same ten. An upper bound on the market's true
            # retail concentration, because the invisible tail is flatter.
            shares = sorted((v / total for v in today.values()), reverse=True)
            hhi = sum(s * s for s in shares)
            top1 = shares[0] if shares else None

            # PERSISTENCE: consecutive days in the visible set, per ticker. A drop
            # to eleventh reads as a break in a run that did not break.
            persistence = {}
            for ticker in today:
                run = 0
                for day in reversed(days):
                    if ticker in by_day[day]:
                        run += 1
                    else:
                        break
                persistence[ticker] = run

            # NEW ENTRANTS: arrivals into the visible set since the prior day --
            # turnover at the boundary, not new retail interest.
            prior = set(by_day[days[-2]]) if len(days) > 1 else set()
            entrants = sorted(set(today) - prior) if prior else []

            return {
                "state": "ok",
                "as_of_day": days[-1],
                "members": len(today),
                "partial_day": len(today) != EXPECTED_PER_DAY,
                "concentration_hhi": round(hhi, 6),
                "concentration_top1_share": (round(top1, 6) if top1 is not None
                                             else None),
                "persistence_days": persistence,
                "persistence_max": max(persistence.values()) if persistence else None,
                "new_entrants": entrants,
                "new_entrant_count": len(entrants),
                "sample": "top10_censored",
                "caveat": ("concentration is an upper bound, persistence breaks "
                           "when a ticker leaves the visible ten, and entrants "
                           "measure boundary turnover"),
            }

        # One gate for the whole block: these three metrics share a history.
        first = (db.instruments(ACTIVITY_KEY) or [None])[0]
        return guarded(ACTIVITY_KEY, MIN_HISTORY, compute, store=db,
                       instrument=first)
    finally:
        if own:
            db.close()


def keys() -> list[str]:
    return [ACTIVITY_KEY, SENTIMENT_KEY]


SPEC = register(LoggerSpec(
    name="rtat10",
    description="Nasdaq RTAT10 -- daily top-ten retail activity share and "
                "sentiment. Top-ten censored sample.",
    keys=keys,
    run=pull,
    requires_key=KEY_NAME,
    min_history=MIN_HISTORY,
    notes="Part 29.3. Logging only; the analysis that reads it is 6h and gated.",
))


def _main(argv: list[str]) -> int:
    import argparse
    p = argparse.ArgumentParser(description="RTAT10 logger.")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("probe")
    pl = sub.add_parser("pull")
    pl.add_argument("--since", default=None)
    bf = sub.add_parser("backfill")
    bf.add_argument("--since", default="2016-01-01")
    sub.add_parser("derived")
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")

    if a.cmd == "probe":
        print(json.dumps(probe(), indent=2, sort_keys=True))
        return 0
    if a.cmd == "derived":
        print(json.dumps(derived(), indent=2, sort_keys=True, default=str))
        return 0
    since = a.since
    r = pull(since=since)
    print(json.dumps(r, indent=2, sort_keys=True))
    return 0 if not r.get("error") else 1


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
