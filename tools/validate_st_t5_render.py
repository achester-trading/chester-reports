#!/usr/bin/env python3
"""
ST-14 AND ST-15: THE MONTHLY'S PRL PART AND THE EMERGING-MECHANISM SCAN
(signal-triage Tranche 5; st-t5-render, 18 Oct 2026).

    python tools/validate_st_t5_render.py

A code gate: fixture stores, a fixture feed and a mocked model behind the scan's
gate. It never reads the live store, fetches or calls a model.

  A  THE PART (2.7.6): the Security Master guard (coingecko_id pearl-2, name
     Pearl), the thesis with its trace as a label (never a recommendation), the
     S1-S8 table with "not tracked" and ESTIMATED where the inputs say so, the
     supply within 2% of the formula, available_at present, STALE never empty,
     the register's month; the part reads stored rows and computes nothing
  B  THE FIGURE: M13 only once the explorer has read, else no figure and one
     line; first set aside at the cap
  C  THE MONTHLY: the part present (rows stored) and absent (nothing stored, or
     the builder failing) and the Monthly unharmed; no words against the budget
  D  THE SCAN (2.7.7): the feeds under robots, filtered by the declared terms;
     DefiLlama's recently added; the hashrate trackers a listed gap; dedupe
     against the Security Master and the register; the exclusion classes; the
     materiality hits; THE GATE: no model call when nothing survives, one when
     something does, Appendix F verbatim from the order with the list
     substituted; drafts only; a dry run writes nothing and calls nothing
  E  THE REGISTER AND ITS CLI: promote and reject write only with the operator's
     flag; PROMOTED is not a command; a rejected candidate is never surfaced
     again; the rendered view
  F  NOTHING ELSE: no PRL or Pearl string in any daily module; no name of a
     person in the new modules; the Saturday step on the basket's run, no new
     timer; the registry and the catalogue
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import datetime as dt
import json
import re
import sys
import types
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gate_tmp import mkdtemp  # noqa: E402

from altdata import observations, prl  # noqa: E402

TMP = Path(mkdtemp("gate_st_t5_render_"))
LINE = "=" * 78
PASS = FAIL = 0
NOW = "2026-10-31T22:00:00+00:00"
THEN = "2026-09-30T23:59:59+00:00"


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


def db(rows: list[dict]) -> str:
    global _N
    _N += 1
    p = str(TMP / f"s{_N}.sqlite")
    with observations.ObservationStore(p) as st:
        st.write_many(rows)
    return p


def row(key, day, value, avail=None, source="fixture"):
    return {"registry_key": key, "instrument": None, "observed_at": str(day),
            "available_at": avail or f"{day}T21:30:00+00:00", "value": value,
            "source": source, "availability_kind": "ingest_instant"}


def stored(explorer: bool, day="2026-10-31", stale=False) -> list[dict]:
    """The rows altdata.prl writes, as the daily compute would leave them."""
    av = f"{day}T21:30:00+00:00"
    h = 270000
    R = []
    for d, hh in (("2026-09-30", 262000), (day, h)):
        a = f"{d}T21:30:00+00:00"
        sc = prl.supply_code(hh)
        R += [row("calc.prl_supply_code", d, sc, a, "calc"),
              row("calc.prl_overhang", d, 100 * 121.70e6 / sc, a, "calc"),
              row("calc.prl_reward", d, prl.reward(hh), a, "calc"),
              row("calc.prl_emission_to_volume", d, 0.45 if d == day else 0.30, a, "calc"),
              row("calc.prl_idle_gpu_flag", d, 0.0, a, "calc"),
              row("calc.prl_thesis_status", d, json.dumps(
                  {"status": "UNCHANGED", "trace": "UNCHANGED: no rule fired. Read: D4 "
                   "the last 4 weekly reads 0.45, 0.40, 0.35, 0.30."}), a, "calc"),
              row("yfinance.crypto_prl", d, 1.05 if d == day else 0.98, a, "yfinance")]
        if not explorer:
            R.append(row("calc.prl_height_estimated", d, float(hh), a, "calc"))
    if explorer:
        for d, hh, sup in (("2026-09-26", 261000, None), ("2026-10-03", 264000, None),
                           ("2026-10-10", 267000, None), ("2026-10-31", h, None)):
            a = f"{d}T21:30:00+00:00"
            R += [row("pearl.chain_height", d, float(hh), a, "pearl_explorer"),
                  row("pearl.chain_supply", d, prl.supply_code(hh) * 1.004, a,
                      "pearl_explorer"),
                  row("pearl.chain_difficulty", d, 31.0e6 + hh, a, "pearl_explorer")]
        R.append(row("calc.prl_supply_gap", day, prl.supply_code(h) * -0.004, av, "calc"))
    if stale:
        R = [dict(r, available_at=r["available_at"].replace(day, "2026-10-20"),
                  observed_at=r["observed_at"].replace(day, "2026-10-20")) for r in R]
    return R


def part(rows: list[dict], now: str = NOW, reg_db=None):
    from monthly_macro import prl_part
    p = db(rows)
    with observations.ObservationStore(p) as st:
        return prl_part.build(st, now, THEN, reg_db or p), p


# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. THE PART (2.7.6)")
    from monthly_macro import prl_part
    check(prl_part.guard_master() == [],
          "the Security Master guard holds: coingecko_id pearl-2, name Pearl, crypto.watch")
    from altdata import security_master as sm
    real = sm.Master.by_coingecko
    sm.Master.by_coingecko = lambda self, cid, on=None: {
        "name": "Pearl Research", "asset_class": "crypto", "watch": {"coingecko_id": "pearl"}}
    try:
        bad, _ = part(stored(False))
    finally:
        sm.Master.by_coingecko = real
    check(len(bad) == 1 and "fails its guard" in bad[0]["lines"][0]
          and "not 'pearl-2'" in bad[0]["lines"][0] and "not 'Pearl'" in bad[0]["lines"][0]
          and not bad[0].get("table"),
          "a wrong entry: the part prints its refusal and nothing else")
    subs, _ = part(stored(False))
    p0 = subs[0]
    lines = " ".join(p0["lines"])
    check(p0["title"] == prl_part.TITLE and lines.startswith(
              "Thesis status, an informational label by the rule of 2.7.5 with no "
              "decision rights: UNCHANGED")
          and "The rule's trace: UNCHANGED: no rule fired." in lines
          and not re.search(r"\b(buy|sell|accumulate|recommend)\b", lines, re.I),
          "the thesis prints with its trace, as a label, never a recommendation")
    rows = {r[0].split(" ")[0]: r for r in p0["table"]["rows"]}
    check(p0["table"]["columns"] == prl_part.SIGNPOST_COLUMNS and len(rows) == 8
          and rows["S3"][3] == "not tracked (source retired): calc.prl_venue_conc"
          and "ESTIMATED" in rows["S5"][3] and "gap ESTIMATED" in rows["S5"][3]
          and "the explorer has not read" in rows["S4"][3]
          and "NOT AVAILABLE (G-27)" in rows["S4"][3]
          and rows["S1"][3].startswith("not read: a narrative signpost"),
          "S1-S8: venues not tracked, the overhang and the gap ESTIMATED, S4 waiting on "
          "the explorer, the pool share NOT AVAILABLE, the narratives not read")
    check("emission-to-volume 0.45" in rows["S6"][3] and "$1.0500" in rows["S6"][3]
          and rows["S6"][4] == "$+0.0700" and rows["S5"][4].endswith(" pp"),
          f"S6 now and the prior month from the stored rows, with the change "
          f"({rows['S6'][3]}; {rows['S6'][4]})")
    check("Supply figure: not drawn -- the explorer has not read (G-26)" in lines,
          "no explorer read: no figure, and one line saying why")
    subs2, _ = part(stored(True))
    l2 = " ".join(subs2[0]["lines"])
    r2 = {r[0].split(" ")[0]: r for r in subs2[0]["table"]["rows"]}
    check("within 2% of the formula at its height (+0.40%)" in l2
          and "ESTIMATED" not in r2["S5"][3] and "difficulty" in r2["S4"][3]
          and "Supply figure: not drawn" not in l2,
          "the explorer read: its supply within 2% of the formula (+0.40%), nothing "
          "ESTIMATED, S4 from its difficulty")
    off = stored(True)
    off = [dict(r, value=prl.supply_code(270000) * 1.05)
           if r["registry_key"] == "pearl.chain_supply" and r["observed_at"] == "2026-10-31"
           else r for r in off]
    s3, _ = part(off)
    check(any(x.startswith("CHECK: the explorer's supply") and "+5.0%" in x
              and "outside 2%" in x for x in s3[0]["lines"]),
          "an explorer supply 5% off the formula prints a CHECK line")
    st_, _ = part(stored(False, stale=True))
    l3 = " ".join(st_[0]["lines"])
    r3 = {r[0].split(" ")[0]: r for r in st_[0]["table"]["rows"]}
    check("STALE: calc.prl_* last computed 2026-10-20" in l3
          and "STALE (as of 2026-10-20)" in r3["S5"][3] and r3["S5"][3] != "not stored",
          "STALE, never empty: the last good values print with their dates")
    empty, _ = part([])
    e0 = empty[0]
    check(e0["table"] and all(len(r) == 5 for r in e0["table"]["rows"])
          and "Thesis status: not stored yet" in e0["lines"][0],
          "nothing stored: the table still prints, each cell saying why")
    src = (REPO / "monthly_macro" / "prl_part.py").read_text(encoding="utf-8")
    check("derive(" not in src and "prl.rows(" not in src and "supply_code(" in src,
          "it reads and does not compute: no derive, only the 2% check against the formula")


# ---------------------------------------------------------------------------
def group_b() -> None:
    head("B. THE FIGURE (M13)")
    from monthly_macro import charts as mch, prl_part
    p_no, p_yes = db(stored(False)), db(stored(True))
    with observations.ObservationStore(p_no) as a, observations.ObservationStore(p_yes) as b:
        check(not prl_part.explorer_read(a, NOW) and prl_part.explorer_read(b, NOW),
              "the figure's condition: the explorer has stored a height and a supply")
    c = mch.m13(p_yes, NOW, "m13_fixture", str(TMP))
    check(not c.get("unavailable") and c.get("png") and c["title"].startswith(
              "Pearl: realized and designed supply, 4 explorer read(s)"),
          f"with the explorer read, M13 draws ({c.get('title')})")
    check(mch.ORDER[-1] == "M13" and mch.DROP_ORDER[0] == "M13"
          and mch.PLACE["M13"] == ("slow", prl_part.TITLE),
          "planned last, first set aside at the cap, placed under the part")
    src = (REPO / "monthly_macro" / "charts.py").read_text(encoding="utf-8")
    check("if prl_part.explorer_read(st11, now):" in src,
          "build() draws it only when the explorer has read")


# ---------------------------------------------------------------------------
def group_c() -> None:
    head("C. THE MONTHLY, WITH THE PART AND WITHOUT IT")
    from monthly_macro import prl_part, stack as mstack
    src = (REPO / "monthly_macro" / "stack.py").read_text(encoding="utf-8")
    i = src.index("from . import prl_part")
    block = src[src.rindex("try:", 0, i):src.index("except Exception", i)]
    check("prl_part.build(st, now, window(p)[2], db_path)" in block
          and "the mechanism watch part is unavailable" in src[i:i + 1200],
          "the slow layers insert the part in its own try: a failure costs only the part")
    present, _ = part(stored(True))
    absent, _ = part([])
    words = mstack.stack_mod.section_words({"id": "slow", "claim": "x", "paragraphs": [],
                                            "subsections": present})
    base = mstack.stack_mod.section_words({"id": "slow", "claim": "x", "paragraphs": [],
                                           "subsections": []})
    check(words == base and all(s.get("paragraph_wanted") is False and not s.get("charts")
                                for s in present + absent),
          "no word against the Monthly's 10,000: tables and code-written lines, no "
          "paragraph; its one chart is M13, only once the explorer has read")
    check(len(present) == 3 and len(absent) == 3
          and [s["title"] for s in present] == [prl_part.TITLE, prl_part.TITLE_REGISTER,
                                                prl_part.TITLE_ENTRIES],
          "present or empty, the part keeps its three sub-sections in 2.7.6's order")
    check(prl_part.AFTER_TITLES[0] == "Themes: digital",
          "it prints inside the digital-assets material, after the crypto data layer")


# ---------------------------------------------------------------------------
def rss(items: list[tuple[str, str, str]]) -> bytes:
    body = "".join(f"<item><title>{t}</title><link>{u}</link><pubDate>{d}</pubDate>"
                   f"<description>BODY NEVER STORED</description></item>"
                   for t, u, d in items)
    return f'<?xml version="1.0"?><rss version="2.0"><channel>{body}</channel></rss>'.encode()


FEEDS = {
    "https://www.coindesk.com/arc/outboundfeeds/rss/": rss([
        ("Proof of useful work chain Lumen lists on Kraken after mainnet",
         "https://www.coindesk.com/a/lumen", "Wed, 28 Oct 2026 10:00:00 GMT"),
        ("Pearl's proof of useful work draws GPU miners",
         "https://www.coindesk.com/a/pearl", "Wed, 28 Oct 2026 11:00:00 GMT"),
        ("A memecoin claims proof of useful work",
         "https://www.coindesk.com/a/meme", "Wed, 28 Oct 2026 12:00:00 GMT"),
        ("Bitcoin rallies on ETF flows", "https://www.coindesk.com/a/btc",
         "Wed, 28 Oct 2026 13:00:00 GMT"),
        ("Old proof of useful work story", "https://www.coindesk.com/a/old",
         "Mon, 01 Sep 2026 10:00:00 GMT")]),
    "https://eprint.iacr.org/rss/rss.xml": rss([
        ("A new proof-of-work algorithm from matrix sketches",
         "https://eprint.iacr.org/2026/1234", "Tue, 27 Oct 2026 09:00:00 GMT")]),
}


def fetch(u):
    return FEEDS.get(u, rss([]))


def robots(u):
    return "User-agent: *\nDisallow: /feeds/\n" if "tomshardware" in u else ""


PROTOCOLS = [
    {"name": "Lattice Compute", "slug": "lattice", "category": "Decentralized AI",
     "listedAt": dt.datetime(2026, 10, 25, tzinfo=dt.timezone.utc).timestamp(),
     "gecko_id": "lattice-compute", "mcap": 180e6, "url": "https://lattice.example",
     "description": "Verifiable compute L1"},
    {"name": "Some DEX", "slug": "dex", "category": "Dexs",
     "listedAt": dt.datetime(2026, 10, 25, tzinfo=dt.timezone.utc).timestamp()},
    {"name": "Old Chain", "slug": "oldc", "category": "Chain",
     "listedAt": dt.datetime(2026, 8, 1, tzinfo=dt.timezone.utc).timestamp()}]


class Model:
    def __init__(self, reply):
        self.calls, self.reply = [], reply
        self.messages = types.SimpleNamespace(create=self.create)

    def create(self, **kw):
        self.calls.append(kw)
        return types.SimpleNamespace(
            model="fixture", usage=types.SimpleNamespace(input_tokens=1, output_tokens=1),
            content=[types.SimpleNamespace(type="text", text=self.reply)])


REPLY = json.dumps([
    {"qualifies": True, "name": "Lumen", "canonical_id": None,
     "mechanism_class": "PoUW / AI-compute", "whats_new": "useful-work proofs over matmul",
     "team_or_paper": "https://example.invalid/paper", "stage": "mainnet",
     "materiality_evidence": "a Kraken listing", "key_risk": "proof gaming",
     "why_it_could_matter": "a second PoUW chain", "sources": ["https://www.coindesk.com/a/lumen"]},
    {"qualifies": False, "name": "Lattice Compute", "fail_reason": "(i) no team identified"}])


def group_d() -> None:
    head("D. THE EMERGING-MECHANISM SCAN (2.7.7)")
    from altdata import mechanism_scan as ms, mechanism_watch as mw
    from altdata.sources import news
    items, rep = news.mechanism_items(NOW, fetch=fetch, robots=robots)
    titles = [i["title"] for i in items]
    check(set(titles) == {"Proof of useful work chain Lumen lists on Kraken after mainnet",
                          "Pearl's proof of useful work draws GPU miners",
                          "A memecoin claims proof of useful work",
                          "A new proof-of-work algorithm from matrix sketches"}
          and all(set(i) == {"feed", "query", "title", "url", "published_at"} for i in items),
          "the feeds, filtered by the declared terms in the 14-day window: title, link "
          "and date only, never the body")
    check(rep["feeds"]["tomshardware"]["state"] == "skipped"
          and "robots.txt refuses" in rep["feeds"]["tomshardware"]["reason"],
          "a feed whose robots.txt refuses its path is skipped, with the rule")
    added, arep = ms.recently_added(NOW, lambda u: PROTOCOLS)
    check([a["name"] for a in added] == ["Lattice Compute"]
          and added[0]["canonical_id"] == "coingecko:lattice-compute",
          "DefiLlama's recently added: the window and the declared categories only")
    known = ms.known_names()
    check({"pearl", "pearl-2"} <= known,
          "dedupe knows the Security Master's names and CoinGecko ids")
    pf = {t: ms.prefilter({"text": t, "url": u}, known)
          for t, u in [(i["title"], i["url"]) for i in items]}
    check(pf["Pearl's proof of useful work draws GPU miners"]["why"].startswith(
              "already covered (pearl")
          and pf["A memecoin claims proof of useful work"]["why"].startswith(
              "an excluded class (memecoin")
          and pf["Proof of useful work chain Lumen lists on Kraken after mainnet"]["keep"]
          and "tier-1 exchange: Kraken" in pf[
              "Proof of useful work chain Lumen lists on Kraken after mainnet"]["hits"]
          and not pf["A new proof-of-work algorithm from matrix sketches"]["keep"],
          "the pre-filter: Pearl dropped as covered, the memecoin as excluded, Lumen "
          "kept on its Kraken hit, the paper with no (iii) hit dropped")
    check(ms.prefilter(added[0], known)["hits"] == ["market cap above $50M"],
          "the recently-added leg's cap above $50M is a materiality hit")
    # THE GATE CLOSED: nothing survives, no model call
    closed = Model(REPLY)
    regp = str(TMP / "reg_closed.sqlite")
    r0 = ms.run(force=True, now=NOW, db_path=regp, client=closed,
                news_kw={"fetch": lambda u: rss([]), "robots": robots},
                fetch_json=lambda u: [])
    check(r0["gate"] == "closed" and not closed.calls and "written" not in r0,
          "nothing survives: the gate stays closed and the model is not called")
    # A DRY RUN: no call, no write
    dry = Model(REPLY)
    regd = str(TMP / "reg_dry.sqlite")
    r1 = ms.run(dry_run=True, force=True, now=NOW, db_path=regd, client=dry,
                news_kw={"fetch": fetch, "robots": robots},
                fetch_json=lambda u: PROTOCOLS)
    check(r1["gate"] == "open" and r1["survivors"] == 2 and not dry.calls
          and not Path(regd).exists() and r1["prompt_chars"] > 1000,
          "a dry run: two survive, the prompt is built, no call and nothing written")
    # THE GATE OPEN: one call, Appendix F verbatim, drafts only
    m = Model(REPLY)
    rego = str(TMP / "reg_open.sqlite")
    r2 = ms.run(force=True, now=NOW, db_path=rego, client=m,
                news_kw={"fetch": fetch, "robots": robots},
                fetch_json=lambda u: PROTOCOLS)
    sysp = m.calls[0]["system"] if m.calls else ""
    af = ms.appendix_f()
    order = (REPO / "docs" / "change-order-signal-triage-2026-09-25.md").read_text(
        encoding="utf-8")
    quoted = "\n".join(ln[2:] if ln.startswith("> ") else ln[1:]
                       for ln in order[order.index("## Appendix F"):].splitlines()
                       if ln.startswith(">"))
    check(len(m.calls) == 1 and af == quoted.strip()
          and sysp.startswith(af.split(ms.SUBSTITUTE)[0])
          and sysp.endswith(af.split(ms.SUBSTITUTE)[1])
          and "Lumen" in sysp and "Lattice Compute" in sysp and ms.SUBSTITUTE not in sysp,
          "one call, its prompt Appendix F verbatim from the order with the list "
          "substituted")
    with mw.Register(rego, readonly=True) as reg:
        rows = reg.all()
        ents = reg.month("2026-10-01", "2026-11-30")["entries"]
    check(len(rows) == 1 and rows[0]["name"] == "Lumen" and rows[0]["status"] == "CANDIDATE"
          and rows[0]["draft"] == 1 and rows[0]["grade"] == mw.GRADE_PROPOSED
          and len(r2["posted"]["posted"]) == 1
          and r2["written"]["failed"] == [{"name": "Lattice Compute",
                                           "fail_reason": "(i) no team identified"}],
          "drafts only: Lumen a CANDIDATE draft, its entry posted as a proposed story "
          "(ruling 6 of 19 Oct 2026); the failing one written nowhere, its criterion "
          "listed")
    check(len(ents) == 1 and ents[0]["draft"] == 1 and ents[0]["factor"] == "I"
          and len(ents[0]["text"].split()) <= 60 and ents[0]["cls"] == "mechanism-watch",
          "and one drafted narrative-register entry: factor I, at most 60 words")
    check("not read" in str(r2["hashrate_trackers"]),
          "the hashrate trackers are a listed gap, not a key")
    sub, _ = part(stored(False), reg_db=rego)
    cand = next(s for s in sub if s["title"].startswith("Mechanism Watch: candidates"))
    ent = next(s for s in sub if s["title"].startswith("Mechanism Watch: narrative"))
    check(cand["table"]["rows"][0][1] == "Lumen" and "(draft)" in cand["table"]["rows"][0][4]
          and "CANDIDATE" in " ".join(cand["lines"])
          and ent["lines"][0].endswith("(draft)") and "class=mechanism-watch" in ent["lines"][0],
          "the Monthly part prints the month's candidates, status changes and drafted "
          "entries from the register")


# ---------------------------------------------------------------------------
def group_e() -> None:
    head("E. THE REGISTER AND ITS CLI")
    from altdata import mechanism_watch as mw
    p = str(TMP / "reg_cli.sqlite")
    with mw.Register(p) as reg:
        mid = reg.add_candidate({"name": "Fixture Chain", "stage": "testnet"}, "fixture",
                                {"hits": ["x"]}, at="2026-10-30T12:00:00+00:00")
        plan = reg.set_status(mid, "WATCH", "operator", "two partners live")
        after = reg.get(mid)["status"]
        done = reg.set_status(mid, "WATCH", "operator", "two partners live", confirm=True)
        st2 = reg.get(mid)["status"]
        try:
            reg.set_status(mid, "PROMOTED", "operator", "x", confirm=True)
            promoted = True
        except ValueError:
            promoted = False
        rid = reg.add_candidate({"name": "Dud"}, "fixture", {}, at="2026-10-30T12:00:00+00:00")
        reg.set_status(rid, "REJECTED", "operator", "a fork", confirm=True)
        try:
            reg.add_candidate({"name": "dud"}, "fixture", {})
            again = True
        except ValueError:
            again = False
        changes = reg.month("2026-10-01", "2026-10-31")["changes"]
        rows = reg.all()
    check(not plan["written"] and after == "CANDIDATE" and "security_master" in plan,
          "promote without the operator's flag writes nothing and prints what it would do "
          "(and the Security Master entry to add)")
    check(done["written"] and st2 == "WATCH",
          "with --confirm it writes the status and its change")
    check(not promoted, "PROMOTED (core coverage, MW-7) is a ruling, not a command")
    check(not again, "a rejected candidate is never surfaced again (dedupe, any status)")
    check(sorted(c["to_status"] for c in changes)
          == sorted(["CANDIDATE", "WATCH", "CANDIDATE", "REJECTED"])
          and all(c["by"] and c["reason"] for c in changes),
          "every status change is logged with who and why")
    md = mw.render(rows, as_of="2026-10-31")
    check(md.startswith("# Mechanism-watch register") and "| MW-0001 | Fixture Chain |" in md
          and "Never edited by hand" in md, "the rendered view (make mechanism-register)")
    mk = (REPO / "Makefile").read_text(encoding="utf-8")
    check("mechanism-register:" in mk and "altdata.mechanism_watch render" in mk,
          "make mechanism-register renders it")
    try:
        with mw.Register(p) as reg:
            reg.add_entry(" ".join(["word"] * 61), "I", "s")
        long_ok = True
    except ValueError:
        long_ok = False
    check(not long_ok, "an entry over 60 words is refused")


# ---------------------------------------------------------------------------
NAME_RX = re.compile(r"\bAri\b|Chester|Weinstein|Komargodski|@", re.I)


def group_f() -> None:
    head("F. NOTHING ELSE")
    hits = [f.name for f in sorted((REPO / "daily_cascade").glob("*.py"))
            if re.search(r"\bPRL\b|\bPearl\b", f.read_text(encoding="utf-8"))]
    check(not hits, "no daily_cascade module names PRL or Pearl (the grep gate)"
          + (f": {hits}" if hits else ""))
    new = ["altdata/mechanism_scan.py", "altdata/mechanism_watch.py",
           "monthly_macro/prl_part.py"]
    named = [f for f in new if NAME_RX.search((REPO / f).read_text(encoding="utf-8")
                                              .replace("chester-reports", ""))]
    check(not named, "no name of a person (or an address) in the new modules: Appendix F "
                     "is read from the order at run time" + (f": {named}" if named else ""))
    wrap = (REPO / "scripts" / "run_crypto_basket.sh").read_text(encoding="utf-8")
    steps = [ln.split()[1] for ln in wrap.splitlines() if ln.startswith("step ")]
    check("mechanism_scan" in steps and steps.index("mechanism_scan") > steps.index("derive")
          and not list((REPO / "deploy" / "systemd").glob("*mechanism*")),
          "the scan is a step of the basket's run (Saturdays only), no new timer")
    from altdata import mechanism_scan as ms
    sk = ms.run(today="2026-10-30")
    check("skipped" in sk and "Saturdays" in sk["skipped"],
          "on a Friday it skips itself")
    import yaml
    cat = yaml.safe_load((REPO / "config" / "catalogue_commands.yaml").read_text(
        encoding="utf-8"))["commands"]
    check({"altdata.mechanism_scan", "altdata.mechanism_watch"} <= set(cat),
          "the catalogue names both commands")
    sq = yaml.safe_load((REPO / "config" / "story_queries.yaml").read_text(
        encoding="utf-8"))
    check(set(sq["mechanism_watch"]["queries"]) == {
        "proof_of_useful_work", "ai_compute_mainnet", "fair_launch_gpu_l1",
        "verifiable_compute", "new_proof_of_work", "post_quantum_mainnet"}
          and all(f.get("robots_line") for f in sq["mechanism_watch"]["feeds"])
          and sq.get("queries") and "mechanism_watch" not in sq["queries"],
          "the group sits beside `queries` (G-28), every feed with its robots line")


def main() -> int:
    for g in (group_a, group_b, group_c, group_d, group_e, group_f):
        g()
    print(f"\n{PASS} passed, {FAIL} failed")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
