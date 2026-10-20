"""
SR-21 -- the Fed-market divergence episodes, conceded or refused (signal-triage
ST-7; st-t2-rates, 18 Oct 2026).

    python tools/calibration/sr21_divergence.py [--box] [--out DIR] [--date D]

THE REGISTER'S GATE (docs/signal-triage-register.md, SR-21). "Episodes of >= 50
bp divergence within 3 months (1994, 1998, 2007, 2013, 2018, 2022, 2024).
Statistic: forward 3m 10y change and equity return split by conceded / refused.
Pass: the split separates the long-end outcome. First live test: 28 Oct 2026."

THE TWO LEGS over history. The live feature (calc.fed_mkt_gap_12m, ST-4) is the
futures-implied rate twelve months out less the SEP median dot (FEDTARMD). Neither
has a keyless history: FRED's graph CSV serves only the current SEP's vintage
(four years from 2026), and fed funds futures prices are not free before
yfinance's recent contracts. So the first edition pre-registers the longest
keyless pair:
  market   the 1-year constant-maturity yield (DGS1): the average funds rate the
           market expects over the coming year, plus a small premium
  the Fed  the funds-rate target: DFEDTAR to 15 Dec 2008, then the midpoint of
           DFEDTARL and DFEDTARU -- the path the Fed is holding, with no move
           signalled
  gap      market less the Fed, in bp; a DIVERGENCE starts the first session
           its change over 63 sessions reaches 50 bp either way, and no new
           episode starts within 126 sessions of the last.
CONCEDED: the target moves at least 25 bp in the gap's direction within 63
sessions of the start; otherwise REFUSED. The outcome is DGS10's change and the
S&P 500's price return (^GSPC) over the next 63 sessions, the 10-year's
sign-aligned to the divergence (positive = the long end moved the way the market
had leaned).

THE RULE, pre-registered: the split separates when the refused episodes'
median aligned 10-year change exceeds the conceded's by at least 25 bp (the
register's mechanism: a refused Fed reprices the long end through the term
premium; a conceding one flattens the curve). FLOOR: five completed episodes,
at least two in each group; below it no split prints.

Point in time: DGS1, DGS10 and the targets are not revised; ^GSPC closes are
not revised. The order's named years are listed with whether the rule finds an
episode in them.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import st7_common as C                                           # noqa: E402

ITEM = "SR-21"
WIDEN_BP = 50.0
LOOK = 63
QUIET = 126
CONCEDE_BP = 25.0
SEPARATE_BP = 25.0
FLOOR, FLOOR_GROUP = 5, 2
NAMED = ("1994", "1998", "2007", "2013", "2018", "2022", "2024")


def load_public() -> dict:
    from altdata.ledgers import sources as S
    return {"dgs1": S.fred("DGS1"), "dgs10": S.fred("DGS10"),
            "tar": S.fred("DFEDTAR"), "tar_l": S.fred("DFEDTARL"),
            "tar_u": S.fred("DFEDTARU"), "spx": S.yahoo("^GSPC")}


def target(d: dict) -> dict[str, float]:
    out = dict(d["tar"])
    lo = dict(d["tar_l"])
    for day, u in d["tar_u"]:
        if day in lo:
            out[day] = (u + lo[day]) / 2.0
    return out


def gap_series(d: dict) -> C.Daily:
    """[(day, DGS1 - target, in bp)] on the days both are held (the target
    carried forward over days it has no row)."""
    tar = target(d)
    days = sorted(tar)
    out, j, cur = [], 0, None
    for day, y in d["dgs1"]:
        while j < len(days) and days[j] <= day:
            cur = tar[days[j]]
            j += 1
        if cur is not None and day >= days[0]:
            out.append((day, 100.0 * (y - cur)))
    return out


def episodes(gap: C.Daily) -> list[tuple[int, int]]:
    """[(index into gap, direction +1/-1)] by the pre-registered rule."""
    out, last = [], -10 ** 9
    for i in range(LOOK, len(gap)):
        ch = gap[i][1] - gap[i - LOOK][1]
        if abs(ch) >= WIDEN_BP and i - last > QUIET:
            out.append((i, 1 if ch > 0 else -1))
            last = i
    return out


def judge(rows: list[dict]) -> dict:
    """The pre-registered split over the episodes; the verdict carries its
    inputs."""
    done = [r for r in rows if r["completed"]]
    con = [r for r in done if r["outcome"] == "conceded"]
    ref = [r for r in done if r["outcome"] == "refused"]
    mc = C.median([r["d10_aligned_bp"] for r in con])
    mr = C.median([r["d10_aligned_bp"] for r in ref])
    if len(done) < FLOOR or len(con) < FLOOR_GROUP or len(ref) < FLOOR_GROUP:
        verdict = (f"{C.INSUFFICIENT} -- {len(done)} completed ({len(con)} conceded, "
                   f"{len(ref)} refused); floor {FLOOR}, {FLOOR_GROUP} a group; no split prints")
    else:
        ok = mr - mc >= SEPARATE_BP
        verdict = (f"{C.PASS if ok else C.FAIL} -- refused median "
                   f"{C.f2(mr, 1, ' bp')} vs conceded {C.f2(mc, 1, ' bp')} "
                   f"(rule: refused exceeds conceded by >= {SEPARATE_BP:.0f} bp)")
    return {"done": done, "con": con, "ref": ref, "mc": mc, "mr": mr,
            "verdict": verdict}


def study(d: dict, mode: str) -> dict:
    gap = gap_series(d)
    tar = target(d)
    tdays = sorted(tar)
    ten, spx = d["dgs10"], d["spx"]

    def tar_on(day):
        import bisect
        k = bisect.bisect_right(tdays, day) - 1
        return tar[tdays[k]] if k >= 0 else None

    rows = []
    for i, sgn in episodes(gap):
        day = gap[i][0]
        end = gap[i + LOOK][0] if i + LOOK < len(gap) else None
        t0, t1 = tar_on(day), (tar_on(end) if end else None)
        moved = None if t1 is None else 100.0 * (t1 - t0) * sgn
        j10, js = C.index_on_or_before(ten, day), C.index_on_or_before(spx, day)
        d10 = None if j10 is None else C.fwd_change(ten, j10, LOOK)
        sp = (None if js is None or js + LOOK >= len(spx)
              else spx[js + LOOK][1] / spx[js][1] - 1)
        completed = end is not None and d10 is not None
        rows.append({
            "start": day, "direction": "toward hikes" if sgn > 0 else "toward cuts",
            "gap_bp": round(gap[i][1], 1),
            "gap_change_63s_bp": round(gap[i][1] - gap[i - LOOK][1], 1),
            "target_move_toward_bp": None if moved is None else round(moved, 1),
            "outcome": (None if moved is None else
                        "conceded" if moved >= CONCEDE_BP else "refused"),
            "d10_63s_bp": None if d10 is None else round(100 * d10, 1),
            "d10_aligned_bp": None if d10 is None else round(100 * d10 * sgn, 1),
            "spx_63s": None if sp is None else round(sp, 4),
            "completed": completed and moved is not None})
    j = judge(rows)
    done, con, ref, mc, mr, verdict = (j["done"], j["con"], j["ref"], j["mc"],
                                      j["mr"], j["verdict"])
    found = {y: [r["start"] for r in rows if r["start"][:4] == y] for y in NAMED}
    body = [f"The gap (DGS1 less the target), latest {gap[-1][0] if gap else 'n/a'}: "
            f"{C.f2(gap[-1][1] if gap else None, 0, ' bp')}.",
            "",
            f"Episodes: {len(rows)}; completed {len(done)} (conceded {len(con)}, "
            f"refused {len(ref)}).",
            "",
            "| Start | Direction | Gap | 63s change | Target toward (bp) | Outcome | 10y 63s (bp) | Aligned | S&P 63s |",
            "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        body.append(f"| {r['start']} | {r['direction']} | {r['gap_bp']:+.0f} | "
                    f"{r['gap_change_63s_bp']:+.0f} | {C.f2(r['target_move_toward_bp'], 0)} | "
                    f"{r['outcome'] or 'open'} | {C.f2(r['d10_63s_bp'], 0)} | "
                    f"{C.f2(r['d10_aligned_bp'], 0)} | {C.pct(r['spx_63s'])} |")
    body += ["",
             "| Group | n | Median aligned 10y (bp) | Median S&P 63s |", "|---|---|---|---|",
             f"| conceded | {len(con)} | {C.f2(mc, 1)} | "
             f"{C.pct(C.median([r['spx_63s'] for r in con if r['spx_63s'] is not None]))} |",
             f"| refused | {len(ref)} | {C.f2(mr, 1)} | "
             f"{C.pct(C.median([r['spx_63s'] for r in ref if r['spx_63s'] is not None]))} |",
             "",
             "The order's named years: " + "; ".join(
                 f"{y} {'found (' + ', '.join(v) + ')' if v else 'not found'}"
                 for y, v in found.items()) + ".",
             "",
             f"Two-sided, the groups differ by "
             f"{C.f2(None if mr is None or mc is None else abs(mr - mc), 1, ' bp')}; "
             "the pre-registered rule is one-sided, in the direction the register's "
             "mechanism states (a refusal reprices the long end the market's way)."]
    return {
        "item": ITEM, "title": "Fed-market divergence episodes, conceded or refused",
        "as_of": f"{gap[-1][0] if gap else 'n/a'} (latest gap); last completed "
                 f"{done[-1]['start'] if done else 'n/a'}",
        "window": f"{gap[0][0] if gap else 'n/a'} to {gap[-1][0] if gap else 'n/a'}",
        "n": len(done),
        "statistic": "median forward 63-session 10-year change (aligned to the "
                     "divergence) and S&P return, conceded vs refused",
        "pass_rule": ("the register's: the conceded/refused split separates the "
                      "long-end outcome. Pre-registered by this first edition: DGS1 "
                      "less the target; >= 50 bp in 63 sessions; conceded = >= 25 bp "
                      "of target move toward the market in 63 sessions; separates = "
                      "refused median aligned 10y change >= conceded's + 25 bp; floor "
                      f"{FLOOR} completed, {FLOOR_GROUP} a group"),
        "verdict": verdict,
        "rights": ("The register grants SR-21 no Book rights either way: a derived "
                   "metric, the CRED_STRESS narrow flag, the Warsh-matrix scenario and "
                   "the PM disagreement record. A PASS lets the Rate machine quote "
                   "this split as the base rate for the 28 Oct live test; a FAIL keeps "
                   "it a table. " + C.RIGHTS_NOTE),
        "sources": ["FRED graph CSV (no key): DGS1, DGS10, DFEDTAR, DFEDTARL, DFEDTARU",
                    "Yahoo ^GSPC daily closes through altdata.import_yfinance"],
        "source_mode": mode, "body": body, "episodes": rows,
        "caveats": ["The box re-run reads the same public sources (the calibration "
                    "rule), not the store.",
                    "DGS1 is not the live feature's futures-implied rate and the "
                    "target is not the SEP dot: the live gap and this one measure the "
                    "same disagreement through different instruments.",
                    "The S&P 500 is its price, not its total return, over 63 sessions."]}


if __name__ == "__main__":
    raise SystemExit(C.cli(ITEM, load_public, study))
