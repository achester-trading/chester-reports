"""
Signal-triage Batch 15, item 77 (written as 70; ST-R6.77a): the weekly cyber-
pressure line -- two public feeds, their dual percentiles and a joint flag.
Report only.

    python -m altdata.cyber_pressure weekly [--dry-run] [--force]   # Saturdays
    python -m altdata.cyber_pressure backfill [--dry-run]           # the operator's
    python -m altdata.cyber_pressure show [--as-of D]

THE TWO FEEDS (the source checks of 23 Oct 2026, docs/briefs/b56-batch15-2-notes.md):
  cyber.kev_added_week    CISA's Known Exploited Vulnerabilities catalogue, the
                          entries ADDED in the ISO week (Monday to Sunday) by their
                          `dateAdded`. One public JSON file holds the whole
                          catalogue from 3 Nov 2021; no key; robots.txt allows the
                          feeds path; a US government work. The catalogue's first
                          day (287 entries at launch) is its seeding, not a week's
                          pressure: the first week is stored and left out of the
                          percentiles (config `kev_exclude_before`).
  cyber.nvd_critical_week NVD's CVE API 2.0, the CVEs PUBLISHED in the week with a
                          CVSS v3 severity of CRITICAL (a base score of 9.0 or
                          higher), counted by `totalResults`. No key: the public
                          limit is 5 requests in a rolling 30 seconds, so the
                          reader waits 6.5 s between requests. NVD scores a new CVE
                          after its publication, so a recent week's count rises as
                          scoring catches up: each run re-reads the last 8 weeks,
                          each a new vintage at the pull instant, and the line
                          labels the newest weeks provisional.

Observed_at is the week's Monday; only complete weeks are written. KEV's rows are
`reconstructed` (the catalogue dates each entry; the week is complete at its
Sunday's end); NVD's are the pull instant (`ingest_instant`).

THE FLAG: both weeks' counts at or above the 95th percentile of their own five-
year history in the same week. It is a report-only line for the tail register's
cyber family (the Twenty-Five's scenario 13) and item 16, never a tripwire:
scenario 13 keeps its documented no-tripwire ruling, because settlement can stop
before any of this moves.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
import time
from pathlib import Path
from typing import Any, Optional

from . import st_r5_rates as rt

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / "config" / "cyber_pressure.yaml"
ROSTER = "cyber"
KEV_KEY = "cyber.kev_added_week"
NVD_KEY = "cyber.nvd_critical_week"
ROSTER_KEYS = [KEV_KEY, NVD_KEY]
KEV_SOURCE, NVD_SOURCE = "cisa_kev", "nvd"


def config(path: Optional[Path] = None) -> dict:
    import yaml                                                 # noqa: PLC0415
    return yaml.safe_load(Path(path or CONFIG).read_text(encoding="utf-8")) or {}


def monday(day: dt.date) -> dt.date:
    return day - dt.timedelta(days=day.weekday())


def complete_weeks_before(today: dt.date) -> dt.date:
    """The Monday of the newest complete week (the week before this one)."""
    return monday(today) - dt.timedelta(days=7)


# ---------------------------------------------------------------------------
# KEV
# ---------------------------------------------------------------------------
def kev_weekly(catalogue: dict, today: dt.date) -> dict[str, int]:
    """{Monday: entries added that week} for every complete week from the first
    entry's week, zeros included."""
    days = []
    for v in catalogue.get("vulnerabilities") or []:
        try:
            days.append(dt.date.fromisoformat(str(v.get("dateAdded"))[:10]))
        except ValueError:
            continue
    if not days:
        return {}
    last = complete_weeks_before(today)
    out: dict[str, int] = {}
    w = monday(min(days))
    while w <= last:
        out[w.isoformat()] = 0
        w += dt.timedelta(days=7)
    for d in days:
        k = monday(d).isoformat()
        if k in out:
            out[k] += 1
    return out


def kev_rows(weekly: dict[str, int]) -> list[dict]:
    from . import observations, session                         # noqa: PLC0415
    out = []
    for wk, n in sorted(weekly.items()):
        end = dt.datetime.combine(dt.date.fromisoformat(wk) + dt.timedelta(days=6),
                                  dt.time(23, 59), tzinfo=session._eastern_tz())  # noqa: SLF001
        out.append({"registry_key": KEV_KEY, "instrument": None, "observed_at": wk,
                    "available_at": observations.canonical_instant(
                        end.astimezone(dt.timezone.utc).isoformat()),
                    "value": n, "source": KEV_SOURCE,
                    "availability_kind": "reconstructed"})
    return out


# ---------------------------------------------------------------------------
# NVD
# ---------------------------------------------------------------------------
def nvd_params(week: str, cfg: dict, per_page: int = 1, start: int = 0) -> dict:
    a = dt.date.fromisoformat(week)
    b = a + dt.timedelta(days=7)
    return {"pubStartDate": f"{a}T00:00:00.000", "pubEndDate": f"{b}T00:00:00.000",
            cfg["nvd"]["severity_param"]: cfg["nvd"]["severity"],
            "resultsPerPage": per_page, "startIndex": start}


