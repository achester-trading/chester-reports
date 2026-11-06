"""
A127 (session A, 6 Nov 2026): signal-triage Batch 22 item 116 (the order's 98.1
and 98.3; SR-77, provisional), the levered-ETF close flow.

  A  THE FORMULA. On a fixture roster: L x (L - 1) is 6, 2, 2, 6 and 12 for 3x,
     2x, -1x, -2x and -3x, so a 3x fund trades 6 x AUM x r and a -3x 12 x AUM x r;
     the bucket sums and the total by hand; % of ADV against the bucket's ADV; a
     gap fund, a fund with no AUM and one with no return are left out and named;
     a bucket with no fund is "not estimated"; dollars per 1% (V-98c).
  B  THE FLAG (O-1). At 15:00, |the total| >= $20bn either way: $20bn fires,
     $19.9bn does not, -$20bn fires. The switch: 59 stored sessions keep the
     dollar rule; at 60 the 90th percentile of |the history| in % of ADV takes
     over, dated the session after the 60th, by itself.
  C  THE STORE. A seeded temporary store: the 16:45 estimate from stored closes
     and prior AUM equals the hand sum; the rows are calc.close_flow.<bucket>,
     .total and _pct_adv, instrument = the slot; a stale AUM is left out; the
     15:00 pass on a fake intraday reader stores instrument 1500 rows, reads only
     completed bars, and no unstored symbol is read from Yahoo (D33). MSTR's and
     COIN's spot come from fixture captured chains (D66 ruling 2, A127b): the
     newest chain at or before the instant against the previous session's, a
     chain fetched after the cutoff never seen, a 15:00 chain older than its
     allowance refused and named; SNDK's fund prints "gap: no keyless price".
  D  THE PRINTS. The close's table (16:45 and 15:00 by bucket, $bn and % of ADV),
     the flag's line only when it fired, the "mechanical close flow" line with
     "dealer hedging: not yet combined"; the Weekly's sessions largest first; the
     Monthly's five; the close and the Weekly call the block, the 07:00 anchor
     does not.
  E  THE ROSTER AND THE BLOCKLIST. Every fund in the Security Master (etf, with
     yahoo and store_key identifiers); the paste's named funds present; UVXY
     excluded; leverage in {3, 2, -1, -2, -3}; no fund restricted, and the
     writer's assertion refuses a planted Brookfield ticker and fails closed when
     the blocklist will not load.
  F  THE WRITER. Direxion's file, GraniteShares' workbook and REX's page parsed
     and Defiance's page (A127b) from fixtures, each observed at the close it
     values; Direxion lines that
     disagree are refused; a robots disallow is never requested; the Crawl-delay
     is honoured; one request per page.
  G  HYGIENE. The keys registered and barred from the market-state object (named
     in neither its config nor regime.py); the DTH-1 draft setup (98.3) is a
     Book C draft the lab does not import; levered_etf on the external roster
     after proshares; the 15:00 timer held out of DEPLOY_TIMERS; the wrapper's
     one call; the gate on the list.
  H  THE EVENT-STUDY UTILITY (Batch 16 item 91(a); A128). Windows in sessions,
     the pre / day-0 / post views, forward returns pending past the end, the
     cross-event average, the base rate and the two-asset comparison, each by
     hand; pure arithmetic; one utility, no second implementation.
  I  THE CLOSE-FLOW LEDGER (98.2; A128). The pre-registration's SHA-256 held;
     below 20 stored sessions "accruing (n=k of 20)"; the top-decile cut and its
     events by hand; the measures (the last 30 minutes, the next open, +1, +5);
     the two seed rows marked "seed, order's figure", 5 Nov "estimate,
     unconfirmed"; no pass rule; the first edition registers it.
  J  ITEM 118 (A128). SPHB and SPLV through the Security Master into the basket;
     the crowding family's member (its config, the 89(a) gauge "not built");
     calc.hb_lv_ratio and its change by hand; the flag at both edges; its one
     line in What doesn't fit on a fired day only; the backtest's events and
     V-100a's two branches; the keys barred; the pre-registration's hash held.

Synthetic fixtures only: no live store, no network, no model. The clock is pinned
to GATE_NOW (B106's rule).

    python tools/validate_item_116.py
"""

from __future__ import annotations

import datetime as dt
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import yaml  # noqa: E402

import gate_tmp  # noqa: E402
from altdata import close_flow as cf  # noqa: E402
from altdata import observations, session  # noqa: E402
from altdata.sources import levered_etf as le  # noqa: E402

GATE_KIND = "code"
GATE_NOW = "2026-11-06T23:00:00+00:00"   # 18:00 ET on a Friday, after the close
DAY = "2026-11-06"
PREV = "2026-11-05"
PASS = FAIL = 0
TD116 = None
LINE = "=" * 78
CFG = cf.config()


def pin_clock() -> None:
    session.utc_now = lambda: dt.datetime.fromisoformat(GATE_NOW)


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


def close(a, b, tol=1e-6) -> bool:
    return a is not None and b is not None and abs(a - b) <= tol * max(1.0, abs(b))


def weekdays(n: int, end: str) -> list[str]:
    out, d = [], dt.date.fromisoformat(end)
    while len(out) < n:
        if session.is_trading_session(d):
            out.append(d.isoformat())
        d -= dt.timedelta(days=1)
    return out[::-1]


FIX = {
    "buckets": [{"id": "semis", "label": "Semis", "adv": ["smh"]},
                {"id": "ndx", "label": "Nasdaq 100", "adv": ["qqq"]},
                {"id": "empty", "label": "Empty", "adv": ["spy"]}],
    "underlyings": {"smh": {}, "qqq": {}, "spy": {}, "mstr": {}},
    "funds": [{"ticker": "BULL3", "leverage": 3, "underlying": "smh", "bucket": "semis"},
              {"ticker": "BEAR3", "leverage": -3, "underlying": "smh", "bucket": "semis"},
              {"ticker": "Q2", "leverage": 2, "underlying": "qqq", "bucket": "ndx"},
              {"ticker": "QINV1", "leverage": -1, "underlying": "qqq", "bucket": "ndx"},
              {"ticker": "QINV2", "leverage": -2, "underlying": "qqq", "bucket": "ndx"},
              {"ticker": "NOAUM", "leverage": 3, "underlying": "qqq", "bucket": "ndx"},
              {"ticker": "NORET", "leverage": 2, "underlying": "mstr", "bucket": "ndx"},
              {"ticker": "GAPPY", "leverage": 2, "underlying": "qqq", "bucket": "ndx",
               "method": "gap", "gap": "no keyless reading"}],
}


# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. THE FORMULA ON A FIXTURE ROSTER")
    check([cf.factor(x) for x in (3, 2, -1, -2, -3)] == [6.0, 2.0, 2.0, 6.0, 12.0],
          "L x (L - 1): 3x 6, 2x 2, -1x 2, -2x 6, -3x 12")
    aum = {"BULL3": 1e9, "BEAR3": 1e9, "Q2": 2e9, "QINV1": 1e9, "QINV2": 0.5e9,
           "NORET": 1e9}
    e = cf.estimate(FIX, aum, {"smh": -0.02, "qqq": 0.01},
                    {"smh": 4e10, "qqq": 2e10, "spy": 3e10})
    fl = {f["ticker"]: f["flow"] for f in e["funds"]}
    check(close(fl["BULL3"], 6 * 1e9 * -0.02) and close(fl["BEAR3"], 12 * 1e9 * -0.02),
          f"a 3x fund trades 6 x AUM x r ({cf.usd(fl['BULL3'])}); a -3x 12 x AUM x r "
          f"({cf.usd(fl['BEAR3'])}): both sell on a fall")
    b = {x["id"]: x for x in e["buckets"]}
    semis = 6 * 1e9 * -0.02 + 12 * 1e9 * -0.02
    ndx = 2 * 2e9 * 0.01 + 2 * 1e9 * 0.01 + 6 * 0.5e9 * 0.01
    check(close(b["semis"]["flow"], semis) and close(b["ndx"]["flow"], ndx)
          and close(e["total"]["flow"], semis + ndx),
          f"the bucket sums by hand (semis {cf.usd(semis)}, Nasdaq 100 {cf.usd(ndx)}) "
          f"and the total ({cf.usd(semis + ndx)})")
    check(close(b["semis"]["pct_adv"], 100 * semis / 4e10)
          and close(e["total"]["pct_adv"], 100 * (semis + ndx) / 6e10),
          f"% of ADV: the bucket against its ADV ({b['semis']['pct_adv']:+.2f}%); the total "
          f"against the estimated buckets' ADV, each instrument once")
    check(b["empty"]["flow"] is None and b["empty"]["pct_adv"] is None,
          "a bucket with no fund estimated is 'not estimated' (no figure, no zero)")
    lo = e["left_out"]
    check(lo.get("GAPPY", "").startswith("gap:") and lo.get("NOAUM") == "no AUM stored"
          and "mstr" in lo.get("NORET", ""),
          f"left out and named: the gap fund, the fund with no AUM, the fund with no return "
          f"({sorted(lo)})")
    pm = cf.per_move(FIX, aum)
    want = 0.01 * (6e9 + 12e9 + 2 * 2e9 + 2 * 1e9 + 6 * 0.5e9 + 2 * 1e9)
    check(close(pm["total"], want),
          f"V-98c: dollars per 1% move in every underlying, from the roster's AUM "
          f"({cf.usd(pm['total'])} on the fixture)")


# ---------------------------------------------------------------------------
def group_b() -> None:
    head("B. THE FLAG AND ITS DATED SWITCH (O-1)")
    r0 = cf.flag_rule([], CFG)
    check(r0["basis"] == "dollars" and r0["threshold"] == 20e9,
          "no history: the dollar rule, $20bn (config, O-1)")
    f1 = cf.flag({"flow": 20e9, "pct_adv": 1.0}, r0)
    f2 = cf.flag({"flow": 19.9e9, "pct_adv": 1.0}, r0)
    f3 = cf.flag({"flow": -20e9, "pct_adv": -1.0}, r0)
    check(f1["fired"] is True and f2["fired"] is False and f3["fired"] is True,
          "$20bn fires, $19.9bn does not, -$20bn fires (either way)")
    check("FIRED (selling" in f3["line"] and "Alert-only; no rights" in f3["line"],
          f"the line names the side and carries no rights: {f3['line'][:90]}...")
    check(cf.flag({"flow": None, "pct_adv": None}, r0)["fired"] is None,
          "no 15:00 estimate: the flag is 'not read', never 'not fired'")
    days = weekdays(61, "2026-02-02")
    hist = [(d, float(i % 30) - 15.0) for i, d in enumerate(days)]
    r59 = cf.flag_rule(hist[:59], CFG)
    r60 = cf.flag_rule(hist[:60], CFG)
    check(r59["basis"] == "dollars" and r59["stored"] == 59,
          "59 stored sessions: still the dollar rule")
    exp_since = cf.next_session(days[59])
    absv = sorted(abs(v) for _, v in hist[:60])
    k = 59 * 0.9
    p90 = absv[int(k)] + (absv[int(k) + 1] - absv[int(k)]) * (k - int(k))
    check(r60["basis"] == "pct_adv" and r60["since"] == exp_since
          and close(r60["threshold"], p90),
          f"at 60: the 90th percentile of |the history| in % of ADV "
          f"({r60['threshold']:.2f}%), in force since {r60['since']} -- the switch, dated, "
          f"by the code")
    fp = cf.flag({"flow": 5e9, "pct_adv": -(p90 + 0.1)}, r60)
    check(fp["fired"] and "percentile of the box's own 15:00 history" in fp["line"]
          and exp_since in fp["line"],
          "after the switch a -$5bn day past the percentile fires, and the line names "
          "the rule's date")
    sw = CFG["flag"]["switch"]
    check(sw["after_sessions"] == 60 and sw["percentile"] == 90
          and sw["basis"] == "total_pct_adv" and CFG["flag"]["slot"] == "1500",
          "config: 60 sessions, the 90th percentile, % of ADV, the 15:00 slot")


# ---------------------------------------------------------------------------
CHAIN_COLS = ["expiry", "dte", "right", "strike", "bid", "ask", "last_price", "volume",
              "open_interest", "last_trade_date", "fetched_at", "spot"]


def seed_chains(base: Path) -> dict:
    """Fixture captured chains (data/chains/<day>/<SYM>_<utc>.csv) for MSTR and
    COIN; returns the 16:45 returns by hand. A chain fetched after GATE_NOW (MSTR
    at 23:30 UTC, spot 500) must never be read; COIN's newest by 15:00 is 11:00 ET,
    older than the 180-minute allowance."""
    plan = {
        ("MSTR", PREV): [("2026-11-05T21:10:00+00:00", 100.0)],
        ("MSTR", DAY): [("2026-11-06T17:30:00+00:00", 95.0),
                        ("2026-11-06T20:40:00+00:00", 97.0),
                        ("2026-11-06T21:10:00+00:00", 90.0),
                        ("2026-11-06T23:30:00+00:00", 500.0)],
        ("COIN", PREV): [("2026-11-05T21:10:00+00:00", 200.0)],
        ("COIN", DAY): [("2026-11-06T16:00:00+00:00", 204.0),
                        ("2026-11-06T21:10:00+00:00", 210.0)],
    }
    for (sym, day), caps in plan.items():
        d = base / day
        d.mkdir(parents=True, exist_ok=True)
        for at, spot in caps:
            stamp = at[:19].replace("-", "").replace(":", "")
            with open(d / f"{sym}_{stamp}.csv", "w", encoding="utf-8", newline="") as fh:
                fh.write(",".join(CHAIN_COLS) + "\n")
                fh.write(f"2026-11-20,14,C,100,1,1.1,1.05,10,100,{day},{at},{spot}\n")
    return {"mstr": 90.0 / 100.0 - 1.0, "coin": 210.0 / 200.0 - 1.0}


