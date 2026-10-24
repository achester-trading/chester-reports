#!/usr/bin/env python3
"""
Validation gate for the ten-section stack on the Weekly. (reporting-stack T2)

    python tools/validate_weekly_stack.py

The brief's section 5 at the Weekly cadence, on a SYNTHETIC week in a temporary
store -- a code gate never reads the live store, and no figure here is real:

  A STACK      ten sections in order at the Weekly's depths; marks and collapse
               against the PRIOR WEEKLY, never a daily edition; What's priced goes
               deep on a week's 12 bp breakeven move and stays medium without one.
  B LEVELS     the tape names only listed levels; W1/W2 draw only listed levels.
  C PROSE      one audited call per section in the Weekly's frames.
  D CHARTS     W1-W6 render to PNG (<= 150 KB) and SVG; the Content-ID set matches
               the body; a chart that cannot render prints its reason.
  E POSITIONING  CFTC, FINRA, RTAT10, ApeWisdom, TIC and leadership from the store;
               S&P 500 and 10-year CFTC positioning "not yet tracked".
  F CALLS      Brier by source over the last four weeks; base-rate outlooks on
               their own line; a call resolved five weeks ago is not counted.
  G ATTENTION  packets approved / 7 from the register; a deferral recorded with
               the attention_budget reason; sitting hours / 2 and rulings from the
               attention log; each trigger's firing count.
  H BUDGET     a 35-minute, 7,900-word target (D19/D20); over it nothing is cut, one foot line.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import tempfile
import os as _gt_os                                            # noqa: E402
import sys as _gt_sys                                          # noqa: E402
_gt_dir = _gt_os.path.dirname(_gt_os.path.abspath(__file__))
_gt_sys.path.insert(0, _gt_dir if _gt_os.path.basename(_gt_dir) == "tools"
                    else _gt_os.path.join(_gt_dir, "tools"))
# PB-1: the gate's temporary store is removed when the gate exits.
from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402
import types
from email import message_from_bytes
from email.policy import default as email_default
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from packet_fixture import FALSIFIER, PACKET_CLI, PACKET_FULL  # noqa: E402
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LINE = "=" * 78
PASS = FAIL = 0
ENDING = "2026-10-02"                       # a Friday; everything is synthetic
AS_OF = "2026-10-04T09:00:00+00:00"         # the Sunday edition's cutoff


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def weekdays(end: str, n: int) -> list[str]:
    d, out = dt.date.fromisoformat(end), []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d -= dt.timedelta(days=1)
    return list(reversed(out))


def seed(db: str, breakeven_jump: float = 0.12, cpi: bool = False) -> dict:
    import validate_stack as vs
    vs.SESSION = ENDING
    seeded = vs.seed(db, cpi_today=cpi)
    from altdata import observations, probability_ledger as pl
    days = weekdays(ENDING, 520)
    obs = []

    def put(key, inst, day, v):
        obs.append({"registry_key": key, "instrument": inst, "observed_at": day,
                    "available_at": f"{day}T22:00:00+00:00", "value": v,
                    "source": "synthetic"})
    # Rates and breakevens: last week and this week.
    for key, a, b in (("fred.breakeven_10y", 2.30, 2.30 + breakeven_jump),
                      ("fred.breakeven_5y", 2.20, 2.21),
                      # The 10- and 30-year end the week where the tape's bars
                      # do (4.289%, 4.789%): one instrument on one date prints
                      # one level (W-1.1a item 6, the alias check).
                      ("fred.yield_2y", 3.90, 3.95), ("fred.yield_10y", 4.00, 4.289),
                      ("fred.yield_30y", 4.50, 4.789), ("fred.hy_oas", 3.00, 3.10)):
        put(key, None, "2026-09-25", a)
        put(key, None, ENDING, b)
    for i, d in enumerate(days[-260:]):           # a year of rates for W3
        for key, base in (("fred.yield_2y", 3.9), ("fred.yield_10y", 4.0),
                          ("fred.yield_30y", 4.5), ("fred.hy_oas", 3.0)):
            if d < "2026-09-25":
                put(key, None, d, base + 0.001 * (i % 30))
    # CFTC: two years of Tuesdays.
    for i, d in enumerate(days[::5][-104:]):
        put("cftc.noncomm_net", "USD_INDEX", d, 10000 + 50 * (i % 20))
        put("cftc.noncomm_net", "JPY", d, -20000 + 300 * (i % 15))
    for sym, a, b in (("SPY", 2.0, 2.3), ("QQQ", 1.5, 1.4)):
        put("finra.short_interest_days_to_cover", sym, "2026-09-15", a)
        put("finra.short_interest_days_to_cover", sym, "2026-09-30", b)
    for d in days[-10:]:
        put("ndl.rtat10_sentiment", "SPY", d, 0.4 if d > "2026-09-27" else 0.1)
    put("apewisdom.mentions", "SPY@wallstreetbets", "2026-09-25", 120)
    put("apewisdom.mentions", "SPY@wallstreetbets", ENDING, 180)
    put("tic.flow_net_foreign", None, "2026-07-31", 45000)
    # Leadership: every sector and style leg, a week apart.
    for i, s in enumerate(("xlk", "xlf", "xle", "xlv", "xli", "xlp", "xly", "xlu",
                           "xlb", "xlre", "xlc", "ivw", "ive", "iwf", "iwd", "rsp",
                           "spy", "iwm")):
        put(f"yfinance.mkt_{s}", None, "2026-09-25", 100.0)
        put(f"yfinance.mkt_{s}", None, ENDING, 100.0 + (i % 7) - 3)
    with observations.ObservationStore(db) as st:
        st.write_many(obs)
    # The ledger: three resolved inside four weeks, one five weeks ago, outlooks.
    with pl.ProbabilityLedger(db) as led:
        def fc(src, p, emitted, resolved, outcome, n):
            pid = led.record(source=src, claim=f"fixture {src} {n}", probability=p,
                             emitted_at=emitted, horizon_date=resolved[:10],
                             resolution_criterion="fixture")
            led.resolve(pid, outcome, resolved_at=resolved)
        fc("narrative_register", 0.6, "2026-09-10T12:00:00+00:00",
           "2026-09-20T12:00:00+00:00", 1, 1)
        fc("narrative_register", 0.7, "2026-09-11T12:00:00+00:00",
           "2026-09-22T12:00:00+00:00", 0, 2)
        fc("daily_close_outlook", 0.8, "2026-09-28T21:00:00+00:00",
           "2026-09-29T21:00:00+00:00", 1, 3)
        fc("narrative_register", 0.9, "2026-08-01T12:00:00+00:00",
           "2026-08-28T12:00:00+00:00", 0, 4)
    # The register: two packets approved this week, one deferred by the budget.
    from register.store import Register
    from altdata import session as _sess
    base = dict(direction="long", thesis="t", edge_type="positioning",
                horizon="swing", invalidation="i", book="B", falsifiers=[FALSIFIER],
                counter_thesis="c", currency_exposure="unhedged", **PACKET_FULL)
    # THE CLOCK IS PINNED INSIDE THE FIXTURE WEEK. The register stamps created_at
    # from the real clock, so on any day after the fixture week these rows fell
    # outside it and the counts read 0 (first seen 5 Oct 2026, 00:00 UTC).
    real_now = _sess.utc_iso
    _sess.utc_iso = lambda timespec="seconds": f"{ENDING}T15:00:00+00:00"
    try:
        _seed_register(Register, db, base)
    finally:
        _sess.utc_iso = real_now
    return seeded


def _seed_register(Register, db, base) -> None:
    with Register(db) as reg:
        for k in range(2):
            d = reg.record(instrument="TEST@ARCA.USD", status="draft",
                           expression_currency="USD", **base)
            reg.supersede(d, instrument="TEST@ARCA.USD", status="active",
                          expression_currency="USD", **base)
        d = reg.record(instrument="TEST@ARCA.USD", status="draft",
                       expression_currency="USD", **base)
        reg.supersede(d, instrument="TEST@ARCA.USD", status="declined",
                      operator_action="DECLINE", abstention_reason="attention_budget",
                      expression_currency="USD", **base)


def payload(seeded: dict) -> dict:
    obj = seeded["market_state"]
    return {"report": "weekly_tactical", "week_ending": ENDING,
            "previous_week_ending": "2026-09-25",
            "sessions_in_week": weekdays(ENDING, 5), "as_of": AS_OF,
            "week_in_state": {"dials_now": {"gamma": "negative", "vol": "normal",
                                            "macro": "mixed"},
                              "dial_changes": [{"dial": "gamma", "from": "positive",
                                                "to": "negative"}],
                              "contradictions": [dict(c, open_state="open")
                                                 for c in obj["contradictions"]],
                              "exceptions_opened": ["extreme:fixture"],
                              "exceptions_intraweek_only": [],
                              "exceptions_open_now": ["extreme:fixture"]},
            "narratives": {"narratives": [{"id": "fixture_story", "name": "Fixture story",
                                           "state": "emerging", "evidence_for": 1,
                                           "evidence_against": 0}],
                           "proposals": []},
            "register": {"open_count": 2, "drafts_count": 0, "rule_breaks": {}},
            "week_ahead": {"releases": {"rows": [{"date": "2026-10-06",
                                                  "release_name": "Employment Situation"}]},
                           "session_events": {"2026-10-09": ["OPEX"]}},
            "grades": {}, "weekend_developments": {}, "warnings": []}


class Resp:
    def __init__(self, t):
        self.content = [types.SimpleNamespace(type="text", text=t)]
        self.model = "fixture-model"
        self.stop_reason = "end_turn"


# THE OPENER SHAPE (W-1.3a item 3.0): the scripted writer's reply is one
# paragraph inside every Weekly band (deep 120-220, medium 80-150) ending in its
# Takeaway, so the fixture's commentaries publish as a model's would.
OPENER_TEXT = ("The week left this section where it was. A reader new to the system can take "
        "the readings here as the plain record of where each market sat when the week "
        "closed, set beside where it sat a week earlier, so that a change shows up as a "
        "difference between two columns rather than as a judgement. Nothing in the week "
        "went far enough to alter how the readings fit together, and the relationships "
        "that held at the start of the week held at its end. The quiet was broad rather "
        "than confined to one corner of the market, and no single reading stood apart "
        "from the rest. Takeaway: with nothing pulling the readings apart, the coming "
        "week starts from the same footing, and a change would have to come from a "
        "scheduled event rather than from drift.")


def opener_text(tag: str) -> str:
    """An opener-shaped paragraph worded for one section (`tag`), so no two
    sections -- and not The read -- share a sentence the duplicate guard would
    withhold. Inside every Weekly band, no figure, ending in its Takeaway."""
    return (f"A reader new to the system can take the {tag} readings as the plain "
            f"record of where each market sat when the week closed, set beside "
            f"where it sat a week earlier, so that a change shows up as a "
            f"difference between two columns rather than as a judgement. Nothing "
            f"in the {tag} readings went far enough to alter how they fit together, "
            f"and the relationships that held at the start of the week in the {tag} "
            f"readings held at its end. The quiet in the {tag} readings was broad "
            f"rather than confined to one corner of the market, and no single one "
            f"of them stood apart from the rest. Takeaway: with nothing pulling the "
            f"{tag} readings apart, the coming week starts from the same footing, "
            f"and a change would have to come from a scheduled event rather than "
            f"from drift.")


def client(calls: list, text: str = OPENER_TEXT):
    def create(**k):
        calls.append(k["system"])
        return Resp(text)
    return types.SimpleNamespace(messages=types.SimpleNamespace(create=create))


def group_v(out: dict, td: str) -> None:
    """VP-1 item 7: the week's value-area table beside the levels, and W7's
    volume-at-price panel."""
    from altdata import bars as bars_mod, session
    from daily_cascade import charts as charts_mod
    print(f"\n{LINE}\nV. THE VOLUME PROFILE ON THE WEEKLY (VP-1 item 7)\n{LINE}")
    tape = next(s for s in out["edition"]["sections"] if s["id"] == "tape")
    titles = [ss.get("title") for ss in tape.get("subsections") or []]
    # The storyline (W-1.2) moves the Levels table to the detail tables, and the
    # value-area table follows it there, directly after it (ruled 14 Oct 2026,
    # 14:04 ET). What the profile could not compute stays in the tape's foot.
    detail = out["edition"].get("detail") or []
    dtitles = [d.get("title") for d in detail]
    VA = "The tape: value area, the week against the prior week"
    vt = next((d for d in detail if d.get("title") == VA), {})
    check((vt.get("table") or {}).get("columns") == [
              "Market", "Value area (POC)", "Prior week", "Migration",
              "Close vs value"]
          and [r[0] for r in vt["table"]["rows"]] == ["SPY", "QQQ", "IWM"],
          f"the detail tables carry the week against the prior week, one row per "
          f"instrument ({dtitles})")
    check("The tape: named levels" in dtitles and VA in dtitles
          and dtitles.index(VA) == dtitles.index("The tape: named levels") + 1,
          "beside the named levels: the value-area table directly after them")
    check(not any(str(t or "").startswith("Value area") for t in titles),
          f"and no longer in the tape section ({titles})")
    check(not tape.get("tables"),
          "and not the close's session table: the Weekly's is the week's")
    check(any(" week: " in x or " prior week: " in x
              for x in tape.get("not_tracked") or []),
          "a week the fixture does not store whole is not computed, with its "
          "reason, in the tape's own not-yet-tracked")
    html = out["html_archive"]
    i_lv, i_va = html.find("The tape: named levels"), html.find(VA)
    check(0 <= i_lv < i_va, "and the archive's HTML prints it after the named levels")
    # W7 over ten fixture sessions, two weeks: still one chart, one figure.
    days, d = [], dt.date.fromisoformat(ENDING)
    while len(days) < 10:
        if session.is_trading_session(d):
            days.insert(0, d.isoformat())
        d -= dt.timedelta(days=1)
    bars5 = []
    for k, day in enumerate(days):
        first, _, n = bars_mod.session_window("spy", day)
        t0 = dt.datetime.fromisoformat(first)
        for j in range(n):
            px = 640.0 + 1.5 * k + 0.8 * ((j % 11) - 5) / 5
            bars5.append({"observed_at": (t0 + dt.timedelta(minutes=5 * j)).isoformat(),
                          "open": px, "high": px + 0.3, "low": px - 0.3,
                          "close": px + 0.1, "volume": 5000 + 40 * (j % 13),
                          "available_at": f"{day}T21:00:00+00:00",
                          "source": "yfinance"})
    w7 = charts_mod.w7(bars5, {}, "w7_vp", str(Path(td) / "w7vp"))
    vap = w7.get("volume_at_price") or {}
    week = vap.get("week") or {}
    check(w7.get("png") and w7["png_bytes"] <= charts_mod.MAX_PNG_BYTES
          and w7.get("svg_path") and Path(w7["svg_path"]).exists(),
          f"W7 with its panel is still one chart, under the size cap "
          f"({w7.get('png_bytes')} bytes; {w7.get('unavailable')})")
    check(len(vap.get("week_sessions") or []) == 5 and vap.get("sessions") == 10,
          f"the panel covers the ten sessions W7 draws, this week's five apart "
          f"({vap.get('week_sessions')})")
    check(week.get("poc") is not None and week["val"] <= week["poc"] <= week["vah"],
          f"the week's POC is marked inside its value area ({week.get('poc')}, "
          f"{week.get('val')} to {week.get('vah')})")
    cap = w7.get("caption") or ""
    check("volume at price over the 10 sessions" in cap
          and f"POC {week.get('poc') or 0:,.2f}" in cap
          and "this week's 5 darker, the earlier 5 lighter" in cap,
          f"the caption is written from the data ({cap[cap.find('beside'):][:150]})")
    check((w7.get("min_px_at_400") or 0) >= charts_mod.MIN_PX_AT_400,
          f"and the mobile rule holds: no text under {charts_mod.MIN_PX_AT_400} px "
          f"at 400 px ({w7.get('min_px_at_400')})")


def main() -> int:
    from altdata import config, bars as bars_mod
    from daily_cascade import deliver, stack as stack_mod, stack_prose, stack_render
    from daily_cascade import charts as charts_mod, weekly_stack as ws
    print(f"{LINE}\nThe ten-section stack on the Weekly (T2) -- synthetic week ending "
          f"{ENDING}\n{LINE}")
    td = gate_mkdtemp(prefix="validate_weekly_stack_")
    config.COMPUTED_DIR = str(Path(td) / "computed")
    db = str(Path(td) / "weekly.db")
    arch = str(Path(td) / "reports")
    logp = Path(td) / "attention-log.md"
    logp.write_text(
        "| date | kind | minutes | note |\n|---|---|---|---|\n"
        "| 2026-09-30 | sitting | 45 | fixture sitting |\n"
        "| 2026-10-01 | ruling | — | fixture ruling |\n"
        "| 2026-10-03 | ruling | 5 | fixture ruling, Saturday |\n"
        "| 2026-10-05 | ruling | — | next week: not counted |\n", encoding="utf-8")
    seeded = seed(db)
    p = payload(seeded)
    calls: list = []
    out = ws.produce(p, archive_dir=arch, client=client(calls), db_path=db,
                     log_path=logp)
    ed = out["edition"]
    sec = {s["id"]: s for s in ed["sections"]}

    # --- A. STACK --------------------------------------------------------------
    print(f"\n{LINE}\nA. THE STACK AT THE WEEKLY'S DEPTHS\n{LINE}")
    check([s["id"] for s in ed["sections"]] == list(stack_mod.SECTION_ORDER),
          "ten sections in the brief's order")
    want = {"read": "deep", "tape": "deep", "mechanics": "medium", "misfit": "deep",
            "plumbing": "medium", "positioning": "deep", "narratives": "medium",
            "ahead": "deep", "book": "medium"}
    got = {k: sec[k]["depth"] for k in want}
    check(got == want, f"the matrix's Weekly column ({got})")
    check(sec["priced"]["depth"] == "deep"
          and "on the week" in (sec["priced"]["depth_reason"] or ""),
          f"What's priced goes deep on the week's 12 bp breakeven move "
          f"({sec['priced']['depth_reason']})")
    db2 = str(Path(td) / "quiet.db")
    s2 = seed(db2, breakeven_jump=0.02)
    ed_q, _ = ws.build(payload(s2), ws.levels_mod.compute(
        ENDING, [], store=bars_mod.BarStore(db2)), None, db2, logp)
    pq = next(s for s in ed_q["sections"] if s["id"] == "priced")
    check(pq["depth"] == "medium" and not pq.get("depth_reason"),
          "and stays medium on a 2 bp week")
    ws.save_edition(ed, ENDING, arch)
    # The next Sunday, nothing changed: compared with the prior WEEKLY.
    p_next = dict(p, week_ending="2026-10-09", previous_week_ending=ENDING)
    prior = ws.load_prior(ENDING, arch)
    with bars_mod.BarStore(db) as bst:
        book = ws.levels_mod.compute(ENDING, [], store=bst)
    ed2, _ = ws.build(dict(p_next, week_ending=ENDING), book, prior, db, logp)
    mech = next(s for s in ed2["sections"] if s["id"] == "mechanics")
    check(mech["collapsed"] and mech["unchanged_since"] == ENDING,
          "an unchanged section collapses against the prior WEEKLY edition")
    check(ws.load_prior("2026-09-30", arch) is None and not Path(arch, ws.edition_name(
          "2026-09-30")).exists(),
          "and a daily edition is never read as the prior Weekly")
    p_mv = json.loads(json.dumps(p))
    p_mv["week_in_state"]["dial_changes"] = [{"dial": "vol", "from": "normal",
                                              "to": "elevated"}]
    ed3, _ = ws.build(p_mv, book, prior, db, logp)
    m3 = next(s for s in ed3["sections"] if s["id"] == "mechanics")
    check(not m3["collapsed"] and any(i["changed"] for i in m3["items"]),
          "a new dial change marks its line with ◆")

    # --- B. LEVELS ---------------------------------------------------------------
    print(f"\n{LINE}\nB. LEVELS\n{LINE}")
    listed = {(lv["label"], lv["value"]) for i in ed["levels"]["instruments"]
              for lv in i["levels"]}
    drawn = [d for k in ("W1", "W2") for d in out["charts"][k].get("drawn") or []]
    check(drawn and all((d["label"], d["value"]) in listed for d in drawn),
          f"every level W1 and W2 draw ({len(drawn)}) is in the level list")
    prose = " ".join((s.get("claim") or "") + " ".join(s.get("paragraphs") or [])
                     for s in ed["sections"])
    check(not stack_prose.prose_levels(prose, ed["levels"]),
          "the prose names no level the list does not hold")

    # --- C. PROSE ------------------------------------------------------------------
    print(f"\n{LINE}\nC. PROSE IN THE WEEKLY'S FRAMES\n{LINE}")
    sec_calls = [c for c in calls if "THE SECTION:" in c]
    check(len(sec_calls) == 9 and all("ONE SECTION of\nthe Weekly" in c
                                      or "ONE SECTION of the Weekly" in c for c in sec_calls)
          and all("the week as a whole" in c for c in sec_calls),
          f"one audited call per section, written as the Weekly in its frames "
          f"({len(sec_calls)} calls)")
    check(any("about the week" in c for c in calls if "Write THE READ" in c),
          "and The read is about the week")

    # --- D. CHARTS -------------------------------------------------------------------
    print(f"\n{LINE}\nD. CHARTS W1-W6\n{LINE}")
    for k in ("W1", "W2", "W3", "W4", "W5", "W6"):
        c = out["charts"].get(k) or {}
        check(c.get("png") and c["png"][:4] == b"\x89PNG"
              and c["png_bytes"] <= charts_mod.MAX_PNG_BYTES
              and c.get("svg_path") and Path(c["svg_path"]).exists(),
              f"{k} renders to PNG ({c.get('png_bytes')} bytes) and SVG -- "
              f"{str(c.get('caption') or c.get('unavailable'))[:70]}")
    cids = set(re.findall(r'src="cid:([^"]+)"', out["html_email"]))
    msg = deliver.build_message({"user": "a@x.invalid", "rcpt": "b@x.invalid"}, "s",
                                out["html_email"], "t",
                                inline_images=out["inline_images"])
    parts = {str(pp.get("Content-ID", "")).strip("<>")
             for pp in message_from_bytes(msg.as_bytes(), policy=email_default).walk()
             if pp.get_content_type() == "image/png"}
    check(cids and cids == parts and len(cids) == ed["chart_count"],
          f"the Content-ID set matches the charts in the body ({sorted(cids)})")
    # BATCH 8 ITEM 51: the Digital Assets addendum's one line -- absent when the
    # run carries no addendum, one line when it does (validate_digital_addendum.py
    # holds the page itself).
    check("Digital Assets addendum" not in out["html_email"],
          "without an addendum the Weekly prints no addendum line")
    pa = {**p, "addendum": {"state": "built", "name": f"weekly_digital_{ENDING}.html",
                            "minutes": 4}}
    wa = ws.render(pa, ed, out["charts"], "email")
    check(f"Digital Assets addendum, about 4 minutes: weekly_digital_{ENDING}.html, "
          f"attached to this message." in wa
          and wa.count("Digital Assets addendum") == 1,
          "with one, the Weekly gains exactly one line naming the attached page")
    bad = charts_mod.bars_chart("W5", [], "x", "x", None)
    check(bad.get("unavailable") and "chart unavailable" in
          stack_render._chart_html(bad, "email").lower(),
          f"a chart that cannot render prints its reason ({bad['unavailable']})")
    check(out["charts"]["W2"]["caption"].startswith("SPY, ") and "weekly bars"
          in out["charts"]["W2"]["caption"],
          f"W2's caption is written from the data ({out['charts']['W2']['caption'][:70]})")

    # --- E. POSITIONING --------------------------------------------------------------
    print(f"\n{LINE}\nE. POSITIONING & FLOWS, DEEP\n{LINE}")
    keys = [i["key"] for i in sec["positioning"]["items"]]
    for pre, what in (("pos:cftc:", "CFTC"), ("pos:si:", "FINRA short interest"),
                      ("pos:rtat:", "RTAT10"), ("pos:ape:", "ApeWisdom"),
                      ("pos:tic.", "TIC"), ("pos:leadership", "leadership"),
                      ("pos:style:", "style pairs")):
        check(any(k.startswith(pre) for k in keys), f"{what} is in the section")

    # --- F. GRADED CALLS -----------------------------------------------------------
    print(f"\n{LINE}\nF. THE GRADED-CALLS TABLE\n{LINE}")
    gc = sec["ahead"]["data"]["graded_calls"]
    by = {r["source"]: r for r in gc["rows"]}
    check(by.get("narrative_register", {}).get("n") == 2,
          "Brier by source over four weeks: the call resolved five weeks ago is out")
    nr = by["narrative_register"]["mean_brier"]
    check(abs(nr - ((0.4 ** 2 + 0.7 ** 2) / 2)) < 1e-9,
          f"the mean Brier is the ledger's own ({nr})")
    texts = [i["text"] for i in sec["ahead"]["items"]]
    check(any(t.startswith("Base-rate outlooks, last four weeks: n=1") for t in texts)
          and not any("daily_close_outlook" in t for t in texts
                      if t.startswith("Graded calls")),
          "the base-rate outlooks have their own line, not the graded calls'")

    # --- G. ATTENTION ----------------------------------------------------------------
    print(f"\n{LINE}\nG. THE ATTENTION COUNTS AND THE TRIGGERS\n{LINE}")
    a = sec["book"]["data"]["attention"]
    check(a["packets_approved"] == 2 and a["packets_budget"] == 7,
          f"packets approved {a['packets_approved']} of 7, from the register")
    check(a["packets_deferred_attention_budget"] == 1,
          "a deferral recorded with the attention_budget reason is counted")
    check(a["sitting_hours"] == 0.75 and a["rulings"] == 2,
          f"sitting hours {a['sitting_hours']} of 2 and {a['rulings']} rulings from "
          f"the log, Saturday included, next Monday not")
    from register.store import Register
    with Register(str(Path(td) / "abst.db")) as reg:
        try:
            reg.record(instrument="TEST@ARCA.USD", direction="long", thesis="t",
                       edge_type="positioning", horizon="swing", invalidation="i",
                       status="active", book="B", falsifiers=["f"],
                       counter_thesis="c", abstention_reason="attention_budget")
            ok_refused = False
        except ValueError:
            ok_refused = True
    check(ok_refused, "an abstention reason belongs on a declined row only")
    t = sec["book"]["data"]["triggers"]
    check(t["sessions"] == 5 and isinstance(t["plumbing"], list)
          and any(x["key"] == "book:triggers" for x in sec["book"]["items"]),
          f"each trigger's firing count for the week: plumbing "
          f"{len(t['plumbing'])}, priced {len(t['priced'])} of 5")
    db4 = str(Path(td) / "cpi.db")
    seed(db4, cpi=True)
    from altdata import observations as _obs
    with _obs.ObservationStore(db4) as st4:
        t4 = ws.trigger_counts(weekdays(ENDING, 5), st4, stack_mod.config())
    fired = [x["session"] for x in t4["plumbing"]]
    check(fired == ["2026-10-02"],
          f"a CPI release knowable only from Friday counts Plumbing deep on Friday "
          f"alone -- each session is judged at its own cutoff, never with "
          f"hindsight ({fired})")
    # W-1.3c finding 9: a code gate never reads the live store. book_week with no
    # db_path sent the Book B scanner to observations.DEFAULT_DB (the laptop's
    # data/chester.db). Every SQLite file the call opens is recorded, and the
    # default store is pointed at a sentinel so even the old call cannot read it.
    import sqlite3 as _sq
    from altdata import observations as _obs_mod
    _opened: list[str] = []
    _real_connect = _sq.connect

    def _spy_connect(path, *a_, **k_):
        # Recorded, and refused outside the gate's own directory: the probe of
        # the old call must not itself open the laptop's store.
        _opened.append(str(path))
        if str(path) != ":memory:" and not Path(str(path)).resolve().is_relative_to(
                Path(td).resolve()):
            raise _sq.OperationalError(f"gate refuses a store outside its tmp: {path}")
        return _real_connect(path, *a_, **k_)

    def _book_week_paths(db_path):
        _opened.clear()
        sentinel = str(Path(td) / "DEFAULT_DB_SENTINEL.db")
        saved = _obs_mod.DEFAULT_DB
        _obs_mod.DEFAULT_DB, _sq.connect = sentinel, _spy_connect
        try:
            out_ = ws.book_week({"register": {"open_count": 0, "drafts_count": 0,
                "rule_breaks": {"decision_blocked_this_week": 2, "rule_breaks_total": 5,
                                "rule_breaks_listed": [{"kind": "currency_mismatch"}]}}},
                a, {"plumbing": [], "priced": [], "sessions": 5}, None,
                ending=ENDING, db_path=db_path)
        finally:
            _obs_mod.DEFAULT_DB, _sq.connect = saved, _real_connect
        return out_, [p_ for p_ in _opened if p_ != ":memory:"], sentinel

    _, old_paths, sentinel = _book_week_paths(None)
    live = [p_ for p_ in old_paths
            if not Path(p_).resolve().is_relative_to(Path(td).resolve())]
    check(sentinel in old_paths or bool(live),
          f"the old call (no db_path) reaches the default store -- the fault this "
          f"fixture exists to catch ({old_paths})")
    book_db = str(Path(td) / "book_week.db")
    bk, new_paths, _ = _book_week_paths(book_db)
    check(new_paths and all(Path(p_).resolve().is_relative_to(Path(td).resolve())
                            for p_ in new_paths) and sentinel not in new_paths,
          f"book_week with an explicit temporary db_path opens only the gate's own "
          f"files, never the default store ({new_paths})")
    bt = {i["key"]: i["text"] for i in bk["items"]}
    check(bt["book:breaks"].startswith("1 rule break(s) this week (currency mismatch); "
                                        "5 on the register")
          and bt.get("book:blocked", "").startswith("2 decision(s) blocked"),
          "the week's rule breaks are the listed ones, never summed with the running "
          "total or the blocked count")
    legs = [{"venue": "kalshi", "event_id": "CPI-X", "instrument": f"kalshi:CPI-X-{k}",
             "question": f"leg {k}", "probability": 0.5, "change_5s_points": c}
            for k, c in (("a", 13.5), ("b", -27.5), ("c", 11.0))]
    rw = ws.read_week({"markets": legs})
    check(len(rw["items"]) == 1 and "27.5 pts" in rw["items"][0]["text"],
          "The read carries one line per venue event: its largest five-session move")
    # --- T2 RULINGS (3 Oct 2026) -------------------------------------------------
    from altdata import benchmark, observations as _o
    db5 = str(Path(td) / "bookz.db")
    with _o.ObservationStore(db5) as st5:
        rows5 = []
        for ld, v0, v1 in (("cash", 100.0, 100.4), ("spy", 100.0, 101.0),
                           ("sixty_forty", 100.0, 99.5)):
            for day, v in (("2026-09-01", 100.0), ("2026-09-05", v0), (ENDING, v1)):
                rows5.append({"registry_key": benchmark.KEY, "instrument": ld,
                              "observed_at": day,
                              "available_at": f"{day}T21:00:00+00:00",
                              "value": json.dumps({"value": v, "session": day,
                                                   "start": "2026-09-01"}),
                              "source": "derived_state"})
        for day, nav in (("2026-09-05", 1000.0), (ENDING, 1012.0)):
            rows5.append({"registry_key": "portfolio.nav", "instrument": None,
                          "observed_at": f"{day}T20:00:00+00:00",
                          "available_at": f"{day}T20:00:00+00:00", "value": nav,
                          "source": "ibkr_paper"})
        st5.write_many(rows5)
        bl = benchmark.book_line(AS_OF, st5)
    check(bl["book_pct"] == 1.2 and bl["benchmarks_pct"] == {"cash": 0.4, "spy": 1.0,
                                                             "sixty_forty": -0.5}
          and bl["excess_pts"] == {"cash": 0.8, "spy": 0.2, "sixty_forty": 1.7}
          and bl["window_start"] == "2026-09-05",
          f"Book Z: the book's return and each benchmark's over the SAME window "
          f"(from the first NAV), then the excess in points ({bl['text']})")
    check("the book +1.20%" in bl["text"] and "excess vs cash / SPY / 60-40: "
          "+0.80 / +0.20 / +1.70 pts" in bl["text"],
          "printed as labelled absolutes, then the excess")
    check(stack_prose.excess_faults("The book returned +1.2% against cash at +0.4%.")
          and not stack_prose.excess_faults("The book's +1.2% is an excess of +0.8 pts "
                                            "relative to cash."),
          "the prose check refuses a vs-figure without 'excess' or 'relative to'")
    check(stack_prose.policy_word_faults("Kalshi's CPI market moved toward a hike.")
          and not stack_prose.policy_word_faults("Kalshi prices a hike at the "
                                                 "October meeting at 19%.")
          and not stack_prose.policy_word_faults("The week's low holds at 515.06."),
          "a policy word attached to a CPI market is withheld; the FOMC item and a "
          "level that holds are not")
    pt = {i["key"]: i["text"] for i in sec["plumbing"]["items"]}
    y10 = pt.get("plumb:fred.yield_10y", "")
    check("Friday to Friday" in y10 and "FRED" in y10,
          f"Plumbing's 10-year week change is the bars' Friday to Friday, FRED "
          f"labelled with its own as-of ({y10[:90]})")
    # The section's footnote and its sub-sections' (T2.5: the CFTC sub-section
    # lists the contracts once; the section no longer repeats them).
    nt = " ".join(sec["positioning"]["not_tracked"]
                  + [x for ss in sec["positioning"].get("subsections") or []
                     for x in ss.get("not_tracked") or []])
    check("S&P 500 futures" in nt and "10-year note futures" in nt
          and "VIX futures" in nt and "Yen futures" not in nt,
          "CFTC contracts not yet stored print as not yet tracked, by name")
    from altdata.sources import cftc
    check({"13874+": "SP500", "043602": "UST10Y", "1170E1": "VIX"}.items()
          <= cftc.CONTRACTS.items(),
          "the CFTC feed carries S&P 500 consolidated, the 10-year note and VIX")
    ag = (REPO / "docs" / "attention-log.md").read_text(encoding="utf-8")
    check("| 2026-10-02 | sitting | 22 |" in ag and ws.read_attention_log()
          and all(e["kind"] in ("sitting", "ruling") for e in ws.read_attention_log()),
          "docs/attention-log.md holds the 2 Oct sitting at 22 minutes, and parses")

    # --- T2.1 (4 Oct 2026): defects from the first live stacked Weekly ------------
    print(f"\n{LINE}\nT2.1 THE FIRST LIVE WEEKLY'S DEFECTS\n{LINE}")
    import inspect as _insp
    from altdata import bars as _bars, labels as _labels, levels as _lv
    from altdata.numeral_audit import scaled_display
    from daily_cascade import stack as _st, stack_prose as _sp
    spy_i = next(i for i in ed["levels"]["instruments"] if i["id"] == "spy")
    check(spy_i["daily_source"]["key"] == "yfinance.mkt_spy"
          and not spy_i["daily_source"]["proxy"] and spy_i.get("frame", {}).get("last"),
          "1: the tape's daily frames read the store's daily series (yfinance.mkt_spy)")
    rows_fb, meta_fb = _lv.daily_bars({"id": "x", "daily": "yfinance.mkt_none",
                                       "fallback": {"daily": "yfinance.mkt_spy",
                                                    "label": "SPY"}}, ENDING,
                                      None, _o.ObservationStore(db))
    check(rows_fb and meta_fb["proxy"] == "SPY",
          "1: a proxy is read only when the instrument's own series is empty, and named")
    check("interval=\"1d\"" not in _insp.getsource(_bars.pull)
          and "def daily(" not in _insp.getsource(_bars),
          "1: the eod bars feed pulls the session's 5-minute bars only")
    w4 = out["charts"]["W4"].get("caption") or ""
    check(w4.count("Speculative positioning") == 1,
          f"2: a chart caption prints its words once ({w4[:80]})")
    every = " ".join([s.get("claim") or "" for s in ed["sections"]]
                     + [" ".join(s.get("paragraphs") or []) for s in ed["sections"]]
                     + [i["text"] for s in ed["sections"] for i in s["items"]]
                     + [" ".join(map(str, r)) for s in ed["sections"]
                        for r in (s.get("table") or {}).get("rows") or []])
    ids = re.findall(r"\b(?:extreme|contradiction):\S+|\b(?:fred|calc|yfinance)\.\w+"
                     r"|\b(?:equities_vs_credit|long_bond_vs_hy|fixture_pair|"
                     r"narrative_register|daily_close_outlook)\b", every)
    check(not ids, f"3: no internal id in any section's text or table ({ids[:4]})")
    ms_ids = re.findall(r"\b(?:fred|calc|yfinance|dial|pm)\.[a-z0-9_]+",
                        (REPO / "config" / "market_state.yaml").read_text(encoding="utf-8"))
    check(not _labels.missing(sorted(set(ms_ids))),
          f"3: every metric the market state can name has a display label "
          f"({_labels.missing(sorted(set(ms_ids)))[:4]})")
    pm_rows = [{"venue": v, "watch_id": "us_recession", "event_id": f"E-{v}",
                "question": "Recession in 2026?", "outcome": "Yes",
                "probability": 0.04, "change_1s_points": -2.5, "bias_zone": True,
                "close_at": "2026-12-31"} for v in ("kalshi", "polymarket")]
    cpi_rows = [{"venue": "kalshi", "watch_id": "cpi_monthly", "event_id": "K",
                 "question": "Will CPI rise more than 0.3%?", "outcome": "Above 0.3%",
                 "probability": 0.18, "change_1s_points": 1.0, "volume": 10},
                {"venue": "polymarket", "watch_id": "cpi_monthly", "event_id": "P",
                 "question": "CPI 2.4% in December?", "outcome": "2.4%",
                 "probability": 0.36, "change_1s_points": -3.5, "volume": 10}]
    vi = _st.venue_items({"watch": {"us_recession": pm_rows, "cpi_monthly": cpi_rows}},
                         None)
    vt = [i["text"] for i in vi]
    check(any(t.startswith("US recession in 2026 and in 2027 (Yes): Kalshi 4%") for t in vt),
          "5: an item prints its declared side for both venues on one line")
    check(sum(1 for t in vt if t.startswith("Each month's CPI print --")) == 2
          and any("Will CPI rise more than 0.3%?" in t for t in vt),
          "5: the CPI item prints each venue's market by its own title, never paired")
    # W-1.1 item 1.5: the rule is the favourite-longshot check, a flag.
    check(all("bias zone" not in t for t in vt) and any("outside 10-90%" in t for t in vt)
          and any("favourite–longshot check" in t for t in vt)
          and _st.BIAS_LEGEND.startswith("Favourite–longshot check (outside 10-90%)"),
          "3: the bias zone is in plain words -- the favourite-longshot check -- with "
          "a one-line legend")
    check(not _sp.policy_word_faults("The CPI market holds near 0.3%, and the low held.")
          and _sp.policy_word_faults("The Fed holds at the October meeting, says the "
                                     "CPI market."),
          "6: 'hold' counts only with Fed, FOMC or meeting in its clause")
    c_line = _st.contradiction_line({"id": "equities_vs_credit", "persistence_days": 5,
                                     "magnitude": 3.0054, "threshold_z": 2.0})
    check("z +3.0 against a threshold of 2.0" in c_line
          and c_line.startswith("Equities against high-yield credit"),
          f"7: z to one decimal, under its label ({c_line})")
    check(_st._signed(4.4, "bp") == "+4 bp" and _st._signed(-0.4, "bp") == "0 bp",
          "7: basis points whole, and a move that rounds to zero carries no sign "
          "(weekly-fixes-7 item 12)")
    check(scaled_display(-68522000000.0, "usd") == "−$68.52bn",
          "7: TIC in billions through the scaled display")
    sp = _sp.stack_system_prompt(__import__("daily_cascade.narrative",
                                            fromlist=["x"]))
    check("END ON THE SYSTEM" not in sp and "Only the Ahead" in sp
          and _sp.style_faults("For the system, the week held.",
                               _bars.load_config()),
          "8: no section closes on the system; 'For the system' is a banned phrase")
    pos_calls = [c for c in calls if "THE SECTION: Positioning & flows." in c]
    # T2.5 item 2 (ruled 5 Oct 2026) replaced T2.2 item 7's tagged paragraph
    # per sub-section: one paragraph across every sub-section's table.
    check(pos_calls and "ONE paragraph" in pos_calls[0]
          and "[A]" not in pos_calls[0]
          and "across the sub-sections' tables" in pos_calls[0],
          "9: Positioning's prose is asked for ONE paragraph across its "
          "sub-sections' tables, untagged (T2.5 item 2)")
    sl = _sp._slice(sec["misfit"], ed)
    check("not_tracked" not in sl and "_id" not in json.dumps(sl),
          "10: a prose slice carries no not-yet-tracked list and no id")
    html = out["html_archive"]
    check(">Detail<" not in html and sec["misfit"].get("table", {}).get("rows") is not None
          and any(i["key"] == "ahead:calls" for i in sec["ahead"]["items"])
          and any(i["key"].startswith("mech:") for i in sec["mechanics"]["items"]),
          "11: the Detail tail is gone; its blocks live in their sections")
    with _o.ObservationStore(str(Path(td) / "nav.db")) as stn:
        stn.write_many(rows5[:-2] + [dict(r, instrument="DU0000") for r in rows5[-2:]])
        bln = benchmark.book_line(AS_OF, stn)
    check(bln["book_pct"] == 1.2,
          "12: the book's return reads the NAV keyed to the account (the 4 Oct miss)")
    with _o.ObservationStore(str(Path(td) / "rel.db")) as str_:
        str_.write_many([{"registry_key": "fred.nfp", "instrument": None,
                          "observed_at": d, "available_at": f"{d}T13:00:00+00:00",
                          "value": v, "source": "synthetic"}
                         for d, v in (("2026-08-01", 159000.0), ("2026-09-01", 159150.0))])
        from altdata import events as _ev
        with _ev.EventStore(str(Path(td) / "rel.db")) as evs:
            evs.conn.execute(
                "INSERT INTO events (content_hash, type, observed_at, available_at,"
                " ingested_at, source, title, payload) VALUES (?,?,?,?,?,?,?,?)",
                ("rel-1", "release", "2026-10-02T12:30:00+00:00",
                 "2026-10-02T12:30:00+00:00", "2026-10-02T12:31:00+00:00",
                 "fred_releases", "Employment Situation -- release date",
                 json.dumps({"series": ["nfp"]})))
            evs.conn.commit()
        rel = ws.tier1_releases(str_, AS_OF, ws.week_ago(AS_OF))
    # Rulings of 5 Oct, item 1: payrolls print as the monthly change, under the
    # declared label, never the raw series name. T3.4a: in the one change form
    # every report shares -- +150 thousand prints "+150,000 jobs" (T3.5), which
    # the audit accepts as the display form.
    check(rel and rel[0]["release"] == "Employment Situation"
          and rel[0]["form"] == "change" and rel[0]["actual"] == 150.0
          and rel[0]["actual_text"] == "+150,000 jobs"
          and rel[0]["label"] == "nonfarm payrolls, monthly change"
          and rel[0]["as_of"] == "2026-09-01",
          f"13: Plumbing lists the week's tier-1 release in its declared form, with "
          f"actual, prior and as-of ({rel[:1]})")
    from altdata import config as _cfg
    ids_be = {s.key: s.fred_id for s in _cfg.FRED_PULL_SERIES if "breakeven" in s.key}
    pr_items = [i["text"] for i in sec["priced"]["items"] if "breakeven" in i["text"]]
    check(len(set(ids_be.values())) == len(ids_be) == 3
          # The window in prose reads "25 Sep to 2 Oct" (T2.5 item 6).
          and any("on the week (25 Sep to 2 Oct)" in t for t in pr_items),
          f"14: the breakevens are three distinct series, and the week's change "
          f"prints its real window ({pr_items[:1]})")

    # --- H. BUDGET -------------------------------------------------------------------
    print(f"\n{LINE}\nH. BUDGET\n{LINE}")
    check(ed["budget"] == {"words": 7900, "charts": 10} and ed["words"] <= 7900
          and ed["chart_count"] <= 11 and ed.get("reading_target_minutes") == 35,
          f"the Weekly's target is 35 minutes, 7,900 words of prose / 10 charts "
          f"(D19/D20; {ed['words']} words, {ed['chart_count']} charts; a fired "
          f"trigger lifts the chart cap by one)")
    e = json.loads(json.dumps(ed))
    deep = next(s for s in e["sections"] if s["depth"] == "deep" and s.get("claim"))
    deep["paragraphs"] = ["Prose printed in full past the target. " * 900] * 3
    paras = list(deep["paragraphs"])
    n_items = sum(len(s["items"]) for s in e["sections"])
    e["reading_target_minutes"] = None
    stack_mod.enforce_budget(e, "weekly")
    check(deep["paragraphs"] == paras and not deep.get("trimmed")
          and sum(len(s["items"]) for s in e["sections"]) == n_items
          and e["reading_target_minutes"] == 35
          and str(e.get("target_line") or "").endswith("against a 35-minute target."),
          f"over its 35-minute target the Weekly prints every paragraph and item in "
          f"full and one foot line (D19/D20): {e.get('target_line')!r}")

    group_v(out, td)

    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
