"""
6i-1 -- the Quarterly's class-W rows switched to their stored keys (A77, 26 Oct
2026; docs/briefs/6i-spec-draft-2026-10-25.md, section 4.1 and the appendix).

    python tools/validate_quarterly_rows_6i.py

The brief classified the 230 rows of config/quarterly_chapters.yaml that print
"not tracked" and found 40 of class W: a key in metrics_registry.yaml covers the
row, and the row was never switched. This gate holds the switch:

  A  every switched W row names registered keys and no longer carries the reason
     the brief read; the six that keep part of a reason keep only the part that
     is still not stored, and say so
  B  the three W rows that stay: USD/THB in the currency pairs, on the operator's
     ruling (AQ-3 part 1, Needs you 2); and SOL's and ZEC's derivatives, which
     the brief read as W but whose keys (hl.funding, fut.funding_okx,
     calc.oi_mcap, calc.funding_agg, the Farside flows) are BTC and ETH only
  C  no other row's class changed: the count of rows carrying a reason, family by
     family, is the base's less the switched rows plus the declared remainders
  D  a fixture render: a switched row prints a value where the fixture store
     holds one and "not tracked" with its reason where it does not; a coin page
     and a measurable read the instrument the config names, not the all-chain row

Fixtures only: no store, no network.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

from altdata import derived                                    # noqa: E402
from monthly_macro import quarterly_items as qi                 # noqa: E402

PASS = FAIL = 0


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  ok    {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


# THE SWITCHED ROWS: (family, where, locator, the keys it must now read, the
# reason the brief read and that must be gone). `where` is structure / five_lines
# / panel:<id> (a series panel's rows, by label), analysis (by id), test (a
# falsification test, by id) or coin:<id>.<field>.
SWITCHED = [
    ("currency", "structure", "The EM dollar index (DTWEXEMEGS)", ["fred.dxy_em"], "not stored (AQ-3)"),
    ("currency", "structure", "Stablecoin supply, all chains (DefiLlama)", ["llama.stable_total"], "not stored (AQ-3)"),
    ("currency", "analysis", "stablecoin_dollarisation", ["llama.stable_total"], "stablecoin supply is not stored (AQ-3)"),
    ("currency", "test", "stablecoins_dollar", ["llama.stable_total"], "stablecoin supply is not stored (AQ-3)"),
    ("em", "structure", "The EM dollar index (DTWEXEMEGS)", ["fred.dxy_em"], "FRED's emerging-market dollar index is not in the pull (AQ-3)"),
    ("em", "analysis", "em_copper_gold", ["corr.copper_gold__10y.60d", "corr.copper_gold__10y.252d"], "the correlation layer's rows (aq-5-correlation-layer)"),
    ("china", "analysis", "china_imf_gold", ["safe.gold_reserves_oz", "imf.ifs.gold_reserves_oz.chn"], "imf-ifs-gold (imf.ifs.gold_reserves_oz.chn)"),
    ("china", "panel:china_observables", "Property: starts (NBS, floor space newly started, year to date)", ["nbs.re_starts_ytd"], "not stored (AQ-3, China property)"),
    ("crypto", "structure", "Stablecoin total supply (S-1)", ["llama.stable_total"], "not stored (AQ-3)"),
    ("crypto", "structure", "BTC long-term-holder supply, % of supply (SR-29)", ["btcdata.lth_supply_share"], "not stored"),
    ("crypto", "structure", "OI-weighted funding, BTC (S-3; crowded at z > +2 with OI/mcap at a 90-day high)", ["calc.funding_agg"], "not stored"),
    ("crypto", "structure", "The DVOL regime (S-4, DS-41)", ["deribit.dvol_btc"], "not stored"),
    ("crypto", "structure", "Hashrate (mempool.space)", ["mempool.hashrate"], "not stored"),
    ("crypto", "structure", "Treasury-company premium to NAV: MSTR's mNAV (item 49a)", ["calc.mnav"], "not stored; a named Gap"),
    ("crypto", "analysis", "stable_bills", ["llama.stable_total"], "stablecoin supply is not stored (AQ-3)"),
    ("crypto", "test", "sol_pmf", ["llama.chain_tvl", "yfinance.mkt_btc_usd"], "Solana's application TVL is not stored (AQ-3)"),
    ("crypto", "test", "stablecoin_infra", ["llama.stable_total"], "stablecoin supply is not stored (AQ-3)"),
    ("crypto", "coin:btc.supply", None, ["btcdata.lth_supply_share"], "circulating against fully diluted, LTH supply (SR-29), lost coins and ETF/treasury holdings — the effective float — are not stored"),
    ("crypto", "coin:btc.derivatives", None, ["calc.funding_agg", "calc.oi_mcap", "deribit.dvol_btc", "farside.btc_total"], "funding, OI (S-3), CME positioning, DVOL (DS-41) and ETF flows are not stored"),
    ("crypto", "coin:eth.market", None, ["yfinance.mkt_eth_usd"], "ETH is not in the price feed (AQ-3)"),
    ("crypto", "coin:eth.derivatives", None, ["hl.funding", "fut.funding_okx", "calc.oi_mcap", "farside.eth_total"], "funding, OI and ETF flows are not stored"),
    ("crypto", "coin:sol.economics", None, ["llama.chain_tvl"], "application TVL and its composition are not stored"),
    ("crypto", "coin:sol.usage", None, ["llama.chain_tvl"], "application TVL, DEX volume and the memecoin share are not stored"),
    ("crypto", "coin:sol.market", None, ["yfinance.mkt_sol_usd"], "SOL is not in the price feed (AQ-3)"),
    ("crypto", "coin:prl.supply", None, ["calc.prl_supply_code", "calc.prl_overhang", "calc.prl_supply_gap"], "D1-D3 (code supply, week-one overhang, supply gap) are not stored (ST-13)"),
    ("crypto", "coin:prl.market", None, ["calc.prl_venue_conc"], "S3 (exchange access) and D5 (venue concentration) are not stored (ST-13)"),
    ("crypto", "coin:prl.derivatives", None, ["calc.prl_emission_to_volume"], "S6 and D4 (emission-to-volume) are not stored (ST-13)"),
    ("crypto", "panel:category_gauges", "Stablecoin supply, all chains (S-1)", ["llama.stable_total"], "not stored (AQ-3)"),
    ("crypto", "panel:category_gauges", "Memecoin froth (S-5), Solana new pools, z (unscored until 90 days are stored)", ["calc.froth_z"], "not stored (AQ-3)"),
    ("real_estate", "structure", "House prices: Case-Shiller national, NSA (nominal; the real year-on-year read against CPI is not computed here)", ["fred.case_shiller_national"], "Case-Shiller is not in the FRED pull (AQ-3)"),
    ("intl_equities", "structure", "Hedged against unhedged, HEFA/EFA (\"two decisions wearing one ticker\")", ["calc.hefa_efa"], "the hedged funds are not in the price feed (AQ-3)"),
    ("intl_equities", "structure", "The euro fragmentation spread (BTP less Bund, 10-year, bp)", ["calc.btp_bund_bp"], "Italian and German 10-year yields are not stored (AQ-3)"),
    ("thailand", "five_lines", "The BoT policy rate", ["thai.bot_policy_rate"], "the BoT API is not pulled (AQ-3, AQ-12)"),
    ("thailand", "structure", "The BoT policy rate (its stated path is not stored)", ["thai.bot_policy_rate"], "the BoT API is not pulled (AQ-3, AQ-12)"),
    ("thailand", "structure", "Thai CPI, year on year", ["thai.cpi_yoy"], "not pulled (AQ-3, AQ-12)"),
    ("thailand", "structure", "Tourist arrivals", ["thai.tourist_arrivals"], "not pulled (AQ-3, AQ-12)"),
]
# Two W rows became two keyed rows each (S-3's legs; the treasury companies'
# activity and premium); their second rows are held here.
SECOND_ROWS = [
    ("crypto", "structure", "Open interest over market cap, BTC (S-3's second leg)", ["calc.oi_mcap"]),
    ("crypto", "structure", "Treasury-company activity: the month's net BTC bought (item 49b)", ["calc.treasury_net_purchases"]),
]
# PRL's definition is not a series: it now points at the Security Master entry
# ST-13 built, as the coin pages point at their papers.
PRL_DEFINITION = "the Security Master's SM00118"

# The remainders: what a switched row still does not hold, by its own reason.
REMAINDERS = {
    "circulating against fully diluted, lost coins and ETF/treasury holdings — the rest of the effective float — are not stored",
    "CME positioning is not stored",
    "the TVL's composition is not stored",
    "Solana's DEX volume (llama.dex_volume is all chains) and the memecoin share are not stored",
    "S3 (exchange access) is not stored (ST-13); D5's one input, CoinGecko's tickers, is retired (rulings of 13 and 18 Oct 2026)",
    "S6 is not stored (ST-13)",
    "not stored",                                    # Miner reserves, its own row now
    "issuer attestations are not stored (AQ-3)",     # Stablecoin supply by issuer
}

# The rows carrying a reason (absent / waits / not_measured), family by family:
# the brief's 230 less the switched rows plus the remainders, less the rows a
# later paste switched (LATER_SWITCHED). A change to any other row moves a count.
# Updated at the chain-8 stitch (D42.11, 29 Oct 2026), old -> new: oil_energy
# 24 -> 20, currency 18 -> 17, crypto 66 -> 63, agriculture 15 -> 11; the rest
# unchanged. The evidence is b69's and b70's readers (docs/briefs/b69-quarterly-
# readers-1-notes.md, b70-quarterly-readers-2-notes.md): fifteen rows filled from
# a stored key, three of them leaving a remainder row that still carries a reason
# ("Crude skew", "RWA holder count", "WASDE production and trade lines"), so
# twelve rows switched off a reason, recorded below with the key each reads.
REASON_ROWS = {"metals": 14, "oil_energy": 20, "currency": 17, "em": 8, "china": 21,
               "crypto": 63, "real_estate": 5, "credit": 12, "intl_equities": 13,
               "thailand": 4, "agriculture": 11}
BASE_REASON_ROWS = 230
# Rows switched off a reason after 6i-1, each by the paste that built its reading:
# credit's "HY spread acceleration" reads the T&B harness's overlay (6i-4, A79).
LATER_SWITCHED = {("credit", "HY spread acceleration"): "harness_overlay",
                  # b69's readers (D34): the EIA buffers, NOAA's ONI, CFTC's
                  # disaggregated grains, WASDE (corn and wheat; soybeans' row
                  # is carried by the WASDE remainder), MoF's intervention.
                  ("oil_energy", "The SPR beside commercial stocks, barrels (EIA, b69)"): "key",
                  ("oil_energy", "Refinery utilisation, % (EIA, b69)"): "key",
                  ("oil_energy", "US working gas in storage, Bcf, against the five-year "
                                 "band (EIA, b69)"): "key",
                  ("oil_energy", "US LNG exports, MMcf, monthly (EIA, b69); daily "
                                 "feedgas not tracked"): "key",
                  ("agriculture", "WASDE corn, stocks-to-use, %, the 2026/27 projection "
                                  "(USDA)"): "key",
                  ("agriculture", "WASDE wheat, stocks-to-use, %, the 2026/27 projection "
                                  "(USDA)"): "key",
                  ("agriculture", "NOAA's ENSO state, the ONI, deg C (context, never "
                                  "extrapolated to price)"): "key",
                  ("agriculture", "Corn, managed money net, % of open interest (CFTC "
                                  "disaggregated)"): "key",
                  ("currency", "Japan's FX intervention in the release period, yen "
                               "(Ministry of Finance, Japan)"): "key",
                  # b70's readers (D34): DefiLlama's TVL and iShares' AUM.
                  ("crypto", "Tokenised treasuries and RWA, TVL, USD (DefiLlama)"): "key",
                  ("crypto", "Arbitrum TVL, USD (DefiLlama)"): "key",
                  ("crypto", "IBIT net assets, USD (iShares; level, not flow)"): "key"}


def reason_rows(fams: dict) -> dict:
    out: dict[str, int] = {}

    def walk(x, fid):
        if isinstance(x, dict):
            out[fid] = out.get(fid, 0) + sum(
                1 for f in ("absent", "waits", "not_measured") if isinstance(x.get(f), str))
            for v in x.values():
                walk(v, fid)
        elif isinstance(x, list):
            for v in x:
                walk(v, fid)
    for fid, f in fams.items():
        out.setdefault(fid, 0)
        walk(f, fid)
    return out


def leaves(m) -> list[dict]:
    if not isinstance(m, dict):
        return []
    if "all" in m or "any" in m:
        return [x for leg in (m.get("all") or m.get("any")) for x in leaves(leg)]
    return [p for p in m.values() if isinstance(p, dict)]


def find(fam: dict, where: str, loc: str):
    if where in ("structure", "five_lines"):
        return next((s for s in fam.get(where) or [] if s.get("label") == loc), None)
    if where.startswith("panel:"):
        p = next((p for p in fam.get("panels") or [] if p.get("id") == where[6:]), {})
        return next((s for s in p.get("rows") or [] if s.get("label") == loc), None)
    if where == "analysis":
        return next((a for a in fam.get("analyses") or [] if a.get("id") == loc), None)
    if where == "test":
        return next((t for t in fam.get("falsification") or [] if t.get("id") == loc), None)
    if where.startswith("coin:"):
        cid, fld = where[5:].split(".")
        for p in fam.get("panels") or []:
            for c in p.get("coins") or []:
                if c.get("id") == cid:
                    return (c.get("fields") or {}).get(fld)
    return None


def keys_of(where: str, spec: dict) -> list[str]:
    if where == "test":
        return [p.get("series") for p in leaves(spec.get("measurable")) if p.get("series")]
    if where.startswith("coin:"):
        return list(spec.get("keys") or [])
    return list(spec.get("series") or []) + qi.spec_keys(spec)


def group_a(fams: dict) -> None:
    print("A. the switched rows read registered keys")
    missing, wrong, unreg, kept = [], [], [], []
    for fid, where, loc, want, old in SWITCHED:
        spec = find(fams[fid], where, loc)
        tag = f"{fid}/{where}/{loc or ''}"
        if spec is None:
            missing.append(tag)
            continue
        got = keys_of(where, spec)
        if sorted(set(got)) != sorted(set(want)):
            wrong.append(f"{tag}: {got}")
        unreg += [k for k in got if not derived.registry_entry(k)]
        left = [spec.get(f) for f in ("absent", "waits", "not_measured") if spec.get(f)]
        if old in left or any(x not in REMAINDERS for x in left):
            kept.append(f"{tag}: {left}")
    for fid, where, loc, want in SECOND_ROWS:
        spec = find(fams[fid], where, loc)
        if spec is None or qi.spec_keys(spec) != want:
            wrong.append(f"{fid}/{where}/{loc}")
    n = len(SWITCHED) + len(SECOND_ROWS)
    check(not missing, f"all {len(SWITCHED)} switched rows are found where the config "
                       f"keeps them {missing[:2]}")
    check(not wrong, f"each names the keys the brief's appendix names ({n} rows) {wrong[:2]}")
    check(not unreg, f"every key is registered {sorted(set(unreg))[:3]}")
    check(not kept, f"the brief's reason is gone; a row that keeps one keeps only a "
                    f"declared remainder {kept[:2]}")
    prl = find(fams["crypto"], "coin:prl.definition", None) or {}
    check(PRL_DEFINITION in str(prl.get("paper")) and not prl.get("absent"),
          "PRL's definition points at the Security Master entry ST-13 built (SM00118)")
    th = [s for s in (fams["thailand"].get("five_lines") or []) + (fams["thailand"].get("structure") or [])
          if str(s.get("key") or "").startswith("thai.")]
    check(len(th) == 4 and all(s.get("namespace") == "thailand" for s in th)
          and all((derived.registry_entry(s["key"]) or {}).get("trigger_eligible") is False
                  for s in th),
          "the four Thailand rows keep namespace: thailand on keys that are never "
          "trigger-eligible (the isolation)")


def group_b(fams: dict) -> None:
    print("B. the W rows that stay")
    pair = [p for p in (fams["currency"].get("pairs") or {}).get("deep") or []
            if p.get("pair") == "USD/THB"]
    check(len(pair) == 1 and not pair[0].get("key")
          and "read here only on the operator's ruling" in str(pair[0].get("absent")),
          "USD/THB in the currency pairs stays unswitched, on the operator's ruling "
          "(AQ-3 part 1, Needs you 2)")
    stays = []
    for cid in ("sol", "zec"):
        spec = find(fams["crypto"], f"coin:{cid}.derivatives", None) or {}
        stays.append(spec.get("absent") == "funding, OI and ETF flows are not stored")
    check(all(stays), "SOL's and ZEC's derivatives stay not tracked: the funding, OI and "
                      "flow keys are BTC and ETH only (the brief read them as W)")
    for k in ("hl.funding", "fut.funding_okx", "calc.oi_mcap", "calc.funding_agg"):
        d = str((derived.registry_entry(k) or {}).get("description"))
        check("BTC or ETH" in d, f"{k}'s registry entry names its instruments BTC or ETH")


def group_c(fams: dict) -> None:
    print("C. no other row's class changed")
    got = reason_rows(fams)
    check(got == REASON_ROWS, f"the rows carrying a reason, by family, are the pinned "
                              f"counts ({sum(got.values())} of the base's {BASE_REASON_ROWS}) "
                              f"{ {k: v for k, v in got.items() if REASON_ROWS.get(k) != v} }")
    switched = len(SWITCHED)
    whole = 1 + sum(1 for fid, where, loc, _, _ in SWITCHED      # 1: PRL's definition
                    if not any((find(fams[fid], where, loc) or {}).get(f)
                               for f in ("absent", "waits", "not_measured")))
    later = len(LATER_SWITCHED)
    check(BASE_REASON_ROWS - whole + 2 - later == sum(REASON_ROWS.values()),
          f"the arithmetic: 230 less the {whole} rows switched whole, plus the two "
          f"remainder rows, less {later} switched later, is {sum(REASON_ROWS.values())} "
          f"({switched} switched, {switched - whole + 1} keeping a remainder)")
    for (fid, label), field in LATER_SWITCHED.items():
        rows = []

        def walk(x):
            if isinstance(x, dict):
                if x.get("label") == label:
                    rows.append(x)
                for v in x.values():
                    walk(v)
            elif isinstance(x, list):
                for v in x:
                    walk(v)
        walk(fams[fid])
        check(len(rows) == 1 and rows[0].get(field)
              and not any(rows[0].get(f) for f in ("absent", "waits", "not_measured")),
              f"{fid}'s \"{label}\" is switched by a later paste: it reads {field}, no reason")


class FakeStore:
    """as_of over a dict {(key, instrument): [(day, value)]}: every row knowable."""

    def __init__(self, data: dict) -> None:
        self.data = data

    def as_of(self, key, now=None, inst=None, observed_from=None):
        return [{"observed_at": d, "value_num": v, "available_at": f"{d}T21:00:00+00:00",
                 "source": "fixture"} for d, v in self.data.get((key, inst), [])]


def series(start: float, step: float, days: int = 200) -> list[tuple[str, float]]:
    import datetime as dt
    d0 = dt.date(2026, 3, 1)
    return [((d0 + dt.timedelta(days=i)).isoformat(), start + step * i) for i in range(days)]


def group_d(fams: dict) -> None:
    print("D. a fixture render")
    ctx = {"now": "2026-10-10T12:00:00+00:00", "start": "2026-06-30", "end": "2026-09-30",
           "common": qi.load_config().get("common") or {}}
    st = FakeStore({
        ("fred.dxy_em", None): series(120.0, 0.01),
        ("yfinance.mkt_eth_usd", None): series(3000.0, 1.0),
        ("llama.chain_tvl", None): series(9e10, 1e8),          # all chains, rising
        ("llama.chain_tvl", "Solana"): series(9e9, -1e6),      # Solana, falling
        ("yfinance.mkt_btc_usd", None): series(60000.0, 50.0),
    })
    cur = fams["currency"]
    specs = [s for s in cur["structure"] if s.get("key") in ("fred.dxy_em", "llama.stable_total")]
    rws, nt, _ = qi.structure_rows(st, specs, ctx)
    check(any(r[0] == "The EM dollar index (DTWEXEMEGS)" and r[1] != "—" for r in rws),
          "a switched row prints its value where the fixture store holds one (the EM "
          "dollar index)")
    check(any(x.startswith("Stablecoin supply, all chains (DefiLlama): ") for x in nt)
          and not any(r[0].startswith("Stablecoin supply") for r in rws),
          f"and prints as not tracked, by name with its reason, where it holds none "
          f"(stablecoin supply: {next((x for x in nt if x.startswith('Stablecoin')), '')!r})")
    coins = {c["id"]: c for p in fams["crypto"]["panels"] if p.get("kind") == "coins"
             for c in p.get("coins") or []}
    eth = qi.coin_page(st, coins["eth"], fams["crypto"], ctx, {})
    sol = qi.coin_page(st, coins["sol"], fams["crypto"], ctx, {})
    erow = dict((r[0], r[1]) for r in eth["table"]["rows"])
    srow = dict((r[0], r[1]) for r in sol["table"]["rows"])
    mk = next(lab for f, lab in qi.COIN_FIELDS if f == "market")
    us = next(lab for f, lab in qi.COIN_FIELDS if f == "usage")
    check(erow[mk].startswith("yfinance.mkt_eth_usd ") and "not yet" not in erow[mk],
          f"ETH's market field reads its price ({erow[mk][:48]!r})")
    check(srow[mk] == "yfinance.mkt_sol_usd: nothing stored",
          f"SOL's market field says nothing is stored where the fixture holds none "
          f"({srow[mk]!r})")
    sol_last = qi.fmt_level(st.data[("llama.chain_tvl", "Solana")][-1][1], "llama.chain_tvl")
    check(srow[us].startswith(f"llama.chain_tvl {sol_last} ")
          and "the rest not yet — Solana's DEX volume" in srow[us],
          f"SOL's usage reads Solana's TVL, not the all-chain row, and keeps its "
          f"remainder ({srow[us][:70]!r})")
    sol_pmf = next(t for t in fams["crypto"]["falsification"] if t["id"] == "sol_pmf")
    r = qi.evaluate(st, sol_pmf["measurable"], ctx)
    check(r.get("met") is True and "llama.chain_tvl" in r.get("evidence", ""),
          f"sol_pmf reads Solana's TVL down while BTC rose: failed ({r.get('evidence', '')[:80]!r})")
    inf = next(t for t in fams["crypto"]["falsification"] if t["id"] == "stablecoin_infra")
    grow = FakeStore({("llama.stable_total", None): series(2.0e11, 1e8, 400)})
    fall = FakeStore({("llama.stable_total", None): series(2.6e11, -1e8, 400)})
    g, f = qi.evaluate(grow, inf["measurable"], ctx), qi.evaluate(fall, inf["measurable"], ctx)
    check(g.get("met") is False and f.get("met") is None and "price stability" in f.get("missing", ""),
          "stablecoin_infra holds while supply grows, and a contraction prints not "
          "measured until \"price stability\" has a reading")


def main() -> int:
    line = "=" * 72
    print(f"{line}\n6i-1 -- the Quarterly's W rows switched to their stored keys\n{line}")
    fams = qi.load_config()["families"]
    group_a(fams)
    group_b(fams)
    group_c(fams)
    group_d(fams)
    print(f"\n{line}\n{PASS} passed, {FAIL} failed\n{line}")
    print("VALIDATION FAILED" if FAIL else "VALIDATION PASSED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