def seed_store(db: Path, aum_day: str = PREV) -> tuple[dict, dict, dict]:
    """AUM for every non-gap fund at `aum_day`; 25 sessions of closes and volume
    for every stored underlying. Returns (aum, r on DAY, adv) by hand."""
    rows = []
    sess = weekdays(26, DAY)
    aum, rets, adv = {}, {}, {}
    for i, f in enumerate(CFG["funds"]):
        if f.get("method") == "gap":
            continue
        aum[f["ticker"]] = 1e9 + 1e7 * i
        rows.append({"registry_key": "levetf.aum", "instrument": f["ticker"],
                     "observed_at": aum_day, "available_at": f"{DAY}T19:00:00+00:00",
                     "value": aum[f["ticker"]], "source": "levered_etf:direxion"})
    for j, (u, x) in enumerate(CFG["underlyings"].items()):
        k = x.get("store_key")
        if not k:
            continue
        px = [100.0 + j + 0.1 * n for n in range(len(sess))]
        px[-1] = px[-2] * (1.0 - 0.01 * (j + 1) / 4)
        rets[u] = px[-1] / px[-2] - 1.0
        for d, p in zip(sess, px):
            rows.append({"registry_key": k, "instrument": None, "observed_at": d,
                         "available_at": f"{d}T21:05:00+00:00", "value": p,
                         "source": "yfinance"})
            rows.append({"registry_key": k + "_volume", "instrument": None,
                         "observed_at": d, "available_at": f"{d}T21:05:00+00:00",
                         "value": 1e6 * (j + 1), "source": "yfinance"})
        dv = [p * 1e6 * (j + 1) for p in px[-21:-1]]
        adv[u] = sum(dv) / len(dv)
    with observations.ObservationStore(str(db)) as st:
        st.write_many(rows)
    return aum, rets, adv


def hand(aum, rets, adv) -> tuple[float, dict]:
    tot, byb = 0.0, {}
    for f in CFG["funds"]:
        t, u = f["ticker"], f["underlying"]
        if t in aum and u in rets:
            v = aum[t] * cf.factor(f["leverage"]) * rets[u]
            tot += v
            byb[f["bucket"]] = byb.get(f["bucket"], 0.0) + v
    return tot, byb


def group_c(td: str) -> Path:
    head("C. THE STORE: THE 16:45 ESTIMATE, THE ROWS, THE 15:00 PASS")
    cf.CHAIN_BASE = Path(td) / "chains"
    chain_rets = seed_chains(cf.CHAIN_BASE)
    db = Path(td) / "c.db"
    aum, rets, adv = seed_store(db)
    rets.update(chain_rets)
    tot, byb = hand(aum, rets, adv)
    with observations.ObservationStore(str(db)) as st:
        e = cf.for_close(st, DAY, GATE_NOW)
        rows = cf.rows(e, "1645", DAY, GATE_NOW)
        st.write_many(rows)
        back = cf.stored(st, DAY, GATE_NOW, "1645")
    b = {x["id"]: x for x in e["buckets"]}
    check(close(e["total"]["flow"], tot) and all(close(b[k]["flow"], v) for k, v in byb.items()),
          f"the 16:45 estimate from stored closes and prior AUM equals the hand sum "
          f"({cf.usd(tot)}; {len(byb)} buckets)")
    semi_adv = adv["smh"]
    check(close(b["semiconductors"]["pct_adv"], 100 * byb["semiconductors"] / semi_adv),
          "the semiconductors' % of ADV against SMH's 20-session dollar volume, by hand")
    keys = {r["registry_key"] for r in rows}
    check(set(keys) <= set(cf.store_keys()) and "calc.close_flow.total" in keys
          and "calc.close_flow.total_pct_adv" in keys
          and all(r["instrument"] == "1645" and r["observed_at"] == DAY for r in rows),
          f"the rows: calc.close_flow.<bucket>, .total and _pct_adv, instrument = the slot "
          f"({len(rows)} rows)")
    check(close(back["total"][0], tot), "and they read back as stored")
    nr = {t: w for t, w in e["left_out"].items()}
    fl45 = {f["ticker"]: f for f in e["funds"]}
    check(all(t in fl45 for t in ("MSTU", "MSTZ", "MSTX", "CONL"))
          and close(fl45["MSTU"]["r"], -0.10) and close(fl45["CONL"]["r"], 0.05),
          "D66 ruling 2: MSTU, MSTZ, MSTX and CONL rejoin the 16:45 estimate on the "
          "captured chains' spot (MSTR -10.0%, COIN +5.0%), the chain fetched after the "
          "cutoff never read")
    check(nr.get("SNXX", "").startswith("gap:") and "no keyless price" in nr["SNXX"],
          f"SNXX is a named gap and its underlying prints 'gap: no keyless price': "
          f"{nr.get('SNXX', '')[:60]}...")
    check(CFG["aum_floor_usd"] == 250e6 and "D66" in CFG.get("aum_floor_set", "")
          and {"NVDU", "MSFU", "METU", "AMZU", "NVDX", "MSTX"}
          <= {f["ticker"] for f in CFG["funds"]},
          "D66 ruling 5: the floor is $250m, dated; NVDU, MSFU, METU, AMZU, NVDX and "
          "MSTX admitted")
    db2 = Path(td) / "c2.db"
    seed_store(db2, aum_day="2026-10-28")
    with observations.ObservationStore(str(db2)) as st:
        e2 = cf.for_close(st, DAY, GATE_NOW)
    check(e2["total"]["flow"] is None and "older than 5 days" in e2["left_out"].get("SOXL", ""),
          "an AUM older than five days is left out and named, never carried")

    # The 15:00 pass, on a fake intraday reader, into the temporary store.
    calls = []

    def fetcher(sym, start, end):
        calls.append(sym)
        out = []
        for hm, px in (("14:50", 99.0), ("14:55", 100.0), ("15:00", 900.0)):
            t = dt.datetime.combine(dt.date.fromisoformat(DAY),
                                    dt.time(*map(int, hm.split(":"))),
                                    tzinfo=session._eastern_tz())  # noqa: SLF001
            out.append({"observed_at": t.astimezone(dt.timezone.utc).isoformat(),
                        "open": px, "high": px, "low": px, "close": px})
        return out
    db3 = Path(td) / "c3.db"
    seed_store(db3)
    now = dt.datetime.combine(dt.date.fromisoformat(DAY), dt.time(15, 1),
                              tzinfo=session._eastern_tz())     # noqa: SLF001
    out = cf.run_1500(DAY, dry_run=False, db_path=str(db3), fetcher=fetcher,
                      now=now.astimezone(dt.timezone.utc), refresh=False)
    with observations.ObservationStore(str(db3)) as st:
        s15 = cf.stored(st, DAY, GATE_NOW, "1500")
    prices = out.get("prices") or {}
    bars = {u: p for u, p in prices.items() if "bar_end" in p}
    check(out["written"] > 0 and s15["total"][0] is not None and bars
          and all(p["price"] == 100.0 for p in bars.values()),
          f"the 15:00 pass stores instrument-1500 rows ({out['written']}) and reads the bar "
          f"ending 15:00 (14:55's), never the bar still open at 15:01")
    mp = prices.get("mstr") or {}
    check(mp.get("price") == 95.0 and "chain" in mp.get("basis", "")
          and "MSTU" not in out["left_out"],
          f"15:00: MSTR's spot is the newest chain at or before 15:00 (12:30 ET, "
          f"{mp.get('price')}), not the 15:40 capture")
    check("older than 180 minutes" in out["left_out"].get("CONL", ""),
          f"15:00: COIN's newest chain by 15:00 (11:00 ET) is past the 180-minute "
          f"allowance, so CONL is left out and named: {out['left_out'].get('CONL', '')[:70]}")
    check("MSTR" not in calls and "COIN" not in calls and "SNDK" not in calls
          and len(calls) == sum(1 for x in CFG["underlyings"].values() if x.get("yahoo")),
          f"only basket symbols are read intraday (D33): {len(calls)} reads, no MSTR, COIN "
          f"or SNDK")
    return db3


