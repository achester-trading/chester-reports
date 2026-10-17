"""
Validation gate for AQ-8a: the gold residual, the driver attribution, the
two-bid decomposition's first parts and the yields-up/dollar-down series (change
order "Alternative Assets Quarterly", 10 Oct 2026, section 5).

SEEDED, never sampled: every store and chain directory here is a throwaway,
written by this gate with returns whose betas are known by construction, so the
verdict is about the commit and is the same in CI, on the laptop and on the box.
Nothing here opens the live store.

  A  SHAPES. Every calc.gold_residual.* and calc.yields_up_dollar_down.* entry
     is calculated, a narrow flag at most, never trigger-eligible, dated, with
     the lenses' long window pending; the yields-up/dollar-down description
     carries both papers' names; the driver blocks hold exactly the members the
     universe implies and carry section 5's kill condition; the paper-bid blocks
     hold the four symbols, the OI block its twelve-month kill condition; the
     official leg reads the IMF IFS writer's aggregate net purchases (post-Friday
     fix 2, 16 Oct 2026), the earlier imf.ifs_official_gold_oz is superseded by
     it and nothing writes that name; the four are in the
     chain universe and in no exposure or pin stage; the hooks are named.
  B  THE REGRESSIONS RECOVER KNOWN BETAS. Gold built from a real-yield and a
     dollar factor with betas -0.08 and -1.0 gives those back; the residual is
     the return less the window's own fit; the driver attribution's loadings and
     explained share match an independent least squares on the same months,
     with the surprises aligned to the month they printed in.
  C  THE KILL CONDITION'S CHECK. A family with fixed loadings is sign-stable on
     every factor; one whose dollar loading flips with the real-rate regime is
     not, on the dollar; a split too short to test writes no sign row and the
     state reads "untestable".
  D  FLAGS OFF BELOW THE WINDOW. 35 monthly returns write no gold row and 36
     write one; under 60 no driver row; recurrence waits for 13 weeks and
     persistence for the run's start; an incomplete month or week is not read.
  E  AS-OF NEVER LATER THAN THE CUTOFF. Every row computed at a cutoff is
     available and observed at or before it.
  F  POINT IN TIME. A revision knowable only after the cutoff changes nothing;
     stored values recompute to the same number from only the rows knowable at
     their own available_at; a late input (the dollar, a week behind) makes a
     late row; a re-run writes nothing.
  G  YIELDS-UP/DOLLAR-DOWN. The flag, the two moves, recurrence and persistence
     match a hand count; the Weekly's line prints only when a flagged week
     became known in its window, only at the weekly cadence, and never in the
     Monthly's Plumbing.
  H  THE PAPER BID. Net call-put OI and the 30-day 25-delta risk reversal from a
     seeded chain match by hand; available_at is the capture's fetched_at; a
     re-run writes nothing; the two-bid state waits, naming the leg, below
     twelve months, and reads fragile rally / durable base by the declared rule
     once both legs hold them.
  I  THE KILL STATE IS PRINTED FOR EVERY SERIES, and where it prints: the
     metals block carries the residual and the two-bid legs in the triple form
     ("until the lenses") with the state line; the driver table sits in the
     slow layers before the families; no chart is added.

    python tools/validate_attribution.py
"""

from __future__ import annotations

import ast
import copy
import csv
import datetime as dt
import math
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

import numpy as np  # noqa: E402
import yaml  # noqa: E402

from altdata import attribution as A, config, observations, paper_bid as P  # noqa: E402
from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = 0
FAIL = 0
LINE = "=" * 78
TD = Path(gate_mkdtemp("attribution_gate_"))


def ok(m: str) -> None:
    global PASS
    PASS += 1
    print(f"  PASS  {m}")


def bad(m: str) -> None:
    global FAIL
    FAIL += 1
    print(f"  FAIL  {m}")


def check(c: bool, m: str) -> None:
    ok(m) if c else bad(m)


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


# ---------------------------------------------------------------------------
# Seeding
# ---------------------------------------------------------------------------
_N = 0


def store() -> observations.ObservationStore:
    global _N
    _N += 1
    return observations.ObservationStore(str(TD / f"s{_N}.db"))


def avail(day: str, lag_days: int = 0) -> str:
    d = dt.date.fromisoformat(day) + dt.timedelta(days=lag_days)
    return f"{d.isoformat()}T21:00:00+00:00"


def put(st, key: str, pts, lag: int = 0, kind: str = "observed") -> None:
    st.write_many([{"registry_key": key, "instrument": None, "observed_at": d,
                    "available_at": avail(d, lag), "value": float(v),
                    "source": "synthetic", "availability_kind": kind}
                   for d, v in pts])


def months(start: str, n: int) -> list[str]:
    return [A.add_months(start, i) for i in range(n)]


def month_ends(ms: list[str]) -> list[str]:
    return [A.month_last_day(m) for m in ms]


def levels(start: float, steps, log: bool) -> list[float]:
    out, v = [], start
    for s in steps:
        v = v * math.exp(s) if log else v + s
        out.append(v)
    return out


def factor_world(n: int, seed: int = 7, start: str = "2010-01"):
    """n months of the four factors, as the store holds them: real yield and
    dollar levels on month-ends; each surprise on the 1st of its REFERENCE month,
    which the attribution moves one month forward."""
    rnd = random.Random(seed)
    ms = months(start, n)
    dr = [rnd.gauss(0, 0.20) for _ in ms]
    du = [rnd.gauss(0, 0.02) for _ in ms]
    gs = [rnd.gauss(0, 100.0) for _ in ms]
    inf = [rnd.gauss(0, 0.30) for _ in ms]
    cpi = levels(250.0, [0.002 + 0.002 * math.sin(i / 9.0) for i in range(n + 1)], True)
    return {"months": ms, "dr": dr, "du": du, "gs": gs, "inf": inf, "cpi": cpi}


