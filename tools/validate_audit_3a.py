"""
AUD-3a: retrieval -- the store against the registry, the units, the sources, the
catalogue, the counts. (The data and architecture audit of 14 Oct 2026,
recommendations 12 and 15.)

What fits in no existing gate. check_registry carries the registry rules
themselves (aud3a_faults); this gate shows each one firing on a synthetic
registry, and holds the rest:

  A  THE RESOLVER (item 2). The five bulk blocks that resolved to nothing -- the
     46 overnight.* keys among them -- resolve; check_registry fails a block that
     expands to no key, a member with no entry, the undivided `percent`, a
     member_units key that is no member, and an unknown source.
  B  THE UNITS (item 3). Percent split by meaning, one fixture delta before and
     after for each changed rule; ^TNX in bp, ^VIX in points; pm.volume's unit per
     venue; a bar's volume unit per instrument; a level prints under the word it
     printed as before. Every key's delta rule equals fb67bf3's
     (tests/fixtures/aud3a_delta_rules_fb67bf3.json) unless declared below.
  C  THE STORE CHECK (item 1). tools/check_store_registry.py on a synthetic store:
     the three lists, the off-list sources, exit 0 / 1 / 2, and nothing written.
  D  SOURCE IDS (item 4). A stored string read as an id; a stored row never
     rewritten. The 15 Oct rulings: four internal writers' strings registered,
     alt_asset:<family> read as alt_asset, a bare `ibkr` resolved by its key's
     family through stored_aliases, each line with its reason.
  E  THE CATALOGUE (item 5). list, search, show, commands; every command module
     has its line; every metric has a description.
  F  THE COUNTS (item 6). Each count CLAUDE.md prints equals the code's.
  G  CLIENT IDS AND THE PRICE RANGE (item 7).

No gate reads the live store, fetches or calls a model.

    python tools/validate_audit_3a.py
"""

from __future__ import annotations

import io
import json
import os
import sqlite3
import sys
from contextlib import redirect_stdout
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gate_tmp                                                 # noqa: E402

LINE = "=" * 78
PASS = FAIL = 0
AS_OF = "2026-10-14T21:00:00+00:00"

# A members_from target that names nothing: the block that resolves to no key.
EMPTY_MEMBERS: list = []

# THE DELTA RULES AUD-3a CHANGES ON PURPOSE (item 3), with one fixture pair each:
# (prior level, level, the delta at fb67bf3, the delta now). Any other key whose
# rule moved from fb67bf3's fails group B.
CHANGED_RULES = {
    "yfinance.mkt_tnx": ("bps", (4.25, 4.32, 1.6471, 7.0)),
    "yfinance.mkt_tnx_open": ("bps", (4.25, 4.32, 1.6471, 7.0)),
    "yfinance.mkt_tnx_high": ("bps", (4.25, 4.32, 1.6471, 7.0)),
    "yfinance.mkt_tnx_low": ("bps", (4.25, 4.32, 1.6471, 7.0)),
    "yfinance.mkt_tyx": ("bps", (4.80, 4.75, -1.0417, -5.0)),
    "yfinance.mkt_tyx_open": ("bps", (4.80, 4.75, -1.0417, -5.0)),
    "yfinance.mkt_tyx_high": ("bps", (4.80, 4.75, -1.0417, -5.0)),
    "yfinance.mkt_tyx_low": ("bps", (4.80, 4.75, -1.0417, -5.0)),
    "yfinance.mkt_vix": ("pts", (18.0, 20.0, 11.1111, 2.0)),
    "yfinance.mkt_vix3m": ("pts", (20.0, 21.5, 7.5, 1.5)),
    "regime.dimension_percentile": ("pts", (40.0, 55.0, 1500.0, 15.0)),
    "chain.spy_atm_iv_30d": ("pts", (16.0, 18.5, 250.0, 2.5)),
    "calc.vol_spy_realized_20d": ("pts", (12.0, 14.0, 200.0, 2.0)),
    "zec.realized_vol_20d": ("pts", (80.0, 95.0, 1500.0, 15.0)),
    "calc.trend_spy_vs_50d": ("pp", (1.2, 1.5, 30.0, 0.3)),
    "calc.trend_spy_vs_200d": ("pp", (4.0, 3.5, -50.0, -0.5)),
    "calc.trend_spy_ma20_slope": ("pp", (0.8, 1.1, 30.0, 0.3)),
    "calc.stable_impulse_30d": ("pp", (2.0, 2.6, 60.0, 0.6)),
    "calc.stable_impulse_90d": ("pp", (5.0, 4.0, -100.0, -1.0)),
    "french.hml": ("pp", (-0.5, 1.2, 170.0, 1.7)),
    "french.ind49_ret_vw": ("pp", (1.0, -2.0, -300.0, -3.0)),
    "grade.return_pct": ("pp", (0.5, 2.5, 200.0, 2.0)),
    "grade.mae_close_pct": ("pp", (-1.0, -2.5, -150.0, -1.5)),
    "aaii.bull_bear_spread": ("pp", (10.0, 4.0, -600.0, -6.0)),
    "manual.cbo_deficit_path": ("pp", (5.9, 6.2, 30.0, 0.3)),
    # Ruled 15 Oct 2026 (follow-up 1): FRED's shares and rates of change, bp -> pp.
    "fred.u3_rate": ("pp", (4.1, 4.3, 20.0, 0.2)),
    "fred.lfp_rate": ("pp", (62.6, 62.4, -20.0, -0.2)),
    "fred.emp_pop_ratio": ("pp", (60.0, 59.8, -20.0, -0.2)),
    "fred.quits_rate": ("pp", (2.0, 2.1, 10.0, 0.1)),
    "fred.mortgage_delinq": ("pp", (1.73, 1.80, 7.0, 0.07)),
    "fred.cc_delinq_30": ("pp", (3.05, 3.12, 7.0, 0.07)),
    "fred.auto_delinq": ("pp", (2.62, 2.70, 8.0, 0.08)),
    "fred.cc_chargeoff": ("pp", (4.40, 4.25, -15.0, -0.15)),
    "fred.sticky_cpi": ("pp", (3.2, 3.5, 30.0, 0.3)),
    "fred.sticky_core": ("pp", (3.3, 3.1, -20.0, -0.2)),
    "fred.flex_cpi": ("pp", (1.0, 4.0, 300.0, 3.0)),
    "fred.fed_debt_pct_gdp": ("pp", (97.0, 98.5, 150.0, 1.5)),
    "fred.cre_delinq": ("pp", (1.40, 1.55, 15.0, 0.15)),
    # Ruled 15 Oct 2026 (follow-up 2): the MOVE and the VVIX are volatility
    # indexes, SKEW an index level -- percent -> points.
    "yfinance.mkt_vvix": ("pts", (90.0, 99.0, 10.0, 9.0)),
    "yfinance.mkt_move": ("pts", (80.0, 88.0, 10.0, 8.0)),
    "yfinance.mkt_skew": ("pts", (140.0, 146.0, 4.2857, 6.0)),
    # Ruled 15 Oct 2026 (AUD-3a part 1): the naive expectation and the surprise
    # follow their FRED series, bp -> pp.
    "calc.naive_expectation.u3_rate": ("pp", (4.1, 4.3, 20.0, 0.2)),
    "calc.naive_expectation.lfp_rate": ("pp", (62.6, 62.4, -20.0, -0.2)),
    "calc.naive_expectation.emp_pop_ratio": ("pp", (60.0, 59.8, -20.0, -0.2)),
    "calc.naive_expectation.quits_rate": ("pp", (2.0, 2.1, 10.0, 0.1)),
    "calc.naive_expectation.mortgage_delinq": ("pp", (1.73, 1.8, 7.0, 0.07)),
    "calc.naive_expectation.cc_delinq_30": ("pp", (3.05, 3.12, 7.0, 0.07)),
    "calc.naive_expectation.auto_delinq": ("pp", (2.62, 2.7, 8.0, 0.08)),
    "calc.naive_expectation.cc_chargeoff": ("pp", (4.4, 4.25, -15.0, -0.15)),
    "calc.naive_expectation.sticky_cpi": ("pp", (3.2, 3.5, 30.0, 0.3)),
    "calc.naive_expectation.sticky_core": ("pp", (3.3, 3.1, -20.0, -0.2)),
    "calc.naive_expectation.flex_cpi": ("pp", (1.0, 4.0, 300.0, 3.0)),
    "calc.naive_expectation.fed_debt_pct_gdp": ("pp", (97.0, 98.5, 150.0, 1.5)),
    "calc.surprise_vs_naive.u3_rate": ("pp", (0.1, -0.1, -20.0, -0.2)),
    "calc.surprise_vs_naive.lfp_rate": ("pp", (-0.1, 0.1, 20.0, 0.2)),
    "calc.surprise_vs_naive.emp_pop_ratio": ("pp", (0.0, -0.2, -20.0, -0.2)),
    "calc.surprise_vs_naive.quits_rate": ("pp", (0.1, 0.0, -10.0, -0.1)),
    "calc.surprise_vs_naive.mortgage_delinq": ("pp", (0.02, 0.05, 3.0, 0.03)),
    "calc.surprise_vs_naive.cc_delinq_30": ("pp", (0.05, 0.12, 7.0, 0.07)),
    "calc.surprise_vs_naive.auto_delinq": ("pp", (-0.03, 0.05, 8.0, 0.08)),
    "calc.surprise_vs_naive.cc_chargeoff": ("pp", (0.1, -0.05, -15.0, -0.15)),
    "calc.surprise_vs_naive.sticky_cpi": ("pp", (0.2, 0.5, 30.0, 0.3)),
    "calc.surprise_vs_naive.sticky_core": ("pp", (0.3, 0.1, -20.0, -0.2)),
    "calc.surprise_vs_naive.flex_cpi": ("pp", (-1.0, 2.0, 300.0, 3.0)),
    "calc.surprise_vs_naive.fed_debt_pct_gdp": ("pp", (0.5, 1.0, 50.0, 0.5)),
}
# The SLOOS five were already pp by their block's delta_unit at fb67bf3; the 15 Oct
# ruling gives them the unit `percent_share` and their rule does not move.
UNCHANGED_RULED = ("fred.sloos_ci_large", "fred.sloos_ci_small",
                   "fred.sloos_cre_construction", "fred.sloos_cre_nonres",
                   "fred.sloos_cre_multifamily")
