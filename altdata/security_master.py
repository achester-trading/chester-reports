"""
The Security Master, v1 (AUD-3b; the audit of 14 Oct 2026, recommendation 13;
architecture Part 26.2 #6).

    python -m altdata.security_master check            # the consistency check
    python -m altdata.security_master resolve SPY --scheme yahoo [--on DATE]
    python -m altdata.security_master export [--out PATH]

config/security_master.yaml IS THE SOURCE OF TRUTH: in git, reviewed by Ari.
This module loads it and serves it. It was seeded once by
tools/seed_security_master.py from the maps the code already keeps; the call
sites keep their own maps for now, and move to the master one at a time later.
The consistency check is what holds the two together until then.

AN INSTRUMENT is: a stable internal `id` (SM + five digits, allocated in order
and never reused -- an instrument that stops trading is closed with active_to,
never deleted, and `next_id` only grows); `name`; `asset_class` (equity, etf,
index, future, option_root, fx, crypto, rate, prediction_contract); `currency`;
`multiplier`; `exchange` (its MIC where known); `identifiers` by scheme (yahoo,
store_key, ticker, occ_root, ibkr_conid, pm_id, crypto_id, overnight_slug);
`aliases`; `active_from` and `active_to`; for an option root, its `underlying`.
A fact found in neither the repo nor a stored source is null and named in the
entry's `unverified` list, never typed from memory.

TICKER REUSE. An identifier maps to an instrument only inside that instrument's
active window, so a reused ticker resolves to the right company on each date:
BAM before 9 Dec 2022 is the issuer now called BN; SPCX before 12 Jun 2026 is
not Space Exploration Technologies. resolve() returns exactly one instrument or
raises -- never the first of two.

THE RESTRICTION CANNOT BE WEAKENED HERE. `restricted` is COMPUTED at load, from
config/tracked_entities.yaml through register.instruments (normalise() and the
name patterns), over every identifier, alias and the name. A YAML line cannot
set it: a `restricted` key in the file is discarded and counted, and the gate
fails the committed file if it carries one. The register's own check and its
SQLite trigger are untouched; this is one more reader of the same rule.

THE EXPORT is one-way, for chester-meme (ruled 11 Oct): one JSON file -- a
schema version, generated_at, a content hash, the master's instruments and the
newest listings snapshot (altdata/listings.py), each with its identifiers,
asset class, currency, exchange, active window and restricted flag, so the
other repository can enforce the blocklist on its own side. Nothing in this
repository reads it back.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Optional, Union

REPO = Path(__file__).resolve().parent.parent
MASTER_PATH = REPO / "config" / "security_master.yaml"
EXPORT_DEFAULT = "~/chester-data/export/security_master.json"
EXPORT_SCHEMA = "security-master-export-v1"

ASSET_CLASSES = ("equity", "etf", "index", "future", "option_root", "fx", "crypto",
                 "rate", "prediction_contract")
SCHEMES = ("yahoo", "store_key", "ticker", "occ_root", "ibkr_conid", "pm_id",
           "crypto_id", "overnight_slug")
FIELDS = ("id", "name", "asset_class", "currency", "multiplier", "exchange",
          "identifiers", "aliases", "active_from", "active_to")

Day = Union[str, dt.date, None]


class NotFound(LookupError):
    """No instrument carries this identifier on this date."""


class Ambiguous(LookupError):
    """More than one instrument carries this identifier on this date."""


def _day(d: Day) -> str:
    if d is None:
        return dt.date.today().isoformat()
    return d.isoformat() if isinstance(d, dt.date) else str(d)[:10]


def _iso(v: Any) -> Optional[str]:
    if v is None or v == "":
        return None
    return v.isoformat() if isinstance(v, dt.date) else str(v)[:10]


class Master:
    """The loaded master. Every instrument carries a computed `restricted` and
    `restricted_by`; the file's own `restricted` key, if any, is discarded."""

    def __init__(self, path: Optional[Path] = None, restrictions=None) -> None:
        import yaml  # noqa: PLC0415
        from register.instruments import Restrictions  # noqa: PLC0415
        self.path = Path(path or MASTER_PATH)
        self.raw = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        self.rules = restrictions or Restrictions()
        self.discarded_claims: list[str] = []
        self.instruments: list[dict] = []
        for e in self.raw.get("instruments") or []:
            e = dict(e)
            if "restricted" in e or "restricted_by" in e:
                self.discarded_claims.append(str(e.get("id")))
                e.pop("restricted", None)
                e.pop("restricted_by", None)
            e["identifiers"] = {k: str(v) for k, v in (e.get("identifiers") or {}).items()
                                if v is not None and v != ""}
            e["aliases"] = [str(a) for a in e.get("aliases") or []]
            e["active_from"] = _iso(e.get("active_from"))
            e["active_to"] = _iso(e.get("active_to"))
            hit = self._restriction(e)
            e["restricted"] = hit is not None
            e["restricted_by"] = hit
            self.instruments.append(e)
        self._by_id = {e["id"]: e for e in self.instruments}

    def _restriction(self, e: dict) -> Optional[dict]:
        probes = list(e["identifiers"].values()) + e["aliases"]
        if e.get("name"):
            probes.append(str(e["name"]))
        for p in probes:
            hit = self.rules.check(p)
            if hit:
                return {"entity_id": hit.get("entity_id"), "matched_on": hit["matched_on"],
                        "root": hit.get("root"), "probe": p}
        return None

    # -- the API ---------------------------------------------------------------
    def by_id(self, sid: str) -> dict:
        if sid not in self._by_id:
            raise NotFound(sid)
        return self._by_id[sid]

    def list(self, asset_class: Optional[str] = None) -> list[dict]:
        if asset_class is not None and asset_class not in ASSET_CLASSES:
            raise ValueError(f"no asset class {asset_class!r}")
        return [e for e in self.instruments
                if asset_class is None or e["asset_class"] == asset_class]

    @staticmethod
    def active(e: dict, on: str) -> bool:
        return ((e["active_from"] is None or e["active_from"] <= on)
                and (e["active_to"] is None or on <= e["active_to"]))

    def candidates(self, identifier: str, scheme: str, on: Day = None) -> list[dict]:
        if scheme not in SCHEMES + ("alias",):
            raise ValueError(f"no identifier scheme {scheme!r}")
        day, ident = _day(on), str(identifier)
        out = []
        for e in self.instruments:
            if scheme == "alias":
                hit = ident in e["aliases"]
            else:
                hit = e["identifiers"].get(scheme) == ident
            if hit and self.active(e, day):
                out.append(e)
        return out

    def resolve(self, identifier: str, scheme: str, on: Day = None) -> dict:
        """The one instrument `identifier` names under `scheme` on `on` (today
        by default). Raises NotFound or Ambiguous; never guesses."""
        c = self.candidates(identifier, scheme, on)
        if not c:
            raise NotFound(f"{scheme}:{identifier} on {_day(on)}")
        if len(c) > 1:
            raise Ambiguous(f"{scheme}:{identifier} on {_day(on)}: "
                            f"{[e['id'] for e in c]}")
        return c[0]

    def is_restricted(self, identifier: str, scheme: Optional[str] = None,
                      on: Day = None) -> bool:
        """True if the identifier resolves to a restricted instrument -- or, with
        no scheme or nothing resolving, if the rule itself restricts the string.
        The fallback means an identifier the master does not know is judged by
        the blocklist, never waved through."""
        if scheme:
            try:
                return bool(self.resolve(identifier, scheme, on)["restricted"])
            except NotFound:
                pass
        return self.rules.is_restricted(identifier)

    # -- the consistency check ---------------------------------------------------
    def overlaps(self) -> list[str]:
        """Two entries active on the same identifier at once."""
        out = []
        seen: dict[tuple[str, str], list[dict]] = {}
        for e in self.instruments:
            for s, v in e["identifiers"].items():
                seen.setdefault((s, v), []).append(e)
        lo, hi = "0000-01-01", "9999-12-31"
        for (s, v), es in sorted(seen.items()):
            for i in range(len(es)):
                for j in range(i + 1, len(es)):
                    a, b = es[i], es[j]
                    if (max(a["active_from"] or lo, b["active_from"] or lo)
                            <= min(a["active_to"] or hi, b["active_to"] or hi)):
                        out.append(f"{s}:{v} is active on {a['id']} and {b['id']} at once")
        return out

    def structural(self) -> list[str]:
        out = []
        ids = [e.get("id") for e in self.instruments]
        if len(ids) != len(set(ids)):
            out.append("an id is used twice")
        nxt = int(self.raw.get("next_id") or 0)
        for e in self.instruments:
            sid = str(e.get("id") or "")
            if not (sid.startswith("SM") and sid[2:].isdigit() and len(sid) == 7):
                out.append(f"{sid!r}: not an SM + five digits id")
            elif int(sid[2:]) >= nxt:
                out.append(f"{sid}: at or above next_id {nxt}")
            if e.get("asset_class") not in ASSET_CLASSES:
                out.append(f"{sid}: asset_class {e.get('asset_class')!r}")
            bad = [s for s in e["identifiers"] if s not in SCHEMES]
            if bad:
                out.append(f"{sid}: unknown identifier scheme(s) {bad}")
            if not e["identifiers"]:
                out.append(f"{sid}: no identifier")
            if e["active_from"] and e["active_to"] and e["active_from"] > e["active_to"]:
                out.append(f"{sid}: active_from after active_to")
            if e.get("asset_class") == "option_root" and e.get("underlying") not in self._by_id:
                out.append(f"{sid}: option root without a known underlying")
            for f in FIELDS:
                if f not in e:
                    out.append(f"{sid}: missing field {f}")
            nulls = sorted(f for f in ("name", "currency", "multiplier", "exchange")
                           if e.get(f) is None)
            if sorted(set(nulls) - set(e.get("unverified") or [])):
                out.append(f"{sid}: null {nulls} not all listed as unverified")
        return out

    # -- the export --------------------------------------------------------------
    def export_doc(self, listings: Optional[list[dict]] = None,
                   listings_day: Optional[str] = None,
                   generated_at: Optional[str] = None) -> dict:
        inst = [{k: e.get(k) for k in FIELDS + ("underlying",)}
                | {"restricted": e["restricted"],
                   "restricted_by": (e["restricted_by"] or {}).get("entity_id")}
                for e in self.instruments]
        lst = []
        for r in listings or []:
            hit = self.rules.check(r["symbol"]) or self.rules.check(r.get("name") or "")
            lst.append({"symbol": r["symbol"], "name": r.get("name"),
                        "asset_class": "etf" if r.get("etf") == "Y" else "equity",
                        "currency": None, "exchange": r.get("exchange"),
                        "identifiers": {"ticker": r["symbol"]},
                        "active_from": None, "active_to": None,
                        "seen_on": listings_day,
                        "restricted": hit is not None,
                        "restricted_by": (hit or {}).get("entity_id")})
        body = {"instruments": inst, "listings": lst}
        return {"schema_version": EXPORT_SCHEMA,
                "generated_at": generated_at or dt.datetime.now(dt.timezone.utc)
                .isoformat(timespec="seconds"),
                "content_hash": content_hash(body),
                "master": {"path": "config/security_master.yaml",
                           "version": self.raw.get("version"),
                           "instruments": len(inst)},
                "listings_snapshot": listings_day,
                **body}