def seed_factors(st, w: dict, dollar_lag: int = 0) -> None:
    ms = w["months"]
    put(st, "fred.tips_10y", zip(month_ends(ms), levels(1.0, w["dr"], False)))
    put(st, "fred.dxy", zip(month_ends(ms), levels(100.0, w["du"], True)), lag=dollar_lag)
    # The surprise for month t was printed in t and describes t - 1.
    ref = [A.add_months(m, -1) + "-01" for m in ms]
    put(st, "calc.surprise_vs_naive.nfp", zip(ref, w["gs"]))
    put(st, "calc.surprise_vs_naive.core_cpi", zip(ref, w["inf"]))
    put(st, "fred.core_cpi", zip([A.add_months(ms[0], i - 1) + "-01"
                                  for i in range(len(w["cpi"]))], w["cpi"]))


def family_returns(w: dict, betas, noise: float, seed: int, flip_dollar=False):
    rnd = random.Random(seed)
    rl = levels(1.0, w["dr"], False)
    out = []
    for i in range(len(w["months"])):
        b = list(betas)
        if flip_dollar:
            up = i >= 12 and rl[i] - rl[i - 12] > 0
            b[1] = abs(b[1]) if up else -abs(b[1])
        out.append(b[0] * w["dr"][i] + b[1] * w["du"][i] + b[2] * w["gs"][i]
                   + b[3] * w["inf"][i] + rnd.gauss(0, noise))
    return out


def gate_cfg(fams: list[dict], **da) -> dict:
    c = copy.deepcopy(A.config())
    c["driver_attribution"] = {**c["driver_attribution"], "universe": fams, **da}
    return c


NOW = "2026-10-10T12:00:00+00:00"


# ---------------------------------------------------------------------------
# A
# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A  SHAPES")
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    mets, bulk = reg["metrics"], reg["bulk_imports"]
    keys = list(A.GOLD_KEYS.values()) + list(A.YUDD_KEYS.values())
    for k in keys:
        m = mets.get(k) or {}
        good = (m.get("observation_type") == "calculated"
                and m.get("rights_ceiling") == "narrow_flag"
                and m.get("trigger_eligible") is False
                and m.get("added_date") == "2026-10-10"
                and m.get("long_window") == "until_the_lenses"
                and m.get("source") == "derived_state")
        check(good, f"{k}: calculated, narrow flag, not trigger-eligible, dated, "
                    f"long window until the lenses")
    d = " ".join(str((mets.get(k) or {}).get("description")) for k in A.YUDD_KEYS.values())
    check(all(("yields-up/dollar-down" in str(mets[k].get("description"))
               and "credibility" in str(mets[k].get("description")))
              for k in A.YUDD_KEYS.values()),
          "every yields-up/dollar-down entry carries both papers' names (Currencies "
          "section 19; Rates S10/S29 'credibility repricing')")
    check("section 5 rules no kill condition" in
          " ".join(str(mets[A.GOLD_KEYS["residual"]].get("description")).split()).lower()
          and "no kill condition" in d.lower(),
          "the gold residual and the flag say no kill condition is ruled")
    da = {b: bulk.get(b) or {} for b in ("driver_attribution_explained",
                                         "driver_attribution_residual",
                                         "driver_attribution_loadings",
                                         "driver_attribution_sign_stability")}
    check(all(v.get("members_are") == "keys" and "stable sign" in str(v.get("kill_condition"))
              and v.get("rights_ceiling") == "narrow_flag" and v.get("trigger_eligible") is False
              for v in da.values()),
          "the four driver blocks: keyed members, section 5's kill condition, narrow "
          "flag, never trigger-eligible")
    check(all("expected_members" not in v for v in da.values()),
          "the driver blocks carry no second count of the correlation universe")
    fams = [{"id": "gold", "label": "Gold", "key": "t.gold"},
            {"id": "em", "label": "EM", "key": "t.em"},
            {"id": "china", "label": "China", "absent": "no feed"}]
    ex, rs, ld, sg = A._series_registry(gate_cfg(fams))
    nf = len(A.driver_factors())
    check(len(ex) == 2 and len(rs) == 2 and len(ld) == 2 * nf and len(sg) == 2 * nf,
          f"the members are the universe's keyed families x the {nf} factors (an "
          f"absent family is not a member)")
    check(set(ld) == {A.loading_key(f, x) for f in ("gold", "em")
                      for x in A.driver_factors()}, "loading keys calc.driver_attribution.<family>.loading.<factor>")
    corr = REPO / "config" / "correlation.yaml"
    if corr.exists():
        u = [a for a in yaml.safe_load(corr.read_text(encoding="utf-8"))["universe"]
             if a.get("key")]
        check(len(A.DRIVER_EXPLAINED) == len(u),
              f"with the correlation layer present, one family per keyed member ({len(u)})")
    else:
        check(A.DRIVER_EXPLAINED == {} and A.universe()[2],
              "without config/correlation.yaml the blocks are empty and the reason is named")
    pb = {b: bulk.get(b) or {} for b in ("paper_bid_call_put_oi", "paper_bid_risk_reversal")}
    check(all(v.get("expected_members") == 4 for v in pb.values())
          and set(P.PAPER_OI_SERIES) == {f"calc.paper_bid.{s}.net_call_put_oi"
                                         for s in ("gld", "slv", "ibit", "uso")},
          "the paper-bid blocks hold GLD, SLV, IBIT and USO")
    check("twelve months" in str(pb["paper_bid_call_put_oi"].get("kill_condition"))
          and pb["paper_bid_call_put_oi"].get("added_date") == "2026-10-10",
          "call-put OI carries section 5's twelve-month kill condition, added today")
    imf = mets.get("imf.ifs_official_gold_oz") or {}
    src = yaml.safe_load((REPO / "source_registry.yaml").read_text(encoding="utf-8"))["sources"]
    off = (P.cfg().get("official") or {})
    # Post-Friday fix 2 (16 Oct 2026): the official leg reads the IMF IFS
    # writer's aggregate; the placeholder name is superseded by it.
    check(off.get("key") == "imf.ifs.gold_net_purchases_oz.total"
          and off.get("kind") == "flow"
          and off.get("count_key") == "imf.ifs.gold_net_purchases_count.total"
          and "imf.ifs.gold_net_purchases_oz.total" in mets
          and not off.get("not_yet_sourced")
          and (src.get("imf_ifs") or {}).get("status") == "live",
          "the two-bid official leg reads the IMF IFS writer's aggregate net "
          "purchases (a flow, with its country count), a live source")
    check(imf.get("status_extra") == "superseded"
          and imf.get("superseded_by") == "imf.ifs.gold_net_purchases_oz.total",
          "imf.ifs_official_gold_oz is superseded by the writer's aggregate")
    writers = [p for p in (REPO / "altdata").rglob("*.py")
               if "imf.ifs_official_gold_oz" in p.read_text(encoding="utf-8")
               and "registry_key" in p.read_text(encoding="utf-8")
               .split("imf.ifs_official_gold_oz")[0][-400:]]
    check(not writers, "nothing writes imf.ifs_official_gold_oz")
    check(config.PAPER_BID_SYMBOLS == ["GLD", "SLV", "IBIT", "USO"]
          and all(s in config.chain_universe() for s in config.PAPER_BID_SYMBOLS)
          and not any(s in config.options_universe() for s in config.PAPER_BID_SYMBOLS),
          "the four are in the chain universe and not in options_universe (no "
          "exposure profile, pin log or dealer table)")
    src_eod = (REPO / "run_eod.py").read_text(encoding="utf-8")
    check("universe + paper_universe" in src_eod and "paper_bid.record_session" in src_eod
          and "exposure_compute.run(symbols=universe" in src_eod
          and "pin_log.run(symbols=universe" in src_eod,
          "run_eod captures the four and records the paper bid; stages 2 and 3 "
          "stay on the 13")
    cron = (REPO / "scripts" / "run_eod_cron.sh").read_text(encoding="utf-8")
    check(cron.index("altdata.attribution compute") > cron.index("run_eod.py --close-source"),
          "the EOD wrapper computes the attribution after the chains")
    tree = ast.parse((REPO / "altdata" / "attribution.py").read_text(encoding="utf-8"))
    fns = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    check("quadrant_factors" in fns and "supply_proxy" in fns
          and isinstance(fns["quadrant_factors"].body[-1], ast.Return)
          and getattr(fns["quadrant_factors"].body[-1].value, "value", 1) is None,
          "the two hooks are named: the surprise quadrant (returns None until item "
          "25) and the per-family supply proxy")
    check(A.config()["driver_attribution"].get("supply_proxy") == {},
          "the supply-proxy hook is empty for every family in v1")


