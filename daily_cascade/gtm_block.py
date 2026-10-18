"""
Where the GTM batch's part 1 prints (J.P. Morgan Guide to the Markets, 17 Oct 2026).

    plumbing_subsections(st, now, cadence, db_path)
        Plumbing & rates: "Fixed income under a 100 bp shift" (GTM-13) at the
        Weekly and the Monthly; at the Monthly also "Effective tariff rate"
        (GTM-15, the inflation modifier) and "Household debt service" (GTM-21,
        SR-5's modifier)
    slow_subsections(st, now, db_path)
        the Monthly's Slow layers: "Inflection points" (GTM-1, the Top & Bottom
        standing exhibit), "Stock-bond correlation regime" (GTM-7, SR-9),
        "Sentiment turning points" (GTM-8) and "All-time highs" (GTM-9)
    base_rate_rows(st, now, db_path)
        the rows GTM-1, 8 and 9 add to the Monthly's base-rates table, each with n

PART 2 (gtm-core-2, 17 Oct 2026):

    mechanics_subsections(st, now, cadence, db_path)
        Mechanics, beside item 31's concentration sub-section: "The concentration
        twin" (GTM-3, report-only; its intake-queue entry is a draft) and "The AI
        buckets" (GTM-4) at the Weekly and the Monthly; at the Monthly the
        bucket sub-section also carries the hyperscaler cash-flow bridge -- the
        Factor I exhibit after the SR-37 panel
    sector_corr_column(st, now, rows, db_path)
        GTM-10's one-year correlation to the 10-year, as a column of the Weekly's
        sector table (the leadership table)
    sector_table(st, now, db_path)
        GTM-10's full rows for the Monthly's sector sub-section
    plumbing_subsections(..., "monthly") also carries "Federal finances" (GTM-12,
        the Factor IV rows) and the monthly effective tariff rate (GTM-15)

The reads are altdata/gtm.py's; this module lays them out. Every sub-section is
a table and lines, and asks no paragraph (`paragraph_wanted: False`), so none
adds a word to a budget or a chart to a cap. A fault never takes a section down.
Nothing here grants a right: each row is a base-rate row or a modifier, read by
a human.
"""

from __future__ import annotations

import logging
from typing import Optional

from altdata import gtm, gtm_equities

log = logging.getLogger(__name__)

FI_TITLE = "Fixed income under a 100 bp shift"
TARIFF_TITLE = "Effective tariff rate"
DSR_TITLE = "Household debt service (SR-5's modifier)"
INFLECTION_TITLE = "Inflection points (the Top & Bottom standing exhibit)"
SB_TITLE = "Stock-bond correlation regime"
SENT_TITLE = "Sentiment turning points"
ATH_TITLE = "All-time highs"
TWIN_TITLE = "The concentration twin (report-only)"
BUCKETS_TITLE = "The AI buckets (Factor I)"
FEDERAL_TITLE = "Federal finances (Factor IV)"
SECTOR_CORR_COLUMN = "Correlation to the 10-year, 1 year"

# Six columns at most (the mobile rule): the scenario table and the correlation
# table are two.
FI_COLUMNS = ["Sector", "Yield", "Year to date", "Duration", "-100 bp", "+100 bp"]
FI_CORR_COLUMNS = ["Sector", "Proxy", "Correlation to the 10-year",
                   "Correlation to the S&P 500", "The Guide, YTD to 30 Sep"]
INFLECTION_COLUMNS = ["Date", "S&P 500", "Forward P/E", "Dividend yield", "10-year",
                      "Source"]
SB_COLUMNS = ["Era", "Average 24-month correlation", "Average inflation", "Window (n)",
              "The Guide"]
SENT_COLUMNS = ["Turning point", "n", "Mean next 12 months", "Median",
                "The Guide (n)"]
ATH_COLUMNS = ["Measure", "Ours, 1988 to 2025", "The Guide, 1988 to 2025",
               "This year"]
TARIFF_COLUMNS = ["Measure", "Latest", "Period", "5-year percentile (n)",
                  "Full-history percentile (n)"]
TWIN_COLUMNS = ["Measure", "Ours", "As of", "The Guide (slide 8)"]
TWIN_AVG_COLUMNS = ["Forward P/E", "Ours: % of own average", "Own average (window, n)",
                    "The Guide: % of its average", "The Guide's average (since 1996)"]
BUCKET_COLUMNS = ["Bucket", "Weight in the S&P 500", "Year to date", "NTM P/E",
                  "Source"]
BRIDGE_COLUMNS = ["Year", "Operating cash flow", "Capex", "Cash flow less capex",
                  "The Guide's capex (slide 22)", "Filers"]
SECTOR_COLUMNS = ["Sector", "Correlation to the 10-year: 1 year / 5 years (ours)",
                  "The Guide's correlation (2-year monthly)",
                  "Forward P/E (20-year average)",
                  "NTM EPS growth (20-year median)", "Foreign share of sales"]
FEDERAL_COLUMNS = ["Series", "Latest", "Period", "Share", "10-year percentile (n)",
                   "Full-history percentile (n)"]

DSR_COLUMNS = ["Series", "Latest", "Quarter", "5-year percentile (n)",
               "Full-history percentile (n)"]

_CACHE: dict = {}
_ECACHE: dict = {}


def reads(st, now: str, db_path: Optional[str] = None) -> dict:
    k = (id(st), now, db_path)
    if k not in _CACHE:
        _CACHE.clear()
        _CACHE[k] = gtm.build(st, now, db_path)
    return _CACHE[k]


