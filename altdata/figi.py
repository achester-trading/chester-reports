"""
FIGIs for the US listings, from OpenFIGI (AUD-3b Part 2, 15 Oct 2026).

    python -m altdata.figi map            # the morning step: new, renamed, unmapped
    python -m altdata.figi map --all      # the first full mapping (a box command)
    python -m altdata.figi show

chester-meme keys every security by its COMPOSITE FIGI (its spec section 3), so
the Security Master export carries one for every US listing it exports. This
module maps each listing in the newest Nasdaq Trader snapshot (altdata/listings.py)
through OpenFIGI's mapping API -- ticker in OpenFIGI's form, exchange code US --
and keeps, per ACT symbol, the composite FIGI, the share-class FIGI, the security
type and the name, in a cache under data/reference/figi/ ($CHESTER_FIGI_DIR for
the gate):

  cache.json        {"symbols": {ACT: {...}}, "unmapped": {ACT: {...}},
                     "figis": {composite FIGI: {...}}} -- `figis` is never pruned,
                    so a holder that lost its ticker still exports its history
  assignments.csv   date,symbol,figi -- one line each time a symbol is mapped to a
                    FIGI it did not hold before. The ticker history
                    (altdata/ticker_history.py) reads it to tell a ticker change
                    and a reuse apart; it is append-only.

A SYMBOL OPENFIGI CANNOT MAP IS LISTED, NEVER GUESSED: no data, a warning, an
error, or more than one composite FIGI for the ticker on US -- each goes to
`unmapped` with the reason, is retried after RETRY_DAYS, and is never exported.

THE LIMITS. OPENFIGI_API_KEY in .env is optional (altdata.secrets; never
printed). Without it the mapper keeps to the keyless limits: 25 requests a
minute, 10 jobs a request. With it: 25 requests per 6 seconds, 100 jobs a
request. A 429 waits the server's reset and retries. The morning step maps only
symbols that are new, renamed or not yet mapped, capped at MORNING_REQUESTS
requests so it fits the 06:45 job; the rest wait for the next morning. The first
full mapping (about 13,000 listings, about 55 minutes keyless) is printed for Ari.

THE TICKER FORM. Nasdaq Trader prints ACT symbols (BRK.B, ABR$D, AAC.W); OpenFIGI
takes Bloomberg's (BRK/B, ABR/PD, AAC/WS). to_openfigi() converts, and the first
full mapping's unmapped list is the test of the conversion.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import os
import sys
import time
from pathlib import Path
from typing import Callable, Optional

REPO = Path(__file__).resolve().parent.parent
DIR_VAR = "CHESTER_FIGI_DIR"
DEFAULT_DIR = REPO / "data" / "reference" / "figi"
URL = "https://api.openfigi.com/v3/mapping"
KEY_NAME = "OPENFIGI_API_KEY"
KEYLESS = {"per_window": 25, "window_s": 60.0, "jobs": 10}
KEYED = {"per_window": 25, "window_s": 6.0, "jobs": 100}
MORNING_REQUESTS = 50
RETRY_DAYS = 7
FIELDS = ("composite_figi", "share_class_figi", "security_type", "security_type2",
          "name", "mapped_on", "listing_name")


def figi_dir() -> Path:
    return Path(os.environ.get(DIR_VAR) or DEFAULT_DIR).expanduser()


def to_openfigi(act: str) -> str:
    """ACT form -> OpenFIGI's ticker form."""
    s = act.strip().upper()
    if "$" in s:                                   # ABR$D -> ABR/PD ; ABR$ -> ABR/P
        root, _, series = s.partition("$")
        return f"{root}/P{series}"
    if s.endswith(".W"):                           # AAC.W -> AAC/WS
        return s[:-2] + "/WS"
    return s.replace(".", "/")                     # BRK.B -> BRK/B ; AAC.U -> AAC/U


