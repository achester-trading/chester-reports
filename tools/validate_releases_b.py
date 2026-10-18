#!/usr/bin/env python3
"""
Batch 7 item 48, Group B, and the surprise index (lenses-group-b, 18 Oct 2026):
ST-R6.48d (the PPI lenses 12-14), ST-R6.48e (the GDP lenses 15-20) and ST-R6.48f
(the surprise index). A code gate: fixture series in temporary observation
stores; it never reads the live store, fetches or calls a model. No figure here
is real.

  A. The lens form: two percentiles over the figure's own history, each with its
     n, the family's long window, and the disagreement flag at 30 points and not
     below, by hand; an absent input prints "not stored"
  B. ST-R6.48d: the pipeline's stages and their gap to final demand, the
     PCE-relevant lines (NSA, never annualised), trade services and the core
     less trade, each by hand; an absent component "not stored"
  C. ST-R6.48e: the private core and the contributions with their residual, the
     investment split (structures less data centers by hand), GDI less GDP,
     profits against S&P EPS, income and saving, the GDPNow path and the print
     against it -- with the vintage rule: the first print, never the revision,
     and nothing a cutoff cannot see
  D. ST-R6.48f: the standardisation by hand; a macro release's surprise end to
     end from a fixture consensus; the payroll and FOMC surprises listed gaps;
     earnings standardised per name; no composite; the stored rows' keys;
     engine 4 reads the consensus surprise by key name before the naive one
  E. The display and lens 24: the inflation block's PPI panel, the GDP block in
     the slow layers, no prose word and no chart, no internal id printed; the
     release-day lines for PPI and GDP, and CPI's with the surprise's percentile
  F. The registry, the config, the counts; no by-hand key; no composite touched;
     no fetch and no model call in the new modules
"""

from __future__ import annotations

import ast
import datetime as dt
import math
import re
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gate_tmp import mkdtemp  # noqa: E402

from altdata import derived, observations, releases, releases_b, surprise_index  # noqa: E402

TMP = Path(mkdtemp("gate_releases_b_"))
LINE = "=" * 78
PASSED = FAILED = 0
CUT = "2026-10-16T22:00:00+00:00"
CFG = releases.config()


def check(c: bool, m: str) -> None:
    global PASSED, FAILED
    if c:
        PASSED += 1
        print(f"  PASS  {m}")
    else:
        FAILED += 1
        print(f"  FAIL  {m}")


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


def near(a, b, tol=1e-6) -> bool:
    return a is not None and b is not None and abs(a - b) <= tol


def row(key, day, value, avail=None, instrument=None):
    return {"registry_key": key, "instrument": instrument, "observed_at": str(day),
            "available_at": avail or f"{day}T21:00:00+00:00", "value": float(value),
            "source": "fixture", "availability_kind": "reconstructed"}


def path(key: str, first: str, mms: list[float], base: float = 100.0) -> list[dict]:
    """A monthly index from `first` whose month-on-month changes are `mms`."""
    out, v = [row(key, f"{first[:7]}-01", base)], base
    for i, x in enumerate(mms, 1):
        v *= 1.0 + x / 100.0
        out.append(row(key, f"{releases.shift(first[:7], i)}-01", v))
    return out


def quarters(first: str, values: list[float], key: str) -> list[dict]:
    return [row(key, f"{releases.shift(first[:7], 3 * i)}-01", v)
            for i, v in enumerate(values)]


_N = 0


def store(rows: list[dict]) -> observations.ObservationStore:
    global _N
    _N += 1
    st = observations.ObservationStore(str(TMP / f"s{_N}.sqlite"))
    st.write_many(rows)
    return st


def ann(g_pct: float, periods_per_year: float) -> float:
    return 100.0 * ((1.0 + g_pct / 100.0) ** periods_per_year - 1.0)


# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. THE LENS FORM: TWO PERCENTILES, THE LONG WINDOW, THE DISAGREEMENT")
    late = [f"{releases.shift('2021-11', i)}-01" for i in range(60)]
    early = [f"{releases.shift('2011-11', i)}-01" for i in range(60)]

    def series(n_low: int) -> list[tuple[str, float]]:
        first = [-1.0] * n_low + [100.0] * (60 - n_low)
        return [(d, v) for d, v in zip(early, first)] + \
               [(d, float(i)) for i, d in enumerate(late)]

    ls = releases_b.lens_stat("fred.ppi_stage1", series(24), CUT)
    # By hand: the latest is 59, the five-year window holds the last 60 (0..59),
    # all at or below it -> 100; the 20-year window holds all 120, of which 24
    # (the -1s) and the 60 late values are at or below -> 84/120 = 70.
    check(ls["family"] == "release" and ls["long_window"] == 20
          and ls["pctile_5y"] == 100.0 and ls["pctile_5y_n"] == 60
          and near(ls["pctile_long"], 70.0) and ls["pctile_long_n"] == 120,
          f"the percentiles by hand: five years 100 (n=60), the release family's 20 "
          f"years 70 (n=120) -- got {ls['pctile_5y']} / {ls['pctile_long']}")
    check(ls["disagree"] is True, "a 30-point difference flags the disagreement")
    ls2 = releases_b.lens_stat("fred.ppi_stage1", series(25), CUT)
    check(near(ls2["pctile_long"], 100.0 * 85 / 120, 1e-3) and ls2["disagree"] is False,
          f"29.2 points does not ({ls2['pctile_long']:.4f})")
    none = releases_b.lens_stat("fred.ppi_stage1", [], CUT)
    check(none["value"] is None and none["reasons"]["value"] == "not stored (fred.ppi_stage1)",
          "an absent figure prints 'not stored' with its key")
    one = releases_b.lens_stat("fred.ppi_stage1", [("2026-09-01", 1.0)], CUT)
    check(one["pctile_5y"] is None and one["disagree"] is None
          and "needs both" in one["reasons"]["disagree"],
          "one observation gives no percentile and no disagreement, with the reason")


# ---------------------------------------------------------------------------
def ppi_rows() -> list[dict]:
    R = []
    for key, g in (("fred.ppi_final_demand", 0.2), ("fred.ppi_stage1", 0.5),
                   ("fred.ppi_stage2", 0.4), ("fred.ppi_stage3", 0.3),
                   ("fred.ppi_stage4", 0.25), ("fred.ppi_fd_core_ex_trade", 0.2),
                   ("fred.ppi_hospitals", 0.3), ("fred.ppi_physicians", 0.1),
                   ("fred.ppi_airline_passenger", 0.5)):
        R += path(key, "2024-09-01", [g] * 24)
    R += path("fred.ppi_trade_services", "2024-09-01", [0.0] * 23 + [1.0])
    return R


def group_b() -> None:
    head("B. ST-R6.48d: THE PPI LENSES 12-14, BY HAND")
    with store(ppi_rows()) as st:
        pp = releases_b.ppi_lenses(st, CUT, CFG)
    fd = pp["final_demand"]
    s1 = next(x for x in pp["pipeline"] if x["key"] == "fred.ppi_stage1")
    s4 = next(x for x in pp["pipeline"] if x["key"] == "fred.ppi_stage4")
    check(fd["month"] == "2026-09" and near(fd["yoy_pct"], ann(0.2, 12), 0.01)
          and near(fd["mm_pct"], 0.2, 0.006),
          f"final demand: +0.2% a month is {ann(0.2, 12):.2f}% on the year ({fd['yoy_pct']})")
    check(near(s1["yoy_pct"], ann(0.5, 12), 0.01) and near(s1["ann_3m_pct"], ann(0.5, 12), 0.01)
          and near(s1["gap_to_final_pp"], ann(0.5, 12) - ann(0.2, 12), 0.01),
          f"lens 12: stage 1 at +0.5% a month, {ann(0.5, 12):.2f}% on the year and "
          f"annualised, {ann(0.5, 12) - ann(0.2, 12):.2f} pp above final demand "
          f"({s1['gap_to_final_pp']})")
    check(near(s4["gap_to_final_pp"], ann(0.25, 12) - ann(0.2, 12), 0.01),
          f"stage 4's gap by hand ({s4['gap_to_final_pp']})")
    check(s1["lens"]["pctile_5y_n"] == 13 and s1["lens"]["family"] == "release"
          and "disagree" in s1["lens"],
          "the lens form on the year: 13 year-on-year readings in 25 months, its family "
          "and the disagreement")
    hosp = next(x for x in pp["pce_relevant"] if x["key"] == "fred.ppi_hospitals")
    pm = next(x for x in pp["pce_relevant"] if x["key"] == "fred.ppi_portfolio_mgmt")
    check(hosp["sa"] is False and hosp["ann_3m_pct"] is None
          and near(hosp["yoy_pct"], ann(0.3, 12), 0.01),
          "lens 13: an NSA line on the year by hand, never annualised over three months")
    check(pm["month"] is None and pm["reason"] == "not stored (fred.ppi_portfolio_mgmt)",
          "an absent component: 'not stored'")
    tr, co = pp["trade_services"], pp["core_ex_trade"]
    check(near(tr["mm_pct"], 1.0, 0.006) and near(tr["yoy_pct"], 1.0, 0.006)
          and near(co["yoy_pct"], ann(0.2, 12), 0.01),
          "lens 14: trade services +1.0% in the month and on the year; the core less "
          "trade by hand")
    with store([]) as st:
        empty = releases_b.ppi_lenses(st, CUT, CFG)
    check(all(x.get("reason", "").startswith("not stored")
              for x in [empty["final_demand"], *empty["pipeline"], *empty["pce_relevant"],
                        empty["trade_services"], empty["core_ex_trade"]]),
          "an empty store: every PPI line 'not stored'")


