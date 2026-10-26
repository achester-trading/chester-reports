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

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

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
def group_c() -> None:
    head("C. COINGECKO STAYS RETIRED (RULING 1 OF 18 OCT)")
    import yaml
    from altdata import config
    check(not (REPO / "altdata" / "sources" / "coingecko.py").exists()
          and "coingecko" not in config.ENABLED_SOURCES,
          "the fetcher is removed, and its switch entry: no flag can turn it on")
    src = yaml.safe_load((REPO / "source_registry.yaml").read_text(encoding="utf-8"))
    cg = src["sources"]["coingecko"]
    cav = " ".join(cg.get("caveats") or [])
    check(cg["status"] == "retired" and "you are not allowed to duplicate, reproduce, "
          "copy, store, derive from or translate any Data" in cav
          and "STAYS RETIRED (ruled 18 Oct 2026" in cav,
          "the retired source keeps its terms line, with the ruling")
    order = (REPO / "docs" / "change-order-signal-triage-2026-09-25.md").read_text(
        encoding="utf-8")
    check("## Rulings addendum — 18 Oct 2026" in order
          and "MW-4's CoinGecko clause is superseded" in order,
          "the order's register says MW-4's CoinGecko clause is superseded, dated")
    cfg = prl.config()
    d = cfg["derived"]
    check("coingecko" not in cfg and d["price"] == ["yfinance.crypto_prl"]
          and d["volume"] == ["yfinance.crypto_prl_volume"]
          and d["market_cap"] == ["llama.mcap_prl"] and d["circulating"] == ["llama.supply_prl"],
          "PRL's inputs are the basket's: Yahoo's price and 24h volume, DefiLlama's cap "
          "and circulating supply")
    hits = [f.name for f in (REPO / "altdata").rglob("*.py")
            if "coingecko.prl_" in f.read_text(encoding="utf-8")]
    check(not hits, "no module reads a CoinGecko key" + (f": {hits}" if hits else ""))


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
          and "G-26 IS CLOSED AS A LISTED GAP" in doc
          and "robots: none (404, the app's HTML page; 18 Oct 2026)" in doc
          and "terms: none covering automated access (18 Oct 2026)" in doc,
          "nothing is declared on this branch, and the docstring records the endpoint "
          "as a listed gap, with its robots and terms lines")
    check(base.get("status") == "listed gap" and base.get("ruled") == "2026-10-18"
          and "no robots file" in str(base.get("reason")),
          "ruling 1 of 18 Oct: config/prl.yaml's explorer entry is a listed gap, with "
          "its reason and date")


