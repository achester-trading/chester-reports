"""
RSS: the agencies' press feeds, and the declared story queries.

    python -m altdata.sources.news probe
    python -m altdata.sources.news pull            # the ingest step
    python -m altdata.sources.news pull --dry-run

Two different things share this module because they share one parser:

  PRESS FEEDS are primary sources. The Fed, BLS and BEA publish their own releases,
  and an item from bls.gov/feed/cpi.rss IS the CPI release -- headline number in
  the title, on the minute it was published.

  STORY QUERIES are an aggregator's answer to a question we wrote down first. The
  item is somebody's summary of somebody else's reporting; the url is where the
  actual claim lives. `source_registry.yaml` marks news_rss `unofficial_mirror`
  for exactly this reason.

-----------------------------------------------------------------------------
WHAT THE PROBE FOUND, 25 September 2026 -- recorded because it decided the list
-----------------------------------------------------------------------------

  fed press_all.xml        200, 20 items   -- kept (404 on one earlier attempt:
                                              transient, and why 404 is not retried)
  fed press_monetary.xml   200, 15 items   -- kept, the FOMC statements
  fed press_bcreg.xml      200, 15 items   -- NOT kept: bank supervision, no
                                              market mechanism in scope
  fed h15.xml              200, 0 items    -- NOT kept: a data feed with a
                                              different schema, not a press feed
  bls empsit.rss           200, 12 items   -- kept, payrolls with the number in
                                              the title
  bls cpi.rss              200, 12 items   -- kept, CPI likewise
  bls bls_latest.rss       200, 1 item     -- NOT kept: a pointer page, not releases
  bls news_release.rss     404             -- gone
  bea rss.xml              200, 48 items   -- kept, GDP and the trade balance
  treasury press feed      404 / 404 / timeout on three separate paths

TREASURY IS ABSENT AND SAYS SO. `home.treasury.gov/news/press-releases/feed` and
`/rss/press.xml` both return 404 and a third attempt timed out. It is declared in
FEEDS with `enabled: False` and a reason rather than deleted, because the absence
is a fact about the source and the next person to look for it should find the
three URLs that did not work instead of trying them again.
"""

from __future__ import annotations

import datetime as dt
import email.utils
import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Iterable, Optional
from urllib.parse import quote

from .. import events as ev_mod
from ._base import FetchError, http_get_bytes

log = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent
QUERIES_PATH = REPO / "config" / "story_queries.yaml"

ATOM = "{http://www.w3.org/2005/Atom}"

# U+FEFF plus the ordinary whitespace. Named because it is the difference
# between a Fed feed parsing and reporting "invalid token, line 1, column 1".
BOM_AND_SPACE = '\ufeff \t\r\n'

# The press feeds, with the entities each one bears on. `entities` is what makes a
# release findable from the metric it moves: an empsit item is linked to
# fred.claims_4wk and fred.u3_rate, so "what landed that touches growth" is a
# query rather than a reading of titles.
FEEDS: dict[str, dict[str, Any]] = {
    "fed_press": {
        "url": "https://www.federalreserve.gov/feeds/press_all.xml",
        "entities": [],
        "why": "every Board press release; the widest net on the Fed",
    },
    "fed_monetary": {
        "url": "https://www.federalreserve.gov/feeds/press_monetary.xml",
        "entities": ["fred.fed_funds", "fred.fed_balance"],
        "why": "the FOMC statements and the policy releases",
    },
    "bls_empsit": {
        "url": "https://www.bls.gov/feed/empsit.rss",
        "entities": ["fred.u3_rate", "fred.nfp", "fred.avg_wkly_hours",
                     "calc.sahm_rule"],
        "why": "the employment situation -- payrolls and the unemployment rate",
    },
    "bls_cpi": {
        "url": "https://www.bls.gov/feed/cpi.rss",
        "entities": ["fred.cpi", "fred.core_cpi", "calc.yoy_cpi",
                     "calc.yoy_core_cpi"],
        "why": "CPI, with the headline change in the title",
    },
    "bea_news": {
        "url": "https://apps.bea.gov/rss/rss.xml",
        "entities": ["fred.real_gdp", "fred.pce", "fred.core_pce",
                     "calc.yoy_real_gdp", "calc.yoy_core_pce"],
        "why": "GDP, PCE and the trade balance",
    },
    "treasury_press": {
        "url": "https://home.treasury.gov/news/press-releases/feed",
        "entities": ["fred.tga"],
        "why": "Treasury press releases",
        "enabled": False,
        "absent_reason": (
            "no working feed found on 25 Sep 2026. "
            "/news/press-releases/feed -> 404, /rss/press.xml -> 404, and a third "
            "attempt read-timed out at 25s. Kept declared with the URLs that "
            "failed so the next attempt starts from evidence"),
    },
}