# ---------------------------------------------------------------------------
def group_d(td: str, db: Path) -> None:
    head("D. THE PRINTS")
    from daily_cascade import close_flow_block as cfb
    with observations.ObservationStore(str(db)) as st:
        sub, rows = cfb.close_subsection(st, DAY, GATE_NOW)
    t = sub["table"]
    check(t["columns"] == cfb.COLUMNS and t["rows"][-1][0] == "Total"
          and len(t["rows"]) == len(CFG["buckets"]) + 1
          and all(r[3] != "—" for r in t["rows"][-1:]),
          "the close's table: the 16:45 and 15:00 estimates by bucket, $bn and % of ADV, "
          "and the total")
    ml = sub.get("mechanical_line") or ""
    check("dealer hedging: not yet combined" in ml and ml.startswith("Mechanical close flow"),
          f"the one line: {ml}")
    check(rows and all(r["instrument"] == "1645" for r in rows),
          "the block hands the close its 16:45 rows to store")
    fired = any("FIRED" in x for x in sub["lines"])
    check(not fired and not any("Close-flow flag" in x for x in sub["lines"]),
          "the flag's line prints only when it fired (the fixture's 15:00 total is small)")
    # A fired 15:00 total prints its line (its own store: the pass above stored
    # a later 15:00 vintage in the first).
    dbf = Path(td) / "f.db"
    seed_store(dbf)
    with observations.ObservationStore(str(dbf)) as st:
        st.write_many([{"registry_key": "calc.close_flow.total", "instrument": "1500",
                        "observed_at": DAY, "available_at": "2026-11-06T20:02:00+00:00",
                        "value": -52e9, "source": "close_flow"}])
        sub2, _ = cfb.close_subsection(st, DAY, GATE_NOW)
    check(any("FIRED (selling into the close)" in x for x in sub2["lines"]),
          "a 15:00 total of -$52bn prints the flag's line, selling into the close")
    check(cfb.mechanical_line(None).endswith("dealer hedging: not yet combined."),
          "with no estimate the line still says dealer hedging is not yet combined")
    # The Weekly: the week's sessions, largest first; the Monthly's five.
    dbw = Path(td) / "w.db"
    wk = weekdays(5, DAY)
    vals = [5e9, -30e9, 12e9, -1e9, 20e9]
    with observations.ObservationStore(str(dbw)) as st:
        st.write_many([{"registry_key": "calc.close_flow.total", "instrument": "1645",
                        "observed_at": d, "available_at": f"{d}T21:50:00+00:00",
                        "value": v, "source": "close_flow"} for d, v in zip(wk, vals)])
        ws = cfb.period_subsection(st, GATE_NOW, "weekly")
        ms = cfb.period_subsection(st, GATE_NOW, "monthly")
    order = [r[1] for r in ws["table"]["rows"]]
    check(order == ["-30.0", "+20.0", "+12.0", "+5.0", "-1.0"],
          f"the Weekly: the week's five sessions, largest first ({order})")
    check(ms is not None and len(ms["table"]["rows"]) <= 5
          and "five largest" in ms["title"],
          "the Monthly reads the same table, its five largest")
    src = {p: (REPO / p).read_text(encoding="utf-8") for p in
           ("daily_cascade/stack.py", "daily_cascade/weekly_stack.py",
            "daily_cascade/stack_close.py", "daily_cascade/morning_payload.py",
            "daily_cascade/morning_render.py", "daily_cascade/morning_anchor.py")}
    check("close_flow_block.close_subsection" in src["daily_cascade/stack.py"]
          and "close_flow_block.period_subsection(st, now, cadence)" in src["daily_cascade/weekly_stack.py"]
          and "_close_flow_rows" in src["daily_cascade/stack_close.py"],
          "the close builds and stores it; the Weekly and the Monthly print the period table")
    check(not any("close_flow" in src[p] for p in src if "morning" in p),
          "nothing in the 07:00 anchor")


# ---------------------------------------------------------------------------
def group_e() -> None:
    head("E. THE ROSTER, THE SECURITY MASTER AND THE BLOCKLIST")
    from altdata.security_master import Master
    m = Master()
    funds = CFG["funds"]
    bad = []
    for f in funds:
        try:
            e = m.resolve(f["ticker"], "ticker")
            ids = e["identifiers"]
            if (e["asset_class"] != "etf" or ids.get("yahoo") != f["ticker"]
                    or ids.get("store_key") != f"levetf.aum:{f['ticker']}"):
                bad.append(f["ticker"])
        except Exception as exc:                                # noqa: BLE001
            bad.append(f"{f['ticker']} ({exc})")
    check(not bad, f"every one of the {len(funds)} funds is in the Security Master as an "
                   f"etf with yahoo and store_key identifiers" + (f": {bad}" if bad else ""))
    tick = {f["ticker"] for f in funds}
    named = {"SPXL", "SPXS", "TQQQ", "SQQQ", "SOXL", "SOXS", "UPRO", "QLD", "SSO", "SDS",
             "TNA", "TZA", "NVDL", "TSLL", "CONL", "MSTU", "MSTZ"}
    check(named <= tick, f"the paste's named funds are on the roster ({len(named)})")
    ex = {t for x in CFG["excluded"] for t in x["tickers"]}
    check("UVXY" not in tick and "UVXY" in ex, "UVXY excluded as a volatility product")
    check({f["leverage"] for f in funds} <= {3, 2, -1, -2, -3}
          and all(f["underlying"] in CFG["underlyings"] for f in funds)
          and all(f["bucket"] in cf.bucket_ids(CFG) for f in funds),
          "every leverage in {3, 2, -1, -2, -3}; every underlying and bucket declared")
    check({"semiconductors", "nasdaq_100", "sp_500", "russell_2000", "single_stocks"}
          <= set(cf.bucket_ids(CFG)),
          "the buckets: semiconductors, Nasdaq 100, S&P 500, Russell 2000, single stocks")
    check(all(f.get("gap") for f in funds if f.get("method") == "gap"),
          "every gap fund carries its reason (V-98b)")
    from register import instruments
    rs = instruments.restrictions()
    check(not [t for t in tick if rs.is_restricted(t)] and not
          [e["identifiers"].get("ticker") for e in m.instruments
           if e["restricted"] and e["identifiers"].get("ticker") in tick],
          "no roster fund is a Brookfield-complex instrument (the blocklist and the master)")
    try:
        le.assert_unrestricted(["SOXL", "BN"])
        ok = False
    except le.Restricted as exc:
        ok = "BN" in str(exc)
    check(ok, "the writer's assertion refuses a planted Brookfield ticker (BN)")

    import register.instruments as ri
    real = ri.restrictions

    def unreadable(*_a, **_k):
        raise RuntimeError("the blocklist file is unreadable")
    ri.restrictions = unreadable
    try:
        le.assert_unrestricted(["SOXL"])
        closed = False
    except le.Restricted:
        closed = True
    finally:
        ri.restrictions = real
    check(closed, "and fails closed: a blocklist that will not load refuses every ticker")
    from altdata.sources import proshares
    ps = {f["ticker"] for f in funds if f["writer"] == "proshares"}
    check(ps == set(proshares.FUNDS),
          "the ProShares funds are the existing writer's FUNDS, extended (USD, ROM): one "
          "key, one writer per issuer, nothing duplicated")