def equity_reads(st, now: str, db_path: Optional[str] = None) -> dict:
    k = (id(st), now, db_path)
    if k not in _ECACHE:
        _ECACHE.clear()
        _ECACHE[k] = gtm_equities.build(st, now, db_path)
    return _ECACHE[k]


def _safe(fn, what: str, default):
    try:
        return fn()
    except Exception:                                           # noqa: BLE001
        log.warning("%s faulted", what, exc_info=True)
        return default


def _pct(v, nd: int = 1, sign: bool = False) -> str:
    if v is None:
        return gtm.NOT_STORED
    return f"{v:+.{nd}f}%" if sign else f"{v:.{nd}f}%"


def _c(v) -> str:
    return gtm.NOT_STORED if v is None else f"{v:+.2f}"


def _ord(p) -> str:
    from altdata.numeral_audit import ordinal  # noqa: PLC0415
    return "—" if p is None else ordinal(p)


def _pr(p, n) -> str:
    return "—" if p is None else f"{_ord(p)} ({n})"


def _src(s: dict, i: str) -> Optional[dict]:
    return s.get(i)


# ---------------------------------------------------------------------------
# Plumbing & rates
# ---------------------------------------------------------------------------
def fi_subsection(b: dict) -> dict:
    fi = b["fixed_income"]
    rows, crow, absent = [], [], []
    for r in fi["rows"]:
        y = r.get("yield")
        ycell = f"{y['value']:.2f}% ({y['label']}, {y['day']})" if y else gtm.NOT_STORED
        if r["state"] == gtm.NO_PROXY:
            rows.append([r["sector"], ycell, gtm.NO_PROXY, gtm.NO_PROXY, gtm.NO_PROXY,
                         gtm.NO_PROXY])
            crow.append([r["sector"], gtm.NO_PROXY, gtm.NO_PROXY, gtm.NO_PROXY,
                         r.get("guide_ytd") or gtm.NOT_STORED])
            continue
        d = r.get("duration")
        dcell = f"{d:.1f} years" if d is not None else "no duration in the reference"
        sc = r["scenario"]
        rows.append([f"{r['sector']} ({r['proxy']})", ycell,
                     _pct(r.get("ytd"), 1, True), dcell,
                     _pct(sc["down"], 1, True) if d is not None else "—",
                     _pct(sc["up"], 1, True) if d is not None else "—"])
        crow.append([r["sector"], r["proxy"], _c(r.get("corr_rate")),
                     _c(r.get("corr_equity")), r.get("guide_ytd") or gtm.NOT_STORED])
        if d is None:
            absent.append(f"{r['sector']} ({r['proxy']}): no duration in "
                          f"config/instrument_reference.yaml")
    note = (f"Year to date: the proxy's total return (close and dividend) from the "
            f"last close of {int(fi['day'][:4]) - 1}. Duration: "
            f"config/instrument_reference.yaml (approximate issuer figures). The "
            f"shift columns are the price return alone, minus duration times the "
            f"change; the reference carries no convexity, so none is applied. "
            f"Correlations: daily total returns over the last {fi['window_sessions']} "
            f"sessions, against the 10-year's change in basis points and against "
            f"SPY. The Guide's column is its own figure, as of 30 Sep, never "
            f"recomputed. A modifier for Book A's rule table, read by a human; "
            f"nothing automated (GTM-13, SR-57).")
    return {"title": FI_TITLE, "table": {"columns": FI_COLUMNS, "rows": rows},
            "tables": [{"columns": FI_CORR_COLUMNS, "rows": crow}],
            "lines": [], "paragraph_wanted": False, "not_tracked": absent,
            "table_note": note, "data": {"fixed_income": fi}}


def tariff_subsection(b: dict) -> dict:
    t, s = b["tariff"], b["sourced"]
    m = b.get("tariff_monthly") or {"state": "absent", "absent_reason": "not read"}
    rows = []
    if m["state"] == "ok":
        rows.append(["Customs duties over goods imports, the month (ours, MTS gross)",
                     f"{m['latest']:.1f}%", m["month"],
                     _pr(m["pctile_5y"], m["n_5y"]),
                     _pr(m["pctile_full"], f"{m['n_full']}, since {m['since'][:4]}")])
        rows.append([f"The same, {m['smooth_months']} months to {m['month']}",
                     _pct(m.get("rate_smooth")), m["month"], "—", "—"])
    else:
        rows.append(["Customs duties over goods imports, the month (ours, MTS gross)",
                     gtm.NOT_STORED, "—", "—", "—"])
    if t["state"] == "ok":
        q = t["day"]
        rows.append(["The cross-check: the quarter (ours, FRED)", f"{t['latest']:.1f}%",
                     f"{q[:4]} Q{(int(q[5:7]) - 1) // 3 + 1}",
                     _pr(t["pctile_5y"], t["n_5y"]),
                     _pr(t["pctile_full"], f"{t['n_full']}, since {t['since'][:4]}")])
    else:
        rows.append(["The cross-check: the quarter (ours, FRED)", gtm.NOT_STORED,
                     "—", "—", "—"])
    for i in ("gtm15.effective", "gtm15.statutory_peak", "gtm15.ieepa"):
        r = _src(s, i)
        lab = r["label"] if r else next(e["label"] for e in gtm.config()["sourced"]
                                        if e["id"] == i)
        rows.append([lab, gtm.cite(r), "—", "—", "—"])
    lines = []
    if m["state"] == "ok" and m.get("refunds") is not None:
        lines.append(f"Customs refunds in {m['month']}: ${m['refunds'] / 1e9:,.1f}bn "
                     f"(MTS); the rate reads the duties collected, before refunds.")
    note = ("Ours, monthly (ruling 3 of 17 Oct 2026): the Monthly Treasury "
            "Statement's customs duties collected in the month (Table 4, gross of "
            "refunds, dollars, not seasonally adjusted) over the month's goods "
            "imports (BOPGIMP, seasonally adjusted, millions), and the same over "
            "three months. The cross-check: FRED's quarterly customs receipts "
            "(B235RC1Q027SBEA, billions at an annual rate) over four times the "
            "quarter's imports. Neither is the Census imports-for-consumption basis "
            "the Guide divides by, so ours and the Guide's differ by construction. "
            "An inflation modifier, read by a human (GTM-15, SR-59).")
    nt = []
    if m["state"] != "ok":
        nt.append(f"the monthly effective tariff rate: {m['absent_reason']}")
    if t["state"] != "ok":
        nt.append(f"the quarterly cross-check: {t['absent_reason']}")
    return {"title": TARIFF_TITLE, "table": {"columns": TARIFF_COLUMNS, "rows": rows},
            "lines": lines, "paragraph_wanted": False, "not_tracked": nt,
            "table_note": note, "data": {"tariff": t, "tariff_monthly": m}}


