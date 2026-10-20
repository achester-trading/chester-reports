"""
SR-5 -- the consumer credit impulse (signal-triage ST-8; st-t3-calib, 18 Oct
2026).

    python tools/calibration/sr05_consumer_credit.py [--box] [--alfred] [--out DIR] [--date D]

THE REGISTER'S GATE (docs/signal-triage-register.md, SR-5). "Replicate at 5- and
10-year z windows; count non-overlapping episodes; run the revolving-only
variant; rerun everything on first prints. Bull side passes if first-print
six-month expectancy stays >= 2x unconditional across >= 8 episodes." The
ruling's object: "bottom decile of the 6-month-average net-change rolling
z-score" (bull side; the source's 84% W/L, about +9% six-month expectancy) and
the top decile (bear side, a Monthly tilt only).

WHAT THE FIRST EDITION PRE-REGISTERS, where the register is silent:
  * THE IMPULSE. TOTALSL's monthly net change ($bn), its 6-month mean, and that
    mean's z against its own trailing 60 (5-year) or 120 (10-year) months.
  * THE DECILES, point in time: a month is bottom decile when its z is at or
    below the 10th percentile of every z to date (at least 120 of them), top
    decile at or above the 90th.
  * ENTRY. G.19 is published about five weeks after the month, so a signal for
    month m is acted on at the end of month m+2. The six-month return is the S&P
    500's total return (Shiller's price and dividend) over the six months after
    the entry month; unconditional is the same over every month with a z.
  * EPISODES. Signal months more than 183 days after the previous episode's start
    (no two share a six-month window). Expectancy is the mean over episodes.
  * THE VERDICT. Both windows must meet the rule (>= 8 episodes, expectancy >= 2x
    unconditional, unconditional positive). The revolving-only variant (REVOLSL)
    and the bear side are printed, not judged.

THE VINTAGES. The rule is on FIRST PRINTS and G.19 is heavily revised.
  * The laptop edition (default) reads FRED's latest vintages and SAYS SO: it
    cannot pass the register's rule, so its verdict is INSUFFICIENT with the
    latest-vintage reading printed beside it, labelled.
  * The box edition (--alfred) reads ALFRED's vintages with the key, through
    altdata.fred_history's paged reader: the first-print net change for month m is
    m's level in its first vintage less m-1's level in that same vintage (so a
    revision to m-1 is not read as m's change). That edition's word is the gate's.
    ALFRED's vintages of these series begin in the 1980s-90s, so its n is smaller,
    and the ledger prints it.
"""

from __future__ import annotations

import bisect
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import st8_common as C                                           # noqa: E402
import st7_common as C7                                          # noqa: E402

ITEM = "SR-5"
WINDOWS = (60, 120)
AVG = 6
LAG = 2
H = 6
MIN_Z = 120
GAP_DAYS = 183
FLOOR = 8
MULT = 2.0
SERIES = {"total": "TOTALSL", "revolving": "REVOLSL"}
SOURCED_5 = ("the ruling's source (register SR-5: a research chart on the G.19 July print, 8 Sep 2026): "
             "bull side 84% W/L, about +9% six-month expectancy, double the base rate; "
             "bear side 59% W/L, about -0.5% against about +4.5% unconditional; about "
             "70 overlapping observations, about 12 episodes")


# ---------------------------------------------------------------------------
def first_print_changes(rows: list[tuple[str, float, str]]) -> C.Monthly:
    """{YYYY-MM: m's first-print level less m-1's level in m's first vintage}
    from ALFRED rows (observation date, value, vintage), one per change."""
    hist: dict[str, list[tuple[str, float]]] = {}
    for d, v, vin in rows:
        hist.setdefault(d[:7], []).append((vin, v))
    for k in hist:
        hist[k].sort()
    out: C.Monthly = {}
    for m, h in hist.items():
        v_m, lvl = h[0]
        prev = hist.get(C.madd(m, -1))
        if not prev:
            continue
        j = bisect.bisect_right([vin for vin, _ in prev], v_m) - 1
        if j >= 0:
            out[m] = lvl - prev[j][1]
    return out


def latest_changes(level: C.Monthly) -> C.Monthly:
    return {m: v - level[C.madd(m, -1)] for m, v in level.items()
            if C.madd(m, -1) in level}


