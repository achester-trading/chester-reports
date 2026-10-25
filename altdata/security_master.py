"""
The Security Master, v1 (AUD-3b; the audit of 14 Oct 2026, recommendation 13;
architecture Part 26.2 #6).

    python -m altdata.security_master check            # the consistency check
    python -m altdata.security_master resolve SPY --scheme yahoo [--on DATE]
    python -m altdata.security_master export [--out PATH]   # chester-meme's contract
    python -m altdata.security_master draft-box [--store PATH]  # box: print YAML

config/security_master.yaml IS THE SOURCE OF TRUTH: in git, reviewed by the operator.
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
entry's `unverified` list, never typed from memory. An entry may carry its own
`ticker_history` ([{ticker, from, to}], inclusive dates) when one security has
traded under more than one ticker (BN was BAM before 9 Dec 2022); an entry
folded into another carries `merged_into` and resolves to nothing, its id kept.

THE CURRENCY RULE (ruled 15 Oct 2026): a listing in Nasdaq Trader's symbol
directories trades on a US exchange in USD. An entry found in those files
carries currency USD and the MIC of its listing exchange
(config/listing_exchanges.yaml), with the snapshot it was read from.

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

THE EXPORT is one-way, to chester-meme's contract (its spec section 3;
docs/interface/security_master.schema.json, copied byte for byte): one security
per composite FIGI, with its ticker history. altdata/sm_export.py builds and
validates it. Nothing in this repository reads it back.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any, Optional, Union

REPO = Path(__file__).resolve().parent.parent
MASTER_PATH = REPO / "config" / "security_master.yaml"
EXPORT_DEFAULT = "~/chester-data/export/security_master.json"
EXPORT_VAR = "CHESTER_SM_EXPORT"

ASSET_CLASSES = ("equity", "etf", "index", "future", "option_root", "fx", "crypto",
                 "rate", "prediction_contract", "preferred", "note", "closed_end_fund",
                 "crypto.watch")
# THE crypto.watch CLASS (ST-13, MW-1; G-24 settled by AUD-3b: the class lives in
# this instrument model, not a separate table). A watch instrument is keyed by its
# CoinGecko id (identifiers.crypto_id = "coingecko:<id>"), carries the MW-1
# disambiguation fields under `watch`, and is NEVER keyed by a ticker: several
# unrelated projects share PRL's. It has no FIGI, so the export to chester-meme
# (US-listed with a FIGI only) never carries it.
WATCH_FIELDS = ("coingecko_id", "name", "issuer", "chain", "explorer", "mechanism_class")
# The bare ticker is the collision MW-1 names, so a watch entry carries no `ticker`
# identifier, no ticker history and no bare-ticker alias. A source's own
# coin-specific id (Yahoo's PRL41876-USD; plain PRL-USD is another coin) and the
# store key it is filed under are not tickers, and the baskets resolve through them.
WATCH_TICKER_SCHEMES = ("ticker",)
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


def watch_faults(e: dict) -> list[str]:
    """A crypto.watch entry's faults (ST-13, MW-1): keyed by a ticker in any form,
    missing a disambiguation field, or its CoinGecko id and name disagreeing with
    its identifier and its own name. The loader test (G-24) holds every entry."""
    sid, out = str(e.get("id")), []
    keyed = sorted(s for s in (e.get("identifiers") or {}) if s in WATCH_TICKER_SCHEMES)
    if keyed:
        out.append(f"{sid}: a crypto.watch entry keyed by ticker ({', '.join(keyed)}): "
                   f"the ticker is never a key (MW-1)")
    if e.get("ticker_history"):
        out.append(f"{sid}: a crypto.watch entry with a ticker history (MW-1)")
    bare = [a for a in e.get("aliases") or [] if str(a).isupper() and 2 <= len(str(a)) <= 6]
    if bare:
        out.append(f"{sid}: a crypto.watch alias that is a bare ticker {bare} (MW-1)")
    w = e.get("watch") or {}
    miss = [f for f in WATCH_FIELDS if not w.get(f)]
    if miss:
        out.append(f"{sid}: crypto.watch without {', '.join(miss)} (MW-1)")
    cid = (e.get("identifiers") or {}).get("crypto_id")
    if w.get("coingecko_id") and cid != f"coingecko:{w['coingecko_id']}":
        out.append(f"{sid}: crypto_id {cid!r} is not coingecko:{w.get('coingecko_id')}")
    if w.get("name") and e.get("name") != w["name"]:
        out.append(f"{sid}: name {e.get('name')!r} is not the watch name {w['name']!r}")
    return out


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
            e["ticker_history"] = [{"ticker": str(r["ticker"]), "from": _iso(r.get("from")),
                                    "to": _iso(r.get("to"))}
                                   for r in e.get("ticker_history") or []]
            hit = self._restriction(e)
            e["restricted"] = hit is not None
            e["restricted_by"] = hit
            self.instruments.append(e)
        self._by_id = {e["id"]: e for e in self.instruments}

    def _restriction(self, e: dict) -> Optional[dict]:
        probes = (list(e["identifiers"].values()) + e["aliases"]
                  + [r["ticker"] for r in e["ticker_history"]])
        if e.get("name"):
            probes.append(str(e["name"]))
        for p in probes:
            hit = self.rules.check(p)
            if hit:
                return {"entity_id": hit.get("entity_id"), "matched_on": hit["matched_on"],
                        "root": hit.get("root"), "probe": p}
        return None

    # -- the API ---------------------------------------------------------------
    def by_coingecko(self, coingecko_id: str, on: Day = None) -> dict:
        """The instrument CoinGecko's id names (ST-13): its crypto_id scheme."""
        return self.resolve(f"coingecko:{coingecko_id}", "crypto_id", on)

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
            if e.get("merged_into"):
                continue
            if scheme == "ticker" and e["ticker_history"]:
                if any(r["ticker"] == ident and (r["from"] is None or r["from"] <= day)
                       and (r["to"] is None or day <= r["to"])
                       for r in e["ticker_history"]):
                    out.append(e)
                continue
            if scheme == "alias":
                hit = ident in e["aliases"]
            else:
                hit = e["identifiers"].get(scheme) == ident
            if hit and self.active(e, day):
                out.append(e)
        return out

    def windows(self, e: dict) -> list[tuple[str, str, Optional[str], Optional[str]]]:
        """(scheme, value, from, to) for every identifier, by its own window."""
        out = []
        for sc, v in e["identifiers"].items():
            if sc == "ticker" and e["ticker_history"]:
                continue
            out.append((sc, v, e["active_from"], e["active_to"]))
        out += [("ticker", r["ticker"], r["from"], r["to"]) for r in e["ticker_history"]]
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
        seen: dict[tuple[str, str], list[tuple[dict, Optional[str], Optional[str]]]] = {}
        for e in self.instruments:
            if e.get("merged_into"):
                continue
            for sc, v, f, t in self.windows(e):
                seen.setdefault((sc, v), []).append((e, f, t))
        lo, hi = "0000-01-01", "9999-12-31"
        for (sc, v), es in sorted(seen.items(), key=lambda kv: kv[0]):
            for i in range(len(es)):
                for j in range(i + 1, len(es)):
                    (a, af, at), (b, bf, bt) = es[i], es[j]
                    if max(af or lo, bf or lo) <= min(at or hi, bt or hi):
                        out.append(f"{sc}:{v} is active on {a['id']} and {b['id']} at once")
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
            if not e["identifiers"] and not e["ticker_history"]:
                out.append(f"{sid}: no identifier")
            if e.get("merged_into") and e["merged_into"] not in self._by_id:
                out.append(f"{sid}: merged into an unknown id")
            if e["active_from"] and e["active_to"] and e["active_from"] > e["active_to"]:
                out.append(f"{sid}: active_from after active_to")
            if e.get("asset_class") == "option_root" and e.get("underlying") not in self._by_id:
                out.append(f"{sid}: option root without a known underlying")
            if e.get("asset_class") == "crypto.watch":
                out += watch_faults(e)
            for f in FIELDS:
                if f not in e:
                    out.append(f"{sid}: missing field {f}")
            nulls = sorted(f for f in ("name", "currency", "multiplier", "exchange")
                           if e.get(f) is None)
            if sorted(set(nulls) - set(e.get("unverified") or [])):
                out.append(f"{sid}: null {nulls} not all listed as unverified")
        return out


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
    e.add_argument("--out", default=None, help="else $CHESTER_SM_EXPORT, else "
                   + EXPORT_DEFAULT)
    b = sub.add_parser("draft-box", help="read the store read-only; print master YAML")
    b.add_argument("--store")
    a = ap.parse_args(argv)
    if a.cmd == "draft-box":
        from . import sm_draft  # noqa: PLC0415
        return sm_draft._main(a.store)
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
    from . import sm_export  # noqa: PLC0415
    r = sm_export.export(a.out, m)
    print(json.dumps(r, sort_keys=True))
    return 0 if r.get("written") else 1


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
