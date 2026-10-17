"""
Validation gate for W-1.3a items 3.6-3.9 -- the Weekly's Ahead calendar, Book B's
candidates, the book's productivity line, the glossary's stamp and the technical
appendix (change order of 11 Oct 2026, section 4, amended 12 Oct). On the
Weekly's fixture payload with a scripted writer and synthetic register rows; no
network, no box, no register write (the register rows are dicts in memory).

  A  AHEAD, ONE RANKED TABLE (3.9). Six columns: when (ET), the event, its
     importance tier, the consensus or modal outcome, why it matters (the
     class's channel) and the positioning that would amplify a surprise. Ranked
     by the config tier, then time. Earnings print with their session, the
     consensus EPS and the implied move where a chain is captured ("not
     captured" otherwise), classed mega / bank / tracked by config. Where the source
     carries a release time the session prints pre- or post-market; a bare date
     prints "release time not captured" (W-1.3c item 9). Routine
     releases and bill auctions go to the reference tables, counted. The
     top playbook-class event keeps the playbook slot.
  B  AHEAD'S OTHER SOURCES. A family of prediction-market resolutions collapses
     to its modal outcome; the hand-seeded calendars and the claims register's
     dated events print when in the window; a calendar file not present is
     named; an index rebalance prints; an amplifier is a contract at |z| >= the
     threshold, read from the Positioning section's own rows.
  C  CANDIDATES FOR THE SITTING (PAPER) (3.8). The Book B scanner runs inside
     the build and the block prints its result (its forecasts, in a dry run,
     in the dry-run namespace); against the scanner's own candidates over a
     synthetic store, the list is ranked by its score, one line each with every
     field; a
     candidate with no register draft or on a restricted instrument never
     prints; a candidate the prior sitting passed over prints once with its
     reason and is not carried forward.
  D  THE PRODUCTIVITY LINE (3.6). Four counts, fired -> reviewed -> drafted ->
     approved; a passed-over row for every reviewed signal with no approval,
     its reason from the register or "no reason recorded"; the decisions count
     captioned as register decisions.
  E  THE GLOSSARY AND THE APPENDIX (3.7). The definitions-version stamp; the
     technical appendix in the reference tier with the GEX/DEX universe and the
     expiry coverage; the unvalidated and validated tags distinct (n >= 30).

    python tools/validate_weekly_calendar.py
"""

from __future__ import annotations

import datetime as dt
import os
import sys
import types
from pathlib import Path

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import validate_weekly_stack as W                              # noqa: E402

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


MON = "2026-10-05"                    # the Monday after the fixture's week


def day(k: int) -> str:
    return (dt.date.fromisoformat(MON) + dt.timedelta(days=k)).isoformat()


def release_at_captured() -> bool:
    """W-1.3c item 9 at the source: a fake yfinance whose calendar gives a bare
    date and whose earnings-dates table gives the unreported row a time."""
    import datetime as _dt
    import types as _types
    import pandas as pd
    import altdata
    from altdata.sources import earnings

    def ticker(with_time: bool):
        idx = pd.DatetimeIndex([
            pd.Timestamp("2026-10-27 16:05" if with_time else "2026-10-27 00:00",
                         tz="America/New_York"),
            pd.Timestamp("2026-07-28 16:05", tz="America/New_York")])
        df = pd.DataFrame({"EPS Estimate": [2.1, 2.0], "Reported EPS": [None, 2.2],
                           "Surprise(%)": [None, 10.0]}, index=idx)
        return _types.SimpleNamespace(
            calendar={"Earnings Date": [_dt.date(2026, 10, 27)],
                      "Earnings Average": 2.1},
            get_earnings_dates=lambda limit=12: df)

    real = altdata.import_yfinance
    got = []
    try:
        for with_time in (True, False):
            altdata.import_yfinance = (lambda w=with_time: _types.SimpleNamespace(
                Ticker=lambda sym: ticker(w)))
            evs, _ = earnings.events_for("GOOGL")
            fwd = next((e for e in evs if e.type == "scheduled"), None)
            got.append((fwd.payload.get("release_at") if fwd else "no event"))
    finally:
        altdata.import_yfinance = real
    print(f"    release_at with a time: {got[0]}; without: {got[1]}")
    return (str(got[0]).startswith("2026-10-27T20:05") and got[1] is None)


