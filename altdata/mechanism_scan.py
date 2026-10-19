"""
THE EMERGING-MECHANISM SCAN (ST-15, the order's MW-5 and 2.7.7; st-t5-render,
18 Oct 2026). Weekly, deterministic first and the model second.

    python -m altdata.mechanism_scan run [--dry-run] [--force]   # Saturdays; --force any day

  1  the legs: the mechanism-watch query group over the declared public feeds
     (altdata/sources/news.py mechanism_items, config/story_queries.yaml
     `mechanism_watch`), and DefiLlama's recently-added protocols in the declared
     categories. The hashrate trackers are a listed gap (no feed or API), and
     CoinGecko's recently-added list is not read: CoinGecko is retired.
  2  dedupe: drop anything already in the Security Master (its names, aliases and
     CoinGecko ids) or the mechanism-watch register (any status: a rejected
     candidate is never surfaced again)
  3  the rule pre-filter: drop the exclusion classes by keyword (unless on the
     override list); keep only a candidate with at least one materiality-bar (iii)
     hit detectable by rule -- a tier-1 exchange named, a market cap above $50M, a
     serious outlet's domain, a hashrate tracker's -- each hit recorded
  4  THE GATE: the model is called only when at least one candidate survives
     (the Audit #3 ruling: the gate stays closed otherwise), ONCE, with at most
     `max_candidates`, through the one metered client (altdata/model_meter.py).
     Its prompt is Appendix F of the order, VERBATIM, read from the order itself
     at run time (docs/change-order-signal-triage-2026-09-25.md) -- not copied into
     code -- with the bracketed list substituted
  5  the writes, DRAFTS ONLY (rule 31): each qualifying candidate a CANDIDATE row
     at the pending grade with `draft` set, and a drafted narrative-register entry
     (<= 60 words, factor I or V). Only a human changes a status
     (altdata/mechanism_watch.py promote | reject, with the operator's flag).
  6  the posting (ruling 6 of 19 Oct 2026): each entry posted to the narrative
     register as a PROPOSED story through its existing proposal path, with its
     factor's declared implied outcome and horizon (mechanism_watch.post_entries),
     for the operator's confirm or reject. Nothing here confirms.

The whole scan is a step of the Saturday run of the crypto basket's timer
(scripts/run_crypto_basket.sh); no new timer. Watch-level rights only (MW-2).
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import re
from pathlib import Path
from typing import Any, Callable, Optional

log = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent
ORDER_PATH = REPO / "docs" / "change-order-signal-triage-2026-09-25.md"
SUBSTITUTE = "[list of name, links, pre-filter evidence]"
_MCAP = re.compile(r"\$\s?(\d+(?:\.\d+)?)\s?(billion|bn|b|million|mn|m)\b", re.I)


def config() -> dict:
    from .sources import news                                   # noqa: PLC0415
    return news.load_queries().get("mechanism_watch") or {}


def appendix_f(path: Optional[Path] = None) -> str:
    """Appendix F's prompt, verbatim: the quoted block under its heading."""
    text = Path(path or ORDER_PATH).read_text(encoding="utf-8")
    i = text.index("## Appendix F")
    j = text.find("\n## ", i + 5)
    block = text[i:j if j > 0 else len(text)]
    lines = [ln[2:] if ln.startswith("> ") else ln[1:] if ln.startswith(">") else None
             for ln in block.splitlines()]
    q = [ln for ln in lines if ln is not None]
    if not q or SUBSTITUTE not in "\n".join(q):
        raise ValueError("Appendix F's quoted prompt was not found intact")
    return "\n".join(q).strip()


# ---------------------------------------------------------------------------
# 1. The legs
# ---------------------------------------------------------------------------
def recently_added(now: str, fetch_json: Optional[Callable[[str], Any]] = None,
                   cfg: Optional[dict] = None) -> tuple[list[dict], dict]:
    """DefiLlama's protocols listed in the window, in the declared categories."""
    cfg = cfg or config()
    leg = (cfg.get("legs") or {}).get("recently_added") or {}
    if not leg:
        return [], {"state": "not declared"}
    if fetch_json is None:
        from .sources._base import http_get_json                # noqa: PLC0415

        def fetch_json(u: str) -> Any:
            return http_get_json(u, timeout=60)
    now_ts = dt.datetime.fromisoformat(now.replace("Z", "+00:00")).timestamp()
    win = int(leg.get("window_days") or 14) * 86400
    cats = set(leg.get("categories") or [])
    try:
        doc = fetch_json(leg["url"])
    except Exception as exc:                                    # noqa: BLE001
        return [], {"state": "failed", "reason": f"{type(exc).__name__}: {exc}"[:160]}
    out = []
    for p in doc or []:
        t = p.get("listedAt")
        if not t or now_ts - float(t) > win or p.get("category") not in cats:
            continue
        gid = p.get("gecko_id")
        out.append({"leg": "recently_added", "name": p.get("name"),
                    "canonical_id": f"coingecko:{gid}" if gid else f"defillama:{p.get('slug')}",
                    "category": p.get("category"), "mcap": p.get("mcap"),
                    "url": p.get("url") or f"https://defillama.com/protocol/{p.get('slug')}",
                    "text": f"{p.get('name')}: {p.get('description') or ''}"[:400],
                    "listed": dt.datetime.fromtimestamp(float(t), dt.timezone.utc)
                    .date().isoformat()})
    return out, {"state": "ok", "protocols": len(doc or []), "kept": len(out)}


