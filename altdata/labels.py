"""
The reader's names for the system's ids. (T2.1, 4 Oct 2026)

    from altdata import labels
    labels.contradiction("equities_vs_credit")   # "equities against high-yield credit"
    labels.exception("extreme:fred.mortgage_30y") # "the 30-year mortgage rate at a five-year extreme"
    labels.metric("fred.hy_oas")                 # "high-yield credit spreads (OAS)"

No internal id reaches prose or a list: the reports print these, and the prose
slices carry labels in place of ids. Read from config/display_labels.yaml; a
narrative_vs_data row takes its story's name from config/narratives.yaml. An id
with no label is returned in a plain form (underscores to spaces, prefix
dropped) and the gate fails on it, so a missing label is caught, not printed.
"""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Optional

import yaml

REPO = Path(__file__).resolve().parent.parent
PATH = REPO / "config" / "display_labels.yaml"


@functools.lru_cache(maxsize=1)
def _cfg() -> dict:
    with open(PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


@functools.lru_cache(maxsize=1)
def _stories() -> dict:
    try:
        with open(REPO / "config" / "narratives.yaml", encoding="utf-8") as fh:
            d = yaml.safe_load(fh) or {}
        out = {}
        for k, v in d.items():
            if isinstance(v, dict) and v.get("name"):
                out[k] = v["name"]
            if isinstance(v, dict):
                for kk, vv in v.items():
                    if isinstance(vv, dict) and vv.get("name"):
                        out[kk] = vv["name"]
        return out
    except Exception:                                           # noqa: BLE001
        return {}


def plain(s: str) -> str:
    return str(s).split(".", 1)[-1].replace("_", " ")


def metric(key: Optional[str]) -> str:
    if not key:
        return ""
    return (_cfg().get("metrics") or {}).get(key) or plain(key)


def contradiction(cid: Optional[str]) -> str:
    if not cid:
        return ""
    c = _cfg().get("contradictions") or {}
    if cid in c:
        return c[cid]
    head, _, story = str(cid).partition(".")
    if head == "narrative_vs_data" and story:
        return f"the {_stories().get(story, plain(story))} story against the data"
    return plain(cid)


def exception(eid: Optional[str]) -> str:
    """An exception id ('extreme:<metric>' or 'contradiction:<id>') in words."""
    kind, _, rest = str(eid or "").partition(":")
    if kind == "extreme":
        return f"{metric(rest)} at a five-year extreme"
    if kind == "contradiction":
        return f"{contradiction(rest)}, held past its session count"
    return plain(eid or "")


def missing(ids: list[str]) -> list[str]:
    """Metric and contradiction ids with no declared label (the gate's check)."""
    m, c = _cfg().get("metrics") or {}, _cfg().get("contradictions") or {}
    return [i for i in ids if i not in m and i not in c]
