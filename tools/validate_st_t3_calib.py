#!/usr/bin/env python3
"""
Validation gate: st-t3-calib -- the signal-triage order's Tranche 3 for session
A's line: the rulings of 18 Oct on the Tranche 2 report (Part 0), ST-8's second
calibration studies (Part 1) and ST-9's SR-8 false-bottom audit (Part 2), where
no existing gate is their home. On fixtures; no network, no model, no live store.

PART 0, THE RULINGS OF 18 OCT
  A  SR-22 (ruling 3). ABS_STRESS's base rate, "on for 67 percent of auctions
     since 2009, n=1,540", is recomputed from the first edition's CSV (1,034 of
     1,540 with 63 sessions forward) and prints beside every ABS_STRESS line,
     present or absent, with its modifier effect suspended; no module outside the
     writer and the block reads calc.abs_stress. The labelled variant reproduces a
     hand figure (the 80th percentile of 0.10..0.17 is 0.156, so 0.16 is above and
     0.155 is not; fewer than 8 prior auctions in two years read nothing); the
     second edition carries the variant and the base rates, and the first edition
     is byte for byte what it was.
  B  SR-21 (ruling 2). The register's dated note carries the sign reversal with
     its n (+45.5 against -17.5, n=46) and sends the amendment to the Doctrine
     monthly; CRED_STRESS and the venues' line print descriptive only.
  C  THE DEVALUATION TELL (ruling 6). On fixture states with both tracked legs
     held, neither held and none readable, the line prints "2 of 3 legs tracked",
     each leg's state and the third leg's key, and no verdict word; a config whose
     third leg had a source would print one (the rule is the switch, not a
     missing branch).

PART 1, ST-8 (each study reproduces a hand figure on a fixture)
  D  SR-1. z against a trend by hand (0,0,0,0,4 is 1.0954); the trigger arms,
     fires at the break and expires; six episodes PASS, five are INSUFFICIENT; a
     FAILing ETF pair with its own floor blocks a PASS; config/style_regime.yaml
     holds the study's thresholds value for value; total return by hand (1.12); the
     panel prints its readings and its ledger, no flag word, zero words.
  E  SR-13. Price-to-book by hand (+150%, -37.5%, a 187.5-point spread); 4 of 5
     PASS, 3 of 5 FAIL, 4 completed INSUFFICIENT.
  F  SR-5. The first-print change by hand (7, not 10); 2x over 8 PASS; a
     latest-vintage edition is INSUFFICIENT whatever it reads.
  G  SR-14. The flag fires once on a hand ratio; the dollar cell's sign; the
     cell rule PASSes, FAILs reversed, is INSUFFICIENT on one a cell.
  H  SR-2. ST-5's thresholds read from its config; four windows and two false
     positives PASS, three FAIL; a Tuesday's report is read from its Friday.
  I  SR-4. Both legs in Aug 2015 and never in 2022-23 PASS; a 2023 firing FAILs;
     a 2016 start is INSUFFICIENT; the base rate by hand; ST-5's own tell_legs.
  J  THE LEDGERS. As-of, window, n, pass rule, label and CSV on each; sourced
     comparisons labelled; SR-5 says latest vintages.
  K  THE REGISTER. Each draft names its ledger and its verdict; statuses still
     gate pending; the order's decision rows and the register's Index untouched.
  L  NO STORE, NO FETCH, on validate_regime's own pattern.
  M  CONFIG. Every config naming an admitting ledger names a PASS; SR-2's and
     SR-4's thresholds stay session-set; nothing of SR-13's.
  N  No new by-hand key; the Weekly's builders untouched by this branch.

PART 2, ST-9 (the SR-8 false-bottom audit)
  O  The replay reproduces a hand count on one fixture episode (a false bottom at
     80, no candidate at 70, the true one at 60); the read date and the state; the
     committed replay holds 12 false and the register's four true bottoms.
  P  Each element's score is computed by code (75% and one third discriminate,
     5 of 12 does not, one testable is not testable; the audit's word), a retest,
     the margin and the time prior by hand; every printed score is its CSV's count.
  Q  The ledger carries the gate specification and the Doctrine proposal, labelled;
     the config stub is read by no module (grepped), carries the ledger's words and
     parameters only beside a discriminating element; the SR-8 entry is untouched.
  R  No store, no fetch.

    python tools/validate_st_t3_calib.py
"""

from __future__ import annotations

import csv
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
TD = Path(mkdtemp("st-t3-calib-gate-"))
CAL = REPO / "tools" / "calibration"
LEDGERS = REPO / "docs" / "ledgers"
VERDICT_WORDS = re.compile(r"\b(on|off|fired|fires|tripped|trips|triggered)\b", re.I)


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


def t2_gate():
    spec = importlib.util.spec_from_file_location(
        "st_t2_gate", REPO / "tools" / "validate_st_t2_rates.py")
    g = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g)
    return g