def dsr_subsection(b: dict) -> dict:
    d, s = b["dsr"], b["sourced"]
    rows = []
    for r in d["rows"]:
        if r.get("latest") is None:
            rows.append([r["label"], gtm.NOT_STORED, "—", "—", "—"])
            continue
        q = r["day"]
        rows.append([r["label"], f"{r['latest']:.2f}%",
                     f"{q[:4]} Q{(int(q[5:7]) - 1) // 3 + 1}",
                     _pr(r["pctile_5y"], r["n_5y"]),
                     _pr(r["pctile_full"], f"{r['n_full']}, since {r['since'][:4]}")])
    flows = []
    for i in ("gtm21.dsr", "gtm21.dsr_4q07", "gtm21.flow_cards", "gtm21.flow_auto",
              "gtm21.flow_student", "gtm21.flow_mortgage"):
        r = _src(s, i)
        if r:
            flows.append(f"{r['label']}: {gtm.cite(r)}.")
    note = ("FRED's household debt-service ratio (TDSP) and its consumer and "
            "mortgage splits (CDSP, MDSP), quarterly, with the five-year and the "
            "full-history percentile. The delinquency flows are the Guide's, "
            "labelled; the Guide's slide 26 dates them 2Q26, and its 11.1% DSR is a "
            "3Q26 estimate of its own. A modifier on SR-5, "
            "the consumer-credit impulse, whose own row is not yet built.")
    return {"title": DSR_TITLE, "table": {"columns": DSR_COLUMNS, "rows": rows},
            "lines": flows, "paragraph_wanted": False,
            "not_tracked": [f"{r['label']}: not stored" for r in d["rows"]
                            if r.get("latest") is None],
            "table_note": note, "data": {"dsr": d}}


def federal_subsection(b: dict) -> dict:
    """GTM-12: what the Factor IV panel lacks, with the CBO path as sourced."""
    f, s = b["federal"], b["sourced"]
    rows, nt = [], []
    for r in f["rows"]:
        if r.get("latest") is None:
            rows.append([f"{r['label']} ({r['series']})", gtm.NOT_STORED, "—", "—",
                         "—", "—"])
            nt.append(f"{r['label']}: {r.get('reason') or 'not stored'}")
            continue
        d = r["day"]
        if r["basis"] == "nipa":
            lev = f"${r['latest']:,.0f}bn a year (SAAR)"
            per = f"{d[:4]} Q{(int(d[5:7]) - 1) // 3 + 1}"
        elif r["basis"] == "budget":
            lev, per = f"${r['latest'] / 1000:,.0f}bn", f"FY{d[:4]}"
        else:
            lev, per = f"{r['latest']:.1f}% of GDP", f"FY{d[:4]}"
        share = ("—" if r["basis"] == "gdp" else
                 f"{r['share']:.1f}% of {r['share_of']}" if r.get("share") is not None
                 else gtm.NOT_STORED)
        rows.append([f"{r['label']} ({r['series']})", lev, per, share,
                     _pr(r.get("pctile_5y"), r.get("n_5y")),
                     _pr(r.get("pctile_full"), f"{r.get('n_full')}, since "
                         f"{str(r.get('since') or '')[:4]}")])
    lines = []
    cbo = [s.get(i) for i in f["cbo_path"]]
    if all(cbo):
        lines.append(f"The CBO debt path, federal net debt as a share of GDP (CBO's "
                     f"February 2026 update, through the Guide): {gtm.cite(cbo[0])} "
                     f"at the end of FY2025; {gtm.cite(cbo[1])} in 2036.")
    else:
        nt.append("the CBO debt path: not stored (a sourced figure from the scan)")
    for i in ("gtm12.net_interest", "gtm12.defense", "gtm12.customs", "gtm12.deficit"):
        r = s.get(i)
        if r:
            lines.append(f"{r['label']}: {gtm.cite(r)}.")
    note = ("What the Factor IV rows lacked (they carry debt to GDP and r minus g). "
            "Two bases, never mixed in one ratio: the national accounts, quarterly "
            "at an annual rate, as a share of federal current expenditures "
            "(FGEXPND) -- defense there is consumption and gross investment, which "
            "current expenditures exclude, so its share is a ratio, not a slice; "
            "and the budget by fiscal year, as a share of net outlays (FYONET). The "
            "deficit prints positive. Percentiles are of the share over ten years "
            "and the full history, with n. The Guide's 2026 figures and the CBO "
            "path are sourced figures, dated, never recomputed. A modifier, read by "
            "a human (GTM-12, SR-56).")
    return {"title": FEDERAL_TITLE, "table": {"columns": FEDERAL_COLUMNS, "rows": rows},
            "lines": lines, "paragraph_wanted": False, "not_tracked": nt,
            "table_note": note, "data": {"federal": f}}