def pick(result: dict) -> tuple[Optional[dict], Optional[str]]:
    """(the one composite listing, or None with the reason) from one job's result."""
    if "error" in result:
        return None, f"error: {result['error']}"
    data = result.get("data") or []
    if not data:
        return None, result.get("warning") or "no identifier found"
    us = [d for d in data if d.get("exchCode") == "US"] or data
    comps = {d.get("compositeFIGI") for d in us if d.get("compositeFIGI")}
    if len(comps) != 1:
        return None, (f"{len(comps)} composite FIGIs for the ticker on US"
                      if comps else "no composite FIGI in the result")
    d = next(x for x in us if x.get("compositeFIGI"))
    return d, None


def load_cache(d: Optional[Path] = None) -> dict:
    p = (d or figi_dir()) / "cache.json"
    if not p.is_file():
        return {"symbols": {}, "unmapped": {}, "figis": {}}
    c = json.loads(p.read_text(encoding="utf-8"))
    for k in ("symbols", "unmapped", "figis"):
        c.setdefault(k, {})
    return c


def save_cache(c: dict, d: Optional[Path] = None) -> None:
    d = d or figi_dir()
    d.mkdir(parents=True, exist_ok=True)
    tmp = d / "cache.json.tmp"
    tmp.write_text(json.dumps(c, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(d / "cache.json")


def assignments(d: Optional[Path] = None) -> list[dict]:
    p = (d or figi_dir()) / "assignments.csv"
    if not p.is_file():
        return []
    with p.open(encoding="utf-8", newline="") as fp:
        return list(csv.DictReader(fp))


def _assign(d: Path, rows: list[tuple[str, str, str]]) -> None:
    if not rows:
        return
    d.mkdir(parents=True, exist_ok=True)
    p = d / "assignments.csv"
    new = not p.is_file()
    with p.open("a", encoding="utf-8", newline="") as fp:
        w = csv.writer(fp, lineterminator="\n")
        if new:
            w.writerow(["date", "symbol", "figi"])
        w.writerows(rows)


def due(rows: list[dict], cache: dict, changes: Optional[list[dict]] = None,
        day: str = "", full: bool = False) -> list[dict]:
    """The listings to map: everything with --all; else new, renamed today, or
    unmapped and RETRY_DAYS old."""
    if full:
        return list(rows)
    renamed = {c["symbol"] for c in changes or [] if c.get("change") == "renamed"}
    out = []
    for r in rows:
        s = r["symbol"]
        if s in renamed:
            out.append(r)
        elif s in cache["unmapped"]:
            tried = cache["unmapped"][s].get("tried_on") or ""
            if not day or not tried or (dt.date.fromisoformat(day)
                                        - dt.date.fromisoformat(tried)).days >= RETRY_DAYS:
                out.append(r)
        elif s not in cache["symbols"]:
            out.append(r)
    return out


def _post(jobs: list[dict], key: Optional[str]):
    import requests  # noqa: PLC0415
    h = {"Content-Type": "application/json"}
    if key:
        h["X-OPENFIGI-APIKEY"] = key
    r = requests.post(URL, json=jobs, headers=h, timeout=60)
    if r.status_code == 429:
        return 429, None, float(r.headers.get("ratelimit-reset") or 60)
    r.raise_for_status()
    return r.status_code, r.json(), 0.0


def map_rows(rows: list[dict], day: str, d: Optional[Path] = None,
             post: Optional[Callable] = None, key: Optional[str] = None,
             max_requests: Optional[int] = None,
             sleep: Callable[[float], None] = time.sleep,
             clock: Callable[[], float] = time.monotonic) -> dict:
    """Map `rows` (listing rows) and update the cache. Returns a summary."""
    d = d or figi_dir()
    post = post or _post
    lim = KEYED if key else KEYLESS
    gap = lim["window_s"] / lim["per_window"]
    cache = load_cache(d)
    batches = [rows[i:i + lim["jobs"]] for i in range(0, len(rows), lim["jobs"])]
    if max_requests is not None:
        batches = batches[:max_requests]
    mapped = unmapped = requests_ = 0
    new_assign: list[tuple[str, str, str]] = []
    last = None
    for b in batches:
        jobs = [{"idType": "TICKER", "idValue": to_openfigi(r["symbol"]), "exchCode": "US"}
                for r in b]
        for _attempt in range(5):
            if last is not None:
                wait = gap - (clock() - last)
                if wait > 0:
                    sleep(wait)
            last = clock()
            requests_ += 1
            status, body, reset = post(jobs, key)
            if status == 429:
                sleep(reset)
                continue
            break
        else:
            break                                    # the server kept refusing: stop here
        for r, res in zip(b, body or []):
            s = r["symbol"]
            hit, why = pick(res)
            if hit is None:
                cache["unmapped"][s] = {"why": why, "tried_on": day,
                                        "openfigi_ticker": to_openfigi(s)}
                cache["symbols"].pop(s, None)      # a stale mapping is never exported
                unmapped += 1
                continue
            prev = cache["symbols"].get(s, {}).get("composite_figi")
            cache["symbols"][s] = {
                "composite_figi": hit["compositeFIGI"],
                "share_class_figi": hit.get("shareClassFIGI"),
                "security_type": hit.get("securityType"),
                "security_type2": hit.get("securityType2"),
                "name": hit.get("name"), "mapped_on": day,
                "listing_name": r.get("name")}
            cache["unmapped"].pop(s, None)
            cache["figis"][hit["compositeFIGI"]] = {
                k: v for k, v in cache["symbols"][s].items() if k != "mapped_on"}
            if prev != hit["compositeFIGI"]:
                new_assign.append((day, s, hit["compositeFIGI"]))
            mapped += 1
    save_cache(cache, d)
    _assign(d, new_assign)
    return {"due": len(rows), "requests": requests_, "mapped": mapped,
            "unmapped": unmapped, "left": max(0, len(rows) - sum(len(b) for b in batches)),
            "keyed": bool(key)}


def run(day: Optional[str] = None, full: bool = False, d: Optional[Path] = None,
        listings_dir: Optional[Path] = None, post: Optional[Callable] = None,
        key: Optional[str] = None, **kw) -> dict:
    """The morning step (or --all): map the newest snapshot's due listings."""
    from . import listings as lst  # noqa: PLC0415
    snaps = lst.snapshots(listings_dir)
    if not snaps:
        return {"due": 0, "error": "no listings snapshot"}
    day = day or snaps[-1].stem
    rows = lst.read_snapshot(snaps[-1])
    chg = (listings_dir or lst.listings_dir()) / "changes" / f"{snaps[-1].stem}.csv"
    changes = lst.read_snapshot(chg) if chg.is_file() else []
    if key is None and post is None:
        from . import secrets  # noqa: PLC0415
        key = secrets.get(KEY_NAME)
    todo = due(rows, load_cache(d), changes, day, full)
    out = map_rows(todo, day, d, post=post, key=key,
                   max_requests=None if full else kw.get("max_requests", MORNING_REQUESTS),
                   **{k: v for k, v in kw.items() if k != "max_requests"})
    return {**out, "snapshot": snaps[-1].stem}


def _main(argv: list[str]) -> int:
    import argparse  # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.figi")
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("map")
    m.add_argument("--all", action="store_true")
    sub.add_parser("show")
    a = ap.parse_args(argv)
    if a.cmd == "map":
        r = run(full=a.all)
        print(json.dumps(r, sort_keys=True))
        return 1 if r.get("error") else 0
    c = load_cache()
    print(f"{len(c['symbols'])} mapped, {len(c['unmapped'])} unmapped")
    for s, u in sorted(c["unmapped"].items())[:50]:
        print(f"  {s}: {u['why']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
