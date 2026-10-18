#!/usr/bin/env python3
"""
ST-13, THE PRL DATA LAYER (signal-triage Tranche 5; st-t5-prl, 18 Oct 2026).

    python tools/validate_st_t5_prl.py

A code gate: fixture responses and temporary stores. It never reads the live
store, fetches or calls a model; every network read is a fake.

  A  THE EMISSION (Appendix E): reward(1) = 3,229.6; reward(113,770) = 2,339.4;
     supply_code(113,770) = 312.72M; the rewards sum to the supply (the formula
     telescopes); about 1.04M PRL a day at the target pace
  B  THE SECURITY MASTER (G-24, MW-1): the crypto.watch class; PRL by its
     CoinGecko id; the loader test refuses a watch entry keyed by ticker (a
     ticker identifier, a ticker history, a bare-ticker alias); the MW-1 fields;
     no FIGI, so the chester-meme export never carries it
  C  COINGECKO (MW-4, G-25): a fixture /coins/pearl-2 and /tickers response to
     rows; keyless unless COINGECKO_DEMO_API_KEY is set; the budget; with the
     switch off it writes NOTHING (the 13 Oct ruling), on, it writes point in time
  D  THE EXPLORER (G-26): a declared JSON endpoint where robots allows it; robots
     refusing it reads nothing; the block-page leg; nothing declared reads nothing
     and says the derived layer prints ESTIMATED
  E  D1-D6 AND THE THESIS (2.7.4, 2.7.5): each by hand from a fixture store; the
     ESTIMATED fallback is never blank; D6 on and off; the thesis rule's three
     words, each with its inputs printed beside it; the stored rows point in time
  F  THE DAILY CARRIES NO PRL (MW-3d): no Daily module names PRL or Pearl, or
     imports the PRL layer (the grep gate)
  G  THE REGISTRY (AUD-3a): every new key registered, units and family or a
     lens exclusion; no by-hand key; nothing trigger-eligible; the catalogue; no
     network or model import in the derived layer
"""

from __future__ import annotations

import ast
import json
import math
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gate_tmp import mkdtemp  # noqa: E402

from altdata import derived, observations, prl  # noqa: E402

TMP = Path(mkdtemp("gate_st_t5_prl_"))
LINE = "=" * 78
PASS = FAIL = 0
CUT = "2026-10-16T22:00:00+00:00"


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


_N = 0


def store(rows: list[dict]) -> observations.ObservationStore:
    global _N
    _N += 1
    st = observations.ObservationStore(str(TMP / f"s{_N}.sqlite"))
    st.write_many(rows)
    return st


def row(key, day, value, avail=None, instrument=None, source="fixture"):
    return {"registry_key": key, "instrument": instrument, "observed_at": str(day),
            "available_at": avail or f"{day}T21:00:00+00:00", "value": value,
            "source": source, "availability_kind": "ingest_instant"}


# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. THE EMISSION (APPENDIX E)")
    r1, r2 = prl.reward(1), prl.reward(113770)
    s2 = prl.supply_code(113770)
    check(round(r1, 1) == 3229.6, f"block 1's reward is about 3,229.6 PRL ({r1:,.2f})")
    check(round(r2, 1) == 2339.4, f"block 113,770's is about 2,339.4 PRL ({r2:,.2f})")
    check(round(s2 / 1e6, 2) == 312.72, f"supply at block 113,770 is about 312.72M "
                                         f"({s2 / 1e6:,.3f}M)")
    check(math.isclose(sum(prl.reward(h) for h in range(1, 5001)), prl.supply_code(5000),
                       rel_tol=1e-9),
          "the rewards of blocks 1..H sum to supply_code(H): the formula telescopes")
    check(math.isclose(prl.supply_code(650226), 1.05e9, rel_tol=1e-12),
          "half the supply at block K = 650,226")
    check(round(prl.daily_emission(113770) / 1e6, 2) == 1.04,
          f"about 1.04M PRL a day at the 194 s target "
          f"({prl.daily_emission(113770) / 1e6:.3f}M)")
    try:
        prl.reward(0)
        ok = False
    except ValueError:
        ok = True
    check(ok, "no block 0: the first block is 1")


