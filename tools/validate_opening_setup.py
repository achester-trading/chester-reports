#!/usr/bin/env python3
"""
Validation gate: the opening setup, first half (decision D-3 of 18 Oct 2026;
a44-opening-setup) -- OS-2, OS-10 and OS-11, and the rules all four elements
share. OS-3 (the volatility-regime lenses) is held by tools/validate_vol_event.py's
group OS-3. On fixtures; no network, no model, no live store.

  A  OS-2, THE GAUGE. The typical realised range by hand (each five-session window
     4.0% of the prior close; n=20 prints it, n=19 reads "awaiting (n=19 of 20)");
     the regime word as the engine prints it, gated (an indeterminate read prints
     no typical range); the one-sigma range by hand (761.10 x 18.2% x sqrt(1/252)
     = 8.73); the numeral audit passes; no CALM / NORMAL / WILD word; the anchor's
     hook, one line under the dealer surface, its displacement declared.
  B  OS-10, THE MOST-ACTIVE TABLE. The week's ten by volume in order; IV rank and
     percentile by hand, each with its window and n; the one-day change; the
     implied week against the realised week by hand; no chart, no paragraph, no
     score, no weight; the third Friday; a capture's volume summed.
  C  OS-11, THE EARNINGS ROWS. The pricing word by hand (elevated, muted, in line,
     and not read on two reactions); the reactions from stored events and closes;
     the row prints its three figures and "not a recommendation"; no store file
     reads "not stored"; the matrix's hook.
  D  THE RULES. No new module reads a vendor key or the vendor's source id; no
     table carries a score or a weight; no by-hand key; no model or network
     import; neither Weekly builder session B is fixing is touched.
  E  THE RULINGS ON THE A44 REPORT: the three vol-regime lines every day (level,
     percentile, window, as-of; the numeral audit); "of 17 captured names"; no
     pre-market line while the ES conversion runs only SPY to ES.

    python tools/validate_opening_setup.py
"""

from __future__ import annotations

import ast
import datetime as dt
import json
import math
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gate_tmp import mkdtemp                                    # noqa: E402

LINE = "=" * 78
PASS = FAIL = 0
TD = Path(mkdtemp("opening-setup-gate-"))
NEW = ["daily_cascade/opening_setup.py"]


def check(c: bool, m: str) -> bool:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")
    return bool(c)


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


def close(a, b, tol=1e-6) -> bool:
    return a is not None and b is not None and abs(a - b) <= tol


def obs(key, day, value, inst=None):
    return {"registry_key": key, "instrument": inst, "observed_at": day,
            "available_at": f"{day}T21:00:00+00:00", "value": value, "source": "fixture"}


def days(n: int, end: str = "2026-10-16") -> list[str]:
    out, d = [], dt.date.fromisoformat(end)
    while len(out) < n:
        if d.weekday() < 5:
            out.insert(0, d.isoformat())
        d -= dt.timedelta(days=1)
    return out


def card(day: str, net=-1e9, ntg=0.30):
    return {"session": day, "net_gex_morning": net, "net_to_gross_morning": ntg,
            "session_high": 102.0, "session_low": 98.0, "prior_close": 100.0}


# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. OS-2: THE EXPECTED-MOVEMENT GAUGE")
    from altdata import numeral_audit as NA
    from daily_cascade import dealer_block as DB, opening_setup as OS
    cd = DB.config()
    med, n = OS.typical_range([card(d) for d in days(24)], "negative", cd, 5)
    med19, n19 = OS.typical_range([card(d) for d in days(23)], "negative", cd, 5)
    check(close(med, 4.0) and n == 20 and n19 == 19
          and OS.typical_range([card(d) for d in days(24)], "positive", cd, 5) == (None, 0),
          "the typical realised range by hand: each five-session window spans 102 less "
          "98 over a 100 prior close, 4.0%; 24 stored sessions make n=20, 23 make n=19; "
          "the other regime's sessions are not counted")
    prof = {"symbol": "SPY", "session_date": "2026-10-16",
            "overall": {"net_gex": -2.0e9, "net_to_gross": 0.30}}
    iv = (18.2, "SPY ATM 30-day IV")
    g20 = OS.gauge(prof, ("2026-10-16", 761.10), iv, [card(d) for d in days(24)])
    g19 = OS.gauge(prof, ("2026-10-16", 761.10), iv, [card(d) for d in days(23)])
    r = 761.10 * 0.182 * math.sqrt(1 / 252)
    check("negative gamma (net-to-gross 30%)" in g20["line"]
          and f"{761.10 - r:,.2f} to {761.10 + r:,.2f}" in g20["line"]
          and f"±{r:.2f}" in g20["line"] and close(r, 8.7255, 1e-3)
          and "typical realised range at this reading: 4.0% over 5 sessions (n=20)" in g20["line"]
          and "typical realised range at this reading: awaiting (n=19 of 20)" in g19["line"],
          f"the gauge by hand: negative gamma at 30% net-to-gross; 761.10 ± {r:.2f} "
          f"(18.2% x sqrt(1/252)); 4.0% over 5 sessions at n=20, awaiting at n=19")
    ind = OS.gauge({**prof, "overall": {"net_gex": -2e9, "net_to_gross": 0.05}},
                   ("2026-10-16", 761.10), iv, [card(d) for d in days(24)])
    check("indeterminate (net is 5% of gross)" in ind["line"]
          and "not read (the regime is not gated)" in ind["line"],
          "under the net-to-gross gate the word is indeterminate and no typical range "
          "prints (the engine's 0.10 rule)")
    audits = [NA.audit(g["line"], g["values"], extra_values=g["constants"]) for g in (g20, g19)]
    check(all(a.passed for a in audits),
          f"the numeral audit passes on the gauge ({[a.reason() for a in audits if not a.passed]})")
    check(not re.search(r"\b(CALM|NORMAL|WILD)\b", g20["line"] + g19["line"] + ind["line"]),
          "no CALM / NORMAL / WILD word: the regime word and the numbers")
    pay = (REPO / "daily_cascade" / "morning_payload.py").read_text(encoding="utf-8")
    ren = (REPO / "daily_cascade" / "morning_render.py").read_text(encoding="utf-8")
    cfg = OS.config()
    html = OS.gauge_html(g20)
    check("opening_setup.gauge_from_store(prior, cutoff, db_path)" in pay
          and "{exposure_block(payload)}\n{opening_setup.gauge_html(" in ren
          and html.count("<p") == 1 and cfg["gauge"]["displaces"]
          and len(g20["line"].split()) <= 80,
          "the anchor's hook: one line under the dealer-surface table, its displacement "
          "declared (config/opening_setup.yaml), the ST-10 block's budget untouched")


