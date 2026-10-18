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
  G. The contract: chester-meme's three files, byte for byte (SHA-256 over LF)
  H. The FIGI mapper: OpenFIGI's ticker form, the limits, unmapped never guessed
  I. The ticker history and the export, to the contract, from two fixture days
  J. The box draft: prediction contracts and IBKR conids printed, nothing written
  K. The 06:45 job: the FIGI mapping and the export after the loggers
  L. A missed morning (ruled 15 Oct 2026): a new listing first seen after a
     one-day or a three-day gap starts the day after the previous snapshot,
     from_known false; consecutive sessions and a weekend keep the snapshot
     date; the master's known date still wins; a ticker change keeps the
     snapshot date
  M. The call sites moved (audit-leftovers-2): the yfinance basket and the
     crypto basket resolve their store keys through the master; seed and master
     agree; a symbol the master lacks keeps its seed key and logs
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
    bn = m.resolve("BN", "ticker", TODAY)
    check(old["id"] == bn["id"] and old["id"] != new["id"]
          and new["name"] == "Brookfield Asset Management Ltd.",
          f"BAM on 2021-06-01 is {old['id']} ({old['name']}, the same security as BN "
          f"today); BAM today is {new['id']} ({new['name']})")
    merged = [e for e in m.instruments if e.get("merged_into")]
    check(merged and all(not m.candidates(v, sc, "2021-06-01") or
                         all(c["id"] != e["id"] for c in m.candidates(v, sc, "2021-06-01"))
                         for e in merged for sc, v in e["identifiers"].items()),
          f"a merged entry ({', '.join(e['id'] for e in merged)}) keeps its id and "
          f"resolves to nothing")
    try:
        m.resolve("BN", "ticker", "2021-06-01")
        bad("BN resolves before its 2022-12-09 window")
    except NotFound:
        ok("BN before 2022-12-09 resolves to nothing: the ticker was not Brookfield's")
    a, b = m.resolve("SPCX", "ticker", "2025-01-01"), m.resolve("SPCX", "ticker", TODAY)
    check(a["id"] != b["id"] and b["name"] == "Space Exploration Technologies Corp Class A"
          and a["name"] == "The SPAC and New Issue ETF"
          and m.resolve("SPCK", "ticker", TODAY)["id"] == a["id"],
          f"SPCX: {a['id']} ({a['name']}, SPCK from 2026-04-07) before; {b['id']} "
          f"({b['name']}) from 2026-06-12")
    w = [m.resolve(t, "ticker", d)["id"] for t, d in
         (("BAMR", "2022-06-01"), ("BNRE", "2023-06-01"), ("BNT", TODAY))]
    check(len(set(w)) == 1 and m.by_id(w[0])["restricted"]
          and "0001193125-22-304958" in m.by_id(w[0])["sources"]["ticker_history"]
          and m.is_restricted("BNRE") and m.is_restricted("BAMR"),
          f"BAMR (to 13 Dec 2022), BNRE (to 5 Sep 2024) and BNT are one entry ({w[0]}), "
          f"each change cited to the registrant's 6-K; all three restricted")
    from altdata import sm_export  # noqa: PLC0415
    check(sm_export.venue_of("F", sm_export.exchanges()) == "TXSE"
          and sm_export.exchanges()["codes"]["F"]["mic"] == "TXSE",
          "exchange code F is the Texas Stock Exchange: MIC TXSE, venue TXSE")
    try:
        m.resolve("SPCX", "ticker", "2026-05-01")
        bad("SPCX resolved between the ETF's change and the listing")
    except NotFound:
        ok("SPCX between 7 Apr and 12 Jun 2026 resolves to nothing: nobody held it")
    oa, ob = m.resolve("SPCX", "occ_root", "2026-06-15"), m.resolve("SPCX", "occ_root",
                                                                     "2026-06-16")
    check(oa["underlying"] == a["id"] and ob["underlying"] == b["id"],
          "SPCX's option root follows the hand fence: contracts before 2026-06-16 "
          "belong to the former issuer")

    def overlap(r):
        for e in r["instruments"]:
            for r in e.get("ticker_history") or []:
                if r["ticker"] == "SPCX":
                    r["to"] = "2026-07-01"
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
    closed = [r for r in rules.all_roots() if not m.candidates(r, "ticker", TODAY)
              and any(e["restricted"] for e in m.instruments
                      if any(v == r for sc, v, f, t in m.windows(e) if sc == "ticker"))]
    maps += [("tracked_entities.yaml", r, "ticker") for r in rules.all_roots()
             if r not in closed]
    print(f"        restricted roots with a closed window today (still restricted): {closed}")
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
                 if not m.is_restricted(r)
                 or not any(e["restricted"] for e in m.instruments
                            if any(v == r for sc, v, f, t in m.windows(e) if sc == "ticker"))]
    check(not unflagged, f"every restricted root ({len(rules.all_roots())}) is flagged, "
                         f"a closed one (INF, BBU) on its own window"
          + (f" -- {unflagged}" if unflagged else ""))
    for t, cls in (("BNH", "note"), ("BPYPP", "preferred"), ("RA", "closed_end_fund"),
                   ("BN", "equity")):
        e = m.resolve(t, "ticker", TODAY)
        if e["asset_class"] != cls or "sec.gov" not in str(e.get("sources", {})
                                                             .get("asset_class")):
            bad(f"{t}: class {e['asset_class']} without its filing")
            break
    else:
        ok("the classes are set from filings, each with its URL (BNH note, BPYPP "
           "preferred, RA closed_end_fund, BN equity)")
    left = [e["identifiers"].get("ticker") for e in m.instruments
            if "asset_class" in (e.get("unverified") or [])]
    print(f"        still unverified in class: {left}")
    usd = [e for e in m.instruments if e.get("currency") == "USD"
           and "listing rule" in str((e.get("sources") or {}).get("currency"))]
    check(usd and all(e.get("exchange") for e in usd if e["asset_class"] != "option_root"),
          f"the listing rule: {len(usd)} entries in Nasdaq Trader's files carry USD and "
          f"their MIC")
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

    def no_robots(u: str) -> str:
        return "" if u == listings.ROBOTS_URL else fixture_get(u)
    r = listings.pull(TMP / "listings_norobots", get=no_robots, day="2026-10-13", min_rows=1)
    check(r["written"] == 9, "a site with no robots.txt (Nasdaq Trader's answers 404) has "
                             "no rules: the pull proceeds")
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


