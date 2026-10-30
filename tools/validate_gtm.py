"""
THE J.P. MORGAN GUIDE BATCH, PARTS 1 AND 2 (GTM-1, 3, 4, 7, 8, 9, 10, 12, 13, 15,
21), on fixtures.

  A  THE SOURCED FIGURES. Every declared figure's quote is in the scan, its
     value inside its quote, with a section and the scan's as-of; a fixture
     figure without a section, a quote, or a quote the scan contains is refused,
     and a scan header without an as-of refuses them all. The ingest stores them
     beside the reference table, idempotently, and the printed cell is the
     stored text -- never recomputed.
  B  GTM-7. The par-bond return by hand (-7.022%); a fixture whose equity return
     is a linear function of the bond's correlates at +1.00; CPI at 0.5% a month
     is 6.1678% on the year; an era the history does not reach prints the
     Guide's figure, labelled; the regime word by its bands.
  C  GTM-8. One peak and one trough on the fixture, -10.00% and +25.00% with
     n = 1 each, the trough at a price low, the caveat in the row.
  D  GTM-9. Six all-time highs in twelve sessions, four floors, five repeats
     within a week; five this year in ten sessions.
  E  GTM-13. The year to date +2.5152% by hand; the correlations -1.00 and +1.00
     on the duration-linear fixture; TLT +/-16.5% from its reference duration;
     AGG "no duration in the reference"; TIPS, munis and MBS "no proxy".
  F  GTM-15 and GTM-21. 12.3457% on the tariff fixture; the debt-service
     ratio's two percentiles with their n.
  G  NOT STORED. On an empty store every cell of every table prints a word,
     never a blank or a zero; the base-rate rows carry n.
  H  THE REGISTER. SR-5 and SR-9 keep their keys; the new numbers are the
     run from SR-48, SR-49 skipped (ruling 4); the drafts are marked accepted.
  I  PLACEMENT AND THE BUDGETS. The Weekly's Plumbing carries GTM-13 only, the
     Monthly's three, Slow layers four; every sub-section is tables and lines
     (no word in the budget, no chart); the Weekly's tables are six columns at
     most.
  J  NOTHING LIVE. No network, model or order import; no read of a default
     store path a caller did not name; the FRED series registered with family
     and long_window.

  PART 2 (gtm-core-2, 17 Oct 2026; hand figures in tests/fixtures/gtm/README.md):
  K  GTM-3. The concentration twin reconciles to the hand figures on a fixture
     of holdings and multiples (39.4%, 29.4286%, 27.7861x, 16.9178x, 20.0x, and
     the own averages); its cap share is item 31's; a name without its multiple
     leaves the cell not stored, naming it, with the Guide's figure beside.
  L  GTM-4. The hyperscaler bucket reconciles (19.2%, +6.2374%, 25.9576x); a
     member missing from the store prints the Guide's figure, labelled, never a
     partial computation; the GICS buckets print the Guide's. The cash-flow
     bridge parses a fixture of the XBRL frames (380 / 155 / 225 bn in CY2023)
     and prints "not stored" where a filer lacks a tag; with no SEC contact the
     reader is PENDING and fetches nothing.
  M  GTM-10. The sector correlation reproduces the hand figure (-0.8964); a
     window the store does not cover is "not reached"; the Weekly's leadership
     table gains one column; the Monthly's sector table carries the Guide's rows.
  N  GTM-15 MONTHLY. The MTS reader keeps the customs line only; 10.8% for the
     month and 10.2695% over three months, the refunds beside.
  O  GTM-12. The federal shares reconcile (15.7143%, 14.2857%, 25.7143%, 5.9% of
     GDP); the CBO path prints as a sourced figure.
  P  EVERY SOURCED FIGURE CARRIES ITS SLIDE AND AS-OF: all of them, part 2's
     included; a part-2 fixture figure without a slide is refused.
  Q  THE QUEUE ENTRY IS A DRAFT AND GRANTS NOTHING: every entry draft, rights
     none, position the operator's; the overlay's inputs diffed against the
     ones pinned here; no code reads the queue file.

    python tools/validate_gtm.py
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import ast
import csv
import json
import re
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

from altdata import gtm, observations, scans                    # noqa: E402
from gate_tmp import mkdtemp                                    # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FIX = REPO / "tests" / "fixtures" / "gtm"
SCAN = REPO / "docs" / "scans" / "jpm-gtm-2026q4.md"
LINE = "=" * 78
PASS = FAIL = 0
TD = Path(mkdtemp("gtm-gate-"))
# The declared sourced figures: part 1's 9 non-GTM-1 groups plus GTM-1's 24
# slide-4 cells and the Guide's 30 Sep row, then part 2's (GTM-3, 4, 10, 12).
N_SOURCED = 167


def check(c: bool, m: str) -> bool:
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


def close(a, b, tol=1e-4) -> bool:
    return a is not None and b is not None and abs(a - b) <= tol


def rows_of(name: str) -> list[dict]:
    with open(FIX / name, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def obs(key: str, day: str, value: float, inst=None) -> dict:
    return {"registry_key": key, "instrument": inst, "observed_at": day,
            "available_at": f"{day}T21:00:00+00:00", "value": value,
            "source": "fixture"}


def store(rows: list[dict], name: str) -> str:
    p = str(TD / f"{name}.db")
    with observations.ObservationStore(p) as st:
        st.write_many(rows)
    return p


CUT = "2026-10-31T12:00:00+00:00"


# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. THE SOURCED FIGURES: QUOTED, SECTIONED, DATED, STORED, NEVER RECOMPUTED")
    cfg = gtm.config()
    text = SCAN.read_text(encoding="utf-8")
    figs, refused = gtm.sourced_figures(cfg, SCAN)
    check(len(figs) == len(cfg["sourced"]) == N_SOURCED and not refused
          and all(f["section_ref"] and f["slide"] and f["as_of"] == "2026-09-30"
                  and f["read_on"] == "2026-10-03"
                  and f["source_url"].startswith("https://am.jpmorgan.com/")
                  for f in figs),
          f"all {len(figs)} declared figures pass: each quote in the scan, its value "
          f"inside its quote, a section, a slide, the scan's as-of (30 Sep 2026) "
          f"and URL")
    good = dict(cfg["sourced"][0])
    bad = {"no section": {**good, "section": ""},
           "no quote": {**good, "quote": ""},
           "a quote the scan does not contain": {**good, "quote": "a sentence not in it"},
           "a value outside its quote": {**good, "value": "99x"},
           "no slide": {**good, "slide": None}}
    why = {k: gtm.sourced_refusal(v, text) for k, v in bad.items()}
    check(all(why.values()) and gtm.sourced_refusal(good, text) is None,
          f"a fixture figure is refused for each fault ({why})")
    nodate = TD / "jpm-gtm-2026q4.md"
    nodate.write_text(re.sub(r"data as of 30 September 2026", "data undated",
                             text.replace("(as of 30 Sep 2026)", "")), encoding="utf-8")
    f2, r2 = gtm.sourced_figures(cfg, nodate)
    check(not f2 and len(r2) == N_SOURCED and all(r["reason"] == "no as-of date" for r in r2),
          "a scan whose header and table carry no as-of: every figure refused, "
          "\"no as-of date\"")
    db = str(TD / "scans.db")
    first = scans.ingest([SCAN], db_path=db)
    again = scans.ingest([SCAN], db_path=db)
    by = {s["scan_id"]: s for s in first["scans"]}
    check(by.get("jpm-gtm-2026q4:gtm", {}).get("added") == N_SOURCED
          and by["jpm-gtm-2026q4"]["added"] == 44 and again["added"] == 0,
          f"the ingest stores the {N_SOURCED} beside the 44 reference-table rows, and a "
          "re-ingest adds none")
    src = gtm.sourced(CUT, db)
    con = sqlite3.connect(db)
    secs = {r[0] for r in con.execute("SELECT section_ref FROM scan_figures WHERE "
                                      "metric LIKE 'GTM-%'")}
    con.close()
    check(len(src) == N_SOURCED and secs == {"§4", "§6", "§7"}
          and src["gtm7.2000-2020.corr"]["value"] == "−0.31"
          and gtm.cite(src["gtm8.troughs"]) == "+24.1% (the Guide, §4, slide 30, as of 2026-09-30)",
          "read back by id with the scan's own section; a cell prints the stored "
          "text verbatim (−0.31, +24.1%), never a recomputed number")
    check(not gtm.sourced("2026-10-02", db),
          "point in time: before the read (3 Oct) no GTM figure is readable")


# ---------------------------------------------------------------------------
def group_b() -> None:
    head("B. GTM-7: THE ERAS RECONCILE TO HAND FIGURES")
    check(close(gtm.par_bond_price(0.05, 0.06, 10) - 1 + 0.05 / 12, -0.070221, 1e-6),
          "a 5% 10-year par bond priced at 6%, plus a month's coupon: -7.022% (hand)")
    months = gtm._months("1998-01", "2003-12")
    gs10 = {m: 5.0 + 0.5 * ((i * 7) % 5 - 2) / 2 for i, m in enumerate(months)}
    price, div, cpi = {}, {}, {}
    p, c = 100.0, 100.0
    for i, m in enumerate(months):
        if i:
            prev = months[i - 1]
            bd = gtm.par_bond_price(gs10[prev] / 100, gs10[m] / 100, 10) - 1 \
                + gs10[prev] / 100 / 12
            p *= 1 + 2 * bd + 0.001
            c *= 1.005
        price[m], div[m], cpi[m] = p, 0.0, c
    cfg = gtm.config()
    cfg = {**cfg, "stock_bond": {**cfg["stock_bond"], "eras": [
        {"id": "a", "label": "2000 to 2001", "start": "2000-01", "end": "2001-12"},
        {"id": "b", "label": "1990 to 1995", "start": "1990-01", "end": "1995-12"}]}}
    sb = gtm.stock_bond_eras(price, div, cpi, gs10, cfg)
    a, b = sb["eras"]
    check(a["computed"] and close(a["correlation"], 1.0) and a["n_windows"] == 24
          and close(a["inflation"], 6.1678),
          f"a covered era: +1.00 over 24 windows, inflation 6.1678% "
          f"({a['correlation']}, {a['inflation']})")
    check(not b["computed"] and b["correlation"] is None and b["coverage"] == 0.0,
          "an era the history does not reach is not computed")
    from daily_cascade import gtm_block
    sub = gtm_block.stock_bond_subsection({"stock_bond": {**sb, "eras": [b]},
                                           "sourced": {}})
    check("not reached" in sub["table"]["rows"][0][1]
          and "(the Guide, labelled)" in sub["table"]["rows"][0][4],
          "and prints \"not reached\" beside the Guide's figure, labelled")
    cur = sb["current"]
    sub = gtm_block.stock_bond_subsection({"stock_bond": sb, "sourced": {
        "gtm7.2021-now.corr": {"value": "+0.33"}}})
    last = sub["table"]["rows"][-1]
    y, m = map(int, cur["month"].split("-"))
    k = y * 12 + m - 1 - 23
    check(cur["from"] == f"{k // 12:04d}-{k % 12 + 1:02d}"
          and last[0] == f"Latest 24-month window ({cur['from']} to {cur['month']})"
          and "era 2021 to 2025: +0.33" in last[4]
          and "read on the latest 24-month window" in sub["lines"][0],
          "step 0.5: the latest 24-month window prints with its own window beside "
          "the Guide's 2021 to 2025 era, and the table says which window the word "
          f"is read on ({last[:2]})")
    bands = cfg["stock_bond"]["regime_bands"]
    check([gtm.regime_word(x, bands) for x in (0.3, 0.05, -0.2, None)]
          == ["positive", "near zero", "negative", None],
          "the regime word by its bands: +0.30 positive, +0.05 near zero, "
          "-0.20 negative, none without a reading")


# ---------------------------------------------------------------------------
def group_c() -> None:
    head("C. GTM-8: THE TURNING-POINT BASE RATE, WITH n")
    sent = [(r["month"], float(r["value"])) for r in rows_of("sentiment_monthly.csv")]
    spx = [(r["day"], float(r["close"])) for r in rows_of("spx_month_end.csv")]
    se = gtm.sentiment_base_rate(sent, spx)
    eps = [(e["month"], e["kind"]) for e in se["episodes"]]
    check(eps == [("2001-06", "peak"), ("2002-12", "trough")],
          f"one peak (2001-06) and one trough (2002-12); 2004 has no full window ({eps})")
    check(se["peaks"]["n"] == 1 and close(se["peaks"]["mean"], -10.0)
          and se["troughs"]["n"] == 1 and close(se["troughs"]["mean"], 25.0),
          "after the peak -10.00%, after the trough +25.00%, n = 1 each (hand)")
    check(se["troughs"]["at_price_low"] == 1 and se["troughs"]["with_price"] == 1
          and close(se["current"]["percentile_full"], 98.3333)
          and se["current"]["n_full"] == 60,
          "the trough came 20% below the 12-month high (1 of 1); the current 80 is "
          "the 98.33rd percentile of 60")
    from daily_cascade import gtm_block
    sub = gtm_block.sentiment_subsection({"sentiment": se, "sourced": {}})
    caveat = gtm.config()["sentiment"]["caveat"]
    check(caveat == "every sampled trough coincided with a price low; this one is "
                    "at a high"
          and any(caveat in ln for ln in sub["lines"])
          and [r[1] for r in sub["table"]["rows"]] == ["1", "1"],
          "the order's caveat prints in the row, and the table carries n")


# ---------------------------------------------------------------------------
def group_d() -> None:
    head("D. GTM-9: THE ALL-TIME-HIGH SHARES")
    c = [(r["day"], float(r["close"])) for r in rows_of("ath_closes.csv")]
    a = gtm.ath_stats(c)
    check(a["ath_count"] == 6 and a["sessions"] == 12
          and close(a["share_of_sessions"], 50.0) and a["floors"] == 4
          and close(a["share_floors"], 66.6667) and a["followed_within"] == 5
          and close(a["share_followed_within"], 83.3333),
          f"6 all-time highs in 12 sessions (50%), 4 floors (66.67%), 5 repeats "
          f"within a week (83.33%) -- the hand table ({a['ath_count']}, "
          f"{a['floors']}, {a['followed_within']})")
    y = gtm.ath_year_to_date(c, "2026-01-15")
    check(y["ath_count"] == 5 and y["sessions"] == 10 and close(y["share_of_sessions"], 50.0),
          "this year to 15 Jan: 5 in 10 sessions (50%)")
    check(gtm.config()["all_time_highs"]["definition_source"].startswith("the scan's"),
          "the floor definition is the scan's, and says so")


# ---------------------------------------------------------------------------
def fi_store() -> str:
    rows = []
    for r in rows_of("fi_series.csv"):
        rows += [obs("fred.yield_10y", r["day"], float(r["y10"])),
                 obs("yfinance.mkt_tlt", r["day"], float(r["tlt"])),
                 obs("yfinance.mkt_spy", r["day"], float(r["spy"]))]
    for r in rows_of("shy_ytd.csv"):
        rows.append(obs("yfinance.mkt_shy", r["day"], float(r["close"])))
        if float(r["dividend"]):
            rows.append(obs("yfinance.mkt_shy_dividend", r["day"], float(r["dividend"])))
    for f in ("tariff.csv", "dsr.csv"):
        rows += [obs(r["key"], r["day"], float(r["value"])) for r in rows_of(f)]
    return store(rows, "fi")


def group_e() -> None:
    head("E. GTM-13: THE DURATION RETURNS AND THE CORRELATIONS")
    db = fi_store()
    with observations.ObservationStore(db) as st:
        fi = gtm.fixed_income(st, "2026-01-30T22:00:00+00:00")
        shy_ytd = gtm.ytd_total_return(gtm.points(st, "yfinance.mkt_shy", CUT),
                                       gtm.points(st, "yfinance.mkt_shy_dividend", CUT),
                                       "2026-01-06")
    by = {r["sector"]: r for r in fi["rows"]}
    check(close(shy_ytd, 2.51515, 1e-4),
          f"SHY's year to date with a 0.50 dividend: +2.5152% (hand; {shy_ytd})")
    t = by["Treasury 30-year"]
    check(close(t["corr_rate"], -1.0) and close(t["corr_equity"], 1.0)
          and t["n_rate"] > 30,
          f"TLT against the 10-year's change -1.00 and against SPY +1.00 "
          f"({t['corr_rate']}, {t['corr_equity']}, n={t['n_rate']})")
    check(t["duration"] == 16.5 and t["scenario"] == {"down": 16.5, "up": -16.5}
          and by["Treasury 2-year"]["scenario"] == {"down": 1.9, "up": -1.9},
          "TLT 16.5 years: +16.5% under -100 bp, -16.5% under +100 bp; SHY +/-1.9% "
          "(config/instrument_reference.yaml)")
    agg = by["Aggregate"]
    check(agg["duration"] == 5.70 and agg["scenario"] == {"down": 5.7, "up": -5.7}
          and "iShares product page" in agg["duration_source"]
          and "2026-10-15" in agg["duration_source"],
          "ruling 2: AGG's duration is the issuer's own, 5.70 years as of 15 Oct "
          "2026: +/-5.7% under a 100 bp shift")
    want = {"TIPS": ("TIP", 6.19), "Municipals": ("MUB", 7.13), "MBS": ("MBB", 5.75)}
    check(all(by[s]["proxy"] == px and by[s]["duration"] == d
              and by[s]["state"] == gtm.NOT_STORED for s, (px, d) in want.items()),
          "ruling 2: TIPS, munis and MBS have their proxies (TIP, MUB, MBB) with the "
          "issuer's durations, and a proxy with no closes stored prints \"not stored\"")


def group_f() -> None:
    head("F. GTM-15 AND GTM-21: THE RATIOS AND THEIR PERCENTILES")
    db = str(TD / "fi.db")
    with observations.ObservationStore(db) as st:
        t = gtm.tariff(st, CUT)
        d = gtm.dsr(st, CUT)
    check(t["state"] == "ok" and close(t["latest"], 12.345679) and t["day"] == "2026-04-01"
          and t["n_full"] == 3 and t["pctile_full"] == 100.0
          and t["series_ids"] == ["B235RC1Q027SBEA", "BOPGIMP"],
          f"customs 400 over 4 x 810,000 mn of imports: 12.3457% (hand), the 100th "
          f"of 3, from B235RC1Q027SBEA and BOPGIMP ({t.get('latest')})")
    h = d["rows"][0]
    check(h["latest"] == 11.3 and h["n_5y"] == 4 and h["pctile_5y"] == 100.0
          and h["n_full"] == 5 and h["pctile_full"] == 80.0,
          "TDSP 11.3: the 100th of 4 over five years, the 80th of 5 over the full "
          "history (hand)")


# ---------------------------------------------------------------------------
def group_g() -> None:
    head("G. NOT STORED: NEVER A BLANK OR A ZERO; THE BASE-RATE ROWS CARRY n")
    from daily_cascade import gtm_block
    db = store([], "empty")
    scans.ingest([SCAN], db_path=db)
    with observations.ObservationStore(db) as st:
        gtm_block._CACHE.clear()
        subs = (gtm_block.plumbing_subsections(st, CUT, "monthly")
                + gtm_block.slow_subsections(st, CUT))
        base = gtm_block.base_rate_rows(st, CUT)
    cells = [c for s in subs for t in [s["table"], *(s.get("tables") or [])]
             for r in t["rows"] for c in r]
    check(len(subs) == 8 and cells and all(isinstance(c, str) and c.strip()
                                           and c.strip() not in ("0", "0.0", "0%")
                                           for c in cells),
          f"on an empty store all eight tables print a word in every cell "
          f"({len(cells)} cells; none blank, none zero)")
    today = next(s for s in subs if s["title"] == gtm_block.INFLECTION_TITLE)["table"]["rows"][-1]
    check(today[1:5] == ["not stored"] * 4,
          "GTM-1's today row prints \"not stored\" for each absent input")
    inf = next(s for s in subs if s["title"] == gtm_block.INFLECTION_TITLE)["table"]
    bottom = next(r for r in inf["rows"] if r[0].startswith("9 Mar 2009"))
    top = next(r for r in inf["rows"] if r[0].startswith("24 Mar 2000"))
    check(top[1:6] == ["1,527", "25.2x", "1.4%", "6.2%",
                       "the Guide, slide 4, as of 30 Sep 2026"]
          and bottom[1:5] == ["677", "10.4x", "not on the slide", "not on the slide"],
          "GTM-1 (step 0.4): slide 4's cells print verbatim with the slide and "
          "as-of; a cell the slide does not print prints \"not on the slide\"")
    with observations.ObservationStore(store([], "bare")) as st0:
        gtm_block._CACHE.clear()
        inf0 = gtm_block.slow_subsections(st0, CUT)[0]["table"]
    b0 = next(r for r in inf0["rows"] if r[0].startswith("9 Mar 2009"))
    check(b0[1:5] == ["not stored", "not stored", "not on the slide",
                      "not on the slide"],
          "with nothing ingested, a declared cell prints \"not stored\", never "
          "blank")
    db2 = fi_store()
    rows = [obs("yfinance.mkt_gspc", r["day"], float(r["close"]))
            for r in rows_of("ath_closes.csv")]
    rows += [obs("fred.uoM_sent", r["month"], float(r["value"]))
             for r in rows_of("sentiment_monthly.csv")]
    with observations.ObservationStore(db2) as st:
        st.write_many(rows)
        gtm_block._CACHE.clear()
        base = gtm_block.base_rate_rows(st, CUT)
    check(len(base) == 3 and all(re.search(r"n=\d+", r[0]) for r in base),
          f"each base-rate row carries its n ({[r[0] for r in base]})")


# ---------------------------------------------------------------------------
def group_h() -> None:
    head("H. THE REGISTER: KEYS KEPT, NUMBERS MECHANICAL, DRAFTS MARKED")
    reg = (REPO / "docs" / "signal-triage-register.md").read_text(encoding="utf-8")
    nums = gtm.config()["register_numbers"]
    check(nums["GTM-7"] == "SR-9" and nums["GTM-21"] == "SR-5"
          and "### SR-5 Consumer credit impulse" in reg
          and "### SR-9 5.25% and stock-bond correlation" in reg,
          "SR-5 and SR-9 keep their keys and headings; GTM-21 and GTM-7 amend them")
    adopted = ["GTM-1", "GTM-3", "GTM-4", "GTM-8", "GTM-9", "GTM-10", "GTM-11",
               "GTM-12", "GTM-13", "GTM-14", "GTM-15"]
    fresh = [48, *range(50, 60)]
    check([nums[g] for g in adopted] == [f"SR-{n}" for n in fresh]
          and "SR-49" not in nums.values(),
          "the eleven numbers run from SR-48 in the order's table order, SR-49 "
          "skipped as the shape axis's working number (ruling 4, 17 Oct)")
    check(all(f"### SR-{n} " in reg for n in (48, 52, 53, 57, 59))
          and not any(f"### SR-{n} " in reg for n in (37, 40, 41, 45, 47))
          and all(f"### SR-{n} " in reg for n in (50, 51, 54, 56))
          and reg.count("*Accepted as drafted (rule 31), 17 Oct 2026") == 2,
          "part 1's five and part 2's four have entries; the SR-5 and SR-9 "
          "amendments are marked accepted as drafted (17 Oct)")
    nar = (REPO / "config" / "narratives.yaml").read_text(encoding="utf-8")
    check("disagreements:" in nar and "gtm8_sentiment_trough_at_high" in nar
          and "status: accepted" in nar,
          "the GTM-8 disagreement entry is in the narrative register's config, "
          "accepted as drafted, read by no code")
    br = (REPO / "docs" / "whitepapers" / "base-rates-whitepaper.md").read_text(encoding="utf-8")
    check("A-6 " in br and "A-7 " in br and "GTM-7" in br and "GTM-13" in br,
          "Book A's rule table gains its two candidate rows (A-6 the regime word, "
          "A-7 the duration modifier), dated")


# ---------------------------------------------------------------------------
def group_i() -> None:
    head("I. PLACEMENT AND THE BUDGETS")
    from daily_cascade import gtm_block, stack
    db = store([], "place")
    with observations.ObservationStore(db) as st:
        gtm_block._CACHE.clear()
        wk = gtm_block.plumbing_subsections(st, CUT, "weekly")
        mo = gtm_block.plumbing_subsections(st, CUT, "monthly")
        sl = gtm_block.slow_subsections(st, CUT)
    check([s["title"] for s in wk] == [gtm_block.FI_TITLE]
          and [s["title"] for s in mo] == [gtm_block.FI_TITLE, gtm_block.TARIFF_TITLE,
                                           gtm_block.DSR_TITLE, gtm_block.FEDERAL_TITLE]
          and [s["title"] for s in sl] == [gtm_block.INFLECTION_TITLE,
                                           gtm_block.SB_TITLE, gtm_block.SENT_TITLE,
                                           gtm_block.ATH_TITLE],
          "the Weekly's Plumbing carries GTM-13; the Monthly's adds GTM-15, GTM-21 "
          "and GTM-12; Slow layers GTM-1, 7, 8 and 9")
    with observations.ObservationStore(db) as st:
        gtm_block._ECACHE.clear()
        mwk = gtm_block.mechanics_subsections(st, CUT, "weekly")
        mmo = gtm_block.mechanics_subsections(st, CUT, "monthly")
    check([s["title"] for s in mwk] == [s["title"] for s in mmo]
          == [gtm_block.TWIN_TITLE, gtm_block.BUCKETS_TITLE]
          and not mwk[1]["tables"] and mmo[1]["tables"][0]["columns"]
          == gtm_block.BRIDGE_COLUMNS,
          "Mechanics: the twin (GTM-3) and the buckets (GTM-4) at both cadences; the "
          "cash-flow bridge in the Monthly's only")
    t31, fcf = {"title": "Concentration and breadth"}, {"title": "AI FCF panel"}
    oil = {"title": "The oil-shock signature"}
    mo_order = [x["title"] for x in gtm_block.place_mechanics(
        [fcf, {"title": "rev"}, t31, oil], mmo, after_panel="AI FCF panel")]
    wk_order = [x["title"] for x in gtm_block.place_mechanics([t31, oil], mwk)]
    check(mo_order == ["AI FCF panel", gtm_block.BUCKETS_TITLE, "rev",
                       "Concentration and breadth", gtm_block.TWIN_TITLE,
                       "The oil-shock signature"]
          and wk_order == ["Concentration and breadth", gtm_block.TWIN_TITLE,
                           gtm_block.BUCKETS_TITLE, "The oil-shock signature"],
          "placement: the bucket exhibit after the SR-37 panel (the Monthly's Factor "
          "I exhibit); the twin beside item 31's table, at both cadences")
    allsub = wk + mo + sl + mwk + mmo
    check(all(s.get("paragraph_wanted") is False and not s.get("paragraphs")
              and not s.get("charts") and stack.section_words(s) == 0 for s in allsub),
          "every sub-section is tables and lines: no paragraph asked, no chart, "
          "zero words in the budget")
    check(all(len(t["columns"]) <= 6 for s in wk + mwk + mmo
              for t in [s["table"], *(s.get("tables") or [])]),
          "the Weekly's tables and part 2's keep six columns at most (the mobile "
          "rule)")
    src = (REPO / "monthly_macro" / "stack.py").read_text(encoding="utf-8")
    wsrc = (REPO / "daily_cascade" / "weekly_stack.py").read_text(encoding="utf-8")
    check("gtm_block.slow_subsections(st, now, db_path)" in src
          and "gtm_block.base_rate_rows(st, now, db_path)" in src
          and 'gtm_block.plumbing_subsections(st, now, "monthly")' in src
          and 'gtm_block.plumbing_subsections(st, now, "weekly")' in wsrc
          and 'gtm_block.mechanics_subsections(st, now, "monthly")' in src
          and "after_panel=fcf[\"title\"]" in src
          and "gtm_block.mechanics_subsections(\n        st, cutoff, \"weekly\")" in wsrc
          and "gtm_block.sector_corr_column(" in wsrc
          and "gtm_block.sector_table(st, now)" in wsrc,
          "the Monthly and the Weekly call the block where the order places it")


# ---------------------------------------------------------------------------
def group_j() -> None:
    head("J. NOTHING LIVE; THE SERIES REGISTERED")
    banned = {"requests", "urllib", "httpx", "anthropic", "subprocess", "socket",
              "altdata.model_meter", "register", "ibkr"}
    hits = []
    for f in ("altdata/gtm.py", "altdata/gtm_equities.py", "daily_cascade/gtm_block.py"):
        tree = ast.parse((REPO / f).read_text(encoding="utf-8"))
        for n in ast.walk(tree):
            names = ([a.name for a in n.names] if isinstance(n, ast.Import)
                     else [n.module or ""] if isinstance(n, ast.ImportFrom) else [])
            hits += [f"{f}: {x}" for x in names
                     if any(x == b or x.startswith(b + ".") for b in banned)]
    check(not hits, f"no network, model, order or register import ({hits})")
    called = []
    orig = scans.latest
    scans.latest = lambda *a, **k: called.append(a) or []
    try:
        b = gtm.build(None, CUT)
    finally:
        scans.latest = orig
    from altdata import gtm_equities as ge
    try:
        scans.latest = lambda *a, **k: called.append(a) or []
        e = ge.build(None, CUT)
    finally:
        scans.latest = orig
    check(not called and b["sourced"] == {} and e["sourced"] == {},
          "with no store and no path named, the sourced figures are not read from a "
          "default path (no live store)")
    from altdata import derived, config as acfg
    keys = ["fred.customs_duties", "fred.goods_imports", "fred.dsr_household",
            "fred.dsr_consumer", "fred.dsr_mortgage", "fred.fed_interest_payments",
            "fred.fed_defense", "fred.fy_net_interest", "fred.fy_net_outlays",
            "fred.fy_deficit", "fred.fy_deficit_gdp"]
    # fed_interest_payments is pulled once, under 6e-rest's spec (the chain-2 stitch).
    specs = {f"fred.{s.key}": s for s in acfg.FRED_PULL_SERIES}
    reg = __import__("yaml").safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    check(all(k in specs for k in keys)
          and [specs[k].fred_id for k in keys] == ["B235RC1Q027SBEA", "BOPGIMP", "TDSP",
                                                   "CDSP", "MDSP", "A091RC1Q027SBEA",
                                                   "FDEFX", "FYOINT", "FYONET",
                                                   "FYFSD", "FYFSGDA188S"]
          and [specs[k].units for k in keys[5:]] == ["B", "B", "M", "M", "M", "%"]
          and all(reg["families"].get(k) and reg["long_windows"].get(k) == "full"
                  for k in keys)
          and all(derived.registry_entry(k) for k in keys),
          "the eleven FRED series (part 1's five, GTM-12's six, each unit read off "
          "its FRED page) are pulled, registered, and carry family and long_window")
    new = ["fiscaldata.mts_customs_gross", "fiscaldata.mts_customs_refunds",
           "fiscaldata.mts_customs_net", "edgar.xbrl_operating_cash_flow",
           "edgar.xbrl_capex", "yfinance.mkt_tip", "yfinance.mkt_mub",
           "yfinance.mkt_mbb"]
    check(all(derived.registry_entry(k) and reg["families"].get(k)
              and reg["long_windows"].get(k) == "full" for k in new)
          and derived.registry_entry("edgar.xbrl_capex").get("units") == "usd",
          "part 2's stored keys are registered with units, family and long_window")
    cat = (REPO / "config" / "catalogue_commands.yaml").read_text(encoding="utf-8")
    check("altdata.gtm:" in cat and "altdata.gtm_equities:" in cat
          and "altdata.sources.edgar_xbrl:" in cat,
          "the catalogue lists altdata.gtm, altdata.gtm_equities and the XBRL reader")
    from altdata import feeds
    from altdata.sources import yfinance_source as yf
    check("edgar_xbrl" in feeds.EXTERNAL_WRITERS
          and all(yf.SYMBOLS.get(t) == f"mkt_{t.lower()}" for t in ("TIP", "MUB", "MBB")),
          "the XBRL reader is scheduled with the external writers; TIP, MUB and MBB "
          "are in the price basket")


# ---------------------------------------------------------------------------
# Part 2
# ---------------------------------------------------------------------------
C2 = "2026-10-17T21:00:00+00:00"


def holdings_rows(drop: tuple = ()) -> list[dict]:
    """The fixture's holdings and multiples as store rows; `drop` removes a
    (key, ticker) pair's rows."""
    out = []
    for r in rows_of("holdings_multiples.csv"):
        tk, d = r["ticker"], r["day"]
        out.append(obs("sp500.member_weight", d, float(r["weight"]), tk))
        if ("yf.trailing_pe", tk) not in drop:
            out.append(obs("yf.trailing_pe", d, float(r["trailing_pe"]), tk))
        if ("yf.forward_pe", tk) not in drop:
            out.append(obs("yf.forward_pe", d, float(r["forward_pe"]), tk))
    out += [obs("yfinance.mkt_gspc", "2026-10-15", 5940.0),
            obs("yfinance.mkt_gspc", "2026-10-16", 6000.0),
            obs("shiller.sp_earnings", "2026-06-01", 240.0),
            obs("spdji.fwd12m_op_eps", "2026-10-01", 300.0)]
    for r in rows_of("hyperscaler_closes.csv"):
        out.append(obs("sp500.member_close", "2025-12-31", float(r["close_2025_12_31"]),
                       r["ticker"]))
        out.append(obs("sp500.member_close", "2026-10-16", float(r["close_2026_10_16"]),
                       r["ticker"]))
    return out


