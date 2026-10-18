#!/usr/bin/env python3
"""
Validation gate: st-t1-rest -- Batch 6's two constituent ledgers (ST-R5.31b,
ST-R5.44b) and the signal-triage order's Tranche 1 remainder (ST-3's rest, ST-4,
ST-6) where no existing gate is their home. On fixtures; no network, no model,
no live store.

  A  ST-R5.31b. The back-cast caps, the top share, the leaders' relative low and
     its sessions reproduce hand figures; below five completed episodes the
     verdict is INSUFFICIENT and no rate prints; four of five completed falls
     PASS, three FAIL; the ledger file carries its as-of, window and n.
  B  ST-R5.44b. The one-pass drawdowns equal the windowed definition; a member
     20% off its high under a flat index is a +20-point gap and an episode; the
     resolution rule by hand; the floor as in A.

    python tools/validate_st_t1_rest.py
"""

from __future__ import annotations

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
TD = Path(mkdtemp("st-t1-rest-gate-"))


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


def days(n: int, start: str = "2024-01-01") -> list[str]:
    import datetime as dt
    d0 = dt.date.fromisoformat(start)
    return [(d0 + dt.timedelta(days=i)).isoformat() for i in range(n)]


# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. ST-R5.31b: THE POST-PEAK CONCENTRATION LEDGER")
    from altdata import ledgers
    from altdata.ledgers import st_r5_31b as L
    caps = L.backcast({"A": 50.0, "B": 50.0},
                      {"A": [("d1", 10.0), ("d2", 20.0)],
                       "B": [("d1", 10.0), ("d2", 10.0)]}, "d2")
    check(caps == {"d1": {"A": 25.0, "B": 50.0}, "d2": {"A": 50.0, "B": 50.0}},
          "back-cast: A's D0 weight 50 at half its D0 close is 25 on d1 (hand)")
    s, top = L.top_share(caps["d1"], {}, n=1)
    check(close(s, 66.666667) and top == ["B"],
          f"the top issuer's share on d1: 50 / 75 = 66.67% (hand; {s})")
    s2, _ = L.top_share({"GOOGL": 10.0, "GOOG": 10.0, "X": 15.0}, {"GOOG": "GOOGL"}, n=1)
    check(close(s2, 57.142857), "a second share class counts with its issuer: 20 / 35")
    # The leaders (A) against the rest (B): A halves on d3, recovers on d4.
    cb = {"p": {"A": 60.0, "B": 40.0}, "d3": {"A": 30.0, "B": 40.0},
          "d4": {"A": 45.0, "B": 40.0}}
    pp = L.post_peak(cb, ["p", "d3", "d4"], "p", ["A"], horizon=2)
    check(close(pp["relative_low_pct"], -50.0) and pp["trough"] == "d3"
          and pp["sessions_to_trough"] == 1 and pp["completed"],
          "the leaders' low against the rest: (30/40) / (60/40) - 1 = -50.0%, one "
          "session after the peak (hand); completed with the horizon in")
    check(not L.post_peak(cb, ["p", "d3", "d4"], "p", ["A"], horizon=5)["completed"],
          "an episode without its horizon after the peak is not completed")
    ep = [{"completed": True, "relative_low_pct": -12.0}] * 4
    v, rate = L.verdict(ep)
    check(v.startswith("INSUFFICIENT") and rate is None and "no rate prints" in v,
          "four completed episodes: INSUFFICIENT, below the floor of five, no rate")
    v5, r5 = L.verdict(ep + [{"completed": True, "relative_low_pct": -3.0}])
    v6, _ = L.verdict(ep[:3] + [{"completed": True, "relative_low_pct": -3.0}] * 2)
    check(v5 == "PASS" and close(r5, 0.8) and v6 == "FAIL",
          "four of five completed falls of 10% or more PASS (0.80); three FAIL "
          "(the pre-registered rule)")
    # End to end on a small basket: 11 members, the top ten's share above 40%.
    ds = days(30)
    w = {f"M{i}": (8.0 if i < 10 else 20.0) for i in range(11)}
    cl = {tk: [(d, 100.0) for d in ds] for tk in w}
    r = L.study({"weights": w, "holdings_day": ds[-1], "closes": cl, "classes": {}})
    check(r["n"] == 0 and r["result"]["episodes"] == 1 and r["result"]["rate"] is None
          and r["verdict"].startswith("INSUFFICIENT")
          and any("No rate prints below the floor" in x for x in r["body"])
          and not ledgers.ledger_faults({**r, "sources": ["fixture"],
                                         "source_mode": "fixture"}),
          f"a flat basket at {r['result']['share_now']:.1f}%: one open episode, n 0, "
          f"no rate printed, and the ledger carries its as-of, window and n")
    md, _ = ledgers.write_ledger({**r, "sources": ["fixture"],
                                  "source_mode": "laptop run, public sources"},
                                 TD, "2026-10-18")
    t = md.read_text(encoding="utf-8")
    check(md.name == "st-r5.31b-ledger-2026-10-18.md" and "| n | 0 |" in t
          and "Pre-registered by this first edition" in t and "grants nothing" in t,
          "the file is docs/ledgers/<item>-ledger-<date>.md, with n, the pre-registered "
          "rule and the rights line that grants nothing")