def plumbing_subsections(st, now: str, cadence: str = "weekly",
                         db_path: Optional[str] = None) -> list[dict]:
    def build():
        b = reads(st, now, db_path)
        out = [fi_subsection(b)]
        if cadence == "monthly":
            out += [tariff_subsection(b), dsr_subsection(b), federal_subsection(b)]
        return out
    return _safe(build, "the GTM plumbing tables", [])


# ---------------------------------------------------------------------------
# Slow layers and the base rates
# ---------------------------------------------------------------------------
def _scan_cell(s: dict, i: str) -> str:
    r = s.get(i)
    return r["value"] if r else gtm.NOT_IN_SCAN


def inflection_subsection(b: dict) -> dict:
    s, today = b["sourced"], b["inflection"]["today"]
    cfg = gtm.config()
    rows = []
    # Slide 4's cells, transcribed once (config `sourced`): a declared cell the
    # store does not hold is "not stored"; a cell the slide does not print (the
    # bottoms' dividend yield and 10-year) is "not on the slide".
    declared = {e["id"] for e in cfg.get("sourced") or []}
    for p in cfg["inflection_points"]:
        ids = [f"gtm1.{p['id']}.{f}" for f in cfg["inflection_fields"]]
        cells = [s[i]["value"] if i in s else
                 gtm.NOT_STORED if i in declared else gtm.NOT_ON_SLIDE for i in ids]
        rows.append([f"{p['label']} ({p['kind']})", *cells,
                     "the Guide, slide 4, as of 30 Sep 2026" if any(
                         i in s for i in ids) else "—"])
    rows.append(["30 Sep 2026 (the Guide)",
                 *[_scan_cell(s, f"gtm1.guide.{f}") for f in cfg["inflection_fields"]],
                 "the Guide, §6"])
    lv, y, dy = today["level"], today["yield_10y"], today["dividend_yield"]
    rows.append([f"Today ({(lv or y or {}).get('day') or 'not stored'})",
                 f"{lv['value']:,.0f}" if lv else gtm.NOT_STORED,
                 gtm.NOT_STORED,
                 f"{dy['value']:.1f}%" if dy else gtm.NOT_STORED,
                 f"{y['value']:.2f}%" if y else gtm.NOT_STORED,
                 "the store" + (f"; dividend yield: {dy['source']}" if dy else "")])
    off = sum(1 for r in rows[:8] for c in r[1:5] if c == gtm.NOT_ON_SLIDE)
    note = ("The prior tops and bottoms are the Guide's (slide 4, as of 30 Sep "
            "2026), transcribed once and stored as sourced figures, never "
            f"recomputed; the slide prints {32 - off} of the 32 cells (dividend "
            "yield and the 10-year at the tops only), and the rest print \"not on "
            "the slide\". Today: the S&P 500's close and the 10-year from the store; no "
            "writer stores forward earnings, so the forward P/E is not stored. A "
            "base-rate row for the Top & Bottom report (GTM-1, SR-48).")
    return {"title": INFLECTION_TITLE,
            "table": {"columns": INFLECTION_COLUMNS, "rows": rows},
            "lines": [], "paragraph_wanted": False, "not_tracked": [],
            "table_note": note, "data": {"inflection": today,
                                         "cells_not_on_slide": off}}


def stock_bond_subsection(b: dict) -> dict:
    sb, s = b["stock_bond"], b["sourced"]
    rows, lines = [], []
    if sb["state"] != "ok":
        for e in gtm.config()["stock_bond"]["eras"]:
            rows.append([e["label"], gtm.NOT_STORED, gtm.NOT_STORED, "—",
                         f"{_scan_cell(s, 'gtm7.' + e['id'] + '.corr')} / "
                         f"{_scan_cell(s, 'gtm7.' + e['id'] + '.inflation')}"])
        lines.append(f"Not computed: {sb['absent_reason']}; the Guide's eras print "
                     f"as sourced figures.")
    else:
        for e in sb["eras"]:
            guide = (f"{_scan_cell(s, 'gtm7.' + e['id'] + '.corr')} / "
                     f"{_scan_cell(s, 'gtm7.' + e['id'] + '.inflation')}")
            if e["computed"]:
                rows.append([f"{e['label']} ({e['start']} to {e['end']})",
                             _c(e["correlation"]), _pct(e["inflation"], 2),
                             f"{e['n_windows']} windows", guide])
            else:
                rows.append([f"{e['label']} ({e['start']} to {e['end']})",
                             f"not reached ({100 * e['coverage']:.0f}% of months)",
                             "—", f"{e['n_windows']} windows",
                             guide + " (the Guide, labelled)"])
        cur = sb["current"]
        if cur["correlation"] is not None:
            # The current window and the Guide's 2021 to 2025 era are different
            # windows; both print, each with its own, and the table says which
            # one the regime word is read on.
            win = f"{cur.get('from') or '?'} to {cur['month']}"
            rows.append([f"Latest 24-month window ({win})", _c(cur["correlation"]),
                         "—", "1 window",
                         f"era 2021 to 2025: {_scan_cell(s, 'gtm7.2021-now.corr')}"])
            lines.append(f"The latest 24-month correlation, {win}: "
                         f"{cur['correlation']:+.2f}, {cur['word']}; the Guide's "
                         f"{_scan_cell(s, 'gtm7.2021-now.corr')} is its 2021 to 2025 "
                         f"era average, a different window. The regime word is read "
                         f"on the latest 24-month window. Book A's rule "
                         f"table reads this word only (A-1 as amended), and nothing "
                         f"automated does.")
    note = ("Monthly total returns from Shiller's sheet: the S&P Composite with its "
            "dividend, and a 10-year par bond priced off the long rate (GS10). Each "
            "era is the average of the 24-month rolling correlations whose window "
            "ends in it, beside the era's average CPI inflation on the year. The "
            "Guide's figures are its own, as of 30 Sep 2026 (2021 to 2025). Amends "
            "SR-9 (GTM-7).")
    return {"title": SB_TITLE, "table": {"columns": SB_COLUMNS, "rows": rows},
            "lines": lines, "paragraph_wanted": False, "not_tracked": [],
            "table_note": note, "data": {"stock_bond": sb}}


