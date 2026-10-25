"""
The Quarterly's readers, tranche 2 (b70-quarterly-readers-2, 25 Oct 2026; D34).

    python tools/validate_quarterly_readers_2.py

FIXTURES ONLY: no network, no live store.

  A  the parsers, on fixtures (iShares, DefiLlama, EDGAR, Blockscout)
  B  the Blockscout field check: absent is PENDING and writes nothing; a field
     that appears is STALE, never guessed
  C  DefiLlama: the no-republish note on every key; the AERO convention
  D  iShares: level, not flow, on every key and Quarterly label
  E  EDGAR: the facts on a fixture filing; the Brookfield blocklist refuses OCSL;
     PENDING without the contact
  F  every declared gap present, with its reason and check date, and printing
     "not tracked" (or "pending D33") where it would have printed
  G  keys registered, barred from the market-state object, no regime import
  H  no person's name or address in the readers
  I  wired: the external roster, static KEYS, the catalogue
"""
from __future__ import annotations

import fnmatch
import json
import os
import re
import sys
import tempfile
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
_TMP = gate_mkdtemp(prefix="validate_qr2_")
os.environ["CHESTER_STATE_DIR"] = _TMP

import yaml  # noqa: E402

from altdata import derived, feeds, observations  # noqa: E402
from altdata.sources import _publication as pub  # noqa: E402
from altdata.sources import (blockscout_supply, edgar_bdc, ishares_holdings,  # noqa: E402
                             llama_breadth)
from altdata.sources import edgar  # noqa: E402

READERS = [ishares_holdings, llama_breadth, edgar_bdc, blockscout_supply]
PASS = FAIL = 0
LINE = "=" * 78


def ok(m):
    global PASS
    PASS += 1
    print(f"  PASS  {m}")


def bad(m):
    global FAIL
    FAIL += 1
    print(f"  FAIL  {m}")


def check(c, m):
    ok(m) if c else bad(m)


def head(t):
    print(f"{LINE}\n{t}\n{LINE}")


def temp_store():
    fd, path = tempfile.mkstemp(suffix=".sqlite", dir=_TMP)
    os.close(fd)
    os.unlink(path)
    return observations.ObservationStore(path)


REG = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
METRICS = REG["metrics"]
QTXT = (REPO / "config" / "quarterly_chapters.yaml").read_text(encoding="utf-8")


def key_fact(name, value, day):
    return (f'{{"formattedValue":"{value}","formattedAsOfDate":"{day}",'
            f'"name":"{name}"}}')


ISHARES_PAGE = ("<html><script>" + key_fact("totalNetAssetsFundLevel", "7,815,585,782.00", "Oct 23, 2026")
                + "," + key_fact("sharesOutstanding", "144,293,284.00", "Oct 23, 2026")
                + "</script></html>")
PROTOCOLS = [{"slug": "a", "category": "RWA", "tvl": 1.5e9},
             {"slug": "b", "category": "RWA", "tvl": 0.5e9},
             {"slug": "c", "category": "CEX", "tvl": 9e10},
             {"slug": "aerodrome-v1", "category": "Dexs", "tvl": 1e8,
              "parentProtocol": "parent#aero-protocol"},
             {"slug": "d", "category": "Lending", "tvl": None}]
CHAINS = [{"name": "Arbitrum", "tvl": 3.2e9}, {"name": "Ethereum", "tvl": 7e10},
          {"name": "Base", "tvl": 4.1e9}]
CONCEPT_FV = {"units": {"USD": [
    {"end": "2026-06-30", "val": 27000000000, "filed": "2026-07-29"},
    {"end": "2026-06-30", "val": 27100000000, "filed": "2026-08-15"},
    {"end": "2026-03-31", "val": 26500000000, "filed": "2026-04-30"},
    {"start": "2026-01-01", "end": "2026-03-31", "val": 1, "filed": "2026-04-30"}]}}
CONCEPT_NAV = {"units": {"USD/shares": [{"end": "2026-06-30", "val": 19.74, "filed": "2026-07-29"}]}}
STATS = {"average_block_time": 12000, "coin_price": "2363.39", "gas_prices": {},
         "total_blocks": "1", "tvl": None}