# ---------------------------------------------------------------------------
def prl_rows(height_day="2026-10-16", d0=21.4e6, d1=31.2e6, p0=1.40, p1=1.05,
             explorer_supply=None):
    av = "2026-10-16T21:30:00+00:00"
    R = [row("pearl.chain_height", height_day, 260000.0, av, source="pearl_explorer"),
         row("pearl.chain_difficulty", "2026-09-16", d0, "2026-09-16T21:30:00+00:00",
             source="pearl_explorer"),
         row("pearl.chain_difficulty", "2026-10-16", d1, av, source="pearl_explorer"),
         row("yfinance.crypto_prl", "2026-09-16", p0, "2026-09-17T00:30:00+00:00",
             source="yfinance"),
         row("yfinance.crypto_prl", "2026-10-16", p1, av, source="yfinance"),
         row("yfinance.crypto_prl_volume", "2026-10-16", 4.0e6, av, source="yfinance"),
         row("llama.supply_prl", "2026-10-16", 520.0e6, av, source="defillama")]
    if explorer_supply is not None:
        R.append(row("pearl.chain_supply", height_day, explorer_supply, av,
                     source="pearl_explorer"))
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
    check(d["supply_gap"]["value"] is None and d["supply_gap"].get("estimated")
          and d["supply_gap"]["reason"].startswith("ESTIMATED: the gap is the formula "
                                                   "against the explorer's supply"),
          "D3 with no explorer supply: ESTIMATED, no row, with the reason (ruling 1)")
    with store(prl_rows(explorer_supply=583.0e6)) as st:
        d3 = prl.derive(st, CUT)["supply_gap"]
    check(math.isclose(d3["value"], sc - 583.0e6, rel_tol=1e-12)
          and "the explorer's supply" in d3["trace"],
          f"D3 once the explorer reads: the formula less its supply = "
          f"{(sc - 583e6) / 1e6:,.2f}M")
    em = prl.reward(H) * 86400 / 194 * 1.05 / 4.0e6
    check(math.isclose(d["emission_to_volume"]["value"], em, rel_tol=1e-12)
          and "yfinance.crypto_prl_volume" in d["emission_to_volume"]["trace"]
          and "yfinance.crypto_prl)" in d["emission_to_volume"]["trace"],
          f"D4 from Yahoo's bars: reward x 86400/194 x $1.05 / $4.0M volume = {em:.3f}")
    check(d["venue_conc"]["value"] is None and d["venue_conc"].get("not_tracked")
          and d["venue_conc"]["reason"].startswith("not tracked (source retired): "
                                                   "calc.prl_venue_conc")
          and derived.registry_entry("calc.prl_venue_conc").get("tracked") is False,
          "D5 prints 'not tracked (source retired)' with its key named; no row")
    check(d["idle_gpu_flag"]["value"] == 1.0
          and "difficulty +45.8%" in d["idle_gpu_flag"]["trace"]
          and "price -25.0%" in d["idle_gpu_flag"]["trace"],
          f"D6 ON: difficulty up 45.8% while Yahoo's price fell 25.0% over 30 days "
          f"({d['idle_gpu_flag']['trace'][:80]})")
    with store(prl_rows(p1=1.30)) as st:
        off = prl.idle_gpu(st, CUT)
    check(off["value"] == 0.0, "D6 OFF when price fell only 7.1%")
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
    check(e0["emission_to_volume"]["value"] is None and e0["emission_to_volume"]["reason"],
          "a figure whose input is absent is absent with its reason; nothing substituted")
    check({"calc.prl_height_estimated", "calc.prl_supply_code"} <= {x["registry_key"]
                                                                     for x in er}
          and "calc.prl_venue_conc" not in {x["registry_key"] for x in er},
          "the estimate is stored as calc.prl_height_estimated; D5 writes no row")
    with store([row("pearl.chain_height", "2026-10-09", 257000.0,
                    "2026-10-09T21:30:00+00:00", source="pearl_explorer")]) as st:
        h = prl.height_at(st, CUT)
    check(h["estimated"] and h["height"] == 257000 + int(
              (prl._instant(CUT) - prl._instant("2026-10-09")).total_seconds() // 194)
          and "from the explorer's 257,000" in h["from"],
          f"a week-old observed height is the anchor of the estimate ({h['from'][:70]})")
    check(ts["value"] == "UNCHANGED" and "Not read:" in ts["trace"]
          and "D5 not tracked: source retired" in ts["trace"],
          f"no rule fired: UNCHANGED, with what was not read ({ts['trace'][:90]})")
    check(tsi["value"] == "IMPROVED"
          and tsi["trace"].startswith("IMPROVED: S1 a named paid-compute partner added")
          and "S1 a named paid-compute partner added yes" in tsi["trace"],
          f"S1 gains a partner: IMPROVED, the input beside the word ({tsi['trace'][:90]})")
    check(tsd["value"] == "DETERIORATED" and tsd["deteriorated"] ==
          ["S7 an exploit, chain halt or reorg"],
          "an incident outranks a partner: DETERIORATED")
    import datetime as _dt
    hot = []
    for w in range(4):
        day = (prl._instant(CUT) - _dt.timedelta(days=7 * w)).date().isoformat()
        av = f"{day}T21:30:00+00:00"
        hot += [row("pearl.chain_height", day, 260000.0 - 3000 * w, av, source="pearl_explorer"),
                row("yfinance.crypto_prl", day, 1.05, av, source="yfinance"),
                row("yfinance.crypto_prl_volume", day, 0.5e6, av, source="yfinance")]
    with store(hot) as st:
        t4 = prl.thesis_status(st, CUT)
    check(t4["value"] == "DETERIORATED" and "D4 above 1.0 for 4 weekly reads" in t4["trace"],
          f"D4 above 1.0 for four weekly reads: DETERIORATED ({t4['trace'][:100]})")
    keys = {x["registry_key"] for x in rows}
    th = next(x for x in rows if x["registry_key"] == "calc.prl_thesis_status")
    check(keys >= {"calc.prl_reward", "calc.prl_supply_code", "calc.prl_overhang",
                   "calc.prl_emission_to_volume", "calc.prl_idle_gpu_flag",
                   "calc.prl_thesis_status"}
          and all(observations.canonical_instant(x["available_at"])
                  <= observations.canonical_instant(CUT) for x in rows)
          and json.loads(th["value"])["status"] == "UNCHANGED"
          and "trace" in json.loads(th["value"]),
          "the stored rows: every computed calc.prl_* key, none available after the "
          "cutoff, the thesis stored with its trace")


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
NEW_KEYS = ["pearl.chain_height", "pearl.chain_difficulty",
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
    check(all(e.get("source") in ("pearl_explorer", "calc")
              for e in ents.values()), "no by-hand key: every source is a writer or calc")
    check(not any(e.get("trigger_eligible") for e in ents.values())
          and ents["calc.prl_idle_gpu_flag"].get("rights_ceiling") == "narrow_flag",
          "nothing trigger-eligible; D6 is MW-2's one narrow flag")
    cat = yaml.safe_load((REPO / "config" / "catalogue_commands.yaml").read_text(
        encoding="utf-8"))["commands"]
    check({"altdata.sources.pearl_explorer", "altdata.prl"} <= set(cat)
          and "altdata.sources.coingecko" not in cat,
          "the catalogue names the explorer and the derived layer, and no CoinGecko")
    src = yaml.safe_load((REPO / "source_registry.yaml").read_text(encoding="utf-8"))
    check(src["sources"]["coingecko"]["status"] == "retired"
          and src["sources"]["pearl_explorer"]["implemented_by"]
          == "altdata/sources/pearl_explorer.py",
          "the source registry: CoinGecko stays retired; the explorer registered")
    tree = ast.parse((REPO / "altdata" / "prl.py").read_text(encoding="utf-8"))
    mods = {n.names[0].name if isinstance(n, ast.Import) else (n.module or "")
            for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))}
    bad = {m for m in mods if any(m == x or m.startswith(x + ".") for x in
                                  ("requests", "urllib", "http", "socket", "anthropic"))}
    check(not bad, f"the derived layer imports no network or model library ({sorted(mods)})")
    check("anthropic" not in sys.modules, "no model client was built")
    claude = (REPO / "CLAUDE.md").read_text(encoding="utf-8")
    check("validate_st_t5_prl" in __import__("gate_list").makefile_text(REPO)
          and "crypto.watch" in claude, "the Makefile runs this gate; CLAUDE.md names the class")


