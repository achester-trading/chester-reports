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
  J  ST-5, BY HAND. On one fixture store: the yen front differential +369 bp and
     +60 bp over 60 sessions; the positioning z 1.6826 (1 to 52) and 1.7006 (1 to
     82); the hedged carry 1.00%; USDJPY's calm realized vol 8.1435%; the unwind
     tell on after five 2% falls and off the session before; the fix -14.2857 bp
     against the close, then 0; the US-China spread +270 bp; the devaluation
     tell's two legs on at the end and off while the fix leaned; the candidate
     fix_vs_offshore z -1.2486 over 39 dates through the gap machinery.
  K  ABSENT IS SAID, NEVER BLANK OR ZERO. An empty store writes no row, and every
     Factor IV line names its key and source; a missing JGB leg writes no front
     differential rather than a zero; the third leg reads NOT TRACKED with its
     by-hand key named.
  L  NOTHING ENTERS A COMPOSITE. No ST-5 key or candidate row is in the
     market-state config or any other config but its own; regime and
     contradictions import nothing of ST-5; every key is trigger_eligible false.
  M  THE REGISTRY. Each of the nine keys is registered with its unit, family and
     long window, and the catalogue resolves it with its command line; the
     order's calc.cnh_cny_gap is no second series; no manual.* key but the PMI;
     funding_currency.py imports no network library.

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
    # validate_regime's own pattern; its group L also holds every module to not
    # naming the withdrawn cell, so that half is not repeated here.
    pat = re.compile(r"ObservationStore|from altdata import .*observations|"
                     r"derived_forms|regime\.")
    bad = [p.name for p in CAL.glob("*.py")
           if pat.search(p.read_text(encoding="utf-8"))]
    check(not bad, f"no calibration script opens the store or reads the market-state "
                   f"object ({bad or 'none'})")
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


# ---------------------------------------------------------------------------
# ST-5
# ---------------------------------------------------------------------------
def obs(key, day, value, inst=None):
    return {"registry_key": key, "instrument": inst, "observed_at": day,
            "available_at": f"{day}T21:00:00+00:00", "value": value,
            "source": "fixture"}


def days(n: int, start: str) -> list[str]:
    import datetime as dt
    d0 = dt.date.fromisoformat(start)
    return [(d0 + dt.timedelta(days=i)).isoformat() for i in range(n)]


def funding_fixture() -> list[dict]:
    """The hand figures of group J (and validate_monthly group J)."""
    import math
    rows = []
    d70 = days(70, "2025-01-01")
    for i, d in enumerate(d70):
        rows += [obs("fred.yield_2y", d, 4.00 + 0.01 * i), obs("mof.jgb_2y", d, 1.00),
                 obs("fred.yield_10y", d, 4.50), obs("fred.tbill_3m", d, 4.00),
                 obs("cfets.cgb_10y", d, 1.80)]
    rows += [obs("fred.jp_3m", m, 0.50) for m in ("2025-01-01", "2025-02-01", "2025-03-01")]
    for i, d in enumerate(days(82 * 7, "2023-01-03")[::7]):
        rows.append(obs("cftc.noncomm_net", d, float(i + 1), "JPY"))
    px, lp = [], math.log(150.0)
    for i in range(300):
        if i:
            lp += (-0.02 if i >= 295 else (0.005 if i % 2 else -0.005))
        px.append(math.exp(lp))
    rows += [obs("yfinance.mkt_usdjpy", d, v) for d, v in zip(days(300, "2024-01-01"), px)]
    for i, d in enumerate(days(40, "2025-06-01")):
        late = i >= 25
        rows += [obs("yfinance.mkt_usdcny", d, 7.0),
                 obs("cfets.cny_fix", d, 7.00 if late else 6.99),
                 obs("cnh.usdcnh", d, 7.035 if late else 7.007),
                 obs("calc.cnh_cny_bp", d, 50.0 if late else 10.0)]
    return rows


def funding_store(rows, name):
    from altdata import observations
    p = str(TD / f"{name}.db")
    with observations.ObservationStore(p) as st:
        st.write_many(rows)
    return p