def group_k() -> None:
    head("K. GTM-3: THE CONCENTRATION TWIN RECONCILES TO THE HAND FIGURES")
    from altdata import gtm_equities as ge, st_r5_t1_rest as tr
    from daily_cascade import gtm_block
    db = store(holdings_rows(), "twin")
    scans.ingest([SCAN], db_path=db)
    with observations.ObservationStore(db) as st:
        t = ge.concentration_twin(st, C2)
        item31 = tr.concentration(st, C2)
        gtm_block._ECACHE.clear()
        sub = gtm_block.mechanics_subsections(st, C2, "weekly")[0]
    L = t["latest"]
    check(t["state"] == "ok" and L["day"] == "2026-10-16" and close(L["cap_share"], 39.4)
          and L["issuers"] == ["NVDA", "MSFT", "AAPL", "AMZN", "GOOGL", "META", "AVGO",
                               "TSLA", "BRK-B", "JPM"],
          f"the ten largest issuers on 16 Oct, GOOG with GOOGL: 39.4% of the cap "
          f"(hand; {L.get('cap_share')})")
    check(item31.get("state") == "read" and close(item31["top_share_pct"], L["cap_share"], 0.01),
          f"the cap share is item 31's own top-10 share ({item31.get('top_share_pct')})")
    check(close(L["earn_share"], 29.428571) and L["index_earnings_month"] == "2026-06",
          f"earnings share: sum(w/PE) x the index's trailing P/E (6,000 / 240 = 25) = "
          f"29.4286% (hand; {L.get('earn_share')}), Shiller's month named")
    check(close(L["pe_top"], 27.786133) and close(L["pe_other"], 16.917798)
          and close(L["pe_index"], 20.0),
          f"forward P/E: the top 10 27.7861x, the other 490 16.9178x, the index 20.0x "
          f"(hand; {L.get('pe_top')}, {L.get('pe_other')}, {L.get('pe_index')})")
    o = t["own"]
    check(o["pe_index"]["n"] == 2 and close(o["pe_index"]["average"], 19.9)
          and close(o["pe_index"]["pct_of_average"], 100.50, 0.01)
          and close(o["pe_other"]["pct_of_average"], 100.70, 0.01)
          and close(o["pe_top"]["pct_of_average"], 100.0, 0.01)
          and o["pe_index"]["short"] and o["pe_index"]["from"] == "2026-10-15",
          "own averages over the two stored days, with the window and n: 100.50%, "
          "100.70%, 100%; the history is marked short")
    rows = {r[0]: r for r in sub["table"]["rows"]}
    avg = sub["tables"][0]["rows"]
    check(rows["Top-10 share of index market cap"][3] == "40.6%"
          and rows["Forward P/E, the top 10"][1] == "27.8x"
          and rows["Forward P/E, the top 10"][3] == "20.9x"
          and avg[0][3] == "100%" and avg[1][3] == "112%" and avg[2][3] == "113%"
          and any("short" in c for c in avg[0]),
          "the exhibit prints ours beside the Guide's slide-8 figures (40.6%, 20.9x; "
          "100%, 112% and 113% of own average), and says our history is short")
    db2 = store(holdings_rows(drop=(("yf.forward_pe", "BRK-B"),)), "twin_missing")
    scans.ingest([SCAN], db_path=db2)
    with observations.ObservationStore(db2) as st:
        t2 = ge.concentration_twin(st, C2)
        gtm_block._ECACHE.clear()
        sub2 = gtm_block.mechanics_subsections(st, C2, "weekly")[0]
    r2 = {r[0]: r for r in sub2["table"]["rows"]}
    check(t2["latest"]["pe_top"] is None and t2["latest"]["pe_other"] is None
          and t2["latest"]["missing_forward"] == ["BRK-B"]
          and "BRK-B" in r2["Forward P/E, the top 10"][1]
          and r2["Forward P/E, the top 10"][1].startswith("not stored")
          and r2["Forward P/E, the top 10"][3] == "20.9x",
          "a top-10 name without its forward P/E: the top 10's and the other 490's "
          "cells are not stored, naming BRK-B, with the Guide's 20.9x beside -- never "
          "a partial sum")


