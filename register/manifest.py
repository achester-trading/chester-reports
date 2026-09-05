"""
Run identity: what went in, what came out, and what code did it.

A packet is only worth keeping if a run REPLAYS EXACTLY from it (26.2 #3). That
requires pinning four things and being honest about a fifth.

    git_sha             the code
    data_manifest_hash  the inputs, by content and not by path
    registry versions   the declared semantics
    available_at_cutoff what the as-of join was allowed to see
    output_hash         what came out, canonicalised

CANONICALISATION IS NOT OPTIONAL, AND SAYING SO IS THE POINT. Every profile
carries `computed_at`, and its quality gates carry `evaluated_at`. Both are
clocks, both change on every run, and a raw byte comparison of two identical
runs therefore fails. Measured on Friday's SPY chain: two consecutive runs over
the same input hash differently raw, and identically once those two fields are
removed -- nothing else varies.

So output_hash is taken over the output with VOLATILE_FIELDS stripped, and the
packet records which fields those were. A future reader can then reproduce the
hash instead of guessing why it does not match, and a field quietly added to
that list later is visible in the packet rather than hidden in a constant.

CODE_DIRTY. A packet naming a SHA while the working tree had uncommitted edits
is a lie about replayability. It gets recorded rather than prevented -- the run
still happened, and a run you cannot replay is worth knowing about.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Iterable, Optional

REPO = Path(__file__).resolve().parent.parent

# Clocks. They describe when the computation ran, never what it concluded, so
# excluding them removes no information about the result.
VOLATILE_FIELDS = ("computed_at", "evaluated_at")


def git_sha(short: bool = False) -> str:
    try:
        args = ["git", "rev-parse"] + (["--short"] if short else []) + ["HEAD"]
        return subprocess.run(args, cwd=REPO, capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:  # noqa: BLE001 -- a missing git is a fact, not a crash
        return "unknown"


def code_dirty() -> bool:
    """Did the working tree have uncommitted changes when this ran?"""
    try:
        out = subprocess.run(["git", "status", "--porcelain"], cwd=REPO,
                             capture_output=True, text=True, check=True).stdout
        return bool(out.strip())
    except Exception:  # noqa: BLE001
        return True          # unknown counts as dirty: it cannot be replayed


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def data_manifest(paths: Iterable[Path]) -> dict:
    """Content-addressed manifest of the run's inputs.

    Paths are recorded relative to the repo and hashed by CONTENT, so a file
    moved or a directory renamed does not change the manifest while an edited
    byte does. That is the property replay needs: same inputs, not same layout.
    """
    files = []
    for p in sorted(set(Path(x) for x in paths)):
        if not p.is_file():
            continue
        try:
            rel = str(p.resolve().relative_to(REPO)).replace("\\", "/")
        except ValueError:
            rel = str(p).replace("\\", "/")
        files.append({"path": rel, "sha256": sha256_file(p),
                      "bytes": p.stat().st_size})
    blob = json.dumps(files, sort_keys=True, separators=(",", ":"))
    return {"files": files,
            "hash": hashlib.sha256(blob.encode()).hexdigest(),
            "file_count": len(files)}


def strip_volatile(obj: Any, volatile: Iterable[str] = VOLATILE_FIELDS) -> Any:
    """Recursively drop clock fields so two runs are comparable."""
    vol = set(volatile)
    if isinstance(obj, dict):
        return {k: strip_volatile(v, vol) for k, v in obj.items() if k not in vol}
    if isinstance(obj, list):
        return [strip_volatile(v, vol) for v in obj]
    return obj


def output_hash(obj: Any, volatile: Iterable[str] = VOLATILE_FIELDS) -> str:
    """Canonical hash of a run's output, clocks removed."""
    canon = json.dumps(strip_volatile(obj, volatile), sort_keys=True,
                       separators=(",", ":"), default=str)
    return hashlib.sha256(canon.encode()).hexdigest()


def registry_versions() -> dict:
    """Declared versions of the two registries, for the packet."""
    import yaml  # noqa: PLC0415
    out = {}
    for name, fn in (("metrics_registry_version", "metrics_registry.yaml"),
                     ("source_registry_version", "source_registry.yaml")):
        try:
            with (REPO / fn).open(encoding="utf-8") as fp:
                out[name] = str((yaml.safe_load(fp) or {}).get("version", "unknown"))
        except Exception:  # noqa: BLE001
            out[name] = "unknown"
    return out


def build_packet(run_id: str, decision_time: str, available_at_cutoff: str,
                 input_paths: Iterable[Path], outputs: Any,
                 volatile: Iterable[str] = VOLATILE_FIELDS) -> dict:
    """Everything needed to replay one run, assembled in one place."""
    manifest = data_manifest(input_paths)
    return {
        "run_id": run_id,
        "decision_time": decision_time,
        "available_at_cutoff": available_at_cutoff,
        "git_sha": git_sha(),
        "code_dirty": code_dirty(),
        "data_manifest": manifest,
        "data_manifest_hash": manifest["hash"],
        "output_hash": output_hash(outputs, volatile),
        "volatile_fields": list(volatile),
        **registry_versions(),
    }
