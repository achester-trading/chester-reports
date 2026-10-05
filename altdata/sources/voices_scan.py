"""
The voices scan: desks', strategists' and officials' published views, once a day.

    python -m altdata.sources.voices_scan probe          # fetch and filter; no model, no writes
    python -m altdata.sources.voices_scan run            # the 06:45 step
    python -m altdata.sources.voices_scan run --no-model # fetch, record nothing as seen

Phase B, ruled 4 Oct 2026. Sources, caps and vocabularies are declared in
config/voices_sources.yaml, which says why each is there; this module reads them.

-----------------------------------------------------------------------------
WHAT ONE RUN DOES
-----------------------------------------------------------------------------
For each declared source: read its robots.txt (and obey it -- a disallowed path is
`robots_disallowed`, never fetched); read the feed or listing page; for each item
NOT SEEN BEFORE, fetch the article once, date it from the feed or the page's own
metadata, and -- if it is inside the lookback window and under the day's model cap
-- make ONE model call that returns the voices it carries. Each voice is written to
the register through `VoicesStore.write`, which refuses an unsourced row; each story
an item bears on becomes an evidence row and a `headline` event under that story's
declared query (below). The article text is held in memory for the call and never
written anywhere.

A source that cannot be read records `unreachable` with its reason, and the
reports print "unreachable: <name>" -- they never print that source's older rows
as if they were today's.

-----------------------------------------------------------------------------
THE STORY QUERIES ARE FOLDED IN HERE (item 7 of the Phase B instruction)
-----------------------------------------------------------------------------
The story-queries block returned zero items for every declared query. Two causes,
both in how the queries were fetched rather than in the queries:

  1. Google News search returns its results by RELEVANCE, not date, and the ingest
     kept the first `cap_per_day` (12). Those were the same months-old items every
     morning (ages 4 to 300 days on 4 Oct), so every one was a duplicate of a row
     already stored: 2 new of 156 seen on 2 Oct. Nothing published since the prior
     close survived, and a block reading "since the previous close" found nothing.
  2. news.google.com/robots.txt disallows /rss/search for every user agent. The
     Phase B rule is to respect robots.txt, so the fetch could not be repaired in
     place by adding a recency window.

It is the same job -- coverage that bears on a declared story, from tiered outlets
-- so it is folded in rather than retired: an item this scan tags to a story is
written as a `headline` event with that story's declared `story_query` in its
payload, titled "<title> - <outlet>" so source_tiers classifies it exactly as it
classified an aggregator headline. The register's attention and headline-evidence
rules read those rows unchanged. What changed is where the rows come from: a
declared list of public sources, instead of a search the host forbids.
"""

from __future__ import annotations

import datetime as dt
import html as html_mod
import json
import logging
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from typing import Any, Callable, Optional

from .. import events as ev_mod
from .. import session, source_tiers
from .. import voices as vmod

log = logging.getLogger(__name__)

TIMEOUT = 25
MAX_BYTES = 3_000_000


# ---------------------------------------------------------------------------
# Identity and politeness
# ---------------------------------------------------------------------------
def user_agent() -> Optional[str]:
    """The EDGAR User-Agent, with the operator's contact. None when unset."""
    from . import edgar  # noqa: PLC0415
    return edgar.user_agent()


class Fetcher:
    """GETs with one User-Agent, robots.txt obeyed, one request per host per
    `pause` seconds. `get` raises urllib errors; `allowed` never raises."""

    def __init__(self, ua: str, pause: float = 2.0,
                 opener: Optional[Callable[[str, dict], bytes]] = None) -> None:
        self.ua = ua
        self.pause = pause
        self._last: dict[str, float] = {}
        self._robots: dict[str, Any] = {}
        self._open = opener or self._urlopen

    def _urlopen(self, url: str, headers: dict) -> bytes:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.read(MAX_BYTES)

    def _wait(self, host: str) -> None:
        last = self._last.get(host)
        if last is not None:
            gap = time.monotonic() - last
            if gap < self.pause:
                time.sleep(self.pause - gap)
        self._last[host] = time.monotonic()

    def get(self, url: str) -> bytes:
        host = urllib.parse.urlsplit(url).netloc
        self._wait(host)
        return self._open(url, {"User-Agent": self.ua,
                                "Accept-Language": "en-US,en;q=0.8"})

    def robots(self, url: str):
        """The host's parsed robots.txt; None when it could not be read at all
        (a network failure, a 5xx) -- which is treated as disallow, the
        conservative reading. A 4xx means no rules, which allows."""
        p = urllib.parse.urlsplit(url)
        base = f"{p.scheme}://{p.netloc}"
        if base in self._robots:
            return self._robots[base]
        rp = urllib.robotparser.RobotFileParser()
        try:
            body = self.get(base + "/robots.txt")
            rp.parse(body.decode("utf-8", "replace").splitlines())
        except urllib.error.HTTPError as exc:
            if 400 <= exc.code < 500:
                rp.parse([])
            else:
                rp = None
        except Exception:                                       # noqa: BLE001
            rp = None
        self._robots[base] = rp
        return rp

    def allowed(self, url: str) -> bool:
        rp = self.robots(url)
        if rp is None:
            return False
        return rp.can_fetch("chester-reports", url) and rp.can_fetch(self.ua, url)


