"""
SR-12 -- the bond-allocation rule under the inflation-by-correlation split
(signal-triage ST-7; st-t2-rates, 18 Oct 2026).

    python tools/calibration/sr12_bond_alloc.py [--box] [--out DIR] [--date D]

THE REGISTER'S GATE (docs/signal-triage-register.md, SR-12). Episodes:
bottom-decile readings of investors' bond allocation. Statistic: forward 12m and
36m 10-year Treasury total return, nominal and real, against cash, split by
trailing CPI >= 4% / < 4% and by the sign of the 1-year stock-bond correlation.
Pass for the modifier: "in the growth/term-premium cell, median real return
beats unconditional with >= 2/3 hit rate. If the split does not separate, table
only." Falsifier: bonds lose to cash over 12m from a bottom-decile print in an
inflation regime (quoted).

WHAT THE FIRST EDITION PRE-REGISTERS, where the register is silent or names
what no longer exists:
  * THE CELL. The "growth/term-premium cell" was a cell of the rates driver,
    which was withdrawn on 30 Sep and stays withdrawn (ruling 1, 18 Oct). The
    split the paste names is inflation by correlation, so the cell is read as
    CPI < 4% AND a negative 1-year stock-bond correlation: the quadrant where
    bonds hedge equities, which is the growth case. The other three are tabled.
  * THE ALLOCATION. AAII's survey is not tracked (the by-hand audit, 16 Oct), and
    ICI is a gap, so the reading is the Fed's Z.1, as ST-R5.30a built the live
    panel: households' directly held debt securities (HNODSAQ027S) over their
    total financial assets (TFAABSHNO), quarterly from 1945. Bond funds are not
    in it (Z.1 does not split fund shares by type).
  * BOTTOM DECILE, point in time: at or below the 10th percentile of the
    readings from the first quarter through that quarter, once 40 quarters are
    held. A quarter's reading is entered at the end of the fifth month after
    the quarter starts (Z.1 publishes about ten weeks after the quarter ends).
  * EPISODES: contiguous bottom-decile quarters, two quiet quarters or fewer
    merged; an episode enters at its first reading. Its regime is read at entry:
    CPI on the year from CPIAUCNS (not seasonally adjusted, never revised) for
    the month before entry, and the 12-month correlation of monthly S&P total
    returns (Shiller) with the par bond's ending at entry.
  * UNCONDITIONAL: the median forward real return over every entry month in the
    sample (monthly, 1955 on), at each horizon.
  * THE RULE: in the cell, BOTH horizons' median real 10-year return above the
    unconditional median, and at least two thirds of the cell's episodes above
    it at both. FLOOR: five completed episodes in the cell (36 months of forward
    data), below which no rate prints (INSUFFICIENT).
  * "SEPARATES": the cell's 36-month median real return exceeds the median of
    the other cells' episodes. A PASS needs separation; a FAIL reads "table only".

The 10-year return is a par bond priced off GS10 each month, plus a month's
coupon; cash earns the 3-month bill (TB3MS). Point in time: GS10, TB3MS and
CPIAUCNS are not revised; Z.1 IS revised, and the laptop edition reads its
current vintage (FRED's graph CSV), so a bottom decile here is a decile of
today's estimates. ALFRED's first prints are the box run's improvement, if the
operator wants it; a signal that survives only on revised data gets no rights.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import st7_common as C                                           # noqa: E402
from altdata.ledgers import ordinal                              # noqa: E402

ITEM = "SR-12"
MIN_QUARTERS = 40
DECILE = 10.0
MERGE_GAP = 2
ENTRY_LAG = 5                    # months after the quarter's first month
FLOOR = 5
CPI_HIGH = 4.0
HORIZONS = (12, 36)
HIT = 2.0 / 3.0


def load_public() -> dict:
    from altdata.ledgers import sources as S
    sh = S.shiller()
    return {"bonds": C.monthly_last(S.fred("HNODSAQ027S")),
            "assets": C.monthly_last(S.fred("TFAABSHNO")),
            "gs10": C.monthly_last(S.fred("GS10")),
            "tb3": C.monthly_last(S.fred("TB3MS")),
            "cpi": C.monthly_last(S.fred("CPIAUCNS")),
            "sp_price": C.monthly_last(sh["shiller.sp_price"]),
            "sp_div": C.monthly_last(sh["shiller.sp_dividend"])}


def allocation(d: dict) -> dict[str, float]:
    """{quarter's first month: percent of financial assets in debt securities}."""
    return {q: 100.0 * d["bonds"][q] / d["assets"][q]
            for q in sorted(d["bonds"]) if d["assets"].get(q)}


def bottom_decile(alloc: dict[str, float]) -> list[tuple[str, float, float, bool]]:
    """[(quarter, reading, percentile, in the bottom decile)], point in time."""
    out, hist = [], []
    for q in sorted(alloc):
        hist.append(alloc[q])
        if len(hist) < MIN_QUARTERS:
            continue
        p = 100.0 * sum(1 for h in hist if h <= alloc[q]) / len(hist)
        out.append((q, alloc[q], p, p <= DECILE))
    return out


def episodes(rows: list[tuple[str, float, float, bool]]) -> list[dict]:
    out: list[dict] = []
    quiet = None
    for q, v, p, low in rows:
        if low:
            if out and quiet is not None and quiet <= MERGE_GAP:
                out[-1]["last_quarter"] = q
                out[-1]["low"] = min(out[-1]["low"], v)
            else:
                out.append({"first_quarter": q, "last_quarter": q, "reading": v,
                            "percentile": p, "low": v})
            quiet = 0
        elif quiet is not None:
            quiet += 1
    return out


def judge(table: list[dict], unc: dict) -> dict:
    """The pre-registered rule over the episode table and the unconditional
    medians; the verdict carries its inputs."""
    cell = [t for t in table if t["in_cell"] and t["completed"]]
    rest = [t for t in table if not t["in_cell"] and t["completed"]
            and t["cell"] != "not determinable"]
    med = {h: C.median([t[f"real_{h}m"] for t in cell]) for h in HORIZONS}
    hit = {h: C.share([t[f"real_{h}m"] > unc[h] for t in cell]) for h in HORIZONS}
    rest36 = C.median([t["real_36m"] for t in rest])
    separates = med[36] is not None and rest36 is not None and med[36] > rest36
    n = len(cell)
    if n < FLOOR:
        return {"n": n, "med": med, "hit": hit, "rest36": rest36,
                "separates": separates, "rate_line": "no rate prints below the floor",
                "verdict": (f"{C.INSUFFICIENT} -- {n} completed episode(s) in the "
                            f"cell, below the floor of {FLOOR}; no rate prints")}
    ok = all(med[h] is not None and med[h] > unc[h] and hit[h] >= HIT
             for h in HORIZONS) and separates
    rate_line = "; ".join(
        f"{h}m: cell median {C.pct(med[h])} vs unconditional {C.pct(unc[h])}, "
        f"hit {C.sh(hit[h], 0)}" for h in HORIZONS)
    return {"n": n, "med": med, "hit": hit, "rest36": rest36, "separates": separates,
            "rate_line": rate_line,
            "verdict": (f"{C.PASS} -- modifier" if ok else f"{C.FAIL} -- table only")
            + f" ({rate_line}; {'separates' if separates else 'does not separate'})"}


def study(d: dict, mode: str) -> dict:
    alloc = allocation(d)
    rows = bottom_decile(alloc)
    eps = episodes(rows)
    bond, cash = C.bond_tr(d["gs10"]), C.cash_tr(d["tb3"])
    stock = C.equity_tr(d["sp_price"], d["sp_div"])
    infl = C.yoy_pct(d["cpi"])

    def fwd(entry: str, n: int) -> dict:
        b, c = C.compound(bond, entry, n), C.compound(cash, entry, n)
        return {"bond": b, "cash": c, "real": C.real(b, d["cpi"], entry, n),
                "excess": None if b is None or c is None else b - c}

    def corr12(entry: str):
        ms = [C.madd(entry, -k) for k in range(11, -1, -1)]
        if not all(m in stock and m in bond for m in ms):
            return None
        from altdata.ledgers import corr
        return corr([stock[m] for m in ms], [bond[m] for m in ms])

    # Unconditional: every month with both horizons' forward data.
    first_m = min(bond) if bond else None
    unc = {}
    for n in HORIZONS:
        vals = [C.real(C.compound(bond, m, n), d["cpi"], m, n)
                for m in sorted(bond) if m >= C.madd(first_m, 12)]
        unc[n] = C.median([v for v in vals if v is not None])

    table = []
    for e in eps:
        entry = C.madd(e["first_quarter"], ENTRY_LAG)
        cpi_y = infl.get(C.madd(entry, -1))
        rho = corr12(entry)
        f = {n: fwd(entry, n) for n in HORIZONS}
        cell = (None if cpi_y is None or rho is None else
                f"CPI {'>=' if cpi_y >= CPI_HIGH else '<'} 4%, correlation "
                f"{'negative' if rho < 0 else 'positive'}")
        table.append({
            "first_quarter": e["first_quarter"], "last_quarter": e["last_quarter"],
            "entry_month": entry, "reading_pct": round(e["reading"], 3),
            "percentile": round(e["percentile"], 1), "cpi_yoy": _r(cpi_y, 2),
            "sb_corr_12m": _r(rho, 3), "cell": cell or "not determinable",
            "in_cell": bool(cell) and cpi_y < CPI_HIGH and rho < 0,
            **{f"bond_{n}m": _r(f[n]["bond"], 4) for n in HORIZONS},
            **{f"real_{n}m": _r(f[n]["real"], 4) for n in HORIZONS},
            **{f"excess_{n}m": _r(f[n]["excess"], 4) for n in HORIZONS},
            "completed": all(f[n]["real"] is not None for n in HORIZONS)})

    j = judge(table, unc)
    verdict, rate_line, n = j["verdict"], j["rate_line"], j["n"]
    med, rest36, separates = j["med"], j["rest36"], j["separates"]
    infl_eps = [t for t in table if t["cell"].startswith("CPI >=") and
                t["excess_12m"] is not None]
    falsified = [t["entry_month"] for t in infl_eps if t["excess_12m"] < 0]

    last_q = max(alloc) if alloc else None
    cur = next((r for r in reversed(rows)), None)
    body = [
        f"Z.1 bond allocation, latest quarter {last_q}: {cur[1]:.2f}% of households' "
        f"financial assets, at the {ordinal(cur[2])} percentile of the {len(alloc)} "
        f"quarters held." if cur else "No reading.",
        "",
        f"Bottom-decile episodes (point in time, {MIN_QUARTERS}-quarter minimum "
        f"history): {len(table)}; completed (36 months forward): "
        f"{sum(t['completed'] for t in table)}; in the cell: {n}.",
        "",
        "| Entry | Quarters | Reading | Pctile | CPI y/y | Corr 12m | Cell | Real 12m | Real 36m | Excess 12m | Excess 36m |",
        "|---|---|---|---|---|---|---|---|---|---|---|"]
    for t in table:
        body.append(
            f"| {t['entry_month']} | {t['first_quarter']} to {t['last_quarter']} | "
            f"{t['reading_pct']:.2f}% | {t['percentile']:.0f} | {C.f2(t['cpi_yoy'], 1)} | "
            f"{C.f2(t['sb_corr_12m'])} | {t['cell']} | {C.pct(t['real_12m'])} | "
            f"{C.pct(t['real_36m'])} | {C.pct(t['excess_12m'])} | {C.pct(t['excess_36m'])} |")
    body += ["",
             f"Unconditional median real 10-year return: 12m {C.pct(unc[12])}, "
             f"36m {C.pct(unc[36])} (every month from "
             f"{C.madd(first_m, 12) if first_m else 'n/a'}).",
             f"The rule, evaluated: {rate_line}. Separation: cell 36m median "
             f"{C.pct(med[36])} vs the other cells' {C.pct(rest36)} -> "
             f"{'separates' if separates else 'does not separate'}.",
             f"Falsifier (bonds lose to cash over 12m from an inflation-regime "
             f"episode): {', '.join(falsified) if falsified else 'none'} of "
             f"{len(infl_eps)} inflation-regime episode(s)."]
    as_of = max((t["entry_month"] for t in table if t["completed"]), default=last_q)
    return {
        "item": ITEM, "title": "investor bond allocation, by inflation and stock-bond correlation",
        "as_of": f"{last_q} (latest Z.1 quarter); last completed entry {as_of}",
        "window": f"Z.1 from {min(alloc) if alloc else 'n/a'} to {last_q}; returns "
                  f"from {first_m} on",
        "n": n,
        "statistic": "forward 12m and 36m real 10-year total return from each "
                     "bottom-decile episode's entry, and its excess over bills, by cell",
        "pass_rule": ("the register's: in the growth cell, median real return beats "
                      "unconditional with >= 2/3 hit rate; else table only. "
                      "Pre-registered by this first edition: the cell is CPI < 4% and "
                      "negative 12-month stock-bond correlation (the rates driver "
                      "stays withdrawn); both horizons; the cell must separate; floor "
                      f"{FLOOR} completed episodes"),
        "verdict": verdict,
        "rights": ("PASS: a confidence modifier for Book A duration sizing and an "
                   "input to rule A-3. FAIL: the conditional base-rate table only. "
                   "INSUFFICIENT: neither. " + C.RIGHTS_NOTE),
        "sources": ["FRED graph CSV (no key), current vintage: HNODSAQ027S, "
                    "TFAABSHNO (Z.1, revised), GS10, TB3MS, CPIAUCNS (not revised)",
                    "Shiller's ie_data.xls through altdata/sources/shiller.py: the "
                    "S&P Composite price and dividend"],
        "source_mode": mode, "body": body, "episodes": table,
        "caveats": ["Z.1's current vintage, not its first prints; the bottom decile "
                    "is of today's estimates.",
                    "Episodes overlap in their 36-month windows when they come close "
                    "together; the hit rate counts episodes, not months."]}


def _r(v, nd):
    return None if v is None else round(v, nd)


if __name__ == "__main__":
    raise SystemExit(C.cli(ITEM, load_public, study))