PINNED = {
    "security_master.schema.json": "5288446f9dd164b91fea6e28d3c2919de975d65fd938f5e8a4aa3484a5e78fb2",
    "decision_packet.schema.json": "e3e97e0e1fdb0439610e86ecea0d878a402a15bf1ed3b3b65420e32b0d569522",
    "README-interface.md": "bfe8ec7c1f86dd06735295afc139f91bafad380428d9993682189bdf1b87a421",
}
EXF = FIX / "export"


def group_g() -> None:
    head("G. THE CONTRACT: CHESTER-MEME'S FILES, BYTE FOR BYTE")
    for name, want in PINNED.items():
        b = (REPO / "docs" / "interface" / name).read_bytes()
        got = hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest()
        check(got == want and b"\r\n" not in b,
              f"docs/interface/{name}: sha256 {got[:16]}... as pinned, LF endings")
    attrs = (REPO / ".gitattributes").read_text(encoding="utf-8")
    check(re.search(r"^docs/interface/\*\s+text eol=lf", attrs, re.M) is not None,
          ".gitattributes keeps docs/interface/ LF")


class FakeFigi:
    """OpenFIGI's /v3/mapping, answered from saved responses; counts the calls."""

    def __init__(self, day: str) -> None:
        self.res = json.loads((EXF / f"openfigi_{day}.json").read_text(encoding="utf-8"))["results"]
        self.calls: list[list[dict]] = []
        self.refuse = 0

    def __call__(self, jobs: list[dict], key):
        self.calls.append(jobs)
        if self.refuse:
            self.refuse -= 1
            return 429, None, 7.0
        return 200, [self.res.get(j["idValue"], {"warning": "No identifier found."})
                     for j in jobs], 0.0