def nvd_rows(counts: dict[str, int], at: str) -> list[dict]:
    return [{"registry_key": NVD_KEY, "instrument": None, "observed_at": wk,
             "available_at": at, "value": int(n), "source": NVD_SOURCE,
             "availability_kind": "ingest_instant"} for wk, n in sorted(counts.items())]


def bin_published(vulns: list[dict]) -> dict[str, int]:
    """Count CVEs by the Monday of their publication week (for the backfill)."""
    out: dict[str, int] = {}
    for v in vulns:
        p = str((v.get("cve") or {}).get("published") or "")[:10]
        try:
            k = monday(dt.date.fromisoformat(p)).isoformat()
        except ValueError:
            continue
        out[k] = out.get(k, 0) + 1
    return out


# ---------------------------------------------------------------------------
# The steps
# ---------------------------------------------------------------------------
def _get(url: str, params: Optional[dict] = None) -> dict:
    from .sources._base import http_get_bytes                   # noqa: PLC0415
    return json.loads(http_get_bytes(url, params=params, timeout=90))


def weekly(dry_run: bool = False, today: Optional[str] = None, force: bool = False,
           record: bool = True, cfg: Optional[dict] = None, fetch=None,
           sleep=time.sleep, db=None) -> dict:
    """The Saturday step of the crypto basket's run (no new timer): KEV's whole
    catalogue, NVD's last `nvd.reread_weeks` complete weeks."""
    from . import observations, session                         # noqa: PLC0415
    cfg = cfg or config()
    fetch = fetch or _get
    day = dt.date.fromisoformat((today or session.session_date())[:10])
    if day.weekday() != int(cfg.get("run_weekday", 5)) and not force:
        return {"step": "weekly", "skipped": f"{day:%a} {day}: the cyber feeds read on "
                                            f"Saturdays"}
    at = session.utc_iso(timespec="microseconds")
    out: dict[str, Any] = {"step": "weekly", "dry_run": dry_run, "failed": {}}
    rows: list[dict] = []
    try:
        rows += kev_rows(kev_weekly(fetch(cfg["kev"]["url"]), day))
    except Exception as exc:                                    # noqa: BLE001
        out["failed"][KEV_KEY] = f"cisa_kev: {type(exc).__name__}: {str(exc)[:120]}"
    last = complete_weeks_before(day)
    weeks = [(last - dt.timedelta(days=7 * i)).isoformat()
             for i in range(int(cfg["nvd"]["reread_weeks"]))]
    counts: dict[str, int] = {}
    try:
        for i, wk in enumerate(sorted(weeks)):
            if i:
                sleep(float(cfg["nvd"]["pause_seconds"]))
            counts[wk] = int(fetch(cfg["nvd"]["url"], nvd_params(wk, cfg))["totalResults"])
        rows += nvd_rows(counts, at)
    except Exception as exc:                                    # noqa: BLE001
        out["failed"][NVD_KEY] = f"nvd: {type(exc).__name__}: {str(exc)[:120]}"
    out["rows"] = len(rows)
    if dry_run:
        out["preview"] = rows[-12:]
        return out
    own = db is None
    st = db or observations.open_writer(__name__)
    try:
        out["written"] = st.write_many(rows)
    finally:
        if own:
            st.close()
    if record:
        from . import feeds                                     # noqa: PLC0415
        feeds.record_attempted(ROSTER, ROSTER_KEYS, merge=True,
                               failed=out["failed"] or None)
    return out


def backfill(dry_run: bool = False, cfg: Optional[dict] = None, fetch=None,
             sleep=time.sleep, today: Optional[str] = None, db=None) -> dict:
    """NVD's history in windows of at most `nvd.backfill_window_days`, every
    critical CVE listed and binned by its publication week (the operator's, once;
    about 35 requests at the public rate)."""
    from . import observations, session                         # noqa: PLC0415
    cfg = cfg or config()
    fetch = fetch or _get
    day = dt.date.fromisoformat((today or session.session_date())[:10])
    start = dt.date.fromisoformat(cfg["nvd"]["backfill_from"])
    last = complete_weeks_before(day) + dt.timedelta(days=7)
    span = int(cfg["nvd"]["backfill_window_days"])
    per = int(cfg["nvd"]["page_size"])
    vulns: list[dict] = []
    a, n = start, 0
    while a < last:
        b = min(a + dt.timedelta(days=span), last)
        idx = 0
        while True:
            if n:
                sleep(float(cfg["nvd"]["pause_seconds"]))
            n += 1
            page = fetch(cfg["nvd"]["url"], {
                "pubStartDate": f"{a}T00:00:00.000", "pubEndDate": f"{b}T00:00:00.000",
                cfg["nvd"]["severity_param"]: cfg["nvd"]["severity"],
                "resultsPerPage": per, "startIndex": idx})
            got = page.get("vulnerabilities") or []
            vulns += got
            idx += len(got)
            if not got or idx >= int(page.get("totalResults") or 0):
                break
        a = b
    counts = bin_published(vulns)
    w, full = monday(start), {}
    while w < last:
        full[w.isoformat()] = counts.get(w.isoformat(), 0)
        w += dt.timedelta(days=7)
    rows = nvd_rows(full, session.utc_iso(timespec="microseconds"))
    if dry_run:
        return {"requests": n, "weeks": len(rows), "preview": rows[-6:]}
    own = db is None
    st = db or observations.open_writer(__name__)
    try:
        written = st.write_many(rows)
    finally:
        if own:
            st.close()
    return {"requests": n, "weeks": len(rows), "written": written}


