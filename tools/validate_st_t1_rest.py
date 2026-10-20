#!/usr/bin/env python3
"""
Validation gate: st-t1-rest -- Batch 6's two constituent ledgers (ST-R5.31b,
ST-R5.44b) and the signal-triage order's Tranche 1 remainder (ST-3's rest, ST-4,
ST-6) where no existing gate is their home. On fixtures; no network, no model,
no live store.

  A  ST-R5.31b. The back-cast caps, the top share, the leaders' relative low and
     its sessions reproduce hand figures; below five completed episodes the
     verdict is INSUFFICIENT and no rate prints; four of five completed falls
     PASS, three FAIL; the ledger file carries its as-of, window and n.
  B  ST-R5.44b. The one-pass drawdowns equal the windowed definition; a member
     20% off its high under a flat index is a +20-point gap and an episode; the
     resolution rule by hand; the floor as in A.
  C  ST-3's rest. The since-the-last-FOMC cut reproduces hand figures on a fixture
     (+18 bp, real share 0.6111, curve share 1.0); a day before the first
     registered decision has none.
  D  ST-4. Each feature reconciles to a hand figure on one fixture store: net
     supply 110bn a month, 4.40% of GDP over 12 months, the private residual
     1.12tn, the official share 41.11%, the custodial share 25%, Treasuries'
     share of net foreign long-term buying 15%, ABS_STRESS by G-32's rule, the 12m
     fed-market gap -30 bp and CRED_STRESS at -60 bp, DEANCHOR on and the 5y5y at
     its 100th percentile, GUNR/DBC 2.0, BBB-AA 45 bp, self-funding 2.0x, net debt
     +20bn, Micron 136.5 days, central-bank gold 120 t.
  E  NOTHING BLANK, NOTHING BY HAND. On an empty store no feature is written and
     every block line names its key and source; the four NOT TRACKED features
     are registered not_yet_sourced, never written; no manual.* key but the
     global PMI is registered (the by-hand audit's rule); no ST-4 or ST-6 module
     imports a network library or opens a store the caller did not name.

    python tools/validate_st_t1_rest.py
"""

from __future__ import annotations

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
TD = Path(mkdtemp("st-t1-rest-gate-"))


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


def close(a, b, tol=1e-4) -> bool:
    return a is not None and b is not None and abs(a - b) <= tol


def days(n: int, start: str = "2024-01-01") -> list[str]:
    import datetime as dt
    d0 = dt.date.fromisoformat(start)
    return [(d0 + dt.timedelta(days=i)).isoformat() for i in range(n)]


# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. ST-R5.31b: THE POST-PEAK CONCENTRATION LEDGER")
    from altdata import ledgers
    from altdata.ledgers import st_r5_31b as L
    caps = L.backcast({"A": 50.0, "B": 50.0},
                      {"A": [("d1", 10.0), ("d2", 20.0)],
                       "B": [("d1", 10.0), ("d2", 10.0)]}, "d2")
    check(caps == {"d1": {"A": 25.0, "B": 50.0}, "d2": {"A": 50.0, "B": 50.0}},
          "back-cast: A's D0 weight 50 at half its D0 close is 25 on d1 (hand)")
    s, top = L.top_share(caps["d1"], {}, n=1)
    check(close(s, 66.666667) and top == ["B"],
          f"the top issuer's share on d1: 50 / 75 = 66.67% (hand; {s})")
    s2, _ = L.top_share({"GOOGL": 10.0, "GOOG": 10.0, "X": 15.0}, {"GOOG": "GOOGL"}, n=1)
    check(close(s2, 57.142857), "a second share class counts with its issuer: 20 / 35")
    # The leaders (A) against the rest (B): A halves on d3, recovers on d4.
    cb = {"p": {"A": 60.0, "B": 40.0}, "d3": {"A": 30.0, "B": 40.0},
          "d4": {"A": 45.0, "B": 40.0}}
    pp = L.post_peak(cb, ["p", "d3", "d4"], "p", ["A"], horizon=2)
    check(close(pp["relative_low_pct"], -50.0) and pp["trough"] == "d3"
          and pp["sessions_to_trough"] == 1 and pp["completed"],
          "the leaders' low against the rest: (30/40) / (60/40) - 1 = -50.0%, one "
          "session after the peak (hand); completed with the horizon in")
    check(not L.post_peak(cb, ["p", "d3", "d4"], "p", ["A"], horizon=5)["completed"],
          "an episode without its horizon after the peak is not completed")
    ep = [{"completed": True, "relative_low_pct": -12.0}] * 4
    v, rate = L.verdict(ep)
    check(v.startswith("INSUFFICIENT") and rate is None and "no rate prints" in v,
          "four completed episodes: INSUFFICIENT, below the floor of five, no rate")
    v5, r5 = L.verdict(ep + [{"completed": True, "relative_low_pct": -3.0}])
    v6, _ = L.verdict(ep[:3] + [{"completed": True, "relative_low_pct": -3.0}] * 2)
    check(v5 == "PASS" and close(r5, 0.8) and v6 == "FAIL",
          "four of five completed falls of 10% or more PASS (0.80); three FAIL "
          "(the pre-registered rule)")
    # End to end on a small basket: 11 members, the top ten's share above 40%.
    ds = days(30)
    w = {f"M{i}": (8.0 if i < 10 else 20.0) for i in range(11)}
    cl = {tk: [(d, 100.0) for d in ds] for tk in w}
    r = L.study({"weights": w, "holdings_day": ds[-1], "closes": cl, "classes": {}})
    check(r["n"] == 0 and r["result"]["episodes"] == 1 and r["result"]["rate"] is None
          and r["verdict"].startswith("INSUFFICIENT")
          and any("No rate prints below the floor" in x for x in r["body"])
          and not ledgers.ledger_faults({**r, "sources": ["fixture"],
                                         "source_mode": "fixture"}),
          f"a flat basket at {r['result']['share_now']:.1f}%: one open episode, n 0, "
          f"no rate printed, and the ledger carries its as-of, window and n")
    md, _ = ledgers.write_ledger({**r, "sources": ["fixture"],
                                  "source_mode": "laptop run, public sources"},
                                 TD, "2026-10-18")
    t = md.read_text(encoding="utf-8")
    check(md.name == "st-r5.31b-ledger-2026-10-18.md" and "| n | 0 |" in t
          and "Pre-registered by this first edition" in t and "grants nothing" in t,
          "the file is docs/ledgers/<item>-ledger-<date>.md, with n, the pre-registered "
          "rule and the rights line that grants nothing")


