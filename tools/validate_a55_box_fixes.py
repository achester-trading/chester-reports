"""
a55-box-fixes (session A, 20-21 Oct 2026): five defects the box evening of 20 Oct
2026 turned up.

  A  THE FRED HISTORY'S SPLIT. A fake ALFRED that counts one more vintage date in
     a real-time period than the window's list holds (as FRED did: 2001 for 2000)
     and refuses more than 2000: the old split's window would be refused; the
     fixed split's never is; the windows partition the vintages, each exactly once;
     a value unchanged across a boundary is not a new row.
  B  THE NOTES' PARAGRAPH. A 170-word draft against the 150 cap is withheld with
     its reason, never trimmed; the prompt's stated target is under the cap for
     the evening, the Sunday and the open note.
  C  THE BLS FEEDS. bls.gov is a contact host: with no contact set the feed is
     pending and no request is made; with one, the request carries it. No
     address is written in the tree.
  D  THE FOMC EVENT ROWS. The claims writer's FOMC rows (source claims_registry)
     are found by alpha.event_rates, as are the older spelling's.
  E  THE REQUIREMENTS CHECK. A requirement absent from the venv is named, one out
     of range is named with its version, a satisfied one is not; the heartbeat
     block warns and never changes the verdict or the exit code.

Round 2 (21 Oct 2026, Ari's rulings of 00:41 ET):

  F  THE FOMC HISTORY. cal.fomc_history's rows: dated, kinded, each citing the
     Board page it was read from and its statement; ascending and unique, from the
     first statement (4 Feb 1994); no notation vote; the June 2007 statement at
     its printed date; the claims writer emits one event per row.
  G  THE FOMC AUDIT, on a synthetic calendar page: a missing meeting, a changed
     date, an unreadable page (the six-month line still printed from the file),
     the six-month warning; a clean page is clean; the heartbeat runs it on the
     first of the month only and never touches the verdict or the exit code.
  H  EVENT_RATES COUNTS FOMC EVENTS from a synthetic claims file, through the
     claims writer into a scratch events table.

Synthetic fixtures only: no live store, no network, no model, no real names.
"""

from __future__ import annotations

import datetime as dt
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gate_tmp import mkdtemp                                    # noqa: E402

LINE = "=" * 78
PASS = FAIL = 0
TD = Path(mkdtemp("a55-gate-"))
LIVE_DB = REPO / "data" / "chester.db"
LIVE_DB_AT_START = LIVE_DB.exists()


def check(ok: bool, what: str) -> None:
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  PASS  {what}")
    else:
        FAIL += 1
        print(f"  FAIL  {what}")


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


# ---------------------------------------------------------------------------
class FakeAlfred:
    """FRED's observations endpoint over a synthetic vintage list. It counts the
    vintage dates in [realtime_start, realtime_end] PLUS ONE -- the vintage in
    force at the period's start, as the box's refusal showed -- and refuses more
    than 2000, as FRED does."""

    def __init__(self, vintages: list[str]):
        self.v = vintages
        self.calls: list[tuple[str, str, int]] = []

    def count(self, start: str, end: str) -> int:
        return sum(1 for d in self.v if start <= d <= end) + 1

    def __call__(self, path: str, params: dict) -> dict:
        s, e = params["realtime_start"], params["realtime_end"]
        n = self.count(s, e)
        self.calls.append((s, e, n))
        if n > 2000:
            raise RuntimeError(f"HTTP 400: There are {n} vintage dates in the specified "
                               f"real-time period: {s} to {e}. This exceeds the maximum")
        # One observation date whose value is unchanged across every window, and
        # one revised in the window holding the 3,000th vintage.
        rev = self.v[3000]
        if e < rev:
            obs = [{"date": "2005-01-03", "value": "4.0", "realtime_start": s}]
        elif s <= rev:
            obs = [{"date": "2005-01-03", "value": "4.0", "realtime_start": s},
                   {"date": "2005-01-03", "value": "4.1", "realtime_start": rev}]
        else:                                   # after the revision, as FRED serves it
            obs = [{"date": "2005-01-03", "value": "4.1", "realtime_start": s}]
        return {"observations": obs}


