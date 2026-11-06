"""
The yfinance exposure, inventoried (B68, the price-source migration brief; D33 of
24 Oct 2026).

    python -m tools.price_source_inventory            # Markdown, to stdout
    python -m tools.price_source_inventory --json     # the same, as JSON

READ-ONLY. It reads metrics_registry.yaml, source_registry.yaml and the code's own
symbol tables (altdata/sources/yfinance_source.py, altdata/bars.py,
altdata/sources/overnight.py, tools/pin_log.py), and it scans the tree's .py and
config .yaml files for the keys. It opens no store, makes no request and writes
nothing. Its output is the exposure table of
docs/briefs/price-source-migration-brief-2026-10-25.md, section 1.

What it counts, per group: the keys whose source is Yahoo, the files that name
them (by role: writers, computations, reports, ledgers, the lab, gates), and the
history the code declares. The registry declares no start date for these keys,
so "history" is the code's declared pull (the routine period, the backfill's
period, and the long-history symbols' documented starts), never the store's.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import yaml  # noqa: E402

from altdata import bars  # noqa: E402
from altdata.sources import overnight  # noqa: E402
from altdata.sources import yfinance_source as yf  # noqa: E402
from tools import pin_log  # noqa: E402

YAHOO_SOURCES = ("yfinance", "yfinance_fundamentals", "yahoo_cnh", "yahoo_set")

# The basket by family. A symbol named in no family below is reported under
# "unclassified", so a new symbol can never be silently left out of a count.
FAMILIES: "OrderedDict[str, set]" = OrderedDict([
    ("US equity index funds", {"SPY", "QQQ", "IWM", "DIA", "RSP"}),
    ("Sector funds", {"XLK", "XLF", "KRE", "XLE", "XLV", "XLI", "XLP", "XLY",
                      "XLU", "XLB", "XLRE", "XLC", "SMH"}),
    ("Style funds", {"IVW", "IVE", "IWF", "IWD"}),
    ("Rates and credit funds", {"TLT", "IEF", "SHY", "HYG", "LQD", "AGG", "TIP",
                                "MUB", "MBB"}),
    ("Commodity and real-asset funds", {"GLD", "SLV", "USO", "DBC", "DBA", "GUNR",
                                        "VNQ", "VNQI"}),
    ("International and EM funds", {"EFA", "EEM", "VEA", "HEFA", "VWO", "ACWX",
                                    "EMXC", "EWZ", "EWW", "EZA", "INDA", "EWY",
                                    "EWT", "THD", "FXI", "TUR", "EIDO", "MCHI"}),
    ("Thematic and replication funds", {"GRID", "PAVE", "AIQ", "SPXT", "QAI",
                                        "UUP"}),
    ("Single names", set(yf.EARNINGS_SYMBOLS) | set(yf.CAPEX_CHAIN_SYMBOLS)),
    ("Index levels (Cboe, S&P, ICE)", {"^GSPC", "^VIX", "^VIX3M", "^VIX9D",
                                       "^VIX6M", "^VVIX", "^SKEW", "^DSPX",
                                       "^COR1M", "^COR3M", "^MOVE", "DX-Y.NYB"}),
    ("Yield proxies", {"^TNX", "^TYX"}),
    ("Futures fronts (gold, oil, copper, products, the 10-year note)",
     {"GC=F", "CL=F", "HG=F", "RB=F", "HO=F", "ZN=F"}),
    ("FX rates", {"CNY=X", "TRY=X", "IDR=X", "JPY=X", "EURUSD=X", "EURCHF=X"}),
    ("Crypto in the basket", {"BTC-USD", "ETH-USD", "SOL-USD", "ZEC-USD"}),
])

# The shared lists a family is read through, so a reader that iterates a list
# rather than naming a key is still counted (the scan is a literal token match).
LIST_TOKENS = {
    "Sector funds": ["SECTOR_KEYS"],
    "Single names": ["EARNINGS_SYMBOLS", "CAPEX_CHAIN_SYMBOLS"],
}

# The code's declared history (comments and constants), quoted, not measured.
HISTORY = {
    "routine": f"the routine pull's period is {yf.LOOKBACK_PERIOD!r} "
               "(yfinance_source.LOOKBACK_PERIOD)",
    "backfill": "tools/backfill_prices.py: five years for every symbol, "
                "availability RECONSTRUCTED; `--period max` for ^GSPC and ^VIX",
    "long": "^GSPC daily from 1927-12-30 and ^VIX from 1990-01-02 "
            "(yfinance_source's THE LONG HISTORY comment)",
    "chains": "none: the registry's yfinance entry says it 'serves NO history "
              "for option chains, so an uncaptured session is lost permanently'",
}

ROLES = OrderedDict([
    ("writers", ("altdata/sources/", "altdata/loggers/", "altdata/bars.py",
                 "altdata/note_fetch.py", "altdata/dealer_capture.py",
                 "altdata/fed_funds.py", "tools/backfill_prices.py")),
    ("ledgers", ("altdata/ledgers/", "tools/calibration/", "docs/ledgers/")),
    ("lab", ("alpha/", "alpha_proposer/")),
    ("reports", ("daily_cascade/", "monthly_macro/", "register/")),
    ("gates", ("tools/validate_", "tools/check_", "smoke_test.py")),
    ("computations", ("altdata/", "regime.py", "contradictions.py")),
    ("config", ("config/",)),
    ("other tools", ("tools/",)),
])


def role(rel: str) -> str:
    for r, prefixes in ROLES.items():
        if any(rel.startswith(p) or rel == p for p in prefixes):
            return r
    return "other"


def load_registry() -> dict:
    return yaml.safe_load((ROOT / "metrics_registry.yaml").read_text(encoding="utf-8"))


def yahoo_metric_keys(reg: dict) -> "OrderedDict[str, list]":
    """The registry's single entries whose source is Yahoo, by source."""
    out: "OrderedDict[str, list]" = OrderedDict((s, []) for s in YAHOO_SOURCES)
    for k, v in (reg.get("metrics") or {}).items():
        if isinstance(v, dict) and v.get("source") in YAHOO_SOURCES:
            out[v["source"]].append(k)
    return out