def impulse_z(chg: C.Monthly, window: int) -> C.Monthly:
    ms = sorted(chg)
    avg = {}
    for i in range(AVG - 1, len(ms)):
        win = ms[i - AVG + 1:i + 1]
        if win[0] == C.madd(ms[i], -(AVG - 1)):
            avg[ms[i]] = sum(chg[m] for m in win) / AVG
    am = sorted(avg)
    out: C.Monthly = {}
    for i in range(window - 1, len(am)):
        xs = [avg[m] for m in am[i - window + 1:i + 1]]
        mu = sum(xs) / window
        sd = (sum((x - mu) ** 2 for x in xs) / (window - 1)) ** 0.5
        if sd:
            out[am[i]] = (xs[-1] - mu) / sd
    return out


def deciles(z: C.Monthly) -> dict[str, str]:
    """{month: "bottom" | "top" | ""}, against every z to date (point in time)."""
    from altdata import ledgers
    out, hist = {}, []
    for m in sorted(z):
        hist.append(z[m])
        if len(hist) < MIN_Z:
            out[m] = ""
            continue
        lo, hi = ledgers.quantile(hist, 0.10), ledgers.quantile(hist, 0.90)
        out[m] = "bottom" if z[m] <= lo else "top" if z[m] >= hi else ""
    return out


def side(z: C.Monthly, eq: C.Monthly, which: str) -> dict:
    dec = deciles(z)
    fwd = {m: C.compound(eq, C.madd(m, LAG), H) for m in z}
    unc = C.mean([v for m, v in fwd.items() if v is not None and dec.get(m) is not None
                  and len([k for k in z if k <= m]) >= MIN_Z])
    sig = [m for m in sorted(z) if dec.get(m) == which]
    starts = C.first_of_runs([m + "-01" for m in sig], GAP_DAYS)
    eps = [{"signal": s[:7], "z": round(z[s[:7]], 3), "entry": C.madd(s[:7], LAG),
            "fwd_6m": None if fwd.get(s[:7]) is None else round(fwd[s[:7]], 5)}
           for s in starts]
    done = [e for e in eps if e["fwd_6m"] is not None]
    exp = C.mean([e["fwd_6m"] for e in done])
    wl = C.share([e["fwd_6m"] > 0 for e in done])
    return {"signals": len(sig), "eps": eps, "n": len(done), "exp": exp, "wl": wl,
            "unc": unc}


def judge(s: dict) -> str:
    if s["n"] < FLOOR or s["unc"] is None or s["exp"] is None:
        return C.INSUFFICIENT
    return C.PASS if s["unc"] > 0 and s["exp"] >= MULT * s["unc"] else C.FAIL


# ---------------------------------------------------------------------------
def load_public(a=None) -> dict:
    from altdata.ledgers import sources as S
    sh = S.shiller()
    d = {"sp_price": C.monthly_last(sh["shiller.sp_price"]),
         "sp_div": C.monthly_last(sh["shiller.sp_dividend"]), "first_prints": False}
    if a is not None and a.alfred:
        from altdata import fred_history, secrets
        key = secrets.get("FRED_API_KEY")
        if not key:
            raise SystemExit("--alfred needs the FRED key configured (the box edition)")
        get = fred_history._live_get(key.strip())                 # noqa: SLF001
        for k, sid in SERIES.items():
            rows = fred_history.vintage_history(sid, get, fred_history.vintage_dates(sid, get))
            d[k] = first_print_changes(rows)
        d["first_prints"] = True
    else:
        for k, sid in SERIES.items():
            d[k] = latest_changes(C.monthly_last(S.fred(sid)))
    return d