# Keys the registry resolves for the first time (no rule at fb67bf3), by block:
# what the resolver fix and the bars blocks add.
NEW_KEY_BLOCKS = {"overnight_levels", "overnight_percent_changes", "event_columns",
                  "event_types", "pin_log_columns", "bars_prices",
                  "bars_volume_shares", "bars_volume_contracts", "bars_volume_usd"}
# Members a later branch added to an EXISTING block, declared by name: new by
# their spec line, not by the resolver fix (signal-triage Batch 5, ST-R4.23a:
# PPIDCS joins FRED_SIGNAL_SERIES, 16 Oct 2026; st-r5-rates declares its own two
# the same way -- the merge takes the union).
NEW_BLOCK_MEMBERS = {"fred.ppi_construction",
                     # ST-R4 Tranche 1 part 2 (Batch 5 items 18, 22, 27; 16 Oct
                     # 2026): two FRED contributions, four basket symbols with
                     # their actions, ZN=F's volume, TLT's and ZN=F's OHLC.
                     "fred.contrib_info_equipment", "fred.contrib_software",
                     *(f"yfinance.mkt_{s}{x}" for s in ("dspx", "cor1m", "cor3m",
                                                       "zn_front")
                       for x in ("", "_dividend", "_split")),
                     "yfinance.mkt_zn_front_volume",
                     *(f"yfinance.mkt_{s}_{x}" for s in ("tlt", "zn_front")
                       for x in ("open", "high", "low"))}


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


def registry() -> dict:
    import yaml
    return yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))


def source_ids_set() -> set:
    import yaml
    return set((yaml.safe_load((REPO / "source_registry.yaml").read_text(
        encoding="utf-8")) or {}).get("sources") or {})


