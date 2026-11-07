#!/usr/bin/env python3
"""
Validation gate: the annual-review tooling (the library programme's L-5; Audit 2
section 5.1, Instruments 2 and 3). A131, 6 Nov 2026. A fixture paper and a
fixture store only: no network, no live store, no real paper written.

  A  THE FIGURES PARSER on a fixture paper: only dated appendices are read; a
     figure names its series ("(FRED <ID>)" or a backticked registered key), a
     value and its date ("on <date>", "<date> (<value>)"); a threshold "in the
     week of" is not a dated close; the as-of is the heading's.
  B  THE UNRECOMPUTABLE PATH: no series key, a key the pull does not carry, no
     date for the value, a backticked file name (not a series) -- each listed
     with its reason, never guessed.
  C  THE TOLERANCE RULE on a fixture store, read-only: within and beyond by the
     family's tolerance (abs for a rate, rel for a price); a bp figure against a
     series stored in percent; a value stored only after the as-of is not used.
  D  THE FOUR GRADES on synthetic monthly series: holding, weakening, broken and
     re-attached, a range claim, an insufficient window, a claim not in the
     relationship form; a paper without an Appendix A(b) is listed, not failed.
  E  THE OUTPUTS AND THE TARGET: both files written with their tables and count
     lines; the store opened mode=ro and unchanged; no paper written; `all`
     exits 0 even with no store; the Makefile and scripts/make.sh carry
     annual-review and no gate list does.

    python tools/validate_annual_review.py
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import datetime as dt
import hashlib
import random
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

TD = Path(gate_mkdtemp("annual_review_"))
ROOT = TD / "repo"
LINE = "=" * 78
PASS = FAIL = 0
# The clock is pinned to the fixture's day (B106): nothing here reads today.
GATE_NOW = "2026-11-06T22:00:00+00:00"


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


def pin_clock() -> None:
    from altdata import session                                 # noqa: PLC0415
    session.utc_now = lambda: dt.datetime.fromisoformat(GATE_NOW)


def fixture_ids(ar) -> list[tuple[str, str]]:
    """Eight (FRED id, store key) pairs from the real pull, for the synthetic
    relationship series (the values are invented)."""
    fm = ar.fred_map()
    want = ["DGS10", "DFII10", "BAMLH0A0HYM2", "BAMLC0A0CM", "DGS2", "DGS30",
            "T10Y2Y", "VIXCLS", "DTWEXBGS", "T10YIE", "DGS5", "DGS3MO"]
    out = [(i, fm[i]) for i in want if i in fm]
    for i, k in sorted(fm.items()):
        if len(out) >= 8:
            break
        if (i, k) not in out:
            out.append((i, k))
    return out[:8]


def write_paper(ids) -> Path:
    p = ROOT / "docs" / "whitepapers" / "fixture-whitepaper.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    (a1, _), (b1, _), (a2, _), (b2, _), (a3, _), (b3, _), (a4, _), (b4, _) = ids
    p.write_text(f"""# A Fixture Paper (invented: the gate's own)

## Part I

The body is never read: (FRED DGS10) at 9.99% on 5 Oct 2026.

## Appendix A — Notes, undated

(FRED DGS10) closed at 8.88% on 5 Oct 2026, which no instrument reads here.

## Appendix B — Dated: Fixture levels (as of 20 October 2026)

> The 10-year Treasury yield (FRED DGS10) closed at 4.50% on 5 Oct 2026.
> The S&P 500 (`yfinance.mkt_gspc`) closed at 6,000.00 on 6 Oct 2026.
> High-yield spreads (FRED BAMLH0A0HYM2) stood at 350bp on 5 Oct 2026.
> The 10-year (FRED DGS10) closed at 4.60% on 7 Oct 2026, a level stored only later.
> The 10-year (FRED DGS10) traded at or above 4.25% in the week of 5 Oct 2026.
> The 10-year (FRED DGS10) was 4.40% the same day as the long bond, and higher since 1 Oct 2026 (4.10%).

A figure with no series: the index rose 2.5% in the session.

A key outside the pull: (FRED NOSUCHID) at 1.25% on 5 Oct 2026.

A file is not a series: `oneday_10y.yaml` sets 2.5% on 5 Oct 2026.