# ---------------------------------------------------------------------------
# B
# ---------------------------------------------------------------------------
def gold_world(st, n_days_end: dt.date = dt.date(2026, 9, 30), seed: int = 3,
               start: dt.date = dt.date(2012, 1, 2), dollar_lag: int = 0):
    rnd = random.Random(seed)
    d, ry, usd, g = start, 1.0, 100.0, 1500.0
    R, U, G = [], [], []
    while d <= n_days_end:
        if d.weekday() < 5:
            dr, du, e = rnd.gauss(0, 0.03), rnd.gauss(0, 0.003), rnd.gauss(0, 0.001)
            ry += dr
            usd *= math.exp(du)
            g *= math.exp(-0.08 * dr - 1.0 * du + e)
            R.append((d.isoformat(), ry))
            U.append((d.isoformat(), usd))
            G.append((d.isoformat(), g))
        d += dt.timedelta(days=1)
    put(st, "fred.tips_10y", R)
    put(st, "fred.dxy", U, lag=dollar_lag)
    put(st, "yfinance.mkt_gold_front", G)
    return R, U, G


def stored(st, key: str, now: str = NOW) -> dict[str, tuple[float, str]]:
    return {str(r["observed_at"])[:10]: (float(r["value_num"]), str(r["available_at"]))
            for r in st.as_of(key, now) if r.get("value_num") is not None}