# ---------------------------------------------------------------------------
DIREXION = ("Direxion Daily Semiconductor Bull 3X ETF\nSOXL\nShares Outstanding:100\n\n"
            '"TradeDate","AccountTicker","StockTicker","SecurityDescription","Shares","Price",'
            '"MarketValue","Cusip","HoldingsPercent"\n'
            '"11/6/2026 12:00:00 AM","SOXL","AMD","AMD","1","1","500000000.0000","x","5.0000000000"\n'
            '"11/6/2026 12:00:00 AM","SOXL","NVDA","NVDA","1","1","1000000000.0000","x","10.0000000000"\n'
            '"11/6/2026 12:00:00 AM","SOXL","","SWAP","1","1","100.0000","x","0.0000010000"\n')
DEFIANCE = ("<div>Fund Details</div> <div>Data as of 11/05/2026</div> <div>Net Assets</div>"
            "<div>$254.91M</div> <div>Premium/Discount</div> 0.62% NAV $11.94")
REX = ("<div>Exchange Cboe BZX</div><div>As of 11/04/2026</div> <span>NAV $32.04</span> "
       "NAV Change ($) $2.94 NAV Change (%) 10.12% Closing Price $32.03 Fund Assets "
       "$629,288,957.83 Shares Outstanding 19,646,861")


def group_f() -> None:
    head("F. THE WRITER, ON FIXTURES")
    d, v = le.parse_direxion(DIREXION, "SOXL")
    check(d == PREV and close(v, 1e10),
          f"Direxion: MarketValue x 100 / HoldingsPercent = $10.0bn, observed at the "
          f"session before the file's date ({d})")
    try:
        le.parse_direxion(DIREXION.replace('"10.0000000000"', '"11.0000000000"'), "SOXL")
        ok = False
    except ValueError as exc:
        ok = "disagree" in str(exc)
    check(ok, "Direxion lines that disagree by more than 0.1% are refused")
    d, v = le.parse_granite([{"Position Date": dt.datetime(2026, 11, 6), "Shares Outstanding":
                              100350018, "NAV/Share": 22.441502}], "NVDL")
    check(d == PREV and close(v, 100350018 * 22.441502),
          f"GraniteShares: shares outstanding x NAV/Share, at the session before its "
          f"Position Date (${v / 1e9:.2f}bn)")
    link = le.granite_link('<a href="/media/lurill5v/nvdl_holdings_file_20261105.xls">x</a>',
                           "NVDL")
    check(link.endswith("/media/lurill5v/nvdl_holdings_file_20261105.xls"),
          "GraniteShares: the page's link names the dated workbook")
    d, v = le.parse_rex(REX, "MSTU")
    check(d == "2026-11-04" and close(v, 629288957.83),
          "REX: 'Fund Assets' at the page's own As-of date")
    d, v = le.parse_defiance(DEFIANCE, "MSTX")
    check(d == PREV and close(v, 254.91e6),
          "Defiance (A127b): 'Net Assets $254.91M' at the page's 'Data as of' date")
    gets, sleeps = [], []

    def get(url, timeout=60, max_retries=1):
        gets.append(url)
        return (DIREXION.encode() if "direxion" in url else REX.encode()), {}

    def robots(url):
        if "rexshares" in url:
            return "User-agent: *\nCrawl-delay: 10\nDisallow:\n"
        return "User-agent: *\nDisallow: /holdings/SOXS.csv\n"
    cfg = {"funds": [
        {"ticker": "SOXL", "issuer": "Direxion", "writer": "levered_etf",
         "method": "direxion_holdings", "aum_page": "https://www.direxion.com/holdings/SOXL.csv"},
        {"ticker": "SOXS", "issuer": "Direxion", "writer": "levered_etf",
         "method": "direxion_holdings", "aum_page": "https://www.direxion.com/holdings/SOXS.csv"},
        {"ticker": "MSTU", "issuer": "REX", "writer": "levered_etf",
         "method": "rex_page", "aum_page": "https://www.rexshares.com/mstu/"},
        {"ticker": "MSTZ", "issuer": "REX", "writer": "levered_etf",
         "method": "rex_page", "aum_page": "https://www.rexshares.com/mstz/"},
        {"ticker": "SNXX", "issuer": "Tradr", "writer": "levered_etf", "method": "gap",
         "gap": "no figure", "aum_page": "https://www.tradretfs.com/snxx"}]}
    rows, missed = le.produce(cfg, get=get, get_text=robots, now=GATE_NOW,
                              sleep=sleeps.append, is_restricted=lambda t: False)
    check("SOXS" in missed and "robots.txt disallows" in missed["SOXS"]
          and not any("SOXS" in g for g in gets),
          "a robots disallow is a refusal for that fund, never requested")
    check(sorted(r["instrument"] for r in rows) == ["MSTU", "MSTZ", "SOXL"]
          and all(r["registry_key"] == "levetf.aum" and r["available_at"] == GATE_NOW
                  for r in rows)
          and {r["source"] for r in rows} == {"levered_etf:direxion", "levered_etf:rex"},
          "the rows: levetf.aum per fund, available at the pull, source levered_etf:<issuer>")
    check(len(gets) == 3 and "SNXX" in missed and not any("tradr" in g for g in gets),
          "one request per page; a gap is never requested, and named")
    check(sleeps and max(sleeps) > 9.0, f"REX's Crawl-delay is honoured ({max(sleeps or [0]):.1f} s)")


