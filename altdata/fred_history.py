"""
The FRED history writer (AUD-3d, 15 Oct 2026): each value at the moment FRED
first published it.

    python -m altdata.fred_history backfill --series KEY[,KEY] [--from DATE] [--dry-run]
    python -m altdata.fred_history backfill --all [--from DATE] [--dry-run]

WHY. The live pull (altdata/sources/fred.py) reads 1,500 days and stamps every
row available at the instant it was written (availability_kind ingest_instant).
FRED history before about 2022 is therefore missing, and a deep pull stamped
today would be invisible to every as-of query before today -- the Alpha Lab's
long windows (H-002, H-004, H-005) would stay empty. observations.py reserves
`observed` for exactly this: "ALFRED vintages would be this".

WHAT IT WRITES, per registered FRED series (altdata.config.FRED_PULL_SERIES):

  - ALFRED's vintage history: every observation with its realtime_start, paged
    as FRED requires (vintage dates in pages of 10,000; observations over at most
    MAX_VINTAGES vintage dates a request, in pages of 100,000). A value is
    written once per vintage in which it CHANGED, so a revised value gets its own
    row from its own vintage date, and a window boundary never invents one.
  - available_at = the vintage's first publication: its date at the series'
    release time when the release calendar holds it (data/fred_release_map.json
    names the release; config/release_calendar.yaml gives its time, US Eastern),
    otherwise the END of that day (23:59:59.999999 ET) -- never earlier than the
    truth. availability_kind `observed`.
  - A series whose revision_policy is `never` or `split_only` and that ALFRED
    holds no vintages for may instead take RECONSTRUCTED availability: the
    observation date plus RECONSTRUCTED_LATENCY_BUSINESS_DAYS, at the end of that
    day ET (as tools/backfill_prices.py does for closes).
  - A REVISABLE series without vintages gets NOTHING, and is listed. (All 129
    registered FRED series are `revised` today.)

  Rows carry source `fred:backfill` (read as fred, per AUD-3a) and their own
  run_id. Existing rows are never rewritten (the store's INSERT OR IGNORE), and a
  value equal to one already stored for that period at the same or an EARLIER
  availability is not written again: it would be no new information. A stored
  value whose availability is LATER (a live pull's ingest instant) does not stop
  the earlier, truer vintage from being written -- that is the point.

THE ICE BOFA SERIES (BAML...): FRED keeps only about three years of them, by
licence. The dry run says so per series rather than treating a short history as
a failure.

--dry-run prints, per series: vintages, rows, the earliest observation and the
earliest availability; with --all, an estimate of rows, disk and run time. It
writes nothing.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
import time
from pathlib import Path
from typing import Callable, Optional

REPO = Path(__file__).resolve().parent.parent
BASE = "https://api.stlouisfed.org/fred"
SOURCE = "fred:backfill"
MAX_VINTAGES = 2000              # FRED refuses more vintage dates in one request
OBS_PAGE = 100000
VINTAGE_PAGE = 10000
PACING_SECONDS = 0.6             # under FRED's 120 requests a minute
RECONSTRUCTED_LATENCY_BUSINESS_DAYS = 1
BYTES_PER_ROW = 250              # the estimate's figure for a numeric row with its indexes
REALTIME_START = "1776-07-04"    # FRED's own earliest real-time date
REALTIME_END = "9999-12-31"
ICE_PREFIX = "BAML"

Get = Callable[[str, dict], dict]


# -- time --------------------------------------------------------------------
def _eastern():
    from . import session  # noqa: PLC0415
    return session._eastern_tz()                                  # noqa: SLF001


def published_at(day: str, release_time: Optional[str]) -> str:
    """The first-publication instant of a vintage dated `day`: at the release's
    time (HH:MM ET) when known, else the last microsecond of the day ET."""
    from .observations import canonical_instant  # noqa: PLC0415
    d = dt.date.fromisoformat(day[:10])
    if release_time:
        h, m = (int(x) for x in release_time.split(":"))
        local = dt.datetime(d.year, d.month, d.day, h, m)
    else:
        local = dt.datetime(d.year, d.month, d.day, 23, 59, 59, 999999)
    tz = _eastern()
    aware = local.replace(tzinfo=tz) if tz is not None else local.replace(
        tzinfo=dt.timezone(dt.timedelta(hours=-5)))
    return canonical_instant(aware.astimezone(dt.timezone.utc).isoformat())


def reconstructed_at(day: str) -> str:
    """The observation date plus the declared latency, at the end of that day ET."""
    d = dt.date.fromisoformat(day[:10])
    n = 0
    while n < RECONSTRUCTED_LATENCY_BUSINESS_DAYS:
        d += dt.timedelta(days=1)
        if d.weekday() < 5:
            n += 1
    return published_at(d.isoformat(), None)


def release_times(map_path: Optional[Path] = None,
                  calendar_path: Optional[Path] = None) -> dict[str, str]:
    """series key -> HH:MM ET, from the cached release map and the calendar's
    patterns. Read only; a missing map means end-of-day for every series."""
    import yaml  # noqa: PLC0415
    mp = Path(map_path or REPO / "data" / "fred_release_map.json")
    cp = Path(calendar_path or REPO / "config" / "release_calendar.yaml")
    if not mp.is_file():
        return {}
    rel = json.loads(mp.read_text(encoding="utf-8"))
    pats = (yaml.safe_load(cp.read_text(encoding="utf-8")) or {}).get("releases") or []
    out = {}
    for key, m in rel.items():
        name = str((m or {}).get("release_name") or "").lower()
        hit = next((p for p in pats if str(p.get("match", "")).lower() in name and name), None)
        if hit and hit.get("time"):
            out[key] = str(hit["time"])
    return out


# -- ALFRED ------------------------------------------------------------------
def _live_get(key: str) -> Get:
    from .sources._base import http_get_json  # noqa: PLC0415

    def get(path: str, params: dict) -> dict:
        time.sleep(PACING_SECONDS)
        return http_get_json(f"{BASE}/{path}", params={**params, "api_key": key,
                                                       "file_type": "json"})
    return get


def vintage_dates(series_id: str, get: Get) -> list[str]:
    out, offset = [], 0
    while True:
        try:
            r = get("series/vintagedates", {"series_id": series_id, "limit": VINTAGE_PAGE,
                                           "offset": offset, "sort_order": "asc"})
        except Exception as exc:                                  # noqa: BLE001
            if "400" in str(exc) or "not" in str(exc).lower():
                return []                                         # not in ALFRED
            raise
        page = r.get("vintage_dates") or []
        out += page
        if len(page) < VINTAGE_PAGE:
            return out
        offset += VINTAGE_PAGE


def _observations(series_id: str, get: Get, rt_start: str, rt_end: str,
                  obs_from: Optional[str]) -> list[dict]:
    out, offset = [], 0
    while True:
        p = {"series_id": series_id, "realtime_start": rt_start, "realtime_end": rt_end,
             "limit": OBS_PAGE, "offset": offset, "sort_order": "asc"}
        if obs_from:
            p["observation_start"] = obs_from
        page = get("series/observations", p).get("observations") or []
        out += page
        if len(page) < OBS_PAGE:
            return out
        offset += OBS_PAGE


def _num(v) -> Optional[float]:
    try:
        return None if v in (None, "", ".") else float(v)
    except (TypeError, ValueError):
        return None


def vintage_history(series_id: str, get: Get, vintages: list[str],
                    obs_from: Optional[str] = None) -> list[tuple[str, float, str]]:
    """(observation date, value, first-publication vintage date), one row per
    vintage in which the value changed. Requests at most MAX_VINTAGES vintage
    dates at a time; a period carried across a window boundary (FRED clips its
    realtime_start to the window) is not a new vintage because its value is
    unchanged."""
    last: dict[str, float] = {}
    rows: list[tuple[str, float, str]] = []
    for i in range(0, len(vintages), MAX_VINTAGES):
        win = vintages[i:i + MAX_VINTAGES]
        nxt = vintages[i + MAX_VINTAGES] if i + MAX_VINTAGES < len(vintages) else None
        end = ((dt.date.fromisoformat(nxt) - dt.timedelta(days=1)).isoformat()
               if nxt else REALTIME_END)
        obs = _observations(series_id, get, win[0], end, obs_from)
        for o in sorted(obs, key=lambda o: (o["date"], o["realtime_start"])):
            v = _num(o.get("value"))
            if v is None:
                continue
            if last.get(o["date"]) == v:
                continue
            last[o["date"]] = v
            rows.append((o["date"], v, o["realtime_start"]))
    return rows


# -- one series --------------------------------------------------------------
def plan(spec, get: Get, policy_of: Callable[[str], Optional[str]],
         times: dict[str, str], obs_from: Optional[str] = None) -> dict:
    """What the backfill would write for one series: rows and the summary."""
    from .observations import RECONSTRUCTABLE_POLICIES  # noqa: PLC0415
    key, sid = spec.key, spec.fred_id
    out = {"key": key, "fred_id": sid, "rows": [], "vintages": 0, "status": None,
           "note": None}
    vints = vintage_dates(sid, get)
    out["vintages"] = len(vints)
    if vints:
        t = times.get(key)
        for d, v, vd in vintage_history(sid, get, vints, obs_from):
            out["rows"].append({"observed_at": d, "value": v,
                                "available_at": published_at(vd, t),
                                "availability_kind": "observed"})
        out["status"] = "observed"
        out["release_time"] = t or "end of day (no release time held)"
    else:
        policy = policy_of(f"fred.{key}")
        if policy in RECONSTRUCTABLE_POLICIES:
            today = dt.date.today().isoformat()            # the current vintage only
            obs = _observations(sid, get, today, today, obs_from)
            for o in obs:
                v = _num(o.get("value"))
                if v is not None:
                    out["rows"].append({"observed_at": o["date"], "value": v,
                                        "available_at": reconstructed_at(o["date"]),
                                        "availability_kind": "reconstructed"})
            out["status"] = "reconstructed"
        else:
            out["status"] = "refused"
            out["note"] = (f"revision_policy {policy!r} and no ALFRED vintages: a revisable "
                           f"series gets vintages or nothing")
    if out["rows"]:
        out["earliest_observation"] = min(r["observed_at"] for r in out["rows"])
        out["earliest_available"] = min(r["available_at"] for r in out["rows"])
    if sid.startswith(ICE_PREFIX):
        span = out.get("earliest_observation")
        out["note"] = (f"ICE BofA: FRED keeps only about three years of this series, by "
                       f"licence (earliest held {span or 'none'}); a short history here "
                       f"is not a failure")
    return out


def new_rows(db, key: str, rows: list[dict]) -> list[dict]:
    """Drop a value already stored for its period at the same or an earlier
    availability: no new information. A later stored availability does not
    block an earlier, truer one."""
    have: dict[str, list[tuple[float, str]]] = {}
    for r in db.all_vintages(f"fred.{key}"):
        if r.get("value_num") is not None:
            have.setdefault(r["observed_at"][:10], []).append(
                (float(r["value_num"]), r["available_at"]))
    out = []
    for r in rows:
        prior = have.get(r["observed_at"][:10], [])
        if any(v == r["value"] and a <= r["available_at"] for v, a in prior):
            continue
        out.append(r)
    return out


def backfill(specs: list, get: Get, db=None, dry_run: bool = False,
             obs_from: Optional[str] = None,
             policy_of: Optional[Callable[[str], Optional[str]]] = None,
             times: Optional[dict[str, str]] = None,
             run_id: Optional[str] = None, echo: Callable[[str], None] = print) -> dict:
    from . import derived  # noqa: PLC0415
    policy_of = policy_of or (lambda m: derived.registry_entry(m).get("revision_policy"))
    times = release_times() if times is None else times
    run_id = run_id or "fred_history:" + dt.datetime.now(dt.timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ")
    t0 = time.monotonic()
    res = {"run_id": run_id, "dry_run": dry_run, "series": [], "written": 0,
           "rows": 0, "refused": [], "failed": []}
    for spec in specs:
        try:
            p = plan(spec, get, policy_of, times, obs_from)
        except Exception as exc:                                  # noqa: BLE001
            from . import secrets  # noqa: PLC0415
            res["failed"].append((spec.key, secrets.redact(str(exc))))
            echo(f"  FAILED  {spec.key}: {secrets.redact(str(exc))}")
            continue
        rows = p.pop("rows")
        if db is not None:
            rows = new_rows(db, spec.key, rows)
        p["rows"] = len(rows)
        res["rows"] += len(rows)
        if p["status"] == "refused":
            res["refused"].append((spec.key, p["note"]))
        if not dry_run and db is not None and rows:
            n = db.write_many([{**r, "registry_key": f"fred.{spec.key}", "instrument": None,
                                "source": SOURCE, "run_id": run_id} for r in rows])
            res["written"] += n
            p["written"] = n
        res["series"].append(p)
        echo(f"  {spec.key:<22} {p['status']:<13} vintages {p['vintages']:>5}  rows "
             f"{p['rows']:>7}  earliest obs {p.get('earliest_observation') or '-':<10}  "
             f"earliest avail {p.get('earliest_available') or '-'}"
             + (f"\n      {p['note']}" if p.get("note") else ""))
    res["seconds"] = round(time.monotonic() - t0, 1)
    if len(specs) > 1:
        res["estimate"] = {"rows": res["rows"],
                           "disk_mb": round(res["rows"] * BYTES_PER_ROW / 1e6, 1),
                           "run_minutes": round(res["seconds"] / 60 * 1.2, 1)}
        echo(f"\n  estimate: {res['rows']:,} rows, ~{res['estimate']['disk_mb']} MB at "
             f"~{BYTES_PER_ROW} bytes a row, ~{res['estimate']['run_minutes']} min "
             f"(this run's fetch time, plus a fifth for the writes)")
    return res


def _main(argv: list[str]) -> int:
    import argparse  # noqa: PLC0415
    from . import config, observations, secrets  # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.fred_history")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("backfill")
    g = b.add_mutually_exclusive_group(required=True)
    g.add_argument("--series")
    g.add_argument("--all", action="store_true")
    b.add_argument("--from", dest="obs_from")
    b.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    specs = list(config.FRED_PULL_SERIES)
    if a.series:
        want = {s.strip() for s in a.series.split(",") if s.strip()}
        specs = [s for s in specs if s.key in want]
        missing = want - {s.key for s in specs}
        if missing:
            print(f"not a registered FRED series: {sorted(missing)}")
            return 2
    key = secrets.get("FRED_API_KEY")
    if not key:
        print("FRED_API_KEY is not configured")
        return 2
    print(f"FRED history -- {len(specs)} series, {'DRY RUN, nothing written' if a.dry_run else 'writing'}")
    db = observations.ObservationStore()
    try:
        r = backfill(specs, _live_get(key.strip()), db=db, dry_run=a.dry_run,
                     obs_from=a.obs_from)
    finally:
        db.close()
    print(f"\n{r['rows']:,} rows {'would be ' if a.dry_run else ''}written "
          f"({r['written']:,} written); {len(r['refused'])} refused, {len(r['failed'])} failed")
    return 1 if r["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