def sentiment_subsection(b: dict) -> dict:
    se, s = b["sentiment"], b["sourced"]
    rows, lines = [], []
    gp, gt = s.get("gtm8.peaks"), s.get("gtm8.troughs")
    if se["state"] != "ok":
        rows += [["Peaks", "—", gtm.NOT_STORED, "—", f"{gtm.cite(gp)}"],
                 ["Troughs", "—", gtm.NOT_STORED, "—", f"{gtm.cite(gt)}"]]
        lines.append(f"Not computed: {se['absent_reason']}.")
    else:
        for kind, g in (("peaks", gp), ("troughs", gt)):
            k = se[kind]
            rows.append([kind.capitalize(), str(k["n"]), _pct(k["mean"], 1, True),
                         _pct(k["median"], 1, True),
                         f"{g['value']} ({g['n']})" if g else gtm.NOT_STORED])
        cur = se["current"]
        tr = se["troughs"]
        lines.append(f"Michigan sentiment {cur['value']:.1f} ({cur['month']}), the "
                     f"{_ord(cur['percentile_full'])} percentile of "
                     f"{cur['n_full']} readings since {se['first_month'][:4]}; the "
                     f"S&P 500 {cur['spx_from_ath_pct']:+.1f}% from its all-time "
                     f"high." if cur.get("spx_from_ath_pct") is not None else
                     f"Michigan sentiment {cur['value']:.1f} ({cur['month']}).")
        lines.append(f"Caveat: {se['caveat']}. Of our {tr['with_price']} troughs, "
                     f"{tr['at_price_low']} came with the S&P 500 at least "
                     f"{gtm.config()['sentiment']['price_low_drawdown_pct']:.0f}% below "
                     f"its 12-month high.")
    note = ("Our own turning points of FRED's Michigan sentiment (UMCSENT; quarterly "
            "before 1978): the extreme within 12 months either side, alternating, a "
            "swing of at least 15 points; the S&P 500's price return over the next "
            "12 months from month-end closes. The Guide's figures are its own (as "
            "of 30 Sep 2026), never recomputed. A base-rate row; the disagreement "
            "with its applicability is a draft in the narrative register (GTM-8, "
            "SR-52).")
    return {"title": SENT_TITLE, "table": {"columns": SENT_COLUMNS, "rows": rows},
            "lines": lines, "paragraph_wanted": False, "not_tracked": [],
            "table_note": note, "data": {"sentiment": se}}


def ath_subsection(b: dict) -> dict:
    a, s = b["ath"], b["sourced"]
    sm, ytd = a["sample"], a["ytd"]
    ok, yok = sm.get("state") == "ok", ytd.get("state") == "ok"
    rows = [
        ["All-time highs", str(sm["ath_count"]) if ok else gtm.NOT_STORED,
         "—", (str(ytd["ath_count"]) if yok else gtm.NOT_STORED)
         + (f" (the Guide: {_scan_cell(s, 'gtm9.ytd_count')} to 30 Sep)")],
        ["Share of sessions", _pct(sm.get("share_of_sessions")) if ok else gtm.NOT_STORED,
         _scan_cell(s, "gtm9.share_days"),
         _pct(ytd.get("share_of_sessions")) if yok else gtm.NOT_STORED],
        ["Share that became floors", _pct(sm.get("share_floors")) if ok else gtm.NOT_STORED,
         _scan_cell(s, "gtm9.share_floors"), "—"],
        ["Followed by another within a week",
         _pct(sm.get("share_followed_within")) if ok else gtm.NOT_STORED,
         _scan_cell(s, "gtm9.share_week"), "—"],
    ]
    note = ("From the S&P 500's daily closes (^GSPC). A floor is the scan's "
            "definition: an all-time high the index never afterwards closed 5% or "
            "more below, to the end of the data. Within a week: another all-time "
            f"high in the next five sessions. n: {sm.get('ath_count', 0)} all-time "
            f"highs in {sm.get('sessions', 0)} sessions. The Guide's figures are its "
            "own. A base-rate row the Bull Rebuttal reads as the order places it, "
            "with no new right (GTM-9, SR-53).")
    return {"title": ATH_TITLE, "table": {"columns": ATH_COLUMNS, "rows": rows},
            "lines": [], "paragraph_wanted": False, "not_tracked": [],
            "table_note": note, "data": {"ath": a}}


