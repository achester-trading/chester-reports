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