def stage_listings(d: Path, days: list[str]) -> None:
    d.mkdir(parents=True, exist_ok=True)
    for day in days:
        shutil.copyfile(EXF / f"{day}.csv", d / f"{day}.csv")
        listings.write_changes(d, day)


def group_h() -> tuple[Path, Path]:
    head("H. THE FIGI MAPPER (OpenFIGI, from saved responses; nothing fetches)")
    from altdata import figi  # noqa: PLC0415
    check([figi.to_openfigi(x) for x in ("BRK.B", "ABR$D", "AAC.W", "AAC.U", "AAPL")]
          == ["BRK/B", "ABR/PD", "AAC/WS", "AAC/U", "AAPL"],
          "ACT -> OpenFIGI's ticker form: BRK.B -> BRK/B, ABR$D -> ABR/PD, AAC.W -> AAC/WS")
    hit, why = figi.pick({"warning": "No identifier found."})
    amb, why2 = figi.pick({"data": [
        {"exchCode": "US", "compositeFIGI": "BBG000FXAA01"},
        {"exchCode": "US", "compositeFIGI": "BBG000FXAA02"}]})
    check(hit is None and "No identifier" in why and amb is None and "2 composite" in why2,
          "no data, or two composite FIGIs for one ticker, is unmapped with its reason -- "
          "never a guess")
    ld, fd = TMP / "fx_listings", TMP / "fx_figi"
    stage_listings(ld, ["2026-10-13"])
    sleeps: list[float] = []
    clock = [0.0]

    def tick() -> float:
        clock[0] += 0.1
        return clock[0]
    post = FakeFigi("2026-10-13")
    post.refuse = 1
    r = figi.run(full=True, d=fd, listings_dir=ld, post=post, key=None,
                 sleep=sleeps.append, clock=tick)
    c = figi.load_cache(fd)
    check(r["mapped"] == 10 and r["unmapped"] == 1 and "ZZZZ" in c["unmapped"]
          and "ZZZZ" not in c["symbols"],
          f"the first full mapping: {r['mapped']} mapped, ZZZZ listed unmapped "
          f"({c['unmapped']['ZZZZ']['why']})")
    check(all(len(j) <= figi.KEYLESS["jobs"] for j in post.calls)
          and any(abs(x - 7.0) < 1e-9 for x in sleeps)
          and any(x > 2.0 for x in sleeps),
          f"keyless: at most 10 jobs a request, {len(post.calls)} requests, paced "
          f"{figi.KEYLESS['window_s'] / figi.KEYLESS['per_window']:.1f}s apart; a 429 waits "
          f"the server's reset and retries")
    check(c["symbols"]["BRK.B"]["composite_figi"] == "BBG000FXBK01"
          and c["symbols"]["BN"]["share_class_figi"] == "BBG001FXBN01",
          "the cache keeps the composite and share-class FIGIs, the type and the name, by "
          "ACT symbol")
    keyed = FakeFigi("2026-10-13")
    figi.map_rows(listings.read_snapshot(ld / "2026-10-13.csv"), "2026-10-13",
                  TMP / "fx_figi_keyed", post=keyed, key="fixture-key",
                  sleep=lambda x: None, clock=tick)
    check(len(keyed.calls) == 1, "with a key: 100 jobs a request (one request here)")
    stage_listings(ld, ["2026-10-14"])
    post2 = FakeFigi("2026-10-14")
    r2 = figi.run(d=fd, listings_dir=ld, post=post2, key=None, sleep=lambda x: None,
                  clock=tick)
    asked = sorted(j["idValue"] for b in post2.calls for j in b)
    check(asked == ["MEMEA", "NEWT", "REUS"],
          f"the morning maps only what is new, renamed or not yet mapped: {asked} (ZZZZ "
          f"waits {figi.RETRY_DAYS} days)")
    a = figi.assignments(fd)
    check(any(x["symbol"] == "REUS" and x["figi"] == "BBG000FXRV02" and x["date"] ==
              "2026-10-14" for x in a)
          and not any(x["symbol"] == "MEMEA" and x["date"] == "2026-10-14" for x in a),
          "the assignment log records REUS's new holder on 14 Oct, and nothing for MEMEA's "
          "rename")
    src = (REPO / "altdata" / "figi.py").read_text(encoding="utf-8")
    check("secrets.get(KEY_NAME)" in src and "print(key" not in src
          and "keyed" in r2, "the key comes from altdata.secrets and is never printed "
                             "(the summary says only whether one was used)")
    return ld, fd


