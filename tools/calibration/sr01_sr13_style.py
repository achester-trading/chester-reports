"""
SR-1 with SR-13 -- the growth/value style regime and the tech/defensives spread
(signal-triage ST-8; st-t3-calib, 18 Oct 2026). One session, one panel (SR-1's
integration note), two ledgers.

    python tools/calibration/sr01_sr13_style.py [--box] [--out DIR] [--date D]

SR-1, THE REGISTER'S RULE AND GATE (docs/signal-triage-register.md, SR-1). Rule:
"Log Growth/Value total-return ratio, z-score vs. its 10-year trend > +2,
followed by a break: ratio below its 40-week MA, or >8% off its 52-week high."
Gate: "Forward 3/6/12-month value-minus-growth after each trigger, HML from 1963
and ETFs from 2000; hit rate and asymmetry; check the late 1990s for early fires
and 2023 for the reversal. Pass: positive expectancy after costs at 6 and 12
months across >=6 non-overlapping episodes."

WHAT THE FIRST EDITION PRE-REGISTERS, where the register is silent:
  * THE HML LEG. The growth/value log ratio is minus the cumulated log of
    (1 + HML) from July 1963; HML is French's value-minus-growth return, so its
    cumulation is the long-sample ratio. Monthly: the 10-year trend is a
    least-squares line through the last 120 months and z is the last residual
    over the residuals' sd; 40 weeks is 9 months (a 9-month mean) and 52 weeks is
    12 months. The forward return is HML compounded over 3, 6 and 12 months
    after the trigger month.
  * THE ETF LEGS. IVW/IVE and IWF/IWD, weekly closes adjusted for distributions
    (Yahoo, auto-adjusted), from May 2000; the trend is fitted over up to 520
    weeks with at least 260 (so the first z is mid-2005); the 40-week mean and
    52-week high are as the rule says; the forward return is the value leg's
    total return less the growth leg's over 13, 26 and 52 weeks (a dollar-neutral
    pair).
  * THE TRIGGER. A z above +2 arms the rule for 12 months (52 weeks); the first
    break while armed is a trigger and disarms it; a new z above +2 after the
    trigger re-arms it. Episodes are triggers more than 365 days after the
    previous episode's start, so no two share a 12-month horizon.
  * COSTS. 0.50% round trip off every forward return (both legs in, both out).
  * THE VERDICT. The gate's rule on HML (the long sample; at least 6 completed
    episodes, else INSUFFICIENT); a PASS also needs neither ETF pair to FAIL the
    same rule where it has 6 episodes of its own.

SR-13, THE REGISTER'S GATE (SR-13): "Episodes: top-decile spread (1929, 1968-72,
1983, 1999-2000, 2020-21, 2024-26). Statistic: forward 12/36/60m relative return
of defensives vs. tech, (a) on spread alone, (b) on spread plus negative 12m tech
relative momentum. Pass for the tilt modifier: defensives' 36m relative return
positive in >=4 of 5 completed episodes in cell (b)."
  PRE-REGISTERED: from French's 49 industries, tech is Softw, Hardw, Chips and
  Telcm; defensives are staples (Food, Beer, Smoke, Hshld), healthcare (Hlth,
  MedEq, Drugs) and utilities (Util). A basket's price-to-book is its summed
  December market equity (firms x average size) over its summed book equity (the
  file's Sum BE / Sum ME times that ME), each against the 49-industry market;
  the spread is tech's premium less defensives', in points. Top decile is the
  full sample's (the register's episode list is in-sample, so this is labelled),
  consecutive years one episode. Cell (a) enters at the end of June of the
  episode's first year (the formation date); cell (b) at the first month from
  then to the episode's end where tech's trailing 12-month return less the
  market's is negative; years in the top decile with at most one quiet year
  between them are one episode. Baskets are equal-weighted across their industries'
  value-weighted returns. "4 of 5" is read as 80% of at least 5.

The rule's arithmetic (the trend z, the break, the trigger) is
the altdata style_regime module's, the one definition the Monthly's panel reads too.

Point in time: French restates the whole history with each CRSP update (the
vintage is printed), and the Yahoo closes are not revised.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import st8_common as C                                           # noqa: E402
from altdata import style_regime as SR                          # noqa: E402

START = "1963-07"
COST = 0.005
Z_ARM = 2.0
ARM_MONTHS, ARM_WEEKS = 12, 52
TREND_M, TREND_W, TREND_W_MIN = 120, 520, 260
MA_M, HIGH_M = 9, 12
MA_W, HIGH_W = 40, 52
OFF_HIGH = math.log(0.92)
H_M = (3, 6, 12)
H_W = (13, 26, 52)
FLOOR = 6
PAIRS = (("IVW", "IVE"), ("IWF", "IWD"))
TECH = ("Softw", "Hardw", "Chips", "Telcm")
STAPLES, HEALTH, UTIL = ("Food", "Beer", "Smoke", "Hshld"), ("Hlth", "MedEq", "Drugs"), ("Util",)
DEF = STAPLES + HEALTH + UTIL
H13 = (12, 36, 60)
FLOOR13 = 5
SHARE13 = 0.80
SOURCED_13 = ("the register's cited episode list (Topdown Charts / LSEG, 24 Sep 2026): "
              "1929, 1968-72, 1983, 1999-2000, 2020-21, 2024-26, and the 2000 peak "
              "near 210 pp against about 150 pp now")


# ---------------------------------------------------------------------------
def load_public() -> dict:
    fac, v1 = C.french_text("factors")
    ind, v2 = C.french_text("industries")
    fs = C.french_sections(fac)
    mon = next(r for r in fs.values() if len(r) > 1 and "HML" in r[0]
               and len(r[1][0]) == 6)
    f = C.french_monthly(mon)
    s = C.french_sections(ind)

    def sec(prefix):
        return next(v for k, v in s.items() if k.startswith(prefix))
    return {"hml": f["HML"], "mkt": {m: f["Mkt-RF"][m] + f["RF"][m] for m in f["RF"]},
            "ret": C.french_monthly(sec("Average Value Weighted Returns -- Monthly")),
            "nfirms": C.french_monthly(sec("Number of Firms in Portfolios")),
            "size": C.french_monthly(sec("Average Firm Size")),
            "beme": C.french_annual(sec("Sum of BE / Sum of ME")),
            "etf": {s_: C.yahoo_tr(s_) for p in PAIRS for s_ in p},
            "vintage": f"factors {v1}; 49 industries {v2}"}


# ---------------------------------------------------------------------------
# SR-1
# ---------------------------------------------------------------------------
def hml_ratio(hml: C.Monthly) -> list[tuple[str, float]]:
    out, g = [], 0.0
    for m in sorted(k for k in hml if k >= START):
        g -= math.log(1 + hml[m] / 100.0)
        out.append((m, g))
    return out


def hml_events(hml: C.Monthly) -> list[dict]:
    xs = hml_ratio(hml)
    r = {m: v / 100.0 for m, v in hml.items()}

    def z_of(i):
        return C.trend_z([v for _, v in xs[i - TREND_M + 1:i + 1]]) if i >= TREND_M - 1 else None
    rows = []
    for t in SR.triggers(xs, z_of, MA_M, HIGH_M, ARM_MONTHS, Z_ARM, OFF_HIGH):
        m = t["day"]
        fw = {h: C.compound(r, m, h) for h in H_M}
        rows.append({"set": "HML", "trigger": m, "z_setup": round(t["z_setup"], 3),
                     "break": t["break"],
                     **{f"vmg_{h}m": None if fw[h] is None else round(fw[h] - COST, 5)
                        for h in H_M}})
    return rows


def etf_events(growth: C.Daily, value: C.Daily, label: str) -> list[dict]:
    g, v = dict(C.weekly_last(growth)), dict(C.weekly_last(value))
    days = sorted(set(g) & set(v))
    xs = [(d, math.log(g[d] / v[d])) for d in days]

    def z_of(i):
        if i < TREND_W_MIN - 1:
            return None
        return C.trend_z([x for _, x in xs[max(0, i - TREND_W + 1):i + 1]])
    rows = []
    for t in SR.triggers(xs, z_of, MA_W, HIGH_W, ARM_WEEKS, Z_ARM, OFF_HIGH):
        i = t["i"]
        fw = {}
        for h in H_W:
            if i + h < len(days):
                d0, d1 = days[i], days[i + h]
                fw[h] = (v[d1] / v[d0] - 1) - (g[d1] / g[d0] - 1) - COST
            else:
                fw[h] = None
        rows.append({"set": label, "trigger": t["day"], "z_setup": round(t["z_setup"], 3),
                     "break": t["break"],
                     **{f"vmg_{h}w": None if fw[h] is None else round(fw[h], 5)
                        for h in H_W}})
    return rows


def episodes_of(rows: list[dict]) -> list[dict]:
    day = (lambda r: r["trigger"] + "-01" if len(r["trigger"]) == 7 else r["trigger"])
    keep = set(C.first_of_runs([day(r) for r in rows], 365))
    return [r for r in rows if day(r) in keep]


def judge_sr1(eps: list[dict], k6: str, k12: str) -> dict:
    done = [e for e in eps if e.get(k12) is not None]
    e6, e12 = C.mean([e[k6] for e in done]), C.mean([e[k12] for e in done])
    hit = C.share([e[k12] > 0 for e in done])
    asym = C.asymmetry([e[k12] for e in done])
    if len(done) < FLOOR:
        word = C.INSUFFICIENT
    else:
        word = C.PASS if e6 is not None and e6 > 0 and e12 > 0 else C.FAIL
    return {"n": len(done), "e6": e6, "e12": e12, "hit": hit, "asym": asym, "word": word}


def combine(j: dict) -> tuple[str, list[str]]:
    """The verdict word: HML's, unless HML passes and an ETF pair with its own
    floor of episodes FAILs the same rule."""
    etf_fail = [k for k in j if k != "HML" and j[k]["word"] == C.FAIL]
    w = j["HML"]["word"]
    return (C.FAIL if w == C.PASS and etf_fail else w), etf_fail


def sr1(d: dict, mode: str) -> dict:
    hml = hml_events(d["hml"])
    eps_h = episodes_of(hml)
    j = {"HML": judge_sr1(eps_h, "vmg_6m", "vmg_12m")}
    etf_rows = []
    for gs, vs in PAIRS:
        rows = etf_events(d["etf"][gs], d["etf"][vs], f"{vs}-{gs}")
        etf_rows += rows
        j[f"{vs}-{gs}"] = judge_sr1(episodes_of(rows), "vmg_26w", "vmg_52w")
    h = j["HML"]
    word, etf_fail = combine(j)
    if word == C.INSUFFICIENT:
        verdict = (f"{C.INSUFFICIENT} -- {h['n']} completed non-overlapping HML episodes, "
                   f"below the floor of {FLOOR}; no rate prints")
    elif word == C.PASS:
        verdict = (f"{C.PASS} -- HML: mean value-minus-growth after costs "
                   f"{C.pct(h['e6'])} at 6 months and {C.pct(h['e12'])} at 12 across "
                   f"{h['n']} non-overlapping episodes (rule: both > 0, >= {FLOOR})")
    else:
        verdict = (f"{C.FAIL} -- HML: mean value-minus-growth after costs "
                   f"{C.pct(h['e6'])} at 6 months and {C.pct(h['e12'])} at 12 across "
                   f"{h['n']} non-overlapping episodes (rule: both > 0, >= {FLOOR})"
                   + (f"; ETF pairs failing the same rule: {', '.join(etf_fail)}"
                      if etf_fail else ""))
    body = ["Every trigger is in the CSV; the episodes are the triggers more than 365 "
            "days after the previous episode's start.",
            "",
            "| Set | Triggers | Episodes completed | Mean 6m (26w) after costs | "
            "Mean 12m (52w) after costs | Hit, 12m | Asymmetry | Rule |",
            "|---|---|---|---|---|---|---|---|"]
    counts = {"HML": len(hml)}
    for gs, vs in PAIRS:
        counts[f"{vs}-{gs}"] = sum(1 for r in etf_rows if r["set"] == f"{vs}-{gs}")
    for k, e in j.items():
        body.append(f"| {k} | {counts[k]} | {e['n']} | {C.pct(e['e6'])} | "
                    f"{C.pct(e['e12'])} | {C.sh(e['hit'])} | {C.f2(e['asym'])} | "
                    f"{e['word']} |")
    body += ["", "**HML episodes:**", "",
             "| Trigger | z at the setup | Break | 3m | 6m | 12m (after costs) |",
             "|---|---|---|---|---|---|"]
    for e in eps_h:
        body.append(f"| {e['trigger']} | {e['z_setup']:+.2f} | {e['break']} | "
                    f"{C.pct(e['vmg_3m'])} | {C.pct(e['vmg_6m'])} | {C.pct(e['vmg_12m'])} |")
    body += ["", "**ETF episodes** (the tradeable pairs; under the floor of "
             f"{FLOOR} each, so they inform and do not block):", "",
             "| Pair | Trigger | z at the setup | Break | 13w | 26w | 52w (after costs) |",
             "|---|---|---|---|---|---|---|"]
    for e in [x for gs, vs in PAIRS
              for x in episodes_of([r for r in etf_rows if r["set"] == f"{vs}-{gs}"])]:
        body.append(f"| {e['set']} | {e['trigger']} | {e['z_setup']:+.2f} | {e['break']} | "
                    f"{C.pct(e['vmg_13w'])} | {C.pct(e['vmg_26w'])} | {C.pct(e['vmg_52w'])} |")
    early = [e for e in hml if "1995-01" <= e["trigger"] <= "2000-12"]
    late = [e for e in hml + etf_rows if "2021-01" <= e["trigger"][:7] <= "2024-12"]
    body += ["",
             f"**The late 1990s (early fires).** HML triggers 1995-2000: "
             + ("; ".join(f"{e['trigger']} (12m {C.pct(e['vmg_12m'])})" for e in early)
                or "none") + ". A trigger whose 12-month value-minus-growth is "
             "negative before the 2000 turn is an early fire.",
             f"**2023 (the reversal).** Triggers 2021-2024 in any set: "
             + ("; ".join(f"{e['set']} {e['trigger']} (12m "
                          f"{C.pct(e.get('vmg_12m', e.get('vmg_52w')))})" for e in late)
                or "none") + ". The register's hard stop on a new ratio high exists "
             "for this case; the study measures the trigger, not the stop."]
    rows = [dict(r, episode=r in eps_h) for r in hml] + etf_rows
    cols = list(dict.fromkeys(k for r in rows for k in r))
    rows = [{k: r.get(k) for k in cols} for r in rows]
    last = d["hml"] and max(d["hml"])
    return {
        "item": "SR-1", "title": "growth/value: the z-above-trend setup and the break",
        "as_of": f"HML {last}; ETFs {max(s[-1][0] for s in d['etf'].values())}",
        "window": f"HML {START} to {last}; ETFs 2000-05 to "
                  f"{max(s[-1][0] for s in d['etf'].values())[:7]}",
        "n": h["n"],
        "statistic": "mean forward 3/6/12-month value-minus-growth after costs after "
                     "each trigger, hit rate and asymmetry (mean win over mean loss)",
        "pass_rule": (f"the register's: positive expectancy after costs at 6 and 12 "
                      f"months across >= {FLOOR} non-overlapping episodes. Pre-registered "
                      f"by this first edition: on HML, with neither ETF pair failing the "
                      f"same rule; costs {100 * COST:.2f}% round trip; the trigger as the "
                      f"docstring states"),
        "verdict": verdict,
        "rights": ("PASS: the narrow flag 'Style regime -- growth extreme / rotation "
                   "triggered', the Monthly style panel and Book B's pair rule ship. "
                   "FAIL or INSUFFICIENT: nothing new renders; the panel stays in the "
                   "backlog. " + C.RIGHTS_NOTE),
        "sources": [f"Kenneth French data library (no key; free for research use): "
                    f"F-F_Research_Data_Factors_CSV.zip, HML monthly; vintage "
                    f"{d['vintage']}",
                    "Yahoo daily closes, auto-adjusted for distributions (through "
                    "altdata.import_yfinance): IVW, IVE, IWF, IWD from 2000-05-26"],
        "source_mode": mode, "body": body, "episodes": rows,
        "caveats": ["French restates the whole HML history with each CRSP update; "
                    "the vintage is printed, and a box edition may differ by it.",
                    "HML is a long-short paper portfolio rebalanced annually; the ETF "
                    "pairs are the tradeable expression, and their sample begins in "
                    "2000, so the late-1990s check is HML's alone.",
                    C.CONFIG_NOTE]}


# ---------------------------------------------------------------------------
# SR-13
# ---------------------------------------------------------------------------
def spread_by_year(d: dict) -> dict[int, dict]:
    """{year: {tech, def, staples, health, util (premiums vs the market), spread}}."""
    out = {}
    for y in sorted({y for s in d["beme"].values() for y in s}):
        dec = f"{y - 1}-12"
        me, be = {}, {}
        for ind, s in d["beme"].items():
            n, sz = d["nfirms"].get(ind, {}).get(dec), d["size"].get(ind, {}).get(dec)
            if y in s and n and sz and s[y] > 0:
                me[ind] = n * sz
                be[ind] = s[y] * me[ind]
        if not me:
            continue
        mkt = sum(me.values()) / sum(be.values())

        def prem(basket):
            k = [i for i in basket if i in me]
            return (sum(me[i] for i in k) / sum(be[i] for i in k)) / mkt - 1 if k else None
        row = {"tech": prem(TECH), "def": prem(DEF), "staples": prem(STAPLES),
               "health": prem(HEALTH), "util": prem(UTIL)}
        if row["tech"] is not None and row["def"] is not None:
            row["spread"] = 100.0 * (row["tech"] - row["def"])
            out[y] = row
    return out


def basket_ret(ret: dict, basket) -> C.Monthly:
    ms = sorted({m for i in basket for m in ret.get(i, {})})
    out = {}
    for m in ms:
        xs = [ret[i][m] / 100.0 for i in basket if m in ret.get(i, {})]
        if xs:
            out[m] = sum(xs) / len(xs)
    return out


def rel(def_r: C.Monthly, tech_r: C.Monthly, start: str, n: int):
    a, b = C.compound(def_r, start, n), C.compound(tech_r, start, n)
    return None if a is None or b is None else (1 + a) / (1 + b) - 1


def mom12(r: C.Monthly, m: str):
    g = 1.0
    for k in range(0, 12):
        x = r.get(C.madd(m, -k))
        if x is None:
            return None
        g *= 1 + x
    return g - 1


def judge_sr13(eps: list[dict]) -> dict:
    done = [e for e in eps if e["cell_b_entry"] and e["b_36m"] is not None]
    pos = sum(1 for e in done if e["b_36m"] > 0)
    if len(done) < FLOOR13:
        word = C.INSUFFICIENT
    else:
        word = C.PASS if pos / len(done) >= SHARE13 else C.FAIL
    return {"n": len(done), "pos": pos, "word": word}


def sr13(d: dict, mode: str) -> dict:
    from altdata import ledgers
    sp = spread_by_year(d)
    years = sorted(sp)
    cut = ledgers.quantile([sp[y]["spread"] for y in years], 0.90)
    top = [y for y in years if sp[y]["spread"] >= cut]
    groups: list[list[int]] = []
    for y in top:
        if groups and y - groups[-1][-1] <= 2:
            groups[-1].append(y)
        else:
            groups.append([y])
    tech_r, def_r = basket_ret(d["ret"], TECH), basket_ret(d["ret"], DEF)
    mkt = {m: v / 100.0 for m, v in d["mkt"].items()}
    eps = []
    for g in groups:
        a = f"{g[0]}-06"
        end = f"{g[-1] + 1}-05"
        b = None
        for m in C.months(a, end):
            tm, mm = mom12(tech_r, m), mom12(mkt, m)
            if tm is not None and mm is not None and tm - mm < 0:
                b = m
                break
        row = {"years": f"{g[0]}-{g[-1]}" if len(g) > 1 else str(g[0]),
               "peak_spread_pp": round(max(sp[y]["spread"] for y in g), 1),
               "cell_a_entry": a}
        for h in H13:
            x = rel(def_r, tech_r, a, h)
            row[f"a_{h}m"] = None if x is None else round(x, 5)
        row["cell_b_entry"] = b
        for h in H13:
            x = rel(def_r, tech_r, b, h) if b else None
            row[f"b_{h}m"] = None if x is None else round(x, 5)
        y3 = g[0] + 3
        row["spread_change_36m_pp"] = (round(sp[y3]["spread"] - sp[g[0]]["spread"], 1)
                                       if y3 in sp else None)
        eps.append(row)
    j = judge_sr13(eps)
    if j["word"] == C.INSUFFICIENT:
        verdict = (f"{C.INSUFFICIENT} -- {j['n']} completed episodes in cell (b) "
                   f"(spread plus negative tech momentum), below the floor of "
                   f"{FLOOR13}; no rate prints")
    else:
        verdict = (f"{j['word']} -- defensives' 36m relative return positive in "
                   f"{j['pos']} of {j['n']} completed cell (b) episodes (rule: >= 4 of 5, "
                   f"{100 * SHARE13:.0f}%)")
    now = sp[years[-1]]
    body = [f"Top decile of the tech/defensives price-to-book spread, {years[0]} to "
            f"{years[-1]}: at or above {cut:.1f} points (the full sample's 90th "
            f"percentile; in-sample, labelled). Latest formation year {years[-1]}: "
            f"tech {C.pct(now['tech'], 0)} against the market, defensives "
            f"{C.pct(now['def'], 0)} (staples {C.pct(now['staples'], 0)}, healthcare "
            f"{C.pct(now['health'], 0)}, utilities {C.pct(now['util'], 0)}); spread "
            f"{now['spread']:.0f} points, at the "
            f"{ledgers.ordinal(ledgers.percentile_rank([sp[y]['spread'] for y in years], now['spread']))} "
            f"percentile of {len(years)} years.",
            "",
            "| Episode | Peak spread (pp) | Cell (a) entry | (a) 12m | (a) 36m | (a) 60m | "
            "Cell (b) entry | (b) 12m | (b) 36m | (b) 60m | Spread change, 36m (pp) |",
            "|---|---|---|---|---|---|---|---|---|---|---|"]
    for e in eps:
        body.append(f"| {e['years']} | {e['peak_spread_pp']:.0f} | {e['cell_a_entry']} | "
                    f"{C.pct(e['a_12m'])} | {C.pct(e['a_36m'])} | {C.pct(e['a_60m'])} | "
                    f"{e['cell_b_entry'] or 'never'} | {C.pct(e['b_12m'])} | "
                    f"{C.pct(e['b_36m'])} | {C.pct(e['b_60m'])} | "
                    f"{C.f2(e['spread_change_36m_pp'], 0)} |")
    body += ["",
             "**The falsifier** (reversion through earnings with flat relative prices): "
             "an episode whose spread fell over 36 months while defensives' relative "
             "return was near zero is that case; the last column beside (a) 36m shows it.",
             "",
             f"**Sourced comparison, not episodes of ours:** {SOURCED_13}. The episodes above are "
             "ours, from French's book-to-market; the register's list is the chart's."]
    return {
        "item": "SR-13", "title": "tech against defensives: the spread's top decile",
        "as_of": f"formation year {years[-1]} (June); returns to {max(def_r)}",
        "window": f"{years[0]} to {years[-1]} (annual book-to-market); monthly returns "
                  f"{min(def_r)} to {max(def_r)}",
        "n": j["n"],
        "statistic": "forward 12/36/60-month relative return of defensives against tech "
                     "after each top-decile spread episode, (a) on the spread alone and "
                     "(b) with negative 12-month tech relative momentum",
        "pass_rule": ("the register's: defensives' 36m relative return positive in >= 4 "
                      "of 5 completed episodes in cell (b). Pre-registered by this first "
                      "edition: the baskets, the price-to-book and the entries as the "
                      f"docstring states; at least {FLOOR13} completed, 80% positive"),
        "verdict": verdict,
        "rights": ("PASS: the Book A tilt modifier, gated on SR-1's break, and the "
                   "base-rate table; it rides SR-1's panel. FAIL or INSUFFICIENT: base "
                   "rate only, no modifier. " + C.RIGHTS_NOTE),
        "sources": [f"Kenneth French data library (no key): 49_Industry_Portfolios_CSV.zip "
                    f"(value-weighted monthly returns, number of firms, average firm size, "
                    f"Sum of BE / Sum of ME); F-F_Research_Data_Factors_CSV.zip "
                    f"(Mkt-RF + RF); vintage {d['vintage']}"],
        "source_mode": mode, "body": body, "episodes": eps,
        "caveats": ["The baskets are French's SIC-based industries, not LSEG's sectors; "
                    "the chart's ~150 pp is a different construction, so the levels are "
                    "not comparable, only the episodes' timing.",
                    "The top decile is the full sample's, as the register's own list is; "
                    "an expanding-window decile would admit fewer early episodes.",
                    C.CONFIG_NOTE]}


def study(d: dict, mode: str) -> list[dict]:
    return [sr1(d, mode), sr13(d, mode)]


if __name__ == "__main__":
    raise SystemExit(C.cli("SR-1 and SR-13", load_public, study))