# ---------------------------------------------------------------------------
NOW_Q = [  # (observed quarter, available_at, value) of GDPNow
    ("2026-04-01", "2026-05-01T16:00:00+00:00", 1.5),
    ("2026-04-01", "2026-07-29T16:00:00+00:00", 2.6),
    ("2026-07-01", "2026-07-31T16:00:00+00:00", 2.0),
    ("2026-07-01", "2026-08-15T16:00:00+00:00", 2.5),
    ("2026-07-01", "2026-09-30T16:00:00+00:00", 3.1),
    ("2026-07-01", "2026-10-10T16:00:00+00:00", 3.4),
]


def gdp_rows() -> list[dict]:
    R = []
    fs = [1000.0]
    for g in [1.0] * 7 + [2.0]:
        fs.append(fs[-1] * (1 + g / 100.0))
    R += quarters("2024-04-01", fs, "fred.final_sales_pdp")
    R.append(row("fred.gdp_real_growth", "2026-01-01", 1.0, "2026-04-30T12:30:00+00:00"))
    R.append(row("fred.gdp_real_growth", "2026-04-01", 3.0, "2026-07-30T12:30:00+00:00"))
    R.append(row("fred.gdp_real_growth", "2026-04-01", 3.3, "2026-08-28T12:30:00+00:00"))
    for key, v in (("fred.gdp_contrib_pce", 2.6), ("fred.gdp_contrib_nonres", 0.6),
                   ("fred.gdp_contrib_residential", -0.1),
                   ("fred.gdp_contrib_inventories", -0.4),
                   ("fred.gdp_contrib_net_exports", 0.3),
                   ("fred.gdp_contrib_government", 0.2)):
        R.append(row(key, "2026-04-01", v, "2026-07-30T12:30:00+00:00"))
    for key, vals in (("fred.inv_info_equipment", (600.0, 620.0, 630.0)),
                      ("fred.inv_software", (700.0, 715.0, 720.0)),
                      ("fred.inv_nonres_structures", (850.0, 880.0, 900.0))):
        for d, v in zip(("2025-04-01", "2026-01-01", "2026-04-01"), vals):
            R.append(row(key, d, v))
    for d in ("2025-04-01", "2025-05-01", "2025-06-01"):
        R.append(row("census.vip_data_center", d, 24000.0))
    for d, v in (("2026-04-01", 30000.0), ("2026-05-01", 33000.0), ("2026-06-01", 36000.0)):
        R.append(row("census.vip_data_center", d, v))
    for d, gdi, gdp in (("2025-04-01", 29000.0, 29200.0), ("2026-04-01", 30100.0, 30000.0)):
        R += [row("fred.gdi_nominal", d, gdi), row("fred.gdp_nominal", d, gdp)]
    R += [row("fred.corp_profits_after_tax", "2025-04-01", 2800.0),
          row("fred.corp_profits_after_tax", "2026-04-01", 3000.0),
          row("shiller.sp_earnings", "2025-06-01", 200.0),
          row("shiller.sp_earnings", "2026-06-01", 220.0)]
    R += path("fred.real_disp_income", "2025-08-01", [0.2] * 12)
    R += [row("fred.saving_rate", "2025-08-01", 5.0), row("fred.saving_rate", "2026-08-01", 4.6)]
    R += [row("fred.gdpnow", q, v, a) for q, a, v in NOW_Q]
    return R