def hist_of(doc: dict, figi_: str) -> list[tuple]:
    sec = next(x for x in doc["securities"] if x["figi"] == figi_)
    return [(r["ticker"], r["effective_from"], r["effective_to"], r["from_known"])
            for r in sec["ticker_history"]]


def group_i(m: Master, ld: Path, fd: Path) -> None:
    head("I. THE TICKER HISTORY AND THE EXPORT, TO THE CONTRACT")
    from altdata import sm_export  # noqa: PLC0415
    doc, summ = sm_export.build(m, ld, fd, exported_at="2026-10-14T11:00:00Z")
    errs = sm_export.validate(doc)
    check(not errs, f"the fixture export validates against docs/interface/"
                    f"security_master.schema.json ({summ['securities']} securities)"
          + (f" -- {errs[:2]}" if errs else ""))
    check(hist_of(doc, "BBG000FXME01") == [("MEMEA", "1900-01-01", None, False)],
          "a rename (same FIGI, new name) changes nothing")
    check(hist_of(doc, "BBG000FXOT01") == [("OLDT", "1900-01-01", "2026-10-14", False),
                                           ("NEWT", "2026-10-14", None, True)],
          "a ticker change (same FIGI, new ticker) closes OLDT and opens NEWT on the "
          "snapshot date")
    check(hist_of(doc, "BBG000FXRU01") == [("REUS", "1900-01-01", "2026-10-14", False)]
          and hist_of(doc, "BBG000FXRV02") == [("REUS", "2026-10-14", None, True)],
          "a reuse (a new FIGI on REUS) closes the old holder with an exclusive "
          "effective_to of 2026-10-14 and opens the new one from it")
    check(hist_of(doc, "BBG000FXBN01") == [("BAM", "1900-01-01", "2022-12-09", False),
                                           ("BN", "2022-12-09", None, True)]
          and hist_of(doc, "BBG000FXBM01") == [("BAM", "2022-12-09", None, True)],
          "the master's known reuse carries its real date: BN held BAM to 2022-12-09 "
          "(exclusive); the new BAM from it")
    check(hist_of(doc, "BBG000FXSK01") == [("SPCX", "1900-01-01", "2026-04-07", False),
                                           ("SPCK", "2026-04-07", None, True)]
          and hist_of(doc, "BBG000FXSX01") == [("SPCX", "2026-06-12", None, True)],
          "and SPCX's: the ETF to 2026-04-07 (then SPCK), the new issuer from 2026-06-12")
    check(all(r[1] == "1900-01-01" for f in ("BBG000FXAA01", "BBG000FXSP01")
              for r in hist_of(doc, f)) and summ["unknown_starts"] >= 6,
          f"an unknown start is 1900-01-01 with from_known false "
          f"({summ['unknown_starts']} rows)")
    sec = {x["figi"]: x for x in doc["securities"]}
    check(sec["BBG000FXBN01"]["restricted"] and sec["BBG000FXBM01"]["restricted"]
          and not sec["BBG000FXAA01"]["restricted"],
          "a restricted name exports with restricted: true (BN, BAM), AAPL false")
    check(sec["BBG000FXSP01"]["type"] == "ETF" and sec["BBG000FXAA01"]["type"] == "CS"
          and sec["BBG000FXBN01"]["venue"] == "NYSE" and sec["BBG000FXAA01"]["venue"] == "Nasdaq"
          and sec["BBG000FXSP01"]["venue"] == "NYSE Arca" and sec["BBG000FXBK01"]["cik"] is None,
          "type from OpenFIGI's type and the ETF flag (SPY ETF, AAPL CS); venue from the "
          "exchange code (NYSE, Nasdaq, NYSE Arca); cik null in v1")
    check(any(r["ticker"] == "BRK.B" for r in sec["BBG000FXBK01"]["ticker_history"])
          and not any(x["name"] and "Unmappable" in x["name"] for x in doc["securities"]),
          "tickers in ACT form (BRK.B); a listing with no FIGI is not exported")
    check(doc["schema_version"] == "1.0" and doc["source"] == "chester-reports"
          and doc["exported_at"].endswith("Z") and set(doc) == {
              "schema_version", "exported_at", "source", "securities"},
          "schema_version 1.0, exported_at in UTC with a Z, source chester-reports")
    out = TMP / "sm_out" / "security_master.json"
    import os  # noqa: PLC0415
    os.environ[sm_export.VAR] = str(out)
    try:
        w = sm_export.write(doc)
    finally:
        os.environ.pop(sm_export.VAR, None)
    back = json.loads(out.read_text(encoding="utf-8"))
    check(w["written"] and w["path"] == str(out) and back == doc
          and not out.with_name(out.name + ".tmp").exists(),
          "$CHESTER_SM_EXPORT sets the path; written atomically and read back equal")
    bad_doc = json.loads(json.dumps(doc))
    bad_doc["securities"][0]["figi"] = "NOT-A-FIGI"
    out2 = TMP / "sm_bad" / "security_master.json"
    w2 = sm_export.write(bad_doc, out2)
    check(not w2["written"] and w2["errors"] and not out2.exists(),
          f"an invalid export is refused and never written ({w2['errors'][0][:60]})")
    saved = sys.modules.get("jsonschema")
    sys.modules["jsonschema"] = None
    try:
        e3 = sm_export.validate(doc)
    finally:
        if saved is not None:
            sys.modules["jsonschema"] = saved
        else:
            sys.modules.pop("jsonschema", None)
    check(e3 and "not installed" in e3[0], "with no validator installed, nothing is written")
    print("        sample (the reuse and BN):")
    for f in ("BBG000FXRU01", "BBG000FXRV02", "BBG000FXBN01"):
        print("          " + json.dumps(sec[f], ensure_ascii=False))
    readers = []
    for pth in list(REPO.glob("**/*.py")) + list(REPO.glob("scripts/*.sh")):
        if any(part in (".venv", ".git") for part in pth.parts):
            continue
        if pth.name in ("security_master.py", "sm_export.py", "validate_security_master.py"):
            continue
        if "security_master.json" in pth.read_text(encoding="utf-8", errors="replace"):
            readers.append(str(pth.relative_to(REPO)))
    check(not readers, "one-way: nothing else in this repository names the export"
          + (f" -- {readers}" if readers else ""))


