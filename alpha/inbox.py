"""
The Drive inbox (X-2.11; change order 10.2).

    ~/chester-data/inbox/lab/            (config/alpha.yaml files.inbox; $ALPHA_INBOX)
      hypotheses-YYYY-MM-DD.yaml         a batch, alpha-lab-hypotheses/v1
      hypotheses-YYYY-MM-DD.md           its human copy: ignored
      manifest-drive.json                the sweep's `rclone lsjson --metadata
                                         --hash` of the Drive folder
      manifest-proposer.jsonl            one line per file the daily proposer
                                         wrote on the box: name, sha256, written_at

The nightly sweep (scripts/rclone_sync.sh) lists <remote>:chester-vendor-checks/
lab-inbox into manifest-drive.json and copies the folder here (copy, never sync).
The nightly loop then ingests each NEW *.yaml once, in name order:

  pre_registered_at = the file's CREATED time, from its manifest -- Drive's
      `Metadata.btime` (rclone's Drive metadata: btime is the file's creation,
      mtime its last modification, both RFC 3339 to the millisecond; verified on
      rclone.org/drive, 14 Oct 2026), or the proposer's line for a file written
      on the box. Never the author's own `written_at`, never the local mtime.

  REFUSED (the whole file, logged in inbox_log with the reason):
    * a manifest entry without a created time (Drive btime)
    * bytes that do not match the manifest's hash         (md5 for Drive, sha256
      for the proposer)
    * modified more than 5 minutes after its creation     -- an edited batch is
      not a pre-registration; a correction is a new file naming what it
      supersedes
    * written_at later than its created time              -- a file cannot have
      been written after it existed
    * a duplicate batch_id
    * the v1 schema, or a batch-level budget
  WAITING (retried next night, not refused): no manifest entry at all -- the
      sweep lists the folder before it copies, so a file can land in between.
  REFUSED (one hypothesis): a blocked instrument (alpha/intake.py).
  An instrument not in the store registers as data_gap. Local ids map to register
  ids (hypotheses.batch_id + local_id).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Optional

from . import files, intake
from . import hypotheses as hyp

DRIVE_MANIFEST = "manifest-drive.json"
PROPOSER_MANIFEST = "manifest-proposer.jsonl"
EDIT_TOLERANCE = dt.timedelta(minutes=5)


def drive_manifest(inbox: Path) -> dict[str, dict]:
    """name -> {created, modified, md5} from the sweep's lsjson listing."""
    p = inbox / DRIVE_MANIFEST
    if not p.is_file():
        return {}
    try:
        rows = json.loads(p.read_text(encoding="utf-8"))
    except ValueError:
        return {}
    out = {}
    for r in rows if isinstance(rows, list) else []:
        if not isinstance(r, dict) or r.get("IsDir"):
            continue
        md = r.get("Metadata") or {}
        hashes = r.get("Hashes") or {}
        out[str(r.get("Name") or r.get("Path"))] = {
            "created": hyp.instant(md.get("btime")),
            "modified": hyp.instant(md.get("mtime") or r.get("ModTime")),
            "md5": (hashes.get("md5") or hashes.get("MD5") or "").lower() or None,
            "via": "drive"}
    return out


def proposer_manifest(inbox: Path) -> dict[str, dict]:
    p = inbox / PROPOSER_MANIFEST
    out: dict[str, dict] = {}
    if not p.is_file():
        return out
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        w = hyp.instant(r.get("written_at"))
        if r.get("name") and w:
            out[str(r["name"])] = {"created": w, "modified": w,
                                   "sha256": str(r.get("sha256") or "").lower(),
                                   "via": "proposer"}
    return out


def _seen(ledger, name: str, sha: str) -> bool:
    return ledger.one("SELECT 1 AS x FROM inbox_log WHERE file_name=? AND "
                      "file_sha256=? AND local_id IS NULL AND verdict IN "
                      "('ingested','refused')", (name, sha)) is not None


def _log(ledger, name: str, sha: Optional[str], verdict: str, reason: str,
         as_of: str, batch_id: Optional[str] = None, created: Optional[str] = None,
         modified: Optional[str] = None) -> None:
    ledger._insert("inbox_log", {"file_name": name, "file_sha256": sha,
                                 "batch_id": batch_id, "local_id": None,
                                 "verdict": verdict, "reason": reason,
                                 "created_time": created, "modified_time": modified,
                                 "as_of": as_of})


