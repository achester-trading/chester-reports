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
import re
from pathlib import Path
from typing import Optional

import yaml

REPO = Path(__file__).resolve().parent.parent
PATH = REPO / "config" / "display_labels.yaml"

# WHICH HY SERIES, AND FROM WHEN (ruled 18 Oct 2026; the register's SR-8 dated
# note). FRED serves ICE BofA's high-yield OAS from 2023-10-17 only, so a chart or
# lens printing HY names its series and the first day the store holds.
# No internal id prints (the Weekly's id rule); the FRED code is the public name.
HY_SERIES = "ICE BofA US High Yield OAS (FRED BAMLH0A0HYM2)"
FRED_HY_FROM = "2023-10-17"


def hy_source(first_day: Optional[str]) -> str:
    held = f"stored from {first_day}" if first_day else "not stored"
    return (f"series {HY_SERIES}, {held}; FRED's own history now starts "
            f"{FRED_HY_FROM}")


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
    """A registry key in words: its declared display label, else a name the
    repo already holds for it (W8-12), else the key made plain."""
    if not key:
        return ""
    return (_cfg().get("metrics") or {}).get(key) or derived_label(key) or plain(key)


# THE NAMES THE REPO ALREADY HOLDS (W8-12, weekly-fixes-9): the Weekly's detail
# tables printed "mkt eido volume", "mkt vvix" -- the key made plain. A FRED key
# takes its series description (altdata/config.py); a Yahoo key takes the
# Security Master's name, with its ticker where the ticker is a plain one (a
# ^ or =X symbol never prints: weekly-fixes-7 item 11), and the companion's
# word (volume, high, low, open).
_COMPANIONS = (("_volume", "volume"), ("_high", "high"), ("_low", "low"),
               ("_open", "open"))
_PLAIN_TICKER = re.compile(r"[A-Z][A-Z.]{0,5}")


@functools.lru_cache(maxsize=1)
def _fred_names() -> dict:
    try:
        from altdata import config                              # noqa: PLC0415
        return {f"fred.{s.key}": s.description for s in config.FRED_PULL_SERIES}
    except Exception:                                           # noqa: BLE001
        return {}


@functools.lru_cache(maxsize=1)
def _tape_names() -> dict:
    """The tape's own labels by daily store key ("10-year yield")."""
    try:
        from altdata import bars                                # noqa: PLC0415
        return {t["daily"]: t["label"] for t in bars.tape()
                if t.get("daily") and t.get("label")}
    except Exception:                                           # noqa: BLE001
        return {}


_FX = re.compile(r"([A-Z]{3})([A-Z]{3})=X")


@functools.lru_cache(maxsize=1)
def _master():
    try:
        from altdata import security_master                     # noqa: PLC0415
        return security_master.Master()
    except Exception:                                           # noqa: BLE001
        return None


@functools.lru_cache(maxsize=1024)
def derived_label(key: str) -> Optional[str]:
    if key in _fred_names():
        return _fred_names()[key]
    fam, _, rest = str(key).partition(".")
    if fam != "yfinance" or not rest.startswith("mkt_"):
        return None
    base, word = rest, ""
    for suf, w in _COMPANIONS:
        if rest.endswith(suf):
            base, word = rest[: -len(suf)], f" {w}"
            break
    tape = _tape_names().get(f"yfinance.{base}")
    m = _master()
    try:
        e = m.resolve(f"yfinance.{base}", "store_key") if m else None
    except Exception:                                           # noqa: BLE001
        e = None
    name = (e or {}).get("name") or tape
    sym = str(((e or {}).get("identifiers") or {}).get("yahoo") or "")
    fx = _FX.fullmatch(sym)
    if not name and fx:
        name = f"{fx.group(1)}/{fx.group(2)}"
    tick = sym if _PLAIN_TICKER.fullmatch(sym) else None
    label = (f"{name} ({tick})" if name and tick else name or tick)
    return f"{label}{word}" if label else None


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


# ---------------------------------------------------------------------------
# PLAIN LANGUAGE (T2.2, 4 Oct 2026, item 2): the words the prose may use
# ---------------------------------------------------------------------------
def contradiction_plain(cid: Optional[str]) -> dict:
    """{'legs': what each side says, 'closes': what would close it}, or {}. A
    narrative_vs_data row reads the generic narrative entry."""
    c = _cfg().get("contradiction_plain") or {}
    head = str(cid or "").partition(".")[0]
    return dict(c.get(cid) or c.get(head) or {})


def exception_kind(kind: Optional[str]) -> str:
    return str((_cfg().get("exception_kinds") or {}).get(kind) or kind or "")


def story(sid: Optional[str]) -> dict:
    """{'title', 'statement'} in plain words, or {} for an undeclared story."""
    return dict((_cfg().get("stories") or {}).get(sid) or {})


def sector(ticker: Optional[str]) -> str:
    """'Health Care (XLV)' for 'XLV'; the ticker itself when undeclared."""
    t = str(ticker or "").upper()
    return str((_cfg().get("sectors") or {}).get(t) or t)


def state(word: Optional[str]) -> str:
    return str((_cfg().get("states") or {}).get(str(word or "").lower()) or "")


def glossary() -> list[dict]:
    return list(_cfg().get("glossary") or [])