def group_j(m: Master) -> None:
    head("J. THE BOX DRAFT (prediction contracts, IBKR conids): printed, never written")
    import contextlib  # noqa: PLC0415
    import io  # noqa: PLC0415
    from altdata import observations, sm_draft  # noqa: PLC0415
    sp = TMP / "draft_store.sqlite"
    st = observations.ObservationStore(str(sp))
    st.write_many([
        {"registry_key": "pm.market", "instrument": "kalshi:KXFEDDECISION-26DEC-H0",
         "observed_at": "2026-10-14T13:00:00+00:00", "available_at": "2026-10-14T13:00:00+00:00",
         "source": "kalshi", "value": json.dumps({"question": "Fed decision in Dec 2026?",
                                                  "outcome": "Hold",
                                                  "close_at": "2026-12-09T19:00:00Z"})},
        {"registry_key": "portfolio.position_con_id", "instrument": "SPY@ARCA.USD",
         "observed_at": "2026-10-14T21:00:00+00:00", "available_at": "2026-10-14T21:00:00+00:00",
         "source": "ibkr", "value": 1234567},
    ])
    st.close()
    before = hashlib.sha256(sp.read_bytes()).hexdigest()
    ro = sm_draft._ro(str(sp))
    try:
        entries = sm_draft.draft(ro, int(m.raw["next_id"]))
    finally:
        ro.conn.close()
    text = sm_draft.render(entries, int(m.raw["next_id"]))
    back = yaml.safe_load(text)["instruments"]
    pm = next(e for e in back if e["identifiers"].get("pm_id"))
    ib = next(e for e in back if e["identifiers"].get("ibkr_conid"))
    check(pm["asset_class"] == "prediction_contract" and pm["active_to"] == "2026-12-09"
          and ib["identifiers"]["ibkr_conid"] == "1234567" and ib["currency"] == "USD"
          and ib["aliases"] == ["SPY@ARCA.USD"],
          "it drafts a prediction contract (pm_id, closing 2026-12-09) and an IBKR conid "
          "(the key as alias, USD from its suffix)")
    check(back[0]["id"] == f"SM{int(m.raw['next_id']):05d}" and "restricted" not in text,
          f"ids proposed from next_id ({back[0]['id']}); no restricted line printed")
    check(hashlib.sha256(sp.read_bytes()).hexdigest() == before,
          "the store is byte-identical after the draft (mode=ro, query_only)")
    src = (REPO / "altdata" / "sm_draft.py").read_text(encoding="utf-8").split('"""', 2)[2]
    check("write_text" not in src and "open(" not in src and "write_many" not in src,
          "the draft writes nothing: it prints to the screen")
    raw = yaml.safe_load(smod.MASTER_PATH.read_text(encoding="utf-8"))
    check(not any(e.get("identifiers", {}).get(k) for e in raw["instruments"]
                  for k in ("pm_id", "ibkr_conid")),
          "until Ari's paste is committed, both schemes stay empty in the master")
    _ = contextlib, io


