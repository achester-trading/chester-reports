#!/usr/bin/env python3
"""
Validation gate: st-t2-rates -- the signal-triage order's Tranche 2 for session
A's line: ST-7 (the first calibration studies, tools/calibration/sr*.py) and
ST-5 (the funding-currency features) where no existing gate is their home. On
fixtures; no network, no model, no live store.

  A  THE SHARED ARITHMETIC. A par bond at an unchanged 4% returns 1/300 a month
     and 4.0742% over twelve; least squares with Newey-West errors on four
     points reproduces b 0.8, se 0.18, t 4.444; an expanding z of 1, 2, 3 is
     +1.0.
  B  SR-12. A 4.0 reading after forty at 5.0 is at the 2.44th percentile, a
     bottom decile; quiet gaps of two merge and three do not; the rule PASSes on
     five hand-made episodes, FAILs ("table only") when a horizon's hit falls to
     3 of 5, and is INSUFFICIENT on four.
  C  SR-15. The Treasuries metric is minus the ex-post real yield (-2.0 at 5%
     and 3% inflation); 121 of 180 paired months PASS, 119 FAIL, and 60 pairs
     are INSUFFICIENT; gold's conclusion is undefined below twelve months a
     bucket.
  D  SR-22. The old and the renamed TreasuryDirect fields read the same auction
     (dealers 12.53% of competitive); a 4.10% high yield over a 4.05% prior close
     is a 5.0 bp pseudo-tail; the live ABS_STRESS fires on the second consecutive
     bottom-decile cover; 20 falls in 30 PASS, 17 in 30 FAIL, 29 auctions are
     INSUFFICIENT.
  E  SR-23. $10bn a month for twelve months over $24tn of GDP is 0.50%; a quarter
     is used from the second month after it ends; both subsamples significant
     PASS, post-2008 only and neither FAIL, a short subsample is INSUFFICIENT.
  F  SR-21. A gap widening 1 bp a session starts episodes at sessions 63 and
     190; refused 35 bp above conceded PASSes, 20 bp FAILs, one conceded episode
     is INSUFFICIENT.
  G  THE LEDGERS. Each committed first edition carries its as-of, window and n,
     the pass rule, and a verdict that prints its inputs; a ledger missing its
     as-of, window or n is refused by the writer.
  H  THE REGISTER. Each entry's A-3 gate status is a rule-31 draft naming a
     ledger that exists, with the ledger's own verdict word; each register status
     still reads "gate pending"; the decision tables' rows are byte for byte
     what they were (sha256 pinned).
  I  NO STORE, NO FETCH. No calibration script opens the store or reads the
     market-state object (validate_regime's own test, run here on the new
     scripts); every study runs on its fixture with every HTTP helper raising.

    python tools/validate_st_t2_rates.py
"""

from __future__ import annotations

import hashlib
import importlib.util
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gate_tmp import mkdtemp                                    # noqa: E402

LINE = "=" * 78
PASS = FAIL = 0
TD = Path(mkdtemp("st-t2-rates-gate-"))
CAL = REPO / "tools" / "calibration"
STUDIES = {"SR-12": "sr12_bond_alloc", "SR-15": "sr15_valuation",
           "SR-21": "sr21_divergence", "SR-22": "sr22_auctions",
           "SR-23": "sr23_net_supply"}
EDITION = "2026-10-18"
# The order's decision rows for SR-12, 15, 21, 22, 23 and rule A-3, as they stood
# before ST-7 (docs/change-order-signal-triage-2026-09-25.md).
DECISION_ROWS_SHA = "8a8a418e4c9ceb5b8810099135c5c43a04a188ec462e36911009fe3909f9e877"


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


