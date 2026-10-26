"""
Validation gate for the cross-table consistency gate (W-1.1 item 1.1, ruled 11
Oct 2026; daily_cascade/consistency.py).

The 9 Oct Weekly printed SPY's week as +1.16% in the tape and +1.17% in the
overnight/cash split. Any figure keyed by (series, as-of) that appears in more
than one table must be identical at printed precision. FIXTURES, no store, no
network, no model:

  A  WITHIN ROUNDING. Two tagged cells, +1.16% and +1.17%: every place prints the
     canonical one (the tape's), and the log names both sources.
  B  BEYOND ROUNDING. +1.16% against +1.31%: EditionInconsistent, naming the key
     and both cells; `check()` reports the same without raising or rewriting.
  C  THE CONVENTION. On constructed bars where compounding rounded session
     returns drifts a hundredth (the 9 Oct case), the overnight split's week now
     equals the tape's close to close exactly, and the overnight and intraday
     legs compound unrounded to it.
  D  THE TAGS. The Weekly's tagger marks the tape's week and session (canonical),
     the overnight split's sessions and week, the week by day's SPY and 10-year,
     and Plumbing's 10- and 30-year week; a consistent edition passes untouched.
  E  THE RUN. The Weekly reconciles before the prose (so every frame copies the
     canonical figure), and a mismatch beyond rounding fails the run with exit 5
     and an error state record, never a sent edition.

    python tools/validate_edition_consistency.py
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import copy
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from daily_cascade import consistency as cons  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = 0
FAIL = 0
LINE = "=" * 78


def check(c: bool, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def edition(tape_week: str, split_week: str) -> dict:
    tape = {"columns": ["Market", "Last", "Session", "Week", "Month", "YTD"],
            "rows": [["SPY", "671.20", "+0.40%", tape_week, "+2.10%", "+14.00%"]]}
    split = {"columns": ["Session", "Overnight", "Intraday", "Close to close"],
             "rows": [["Fri 9 Oct", "+0.10%", "+0.30%", "+0.40%"],
                      ["The week", "+0.60%", "+0.56%", split_week]]}
    cons.tag(tape, 0, 3, cons.fact_key("spy", "2026-10-09", "week"), True)
    cons.tag(split, 1, 3, cons.fact_key("spy", "2026-10-09", "week"))
    cons.tag(tape, 0, 2, cons.fact_key("spy", "2026-10-09", "session"), True)
    cons.tag(split, 0, 3, cons.fact_key("spy", "2026-10-09", "session"))
    return {"sections": [{"id": "tape", "title": "The tape", "table": tape,
                          "subsections": [{"title": "SPY overnight against the cash "
                                                    "session", "table": split}]}]}


def group_a() -> None:
    print(f"\n{LINE}\nA. WITHIN ROUNDING: ONE CANONICAL FIGURE, LOGGED\n{LINE}")
    ed = edition("+1.16%", "+1.17%")
    log = cons.reconcile(ed)
    split = ed["sections"][0]["subsections"][0]["table"]
    check(split["rows"][1][3] == "+1.16%" and ed["sections"][0]["table"]["rows"][0][3]
          == "+1.16%", "both places now print +1.16%, the tape's")
    check(len(log) == 1 and log[0]["verdict"] == "rounding" and log[0]["fixed"]
          and {c["printed"] for c in log[0]["cells"]} == {"+1.16%", "+1.17%"}
          and log[0]["canonical_where"] == "The tape",
          "the log keeps the difference and each cell's source")
    check(ed.get("consistency") == log, "the log rides on the edition")


def group_b() -> None:
    print(f"\n{LINE}\nB. BEYOND ROUNDING: THE RUN FAILS\n{LINE}")
    ed = edition("+1.16%", "+1.31%")
    try:
        cons.reconcile(ed)
        check(False, "a 0.15-point difference raises")
    except cons.EditionInconsistent as exc:
        check("spy|2026-10-09|week" in str(exc) and "+1.31%" in str(exc)
              and len(exc.mismatches) == 1,
              f"EditionInconsistent names the key and both cells: {exc}")
    ed = edition("+1.16%", "+1.31%")
    log = cons.check(ed)
    check(log and log[0]["verdict"] == "beyond"
          and ed["sections"][0]["subsections"][0]["table"]["rows"][1][3] == "+1.31%",
          "check() reports without raising and rewrites nothing")
    ed = edition("+1.16%", "+1.16%")
    check(cons.reconcile(ed) == [], "identical figures: nothing logged")
    ed = edition("+1.16%", "+12 bp")
    check(cons.check(ed)[0]["verdict"] == "beyond",
          "a figure in a different unit is never 'within rounding'")


class Store:
    def __init__(self, series: dict):
        self.series = series

    def as_of(self, key, cutoff=None, instrument=None):
        return [{"observed_at": d, "value_num": v} for d, v in self.series.get(key, [])]


def group_c() -> None:
    print(f"\n{LINE}\nC. THE CONVENTION: CLOSE TO CLOSE, LEGS UNROUNDED\n{LINE}")
    from daily_cascade import weekly_sections as wsec
    from altdata import levels
    days = ["2026-10-02", "2026-10-05", "2026-10-06", "2026-10-07", "2026-10-08",
            "2026-10-09"]
    found = None
    for seed in range(400):
        rnd = random.Random(seed)
        c = 660.0
        bars = {"o": [], "c": []}
        for _ in days:
            o = c * (1 + rnd.gauss(0, 0.002))
            c = o * (1 + rnd.gauss(0, 0.004))
            bars["o"].append(round(o, 2))
            bars["c"].append(round(c, 2))
        cl, op = bars["c"], bars["o"]
        old_on = old_id = 1.0
        for i in range(1, len(days)):
            old_on *= 1 + round(100 * (op[i] / cl[i - 1] - 1), 2) / 100
            old_id *= 1 + round(100 * (cl[i] / op[i] - 1), 2) / 100
        old = round(100 * (old_on * old_id - 1), 2)
        true = round(100 * (cl[-1] / cl[0] - 1), 2)
        if old != true:
            found = (cl, op, old, true)
            break
    check(found is not None, f"bars found where the old compounding drifts: "
                             f"{found and found[2]} against {found and found[3]}")
    if not found:
        return
    cl, op, old, true = found
    spec = levels.tape_spec("spy")
    key = spec["daily"]
    st = Store({key: list(zip(days, cl)), key + "_open": list(zip(days, op)),
                key + "_high": [(d, max(a, b) + 0.5) for d, a, b in zip(days, op, cl)],
                key + "_low": [(d, min(a, b) - 0.5) for d, a, b in zip(days, op, cl)]})
    oi = wsec.overnight_intraday(st, days[1:], days[-1], days[-1] + "T22:00:00+00:00")
    check(oi["totals"]["close_to_close_pct"] == true,
          f"the week prints {oi['totals']['close_to_close_pct']:+.2f}%, the tape's close "
          f"to close {true:+.2f}% (the old method printed {old:+.2f}%)")
    on, intr = oi["totals"]["overnight_pct"], oi["totals"]["intraday_pct"]
    check(abs((1 + on / 100) * (1 + intr / 100) - (1 + true / 100)) < 1e-3,
          "the overnight and intraday legs compound to the week")


def group_d() -> None:
    print(f"\n{LINE}\nD. THE WEEKLY'S TAGS\n{LINE}")
    from daily_cascade import weekly_stack as ws
    ed = edition("+1.16%", "+1.16%")
    secs = ed["sections"]
    for t in (secs[0]["table"], secs[0]["subsections"][0]["table"]):
        t.pop("facts", None)
    secs[0]["subsections"][0]["title"] = "SPY overnight against the cash session"
    secs.append({"id": "read", "title": "The read", "subsections": [],
                 "table": {"columns": ["Day", "SPY", "10-year"],
                           "rows": [["Fri 9 Oct", "+0.40%", "+3 bp"]]}})
    secs.append({"id": "plumbing", "title": "Plumbing & rates", "subsections": [],
                 "table": {"columns": ["Series", "Level or actual", "Week or prior",
                                       "As of"],
                           "rows": [["10-year", "4.120%", "+6 bp", "2026-10-09"]]}})
    secs[0]["table"]["rows"].append(["10-year yield", "4.120%", "+3 bp", "+6 bp", "—", "—"])
    book = {"instruments": [{"id": "y10", "frame": {"as_of": "2026-10-09",
                                                    "wtd_change_bps": 6}}]}
    ws.tag_facts(secs, [("spy", "2026-10-09"), ("y10", "2026-10-09")],
                 [{"day": "2026-10-09"}], [{"day": "2026-10-09"}], book)
    got = cons.collect(ed)
    check(len(got.get("spy|2026-10-09|week") or []) == 2
          and len(got.get("spy|2026-10-09|session") or []) == 3
          and len(got.get("y10|2026-10-09|session") or []) == 2
          and len(got.get("y10|2026-10-09|week") or []) == 2,
          f"the tape, the split, the week by day and Plumbing are tagged "
          f"({ {k: len(v) for k, v in got.items()} })")
    before = copy.deepcopy(ed)
    check(cons.reconcile(ed) == [] and ed["sections"] == before["sections"],
          "a consistent edition passes untouched")


def group_e() -> None:
    print(f"\n{LINE}\nE. THE RUN\n{LINE}")
    src = (REPO / "daily_cascade" / "weekly_stack.py").read_text(encoding="utf-8")
    i, j = src.find("consistency.reconcile(ed)"), src.find("stack_prose.write(ed")
    check(0 < i < j, "produce() reconciles before the prose is written")
    rep = (REPO / "daily_cascade" / "weekly_report.py").read_text(encoding="utf-8")
    check("except consistency.EditionInconsistent" in rep and "return 5" in rep
          and '"error", "stacked weekly failed the consistency gate"' in rep,
          "a mismatch beyond rounding exits 5 with an error state record")


def main() -> int:
    print(f"{LINE}\nTHE CROSS-TABLE CONSISTENCY GATE (W-1.1 item 1.1)\n{LINE}")
    group_a()
    group_b()
    group_c()
    group_d()
    group_e()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