def group_a() -> None:
    head("A. THE FRED HISTORY'S SPLIT")
    from altdata import fred_history as fh
    d0, vint = dt.date(2005, 6, 28), []
    while len(vint) < 4500:
        if d0.weekday() < 5:
            vint.append(d0.isoformat())
        d0 += dt.timedelta(days=1)
    fake = FakeAlfred(vint)
    old = fh.windows(vint, size=fh.MAX_VINTAGES)
    check(fake.count(old[0][0], old[0][1]) == 2001,
          "the old split: a window of 2,000 vintage dates is 2,001 by FRED's count "
          "(the box's refusal reproduced)")
    check(fh.WINDOW_VINTAGES == 1900 and fh.WINDOW_VINTAGES < fh.MAX_VINTAGES,
          "the fixed split: windows of 1,900, a margin of 100 under the limit")
    rows = fh.vintage_history("FIXTURE", fake, vint)
    check(all(n <= 2000 for _, _, n in fake.calls) and len(fake.calls) == 3,
          f"no request FRED would count over 2,000 ({[n for _, _, n in fake.calls]})")
    wins = fh.windows(vint)
    covered = [d for s, e, _ in wins for d in vint if s <= d <= e]
    check(sorted(covered) == vint and len(covered) == len(set(covered)) == len(vint)
          and wins[-1][1] == fh.REALTIME_END,
          "the windows partition the vintages: every one exactly once, the last open-ended")
    check(rows == [("2005-01-03", 4.0, vint[0]), ("2005-01-03", 4.1, vint[3000])],
          "a value unchanged across a window boundary is not a new row; a revision is")


def group_b() -> None:
    head("B. THE NOTES' PARAGRAPH")
    from daily_cascade import audit_retry, note_common as nc

    class R:
        published, state, reason, model = True, "published", None, "fixture"
        text = " ".join(["word"] * 170) + "."
    saved = audit_retry.generate
    audit_retry.generate = lambda *a, **k: R()
    try:
        out = nc.prose({"blocks": []}, report="evening_note", words_cap=150, run_id="fx")
    finally:
        audit_retry.generate = saved
    check(out["state"] == "too_long" and out["text"] is None
          and out["reason"] == "the paragraph runs 170 words; the cap is 150",
          f"a 170-word draft is withheld with its reason, never trimmed ({out['reason']})")
    rules = nc.NOTE_RULES.format(words=150, target=nc.target_words(150), extra="")
    check(nc.target_words(150) == 120 and nc.target_words(250) == 200
          and nc.target_words(400) == 320 and "about 120 words" in rules
          and "150 words is a hard cap" in rules,
          "the prompt aims at 120 of 150 (the evening), 200 of 250 (the open note), "
          "320 of 400 (Sunday): each target under its cap")
    src = (REPO / "daily_cascade" / "note_common.py").read_text(encoding="utf-8")
    check("target=target_words(words_cap)" in src and "n > words_cap" in src,
          "the prose call states the target and still withholds past the cap")


