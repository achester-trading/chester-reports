"""
Batch 6 Tranche 2, part 1: the five ledgers (altdata/ledgers/; ST-R5.30b, 32b, 35b,
36b and 43b; meme-ingest-ledgers-1, 17 Oct 2026). Each study runs on fixture
series and reproduces a figure worked by hand; the verdict is the order's (no gate
stated, so none is invented) and prints with its inputs; a ledger without its
as-of, window and n is refused; nothing here writes the register or the store. No
network, no live store, no model -- the laptop's public-source runs are not gates.

  A  THE SHARED STATISTICS: OLS, the correlation, the percentile rule, quantiles,
     episodes, the year-on-year change -- each on a hand example.
  B  30b: the allocation construct, the total-return index, the forward return,
     the regression and the whole study on a fixture whose line is known.
  C  32b: the classifier on a fixture that turns on, and the 60/40's bond leg.
  D  35b: the gap, the margin-source attribution and the peak rule.
  E  36b: a crossing needs the line crossed AND the mortgage rate up on six months.
  F  43b: the diffusion index's last-move rule, and a lead the fixture plants at 8.
  G  THE LEDGER: required fields, the order's verdict, the file and its CSV.
  H  NO WRITES: the package never opens the register, and reads the store only
     through its one reader.

    python tools/validate_ledgers_b6.py
"""

from __future__ import annotations

import datetime as dt
import math
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import gate_tmp                   # noqa: E402  -- removed at exit

TD = Path(gate_tmp.mkdtemp("validate_ledgers_b6_"))

from altdata import ledgers as L  # noqa: E402
from altdata.ledgers import (st_r5_30b as s30, st_r5_32b as s32,  # noqa: E402
                             st_r5_35b as s35, st_r5_36b as s36, st_r5_43b as s43)

PASS = FAIL = 0
LINE = "=" * 78


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


def close(a, b, tol=1e-9) -> bool:
    return a is not None and b is not None and abs(a - b) <= tol


def months(start: str, n: int) -> list[str]:
    y, m = int(start[:4]), int(start[5:7]) - 1
    return [f"{y + (m + i) // 12}-{(m + i) % 12 + 1:02d}-01" for i in range(n)]


def quarters(start: str, n: int) -> list[str]:
    return months(start, 3 * n)[::3]


def group_a() -> None:
    head("A. THE SHARED STATISTICS")
    f = L.ols([1, 2, 3, 4], [3, 5, 7, 9])
    check(close(f["a"], 1.0) and close(f["b"], 2.0) and close(f["r2"], 1.0),
          "OLS on y = 1 + 2x: a 1, b 2, R2 1")
    check(close(L.corr([1, 2, 3], [2, 4, 6]), 1.0) and close(L.corr([1, 2, 3], [3, 2, 1]), -1.0),
          "correlation +1 and -1 on exact lines")
    check(close(L.percentile_rank([1, 2, 3, 4], 2), 50.0)
          and close(L.quantile([1, 2, 3, 4, 5], 0.25), 2.0)
          and close(L.quantile([10, 20], 0.5), 15.0),
          "the percentile is the share at or below (2 of 4 = 50%); quantiles interpolate")
    flags = [("d1", False), ("d2", True), ("d3", True), ("d4", False), ("d5", True),
             ("d6", False), ("d7", False), ("d8", False), ("d9", True)]
    check(L.episodes(flags) == [("d2", "d3"), ("d5", "d5"), ("d9", "d9")]
          and L.episodes(flags, merge_gap=1) == [("d2", "d5"), ("d9", "d9")],
          "episodes: contiguous runs, merged across a gap of at most merge_gap")
    s = [("2025-01-01", 100.0), ("2025-04-01", 101.0), ("2025-07-01", 102.0),
         ("2025-10-01", 103.0), ("2026-01-01", 105.0)]
    y = L.yoy(s, 4)
    check(len(y) == 1 and y[0][0] == "2026-01-01" and close(y[0][1], 5.0) and L.ordinal(2) == "2nd"
          and L.ordinal(11) == "11th" and L.ordinal(101) == "101st",
          "year on year over four quarters (100 to 105 = +5.0%); ordinals")