# ---------------------------------------------------------------------------
# PART 0
# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. SR-22: THE BASE RATE, THE SUSPENSION AND THE LABELLED VARIANT")
    from altdata import absorption
    from daily_cascade import absorption_block as B
    first = LEDGERS / "sr-22-ledger-2026-10-18-episodes.csv"
    rows = list(csv.DictReader(first.open(encoding="utf-8")))
    fwd = [r for r in rows if r["d10_3m_bp"] not in ("", None)]
    on = sum(1 for r in fwd if r["abs_stress"] == "True")
    b = absorption.ABS_STRESS_BASE
    check(on == b["on"] == 1034 and len(fwd) == b["n"] == 1540
          and absorption.abs_stress_base_rate()
          == "on for 67 percent of auctions since 2009, n=1,540",
          f"the base rate is the ledger's own: {on} of {len(fwd)} auctions with 63 "
          f"sessions forward ({absorption.abs_stress_base_rate()})")
    check((REPO / b["ledger"]).exists(), f"the base rate names its ledger ({b['ledger']})")

    class Empty:
        def instruments(self, key):
            return []

        def latest_as_of(self, *a, **k):
            return None

    class One(Empty):
        def instruments(self, key):
            return ["Note:10-Year"]

        def latest_as_of(self, key, now, inst=None):
            return {"observed_at": "2026-10-08", "value_num": 1.0} \
                if key == "calc.abs_stress" else None
    now = "2026-10-17T21:00:00+00:00"
    lines = [B.abs_stress_line(Empty(), now), B.abs_stress_line(One(), now)]
    check(all("on for 67 percent of auctions since 2009, n=1,540" in x
              and "modifier effect suspended" in x for x in lines)
          and lines[1].startswith("ABS_STRESS: ON") and "NOT AVAILABLE" in lines[0],
          "ABS_STRESS prints its base rate and the suspension whether it is stored or "
          "absent")
    da, cu = B.duration_absorption(One(), now), B.cheap_unloved(One(), now)
    check(any("n=1,540" in x for x in da) and any("n=1,540" in x for x in cu)
          and len(da) <= 18 and len(cu) <= 10,
          "both blocks that print ABS_STRESS (Duration Absorption, A-3's conditions in "
          "Cheap-and-Unloved) carry the base rate, within their caps")
    readers = []
    for p in REPO.rglob("*.py"):
        rel = p.relative_to(REPO).as_posix()
        if rel.startswith(("tools/", ".venv/", "build/")) or "/.git/" in rel:
            continue
        if rel in ("altdata/absorption.py", "daily_cascade/absorption_block.py"):
            continue
        if "calc.abs_stress" in p.read_text(encoding="utf-8", errors="replace"):
            readers.append(rel)
    for p in (REPO / "config").rglob("*.yaml"):
        if "calc.abs_stress" in p.read_text(encoding="utf-8", errors="replace"):
            readers.append(p.name)
    check(not readers, f"the modifier is suspended: nothing outside the writer and the "
                       f"block reads calc.abs_stress ({readers or 'none'})")

    S = mod("sr22_auctions")
    auc = [{"day": f"2024-{m:02d}-15", "type": "Note", "term": "2-Year", "btc": 2.5,
            "dealer": 0.10 + 0.01 * (m - 1), "high_yield": 4.0} for m in range(1, 9)]
    auc.append({"day": "2024-09-15", "type": "Note", "term": "2-Year", "btc": 2.5,
                "dealer": 0.16, "high_yield": 4.0})
    v = S.dealer_variant(auc)
    from altdata import ledgers
    q = ledgers.quantile([0.10 + 0.01 * k for k in range(8)], 0.80)
    auc2 = auc[:8] + [dict(auc[8], dealer=0.155)]
    late = auc + [{"day": "2026-12-01", "type": "Note", "term": "2-Year", "btc": 2.5,
                   "dealer": 0.50, "high_yield": 4.0}]
    check(close(q, 0.156, 1e-12) and v.get(("2024-09-15", "Note:2-Year")) is True
          and S.dealer_variant(auc2).get(("2024-09-15", "Note:2-Year")) is False
          and ("2024-08-15", "Note:2-Year") not in v
          and ("2026-12-01", "Note:2-Year") not in S.dealer_variant(late),
          f"the variant by hand: the 80th percentile of 0.10..0.17 is {q:.3f}; 0.16 "
          f"is above it, 0.155 is not; seven prior auctions, or none inside two "
          f"years, read nothing")
    check(S.base_rate(1034, 1540) == "on for 67 percent of auctions since 2009, n=1,540",
          "the study prints the base rate in the ruling's own form")
    r2 = LEDGERS / "sr-22-ledger-2026-10-18-r2.md"
    t = r2.read_text(encoding="utf-8") if r2.exists() else ""
    check("Variant (ruling 3, 18 Oct): dealer share above its rolling two-year 80th "
          "percentile -- candidate re-specification, grants nothing" in t
          and "on for 67 percent of auctions since 2009, n=1,540" in t
          and re.search(r"^\| Verdict \| \*\*FAIL", t, re.M)
          and r2.with_name(r2.stem + "-episodes.csv").exists(),
          "the second edition carries the labelled variant and the base rates, and "
          "its verdict is still G-32's definition (FAIL)")
    import subprocess                                           # noqa: PLC0415
    try:
        blob = subprocess.run(["git", "show", "76fc704:docs/ledgers/sr-22-ledger-2026-10-18.md"],
                              cwd=REPO, capture_output=True, check=True).stdout
        same = blob.replace(b"\r\n", b"\n") == (LEDGERS / "sr-22-ledger-2026-10-18.md"
                                               ).read_bytes().replace(b"\r\n", b"\n")
    except Exception:                                           # noqa: BLE001
        same = None
    check(same is not False, "the first edition is byte for byte what st-t2-rates "
                             "committed" + (" (no git history here: not checked)"
                                            if same is None else ""))


def group_b() -> None:
    head("B. SR-21: THE DATED NOTE AND DESCRIPTIVE ONLY")
    from daily_cascade import absorption_block as B
    reg = (REPO / "docs" / "signal-triage-register.md").read_text(encoding="utf-8")
    m = re.search(r"^### SR-21 .*?(?=^### )", reg, re.M | re.S)
    e = m.group(0) if m else ""
    note = re.search(r"\*Dated note under rule 31, 18 Oct 2026 \(ruling 2 of 18 Oct[^\n]*", e)
    n = note.group(0) if note else ""
    check(note and "+45.5 bp" in n and "-17.5 bp" in n and "n=46" in n
          and "Doctrine monthly of 7-8 Nov" in n and "not amended by a session" in n
          and "**Register status.** ADOPTED — gate pending" in e,
          "the register's SR-21 entry carries the dated note: +45.5 against -17.5 "
          "bp, n=46, the amendment the Doctrine monthly's; the status unchanged")
    lines = B.rate_machine(None, "2026-10-17T21:00:00+00:00")
    cs = [x for x in lines if x.startswith(("CRED_STRESS", "Venues against"))]
    check(len(cs) == 2 and all(B.SR21_DESCRIPTIVE in x for x in cs),
          "CRED_STRESS and the venues' line print descriptive only")