# ---------------------------------------------------------------------------
# Parsing -- pure functions of the bytes, so the gate drives them from fixtures
# ---------------------------------------------------------------------------
MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], 1)}
MON3 = {k[:3]: v for k, v in MONTHS.items()}

META_DATE = [
    r'"datePublished"\s*:\s*"([^"]+)"',
    r'<meta[^>]+(?:property|name)="article:published_time"[^>]+content="([^"]+)"',
    r'<meta[^>]+content="([^"]+)"[^>]+(?:property|name)="article:published_time"',
    r'<meta[^>]+name="(?:publish[_-]?date|pubdate|date|dc\.date|DC\.date\.issued)"'
    r'[^>]+content="([^"]+)"',
    r'"publishDate"\s*:\s*"([^"]+)"',
    r'"publishedDate"\s*:\s*"([^"]+)"',
    r'"firstPublishedDate"\s*:\s*"([^"]+)"',
    r'<meta[^>]+name="content_publishedAt"[^>]+content="([^"]+)"',
    r'<time[^>]+datetime="([^"]+)"',
]
TEXT_DATE = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|October|"
    r"November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?"
    r"\s+(\d{1,2}),\s+(20\d\d)\b"
    r"|\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\s+(20\d\d)\b")
URL_DATE = re.compile(r"(?<!\d)(20[2-3]\d)(0[1-9]|1[0-2])([0-2]\d|3[01])[a-z]?\.htm")


def parse_date(raw: str) -> Optional[str]:
    """An ISO date (YYYY-MM-DD) from the shapes these pages use, or None.
    `0001-01-01` and other placeholder years are None, never a date."""
    s = html_mod.unescape(str(raw or "")).strip()
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        y = int(m.group(1))
        if 2000 <= y <= 2100:
            try:
                return dt.date(y, int(m.group(2)), int(m.group(3))).isoformat()
            except ValueError:
                return None
        return None
    m = TEXT_DATE.search(s)
    if m:
        try:
            if m.group(1):
                mon = MONTHS.get(m.group(1).lower()) or MON3.get(m.group(1).lower()[:3])
                return dt.date(int(m.group(3)), mon, int(m.group(2))).isoformat()
            return dt.date(int(m.group(6)), MONTHS[m.group(5).lower()],
                           int(m.group(4))).isoformat()
        except (ValueError, TypeError):
            return None
    try:
        import email.utils  # noqa: PLC0415
        d = email.utils.parsedate_to_datetime(s)
        if d is not None and 2000 <= d.year <= 2100:
            return d.date().isoformat()
    except (TypeError, ValueError, IndexError):
        pass
    return None


def page_date(html: str, url: str = "",
              patterns: Optional[list[str]] = None) -> Optional[str]:
    """The article's own published date: structured metadata first, then the
    source's DECLARED date pattern (config `date_pattern`), then the URL's date
    stamp (the Fed's `bowman20261001a.htm`). None if none yields one.

    No guess from the page's running text: a listing's related-article promos
    carry dates too, and the first date on a page is as often theirs as its own.
    An undated item is not stored."""
    for p in META_DATE + list(patterns or []):
        for m in re.finditer(p, html, re.I):
            d = parse_date(m.group(1))
            if d:
                return d
    m = URL_DATE.search(url or "")
    if m:
        return parse_date(f"{m.group(1)}-{m.group(2)}-{m.group(3)}")
    return None


def url_date(url: str, pattern: Optional[str]) -> Optional[str]:
    """A date the URL itself carries, by a source's DECLARED pattern with named
    groups `year`, `month` (a name or abbreviation) and `day` -- the Chicago
    Fed's pages carry no date but their path (/2026/sept-30-norc)."""
    if not pattern:
        return None
    m = re.search(pattern, url or "")
    if not m:
        return None
    mon = m.group("month").lower()
    num = MONTHS.get(mon) or MON3.get(mon[:3])
    try:
        return dt.date(int(m.group("year")), int(num), int(m.group("day"))).isoformat()
    except (TypeError, ValueError):
        return None