def group_c() -> None:
    head("C. ST-R6.48e: THE GDP LENSES 15-20, BY HAND, AND THE VINTAGE RULE")
    with store(gdp_rows()) as st:
        gd = releases_b.gdp_lenses(st, CUT, CFG)
        early = releases_b.gdp_lenses(st, "2026-07-29T20:00:00+00:00", CFG)
    core = gd["core"]
    fs = core["final_sales"]
    check(near(fs["qq_ann_pct"], ann(2.0, 4), 0.006)
          and near(fs["yoy_pct"], 100 * (1.01 ** 3 * 1.02 - 1), 0.006),
          f"lens 15: final sales up 2% in the quarter is {ann(2.0, 4):.3f}% annualised; "
          f"{100 * (1.01 ** 3 * 1.02 - 1):.3f}% on the year ({fs['qq_ann_pct']}, "
          f"{fs['yoy_pct']})")
    check(core["quarter"] == "2026-04" and core["real_growth"]["value"] == 3.3
          and near(core["sum_pp"], 3.2) and near(core["residual_pp"], 0.1),
          f"the six contributions sum to 3.2 pp against the revised 3.3%; residual 0.1 "
          f"({core['sum_pp']}, {core['residual_pp']})")
    inv = gd["investment"]
    ai, sx = inv["ai_related"], inv["structures"]
    check(near(ai["yoy_pct"], 100 * (1350 / 1300 - 1), 0.006)
          and near(ai["qq_ann_pct"], 100 * ((1350 / 1335) ** 4 - 1), 0.006),
          f"lens 16: AI-related (equipment and software) {100 * (1350 / 1300 - 1):.3f}% on "
          f"the year, by hand")
    check(near(sx["dc_bn"], 33.0) and near(sx["ex_dc_bn"], 867.0)
          and near(sx["ex_dc_yoy_pct"], 100 * (867 / 826 - 1), 0.006),
          f"structures less data centers: 900 less the quarter's mean 33,000m (33.0bn) "
          f"= 867, against 826 a year before: {100 * (867 / 826 - 1):.3f}%")
    gg = gd["gdi_gap"]
    hand = 100 * 100 / 30000 - 100 * (-200) / 29200
    check(near(gg["gap_pct_gdp"], 100 * 100 / 30000, 0.006) and near(gg["change_4q_pp"], hand, 0.006),
          f"lens 17: GDI less GDP {100 * 100 / 30000:.3f}% of GDP, {hand:.3f} pp on four "
          f"quarters")
    pf = gd["profits"]
    check(near(pf["profits_yoy_pct"], 100 * (3000 / 2800 - 1), 0.006)
          and near(pf["eps_yoy_pct"], 10.0) and pf["eps_month"] == "2026-06"
          and near(pf["divergence_pp"], 100 * (3000 / 2800 - 1) - 10.0, 0.006),
          "lens 18: NIPA profits +7.14% against S&P EPS +10.0% at the quarter's last "
          "month, a gap of -2.86 pp")
    inc = gd["income"]
    check(near(inc["disp_income"]["yoy_pct"], ann(0.2, 12), 0.01)
          and near(inc["saving_rate"]["change_12m_pp"], -0.4)
          and inc["ex_transfers"]["reason"] == "not stored (fred.real_income_ex_transfers)"
          and "consumption-by-income" in inc["k_shape_gap"],
          "lens 19: real disposable income by hand, the saving rate's -0.4 pp, income ex "
          "transfers 'not stored', the K-shape panel a listed gap")
    nc = gd["nowcast"]
    check(nc["quarter"] == "2026-07" and nc["updates"] == 4 and nc["first"] == 2.0
          and nc["latest"] == 3.4 and near(nc["change_pp"], 1.4),
          f"lens 20: GDPNow's four updates for Q3, 2.0% to 3.4% (+1.4 pp)")
    pr = nc["print"]
    check(pr and pr["quarter"] == "2026-04" and pr["first_print"] == 3.0
          and pr["last_nowcast"] == 2.6 and near(pr["miss_pp"], 0.4),
          "the print read against the nowcast: Q2's FIRST print 3.0% (not the 3.3% "
          "revision) less GDPNow's last before it, 2.6%: +0.4 pp")
    check("New York Fed" in nc["nyfed_gap"], "the NY Fed nowcast is a listed gap")
    ne = early["nowcast"]
    check(ne["quarter"] == "2026-04" and ne["updates"] == 2 and ne["print"] is None
          and "no quarter" in ne["print_reason"]
          and early["core"]["real_growth"]["value"] == 1.0,
          "the vintage rule: at 29 Jul neither Q3's nowcast nor Q2's print exists; Q1's "
          "print is the latest growth")
    with store([]) as st:
        none = releases_b.gdp_lenses(st, CUT, CFG)
    check(none["core"]["final_sales"]["reason"] == "not stored (fred.final_sales_pdp)"
          and none["nowcast"]["reason"] == "not stored (fred.gdpnow)"
          and "not stored" in none["gdi_gap"]["reason"],
          "an empty store: every GDP lens 'not stored'")
    with store([r for r in gdp_rows() if r["registry_key"] != "census.vip_data_center"]) as st:
        nodc = releases_b.gdp_lenses(st, CUT, CFG)["investment"]["structures"]
    check(nodc["ex_dc_reason"] == "not stored (census.vip_data_center)"
          and nodc["level_bn"] == 900.0,
          "without the Census data-center series: structures in full, 'ex data centers' "
          "not stored")