def news_leg(now: str, **kw) -> tuple[list[dict], dict]:
    from .sources import news                                   # noqa: PLC0415
    items, rep = news.mechanism_items(now, **kw)
    return [{"leg": "feed", "name": None, "canonical_id": None, "url": it["url"],
             "text": it["title"], "feed": it["feed"], "query": it["query"],
             "published_at": it["published_at"]} for it in items], rep


# ---------------------------------------------------------------------------
# 2-3. Dedupe and the rule pre-filter
# ---------------------------------------------------------------------------
def known_names(register=None) -> set[str]:
    """The Security Master's names, aliases and CoinGecko ids, and the register's
    names and canonical ids, lower-cased."""
    from . import security_master as sm                         # noqa: PLC0415
    out: set[str] = set()
    for e in sm.Master().instruments:
        for x in [e.get("name"), *(e.get("aliases") or []),
                  (e.get("identifiers") or {}).get("crypto_id"),
                  ((e.get("watch") or {}).get("coingecko_id"))]:
            if x:
                out.add(str(x).strip().lower())
                if str(x).startswith("coingecko:"):
                    out.add(str(x).split(":", 1)[1].lower())
    if register is not None:
        out |= register.known()
    return {x for x in out if len(x) >= 4}


def prefilter(c: dict, known: set[str], cfg: Optional[dict] = None) -> dict:
    """{keep, why, hits}: the rule pre-filter of 2.7.7 on one candidate."""
    cfg = cfg or config()
    pf = cfg.get("prefilter") or {}
    text = f"{c.get('name') or ''} {c.get('text') or ''}"
    low = text.lower()
    names = {str(c.get("name") or "").lower(), str(c.get("canonical_id") or "").lower(),
             str(c.get("canonical_id") or "").split(":", 1)[-1].lower()} - {""}
    dup = sorted(k for k in known if k in names
                 or re.search(rf"(?<![\w-]){re.escape(k)}(?![\w-])", low))
    if dup:
        return {"keep": False, "why": f"already covered ({dup[0]})", "hits": []}
    override = {str(x).lower() for x in pf.get("override") or []}
    exc = [w for w in pf.get("exclusions") or [] if w.lower() in low]
    if exc and not (names & override):
        return {"keep": False, "why": f"an excluded class ({exc[0]})", "hits": []}
    hits = []
    hits += [f"tier-1 exchange: {x}" for x in pf.get("tier1_exchanges") or []
             if re.search(rf"\b{re.escape(x)}\b", text)]
    m = c.get("mcap")
    caps = [float(m)] if isinstance(m, (int, float)) and m else []
    for n, unit in _MCAP.findall(text):
        caps.append(float(n) * (1e9 if unit.lower() in ("billion", "bn", "b") else 1e6))
    if any(v > float(pf.get("mcap_min_usd") or 5e7) for v in caps):
        hits.append(f"market cap above ${float(pf.get('mcap_min_usd') or 5e7) / 1e6:.0f}M")
    url = str(c.get("url") or "")
    hits += [f"serious outlet: {d}" for d in pf.get("serious_outlets") or [] if d in url]
    hits += [f"hashrate tracker: {d}" for d in pf.get("hashrate_trackers") or [] if d in url]
    return {"keep": bool(hits), "why": "passed" if hits else "no materiality-bar (iii) hit",
            "hits": hits}


# ---------------------------------------------------------------------------
# 4-5. The gate, the model step, the drafts
# ---------------------------------------------------------------------------
def prompt(survivors: list[dict]) -> str:
    lines = [f"- {c.get('name') or '(name not given: the item)'} -- {c.get('text')} -- "
             f"{c.get('url')} -- pre-filter: {'; '.join(c['prefilter']['hits'])}"
             for c in survivors]
    return appendix_f().replace(SUBSTITUTE, "\n" + "\n".join(lines) + "\n")


def parse_reply(text: str) -> list[dict]:
    """The model's JSON list (Appendix F's schema); [] when it returns none."""
    t = (text or "").strip()
    m = re.search(r"\[.*\]", t, re.S)
    if not m:
        return []
    doc = json.loads(m.group(0))
    return [d for d in doc if isinstance(d, dict)]


def _entry_text(d: dict) -> str:
    words = " ".join(x for x in (f"{d.get('name')}:", d.get("whats_new"),
                                 f"({d.get('stage')})" if d.get("stage") else None,
                                 d.get("why_it_could_matter")) if x).split()
    return " ".join(words[:60])


def _factor(d: dict) -> str:
    cls = str(d.get("mechanism_class") or "").lower()
    return "I" if any(w in cls for w in ("ai", "compute", "useful work", "pouw")) else "V"


