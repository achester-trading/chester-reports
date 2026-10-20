"""
Pre-registration by manifest (X-3; the paste of 17 Oct 2026 for alpha-lab-3).

    python -m alpha.manifest register FILE.yaml [--source operator]   # box write
    python -m alpha.manifest show BATCH_ID

A MANIFEST IS WRITTEN BEFORE THE REGISTER IS. For a batch that does not come from
Drive (whose manifest is the sweep's `rclone lsjson`, X-2.11) or from the daily
proposer (its own manifest-proposer.jsonl), the lab writes one file first:

    <research_dir>/manifests/<batch_id>--<written_at, compact>.json

holding the batch exactly as it is registered, the instant it was written and
the sha256 of the batch's canonical JSON. Only then does the register take the
batch, with that instant as every hypothesis's pre_registered_at and the file's
sha256 on the batch row (hypothesis_batches.file_sha256). The importer of tells
(alpha/tells.py), the workbench's `new` and the X-3 engines' roster all register
this way.

THE HARNESS REFUSES A HYPOTHESIS WITHOUT ONE. check() runs beside
hypotheses.refuse_if_unregistered() before every harness run: the hypothesis's
batch must be on file, carry a manifest (a Drive or proposer created time, or a
manifest file's sha256), and the manifest's instant must not be later than the
run. A manifest file that is present on disk must still hash to what the batch
row recorded; one that has been edited since is refused. A hypothesis with no
manifest is a variant, not an idea.

The manifest goes through alpha/files.py, the lab's one file writer, under
research_dir (gitignored, alpha/research/manifests/). Nothing here runs a test.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Optional

from altdata import session

from . import files
from . import hypotheses as hyp

SUBDIR = "manifests"
FORMAT = "alpha-lab-manifest/v1"


class NoManifest(hyp.PreRegistrationViolation):
    """A hypothesis whose batch carries no manifest dated before the run."""


def canonical(doc: Any) -> str:
    return json.dumps(doc, sort_keys=True, default=str, ensure_ascii=False,
                      separators=(",", ":"))


def batch_sha256(doc: dict) -> str:
    return hashlib.sha256(canonical(doc).encode("utf-8")).hexdigest()


def file_name(batch_id: str, written_at: str) -> str:
    stamp = written_at[:26].replace("-", "").replace(":", "").replace(".", "")
    return f"{batch_id}--{stamp}.json"


def path_for(name: str) -> Path:
    return files.root("research_dir") / SUBDIR / name


def write(doc: dict, written_at: Optional[str] = None) -> dict:
    """Write the batch's manifest now; returns {path, name, sha256, written_at}.
    A manifest already on file is never overwritten."""
    at = hyp.instant(written_at or session.utc_iso(timespec="microseconds"))
    if at is None:
        raise ValueError(f"the manifest's instant {written_at!r} has no zone")
    name = file_name(doc["batch_id"], at)
    p = path_for(name)
    if p.is_file():
        raise FileExistsError(f"a manifest is already on file at {p}; it is never "
                              f"overwritten")
    sha = batch_sha256(doc)
    body = {"format": FORMAT, "batch_id": doc["batch_id"], "written_at": at,
            "batch_sha256": sha, "n_hypotheses": len(doc.get("hypotheses") or []),
            "batch": doc}
    files.write_text(p, json.dumps(body, indent=2, sort_keys=True, default=str,
                                   ensure_ascii=False) + "\n")
    return {"path": str(p), "name": name, "sha256": sha, "written_at": at}


def read(name: str) -> Optional[dict]:
    p = path_for(name)
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def register(ledger, store, doc: dict, as_of: Optional[str] = None,
             written_at: Optional[str] = None) -> dict:
    """The manifest first, then the register (intake.admit) at the manifest's
    instant. The batch has passed the v1 schema check."""
    from . import intake                                        # noqa: PLC0415
    errs = hyp.validate_batch(doc)
    if errs:
        raise ValueError("the batch fails the v1 schema: " + "; ".join(errs[:8]))
    if hyp.Register(ledger).batch(doc["batch_id"]):
        raise ValueError(f"batch {doc['batch_id']} is already registered")
    m = write(doc, written_at or as_of)
    out = intake.admit(ledger, store, doc, m["written_at"], as_of or m["written_at"],
                       file_name=m["name"], file_sha256=m["sha256"],
                       created_time=m["written_at"])
    out["manifest"] = m
    return out


def manifest_of(ledger, h: dict) -> Optional[dict]:
    """The hypothesis's manifest as the register holds it: {instant, kind, sha256}
    or None. Drive and the proposer give a created time; a manifest file gives
    its sha256 and its instant."""
    b = ledger.one("SELECT * FROM hypothesis_batches WHERE batch_id=?",
                   (h.get("batch_id"),))
    if not b:
        return None
    at = hyp.instant(b.get("created_time")) or (
        hyp.instant(b.get("pre_registered_at")) if b.get("file_sha256") else None)
    if at is None:
        return None
    kind = ("manifest_file" if str(b.get("file_name") or "").startswith(
        f"{h.get('batch_id')}--") and b.get("file_sha256") else "created_time")
    return {"instant": at, "kind": kind, "sha256": b.get("file_sha256"),
            "file_name": b.get("file_name")}


def check(ledger, h: Optional[dict], run_as_of: str) -> dict:
    """Refuse a run on a hypothesis with no manifest dated at or before it."""
    if not h:
        raise NoManifest("no such hypothesis: a rule is registered before it is run")
    m = manifest_of(ledger, h)
    if m is None:
        raise NoManifest(f"{h.get('id')}: its batch {h.get('batch_id')} carries no "
                         f"manifest -- every hypothesis is pre-registered by its "
                         f"manifest before its first backtest")
    run = hyp.instant(run_as_of)
    if run is None or m["instant"] > run:
        raise NoManifest(f"{h.get('id')}: its manifest is dated {m['instant']}, after "
                         f"the run at {run_as_of}")
    if m["kind"] == "manifest_file":
        doc = read(str(m["file_name"]))
        if doc is not None and doc.get("batch_sha256") != m["sha256"]:
            raise NoManifest(f"{h.get('id')}: the manifest on file no longer hashes to "
                             f"what the register recorded -- it was edited after "
                             f"registration")
    return m


def _main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="python -m alpha.manifest",
                                 description="pre-register a batch by its manifest")
    ap.add_argument("--store")
    ap.add_argument("--ledger")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("register", help="write the manifest, then register (box write)")
    r.add_argument("file")
    s = sub.add_parser("show", help="print a manifest, by its file name")
    s.add_argument("name")
    a = ap.parse_args(argv)
    if a.cmd == "show":
        doc = read(a.name)
        if doc is None:
            print(f"no manifest on file named {a.name}")
            return 2
        print(f"{doc['batch_id']}: written {doc['written_at']}, sha256 "
              f"{doc['batch_sha256']}, {doc['n_hypotheses']} hypotheses")
        return 0
    import yaml                                                 # noqa: PLC0415
    from .ledger import Ledger                                  # noqa: PLC0415
    from .store import ReadOnlyStore                            # noqa: PLC0415
    doc = yaml.safe_load(Path(a.file).read_text(encoding="utf-8"))
    with Ledger(a.ledger) as lg:
        st = ReadOnlyStore(a.store)
        try:
            out = register(lg, st, doc)
        finally:
            st.close()
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
