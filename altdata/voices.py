"""
The voices register -- who said what about the market, where, and when.

    python -m altdata.voices list [--days 30]
    python -m altdata.voices status --end 2026-10-04 --cadence weekly
    python -m altdata.voices seed                 # config/voices_sources.yaml seeds
    python -m altdata.voices runs                 # the latest scan run per source

Phase B, pulled forward and ruled 4 Oct 2026 (docs/briefs/monthly-v2-brief-2026-
10-01.md, Phase B and the Rules; reporting-stack brief section 1, row 8; the J.P.
Morgan GTM change order's voices entry). The scan that fills it is
altdata/sources/voices_scan.py, run once a day in the 06:45 overnight fetch.

-----------------------------------------------------------------------------
NO STORED SOURCE, NOT PRINTED
-----------------------------------------------------------------------------
A row is a voice's view as one paraphrased line, with the URL it came from, the
date it was published, the instant we retrieved it and the outlet's tier. A row
without a source URL, a published date, a retrieval instant or a tier is REFUSED
AT WRITE (`VoiceError`), and the schema refuses it again underneath, so a bug in a
writer cannot store an unsourced voice. The article body is never stored: the scan
reads it in memory, the model paraphrases it, and the paraphrase and the URL are
what remain.

-----------------------------------------------------------------------------
STATUS IS COMPUTED, NEVER DECLARED
-----------------------------------------------------------------------------
The model returns directions -- bullish, bearish or neutral on a DECLARED subject
(config/voices_sources.yaml `subjects`). It never returns a status. Status is
computed here, from stored rows only, per voice and subject, against a window:

    NEW          no earlier entry from this voice on any subject it names now
    REITERATED   an earlier entry on the same subject, in the same direction
    INFLECTED    an earlier entry on the same subject, in a different direction
    SILENT       an entry in the prior window and none in this one
    UNREACHABLE  as SILENT, but the voice's source could not be read on the
                 latest run -- silence is not inferred from a source we could
                 not read

A voice's status is INFLECTED if any of its subjects inflected, else REITERATED
if any reiterated, else NEW. "Earlier" is the voice's latest entry published
before the window opens, at any distance; "the prior window" is the one window
before (the prior week for the Weekly, the prior month for the Monthly). Only
rows retrieved at or before the cutoff count, so a status recomputed later from
the same rows is the same status.

-----------------------------------------------------------------------------
NARRATIVE EVIDENCE
-----------------------------------------------------------------------------
Each item the model says bears on one of the register's stories is written as an
evidence row -- for or against, with its own source -- directly, because evidence
is a record of what was published, not a state. The story's STATE still moves
only by the register's declared rules, and a new story is still only a proposal
under the operator's gate (altdata/narratives.py).
"""

from __future__ import annotations

import datetime as dt
import json
import re
import sqlite3
from pathlib import Path
from typing import Any, Iterable, Optional

from . import observations, session

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "config" / "voices_sources.yaml"

STATUSES = ("NEW", "REITERATED", "INFLECTED", "SILENT", "UNREACHABLE")
SIDES = ("for", "against")
QUOTE_MAX_WORDS = 14            # "at most one quote under 15 words"