# ---------------------------------------------------------------------------
CPI_MM = [0.3, 0.1, 0.2, 0.4, 0.2, 0.3, 0.1, 0.2, 0.5]


def cpi_consensus_rows() -> list[dict]:
    R = path("fred.cpi", "2025-12-01", CPI_MM)
    for i in range(1, 10):
        d = f"{releases.shift('2025-12', i)}-01"
        R.append(row("consensus.cpi", d, 0.2, f"{d}T12:00:00+00:00"))
    return R


def group_d() -> None:
    head("D. ST-R6.48f: THE SURPRISE INDEX")
    prior = [0.1, -0.1] * 4
    z = surprise_index.standardise(prior, 0.2, 8, 40)
    check(near(z["z"], 0.2 / math.sqrt(8 * 0.01 / 7), 1e-4) and z["pctile"] == 100.0
          and z["n_prior"] == 8,
          f"by hand: 0.2 over the standard deviation of eight +/-0.1 surprises "
          f"(sqrt(0.08/7)) is {0.2 / math.sqrt(8 * 0.01 / 7):.4f}; the 100th percentile")
    short = surprise_index.standardise(prior[:7], 0.2, 8, 40)
    check(short["z"] is None and "8 needed" in short["reason"],
          "seven earlier surprises: not standardised, with the reason")
    with store(cpi_consensus_rows()) as st:
        s = surprise_index.macro_series(st, CFG["surprise_index"]["macro"][0], CUT, CFG)
        last = surprise_index.latest(st, "cpi", CUT, CFG)
        pay = surprise_index.latest(st, "payrolls", CUT, CFG)
        fomc = surprise_index.latest(st, "fomc", CUT, CFG)
        idx = surprise_index.index(st, CUT, CFG)
        stored = surprise_index.rows(st, CUT, CFG)
    hand = [m - 0.2 for m in CPI_MM]
    check(s["state"] == "read" and len(s["rows"]) == 9
          and all(near(x["surprise"], h, 1e-6) for x, h in zip(s["rows"], hand)),
          f"CPI end to end: nine surprises, each the first print's month on month less "
          f"the 0.2 consensus ({[round(x['surprise'], 3) for x in s['rows']]})")
    sd = math.sqrt(0.075 / 7)       # the eight earlier surprises' deviations, by hand
    check(near(last["surprise"], 0.3, 1e-6) and near(last["z"], 0.3 / sd, 0.006)
          and last["pctile"] == 100.0 and last["n_prior"] == 8,
          f"the newest: +0.3 pp, z {0.3 / sd:.4f} against its own eight earlier "
          f"surprises, the 100th percentile ({last['z']})")
    check(pay["state"] == "no consensus" and "ruling 5" in pay["reason"]
          and fomc["state"] == "no consensus",
          "payrolls and FOMC: no consensus stored, listed gaps under ruling 5")
    check(idx["composite"] is None and "defines no composite" in idx["composite_reason"],
          "no composite: the order defines none")
    keys = {r["registry_key"] for r in stored}
    check(keys == {"calc.consensus_surprise.cpi", "calc.consensus_surprise_z.cpi"}
          and all(derived.registry_entry(k) for k in keys),
          f"the stored rows: CPI's surprise and its z, both registered ({sorted(keys)})")
    vals = [5, -3, 2, 4, -1, 3, 0, 6, 10]
    er = [row("calc.earnings_surprise_pct", f"{releases.shift('2024-07', 3 * i)}-15", v,
              instrument="AAPL") for i, v in enumerate(vals)]
    with store(er) as st:
        e = surprise_index.earnings_series(st, CUT, CFG)
        er_rows = surprise_index.rows(st, CUT, CFG)
    check(near(e["AAPL"][-1]["z"], 10 / math.sqrt(68 / 7), 1e-4)
          and e["AAPL"][-2]["z"] is None,
          f"earnings, per name: AAPL's +10% over the sd of its eight earlier surprises "
          f"(sqrt(68/7)) is {10 / math.sqrt(68 / 7):.4f}; the eighth has seven before it")
    check({r["registry_key"] for r in er_rows} == {surprise_index.EARNINGS_Z}
          and all(r["instrument"] == "AAPL" for r in er_rows) and len(er_rows) == 1,
          "its stored row: one z under the name, only where eight came before")
    # Engine 4 reads the consensus surprise by key name, before the naive one
    from alpha import event_rates
    ev = {"consensus_surprise": "calc.consensus_surprise.cpi",
          "surprise": "calc.surprise_vs_naive.cpi", "surprise_kind": "naive: ..."}
    with store([row("calc.consensus_surprise.cpi", "2026-09-01", 0.3),
                row("calc.surprise_vs_naive.cpi", "2026-09-01", 0.1)]) as st:
        ser, kind = event_rates.surprise_series(st, ev)
    with store([row("calc.surprise_vs_naive.cpi", "2026-09-01", 0.1)]) as st:
        ser2, kind2 = event_rates.surprise_series(st, ev)
    check(ser.key == "calc.consensus_surprise.cpi" and kind.startswith("consensus")
          and ser2.key == "calc.surprise_vs_naive.cpi" and kind2.startswith("naive"),
          "engine 4 reads calc.consensus_surprise.<id> by name where stored, else the "
          "naive surprise under its own label")
    import yaml
    acfg = yaml.safe_load((REPO / "config" / "alpha_events.yaml").read_text(encoding="utf-8"))
    check({k: v.get("consensus_surprise") for k, v in acfg["events"].items()} ==
          {"cpi": "calc.consensus_surprise.cpi", "payrolls": "calc.consensus_surprise.payrolls",
           "fomc": "calc.consensus_surprise.fomc"},
          "engine 4's three events name their consensus keys")