def group_b() -> None:
    head("B. ST-R5.44b: THE DRAWDOWN-GAP LEDGER")
    from altdata.ledgers import st_r5_44b as L
    s = [("a", 100.0), ("b", 110.0), ("c", 99.0)]
    check(close(L.drawdown_at(s, 2, window=3, min_closes=3), -10.0)
          and L.drawdown_at(s, 1, window=3, min_closes=3) is None,
          "99 against the window's 110: -10.0% (hand); a short window is none")
    import random
    rng = random.Random(7)
    ser = [(f"{i:05d}", 100 + rng.uniform(-30, 30)) for i in range(400)]
    one = L.drawdowns(ser)
    check(all(close(one.get(d), L.drawdown_at(ser, i), 1e-9) if L.drawdown_at(ser, i)
              is not None else d not in one for i, (d, _) in enumerate(ser)),
          "the one-pass drawdowns equal the windowed definition on 400 random closes")
    ds = days(300)
    index = [(d, 100.0) for d in ds]
    fall = [(d, 100.0 if i < 280 else 80.0) for i, d in enumerate(ds)]
    gs = L.gap_series({"X": fall, "Y": fall}, index)
    last = gs[-1]
    check(close(last[1], 0.0) and close(last[2], -20.0) and close(last[3], 20.0)
          and last[4] == 2,
          "members 20% off their high under a flat index: a +20-point gap (hand)")
    r = L.study({"closes": {"X": fall, "Y": fall}, "index": index})
    check(r["result"]["episodes"] == 1 and r["n"] == 0
          and r["verdict"].startswith("INSUFFICIENT") and r["result"]["rate"] is None,
          "the gap opens one wide episode, not completed: n 0, no rate printed")
    g = [("p", -1.0, -21.0, 20.0, 9)] + [(f"x{i}", -7.0, -20.0, 13.0, 9)
                                         for i in range(3)]
    check(L.resolve(g, 0, horizon=3)["resolution"] == "leaders fell"
          and L.resolve(g, 0, horizon=3)["completed"],
          "the index 6 points deeper within the horizon: the leaders fell (hand)")
    g2 = [("p", -1.0, -21.0, 20.0, 9)] + [(f"x{i}", -2.0, -15.0, 13.0, 9)
                                          for i in range(3)]
    g3 = [("p", -1.0, -21.0, 20.0, 9)] + [(f"x{i}", -2.0, -18.0, 16.0, 9)
                                          for i in range(3)]
    check(L.resolve(g2, 0, horizon=3)["resolution"] == "broadening"
          and L.resolve(g3, 0, horizon=3)["resolution"] == "unresolved",
          "the average member 6 points better: broadening; 3 points: unresolved")
    done = [{"completed": True, "resolution": "leaders fell"}] * 3 + \
           [{"completed": True, "resolution": "broadening"}] * 2
    v, rate = L.verdict(done)
    v2, _ = L.verdict(done[:4])
    check(v == "PASS" and close(rate, 0.6) and v2.startswith("INSUFFICIENT"),
          "three of five resolved by the leaders falling PASS (0.60); four "
          "completed is INSUFFICIENT")


def obs(key, day, value, inst=None, avail=None):
    return {"registry_key": key, "instrument": inst, "observed_at": day,
            "available_at": avail or f"{day}T21:00:00+00:00", "value": value,
            "source": "fixture"}


def store(rows, name):
    from altdata import observations
    p = str(TD / f"{name}.db")
    with observations.ObservationStore(p) as st:
        st.write_many(rows)
    return p