def group_j() -> None:
    head("J. ST-5, BY HAND")
    import math
    from altdata import funding_currency as F, observations
    db = funding_store(funding_fixture(), "st5")
    with observations.ObservationStore(db) as st:
        rows = F.compute_rows(st, "2026-10-17T21:00:00+00:00")
        st.write_many(rows)
        cands = {c["id"]: c for c in F.candidate_rows(st, "2026-10-17T21:00:00+00:00")}
    by: dict = {}
    for r in rows:
        by.setdefault(r["registry_key"], {})[r["observed_at"]] = r["value"]
    fd, f60 = by.get("calc.jp_front_diff", {}), by.get("calc.jp_front_diff_60d", {})
    check(close(fd.get("2025-03-11"), 369.0) and close(f60.get("2025-03-11"), 60.0)
          and "2025-03-01" not in f60 and close(f60.get("2025-03-02"), 60.0),
          f"the front differential: 4.69% less 1.00% is +369 bp, +60 bp over 60 "
          f"sessions, none before the 61st ({fd.get('2025-03-11')}, {f60.get('2025-03-11')})")
    z = by.get("calc.jpy_pos_z", {})
    zs = sorted(z.items())
    check(len(zs) == 31 and close(zs[0][1], 25.5 / math.sqrt(52 * 53 / 12))
          and close(zs[-1][1], 40.5 / math.sqrt(82 * 83 / 12)),
          f"positioning z: the 52nd report of 1..52 is {zs[0][1]:.4f} (25.5 over "
          f"sqrt(52 x 53 / 12)), the 82nd {zs[-1][1]:.4f}; none before 52 weeks")
    hc = by.get("calc.jp_hedged_carry", {})
    check(len(hc) == 70 and all(close(v, 1.00) for v in hc.values()),
          "the hedged carry: 4.50% less (4.00% less 0.50%) is +1.00% on all 70 days "
          "(the monthly yen leg carried)")
    rv = by.get("calc.usdjpy_rvol_20d", {})
    calm = 100 * 0.005 * math.sqrt(20 / 19) * math.sqrt(252)
    check(close(rv.get("2024-06-01"), calm, 1e-6) and close(calm, 8.1435, 1e-4),
          f"realized vol of alternating 0.5% days: 0.5% x sqrt(20/19) x sqrt(252) = "
          f"{calm:.4f}% ({rv.get('2024-06-01')})")
    uw = by.get("calc.jpy_unwind", {})
    check(uw.get("2024-10-26") == 1.0 and uw.get("2024-10-21") == 0.0
          and not any(v for d, v in uw.items() if d < "2024-10-22"),
          f"the unwind tell: on after five 2% falls (USDJPY -9.5% in 5 sessions, vol "
          f"{rv.get('2024-10-26', 0):.1f}% against a {calm:.1f}% median), off the "
          f"session before, and never in the calm before it")
    dev = by.get("calc.cny_fix_dev", {})
    check(close(dev.get("2025-06-02"), 1e4 * (6.99 / 7.0 - 1)) and close(dev.get("2025-07-10"), 0.0)
          and "2025-06-01" not in dev,
          f"the fix against the previous close: 6.99 on 7.00 is {dev.get('2025-06-02'):.4f} bp "
          f"(leaning), 7.00 on 7.00 is 0; no previous close, no row")
    us = by.get("calc.uscn_10y_spread", {})
    check(close(us.get("2025-01-01"), 270.0), "the US-China spread: 4.50% less 1.80% is +270 bp")
    dt_ = by.get("calc.deval_tell", {})
    check(dt_.get("2025-07-10") == 1.0 and dt_.get("2025-06-25") == 0.0
          and min(dt_) == "2025-06-25",
          "the devaluation tell's two legs: on at the end (no lean, the gap +50 bp and "
          "40 bp wider), off while the fix leaned; first read at the 25th observation")
    c = cands.get("fix_vs_offshore", {})
    check(close(c.get("magnitude"), -1.2486, 1e-4) and c.get("n") == 39,
          f"the candidate fix_vs_offshore through contradictions.gap_z: z "
          f"{c.get('magnitude')} over {c.get('n')} dates (hand: -(15/39 high) "
          f"standardised = -1.2486)")
    c2 = cands.get("carry_vs_vol", {})
    check(c2.get("magnitude") is not None and (c2.get("n") or 0) >= 30,
          f"the candidate carry_vs_vol computes ({c2.get('magnitude')}, n {c2.get('n')})")


