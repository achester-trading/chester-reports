"""
Validation gate for Batch 5 Tranche 1, part 1 (signal-triage round 4, part 2:
items 17, 21, 23, 24 and 26; docs/briefs/st-r4-tranche-1-notes.md). FIXTURES
ONLY: every store is the gate's own, in a temporary directory; no fetch (the HTTP
reader is poisoned), no model, no live store.

  A  ST-R4.21b  THE TERM PREMIUM PRINTS: ACM's level, its change, and both
     percentiles with their n and first date; a window the store does not fill
     says how many years it holds.
  B  ST-R4.26a  THE FISCAL-BARK FLAG fires at its thresholds and not below: a
     share of exactly 0.50 on a 30 bp rise fires, 0.49 does not, a 20 bp move
     has no share, a rally never fires; the divergence fires at 10 bp each way
     and not at 9.
  C  ST-R4.24a/b  THE STOCK-BOND FLAG: live above 0.20 and not at it; the
     two-year weekly window computed, and absent below 78 weeks; the
     conditioning moves the strength the right way -- breakeven-led strong,
     real-yield-led with inflation anchored weak, not anchored moderate, no
     attribution unconditioned; SR-9's 5.25% prior; the companions named.
  D  ST-R4.17a  NET LIQUIDITY: the 4- and 13-week changes, each split into its
     legs in dollars (the units trap: WALCL and WTREGEN millions, RRPONTSYD
     billions), the legs summing to the change, the leading leg named with its
     meaning; verify item 2 answered on a fixture September (TGA-led).
  E  ST-R4.21a  GREECE: the ECB writer stores GR beside DE, FR and IT; a
     response without GR still writes the three legs; GR alone is refused.
  F  ST-R4.23a  THE HELD CENSUS WRITER fetches and writes nothing while held,
     and writes into a temporary store when unheld; the workbook read by column
     name, a blank month skipped, a detailed type's pre-2002 zero skipped.
  G  ST-R4.23a  CONSTRUCTION, REAL: the data-center and ex-data-center lines'
     real year over year and level against 2019 by hand; the share of private
     nonresidential; held, the block says why.
  H  THE PRINT AND THE REGISTRY: each subsection's table and lines; the hooks in
     the Weekly and the Monthly; every new key registered with its units; the
     catalogue lines; neither module can fetch.

    python tools/validate_st_r4_t1.py
"""

from __future__ import annotations

import datetime as dt
import io
import math
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import gate_tmp  # noqa: E402
import yaml  # noqa: E402

from altdata import batch5, observations  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = 0
FAIL = 0
LINE = "=" * 78
CFG = batch5.config()


