"""
Validation gate for signal-triage batch 3, Tranche A (13 Oct 2026; the change
order docs/change-order-signal-triage-batch-3-2026-10-02.md, ruled 6 Oct 2026):
ST-B3-16, ST-B3-03, ST-B3-04, ST-B3-05, ST-B3-02 and the register.

FIXTURES only (tests/fixtures/batch3_tranche_a.json), each in a temporary store
of its own -- no live store, no network, no model:

  A  ST-B3-16  THE 30Y JGB LINE. One session in each state: below 4.40% nothing
     prints; 4.40-4.50% one line; at or above 4.5% the line and the entry's
     mechanism, verbatim -- on the close's tape and in Plumbing & rates.
  B  ST-B3-03  SR-30. OAT-Bund and BTP-Bund from the stored monthly legs with
     five- and twenty-year percentiles (their n); 149 bp is below the 150 bp
     watch line, 150 bp is the watch tier, the stored November 2011 peak is the
     crisis tier, recomputed from the store; the crisis tier and only it earns
     the Monthly's "what doesn't fit" sentence; "(descriptive; unvalidated,
     n=0)"; EUR/CHF beside it; the legs absent print their reason.
  C  ST-B3-04  SR-33. 10 Sep 2026's operation, $5.19bn of $6bn, bought/max 87%,
     the 30-year's next session +5.0 bp; the TGA in $bn from millions; the
     Monthly's lever table carries the modifier line; the Fiscal Data parser on
     records; the schedule in the release calendar prints in the Weekly's days.
  D  ST-B3-05  SR-34. August 2026's $79.6bn fall in Japan's reserves and the
     securities line, each with its as-of; a week with FIMA usage above zero
     says so; the MoF and H.4.1 parsers on fixture text.
  E  ST-B3-02  SR-6 BY TENOR. A week where the front end's move is real yield
     and the long end's is term premium; breakeven is the move less the real
     leg; the 2-year's real leg names the nearest TIPS tenor; the 30-year prints
     "not published at this tenor"; the frame names the tenor and the leg,
     nothing causal.
  F  THE REGISTER AND THE REGISTRY. SR-30, SR-33 and SR-34 carry §2's bullets
     verbatim and their "built" lines; SR-6 carries the amendment; SR-32 is a
     stub with its dated early-line note. Every new series has a registry entry
     stating its available_at, a family and a long window.
  G  THE EXISTING AUDITS ON THE NEW LINES. The Weekly's Plumbing & rates and the
     Monthly's Plumbing carry the sub-sections; every printed line passes the
     filler rule, the coincidence rule and the readability figure count; the
     numeral audit finds every figure of a code-written line in its own data.

    python tools/validate_batch3_a.py
"""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import gate_tmp  # noqa: E402
import yaml  # noqa: E402

from altdata import batch3, observations  # noqa: E402
from daily_cascade import batch3_block as blk  # noqa: E402

PASS = 0
FAIL = 0
LINE = "=" * 78
FIX = json.loads((REPO / "tests" / "fixtures" / "batch3_tranche_a.json")
                 .read_text(encoding="utf-8"))
CFG = batch3.config()


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def store(rows: list[tuple]) -> str:
    """A temporary store holding (key, instrument, day, value) rows, each
    available at 21:00 UTC on its day."""
    db = str(Path(gate_tmp.mkdtemp("b3a_")) / "obs.db")
    with observations.ObservationStore(db) as st:
        st.write_many([{"registry_key": k, "instrument": i, "observed_at": d,
                        "available_at": d + "T21:00:00+00:00", "value": float(v),
                        "source": "fixture"} for k, i, d, v in rows])
    return db


def open_store(db: str):
    return observations.ObservationStore(db)