# ---------------------------------------------------------------------------
# A. THE RESOLVER
# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. THE RESOLVER (item 2)")
    import copy
    import check_registry as cr
    from altdata import derived
    reg = registry()
    by: dict = {}
    resolved = derived.resolve_registry(reg, by)
    five = {"overnight_levels": 36, "overnight_percent_changes": 10,
            "event_columns": 12, "event_types": 6, "pin_log_columns": 83}
    got = {b: len(by.get(b) or []) for b in five}
    check(got == five, f"the five blocks that resolved to nothing now expand: {got}")
    ov = [k for k in resolved if k.startswith("overnight.")]
    ovb = [k for k in ov if derived.registry_entry(k).get("bulk_block")]
    check(len(ovb) == 46 and derived.registry_entry("overnight.es_chg_pct")
          .get("bulk_block") == "overnight_percent_changes",
          f"all 46 overnight.* block keys resolve, each naming its block ({len(ovb)}; "
          f"{len(ov) - len(ovb)} more registered one by one)")
    check(not [b for b, keys in by.items() if not keys],
          "every bulk block in the registry expands to at least one key")
    check(not cr.aud3a_faults(reg, source_ids_set()),
          "and check_registry's AUD-3a rules hold on the real registry")

    def faults_of(mutate) -> list:
        r = copy.deepcopy(reg)
        mutate(r)
        return [c for c, _ in cr.aud3a_faults(r, source_ids_set())]

    def empty_block(r):
        r["bulk_imports"]["overnight_levels"]["members_from"] = \
            "validate_audit_3a.EMPTY_MEMBERS"
    check("bulk block expands" in faults_of(empty_block),
          "a bulk block that expands to no key fails check_registry")

    def lost_member(r):
        r["bulk_imports"]["overnight_levels"]["members_from"] = "no.such.MODULE"
    check("bulk block expands" in faults_of(lost_member),
          "a block whose members cannot be found fails it too")

    def undivided(r):
        r["metrics"]["regime.dimension_percentile"]["units"] = "percent"
    check("percent is split" in faults_of(undivided),
          "the undivided `percent` on a metric fails")

    def stray_member_unit(r):
        r["bulk_imports"]["market_closes"]["member_units"]["yfinance.mkt_nope"] = \
            "vol_index"
    check("member_units names a member" in faults_of(stray_member_unit),
          "a member_units key that is no member of its block fails")

    def unknown_source(r):
        r["metrics"]["pm.volume"]["sources"] = ["kalshi", "polymarkett"]
    check("sources resolve" in faults_of(unknown_source),
          "a `sources` id that is not in source_registry.yaml fails")

    def no_map(r):
        r["metrics"]["pm.volume"].pop("units_by_source")
    check("units_by_source declared" in faults_of(no_map),
          "`units: by_source` without its map fails")


# ---------------------------------------------------------------------------
# B. THE UNITS
# ---------------------------------------------------------------------------
def group_b() -> None:
    head("B. THE UNITS (item 3)")
    from altdata import bars, derived
    base = json.loads((REPO / "tests" / "fixtures" / "aud3a_delta_rules_fb67bf3.json")
                      .read_text(encoding="utf-8"))["rules"]
    reg = registry()
    resolved = derived.resolve_registry(reg)
    moved = {k: (base[k], derived.delta_unit_for(k)[0]) for k in base
             if k in resolved and derived.delta_unit_for(k)[0] != base[k]}
    undeclared = sorted(set(moved) - set(CHANGED_RULES))
    check(len(CHANGED_RULES) == 65,
          f"the allowed-changes list is exactly 65: 25 (14 Oct), 16 (15 Oct "
          f"rulings 1-2), 24 (the naive expectation and surprise mirrors) "
          f"({len(CHANGED_RULES)})")
    check(not undeclared,
          f"no delta rule moved from fb67bf3's but the {len(CHANGED_RULES)} declared "
          f"({len(moved)} moved; undeclared: {undeclared[:6] or 'none'})")
    check(all(derived.delta_unit_for(k)[0] == want for k, (want, _) in
              CHANGED_RULES.items()),
          "and each declared one now reads its new rule")
    lost = sorted(k for k in base if k not in resolved)
    check(not lost, f"no key fb67bf3 resolved is lost ({lost[:5] or 'none'})")
    new = [k for k in resolved if k not in base]
    # A metric registered one by one since fb67bf3 (another branch's new series:
    # VP-1's calc.vp_*, stitched 15 Oct) is new by its own entry. A BLOCK key
    # first resolved must come from the resolver fix and the bars blocks.
    one_by_one = [k for k in new if k in (reg.get("metrics") or {})
                  or k in NEW_BLOCK_MEMBERS]
    blocks = {derived.registry_entry(k).get("bulk_block") for k in new
              if k not in one_by_one}
    check(blocks <= NEW_KEY_BLOCKS and None not in blocks,
          f"the {len(new) - len(one_by_one)} newly resolved block keys all come from "
          f"the resolver fix and the bars blocks ({sorted(b for b in blocks if b)}); "
          f"{len(one_by_one)} more are metrics registered one by one since")
    # One fixture delta before and after, for every declared change.
    bad = []
    for k, (unit, (a, b, before, after)) in CHANGED_RULES.items():
        was = derived._delta(b, a, base[k])                     # noqa: SLF001
        now = derived._delta(b, a, unit)                        # noqa: SLF001
        if was is None or abs(was - before) > 1e-3 or abs(now - after) > 1e-6:
            bad.append((k, was, now))
    check(not bad, "each declared change, one fixture pair: the delta at fb67bf3 "
          "and now (^TNX 4.25 -> 4.32: +1.6471% then, +7 bp now; ^VIX 18 -> 20: "
          f"+11.1111% then, +2 pts now; a percentile 40 -> 55: +1,500 bp then, "
          f"+15 pts now) {bad or ''}")
    # The split: every percent meaning has its unit and its rule.
    want = {"percent_rate": "bps", "percentile": "pts", "percent_return": "pp",
            "percent_share": "pp", "vol_pct": "pts", "vol_index": "pts"}
    vocab = set(reg["vocabularies"]["units"])
    check(all(derived.DELTA_UNITS.get(u) == r and u in vocab for u, r in want.items())
          and "pts" in reg["vocabularies"]["delta_unit"]
          and "pts" in derived.DELTA_UNITS_ALL,
          "the six units are declared in the units table and in the delta rule; "
          "`pts` is a delta unit")
    left = [k for k, m in reg["metrics"].items() if (m or {}).get("units") == "percent"]
    check(not left, f"no metric keeps the undivided percent ({len(left)})")
    # ^TNX and ^VIX.
    check(derived.delta_unit_for("yfinance.mkt_tnx")[0] == "bps"
          and derived.delta_unit_for("yfinance.mkt_vix")[0] == "pts"
          and derived.delta_unit_for("yfinance.mkt_spy")[0] == "percent",
          "^TNX is a yield (bp), ^VIX a volatility index (points); SPY is still a "
          "price (percent)")
    # FRED's % members: yields, rates and spreads keep bp; shares and rates of
    # change move in pp (ruled 15 Oct 2026); the SLOOS five were pp already.
    keep_bp = ("fred.hy_oas", "fred.yield_10y", "fred.mortgage_30y", "fred.fed_funds",
               "fred.breakeven_10y", "fred.effr_daily", "fred.gilt_10y")
    check(all(derived.delta_unit_for(k)[0] == "bps" for k in keep_bp)
          and derived.delta_unit_for("fred.u3_rate")[0] == "pp",
          "FRED's yields, rates and spreads keep basis points; U-3 moves in pp")
    sl = {k: (base[k], derived.delta_unit_for(k)[0],
              derived.registry_entry(k).get("units")) for k in UNCHANGED_RULED}
    check(all(v == ("pp", "pp", "percent_share") for v in sl.values()),
          f"the SLOOS five: percent_share, rule pp before and after ({len(sl)})")
    check(derived.delta_unit_for("yfinance.mkt_skew")[0] == "pts"
          and derived.level_units("index_points") == "price"
          and derived.registry_entry("yfinance.mkt_vvix").get("units") == "vol_index"
          and derived.registry_entry("yfinance.mkt_move").get("units") == "vol_index",
          "^VVIX and ^MOVE are vol_index, ^SKEW index_points (points; its level "
          "prints as the price it was)")
    # A level prints under the word it printed as before.
    check(derived.level_units("percent_share") == "percent"
          and derived.level_units("percentile") == "percent"
          and derived.level_units("vol_index") == "price"
          and derived.level_units("usd") == "usd",
          "a split unit's level prints as it did: percent's as percent, the VIX's as "
          "the price it was")
    from daily_cascade import stack as stack_mod
    check(stack_mod._lvl({"level_units": derived.level_units("percent_share"),   # noqa: SLF001
                          "level": 45.0}) == "45.00%",
          "the close's level formatter prints a share as 45.00%, as before")
    # A FRED member given its own unit on 15 Oct keeps FRED's word for its level
    # ("%", which the Monthly's v2 table prints bare); the closes keep LEVEL_UNITS'
    # (^TNX with %, accepted; the VIX, the MOVE, SKEW as prices).
    words = {k: derived.level_units_of(k) for k in (
        "fred.u3_rate", "fred.sticky_cpi", "fred.sloos_ci_large", "fred.cre_delinq",
        "fred.yield_10y", "yfinance.mkt_tnx", "yfinance.mkt_vix", "yfinance.mkt_move",
        "yfinance.mkt_skew", "yfinance.mkt_spy")}
    check(words == {"fred.u3_rate": "%", "fred.sticky_cpi": "%",
                    "fred.sloos_ci_large": "%", "fred.cre_delinq": "%",
                    "fred.yield_10y": "%", "yfinance.mkt_tnx": "percent",
                    "yfinance.mkt_vix": "price", "yfinance.mkt_move": "price",
                    "yfinance.mkt_skew": "price", "yfinance.mkt_spy": "price"},
          f"each level prints under the word it printed under on 14 Oct ({words})")
    from monthly_macro.writer import render_v2
    check(render_v2._macro_level({"units": derived.level_units_of("fred.u3_rate"),  # noqa: SLF001
                                  "level": 4.2})
          == render_v2._macro_level({"units": "%", "level": 4.2}),           # noqa: SLF001
          "the Monthly's v2 table prints U-3's level exactly as it did")
    # pm.volume, per venue.
    pv = reg["metrics"]["pm.volume"]
    check(pv.get("units") == "by_source" and pv.get("units_by_source") ==
          {"kalshi": "count", "polymarket": "usd"} and pv.get("sources") ==
          ["kalshi", "polymarket"]
          and derived.delta_unit_for("pm.volume")[0] == "raw",
          "pm.volume declares contracts on Kalshi, dollars on Polymarket; its "
          "change stays the raw difference")
    po = reg["metrics"]["pm.open_interest"]
    check(po.get("units_by_source") == {"kalshi": "count", "polymarket": "usd"},
          "pm.open_interest likewise (Kalshi's open interest, Polymarket's liquidity)")
    # A bar's volume unit per instrument.
    check(bars.volume_unit("SPY") == "shares" and bars.volume_unit("GC=F") == "count"
          and bars.volume_unit("ES=F") == "count"
          and bars.volume_unit("BTC-USD") == "usd"
          and bars.volume_unit("^TNX") is None
          and bars.volume_unit("DX-Y.NYB") is None,
          "a bar's volume: shares for an ETF, contracts for a future (ES=F too), "
          "dollars for Bitcoin, none for an index or the dollar index")
    check(derived.registry_entry("bars.gold.volume").get("units") == "count"
          and derived.registry_entry("bars.btc.volume").get("units") == "usd"
          and derived.registry_entry("bars.spy.volume").get("units") == "shares"
          and derived.registry_entry("bars.y10").get("units") == "percent_rate"
          and not derived.registry_entry("bars.y10.volume"),
          "the bars table's keys resolve with their units; a yield has no volume key")


