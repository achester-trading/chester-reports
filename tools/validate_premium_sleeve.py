#!/usr/bin/env python3
"""
Validation gate for the premium sleeve, Batch 19 item 100 (B99). On a synthetic
store and a synthetic SPX chain in the gate's own temporary directory: no live
store, no chain file of the box's, no network, no model, and no backtest of the
real store.

  A  THE REGISTRATION. alpha/research/roster-2026-10-31-premium-sleeve.yaml parses
     as alpha-lab-hypotheses/v1, carries family_ref "KS options", model_idea_rule
     false, its five counted variants and its gaps (the PUT benchmark, the count),
     and quotes the spec's sha256; the engine refuses a changed spec.
  B  DISABLED BY DEFAULT. The registry entry says enabled: false; engine.active()
     leaves it out, so no loop loads it.
  C  THE ENTRY GATES. All three pass: a spread is entered. Each one alone failing
     -- VRP, IV rank, the dealer gate -- enters nothing.
  D  THE STAND-DOWNS. HY Spread Acceleration FIRES, Liquidity FIRES, an overlay
     unread, the count at surrender without a BOTTOM SIGNAL, and the count not
     stored ("count not stored") each stand down; surrender WITH a BOTTOM SIGNAL
     does not.
  E  THE EXITS. The 50% take-profit fires at the session the debit first falls to
     half the credit; the 21-DTE close at the first session 21 days or fewer from
     expiry; the entry fills at the session after the decision.
  F  THE CHAIN. A day without a snapshot trades nothing and logs "chain not
     stored"; a snapshot fetched after the read is never read.
  G  THE COSTS. Every leg fills at its executable side through the
     index_option_spread line: never the mid.
  H  THE RECORD. A closed trade in the positions table's shape, its family_ref
     beside it.

    python tools/validate_premium_sleeve.py
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import csv
import datetime as dt
import math
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

_TMP = gate_mkdtemp(prefix="validate_premium_sleeve_")
os.environ["CHESTER_DB"] = os.path.join(_TMP, "store.sqlite")
os.environ["CHESTER_CHAIN_DIR"] = os.path.join(_TMP, "chains")   # never the box's

import yaml  # noqa: E402

from altdata import observations, session  # noqa: E402
from alpha import engine as engine_mod  # noqa: E402
from alpha import hypotheses as hyp  # noqa: E402
from alpha import pit  # noqa: E402
from alpha.engines import premium_sleeve as ps  # noqa: E402

LINE = "=" * 78
PASS = FAIL = 0
ROSTER = REPO / "alpha" / "research" / "roster-2026-10-31-premium-sleeve.yaml"
START, END = "2025-03-03", "2026-06-30"       # the VIX's year before, then the test window
T0 = "2026-04-01"                              # the first test session


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


def sessions(a: str, b: str) -> list[str]:
    d, out = dt.date.fromisoformat(a), []
    while d <= dt.date.fromisoformat(b):
        if session.is_trading_session(d):
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


DAYS = sessions(START, END)
TEST = [d for d in DAYS if d >= T0]


# ---------------------------------------------------------------------------
# The fixture: a store, a chain, a scenario
# ---------------------------------------------------------------------------
def store(name: str, vix_last=28.0, rv=12.0, gex=1.0e9, spot=6000.0, flip=5900.0,
          band="none", verdict=None, count=True) -> observations.ObservationStore:
    """The gate inputs over every session: the VIX between 12 and 30 over the year
    before T0 and `vix_last` from T0 (so its rank is high or low), SPY's realised
    at `rv`, SPX's dealer rows, and the count's band (or none at all)."""
    p = os.path.join(_TMP, f"{name}.sqlite")
    st = observations.ObservationStore(p)
    rows = []
    for i, d in enumerate(DAYS):
        av = f"{d}T21:00:00+00:00"
        vix = (12.0 + 18.0 * (0.5 + 0.5 * math.sin(i / 9.0))) if d < T0 else vix_last
        for key, v, inst in (("yfinance.mkt_vix", vix, None),
                             ("calc.vol_spy_realized_20d", rv, None),
                             ("exposure.net_gex", gex, "SPX"),
                             ("exposure.gamma_flip", flip, "SPX"),
                             ("exposure.spot", spot, "SPX"),
                             ("yfinance.mkt_gspc", spot, None)):
            rows.append({"registry_key": key, "instrument": inst, "observed_at": d,
                         "available_at": av, "value": v, "source": "synthetic"})
        if count:
            rows.append({"registry_key": "capitulation.count_band", "instrument": None,
                         "observed_at": d, "available_at": av, "value": band,
                         "source": "synthetic"})
        if verdict:
            rows.append({"registry_key": "top_bottom.verdict", "instrument": None,
                         "observed_at": d, "available_at": av, "value": verdict,
                         "source": "synthetic"})
    st.write_many(rows)
    return st


def bs_put(s, k, iv, t):
    if t <= 0:
        return max(k - s, 0.0)
    d1 = (math.log(s / k) + 0.5 * iv * iv * t) / (iv * math.sqrt(t))
    d2 = d1 - iv * math.sqrt(t)
    n = lambda x: 0.5 * math.erfc(-x / math.sqrt(2.0))          # noqa: E731
    return k * n(-d2) - s * n(-d1)


def fridays(a: str, b: str) -> list[str]:
    d = dt.date.fromisoformat(a)
    out = []
    while d <= dt.date.fromisoformat(b):
        if d.weekday() == 4:
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


EXPIRIES = fridays("2026-04-01", "2026-09-30")


class Chains:
    """A synthetic SPX chain: weekly Friday expiries, strikes every 25 points,
    Black-Scholes prices at `iv` with a quoted spread either side. `spot(d)` sets
    the path; a day in `missing` has no snapshot; fetched at 20:31 UTC."""

    def __init__(self, spot=lambda d: 6000.0, iv=0.18, missing=()):
        self.spot, self.iv, self.missing = spot, iv, set(missing)

    def days(self):
        return list(TEST)

    def rows(self, d):
        s = self.spot(d)
        out = []
        for e in EXPIRIES:
            dte = (dt.date.fromisoformat(e) - dt.date.fromisoformat(d)).days
            if dte < 0 or dte > 120:
                continue
            for k in range(4000, 7001, 25):
                px = bs_put(s, float(k), self.iv, dte / 365.0)
                out.append({"expiry": e, "dte": dte, "right": "P", "strike": float(k),
                            "bid": max(0.0, round(px * 0.97 - 0.05, 2)),
                            "ask": round(px * 1.03 + 0.05, 2), "iv": self.iv, "spot": s,
                            "fetched_at": f"{d}T20:31:00+00:00"})
        return out

    def snapshot(self, day, as_of):
        if day in self.missing or pit.canon(f"{day}T20:31:00+00:00") > pit.canon(as_of):
            return None
        return self.rows(day)


def engine(chains=None, overlays=None) -> ps.PremiumSleeveEngine:
    e = ps.PremiumSleeveEngine({})
    e.chains = chains or Chains()
    ov = overlays or {"hy_accel": "CLEAR", "liquidity": "CLEAR"}
    e.overlay_reader = lambda store, day, t: ov
    return e


def run(e, st, days=None):
    return e.simulate(st, f"{END}T23:00:00+00:00", days or TEST[:30])


# ---------------------------------------------------------------------------
# The groups
# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. THE REGISTRATION: P-1, family_ref KS options, the spec's sha256")
    doc = yaml.safe_load(ROSTER.read_text(encoding="utf-8"))
    h = doc["hypotheses"][0]
    check(hyp.validate_batch(doc) == [] and hyp.budget_errors(doc) == []
          and doc["schema"] == "alpha-lab-hypotheses/v1",
          f"{ROSTER.name} parses as alpha-lab-hypotheses/v1, inside its budgets")
    check(h["family_ref"] == "KS options" and doc["model_idea_rule"] is False
          and doc["source"] == "operator" and h["engine"] == "premium_sleeve",
          "P-1 carries family_ref 'KS options', model_idea_rule false (an operator-ruled "
          "item), source operator, engine premium_sleeve")
    names = [c["name"] for c in h["conditioning"]]
    check(names == ["delta_band_low_end", "delta_band_high_end", "dte_low_bound",
                    "dte_high_bound", "take_profit_level"],
          f"five counted variants: the delta band's ends, the two DTE bounds, the take "
          f"profit ({len(names)})")
    gaps = " ".join(h["data"]["gaps"])
    check("PUT index" in gaps and "D2-74" in gaps and "count" in gaps,
          "data.gaps name the PUT benchmark (not stored, D2-74) and the count")
    cfg = ps.load_config()
    check(h["data"]["spec_sha256"] == cfg["spec_sha256"] == ps.spec_sha256(cfg),
          f"the registration quotes the spec's sha256 ({cfg['spec_sha256'][:12]}...), "
          "and the spec still hashes to it")
    bad = yaml.safe_load(yaml.safe_dump(cfg))
    bad["spec"]["take_profit_frac"] = 0.45
    try:
        ps.check_spec(bad)
        refused = False
    except ps.SpecChanged:
        refused = True
    check(refused, "the engine refuses a changed spec: a new rule is a new hypothesis")
    e = engine()
    check(e.grid_size == 6 and e.family == "KS options",
          "the engine counts 6 variants (the base and five), under the family_ref")


def group_b() -> None:
    head("B. DISABLED BY DEFAULT")
    entry = next(x for x in engine_mod.registered() if x["id"] == "premium_sleeve")
    check(entry.get("enabled") is False and entry["family"] == "KS options"
          and entry["cost_class"] == "index_option_spread",
          "config/alpha_engines.yaml registers premium_sleeve with enabled: false")
    check("premium_sleeve" not in {x["id"] for x in engine_mod.active()},
          "engine.active(), which the nightly and weekly loops load, leaves it out")


def group_c() -> None:
    head("C. THE ENTRY GATES: all three enter; each alone failing enters nothing")
    st = store("c_all")
    tr = run(engine(), st)
    check(tr and tr[0]["signal_day"] == TEST[0],
          f"all three gates hold: a spread is entered on the first session "
          f"({tr[0]['signal_day'] if tr else None})")
    for name, kw, why in (("vrp", {"rv": 40.0}, "vrp"),
                          ("iv_rank", {"vix_last": 13.0}, "iv_rank"),
                          ("dealer", {"gex": -1.0e9, "spot": 5800.0, "flip": 5900.0},
                           "dealer")):
        e = engine()
        tr = run(e, store(f"c_{name}", **kw))
        check(not tr and all(why in x["why"] for x in e.log),
              f"{name} alone failing: nothing entered, every day logs '{why}' "
              f"({e.log[0]['why'] if e.log else None})")
    e = engine()
    tr = run(e, store("c_flip", gex=-1.0e9, spot=6000.0, flip=5900.0))
    check(bool(tr), "net GEX negative but spot above the flip: the dealer gate holds")


def group_d() -> None:
    head("D. THE STAND-DOWNS")
    for label, ov, kw, want in (
            ("HY Spread Acceleration FIRES", {"hy_accel": "FIRES", "liquidity": "CLEAR"}, {},
             "hy_accel: FIRES"),
            ("Liquidity FIRES", {"hy_accel": "CLEAR", "liquidity": "FIRES"}, {},
             "liquidity: FIRES"),
            ("an overlay unread", {"hy_accel": "UNREAD", "liquidity": "CLEAR"}, {},
             "hy_accel: UNREAD"),
            ("surrender without a BOTTOM SIGNAL", None, {"band": "surrender"},
             "surrender without a BOTTOM SIGNAL"),
            ("the count not stored", None, {"count": False}, ps.COUNT_NOT_STORED)):
        e = engine(overlays=ov)
        tr = run(e, store(f"d_{len(label)}_{want[:4]}", **kw))
        check(not tr and e.log and all(want in x["why"] for x in e.log),
              f"{label}: stands down every session ({e.log[0]['why'] if e.log else None})")
    e = engine()
    tr = run(e, store("d_bottom", band="surrender", verdict="BOTTOM SIGNAL"))
    check(bool(tr), "surrender WITH a T&B BOTTOM SIGNAL: no stand-down, a spread is entered")
    e = ps.PremiumSleeveEngine({})
    e.chains = Chains()
    ov = e.overlays(store("d_default"), TEST[0], pit.decision_instant(TEST[0]))
    check(set(ov) >= {"hy_accel", "liquidity"} and all(v != "CLEAR" for k, v in ov.items()
                                                       if k in ("hy_accel", "liquidity")),
          f"the real reader (altdata/tb_harness.py) on a store without the overlays' "
          f"inputs reads them as not CLEAR, so the sleeve stands down ({ov.get('hy_accel')})")


def group_e() -> None:
    head("E. THE EXITS: entry the session after; 50% take-profit; the 21-DTE close")
    jump = TEST[6]
    ch = Chains(spot=lambda d: 6000.0 if d < jump else 6600.0)
    tr = run(engine(ch), store("e_tp"))
    t = tr[0] if tr else {}
    check(t and t["entry_day"] == TEST[1] and t["signal_day"] == TEST[0],
          f"the entry decided on {TEST[0]} fills at the next session's snapshot "
          f"({t.get('entry_day')})")
    check(t and t["exit_reason"] == "take_profit" and t["exit_day"] == jump
          and t["debit"] <= 0.5 * t["credit"],
          f"the take-profit fires at the session the debit first falls to half the "
          f"credit ({t.get('exit_day')}, debit {t.get('debit', 0):.2f} against credit "
          f"{t.get('credit', 0):.2f})")
    # Spot drifting down keeps the spread above half its credit until 21 days out.
    ch2 = Chains(spot=lambda d: 6000.0 - 6.0 * TEST.index(d) if d in TEST else 6000.0)
    tr2 = run(engine(ch2), store("e_dte"))
    t2 = tr2[0] if tr2 else {}
    ok_day = None
    if t2:
        ok_day = next(d for d in TEST if d > t2["entry_day"] and
                      (dt.date.fromisoformat(t2["expiry"]) - dt.date.fromisoformat(d)).days <= 21)
    check(t2 and t2["exit_reason"] == "dte_21" and t2["exit_day"] == ok_day,
          f"the 21-DTE close fires at the first session 21 days or fewer from expiry "
          f"({t2.get('exit_day')}, expiry {t2.get('expiry')})")
    e = engine(ch)
    tr3 = run(e, store("e_one"))
    opens = [(x["entry_day"], x["exit_day"]) for x in tr3]
    check(all(a[1] <= b[0] for a, b in zip(opens, opens[1:])),
          f"one spread at a time: no entry while one is open ({len(tr3)} trades)")


def group_f() -> None:
    head("F. THE CHAIN: a missing day trades nothing; nothing read before it is fetched")
    miss = {TEST[0]}
    e = engine(Chains(missing=miss))
    tr = run(e, store("f_miss"))
    first = next((x for x in e.log if x["day"] == TEST[0]), {})
    check(ps.CHAIN_NOT_STORED in first.get("why", "")
          and (not tr or tr[0]["signal_day"] != TEST[0]),
          f"no snapshot on {TEST[0]}: no trade that day, logged "
          f"'{first.get('why')}'")
    e2 = engine(Chains(missing=set(TEST[:30])))
    check(not run(e2, store("f_none")) and all(ps.CHAIN_NOT_STORED in x["why"] for x in e2.log),
          "no snapshot at all: nothing traded, every day says so")
    # The file reader: a snapshot fetched after the read is never read.
    d = TEST[0]
    base = Path(_TMP) / "chains"
    (base / d).mkdir(parents=True, exist_ok=True)
    cols = ["symbol", "fetched_at", "spot", "expiry", "dte", "right", "strike", "bid",
            "ask", "implied_vol"]
    for tag, at, bid in (("203100Z", f"{d}T20:31:00Z", 1.0), ("235900Z", f"{d}T23:59:00Z", 9.0)):
        with (base / d / f"SPX_{tag}.csv").open("w", newline="", encoding="utf-8") as fp:
            w = csv.DictWriter(fp, fieldnames=cols)
            w.writeheader()
            w.writerow({"symbol": "SPX", "fetched_at": at, "spot": 6000, "expiry": "2026-05-08",
                        "dte": 37, "right": "P", "strike": 5700, "bid": bid, "ask": bid + 0.2,
                        "implied_vol": 0.18})
    fc = ps.FileChains(base, "SPX")
    t = pit.decision_instant(d)
    rows = fc.snapshot(d, t)
    check(fc.days() == [d] and rows and rows[0]["bid"] == 1.0,
          f"the file reader reads the snapshot knowable at the decision ({t[11:16]} UTC) "
          f"and not the one fetched at 23:59 UTC (bid {rows[0]['bid'] if rows else None})")
    check(fc.snapshot(d, f"{d}T20:00:00+00:00") is None,
          "and before the first snapshot is fetched, nothing")


def group_g() -> None:
    head("G. THE COSTS: each leg at its executable side, never the mid")
    e = engine()
    rows = Chains().rows(TEST[0])
    sprd, why = e.choose(rows)
    check(sprd and 0.16 <= sprd["short_delta"] <= 0.20 and 30 <= sprd["dte"] <= 45
          and sprd["short"]["strike"] - sprd["long"]["strike"] == 50,
          f"the spread: {sprd['dte'] if sprd else None} days, short |delta| "
          f"{sprd['short_delta'] if sprd else 0:.3f}, 50 points wide")
    s, lg = sprd["short"], sprd["long"]
    sell, buy = e.leg(-1, s, 1), e.leg(+1, lg, 1)
    mid_s, mid_l = (s["bid"] + s["ask"]) / 2, (lg["bid"] + lg["ask"]) / 2
    check(sell.price < s["bid"] + 1e-12 and sell.price < mid_s
          and buy.price > lg["ask"] - 1e-12 and buy.price > mid_l,
          f"the short sells at or below its bid ({sell.price:.2f} <= {s['bid']}), the long "
          f"buys at or above its ask ({buy.price:.2f} >= {lg['ask']})")
    op = e.open_price(sprd, 1)
    check(op["credit"] < mid_s - mid_l and op["commission"] >= 2.0,
          f"the credit ({op['credit']:.2f}) is under the mid credit ({mid_s - mid_l:.2f}), "
          f"and each leg pays its commission ({op['commission']:.2f})")
    cp = e.close_price(s, lg, 1)
    check(cp["debit"] > mid_s - mid_l,
          f"closing pays above the mid ({cp['debit']:.2f} against {mid_s - mid_l:.2f})")


def group_h() -> None:
    head("H. THE RECORD: the positions table's shape, the family_ref beside it")
    import sqlite3                                              # noqa: PLC0415
    from alpha.ledger import Ledger                             # noqa: PLC0415
    jump = TEST[6]
    tr = run(engine(Chains(spot=lambda d: 6000.0 if d < jump else 6600.0)), store("h"))
    rec = engine().position_record(tr[0], "2026-06-30T22:00:00+00:00")
    p = Path(_TMP) / "h_ledger.db"
    with Ledger(p):
        pass
    con = sqlite3.connect(p)
    cols = {r[1] for r in con.execute("PRAGMA table_info(positions)")}
    con.close()
    check(set(rec["row"]) <= cols and rec["row"]["direction"] == -1
          and rec["row"]["cost_class"] == "index_option_spread",
          f"every field is a positions column ({len(rec['row'])} of {len(cols)}), the "
          f"spread short (-1), its cost class the spread's line")
    check(rec["family_ref"] == "KS options" and tr[0]["family_ref"] == "KS options",
          "and the trade carries family_ref 'KS options'")
    check(isinstance(tr[0]["net"], float) and "net_usd" in tr[0],
          f"its return is ledgered against the sleeve's capital, the benchmark not stored "
          f"(net {tr[0]['net']:+.4f})")


def main() -> int:
    print(f"{LINE}\nTHE PREMIUM SLEEVE (Batch 19 item 100, B99) -- SYNTHETIC STORE AND CHAIN\n{LINE}")
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g, group_h):
        g()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