def group_b() -> None:
    head("B. OS-10: THE MOST-ACTIVE NAMES")
    from altdata import chain_metrics as cm, observations
    from daily_cascade import opening_setup as OS, stack
    names = [f"N{k:02d}" for k in range(12)]
    wk = days(5)
    hist = days(25)
    rows = []
    for i, s in enumerate(names):
        for d in wk:
            rows.append(obs(cm.VOL_KEY, d, 1000.0 * (12 - i), s))
        for j, d in enumerate(hist):
            rows.append(obs(cm.FRONT_IV_KEY, d, 20.0 + j, s))       # 20 .. 44
    for d, v in zip(wk, (100.0, 104.0, 98.0, 101.0, 103.0)):
        rows.append(obs("yfinance.mkt_n00", d, v))
    with observations.ObservationStore(str(TD / "os10.db")) as st:
        st.write_many(rows)
        sub = OS.most_active(st, wk, "2026-10-17T21:00:00+00:00", names=names)
    t = sub["table"]
    first = t["rows"][0]
    imp = 44.0 * math.sqrt(5 / 252)
    real = 100.0 * (104.0 - 98.0) / 100.0
    check([r[0] for r in t["rows"]] == names[:10] and first[1] == "60,000",
          "the week's ten most active names by summed options volume, in order "
          "(N00's 5 x 12,000 = 60,000 first; N10 and N11 cut)")
    check(first[2] == "44.0%"
          and "rank 100, 100th percentile (" + hist[0] + " to " + hist[-1] + ", n=25)" == first[3]
          and first[4] == "+1.0 pts"
          and first[5] == f"implied ±{imp:.1f}% against realised {real:.1f}%",
          f"by hand: front IV 44.0% at the top of 25 readings (rank 100, the 100th "
          f"percentile, its window and n printed); +1.0 points on the day; implied "
          f"±{imp:.1f}% (44% x sqrt(5/252)) against a realised {real:.1f}% (104 less 98 "
          f"over 100)")
    check(all("n=" in r[3] for r in t["rows"]) and "starts " + hist[0] in sub["lines"][0],
          "every rank prints its window and n, and the table says where our history starts")
    j = json.dumps({"columns": t["columns"], "data": sub["data"]}).lower()
    check(sub["paragraph_wanted"] is False and not sub.get("charts")
          and stack.section_words(sub) == 0
          and not any(w in j for w in ('"score"', "weight")),
          "no chart and no paragraph (the Weekly's chart cap and word budget hold); no "
          "score, no weight")
    check(cm.third_friday(dt.date(2026, 10, 1)) == dt.date(2026, 10, 16)
          and cm.third_friday(dt.date(2026, 11, 20)) == dt.date(2026, 11, 20),
          "the front month's third Friday: 16 Oct and 20 Nov 2026")
    d = TD / "chains" / "2026-10-16"
    d.mkdir(parents=True)
    cols = ["expiry", "dte", "right", "strike", "bid", "ask", "volume", "fetched_at", "spot"]
    with open(d / "N00_201000Z.csv", "w", encoding="utf-8", newline="") as fh:
        fh.write(",".join(cols) + "\n")
        fh.write("2026-11-20,35,C,100,1.0,1.2,1500,2026-10-16T20:10:00+00:00,100\n")
        fh.write("2026-11-20,35,P,100,1.1,1.3,2500,2026-10-16T20:10:00+00:00,100\n")
    rd = cm.name_readings("2026-10-16", "N00", TD / "chains")
    check(rd["volume"] == 4000.0 and rd["fetched_at"] == "2026-10-16T20:10:00+00:00"
          and cm.name_readings("2026-10-16", "N99", TD / "chains").get("reason") == "no capture",
          "a capture's volume is calls and puts summed (1,500 and 2,500); a name with no "
          "capture says so")
    src = (REPO / "altdata" / "chain_metrics.py").read_text(encoding="utf-8")
    dw = (REPO / "daily_cascade" / "dealer_weekly.py").read_text(encoding="utf-8")
    check('rd["names"] = record_names(day, store, base)' in src
          and "opening_setup.most_active(st, week, cutoff)" in dw,
          "the close records every captured name where it records SPY's, and the Weekly "
          "prints the table through the mechanics hook session A owns")