def group_l() -> None:
    head("L. GTM-4: THE BUCKETS AND THE CASH-FLOW BRIDGE")
    import json
    from unittest import mock
    from altdata import gtm_equities as ge
    from altdata.sources import edgar, edgar_xbrl as ex
    from daily_cascade import gtm_block
    frames = {}
    for k, v in json.loads((FIX / "xbrl_frames.json").read_text(encoding="utf-8")).items():
        if "|" in k:
            tag, year = k.split("|")
            frames[(tag, int(year))] = v
    rows = ex.rows_from_frames(frames, ex.bridge_config(), f"{C2}")
    db = store(holdings_rows() + [dict(r, source="fixture") for r in rows], "buckets")
    scans.ingest([SCAN], db_path=db)
    with observations.ObservationStore(db) as st:
        b = ge.bucket_reads(st, C2)
        br = ge.cash_flow_bridge(st, C2)
        gtm_block._ECACHE.clear()
        sub = gtm_block.mechanics_subsections(st, C2, "monthly")[1]
    hy = b["rows"][0]
    check(hy["id"] == "hyperscalers" and close(hy["weight"], 19.2)
          and close(hy["ytd"], 6.237425) and close(hy["ntm_pe"], 25.957639),
          f"the hyperscalers: 19.2% of the index, +6.2374% market-weighted year to "
          f"date, 25.9576x NTM P/E (hand; {hy['weight']}, {hy['ytd']}, {hy['ntm_pe']})")
    check(all(r["weight"] is None and "GICS" in r["reason"] for r in b["rows"][1:])
          and b["total_weight"] is None,
          "the four GICS buckets have no stored members: nothing computed, the reason "
          "given; the total is not computed either")
    t = {r[0]: r for r in sub["table"]["rows"]}
    check(t["Hyperscalers"][1] == "19.2%" and t["Hyperscalers"][4] == "ours"
          and t["Semiconductors"][1] == "18.6% (the Guide's)"
          and t["Semiconductors"][2] == "44% (the Guide's)"
          and t["Semiconductors"][4] == "the Guide's, slide 11"
          and t["The five together (each name once)"][1] == "53.2% (the Guide's)",
          "a bucket without stored members prints the Guide's figures, labelled "
          "(semis 18.6%, +44%), and so does the total (53.2%)")
    db2 = store(holdings_rows(drop=(("yf.forward_pe", "ORCL"),)), "buckets_missing")
    scans.ingest([SCAN], db_path=db2)
    with observations.ObservationStore(db2) as st:
        b2 = ge.bucket_reads(st, C2)
        gtm_block._ECACHE.clear()
        t2 = {r[0]: r for r in gtm_block.mechanics_subsections(st, C2, "weekly")[1]
              ["table"]["rows"]}
    check(b2["rows"][0]["ntm_pe"] is None and b2["rows"][0]["missing"]["ntm_pe"] == ["ORCL"]
          and t2["Hyperscalers"][3] == "22.2x (the Guide's)"
          and t2["Hyperscalers"][4] == "mixed: each cell labelled",
          "a member missing from the store (ORCL's multiple): the NTM P/E prints the "
          "Guide's 22.2x, labelled, never a five-name figure presented as the bucket")
    y = {r["year"]: r for r in br["rows"]}
    check(close(y[2023]["ocf"], 380e9, 1) and close(y[2023]["capex"], 155e9, 1)
          and close(y[2023]["fcf"], 225e9, 1) and y[2024]["capex"] is None
          and y[2024]["lack"]["capex"] == ["META"] and close(y[2024]["ocf"], 470e9, 1),
          "the bridge from the frames fixture: CY2023 380 - 155 = 225 bn (Microsoft's "
          "June and Oracle's May years in CY2023; Alphabet's second tag ignored); "
          "CY2024's capex lacks META")
    bt = {r[0]: r for r in sub["tables"][0]["rows"]}
    check(bt["2023"][1] == "$380bn" and bt["2023"][3] == "$225bn"
          and bt["2024"][2] == "not stored (META)" and bt["2024"][3] == "—"
          and bt["2026F (forecast)"][4] == "799" and bt["2025"][4] == "416",
          "the printed bridge: \"not stored (META)\" where a filer lacks a tag; the "
          "Guide's capex path beside it (416 in 2025, 799 forecast for 2026)")
    calls = []
    with mock.patch.object(edgar, "contact", lambda: None), \
            mock.patch.object(ex, "http_get_json",
                              lambda *a, **k: calls.append(a) or {}):
        r = ex.pull(db=None)
    check(r["status"] == "PENDING" and not calls and "not configured" in r["reason"],
          "with no SEC contact the XBRL reader is PENDING and fetches nothing")