SCHEMA = """
CREATE TABLE IF NOT EXISTS voices (
    id            INTEGER PRIMARY KEY,
    voice         TEXT NOT NULL,
    voice_key     TEXT NOT NULL,
    affiliation   TEXT NOT NULL,
    kind          TEXT NOT NULL,
    view          TEXT NOT NULL,
    quote         TEXT,
    directions    TEXT NOT NULL DEFAULT '[]',
    horizon       TEXT,
    source_id     TEXT NOT NULL,
    outlet        TEXT NOT NULL,
    source_url    TEXT NOT NULL CHECK (length(source_url) > 10
                                      AND source_url LIKE 'http%'),
    title         TEXT,
    published_at  TEXT NOT NULL CHECK (length(published_at) >= 10),
    retrieved_at  TEXT NOT NULL CHECK (length(retrieved_at) >= 10),
    tier          INTEGER NOT NULL CHECK (tier IN (1, 2, 3)),
    origin        TEXT NOT NULL,
    model         TEXT,
    run_id        TEXT,
    created_at    TEXT NOT NULL,
    CHECK (kind IN ('sell_side', 'buy_side', 'independent', 'official')),
    UNIQUE (voice_key, source_url)
);
CREATE INDEX IF NOT EXISTS voices_pub ON voices (published_at);

-- A STORED VIEW IS THE RECORD. Status is computed against it, so an edited row
-- would rewrite every status computed from it.
CREATE TRIGGER IF NOT EXISTS voices_immutable
BEFORE UPDATE ON voices
BEGIN SELECT RAISE(ABORT, 'a stored voice is the record; it is never edited'); END;
CREATE TRIGGER IF NOT EXISTS voices_no_delete
BEFORE DELETE ON voices
BEGIN SELECT RAISE(ABORT, 'a stored voice is the record; it is never deleted'); END;

CREATE TABLE IF NOT EXISTS narrative_evidence (
    id            INTEGER PRIMARY KEY,
    narrative_id  TEXT NOT NULL,
    side          TEXT NOT NULL CHECK (side IN ('for', 'against')),
    voice_id      INTEGER NOT NULL REFERENCES voices(id),
    summary       TEXT NOT NULL,
    outlet        TEXT NOT NULL,
    source_url    TEXT NOT NULL CHECK (length(source_url) > 10
                                      AND source_url LIKE 'http%'),
    published_at  TEXT NOT NULL,
    retrieved_at  TEXT NOT NULL,
    tier          INTEGER NOT NULL,
    created_at    TEXT NOT NULL,
    UNIQUE (narrative_id, voice_id)
);
CREATE INDEX IF NOT EXISTS narrative_evidence_pub
    ON narrative_evidence (narrative_id, published_at);

-- EVERY ITEM THE SCAN HAS LOOKED AT, so a model call is spent once per item and
-- never again. `status` says what became of it.
CREATE TABLE IF NOT EXISTS voice_scan_seen (
    source_id     TEXT NOT NULL,
    item_url      TEXT NOT NULL,
    first_seen    TEXT NOT NULL,
    status        TEXT NOT NULL,
    published_at  TEXT,
    title         TEXT,
    reason        TEXT,
    PRIMARY KEY (source_id, item_url)
);

-- 13F POSITIONING, where a voice's firm files one (SEC EDGAR, through the
-- EDGAR contact). One row per filing; dated to its PERIOD OF REPORT, never to the
-- filing date. `edgar_name` is EDGAR's own name for the CIK, stored so a mapping
-- that points at the wrong filer shows rather than prints quietly.
CREATE TABLE IF NOT EXISTS voice_13f (
    accession      TEXT PRIMARY KEY,
    affiliation    TEXT NOT NULL,
    cik            TEXT NOT NULL,
    edgar_name     TEXT,
    expected_name  TEXT,
    form           TEXT NOT NULL,
    period_of_report TEXT NOT NULL,
    filed          TEXT NOT NULL,
    source_url     TEXT NOT NULL CHECK (source_url LIKE 'http%'),
    retrieved_at   TEXT NOT NULL
);

-- ONE ROW PER SOURCE PER RUN: what the reports print as "unreachable".
CREATE TABLE IF NOT EXISTS voice_scan_runs (
    id            INTEGER PRIMARY KEY,
    run_id        TEXT NOT NULL,
    source_id     TEXT NOT NULL,
    source_name   TEXT NOT NULL,
    started_at    TEXT NOT NULL,
    state         TEXT NOT NULL,
    reason        TEXT,
    candidates    INTEGER NOT NULL DEFAULT 0,
    new_items     INTEGER NOT NULL DEFAULT 0,
    extracted     INTEGER NOT NULL DEFAULT 0,
    voices        INTEGER NOT NULL DEFAULT 0,
    model_calls   INTEGER NOT NULL DEFAULT 0,
    UNIQUE (run_id, source_id)
);
"""

# States a run row may carry. `ok` is the only one that means the source was read.
RUN_STATES = ("ok", "unreachable", "robots_disallowed", "not_configured")


