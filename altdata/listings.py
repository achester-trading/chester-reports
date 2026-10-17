"""
The listings layer (AUD-3b item 5): every US listing's symbol and name, by day,
for the meme scan's identity -- REFERENCE DATA, not observations.

    python -m altdata.listings pull              # the 06:45 loggers step
    python -m altdata.listings diff A.csv B.csv  # the changes between two days
    python -m altdata.listings show              # the newest snapshot's counts
    python -m altdata.listings age [--today D]   # the newest snapshot's age, in
                                                 # sessions (the 08:30 heartbeat)

THE SOURCE. Nasdaq Trader's public symbol directories, the two files the
exchange publishes for the whole US market each day:

  nasdaqlisted.txt   Symbol|Security Name|Market Category|Test Issue|
                     Financial Status|Round Lot Size|ETF|NextShares
  otherlisted.txt    ACT Symbol|Security Name|Exchange|CQS Symbol|ETF|
                     Round Lot Size|Test Issue|NASDAQ Symbol

Pipe-delimited, one header line, and a last line "File Creation Time: ..."
that proves the file arrived whole. A file without that line is refused, so a
truncated download can never read as a day of delistings. TEST ISSUES ARE
DROPPED (Test Issue = Y): they are the exchanges' test symbols, not listings.

WHAT IS KEPT, AND WHERE. One CSV per day, data/reference/listings/YYYY-MM-DD.csv
(the ET date of the pull; $CHESTER_LISTINGS_DIR overrides the directory for the
gate): symbol, name, exchange (the file's code as published: Q for a Nasdaq
listing, else otherlisted's Exchange), market_category, etf, source, and the
file's creation time. Reference data, so NO registry key is added and nothing
here enters the observation store: a listing is a fact about identity on a
day, not a measurement with an availability clock.

THE CHANGES. Two consecutive snapshots give the day's changes, written to
data/reference/listings/changes/YYYY-MM-DD.csv (the newer day):

  added      a symbol in the newer snapshot only
  removed    a symbol in the older snapshot only
  renamed    the same symbol under a different name -- a REUSE CANDIDATE, the
             case the Security Master's active windows exist for

Changes are only ever written to the change file. Nothing here edits
config/security_master.yaml: a reuse is ruled by a human reading the change
file, never applied by a script. A day whose removals exceed REMOVAL_SUSPECT of
the older snapshot is marked suspect in the summary, because a vendor-side
outage looks exactly like a mass delisting.

THE FETCH obeys robots.txt (aaii.robots_verdict, the wildcard-aware reader) and
names itself as chester-reports. A refusal, a failed fetch or a truncated file
writes nothing and is reported; the step never raises past its own boundary.
"""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path
from typing import Callable, Optional

REPO = Path(__file__).resolve().parent.parent
DIR_VAR = "CHESTER_LISTINGS_DIR"
DEFAULT_DIR = REPO / "data" / "reference" / "listings"

BASE = "https://www.nasdaqtrader.com/dynamic/SymDir/"
FILES = ("nasdaqlisted.txt", "otherlisted.txt")
ROBOTS_URL = "https://www.nasdaqtrader.com/robots.txt"
USER_AGENT = "chester-reports/1.0 (reference data; no trading)"
FOOTER = "File Creation Time:"
COLUMNS = ("symbol", "name", "exchange", "market_category", "etf", "source",
           "file_created")
CHANGE_COLUMNS = ("change", "symbol", "old_name", "new_name", "exchange",
                  "previous", "snapshot", "reuse_candidate")
REMOVAL_SUSPECT = 0.05
MIN_ROWS = 1000                 # a real day has thousands; the gate passes its own


class ListingsError(ValueError):
    """A directory file that cannot be read as a whole day."""


def listings_dir() -> Path:
    return Path(os.environ.get(DIR_VAR) or DEFAULT_DIR).expanduser()


