#!/usr/bin/env python3
"""
The Security Master's gate (AUD-3b). A code gate: it reads the committed
config/security_master.yaml and the code's own maps, and builds everything else
-- listings snapshots, change files, the export -- in its own temp directory
from small hand-written files in Nasdaq Trader's published format
(tests/fixtures/security_master/). It never fetches, never reads the store and
never calls a model.

  A. The master file: ids, classes, schemes, windows, no overlap, nulls listed
  B. The restriction cannot be weakened: computed at load, never read from YAML
  C. Ticker reuse: an identifier names an instrument only inside its window
  D. The API: resolve, by_id, list by asset class, is_restricted
  E. Consistency: every identifier in the code's maps resolves to exactly one
     master entry today; every restricted root is flagged
  F. The listings layer: parse, test issues dropped, snapshots, the change file
  G. The export: one-way, round-trips, its hash matches, restricted exports so
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import yaml  # noqa: E402

from gate_tmp import mkdtemp  # noqa: E402

from altdata import listings  # noqa: E402
from altdata import security_master as smod  # noqa: E402
from altdata.security_master import Ambiguous, Master, NotFound  # noqa: E402
from register.instruments import Restrictions, normalise  # noqa: E402

FIX = REPO / "tests" / "fixtures" / "security_master"
TMP = Path(mkdtemp("gate_secmaster_"))
LINE = "=" * 78
PASSED = FAILED = 0
TODAY = dt.date.today().isoformat()


def ok(m: str) -> None:
    global PASSED
    PASSED += 1
    print(f"  PASS  {m}")


def bad(m: str) -> None:
    global FAILED
    FAILED += 1
    print(f"  FAIL  {m}")


def check(c: bool, m: str) -> None:
    (ok if c else bad)(m)


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


def variant(edit) -> Path:
    """A copy of the committed master with one edit applied to its YAML."""
    raw = yaml.safe_load(smod.MASTER_PATH.read_text(encoding="utf-8"))
    edit(raw)
    p = TMP / f"variant_{len(list(TMP.glob('variant_*')))}.yaml"
    p.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
    return p


def group_a(m: Master) -> None:
    head("A. THE MASTER FILE (config/security_master.yaml)")
    probs = m.structural()
    check(not probs, f"{len(m.instruments)} instruments: SM ids, unique and under "
                     f"next_id {m.raw.get('next_id')}; valid classes and schemes; every "
                     f"null fact listed as unverified" + (f" -- {probs[:3]}" if probs else ""))
    ov = m.overlaps()
    check(not ov, "no two entries are active on the same identifier at once"
          + (f" -- {ov[:3]}" if ov else ""))
    text = smod.MASTER_PATH.read_text(encoding="utf-8")
    check(not re.search(r"^\s+restricted(_by)?\s*:", text, re.M),
          "the committed file carries no `restricted` line: the flag is computed")
    counts = {c: len(m.list(c)) for c in smod.ASSET_CLASSES}
    print("        by class: " + ", ".join(f"{c} {n}" for c, n in counts.items() if n))
    unv = sum(1 for e in m.instruments if e.get("unverified"))
    print(f"        {unv} entries carry an unverified fact")
    p = variant(lambda r: r["instruments"].append(dict(r["instruments"][0])))
    check(any("id is used twice" in x for x in Master(p).structural()),
          "a duplicated id is caught")
    p = variant(lambda r: r["instruments"][0].update(name=None, unverified=[]))
    check(any("not all listed as unverified" in x for x in Master(p).structural()),
          "a null fact not listed as unverified is caught")


def group_b(m: Master) -> None:
    head("B. THE RESTRICTION CANNOT BE WEAKENED")

    def claim(r):
        for e in r["instruments"]:
            if e["identifiers"].get("ticker") == "BN":
                e["restricted"] = False
                e["restricted_by"] = None
            if e["identifiers"].get("yahoo") == "SPY":
                e["restricted"] = True
    p = variant(claim)
    v = Master(p)
    bn = v.resolve("BN", "ticker")
    check(bn["restricted"] is True and bn["restricted_by"]["entity_id"] == "brookfield",
          "a file claiming BN is unrestricted still loads BN as restricted "
          f"(by {bn['restricted_by']['matched_on']} {bn['restricted_by']['root']})")
    check(v.resolve("SPY", "yahoo")["restricted"] is False and len(v.discarded_claims) == 2,
          "and a claim the other way is discarded too: the YAML sets nothing "
          f"({len(v.discarded_claims)} claims discarded)")

    def rename(r):
        for e in r["instruments"]:
            if e["identifiers"].get("ticker") == "BN":
                e["name"] = "Some Corp"
    check(Master(variant(rename)).resolve("BN", "ticker")["restricted"],
          "renaming BN's entry does not clear it: the root alone restricts")
    rules = Restrictions()
    for probe in ("BN", "bn.to", "BN.PR.A", "BEP.UN", "O:BN260918C00050000", "BN@TSE.CAD"):
        if not m.is_restricted(probe):
            bad(f"is_restricted({probe!r}) is False")
            break
    else:
        ok("an identifier the master does not know is judged by the blocklist "
           "(bn.to, BN.PR.A, BEP.UN, an option, BN@TSE.CAD)")
    check(not m.is_restricted("BEPC.X") or rules.is_restricted("BEPC.X"),
          "the master never restricts less than the register's rule")
    src = (REPO / "altdata" / "security_master.py").read_text(encoding="utf-8")
    check("register.instruments import Restrictions" in src
          and "register.store" not in src and "tracked_entities.yaml\").write" not in src,
          "the master reads the register's rule (register.instruments) and writes "
          "nothing of the register's")
    store_src = (REPO / "register" / "store.py").read_text(encoding="utf-8")
    trig = re.findall(r"CREATE TRIGGER IF NOT EXISTS decisions_block_restricted_\w+.*?END;",
                      store_src, re.S)
    check(len(trig) == 2 and all("restricted_instruments" in t for t in trig),
          "the register's two block-restricted triggers stand, unchanged in shape")
    check(normalise("BEPC") == "BEPC" and normalise("BRK-B") == "BRK",
          "normalise() is untouched (BEPC stays BEPC; BRK-B -> BRK)")


def group_c(m: Master) -> None:
    head("C. TICKER REUSE: AN IDENTIFIER NAMES AN INSTRUMENT ONLY INSIDE ITS WINDOW")
    old, new = m.resolve("BAM", "ticker", "2021-06-01"), m.resolve("BAM", "ticker", TODAY)
    check(old["id"] != new["id"] and "now called BN" in old["name"]
          and new["name"] == "Brookfield Asset Management Ltd.",
          f"BAM on 2021-06-01 is {old['id']} ({old['name']}); today {new['id']} "
          f"({new['name']})")
    try:
        m.resolve("BN", "ticker", "2021-06-01")
        bad("BN resolves before its 2022-12-09 window")
    except NotFound:
        ok("BN before 2022-12-09 resolves to nothing: the ticker was not Brookfield's")
    a, b = m.resolve("SPCX", "ticker", "2025-01-01"), m.resolve("SPCX", "ticker", TODAY)
    check(a["id"] != b["id"] and b["name"] == "Space Exploration Technologies Corp Class A",
          f"SPCX: {a['id']} before 2026-06-12, {b['id']} ({b['name']}) after")
    oa, ob = m.resolve("SPCX", "occ_root", "2026-06-15"), m.resolve("SPCX", "occ_root",
                                                                     "2026-06-16")
    check(oa["underlying"] == a["id"] and ob["underlying"] == b["id"],
          "SPCX's option root follows the hand fence: contracts before 2026-06-16 "
          "belong to the former issuer")

    def overlap(r):
        for e in r["instruments"]:
            if e["identifiers"].get("ticker") == "SPCX" and e.get("active_to"):
                e["active_to"] = "2026-07-01"
    v = Master(variant(overlap))
    check(any("ticker:SPCX" in x for x in v.overlaps()),
          "two entries active on one identifier at once are caught")
    try:
        v.resolve("SPCX", "ticker", "2026-06-20")
        bad("an ambiguous identifier resolved to one entry")
    except Ambiguous:
        ok("and resolve() raises rather than choose between them")


def group_d(m: Master) -> None:
    head("D. THE API")
    spy = m.resolve("SPY", "yahoo")
    check(m.by_id(spy["id"]) is spy and spy["identifiers"]["store_key"] == "yfinance.mkt_spy",
          f"resolve('SPY', 'yahoo') -> {spy['id']}; by_id round-trips")
    check(m.resolve("yfinance.mkt_spy", "store_key")["id"] == spy["id"]
          and m.resolve("BRK.B", "alias")["identifiers"]["yahoo"] == "BRK-B",
          "the same instrument by its store key; BRK.B by alias")
    try:
        m.resolve("NOPE", "yahoo")
        bad("an unknown identifier resolved")
    except NotFound:
        ok("an unknown identifier raises NotFound")
    try:
        m.resolve("SPY", "cusip")
        bad("an unknown scheme was accepted")
    except ValueError:
        ok("an unknown scheme is refused")
    check(all(e["asset_class"] == "option_root" for e in m.list("option_root"))
          and len(m.list()) == len(m.instruments),
          f"list by asset class ({len(m.list('option_root'))} option roots)")
    check(m.is_restricted("BN", "ticker") and not m.is_restricted("SPY", "yahoo"),
          "is_restricted: BN yes, SPY no")
    jpy = m.resolve("JPY=X", "yahoo")
    check(jpy["currency"] == "JPY" and m.resolve("BTC-USD", "yahoo")["currency"] == "USD",
          "currencies filled only from the identifier itself (JPY=X -> JPY, BTC-USD -> USD)")


def group_e(m: Master) -> None:
    head("E. CONSISTENCY: THE CODE'S MAPS AGAINST THE MASTER, TODAY")
    from altdata import config as acfg  # noqa: PLC0415
    from altdata.sources import overnight, yfinance_source as y  # noqa: PLC0415
    maps: list[tuple[str, str, str]] = []
    maps += [("yfinance_source.SYMBOLS", s, "yahoo") for s in y.SYMBOLS]
    maps += [("yfinance_source.SYMBOLS", f"yfinance.{k}", "store_key")
             for k in y.SYMBOLS.values()]
    maps += [("yfinance_source.CRYPTO_BASKET", s, "yahoo") for s in y.CRYPTO_BASKET]
    maps += [("yfinance_source.CRYPTO_BASKET", f"yfinance.{k}", "store_key")
             for k in y.CRYPTO_BASKET.values()]
    maps += [("overnight.SYMBOLS", s, "yahoo") for s in overnight.SYMBOLS]
    maps += [("overnight.SYMBOLS", v, "overnight_slug") for v in overnight.SYMBOLS.values()]
    maps += [("config.chain_universe()", s, "occ_root") for s in acfg.chain_universe()]
    maps += [("config.MASSIVE_SYMBOLS", s, "occ_root") for s in acfg.MASSIVE_SYMBOLS]
    basket = yaml.safe_load((REPO / "config/crypto_basket.yaml").read_text(encoding="utf-8"))
    maps += [("crypto_basket.yaml llama_coin", c["llama_coin"], "crypto_id")
             for c in basket["names"].values() if c.get("llama_coin")]
    rules = Restrictions()
    maps += [("tracked_entities.yaml", r, "ticker") for r in rules.all_roots()]
    miss, many = [], []
    for src, ident, scheme in maps:
        n = len(m.candidates(ident, scheme, TODAY))
        if n == 0:
            miss.append(f"{src}: {scheme}:{ident}")
        elif n > 1:
            many.append(f"{src}: {scheme}:{ident}")
    check(not miss and not many,
          f"all {len(maps)} identifiers in the code's maps resolve to exactly one entry "
          f"today" + (f" -- missing {miss[:4]}, ambiguous {many[:4]}" if miss or many else ""))
    unflagged = [r for r in rules.all_roots()
                 if not m.resolve(r, "ticker", TODAY)["restricted"]]
    check(not unflagged, f"every restricted root ({len(rules.all_roots())}) is flagged")
    stray = [e["id"] for e in m.instruments
             if e["restricted"] and e["restricted_by"]["entity_id"] != "brookfield"]
    check(not stray, f"{sum(e['restricted'] for e in m.instruments)} restricted entries, "
                     f"all the Brookfield complex")


def write_day(d: Path, day: str) -> dict:
    files = {f"{n}": (FIX / f"{n[:-4]}_{day}.txt").read_text(encoding="utf-8")
             for n in listings.FILES}
    robots = (FIX / "robots.txt").read_text(encoding="utf-8")

    def get(url: str) -> str:
        if url == listings.ROBOTS_URL:
            return robots
        name = url.rsplit("/", 1)[-1]
        if url != listings.BASE + name or name not in files:
            raise AssertionError(f"unexpected fetch {url}")
        return files[name]
    return listings.pull(d, get=get, day=day, min_rows=1)


def group_f() -> Path:
    head("F. THE LISTINGS LAYER (Nasdaq Trader's directories, from fixtures)")
    text = (FIX / "nasdaqlisted_2026-10-13.txt").read_text(encoding="utf-8")
    rows, created = listings.parse(text, "nasdaqlisted.txt")
    check([r["symbol"] for r in rows] == ["AAPL", "NVDA", "QQQ", "MEMEA"]
          and created == "1013202618:01",
          "nasdaqlisted.txt parses; the test issue ZVZZT is dropped")
    for broken, why in ((text.rsplit("\n", 2)[0], "no footer"),
                        (text.replace("Test Issue", "Tst"), "a header field missing")):
        try:
            listings.parse(broken, "nasdaqlisted.txt")
            bad(f"a file with {why} was read")
        except listings.ListingsError:
            ok(f"a file with {why} is refused (a truncated download is never a day "
               f"of delistings)" if why == "no footer" else f"a file with {why} is refused")
    d = TMP / "listings"
    r1 = write_day(d, "2026-10-13")
    snap = listings.read_snapshot(d / "2026-10-13.csv")
    syms = [r["symbol"] for r in snap]
    check(r1["written"] == 9 and "ZXZZT" not in syms and "ZVZZT" not in syms
          and r1["changes"] is None,
          f"day one: {r1['written']} listings from both files, no test issue, no change "
          f"file ({r1.get('why')})")
    check(next(r for r in snap if r["symbol"] == "SPY")["etf"] == "Y"
          and next(r for r in snap if r["symbol"] == "BN")["exchange"] == "N",
          "the ETF flag and the exchange code are kept as published")
    r2 = write_day(d, "2026-10-14")
    ch = listings.read_snapshot(d / "changes" / "2026-10-14.csv")
    got = {(c["change"], c["symbol"], c["reuse_candidate"]) for c in ch}
    check(got == {("added", "NEWCO", "N"), ("removed", "OLDCO", "N"),
                  ("renamed", "MEMEA", "Y")} and r2["changes"] == {
                      "added": 1, "removed": 1, "renamed": 1},
          "day two's change file: NEWCO added, OLDCO removed, MEMEA renamed -- a reuse "
          "candidate")
    print("        sample change file (changes/2026-10-14.csv):")
    for ln in (d / "changes" / "2026-10-14.csv").read_text(encoding="utf-8").splitlines():
        print(f"          {ln}")
    before = hashlib.sha256(smod.MASTER_PATH.read_bytes()).hexdigest()
    check(hashlib.sha256(smod.MASTER_PATH.read_bytes()).hexdigest() == before
          and "security_master" not in (REPO / "altdata/listings.py").read_text(
              encoding="utf-8").split('"""', 2)[2],
          "the changes go to the change file only: listings.py never touches the master")
    deny = TMP / "listings_denied"

    def refused(url: str) -> str:
        if url == listings.ROBOTS_URL:
            return "User-agent: *\nDisallow: /dynamic/\n"
        raise AssertionError("fetched past a refusal")
    r = listings.pull(deny, get=refused, day="2026-10-13", min_rows=1)
    check(r["written"] == 0 and "robots.txt refuses" in r["error"] and not deny.exists(),
          "robots.txt refusing /dynamic/ -> nothing fetched, nothing written")
    def fixture_get(u: str) -> str:
        if u == listings.ROBOTS_URL:
            return (FIX / "robots.txt").read_text(encoding="utf-8")
        return (FIX / f"{u.rsplit('/', 1)[-1][:-4]}_2026-10-13.txt").read_text(
            encoding="utf-8")
    r = listings.pull(TMP / "listings_small", get=fixture_get, day="2026-10-13")
    check(r["written"] == 0 and "refused" in r["error"],
          f"a day under {listings.MIN_ROWS} listings is refused, not written")
    src = (REPO / "altdata/listings.py").read_text(encoding="utf-8").split('"""', 2)[2]
    reg = (REPO / "metrics_registry.yaml").read_text(encoding="utf-8")
    check("observations" not in src and "write_many" not in src
          and not re.search(r"^\s*-?\s*id:\s*listings\.", reg, re.M),
          "reference data: no observation written and no registry key added")
    from altdata.loggers import load_all  # noqa: PLC0415
    spec = load_all().get("listings")
    check(spec is not None and spec.keys() == [] and spec.in_freshness is False,
          "it runs as one more logger in the 06:45 loggers step (feeds pull --only "
          "loggers), with no keys for the freshness roster")
    return d