def check(c: bool, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


def store(rows: list[tuple]) -> str:
    """A temporary store of (key, day, value), each available 21:00 UTC on its day."""
    db = str(Path(gate_tmp.mkdtemp("st_r4_")) / "obs.db")
    with observations.ObservationStore(db) as st:
        if rows:
            st.write_many([{"registry_key": k, "instrument": None, "observed_at": d,
                            "available_at": d + "T21:00:00+00:00", "value": float(v),
                            "source": "fixture"} for k, d, v in rows])
    return db


def weekdays(start: str, end: str) -> list[str]:
    d, e, out = dt.date.fromisoformat(start), dt.date.fromisoformat(end), []
    while d <= e:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def ramp(key: str, days: list[str], a: float, b: float) -> list[tuple]:
    n = len(days) - 1
    return [(key, d, a + (b - a) * i / n) for i, d in enumerate(days)]


CUT = "2026-10-09T23:00:00+00:00"


def no_iso(sub: dict) -> bool:
    """validate_readability's rule: no ISO date outside a table."""
    import re
    txt = " ".join(list(sub.get("lines") or []) + [sub.get("table_note") or ""])
    return not re.search(r"\d{4}-\d{2}-\d{2}", txt)


# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. ST-R4.21b  THE TERM PREMIUM PRINTS, WITH ITS PERCENTILES' n")
    days = weekdays("2016-10-10", "2026-10-09")
    rows = [("acm.term_premium_10y", d, 0.2 + 0.0001 * i) for i, d in enumerate(days)]
    with observations.ObservationStore(store(rows)) as st:
        tp = batch5.term_premium(st, CUT)
        from daily_cascade import batch5_block as blk
        sub = blk.attribution_subsection(st, CUT)
    p5, p20 = tp["percentiles"][5], tp["percentiles"][20]
    check(tp["as_of"] == "2026-10-09" and p5["pct"] == 100.0 and p20["pct"] == 100.0,
          f"the latest print at the top of each window ({p5['pct']}, {p20['pct']})")
    check(p5["n"] == len([d for d in days if d > "2021-10-09"]) and not p5["short"]
          and p20["n"] == len(days) and p20["short"] and p20["window_years_real"] == 10.0,
          f"each percentile carries its n; the 20-year window holds 10 years and says "
          f"so (n={p5['n']}, {p20['n']}; {p20['window_years_real']} years)")
    row = sub["table"]["rows"][0]
    check(row[0] == "10-year term premium (ACM)" and "(n=" in row[3]
          and "10.0 years stored" in row[4] and row[-1] == "2026-10-09",
          f"printed where the attribution prints, n and real window in the cell ({row})")
    with observations.ObservationStore(store([])) as st:
        none = batch5.term_premium(st, CUT)
    check(none["absent"] and "no acm.term_premium_10y" in none["reason"],
          "absent with its reason when nothing is stored")


def _bark_store(fit_bp: float, tp_bp: float, path_bp: float) -> str:
    """Flat to 8 Apr, then a straight line over exactly the six months from
    9 Apr (six calendar months before 9 Oct) -- so the six-month move is the
    whole move."""
    pre, days = weekdays("2026-03-02", "2026-04-08"), weekdays("2026-04-09", "2026-10-09")
    rows = []
    for key, a, mv in (("acm.fitted_yield_10y", 4.30, fit_bp),
                       ("acm.term_premium_10y", 0.50, tp_bp),
                       ("acm.risk_neutral_yield_10y", 3.80, path_bp),
                       ("fred.yield_10y", 4.40, fit_bp)):
        rows += [(key, d, a) for d in pre] + ramp(key, days, a, a + mv / 100)
    return store(rows)


def group_b() -> None:
    head("B. ST-R4.26a  THE FISCAL-BARK FLAG, AT ITS THRESHOLDS")
    cases = [("a 100 bp rise, the term premium 60 of it", 100, 60, 40, True, 0.6),
             ("a 30 bp rise, the term premium exactly half", 30, 15, 15, True, 0.5),
             ("a 100 bp rise, the term premium 49 of it", 100, 49, 51, False, 0.49),
             ("a 20 bp rise: under 25 bp, no share", 20, 18, 2, False, None),
             ("a 100 bp rally, the term premium 70 of it", -100, -70, -30, False, 0.7)]
    for name, f, t, pth, fires, share in cases:
        with observations.ObservationStore(_bark_store(f, t, pth)) as st:
            fb = batch5.fiscal_bark(st, CUT)
        ok_share = (fb["tp_share"] is None if share is None
                    else abs(fb["tp_share"] - share) < 0.011)
        check(fb["fiscal_bark"] is fires and ok_share,
              f"{name}: flag {fb['fiscal_bark']}, share {fb['tp_share']} "
              f"(fitted {fb['fitted_bp']:+.0f} bp from {fb['from']})")
    for name, t, pth, fires in (("term premium +12, expected short rate -11", 12, -11, True),
                                ("term premium +9, expected short rate -11", 9, -11, False),
                                ("term premium +12, expected short rate -9", 12, -9, False)):
        with observations.ObservationStore(_bark_store(t + pth, t, pth)) as st:
            fb = batch5.fiscal_bark(st, CUT)
        check(fb["divergence"] is fires, f"divergence, {name}: {fb['divergence']}")
    with observations.ObservationStore(_bark_store(100, 60, 40)) as st:
        from daily_cascade import batch5_block as blk
        sub = blk.attribution_subsection(st, CUT)
    check(any(x.startswith("FISCAL-BARK FLAG: the term premium carried 0.60") and
              "A flag, not a state" in x for x in sub["lines"])
          and any("quoted 10-year (FRED DGS10) moved +100 bp" in x for x in sub["lines"]),
          "the flag prints with its thresholds, the quoted move beside it")
    check(no_iso(sub), "no ISO date outside its table")


def _sb_store(c60: float, real_share, be_move_bp: float, weeks: int = 110,
              ten: float = 5.30, tp_share=None) -> str:
    # SPY and TLT: weekly prices whose log returns move together (TLT = 0.6 x
    # SPY's, plus a fixed wobble), so the two-year correlation is positive.
    end = dt.date(2026, 10, 9)
    rows, s, b = [], 500.0, 90.0
    fridays = [end - dt.timedelta(weeks=k) for k in range(weeks)][::-1]
    for i, d in enumerate(fridays):
        r = 0.01 * math.sin(i * 1.3)
        s *= math.exp(r)
        b *= math.exp(0.6 * r + 0.002 * math.cos(i * 0.7))
        rows += [("yfinance.mkt_spy", d.isoformat(), s), ("yfinance.mkt_tlt", d.isoformat(), b)]
    rows.append(("calc.corr_spy_tlt_60d", "2026-10-09", c60))
    rows.append(("fred.yield_10y", "2026-10-09", ten))
    if real_share is not None:
        rows.append(("calc.attr_real_share_60d", "2026-10-09", real_share))
    if tp_share is not None:
        rows.append(("calc.attr_acm_tp_share_60d", "2026-10-09", tp_share))
    days = weekdays("2026-06-01", "2026-10-09")
    rows += ramp("fred.breakeven_10y", days, 2.30, 2.30 + be_move_bp / 100)
    return store(rows)


def group_c() -> None:
    head("C. ST-R4.24a/b  THE STOCK-BOND FLAG AND ITS CONDITIONING")
    with observations.ObservationStore(_sb_store(0.20, 0.3, 30)) as st:
        at = batch5.stock_bond(st, CUT)
    with observations.ObservationStore(_sb_store(0.21, 0.3, 30)) as st:
        above = batch5.stock_bond(st, CUT)
    check(not at["live"] and above["live"],
          f"live above 0.20 and not at it ({at['live']}, {above['live']})")
    two = above["two_year"]
    check(two["value"] is not None and two["value"] > 0.9 and two["n_weeks"] == 104
          and above["persistent"],
          f"the two-year window of weekly changes: {two['value']} over "
          f"{two['n_weeks']} weeks, positive: persistent")
    strengths = {}
    for name, rs, be, tps in (("breakeven-led", 0.3, 30, None),
                              ("real-yield-led, inflation anchored", 0.8, 5, None),
                              ("term-premium-led, inflation anchored", 0.8, 5, 0.7),
                              ("real-yield-led, inflation not anchored", 0.8, 30, None),
                              ("no attribution", None, 5, None)):
        with observations.ObservationStore(_sb_store(0.45, rs, be, tp_share=tps)) as st:
            strengths[name] = batch5.stock_bond(st, CUT)
    got = {k: v["strength"] for k, v in strengths.items()}
    check(got == {"breakeven-led": "strong",
                  "real-yield-led, inflation anchored": "weak",
                  "term-premium-led, inflation anchored": "weak",
                  "real-yield-led, inflation not anchored": "moderate",
                  "no attribution": "unconditioned"},
          f"the conditioning moves the strength the right way ({got})")
    check("term-premium-led" in strengths["term-premium-led, inflation anchored"]["why"],
          "and says which leg led")
    check(above["above_prior"] and above["ten_year"] == 5.30,
          "the 10-year at 5.30% is above SR-9's 5.25% prior")
    with observations.ObservationStore(_sb_store(0.45, 0.3, 30, weeks=50)) as st:
        short = batch5.stock_bond(st, CUT)
    check(short["two_year"].get("absent", "").startswith("49 weeks")
          and not short["persistent"],
          f"below 78 weeks the two-year window is absent ({short['two_year'].get('absent')})")
    from daily_cascade import batch5_block as blk
    with observations.ObservationStore(_sb_store(0.45, 0.3, 30)) as st:
        sub = blk.mechanics_subsection(st, CUT)
    lines = " ".join(sub["lines"])
    check(sub["table"]["rows"][1][1].endswith("(n=104 weeks)")
          and "STOCK-BOND FLAG LIVE (strong)" in lines
          and "quadrant sub-state (item 25" in lines and "r−g (item 29" in lines,
          "printed in Mechanics with its strength and its two companions named")
    check(no_iso(sub) and "(9 Oct)" in lines, "its dates print as '9 Oct', never ISO")


def _nl_store(weeks: int = 14) -> str:
    """Wednesdays. Fed assets (millions) +10bn over the span, TGA (millions)
    falls 200bn in the last four weeks, RRP (billions) falls 5bn."""
    end = dt.date(2026, 10, 7)
    rows = []
    for k in range(weeks):
        d = (end - dt.timedelta(weeks=weeks - 1 - k)).isoformat()
        fed = 6_600_000 + 10_000 * k / (weeks - 1)          # millions
        tga = 850_000 - (200_000 * (k - (weeks - 5)) / 4 if k > weeks - 5 else 0)
        rrp = 20.0 - 5.0 * k / (weeks - 1)                  # billions
        net = fed * 1e6 - rrp * 1e9 - tga * 1e6
        rows += [("fred.fed_balance", d, fed), ("fred.tga", d, tga),
                 ("fred.rrp", d, rrp), ("calc.net_liquidity", d, net)]
    return store(rows)


def group_d() -> None:
    head("D. ST-R4.17a  NET LIQUIDITY, ATTRIBUTED")
    with observations.ObservationStore(_nl_store()) as st:
        nl = batch5.net_liquidity(st, CUT)
        ver = batch5.verify(st, CUT)
        from daily_cascade import batch5_block as blk
        sub = blk.net_liquidity_subsection(st, CUT)
    w4, w13 = nl["windows"]["4"], nl["windows"]["13"]
    c = w13["contributions"]
    # Over 13 weeks: Fed assets +10bn; the TGA fell 200bn (+200bn); RRP fell 5bn (+5bn).
    check(abs(c["fed_assets"] - 10e9) < 1e3 and abs(c["tga"] - 200e9) < 1e3
          and abs(c["rrp"] - 5e9) < 1e3 and abs(w13["residual"]) < 1e3
          and abs(w13["change"] - 215e9) < 1e3,
          f"13 weeks: +$215bn = Fed assets +$10bn, the TGA's fall +$200bn, the RRP's "
          f"+$5bn; the legs sum to the change (residual {w13['residual']:.0f})")
    check(w4["led_by"] == "tga" and "transient" in w4["meaning"]
          and w4["from"] == "2026-09-09",
          f"4 weeks: led by the TGA, transient ({w4['from']} to {w4['to']})")
    sep = ver["item_2_september"]
    check(sep and max(sep["legs"], key=lambda k: abs(sep["legs"][k])) == "tga",
          f"verify item 2 on the fixture: the September upturn was the TGA "
          f"({ {k: round(v / 1e9) for k, v in sep['legs'].items()} } bn)")
    check(sub["table"]["rows"][1][1] == "+215bn" and sub["table"]["rows"][1][3] == "+200bn"
          and any("calibration ledger" in x for x in sub["lines"]),
          "printed with each leg in dollars, report only")
    check(no_iso(sub) and any("as of 7 Oct" in x for x in sub["lines"]),
          "its dates print as '7 Oct', never ISO")
    with observations.ObservationStore(_nl_store(weeks=3)) as st:
        short = batch5.net_liquidity(st, CUT)
    check(short["windows"]["4"].get("absent") and short["windows"]["13"].get("absent"),
          "a window the series does not reach is absent with its reason")


def ecb_csv(pts: dict) -> str:
    out = ["KEY,REF_AREA,TIME_PERIOD,OBS_VALUE"]
    for c, rows in pts.items():
        for d, v in rows:
            out.append(f"IRS.M.{c}.L.L40.CI.0000.EUR.N.Z,{c},{d},{v}")
    return "\n".join(out) + "\n"


def group_e() -> None:
    head("E. ST-R4.21a  GREECE IN THE ECB WRITER")
    from altdata.sources import ecb_irs
    base = {"DE": [("2026-08", "2.70")], "FR": [("2026-08", "3.42")],
            "IT": [("2026-08", "3.61")]}
    rows = ecb_irs.rows_from_csv(ecb_csv({**base, "GR": [("2026-08", "3.87")]}),
                                 "2026-09-10T08:00:00+00:00", "observed")
    got = {r["registry_key"]: r["value"] for r in rows}
    check(got.get("ecb.irs_10y_gr") == 3.87 and len(rows) == 4,
          "Greece stored beside the three legs")
    three = ecb_irs.rows_from_csv(ecb_csv(base), "x", "observed")
    check(len(three) == 3, "a response without Greece still writes SR-30's three legs")
    try:
        ecb_irs.rows_from_csv(ecb_csv({"GR": [("2026-08", "3.87")]}), "x", "observed")
        refused = False
    except ValueError:
        refused = True
    check(refused, "Greece alone is refused: the three legs are required")
    check("GR" in ecb_irs.URL, "and the request asks for it")


def _xlsx(header: list, rows: list[list]) -> bytes:
    """A minimal workbook: inline-string header, numeric cells, blanks omitted."""
    def col(i):
        s = ""
        i += 1
        while i:
            i, r = divmod(i - 1, 26)
            s = chr(65 + r) + s
        return s

    def cell(r, i, v):
        ref = f"{col(i)}{r}"
        if v is None:
            return ""
        if isinstance(v, str):
            return f'<c r="{ref}" t="inlineStr"><is><t>{v}</t></is></c>'
        return f'<c r="{ref}"><v>{v}</v></c>'
    body = [f'<row r="1">{cell(1, 0, "Title")}</row>',
            f'<row r="4">' + "".join(cell(4, i, h) for i, h in enumerate(header)) + "</row>"]
    for k, r in enumerate(rows):
        body.append(f'<row r="{5 + k}">' + "".join(cell(5 + k, i, v) for i, v in enumerate(r))
                    + "</row>")
    sheet = ('<?xml version="1.0"?><worksheet xmlns="http://schemas.openxmlformats.org/'
             'spreadsheetml/2006/main"><sheetData>' + "".join(body)
             + "</sheetData></worksheet>")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("xl/worksheets/sheet1.xml", sheet)
    return buf.getvalue()


PRIV = _xlsx(["Date", "Total\n_x000D_Private Construction1", "Nonresidential", "Office",
              "Data center"],
             [["Aug-26p", 1655280, 773010, 134119, 84950],
              ["Aug-25", 1600000, 700000, 120000, 50000],
              ["Dec-13", 900000, 400000, 50000, None]])
TOT = _xlsx(["Date", "Total\n_x000D_Construction1", "Total\n_x000D_Power"],
            [["Aug-26p", 2203129, 185973], ["Aug-25", 2150000, 171000],
             ["Dec-01", 900000, 0]])


def group_f(td: str) -> None:
    head("F. ST-R4.23a  THE HELD CENSUS WRITER")
    from altdata.sources import census_vip as cv
    calls = []

    def poisoned(url, **kw):
        calls.append(url)
        raise AssertionError("a held writer fetched")

    def served(url, **kw):
        calls.append(url)
        return (PRIV if "privsatime" in url else TOT), {"last-modified":
                                                        "Thu, 01 Oct 2026 14:04:30 GMT"}
    saved = cv.http_get_response
    db = observations.ObservationStore(str(Path(td) / "census.db"))
    try:
        cv.http_get_response = poisoned
        r = cv.pull(db=db)
        n0 = db.conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0] \
            if db.conn.execute("SELECT 1 FROM sqlite_master WHERE name='observations'"
                               ).fetchone() else 0
        check(cv.HELD_FOR_D1C and r["status"] == "HELD" and r["written"] == 0
              and not calls and n0 == 0 and "D1c" in r["reason"],
              f"held: it fetches nothing, writes nothing, and says why ({r['reason']})")
        cv.HELD_FOR_D1C = False
        cv.http_get_response = served
        r2 = cv.pull(db=db)
        got = {(k, str(x["observed_at"])[:10]): x["value_num"]
               for k in cv.KEYS for x in db.as_of(k, "2026-10-16T00:00:00+00:00")}
        check(r2.get("status") in ("OK", "ok") or r2.get("written", 0) > 0,
              f"unheld, in a temporary store, it writes ({r2.get('status')}, "
              f"{r2.get('written')})")
        check(got.get(("census.vip_data_center", "2026-08-01")) == 84950.0
              and ("census.vip_data_center", "2013-12-01") not in got
              and got.get(("census.vip_total", "2026-08-01")) == 2203129.0
              and got.get(("census.vip_power", "2026-08-01")) == 185973.0
              and ("census.vip_power", "2001-12-01") not in got,
              "read by column name; a blank data-center month and a pre-2002 detailed-"
              "type zero are skipped, never stored as zero")
    finally:
        cv.HELD_FOR_D1C = True
        cv.http_get_response = saved
        db.close()
    src = (REPO / "altdata" / "feeds.py").read_text(encoding="utf-8")
    check("census_vip" not in src, "the held writer is on no feeds roster")