def group_a():
    head("A. THE PARSERS, ON FIXTURES")
    r = ishares_holdings.rows_from_page("etha", ISHARES_PAGE, "2026-10-25T12:00:00Z")
    got = {x["registry_key"]: (x["value"], x["observed_at"]) for x in r}
    check(got == {"ishares.etha.aum": (7815585782.0, "2026-10-23"),
                  "ishares.etha.shares": (144293284.0, "2026-10-23")},
          "iShares: net assets and shares outstanding at the facts' own as-of date")
    c = llama_breadth.category_rows(PROTOCOLS, "2026-10-25", "x")
    cg = {x["registry_key"]: x["value"] for x in c}
    check(cg.get("llama.tvl.category.rwa") == 2.0e9 and "llama.tvl.category.cex" not in cg
          and cg.get("llama.tvl.category.dexs") == 1e8,
          "DefiLlama: a category's TVL is its protocols' sum; CEX excluded; a null skipped")
    ch = {x["registry_key"]: x["value"] for x in llama_breadth.chain_rows(CHAINS, "2026-10-25", "x")}
    check(ch == {"llama.tvl.chain.arbitrum": 3.2e9, "llama.tvl.chain.base": 4.1e9},
          "DefiLlama: the configured layer-2 chains only")
    try:
        llama_breadth.category_rows([], "d", "x")
        bad("an empty /protocols response was accepted")
    except ValueError:
        ok("an empty /protocols response raises (STALE), never a zero")


def group_b():
    head("B. THE BLOCKSCOUT FIELD CHECK")
    st, why = blockscout_supply.field_check(STATS)
    check(st == pub.PENDING and "no burn or issuance field" in why,
          "the public stats without a supply field: PENDING, with the field list")
    st2, why2 = blockscout_supply.field_check(dict(STATS, burnt_fees_today="1.2"))
    check(st2 == pub.STALE and "burnt_fees_today" in why2 and "operator rules" in why2,
          "a supply field that appears is named, STALE, and never guessed at")
    saved = blockscout_supply._fetch
    db = temp_store()
    try:
        blockscout_supply._fetch = lambda url, **kw: (json.dumps(STATS).encode(), {})
        out = blockscout_supply.pull(db=db)
    finally:
        blockscout_supply._fetch = saved
    n = db.conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
    check(out["status"] == pub.PENDING and n == 0, "and the pull writes nothing")
    db.close()
    check(all((METRICS.get(k) or {}).get("status_extra") == "not_yet_sourced"
              for k in blockscout_supply.KEYS),
          "the three ETH supply keys are registered not_yet_sourced")


def group_c():
    head("C. DEFILLAMA: STORED, NEVER REPUBLISHED; THE AERO CONVENTION")
    keys = llama_breadth.KEYS
    check(all("never republished" in (METRICS[k].get("description") or "").lower() for k in keys),
          "every DefiLlama key's description says stored, never republished")
    check(llama_breadth.breaks(PROTOCOLS) == [],
          "AERO's children in their merge category: no break")
    moved = [dict(p, category="Launchpad") if p["slug"] == "aerodrome-v1" else p for p in PROTOCOLS]
    check(llama_breadth.breaks(moved) and "aerodrome-v1" in llama_breadth.breaks(moved)[0],
          "a merged child listed under another category is a named, labelled break")
    check("AERO" in Path(llama_breadth.__file__).read_text(encoding="utf-8")
          and "D29 (3)" in Path(llama_breadth.__file__).read_text(encoding="utf-8"),
          "the module cites the AERO ruling it follows")


def group_d():
    head("D. ISHARES: LEVEL, NOT FLOW")
    keys = ishares_holdings.KEYS
    check(all("level, not flow" in (METRICS[k].get("description") or "").lower() for k in keys),
          "every iShares key's description says level, not flow")
    rows = [l for l in QTXT.splitlines() if "ishares." in l and "key:" in l]
    check(rows and all("level, not flow" in l for l in rows),
          f"every Quarterly row that prints one says so too ({len(rows)} rows)")


def group_e():
    head("E. EDGAR: FACTS ON A FIXTURE FILING; THE BLOCKLIST; THE CONTACT")
    fv = edgar_bdc.rows_from_concept(CONCEPT_FV, "edgar.bdc.arcc.investments_fv", "ARCC",
                                     "USD", "x")
    check([(r["observed_at"], r["value"]) for r in fv]
          == [("2026-03-31", 26.5e9), ("2026-06-30", 27.1e9)],
          "instants only, the later filing of a period wins, oldest first")
    nav = edgar_bdc.rows_from_concept(CONCEPT_NAV, "edgar.bdc.arcc.nav_per_share", "ARCC",
                                      "USD/shares", "x")
    check(nav and nav[0]["value"] == 19.74, "NAV per share from the USD/shares unit")
    check(edgar_bdc.allowed(("ARCC", "OCSL", "MAIN")) == ["ARCC", "MAIN"],
          "OCSL, Oaktree's BDC, is refused by the Brookfield blocklist")
    check(not any(t in ("OCSL",) for t in edgar_bdc.NAMES), "and it is not in NAMES")
    saved = edgar.user_agent
    try:
        edgar.user_agent = lambda: None
        out = edgar_bdc.pull()
    finally:
        edgar.user_agent = saved
    check(out["status"] == pub.PENDING and edgar.CONTACT_VAR in out["reason"],
          "without the SEC contact the reader is PENDING and sends nothing")
    check(all((METRICS.get(f"edgar.bdc.{t.lower()}.nonaccrual_fv") or {}).get("status_extra")
              == "not_yet_sourced" for t in edgar_bdc.NAMES),
          "non-accruals are registered not_yet_sourced, a listed gap")