def group_m() -> None:
    head("M. GTM-10: THE SECTOR ROWS")
    from altdata import gtm_equities as ge
    from daily_cascade import gtm_block
    rs = rows_of("sector_corr.csv")
    closes = [(r["day"], float(r["etf_close"])) for r in rs]
    rate = [(r["day"], float(r["dgs10"])) for r in rs]
    one = ge.rate_correlation(closes, rate, 5, 0.9)
    five = ge.rate_correlation(closes, rate, 10, 0.9)
    check(close(one["corr"], -0.896421) and one["n"] == 5 and one["reached"],
          f"the ETF's daily return against the 10-year's daily change in bp: -0.8964 "
          f"(hand; {one['corr']}, n={one['n']})")
    check(five["corr"] is None and not five["reached"] and five["n"] == 5,
          "a window the store does not cover is not reached (5 of 10)")
    db = store([obs("yfinance.mkt_xlk", d, v) for d, v in closes]
               + [obs("fred.yield_10y", d, v) for d, v in rate], "sectors")
    scans.ingest([SCAN], db_path=db)
    with observations.ObservationStore(db) as st:
        gtm_block._ECACHE.clear()
        col = gtm_block.sector_corr_column(st, C2, [["Technology (XLK)", "+1.0%", "—", "—"],
                                                   ["Growth vs value", "+0.5%", "—", "—"]])
        tab = gtm_block.sector_table(st, C2)
    check(col[0][-1] == "not reached (5 of 252)" and col[1][-1] == "—"
          and all(len(r) == 5 for r in col),
          "the Weekly's leadership table gains one column: the sector's one-year "
          "correlation (here not reached), \"—\" for a pair")
    tech = next(r for r in tab["rows"] if r[0] == "Technology (XLK)")
    check(len(tab["columns"]) == 6 and tech[2] == "0.0" and tech[3] == "21.5x (18.8x)"
          and tech[4] == "43.4% (12.3%)" and tech[5] == "52.3%"
          and tab["rows"][-1][0] == "The S&P 500 (the Guide)",
          "the Monthly's sector table: ours beside the Guide's slide-15 rows (Tech "
          "21.5x against 18.8x, NTM EPS 43.4% against 12.3%, 52.3% foreign sales)")


