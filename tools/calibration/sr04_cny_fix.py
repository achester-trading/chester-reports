"""
SR-4 -- the yuan fix and the offshore gap, calibrated on two windows, with the
Japan-US spread-persistence base rate (signal-triage ST-8; st-t3-calib, 18 Oct
2026).

    python tools/calibration/sr04_cny_fix.py [--box] [--out DIR] [--date D]

THE REGISTER'S GATE (docs/signal-triage-register.md, SR-4). "Calibrate
fix-deviation and CNH-CNY thresholds on Aug 2015-Jan 2017 and Sep 2022-Sep 2023.
Base rate for spread persistence from Japan-US 1998-2022." It states no pass rule.

WHAT THE FIRST EDITION PRE-REGISTERS (the register is silent). The thresholds are
ST-5's (config/funding_currency.yaml), read through altdata.funding_currency's own
tell_legs(), never chosen here. The two windows are the order's two kinds of
episode: Aug 2015 the deliberate devaluation (the fix moved to the close), Sep
2022-Sep 2023 the defended depreciation (the fix leaned hard against weakness).
PASS when, on spot data:
  (a) both tracked legs hold together on a session from 11 to 18 Aug 2015;
  (b) they never hold together in Sep 2022-Sep 2023;
  (c) outside Aug 2015-Jan 2017, at most 2 episodes (sessions within 20 of each
      other are one) from Aug 2015 to the data's end.
INSUFFICIENT when the spot series do not cover both windows. The third leg is not
tracked (rule 30), so no verdict here is the tell's: it is the two legs'.

WHAT OUR SOURCES ALLOW. The CFETS fix (chinamoney, through altdata.sources.cfets,
paged at the site's own size) and onshore CNY=X (Yahoo, from 2001) reach both
windows. SPOT CNH does not: Yahoo serves CNH=X only as hourly bars from 25 Dec
2023 (altdata/sources/cnh.py), and FRED carries none. So the gap leg's verdict is
INSUFFICIENT on our n. CME's USD/CNH future (Yahoo CNH=F, the front contract) does
reach both windows, and the same rule is run on it LABELLED A PROXY: a future
carries forward points, which in Jan 2016 (CNH HIBOR 66%) were large, so the
proxy's gap is not spot's and admits no threshold.

THE BASE RATE. FRED's monthly GS10 less Japan's 10-year (IRLTLT01JPM156N),
1998-01 to 2022-12: the share of months the spread's sign held 12, 24 and 60
months later, and the longest run above +200 bp. Beside it, the US-China spread's
current sign and run (GS10 less IRLTLT01CNM156N).
"""

from __future__ import annotations

import datetime as dt
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import st8_common as C                                           # noqa: E402

ITEM = "SR-4"
W1 = ("2015-08-01", "2017-01-31")
W2 = ("2022-09-01", "2023-09-30")
DEVAL = ("2015-08-11", "2015-08-18")
MERGE = 20
MAX_EP = 2
FIX_FROM = "2015-01-01"
PERSIST = (12, 24, 60)
JP_FROM, JP_TO = "1998-01", "2022-12"
CN10 = "IRLTLT01CNM156N"


def load_public() -> dict:
    import time
    from altdata.ledgers import sources as S
    from altdata.sources import cfets, cnh
    fix = []
    start = dt.date.fromisoformat(FIX_FROM)
    today = dt.date.today()
    while start <= today:
        end = min(start + dt.timedelta(days=360), today)
        page = 1
        while True:
            p = cfets._get(cfets.FIX_URL, {"startDate": start.isoformat(),  # noqa: SLF001
                                           "endDate": end.isoformat(),
                                           "currency": "USD/CNY", "pageNum": page,
                                           "pageSize": cfets.PAGE_SIZE})
            fix += [(r["observed_at"], r["value"]) for r in cfets.fix_rows(p)]
            if page >= int(((p.get("data") or {}).get("pageTotal")) or 1):
                break
            page += 1
            time.sleep(cfets.PAGE_PAUSE_SECONDS)
        start = end + dt.timedelta(days=1)
    now = dt.datetime.now(dt.timezone.utc)
    spot = [(r["observed_at"], r["value"]) for r in
            cnh.closes_from_bars(cnh.fetch_frames("730d"), now)]
    return {"fix": sorted(set(fix)), "cny": C.yahoo_close("CNY=X"),
            "cnh_spot": spot, "cnh_fut": C.yahoo_close("CNH=F", "2014-01-01"),
            "gs10": C.monthly_last(S.fred("GS10")),
            "jp10": C.monthly_last(S.fred("IRLTLT01JPM156N")),
            "cn10": _optional(lambda: C.monthly_last(S.fred(CN10)))}