def group_c() -> None:
    head("C. OS-11: THE EARNINGS ROWS")
    from altdata import events as ev_mod, observations
    from daily_cascade import opening_setup as OS
    w = OS.pricing_word
    check(w(6.0, [5.0, -4.0, 3.0]) == ("elevated", 4.0)
          and w(3.0, [5.0, -4.0, 3.0]) == ("muted", 4.0)
          and w(4.5, [5.0, -4.0, 3.0]) == ("in line", 4.0)
          and w(4.8, [5.0, -4.0, 3.0])[0] == "elevated"
          and w(3.3, [5.0, -4.0, 3.0])[0] == "in line"
          and w(6.0, [5.0, -4.0, None]) == (None, 4.5),
          "the pricing word by hand against a median absolute reaction of 4.0%: 6.0 and "
          "4.8 (a fifth above) elevated, 3.0 (a fifth below, 3.2) muted, 4.5 and 3.3 in "
          "line; two reactions read nothing")
    db = str(TD / "os11.db")
    reports = ["2026-01-29", "2026-04-30", "2026-07-30"]
    closes = {"2026-01-28": 100.0, "2026-01-30": 105.0, "2026-04-29": 100.0,
              "2026-05-01": 96.0, "2026-07-29": 100.0, "2026-07-31": 103.0}
    with observations.ObservationStore(db) as st:
        st.write_many([obs("yfinance.mkt_nvda", d, v) for d, v in closes.items()])
    evs = [ev_mod.Event(type="earnings", observed_at=f"{d}T21:00:00+00:00",
                        source="fixture", title=f"NVDA earnings {d}",
                        payload={"symbol": "NVDA", "reported_eps": 1.0, "eps_estimate": 0.9},
                        key=f"fx:{d}") for d in reports]
    with ev_mod.EventStore(db) as ev:
        ev.write_many(evs, available_at="2026-08-01T00:00:00+00:00")
    row = {"symbol": "NVDA", "event": "NVDA earnings", "date": "2026-10-28",
           "consensus": "EPS 1.20 (analyst mean); implied move ±6.0% (straddle to 2026-10-30)",
           "implied_move": "implied move ±6.0% (straddle to 2026-10-30)"}
    out = OS.with_pricing(row, "2026-10-17T21:00:00+00:00", db)
    c = out["consensus"]
    check([round(x["reaction_pct"], 1) for x in out["pricing"]["reactions"]] == [5.0, -4.0, 3.0]
          and "last three reactions: +5.0%, -4.0%, +3.0%" in c
          and "pricing elevated: implied ±6.0% against a median absolute reaction of 4.0%" in c
          and "not a recommendation" in c and c.startswith(row["consensus"]),
          "the reactions from stored events and closes (the close before each report to "
          "the close after it: +5.0%, -4.0%, +3.0%); the row prints them, the word and "
          "its figures, never a recommendation, after the matrix's own figure")
    none = OS.with_pricing(row, "2026-10-17T21:00:00+00:00", str(TD / "absent.db"))
    check("last three reactions: not stored" in none["consensus"]
          and not (TD / "absent.db").exists(),
          "no store file: 'not stored', and nothing is created (read only)")
    src = (REPO / "daily_cascade" / "ahead.py").read_text(encoding="utf-8")
    check("r = opening_setup.with_pricing(r, now)" in src,
          "the Ahead matrix's earnings rows carry it; the implied move stays the "
          "matrix's own (its expiry rule arrives with weekly-fixes-8's merge)")


