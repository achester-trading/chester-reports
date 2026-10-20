#!/usr/bin/env python3
"""
Validation gate: b48-scoreboard -- the Card's scoreboard (ruled 19 Oct 2026,
"accept all" on the four decisions sent at 23:35 ET), measurement only. On
synthetic fixtures; no network, no model, no live store. The register, the grades
and the store are seeded in a temporary database of the gate's own.

  A  THE SCORE. The rolling thirteen-week expectancy in ruled R, by book (the
     decision's own book) and by regime (the stamp the order gate stored at entry,
     never recomputed), interval first; taken decisions only, one grade per
     decision (its latest), graded inside the window and knowable at the as-of;
     below the session-set minimum a cell prints "accruing (n=k)".
  B  THE BENCHMARKS. The active books (B, C, D) and Book A alone as a share of
     capital from realised P&L, against Book Z's stored 60/40 over the same
     window; "not built" with its reason where the register cannot mark a book.
     Percentages only, never dollars.
  C  THE WEEKLY'S TOP AND THE MONTHLY'S CUT. Heat, net exposure, the score and
     the rule-break count, above the precis; the Monthly's register month prints
     the cut beside its overall figure, from the same function.
  D  READ-ONLY, AND NOTHING ELSE. The live databases are opened mode=ro; the
     module imports no order path and writes nothing; no figure in dollars.

    python tools/validate_b48_scoreboard.py
"""

from __future__ import annotations

import json
import os
import socket
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

TD = Path(gate_mkdtemp("b48_scoreboard_"))
DB = TD / "store.sqlite"
os.environ["CHESTER_DB"] = str(DB)
PASS = FAIL = 0
LINE = "=" * 78
AS_OF = "2026-12-31T22:00:00+00:00"


def _no_connect(*a, **k):
    raise OSError("validate_b48_scoreboard: no network in a code gate")


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


# ---------------------------------------------------------------------------
# The synthetic fixture: every figure invented, every name a placeholder
# ---------------------------------------------------------------------------
def _gd(regime: str) -> str:
    return json.dumps({"outcome": "approve", "regime": {"regime": regime,
                                                        "dial_state": "synthetic"}})


def seed(db: Path) -> None:
    from altdata import grader, observations
    from register.store import Register
    Register(str(db)).close()
    grader.GradeStore(str(db)).conn.close()
    observations.ObservationStore(str(db)).close()
    conn = sqlite3.connect(str(db))

    def dec(i, book, status, action, gd, **kw):
        cols = {"id": i, "created_at": "2026-10-02T14:00:00+00:00",
                "decision_time": "2026-10-02T14:00:00+00:00", "instrument": "SYNTH",
                "instrument_norm": "SYNTH", "direction": "long",
                "thesis": "synthetic", "edge_type": "synthetic", "horizon": "swing",
                "invalidation": "synthetic", "status": status,
                "operator_action": action, "book": book, "gate_detail": gd, **kw}
        conn.execute(f"INSERT INTO decisions ({', '.join(cols)}) VALUES "
                     f"({', '.join('?' for _ in cols)})", list(cols.values()))

    def grade(i, r, at, action="TAKE"):
        conn.execute("INSERT INTO grades (decision_id, horizon, graded_at, horizon_date,"
                     " operator_action, r_multiple_ruled, observations_json, price_source,"
                     " method_version) VALUES (?,?,?,?,?,?,?,?,?)",
                     (i, "swing", at, at[:10], action, r, "[]", "synthetic",
                      grader.METHOD_VERSION))

    # Book B, Expansion: twelve taken grades in the window. Mean +0.25R.
    b_r = [2, -1, 1, -1, 2, -1, 1, -1, 2, -1, 1, -1]
    for n, r in enumerate(b_r, start=1):
        dec(f"B{n}", "B", "closed", "TAKE", _gd("Expansion"))
        grade(f"B{n}", r, f"2026-11-{n:02d}T21:00:00+00:00")
    # B1 graded earlier at -5R: the LATER grade (2R) is the one that counts.
    grade("B1", -5, "2026-10-15T21:00:00+00:00")
    # Book C, Transition: three, so it accrues.
    for n, r in enumerate([0.5, 0.5, -1], start=1):
        dec(f"C{n}", "C", "closed", "TAKE", _gd("Transition"))
        grade(f"C{n}", r, f"2026-12-{n:02d}T21:00:00+00:00")
    # Book D with no stamp at entry.
    dec("D1", "D", "closed", "TAKE", None)
    grade("D1", 0.5, "2026-12-10T21:00:00+00:00")
    # Excluded: a declined decision, one graded before the window, one graded
    # after the as-of (not knowable), and one with no ruled R.
    dec("X1", "B", "declined", "DECLINE", _gd("Expansion"))
    grade("X1", 9, "2026-11-20T21:00:00+00:00", action="DECLINE")
    dec("X2", "B", "closed", "TAKE", _gd("Expansion"))
    grade("X2", 9, "2026-09-01T21:00:00+00:00")
    dec("X3", "B", "closed", "TAKE", _gd("Expansion"))
    grade("X3", 9, "2027-01-05T21:00:00+00:00")
    dec("X4", "B", "closed", "TAKE", _gd("Expansion"))
    grade("X4", None, "2026-12-11T21:00:00+00:00")
    # Rule breaks: two this week, one earlier.
    for k, s in enumerate(("2026-12-28", "2026-12-30", "2026-11-03")):
        conn.execute("INSERT INTO rule_breaks (detected_at, session, kind, reason, source,"
                     " dedupe_key) VALUES (?,?,?,?,?,?)",
                     (s + "T21:00:00+00:00", s, "time_stop_passed", "synthetic",
                      "synthetic", f"k{k}"))
    conn.commit()
    conn.close()


