"""
THE J.P. MORGAN GUIDE BATCH, PART 1 (GTM-1, 7, 8, 9, 13, 15, 21), on fixtures.

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
     mechanical continuation; the drafts are present and marked as drafts.
  I  PLACEMENT AND THE BUDGETS. The Weekly's Plumbing carries GTM-13 only, the
     Monthly's three, Slow layers four; every sub-section is tables and lines
     (no word in the budget, no chart); the Weekly's tables are six columns at
     most.
  J  NOTHING LIVE. No network, model or order import; no read of a default
     store path a caller did not name; the five FRED series registered with
     family and long_window.

    python tools/validate_gtm.py
"""

from __future__ import annotations

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
N_SOURCED = 51


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
    check(agg["duration"] is None and agg["scenario"] == {"down": None, "up": None}
          and "no duration" in agg["duration_source"],
          "AGG has no duration in the reference: no shift return, and it says why")
    check(all(by[s]["state"] == gtm.NO_PROXY for s in ("TIPS", "Municipals", "MBS")),
          "TIPS, munis and MBS have no proxy in the store and print \"no proxy\"")


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
    check(len(subs) == 7 and cells and all(isinstance(c, str) and c.strip()
                                           and c.strip() not in ("0", "0.0", "0%")
                                           for c in cells),
          f"on an empty store all seven tables print a word in every cell "
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
          and reg.count("*Draft (rule 31") >= 2,
          "the five built here have entries; the SR-5 and SR-9 amendments are "
          "committed as drafts under rule 31")
    nar = (REPO / "config" / "narratives.yaml").read_text(encoding="utf-8")
    check("disagreements:" in nar and "gtm8_sentiment_trough_at_high" in nar
          and "status: draft" in nar,
          "the GTM-8 disagreement entry is in the narrative register's config as a "
          "draft, read by no code until accepted")
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
                                           gtm_block.DSR_TITLE]
          and [s["title"] for s in sl] == [gtm_block.INFLECTION_TITLE,
                                           gtm_block.SB_TITLE, gtm_block.SENT_TITLE,
                                           gtm_block.ATH_TITLE],
          "the Weekly's Plumbing carries GTM-13; the Monthly's adds GTM-15 and "
          "GTM-21; Slow layers GTM-1, 7, 8 and 9")
    allsub = wk + mo + sl
    check(all(s.get("paragraph_wanted") is False and not s.get("paragraphs")
              and not s.get("charts") and stack.section_words(s) == 0 for s in allsub),
          "every sub-section is tables and lines: no paragraph asked, no chart, "
          "zero words in the budget")
    check(all(len(t["columns"]) <= 6 for s in wk
              for t in [s["table"], *(s.get("tables") or [])]),
          "the Weekly's tables keep six columns at most (the mobile rule)")
    src = (REPO / "monthly_macro" / "stack.py").read_text(encoding="utf-8")
    wsrc = (REPO / "daily_cascade" / "weekly_stack.py").read_text(encoding="utf-8")
    check("gtm_block.slow_subsections(st, now, db_path)" in src
          and "gtm_block.base_rate_rows(st, now, db_path)" in src
          and 'gtm_block.plumbing_subsections(st, now, "monthly")' in src
          and 'gtm_block.plumbing_subsections(st, now, "weekly")' in wsrc,
          "the Monthly and the Weekly call the block where the order places it")


# ---------------------------------------------------------------------------
def group_j() -> None:
    head("J. NOTHING LIVE; THE SERIES REGISTERED")
    banned = {"requests", "urllib", "httpx", "anthropic", "subprocess", "socket",
              "altdata.model_meter", "register", "ibkr"}
    hits = []
    for f in ("altdata/gtm.py", "daily_cascade/gtm_block.py"):
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
    check(not called and b["sourced"] == {},
          "with no store and no path named, the sourced figures are not read from a "
          "default path (no live store)")
    from altdata import derived, config as acfg
    keys = ["fred.customs_duties", "fred.goods_imports", "fred.dsr_household",
            "fred.dsr_consumer", "fred.dsr_mortgage"]
    specs = {f"fred.{s.key}": s for s in acfg.FRED_SIGNAL_SERIES}
    reg = __import__("yaml").safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    check(all(k in specs for k in keys)
          and [specs[k].fred_id for k in keys] == ["B235RC1Q027SBEA", "BOPGIMP", "TDSP",
                                                   "CDSP", "MDSP"]
          and all(reg["families"].get(k) and reg["long_windows"].get(k) == "full"
                  for k in keys)
          and all(derived.registry_entry(k) for k in keys),
          "the five FRED series are pulled, registered, and carry family and "
          "long_window (full)")
    cat = (REPO / "config" / "catalogue_commands.yaml").read_text(encoding="utf-8")
    check("altdata.gtm:" in cat, "the catalogue lists python -m altdata.gtm")


def main() -> int:
    print(f"{LINE}\nThe J.P. Morgan Guide batch, part 1\n{LINE}")
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g,
              group_h, group_i, group_j):
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