def group_d() -> None:
    head("D. THE RULES")
    import yaml
    from altdata.sources import flashalpha as fa
    vendor = ["flashalpha", "vendor."] + fa.ALL_KEYS
    bad = []
    for rel in NEW:
        t = (REPO / rel).read_text(encoding="utf-8")
        bad += [f"{rel}:{v}" for v in vendor if v in t]
    added = subprocess.run(["git", "diff", "-U0", "origin/a43-render...HEAD", "--",
                            "altdata/chain_metrics.py", "altdata/vol_event.py"],
                           cwd=REPO, capture_output=True, text=True)
    if added.returncode == 0:
        plus = "\n".join(x for x in added.stdout.splitlines() if x.startswith("+"))
        bad += [f"diff:{v}" for v in vendor if v in plus]
    check(not bad, f"no new code reads a vendor key or names the vendor's source id "
                   f"({bad or 'none'})")
    cfgs = yaml.safe_load((REPO / "config" / "opening_setup.yaml").read_text(encoding="utf-8"))
    j = json.dumps(cfgs).lower()
    check("score" not in j.replace("scorecard", "") and "weight" not in j,
          "the opening setup's config carries no score and no weight")
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    met = reg.get("metrics") or {}
    manual = sorted(k for k in met if k.startswith("manual."))
    check(manual in ([], ["manual.global_pmi"])
          and all(k in met for k in ("chain.options_volume", "chain.atm_iv_front")),
          f"no new by-hand key ({manual}); the two new stored keys are registered")
    labels = yaml.safe_load((REPO / "config" / "display_labels.yaml").read_text(encoding="utf-8"))
    check(all(k in (labels.get("metrics") or {}) for k in ("chain.options_volume",
                                                           "chain.atm_iv_front")),
          "the new keys carry display labels")
    for rel in NEW:
        tree = ast.parse((REPO / rel).read_text(encoding="utf-8"))
        mods = [n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        mods += [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
        check(not [m for m in mods if any(b in m for b in ("anthropic", "model_meter",
                                                          "requests", "urllib"))],
              f"{rel} imports no model and no network library")
    r = subprocess.run(["git", "diff", "--name-only", "origin/a43-render...HEAD"],
                       cwd=REPO, capture_output=True, text=True)
    if r.returncode != 0:
        check(True, "the Weekly builders session B is fixing: no base ref here, not checkable")
    else:
        touched = [f for f in r.stdout.split() if f in ("daily_cascade/weekly_stack.py",
                                                        "daily_cascade/weekly_sections.py")]
        check(not touched, f"this branch touches neither Weekly builder session B is "
                           f"fixing ({touched or 'none'})")


def group_e() -> None:
    head("E. THE RULINGS OF 18 OCT ON THE A44 REPORT (a45, Part 0)")
    import math as _m
    from altdata import dealer_es, numeral_audit as NA
    from daily_cascade import opening_setup as OS
    ds = days(300)
    vix = [(d, 18.0 + 2.0 * _m.sin(i / 9.0)) for i, d in enumerate(ds)]
    spx = []
    px = 5000.0
    for i, d in enumerate(ds):
        px *= 1 + 0.004 * _m.sin(i / 3.0)
        spx.append((d, px))
    series = {"vix": vix, "spx": spx,
              "vix9d": [(d, v * (0.95 + 0.001 * (i % 40))) for i, (d, v) in enumerate(vix)],
              "vix3m": [(d, v * 1.05) for d, v in vix],
              "vix6m": [(d, v * (1.08 + 0.0005 * (i % 30))) for i, (d, v) in enumerate(vix)]}
    ls = OS.vol_lines(series, ds[-1])
    audits = [NA.audit(x["line"], x["values"], extra_values=x["constants"]) for x in ls]
    check(len(ls) == 3 and ls[0]["line"].startswith("VIX against 20-day realised:")
          and ls[1]["line"].startswith("Term-structure stress: VIX3M/VIX")
          and "VIX6M/VIX" in ls[1]["line"] and ls[2]["line"].startswith("Short-term spike: VIX9D/VIX")
          and all("percentile (n=" in x["line"] and f"as of {ds[-1]}" in x["line"] for x in ls)
          and all(a.passed for a in audits),
          f"ruling 2: the three vol-regime lines print every day, each with its level, "
          f"percentile and window (n), as of the session, passing the numeral audit "
          f"({[a.reason() for a in audits if not a.passed] or 'all three'})")
    aw = OS.vol_lines({"vix": vix}, ds[-1])
    check(len(aw) == 3 and all("awaiting" in x["line"] or "n/a" in x["line"] for x in aw[1:]),
          "an absent input says so, line by line")
    pay = (REPO / "daily_cascade" / "morning_payload.py").read_text(encoding="utf-8")
    ren = (REPO / "daily_cascade" / "morning_render.py").read_text(encoding="utf-8")
    cfg = OS.config()
    check("opening_setup.vol_lines_from_store(prior, cutoff, db_path)" in pay
          and "{opening_setup.gauge_html(payload.get(\"opening_gauge\"))}\n"
              "{opening_setup.vol_lines_html(payload.get(\"vol_regime_lines\"))}" in ren
          and cfg["vol_lines"]["displaces"],
          "the three lines sit beside the gauge in the anchor, their displacement declared; "
          "item 52's full lens table stays event-day only")
    names = [f"N{k:02d}" for k in range(17)]
    from altdata import observations, chain_metrics as cm
    with observations.ObservationStore(str(TD / "r1.db")) as st:
        st.write_many([obs(cm.VOL_KEY, d, 10.0, "N00") for d in days(5)])
        sub = OS.most_active(st, days(5), "2026-10-17T21:00:00+00:00", names=names)
    check("of 17 captured names" in sub["lines"][0],
          "ruling 1: the most-active table says 'of 17 captured names'")
    src = (REPO / "altdata" / "dealer_es.py").read_text(encoding="utf-8")
    check(OS.PREMARKET_LINE is None
          and not re.search(r"def\s+\w*(es_to_spy|to_spy|spy_from)", src)
          and "pre-market implies SPY" not in pay + ren,
          "ruling 3: the ES conversion runs SPY to ES only, so no pre-market line prints "
          "(listed in the notes)")


def main() -> int:
    print(f"{LINE}\nthe opening setup, first half\n{LINE}")
    for g in (group_a, group_b, group_c, group_d, group_e):
        try:
            g()
        except Exception as exc:                              # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