GAPS = {"pjm.capacity_auction": "does not confer any license",
        "lbnl.interconnection_queue": "403", "moea.export_orders": "403",
        "tsmc.monthly_revenue": "personal", "circle.usdc_reserves": "terms",
        "tether.usdt_reserves": "robots", "thai.current_account_usd": "no verified",
        "thai.construction_materials_index": "500",
        "yahoo_pending.gdx": "D33", "yahoo_pending.sil": "D33",
        "yahoo_pending.corn_front": "D33", "yahoo_pending.wheat_front": "D33",
        "yahoo_pending.soybeans_front": "D33"}
PRINTS = ["not tracked: PJM's terms confer no licence", "LBNL's queue data answered HTTP 403",
          "MOEA answered HTTP 403", "TSMC's terms allow personal viewing only",
          "Tether's robots", "pending D33: no new yfinance symbols (yahoo_pending.corn_front)",
          "pending D33: no new yfinance symbols, so GDX and SIL",
          "the Commerce ministry's site answered HTTP 500",
          "Blockscout's public stats carry no burn or issuance field"]


def group_f():
    head("F. EVERY DECLARED GAP, WITH ITS REASON AND CHECK DATE")
    missing = []
    for k, word in GAPS.items():
        e = METRICS.get(k) or {}
        d = e.get("description") or ""
        if e.get("status_extra") != "not_yet_sourced" or word not in d or "2026" not in d:
            missing.append(k)
    check(not missing, f"each gap is registered not_yet_sourced with its reason and date {missing or ''}")
    unprinted = [p for p in PRINTS if p not in QTXT]
    check(not unprinted, f"each prints its reason where it would have printed {unprinted or ''}")
    src = yaml.safe_load((REPO / "source_registry.yaml").read_text(encoding="utf-8"))["sources"]
    refused = [s for s in ("pjm", "lbnl", "moea_tw", "tsmc", "circle", "tether")
               if (src.get(s) or {}).get("status") != "refused" or not (src.get(s) or {}).get("terms_read")]
    check(not refused, f"each refused source is registered refused, with its read date {refused or ''}")


def group_g():
    head("G. REGISTERED, BARRED FROM THE OBJECT, NO REGIME IMPORT")
    globs = [g for e in REG["market_state_barred"] for g in (e.get("keys") or [])]
    keys = [k for m in READERS for k in m.KEYS] + list(GAPS)
    unreg = [k for k in keys if k not in METRICS]
    unbarred = [k for k in keys if not any(fnmatch.fnmatch(k, g) for g in globs)]
    check(not unreg, f"every key is registered {unreg or ''}")
    check(not unbarred, f"every key is barred from the market-state object {unbarred or ''}")
    names = "|".join(m.__name__.split(".")[-1] for m in READERS)
    hits = [p for p in ("regime.py", "contradictions.py")
            if re.search(rf"\b({names})\b", (REPO / p).read_text(encoding="utf-8"))]
    check(not hits, f"regime.py and contradictions.py import no reader {hits or ''}")


def group_h():
    head("H. NO PERSON'S NAME OR ADDRESS IN THE READERS")
    off = [m.__name__ for m in READERS
           if re.search(r"[\w.]+@[\w-]+\.\w+", Path(m.__file__).read_text(encoding="utf-8"))]
    check(not off, f"no address in a reader {off or ''}")


def group_i():
    head("I. WIRED: THE EXTERNAL ROSTER, STATIC KEYS, THE CATALOGUE")
    names = [m.__name__.split(".")[-1] for m in READERS]
    check(set(names) <= set(feeds.EXTERNAL_WRITERS), "the four readers run as external writers")
    check(all(list(feeds.static_keys(n)) == list(m.KEYS) for n, m in zip(names, READERS)),
          "each reader's KEYS read from source match the module's")
    cat = yaml.safe_load((REPO / "config" / "catalogue_commands.yaml").read_text(encoding="utf-8"))
    check(all(f"altdata.sources.{n}" in cat["commands"] for n in names),
          "each reader has its catalogue line")


def main() -> int:
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g, group_h,
              group_i):
        try:
            g()
        except Exception as exc:                              # noqa: BLE001
            bad(f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
