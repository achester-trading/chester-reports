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
  H BUDGET     <= 3,500 words and <= 6 charts; over budget prints "(trimmed)".
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import tempfile
import types
from email import message_from_bytes
from email.policy import default as email_default
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
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
                      ("fred.yield_2y", 3.90, 3.95), ("fred.yield_10y", 4.00, 4.06),
                      ("fred.yield_30y", 4.50, 4.53), ("fred.hy_oas", 3.00, 3.10)):
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
    base = dict(direction="long", thesis="t", edge_type="positioning",
                horizon="swing", invalidation="i", book="B", falsifiers=["f"],
                counter_thesis="c", currency_exposure="unhedged")
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
    return seeded


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


def client(calls: list, text: str = "The week left this section where it was."):
    def create(**k):
        calls.append(k["system"])
        return Resp(text)
    return types.SimpleNamespace(messages=types.SimpleNamespace(create=create))


def main() -> int:
    from altdata import config, bars as bars_mod
    from daily_cascade import deliver, stack as stack_mod, stack_prose, stack_render
    from daily_cascade import charts as charts_mod, weekly_stack as ws
    print(f"{LINE}\nThe ten-section stack on the Weekly (T2) -- synthetic week ending "
          f"{ENDING}\n{LINE}")
    td = tempfile.mkdtemp(prefix="validate_weekly_stack_")
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
    check(len(cids) == 6 and cids == parts,
          f"the Content-ID set matches the six charts in the body ({sorted(cids)})")
    bad = charts_mod.bars_chart("W5", [], "x", "x", None)
    check(bad.get("unavailable") and "chart unavailable" in
          stack_render._chart_html(bad, "email"),
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
    bk = ws.book_week({"register": {"open_count": 0, "drafts_count": 0, "rule_breaks": {
        "decision_blocked_this_week": 2, "rule_breaks_total": 5,
        "rule_breaks_listed": [{"kind": "currency_mismatch"}]}}},
        a, {"plumbing": [], "priced": [], "sessions": 5}, None)
    bt = {i["key"]: i["text"] for i in bk["items"]}
    check(bt["book:breaks"].startswith("1 rule break(s) this week (currency_mismatch); "
                                        "5 on the register")
          and bt.get("book:blocked", "").startswith("2 decision(s) blocked"),
          "the week's rule breaks are the listed ones, never summed with the running "
          "total or the blocked count")
    legs = [{"venue": "kalshi", "event_id": "CPI-X", "instrument": f"kalshi:CPI-X-{k}",
             "question": f"leg {k}", "probability": 0.5, "change_5s_points": c}
            for k, c in (("a", 13.5), ("b", -27.5), ("c", 11.0))]
    rw = ws.read_week({"markets": legs})
    check(len(rw["items"]) == 1 and "-27.5 pts" in rw["items"][0]["text"],
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
    nt = " ".join(sec["positioning"]["not_tracked"])
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

    # --- H. BUDGET -------------------------------------------------------------------
    print(f"\n{LINE}\nH. BUDGET\n{LINE}")
    check(ed["budget"] == {"words": 3500, "charts": 6} and ed["words"] <= 3500
          and ed["chart_count"] <= 7,
          f"the Weekly's budget is 3,500 words / 6 charts ({ed['words']} words, "
          f"{ed['chart_count']} charts; a fired trigger lifts the cap by one)")
    e = json.loads(json.dumps(ed))
    before = sum(stack_mod.section_words(s) for s in e["sections"])
    e["budget"] = {"words": before - 40, "charts": 6}
    stack_mod.enforce_budget(e)
    check(any(s["trimmed"] for s in e["sections"]) and e["words"] <= before - 40,
          "over budget, low-priority lines go and the section prints \"(trimmed)\"")

    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