def group_b() -> None:
    head("B  THE REGRESSIONS RECOVER KNOWN BETAS")
    st = store()
    R, U, G = gold_world(st)
    r = A.compute(as_of=NOW, store=st, backfill=True)
    check(r["written"] > 0, f"the backfill writes ({r['written']} rows)")
    br = stored(st, A.GOLD_KEYS["beta_real_yield"])
    bd = stored(st, A.GOLD_KEYS["beta_dollar"])
    last = max(br)
    check(abs(br[last][0] + 0.08) < 0.012, f"gold's beta to the real yield recovers "
          f"-0.08 ({br[last][0]:+.4f})")
    check(abs(bd[last][0] + 1.0) < 0.12, f"gold's beta to the dollar recovers -1.0 "
          f"({bd[last][0]:+.3f})")
    # Independent: month-end closes, log returns, lstsq over the 36 ending `last`.
    def me(pts):
        by = {}
        for d, v in pts:
            by[d[:7]] = v
        return by
    mg, mr, mu = me(G), me(R), me(U)
    ms = [A.add_months(last[:7], -i) for i in range(35, -1, -1)]
    y = np.array([math.log(mg[m] / mg[A.add_months(m, -1)]) for m in ms])
    X = np.array([[mr[m] - mr[A.add_months(m, -1)],
                   math.log(mu[m] / mu[A.add_months(m, -1)])] for m in ms])
    Aa = np.column_stack([np.ones(len(ms)), X])
    coef, *_ = np.linalg.lstsq(Aa, y, rcond=None)
    res = y - Aa @ coef
    r2 = 1 - (res ** 2).sum() / ((y - y.mean()) ** 2).sum()
    check(abs(stored(st, A.GOLD_KEYS["residual"])[last][0] - 100 * res[-1]) < 1e-5,
          "the residual is the month's return less the window's own fit (x100)")
    check(abs(stored(st, A.GOLD_KEYS["explained_share"])[last][0] - r2) < 1e-6
          and abs(br[last][0] - coef[1]) < 1e-6,
          f"explained share and betas match an independent least squares "
          f"(R2 {r2:.3f})")
    # The fallback: GLD where the front has no return for the month -- here the
    # front stops in mid-2020 and GLD (at a tenth of the price) carries on.
    st2 = store()
    _, _, G2 = gold_world(st2, n_days_end=dt.date(2016, 12, 31))
    front = [(d, v) for d, v in G2 if d < "2015-07-01"]
    st3 = store()
    put(st3, "yfinance.mkt_gold_front", front)
    put(st3, "yfinance.mkt_gld", [(d, v / 10) for d, v in G2])
    y2, src = A.gold_returns(A.Inputs(st3, NOW), A.config())
    gy, _ = A.gold_returns(A.Inputs(st2, NOW), A.config())
    check(src.get("2015-06") == "yfinance.mkt_gold_front"
          and src.get("2016-06") == "yfinance.mkt_gld"
          and abs(y2["2016-06"][0] - gy["2016-06"][0]) < 1e-12
          and "2015-07" in y2,
          "a month the front cannot return is read from GLD, each return within one "
          "series (no jump at the switch)")

    # Driver attribution.
    st = store()
    w = factor_world(200)
    seed_factors(st, w)
    betas = (-0.05, -0.8, 0.0001, -0.02)
    ra = family_returns(w, betas, 0.005, 11)
    put(st, "t.famA", zip(month_ends(w["months"]), levels(100.0, ra, True)))
    cfg = gate_cfg([{"id": "fa", "label": "Family A", "key": "t.famA"}])
    rows = A.compute_rows(st, as_of=NOW, cfg=cfg)
    got = {(x["registry_key"], x["observed_at"]): x["value"] for x in rows}
    last = month_ends([w["months"][-1]])[0]
    ms = w["months"][-60:]
    idx = {m: i for i, m in enumerate(w["months"])}
    y = np.array([ra[idx[m]] for m in ms])
    X = np.array([[w["dr"][idx[m]], w["du"][idx[m]], w["gs"][idx[m]], w["inf"][idx[m]]]
                  for m in ms])
    Aa = np.column_stack([np.ones(60), X])
    coef, *_ = np.linalg.lstsq(Aa, y, rcond=None)
    std = coef[1:] * X.std(axis=0) / y.std()
    loads = [got.get((A.loading_key("fa", f), last)) for f in A.driver_factors()]
    check(all(v is not None for v in loads) and
          max(abs(a - b) for a, b in zip(loads, std)) < 1e-6,
          "the four standardised loadings match an independent least squares, the "
          "surprises aligned to the month they printed in")
    check(all(abs(c - b) / abs(b) < 0.25 for c, b in zip(coef[1:], betas)),
          "and the raw betas recover the seeded ones")
    res = y - Aa @ coef
    r2 = 1 - (res ** 2).sum() / ((y - y.mean()) ** 2).sum()
    check(abs(got[(A.driver_key("fa", "explained_share"), last)] - r2) < 1e-6
          and abs(got[(A.driver_key("fa", "residual"), last)] - 100 * res[-1]) < 1e-5,
          f"explained share ({r2:.2f}) and residual likewise")
    # Misaligned (no lag) would not match: the lag is doing work.
    cfg2 = copy.deepcopy(cfg)
    for f in ("growth_surprise", "inflation_surprise"):
        cfg2["factors"][f]["release_lag_months"] = 0
    got2 = {(x["registry_key"], x["observed_at"]): x["value"]
            for x in A.compute_rows(st, as_of=NOW, cfg=cfg2)}
    check(abs((got2.get((A.driver_key("fa", "explained_share"), last)) or 0) - r2) > 0.05,
          "without the release lag the fit is materially worse (the alignment matters)")


# ---------------------------------------------------------------------------
# C
# ---------------------------------------------------------------------------
def group_c() -> None:
    head("C  THE KILL CONDITION'S CHECK (sign stability across the regime splits)")
    st = store()
    w = factor_world(200, seed=21)
    seed_factors(st, w)
    betas = (-0.05, -0.8, 0.0001, -0.02)
    ra = family_returns(w, betas, 0.004, 5)
    rb = family_returns(w, betas, 0.004, 6, flip_dollar=True)
    put(st, "t.famA", zip(month_ends(w["months"]), levels(100.0, ra, True)))
    put(st, "t.famB", zip(month_ends(w["months"]), levels(100.0, rb, True)))
    fams = [{"id": "fa", "label": "A", "key": "t.famA"},
            {"id": "fb", "label": "B", "key": "t.famB"}]
    cfg = gate_cfg(fams)
    rows = A.compute_rows(st, as_of=NOW, cfg=cfg)
    st.write_many(rows)
    last = month_ends([w["months"][-1]])[0]
    sa = {f: stored(st, A.sign_key("fa", f)).get(last) for f in A.driver_factors()}
    sb = {f: stored(st, A.sign_key("fb", f)).get(last) for f in A.driver_factors()}
    check(all(v is not None and v[0] == 1.0 for v in sa.values()),
          "fixed loadings: every factor's sign is stable")
    check(sb["dollar"] is not None and sb["dollar"][0] == 0.0,
          "a dollar loading that flips with the real-rate regime has no stable sign "
          "(the kill condition met)")
    ks = A.driver_kill_states(st, "fb", NOW, last, cfg)
    check(ks["dollar"].startswith("no stable sign") and "not acted on" in ks["dollar"],
          f"its state prints, and says it is not acted on: {ks['dollar']!r}")
    check(stored(st, A.driver_key("fb", "residual")).get(last) is not None,
          "the residual stays")
    cfg_u = gate_cfg(fams, min_months=100)
    rows_u = A.compute_rows(st, as_of=NOW, cfg=cfg_u)
    check(not any(".sign_stable." in x["registry_key"] for x in rows_u),
          "a split too short to test writes no sign row")
    st2 = store()
    st2.write_many([x for x in rows_u])
    ku = A.driver_kill_states(st2, "fa", NOW, last, cfg_u)
    check(set(ku.values()) == {"untestable"}, "and the state reads 'untestable'")