def yahoo_bulk_blocks(reg: dict) -> list:
    return [(k, v) for k, v in (reg.get("bulk_imports") or {}).items()
            if isinstance(v, dict) and v.get("source") in YAHOO_SOURCES]


def groups(reg: dict) -> "OrderedDict[str, dict]":
    g: "OrderedDict[str, dict]" = OrderedDict()
    placed = set()
    for fam, syms in FAMILIES.items():
        s = sorted(x for x in yf.SYMBOLS if x in syms)
        placed |= set(s)
        g[f"Price basket: {fam}"] = {
            "symbols": s, "keys": [f"yfinance.{yf.SYMBOLS[x]}" for x in s],
            "tokens": [yf.SYMBOLS[x] for x in s] + LIST_TOKENS.get(fam, []),
            "history": "routine; backfill"
            + ("; long" if {"^GSPC", "^VIX"} & set(s) else "")}
    rest = sorted(set(yf.SYMBOLS) - placed)
    if rest:
        g["Price basket: unclassified"] = {
            "symbols": rest, "keys": [f"yfinance.{yf.SYMBOLS[x]}" for x in rest],
            "tokens": [yf.SYMBOLS[x] for x in rest], "history": "routine; backfill"}
    g["Crypto basket (config/crypto_basket.yaml)"] = {
        "symbols": sorted(yf.CRYPTO_BASKET), "keys": [f"yfinance.{v}" for v in
                                                      yf.CRYPTO_BASKET.values()],
        "tokens": list(yf.CRYPTO_BASKET.values()) + ["CRYPTO_BASKET"], "history": "routine; backfill"}
    g["OHLC companions (_open/_high/_low)"] = {
        "symbols": sorted(yf.OHLC_KEYS),
        "keys": [f"yfinance.{v}{s}" for v in yf.OHLC_KEYS.values()
                 for s in yf.OHLC_SUFFIXES],
        "tokens": [f"{v}_open" for v in yf.OHLC_KEYS.values()] + ["OHLC_KEYS"],
        "history": "routine; backfill"}
    g["Volume (_volume)"] = {
        "symbols": sorted(yf.VOLUME_UNITS),
        "keys": [f"yfinance.{yf.SYMBOLS[s]}_volume" for s in yf.VOLUME_UNITS],
        "tokens": ["_volume", "VOLUME_UNITS", "VOLUME_SHARE_KEYS"],
        "history": "routine; backfill (`--volume-only`)"}
    g["Dividends and splits (_dividend/_split)"] = {
        "symbols": sorted(yf.SYMBOLS),
        "keys": [f"yfinance.{v}{s}" for v in yf.SYMBOLS.values()
                 for s in (yf.DIVIDEND_SUFFIX, yf.SPLIT_SUFFIX)],
        "tokens": ["_dividend", "_split", "market_actions"],
        "history": "routine; backfill"}
    nb = dict(bars.NOTE_BAR_PRICE_KEYS)
    g["The notes' 5-minute bars (note_bars_prices)"] = {
        "symbols": sorted(set(nb.values())), "keys": sorted(nb),
        "tokens": sorted(nb) + ["NOTE_BAR_PRICE_KEYS"],
        "history": "intraday; the session only"}
    bp = list(bars.BAR_PRICE_KEYS)
    bv = list(bars.BAR_VOLUME_SHARE_KEYS) + list(bars.BAR_VOLUME_CONTRACT_KEYS) \
        + list(bars.BAR_VOLUME_USD_KEYS)
    g["The tape set's bars (bars_prices and volume)"] = {
        "symbols": [], "keys": sorted(set(bp) | set(bv)),
        "tokens": sorted(set(bp) | set(bv)) + ["BAR_PRICE_KEYS"],
        "history": "intraday 5-minute and daily frames"}
    g["Overnight levels and changes (the 07:00 anchor)"] = {
        "symbols": sorted(overnight.SYMBOLS),
        "keys": list(overnight.PRICE_KEYS) + list(overnight.PERCENT_KEYS),
        "tokens": list(overnight.PRICE_KEYS)[:6] + ["overnight."],
        "history": "intraday; forward only"}
    g["The pin log's columns (tools/pin_log.py)"] = {
        "symbols": [], "keys": list(pin_log.PIN_COLUMNS),
        "tokens": ["pin_log", "PIN_COLUMNS"], "history": "forward only"}
    # A key whose registry source is not Yahoo but whose values are (the code's
    # own docstring says so): the members' closes come from yf.download().
    g["S&P 500 members' closes (registry source sp500_members; values from Yahoo)"] = {
        "symbols": [], "keys": ["sp500.member_close"],
        "tokens": ["sp500.member_close", "CLOSE_KEY"],
        "history": "routine"}
    m = yahoo_metric_keys(reg)
    for src, keys in m.items():
        if not keys:
            continue
        g[f"Registry entries, source {src}"] = {
            "symbols": [], "keys": keys,
            "tokens": keys, "history": "chains" if src == "yfinance" else "routine"}
    return g