# ---------------------------------------------------------------------------
def group_a() -> None:
    print(f"\n{LINE}\nA. ST-B3-16  THE 30Y JGB LINE\n{LINE}")
    f = FIX["jgb_line"]
    mech = CFG["jgb_line"]["mechanism"]
    for state in ("below", "approaching", "flagged"):
        c = f[state]
        db = store([("mof.jgb_30y", None, c["day"], c["level"])])
        with open_store(db) as st:
            cut = c["day"] + "T23:00:00+00:00"
            j = batch3.jgb_line(st, cut)
            tape = blk.tape_items(st, cut)
            sub = blk.jgb_subsection(st, cut)
        if state == "below":
            check(j["state"] == "below" and not tape and sub is None,
                  f"{c['level']}%: below the approach line, nothing prints")
        elif state == "approaching":
            check(j["state"] == "approaching" and len(tape) == 1 and sub
                  and mech not in tape[0]["text"] and "4.40–4.50%" in tape[0]["text"]
                  and c["day"] in tape[0]["text"],
                  f"{c['level']}%: approaching, one line, dated ({tape and tape[0]['text']})")
        else:
            check(j["state"] == "flagged" and len(tape) == 1 and mech in tape[0]["text"]
                  and sub and mech in sub["lines"][0],
                  f"{c['level']}%: flagged, the line and the mechanism verbatim, on the "
                  f"tape and in Plumbing")
    check(mech == ("above ~4.5% unrealised losses on lifers' bond and hedge books "
                   "dominate the solvency benefit of higher yields"),
          "the mechanism is the entry's line, verbatim")
    import inspect                                              # noqa: PLC0415
    from daily_cascade import stack                             # noqa: PLC0415
    check("batch3_block.tape_items(st, cutoff)" in inspect.getsource(stack.build),
          "the close's build puts the line on its tape")