# THE SEARCH FEED. Google News returned 68 items for a probe query against Bing's
# 8, which is the whole reason it is primary; both are aggregators and both hand
# back a redirect rather than the publisher's url, which the registry records as a
# caveat rather than pretending otherwise.
SEARCH = {
    "google_news": ("https://news.google.com/rss/search?q={q}"
                    "&hl=en-US&gl=US&ceid=US:en"),
    "bing_news": "https://www.bing.com/news/search?q={q}&format=RSS",
}
SEARCH_PRIMARY = "google_news"


def load_queries() -> dict:
    import yaml
    with QUERIES_PATH.open(encoding="utf-8") as fp:
        return yaml.safe_load(fp) or {}


def _text(el: Optional[ET.Element]) -> str:
    return "" if el is None else (el.text or "").strip()


def _first(item: ET.Element, *names: str) -> str:
    for n in names:
        el = item.find(n)
        if el is not None:
            got = (el.text or el.get("href") or "").strip()
            if got:
                return got
    return ""


def _when(raw: str) -> Optional[str]:
    """An RSS date in any of the three shapes these feeds use, as UTC ISO.

    BLS stamps ISO-8601 with an offset, the Fed and Google use RFC-2822, and BEA
    uses RFC-2822 with a NAMED zone ("EDT") that email.utils cannot offset. The
    named-zone case is why this returns None rather than guessing: a timestamp
    guessed four hours wrong would put a morning release in the previous session.
    """
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        d = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=dt.timezone.utc)
        return d.astimezone(dt.timezone.utc).isoformat()
    except ValueError:
        pass
    try:
        d = email.utils.parsedate_to_datetime(raw)
        if d is None:
            return None
        if d.tzinfo is None:
            # A named zone parsed to naive. EDT/EST are the only ones these feeds
            # use and both are US Eastern, so the session calendar's own zone is
            # the right answer rather than UTC -- which would be four or five
            # hours early and could move an 08:30 release into the day before.
            from .. import session as sess
            d = d.replace(tzinfo=sess.EASTERN)
        return d.astimezone(dt.timezone.utc).isoformat()
    except (TypeError, ValueError):
        return None


def parse_feed(xml: "bytes | str") -> list[dict]:
    """RSS 2.0 or Atom, whichever this feed happens to be.

    THE BOM IS WHY THIS IS NOT A ONE-LINER. The Fed's feeds are UTF-8 with a byte
    order mark, and ExpatError reports it as "not well-formed (invalid token): line
    1, column 1" -- which reads like a broken feed rather than a leading character.
    A probe that passed raw BYTES to the parser never saw it, because ET strips the
    mark itself when it is decoding; passing an already-decoded string leaves
    U+FEFF sitting in front of the declaration. Both Fed feeds parsed in the probe
    and failed in the module for exactly this reason.
    """
    # BYTES STRAIGHT TO THE PARSER, which reads the document's own encoding
    # declaration. A str argument is accepted for a caller with a literal, and is
    # stripped of a leading BOM first -- but the fetch path never takes it.
    if isinstance(xml, str):
        root = ET.fromstring(xml.lstrip(BOM_AND_SPACE).encode("utf-8"))
    else:
        root = ET.fromstring(xml)
    items = root.findall(".//item") or root.findall(f".//{ATOM}entry")
    out = []
    for it in items:
        title = _first(it, "title", f"{ATOM}title")
        if not title:
            continue
        out.append({
            "title": re.sub(r"\s+", " ", title).strip(),
            "url": _first(it, "link", f"{ATOM}link", "guid"),
            "published_raw": _first(it, "pubDate", f"{ATOM}updated",
                                    f"{ATOM}published",
                                    "{http://purl.org/dc/elements/1.1/}date"),
            "body": re.sub(r"<[^>]+>", " ",
                           _first(it, "description", f"{ATOM}summary",
                                  f"{ATOM}content")),
            "guid": _first(it, "guid", f"{ATOM}id"),
        })
    return out


