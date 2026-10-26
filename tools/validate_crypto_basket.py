#!/usr/bin/env python3
"""
Validation gate for the crypto basket tier (the crypto basket brief, ruled
12 Oct 2026; config/crypto_basket.yaml; altdata/crypto_basket.py;
altdata/sources/llama.py).

    python tools/validate_crypto_basket.py

On temporary stores and captured fixtures (tests/fixtures/llama/). No gate
fetches: the network is refused for the whole run, and the live store is never
opened.

  A  THE CONFIG. Twelve names; every one has a thesis, a falsifier, the odds dated
     2026-10-12 with their source, and a source per series. Every quoted field is
     the operator's document, verbatim; the odds equal the document's table, so a
     revised odds field fails here -- the model never writes one. The Yahoo
     symbols are the resolved ones, never the bare pair that is another coin.
  B  THE SERIES. The DefiLlama parsers on the captured fixtures; a day is written
     only once it has ended; the coin service's supply; every key the basket
     names is registered with a family and a long window; a re-run writes nothing.
  C  THE GRADER, on a fixture store with one of each state: holds, strained,
     failed, not measured -- each with its rule printed beside it.
  D  THE WEEKLY LINE fires on each of the four event kinds -- a 2.5-sigma move, a
     falsifier crossed, a dated event due, a scan item -- and is silent otherwise.
  E  THE RESTATEMENT (decision 3): an undated odds row is refused; a move without
     a reason is refused; a move with no measurable change is refused; nothing
     restates outside the Quarterly; "unchanged -- no measurable moved" without
     asking the model; the reference column byte-identical across two quarters;
     each restatement an `alt_asset` entry labelled "model estimate", in the
     dry-run namespace.
  F  THE BLOCKS. At most six columns; the figure budget and the readability rules
     on the new blocks; the consistency gate reads their tagged moves; the Monthly
     inserts the basket after the classics, which are unchanged.
  G  WIRING. The writers' unit and timer, DEPLOY_TIMERS, the registry blocks and
     sources, the §4.6 amendment for PRL.
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import copy
import datetime as dt
import json
import math
import os
import re
import sys
from pathlib import Path

import os as _gt_os                                            # noqa: E402
import sys as _gt_sys                                          # noqa: E402
_gt_dir = _gt_os.path.dirname(_gt_os.path.abspath(__file__))
_gt_sys.path.insert(0, _gt_dir if _gt_os.path.basename(_gt_dir) == "tools"
                    else _gt_os.path.join(_gt_dir, "tools"))
from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_TMP = gate_mkdtemp(prefix="validate_crypto_basket_")
os.environ["CHESTER_DB"] = os.path.join(_TMP, "never.sqlite")
os.environ["CHESTER_DRYRUN_DIR"] = os.path.join(_TMP, "dryrun")
os.environ.setdefault("CHESTER_STATE_DIR", _TMP)

# NO GATE FETCHES. Any HTTP call in this run is a failure, not a slow pass.
import requests  # noqa: E402


def _refuse(*a, **k):
    raise RuntimeError("validate_crypto_basket made a network call")


requests.get = requests.post = _refuse                       # type: ignore

import yaml  # noqa: E402
from altdata import crypto_basket as cb, derived, observations  # noqa: E402
from altdata.sources import llama, yfinance_source as yf  # noqa: E402

PASS = FAIL = 0
LINE = "=" * 78
FIX = REPO / "tests" / "fixtures" / "llama"
DOC = REPO / "docs" / "scans" / "crypto-basket-summary-2026-10-12.md"
AS_OF = "2027-06-30T00:00:00+00:00"
NAMES = ["SKY", "LDO", "SYRUP", "AAVE", "AERO", "TAO", "MORPHO", "UNI", "ONDO",
         "KAS", "VVV", "PRL"]


def check(c: bool, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def head(t: str) -> None:
    print(f"{LINE}\n{t}\n{LINE}")


def fx(name: str):
    return json.loads((FIX / f"{name}.json").read_text(encoding="utf-8"))


def days(first: str, n: int) -> list[str]:
    d = dt.date.fromisoformat(first)
    return [(d + dt.timedelta(days=i)).isoformat() for i in range(n)]


def seed(st, key, pts, instrument=None):
    st.write_many([{"registry_key": key, "instrument": instrument, "observed_at": d,
                    "available_at": f"{d}T23:00:00+00:00", "value": float(v),
                    "source": "synthetic", "availability_kind": "ingest_instant"}
                   for d, v in pts])


def alternating(first: str, n: int, start: float = 100.0, jump_at=None,
                jump: float = 0.0):
    """A price that alternates +1% / -1%: every ordinary day is |z| = 1, so a
    quiet store can never flag by chance; `jump_at` adds one large move."""
    out, v = [], start
    for i, d in enumerate(days(first, n)):
        v *= (1.01 if i % 2 == 0 else 1 / 1.01)
        if jump_at and d == jump_at:
            v *= 1 + jump
        out.append((d, v))
    return out


def unescape(s: str) -> str:
    return re.sub(r"\\([$<>#*_\[\]])", r"\1", s)


# ---------------------------------------------------------------------------
def group_a() -> dict:
    head("A. THE CONFIG -- quoted, dated, the operator's odds")
    cfg = cb.config()
    n = cb.names(cfg)
    check(list(n) == NAMES, f"twelve names, in the brief's order ({list(n)})")
    doc = unescape(DOC.read_text(encoding="utf-8"))
    flat = re.sub(r"\s+", " ", doc)
    table = {}
    for ln in doc.splitlines():
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) == 7 and re.search(r"\((\w+)\)", cells[1]) and cells[0] != "#":
            table[re.search(r"\((\w+)\)", cells[1]).group(1)] = cells
    missing = {k: [f for f in ("thesis", "falsifier", "odds", "us_access",
                               "case_for", "case_against", "measurable", "yahoo",
                               "llama_coin") if not v.get(f)]
               for k, v in n.items()}
    check(not any(missing.values()),
          f"every name has a thesis, a falsifier, odds, US access, the case for and "
          f"against, a measurable and a source per series "
          f"({ {k: m for k, m in missing.items() if m} })")
    check(all(str(v["odds"].get("dated")) == "2026-10-12"
              and v["odds"].get("source") == "docs/scans/crypto-basket-summary-2026-10-12.md"
              for v in n.values()),
          "every odds row is dated 2026-10-12 and names the document as its source")
    quoted = []
    for k, v in n.items():
        for f in ("thesis", "case_for", "case_against"):
            quoted.append((k, f, v[f] in flat))
        quoted.append((k, "falsifier.quoted", v["falsifier"]["quoted"] == v["case_against"]))
        quoted.append((k, "measurable.pays", v["measurable"]["pays"] == table[k][3]))
        quoted.append((k, "us_access", v["us_access"] == table[k][4]))
    bad = [(k, f) for k, f, ok in quoted if not ok]
    check(not bad, f"every quoted field is the document's text, verbatim -- the "
                   f"thesis, the case for and against, what pays the token, US "
                   f"access ({len(quoted)} fields; mismatched: {bad})")
    odds_bad = [k for k, v in n.items()
                if (v["odds"]["operator_10x"], v["odds"]["operator_100x"])
                != (table[k][5], table[k][6])]
    check(not odds_bad, f"the odds equal the document's table for all twelve, so a "
                        f"revised odds field fails this gate ({odds_bad})")
    src = (REPO / "altdata" / "crypto_basket.py").read_text(encoding="utf-8")
    check("crypto_basket.yaml" in src and not re.search(
              r"(write_text|open\([^)]*['\"]w)[^\n]*CONFIG", src)
          and "yaml.safe_dump" not in src and "yaml.dump" not in src,
          "nothing in the basket module writes the config: the model never "
          "writes or revises an odds field")
    resolved = {k: v["yahoo"] for k, v in n.items()}
    check(resolved["SKY"] == "SKY33038-USD" and resolved["AERO"] == "AERO29270-USD"
          and resolved["PRL"] == "PRL41876-USD"
          and not {"SKY-USD", "AERO-USD", "PRL-USD"} & set(resolved.values()),
          "the Yahoo symbols are resolved: never SKY-USD (Skycoin), AERO-USD "
          "(Aerovek) or PRL-USD (The Parallel)")
    check(resolved["TAO"] == "TAO22974-USD" and resolved["UNI"] == "UNI7083-USD"
          and resolved["MORPHO"] == "MORPHO34104-USD"
          and resolved["VVV"] == "VVV35509-USD",
          "and the four Yahoo serves only under a suffixed id")
    f = {k: v["falsifier"] for k, v in n.items()}
    check(f["ONDO"]["measured"] and f["ONDO"]["threshold"] == 2.0
          and f["ONDO"]["date"] == "2029-01-31"
          and f["ONDO"]["series"] == "llama.supply_ondo",
          "ONDO: supply doubling by January 2029, measured on llama.supply_ondo")
    check(f["AERO"]["measured"] and f["AERO"]["event_date"] == "2026-10-21"
          and f["AERO"]["series"] == "llama.fees_aero",
          "AERO: the six-chain launch of 21 Oct 2026, graded on its fees")
    check(f["MORPHO"]["kind"] == "switch"
          and f["MORPHO"]["series"] == "llama.holders_revenue_morpho",
          "MORPHO: the fee switch, read from the value reaching holders")
    check(not f["KAS"]["measured"] and "not listed on DefiLlama" in f["KAS"]["reason"],
          "KAS: fees, not measured -- Kaspa is not on DefiLlama, said so")
    check(f["PRL"]["kind"] == "signposts" and "S1-S8" in f["PRL"]["signposts"]
          and (n["PRL"].get("demoted") or {}).get("coin_page") is False
          and (n["PRL"].get("demoted") or {}).get("to") == "basket",
          "PRL: SR-10's S1-S8 as its falsifier set, demoted to basket, no coin page")
    unmeasured = [k for k, v in f.items() if not v["measured"]]
    check(all(f[k].get("reason") for k in unmeasured),
          f"every unmeasured falsifier says why ({', '.join(unmeasured)})")
    keys = [v["measurable"]["key"] for v in n.values() if v["measurable"]["key"]]
    keys += [v.get("series") for v in f.values() if v.get("series")]
    keys += [cb.price_key(k) for k in n] + [f"llama.mcap_{k.lower()}" for k in n]
    unreg = [k for k in keys if not derived.registry_entry(k)]
    check(not unreg, f"every series the basket names is registered ({len(keys)} "
                     f"keys; unregistered: {unreg})")
    lens = [k for k in keys if not (derived.registry_entry(k).get("family")
                                    and derived.registry_entry(k).get("long_window"))]
    check(not lens, f"and carries its family and long window ({lens})")
    return cfg


def group_b() -> None:
    head("B. THE SERIES -- DefiLlama's parsers on captured fixtures, no fetch")
    today = "2026-10-12"
    fees = llama.parse_chart(fx("fees_aave"), today)
    raw_last = llama._day(fx("fees_aave")["totalDataChart"][-1][0])
    check(fees and fees[-1][0] < today and all(isinstance(v, float) for _, v in fees),
          f"fees: {len(fees)} days, the last {fees[-1][0]} (raw ends {raw_last}); a "
          f"day is written only once it has ended")
    tvl = llama.parse_protocol_tvl(fx("protocol_aave"), "2026-10-13")
    raw = fx("protocol_aave")["tvl"]
    check(tvl and tvl[-1][0] == "2026-10-12" and llama._day(raw[-1]["date"]) == "2026-10-13",
          "TVL: today's intraday snapshot is held back; the last whole day stands")
    st_all = llama.parse_stable_chart(fx("stable_all"), today)
    st_eth = llama.parse_stable_chart(fx("stable_ethereum"), today)
    check(st_all and st_eth and st_all[-1][1] > st_eth[-1][1] > 0,
          f"S-1: total stablecoin supply {st_all[-1][1] / 1e9:,.0f}bn above "
          f"Ethereum's {st_eth[-1][1] / 1e9:,.0f}bn")
    ct = llama.parse_chain_tvl(fx("chaintvl_all"), today)
    check(ct and ct[-1][1] > 0, "chain TVL parses")
    coins = llama.parse_coins(fx("coins_mcaps"), fx("coins_prices"))
    sky = coins.get("coingecko:sky") or {}
    check(sky.get("supply") and abs(sky["supply"] * sky["price"] - sky["mcap"]) < 1,
          f"the coin service: SKY supply {sky.get('supply', 0) / 1e9:.2f}bn tokens "
          f"= its cap over its own price")
    check("Upgrade to the paid API plan" in (FIX / "raises_paywalled.txt").read_text()
          and "raises" in llama.NOT_SERVED and "emissions" in llama.NOT_SERVED,
          "/raises and /emissions are recorded as not served free, not pulled")
    # The whole writer on fixtures, through a fake fetch.
    one = {"AAVE": cb.names()["AAVE"]}
    calls = []

    def fetch(url, params=None):
        calls.append(url)
        if "/summary/fees/" in url:
            return fx({"dailyFees": "fees_aave", "dailyRevenue": "rev_aave",
                       "dailyHoldersRevenue": "hrev_uniswap"}[params["dataType"]])
        if "/protocol/" in url:
            return fx("protocol_aave")
        if "/prices/current/" in url:
            return fx("coins_prices")
        if "stablecoincharts/all" in url:
            return fx("stable_all")
        if "stablecoincharts/" in url:
            return fx("stable_ethereum")
        if "historicalChainTvl/" in url:
            return fx("chaintvl_ethereum")
        if "historicalChainTvl" in url:
            return fx("chaintvl_all")
        if "/overview/dexs" in url:
            return fx("dexs")
        if "/overview/open-interest" in url:
            return fx("oi")
        raise AssertionError(url)
    saved = llama.basket
    llama.basket = lambda path=None: one
    try:
        rows, summ = llama.collect(fetch=fetch, post=lambda u, b: fx("coins_mcaps"),
                                   today=today)
    finally:
        llama.basket = saved
    keys = {r["registry_key"] for r in rows}
    check({"llama.fees_aave", "llama.revenue_aave", "llama.holders_revenue_aave",
           "llama.tvl_aave", "llama.stable_total", "llama.stable_by_chain",
           "llama.chain_tvl", "llama.dex_volume", "llama.perps_oi"} <= keys,
          f"the writer produces every CD-1 series it is asked for ({len(keys)} keys)")
    check(all(r["availability_kind"] == "ingest_instant" and r["source"] == "defillama"
              and r["available_at"] > "2026" for r in rows),
          "every row is stamped at the pull instant, ingest_instant -- never "
          "backdated, never reconstructed (DefiLlama refills history)")
    check({r["instrument"] for r in rows if r["registry_key"] == "llama.stable_by_chain"}
          == set(llama.STABLE_CHAINS),
          f"S-1 by chain: {', '.join(llama.STABLE_CHAINS)}")
    db = observations.ObservationStore(os.path.join(_TMP, "b.sqlite"))
    try:
        sub = [r for r in rows if r["registry_key"] == "llama.fees_aave"]
        n1 = db.write_many(observations.drop_unchanged(db, sub))
        n2 = db.write_many(observations.drop_unchanged(db, [dict(r, available_at="2026-10-14T01:00:00+00:00") for r in sub]))
        check(n1 == len(sub) and n2 == 0,
              f"a re-read of unchanged values writes nothing ({n1} then {n2})")
        imp = llama.parse_stable_chart(fx("stable_all"), today)
        seed(db, "llama.stable_total", imp)
        r = cb.write_stable_impulse(store=db)
        i30 = db.latest_as_of("calc.stable_impulse_30d", as_of=AS_OF)
        check(r["written"] > 300 and i30 is not None,
              f"S-1's 30- and 90-day impulse derived from the stored total "
              f"({r['written']} rows; latest 30-day {i30['value_num']:+.2f}%)")
    finally:
        db.close()
    check(llama.PROTOCOL_KEYS.count("fees_prl") == 1 and "tvl_prl" not in llama.PROTOCOL_KEYS
          and "tvl_ondo" not in llama.PROTOCOL_KEYS and "fees_tao" not in llama.PROTOCOL_KEYS,
          "only what DefiLlama serves is declared: Pearl's fees (a chain), no Ondo "
          "TVL chart, nothing for TAO or KAS")
    check(len(yf.CRYPTO_BASKET) == 12 and all(k.startswith("crypto_")
                                              for k in yf.CRYPTO_BASKET.values())
          and not set(yf.CRYPTO_BASKET) & set(yf.SYMBOLS),
          "the Yahoo basket is its own: twelve yfinance.crypto_<sym> keys, none in "
          "the market basket")
    ok = yf.drop_non_session_bars("TAO22974-USD", [("2026-10-10", 1.0), ("2026-10-11", 2.0)])
    check(ok[0] == [("2026-10-10", 1.0), ("2026-10-11", 2.0)] and not ok[1],
          "a basket coin keeps its weekend bars (continuous, declared)")
    parsed = yf.parse_rows([{"Date": "2026-10-10", "Close": 1.5, "Volume": 1e6}])
    # The market basket's volume is stored too since the Book B scanner's
    # follow-up 1 (ruled 13 Oct 2026, by its unit); an index level still stores
    # none (Friday stitching, 13 Oct).
    check(parsed["volumes"] == [("2026-10-10", 1e6)]
          and yf.volume_series("TAO22974-USD", parsed, ["2026-10-10"])
          and yf.volume_series("SPY", parsed, ["2026-10-10"])
          and not yf.volume_series("^VIX", parsed, ["2026-10-10"]),
          "volume is kept for the basket (MW-7's turnover) and the market basket "
          "by its unit, never for an index level")


def grade_store():
    """One store with every grader state in it."""
    db = observations.ObservationStore(os.path.join(_TMP, "grade.sqlite"))
    # ONDO supply: 1.0 -> 1.2 (holds) ... -> 1.85 (strained) ... -> 2.05 (failed)
    seed(db, "llama.supply_ondo", [("2026-10-13", 1.0e9), ("2026-11-15", 1.2e9),
                                   ("2027-01-20", 1.85e9), ("2027-03-10", 2.05e9)])
    # AERO fees: 100 a day before 21 Oct; after, 105 a day (strained: within 10%)
    seed(db, "llama.fees_aero", [(d, 100.0) for d in days("2026-09-01", 50)]
         + [(d, 105.0) for d in days("2026-10-21", 40)])
    # MORPHO holders revenue: zero, then on.
    seed(db, "llama.holders_revenue_morpho", [(d, 0.0) for d in days("2026-09-01", 60)]
         + [(d, 1000.0) for d in days("2026-12-01", 10)])
    return db


def group_c(cfg: dict) -> None:
    head("C. THE GRADER -- holds / strained / failed / not measured, with the rule")
    n = cb.names(cfg)
    db = grade_store()
    try:
        g = {
            "holds": cb.grade("ONDO", n["ONDO"], db, AS_OF, on="2026-12-01"),
            "strained": cb.grade("ONDO", n["ONDO"], db, AS_OF, on="2027-02-01"),
            "failed": cb.grade("ONDO", n["ONDO"], db, AS_OF, on="2027-03-15"),
            "not measured": cb.grade("KAS", n["KAS"], db, AS_OF),
        }
        for want, got in g.items():
            print(f"        {want:<13} -> {got['status']:<13} {got['detail']}"
                  + (f"  [rule: {got['rule']}]" if got.get("rule") else ""))
        check(all(g[k]["status"] == k for k in g),
              f"one of each state on the fixture store "
              f"({', '.join(v['status'] for v in g.values())})")
        check(all(g[k].get("rule") for k in ("holds", "strained", "failed"))
              and "2x" in g["failed"]["rule"] and "2029-01-31" in g["failed"]["rule"],
              "every measured status carries its rule, printed beside it")
        check(g["not measured"]["detail"].startswith("not measured — ")
              and "DefiLlama" in g["not measured"]["detail"],
              f"not measured says why: {g['not measured']['detail']}")
        a = cb.grade("AERO", n["AERO"], db, AS_OF, on="2026-11-20")
        a0 = cb.grade("AERO", n["AERO"], db, AS_OF, on="2026-10-15")
        check(a["status"] == "strained" and a0["status"] == "holds",
              f"AERO: holds before the launch, strained when fees after it sit "
              f"within the band of the pre-launch level ({a['detail']})")
        m0 = cb.grade("MORPHO", n["MORPHO"], db, AS_OF, on="2026-10-30")
        m1 = cb.grade("MORPHO", n["MORPHO"], db, AS_OF, on="2026-12-10")
        check(m0["status"] == "holds" and "off" in m0["detail"] and "undated" in m0["rule"]
              and "ON" in m1["detail"],
              "MORPHO: the switch read off then on; undated, so it cannot fail")
        p = cb.grade("PRL", n["PRL"], db, AS_OF)
        check(p["status"] == "not measured" and "S1-S8" in p["detail"],
              "PRL: its signposts are not stored yet, and the status says so")
        empty = cb.grade("ONDO", n["ONDO"], db, "2026-01-01T00:00:00+00:00")
        check(empty["status"] == "not measured" and "nothing stored" in empty["detail"],
              "a measured falsifier with nothing stored at the cutoff is not "
              "measured, never 'holds'")
    finally:
        db.close()


def group_d(cfg: dict) -> None:
    head("D. THE WEEKLY LINE -- the four event kinds, and silence")
    n = cb.names(cfg)
    q = copy.deepcopy(cfg)
    db = observations.ObservationStore(os.path.join(_TMP, "weekly.sqlite"))
    try:
        for sym in n:
            seed(db, cb.price_key(sym), alternating("2024-12-01", 700))
        quiet_end = "2026-09-06"
        ev = cb.weekly_events(db, quiet_end, AS_OF, q)
        blk = cb.weekly_block(db, quiet_end, AS_OF, q)
        check(ev == [] and blk["line"] is None,
              "nothing happened: no events and no line -- silence")
        check(blk["detail"]["title"] == "The crypto basket"
              and len(blk["detail"]["table"]["rows"]) == 12,
              "and the reference table still prints all twelve")
        # 1. a move past 2.5 sigma
        base = dict(alternating("2024-12-01", 700))["2026-09-03"]
        db.write_many([{"registry_key": cb.price_key("TAO"), "instrument": None,
                        "observed_at": "2026-09-03",
                        "available_at": "2026-09-04T01:00:00+00:00",
                        "value": base * 1.4, "source": "synthetic",
                        "availability_kind": "ingest_instant"}])
        ev = cb.weekly_events(db, quiet_end, AS_OF, q)
        kinds = {e["kind"] for e in ev}
        check(kinds == {"move"} and ev[0]["name"] == "TAO" and abs(ev[0]["z"]) >= 2.5,
              f"a move past the screen's 2.5 sigma fires ({ev[0]['text'] if ev else '-'})")
        line = cb.weekly_line(ev)
        check(line and line.startswith("Crypto basket: TAO moved"),
              f"and the line prints it: {line}")
        # 2. a falsifier crossed this week
        seed(db, "llama.supply_ondo", [("2026-08-01", 1.0e9), ("2026-09-01", 1.9e9),
                                       ("2026-09-05", 2.1e9)])
        ev = cb.weekly_events(db, quiet_end, AS_OF, q)
        check(any(e["kind"] == "threshold" and e["name"] == "ONDO" for e in ev),
              "a falsifier's threshold crossed this week fires")
        # 3. a dated event due this week
        ev = cb.weekly_events(db, "2026-10-18", AS_OF, q)
        due = [e for e in ev if e["kind"] == "dated_event"]
        check(due and due[0]["name"] == "AERO" and "2026-10-21" in due[0]["text"],
              f"a dated event due this week fires: {due[0]['text'] if due else '-'}")
        # 4. a scan item on a name
        items = Path(_TMP) / "scan.yaml"
        items.write_text(yaml.safe_dump([{"name": "UNI", "kind": "fee_switch_vote",
                                          "title": "Uniswap fee vote opens",
                                          "url": "https://example.org/uni",
                                          "date": "2026-09-04"}]), encoding="utf-8")
        r = cb.ingest_scan_items(items, store=db)
        ev = cb.weekly_events(db, quiet_end, AS_OF, q)
        check(r["written"] == 1 and any(e["kind"] == "scan_item" and e["name"] == "UNI"
                                        for e in ev),
              "a scan item on a name fires (exploit, listing, fee-switch vote)")
        bad = Path(_TMP) / "bad.yaml"
        bad.write_text(yaml.safe_dump([{"name": "DOGE", "kind": "rumour",
                                        "title": "x", "url": "nope", "date": "soon"}]),
                       encoding="utf-8")
        r = cb.ingest_scan_items(bad, store=db)
        check(r["written"] == 0 and len(r["refused"]) >= 3,
              f"an item outside the basket, the kinds or a URL and date is refused "
              f"whole ({len(r['refused'])} reasons)")
        check({e["kind"] for e in cb.weekly_events(db, quiet_end, AS_OF, q)}
              <= set(cb.EVENT_KINDS),
              f"only the four kinds exist ({', '.join(cb.EVENT_KINDS)})")
    finally:
        db.close()


def group_e(cfg: dict) -> None:
    head("E. THE RESTATEMENT -- decision 3's rules")
    n = cb.names(cfg)
    prior = {"10x": n["ONDO"]["odds"]["operator_10x"],
             "100x": n["ONDO"]["odds"]["operator_100x"]}
    changes = ["llama.fees_ondo +40% on the quarter"]

    def refused(row, ch) -> str:
        try:
            cb.validate_restatement(row, prior, ch)
        except cb.RestatementRefused as exc:
            return str(exc)
        return ""
    check("undated" in refused({"10x": "5–7%", "100x": "<0.5%", "dated": "",
                                "reason": "fees rose", "change": changes[0]}, changes),
          "an undated odds row is refused")
    check("without a reason" in refused({"10x": "5–7%", "100x": "<0.5%",
                                         "dated": "2026-12-31", "reason": "",
                                         "change": changes[0]}, changes),
          "a move without a reason is refused")
    check("no measurable moved" in refused({"10x": "5–7%", "100x": "<0.5%",
                                            "dated": "2026-12-31", "reason": "x y z",
                                            "change": None}, []),
          "a move with no measurable change is refused")
    check("one clause" in refused({"10x": "5–7%", "100x": "<0.5%",
                                   "dated": "2026-12-31",
                                   "reason": "Fees rose. And the vote passed.",
                                   "change": changes[0]}, changes),
          "a reason longer than one clause is refused")
    check("not one of" in refused({"10x": "5–7%", "100x": "<0.5%",
                                   "dated": "2026-12-31", "reason": "a rumour",
                                   "change": "a rumour"}, changes),
          "a move naming no change of this quarter is refused")
    check(refused({"10x": "5–7%", "100x": "<0.5%", "dated": "2026-12-31",
                   "reason": "fees rose 40% on the quarter",
                   "change": changes[0]}, changes) == "",
          "a dated move, on a named change, with a one-clause reason, passes")
    db = observations.ObservationStore(os.path.join(_TMP, "restate.sqlite"))
    asked = []

    def propose(**kw):
        asked.append(kw["sym"])
        return {"10x": "5–7%", "100x": "<0.5%", "change": kw["changes"][0],
                "reason": "fees rose by two fifths on the quarter",
                "dated": "2026-12-31"}
    try:
        seed(db, "llama.fees_ondo", [(d, 100.0) for d in days("2026-08-01", 70)]
             + [(d, 160.0) for d in days("2026-10-10", 90)])
        try:
            cb.restate("ONDO", n["ONDO"], db, "2026Q4", None, propose, None, AS_OF)
            outside = False
        except cb.RestatementRefused as exc:
            outside = "Quarterly only" in str(exc)
        check(outside and not asked, "nothing restates outside the Quarterly's run")
        path = Path(_TMP) / "dryrun" / "q.jsonl"
        out4 = cb.restate_quarter(db, "2026Q4", "quarterly-2026Q4", propose, AS_OF,
                                  path, cfg)
        by = {r["name"]: r for r in out4}
        check(asked == ["ONDO"] and by["ONDO"]["direction"] == "up"
              and by["ONDO"]["changes"],
              f"only a name with a named change asks the model ({asked}); ONDO moves "
              f"{by['ONDO']['direction']} on {by['ONDO']['changes'][0]}")
        check(by["KAS"]["reason"] == "unchanged — no measurable moved"
              and by["KAS"]["10x"] == n["KAS"]["odds"]["operator_10x"],
              "a name with nothing moved prints 'unchanged — no measurable moved', "
              "the model not asked")
        entries = cb.read_entries(path)
        e = next(x for x in entries if x["family"] == "crypto_basket.ondo")
        check(len(entries) == 12 and e["label"] == "model estimate"
              and e["emitted_by"] == "model"
              and e["source"] == "alt_asset:crypto_basket.ondo"
              and e["scenario_set"] == "crypto_basket.ondo-2026Q4-odds"
              and e["graded_against"] == "llama.fees_ondo",
              "every restatement is an alt_asset entry under the name's family, "
              "labelled 'model estimate', graded against its measurable")
        check(str(path).startswith(os.environ["CHESTER_DRYRUN_DIR"])
              and str(cb.dry_run_path()).startswith(os.environ["CHESTER_DRYRUN_DIR"]),
              "written to the dry-run namespace, never the register, until "
              "aq-6-thesis-register merges")
        out1 = cb.restate_quarter(db, "2027Q1", "quarterly-2027Q1", propose, AS_OF,
                                  path, cfg)
        b1 = {r["name"]: r for r in out1}
        t4 = cb.odds_table(n["ONDO"], by["ONDO"])
        t1 = cb.odds_table(n["ONDO"], b1["ONDO"])
        ref4 = json.dumps([r[1] for r in t4["rows"]] + [t4["columns"][1]],
                          ensure_ascii=False).encode()
        ref1 = json.dumps([r[1] for r in t1["rows"]] + [t1["columns"][1]],
                          ensure_ascii=False).encode()
        check(ref4 == ref1 and t4["rows"][0][1] == n["ONDO"]["odds"]["operator_10x"]
              and t4["columns"][1] == "Reference, 2026-10-12",
              "the reference column is byte-identical across two fixture quarters, "
              "and is the operator's original")
        check(b1["ONDO"]["10x"] == "5–7%" and "Model estimate" in t1["columns"][2],
              "and the model's column beside it carries last quarter's restatement "
              "forward when nothing moved")
        nn = copy.deepcopy(n["ONDO"])
        nn["operator_restatement"] = {"10x": "3–5%", "100x": "<0.5%", "dated": "2027-01-15"}
        t3 = cb.odds_table(nn, by["ONDO"])
        check(len(t3["columns"]) == 4 and t3["columns"][3] == "Operator, 2027-01-15",
              "the operator's own restatement prints as a third column when seeded")
        undated = cb.restate_quarter(db, "2026Q4", "quarterly-2026Q4",
                                     lambda **kw: {"10x": "9–11%", "100x": "1%",
                                                   "change": kw["changes"][0],
                                                   "reason": "x y z", "dated": ""},
                                     AS_OF, Path(_TMP) / "u.jsonl", cfg)
        check(any(r.get("refused") and "undated" in r["refused"] for r in undated),
              "an undated row from the model is refused at the Quarterly too, and "
              "the name keeps its prior odds")
    finally:
        db.close()
    src = (REPO / "altdata" / "crypto_basket.py").read_text(encoding="utf-8")
    check("register.store" not in src and "Register(" not in src
          and not re.search(r'add_parser\("restate', src),
          "no path writes the live register, and no command restates by hand")


def group_f(cfg: dict) -> None:
    head("F. THE BLOCKS -- budget, readability, consistency, the Monthly")
    from daily_cascade import consistency, figure_budget as fb, readability as rd
    from monthly_macro import stack as mstack
    db = observations.ObservationStore(os.path.join(_TMP, "blocks.sqlite"))
    try:
        for i, sym in enumerate(cb.names(cfg)):
            seed(db, cb.price_key(sym), alternating("2025-06-01", 480, 10.0 + i))
            seed(db, f"llama.mcap_{sym.lower()}", [("2026-09-20", 1e9 + i * 1e8)])
        seed(db, "llama.fees_aave", [(d, 250000.0 + 10 * k)
                                     for k, d in enumerate(days("2026-08-01", 50))])
        wk = cb.weekly_block(db, "2026-09-20", AS_OF, cfg)
        mo = cb.monthly_block(db, "2026-09-20T23:59:00+00:00", cfg)
        tabs = ([wk["detail"]["table"]] + wk["detail"]["tables"]
                + [mo["table"]] + mo["tables"])
        check(all(len(t["columns"]) <= rd.MAX_TABLE_COLUMNS for t in tabs),
              f"every new table has at most {rd.MAX_TABLE_COLUMNS} columns "
              f"({[len(t['columns']) for t in tabs]})")
        check(len(mo["lines"]) == 12 and all(re.match(r"^[A-Z]+: (holds|strained|failed|not measured)", ln)
                                             for ln in mo["lines"])
              and not any(ln.lstrip().startswith(("-", "•", "*")) for ln in mo["lines"]),
              "the Monthly prints a status line per name, no bullets")
        frame = fb.block_frame({"title": "Slow layers", "data": {}}, mo,
                               "September 2026", 8, "Month")
        used = sum(fb.quantified_figures(r) for r in frame["figures_you_may_cite"])
        moves = fb.table_moves(mo["table"], mo["title"], "Month")
        check(used <= 8 and len([m for m in moves if m.get("kind") == "move"]) == 12,
              f"the figure budget reads the block's twelve moves and lets a "
              f"paragraph cite {used} figures, inside the cap of 8")
        ed = {"sections": [], "detail": [wk["detail"]]}
        check(consistency.check(ed) == [],
              "the consistency gate reads the basket's tagged moves and finds them "
              "consistent")
        bad = copy.deepcopy(wk["detail"])
        bad["title"] = "A second table"
        bad["table"]["rows"][0][2] = "+9.9%"
        try:
            consistency.reconcile({"sections": [], "detail": [wk["detail"], bad]},
                                  fix=False)
            caught = False
        except consistency.EditionInconsistent:
            caught = True
        check(caught, "and fails an edition printing a basket name's week two ways")
        cfg_stack = __import__("daily_cascade.stack", fromlist=["config"]).config()
        p = {"alternative_assets": {"families": {"digital": {
            "metrics": [{"metric": "yfinance.mkt_btc_usd", "level": None}],
            "note": None}}}}
        sl = mstack.slow_layers(p, cfg_stack, db, "2026-09-20T23:59:00+00:00",
                                os.path.join(_TMP, "blocks.sqlite"))
        titles = [s["title"] for s in sl["subsections"]]
        i_dig = titles.index("Themes: digital")
        check(titles[i_dig + 1] == "Themes: digital — the crypto basket",
              f"the Monthly's Themes: digital gains the basket block right after the "
              f"classics ({titles[i_dig:i_dig + 2]})")
    finally:
        db.close()
    w = (REPO / "daily_cascade" / "weekly_stack.py").read_text(encoding="utf-8")
    check("crypto_basket.weekly_block(st" in w and '"misfit:crypto_basket"' in w
          and 'ed["detail"] = list(ed.get("detail") or []) + [cb["detail"]]' in w,
          "the Weekly carries the table after its sections and the line in What "
          "doesn't fit only when it has one")


def group_g() -> None:
    head("G. WIRING")
    unit = REPO / "deploy" / "systemd" / "chester-crypto-basket.service"
    timer = REPO / "deploy" / "systemd" / "chester-crypto-basket.timer"
    wrap = (REPO / "scripts" / "run_crypto_basket.sh").read_text(encoding="utf-8")
    check(unit.exists() and timer.exists()
          and "17:25 America/New_York" in timer.read_text(encoding="utf-8"),
          "the writers' unit and its 17:25 ET timer, after the close capture")
    check("pull_crypto_basket" in wrap and "altdata.sources.llama pull" in wrap
          and "altdata.crypto_basket derive" in wrap and "git pull --ff-only" in wrap,
          "the wrapper runs Yahoo, DefiLlama and the derived pass, after a pull")
    dr = (REPO / "scripts" / "deploy_remote.sh").read_text(encoding="utf-8")
    check("chester-crypto-basket.timer" in re.search(r'DEPLOY_TIMERS="([^"]*)"', dr,
                                                     re.S).group(1),
          "the timer is in DEPLOY_TIMERS")
    srcs = yaml.safe_load((REPO / "source_registry.yaml").read_text(encoding="utf-8"))
    check({"defillama", "saturday_scan"} <= set(srcs["sources"]),
          "DefiLlama and the Saturday scan are registered sources")
    aq = (REPO / "docs" / "change-order-alternative-assets-quarterly-2026-10-10.md"
          ).read_text(encoding="utf-8")
    sec = aq[aq.index("### 4.6"):aq.index("### 4.7")]
    check("PRL: deep → basket, 12 Oct, by the crypto basket brief" in sec,
          "the AQ order's §4.6 carries PRL's one amendment line")
    body = (REPO / "altdata" / "crypto_basket.py").read_text(encoding="utf-8")
    check(not re.search(r"(import requests|http_get|import_yfinance|llama\.fi|"
                        r"urllib\.request)", body),
          "the basket module reads the store only; the writers fetch")


def group_h() -> None:
    """13 Oct 2026: the digital block's registered keys, and the ZEC logger's
    CoinGecko reads withdrawn."""
    head("H. THEMES: DIGITAL -- REGISTERED KEYS; THE ZEC LOGGER OFF COINGECKO")
    from monthly_macro import payload as pl, stack as mstack
    from altdata.loggers import shielded
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    mets = reg.get("metrics") or reg
    dig = pl.ALT_FAMILIES["digital"]["metrics"]
    check("zec.price_usd" in dig and "zec.crypto_cap_share" in dig
          and "zec.price" not in dig and "crypto.cap_share" not in dig,
          f"the digital block reads the registered keys ({dig})")
    check(all(k in mets for k in dig if k.startswith("zec.")),
          "every ZEC key the digital block reads is a registered metric")
    db = observations.ObservationStore(os.path.join(_TMP, "digital.sqlite"))
    try:
        span = days("2025-06-01", 480)
        seed(db, "yfinance.mkt_btc_usd", alternating("2025-06-01", 480, 60000.0))
        seed(db, "zec.price_usd", alternating("2025-06-01", 480, 40.0))
        seed(db, "zec.shielded_value_share", [(d, 0.30) for d in span])
        # The share's real stored history: CoinGecko, 6 to 12 Oct 2026.
        seed(db, "zec.crypto_cap_share",
             [(d, 0.0094) for d in days("2026-10-06", 7)])
        now = "2026-10-13T23:00:00+00:00"
        alt = pl.alternative_assets_block(now, store=db)
        rows = {m["metric"]: m for m in alt["families"]["digital"]["metrics"]}
        check(rows["zec.price_usd"]["level"] is not None,
              "zec.price_usd has a level at the cutoff")
        cs = rows["zec.crypto_cap_share"]
        check(cs["level"] is None and cs.get("not_sourced")
              and cs.get("last_stored") == "2026-10-12",
              f"the cap share is not sourced, its last stored value dated "
              f"({cs.get('last_stored')}), never read as current")
        cfg_stack = __import__("daily_cascade.stack", fromlist=["config"]).config()
        sl = mstack.slow_layers({"alternative_assets": alt}, cfg_stack, db, now,
                                os.path.join(_TMP, "digital.sqlite"))
        sub = next(s for s in sl["subsections"] if s["title"] == "Themes: digital")
        names = [r[0] for r in sub["table"]["rows"]]
        check("Zcash (ZEC-USD)" in names
              and "Zcash's share of crypto market cap" in names,
              f"both rows print in the Monthly's Themes: digital ({names})")
        cap_row = next(r for r in sub["table"]["rows"]
                       if r[0] == "Zcash's share of crypto market cap")
        check(cap_row[1].startswith("not sourced — ")
              and "last stored 2026-10-12" in cap_row[1]
              and "0.94" not in " ".join(cap_row),
              f"the cap share prints 'not sourced — <reason>', dated, no figure "
              f"({cap_row[1][:60]}...)")
        price_row = next(r for r in sub["table"]["rows"] if r[0] == "Zcash (ZEC-USD)")
        check(re.search(r"\d", price_row[1]) is not None,
              f"the ZEC price row prints a level ({price_row[1]})")
        check(all("zec_price" not in r[0] and "." not in r[0]
                  for r in sub["table"]["rows"]),
              "no row is named by its store key")

        # THE LOGGER: ZEC's cap from DefiLlama's coin service; nothing else.
        calls = []

        def fetch(url, params=None):
            calls.append(url)
            return fx("coins_zcash_prices")

        def post(url, body):
            calls.append(url)
            return fx("coins_zcash_mcaps")
        cap = shielded.probe_cap(store=db, fetch=fetch, post=post)
        check(cap["state"] == "available" and cap["day"] == "2026-10-13"
              and all("coins.llama.fi" in u for u in calls),
              f"ZEC's cap is read from the coin service only ({calls}), on the "
              f"service's own day")
        wrote = shielded.cap_rows(cap, "gate")
        check([r["registry_key"] for r in wrote] == ["zec.market_cap_usd"]
              and wrote[0]["source"] == "defillama"
              and wrote[0]["observed_at"] == "2026-10-13",
              "the cap read writes zec.market_cap_usd only, sourced defillama")
        check(cap["total"]["state"] == "not_sourced"
              and cap["total"]["reason"] == shielded.CAP_SHARE_NOT_SOURCED,
              "the stored probe says the total is not sourced, with the reason")
        probe = db.as_of("zec.cap_probe", "2099-01-01T00:00:00+00:00")
        check(probe and json.loads(probe[-1]["value_text"] or "{}").get("source")
              == "defillama", "the probe row is stored and names defillama")

        def broken(*a, **k):
            raise RuntimeError("down")
        bad = shielded.probe_cap(store=db, fetch=broken, post=broken)
        check(bad["state"] == "error" and shielded.cap_rows(bad) == [],
              "a failed read writes nothing rather than a stale cap")
    finally:
        db.close()
    src = (REPO / "altdata" / "loggers" / "shielded.py").read_text(encoding="utf-8")
    check("api.coingecko.com" not in src,
          "the ZEC logger reads no CoinGecko endpoint")
    keys = shielded.keys()
    check("crypto.total_market_cap_usd" not in keys
          and "zec.crypto_cap_share" not in keys and "zec.market_cap_usd" in keys,
          "the heartbeat roster drops the two series nothing writes, keeps ZEC's cap")
    check(mets["zec.market_cap_usd"]["source"] == "defillama"
          and "STOPPED 13 OCT 2026" in mets["crypto.total_market_cap_usd"]["description"],
          "the registry says where ZEC's cap comes from and that the total stopped")
    srcs = yaml.safe_load((REPO / "source_registry.yaml").read_text(encoding="utf-8"))
    check(srcs["sources"]["coingecko"]["status"] == "retired",
          "CoinGecko is a retired source")


def main() -> int:
    cfg = group_a()
    group_b()
    group_c(cfg)
    group_d(cfg)
    group_e(cfg)
    group_f(cfg)
    group_g()
    group_h()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