def _optional(f):
    """A comparison line's input that may be gone (FRED retires series): None, and
    the ledger says so, rather than no ledger."""
    try:
        return f()
    except Exception as exc:                                    # noqa: BLE001
        return {"_absent": f"{type(exc).__name__}: {str(exc)[:60]}"}


# ---------------------------------------------------------------------------
def legs(fix: C.Daily, cny: C.Daily, cnh: C.Daily) -> list[dict]:
    """The two tracked legs on each readable session, by ST-5's own function."""
    from altdata import funding_currency as F
    from altdata.sources import cfets
    dev, k = [], -1
    for d, f in fix:
        while k + 1 < len(cny) and cny[k + 1][0] < d:
            k += 1
        if k >= 0 and f and cny[k][1]:
            dev.append((d, cfets.gap_bp(f, cny[k][1]), d))
    cmap = dict(cny)
    gap = [(d, cfets.gap_bp(v, cmap[d]), d) for d, v in cnh if d in cmap and cmap[d]]
    return F.tell_legs(dev, gap, F.config()["yuan"])


def both(lg: list[dict], a: str, b: str) -> list[str]:
    return [x["day"] for x in lg if a <= x["day"] <= b and x["leg1"] and x["leg2"]]


def episodes(days: list[str], all_days: list[str]) -> list[str]:
    idx = {d: i for i, d in enumerate(all_days)}
    out, last = [], None
    for d in days:
        if last is None or idx[d] - idx[last] > MERGE:
            out.append(d)
        last = d
    return out


def judge(lg: list[dict]) -> dict:
    days = [x["day"] for x in lg]
    covers = bool(days) and days[0] <= W1[0] and days[-1] >= W2[1] and \
        any(W2[0] <= d <= W2[1] for d in days)
    on = [x["day"] for x in lg if x["leg1"] and x["leg2"]]
    a = bool(both(lg, *DEVAL))
    b = not both(lg, *W2)
    out_eps = [d for d in episodes(on, days) if not (W1[0] <= d <= W1[1])]
    c = len(out_eps) <= MAX_EP
    word = C.INSUFFICIENT if not covers else (C.PASS if a and b and c else C.FAIL)
    return {"covers": covers, "a": a, "b": b, "c": c, "outside": out_eps, "word": word,
            "first": days[0] if days else None, "last": days[-1] if days else None}


def window_stats(lg: list[dict], a: str, b: str) -> dict:
    xs = [x for x in lg if a <= x["day"] <= b]
    if not xs:
        return {"n": 0}
    lean = [x["lean_bp"] for x in xs]
    gaps = [x["gap_bp"] for x in xs]
    return {"n": len(xs), "lean_min": min(lean), "lean_med": statistics.median(lean),
            "lean_max": max(lean), "leg1": C.share([x["leg1"] for x in xs]),
            "gap_med": statistics.median(gaps), "gap_max": max(gaps),
            "leg2": C.share([x["leg2"] for x in xs]),
            "both": C.share([x["leg1"] and x["leg2"] for x in xs])}


def persistence(us: C.Monthly, other: C.Monthly, a: str, b: str) -> dict:
    ms = [m for m in sorted(set(us) & set(other)) if a <= m <= b]
    sp = {m: 100.0 * (us[m] - other[m]) for m in ms}
    held = {}
    for h in PERSIST:
        pairs = [(sp[m], sp[C.madd(m, h)]) for m in ms if C.madd(m, h) in sp]
        held[h] = C.share([(x > 0) == (y > 0) for x, y in pairs])
    run = best = 0
    for m in ms:
        run = run + 1 if sp[m] > 200 else 0
        best = max(best, run)
    return {"n": len(ms), "pos": C.share([v > 0 for v in sp.values()]), "held": held,
            "longest_200": best, "mean": C.mean(list(sp.values()))}