def seed_benchmarks(db: Path, open_a: bool) -> None:
    """A closed Book B decision with its exit and Portfolio Truth's cost; Book A
    open (or closed); Book Z's 60/40 marked 100 then 105."""
    from altdata import grader, observations
    from register.store import Register
    Register(str(db)).close()
    grader.GradeStore(str(db)).conn.close()
    conn = sqlite3.connect(str(db))
    base = {"created_at": "2026-03-02T14:00:00+00:00",
            "decision_time": "2026-03-02T14:00:00+00:00", "instrument": "SYNTH@X.USD",
            "instrument_norm": "SYNTH", "direction": "long", "thesis": "synthetic",
            "edge_type": "synthetic", "horizon": "swing", "invalidation": "synthetic",
            "operator_action": "TAKE"}
    rows = [{**base, "id": "B1", "book": "B", "status": "closed", "exit_price": 110.0,
             "exit_time": "2026-06-01T15:00:00+00:00", "exit_currency": "USD",
             "exit_fx_to_usd": 1.0},
            {**base, "id": "A1", "book": "A", "instrument": "SYNTHA@X.USD",
             "status": "active" if open_a else "closed",
             **({} if open_a else {"exit_price": 52.0,
                                   "exit_time": "2026-07-01T15:00:00+00:00",
                                   "exit_currency": "USD", "exit_fx_to_usd": 1.0})}]
    for c in rows:
        conn.execute(f"INSERT INTO decisions ({', '.join(c)}) VALUES "
                     f"({', '.join('?' for _ in c)})", list(c.values()))
    conn.commit()
    conn.close()
    with observations.ObservationStore(str(db)) as st:
        for inst, qty, cost in (("SYNTH@X.USD", 100, 100.0), ("SYNTHA@X.USD", 50, 40.0)):
            st.write("portfolio.position_qty", inst, "2026-05-01", "2026-05-01T20:00:00+00:00",
                     qty, "synthetic")
            st.write("portfolio.position_avg_cost", inst, "2026-05-01",
                     "2026-05-01T20:00:00+00:00", cost, "synthetic")
        for day, v in (("2026-01-02", 100.0), ("2026-12-30", 105.0)):
            st.write("paper.benchmark", "sixty_forty", day, day + "T21:30:00+00:00",
                     json.dumps({"value": v, "session": day, "start": "2025-12-31"}),
                     "book_z")


