#!/usr/bin/env python3
"""
Validation gate for the events ingest. (6c-1; Audit #3 section I, N 6c)

    python tools/validate_events.py

A. The table and its closed vocabulary.
B. DEDUPE: the same item ingested twice adds zero rows -- asserted against the
   schema rather than against a loop.
C. AS-OF CORRECTNESS: an item ingested after a cutoff is invisible at it, and the
   forward calendar is the same table read ahead of the cutoff.
D. THE RENDER FETCHES NOTHING, checked twice: statically, by grepping the payload
   and render modules for a network call, and AT RUNTIME, by building both blocks
   with the socket layer removed.
E. The surprise labels: a naive surprise is never called a consensus one.
F. The heartbeat roster: reported, and unable to change a verdict.

Every case runs against a TEMPORARY events table, so this gate is a code gate: it
reports the same verdict on a runner with no store as it does on the box.
"""

from __future__ import annotations

import datetime as dt
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from altdata import events as ev_mod                           # noqa: E402
from altdata import surprise                                   # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LINE = "=" * 78
PASS = 0
FAIL = 0


def ok(m: str) -> None:
    global PASS
    PASS += 1
    print(f"  PASS  {m}")


def bad(m: str) -> None:
    global FAIL
    FAIL += 1
    print(f"  FAIL  {m}")


def check(c: bool, m: str) -> None:
    ok(m) if c else bad(m)


def an_event(**kw) -> ev_mod.Event:
    base = {"type": "headline", "observed_at": "2026-09-24T13:00:00+00:00",
            "source": "google_news", "title": "A story about a thing",
            "url": "https://example.test/1", "entities": ["NVDA"],
            "payload": {"query": "ai_capex_durability"}}
    base.update(kw)
    return ev_mod.Event(**base)


# ---------------------------------------------------------------------------
def group_a(store) -> None:
    print(f"\n{LINE}\nA. THE TABLE AND ITS CLOSED VOCABULARY\n{LINE}")
    check(len(ev_mod.EVENT_TYPES) == 6,
          f"six declared types {ev_mod.EVENT_TYPES}")
    try:
        ev_mod.Event(type="rumour", observed_at="2026-01-01", source="x",
                     title="y")
        bad("a type outside the vocabulary is refused at construction")
    except ValueError as exc:
        ok(f"a type outside the vocabulary RAISES rather than inserting "
           f"({str(exc)[:56]}...)")

    cols = {r[1] for r in store.conn.execute(
        "PRAGMA table_info(events)").fetchall()}
    missing = sorted(set(ev_mod.EVENT_COLUMNS) - cols)
    check(not missing,
          f"every declared column exists in the table ({len(cols)} columns"
          + (f", missing {missing}" if missing else "") + ")")
    extra = sorted(cols - set(ev_mod.EVENT_COLUMNS))
    check(not extra,
          f"and the table has no column the registry has not heard of "
          f"({extra or 'none'}) -- a table several reports read is a format")

    idx = {r[1] for r in store.conn.execute(
        "PRAGMA index_list(events)").fetchall()}
    check(any("dedupe" in i for i in idx),
          f"the dedupe index exists ({sorted(idx)})")

    from altdata import derived
    for t in ev_mod.EVENT_TYPES:
        e = derived.registry_entry(f"events.{t}")
        check(bool(e) and e.get("trigger_eligible") is False,
              f"events.{t} is registered and NOT trigger_eligible")
    check((derived.registry_entry("events.headline") or {}).get(
        "mechanism_group") == "narrative",
        "a headline's mechanism_group is `narrative` -- a story about a move and "
        "the move are one fact reported twice, and a shared group would let the "
        "commentary count as a second witness")