def mod(name: str):
    if str(CAL) not in sys.path:
        sys.path.insert(0, str(CAL))
    spec = importlib.util.spec_from_file_location(name, CAL / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def ms(a: str, n: int) -> list[str]:
    C = mod("st7_common")
    return [C.madd(a, k) for k in range(n)]


# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. THE SHARED ARITHMETIC")
    C = mod("st7_common")
    check(C.madd("2026-11", 3) == "2027-02" and C.madd("2026-01", -1) == "2025-12",
          "months add across a year end")
    tr = C.bond_tr({m: 4.0 for m in ms("2025-01", 13)})
    check(close(tr["2025-02"], 1 / 300, 1e-12)
          and close(C.compound(tr, "2025-01", 12), (1 + 1 / 300) ** 12 - 1, 1e-12)
          and close(C.compound(tr, "2025-01", 12), 0.040742, 1e-6),
          f"a par bond at an unchanged 4% returns 1/300 a month and 4.0742% over "
          f"twelve ({C.compound(tr, '2025-01', 12):.6f})")
    check(C.compound(tr, "2025-06", 12) is None,
          "a horizon past the data compounds to None, not to a short product")
    r = C.ols_nw([1, 3, 2, 4], [[1, 2, 3, 4]], 0)
    check(close(r["b"][0], 0.5) and close(r["b"][1], 0.8) and close(r["se"][1], 0.18)
          and close(r["t"][1], 0.8 / 0.18),
          f"least squares by hand: a 0.5, b 0.8, HC se 0.18, t 4.444 "
          f"({r['b'][1]:.4f}, {r['se'][1]:.4f}, {r['t'][1]:.4f})")
    z = C.expanding_z({"2020-01": 1.0, "2020-02": 2.0, "2020-03": 3.0}, "2020-01", 3)
    check(list(z) == ["2020-03"] and close(z["2020-03"], 1.0),
          "an expanding z of 1, 2, 3 at a burn-in of three is +1.0, and none before")


def group_b() -> None:
    head("B. SR-12: THE BOND ALLOCATION")
    S = mod("sr12_bond_alloc")
    qs = [f"{1950 + i // 4}-{(i % 4) * 3 + 1:02d}" for i in range(48)]
    alloc = {q: 5.0 for q in qs[:40]}
    alloc[qs[40]] = 4.0
    rows = S.bottom_decile(alloc)
    check(len(rows) == 2 and rows[1][3] and close(rows[1][2], 100 / 41, 1e-9)
          and not rows[0][3],
          f"a 4.0 reading after forty at 5.0 is at the {rows[1][2]:.2f}th percentile, "
          f"a bottom decile; the fortieth reading (n = 40) is not")
    flags = [(q, 1.0, 5.0, low) for q, low in zip(
        qs, [True, False, False, True, False, False, False, True])]
    eps = S.episodes(flags)
    check([(e["first_quarter"], e["last_quarter"]) for e in eps]
          == [(qs[0], qs[3]), (qs[7], qs[7])],
          "two quiet quarters merge into one episode; three start a new one")

    def row(r12, r36, cell=True):
        return {"in_cell": cell, "completed": True, "cell": "x",
                "real_12m": r12, "real_36m": r36}
    unc = {12: 0.02, 36: 0.12}
    rest = [row(0.0, 0.0, False), row(0.0, 0.05, False)]
    good = [row(a, b) for a, b in zip([0.05, 0.06, 0.07, 0.01, 0.08],
                                      [0.20, 0.25, 0.30, 0.10, 0.22])]
    j = S.judge(good + rest, unc)
    check(j["verdict"].startswith("PASS") and close(j["med"][12], 0.06)
          and close(j["hit"][12], 0.8) and close(j["med"][36], 0.22) and j["separates"]
          and "unconditional" in j["verdict"],
          f"five episodes, medians 6.0% and 22.0% over 2% and 12%, hits 4 of 5: PASS, "
          f"printed with its inputs ({j['verdict'][:60]}...)")
    bad = [row(a, b) for a, b in zip([0.05, 0.06, 0.01, 0.01, 0.08],
                                     [0.20, 0.25, 0.30, 0.10, 0.22])]
    j = S.judge(bad + rest, unc)
    check(j["verdict"].startswith("FAIL -- table only") and close(j["hit"][12], 0.6),
          "the 12-month hit at 3 of 5 (60%) is under two thirds: FAIL, table only")
    j = S.judge(good[:4] + rest, unc)
    check(j["verdict"].startswith("INSUFFICIENT") and "no rate prints" in j["verdict"],
          "four completed episodes in the cell are INSUFFICIENT: no rate prints")


def group_c() -> None:
    head("C. SR-15: THE RANK TEST AND GOLD'S WINDOW")
    S = mod("sr15_valuation")
    C = mod("st7_common")
    cpi = {m: 100.0 for m in ms("2019-01", 12)}
    cpi.update({m: 103.0 for m in ms("2020-01", 12)})
    lv = S.metrics({"gold": {}, "cmdty": {}, "cape": {}, "cpi": cpi,
                    "gs10": {"2020-06": 5.0}})
    check(close(lv["ust"]["2020-06"], -2.0),
          "Treasuries' metric is minus the ex-post real yield: GS10 5% less 3% "
          "inflation reads -2.0 (rich is high for all four)")
    pairs = [{"cheap_beats_rich": i < 121} for i in range(180)]
    j = S.judge(pairs)
    check(j["verdict"].startswith("PASS") and len(j["blocks"]) == 5
          and "67.2% of 180" in j["verdict"],
          f"121 of 180 paired months: PASS ({j['verdict']})")
    j = S.judge([{"cheap_beats_rich": i < 119} for i in range(180)])
    check(j["verdict"].startswith("FAIL") and "66.1%" in j["verdict"],
          "119 of 180 (66.1%) is under two thirds: FAIL")
    j = S.judge([{"cheap_beats_rich": True} for _ in range(60)])
    check(j["verdict"].startswith("INSUFFICIENT"),
          "sixty pairs give two non-overlapping blocks, under the floor of five: "
          "INSUFFICIENT")
    months = ms("2000-01", 120)
    rets = {"gold": {m: 0.0 for m in months}}
    cpi2 = {m: 100.0 for m in months}
    z = {m: (2.0 if i < 12 else -2.0 if i < 24 else 0.0) for i, m in enumerate(months)}
    g = S.gold_conclusion(z, rets, cpi2, months)
    check(g["n_rich"] == 12 and g["n_cheap"] == 12 and g["reverts"] is False
          and close(g["rich"], 0.0),
          "twelve rich and twelve cheap months with flat gold: defined, no reversion")
    z[months[0]] = 0.0
    g = S.gold_conclusion(z, rets, cpi2, months)
    check(g["reverts"] is None and g["n_rich"] == 11,
          "eleven rich months leave the conclusion undefined, not decided")
    check(close(C.real(0.10, {"2020-01": 100.0, "2021-01": 110.0}, "2020-01", 12), 0.0)
          and close(C.real(0.21, {"2020-01": 100.0, "2021-01": 110.0}, "2020-01", 12), 0.10),
          "real returns deflate by the CPI ratio: 10% nominal over 10% inflation is "
          "0%, 21% is 10%")


def group_d() -> None:
    head("D. SR-22: THE AUCTIONS")
    S = mod("sr22_auctions")
    new = {"type": "Note", "competitiveAuctionCloseDate": "2026-09-24T00:00:00",
           "bidToCoverRatio": "2.50", "originalSecurityTerm": "7-Year",
           "primaryDealersCompetitiveParAwarded": "5448000000",
           "subtotalCompetitiveParAwardedInsideOfOfferingAmount": "43481000000",
           "highYield": "4.100"}
    old = {"type": "Note", "auctionDate": "2026-09-24T00:00:00",
           "bidToCoverRatio": "2.50", "originalSecurityTerm": "7-Year",
           "primaryDealerAccepted": "5448000000", "competitiveAccepted": "43481000000",
           "highYield": "4.100"}
    a, b = S.auctions_from_records([new]), S.auctions_from_records([old])
    check(a == b and len(a) == 1 and close(a[0]["dealer"], 5.448 / 43.481)
          and a[0]["day"] == "2026-09-24",
          f"the renamed and the old field names read the same auction: dealers "
          f"{100 * a[0]['dealer']:.2f}% of competitive accepted")
    pt = S.pseudo_tails(a, {"7-Year": [("2026-09-22", 4.00), ("2026-09-23", 4.05),
                                       ("2026-09-24", 4.20)]})
    tail = pt[("2026-09-24", "Note:7-Year")]
    check(close(tail[0], 5.0) and tail[1] is False,
          "a 4.10% high yield over the previous session's 4.05% is a 5.0 bp "
          "pseudo-tail (the auction day's own close is not used); no decile yet")
    auc = [{"day": f"2025-{k + 1:02d}-15", "type": "Note", "term": "7-Year",
            "btc": 3.0 + 0.1 * k if k < 10 else 2.0, "dealer": 0.10, "high_yield": 4.0}
           for k in range(12)]
    fl = S.flags(auc)
    on = [d for (d, _), v in sorted(fl.items()) if v["abs_stress"]]
    check(on == ["2025-12-15"] and fl[("2025-12-15", "Note:7-Year")]["two_low"],
          "the live ABS_STRESS fires on the second consecutive bottom-decile cover "
          "and not on the first")
    auc[3]["dealer"] = 0.25
    check(S.flags(auc)[("2025-04-15", "Note:7-Year")]["dealer"],
          "and on dealers above 20% (25%) by the dealer leg")

    def ev(neg, pos):
        return [{"day": f"2020-{1 + i % 12:02d}-01", "d10_1m_bp": -1.0,
                 "d10_3m_bp": -10.0 if i < neg else 5.0} for i in range(neg + pos)]
    e = S.evaluate(ev(20, 10))
    check(e["word"] == "PASS" and close(e["m3"], -10.0) and close(e["hit"], 2 / 3),
          "20 falls in 30, median -10 bp: PASS")
    e = S.evaluate(ev(17, 13))
    check(e["word"] == "FAIL" and close(e["hit"], 17 / 30),
          "17 falls in 30 (56.7%) is under 60%: FAIL, stress flag only")
    check(S.evaluate(ev(29, 0))["word"] == "INSUFFICIENT",
          "29 flagged auctions are under the floor of 30: INSUFFICIENT")


def group_e() -> None:
    head("E. SR-23: THE NET-SUPPLY REGRESSION")
    S = mod("sr23_net_supply")
    months = ms("2024-01", 14)
    d = {"issuance": {m: 10e9 for m in months},
         "soma": {m: 1000.0 for m in ["2023-12"] + months},
         "gdp": {"2024-01": 24000.0}}
    sr = S.supply_ratio(d)
    check(close(sr.get("2024-12"), 0.5) and "2024-11" not in sr,
          f"$10bn a month for twelve months over $24tn of GDP is 0.50% "
          f"({sr.get('2024-12')}); eleven months are no ratio")
    check(S.gdp_known(d["gdp"], "2024-04") is None
          and S.gdp_known(d["gdp"], "2024-05") == 24000.0,
          "a quarter dated January is used from May (two months after it ends)")
    ok = {"b": 10.0, "t": 2.5, "n": 40}
    check(S.judge(ok, {"b": 5.0, "t": 2.0, "n": 200}).startswith("PASS")
          and "t +2.00" in S.judge(ok, {"b": 5.0, "t": 2.0, "n": 200}),
          "positive and significant in both: PASS, printed with b and t")
    check("post-2008 only" in S.judge({"b": 10.0, "t": 1.0, "n": 40},
                                      {"b": 5.0, "t": 2.5, "n": 200}),
          "significant post-2008 only: FAIL, descriptive")
    check("not significant post-2008" in S.judge(ok, {"b": 5.0, "t": 1.5, "n": 200}),
          "not significant post-2008: FAIL, descriptive")
    check(S.judge({"b": None, "t": None, "n": 10}, ok).startswith("INSUFFICIENT"),
          "a subsample under 24 months is INSUFFICIENT: no coefficient prints")


def group_f() -> None:
    head("F. SR-21: THE DIVERGENCE EPISODES")
    S = mod("sr21_divergence")
    import datetime as dt
    days = [(dt.date(2020, 1, 1) + dt.timedelta(days=i)).isoformat() for i in range(260)]
    d = {"dgs1": [(x, 2.0 + 0.01 * i) for i, x in enumerate(days)],
         "tar": [(days[0], 2.0)], "tar_l": [], "tar_u": []}
    gap = S.gap_series(d)
    check(close(gap[100][1], 100.0, 1e-6), "the gap is DGS1 less the target in bp "
                                         "(+100 bp after 100 sessions of +1)")
    eps = S.episodes(gap)
    check([i for i, _ in eps] == [63, 190] and all(s == 1 for _, s in eps),
          f"a gap widening 1 bp a session starts episodes at sessions 63 and 190 "
          f"({[i for i, _ in eps]}), nothing within 126 of the last")

    def r(outcome, x):
        return {"completed": True, "outcome": outcome, "d10_aligned_bp": x}
    con = [r("conceded", 10.0), r("conceded", 20.0)]
    j = S.judge(con + [r("refused", x) for x in (50.0, 60.0, 40.0)])
    check(j["verdict"].startswith("PASS") and close(j["mr"] - j["mc"], 35.0),
          "refused 50 bp against conceded 15 bp (35 apart): PASS")
    j = S.judge(con + [r("refused", x) for x in (30.0, 35.0, 40.0)])
    check(j["verdict"].startswith("FAIL") and close(j["mr"] - j["mc"], 20.0),
          "20 bp apart is under 25: FAIL")
    j = S.judge(con[:1] + [r("refused", x) for x in (30.0, 35.0, 40.0, 50.0)])
    check(j["verdict"].startswith("INSUFFICIENT"),
          "one conceded episode is under the floor of two a group: INSUFFICIENT")


def group_g() -> None:
    head("G. THE LEDGERS")
    from altdata import ledgers
    for sr in STUDIES:
        p = REPO / "docs" / "ledgers" / f"{sr.lower()}-ledger-{EDITION}.md"
        t = p.read_text(encoding="utf-8") if p.exists() else ""
        rows = dict(re.findall(r"^\| (As of|Window|n|Verdict|Pass rule[^|]*) \| (.+?) \|$",
                               t, re.M))
        check(p.exists() and all(rows.get(k, "").strip() for k in ("As of", "Window", "n"))
              and any(k.startswith("Pass rule") for k in rows)
              and re.search(r"\d", rows.get("Verdict", ""))
              and "laptop run, public sources" in t
              and (p.with_name(p.stem + "-episodes.csv")).exists(),
              f"{p.name}: as-of, window, n, the pass rule, a verdict printing its "
              f"inputs, the edition's label and its CSV")
    r = {"item": "SR-00", "title": "t", "as_of": "", "window": "w", "n": 3,
         "statistic": "s", "pass_rule": "p", "verdict": "PASS", "rights": "r",
         "sources": ["x"], "source_mode": "laptop run, public sources"}
    try:
        ledgers.write_ledger(r, TD)
        refused = False
    except ValueError:
        refused = True
    r2 = dict(r, as_of="2026-10", window="", n=None)
    check(refused and "missing as_of" in ledgers.ledger_faults(r)
          and {"missing window", "missing n"} <= set(ledgers.ledger_faults(r2)),
          "a ledger without its as-of, window or n is refused by the writer")


def group_h() -> None:
    head("H. THE REGISTER")
    reg = (REPO / "docs" / "signal-triage-register.md").read_text(encoding="utf-8")
    for sr in STUDIES:
        m = re.search(rf"^### {sr} .*?(?=^### )", reg, re.M | re.S)
        e = m.group(0) if m else ""
        d = re.search(r"\*Drafted under rule 31, 18 Oct 2026 \(ST-7[^*]*\*\s*\*\*A-3 gate "
                      r"status: (PASS|FAIL|INSUFFICIENT)\.\*\* ledger: (docs/ledgers/\S+\.md), "
                      r"(PASS|FAIL|INSUFFICIENT)", e)
        led = (REPO / d.group(2)) if d else None
        word = None
        if led and led.exists():
            v = re.search(r"^\| Verdict \| \*\*(\w+)", led.read_text(encoding="utf-8"), re.M)
            word = v.group(1) if v else None
        check(d and led.exists() and d.group(1) == d.group(3) == word
              and "**Register status.** ADOPTED — gate pending" in e,
              f"{sr}: the draft names {d.group(2) if d else 'no ledger'} with its "
              f"verdict ({word}); the register status still reads gate pending")
    co = (REPO / "docs" / "change-order-signal-triage-2026-09-25.md").read_text(
        encoding="utf-8").split("\n")
    rows = [x for x in co if re.match(r"^\| (12|15|21|22|23) \| [AR] \|", x)
            or x.startswith("| A-3 Duration tilt |")]
    sha = hashlib.sha256("\n".join(rows).encode()).hexdigest()
    check(len(rows) == 6 and sha == DECISION_ROWS_SHA,
          f"the order's decision rows for SR-12, 15, 21, 22, 23 and A-3 are untouched "
          f"({len(rows)} rows, sha256 {sha[:12]})")


def group_i() -> None:
    head("I. NO STORE, NO FETCH")
    pat = re.compile(r"ObservationStore|from altdata import .*observations|"
                     r"derived_forms|regime\.|['\"]fed_path['\"]|driver_cell")
    bad = [p.name for p in CAL.glob("*.py")
           if pat.search(p.read_text(encoding="utf-8"))]
    check(not bad, f"no calibration script opens the store, reads the market-state "
                   f"object or names the withdrawn cell ({bad or 'none'})")
    from altdata.sources import _base
    names = [n for n in ("http_get_json", "http_get_text", "http_get_response",
                         "http_get_bytes") if hasattr(_base, n)]
    saved = {n: getattr(_base, n) for n in names}
    calls = []

    def boom(*a, **k):
        calls.append(a[:1])
        raise RuntimeError("a study fetched")
    for n in names:
        setattr(_base, n, boom)
    try:
        for name in STUDIES.values():
            mod(name)
        S = mod("sr22_auctions")
        S.study({"auctions": [], "cmt": {"10-Year": [("2020-01-01", 1.0)]}},
                "laptop run, public sources")
    finally:
        for n, f in saved.items():
            setattr(_base, n, f)
    check(not calls, "importing the five studies and running one on a fixture, "
                     "every HTTP helper raising, fetches nothing")


def main() -> int:
    print(f"{LINE}\nst-t2-rates\n{LINE}")
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g,
              group_h, group_i):
        try:
            g()
        except Exception as exc:                              # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