def press_events(now: Optional[str] = None) -> tuple[list[ev_mod.Event], dict]:
    """Every enabled press feed, as `release` events. Never raises."""
    from .. import session
    out: list[ev_mod.Event] = []
    report: dict[str, Any] = {}
    for name, spec in FEEDS.items():
        if spec.get("enabled") is False:
            report[name] = {"state": "disabled",
                            "reason": spec.get("absent_reason")}
            continue
        try:
            xml = http_get_bytes(spec["url"])
        except (FetchError, Exception) as exc:                  # noqa: BLE001
            report[name] = {"state": "failed",
                            "reason": f"{type(exc).__name__}: {exc}"[:200]}
            continue
        try:
            items = parse_feed(xml)
        except ET.ParseError as exc:
            report[name] = {"state": "unparseable", "reason": str(exc)[:160]}
            continue
        kept = 0
        for it in items:
            when = _when(it["published_raw"])
            if when is None:
                # NO TIMESTAMP, NO ROW. observed_at is the event's own clock and
                # substituting "now" would date a month-old release to today.
                continue
            out.append(ev_mod.Event(
                type="release", observed_at=when, source=name,
                title=it["title"], body=it["body"], url=it["url"],
                entities=spec.get("entities") or [],
                key=it["guid"] or None,
                payload={"feed": name, "published_at": when,
                         "published_raw": it["published_raw"]}))
            kept += 1
        report[name] = {"state": "ok", "items": len(items), "kept": kept,
                        "undated": len(items) - kept}
    return out, report


def story_events(now: Optional[str] = None,
                 feed: Optional[str] = None) -> tuple[list[ev_mod.Event], dict]:
    """The declared story queries, as `headline` events, capped per query."""
    cfg = load_queries()
    cap = int(cfg.get("cap_per_day") or 12)
    which = feed or SEARCH_PRIMARY
    template = SEARCH[which]
    out: list[ev_mod.Event] = []
    report: dict[str, Any] = {"feed": which, "cap_per_day": cap,
                             "version": cfg.get("version")}
    for name, spec in (cfg.get("queries") or {}).items():
        url = template.format(q=quote(spec["query"]))
        try:
            xml = http_get_bytes(url)
            items = parse_feed(xml)
        except Exception as exc:                               # noqa: BLE001
            report[name] = {"state": "failed",
                            "reason": f"{type(exc).__name__}: {exc}"[:160]}
            continue
        kept = 0
        for it in items:
            if kept >= cap:
                break
            when = _when(it["published_raw"])
            if when is None:
                continue
            out.append(ev_mod.Event(
                type="headline", observed_at=when, source=f"{which}",
                title=it["title"], body=it["body"], url=it["url"],
                entities=spec.get("entities") or [],
                key=it["guid"] or None,
                payload={"query": name, "theme": spec.get("theme"),
                         "query_text": spec["query"], "published_at": when,
                         "queries_version": cfg.get("version")}))
            kept += 1
        report[name] = {"state": "ok", "returned": len(items), "kept": kept,
                        "capped": len(items) > kept}
    return out, report


def pull(store: Optional[ev_mod.EventStore] = None,
         dry_run: bool = False) -> dict:
    """Press feeds plus story queries, into the events table."""
    own = store is None
    ev = store or ev_mod.EventStore()
    try:
        press, press_report = press_events()
        stories, story_report = story_events()
        events = press + stories
        wrote = ({"seen": len(events), "inserted": 0, "duplicates": 0}
                 if dry_run else ev.write_many(events))
        return {"press": press_report, "stories": story_report,
                "written": wrote, "dry_run": dry_run}
    finally:
        if own:
            ev.close()


def _main(argv: list[str]) -> int:
    import argparse
    import json
    p = argparse.ArgumentParser(description="Press feeds and story queries.")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("probe")
    pl = sub.add_parser("pull")
    pl.add_argument("--dry-run", action="store_true")
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")

    if a.cmd == "probe":
        print(f"{'feed':<18}{'state':<14}{'items':>7}{'kept':>6}  reason/why")
        press, rep = press_events()
        for name, r in rep.items():
            print(f"{name:<18}{r['state']:<14}{r.get('items', ''):>7}"
                  f"{r.get('kept', ''):>6}  "
                  f"{(r.get('reason') or FEEDS[name].get('why') or '')[:74]}")
        stories, srep = story_events()
        print(f"\nstory queries via {srep['feed']}, cap {srep['cap_per_day']}/day, "
              f"{srep.get('version')}")
        for name, r in srep.items():
            if not isinstance(r, dict):
                continue
            print(f"  {name:<24}{r.get('state',''):<10}"
                  f"returned={r.get('returned','-'):<5} kept={r.get('kept','-')}")
        print(f"\n{len(press)} press event(s), {len(stories)} headline(s) ready")
        for e in (press[:2] + stories[:2]):
            print(f"  {e.observed_at[:19]}  {e.type:<9} {e.source:<14} "
                  f"{e.title[:66]}")
        return 0

    r = pull(dry_run=a.dry_run)
    print(json.dumps(r, indent=2, default=str)[:2400])
    return 0


if __name__ == "__main__":                                     # pragma: no cover
    import sys
    raise SystemExit(_main(sys.argv[1:]))