def group_g() -> None:
    head("G. ST-R4.23a  CONSTRUCTION SPENDING, REAL")
    rows = []
    for m in range(1, 13):
        d = f"2019-{m:02d}-01"
        rows += [("census.vip_data_center", d, 10000), ("census.vip_total", d, 1300000),
                 ("fred.ppi_construction", d, 120.0)]
    rows += [("census.vip_data_center", "2025-08-01", 50000),
             ("census.vip_data_center", "2026-08-01", 84950),
             ("census.vip_total", "2025-08-01", 2150000),
             ("census.vip_total", "2026-08-01", 2203129),
             ("census.vip_private_nonresidential", "2026-08-01", 773010),
             ("fred.ppi_construction", "2025-08-01", 180.0),
             ("fred.ppi_construction", "2026-08-01", 188.186)]
    with observations.ObservationStore(store(rows)) as st:
        con = batch5.construction(st, CUT)
        from daily_cascade import batch5_block as blk
        sub = blk.slow_subsection(st, CUT)
    dc, ex = con["data_center"], con["ex_data_center"]
    # Real YoY: (84950/188.186) / (50000/180) - 1 = 451.41 / 277.78 - 1 = +62.5%.
    # Nominal: 84950/50000 - 1 = +69.9%. Against 2019: 451.41 / (10000/120) - 1 = +441.7%.
    check(dc["real_yoy_pct"] == 62.5 and dc["nominal_yoy_pct"] == 69.9
          and dc["vs_base_pct"] == 441.7 and dc["base_months"] == 12,
          f"data centers: real +62.5%, nominal +69.9%, +441.7% against 2019 ({dc})")
    # Ex data centers: (2118179/188.186) / (2100000/180) - 1 = 11255.8 / 11666.7 - 1 = -3.5%.
    check(ex["real_yoy_pct"] == -3.5 and ex["nominal_yoy_pct"] == 0.9,
          f"ex data centers: real -3.5%, nominal +0.9% ({ex['real_yoy_pct']}, "
          f"{ex['nominal_yoy_pct']})")
    check(dc["share_of_private_nonres_pct"] == 11.0,
          "data centers 11.0% of private nonresidential (84,950 / 773,010)")
    check([r[0] for r in sub["table"]["rows"]] == ["Data centers",
                                                   "Total construction ex data centers"]
          and any("No rights until the Disruptive Themes refresh" in x for x in sub["lines"]),
          "printed under Factor I in the slow layers, with no rights")
    check(no_iso(sub), "no ISO date outside its table")
    with observations.ObservationStore(store([])) as st:
        held = blk.slow_subsection(st, CUT)
    check("held until D1c" in held["lines"][0],
          f"held, the block says why ({held['lines'][0][:80]}...)")