def seed_ahead(db: str, chain_dir: Path) -> None:
    """The edits gate's calendar, plus scheduled earnings: NVDA after the close
    with a consensus and a captured chain, MSFT with a bare date and no chain,
    GOOGL with a bare date and a release time the source carried (W-1.3c 9)."""
    import validate_weekly_edits as E
    from altdata import events as ev_mod
    E.seed_calendar(db, W.ENDING)
    Ev = ev_mod.Event
    with ev_mod.EventStore(db) as ev:
        ev.write_many([
            Ev(type="scheduled", observed_at=f"{day(2)}T20:15:00+00:00",
               source="yfinance", title="NVDA earnings (confirmed)",
               entities=["NVDA"], key=f"earnings-cal-NVDA-{day(2)}-confirmed",
               payload={"kind": "earnings", "symbol": "NVDA", "eps_estimate": 1.05}),
            Ev(type="scheduled", observed_at=f"{day(3)}T13:30:00+00:00",
               source="yfinance", title="MSFT earnings (expected)", entities=["MSFT"],
               key=f"earnings-cal-MSFT-{day(3)}",
               payload={"kind": "earnings", "symbol": "MSFT", "eps_estimate": None}),
            Ev(type="scheduled", observed_at=f"{day(3)}T13:30:00+00:00",
               source="yfinance", title="GOOGL earnings (confirmed)",
               entities=["GOOGL"], key=f"earnings-cal-GOOGL-{day(3)}-confirmed",
               payload={"kind": "earnings", "symbol": "GOOGL", "eps_estimate": None,
                        "release_at": f"{day(3)}T10:30:00+00:00"}),
            Ev(type="scheduled", observed_at=f"{day(1)}T13:30:00+00:00",
               source="fred_releases", title="Producer Price Index -- release date",
               payload={"release_name": "Producer Price Index"})],
            available_at="2026-10-01T00:00:00+00:00")
    d = chain_dir / W.ENDING
    d.mkdir(parents=True, exist_ok=True)
    rows = ["expiry,dte,right,strike,bid,ask,last_price,volume,last_trade_date,"
            "fetched_at,spot"]
    for ex in (day(4), "2026-10-16"):
        for k, (cb, ca, pb, pa) in {180.0: (6.9, 7.1, 6.4, 6.6),
                                    190.0: (2.0, 2.2, 11.0, 11.4)}.items():
            rows.append(f"{ex},5,C,{k},{cb},{ca},,100,,{W.ENDING}T20:00:00Z,181.0")
            rows.append(f"{ex},5,P,{k},{pb},{pa},,100,,{W.ENDING}T20:00:00Z,181.0")
    (d / "NVDA_200000.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")


def scanner_module(cands: list[dict]) -> str:
    name = "_fixture_book_b_scanner"
    mod = types.ModuleType(name)
    mod.candidates = lambda ending, db_path=None: [dict(c) for c in cands]
    sys.modules[name] = mod
    return name


# THE CANDIDATE'S SHAPE (ruled 12 Oct 2026): the register's draft fields (the
# Alternative Assets order, section 4.1 item 10), the setup (EL-1), the score, the
# catalyst and an id; decision_id is null until the sitting approves a packet.
def cand(cid, inst, direction, thesis, setup, score, **kw):
    return {"candidate_id": cid, "instrument": inst, "direction": direction,
            "thesis": thesis, "edge": kw.get("edge", "trend"),
            "horizon": kw.get("horizon", "swing"), "size": kw.get("size"),
            "invalidation": kw.get("invalidation"),
            "counter_thesis": kw.get("counter_thesis", "the move fades"),
            "setup_id": setup, "score": score, "catalyst": kw.get("catalyst"),
            "catalyst_date": kw.get("catalyst_date"), "decision_id": None}


