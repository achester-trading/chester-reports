#!/usr/bin/env python3
"""
The FRED history writer's gate (AUD-3d). A code gate: a fake ALFRED answers in
FRED's documented shapes (series/vintagedates, series/observations with
realtime_start/realtime_end, clipped to the requested real-time window, paged by
limit and offset), and every row lands in a temporary observation store. It never
fetches, never reads the live store and never calls a model.

  A. A revised series, as of three instants: before its first publication
     nothing; between the publication and the revision the first value; after
     the revision the revised one. No row is available before its publication.
  B. Release times: a series with one is stamped at it (ET); one without, at the
     end of the day ET -- never earlier.
  C. A never-revised series without vintages reconstructs; a revisable series
     without vintages is refused, listed, and gets nothing.
  D. Paging: vintage dates over the per-request cap and observations over a page
     are fetched in pieces, and a window boundary invents no vintage.
  E. The rows: source fred:backfill, its own run, kind observed; a re-run writes
     nothing; a value already stored earlier is not written again; a value stored
     only LATER (a live pull) does not block the truer earlier vintage.
  F. The dry run writes nothing; --all adds the estimate; ICE BofA is a note.
  G. Nothing fetches.
"""

from __future__ import annotations

import sys
from collections import namedtuple
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gate_tmp import mkdtemp  # noqa: E402

from altdata import fred_history as fh  # noqa: E402
from altdata import observations  # noqa: E402

TMP = Path(mkdtemp("gate_fredhist_"))
LINE = "=" * 78
PASSED = FAILED = 0
Spec = namedtuple("Spec", "key fred_id")
END = "9999-12-31"


def ok(m: str) -> None:
    global PASSED
    PASSED += 1
    print(f"  PASS  {m}")


def bad(m: str) -> None:
    global FAILED
    FAILED += 1
    print(f"  FAIL  {m}")


def check(c: bool, m: str) -> None:
    (ok if c else bad)(m)


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


# The fake ALFRED's data: series id -> [(date, value, realtime_start, realtime_end)]
SERIES = {
    "REV1": [("2020-01-01", "100", "2020-02-07", "2020-03-05"),
             ("2020-01-01", "105", "2020-03-06", END),
             ("2020-02-01", "200", "2020-03-06", "2020-04-02"),
             ("2020-02-01", "203", "2020-04-03", END),
             ("2020-03-01", ".", "2020-04-03", END)],
    "REV2": [("2021-06-01", "7.5", "2021-07-15", END)],
    "NEV1": [("2024-03-01", "4.25", "2024-03-04", END),
             ("2024-03-04", "4.30", "2024-03-05", END)],
    "NOV1": [("2024-03-01", "1.0", "2024-03-04", END)],
    "BAMLX": [("2023-10-16", "3.10", "2023-10-17", END)],
}
VINTAGES = {"REV1": ["2020-02-07", "2020-03-06", "2020-04-03"], "REV2": ["2021-07-15"],
            "BAMLX": ["2023-10-17"]}
POLICY = {"fred.nev1": "never", "fred.nov1": "revised"}


class FakeAlfred:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def __call__(self, path: str, p: dict) -> dict:
        self.calls.append((path, dict(p)))
        sid = p["series_id"]
        if path == "series/vintagedates":
            if sid not in VINTAGES:
                raise RuntimeError("HTTP 400 from api.stlouisfed.org: series not in ALFRED")
            v = VINTAGES[sid]
            return {"vintage_dates": v[p["offset"]:p["offset"] + p["limit"]]}
        rs, re_ = p["realtime_start"], p["realtime_end"]
        rows = []
        for d, v, a, b in SERIES[sid]:
            if a <= re_ and b >= rs and d >= p.get("observation_start", ""):
                rows.append({"date": d, "value": v, "realtime_start": max(a, rs),
                             "realtime_end": min(b, re_)})
        rows.sort(key=lambda r: (r["date"], r["realtime_start"]))
        return {"observations": rows[p["offset"]:p["offset"] + p["limit"]]}


def store(name: str) -> observations.ObservationStore:
    return observations.ObservationStore(str(TMP / f"{name}.sqlite"))


def run(specs, db, **kw):
    lines: list[str] = []
    r = fh.backfill(specs, kw.pop("get", FakeAlfred()), db=db,
                    policy_of=lambda m: POLICY.get(m, "revised"),
                    times=kw.pop("times", {"rev1": "08:30"}), run_id=kw.pop("run_id", "fh:gate"),
                    echo=lines.append, **kw)
    return r, lines


def val(db, key, cutoff, period):
    rows = [r for r in db.as_of(f"fred.{key}", cutoff) if r["observed_at"][:10] == period]
    return rows[-1]["value_num"] if rows else None