# ---------------------------------------------------------------------------
def group_g() -> None:
    head("G. HYGIENE")
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    mets = reg["metrics"]
    keys = cf.store_keys()
    check(all(k in mets and mets[k].get("trigger_eligible") is False for k in keys),
          f"the {len(keys)} calc.close_flow keys registered, trigger-ineligible")
    barred = [k for b in reg["market_state_barred"] for k in b["keys"]]
    check("calc.close_flow.*" in barred, "calc.close_flow.* barred from the market-state object")
    lev = [b for b in reg["market_state_barred"] if "levetf.aum" in b["keys"]
           and "SOXL" in (b.get("instruments") or [])]
    check(lev and set(lev[0]["instruments"]) >= {f["ticker"] for f in CFG["funds"]
                                                 if f["writer"] == "levered_etf"},
          "the roster's new levetf.aum instruments are barred too")
    check(set(mets["levetf.aum"].get("sources") or []) == {"proshares", "levered_etf"},
          "levetf.aum: one key, two writers declared")
    ms = (REPO / "config" / "market_state.yaml").read_text(encoding="utf-8")
    rg = (REPO / "regime.py").read_text(encoding="utf-8")
    check("close_flow" not in ms and "close_flow" not in rg,
          "named in neither config/market_state.yaml nor regime.py")
    st = yaml.safe_load((REPO / "config" / "setups.yaml").read_text(encoding="utf-8"))
    s = st["setups"].get("c_dth1_close_flow_reversal") or {}
    check(s.get("status") == "draft" and s.get("book") == "C"
          and "do not fade the move into the close" in s.get("mechanism", "")
          and "next morning's reversal" in s.get("mechanism", ""),
          "98.3: the DTH-1 setup is a Book C draft, in the order's words")
    at = yaml.safe_load((REPO / "config" / "alpha_tells.yaml").read_text(encoding="utf-8"))
    check("c_dth1_close_flow_reversal" in at["setups_skipped"],
          "the lab does not import the draft as a hypothesis (rights unchanged)")
    from altdata import feeds
    ew = list(feeds.EXTERNAL_WRITERS)
    check("levered_etf" in ew and ew.index("levered_etf") == ew.index("proshares") + 1,
          "levered_etf on the external roster (the EOD pass, after the prices), after proshares")
    dr = (REPO / "scripts" / "deploy_remote.sh").read_text(encoding="utf-8")
    m = re.search(r'DEPLOY_TIMERS="(.*?)"', dr, re.S)
    check(m and "chester-close-flow.timer" not in m.group(1)
          and (REPO / "deploy/systemd/chester-close-flow.timer").exists(),
          "the 15:00 timer ships, held out of DEPLOY_TIMERS (the operator enables it)")
    w = (REPO / "scripts" / "run_close_flow.sh").read_text(encoding="utf-8")
    calls = re.findall(r'"\$PY" -m (\S+)', w)
    check(calls == ["altdata.session", "altdata.close_flow"]
          and "estimate --slot 1500" in w and w.rstrip().endswith("exit 0"),
          "the wrapper's one call (after the calendar guard), non-fatal")
    import gate_list
    check(any("validate_item_116" in g for g in gate_list.gates("code")),
          "the gate is on the code-gate list (GATE_KIND, S1)")


# ---------------------------------------------------------------------------
# A128: the event-study utility, the close-flow ledger, item 118
# ---------------------------------------------------------------------------
CF_PREREG_SHA = "2e55de27a48183fc7ba752be94d11b035a735f1402928eb439233580124cd68f"
HB_PREREG_SHA = "cdadf38f9f3a45732a38a068453d4a912fc0a18116c1222199a3a569cb05de84"