def assess(survivors: list[dict], client=None, model: Optional[str] = None) -> dict:
    """The one model call behind the gate, through the metered client."""
    from . import model_meter                                   # noqa: PLC0415
    if client is None:
        client, why = model_meter.client()
        if client is None:
            return {"state": "unavailable", "reason": why, "assessed": []}
    from daily_cascade import narrative                         # noqa: PLC0415
    model = model or narrative.DEFAULT_MODEL
    with model_meter.scope(report="mechanism_watch", section="assessment"):
        resp = model_meter.create(
            client, model=model, max_tokens=4000, system=prompt(survivors),
            messages=[{"role": "user", "content": "Return the JSON list for the "
                                                  "candidates above, and nothing else."}])
    text = "".join(getattr(b, "text", "") for b in getattr(resp, "content", []) or []
                   if getattr(b, "type", "") == "text")
    try:
        return {"state": "ok", "assessed": parse_reply(text)}
    except ValueError as exc:
        return {"state": "unparsed", "reason": str(exc)[:160], "assessed": []}


def write_drafts(register, assessed: list[dict], survivors: list[dict],
                 at: Optional[str] = None) -> dict:
    """Each qualifying assessment as a CANDIDATE draft and a drafted entry; the
    rest are listed with the criterion they failed, and written nowhere."""
    out = {"candidates": [], "entries": [], "failed": [], "refused": []}
    for d in assessed:
        if not d.get("qualifies"):
            out["failed"].append({"name": d.get("name"), "fail_reason": d.get("fail_reason")})
            continue
        pf = next((c["prefilter"] for c in survivors
                   if (c.get("name") or "").lower() == str(d.get("name") or "").lower()),
                  {"hits": [c for s in survivors for c in s["prefilter"]["hits"]][:3]})
        try:
            mid = register.add_candidate(d, origin="llm_draft", prefilter=pf, at=at,
                                         draft=True)
        except ValueError as exc:
            out["refused"].append({"name": d.get("name"), "why": str(exc)})
            continue
        out["candidates"].append(mid)
        out["entries"].append(register.add_entry(
            _entry_text(d), _factor(d), (d.get("sources") or [d.get("team_or_paper") or
                                                             "the scan"])[0], mid, at))
    return out


def run(dry_run: bool = False, today: Optional[str] = None, force: bool = False,
        now: Optional[str] = None, db_path: Optional[str] = None, client=None,
        news_kw: Optional[dict] = None, fetch_json=None) -> dict:
    """The weekly scan. Saturdays (ET) unless forced. Dry run: the legs, the
    dedupe and the pre-filter, and the prompt's size -- no model call, no write."""
    from . import mechanism_watch as mw, session                # noqa: PLC0415
    day = dt.date.fromisoformat((today or session.session_date())[:10])
    if day.weekday() != 5 and not force:
        return {"step": "mechanism_scan", "skipped": f"{day:%a} {day}: the scan runs "
                                                     f"on Saturdays"}
    now = now or session.utc_iso()
    cfg = config()
    feed, frep = news_leg(now, **(news_kw or {}))
    added, arep = recently_added(now, fetch_json, cfg)
    reg = mw.Register(db_path) if not dry_run else _readonly_or_none(mw, db_path)
    try:
        known = known_names(reg)
        cands = feed + added
        for c in cands:
            c["prefilter"] = prefilter(c, known, cfg)
        survivors = [c for c in cands if c["prefilter"]["keep"]][
            :int(cfg.get("max_candidates") or 20)]
        rep = {"step": "mechanism_scan", "dry_run": dry_run, "feeds": frep,
               "recently_added": arep,
               "hashrate_trackers": ((cfg.get("legs") or {}).get("hashrate_trackers")
                                     or {}).get("gap"),
               "candidates": len(cands), "survivors": len(survivors),
               "dropped": {}, "gate": "closed" if not survivors else "open"}
        for c in cands:
            if not c["prefilter"]["keep"]:
                w = c["prefilter"]["why"].split(" (")[0]
                rep["dropped"][w] = rep["dropped"].get(w, 0) + 1
        if not survivors:
            return rep
        if dry_run:
            rep["prompt_chars"] = len(prompt(survivors))
            rep["survivor_names"] = [c.get("name") or c.get("text")[:60] for c in survivors]
            return rep
        a = assess(survivors, client=client)
        rep["assessment"] = {k: v for k, v in a.items() if k != "assessed"}
        rep["written"] = write_drafts(reg, a.get("assessed") or [], survivors)
        rep["posted"] = mw.post_entries(reg, db_path)
        return rep
    finally:
        if reg is not None:
            reg.close()


def _readonly_or_none(mw, db_path):
    try:
        return mw.Register(db_path, readonly=True)
    except FileNotFoundError:
        return None


def _main(argv: list[str]) -> int:
    import argparse
    ap = argparse.ArgumentParser(prog="python -m altdata.mechanism_scan")
    ap.add_argument("cmd", choices=["run"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="run on any day")
    ap.add_argument("--db", default=None)
    a = ap.parse_args(argv)
    print(json.dumps(run(a.dry_run, force=a.force, db_path=a.db), indent=2, default=str))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(_main(sys.argv[1:]))