def group_a() -> None:
    head("A. A REVISED SERIES, AS OF THREE INSTANTS")
    db = store("a")
    run([Spec("rev1", "REV1")], db)
    # 7 Feb 2020 08:30 ET is 13:30 UTC (EST); 3 Apr 2020 08:30 ET is 12:30 UTC (EDT)
    check(val(db, "rev1", "2020-02-07T13:29:59+00:00", "2020-01-01") is None,
          "before the first publication (7 Feb 2020 08:30 ET) the period is invisible")
    check(val(db, "rev1", "2020-02-07T13:30:00+00:00", "2020-01-01") == 100.0
          and val(db, "rev1", "2020-03-06T13:29:59+00:00", "2020-01-01") == 100.0,
          "from the publication to the revision it reads the first value (100)")
    check(val(db, "rev1", "2020-03-06T13:30:00+00:00", "2020-01-01") == 105.0,
          "after the revision (6 Mar 2020 08:30 ET) it reads the revised value (105)")
    check(val(db, "rev1", "2020-03-06T13:29:00+00:00", "2020-02-01") is None
          and val(db, "rev1", "2020-03-06T13:30:00+00:00", "2020-02-01") == 200.0
          and val(db, "rev1", "2020-04-03T12:30:00+00:00", "2020-02-01") == 203.0,
          "February's print: unseen, then 200, then 203 from 3 Apr 08:30 EDT")
    rows = db.all_vintages("fred.rev1")
    first: dict[str, str] = {}
    for d, v, a, _b in SERIES["REV1"]:
        if v != ".":
            t = fh.published_at(a, "08:30")
            first[d] = min(first.get(d, t), t)
    check(len(rows) == 4 and all(r["available_at"] >= first[r["observed_at"][:10]]
                                 for r in rows),
          f"4 vintages written, a revised value its own row; none available before "
          f"its period's first publication")
    check(not any(r["observed_at"][:10] == "2020-03-01" for r in rows),
          "FRED's '.' (no value) writes nothing")


def group_b() -> None:
    head("B. RELEASE TIMES")
    db = store("b")
    run([Spec("rev2", "REV2")], db, times={})
    r = db.all_vintages("fred.rev2")[0]
    check(r["available_at"].startswith("2021-07-16T03:59:59.999999"),
          f"no release time held: the end of the vintage's day ET ({r['available_at']})")
    check(fh.published_at("2021-07-15", "08:30").startswith("2021-07-15T12:30:00"),
          "a release time held: its ET time on the vintage date (08:30 EDT = 12:30 UTC)")
    mp = TMP / "release_map.json"
    mp.write_text('{"rev1": {"release_id": 50, "release_name": "Employment Situation"}, '
                  '"rev2": {"release_id": 9, "release_name": "Some Unlisted Release"}}',
                  encoding="utf-8")
    t = fh.release_times(mp)
    check(t == {"rev1": "08:30"}, f"the release map and the calendar give the time: {t}")
    check(fh.release_times(TMP / "absent.json") == {},
          "with no release map on disk every series falls to the end of day")


def group_c() -> None:
    head("C. RECONSTRUCTED WHERE PERMITTED; REFUSED WHERE REVISABLE")
    db = store("c")
    r, lines = run([Spec("nev1", "NEV1"), Spec("nov1", "NOV1")], db)
    rows = db.all_vintages("fred.nev1")
    check(len(rows) == 2 and all(x["availability_kind"] == "reconstructed" for x in rows)
          and rows[0]["available_at"] >= fh.reconstructed_at("2024-03-01"),
          "a never-revised series without vintages reconstructs: the observation plus "
          f"{fh.RECONSTRUCTED_LATENCY_BUSINESS_DAYS} business day, end of day ET")
    check(fh.reconstructed_at("2024-03-01").startswith("2024-03-05T04:59:59")
          and val(db, "nev1", "2024-03-04T12:00:00+00:00", "2024-03-01") is None,
          "Friday 1 Mar reconstructs to the end of Monday 4 Mar ET, and is unseen before")
    check(db.all_vintages("fred.nov1") == [] and r["refused"]
          and r["refused"][0][0] == "nov1" and any("refused" in ln for ln in lines),
          f"a revisable series without vintages is refused and listed: {r['refused'][0][1]}")


def group_d() -> None:
    head("D. PAGING, AND NO VINTAGE INVENTED AT A WINDOW'S EDGE")
    saved = (fh.MAX_VINTAGES, fh.OBS_PAGE, fh.VINTAGE_PAGE)
    fh.MAX_VINTAGES, fh.OBS_PAGE, fh.VINTAGE_PAGE = 2, 2, 2
    try:
        get = FakeAlfred()
        db = store("d")
        run([Spec("rev1", "REV1")], db, get=get)
    finally:
        fh.MAX_VINTAGES, fh.OBS_PAGE, fh.VINTAGE_PAGE = saved
    vd = [c for c in get.calls if c[0] == "series/vintagedates"]
    ob = [c for c in get.calls if c[0] == "series/observations"]
    wins = sorted({(c[1]["realtime_start"], c[1]["realtime_end"]) for c in ob})
    check(len(vd) == 2 and len(wins) == 2 and wins[0] == ("2020-02-07", "2020-04-02")
          and wins[1] == ("2020-04-03", END) and len(ob) > len(wins),
          f"vintage dates in pages ({len(vd)} requests); observations over at most two "
          f"vintage dates a request ({wins}), each paged ({len(ob)} requests)")
    check(len(db.all_vintages("fred.rev1")) == 4,
          "the period carried across the window edge (clipped to 3 Apr) is not a new "
          "vintage: still 4 rows")