# ---------------------------------------------------------------------------
WATCH = {"coingecko_id": "fixture-coin", "name": "Fixture", "issuer": "x",
         "chain": "y", "explorer": "https://example.invalid", "mechanism_class": "z"}


def master_file(entries: list[dict]) -> Path:
    import yaml
    p = TMP / f"sm_{len(entries)}_{_N}.yaml"
    base = {"id": None, "name": "Fixture", "asset_class": "crypto.watch",
            "currency": "USD", "multiplier": 1, "exchange": None, "aliases": [],
            "active_from": None, "active_to": None, "unverified": ["exchange"]}
    doc = {"version": 1, "schema": "security-master-v1", "next_id": 10,
           "instruments": [{**base, **e} for e in entries]}
    p.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    return p


def group_b() -> None:
    head("B. THE SECURITY MASTER: crypto.watch AND PRL (G-24, MW-1)")
    from altdata import security_master as sm
    m = sm.Master()
    check("crypto.watch" in sm.ASSET_CLASSES, "crypto.watch is a class of the instrument model")
    e = m.by_coingecko("pearl-2")
    w = e.get("watch") or {}
    check(e["asset_class"] == "crypto.watch" and e["name"] == "Pearl"
          and w == {"coingecko_id": "pearl-2", "name": "Pearl",
                    "issuer": "Pearl Research Labs",
                    "chain": "pearl (native L1, btcd fork)",
                    "explorer": "https://explorer.pearlresearch.ai",
                    "mechanism_class": "PoUW / AI-compute"},
          f"the resolver returns PRL by its CoinGecko id, with MW-1's fields ({e['id']})")
    check(m.resolve("PRL41876-USD", "yahoo")["id"] == e["id"]
          and "PRL" not in e["aliases"] and "ticker" not in e["identifiers"],
          "one coin, one id: the basket still resolves it by Yahoo's coin id; no "
          "ticker key, no bare-ticker alias")
    check(not m.structural() and not sm.watch_faults(e),
          "the real master passes the structural checks with the new class")
    ok = sm.Master(master_file([{"id": "SM00001", "identifiers":
                                 {"crypto_id": "coingecko:fixture-coin"}, "watch": WATCH}]))
    check(not ok.structural(), "a well-formed watch entry loads clean")
    cases = {
        "a ticker identifier": {"identifiers": {"crypto_id": "coingecko:fixture-coin",
                                                "ticker": "PRL"}},
        "a bare-ticker alias": {"identifiers": {"crypto_id": "coingecko:fixture-coin"},
                                "aliases": ["PRL"]},
        "a ticker history": {"identifiers": {"crypto_id": "coingecko:fixture-coin"},
                             "ticker_history": [{"ticker": "PRL", "from": None,
                                                 "to": None}]}}
    for what, extra in cases.items():
        bad = sm.Master(master_file([{"id": "SM00001", "watch": WATCH, **extra}]))
        faults = bad.structural()
        check(any("crypto.watch" in f and "(MW-1)" in f for f in faults),
              f"the loader test refuses {what} ({faults[:1]})")
    miss = sm.Master(master_file([{"id": "SM00001", "identifiers":
                                   {"crypto_id": "coingecko:other"},
                                   "watch": {k: v for k, v in WATCH.items()
                                             if k != "issuer"}}]))
    f2 = miss.structural()
    check(any("without issuer" in f for f in f2) and any("is not coingecko:fixture-coin"
                                                         in f for f in f2),
          "and a missing MW-1 field, and a crypto_id that is not its CoinGecko id")
    ex = (REPO / "altdata" / "sm_export.py").read_text(encoding="utf-8")
    check("composite_figi" in ex and "figi" not in json.dumps(e).lower(),
          "no FIGI: the export, keyed by composite FIGI, never carries a watch coin")