class VoiceError(ValueError):
    """A write the register refuses. The message says why."""


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
_CFG: Optional[dict] = None


def load_config(path: Optional[Path] = None) -> dict:
    global _CFG
    if _CFG is not None and path is None:
        return _CFG
    import yaml  # noqa: PLC0415
    cfg = yaml.safe_load((path or CONFIG_PATH).read_text(encoding="utf-8")) or {}
    if path is None:
        _CFG = cfg
    return cfg


def subjects(cfg: Optional[dict] = None) -> dict:
    return (cfg or load_config()).get("subjects") or {}


def subject_label(sid: str, cfg: Optional[dict] = None) -> str:
    return str((subjects(cfg).get(sid) or {}).get("label") or sid)


def voice_key(voice: str, affiliation: str) -> str:
    """One voice across rows: the person (or desk) at the firm, case- and
    punctuation-blind, so "Goldman Sachs Research" on two days is one voice."""
    def slug(s: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", str(s or "").lower()).strip("-")
    return f"{slug(voice)}@{slug(affiliation)}"


def _iso(v: Any) -> Optional[str]:
    s = str(v or "").strip()
    if not s:
        return None
    try:
        if len(s) == 10:
            dt.date.fromisoformat(s)
            return s
        d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=dt.timezone.utc)
        return d.astimezone(dt.timezone.utc).isoformat()
    except ValueError:
        return None


def validate(row: dict, cfg: Optional[dict] = None,
             stories: Optional[Iterable[str]] = None) -> list[str]:
    """Every reason a voice row is not writable. Empty means writable."""
    cfg = cfg or load_config()
    errs: list[str] = []
    url = str(row.get("source_url") or "")
    if not url.startswith("http") or len(url) <= 10:
        errs.append("no source URL -- no stored source, not printed")
    if not _iso(row.get("published_at")):
        errs.append("no published date")
    if not _iso(row.get("retrieved_at")):
        errs.append("no retrieval instant")
    if row.get("tier") not in (1, 2, 3):
        errs.append(f"tier {row.get('tier')!r} is not 1, 2 or 3 -- the outlet is "
                    f"not classified in config/source_tiers.yaml")
    if not str(row.get("voice") or "").strip():
        errs.append("no voice named")
    if not str(row.get("affiliation") or "").strip():
        errs.append("no affiliation")
    if not str(row.get("outlet") or "").strip():
        errs.append("no outlet")
    if row.get("kind") not in (cfg.get("kinds") or {}):
        errs.append(f"kind {row.get('kind')!r} is not one of "
                    f"{list(cfg.get('kinds') or {})}")
    view = str(row.get("view") or "").strip()
    if not view:
        errs.append("no view")
    elif len(view.split()) > 45:
        errs.append(f"view runs {len(view.split())} words; one line is 45 at most")
    q = row.get("quote")
    if q and len(str(q).split()) > QUOTE_MAX_WORDS:
        errs.append(f"quote runs {len(str(q).split())} words; under 15 is the rule")
    subj = subjects(cfg)
    dirs = set(cfg.get("directions") or ())
    for d in row.get("directions") or []:
        if d.get("subject") not in subj:
            errs.append(f"subject {d.get('subject')!r} is not declared")
        if d.get("direction") not in dirs:
            errs.append(f"direction {d.get('direction')!r} is not one of {sorted(dirs)}")
    if stories is not None:
        known = set(stories)
        for e in row.get("stories") or []:
            if e.get("story") not in known:
                errs.append(f"story {e.get('story')!r} is not in the register")
            if e.get("side") not in SIDES:
                errs.append(f"story side {e.get('side')!r} is not for/against")
    return errs


