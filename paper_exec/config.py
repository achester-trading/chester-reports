"""The executor's config (config/paper_exec.yaml) and its state directory."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / "config" / "paper_exec.yaml"
RISK_LIMITS = REPO / "config" / "risk_limits.yaml"


def load(path: Optional[Path] = None) -> dict:
    return yaml.safe_load(Path(path or CONFIG).read_text(encoding="utf-8")) or {}


def risk_limits(path: Optional[Path] = None) -> dict:
    return yaml.safe_load(Path(path or RISK_LIMITS).read_text(encoding="utf-8")) or {}


def state_dir(cfg: dict) -> Path:
    """$CHESTER_STATE_DIR/<state_subdir>, else ~/.chester/<state_subdir>: the
    wrappers' own state root, which the deny list keeps from rm."""
    root = Path(os.environ.get("CHESTER_STATE_DIR") or (Path.home() / ".chester"))
    return root / str(cfg.get("state_subdir") or "paper_exec")


def client_id(cfg: dict) -> int:
    from altdata.ibkr_clients import CLIENT_IDS                 # noqa: PLC0415
    return int(CLIENT_IDS[str(cfg.get("client_id_key") or "paper_exec")])


def mode(cfg: dict) -> str:
    """'off', 'dry' or 'send' -- send only when the operator has set both flags."""
    if not cfg.get("enabled"):
        return "off"
    return "dry" if cfg.get("dry_run", True) is not False else "send"