# ---------------------------------------------------------------------------
# D
# ---------------------------------------------------------------------------
def group_d() -> None:
    head("D  FLAGS OFF BELOW THE WINDOW")
    for n_ret, want in ((35, 0), (36, 1)):
        st = store()
        w = factor_world(n_ret + 1, seed=n_ret, start="2020-01")
        ms = month_ends(w["months"])
        put(st, "fred.tips_10y", zip(ms, levels(1.0, w["dr"], False)))
        put(st, "fred.dxy", zip(ms, levels(100.0, w["du"], True)))
        put(st, "yfinance.mkt_gold_front",
            zip(ms, levels(1500.0, [-0.08 * a - b + 0.01 * math.sin(i)
                                    for i, (a, b) in enumerate(zip(w["dr"], w["du"]))], True)))
        rows = [x for x in A.compute_rows(st, as_of=NOW)
                if x["registry_key"] == A.GOLD_KEYS["residual"]]
        check(len(rows) == want, f"{n_ret} monthly returns write {want} gold row(s)")
    st = store()
    w = factor_world(60, seed=2)
    seed_factors(st, w)
    put(st, "t.famA", zip(month_ends(w["months"]), levels(100.0, family_returns(
        w, (-0.05, -0.8, 0.0001, -0.02), 0.005, 1), True)))
    cfg = gate_cfg([{"id": "fa", "label": "A", "key": "t.famA"}])
    rows = A.compute_rows(st, as_of=NOW, cfg=cfg)
    check(not any(x["registry_key"].startswith(A.DRIVER) for x in rows),
          "59 monthly returns write no driver-attribution row (60 needed)")
    # An incomplete month is not read: a cutoff mid-September.
    st = store()
    gold_world(st)
    rows = A.compute_rows(st, as_of="2026-09-15T12:00:00+00:00")
    days = {x["observed_at"] for x in rows if x["registry_key"] == A.GOLD_KEYS["residual"]}
    check(max(days) == "2026-08-31", f"a mid-month cutoff reads up to the last "
          f"complete month ({max(days)})")
    s = {"2026-09-25": (1.0, "a", None), "2026-09-29": (2.0, "a", None)}
    check(A.month_closes(s) == {}, "a month whose last print is not final is not read")
    s["2026-10-01"] = (3.0, "a", None)
    check(A.month_closes(s).get("2026-09", (None,))[0] == 2.0,
          "and is read on its last print once a later one proves it final")


# ---------------------------------------------------------------------------
# E and F
# ---------------------------------------------------------------------------
def group_ef() -> None:
    head("E  AS-OF NEVER LATER THAN THE CUTOFF   /   F  POINT IN TIME")
    st = store()
    gold_world(st, dollar_lag=7)
    w = factor_world(200, seed=9, start="2010-02")
    # Weekly legs for the flag, on the same store.
    cut = "2026-06-30T12:00:00+00:00"
    rows = A.compute_rows(st, as_of=cut)
    check(rows and all(x["available_at"] <= cut for x in rows),
          f"every row computed at a cutoff is available at or before it ({len(rows)} rows)")
    check(all(x["observed_at"] <= cut[:10] for x in rows), "and observed on or before it")
    late = [x for x in rows if x["registry_key"] == A.GOLD_KEYS["residual"]]
    lr = max(late, key=lambda x: x["observed_at"])
    # May 2026 ends on a Sunday: the dollar's Friday 29 May print lands a week
    # late (5 Jun), and is proved final only by Monday 1 Jun's (8 Jun).
    check(lr["observed_at"] == "2026-05-31" and lr["available_at"][:10] == "2026-06-08",
          f"a late input makes a late row: the {lr['observed_at']} residual is "
          f"available {lr['available_at'][:10]} -- the dollar a week behind, and its "
          f"month final only once the next print is in")
    # A revision knowable only after the cutoff changes nothing.
    before = {(x["registry_key"], x["observed_at"]): x["value"] for x in rows}
    st.write_many([{"registry_key": "yfinance.mkt_gold_front", "instrument": None,
                    "observed_at": "2026-05-29", "available_at": "2026-07-15T21:00:00+00:00",
                    "value": 99999.0, "source": "synthetic", "availability_kind": "observed"}])
    after = {(x["registry_key"], x["observed_at"]): x["value"]
             for x in A.compute_rows(st, as_of=cut)}
    check(after == before, "a revision knowable only after the cutoff changes nothing")
    later = {(x["registry_key"], x["observed_at"]): x["value"]
             for x in A.compute_rows(st, as_of="2026-07-20T12:00:00+00:00")}
    check(later.get((A.GOLD_KEYS["residual"], "2026-05-31")) !=
          before.get((A.GOLD_KEYS["residual"], "2026-05-31")),
          "and the same revision moves the month once it is knowable")
    # Stored values recompute from only what was knowable at their own available_at.
    st2 = store()
    gold_world(st2, dollar_lag=7)
    A.compute(as_of=NOW, store=st2, backfill=True)
    sample = sorted(stored(st2, A.GOLD_KEYS["residual"]).items())[::40]
    good = True
    for day, (v, av) in sample:
        re = {x["observed_at"]: x["value"] for x in A.compute_rows(st2, as_of=av)
              if x["registry_key"] == A.GOLD_KEYS["residual"]}
        good &= abs(re.get(day, 1e9) - v) < 1e-9
    check(good, f"{len(sample)} stored residuals recompute to the same number from the "
                f"rows knowable at their own available_at")
    r2 = A.compute(as_of=NOW, store=st2, backfill=True)
    check(r2["written"] == 0, "a re-run of the backfill writes nothing (idempotent)")