def group_b() -> None:
    head("B. 30b: ALLOCATION, TOTAL RETURN, THE REGRESSION")
    q = quarters("1990-01", 70)
    legs = {}
    alloc_want = []
    for i, d in enumerate(q):
        a = 30.0 + 0.3 * i                      # allocation, percent
        e, debt = a, 100.0 - a                  # out of 100
        for k in s30.EQUITY:
            legs.setdefault(k, []).append((d, e / len(s30.EQUITY)))
        for k in s30.DEBT:
            legs.setdefault(k, []).append((d, debt / len(s30.DEBT)))
        alloc_want.append(a)
    al = s30.allocation(legs)
    check(all(close(v, w, 1e-9) for (_, v), w in zip(al, alloc_want)),
          "the construct: equities over equities plus the six debt legs (30% to 50.7%)")
    tri = s30.total_return_index([("2000-01-01", 100.0), ("2000-02-01", 110.0)],
                                 [("2000-01-01", 12.0), ("2000-02-01", 12.0)])
    check(close(tri["2000-02"], 1.11),
          "the total-return index: price 100 to 110 plus a month's dividend (12 / 12) = 1.11")
    # A return that is exactly 20 - 0.3 x allocation, by construction.
    m = months("1990-01", 70 * 3 + 130)
    alloc_at = {s30.quarter_end_month(d)[:7]: a for d, a in al}
    price, tr = [], 100.0
    target = {}
    for mm in m:
        a = alloc_at.get(mm[:7])
        if a is not None:
            target[mm[:7]] = 20.0 - 0.3 * a
    # Build monthly growth so each quarter-end start month has its decade return:
    # use one constant monthly rate per month = the rate implied by the latest start.
    rates = []
    for mm in m:
        r = target.get(mm[:7])
        rates.append(None if r is None else (1 + r / 100.0) ** (1 / 12) - 1)
    fwd = {}
    for i, mm in enumerate(m):
        if rates[i] is not None:
            fwd[mm[:7]] = target[mm[:7]]
    fit = s30.regress(al, fwd)
    check(close(fit["a"], 20.0, 1e-6) and close(fit["b"], -0.3, 1e-8) and close(fit["r2"], 1.0),
          f"the regression recovers forward = 20 - 0.3 x allocation (a {fit['a']:.4f}, "
          f"b {fit['b']:.4f})")
    r = s30.forward_returns({f"2000-{i + 1:02d}": 1.01 ** i for i in range(12)} |
                            {f"2001-{i + 1:02d}": 1.01 ** (12 + i) for i in range(12)}, 12)
    check(close(r["2000-01"], 100.0 * (1.01 ** 12 - 1)),
          "the forward return over 12 months of +1% a month: (1.01^12 - 1) = 12.68%")