# ---------------------------------------------------------------------------
COIN = {"id": "pearl-2", "symbol": "prl", "name": "Pearl",
        "market_data": {"current_price": {"usd": 1.05}, "market_cap": {"usd": 268.0e6},
                        "total_volume": {"usd": 4.0e6}, "circulating_supply": 255.05e6,
                        "last_updated": "2026-10-16T21:58:00.000Z"}}
TICKERS = {"name": "Pearl", "tickers": [
    {"market": {"name": "CoinEx"}, "converted_volume": {"usd": 3.64e6},
     "last_fetch_at": "2026-10-16T21:50:00+00:00"},
    {"market": {"name": "BigONE"}, "converted_volume": {"usd": 0.24e6},
     "last_fetch_at": "2026-10-16T21:50:00+00:00"},
    {"market": {"name": "SafeTrade"}, "converted_volume": {"usd": 0.12e6},
     "last_fetch_at": "2026-10-16T21:50:00+00:00"},
    {"market": {"name": "CoinEx"}, "converted_volume": {"usd": None},
     "last_fetch_at": "2026-10-16T21:50:00+00:00"}]}


def fake_get(calls: list):
    def get(path, params=None):
        calls.append(path)
        return COIN if path.endswith("/coins/pearl-2") else TICKERS
    return get


def group_c() -> None:
    head("C. COINGECKO FOR pearl-2 (MW-4, G-25)")
    from altdata import config
    from altdata.sources import coingecko as cg
    now = "2026-10-16T22:00:00.000000+00:00"
    rows = cg.parse_coin(COIN, now)
    by = {r["registry_key"]: r["value"] for r in rows}
    check(by == {"coingecko.prl_price": 1.05, "coingecko.prl_market_cap": 268.0e6,
                 "coingecko.prl_volume_24h": 4.0e6, "coingecko.prl_circulating": 255.05e6}
          and all(r["observed_at"] == "2026-10-16" and r["available_at"] == now
                  for r in rows),
          "the coin's four market fields, on last_updated's UTC day, available at the pull")
    try:
        cg.parse_coin({**COIN, "id": "the-parallel"}, now)
        ok = False
    except ValueError:
        ok = True
    check(ok, "a response for another coin is refused, never stored under PRL")
    tk = cg.parse_tickers(TICKERS, now)
    vv = {r["instrument"]: r["value"] for r in tk
          if r["registry_key"] == "coingecko.prl_venue_volume"}
    n = [r["value"] for r in tk if r["registry_key"] == "coingecko.prl_venues"]
    check(vv == {"CoinEx": 3.64e6, "BigONE": 0.24e6, "SafeTrade": 0.12e6} and n == [3.0],
          f"tickers: one row per venue (a pair with no USD volume counted, not summed), "
          f"and three venues ({vv})")
    h0 = cg.headers({})
    h1 = cg.headers({"COINGECKO_DEMO_API_KEY": "fixture-not-a-key"})
    check("x-cg-demo-api-key" not in h0 and h1.get("x-cg-demo-api-key") == "fixture-not-a-key"
          and "@" not in h0["User-Agent"],
          "keyless unless COINGECKO_DEMO_API_KEY is in the environment; the User-Agent "
          "names no one")
    calls, slept = [], []
    r = cg.collect(get=fake_get(calls), now=now, sleep=slept.append)
    c = prl.config()["coingecko"]
    check(len(calls) == c["calls_per_pull"] == 2 and slept == [6.0] and len(r) == 8,
          "the budget: two calls a pull, six seconds apart (16 a week at weekly plus a "
          "daily close)")
    check(config.ENABLED_SOURCES.get("coingecko") is False,
          "the switch stays off on this branch (the 13 Oct ruling; Ari's to rule)")
    db = str(TMP / "cg.sqlite")
    with observations.ObservationStore(db) as st:
        off = cg.pull(db=st, get=fake_get([]), now=now, sleep=lambda s: None)
        n_off = len(st.as_of("coingecko.prl_price", CUT))
    check(off["state"] == "disabled" and off["written"] == 0 and n_off == 0
          and off["rows"] == 8,
          "switch off: it fetches and parses, and writes NOTHING")
    config.ENABLED_SOURCES["coingecko"] = True
    try:
        with observations.ObservationStore(db) as st:
            on = cg.pull(db=st, get=fake_get([]), now=now, sleep=lambda s: None)
            got = st.as_of("coingecko.prl_price", CUT)
    finally:
        config.ENABLED_SOURCES["coingecko"] = False
    check(got and got[-1]["value_num"] == 1.05 and str(got[-1]["available_at"])[:10]
          == "2026-10-16",
          f"switch on: the rows are written point in time ({on.get('state')})")