def current_run(us: C.Monthly, other: C.Monthly) -> dict:
    ms = sorted(set(us) & set(other))
    sp = [(m, 100.0 * (us[m] - other[m])) for m in ms]
    m0, v0 = sp[-1]
    n = 0
    for m, v in reversed(sp):
        if (v > 0) != (v0 > 0):
            break
        n += 1
    return {"month": m0, "spread": v0, "run": n}


def study(d: dict, mode: str) -> dict:
    from altdata import funding_currency as F
    y = F.config()["yuan"]
    lg_spot = legs(d["fix"], d["cny"], d["cnh_spot"])
    lg_fut = legs(d["fix"], d["cny"], d["cnh_fut"])
    js, jf = judge(lg_spot), judge(lg_fut)
    if js["word"] == C.INSUFFICIENT:
        verdict = (f"{C.INSUFFICIENT} -- spot CNH reaches neither window (Yahoo's hourly "
                   f"bars from {d['cnh_spot'][0][0] if d['cnh_spot'] else 'n/a'}), so the "
                   f"gap leg cannot be calibrated on our n; the thresholds stay "
                   f"session-set. The CNH=F proxy (labelled, not the gate) reads "
                   f"{jf['word']}")
    else:
        verdict = (f"{js['word']} -- Aug 2015 {'held' if js['a'] else 'not held'}; "
                   f"2022-23 {'clear' if js['b'] else 'held'}; {len(js['outside'])} "
                   f"episodes outside the windows (rule: <= {MAX_EP})")
    jp = persistence(d["gs10"], d["jp10"], JP_FROM, JP_TO)
    cn = None if "_absent" in d["cn10"] else current_run(d["gs10"], d["cn10"])
    body = [f"**ST-5's thresholds, read** (config/funding_currency.yaml): leg 1 holds when "
            f"the fix's 5-observation mean against the previous close is at or above "
            f"{y['lean_gone_bp']:+g} bp; leg 2 when the CNH-CNY gap's 5-observation mean "
            f"is at or above {y['gap_weak_bp']:+g} bp and {y['gap_widen_bp']:+g} bp wider "
            f"than {y['gap_widen_obs']} observations before.", "",
            "**The windows** (spot where it reaches; the CNH=F proxy labelled):", "",
            "| Window | Gap series | Sessions | Fix lean, min / median / max (bp) | "
            "Leg 1 held | Gap median / max (bp) | Leg 2 held | Both |",
            "|---|---|---|---|---|---|---|---|"]
    for wn, (a, b) in (("Aug 2015-Jan 2017", W1), ("Sep 2022-Sep 2023", W2)):
        for gn, lg in (("spot CNH", lg_spot), ("CNH=F (proxy)", lg_fut)):
            s = window_stats(lg, a, b)
            if not s["n"]:
                body.append(f"| {wn} | {gn} | 0 | not reached | | | | |")
                continue
            body.append(f"| {wn} | {gn} | {s['n']} | {s['lean_min']:+.0f} / "
                        f"{s['lean_med']:+.0f} / {s['lean_max']:+.0f} | {C.sh(s['leg1'])} | "
                        f"{s['gap_med']:+.0f} / {s['gap_max']:+.0f} | {C.sh(s['leg2'])} | "
                        f"{C.sh(s['both'])} |")
    body += ["",
             f"**The proxy under the pre-registered rule:** Aug 2015 "
             f"{'held' if jf['a'] else 'not held'}; Sep 2022-Sep 2023 "
             f"{'clear' if jf['b'] else 'held'}; {len(jf['outside'])} episodes outside the "
             f"windows ({', '.join(jf['outside']) or 'none'}): **{jf['word']}** (a proxy; "
             "it admits nothing).",
             f"**Spot, where it reaches** ({js['first'] or 'n/a'} to {js['last'] or 'n/a'}): "
             f"{len(js['outside'])} episodes ({', '.join(js['outside']) or 'none'}).",
             "",
             f"**The base rate: Japan-US spread persistence, {JP_FROM} to {JP_TO}** (GS10 "
             f"less Japan's 10-year, monthly, n {jp['n']}): US above Japan in "
             f"{C.sh(jp['pos'])} of months (mean {jp['mean']:+.0f} bp); the sign held "
             + ", ".join(f"{C.sh(jp['held'][h])} of the time {h} months later" for h in PERSIST)
             + f"; the longest run above +200 bp was {jp['longest_200']} months.",
             (f"**US-China now** (GS10 less {CN10}): {cn['spread']:+.0f} bp in "
              f"{cn['month']}, the same sign for {cn['run']} months." if cn else
              f"**US-China now:** NOT AVAILABLE on the laptop (FRED {CN10}: "
              f"{d['cn10']['_absent']}); the live line reads calc.uscn_10y_spread from "
              "the CFETS curve.")
             + " The register's ruling stands: a wide spread inside a long one-signed "
             "regime is not a fade signal, and the Japan-US base rate is why."]
    rows = [dict(series="spot", **x) for x in lg_spot] + \
        [dict(series="CNH=F proxy", **x) for x in lg_fut
         if W1[0] <= x["day"] <= W1[1] or W2[0] <= x["day"] <= W2[1]]
    for r in rows:
        for k in ("lean_bp", "gap_bp", "widen_bp"):
            r[k] = round(r[k], 2)
        r.pop("available", None)
    return {
        "item": ITEM, "title": "the fix and the offshore gap on 2015-17 and 2022-23",
        "as_of": f"fix {d['fix'][-1][0]}; CNY=X {d['cny'][-1][0]}; spot CNH "
                 f"{d['cnh_spot'][-1][0] if d['cnh_spot'] else 'n/a'}; GS10 {max(d['gs10'])}",
        "window": f"fix {d['fix'][0][0]} to {d['fix'][-1][0]}; spot CNH "
                  f"{d['cnh_spot'][0][0] if d['cnh_spot'] else 'n/a'} on; base rate "
                  f"{JP_FROM} to {JP_TO}",
        "n": len(lg_spot),
        "statistic": "the devaluation tell's two tracked legs at ST-5's thresholds in the "
                     "two windows; episodes outside them; the Japan-US spread's sign "
                     "persistence",
        "pass_rule": ("the register states none. Pre-registered by this first edition: "
                      "on spot, both legs on 11-18 Aug 2015, never in Sep 2022-Sep 2023, "
                      f"<= {MAX_EP} episodes outside Aug 2015-Jan 2017; INSUFFICIENT where "
                      "spot does not cover both windows"),
        "verdict": verdict,
        "rights": ("PASS: ST-5's yuan thresholds enter config with this ledger named "
                   "beside them. FAIL or INSUFFICIENT: they stay session-set in "
                   "config/funding_currency.yaml; the tell prints as 2 of 3 legs tracked "
                   "and never a verdict (ruling 6 of 18 Oct). " + C.RIGHTS_NOTE),
        "sources": ["CFETS central parity, chinamoney.com.cn (no key), through "
                    "altdata/sources/cfets.py, paged at the site's size",
                    "Yahoo (altdata.import_yfinance): CNY=X daily; CNH=X hourly bars "
                    "through altdata/sources/cnh.py; CNH=F (CME USD/CNH front future), "
                    "a proxy",
                    f"FRED graph CSV (no key): GS10, IRLTLT01JPM156N, {CN10} (where served)"],
        "source_mode": mode, "body": body, "episodes": rows,
        "caveats": ["The CNH=F proxy carries forward points; its gap is not spot's, so "
                    "its reading informs and admits no threshold.",
                    "The third leg (state banks selling dollars) is not tracked (rule 30); "
                    "every reading here is the two tracked legs'.",
                    C.CONFIG_NOTE]}


if __name__ == "__main__":
    raise SystemExit(C.cli(ITEM, load_public, study))