def _meta(html: str, *names: str) -> Optional[str]:
    for n in names:
        for p in (rf'<meta[^>]+(?:property|name)="{n}"[^>]+content="([^"]*)"',
                  rf'<meta[^>]+content="([^"]*)"[^>]+(?:property|name)="{n}"'):
            m = re.search(p, html, re.I)
            if m and m.group(1).strip():
                return html_mod.unescape(m.group(1)).strip()
    return None


def page_title(html: str) -> Optional[str]:
    t = _meta(html, "og:title", "twitter:title")
    if t:
        return re.sub(r"\s+", " ", t)
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    return re.sub(r"\s+", " ", html_mod.unescape(m.group(1))).strip() if m else None


def page_text(html: str, limit: int = 12000) -> str:
    """The page's readable text, boilerplate blocks removed. Held in memory for
    the model call; never stored."""
    h = re.sub(r"(?is)<(script|style|noscript|svg|nav|header|footer|form|"
               r"aside)[^>]*>.*?</\1>", " ", html)
    m = re.search(r"(?is)<(article|main)[^>]*>(.*)</\1>", h)
    if m and len(m.group(2)) > 2000:
        h = m.group(2)
    t = re.sub(r"(?s)<[^>]+>", " ", h)
    t = html_mod.unescape(t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:limit]


def listing_links(html: str, base: str, pattern: str, limit: int) -> list[str]:
    """Article URLs on a listing page, in page order, deduplicated. The pattern
    is matched anywhere in the page -- several desks put their links in JSON
    rather than in href attributes."""
    out: list[str] = []
    rx = re.compile(r"(?:https?://[A-Za-z0-9.-]+)?" + pattern)
    for m in rx.finditer(html.replace("\\/", "/")):
        u = urllib.parse.urljoin(base, m.group(0))
        u = u.split("#")[0].split("?")[0]
        if u.rstrip("/") == base.rstrip("/") or u in out:
            continue
        if urllib.parse.urlsplit(u).netloc != urllib.parse.urlsplit(base).netloc:
            continue
        out.append(u)
        if len(out) >= limit:
            break
    return out


# ---------------------------------------------------------------------------
# Extraction -- one model call per new item
# ---------------------------------------------------------------------------
def _client():
    """The Anthropic client through the one secrets loader, or (None, reason)."""
    from .. import secrets  # noqa: PLC0415
    key_name = "ANTHROPIC" + "_API_KEY"
    if not secrets.present(key_name):
        return None, f"{key_name} is not set (checked environment, then .env)"
    try:
        import anthropic  # noqa: PLC0415
    except ImportError:
        return None, "the anthropic package is not installed"
    try:
        return anthropic.Anthropic(), ""
    except Exception as exc:                                    # noqa: BLE001
        return None, f"client construction failed: {type(exc).__name__}: {exc}"


def extraction_prompt(cfg: dict, stories: dict[str, dict]) -> str:
    subj = "\n".join(f"  {k}: {v.get('label')} -- bullish means it {v.get('means')}"
                     for k, v in (cfg.get("subjects") or {}).items())
    st = "\n".join(f"  {k}: {v.get('name')} -- the story: {v.get('direction')}"
                   for k, v in stories.items())
    kinds = ", ".join(f"{k} ({v})" for k, v in (cfg.get("kinds") or {}).items())
    return f"""You read one published article and list the market VIEWS it attributes to named voices. Return JSON only.

A voice is a person or a desk (a strategist, an economist, a fund manager, a central bank official, or a firm's research or investment team) whose own view on markets or the economy the article states. Reporters, unnamed "investors", "traders" and "the market" are not voices. If the article attributes no such view, return {{"voices": []}}.

For each voice return:
  voice        the person's name, or the desk's name when no person is named
  affiliation  the firm or institution
  kind         one of: {kinds}
  view         ONE line, at most 35 words, in your own words: what the voice expects or recommends. Plain declarative sentences. No adjective that does a number's work (no "sharply", "massive", "surged"). Use "hike", "cut" or "hold" only for the Federal Reserve's policy rate.
  quote        at most one verbatim quote from the article, under 15 words, copied exactly; or null
  directions   a list of {{"subject": <id>, "direction": "bullish" | "bearish" | "neutral"}} for each declared subject the view takes a side on. Only these subjects:
{subj}
               A subject the voice does not take a side on is left out. Never invent a subject.
  horizon      the horizon the voice states ("next 12 months", "into year-end", "near term"), or null when none is stated
  stories      a list of {{"story": <id>, "side": "for" | "against"}} for each story below the view bears on directly -- "for" when it supports the story as stated, "against" when it disputes it. Leave it empty when the view does not bear on a story.
{st}

Return exactly: {{"voices": [ ... ]}}. No prose outside the JSON."""


