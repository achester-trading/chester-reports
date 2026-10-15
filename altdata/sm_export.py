"""
The Security Master export, to chester-meme's contract (AUD-3b Part 2, 15 Oct
2026; chester-meme's spec section 3, ruled 11 Oct).

    python -m altdata.security_master export [--out PATH]

THE CONTRACT is docs/interface/security_master.schema.json, copied byte for byte
from chester-meme (README-interface.md beside it). chester-meme reads the file
read-only, keys every security by its composite FIGI, and its guard (R-T1a-3)
remaps two years of backfilled history row by row from `ticker_history` -- so
an exact effective_to on a reused ticker repairs its history, and a start stated
too late would wipe it (altdata/ticker_history.py: unknown starts are 1900-01-01
with from_known false).

THE FILE: schema_version "1.0", exported_at (UTC, Z), source "chester-reports",
and `securities`, one per composite FIGI that a Nasdaq Trader listing mapped to
(altdata/figi.py): figi, share_class_figi, cik (null in v1), name, type, venue,
active and ticker_history, tickers in ACT form as Nasdaq Trader prints them
(BRK.B, ABR$D, AAC.W). Two extra fields the schema allows: `restricted` (the
Brookfield complex, by register.instruments' rule over every ticker the security
has held and its name) and, on each history row, `from_known`. Indices,
futures, FX, crypto, rates and prediction contracts are not in the contract and
are not exported.

VALIDATED BEFORE IT IS WRITTEN, against the committed schema; written atomically
(.tmp, then rename). An invalid file is never written: the run says why and
exits non-zero. With no validator installed (jsonschema), nothing is written.

THE PATH: $CHESTER_SM_EXPORT, else ~/chester-data/export/security_master.json --
outside both checkouts. chester-meme reads it through its MEME_SM_EXPORT.
"""

from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
from typing import Optional

import yaml

REPO = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO / "docs" / "interface" / "security_master.schema.json"
EXCHANGES_PATH = REPO / "config" / "listing_exchanges.yaml"
DEFAULT = "~/chester-data/export/security_master.json"
VAR = "CHESTER_SM_EXPORT"

# OpenFIGI's securityType (then securityType2) -> the contract's `type`. A value
# not here is OTHER; the export's summary counts each OTHER's OpenFIGI type so a
# missing line shows up on the first full run.
BY_TYPE = {
    "common stock": "CS", "reit": "CS", "mlp": "CS", "ltd part": "CS",
    "royalty trst": "CS", "tracking stk": "CS", "stapled security": "CS",
    "adr": "ADRC", "gdr": "GDR", "ny reg shrs": "NYRS",
    "preference": "PFD", "preferred": "PFD", "pfd": "PFD",
    "warrant": "WARRANT", "right": "RIGHT", "unit": "UNIT",
    "closed-end fund": "FUND", "open-end fund": "FUND", "mutual fund": "FUND",
    "fund of funds": "FUND", "etp": "ETF", "etf": "ETF", "etn": "ETN",
}
BY_TYPE2 = {
    "common stock": "CS", "preferred stock": "PFD", "depositary receipt": "ADRC",
    "warrant": "WARRANT", "right": "RIGHT", "unit": "UNIT", "mutual fund": "FUND",
    "note": "NOTE", "corp": "NOTE", "bond": "NOTE",
}


def contract_type(st: Optional[str], st2: Optional[str], etf_flag: Optional[str]) -> str:
    t, t2 = (st or "").strip().lower(), (st2 or "").strip().lower()
    if t == "etn" or "etn" in t2:
        return "ETN"
    if etf_flag == "Y":
        return "ETF"
    return BY_TYPE.get(t) or BY_TYPE2.get(t2) or "OTHER"


def exchanges() -> dict:
    return yaml.safe_load(EXCHANGES_PATH.read_text(encoding="utf-8"))


def venue_of(code: Optional[str], ex: dict) -> Optional[str]:
    c = (ex.get("codes") or {}).get(code or "")
    return c["venue"] if c else ("OTHER" if code else None)


def _latest_rows(snaps: list[Path]) -> dict[str, dict]:
    from . import listings  # noqa: PLC0415
    return {r["symbol"]: r for r in listings.read_snapshot(snaps[-1])} if snaps else {}


