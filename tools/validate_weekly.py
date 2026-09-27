#!/usr/bin/env python3
"""
Validation gate for the Weekly Tactical. (Phase 4a)

    python tools/validate_weekly.py

Five groups, and the third is the one the phase turns on:

  A. PAYLOAD COMPLETENESS. Every declared block is present, and each is either
     `ok`/`empty`/`not_yet_sourced` or absent WITH A REASON. A block that went
     missing would be invisible in a document that renders what it is given.

  B. RENDER. Data only -- the same forbidden-import scan the close report's
     modules get -- and the document's headings are the payload's blocks in the
     payload's order. A renderer with its own order would make the document and
     the payload two different accounts of the week.

  C. THE GRADES MOVE. The close report no longer renders the block, and the
     weekly does. This is the assertion that makes the move real rather than a
     duplication: two documents answering one question drift, and the first to
     drift is the one nobody is reading for it.

  D. REPLAY. A past week rebuilds from the store byte-identically. The weekly
     computes nothing, so a rebuild must agree with itself -- and this is what
     makes "read the object, never recompute" checkable rather than asserted.

  E. THE UNIT AND THE WRAPPER. Sunday 05:00 ET, zone-pinned, Persistent=true with
     its reason, not in DEPLOY_TIMERS (so no deploy can enable it), and the
     heartbeat check dormant until the timer is.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

from daily_cascade import weekly_payload as wp                 # noqa: E402
from daily_cascade import weekly_render as wr                  # noqa: E402
from daily_cascade import weekly_report as wrep                # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LINE = "=" * 78
PASS = 0
FAIL = 0
SKIPPED: list[str] = []

# The week the test edition is built for. A PAST week with objects in the store,
# so the gate exercises a real replay rather than whatever today happens to be.
TEST_WEEK = "2026-09-18"

# Nothing in a payload or render module may reach a model or a network. The same
# list validate_daily_close.py applies to the close report's modules.
FORBIDDEN = ("anthropic", "openai", "requests", "urllib.request", "httpx",
             "socket")


def ok(msg: str) -> None:
    global PASS
    PASS += 1
    print(f"  PASS  {msg}")


def bad(msg: str) -> None:
    global FAIL
    FAIL += 1
    print(f"  FAIL  {msg}")


def check(cond: bool, msg: str) -> bool:
    (ok if cond else bad)(msg)
    return bool(cond)


def group_a(p: dict) -> None:
    print(f"\n{LINE}\nA. PAYLOAD COMPLETENESS\n{LINE}")
    check(list(p.get("blocks") or []) == list(wp.BLOCKS),
          f"the payload declares its blocks, in order ({list(wp.BLOCKS)})")
    for name in wp.BLOCKS:
        b = p.get(name)
        if not check(isinstance(b, dict), f"{name} is present"):
            continue
        state = b.get("state")
        if state in ("ok", "empty", "not_yet_sourced"):
            ok(f"{name}: {state}")
        else:
            check(bool(b.get("reason")),
                  f"{name}: {state} AND carries a reason "
                  f"({str(b.get('reason'))[:60]})")
    check(p.get("week_ending") and p.get("previous_week_ending"),
          f"the week is named by its Friday ({p.get('week_ending')}) and so is "
          f"the week it is compared against ({p.get('previous_week_ending')})")
    check(len(p.get("sessions_in_week") or []) in (4, 5),
          f"a week is four or five sessions "
          f"({len(p.get('sessions_in_week') or [])}) -- four on a holiday week")

    # THE WEEK IS FRIDAY AGAINST FRIDAY, not five daily diffs added up.
    check(wp.week_ending("2026-09-20") == "2026-09-18",
          "a Sunday resolves to the Friday just past")
    check(wp.previous_week_ending("2026-09-18") == "2026-09-11",
          "and the comparison week is the Friday before that")
    st = p.get("week_in_state") or {}
    if st.get("state") == "ok":
        check("exceptions_intraweek_only" in st,
              "the week reports exceptions that OPENED AND CLOSED INSIDE it -- "
              "neither endpoint would show them, and 'it moved twice and came "
              "back' is a different week from 'nothing happened'")
        ag = (st.get("vol_term_structure") or {}).get("week_agreement") or {}
        check(set(ag) == {"agreed", "disagreed", "not_comparable"},
              f"and the vol dial's two legs are counted for the week ({ag}) -- the "
              f"dual run's question is a count of disagreeing sessions")
        check(sum(ag.values()) <= len(p.get("sessions_in_week") or []),
              "with the counts bounded by the week's sessions")


def group_b(p: dict) -> None:
    print(f"\n{LINE}\nB. RENDER: DATA ONLY, AND THE PAYLOAD'S ORDER\n{LINE}")
    for mod in ("weekly_payload.py", "weekly_render.py"):
        src = (REPO / "daily_cascade" / mod).read_text(encoding="utf-8")
        # urllib is reached by the FRED release calendar in the payload, which is
        # a declared read of a calendar and not a model call. The render must have
        # nothing at all.
        banned = FORBIDDEN if mod == "weekly_render.py" else (
            "anthropic", "openai", "httpx")
        hits = [f for f in banned if re.search(rf"\b{re.escape(f)}\b", src)]
        check(not hits, f"{mod} imports no model client{'' if not hits else f' -- {hits}'}")
    html = wr.render(p, {"archive_path": "x"}, narrative=None)
    titles = ["The week in state", "Grades", "Register", "The week ahead",
              "Weekend developments"]
    positions = [html.find(t) for t in titles]
    check(all(x > 0 for x in positions),
          f"every block has a heading in the document ({titles})")
    check(positions == sorted(positions),
          "and they appear in the payload's order, so the document and the "
          "payload are one account of the week")
    check("weekly_tactical" in html or "Weekly Tactical" in html,
          "the document names itself")
    txt = wr.text_fallback(p)
    check("Weekly Tactical" in txt and str(p.get("week_ending")) in txt,
          "and the text fallback names the report and the week")


def group_c(p: dict) -> None:
    print(f"\n{LINE}\nC. THE GRADES MOVE\n{LINE}")
    close = (REPO / "daily_cascade" / "render.py").read_text(encoding="utf-8")
    check("{grades_line(payload)}" in close,
          "the close report's document calls grades_line()")
    check("{grades_block_full(payload)}" not in close
          and "{grades_block(payload)}" not in close,
          "and no longer renders the block -- two documents answering one "
          "question drift, and the first to drift is the one nobody is reading "
          "for it")
    check("see Sunday" in close,
          "the close's one line points at the anchor that carries the loop")
    gr = p.get("grades") or {}
    check("cuts" in gr or gr.get("state") == "empty",
          f"and the weekly carries the cuts ({gr.get('state')})")
    if gr.get("state") == "ok":
        cuts = gr.get("cuts") or {}
        for key in ("by_owning_report", "by_book", "by_mechanism_group",
                    "by_regime_spy_gamma"):
            check(key in cuts, f"including the {key} cut")
    else:
        SKIPPED.append(f"cuts not exercised: grades are {gr.get('state')}")
        print(f"  SKIP  the four cuts: grades are {gr.get('state')} on this store")
    check("brier" in gr,
          "and the Brier ledger, whether or not a probability has been emitted")


def group_d() -> None:
    print(f"\n{LINE}\nD. REPLAY: A PAST WEEK REBUILDS IDENTICALLY\n{LINE}")

    STAMPS = ("generated_at", "as_of", "run_id")

    def strip(d):
        """Drop the stamps AT EVERY DEPTH, then compare.

        It used to drop them at the top level only, which was enough until a block
        recorded its own cutoff -- the events block does, because it can be built
        standalone and a block without its own as_of is a block whose replay nobody
        can reproduce. A stamp nested one level down is the same provenance as a
        stamp at the top, and comparing it would make this gate fail on the clock
        rather than on the content. regime.py's REPLAY_EXCLUDE draws the same line.
        """
        if isinstance(d, dict):
            return {k: strip(v) for k, v in d.items() if k not in STAMPS}
        if isinstance(d, list):
            return [strip(v) for v in d]
        return d

    def dump(d: dict) -> str:
        return json.dumps(strip(d), sort_keys=True, default=str)

    a = wp.build(TEST_WEEK, fetch=False)
    b = wp.build(TEST_WEEK, fetch=False)
    check(dump(a) == dump(b),
          f"two builds of the week ending {TEST_WEEK} agree byte for byte "
          f"({len(strip(a))} chars) -- the weekly computes nothing, so a rebuild "
          f"must agree with itself")
    check(a.get("generated_at") != b.get("generated_at")
          or a.get("as_of") != b.get("as_of"),
          "and the two runs DID have different stamps, so the comparison is not "
          "vacuously true")
    check(a.get("week_ending") == TEST_WEEK,
          f"the replayed week is the one asked for ({a.get('week_ending')})")
    np_ = wp.narrative_payload(a)
    from daily_cascade import precision as pr
    v = pr.violations(np_)
    check(not v,
          f"and the narrative payload conforms to print precision"
          + (f" -- {[x['path'] for x in v][:4]}" if v else ""))


def group_e() -> None:
    print(f"\n{LINE}\nE. THE UNIT, THE WRAPPER AND THE HEARTBEAT\n{LINE}")
    units = REPO / "deploy" / "systemd"
    t = (units / "chester-weekly.timer").read_text(encoding="utf-8")
    s = (units / "chester-weekly.service").read_text(encoding="utf-8")
    check("OnCalendar=Sun 05:00 America/New_York" in t,
          "the timer fires Sunday 05:00 ET, zone-pinned")
    check("Persistent=true" in t,
          "Persistent=true -- a weekly that arrives Sunday afternoon is still the "
          "anchor for a week that has not started, unlike a session report")
    check("SuccessExitStatus=0 2 3" in s,
          "the service treats archived-but-not-sent and dry-run as successful "
          "runs, and 'no payload' as red")
    check("run_weekly.sh" in s, "and runs the wrapper")

    mk = (REPO / "Makefile").read_text(encoding="utf-8")
    m = re.search(r"DEPLOY_TIMERS\s*[:?]?=\s*((?:.*\\\n)*.*)", mk)
    timers = m.group(1) if m else ""
    check("chester-weekly.timer" not in timers,
          "chester-weekly.timer is NOT in DEPLOY_TIMERS, so no deploy can enable "
          "it -- the enable is a human act, printed and not taken")
    check("tools/validate_weekly.py" in mk,
          "and this gate is in the Makefile's validator list, which CI reads")

    w = (REPO / "scripts" / "run_weekly.sh").read_text(encoding="utf-8")
    check("CHESTER_STATE_DIR" in w and "is unset" in w,
          "the wrapper refuses to guess a state directory")
    check("weekly_heartbeat" in w,
          "and writes a heartbeat, because a missed Sunday is otherwise invisible "
          "for a week")
    check("RC\" -eq 0 || \"$RC\" -eq 2 || \"$RC\" -eq 3" in w
          or "-eq 0 || " in w,
          "written only on a run that produced a report -- a no-payload run must "
          "not let a broken week look current")
    # NOT INVOKED, rather than not mentioned: the wrapper's own header explains at
    # length why there is no guard, and a gate that banned the word would ban the
    # explanation. What must be absent is the CALL.
    called = [ln for ln in w.splitlines()
              if "is-session" in ln and not ln.lstrip().startswith("#")]
    check(not called,
          "and there is NO calendar guard invoked: the weekly runs on a day the "
          "market is shut on purpose, and week_ending() resolves a holiday Friday "
          "itself" + (f" -- found {called}" if called else ""))

    hb = (REPO / "scripts" / "check_heartbeat_cron.sh").read_text(encoding="utf-8")
    # THE CHECK IS A LOOP OVER A DECLARED TABLE now that the Monthly joined it, so
    # the assertion is on the table and the gate rather than on a literal command:
    # two copies of a staleness rule would be two places for it to drift.
    check('is-enabled "$unit"' in hb and "ANCHOR_TABLE" in hb,
          "the heartbeat gates its anchors on the timer being ENABLED, from one "
          "declared table -- an alarm red for a week before it means anything is an "
          "alarm that gets muted")
    check("chester-weekly.timer:weekly_heartbeat" in hb,
          "and the weekly is in that table with its heartbeat file")
    check("WEEKLY_STATE=not_enabled" in hb,
          "and reports not_enabled until then")
    check("weekly=$WEEKLY_STATE" in hb,
          "with the state on the verdict line")
    # It must not be able to change the verdict.
    seg = hb[hb.find("WEEKLY_STATE=not_enabled"):]
    # UP TO WHICHEVER BLOCK COMES NEXT. This used to cut at the claims registry
    # marker, which stopped being the next block when the events ingest landed
    # between them -- and the assertion then read the events block's own exit
    # handling as the weekly's. A slice that names one successor is a slice that
    # breaks the next time something is inserted.
    ends = [i for i in (seg.find("# ---- the events ingest"),
                        seg.find("# ---- the claims registry")) if i > 0]
    seg = seg[:min(ends)] if ends else seg
    check("RC=" not in seg and "STATE=feed" not in seg,
          "and it changes no exit code: a weekly that has not run is a report to "
          "re-run by hand, not a capture that was lost")

    check(wrep.TEMPLATE_PATH.exists(),
          f"the weekly template is committed ({wrep.TEMPLATE_PATH.name})")
    tpl = wrep.TEMPLATE_PATH.read_text(encoding="utf-8")
    check("Reference paragraph" in tpl, "with a reference paragraph")
    sp = wrep.weekly_system_prompt()
    check("LENGTH IS WHATEVER THE WEEK NEEDS" in sp,
          "the brief permits long form and states no word count")
    for word in ("word count", "paragraph count"):
        check(f"No {word}" in sp or f"no {word}" in sp,
              f"and says so explicitly ('{word}')")
    check("NO RECOMMENDATION" in sp,
          "while the no-recommendation rule is unchanged")
    check("numeral audit" in sp.lower() or "audit" in sp.lower(),
          "and the audit still gates it")


def _obj(day: str, method: Optional[str], liq: Optional[str]) -> dict:
    return {"object": "market_state", "session": day, "method_version": method,
            "config_version": "fixture", "as_of": f"{day}T20:45:00+00:00",
            "computed_at": f"{day}T20:46:00+00:00",
            "dimensions": {"liquidity": {"state": liq,
                                         "last_changed": "2026-09-24"}},
            "dials": {}, "contradictions": []}


def group_f() -> None:
    """Method-caused changes print as such (Weekly edition 1, item 2)."""
    print(f"\n{LINE}\nF. A METHOD-CAUSED CHANGE IS NOT DATED AS A MARKET MOVE\n{LINE}")
    import tempfile
    import regime
    from altdata import observations
    from daily_cascade import state_block
    with tempfile.TemporaryDirectory() as td:
        st = observations.ObservationStore(str(Path(td) / "m.db"))
        try:
            # As first published: 23 Sep under method-5 (ample), 24 Sep under
            # method-6 (the primary moved), 25 Sep method-6. Then a backfill
            # rewrites all three under method-7, where liquidity reads absent
            # until 24 Sep and tight from then -- the 27 Sep Weekly's row.
            first = [("2026-09-18", None, "ample"), ("2026-09-23", "market-state-method-5", "ample"),
                     ("2026-09-24", "market-state-method-6", "ample"),
                     ("2026-09-25", "market-state-method-6", "tight")]
            for day, m, s in first:
                st.write(regime.STORE_KEY, None, day, f"{day}T20:46:00+00:00",
                         json.dumps(_obj(day, m, s)), source="derived_state")
            for day, _, _ in first:
                s = "tight" if day >= "2026-09-24" else None
                st.write(regime.STORE_KEY, None, day, "2026-09-27T00:34:00+00:00",
                         json.dumps(_obj(day, "market-state-method-7", s)),
                         source="derived_state")
            check(regime.published_method("2026-09-24", st) ==
                  (True, "market-state-method-6"),
                  "the FIRST-published object is the record, not the backfill")
            mc = regime.method_change_at("2026-09-24", st)
            check(bool(mc) and mc["label"] == "changed (method v5→v6)",
                  f"a change dated 24 Sep is method-caused: {mc and mc['label']}")
            check(regime.method_change_at("2026-09-25", st) is None,
                  "25 Sep, same method as 24 Sep, is not")
            w = wp.week_in_state("2026-09-25", store=st)
        finally:
            st.close()
    row = next((c for c in w.get("dimension_changes") or []
                if c["dimension"] == "liquidity"), {})
    check((row.get("method_change") or {}).get("label")
          == "changed (method v5→v6)",
          f"the Weekly's liquidity row carries the label "
          f"({(row.get('method_change') or {}).get('label')})")
    html = wr.state_block({"week_in_state": w})
    check("changed (method v5→v6)" in html and ">2026-09-24<" not in html,
          "and the rendered row prints the label, never 'since 2026-09-24'")

    cur = _obj("2026-09-25", "market-state-method-8", "tight")
    prev = _obj("2026-09-24", "market-state-method-7", "ample")
    wc = regime.what_changed(cur, prev)
    ch = next((c for c in wc.get("dimension_changes") or []
               if c["dimension"] == "liquidity"), {})
    check((ch.get("method_change") or {}).get("label")
          == "changed (method v7→v8)",
          "the close's WHAT CHANGED labels a change between objects of two methods")
    pay = {"market_state": cur, "what_changed": wc}
    check("changed (method v7→v8)" in state_block.what_changed_block(pay)
          and any("changed (method v7→v8)" in ln
                  for ln in state_block.text_lines(pay)),
          "and prints it, in the HTML and in the text fallback")
    same = regime.what_changed(_obj("2026-09-25", "market-state-method-8", "tight"),
                               _obj("2026-09-24", "market-state-method-8", "ample"))
    check(not any(c.get("method_change") for c in same["dimension_changes"]),
          "while a change between two objects of one method is the market's")


def group_g() -> None:
    """Exceptions print their side (Weekly edition 1, item 3)."""
    print(f"\n{LINE}\nG. AN EXTREME SAYS WHICH TAIL IT IS IN\n{LINE}")
    from altdata import derived
    from daily_cascade import state_block
    rule = "percentile <= 5 or >= 95"
    lo = {"id": "extreme:fred.rrp", "kind": "extreme", "value": 4.792,
          "threshold": rule, "what": "fred.rrp at a five-year extreme (liquidity)"}
    hi = {"id": "extreme:fred.ccc_oas", "kind": "extreme", "value": 99.7706,
          "threshold": rule, "what": "fred.ccc_oas at a five-year extreme (credit)"}
    check(derived.extreme_side(lo)["label"] == "4.8 (≤5)"
          and derived.extreme_side(hi)["label"] == "99.8 (≥95)",
          "the side is read from the exception's own percentile and rule")
    check(derived.extreme_side({"kind": "extreme", "value": 1.5,
                                "threshold": "percentile <= 2 or >= 98"})["label"]
          == "1.5 (≤2)", "a changed threshold changes the label with it")
    check(derived.extreme_side({"kind": "contradiction", "value": 2.4}) == {},
          "a contradiction has no side")
    pay = {"market_state": {"exceptions": [lo, hi]}}
    html = state_block.exceptions_block(pay)
    check("4.8 (≤5)" in html and "99.8 (≥95)" in html,
          "the close's exceptions table prints both sides")
    w = {"state": "ok", "week_ending": "2026-09-25",
         "exceptions_opened": ["extreme:fred.rrp"],
         "exceptions_open_now": ["extreme:fred.rrp", "extreme:fred.ccc_oas"],
         "exceptions_side": {"extreme:fred.rrp": derived.extreme_side(lo),
                             "extreme:fred.ccc_oas": derived.extreme_side(hi)}}
    wh = wr.state_block({"week_in_state": w})
    check("extreme:fred.rrp 4.8 (≤5)" in wh
          and "extreme:fred.ccc_oas 99.8 (≥95)" in wh,
          "and the Weekly's exception lines do")


NONE_IN_TEXT = re.compile(r"\bNone\b")


def visible_text(html: str) -> str:
    import html as _h
    return _h.unescape(re.sub(r"<[^>]+>", " ", html))


def group_h(p: dict) -> None:
    """The calendar lists events, not every business day (Weekly ed. 1, item 4)."""
    print(f"\n{LINE}\nH. THE CALENDAR, AND NO None IN A SENTENCE\n{LINE}")
    from altdata import events as ev_mod
    from daily_cascade import events_block
    rows = [
        {"source": "fred_releases", "entities": ["fred.yield_10y", "fred.yield_2y"]},
        {"source": "fred_releases", "entities": ["fred.job_openings"]},
        {"source": "fred_releases", "entities": ["fred.fed_balance", "fred.tga"]},
        {"source": "fred_releases", "entities": ["fred.rrp"]},
        {"source": "yfinance", "entities": []},
    ]
    check([ev_mod.is_daily_release(r) for r in rows]
          == [True, False, False, True, False],
          "H.15 and RRP are daily releases; JOLTS and H.4.1 are not; an earnings "
          "date is not a release")
    check(ev_mod.release_cadence(["fred.nfci", "fred.nfci_lev"]) == "weekly"
          and ev_mod.release_cadence(["fred.real_gdp", "fred.fed_outlays"])
          == "quarterly",
          "a release takes the slowest cadence it carries (NFCI weekly, GDP "
          "quarterly)")

    wa = {"state": "ok", "window": ["2026-09-28", "2026-10-04"],
          "releases": {"state": "ok", "count": 4, "listed_count": 2,
                       "rows": [{"date": "2026-09-29", "cadence": "monthly",
                                 "release_name": "Job Openings and Labor "
                                                 "Turnover Survey",
                                 "tracked_series": ["job_openings"]},
                                {"date": "2026-10-01", "cadence": "weekly",
                                 "release_name": "H.4.1 Factors Affecting "
                                                 "Reserve Balances",
                                 "tracked_series": ["fed_balance", "tga"]}],
                       "daily_rows": 2,
                       "daily_releases": ["H.15 Selected Interest Rates"]},
          "earnings": {"state": "empty"}, "dated_claims": []}
    html = wr.week_ahead_block({"week_ahead": wa})
    txt = visible_text(html)
    check("Job Openings" in txt and "H.4.1" in txt
          and "H.15 Selected Interest Rates" not in txt.split("Daily series")[0],
          "the table lists JOLTS and H.4.1, and H.15 appears only in the footnote")
    check("Daily series, not listed: 2 row(s) from 1 release(s)" in txt,
          "the daily releases are one footnote line with their count")
    old = {"state": "ok", "window": ["a", "b"],
           "releases": {"state": "ok", "count": 37, "rows": []},
           "earnings": {"state": "empty"}, "dated_claims": []}
    check(not NONE_IN_TEXT.search(visible_text(wr.week_ahead_block(
              {"week_ahead": old}))),
          "an old-shape releases block (no counts beyond `count`) prints no None "
          "-- the 27 Sep header read 'None of 37 ... None of None resolved'")

    wk = {"state": "ok", "since": "2026-09-25T20:00:00+00:00", "ahead_days": 9,
          "ahead_total": 3, "ahead_listed_in": "The week ahead",
          "ahead": [{"when": "2026-09-29T13:30", "source": "fred_releases",
                     "title": "Job Openings -- release date", "payload": {}}],
          "headlines": [], "releases": [], "earnings": [], "filings": []}
    eh = visible_text(events_block.html(wk))
    check("Listed under The week ahead" in eh and "Job Openings" not in eh,
          "the Weekly's Ahead list points at the week-ahead table instead of "
          "repeating it")
    check("Job Openings" not in events_block.markdown(wk)
          if hasattr(events_block, "markdown") else True,
          "and so does the Markdown edition")

    full = visible_text(wr.render(p))
    bad_s = [m.start() for m in NONE_IN_TEXT.finditer(full)]
    check(not bad_s, "no None inside any rendered sentence of the test edition"
                     + (f": ...{full[max(0, bad_s[0] - 60):bad_s[0] + 20]}..."
                        if bad_s else ""))


def group_i(p: dict) -> None:
    """Still-missing and dormant are this run's results (Weekly ed. 1, item 6)."""
    print(f"\n{LINE}\nI. STILL MISSING AND DORMANT ARE COMPUTED, NOT LISTED\n{LINE}")
    both = wp.needs_still({"fred_releases": {}, "sec_edgar": {}})
    check(len(both) == 1 and "CONSENSUS" in both[0],
          "with both sources written, only the macro consensus is missing")
    none_ = wp.needs_still({})
    check(len(none_) == 3 and any("fred_releases" in n for n in none_),
          "with neither, all three gaps print, each naming its source")

    # THE 27 SEPTEMBER CONTRADICTION, rebuilt: the calendar rendered rows while
    # the footer called its source dormant.
    wa = {"state": "ok", "window": ["2026-09-28", "2026-10-04"],
          "releases": {"state": "ok", "count": 1, "rows": [
              {"date": "2026-10-02", "cadence": "monthly",
               "release_name": "Employment Situation", "tracked_series": ["nfp"]}]},
          "earnings": {"state": "empty"}, "dated_claims": []}
    srcs = {"fred_releases": {"rows": 50}, "google_news": {"rows": 48}}
    wd = {"state": "ok", "since": "2026-09-25T20:00:00+00:00", "ahead_days": 9,
          "headlines": [], "releases": [], "earnings": [], "filings": [],
          "sources": srcs, "dormant": {"sec_edgar": "CHESTER_SEC_CONTACT unset"},
          "needs_still": wp.needs_still(srcs)}
    txt = visible_text(wr.week_ahead_block({"week_ahead": wa})
                       + wr.weekend_block({"weekend_developments": wd}))
    check("Employment Situation" in txt
          and "release calendar" not in txt.split("Still missing")[-1]
          and "fred_releases" not in txt.split("Dormant")[-1].split(".")[0],
          "a calendar that rendered rows is never called dormant or missing")
    check("SEC filings" in txt.split("Still missing")[-1],
          "while a source that has not written still is")

    # And on the test edition itself: nothing printed dormant has written.
    wdp = p.get("weekend_developments") or {}
    written = set((wdp.get("sources") or {}))
    called = set((wdp.get("dormant") or {})) | {
        s for s, _ in wp.NEEDS
        if any(s in n for n in wdp.get("needs_still") or [])}
    check(not (called & written),
          f"on the test edition no source both wrote rows and is called dormant "
          f"or missing ({sorted(called & written) or 'none'})")


def main() -> int:
    print(f"{LINE}\nWeekly Tactical -- Phase 4a\n{LINE}")
    p = wp.build(TEST_WEEK, fetch=False)
    print(f"  week ending {p.get('week_ending')}, "
          f"{len(p.get('sessions_in_week') or [])} sessions, "
          f"{len(p.get('warnings') or [])} absence(s)")
    group_a(p)
    group_b(p)
    group_c(p)
    group_d()
    group_e()
    group_f()
    group_g()
    group_h(p)
    group_i(p)
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed"
          + (f", {len(SKIPPED)} skipped" if SKIPPED else "") + f"\n{LINE}")
    for s in SKIPPED:
        print(f"  SKIPPED: {s}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