## Appendix C — Assumptions and Falsifiers

**Mechanisms this paper assumes.** Prices clear, at 1.5% a year.

**(b) Regularities.**

- (FRED {a1}) and (FRED {b1}) move together: positive, 2000 to 2015.
- (FRED {a1}) and (FRED {b1}): a correlation between 0.5 and 1.0, 2000-01 to 2015-12.
- (FRED {a2}) and (FRED {b2}) move together: positive, 2000 to 2015.
- (FRED {a3}) and (FRED {b3}) move together: positive, 2000 to 2015.
- (FRED {a4}) and (FRED {b4}) move together: positive, 2000 to 2015.
- (FRED {a1}) and (FRED {b1}): positive, 1980 to 1985 (before the fixture's data).
- Credit leads equities by about a month, which no row here measures.

**(c) Falsifiers.** Not read by the health check.
""", encoding="utf-8")
    q = ROOT / "docs" / "whitepapers" / "plain-whitepaper.md"
    q.write_text("# A Paper Without the Appendix\n\n## Part I\n\nNothing dated.\n",
                 encoding="utf-8")
    return p


def month_ends(a: str, b: str) -> list[str]:
    out, y, m = [], int(a[:4]), int(a[5:7])
    while f"{y:04d}-{m:02d}" <= b:
        nxt = dt.date(y + (m == 12), m % 12 + 1, 1)
        out.append((nxt - dt.timedelta(days=1)).isoformat())
        y, m = nxt.year, nxt.month
    return out


def series(rng: random.Random, days: list[str], k_of) -> tuple[list, list]:
    """Two random walks whose monthly changes correlate with weight k_of(day)."""
    a = b = 100.0
    xa, xb = [], []
    for d in days:
        e1, e2 = rng.gauss(0, 1), rng.gauss(0, 1)
        k = k_of(d)
        a += e1
        b += k * e1 + (1 - abs(k)) * e2
        xa.append((d, round(a, 6)))
        xb.append((d, round(b, 6)))
    return xa, xb


def build_store(ids) -> str:
    from altdata import observations                            # noqa: PLC0415
    db = str(TD / "store.db")
    rows = []

    def put(key, d, v, avail=None):
        rows.append({"registry_key": key, "instrument": None, "observed_at": d,
                     "available_at": avail or f"{d}T22:00:00+00:00", "value": v,
                     "source": "fred"})
    fm = {"DGS10": "fred.yield_10y", "BAMLH0A0HYM2": "fred.hy_oas"}
    put(fm["DGS10"], "2026-10-05", 4.50, "2026-10-06T21:00:00+00:00")
    put(fm["DGS10"], "2026-10-07", 4.60, "2026-10-25T21:00:00+00:00")   # after the as-of
    put(fm["BAMLH0A0HYM2"], "2026-10-05", 3.51)
    rows.append({"registry_key": "yfinance.mkt_gspc", "instrument": None,
                 "observed_at": "2026-10-06", "available_at": "2026-10-06T21:05:00+00:00",
                 "value": 6050.0, "source": "yfinance"})
    days = month_ends("2000-01", "2026-09")
    rng = random.Random(20261106)
    shapes = [lambda d: 0.9,                                              # holding
              lambda d: 0.9 if d < "2023-10" else 0.25,                   # weakening
              lambda d: 0.9 if d < "2023-10" else -0.8,                   # broken
              lambda d: 0.9 if d < "2016" else (-0.8 if d < "2023-10" else 0.9)]  # re-attached
    for j, shape in enumerate(shapes):
        xa, xb = series(rng, days, shape)
        ka, kb = ids[2 * j][1], ids[2 * j + 1][1]
        for d, v in xa:
            put(ka, d, v)
        for d, v in xb:
            put(kb, d, v)
    with observations.ObservationStore(db) as st:
        st.write_many(rows)
    return db


def group_a_b(ar, cfg, paper) -> None:
    head("A/B. THE FIGURES PARSER AND THE UNRECOMPUTABLE PATH")
    r = ar.parse_figures(paper, cfg)
    figs, unrec = r["figures"], r["unrecomputable"]
    got = {(f["series"], f["date"], f["printed"]) for f in figs}
    check(r["appendices"] == 1, "one dated appendix: the undated one and the body are not read")
    check(("FRED DGS10", "2026-10-05", 4.5) in got
          and ("yfinance.mkt_gspc", "2026-10-06", 6000.0) in got
          and ("FRED BAMLH0A0HYM2", "2026-10-05", 350.0) in got
          and ("FRED DGS10", "2026-10-07", 4.6) in got,
          f"a figure names its series, a value and its date ({sorted(got)})")
    check(("FRED DGS10", "2026-10-01", 4.1) in got,
          "'<date> (<value>)' pairs the value with the date before it")
    check(not any(f["printed"] in (9.99, 8.88) for f in figs + unrec),
          "the body and the undated appendix are never read")
    check(not any(f["printed"] == 4.25 for f in figs),
          "a threshold 'in the week of' is not a dated close")
    check(all(f["as_of"] == "2026-10-20" for f in figs), "the as-of is the heading's")
    why = {(u["printed"], u["reason"]) for u in unrec}
    check((2.5, "no series key in the sentence") in why,
          "a figure without a series key: unrecomputable")
    check(any(u["printed"] == 1.25 and "not a stored series" in u["reason"] for u in unrec),
          "a FRED id the pull does not carry: unrecomputable")
    check((4.4, "no date for the value") in why and (4.25, "no date for the value") in why,
          "a value without its own date: unrecomputable, never the sentence's other date")
    check(not any(f["series"].endswith(".yaml") for f in figs)
          and any(u["printed"] == 2.5 and "oneday_10y.yaml" in u["text"] for u in unrec),
          "a backticked file name is not a series key")


def group_c(ar, cfg, db) -> None:
    head("C. THE TOLERANCE RULE ON A FIXTURE STORE")
    before = hashlib.sha256(Path(db).read_bytes()).hexdigest()
    per = ar.run_figures(cfg, db, "fixture", ROOT)
    figs = {(f["series"], f["date"]): f for f in per["fixture-whitepaper.md"]["figures"]}
    f1 = figs[("FRED DGS10", "2026-10-05")]
    check(f1["recomputed"] == 4.5 and f1["verdict"] == "within tolerance"
          and f1["family"] == "rate",
          f"a rate within its absolute tolerance ({f1['verdict']})")
    f2 = figs[("yfinance.mkt_gspc", "2026-10-06")]
    check(f2["recomputed"] == 6050.0 and f2["verdict"] == "beyond tolerance"
          and abs(f2["diff"] - 50.0) < 1e-9,
          f"a price 0.83% off is beyond its 0.5% relative tolerance ({f2['diff']})")
    f3 = figs[("FRED BAMLH0A0HYM2", "2026-10-05")]
    check(f3["verdict"] == "within tolerance" and abs(f3["diff"] - 0.01) < 1e-9,
          "350bp is compared as 3.50 against a spread stored in percent")
    f4 = figs[("FRED DGS10", "2026-10-07")]
    check(f4["recomputed"] is None and f4["verdict"] == "not stored at its date",
          "a value stored only after the appendix's as-of is not used")
    d, v = ar.judge(100.0, "", 100.4, "price", cfg)
    d2, v2 = ar.judge(100.0, "", 100.6, "price", cfg)
    check(v == "within tolerance" and v2 == "beyond tolerance",
          "the relative tolerance at its edge: 0.4% within, 0.6% beyond")
    check(ar.judge(5.0, "%", 5.02, "rate", cfg)[1] == "beyond tolerance"
          and ar.judge(5.0, "%", 5.005, "rate", cfg)[1] == "within tolerance",
          "the absolute tolerance for a rate: 1bp")
    check(hashlib.sha256(Path(db).read_bytes()).hexdigest() == before,
          "the store is opened read-only and is unchanged")


def group_d(ar, cfg, db) -> None:
    head("D. THE FOUR GRADES ON SYNTHETIC MONTHLY SERIES")
    per = ar.run_relationships(cfg, db, None, ROOT)
    fx = per["fixture-whitepaper.md"]
    rows = fx["rows"]
    grades = [r["grade"] for r in rows]
    print("    " + "; ".join(f"line {r['line']}: {r['grade']} (stated "
                              f"{r.get('stated_rho') or 0:+.2f}, trailing "
                              f"{r.get('trailing_rho') or 0:+.2f}, between "
                              f"{r.get('middle_rho') or 0:+.2f})" for r in rows))
    check(len(rows) == 6, f"six relationship rows parsed ({len(rows)})")
    check(grades[0] == "holding", "a claim that still agrees: holding")
    check(grades[1] == "holding" and rows[1]["range"] == [0.5, 1.0],
          "a range claim inside its range: holding")
    check(grades[2] == "weakening", "the sign agrees, the strength has halved: weakening")
    check(grades[3] == "broken", "the trailing sign is the opposite: broken")
    check(grades[4] == "re-attached",
          "broken between the windows, agreeing again now: re-attached")
    check(grades[5].startswith("insufficient"),
          "a window before the data: insufficient, never graded")
    check(any("Credit leads equities" in u["text"] for u in fx["unparsed"]),
          "a claim in part (b) not in the relationship form is listed")
    pl = per["plain-whitepaper.md"]
    check(not pl["has_appendix"] and not pl["rows"],
          "a paper without an Appendix A(b) is listed, not failed")
    md = ar.relationships_md(per, "2026-11-06", db)
    check("1 broken" in md and "1 re-attached" in md and "plain-whitepaper.md" in md
          and "**broken**" in md,
          "the relationships file counts the grades and lists the paper without A(b)")
    check(set(ar.GRADES) == {"holding", "weakening", "broken", "re-attached"},
          "the four words are Audit 2's")


def group_e(ar, cfg, db) -> None:
    head("E. THE OUTPUTS AND THE TARGET")
    import subprocess                                           # noqa: PLC0415
    paper = ROOT / "docs" / "whitepapers" / "fixture-whitepaper.md"
    sha = hashlib.sha256(paper.read_bytes()).hexdigest()
    md = ar.figures_md(ar.run_figures(cfg, db, "fixture", ROOT), "2026-11-06", db)
    check(md.count("| Line | Figure |") == 1 and "## Unrecomputable" in md
          and re.search(r"\*\*Count:\*\* 5 recomputable figure\(s\) in 1 paper\(s\); "
                        r"1 beyond tolerance; \d+ unrecomputable\.", md) is not None,
          "the figures file: a table per paper, the unrecomputable list, a count line")
    check(hashlib.sha256(paper.read_bytes()).hexdigest() == sha,
          "no paper is written")
    out = TD / "out"
    r = subprocess.run([sys.executable, "-m", "tools.annual_review", "all",
                        "--db", str(TD / "absent.db"), "--date", "2026-11-06",
                        "--out", str(out)], capture_output=True, text=True,
                       cwd=str(REPO), timeout=300)
    check(r.returncode == 0 and (out / "annual-review-figures-2026-11-06.md").is_file()
          and (out / "annual-review-relationships-2026-11-06.md").is_file()
          and "annual-review-figures-2026-11-06.md" in r.stdout,
          "`all` writes both files, prints their paths and exits 0 with no store")
    mk = (REPO / "Makefile").read_text(encoding="utf-8")
    sh = (REPO / "scripts" / "make.sh").read_text(encoding="utf-8")
    check(re.search(r"^annual-review:\n\t@\$\(PYTHON\) -m tools\.annual_review all", mk, re.M)
          and "annual-review" in mk.split(".PHONY:")[1].splitlines()[0]
          and "annual-review)" in sh and "-m tools.annual_review all" in sh,
          "make annual-review and scripts/make.sh annual-review run `all`")
    import gate_list                                            # noqa: PLC0415
    names = gate_list.gates("code") + gate_list.gates("data") + gate_list.gates("shell")
    check(not any("annual_review.py" == Path(n).name for n in names),
          "it is not a gate: tools/annual_review.py declares no GATE_KIND")


def main() -> int:
    pin_clock()
    print(f"the gate's clock is pinned to {GATE_NOW}")
    import annual_review as ar                                  # noqa: PLC0415
    cfg = ar.config()
    try:
        ids = fixture_ids(ar)
        paper = write_paper(ids)
        db = build_store(ids)
        group_a_b(ar, cfg, paper)
        group_c(ar, cfg, db)
        group_d(ar, cfg, db)
        group_e(ar, cfg, db)
    finally:
        import shutil                                           # noqa: PLC0415
        shutil.rmtree(TD, ignore_errors=True)
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
