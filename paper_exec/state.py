"""
The executor's state files, under the state directory (config.state_dir):

  kill        the operator's (or anyone's) stop: its presence stops all sending
  killed      written the first time `kill` is seen; STICKY: removing `kill` does
              not clear it -- only the operator's clear-kill does, with a reason
  reconcile   the last reconciliation's mismatches; present = sending stopped
  pause-<engine>.json   an edge-decay pause with its figures; never cleared here
  orders.jsonl          every bracket built (dry) or sent: the executor's order log
  cleared.jsonl         each operator clear-kill, with its reason
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Optional


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


class State:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def _p(self, name: str) -> Path:
        return self.root / name

    def _write(self, name: str, doc: dict) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        p = self._p(name)
        p.write_text(json.dumps(doc, sort_keys=True, indent=1), encoding="utf-8")
        return p

    def _append(self, name: str, doc: dict) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with open(self._p(name), "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(doc, sort_keys=True, default=str) + "\n")

    # -- the kill switch (sticky) -------------------------------------------
    def killed(self) -> Optional[dict]:
        """The kill state: `killed` if written; a fresh `kill` file writes it."""
        k = self._p("killed")
        if k.exists():
            return json.loads(k.read_text(encoding="utf-8") or "{}")
        if self._p("kill").exists():
            doc = {"at": now(), "by": "the kill file",
                   "note": self._p("kill").read_text(encoding="utf-8").strip()[:200]}
            self._write("killed", doc)
            return doc
        return None

    def clear_kill(self, reason: str) -> bool:
        """The operator's clear: removes both files and records the reason."""
        if not reason or not reason.strip():
            raise ValueError("a clear-kill carries the operator's reason")
        was = self._p("killed").exists() or self._p("kill").exists()
        for n in ("kill", "killed"):
            self._p(n).unlink(missing_ok=True)
        self._append("cleared.jsonl", {"at": now(), "reason": reason.strip()})
        return was

    # -- reconciliation ------------------------------------------------------
    def set_reconcile(self, mismatches: list[str]) -> None:
        if mismatches:
            self._write("reconcile", {"at": now(), "mismatches": mismatches})
        else:
            self._p("reconcile").unlink(missing_ok=True)

    def reconcile_block(self) -> Optional[dict]:
        p = self._p("reconcile")
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    # -- the edge-decay pause (never cleared here) --------------------------
    def pause(self, engine_id: str) -> Optional[dict]:
        p = self._p(f"pause-{engine_id}.json")
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    def set_pause(self, engine_id: str, doc: dict) -> Path:
        if self.pause(engine_id):
            return self._p(f"pause-{engine_id}.json")
        return self._write(f"pause-{engine_id}.json", {"at": now(), **doc})

    def pauses(self) -> dict[str, dict]:
        out = {}
        if self.root.is_dir():
            for p in sorted(self.root.glob("pause-*.json")):
                out[p.stem[len("pause-"):]] = json.loads(p.read_text(encoding="utf-8"))
        return out

    # -- the order log -------------------------------------------------------
    def log_order(self, doc: dict) -> None:
        self._append("orders.jsonl", {"at": now(), **doc})

    def orders(self) -> list[dict]:
        p = self._p("orders.jsonl")
        if not p.exists():
            return []
        return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
