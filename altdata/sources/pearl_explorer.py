"""
Pearl's explorer -- the `pearl.chain_*` family (ST-13, signal-triage Tranche 5,
MW-4 and G-26; st-t5-prl, 18 Oct 2026).

    python -m altdata.sources.pearl_explorer --dry-run   # read and parse; write nothing
    python -m altdata.sources.pearl_explorer             # one pull

explorer.pearlresearch.ai. Three legs, in order (MW-4):

  1. the JSON endpoint, where one is declared in config/prl.yaml `explorer.
     json_endpoint` (its URL and the JSON path of each field);
  2. the block page, where `explorer.block_page` is declared (its URL and the
     regex of each field);
  3. neither read: NOTHING IS STORED, and the derived layer (altdata/prl.py)
     prints the height and supply ESTIMATED from the emission formula, stepped
     at the 194 s target -- never a blank.

Each of legs 1 and 2 is read only where robots.txt allows its path (the REP's
reading with wildcards, altdata/sources/aaii.robots_verdict) and the site's terms
allow it.

THE ENDPOINT IS NOT YET DISCOVERED (G-26). On 18 Oct 2026 neither
explorer.pearlresearch.ai nor pearlresearch.ai answered from the session's
machine (the TLS connection closed on /robots.txt; later connections refused), so
no robots.txt or terms line could be read and no endpoint is declared. When one
is found, its URL goes in config/prl.yaml and its robots and terms line here:

    robots:  (not read: unreachable 18 Oct 2026)
    terms:   (not read: unreachable 18 Oct 2026)
    endpoint: (none declared)

    pearl.chain_height       the chain-tip height              count
    pearl.chain_difficulty   the tip's difficulty              ratio
    pearl.chain_supply       the supply the explorer reports   count (PRL)

Point in time: observed_at is the UTC day of the tip's time (else of the read),
available_at the pull instant. Observed values only: an estimate is never stored
here (it is calc.prl_height_estimated, the derived layer's).
"""

from __future__ import annotations

import logging
import re
from typing import Any, Callable, Optional

from . import _crypto as C

log = logging.getLogger(__name__)

SOURCE = "pearl_explorer"
KEYS = ["pearl.chain_height", "pearl.chain_difficulty", "pearl.chain_supply"]
NOT_DECLARED = ("no explorer endpoint is declared (G-26: not yet discovered); the "
                "derived layer prints ESTIMATED from the emission formula")


def _cfg() -> dict:
    from .. import prl                                          # noqa: PLC0415
    return prl.config()["explorer"]


def _text(url: str) -> str:
    from ._base import http_get_text                            # noqa: PLC0415
    return http_get_text(url, timeout=30, headers={"User-Agent": _cfg()["user_agent"]})


def robots_ok(path: str, get: Callable[[str], str] = _text) -> tuple[bool, str]:
    """(allowed, why): `path` under the explorer's robots.txt. An unreadable
    robots.txt is not permission: the leg is skipped."""
    from .aaii import robots_verdict                            # noqa: PLC0415
    try:
        text = get(_cfg()["robots"])
    except Exception as exc:                                    # noqa: BLE001
        if "HTTP 4" in str(exc):
            text = ""                       # a 4xx robots.txt is no rules (RFC 9309)
        else:
            return False, f"robots.txt unreadable ({type(exc).__name__})"
    ok, rule = robots_verdict(text, path, "chester-reports")
    return ok, "" if ok else f"robots.txt refuses {path} ({rule})"


def _path(doc: Any, dotted: Optional[str]) -> Any:
    if not dotted:
        return None
    for part in str(dotted).split("."):
        if isinstance(doc, list):
            try:
                doc = doc[int(part)]
            except (ValueError, IndexError):
                return None
        elif isinstance(doc, dict):
            doc = doc.get(part)
        else:
            return None
    return doc


def parse_json(doc: Any, spec: dict, now: str) -> list[dict]:
    """The declared fields of a JSON response -> rows. A field the response lacks
    is left out, never zero."""
    t = _path(doc, spec.get("time"))
    day = C.utc_day(t) if isinstance(t, (int, float)) else (str(t)[:10] if t else now[:10])
    out = []
    for key, field in (("pearl.chain_height", "height"),
                       ("pearl.chain_difficulty", "difficulty"),
                       ("pearl.chain_supply", "supply")):
        v = C.num(_path(doc, spec.get(field)))
        if v is not None:
            out.append(C.row(key, day, v, now, SOURCE))
    return out


def parse_page(html: str, spec: dict, now: str) -> list[dict]:
    """The block page's declared regexes -> rows (the second leg)."""
    out = []
    for key, field in (("pearl.chain_height", "height_regex"),
                       ("pearl.chain_difficulty", "difficulty_regex"),
                       ("pearl.chain_supply", "supply_regex")):
        rx = spec.get(field)
        m = re.search(rx, html or "") if rx else None
        v = C.num(m.group(1).replace(",", "")) if m else None
        if v is not None:
            out.append(C.row(key, now[:10], v, now, f"{SOURCE}:page"))
    return out


def collect(get_json: Optional[Callable[[str], Any]] = None,
            get_text: Callable[[str], str] = _text, now: Optional[str] = None,
            cfg: Optional[dict] = None) -> dict:
    """{rows, leg, reason}: the first leg that reads, else none."""
    import json                                                 # noqa: PLC0415
    from urllib.parse import urlparse                           # noqa: PLC0415
    now = now or C.now_iso()
    c = cfg or _cfg()
    tried = []
    js = c.get("json_endpoint")
    if js:
        ok, why = robots_ok(urlparse(js["url"]).path or "/", get_text)
        if ok:
            doc = (get_json or (lambda u: json.loads(get_text(u))))(js["url"])
            rows = parse_json(doc, js, now)
            if rows:
                return {"rows": rows, "leg": "json", "reason": None}
            tried.append("the JSON endpoint parsed to nothing")
        else:
            tried.append(why)
    bp = c.get("block_page")
    if bp:
        ok, why = robots_ok(urlparse(bp["url"]).path or "/", get_text)
        if ok:
            rows = parse_page(get_text(bp["url"]), bp, now)
            if rows:
                return {"rows": rows, "leg": "page", "reason": None}
            tried.append("the block page parsed to nothing")
        else:
            tried.append(why)
    return {"rows": [], "leg": None,
            "reason": "; ".join(tried) if tried else NOT_DECLARED}


def pull(dry_run: bool = False, run_id: Optional[str] = None, db=None, **kw) -> dict:
    try:
        got = collect(**kw)
    except Exception as exc:                                    # noqa: BLE001
        got = {"rows": [], "leg": None, "reason": f"{type(exc).__name__}: {exc}"}
    if dry_run or not got["rows"]:
        return {"source": SOURCE, "written": 0, "leg": got["leg"], "rows": len(got["rows"]),
                "state": "dry_run" if dry_run else "estimated",
                "reason": got["reason"], "preview": got["rows"]}
    from . import _publication as pub                           # noqa: PLC0415
    res = pub.run(SOURCE, KEYS, lambda: got["rows"], run_id=run_id, db=db)
    res["leg"] = got["leg"]
    return res


if __name__ == "__main__":
    import argparse
    import json
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    ap = argparse.ArgumentParser(prog="python -m altdata.sources.pearl_explorer")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(sys.argv[1:])
    print(json.dumps(pull(dry_run=a.dry_run), indent=2, sort_keys=True, default=str))
