#!/usr/bin/env python3
"""
Validation gate: DTH-1's box pieces (ruling D41, 27 Oct 2026; A92) -- the rules
checklist in the 07:00 anchor and the manual ledger's aggregates in the Weekly.

  A  THE CHECKLIST   it renders from config/dth1.yaml after the ES read, in the
                     HTML and the text edition, and the config's switch turns it off
  B  THE READER      its aggregates match a hand computation on a synthetic ledger;
                     a verify row and a blank result wait for the statement; a row
                     after the week is not counted; a missing column is named; no
                     file prints "not stored"
  C  PRIVACY         no currency symbol, no price, no row's date and no single
                     trade reaches the rendered text; the reader writes nothing and
                     reads the ledger from the box's inbox, never the repo
  D  THE WIRING      the anchor's payload and render carry the block, the Weekly's
                     book section the lines, and the sweep pulls the one file

The fixtures (tests/fixtures/dth1/) are SYNTHETIC: invented rows, no real trade,
price, size, P&L or account.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import datetime as dt                                           # noqa: E402

from altdata import dth1_ledger as dl                           # noqa: E402

LINE = "=" * 78
PASS = FAIL = 0
FIX = REPO / "tests" / "fixtures" / "dth1"
LEDGER = FIX / "synthetic-ledger.csv"
ENDING = dt.date(2026, 11, 1)                     # the week 26 Oct - 1 Nov 2026
PRICES = ("101.25", "102.75", "99.75", "100.25", "103.10", "104.90", "102.40",
          "101.40", "100.80", "101.00", "101.50", "104.00", "106.50")
DATES = ("2026-10-20", "2026-10-22", "2026-10-27", "2026-10-28", "2026-10-29",
         "2026-10-30", "2026-11-03")
CURRENCY = re.compile(r"[$€£¥]|\bUSD\b|\bdollars?\b", re.I)


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


def group_a() -> None:
    head("A. THE CHECKLIST")
    cfg = dl.config()
    blk = dl.checklist(cfg)
    text = "\n".join(blk["lines"])
    check(blk["enabled"] and blk["title"] == "Day-trade rules (DTH-1)"
          and len(blk["lines"]) == 5,
          f"it renders the title and five lines from config ({len(blk['lines'])})")
    check(all(w in text for w in ("right side of the structure", "risk budget",
                                  "after each fill", "60 minutes of a stop-out",
                                  "15:45 ET", "+1R", "range edge", "2R of room",
                                  "backdrop agrees")),
          "the four rules and the promotion test are all there")
    html = dl.checklist_html(blk)
    check("<h2" in html and html.count("<li>") == 5, "the HTML block: a heading and five items")
    off = dict(cfg, checklist={**cfg["checklist"], "enabled": False})
    check(not dl.checklist(off)["lines"] and dl.checklist_html(dl.checklist(off)) == ""
          and dl.checklist_text(dl.checklist(off)) == [],
          "the config's switch turns the block off: no lines, no HTML, no text")
    from daily_cascade import morning_render as mr              # noqa: PLC0415
    src = (REPO / "daily_cascade" / "morning_render.py").read_text(encoding="utf-8")
    es_at = src.find("{es_section(payload, es)}")
    check(0 < es_at < src.find('dth1_ledger.checklist_html(payload.get("dth1_checklist"))'),
          "the anchor prints it straight after the ES read")
    lines = mr.text_fallback({"session": "2026-10-30", "dth1_checklist": blk})
    check("Day-trade rules (DTH-1)" in lines and "15:45 ET" in lines,
          "and the text edition carries it")


def group_b() -> None:
    head("B. THE READER")
    a = dl.read(str(LEDGER), ENDING)
    # By hand: the scored rows are 20, 22, 27 and 28 Oct, R +1.5, -0.5, +2.0,
    # -1.0; 22 Oct broke a rule; 27 Oct was promoted; 29 Oct (blank result) and
    # 30 Oct (verify) wait for the statement; 3 Nov is after the week.
    want = {"week_n": 2, "total_n": 4, "clean_n": 3, "wins": 2, "promotions": 1,
            "awaiting": 2}
    check(all(a.get(k) == v for k, v in want.items()),
          f"counts match the hand computation ({ {k: a.get(k) for k in want} })")
    check(abs(a["mean_r"] - 0.5) < 1e-9 and abs(a["median_r"] - 0.5) < 1e-9
          and abs(a["clean_share"] - 0.75) < 1e-9 and abs(a["win_rate"] - 0.5) < 1e-9
          and a["largest_loss_r"] == -1.0,
          "mean +0.50R, median +0.50R, 75% clean, 50% wins, largest loss -1.00R")
    lines = dl.weekly_lines(a)
    check(lines[0] == "DTH-1 (manual): 2 trade(s) this week, 4 to date; no rule "
          "broken in 3 of 4 (75%); R per trade mean +0.50R, median +0.50R; win rate "
          "50% (2 of 4); largest loss −1.00R; promotions to Book C: 1.",
          f"the Weekly's line ({lines[0]})")
    check("2 row(s) awaiting the statement." in lines,
          "the verify row and the blank result are counted as awaiting, never scored")
    m = dl.read(str(FIX / "synthetic-ledger-no-result.csv"), ENDING)
    ml = dl.weekly_lines(m)
    check(m["state"] == "missing_columns" and "result_r" in ml[0]
          and "nothing is scored" in ml[0],
          f"a missing column is named, not guessed ({ml[0]})")
    nf = dl.weekly_subsection("2026-11-01", str(FIX / "no-such-ledger.csv"))
    check(nf["lines"] == ["DTH-1 ledger not stored."], f"no file: {nf['lines']}")


def group_c() -> None:
    head("C. PRIVACY")
    sub = dl.weekly_subsection("2026-11-01", str(LEDGER))
    out = "\n".join(sub["lines"] + dl.checklist_text(dl.checklist())
                    + [dl.checklist_html(dl.checklist())])
    check(not CURRENCY.search(out), "no currency symbol or word reaches the text")
    check(not any(p in out for p in PRICES), "no entry or exit price reaches the text")
    check(not any(d in out for d in DATES), "no single trade's date reaches the text")
    check(not any(k in str(sub["data"]) for k in ("long", "short") + PRICES),
          "the section's data holds aggregates only: no side, no price")
    tree = ast.parse((REPO / "altdata" / "dth1_ledger.py").read_text(encoding="utf-8"))
    names = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)} | \
        {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    writes = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
              and getattr(n.func, "attr", "") in ("write_text", "write_many", "write")]
    check(not ({"altdata.observations", "observations"} & names) and not writes,
          "the reader imports no store and writes nothing")
    cfg = dl.config()
    check(cfg["ledger"]["path"].startswith("~/chester-data/inbox/dth1/"),
          f"the ledger is read from the box's inbox ({cfg['ledger']['path']})")
    real = list((REPO).glob("**/dth1-manual-ledger.csv"))
    check(not real, f"no ledger file named like the real one is in the repo ({real})")


def group_d() -> None:
    head("D. THE WIRING")
    pay = (REPO / "daily_cascade" / "morning_payload.py").read_text(encoding="utf-8")
    check('"dth1_checklist": dth1' in pay and "dth1_ledger.checklist()" in pay,
          "the anchor's payload carries the checklist")
    ws = (REPO / "daily_cascade" / "weekly_stack.py").read_text(encoding="utf-8")
    check("dth1_subsection(ending)" in ws and 'subs.append({"title": dth1["title"]' in ws,
          "the Weekly's book section carries the DTH-1 lines after Book B")
    sync = (REPO / "scripts" / "rclone_sync.sh").read_text(encoding="utf-8")
    check(re.search(r"^pull_inbox_file dth1 dth1-manual-ledger\.csv \|\| true$", sync, re.M)
          is not None, "the nightly sweep pulls the one file into the dth1 inbox")


def main() -> int:
    group_a()
    group_b()
    group_c()
    group_d()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
