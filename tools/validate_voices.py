"""
Validation gate for Phase B: the voices register and the daily voices scan.

    python tools/validate_voices.py

Against a TEMPORARY database (CHESTER_DB is set before anything is imported) and
FIXTURE pages served by a fake fetcher and a stub model -- a code gate never reads
the live store and never opens a socket. No voice or view here is a real one.

  A REFUSED      a voice with no source URL, no published date, no tier, a quote
                 of 15+ words or an undeclared subject is refused at write, and
                 the schema refuses an unsourced row underneath the code; a stored
                 voice cannot be edited or deleted; a 13F row needs its source.
  B STATUS       NEW / REITERATED / INFLECTED / SILENT computed from stored rows,
                 reproducible: the same rows in reverse insert order give the same
                 statuses; a row retrieved after the cutoff does not count; a voice
                 whose source was unreachable is UNREACHABLE, never SILENT.
  C SCAN         robots.txt obeyed; only NEW items reach the model, and a second
                 run makes no call; the day's cap holds; undated and out-of-window
                 items are not extracted; an undeclared subject and a non-verbatim
                 quote are dropped; the article body is stored nowhere; each item
                 tagged to a story is one headline under that story's query.
  D UNREACHABLE  a source that fails records `unreachable`, the pass goes on, and
                 the reports print "Unreachable on the latest scan: <name>" --
                 never that source's older rows as today's.
  E RENDERS      a fixture week renders section 8 (each story's items for and
                 against, the dissent, the voices table with weekly status, the
                 consensus line) and the daily Narratives line (most-cited story
                 and its dissent), every voice line carrying outlet, date and URL;
                 a view that breaks the style or policy-word rule prints withheld;
                 the Monthly's section 4 prints monthly status, the weeks and 13F.
  F ITEM 7       the Google News story fetch is retired with its reason and makes
                 no request; the overnight pass runs the scan; every source's
                 outlet is tiered; no source points at a host whose robots.txt
                 forbids it; the GTM seed is written once and computes NEW.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sqlite3
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TMP = tempfile.mkdtemp(prefix="validate_voices_")
DB = str(Path(TMP) / "chester.db")
os.environ["CHESTER_DB"] = DB

LINE = "=" * 78
PASS = FAIL = 0


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def base_row(**kw) -> dict:
    r = {"voice": "Fixture Strategist", "affiliation": "Fixture Bank",
         "kind": "sell_side", "view": "Expects fixture equities to rise into "
         "year-end on steady earnings.", "outlet": "Goldman Sachs",
         "source_url": "https://fixture.example/a", "published_at": "2026-09-28",
         "retrieved_at": "2026-09-29T11:00:00+00:00", "tier": 2,
         "directions": [{"subject": "us_equities", "direction": "bullish"}],
         "source_id": "fixture", "origin": "scan"}
    r.update(kw)
    return r


# ---------------------------------------------------------------------------
# Fixture pages and a fake fetcher
# ---------------------------------------------------------------------------
ROBOTS_OK = b"User-agent: *\nDisallow: /private/\n"
ROBOTS_NONE = b"User-agent: *\nDisallow: /\n"
BODY_SENTINEL = "ZEBRA-QUOKKA article body sentence that must never be stored"


def article(title: str, date: str, extra: str = "") -> bytes:
    return (f'<html><head><title>{title}</title>'
            f'<meta property="article:published_time" content="{date}T13:00:00Z">'
            f'</head><body><article><p>{BODY_SENTINEL}. Jane Fixture, chief '
            f'strategist at Fixture Bank, said "equities still have room to run '
            f'into year-end" and that the capex cycle is intact. {extra}</p>'
            f'{"<p>filler text. </p>" * 200}</article></body></html>').encode()


def rss(items: list[tuple]) -> bytes:
    xs = "".join(f"<item><title>{t}</title><link>{u}</link><pubDate>{d}</pubDate>"
                 f"<description>{s}</description></item>" for t, u, d, s in items)
    return f'<?xml version="1.0"?><rss version="2.0"><channel>{xs}</channel></rss>'.encode()


class FakeWeb:
    def __init__(self, pages: dict, fail: set = frozenset()):
        self.pages, self.fail, self.calls = pages, set(fail), []

    def __call__(self, url: str, headers: dict) -> bytes:
        import urllib.error  # noqa: PLC0415
        self.calls.append((url, headers.get("User-Agent")))
        host = url.split("/")[2]
        if host in self.fail:
            raise urllib.error.URLError("fixture: host down")
        if url in self.pages:
            return self.pages[url]
        raise urllib.error.HTTPError(url, 404, "nf", {}, None)


class StubClient:
    """Answers like the model: a JSON voices list keyed by the title."""

    def __init__(self, by_title: dict):
        self.by_title, self.calls = by_title, 0
        self.messages = self

    def create(self, **kw):
        self.calls += 1
        msg = kw["messages"][0]["content"]
        title = msg.split("\n", 1)[0].replace("TITLE: ", "")
        out = self.by_title.get(title, {"voices": []})

        class B:
            text = json.dumps(out)

        class M:
            content = [B()]
        return M()


def scan_cfg() -> dict:
    from altdata import voices as vmod
    cfg = json.loads(json.dumps(vmod.load_config(), default=str))
    cfg["politeness_seconds"] = 0
    cfg["lookback_days"] = 10
    cfg["sources"] = [
        {"id": "fx_feed", "name": "Fixture Feed", "outlet": "CNBC", "method": "rss",
         "url": "https://feed.example/rss.xml",
         "require_any": ["strategist", "says"]},
        {"id": "fx_desk", "name": "Fixture Desk", "outlet": "Goldman Sachs",
         "method": "listing", "url": "https://desk.example/insights",
         "link_pattern": "/insights/articles/[a-z0-9-]+",
         "default_voice": "Fixture Research", "default_kind": "sell_side"},
        {"id": "fx_down", "name": "Fixture Down", "outlet": "PIMCO",
         "method": "listing", "url": "https://down.example/insights",
         "link_pattern": "/x/[a-z]+"},
        {"id": "fx_blocked", "name": "Fixture Blocked", "outlet": "PIMCO",
         "method": "listing", "url": "https://blocked.example/insights",
         "link_pattern": "/x/[a-z]+"},
    ]
    return cfg


def main() -> int:
    from altdata import voices as vmod
    from altdata import narratives as nr
    from altdata import events as ev_mod
    from altdata.sources import voices_scan as vsn

    # The register's four stories, seeded as the box has them.
    with nr.NarrativeRegister() as reg:
        reg.seed(nr.load_config(), today="2026-09-26")
    stories = {r["narrative_id"]: r for r in nr.NarrativeRegister().all("active")}

    # --- A. REFUSED -----------------------------------------------------------
    print(f"\n{LINE}\nA. A VOICE WITHOUT A SOURCE IS REFUSED AT WRITE\n{LINE}")
    with vmod.VoicesStore() as vs:
        for label, row in (("no source URL", base_row(source_url="")),
                           ("a non-URL source", base_row(source_url="see desk note")),
                           ("no published date", base_row(published_at="")),
                           ("no tier (outlet unclassified)", base_row(tier=None)),
                           ("a 15-word quote", base_row(quote=" ".join(["word"] * 15))),
                           ("an undeclared subject", base_row(directions=[
                               {"subject": "tulips", "direction": "bullish"}])),
                           ("an undeclared kind", base_row(kind="pundit")),
                           ("a story not in the register", base_row(
                               stories=[{"story": "made_up", "side": "for"}]))):
            try:
                vs.write(row, stories=set(stories))
                check(False, f"{label} is refused")
            except vmod.VoiceError as exc:
                check(True, f"{label} is refused ({str(exc)[:70]})")
        try:
            vs.conn.execute(
                "INSERT INTO voices (voice, voice_key, affiliation, kind, view, "
                "source_id, outlet, source_url, published_at, retrieved_at, tier, "
                "origin, created_at) VALUES ('a','a@b','b','sell_side','v','x','o',"
                "'', '2026-09-28', '2026-09-28T00:00:00', 2, 'x', 'now')")
            check(False, "the schema refuses an unsourced row under the code")
        except sqlite3.IntegrityError:
            check(True, "the schema refuses an unsourced row under the code (CHECK)")
        vs.conn.rollback()
        w = vs.write(base_row(stories=[{"story": "ai_capex_durability",
                                        "side": "for"}]), stories=set(stories))
        check(w["inserted"] and w["evidence"] == 1,
              "a sourced voice is written, with its evidence row")
        check(not vs.write(base_row(), stories=set(stories))["inserted"],
              "the same voice and URL twice is one row")
        for sql, what in (("UPDATE voices SET view = 'x'", "edited"),
                          ("DELETE FROM voices", "deleted")):
            try:
                vs.conn.execute(sql)
                check(False, f"a stored voice cannot be {what}")
            except sqlite3.DatabaseError:
                check(True, f"a stored voice cannot be {what}")
            vs.conn.rollback()
        try:
            vs.write_13f({"accession": "0001", "affiliation": "Goldman Sachs",
                          "cik": "1", "form": "13F-HR", "period_of_report":
                          "2026-06-30", "filed": "2026-08-14", "source_url": "",
                          "retrieved_at": "2026-10-01"})
            check(False, "a 13F row without its source is refused")
        except vmod.VoiceError:
            check(True, "a 13F row without its source is refused")

    # --- B. STATUS ------------------------------------------------------------
    print(f"\n{LINE}\nB. STATUS IS COMPUTED, AND REPRODUCIBLE FROM STORED ROWS\n{LINE}")
    sdb1 = str(Path(TMP) / "status1.db")
    sdb2 = str(Path(TMP) / "status2.db")
    rows = [
        # A: bullish in the prior week, bullish again -> REITERATED
        base_row(voice="Alpha", source_url="https://f.example/a1",
                 published_at="2026-09-22", retrieved_at="2026-09-23T11:00:00+00:00"),
        base_row(voice="Alpha", source_url="https://f.example/a2",
                 published_at="2026-09-29", retrieved_at="2026-09-30T11:00:00+00:00"),
        # B: bullish a month ago, bearish now -> INFLECTED
        base_row(voice="Bravo", source_url="https://f.example/b1",
                 published_at="2026-09-01", retrieved_at="2026-09-02T11:00:00+00:00"),
        base_row(voice="Bravo", source_url="https://f.example/b2",
                 published_at="2026-09-30", retrieved_at="2026-10-01T11:00:00+00:00",
                 directions=[{"subject": "us_equities", "direction": "bearish"}]),
        # C: first entry -> NEW
        base_row(voice="Charlie", source_url="https://f.example/c1",
                 published_at="2026-10-01", retrieved_at="2026-10-02T11:00:00+00:00",
                 directions=[{"subject": "treasuries", "direction": "bullish"}]),
        # D: spoke in the prior week only -> SILENT
        base_row(voice="Delta", source_url="https://f.example/d1",
                 published_at="2026-09-24", retrieved_at="2026-09-25T11:00:00+00:00"),
        # E: prior week only, and its source was unreachable -> UNREACHABLE
        base_row(voice="Echo", source_url="https://f.example/e1", source_id="fx_down",
                 published_at="2026-09-24", retrieved_at="2026-09-25T11:00:00+00:00"),
        # F: published in the window but retrieved after the cutoff -> unseen
        base_row(voice="Foxtrot", source_url="https://f.example/f1",
                 published_at="2026-10-02", retrieved_at="2026-10-09T11:00:00+00:00"),
    ]
    for path, order in ((sdb1, rows), (sdb2, list(reversed(rows)))):
        with vmod.VoicesStore(path) as vs:
            for r in order:
                vs.write(r)
            vs.record_run("r1", "fx_down", "Fixture Down", "unreachable", "fixture")
            vs.conn.execute("UPDATE voice_scan_runs SET started_at = "
                            "'2026-10-03T10:50:00+00:00'")
            vs.conn.commit()
    cutoff = "2026-10-04T09:00:00+00:00"
    t1 = vmod.status_table("2026-10-05", "weekly", as_of=cutoff, db_path=sdb1)
    t2 = vmod.status_table("2026-10-05", "weekly", as_of=cutoff, db_path=sdb2)
    got = {v["row"]["voice"]: v["status"] for v in t1["voices"]}
    check(got == {"Alpha": "REITERATED", "Bravo": "INFLECTED", "Charlie": "NEW",
                  "Delta": "SILENT", "Echo": "UNREACHABLE"},
          f"the five statuses from stored directions: {got}")
    sig = lambda t: [(v["voice_key"], v["status"], json.dumps(v["subjects"],
                                                              sort_keys=True))
                     for v in t["voices"]]
    check(sig(t1) == sig(t2), "the same rows inserted in reverse order give the "
                              "same statuses -- reproducible from stored rows")
    check("Foxtrot" not in got, "a row retrieved after the cutoff does not count")
    inf = next(v for v in t1["voices"] if v["row"]["voice"] == "Bravo")
    check(inf["subjects"][0].get("was") == "bullish"
          and inf["subjects"][0].get("now") == "bearish",
          "an inflection records what the direction was and is")
    tm = vmod.status_table("2026-10-01", "monthly", as_of=cutoff, db_path=sdb1)
    check(tm["start"] == "2026-09-01" and tm["prior_start"] == "2026-08-01",
          "the Monthly's window is the calendar month against the month before")

    # --- C. SCAN --------------------------------------------------------------
    print(f"\n{LINE}\nC. THE SCAN: NEW ITEMS ONLY, ONE CALL EACH, NO BODY STORED\n{LINE}")
    today = "2026-10-03"
    pages = {
        "https://feed.example/robots.txt": ROBOTS_OK,
        "https://desk.example/robots.txt": ROBOTS_OK,
        "https://blocked.example/robots.txt": ROBOTS_NONE,
        "https://feed.example/rss.xml": rss([
            ("Strategist says stocks have room", "https://feed.example/a/1",
             "Fri, 02 Oct 2026 14:00:00 GMT", "A strategist view"),
            ("Local sports results", "https://feed.example/a/2",
             "Fri, 02 Oct 2026 14:00:00 GMT", "No view here"),
            ("Old strategist note", "https://feed.example/a/3",
             "Mon, 07 Sep 2026 14:00:00 GMT", "Too old"),
        ]),
        "https://feed.example/a/1": article("Strategist says stocks have room",
                                            "2026-10-02"),
        "https://desk.example/insights": (
            b'<a href="/insights/articles/capex-holds">x</a>'
            b'<script>{"u":"https:\\/\\/desk.example\\/insights\\/articles\\/undated-one"}'
            b'</script><a href="/private/x">p</a>'),
        "https://desk.example/insights/articles/capex-holds":
            article("Capex holds", "2026-10-01"),
        "https://desk.example/insights/articles/undated-one":
            b"<html><title>Undated</title><body>No date anywhere.</body></html>",
    }
    replies = {
        "Strategist says stocks have room": {"voices": [{
            "voice": "Jane Fixture", "affiliation": "Fixture Bank",
            "kind": "sell_side", "view": "Expects equities to keep rising into "
            "year-end; sees the capex cycle intact.",
            "quote": "equities still have room to run into year-end",
            "directions": [{"subject": "us_equities", "direction": "bullish"},
                           {"subject": "tulips", "direction": "bullish"}],
            "horizon": "into year-end",
            "stories": [{"story": "ai_capex_durability", "side": "for"}]}]},
        "Capex holds": {"voices": [{
            "voice": "Fixture Research", "affiliation": "Goldman Sachs",
            "kind": None, "view": "Expects hyperscaler capital spending to keep "
            "rising through 2027.",
            "quote": "a quote that is not anywhere in the article text",
            "directions": [{"subject": "ai_capex", "direction": "bullish"}],
            "horizon": "through 2027",
            "stories": [{"story": "ai_capex_durability", "side": "for"},
                        {"story": "midterm_cycle", "side": "against"}]}]},
    }
    web = FakeWeb(pages, fail={"down.example"})
    client = StubClient(replies)
    cfg = scan_cfg()
    ua = "chester-reports/1.0 (fixture@example.invalid)"
    r1 = vsn.run(DB, ua=ua, client=client, fetcher=vsn.Fetcher(ua, 0, opener=web),
                 today=today, cfg=cfg)
    S = r1["sources"]
    check(client.calls == 2, f"one model call per new, dated, in-window item "
                             f"({client.calls} calls)")
    check(all(h == ua for _, h in web.calls),
          "every request carries the EDGAR contact User-Agent")
    check(not any("/private/" in u for u, _ in web.calls),
          "a path robots.txt disallows is never requested")
    check(S["fx_blocked"]["state"] == "robots_disallowed"
          and not any(u.startswith("https://blocked.example/insights")
                      for u, _ in web.calls),
          "a source whose robots.txt disallows it is recorded, not fetched")
    with vmod.VoicesStore() as vs:
        seen = {r["item_url"]: r["status"] for r in vs.conn.execute(
            "SELECT * FROM voice_scan_seen")}
        vrows = vs.rows()
        dump = "\n".join(json.dumps(dict(r)) for t in
                         ("voices", "narrative_evidence", "voice_scan_seen",
                          "voice_scan_runs")
                         for r in vs.conn.execute(f"SELECT * FROM {t}"))
    with ev_mod.EventStore() as ev:
        heads = [dict(r) for r in ev.conn.execute(
            "SELECT * FROM events WHERE source = 'voices_scan'")]
        dump += "\n".join(json.dumps(h) for h in heads)
    check(seen.get("https://feed.example/a/2") == "filtered"
          and seen.get("https://feed.example/a/3") == "old"
          and seen.get("https://desk.example/insights/articles/undated-one") == "undated",
          "off-topic, out-of-window and undated items are recorded and not extracted")
    jane = next((v for v in vrows if v["voice"] == "Jane Fixture"), None)
    desk = next((v for v in vrows if v["voice"] == "Fixture Research"), None)
    check(jane and jane["directions"] == [{"subject": "us_equities",
                                           "direction": "bullish"}]
          and jane["quote"] == "equities still have room to run into year-end"
          and jane["tier"] == 1 and jane["source_url"] == "https://feed.example/a/1",
          "an undeclared subject is dropped; a verbatim quote is kept; the tier "
          "is the outlet's (CNBC, tier 1)")
    check(desk and desk["quote"] is None and desk["kind"] == "sell_side"
          and desk["published_at"] == "2026-10-01",
          "a quote not in the article is dropped; the desk's kind fills a missing "
          "one; the date is the page's own")
    check(BODY_SENTINEL not in dump and "filler text" not in dump,
          "the article body is stored nowhere -- paraphrase, URL and dates only")
    qs = sorted((json.loads(h["payload"])["query"], h["title"]) for h in heads)
    from altdata import source_tiers
    check(len(heads) == 3 and all(source_tiers.counted(t) for _, t in qs)
          and {q for q, _ in qs} == {stories["ai_capex_durability"]["story_query"],
                                     stories["midterm_cycle"]["story_query"]},
          f"each item tagged to a story is one tiered headline under that story's "
          f"query ({len(heads)} rows)")
    calls_before = client.calls
    web2 = FakeWeb(pages, fail={"down.example"})
    vsn.run(DB, ua=ua, client=client, fetcher=vsn.Fetcher(ua, 0, opener=web2),
            today=today, cfg=cfg)
    check(client.calls == calls_before,
          "a second run over the same items makes no model call")
    capped = json.loads(json.dumps(cfg, default=str))
    capped["max_model_calls_per_day"] = 0
    pages2 = dict(pages)
    pages2["https://desk.example/insights"] += b'<a href="/insights/articles/fresh-one">'
    pages2["https://desk.example/insights/articles/fresh-one"] = article(
        "Fresh one", "2026-10-02")
    r3 = vsn.run(DB, ua=ua, client=client,
                 fetcher=vsn.Fetcher(ua, 0, opener=FakeWeb(pages2)),
                 today=today, cfg=capped)
    with vmod.VoicesStore() as vs:
        fresh_seen = vs.seen("fx_desk",
                             "https://desk.example/insights/articles/fresh-one")
    check(client.calls == calls_before and not fresh_seen
          and any(i.get("state") == "deferred_cap"
                  for i in r3["sources"]["fx_desk"]["items"]),
          "past the day's cap no call is made and the item waits, unseen, for "
          "tomorrow")
    r4 = vsn.run(str(Path(TMP) / "nc.db"), ua=None, cfg=cfg)
    with vmod.VoicesStore(str(Path(TMP) / "nc.db")) as vs:
        nc = {r["state"] for r in vs.latest_runs().values()}
    check(r4["state"] == "not_configured" and nc == {"not_configured"},
          "without the EDGAR contact the scan is dormant and says so; no anonymous "
          "fallback")

    # --- D. UNREACHABLE -------------------------------------------------------
    print(f"\n{LINE}\nD. AN UNREACHABLE SOURCE IS NAMED, NEVER PRINTED STALE\n{LINE}")
    check(S["fx_down"]["state"] == "unreachable" and S["fx_desk"]["state"] == "ok",
          "a failing host costs that source only; the pass goes on")
    from daily_cascade import voices_block as vb
    line = vb.daily_line("2026-10-05", "2026-10-05T20:45:00+00:00", DB)
    check(any("Unreachable on the latest scan: Fixture Blocked; Fixture Down" in t
              for t in line["lines"]),
          "the daily line names each unreachable source")
    # An old row from the unreachable source, and nothing new from it:
    with vmod.VoicesStore() as vs:
        vs.write(base_row(voice="Stale Voice", source_id="fx_down", outlet="PIMCO",
                          source_url="https://down.example/x/old",
                          published_at="2026-09-29",
                          retrieved_at="2026-09-30T11:00:00+00:00"))
    wk = vb.week_section("2026-10-10", "2026-10-10T12:00:00+00:00", DB)
    stale = [r for r in wk["table"]["rows"] if r[0] == "Stale Voice"]
    check(stale and stale[0][4].startswith("UNREACHABLE")
          and stale[0][3].startswith("last:"),
          "its voice prints UNREACHABLE with its last view marked as last, never "
          "as this week's")

    # --- E. RENDERS -----------------------------------------------------------
    print(f"\n{LINE}\nE. A FIXTURE WEEK RENDERS SECTION 8 AND THE DAILY LINE\n{LINE}")
    with vmod.VoicesStore() as vs:
        for v, side, aff, d in (("Kilo", "for", "Morgan Stanley", "bullish"),
                                ("Lima", "against", "GMO", "bearish"),
                                ("Mike", "for", "BlackRock Investment Institute",
                                 "bullish")):
            vs.write(base_row(voice=v, affiliation=aff, outlet=aff if aff != "Morgan Stanley"
                              else "Morgan Stanley",
                              source_url=f"https://f.example/{v}",
                              published_at="2026-10-02",
                              retrieved_at="2026-10-05T10:50:00+00:00",
                              directions=[{"subject": "us_equities", "direction": d}],
                              stories=[{"story": "ai_capex_durability", "side": side}]),
                     stories=set(stories))
        vs.write(base_row(voice="Noisy", source_url="https://f.example/noisy",
                          view="Stocks surged and will keep soaring.",
                          published_at="2026-10-02",
                          retrieved_at="2026-10-05T10:50:00+00:00"))
        vs.write(base_row(voice="Policy", source_url="https://f.example/pol",
                          view="Expects a cut after the CPI print shows cooling.",
                          published_at="2026-10-02",
                          retrieved_at="2026-10-05T10:50:00+00:00"))
    line = vb.daily_line("2026-10-05", "2026-10-05T20:45:00+00:00", DB)
    txt = " ".join(line["lines"])
    check(line.get("story") == "ai_capex_durability"
          and txt.startswith("Most cited: AI capex durability")
          and "Dissent: Lima, against" in txt and "https://f.example/Lima" in txt,
          f"the daily line names the most-cited story and its dissent, sourced: "
          f"{txt[:150]}...")
    wk = vb.week_section("2026-10-04", "2026-10-05T20:45:00+00:00", DB)
    texts = [i["text"] for i in wk["items"]]
    ai = next(t for t in texts if t.startswith("AI capex durability"))
    check("for" in ai and "against" in ai and "Dissent:" in ai,
          f"each story states what moved it for and against and who dissented: {ai}")
    ev_lines = [t for t in texts if t.startswith("— ")]
    import re
    check(ev_lines and all("https://" in t and re.search(r", \d{1,2} [A-Z][a-z]{2} "
                                                         r"20\d\d, ", t)
                           for t in ev_lines),
          f"every sourced item carries outlet, date and URL ({len(ev_lines)} items)")
    check(len([t for t in ev_lines]) <= 5 * 4,
          "no story prints more than five items")
    check(any(t.startswith("Consensus: bullish on US equities") and "Against it:" in t
              for t in texts),
          "one consensus-against-contrarian line, with the contrarian sourced")
    cols = wk["table"]["columns"]
    check(cols[:8] == ["Voice", "Affiliation", "Kind", "View", "Status", "Source",
                       "Tier", "Horizon"],
          "the voices table: voice, affiliation, kind, view, status, source, tier, "
          "horizon")
    noisy = next(r for r in wk["table"]["rows"] if r[0] == "Noisy")
    pol = next(r for r in wk["table"]["rows"] if r[0] == "Policy")
    check(noisy[3].startswith("view withheld") and pol[3].startswith("view withheld"),
          f"a view breaking the style rule or the policy-word rule prints withheld "
          f"({noisy[3][:60]} / {pol[3][:60]})")
    from daily_cascade import weekly_stack, stack as stack_mod, stack_render
    sec = weekly_stack.narratives_week_section({"narratives": []}, {}, wk)
    html = stack_render.section_html(
        {"title": "Narratives", "depth": "medium", "items": sec["items"],
         "table": sec["table"], "paragraphs": []}, 8, {}, "email")
    check("Consensus:" in html and "<table" in html and "https://f.example/Lima" in html,
          "section 8 renders its items and the voices table")
    from altdata import observations
    with observations.ObservationStore(DB) as st:
        dsec = stack_mod.narratives_section(st, "2026-10-05",
                                            "2026-10-05T20:45:00+00:00")
    check(dsec["items"][0]["text"].startswith("Most cited: AI capex durability"),
          "the daily close's Narratives section leads with the voices line")
    # 13F (ruled 4 Oct): the CIK is resolved from EDGAR's company lookup at run
    # time, held to EDGAR's CURRENT name, cached, and only a match prints.
    lookup = ["MORGAN STANLEY:0000895421:",
              "GRANTHAM, MAYO, VAN OTTERLOO & CO. LLC:0000999001:",
              "BLACKROCK INC.:0001364742:", "BlackRock, Inc.:0002012383:",
              "UNRELATED FIRM:0000000042:"]
    subs = {"0000895421": {"name": "MORGAN STANLEY", "filings": {"recent": {
                "form": ["10-Q", "13F-HR"], "accessionNumber": ["a-1", "0000895421-26-000001"],
                "reportDate": ["2026-06-30", "2026-06-30"],
                "filingDate": ["2026-08-01", "2026-08-14"]}}},
            "0000999001": {"name": "GMO TRUST (A DIFFERENT FILER NOW)",
                           "filings": {"recent": {"form": []}}},
            "0001364742": {"name": "BlackRock Finance, Inc.",
                           "filings": {"recent": {"form": []}}},
            "0002012383": {"name": "BlackRock, Inc.", "filings": {"recent": {
                "form": ["13F-HR"], "accessionNumber": ["0002012383-26-000009"],
                "reportDate": ["2026-06-30"], "filingDate": ["2026-08-13"]}}}}
    asked = []

    def sec_get(url):
        asked.append(url)
        cik = url.rsplit("CIK", 1)[1].split(".")[0]
        if cik not in subs:
            raise OSError("fixture: no such CIK")
        return json.dumps(subs[cik]).encode()
    r13 = vsn.pull_13f(DB, ua=ua, getter=sec_get, lines=iter(lookup))
    with vmod.VoicesStore() as vs:
        ck = vs.cik_rows()
    check(ck.get("Morgan Stanley", {}).get("state") == "matched"
          and ck["Morgan Stanley"]["cik"] == "0000895421",
          "a voice's CIK is resolved from EDGAR's company lookup and matched on "
          "EDGAR's current name")
    check(ck.get("BlackRock Investment Institute", {}).get("state") == "matched"
          and ck["BlackRock Investment Institute"]["cik"] == "0002012383",
          "a name two CIKs have carried resolves to the one EDGAR names so today "
          "(the former holding company is not taken)")
    check(ck.get("GMO", {}).get("state") == "unmatched"
          and any(m.startswith("GMO:") for m in r13["mismatches"]),
          f"a name that does not match is printed: {r13['mismatches'][:1]}")
    check(all(c["state"] != "matched" for a, c in ck.items()
              if a not in ("Morgan Stanley", "BlackRock Investment Institute")),
          "every other affiliation is unmatched, not guessed")
    n_asked = len(asked)
    vsn.pull_13f(DB, ua=ua, getter=sec_get, lines=iter([]))
    with vmod.VoicesStore() as vs:
        ck2 = vs.cik_rows()
    check(ck2["Morgan Stanley"]["state"] == "matched"
          and ck2["GMO"]["resolved_at"] == ck["GMO"]["resolved_at"],
          "the resolution is cached: a matched CIK stays matched and an unmatched "
          "one is not looked up again inside a week")
    mb = vb.month_block("2026-10-31", "2026-11-01T12:00:00+00:00", DB)
    from monthly_macro.writer import render_v2
    md = render_v2.voices_section({"voices": mb, "tie_backs": {}})
    kilo = next(r for r in mb["table"]["rows"] if r[0] == "Kilo")
    lima = next(r for r in mb["table"]["rows"] if r[0] == "Lima")
    check("| Voice | Affiliation |" in md and "13F (period of report)" in md
          and "13F-HR for 2026-06-30" in kilo[-1] and "**The four weeks, by story**"
          in md and "Consensus vs contrarian" in md,
          "the Monthly's section 4: monthly status, 13F dated to its period of "
          "report, the weeks rolled up by story, the consensus line")
    check(lima[-1] == "—",
          "no 13F figure prints for a voice whose CIK has not matched (GMO)")
    cfg13 = vmod.load_config().get("filers_13f") or {}
    check(cfg13 and all(isinstance(v, str) and not re.fullmatch(r"\d+", v)
                        for v in cfg13.values())
          and "cik" not in json.dumps(cfg13).lower(),
          "no hand-typed CIK anywhere in the config: names only")

    # The scanner's declared helpers for the sources added on 4 Oct.
    check(vsn.url_date("https://x.example/publications/speeches/2026/sept-30-norc",
                       r"/speeches/(?P<year>20\d\d)/(?P<month>[a-z]+)-(?P<day>\d{1,2})-")
          == "2026-09-30",
          "a date the URL carries is read by the source's declared pattern")
    ecb_cfg = json.loads(json.dumps(scan_cfg(), default=str))
    ecb_cfg["sources"] = [{"id": "fx_ecb", "name": "Fixture ECB",
                           "outlet": "European Central Bank", "method": "rss",
                           "url": "https://ecb.example/rss.xml",
                           "link_filter": "/press/key/date/.*\\.html$"}]
    ecb_pages = {"https://ecb.example/robots.txt": ROBOTS_OK,
                 "https://ecb.example/rss.xml": rss([
                     ("A speech", "https://ecb.example/press/key/date/2026/sp1.en.html",
                      "Fri, 02 Oct 2026 10:00:00 GMT", "s"),
                     ("A decision", "https://ecb.example/press/govcdec/2026/d1.en.html",
                      "Fri, 02 Oct 2026 10:00:00 GMT", "d")])}
    re_ = vsn.run(str(Path(TMP) / "ecb.db"), ua=ua, use_model=False,
                  fetcher=vsn.Fetcher(ua, 0, opener=FakeWeb(ecb_pages)),
                  today=today, cfg=ecb_cfg)
    check(re_["sources"]["fx_ecb"]["candidates"] == 1,
          "a mixed feed keeps only the links its source declares (speeches)")

    # --- F. ITEM 7, THE SOURCE LIST, THE SEED ---------------------------------
    print(f"\n{LINE}\nF. THE STORY QUERIES FOLDED IN; THE SOURCES; THE SEED\n{LINE}")
    from altdata.sources import news
    import urllib.request
    real = urllib.request.urlopen
    hit = []
    urllib.request.urlopen = lambda *a, **k: hit.append(a) or (_ for _ in ()).throw(
        RuntimeError("no socket in a code gate"))
    try:
        ev_rows, rep = news.story_events()
    finally:
        urllib.request.urlopen = real
    check(ev_rows == [] and rep.get("state") == "retired" and "robots.txt" in
          rep.get("reason", "") and not hit,
          "the Google News story fetch is retired with its reason and makes no request")
    sh = (REPO / "scripts" / "fetch_overnight.sh").read_text(encoding="utf-8")
    check("altdata.sources.voices_scan run" in sh and "altdata.voices seed" in sh,
          "the 06:45 overnight pass runs the seed and the scan")
    full = vmod.load_config()
    untiered = [s["id"] for s in full["sources"]
                if source_tiers.tier_of(f"x - {s['outlet']}") is None]
    check(not untiered, f"every source's outlet is tiered in source_tiers.yaml "
                        f"({len(full['sources'])} sources)")
    banned_hosts = ("news.google.com", "search.cnbc.com", "reuters.com",
                    "apolloacademy.com")
    check(not [s for s in full["sources"] if any(h in s["url"] for h in banned_hosts)],
          "no source points at a host whose robots.txt forbids the scan")
    check(all(s["method"] in ("rss", "listing", "page") for s in full["sources"])
          and all(s.get("link_pattern") for s in full["sources"]
                  if s["method"] == "listing")
          and all(s.get("edition_pattern") for s in full["sources"]
                  if s["method"] == "page"),
          "every source declares a known method and what it needs")
    gdb = str(Path(TMP) / "seed.db")
    a = vmod.seed(gdb)
    b = vmod.seed(gdb)
    g = vmod.status_table("2026-10-05", "weekly", as_of="2026-10-04T12:00:00+00:00",
                          db_path=gdb)
    gtm = [v for v in g["voices"] if "J.P. Morgan" in v["row"]["voice"]]
    check(a["written"] == 1 and b["written"] == 0 and b["present"] == 1,
          "the J.P. Morgan GTM seed is written once (idempotent)")
    check(gtm and gtm[0]["status"] == "NEW"
          and gtm[0]["row"]["published_at"] == "2026-09-30"
          and gtm[0]["row"]["source_url"].startswith("https://am.jpmorgan.com/")
          and gtm[0]["row"]["tier"] == 2 and gtm[0]["row"]["kind"] == "buy_side",
          "its status is computed NEW, sourced to the GTM URL, 30 Sep 2026, tier 2, "
          "buy-side (an asset manager)")

    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
