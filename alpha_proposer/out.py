"""
The proposer's ONE writer. It writes two places and nothing else:

  inbox    ~/chester-data/inbox/lab/ (config/alpha.yaml files.inbox; $ALPHA_INBOX):
           its batch file, proposals-YYYY-MM-DD.yaml, and one line appended to
           manifest-proposer.jsonl (name, sha256, written_at) that the
           ingestion checks the bytes against
  log      its own decision log, alpha_proposer-YYYY-MM.jsonl, under
           $CHESTER_LOG_DIR (else ~/logs)

tools/validate_alpha_proposer.py holds it: no other module of the package
writes a file, and these refuse any path outside the two roots.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from alpha import files

MANIFEST = "manifest-proposer.jsonl"


class OutsideTheProposer(PermissionError):
    """A write outside the inbox or the proposer's log."""


def inbox_root() -> Path:
    return files.root("inbox")


def log_root() -> Path:
    return Path(os.environ.get("CHESTER_LOG_DIR") or "~/logs").expanduser().resolve()


def _under(p: Path, root: Path) -> bool:
    p, root = p.resolve(), root.resolve()
    return p == root or root in p.parents


def write_batch(name: str, data: bytes, inbox: Optional[Path] = None) -> Path:
    root = Path(inbox or inbox_root())
    p = (root / name).resolve()
    if not _under(p, root) or p.parent != root.resolve() or p.suffix != ".yaml":
        raise OutsideTheProposer(f"{p}: the proposer writes a .yaml batch in the inbox only")
    if p.exists():
        raise FileExistsError(f"{p} exists: a batch file is never rewritten")
    root.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(f".{p.name}.part")
    with open(tmp, "wb") as fh:
        fh.write(data)
    os.replace(tmp, p)
    return p


def append_manifest(line: dict, inbox: Optional[Path] = None) -> Path:
    root = Path(inbox or inbox_root())
    p = (root / MANIFEST).resolve()
    if not _under(p, root):
        raise OutsideTheProposer(str(p))
    with open(p, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(line, sort_keys=True) + "\n")
    return p


def append_log(record: dict, month: str, log_dir: Optional[Path] = None) -> Path:
    root = Path(log_dir or log_root())
    p = (root / f"alpha_proposer-{month}.jsonl").resolve()
    if not _under(p, root):
        raise OutsideTheProposer(str(p))
    root.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(record, sort_keys=True, default=str) + "\n")
    return p
