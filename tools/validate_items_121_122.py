"""
Validation gate for Batch 22 items 121 and 122 (the order's 103 and 104; A134,
7 Nov 2026): the forward TGA-path row in item 17's block, and the Monthly's
earnings-quality line and flag with O-3's calibration. On fixtures in a
temporary store: no network, no live store, no box. The clock is pinned to
GATE_NOW (B106's rule).

  A  THE DTS WRITER. fiscaldata reads the Daily Treasury Statement's TGA closing
     line: the figure from open_today_bal where close_today_bal is "null" (the
     post-2021 layout), millions stored in dollars, other lines skipped; the key
     is the writer's and registered; a DTS fault never fails the MSPD rows.
  B  THE FORWARD TGA ROW. Against a fixture refunding read (scan figures, the
     only source of the assumption): the implied reserve add or drain from the
     DTS's TGA to the assumed quarter-end balance, with the refunding date; Q1
     2027 named, with its implied drain when the end-March assumption is
     stored; "no refunding read stored" with none; a read not yet readable at
     the cutoff is not used; the amounts parse; the row sits in item 17's table
     and its line in the Weekly's and the Monthly's Plumbing block. Nothing
     typed by hand: the module reads the scans table and no config figure.
  C  THE EARNINGS-QUALITY ARITHMETIC. Growth on the year, the gap, the
     two-quarters-running fire, episodes; O-3's calibration picks the admissible
     margin with the fewest false positives, and falls to 10 points, saying
     why, when no margin is admissible or the fewest is tied.
  D  THE MONTHLY'S LINE. As of the cutoff from the store: the three growth
     rates and the gaps, the flag on and off, "not stored" by name and never a
     registry id; Monthly only (the earnings chain at cadence "monthly", not
     "weekly").
  E  THE LEDGER AND CONFIG. The pre-registered head's rule hashes to config's
     rule_sha256; the Result is written once and its margin is config's; the
     two FRED legs are in the pull and registered, barred from the market-state
     object with the flag's keys; the DTS key is registered.

    python tools/validate_items_121_122.py
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

_TMP = gate_mkdtemp(prefix="validate_items_121_122_")
os.environ["CHESTER_DB"] = os.path.join(_TMP, "store.sqlite")

import yaml                                                     # noqa: E402

from altdata import observations                                # noqa: E402

observations.DEFAULT_DB = os.environ["CHESTER_DB"]

GATE_NOW = "2026-11-07T15:00:00+00:00"
CUT = "2026-11-06T22:00:00+00:00"
LINE = "=" * 78
PASS = FAIL = 0


def check(cond: bool, label: str) -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {label}")
    else:
        FAIL += 1
        print(f"  FAIL  {label}")


def pin_clock() -> None:
    import datetime as dt
    from altdata import session
    session.utc_now = lambda: dt.datetime.fromisoformat(GATE_NOW)


def store(name: str):
    return observations.ObservationStore(os.path.join(_TMP, f"{name}.sqlite"))


def put(st, key: str, pts, source: str, avail_lag_days: int = 1) -> None:
    import datetime as dt
    rows = []
    for d, v in pts:
        av = (dt.date.fromisoformat(d[:10]) + dt.timedelta(days=avail_lag_days)).isoformat()
        rows.append({"registry_key": key, "instrument": None, "observed_at": d,
                     "available_at": f"{av}T21:00:00+00:00", "value": v,
                     "source": source})
    st.write_many(rows)


# Invented-for-the-gate refunding read rows, in the scans table's shape. The
# figures mirror a statement's form; the gate tests the arithmetic, not them.
SCAN = {"scan_id": "treasury-refunding-2026q4", "family": "treasury-refunding",
        "title": "Treasury refunding read (gate fixture)", "edition": "gate",
        "source_url": "https://home.treasury.gov/news/press-releases/fixture",
        "section_ref": "§2", "slide": None, "comparison": None,
        "as_of": "2026-11-02", "read_on": "2026-11-03",
        "scan_path": "docs/scans/treasury-refunding-2026q4.md"}
ROWS = [dict(SCAN, metric="Assumed end-of-December 2026 cash balance", value="$850 billion"),
        dict(SCAN, metric="Assumed end-of-March 2027 cash balance", value="$1.000 trillion"),
        dict(SCAN, metric="Privately-held net marketable borrowing, Oct-Dec 2026",
             value="$618 billion")]


# ---------------------------------------------------------------------------
def group_a() -> None:
    print(f"\n{LINE}\nA. THE DTS WRITER\n{LINE}")
    from altdata.sources import fiscaldata as fd
    recs = [
        {"record_date": "2026-10-29", "account_type": "Treasury General Account (TGA) Opening Balance",
         "open_today_bal": "1015632", "close_today_bal": "null"},
        {"record_date": "2026-10-29", "account_type": "Treasury General Account (TGA) Closing Balance",
         "open_today_bal": "1040236", "close_today_bal": "null"},
        {"record_date": "2026-10-30", "account_type": "Treasury General Account (TGA) Closing Balance",
         "open_today_bal": "900000", "close_today_bal": "951593"},
        {"record_date": "2026-10-31", "account_type": "Treasury General Account (TGA) Closing Balance",
         "open_today_bal": "null", "close_today_bal": "null"},
    ]
    rows = fd.rows_from_dts(recs, "2026-11-07T00:00:00+00:00")
    by = {r["observed_at"]: r["value"] for r in rows}
    check(by.get("2026-10-29") == 1040236 * 1e6,
          "the closing line's figure comes from open_today_bal where close is \"null\", "
          "millions to dollars ($1.040tn on 29 Oct)")
    check(by.get("2026-10-30") == 951593 * 1e6,
          "a numeric close_today_bal wins over open_today_bal")
    check(len(rows) == 2 and all(r["registry_key"] == fd.DTS_KEY for r in rows),
          "the opening line and a day with no figure write nothing")
    check(fd.DTS_KEY in fd.KEYS and fd.DTS_KEY == "fiscaldata.dts_tga_close",
          "fiscaldata.dts_tga_close is one of the writer's keys")
    src = (REPO / "altdata" / "sources" / "fiscaldata.py").read_text(encoding="utf-8")
    body = src.split("def pull(", 1)[1]
    check("rows_from_dts(fetch_dts(" in body and body.index("rows_from_dts") > body.index("rows_from_records")
          and "the DTS TGA line failed" in body,
          "the DTS line is read after the MSPD rows inside its own try: its fault "
          "never fails them")
    from altdata import derived
    e = derived.registry_entry(fd.DTS_KEY)
    check(bool(e) and e.get("units") == "usd" and e.get("freq") == "daily",
          "the key is registered: usd, daily")


def group_b() -> None:
    print(f"\n{LINE}\nB. THE FORWARD TGA ROW\n{LINE}")
    from altdata import batch5, scans
    from daily_cascade import batch5_block
    check(batch5.parse_amount("$850 billion") == 850e9
          and batch5.parse_amount("$1.000 trillion") == 1e12
          and batch5.parse_amount("1,040bn") == 1040e9
          and batch5.parse_amount("about half") is None,
          "amounts parse ($850 billion, $1.000 trillion, 1,040bn); prose does not")
    a = batch5.refunding_assumptions(ROWS)
    check([x["quarter_end"] for x in a] == ["2026-12-31", "2027-03-31"]
          and a[0]["value"] == 850e9 and a[0]["refunding_date"] == "2026-11-02",
          "the read's two assumptions, by quarter end, the borrowing row ignored")
    st = store("b")
    put(st, "fiscaldata.dts_tga_close",
        [("2026-10-29", 1040.236e9), ("2026-11-05", 922.752e9)], "fiscaldata")
    f = batch5.forward_tga(st, CUT, scan_rows=ROWS)
    imp = f.get("implied") or {}
    check(imp.get("direction") == "add" and abs(imp["amount"] - 72.752e9) < 1
          and imp["from"] == "2026-11-05" and imp["to"] == "2026-12-31",
          "TGA $922.8bn (5 Nov) to the assumed $850bn at end-December: an implied "
          "reserve add of $72.8bn")
    w = f.get("watch") or {}
    check(f["watch_label"] == "Q1 2027" and w.get("direction") == "drain"
          and abs(w["amount"] - 150e9) < 1,
          "Q1 2027 named: $850bn to the assumed $1.000tn, an implied drain of $150bn")
    f29 = batch5.forward_tga(st, "2026-10-30T22:00:00+00:00", scan_rows=ROWS)
    check(f29.get("refunding") is None and f29.get("reason") == "no refunding read stored",
          "a read whose read_on is after the cutoff is not used: \"no refunding read stored\"")
    f0 = batch5.forward_tga(st, CUT, scan_rows=[])
    check(f0.get("reason") == "no refunding read stored" and f0["tga"]["value"] == 922.752e9,
          "no read stored: the row says so and prints the TGA alone")
    # Through the real scans table, in the store's own file.
    conn = scans._connect(str(st.path), readonly=False)
    for r in ROWS:
        scans.write(conn, r)
    conn.commit()
    conn.close()
    fs = batch5.forward_tga(st, CUT)
    check((fs.get("implied") or {}).get("amount") == imp.get("amount"),
          "read from the store's scans table (scans.latest), the same row")
    sub = batch5_block.net_liquidity_subsection(st, CUT)
    txt = " ".join(sub["lines"])
    check("Forward TGA path (refunding of 2 Nov)" in txt and "implied reserve add of $73bn" in txt
          and "Q1 2027 is the quarter to watch" in txt and "implies a drain of $150bn" in txt,
          "the line: the refunding date, the implied add, Q1 2027 with its drain")
    st.close()
    st2 = store("b2")
    put(st2, "calc.net_liquidity", [(f"2026-{m:02d}-{d:02d}", 5.8e12 + i * 1e10)
                                    for i, (m, d) in enumerate(
                                        [(7, 1), (7, 8), (7, 15), (7, 22), (7, 29), (8, 5), (8, 12),
                                         (8, 19), (8, 26), (9, 2), (9, 9), (9, 16), (9, 23),
                                         (9, 30), (10, 7), (10, 14), (10, 21), (10, 28)])],
        "derived")
    put(st2, "fiscaldata.dts_tga_close", [("2026-11-05", 922.752e9)], "fiscaldata")
    conn = scans._connect(str(st2.path), readonly=False)
    for r in ROWS:
        scans.write(conn, r)
    conn.commit()
    conn.close()
    for cad in ("weekly", "monthly"):
        subs = batch5_block.plumbing_subsections(st2, CUT, "2026-10-30T22:00:00+00:00", cad)
        nl = next((s for s in subs if s.get("title") == batch5_block.TITLE_NL), None)
        rows = (nl or {}).get("table", {}).get("rows") or []
        fwd = [r for r in rows if str(r[0]).startswith("Forward")]
        check(bool(fwd) and fwd[0][1] == "+73bn" and fwd[0][3] == "+73bn"
              and "refunding 2026-11-02" in fwd[0][5],
              f"{cad}: one forward row in item 17's table, the TGA leg alone (+73bn), "
              f"with the refunding date")
    st2.close()
    src = (REPO / "altdata" / "batch5.py").read_text(encoding="utf-8")
    fn = src.split("def forward_tga(", 1)[1].split("\ndef ", 1)[0]
    check("scans.latest" in fn and not re.search(r"\b850\b|1\.040|1040", fn),
          "the assumption is read from the scans table only: no figure in the code")
    cfg = yaml.safe_load((REPO / "config" / "batch5_tranche_1.yaml").read_text(encoding="utf-8"))
    ft = cfg["net_liquidity"]["forward_tga"]
    check(not any(re.search(r"(?i)assum.*\d{3}", str(v)) for k, v in ft.items()
                  if k not in ("metric_pattern",)) and ft["watch_quarter"] == "2027-03-31",
          "config holds no assumed balance (rule 30): only the key, family, pattern, "
          "watch quarter and staleness")


def group_c() -> None:
    print(f"\n{LINE}\nC. THE EARNINGS-QUALITY ARITHMETIC\n{LINE}")
    from altdata import earnings_quality as eq
    check(eq.quarter_of("2026-04-01") == "2026Q2" and eq.prev_quarter("2027Q1") == "2026Q4"
          and eq.prev_quarter("2026Q2", 4) == "2025Q2" and eq.last_month("2026Q2") == "2026-06",
          "quarter arithmetic")
    nipa = {"2025Q1": 100.0, "2025Q2": 100.0, "2026Q1": 110.0, "2026Q2": 105.0}
    eps = {"2025-03": 200.0, "2025-06": 200.0, "2026-03": 250.0, "2026-06": 240.0}
    rows = eq.growth_rows(nipa, eps)
    check(abs(rows["2026Q1"]["nipa_yoy"] - 10) < 1e-9 and abs(rows["2026Q1"]["eps_yoy"] - 25) < 1e-9
          and abs(rows["2026Q1"]["gap"] - 15) < 1e-9 and abs(rows["2026Q2"]["gap"] - 15) < 1e-9,
          "growth on the year, EPS read at the quarter's last month; the gap in points")
    check(eq.fired(rows, 14.9) == ["2026Q2"] and eq.fired(rows, 15.1) == [],
          "the flag fires at the second quarter running at or above the margin")
    check(eq.episodes(["1999Q4", "2000Q1", "2000Q3", "2007Q1"])
          == [["1999Q4", "2000Q1"], ["2000Q3"], ["2007Q1"]], "episodes are runs")

    def series(gaps: dict) -> dict:
        return {q: {"gap": g} for q, g in gaps.items()}
    cfg = {"calibration": {"targets": {"1999-2000": ["1999Q1", "2000Q4"],
                                       "2006-07": ["2006Q1", "2007Q4"]},
                           "fp_from": "1990Q1", "candidates": [5, 30], "ambiguous_margin": 10}}
    g = {}
    q = "1989Q4"
    while q <= "2010Q4":
        g[q] = 0.0
        q = eq.prev_quarter(q, -1)
    g.update({"1999Q3": 25, "1999Q4": 25, "2006Q4": 18, "2007Q1": 18,
              "1995Q1": 12, "1995Q2": 12, "2004Q1": 8, "2004Q2": 8})
    r = eq.calibrate(series(g), cfg)
    check(r["admissible"] == list(range(5, 19)),
          "admissible margins 5 to 18: both targets fire")
    fp ={t["margin"]: t["false_positives"] for t in r["table"]}
    check(fp[5] == 2 and fp[9] == 1 and fp[12] == 1 and fp[13] == 0 and r["ambiguous"]
          and r["margin"] == 10 and "shared by 6 admissible margins (13 to 18" in r["why"],
          "a tied minimum (0 false positives at 13 to 18) is ambiguous: 10 points, and why")
    g2 = dict(g, **{"2006Q4": 13, "2007Q1": 13})
    r2 = eq.calibrate(series(g2), cfg)
    check(r2["margin"] == 13 and not r2["ambiguous"] and r2["admissible"] == list(range(5, 14)),
          "a unique minimum picks its margin (13: both targets, no false positive)")
    g3 = dict(g, **{"2006Q4": 0, "2007Q1": 0})
    r3 = eq.calibrate(series(g3), cfg)
    check(r3["ambiguous"] and r3["margin"] == 10 and "no candidate margin" in r3["why"],
          "no admissible margin: 10 points, and why")


def group_d() -> None:
    print(f"\n{LINE}\nD. THE MONTHLY'S LINE\n{LINE}")
    from altdata import earnings_quality as eq
    st = store("d")
    put(st, "fred.cpatax", [("2025-01-01", 3000.0), ("2025-04-01", 3000.0),
                            ("2026-01-01", 3150.0), ("2026-04-01", 3150.0)], "fred", 50)
    put(st, "fred.profits_domestic_nonfin", [("2025-01-01", 2000.0), ("2025-04-01", 2000.0),
                                             ("2026-01-01", 2200.0), ("2026-04-01", 2100.0)],
        "fred", 50)
    put(st, "shiller.sp_earnings", [("2025-03-01", 200.0), ("2025-06-01", 200.0),
                                    ("2026-03-01", 245.0), ("2026-06-01", 250.0)], "shiller", 40)
    cfg = eq.config()
    r = eq.read(st, CUT, cfg)
    check(r.get("quarter") == "2026Q2" and abs(r["nipa_yoy"] - 5) < 1e-9
          and abs(r["eps_yoy"] - 25) < 1e-9 and abs(r["gap"] - 20) < 1e-9
          and abs(r["nonfin_yoy"] - 5) < 1e-9 and abs(r["gap_nonfin"] - 20) < 1e-9,
          "Q2 2026: EPS +25% against NIPA +5% and nonfinancial +5%, gaps of 20 points")
    check(r["flag"] is True and r["margin"] == cfg["margin"],
          f"two quarters at or above {cfg['margin']:.0f} points: the flag is on")
    ln = " ".join(eq.lines(r))
    check("Earnings quality, 2026Q2 on the year" in ln and "a gap of +20.0 pts" in ln
          and "Earnings-quality flag:" in ln and "operating EPS not tracked" in ln,
          "the line prints the three rates, the gap, the flag and the EPS label")
    r_early = eq.read(st, "2026-05-10T22:00:00+00:00", cfg)
    check(r_early.get("quarter") == "2026Q1" and r_early["flag"] is False,
          "as of 10 May Q2 is not yet knowable: Q1 alone, one quarter, the flag off")
    check("Earnings-quality flag off" in " ".join(eq.lines(r_early)),
          "the flag-off line names the rule")
    st.close()
    e = store("d0")
    ln0 = " ".join(eq.lines(eq.read(e, CUT, cfg)))
    check("not stored" in ln0 and not re.search(r"\b(fred|shiller)\.", ln0),
          "an empty store says \"not stored\" by name, never a registry id")
    e.close()
    from daily_cascade import index_carry_block as icb
    src = (REPO / "daily_cascade" / "index_carry_block.py").read_text(encoding="utf-8")
    body = src.split("def priced_subsection(", 1)[1].split("\ndef ", 1)[0]
    mon = body.split('if cadence == "monthly":', 1)
    check(len(mon) == 2 and "earnings_quality" in mon[1] and "earnings_quality" not in mon[0],
          "the line rides the earnings chain at cadence \"monthly\" only")
    st = store("d")
    sub_m = icb.priced_subsection(st, CUT, "monthly")
    sub_w = icb.priced_subsection(st, CUT, "weekly")
    lm = " ".join((sub_m or {}).get("lines") or [])
    lw = " ".join((sub_w or {}).get("lines") or [])
    check(sub_m is not None and "Earnings quality" in lm and "Earnings quality" not in lw,
          "the Monthly's 'What's carrying the index' prints it; the Weekly's does not")
    st.close()


def group_e() -> None:
    print(f"\n{LINE}\nE. THE LEDGER AND CONFIG\n{LINE}")
    from altdata import config as acfg, derived, earnings_quality as eq
    cfg = eq.config()
    led = (REPO / cfg["calibration"]["ledger"]).read_text(encoding="utf-8")
    head, _, result = led.partition("<!-- RESULT BELOW.")
    rule = next(ln[2:] for ln in head.splitlines() if ln.startswith("> "))
    check(eq.rule_sha256(rule) == cfg["calibration"]["rule_sha256"]
          and cfg["calibration"]["rule_sha256"] in head,
          "the head's pre-registered rule hashes to config's rule_sha256, printed at the head")
    m = re.search(r"\*\*Verdict: (?:AMBIGUOUS\. )?[Tt]he margin is (\d+) points", result)
    check(result.count("## Result") == 1 and bool(m) and float(m.group(1)) == float(cfg["margin"]),
          f"the Result is written once and its margin is config's ({cfg['margin']})")
    check(bool(re.search(r"\*\*\d+ false-positive episodes since 1990\*\*", result)),
          "the Result reports the false positives since 1990")
    check((REPO / cfg["calibration"]["ledger"]).with_suffix(".csv").exists(),
          "the per-quarter CSV sits beside it")
    ids = {s.fred_id: s.key for s in acfg.FRED_PULL_SERIES}
    check(ids.get("CPATAX") == "cpatax" and ids.get("A463RC1Q027SBEA") == "profits_domestic_nonfin",
          "CPATAX and A463RC1Q027SBEA are in the FRED pull")
    for k in ("fred.cpatax", "fred.profits_domestic_nonfin"):
        check(bool(derived.market_state_barred(derived.registry_entry(k))),
              f"{k} is registered and barred from the market-state object")
    check(cfg["keys"]["eps"] == "shiller.sp_earnings" and "operating EPS not tracked" in cfg["eps_label"],
          "V-104a: Shiller's reported EPS, labelled; operating EPS not tracked")
    gm = (REPO / "docs" / "master-guide.md").read_text(encoding="utf-8")
    check("`earnings-quality-calibration-2026-11.md`" in gm, "Table 7a carries the ledger")


def main() -> int:
    pin_clock()
    print(f"the gate's clock is pinned to {GATE_NOW}")
    print(f"{LINE}\nBATCH 22 ITEMS 121 AND 122: THE FORWARD TGA ROW AND EARNINGS QUALITY\n{LINE}")
    for g in (group_a, group_b, group_c, group_d, group_e):
        g()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