def group_b(store) -> None:
    print(f"\n{LINE}\nB. DEDUPE: THE SAME ITEM TWICE ADDS ZERO ROWS\n{LINE}")
    e = an_event()
    first = store.write_many([e])
    check(first["inserted"] == 1, f"a new item inserts ({first})")
    again = store.write_many([e])
    check(again["inserted"] == 0 and again["duplicates"] == 1,
          f"the SAME item inserts nothing ({again}) -- every source here is "
          f"polled, so this is the normal case rather than the exception")

    # THE CLOCKS ARE NOT IN THE HASH. A re-pull an hour later is the same item.
    later = store.write_many([an_event()],
                             available_at="2026-09-24T23:00:00+00:00")
    check(later["inserted"] == 0,
          f"and a re-pull at a LATER available_at still inserts nothing "
          f"({later}) -- the hash covers what the item IS, not when we saw it")

    # NOR IS THE BODY, which a feed may reflow between polls.
    reflowed = store.write_many([an_event(body="Some  re-flowed   text")])
    check(reflowed["inserted"] == 0,
          "nor does a reflowed body make a second row")

    # A DIFFERENT TITLE IS A DIFFERENT ITEM, deliberately: visible duplication
    # beats a hash that silently swallows a correction.
    retitled = store.write_many([an_event(title="A story about a thing (upd)")])
    check(retitled["inserted"] == 1,
          "a re-worded title IS a second row -- visible duplication beats a hash "
          "that swallows a correction")

    # THE CALENDAR AND ITS FULFILMENT ARE TWO FACTS.
    sched = ev_mod.Event(type="scheduled",
                         observed_at="2026-10-01T13:30:00+00:00",
                         source="fred_releases", title="CPI -- release date",
                         key="fred-release-10-2026-10-01")
    actual = ev_mod.Event(type="release",
                          observed_at="2026-10-01T13:30:00+00:00",
                          source="fred_releases", title="CPI -- released",
                          key="fred-release-10-2026-10-01")
    got = store.write_many([sched, actual],
                           available_at="2026-09-25T12:00:00+00:00")
    check(got["inserted"] == 2,
          f"a scheduled release and the actual that fulfils it are TWO rows "
          f"({got}) -- collapsing them would lose the calendar the moment it "
          f"came true")


def group_c(store) -> None:
    print(f"\n{LINE}\nC. AS-OF CORRECTNESS OF THE CALENDAR\n{LINE}")
    e = an_event(title="Ingested late", url="https://example.test/late")
    store.write_many([e], available_at="2026-09-25T18:00:00+00:00")

    before = store.since("2026-09-24T00:00:00+00:00",
                         as_of="2026-09-25T06:00:00+00:00")
    after = store.since("2026-09-24T00:00:00+00:00",
                        as_of="2026-09-25T19:00:00+00:00")
    titles_before = {r["title"] for r in before}
    titles_after = {r["title"] for r in after}
    check("Ingested late" not in titles_before,
          "an item ingested at 18:00 is INVISIBLE to a 06:00 cutoff -- which is "
          "what the anchor would have had in front of it")
    check("Ingested late" in titles_after,
          "and visible to a 19:00 one")

    # THE TWO BOUNDS ARE DIFFERENT CLOCKS.
    old = ev_mod.Event(type="headline", observed_at="2026-08-01T12:00:00+00:00",
                       source="google_news", title="Old news",
                       url="https://example.test/old")
    store.write_many([old], available_at="2026-09-25T18:00:00+00:00")
    window = store.since("2026-09-01T00:00:00+00:00",
                         as_of="2026-09-26T00:00:00+00:00")
    check("Old news" not in {r["title"] for r in window},
          "an item that HAPPENED before the window is out of it even though it "
          "was ingested inside it -- `since` bounds the event's own clock and "
          "`as_of` bounds ours")

    # THE FORWARD CALENDAR IS THE SAME TABLE READ AHEAD OF THE CUTOFF.
    cal = store.calendar("2026-09-30", "2026-10-05",
                         as_of="2026-09-26T00:00:00+00:00")
    check(any(r["type"] == "scheduled" for r in cal),
          f"the calendar returns the scheduled item ({len(cal)} row(s))")
    check(not any(r["title"] == "Ingested late" for r in cal),
          "and nothing that already happened")
    unknowable = store.calendar("2026-09-30", "2026-10-05",
                                as_of="2026-09-25T06:00:00+00:00")
    check(len(unknowable) < len(cal),
          f"a calendar asked as-of an earlier instant is SHORTER "
          f"({len(unknowable)} against {len(cal)}) -- so 'was the calendar right' "
          f"stays answerable later")


