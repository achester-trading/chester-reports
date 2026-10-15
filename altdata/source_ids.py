"""
The stored `source` string, read as a source id. (AUD-3a item 4, 14 Oct 2026)

A row's `source` is free text: whatever its writer wrote. Most writers write an
id from source_registry.yaml (`fred`, `cftc`, `kalshi`), and some write a
variant -- `kalshi:backfill` for a backfilled row, `fred:csv_migrated` for the
migrated history. The data and architecture audit found Polymarket rows under
metrics declared as Kalshi's and no list to check a string against.

THE STORE IS APPEND-ONLY, so stored strings are never rewritten. They are read
through `canonical()`:

    1. an id in source_registry.yaml is itself;
    2. a string declared in source_registry.yaml's `stored_aliases` is the id it
       names there (a declared alias, with its reason beside it) -- or, for an
       alias declared `by_key_family`, the id its row's registry key selects by
       prefix (a bare `ibkr`, ruled 15 Oct 2026), and off the list for a row whose
       key no line matches or when no key is given;
    3. `<id>:<anything>` is <id> -- the venue's or the source's own variant;
    4. anything else is OFF THE LIST: canonical() returns None and
       tools/check_store_registry.py prints it, which is the prompt to register
       the source or declare the alias. Nothing is guessed.

The as-of join's use of a source tier lives in altdata/observations.py and is
unchanged here (it is aud-1-data-fixes's file); reading it through these ids is
listed for after that branch merges.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parent.parent
_CACHE: Optional[tuple[frozenset, dict]] = None


def _load() -> tuple[frozenset, dict]:
    global _CACHE
    if _CACHE is None:
        import yaml                                             # noqa: PLC0415
        reg = yaml.safe_load((REPO / "source_registry.yaml").read_text(
            encoding="utf-8")) or {}
        _CACHE = (frozenset(reg.get("sources") or {}),
                  {str(k): (v if isinstance(v, dict) else str(v))
                   for k, v in (reg.get("stored_aliases") or {}).items()})
    return _CACHE


def ids() -> frozenset:
    """Every source id source_registry.yaml declares."""
    return _load()[0]


def _by_family(alias: dict, key: Optional[str]) -> Optional[str]:
    """The id a `by_key_family` alias gives the row's registry key: the first line
    whose prefix the key starts with, or None."""
    if not key:
        return None
    for line in alias.get("by_key_family") or []:
        # A trailing `*` marks a family (source_registry.yaml's comment).
        if str(key).startswith(str(line.get("prefix") or "\0").rstrip("*")):
            return str(line.get("source"))
    return None


def canonical(stored: Optional[str], known: Optional[frozenset] = None,
              aliases: Optional[dict] = None,
              key: Optional[str] = None) -> Optional[str]:
    """The source id a stored string means, or None when it is on no list. `key`
    is the row's registry key, which a `by_key_family` alias needs."""
    if stored is None:
        return None
    s = str(stored).strip()
    k = known if known is not None else ids()
    a = aliases if aliases is not None else _load()[1]
    if s in k:
        return s
    if s in a:
        hit = _by_family(a[s], key) if isinstance(a[s], dict) else a[s]
        if hit in k:
            return hit
        if isinstance(a[s], dict):
            return None
    head = s.split(":", 1)[0]
    if ":" in s and head in k:
        return head
    return None