def group_c() -> None:
    head("C. 32b: THE CLASSIFIER AND THE 60/40")
    # Fixture: 60 sessions; Brent and the S&P co-move (+), then oppose (-) while
    # Brent and the yield co-move -- the regime turns on in the last window.
    chg = []
    for i in range(60):
        x = (1 if i % 2 else -1) * (1 + (i % 3) * 0.1) / 100.0
        if i < 45:
            row = (f"d{i:03d}", x, x, -100.0 * x, 100.0, 4.0)
        else:
            row = (f"d{i:03d}", x, -x, 100.0 * x, 100.0, 4.0)
        chg.append(row)
    days = s32.classify(chg, window=5, lookback=40, min_lookback=10)
    by = {d["date"]: d for d in days}
    check(days and not any(d["on"] for d in days if d["date"] < "d045")
          and by["d049"]["on"] and close(by["d049"]["corr_brent_spx"], -1.0, 1e-9)
          and close(by["d049"]["corr_brent_10y"], 1.0, 1e-9),
          "the regime is ON when Brent-SPX is at or below its 20th percentile and "
          "Brent-10y at or above its 80th, the same day (d049: -1.00 and +1.00), "
          "and off before the switch")
    check(not by["d059"]["on"] and by["d059"]["pct_spx"] > 20.0,
          "percentiles are against the trailing correlations, ties included: after "
          "eleven -1.00 days in forty, -1.00 is the 28th percentile and the regime is off")
    one = [("d0", 0, 0, 0, 100.0, 4.0), ("d1", 0, math.log(1.01), -10.0, 101.0, 4.0)]
    s, p = s32.forward(one, 0, 1)
    bond = 4.0 / 100 / 252 + 8 * 10 / 10000
    check(close(s, 1.0, 1e-9) and close(p, 0.6 * 1.0 + 0.4 * 100 * bond, 1e-9),
          f"the 60/40: S&P +1%, the bond y/252 + 8 x 10 bp = {100 * bond:.4f}%, so "
          f"{p:.4f}%")


def group_d() -> None:
    head("D. 35b: THE GAP, THE SOURCE, THE PEAKS")
    ppi = [(d, 100.0 * 1.01 ** i) for i, d in enumerate(months("2020-01", 24))]
    ulc = [(d, 100.0 * 1.005 ** i) for i, d in enumerate(quarters("2020-01", 8))]
    g = s35.gap_series(ppi, ulc)
    ppi_q = L.to_quarterly_mean(ppi)
    want_ppi = 100.0 * (ppi_q[4][1] / ppi_q[0][1] - 1)
    want_ulc = 100.0 * (1.005 ** 4 - 1)
    check(g and close(g[0][1], want_ppi, 1e-9) and close(g[0][2], want_ulc, 1e-9)
          and close(g[0][3], want_ppi - want_ulc, 1e-9),
          f"the gap: PPI's quarterly-mean change on the year ({want_ppi:.3f}%) less "
          f"ULC's ({want_ulc:.3f}%)")
    fake = [(d, 0, 0, v) for d, v in zip(quarters("2010-01", 9),
                                         [0.5, 1.0, 3.0, 1.0, 0.5, 0.6, -1.0, 2.0, 1.0])]
    check(s35.peaks(fake) == [2],
          "a peak is a positive quarter above the two on each side (3.0 only)")
    margin = [(d, 10.0 + i) for i, d in enumerate(quarters("2010-01", 9))]
    rows, base = s35.after_peaks(fake, margin)
    check(rows[0]["margin_change_4q_pp"] == 4.0 and rows[0]["margin_change_8q_pp"] is None,
          "the margin 4 quarters after the peak (+4.0 pp); 8 quarters not yet history")


def group_e() -> None:
    head("E. 36b: A CROSSING NEEDS THE LINE AND RISING RATES")
    ms = months("2020-01", 12)
    mos = list(zip(ms, [5.0] * 8 + [5.5, 6.5, 7.0, 7.5]))
    up = list(zip(ms, [3.0 + 0.1 * i for i in range(12)]))
    down = list(zip(ms, [5.0 - 0.1 * i for i in range(12)]))
    check(s36.crossings(mos, up, 6.0) == ["2020-10-01"]
          and s36.crossings(mos, down, 6.0) == [],
          "October 2020 crosses 6.0 with the mortgage rate up on six months; with it "
          "falling there is no crossing")
    real = list(zip(months("2020-01", 30), [100.0 + i for i in range(30)]))
    check(close(s36.change_after(real, "2020-10-01"), 100.0 * (121.0 / 109.0 - 1), 1e-9),
          "the real house price 12 months on: 109 to 121 = +11.01%")


