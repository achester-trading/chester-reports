"""
Validation gate for the Weekly's integrity tranche, items 1.2 to 1.7 (W-1.1,
ruled 11 Oct 2026; docs/change-order-weekly-storyline-2026-10-11.md section 2).
Item 1.0 is tools/validate_figure_budget.py groups H and I and
tools/validate_no_filler.py; item 1.1 is tools/validate_edition_consistency.py.

FIXTURES only -- no store, no network, no model:

  A  1.2 PER-ROW AS-OF. A price whose last bar is older than the edition's
     session prints "stale since <date>" beside it (the 9 Oct Bitcoin row); an
     instrument with no bar for the session prints its last close, stale, and
     no move; a series with a declared lag (TIC) prints "lag: monthly (<month>,
     released <date>)", from config, never "stale".
  B  1.3 AGE VERSUS STATUS. From the stored objects, a gap above its line for
     eight sessions, opened on its second and an exception from its fifth,
     prints three dates; the z column names its five-year window; the glossary
     says what the gap z measures; the exceptions table prints "exception since".
  C  1.4 AUCTION FIELDS. Bid-to-cover, indirect, direct and dealer shares, each
     with its percentile among the same security's auctions over two years; the
     tail prints "not stored"; "tail" in a sentence about an auction is
     withheld unless a stored tail is positive.
  D  1.5 THE CONTRACT RECORD. The writer stores bid, ask, last and liquidity
     beside the mid, and the rules link; the reader marks a contract illiquid past
     the config's spread; a meeting's legs print "legs sum 108%" with the
     normalised odds beside the quoted ones; "outside 10-90%" is the
     favourite-longshot check, a flag.
  E  1.6 COINCIDENCE, NOT CAUSATION. "on the back of", "in response to" and
     "reacting to" join the motive words; quoted text is exempt; the daily table
     is "events alongside the session"; the events line takes a clause or a
     quotation -- never "attributed the move in oil to Oil prices rose".
  F  1.7 UNVALIDATED. Each descriptive classification in config prints
     "(descriptive; unvalidated, n=0)" in the glossary and one footnote in each
     section that prints it.

    python tools/validate_weekly_integrity.py
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from daily_cascade import stack_prose as sp  # noqa: E402
from daily_cascade import weekly_sections as wsec  # noqa: E402

PASS = 0
FAIL = 0
LINE = "=" * 78
DAY = "2026-10-09"


def check(c: bool, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def inst(iid, label, kind, as_of, last, cont=False, prior=None):
    f = {"as_of": as_of, "last": last}
    if last is not None:
        k = "bps" if kind == "yield" else "pct"
        f.update({f"session_change_{k}": 0.4, f"wtd_change_{k}": 1.16,
                  f"mtd_change_{k}": 2.1, f"ytd_change_{k}": 14.0})
    lv = [{"type": "prior_close", "value": prior, "as_of": as_of}] if prior else []
    return {"id": iid, "label": label, "kind": kind, "continuous": cont, "frame": f,
            "levels": lv}


def group_a() -> None:
    print(f"\n{LINE}\nA. 1.2 PER-ROW AS-OF: STALE SINCE, AND LAG\n{LINE}")
    book = {"instruments": [inst("spy", "SPY", "price", DAY, 671.2),
                            inst("btc", "Bitcoin", "price", "2026-10-07", 64000.0, True),
                            inst("gold", "Gold (front future)", "price", "2026-10-08",
                                 None, prior=2650.0)]}
    t = wsec.tape_table(book)
    rows = {r[0]: r for r in t["table"]["rows"]}
    # W-1.2 item 2.8: the price carries its unit ("$671.20").
    check(rows["SPY"][1] == "$671.20",
          "a current row prints its price, with its unit and no stale mark")
    check(rows["Bitcoin"][1] == "$64,000.00 (stale since 2026-10-07)",
          f"Bitcoin, two days behind the edition: '{rows['Bitcoin'][1]}'")
    check(rows["Gold (front future)"][1] == "$2,650.00 (stale since 2026-10-08)"
          and rows["Gold (front future)"][3] == "—",
          "no bar for the session: the last close, stale, and no move")
    check(wsec.edition_session("2026-10-11T09:00:00+00:00") == DAY,
          "a Sunday run holds prices to Friday's session, not to Sunday")
    lab = wsec.lag_label("tic.flow_net_foreign", "2026-07-31", "2026-09-18T20:00:00+00:00")
    check(lab == "lag: monthly (July, released 2026-09-18)", f"TIC: '{lab}'")
    check(wsec.lag_label("fred.yield_10y", DAY, DAY) is None,
          "an undeclared series carries no lag label")
    from altdata import bars as bars_mod
    check((bars_mod.load_config().get("freshness") or {}).get("expected_lag", {})
          .get("tic.flow_total") == "monthly", "the lag is config, per series")


def group_b() -> None:
    print(f"\n{LINE}\nB. 1.3 AGE VERSUS STATUS\n{LINE}")
    days = ["2026-09-28", "2026-09-29", "2026-09-30", "2026-10-01", "2026-10-02",
            "2026-10-05", "2026-10-06", "2026-10-07", "2026-10-08", "2026-10-09"]
    objs = []
    for n, d in enumerate(days):
        run = n - 1                       # above its line from the second day
        cond = run >= 0
        c = {"id": "equities_vs_credit", "condition_met": cond,
             "open_state": "open" if run >= 1 else ("pending" if cond else "closed"),
             "exception": run >= 4, "magnitude": 2.4}
        objs.append((d, {"contradictions": [c], "dimensions": {}}))
    dates = wsec.state_dates(objs)
    d = dates["equities_vs_credit"]
    check(d["gap_since"] == "2026-09-29" and d["open_since"] == "2026-09-30"
          and d["exception_since"] == "2026-10-05" and d["sessions"] == 9,
          f"three dates: gap since, open since, exception since ({d})")
    line = wsec.three_dates(d)
    check(line == "gap since 2026-09-29 (9 sessions) · open since 2026-09-30 · "
                  "exception since 2026-10-05", f"printed: '{line}'")
    g = wsec.gap_table([{"id": "equities_vs_credit", "magnitude": 2.4,
                         "threshold_z": 2.0, "persistence_days": 9}], {}, dates)
    cols = g["table"]["columns"]
    check("five-year window" in cols[2] and cols[4].startswith("Gap since"),
          f"the z column names its window; the dates column ({cols[2]}; {cols[4]})")
    check(g["data"][0]["sessions_open"] == 9 and g["data"][0]["exception_since"]
          == "2026-10-05", "the data carries the gap's age and the exception's date apart")
    from altdata import labels
    gl = {x["term"]: x["text"] for x in labels.glossary()}
    check("five-year window" in gl["gap z-score"] and "not the week's move" in
          gl["gap z-score"] and "gap since, open since, exception since" in gl,
          "the glossary states the window and what the gap z measures")
    from daily_cascade import weekly_stack as ws
    mis = ws.misfit_week({"contradictions": [{"id": "equities_vs_credit",
                                              "open_state": "open", "magnitude": 2.4,
                                              "persistence_days": 9}],
                          "exceptions_open_now": ["contradiction:equities_vs_credit"],
                          "exceptions_opened": ["contradiction:equities_vs_credit"]},
                         None, {}, dates={**dates, "contradiction:equities_vs_credit":
                                          {"exception_since": "2026-10-05"}})
    et = mis["subsections"][0]["table"]
    # W-1.3b item 3.2: the tiered table keeps the column, with "opened this week"
    # beside the date rather than in a column of its own.
    i_s = et["columns"].index("Exception since")
    check(str(et["rows"][0][i_s]).startswith("2026-10-05"),
          "the exceptions table prints each exception's own date")
    check("only of a gap's age" in sp.section_prompt(
        {"id": "misfit", "title": "What doesn't fit", "depth": "deep"}, "weekly"),
        "the prose may say 'open n sessions' only of the gap's age")


class AuctionStore:
    def __init__(self, rows: dict):
        self.rows = rows

        class Conn:
            def execute(_s, sql, *a):
                return [("Bond:30-Year",)]
        self.conn = Conn()

    def as_of(self, key, cutoff=None, instrument=None):
        return [{"observed_at": d, "value_num": v}
                for d, v in self.rows.get((key, instrument), [])]


def group_c() -> None:
    print(f"\n{LINE}\nC. 1.4 AUCTION FIELDS\n{LINE}")
    inst_ = "Bond:30-Year"
    hist_days = [f"2025-{m:02d}-11" for m in range(1, 13)] + \
        [f"2026-{m:02d}-11" for m in range(1, 10)] + ["2026-10-08"]
    btc = [2.3 + 0.01 * i for i in range(len(hist_days) - 1)] + [2.25]
    dealer = [0.15 - 0.001 * i for i in range(len(hist_days) - 1)] + [0.07]
    st = AuctionStore({
        ("auction.high_yield", inst_): list(zip(hist_days, [4.6] * len(hist_days))),
        ("auction.bid_to_cover", inst_): list(zip(hist_days, btc)),
        ("auction.dealer_share", inst_): list(zip(hist_days, dealer)),
        ("auction.indirect_share", inst_): list(zip(hist_days, [0.62] * len(hist_days))),
        ("auction.direct_share", inst_): list(zip(hist_days, [0.31] * len(hist_days)))})
    recs = wsec.auction_records(st, DAY + "T21:00:00+00:00", "2026-10-02T21:00:00+00:00")
    check(len(recs) == 1 and recs[0]["dealer"] == 0.07
          and recs[0]["dealer_percentile_2y"] is not None
          and recs[0]["dealer_percentile_2y"] <= 5,
          f"the 30-year: dealers took 7.0%, at the {recs and recs[0]['dealer_percentile_2y']}"
          f"th percentile of two years")
    t = wsec.auction_table(recs)
    row = t["rows"][0]
    check(t["columns"] == ["Auction", "Bid-to-cover", "Indirect", "Direct", "Dealers",
                           "Tail vs when-issued"] and row[5] == "not stored"
          and "7.0% (" in row[4] and row[1].startswith("2.25 ("),
          f"the table prints every field with its percentile ({row})")
    check(sp.tail_faults("The 30-year auction tailed, dealers taking 7.0%.", [])
          and not sp.tail_faults("The 30-year auction drew a 7.0% dealer take.", [])
          and not sp.tail_faults("The 30-year auction tailed by 1.2 bp.", [1.2])
          and not sp.tail_faults("SKEW, the tail-risk gauge, rose 3 points.", []),
          "'tail' about an auction only with a positive stored tail")


def group_d() -> None:
    print(f"\n{LINE}\nD. 1.5 THE PREDICTION-MARKET CONTRACT RECORD\n{LINE}")
    from altdata.sources import prediction_markets as src
    from altdata import prediction_markets as pm, derived
    kal = {"event": {"event_ticker": "KXFEDDECISION-26OCT", "series_ticker": "KXFEDDECISION",
                     "title": "Fed decision in October"},
           "markets": [{"ticker": "KXFEDDECISION-26OCT-C25", "title": "Cut 25bp?",
                        "yes_bid_dollars": "0.55", "yes_ask_dollars": "0.70",
                        "last_price_dollars": "0.60", "volume": 1000,
                        "open_interest": 400, "rules_primary": "Resolves Yes if ..."}]}
    rows = src.parse_kalshi_event(kal, "fomc_decision")
    obs = src.to_observations(rows, "2026-10-09T20:10:00+00:00")
    keys = {o["registry_key"] for o in obs}
    check({"pm.probability", "pm.bid", "pm.ask", "pm.last", "pm.open_interest",
           "pm.price_basis", "pm.market"} <= keys,
          f"the writer stores the book beside the mid ({sorted(keys)})")
    meta = json.loads(next(o["value"] for o in obs if o["registry_key"] == "pm.market"))
    check(meta.get("rules_url") == "https://kalshi.com/markets/kxfeddecision"
          and meta.get("criteria"), "the rules text and its link")
    check(all(derived.registry_entry(k).get("units") for k in
              ("pm.bid", "pm.ask", "pm.last", "pm.open_interest")),
          "each new key is registered")
    mk = {"instrument": "kalshi:X", "venue": "kalshi", "history": [
        {"available_at": "2026-10-09T20:10:00.000000+00:00", "value_num": 0.625}],
        "book": {"bid": 0.55, "ask": 0.70, "last": 0.60, "open_interest": 400},
        "rules_url": "https://kalshi.com/markets/x"}
    f = pm.forms(mk, dt.date(2026, 10, 9), src.load_config(), DAY + "T21:00:00+00:00")
    check(f["spread_points"] == 15.0 and f["illiquid"] and f["retrieved_at"]
          and f["bid"] == 0.55 and f["last"] == 0.60,
          "a 15-point spread past the 10-point threshold is illiquid; the record carries "
          "bid, ask, last and the retrieval instant")
    from daily_cascade import readability as rd
    pmb = {"legs_sum_band": [0.95, 1.05],
           "fomc_odds": {"2026-10-28": {"kalshi": {"hold": 0.40, "cut": 0.68, "hike": 0.0}}},
           "watch": {"fomc_decision": []}}
    tbl = rd.pm_table(pmb, "5s")
    cut = next(r for r in tbl["rows"] if r[0].endswith("cut"))
    check(cut[1] == "68% (63% normalised)" and "Kalshi legs sum 108%" in cut[4],
          f"legs sum 108%: the quoted and normalised odds side by side ({cut})")
    check("favourite–longshot check" in rd._pm_note([{"bias_zone": True}])
          and "illiquid (spread 15 pts)" in rd._pm_note([{"venue": "kalshi",
                                                         "illiquid": True,
                                                         "spread_points": 15.0}]),
          "the note: the favourite-longshot check and the illiquid flag")
    from daily_cascade import stack
    check(stack.BIAS_LEGEND.startswith("Favourite–longshot check")
          and "a flag, not a verdict" in stack.BIAS_LEGEND
          and "mispric" not in stack.BIAS_LEGEND,
          "the rule is renamed and reads as a flag")


def group_e() -> None:
    print(f"\n{LINE}\nE. 1.6 COINCIDENCE, NOT CAUSATION\n{LINE}")
    from altdata import bars as bars_mod
    cfg = bars_mod.load_config()
    mp = (cfg.get("style") or {}).get("motive_phrases") or []
    check({"because", "on the back of", "in response to", "reacting to"} <= set(mp),
          "the motive words include the four")
    f = sp.style_faults("Yields rose on the back of the CPI print.", cfg)
    check(any("on the back of" in x for x in f), "in our voice: withheld")
    f = sp.style_faults('Lane said the rise was "driven by energy" and "because of '
                        'base effects".', cfg)
    check(not any(x.startswith("motive") for x in f), "inside a quotation: exempt")
    sec = next(s for s in cfg["sections"] if s["id"] == "read")
    check("events alongside each session" in sec["subtitle"],
          f"the read's daily table: '{sec['subtitle']}'")
    from daily_cascade import weekly_stack as ws
    rw = ws.read_week(None, {"table": {"columns": ["Day"], "rows": [["Fri 9 Oct"]]}})
    check(rw.get("table_note", "").startswith("Events alongside the session"),
          "and its note says coincidence, not cause")
    a = wsec.attribution_text({"outlet": "CNBC", "market": "oil",
                               "claim": "Oil prices rose as OPEC signalled cuts."})
    check(a == "CNBC, on the move in oil: “Oil prices rose as OPEC signalled cuts.”",
          f"a sentence is quoted: '{a}'")
    b = wsec.attribution_text({"outlet": "Reuters", "market": "oil",
                               "claim": "supply worries in the Gulf"})
    check(b == "Reuters attributed the move in oil to supply worries in the Gulf",
          f"a clause follows 'to': '{b}'")
    rp = sp.read_prompt("weekly")
    check("alongside" in rp and "coincided with" in rp and "the same session as" in rp,
          "the read's frame names the allowed connectors")


def group_f() -> None:
    print(f"\n{LINE}\nF. 1.7 DESCRIPTIVE; UNVALIDATED\n{LINE}")
    from altdata import bars as bars_mod
    classes = wsec.classifications(bars_mod.load_config())
    ids = {c["id"] for c in classes}
    check({"dealer_flags", "gamma_regime", "gap_states", "extremes"} <= ids
          and all(c["n"] == 0 for c in classes),
          f"the classifications, each n=0 until the scorecard grades it ({sorted(ids)})")
    secs = [{"id": "mechanics"}, {"id": "misfit"}, {"id": "tape"}]
    wsec.unvalidated_notes(secs, classes)
    check(secs[0]["notes"] == ["The dealer flags (pinned, held, amplified) and the gamma "
                               "regime: (descriptive; unvalidated, n=0)."]
          and len(secs[1]["notes"]) == 1 and "notes" not in secs[2],
          f"one footnote per section that prints one ({secs[0].get('notes')})")
    gl = wsec.unvalidated_glossary(classes)
    check(all("(descriptive; unvalidated, n=0)" in g["text"] for g in gl)
          and any(g["term"].startswith("dealer flags") for g in gl),
          "each carries the tag in the glossary")
    src = (REPO / "daily_cascade" / "weekly_stack.py").read_text(encoding="utf-8")
    check("glossary_extra" in src and "unvalidated_notes(sections, classes)" in src,
          "the Weekly prints both")


def main() -> int:
    print(f"{LINE}\nTHE WEEKLY'S INTEGRITY TRANCHE, ITEMS 1.2-1.7 (W-1.1)\n{LINE}")
    for g in (group_a, group_b, group_c, group_d, group_e, group_f):
        g()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
