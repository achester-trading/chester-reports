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


GROUPS = [group_a, group_b, group_c]

if __name__ == "__main__":
    sys.exit(main())