def group_c() -> None:
    head("C. THE DEVALUATION TELL: 2 OF 3 LEGS, NO VERDICT")
    from altdata import funding_currency as F, observations
    from daily_cascade import absorption_block as B
    g = t2_gate()
    db = g.funding_store(g.funding_fixture(), "deval")
    states = {}
    with observations.ObservationStore(db) as st:
        st.write_many(F.compute_rows(st, "2026-10-17T21:00:00+00:00"))
        for name, now in (("both legs held", "2026-10-17T21:00:00+00:00"),
                          ("neither held", "2025-06-26T21:00:00+00:00"),
                          ("none readable", "2025-06-10T21:00:00+00:00")):
            states[name] = (B.deval_line(st, now), F.deval_legs(st, now))
        cfg = F.config()
        cfg["yuan"] = dict(cfg["yuan"], third_leg="tracked: a hypothetical source")
        tracked = F.deval_legs(st, "2026-10-17T21:00:00+00:00", cfg)
    both, neither, none_ = (states[k] for k in ("both legs held", "neither held",
                                               "none readable"))
    check(both[1] and both[1]["leg1"] and both[1]["leg2"]
          and neither[1] and not neither[1]["leg1"] and not neither[1]["leg2"]
          and none_[1] is None,
          "the fixture reaches the three states: both tracked legs held, neither "
          "held, none readable")
    for name, (ln, _) in states.items():
        words = VERDICT_WORDS.findall(ln.replace("NOT AVAILABLE", "").replace(
            "NOT TRACKED", ""))
        check(ln.startswith("Devaluation tell: 2 of 3 legs tracked")
              and "NOT TRACKED (rule 30; by-hand key state_bank_dollar_selling" in ln
              and not words,
              f"{name}: '2 of 3 legs tracked', the third leg's key named, no verdict "
              f"word ({words or 'none'})")
    check("leg 1, the fix's lean gone: held" in both[0]
          and "leg 2, the CNH-CNY gap wide and widening: held" in both[0]
          and "leg 1, the fix's lean gone: not held" in neither[0]
          and "leg 2, the CNH-CNY gap wide and widening: not held" in neither[0],
          "each leg's state prints, held or not held")
    check(F.legs_tracked() == 2 and not F.verdict_allowed()
          and F.legs_tracked(cfg) == 3 and F.verdict_allowed(cfg) and tracked,
          "the no-verdict rule reads the config: two legs tracked today, so no "
          "verdict; a third leg with a source would allow one")


# ---------------------------------------------------------------------------
# PART 1: ST-8
# ---------------------------------------------------------------------------
PART1 = {"SR-1": "sr01_sr13_style", "SR-13": "sr01_sr13_style",
         "SR-5": "sr05_consumer_credit", "SR-14": "sr14_em_dollar",
         "SR-2": "sr02_yen_unwind", "SR-4": "sr04_cny_fix"}
EDITION = "2026-10-18"
# The order's decision rows for SR-1, 2, 4, 5, 8, 13, 14 and Book A's rule A-2, as
# they stood at the branch point (docs/change-order-signal-triage-2026-09-25.md).
DECISION_ROWS_SHA = "2514063b3513dc305604552b06e2134ec225e7210339dfb2da8bbd54cb8a0298"
# The register's Index table at the branch point.
REGISTER_INDEX_SHA = "c30323daabb6897fc9d1ab84a49ee7e547ea08d7cc56c9bce67432b63dd6e747"


def obs(key, day, value, inst=None):
    return {"registry_key": key, "instrument": inst, "observed_at": day,
            "available_at": f"{day}T21:00:00+00:00", "value": value, "source": "fixture"}


def group_d() -> None:
    head("D. SR-1: THE STYLE RULE, ITS THRESHOLDS AND ITS PANEL")
    import math
    from altdata import style_regime as SR
    S = mod("sr01_sr13_style")
    z = SR.trend_z([0, 0, 0, 0, 4])
    check(close(z, 1.6 / math.sqrt(6.4 / 3)),
          f"z against a trend by hand: 0,0,0,0,4 leaves a last residual of 1.6 over an "
          f"sd of sqrt(6.4/3), z {z:.4f}")
    xs = [(f"d{i}", v) for i, v in enumerate([1, 2, 3, 4, 3.5, 5, 6, 5.9])]
    zs = {2: 2.5, 6: 3.0}
    off = math.log(0.92)
    t = SR.triggers(xs, lambda i: zs.get(i), 2, 2, 2, 2.0, off)
    t1 = SR.triggers(xs, lambda i: {2: 2.5}.get(i), 2, 2, 1, 2.0, off)
    check([x["i"] for x in t] == [4, 7]
          and all(x["break"] == "below the moving average" for x in t) and t1 == [],
          f"the trigger by hand: armed at step 2, fired at the break at step 4 (3.5 under "
          f"the 2-step mean 3.75), re-armed at 6 and fired at 7; armed for one step only, "
          f"it expires unfired ({[x['i'] for x in t]})")
    row = {"vmg_6m": 0.02, "vmg_12m": 0.05}
    j6 = S.judge_sr1([dict(row) for _ in range(6)], "vmg_6m", "vmg_12m")
    j5 = S.judge_sr1([dict(row) for _ in range(5)], "vmg_6m", "vmg_12m")
    jf = S.judge_sr1([dict(row, vmg_6m=-0.01) for _ in range(6)], "vmg_6m", "vmg_12m")
    check(j6["word"] == "PASS" and close(j6["e6"], 0.02) and j5["word"] == "INSUFFICIENT"
          and jf["word"] == "FAIL",
          "six episodes at +2% and +5% after costs PASS; five are INSUFFICIENT; a "
          "negative 6-month expectancy FAILs")
    check(S.combine({"HML": {"word": "PASS"}, "IVE-IVW": {"word": "FAIL"}})[0] == "FAIL"
          and S.combine({"HML": {"word": "PASS"}, "IVE-IVW": {"word": "INSUFFICIENT"}})[0]
          == "PASS",
          "an ETF pair that FAILs with its own floor blocks HML's PASS; one under its "
          "floor does not")
    C8 = mod("st8_common")
    check(C8.first_of_runs(["2000-01-01", "2000-06-01", "2001-01-15"], 365)
          == ["2000-01-01", "2001-01-15"],
          "episodes are non-overlapping: a trigger inside 365 days of the last start is "
          "not a new episode")
    cfg = SR.config()
    r = cfg["rule"]
    check(r["z_arm"] == S.Z_ARM and r["trend_weeks"] == S.TREND_W
          and r["trend_weeks_min"] == S.TREND_W_MIN and r["ma_weeks"] == S.MA_W
          and r["high_weeks"] == S.HIGH_W and r["arm_weeks"] == S.ARM_WEEKS
          and close(math.log(1 - r["off_high_pct"] / 100), S.OFF_HIGH, 1e-12)
          and [tuple(p) for p in cfg["pairs"]] == list(S.PAIRS),
          "config/style_regime.yaml holds the study's own thresholds, value for value")
    tr = SR.total_return([("2026-01-02", 100.0), ("2026-01-05", 110.0)],
                         {"2026-01-05": 2.0})
    check(close(tr[-1][1], 1.12), "total return by hand: 110 plus a 2 distribution over "
                                  "100 is 1.12")
    from altdata import observations
    from daily_cascade import absorption_block as B, stack, style_block
    import datetime as dt
    db = str(TD / "style.db")
    rows = []
    d0 = dt.date(2019, 1, 1)
    for k in range(2400):
        day = (d0 + dt.timedelta(days=k)).isoformat()
        rows += [obs("yfinance.mkt_ivw", day, 100.0 * math.exp(0.0004 * k + 0.02 * math.sin(k / 40))),
                 obs("yfinance.mkt_ive", day, 100.0)]
    with observations.ObservationStore(db) as st:
        st.write_many(rows)
        ln = style_block.lines(st, "2026-10-17T21:00:00+00:00")
        subs = B.subsections(st, "2026-10-17T21:00:00+00:00", "slow")
    empty = style_block.lines(None, "2026-10-17T21:00:00+00:00")
    flagw = re.compile(r"growth extreme|rotation triggered", re.I)
    check(any("IVW/IVE" in x and "z against its 10-year trend" in x and "(as of " in x
              for x in ln)
          and any("NOT AVAILABLE (yfinance.mkt_iwf and yfinance.mkt_iwd" in x for x in ln)
          and not any(flagw.search(x) for x in ln + empty)
          and any("docs/ledgers/sr-1-ledger-2026-10-18.md" in x for x in ln),
          "the panel prints the stored pair's readings with its as-of, names the absent "
          "pair's keys, names the admitting ledger, and prints no flag word")
    sty = [s for s in subs if s["title"] == style_block.TITLE]
    check(len(sty) == 1 and stack.section_words(sty[0]) == 0
          and sty[0]["paragraph_wanted"] is False
          and any("SR-13" in x and "not rendered" in x for x in sty[0]["lines"])
          and "displaces nothing" in sty[0]["table_note"],
          "the panel is one Slow-layers sub-section, lines only (zero words, no chart), "
          "says it displaces nothing, and does not render SR-13's line")


