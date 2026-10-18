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

The reads are altdata/gtm.py's; this module lays them out. Every sub-section is
a table and lines, and asks no paragraph (`paragraph_wanted: False`), so none
adds a word to a budget or a chart to a cap. A fault never takes a section down.
Nothing here grants a right: each row is a base-rate row or a modifier, read by
a human.
"""

from __future__ import annotations

import logging
from typing import Optional

from altdata import gtm

log = logging.getLogger(__name__)

FI_TITLE = "Fixed income under a 100 bp shift"
TARIFF_TITLE = "Effective tariff rate"
DSR_TITLE = "Household debt service (SR-5's modifier)"
INFLECTION_TITLE = "Inflection points (the Top & Bottom standing exhibit)"
SB_TITLE = "Stock-bond correlation regime"
SENT_TITLE = "Sentiment turning points"
ATH_TITLE = "All-time highs"

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
TARIFF_COLUMNS = ["Measure", "Latest", "Quarter", "5-year percentile (n)",
                  "Full-history percentile (n)"]
DSR_COLUMNS = ["Series", "Latest", "Quarter", "5-year percentile (n)",
               "Full-history percentile (n)"]

_CACHE: dict = {}


def reads(st, now: str, db_path: Optional[str] = None) -> dict:
    k = (id(st), now, db_path)
    if k not in _CACHE:
        _CACHE.clear()
        _CACHE[k] = gtm.build(st, now, db_path)
    return _CACHE[k]


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
            f"nothing automated (GTM-13, SR-45).")
    return {"title": FI_TITLE, "table": {"columns": FI_COLUMNS, "rows": rows},
            "tables": [{"columns": FI_CORR_COLUMNS, "rows": crow}],
            "lines": [], "paragraph_wanted": False, "not_tracked": absent,
            "table_note": note, "data": {"fixed_income": fi}}


def tariff_subsection(b: dict) -> dict:
    t, s = b["tariff"], b["sourced"]
    rows = []
    if t["state"] == "ok":
        q = t["day"]
        rows.append(["Customs duties over goods imports (ours)", f"{t['latest']:.1f}%",
                     f"{q[:4]} Q{(int(q[5:7]) - 1) // 3 + 1}",
                     _pr(t["pctile_5y"], t["n_5y"]),
                     _pr(t["pctile_full"], f"{t['n_full']}, since {t['since'][:4]}")])
    else:
        rows.append(["Customs duties over goods imports (ours)", gtm.NOT_STORED,
                     "—", "—", "—"])
    for i in ("gtm15.effective", "gtm15.statutory_peak", "gtm15.ieepa"):
        r = _src(s, i)
        lab = r["label"] if r else next(e["label"] for e in gtm.config()["sourced"]
                                        if e["id"] == i)
        rows.append([lab, gtm.cite(r), "—", "—", "—"])
    note = ("Ours: FRED's customs-duties receipts (B235RC1Q027SBEA, quarterly, "
            "billions at an annual rate) over four times the quarter's goods "
            "imports (BOPGIMP, monthly, millions). FRED carries no monthly "
            "customs-receipts series, so the rate is quarterly; and the national-"
            "accounts receipts are not the Census imports-for-consumption basis the "
            "Guide divides by, so the two differ by construction. An inflation "
            "modifier, read by a human (GTM-15, SR-47).")
    return {"title": TARIFF_TITLE, "table": {"columns": TARIFF_COLUMNS, "rows": rows},
            "lines": [], "paragraph_wanted": False,
            "not_tracked": [] if t["state"] == "ok" else [f"the effective tariff rate: "
                                                         f"{t['absent_reason']}"],
            "table_note": note, "data": {"tariff": t}}


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
            "labelled; the scan does not name their quarter. A modifier on SR-5, "
            "the consumer-credit impulse, whose own row is not yet built.")
    return {"title": DSR_TITLE, "table": {"columns": DSR_COLUMNS, "rows": rows},
            "lines": flows, "paragraph_wanted": False,
            "not_tracked": [f"{r['label']}: not stored" for r in d["rows"]
                            if r.get("latest") is None],
            "table_note": note, "data": {"dsr": d}}


def plumbing_subsections(st, now: str, cadence: str = "weekly",
                         db_path: Optional[str] = None) -> list[dict]:
    def build():
        b = reads(st, now, db_path)
        out = [fi_subsection(b)]
        if cadence == "monthly":
            out += [tariff_subsection(b), dsr_subsection(b)]
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
    for p in cfg["inflection_points"]:
        cells = [_scan_cell(s, f"gtm1.{p['id']}.{f}") for f in cfg["inflection_fields"]]
        rows.append([f"{p['label']} ({p['kind']})", *cells,
                     "the Guide, as of 30 Sep 2026" if any(
                         c != gtm.NOT_IN_SCAN for c in cells) else "—"])
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
    missing = sum(1 for r in rows[:8] for c in r[1:5] if c == gtm.NOT_IN_SCAN)
    note = ("The prior tops and bottoms are the Guide's (its inflection-points "
            "slide), stored as sourced figures where the scan states them; the scan "
            f"states {32 - missing} of the 32 cells, and the rest print \"not in the "
            "scan\". Today: the S&P 500's close and the 10-year from the store; no "
            "writer stores forward earnings, so the forward P/E is not stored. A "
            "base-rate row for the Top & Bottom report (GTM-1, SR-37).")
    return {"title": INFLECTION_TITLE,
            "table": {"columns": INFLECTION_COLUMNS, "rows": rows},
            "lines": [], "paragraph_wanted": False, "not_tracked": [],
            "table_note": note, "data": {"inflection": today,
                                         "cells_not_in_scan": missing}}


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
            lines.append(f"The latest 24-month correlation, to {cur['month']}: "
                         f"{cur['correlation']:+.2f}, {cur['word']}. Book A's rule "
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
            "SR-40).")
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
            "with no new right (GTM-9, SR-41).")
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