def group_n() -> None:
    head("N. GTM-15 MONTHLY: THE MTS CUSTOMS LINE")
    import json
    from altdata.sources import fiscaldata
    from daily_cascade import gtm_block
    recs = json.loads((FIX / "mts_customs.json").read_text(encoding="utf-8"))["data"]
    rows = fiscaldata.rows_from_mts(recs, C2)
    check(len(rows) == 9 and {r["registry_key"] for r in rows} == set(fiscaldata.MTS_KEYS.values())
          and all(r["observed_at"] != "2026-09-30" or r["value"] != 9e9 for r in rows),
          "the MTS reader keeps the Customs Duties line only: 3 months x gross, refunds, "
          "net; the excise line is skipped")
    db = store([dict(r, source="fixture") for r in rows]
               + [obs("fred.goods_imports", "2026-07-01", 240000.0),
                  obs("fred.goods_imports", "2026-08-01", 252000.0),
                  obs("fred.goods_imports", "2026-09-01", 250000.0)], "mts")
    with observations.ObservationStore(db) as st:
        m = gtm.tariff_monthly(st, CUT)
        gtm_block._CACHE.clear()
        sub = next(x for x in gtm_block.plumbing_subsections(st, CUT, "monthly")
                   if x["title"] == gtm_block.TARIFF_TITLE)
    check(m["state"] == "ok" and close(m["latest"], 10.8) and m["month"] == "2026-09"
          and close(m["rate_smooth"], 10.269542) and m["refunds"] == 20e9
          and m["n_full"] == 3 and m["pctile_full"] == 100.0,
          f"27.0bn gross over 250,000 mn of imports: 10.8% (hand); three months "
          f"10.2695%; the refunds 20bn beside it ({m.get('latest')}, {m.get('rate_smooth')})")
    check(sub["table"]["rows"][0][1] == "10.8%" and sub["table"]["rows"][1][1] == "10.3%"
          and sub["table"]["rows"][2][0].startswith("The cross-check")
          and any("refunds" in x for x in sub["lines"]),
          "the table opens on the month, then three months, with the quarterly FRED "
          "rate as the cross-check and the refunds line")