def group_c() -> None:
    head("C. THE BLS FEEDS")
    from altdata.sources import edgar, news, user_agent as ua
    url = news.FEEDS["bls_cpi"]["url"]
    check(ua.is_contact_host(url) and ua.is_contact_host(news.FEEDS["bls_empsit"]["url"])
          and ua.is_contact_host("https://www.sec.gov/x")
          and not ua.is_contact_host("https://www.federalreserve.gov/feeds/press_all.xml"),
          "bls.gov joins the SEC as a contact host; other hosts keep the generic agent")
    saved = (news.FEEDS, news.http_get_bytes, edgar.contact)
    seen = []
    try:
        news.FEEDS = {"bls_cpi": dict(saved[0]["bls_cpi"])}
        news.http_get_bytes = lambda u, **k: seen.append(k.get("headers")) or b"<rss/>"
        edgar.contact = lambda: None
        _, rep = news.press_events("2026-10-20T22:00:00+00:00")
        pending = (rep["bls_cpi"]["state"] == "pending" and not seen)
        edgar.contact = lambda: "the-operator-contact"
        _, rep2 = news.press_events("2026-10-20T22:00:00+00:00")
    finally:
        news.FEEDS, news.http_get_bytes, edgar.contact = saved
    check(pending, "with no contact set: the feed is pending and no request is made")
    check(seen and seen[-1] and "the-operator-contact" in seen[-1]["User-Agent"]
          and rep2["bls_cpi"]["state"] != "failed",
          "with a contact: the request carries it in the User-Agent")
    tree = "".join((REPO / p).read_text(encoding="utf-8") for p in
                   ("altdata/sources/user_agent.py", "altdata/sources/news.py",
                    "tools/validate_a55_box_fixes.py"))
    check(not re.search(r"[\w.+-]+@[\w-]+\.[A-Za-z]{2,}", tree),
          "no address in the tree: the contact is read from .env at run time")


def group_d() -> None:
    head("D. THE FOMC EVENT ROWS")
    from altdata import events as ev_mod, events_ingest, observations
    from alpha import event_rates as er
    evs, _ = events_ingest.claims_events()
    fomc = [e for e in evs if (e.payload or {}).get("kind") == "fomc"]
    check(fomc and all(e.source == "claims_registry" and e.type == "scheduled" for e in fomc),
          f"the claims writer stores FOMC rows as scheduled, source claims_registry "
          f"({len(fomc)} meetings)")
    db = TD / "events.db"
    with ev_mod.EventStore(str(db)) as ev:
        ev.write_many([ev_mod.Event(type="scheduled", observed_at="2026-03-18T18:00:00+00:00",
                                    source="claims_registry", title="FOMC statement -- 2026-03-18",
                                    entities=["fred.fed_funds"], key="fomc-2026-03-18",
                                    payload={"kind": "fomc"}),
                       ev_mod.Event(type="scheduled", observed_at="2026-06-17T18:00:00+00:00",
                                    source="claims", title="FOMC statement -- 2026-06-17",
                                    entities=["fred.fed_funds"], key="fomc-2026-06-17",
                                    payload={"kind": "fomc"})],
                      available_at="2026-01-02T00:00:00+00:00")
    with observations.ObservationStore(str(db)) as st:
        days = er.release_days(st, {"claims_kind": "fomc"}, "2026-10-20T22:00:00+00:00")
    check([d["day"] for d in days] == ["2026-03-18", "2026-06-17"],
          "alpha.event_rates finds them: the writer's claims_registry rows and the older "
          f"spelling's ({[d['day'] for d in days]})")


def group_e() -> None:
    head("E. THE REQUIREMENTS CHECK")
    from importlib import metadata
    from altdata import requirements_check as rc
    have = {"present": "1.4.0", "oldpkg": "1.0"}

    def v(name):
        if name not in have:
            raise metadata.PackageNotFoundError(name)
        return have[name]
    r = rc.check("present>=1.0,<2  # a comment\nabsentpkg>=2.0\noldpkg>=3.0\n"
                 "winonly>=1 ; sys_platform == 'nowhere'\n", version_of=v)
    ln = rc.line(r)
    check(r["missing"] == ["absentpkg"] and r["out_of_range"] == [("oldpkg", "1.0", ">=3.0")]
          and "present" not in ln and "absentpkg" in ln and "oldpkg 1.0 (wants >=3.0)" in ln
          and rc.FIX in ln,
          f"an absent requirement is named, one out of range named with its version, a "
          f"satisfied one not ({ln})")
    ok = rc.check("present>=1.0\n", version_of=v)
    check(rc.line(ok) == "requirements: all 1 satisfied" and r["checked"] == 3,
          "all satisfied reads so; a marker that does not apply is skipped")
    sh = (REPO / "scripts" / "check_heartbeat_cron.sh").read_text(encoding="utf-8")
    blk = sh[sh.find("# ---- the venv against requirements.txt"):sh.find("# ---- 1. the distinct log line")]
    check("altdata.requirements_check" in blk and "WARNING" in blk
          and not re.search(r"^\s*exit\b|\bRC=|VERDICT=", blk, re.M)
          and ".venv/bin/pip install -r requirements.txt" in blk,
          "the heartbeat's block warns, names the fix, and never touches the verdict or "
          "the exit code")