# ---------------------------------------------------------------------------
# C. THE STORE CHECK
# ---------------------------------------------------------------------------
OBS_DDL = """
CREATE TABLE observations (
    id INTEGER PRIMARY KEY, registry_key TEXT NOT NULL, instrument TEXT,
    observed_at TEXT NOT NULL, available_at TEXT NOT NULL, ingested_at TEXT NOT NULL,
    value_num REAL, value_text TEXT, source TEXT NOT NULL, run_id TEXT,
    availability_kind TEXT);
"""


def seed_store(path: str, dirty: bool = True) -> None:
    from altdata import bars
    conn = sqlite3.connect(path)
    conn.executescript(OBS_DDL)
    rows = [("fred.hy_oas", None, "2026-10-14", "fred"),
            ("pm.probability", "kalshi:KX1", "2026-10-14", "kalshi:backfill"),
            ("pm.volume", "polymarket:0xab", "2026-10-14", "polymarket"),
            ("calc.trend_spy_vs_50d", None, "2026-10-14", "calc"),
            ("yfinance.mkt_spy", None, "2026-10-14", "yfinance")]
    if dirty:
        rows += [("yfinance.mkt_qqq", None, "2026-08-31", "yfinance"),   # stale
                 ("bogus.key", None, "2026-10-14", "fred"),              # unregistered
                 ("fred.ig_oas", None, "2026-10-14", "mystery_feed")]    # off the list
    conn.executemany(
        "INSERT INTO observations (registry_key, instrument, observed_at, "
        "available_at, ingested_at, value_num, source) VALUES (?,?,?,?,?,1.0,?)",
        [(k, i, d, d + "T21:00:00+00:00", d + "T21:00:00+00:00", s)
         for k, i, d, s in rows])
    conn.commit()
    conn.close()
    with bars.BarStore(path, create=True) as bst:
        bst.conn.executemany(
            "INSERT INTO bars (instrument, symbol, interval, observed_at, open, high,"
            " low, close, volume, available_at, ingested_at, source) VALUES "
            "(?,?,?,?,1,1,1,1,?,?,?,?)",
            [("spy", "SPY", "1d", "2026-10-14", 1000.0, "2026-10-14", "2026-10-14",
              "yfinance"),
             ("y10", "^TNX", "1d", "2026-10-14", 0.0, "2026-10-14", "2026-10-14",
              "yfinance")]
            + ([("zzz", "ZZZ", "1d", "2026-10-14", 5.0, "2026-10-14", "2026-10-14",
                 "yfinance")] if dirty else []))
        bst.conn.commit()