def group_o() -> None:
    head("O. GTM-12: THE FEDERAL ROWS")
    from daily_cascade import gtm_block
    db = store([obs("fred.fed_interest_payments", "2025-04-01", 1000.0),
                obs("fred.fed_interest_payments", "2026-04-01", 1100.0),
                obs("fred.fed_outlays", "2025-04-01", 6800.0),
                obs("fred.fed_outlays", "2026-04-01", 7000.0),
                obs("fred.fy_net_interest", "2025-01-01", 1_000_000.0),
                obs("fred.fy_net_outlays", "2025-01-01", 7_000_000.0),
                obs("fred.fy_deficit", "2025-01-01", -1_800_000.0),
                obs("fred.fy_deficit_gdp", "2025-01-01", -5.9)], "federal")
    scans.ingest([SCAN], db_path=db)
    with observations.ObservationStore(db) as st:
        f = gtm.federal(st, CUT)
        gtm_block._CACHE.clear()
        sub = next(x for x in gtm_block.plumbing_subsections(st, CUT, "monthly")
                   if x["title"] == gtm_block.FEDERAL_TITLE)
    r = {x["id"]: x for x in f["rows"]}
    check(close(r["interest_nipa"]["share"], 15.714286)
          and r["interest_nipa"]["pctile_full"] == 100.0 and r["interest_nipa"]["n_full"] == 2
          and close(r["net_interest_fy"]["share"], 14.285714)
          and r["deficit_fy"]["latest"] == 1_800_000.0
          and close(r["deficit_fy"]["share"], 25.714286)
          and close(r["deficit_gdp"]["latest"], 5.9),
          "interest 1,100 of 7,000 (15.7143%, the 100th of 2); net interest 14.2857% of "
          "net outlays; the deficit $1,800bn, 25.7143%; 5.9% of GDP (hand)")
    t = {x[0]: x for x in sub["table"]["rows"]}
    check(t["Deficit (budget, fiscal year) (FYFSD)"][1] == "$1,800bn"
          and t["Deficit (budget, fiscal year) (FYFSD)"][2] == "FY2025"
          and t["Defense consumption and gross investment (national accounts) (FDEFX)"][1]
          == "not stored"
          and any("99.4% (the Guide, §7, slide 27, as of 2026-09-30)" in x
                  and "120.2% (the Guide" in x for x in sub["lines"]),
          "the printed rows (the deficit $1,800bn, FY2025; an absent series \"not "
          "stored\") and the CBO path 99.4% to 120.2% as a sourced figure, slide 27")