# ---------------------------------------------------------------------------
# The store
# ---------------------------------------------------------------------------
class VoicesStore:
    """The voices tables, in the same database as the observations."""

    def __init__(self, path: Optional[str] = None, readonly: bool = False) -> None:
        """`readonly` is how every REPORT opens it: no schema is created and no
        row can be written, so rendering never touches the store. Before the
        scan's first run the tables do not exist, and every read is empty."""
        self.path = Path(path or observations.DEFAULT_DB)
        self.readonly = readonly
        if readonly:
            if not self.path.exists():
                self.conn = sqlite3.connect(":memory:")
            else:
                self.conn = sqlite3.connect(
                    f"{self.path.resolve().as_uri()}?mode=ro", uri=True)
            self.conn.row_factory = sqlite3.Row
            have = {r[0] for r in self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'")}
            if "voices" not in have:
                # An empty schema in memory, so reads answer "nothing" rather
                # than fault on a store the scan has not reached yet.
                self.conn.close()
                self.conn = sqlite3.connect(":memory:")
                self.conn.row_factory = sqlite3.Row
                self.conn.executescript(SCHEMA)
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.execute("PRAGMA busy_timeout = 5000")
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "VoicesStore":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # -- write --------------------------------------------------------------
    def write(self, row: dict, *, cfg: Optional[dict] = None,
              stories: Optional[Iterable[str]] = None) -> dict:
        """One voice and its evidence rows. Raises VoiceError on any refusal;
        a duplicate (same voice, same URL) is a no-op that returns its id."""
        cfg = cfg or load_config()
        errs = validate(row, cfg, stories)
        if errs:
            raise VoiceError("; ".join(errs))
        key = voice_key(row["voice"], row["affiliation"])
        now = session.utc_iso()
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO voices (voice, voice_key, affiliation, kind, "
            " view, quote, directions, horizon, source_id, outlet, source_url, "
            " title, published_at, retrieved_at, tier, origin, model, run_id, "
            " created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (row["voice"].strip(), key, row["affiliation"].strip(), row["kind"],
             row["view"].strip(), (row.get("quote") or None),
             json.dumps(row.get("directions") or [], sort_keys=True),
             row.get("horizon"), row.get("source_id") or "manual",
             row["outlet"], row["source_url"], row.get("title"),
             _iso(row["published_at"]), _iso(row["retrieved_at"]),
             int(row["tier"]), row.get("origin") or "scan", row.get("model"),
             row.get("run_id"), now))
        if not cur.rowcount:
            vid = self.conn.execute(
                "SELECT id FROM voices WHERE voice_key = ? AND source_url = ?",
                (key, row["source_url"])).fetchone()[0]
            self.conn.commit()
            return {"id": vid, "inserted": False, "evidence": 0}
        vid = cur.lastrowid
        n_ev = 0
        for e in row.get("stories") or []:
            n_ev += self.conn.execute(
                "INSERT OR IGNORE INTO narrative_evidence (narrative_id, side, "
                " voice_id, summary, outlet, source_url, published_at, "
                " retrieved_at, tier, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (e["story"], e["side"], vid, row["view"].strip(), row["outlet"],
                 row["source_url"], _iso(row["published_at"]),
                 _iso(row["retrieved_at"]), int(row["tier"]), now)).rowcount
        self.conn.commit()
        return {"id": vid, "inserted": True, "evidence": n_ev}

    def mark_seen(self, source_id: str, url: str, status: str, *,
                  published_at: Optional[str] = None, title: Optional[str] = None,
                  reason: Optional[str] = None) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO voice_scan_seen (source_id, item_url, "
            " first_seen, status, published_at, title, reason) VALUES "
            " (?, ?, COALESCE((SELECT first_seen FROM voice_scan_seen WHERE "
            "  source_id = ? AND item_url = ?), ?), ?, ?, ?, ?)",
            (source_id, url, source_id, url, session.utc_iso(), status,
             published_at, (title or "")[:300] or None, (reason or "")[:300] or None))
        self.conn.commit()

    def seen(self, source_id: str, url: str) -> bool:
        return self.conn.execute(
            "SELECT 1 FROM voice_scan_seen WHERE source_id = ? AND item_url = ?",
            (source_id, url)).fetchone() is not None

    def record_run(self, run_id: str, source_id: str, source_name: str,
                   state: str, reason: Optional[str] = None, **counts: int) -> None:
        if state not in RUN_STATES:
            raise VoiceError(f"run state {state!r} is not one of {RUN_STATES}")
        self.conn.execute(
            "INSERT OR REPLACE INTO voice_scan_runs (run_id, source_id, "
            " source_name, started_at, state, reason, candidates, new_items, "
            " extracted, voices, model_calls) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (run_id, source_id, source_name, session.utc_iso(), state,
             (reason or "")[:300] or None, counts.get("candidates", 0),
             counts.get("new_items", 0), counts.get("extracted", 0),
             counts.get("voices", 0), counts.get("model_calls", 0)))
        self.conn.commit()

    def model_calls_on(self, day: str) -> int:
        r = self.conn.execute(
            "SELECT COALESCE(SUM(model_calls), 0) FROM voice_scan_runs "
            "WHERE substr(started_at, 1, 10) = ?", (day,)).fetchone()
        return int(r[0] or 0)

    def write_13f(self, row: dict) -> bool:
        for k in ("accession", "affiliation", "cik", "form", "period_of_report",
                  "filed", "source_url", "retrieved_at"):
            if not row.get(k):
                raise VoiceError(f"13F row has no {k} -- no stored source, not printed")
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO voice_13f (accession, affiliation, cik, "
            " edgar_name, expected_name, form, period_of_report, filed, "
            " source_url, retrieved_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            tuple(row.get(k) for k in ("accession", "affiliation", "cik",
                                       "edgar_name", "expected_name", "form",
                                       "period_of_report", "filed", "source_url",
                                       "retrieved_at")))
        self.conn.commit()
        return bool(cur.rowcount)

    def latest_13f(self, affiliation_key: str, on_or_before: str,
                   as_of: Optional[str] = None) -> Optional[dict]:
        q = ("SELECT * FROM voice_13f WHERE affiliation = ? AND period_of_report <= ?"
             + (" AND retrieved_at <= ?" if as_of else "")
             + " ORDER BY period_of_report DESC, filed DESC LIMIT 1")
        args = [affiliation_key, on_or_before] + ([as_of] if as_of else [])
        r = self.conn.execute(q, args).fetchone()
        return dict(r) if r else None

    # -- read ---------------------------------------------------------------
    def rows(self, *, as_of: Optional[str] = None, since: Optional[str] = None,
             until: Optional[str] = None) -> list[dict]:
        """Voices knowable at `as_of`, published in [since, until)."""
        q = "SELECT * FROM voices WHERE 1=1"
        args: list = []
        if as_of:
            q += " AND retrieved_at <= ?"
            args.append(as_of)
        if since:
            q += " AND published_at >= ?"
            args.append(since)
        if until:
            q += " AND published_at < ?"
            args.append(until)
        q += " ORDER BY published_at, id"
        out = []
        for r in self.conn.execute(q, args):
            d = dict(r)
            d["directions"] = json.loads(d.get("directions") or "[]")
            out.append(d)
        return out

    def evidence(self, *, as_of: Optional[str] = None, since: Optional[str] = None,
                 until: Optional[str] = None) -> list[dict]:
        q = ("SELECT e.*, v.voice, v.affiliation, v.kind FROM narrative_evidence e "
             "JOIN voices v ON v.id = e.voice_id WHERE 1=1")
        args: list = []
        if as_of:
            q += " AND e.retrieved_at <= ?"
            args.append(as_of)
        if since:
            q += " AND e.published_at >= ?"
            args.append(since)
        if until:
            q += " AND e.published_at < ?"
            args.append(until)
        q += " ORDER BY e.published_at, e.id"
        return [dict(r) for r in self.conn.execute(q, args)]

    def latest_runs(self, as_of: Optional[str] = None) -> dict[str, dict]:
        """Each source's latest run row at or before `as_of`."""
        q = "SELECT * FROM voice_scan_runs"
        args: list = []
        if as_of:
            q += " WHERE started_at <= ?"
            args.append(as_of)
        q += " ORDER BY started_at, id"
        out: dict[str, dict] = {}
        for r in self.conn.execute(q, args):
            out[r["source_id"]] = dict(r)
        return out


