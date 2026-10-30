"""
Validation gate for "what's carrying the index" and the allocation block
(16 Oct 2026; signal-triage Batch 6 items 40, 35 and 30 and Batch 5 item 29;
docs/briefs/st-r5-index-notes.md).

FIXTURES only, built here in temporary stores -- no live store, no network, no
model. Every expected figure below is computed by hand in its comment:

  A  ST-R5.40a THE DECOMPOSITION. The three anchors agree with a hand-computed
     fixture (S&P 500 3600 / 6000 / 6600 -> 7800; forward EPS 240 / 300 / 315 ->
     360: earnings' log shares 52.4%, 69.5%, 79.9%); the carrier read; the
     trailing version beside it; with no drop stored the forward legs print
     "awaiting the estimates workbook (drop pending)" and the read falls to the
     trailing one with its as-of; nothing stored at all says so.
  B  ST-R4.29a r-g AND THE REVISIONS-TURN FLAG. g from the drop's eight
     quarters (392/355 - 1 = 10.42%); r-g = 5.05 - 10.42; the flag fires at
     revisions +0.25% with the 10-year +15 bp, not at +0.30%, not with the
     10-year +9.9 bp; awaiting and one-drop states carry their reasons.
  C  ST-R5.35a THE PRICE-ULC GAP. PPI +5.0% against ULC +1.5% carried forward
     from Q2: +3.5 pp; closing at 1.0 pp off the six-month peak fires, 0.9
     does not, a negative gap does not; the margin-source line.
  D  ST-R5.30a THE ALLOCATION BLOCK. Three panels with five-year and full
     percentiles and their n (106 quarters; a short history prints one
     window); bonds and cash as shares of financial assets; AAII and ICI
     listed gaps (AAII's by-hand entry dropped, 16 Oct 2026, and nothing reads
     its keys); "base rate: after ST-R5.30b".
  E  THE CHARTS AND THE CAPS. W11 and M11 render from the fixture (twelve
     months; the cycle low); the Weekly's plan puts W11 before W10 and sets W10
     aside when W6 is open; the Monthly's twelve fill its cap, and a thirteenth
     is set aside, M8 first.
  F  THE DISPLAY. One "What's carrying the index" sub-section in the Weekly's
     What's priced (two anchors) and the Monthly's (three, bucket "carry"); the
     margin line in the earnings block when there is one and in the
     sub-section when there is not; the allocation block in Positioning; the
     close's one line; the filler, coincidence and numeral audits.
  G  THE REGISTRY. Every key read is registered with its units; the four new
     FRED series carry their units and a family and long window; the catalogue
     names the command; nothing here imports regime.

    python tools/validate_st_r5_index.py
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import datetime as dt
import inspect
import json
import math
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import gate_tmp  # noqa: E402

from altdata import observations  # noqa: E402
from altdata import st_r5_index as ix  # noqa: E402
from daily_cascade import index_carry_block as icb  # noqa: E402

PASS = 0
FAIL = 0
LINE = "=" * 78
CFG = ix.config()
NOW_DAY = "2026-10-09"
NOW = NOW_DAY + "T23:00:00+00:00"


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def store(rows: list[tuple]) -> str:
    """(key, instrument, day, value) rows; a str value is stored as text."""
    db = str(Path(gate_tmp.mkdtemp("str5i_")) / "obs.db")
    with observations.ObservationStore(db) as st:
        st.write_many([{"registry_key": k, "instrument": i, "observed_at": d,
                        "available_at": d + "T21:00:00+00:00",
                        "value": v if isinstance(v, str) else float(v),
                        "source": "fixture"} for k, i, d, v in rows])
    return db


def open_store(db: str):
    return observations.ObservationStore(db)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
CLOSES = [("2022-10-12", 3600), ("2025-10-09", 6000), ("2025-12-31", 6600),
          ("2026-02-06", 6800), ("2026-05-08", 7100), ("2026-08-07", 7500),
          (NOW_DAY, 7800)]
DROPS = [("2022-10-07", 240), ("2025-10-03", 300), ("2025-12-26", 315),
         ("2026-02-06", 325), ("2026-05-08", 340), ("2026-08-07", 350),
         ("2026-10-02", 360)]
TRAILING = [("2022-09-01", 190), ("2025-09-01", 225), ("2025-12-01", 232),
            ("2026-06-01", 240)]


def decomposition_rows(forward: bool = True, trailing: bool = True) -> list[tuple]:
    rows = [("yfinance.mkt_gspc", None, d, v) for d, v in CLOSES]
    if forward:
        rows += [("spdji.fwd12m_op_eps", None, d, v) for d, v in DROPS]
    if trailing:
        rows += [("shiller.sp_earnings", None, d, v) for d, v in TRAILING]
    return rows


Q1 = ["2026Q4", "2027Q1", "2027Q2", "2027Q3"]
Q2 = ["2027Q4", "2028Q1", "2028Q2", "2028Q3"]
Y1 = [85.0, 88.0, 90.0, 92.0]                       # sum 355
Y2 = [95.0, 97.0, 99.0, 101.0]                      # sum 392


def drop_rows(revision_pct: float = 0.0, ten_bp: float = 15.0,
              second: bool = True) -> list[tuple]:
    """Two drops, 2026-09-04 and 2026-10-02 (28 days), the same four forward
    quarters revised by `revision_pct`; the 10-year 4.90% on 2026-09-11 and
    4.90 + ten_bp on NOW_DAY."""
    rec = json.dumps({"forward_quarters": Q1})
    rows = [("spdji.eps_drop", None, "2026-09-04", rec)]
    rows += [("spdji.op_eps_est_q", q, "2026-09-04", v) for q, v in zip(Q1 + Q2, Y1 + Y2)]
    if second:
        k = 1 + revision_pct / 100.0
        rows += [("spdji.eps_drop", None, "2026-10-02", rec)]
        rows += [("spdji.op_eps_est_q", q, "2026-10-02", v * k) for q, v in zip(Q1, Y1)]
        rows += [("spdji.op_eps_est_q", q, "2026-10-02", v) for q, v in zip(Q2, Y2)]
    rows += [("fred.yield_10y", None, "2026-09-11", 4.90),
             ("fred.yield_10y", None, NOW_DAY, round(4.90 + ten_bp / 100.0, 4))]
    return rows


def month_list(start: str, n: int) -> list[str]:
    y, m = int(start[:4]), int(start[5:7])
    out = []
    for i in range(n):
        yy, mm = divmod(y * 12 + m - 1 + i, 12)
        out.append(f"{yy:04d}-{mm + 1:02d}-01")
    return out


def gap_rows(last_gaps: list[float]) -> list[tuple]:
    """ULC +1.5% on the year in Q1 and Q2 2026; PPI 100 through 2025 and
    100 x (1 + (1.5 + gap)/100) in 2026, the gaps for January-September."""
    rows = [("fred.ulc_nfb", None, d, 100.0) for d in ("2025-01-01", "2025-04-01")]
    rows += [("fred.ulc_nfb", None, d, 101.5) for d in ("2026-01-01", "2026-04-01")]
    rows += [("fred.ppi_fd_core_ex_trade", None, d, 100.0) for d in month_list("2025-01-01", 9)]
    for d, g in zip(month_list("2026-01-01", 9), last_gaps):
        rows.append(("fred.ppi_fd_core_ex_trade", None, d, 100.0 * (1 + (1.5 + g) / 100.0)))
    return rows


GAPS_CLOSING = [4.0, 4.0, 4.0, 4.5, 4.2, 4.0, 3.8, 3.6, 3.5]   # peak 4.5, last 3.5
GAPS_NEAR = [4.0, 4.0, 4.0, 4.5, 4.2, 4.0, 3.8, 3.7, 3.6]      # 0.9 off the peak
GAPS_NEG = [0.5, 0.5, 0.5, 0.0, -0.2, -0.4, -0.6, -0.8, -1.0]


def quarters(start: str, n: int) -> list[str]:
    return month_list(start, 3 * n)[::3]


def alloc_rows(n: int = 106) -> list[tuple]:
    qs = quarters("2000-01-01", n)
    rows = []
    for i, d in enumerate(qs):
        rows += [("fred.hh_equity_share", None, d, 30.0 + 18.0 * i / (n - 1)),
                 ("fred.hh_fin_assets", None, d, 100000.0),
                 ("fred.hh_debt_securities", None, d, 8000.0 - 30.0 * i),
                 ("fred.hh_deposits", None, d, 15000.0 - 20.0 * i)]
    return rows


# ---------------------------------------------------------------------------
def group_a() -> None:
    print(f"\n{LINE}\nA. ST-R5.40a THE DECOMPOSITION, THREE ANCHORS\n{LINE}")
    with open_store(store(decomposition_rows())) as st:
        d = ix.decomposition(st, NOW, CFG)
    f = d["versions"]["forward"]["anchors"]
    check(d["anchors"] == {"cycle_low": "2022-10-12", "twelve_months": "2025-10-09",
                           "ytd": "2025-12-31"},
          f"the anchors: the 12 Oct 2022 low, twelve months, the prior year's end "
          f"({d['anchors']})")
    # By hand: ln(7800/3600)=0.773190, ln(360/240)=0.405465 -> 52.4%;
    # ln(7800/6000)=0.262364, ln(360/300)=0.182322 -> 69.5%;
    # ln(7800/6600)=0.167054, ln(360/315)=0.133531 -> 79.9%.
    want = {"cycle_low": (116.67, 50.0, 52.4, 47.6, 15.0),
            "twelve_months": (30.0, 20.0, 69.5, 30.5, 20.0),
            "ytd": (18.18, 14.29, 79.9, 20.1, 20.95)}
    got = {k: (a["price_pct"], a["eps_pct"], a["eps_share_pct"], a["pe_share_pct"],
               a["pe_start"]) for k, a in f.items()}
    check(got == want, f"each anchor agrees with the hand computation ({got})")
    check(all(abs(a["log_eps"] + a["log_pe"] - a["log_price"]) < 1e-5 for a in f.values())
          and f["twelve_months"]["pe_end"] == round(7800 / 360, 2),
          "the split is exact in logs: ln P = ln EPS + ln P/E")
    check(f["twelve_months"]["carrier"] == "earnings carry most of the gain",
          "the carrier: earnings carry most of the twelve months' gain")
    check(ix.carrier(-0.05, 0.15, 0.10, 0.01) ==
          "the multiple carries the gain; earnings work against it"
          and ix.carrier(0.002, 0.001, 0.003, 0.01) ==
          "neither: the index is flat over the span",
          "the multiple carrying it, and a flat index, each read so")
    t = d["versions"]["trailing"]
    check(t["state"] == "read" and t["eps_as_of"] == "2026-06-01"
          and t["anchors"]["cycle_low"]["eps_start_as_of"] == "2022-09-01",
          "the trailing version beside it, each earnings leg at its own as-of")
    line = ix.read_line(d)
    check(line.startswith("What's carrying the index, twelve months (2025-10-09 to "
                          "2026-10-09): the S&P 500 +30.0%, forward EPS +20.0%")
          and "earnings 70% of it in log terms" in line,
          f"the read line names the leg: {line[:120]}")
    with open_store(store(decomposition_rows(forward=False))) as st:
        a = ix.decomposition(st, NOW, CFG)
    rows = icb.decomposition_rows(a, icb.ANCHORS["weekly"])
    la = ix.read_line(a)
    check(a["versions"]["forward"]["state"] == "awaiting"
          and rows[0][:3] == ["All anchors", "forward",
                              "awaiting the estimates workbook (drop pending)"]
          and "trailing EPS" in la and "trailing earnings as of 2026-06" in la
          and "awaiting the estimates workbook (drop pending)" in la,
          "no drop stored: the forward legs print 'drop pending'; the read falls to "
          "trailing with its as-of")
    with open_store(store(decomposition_rows(forward=True, trailing=False)
                          [:len(CLOSES)] + [("spdji.fwd12m_op_eps", None, "2026-10-02",
                                             360)])) as st:
        one = ix.decomposition(st, NOW, CFG)
    check("no S&P DJI drop stored on or before 2025-10-09" in
          one["versions"]["forward"]["anchors"]["twelve_months"]["reason"],
          "a drop newer than the anchor: that anchor is absent, with its reason")
    with open_store(store([])) as st:
        e = ix.decomposition(st, NOW, CFG)
    check(e["absent"] and "not read" in ix.read_line(e), "nothing stored: says so")


def rg(rows) -> dict:
    with open_store(store(rows)) as st:
        return ix.r_minus_g(st, NOW, CFG)


def group_b() -> None:
    print(f"\n{LINE}\nB. ST-R4.29a r-g AND THE REVISIONS-TURN FLAG\n{LINE}")
    r0 = rg(drop_rows(0.0, 15))
    g = r0["g"]
    check(not g["absent"] and g["g_pct"] == round(100 * (392 / 355 - 1), 2) == 10.42
          and g["year1"] == Q1 and g["year2"] == Q2,
          "g: the four quarters after the forward four against them, 392/355 - 1 = "
          "10.42%")
    check(r0["r_minus_g_pp"] == round(5.05 - 10.42, 2),
          f"r-g = the 10-year 5.05% less g ({r0['r_minus_g_pp']} pp)")
    r = rg(drop_rows(0.25, 15))
    check(r["flag"] == "on" and r["revision_pct"] == 0.25 and r["ten_change_bp"] == 15.0,
          "revisions +0.25% with the 10-year +15 bp: the flag fires (at threshold)")
    check(rg(drop_rows(0.30, 15))["flag"] == "off", "+0.30%: off (above flat)")
    check(rg(drop_rows(-1.0, 9.9))["flag"] == "off", "the 10-year +9.9 bp: off")
    check(rg(drop_rows(-1.0, 10))["flag"] == "on", "falling estimates, the 10-year "
          "+10 bp: on")
    lines = ix.r_minus_g_lines(r0)
    check(lines[0].startswith("r−g -5.37 pp: the 10-year 5.05%")
          and "Revisions turn" in lines[1] and "(descriptive; unvalidated, n=0)" in lines[1],
          f"the lines: {lines[0][:60]} / {lines[1][:40]}")
    one = rg(drop_rows(second=False))
    check(one["flag"] == "absent" and "second drop" in one["flag_reason"]
          and not one["g"]["absent"],
          "one drop: g prints, the flag needs a second drop")
    none = rg([("fred.yield_10y", None, NOW_DAY, 5.0)])
    check(none["g"]["absent"] and "drop pending" in ix.r_minus_g_lines(none)[0]
          and "5.00%" in ix.r_minus_g_lines(none)[0],
          "no drop: 'drop pending', with the 10-year printed")
    with open_store(store(drop_rows(0.25, 15) + gap_rows(GAPS_CLOSING))) as st:
        lead = ix.build(st, NOW, CFG)["r_minus_g"]
    check(lead["leading"] is True and "closing from above (a leading input)" in
          ix.r_minus_g_lines(lead)[1],
          "the price-ULC gap's closing flag prints beside it as the leading input")


def gap(rows) -> dict:
    with open_store(store(rows)) as st:
        return ix.price_ulc(st, NOW, CFG)


def group_c() -> None:
    print(f"\n{LINE}\nC. ST-R5.35a THE CORPORATE-PRICE/ULC GAP\n{LINE}")
    g = gap(gap_rows(GAPS_CLOSING))
    check(not g["absent"] and g["month"] == "2026-09-01" and round(g["gap_pp"], 2) == 3.5
          and round(g["ppi_yoy_pct"], 2) == 5.0 and round(g["ulc_yoy_pct"], 2) == 1.5
          and g["ulc_quarter"] == "2026-04-01" and g["carried"],
          "PPI +5.0% against ULC +1.5% (Q2, carried forward): +3.5 pp")
    check(g["closing"] and round(g["off_peak_pp"], 2) == 1.0 and round(g["peak_pp"], 2) == 4.5,
          "1.0 pp below the six-month peak of 4.5: closing (at threshold)")
    check(not gap(gap_rows(GAPS_NEAR))["closing"], "0.9 pp below the peak: not")
    check(not gap(gap_rows(GAPS_NEG))["closing"], "a gap below zero: not closing "
          "from above")
    lines = ix.price_ulc_lines(g)
    check("Q2 2026, carried forward to the next print" in lines[0] and "n=" in lines[0]
          and "closing from above" in lines[1],
          f"the lines label the carried quarter and the percentile's n: {lines[0][:70]}")
    ml = ix.margin_line(g)
    check("pricing ahead of cost" in ml
          and "cost ahead of pricing" in ix.margin_line(gap(gap_rows(GAPS_NEG))),
          "the margin-source line: pricing-led, and the squeeze when cost leads")
    check(gap([])["absent"] and "not read" in ix.price_ulc_lines(gap([]))[0],
          "nothing stored: absent, with its reason")


def group_d() -> None:
    print(f"\n{LINE}\nD. ST-R5.30a THE ALLOCATION BLOCK\n{LINE}")
    rows = alloc_rows()
    with open_store(store(rows)) as st:
        a = ix.allocation(st, NOW, CFG)
    eq, bo, ca = (a["panels"][k] for k in ("equities", "bonds", "cash"))
    check(round(eq["share_pct"], 1) == 48.0 and eq["quarter"] == "2026-04-01"
          and round(bo["share_pct"], 2) == round(100 * (8000 - 30 * 105) / 100000, 2)
          and round(ca["share_pct"], 2) == round(100 * (15000 - 20 * 105) / 100000, 2),
          "equities the Fed's share; bonds and cash over financial assets")
    lz = eq["lens"]
    check(lz["n_full"] == 106 and lz["n_window"] == 20 and not lz["same"]
          and lz["percentile_full"] == 100.0,
          "five-year (n=20) and full (n=106) percentiles, each with its n")
    tbl = icb.positioning_subsection.__name__ and ix.allocation_rows(a)
    check("of 5 years (n=20)" in tbl[0][4] and "since 2000-01-01 (n=106)" in tbl[0][4]
          and tbl[0][2] == "Q2 2026",
          f"the table prints both windows: {tbl[0][4][:80]}")
    lines = ix.allocation_lines(a)
    check("base rate: after ST-R5.30b" in lines[0]
          and lines[1].startswith("AAII asset-allocation survey: not tracked")
          and "403" in lines[1] and "by hand" not in lines[1].replace("by-hand", "")
          and lines[2].startswith("ICI monthly: no free source"),
          "the base-rate placeholder; AAII and ICI listed gaps, nothing by hand")
    check("aaii_keys" not in (CFG.get("allocation") or {}) and "aaii" not in a,
          "no AAII key is read (the by-hand entry is dropped)")
    with open_store(store(alloc_rows(8))) as st:
        short = ix.allocation(st, NOW, CFG)
    check(short["panels"]["equities"]["lens"]["same"]
          and "shorter than 5 years" in ix.allocation_rows(short)[0][4],
          "a short history prints one window, named as shorter than five years")
    with open_store(store([])) as st:
        sub = icb.positioning_subsection(st, NOW)
    check(sub["table"]["rows"] == [] and len(sub["not_tracked"]) == 3
          and all("not stored yet" in x for x in sub["not_tracked"]),
          "nothing stored: no empty rows asking for a read; each panel footnoted")


def group_e() -> None:
    print(f"\n{LINE}\nE. THE CHARTS AND THE CAPS\n{LINE}")
    from daily_cascade import charts as charts_mod               # noqa: PLC0415
    from daily_cascade import weekly_stack as ws                # noqa: PLC0415
    from monthly_macro import charts as mch                     # noqa: PLC0415
    out = gate_tmp.mkdtemp("str5i_ch_")
    with open_store(store(decomposition_rows())) as st:
        w = ix.chart_series(st, NOW, "twelve_months", CFG)
        m = ix.chart_series(st, NOW, "cycle_low", CFG)
    check(w["version"] == "forward" and w["anchor_day"] == "2025-10-09"
          and w["series"]["S&P 500"][0][1] == 100.0
          and w["series"]["S&P 500"][-1][1] == 130.0
          and w["series"]["Forward EPS"][-1][1] == 120.0
          and abs(w["series"]["Forward P/E"][-1][1] - round(100 * 1.3 / 1.2, 2)) < 0.01,
          "the chart's lines, indexed to 100: price 130 = EPS 120 x P/E 108.33")
    cw = charts_mod.index_carry("W11", w, "twelve months", "w11", out)
    cm = charts_mod.index_carry("M11", m, "since the 12 Oct 2022 low", "m11", out)
    check(not cw.get("unavailable") and not cm.get("unavailable")
          and cw.get("svg_path") and "twelve months" in cw["title"]
          and "since the 12 Oct 2022 low" in cm["title"],
          f"W11 and M11 render, each title naming its span "
          f"({cw.get('unavailable') or cm.get('unavailable') or 'drawn'})")
    check(charts_mod.index_carry("W11", {"absent": True, "reason": "x"}, "",
                                 "n", out).get("unavailable") == "x",
          "with nothing to draw, the chart says why")
    ed = {"budget": {"charts": 10}, "sections": [{"id": "misfit", "data": {}}]}
    plan = ws.chart_plan(ed)
    check(plan == ["W1", "W2", "W8", "W7", "W3", "W5", "W4", "W9", "W11", "W10"],
          "the Weekly's ten fill its cap, W11 before W10")
    ed["sections"][0]["data"] = {"open_contradictions": [1]}
    plan6 = ws.chart_plan(ed)
    check("W11" in plan6 and "W10" not in plan6 and len(plan6) == 10,
          "with W6 open, W10 is the one set aside; W11 holds")
    check(ws.PLACE["W11"] == ("priced", None) and mch.PLACE["M11"] == ("priced", "carry")
          and "M11" in mch.ORDER and len(mch.ORDER) == 13 and mch.ORDER[-1] == "M13",
          "W11 prints in What's priced; M11 beside its block; thirteen planned (M13, "
          "ST-14's, last)")
    many = {k: {"id": k, "png": b"x"} for k in mch.ORDER}
    check(mch.hold_cap(dict(many), 13) == [], "thirteen render at the cap of 13")
    many["M99"] = {"id": "M99", "png": b"x"}
    check(mch.hold_cap(many, 13) == ["M13"], "a fourteenth: M13 is set aside first")
    twelve = {k: v for k, v in many.items() if k != "M13"}
    check(mch.hold_cap(twelve, 12) == ["M8"],
          "without M13, a thirteenth at the cap of 12: M8 is set aside first")


def group_f() -> None:
    print(f"\n{LINE}\nF. THE DISPLAY AND THE EXISTING AUDITS\n{LINE}")
    from altdata import numeral_audit as na                     # noqa: PLC0415
    from daily_cascade import stack as stack_mod                # noqa: PLC0415
    from daily_cascade import stack_prose as sp                 # noqa: PLC0415
    from daily_cascade import weekly_stack as ws                # noqa: PLC0415
    from monthly_macro import stack as mstack                   # noqa: PLC0415
    rows = (decomposition_rows() + drop_rows(0.25, 15) + gap_rows(GAPS_CLOSING)
            + alloc_rows())
    db = store(rows)
    then = "2026-10-02T23:00:00+00:00"
    cfg = stack_mod.config()
    with open_store(db) as st:
        wk = ws.priced_week(st, NOW, then, cfg, None, None, None)
        mo = mstack.priced_section(st, NOW, "2026-09-09T23:00:00+00:00", cfg, None,
                                   None, None)
        pos = ws.positioning_week(st, NOW, then)
        close = icb.close_items(st, NOW)
        alone = icb.priced_subsection(st, NOW, "weekly", margin=True)
        inside = icb.priced_subsection(st, NOW, "weekly", margin=False)
    wt = [s for s in wk["subsections"] if s.get("title") == icb.TITLE]
    check(len(wt) == 1 and [r[0] for r in wt[0]["table"]["rows"]] ==
          ["Twelve months", "Year to date", "Twelve months", "Year to date"],
          "the Weekly's What's priced: one sub-section, twelve months and YTD, "
          "forward and trailing")
    mt = [s for s in mo["subsections"] if s.get("title") == icb.TITLE]
    check(len(mt) == 1 and mt[0].get("bucket") == "carry"
          and [r[0] for r in mt[0]["table"]["rows"]][:3] ==
          ["Since the 12 Oct 2022 low", "Twelve months", "Year to date"],
          "the Monthly's: all three anchors, bucket 'carry' for M11")
    check(any(l.startswith("Margin source") for l in alone["lines"])
          and not any(l.startswith("Margin source") for l in inside["lines"]),
          "the margin line rides in the sub-section only when no earnings block "
          "carries it")
    src = inspect.getsource(ws.priced_week)
    check('startswith("Earnings")' in src and "margin=eb is None" in src,
          "and the Weekly puts it in the earnings block when the season has one")
    pt = [s for s in pos["subsections"] if s.get("title") == icb.ALLOC_TITLE]
    check(len(pt) == 1 and len(pt[0]["table"]["rows"]) == 3,
          "Positioning & flows carries the three-panel allocation block")
    check(len(close) == 1 and close[0]["key"] == "priced:index_carry"
          and close[0]["text"].startswith("What's carrying the index, twelve months")
          and "index_carry_block.close_items" in inspect.getsource(stack_mod.build),
          "the close carries the one-line read only, in What's priced")
    lines = wt[0]["lines"] + pt[0]["lines"] + [close[0]["text"]]
    check(not [x for x in lines if sp.filler_faults(x)], f"no line is filler "
          f"({len(lines)} lines)")
    causal = [x for x in lines if re.search(r"\b(because|drove|driven by|due to|caused|"
                                            r"on the back of|in response to|reacting to)\b",
                                            x, re.I)]
    check(not causal, f"no line claims a cause ({causal[:1]})")
    a = wt[0]["data"]["index_carry"]["decomposition"]["versions"]["forward"]["anchors"][
        "twelve_months"]
    head = close[0]["text"].split(" — ")[0]
    r = na.audit(head, na.with_signed({"price_pct": a["price_pct"],
                                       "eps_pct": a["eps_pct"],
                                       "pe_change_pct": a["pe_change_pct"],
                                       "eps_share_pct": a["eps_share_pct"],
                                       "start_day": a["start_day"],
                                       "end_day": NOW_DAY}))
    check(r.passed, f"the numeral audit finds the read's figures in its data "
                    f"({r.reason()[:90]})")
    wrong = f"The index rose {a['price_pct']:.1f} bp."
    check(na.audit(wrong, wt[0]["data"]).n_unmatched >= 1,
          "and refuses a price change quoted in the wrong unit")


def group_g() -> None:
    print(f"\n{LINE}\nG. THE REGISTRY\n{LINE}")
    import yaml                                                 # noqa: PLC0415
    from altdata import catalogue, config as acfg, derived      # noqa: PLC0415
    keys = set()
    for sec in ("decomposition", "r_minus_g", "price_ulc", "allocation"):
        keys |= {v for k, v in (CFG.get(sec) or {}).items() if k.endswith("_key")}
    unreg = sorted(k for k in keys if not (derived.registry_entry(k) or {}).get("units"))
    # 12 since the by-hand audit dropped AAII's three keys (16 Oct 2026).
    check(len(keys) >= 12 and not unreg,
          f"every key read is registered with its units ({len(keys)}; {unreg or 'none'})")
    specs = {s.key: s for s in acfg.FRED_PULL_SERIES}
    want = {"hh_equity_share": ("BOGZ1FL153064486Q", "%", "quarterly"),
            "hh_fin_assets": ("TFAABSHNO", "M", "quarterly"),
            "ppi_fd_core_ex_trade": ("WPSFD49116", "idx", "monthly"),
            "ulc_nfb": ("ULCNFB", "idx", "quarterly")}
    check(all(k in specs and (specs[k].fred_id, specs[k].units, specs[k].freq) == v
              for k, v in want.items())
          and derived.delta_unit_for("fred.hh_equity_share")[0] == "pp",
          "the four FRED series, each with its FRED page's unit; the share moves in pp")
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    # The PPI key is Group B's since the chain-2 stitch: its family is its
    # block's member family, and ruling 7 of 18 Oct holds it to the release
    # family's window, so it carries no long-window override of its own.
    member_fams = {}
    for blk in (reg.get("bulk_imports") or {}).values():
        member_fams.update((blk or {}).get("member_families") or {})
    own = [k for k in want if k != "ppi_fd_core_ex_trade"]
    check(all(f"fred.{k}" in reg["families"] and f"fred.{k}" in reg["long_windows"]
              for k in own)
          and member_fams.get("fred.ppi_fd_core_ex_trade") == "release"
          and "fred.ppi_fd_core_ex_trade" not in reg["long_windows"],
          "each carries a family and a long window; the PPI key the release "
          "family's, under Group B's block (ruling 7, 18 Oct)")
    check("altdata.st_r5_index" in catalogue.commands(), "the catalogue names the command")
    mine = "".join((REPO / p).read_text(encoding="utf-8") for p in
                   ("altdata/st_r5_index.py", "daily_cascade/index_carry_block.py"))
    check(not re.search(r"^\s*(from|import)\s+regime\b", mine, re.M)
          and "st_r5_index" not in (REPO / "regime.py").read_text(encoding="utf-8"),
          "report-only: no regime either way")


def main() -> int:
    print(f"{LINE}\nWhat's carrying the index, and the allocation block\n{LINE}")
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
