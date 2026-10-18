#!/usr/bin/env python3
"""
6e, the rest (macro completeness; 16 Oct 2026) -- what has no home in
tools/validate_lenses.py, which holds the lenses themselves (groups H-L). A code
gate: fixture series in temporary observation stores; it never reads the live
store, fetches or calls a model. No figure here is real.

  A. S3a-S3c by hand: path divergence, the policy spreads and differentials, the
     real policy rate, the twelve-month deficit against GDP, interest against
     receipts, the effective rate, R less G on both bases, debt against GDP by
     sector, the TGA's 13-week range and volatility; the core CPI-PCE gap and
     realized ten-year inflation against the breakeven
  B. The CPI lead composite: each horizon by hand from its stated lags, the
     covered basket share, a horizon no lag reaches absent with its reason, the
     kill test untested / killed / passed, the roll-off calendar by hand
  C. The path-divergence flag at three sigma and not below
  D. The inflation block: its panels, the two reserved slots (Batch 7 items 46
     and 48) print nothing; "stated lags, unvalidated"
  E. The budgets hold: the Weekly's and the close's lens tables and the inflation
     block add no prose word and no chart
  F. The registry, the config, the hooks, no fetch
"""

from __future__ import annotations

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

from altdata import cpi_lead, derived, macro_6e, observations  # noqa: E402

TMP = Path(mkdtemp("gate_6e_rest_"))
LINE = "=" * 78
PASSED = FAILED = 0
CUT = "2026-10-16T22:00:00+00:00"


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


def row(key, day, value):
    return {"registry_key": key, "instrument": None, "observed_at": str(day),
            "available_at": f"{day}T21:00:00+00:00", "value": float(value),
            "source": "fixture", "availability_kind": "reconstructed"}