def _json_from(text: str) -> dict:
    t = (text or "").strip()
    m = re.search(r"\{.*\}", t, re.S)
    if not m:
        raise ValueError("no JSON object in the reply")
    return json.loads(m.group(0))


def extract(client, model: str, system: str, title: str, url: str,
            published: str, text: str, max_tokens: int = 1800) -> list[dict]:
    """One call; the voices the article carries, unvalidated."""
    msg = client.messages.create(
        model=model, max_tokens=max_tokens, system=system,
        messages=[{"role": "user", "content":
                   f"TITLE: {title}\nURL: {url}\nPUBLISHED: {published}\n\n"
                   f"ARTICLE TEXT:\n{text}"}])
    reply = "".join(getattr(b, "text", "") for b in msg.content)
    return list((_json_from(reply).get("voices") or []))


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[‘’“”\"']", "",
                                      str(s or ""))).strip().lower()


def clean_voice(v: dict, cfg: dict, text: str, stories: set) -> tuple[dict, list[str]]:
    """The model's voice held to the declared vocabularies before the register's
    own refusal: an undeclared subject or story is dropped (and noted), and a
    quote that is not verbatim in the article is dropped -- a quote we cannot show
    is in the source is not a quote."""
    notes = []
    subj = set((cfg.get("subjects") or {}).keys())
    dirs = set(cfg.get("directions") or ())
    out_dirs = []
    for d in v.get("directions") or []:
        if d.get("subject") in subj and d.get("direction") in dirs:
            out_dirs.append({"subject": d["subject"], "direction": d["direction"]})
        else:
            notes.append(f"direction dropped: {d}")
    out_st = []
    for e in v.get("stories") or []:
        if e.get("story") in stories and e.get("side") in vmod.SIDES:
            out_st.append({"story": e["story"], "side": e["side"]})
        else:
            notes.append(f"story dropped: {e}")
    q = v.get("quote")
    if q:
        if len(str(q).split()) > vmod.QUOTE_MAX_WORDS or _norm(q) not in _norm(text):
            notes.append("quote dropped: not verbatim in the article, or 15+ words")
            q = None
    return ({"voice": str(v.get("voice") or "").strip(),
             "affiliation": str(v.get("affiliation") or "").strip(),
             "kind": v.get("kind"), "view": str(v.get("view") or "").strip(),
             "quote": q, "directions": out_dirs, "horizon": v.get("horizon"),
             "stories": out_st}, notes)


# ---------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------
def _candidates(src: dict, f: Fetcher, cfg: dict) -> list[dict]:
    """The source's items: url, title, summary and (for a feed) date."""
    from . import news  # noqa: PLC0415
    raw = f.get(src["url"])
    if src["method"] == "rss":
        out = []
        keep = re.compile(src["link_filter"]) if src.get("link_filter") else None
        for it in news.parse_feed(raw):
            when = news._when(it["published_raw"])
            # A feed that mixes kinds (the ECB's press feed carries speeches,
            # decisions and statistics) declares which links are its voices.
            if keep and not keep.search(it["url"] or ""):
                continue
            out.append({"url": it["url"].strip(), "title": it["title"],
                        "summary": re.sub(r"\s+", " ", it.get("body") or "").strip(),
                        "published": when[:10] if when else None,
                        "published_at": when})
        return out
    html = raw.decode("utf-8", "replace")
    if src["method"] == "page":
        # A FIXED PAGE THAT CHANGES EACH EDITION. The edition is identified by its
        # own permanent document (the dated link the page carries), which is what
        # is stored as the source; the page's HTML is the text the model reads.
        m = re.search(src["edition_pattern"], html.replace("\\/", "/"))
        if not m:
            return []
        ed_url = urllib.parse.urljoin(src["url"], m.group(0))
        st = re.search(r"(20\d\d)(\d\d)(\d\d)", ed_url)
        pub = parse_date(f"{st.group(1)}-{st.group(2)}-{st.group(3)}") if st else None
        return [{"url": ed_url, "fetch_url": src["url"], "title": page_title(html),
                 "summary": "", "published": pub, "published_at": None}]
    links = listing_links(html, src["url"], src["link_pattern"],
                          int(src.get("max_links") or 40))
    return [{"url": u, "title": None, "summary": "", "published": None,
             "published_at": None} for u in links]