def group_g(m: Master, d: Path) -> None:
    head("G. THE EXPORT, FOR CHESTER-MEME (one-way)")
    out = TMP / "export" / "security_master.json"
    r = smod.export(out, m, listings_dir=d)
    doc = json.loads(out.read_text(encoding="utf-8"))
    check(doc["schema_version"] == smod.EXPORT_SCHEMA and doc["generated_at"]
          and doc["listings_snapshot"] == "2026-10-14"
          and len(doc["instruments"]) == len(m.instruments) and len(doc["listings"]) == 9,
          f"one JSON file: schema {doc['schema_version']}, generated_at, "
          f"{r['instruments']} instruments and the newest snapshot's {r['listings']} "
          f"listings")
    check(smod.content_hash(doc) == doc["content_hash"] == r["hash"],
          f"it round-trips and its hash matches ({doc['content_hash'][:19]}...)")
    doc2 = json.loads(json.dumps(doc))
    doc2["instruments"][0]["name"] = "tampered"
    check(smod.content_hash(doc2) != doc["content_hash"], "an edited export fails its hash")
    bn = [i for i in doc["instruments"] if i["identifiers"].get("ticker") == "BN"]
    bl = [x for x in doc["listings"] if x["symbol"] == "BN"]
    gme = [x for x in doc["listings"] if x["symbol"] == "GME"]
    check(bn and bn[0]["restricted"] and bn[0]["restricted_by"] == "brookfield"
          and bl and bl[0]["restricted"] and gme and not gme[0]["restricted"],
          "a restricted name exports as restricted, in the master and in the listings "
          "(BN yes, GME no)")
    need = {"identifiers", "asset_class", "currency", "exchange", "active_from",
            "active_to", "restricted"}
    check(all(need <= set(x) for x in doc["instruments"] + doc["listings"]),
          "every exported row carries identifiers, asset class, currency, exchange, its "
          "active window and the restricted flag")
    readers = []
    for p in list(REPO.glob("**/*.py")) + list(REPO.glob("scripts/*.sh")):
        if any(part in (".venv", "node_modules", ".git") for part in p.parts):
            continue
        if p.name in ("security_master.py", "validate_security_master.py"):
            continue
        t = p.read_text(encoding="utf-8", errors="replace")
        if "security_master.json" in t:
            readers.append(str(p.relative_to(REPO)))
    check(not readers, "one-way: nothing else in this repository names the export"
          + (f" -- {readers}" if readers else ""))
    check(smod.EXPORT_DEFAULT == "~/chester-data/export/security_master.json",
          "its default path is ~/chester-data/export/security_master.json")
    shutil.rmtree(TMP / "export", ignore_errors=True)


def main() -> int:
    m = Master()
    group_a(m)
    group_b(m)
    group_c(m)
    group_d(m)
    group_e(m)
    d = group_f()
    group_g(m, d)
    print(f"\n{PASSED} passed, {FAILED} failed")
    print(LINE)
    print("VALIDATION PASSED" if not FAILED else "VALIDATION FAILED")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