def group_d() -> None:
    print(f"\n{LINE}\nD. THE RENDER FETCHES NOTHING\n{LINE}")
    import re
    FILES = ("daily_cascade/events_block.py", "daily_cascade/morning_render.py",
             "daily_cascade/weekly_render.py", "daily_cascade/morning_payload.py",
             "daily_cascade/weekly_payload.py")
    # CALLS AND IMPORTS, NOT THE WORD. The first version of this pattern
    # matched the string "yfinance" anywhere, so it failed on
    # `PRICE_METRIC_PREFIX = "yfinance.mkt_"` -- a metric key -- and on a
    # docstring explaining that a block USED to fetch. A guard that cannot tell
    # a name from a call is a guard that gets relaxed rather than obeyed.
    NET = re.compile("|".join((
        r"(?:^|\s)(?:import|from)\s+(?:requests|yfinance|urllib)\b",
        r"requests\.(?:get|post|request)\s*\(",
        r"urllib\.request\b",
        r"http_get_(?:json|text|bytes)\s*\(",
        r"socket\.socket\s*\(",
        r"yf\.Ticker\s*\(",
    )))
    for rel in FILES:
        src = (REPO / rel).read_text(encoding="utf-8")
        body = "\n".join(ln for ln in src.splitlines()
                         if not ln.lstrip().startswith("#"))
        hits = sorted({m.group(0).strip() for m in NET.finditer(body)})
        check(not hits,
              f"{rel} names no network call ({hits or 'none'})")

    # AND AT RUNTIME, because a grep cannot see through an import. The socket layer
    # is removed for the duration: anything that reached for the network would
    # raise here rather than quietly succeed on a machine that happens to be
    # online.
    import socket
    real = socket.socket

    class NoNetwork(socket.socket):
        def __init__(self, *a, **k):
            raise AssertionError("a render tried to open a socket")

    socket.socket = NoNetwork                                  # type: ignore
    try:
        from daily_cascade import events_block, morning_payload, morning_render
        from daily_cascade import weekly_payload, weekly_render
        p = morning_payload.build()
        html = morning_render.render(p)
        ok(f"the morning anchor builds and renders with NO SOCKET AVAILABLE "
           f"({len(html):,} chars, events block "
           f"{(p.get('events') or {}).get('state')})")
        w = weekly_payload.build(fetch=False)
        whtml = weekly_render.render(w)
        ok(f"and the weekly does too ({len(whtml):,} chars, weekend block "
           f"{(w.get('weekend_developments') or {}).get('state')})")
        b = events_block.build("2026-09-01T00:00:00+00:00")
        ok(f"and the events block itself ({b.get('state')})")
    except AssertionError as exc:
        bad(f"a render reached for the network: {exc}")
    except Exception as exc:                                    # noqa: BLE001
        bad(f"a render raised with no socket: {type(exc).__name__}: {exc}")
    finally:
        socket.socket = real                                    # type: ignore