def group_f() -> None:
    head("F. THE FOMC HISTORY")
    from altdata import claims, events_ingest
    c = claims.load(reload=True)["claims"]["cal.fomc_history"]
    rows = c["detail"]["statements"]
    ds = [str(r["date"]) for r in rows]
    check(len(rows) == 239 and ds == sorted(set(ds)) and ds[0] == "1994-02-04"
          and ds[-1] == "2025-12-10",
          f"239 statements, ascending and unique, 1994-02-04 to 2025-12-10 ({len(rows)})")
    check(all(r["kind"] in ("scheduled", "unscheduled") for r in rows)
          and sum(r["kind"] == "unscheduled" for r in rows) == 14
          and all(str(r["page"]).startswith("https://www.federalreserve.gov/monetarypolicy/fomc")
                  for r in rows)
          and all(str(r["statement"]).startswith("/") for r in rows),
          "each row carries its kind (14 unscheduled), the Board page it was read from, "
          "and its statement")
    check("2007-06-28" in ds and "2007-06-18" not in ds
          and not {"2020-03-19", "2020-03-23", "2020-03-31", "2025-08-22"} & set(ds)
          and "conference calls and meetings with no" in c["detail"]["note"].replace("\n", " ")
          and c["source_class"] == "cited",
          "the June 2007 statement at its printed date; notation votes left out; the "
          "claim says what it leaves out")
    evs, _ = events_ingest.claims_events()
    hist = [e for e in evs if (e.payload or {}).get("cited_as") == "cal.fomc_history"]
    check(len(hist) == 239 and all(e.source == "claims_registry" for e in hist)
          and {e.observed_at[:10] for e in hist} == set(ds),
          "the claims writer emits one claims_registry event per statement")


PAGE = """<h4><a id="1">2031 FOMC Meetings</a></h4>
<div class="row fomc-meeting"><div class="fomc-meeting__month"><strong>January</strong></div>
<div class="fomc-meeting__date">27-28</div>
<a href="/newsevents/pressreleases/monetary20310128a.htm">HTML</a></div>
<div class="row fomc-meeting"><div class="fomc-meeting__month"><strong>March</strong></div>
<div class="fomc-meeting__date">18-19</div></div>
<div class="row fomc-meeting"><div class="fomc-meeting__month"><strong>May</strong></div>
<div class="fomc-meeting__date">4 (notation vote)</div></div>
<h4><a id="2">2032 FOMC Meetings</a></h4>
<div class="row fomc-meeting"><div class="fomc-meeting__month"><strong>Jan/Feb</strong></div>
<div class="fomc-meeting__date">31-1</div></div>
"""


