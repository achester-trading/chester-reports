#!/usr/bin/env python3
"""
Batch 7 items 46 and 48, Group A, and the cross-cutting lenses (6e-releases, 16 Oct
2026) -- what has no home in tools/validate_lenses.py or tools/validate_6e_rest.py.
A code gate: fixture series in temporary observation stores and fixture files for
the readers; it never reads the live store, fetches or calls a model. No figure
here is real.

  A. Item 46a, the decomposition by hand: the five contributions, supercore from
     core services less shelter, the residual; the Cleveland median and trimmed
     mean; the diffusion's share and its minimum count
  B. Item 46b, the pass-through flag at its thresholds and not below (the spike
     and the acceleration); withheld for a vintage not yet published; item 32's
     printed state switched
  C. Item 48 lenses 1-6: cyclical core payrolls by hand; the diffusion flag under
     50 for three months and not at 50 or for two; the revision flag from stored
     vintages by hand, withheld before the third release; permanent job losers at
     10% and not below; the claims read; the leading pieces and wages
  D. Item 48 lenses 7-11: the shelter lead, supercore 3 and 6 months, sticky and
     flexible, goods and services, the base-effect ladder against a hand-computed
     fixture, the wedge with its weights named
  E. Lens 22, the vintage rule: a flag reads the vintage knowable at the cutoff,
     and one that would need a later vintage is withheld
  F. Lens 21 and 23: six months annualised beside three for every release;
     "no consensus" renders in the lens cell and the release-day line
  G. The display: the inflation block's panels, the labour block, its Monthly
     place, the budgets (no prose but the claim, no chart), the release-day lines
     on a fixture calendar and in the close's Plumbing
  H. The readers (Zillow, Apartment List, the Cleveland Fed rules) on fixture
     files, robots refusal writes nothing; the registry, the rosters, the
     catalogue, the Makefile; no fetch and no model call in the lens code
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import datetime as dt
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gate_tmp import mkdtemp  # noqa: E402

from altdata import derived, observations, releases  # noqa: E402

TMP = Path(mkdtemp("gate_releases_"))
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


def near(a, b, tol=1e-6) -> bool:
    return a is not None and b is not None and abs(a - b) <= tol


def row(key, day, value, avail=None):
    return {"registry_key": key, "instrument": None, "observed_at": str(day),
            "available_at": avail or f"{day}T21:00:00+00:00", "value": float(value),
            "source": "fixture", "availability_kind": "reconstructed"}


def months(first: str, n: int) -> list[str]:
    return [f"{releases.shift(first[:7], i)}-01" for i in range(n)]


_N = 0


def store(rows: list[dict]) -> observations.ObservationStore:
    global _N
    _N += 1
    st = observations.ObservationStore(str(TMP / f"s{_N}.sqlite"))
    st.write_many(rows)
    return st


def path(key: str, first: str, mms: list[float], base: float = 100.0) -> list[dict]:
    """An index from `first` whose month-on-month changes (percent) are `mms`."""
    out, v = [row(key, f"{first[:7]}-01", base)], base
    for i, x in enumerate(mms, 1):
        v *= 1.0 + x / 100.0
        out.append(row(key, f"{releases.shift(first[:7], i)}-01", v))
    return out


CFG = releases.config()


# ---------------------------------------------------------------------------
def decomposition_rows(n_hot: int = 10, n_cool: int = 14) -> list[dict]:
    R = []
    R += path("fred.cpi", "2025-09-01", [0.2] * 11 + [0.6])
    R += path("fred.core_cpi", "2025-09-01", [0.25] * 12)
    R += path("fred.cpi_energy", "2025-09-01", [0.0] * 11 + [5.0])
    R += path("fred.cpi_food", "2025-09-01", [0.0] * 11 + [0.1])
    R += path("fred.cpi_core_goods", "2025-09-01", [0.0] * 11 + [-0.1])
    R += path("fred.cpi_shelter", "2025-09-01", [0.3] * 12)
    R += path("fred.cpi_core_services", "2025-09-01", [0.4] * 12)
    for i, m in enumerate(("2026-07-01", "2026-08-01", "2026-09-01")):
        R.append(row("fred.cpi_median", m, (3.2, 3.0, 2.8)[i]))
        R.append(row("fred.cpi_trimmed_mean", m, (3.6, 3.4, 3.5)[i]))
    cats = CFG["diffusion"]["categories"]
    for j, k in enumerate(cats[:n_hot + n_cool]):
        R += path(k, "2026-08-01", [0.5 if j < n_hot else 0.1])
    return R


def group_a() -> None:
    head("A. ITEM 46a: THE DECOMPOSITION BY HAND")
    with store(decomposition_rows()) as st:
        dc = releases.decomposition(st, CUT, CFG)
    p = {x["name"]: x for x in dc["pieces"]}
    sc = (0.61 * 0.4 - 0.355 * 0.3) / 0.255
    want = {"energy": 0.064 * 5.0, "food": 0.136 * 0.1, "core goods": 0.19 * -0.1,
            "shelter": 0.355 * 0.3, "core services ex shelter": 0.255 * sc}
    check(dc["month"] == "2026-09" and all(near(p[k]["contribution_pp"], v, 1e-3)
                                           for k, v in want.items()),
          f"each contribution is its weight x its own month-on-month change: energy "
          f"0.064 x 5.0 = 0.320 pp ... supercore 0.255 x {sc:.4f} "
          f"({ {k: p[k]['contribution_pp'] for k in p} })")
    check(near(p["core services ex shelter"]["mm_pct"], sc, 1e-3),
          f"supercore's month = (0.61 x core services 0.4 - 0.355 x shelter 0.3) / "
          f"0.255 = {sc:.3f}%")
    tot = sum(want.values())
    check(near(dc["sum_pp"], tot, 1e-3) and near(dc["residual_pp"], 0.6 - tot, 1e-3)
          and near(dc["headline_mm_pct"], 0.6, 1e-3),
          f"the pieces sum to {tot:.3f} pp; the headline's 0.600% leaves a residual of "
          f"{0.6 - tot:.3f} pp, printed")
    m, t = dc["median"], dc["trimmed_mean"]
    check(near(m["ann_pct"], 2.8) and near(m["avg_3m_ann_pct"], 3.0)
          and near(t["ann_pct"], 3.5) and near(t["avg_3m_ann_pct"], 3.5),
          "the Cleveland median 2.8% (3.0% over three months) and trimmed mean 3.5%")
    d = dc["diffusion"]
    check(d["hot"] == 10 and d["n"] == 24 and near(d["share_pct"], 41.7, 0.05),
          f"diffusion: 10 of 24 categories above 4% annualised (0.5% a month is "
          f"{releases.ann_mm(0.5):.2f}%; 0.1% is {releases.ann_mm(0.1):.2f}%): "
          f"{d['share_pct']}%")
    with store(decomposition_rows(5, 12)) as st:
        d2 = releases.decomposition(st, CUT, CFG)["diffusion"]
    check(d2["share_pct"] is None and d2["n"] == 17 and "18 needed" in d2["reason"],
          f"under 18 categories printed, no share and the reason ({d2['reason']})")
    with store([x for x in decomposition_rows() if x["registry_key"] != "fred.cpi_food"
                or x["observed_at"] < "2026-09-01"]) as st:
        dc3 = releases.decomposition(st, CUT, CFG)
    f = {x["name"]: x for x in dc3["pieces"]}["food"]
    check(f["contribution_pp"] is None and "not published" in f["reason"]
          and dc3["sum_pp"] is None,
          f"a piece without the month's print carries its reason and no sum is "
          f"claimed ({f['reason']})")


# ---------------------------------------------------------------------------
S = "2026-06"            # the spike month; the latest month is S + 3


def pt_rows(spike: float = 5.0, ppi_last: bool = True) -> list[dict]:
    a = 100.0 * (1.02 ** (1 / 12) - 1.0)
    b = 100.0 * (1.04 ** (1 / 12) - 1.0)
    mms = [a] * 7 + [b] * 3                  # Dec 2025 base; Jan-Jun at a; Jul-Sep at b
    R = path("fred.cpi_energy", "2025-12-01", [0.1] * 5 + [spike] + [0.1] * 3)
    for k in CFG["pass_through"]["basket"]:
        rr = path(k, "2025-11-01", mms)
        if k == "fred.ppi_truck_freight" and not ppi_last:
            rr = [x for x in rr if x["observed_at"] < "2026-09-01"]
        R += rr
    return R


def cfg_with(**kw) -> dict:
    import copy
    c = copy.deepcopy(CFG)
    c["pass_through"].update(kw)
    return c


def group_b() -> None:
    head("B. ITEM 46b: THE PASS-THROUGH FLAG AT ITS THRESHOLDS, AND ITEM 32'S STATE")
    with store(pt_rows()) as st:
        base = releases.pass_through(st, CUT, cfg_with(acceleration_pp=0.0))
        idx, _ = releases.basket_index(st, CUT, CFG)
        acc = releases.annualised(idx, "2026-09", 3) - releases.annualised(idx, S, 3)
        at = releases.pass_through(st, CUT, cfg_with(acceleration_pp=acc))
        above = releases.pass_through(st, CUT, cfg_with(acceleration_pp=acc + 0.0001))
    check(base["spikes"] and base["spikes"][0]["month"] == S
          and near(releases.annualised(idx, S, 3), 2.0, 1e-6)
          and near(releases.annualised(idx, "2026-09", 3), 4.0, 1e-6),
          f"the {S} energy spike (+5.0%); the basket at 2.0% annualised then, 4.0% "
          f"three months on (accelerating {acc:.4f} points)")
    check(at["flag"] is True and at["fired"]["month"] == "2026-09"
          and above["flag"] is False,
          f"the flag fires with the threshold at the acceleration ({acc:.4f}) and not "
          f"0.0001 above it")
    with store(pt_rows()) as st:
        dflt = releases.pass_through(st, CUT, CFG)
    check(dflt["flag"] is (acc >= CFG["pass_through"]["acceleration_pp"]),
          f"at the session-set {CFG['pass_through']['acceleration_pp']} points the "
          f"fixture's {acc:.2f} {'fires' if dflt['flag'] else 'does not fire'}")
    with store(pt_rows(spike=3.0)) as st:
        s_at = releases.pass_through(st, CUT, cfg_with(energy_spike_mm_pct=3.0))
    with store(pt_rows(spike=2.99)) as st:
        s_below = releases.pass_through(st, CUT, cfg_with(energy_spike_mm_pct=3.0))
    check(s_at["spikes"] and not s_below["spikes"] and s_below["flag"] is False
          and "no energy spike" in s_below["reason"],
          "an energy spike at +3.0% on the month and not at +2.99%")
    with store(pt_rows(ppi_last=False)) as st:
        held = releases.pass_through(st, CUT, cfg_with(acceleration_pp=acc))
    check(held["flag"] is None and "truck-freight PPI" in (held["withheld"] or ""),
          f"the truck-freight PPI for Sep not yet published: the flag is WITHHELD, not "
          f"read on the legs that are in ({held['withheld']})")
    st_ = CFG["pass_through"]["states"]
    check(releases.item32_state(True, {"flag": True}) == st_["propagating"]
          and releases.item32_state(True, {"flag": False}) == st_["contained"]
          and releases.item32_state(True, {"flag": None}) == st_["contained"]
          and releases.item32_state(False, {"flag": True}) is None
          and releases.item32_state(None, {"flag": True}) is None,
          "item 32's printed state: a supply shock reads 'contained' until the flag "
          "fires, 'propagating' after; no supply shock, no switch (ruling (d))")
    with store([]) as st:
        r32 = releases.item32_read(st, CUT)
    try:
        import altdata.st_r5_t1_rest  # noqa: F401
        on_branch = True
    except ImportError:
        on_branch = False
    check(on_branch or (r32["supply_shock"] is None and "st-r5-t1-rest" in r32["reason"]),
          f"without item 32's classifier on the branch, the absence says where it is "
          f"({r32.get('reason')})")


# ---------------------------------------------------------------------------
E_ = CFG["employment"]


def group_c() -> None:
    head("C. ITEM 48 LENSES 1-6: EMPLOYMENT, AND THE THREE FLAGS")
    R = []
    for i, m in enumerate(months("2026-06-01", 4)):
        R.append(row(E_["private"], m, (135000, 135100, 135150, 135180)[i]))
        R.append(row(E_["edu_health"], m, (28000, 28050, 28100, 28160)[i]))
        R.append(row(E_["payrolls"], m, 159000 + 40 * i))
    for m, v in zip(months("2026-04-01", 5), (55, 52, 49, 48, 49.9)):
        R.append(row(E_["diffusion_1m"], m, v))
        R.append(row(E_["diffusion_3m"], m, v + 1))
    for i, m in enumerate(months("2025-07-01", 15)):
        R.append(row(E_["permanent_losers"], m, 1920.001 if i >= 12 else 1600.0))
    w0 = dt.date(2026, 5, 30)
    for i in range(20):
        d = w0 + dt.timedelta(days=7 * i)
        R.append(row(E_["claims_initial"], d, 220000))
        R.append(row(E_["claims_continuing"], d, 1_900_000 if i >= 9 else 1_800_000))
    for i, m in enumerate(months("2025-09-01", 13)):
        R.append(row(E_["temp_help"], m, 2500 - 5 * i))
        R.append(row(E_["agg_hours"], m, 120.0 * 1.01 ** (i / 12)))
        R.append(row(E_["quits_rate"], m, 2.3 if i == 0 else 2.0))
        R.append(row(E_["openings"], m, 7000))
        R.append(row(E_["unemployed"], m, 7000))
        R.append(row(E_["atl_wage"], m, 4.1))
        R.append(row(E_["ahe"], m, 36.0 * 1.035 ** (i / 12)))
        R.append(row(E_["switchers"], m, 4.7))
        R.append(row(E_["stayers"], m, 3.4))
    R += [row(E_["eci"], "2025-04-01", 100.0), row(E_["eci"], "2026-04-01", 103.5)]
    with store(R) as st:
        em = releases.employment(st, CUT, CFG)
    cy = em["cyclical"]
    check(near(cy["core_change_k"], -30.0) and near(cy["core_3m_avg_k"], 6.7)
          and near(cy["headline_change_k"], 40.0),
          "lens 1: private less education and health, 107,050k to 107,020k is -30k "
          "(three-month average +6.7k) against a +40k headline")
    d = em["diffusion"]
    check(d["flag"] is True and d["run"] == [49.9, 48.0, 49.0],
          "lens 2: three consecutive months under 50 (49, 48, 49.9) FLAG")
    for last, nm in ((50.0, "exactly 50"),):
        R2 = [x for x in R if not (x["registry_key"] == E_["diffusion_1m"]
                                   and x["observed_at"] == "2026-08-01")]
        R2.append(row(E_["diffusion_1m"], "2026-08-01", last))
        with store(R2) as st:
            d2 = releases.employment(st, CUT, CFG)["diffusion"]
        check(d2["flag"] is False, f"and no flag when the third month is {nm} (under, "
                                   f"not at)")
    R3 = [x for x in R if not (x["registry_key"] == E_["diffusion_1m"]
                               and x["observed_at"] == "2026-06-01")]
    R3.append(row(E_["diffusion_1m"], "2026-06-01", 51.0))
    with store(R3) as st:
        d3 = releases.employment(st, CUT, CFG)["diffusion"]
    check(d3["flag"] is False, "nor for two months under 50 (51, 48, 49.9)")
    R4 = [x for x in R if not (x["registry_key"] == E_["diffusion_1m"]
                               and x["observed_at"] == "2026-07-01")]
    with store(R4) as st:
        d4 = releases.employment(st, CUT, CFG)["diffusion"]
    check(d4["flag"] is None and "Jul 2026" in d4["withheld"],
          f"a missing month withholds the flag ({d4['withheld']})")
    pl = em["permanent_losers"]
    check(pl["flag"] is True and near(pl["yoy_pct"], 20.0, 1e-3),
          "lens 4: permanent job losers' three-month average 1,920k against 1,600k a "
          "year earlier, +20.0%: FLAG at the threshold")
    R5 = [x for x in R if x["registry_key"] != E_["permanent_losers"]]
    R5 += [row(E_["permanent_losers"], m, 1919.84 if i >= 12 else 1600.0)
           for i, m in enumerate(months("2025-07-01", 15))]
    with store(R5) as st:
        pl5 = releases.employment(st, CUT, CFG)["permanent_losers"]
    check(pl5["flag"] is False and near(pl5["yoy_pct"], 19.99, 1e-6),
          "and not at +19.99%")
    cl = em["claims"]
    check(cl["hiring_freeze_read"] and near(cl["initial_change_pct"], 0.0)
          and near(cl["continuing_change_pct"], round(100 * (1.9 / 1.8 - 1), 1)),
          f"lens 4's claims read: continuing up {cl['continuing_change_pct']}% over 13 "
          f"weeks with initial flat -- the hiring-freeze read (report-only)")
    le, wg = em["leading"], em["wages"]
    check(near(le["temp_help"]["change_3m_k"], -15.0)
          and near(le["agg_hours"]["yoy_pct"], 1.0, 1e-3)
          and near(le["quits_rate"]["change_12m_pp"], -0.3)
          and near(le["openings_per_unemployed"]["ratio"], 1.0),
          "lens 5: temp help -15k over three months; aggregate hours +1.0% on the "
          "year; quits 2.0%, -0.3 pp; 1.00 openings per unemployed")
    check(near(wg["eci"]["yoy_pct"], 3.5) and near(wg["ahe"]["yoy_pct"], 3.5, 1e-3)
          and near(wg["switcher_premium"]["premium_pp"], 1.3)
          and near(wg["atlanta"]["pct"], 4.1),
          "lens 6: ECI +3.5% on the year; the tracker 4.1% beside AHE +3.5%; the "
          "switcher premium 4.7 less 3.4 = 1.3 pp")


def rev_rows(last_up: bool = False) -> list[dict]:
    """Payroll releases R1-R4 as vintages: each prints a new month and revises
    the two before it."""
    k = E_["payrolls"]
    R1, R2, R3, R4 = ("2026-07-03T12:30:00+00:00", "2026-08-01T12:30:00+00:00",
                      "2026-09-05T12:30:00+00:00", "2026-10-03T12:30:00+00:00")
    return [row(k, "2026-04-01", 1000, R1), row(k, "2026-05-01", 1100, R1),
            row(k, "2026-06-01", 1200, R1),
            row(k, "2026-07-01", 1300, R2), row(k, "2026-05-01", 1090, R2),
            row(k, "2026-06-01", 1180, R2),
            row(k, "2026-08-01", 1400, R3), row(k, "2026-06-01", 1170, R3),
            row(k, "2026-07-01", 1290, R3),
            row(k, "2026-09-01", 1500, R4), row(k, "2026-07-01", 1280, R4),
            row(k, "2026-08-01", 1410 if last_up else 1390, R4)]


def group_c2() -> None:
    head("C2. LENS 3: THE REVISION FLAG FROM STORED VINTAGES, BY HAND")
    with store(rev_rows()) as st:
        revs = releases.net_revisions(st, E_["payrolls"], CUT)
        em = releases.employment(st, CUT, CFG)
    got = [(x["month"], x["net_revision"]) for x in revs]
    check(got == [("2026-07", -20.0), ("2026-08", -10.0), ("2026-09", -10.0)],
          f"the two-month net revisions by hand: (1180-1000)-(1200-1000) = -20; "
          f"(1290-1090)-(1300-1090) = -10; (1390-1170)-(1400-1170) = -10 ({got})")
    check(em["revisions"]["flag"] is True,
          "negative at each of the last three releases: FLAG")
    with store(rev_rows(last_up=True)) as st:
        up = releases.employment(st, CUT, CFG)["revisions"]
    check(up["flag"] is False and up["releases"][-1]["net_revision"] == 10.0,
          "a positive third revision (+10) clears it")


# ---------------------------------------------------------------------------
def group_d() -> None:
    head("D. ITEM 48 LENSES 7-11: CPI")
    c = CFG["cpi_lenses"]
    R = []
    R += [row("zillow.zori_us", m, 2000 * 1.03 ** (i / 12))
          for i, m in enumerate(months("2024-09-01", 25))]
    R += path("fred.cpi_shelter", "2025-09-01", [0.3] * 12)
    R += path("fred.cpi_core_services", "2025-09-01", [0.4] * 12)
    R += [row(c["sticky"], "2026-09-01", 3.6), row(c["flexible"], "2026-09-01", 1.2),
          row(c["sticky"], "2026-08-01", 3.3), row(c["sticky"], "2026-07-01", 3.0),
          row(c["flexible"], "2026-08-01", 0.0), row(c["flexible"], "2026-07-01", 0.0)]
    R += path(c["goods"], "2025-09-01", [0.0] * 12)
    R += path(c["services"], "2025-09-01", [0.3] * 12)
    # The ladder's fixture: Oct, Nov, Dec 2025 drop out next (0.4, 0.1, 0.2).
    lad_mm = [0.2, 0.4, 0.1, 0.2] + [0.2] * 6 + [0.3, 0.3, 0.3]   # Sep 2025 -> Sep 2026
    R += path("fred.cpi", "2025-08-01", lad_mm)
    R += path("fred.core_cpi", "2025-08-01", [0.25] * 13)
    R.append(row(c["wedge"], "2026-09-01", 0.45))
    with store(R) as st:
        L = releases.cpi_lenses(st, CUT, CFG)
    sl = L["shelter_lead"]
    z = next(x for x in sl["leads"] if x["key"] == "zillow.zori_us")
    a = next(x for x in sl["leads"] if x["key"] == "aptlist.rent_us")
    check(near(z["yoy_pct"], 3.0, 0.05) and near(z["yoy_lag_ago_pct"], 3.0, 0.05)
          and z["month"] == "2026-09" and a["month"] is None
          and "Apartment List" in a["reason"] and "new-tenant" in sl["gap"],
          "lens 7: Zillow +3.0% on the year now and 12 months earlier; Apartment List "
          "absent with its reason; the BLS new-tenant index named a gap")
    sc = (0.61 * 0.4 - 0.355 * 0.3) / 0.255
    want = 100 * ((1 + sc / 100) ** 12 - 1)
    check(near(L["supercore"]["ann_3m_pct"], want, 0.01)
          and near(L["supercore"]["ann_6m_pct"], want, 0.01),
          f"lens 8: supercore at {sc:.4f}% a month is {want:.2f}% annualised over three "
          f"months and over six")
    check(near(L["sticky"]["ann_pct"], 3.6) and near(L["sticky"]["avg_3m_pct"], 3.3)
          and near(L["flexible"]["avg_3m_pct"], 0.4)
          and near(L["goods"]["yoy_pct"], 0.0) and near(L["services"]["yoy_pct"],
                                                        100 * (1.003 ** 12 - 1), 0.01),
          "lens 9: sticky 3.6% (3.3% over three months), flexible 1.2% (0.4%); goods "
          "flat on the year, services +3.66%")
    lad = L["ladder"]["fred.cpi"]
    # BY HAND: Sep 2026's index over Oct 2025's, times the pace, for each rung.
    idx = [100.0]
    for x in lad_mm:
        idx.append(idx[-1] * (1 + x / 100))
    by_month = dict(zip(months("2025-08-01", 14), idx))
    pace = 0.3
    hand = [100 * (by_month["2026-09-01"] * (1 + pace / 100) ** k
                   / by_month[f"{releases.shift('2025-09', k)}-01"] - 1) for k in (1, 2, 3)]
    got = [x["yoy_pct"] for x in lad["rungs"]]
    check(near(lad["pace_mm_pct"], 0.3) and all(near(g, h, 1e-3) for g, h in zip(got, hand))
          and [x["drops_out_mm_pct"] for x in lad["rungs"]] == [0.4, 0.1, 0.2]
          and len(got) == 3,
          f"lens 10: the ladder at 0.3% a month, with Oct-Dec 2025's 0.4, 0.1 and 0.2 "
          f"dropping out, agrees with the hand computation ({[round(h, 3) for h in hand]})")
    check(near(L["wedge"]["gap_pp"], 0.45) and len(L["wedge"]["weights"]) == 3
          and any("shelter" in w["component"] for w in L["wedge"]["weights"]),
          "lens 11: the wedge 0.45 pp with the three weight differences named")


# ---------------------------------------------------------------------------
def group_e() -> None:
    head("E. LENS 22: THE VINTAGE RULE")
    k = E_["diffusion_1m"]
    first = "2026-09-04T12:30:00+00:00"
    revised = "2026-10-02T12:30:00+00:00"
    R = [row(k, "2026-06-01", 49.0, "2026-07-03T12:30:00+00:00"),
         row(k, "2026-07-01", 48.0, "2026-08-01T12:30:00+00:00"),
         row(k, "2026-08-01", 49.5, first),
         row(k, "2026-08-01", 50.5, revised)]       # August revised above 50
    with store(R) as st:
        before = releases.employment(st, "2026-09-20T20:00:00+00:00", CFG)["diffusion"]
        after = releases.employment(st, "2026-10-05T20:00:00+00:00", CFG)["diffusion"]
    check(before["flag"] is True and before["one_month"] == 49.5
          and after["flag"] is False and after["one_month"] == 50.5,
          "the flag reads the first print while it is the vintage knowable (FLAG on 20 "
          "Sep), and the revision once it is (no flag on 5 Oct)")
    with store(rev_rows()) as st:
        early = releases.employment(st, "2026-09-20T20:00:00+00:00", CFG)["revisions"]
        late = releases.employment(st, CUT, CFG)["revisions"]
    check(early["flag"] is None and "2 release" in early["withheld"]
          and late["flag"] is True,
          f"before the third release's vintage the revision flag is withheld "
          f"({early['withheld']}); after it, read")
    with store(pt_rows(ppi_last=False)) as st:
        idx, _ = releases.basket_index(st, CUT, CFG)
    check(max(idx) == "2026-08",
          "the basket's months are those all three legs printed: September waits on "
          "the PPI")


# ---------------------------------------------------------------------------
def group_f() -> None:
    head("F. LENS 21 (SIX MONTHS BESIDE THREE) AND LENS 23 (NO CONSENSUS)")
    from daily_cascade import lens_cells
    R = path("fred.cpi", "2025-06-01", [0.3] * 15)
    R += [row("fred.u3_rate", m, 4.0 + 0.05 * i) for i, m in enumerate(months("2025-06-01", 16))]
    with store(R) as st:
        lf = derived.lens_forms("fred.cpi", CUT, store=st)
        lu = derived.lens_forms("fred.u3_rate", CUT, store=st)
    f = lf["forms"]
    check(near(f.get("annualized_6m"), 100 * (1.003 ** 12 - 1), 1e-3)
          and near(f.get("annualized_3m"), 100 * (1.003 ** 12 - 1), 1e-3),
          f"an index release: 6-month annualised beside 3-month "
          f"({f.get('annualized_6m')}, {f.get('annualized_3m')})")
    check(near(lu["forms"].get("change_6m"), 0.30, 1e-6),
          f"a rate-like release: the 6-month change in pp (+0.30) "
          f"({lu['forms'].get('change_6m')})")
    cells = [c for c, _ in lens_cells.LENS_COLUMNS["release"]]
    check("6m ann. / 6m chg" in cells
          and lens_cells.cell(lf, "m6") == f"{100 * (1.003 ** 12 - 1):+.1f}% ann."
          and lens_cells.cell(lu, "m6") == "+0.30 pp",
          "the lens column prints it, the Monthly's and the Weekly's alike")
    check(lens_cells.cell(lf, "surprise") == "no consensus",
          "lens 23: the surprise cell prints 'no consensus'")


# ---------------------------------------------------------------------------
def group_g() -> None:
    head("G. THE DISPLAY: THE PANELS, THE LABOUR BLOCK, THE BUDGETS, THE RELEASE DAYS")
    from daily_cascade import inflation_block as ib
    from daily_cascade import labour_block as lb
    from daily_cascade import stack
    with store(decomposition_rows() + pt_rows()) as st:
        subs = ib.subsections(st, CUT)
    titles = [s["title"] for s in subs]
    dec = next((s for s in subs if s["title"] == ib.TITLE_DECOMP), None)
    check(dec is not None and ib.TITLE_LENSES in titles
          and len(dec["table"]["rows"]) == 6
          and any("median CPI 2.8%" in x for x in dec["lines"])
          and any("pass-through basket" in x for x in dec["lines"]),
          f"the inflation block prints the decomposition table (five pieces and the "
          f"headline) with the median, breadth and pass-through lines ({titles})")
    body = " ".join(" ".join(s.get("lines") or []) + (s.get("table_note") or "") for s in subs)
    check(not re.search(r"\b(?:fred|calc|zillow|aptlist|clevfed)\.[a-z0-9_]+", body),
          "no internal id in any printed line")
    R = []
    for i, m in enumerate(months("2026-06-01", 4)):
        R.append(row(E_["private"], m, 135000 + 10 * i))
        R.append(row(E_["edu_health"], m, 28000))
    with store(R + rev_rows()) as st:
        sec = lb.stack_section(st, CUT, {"title": "Labour", "monthly": "medium"}, None)
        lsubs = lb.subsections(st, CUT)
    check(sec["id"] == "labour" and sec["prose_wanted"] is False and lsubs
          and all(not s.get("paragraph_wanted") and not s.get("charts") for s in lsubs)
          and "FLAG" in " ".join(str(c) for r in lsubs[0]["table"]["rows"] for c in r),
          "the labour block: its tables, the revision flag in its row, no paragraph "
          "asked for and no chart")
    claim_w = stack.words(sec["claim"])
    check(stack.section_words(sec) == claim_w and claim_w <= 40,
          f"its budget: the code-written claim's {claim_w} words and nothing else -- "
          f"tables and lines never count")
    cfg = stack.config()
    ids = stack.section_ids(cfg, "monthly", {"labour": sec})
    ten = list(stack.SECTION_ORDER)
    check(ids[ids.index("plumbing") + 1] == "labour"
          and stack.section_ids(cfg, "daily", {}) == ten
          and stack.section_ids(cfg, "weekly", {}) == ten,
          "its place: after Plumbing in the Monthly; the close and the Weekly lay out "
          "the ten as before")
    spec = next(s for s in cfg["sections"] if s["id"] == "labour")
    check(spec.get("monthly") and not spec.get("weekly") and not spec.get("daily")
          and not spec.get("quarterly")
          and cfg["budget"]["monthly"] == {"words": 10000, "charts": 12},
          "config declares it at the Monthly's depth only; the Monthly's budgets "
          "(10,000 words, 12 charts) are unchanged")
    # The release-day lines on a fixture calendar: CPI for September first printed
    # 15 Oct 08:30 ET (12:30 UTC).
    on = "2026-10-15T12:30:00+00:00"
    cal = [x for x in decomposition_rows() if x["observed_at"] < "2026-09-01"]
    cal += [dict(x, available_at=on) for x in decomposition_rows()
            if x["observed_at"] == "2026-09-01"]
    with store(cal) as st:
        day = releases.release_day_lines(st, "2026-10-15T20:45:00+00:00", CFG)
        nxt = releases.release_day_lines(st, "2026-10-16T20:45:00+00:00", CFG)
        sec_c = stack.plumbing_section({"session": "2026-10-15"}, st,
                                       "2026-10-15T20:45:00+00:00", cfg)
    cpi = next((x for x in day if x["release"] == "cpi"), None)
    check(cpi is not None and "CPI for Sep 2026: +0.6% on the month" in cpi["line"]
          and "energy +0.32 pp" in cpi["line"] and not nxt,
          f"on CPI day the close's line names what moved the print; the next day "
          f"nothing ({cpi['line'] if cpi else None})")
    check(cpi is not None and "surprise: no consensus" in cpi["line"],
          "and the line says 'no consensus' for the surprise (lens 23)")
    it = next((i for i in sec_c["items"] if i["key"] == "plumb:release:cpi"), None)
    check(it is not None and it["priority"] == 1
          and sec_c["data"]["release_lines"][0]["release"] == "cpi",
          "the close's Plumbing carries it as a first-priority item, the path its "
          "existing narrative step reads (no new model call)")
    emp = [row(E_["payrolls"], m, 159000 + 40 * i, on)
           for i, m in enumerate(months("2026-06-01", 4))]
    with store(emp) as st:
        el = releases.release_day_lines(st, "2026-10-15T20:45:00+00:00", CFG)
    check(el and el[0]["release"] == "employment" and "payrolls +40k" in el[0]["line"],
          f"the employment report's line on its day ({el[0]['line'] if el else None})")


# ---------------------------------------------------------------------------
ZORI = ("RegionID,SizeRank,RegionName,RegionType,StateName,2026-07-31,2026-08-31,2026-09-30\n"
        "102001,0,United States,country,,2010.5,2015.25,\n"
        "394913,1,\"New York, NY\",msa,NY,3300,3310,3320\n")
APTL = ("\"location_name\",\"location_type\",\"location_fips_code\",\"population\","
        "\"state\",\"county\",\"metro\",\"bed_size\",\"2026_08\",\"2026_09\"\n"
        "\"United States\",\"National\",0,331097593,,,,\"1br\",1300,1310\n"
        "\"United States\",\"National\",0,331097593,,,,\"overall\",1388,1392\n")
RULES = ("Date,Maximum,75th Percentile,Median,25th Percentile,Minimum\n"
         + "\n".join(f"{m}/1/{y},{h},{q3},{md},{q1},{lo}" for m, y, h, q3, md, q1, lo in [
             (6, 2026, 3.63, 3.63, 3.63, 3.63, 3.63), (9, 2026, 6.8, 5.4, 4.25, 3.97, 3.65),
             (12, 2026, 9.6, 5.3, 4.43, 4.12, 3.65), (3, 2027, 11.9, 5.0, 4.5, 4.19, 3.66),
             (6, 2027, 14.0, 4.78, 4.42, 3.98, 3.65), (9, 2027, 15.9, 4.7, 4.39, 3.97, 3.64),
             (12, 2027, 17.6, 4.75, 4.44, 4.23, 3.63), (3, 2028, 19.2, 4.66, 4.32, 4.12, 3.58),
             (6, 2028, 20.8, 4.51, 4.28, 3.97, 3.5)]) + "\n")


def group_h() -> None:
    head("H. THE READERS ON FIXTURE FILES; THE REGISTRY, ROSTERS AND CATALOGUE")
    import yaml
    from altdata import config, feeds
    from altdata.sources import clevfed_rules, rent_indices
    av = "2026-10-15T14:00:00+00:00"
    z = rent_indices.zillow_rows(ZORI, av, "observed")
    a = rent_indices.aptlist_rows(APTL, av, "observed")
    check([(x["observed_at"], x["value"]) for x in z] == [("2026-07-01", 2010.5),
                                                          ("2026-08-01", 2015.25)]
          and all(x["registry_key"] == "zillow.zori_us" for x in z),
          "Zillow: the United States row only, month-end columns to month-start "
          "observations, a blank cell skipped, never zero")
    check([(x["observed_at"], x["value"]) for x in a] == [("2026-08-01", 1388.0),
                                                          ("2026-09-01", 1392.0)],
          "Apartment List: the national 'overall' row, not the 1-bedroom")
    c = clevfed_rules.rows_from_csv(RULES, av, "observed")
    got = {x["registry_key"]: x["value"] for x in c}
    check(all(x["observed_at"] == "2026-06-01" for x in c)
          and near(got["clevfed.rules_start"], 3.63) and near(got["clevfed.rules_median_4q"], 4.42)
          and near(got["clevfed.rules_iqr_4q"], 4.78 - 3.98)
          and near(got["clevfed.rules_median_8q"], 4.28),
          "the Cleveland Fed rules: the starting quarter, the median four and eight "
          "quarters on, the interquartile width four on")
    no = "User-agent: *\nDisallow: /research/\n"
    ok, why = rent_indices.robots_ok(lambda u: no if "zillowstatic" in u else "")
    ok2, _ = rent_indices.robots_ok(lambda u: "")
    okc, _ = clevfed_rules.robots_ok(lambda u: "User-agent: *\nDisallow: /errors/*\n")
    okc2, _ = clevfed_rules.robots_ok(lambda u: "User-agent: *\nDisallow: /-/media/\n")
    check(not ok and "zillowstatic" in why and ok2 and okc and not okc2,
          "robots: a disallowed path refuses the pull; the rules as they stand allow it")
    with store([]) as st:
        saved = rent_indices.robots_ok
        rent_indices.robots_ok = lambda get=None: (False, "fixture refusal")
        try:
            res = rent_indices.pull(db=st)
        finally:
            rent_indices.robots_ok = saved
        n = st.conn.execute("SELECT COUNT(*) FROM observations WHERE registry_key "
                            "LIKE 'zillow.%'").fetchone()[0]
    check(res["status"] == "STALE" and n == 0, "and a refused pull is STALE and writes "
                                               "nothing")
    check("rent_indices" in feeds.EXTERNAL_WRITERS and "clevfed_rules" in feeds.OFFICIAL_WRITERS
          and feeds.static_keys("rent_indices") == rent_indices.KEYS
          and feeds.static_keys("clevfed_rules") == clevfed_rules.KEYS,
          "both readers ride the existing pull, their KEYS literal for the roster")
    keys = ([f"fred.{s.key}" for s in config.FRED_RELEASES_SERIES]
            + rent_indices.KEYS + clevfed_rules.KEYS)
    bad = [k for k in keys if not derived.registry_entry(k).get("units")
           or derived.family_of(k)[0] is None]
    check(len(config.FRED_RELEASES_SERIES) == 45 and not bad
          and set(config.FRED_RELEASES_SERIES) <= set(config.FRED_PULL_SERIES),
          f"{len(keys)} new keys, each registered with its units and a family; the 45 "
          f"FRED legs on the existing pull {bad or ''}")
    check(derived.registry_entry("fred.cpi_median")["units"] == "percent_return"
          and derived.registry_entry("fred.lfpr_prime_age")["units"] == "percent_share"
          and derived.registry_entry("fred.ecb_assets")["units"] == "EUR_M"
          and derived.delta_unit_for("clevfed.rules_median_4q")[0] == "bps",
          "units by meaning: the medians in pp, participation a share, the ECB in euro "
          "millions, the rules' path in bp")
    cats = CFG["diffusion"]["categories"]
    check(len(cats) == 24 and len(set(cats)) == 24
          and all(derived.registry_entry(k) for k in cats),
          "the diffusion's 24 categories, distinct, each registered")
    src = yaml.safe_load((REPO / "source_registry.yaml").read_text(encoding="utf-8"))["sources"]
    cat = (REPO / "config" / "catalogue_commands.yaml").read_text(encoding="utf-8")
    mk = __import__("gate_list").makefile_text(REPO)
    check(src.get("rent_indices", {}).get("status") == "live"
          and src.get("clevfed_rules", {}).get("status") == "live"
          and "altdata.sources.rent_indices:" in cat and "altdata.releases:" in cat
          and "tools/validate_releases.py" in mk,
          "the source registry says live; the catalogue names the commands; the "
          "Makefile the gate")
    lens_src = "".join((REPO / p).read_text(encoding="utf-8") for p in (
        "altdata/releases.py", "daily_cascade/inflation_block.py",
        "daily_cascade/labour_block.py"))
    check(not re.search(r"\bimport (requests|urllib|anthropic|httpx)|http_get|"
                        r"import_yfinance|narrative\.", lens_src),
          "no fetch and no model call in the lens code")
    m6 = (REPO / "config" / "macro_6e.yaml").read_text(encoding="utf-8")
    check("lead: zillow.zori_us" in m6,
          "the CPI lead composite's shelter component reads Zillow (ruling (a)3)")


def main() -> int:
    group_a()
    group_b()
    group_c()
    group_c2()
    group_d()
    group_e()
    group_f()
    group_g()
    group_h()
    print(f"\n{PASSED} passed, {FAILED} failed")
    print(LINE)
    print("VALIDATION PASSED" if not FAILED else "VALIDATION FAILED")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