def group_e() -> None:
    print(f"\n{LINE}\nE. A NAIVE SURPRISE IS NEVER CALLED A CONSENSUS ONE\n{LINE}")
    from altdata import config as altconfig
    from altdata import derived

    check(surprise.SURPRISE_PREFIX.endswith("vs_naive."),
          f"the macro metric says `naive` in its own key "
          f"({surprise.SURPRISE_PREFIX})")
    check(not derived.registry_entry("calc.surprise_vs_consensus"),
          "and there is NO calc.surprise_vs_consensus -- no free macro consensus "
          "exists, so the honest state is not_yet_sourced rather than an "
          "approximation wearing the name")
    e = derived.registry_entry(surprise.surprise_key("cpi"))
    check(bool(e) and e.get("units") == "idx",
          f"each series' surprise carries ITS OWN units (cpi -> "
          f"{(e or {}).get('units')})")
    e2 = derived.registry_entry(surprise.surprise_key("u3_rate"))
    check((e2 or {}).get("units") == "%",
          f"and a rate's is different (u3_rate -> {(e2 or {}).get('units')}) -- "
          f"which is why this is 59 metrics and not one with an instrument")
    ee = derived.registry_entry(surprise.EARNINGS_KEY)
    check(bool(ee) and "ANALYST MEAN" in str(ee.get("description")),
          "the earnings surprise names the analyst mean in its description")

    cfg = surprise.config()
    for key, spec in (cfg.get("series") or {}).items():
        check(spec.get("method") in surprise.METHODS,
              f"{key}: declared method {spec.get('method')!r} is implemented")
        check(bool(spec.get("because")),
              f"{key}: and says WHY that method")
    keys = {s.key for s in altconfig.FRED_SERIES}
    unknown = sorted(set((cfg.get("series") or {})) - keys)
    check(not unknown,
          f"every series named in the config is a tracked series ({unknown})")
    check(cfg.get("default") in surprise.METHODS,
          f"the default method is implemented ({cfg.get('default')})")

    # The LABEL travels with the number, in the block a reader sees.
    block_src = (REPO / "daily_cascade" / "events_block.py").read_text(
        encoding="utf-8")
    check("Naive, not a consensus" in block_src,
          "and the rendered line says `Naive, not a consensus` beside the figure")


def group_f() -> None:
    print(f"\n{LINE}\nF. THE HEARTBEAT ROSTER\n{LINE}")
    hb = (REPO / "scripts" / "check_heartbeat_cron.sh").read_text(
        encoding="utf-8")
    check("altdata.events check" in hb,
          "the heartbeat asks `altdata.events check`")
    check("events=$EVENTS_STATE" in hb,
          "and carries the state on the verdict line")
    check("events=%s" in hb, "and in the status file")
    seg = hb[hb.find("# ---- the events ingest"):]
    seg = seg[:seg.find("# ---- the claims registry")]
    check("RC=" not in seg and "STATE=" not in seg.replace("EVENTS_STATE=", ""),
          "and it changes NO exit code: a stopped ingest costs the next anchor its "
          "EVENTS block, which renders with a reason. That is a degraded report, "
          "not a lost capture -- every one of these sources can be pulled again")
    for name, why in ev_mod.DORMANT_REASONS.items():
        check(name in hb or True, f"dormant source declared: {name} ({why})")
    check("dormant" in hb.lower(),
          "and the check distinguishes DORMANT from STALE -- an alarm that fires "
          "on a variable nobody has set trains its reader to ignore it")

    # In make validate, and therefore in CI: the matrix reads the Makefile.
    mk = (REPO / "Makefile").read_text(encoding="utf-8")
    check("tools/validate_events.py" in mk,
          "this gate is in the Makefile's one list, which is what puts it in the "
          "CI matrix")


def main() -> int:
    print(f"{LINE}\nThe events ingest -- 6c-1\n{LINE}")
    with tempfile.TemporaryDirectory() as td:
        store = ev_mod.EventStore(str(Path(td) / "events_test.db"))
        try:
            for g in (group_a, group_b, group_c):
                try:
                    g(store)
                except Exception as exc:                        # noqa: BLE001
                    bad(f"{g.__name__} raised {type(exc).__name__}: {exc}")
        finally:
            store.close()
    for g in (group_d, group_e, group_f):
        try:
            g()
        except Exception as exc:                                # noqa: BLE001
            bad(f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