def group_p() -> None:
    head("P. EVERY SOURCED FIGURE CARRIES ITS SLIDE AND AS-OF")
    cfg = gtm.config()
    text = SCAN.read_text(encoding="utf-8")
    items = {e["item"] for e in cfg["sourced"]}
    check(all(isinstance(e.get("slide"), int) and e["slide"] > 0 and e.get("section")
              for e in cfg["sourced"])
          and {"GTM-3", "GTM-4", "GTM-10", "GTM-12"} <= items,
          f"all {len(cfg['sourced'])} declared figures carry a slide and a section, "
          f"part 2's included")
    e4 = next(e for e in cfg["sourced"] if e["id"] == "gtm4.semiconductors.ytd")
    check(gtm.sourced_refusal({**e4, "slide": None}, text) == "no slide reference"
          and gtm.sourced_refusal(e4, text) is None,
          "a part-2 fixture figure without its slide is refused")
    db = str(TD / "slides.db")
    scans.ingest([SCAN], db_path=db)
    src = gtm.sourced(C2, db)
    check(gtm.cite(src["gtm12.debt_2036"])
          == "120.2% (the Guide, §7, slide 27, as of 2026-09-30)"
          and gtm.cite(src["gtm3.earn_share"])
          == "36.1% (the Guide, §7, slide 8, as of 2026-09-30)",
          "a stored figure prints with its slide and the scan's as-of")