def parse(text: str, source: str) -> tuple[list[dict], str]:
    """(rows, the file's creation time) from one directory file. Raises
    ListingsError on a missing header field or a missing footer."""
    lines = [ln.rstrip("\r") for ln in text.splitlines() if ln.strip()]
    if not lines:
        raise ListingsError(f"{source}: empty")
    if not lines[-1].startswith(FOOTER):
        raise ListingsError(f"{source}: no '{FOOTER}' line -- truncated or not the file")
    created = lines[-1][len(FOOTER):].split("|", 1)[0].strip()
    head = lines[0].split("|")
    nasdaq = source == "nasdaqlisted.txt"
    sym_col = "Symbol" if nasdaq else "ACT Symbol"
    need = [sym_col, "Security Name", "Test Issue", "ETF"] + ([] if nasdaq else ["Exchange"])
    missing = [c for c in need if c not in head]
    if missing:
        raise ListingsError(f"{source}: header lacks {missing}")
    ix = {c: head.index(c) for c in head}
    out = []
    for ln in lines[1:-1]:
        f = ln.split("|")
        if len(f) < len(head):
            raise ListingsError(f"{source}: a short line: {ln[:60]!r}")
        sym = f[ix[sym_col]].strip()
        if not sym or f[ix["Test Issue"]].strip().upper() == "Y":
            continue
        out.append({
            "symbol": sym, "name": f[ix["Security Name"]].strip(),
            "exchange": "Q" if nasdaq else f[ix["Exchange"]].strip(),
            "market_category": f[ix["Market Category"]].strip() if nasdaq else "",
            "etf": "Y" if f[ix["ETF"]].strip().upper() == "Y" else "N",
            "source": source, "file_created": created})
    return out, created


def merge(parts: list[list[dict]]) -> list[dict]:
    """One row per symbol, sorted; a symbol in both files keeps its first."""
    seen: dict[str, dict] = {}
    for rows in parts:
        for r in rows:
            seen.setdefault(r["symbol"], r)
    return [seen[k] for k in sorted(seen)]


def write_csv(path: Path, columns: tuple, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".part")
    with tmp.open("w", encoding="utf-8", newline="") as fp:
        w = csv.DictWriter(fp, fieldnames=list(columns), lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in columns})
    tmp.replace(path)


def read_snapshot(path: Path) -> list[dict]:
    with Path(path).open(encoding="utf-8", newline="") as fp:
        return list(csv.DictReader(fp))


def snapshots(d: Optional[Path] = None) -> list[Path]:
    """The day files, oldest first (YYYY-MM-DD.csv only)."""
    d = d or listings_dir()
    if not d.is_dir():
        return []
    return sorted(p for p in d.glob("????-??-??.csv"))


# THE HEARTBEAT'S RULE (stitching, week of 19 Oct; meeting c): the newest
# snapshot may be at most this many SESSIONS old, counted by the session calendar
# from the snapshot's day (exclusive) to today (inclusive) -- so a weekend or a
# holiday is never a miss, and one failed 06:45 pull is not yet a warning.
MAX_AGE_SESSIONS = 2


def age(today: Optional[str] = None, d: Optional[Path] = None) -> dict:
    """{"state": "fresh" | "stale" | "none", "newest", "sessions", "allowed"}."""
    from . import derived, session                              # noqa: PLC0415
    today = (today or session.session_date())[:10]
    snaps = snapshots(d)
    if not snaps:
        return {"state": "none", "newest": None, "sessions": None,
                "allowed": MAX_AGE_SESSIONS, "dir": str(d or listings_dir())}
    newest = snaps[-1].stem
    n, basis = derived.sessions_between(newest, today)
    return {"state": "stale" if n > MAX_AGE_SESSIONS else "fresh", "newest": newest,
            "sessions": n, "basis": basis, "allowed": MAX_AGE_SESSIONS,
            "dir": str(d or listings_dir())}


def diff(prev: list[dict], cur: list[dict], prev_day: str = "",
         day: str = "") -> list[dict]:
    a = {r["symbol"]: r for r in prev}
    b = {r["symbol"]: r for r in cur}
    out = []
    for s in sorted(set(a) | set(b)):
        if s not in a:
            out.append({"change": "added", "symbol": s, "old_name": "",
                        "new_name": b[s]["name"], "exchange": b[s]["exchange"]})
        elif s not in b:
            out.append({"change": "removed", "symbol": s, "old_name": a[s]["name"],
                        "new_name": "", "exchange": a[s]["exchange"]})
        elif a[s]["name"] != b[s]["name"]:
            out.append({"change": "renamed", "symbol": s, "old_name": a[s]["name"],
                        "new_name": b[s]["name"], "exchange": b[s]["exchange"]})
    for c in out:
        c.update(previous=prev_day, snapshot=day,
                 reuse_candidate="Y" if c["change"] == "renamed" else "N")
    return out


