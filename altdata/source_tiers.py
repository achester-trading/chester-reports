"""
Source tiers for story-query headlines, and kinds for Fed press releases.

    from altdata import source_tiers as tiers
    tiers.tier_of(title)          # 1, 2, 3, or None when unclassified
    tiers.counted(title)          # True only for tiers 1 and 2
    tiers.fed_class(title)        # applications | monetary_policy | speeches |
                                  # supervision | other

Weekly edition 1, item 5. Everything is declared in config/source_tiers.yaml,
which says why; this module reads it and applies it, and computes nothing else.
Pure functions of the stored title, so every count they feed replays exactly.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "config" / "source_tiers.yaml"
_CFG: Optional[dict] = None


def load(path: Optional[Path] = None) -> dict:
    global _CFG
    if _CFG is not None and path is None:
        return _CFG
    import yaml  # noqa: PLC0415
    cfg = yaml.safe_load((path or CONFIG_PATH).read_text(encoding="utf-8")) or {}
    if path is None:
        _CFG = cfg
    return cfg


def config_hash(cfg: Optional[dict] = None) -> str:
    """What a narrative evaluation's rules_version folds in: a reclassified
    outlet is a declared rule change, not a regression."""
    blob = json.dumps(cfg if cfg is not None else load(), sort_keys=True,
                      default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def outlet_of(title: Optional[str]) -> Optional[str]:
    """The attribution after the last " - " of a Google News title, or None."""
    t = str(title or "")
    if " - " not in t:
        return None
    return t.rsplit(" - ", 1)[-1].strip() or None


def tier_of(title: Optional[str], cfg: Optional[dict] = None) -> Optional[int]:
    """1, 2 or 3 for a listed outlet; None for an unclassified one."""
    cfg = cfg if cfg is not None else load()
    o = (outlet_of(title) or "").lower()
    if not o:
        return None
    for tier, names in (cfg.get("tiers") or {}).items():
        if o in {str(n).lower() for n in names or []}:
            return int(tier)
    return None


def counted(title: Optional[str], cfg: Optional[dict] = None) -> bool:
    """Whether a headline counts toward attention and evidence."""
    cfg = cfg if cfg is not None else load()
    t = tier_of(title, cfg)
    if t is None:
        t = int(cfg.get("unclassified_counts_as") or 3)
    return t in {int(x) for x in cfg.get("counted_tiers") or [1, 2]}


def fed_class(title: Optional[str], cfg: Optional[dict] = None) -> str:
    """The declared kind of a Fed press release; first match wins."""
    cfg = cfg if cfg is not None else load()
    t = str(title or "")
    for c in cfg.get("fed_press_classes") or []:
        if any(re.search(p, t) for p in c.get("patterns") or []):
            return str(c["class"])
    return "other"


def fed_listed(title: Optional[str], cfg: Optional[dict] = None) -> bool:
    """False for a kind declared count-only (applications)."""
    cfg = cfg if cfg is not None else load()
    k = fed_class(title, cfg)
    for c in cfg.get("fed_press_classes") or []:
        if c.get("class") == k:
            return bool(c.get("listed", True))
    return True


def is_fed(source: Optional[str], cfg: Optional[dict] = None) -> bool:
    cfg = cfg if cfg is not None else load()
    return str(source or "") in set(cfg.get("fed_press_sources") or [])