# ---------------------------------------------------------------------------
def eu_rows(oat_last: float) -> list[tuple]:
    f = FIX["eu_stress"]
    rows = []
    d = dt.date(2006, 1, 1)
    end = dt.date(2026, 9, 1)
    while d <= end:
        day = d.isoformat()
        oat, btp = f["history_oat_bp"], f["history_btp_bp"]
        if day == "2011-11-01":
            oat, btp = f["nov_2011_oat_bp"], f["nov_2011_btp_bp"]
        if d == end:
            oat = oat_last
        rows += [("ecb.irs_10y_de", None, day, f["de_level"]),
                 ("ecb.irs_10y_fr", None, day, f["de_level"] + oat / 100.0),
                 ("ecb.irs_10y_it", None, day, f["de_level"] + btp / 100.0)]
        d = (d.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
    rows += [(batch3.EURCHF_KEY, None, dd, v) for dd, v in f["eurchf"]]
    return rows


def group_b() -> None:
    print(f"\n{LINE}\nB. ST-B3-03  SR-30, EU SOVEREIGN STRESS\n{LINE}")
    f = FIX["eu_stress"]
    cut = "2026-10-09T23:00:00+00:00"
    for case in f["cases"]:
        db = store(eu_rows(case["oat_bp"]))
        with open_store(db) as st:
            e = batch3.eu_stress(st, cut)
            sub = blk.eu_subsection(st, cut)
            mis = blk.misfit_items(st, cut)
            peak = batch3.crisis_level_from_store(st, cut)
        oat = next(p for p in e["pairs"] if p["id"] == "oat_bund")
        check(abs(oat["bp"] - case["oat_bp"]) < 0.05 and e["tier"] == case["tier"]
              and (bool(mis) == (case["tier"] == "crisis")),
              f"{case['name']}: tier {e['tier']}; the Monthly's sentence "
              f"{'prints' if mis else 'does not print'}")
        if case["tier"] == "crisis":
            check(peak == CFG["eu_stress"]["crisis_bp"] == 154.0,
                  f"the crisis level is recomputed from the stored November 2011 "
                  f"peak: {peak} bp = config {CFG['eu_stress']['crisis_bp']}")
            check(mis and "(descriptive; unvalidated, n=0)" in mis[0]["text"]
                  and "crisis tier" in mis[0]["text"],
                  f"one sentence at the crisis tier ({mis and mis[0]['text'][:90]}...)")
        if case["tier"] == "watch":
            pc = oat["percentiles"]
            check(set(pc) == {5, 20} and pc[5]["n"] == 60 and pc[20]["n"] == 240
                  and pc[5]["pct"] == 100.0,
                  f"dual percentiles over five and twenty years, each with its n "
                  f"({pc[5]['n']}, {pc[20]['n']})")
            row = sub["table"]["rows"][0]
            check(row[0] == "OAT–Bund" and row[1] == "150.0 bp" and "WATCH" in row[5]
                  and "(n=60)" in row[3] and "(n=240)" in row[4] and row[6] == "2026-09-01",
                  f"the narrow flag: spread, both percentiles, the tier, the as-of ({row})")
            btp = sub["table"]["rows"][1]
            check(btp[0] == "BTP–Bund" and btp[5] == "untiered",
                  "BTP–Bund prints untiered beside it")
            chf = sub["table"]["rows"][2]
            check(chf[0].startswith("EUR/CHF") and chf[1] == "0.9250"
                  and chf[2] == "-0.64%",
                  f"EUR/CHF daily, the transmission tell, with its week ({chf[1]}, {chf[2]})")
            check(sub["lines"][0].startswith("OAT–Bund at the watch tier")
                  and "(descriptive; unvalidated, n=0)" in sub["lines"][0],
                  "the watch tier's line, labelled unvalidated")
    db = store([])
    with open_store(db) as st:
        sub = blk.eu_subsection(st, cut)
    check(sub["table"] is None and any("not yet stored" in x and "aq-3-series-2" in x
                                       for x in sub["lines"]),
          "without the legs, the block says they are not yet stored and names the writer")


# ---------------------------------------------------------------------------
def group_c() -> None:
    print(f"\n{LINE}\nC. ST-B3-04  SR-33, TREASURY BUYBACKS\n{LINE}")
    from altdata.sources import treasury_buybacks as tb         # noqa: PLC0415
    f = FIX["buybacks"]
    op = f["operation"]
    rows = [("treasury.buyback_max", op["instrument"], op["date"], op["max"]),
            ("treasury.buyback_accepted", op["instrument"], op["date"], op["accepted"]),
            ("treasury.buyback_offered", op["instrument"], op["date"], op["offered"]),
            ("fred.tga", None, f["tga_day"], f["tga_millions"])]
    rows += [("fred.yield_30y", None, d, v) for d, v in f["y30"]]
    db = store(rows)
    cut, then = "2026-09-11T23:00:00+00:00", "2026-09-04T23:00:00+00:00"
    with open_store(db) as st:
        ops = batch3.buyback_operations(st, cut, then[:10])
        sub = blk.buyback_subsection(st, cut, then)
        lev = blk.levers_subsection(st, cut, then)
    o = ops[0]
    check(len(ops) == 1 and o["long_end"] and o["sector"] == "10Y to 20Y"
          and o["ratio"] == 0.865 and o["y30_next_bp"] == f["next_session_bp"]
          and o["y30_next_day"] == "2026-09-11",
          f"the operation: bought/max {o['ratio']}, the 30-year's next session "
          f"{o['y30_next_bp']:+.1f} bp ({o['y30_next_day']})")
    r = sub["table"]["rows"][0]
    check(r == ["2026-09-10", "10Y to 20Y", "$5.19bn of $6.00bn", "86%",
                "+5.0 bp (2026-09-11)"],
          f"the events block's row: {r}")
    check("TGA $950.0bn (FRED, 2026-09-10)." in sub["lines"],
          "the TGA from the stored series, millions read as millions ($950.0bn)")
    m = lev["data"]["modifier"]
    check(lev["title"].startswith("The Rate and Liquidity Machine")
          and lev["table"]["rows"][0][0].startswith("Long-end supply")
          and "$5.19bn bought" in m and "1 below 90% of its maximum" in m
          and "+5.0 bp" in m and "unvalidated, n=0" in m,
          f"the Monthly's lever table carries the modifier line ({m[:100]}...)")
    recs = [{"operation_date": op["date"], "operation_type": "Liquidity Support",
             "security_type": "Nominal Coupons", "maturity_bucket": "10Y to 20Y",
             "max_par_amt_redeemed": "6000000000",
             "total_par_amt_accepted": "5187000000.00",
             "total_par_amt_offered": "14500000000.00"},
            {"operation_date": "2026-09-15", "operation_type": "Liquidity Support",
             "security_type": "TIPS", "maturity_bucket": "10Y to 30Y",
             "max_par_amt_redeemed": "null", "total_par_amt_accepted": "null",
             "total_par_amt_offered": "null"}]
    parsed = tb.rows_from_records(recs, "2026-09-10T20:00:00+00:00")
    check(len(parsed) == 3 and {p["registry_key"] for p in parsed} == set(tb.KEYS)
          and parsed[0]["instrument"] == op["instrument"],
          "the Fiscal Data parser: three series per operation, a row without its "
          "amounts skipped")
    try:
        tb.rows_from_records([{"operation_date": "2026-09-10"}], "x")
        check(False, "a changed shape fails the parse")
    except ValueError:
        check(True, "a changed shape fails the parse (STALE, never empty)")
    from daily_cascade import calendar_config, weekly_sections  # noqa: PLC0415
    cal = weekly_sections.load_calendar()
    wk = calendar_config.rows(cal, "2026-10-26", "2026-10-31")
    names = [r["event"] for r in wk]
    check(any("Treasury buyback: nominal coupons, 20 to 30 years" in n for n in names)
          and any(n.startswith("Bank of Japan") for n in names)
          and "Fed balance sheet (H.4.1)" in names
          and "EIA Weekly Petroleum Status Report" in names
          and any(n.startswith("CFTC Traders in Financial Futures") for n in names),
          f"the week of 26 Oct: the 27 Oct buyback, the BoJ, H.4.1, EIA, CFTC TFF "
          f"from config ({len(wk)} rows)")
    nov = calendar_config.rows(cal, "2026-11-02", "2026-11-07")
    check(any(r["event"] == "Japan's international reserves (MoF)"
              and r["date"] == "2026-11-09" for r in
              calendar_config.rows(cal, "2026-11-09", "2026-11-14"))
          and any("1 month to 2 years" in r["event"] for r in nov),
          "MoF reserves on the first weekday on or after the 7th (Mon 9 Nov); the "
          "5 Nov operation")
    import inspect                                              # noqa: PLC0415
    check("calendar_config.rows(cal, mon, sat)" in
          inspect.getsource(weekly_sections.calendar_week),
          "the Weekly's day-by-day calendar reads them")


# ---------------------------------------------------------------------------
def group_d() -> None:
    print(f"\n{LINE}\nD. ST-B3-05  SR-34, JAPAN'S RESERVES AND FIMA\n{LINE}")
    from altdata.sources import fedboard, mof_reserves          # noqa: PLC0415
    f = FIX["japan_funding"]
    rows = []
    for key, name in (("tic.jp_reserves_total", "reserves_total_musd"),
                      ("tic.jp_reserves_fx_securities", "reserves_securities_musd"),
                      ("tic.fima_repo", "fima_musd"),
                      ("tic.fima_repo_weekavg", "fima_weekavg_musd")):
        rows += [(key, None, d, v * 1e6) for d, v in f[name]]
    db = store(rows)
    with open_store(db) as st:
        sub = blk.japan_subsection(st, "2026-09-10T23:00:00+00:00")
    l0, l1 = sub["lines"][0], sub["lines"][1]
    check("Japan's reserves $1,207.5bn, −$79.6bn on the month (MoF, month to "
          "2026-08-31)" in l0 and "foreign securities $839.6bn, −$87.8bn (to "
          "2026-08-31)" in l0,
          f"August 2026's $79.6bn fall, and the securities line, each dated ({l0})")
    check("$5.0bn outstanding on Wednesday 2026-09-02" in l1 and "in use" in l1
          and "week average $2.1bn" in l1,
          f"a week with FIMA usage above zero says so ({l1})")
    check(sub["lines"][2].startswith("Both are fast tells ahead of TIC"),
          "both are the fast tells ahead of TIC; the TIC rows' lag line is untouched")
    csv_text = ("﻿財務省\nMinistry of Finance\n,,,,I. Official reserve assets\n"
                ",,,,A. Official reserve assets\n,,,,,(1) Foreign currency reserves\n"
                ",,,,,,(a) Securities\n"
                "令和8年,7月,,July,1287099,1089617,927332\n"
                ",8月,,August,1207524,994976,839559\n")
    parsed = mof_reserves.rows_from_csv(csv_text, "2026-09-07T23:50:00+00:00", "observed")
    got = {(r["registry_key"], r["observed_at"]): r["value"] for r in parsed}
    check(got.get(("tic.jp_reserves_total", "2026-08-31")) == 1207524e6
          and got.get(("tic.jp_reserves_fx_securities", "2026-07-31")) == 927332e6,
          "the MoF parser: the era year (令和8年 = 2026) carried, millions stored as dollars")
    try:
        mof_reserves.rows_from_csv(csv_text.replace("Securities", "Deposits"), "x", "o")
        check(False, "a moved column fails")
    except ValueError:
        check(True, "a moved column fails the parse")
    h41 = ('"Series Description","Assets: Other: Repurchase agreements - Foreign '
           'official: Wednesday level","Assets: Other: Repurchase agreements - '
           'Foreign official: week average"\n"Unit:","Currency","Currency"\n'
           '"Multiplier:","1000000","1000000"\n"Currency:","USD","USD"\n'
           '"Unique Identifier: ","H41/H41/RESPPALGTRF_N.WW","H41/H41/RESPPALGTRF_XAW_N.WW"\n'
           '"Time Period","RESPPALGTRF_N.WW","RESPPALGTRF_XAW_N.WW"\n'
           '2026-09-02,5000,2143\n2026-09-09,0,ND\n')
    hp = fedboard.h41_rows_from_csv(h41, "2026-09-03T20:30:00+00:00", "observed")
    check(len(hp) == 3 and hp[0]["value"] == 5e9 and hp[0]["registry_key"] == "tic.fima_repo",
          "the H.4.1 parser: columns by unique identifier, millions to dollars, ND skipped")


# ---------------------------------------------------------------------------
def group_e() -> None:
    print(f"\n{LINE}\nE. ST-B3-02  SR-6 BY TENOR\n{LINE}")
    f = FIX["tenor_lens"]
    rows = []
    for key, (a, b) in f["levels"].items():
        rows += [(key, None, f["from"], a), (key, None, f["to"], b)]
    db = store(rows)
    cut = f["to"] + "T23:00:00+00:00"
    then = f["from"] + "T23:00:00+00:00"
    with open_store(db) as st:
        lens = batch3.tenor_lens(st, cut, then)
        sub = blk.tenor_subsection(st, cut, then, then)
    by = {r["tenor"]: r for r in lens["rows"]}
    check(by["2y"]["leg"] == "real" and by["2y"]["real"]["bp"] == 10.0
          and by["2y"]["breakeven_bp"] == 2.0,
          "the front end's move is real yield: 2y +12.0 bp = real +10.0 + breakeven +2.0")
    check(by["10y"]["acm_leg"] == "term premium" and by["10y"]["term_premium"]["bp"] == 13.0
          and by["10y"]["expected_rate"]["bp"] == 2.0,
          "the long end's move is term premium: ACM 10y term premium +13.0 bp, "
          "expected short rate +2.0")
    check(all(abs(r["nominal"]["bp"] - r["real"]["bp"] - r["breakeven_bp"]) < 1e-9
              for r in lens["rows"]),
          "breakeven is the move less the real leg: the two sum to the move")
    r2 = sub["table"]["rows"][0]
    check(r2[0] == "2y, week" and "(nearest: the 5-year TIPS)" in r2[2],
          f"the 2-year's real leg names the nearest TIPS tenor ({r2[2]})")
    r30 = next(r for r in sub["table"]["rows"] if r[0] == "30y, week")
    check(r30[4] == r30[5] == "not published at this tenor",
          "ACM at the 30-year: not published at this tenor")
    check(len(sub["table"]["rows"]) == 8 and any(r[0] == "10y, month"
                                                 for r in sub["table"]["rows"]),
          "the week's and the month's split, by tenor")
    fr = sub["lines"][0]
    check(fr.startswith("Over the week, the 30y moved most (+17.0 bp)")
          and not re.search(r"\b(because|drove|driven|due to|caused|on the back of)\b", fr),
          f"the frame names the tenor and the leg, nothing causal ({fr})")


# ---------------------------------------------------------------------------
def entry_of(reg: str, sr: str) -> str:
    """An entry's text: its heading to the next entry or section heading."""
    j = reg.index(f"### {sr} ")
    ends = [k for k in (reg.find("\n### ", j + 1), reg.find("\n## ", j + 1)) if k > 0]
    return reg[j:min(ends)]


def group_f() -> None:
    print(f"\n{LINE}\nF. THE REGISTER AND THE REGISTRY\n{LINE}")
    co = (REPO / "docs" / "change-order-signal-triage-batch-3-2026-10-02.md").read_text(
        encoding="utf-8")
    reg = (REPO / "docs" / "signal-triage-register.md").read_text(encoding="utf-8")
    for sr, head, st_id in (("SR-30", "### SR-30 — EU sovereign stress (OAT–Bund)", "ST-B3-03"),
                            ("SR-33", "### SR-33 — Treasury long-end buybacks as a "
                                      "yield-management lever", "ST-B3-04"),
                            ("SR-34", "### SR-34 — Japan intervention funding and FIMA",
                             "ST-B3-05")):
        i = co.index(head)
        body = co[i + len(head):co.index("\n### ", i + 1)].strip("\n")
        bullets = [ln for ln in body.splitlines() if ln.startswith("- **")]
        entry = entry_of(reg, sr)
        check(bullets and all(b in entry for b in bullets)
              and f"*Built: {st_id}, branch b3-tranche-a" in entry,
              f"{sr}: §2's {len(bullets)} bullets verbatim, and its built line ({st_id})")
    sr6 = reg[reg.index("### SR-6 "):reg.index("\n### SR-7 ")]
    amend = next(ln for ln in co.splitlines()
                 if ln.startswith("- **SR-6 (10y yield-move attribution):**"))
    check(amend in sr6 and "*Built: ST-B3-02, branch b3-tranche-a" in sr6,
          "SR-6 carries the amendment verbatim and its built line")
    sr32 = entry_of(reg, "SR-32")
    check("STUB" in sr32 and "early line built — ST-B3-16; family in Tranche B" in sr32
          and "13 Oct 2026" in sr32,
          "SR-32 is a stub with its dated note: early line built — ST-B3-16; family "
          "in Tranche B")
    check(all(f"| {n} |" in reg for n in (30, 32, 33, 34)),
          "the index carries rows 30, 32, 33 and 34")
    m = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    new = ["fred.tips_5y", "acm.risk_neutral_yield_2y", "acm.risk_neutral_yield_5y",
           "yfinance.mkt_eurchf", "treasury.buyback_max", "treasury.buyback_accepted",
           "treasury.buyback_offered", "tic.jp_reserves_total",
           "tic.jp_reserves_fx_securities", "tic.fima_repo", "tic.fima_repo_weekavg"]
    fam, lw, met = m.get("families") or {}, m.get("long_windows") or {}, m["metrics"]
    check(all(k in fam and k in lw for k in new),
          f"every new series has a family and a long window ({len(new)})")
    own = [k for k in new if k in met]
    check(len(own) == 9 and all("available_at" in str(met[k].get("description"))
                                for k in own),
          "each new metric entry states its available_at; the bulk members (DFII5, "
          "EUR/CHF) take their blocks'")
    from altdata import config as acfg                          # noqa: PLC0415
    from altdata.sources import yfinance_source as yf           # noqa: PLC0415
    check(any(s.fred_id == "DFII5" and s.key == "tips_5y" for s in acfg.FRED_SIGNAL_SERIES)
          and yf.SYMBOLS.get("EURCHF=X") == "mkt_eurchf"
          and "EURCHF=X" in yf.CONTINUOUS_SYMBOLS,
          "DFII5 joins the FRED signal series; EUR/CHF the price basket (continuous)")


# ---------------------------------------------------------------------------
def group_g() -> None:
    print(f"\n{LINE}\nG. THE EXISTING AUDITS ON THE NEW LINES\n{LINE}")
    from altdata import numeral_audit as na                     # noqa: PLC0415
    from daily_cascade import readability                       # noqa: PLC0415
    from daily_cascade import stack_prose as sp                 # noqa: PLC0415
    from daily_cascade import weekly_stack as ws                # noqa: PLC0415
    from monthly_macro import stack as mstack                   # noqa: PLC0415
    f = FIX
    rows = eu_rows(150.0)
    op = f["buybacks"]["operation"]
    rows += [("treasury.buyback_max", op["instrument"], "2026-10-07", op["max"]),
             ("treasury.buyback_accepted", op["instrument"], "2026-10-07", op["accepted"]),
             ("mof.jgb_30y", None, "2026-10-09", 4.52)]
    for key, (a, b) in f["tenor_lens"]["levels"].items():
        rows += [(key, None, "2026-10-02", a), (key, None, "2026-10-09", b)]
    for key, name in (("tic.jp_reserves_total", "reserves_total_musd"),
                      ("tic.fima_repo", "fima_musd")):
        rows += [(key, None, d, v * 1e6) for d, v in f["japan_funding"][name]]
    db = store(rows)
    now, then = "2026-10-09T23:00:00+00:00", "2026-10-02T23:00:00+00:00"
    with open_store(db) as st:
        wk = ws.plumbing_week(st, now, then)
        mo = mstack.plumbing_section(st, now, "2026-09-09T23:00:00+00:00", set(),
                                     {"monthly_plumbing_buckets": None})
        mo_b = mstack.plumbing_section(st, now, "2026-09-09T23:00:00+00:00", set(),
                                       mstack.stack_mod.config())
    titles = [s.get("title") for s in wk["subsections"]]
    check(all(t in titles for t in (blk.TITLE_JGB, blk.TITLE_EU, blk.TITLE_BUYBACKS,
                                    blk.TITLE_JAPAN, blk.TITLE_TENOR))
          and titles[0] == "Global rates and FX",
          f"the Weekly's Plumbing & rates carries the five, after Global rates ({len(titles)})")
    mt = [s.get("title") for s in mo_b["subsections"]]
    check(blk.TITLE_TENOR in mt and blk.TITLE_LEVERS in mt and blk.TITLE_EU in mt,
          "the Monthly's Plumbing (bucketed) carries them and the lever table")
    del mo
    lines = [x for s in wk["subsections"] for x in s.get("lines") or []]
    bad = [x for x in lines if sp.filler_faults(x)]
    check(lines and not bad, f"no printed line is filler ({len(lines)} lines; {bad[:1]})")
    causal = [x for x in lines if re.search(r"\b(because|drove|driven by|due to|caused|"
                                            r"on the back of|in response to|reacting to)\b",
                                            x, re.I)]
    check(not causal, "no printed line claims a cause (the coincidence rule)")
    check(all(readability.figures(x) is not None for x in lines),
          "the readability figure count reads every line")
    jline = next(s for s in wk["subsections"] if s["title"] == blk.TITLE_JGB)
    jd = jline["data"]["jgb_line"]
    r = na.audit(jline["lines"][0].split(" — ")[0],
                 {"yield_pct": jd["level"], "flag_pct": jd["flag_pct"],
                  "as_of": jd["as_of"]})
    check(r.passed, f"the numeral audit finds the JGB line's figures in its data "
                    f"({r.reason()[:80]})")
    tl = next(s for s in wk["subsections"] if s["title"] == blk.TITLE_TENOR)
    pay = {"rows": [{"tenor": x["tenor"], "nominal_bp": x["nominal"]["bp"]}
                    for x in tl["data"]["tenor_week"]["rows"] if x["nominal"]],
           "series_kind": "yield"}
    r = na.audit(tl["lines"][0], na.with_signed(pay))
    check(r.passed, f"the numeral audit finds the tenor frame's figure in its data "
                    f"({r.reason()[:80]})")


def main() -> int:
    print(f"{LINE}\nSignal-triage batch 3, Tranche A\n{LINE}")
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g):
        try:
            g()
        except Exception as exc:                                # noqa: BLE001
            import traceback                                    # noqa: PLC0415
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