def group_k() -> None:
    head("K. THE 06:45 JOB")
    sh = (REPO / "scripts" / "fetch_overnight.sh").read_text(encoding="utf-8")
    i_log = sh.find('"$PY" -m altdata.feeds pull --only loggers')
    i_map = sh.find('"$PY" -m altdata.figi map')
    i_exp = sh.find('"$PY" -m altdata.security_master export')
    check(0 <= i_log < i_map < i_exp,
          "fetch_overnight.sh: the loggers (the listings snapshot), then the FIGI morning "
          "mapping, then the export")
    blk = sh[i_map:sh.find('log "security master: figi + export done"')]
    check(not re.search(r"\bexit\b", blk) and "WARN" in blk,
          "each step's failure is logged and skipped, never the job's")


def group_l() -> None:
    head("L. A MISSED MORNING: THE NEW LISTING'S START (ruled 15 Oct 2026)")
    from altdata import ticker_history as th  # noqa: PLC0415

    def snap(*syms):
        return [{"symbol": s} for s in syms]

    def rows_of(days, assigns, master=None):
        return th.build(days, th.Assignments(assigns), master)

    base = [{"symbol": "OLDA", "date": "2026-10-19", "figi": "BBG000FXOL01"}]
    # Mon 19 -> Tue 20, consecutive: NEWA's start is Tuesday, known.
    h = rows_of([("2026-10-19", snap("OLDA")), ("2026-10-20", snap("OLDA", "NEWA"))],
                base + [{"symbol": "NEWA", "date": "2026-10-20", "figi": "BBG000FXNA01"}])
    check(h["BBG000FXNA01"] == [{"ticker": "NEWA", "effective_from": "2026-10-20",
                                 "effective_to": None, "from_known": True}],
          "consecutive sessions (Mon 19 -> Tue 20): the snapshot date, from_known true")
    # One-day gap: Mon 19, Tuesday missed, Wed 21.
    h = rows_of([("2026-10-19", snap("OLDA")), ("2026-10-21", snap("OLDA", "NEWB"))],
                base + [{"symbol": "NEWB", "date": "2026-10-21", "figi": "BBG000FXNB01"}])
    check(h["BBG000FXNB01"] == [{"ticker": "NEWB", "effective_from": "2026-10-20",
                                 "effective_to": None, "from_known": False}],
          f"a one-day gap (Mon 19, Tuesday missed, Wed 21): from Tue 20, the day after "
          f"the previous snapshot, from_known false ({h['BBG000FXNB01']})")
    check(h["BBG000FXOL01"][0]["effective_to"] is None,
          "the running holding is untouched by the gap")
    # Three-day gap: Mon 19, Tue-Thu missed, Fri 23.
    h = rows_of([("2026-10-19", snap("OLDA")), ("2026-10-23", snap("OLDA", "NEWC"))],
                base + [{"symbol": "NEWC", "date": "2026-10-23", "figi": "BBG000FXNC01"}])
    check(h["BBG000FXNC01"] == [{"ticker": "NEWC", "effective_from": "2026-10-20",
                                 "effective_to": None, "from_known": False}],
          f"a three-day gap (Mon 19, Tue-Thu missed, Fri 23): from Tue 20, from_known "
          f"false ({h['BBG000FXNC01']})")
    # A weekend is no miss: Fri 23 -> Mon 26.
    h = rows_of([("2026-10-23", snap("OLDA")), ("2026-10-26", snap("OLDA", "NEWD"))],
                base + [{"symbol": "NEWD", "date": "2026-10-26", "figi": "BBG000FXND01"}])
    check(h["BBG000FXND01"][0]["effective_from"] == "2026-10-26"
          and h["BBG000FXND01"][0]["from_known"] is True,
          "a weekend is no missed morning (Fri 23 -> Mon 26): the snapshot date, known")
    # Three snapshots, the gap in the middle: the start counts from the snapshot
    # just before the listing appeared, not the first.
    h = rows_of([("2026-10-19", snap("OLDA")), ("2026-10-20", snap("OLDA")),
                 ("2026-10-23", snap("OLDA", "NEWE"))],
                base + [{"symbol": "NEWE", "date": "2026-10-23", "figi": "BBG000FXNE01"}])
    check(h["BBG000FXNE01"][0]["effective_from"] == "2026-10-21"
          and h["BBG000FXNE01"][0]["from_known"] is False,
          "the bound is the day after the snapshot just before (Tue 20 -> Wed 21), not "
          "the first snapshot")

    class FakeMaster:
        instruments = [{"id": "SM99901", "identifiers": {"ticker": "NEWF"},
                        "active_from": "2026-10-22", "active_to": None}]
    h = rows_of([("2026-10-19", snap("OLDA")), ("2026-10-23", snap("OLDA", "NEWF"))],
                base + [{"symbol": "NEWF", "date": "2026-10-23", "figi": "BBG000FXNF01"}],
                FakeMaster())
    check(h["BBG000FXNF01"][0]["effective_from"] == "2026-10-22"
          and h["BBG000FXNF01"][0]["from_known"] is True,
          "the master's known date inside the gap still wins (Thu 22, known)")
    # A ticker change across a gap keeps the snapshot date (the ruling names new
    # listings only).
    h = rows_of([("2026-10-19", snap("OLDA")), ("2026-10-21", snap("OLDB"))],
                base + [{"symbol": "OLDB", "date": "2026-10-21", "figi": "BBG000FXOL01"}])
    check([(r["ticker"], r["effective_from"], r["effective_to"], r["from_known"])
           for r in h["BBG000FXOL01"]]
          == [("OLDA", "1900-01-01", "2026-10-21", False),
              ("OLDB", "2026-10-21", None, True)],
          "a ticker change across the gap keeps the snapshot date")