def sha_lf(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def group_h() -> None:
    head("H. THE EVENT-STUDY UTILITY (Batch 16 item 91(a); A128)")
    from altdata import event_study as es
    days = weekdays(10, "2026-11-06")
    px = [100.0, 101.0, 99.0, 102.0, 104.0, 103.0, 105.0, 106.0, 108.0, 107.0]
    s = list(zip(days, px))
    w = es.window(s, days[3], 2, 3)
    check(w["complete"] and w["values"] == {-2: 101.0, -1: 99.0, 0: 102.0, 1: 104.0,
                                            2: 103.0, 3: 105.0},
          "window: the values at offsets -2..+3 in sessions, complete")
    check(not es.window(s, days[8], 1, 3)["complete"]
          and es.window(s, "2026-11-07", 1, 1)["reason"],
          "a window past the series' end is incomplete; a day not in the series says so")
    v = es.views(s, days[3], 2, 2)
    check(close(v["pre"], 99 / 101 - 1) and close(v["day0"], 102 / 99 - 1)
          and close(v["post"][1], 104 / 102 - 1) and close(v["post"][2], 103 / 102 - 1),
          "views: pre (-2 close to -1), day 0 (-1 to 0), post (0 to +k), by hand")
    check(close(es.forward(s, days[3], 5), 108 / 102 - 1) and es.forward(s, days[8], 5) is None,
          "forward: the event close to the k-th session's; None (pending) past the end")
    a = es.average([0.01, -0.02, 0.03, None])
    check(a["n"] == 3 and close(a["mean"], 0.02 / 3) and close(a["median"], 0.01)
          and close(a["share_negative"], 1 / 3)
          and es.average([None])["n"] == 0 and es.average([])["mean"] is None,
          "average: n, mean, median, share negative over the non-missing values; empty is "
          "None, never zero")
    st_ = es.study(s, [days[1], days[7]], (1, 5))
    check(close(st_["average"][1]["mean"], ((99 / 101 - 1) + (108 / 106 - 1)) / 2)
          and st_["average"][5]["n"] == 1 and st_["pending"][5] == 1,
          "study: the cross-event average at each horizon, a pending window left out and "
          "counted")
    br = es.base_rate(s, (1,))
    check(br[1]["n"] == 9 and close(br[1]["mean"],
                                    sum(px[i + 1] / px[i] - 1 for i in range(9)) / 9),
          "base rate: the same average over every session whose window has closed")
    b = list(zip(days, [50.0 + i for i in range(10)]))
    c = es.compare(s, b, [days[2]], (1,))
    check(close(c["rows"][0][1]["spread"], (102 / 99 - 1) - (53 / 52 - 1)),
          "compare: two assets over the same events, a minus b")
    import ast
    tree = ast.parse((REPO / "altdata" / "event_study.py").read_text(encoding="utf-8"))
    mods = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)} | \
           {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    check(mods <= {"__future__", "math", "typing"},
          f"pure arithmetic: no store, network or clock import ({sorted(mods)})")
    hits = [p.name for p in (REPO / "altdata").rglob("*.py")
            if p.name != "event_study.py"
            and re.search(r"^def (window|views|forward)\(series", p.read_text(encoding="utf-8"), re.M)]
    check(not hits, "one utility: no second window/views/forward implementation" +
          (f" ({hits})" if hits else ""))


def _cf_fixture(n_stored: int = 20) -> tuple[dict, list[str]]:
    days = weekdays(30, "2026-11-06")
    closes = {"spy": [(d, 100.0 + i) for i, d in enumerate(days)],
              "qqq": [(d, 200.0 + 2 * i) for i, d in enumerate(days)],
              "smh": [(d, 300.0 + 3 * i) for i, d in enumerate(days)],
              "iwm": [(d, 50.0 + 0.5 * i) for i, d in enumerate(days)]}
    opens = {e: [(d, v + 0.5) for d, v in ser] for e, ser in closes.items()}
    vals = [0.1 * (i + 1) for i in range(20)]
    vals[19] = -2.0
    pct = list(zip(days[5:25], vals))[20 - n_stored:]
    total = [(d, v * 1e9) for d, v in pct]
    buckets = {"semiconductors": [], "nasdaq_100": [(days[23], 5e9)],
               "sp_500": [(days[23], 1e9), (days[24], -8e9)], "russell_2000": []}
    bars = {"spy": {days[24]: {"15:30": {"open": 120.0, "close": 119.0},
                               "15:55": {"open": 119.0, "close": 118.8}}}}
    return ({"mode": "store", "closes": closes, "opens": opens, "bars": bars,
             "pct": pct, "total": total, "buckets": buckets}, days)


def group_i() -> None:
    head("I. ITEM 116'S CALIBRATION LEDGER (98.2; A128)")
    from altdata import ledgers as L
    from altdata.ledgers import close_flow_116 as cfl
    pre = REPO / cfl.PREREG
    check(pre.exists() and sha_lf(pre) == CF_PREREG_SHA
          and CFG["ledger"]["preregistration_sha256"] == CF_PREREG_SHA,
          f"the pre-registration's SHA-256 is held: {CF_PREREG_SHA[:16]}... (the gate and "
          f"config/levered_etf.yaml)")
    txt = pre.read_text(encoding="utf-8")
    check(all(w in txt for w in ("top decile", "accruing (n=k of 20)", "last-30-minute",
                                 "gap at the next open", "5-day forward", "None stated",
                                 "seed, order's figure", "estimate, unconfirmed (V-98a open)")),
          "it states the event, the measures, no pass rule and the two seeds, before the code")
    s19, _ = _cf_fixture(19)
    r19 = cfl.study(s19)
    check(r19["n"] == 0 and r19["verdict"].startswith("ACCRUING (n=19 of 20)")
          and any("Accruing (n=19 of 20)" in b for b in r19["body"]),
          "19 stored sessions: 'accruing (n=19 of 20)', no decile and no event")
    s, days = _cf_fixture(20)
    cut, evs, k = cfl.events(s["pct"])
    check(k == 20 and close(cut, 1.81) and evs == [days[23], days[24]],
          f"20 stored: the cut is the 90th percentile of |% of ADV| (1.81 by hand), the "
          f"events the two sessions at or above it ({evs})")
    r = cfl.study(s)
    ep = {e["session"]: e for e in r["episodes"]}
    e23, e24 = ep[days[23]], ep[days[24]]
    check(e23["index"] == "QQQ" and e24["index"] == "SPY",
          "each event's index is its largest index bucket's ETF (Nasdaq 100 -> QQQ, "
          "S&P 500 -> SPY)")
    check(close(e24["index_last30"], 118.8 / 120.0 - 1)
          and close(e24["index_gap"], (125.0 + 0.5) / 124.0 - 1)
          and close(e24["index_fwd1"], 125.0 / 124.0 - 1)
          and close(e24["index_fwd5"], 129.0 / 124.0 - 1)
          and e24["gap_against_flow"] is True,
          "the measures by hand: the last 30 minutes from the 5-minute bars, the next "
          "open, +1 and +5; a selling day's up-gap is against the flow")
    check(e23["index_last30"] is None and e23["index_fwd5"] is not None,
          "an instrument with no bars that session prints no last 30 minutes, never a guess")
    seeds = [e for e in r["episodes"] if e["mark"].startswith("seed")]
    check([e["session"] for e in seeds] == ["2026-06-05", "2026-11-05"]
          and seeds[0]["flow_usd"] == -55e9 and seeds[1]["flow_usd"] == -52e9
          and all(e["mark"].startswith("seed, order's figure") for e in seeds)
          and "estimate, unconfirmed" in seeds[1]["mark"]
          and seeds[1]["index"] == "SMH" and seeds[0]["index"] == "SPY",
          "rows one and two are the seeds: the order's -$55bn and -$52bn, marked 'seed, "
          "order's figure', 5 Nov 'estimate, unconfirmed'; never counted as events")
    check(r["n"] == 2 and r["pass_rule"].startswith("none stated")
          and r["verdict"] == L.NO_GATE and "grants nothing" in r["rights"],
          "n counts the events only; no pass rule, no verdict by judgment; grants nothing")
    md, csv_path = L.write_ledger(dict(r, source_mode="laptop run, public sources",
                                       sources=["fixture"]), TD116, "2026-11-06")
    check(md.name == "close-flow-ledger-2026-11-06.md" and csv_path.exists(),
          "written as docs/ledgers/close-flow-ledger-<date>.md with its CSV")
    reg = L.registered_rule("close-flow")
    check(reg and reg.startswith("none stated") and reg == cfl.PASS_RULE,
          "the first edition on file registers 'none stated' (python -m altdata.ledgers "
          "run close-flow)")
    from altdata.ledgers.__main__ import ITEMS
    check(ITEMS.get("close-flow") == "close_flow_116"
          and ITEMS.get("hb-lv-divergence") == "hb_lv_118",
          "both ledgers on the ledgers CLI")


def _hb_series(spx_on_1104: float = 1.01) -> tuple[dict, list[str]]:
    days = weekdays(60, "2026-12-31")
    ev = {days[10], "2026-11-04"}
    spx, sphb, splv = [], [], []
    p, r = 4000.0, 2.0
    for i, d in enumerate(days):
        if i:
            if d == "2026-11-04":
                p *= spx_on_1104
                r *= 0.97
            elif d in ev:
                p *= 1.01
                r *= 0.97
            else:
                p *= 1.001
        spx.append((d, p))
        sphb.append((d, 50.0 * r))
        splv.append((d, 50.0))
    return {"spx": spx, "sphb": sphb, "splv": splv}, days


def _seed_hb(db: Path, series: dict) -> None:
    rows = []
    for name, key in (("spx", "yfinance.mkt_gspc"), ("sphb", "yfinance.mkt_sphb"),
                      ("splv", "yfinance.mkt_splv")):
        for d, v in series[name]:
            rows.append({"registry_key": key, "instrument": None, "observed_at": d,
                         "available_at": f"{d}T21:05:00+00:00", "value": v,
                         "source": "yfinance"})
    with observations.ObservationStore(str(db)) as st:
        st.write_many(rows)


def group_j(td: str) -> None:
    head("J. ITEM 118: SPHB/SPLV, THE CROWDING MEMBER, THE FLAG, ITS LEDGER (A128)")
    from altdata import hb_lv
    from altdata.ledgers import hb_lv_118 as hbl
    from altdata.security_master import Master
    from altdata.sources import yfinance_source as yf
    m = Master()
    ok = all(m.resolve(t, "yahoo")["asset_class"] == "etf"
             and m.resolve(t, "yahoo")["identifiers"].get("store_key") == f"yfinance.mkt_{t.lower()}"
             for t in ("SPHB", "SPLV"))
    check(ok and yf.SYMBOLS.get("SPHB") == "mkt_sphb" and yf.SYMBOLS.get("SPLV") == "mkt_splv",
          "SPHB and SPLV are in the Security Master (etf, yahoo, store_key) and the basket")
    rb = yf.resolve_basket({"SPHB": "mkt_sphb", "SPLV": "mkt_splv"})
    check(rb == {"SPHB": "mkt_sphb", "SPLV": "mkt_splv"},
          "the basket resolves them through the master (resolve_basket)")
    hc = hb_lv.config()
    cr = yaml.safe_load((REPO / "config" / "crowding.yaml").read_text(encoding="utf-8"))
    check(cr["gauge"]["built"] is False and "hb_lv" in cr["members"]
          and hc["keys"] == {"ratio": "calc.hb_lv_ratio", "change_1d": "calc.hb_lv_ratio_chg_1d"},
          "the crowding family's config: the member declared, the 89(a) gauge 'not built'")
    pre = REPO / hc["ledger"]["preregistration"]
    check(pre.exists() and sha_lf(pre) == HB_PREREG_SHA
          and hc["ledger"]["preregistration_sha256"] == HB_PREREG_SHA,
          f"the pre-registration's SHA-256 is held: {HB_PREREG_SHA[:16]}... (the gate and "
          f"config/crowding.yaml)")
    check(hb_lv.flag(0.5, -2.0) is True and hb_lv.flag(0.49, -3.0) is False
          and hb_lv.flag(1.0, -1.99) is False and hb_lv.flag(None, -3.0) is None,
          "the flag: the S&P up 0.5% or more with SPHB/SPLV down 2% or more (both edges)")
    series, days = _hb_series()
    db = Path(td) / "hb.db"
    _seed_hb(db, series)
    with observations.ObservationStore(str(db)) as st:
        rows = hb_lv.compute_rows(st, GATE_NOW)
        ratio = {r["observed_at"]: r for r in rows if r["registry_key"] == "calc.hb_lv_ratio"}
        chg = {r["observed_at"]: r for r in rows if r["registry_key"] == "calc.hb_lv_ratio_chg_1d"}
        f = hb_lv.for_session(st, "2026-11-04", GATE_NOW)
        q = hb_lv.for_session(st, days[12], GATE_NOW)
        built = {"misfit": {"items": [{"key": "misfit:none", "text": "x"}]}}
        from daily_cascade import hb_lv_block
        hb_lv_block.close_extras(built, st, "2026-11-04", GATE_NOW)
        quiet = {"misfit": {"items": [{"key": "misfit:none", "text": "x"}]}}
        hb_lv_block.close_extras(quiet, st, days[12], GATE_NOW)
    check(close(ratio["2026-11-04"]["value"], dict(series["sphb"])["2026-11-04"] / 50.0, 1e-6)
          and close(chg["2026-11-04"]["value"], -3.0, 1e-4)
          and dt.datetime.fromisoformat(ratio["2026-11-04"]["available_at"])
          == dt.datetime.fromisoformat("2026-11-04T21:05:00+00:00"),
          "calc.hb_lv_ratio and its 1-day change by hand (-3.0%), available at the later close")
    check(f["fired"] is True and "+1.0%" in f["line"] and "-3.0%" in f["line"]
          and "No rights until the backtest" in f["line"],
          f"a fired day's line carries both figures and 'no rights until the backtest': "
          f"{(f['line'] or '')[:70]}...")
    items = built["misfit"]["items"]
    check([i["key"] for i in items] == ["misfit:hb_lv_divergence"]
          and quiet["misfit"]["items"][0]["key"] == "misfit:none" and q["fired"] is False,
          "it prints in What doesn't fit on a fired day only (replacing 'nothing open'); a "
          "quiet day adds nothing")
    r = hbl.study(series)
    ev = [e["session"] for e in r["episodes"]]
    e10 = next(e for e in r["episodes"] if e["session"] == days[10])
    check(r["n"] == 2 and sorted(ev) == sorted([days[10], "2026-11-04"])
          and close(e10["spx_fwd_1"], 0.001, 1e-6),
          f"the backtest: the flag's events by hand (2) and their forward returns through "
          f"the utility")
    check(r["v100a"]["holds"] and any(e["mark"] == "the order's day (V-100a checked)"
                                      for e in r["episodes"])
          and "V-100a holds" in r["body"][0],
          "V-100a holds on the fixture: 4 Nov is the order's first row, marked")
    s2, _ = _hb_series(spx_on_1104=1.003)
    r2 = hbl.study(s2)
    check(r2["v100a"]["holds"] is False and "NOT written" in r2["body"][0]
          and "2026-11-04" not in [e["session"] for e in r2["episodes"]],
          "V-100a fails when the S&P closed up less than 0.5%: the row is NOT written, "
          "and the edition says so")
    check(r["pass_rule"].startswith("none stated") and "grants nothing" in r["rights"],
          "no pass rule set; grants nothing")
    from altdata import ledgers as L
    reg = L.registered_rule("hb-lv-divergence")
    check(reg and reg == hbl.PASS_RULE, "the first edition on file registers 'none stated'")
    regm = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    barred = [k for b in regm["market_state_barred"] for k in b["keys"]]
    check(all(k in regm["metrics"] and regm["metrics"][k]["trigger_eligible"] is False
              and k in barred for k in ("calc.hb_lv_ratio", "calc.hb_lv_ratio_chg_1d"))
          and "yfinance.mkt_sphb" in barred and "yfinance.mkt_splv" in barred,
          "the keys registered, trigger-ineligible and barred from the market-state object")
    ms = (REPO / "config" / "market_state.yaml").read_text(encoding="utf-8")
    rg = (REPO / "regime.py").read_text(encoding="utf-8")
    check("hb_lv" not in ms and "hb_lv" not in rg,
          "named in neither config/market_state.yaml nor regime.py")


def main() -> int:
    global TD116
    pin_clock()
    print(f"the gate's clock is pinned to {GATE_NOW}")
    print(f"{LINE}\nITEM 116: THE LEVERED-ETF CLOSE FLOW (A127)\n{LINE}")
    td = gate_tmp.mkdtemp("item116_")
    TD116 = Path(td) / "ledgers"
    group_a()
    group_b()
    db = group_c(td)
    group_d(td, db)
    group_e()
    group_f()
    group_g()
    group_h()
    group_i()
    group_j(td)
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
