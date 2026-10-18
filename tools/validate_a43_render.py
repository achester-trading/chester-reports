#!/usr/bin/env python3
"""
Validation gate: a43-render -- session A's Part 0 of 18 Oct (the rulings on the
ST-8 / ST-9 report, the Massive capture clock, the FlashAlpha writer's
configuration and conventions) and Part 1 (ST-10's rendering rows for ST-4 and
ST-5), where no existing gate is their home. On fixtures; no network, no model,
no live store.

  A  THE RULINGS. SR-1's panel prints HML beside the ETF pairs, each pair's n and
     "under its floor of six", every figure recomputed from the ledger's CSV; the
     gate-status draft carries ruling 1; the two FRED source notes are in the
     register; the Weekly's and the Monthly's HY charts name their series and the
     first day the store holds.

    python tools/validate_a43_render.py
"""

from __future__ import annotations

import csv
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
TD = Path(mkdtemp("a43-render-gate-"))
CAL = REPO / "tools" / "calibration"
LEDGERS = REPO / "docs" / "ledgers"


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


def _num(v):
    return None if v in ("", None) else float(v)


# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. THE RULINGS OF 18 OCT")
    from altdata import labels, style_regime as SR
    from daily_cascade import style_block
    S = mod("sr01_sr13_style")
    rows = list(csv.DictReader((LEDGERS / "sr-1-ledger-2026-10-18-episodes.csv")
                               .open(encoding="utf-8")))
    for r in rows:
        for k in list(r):
            if k.startswith("vmg_"):
                r[k] = _num(r[k])
    hml = [r for r in rows if r["set"] == "HML" and r["episode"] == "True"]
    jh = S.judge_sr1(hml, "vmg_6m", "vmg_12m")
    g = SR.config()["gate_reading"]
    ok = (jh["n"] == g["hml"]["n"] and round(100 * jh["e6"], 1) == g["hml"]["mean_6m_pct"]
          and round(100 * jh["e12"], 1) == g["hml"]["mean_12m_pct"])
    for pair, v in g["pairs"].items():
        jp = S.judge_sr1(S.episodes_of([r for r in rows if r["set"] == pair]),
                         "vmg_26w", "vmg_52w")
        ok = ok and jp["n"] == v["n"] and round(100 * jp["e12"], 1) == v["mean_52w_pct"]
    check(ok and g["floor"] == S.FLOOR,
          f"config/style_regime.yaml's gate reading is the ledger CSV's own: HML n "
          f"{jh['n']} at {100 * jh['e6']:+.1f}% and {100 * jh['e12']:+.1f}%, each pair's n "
          f"and 52-week mean, the floor of {S.FLOOR}")
    ln = style_block.gate_line(SR.config())
    check("HML PASS, n 6" in ln and ln.count("under its floor of six") == 2
          and "IVE-IVW n 3" in ln and "IWD-IWF n 3" in ln and "display only" in ln
          and "Doctrine monthly's (7-8 Nov)" in ln,
          "the panel prints the pairs beside HML, each n with 'under its floor of six', "
          "display only, the rights question the monthly's")
    check(any(x.strip().startswith("The gate (as of the ledger)")
              for x in style_block.lines(None, "2026-10-17T21:00:00+00:00")),
          "the gate line is in the panel")
    reg = (REPO / "docs" / "signal-triage-register.md").read_text(encoding="utf-8")
    e1 = re.search(r"^### SR-1 .*?(?=^### )", reg, re.M | re.S).group(0)
    check("Ruled 18 Oct (ruling 1): the pre-registered pass stands" in e1
          and "under its floor of six" in e1 and "Doctrine monthly of 7-8 Nov" in e1
          and "**Gate status (ST-8): PASS.**" in e1,
          "SR-1's gate-status draft says all of ruling 1, under its label (ruling 2)")
    e4 = re.search(r"^### SR-4 .*?(?=^### )", reg, re.M | re.S).group(0)
    e8 = re.search(r"^### SR-8 .*?(?=^### )", reg, re.M | re.S).group(0)
    check("*Dated note under rule 31, 18 Oct 2026 (a register fact" in e4
          and "IRLTLT01CNM156N" in e4 and "404" in e4
          and "*Dated note under rule 31, 18 Oct 2026 (a register fact" in e8
          and "BAMLH0A0HYM2" in e8 and "2023-10-17" in e8 and "Baa less the 10-year" in e8,
          "the two FRED source changes are dated rule-31 notes: the China 10-year gone "
          "(SR-4) and HY OAS from Oct 2023 with the labelled Baa proxy (SR-8)")
    from daily_cascade import charts
    from monthly_macro import charts as mc
    hy = [(f"{2010 + i // 12}-{i % 12 + 1:02d}-01", 4.0 + 0.01 * (i % 7)) for i in range(120)]
    w3 = charts.w3_panel({"10y": [(d, 4.0) for d, _ in hy]}, hy, "w3", str(TD),
                         hy[-1][0] + "T21:00:00+00:00")
    m5 = mc.m5(hy, "m5", str(TD))
    want = labels.hy_source(hy[0][0])
    check(want in (w3.get("caption") or "") and want in (m5.get("caption") or "")
          and "BAMLH0A0HYM2" in want and "stored from 2010-01-01" in want
          and "2023-10-17" in want,
          f"the Weekly's W3 and the Monthly's M5 captions name the series and the first "
          f"stored day ({want})")
    from altdata import st_r5_rates as R5
    q = {"absent": False, "as_of": "2026-10-16", "ccc_bb_bp": 400.0,
         "ccc_bb_lens": {"percentile": 50.0}, "cosignal": "absent", "cosignal_reason": "x",
         "overlay": "o", "overlay_built": False, "euro_leg": "e",
         "euro_hy": {"oas_bp": 300.0, "as_of": "2026-10-16", "lens": {"percentile": 40.0}},
         "us_hy": {"oas_bp": 290.0, "as_of": "2026-10-16", "lens": {"percentile": 30.0}}}
    try:
        lines = R5.quality_tail_lines(q)
    except Exception:                                           # noqa: BLE001
        lines = []
    check(any(labels.HY_SERIES in x for x in lines),
          "the quality-tail lens's US HY clause names its series")


# ---------------------------------------------------------------------------
GROUPS = [group_a]


def main() -> int:
    print(f"{LINE}\na43-render\n{LINE}")
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


if __name__ == "__main__":
    sys.exit(main())