# ---------------------------------------------------------------------------
# Status -- computed from stored rows, never declared
# ---------------------------------------------------------------------------
def windows(end: str, cadence: str) -> tuple[str, str, str]:
    """(prior_start, start, end) as dates, end exclusive. Weekly: the seven days
    to `end` against the seven before. Monthly: the calendar month containing
    the day before `end` against the month before it."""
    e = dt.date.fromisoformat(end[:10])
    if cadence == "weekly":
        s = e - dt.timedelta(days=7)
        return ((s - dt.timedelta(days=7)).isoformat(), s.isoformat(), e.isoformat())
    if cadence == "monthly":
        last = e - dt.timedelta(days=1)
        s = last.replace(day=1)
        ps = (s - dt.timedelta(days=1)).replace(day=1)
        return ps.isoformat(), s.isoformat(), e.isoformat()
    if cadence == "daily":
        s = e - dt.timedelta(days=1)
        return ((s - dt.timedelta(days=1)).isoformat(), s.isoformat(), e.isoformat())
    raise ValueError(f"cadence {cadence!r}")


def compute_status(rows: list[dict], start: str, end: str, prior_start: str,
                   runs: Optional[dict] = None) -> list[dict]:
    """One entry per voice: its status, its latest view in the window, and the
    per-subject comparison that decided it. A pure function of `rows` (already
    filtered to what was knowable at the cutoff) -- the gate recomputes it."""
    runs = runs or {}
    by: dict[str, list[dict]] = {}
    for r in rows:
        by.setdefault(r["voice_key"], []).append(r)
    out = []
    for key, rs in by.items():
        rs = sorted(rs, key=lambda r: (str(r["published_at"]), r["id"]))
        cur = [r for r in rs if start <= str(r["published_at"])[:10] < end]
        before = [r for r in rs if str(r["published_at"])[:10] < start]
        prior_win = [r for r in before if str(r["published_at"])[:10] >= prior_start]
        if not cur:
            if not prior_win:
                continue
            last = prior_win[-1]
            run = runs.get(last.get("source_id")) or {}
            st = ("UNREACHABLE" if run.get("state") not in (None, "ok")
                  else "SILENT")
            out.append({"voice_key": key, "status": st, "row": last,
                        "subjects": [], "source_state": run.get("state"),
                        "source_name": run.get("source_name")})
            continue
        latest = cur[-1]
        # The voice's view on each subject as it stood before the window opened.
        was: dict[str, str] = {}
        for r in before:
            for d in r.get("directions") or []:
                was[d["subject"]] = d["direction"]
        # And its view on each subject now: the latest entry in the window wins.
        now: dict[str, str] = {}
        for r in cur:
            for d in r.get("directions") or []:
                now[d["subject"]] = d["direction"]
        subj = []
        for s, d in sorted(now.items()):
            if s not in was:
                subj.append({"subject": s, "status": "NEW", "now": d})
            elif was[s] == d:
                subj.append({"subject": s, "status": "REITERATED", "now": d})
            else:
                subj.append({"subject": s, "status": "INFLECTED", "now": d,
                             "was": was[s]})
        sts = {x["status"] for x in subj}
        if "INFLECTED" in sts:
            st = "INFLECTED"
        elif "REITERATED" in sts:
            st = "REITERATED"
        elif before and not now:
            # Spoke before and now, but on nothing declared: the same voice
            # speaking again, with no direction to compare.
            st = "REITERATED"
        else:
            st = "NEW"
        out.append({"voice_key": key, "status": st, "row": latest,
                    "subjects": subj, "entries_in_window": len(cur)})
    order = {s: i for i, s in enumerate(("INFLECTED", "NEW", "REITERATED",
                                          "SILENT", "UNREACHABLE"))}
    out.sort(key=lambda x: (order[x["status"]], -int(x["row"].get("tier") == 1),
                            str(x["row"].get("voice"))))
    return out