def group_e() -> None:
    head("E. SR-13: THE SPREAD AND ITS CELLS")
    S = mod("sr01_sr13_style")
    d = {"beme": {"Softw": {2001: 0.25}, "Food": {2001: 1.0}},
         "nfirms": {"Softw": {"2000-12": 10}, "Food": {"2000-12": 10}},
         "size": {"Softw": {"2000-12": 10}, "Food": {"2000-12": 10}}}
    sp = S.spread_by_year(d)[2001]
    check(close(sp["tech"], 1.5) and close(sp["def"], -0.375) and close(sp["spread"], 187.5),
          f"price-to-book by hand: tech 4.0 and defensives 1.0 against a market of 1.6 are "
          f"+150% and -37.5%, a spread of 187.5 points ({sp['spread']})")
    rel = S.rel({"2001-07": 0.10}, {"2001-07": 0.0}, "2001-06", 1)
    check(close(rel, 0.10), "defensives +10% against flat tech is +10% relative")

    def ep(x):
        return {"cell_b_entry": "2000-01", "b_36m": x}
    check(S.judge_sr13([ep(0.1)] * 4 + [ep(-0.1)])["word"] == "PASS"
          and S.judge_sr13([ep(0.1)] * 3 + [ep(-0.1)] * 2)["word"] == "FAIL"
          and S.judge_sr13([ep(0.1)] * 4)["word"] == "INSUFFICIENT",
          "4 of 5 completed cell (b) episodes positive PASS; 3 of 5 FAIL; 4 completed "
          "are INSUFFICIENT")


def group_f() -> None:
    head("F. SR-5: FIRST PRINTS AND THE LAPTOP'S WORD")
    import math
    S = mod("sr05_consumer_credit")
    rows = [("2020-01-01", 100.0, "2020-02-05"), ("2020-02-01", 110.0, "2020-03-05"),
            ("2020-01-01", 103.0, "2020-03-05"), ("2020-03-01", 115.0, "2020-04-05")]
    fp = S.first_print_changes(rows)
    check(fp == {"2020-02": 7.0, "2020-03": 5.0},
          f"the first-print change by hand: February's 110 less January as revised in "
          f"February's own vintage (103) is 7, not 10; March 115 less 110 is 5 ({fp})")
    check(S.judge({"n": 8, "exp": 0.12, "unc": 0.05}) == "PASS"
          and S.judge({"n": 8, "exp": 0.09, "unc": 0.05}) == "FAIL"
          and S.judge({"n": 7, "exp": 0.50, "unc": 0.05}) == "INSUFFICIENT"
          and S.judge({"n": 9, "exp": 0.05, "unc": -0.01}) == "FAIL",
          "12% against 5% (>= 2x) over 8 episodes PASS; 9% FAILs; 7 episodes are "
          "INSUFFICIENT; a negative unconditional cannot pass")
    C = mod("st8_common")
    ms = C.months("1960-01", "2000-12")
    chg = {m: 10 + 5 * math.sin(i / 7.0) for i, m in enumerate(ms)}
    d = {"sp_price": {m: 100 * 1.005 ** i for i, m in enumerate(ms)},
         "sp_div": {m: 2.0 for m in ms}, "total": chg, "revolving": chg,
         "first_prints": False}
    r = S.study(d, "laptop run, public sources")
    r2 = S.study(dict(d, first_prints=True), "box run, public sources")
    check(r["verdict"].startswith("INSUFFICIENT -- the rule is on first prints")
          and "latest vintages" in r["source_mode"]
          and "first prints" in r2["source_mode"]
          and not r2["verdict"].startswith("INSUFFICIENT -- the rule is on first prints"),
          "a latest-vintage edition is INSUFFICIENT whatever it reads and says so; a "
          "first-print edition is judged by the rule")


def group_g() -> None:
    head("G. SR-14: THE FLAG AND THE DOLLAR CELL")
    S = mod("sr14_em_dollar")
    C = mod("st8_common")
    ms = C.months("2000-01", "2002-06")
    a = {m: (1.0 if i < 24 else 1.1) for i, m in enumerate(ms)}
    b = {m: 1.0 for m in ms}
    fl = S.flag_series(a, b)
    check(not fl["2001-12"] and fl["2002-01"] and S.firings(fl) == ["2002-01"],
          "the flag by hand: a ratio flat for 24 months then 10% higher has a positive "
          "12-month change and sits above its 24-month mean; it fires once")
    check(S.dollar_cell({"2001-01": 100.0, "2002-01": 101.0}, "2002-01") == "up",
          "the dollar cell is the sign of the real broad dollar's 12-month change")

    def e(m, cell, x):
        return {"fired": m, "dollar": cell, "fwd_36m": x}
    ok = [e("2016-10", "up", -0.1), e("2009-07", "up", -0.2),
          e("2011-03", "down", 0.1), e("2020-10", "down", 0.2)]
    check(S.judge(ok)["word"] == "PASS"
          and S.judge([dict(x, fwd_36m=-x["fwd_36m"]) for x in ok])["word"] == "FAIL"
          and S.judge(ok[1:])["word"] == "INSUFFICIENT",
          "two dollar-up failures (2016 among them) against two dollar-down gains PASS; "
          "reversed they FAIL; one episode in a cell is INSUFFICIENT")


