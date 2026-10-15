"""
The lab's configuration: the constitution (ruled, read-only), the session-set
settings, the engine registry and the cost classes -- one loader each, and the
one place the ledger's path is resolved.

THE CONSTITUTION IS READ, NEVER WRITTEN. There is no function here, or anywhere
in alpha/, that opens config/alpha_constitution.yaml for writing; its sha256 is
recorded in docs/alpha-lab.md and tools/validate_alpha.py fails on an unrecorded
change.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any, Optional

import yaml

REPO = Path(__file__).resolve().parent.parent
CONSTITUTION_PATH = REPO / "config" / "alpha_constitution.yaml"
SETTINGS_PATH = REPO / "config" / "alpha.yaml"
ENGINES_PATH = REPO / "config" / "alpha_engines.yaml"
COSTS_PATH = REPO / "config" / "alpha_costs.yaml"
DB_VAR = "ALPHA_DB"

HORIZONS = ("intraday", "daily", "weekly")


def _load(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def constitution(path: Optional[Path] = None) -> dict:
    return _load(path or CONSTITUTION_PATH)


def constitution_sha256(path: Optional[Path] = None) -> str:
    """The hash recorded in docs/alpha-lab.md. Over the file's bytes with line
    endings normalised to LF, so a Windows checkout and the box agree."""
    data = Path(path or CONSTITUTION_PATH).read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def settings(path: Optional[Path] = None) -> dict:
    return _load(path or SETTINGS_PATH)


def costs(path: Optional[Path] = None) -> dict:
    return _load(path or COSTS_PATH)


def engines(path: Optional[Path] = None) -> list[dict]:
    """The registry: the only place an engine is named (X-1.3)."""
    return list(_load(path or ENGINES_PATH).get("engines") or [])


def data_root() -> Path:
    """The directory holding the observation store -- the lab's ledger sits
    beside it. Read through altdata.observations so the two cannot disagree."""
    from altdata import observations                           # noqa: PLC0415
    return Path(observations.DEFAULT_DB).resolve().parent


def ledger_path(cfg: Optional[dict] = None) -> Path:
    """$ALPHA_DB, else config/alpha.yaml's ledger.path with {data_root} filled."""
    env = os.environ.get(DB_VAR)
    if env:
        return Path(env)
    tmpl = str(((cfg or settings()).get("ledger") or {}).get("path")
               or "{data_root}/alpha.db")
    return Path(tmpl.replace("{data_root}", str(data_root())))


def min_signals(horizon: str, con: Optional[dict] = None) -> int:
    con = con or constitution()
    return int(con["validation"]["min_signals"][horizon])


def periods_per_year(horizon: str, cfg: Optional[dict] = None) -> float:
    cfg = cfg or settings()
    return float((cfg.get("periods_per_year") or {}).get(horizon) or 252)


def get(d: dict, dotted: str, default: Any = None) -> Any:
    cur: Any = d
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur
