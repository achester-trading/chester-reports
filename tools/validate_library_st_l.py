#!/usr/bin/env python3
"""
Validation gate: library-st-l -- the signal-triage order's Slot L (ST-L, the
dated appendices) and Tranche H's one-time items (session B, 19 Oct 2026), where
no existing gate is their home. On fixtures; no network, no model, no live store.

  A  THE HIKING-CYCLE TABLE (tools/calibration/fed_cycles.py). A fixture of the
     target's real steps from 2002 to 2020 reproduces two cycles worked by hand:
     June 2004 to June 2006, 1.00% to 5.25%, +425 bp over 25 months; and December
     2015 to December 2018, the range's midpoint 0.125% to 2.375%, +225 bp over 37
     months. A 50 bp wobble is not a cycle; a rise not yet reversed by 75 bp is
     open; SR-21's rows land inside the cycle they started in; the conditional
     table prints and no all-cycle average does; the ledger writes through
     altdata.ledgers with its as-of, window and n.
  B  THE APPENDICES. Every paper ST-L names that exists on this line carries one
     dated appendix of calibration ledgers, each entry naming a ledger that
     exists, with its as-of, n, verdict and rights consequence as the ledger
     records them; the Disruptive Themes paper carries the evidence-log frame,
     empty; the Digital Assets paper carries the mechanism-watch appendix and the
     one timeless paragraph on proof of useful work.
  C  TRANCHE H'S DOCUMENTS. The Warsh matrix's single edit, the Doctrine #2
     proposals and the Livingston ledger are where the notes say, each a rule-31
     draft; no manual_input entry is created.

    python tools/validate_library_st_l.py
"""

from __future__ import annotations

import datetime as dt
import os
import re
import socket
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "tools" / "calibration"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

TD = Path(gate_mkdtemp("library_st_l_"))
PASS = FAIL = 0
LINE = "=" * 78


def _no_connect(*a, **k):
    raise OSError("validate_library_st_l: no network in a code gate")


socket.socket.connect = _no_connect                             # type: ignore[method-assign]
socket.create_connection = _no_connect                          # type: ignore[assignment]


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


def daily(steps: list[tuple[str, float]], last: str) -> list[tuple[str, float]]:
    """Every calendar day from the first step to `last`, carrying each level."""
    out, i = [], 0
    d, end = dt.date.fromisoformat(steps[0][0]), dt.date.fromisoformat(last)
    cur = steps[0][1]
    while d <= end:
        while i < len(steps) and steps[i][0] <= d.isoformat():
            cur = steps[i][1]
            i += 1
        out.append((d.isoformat(), cur))
        d += dt.timedelta(days=1)
    return out


# The FOMC's target changes, 2002-11 to 2008-12 (DFEDTAR), as published.
TAR = [("2002-11-06", 1.25), ("2003-06-25", 1.00), ("2004-06-30", 1.25),
       ("2004-08-10", 1.50), ("2004-09-21", 1.75), ("2004-11-10", 2.00),
       ("2004-12-14", 2.25), ("2005-02-02", 2.50), ("2005-03-22", 2.75),
       ("2005-05-03", 3.00), ("2005-06-30", 3.25), ("2005-08-09", 3.50),
       ("2005-09-20", 3.75), ("2005-11-01", 4.00), ("2005-12-13", 4.25),
       ("2006-01-31", 4.50), ("2006-03-28", 4.75), ("2006-05-10", 5.00),
       ("2006-06-29", 5.25), ("2007-09-18", 4.75), ("2007-10-31", 4.50),
       ("2007-12-11", 4.25), ("2008-01-22", 3.50), ("2008-01-30", 3.00),
       ("2008-03-18", 2.25), ("2008-04-30", 2.00), ("2008-10-08", 1.50),
       ("2008-10-29", 1.00)]
# The range's upper limit from 2008-12-16 (DFEDTARU; the lower is 25 bp below).
UPPER = [("2008-12-16", 0.25), ("2015-12-17", 0.50), ("2016-12-15", 0.75),
         ("2017-03-16", 1.00), ("2017-06-15", 1.25), ("2017-12-14", 1.50),
         ("2018-03-22", 1.75), ("2018-06-14", 2.00), ("2018-09-27", 2.25),
         ("2018-12-20", 2.50), ("2019-08-01", 2.25), ("2019-09-19", 2.00),
         ("2019-10-31", 1.75), ("2020-03-04", 1.25), ("2020-03-16", 0.25)]