def group_h() -> None:
    head("H. THE SCHEDULED STEPS, THE ROSTER, THE BASKET (RULINGS 3 AND 4)")
    import datetime as _dt
    from altdata import feeds
    from altdata.sources import yfinance_source as yf
    db = str(TMP / "daily.sqlite")
    with observations.ObservationStore(db) as st:
        st.write_many(prl_rows())
        dr = prl.daily(dry_run=True, at=CUT, db=st, record=False)
        n0 = len(st.as_of("calc.prl_supply_code", CUT))
        real = prl.daily(dry_run=False, at=CUT, db=st, record=False)
        n1 = len(st.as_of("calc.prl_supply_code", CUT))
    check(dr["written"] == 0 and n0 == 0 and dr["rows"]
          and real["written"] > 0 and n1 == 1,
          f"the daily compute dry-runs (rows, nothing written), then writes "
          f"({real['written']} rows)")
    sk = prl.weekly(dry_run=True, today="2026-10-16")
    ran = prl.weekly(dry_run=False, today="2026-10-17", record=False,
                     get_text=lambda u: "User-agent: *\n")
    check("skipped" in sk and "Saturdays" in sk["skipped"]
          and ran["status"] == "PENDING" and ran["written"] == 0
          and "G-26" in str(ran["reason"]),
          "the explorer read runs on Saturdays; with no endpoint declared it is "
          "PENDING (the heartbeat's no-allowance state), never a blank")
    wrap = (REPO / "scripts" / "run_crypto_basket.sh").read_text(encoding="utf-8")
    lines = [ln for ln in wrap.splitlines() if ln.startswith("step ")]
    names = [ln.split()[1] for ln in lines]
    check("prl_weekly" in names and "prl_daily" in names
          and names.index("prl_daily") > names.index("derive")
          and names.index("prl_weekly") > names.index("derive"),
          "the basket's 17:25 run: one line each, after the basket's own writes; no new "
          "timer")
    units = [p.name for p in (REPO / "deploy" / "systemd").glob("*prl*")]
    check(not units, "no PRL unit or timer exists")
    src = (REPO / "altdata" / "feeds.py").read_text(encoding="utf-8")
    check("rosters += [(_prl.ROSTER, list(_prl.ROSTER_KEYS))]" in src
          and set(prl.ROSTER_KEYS) == set(prl.DAILY_KEYS) | set(prl.EXPLORER_KEYS),
          "both are on the freshness roster (prl), so the heartbeat sees them")
    # RULING 4: the basket still finds SM00118 by its ids
    res = yf.resolve_basket(yf.CRYPTO_BASKET)
    from altdata import security_master as sm
    e = sm.Master().by_coingecko("pearl-2")
    check(res.get("PRL41876-USD") == "crypto_prl" and e["id"] == "SM00118"
          and e["asset_class"] == "crypto.watch",
          "the basket's reader still resolves PRL to yfinance.crypto_prl through the "
          "reclassified SM00118 (one coin, one id)")


def main() -> int:
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g, group_h):
        g()
    print(f"\n{PASS} passed, {FAIL} failed")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