# ---------------------------------------------------------------------------
# G
# ---------------------------------------------------------------------------
def group_g() -> None:
    head("G  YIELDS-UP/DOLLAR-DOWN")
    rnd = random.Random(4)
    st = store()
    start = dt.date(2026, 1, 5)          # a Monday
    days, y, u = [], 4.0, 100.0
    Y, U = [], []
    for i in range(7 * 30):
        d = start + dt.timedelta(days=i)
        if d.weekday() >= 5:
            continue
        y += rnd.gauss(0, 0.03)
        u *= math.exp(rnd.gauss(0, 0.003))
        Y.append((d.isoformat(), y))
        U.append((d.isoformat(), u))
    put(st, "fred.yield_10y", Y)
    put(st, "fred.dxy", U, lag=3)
    rows = A.compute_rows(st, as_of=NOW)
    by = {}
    for x in rows:
        by.setdefault(x["registry_key"], {})[x["observed_at"]] = x
    fri = {}
    for d, v in Y:
        fri.setdefault(A.week_of(d), {})["y"] = v
    for d, v in U:
        fri.setdefault(A.week_of(d), {})["u"] = v
    weeks = sorted(fri)
    exp_flag = {}
    for a, b in zip(weeks, weeks[1:]):
        dy = fri[b]["y"] - fri[a]["y"]
        du = fri[b]["u"] / fri[a]["u"] - 1
        exp_flag[b] = (1 if dy > 0 and du < 0 else 0, 100 * dy, 100 * du)
    fl = by.get(A.YUDD_KEYS["flag"], {})
    check(set(fl) == set(exp_flag) and all(fl[k]["value"] == v[0] for k, v in exp_flag.items()),
          f"the flag matches a hand count over {len(exp_flag)} weeks "
          f"({sum(v[0] for v in exp_flag.values())} flagged)")
    check(all(abs(by[A.YUDD_KEYS["yield_change_bp"]][k]["value"] - v[1]) < 1e-6
              and abs(by[A.YUDD_KEYS["dollar_change_pct"]][k]["value"] - v[2]) < 1e-6
              for k, v in exp_flag.items()), "each move is stored beside it (bp, percent)")
    ws = sorted(exp_flag)
    rec = by.get(A.YUDD_KEYS["recurrence"], {})
    check(set(rec) == set(ws[12:]) and all(
        rec[ws[i]]["value"] == sum(exp_flag[w][0] for w in ws[i - 12:i + 1])
        for i in range(12, len(ws))),
        "recurrence counts the trailing 13 and is not written before 13 weeks")
    per = by.get(A.YUDD_KEYS["persistence"], {})
    good = True
    for i, wk in enumerate(ws):
        j = i
        while j >= 0 and exp_flag[ws[j]][0] == 1:
            j -= 1
        want = None if j < 0 else i - j
        got = per.get(wk, {}).get("value")
        good &= (got is None) if want is None else (got == want)
    check(good, "persistence counts consecutive flagged weeks, off where the run's "
                "start is not in the history")
    check(all(x["available_at"] <= NOW for x in rows)
          and all(fl[k]["available_at"] == avail(max(d for d, _ in U if A.week_of(d) == k), 3)
                  or fl[k]["available_at"] >= avail(k, 0) for k in fl),
          "a week's row is available when its later leg is (the dollar, three days late)")
    st.write_many(rows)
    flagged = sorted(k for k, v in exp_flag.items() if v[0] == 1)
    wk = flagged[-1]
    av = fl[wk]["available_at"]
    then = (dt.datetime.fromisoformat(av) - dt.timedelta(days=1)).isoformat()
    now = (dt.datetime.fromisoformat(av) + dt.timedelta(days=1)).isoformat()
    line = A.yudd_week_line(st, now, then)
    check(line is not None and line["week"] == wk and "Yields up, dollar down" in line["text"],
          f"the Weekly's line prints when a flagged week became known this week: "
          f"{line['text'] if line else None!r}")
    quiet = [k for k in ws if exp_flag[k][0] == 0 and k > flagged[0]]
    qa = fl[quiet[-1]]["available_at"] if quiet else None
    if qa:
        q_now = (dt.datetime.fromisoformat(qa) + dt.timedelta(hours=1)).isoformat()
        q_then = (dt.datetime.fromisoformat(qa) - dt.timedelta(hours=1)).isoformat()
        check(A.yudd_week_line(st, q_now, q_then) is None,
              "a week that knew no flagged week prints nothing")
    from daily_cascade import weekly_stack as ws_mod             # noqa: PLC0415
    pw = ws_mod.plumbing_week(st, now, then)
    titles = [s.get("title") for s in pw.get("subsections") or []]
    check("Yields up, dollar down" in titles, "the Weekly's Plumbing carries it as one line")
    pm = ws_mod.plumbing_week(st, now, then, None, liquidity_deltas=True, yudd_line=False)
    pc = ws_mod.plumbing_week(st, now, then, None, cadence="monthly")
    check("Yields up, dollar down" not in [s.get("title") for s in pm.get("subsections") or []]
          and "Yields up, dollar down" not in [s.get("title") for s in pc.get("subsections") or []],
          "and the Monthly's Plumbing does not (it carries the series in fiscal_dollar)")
    themes = yaml.safe_load((REPO / "config" / "monthly_themes.yaml").read_text(encoding="utf-8"))
    check(any(m.get("metric") == A.YUDD_KEYS["recurrence"]
              for m in themes["themes"]["fiscal_dollar"]["metrics"]),
          "the fiscal_dollar theme carries the yields-up/dollar-down line")