def _story_defs(db_path: Optional[str]) -> dict[str, dict]:
    """The register's active stories and their declared query names."""
    from .. import narratives  # noqa: PLC0415
    cfg = narratives.load_config()
    defs = cfg.get("narratives") or {}
    try:
        with narratives.NarrativeRegister(db_path) as reg:
            active = {r["narrative_id"] for r in reg.all("active")}
    except Exception:                                           # noqa: BLE001
        active = set()
    if active:
        defs = {k: v for k, v in defs.items() if k in active}
    return defs


def run(db_path: Optional[str] = None, *, ua: Optional[str] = None,
        use_model: bool = True, client=None, fetcher: Optional[Fetcher] = None,
        only: Optional[list[str]] = None, today: Optional[str] = None,
        cfg: Optional[dict] = None) -> dict:
    """One pass over every declared source. Never raises for a source's failure:
    that source records its state and the pass moves on."""
    cfg = cfg or vmod.load_config()
    now = session.utc_iso()
    today = today or now[:10]
    run_id = f"voices-{now.replace(':', '').replace('-', '')[:15]}"
    ua = ua or user_agent()
    report: dict[str, Any] = {"run_id": run_id, "sources": {}, "model": None}
    sources = [s for s in cfg.get("sources") or []
               if not only or s["id"] in only]
    with vmod.VoicesStore(db_path) as vs:
        if not ua:
            for s in sources:
                vs.record_run(run_id, s["id"], s["name"], "not_configured",
                              "CHESTER_SEC_CONTACT is unset: the scan identifies "
                              "itself as EDGAR does and has no other identity")
            report["state"] = "not_configured"
            return report
        f = fetcher or Fetcher(ua, float(cfg.get("politeness_seconds") or 2))
        model = cfg.get("model") or "claude-sonnet-5"
        if use_model and client is None:
            client, why = _client()
            if client is None:
                report["model"] = f"unavailable: {why}"
                use_model = False
        stories = _story_defs(db_path)
        system = extraction_prompt(cfg, stories)
        cap = int(cfg["max_model_calls_per_day"] if cfg.get("max_model_calls_per_day") is not None else 30)
        used = vs.model_calls_on(today)
        lookback = (dt.date.fromisoformat(today)
                    - dt.timedelta(days=int(cfg.get("lookback_days") or 10))).isoformat()
        events: list[ev_mod.Event] = []
        deadline = time.monotonic() + float(cfg.get("time_budget_seconds") or 240)
        for s in sources:
            if time.monotonic() > deadline:
                vs.record_run(run_id, s["id"], s["name"], "ok",
                              "not reached: the scan's time budget ran out")
                report["sources"][s["id"]] = {"state": "ok", "candidates": 0,
                                              "new_items": 0, "extracted": 0,
                                              "voices": 0, "model_calls": 0,
                                              "refused": [], "items": [],
                                              "reason": "time budget"}
                continue
            rep = {"candidates": 0, "new_items": 0, "extracted": 0, "voices": 0,
                   "model_calls": 0, "refused": [], "items": []}
            report["sources"][s["id"]] = rep
            tier = source_tiers.tier_of(f"x - {s['outlet']}")
            if not f.allowed(s["url"]):
                rp = f.robots(s["url"])
                state = "unreachable" if rp is None else "robots_disallowed"
                why = ("robots.txt could not be read" if rp is None
                       else "robots.txt disallows the declared URL")
                vs.record_run(run_id, s["id"], s["name"], state, why)
                rep.update(state=state, reason=why)
                continue
            try:
                cands = _candidates(s, f, cfg)
            except Exception as exc:                            # noqa: BLE001
                why = f"{type(exc).__name__}: {exc}"[:200]
                vs.record_run(run_id, s["id"], s["name"], "unreachable", why)
                rep.update(state="unreachable", reason=why)
                continue
            rep["candidates"] = len(cands)
            fetched = extracted = 0
            req = [w.lower() for w in s.get("require_any") or []]
            for c in cands:
                url = c["url"]
                if not url or vs.seen(s["id"], url):
                    continue
                if c["published"] and c["published"] < lookback:
                    vs.mark_seen(s["id"], url, "old", published_at=c["published"],
                                 title=c["title"])
                    continue
                if req and c["title"] is not None:
                    blob = f"{c['title']} {c['summary']}".lower()
                    if not any(w in blob for w in req):
                        vs.mark_seen(s["id"], url, "filtered",
                                     published_at=c["published"], title=c["title"],
                                     reason="no strategist or forecast word")
                        continue
                if (fetched >= int(cfg.get("max_fetch_per_source") or 10)
                        or time.monotonic() > deadline):
                    break                     # the rest wait for tomorrow, unseen
                fetch_url = c.get("fetch_url") or url
                if not f.allowed(fetch_url):
                    vs.mark_seen(s["id"], url, "robots_disallowed", title=c["title"])
                    continue
                try:
                    page = f.get(fetch_url).decode("utf-8", "replace")
                except Exception as exc:                        # noqa: BLE001
                    rep["items"].append({"url": url, "state": "fetch_failed",
                                         "reason": str(exc)[:120]})
                    continue
                fetched += 1
                rep["new_items"] += 1
                title = c["title"] or page_title(page) or url
                pub = (c["published"] or page_date(page, url, s.get("date_pattern"))
                       or url_date(url, s.get("url_date_pattern")))
                if not pub:
                    vs.mark_seen(s["id"], url, "undated", title=title,
                                 reason="no published date on the feed or the page")
                    rep["items"].append({"url": url, "title": title, "state": "undated"})
                    continue
                if pub < lookback:
                    vs.mark_seen(s["id"], url, "old", published_at=pub, title=title)
                    continue
                # A listing's title is known only now; a source that declares
                # topic words is held to them here, before any model call. The
                # TITLE only: a page's navigation names every topic it has.
                if req and c["title"] is None and not any(
                        w in str(title).lower() for w in req):
                    vs.mark_seen(s["id"], url, "filtered", published_at=pub,
                                 title=title, reason="none of the declared topic words")
                    continue
                item = {"url": url, "title": title, "published": pub,
                        "state": "candidate"}
                rep["items"].append(item)
                if not use_model:
                    continue                  # unseen: a model run extracts it
                if used >= cap or extracted >= int(cfg.get("max_extract_per_source") or 6):
                    item["state"] = "deferred_cap"
                    continue
                text = page_text(page, int(cfg.get("max_text_chars") or 12000))
                if c["summary"] and c["summary"] not in text:
                    text = f"{c['summary']}\n\n{text}"
                try:
                    found = extract(client, model, system, title, url, pub, text)
                except Exception as exc:                        # noqa: BLE001
                    used += 1
                    rep["model_calls"] += 1
                    item["state"] = "extract_failed"
                    item["reason"] = f"{type(exc).__name__}: {exc}"[:160]
                    continue
                used += 1
                extracted += 1
                rep["model_calls"] += 1
                rep["extracted"] += 1
                retrieved = session.utc_iso()
                n_voices, touched = 0, set()
                for v in found:
                    # The model names the kind; a desk's own page supplies it
                    # only where the model returned none it may use.
                    if v.get("kind") not in (cfg.get("kinds") or {}) and \
                            s.get("default_kind"):
                        v["kind"] = s["default_kind"]
                    row, notes = clean_voice(v, cfg, text, set(stories))
                    row.update({"outlet": s["outlet"], "source_id": s["id"],
                                "source_url": url, "title": title,
                                "published_at": c.get("published_at") or pub,
                                "retrieved_at": retrieved, "tier": tier,
                                "origin": "scan", "model": model,
                                "run_id": run_id})
                    try:
                        w = vs.write(row, cfg=cfg, stories=set(stories))
                    except vmod.VoiceError as exc:
                        rep["refused"].append({"url": url, "voice": row.get("voice"),
                                               "reason": str(exc)[:200]})
                        continue
                    n_voices += int(w["inserted"])
                    touched |= {e["story"] for e in row["stories"]}
                    if notes:
                        item.setdefault("notes", []).extend(notes[:3])
                rep["voices"] += n_voices
                item["state"] = "extracted"
                item["voices"] = n_voices
                vs.mark_seen(s["id"], url, "extracted" if n_voices else "no_voice",
                             published_at=pub, title=title)
                # THE FOLD: each story the item bears on is one headline under
                # that story's declared query, attributed to the outlet.
                when = c.get("published_at") or f"{pub}T12:00:00+00:00"
                for sid in sorted(touched):
                    q = (stories.get(sid) or {}).get("story_query") or sid
                    events.append(ev_mod.Event(
                        type="headline", observed_at=when, source="voices_scan",
                        title=f"{title} - {s['outlet']}", url=url,
                        key=f"voices:{sid}:{url}",
                        payload={"query": q, "theme": (stories.get(sid) or {}).get("name"),
                                 "via": "voices_scan", "source_id": s["id"],
                                 "published_at": when}))
            vs.record_run(run_id, s["id"], s["name"], "ok", None,
                          candidates=rep["candidates"], new_items=rep["new_items"],
                          extracted=rep["extracted"], voices=rep["voices"],
                          model_calls=rep["model_calls"])
            rep["state"] = "ok"
        if events:
            with ev_mod.EventStore(db_path) as ev:
                report["headline_events"] = ev.write_many(events)
        report["model_calls_today"] = used
        report["state"] = "ok"
        if use_model:
            report["model"] = model
    return report


SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
# EDGAR's company lookup: every name a CIK has filed under, one "NAME:CIK:" line
# each. Streamed, never held whole; read only when an affiliation is unresolved.
LOOKUP_URL = "https://www.sec.gov/Archives/edgar/cik-lookup-data.txt"
FILING_URL = ("https://www.sec.gov/Archives/edgar/data/{cik}/{acc_nodash}/"
              "{acc}-index.htm")
# An affiliation that did not match is looked up again after this many days, not
# every morning: the lookup file is large, and a firm that does not file 13F under
# the expected name will not start to overnight.
RETRY_UNMATCHED_DAYS = 7


def _lookup_lines(ua: str):
    """EDGAR's company lookup, line by line, over one request."""
    req = urllib.request.Request(LOOKUP_URL, headers={"User-Agent": ua})
    with urllib.request.urlopen(req, timeout=120) as r:
        for raw in r:
            yield raw.decode("latin-1", "replace").rstrip("\r\n")


def lookup_ciks(lines, wanted: set[str]) -> dict[str, set[str]]:
    """Normalised expected name -> every CIK EDGAR lists under that name (a
    CIK's former names are listed too, which is why candidates are then held
    to the filer's CURRENT name)."""
    out: dict[str, set[str]] = {w: set() for w in wanted}
    for ln in lines:
        parts = ln.rsplit(":", 2)
        if len(parts) < 3:
            continue
        n = vmod.norm_name(parts[0])
        if n in out and parts[1].strip().isdigit():
            out[n].add(parts[1].strip().zfill(10))
    return out