# ---------------------------------------------------------------------------
EXPL = {"tip": {"height": 260000, "difficulty": 31.2e6, "time": 1792184400},
        "supply": {"total": 600.0e6}}
SPEC = {"url": "https://explorer.example/api/tip", "height": "tip.height",
        "difficulty": "tip.difficulty", "supply": "supply.total", "time": "tip.time"}


def group_d() -> None:
    head("D. THE EXPLORER (G-26)")
    from altdata.sources import pearl_explorer as pe
    now = "2026-10-16T22:00:00.000000+00:00"
    base = dict(prl.config()["explorer"])
    allow = lambda u: "User-agent: *\nDisallow: /private/\n"          # noqa: E731
    deny = lambda u: "User-agent: *\nDisallow: /api/\n"               # noqa: E731
    got = pe.collect(get_json=lambda u: EXPL, get_text=allow, now=now,
                     cfg={**base, "json_endpoint": SPEC})
    by = {r["registry_key"]: (r["value"], r["observed_at"]) for r in got["rows"]}
    check(got["leg"] == "json" and by == {
        "pearl.chain_height": (260000.0, "2026-10-16"),
        "pearl.chain_difficulty": (31.2e6, "2026-10-16"),
        "pearl.chain_supply": (600.0e6, "2026-10-16")},
          f"a declared JSON endpoint, robots allowing it: height, difficulty, supply on "
          f"the tip's UTC day ({by})")
    no = pe.collect(get_json=lambda u: EXPL, get_text=deny, now=now,
                    cfg={**base, "json_endpoint": SPEC})
    check(not no["rows"] and "robots.txt refuses /api/tip" in no["reason"],
          f"robots refusing the path reads nothing ({no['reason']})")
    page = {"url": "https://explorer.example/blocks", "height_regex": r"Height\s*([\d,]+)",
            "difficulty_regex": r"Difficulty\s*([\d.]+)"}
    pg = pe.collect(get_text=lambda u: (allow(u) if u.endswith("robots.txt") else
                                        "<b>Height 260,001</b> <i>Difficulty 31200000.5</i>"),
                    now=now, cfg={**base, "block_page": page})
    check(pg["leg"] == "page" and {r["registry_key"]: r["value"] for r in pg["rows"]} ==
          {"pearl.chain_height": 260001.0, "pearl.chain_difficulty": 31200000.5}
          and all(r["source"] == "pearl_explorer:page" for r in pg["rows"]),
          "the block-page leg, its rows marked by their variant")
    none = pe.collect(get_text=allow, now=now, cfg=base)
    res = pe.pull(get_text=allow, now=now, cfg=base)
    check(not none["rows"] and none["reason"] == pe.NOT_DECLARED
          and res["state"] == "estimated" and res["written"] == 0,
          "nothing declared (as on this branch): it reads nothing, writes nothing, and "
          "says the derived layer prints ESTIMATED")
    doc = " ".join((pe.__doc__ or "").split())
    check(base.get("json_endpoint") is None and base.get("block_page") is None
          and "THE ENDPOINT IS NOT YET DISCOVERED" in doc
          and "robots: (not read: unreachable 18 Oct 2026)" in doc
          and "terms: (not read: unreachable 18 Oct 2026)" in doc,
          "nothing is declared on this branch, and the docstring records the endpoint "
          "as not yet discovered, with its robots and terms lines")