def group_h() -> None:
    head("H. THE HOOKS, THE REGISTRY, NO FETCH")
    ws = (REPO / "daily_cascade" / "weekly_stack.py").read_text(encoding="utf-8")
    ms = (REPO / "monthly_macro" / "stack.py").read_text(encoding="utf-8")
    check("batch5_block.plumbing_subsections(st, now, then, cadence)" in ws
          and "batch5_block.mechanics_subsection(st, cutoff)" in ws,
          "the Weekly: the attribution and net liquidity in Plumbing, 24 in Mechanics")
    check('batch5_block.plumbing_subsections(st, now, then, "monthly")' in ms
          and "batch5_block.mechanics_subsection(st, now)" in ms
          and "batch5_block.slow_subsection(st, now)" in ms,
          "the Monthly: Plumbing, Mechanics, and Factor I in the slow layers")
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    met = reg["metrics"]
    want = {"ecb.irs_10y_gr": "percent_rate", "census.vip_data_center": "usd",
            "census.vip_private_nonresidential": "usd", "census.vip_total": "usd",
            "census.vip_power": "usd"}
    check(all(met.get(k, {}).get("units") == u for k, u in want.items()),
          "every new stored key registered with its units")
    from altdata import config as acfg
    pp = {s.key: s for s in acfg.FRED_SIGNAL_SERIES}.get("ppi_construction")
    check(pp is not None and pp.fred_id == "PPIDCS" and pp.units == "idx"
          and pp in acfg.FRED_PULL_SERIES,
          "PPIDCS in the FRED signal list (index), so the pull walks it")
    cat = (REPO / "config" / "catalogue_commands.yaml").read_text(encoding="utf-8")
    check("altdata.batch5:" in cat and "altdata.sources.census_vip:" in cat,
          "the catalogue names the two new commands")
    src = ((REPO / "altdata" / "batch5.py").read_text(encoding="utf-8")
           + (REPO / "daily_cascade" / "batch5_block.py").read_text(encoding="utf-8"))
    check("http" not in src.replace("https://", "") and "import_yfinance" not in src,
          "neither the computation nor the print can fetch")


def main() -> int:
    td = gate_tmp.mkdtemp("st_r4_t1_")
    group_a()
    group_b()
    group_c()
    group_d()
    group_e()
    group_f(td)
    group_g()
    group_h()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
