"""
THE MECHANISM-WATCH REGISTER (ST-15's store table, read by ST-14's Monthly part;
st-t5-render, 18 Oct 2026). The order's 2.7.7 schema, in the observation store's
database (the "mechanism_watch store table"):

    python -m altdata.mechanism_watch review                 # read only
    python -m altdata.mechanism_watch promote MW-0001 --reason TEXT [--confirm]
    python -m altdata.mechanism_watch reject  MW-0001 --reason TEXT [--confirm]
    python -m altdata.mechanism_watch render [--out docs/mechanism-watch-register.md]

  mechanism_watch          one row a candidate: id, name, canonical_id,
                           mechanism_class, whats_new, team_or_paper, stage,
                           materiality_evidence, key_risk, grade, status
                           (CANDIDATE / WATCH / REJECTED / PROMOTED), first_seen,
                           last_reviewed, sources -- and `draft`, 1 while any
                           field is a model's and unconfirmed (rule 31)
  mechanism_watch_status   every status change: who, when, from, to, why
  mechanism_watch_entries  the narrative-register entries the scan drafts
                           (date, class mechanism-watch, factor I or V, grade,
                           <= 60 words, source), held here as DRAFTS: the
                           narrative register's grade scale is not in the repo
                           (G-29), so nothing is posted to it and the grade
                           reads "awaiting G-29"

ONLY A HUMAN CHANGES A STATUS (MW-6). `promote` (to WATCH) and `reject` print what
they would do and write only with `--confirm`, which is the operator's flag, as the
narrative register's confirm and reject are; nothing auto-promotes. A rejected
candidate is kept, so it is not surfaced again. PROMOTE does not create the
Security Master entry: that file is reviewed by the operator (AUD-3b), and the
command prints the entry to add.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger(__name__)

STATUSES = ("CANDIDATE", "WATCH", "REJECTED", "PROMOTED")
STAGES = ("paper", "testnet", "mainnet")
GRADE_PENDING = "awaiting G-29"
MAX_ENTRY_WORDS = 60
FIELDS = ("name", "canonical_id", "mechanism_class", "whats_new", "team_or_paper",
          "stage", "materiality_evidence", "key_risk", "grade", "status",
          "first_seen", "last_reviewed", "sources")

SCHEMA = """
CREATE TABLE IF NOT EXISTS mechanism_watch (
    id                   TEXT PRIMARY KEY,
    name                 TEXT NOT NULL,
    canonical_id         TEXT,
    mechanism_class      TEXT,
    whats_new            TEXT,
    team_or_paper        TEXT,
    stage                TEXT,
    materiality_evidence TEXT,
    key_risk             TEXT,
    grade                TEXT NOT NULL,
    status               TEXT NOT NULL CHECK (status IN
                             ('CANDIDATE','WATCH','REJECTED','PROMOTED')),
    first_seen           TEXT NOT NULL,
    last_reviewed        TEXT,
    sources              TEXT NOT NULL DEFAULT '[]',
    draft                INTEGER NOT NULL DEFAULT 1,
    origin               TEXT NOT NULL,
    prefilter            TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS mechanism_watch_status (
    id          INTEGER PRIMARY KEY,
    mw_id       TEXT NOT NULL,
    at          TEXT NOT NULL,
    from_status TEXT,
    to_status   TEXT NOT NULL,
    by          TEXT NOT NULL,
    reason      TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS mechanism_watch_entries (
    id      INTEGER PRIMARY KEY,
    at      TEXT NOT NULL,
    mw_id   TEXT,
    cls     TEXT NOT NULL DEFAULT 'mechanism-watch',
    factor  TEXT NOT NULL CHECK (factor IN ('I','V')),
    grade   TEXT NOT NULL,
    text    TEXT NOT NULL,
    source  TEXT NOT NULL,
    draft   INTEGER NOT NULL DEFAULT 1
);
"""


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


class Register:
    def __init__(self, path: Optional[str] = None, readonly: bool = False) -> None:
        from . import observations                              # noqa: PLC0415
        self.path = str(path or observations.DEFAULT_DB)
        if readonly:
            if not Path(self.path).exists():
                raise FileNotFoundError(self.path)
            self.conn = sqlite3.connect(f"file:{Path(self.path).as_posix()}?mode=ro",
                                        uri=True)
        else:
            self.conn = sqlite3.connect(self.path)
            self.conn.executescript(SCHEMA)
        self.conn.row_factory = sqlite3.Row
        self.readonly = readonly

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "Register":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def _has(self, table: str) -> bool:
        return bool(self.conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone())

    # -- reading --------------------------------------------------------------
    def all(self, status: Optional[str] = None) -> list[dict]:
        if not self._has("mechanism_watch"):
            return []
        q = "SELECT * FROM mechanism_watch" + (" WHERE status=?" if status else "")
        rows = self.conn.execute(q + " ORDER BY id", (status,) if status else ()).fetchall()
        return [dict(r, sources=json.loads(r["sources"] or "[]")) for r in rows]

    def get(self, mw_id: str) -> Optional[dict]:
        return next((r for r in self.all() if r["id"] == mw_id), None)

    def known(self) -> set[str]:
        """Every name and canonical id in the register, any status, lower-cased:
        the dedupe set (a rejected candidate is never surfaced again)."""
        out: set[str] = set()
        for r in self.all():
            out |= {str(x).strip().lower() for x in (r["name"], r["canonical_id"]) if x}
        return out

    def month(self, start: str, end: str) -> dict:
        """The month's activity for the Monthly part (2.7.6 items 4 and 5):
        candidates first seen in (start, end], status changes made, and the
        drafted narrative-register entries."""
        out = {"candidates": [], "changes": [], "entries": []}
        if self._has("mechanism_watch"):
            out["candidates"] = [r for r in self.all() if start < r["first_seen"][:10] <= end]
        if self._has("mechanism_watch_status"):
            out["changes"] = [dict(r) for r in self.conn.execute(
                "SELECT s.*, m.name FROM mechanism_watch_status s LEFT JOIN "
                "mechanism_watch m ON m.id = s.mw_id WHERE substr(s.at,1,10) > ? AND "
                "substr(s.at,1,10) <= ? ORDER BY s.at", (start, end)).fetchall()]
        if self._has("mechanism_watch_entries"):
            out["entries"] = [dict(r) for r in self.conn.execute(
                "SELECT * FROM mechanism_watch_entries WHERE substr(at,1,10) > ? AND "
                "substr(at,1,10) <= ? ORDER BY at", (start, end)).fetchall()]
        return out

    # -- writing (the scan's drafts; the operator's status changes) ------------
    def next_id(self) -> str:
        n = self.conn.execute("SELECT COUNT(*) FROM mechanism_watch").fetchone()[0]
        return f"MW-{n + 1:04d}"

    def add_candidate(self, fields: dict, origin: str, prefilter: dict,
                      at: Optional[str] = None, draft: bool = True) -> str:
        """A CANDIDATE row at the pending grade. The scan's only write to the
        candidate table; a name already known is refused (dedupe)."""
        name = str(fields.get("name") or "").strip()
        if not name:
            raise ValueError("a candidate needs a name")
        known = self.known()
        cid = str(fields.get("canonical_id") or "").strip().lower()
        if name.lower() in known or (cid and cid in known):
            raise ValueError(f"{name}: already in the register")
        if fields.get("stage") not in (None, *STAGES):
            raise ValueError(f"stage {fields.get('stage')!r} is not one of {STAGES}")
        mid = self.next_id()
        at = at or _now()
        self.conn.execute(
            "INSERT INTO mechanism_watch (id, name, canonical_id, mechanism_class, "
            "whats_new, team_or_paper, stage, materiality_evidence, key_risk, grade, "
            "status, first_seen, last_reviewed, sources, draft, origin, prefilter) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (mid, name, fields.get("canonical_id"), fields.get("mechanism_class"),
             fields.get("whats_new"), fields.get("team_or_paper"), fields.get("stage"),
             _text(fields.get("materiality_evidence")), fields.get("key_risk"),
             GRADE_PENDING, "CANDIDATE", at, None,
             json.dumps(list(fields.get("sources") or [])), 1 if draft else 0, origin,
             json.dumps(prefilter, sort_keys=True, default=str)))
        self.conn.execute(
            "INSERT INTO mechanism_watch_status (mw_id, at, from_status, to_status, by, "
            "reason) VALUES (?,?,?,?,?,?)",
            (mid, at, None, "CANDIDATE", origin, "passed the rule pre-filter"))
        self.conn.commit()
        return mid

    def add_entry(self, text: str, factor: str, source: str, mw_id: Optional[str] = None,
                  at: Optional[str] = None) -> int:
        """A DRAFT narrative-register entry (2.7.6 item 5): <= 60 words, factor I
        or V, the pending grade until G-29 is confirmed."""
        n = len(str(text).split())
        if n > MAX_ENTRY_WORDS:
            raise ValueError(f"an entry runs {n} words; at most {MAX_ENTRY_WORDS}")
        if factor not in ("I", "V"):
            raise ValueError(f"factor {factor!r}: I or V")
        cur = self.conn.execute(
            "INSERT INTO mechanism_watch_entries (at, mw_id, factor, grade, text, source, "
            "draft) VALUES (?,?,?,?,?,?,1)",
            (at or _now(), mw_id, factor, GRADE_PENDING, str(text).strip(), source))
        self.conn.commit()
        return int(cur.lastrowid)

    def set_status(self, mw_id: str, to: str, by: str, reason: str,
                   confirm: bool = False, at: Optional[str] = None) -> dict:
        """The operator's status change (MW-6). Without `confirm` it writes
        nothing and returns what it would do."""
        if to not in ("WATCH", "REJECTED"):
            raise ValueError(f"{to}: the CLI promotes to WATCH or rejects; PROMOTED "
                             f"(core coverage, MW-7) is a ruling, not a command")
        r = self.get(mw_id)
        if r is None:
            raise KeyError(mw_id)
        if not reason.strip():
            raise ValueError("a status change needs its reason")
        plan = {"id": mw_id, "name": r["name"], "from": r["status"], "to": to,
                "by": by, "reason": reason, "written": False}
        if to == "WATCH":
            plan["security_master"] = (
                f"add a crypto.watch entry for {r['name']} keyed by its CoinGecko id "
                f"({r.get('canonical_id') or 'unknown'}), with the MW-1 fields, to "
                f"config/security_master.yaml (the operator's file)")
        if not confirm:
            return plan
        at = at or _now()
        self.conn.execute("UPDATE mechanism_watch SET status=?, last_reviewed=? WHERE id=?",
                          (to, at, mw_id))
        self.conn.execute(
            "INSERT INTO mechanism_watch_status (mw_id, at, from_status, to_status, by, "
            "reason) VALUES (?,?,?,?,?,?)", (mw_id, at, r["status"], to, by, reason))
        self.conn.commit()
        return {**plan, "written": True}


def _text(v: Any) -> Optional[str]:
    if v is None:
        return None
    return v if isinstance(v, str) else json.dumps(v, sort_keys=True, default=str)


# ---------------------------------------------------------------------------
# The rendered view (`make mechanism-register`)
# ---------------------------------------------------------------------------
def render(rows: list[dict], entries: Optional[list[dict]] = None,
           as_of: Optional[str] = None) -> str:
    """docs/mechanism-watch-register.md: the register as a table, then the drafted
    entries. A rendered view; never edited by hand."""
    out = ["# Mechanism-watch register", "",
           f"A rendered view of the `mechanism_watch` store table (`make "
           f"mechanism-register`; as of {as_of or _now()[:10]}). Never edited by hand: "
           f"a status changes through `python -m altdata.mechanism_watch promote | "
           f"reject`, the operator's commands. Rows marked draft carry a model's "
           f"fields, unconfirmed (rule 31); grades read \"{GRADE_PENDING}\" until the "
           f"narrative register's scale is confirmed.", ""]
    if not rows:
        out.append("No candidate yet.")
    else:
        out += ["| ID | Name | Mechanism | Stage | Status | Grade | First seen | Draft |",
                "|---|---|---|---|---|---|---|---|"]
        for r in rows:
            out.append(f"| {r['id']} | {r['name']} | {r.get('mechanism_class') or '-'} | "
                       f"{r.get('stage') or '-'} | {r['status']} | {r['grade']} | "
                       f"{r['first_seen'][:10]} | {'yes' if r.get('draft') else 'no'} |")
    if entries:
        out += ["", "## Draft narrative-register entries", ""]
        out += [f"- {e['at'][:10]} · class={e['cls']} · factor={e['factor']} · "
                f"{e['grade']} · {e['text']} · {e['source']}" for e in entries]
    return "\n".join(out) + "\n"


def _main(argv: list[str]) -> int:
    import argparse
    ap = argparse.ArgumentParser(prog="python -m altdata.mechanism_watch")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("review")
    for c in ("promote", "reject"):
        s = sub.add_parser(c)
        s.add_argument("id")
        s.add_argument("--reason", required=True)
        s.add_argument("--confirm", action="store_true",
                       help="the operator's flag: without it nothing is written")
    r = sub.add_parser("render")
    r.add_argument("--out", default=None)
    ap.add_argument("--db", default=None)
    a = ap.parse_args(argv)
    if a.cmd in ("review", "render"):
        try:
            reg = Register(a.db, readonly=True)
        except FileNotFoundError:
            print("no store yet")
            return 0
        with reg:
            rows = reg.all()
            ents = reg.month("0000-00-00", "9999-12-31")["entries"]
        if a.cmd == "review":
            print(json.dumps(rows, indent=2, default=str))
            return 0
        md = render(rows, ents)
        if a.out:
            Path(a.out).write_text(md, encoding="utf-8")
            print(f"wrote {a.out}")
        else:
            print(md)
        return 0
    with Register(a.db) as reg:
        res = reg.set_status(a.id, "WATCH" if a.cmd == "promote" else "REJECTED",
                             by="operator", reason=a.reason,
                             confirm=a.confirm)
    print(json.dumps(res, indent=2))
    if not a.confirm:
        print("nothing written: add --confirm (the operator's flag) to record it")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(_main(sys.argv[1:]))