def group_q() -> None:
    head("Q. THE QUEUE ENTRY IS A DRAFT AND GRANTS NOTHING")
    import yaml
    q = yaml.safe_load((REPO / "config" / "tb_intake_queue.yaml").read_text(encoding="utf-8"))
    e = {x["id"]: x for x in q["entries"]}
    check(all(x["status"] == "draft" and x["rights"] == "none" and x["position"] is None
              for x in q["entries"])
          and e["GTM-3"]["register"] == "SR-50" and e["GTM-3"]["ledger_needed"],
          "every queue entry is a draft with no right and no position (the order is "
          "the operator's, 25 Oct); GTM-3's names the ledger it would need")
    # The overlay's declared inputs, diffed against the ones the order left them at.
    pinned = {
        "docs/master-narrative.md": "| **Concentration & Complacency** | Valuation tops the composite misses (2000, 2022) | 3+ of: Fwd P/E ≥20x · CAPE ≥30 · ERP ≤1.5% · Top-10 ≥25% · VIX ≤18 |",
        "docs/translation-table.md": "| **Concentration & Complacency** | Valuation tops the composite under-weights (2000, 2022) | 3+ of 5: Fwd P/E ≥ 20x · CAPE ≥ 30 · ERP ≤ 1.5% · Top-10 ≥ 25% · VIX ≤ 18 |",
        "docs/chester-reports-architecture-v3.md": "| Concentration & Complacency | 2000/2022 valuation | FwdPE≥20 · CAPE≥30 · ERP≤1.5% · Top10≥25% · VIX≤18 |",
    }
    diffs = []
    for f, row in pinned.items():
        lines = [ln for ln in (REPO / f).read_text(encoding="utf-8").splitlines()
                 if "Concentration & Complacency" in ln and ln.startswith("| ")
                 and "≥" in ln]
        if len(lines) != 1 or not lines[0].startswith(row):
            diffs.append(f)
    import yaml as _y
    t1 = _y.safe_load((REPO / "config" / "st_r5_t1_rest.yaml").read_text(encoding="utf-8"))
    check(not diffs and t1["concentration"].get("overlay_built") is False,
          f"the overlay's five inputs are unchanged in every document that declares "
          f"them, and the overlay is not built ({diffs})")
    import re
    load = re.compile(r"""["']tb_intake_queue(\.yaml)?["']""")
    readers = [str(pth.relative_to(REPO)) for pth in REPO.rglob("*.py")
               if ".venv" not in pth.parts and pth.name != "validate_gtm.py"
               and load.search(pth.read_text(encoding="utf-8", errors="replace"))]
    ms = (REPO / "config" / "market_state.yaml").read_text(encoding="utf-8")
    check(not readers and "gtm" not in ms.lower() and "concentration_twin" not in ms,
          f"no code reads the queue file, and the market-state object reads nothing of "
          f"the GTM batch ({readers})")


def main() -> int:
    print(f"{LINE}\nThe J.P. Morgan Guide batch, parts 1 and 2\n{LINE}")
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g,
              group_h, group_i, group_j, group_k, group_l, group_m, group_n,
              group_o, group_p, group_q):
        try:
            g()
        except Exception as exc:                              # noqa: BLE001
            import traceback
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