def pull_13f(db_path: Optional[str] = None, *, ua: Optional[str] = None,
             getter: Optional[Callable[[str], bytes]] = None,
             lines=None, cfg: Optional[dict] = None) -> dict:
    """13F for every voice whose firm files one (ruled 4 Oct 2026).

    1. Each stored voice's affiliation (officials excluded) is mapped to the
       EDGAR name its firm is expected to file under (`filers_13f`, names only;
       otherwise the affiliation itself).
    2. The CIK is RESOLVED AT RUN TIME from EDGAR's company lookup and cached in
       voice_13f_ciks. A candidate counts only if EDGAR's current name for it
       equals the expected name; none is `unmatched`, two are `ambiguous`, and
       both are printed. No hand-typed CIK exists anywhere.
    3. For each matched CIK, its recent 13F-HR filings are stored, dated to their
       period of report. The reports print a 13F only for a matched CIK.

    Needs the EDGAR contact; dormant without it, as edgar.py is."""
    cfg = cfg or vmod.load_config()
    ua = ua or user_agent()
    if not ua:
        return {"state": "not_configured",
                "reason": "CHESTER_SEC_CONTACT is unset (EDGAR refuses an "
                          "anonymous User-Agent)"}
    get = getter or Fetcher(ua, 0.2).get
    out: dict[str, Any] = {"state": "ok", "filers": {}, "mismatches": []}
    now = session.utc_iso()
    retry_before = (dt.datetime.fromisoformat(now.replace("Z", "+00:00"))
                    - dt.timedelta(days=RETRY_UNMATCHED_DAYS)).isoformat()
    subs: dict[str, dict] = {}

    def submissions(cik: str) -> Optional[dict]:
        if cik not in subs:
            try:
                subs[cik] = json.loads(get(SUBMISSIONS_URL.format(cik=cik)))
            except Exception:                                   # noqa: BLE001
                subs[cik] = None
        return subs[cik]

    with vmod.VoicesStore(db_path) as vs:
        affs = sorted({r["affiliation"] for r in vs.rows()
                       if r["kind"] != "official"})
        cache = vs.cik_rows()
        todo = {}
        for a in affs:
            exp = vmod.expected_filer(a, cfg)
            c = cache.get(a)
            if c and c["state"] == "matched" and c["expected_name"] == exp:
                continue
            if c and c["expected_name"] == exp and c["resolved_at"] > retry_before:
                continue                      # unmatched recently; wait a week
            todo[a] = exp
        if todo:
            try:
                found = lookup_ciks(lines if lines is not None else _lookup_lines(ua),
                                    {vmod.norm_name(e) for e in todo.values()})
            except Exception as exc:                            # noqa: BLE001
                out["state"] = "lookup_unreachable"
                out["reason"] = f"{type(exc).__name__}: {exc}"[:160]
                found = None
            for a, exp in (todo.items() if found is not None else ()):
                cands = sorted(found.get(vmod.norm_name(exp)) or ())
                good = []
                for cik in cands:
                    j = submissions(cik)
                    if j and vmod.norm_name(j.get("name")) == vmod.norm_name(exp):
                        good.append((cik, j.get("name")))
                if len(good) == 1:
                    vs.set_cik(a, exp, "matched", cik=good[0][0],
                               edgar_name=good[0][1])
                elif not good:
                    names = [((subs.get(c) or {}).get("name") or "?") for c in cands]
                    why = (f"no EDGAR filer is currently named {exp!r}"
                           + (f" (listed under it formerly: {', '.join(names)})"
                              if names else ""))
                    vs.set_cik(a, exp, "unmatched", reason=why)
                    out["mismatches"].append(f"{a}: {why}")
                else:
                    why = (f"{len(good)} EDGAR filers are currently named {exp!r}: "
                           + ", ".join(c for c, _ in good))
                    vs.set_cik(a, exp, "ambiguous", reason=why)
                    out["mismatches"].append(f"{a}: {why}")
        for a, c in vs.cik_rows().items():
            if c["state"] != "matched":
                out["filers"][a] = {"state": c["state"], "reason": c["reason"]}
                continue
            j = submissions(c["cik"])
            if not j:
                out["filers"][a] = {"state": "unreachable"}
                continue
            if vmod.norm_name(j.get("name")) != vmod.norm_name(c["expected_name"]):
                # The filer renamed since it matched: unmatch it, print it.
                why = (f"EDGAR now names CIK {c['cik']} {j.get('name')!r}, not "
                       f"{c['expected_name']!r}")
                vs.set_cik(a, c["expected_name"], "unmatched", cik=c["cik"],
                           edgar_name=j.get("name"), reason=why)
                out["mismatches"].append(f"{a}: {why}")
                out["filers"][a] = {"state": "unmatched", "reason": why}
                continue
            rec = (j.get("filings") or {}).get("recent") or {}
            n = seen = 0
            for i, form in enumerate(rec.get("form") or []):
                if form not in ("13F-HR", "13F-HR/A"):
                    continue
                acc = rec["accessionNumber"][i]
                n += vs.write_13f({
                    "accession": acc, "affiliation": a, "cik": c["cik"],
                    "edgar_name": j.get("name"), "expected_name": c["expected_name"],
                    "form": form, "period_of_report": rec["reportDate"][i],
                    "filed": rec["filingDate"][i], "retrieved_at": now,
                    "source_url": FILING_URL.format(cik=int(c["cik"]),
                                                    acc_nodash=acc.replace("-", ""),
                                                    acc=acc)})
                seen += 1
                if seen >= 4:
                    break
            out["filers"][a] = {"state": "matched", "cik": c["cik"], "new": n}
    return out