# ---------------------------------------------------------------------------
def group_a() -> None:
    from register import scoreboard as sb
    head("A. THE SCORE: THIRTEEN WEEKS, BY BOOK AND BY THE REGIME STAMPED AT ENTRY")
    e = sb.expectancy_13w(AS_OF, str(DB))
    check(e["window"] == ["2026-10-01", "2026-12-31"] and e["unit"] == "R (ruled)",
          f"the window is thirteen weeks to the as-of, in ruled R ({e['window']})")
    ov = e["overall"]
    check(ov["n"] == 16 and abs(ov["mean"] - 3.5 / 16) < 1e-9,
          f"overall: 16 taken decisions, mean 3.5/16 R (n={ov['n']}, mean={ov['mean']})")
    bb = e["by_book"]
    check(set(bb) == {"B", "C", "D"} and bb["B"]["n"] == 12
          and abs(bb["B"]["mean"] - 0.25) < 1e-9,
          "Book B: twelve, mean +0.25R -- B1's later grade (2R) counted, not its -5R")
    check(bb["C"]["accruing"] and sb.cell_text(bb["C"], e["min_n"]) == "accruing (n=3)",
          "below the minimum n a cell prints 'accruing (n=3)'")
    check(not bb["B"]["accruing"] and sb.cell_text(bb["B"], e["min_n"]).startswith("n=12, "),
          "at or above it, n and the interval print before the mean")
    check(set(e["by_regime"]) == {"Expansion", "Transition", sb.NO_STAMP},
          f"by regime: the stored stamps, and a decision with none named as such "
          f"({sorted(e['by_regime'])})")
    check("B | Expansion" in e["by_book_regime"] and "C | Transition" in e["by_book_regime"],
          "the book-and-regime cut")
    # The excluded rows: a declined decision, outside the window, after the as-of,
    # no ruled R. None of their 9R reaches any cell.
    check(all(abs(v["mean"] or 0) < 9 for v in e["by_book_regime"].values()),
          "declined, out-of-window, not-yet-knowable and R-less grades are excluded")
    later = sb.expectancy_13w("2027-01-06T22:00:00+00:00", str(DB))
    check(later["by_book"]["B"]["n"] == 13,
          "a later as-of reads the grade that became knowable since (point in time)")
    regime_src = Path(REPO / "register" / "scoreboard.py").read_text(encoding="utf-8")
    check("regime.latest" not in regime_src and "import regime" not in regime_src,
          "the stamp is read from the decision, never recomputed from the object")
    ln = sb.expectancy_line(e)
    check(ln.startswith("Thirteen-week expectancy (1 Oct 2026 to 31 Dec 2026, ruled R")
          and "Book C: accruing (n=3)" in ln, ln)
    empty = sb.expectancy_13w(AS_OF, str(TD / "absent.sqlite"))
    check(empty.get("not_built") and "not built" in sb.expectancy_line(empty),
          "no grades table: 'not built' with its reason")


def group_b() -> None:
    from register import scoreboard as sb
    head("B. THE BENCHMARKS OVER FOUR QUARTERS, AS A SHARE OF CAPITAL")
    db1 = TD / "bench_open.sqlite"
    seed_benchmarks(db1, open_a=True)
    b = sb.benchmarks_4q(AS_OF, str(db1))
    check(b["window"] == ["2025-12-31", "2026-12-31"], f"four quarters ({b['window']})")
    # (110 - 100) x 100 = 1,000 on a declared capital of 300,000: 0.33%.
    check(b["active"]["pct"] == 0.33, f"the active books: realised, 0.33% ({b['active']})")
    check(b["book_a"]["pct"] is None
          and "1 open decision held" in b["book_a"]["not_built"],
          f"Book A open: not built, naming what is missing ({b['book_a'].get('not_built')})")
    check(b["sixty_forty"]["pct"] == 5.0, f"the static 60/40 from Book Z: +5.00% "
          f"({b['sixty_forty']})")
    line = sb.benchmarks_line(b)
    check("Book A alone not built (" in line and "+0.33%" in line and "+5.00%" in line
          and "$" not in line, line)
    db2 = TD / "bench_closed.sqlite"
    seed_benchmarks(db2, open_a=False)
    b2 = sb.benchmarks_4q(AS_OF, str(db2))
    # (52 - 40) x 50 = 600: 0.20%.
    check(b2["book_a"]["pct"] == 0.2, f"Book A closed: realised, 0.20% ({b2['book_a']})")
    none = sb.benchmarks_4q(AS_OF, str(TD / "absent2.sqlite"))
    check(none["active"]["not_built"].startswith("no taken decision")
          and none["sixty_forty"]["not_built"] == "no Book Z mark is stored",
          "an empty register and no Book Z: each not built, with its reason")