def group_k() -> None:
    head("K. ABSENT IS SAID, NEVER BLANK OR ZERO")
    from altdata import funding_currency as F, observations
    from daily_cascade import absorption_block as B
    db = funding_store([], "st5-empty")
    with observations.ObservationStore(db) as st:
        rows = F.compute_rows(st, "2026-10-17T21:00:00+00:00")
        ls = B.funding_lines(st, "2026-10-17T21:00:00+00:00")
        cs = B.china_status(st, "2026-10-17T21:00:00+00:00")
    keys = ("calc.jp_front_diff", "calc.jpy_pos_z", "calc.jp_hedged_carry",
            "calc.jpy_unwind", "calc.cny_fix_dev", "calc.deval_tell")
    check(not rows and all(any(f"NOT AVAILABLE ({k}" in x for x in ls) for k in keys)
          and all(x.strip() and "(" in x for x in ls)
          and not any(": 0" in x or ": +0" in x for x in ls),
          f"an empty store writes no row; every Factor IV line names its key and "
          f"source, none blank, none zero ({len(ls)} lines)")
    check(any("NOT TRACKED (rule 30; by-hand key state_bank_dollar_selling" in x for x in ls),
          "the third leg reads NOT TRACKED with its by-hand key named")
    check(any("NOT AVAILABLE (calc.uscn_10y_spread" in x for x in cs)
          and any("NOT AVAILABLE (calc.cnh_cny_bp" in x for x in cs),
          "the China panel's spread and gap lines name their keys when absent")
    one = [r for r in funding_fixture() if r["registry_key"] == "fred.yield_2y"]
    db = funding_store(one, "st5-half")
    with observations.ObservationStore(db) as st:
        rows = F.compute_rows(st, "2026-10-17T21:00:00+00:00")
    check(not [r for r in rows if r["registry_key"].startswith("calc.jp_front")],
          "with the JGB leg missing no front differential is written (not a zero)")


def group_l() -> None:
    head("L. NOTHING ENTERS A COMPOSITE")
    from altdata import derived, funding_currency as F
    keys = list(F.FEATURES) + ["carry_vs_vol", "fix_vs_offshore"]
    hits = []
    for p in list((REPO / "config").rglob("*.yaml")) + [REPO / "regime.py",
                                                       REPO / "contradictions.py"]:
        if p.name in ("funding_currency.yaml", "catalogue_commands.yaml"):
            continue
        t = p.read_text(encoding="utf-8", errors="replace")
        hits += [f"{p.name}:{k}" for k in keys if k in t]
    check(not hits, f"no ST-5 key or candidate row is in the market-state config or "
                    f"any other config but its own ({hits or 'none'})")
    src = "".join((REPO / f).read_text(encoding="utf-8") for f in ("regime.py", "contradictions.py"))
    check("funding_currency" not in src, "regime and contradictions import nothing of ST-5")
    te = [k for k in F.FEATURES if (derived.registry_entry(k) or {}).get("trigger_eligible")]
    check(not te, f"every ST-5 key is trigger_eligible false ({te or 'all false'})")


def group_m() -> None:
    head("M. THE REGISTRY")
    import ast
    import yaml
    from altdata import catalogue, funding_currency as F
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    met, fam, lw = reg.get("metrics") or {}, reg.get("families") or {}, reg.get("long_windows") or {}
    want = {"calc.jp_front_diff": "bps", "calc.jp_front_diff_60d": "bps",
            "calc.jpy_pos_z": "ratio", "calc.jp_hedged_carry": "percent_rate",
            "calc.usdjpy_rvol_20d": "vol_pct", "calc.jpy_unwind": "boolean",
            "calc.cny_fix_dev": "bps", "calc.uscn_10y_spread": "bps",
            "calc.deval_tell": "boolean"}
    bad = [k for k, u in want.items() if (met.get(k) or {}).get("units") != u
           or k not in fam or k not in lw]
    res = catalogue.resolved()
    check(set(want) == set(F.FEATURES) and not bad and all(k in res for k in want),
          f"the nine keys are registered with their units, families and long windows, "
          f"and the catalogue resolves them ({bad or 'all'})")
    cmds = yaml.safe_load((REPO / "config" / "catalogue_commands.yaml").read_text(encoding="utf-8"))
    check("altdata.funding_currency" in str(cmds), "the catalogue's command line names "
                                                  "altdata.funding_currency")
    check("calc.cnh_cny_gap" not in met
          and "calc.cnh_cny_gap" in str((met.get("calc.cnh_cny_bp") or {}).get("description")),
          "the order's calc.cnh_cny_gap is no second series: calc.cnh_cny_bp says it is the one")
    manual = sorted(k for k in met if k.startswith("manual."))
    check(manual in ([], ["manual.global_pmi"]),
          f"no new by-hand key: the registry's manual.* metrics are the PMI alone ({manual})")
    banned = {"requests", "urllib", "httpx", "socket", "anthropic", "subprocess"}
    tree = ast.parse((REPO / "altdata" / "funding_currency.py").read_text(encoding="utf-8"))
    names = [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
    names += [n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    check(not [x for x in names if any(x == b or x.startswith(b + ".") for b in banned)],
          "altdata/funding_currency.py imports no network library")


def main() -> int:
    print(f"{LINE}\nst-t2-rates\n{LINE}")
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g,
              group_h, group_i, group_j, group_k, group_l, group_m):
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
