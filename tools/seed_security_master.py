#!/usr/bin/env python3
"""
Seed config/security_master.yaml ONCE from the maps the code already keeps
(AUD-3b item 2). Its output is committed and reviewed; from then on the YAML is
the source of truth and this tool refuses to overwrite it (--force exists for a
scratch path, never for the committed file once reviewed).

    python tools/seed_security_master.py --out config/security_master.yaml
    python tools/seed_security_master.py --out /tmp/x.yaml --force

WHAT IT READS, and nothing else -- no network, no store:

  altdata/sources/yfinance_source.py  SYMBOLS (yahoo -> store key), CRYPTO_BASKET,
                                       EARNINGS_SYMBOLS (the single names)
  config/crypto_basket.yaml            each coin's name and its coingecko id
  altdata/loggers/shielded.py          ZEC's coingecko id
  altdata/sources/overnight.py         SYMBOLS (yahoo -> overnight slug)
  altdata/sources/cnh.py               CNH=X
  altdata/config.py                    the option universes, the SPCX reuse fence
  altdata/sources/fundamentals.py      TICKERS
  altdata/sources/proshares.py,        the funds they log, by ticker
    ishares_trusts.py
  tools/probe_massive.py               SPX's option roots
  config/tracked_entities.yaml         the Brookfield complex: root, entity,
                                       valid_from; the BAM/BN note

A FACT NOT FOUND THERE IS NULL and named in the entry's `unverified` list.
Currency is filled only where the identifier itself encodes it (a -USD coin; an
FX pair whose store key names it, mkt_usdjpy -> JPY); a share's multiplier of 1
is the definition of a share. Exchanges (MICs) and most names are not in the
repo, so they are null tonight.

`restricted` is NOT written: altdata/security_master.py computes it at load.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import yaml  # noqa: E402

FACTS = ("name", "currency", "multiplier", "exchange")


def _literal(path: str, name: str):
    """A module-level literal, read by ast so no module is imported for it."""
    tree = ast.parse((REPO / path).read_text(encoding="utf-8"))
    for node in tree.body:
        tgt = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            tgt = node.targets[0]
        elif isinstance(node, ast.AnnAssign):
            tgt = node.target
        if isinstance(tgt, ast.Name) and tgt.id == name and node.value is not None:
            v = node.value
            if (isinstance(v, ast.Call) and isinstance(v.func, ast.Name)
                    and v.func.id in ("frozenset", "set", "tuple", "list")
                    and len(v.args) == 1):
                v = v.args[0]                      # frozenset({...}) -> {...}
            return ast.literal_eval(v)
    raise KeyError(f"{path}: no literal {name}")


def asset_class(sym: str, single: set[str]) -> str:
    if sym in ("^TNX", "^TYX"):
        return "rate"                    # Cboe's yield indices: a rate, not a level
    if sym.startswith("^") or sym == "DX-Y.NYB":
        return "index"
    if sym.endswith("=F"):
        return "future"
    if sym.endswith("=X"):
        return "fx"
    if sym.endswith("-USD"):
        return "crypto"
    return "equity" if sym in single else "etf"


def fx_currency(sym: str, store_key: str) -> tuple[str | None, str | None]:
    m = re.fullmatch(r"([A-Z]{6})=X", sym)
    if m:
        return m.group(1)[3:], f"the pair {m.group(1)} is quoted in its second currency"
    m = re.fullmatch(r"(?:yfinance\.)?mkt_usd([a-z]{3})|cnh\.usd([a-z]{3})", store_key)
    if m:
        ccy = (m.group(1) or m.group(2)).upper()
        return ccy, f"the store key {store_key} names USD/{ccy}, quoted in {ccy}"
    return None, None


class Seed:
    def __init__(self) -> None:
        self.rows: list[dict] = []
        self.by_yahoo: dict[str, dict] = {}
        self.by_ticker: dict[str, dict] = {}

    def add(self, **kw) -> dict:
        e = {"id": None, "name": None, "asset_class": None, "currency": None,
             "multiplier": None, "exchange": None, "identifiers": {}, "aliases": [],
             "active_from": None, "active_to": None}
        e.update(kw)
        e["sources"] = kw.get("sources", {})
        self.rows.append(e)
        y = e["identifiers"].get("yahoo")
        if y:
            self.by_yahoo[y] = e
        t = e["identifiers"].get("ticker")
        if t and not e.get("active_to"):
            self.by_ticker.setdefault(t, e)
        return e

    def finish(self) -> dict:
        for i, e in enumerate(self.rows, start=1):
            e["id"] = f"SM{i:05d}"
        for e in self.rows:
            u = e.pop("_underlying", None)
            if u is not None:
                e["underlying"] = u["id"]
            e["unverified"] = sorted(f for f in FACTS if e.get(f) is None) + \
                sorted(e.pop("_unverified_extra", []))
            if not e["sources"]:
                e.pop("sources")
        return {"version": 1, "schema": "security-master-v1",
                "next_id": len(self.rows) + 1, "instruments": self.rows}


def build() -> dict:
    s = Seed()
    symbols: dict = _literal("altdata/sources/yfinance_source.py", "SYMBOLS")
    single = set(_literal("altdata/sources/yfinance_source.py", "EARNINGS_SYMBOLS"))
    for sym, key in symbols.items():
        ac = asset_class(sym, single)
        e = s.add(asset_class=ac,
                  identifiers={"yahoo": sym, "store_key": f"yfinance.{key}"},
                  sources={"identifiers": "yfinance_source.SYMBOLS",
                           "asset_class": "the symbol's form; equity = EARNINGS_SYMBOLS"})
        if ac in ("equity", "etf"):
            e["multiplier"] = 1
            if "-" in sym:
                e["aliases"] = [sym.replace("-", ".")]   # the class-share dotted form
        if ac == "crypto":
            e["currency"] = "USD"
            e["multiplier"] = 1
            e["sources"]["currency"] = "the -USD suffix of its Yahoo id"
        if ac == "fx":
            ccy, why = fx_currency(sym, key)
            if ccy:
                e["currency"] = ccy
                e["sources"]["currency"] = why
    # the crypto basket (config/crypto_basket.yaml), stored as yfinance.crypto_<sym>
    basket = yaml.safe_load((REPO / "config/crypto_basket.yaml").read_text(encoding="utf-8"))
    for sym, c in (basket.get("names") or {}).items():
        ids = {"yahoo": c["yahoo"], "store_key": f"yfinance.crypto_{sym.lower()}"}
        if c.get("llama_coin"):
            ids["crypto_id"] = c["llama_coin"]
        s.add(name=c.get("name"), asset_class="crypto", currency="USD", multiplier=1,
              identifiers=ids, aliases=[sym],
              sources={"identifiers": "config/crypto_basket.yaml",
                       "currency": "the -USD suffix of its Yahoo id"})
    zec = s.by_yahoo.get("ZEC-USD")
    if zec is not None:
        zec["identifiers"]["crypto_id"] = _literal("altdata/loggers/shielded.py",
                                                   "ZEC_LLAMA_COIN")
    # the overnight pass's slugs (a second Yahoo -> key scheme)
    for sym, slug in _literal("altdata/sources/overnight.py", "SYMBOLS").items():
        e = s.by_yahoo.get(sym)
        if e is None:
            e = s.add(asset_class=asset_class(sym, single), identifiers={"yahoo": sym},
                      sources={"identifiers": "altdata/sources/overnight.py SYMBOLS"})
        e["identifiers"]["overnight_slug"] = slug
    cnh = _literal("altdata/sources/cnh.py", "SYMBOL")
    ccy, why = fx_currency(cnh, "cnh.usdcnh")
    s.add(asset_class="fx", currency=ccy, identifiers={"yahoo": cnh, "store_key": "cnh.usdcnh"},
          sources={"identifiers": "altdata/sources/cnh.py", "currency": why})
    # names the system logs or captures by ticker but does not price through SYMBOLS
    single_names = _literal("altdata/config.py", "SINGLE_NAMES")
    extra = [(t, "equity", "altdata/config.py SINGLE_NAMES") for t in single_names]
    extra += [(t, "equity", "altdata/sources/fundamentals.py TICKERS")
              for t in _literal("altdata/sources/fundamentals.py", "TICKERS")]
    extra += [(t.upper(), "etf", "altdata/sources/ishares_trusts.py TRUSTS")
              for t in _literal("altdata/sources/ishares_trusts.py", "TRUSTS")]
    extra += [(t, "etf", "altdata/config.py PAPER_BID_SYMBOLS")
              for t in _literal("altdata/config.py", "PAPER_BID_SYMBOLS")]
    pro = re.findall(r"\b([A-Z]{3,4}) \(-?\dx\)",
                     (REPO / "altdata/sources/proshares.py").read_text(encoding="utf-8"))
    extra += [(t, "etf", "altdata/sources/proshares.py FUNDS") for t in pro]
    for t, ac, src in extra:
        if t in s.by_yahoo or t in s.by_ticker:
            continue
        s.add(asset_class=ac, multiplier=1, identifiers={"ticker": t},
              sources={"identifiers": src})
    # SPX: the index Massive serves; not merged with ^GSPC without a stored source
    spx = s.add(asset_class="index", identifiers={"ticker": "SPX"}, aliases=["I:SPX"],
                sources={"identifiers": "altdata/config.py MASSIVE_SYMBOLS; "
                                        "tools/probe_massive.py SPX_ROOTS"})
    # SPCX: a reused ticker, fenced by hand in altdata/config.py
    fence = _literal("altdata/config.py", "UNDERLYING_VERIFIED_FROM")
    old_spcx = s.add(asset_class="etf", identifiers={"ticker": "SPCX"}, active_to="2026-06-11",
                     sources={"identifiers": "altdata/config.py UNDERLYING_VERIFIED_FROM's note",
                              "active_to": "the day before the current issuer listed "
                                            "(2026-06-12); its own delisting date is not stored"},
                     _unverified_extra=["active_to", "asset_class"])
    new_spcx = s.add(name="Space Exploration Technologies Corp Class A", asset_class="equity",
                     multiplier=1, identifiers={"ticker": "SPCX"}, active_from="2026-06-12",
                     sources={"identifiers": "altdata/config.py UNDERLYING_VERIFIED_FROM's note",
                              "active_from": "listed 2026-06-12, per the note"})
    # option roots: every underlying the chain passes capture
    roots = list(dict.fromkeys(_literal("altdata/config.py", "INDEX_ETF_SYMBOLS")
                               + single_names
                               + _literal("altdata/config.py", "PAPER_BID_SYMBOLS")))
    for r in roots:
        u = s.by_yahoo.get(r) or s.by_ticker.get(r)
        s.add(asset_class="option_root", identifiers={"occ_root": r}, _underlying=u,
              sources={"identifiers": "altdata/config.py chain_universe()"})
    for r in ("SPX", "SPXW"):
        s.add(asset_class="option_root", identifiers={"occ_root": r}, _underlying=spx,
              sources={"identifiers": "tools/probe_massive.py SPX_ROOTS"})
    s.add(asset_class="option_root", identifiers={"occ_root": "SPCX"}, _underlying=old_spcx,
          active_to="2026-06-15",
          sources={"active_to": "contracts before the fence date belong to the former issuer"},
          _unverified_extra=["active_to"])
    s.add(asset_class="option_root", identifiers={"occ_root": "SPCX"}, _underlying=new_spcx,
          active_from=fence["SPCX"],
          sources={"active_from": "altdata/config.py UNDERLYING_VERIFIED_FROM"})
    # the Brookfield complex, so the export carries the blocklist
    ents = yaml.safe_load((REPO / "config/tracked_entities.yaml").read_text(encoding="utf-8"))
    bf = ents["entities"]["brookfield"]
    for row in bf.get("tickers") or []:
        vf = row.get("valid_from")
        s.add(name=row["entity"], asset_class="equity", identifiers={"ticker": row["root"]},
              active_from=str(vf) if vf else None,
              sources={"identifiers": "config/tracked_entities.yaml",
                       "asset_class": "listed security of the complex (common, unit, "
                                      "preferred or note); not split further"},
              _unverified_extra=["asset_class"])
        if row["root"] == "BAM":
            s.add(name="Brookfield Asset Management Inc. (the issuer now called BN)",
                  asset_class="equity", identifiers={"ticker": "BAM"},
                  active_to="2022-12-08",
                  sources={"identifiers": "config/tracked_entities.yaml's BAM and BN notes"})
    for row in bf.get("name_only") or []:
        s.add(name=row["entity"], asset_class="etf", identifiers={"ticker": row["ticker"]},
              sources={"identifiers": "config/tracked_entities.yaml name_only",
                       "asset_class": "a listed fund"},
              _unverified_extra=["asset_class"])
    return s.finish()


HEADER = """\
# security_master.yaml -- the Security Master, v1 (AUD-3b). THE SOURCE OF TRUTH
# for instrument identity: reviewed by the operator, served by altdata/security_master.py.
#
# Seeded once by tools/seed_security_master.py from the code's own maps; edit it
# by hand from here, by review. Ids are SM + five digits, never reused: close an
# instrument with active_to, never delete it, and take new ids from next_id.
# An identifier names an instrument only inside its active window.
#
# A null fact is unverified, and listed in the entry's `unverified`: never type
# one from memory. `restricted` is NOT a field: it is computed at load from
# config/tracked_entities.yaml, and a `restricted:` line here is discarded and
# fails the gate (tools/validate_security_master.py).
"""


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=str(REPO / "config" / "security_master.yaml"))
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    out = Path(a.out)
    if out.exists() and not a.force:
        print(f"{out} exists: the master is seeded once, then edited by review")
        return 2
    doc = build()
    out.write_text(HEADER + yaml.safe_dump(doc, sort_keys=False, allow_unicode=True,
                                           width=100), encoding="utf-8")
    n = len(doc["instruments"])
    print(f"wrote {out}: {n} instruments, next_id {doc['next_id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