def group_c() -> None:
    from register import scoreboard as sb
    from daily_cascade import weekly_stack as ws
    from monthly_macro import stack as ms
    head("C. THE WEEKLY'S TOP; THE MONTHLY'S CUT BESIDE ITS OVERALL FIGURE")
    t = sb.weekly_top(AS_OF, str(DB))
    ln = t["lines"]
    check(len(ln) == 4 and ln[0].startswith("Heat: ") and ln[1].startswith("Net exposure: ")
          and ln[2].startswith("Thirteen-week expectancy") and ln[3].startswith("Rule breaks: "),
          "four lines in the Doctrine's order: heat, net exposure, the score, rule breaks")
    check(ln[3] == "Rule breaks: 2 this week; 3 on the register to date (the Doctrine's "
                  "target is zero).", ln[3])
    check(t["heat"].get("pct") == 0.0 and "0.00% of capital" in ln[0],
          f"no open decision: heat 0.00% of capital ({ln[0]})")
    check(all("$" not in x for x in ln), "percentages only, never dollars")
    import re                                                   # noqa: PLC0415
    printed = ln + [sb.benchmarks_line(sb.benchmarks_4q(AS_OF, str(DB)))]
    check(not any("(s)" in x or re.search(r"\d{4}-\d{2}-\d{2}", x) for x in printed),
          "the house's readability: no '(s)' and no ISO date in a printed line")
    html = ws.scoreboard_html(t)
    check(html.startswith('<div id="scoreboard"') and "The ledger, first" in html
          and all(x.split(":")[0] in html for x in ln), "the block renders every line")
    src = Path(REPO / "daily_cascade" / "weekly_stack.py").read_text(encoding="utf-8")
    r = src[src.index("def render("):]
    check(r.index("scoreboard_html(") < r.index("precis.precis_html(ed)"),
          "the block is placed before the precis, above anything about the market")
    check(ws.scoreboard_html({}) == "", "no scoreboard: nothing printed")
    e = sb.expectancy_13w(AS_OF, str(DB))
    p = {"register_month": {"state": "ok", "graded_total": 21, "graded_this_month": 4,
                            "cuts": {"overall": {}},
                            "scoreboard": {"expectancy": e,
                                           "benchmarks": sb.benchmarks_4q(AS_OF, str(DB))}}}
    reg = [s for s in ms.detail_tables(p, set()) if s.get("id") == "register"][0]
    lines = reg["lines"]
    check(any(x.startswith("Thirteen-week expectancy") for x in lines)
          and any(x.startswith("By regime at entry: ") for x in lines)
          and any(x.startswith("Four quarters") for x in lines),
          "the Monthly's register month: the score, the regime cut and the benchmarks")
    check(any(tb["columns"][0].startswith("Book | regime at entry") for tb in reg["tables"]),
          "and the book-and-regime table beside its overall figure")


def group_d() -> None:
    head("D. READ-ONLY, NO ORDER PATH, NO DOLLARS")
    src = Path(REPO / "register" / "scoreboard.py").read_text(encoding="utf-8")
    import re                                                   # noqa: PLC0415
    check("mode=ro" in src and not re.search(
              r"\b(INSERT\s+(OR\s+\w+\s+)?INTO|UPDATE\s+\w+\s+SET|DELETE\s+FROM|"
              r"CREATE\s+TABLE|DROP\s+TABLE)\b", src, re.I),
          "the module opens the databases mode=ro and holds no write statement")
    for bad in ("placeOrder", "place_order", "submit_order", "ibkr_orders", "order_router"):
        check(bad not in src, f"no {bad}")
    before = DB.stat().st_mtime_ns
    from register import scoreboard as sb
    sb.weekly_top(AS_OF, str(DB))
    sb.expectancy_13w(AS_OF, str(DB))
    conn = sqlite3.connect(str(DB))
    n = conn.execute("SELECT COUNT(*) FROM grades").fetchone()[0]
    conn.close()
    check(n == 21, f"the grades are unchanged after the reads ({n} rows)")
    cfg = (REPO / "config" / "scoreboard.yaml").read_text(encoding="utf-8")
    check("min_n: 10" in cfg and "SESSION-SET" in cfg, "the minimum n is session-set, in config")
    del before


def main() -> int:
    try:
        seed(DB)
        group_a()
        group_b()
        group_c()
        group_d()
    finally:
        import shutil                                           # noqa: PLC0415
        shutil.rmtree(TD, ignore_errors=True)
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