def status_table(end: str, cadence: str, as_of: Optional[str] = None,
                 db_path: Optional[str] = None) -> dict:
    """The voices table for a report: rows, each with its computed status."""
    ps, s, e = windows(end, cadence)
    with VoicesStore(db_path, readonly=True) as vs:
        rows = vs.rows(as_of=as_of)
        runs = vs.latest_runs(as_of)
    return {"cadence": cadence, "prior_start": ps, "start": s, "end": e,
            "as_of": as_of, "voices": compute_status(rows, s, e, ps, runs),
            "unreachable": sorted({r["source_name"] for r in runs.values()
                                   if r["state"] in ("unreachable",
                                                     "robots_disallowed")}),
            "not_configured": sorted({r["source_name"] for r in runs.values()
                                      if r["state"] == "not_configured"})}


# ---------------------------------------------------------------------------
# Seeds
# ---------------------------------------------------------------------------
def filer_for(affiliation: str, cfg: Optional[dict] = None) -> Optional[str]:
    """The `filers_13f` key a voice's affiliation belongs to, or None. A key
    matches when it opens the affiliation ("BlackRock" covers "BlackRock
    Investment Institute"); the longest such key wins."""
    a = str(affiliation or "").lower()
    keys = [k for k in ((cfg or load_config()).get("filers_13f") or {})
            if a.startswith(k.lower())]
    return max(keys, key=len) if keys else None