def month_ends(start: str, n: int) -> list[str]:
    import calendar
    y, m = int(start[:4]), int(start[5:7])
    out = []
    for _ in range(n):
        out.append(f"{y:04d}-{m:02d}-{calendar.monthrange(y, m)[1]:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def group_c() -> None:
    head("C. ST-3's REST: THE CUT SINCE THE LAST FOMC DECISION")
    from altdata import market_features as mf, observations
    ds = ["2026-03-16", "2026-03-17", "2026-03-18", "2026-03-19"]
    y10, tips, y2 = [4.00, 4.02, 4.10, 4.20], [1.80, 1.81, 1.86, 1.92], [3.50, 3.52, 3.62, 3.70]
    rows = ([obs("fred.yield_10y", d, v) for d, v in zip(ds, y10)]
            + [obs("fred.tips_10y", d, v) for d, v in zip(ds, tips)]
            + [obs("fred.yield_2y", d, v) for d, v in zip(ds, y2)])
    with observations.ObservationStore(store(rows, "fomc")) as st:
        out = mf.rates_rows(st, as_of="2026-03-20T00:00:00+00:00")
    got = {(r["registry_key"], r["observed_at"]): r["value"] for r in out
           if "since_fomc" in r["registry_key"]}
    check("2026-03-18" in mf.fomc_decision_days(),
          "the decision days are the claims registry's (18 Mar 2026 among them)")
    check(close(got.get(("calc.attr_d10y_since_fomc", "2026-03-19")), 18.0)
          and close(got.get(("calc.attr_real_share_since_fomc", "2026-03-19")), 0.611111)
          and close(got.get(("calc.attr_curve_share_since_fomc", "2026-03-19")), 1.0),
          "the day after the decision: +18 bp since the close before it; real share "
          "0.11/0.18 = 0.6111; curve 0.18/0.18 = 1.0 (hand)")
    check(close(got.get(("calc.attr_d10y_since_fomc", "2026-03-18")), 8.0)
          and close(got.get(("calc.attr_curve_share_since_fomc", "2026-03-18")), 1.25),
          "the decision day carries its own reaction: +8 bp, curve 1.25 (hand)")
    check(("calc.attr_d10y_since_fomc", "2026-03-17") not in got,
          "a day whose last decision has no close before it in the store has no cut")


def absorption_fixture() -> list:
    me = month_ends("2025-01", 13)
    rows = []
    for i, d in enumerate(me):
        rows.append(obs("fred.soma_treasuries", d, 4_000_000.0 - 10_000.0 * i))
        if i:
            rows.append(obs("fiscaldata.mspd_net_marketable_issuance", d, 100e9))
        rows.append(obs("tic.flow_private_treasuries", d, 10.0))
        rows.append(obs("tic.flow_official_treasuries", d, 5.0))
        rows.append(obs("tic.flow_net_domestic", d, 100.0))
        rows.append(obs("imf.ifs.gold_net_purchases_oz.total", d, 32150.7466 * 10))
    rows += [obs("fred.gdp_nominal", "2025-10-01", 30000.0),
             obs("tic.official_holdings", me[0], 3.8e12),
             obs("tic.official_holdings", me[12], 3.7e12),
             obs("tic.private_holdings", me[0], 5.0e12),
             obs("tic.private_holdings", me[12], 5.3e12),
             obs("tic.holdings_total", me[12], 2000.0)]
    for c in ("United Kingdom", "Belgium", "Ireland", "Luxembourg", "Cayman Islands"):
        rows.append(obs("tic.holdings_by_country", me[12], 100.0, c))
    btc = [2.5] * 9 + [2.2, 2.1]
    for i, v in enumerate(btc):
        d = f"2026-0{1 + i // 4}-{10 + i % 4:02d}" if i < 8 else f"2026-03-{20 + i:02d}"
        rows.append(obs("auction.bid_to_cover", d, v, "Note:10-Year"))
        rows.append(obs("auction.dealer_share", d, 0.25 if i == 0 else 0.10, "Note:10-Year"))
    rows += [obs("fred.aa_oas", "2026-10-16", 0.60), obs("fred.bbb_oas", "2026-10-16", 1.05),
             obs("fedfunds.futures_price", "2026-10-15", 96.20, "2027-10"),
             obs("fedfunds.futures_price", "2026-10-16", 96.50, "2027-10"),
             obs("fred.sep_median_ff", "2026-01-01", 4.1, None, "2026-09-18T00:00:00+00:00"),
             obs("fred.sep_median_ff", "2027-01-01", 4.1, None, "2026-09-18T00:00:00+00:00"),
             obs("fred.breakeven_5y5y", "2022-04-20", 2.65),
             obs("fedboard.cie", "2022-07-01", 2.20), obs("fedboard.cie", "2026-07-01", 2.30),
             obs("yfinance.mkt_gunr", "2026-10-16", 40.0),
             obs("yfinance.mkt_dbc", "2026-10-16", 20.0)]
    import datetime as dt
    d0 = dt.date(2026, 9, 1)
    for k in range(25):
        rows.append(obs("fred.breakeven_5y5y", (d0 + dt.timedelta(days=k)).isoformat(), 2.70))
    for tk in ("AMZN", "GOOGL", "META", "MSFT", "ORCL"):
        rows += [obs("edgar.xbrl_operating_cash_flow", "2024-12-31", 20e9, tk),
                 obs("edgar.xbrl_capex", "2024-12-31", 10e9, tk),
                 obs("edgar.xbrl_long_term_debt", "2023-12-31", 50e9, tk),
                 obs("edgar.xbrl_cash", "2023-12-31", 30e9, tk),
                 obs("edgar.xbrl_long_term_debt", "2024-12-31", 54e9, tk),
                 obs("edgar.xbrl_cash", "2024-12-31", 30e9, tk)]
    rows += [obs("edgar.xbrl_mu_inventory", "2026-08-27", 9e9, "MU"),
             obs("edgar.xbrl_mu_cogs_q", "2026-08-27", 6e9, "MU")]
    return rows


def group_d() -> None:
    head("D. ST-4: EACH FEATURE AGAINST A HAND FIGURE")
    from altdata import absorption as A, observations
    with observations.ObservationStore(store(absorption_fixture(), "absorb")) as st:
        rows = A.compute_rows(st, "2026-10-17T21:00:00+00:00")
    by: dict = {}
    for r in rows:
        by.setdefault(r["registry_key"], []).append(r)

    def last(k, inst=None):
        xs = [r for r in by.get(k, []) if inst is None or r["instrument"] == inst]
        return sorted(xs, key=lambda r: r["observed_at"])[-1]["value"] if xs else None
    check(close(last("calc.net_supply_1m"), 110e9, 1)
          and close(last("calc.net_supply_12m"), 1.32e12, 1)
          and close(last("calc.net_supply_12m_gdp"), 4.4),
          "net supply: 100bn issued less the Fed's -10bn = 110bn a month; 1.32tn over "
          "12 months, 4.40% of a 30tn GDP (hand)")
    check(close(last("calc.tic_official_12m"), -0.1e12, 1)
          and close(last("calc.tic_private_12m"), 0.3e12, 1)
          and close(last("calc.priv_residual_12m"), 1.12e12, 1),
          "foreign holders -0.1tn official, +0.3tn private; the residual 1.32 + 0.1 - "
          "0.3 = 1.12tn (hand)")
    check(close(last("calc.tic_official_share"), 41.111111)
          and close(last("calc.tic_custodial_share"), 25.0)
          and close(last("calc.foreign_ust_share_lt"), 15.0),
          "the official share 3.7/9.0 = 41.11%; the custodial centres 500/2000 = 25%; "
          "Treasuries 15 of 100 in net foreign long-term buying (hand)")
    st_ = sorted((r["observed_at"], r["value"]) for r in by.get("calc.abs_stress", []))
    check([v for _, v in st_][:1] == [1] and [v for _, v in st_][-2:] == [0, 1]
          and len(st_) == 11,
          "ABS_STRESS (G-32): dealers 25% on the first auction ON; the tenth, the "
          "first bottom-decile cover, off; the eleventh, the second in a row, ON (hand)")
    gaps = sorted((r["observed_at"], r["value"]) for r in by.get("calc.fed_mkt_gap_12m", []))
    creds = sorted((r["observed_at"], r["value"]) for r in by.get("calc.cred_stress", []))
    check(gaps == [("2026-10-15", -30.0), ("2026-10-16", -60.0)]
          and creds == [("2026-10-15", 0), ("2026-10-16", 1)],
          "the 12m gap: 3.80% implied against the 2027 dot of 4.10%, -30 bp, then "
          "-60 bp; CRED_STRESS off, then on past 50 bp (hand)")
    check(last("calc.deanchor") == 1 and close(last("calc.be5y5y_range_pos"), 100.0),
          "DEANCHOR: 25 sessions above the 2022 high of 2.65% with the CIE above its "
          "2022 high; the 5y5y at its 100th percentile since 2010 (hand)")
    check(close(last("calc.producers_spot_ratio"), 2.0) and close(last("calc.aa_bbb_oas_diff"), 45.0),
          "GUNR over DBC 40/20 = 2.0; BBB 1.05% less AA 0.60% = 45 bp (hand)")
    check(close(last("calc.self_fund_ratio"), 2.0) and close(last("calc.hs_netdebt_12m"), 20e9, 1)
          and close(last("calc.mu_inv_days"), 136.5) and close(last("calc.cb_gold_12m"), 120.0),
          "self-funding 100/50 = 2.0x; net debt (270 - 150) less (250 - 150) = +20bn; "
          "Micron 9/6 x 91 = 136.5 days; gold 12 x 10 t = 120 t (hand)")


def group_e() -> None:
    head("E. NOTHING BLANK, NOTHING BY HAND, NOTHING LIVE")
    import ast
    from altdata import absorption as A, derived, observations
    from daily_cascade import absorption_block as B
    with observations.ObservationStore(store([], "empty")) as st:
        rows = A.compute_rows(st, "2026-10-17T21:00:00+00:00",
                              cutoff_day="2026-10-17")
        subs = (B.subsections(st, "2026-10-17T21:00:00+00:00", "plumbing")
                + B.subsections(st, "2026-10-17T21:00:00+00:00", "slow"))
    lines = [x for s in subs for x in s["lines"]]
    check(not rows, "on an empty store no feature is written: never a blank, never a zero")
    data_lines = [x for x in lines if ":" in x and not x.rstrip().endswith(":")]
    # Six: SR-1's style-regime panel joined the Slow layers (ST-8, st-t3-calib).
    check(len(subs) == 6 and lines and all(x.strip() for x in lines)
          and all(("NOT AVAILABLE (" in x or "NOT TRACKED (" in x or "not determinable"
                   in x or "withdrawn" in x or "deferred" in x or "zero rebalancing" in x
                   or "not assessable" in x or "not rendered" in x
                   or "(as of the ledger)" in x)
                  for x in data_lines),
          f"every one of the {len(data_lines)} block lines on an empty store names its "
          f"key and source (NOT AVAILABLE / NOT TRACKED), or says why it is not read")
    check(all(len(s["lines"]) <= B.CAPS.get(s["title"], 99) for s in subs)
          and len(next(s for s in subs if s["title"] == B.DA_TITLE)["lines"]) <= 18
          and len(next(s for s in subs if s["title"] == B.CU_TITLE)["lines"]) <= 10,
          "the line caps hold: Duration Absorption 18, Cheap-and-Unloved 10")
    nt = [derived.registry_entry(k) for k in A.NOT_TRACKED]
    check(all(e and e.get("status_extra") == "not_yet_sourced" for e in nt)
          and not any(r["registry_key"] in A.NOT_TRACKED for r in rows),
          "the four NOT TRACKED features are registered not_yet_sourced and never written")
    import yaml
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    manual = sorted(k for k in (reg.get("metrics") or {}) if str(k).startswith("manual.")
                    and (reg["metrics"][k] or {}).get("status_extra") != "superseded")
    check(manual == ["manual.global_pmi"] or manual == [],
          f"no new by-hand key: the registry's manual.* metrics are the PMI alone ({manual})")
    banned = {"requests", "urllib", "httpx", "socket", "anthropic", "subprocess"}
    hits = []
    for f in ("altdata/absorption.py", "daily_cascade/absorption_block.py",
              "altdata/ledgers/st_r5_31b.py", "altdata/ledgers/st_r5_44b.py"):
        tree = ast.parse((REPO / f).read_text(encoding="utf-8"))
        for n in ast.walk(tree):
            names = ([a.name for a in n.names] if isinstance(n, ast.Import)
                     else [n.module or ""] if isinstance(n, ast.ImportFrom) else [])
            hits += [f"{f}: {x}" for x in names
                     if any(x == b or x.startswith(b + ".") for b in banned)]
    opened = []
    orig = observations.ObservationStore.__init__

    def spy(self, path=None, *a, **k):
        opened.append(path)
        return orig(self, path, *a, **k)
    observations.ObservationStore.__init__ = spy
    try:
        B.subsections(None, "2026-10-17T21:00:00+00:00", "plumbing")
        B.subsections(None, "2026-10-17T21:00:00+00:00", "slow")
    finally:
        observations.ObservationStore.__init__ = orig
    check(not hits and not opened,
          f"no ST-4/ST-6 or ledger module imports a network library ({hits}); with no "
          f"store named, the blocks open none ({opened})")


def main() -> int:
    print(f"{LINE}\nst-t1-rest\n{LINE}")
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