def group_c(td: str) -> None:
    head("C. THE STORE CHECK (item 1)")
    import hashlib
    import check_store_registry as csr
    db = str(Path(td) / "store.db")
    seed_store(db)
    before = (hashlib.sha256(Path(db).read_bytes()).hexdigest(),
              sorted(os.listdir(td)))
    r = csr.check(db, AS_OF)
    check(r["unregistered"] == ["bars.zzz", "bars.zzz.volume", "bogus.key"],
          f"list 1, stored and unregistered: a bogus key and a bar instrument the "
          f"tape does not declare ({r['unregistered']})")
    check([s["key"] for s in r["stale"]] == ["yfinance.mkt_qqq"]
          and r["stale"][0]["allowance"] == 1,
          f"list 3, stale by the key's own allowance (session half-life, 1): "
          f"{[(s['key'], s['sessions']) for s in r['stale']]}")
    check("fred.yield_10y" in r["no_rows"] and "yfinance.mkt_spy" not in r["no_rows"]
          and "bars.spy.volume" not in r["no_rows"]
          and "bars.y10.volume" not in r["no_rows"],
          f"list 2, registered with no rows ({len(r['no_rows'])}); a stored key and "
          f"a bar with volume are not on it")
    check(r["off_list_sources"] == ["mystery_feed"],
          f"list 4, the stored source strings on no list: kalshi:backfill, "
          f"polymarket and calc read as ids, 'mystery_feed' does not "
          f"({r['off_list_sources']})")
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = csr.main(["--db", db, "--as-of", AS_OF])
    check(rc == 1 and "FINDINGS" in buf.getvalue(), "exit 1 on findings")
    clean = str(Path(td) / "clean.db")
    seed_store(clean, dirty=False)
    with redirect_stdout(io.StringIO()):
        rc0 = csr.main(["--db", clean, "--as-of", AS_OF])
        rc2 = csr.main(["--db", str(Path(td) / "absent.db")])
    check(rc0 == 0, "exit 0 on a clean store (list 2 is read, not gated)")
    check(rc2 == 2, "exit 2 when the store cannot be opened")
    conn = csr.open_ro(db)
    try:
        conn.execute("INSERT INTO observations (registry_key, observed_at, "
                     "available_at, ingested_at, value_num, source) VALUES "
                     "('x','d','d','d',1,'s')")
        refused = False
    except sqlite3.OperationalError as exc:
        refused = "readonly" in str(exc).lower()
    finally:
        conn.close()
    check(refused, "it opens the store mode=ro: a write through its connection is "
          "refused")
    after = (hashlib.sha256(Path(db).read_bytes()).hexdigest(),
             sorted(os.listdir(td)))
    side = set(after[1]) - set(before[1]) - {"clean.db", "clean.db-wal",
                                              "clean.db-shm"}
    wal = Path(td) / "store.db-wal"
    check(before[0] == after[0] and side <= {"store.db-wal", "store.db-shm"}
          and (not wal.exists() or wal.stat().st_size == 0),
          f"and it wrote nothing: the store's bytes are unchanged; a WAL store "
          f"gains only SQLite's read index (-shm) and an empty -wal, which a "
          f"read-only connection cannot checkpoint away ({sorted(side)})")


# ---------------------------------------------------------------------------
# D. SOURCE IDS
# ---------------------------------------------------------------------------
# THE INTERNAL WRITERS' STRINGS (ruled 15 Oct 2026): id -> the file that writes it
# today, which must still carry the literal (the writers are not moved until
# aud-1-data-fixes merges).
INTERNAL_WRITERS = {
    "daily_close": ("daily_cascade/stack_close.py", '"source": "daily_close"'),
    "book_z": ("altdata/benchmark.py", '"source": "book_z"'),
    "narrative_register": ("altdata/narratives.py",
                           'LEDGER_SOURCE = "narrative_register"'),
    "paper_bid_chain": ("altdata/paper_bid.py", 'SOURCE = "paper_bid_chain"'),
    "alt_asset": ("altdata/thesis_register.py", "alt_asset:<family>"),
}


