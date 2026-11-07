"""
The refused sources, as source_registry.yaml declares them (the feed repair of
24 Oct 2026; the 16 Oct sources rule: a refusal -- a 403, a Cloudflare challenge,
a robots disallow -- becomes a listed gap and the writer stops requesting; it is
never worked around).

    from altdata import refusals
    refusals.text("farside")   # "not tracked: Farside refuses automated reads since ..."

A source is refused when its registry entry says `status: refused`, with
`refused_since` (the date) and `refused_seen` (the status the box saw). The writer
asks nothing (altdata/sources/_publication.refused) and every reader prints this
module's text where the series would have been. Not a writer: a report may
import it.

A GATE that tests a refused writer's parser on fixtures sets an empty registry
with `set_registry({"sources": {}})`; tools/validate_feed_repair.py holds the
refusal itself against the real registry.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

SOURCE_REGISTRY = Path(__file__).resolve().parent.parent / "source_registry.yaml"
_OVERRIDE: Optional[dict] = None
_CACHE: Optional[dict] = None


def set_registry(registry: Optional[dict]) -> None:
    """For a gate: read `registry` instead of the file (None restores the file)."""
    global _OVERRIDE
    _OVERRIDE = registry


def _registry() -> dict:
    global _CACHE
    if _OVERRIDE is not None:
        return _OVERRIDE
    if _CACHE is None:
        try:
            import yaml                                         # noqa: PLC0415
            _CACHE = yaml.safe_load(SOURCE_REGISTRY.read_text(encoding="utf-8")) or {}
        except Exception:                                     # noqa: BLE001
            _CACHE = {}
    return _CACHE


def refusal(source: str, registry: Optional[dict] = None) -> Optional[dict]:
    """{source, name, since, seen} when the source is declared refused, else None."""
    reg = registry if registry is not None else _registry()
    e = ((reg.get("sources") or {}).get(source)) or {}
    if e.get("status") != "refused":
        return None
    return {"source": source, "name": e.get("short_name") or source,
            "since": e.get("refused_since"), "seen": e.get("refused_seen")}


def text(source: str, registry: Optional[dict] = None) -> Optional[str]:
    """'not tracked: <source> refuses automated reads since <date> (<seen>)', or None."""
    r = refusal(source, registry)
    if not r:
        return None
    return (f"not tracked: {r['name']} refuses automated reads since {r['since']}"
            + (f" ({r['seen']})" if r.get("seen") else ""))


# ---------------------------------------------------------------------------
# HELD (D45, ruled 31 Oct 2026; paste B95). A source the box CAN read but whose
# terms forbid what the store does with it -- Cboe's, "storage in a retrieval
# system" -- is put on a declared hold while a sitting rules: `status: held`,
# `held_since`, `held_reason` and `held_line` in source_registry.yaml. The
# writer asks nothing, exactly as for a refusal; the stored rows are kept, never
# purged; and every reader prints "not tracked: <held_line>" with the last
# stored date where the series would have been. Its keys carry
# `status_extra: held` and `held_source: <source>` in metrics_registry.yaml's
# member_overrides, so the store check and the heartbeat count them declared.
# Lifting the hold is the source entry's status back to live (and the
# member_overrides lines removed); nothing else changes.
# ---------------------------------------------------------------------------

def hold(source: str, registry: Optional[dict] = None) -> Optional[dict]:
    """{source, name, since, reason, line} when the source is declared held."""
    reg = registry if registry is not None else _registry()
    e = ((reg.get("sources") or {}).get(source)) or {}
    if e.get("status") != "held":
        return None
    return {"source": source, "name": e.get("short_name") or source,
            "since": e.get("held_since"), "reason": e.get("held_reason"),
            "line": e.get("held_line") or f"held ({source})"}


def held_text(source: str, last: Optional[str] = None,
              registry: Optional[dict] = None) -> Optional[str]:
    """'not tracked: <held_line>[, last stored <date>]', or None when not held."""
    h = hold(source, registry)
    if not h:
        return None
    return f"not tracked: {h['line']}" + (f", last stored {last}" if last else "")


def key_hold(key: str, registry: Optional[dict] = None) -> Optional[dict]:
    """The hold over a registry key, through its `held_source`, or None.

    Both halves must agree: the key declared `held` AND its source held in the
    source registry, so a gate that sets an empty source registry
    (`set_registry({"sources": {}})`) sees no hold at all."""
    try:
        from . import derived                                   # noqa: PLC0415
        e = derived.registry_entry(key) or {}
    except Exception:                                         # noqa: BLE001
        return None
    if derived.declared_status(e) != "held" or not e.get("held_source"):
        return None
    return hold(str(e["held_source"]), registry)


def key_text(key: str, last: Optional[str] = None,
             registry: Optional[dict] = None) -> Optional[str]:
    """held_text for the source holding `key`, or None when the key is not held."""
    h = key_hold(key, registry)
    if not h:
        return None
    return held_text(h["source"], last, registry)


def held_leg(leg: Optional[dict], store=None, as_of: Optional[str] = None
             ) -> Optional[dict]:
    """A copy of a stored term-structure leg (the market-state object's
    champion or its basis) with the hold applied, or None when no key of it is
    held. The object is read, never recomputed (regime.py is hash-pinned): the
    hold is applied where a report prints the leg."""
    if not leg:
        return None
    keys = [k for k in [leg.get("metric"), *(leg.get("requires_store_keys") or [])]
            if k]
    for k in keys:
        last = last_stored(store, k, as_of) if store is not None else None
        t = key_text(str(k), last)
        if t:
            out = dict(leg)
            out.update({"state": None, "ratio": None, "percentile": None,
                        "value": None, "absent_reason": t, "held": True})
            return out
    return None


def last_stored(store, key: str, as_of: Optional[str] = None) -> Optional[str]:
    """The newest stored observation date of `key` (YYYY-MM-DD), or None."""
    try:
        r = (store.latest_as_of(key, as_of=as_of) if as_of
             else store.latest_as_of(key))
    except Exception:                                         # noqa: BLE001
        return None
    return str(r["observed_at"])[:10] if r and r.get("observed_at") else None
