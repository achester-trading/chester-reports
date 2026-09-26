"""
The FRED release calendar: when the tracked series print next, and when they did.

    python -m altdata.sources.fred_releases probe
    python -m altdata.sources.fred_releases pull

-----------------------------------------------------------------------------
IT NEEDS THE FRED KEY, AND IT IS DORMANT WITHOUT ONE
-----------------------------------------------------------------------------

Three endpoints, all requiring `api_key`:

  /fred/series/release?series_id=X      which release a series belongs to
  /fred/releases/dates?realtime_start=  every release date across FRED
  /fred/release/dates?release_id=X      one release's dates, forward and back

`FRED_API_KEY` is not set on the authoring laptop, so this module could not be
probed here and reports `not_configured` rather than guessing at shapes. The box
has the key -- the daily FRED pull runs there -- so the probe command is printed
for it in the report.

WHAT IT WILL PRODUCE, from the documented shapes: one `scheduled` event per
upcoming release for the series this system actually tracks, and one `release`
event per date that has passed. The series-to-release mapping is fetched once and
cached to `data/fred_release_map.json`, because it is a property of FRED's
catalogue rather than of today -- a series moves between releases roughly never,
and 59 lookups per pass to learn that is 59 requests for nothing.

-----------------------------------------------------------------------------
THE CALENDAR IS THE POINT, AND IT IS THE PART THIS SYSTEM HAS NEVER HAD
-----------------------------------------------------------------------------

Everything else here reports what happened. This is the only source that says what
is ABOUT to happen, which is what makes the anchor's "day ahead" block possible and
what makes `surprise_vs_naive` computable at all: a naive expectation has to exist
BEFORE the print, and knowing the print is due on Thursday is how it gets written
down on Wednesday.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

from .. import events as ev_mod
from .. import secrets, session
from ._base import FetchError, http_get_json

log = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent
MAP_PATH = REPO / "data" / "fred_release_map.json"
BASE = "https://api.stlouisfed.org/fred"

# How far forward and back a pull looks. Forward is the calendar the anchor prints;
# back is short because the actuals arrive through the ordinary FRED series pull and
# this is only the record that a release HAPPENED.
FORWARD_DAYS = 21
BACK_DAYS = 7


def key() -> Optional[str]:
    try:
        return secrets.get("FRED_" + "API_KEY")
    except Exception:                                          # noqa: BLE001
        return None


def _get(path: str, **params) -> dict:
    k = key()
    if not k:
        raise FetchError("FRED_API_KEY is not set")
    params.update({"api_key": k, "file_type": "json"})
    return http_get_json(f"{BASE}/{path}", params=params)


def release_map(refresh: bool = False) -> dict[str, dict]:
    """series key -> {release_id, release_name}, cached on disk.

    CACHED BECAUSE IT IS CATALOGUE, NOT DATA. Which release CPIAUCSL belongs to is
    a fact about FRED's structure that changes approximately never; asking it 59
    times on every pass would be 59 requests to learn the same thing.
    """
    if MAP_PATH.exists() and not refresh:
        try:
            return json.loads(MAP_PATH.read_text(encoding="utf-8"))
        except Exception:                                      # noqa: BLE001
            pass
    from .. import config
    out: dict[str, dict] = {}
    for spec in config.FRED_SERIES:
        try:
            j = _get("series/release", series_id=spec.fred_id)
        except Exception as exc:                               # noqa: BLE001
            log.warning("no release for %s: %s", spec.fred_id, exc)
            continue
        rel = (j.get("releases") or [{}])[0]
        if rel.get("id"):
            out[spec.key] = {"release_id": rel["id"],
                             "release_name": rel.get("name"),
                             "fred_id": spec.fred_id}
    MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
    MAP_PATH.write_text(json.dumps(out, indent=2, sort_keys=True),
                        encoding="utf-8")
    return out


def calendar_events() -> tuple[list[ev_mod.Event], dict]:
    """Upcoming and just-passed release dates for the tracked series."""
    if not key():
        return [], {"state": "not_configured", "reason": (
            "FRED_API_KEY is not set. Every releases endpoint requires it, so "
            "this source is dormant rather than guessed at: run "
            "`python -m altdata.sources.fred_releases probe` on the box, which "
            "has the key the daily FRED pull uses")}
    import datetime as dt
    today = dt.date.fromisoformat(session.session_date())
    start = (today - dt.timedelta(days=BACK_DAYS)).isoformat()
    end = (today + dt.timedelta(days=FORWARD_DAYS)).isoformat()
    report: dict[str, Any] = {"state": "ok", "window": [start, end]}
    try:
        rmap = release_map()
    except Exception as exc:                                   # noqa: BLE001
        return [], {"state": "failed",
                    "reason": f"release map: {type(exc).__name__}: {exc}"[:200]}
    report["series_mapped"] = len(rmap)

    # One request per RELEASE, not per series: a dozen releases cover 59 series,
    # and the entities on each event name every series that release carries.
    by_release: dict[int, dict] = {}
    for skey, m in rmap.items():
        r = by_release.setdefault(int(m["release_id"]),
                                  {"name": m.get("release_name"), "keys": []})
        r["keys"].append(skey)
    report["releases"] = len(by_release)

    out: list[ev_mod.Event] = []
    now = session.utc_iso()
    for rid, meta in sorted(by_release.items()):
        try:
            j = _get("release/dates", release_id=rid, realtime_start=start,
                     realtime_end=end, include_release_dates_with_no_data="true")
        except Exception as exc:                               # noqa: BLE001
            report.setdefault("failed", {})[str(rid)] = (
                f"{type(exc).__name__}: {exc}"[:120])
            continue
        for row in j.get("release_dates") or []:
            day = str(row.get("date") or "")[:10]
            if not day:
                continue
            # 13:30 UTC: most US macro prints land at 08:30 ET, and a date with no
            # time would otherwise sit at midnight -- in the previous session.
            when = f"{day}T13:30:00+00:00"
            forward = when > now
            out.append(ev_mod.Event(
                type="scheduled" if forward else "release",
                observed_at=when, source="fred_releases",
                title=f"{meta['name']} -- release date",
                entities=[f"fred.{k}" for k in meta["keys"]],
                key=f"fred-release-{rid}-{day}",
                payload={"release_id": rid, "release_name": meta["name"],
                         "series": meta["keys"], "release_date": day,
                         "forward": forward,
                         "time_note": "date only from FRED; stamped 13:30 UTC, "
                                      "the usual 08:30 ET print"}))
    report["events"] = len(out)
    return out, report


def pull(store: Optional[ev_mod.EventStore] = None,
         dry_run: bool = False) -> dict:
    own = store is None
    ev = store or ev_mod.EventStore()
    try:
        events, report = calendar_events()
        wrote = ({"seen": len(events), "inserted": 0, "duplicates": 0}
                 if dry_run else ev.write_many(events))
        return {"fred_releases": report, "written": wrote, "dry_run": dry_run}
    finally:
        if own:
            ev.close()


def _main(argv: list[str]) -> int:
    import argparse
    p = argparse.ArgumentParser(description="The FRED release calendar.")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("probe")
    pl = sub.add_parser("pull")
    pl.add_argument("--dry-run", action="store_true")
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO)
    events, rep = calendar_events()
    print(json.dumps(rep, indent=2, default=str)[:1600])
    for e in events[:10]:
        print(f"  {e.observed_at[:16]}  {e.type:<10} {e.title[:58]:<60}"
              f"{len(e.entities)} series")
    if a.cmd == "pull" and events:
        print(json.dumps(pull(dry_run=a.dry_run), indent=2, default=str)[:600])
    return 0


if __name__ == "__main__":                                     # pragma: no cover
    import sys
    raise SystemExit(_main(sys.argv[1:]))