def group_g() -> None:
    head("G. THE FOMC AUDIT")
    from altdata import fomc_audit as fa
    syn = {"cal.fomc_2031": {"detail": {"decision_days": [dt.date(2031, 1, 28),
                                                          dt.date(2031, 3, 18)]}}}
    page = fa.parse_page(PAGE)
    check(sorted(page) == [2031, 2032] and len(page[2031]) == 2
          and page[2032][0]["date"] == dt.date(2032, 2, 1),
          "the page parses: a statement's own date, a meeting's last day across a "
          "month, a notation vote skipped")
    rc, lines = fa.run(dt.date(2031, 1, 1), get=lambda u: PAGE.encode(), claims=syn)
    txt = "\n".join(lines)
    check(rc == 1 and "MISSING 2032-02-01" in txt,
          "a published meeting the file lacks is named (the next year's calendar)")
    check("CHANGED the file holds 2031-03-18, the Board's calendar 2031-03-19" in txt,
          "a date that differs is named, file and page")
    check("SOON the file's last meeting is 2031-03-18, 76 days away" in txt,
          "the six-month warning prints when the file's last meeting is near")

    def boom(u):
        raise OSError("connection refused")
    rc2, l2 = fa.run(dt.date(2031, 1, 1), get=boom, claims=syn)
    check(rc2 == 2 and l2[0].startswith("fomc audit: UNREADABLE")
          and any("SOON" in x for x in l2),
          "an unreadable page is said so, and the six-month line still prints from "
          "the file alone")
    syn_ok = {"cal.fomc_2031": {"detail": {"decision_days": [
        dt.date(2031, 1, 28), dt.date(2031, 3, 19), dt.date(2032, 2, 1)]}}}
    rc3, l3 = fa.run(dt.date(2031, 1, 1), get=lambda u: PAGE.encode(), claims=syn_ok)
    check(rc3 == 0 and l3[0].startswith("fomc audit: clean"),
          f"a page the file matches, with the last meeting over six months away, is clean")
    sh = (REPO / "scripts" / "check_heartbeat_cron.sh").read_text(encoding="utf-8")
    blk = sh[sh.find("# ---- the FOMC calendar audit"):sh.find("# ---- 1. the distinct log line")]
    check("altdata.fomc_audit check" in blk and '"${FOMC_AUDIT_DAY:8:2}" != "01"' in blk
          and "WARNING" in blk and not re.search(r"^\s*exit\b|\bRC=|VERDICT=", blk, re.M),
          "the heartbeat runs it on the first of the month only, as a WARNING, never "
          "touching the verdict or the exit code")
    src = (REPO / "altdata" / "fomc_audit.py").read_text(encoding="utf-8")
    check(not re.search(r"\.write\(|write_many|INSERT|open\([^)]*['\"]w", src),
          "the audit writes no data row")


def group_h() -> None:
    head("H. EVENT_RATES COUNTS FOMC EVENTS FROM A SYNTHETIC CLAIMS FILE")
    from altdata import claims as claims_mod, events as ev_mod, events_ingest, observations
    from alpha import event_rates as er
    syn = {"version": 1, "defaults": {}, "warnings": {}, "claims": {
        "cal.fomc_history": {"value": "FOMC policy statements: fixture",
                             "detail": {"statements": [
                                 {"date": dt.date(2001, 1, 3), "kind": "unscheduled"},
                                 {"date": dt.date(2001, 1, 31), "kind": "scheduled"},
                                 {"date": dt.date(2010, 5, 9), "kind": "unscheduled"}]}},
        "cal.fomc_2030": {"value": "2030 FOMC meeting dates: Jan 29-30, Mar 19-20"}}}
    saved = claims_mod.load
    claims_mod.load = lambda *a, **k: syn
    try:
        evs, _ = events_ingest.claims_events()
    finally:
        claims_mod.load = saved
    db = TD / "fomc.db"
    with ev_mod.EventStore(str(db)) as ev:
        ev.write_many(evs, available_at="2026-10-21T12:00:00+00:00")
    with observations.ObservationStore(str(db)) as st:
        days = [d["day"] for d in er.release_days(st, {"claims_kind": "fomc"},
                                                  "2030-12-31T22:00:00+00:00")]
    check(days == ["2001-01-03", "2001-01-31", "2030-01-30", "2030-03-20"],
          f"history rows and a year's calendar both reach event_rates; a Sunday "
          f"statement is skipped by its session rule ({days})")


def main() -> int:
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g, group_h):
        try:
            g()
        except Exception as exc:                                # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    head("THE GATE RUN")
    check(LIVE_DB.exists() == LIVE_DB_AT_START, "this gate run created no data/chester.db")
    print(f"\n{PASS} passed, {FAIL} failed")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