# THE FIXTURE COMES FROM THE SCANNER (Book B scanner brief, 12 Oct 2026): its
# candidates over the scanner gate's synthetic store, plus two rows the scanner
# never writes, to hold the block's own guards -- an undeclared setup, and a
# restricted instrument.
ADVERSARIAL = [
    cand("c-iwm", "IWM", "long", "an undeclared setup", "not_a_setup", 0.99),
    cand("c-bn", "BN", "long", "restricted", "b_breakout", 0.95),
]


def scanner_candidates(td: str) -> list[dict]:
    """The scanner's candidates over the scanner gate's synthetic store."""
    import validate_book_b_scanner as S
    from altdata import book_b_scanner as bbs
    db = str(Path(td) / "scanner.db")
    S.seed_store(db)
    cal = [{"date": day(2), "event": "Consumer Price Index", "symbol": None,
            "tier1": True}]
    return bbs.candidates(S.ENDING, db, cutoff=S.ENDING + "T23:00:00+00:00",
                          regime=S.ECP, calendar=cal)


def main() -> int:
    from altdata import config
    from daily_cascade import ahead, book_b, stack_render, weekly_sections as wsec
    from daily_cascade import weekly_stack as ws
    print(f"{LINE}\nW-1.3a 3.6-3.9 -- AHEAD, CANDIDATES, PRODUCTIVITY, GLOSSARY "
          f"(synthetic week ending {W.ENDING})\n{LINE}")
    td = W.gate_mkdtemp(prefix="validate_weekly_calendar_")
    config.COMPUTED_DIR = str(Path(td) / "computed")
    chain_dir = Path(td) / "chains"
    config.CHAIN_DIR = str(chain_dir)
    db = str(Path(td) / "weekly.db")
    logp = Path(td) / "attention-log.md"
    logp.write_text("| date | kind | minutes | note |\n|---|---|---|---|\n",
                    encoding="utf-8")
    seeded = W.seed(db)
    p = W.payload(seeded)
    seed_ahead(db, chain_dir)
    out = ws.produce(p, archive_dir=str(Path(td) / "reports"), client=W.client([]),
                     db_path=db, log_path=logp, dry_run=True)
    ed, html = out["edition"], out["html_email"]
    sec = {s["id"]: s for s in ed["sections"]}
    ah = sec["ahead"]
    cal = (ah.get("data") or {}).get("calendar") or []
    by = {r["event"]: r for r in cal}

    # --- A ------------------------------------------------------------------
    print(f"\n{LINE}\nA. AHEAD, ONE RANKED TABLE\n{LINE}")
    cols = (ah.get("table") or {}).get("columns") or []
    check(cols == ahead.COLUMNS and len(cols) <= 6,
          f"six columns: when, event, importance, consensus, why, amplifier ({cols})")
    tiers = [r["tier"] for r in cal]
    check(tiers == sorted(tiers) and [r["rank"] for r in cal] ==
          list(range(1, len(cal) + 1)), f"ranked by the config tier ({tiers})")
    check(by.get("CPI", {}).get("tier") == 1 and by.get("CPI", {}).get("rank") == 1
          and by.get("PPI", {}).get("tier") == 2,
          "CPI ranks first at tier 1; PPI is tier 2 (inflation data)")
    check(all(r.get("why") not in (None, "", "—") for r in cal),
          "every row says why it matters (its class's channel)")
    nv = by.get("NVDA earnings") or {}
    check(nv.get("cls") == "earnings_mega" and nv.get("tier") == 1
          and nv.get("time") == "post-market" and "EPS 1.05 (analyst mean)"
          in str(nv.get("consensus")),
          f"NVDA: an index-weight leader, tier 1, post-market, its consensus EPS ({nv})")
    check("implied move ±" in str(nv.get("consensus"))
          and "straddle to 2026-10-09" in str(nv.get("consensus")),
          "NVDA's implied move from its captured chain, to the first expiry after "
          "the report")
    mv = ahead.implied_move("NVDA", day(2), f"{W.ENDING}T22:00:00+00:00", chain_dir)
    check(mv == "implied move ±7.5% (straddle to 2026-10-09)",
          f"the move is the ATM straddle's mid over spot: (7.0 + 6.5) / 181 ({mv})")
    ms = by.get("MSFT earnings") or {}
    check(ms.get("cls") == "earnings_mega"
          and ms.get("time") == "release time not captured"
          and "not captured" in str(ms.get("consensus"))
          and "no consensus EPS carried" in str(ms.get("consensus")),
          f"MSFT: a hyperscaler, a bare date (release time not captured), not "
          f"captured ({ms})")
    # W-1.3c item 9: where the source carries a release time, the session.
    go = by.get("GOOGL earnings") or {}
    check(go.get("time") == "pre-market",
          f"GOOGL: a bare date beside a stored release time (06:30 ET) prints "
          f"pre-market ({go.get('time')})")
    from daily_cascade import weekly_sections as wsec
    es = wsec.earnings_session
    check(es("2026-10-14T10:30:00+00:00") == "pre-market"
          and es("2026-10-14T20:05:00+00:00") == "post-market"
          and es("2026-10-14T13:30:00+00:00") == "release time not captured"
          and es("2026-10-14") == "release time not captured"
          and "session not stated" not in es(None),
          "earnings_session: 06:30 ET pre-market, 16:05 ET post-market, a bare "
          "date (13:30Z or no time) \"release time not captured\", never "
          "\"session not stated\"")
    check(release_at_captured(),
          "the earnings source stores the unreported row's release time beside "
          "the calendar's bare date (release_at), and none where it has no time")
    jp = by.get("JPM earnings") or {}
    check(jp.get("cls") == "earnings_bank" and jp.get("tier") == 2,
          "JPM: a large bank, tier 2")
    check(ahead.earnings_class("ZZZZ", ahead.load_config()) == "earnings_tracked",
          "a tracked name in no list is earnings_tracked")
    det = {d["title"]: d for d in ed.get("detail") or []}
    rt = det.get("Routine releases and bill auctions, the coming week") or {}
    rows_rt = (rt.get("table") or {}).get("rows") or []
    check(rows_rt and any("bill auction" in r[2] for r in rows_rt)
          and any("H.15" in r[2] for r in rows_rt)
          and not any("H.15" in r["event"] or "Bill" in r["event"] for r in cal)
          and any(f"{len(rows_rt)} routine" in n for n in ah.get("notes") or []),
          f"routine releases and bill auctions: in the reference tables, counted "
          f"({len(rows_rt)})")
    pb = (ah.get("data") or {}).get("playbook") or {}
    # W-1.3b fills the slot (item 3.5): its outcome rows, tested in
    # validate_weekly_analytics.
    check(pb.get("event") == cal[0]["event"] and pb.get("playbook_class") is True
          and any(ss.get("playbook") for ss in ah.get("subsections") or []),
          f"the top playbook-class event keeps the playbook slot ({pb.get('event')})")
    check("Positioning that would amplify a surprise" in html and "post-market" in html,
          "the ranked table prints in the edition")

    # --- B ------------------------------------------------------------------
    print(f"\n{LINE}\nB. AHEAD'S OTHER SOURCES\n{LINE}")
    pm = [{"date": day(2), "time": "08:30", "event": f"Prediction market resolves: "
           f"Core CPI m/m above {x}%?", "tier": 3, "consensus": f"last {q}%",
           "cls": "prediction_family", "probability": q / 100}
          for x, q in (("0.1", 80), ("0.2", 55), ("0.3", 20))]
    a2 = ahead.build({"rows": pm, "window": [MON, day(4)], "routine": []},
                     {"week_ending": W.ENDING}, {}, f"{W.ENDING}T22:00:00+00:00")
    check(len(a2["rows"]) == 1 and "3 outcomes; modal: Core CPI m/m above 0.1%?"
          in a2["rows"][0]["event"] and "80%" in a2["rows"][0]["consensus"]
          and a2["reference"][0]["title"] == "Prediction-market resolutions, every outcome"
          and len(a2["reference"][0]["table"]["rows"]) == 3 and a2["collapsed"],
          "a family of resolutions collapses to its modal outcome; every outcome "
          "in the reference tables")
    repo = Path(td) / "repo"
    (repo / "config").mkdir(parents=True)
    (repo / "config" / "em_calendar.yaml").write_text(
        f"entries:\n  - {{date: {day(1)}, country: Brazil, event: 'Copom decision', "
        f"source: 'https://example.invalid'}}\n  - {{date: 2026-12-01, country: "
        f"Chile, event: 'later'}}\n", encoding="utf-8")
    cfg = ahead.load_config()
    hr, absent = ahead.hand_rows(cfg, dt.date.fromisoformat(MON),
                                 dt.date.fromisoformat(day(5)), repo)
    check(len(hr) == 1 and hr[0]["event"] == "Brazil: Copom decision"
          and hr[0]["cls"] == "em_event"
          and "china_political_calendar.yaml" in absent,
          f"a hand-seeded entry in the window prints; a file not present is named "
          f"({absent})")
    # BATCH 8 ITEM 49c: the digital-asset calendar, its marker printed.
    (repo / "config" / "digital_asset_calendar.yaml").write_text(
        f"entries:\n  - {{date: {day(3)}, body: MSCI, event: 'Index Review takes "
        f"effect', time: 'at the US close', marker: '30 Nov, to verify on MSCI''s "
        f"calendar', source: 'fixture'}}\n", encoding="utf-8")
    hr3, _ = ahead.hand_rows(cfg, dt.date.fromisoformat(MON),
                             dt.date.fromisoformat(day(5)), repo)
    dg = [r for r in hr3 if r["cls"] == "crypto_index_event"]
    check(len(dg) == 1 and dg[0]["event"] == "MSCI: Index Review takes effect (30 Nov, "
          "to verify on MSCI's calendar)" and dg[0]["time"] == "at the US close"
          and cfg["classes"]["crypto_index_event"]["tier"] == 2,
          "a digital-asset calendar entry prints in its week as crypto_index_event, "
          "its \"to verify\" marker beside the event")
    rr = ahead.register_rows(cfg, dt.date(2026, 11, 2), dt.date(2026, 11, 7))
    check(len(rr) == 1 and rr[0]["cls"] == "register_event"
          and rr[0]["date"] == "2026-11-03",
          "the claims register's dated event (the midterm) prints in its week")
    rb = ahead.rebalance_rows({"week_ahead": {"session_events": {
        day(4): ["NORMAL", "INDEX_REBALANCE"]}}}, dt.date.fromisoformat(MON),
        dt.date.fromisoformat(day(5)))
    check(len(rb) == 1 and rb[0]["cls"] == "index_rebalance",
          "an index rebalance from the session calendar prints")
    pos = {"cftc:UST10Y": {"z_2y": 2.1, "level": 250000},
           "cftc:UST30Y": {"z_2y": 0.4, "level": -1000}}
    amp = ahead.amplifier(cfg["classes"]["inflation_print"], pos, 1.5)
    check(amp == "speculators net long 10-year note futures (z +2.1)",
          f"an amplifier is a contract at |z| >= 1.5, from Positioning's rows ({amp})")
    check(ahead.amplifier(cfg["classes"]["coupon_benchmark"],
                          {"cftc:UST30Y": {"z_2y": 0.4}}, 1.5).startswith(
                              "no crowded position")
          and ahead.amplifier({"amplifiers": []}, pos, 1.5) == "—",
          "no crowding says so; a class with no amplifier prints a dash")

    # --- C ------------------------------------------------------------------
    print(f"\n{LINE}\nC. CANDIDATES FOR THE SITTING (PAPER)\n{LINE}")
    bk = sec["book"]
    subs = {ss["title"]: ss for ss in bk.get("subsections") or []}
    cb = subs.get(book_b.HEADING) or {}
    bdata = bk.get("data") or {}
    check(bdata.get("scanner") == "present" and book_b.HEADING in html
          and cb.get("lines") and cb["lines"] != [book_b.NO_SCANNER]
          and "activates when" not in html,
          f"the scanner runs inside the Weekly's build and the block prints its "
          f"result; the 'activates when' line is gone "
          f"({(cb.get('lines') or [''])[0][:60]})")
    check(isinstance(book_b.scanner_output(W.ENDING, db), list),
          "the hook reads the scanner by name (a list, never None, now it exists)")
    led = bdata.get("scanner_ledger") or {}
    check(led.get("source") == "dryrun.book_b_candidate" and "error" not in led,
          f"a dry-run Weekly writes the candidates' forecasts to the dry-run "
          f"namespace ({led})")
    real = scanner_candidates(td)
    order = [c["candidate_id"] for c in sorted(real, key=lambda c: -c["score"])]
    mod = scanner_module(real + ADVERSARIAL)
    scan = book_b.scanner_output(W.ENDING, None, module=mod)
    prior_printed = [{"candidate_id": "c-spy", "instrument": "SPY",
                      "direction": "long", "setup_id": "b_breakout",
                      "decision_id": None},
                     {"candidate_id": "c-xle", "instrument": "XLE",
                      "direction": "short", "setup_id": "b_reclaim",
                      "decision_id": None}]
    rows = [
        {"id": "d-spy", "created_at": "2026-09-30T20:00:00+00:00", "instrument": "SPY",
         "direction": "long", "status": "declined", "operator_action": "DECLINE",
         "abstention_reason": "operator_judgment", "note": None, "superseded_by": None,
         "setup_id": "b_breakout"},
        {"id": "d-xle", "created_at": "2026-09-25T20:00:00+00:00", "instrument": "XLE",
         "direction": "short", "status": "draft", "operator_action": None,
         "superseded_by": "d-xle2"},
        {"id": "d-xle2", "created_at": "2026-09-30T20:00:00+00:00", "instrument": "XLE",
         "direction": "short", "status": "active", "operator_action": "TAKE",
         "superseded_by": None, "setup_id": "b_reclaim"},
        {"id": "d-gld", "created_at": "2026-10-01T15:00:00+00:00", "instrument": "GLD",
         "direction": "long", "status": "declined", "operator_action": "DECLINE",
         "abstention_reason": None, "note": None, "superseded_by": None},
    ]
    flow = book_b.sitting_flow(W.ENDING, None, scan, prior_printed, rows=rows)
    subs2, kept = book_b.subsections(scan, flow)
    lines = subs2[0]["lines"]
    top = sorted(real, key=lambda c: -c["score"])[0]
    check(len(real) >= 5 and lines[0].startswith(
        f"1. {top['instrument']} {top['direction']} — ")
          and [c["candidate_id"] for c in kept["printed"]] == order,
          f"ranked by the scanner's own score, highest first ({len(real)} candidates)")
    cl = [x for x in lines if x[:1].isdigit()]
    check(cl and all(k in x for x in cl for k in (
        f"catalyst: Consumer Price Index ({day(2)})", "; invalidation: ",
        "horizon: one to six weeks; time stop ", "; size band: ",
        "% of capital at risk")),
          "one line each: instrument, direction, thesis, catalyst and date, "
          "invalidation, horizon, size band")
    check(not any("undeclared" in x or "BN " in x for x in lines)
          and any("without an id or a declared setup" in n for n in subs2[0]["notes"])
          and any("restricted instrument" in n for n in subs2[0]["notes"]),
          "a candidate with an undeclared setup, or on a restricted instrument, "
          "never prints; each is counted")
    check(all(c["decision_id"] is None for c in kept["printed"])
          and set(book_b.FIELDS) >= {"candidate_id", "edge", "size", "counter_thesis",
                                     "setup_id", "score", "catalyst", "catalyst_date"}
          and all(set(book_b.FIELDS) <= set(c) for c in kept["printed"]),
          "a candidate carries the register's draft fields, its setup, score, "
          "catalyst and id; decision_id is null on every one")
    pc = [x for x in lines if x.startswith("Passed over")]
    check(pc == ["Passed over at the sitting: SPY long — operator judgment."],
          f"the prior sitting's pass prints once with its reason; the approved one "
          f"does not ({pc})")
    check("c-spy" not in {c["candidate_id"] for c in kept["printed"]},
          "and it is not carried into this edition's printed list, so it drops")
    flow_next = book_b.sitting_flow("2026-10-09", None, [], kept["printed"], rows=rows)
    nxt = {c["candidate_id"]: c["reason"] for c in flow_next["passed_candidates"]}
    check("c-spy" not in nxt and nxt == {c: book_b.NO_REASON for c in order},
          f"next week SPY does not print again; this week's candidates, with no "
          f"register row, are passes with no reason recorded ({len(nxt)})")

    # --- D ------------------------------------------------------------------
    print(f"\n{LINE}\nD. THE PRODUCTIVITY LINE\n{LINE}")
    fired = len(real) + len(ADVERSARIAL)
    check(flow["fired"] == fired and flow["reviewed"] == 3 and flow["drafted"] == 2
          and flow["approved"] == 1,
          f"fired {fired} -> reviewed 3 (SPY, XLE, GLD) -> drafted 2 (a supersession "
          f"is not a new packet) -> approved 1 ({flow['fired']}, {flow['reviewed']}, "
          f"{flow['drafted']}, {flow['approved']})")
    ln = book_b.productivity_line(flow)
    check(ln.startswith(f"Triggers fired {fired} → reviewed 3 → packets drafted 2 → "
                        "approved 1;")
          and "register decisions (chat rulings on briefs are not book decisions): "
          in ln, f"four counts and the captioned decisions count ({ln})")
    pt = subs2[1].get("table") or {}
    check(pt.get("rows") == [["GLD", "long", book_b.NO_REASON]],
          "a passed-over row for a reviewed signal with no packet, 'no reason "
          "recorded' where the register carries none")
    pl = (subs.get(book_b.PRODUCTIVITY) or {}).get("lines") or [""]
    import re as _re
    check(_re.match(r"Triggers fired \d+ → reviewed", pl[0]) and
          "chat rulings on briefs are not book decisions" in html,
          f"in the edition, the fired count is the scanner's ({pl[0][:40]})")

    # --- E ------------------------------------------------------------------
    print(f"\n{LINE}\nE. THE GLOSSARY AND THE APPENDIX\n{LINE}")
    import re
    v = ed.get("definitions_version") or ""
    check((re.fullmatch(r"[0-9a-f]{6,40}", v) or v.startswith("unavailable"))
          and f"Definitions version {v}" in html
          and html.find("definitions-version") > html.find(">Glossary</h2>"),
          f"the glossary carries the definitions-version stamp ({v})")
    ta = det.get("Technical appendix") or {}
    tr = {r[0]: r for r in (ta.get("table") or {}).get("rows") or []}
    check(ta and {"Net GEX", "DEX", "Credit spread (OAS)", "Brier score"} <= set(tr)
          and (ta["table"]["columns"] == ["Quantity", "Formula", "Units",
                                          "Sign convention"]),
          "the technical appendix: formulas, units and sign conventions")
    check("SPY, QQQ, IWM" in str(tr.get("GEX/DEX universe")) and "bucket"
          in str(tr.get("Expiry coverage")) and "Technical appendix" in html,
          "the GEX/DEX universe from the tape's dealer symbols, and the expiry coverage")
    check(html.find("Technical appendix") > html.find(">Detail tables</h2>") > 0,
          "it sits in the reference tier")
    check(wsec.unvalidated_tag(0) == "(descriptive; unvalidated, n=0)"
          and wsec.unvalidated_tag(29) == "(descriptive; unvalidated, n=29)"
          and wsec.unvalidated_tag(30) == "(validated, n=30)",
          "unvalidated below n=30; validated at n >= 30")
    g = wsec.unvalidated_glossary([{"label": "the x", "n": 31},
                                   {"label": "the y", "n": 0}])
    check(g[0]["text"].startswith("a validated signal") and
          g[1]["text"].startswith("a descriptive classification"),
          "the glossary keeps descriptive classifications and validated signals "
          "visibly distinct")
    check("(validated," not in html, "no signal is validated today")
    _ = stack_render

    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