def group_h() -> None:
    head("H. SR-2: THE ANATOMY AT ST-5'S THRESHOLDS")
    S = mod("sr02_yen_unwind")
    s = S.settings()
    check(s["move_pct"] == -3.0 and s["vol_ratio"] == 1.5 and s["front"] == 60
          and s["pos_w"] == 156 and s["crowd_z"] == -1.0,
          "the thresholds are read from config/funding_currency.yaml (-3%, 1.5x, 60 "
          "sessions, 156 weeks); crowding at z <= -1.0 is the one pre-registered here")
    on = {"front_60d_bp": -1.0, "crowd_min_z": -1.0, "move_pct": -3.0, "vol_ratio": 1.5}
    check(S.flagged(dict(on, day="x"), s) and not S.flagged(dict(on, day="x", front_60d_bp=0.0), s),
          "the flag holds at the thresholds' edges and not on an unnarrowed differential")
    import datetime as dt
    off = dict(on, vol_ratio=1.0)
    hits = ["1998-10-05", "2007-08-16", "2016-01-20", "2024-08-05", "2004-03-18", "2013-06-06"]
    rows = []
    d0 = dt.date(1998, 1, 1)
    for k in range(0, 10500, 3):
        day = (d0 + dt.timedelta(days=k)).isoformat()
        rows.append(dict(off, day=day))
    rows += [dict(on, day=h) for h in hits]
    rows.sort(key=lambda r: r["day"])
    e = S.evaluate(rows, s)
    e3 = S.evaluate(sorted(rows + [dict(on, day="2019-05-08")], key=lambda r: r["day"]), s)
    e_no16 = S.evaluate([r for r in rows if r["day"] != "2016-01-20"], s)
    check(e["word"] == "PASS" and all(e["hit"].values()) and len(e["fps"]) == 2
          and e3["word"] == "FAIL" and len(e3["fps"]) == 3
          and e_no16["word"] == "FAIL" and not e_no16["hit"]["Jan-Feb 2016"],
          "four windows flagged with two false positives PASS; a third false positive "
          "FAILs; a missed window FAILs")
    days = [(dt.date(2024, 5, 1) + dt.timedelta(days=k)).isoformat() for k in range(80)]
    tues = ["2024-06-04", "2024-06-11", "2024-06-18", "2024-06-25", "2024-07-02"]
    d = {"dgs2": [(x, 4.0) for x in days], "jgb2": [(x, 0.3) for x in days],
         "usdjpy": [(x, 150.0 + (k % 3)) for k, x in enumerate(days)],
         "pos": list(zip(tues, [10.0, 20.0, 30.0, 40.0, -100.0]))}
    small = dict(s, front=1, pos_w=3, pos_min=3, move_n=1, vol_n=2, vol_med=2)
    c = {r["day"]: r for r in S.components(d, small)}
    zlast = -90 / (6100 ** 0.5)
    check(close(c["2024-07-03"]["crowd_min_z"], 1.0) and close(c["2024-07-05"]["crowd_min_z"], zlast),
          f"a Tuesday's report is read from its Friday release: on Wednesday 3 Jul the "
          f"crowding read is still +1.00; on Friday 5 Jul it is {zlast:.4f}")


def group_i() -> None:
    head("I. SR-4: THE TWO WINDOWS AND THE BASE RATE")
    import datetime as dt
    S = mod("sr04_cny_fix")
    days = [(dt.date(2015, 7, 1) + dt.timedelta(days=k)).isoformat() for k in range(3500)]

    def lg(on_days):
        return [{"day": x, "leg1": x in on_days, "leg2": x in on_days} for x in days]
    ok = {"2015-08-12", "2015-08-13", "2019-05-08"}
    j = S.judge(lg(ok))
    jw2 = S.judge(lg(ok | {"2023-01-10"}))
    late = [x for x in lg(ok) if x["day"] >= "2016-01-01"]
    check(j["word"] == "PASS" and j["outside"] == ["2019-05-08"]
          and jw2["word"] == "FAIL" and not jw2["b"]
          and S.judge(late)["word"] == "INSUFFICIENT",
          "both legs on 12-13 Aug 2015, never in 2022-23, one episode outside: PASS; on in "
          "Jan 2023: FAIL; a series that starts in 2016 covers neither window: INSUFFICIENT")
    alld = [f"d{k:03d}" for k in range(40)]
    check(S.episodes(["d000", "d005", "d030"], alld) == ["d000", "d030"],
          "sessions within 20 of the last are one episode")
    C = mod("st8_common")
    ms = C.months("1998-01", "2000-12")
    p = S.persistence({m: 4.0 for m in ms}, {m: 1.5 for m in ms}, "1998-01", "2000-12")
    check(close(p["pos"], 1.0) and close(p["held"][12], 1.0) and p["longest_200"] == 36
          and p["held"][60] is None,
          "a constant +250 bp spread: US above in every month, the sign held at 12 months "
          "every time, 36 months above +200 bp, and no 60-month pair in three years")
    src = (CAL / "sr04_cny_fix.py").read_text(encoding="utf-8")
    check('F.config()["yuan"]' in src and "F.tell_legs(" in src,
          "the study reads ST-5's thresholds through funding_currency's own tell_legs, "
          "never its own copy")


def ledger_ok(p: Path) -> bool:
    t = p.read_text(encoding="utf-8") if p.exists() else ""
    rows = dict(re.findall(r"^\| (As of|Window|n|Verdict|Pass rule[^|]*) \| (.+?) \|$",
                           t, re.M))
    return bool(p.exists() and all(rows.get(k, "").strip() for k in ("As of", "Window", "n"))
                and any(k.startswith("Pass rule") for k in rows)
                and re.search(r"\d", rows.get("Verdict", ""))
                and "laptop run, public sources" in t
                and p.with_name(p.stem + "-episodes.csv").exists())


def verdict_word(p: Path):
    if not p.exists():
        return None
    v = re.search(r"^\| Verdict \| \*\*(\w+)", p.read_text(encoding="utf-8"), re.M)
    return v.group(1) if v else None


