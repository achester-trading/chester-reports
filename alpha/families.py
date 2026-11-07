"""
The lab's family registry (Batch 19 item 99, accepted 27 Oct 2026; B98).

    from alpha import families
    families.family_ref_of(h, batch_id)     # a hypothesis's family_ref, or None
    families.count_key(h, batch_id)         # what its variants are counted under

`config/alpha_families.yaml` holds one entry per section of Kakushadze and
Serur's "151 Trading Strategies" the lab could use, and two house entries. A
hypothesis's family_ref comes from the hypothesis itself, carried in its batch
from the next inbox batch on, or else from the registry's `assignments`, which
map every hypothesis registered before this change once. A registered file is
never edited, because its manifest and translations hold its sha256.

THE COUNT KEYS ON IT (docs/alpha-lab-rules.md section 15). The variant count, the
budget and the deflated Sharpe group by count_key: the family_ref where there is
one, the old `family` where there is none (an importer's tell, a search
survivor or a proposer idea from before the change). A family_ref's first
count starts from the counts already stored under the old families its
hypotheses came from (`legacy_families`), so no trial the lab made is lost when
the key changes. Where an old family split across several refs, each ref
starts from its whole count, which over-counts and so deflates harder, never
softer.

Reads config only; writes nothing.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parent.parent
REGISTRY = REPO / "config" / "alpha_families.yaml"


@lru_cache(maxsize=4)
def registry(path: Optional[str] = None) -> dict:
    import yaml                                                 # noqa: PLC0415
    return yaml.safe_load(Path(path or REGISTRY).read_text(encoding="utf-8")) or {}


def refs(path: Optional[str] = None) -> set[str]:
    return {f["ref"] for f in registry(path).get("families") or []}


def assigned(path: Optional[str] = None) -> dict[tuple[str, str], str]:
    return {(a["batch_id"], a["local_id"]): a["family_ref"]
            for a in registry(path).get("assignments") or []}


def _spec(h: dict) -> dict:
    s = h.get("spec")
    if isinstance(s, str):
        try:
            s = json.loads(s)
        except ValueError:
            s = None
    return s if isinstance(s, dict) else {}


def family_ref_of(h: dict, batch_id: Optional[str] = None,
                  path: Optional[str] = None) -> Optional[str]:
    """The hypothesis's own family_ref (a batch field or a stored row's spec),
    else its assignment by (batch_id, local_id), else None."""
    own = h.get("family_ref") or _spec(h).get("family_ref")
    if own:
        return own
    bid = batch_id or h.get("batch_id")
    return assigned(path).get((bid, h.get("local_id"))) if bid else None


def count_key(h: dict, batch_id: Optional[str] = None,
              path: Optional[str] = None) -> str:
    """The key a hypothesis's variants are counted, budgeted and deflated under."""
    return family_ref_of(h, batch_id, path) or h["family"]


@lru_cache(maxsize=4)
def _legacy(path: Optional[str] = None) -> dict[str, frozenset]:
    """family_ref -> the old `family` strings of the hypotheses assigned to it,
    read from the registered files the assignments name."""
    import yaml                                                 # noqa: PLC0415
    out: dict[str, set] = {}
    a = assigned(path)
    files = [REPO / "tests" / "fixtures" / "alpha" / "inbox" / "hypotheses-2026-10-14.yaml",
             *sorted((REPO / "alpha" / "research").glob("*.yaml"))]
    for f in files:
        doc = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        for h in doc.get("hypotheses") or []:
            ref = a.get((doc.get("batch_id"), h.get("local_id")))
            if ref and h.get("family"):
                out.setdefault(ref, set()).add(h["family"])
    return {k: frozenset(v) for k, v in out.items()}


def legacy_families(ref: str, path: Optional[str] = None) -> frozenset:
    return _legacy(path).get(ref, frozenset())


def validate_ref(ref, path: Optional[str] = None) -> Optional[str]:
    """None when `ref` is a registered family_ref, else why not."""
    if not isinstance(ref, str) or not ref.strip():
        return "family_ref is not a non-empty string"
    if ref not in refs(path):
        return f"family_ref {ref!r} is not in config/alpha_families.yaml"
    return None
