"""
Validation gate for ST-R4, Tranche 1 part 2 -- Batch 5 items 18, 19, 22 and 27
(signal-triage round 4, part 2; filed 9 Oct 2026). A code gate: it seeds its own
temporary stores, never reads the live store, never fetches and never calls a
model. No figure here is real.

  A  ST-R4.18a  THE DISPERSION PANEL: dual percentiles print their n and real
     window; the "dispersion regime" flag fires high at the 80th percentile and
     not at the 79.67th, low at the 20th and not at the 20.33rd, and is withheld
     below 250 sessions; high dispersion with low implied correlation prints its
     line; the realized fallback prints "awaiting constituent prices" until its
     series is named, and computes the cross-sectional dispersion by hand once it
     is; the two by-hand FlashAlpha keys print when entered.
  B  ST-R4.19a  THE CROSS-ASSET VOL DIVERGENCE FLAG: z and percentile over one
     year; watch fires at MOVE z +0.51 and not at +0.50; strong at +1.01 and not
     at +1.00; neither with the VIX's z at +0.40; the conditioner inactive while
     T&B is not built, and on a fixture that pretends T&B fired it discounts
     within 12 months and not after; the read's line only when a tier is live.
  C  ST-R4.22a  THE EXPANSION'S AGE: the code's hazard agrees with the fixture's
     hand-computed table at every age; 78 months at October 2026, 0 of 4; past
     the longest, no base rate.
  D  ST-R4.22b  FACTOR I: the two contributions summed, real GDP's annualized
     growth and the share by hand; absent by plain name when not stored.
  E  ST-R4.27a  OVERNIGHT VS SESSION: the two legs sum to the daily change on
     every session; 20-session sums and the leg that carried the move; the
     co-signal on at -2 sigma on a fixture and counted in SR-36's unwind watch.
  F  THE PRINT AND THE REGISTRY: the hooks in the Weekly and the Monthly; every
     new key registered with its units; the catalogue line; the basket and the
     OHLC set; no internal id and no ISO date outside a table; neither module can
     fetch (22b is a FRED extension).
  G  THE CBOE HISTORY READER (ruling (e), 16 Oct 2026): the CLOSE column and
     DSPX's one column read by name, a blank row skipped; robots.txt checked on
     both hosts, a 403 read as no rules, a refusal fetching no file and writing
     nothing; not held, on the external roster, its KEYS read from source; the
     panel reads Cboe's key first and Yahoo's as the fallback, never spliced,
     and says which.

    python tools/validate_st_r4_t1b.py
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import datetime as dt
import json
import math
import re
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import gate_tmp  # noqa: E402
import yaml  # noqa: E402

from altdata import batch5b, derived, observations  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = 0
FAIL = 0
LINE = "=" * 78
CFG = batch5b.config()
CUT = "2026-10-09T23:00:00+00:00"


def check(c: bool, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


def store(rows: list[tuple]) -> str:
    """A temporary store of (key, day, value[, instrument]), each available
    21:00 UTC on its day."""
    db = str(Path(gate_tmp.mkdtemp("st_r4b_")) / "obs.db")
    with observations.ObservationStore(db) as st:
        if rows:
            st.write_many([{"registry_key": r[0],
                            "instrument": r[3] if len(r) > 3 else None,
                            "observed_at": r[1], "available_at": r[1] + "T21:00:00+00:00",
                            "value": float(r[2]), "source": "fixture"} for r in rows])
    return db


def weekdays_back(end: str, n: int) -> list[str]:
    d, out = dt.date.fromisoformat(end), []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d -= dt.timedelta(days=1)
    return out[::-1]


def no_iso(sub: dict) -> bool:
    txt = " ".join(list(sub.get("lines") or []) + [sub.get("table_note") or ""])
    return not re.search(r"\d{4}-\d{2}-\d{2}", txt)


def printed(sub: dict) -> str:
    return json.dumps({k: v for k, v in sub.items() if k != "data"}, ensure_ascii=False)


def with_z(base: list[float], target: float) -> list[float]:
    """base + [x], x found by bisection so that derived.z_of(all, x) == target."""
    lo, hi = min(base) - 50 * statistics.pstdev(base), max(base) + 50 * statistics.pstdev(base)
    for _ in range(200):
        mid = (lo + hi) / 2
        if derived.z_of(base + [mid], mid) < target:
            lo = mid
        else:
            hi = mid
    return base + [(lo + hi) / 2]


# ---------------------------------------------------------------------------
def _dspx(last: float, n: int = 300) -> list[tuple]:
    days = weekdays_back("2026-10-09", n)
    return [("yfinance.mkt_dspx", d, float(i + 1)) for i, d in enumerate(days[:-1])] + \
           [("yfinance.mkt_dspx", days[-1], last)]


def group_a() -> None:
    head("A. ST-R4.18a  THE DISPERSION PANEL")
    from daily_cascade import batch5b_block as blk
    res = {}
    for name, last in (("high80", 239.5), ("below80", 238.5), ("low20", 59.5),
                       ("above20", 60.5)):
        with observations.ObservationStore(store(_dspx(last))) as st:
            res[name] = batch5b.dispersion(st, CUT, CFG)
    f = {k: v["flag"] for k, v in res.items()}
    check(f["high80"]["state"] == "high" and f["high80"]["pct"] == 80.0,
          f"high fires at the 80th percentile ({f['high80'].get('pct')})")
    check(f["below80"]["state"] == "none",
          f"and not at the {f['below80'].get('pct')}th")
    check(f["low20"]["state"] == "low" and f["low20"]["pct"] == 20.0,
          f"low fires at the 20th percentile ({f['low20'].get('pct')})")
    check(f["above20"]["state"] == "none", f"and not at the {f['above20'].get('pct')}th")
    p = res["high80"]["rows"]["dspx"]["percentiles"]
    check(p[5]["n"] == 300 and p[5]["short"] and p[5]["window_years_real"] < 1.3
          and not p[1]["short"] and p[1]["n"] < 300,
          f"each window prints its n and real span: 1 year n={p[1]['n']}, 5 years "
          f"n={p[5]['n']} holding {p[5]['window_years_real']} years")
    with observations.ObservationStore(store(_dspx(500.0, 200))) as st:
        short = batch5b.dispersion(st, CUT, CFG)
    check(short["flag"]["state"] is None and "withheld" in short["flag"]["why"]
          and "200 sessions" in short["flag"]["why"],
          f"withheld below 250 sessions ({short['flag']['why']})")
    # High dispersion with low implied correlation.
    days = weekdays_back("2026-10-09", 300)
    cor = [("yfinance.mkt_cor3m", d, 300.0 - i) for i, d in enumerate(days)]
    with observations.ObservationStore(store(_dspx(400.0) + cor)) as st:
        pair = batch5b.dispersion(st, CUT, CFG)
        sub = blk.dispersion_subsection(st, CUT, CFG)
    check(pair["flag"]["state"] == "high" and pair["single_name_edge"]
          and any("single names" in x for x in sub["lines"]),
          "DSPX high with COR3M at its low prints the single-name line")
    check(any("Implied correlation, 1 month" in x and "Not stored" in x
              for x in sub["lines"]),
          "a COR index not stored is a listed gap, never guessed")
    check(any(r[1] == "awaiting constituent prices" for r in sub["table"]["rows"])
          and any("awaiting constituent prices" in x for x in sub["lines"]),
          "the realized fallback prints 'awaiting constituent prices' while its series "
          "has no rows")
    check(CFG["dispersion"]["realized"]["key"] == "sp500.member_close",
          "the fallback reads session A's item 44 series, sp500.member_close")
    # The fallback, once named: 120 names, each with a constant daily log return
    # r_i = (i - 59.5) * 0.001, so the cross-sectional sd is the same every day:
    # 0.001 * sqrt((120^2 - 1) / 12) = 3.4637% a day.
    cdays = weekdays_back("2026-10-09", 25)
    rows = [("fixture.constituent_close", d, 100.0 * math.exp((i - 59.5) * 0.001 * j),
             f"N{i:03d}") for i in range(120) for j, d in enumerate(cdays)]
    cfg = json.loads(json.dumps(CFG))
    cfg["dispersion"]["realized"]["key"] = "fixture.constituent_close"
    with observations.ObservationStore(store(rows)) as st:
        rz = batch5b.realized_dispersion(st, CUT, cfg["dispersion"]["realized"])
    want = 0.1 * math.sqrt((120 ** 2 - 1) / 12)
    check(not rz.get("absent") and abs(rz["value"] - want) < 1e-3 and rz["names"] == 120,
          f"named, it computes the cross-sectional dispersion by hand ({rz.get('value')} "
          f"against {want:.4f}% a day)")
    man = [("manual.flashalpha_implied_corr", "2026-10-07", 0.42),
           ("manual.flashalpha_realized_corr", "2026-10-07", 0.31)]
    with observations.ObservationStore(store(_dspx(239.5) + man)) as st:
        sub = blk.dispersion_subsection(st, CUT, CFG)
    check(not any(r[0].startswith("FlashAlpha") for r in sub["table"]["rows"])
          and "manual" not in CFG["dispersion"],
          "no by-hand FlashAlpha row, even with figures stored: ST-R4.18b's keys are "
          "not by-hand keys under the by-hand audit (chain-2 stitch, 19 Oct 2026)")
    check(no_iso(sub) and "DISPERSION REGIME: HIGH" in printed(sub),
          "the flag line prints, with no ISO date outside the table")


# ---------------------------------------------------------------------------
def _vol_store(move_z: float, vix_z: float, extra: list | None = None) -> str:
    days = weekdays_back("2026-10-09", 252)
    base_m = [100 + 10 * math.sin(i / 7.0) for i in range(251)]
    base_v = [20 + 3 * math.cos(i / 5.0) for i in range(251)]
    m, v = with_z(base_m, move_z), with_z(base_v, vix_z)
    return store([("yfinance.mkt_move", d, m[i]) for i, d in enumerate(days)]
                 + [("yfinance.mkt_vix", d, v[i]) for i, d in enumerate(days)]
                 + (extra or []))


def group_b() -> None:
    head("B. ST-R4.19a  THE CROSS-ASSET VOL DIVERGENCE FLAG")
    from daily_cascade import batch5b_block as blk
    got = {}
    for mz, vz in ((0.51, 0.0), (0.50, 0.0), (1.01, 0.39), (1.00, 0.39), (1.5, 0.40),
                   (0.8, -0.57)):
        with observations.ObservationStore(_vol_store(mz, vz)) as st:
            got[(mz, vz)] = batch5b.vol_divergence(st, CUT, CFG)
    t = {k: v["tier"] for k, v in got.items()}
    check(t[(0.51, 0.0)] == "watch" and t[(0.50, 0.0)] is None,
          "watch fires at MOVE z +0.51 and not at +0.50 (strictly above, as ruled)")
    check(t[(1.01, 0.39)] == "strong" and t[(1.00, 0.39)] == "watch",
          "strong fires at +1.01; at +1.00 it is watch, not strong")
    check(t[(1.5, 0.40)] is None, "no tier with the VIX's z at +0.40 (below +0.4 needed)")
    g = got[(0.8, -0.57)]
    check(g["n"] == 252 and g["move"]["pct"] is not None and g["vix"]["pct"] is not None
          and g["spread_z"] == round(0.8 + 0.57, 2),
          f"one-year window (n={g['n']}), percentile ranks beside z, spread "
          f"{g['spread_z']:+.2f}")
    check(g["conditioner"]["active"] is False and g["conditioner"]["why"] ==
          "T&B not built; conditioner inactive",
          "the conditioner prints 'T&B not built; conditioner inactive'")
    cfg = json.loads(json.dumps(CFG))
    cfg["vol_divergence"]["tb_bottom"]["key"] = "fixture.tb_bottom_signal"
    with observations.ObservationStore(_vol_store(
            1.2, 0.0, [("fixture.tb_bottom_signal", "2026-04-15", 1)])) as st:
        disc = batch5b.vol_divergence(st, CUT, cfg)
    with observations.ObservationStore(_vol_store(
            1.2, 0.0, [("fixture.tb_bottom_signal", "2025-09-15", 1)])) as st:
        old = batch5b.vol_divergence(st, CUT, cfg)
    check(disc["conditioner"]["discounted"] and disc["conditioner"]["fired"] == "2026-04-15"
          and "discounted" in blk._vol_line(disc),
          "pretending T&B fired six months ago: the flag is discounted and says so")
    check(old["conditioner"]["active"] and not old["conditioner"]["discounted"],
          "fired thirteen months ago: active, not discounted")
    with observations.ObservationStore(_vol_store(1.2, 0.0)) as st:
        on = blk.read_items(st, CUT)
        sub = blk.vol_subsection(st, CUT, CFG)
    with observations.ObservationStore(_vol_store(0.3, 0.0)) as st:
        off = blk.read_items(st, CUT)
    check(len(on) == 1 and on[0][0] == "mech:vol_divergence"
          and "STRONG TIER" in on[0][1] and not off,
          "the read carries one line when a tier is live, none when not")
    check([r[0] for r in sub["table"]["rows"]][:2] == ["The MOVE (Treasury implied vol)",
                                                      "The VIX (S&P 500 implied vol)"]
          and blk._prose(sub, CUT) and no_iso(blk._prose(sub, CUT)),
          "Mechanics' table: level, z and percentile, no ISO date outside it")
    with observations.ObservationStore(store([])) as st:
        none = batch5b.vol_divergence(st, CUT, CFG)
    check(none["absent"] and "the MOVE" in none["reason"],
          f"absent with its reason by plain name ({none['reason']})")


# ---------------------------------------------------------------------------
def group_c() -> None:
    head("C. ST-R4.22a  THE EXPANSION'S AGE AND THE POST-WAR HAZARD")
    fx = yaml.safe_load((REPO / "config" / "nber_expansions.yaml").read_text(
        encoding="utf-8"))
    done = [e["months"] for e in fx["expansions"] if e.get("peak")]
    check(len(done) == 12 and sum(done) == 770 and done[-1] == 128
          and fx["expansions"][-1] == {"trough": "2020-04", "peak": None}
          and "nber.org" in fx["source"],
          "the fixture: twelve completed post-war expansions (770 months), the "
          "current one from April 2020, its source named")
    bad = [(r["age"], (h["ended"], h["of"]), (r["ended"], r["of"]))
           for r in fx["hazard_check"] for h in [batch5b.hazard(done, r["age"])]
           if (h["ended"], h["of"]) != (r["ended"], r["of"])]
    check(not bad, f"the code's hazard agrees with the hand-computed table at all "
                   f"{len(fx['hazard_check'])} ages ({bad[:2] or 'no difference'})")
    e = batch5b.expansion_age(CUT, CFG)
    check(e["age_months"] == 78 and e["hazard"]["of"] == 4 and e["hazard"]["ended"] == 0
          and e["mean"] == 64.2 and e["median"] == 51.5 and e["modern"]["n"] == 4,
          f"October 2026: 78 months, 0 of 4 ended within 12 months; mean {e['mean']}, "
          f"median {e['median']}; four since 1982")
    from daily_cascade import batch5b_block as blk
    sub = blk.expansion_subsection(CUT, CFG)
    ln = sub["lines"][0]
    check("April 2020 trough is 78 months old" in ln and "4 lasted 78 months or more"
          in ln and "0 of those 4 ended" in ln and "not a timing tool" in ln,
          "one line in the slow layers, base rate and caveat")
    far = blk.expansion_subsection("2031-01-09T23:00:00+00:00", CFG)["lines"][0]
    check("no base rate past the longest (128 months)" in far,
          "past the longest expansion the line says there is no base rate")


# ---------------------------------------------------------------------------
def group_d() -> None:
    head("D. ST-R4.22b  FACTOR I: INFORMATION PROCESSING IN REAL GDP GROWTH")
    qs = ["2025-07-01", "2025-10-01", "2026-01-01", "2026-04-01"]
    eq, sw = [0.30, 0.67, 0.79, 0.19], [0.08, 0.05, 0.60, 0.33]
    gdp = [100.0, 100.5, 100.6, 100.6, 101.606]   # the last step: +1% q/q
    rows = ([("fred.contrib_info_equipment", d, v) for d, v in zip(qs, eq)]
            + [("fred.contrib_software", d, v) for d, v in zip(qs, sw)]
            + [("fred.real_gdp", d, v) for d, v in zip(["2025-04-01"] + qs, gdp)])
    with observations.ObservationStore(store(rows)) as st:
        f = batch5b.factor_i(st, CUT, CFG)
        from daily_cascade import batch5b_block as blk
        sub = blk.factor_i_subsection(st, CUT, CFG)
    lt = f["latest"]
    g = round((1.01 ** 4 - 1) * 100, 2)
    check(lt["quarter"] == "Q2 2026" and lt["total"] == 0.52 and lt["gdp_growth"] == g
          and lt["share_pct"] == round(100 * 0.52 / g),
          f"Q2 2026: 0.19 + 0.33 = +0.52 pp of {g}% annualized growth, "
          f"{lt['share_pct']}% of it")
    q1 = f["rows"][2]
    check(q1["gdp_growth"] == 0.0 and q1["share_pct"] is None,
          "flat growth: the share is left blank, never a division by zero")
    check(f["avg_total"] == round(statistics.fmean(a + b for a, b in zip(eq, sw)), 2),
          f"the four quarters' average contribution ({f['avg_total']})")
    check("added +0.52 pp to real GDP growth in Q2 2026" in sub["lines"][0]
          and len(sub["table"]["rows"]) == 4 and no_iso(blk._prose(sub, CUT)),
          "printed under Factor I: the table and one line")
    with observations.ObservationStore(store([])) as st:
        none = batch5b.factor_i(st, CUT, CFG)
    check(none["absent"] and "BEA's software contribution" in none["reason"]
          and "fred." not in none["reason"],
          f"absent by plain name ({none['reason'][:70]})")


# ---------------------------------------------------------------------------
def _tlt_rows(n: int, last_on: float = 0.0, last_k: int = 20) -> list[tuple]:
    """TLT closes and opens: a small alternating overnight and session drift; the
    last `last_k` sessions open `last_on` percent below the prior close."""
    days = weekdays_back("2026-10-09", n)
    rows, close = [], 100.0
    for i, d in enumerate(days):
        on = (0.05 if i % 2 else -0.05) + (0.03 if i % 3 == 0 else -0.02)
        if i >= n - last_k:
            on = last_on
        op = close * math.exp(on / 100)
        cl = op * math.exp((0.04 if i % 5 else -0.12) / 100)
        rows += [("yfinance.mkt_tlt", d, cl), ("yfinance.mkt_tlt_open", d, op)]
        close = cl
    return rows


def group_e() -> None:
    head("E. ST-R4.27a  OVERNIGHT VS SESSION")
    from altdata import basis_proxy as bp
    from daily_cascade import batch5b_block as blk
    with observations.ObservationStore(store(_tlt_rows(60, -0.4))) as st:
        cl = dict(batch5b._pts(st, "yfinance.mkt_tlt", CUT))
        op = dict(batch5b._pts(st, "yfinance.mkt_tlt_open", CUT))
        o = batch5b.overnight(st, CUT, CFG)
        sub = blk.positioning_subsection(st, CUT, CFG)
    lg = batch5b.legs(cl, op)
    check(len(lg) == 59 and max(abs(x["overnight"] + x["session"] - x["change"])
                                for x in lg) < 1e-9,
          "the two legs sum to the daily change on every session (59 of 59)")
    t = o["rows"][0]
    want_on = round(sum(x["overnight"] for x in lg[-20:]), 2)
    check(t["sessions"] == 20 and t["overnight"] == want_on == -8.0
          and abs(t["overnight"] + t["session"] - t["total"]) < 0.011
          and t["carried_by"] == "overnight" and t["yields"] == "up",
          f"20 sessions: overnight {t['overnight']}%, session {t['session']}%, "
          f"together {t['total']}%; the overnight leg carried a rising-yield move")
    z = o["rows"][1]
    check(z.get("absent") and "ZN=F not stored" in z["reason"]
          and "18:00 ET" in (o.get("zn_note") or ""),
          "ZN=F absent by name; its reopen caveat is carried into the note")
    check(any("overnight leg carried it" in x for x in sub["lines"])
          and any("Asia-hours split waits for intraday data" in x for x in sub["lines"])
          and any("Co-signal, not a flag" in x for x in sub["lines"])
          and no_iso(sub),
          "Positioning prints the split, the co-signal line and the deferred Asia split")
    # The co-signal: five years of quiet, then 20 sessions opening 0.4% lower.
    with observations.ObservationStore(store(_tlt_rows(1300, -0.4))) as st:
        co = batch5b.cosignal(st, "2026-10-09", CUT)
        sig = bp.cosignals(st, "2026-10-09", CUT, bp.load_config())
    with observations.ObservationStore(store(_tlt_rows(1300, 0.0))) as st:
        quiet = batch5b.cosignal(st, "2026-10-09", CUT)
    check(co["state"] is True and co["z"] <= -2.0 and quiet["state"] is False,
          f"on at -2 sigma ({co.get('z')}), off when the overnight leg is quiet "
          f"({quiet.get('z')})")
    check(sig.get("overnight", {}).get("state") is True and len(sig) == 5
          and bp.NAMES["overnight"] == "TLT's overnight leg",
          "SR-36's unwind watch carries it as its fifth co-signal, by name")
    orig = bp.cosignals
    try:
        def fake(states):
            return lambda *a, **k: {k2: {"state": v, "why": ""} for k2, v in zip(
                ("sr35", "move", "funding", "swap_spread", "overnight"), states)}
        bp.cosignals = fake([None, False, None, None, True])
        alone = bp.unwind_watch(None, "2026-10-09", CUT, bp.load_config(), True)
        bp.cosignals = fake([None, True, None, None, True])
        two = bp.unwind_watch(None, "2026-10-09", CUT, bp.load_config(), True)
    finally:
        bp.cosignals = orig
    check(not alone["on"] and two["on"] and two["cosignals_on"] == ["move", "overnight"],
          "the watch's rule is unchanged: the overnight leg alone is not enough; with "
          "the MOVE and a level flag it is ON")


# ---------------------------------------------------------------------------
def group_f() -> None:
    head("F. THE PRINT AND THE REGISTRY")
    ws = (REPO / "daily_cascade" / "weekly_stack.py").read_text(encoding="utf-8")
    ms = (REPO / "monthly_macro" / "stack.py").read_text(encoding="utf-8")
    check("batch5b_block.mechanics_subsections(st, cutoff)" in ws
          and "batch5b_block.read_items(st, cutoff)" in ws
          and "batch5b_block.positioning_subsection(st, now)" in ws,
          "the Weekly: Mechanics (18, 19 and the read's line) and Positioning (27)")
    check("batch5b_block.mechanics_subsections(st, now)" in ms
          and __import__('daily_cascade.stack_hooks').stack_hooks.wired("monthly", "slow", "daily_cascade.batch5b_block", "slow_subsections", ["st", "now"]),
          "the Monthly: Mechanics, and the slow layers (22); Positioning through "
          "the Weekly's builder")
    from altdata import config as acfg
    from altdata.sources import yfinance_source as yf
    want = {"fred.contrib_info_equipment": "percent_return",
            "fred.contrib_software": "percent_return",
            "yfinance.mkt_dspx": "vol_index", "yfinance.mkt_cor1m": "index_points",
            "yfinance.mkt_cor3m": "index_points", "yfinance.mkt_zn_front": "price",
            "yfinance.mkt_tlt_open": "price", "yfinance.mkt_zn_front_open": "price"}
    got = {k: derived.registry_entry(k).get("units") for k in want}
    check(got == want, f"every new key registered with its units ({got})")
    check(derived.delta_unit_for("fred.contrib_software")[0] == "pp"
          and derived.delta_unit_for("yfinance.mkt_dspx")[0] == "pts",
          "the contributions move in pp, DSPX in points")
    specs = {s.key: s for s in acfg.FRED_SIGNAL_SERIES}
    check(specs["contrib_info_equipment"].fred_id == "Y034RY2Q224SBEA"
          and specs["contrib_software"].fred_id == "B985RY2Q224SBEA"
          and specs["contrib_software"].freq == "quarterly",
          "22b extends the FRED writer: two quarterly series in FRED_SIGNAL_SERIES")
    check({"^DSPX", "^COR1M", "^COR3M", "ZN=F"} <= set(yf.SYMBOLS)
          and {"TLT", "ZN=F"} <= yf.OHLC_SYMBOLS and yf.VOLUME_UNITS.get("ZN=F") == "count",
          "the basket carries the three Cboe indices and ZN=F; TLT and ZN=F store OHLC")
    cat = (REPO / "config" / "catalogue_commands.yaml").read_text(encoding="utf-8")
    check("altdata.batch5b:" in cat, "the catalogue names the new command")
    mf = __import__("gate_list").makefile_text(REPO)
    check("tools/validate_st_r4_t1b.py" in mf, "this gate is in the Makefile")
    from daily_cascade import batch5b_block as blk
    with observations.ObservationStore(store([])) as st:
        subs = (blk.mechanics_subsections(st, CUT) + blk.slow_subsections(st, CUT)
                + [blk.positioning_subsection(st, CUT)])
    body = json.dumps([{k: v for k, v in x.items() if k != "data"} for x in subs if x],
                      ensure_ascii=False)
    ids = re.findall(r"\b(?:fred|calc|cftc|pm|dial|ndl|yfinance|manual|fixture|cboe)"
                     r"\.[a-z0-9_]+\b", body)
    check(len(subs) == 5 and not ids and all(no_iso(x) for x in subs if x),
          f"on an empty store all five print, no internal id and no ISO date outside "
          f"a table ({ids[:3]})")
    src = ((REPO / "altdata" / "batch5b.py").read_text(encoding="utf-8")
           + (REPO / "daily_cascade" / "batch5b_block.py").read_text(encoding="utf-8"))
    check("http" not in src.replace("https://", "") and "import_yfinance" not in src
          and "altdata.sources" not in src and "urllib" not in src,
          "neither module can fetch: the reads are the store's (22b is FRED's, the "
          "Cboe history altdata/sources/cboe_indices.py's)")


COR_CSV = ("DATE,OPEN,HIGH,LOW,CLOSE\n01/03/2006,23.5,23.5,23.5,23.5\n"
           "10/08/2026,6.81,13.51,6.81,10.07\n10/09/2026,,,,\n")
DSPX_CSV = "﻿DATE,DSPX\n06/19/2014,17.81\n10/09/2026,37.04\n"
LM = {"last-modified": "Fri, 09 Oct 2026 21:31:02 GMT"}


def group_g() -> None:
    head("G. THE CBOE HISTORY READER (COR1M, COR3M, DSPX)")
    from altdata import feeds
    from altdata.sources import cboe_indices as cb
    r = cb.rows_from_csv(COR_CSV, "COR1M", "2026-10-09T21:31:02+00:00", "observed")
    check([(x["observed_at"], x["value"]) for x in r]
          == [("2006-01-03", 23.5), ("2026-10-08", 10.07)]
          and {x["registry_key"] for x in r} == {"cboe.cor1m"},
          "COR1M: the CLOSE by name (10.07, not the open's 6.81), the blank row "
          "skipped, never zero")
    d = cb.rows_from_csv(DSPX_CSV, "DSPX", "2026-10-09T21:31:02+00:00", "observed")
    check([x["value"] for x in d] == [17.81, 37.04] and d[0]["observed_at"] == "2014-06-19",
          "DSPX: its one value column, a byte-order mark tolerated")
    try:
        cb.rows_from_csv("DATE,OPEN\n01/03/2006,1\n", "COR3M", "x", "observed")
        check(False, "a file without its CLOSE column is refused")
    except ValueError:
        check(True, "a file without its CLOSE column is refused: a changed shape is "
                    "a failure, not a quiet day")
    fetched, robots = [], []

    def http(url, **kw):
        fetched.append(url)
        return (DSPX_CSV if "DSPX" in url else COR_CSV).encode("utf-8"), LM

    def robots_refuse(u):
        robots.append(u)
        return "User-agent: *\nDisallow: /api/\n"

    def robots_403(u):
        robots.append(u)
        return ""

    saved = (cb.http_get_response, cb._robots_text)
    db = observations.ObservationStore(str(Path(gate_tmp.mkdtemp("st_r4b_cb_")) / "o.db"))
    try:
        cb.http_get_response = http
        cb._robots_text = robots_refuse
        r0 = cb.pull(db=db)
        check(r0.get("status") != "OK" and not fetched and "robots" in str(r0.get("reason"))
              and len(robots) == 1,
              f"a robots.txt refusal fetches no file and writes nothing "
              f"({str(r0.get('reason'))[:70]})")
        robots.clear()
        cb._robots_text = robots_403
        r1 = cb.pull(db=db)
        got = {(k, str(x["observed_at"])[:10]): x["value_num"]
               for k in cb.KEYS for x in db.as_of(k, "2026-10-10T00:00:00+00:00")}
        check(r1.get("written", 0) == 6 and len(fetched) == 3 and len(robots) == 2
              and got.get(("cboe.cor3m", "2006-01-03")) == 23.5
              and got.get(("cboe.dspx", "2026-10-09")) == 37.04,
              f"robots.txt on both hosts, unavailable read as no rules: three files "
              f"fetched, six rows written ({r1.get('written')}, {len(fetched)}, "
              f"{len(robots)})")
        early = [x for k in cb.KEYS for x in db.as_of(k, "2026-10-09T21:00:00+00:00")]
        check(not early, "the whole history carries the file's Last-Modified: an as-of "
                         "read before it sees nothing")
    finally:
        cb.http_get_response, cb._robots_text = saved
        db.close()
    check("cboe_indices" in feeds.EXTERNAL_WRITERS
          and feeds.static_keys("cboe_indices") == cb.KEYS
          and not hasattr(cb, "HELD_FOR_D1C"),
          "not held (the D1c ruling); on the external roster, its KEYS read from source")
    got = {k: derived.registry_entry(k).get("units") for k in cb.KEYS}
    check(got == {"cboe.cor1m": "index_points", "cboe.cor3m": "index_points",
                  "cboe.dspx": "vol_index"},
          f"the three keys registered with their units ({got})")
    reg = yaml.safe_load((REPO / "source_registry.yaml").read_text(encoding="utf-8"))
    ent = reg["sources"].get("cboe_indices") or {}
    check(ent.get("status") == "live"
          and ent.get("implemented_by") == "altdata/sources/cboe_indices.py",
          "source_registry: live, implemented_by the module")
    from daily_cascade import batch5b_block as blk
    days = weekdays_back("2026-10-09", 300)
    yrows = [("yfinance.mkt_dspx", x, 1.0 + i) for i, x in enumerate(days[-20:])]
    crows = [("cboe.dspx", x, 1.0 + i) for i, x in enumerate(days)]
    with observations.ObservationStore(store(yrows + crows)) as st:
        both = batch5b.dispersion(st, CUT, CFG)
        sub_b = blk.dispersion_subsection(st, CUT, CFG)
    with observations.ObservationStore(store(yrows)) as st:
        fb = batch5b.dispersion(st, CUT, CFG)
        sub_f = blk.dispersion_subsection(st, CUT, CFG)
    b, f = both["rows"]["dspx"], fb["rows"]["dspx"]
    check(b["source"] == "Cboe" and b["n_total"] == 300 and f["source"] == "Yahoo"
          and f["n_total"] == 20,
          "Cboe's key first (300 sessions), Yahoo's the fallback (20), never spliced")
    check(not any("From Yahoo" in x for x in sub_b["lines"])
          and any("From Yahoo's pull" in x and "Dispersion Index" in x
                  for x in sub_f["lines"]),
          "the panel says when it reads Yahoo's fallback, and only then")


def main() -> int:
    group_a()
    group_b()
    group_c()
    group_d()
    group_e()
    group_f()
    group_g()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