def write_changes(d: Path, day: str) -> dict:
    """The change file for `day` against the snapshot before it."""
    days = [p.stem for p in snapshots(d)]
    if day not in days:
        return {"changes": None, "why": f"no snapshot for {day}"}
    i = days.index(day)
    if i == 0:
        return {"changes": None, "why": "the first snapshot: nothing to compare"}
    prev = read_snapshot(d / f"{days[i - 1]}.csv")
    cur = read_snapshot(d / f"{day}.csv")
    ch = diff(prev, cur, days[i - 1], day)
    write_csv(d / "changes" / f"{day}.csv", CHANGE_COLUMNS, ch)
    removed = sum(1 for c in ch if c["change"] == "removed")
    counts = {k: sum(1 for c in ch if c["change"] == k)
              for k in ("added", "removed", "renamed")}
    return {"changes": counts, "previous": days[i - 1],
            "suspect": bool(prev) and removed > REMOVAL_SUSPECT * len(prev)}


def _get(url: str) -> str:
    import requests  # noqa: PLC0415
    r = requests.get(url, timeout=30, headers={"User-Agent": USER_AGENT})
    if url == ROBOTS_URL and 400 <= r.status_code < 500:
        return ""                    # no robots.txt: no rules (RFC 9309, 2.3.1.3)
    r.raise_for_status()
    return r.text


def pull(d: Optional[Path] = None, get: Optional[Callable[[str], str]] = None,
         day: Optional[str] = None, min_rows: int = MIN_ROWS) -> dict:
    """Fetch both files, write the day's snapshot and its change file. Never
    raises: every failure is a summary with nothing written."""
    from altdata import session                                 # noqa: PLC0415
    from altdata.sources.aaii import robots_verdict             # noqa: PLC0415
    d = d or listings_dir()
    get = get or _get
    day = day or session.session_date()
    try:
        ok, rule = robots_verdict(get(ROBOTS_URL), BASE + FILES[0], "chester-reports")
    except Exception as exc:                                    # noqa: BLE001
        return {"written": 0, "error": f"robots.txt unreadable: {exc}"}
    if not ok:
        return {"written": 0, "error": f"robots.txt refuses it ({rule})"}
    parts = []
    try:
        for name in FILES:
            rows, _ = parse(get(BASE + name), name)
            parts.append(rows)
    except Exception as exc:                                    # noqa: BLE001
        return {"written": 0, "error": f"{type(exc).__name__}: {exc}"}
    rows = merge(parts)
    if len(rows) < min_rows:
        return {"written": 0, "error": f"{len(rows)} listings, under {min_rows}: refused"}
    write_csv(d / f"{day}.csv", COLUMNS, rows)
    out = {"written": len(rows), "snapshot": str(d / f"{day}.csv"),
           "etfs": sum(r["etf"] == "Y" for r in rows)}
    out.update(write_changes(d, day))
    return out


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    import json                                                 # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.listings")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("pull")
    dp = sub.add_parser("diff")
    dp.add_argument("older")
    dp.add_argument("newer")
    sub.add_parser("show")
    ag = sub.add_parser("age")
    ag.add_argument("--today", default=None)
    a = ap.parse_args(argv)
    if a.cmd == "age":
        # Exit 3 on a fault, never 1: the heartbeat reads 1 as stale.
        try:
            r = age(a.today)
        except Exception as exc:                                # noqa: BLE001
            print(f"listings: age not computed ({type(exc).__name__}: {exc})")
            return 3
        if r["state"] == "none":
            print(f"listings: no snapshot under {r['dir']}")
            return 2
        print(f"listings: newest snapshot {r['newest']}, {r['sessions']} session(s) "
              f"old (allowed {r['allowed']}) -- {r['state']}")
        return 0 if r["state"] == "fresh" else 1
    if a.cmd == "pull":
        r = pull()
        print(json.dumps(r, sort_keys=True))
        return 1 if r.get("error") else 0
    if a.cmd == "diff":
        ch = diff(read_snapshot(Path(a.older)), read_snapshot(Path(a.newer)),
                  Path(a.older).stem, Path(a.newer).stem)
        w = csv.DictWriter(sys.stdout, fieldnames=list(CHANGE_COLUMNS), lineterminator="\n")
        w.writeheader()
        w.writerows(ch)
        return 0
    snaps = snapshots()
    if not snaps:
        print(f"no snapshot under {listings_dir()}")
        return 1
    rows = read_snapshot(snaps[-1])
    print(f"{snaps[-1].name}: {len(rows)} listings, "
          f"{sum(r['etf'] == 'Y' for r in rows)} ETFs")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))

