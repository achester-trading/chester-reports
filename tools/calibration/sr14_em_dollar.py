"""
SR-14 -- EM against the world, split by the dollar (signal-triage ST-8;
st-t3-calib, 18 Oct 2026).

    python tools/calibration/sr14_em_dollar.py [--box] [--out DIR] [--date D]

THE REGISTER'S FLAG AND GATE (docs/signal-triage-register.md, SR-14). Flag:
"relative trend break: 12m EM/World relative return > 0 and ratio above its 24m
average". Gate: "Episodes: 1988, 2001, 2016 (false), 2024. Statistic: forward 36m
EM/World relative return after the flag fires, split by real-dollar 12m change
sign. Pass: the dollar cell discriminates (2016 in the dollar-up failure cell).
If not, flag only."

WHAT OUR SOURCES ALLOW. MSCI's own index history is not keyless, so the laptop
edition reads the ETF proxies through Yahoo, total return: EEM (from April 2003)
against ACWI (from March 2008) -- the EM/World ratio -- and, labelled auxiliary
and never judged, EEM against SPY from 2003 (EM against the US, a longer line but
not the register's object). The real broad dollar is FRED's RTWEXBGS, from 2006.
So 1988 and 2001 are out of reach: they come from the register's cited chart as
SOURCED COMPARISONS, never as episodes of ours, and 2024's 36 months have not
completed.

WHAT THE FIRST EDITION PRE-REGISTERS, where the register is silent: month-end
total-return closes; the flag FIRES in a month it is on after a month it was off;
episodes are firings more than 1,095 days after the previous episode's start (no
shared 36-month window); the dollar cell is the sign of RTWEXBGS's 12-month change
at the firing month. THE RULE: at least 2 completed episodes in each dollar cell
(else INSUFFICIENT); PASS when the dollar-down cell's mean forward 36-month
relative return is positive, the dollar-up cell's is negative, and a 2016 firing,
if there is one, sits in the dollar-up cell with a negative return. Otherwise
FAIL: flag only, display.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import st8_common as C                                           # noqa: E402

ITEM = "SR-14"
REL_M, AVG_M, H = 12, 24, 36
GAP_DAYS = 1095
CELL_FLOOR = 2
SOURCED_14 = ("the register's cited chart (Topdown Charts / LSEG; MSCI EM from 1987, "
              "24 Sep 2026): completed relative turns in 1988, 1994, 2001 and 2010, each "
              "within about a year of a dollar turn; 2016-18 the instructive false start; "
              "2024's uptick from a 25-year low")


def load_public() -> dict:
    from altdata.ledgers import sources as S
    return {"eem": C.monthly_last(C.yahoo_tr("EEM")),
            "acwi": C.monthly_last(C.yahoo_tr("ACWI")),
            "spy": C.monthly_last(C.yahoo_tr("SPY")),
            "dollar": C.monthly_last(S.fred("RTWEXBGS"))}


def flag_series(a: C.Monthly, b: C.Monthly) -> dict[str, bool]:
    """{month: the flag} on the ratio a/b: its 12-month change > 0 and the ratio
    above its own trailing 24-month mean (that month included)."""
    ms = sorted(set(a) & set(b))
    r = {m: a[m] / b[m] for m in ms}
    out = {}
    for i, m in enumerate(ms):
        if i < AVG_M - 1 or C.madd(m, -REL_M) not in r:
            continue
        avg = sum(r[x] for x in ms[i - AVG_M + 1:i + 1]) / AVG_M
        out[m] = r[m] / r[C.madd(m, -REL_M)] - 1 > 0 and r[m] > avg
    return out


def firings(flags: dict[str, bool]) -> list[str]:
    ms = sorted(flags)
    on = [m for i, m in enumerate(ms) if flags[m] and i and not flags[ms[i - 1]]]
    return [d[:7] for d in C.first_of_runs([m + "-01" for m in on], GAP_DAYS)]


def fwd_rel(a: C.Monthly, b: C.Monthly, m: str, h: int):
    e = C.madd(m, h)
    if m not in a or m not in b or e not in a or e not in b:
        return None
    return (a[e] / a[m]) / (b[e] / b[m]) - 1


def dollar_cell(dollar: C.Monthly, m: str):
    p = dollar.get(C.madd(m, -12))
    return None if p is None or m not in dollar else ("up" if dollar[m] > p else "down")


def judge(eps: list[dict]) -> dict:
    done = [e for e in eps if e["fwd_36m"] is not None and e["dollar"]]
    up = [e["fwd_36m"] for e in done if e["dollar"] == "up"]
    dn = [e["fwd_36m"] for e in done if e["dollar"] == "down"]
    y16 = [e for e in done if e["fired"].startswith("2016")]
    if len(up) < CELL_FLOOR or len(dn) < CELL_FLOOR:
        word = C.INSUFFICIENT
    else:
        ok16 = all(e["dollar"] == "up" and e["fwd_36m"] < 0 for e in y16)
        word = C.PASS if C.mean(dn) > 0 > C.mean(up) and ok16 else C.FAIL
    return {"n": len(done), "up": up, "dn": dn, "word": word}


def episodes(a, b, dollar, label) -> list[dict]:
    return [{"set": label, "fired": m, "dollar": dollar_cell(dollar, m),
             "fwd_12m": fwd_rel(a, b, m, 12), "fwd_36m": fwd_rel(a, b, m, H)}
            for m in firings(flag_series(a, b))]


def study(d: dict, mode: str) -> dict:
    main = episodes(d["eem"], d["acwi"], d["dollar"], "EEM/ACWI (EM/World)")
    aux = episodes(d["eem"], d["spy"], d["dollar"], "EEM/SPY (auxiliary, not judged)")
    j = judge(main)
    if j["word"] == C.INSUFFICIENT:
        verdict = (f"{C.INSUFFICIENT} -- the dollar cell cannot be tested on our n: "
                   f"{len(j['up'])} completed episode(s) in the dollar-up cell and "
                   f"{len(j['dn'])} in the dollar-down cell (floor {CELL_FLOOR} each; "
                   f"{j['n']} completed in all, EEM/ACWI from 2008); the flag stays "
                   f"display only")
    else:
        verdict = (f"{j['word']} -- dollar-down mean 36m relative "
                   f"{C.pct(C.mean(j['dn']))} (n {len(j['dn'])}) against dollar-up "
                   f"{C.pct(C.mean(j['up']))} (n {len(j['up'])})")
    fl = flag_series(d["eem"], d["acwi"])
    now = max(fl)
    body = [f"The flag now ({now}): **{'on' if fl[now] else 'off'}** on EEM/ACWI.", "",
            "| Set | Fired | Real dollar, 12m | Relative, 12m | Relative, 36m |",
            "|---|---|---|---|---|"]
    for e in main + aux:
        body.append(f"| {e['set']} | {e['fired']} | {e['dollar'] or 'n/a (before 2007)'} | "
                    f"{C.pct(e['fwd_12m'])} | {C.pct(e['fwd_36m'])} |")
    body += ["", f"**Sourced comparison, not episodes of ours:** {SOURCED_14}. The "
             "register's 1988 and 2001 episodes are the chart's; MSCI's history is not "
             "keyless, and our proxies begin in 2003 (EEM) and 2008 (ACWI)."]
    return {
        "item": ITEM, "title": "EM against the world after the trend flag, split by the dollar",
        "as_of": f"EEM/ACWI {max(set(d['eem']) & set(d['acwi']))}; RTWEXBGS {max(d['dollar'])}",
        "window": f"{min(set(d['eem']) & set(d['acwi']))} to {max(set(d['eem']) & set(d['acwi']))} "
                  f"(EEM/ACWI); {min(set(d['eem']) & set(d['spy']))} on (EEM/SPY, auxiliary)",
        "n": j["n"],
        "statistic": "forward 36-month EM/World relative total return after the flag "
                     "fires, split by the sign of the real broad dollar's 12-month change",
        "pass_rule": ("the register's: the dollar cell discriminates (2016 in the dollar-up "
                      "failure cell); if not, flag only. Pre-registered by this first "
                      f"edition: at least {CELL_FLOOR} completed episodes a cell, dollar-down "
                      "mean > 0 > dollar-up mean, 2016 in the dollar-up cell and negative"),
        "verdict": verdict,
        "rights": ("PASS: the narrow flag and the Book A tilt modifier conditioned on the "
                   "dollar regime tag, SR-4's tell as exit; the US-vs-RoW block renders. "
                   "FAIL or INSUFFICIENT: flag only, display; nothing new renders. "
                   + C.RIGHTS_NOTE),
        "sources": ["Yahoo daily closes, auto-adjusted (altdata.import_yfinance): EEM "
                    "from 2003-04, ACWI from 2008-03, SPY",
                    "FRED graph CSV (no key): RTWEXBGS, the real broad dollar, from 2006",
                    "MSCI's end-of-month history is not keyless: not read"],
        "source_mode": mode, "body": body, "episodes": main + aux,
        "caveats": ["The ETFs are proxies with their own fees and tracking; EEM's "
                    "composition (Taiwan, Korea, China tech about 40%) is the register's "
                    "own warning that the absolute line is partly the AI-semis trade.",
                    C.CONFIG_NOTE]}


if __name__ == "__main__":
    raise SystemExit(C.cli(ITEM, load_public, study))