def slow_subsections(st, now: str, db_path: Optional[str] = None) -> list[dict]:
    def build():
        b = reads(st, now, db_path)
        return [inflection_subsection(b), stock_bond_subsection(b),
                sentiment_subsection(b), ath_subsection(b)]
    return _safe(build, "the GTM base-rate tables", [])


def base_rate_rows(st, now: str, db_path: Optional[str] = None) -> list[list[str]]:
    """Four cells each, the base-rates table's form: what, figure, range, extra."""
    def build():
        b = reads(st, now, db_path)
        out = []
        y = b["inflection"]["today"]["yield_10y"]
        tops = [b["sourced"].get(f"gtm1.top_{k}.yield_10y") for k in
                ("2000", "2007", "2020", "2022")]
        out.append(["The 10-year at the four prior tops (GTM-1, n=4)",
                    " / ".join(t["value"] for t in tops if t) or gtm.NOT_STORED,
                    f"today {y['value']:.2f}%" if y else f"today {gtm.NOT_STORED}",
                    "the Guide's tops; ours today"])
        se = b["sentiment"]
        if se["state"] == "ok":
            out.append([f"S&P 500, 12 months after a sentiment trough "
                        f"(GTM-8, n={se['troughs']['n']})",
                        f"mean {_pct(se['troughs']['mean'], 1, True)}",
                        f"after peaks {_pct(se['peaks']['mean'], 1, True)} "
                        f"(n={se['peaks']['n']})",
                        f"caveat: {se['caveat']}"])
        sm = b["ath"]["sample"]
        if sm.get("state") == "ok":
            out.append([f"All-time highs that became floors, 1988 to 2025 "
                        f"(GTM-9, n={sm['ath_count']})",
                        _pct(sm["share_floors"]),
                        f"followed within a week {_pct(sm['share_followed_within'])}",
                        "never closed 5% below (the scan's definition)"])
        return out
    return _safe(build, "the GTM base-rate rows", [])

# ---------------------------------------------------------------------------
# Part 2: Mechanics (GTM-3 and GTM-4) and the sector rows (GTM-10)
# ---------------------------------------------------------------------------
def _x(v) -> str:
    return gtm.NOT_STORED if v is None else f"{v:.1f}x"


def _missing(names: list) -> str:
    return f"not stored (no multiple for {', '.join(names)})"


def _guide(s: dict, i: str) -> str:
    """The Guide's figure as printed, or "not stored" -- never recomputed."""
    r = s.get(i)
    return r["value"] if r else gtm.NOT_STORED


def twin_subsection(e: dict) -> dict:
    """GTM-3: the concentration twin, beside item 31's table. Report-only."""
    t, s = e["twin"], e["sourced"]
    rows, avg = [], []
    if t["state"] != "ok":
        for lab, i in (("Top-10 share of index market cap", "gtm3.cap_share"),
                       ("Top-10 share of index earnings (trailing)", "gtm3.earn_share"),
                       ("Forward P/E, the top 10", "gtm3.top10.pe"),
                       ("Forward P/E, the other 490", "gtm3.other.pe"),
                       ("Forward P/E, the S&P 500", "gtm3.index.pe")):
            rows.append([lab, gtm.NOT_STORED, "—", _guide(s, i)])
        nt = [f"the concentration twin: {t['absent_reason']}"]
        lines = []
    else:
        L = t["latest"]
        d = L["day"]
        es = (_pct(L["earn_share"]) if L.get("earn_share") is not None else
              _missing(L["missing_trailing"]) if L["missing_trailing"] else
              "not stored (no index trailing earnings)")
        rows += [["Top-10 share of index market cap", _pct(L["cap_share"]), d,
                  _guide(s, "gtm3.cap_share")],
                 ["Top-10 share of index earnings (trailing)", es,
                  f"{d}; index earnings to {L.get('index_earnings_month') or '—'}",
                  _guide(s, "gtm3.earn_share")]]
        miss_f = L["missing_forward"]
        for lab, k, i in (("Forward P/E, the top 10", "pe_top", "gtm3.top10.pe"),
                          ("Forward P/E, the other 490", "pe_other", "gtm3.other.pe"),
                          ("Forward P/E, the S&P 500", "pe_index", "gtm3.index.pe")):
            v = L.get(k)
            cell = (_x(v) if v is not None else
                    _missing(miss_f) if miss_f and k != "pe_index" else
                    "not stored (no S&P DJI forward EPS)")
            rows.append([lab, cell, d, _guide(s, i)])
        for lab, k, g in (("The top 10", "pe_top", "top10"),
                          ("The other 490", "pe_other", "other"),
                          ("The S&P 500", "pe_index", "index")):
            o = t["own"].get(k)
            if o:
                win = (f"{o['average']:.1f}x ({o['from']} to {o['to']}, n={o['n']}"
                       + ("; short" if o["short"] else "") + ")")
                pct = f"{o['pct_of_average']:.0f}%" if o.get("pct_of_average") else "—"
            else:
                win, pct = gtm.NOT_STORED, gtm.NOT_STORED
            avg.append([lab, pct, win, _guide(s, f"gtm3.{g}.pct_avg"),
                        _guide(s, f"gtm3.{g}.avg")])
        nt = []
        lines = [f"Ours: the ten largest issuers on {d} ({', '.join(L['issuers'])}), "
                 f"the same ten as the peak-band line above."]
        if any(o and o["short"] for o in t["own"].values()):
            lines.append(f"Our own history is short ({t['days']} holdings days); "
                         f"the Guide's averages since 1996 are the comparison.")
    note = ("Cap share: SPY's holdings, a second share class counted with its "
            "issuer. Earnings share: each name's weight over its trailing P/E "
            "(Yahoo's trailing twelve months) times the index's trailing P/E (the "
            "S&P 500's close over Shiller's trailing twelve-month earnings) -- cap "
            "share over P/E is earnings share. Forward P/E: the top 10's from "
            "Yahoo's forward P/E (the next fiscal year); the index's from S&P DJI's "
            "forward operating EPS; the other 490 back the top 10 out of the index, "
            "the Guide's method. The bases differ from the Guide's (FactSet), so the "
            "Guide's figures print beside ours and are never recomputed. A name "
            "without its multiple leaves the cell not stored, never a partial sum. "
            "Report-only: GTM-3 enters the Top & Bottom overlay only through its "
            "intake queue, one candidate at a time, and its entry is a draft "
            "(config/tb_intake_queue.yaml); no right is granted (SR-50).")
    return {"title": TWIN_TITLE, "table": {"columns": TWIN_COLUMNS, "rows": rows},
            "tables": [{"columns": TWIN_AVG_COLUMNS, "rows": avg}] if avg else [],
            "lines": lines, "paragraph_wanted": False, "not_tracked": nt,
            "table_note": note, "data": {"twin": t}}