def group_a() -> None:
    import fed_cycles as F                                      # noqa: PLC0415
    head("A. THE HIKING-CYCLE TABLE, COMPUTED BY RULE")
    tar = daily(TAR, "2008-12-15")
    up = daily(UPPER, "2020-12-31")
    lo = [(d, max(0.0, v - 0.25)) for d, v in up]
    months = sorted({d[:7] for d, _ in up} | {d[:7] for d, _ in tar})
    data = {"ff": [], "tar": tar, "tar_l": lo, "tar_u": up,
            "gs10": [(m + "-01", 4.0 + 0.01 * i) for i, m in enumerate(months)],
            "usrec": [(m + "-01", 1.0 if "2007-12" <= m <= "2009-06"
                       or "2020-02" <= m <= "2020-04" else 0.0) for m in months],
            "spx": [(m + "-28", 1000.0 * (1.005 ** i)) for i, m in enumerate(months)],
            "sr21": [{"start": "2016-11-15", "outcome": "conceded"},
                     {"start": "2017-09-01", "outcome": "refused"},
                     {"start": "2010-05-01", "outcome": "refused"}]}
    p = F.policy_rate(data)
    check(p["2004-05"] == 1.00 and p["2004-06"] == 1.25 and p["2008-12"] == 0.125
          and p["2016-01"] == 0.375,
          "the policy rate: the target at month-end to 2008-12-15, the range's "
          "midpoint after it")
    cyc = F.cycles(p)
    want = [{"start": "2004-06", "end": "2006-06", "from_pct": 1.0, "to_pct": 5.25,
             "rise_bp": 425.0, "months": 25, "completed": True},
            {"start": "2015-12", "end": "2018-12", "from_pct": 0.125, "to_pct": 2.375,
             "rise_bp": 225.0, "months": 37, "completed": True}]
    got = [{k: c[k] for k in want[0]} for c in cyc]
    check(got == want,
          f"two cycles worked by hand: 2004-06 to 2006-06, 1.00% to 5.25%, +425 bp over "
          f"25 months; 2015-12 to 2018-12, 0.125% to 2.375%, +225 bp over 37 months "
          f"(got {got})")
    wob = {m: (1.0 if m < "2010-06" else 1.5 if m < "2011-01" else 1.0)
           for m in F.C.months("2009-01", "2012-12")}
    check(F.cycles(wob) == [], "a 50 bp rise and fall is not a cycle (rise under 100 bp)")
    rising = {m: 1.0 + 0.25 * max(0, i - 6) for i, m in
              enumerate(F.C.months("2020-01", "2021-12"))}
    rising["2019-06"] = 2.0
    rising["2019-12"] = 1.0
    op = F.cycles(rising)
    check(len(op) == 1 and op[0]["completed"] is False and op[0]["end"] == "2021-12",
          "a rise not yet reversed by 75 bp is listed open, not completed")
    r = F.study(data, F.C.LAPTOP)
    rows = {x["start"]: x for x in r["episodes"]}
    check(rows["2015-12"]["sr21_conceded"] == 1 and rows["2015-12"]["sr21_refused"] == 1
          and rows["2004-06"]["sr21_conceded"] == 0
          and rows["2004-06"]["recession_within_24m"] is True
          and rows["2004-06"]["months_to_recession"] == 18
          and rows["2015-12"]["months_to_recession"] == 14,
          "SR-21's rows land in the cycle they started in (the 2010 one in none); the "
          "recession column reads USREC: 18 months after June 2006, 14 after December "
          "2018")
    text = "\n".join(r["body"])
    check("| yes | 2 |" in text and "| no | 0 |" in text
          and "average" not in text.replace("no all-cycle average is printed", ""),
          "the conditional table prints, split by a recession within 24 months, and "
          "no all-cycle average does")
    from altdata import ledgers                                 # noqa: PLC0415
    md, cv = ledgers.write_ledger(r, TD / "ledgers", "2026-10-19")
    t = md.read_text(encoding="utf-8")
    check(md.name == "fed-cycles-ledger-2026-10-19.md" and cv is not None and cv.is_file()
          and "| n | 2 |" in t and "NO GATE IN THE ORDER" in t,
          f"the ledger writes through altdata.ledgers with its as-of, window and n: "
          f"{md.name}, {cv.name}")
    src = (REPO / "tools" / "calibration" / "fed_cycles.py").read_text(encoding="utf-8")
    check("open_reader" not in src and "ObservationStore" not in src
          and "load_public" in src,
          "public sources only, as the calibration rule says: the study opens no store")


WP = REPO / "docs" / "whitepapers"
LED = REPO / "docs" / "ledgers"
# ST-L's papers on this line, and the dated appendix each carries.
APPENDICES = {"rates-liquidity": "A", "equities": "C", "currencies": "E", "metals": "F",
              "energy": "E", "credit": "E", "base-rates": "D",
              "positioning-and-flows": "A", "operating-doctrine": "E",
              "portfolio-construction": "A"}


def section(text: str, head_prefix: str) -> str:
    i = text.find(head_prefix)
    if i < 0:
        return ""
    j = text.find("\n## ", i + 1)
    return text[i:j if j > 0 else len(text)]


def ledger_rows(path: Path) -> dict:
    rows = {}
    for ln in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\| (As of|Window|n|Verdict|Rights consequence) \| (.*) \|$", ln)
        if m and m.group(1) not in rows:
            rows[m.group(1)] = m.group(2).strip()
    return rows


def group_b() -> None:
    head("B. ST-L'S DATED APPENDICES, AS THE LEDGERS RECORD THEM")
    faults, entries = [], 0
    for slug, letter in APPENDICES.items():
        text = (WP / f"{slug}-whitepaper.md").read_text(encoding="utf-8")
        sec = section(text, f"## Appendix {letter} — Dated: Calibration ledgers (ST-L")
        if not sec or "(as of 19 October 2026)" not in sec.splitlines()[0] \
                or "Rule-31 draft" not in sec:
            faults.append(f"{slug}: no dated appendix {letter}")
            continue
        for link in re.findall(r"\*\*Ledger:\*\* \[([^\]]+)\]", sec):
            p = LED / link
            if not p.is_file():
                faults.append(f"{slug}: {link} does not exist")
                continue
            r = ledger_rows(p)
            block = sec[sec.index(link):].split("\n### ", 1)[0]
            for k in ("As of", "n", "Verdict", "Rights consequence"):
                want = r.get(k, "").strip("*")
                if want and want not in block:
                    faults.append(f"{slug}: {link}'s {k} is not quoted as recorded")
            entries += 1
    check(not faults and entries >= 30,
          f"every paper ST-L names on this line carries its dated appendix; {entries} "
          f"entries, each quoting its ledger's as-of, n, verdict and rights consequence "
          f"as recorded" + (f" -- {faults[:4]}" if faults else ""))
    dt_ = (WP / "disruptive-themes-whitepaper.md").read_text(encoding="utf-8")
    ev = section(dt_, "## Appendix A — Dated: Evidence log, Factor I and Factor V")
    check(ev and "No entry has been posted yet." in ev and "\n### " not in ev,
          "the Disruptive Themes paper carries the evidence-log frame, empty")
    da = (WP / "digital-assets-whitepaper.md").read_text(encoding="utf-8")
    pouw = section(da.replace("\n### Proof-of-Useful-Work", "\n## Proof-of-Useful-Work"),
                   "## Proof-of-Useful-Work")
    mw = section(da, "## Appendix F — Dated: Mechanism watch, Pearl")
    check(da.count("### Proof-of-Useful-Work") == 1 and pouw
          and not re.search(r"\b(19|20)\d\d\b|Pearl|PRL", pouw)
          and mw and "SM00118" in mw and "not tracked" in mw and "ESTIMATED" in mw,
          "the Digital Assets paper: one timeless paragraph on proof of useful work (no "
          "date, no project) and the dated mechanism-watch appendix")


def group_c() -> None:
    head("C. TRANCHE H'S DOCUMENTS")
    w = (REPO / "docs" / "warsh-matrix-lines.md").read_text(encoding="utf-8")
    ws = section(w, "## Section 2.1.5")
    check(ws and "Rule-31 draft" in ws and all(
        x in ws for x in ("sr-21-ledger-2026-10-18.md", "sr-24-ledger-2026-10-19.md",
                          "fed-cycles-ledger-2026-10-19.md", "rates-driver-2026-09-30-r2.md")),
          "the Warsh matrix's single edit (section 2.1.5) is a rule-31 draft citing the "
          "ledgers it rests on")
    d = (REPO / "docs" / "briefs" / "doctrine-2-proposals-st-l.md").read_text(encoding="utf-8")
    check(all(f"({x}" in d for x in ("SR-3", "SR-9", "SR-18", "SR-8", "SR-22"))
          and "Rule-31 drafts" in d and "7-8 November" in d,
          "the tail-register, 5.25%, projection-rule and two Doctrine notes are proposals "
          "for Doctrine #2, rule-31 drafts")
    for item, f in (("SR-24", "sr-24-ledger-2026-10-19.md"),
                    ("SR-20", "sr-20-ledger-2026-10-19.md"),
                    ("FED-CYCLES", "fed-cycles-ledger-2026-10-19.md")):
        r = ledger_rows(LED / f)
        check(all(r.get(k) for k in ("As of", "Window", "n", "Verdict"))
              and (LED / f.replace(".md", "-episodes.csv")).is_file(),
              f"{item}'s dated ledger carries its as-of, window, n and verdict, with its "
              f"CSV ({f})")
    cal = REPO / "tools" / "calibration"
    src = "".join((cal / f).read_text(encoding="utf-8")
                  for f in ("fed_cycles.py", "sr20_cofer.py", "sr24_livingston.py"))
    check("manual." not in src and "manual_input" not in src
          and "ObservationStore" not in src and "open_writer" not in src,
          "no manual_input entry is created (rule 30), and no study writes the store: "
          "each reads public sources and writes only its dated ledger")


def main() -> int:
    try:
        group_a()
        group_b()
        group_c()
    finally:
        import shutil                                           # noqa: PLC0415
        shutil.rmtree(TD, ignore_errors=True)
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
