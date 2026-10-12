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
     captured" otherwise), classed mega / bank / tracked by config. Routine
     releases and bill auctions go to the reference tables, counted. The
     rank-1 event keeps the playbook slot.
  B  AHEAD'S OTHER SOURCES. A family of prediction-market resolutions collapses
     to its modal outcome; the hand-seeded calendars and the claims register's
     dated events print when in the window; a calendar file not present is
     named; an index rebalance prints; an amplifier is a contract at |z| >= the
     threshold, read from the Positioning section's own rows.
  C  CANDIDATES FOR THE SITTING (PAPER) (3.8). With no scanner the block prints
     "no scanner yet"; against a fixture of the scanner's documented shape, the
     list is ranked by the scanner's score, one line each with every field; a
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


def seed_ahead(db: str, chain_dir: Path) -> None:
    """The edits gate's calendar, plus scheduled earnings: NVDA after the close
    with a consensus and a captured chain, MSFT with a bare date and no chain."""
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


CANDS = [
    {"decision_id": "d-qqq", "instrument": "QQQ", "direction": "long",
     "thesis": "trend resumption above the 20-day", "catalyst": "CPI",
     "catalyst_date": day(2), "invalidation": "close below 640",
     "horizon": "swing (time stop 2026-10-30)", "size_band": "0.25-0.5% of NAV",
     "score": 0.61, "setup_id": "B1"},
    {"decision_id": "d-tlt", "instrument": "TLT", "direction": "short",
     "thesis": "supply into the refunding", "catalyst": "30-year auction",
     "catalyst_date": day(3), "invalidation": "the 30-year below 4.6%",
     "horizon": "swing", "size_band": "0.25% of NAV", "score": 0.83,
     "setup_id": "C2"},
    {"decision_id": None, "instrument": "IWM", "direction": "long",
     "thesis": "no draft", "score": 0.99},
    {"decision_id": "d-bn", "instrument": "BN", "direction": "long",
     "thesis": "restricted", "score": 0.95},
]


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
    check(ms.get("cls") == "earnings_mega" and ms.get("time") == "session not stated"
          and "not captured" in str(ms.get("consensus"))
          and "no consensus EPS carried" in str(ms.get("consensus")),
          f"MSFT: a hyperscaler, a bare date (session not stated), not captured ({ms})")
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
    check(pb.get("event") == cal[0]["event"] and pb.get("playbook_class") is True
          and pb.get("outcomes") is None
          and any(ss.get("playbook") for ss in ah.get("subsections") or []),
          f"the rank-1 event keeps the playbook slot, unfilled until W-1.3b ({pb.get('event')})")
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
    check(cb.get("lines") == [book_b.NO_SCANNER] and book_b.HEADING in html
          and book_b.NO_SCANNER in html,
          "with no scanner the block prints 'no scanner yet — the first candidates "
          "arrive with Book B'")
    check(book_b.scanner_output(W.ENDING, db) is None,
          "the hook reads None until the scanner module exists")
    mod = scanner_module(CANDS)
    scan = book_b.scanner_output(W.ENDING, None, module=mod)
    prior_printed = [{"decision_id": "d-spy", "instrument": "SPY",
                      "direction": "long"},
                     {"decision_id": "d-xle", "instrument": "XLE",
                      "direction": "short"}]
    rows = [
        {"id": "d-spy", "created_at": "2026-09-25T20:00:00+00:00", "instrument": "SPY",
         "direction": "long", "status": "declined", "operator_action": "DECLINE",
         "abstention_reason": "operator_judgment", "note": None, "superseded_by": None},
        {"id": "d-xle", "created_at": "2026-09-25T20:00:00+00:00", "instrument": "XLE",
         "direction": "short", "status": "draft", "operator_action": None,
         "superseded_by": "d-xle2"},
        {"id": "d-xle2", "created_at": "2026-09-30T20:00:00+00:00", "instrument": "XLE",
         "direction": "short", "status": "active", "operator_action": "TAKE",
         "superseded_by": None},
        {"id": "d-qqq", "created_at": "2026-10-02T21:00:00+00:00", "instrument": "QQQ",
         "direction": "long", "status": "draft", "operator_action": None,
         "superseded_by": None},
        {"id": "d-tlt", "created_at": "2026-10-02T21:00:00+00:00", "instrument": "TLT",
         "direction": "short", "status": "draft", "operator_action": None,
         "superseded_by": None},
        {"id": "d-gld", "created_at": "2026-10-01T15:00:00+00:00", "instrument": "GLD",
         "direction": "long", "status": "declined", "operator_action": "DECLINE",
         "abstention_reason": None, "note": None, "superseded_by": None},
    ]
    flow = book_b.sitting_flow(W.ENDING, None, scan, prior_printed, rows=rows)
    subs2, kept = book_b.subsections(scan, flow)
    lines = subs2[0]["lines"]
    check(lines[0].startswith("1. TLT short — supply into the refunding")
          and lines[1].startswith("2. QQQ long"),
          "ranked by the scanner's own score, highest first")
    check(all(k in lines[1] for k in ("catalyst: CPI (2026-10-07)",
                                      "invalidation: close below 640",
                                      "horizon: swing (time stop 2026-10-30)",
                                      "size band: 0.25-0.5% of NAV")),
          "one line each: instrument, direction, thesis, catalyst and date, "
          "invalidation, horizon, size band")
    check(not any("IWM" in x or "BN " in x for x in lines)
          and [c["decision_id"] for c in kept["printed"]] == ["d-tlt", "d-qqq"]
          and any("without a register draft" in n for n in subs2[0]["notes"])
          and any("restricted instrument" in n for n in subs2[0]["notes"]),
          "a candidate with no register draft, or on a restricted instrument, "
          "never prints; each is counted")
    pc = [x for x in lines if x.startswith("Passed over")]
    check(pc == ["Passed over at the sitting: SPY long — operator judgment."],
          f"the prior sitting's pass prints once with its reason; the approved one "
          f"does not ({pc})")
    check("d-spy" not in {c["decision_id"] for c in kept["printed"]},
          "and it is not carried into this edition's printed list, so it drops")
    flow_next = book_b.sitting_flow("2026-10-09", None, [], kept["printed"], rows=rows)
    check(not flow_next["passed_candidates"],
          "next week it does not print again")

    # --- D ------------------------------------------------------------------
    print(f"\n{LINE}\nD. THE PRODUCTIVITY LINE\n{LINE}")
    check(flow["fired"] == 4 and flow["reviewed"] == 3 and flow["drafted"] == 3
          and flow["approved"] == 1,
          f"fired 4 -> reviewed 3 (SPY, XLE, GLD) -> drafted 3 (a supersession is "
          f"not a new packet) -> approved 1 ({flow})")
    ln = book_b.productivity_line(flow)
    check(ln.startswith("Triggers fired 4 → reviewed 3 → packets drafted 3 → "
                        "approved 1;")
          and "register decisions (chat rulings on briefs are not book decisions): "
          in ln, f"four counts and the captioned decisions count ({ln})")
    pt = subs2[1].get("table") or {}
    check(pt.get("rows") == [["GLD", "long", book_b.NO_REASON]],
          "a passed-over row for a reviewed signal with no packet, 'no reason "
          "recorded' where the register carries none")
    pl = (subs.get(book_b.PRODUCTIVITY) or {}).get("lines") or [""]
    check(pl[0].startswith("Triggers fired — → reviewed") and
          "chat rulings on briefs are not book decisions" in html,
          "in the edition, with no scanner the fired count is a dash")

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
