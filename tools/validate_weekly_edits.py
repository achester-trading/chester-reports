"""
Validation gate for T2.2 -- the Weekly edits from the first live edition.

    python tools/validate_weekly_edits.py

On the Weekly gate's SYNTHETIC week (tools/validate_weekly_stack.py's seed) plus
this gate's own fixtures -- a code gate never reads the live store, never opens a
socket, and no figure here is real:

  A STRUCTURE    every section header is "number · name — subtitle"; What's
                 priced reads "what markets and surveys expect, not how they're
                 positioned"; Positioning has five sub-sections and What's priced
                 three; the glossary prints once, at the end.
  B PLAIN WORDS  every contradiction, story, sector and state word has its plain
                 description; no unlabelled id and no banned phrase reaches the
                 rendered edition; "venue" and the 4 Oct internal phrases are
                 banned in prose; an id in prose withholds it.
  C TABLE+PROSE  the tape is one table of the nine markets and four paragraphs
                 asked for; Plumbing prints no bullets; a paragraph that names a
                 figure not in its table is withheld.
  D WEEK BY DAY  The read's table carries each session's moves, the release, the
                 Fed or auction line and the most-cited story with its source; a
                 press attribution prints as the outlet's, with its URL.
  E FLAGS        pinned, call wall held, put wall held and amplified are computed
                 from a fixture at the config's values, None where a field is
                 missing; the table's flag column says only what is set.
  F CHARTS       W3, W4, W7, W8, W9 and W10 render from fixtures to PNG and SVG;
                 every title carries the count, the plain span and the date range;
                 an unfed gauge prints "not yet tracked" on its panel.
  G CALENDAR     times and tiers come from config/release_calendar.yaml: a CPI
                 release at 08:30 tier 1, ISM at 10:00 tier 2, a reopened 10-year
                 at 13:00 tier 2 with the prior auction, a Fed speech at its own
                 time, a quarterly expiry tier 1; routine releases are counted, not
                 listed; the Transition count's expiry and the next FOMC line print.
  H FEEDS        the ten CFTC contracts; MOVE, VVIX and SKEW in the price basket;
                 AAII registered; the Fed calendar and auctions in the ingest; the
                 5-minute backfill exists with its dry run; budgets count prose
                 only; the chart cap is 10; the minutes and the attention log carry
                 the 4 Oct lines.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TD = tempfile.mkdtemp(prefix="validate_weekly_edits_")
os.environ.setdefault("CHESTER_DB", str(Path(TD) / "default.db"))

LINE = "=" * 78
PASS = FAIL = 0


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def seed_extras(db: str, ending: str, sessions: list[str]) -> None:
    """Scorecards, 5-minute bars, a sourced voice with a press attribution."""
    from altdata import observations, bars as bars_mod, session
    from altdata import voices as vmod
    with observations.ObservationStore(db) as st:
        rows = []
        for n, s in enumerate(sessions):
            card = {"session": s, "symbol": "SPY", "gamma_regime": "negative",
                    "net_gex_close": -1.2e9, "dex_close": 3.4e9,
                    "flip_morning": 700.0, "flip_crossed": n == 0,
                    "session_high": 703.0 + n, "session_low": 690.0,
                    "close": 699.0 + n, "prior_close": 698.0,
                    "call_wall_morning": 704.0, "put_wall_morning": 680.0,
                    "max_pain": 699.0 + n if n == 1 else 650.0}
            rows.append({"registry_key": "dealer.scorecard_day", "instrument": "SPY",
                         "observed_at": s, "available_at": f"{s}T21:00:00+00:00",
                         "value": json.dumps(card), "source": "fixture"})
        st.write_many(rows)
    with bars_mod.BarStore(db, create=True) as bst:
        bars = []
        for s in sessions:
            a, _, n = bars_mod.session_window("spy", s)
            t0 = dt.datetime.fromisoformat(a)
            for k in range(n):
                px = 698.0 + (k % 13) * 0.2
                bars.append({"instrument": "spy", "symbol": "SPY", "interval": "5m",
                             "observed_at": (t0 + dt.timedelta(minutes=5 * k)).isoformat(),
                             "open": px, "high": px + 0.3, "low": px - 0.3,
                             "close": px + 0.1, "volume": 1000.0 + k,
                             "available_at": f"{s}T21:00:00+00:00"})
        bst.write_many(bars)
    with vmod.VoicesStore(db) as vs:
        vs.write({"voice": "Fixture Strategist", "affiliation": "Fixture Bank",
                  "kind": "sell_side", "view": "Expects equities to keep rising.",
                  "outlet": "CNBC", "source_url": "https://fixture.example/story",
                  "published_at": sessions[2], "retrieved_at": f"{sessions[2]}T22:00:00+00:00",
                  "tier": 1, "directions": [{"subject": "us_equities",
                                             "direction": "bullish"}],
                  "stories": [{"story": "ai_capex_durability", "side": "for"}]},
                 stories={"ai_capex_durability"})
        vs.write_attribution({"outlet": "CNBC", "market": "US stocks",
                              "claim": "a softer jobs report lowering yields",
                              "source_url": "https://fixture.example/story",
                              "published_at": sessions[2],
                              "retrieved_at": f"{sessions[2]}T22:00:00+00:00",
                              "tier": 1})


def seed_calendar(db: str, ending: str) -> None:
    from altdata import events as ev_mod, observations
    mon = dt.date.fromisoformat(ending) + dt.timedelta(days=3)
    day = lambda k: (mon + dt.timedelta(days=k)).isoformat()      # noqa: E731
    E = ev_mod.Event
    evs = [
        E(type="scheduled", observed_at=f"{day(2)}T13:30:00+00:00",
          source="fred_releases", title="Consumer Price Index -- release date",
          payload={"release_name": "Consumer Price Index"}),
        E(type="scheduled", observed_at=f"{day(0)}T13:30:00+00:00",
          source="fred_releases", title="H.15 Selected Interest Rates -- release date",
          payload={"release_name": "H.15 Selected Interest Rates"}),
        E(type="scheduled", observed_at=f"{day(0)}T14:00:00+00:00",
          source="schedule_rule", title="ISM Services PMI -- (schedule rule)",
          payload={"rule": "ism_services"}),
        E(type="scheduled", observed_at=f"{day(1)}T17:00:00+00:00",
          source="treasury_upcoming", title="Note:9-Year 10-Month auction",
          payload={"instrument": "Note:9-Year 10-Month"}),
        E(type="scheduled", observed_at=f"{day(1)}T15:00:00+00:00",
          source="treasury_upcoming", title="Bill:4-Week auction",
          payload={"instrument": "Bill:4-Week"}),
        E(type="scheduled", observed_at=f"{day(3)}T14:45:00+00:00",
          source="fed_calendar", title="Speech - Governor Fixture Person -- Outlook",
          payload={"kind": "Speeches", "speaker": "Governor Fixture Person",
                   "time_et": "10:45"}),
        E(type="session_event", observed_at=f"{day(4)}T20:00:00+00:00",
          source="session_calendar", title="OPEX monthly expiration"),
        E(type="earnings", observed_at=f"{day(3)}T12:00:00+00:00", source="yfinance",
          title="JPM earnings", payload={"symbol": "JPM"}),
    ]
    with ev_mod.EventStore(db) as ev:
        ev.write_many(evs, available_at="2026-10-01T00:00:00+00:00")
    with observations.ObservationStore(db) as st:
        st.write_many([{"registry_key": "auction.high_yield", "instrument": "Note:10-Year",
                        "observed_at": "2026-09-09", "available_at": "2026-09-09T18:00:00+00:00",
                        "value": 4.112, "source": "fixture"},
                       {"registry_key": "auction.bid_to_cover", "instrument": "Note:10-Year",
                        "observed_at": "2026-09-09", "available_at": "2026-09-09T18:00:00+00:00",
                        "value": 2.51, "source": "fixture"}])


def main() -> int:
    import validate_weekly_stack as vws
    from altdata import config, labels, bars as bars_mod
    from daily_cascade import (charts as charts_mod, stack as stack_mod, stack_prose,
                               stack_render, weekly_sections as wsec,
                               weekly_stack as ws)
    config.COMPUTED_DIR = str(Path(TD) / "computed")
    db = str(Path(TD) / "weekly.db")
    arch = str(Path(TD) / "reports")
    logp = Path(TD) / "attention-log.md"
    logp.write_text("| date | kind | minutes | note |\n|---|---|---|---|\n",
                    encoding="utf-8")
    seeded = vws.seed(db)
    p = vws.payload(seeded)
    sessions = p.get("sessions_in_week") or vws.weekdays(vws.ENDING, 5)
    seed_extras(db, vws.ENDING, sessions)
    seed_calendar(db, vws.ENDING)
    calls: list = []
    out = ws.produce(p, archive_dir=arch, client=vws.client(calls), db_path=db,
                     log_path=logp)
    ed = out["edition"]
    sec = {s["id"]: s for s in ed["sections"]}
    html = out["html_archive"]
    cfg = stack_mod.config()

    # --- A. STRUCTURE -------------------------------------------------------------
    print(f"\n{LINE}\nA. HEADERS, SUB-SECTIONS, THE GLOSSARY\n{LINE}")
    heads = re.findall(r"<h2[^>]*>(\d+) &middot; ([^<]+?) <span style=\"font-size:13px;"
                       r"font-weight:400;font-style:italic;color:#5a6b7a\">&mdash; "
                       r"([^<]+)</span>", html)
    check(len(heads) == 10 and [int(h[0]) for h in heads] == list(range(1, 11)),
          f"every header is 'number · name — subtitle', styled apart ({len(heads)})")
    check(any(h[2] == "what markets and surveys expect, not how they&#x27;re positioned"
              or h[2] == "what markets and surveys expect, not how they're positioned"
              for h in heads),
          "What's priced: 'what markets and surveys expect, not how they're positioned'")
    check([ss["title"] for ss in sec["positioning"]["subsections"]] ==
          ["Sector rotation and leadership", "Speculative positioning (CFTC)",
           "Short interest", "Retail sentiment", "Foreign flows (TIC)"],
          "Positioning in five sub-sections, each with its table")
    check(len(sec["priced"]["subsections"]) == 3
          and sec["priced"]["subsections"][1]["title"] == "Prediction markets",
          "What's priced in three sub-chapters")
    check(html.count(">Glossary</h2>") == 1 and html.rfind(">Glossary</h2>") >
          html.rfind("&middot; The book"),
          "the glossary prints once, at the end")
    for t in ("z", "gap z-score", "pending, open, exception", "outside 10–90%",
              "base rate", "Brier"):
        check(f"<strong>{stack_render.esc(t)}</strong>" in html, f"glossary: {t}")

    # --- B. PLAIN WORDS -----------------------------------------------------------
    print(f"\n{LINE}\nB. THE PLAIN-LANGUAGE RULE\n{LINE}")
    import yaml
    ms = yaml.safe_load((REPO / "config" / "market_state.yaml").read_text(encoding="utf-8"))
    pairs = [x["id"] for x in (ms.get("contradictions") or {}).get("pairs") or []]
    check(pairs and all(labels.contradiction_plain(c).get("legs")
                        and labels.contradiction_plain(c).get("closes") for c in pairs),
          f"every contradiction pair says what each side says and what closes it "
          f"({len(pairs)})")
    nr = yaml.safe_load((REPO / "config" / "narratives.yaml").read_text(encoding="utf-8"))
    sids = list((nr.get("narratives") or {}).keys())
    check(sids and all(labels.story(s).get("title") and labels.story(s).get("statement")
                       for s in sids), f"every story has a plain title and statement "
                                       f"({len(sids)})")
    check(all(labels.sector(x) != x for x in ws.SECTORS)
          and labels.sector("XLV") == "Health Care (XLV)",
          "every sector ETF reads 'Health Care (XLV)'")
    check(all(labels.state(w) for w in ("pending", "open", "exception", "emerging",
                                        "consensus", "contested", "fading",
                                        "confirmed")),
          "every state word has its plain description")
    check(all(labels.exception_kind(k) for k in ("extreme", "contradiction")),
          "every exception kind has its plain description")
    banned = (cfg.get("style") or {}).get("banned_phrases") or []
    check({"mapped scenario counterpart", "venue disagreement", "venue"} <= set(banned),
          "'mapped scenario counterpart', 'venue disagreement' and 'venue' are banned")
    flt = stack_prose.style_faults("The venue prices a hike at 62%.", cfg)
    check(any("venue" in f for f in flt),
          "'prediction market' replaces 'venue': the prose audit refuses 'venue'")
    check(stack_prose.id_faults("The equities_vs_credit gap and fred.hy_oas.")
          and not stack_prose.id_faults("SPY's 2s10s and the S&P 500 held."),
          "an internal id in prose is a fault; plain names are not")
    body = re.sub(r"<[^>]+>", " ", html)
    ids = re.findall(r"\b(?:fred|calc|cftc|pm|dial|ndl|yfinance)\.[a-z0-9_]+\b", body)
    snakes = [w for w in pairs + sids if re.search(rf"\b{w}\b", body)]
    check(not ids and not snakes,
          f"no unlabelled id reaches the rendered edition ({ids[:3]} {snakes[:3]})")
    vm = re.search(r".{0,60}\bvenue.{0,40}", body, re.I | re.S)
    check(not vm, "the word 'venue' appears nowhere in the rendered edition"
          + (f" ({vm.group(0)!r})" if vm else ""))
    ns = ws.narratives_week_section({"narratives": [
        {"id": "ai_capex_durability", "name": "AI capex durability", "state": "emerging",
         "evidence_for": 9, "evidence_against": 0}]}, {}, None)
    ai = next((i["text"] for i in ns["items"] if i["key"] == "narr:ai_capex_durability"), "")
    check(ai.startswith("AI spending keeps growing (emerging). The largest technology "
                        "companies") and "Nine pieces of evidence supported it, none "
                                          "contradicted it." in ai,
          f"Narratives: nine for and none against reads in words ({ai[-70:]})")
    check(ai and re.search(r"(No evidence supported it|[A-Z][a-z]+ pieces? of "
                           r"evidence supported it), (none|[a-z]+) contradicted it\.$",
                           ai) and not re.search(r"\d+ (for|against)", ai),
          f"Narratives: the plain title and statement, counts in words ({ai[:110]})")
    check((sec["narratives"].get("legend") or "").startswith("States: emerging"),
          f"Narratives: a legend for the states ({sec['narratives'].get('legend')})")

    # --- C. TABLE AND PROSE ------------------------------------------------------
    print(f"\n{LINE}\nC. THE TABLE-AND-PROSE RULE\n{LINE}")
    tt = sec["tape"]["table"]
    check(tt["columns"] == ["Market", "Last", "Session", "Week", "Month", "YTD",
                            "Week high / low", "52-week high (distance)",
                            "vs 20 / 50 / 200-day", "Gamma flip"],
          "the tape is one table: last, session, week, month, YTD, week range, "
          "52-week high and distance, the averages, the flip")
    check(not sec["tape"]["print_items"] and not sec["plumbing"]["print_items"],
          "the tape and Plumbing print no bullets; the prose reads the table")
    tape_calls = [c for c in calls if "THE SECTION: The tape." in c]
    check(tape_calls and "exactly four paragraphs" in tape_calls[0]
          and "equities (SPY, QQQ, IWM); rates" in tape_calls[0],
          "the tape's prose is asked for four paragraphs: equities, rates, the dollar "
          "and commodities, crypto")
    rel = [{"release": "Consumer Price Index", "label": "CPI", "actual_text": "3.10%",
            "prior_text": "3.00%", "as_of": "2026-09-01", "date": "2026-10-01",
            "series": "fred.cpi", "actual": 3.1, "prior": 3.0}]
    import unittest.mock as _mock
    from altdata import observations as _obs
    with _obs.ObservationStore(db) as _st, \
            _mock.patch.object(ws, "tier1_releases", lambda *a, **k: rel):
        pw = ws.plumbing_week(_st, vws.AS_OF, ws.week_ago(vws.AS_OF))
    check(["Consumer Price Index: CPI", "3.10%", "prior 3.00%", "2026-09-01"]
          in pw["table"]["rows"] and pw["print_items"] is False,
          "Plumbing's table carries the week's tier-1 releases: actual, prior, as-of")
    from daily_cascade import narrative as base
    payload_t = stack_prose._slice(sec["tape"], ed)
    r = base.generate(payload_t, client=vws.client([], "SPY rose to 9,999.99 on the week."),
                      system_prompt="x", max_chars=2000, one_paragraph=False,
                      citable_ids=[], unit_constants=[1.0],
                      guide_path=stack_prose.STACK_GUIDE)
    check(not r.published, "a paragraph naming a figure not in its table is withheld "
                           f"({r.state})")

    # --- D. THE WEEK BY DAY -----------------------------------------------------
    print(f"\n{LINE}\nD. THE READ: THE WEEK BY DAY\n{LINE}")
    rt = sec["read"]["table"] or {}
    check(rt.get("columns") == ["Day", "SPY", "10-year", "Tier-1 release (actual, prior)",
                                "Fed speech or auction", "Most-cited story (source)"]
          and len(rt.get("rows") or []) == len(sessions),
          f"one row per session ({len(rt.get('rows') or [])})")
    story_cells = [r[5] for r in rt["rows"] if r[5] != "—"]
    check(story_cells and "AI spending keeps growing" in story_cells[0]
          and "https://fixture.example/story" in story_cells[0],
          f"the day's most-cited story with its source ({story_cells[:1]})")
    attr = [i["text"] for i in sec["read"]["items"] if i["key"].startswith("read:attr")]
    check(attr and "CNBC attributed the move in US stocks to" in attr[0]
          and "https://fixture.example/story" in attr[0],
          f"a press attribution prints as the outlet's, with its URL ({attr[:1]})")
    read_calls = [c for c in calls if "THE WEEK BY DAY" in c]
    check(read_calls and "never the cause as fact" in read_calls[0],
          "The read is told to read the table and never adopt a press cause")

    # --- E. FLAGS ---------------------------------------------------------------
    print(f"\n{LINE}\nE. THE DEALER FLAGS, FROM A FIXTURE\n{LINE}")
    fc = {"dealer_flags": {"pinned_pct": 0.25, "wall_pct": 0.25,
                           "amplified_range_ratio": 1.2}}
    base_c = {"close": 700.0, "prior_close": 700.0, "session_high": 704.5,
              "session_low": 692.0, "max_pain": 700.5, "call_wall_morning": 705.0,
              "put_wall_morning": 692.5, "flip_morning": 699.0, "flip_crossed": True}
    f = wsec.flags_for(base_c, 20.0, fc)
    check(f["pinned"] is True, "pinned: the close within 0.25% of max pain")
    check(wsec.flags_for({**base_c, "max_pain": 703.0}, 20.0, fc)["pinned"] is False,
          "not pinned at 0.43% from max pain")
    check(f["call_wall_held"] is True and
          wsec.flags_for({**base_c, "close": 706.0, "session_high": 706.5}, 20.0,
                         fc)["call_wall_held"] is False,
          "call wall held: the high within 0.25% and the close inside; not when the "
          "close is through it")
    check(f["put_wall_held"] is True, "put wall held: the low within 0.25%, close above")
    imp = 700.0 * 0.20 * (1 / 252) ** 0.5
    check(abs(f["implied_range"] - round(imp, 2)) < 0.01 and f["amplified"] is True,
          f"amplified: the flip crossed and the actual range {f['actual_range']} >= "
          f"1.2 x the implied {f['implied_range']}")
    check(wsec.flags_for({**base_c, "session_high": 701.0, "session_low": 699.0},
                         20.0, fc)["amplified"] is False,
          "not amplified when the range is under 1.2 x the implied")
    g = wsec.flags_for({"close": 700.0}, None, fc)
    check(g["pinned"] is None and g["amplified"] is None and g["call_wall_held"] is None,
          "a flag whose field is missing is None, never guessed")
    mt = sec["mechanics"]["table"]
    check(mt["columns"][-1] == "Flags" and len(mt["rows"]) == len(sessions)
          and any("pinned" in r[-1] for r in mt["rows"]),
          f"the weekly dealer table prints one row per session with its flags "
          f"({[r[-1] for r in mt['rows']]})")
    mech_calls = [c for c in calls if "THE SECTION: Mechanics." in c]
    check(mech_calls and "only where that session's flag column says so" in mech_calls[0],
          "the model may write a flag word only where the flag is set")
    check(cfg["dealer_flags"]["status"] == "proposed",
          "the flag values are config, marked proposed for the Doctrine (#2)")

    # --- F. CHARTS ----------------------------------------------------------------
    print(f"\n{LINE}\nF. THE NEW CHARTS FROM FIXTURES\n{LINE}")
    for k in ("W3", "W4", "W7", "W8", "W9", "W10"):
        c = out["charts"].get(k) or {}
        ok = c.get("png") and c["png"][:4] == b"\x89PNG" and c.get("svg_path") \
            and Path(c["svg_path"]).exists() and c["png_bytes"] <= charts_mod.MAX_PNG_BYTES
        check(ok, f"{k} renders to PNG and SVG -- "
                  f"{str(c.get('caption') or c.get('unavailable'))[:80]}")
    w9 = out["charts"].get("W9") or {}
    check("SPY put/call, volume (SPY chain, own capture)" in (w9.get("not_drawn") or [])
          and "NAAIM exposure" in (w9.get("not_drawn") or []),
          "W9: an unfed gauge prints 'not yet tracked' on its panel")
    st_ = charts_mod.span_title("SPY", 126, "sessions", "2026-04-01", "2026-10-02",
                                "six months")
    check(st_ == "SPY, 126 sessions (six months), 2026-04-01 to 2026-10-02",
          "titles carry the count, the plain span and the date range")
    import inspect as _insp
    srcs = {k: _insp.getsource(getattr(charts_mod, f)) for k, f in
            (("W1", "w1"), ("W2", "w2"), ("W3", "w3_panel"), ("W7", "w7"),
             ("W8", "w8"), ("W10", "w10"))}
    check(all("span_title(" in v or "sessions, {d0} to {d1}" in v
              for v in srcs.values())
          and "span_title(" in _insp.getsource(ws.produce),
          "W1-W10 build their titles with the count, span and dates")
    check(ws.chart_plan({"budget": {"charts": 10}, "sections": [
        {"id": "misfit", "data": {"open_contradictions": [1]}}]}) ==
        ["W1", "W2", "W8", "W7", "W6", "W3", "W5", "W4", "W9", "W10"],
        "the plan carries ten charts at the cap of 10")
    b65 = charts_mod.bars_65([{"observed_at": "2026-10-01T13:30:00+00:00", "open": 1,
                               "high": 2, "low": 0.5, "close": 1.5, "volume": 10},
                              {"observed_at": "2026-10-01T14:35:00+00:00", "open": 1.5,
                               "high": 3, "low": 1, "close": 2, "volume": 10}])
    check(len(b65) == 2 and b65[0]["slot"] == 0 and b65[1]["slot"] == 1,
          "65-minute bars are anchored at 09:30 ET: 09:30 and 10:35 open new bars")

    # --- G. CALENDAR ----------------------------------------------------------
    print(f"\n{LINE}\nG. THE CALENDAR, FROM CONFIG\n{LINE}")
    rows = (sec["ahead"]["data"] or {}).get("calendar") or []
    by = {r["event"]: r for r in rows}
    check(by.get("CPI", {}).get("time") == "08:30" and by["CPI"]["tier"] == 1
          and by["CPI"]["consensus"] == "no consensus stored",
          f"CPI at 08:30, importance 1, consensus 'no consensus stored' ({by.get('CPI')})")
    check(by.get("ISM", {}).get("time") == "10:00" and by["ISM"]["tier"] == 2,
          "ISM at 10:00, importance 2")
    a10 = by.get("10-year note auction") or {}
    check(a10.get("time") == "13:00" and a10.get("tier") == 2
          and "high yield 4.112%" in a10.get("consensus", "")
          and "tail not stored" in a10.get("consensus", ""),
          f"a reopened 10-year at 13:00, importance 2, with the prior auction ({a10})")
    sp = [r for r in rows if "Fixture Person" in r["event"]]
    check(sp and sp[0]["time"] == "10:45", "a Fed speech at its own time from the feed")
    ex = [r for r in rows if "option expiry" in r["event"]]
    check(ex and ex[0]["tier"] == 2, "a monthly expiry, importance 2")
    check(any(r["event"] == "JPM earnings" for r in rows), "earnings from the universe")
    check("H.15" not in json.dumps(rows) and "Bill" not in json.dumps(rows)
          and any("routine data releases" in n for n in sec["ahead"]["not_tracked"]),
          "routine releases and bill auctions are counted, not listed")
    check(wsec.canonical_auction("Bond:29-Year 10-Month") == "Bond:30-Year",
          "a reopening is named by the security it reopens")

    class FakeSt:
        def rows_before(self, key, before, as_of=None, limit=None):
            out = []
            for d, s in (("2026-09-29", "expansion"), ("2026-09-30", "expansion"),
                         ("2026-10-01", "overheating"), ("2026-10-02", "overheating")):
                out.append({"value_text": json.dumps({"session": d, "dials": {
                    "macro": {"state": s}}})})
            return out
    te = wsec.transition_expiry(FakeSt(), "2026-10-04T00:00:00+00:00",
                                {"regime_mapping": {"transition_sessions": 10}})
    check(te and te["changed_on"] == "2026-10-01" and te["expires_after"] == "2026-10-15",
          f"the Transition count runs ten sessions from the change ({te})")
    w_lines = (sec["ahead"]["data"] or {}).get("watching") or []
    check(sec["ahead"]["subsections"][0]["title"] == "What the system is watching",
          f"Ahead carries 'What the system is watching' ({w_lines[:1]})")

    # --- H. FEEDS, CONFIG AND RECORDS ------------------------------------------
    print(f"\n{LINE}\nH. FEEDS, CONFIG AND THE RECORDS\n{LINE}")
    from altdata.sources import cftc, yfinance_source as yfs
    check(set(cftc.CONTRACTS.values()) >= {"SP500", "NDX100", "RUSSELL2000", "UST10Y",
                                           "UST30Y", "VIX", "USD_INDEX", "JPY", "GOLD",
                                           "WTI"}
          and len(ws.CFTC_CONTRACTS) == 10,
          "the CFTC feed carries the ten contracts W4 draws")
    check(all(s in yfs.SYMBOLS for s in ("^MOVE", "^VVIX", "^SKEW")),
          "MOVE, VVIX and SKEW are in the price basket")
    from altdata import derived, feeds, events_ingest
    check(derived.registry_entry("aaii.bull_bear_spread").get("source") == "aaii"
          and "aaii" in feeds.EXTERNAL_WRITERS,
          "the AAII bull-bear spread is registered and fed")
    check({"fed_calendar", "auctions"} <= set(events_ingest.SOURCES),
          "the Fed's speaker calendar and Treasury's auctions are in the ingest")
    import inspect
    check("def backfill(" in inspect.getsource(bars_mod) and "--dry-run" in
          inspect.getsource(bars_mod._main),
          "the one-time 60-day 5-minute backfill exists, with its dry run")
    check(cfg["budget"]["weekly"]["charts"] == 10, "the Weekly's chart cap is 10")
    check("PROSE ONLY" in inspect.getsource(stack_mod.section_words),
          "budgets count prose only, every report")
    mins = (REPO / "docs" / "briefs" / "doctrine-monthly-2026-10-minutes.md").read_text(
        encoding="utf-8")
    check("4 Oct — Weekly chart cap raised (W7 intraday, W8 panel, W9 gauges, W10 "
          "priced); reading budgets count prose only." in mins,
          "the minutes carry the 4 Oct post-sitting note")
    att = ws.read_attention_log()
    check(any(e["date"] == "2026-10-04" and e["minutes"] == 35 and "T2.2" in e["note"]
              for e in att), "the attention log carries the 4 Oct ruling line")

    # --- I. THE RULINGS OF 5 OCT ---------------------------------------------
    print(f"\n{LINE}\nI. THE RULINGS OF 5 OCT\n{LINE}")
    cal_cfg = wsec.load_calendar()
    th = cal_cfg.get("tier1_headlines") or {}
    forms = {(rel, h["key"]): h["form"] for rel, hs in th.items() for h in hs}
    check(forms.get(("Employment Situation", "fred.nfp")) == "change"
          and forms.get(("Employment Situation", "fred.u3_rate")) == "level"
          and forms.get(("Gross Domestic Product", "fred.real_gdp")) == "annualised"
          and forms.get(("Unemployment Insurance Weekly Claims", "fred.claims_4wk")) == "level"
          and {h["form"] for h in th["Consumer Price Index"]} == {"mom", "yoy"}
          and {h["form"] for h in th["Personal Income and Outlays"]} == {"mom", "yoy"},
          "1: headline forms from config -- payrolls change, CPI and PCE m/m and y/y, "
          "unemployment level, GDP annualised, claims level")
    check(all(h.get("label") and "_" not in h["label"] for hs in th.values() for h in hs),
          "1: every headline prints under a declared label, never a raw series name")
    hf = ws.headline_form
    check(hf([159000.0, 159029.0, 159044.0], "change") == (15.0, 29.0)
          and round(hf([100.0, 100.3], "mom")[0], 2) == 0.3
          and round(hf([100.0] + [0] * 0 + [100.0 + i * 0.25 for i in range(1, 13)],
                       "yoy")[0], 2) == 3.0
          and round(hf([100.0, 101.0], "annualised")[0], 2) == 4.06
          and hf([231000.0], "level") == (231000.0, None),
          "1: the forms compute: change, m/m, y/y over twelve prints, annualised, level")
    check(ws.form_text(29.0, "change", "fred.nfp") == "+29"
          and ws.form_text(0.31, "mom", "fred.cpi") == "+0.3%"
          and ws.form_text(4.2, "level", "fred.u3_rate") == "4.2%",
          "1: printed as +29 (thousands), +0.3%, 4.2%")
    wr = (REPO / "daily_cascade" / "weekly_report.py").read_text(encoding="utf-8")
    gi = (REPO / ".gitignore").read_text(encoding="utf-8")
    check('args.archive_dir = str(Path(delivery.ARCHIVE_DIR) / "dryrun")' in wr
          and "args.prior_dir = delivery.ARCHIVE_DIR" in wr
          and "reports/dryrun/" in gi
          and "prior_dir or archive_dir" in _insp.getsource(ws.produce),
          "2: --dry-run renders with the model to reports/dryrun/, reads the prior "
          "edition from the real archive, sends nothing, and is gitignored")
    import iv_solver as _ivs
    from altdata import chain_metrics as cm
    rows = []
    fwd, r = 700.0, 0.043
    for dte in (28, 35):
        t = dte / 365.0
        for k in range(650, 751, 5):
            for right in ("C", "P"):
                px = _ivs.black76_price(fwd, float(k), t, r, 0.20, right)
                rows.append({"expiry": f"exp{dte}", "dte": dte, "right": right,
                             "strike": float(k), "bid": round(px, 4),
                             "ask": round(px, 4), "last_price": round(px, 4),
                             "volume": 100.0 if right == "P" else 80.0,
                             "last_trade_date": None,
                             "fetched_at": "2026-10-02T20:14:00+00:00", "spot": fwd})
    iv = cm.atm_iv_30d(rows, r)
    check(iv and abs(iv["iv_pct"] - 20.0) < 0.2 and iv["method"] == "variance_interpolated",
          f"3: SPY's ATM 30-day IV from the chain solver recovers a 20% chain ({iv})")
    pc = cm.put_call_volume(rows)
    check(pc and pc["ratio"] == 1.25, f"4: put/call from the chain's own volume ({pc})")
    f_own = wsec.flags_for({**base_c, "atm_iv_30d": 15.0}, 20.0, fc)
    f_vix = wsec.flags_for(base_c, 20.0, fc)
    check(f_own["iv_source"] == "SPY ATM 30-day IV"
          and abs(f_own["implied_range"] - round(700 * 0.15 * (1 / 252) ** 0.5, 2)) < 0.01
          and f_vix["iv_source"] == "VIX as proxy",
          "3: the implied range uses SPY's own IV when stored, else the VIX labelled "
          "'VIX as proxy'")
    labels_w9 = [g[0] for g in ws.W9_GAUGES]
    check(any("SPY chain, own capture" in x for x in labels_w9)
          and not any("Equity put/call" == x for x in labels_w9)
          and dict((g[0], g[1]) for g in ws.W9_GAUGES).get("NAAIM exposure") == "naaim.exposure",
          "4: W9's put/call is SPY's own, labelled 'SPY chain, own capture'; no Cboe "
          "series")
    from altdata.sources import naaim
    from altdata import feeds as _feeds
    check(naaim.pull(today=dt.date(2026, 10, 5))["state"] == "not_due"
          and naaim.parse_widget("<b>73.81</b> as of 10/01/2026") ==
          {"date": "2026-10-01", "value": 73.81}
          and "naaim" not in _feeds.EXTERNAL_WRITERS
          and "altdata.sources.naaim pull" in (REPO / "scripts" /
                                              "fetch_overnight.sh").read_text(encoding="utf-8"),
          "4: NAAIM is retried weekly (Thursdays) from the overnight pass, and is "
          "not a feed whose absence marks the feeds stale")
    aaii_rows = [r for r in sec["positioning"]["subsections"][3]["table"]["rows"]
                 if str(r[0]).startswith("AAII")]
    aaii_src = _insp.getsource(ws.positioning_subsections)
    check("source: AAII Sentiment Survey" in aaii_src and "as of {aaii['observed_at']}" in aaii_src,
          f"4: the AAII row prints its source and as-of ({aaii_rows[:1]})")

    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