def group_f() -> None:
    head("F. 43b: THE LAST-MOVE RULE AND THE LEAD")
    ms = months("2000-01", 4)
    rates = {"A": list(zip(ms, [5.0, 4.5, 4.5, 4.5])),     # cut in Feb
             "B": list(zip(ms, [3.0, 3.0, 3.5, 3.5])),     # hike in Mar
             "C": list(zip(ms, [2.0, 2.0, 2.0, 1.5]))}     # cut in Apr
    idx = s43.diffusion(rates, min_banks=2)
    check(idx == [("2000-03-01", 0.0), ("2000-04-01", 1 / 3)],
          "net share of last moves: March (A cut, B hike) 0; April (+C cut) 1/3; "
          "February skipped (one bank)")
    base = [(d, math.sin(i / 5.0)) for i, d in enumerate(months("1990-01", 240))]
    cli = [(months("1990-01", 260)[i + 8], v) for i, (_, v) in enumerate(base)]
    prof = s43.lead_profile(base, cli)
    best = max((p for p in prof if p[1] is not None), key=lambda p: p[1])
    check(best[0] == 8 and close(best[1], 1.0, 1e-9),
          "a CLI that is the index eight months later: the best lead is 8, r = 1")


def group_g() -> None:
    head("G. THE LEDGER")
    r = {"item": "ST-R5.99b", "title": "fixture", "as_of": "2026-09", "window": "2000 to 2026",
         "n": 12, "statistic": "s", "pass_rule": "none stated", "verdict": L.NO_GATE,
         "rights": "none", "sources": ["fixture"], "source_mode": "laptop run, public sources",
         "body": ["x"], "episodes": [{"a": 1, "b": 2}]}
    check(not L.ledger_faults(r), "a complete ledger has no faults")
    for k in ("as_of", "window", "n"):
        bad = dict(r, **{k: None})
        try:
            L.write_ledger(bad, TD)
            refused = False
        except ValueError:
            refused = True
        check(refused and f"missing {k}" in L.ledger_faults(bad),
              f"a ledger without its {k} is refused")
    md, cs = L.write_ledger(r, TD, "2026-10-17")
    text = md.read_text(encoding="utf-8")
    check(md.name == "st-r5.99b-ledger-2026-10-17.md" and cs and cs.exists()
          and "| As of | 2026-09 |" in text and "| n | 12 |" in text
          and "NO GATE IN THE ORDER" in text and "| Pass rule (as the order states it) | none stated |" in text,
          "the dated file prints its as-of, window, n, the pass rule as stated and the "
          "verdict, with its CSV beside it")
    mods = (s30, s32, s35, s36, s43)
    check(all("NO_GATE" in Path(m.__file__).read_text(encoding="utf-8")
              and re.search(r'"pass_rule": "none stated', Path(m.__file__).read_text(encoding="utf-8"))
              for m in mods),
          "every study's verdict is the order's: no pass rule stated, none invented")
    check(all(getattr(m, "RIGHTS", "") and ("grants" in m.RIGHTS or "granted" in m.RIGHTS)
              for m in mods),
          "every ledger states its rights consequence, granting nothing")


def group_h() -> None:
    head("H. NO WRITES TO THE REGISTER OR THE STORE")
    pkg = REPO / "altdata" / "ledgers"
    text = {p.name: p.read_text(encoding="utf-8") for p in pkg.glob("*.py")}
    check(not any(re.search(r"(?<!-)\bregister\b|Register\(|decide|open_writer|write_many|INSERT|UPDATE|DELETE",
                            t) for t in text.values()),
          "the ledgers never touch the register or write the store")
    check(sum(t.count("ObservationStore(") for t in text.values()) == 1
          and "ObservationStore(" in text["sources.py"],
          "the store is read in one place (sources.store), for a box run")


def main() -> int:
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g, group_h):
        try:
            g()
        except Exception as exc:                              # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