# ---------------------------------------------------------------------------
def prl_rows(height_day="2026-10-16", d0=21.4e6, d1=31.2e6, p0=1.40, p1=1.05):
    av = "2026-10-16T21:30:00+00:00"
    R = [row("pearl.chain_height", height_day, 260000.0, av, source="pearl_explorer"),
         row("pearl.chain_difficulty", "2026-09-16", d0, "2026-09-16T21:30:00+00:00",
             source="pearl_explorer"),
         row("pearl.chain_difficulty", "2026-10-16", d1, av, source="pearl_explorer"),
         row("coingecko.prl_price", "2026-09-16", p0, "2026-09-16T21:30:00+00:00",
             source="coingecko"),
         row("coingecko.prl_price", "2026-10-16", p1, av, source="coingecko"),
         row("coingecko.prl_volume_24h", "2026-10-16", 4.0e6, av, source="coingecko"),
         row("coingecko.prl_circulating", "2026-10-16", 520.0e6, av, source="coingecko")]
    for v, x in (("CoinEx", 3.64e6), ("BigONE", 0.24e6), ("SafeTrade", 0.12e6)):
        R.append(row("coingecko.prl_venue_volume", "2026-10-16", x, av, instrument=v,
                     source="coingecko"))
    return R


def group_e() -> None:
    head("E. D1-D6 AND THE THESIS STATUS")
    H = 260000
    sc = 2.1e9 * H / (H + 650226)
    with store(prl_rows()) as st:
        d = prl.derive(st, CUT)
        rows = prl.rows(st, CUT)
        ts = prl.thesis_status(st, CUT)
        tsi = prl.thesis_status(st, CUT, {"s1_partner_added": True})
        tsd = prl.thesis_status(st, CUT, {"s7_incident": True, "s1_partner_added": True})
    check(math.isclose(d["supply_code"]["value"], sc, rel_tol=1e-12)
          and "ESTIMATED" not in d["supply_code"]["trace"],
          f"D1 from the explorer's height: {sc / 1e6:,.2f}M, not estimated")
    check(math.isclose(d["overhang"]["value"], 100 * 121.70e6 / sc, rel_tol=1e-12),
          f"D2 the overhang: 121.70M / D1 = {100 * 121.70e6 / sc:.2f}%")
    check(math.isclose(d["supply_gap"]["value"], sc - 520.0e6, rel_tol=1e-12)
          and "coingecko.prl_circulating" in d["supply_gap"]["trace"],
          f"D3 the gap: D1 less CoinGecko's circulating = {(sc - 520e6) / 1e6:,.2f}M")
    em = prl.reward(H) * 86400 / 194 * 1.05 / 4.0e6
    check(math.isclose(d["emission_to_volume"]["value"], em, rel_tol=1e-12),
          f"D4 emission-to-volume: reward x 86400/194 x $1.05 / $4.0M = {em:.3f}")
    check(math.isclose(d["venue_conc"]["value"], 100 * 3.64 / 4.0, rel_tol=1e-12)
          and "CoinEx 91.0%" in d["venue_conc"]["trace"],
          f"D5 venue concentration: CoinEx 91.0% of $4.0M across three venues")
    check(d["idle_gpu_flag"]["value"] == 1.0
          and "difficulty +45.8%" in d["idle_gpu_flag"]["trace"]
          and "price -25.0%" in d["idle_gpu_flag"]["trace"],
          f"D6 ON: difficulty up 45.8% while price fell 25.0% over 30 days "
          f"({d['idle_gpu_flag']['trace'][:80]})")
    with store(prl_rows(p1=1.30)) as st:
        off = prl.idle_gpu(st, CUT)
    check(off["value"] == 0.0, "D6 OFF when price fell only 7.1%")
    # THE ESTIMATED FALLBACK: an empty store still prints a height and a supply
    with store([]) as st:
        e0 = prl.derive(st, CUT)
        er = prl.rows(st, CUT)
    est = prl.estimate_height(CUT)
    want = 113770 + int((prl._instant(CUT) - prl._instant("2026-09-15T23:53:00+00:00"))
                        .total_seconds() // 194)
    check(est == want and e0["height_estimated"]["value"] == float(est)
          and "ESTIMATED" in e0["supply_code"]["trace"]
          and e0["supply_code"]["value"] == prl.supply_code(est),
          f"nothing stored: the height is ESTIMATED from Appendix E's anchor at 194 s "
          f"({est:,}), and D1 prints from the formula -- never a blank")
    check(e0["supply_gap"]["value"] is None and e0["supply_gap"]["reason"]
          and e0["venue_conc"]["reason"] == "no tickers pull stored",
          "a figure whose input is absent is absent with its reason; nothing substituted")
    check({"calc.prl_height_estimated", "calc.prl_supply_code"} <= {x["registry_key"]
                                                                     for x in er},
          "the estimate is stored as calc.prl_height_estimated, never as pearl.chain_height")
    with store([row("pearl.chain_height", "2026-10-09", 257000.0,
                    "2026-10-09T21:30:00+00:00", source="pearl_explorer")]) as st:
        h = prl.height_at(st, CUT)
    check(h["estimated"] and h["height"] == 257000 + int(
              (prl._instant(CUT) - prl._instant("2026-10-09")).total_seconds() // 194)
          and "from the explorer's 257,000" in h["from"],
          f"a week-old observed height is the anchor of the estimate ({h['from'][:70]})")
    # THE THESIS RULE
    check(ts["value"] == "UNCHANGED" and "Not read:" in ts["trace"]
          and "S1 a named paid-compute partner added" in ts["trace"],
          f"no rule fired: UNCHANGED, with what was not read ({ts['trace'][:90]})")
    check(tsi["value"] == "IMPROVED"
          and tsi["trace"].startswith("IMPROVED: S1 a named paid-compute partner added")
          and "S1 a named paid-compute partner added yes" in tsi["trace"],
          f"S1 gains a partner: IMPROVED, the input beside the word ({tsi['trace'][:90]})")
    check(tsd["value"] == "DETERIORATED" and tsd["deteriorated"] ==
          ["S7 an exploit, chain halt or reorg"],
          "an incident outranks a partner: DETERIORATED")
    hot = []
    for w in range(4):
        day = (prl._instant(CUT) - __import__("datetime").timedelta(days=7 * w)).date().isoformat()
        av = f"{day}T21:30:00+00:00"
        hot += [row("pearl.chain_height", day, 260000.0 - 3000 * w, av, source="pearl_explorer"),
                row("coingecko.prl_price", day, 1.05, av, source="coingecko"),
                row("coingecko.prl_volume_24h", day, 0.5e6, av, source="coingecko")]
    with store(hot) as st:
        t4 = prl.thesis_status(st, CUT)
    check(t4["value"] == "DETERIORATED" and "D4 above 1.0 for 4 weekly reads" in t4["trace"],
          f"D4 above 1.0 for four weekly reads: DETERIORATED ({t4['trace'][:100]})")
    keys = {x["registry_key"] for x in rows}
    th = next(x for x in rows if x["registry_key"] == "calc.prl_thesis_status")
    check(keys >= {"calc.prl_reward", "calc.prl_supply_code", "calc.prl_overhang",
                   "calc.prl_supply_gap", "calc.prl_emission_to_volume",
                   "calc.prl_venue_conc", "calc.prl_idle_gpu_flag", "calc.prl_thesis_status"}
          and all(observations.canonical_instant(x["available_at"])
                  <= observations.canonical_instant(CUT) for x in rows)
          and json.loads(th["value"])["status"] == "UNCHANGED"
          and "trace" in json.loads(th["value"]),
          "the stored rows: every calc.prl_* key, none available after the cutoff, the "
          "thesis stored with its trace")


# ---------------------------------------------------------------------------
def group_f() -> None:
    head("F. THE DAILY CARRIES NO PRL (MW-3d; the grep gate)")
    hits, imps = [], []
    for f in sorted((REPO / "daily_cascade").glob("*.py")):
        t = f.read_text(encoding="utf-8")
        if re.search(r"\bPRL\b|\bPearl\b", t):
            hits.append(f.name)
        if re.search(r"altdata(\.|\s+import\s+)(prl|sources\.coingecko|sources\.pearl_explorer)"
                     r"|from altdata\.sources import (coingecko|pearl_explorer)", t):
            imps.append(f.name)
    check(not hits, "no daily_cascade module names PRL or Pearl"
          + (f": {hits}" if hits else ""))
    check(not imps, "no daily_cascade module imports the PRL layer"
          + (f": {imps}" if imps else ""))


# ---------------------------------------------------------------------------
NEW_KEYS = ["coingecko.prl_price", "coingecko.prl_market_cap", "coingecko.prl_volume_24h",
            "coingecko.prl_circulating", "coingecko.prl_venue_volume",
            "coingecko.prl_venues", "pearl.chain_height", "pearl.chain_difficulty",
            "pearl.chain_supply"] + list(prl.KEYS.values())


def group_g() -> None:
    head("G. THE REGISTRY, THE CATALOGUE, NOTHING ELSE")
    import yaml
    ents = {k: derived.registry_entry(k) for k in NEW_KEYS}
    check(all(ents.values()) and all(e.get("units") for e in ents.values()),
          f"all {len(NEW_KEYS)} new keys registered, each with units")
    fam = {k: derived.family_of(k) for k in NEW_KEYS}
    check(all(f[0] or "not a level series" in f[1] for f in fam.values()),
          "each with a family, or a lens exclusion with its reason (the flag, the label)")
    check(all(e.get("source") in ("coingecko", "pearl_explorer", "calc")
              for e in ents.values()), "no by-hand key: every source is a writer or calc")
    check(not any(e.get("trigger_eligible") for e in ents.values())
          and ents["calc.prl_idle_gpu_flag"].get("rights_ceiling") == "narrow_flag",
          "nothing trigger-eligible; D6 is MW-2's one narrow flag")
    cat = yaml.safe_load((REPO / "config" / "catalogue_commands.yaml").read_text(
        encoding="utf-8"))["commands"]
    check({"altdata.sources.coingecko", "altdata.sources.pearl_explorer", "altdata.prl"}
          <= set(cat) and "COINGECKO_DEMO_API_KEY" in cat["altdata.sources.coingecko"]["line"],
          "the catalogue names the three commands and the optional key's name")
    src = yaml.safe_load((REPO / "source_registry.yaml").read_text(encoding="utf-8"))
    check(src["sources"]["coingecko"]["status"] == "retired"
          and src["sources"]["pearl_explorer"]["implemented_by"]
          == "altdata/sources/pearl_explorer.py",
          "the source registry: CoinGecko stays retired (with the ST-13 caveat); the "
          "explorer registered")
    tree = ast.parse((REPO / "altdata" / "prl.py").read_text(encoding="utf-8"))
    mods = {n.names[0].name if isinstance(n, ast.Import) else (n.module or "")
            for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))}
    bad = {m for m in mods if any(m == x or m.startswith(x + ".") for x in
                                  ("requests", "urllib", "http", "socket", "anthropic"))}
    check(not bad, f"the derived layer imports no network or model library ({sorted(mods)})")
    check("anthropic" not in sys.modules, "no model client was built")
    claude = (REPO / "CLAUDE.md").read_text(encoding="utf-8")
    check("validate_st_t5_prl" in (REPO / "Makefile").read_text(encoding="utf-8")
          and "crypto.watch" in claude, "the Makefile runs this gate; CLAUDE.md names the class")


def main() -> int:
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g):
        g()
    print(f"\n{PASS} passed, {FAIL} failed")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