# ---------------------------------------------------------------------------
# The read
# ---------------------------------------------------------------------------
def series_read(pts: list[tuple[str, float]], years: int, exclude_before: Optional[str]
                ) -> dict:
    use = [(d, v) for d, v in pts if not exclude_before or d >= exclude_before]
    if not use:
        return {"state": "absent"}
    lz = rt.lens(use, years)
    return {"state": "computed", "week": use[-1][0], "count": int(use[-1][1]),
            "lens": lz, "lens_text": rt.lens_text(lz)}


def read(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    years = int(cfg.get("lens_years", 5))
    kev = series_read(rt._pts(st, KEV_KEY, cutoff), years,                 # noqa: SLF001
                      cfg["kev"].get("exclude_before"))
    nvd = series_read(rt._pts(st, NVD_KEY, cutoff), years, None)           # noqa: SLF001
    return {"as_of": cutoff, "kev": kev, "nvd": nvd, "years": years,
            "flag": flag(kev, nvd, float(cfg.get("flag_pct", 95))),
            "provisional_weeks": int(cfg["nvd"]["provisional_weeks"])}


def flag(kev: dict, nvd: dict, pct: float) -> dict:
    if kev.get("state") != "computed" or nvd.get("state") != "computed":
        return {"state": "not read", "on": False}
    if kev["week"] != nvd["week"]:
        return {"state": "not read", "on": False,
                "reason": f"the two feeds' newest weeks differ ({kev['week']}, {nvd['week']})"}
    on = (kev["lens"]["percentile_window"] >= pct
          and nvd["lens"]["percentile_window"] >= pct)
    return {"state": "on" if on else "off", "on": on, "week": kev["week"], "pct": pct}


def lines(r: dict) -> list[str]:
    out = []
    k, n = r["kev"], r["nvd"]
    out.append("CISA known exploited vulnerabilities added: " +
               (f"{k['count']} in the week of {k['week']} ({k['lens_text']})."
                if k.get("state") == "computed" else
                "not read (the cyber feeds' first Saturday pull has not run)."))
    out.append("NVD critical CVEs published (CVSS v3, 9.0 or higher): " +
               (f"{n['count']} in the week of {n['week']} ({n['lens_text']}; the newest "
                f"{r['provisional_weeks']} weeks provisional while NVD scores them)."
                if n.get("state") == "computed" else
                "not read (the cyber feeds' first Saturday pull has not run)."))
    f = r["flag"]
    word = {"on": "ON", "off": "off", "not read": "not read"}[f["state"]]
    out.append(f"Cyber-pressure flag {word}"
               + (f" (both at or above their {rt.ordinal(f['pct'])} percentile in the "
                  f"week of {f['week']})" if f["state"] == "on" else
                  f": {f['reason']}" if f.get("reason") else "")
               + ". Report only: a line for the tail register's cyber family "
                 "(scenario 13) and item 16, never a tripwire.")
    return out


def incidents_line(r: dict) -> str:
    """The cross-reference the Digital Assets addendum's incidents section prints."""
    f = r["flag"]
    k, n = r["kev"], r["nvd"]
    if f["state"] == "not read":
        return ("Cyber pressure (the Weekly's tail register): not read this week.")
    return (f"Cyber pressure (the Weekly's tail register): KEV {k['count']}, NVD "
            f"critical {n['count']} in the week of {k['week']}; the flag is "
            f"{'ON' if f['on'] else 'off'}.")


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415

    from . import observations, session                         # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.cyber_pressure")
    sub = ap.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("weekly")
    w.add_argument("--dry-run", action="store_true")
    w.add_argument("--force", action="store_true")
    b = sub.add_parser("backfill")
    b.add_argument("--dry-run", action="store_true")
    s = sub.add_parser("show")
    s.add_argument("--as-of")
    a = ap.parse_args(argv)
    if a.cmd == "weekly":
        print(json.dumps(weekly(dry_run=a.dry_run, force=a.force), indent=2, default=str))
        return 0
    if a.cmd == "backfill":
        print(json.dumps(backfill(dry_run=a.dry_run), indent=2, default=str))
        return 0
    with observations.ObservationStore() as st:
        for ln in lines(read(st, a.as_of or session.utc_iso())):
            print(ln)
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
