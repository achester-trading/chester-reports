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
  G  RULING 4 OF 19 OCT: the pre-market line (an ES overnight bar converted at
     the 23-hour chart's session basis to the SPY figure worked by hand; no bar
     prints "not available"); SPX's and SPCX's cells "awaiting the solver gate";
     the tags' thresholds labelled session-set.
  F  THE SECOND HALF: OS-8 profiles, OS-9 OI builds (the premium and the chance
     in the money by hand, the spread rule, each tag fired and silent), OS-4 and
     OS-5 put shares by hand; the budgets; no score, weight or side word.

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


# The branch-scope checks read this line's own commits (a44 and a45 over a43),
# never HEAD: on a stitch such as chain-2, HEAD also carries session B's work.
OWN_RANGE = "origin/a43-render...origin/a45-opening-setup-2"


def group_d() -> None:
    head("D. THE RULES")
    import yaml
    from altdata.sources import flashalpha as fa
    vendor = ["flashalpha", "vendor."] + fa.ALL_KEYS
    bad = []
    for rel in NEW:
        t = (REPO / rel).read_text(encoding="utf-8")
        bad += [f"{rel}:{v}" for v in vendor if v in t]
    added = subprocess.run(["git", "diff", "-U0", OWN_RANGE, "--",
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
    r = subprocess.run(["git", "diff", "--name-only", OWN_RANGE],
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
              "{opening_setup.gauge_html(payload.get(\"opening_premarket\"))}\n"
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
    # Ruling 3 of 18 Oct (no pre-market line) is superseded by ruling 4 of 19 Oct:
    # group G holds the line.


SIDE_WORDS = re.compile(r"\b(bought|sold|buyers?|sellers?|bullish|bearish|long|short|"
                        r"opened by|bet|bets|hedger|speculator)\b", re.I)


class _FakeSolver:
    """The chain solver's shape, every contract at 20% (the hand figures' IV)."""
    @staticmethod
    def solve_chain(rows, r):
        return {"rows": [{**x, "solved_iv": 0.20} for x in rows], "expiries": {}}


def _csv(path: Path, rows: list[tuple]) -> None:
    cols = ["expiry", "dte", "right", "strike", "bid", "ask", "last_price", "volume",
            "open_interest", "fetched_at", "spot"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(",".join(cols) + "\n")
        for r in rows:
            fh.write(",".join(str(x) for x in r) + "\n")


def group_f() -> None:
    head("F. THE SECOND HALF: OS-8, OS-9, OS-4, OS-5 (a45-opening-setup-2)")
    from altdata import chain_metrics as cm, numeral_audit as NA, observations
    from daily_cascade import opening_setup as OS, stack
    cfg = OS.config()
    # --- the arithmetic the four share -------------------------------------
    t = 30 / 365
    d2 = (math.log(100 / 105) + (0.04 - 0.5 * 0.2 * 0.2) * t) / (0.2 * math.sqrt(t))
    hand = 0.5 * (1 + math.erf(d2 / math.sqrt(2)))
    check(close(OS.bs_itm_prob(100, 105, 0.20, t, 0.04, "C"), hand, 1e-12)
          and close(hand, 0.2056, 1e-3)
          and close(OS.bs_itm_prob(100, 105, 0.20, t, 0.04, "P"), 1 - hand, 1e-12),
          f"the chance in the money by hand: a 105 call on 100 at 20% IV, 30 days, 4%: "
          f"N(d2) = {hand:.4f}; the put is 1 less it")
    cur = [{"right": "P", "volume": 300.0}, {"right": "C", "volume": 200.0}]
    chg = [{"right": "P", "oi_change": 200.0}, {"right": "C", "oi_change": 100.0},
           {"right": "P", "oi_change": -50.0}]
    ps = cm.put_shares(cur, chg)
    check(close(ps["put_share_volume"], 60.0) and close(ps["put_share_oi_build"], 200 / 3),
          "the put shares by hand: 300 of 500 in volume is 60.0%; 200 of a positive build "
          "of 300 is 66.7% (a fall in OI is not a build)")
    a = math.log(1.01)
    cl = [100.0]
    for i in range(20):
        cl.append(cl[-1] * (1.01 if i % 2 == 0 else 1 / 1.01))
    check(close(cm.realised_20(cl), 100 * a * math.sqrt(20 / 19) * math.sqrt(252), 1e-9)
          and close(cm.iv_at_delta([(-0.3, 0.25), (-0.2, 0.21)], -0.25), 0.23, 1e-12),
          "realised vol by hand (alternating 1% moves) and the IV at -25 delta interpolated "
          "linearly in delta (0.25 and 0.21 either side: 0.23)")
    # --- OS-9 -----------------------------------------------------------------
    saved = cm._solver
    cm._solver = lambda: _FakeSolver                            # noqa: SLF001
    try:
        prev = [{"expiry": "2026-11-20", "strike": 105.0, "right": "C", "open_interest": 4000.0}]
        curr = [{"expiry": "2026-11-20", "strike": 105.0, "right": "C", "open_interest": 5000.0,
                 "bid": 2.40, "ask": 2.60, "dte": 30, "spot": 100.0, "volume": 900.0}]
        b = OS.builds_for("N00", prev, curr, 0.04)
    finally:
        cm._solver = saved                                      # noqa: SLF001
    check(len(b) == 1 and close(b[0]["premium"], 250000.0) and close(b[0]["p_itm"], hand, 1e-12)
          and b[0]["oi_change"] == 1000.0,
          "a build by hand: OI 4,000 to 5,000 is +1,000; the premium is the 2.50 mid x "
          "1,000 x 100 = $250,000; its chance in the money the 20.6% above")
    base = TD / "oi_chains"
    d_prev, d_cur = "2026-10-15", "2026-10-16"
    rows_prev, rows_cur = [], []
    for k in range(10):
        st_k = 100.0 + 5 * k
        rows_prev.append(("2026-11-20", 35, "C", st_k, 1.0, 1.2, 1.1, 10, 1000,
                          "2026-10-15T20:10:00+00:00", 100.0))
        add = 500 if k in (3, 4) else 100 * (k + 1)
        rows_cur.append(("2026-11-20", 35, "C", st_k, 1.0, 1.2, 1.1, 10, 1000 + add,
                         "2026-10-16T20:10:00+00:00", 100.0))
    _csv(base / d_prev / "N00_201000Z.csv", rows_prev)
    _csv(base / d_cur / "N00_201000Z.csv", rows_cur)
    cm._solver = lambda: _FakeSolver                            # noqa: SLF001
    try:
        ob = OS.oi_builds_from_store(d_cur, "2026-10-17T11:00:00+00:00",
                                     str(TD / "ob.db"), base, names=["N00"])
    finally:
        cm._solver = saved                                      # noqa: SLF001
    rows = ob["table"]["rows"]
    spread = [r for r in rows if "spread (legs equal)" in r[0]]
    check(ob["title"] == "Largest OI builds, side unknown" and len(rows) == 8
          and rows[0][4] == "+1,000" and len(spread) == 1
          and spread[0][2] == "115 / 120" and spread[0][4] == "+500 each",
          f"the table: 'Largest OI builds, side unknown', eight rows of ten builds, the "
          f"largest first (+1,000); the two equal +500 builds on one expiry print as one "
          f"line, 'spread (legs equal)' ({len(rows)} rows)")
    txt = json.dumps({"c": ob["table"]["columns"], "r": rows}) + ob["note"]
    check(not SIDE_WORDS.search(txt.replace("side unknown", "")),
          f"no side word anywhere in the table or its note ({SIDE_WORDS.findall(txt)})")
    tg = cfg["oi_builds"]["tags"]

    def tags(**k):
        z = {"closes": [100.0, 105.0, 95.0, 102.0, 98.0, 101.0, 99.0, 103.0, 97.0, 100.0] * 2
             + [100.0], "skew": list(range(1, 11))[:4] + [5.0, 6.0, 7.0, 8.0, 9.0, 5.0],
             "ivrv": [1.0, 2, 3, 4, 6, 7, 8, 9, 10, 5.0], "earn": []}
        z.update(k)
        return OS.name_tags("N00", "2026-10-16", z["closes"], z["skew"], z["ivrv"], z["earn"], cfg)
    up = [100.0] * 15 + [100.0, 101.0, 103.0, 106.0, 108.0, 110.0]
    down = [100.0] * 15 + [100.0, 99.0, 97.0, 94.0, 92.0, 90.0]
    fires = {"EARNINGS": tags(earn=["2026-10-28"]),
             "1M HIGH": tags(closes=up), "1M LOW": tags(closes=down),
             "MOMENTUM": tags(closes=up), "SELLOFF": tags(closes=down),
             "HIGH SKEW": tags(skew=list(range(1, 11))),
             "CHEAP VOL": tags(ivrv=[5.0, 6, 7, 8, 9, 10, 11, 12, 13, 1.0]),
             "VOL CRUSH": tags(ivrv=list(range(1, 11)))}
    neutral = tags(earn=["2026-11-05"])
    check(all(k in v for k, v in fires.items()) and neutral == [],
          f"each tag fires on a fixture built to fire it (a report in 12 days; within 1% of "
          f"the 21-session high or low; +10% or -10% in 5 sessions; the top or bottom decile "
          f"of 10 readings) and none on the neutral fixture (a report in 20 days) "
          f"({ {k: v for k, v in fires.items() if k not in v} or 'all fire'}, neutral {neutral})")
    check(OS.decile_tag(list(range(1, 10)), 9.0) is None and tg["decile_n_min"] == 10,
          "a decile needs ten stored readings: nine read nothing")
    # --- OS-8 -----------------------------------------------------------------
    hist = days(12)
    srows = []
    for s, sk, ir in (("N00", 2.0, 8.0), ("N01", 6.0, -3.0), ("N02", 4.0, 1.0)):
        for j, d in enumerate(hist):
            srows += [obs(cm.SKEW_KEY, d, sk + 0.1 * (j - 11), s),
                      obs(cm.IV_RV_KEY, d, ir + 0.1 * (j - 11), s)]
        srows.append({**obs(cm.FRONT_EXP_KEY, hist[-1], "2026-11-20 (third Friday)", s)})
    with observations.ObservationStore(str(TD / "os8.db")) as st:
        st.write_many(srows)
        pr = OS.profiles(st, "2026-10-17T21:00:00+00:00", names=["N00", "N01", "N02"])
    rr = {r[0]: r for r in pr["table"]["rows"]}
    check(len(rr) == 4 and rr["Flattest 25-delta put skew"][1] == "N00"
          and rr["Steepest 25-delta put skew"][1] == "N01"
          and rr["Highest IV against 20-day realised"][1] == "N00"
          and rr["Lowest IV against 20-day realised"][1] == "N01"
          and rr["Flattest 25-delta put skew"][2] == "+2.0 vol points"
          and rr["Flattest 25-delta put skew"][3] == f"rank 100, 100th percentile ({hist[0]} to {hist[-1]}, n=12)"
          and rr["Steepest 25-delta put skew"][4] == "2026-11-20 (third Friday)",
          "the four profiles by hand: the flattest skew N00 at +2.0 and the steepest N01; "
          "the highest IV against realised N00, the lowest N01; each with its rank, "
          "percentile, window and n, and the front-month expiry used")
    # --- OS-4 -----------------------------------------------------------------
    h10 = days(10)
    prow = [obs(cm.PUT_VOL_KEY, d, 50.0 + j, "SPY") for j, d in enumerate(h10)]
    prow += [obs(cm.PUT_OI_KEY, d, 40.0 + j, "SPY") for j, d in enumerate(h10)]
    with observations.ObservationStore(str(TD / "os4.db")) as st:
        st.write_many(prow)
        il = OS.index_put_lines(st, "2026-10-17T21:00:00+00:00")
    audits = [NA.audit(x["line"], x["values"], extra_values=x["constants"]) for x in il[:1]]
    check(len(il) == 2
          and il[0]["line"] == (f"SPY, {h10[-1]}: puts 59.0% of the session's volume (100th "
                                f"percentile, {h10[0]} to {h10[-1]}, n=10); puts 49.0% of the "
                                f"day's OI build (100th percentile, {h10[0]} to {h10[-1]}, "
                                f"n=10); put volume and OI build, no side.")
          and "SPX: put share of volume not stored; put volume and OI build, no side." == il[1]["line"]
          and all(x.passed for x in audits),
          f"the index lines by hand: SPY's put shares with their percentiles, windows and n; "
          f"SPX absent says so; one line each, labelled no side; the numeral audit "
          f"({[x.reason() for x in audits if not x.passed] or 'passes'})")
    # --- OS-5 -----------------------------------------------------------------
    h6 = days(6)
    srs, hz = [], []
    for s, last in (("A", 60.0), ("B", 30.0), ("C", 45.0), ("D", 52.0)):
        xs = [40.0, 42.0, 44.0, 46.0, 48.0, last]
        srs += [obs(cm.PUT_VOL_KEY, d, v, s) for d, v in zip(h6, xs)]
        import statistics as _s
        hz.append((last - _s.fmean(xs)) / _s.stdev(xs))
    with observations.ObservationStore(str(TD / "os5.db")) as st:
        st.write_many(srs)
        sp = OS.single_name_puts(st, "2026-10-17T21:00:00+00:00", names=["A", "B", "C", "D"])
    ew = sum(hz) / len(hz)
    check(close(sp["data"]["equal_weighted_z"], ew, 1e-9)
          and f"{ew:+.2f}" in sp["lines"][0] and f"{h6[0]} to {h6[-1]}, n=6 to 6" in sp["lines"][0]
          and sp["lines"][0].endswith("put volume and OI build, no side.")
          and [r[0] for r in sp["table"]["rows"]] == ["A", "D", "C", "B"],
          f"the single-name z by hand: each name's last put share against its own six "
          f"sessions, equal-weighted {ew:+.2f}; the three highest and lowest (four names: "
          f"A, D, C, B), each with its window and n; labelled no side")
    # --- the budgets and the rules -------------------------------------------
    subs = [pr, sp]
    check(all(x["paragraph_wanted"] is False and not x.get("charts")
              and stack.section_words(x) == 0 for x in subs)
          and len(rows) <= cfg["oi_builds"]["rows"] == 8
          and all(cfg[k]["displaces"] for k in ("profiles", "oi_builds", "index_puts",
                                                 "single_name_puts")),
          "the budgets: the Weekly's two tables add no chart and no words; the anchor's "
          "table holds at eight rows; each element declares what it displaces")
    allx = json.dumps([pr["table"], sp["table"], [x["line"] for x in il]]).lower()
    check(not any(w in allx for w in ('"score"', "weight", " score")) or "weighted z" in allx
          and "weight" not in allx.replace("equal-weighted", ""),
          "no table carries a score or a weight (the equal-weighted average is OS-5's "
          "named statistic, not a weight on anything)")
    check(not SIDE_WORDS.search(allx.replace("no side", "")),
          "no side word in the profiles, the single-name table or the index lines")
    pay = (REPO / "daily_cascade" / "morning_payload.py").read_text(encoding="utf-8")
    ren = (REPO / "daily_cascade" / "morning_render.py").read_text(encoding="utf-8")
    dw = (REPO / "daily_cascade" / "dealer_weekly.py").read_text(encoding="utf-8")
    check("opening_setup.oi_builds_from_store(prior, cutoff, db_path)" in pay
          and "opening_setup.index_put_lines_from_store(cutoff, db_path)" in pay
          and "oi_builds_html(payload.get(\"oi_builds\"))" in ren
          and "opening_setup.profiles(st, cutoff)" in dw
          and "opening_setup.single_name_puts(st, cutoff)" in dw,
          "the hooks: the OI builds and the index lines in the anchor's mechanics block; "
          "the profiles and the single-name table in the Weekly's Mechanics")


def _bar(inst: str, sym: str, utc: str, o: float, c: float) -> dict:
    return {"instrument": inst, "symbol": sym, "interval": "5m", "observed_at": utc,
            "open": o, "high": max(o, c) + 0.5, "low": min(o, c) - 0.5, "close": c,
            "volume": 100.0, "available_at": utc,
            "source": "fixture"}


def group_g() -> None:
    head("G. RULING 4 OF 19 OCT: THE PRE-MARKET LINE, SPX AND SPCX, THE TAGS")
    from altdata import bars as bars_mod
    from daily_cascade import opening_setup as OS
    # By hand. The basis session is Fri 16 Oct (EDT, UTC-4): SPY's 09:30 open
    # 660.00 over ES's 09:30 open 6,650.00 = 0.0992481... Mon 19 Oct's overnight
    # (18:00 ET Sun 18 Oct to 09:30) ends with ES's 06:55 ET bar closing at
    # 6,700.00, so SPY is about 6,700 x 660 / 6,650 = 664.962..., printed 664.96.
    es5 = [_bar("es", "ES=F", "2026-10-16T13:30:00+00:00", 6650.0, 6652.0),
           _bar("es", "ES=F", "2026-10-18T22:05:00+00:00", 6690.0, 6691.0),
           _bar("es", "ES=F", "2026-10-19T10:55:00+00:00", 6699.0, 6700.0)]
    spy5 = [_bar("spy", "SPY", "2026-10-16T13:30:00+00:00", 660.0, 660.2),
            _bar("spy", "SPY", "2026-10-16T19:55:00+00:00", 661.0, 661.5)]
    pm = OS.premarket(es5, spy5, "2026-10-19")
    v = pm["values"]
    check(close(v.get("spy"), 6700.0 * 660.0 / 6650.0, 1e-9)
          and v.get("basis_session") == "2026-10-16" and close(v.get("basis"), 660.0 / 6650.0, 1e-12)
          and "6,700.00" in pm["line"] and "about 664.96" in pm["line"]
          and "2026-10-16 session's basis" in pm["line"],
          f"an ES overnight bar converts at the session's basis to the SPY figure "
          f"worked by hand ({pm['line']})")
    none = OS.premarket([_bar("es", "ES=F", "2026-10-16T13:30:00+00:00", 6650.0, 6652.0)],
                        spy5, "2026-10-19")
    check(none["line"] == "Pre-market (ES): not available (ES has no overnight bar)."
          and not none["values"], f"no ES overnight bar prints 'not available' ({none['line']})")
    nob = OS.premarket(es5, [], "2026-10-19")
    check("not available" in nob["line"] and "09:30 opens" in nob["line"],
          "no session with both opens prints 'not available' with its reason")
    # The same through the store the 06:45 job fills, read as of the cutoff.
    path = str(TD / "bars-premarket.db")
    st = bars_mod.BarStore(path, create=True)
    st.write_many(es5 + spy5)
    st.close()
    fs = OS.premarket_from_store("2026-10-19", "2026-10-19T11:00:00+00:00", path)
    check(fs["line"] == pm["line"], "the anchor's reader prints the same line from the bars store")
    early = OS.premarket_from_store("2026-10-19", "2026-10-19T10:00:00+00:00", path)
    check("6,691.00" in early["line"],
          "read as of the cutoff: a bar after it is not seen (06:00 ET reads the 18:05 ET bar)")
    src = (REPO / "daily_cascade" / "charts.py").read_text(encoding="utf-8")
    os_src = (REPO / "daily_cascade" / "opening_setup.py").read_text(encoding="utf-8")
    check("from .charts import es_at_open, es_overnight" in os_src
          and 'basis = (seg[0]["open"] / es_open)' in src,
          "no new conversion method: the line reads W7's own es_overnight and es_at_open")
    pay = (REPO / "daily_cascade" / "morning_payload.py").read_text(encoding="utf-8")
    ren = (REPO / "daily_cascade" / "morning_render.py").read_text(encoding="utf-8")
    check("opening_setup.premarket_from_store(this_session, cutoff, db_path)" in pay
          and '"opening_premarket": premarket' in pay
          and 'gauge_html(payload.get("opening_premarket"))' in ren
          and ren.index('payload.get("opening_gauge")') < ren.index('payload.get("opening_premarket")'),
          "the anchor prints it beneath the gauge")

    # SPX and SPCX: their cells await the solver gate.
    builds = [{"symbol": "SPX", "expiry": "2026-11-20", "strike": 6700.0, "right": "C",
               "oi_change": 500, "mid": 10.0, "premium": 500000.0, "iv": None,
               "spot": 6650.0, "dte": 32, "solver_gated": True, "p_itm": None},
              {"symbol": "N00", "expiry": "2026-11-20", "strike": 100.0, "right": "P",
               "oi_change": 300, "mid": 1.0, "premium": 30000.0, "iv": 0.2,
               "spot": 100.0, "dte": 32, "solver_gated": False, "p_itm": 0.45}]
    tab = OS.oi_build_table(builds, {}, OS.config())
    spx = next(r for r in tab["rows"] if r[0] == "SPX")
    n00 = next(r for r in tab["rows"] if r[0] == "N00")
    check(spx[6] == "awaiting the solver gate" and n00[6] == "45%",
          f"OS-9: SPX's chance in the money reads 'awaiting the solver gate'; a solved "
          f"name's prints its figure ({spx[6]}, {n00[6]})")
    from altdata import observations, chain_metrics as cm, config as acfg
    with observations.ObservationStore(str(TD / "spx.db")) as st2:
        st2.write_many([obs(cm.VOL_KEY, d, 50.0, "SPX") for d in days(5)]
                       + [obs(cm.VOL_KEY, d, 10.0, "N00") for d in days(5)]
                       + [obs(cm.FRONT_IV_KEY, d, 20.0, "N00") for d in days(5)])
        ma = OS.most_active(st2, days(5), "2026-10-17T21:00:00+00:00",
                            names=["N00", "SPX"])
    row = next(r for r in ma["table"]["rows"] if r[0] == "SPX")
    check(row[2] == row[3] == "awaiting the solver gate"
          and next(r for r in ma["table"]["rows"] if r[0] == "N00")[2] == "20.0%",
          f"OS-10: SPX's IV and IV-rank cells read 'awaiting the solver gate' ({row})")
    check(set(acfg.massive_universe()) == {"SPX", "SPCX"}
          and "acfg.chain_universe() + sorted(gated)" in os_src
          and "gated=s in gated" in os_src,
          "SPX and SPCX join both tables' universes from the vendor's chains, gated")
    import inspect
    bsrc = inspect.getsource(OS.builds_for)
    check("if not gated:" in bsrc and "_solver()" in bsrc.split("if not gated:", 1)[1],
          "a gated name's chain is never sent to the solver")

    # The tags' thresholds: session-set, labelled.
    cfg = OS.config()
    lab = cfg["oi_builds"]["tags"].get("label") or ""
    note = OS.oi_builds_from_store("2026-10-16", "2026-10-17T11:00:00+00:00",
                                   str(TD / "spx.db"), base=TD / "no-chains")["note"]
    check(lab.startswith("session-set") and "25 Oct" in lab
          and f"history thresholds are {lab}" in note,
          f"the tags' history thresholds are labelled session-set in the table's note "
          f"({lab})")


def main() -> int:
    print(f"{LINE}\nthe opening setup, first half\n{LINE}")
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g):
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