# ---------------------------------------------------------------------------
ID_RE = re.compile(r"\b(?:fred|calc|census|shiller|consensus)\.[a-z0-9_]+")


def group_e() -> None:
    head("E. THE DISPLAY AND LENS 24")
    from daily_cascade import gdp_block, inflation_block as ib, stack
    with store(ppi_rows()) as st:
        subs = ib.subsections(st, CUT)
    ppi = next((s for s in subs if s["title"] == ib.TITLE_PPI), None)
    check(ppi is not None and len(ppi["table"]["rows"]) == 10
          and ppi["table"]["columns"][-3:] == releases_b.LENS_COLUMNS
          and any("Portfolio management and investment advice: not stored" in x
                  for x in ppi["lines"]),
          "the inflation block prints the PPI table (ten lines read), each row in the lens "
          "form, and the absent line 'not stored' by name")
    with store(gdp_rows()) as st:
        gsubs = gdp_block.subsections(st, CUT)
    check(len(gsubs) == 2 and all(g.get("table") for g in gsubs)
          and all(g["table"]["columns"][-3:] == releases_b.LENS_COLUMNS for g in gsubs),
          "the GDP block: two tables in the slow layers, every row in the lens form")
    body = " ".join(" ".join(s.get("lines") or []) + (s.get("table_note") or "")
                    for s in [ppi, *gsubs])
    check(not ID_RE.search(body), "no internal id in any printed line or note"
          + (f" ({ID_RE.findall(body)[:3]})" if ID_RE.search(body) else ""))
    base = {"id": "slow", "claim": "x", "paragraphs": ["One two."], "subsections": []}
    more = dict(base, subsections=[ppi, *gsubs])
    check(stack.section_words(base) == stack.section_words(more)
          and all(not s.get("charts") and not s.get("paragraph") and
                  s.get("paragraph_wanted") is False for s in [ppi, *gsubs]),
          "no prose word and no chart: the Monthly's 10,000 words and 12 charts are "
          "untouched, so the panels displace nothing")
    src = (REPO / "monthly_macro" / "stack.py").read_text(encoding="utf-8")
    check("gdp_block.subsections(st, now)" in src,
          "the Monthly's slow layers carry the GDP block")
    with store([]) as st:
        check(ib.ppi_panel(st, CUT) is None,
              "with no PPI stored the slot prints nothing")
    # Lens 24, on fixture calendars
    on = "2026-10-15T12:30:00+00:00"
    cal = [dict(x, available_at=on) if x["observed_at"] == "2026-09-01" else x
           for x in ppi_rows()]
    with store(cal) as st:
        day = releases.release_day_lines(st, "2026-10-15T20:45:00+00:00", CFG)
    p = next((x for x in day if x["release"] == "ppi"), None)
    check(p is not None and p["line"].startswith("PPI for Sep 2026: final demand +0.2% on "
                                                 "the month")
          and "trade services +1.0%" in p["line"] and "(surprise: no consensus)" in p["line"],
          f"PPI day: the line names what moved the print, 'no consensus' for the "
          f"surprise ({p['line'] if p else None})")
    with store(gdp_rows()) as st:
        gl = releases.release_day_lines(st, "2026-07-30T20:45:00+00:00", CFG)
        nxt = releases.release_day_lines(st, "2026-07-31T20:45:00+00:00", CFG)
    g = next((x for x in gl if x["release"] == "gdp"), None)
    check(g is not None and g["line"].startswith("GDP for Q2 2026: +3.0% annualised")
          and "against GDPNow's last +2.6%, +0.4 pp" in g["line"]
          and not [x for x in nxt if x["release"] == "gdp"],
          f"GDP day: the first print, its contributions, read against GDPNow; nothing "
          f"the next day ({g['line'] if g else None})")
    with store(cpi_consensus_rows()) as st:
        cl = releases.release_day_lines(st, "2026-09-01T22:00:00+00:00", CFG)
    c = next((x for x in cl if x["release"] == "cpi"), None)
    want = f"surprise: +0.30 % m/m against consensus, {derived._ord(100.0)} percentile of its surprises (n=8)"
    check(c is not None and want in c["line"],
          f"CPI day with a consensus stored: the surprise with its percentile ({c['line'] if c else None})")