def bucket_rows(e: dict) -> tuple[list, list]:
    """The five buckets and the total: ours where every member is stored, else
    the Guide's figure, labelled. Never a partial computation."""
    b, s = e["buckets"], e["sourced"]
    rows, nt = [], []
    for r in b["rows"]:
        g = f"gtm4.{r['id']}"
        cells, srcs = [], []
        for k, fmt in (("weight", _pct), ("ytd", lambda v: _pct(v, 1, True)),
                       ("ntm_pe", _x)):
            if r.get(k) is not None:
                cells.append(fmt(r[k]))
                srcs.append("ours")
            else:
                cells.append(f"{_guide(s, f'{g}.{k}')} (the Guide's)")
                srcs.append("the Guide's")
        src = ("ours" if set(srcs) == {"ours"} else
               "the Guide's, slide 11" if set(srcs) == {"the Guide's"} else
               "mixed: each cell labelled")
        rows.append([r["label"], *cells, src])
        if r.get("reason"):
            nt.append(f"{r['label']}: {r['reason']} -- the Guide's figures print")
        else:
            for k, miss in (r.get("missing") or {}).items():
                if miss:
                    nt.append(f"{r['label']}, {k.replace('_', ' ')}: not stored for "
                              f"{', '.join(miss)} -- the Guide's figure prints")
    tot = b.get("total_weight")
    rows.append(["The five together (each name once)",
                 _pct(tot) if tot is not None
                 else f"{_guide(s, 'gtm4.total.weight')} (the Guide's)", "—", "—",
                 "ours" if tot is not None else "the Guide's, slide 11"])
    return rows, nt


def bridge_rows(e: dict) -> tuple[list, list]:
    br, s = e["bridge"], e["sourced"]
    rows, nt = [], []
    n = len(br["filers"])
    for r in br["rows"]:
        lack = sorted(set(r["lack"]["ocf"]) | set(r["lack"]["capex"]))
        def ns(lk: list) -> str:
            return ("not stored" if len(lk) == n
                    else f"not stored ({', '.join(lk)})")
        rows.append([str(r["year"]),
                     _bn(r["ocf"]) if r["ocf"] is not None else ns(r["lack"]["ocf"]),
                     _bn(r["capex"]) if r["capex"] is not None else ns(r["lack"]["capex"]),
                     _bn(r["fcf"]) if r["fcf"] is not None else "—",
                     _guide(s, f"gtm4.capex.{r['year']}"),
                     f"{n - len(lack)} of {n}"])
    if br["state"] != "ok":
        nt.append(f"the cash-flow bridge: {br['absent_reason']}")
    for y in gtm.config()["ai_buckets"]["forecast_years"]:
        rows.append([f"{y} (forecast)", "—", "—", "—",
                     _guide(s, f"gtm4.capex.{y.lower()}"), "consensus"])
    return rows, nt


def _bn(v) -> str:
    return gtm.NOT_STORED if v is None else f"${v / 1e9:,.0f}bn"