def group_b() -> None:
    head("B. ST-R5.44b: THE DRAWDOWN-GAP LEDGER")
    from altdata.ledgers import st_r5_44b as L
    s = [("a", 100.0), ("b", 110.0), ("c", 99.0)]
    check(close(L.drawdown_at(s, 2, window=3, min_closes=3), -10.0)
          and L.drawdown_at(s, 1, window=3, min_closes=3) is None,
          "99 against the window's 110: -10.0% (hand); a short window is none")
    import random
    rng = random.Random(7)
    ser = [(f"{i:05d}", 100 + rng.uniform(-30, 30)) for i in range(400)]
    one = L.drawdowns(ser)
    check(all(close(one.get(d), L.drawdown_at(ser, i), 1e-9) if L.drawdown_at(ser, i)
              is not None else d not in one for i, (d, _) in enumerate(ser)),
          "the one-pass drawdowns equal the windowed definition on 400 random closes")
    ds = days(300)
    index = [(d, 100.0) for d in ds]
    fall = [(d, 100.0 if i < 280 else 80.0) for i, d in enumerate(ds)]
    gs = L.gap_series({"X": fall, "Y": fall}, index)
    last = gs[-1]
    check(close(last[1], 0.0) and close(last[2], -20.0) and close(last[3], 20.0)
          and last[4] == 2,
          "members 20% off their high under a flat index: a +20-point gap (hand)")
    r = L.study({"closes": {"X": fall, "Y": fall}, "index": index})
    check(r["result"]["episodes"] == 1 and r["n"] == 0
          and r["verdict"].startswith("INSUFFICIENT") and r["result"]["rate"] is None,
          "the gap opens one wide episode, not completed: n 0, no rate printed")
    g = [("p", -1.0, -21.0, 20.0, 9)] + [(f"x{i}", -7.0, -20.0, 13.0, 9)
                                         for i in range(3)]
    check(L.resolve(g, 0, horizon=3)["resolution"] == "leaders fell"
          and L.resolve(g, 0, horizon=3)["completed"],
          "the index 6 points deeper within the horizon: the leaders fell (hand)")
    g2 = [("p", -1.0, -21.0, 20.0, 9)] + [(f"x{i}", -2.0, -15.0, 13.0, 9)
                                          for i in range(3)]
    g3 = [("p", -1.0, -21.0, 20.0, 9)] + [(f"x{i}", -2.0, -18.0, 16.0, 9)
                                          for i in range(3)]
    check(L.resolve(g2, 0, horizon=3)["resolution"] == "broadening"
          and L.resolve(g3, 0, horizon=3)["resolution"] == "unresolved",
          "the average member 6 points better: broadening; 3 points: unresolved")
    done = [{"completed": True, "resolution": "leaders fell"}] * 3 + \
           [{"completed": True, "resolution": "broadening"}] * 2
    v, rate = L.verdict(done)
    v2, _ = L.verdict(done[:4])
    check(v == "PASS" and close(rate, 0.6) and v2.startswith("INSUFFICIENT"),
          "three of five resolved by the leaders falling PASS (0.60); four "
          "completed is INSUFFICIENT")


def main() -> int:
    print(f"{LINE}\nst-t1-rest\n{LINE}")
    for g in (group_a, group_b):
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