# ---------------------------------------------------------------------------
NEW_MODULES = ("altdata/releases_b.py", "altdata/surprise_index.py",
               "daily_cascade/gdp_block.py")
FORBIDDEN = ("requests", "urllib", "http", "anthropic", "socket", "subprocess",
             "altdata.model_meter", "altdata.sources")


def group_f() -> None:
    head("F. THE REGISTRY, THE CONFIG, THE COUNTS, NOTHING ELSE TOUCHED")
    from altdata import config
    keys = [f"fred.{s.key}" for s in config.FRED_GROUP_B_SERIES]
    pulled = {s.fred_id for s in config.FRED_PULL_SERIES}
    check(len(keys) == 29 and all(s.fred_id in pulled for s in config.FRED_GROUP_B_SERIES)
          and len(pulled) == len(config.FRED_PULL_SERIES),
          "29 Group B series on the FRED pull, no id twice")
    fam = [derived.family_of(k)[0] for k in keys]
    check(all(f == "release" for f in fam),
          "every one registered, family release (the registry's fred_group_b block)")
    units = {k: derived.registry_entry(k).get("units") for k in keys}
    check(units["fred.saving_rate"] == "percent_share"
          and units["fred.gdp_contrib_pce"] == "percent_return"
          and units["fred.final_sales_pdp"] == "B" and units["fred.ppi_stage1"] == "idx",
          "their units: shares and growth rates split (AUD-3a), billions, indexes")
    new_calc = [f"calc.consensus_surprise.{x['id']}" for x in CFG["surprise_index"]["macro"]]
    new_calc += [f"calc.consensus_surprise_z.{x['id']}" for x in CFG["surprise_index"]["macro"]]
    new_calc.append(surprise_index.EARNINGS_Z)
    ents = [derived.registry_entry(k) for k in new_calc]
    check(all(ents) and all(e.get("source") == "calc" for e in ents),
          f"the surprise index's {len(new_calc)} keys registered, every one calculated "
          f"(source calc): no by-hand key")
    check(all(derived.registry_entry(k).get("source") == "fred" for k in keys),
          "and the 29 series are FRED's: no by-hand key appears")
    ms = (REPO / "config" / "market_state.yaml").read_text(encoding="utf-8")
    composite_cfgs = [ms] + [(REPO / "config" / n).read_text(encoding="utf-8")
                             for n in ("pillars.yaml", "macro_6e.yaml")
                             if (REPO / "config" / n).is_file()]
    hits = [k for k in keys + new_calc if any(k in t for t in composite_cfgs)]
    check(not hits, "no Group B or surprise key enters a composite, the market state or "
                    "a pillar (no composite weight changes)" + (f": {hits}" if hits else ""))
    for mod in NEW_MODULES:
        tree = ast.parse((REPO / mod).read_text(encoding="utf-8"))
        imps = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                imps |= {a.name for a in n.names}
            elif isinstance(n, ast.ImportFrom):
                base = ("altdata." if n.level and mod.startswith("altdata") else "")
                imps.add(base + (n.module or ""))
                imps |= {f"{base}{n.module}.{a.name}" if n.module else f"{base}{a.name}"
                         for a in n.names}
        bad = [i for i in imps if any(i == f or i.startswith(f + ".") for f in FORBIDDEN)]
        check(not bad, f"{mod}: no network, model or source import" + (f" ({bad})" if bad else ""))
    claude = (REPO / "CLAUDE.md").read_text(encoding="utf-8")
    check(f"{len(config.FRED_GROUP_B_SERIES)} in FRED_GROUP_B_SERIES" in claude
          and f"FRED_PULL_SERIES, {len(config.FRED_PULL_SERIES)}," in claude,
          "CLAUDE.md prints the two counts the code has")
    import yaml
    cat = yaml.safe_load((REPO / "config" / "catalogue_commands.yaml").read_text(
        encoding="utf-8"))["commands"]
    check("altdata.releases_b" in cat and "altdata.surprise_index" in cat,
          "the catalogue names both new commands")
    rel = {r["id"] for r in CFG["releases"]}
    check({"ppi", "gdp"} <= rel, "lens 24's releases include PPI and GDP")
    mk = (REPO / "Makefile").read_text(encoding="utf-8")
    check("tools/validate_releases_b.py" in mk, "the Makefile runs this gate")


def main() -> int:
    group_a()
    group_b()
    group_c()
    group_d()
    group_e()
    group_f()
    print(f"\n{PASSED} passed, {FAILED} failed")
    print("VALIDATION PASSED" if not FAILED else "VALIDATION FAILED")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