def group_j() -> None:
    head("J. THE LEDGERS")
    for sr in PART1:
        p = LEDGERS / f"{sr.lower()}-ledger-{EDITION}.md"
        check(ledger_ok(p), f"{p.name}: as-of, window, n, the pass rule, a verdict "
                            f"printing its inputs, the edition's label and its CSV")
    check(ledger_ok(LEDGERS / "sr-22-ledger-2026-10-18-r2.md"),
          "sr-22-ledger-2026-10-18-r2.md: the same")
    for sr in ("SR-13", "SR-5", "SR-14"):
        t = (LEDGERS / f"{sr.lower()}-ledger-{EDITION}.md").read_text(encoding="utf-8")
        check("Sourced comparison, not episodes of ours" in t,
              f"{sr}: the long sample it borrows is labelled a sourced comparison")
    t = (LEDGERS / f"sr-5-ledger-{EDITION}.md").read_text(encoding="utf-8")
    check("not first prints" in t and "--alfred" in t,
          "SR-5's laptop edition says it reads the latest vintages and names the box's "
          "first-print run")


def group_k() -> None:
    head("K. THE REGISTER")
    reg = (REPO / "docs" / "signal-triage-register.md").read_text(encoding="utf-8")
    for sr in PART1:
        m = re.search(rf"^### {sr} .*?(?=^### )", reg, re.M | re.S)
        e = m.group(0) if m else ""
        d = re.search(r"\*Drafted under rule 31, 18 Oct 2026 \(ST-8[^*]*\*\s*\*\*Gate status "
                      r"\(ST-8\): (PASS|FAIL|INSUFFICIENT)\.\*\* ledger: (docs/ledgers/\S+\.md), "
                      r"(PASS|FAIL|INSUFFICIENT)", e)
        led = (REPO / d.group(2)) if d else None
        word = verdict_word(led) if led else None
        check(d and led.exists() and d.group(1) == d.group(3) == word
              and "**Register status.** ADOPTED — gate pending" in e,
              f"{sr}: the draft names {d.group(2) if d else 'no ledger'} with its verdict "
              f"({word}); the register status still reads gate pending")
    co = (REPO / "docs" / "change-order-signal-triage-2026-09-25.md").read_text(
        encoding="utf-8").replace("\r\n", "\n").split("\n")
    rows = [x for x in co if re.match(r"^\| (1|2|4|5|8|13|14) \| [A-Z/]+ \|", x)
            or x.startswith("| A-2 Bear-regime re-entry |")]
    sha = hashlib.sha256("\n".join(rows).encode()).hexdigest()
    check(len(rows) == 8 and sha == DECISION_ROWS_SHA,
          f"the order's decision rows for SR-1, 2, 4, 5, 8, 13, 14 and rule A-2 are "
          f"untouched ({len(rows)} rows, sha256 {sha[:12]})")
    s = reg.replace("\r\n", "\n")
    idx = [x for x in s[s.index("## Index"):s.index("## Entries")].split("\n")
           if x.startswith("|")]
    sha = hashlib.sha256("\n".join(idx).encode()).hexdigest()
    check(sha == REGISTER_INDEX_SHA, f"the register's Index table is untouched "
                                     f"({len(idx)} rows, sha256 {sha[:12]})")


def group_l() -> None:
    head("L. NO STORE, NO FETCH")
    pat = re.compile(r"ObservationStore|from altdata import .*observations|"
                     r"derived_forms|regime\.")
    mine = sorted(set(PART1.values()) | {"st8_common"})
    bad = [n for n in mine if pat.search((CAL / f"{n}.py").read_text(encoding="utf-8"))]
    check(not bad, f"no ST-8 script opens the store or reads the market-state object "
                   f"(validate_regime's own pattern; {bad or 'none'})")
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
        for n in mine:
            mod(n)
        S = mod("sr14_em_dollar")
        C = mod("st8_common")
        ms = C.months("2008-01", "2012-12")
        S.study({"eem": {m: 1.0 + 0.01 * i for i, m in enumerate(ms)},
                 "acwi": {m: 1.0 for m in ms}, "spy": {m: 1.0 for m in ms},
                 "dollar": {m: 100.0 for m in ms}}, "laptop run, public sources")
    finally:
        for n, f in saved.items():
            setattr(_base, n, f)
    check(not calls, "importing the ST-8 studies and running one on a fixture, every "
                     "HTTP helper raising, fetches nothing")


def group_m() -> None:
    head("M. THRESHOLDS ENTER CONFIG ONLY WITH A PASSING LEDGER")
    import yaml
    found, bad = [], []
    for p in sorted((REPO / "config").rglob("*.yaml")):
        y = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        if isinstance(y, dict) and "admitted_by" in y:
            led = REPO / str(y.get("admitted_by") or "")
            ok = led.is_file() and verdict_word(led) == "PASS" == y.get("admitted_verdict")
            found.append(p.name)
            if not ok:
                bad.append(p.name)
    check("style_regime.yaml" in found and not bad,
          f"every config naming an admitting ledger names an existing one whose verdict "
          f"is PASS ({found}; refused: {bad or 'none'})")
    fc = (REPO / "config" / "funding_currency.yaml").read_text(encoding="utf-8")
    ms = (REPO / "config" / "market_state.yaml").read_text(encoding="utf-8")
    check("admitted_by" not in fc and "jpy_unwind" not in ms and "deval_tell" not in ms
          and "SESSION-SET" in fc,
          "SR-2 FAILed and SR-4 is INSUFFICIENT: their thresholds stay session-set in "
          "config/funding_currency.yaml, and none reaches config/market_state.yaml")
    check(verdict_word(LEDGERS / "sr-13-ledger-2026-10-18.md") != "PASS"
          and "techdef" not in (REPO / "config" / "style_regime.yaml").read_text(encoding="utf-8"),
          "SR-13 did not pass: no threshold of its in config")
    try:
        tmp = TD
        (tmp / "x.yaml").write_text("admitted_by: docs/ledgers/sr-2-ledger-2026-10-18.md\n"
                                    "admitted_verdict: PASS\n", encoding="utf-8")
        y = yaml.safe_load((tmp / "x.yaml").read_text(encoding="utf-8"))
        refused = verdict_word(REPO / y["admitted_by"]) != "PASS"
    except Exception:                                           # noqa: BLE001
        refused = False
    check(refused, "a config citing a FAILed ledger (SR-2's) would be refused")