def _main(argv: list[str]) -> int:
    import argparse  # noqa: PLC0415
    p = argparse.ArgumentParser(description="The daily voices scan.")
    sub = p.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("probe")
    pr.add_argument("--only", nargs="*")
    rn = sub.add_parser("run")
    rn.add_argument("--no-model", action="store_true")
    rn.add_argument("--only", nargs="*")
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    if a.cmd == "probe":
        import os  # noqa: PLC0415
        import tempfile  # noqa: PLC0415
        tmp = os.path.join(tempfile.mkdtemp(), "probe.db")
        r = run(tmp, use_model=False, only=a.only)
    else:
        r = run(use_model=not a.no_model, only=a.only)
        r13 = pull_13f()
        print(f"13F: {r13.get('state')} "
              + "; ".join(f"{k}: {v.get('state')}"
                          for k, v in (r13.get("filers") or {}).items())
              + (f" {r13.get('reason')}" if r13.get("reason") else ""))
        for m in r13.get("mismatches") or []:
            print(f"13F NAME MISMATCH -- no 13F prints for it: {m}")
    for sid, s in (r.get("sources") or {}).items():
        print(f"{sid:<26}{s.get('state', ''):<18}cand={s.get('candidates', 0):<4}"
              f"new={s.get('new_items', 0):<4}extracted={s.get('extracted', 0):<3}"
              f"voices={s.get('voices', 0):<3}{s.get('reason') or ''}")
    print(f"state={r.get('state')} model={r.get('model')} "
          f"calls_today={r.get('model_calls_today')} "
          f"headline_events={r.get('headline_events')}")
    return 0 if r.get("state") in ("ok", "not_configured") else 1


if __name__ == "__main__":                                     # pragma: no cover
    import sys
    raise SystemExit(_main(sys.argv[1:]))