def group_m(m: Master) -> None:
    """M. THE CALL SITES MOVED (audit-leftovers-2; aud-3b answer 9, the yfinance
    basket first): the pull resolves each Yahoo symbol's store key through the
    master, the module's maps are its seed, and the two agree."""
    print("\nM. The yfinance basket through the master")
    import inspect
    import logging
    from altdata.sources import yfinance_source as yf
    check(yf.resolve_basket(yf.SYMBOLS) == yf.SYMBOLS,
          f"all {len(yf.SYMBOLS)} SYMBOLS resolve through the master to their seed keys")
    check(yf.resolve_basket(yf.CRYPTO_BASKET) == yf.CRYPTO_BASKET,
          f"the crypto basket's {len(yf.CRYPTO_BASKET)} names resolve likewise")
    check("resolve_basket(symbols or SYMBOLS)" in inspect.getsource(yf.pull),
          "pull() takes its keys from the master's resolver, not the map")
    eq = {s for s in yf.SYMBOLS if m.resolve(s, "yahoo")["asset_class"] == "equity"}
    check(eq == set(yf.EARNINGS_SYMBOLS),
          f"EARNINGS_SYMBOLS is exactly the basket's equities by the master "
          f"({len(eq)}; differ {sorted(eq ^ set(yf.EARNINGS_SYMBOLS))})")
    cont = {s: m.resolve(s, "yahoo")["asset_class"] for s in yf.CONTINUOUS_SYMBOLS}
    # ST-13: a crypto.watch coin (PRL) trades round the clock like any coin.
    check(all(c in ("crypto", "crypto.watch", "fx") for c in cont.values()),
          "every CONTINUOUS symbol is crypto (a watch coin included) or fx by the "
          "master (the rule itself stays the module's: IDR=X and TRY=X are fx and "
          "not continuous)")
    i = yf.instrument("SPY")
    check(i["store_key"] == "yfinance.mkt_spy" and i["asset_class"] == "etf"
          and i["currency"] == "USD" and i["exchange"] == "ARCX" and i["id"] == "SM00001",
          f"instrument('SPY') reads id, class, currency and exchange from the master: {i}")
    logs: list[str] = []

    class H(logging.Handler):
        def emit(self, rec):
            logs.append(rec.getMessage())
    h = H()
    logging.getLogger(yf.__name__).addHandler(h)
    try:
        got = yf.resolve_basket({"NOTAREALSYM": "mkt_fixture"})
    finally:
        logging.getLogger(yf.__name__).removeHandler(h)
    check(got == {"NOTAREALSYM": "mkt_fixture"} and any("does not resolve" in x for x in logs),
          "a symbol the master lacks keeps its seed key and logs an error -- no capture "
          "is lost to a reference gap")


def main() -> int:
    m = Master()
    group_a(m)
    group_b(m)
    group_c(m)
    group_d(m)
    group_e(m)
    group_f()
    group_g()
    ld, fd = group_h()
    group_i(m, ld, fd)
    group_j(m)
    group_k()
    group_l()
    group_m(m)
    print(f"\n{PASSED} passed, {FAILED} failed")
    print(LINE)
    print("VALIDATION PASSED" if not FAILED else "VALIDATION FAILED")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