def content_hash(body: dict) -> str:
    """sha256 over the canonical JSON of {instruments, listings}: sorted keys,
    no whitespace. generated_at is outside it, so two exports of the same
    content carry the same hash."""
    canon = json.dumps({"instruments": body["instruments"], "listings": body["listings"]},
                       sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(canon.encode("utf-8")).hexdigest()


def export(out: Optional[Union[str, Path]] = None, master: Optional[Master] = None,
           listings_dir: Optional[Path] = None) -> dict:
    """Write the export, atomically. Returns {path, hash, instruments, listings}."""
    from . import listings as lst_mod                           # noqa: PLC0415
    m = master or Master()
    snaps = lst_mod.snapshots(listings_dir)
    rows = lst_mod.read_snapshot(snaps[-1]) if snaps else []
    doc = m.export_doc(rows, snaps[-1].stem if snaps else None)
    path = Path(os.path.expanduser(str(out or EXPORT_DEFAULT)))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".part")
    tmp.write_text(json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    tmp.replace(path)
    return {"path": str(path), "hash": doc["content_hash"],
            "instruments": len(doc["instruments"]), "listings": len(doc["listings"]),
            "listings_snapshot": doc["listings_snapshot"]}


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.security_master")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    r = sub.add_parser("resolve")
    r.add_argument("identifier")
    r.add_argument("--scheme", default="yahoo")
    r.add_argument("--on")
    e = sub.add_parser("export")
    e.add_argument("--out", default=EXPORT_DEFAULT)
    a = ap.parse_args(argv)
    m = Master()
    if a.cmd == "check":
        probs = m.structural() + m.overlaps()
        for p in probs:
            print(f"  {p}")
        print(f"{len(m.instruments)} instruments, {len(probs)} problem(s)")
        return 1 if probs else 0
    if a.cmd == "resolve":
        try:
            print(json.dumps(m.resolve(a.identifier, a.scheme, a.on), sort_keys=True))
        except LookupError as exc:
            print(f"{type(exc).__name__}: {exc}")
            return 1
        return 0
    print(json.dumps(export(a.out, m), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