def seed(db_path: Optional[str] = None, cfg: Optional[dict] = None) -> dict:
    """Write the declared seed entries (config `seeds`). Idempotent: the unique
    (voice, URL) key makes a second run a no-op."""
    from . import source_tiers  # noqa: PLC0415
    cfg = cfg or load_config()
    out = {"written": 0, "present": 0, "refused": []}
    with VoicesStore(db_path) as vs:
        for s in cfg.get("seeds") or []:
            row = dict(s)
            row["tier"] = source_tiers.tier_of(f"x - {row.get('outlet')}")
            row.setdefault("origin", "seed")
            row.setdefault("source_id", "seed")
            try:
                r = vs.write(row, cfg=cfg)
            except VoiceError as exc:
                out["refused"].append({"voice": row.get("voice"), "reason": str(exc)})
                continue
            out["written" if r["inserted"] else "present"] += 1
    return out


def _main(argv: list[str]) -> int:
    import argparse  # noqa: PLC0415
    p = argparse.ArgumentParser(description="The voices register.")
    sub = p.add_subparsers(dest="cmd", required=True)
    ls = sub.add_parser("list")
    ls.add_argument("--days", type=int, default=30)
    stp = sub.add_parser("status")
    stp.add_argument("--end", default=dt.date.today().isoformat())
    stp.add_argument("--cadence", default="weekly",
                     choices=("daily", "weekly", "monthly"))
    sub.add_parser("seed")
    sub.add_parser("runs")
    a = p.parse_args(argv)
    if a.cmd == "seed":
        print(json.dumps(seed(), indent=2))
        return 0
    if a.cmd == "runs":
        with VoicesStore() as vs:
            for sid, r in sorted(vs.latest_runs().items()):
                print(f"{r['started_at'][:16]}  {sid:<26}{r['state']:<18}"
                      f"cand={r['candidates']:<4} new={r['new_items']:<4} "
                      f"voices={r['voices']:<3} {r.get('reason') or ''}")
        return 0
    if a.cmd == "list":
        since = (dt.date.today() - dt.timedelta(days=a.days)).isoformat()
        with VoicesStore() as vs:
            for r in vs.rows(since=since):
                dirs = ", ".join(f"{d['subject']} {d['direction']}"
                                 for d in r["directions"])
                print(f"{r['published_at'][:10]}  {r['voice']} ({r['affiliation']}, "
                      f"tier {r['tier']}): {r['view']} [{dirs}] {r['source_url']}")
        return 0
    t = status_table(a.end, a.cadence)
    for v in t["voices"]:
        print(f"{v['status']:<12}{v['row']['voice']} -- {v['row']['view'][:90]}")
    if t["unreachable"]:
        print("unreachable: " + ", ".join(t["unreachable"]))
    return 0


if __name__ == "__main__":                                     # pragma: no cover
    import sys
    raise SystemExit(_main(sys.argv[1:]))