def group_d(td: str) -> None:
    head("D. SOURCE IDS (item 4)")
    from altdata import source_ids
    known = source_ids.ids()
    check({"kalshi", "polymarket", "calc", "fred"} <= known,
          "the controlled list is source_registry.yaml's ids (calc registered)")
    check(source_ids.canonical("kalshi:backfill") == "kalshi"
          and source_ids.canonical("fred:csv_migrated") == "fred"
          and source_ids.canonical("polymarket") == "polymarket",
          "an id is itself and <id>:<variant> is the id")
    check(source_ids.canonical("ibkr") is None
          and source_ids.canonical("nosuch:backfill") is None,
          "a string that is no id, alias or id-prefixed variant is off the list "
          "(a bare `ibkr` with no key to read its family by, too)")
    # The 15 Oct rulings.
    import yaml
    sreg = yaml.safe_load((REPO / "source_registry.yaml").read_text(encoding="utf-8"))
    srcs = sreg.get("sources") or {}
    bad = [sid for sid, (f, lit) in INTERNAL_WRITERS.items()
           if sid not in srcs or (srcs[sid] or {}).get("tier") != "derived"
           or (srcs[sid] or {}).get("implemented_by") != f
           or not (srcs[sid] or {}).get("timestamp_notes")
           or lit not in (REPO / f).read_text(encoding="utf-8")]
    check(not bad, f"the five internal strings are registered sources (tier derived), "
          f"each naming the file that writes it, which still writes it "
          f"({bad or sorted(INTERNAL_WRITERS)})")
    check(source_ids.canonical("alt_asset:gold") == "alt_asset"
          and source_ids.canonical("alt_asset:private_credit") == "alt_asset",
          "alt_asset:<family> reads as alt_asset, the family a suffix")
    fam = {"ibkr.auction_paired_qty": "ibkr_paper",
           "ibkr.auction_imbalance_side": "ibkr_paper",
           "ibkr.borrow_fee_rate": "ibkr_stock_loan",
           "ibkr.borrow_rebate_rate": "ibkr_stock_loan",
           "ibkr.shortable_shares": "ibkr_stock_loan",
           "ibkr.borrow_probe": "ibkr_paper",
           "ibkr.stock_loan_file_probe": "ibkr_paper",
           "portfolio.position_qty": None}
    got = {k: source_ids.canonical("ibkr", key=k) for k in fam}
    check(got == fam, "a bare `ibkr` resolves by the key's family -- the auction and "
          "the probes to ibkr_paper, the borrow rates and shares to ibkr_stock_loan, "
          f"as their writers write today; a family no line names stays off ({got})")
    lines = ((sreg.get("stored_aliases") or {}).get("ibkr") or {}).get(
        "by_key_family") or []
    shadow = [(a["prefix"], b["prefix"]) for i, a in enumerate(lines)
              for b in lines[i + 1:]
              if str(b["prefix"]).rstrip("*").startswith(str(a["prefix"]).rstrip("*"))]
    check(lines and all(ln.get("prefix") and ln.get("source") in srcs
                        and len(str(ln.get("reason") or "")) > 20 for ln in lines)
          and not shadow,
          f"each of the {len(lines)} ibkr lines names a prefix, a registered id and "
          f"its reason, and no line is shadowed by an earlier one ({shadow or 'none'})")
    import check_store_registry as csr
    db = str(Path(td) / "sources.db")
    seed_store(db, dirty=False)
    conn = sqlite3.connect(db)
    conn.executemany(
        "INSERT INTO observations (registry_key, instrument, observed_at, "
        "available_at, ingested_at, value_num, source) VALUES (?,?,?,?,?,1.0,?)",
        [(k, i, "2026-10-14", "2026-10-14T21:00:00+00:00",
          "2026-10-14T21:00:00+00:00", s) for k, i, s in (
            ("ibkr.borrow_fee_rate", "SPY", "ibkr"),
            ("ibkr.auction_paired_qty", "SPY", "ibkr"),
            ("dealer.scorecard_day", "SPY", "daily_close"),
            ("calc.trend_spy_vs_50d", None, "paper_bid_chain"),
            ("portfolio.position_qty", "SPY", "ibkr"))])
    conn.commit()
    conn.close()
    r = csr.check(db, AS_OF)
    d = r["off_list_detail"].get("ibkr") or {}
    rep = csr.report(r)
    check(d == {"rows": 1, "keys": 1, "examples": ["portfolio.position_qty"]}
          and "'ibkr': 1 rows under 1 key(s) -- e.g. portfolio.position_qty" in rep,
          f"each off-list string prints its row count and up to three example keys "
          f"({d})")
    check(r["off_list_sources"] == ["ibkr"],
          "the store check reads each row's source with its key: `ibkr` under the "
          "borrow and auction families and the internal strings are on the list, "
          f"`ibkr` under a family no line names is printed ({r['off_list_sources']})")
    check(source_ids.canonical("old text", known, {"old text": "fred"}) == "fred"
          and source_ids.canonical("old text", known, {"old text": "nosuch"}) is None,
          "a declared alias reads as its id, and only when that id exists")
    reg = registry()
    pm = {k: m for k, m in reg["metrics"].items() if k.startswith("pm.")
          and k != "pm.implied"}
    check(all((m or {}).get("sources") == ["kalshi", "polymarket"] for m in pm.values()),
          f"the {len(pm)} prediction-market metrics both venues write declare both")
    src = (REPO / "altdata" / "sources" / "prediction_markets.py").read_text(
        encoding="utf-8")
    check('f"{r[\'venue\']}:backfill"' in src
          and "<venue>:backfill" in reg["metrics"]["pm.probability"]["description"],
          "the registry names the backfill string the writer really stores")
    check("UPDATE observations" not in (REPO / "altdata" / "source_ids.py").read_text(
        encoding="utf-8"),
          "the mapping is applied when reading: nothing rewrites a stored row")


# ---------------------------------------------------------------------------
# E. THE CATALOGUE
# ---------------------------------------------------------------------------
def command_modules() -> list[str]:
    """Every module under altdata/, altdata/sources/ and altdata/loggers/ that runs
    as `python -m`."""
    import re
    out = []
    for d in ("altdata", "altdata/sources", "altdata/loggers"):
        for p in sorted((REPO / d).glob("*.py")):
            if re.search(r"__name__\s*==\s*.__main__.", p.read_text(encoding="utf-8")):
                out.append(p.relative_to(REPO).as_posix()[:-3].replace("/", "."))
    return out


def group_e(td: str) -> None:
    head("E. THE CATALOGUE (item 5)")
    from altdata import catalogue as cat
    cmds = cat.commands()
    mods = command_modules()
    missing = sorted(set(mods) - set(cmds))
    gone = sorted(set(cmds) - set(mods))
    check(not missing and not gone,
          f"every command module has its line in config/catalogue_commands.yaml "
          f"({len(mods)} modules; missing {missing or 'none'}; gone {gone or 'none'})")
    check(all(c.get("domain") and c.get("line") for c in cmds.values()),
          "and every line names a domain and says what the command does")
    reg = registry()
    nodesc = [k for k, m in reg["metrics"].items() if not (m or {}).get("description")]
    check(not nodesc, f"every registered metric has a description ({len(nodesc)} without)")
    pending = [k for k, m in reg["metrics"].items()
               if "description pending" in str((m or {}).get("description") or "")]
    check(not pending, f"none written as 'description pending' ({pending or 'none'})")
    for k, want in (("exposure.call_wall", "largest POSITIVE signed GEX"),
                    ("gates.oi_weighted_dte", "Open-interest-weighted days"),
                    ("portfolio.excess_liquidity", "ExcessLiquidity")):
        check(want in " ".join(str(reg["metrics"][k].get("description")).split()),
              f"{k}'s description is written from the code that computes it")
    # list, filtered four ways
    pm = [r["key"] for r in cat.rows(source="polymarket")]
    check("pm.volume" in pm and "pm.implied" not in pm,
          f"list --source polymarket: the keys Polymarket really writes, not the "
          f"reserved Kalshi-only one ({len(pm)})")
    ov = [r["key"] for r in cat.rows(kind="bulk", cad="intraday")]
    check("overnight.es_chg_pct" in ov and "bars.spy" in ov,
          f"list --kind bulk --cadence intraday reaches the overnight and bar keys "
          f"({len(ov)})")
    y = [r["key"] for r in cat.rows(kind="yield")]
    check("fred.yield_10y" in y and "yfinance.mkt_spy" not in y,
          f"list --kind yield, from series_kinds ({len(y)})")
    em = cat.rows(domain="option_chains")
    check(any(r["key"].startswith("exposure.") for r in em),
          "list --domain option_chains, from the source's domains")
    # search
    s1 = [r["key"] for r in cat.search("the VIX")]
    s2 = [r["key"] for r in cat.search("ExcessLiquidity")]
    check("yfinance.mkt_vix" in s1 and s2 == ["portfolio.excess_liquidity"],
          "search reaches an alias ('the VIX') and a description")
    # show, with a synthetic store, read-only
    db = str(Path(td) / "cat.db")
    seed_store(db, dirty=False)
    sh = cat.show("yfinance.mkt_vix")
    check(sh["units"] == "vol_index" and sh["delta_unit"] == "pts"
          and sh["level_prints_as"] == "price" and sh["bulk_block"] == "market_closes"
          and "python -m altdata.feeds" in sh["commands"]
          and "altdata/sources/yfinance_source.py" in sh["writers"],
          "show: the resolved units, the delta rule, the block, the writer and the "
          "command that runs it")
    st = cat.show("pm.volume", db=db)["store"]
    check(st == {"rows": 1, "first_observed": "2026-10-14",
                 "newest_observed": "2026-10-14"},
          f"show --db: the row count and the first and newest observation ({st})")
    bs = cat.show("bars.spy", db=db)["store"]
    check(bs["rows"] == 1, "show --db reads a bar instrument from the bars table")
    check(cat.show("no.such.key") is None, "show on an unknown id says so")
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cat.main(["commands", "--domain", "thailand"])
    check(rc == 0 and buf.getvalue().count("python -m ") == 5,
          "commands --domain thailand prints the five Thai commands, one line each")


