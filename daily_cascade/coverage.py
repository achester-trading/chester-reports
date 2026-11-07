"""
THE COVERAGE TABLE (W10-3; D46 decision 4, 31 Oct 2026).

One table at the end of the Weekly's section 10, before the Detail Tables, and
in the Monthly's appendix: what the store holds, family by family, in one place.
The per-cell markers ("not stored", "not tracked", "awaiting") stay where they
are (decision 4); this is their summary.

  - ITS SOURCE. The store check's own lists (tools/check_store_registry.check():
    current, stale with its "dead?" mark, declared, quiet, registered with no
    rows, unregistered), called as a function over the store opened read-only.
    The CLI is never run and its output is unchanged.
  - ITS ROWS. One per family and state. A family is the registry's `family`
    field (price, rate, spread, release, quantity, conditions, ratio); a key the
    lenses exclude has none and is counted under "other"; a stored key the
    registry does not know is "unregistered". Every key sits in exactly one row.
  - ITS STATES: stored; stale (past its own allowance; "dead?" counted in the
    reason); awaiting (registered with no row yet, or declared not_yet_sourced);
    declared gap; refused; held (while_held); superseded; stored, unregistered.
    "Unvalidated" is a signal's tag, not a key's, and no list in the store check
    holds it, so it prints no row.
  - ITS DATE ("Since"): for a stored or stale row, the newest observation among
    its keys; for a declared or awaiting row, the newest `added_date` the
    registry records for its keys, "—" where it records none. The registry keeps
    no date a status changed, and the table says so beneath itself.

It reads; it writes nothing and computes no measure.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

log = logging.getLogger(__name__)

TITLE = "Coverage"
COLUMNS = ["Family", "State", "Keys", "Reason", "Since"]
FAMILY_ORDER = ("price", "rate", "spread", "release", "quantity", "conditions",
                "ratio", "other", "unregistered")
STATE_ORDER = ("stored", "stale", "awaiting", "declared gap", "refused", "held",
               "superseded", "stored, unregistered")
STATUS_STATE = {"gap": "declared gap", "refused": "refused", "while_held": "held",
                "superseded": "superseded", "not_yet_sourced": "awaiting"}
NOTE = ("One row per family and state, from the store check's lists; each key "
        "counts once. Since: the newest observation for a stored or stale row; "
        "the newest date the registry added a declared or awaiting key, \"—\" "
        "where it records none (it keeps no date a status changed). The cells "
        "keep their own markers.")


def _family(e: Optional[dict]) -> str:
    return str((e or {}).get("family") or "other")


_TOKEN = re.compile(r"\b[a-z][a-z0-9_]*\.[A-Za-z0-9_.<>]*[A-Za-z0-9_>]")


def plain(text: str, resolved: dict) -> str:
    """A reason as a reader reads it: no registry id reaches the edition (the
    Weekly's house rule). A key prints as the edition names it everywhere else
    (altdata/labels.metric); a hostname (www.mba.org) is no registry namespace
    and stays."""
    from altdata import labels                                  # noqa: PLC0415
    spaces = {k.split(".", 1)[0] for k in resolved}

    def sub(m: re.Match) -> str:
        tok = m.group(0)
        if tok.split(".", 1)[0] not in spaces:
            return tok
        name = labels.metric(tok)
        return name if name and not _TOKEN.search(name) else "another series"
    return _TOKEN.sub(sub, str(text or ""))


def _reason(e: dict) -> str:
    if e.get("superseded_by"):
        return f"superseded by {e['superseded_by']}"
    return str(e.get("gap_reason") or e.get("not_tracked_reason") or "")


def rows(r: dict, resolved: dict) -> list[dict]:
    """The check's lists as {family, state, keys, reasons, since} rows, each key
    once."""
    acc: dict[tuple, dict] = {}
    placed: set = set()

    def put(key: str, fam: str, state: str, reason: str = "", since: str = "") -> None:
        if key in placed:
            return
        placed.add(key)
        a = acc.setdefault((fam, state), {"family": fam, "state": state, "keys": [],
                                          "reasons": {}, "since": "", "dead": 0})
        a["keys"].append(key)
        reason = plain(reason, resolved)
        if reason:
            a["reasons"][reason] = a["reasons"].get(reason, 0) + 1
        if since and since > a["since"]:
            a["since"] = since

    for x in r.get("current") or []:
        put(x["key"], _family(resolved.get(x["key"])), "stored", since=x.get("newest") or "")
    for x in r.get("stale") or []:
        put(x["key"], _family(resolved.get(x["key"])), "stale",
            "past its own staleness allowance", x.get("newest") or "")
        if x.get("dead"):
            acc[(_family(resolved.get(x["key"])), "stale")]["dead"] += 1
    for x in r.get("declared") or []:
        e = resolved.get(x["key"]) or {}
        put(x["key"], _family(e), STATUS_STATE.get(x.get("status"), "declared gap"),
            _reason(e) or str(x.get("why") or ""), x.get("newest") or "")
    for k in r.get("quiet") or []:
        e = resolved.get(k) or {}
        st = e.get("status_extra") or e.get("status")
        put(k, _family(e), STATUS_STATE.get(st, "declared gap"),
            _reason(e) or ("declared not yet sourced" if st == "not_yet_sourced" else ""),
            str(e.get("added_date") or "")[:10])
    for k in r.get("no_rows") or []:
        e = resolved.get(k) or {}
        put(k, _family(e), "awaiting", "registered; no row in the store yet",
            str(e.get("added_date") or "")[:10])
    for k in r.get("unregistered") or []:
        put(k, "unregistered", "stored, unregistered", "the registry does not know it")

    def order(a: dict) -> tuple:
        f, s = a["family"], a["state"]
        return (FAMILY_ORDER.index(f) if f in FAMILY_ORDER else len(FAMILY_ORDER), f,
                STATE_ORDER.index(s) if s in STATE_ORDER else len(STATE_ORDER))

    return sorted(acc.values(), key=order)


def _reason_cell(a: dict) -> str:
    rs = sorted(a["reasons"].items(), key=lambda kv: (-kv[1], kv[0]))
    txt = "; ".join(r for r, _ in rs[:2])
    if len(rs) > 2:
        txt += f" (+{len(rs) - 2} more)"
    if a.get("dead"):
        txt += f"; {a['dead']} dead? (past three times the allowance)"
    return txt or "—"


def table(r: dict, resolved: dict) -> dict:
    """The Coverage table: one row per family and state."""
    rs = rows(r, resolved)
    return {"title": TITLE, "columns": list(COLUMNS),
            "rows": [[a["family"], a["state"], f"{len(a['keys']):,}", _reason_cell(a),
                      a["since"] or "—"] for a in rs],
            "note": NOTE, "keys": sum(len(a["keys"]) for a in rs)}


def build(db: Optional[str], as_of: Optional[str] = None,
          reg: Optional[dict] = None) -> Optional[dict]:
    """The table over the store at `db` (read-only; None is the default store,
    as the editions' own readers take it), or None with the reason logged when
    the store cannot be read. Never raises."""
    try:
        if not db:
            from altdata import observations                    # noqa: PLC0415
            db = observations.DEFAULT_DB
        from pathlib import Path                                # noqa: PLC0415
        if not Path(db).exists():
            log.warning("coverage table unavailable: no store at %s", db)
            return None
        import yaml                                             # noqa: PLC0415
        from altdata import derived                             # noqa: PLC0415
        from tools import check_store_registry as csr           # noqa: PLC0415
        reg = reg if reg is not None else yaml.safe_load(
            (csr.REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
        r = csr.check(db, as_of, reg)
        return table(r, derived.resolve_registry(reg))
    except Exception as exc:                                    # noqa: BLE001
        log.warning("coverage table unavailable: %s: %s", type(exc).__name__, exc)
        return None
