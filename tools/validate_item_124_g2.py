#!/usr/bin/env python3
"""
Validation gate: DTH-1's constant-dollar-risk sizing (signal-triage Batch 23
item 124g(ii); D63's D8: structure sets the stop, the ATR multiple is its floor,
size = fixed dollar risk / stop distance). A130, 6 Nov 2026.

EVERY FIGURE HERE IS INVENTED: the account base, the bars and the ledger rows
are synthetic, written to a temporary directory by this gate and deleted after.
No real trade, account value or ledger is read or committed.

  A  THE FLOOR: stop distance = max(structural, k x ATR); the floor alone with
     no stop named; the structural stop alone, unfloored and said so, with no ATR.
  B  THE ROUNDING: floor(risk / (distance x point value)); MES when ES rounds to
     zero; "below one MES contract" when MES does too; MES asked directly.
  C  THE NO-BASE PATH: no file, no column, no dated row -- the block prints
     "account base not found in chester-cards (dth1-account-base.csv)" and sizes
     nothing; never read from the repo.
  D  THE PLAN BLOCK on an invented base and ATR: risk and daily limit in dollars,
     the ATR, the floor, k and its hook ("not built"), ES and MES at three
     candidate stop distances; the base itself never printed.
  E  THE ATR from consecutive daily bars (the volatile-day flag's true ranges).
  F  THE LEDGER'S TWO NEW COLUMNS: floor_applied counted when the column exists,
     nothing printed without it; atr_at_entry never read.
  G  NO ORDER PATH: no broker, order or register import in the module (AST and a
     fresh interpreter, validate_alpha_no_orders' pattern), no order identifier;
     the anchor's payload and renderer carry the block; no halve-size line is in
     DTH-1's pieces (124g(ii) item 3: none to retire).

    python tools/validate_item_124_g2.py
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import ast
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

TD = Path(gate_mkdtemp("item_124_g2_"))
LINE = "=" * 78
PASS = FAIL = 0
# The clock is pinned to the fixture's day (B106): nothing here reads today.
GATE_NOW = "2026-11-09T11:30:00+00:00"
DAY = "2026-11-09"
INVENTED_BASE = 50000.0   # an invented account base, for the arithmetic only
BROKER = ("register", "altdata.executions", "altdata.sources.ibkr_portfolio",
          "altdata.sources.ibkr_costs", "altdata.sources.ibkr_whatif",
          "ib_insync", "ib_async", "ibapi", "ibkr", "paper_exec")
ORDER_IDENTIFIERS = {"placeOrder", "place_order", "bracketOrder", "submit_order",
                     "order_router", "ibkr_orders", "execution_framework",
                     "reqGlobalCancel"}


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


def base_file(name: str, rows: list[tuple[str, str]], header=("Date", "Account base")) -> str:
    p = TD / name
    p.write_text("\n".join([",".join(header)] + [f"{d},{v}" for d, v in rows]) + "\n",
                 encoding="utf-8")
    return str(p)


def cfg_with(base_path: str) -> dict:
    from altdata import dth1_sizing as sz                       # noqa: PLC0415
    c = sz.config()
    c["sizing"] = {**c["sizing"], "base_path": base_path}
    return c


def group_a(sz) -> None:
    head("A. THE FLOOR: STRUCTURE SETS THE STOP; k x ATR IS ITS FLOOR")
    r = sz.stop_distance(5.0, 10.0, 1.0)
    check(r["distance"] == 10.0 and r["floor"] == 10.0 and r["floor_applied"],
          "a structural stop tighter than the floor is floored (5 -> 10)")
    r = sz.stop_distance(15.0, 10.0, 1.0)
    check(r["distance"] == 15.0 and not r["floor_applied"],
          "a structural stop wider than the floor stands (15)")
    r = sz.stop_distance(None, 10.0, 1.5)
    check(r["distance"] == 15.0 and r["floor_applied"],
          "no stop named: the floor alone, k x ATR (1.5 x 10)")
    r = sz.stop_distance(8.0, None, 1.0)
    check(r["distance"] == 8.0 and r["floor"] is None and "unfloored" in r["reason"],
          "no ATR stored: the structural stop alone, unfloored, and said so")
    check(sz.stop_distance(None, None, 1.0)["distance"] is None,
          "no stop and no ATR: nothing is sized")


def group_b(sz) -> None:
    head("B. THE ROUNDING: ES, THEN MES, THEN BELOW ONE MES CONTRACT")
    cfg = sz.config()
    risk = INVENTED_BASE * 0.01
    c = sz.contracts(risk, 10.0, cfg, "ES")
    check(c["instrument"] == "ES" and c["contracts"] == 1 and c["risk_at_size"] == 500.0,
          f"$500 at a 10-point stop: 1 ES ($50 a point) ({c})")
    c = sz.contracts(risk, 4.0, cfg, "ES")
    check(c["instrument"] == "ES" and c["contracts"] == 2,
          "$500 at a 4-point stop: floor(2.5) = 2 ES")
    c = sz.contracts(risk, 12.0, cfg, "ES")
    check(c["instrument"] == "MES" and c["contracts"] == 8 and c.get("rounded_from") == "ES",
          f"ES rounds to zero at 12 points, so MES: floor(500 / 60) = 8 ({c})")
    c = sz.contracts(risk, 150.0, cfg, "ES")
    check(c["contracts"] == 0 and c["reason"] == "below one MES contract",
          "at 150 points even MES rounds to zero: 'below one MES contract'")
    c = sz.contracts(risk, 10.0, cfg, "MES")
    check(c["instrument"] == "MES" and c["contracts"] == 10 and "rounded_from" not in c,
          "MES asked directly: floor(500 / 50) = 10")
    check(sz.contracts(None, 10.0, cfg)["reason"] == sz.NO_BASE,
          "no base: no contracts, 'no base'")


def group_c(sz) -> None:
    head("C. THE NO-BASE PATH")
    miss = str(TD / "absent" / sz.BASE_FILE)
    b = sz.account_base(miss, DAY, cfg_with(miss))
    check(b.get("base") is None and b["reason"] == sz.BASE_NOT_FOUND,
          f"no file: '{sz.BASE_NOT_FOUND}'")
    blk = sz.plan_block(DAY, GATE_NOW, None, miss, cfg_with(miss),
                        atr_override={"atr": 20.0, "n": 14})
    check(blk["lines"] == [sz.BASE_NOT_FOUND] and blk["table"] is None,
          "the anchor's block prints that one line and sizes nothing")
    nocol = base_file("nocol.csv", [("2026-11-06", "50000")], header=("Date", "Notes"))
    b = sz.account_base(nocol, DAY, cfg_with(nocol))
    check(b.get("base") is None and "no account base column" in b["reason"],
          "a file without the base column is named, never guessed")
    late = base_file("late.csv", [("2026-11-20", "50000")])
    b = sz.account_base(late, DAY, cfg_with(late))
    check(b.get("base") is None and "no dated row on or before" in b["reason"],
          "a base dated after the day is not used")
    cfgp = sz.config()["sizing"]["base_path"]
    check(cfgp.startswith("~/chester-data/inbox/") and "chester-reports" not in cfgp,
          "the configured base path is the box's inbox, never the repo")
    check(not list(REPO.rglob(sz.BASE_FILE)),
          "no file named like the real account base is in the repo")


def group_d(sz) -> None:
    head("D. THE PLAN BLOCK ON AN INVENTED BASE AND ATR")
    p = base_file("base.csv", [("2026-10-30", "48000"), ("2026-11-06", '"$50,000"'),
                               ("2026-11-20", "99000")])
    cfg = cfg_with(p)
    b = sz.account_base(p, DAY, cfg)
    check(b["base"] == INVENTED_BASE and b["as_of"] == "2026-11-06",
          "the newest row on or before the day ('$' and ',' read), never a later one")
    blk = sz.plan_block(DAY, GATE_NOW, None, p, cfg, atr_override={"atr": 20.0, "n": 14})
    text = "\n".join(sz.plan_text(blk))
    print("    --- the block, on the invented fixture ---")
    for ln in sz.plan_text(blk):
        print(f"    {ln}")
    check("Risk per trade $500" in text and "daily limit $1,000" in text,
          "risk 1% = $500 and the daily limit 2% = $1,000, in dollars")
    check("ATR(14) 20.00 points (n=14)" in text and "floor is k x ATR = 20.00" in text
          and "not built" in text,
          "the ATR, the floor and k's hook ('not built')")
    rows = blk["table"]["rows"]
    check(len(rows) == 3 and rows[0][0].startswith("1 x ATR = 20.00")
          and rows[1][0].startswith("1.5 x ATR = 30.00")
          and rows[2][0].startswith("2 x ATR = 40.00"),
          "three candidate stop distances, 1, 1.5 and 2 x ATR")
    # $500 at 20 points: ES floor(500/1000) = 0, MES floor(500/100) = 5.
    check(rows[0][1].startswith("0") and rows[0][2] == "5" and rows[0][3] == "$500",
          f"at 20 points ES rounds to zero and MES is 5 ({rows[0]})")
    check(rows[2][2] == "2" and rows[2][3] == "$400",
          f"at 40 points MES is floor(500/200) = 2, $400 at that size ({rows[2]})")
    check("50,000" not in text and "50000" not in text and "48,000" not in text,
          "the base itself is never printed")
    html = sz.plan_html(blk)
    check("<table>" in html and "MES contracts" in html and "50,000" not in html,
          "the HTML edition carries the table, never the base")
    noatr = sz.plan_block(DAY, GATE_NOW, None, p, cfg,
                          atr_override={"atr": None, "n": 0, "reason": "no bars"})
    check(noatr["table"] is None and "not read (no bars)" in "\n".join(noatr["lines"]),
          "no ATR stored: the risk prints, nothing is sized, and the reason is named")
    off = {**cfg, "sizing": {**cfg["sizing"], "enabled": False}}
    check(sz.plan_block(DAY, GATE_NOW, None, p, off)["enabled"] is False
          and sz.plan_text({"enabled": False}) == [],
          "the switch off prints nothing")
    check(sz.vol_state_k() is None and "not built" in sz.k_value()[1],
          "the vol state's hook reads 'not built'; config's k applies")


def group_e(sz) -> None:
    head("E. THE ATR FROM CONSECUTIVE DAILY BARS")
    bars = [{"high": 105, "low": 95, "close": 100}, {"high": 108, "low": 99, "close": 104},
            {"high": 104, "low": 90, "close": 92}, {"high": 99, "low": 93, "close": 98}]
    a, n = sz.atr(bars, 14)
    # true ranges: max(108,100)-min(99,100) = 9; max(104,104)-min(90,104) = 14;
    # max(99,92)-min(93,92) = 7 -> mean 10.
    check(n == 3 and abs(a - 10.0) < 1e-9, f"Wilder's true range, averaged ({a}, n={n})")
    a2, n2 = sz.atr(bars, 2)
    check(n2 == 2 and abs(a2 - 10.5) < 1e-9, "only the last n true ranges")
    check(sz.atr([], 14) == (None, 0), "no bars: no ATR")


def group_f() -> None:
    head("F. THE LEDGER'S TWO NEW COLUMNS (INVENTED ROWS)")
    from altdata import dth1_ledger as dl                       # noqa: PLC0415
    p = TD / "ledger.csv"
    p.write_text("date,result_r,rule_broken,status,atr_at_entry,floor_applied\n"
                 "2026-11-02,1.0,n,,17.25,y\n2026-11-03,-1.0,n,,18.5,\n"
                 "2026-11-04,0.5,y,,19.0,yes\n", encoding="utf-8")
    agg = dl.read(str(p), dt.date(2026, 11, 8))
    lines = dl.weekly_lines(agg)
    check(agg["floor_column"] and agg["floor_applied"] == 2
          and "The ATR floor set the stop in 2 of 3." in lines,
          f"floor_applied counted (2 of 3) ({lines})")
    check(not any("17.25" in ln or "18.5" in ln for ln in lines),
          "atr_at_entry is never printed")
    q = TD / "old.csv"
    q.write_text("date,result_r,rule_broken\n2026-11-02,1.0,n\n", encoding="utf-8")
    l2 = dl.weekly_lines(dl.read(str(q), dt.date(2026, 11, 8)))
    check(not any("ATR floor" in ln for ln in l2), "without the column: nothing printed")
    cols = dl.config()["ledger"]["columns"]
    check("floor_applied" in cols and "atr_at_entry" not in cols
          and "atr_at_entry" in (REPO / "config" / "dth1.yaml").read_text(encoding="utf-8"),
          "floor_applied is read; atr_at_entry is documented and never read")


def group_g() -> None:
    head("G. NO ORDER PATH; THE ANCHOR CARRIES THE BLOCK; NO HALVE-SIZE LINE")
    src = (REPO / "altdata" / "dth1_sizing.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    mods = [n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)] + \
        [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
    bad = [m for m in mods if any(m == f or m.startswith(f + ".") for f in BROKER)]
    check(not bad, f"no broker, order or register import in the source ({bad})")
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | \
        {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    check(not (names & ORDER_IDENTIFIERS), "no order identifier is used")
    code = ("import json, sys\n"
            f"sys.path.insert(0, {str(REPO)!r})\n"
            "import altdata.dth1_sizing as s\n"
            "s.contracts(500.0, 10.0)\n"
            "print(json.dumps(sorted(sys.modules)))\n")
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                       cwd=str(REPO), timeout=300)
    loaded = json.loads(r.stdout.strip().splitlines()[-1]) if r.returncode == 0 else []
    hit = [m for m in loaded if any(m == f or m.startswith(f + ".") for f in BROKER)]
    check(r.returncode == 0 and not hit,
          f"in a fresh interpreter, importing and sizing loads no broker module "
          f"({len(loaded)} loaded{'; ' + ', '.join(hit) if hit else ''})")
    mp = (REPO / "daily_cascade" / "morning_payload.py").read_text(encoding="utf-8")
    mr = (REPO / "daily_cascade" / "morning_render.py").read_text(encoding="utf-8")
    check('"dth1_sizing": dth1_size' in mp and "dth1_sizing.plan_block(" in mp
          and "dth1_sizing.plan_text(" in mr and "dth1_sizing.plan_html(" in mr
          and mr.find("dth1_sizing.plan_text(") > mr.find("dth1_ledger.checklist_text("),
          "the 07:00 payload carries the block; both editions print it after the checklist")
    pieces = [REPO / "config" / "dth1.yaml", REPO / "altdata" / "dth1_ledger.py",
              REPO / "docs" / "briefs" / "a92-notes.md"]
    check(not any("halve" in p.read_text(encoding="utf-8").lower()
                  or "bottom-decile" in p.read_text(encoding="utf-8").lower()
                  for p in pieces),
          "a92's DTH-1 pieces carry no halve-size line, so none is retired")


def main() -> int:
    pin_clock()
    print(f"the gate's clock is pinned to {GATE_NOW}")
    print("Every figure in this gate is invented (synthetic fixtures).")
    from altdata import dth1_sizing as sz                       # noqa: PLC0415
    try:
        for g in (group_a, group_b, group_c, group_d, group_e):
            g(sz)
        group_f()
        group_g()
    finally:
        import shutil                                           # noqa: PLC0415
        shutil.rmtree(TD, ignore_errors=True)
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
