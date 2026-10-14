"""
The lab's ONE file writer (Tranche 2).

Until Tranche 2, alpha/ wrote alpha.db and no file at all
(tools/validate_alpha.py group A). Four things now need a file:

  research_dir   alpha/research/agenda.md and agenda.json      (X-2.4, the weekly loop)
  reports_dir    alpha/research/reports/<id>.md                (X-2.9, the workbench)
  outbox         ~/chester-data/outbox/lab/lab-verdicts-*.md   (X-2.11, the weekly loop)
  inbox          read only by the lab; written by the proposer (alpha_proposer/,
                 outside alpha/) and the sweep

so they go through write_text() here, which writes ONLY under the roots declared
in config/alpha.yaml `files:` (or their environment overrides), atomically (a
temporary file beside the target, then a rename), and refuses any other path.
Group A of the gate allows this module and no other; it never writes the
observation store, the register's live tables, a report or a ledger, and it
never deletes.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from . import config as acfg

ENV = {"research_dir": "ALPHA_RESEARCH_DIR", "reports_dir": "ALPHA_REPORTS_DIR",
       "inbox": "ALPHA_INBOX", "outbox": "ALPHA_OUTBOX"}
WRITABLE = ("research_dir", "reports_dir", "outbox")


class OutsideTheLab(PermissionError):
    """A write outside the lab's declared directories."""


def root(name: str, cfg: Optional[dict] = None) -> Path:
    """A declared directory: its environment override, else config/alpha.yaml
    `files.<name>` (repo-relative unless absolute or ~)."""
    env = os.environ.get(ENV[name])
    if env:
        return Path(env).expanduser().resolve()
    raw = str(((cfg or acfg.settings()).get("files") or {}).get(name) or "")
    if not raw:
        raise KeyError(f"config/alpha.yaml declares no files.{name}")
    p = Path(raw).expanduser()
    return (p if p.is_absolute() else acfg.REPO / p).resolve()


def allowed(path: Path) -> bool:
    p = Path(path).resolve()
    for name in WRITABLE:
        r = root(name)
        if p == r or r in p.parents:
            return True
    return False


def write_text(path: Path, text: str) -> Path:
    """Write `text` to `path`, which must lie under a writable lab root."""
    p = Path(path).resolve()
    if not allowed(p):
        raise OutsideTheLab(f"{p} is outside the lab's writable directories "
                            f"({', '.join(str(root(n)) for n in WRITABLE)})")
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(f".{p.name}.part")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    os.replace(tmp, p)
    return p