def buckets_subsection(e: dict, cadence: str) -> dict:
    """GTM-4. The Weekly carries the bucket table; the Monthly adds the
    hyperscaler cash-flow bridge -- the Factor I exhibit."""
    rows, nt = bucket_rows(e)
    tables = []
    if cadence == "monthly":
        brows, bnt = bridge_rows(e)
        tables.append({"columns": BRIDGE_COLUMNS, "rows": brows})
        nt += bnt
    day = e["buckets"].get("day")
    note = ("The Guide's five buckets (slide 11, as of 30 Sep 2026; "
            "config/ai_buckets.yaml, refreshed each quarter from the scan). Ours "
            "where every member is stored: the weight is the members' SPY weights"
            + (f" on {day}" if day else "") + "; the year to date is the market-"
            "weighted price return from the last close of the prior year; the NTM "
            "P/E is the members' weight over the sum of weight over Yahoo's forward "
            "P/E. A bucket the Guide defines by GICS industry has no stored "
            "members, so its cells print the Guide's figures, labelled.")
    if cadence == "monthly":
        note += (" The bridge: the five hyperscalers' operating cash flow and capex "
                 "from their filings (SEC EDGAR's XBRL frames, by calendar frame -- "
                 "a June or May fiscal year sits in the year its larger part falls "
                 "in), only where all five have filed both; the Guide's capex path, "
                 "2026 to 2028 its consensus forecast, beside it, never recomputed. "
                 "Displaces nothing: tables only, no words and no chart, after the "
                 "SR-37 panel.")
    note += " A modifier on Factor I, read by a human (GTM-4, SR-51)."
    return {"title": BUCKETS_TITLE, "table": {"columns": BUCKET_COLUMNS, "rows": rows},
            "tables": tables, "lines": [], "paragraph_wanted": False,
            "not_tracked": nt, "table_note": note,
            "data": {"buckets": e["buckets"],
                     **({"bridge": e["bridge"]} if cadence == "monthly" else {})}}


def place_mechanics(subs: list[dict], gtm_subs: list[dict],
                    after_panel: Optional[str] = None) -> list[dict]:
    """The twin right after item 31's concentration sub-section; the buckets
    right after the SR-37 panel where one is named (the Monthly), else after
    the twin. A sub-section that is not there leaves its GTM table at the end."""
    from . import t1_rest_block                                 # noqa: PLC0415
    by = {x["title"]: x for x in gtm_subs}
    twin, buckets = by.get(TWIN_TITLE), by.get(BUCKETS_TITLE)
    out = []
    for x in subs:
        out.append(x)
        if after_panel and x.get("title") == after_panel and buckets:
            out.append(buckets)
            buckets = None
        if x.get("title") == t1_rest_block.CONC_TITLE and twin:
            out.append(twin)
            twin = None
            if buckets and not after_panel:
                out.append(buckets)
                buckets = None
    return out + [x for x in (twin, buckets) if x]


def mechanics_subsections(st, now: str, cadence: str = "weekly",
                          db_path: Optional[str] = None) -> list[dict]:
    def build():
        e = equity_reads(st, now, db_path)
        return [twin_subsection(e), buckets_subsection(e, cadence)]
    return _safe(build, "the GTM mechanics tables", [])


def _c1(r: dict) -> str:
    return (gtm.NOT_STORED if not r else
            f"{r['corr']:+.2f}" if r["corr"] is not None else
            f"not reached ({r['n']} of {r['window']})")


def sector_corr_column(st, now: str, rows: list[list[str]],
                       db_path: Optional[str] = None) -> list[list[str]]:
    """GTM-10 in the Weekly's leadership table: each sector row gains its
    one-year correlation to the 10-year's daily change; a pair row gets "—"."""
    def build():
        e = equity_reads(st, now, db_path)
        by = {r["etf"]: r["one_year"] for r in e["sectors"]["rows"]}
        out = []
        for row in rows:
            etf = row[0].rsplit("(", 1)[-1].rstrip(")") if row[0].endswith(")") else None
            out.append([*row, _c1(by.get(etf)) if etf in by else "—"])
        return out
    return _safe(build, "the GTM-10 column", [[*r, "—"] for r in rows])


def sector_table(st, now: str, db_path: Optional[str] = None) -> Optional[dict]:
    """GTM-10's full rows for the Monthly's sector sub-section: ours (one year and
    five) beside the Guide's sector figures, each dated."""
    def build():
        from altdata import labels                              # noqa: PLC0415
        e = equity_reads(st, now, db_path)
        s = e["sourced"]
        out = []
        for r in e["sectors"]["rows"]:
            g = f"gtm10.{r['sector_id']}"
            out.append([labels.sector(r["etf"]),
                        f"{_c1(r['one_year'])} / {_c1(r['five_years'])}",
                        _guide(s, f"{g}.corr_guide"),
                        f"{_guide(s, f'{g}.fwd_pe')} ({_guide(s, f'{g}.pe_avg')})",
                        f"{_guide(s, f'{g}.ntm_eps')} ({_guide(s, f'{g}.eps_median')})",
                        f"{_guide(s, f'{g}.foreign_sales')}%"
                        if s.get(f"{g}.foreign_sales") else gtm.NOT_STORED])
        g = f"gtm10.{e['sectors']['index_row']}"
        out.append(["The S&P 500 (the Guide)", "—", _guide(s, f"{g}.corr_guide"),
                    f"{_guide(s, f'{g}.fwd_pe')} ({_guide(s, f'{g}.pe_avg')})",
                    f"{_guide(s, f'{g}.ntm_eps')} ({_guide(s, f'{g}.eps_median')})",
                    f"{_guide(s, f'{g}.foreign_sales')}%"
                    if s.get(f"{g}.foreign_sales") else gtm.NOT_STORED])
        return {"columns": SECTOR_COLUMNS, "rows": out,
                "note": ("Ours: each sector ETF's daily price return against the "
                         "10-year's daily change in basis points (FRED DGS10), over "
                         "the last 252 and 1,260 sessions where both are stored. "
                         "The Guide's columns are its slide 15, as of 30 Sep 2026, "
                         "never recomputed: its correlation is two years of monthly "
                         "returns, a different window and frequency from ours. A "
                         "modifier, read by a human (GTM-10, SR-54).")}
    return _safe(build, "the GTM-10 sector table", None)