def scan(gs: "OrderedDict[str, dict]") -> None:
    files = [p for p in ROOT.rglob("*") if p.is_file()
             and p.suffix in (".py", ".yaml", ".yml", ".sh")
             and not any(part in (".git", ".venv", "node_modules", "build",
                                  "__pycache__", "html") for part in p.parts)
             and p.name != "price_source_inventory.py"]
    texts = {}
    for p in files:
        try:
            texts[p.relative_to(ROOT).as_posix()] = p.read_text(encoding="utf-8",
                                                                errors="replace")
        except OSError:
            continue
    for name, g in gs.items():
        toks = [t for t in g["tokens"] if t]
        rx = re.compile("|".join(re.escape(t) for t in toks)) if toks else None
        hits: "OrderedDict[str, list]" = OrderedDict((r, []) for r in ROLES)
        hits["other"] = []
        if rx:
            for rel, t in texts.items():
                if rx.search(t):
                    hits[role(rel)].append(rel)
        g["readers"] = {r: sorted(v) for r, v in hits.items() if v}


DIRECT_CALLERS_RX = re.compile(r"import_yfinance\(\)")


def direct_callers() -> list:
    out = []
    for p in ROOT.rglob("*.py"):
        if any(part in (".git", ".venv", "build") for part in p.parts):
            continue
        rel = p.relative_to(ROOT).as_posix()
        if rel in ("altdata/__init__.py", "tools/price_source_inventory.py")                 or rel.startswith("tools/validate_"):
            continue
        try:
            if DIRECT_CALLERS_RX.search(p.read_text(encoding="utf-8", errors="replace")):
                out.append(rel)
        except OSError:
            pass
    return sorted(out)


