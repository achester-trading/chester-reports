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

    def strip(d: dict) -> str:
        # The stamps that MUST differ between two builds. Everything else is read
        # from the store and must not.
        out = {k: v for k, v in d.items()
               if k not in ("generated_at", "as_of", "run_id")}
        return json.dumps(out, sort_keys=True, default=str)

    a = wp.build(TEST_WEEK, fetch=False)
    b = wp.build(TEST_WEEK, fetch=False)
    check(strip(a) == strip(b),
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
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed"
          + (f", {len(SKIPPED)} skipped" if SKIPPED else "") + f"\n{LINE}")
    for s in SKIPPED:
        print(f"  SKIPPED: {s}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