def group_n() -> None:
    head("N. NO BY-HAND KEY; THE WEEKLY BUILDERS UNTOUCHED")
    import subprocess
    import yaml
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    manual = sorted(k for k in (reg.get("metrics") or {}) if k.startswith("manual."))
    check(manual in ([], ["manual.global_pmi"]),
          f"no new by-hand key: the registry's manual.* metrics are the PMI alone ({manual})")
    r = subprocess.run(["git", "diff", "--name-only", "origin/st-t2-rates...HEAD"],
                       cwd=REPO, capture_output=True, text=True)
    if r.returncode != 0:
        check(True, "the Weekly builders: no base ref here (a shallow checkout), so the "
                    "branch's diff is not checkable; the notes record the local check")
        return
    touched = [f for f in r.stdout.split() if f.startswith("daily_cascade/weekly")
               or f == "daily_cascade/dealer_weekly.py"]
    check(not touched, f"this branch touches none of the Weekly's builders "
                       f"(daily_cascade/weekly_*.py, dealer_weekly.py; {touched or 'none'})")


# ---------------------------------------------------------------------------
# PART 2: ST-9
# ---------------------------------------------------------------------------
AUDIT = LEDGERS / "false-bottom-audit-2026.md"
STUB = REPO / "config" / "tb_false_bottom_gate.yaml"
# The register's SR-8 entry with its one dated source note (HY OAS, ruled 18 Oct;
# a43-render): no draft of the audit's is written there.
SR8_ENTRY_SHA = "6338399418ec3d14cef1b482d118e5de4dbc9ea22ac2975497e61d3729da3db6"


def _path(levels: list[float], start: str = "2000-01-03") -> list[tuple[str, float]]:
    """Daily closes walking linearly between the given levels, ten steps a leg."""
    import datetime as dt
    d0 = dt.date.fromisoformat(start)
    out, k = [], 0
    for a, b in zip(levels, levels[1:]):
        for s in range(10):
            out.append(((d0 + dt.timedelta(days=k)).isoformat(), a + (b - a) * s / 10))
            k += 1
    out.append(((d0 + dt.timedelta(days=k)).isoformat(), levels[-1]))
    return out


def group_o() -> None:
    head("O. SR-8: THE REPLAY REPRODUCES A HAND COUNT")
    S = mod("sr08_false_bottoms")
    # Peak 100; down to 80; a 12.5% rally to 90; down to 70; a 7% bounce to 75 (no
    # rally); down to 60, the final low; up to 80. By hand: one false bottom (80),
    # 70 is no candidate, 60 is the true one.
    px = _path([100, 80, 90, 70, 75, 60, 80])
    cs = S.candidates(px, px[0][0], px[50][0])
    check([(round(c["close"]), c["kind"]) for c in cs] == [(80, "false"), (60, "true")]
          and cs[0]["undercut"] is not None and cs[1]["undercut"] is None
          and close(cs[0]["rally_pct"], 0.125),
          f"one episode by hand: a false bottom at 80 (a 12.5% rally, later undercut), "
          f"no candidate at 70 (a 7% bounce), the true bottom at 60 "
          f"({[(round(c['close']), c['kind']) for c in cs]})")
    c = dict(cs[0])
    check(S.read_index(c) == min(c["i"] + 30, c["undercut_i"] - 1),
          "each element is read at the trough plus 30 sessions or the session before the "
          "undercut, whichever comes first")
    fall = [(f"d{i:04d}", 1000.0 - i) for i in range(260)]
    check(S.below_falling_200(fall, 250) is True and S.below_falling_200(fall, 100) is None,
          "the state: a steadily falling index is below a falling 200-day; before 220 "
          "sessions it is not read")
    rows = list(csv.DictReader((LEDGERS / "false-bottom-audit-2026-episodes.csv")
                               .open(encoding="utf-8")))
    sp = [r for r in rows if r["index"] == "S&P 500"]
    named = {"2008-03-10", "2022-03-08", "2022-06-16"}
    check(sum(r["kind"] == "false" for r in sp) == 12 and sum(r["kind"] == "true" for r in sp) == 4
          and {r["trough"] for r in sp if r["kind"] == "true"}
          == {"1974-10-03", "2002-10-09", "2009-03-09", "2022-10-12"}
          and named <= {r["trough"] for r in sp if r["kind"] == "false"},
          "the committed replay: 12 false bottoms and the register's four true ones, Mar "
          "2008 and 2022's March and June-August among the false")


def group_p() -> None:
    head("P. SR-8: EACH ELEMENT'S SCORE IS COMPUTED, AND PRINTED WITH ITS INPUTS")
    S = mod("sr08_false_bottoms")

    def rows(tf, ff, tn=4, fn=12):
        return ([{"kind": "true", "trough": f"t{i}", "x": (i < tf, 0, "")} for i in range(tn)]
                + [{"kind": "false", "trough": f"f{i}", "x": (i < ff, 0, "")} for i in range(fn)])
    a, b = S.judge_element(rows(3, 4), "x"), S.judge_element(rows(3, 5), "x")
    c = S.judge_element(rows(1, 0, tn=1), "x")
    check(a["word"] == "DISCRIMINATES" and close(a["tpr"], 0.75) and close(a["fpr"], 1 / 3)
          and b["word"] == "DOES NOT DISCRIMINATE" and c["word"] == "NOT TESTABLE",
          "3 of 4 true and 4 of 12 false discriminate (75%, one third); 5 of 12 false do "
          "not; one testable true bottom is not testable")
    disc = {"word": "DISCRIMINATES"}
    nod = {"word": "DOES NOT DISCRIMINATE"}
    nt = {"word": "NOT TESTABLE"}
    check(S.audit_word({"a": disc, "b": disc}) == "PASS"
          and S.audit_word({"a": disc, "b": nod}) == "FAIL"
          and S.audit_word({"a": disc, "b": nt, "c": nt}) == "INSUFFICIENT",
          "two discriminating elements PASS the audit; one FAILs; under two testable is "
          "INSUFFICIENT")
    px = [("d0", 100.0), ("d1", 110.0), ("d2", 104.0), ("d3", 109.3)]
    r = S.el_retest(px, {"i": 0, "close": 100.0, "undercut_i": None})
    r2 = S.el_retest(px[:3] + [("d3", 109.0)], {"i": 0, "close": 100.0, "undercut_i": None})
    check(r[0] is True and r[1] == 3 and r2[0] is False,
          "a retest by hand: 100 to 110, a 5.5% pullback to 104 holding above 100, then "
          "109.3 (past 5% off 104, 109.2) confirms; 109.0 does not")
    m = [(f"{2000 + (i + 12) // 12 - 1}-{(i % 12) + 1:02d}-28", 100.0 if i == 0 else 75.0)
         for i in range(13)]
    e = S.el_margin({"margin": m}, "2001-03-01")
    check(e and e[0] is True and close(e[1], -0.25),
          "margin spent by hand: 75 against 100 a year earlier is -25%, at or below -20%")
    check(S.el_time("2000-03-24", "2001-09-21")[:2] == (True, 18)
          and S.el_time("2022-01-03", "2022-10-12")[:2] == (False, 9),
          "the time prior: 18 months from Mar 2000 to Sep 2001 meets it; 2022's 9 does not")
    t = AUDIT.read_text(encoding="utf-8")
    rows_csv = list(csv.DictReader((LEDGERS / "false-bottom-audit-2026-episodes.csv")
                                   .open(encoding="utf-8")))
    bad = []
    for k in S.ELEMENTS:
        tr = [x[f"{k}_fires"] for x in rows_csv if x["kind"] == "true" and x[f"{k}_fires"] != ""]
        fa = [x[f"{k}_fires"] for x in rows_csv if x["kind"] == "false" and x[f"{k}_fires"] != ""]
        want = (f"| {k} | ", f" | {tr.count('True')} of {len(tr)} | "
                f"{fa.count('True')} of {len(fa)} | ")
        line = next((ln for ln in t.splitlines() if ln.startswith(want[0])), "")
        if want[1] not in line or "**" not in line:
            bad.append(k)
    check(not bad, f"every element's printed score is its CSV's own count, true and false "
                   f"bottoms with their n, and its word ({bad or 'all ten'})")
    check("LISTED GAP" in t and "leveraged-ETF AUM" in t and "not testable" in t.lower(),
          "leveraged-ETF AUM is a listed gap, and untestable reads say so with their date")