def months(first: dt.date, n: int) -> list[dt.date]:
    return [dt.date(first.year + (first.month - 1 + i) // 12, (first.month - 1 + i) % 12 + 1, 1)
            for i in range(n)]


def store(name: str, rows: list[dict]) -> observations.ObservationStore:
    st = observations.ObservationStore(str(TMP / f"{name}.sqlite"))
    st.write_many(rows)
    return st


def near(a, b, tol=1e-6) -> bool:
    return a is not None and b is not None and abs(a - b) <= tol


def last(rows: list[dict], key: str):
    xs = sorted((r["observed_at"], r["value"]) for r in rows if r["registry_key"] == key)
    return xs[-1] if xs else (None, None)


def build_rows() -> list[dict]:
    R = []
    d = "2026-10-15"
    R += [row("fred.usd_jpy", d, 150.0), row("yfinance.mkt_usdjpy", d, 150.3),
          row("fred.yield_2y", d, 3.90), row("fred.effr", d, 3.88),
          row("fred.sofr", d, 3.95), row("fred.iorb", d, 3.90),
          row("fred.ccc_oas", d, 9.50), row("fred.bb_oas", d, 2.00),
          row("fred.estr", d, 2.44), row("fred.sonia", d, 3.73),
          row("fred.effr", "2026-08-31", 4.00)]
    R += [row("fred.core_pce", "2025-09-01", 100.0), row("fred.core_pce", "2026-09-01", 103.0),
          row("fred.core_cpi", "2025-09-01", 100.0), row("fred.core_cpi", "2026-09-01", 102.4)]
    for m in months(dt.date(2025, 10, 1), 12):
        R.append(row("fred.mts_deficit", m, -100_000.0))
    R += [row("fred.gdp_nominal", "2025-04-01", 30_000.0 / 1.05),
          row("fred.gdp_nominal", "2026-04-01", 30_000.0),
          row("fred.fed_interest_payments", "2026-04-01", 1_200.0),
          row("fred.fed_current_receipts", "2026-04-01", 6_000.0),
          row("fred.fed_debt_total", "2026-04-01", 40_000_000.0),
          row("fred.nonfin_corp_debt", "2026-04-01", 15_000_000.0),
          row("fred.total_hh_debt", "2026-04-01", 21_000_000.0),
          row("fred.yield_10y", "2026-03-31", 4.50)]
    tga = [800_000, 820_000, 790_000, 850_000, 900_000, 870_000, 760_000, 780_000,
           810_000, 840_000, 830_000, 805_000, 815_000]
    w0 = dt.date(2026, 7, 15)
    for i, v in enumerate(tga):
        R.append(row("fred.tga", w0 + dt.timedelta(days=7 * i), v))
    # CPI rising 3% a year for ten years and nine months; the breakeven at the
    # month's end.
    for i, m in enumerate(months(dt.date(2016, 1, 1), 129)):
        R.append(row("fred.cpi", m, 100.0 * 1.03 ** (i / 12)))
    R.append(row("fred.breakeven_10y", "2026-09-30", 2.30))
    # The composite's leads: import prices ex fuel rising exactly 2% a year; the
    # wage tracker at 4.5%.
    for i, m in enumerate(months(dt.date(2025, 1, 1), 21)):
        R.append(row("fred.import_prices_ex_fuel", m, 100.0 * 1.02 ** (i / 12)))
        R.append(row("fred.atl_wage_tracker", m, 4.5))
    # The shelter lead (6e-releases, ruling (a)3): Zillow's rent rising exactly
    # 4% a year, so its year over year is 4.00 from Jan 2025.
    for i, m in enumerate(months(dt.date(2024, 1, 1), 33)):
        R.append(row("zillow.zori_us", m, 2000.0 * 1.04 ** (i / 12)))
    return R


def group_a(rows: list[dict]) -> None:
    head("A. S3a-S3c BY HAND")
    v = {k: last(rows, k)[1] for k in macro_6e.KEYS}
    check(near(v["calc.path_divergence_usdjpy"], 0.2),
          f"S3a: USD/JPY close 150.30 against the noon fixing 150.00 is +0.20% "
          f"({v['calc.path_divergence_usdjpy']})")
    want = {"calc.policy_2y_minus_effr_bp": 2.0, "calc.sofr_iorb_bp": 5.0,
            "calc.sofr_effr_bp": 7.0, "calc.ccc_bb_oas_bp": 750.0,
            "calc.policy_diff_us_ea_bp": 144.0, "calc.policy_diff_us_uk_bp": 15.0}
    bad = {k: v[k] for k, w in want.items() if not near(v[k], w, 1e-4)}
    check(not bad, f"S3b in bp: 2y less EFFR +2, SOFR less IORB +5, SOFR less EFFR +7, "
                   f"CCC less BB 750, EFFR less EURSTR 144, EFFR less SONIA 15 {bad or ''}")
    check(near(v["calc.real_policy_rate"], 1.0),
          f"S3b: EFFR 4.00 known at 1 Sep less core PCE 3.0% is a 1.00% real policy rate "
          f"({v['calc.real_policy_rate']})")
    check(near(v["calc.deficit_ttm_pct_gdp"], -4.0),
          f"S3c: twelve months of -$100bn (millions) against $30tn GDP (billions, "
          f"converted) is -4.00% ({v['calc.deficit_ttm_pct_gdp']})")
    check(near(v["calc.interest_to_receipts"], 20.0) and near(v["calc.federal_effective_rate"], 3.0),
          f"S3c: interest 1,200 against receipts 6,000 is 20%; 1,200bn x 1000 over "
          f"$40tn (millions) is a 3.00% effective rate")
    check(near(v["calc.r_minus_g_marginal"], -0.5) and near(v["calc.r_minus_g_average"], -2.0),
          f"S3c R less G on both bases against 5.0% nominal growth: marginal (10-year "
          f"4.50) -0.50, average (effective 3.00) -2.00 ({v['calc.r_minus_g_marginal']}, "
          f"{v['calc.r_minus_g_average']})")
    check(near(v["calc.fed_debt_total_pct_gdp"], 400.0 / 3.0)
          and near(v["calc.nonfin_corp_debt_pct_gdp"], 50.0)
          and near(v["calc.household_debt_pct_gdp"], 70.0),
          "S3c debt against GDP by sector: federal 133.3%, corporate 50%, households 70% "
          "(every leg in millions)")
    tga = [800_000, 820_000, 790_000, 850_000, 900_000, 870_000, 760_000, 780_000,
           810_000, 840_000, 830_000, 805_000, 815_000]
    ch = [(b - a) * 1e6 for a, b in zip(tga, tga[1:])]
    check(near(v["calc.tga_range_13w"], 140_000 * 1e6, 1e-3)
          and near(v["calc.tga_vol_13w"], statistics.stdev(ch), 1e-3),
          "S3c: the TGA's 13-week range ($140bn) and the deviation of its weekly "
          "changes, in dollars")
    check(near(v["calc.core_cpi_pce_gap"], -0.6),
          f"the gap: core CPI 2.4% less core PCE 3.0% is -0.60 pp "
          f"({v['calc.core_cpi_pce_gap']})")
    check(near(v["calc.realized_10y_vs_expected_10y"], 0.7),
          f"the conditioner: ten years of 3% CPI less a 2.30 breakeven is +0.70 pp "
          f"({v['calc.realized_10y_vs_expected_10y']})")
    rr = [r for r in rows if r["registry_key"] == "calc.deficit_ttm_pct_gdp"]
    check(rr and str(rr[-1]["available_at"]).startswith("2026-09-01T21:00:00")
          and all(r["source"] == "calc" for r in rows),
          "every row's availability is its latest input's, source calc")


def group_b(rows: list[dict]) -> None:
    head("B. THE CPI LEAD COMPOSITE")
    cfg = macro_6e.config()["cpi_lead"]
    w = {c["name"]: c["weight"] for c in cfg["components"]}
    assert abs(sum(w.values()) - 1.0) < 1e-9, w
    cov = w["core goods"] + w["services ex shelter"] + w["shelter"]
    want = (w["core goods"] * 2.0 + w["services ex shelter"] * (4.5 - 1.5)
            + w["shelter"] * 4.0) / cov
    l3, l6 = last(rows, "calc.cpi_lead_3m"), last(rows, "calc.cpi_lead_6m")
    l9 = last(rows, "calc.cpi_lead_9m")
    check(near(l6[1], want, 1e-3) and near(l3[1], want, 1e-3) and l6[0] == "2026-09-01"
          and near(l9[1], 4.0, 1e-3) and l9[0] == "2026-09-01",
          f"3 and 6 months: (core goods x 2.0 + services ex shelter x (4.5 - 1.5) + "
          f"shelter x 4.0) over their weights = {want:.3f}; 9 months: shelter alone "
          f"(its 12-month lag is the only one that reaches it), 4.00")
    with store("lead", rows) as st:
        r = cpi_lead.read(st, CUT, cfg)
    h = {x["horizon"]: x for x in r["horizons"]}
    check(near(h[6]["covered_share"], 0.8) and near(h[9]["covered_share"], 0.355)
          and r["status"] == "unvalidated",
          f"each horizon states its covered share: 80% at 6 months now shelter's lead "
          f"is stored (44.5% before, 6e-rest), 35.5% at 9; status unvalidated")
    miss = {m["name"] for m in h[6]["missing"]}
    check(miss == {"food", "energy"},
          f"the shelter gap is closed (ruling (a)3): food and energy are named as not "
          f"covered, with reasons ({sorted(miss)})")
    with store("lead_no_zillow", [x for x in rows if not x["registry_key"].startswith(
            ("zillow.", "calc.cpi_lead"))]) as st:
        r0 = cpi_lead.read(st, CUT, cfg)
    h0 = {x["horizon"]: x for x in r0["horizons"]}
    check(h0[9]["value"] is None and "shelter" in h0[9]["reason"]
          and "stated lag reaches" not in h0[9]["reason"],
          f"without Zillow stored, the 9-month horizon names the unstored lead, not a "
          f"lag ({h0[9]['reason']})")
    check(r["kill_test"]["state"] == "untested" and "needed" in r["kill_test"]["reason"],
          f"under 60 months the kill test says untested ({r['kill_test']['reason']})")
    # Kill test on its own fixture: a composite that tracks CPI six months on, and
    # one that does not.
    ms = months(dt.date(2015, 1, 1), 120)
    cpi = [100.0]
    for i in range(1, len(ms)):
        cpi.append(cpi[-1] * (1 + (0.002 + 0.002 * math.sin(i / 6))))
    good, bad = [], []
    for i, m in enumerate(ms):
        good.append(row("fred.cpi", m, cpi[i]))
        if 6 <= i < len(ms) - 6:
            fwd = 100.0 * (cpi[i + 6] / cpi[i - 6] - 1.0)
            good.append(row("calc.cpi_lead_6m", m, fwd))
    bad = [x for x in good if x["registry_key"] == "fred.cpi"] + [
        row("calc.cpi_lead_6m", m, 2.0 + (-1) ** i * 0.5) for i, m in enumerate(ms[6:-6], 6)]
    with store("kill_good", good) as st:
        kg = cpi_lead.kill_test(st, CUT, cfg)
    with store("kill_bad", bad) as st:
        kb = cpi_lead.kill_test(st, CUT, cfg)
        withheld = cpi_lead.read(st, CUT, cfg)
    check(kg["state"] == "passed" and kg["corr"] > 0.99 and kb["state"] == "killed"
          and withheld["withheld"],
          f"the kill test: a composite that tracks realized CPI passes (r={kg.get('corr')}); "
          f"one that does not is killed and withheld (r={kb.get('corr', float('nan')):.2f})")
    with store("rolloff", rows) as st:
        ro = cpi_lead.rolloff(st, CUT, cfg)
    p = {(x["path_pct"], x["months"]): x["trailing_10y"] for x in ro["paths"]}
    by_hand = round(100 * (((1.025) * 1.03 ** 9) ** 0.1 - 1), 3)
    check(near(ro["now"], 3.0, 1e-3) and near(p[(3.0, 12)], 3.0, 1e-3)
          and near(p[(2.5, 12)], by_hand, 1e-3) and len(p) == 6,
          f"the roll-off calendar: 3.00% now; 3% for a year keeps it 3.00%; 2.5% for a "
          f"year makes it {by_hand}% (by hand); six paths")


def group_c() -> None:
    head("C. PATH DIVERGENCE: THE FLAG AT THREE SIGMA")
    days = [dt.date(2025, 10, 1) + dt.timedelta(days=i) for i in range(200)]
    hist = [0.01 if i % 2 else -0.01 for i in range(199)]

    def flag(lastv: float) -> dict:
        rows = [row("calc.path_divergence_usdjpy", d, x) for d, x in zip(days, hist + [lastv])]
        with store(f"pd_{lastv}", rows) as st:
            return macro_6e.path_divergence_flag(st, CUT)[0]
    mu = statistics.fmean(hist[-200:])
    sd = statistics.pstdev([x for d, x in zip(days, hist)
                            if d >= days[-1] - dt.timedelta(days=365)])
    at, below = flag(mu + 3.0 * sd + 1e-9), flag(mu + 2.99 * sd)
    check(at["flag"] is True and below["flag"] is False,
          f"flagged at three standard deviations of its trailing year (z {at['z']}), "
          f"not at {below['z']}")
    short = macro_6e.path_divergence_flag(store("pd_short", [row("calc.path_divergence_usdjpy", d, 0.0)
                                                             for d in days[:50]]), CUT)[0]
    check(short["flag"] is None and "needed" in short["reason"],
          f"under 120 days, no flag and its reason ({short['reason']})")


def group_d(rows: list[dict]) -> None:
    head("D. THE INFLATION BLOCK: ITS PANELS, BATCH 7'S FILLED, GROUP B'S SLOT")
    from daily_cascade import inflation_block as ib
    names = [n for n, _ in ib.PANELS]
    check(names == ["lead", "gap", "decomposition", "cpi_lenses", "ppi"]
          and dict(ib.PANELS)["decomposition"] is not None
          and dict(ib.PANELS)["ppi"] is ib.ppi_panel,
          "five panels in order: item 46's decomposition and item 48's CPI lenses "
          "filled (6e-releases); Group B's PPI slot filled (lenses-group-b), "
          "printing nothing while no PPI series is stored; the labour lenses left "
          "for their own section")
    feat = rows + [row("calc.core_cpi_pce_gap", m, 0.3 - 0.1 * i)
                   for i, m in enumerate(months(dt.date(2026, 1, 1), 9))]
    with store("infl", feat) as st:
        subs = ib.subsections(st, CUT)
    t = [s["title"] for s in subs]
    check(t == [ib.TITLE_LEAD, ib.TITLE_GAP, ib.TITLE_DECOMP, ib.TITLE_LENSES],
          f"the block prints the lead table, the gap line, the decomposition and the "
          f"CPI lenses, nothing for the empty slot ({t})")
    lead = subs[0]
    nine = next(r for r in lead["table"]["rows"] if r[0] == "9 months")
    check("unvalidated" in lead["table_note"] and nine[1] == "4.00%"
          and any("Kill test not yet run" in x for x in lead["lines"]),
          "'stated lags, unvalidated'; the 9-month row read from shelter's lead alone; "
          "the kill test's state")
    check("sign has flipped" in subs[1]["lines"][0],
          "the gap's line says when the sign has flipped")
    body = " ".join(" ".join(s.get("lines") or []) + (s.get("table_note") or "") for s in subs)
    check(not re.search(r"\b(?:fred|calc|cboe|yfinance)\.[a-z0-9_]+", body)
          and not re.search(r"\d{4}-\d{2}-\d{2}", body),
          "no internal id and no ISO date outside a table")


def group_e(rows: list[dict]) -> None:
    head("E. THE BUDGETS HOLD")
    from daily_cascade import inflation_block, lens_cells, stack
    feat = rows + [row("fred.yield_10y", dt.date(2026, 1, 1) + dt.timedelta(days=i), 4.0 + i * 0.001)
                   for i in range(280)]
    with store("budget", feat) as st:
        lt = lens_cells.lens_table(st, CUT, [("fred.yield_10y", "10-year"),
                                             ("fred.cpi", "CPI")])
        ib = inflation_block.subsections(st, CUT)
    base = {"id": "plumbing", "claim": "Rates rose.", "paragraphs": ["One two three."],
            "subsections": []}
    more = dict(base, subsections=[lt] + ib)
    check(stack.section_words(base) == stack.section_words(more),
          f"the lens table and the inflation block add no prose word "
          f"({stack.section_words(base)} = {stack.section_words(more)})")
    check(all(not s.get("charts") and not s.get("paragraph") for s in [lt] + ib),
          "and no chart and no paragraph: tables and lines only")
    src = (REPO / "daily_cascade" / "stack.py").read_text(encoding="utf-8")
    check('"charts": ["C3"] if reason else [],' in src,
          "the close's Plumbing keeps its one conditional chart")


def group_f() -> None:
    head("F. THE REGISTRY, THE CONFIG, THE HOOKS, NO FETCH")
    from altdata import config
    keys = [f"fred.{s.key}" for s in config.FRED_6E_SERIES] + macro_6e.KEYS
    unreg = [k for k in keys if not derived.registry_entry(k)]
    nofam = [k for k in keys if derived.family_of(k)[0] is None and k != "fred.mts_deficit"]
    units = [k for k in keys if not derived.registry_entry(k).get("units")]
    check(len(config.FRED_6E_SERIES) == 25 and not unreg and not nofam and not units,
          f"{len(keys)} new keys, each registered with its units and a family (the MTS "
          f"monthly deficit lens-excluded with its reason) {unreg or ''}{nofam or ''}")
    check(set(config.FRED_6E_SERIES) <= set(config.FRED_PULL_SERIES),
          "the FRED legs ride the existing pull")
    check(derived.registry_entry("fred.atl_wage_tracker")["units"] == "percent_return"
          and derived.delta_unit_for("calc.sofr_iorb_bp")[0] == "bps"
          and derived.delta_unit_for("calc.deficit_ttm_pct_gdp")[0] == "pp",
          "units by meaning: the wage tracker in pp, the spreads in bp, the shares in pp")
    mf = (REPO / "altdata" / "market_features.py").read_text(encoding="utf-8")
    ws = (REPO / "daily_cascade" / "weekly_stack.py").read_text(encoding="utf-8")
    pl = (REPO / "monthly_macro" / "payload.py").read_text(encoding="utf-8")
    check("macro_6e.rows(db, as_of=as_of, first_day=first_day)" in mf
          and "inflation_block.subsections(st, now)" in ws
          and "lens_cells.lens_table(" in ws and 'out["completeness"]' in pl,
          "the hooks: the features pass, the Weekly's Plumbing, the Monthly v2 appendix")
    cat = (REPO / "config" / "catalogue_commands.yaml").read_text(encoding="utf-8")
    mk = (REPO / "Makefile").read_text(encoding="utf-8")
    check("altdata.macro_6e:" in cat and "tools/validate_6e_rest.py" in mk,
          "the catalogue names the command; the Makefile the gate")
    src = "".join((REPO / p).read_text(encoding="utf-8") for p in (
        "altdata/macro_6e.py", "altdata/cpi_lead.py", "daily_cascade/lens_cells.py",
        "daily_cascade/inflation_block.py"))
    check(not re.search(r"\bimport (requests|urllib|anthropic|httpx)|http_get|import_yfinance", src),
          "no fetch and no model call in any of the four modules")


def main() -> int:
    with store("calc_in", build_rows()) as st:
        rows = macro_6e.rows(st)
    group_a(rows)
    group_b(build_rows() + rows)
    group_c()
    group_d(build_rows() + rows)
    group_e(build_rows())
    group_f()
    print(f"\n{PASSED} passed, {FAILED} failed")
    print(LINE)
    print("VALIDATION PASSED" if not FAILED else "VALIDATION FAILED")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
