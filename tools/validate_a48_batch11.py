#!/usr/bin/env python3
"""
Signal-triage Batch 11 (items 53-58, ruled 19 Oct 2026; session A's a48-batch11):
what has no other home.

  A  ITEM 54'S SCORECARD BACKFILL. On synthetic captures: a dry run writes
     nothing; a run writes each session that has a settled 16:10 capture and a
     prior-session capture and no row, point in time (the morning profile is the
     prior session's capture; available_at is the capture's own fetched_at), each
     row labelled backfilled under `daily_close:backfill`; a second run writes
     nothing; a live row is never replaced. A backfilled row never enters the test
     sample, whatever its date; the rates print the test sample with the rest
     beside it, "before registration, descriptive"; the registration file's
     SHA-256 is the one validate_dealer_block records.

  B  ITEM 55'S H6, THE LEVEL CLUSTERS. The registration is committed and hashed
     (validate_dealer_block); three families within 0.2% is a cluster, three levels
     from two families is not, and 0.212% apart is not; a zone is frozen 30 days
     and a later overlapping zone is not stored again; held, broke and not reached
     by hand; the anchor prints at most two zones, families named, SPY's in SPX
     and ES terms; the close one line; the rates in H1-H5's form; the vendor note
     in words only, never counted; the detector reads no vendor key and only
     dealer_weekly reads the vendor.

  C  ITEM 53. The VIX premium split by hand (VIX 20.0, RV20 16.0, SPY's ATM IV
     18.0: +4.0 = +2.0 at the money + +2.0 in the wings), labelled "SPY's ATM IV
     as SPX's proxy", absent when SPY's IV is not stored; OS-6's ledger: the
     script reads no store, its first edition is labelled with its verdict, pass
     rule and CSV, it prints no composite and no weight, and states its rights
     while granting none.

  D  ITEM 56. The risk reversal by hand (a +3.0 put skew on a 20.0% ATM IV with
     an 18.0% 25-delta call: 23.0 less 18.0 = +5.0); RV20 and RV60 by hand; the
     close's per-name rows carry chain.iv30_atm, chain.rr_25d, chain.rv20 and
     chain.rv60; the Weekly's per-name table has a row per name with window and n
     and no strategy label; OS-8 reads the 30-day IV.

No gate here reads the live store, fetches or calls a model; every fixture is
synthetic.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gate_tmp import mkdtemp                                    # noqa: E402

LINE = "=" * 78
PASS = FAIL = 0
TD = Path(mkdtemp("a48-batch11-gate-"))


def check(c, m: str) -> bool:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")
    return bool(c)


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


def obs(key: str, day: str, value, inst=None, avail=None, source="fixture") -> dict:
    return {"registry_key": key, "instrument": inst, "observed_at": day,
            "available_at": avail or f"{day}T21:00:00+00:00", "value": value,
            "source": source}


# ---------------------------------------------------------------------------
# A. The scorecard backfill
# ---------------------------------------------------------------------------
CAP_DAYS = ("2026-10-14", "2026-10-15", "2026-10-16", "2026-10-19")


def _capture(day: str, k: int) -> dict:
    return {"symbol": "SPY", "session_date": day, "capture": "settled_eod",
            "fetched_at": f"{day}T20:14:00+00:00",
            "overall": {"net_gex": -1.0e9 - k * 1e8, "net_to_gross": 0.25,
                        "gamma_flip": 660.0 + k, "call_wall_otm": 670.0 + k,
                        "put_wall_otm": 650.0 + k, "peak_abs_gex_strike": 662.0 + k,
                        "call_wall": 671.0 + k, "put_wall": 649.0 + k,
                        "max_pain": 661.0 + k}}


def seed(td: Path) -> tuple[str, str]:
    from altdata import bars as bars_mod, observations
    comp = td / "computed"
    for k, day in enumerate(CAP_DAYS):
        (comp / day).mkdir(parents=True, exist_ok=True)
        (comp / day / "SPY_01_exposure.json").write_text(json.dumps(_capture(day, k)),
                                                         encoding="utf-8")
    db = str(td / "store.db")
    closes = {"2026-10-13": 659.0, "2026-10-14": 660.0, "2026-10-15": 663.0,
              "2026-10-16": 661.0, "2026-10-19": 665.0, "2026-10-20": 666.0}
    rows = [obs("yfinance.mkt_spy", d, v, avail=f"{d}T20:05:00+00:00")
            for d, v in closes.items()]
    rows += [obs("chain.spy_atm_iv_30d", d, 18.0, avail=f"{d}T20:15:00+00:00")
             for d in CAP_DAYS]
    # A live row for 16 Oct (before registration) and one for 20 Oct (after it).
    for d in ("2026-10-16", "2026-10-20"):
        rows.append(obs("dealer.scorecard_day", d,
                        json.dumps({"session": d, "symbol": "SPY", "prior_close": 660.0,
                                    "close": 661.0, "session_high": 662.0,
                                    "session_low": 659.0, "net_gex_morning": -1e9,
                                    "net_to_gross_morning": 0.25, "atm_iv_30d": 18.0,
                                    "regime_eligible": True}),
                        "SPY", source="daily_close"))
    with observations.ObservationStore(db) as st:
        st.write_many(rows)
    bst = bars_mod.BarStore(db, create=True)
    bst.write_many([{"instrument": "spy", "symbol": "SPY", "interval": "5m",
                     "observed_at": t, "open": o, "high": h, "low": lo, "close": c,
                     "volume": 1000.0, "available_at": t[:11] + "20:10:00+00:00",
                     "source": "fixture"}
                    for t, o, h, lo, c in (
                        ("2026-10-15T13:30:00+00:00", 660.0, 661.5, 659.5, 661.0),
                        ("2026-10-15T16:00:00+00:00", 661.0, 664.25, 660.5, 664.0),
                        ("2026-10-15T19:55:00+00:00", 664.0, 664.0, 662.5, 663.0))])
    bst.close()
    return db, str(comp)


def group_a() -> None:
    head("A. ITEM 54: THE SCORECARD BACKFILL, AND THE TWO SAMPLES")
    from altdata import dealer_scorecard as dsc, observations
    from daily_cascade import scorecard_backfill as sb
    db, comp = seed(TD / "a")

    def stored():
        with observations.ObservationStore(db) as st:
            return {str(r["observed_at"])[:10]: r for r in
                    st.as_of("dealer.scorecard_day", "9999", "SPY")}

    before = stored()
    dry = sb.run(db, comp, dry_run=True)
    check(stored().keys() == before.keys() and dry["written"] == 0
          and [r["observed_at"] for r in dry["rows"]] == ["2026-10-15", "2026-10-19"],
          f"the dry run writes nothing and plans 15 and 19 Oct "
          f"({[r['observed_at'] for r in dry['rows']]})")
    why = dict(dry["skipped"])
    check(why.get("2026-10-14", "").startswith("no settled capture for the prior session")
          and why.get("2026-10-16") == "a row exists",
          f"14 Oct is skipped (no prior-session capture), 16 Oct keeps its live row ({why})")
    res = sb.run(db, comp, dry_run=False)
    after = stored()
    r15 = json.loads(after["2026-10-15"]["value_text"])
    check(res["written"] == 2 and after["2026-10-15"]["source"] == "daily_close:backfill"
          and r15["backfilled"] is True
          and after["2026-10-15"]["available_at"].startswith("2026-10-15T20:15")
          and after["2026-10-16"]["source"] == "daily_close",
          "a run writes the two, labelled backfilled under daily_close:backfill, available "
          "at the latest of its inputs (the 20:15 IV, after the 20:14 capture); the live 16 "
          "Oct row is untouched")
    check(r15["flip_morning"] == 660.0 and r15["net_gex_morning"] == -1.0e9
          and r15["prior_close"] == 660.0 and r15["close"] == 663.0
          and r15["session_high"] == 664.25 and r15["session_low"] == 659.5
          and r15["session_range_pct"] == round(100 * 4.75 / 660.0, 3)
          and r15["atm_iv_30d"] == 18.0 and r15["flip_in_range"] is True,
          "point in time: 15 Oct's morning profile is 14 Oct's capture (flip 660, net GEX "
          "-1.0bn), its range 664.25 less 659.50 over the 660.00 prior close, 0.72%")
    again = sb.run(db, comp, dry_run=False)
    check(again["written"] == 0 and len(stored()) == len(after),
          "idempotent: a second run writes nothing")
    with observations.ObservationStore(db) as st:
        t = dsc.from_store(st, "9999-12-31T00:00:00+00:00")
    by = {r["session"]: r for r in t["rows"]}
    check(t["registered_on"] == "2026-10-17" and t["test_n"] == 1 and t["before_n"] == 3
          and by["2026-10-19"]["backfilled"] and not dsc.in_test(by["2026-10-19"], "2026-10-17")
          and dsc.in_test(by["2026-10-20"], "2026-10-17"),
          "a backfilled row never enters the test sample, even dated after the "
          "registration (19 Oct); the live 20 Oct row does; 16 Oct's live row is before it")
    check(len(t["lines"]) == 12 and all(l.split(":")[0].endswith(dsc.BEFORE)
                                        for l in t["lines"][1::2])
          and len(t["rates"]) == 6 and t["promoted"] == 0,
          "the rates print the test sample, each beside its line on the rest, labelled "
          "'before registration, descriptive'; six registered, none promoted")
    src = (REPO / "tools" / "validate_dealer_block.py").read_text(encoding="utf-8")
    pinned = re.search(r'^LEDGER_SHA256 = "([0-9a-f]{64})"', src, re.M).group(1)
    raw = (REPO / "docs" / "ledgers" / "dealer-scorecard-preregistration-2026-10.md"
           ).read_bytes().replace(b"\r\n", b"\n")
    check(hashlib.sha256(raw).hexdigest() == pinned,
          "the registration file's SHA-256 is unchanged (the one validate_dealer_block "
          "records): it is not edited")
    os_src = (REPO / "daily_cascade" / "opening_setup.py").read_text(encoding="utf-8")
    check("def in_test(card: dict, reg: str) -> bool:" in os_src
          and 'return not card.get("backfilled")' in os_src,
          "OS-2's typical range reads both samples by the same rule, with their counts")


def L(fam, name, v):
    return {"family": fam, "name": name, "value": v}


def group_b() -> None:
    head("B. ITEM 55: H6, THE LEVEL CLUSTERS")
    from altdata import level_clusters as lc, observations
    from daily_cascade import dealer_weekly as dw
    three = [L("positioning", "flip", 660.00), L("bands", "one-session band, upper", 660.50),
             L("prior", "session high", 660.90), L("profile", "session POC", 640.0)]
    z = lc.find_clusters(three)
    check(len(z) == 1 and z[0]["low"] == 660.0 and z[0]["high"] == 660.9
          and z[0]["families"] == ["positioning", "bands", "prior"],
          "three families within 0.2% (660.00, 660.50, 660.90: 0.136%) is a cluster, its "
          "zone 660.00 to 660.90; the POC at 640 is not in it")
    two = [L("positioning", "flip", 660.0), L("positioning", "OTM call wall", 660.3),
           L("bands", "one-session band, upper", 660.5)]
    check(lc.find_clusters(two) == [], "three levels from two families is not a cluster")
    wide = [L("positioning", "flip", 660.0), L("bands", "x", 660.5), L("prior", "y", 661.4)]
    check(lc.find_clusters(wide) == [],
          "three families 0.212% apart (660.00 to 661.40) is not a cluster")
    db = str(TD / "b.db")
    rec = {"for": "2026-10-20", "close": 659.0, "levels": three, "zones": [dict(z[0])]}
    with observations.ObservationStore(db) as st:
        st.write_many([obs(lc.KEY, "2026-10-20", json.dumps(rec), "SPY",
                           avail="2026-10-19T20:50:00+00:00")])
        f29 = lc.in_force(st, "SPY", "2026-11-18", "9999")
        f30 = lc.in_force(st, "SPY", "2026-11-19", "9999")
        orig = lc.gather_levels
        try:
            lc.gather_levels = lambda *a, **k: (
                [L("positioning", "flip", 660.4), L("bands", "b", 660.6),
                 L("prior", "p", 660.8)], 659.5)
            nxt = lc.zones_for_next(st, None, "SPY", "2026-10-21", "9999")
        finally:
            lc.gather_levels = orig
    check(len(f29) == 1 and f29[0]["found_for"] == "2026-10-20" and f30 == []
          and nxt["zones"] == [] and nxt["for"] == "2026-10-22",
          "frozen 30 days: in force through 18 Nov, gone on 19 Nov; a later zone "
          "overlapping one in force is not stored again")
    zz = {**z[0], "found_for": "2026-10-20"}
    base = {"high": 660.2, "low": 657.0, "close": 659.8, "prior_close": 658.0}
    held = lc.close_line({"SPY": [zz]}, {"SPY": base})
    broke = lc.close_line({"SPY": [zz]}, {"SPY": {**base, "close": 661.0}})
    away = lc.close_line({"SPY": [zz]}, {"SPY": {**base, "high": 658.2}})
    check("660.00 to 660.90 held" in held and "660.00 to 660.90 broke" in broke
          and "not reached" in away and held.count(";") == 0,
          "by hand: resistance 660.00-660.90 over a 658 prior close; a 660.20 high "
          "approaches it, a 659.80 close holds, a 661 close breaks; a 658.20 high (under "
          "660 x 0.9975 = 658.35) does "
          "not reach it; one line")
    days5 = ["d1", "d2", "d3", "d4", "d5", "d6"]
    ohlc = {"d1": base, "d2": {**base, "high": 658.0}, "d3": base, "d4": base,
            "d5": {**base, "close": 661.0}, "d6": base}
    recs = lc.score_zone_sessions(zz, days5, ohlc, 0.25, 5)
    check([r["h6s"] for r in recs] == [True, None, True, True, False, True]
          and recs[0]["h6f_eligible"] and recs[0]["h6f"] is False
          and not recs[2]["h6f_eligible"] and recs[5]["h6f_eligible"]
          and recs[5]["h6f"] is None,
          "H6s per session; H6f on the first approach in each five-session window, "
          "broke when a close beyond the far edge follows (d5), unresolved without five")
    lines = lc.anchor_lines({"SPY": [zz, {**zz, "low": 650.0, "high": 650.5,
                                          "families": ["bands", "profile", "prior"]}],
                             "QQQ": [{**zz, "low": 505.0, "high": 505.8}]},
                            {"SPY": 658.0, "QQQ": 499.0}, spx_ratio=10.0, es_basis=0.1)
    check(len(lines) == 2
          and lines[0].startswith("Level cluster (SPY, resistance): 660.00 to 660.90; 3 "
                                  "families (positioning, implied bands, the prior session)")
          and "SPX 6,600.00 to 6,609.00" in lines[0] and "ES 6,600.00 to 6,609.00" in lines[0]
          and all(len(x.split()) <= 60 for x in lines),
          "the anchor: at most two zones, nearest first, families named, SPY's also in "
          "SPX and ES terms; under 60 words each")
    from altdata import dealer_scorecard as dsc
    r = lc.rate_h6([{**x, "zone_id": "z"} for x in recs], [], [], "h6s", {})
    check(dsc.rate_line(r).startswith("H6s cluster held (session): 5 scored sessions, "
                                      "under the printing floor of 20"),
          "the rates print in H1-H5's form, with the same floor")
    notes = dw.vendor_zone_notes({"flip": 660.4, "call_wall": 670.0, "put_wall": 650.0}, [zz])
    check(notes == ["The vendor's levels against our cluster 660.00 to 660.90: flip inside "
                    "(an annotation; never counted)."]
          and "660.4" not in notes[0] and "670" not in notes[0],
          "the vendor annotation: words only, no vendor figure, never counted")
    lc_src = (REPO / "altdata" / "level_clusters.py").read_text(encoding="utf-8")
    dw_src = (REPO / "daily_cascade" / "dealer_weekly.py").read_text(encoding="utf-8")
    os_src = (REPO / "daily_cascade" / "opening_setup.py").read_text(encoding="utf-8")
    check("flashalpha" not in lc_src and "vendor_" not in lc_src
          and "vendor_zone_notes(vend, week_zones)" in dw_src
          and "flashalpha" not in os_src,
          "the detector and the opening setup read no vendor key; the annotation is "
          "dealer_weekly's vendor line only")
    st_src = (REPO / "daily_cascade" / "stack.py").read_text(encoding="utf-8")
    sc_src = (REPO / "daily_cascade" / "stack_close.py").read_text(encoding="utf-8")
    check('built["mechanics"]["items"].append(item("mech:clusters", _cl, 3))' in st_src
          and "_lc.store_for_next(st, bst, _sym, sess" in sc_src
          and sc_src.index("_lc.store_for_next") < sc_src.index('"registry_key": SCORECARD_KEY'),
          "the close: one Mechanics item (data, outside the word budget); it stores the "
          "next session's zones, not in a dry run")


def group_c() -> None:
    head("C. ITEM 53: THE VIX PREMIUM SPLIT AND OS-6'S LEDGER")
    import glob
    from daily_cascade import opening_setup as OS
    ser = {"vix": [("2026-10-16", 20.0)], "spy_iv30": [("2026-10-16", 18.0)]}
    sp = OS.premium_split(ser, "2026-10-16", 4.0)
    check(sp and "VIX less RV20 +4.0 = the at-the-money part +2.0 (SPY's 30-day ATM IV "
          "18.0 less RV20 16.0) + the wings +2.0 (VIX 20.0 less SPY's ATM IV)" in sp["line"]
          and "SPY's ATM IV as SPX's proxy" in sp["line"]
          and abs(sp["values"]["atm"] + sp["values"]["wings"] - 4.0) < 1e-9,
          "the split by hand: +4.0 = +2.0 at the money + +2.0 in the wings, labelled")
    check(OS.premium_split({"vix": ser["vix"]}, "2026-10-16", 4.0) is None,
          "absent, not guessed, when SPY's 30-day IV is not stored")
    src = (REPO / "tools" / "calibration" / "os6_positioning.py").read_text(encoding="utf-8")
    check(not re.search(r"ObservationStore|observations|derived_forms|regime\.", src),
          "OS-6's script reads no store (public sources only)")
    eds = sorted(glob.glob(str(REPO / "docs" / "ledgers" / "os-6-ledger-*.md")))
    t = Path(eds[0]).read_text(encoding="utf-8") if eds else ""
    check(eds and "laptop run, public sources" in t
          and re.search(r"^\| Verdict \| \*\*(PASS|FAIL|INSUFFICIENT)", t, re.M)
          and "| Pass rule (as the order states it) |" in t
          and Path(eds[0][:-3] + "-episodes.csv").is_file()
          and "grants nothing" in t and "No composite and no weights are printed" in t
          and "composite score" not in t.lower() and "weight:" not in t.lower(),
          "OS-6's first edition: labelled, its verdict, pass rule and CSV; no composite "
          "and no weight; its rights stated, granting nothing")


def group_d() -> None:
    head("D. ITEM 56: PER-NAME VOLATILITY")
    import math
    from altdata import chain_metrics as cm, config as acfg, observations
    from daily_cascade import opening_setup as OS
    check(abs(cm.risk_reversal_25d(3.0, 0.20, 0.18) - 5.0) < 1e-9
          and cm.risk_reversal_25d(None, 0.20, 0.18) is None,
          "the risk reversal by hand: put 20.0 + 3.0 = 23.0 less the 18.0 call = +5.0 "
          "vol points; none without its legs")
    closes = [100.0 * (1.01 if k % 2 else 0.99) ** 0 * (1 + 0.01 * ((-1) ** k)) for k in range(61)]
    r = [math.log(b / a) for a, b in zip(closes, closes[1:])]
    def rv(xs):
        m = sum(xs) / len(xs)
        return 100 * math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1)) * math.sqrt(252)
    check(abs(cm.realised_n(closes, 20) - rv(r[-20:])) < 1e-9
          and abs(cm.realised_n(closes, 60) - rv(r)) < 1e-9
          and cm.realised_n(closes[:30], 60) is None,
          "RV20 and RV60 by hand, annualised close-to-close; none short of 61 closes")
    rd = {"symbol": "N00", "session": "2026-10-16", "fetched_at": "2026-10-16T20:14:00+00:00",
          "front": {"iv_pct": 30.0, "skew_25d_put": 4.0, "rr_25d": 6.5, "expiry": "2026-11-20",
                    "method": "third Friday"},
          "iv30": {"iv_pct": 29.0}, "put_shares": {}, "volume": 1000.0}
    keys = {x["registry_key"]: x["value"] for x in cm.name_rows(rd, 21.0, 19.0)}
    check(keys.get("chain.iv30_atm") == 29.0 and keys.get("chain.rr_25d") == 6.5
          and keys.get("chain.rv20") == 21.0 and keys.get("chain.rv60") == 19.0,
          "the close's per-name rows carry the four new keys (the same writer backfill-names "
          "runs)")
    db = str(TD / "d.db")
    rows = []
    days = ["2026-10-13", "2026-10-14", "2026-10-15", "2026-10-16"]
    for j, d in enumerate(days):
        rows += [obs(cm.IV30_KEY, d, 25.0 + j, "N00"), obs(cm.RV20_KEY, d, 20.0, "N00"),
                 obs(cm.RV60_KEY, d, 18.0, "N00"), obs(cm.SKEW_KEY, d, 3.0 + j, "N00"),
                 obs(cm.RR_KEY, d, 5.0 - j, "N00")]
    with observations.ObservationStore(db) as st:
        st.write_many(rows)
        t = OS.per_name_table(st, "2026-10-17T21:00:00+00:00", names=["N00", "N01"])
    r0 = t["table"]["rows"][0]
    check(r0[0] == "N00" and r0[1] == "28.0% (rank 100, 100th percentile)"
          and r0[2] == "2026-10-13 to 2026-10-16, n=4" and r0[3] == "+6.0 (100th, n=4)"
          and r0[4] == "+2.0 (25th, n=4)" and r0[5] == "+8.0 (100th, n=4)"
          and r0[6] == "20.0%" and r0[7] == "18.0%"
          and t["table"]["rows"][1][1] == "not stored",
          f"the per-name table by hand: 28.0% at IV rank 100, its window and n; skew, risk "
          f"reversal and IV less RV20 with percentiles and n; RV20, RV60 ({r0})")
    words = json.dumps(t).lower()
    check(not re.search(r"\b(buy|sell|straddle|strangle|condor|butterfly|calendar|"
                        r"overwrite|collar|long vol|short vol)\b", words)
          and len(acfg.chain_universe()) == 17,
          "descriptive words only, no strategy label; 17 names in the universe")
    src = (REPO / "daily_cascade" / "weekly_stack.py").read_text(encoding="utf-8")
    os_src = (REPO / "daily_cascade" / "opening_setup.py").read_text(encoding="utf-8")
    check("_os.per_name_table(_st, ed[\"as_of\"])" in src
          and src.index("wsec.technical_appendix(") < src.index("_os.per_name_table(")
          and "cm.IV30_KEY, now, sym" in os_src and "Highest 30-day IV against 20-day realised" in os_src,
          "the table sits after the Weekly's technical appendix (a table, outside the word "
          "budget); OS-8's IV rows read the 30-day IV")


def main() -> int:
    for g in (group_a, group_b, group_c, group_d):
        try:
            g()
        except Exception as exc:                                # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