STOPS = {
    "Price basket": "the closes stop: every return, percentile, lens and chart on that family",
    "Crypto basket": "the crypto basket's closes and the Digital Assets addendum's price rows",
    "OHLC": "ranges, ATR and the ES/levels reads that use daily highs and lows",
    "Volume": "the volume shares, Amihud's depth stand-in (item 71) and the volume profile's daily approximation",
    "Dividends": "total-return computations (no new actions recorded)",
    "The notes'": "the 09:50 and 21:30 notes' bars and first-hour readings",
    "The tape set's": "the ES block, the volume profile and the session tables",
    "Overnight": "the 07:00 anchor's overnight block and gap attribution",
    "S&P 500 members'": "the breadth histogram, the average-member gap, the top-10 share and the dispersion fallback",
    "The pin log": "the pin log's spot and settlement columns",
    "Registry entries, source yfinance": "the option chains (and every exposure.* reading the dealer engine computes from them), earnings dates and consensus, ZEC's price rows, fed funds futures",
    "Registry entries, source yfinance_fundamentals": "the hyperscaler cash-flow bridge's quarterly fundamentals",
    "Registry entries, source yahoo_cnh": "USD/CNH's hourly-derived daily close",
    "Registry entries, source yahoo_set": "the SET index close",
}


def stop_line(name: str) -> str:
    for k, v in sorted(STOPS.items(), key=lambda kv: -len(kv[0])):
        if name.startswith(k):
            return v
    return "the group's rows"


def build() -> dict:
    reg = load_registry()
    gs = groups(reg)
    scan(gs)
    blocks = yahoo_bulk_blocks(reg)
    return {"groups": gs, "bulk_blocks": [(k, v.get("expected_members")) for k, v in blocks],
            "direct_callers": direct_callers(), "history": HISTORY}


def markdown(r: dict) -> str:
    L = ["| Group | Keys | Symbols | Readers by role (files) | History (the code's) | Stops if Yahoo stopped today |",
         "|---|---|---|---|---|---|"]
    tot = 0
    for name, g in r["groups"].items():
        n = len(g["keys"])
        tot += n
        rd = "; ".join(f"{k} {len(v)}" for k, v in g["readers"].items())
        hist = "; ".join(HISTORY[h.strip()] if h.strip() in HISTORY else h
                         for h in g["history"].split(";"))
        L.append(f"| {name} | {n} | {len(g['symbols'])} | {rd} | {hist} | {stop_line(name)} |")
    L.append(f"| **All groups (keys can appear in two groups)** | **{tot}** | | | | |")
    L.append("")
    L.append("Registry bulk blocks whose source is Yahoo, with their declared "
             "member counts: " + ", ".join(f"`{k}` {n}" for k, n in r["bulk_blocks"]) + ".")
    L.append("")
    L.append("Files that call Yahoo directly (`import_yfinance()`), gates excluded: "
             + ", ".join(f"`{f}`" for f in r["direct_callers"]) + ".")
    L.append("")
    L.append("Readers, by group and role (file paths):")
    for name, g in r["groups"].items():
        L.append(f"\n**{name}**")
        for k, v in g["readers"].items():
            L.append(f"- {k} ({len(v)}): " + ", ".join(f"`{x}`" for x in v[:25])
                     + (" ..." if len(v) > 25 else ""))
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    r = build()
    sys.stdout.reconfigure(encoding="utf-8")
    if a.json:
        print(json.dumps({**r, "groups": {k: {x: v[x] for x in ("keys", "symbols",
                                                                 "readers", "history")}
                                          for k, v in r["groups"].items()}},
                         indent=1, default=str))
    else:
        print(markdown(r))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