# ---------------------------------------------------------------------------
# H
# ---------------------------------------------------------------------------
COLS = ["symbol", "fetched_at", "spot", "expiry", "dte", "right", "strike", "bid",
        "ask", "last_price", "volume", "open_interest", "implied_vol",
        "in_the_money", "contract_symbol", "last_trade_date"]


def write_chain(root: Path, day: str, sym: str, fetched: str, expiries, spot=100.0,
                oi_call=10.0, oi_put=4.0) -> None:
    """expiries: [(expiry, dte, call_iv, put_iv)], strikes 60..140."""
    d = root / day
    d.mkdir(parents=True, exist_ok=True)
    stamp = fetched[11:19].replace(":", "") + "Z"
    with (d / f"{sym}_{stamp}.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        for exp, dte, civ, piv in expiries:
            for k in range(60, 141):
                for right, iv, oi in (("C", civ, oi_call), ("P", piv, oi_put)):
                    w.writerow({"symbol": sym, "fetched_at": fetched, "spot": spot,
                                "expiry": exp, "dte": dte, "right": right, "strike": k,
                                "bid": 1.0, "ask": 1.1, "last_price": 1.05, "volume": 1,
                                "open_interest": oi, "implied_vol": iv,
                                "in_the_money": "", "contract_symbol": "",
                                "last_trade_date": ""})


def group_h() -> None:
    head("H  THE PAPER BID")
    root = TD / "chains"
    day = "2026-10-09"
    fetched = "2026-10-09T20:10:30+00:00"
    exps = [("2026-10-09", 0, 0.5, 0.5), ("2026-10-29", 20, 0.20, 0.25),
            ("2026-11-18", 40, 0.22, 0.24)]
    write_chain(root, day, "GLD", fetched, exps)
    rd = P.readings(day, ["GLD"], base=root)
    g = rd["symbols"]["GLD"]
    n_strikes = 81
    check(g["net_call_put_oi"]["net"] == 2 * n_strikes * (10 - 4),
          f"net call-put OI over the expiries after the session's own "
          f"({g['net_call_put_oi']['net']:+,.0f}; the 0DTE expiry excluded)")
    check(abs(g["rr_25d"]["rr"] - (-3.5)) < 1e-6 and g["rr_25d"]["method"] == "interpolated",
          f"the 30-day 25-delta risk reversal: -5.0 at 20 days, -2.0 at 40, so -3.5 "
          f"({g['rr_25d']['rr']:+.3f})")
    st = store()
    r1 = P.record_session(day, st, base=root)
    rows = {x: stored(st, x) for x in (P.oi_key("GLD"), P.rr_key("GLD"))}
    check(all(v.get(day) and v[day][1] == observations.canonical_instant(fetched)
              for v in rows.values()),
          "observed the session, available at the capture's fetched_at")
    r2 = P.record_session(day, st, base=root)
    check(r1["written"] == 2 and r2["written"] == 0, "a re-run writes nothing")
    check(rd["symbols"]["SLV"]["reason"].startswith("no chain") if "SLV" in rd["symbols"]
          else P.readings(day, ["SLV"], base=root)["symbols"]["SLV"]["reason"].startswith("no chain"),
          "a symbol with no capture says so")
    # The state.
    s = P.two_bid_state(st, NOW)
    lines = P.two_bid_lines(s)
    check(s["state"] is None and "paper" in s["waiting"] and "official" in s["waiting"]
          and "1 of 12 months" in lines[0] and "0 of 12 months" in lines[0],
          f"below twelve months the state waits and names each leg: {lines[0]!r}")
    # The official leg is the IMF IFS writer's aggregate net purchases, a flow
    # (post-Friday fix 2, 16 Oct 2026): the change over three months is their sum.
    off, cnt = P.OFFICIAL_KEY, "imf.ifs.gold_net_purchases_count.total"
    check("IMF IFS" in lines[0] and "China" not in lines[0],
          "the waiting line names the IMF IFS leg, not China's holdings")
    st = store()
    ms = months("2025-09", 13)
    # Net purchases of 1e5 oz a month, then three months of none: flat.
    put(st, off, [(m + "-28", 1e5 if i < 10 else 0.0) for i, m in enumerate(ms)])
    put(st, cnt, [(m + "-28", 25.0) for m in ms])
    put(st, "safe.gold_reserves_oz", [(m + "-07", 7.4e7 + i * 1e5) for i, m in enumerate(ms)])
    put(st, P.oi_key("GLD"), [(m + "-15", 1000.0 + 10 * i) for i, m in enumerate(ms)])
    put(st, P.rr_key("GLD"), [(m + "-15", -2.0 + 0.1 * i) for i, m in enumerate(ms)])
    s = P.two_bid_state(st, NOW)
    check(s["state"] == "fragile rally" and s["paper_reading"] == "surging"
          and s["official_reading"] == "flat"
          and s["official_change"]["change_oz"] == 0.0
          and s["official_countries"] == 25 and s["official_key"] == off,
          f"paper at its highs with three months of no net purchases reads fragile "
          f"rally, though China's holdings rose (the leg is no longer SAFE's) "
          f"({P.two_bid_lines(s)[0]!r})")
    st = store()
    put(st, off, [(m + "-28", 1e5 * (1 + i % 3)) for i, m in enumerate(ms)])
    put(st, P.oi_key("GLD"), [(m + "-15", 1000.0 - 10 * i) for i, m in enumerate(ms)])
    put(st, P.rr_key("GLD"), [(m + "-15", -2.0 - 0.1 * i) for i, m in enumerate(ms)])
    s = P.two_bid_state(st, NOW)
    check(s["state"] == "durable base" and s["official_change"]["change_oz"] == 6e5,
          "net purchases summing to +600,000 oz over three months with the paper leg "
          "at its lows reads durable base (the flow summed, by hand)")
    st = store()
    put(st, off, [(m + "-28", -2e5) for m in ms])
    put(st, P.oi_key("GLD"), [(m + "-15", 1000.0 - 10 * i) for i, m in enumerate(ms)])
    put(st, P.rr_key("GLD"), [(m + "-15", -2.0 - 0.1 * i) for i, m in enumerate(ms)])
    s = P.two_bid_state(st, NOW)
    check(s["official_reading"] == "selling" and s["state"] == "neither",
          "net sales read selling, and neither state")


# ---------------------------------------------------------------------------
# I
# ---------------------------------------------------------------------------
def group_i() -> None:
    head("I  THE KILL STATE FOR EVERY SERIES, AND WHERE IT PRINTS")
    from monthly_macro import stack                              # noqa: PLC0415
    st = store()
    gold_world(st)
    w = factor_world(200, seed=31)
    seed_factors(st, w)
    put(st, "t.famA", zip(month_ends(w["months"]), levels(100.0, family_returns(
        w, (-0.05, -0.8, 0.0001, -0.02), 0.005, 3), True)))
    fams = [{"id": "fa", "label": "Family A", "key": "t.famA"},
            {"id": "zz", "label": "Absent family", "absent": "no feed"}]
    saved = A._CFG
    A._CFG = gate_cfg(fams)
    try:
        st.write_many(A.compute_rows(st, as_of=NOW))
        metals = {"title": "Themes: metals", "family": "metals", "lines": [],
                  "not_tracked": [], "data": {}, "prose": {"words": "60 to 100", "scope": "x"}}
        stack.gold_two_bid(metals, st, NOW)
        tbl = (metals.get("tables") or [{}])[-1]
        labels = [r[0] for r in tbl.get("rows") or []]
        check(tbl.get("columns") == A.TRIPLE_COLUMNS
              and all(r[-1] == "until the lenses" for r in tbl["rows"])
              and any(lb.startswith("Gold residual") for lb in labels),
              "the metals block carries the gold residual in the triple form, the "
              "five-year column 'until the lenses'")
        check(any(ln.startswith("Two-bid state") for ln in metals["lines"]),
              f"and the two-bid state's line: {metals['lines'][-1]!r}")
        note = " ".join(metals.get("notes") or [])
        check("Kill states" in note and A.KILL_NONE in note and "kill test waits" in note
              and "risk reversal" in note,
              "the kill states print for the residual, call-put OI and the risk reversal")
        check(not any("IMF" in x for x in metals["not_tracked"])
              and any("tonnes" in x for x in metals["not_tracked"]),
              "GLD tonnage is named as not yet tracked; IMF IFS no longer is (it "
              "is the official leg)")
        blk = stack.driver_attribution_block(st, NOW)
        cols, rows = blk["table"]["columns"], blk["table"]["rows"]
        check(blk["title"] == "Driver attribution" and cols == A.DRIVER_COLUMNS
              and rows and rows[0][0] == "Family A" and rows[0][4],
              f"one driver table: family, explained share, the largest loading, the "
              f"residual's sign, the kill state ({rows[0] if rows else None})")
        check(any("Absent family" in x for x in blk["not_tracked"])
              and any("item 25" in x for x in blk["not_tracked"])
              and any("supply proxy" in x for x in blk["not_tracked"]),
              "an absent family says why; the quadrant and supply-proxy hooks are named")
    finally:
        A._CFG = saved
    if A.universe()[2]:
        blk = stack.driver_attribution_block(st, NOW)
        check(not blk["table"]["rows"] and "correlation" in blk["not_tracked"][0],
              f"with no correlation universe in the checkout the table says why: "
              f"{blk['not_tracked'][0][:70]!r}")
    check(A.yudd_kill_state() == A.KILL_NONE and A.gold_kill_state() == A.KILL_NONE,
          "the gold residual and yields-up/dollar-down print 'no kill condition ruled'")
    src = (REPO / "monthly_macro" / "stack.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    sl = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "slow_layers")
    calls = {getattr(c.func, "id", None) for c in ast.walk(sl) if isinstance(c, ast.Call)}
    check({"gold_two_bid", "driver_attribution_block"} <= calls,
          "the slow layers call both (the metals block, then one table before the families)")
    for mod in ("attribution.py", "paper_bid.py"):
        t = (REPO / "altdata" / mod).read_text(encoding="utf-8")
        check("charts" not in t and "matplotlib" not in t, f"{mod} draws no chart (the cap of 12 stands)")


def main() -> int:
    print(LINE)
    print("AQ-8a gate: gold residual, driver attribution, paper bid, yields-up/dollar-down")
    print(LINE)
    for g in (group_a, group_b, group_c, group_d, group_ef, group_g, group_h, group_i):
        try:
            g()
        except Exception as exc:                                  # noqa: BLE001
            import traceback
            traceback.print_exc()
            bad(f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{LINE}\n  {PASS} passed, {FAIL} failed\n{LINE}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