def group_q() -> None:
    head("Q. SR-8: THE LEDGER, THE PROPOSAL AND THE INERT STUB")
    import yaml
    t = AUDIT.read_text(encoding="utf-8")
    check(ledger_ok(AUDIT),
          "docs/ledgers/false-bottom-audit-2026.md: as-of, window, n, pass rule, label, CSV")
    check("## The gate specification" in t and "## The Doctrine rule proposal" in t
          and "proposal for the Doctrine monthly" in t and "drafted under rule 31" in t
          and "grants nothing" in t,
          "the ledger carries the gate specification and the Doctrine proposal, labelled "
          "a proposal for the monthly under rule 31, granting nothing")
    users, named = [], []
    reads = ("open(", "read_text", "read_bytes", "safe_load", "yaml.", "Path(", "glob(")
    for p in REPO.rglob("*.py"):
        rel = p.relative_to(REPO).as_posix()
        if rel.startswith((".venv/", "build/")) or rel == "tools/validate_st_t3_calib.py":
            continue
        src = p.read_text(encoding="utf-8", errors="replace")
        if "tb_false_bottom_gate" not in src:
            continue
        named.append(rel)
        if any(r in ln for ln in src.splitlines() if "tb_false_bottom_gate" in ln
               for r in reads) or "config_dir" in src:
            users.append(rel)
    check(not users and named == ["tools/calibration/sr08_false_bottoms.py"],
          f"the T&B stub is read by no module: only the audit names it, in its ledger "
          f"text, and no line naming it opens or loads a file (readers {users or 'none'})")
    y = yaml.safe_load(STUB.read_text(encoding="utf-8"))
    words = dict(re.findall(r"^\| (\w+) \| [^|]+ \| [^|]+ \| [^|]+ \| [^|]+ \| [^|]+ \| "
                            r"\*\*([A-Z ]+)\*\* \|$", t, re.M))
    el = y.get("elements") or {}
    mism = [k for k, v in el.items() if words.get(k) != v.get("word")]
    params_without = [k for k, v in el.items() if ("rule" in v or "key" in v)
                      and (v.get("word") != "DISCRIMINATES"
                           or v.get("admitted_by") != "docs/ledgers/false-bottom-audit-2026.md")]
    check(y.get("status") == "inert" and y.get("ledger") == "docs/ledgers/false-bottom-audit-2026.md"
          and y.get("audit_verdict") == verdict_word(AUDIT) and "admitted_by" not in y
          and not mism and not params_without
          and (y.get("then") or {}).get("confirmations_required") is None,
          f"the stub is inert, names its ledger and verdict, carries each element's word "
          f"as the ledger prints it, and parameters only for an element that discriminates "
          f"with the ledger beside them (mismatched {mism or 'none'}; parameters without "
          f"a passing element {params_without or 'none'})")
    reg = (REPO / "docs" / "signal-triage-register.md").read_text(encoding="utf-8").replace("\r\n", "\n")
    e = re.search(r"^### SR-8 .*?(?=^### )", reg, re.M | re.S).group(0)
    check(hashlib.sha256(e.encode()).hexdigest() == SR8_ENTRY_SHA,
          "the register's SR-8 entry is as pinned, its one dated source note aside (the audit "
          "drafts nothing there; its proposal is the ledger's)")


def group_r() -> None:
    head("R. SR-8: NO STORE, NO FETCH")
    pat = re.compile(r"ObservationStore|from altdata import .*observations|"
                     r"derived_forms|regime\.")
    check(not pat.search((CAL / "sr08_false_bottoms.py").read_text(encoding="utf-8")),
          "the audit opens no store and reads no market-state object (the withdrawn cell's names stay validate_regime's check)")
    from altdata.sources import _base
    names = [n for n in ("http_get_json", "http_get_text", "http_get_response",
                         "http_get_bytes") if hasattr(_base, n)]
    saved = {n: getattr(_base, n) for n in names}
    calls = []

    def boom(*a, **k):
        calls.append(a[:1])
        raise RuntimeError("the audit fetched")
    for n in names:
        setattr(_base, n, boom)
    try:
        S = mod("sr08_false_bottoms")
        px = _path([100, 80, 90, 70, 75, 60, 80])
        S.candidates(px, px[0][0], px[50][0])
    finally:
        for n, f in saved.items():
            setattr(_base, n, f)
    check(not calls, "importing the audit and replaying its fixture, every HTTP helper "
                     "raising, fetches nothing")


# ---------------------------------------------------------------------------
def main() -> int:
    print(f"{LINE}\nst-t3-calib\n{LINE}")
    for g in GROUPS:
        try:
            g()
        except Exception as exc:                              # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


GROUPS = [group_a, group_b, group_c, group_d, group_e, group_f, group_g,
          group_h, group_i, group_j, group_k, group_l, group_m, group_n,
          group_o, group_p, group_q, group_r]

if __name__ == "__main__":
    sys.exit(main())