def _stream(snaps: list[Path]):
    from . import listings  # noqa: PLC0415
    for p in snaps:
        yield p.stem, listings.read_snapshot(p)


def build(master, listings_dir: Optional[Path] = None, figi_dir: Optional[Path] = None,
          exported_at: Optional[str] = None) -> tuple[dict, dict]:
    """(the document, a summary). Reads only the repo's own reference data."""
    from . import figi as fg, listings, ticker_history as th  # noqa: PLC0415
    snaps = listings.snapshots(listings_dir)
    cache = fg.load_cache(figi_dir)
    assigns = th.Assignments(fg.assignments(figi_dir))
    hist = th.build(_stream(snaps), assigns, master)
    latest = _latest_rows(snaps)
    by_figi: dict[str, tuple[str, dict]] = {}
    for f, c in cache.get("figis", {}).items():
        by_figi[f] = ("", c)
    for sym, c in cache["symbols"].items():
        by_figi[c["composite_figi"]] = (sym, c)
    ex = exchanges()
    rules = master.rules
    out, other = [], {}
    for f, rows in sorted(hist.items()):
        if not rows or f not in by_figi:
            continue
        sym, c = by_figi[f]
        open_ = [r for r in rows if r["effective_to"] is None]
        cur = (open_ or rows)[-1]["ticker"]
        lrow = latest.get(cur) or latest.get(sym) or {}
        typ = contract_type(c.get("security_type"), c.get("security_type2"), lrow.get("etf"))
        if typ == "OTHER":
            k = f"{c.get('security_type')}/{c.get('security_type2')}"
            other[k] = other.get(k, 0) + 1
        name = c.get("name") or c.get("listing_name") or lrow.get("name")
        probes = [r["ticker"] for r in rows] + ([name] if name else []) + \
                 ([lrow["name"]] if lrow.get("name") else [])
        hit = next((h for h in (rules.check(x) for x in probes) if h), None)
        out.append({
            "figi": f, "share_class_figi": c.get("share_class_figi"), "cik": None,
            "name": name, "type": typ,
            # an inactive holder's last venue is not kept: null, not its successor's
            "venue": venue_of(lrow.get("exchange"), ex) if lrow and open_ else None,
            "active": bool(open_),
            "ticker_history": [{"ticker": r["ticker"], "effective_from": r["effective_from"],
                                "effective_to": r["effective_to"],
                                "from_known": r["from_known"]} for r in rows],
            "restricted": hit is not None,
        })
    doc = {"schema_version": "1.0",
           "exported_at": exported_at or dt.datetime.now(dt.timezone.utc)
           .strftime("%Y-%m-%dT%H:%M:%SZ"),
           "source": "chester-reports", "securities": out}
    summary = {"securities": len(out), "restricted": sum(s["restricted"] for s in out),
               "unknown_starts": sum(1 for s in out for r in s["ticker_history"]
                                     if not r["from_known"]),
               "snapshots": len(snaps), "unmapped": len(cache["unmapped"]),
               "other_types": other}
    return doc, summary


def validate(doc: dict) -> list[str]:
    """The schema's errors, or ["..."] when no validator is installed."""
    try:
        import jsonschema  # noqa: PLC0415
    except ImportError:
        return ["jsonschema is not installed: nothing is written "
                "(pip install -r requirements.txt)"]
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    v = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    return [f"{'/'.join(map(str, e.absolute_path)) or '(root)'}: {e.message}"
            for e in sorted(v.iter_errors(doc), key=lambda e: list(e.absolute_path))][:20]


def write(doc: dict, out: Optional[str | Path] = None) -> dict:
    """Validate, then write atomically. Never writes an invalid file."""
    errs = validate(doc)
    path = Path(os.path.expanduser(str(out or os.environ.get(VAR) or DEFAULT)))
    if errs:
        return {"written": False, "path": str(path), "errors": errs}
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)
    return {"written": True, "path": str(path)}


def export(out: Optional[str | Path] = None, master=None,
           listings_dir: Optional[Path] = None, figi_dir: Optional[Path] = None) -> dict:
    if master is None:
        from .security_master import Master  # noqa: PLC0415
        master = Master()
    doc, summary = build(master, listings_dir, figi_dir)
    return {**write(doc, out), **summary}