def group_e() -> None:
    head("E. THE ROWS")
    db = store("e")
    r1, _ = run([Spec("rev1", "REV1")], db, run_id="fh:first")
    rows = db.all_vintages("fred.rev1")
    check(all(x["source"] == "fred:backfill" and x["run_id"] == "fh:first"
              and x["availability_kind"] == "observed" for x in rows),
          "source fred:backfill, its own run, availability_kind observed")
    r2, _ = run([Spec("rev1", "REV1")], db, run_id="fh:second")
    check(r2["written"] == 0 and len(db.all_vintages("fred.rev1")) == 4,
          "a re-run writes nothing: existing rows are never rewritten")
    db2 = store("e2")
    db2.write_many([
        {"registry_key": "fred.rev1", "instrument": None, "observed_at": "2020-01-01",
         "available_at": "2026-10-01T20:00:00+00:00", "value": 105.0, "source": "fred",
         "availability_kind": "ingest_instant"},
        {"registry_key": "fred.rev1", "instrument": None, "observed_at": "2020-02-01",
         "available_at": "2020-03-01T00:00:00+00:00", "value": 200.0, "source": "fred",
         "availability_kind": "observed"}])
    r3, _ = run([Spec("rev1", "REV1")], db2, run_id="fh:third")
    back = [(x["observed_at"][:10], x["value_num"], x["source"])
            for x in db2.all_vintages("fred.rev1")]
    check(("2020-01-01", 105.0, "fred:backfill") in back
          and ("2020-02-01", 200.0, "fred:backfill") not in back and r3["written"] == 3,
          "a value stored earlier is not written again (Feb's 200); one stored only "
          "later by a live pull (Jan's 105) still gets its truer, earlier vintage")
    check(val(db2, "rev1", "2026-10-02T00:00:00+00:00", "2020-01-01") == 105.0,
          "and today's read is unchanged")


def group_f() -> None:
    head("F. THE DRY RUN, THE ESTIMATE, ICE BOFA")
    db = store("f")
    r, lines = run([Spec("rev1", "REV1"), Spec("hy_oas", "BAMLX"), Spec("nov1", "NOV1")],
                   db, dry_run=True)
    check(r["written"] == 0 and db.all_vintages("fred.rev1") == [] and r["rows"] == 5,
          f"--dry-run writes nothing ({r['rows']} rows planned)")
    s = {x["key"]: x for x in r["series"]}
    check(s["rev1"]["vintages"] == 3 and s["rev1"]["earliest_observation"] == "2020-01-01"
          and s["rev1"]["earliest_available"].startswith("2020-02-07T13:30"),
          "per series: vintages, rows, the earliest observation and earliest availability")
    check("estimate" in r and r["estimate"]["rows"] == 5 and "disk_mb" in r["estimate"]
          and any("estimate:" in ln for ln in lines),
          f"over several series it adds an estimate of rows, disk and run time "
          f"({r['estimate']})")
    check("three years" in (s["hy_oas"]["note"] or "") and s["hy_oas"]["status"] == "observed"
          and ("hy_oas", s["hy_oas"]["note"]) not in r["failed"],
          "ICE BofA: the dry run says FRED keeps about three years, as a note, not a failure")


def group_g() -> None:
    head("G. NOTHING FETCHES")
    from altdata.sources import _base  # noqa: PLC0415
    saved = (_base.http_get_json, fh._live_get)

    def boom(*a, **k):
        raise AssertionError("the gate fetched")
    _base.http_get_json = boom
    fh._live_get = boom
    try:
        r, _ = run([Spec("rev1", "REV1")], store("g"))
        ok("a full backfill ran against the fake with the network paths disabled")
    except AssertionError:
        bad("the backfill reached the network")
    finally:
        _base.http_get_json, fh._live_get = saved
    src = (REPO / "altdata" / "fred_history.py").read_text(encoding="utf-8")
    check("secrets.get(\"FRED_API_KEY\")" in src and "print(key" not in src,
          "the key is read through altdata.secrets and never printed")


def main() -> int:
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g):
        g()
    print(f"\n{PASSED} passed, {FAILED} failed")
    print(LINE)
    print("VALIDATION PASSED" if not FAILED else "VALIDATION FAILED")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
