#!/usr/bin/env python3
"""
Validation gate for 6d: prediction markets and the rate path.

    python tools/validate_prediction_markets.py

On SYNTHETIC venue JSON and synthetic futures prices in a temporary store -- a
code gate never reads the live store and never opens a socket, and no figure here
is a real market's:

  A PARSERS      Kalshi and Polymarket events -> market rows with probabilities.
  B PULL         the watch list stored with the three clocks; a description is
                 written once, not once a pull; a venue outage costs that venue
                 only, and is recorded as an error, not a crash.
  C FORMS        1-, 5- and 20-session changes in points; the bias zone.
  D SHOCK        >= 10 points in a session is a shock; CONFIRMED by the other venue
                 or by volume, else UNCONFIRMED; 9 points is not a shock.
  E RATE PATH    the meeting-day arithmetic against a hand-computed fixture;
                 fewer than four meetings -> "not yet tracked".
  F DISAGREE     venue vs fed-funds-implied >= 15 points flagged, under it not;
                 venue vs scenario weight >= 20 points, and only for a mapped one.
  G NO SOURCE    a probability with no stored market description is not printed.
  H RIGHTS       the modules write no scenario weight, narrative, theme, book or
                 register row; the calibration gate is in config and unmet.
  I BACKFILL     every backfilled row is flagged; the gate counts live rows only.
  J PLACEMENT    What's priced carries the rate path and the venue lines and goes
                 deep on a shock; The read carries the shock; What doesn't fit the
                 disagreement; an outage prints "as of".
  K FEEDS / CI   the venues in the eod and 06:45 runs, the futures in eod only;
                 the breakeven trigger on T5YIE, T10YIE and T5YIFR; the five data
                 gates skip explicitly under GitHub Actions.
  L MONTHLY      the calibration gate's progress prints in the appendix.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LINE = "=" * 78
PASS = FAIL = 0
SESSION = "2026-09-30"


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


# ---------------------------------------------------------------------------
# Synthetic venue JSON
# ---------------------------------------------------------------------------
def k_market(ticker, title, price, vol="2000000"):
    return {"ticker": ticker, "title": title, "last_price_dollars": f"{price:.4f}",
            "volume_fp": vol, "open_interest_fp": "5000",
            "close_time": "2026-10-28T17:55:00Z", "rules_primary": "Fixture rule."}


def kalshi_fomc(p_hold=0.40, p_hike=0.60):
    ev = {"event_ticker": "KXFEDDECISION-26OCT", "title": "Fed decision in Oct 2026?",
          "strike_date": "2026-10-28T18:00:00Z"}
    return {**ev, "markets": [
        k_market("KXFEDDECISION-26OCT-H0", "Will the Federal Reserve Hike rates by 0bps "
                 "at their October 2026 meeting?", p_hold),
        k_market("KXFEDDECISION-26OCT-H25", "Will the Federal Reserve Hike rates by "
                 "25bps at their October 2026 meeting?", p_hike)]}


def kalshi_recession(p=0.30):
    return {"event": {"event_ticker": "KXRECSSNBER-26", "title": "Recession this year?",
                      "strike_date": "2027-01-01T00:00:00Z"},
            "markets": [k_market("KXRECSSNBER-26", "Recession in 2026?", p, "50000")]}


def poly_fomc(p_hold=0.45, p_hike=0.55):
    def m(cid, title, p):
        return {"conditionId": cid, "question": f"Fed {title} after October 2026?",
                "groupItemTitle": title,
                "outcomePrices": json.dumps([f"{p}", f"{1 - p:.4f}"]),
                "outcomes": json.dumps(["Yes", "No"]), "volume": "3000000",
                "endDate": "2026-10-28T00:00:00Z", "description": "Fixture terms."}
    return {"slug": "fed-decision-in-october-fixture", "title": "Fed Decision in October?",
            "endDate": "2026-10-28T00:00:00Z",
            "markets": [m("0xhold", "No change", p_hold),
                        m("0xhike", "25 bps increase", p_hike)]}


def make_get(kalshi_down=False, poly_down=False, **prices):
    def get(url):
        if "kalshi" in url:
            if kalshi_down:
                raise OSError("fixture: Kalshi unreachable")
            if "series_ticker=KXFEDDECISION" in url:
                return {"events": [kalshi_fomc(prices.get("k_hold", 0.40),
                                               prices.get("k_hike", 0.60))]}
            if "series_ticker=KXRECSSNBER" in url:
                return {"events": [{**kalshi_recession(prices.get("k_rec", 0.30))["event"],
                                    "markets": kalshi_recession(
                                        prices.get("k_rec", 0.30))["markets"]}]}
            return {"events": []} if "series_ticker" in url else \
                {"event": {}, "markets": []}
        if "polymarket" in url:
            if poly_down:
                raise OSError("fixture: Polymarket unreachable")
            if "public-search" in url and "fed+decision" in url:
                return {"events": [{"slug": "fed-decision-in-october-fixture",
                                    "endDate": "2026-10-28T00:00:00Z"}]}
            if "public-search" in url:
                return {"events": []}
            if "slug=fed-decision-in-october-fixture" in url:
                return [poly_fomc(prices.get("p_hold", 0.45), prices.get("p_hike", 0.55))]
            if "order=volume" in url:
                return []
        raise AssertionError(f"fixture has no answer for {url}")
    return get


# ---------------------------------------------------------------------------
def main() -> int:
    from altdata import derived, fed_funds, observations
    from altdata import prediction_markets as pm
    from altdata.sources import prediction_markets as src
    print(f"{LINE}\n6d -- prediction markets and the rate path (synthetic, no network)"
          f"\n{LINE}")
    td = tempfile.mkdtemp(prefix="validate_6d_")
    db = str(Path(td) / "pm.db")
    cfg = src.load_config()

    # --- A. PARSERS -----------------------------------------------------------
    print(f"\n{LINE}\nA. PARSERS\n{LINE}")
    kr = src.parse_kalshi_event(kalshi_fomc(), "fomc_decision")
    check(len(kr) == 2 and kr[1]["probability"] == 0.60 and kr[1]["venue"] == "kalshi"
          and kr[1]["decision_date"] == "2026-10-28" and kr[1]["volume"] == 2e6,
          f"a Kalshi event parses to one row per market, priced in dollars as a "
          f"probability ({[(r['market_id'], r['probability']) for r in kr]})")
    pr = src.parse_polymarket_event(poly_fomc(), "fomc_decision")
    check(len(pr) == 2 and pr[0]["probability"] == 0.45 and pr[0]["outcome"] ==
          "No change" and pr[1]["criteria"] == "Fixture terms.",
          "a Polymarket event parses each market's YES price and keeps its terms text")

    # --- B. PULL --------------------------------------------------------------
    print(f"\n{LINE}\nB. PULL -- three clocks, one description, an outage\n{LINE}")
    t1 = "2026-09-29T20:10:00+00:00"
    with observations.ObservationStore(db) as st:
        r1 = src.pull(store=st, get=make_get(), now=t1)
        n_meta1 = len(st.as_of("pm.market", instrument="kalshi:KXFEDDECISION-26OCT-H25"))
        row = st.latest_as_of("pm.probability", instrument="kalshi:KXFEDDECISION-26OCT-H25")
        r2 = src.pull(store=st, get=make_get(), now="2026-09-29T20:11:00+00:00")
        n_meta2 = len(st.as_of("pm.market", instrument="kalshi:KXFEDDECISION-26OCT-H25"))
    check(r1["markets"] == 5 and row and row["observed_at"] == t1
          and row["available_at"] == observations.canonical_instant(t1)
          and row["availability_kind"] == "ingest_instant"
          and row["source"] == "kalshi",
          f"the watch list is stored with its clocks: observed and available at the "
          f"fetch instant, ingest_instant ({r1['markets']} markets)")
    check(n_meta1 == 1 and n_meta2 == 1,
          "a market's description is written once, not once a pull")
    with observations.ObservationStore(db) as st:
        r3 = src.pull(store=st, get=make_get(kalshi_down=True),
                      now="2026-09-29T20:12:00+00:00")
    check(any(k.endswith(":kalshi") for k in r3["errors"]) and r3["markets"] == 2,
          f"a Kalshi outage costs Kalshi only: Polymarket still stored, the outage "
          f"recorded ({sorted(r3['errors'])[:2]})")

    # --- C/D. FORMS AND SHOCKS --------------------------------------------------
    print(f"\n{LINE}\nC. FORMS  D. SHOCKS\n{LINE}")
    db2 = str(Path(td) / "forms.db")
    # 25 sessions of a quiet 0.50, then today: Kalshi hike 0.62 (+12), Polymarket
    # hike 0.58 (+8, the same way and at least half as far -> confirms), and the
    # recession market +11 on thin volume with no peer -> UNCONFIRMED.
    days = []
    d = dt.date.fromisoformat(SESSION)
    while len(days) < 25:
        d -= dt.timedelta(days=1)
        if d.weekday() < 5:
            days.append(d)
    days.reverse()
    with observations.ObservationStore(db2) as st:
        for day in days:
            src.pull(store=st, get=make_get(k_hold=0.50, k_hike=0.50, p_hold=0.50,
                                            p_hike=0.50, k_rec=0.20),
                     now=f"{day.isoformat()}T20:10:00+00:00")
        src.pull(store=st, get=make_get(k_hold=0.38, k_hike=0.62, p_hold=0.42,
                                        p_hike=0.58, k_rec=0.31),
                 now=f"{SESSION}T20:10:00+00:00")
        blk = pm.block(SESSION, f"{SESSION}T20:45:00+00:00", store=st)
    by = {r["instrument"]: r for r in blk["markets"]}
    kh = by["kalshi:KXFEDDECISION-26OCT-H25"]
    check(kh["change_1s_points"] == 12.0 and kh["change_5s_points"] == 12.0
          and kh["change_20s_points"] == 12.0,
          f"forms: +12.0 points over 1, 5 and 20 sessions "
          f"({kh['change_1s_points']}, {kh['change_5s_points']}, {kh['change_20s_points']})")
    check(derived.probability_points(0.62, 0.50) == 12.0,
          "the change is computed in derived.py, in points")
    shocks = {s["instrument"]: s for s in blk["shocks"]}
    fomc_k = next((x for x in blk["shocks"] if x["venue"] == "kalshi"
                   and x.get("event_id") == "KXFEDDECISION-26OCT"), {})
    check(abs(fomc_k.get("change_1s_points") or 0) == 12.0
          and fomc_k.get("state") == "CONFIRMED",
          f"a 12-point move is an attention shock, CONFIRMED "
          f"(by {fomc_k.get('confirmed_by')})")
    rec = shocks.get("kalshi:KXRECSSNBER-26")
    check(rec and rec["state"] == "UNCONFIRMED",
          "an 11-point move on a thin market with no peer is a shock, UNCONFIRMED "
          "(Part 27's quarantine)")
    check("polymarket:0xhike" not in shocks,
          "an 8-point move is not a shock")
    check(sum(1 for sh in blk["shocks"] if sh["venue"] == "kalshi"
              and sh.get("event_id") == "KXFEDDECISION-26OCT") == 1,
          "one shock per venue event: the hold leg's -12 and the hike leg's +12 "
          "are one move")
    check(not by["kalshi:KXRECSSNBER-26"]["bias_zone"]
          and pm.forms({"instrument": "x", "history": [
              {"available_at": f"{SESSION}T20:10:00+00:00", "value_num": 0.04}]},
              dt.date.fromisoformat(SESSION), cfg)["bias_zone"],
          "a 4% market is in the bias zone; a 31% one is not")

    # --- E. RATE PATH ----------------------------------------------------------
    print(f"\n{LINE}\nE. RATE PATH -- the meeting-day arithmetic, by hand\n{LINE}")
    # HAND-COMPUTED. Meetings 28 Oct, 9 Dec, 27 Jan, 17 Mar; September holds none.
    #   Oct: pre = Sep avg 4.00 (100 - 96.00); Nov holds none -> post = Nov avg
    #        4.25 (100 - 95.75): +25.0 bp, a hike with probability 1.0.
    #   Dec: Jan holds a meeting -> backward step: post = (31 x 4.25 - 9 x 4.25)
    #        / 22 = 4.25: 0.0 bp, a hold.
    #   Jan: Feb holds none -> post = Feb avg 4.125 (95.875): -12.5 bp, p = 0.5.
    #   Mar: Apr holds none -> post = Apr avg 3.875 (96.125): -25.0 bp, p = 1.0.
    #   Cumulative by March: 3.875 - 4.00 = -12.5 bp.
    meets = [dt.date(2026, 10, 28), dt.date(2026, 12, 9), dt.date(2027, 1, 27),
             dt.date(2027, 3, 17)]
    P = {"2026-09": 96.00, "2026-10": 95.80, "2026-11": 95.75, "2026-12": 95.75,
         "2027-01": 95.80, "2027-02": 95.875, "2027-03": 96.00, "2027-04": 96.125}
    path = fed_funds.implied_path(P, meets, dt.date(2026, 10, 1))
    got = [(m["pre_pct"], m["post_pct"], m["change_bp"], m["move_probability_25bp"])
           for m in path["meetings"]]
    want = [(4.0, 4.25, 25.0, 1.0), (4.25, 4.25, 0.0, 0.0), (4.25, 4.125, -12.5, 0.5),
            (4.125, 3.875, -25.0, 1.0)]
    check(got == want, f"the four meetings match the hand computation ({got})")
    check(path["meetings"][1]["post_from"] == "solved from 2026-12",
          "December is the backward step (January holds a meeting)")
    check(path["tracked"] and path["meetings"][-1]["cumulative_bp"] == -12.5
          and "bp of cuts by March 2027" in path["sentence"],
          f"and the sentence: '{path.get('sentence')}'")
    short = fed_funds.implied_path({k: v for k, v in P.items() if k < "2027-02"},
                                   meets, dt.date(2026, 10, 1))
    check(not short["tracked"] and short["reason"].startswith("not yet tracked"),
          f"fewer than four meetings retrievable -> {short.get('reason')}")
    check(fed_funds.symbol(2026, 11) == "ZQX26.CBT" and fed_funds.symbol(2027, 1) ==
          "ZQF27.CBT", "contract symbols: Nov 2026 -> ZQX26.CBT, Jan 2027 -> ZQF27.CBT")

    # --- F. DISAGREEMENT -------------------------------------------------------
    print(f"\n{LINE}\nF. DISAGREEMENT\n{LINE}")
    rows = [{"venue": "kalshi", "watch_id": "fomc_decision", "question":
             "Will the Federal Reserve Hike rates by 25bps?", "outcome": "Yes",
             "decision_date": "2026-10-28", "probability": 0.60, "instrument": "k1"},
            {"venue": "kalshi", "watch_id": "fomc_decision", "question":
             "Will the Federal Reserve Hike rates by 0bps?", "outcome": "Yes",
             "decision_date": "2026-10-28", "probability": 0.40, "instrument": "k2"},
            {"venue": "polymarket", "watch_id": "fomc_decision", "question":
             "Fed 25 bps increase after December?", "outcome": "25 bps increase",
             "decision_date": "2026-12-10", "probability": 0.05, "instrument": "p1"}]
    dis = pm.disagreements(rows, path, cfg)
    flagged = {(d["meeting"], d["venue"], d["side"]) for d in dis["fed_funds"]}
    check(("2026-10-28", "kalshi", "hike") in flagged,
          f"Kalshi's 60% hike against the futures' 100% is 40 points apart: flagged "
          f"({[d['gap_points'] for d in dis['fed_funds']]})")
    check(("2026-12-09", "polymarket", "hike") not in flagged,
          "Polymarket's 5% December hike against the futures' 0% is 5 points: not")
    check(any("no venue market is mapped" in n for n in dis["notes"]),
          "with no market mapped to a scenario, the 20-point rule says so")
    cfg2 = {**cfg, "scenario_map": {"k1": "Fed hikes in October"}}
    d2 = pm.disagreements(rows, path, cfg2, {"Fed hikes in October": 0.35})
    d3 = pm.disagreements(rows, path, cfg2, {"Fed hikes in October": 0.45})
    check(len(d2["scenario"]) == 1 and d2["scenario"][0]["gap_points"] == 25.0
          and not d3["scenario"],
          "a mapped market 25 points from our weight is flagged; 15 points is not")

    # --- G. NO SOURCE ----------------------------------------------------------
    print(f"\n{LINE}\nG. A MARKET WITH NO STORED SOURCE IS REFUSED\n{LINE}")
    with observations.ObservationStore(db2) as st:
        st.write("pm.probability", "kalshi:ORPHAN", f"{SESSION}T20:10:00+00:00",
                 f"{SESSION}T20:10:00+00:00", 0.9, "kalshi")
        b2 = pm.block(SESSION, f"{SESSION}T20:45:00+00:00", store=st)
    check(all(r["instrument"] != "kalshi:ORPHAN" for r in b2["markets"]),
          "a probability with no stored description and source is never printed")

    # --- H. RIGHTS -------------------------------------------------------------
    print(f"\n{LINE}\nH. RIGHTS -- discovery, shock, disagreement; nothing else\n{LINE}")
    code = "".join((REPO / p).read_text(encoding="utf-8") for p in (
        "altdata/prediction_markets.py", "altdata/sources/prediction_markets.py",
        "altdata/fed_funds.py"))
    banned = [w for w in ("Register(", "ProbabilityLedger(", "NarrativeRegister(",
                          "seed_from_monthly", "set_status", ".record(",
                          "sqlite3.connect(") if w in code]
    check(not banned, f"the 6d modules write no register row, ledger entry, "
                      f"narrative or scenario weight, and open no database but the "
                      f"store ({banned or 'none found'})")
    g = cfg.get("calibration_gate") or {}
    check(g.get("live_snapshot_days") == 90 and g.get("qualifying_shocks") == 20
          and g.get("qualifying_shock_points") == 10
          and g.get("consecutive_monthly_calibration_parts") == 2,
          "the calibration-archive gate is config: 90 live days, 20 shocks of 10 "
          "points, the lead study, two Monthly parts")
    with observations.ObservationStore(db2) as st:
        gp = pm.gate_progress(st, f"{SESSION}T20:45:00+00:00", cfg)
    check(not gp["met"] and "NOT BUILT" in gp["right"],
          f"unmet, and confidence-modification is not built "
          f"({[(c['condition'][:20], c['have']) for c in gp['conditions']]})")

    # --- I. BACKFILL -----------------------------------------------------------
    print(f"\n{LINE}\nI. BACKFILL -- flagged on every row\n{LINE}")
    db3 = str(Path(td) / "bf.db")
    with observations.ObservationStore(db3) as st:
        src.pull(store=st, get=make_get(), now=f"{SESSION}T20:10:00+00:00")

    def bf_get(url):
        if "candlesticks" in url:
            base = int(dt.datetime(2026, 9, 1, tzinfo=dt.timezone.utc).timestamp())
            return {"candlesticks": [{"end_period_ts": base + 86400 * i,
                                      "price": {"close_dollars": f"{0.40 + i / 100:.2f}"}}
                                     for i in range(10)]}
        if "prices-history" in url:
            base = int(dt.datetime(2026, 9, 1, tzinfo=dt.timezone.utc).timestamp())
            return {"history": [{"t": base + 86400 * i, "p": 0.5} for i in range(10)]}
        raise AssertionError(url)
    with observations.ObservationStore(db3) as st:
        live_before = pm.gate_progress(st, None, cfg)["conditions"][0]["have"]
        bres = src.backfill(days=60, store=st, get=bf_get)
        rows = st.conn.execute("SELECT source, availability_kind FROM observations "
                               "WHERE registry_key = 'pm.probability' AND source LIKE "
                               "'%backfill%'").fetchall()
        live_after = pm.gate_progress(st, None, cfg)["conditions"][0]["have"]
    check(bres["rows"] > 0 and rows and all(r[0].endswith(":backfill")
                                            and r[1] == "reconstructed" for r in rows),
          f"{len(rows)} backfilled rows, every one flagged: source <venue>:backfill, "
          f"availability reconstructed")
    check(live_before == live_after == 1,
          f"and the gate's live-day count ignores them ({live_before} -> {live_after})")

    # --- J. PLACEMENT ----------------------------------------------------------
    print(f"\n{LINE}\nJ. PLACEMENT -- What's priced, The read, What doesn't fit\n{LINE}")
    import validate_stack as vs
    from altdata import bars as bars_mod, levels as levels_mod
    from daily_cascade import stack as stack_mod
    db4 = str(Path(td) / "close.db")
    seeded = vs.seed(db4)
    with observations.ObservationStore(db4) as st:
        for day in days:
            src.pull(store=st, get=make_get(k_hold=0.50, k_hike=0.50, p_hold=0.50,
                                            p_hike=0.50), now=f"{day.isoformat()}T20:10:00+00:00")
        src.pull(store=st, get=make_get(k_hold=0.38, k_hike=0.62, p_hold=0.42,
                                        p_hike=0.58), now=f"{SESSION}T20:10:00+00:00")
        st.write_many([{"registry_key": fed_funds.KEY, "instrument": k,
                        "observed_at": SESSION, "available_at": f"{SESSION}T20:10:00+00:00",
                        "value": v, "source": "yfinance"} for k, v in P.items()])
    p = vs.payload(seeded["market_state"])
    with bars_mod.BarStore(db4) as bst:
        book = levels_mod.compute(SESSION, p["exposure"], store=bst)
    saved_md = fed_funds.meeting_days
    fed_funds.meeting_days = lambda path=None: meets
    try:
        ed = stack_mod.build(p, book, [], None, db4)
    finally:
        fed_funds.meeting_days = saved_md
    sec = {s["id"]: s for s in ed["sections"]}
    pt = [i["text"] for i in sec["priced"]["items"]]
    check(any(t.startswith("Fed funds futures: the market prices") and
              "(fed funds futures, as of" in t for t in pt),
          f"What's priced prints the rate path ({next((t for t in pt if 'Fed funds' in t), '')[:90]})")
    check(any(t.startswith("FOMC 2026-10-28:") and "Kalshi hold 38%, hike 62%" in t
              and "futures imply 100%" in t for t in pt),
          "and each meeting's venue odds beside the futures' implied move")
    check(sec["priced"]["depth"] == "deep" and "pts" in (sec["priced"]["depth_reason"] or ""),
          f"a 12-point move takes What's priced deep ({sec['priced']['depth_reason']})")
    rt = [i["text"] for i in sec["read"]["items"]]
    check(any(t.startswith("Attention shock (CONFIRMED)") for t in rt),
          "The read carries the attention shock")
    mt = [i["text"] for i in sec["misfit"]["items"]]
    check(any("fed funds futures" in t and "points apart" in t for t in mt),
          f"What doesn't fit carries the venue-vs-futures disagreement "
          f"({next((t for t in mt if 'points apart' in t), '')[:80]})")
    # The outage: Kalshi stops answering today -- its markets print "as of".
    db5 = str(Path(td) / "outage.db")
    seeded5 = vs.seed(db5)
    with observations.ObservationStore(db5) as st:
        src.pull(store=st, get=make_get(), now=f"{days[-1].isoformat()}T20:10:00+00:00")
        src.pull(store=st, get=make_get(kalshi_down=True), now=f"{SESSION}T20:10:00+00:00")
    with bars_mod.BarStore(db5) as bst:
        book5 = levels_mod.compute(SESSION, p["exposure"], store=bst)
    ed5 = stack_mod.build(vs.payload(seeded5["market_state"]), book5, [], None, db5)
    pt5 = [i["text"] for i in next(s for s in ed5["sections"] if s["id"] == "priced")["items"]]
    check(any(t.startswith(f"Kalshi: as of {days[-1].isoformat()}") for t in pt5)
          and not any(t.startswith("Polymarket: as of") for t in pt5),
          f"a Kalshi outage prints 'Kalshi: as of {days[-1].isoformat()}' and "
          f"Polymarket is current")

    # --- K. FEEDS / CI -----------------------------------------------------------
    print(f"\n{LINE}\nK. FEEDS, THE BREAKEVEN TRIGGER, CI\n{LINE}")
    from altdata import config as acfg, feeds
    import inspect
    fsrc = inspect.getsource(feeds.pull)
    skip = re.search(r'skip = \(([^)]*)\)', fsrc).group(1)
    check("prediction_markets" in feeds.FEEDS and "prediction_markets" not in skip
          and "fed_funds" in skip and "fed_funds" in feeds.FEEDS,
          "the venues run at 16:10 and in the 06:45 early set; the futures at 16:10 "
          "only")
    check(any(s.fred_id == "T5YIE" and s.key == "breakeven_5y"
              for s in acfg.FRED_PULL_SERIES),
          "T5YIE is in the FRED pull as fred.breakeven_5y")
    mb = (stack_mod.config()["triggers"]["priced"]["moves_bp"])
    check(mb == {"fred.breakeven_5y": 10, "fred.breakeven_10y": 10,
                 "fred.breakeven_5y5y": 10},
          f"the breakeven trigger checks T5YIE, T10YIE and T5YIFR at 10 bp ({mb})")
    gates = ["validate_regime_store", "validate_weekly_store",
             "validate_base_rates_store", "validate_monthly_store",
             "validate_iv_solver"]
    res = []
    for gname in gates:
        r = subprocess.run([sys.executable, str(REPO / "tools" / f"{gname}.py")],
                           capture_output=True, text=True, cwd=str(REPO),
                           env={**os.environ, "GITHUB_ACTIONS": "true",
                                "CHESTER_DB": str(Path(td) / "empty.db")})
        res.append((gname, r.returncode, "skipped: box-only" in r.stdout))
    check(all(rc == 0 and said for _, rc, said in res),
          f"under GitHub Actions the five data gates print 'skipped: box-only' and "
          f"exit 0 ({[(g[9:], rc) for g, rc, _ in res]})")

    # --- L. MONTHLY ---------------------------------------------------------------
    print(f"\n{LINE}\nL. THE MONTHLY PRINTS THE GATE'S PROGRESS\n{LINE}")
    from monthly_macro.writer import render_v2
    with observations.ObservationStore(db2) as st:
        from monthly_macro import payload as mp
        gb = mp.pm_gate_block(f"{SESSION}T20:45:00+00:00", st)
    md = render_v2.appendix_section({"appendix": {"state": "ok", "note": "n",
                                                  "series_total": 0, "pillars": {},
                                                  "pillars_declared": 0,
                                                  "pm_calibration_gate": gb}})
    check("calibration-archive gate" in md and "| live snapshot days |" in md
          and "NOT BUILT" in md,
          "the Monthly's appendix prints each condition, what it has and needs")

    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