# ---------------------------------------------------------------------------
# F. THE COUNTS
# ---------------------------------------------------------------------------
WORDS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen "
    "fourteen fifteen sixteen seventeen eighteen nineteen".split())}
TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
        "seventy": 70, "eighty": 80, "ninety": 90}


def number(tok: str) -> int:
    """'75', 'seventy-five', 'six' -> an int."""
    t = tok.lower().strip()
    if t.isdigit():
        return int(t)
    if t in WORDS:
        return WORDS[t]
    if t in TENS:
        return TENS[t]
    a, _, b = t.partition("-")
    return TENS[a] + WORDS[b]


def code_counts() -> dict:
    """Each count CLAUDE.md prints, computed from the code it describes."""
    import re

    import yaml
    from altdata import config
    from altdata.sources import yfinance_source as yf
    mk = (REPO / "Makefile").read_text(encoding="utf-8")

    def block(name):
        m = re.search(rf"^{name} := \\\n(.*?)(?:\n\n|\Z)", mk, re.S | re.M)
        return re.findall(r"tools/\S+", m.group(1)) if m else []
    py, sh, data = block("PY_VALIDATORS"), block("SH_VALIDATORS"), block("DATA_GATES")
    extra = len(re.findall(r"^EXTRA := (\S+)", mk, re.M))
    ms = yaml.safe_load((REPO / "config" / "market_state.yaml").read_text(
        encoding="utf-8"))
    small = (config.FRED_FX_SCAN_SERIES, config.FRED_SLOOS_SERIES,
             config.FRED_AQ3_SERIES, config.FRED_SR43_SERIES,
             config.FRED_THAILAND_SERIES)
    return {
        "fred_series": len(config.FRED_SERIES),
        "fred_signal": len(config.FRED_SIGNAL_SERIES),
        "fred_small": sum(len(x) for x in small),
        "fred_pull": len(config.FRED_PULL_SERIES),
        "symbols": len(yf.SYMBOLS),
        "data_store_csv": len(list((REPO / "data_store").glob("*.csv"))),
        "code_gates": len(py) + extra + len(sh),
        "python_gates": len(py) + extra,
        "shell_gates": len(sh),
        "data_gates": len(data),
        "dimensions": len(ms.get("dimensions") or {}),
        "dials": len(ms.get("dials") or {}),
        "contradictions": len(ms.get("contradictions") or []),
    }


# Each printed count: (what, a regex whose group 1 is the number, the code's key).
NUM = r"(\d+|[a-z]+(?:-[a-z]+)?)"
PRINTED_COUNTS = [
    ("FRED_SERIES", rf"Series registry: {NUM} SeriesSpec entries", "fred_series"),
    ("FRED_SIGNAL_SERIES", rf"Monthly's set; {NUM} more in FRED_SIGNAL_SERIES",
     "fred_signal"),
    ("the five smaller FRED lists", rf"freshness-watched; {NUM} in five smaller",
     "fred_small"),
    ("FRED_PULL_SERIES", rf"FRED_PULL_SERIES, {NUM}, is the union", "fred_pull"),
    ("yfinance symbols", rf"yfinance_source\.py\s+{NUM} market symbols", "symbols"),
    ("data_store CSVs", rf"Committed CSV store \({NUM} FRED series\)", "data_store_csv"),
    ("code gates", rf"runs every gate\*\* — {NUM} code gates", "code_gates"),
    ("Python gates", rf"code gates \({NUM} Python", "python_gates"),
    ("shell gates", rf"Python,\s+{NUM} shell\)", "shell_gates"),
    ("data gates", rf"shell\) and {NUM} data gates", "data_gates"),
    ("dimensions", rf"market_state\.yaml` — {NUM} dimensions", "dimensions"),
    ("dials", rf"dimensions, {NUM} dials", "dials"),
    ("contradiction rows", rf"dials and an {NUM}-row", "contradictions"),
]


def printed_count_faults(text: str, counts: dict) -> list[str]:
    import re
    out = []
    for what, rx, key in PRINTED_COUNTS:
        m = re.search(rx, text)
        if not m:
            out.append(f"{what}: the sentence is gone (pattern {rx!r})")
            continue
        try:
            n = number(m.group(1))
        except (KeyError, ValueError):
            out.append(f"{what}: {m.group(1)!r} is not a number")
            continue
        if n != counts[key]:
            out.append(f"{what}: CLAUDE.md prints {n}, the code has {counts[key]}")
    return out