def study(d: dict, mode: str) -> dict:
    eq = C7.equity_tr(d["sp_price"], d["sp_div"])
    res = {}
    for k in SERIES:
        for w in WINDOWS:
            z = impulse_z(d[k], w)
            res[(k, w)] = {"bull": side(z, eq, "bottom"), "bear": side(z, eq, "top"),
                           "z_now": (max(z), z[max(z)]) if z else None}
    words = {w: judge(res[("total", w)]["bull"]) for w in WINDOWS}
    fp = d.get("first_prints")
    b10 = res[("total", 120)]["bull"]
    reading = (f"10-year window {words[120]} (expectancy {C.pct(b10['exp'])} against "
               f"unconditional {C.pct(b10['unc'])}, {b10['n']} episodes), 5-year window "
               f"{words[60]}")
    if not fp:
        verdict = (f"{C.INSUFFICIENT} -- the rule is on first prints, which this laptop "
                   f"edition does not read (latest vintages; the box edition reads "
                   f"ALFRED). On latest vintages: {reading}")
    elif all(w == C.PASS for w in words.values()):
        verdict = f"{C.PASS} -- first prints, both windows: {reading}"
    elif any(w == C.INSUFFICIENT for w in words.values()):
        verdict = f"{C.INSUFFICIENT} -- first prints: {reading}; below the floor of {FLOOR}"
    else:
        verdict = f"{C.FAIL} -- first prints: {reading} (rule: >= {MULT:.0f}x, >= {FLOOR})"
    body = [("**Vintage: FIRST PRINTS (ALFRED).**" if fp else
             "**Vintage: LATEST (FRED's current vintage), not first prints.** The figures "
             "below are the revised history; the register's rule reads first prints, "
             "and only the box edition (--alfred) can pass or fail it."),
            "",
            "| Series | z window | Side | Signal months | Episodes completed | "
            "Expectancy, 6m | W/L | Unconditional, 6m | Multiple | Rule |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for (k, w), r in res.items():
        for nm, s in (("bull (bottom decile)", r["bull"]), ("bear (top decile)", r["bear"])):
            mult = (s["exp"] / s["unc"]) if s["exp"] is not None and s["unc"] else None
            rule = judge(s) if nm.startswith("bull") and k == "total" else "printed"
            body.append(f"| {k} ({SERIES[k]}) | {w // 12}-year | {nm} | {s['signals']} | "
                        f"{s['n']} | {C.pct(s['exp'])} | {C.sh(s['wl'])} | "
                        f"{C.pct(s['unc'])} | {C.f2(mult)} | {rule} |")
    zt = res[("total", 120)]["z_now"]
    body += ["", f"Now: the 10-year z of the total impulse is {zt[1]:+.2f} ({zt[0]})."
             if zt else "", "",
             "**Bull-side episodes, total, 10-year window:**", "",
             "| Signal month | z | Entry | S&P 500 6m total return |", "|---|---|---|---|"]
    for e in b10["eps"]:
        body.append(f"| {e['signal']} | {e['z']:+.2f} | {e['entry']} | {C.pct(e['fwd_6m'])} |")
    body += ["", f"**Sourced comparison, not episodes of ours:** {SOURCED_5}."]
    rows = [dict(series=k, window_months=w, side=nm, **e)
            for (k, w), r in res.items() for nm in ("bull", "bear") for e in r[nm]["eps"]]
    last = max(d["total"])
    return {
        "item": ITEM, "title": "the consumer credit impulse's bull side",
        "as_of": f"G.19 {last} ({'first prints' if fp else 'latest vintage'}); S&P "
                 f"{max(eq)}",
        "window": f"{min(d['total'])} to {last} (total), {min(d['revolving'])} to "
                  f"{max(d['revolving'])} (revolving)",
        "n": b10["n"],
        "statistic": "mean six-month S&P 500 total return after non-overlapping "
                     "bottom-decile episodes of the 6-month-average net-change z, "
                     "against the unconditional mean",
        "pass_rule": (f"the register's: first-print six-month expectancy >= 2x "
                      f"unconditional across >= 8 episodes. Pre-registered by this first "
                      f"edition: both z windows (5 and 10 years) must meet it; entry two "
                      f"months after the signal month; deciles point in time"),
        "verdict": verdict,
        "rights": ("PASS: the bull side becomes a T&B bottom-confirmation trigger "
                   "candidate, behind SR-8's gate, and the consumer/credit tilt line and "
                   "RS tell render. FAIL or INSUFFICIENT: nothing new renders. "
                   + C.RIGHTS_NOTE),
        "sources": ["FRED " + ("ALFRED vintages through altdata.fred_history (keyed; the "
                               "box edition)" if fp else "graph CSV (no key), latest "
                                                         "vintage") + ": TOTALSL, REVOLSL",
                    "Shiller's ie_data.xls through altdata/sources/shiller.py: S&P "
                    "Composite price and dividend (monthly total return)"],
        "source_mode": mode + ("; first prints" if fp else "; latest vintages"),
        "body": body, "episodes": rows,
        "caveats": ["G.19 is heavily revised and its levels have breaks (benchmark "
                    "revisions); the latest vintage smooths both, which is why the rule "
                    "is on first prints.",
                    "Rolling z-scores inflate after quiet stretches (the register's own "
                    "note on 2023-25).",
                    C.CONFIG_NOTE]}


def extra(ap) -> None:
    ap.add_argument("--alfred", action="store_true",
                    help="read ALFRED first prints with the key (the box edition)")


if __name__ == "__main__":
    raise SystemExit(C.cli(ITEM, load_public, study, extra=extra))