def check_file(raw: bytes, meta: Optional[dict]) -> tuple[Optional[dict], list[str]]:
    """The file-level checks. (the parsed batch, []) or (None|doc, reasons)."""
    why: list[str] = []
    if meta is None:
        return None, ["no manifest entry: its created time is unknown"]
    if not meta.get("created"):
        return None, ["the manifest carries no created time (Drive btime)"]
    if meta["via"] == "drive" and meta.get("md5") and \
            hashlib.md5(raw).hexdigest() != meta["md5"]:                     # noqa: S324
        why.append("the bytes do not match the manifest's md5")
    if meta["via"] == "proposer" and hashlib.sha256(raw).hexdigest() != meta.get("sha256"):
        why.append("the bytes do not match the proposer's sha256")
    c = dt.datetime.fromisoformat(meta["created"])
    m = dt.datetime.fromisoformat(meta["modified"] or meta["created"])
    if m - c > EDIT_TOLERANCE:
        why.append(f"modified {m - c} after its creation (more than 5 minutes): "
                   f"an edited batch is not a pre-registration")
    try:
        doc = hyp.load_batch(raw.decode("utf-8"))
    except Exception as exc:                                  # noqa: BLE001
        return None, why + [f"not readable YAML: {type(exc).__name__}"]
    errs = hyp.validate_batch(doc)
    if errs:
        return doc, why + [f"schema: {e}" for e in errs[:8]]
    w = hyp.instant(doc.get("written_at"))
    if w and w > meta["created"]:
        why.append(f"written_at {w} is later than its created time {meta['created']}")
    if meta["via"] == "proposer" and (doc.get("channel") != "daily-proposer"
                                      or doc.get("source") != "model"):
        why.append("a file the proposer wrote is channel daily-proposer, source model")
    for lid, w2 in hyp.budget_errors(doc):
        if lid is None:
            why.append(w2)
    return doc, why


def ingest(ledger, store, as_of: str, inbox: Optional[Path] = None,
           translations_root=None) -> dict:
    """Ingest every new batch file in the inbox, once. Never raises for a bad
    file: it is refused and logged."""
    inbox = Path(inbox or files.root("inbox"))
    out = {"ingested": [], "refused": [], "waiting": [], "ignored": []}
    if not inbox.is_dir():
        out["waiting"].append(f"no inbox at {inbox}")
        return out
    man = {**drive_manifest(inbox), **proposer_manifest(inbox)}
    reg = hyp.Register(ledger)
    # IN ORDER OF CREATION, not of name: of two files carrying one batch_id, the
    # one that existed first is the pre-registration and the later the duplicate.
    order = sorted(inbox.iterdir(), key=lambda q: (
        (man.get(q.name) or {}).get("created") or "9999", q.name))
    for p in order:
        if not p.is_file() or p.name.startswith("."):
            continue
        if p.suffix.lower() == ".md":
            out["ignored"].append(p.name)
            continue
        if p.suffix.lower() not in (".yaml", ".yml"):
            continue
        raw = p.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        if _seen(ledger, p.name, sha):
            continue
        meta = man.get(p.name)
        if meta is None:
            # Not refused: the sweep lists the folder before it copies, so a file
            # that landed between the two waits for the next night's listing.
            out["waiting"].append(f"{p.name}: no manifest entry yet")
            continue
        doc, why = check_file(raw, meta)
        bid = doc.get("batch_id") if isinstance(doc, dict) else None
        if not why and bid and reg.batch(bid):
            why.append(f"a duplicate batch_id: {bid} is already registered")
        created = (meta or {}).get("created")
        modified = (meta or {}).get("modified")
        if why:
            _log(ledger, p.name, sha, "refused", "; ".join(why), as_of, bid,
                 created, modified)
            ledger.event("inbox", "batch_refused", as_of, None,
                         after={"file": p.name, "sha256": sha, "why": why})
            out["refused"].append({"file": p.name, "why": why})
            continue
        res = intake.admit(ledger, store, doc, created, as_of, p.name, sha, created,
                           modified, translations_root)
        _log(ledger, p.name, sha, "ingested",
             f"{len(res['registered'])} registered, {len(res['refused'])} refused",
             as_of, bid, created, modified)
        ledger.event("inbox", "batch_ingested", as_of, None,
                     after={"file": p.name, "sha256": sha, "batch_id": bid,
                            "pre_registered_at": created, **res})
        out["ingested"].append({"file": p.name, **res})
    return out