def group_f() -> None:
    head("F. THE COUNTS (item 6)")
    text = (REPO / "CLAUDE.md").read_text(encoding="utf-8")
    counts = code_counts()
    faults = printed_count_faults(text, counts)
    check(not faults, f"each of the {len(PRINTED_COUNTS)} counts CLAUDE.md prints "
          f"equals the code's ({faults or counts})")
    # Plant 20 over whatever count the file prints (a hard-coded "27" stopped
    # planting anything the day a branch added a signal series).
    import re as _re
    stale = _re.sub(r"\b\d+ more in FRED_SIGNAL_SERIES", "20 more in FRED_SIGNAL_SERIES",
                    text, count=1)
    check(any("FRED_SIGNAL_SERIES: CLAUDE.md prints 20" in f
              for f in printed_count_faults(stale, counts)),
          "and a stale count is caught: the audit's '20 more in FRED_SIGNAL_SERIES'")
    # Plant a wrong count in words beside whatever count the file prints (every
    # branch that adds a gate moves it; AUD-3c moved it to seventy-six).
    import re
    worded = re.sub(r"\b[a-z]+-[a-z]+ code gates",
                    lambda m: ("seventy-four code gates"
                               if m.group(0) != "seventy-four code gates"
                               else "seventy-three code gates"), text, count=1)
    check(any("code gates" in f for f in printed_count_faults(worded, counts)),
          "a count in words is read and caught too ('seventy-four code gates')")
    gone = text.replace("market symbols", "symbols in the basket")
    check(any("sentence is gone" in f for f in printed_count_faults(gone, counts)),
          "and a sentence reworded so its count cannot be found fails rather than "
          "passing unchecked")
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    check("docs/chester-reports-architecture-v3.md" in readme
          and "docs/architecture-v3.md" not in readme
          and (REPO / "docs" / "chester-reports-architecture-v3.md").exists(),
          "the README names the architecture document by its real path")
    arch = (REPO / "docs" / "chester-reports-architecture-v3.md").read_text(
        encoding="utf-8")
    check("The store as built (AUD-3a, 14 Oct 2026)" in arch
          and arch.count("As built (14 Oct 2026)") >= 2,
          "the architecture document's store sections say what was built")


# ---------------------------------------------------------------------------
# G. CLIENT IDS AND THE PRICE RANGE
# ---------------------------------------------------------------------------
def group_g() -> None:
    head("G. CLIENT IDS AND THE PREDICTION-MARKET PRICE RANGE (item 7)")
    import logging
    import re
    from altdata.ibkr_clients import CLIENT_IDS
    from altdata.loggers import auction
    from altdata.sources import ibkr_costs, ibkr_portfolio, ibkr_whatif
    from altdata.sources import prediction_markets as pm
    import inspect
    ids = list(CLIENT_IDS.values())
    check(len(ids) == len(set(ids)), f"every client id in the table is unique {CLIENT_IDS}")
    check(CLIENT_IDS["whatif"] != CLIENT_IDS["watchdog"] == 18
          and ibkr_whatif.WHATIF_CLIENT_ID == CLIENT_IDS["whatif"],
          f"the what-if tool has its own id ({ibkr_whatif.WHATIF_CLIENT_ID}), not the "
          f"watchdog's 18")

    def default(fn, arg="client_id"):
        return inspect.signature(fn).parameters[arg].default
    check(ibkr_portfolio.DEFAULT_CLIENT_ID == CLIENT_IDS["portfolio_sync"]
          and default(ibkr_costs.place_or_preview if hasattr(ibkr_costs,
                      "place_or_preview") else _costs_fn(ibkr_costs)) == CLIENT_IDS["costs"]
          and default(auction._connect) == CLIENT_IDS["auction"],   # noqa: SLF001
          "the sync, the costs tool and the auction logger read their ids from it")
    # The three that carry the number themselves.
    sh = {"scripts/ibgateway_watchdog.sh": (r'WATCHDOG_CLIENT_ID:-(\d+)', "watchdog"),
          "scripts/sync_ibkr.sh": (r'IBKR_CLIENT_ID:-(\d+)', "portfolio_sync"),
          "altdata/loggers/borrow.py": (r'client_id=(\d+)', "borrow")}
    off = {}
    for rel, (rx, name) in sh.items():
        m = re.search(rx, (REPO / rel).read_text(encoding="utf-8"))
        if not m or int(m.group(1)) != CLIENT_IDS[name]:
            off[rel] = m.group(1) if m else None
    check(not off, f"the watchdog's and the sync's shell defaults and the borrow "
          f"logger's literal agree with the table ({off or 'all agree'})")
    # Every literal client id in the code is in the table.
    lits = set()
    for path in list((REPO / "altdata").rglob("*.py")) + [REPO / "tools" / "decide.py"]:
        for m in re.finditer(r"client_id(?:: int)? ?= ?(\d+)\b",
                             path.read_text(encoding="utf-8")):
            lits.add(int(m.group(1)))
    check(lits <= set(ids), f"no client id literal outside the table ({sorted(lits)})")
    # The range check.
    lg = logging.getLogger("altdata.sources.prediction_markets")
    seen: list = []

    class H(logging.Handler):
        def emit(self, rec):
            seen.append(rec.getMessage())
    h = H()
    lg.addHandler(h)
    try:
        k = pm.parse_kalshi_event({"event": {"event_ticker": "E"}, "markets": [
            {"ticker": "BAD", "last_price_dollars": "1.7"},
            {"ticker": "OK", "last_price_dollars": "0.42"}]}, "w")
        p = pm.parse_polymarket_event({"markets": [
            {"conditionId": "0xbad", "outcomePrices": '["-0.2", "1.2"]',
             "outcomes": '["Yes", "No"]'},
            {"conditionId": "0xok", "outcomePrices": '["0.31", "0.69"]',
             "outcomes": '["Yes", "No"]'}]}, "w")
    finally:
        lg.removeHandler(h)
    check([r["market_id"] for r in k] == ["OK"] and [r["market_id"] for r in p]
          == ["0xok"] and k[0]["probability"] == 0.42,
          "a last price outside its venue's 0..1 is dropped (the market with no "
          "price is skipped); one inside is kept")
    check(len(seen) == 2 and all("outside" in m and "dropped" in m for m in seen),
          f"and each drop is logged with the venue, the price and the market "
          f"({len(seen)} logged)")
    check(pm.price(0.40, 0.44, 7.0) == (0.42, "mid"),
          "a valid mid is untouched by the fallback's check")


def _costs_fn(mod):
    import inspect
    return next(f for _, f in inspect.getmembers(mod, inspect.isfunction)
                if "client_id" in inspect.signature(f).parameters
                and f.__module__ == mod.__name__)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    td = gate_tmp.mkdtemp(prefix="validate_audit_3a_")
    print(f"{LINE}\nAUD-3a: retrieval -- the store, the units, the sources, the "
          f"catalogue, the counts\n{LINE}")
    for g in (group_a, group_b, lambda: group_c(td), lambda: group_d(td),
              lambda: group_e(td),
              group_f, group_g):
        g()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
