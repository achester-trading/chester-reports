"""
OS-9's outcome ledger: each printed OI build's chance in the money against whether
the contract finished in the money at expiry (signal-triage Batch 11 item 58, ruled
19 Oct 2026). Report-only.

WHAT IT READS. Our own chain captures on disk (altdata.chain_metrics.chain_dir(),
the box's data/chains), from which every session's printed table is rebuilt with
the anchor's own functions (opening_setup.builds_for, merge_spreads, the D6 floor,
the eight rows), and Yahoo's daily closes for each name at its contracts' expiries
(the one yfinance import). It never opens the observation store. On the laptop,
which holds no captures, the edition is INSUFFICIENT and says so.

WHAT THE FIRST EDITION PRE-REGISTERS (ruling 2 of 17 Oct: a re-run applies it and
may not change it):
  - the printed builds are the eight rows the anchor printed, rebuilt point in
    time from the two captures before each morning (a spread's legs are scored
    as separate contracts); SPX's and SPCX's builds, whose chance awaits the
    solver gate, are not scored;
  - a build resolves at its expiry's close: a call finishes in the money above
    its strike, a put below it; a build whose expiry is not yet past is
    unresolved;
  - with 30 or more resolved builds, the CALIBRATION TABLE prints by decile of
    the printed chance (n, mean printed chance, observed share, Wilson 95%);
  - PASS: 30 or more resolved, the printed chance's Brier score is below the
    base-rate forecast's (every build given the resolved builds' own in-the-money
    share), and every decile with 5 or more builds has its mean printed chance
    inside its Wilson 95% interval; INSUFFICIENT under 30; FAIL otherwise.

THE RIGHTS IT WOULD GRANT, STATED AND NOT GRANTED: a calibration statement beside
OS-9's "Chance in the money" column, nothing more. A PASS reaches the register only
as a rule-31 draft.

    python tools/calibration/os9_build_outcomes.py [--box] [--out DIR] [--date D]
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import st7_common as C                                          # noqa: E402

ITEM = "OS-9"
TITLE = "The OI builds' chance in the money, against the outcome at expiry (item 58)"
LAPTOP = "laptop run, our chain captures (none on the laptop) and public closes"
BOX = "box run, our chain captures and public closes"
MIN_RESOLVED, MIN_DECILE = 30, 5
PASS_RULE = ("With 30 or more resolved builds, the printed chance in the money's Brier "
             "score is below the base-rate forecast's (the resolved builds' own "
             "in-the-money share), and every decile with 5 or more builds has its mean "
             "printed chance inside its Wilson 95% interval; INSUFFICIENT under 30, FAIL "
             "otherwise. A spread's legs are scored as separate contracts; builds whose "
             "chance awaits the solver gate are not scored.")


def load(base: Optional[Path] = None) -> dict:
    """{builds: [{session, symbol, expiry, strike, right, p_itm}], closes: {sym: {day: close}}}."""
    from altdata import chain_metrics as cm, config as acfg     # noqa: PLC0415
    from daily_cascade import opening_setup as OS               # noqa: PLC0415
    root = Path(base) if base else cm.chain_dir()
    builds: list[dict] = []
    days = sorted(p.name for p in root.iterdir() if p.is_dir()) if root.is_dir() else []
    cfg = OS.config()
    for day in days:
        cand = []
        for s in acfg.chain_universe():
            cur = cm.latest_capture(day, root, s)
            prev = cm.previous_capture(day, s, root) if cur else None
            if not (cur and prev):
                continue
            cand += OS.builds_for(s, cm.load_rows(prev), cm.load_rows(cur),
                                  acfg.RISK_FREE_RATE, floor=OS.oi_floor(s, cfg))
        for b in OS.merge_spreads(cand)[:int(cfg["oi_builds"]["rows"])]:
            for leg in b["legs"]:
                if leg.get("p_itm") is not None:
                    builds.append({"session": day, "symbol": leg["symbol"],
                                   "expiry": str(leg["expiry"])[:10],
                                   "strike": float(leg["strike"]), "right": leg["right"],
                                   "p_itm": float(leg["p_itm"])})
    closes: dict[str, dict[str, float]] = {}
    if builds:
        from altdata.ledgers import sources as S                # noqa: PLC0415
        for sym in sorted({b["symbol"] for b in builds}):
            closes[sym] = dict(S.yahoo(sym))
    return {"builds": builds, "closes": closes, "sessions": len(days),
            "retrieved": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}


def resolve(b: dict, closes: dict[str, float], today: str) -> Optional[bool]:
    if b["expiry"] >= today or b["expiry"] not in closes:
        return None
    px = closes[b["expiry"]]
    return px > b["strike"] if b["right"] == "C" else px < b["strike"]


def study(d: dict, mode: str, today: Optional[str] = None) -> dict:
    today = today or dt.date.today().isoformat()
    rows = []
    for b in d["builds"]:
        out = resolve(b, d["closes"].get(b["symbol"]) or {}, today)
        rows.append({**b, "itm": out})
    res = [r for r in rows if r["itm"] is not None]
    n = len(res)
    body = [f"- {d.get('sessions', 0)} capture sessions read; {len(rows)} printed builds "
            f"rebuilt; {n} resolved at expiry."]
    if n < MIN_RESOLVED:
        verdict = f"{C.INSUFFICIENT} ({n} resolved builds; the floor is {MIN_RESOLVED})"
    else:
        base = sum(1 for r in res if r["itm"]) / n
        brier = sum((r["p_itm"] - float(r["itm"])) ** 2 for r in res) / n
        brier0 = sum((base - float(r["itm"])) ** 2 for r in res) / n
        table, ok = [], brier < brier0
        body += ["", "| Decile of the printed chance | n | Mean printed | Observed | "
                     "Wilson 95% |", "|---|---|---|---|---|"]
        for k in range(10):
            lo, hi = k / 10, (k + 1) / 10
            g = [r for r in res if lo <= r["p_itm"] < hi or (k == 9 and r["p_itm"] == 1.0)]
            if not g:
                continue
            obs = sum(1 for r in g if r["itm"])
            ci = C.wilson(obs, len(g)) if hasattr(C, "wilson") else None
            if ci is None:
                from altdata.dealer_scorecard import wilson         # noqa: PLC0415
                ci = wilson(obs, len(g))
            mp = sum(r["p_itm"] for r in g) / len(g)
            if len(g) >= MIN_DECILE and not (ci[0] <= mp <= ci[1]):
                ok = False
            body.append(f"| {lo:.1f}-{hi:.1f} | {len(g)} | {mp:.2f} | {obs / len(g):.2f} | "
                        f"{ci[0]:.2f}-{ci[1]:.2f} |")
            table.append(len(g))
        line = (f"{n} resolved; Brier {brier:.3f} against the base rate's {brier0:.3f} "
                f"(in the money {base * 100:.0f}%)")
        verdict = f"{C.PASS} ({line})" if ok else f"{C.FAIL} ({line})"
    return {"item": ITEM, "title": TITLE, "as_of": today,
            "window": f"every capture session on disk to {today}", "n": n,
            "statistic": "the printed chance in the money's Brier score against the base "
                         "rate's, and its calibration by decile",
            "pass_rule": PASS_RULE, "verdict": verdict,
            "rights": ("Would grant: a calibration statement beside OS-9's chance column, "
                       "nothing more. This ledger grants nothing. " + C.RIGHTS_NOTE),
            "sources": ["Our own chain captures (data/chains), rebuilt by the anchor's "
                        "functions", "Yahoo Finance daily closes at each expiry (the one "
                        f"yfinance import), retrieved {d.get('retrieved', '-')}"],
            "source_mode": mode, "body": body, "episodes": rows,
            "caveats": ["A build's side is unknown: the outcome says whether the contract "
                        "finished in the money, never who won.",
                        "The chance is Black-Scholes on our solver's IV at the later "
                        "capture; a deep-ITM build is near certain by construction."]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="OS-9's outcome ledger (item 58)")
    ap.add_argument("--box", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--date")
    a = ap.parse_args(argv)
    d = load()
    r = study(d, BOX if a.box else LAPTOP)
    C.publish(r, a.out, a.date or dt.date.today().isoformat())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
