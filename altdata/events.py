"""
The events table: what happened, what is scheduled, and when we could know it.

    from altdata.events import EventStore, Event
    with EventStore() as ev:
        ev.write_many([Event(...)])
        rows = ev.since("2026-09-24T20:00:00Z", as_of="2026-09-25T11:00:00Z")
        cal = ev.calendar("2026-09-25", "2026-10-02")

    python -m altdata.events summary
    python -m altdata.events show --type release --since 2026-09-01

-----------------------------------------------------------------------------
INGESTED, NOT FETCHED AT RENDER
-----------------------------------------------------------------------------

This table exists so that no report searches for anything. The 07:00 anchor reads
stored rows; the ingest passes (06:45 overnight, 16:10 EOD) are the only writers.
The rule is not about politeness to a feed, it is about what a report IS: a render
that fetches has a different answer every time it runs, cannot be replayed, and
fails in a way that looks like the market being quiet. `tools/validate_events.py`
greps the render modules for a network call and asserts a runtime guard.

-----------------------------------------------------------------------------
THE THREE CLOCKS, AND THE ONE THAT IS DELIBERATELY PESSIMISTIC
-----------------------------------------------------------------------------

`observed_at`   WHEN THE EVENT IS. For something that happened, its own timestamp
                -- the release time, the filing time, the story's publication. For
                a scheduled item, the future instant it is scheduled FOR, which is
                why a calendar is just this table read forwards.
`available_at`  WHEN THIS SYSTEM COULD HAVE KNOWN IT: the ingest instant. NOT the
                publication time, even where the feed states one to the second.
                A story published at 09:00 and pulled at 16:10 was not knowable
                here at 09:00, and an as-of query that said otherwise would let a
                backtest read the morning's news before the pass that fetched it.
                The publication time is kept in `payload.published_at` for anyone
                measuring latency; it is not a clock this table joins on.
`ingested_at`   The write instant. Equal to available_at for a live pull and
                LATER for a backfill, which is the pair that makes a backfill
                honest rather than a way of inventing foreknowledge.

So `availability_kind` is `ingest_instant` for everything here. Nothing in this
table is `observed` in the store's sense -- that kind is reserved for a source
that states when a value became public -- and nothing is `reconstructed`, because
reconstruction is permitted only where `revision_policy` is never/split_only and a
plausible earlier availability can be argued. For an event we have no such
argument: we know when we pulled it.

-----------------------------------------------------------------------------
DEDUPE IS A CONTENT HASH, AND THE HASH EXCLUDES THE CLOCKS
-----------------------------------------------------------------------------

Every feed here is polled, so the same item arrives repeatedly: an RSS search
returns the same story every hour, and a calendar pull returns the same release
date every day. The hash covers type, observed_at, source, title, url and the
IDENTIFYING part of the payload -- never ingested_at, never available_at, never
the body excerpt (which a feed may reflow). A re-pull is therefore a no-op rather
than a row, and `INSERT OR IGNORE` against a unique index is what enforces it:
dedupe in the schema, not in a loop somebody can forget to write.

WHAT IS *NOT* DEDUPED, on purpose: a scheduled release and the actual that later
lands for it are two rows. They are different facts -- "the print is due Thursday"
and "the print was 3.2%" -- and collapsing them would lose the calendar the moment
it came true.

-----------------------------------------------------------------------------
WHY A TABLE AND NOT OBSERVATIONS
-----------------------------------------------------------------------------

An observation is a NUMBER for a period. An event is a headline, a URL, a body
excerpt and a list of entities, and forcing it into value_text as JSON would make
every entity query a LIKE over a blob. The numbers events produce -- a surprise, a
count -- are written to the observation store as ordinary observations, by the
modules that compute them. This table holds the record; the store holds the
figures derived from it.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Iterable, Optional

from . import session

REPO = Path(__file__).resolve().parent.parent
DEFAULT_DB = os.environ.get("CHESTER_DB") or str(REPO / "data" / "chester.db")

# THE DECLARED VOCABULARY. A type outside this set is a write error rather than a
# new category, for the same reason availability_kind is checked: an unrecognised
# value makes the column unqueryable, and a report that filters on `type` would
# silently miss it.
EVENT_TYPES = ("release", "earnings", "filing", "headline", "session_event",
               "scheduled")

# The column set IS the format. Registered as a bulk block against this constant
# so a new column cannot appear unregistered.
EVENT_COLUMNS = ("id", "content_hash", "type", "observed_at", "available_at",
                 "ingested_at", "source", "title", "body", "url", "payload",
                 "availability_kind")

# A body EXCERPT, not a body. The point of keeping any of it is that a headline
# alone often does not say which way the news cuts; the point of capping it is
# that this table is a record of what happened and not a copy of the internet.
BODY_CHARS = 600

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id            INTEGER PRIMARY KEY,
    content_hash  TEXT NOT NULL,
    type          TEXT NOT NULL,
    observed_at   TEXT NOT NULL,
    available_at  TEXT NOT NULL,
    ingested_at   TEXT NOT NULL,
    source        TEXT NOT NULL,
    title         TEXT NOT NULL,
    body          TEXT,
    url           TEXT,
    payload       TEXT,
    availability_kind TEXT
);

-- DEDUPE IN THE SCHEMA. Every source here is polled, so the same item arrives
-- again and again; INSERT OR IGNORE against this index makes a re-pull cost
-- nothing. A dedupe written as a Python loop is a dedupe one caller forgets.
CREATE UNIQUE INDEX IF NOT EXISTS events_dedupe ON events (content_hash);

-- The two reads this table exists for: "what happened since X" and "what is
-- scheduled between X and Y", both as-of a cutoff.
CREATE INDEX IF NOT EXISTS events_when ON events (observed_at, type);
CREATE INDEX IF NOT EXISTS events_avail ON events (available_at);

-- ENTITIES AS ROWS, not as a JSON array in a column. "Every filing for a symbol
-- in the universe" is the question the anchor asks, and asking it of a blob means
-- a LIKE that matches 'AA' inside 'AAPL'.
CREATE TABLE IF NOT EXISTS event_entities (
    event_id  INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    entity    TEXT NOT NULL,
    PRIMARY KEY (event_id, entity)
);
CREATE INDEX IF NOT EXISTS event_entities_entity ON event_entities (entity);
"""


def content_hash(type_: str, observed_at: str, source: str, title: str,
                 url: Optional[str], key: Optional[str] = None) -> str:
    """The dedupe key: what the item IS, never when we saw it.

    `key` is the source's own identifier where it has one -- a release id, an
    accession number, a story guid -- and it is what makes dedupe survive a feed
    that re-words its own titles. Where a source has no id, the title and url do
    the work and a re-worded title is a second row: visible duplication, which is
    better than a hash that silently swallows a correction.
    """
    parts = [type_, str(observed_at), source, title, url or "", key or ""]
    return hashlib.sha256("\u0000".join(parts).encode("utf-8")).hexdigest()[:32]


class Event:
    """One row, with its hash computed from its own content."""

    __slots__ = ("type", "observed_at", "source", "title", "body", "url",
                 "entities", "payload", "key")

    def __init__(self, type: str, observed_at: str, source: str, title: str,
                 body: Optional[str] = None, url: Optional[str] = None,
                 entities: Optional[Iterable[str]] = None,
                 payload: Optional[dict] = None,
                 key: Optional[str] = None) -> None:
        if type not in EVENT_TYPES:
            raise ValueError(
                f"event type {type!r} is not one of {EVENT_TYPES} -- an "
                f"unrecognised type makes the column unqueryable, and a report "
                f"filtering on it would miss these rows without saying so")
        self.type = type
        self.observed_at = str(observed_at)
        self.source = source
        self.title = (title or "").strip()
        self.body = (body or "").strip()[:BODY_CHARS] or None
        self.url = url
        self.entities = sorted({str(e) for e in (entities or ()) if e})
        self.payload = payload or {}
        self.key = key

    @property
    def content_hash(self) -> str:
        return content_hash(self.type, self.observed_at, self.source,
                            self.title, self.url, self.key)

    def __repr__(self) -> str:                                 # pragma: no cover
        return (f"Event({self.type} {self.observed_at} {self.source} "
                f"{self.title[:40]!r})")


class EventStore:
    """The events table, in the same database as the observations."""

    def __init__(self, path: Optional[str] = None) -> None:
        self.path = Path(path or DEFAULT_DB)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row
        # The same three pragmas the observation store sets, and for the same
        # reason: several timer-driven writers, and a "database is locked" error
        # here would look like a quiet news day.
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.execute("PRAGMA busy_timeout = 5000")
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "EventStore":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # -- write ------------------------------------------------------------
    def write_many(self, events: Iterable[Event],
                   available_at: Optional[str] = None,
                   ingested_at: Optional[str] = None) -> dict:
        """Insert, ignoring what is already here. Returns counts, never raises.

        `available_at` defaults to now, which is the correct default and the whole
        rule: this system could know an event when it pulled it. A backfill may
        pass an earlier instant ONLY if it can argue one, and no source here can.
        """
        now = session.utc_iso()
        avail = available_at or now
        ing = ingested_at or now
        inserted, seen = 0, 0
        for e in events:
            seen += 1
            cur = self.conn.execute(
                "INSERT OR IGNORE INTO events (content_hash, type, observed_at,"
                " available_at, ingested_at, source, title, body, url, payload,"
                " availability_kind)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (e.content_hash, e.type, e.observed_at, avail, ing, e.source,
                 e.title, e.body, e.url,
                 json.dumps(e.payload, sort_keys=True, default=str),
                 "ingest_instant"))
            if not cur.rowcount:
                continue                      # already here; a re-pull is a no-op
            inserted += 1
            eid = cur.lastrowid
            if e.entities:
                self.conn.executemany(
                    "INSERT OR IGNORE INTO event_entities (event_id, entity)"
                    " VALUES (?,?)", [(eid, ent) for ent in e.entities])
        self.conn.commit()
        return {"seen": seen, "inserted": inserted,
                "duplicates": seen - inserted}

    # -- read -------------------------------------------------------------
    def _rows(self, where: str, args: dict) -> list[dict]:
        cur = self.conn.execute(
            "SELECT e.*, (SELECT group_concat(entity) FROM event_entities"
            "              WHERE event_id = e.id) AS entities"
            f"  FROM events e WHERE {where} ORDER BY e.observed_at, e.id", args)
        out = []
        for r in cur.fetchall():
            d = dict(r)
            d["entities"] = [x for x in (d.get("entities") or "").split(",") if x]
            try:
                d["payload"] = json.loads(d.get("payload") or "{}")
            except Exception:                                  # noqa: BLE001
                d["payload"] = {}
            out.append(d)
        return out

    def since(self, since: str, as_of: Optional[str] = None,
              types: Optional[Iterable[str]] = None,
              entity: Optional[str] = None) -> list[dict]:
        """What happened between `since` and `as_of`, knowable at `as_of`.

        BOTH BOUNDS MATTER AND THEY ARE DIFFERENT CLOCKS. `since` bounds the
        event's own time -- "since the previous close" -- and `as_of` bounds what
        this system could know. An item that happened inside the window but was
        ingested after the cutoff is correctly absent: that is what the anchor
        would have had in front of it.
        """
        cutoff = as_of or session.utc_iso()
        where = ["e.observed_at >= :since", "e.observed_at <= :cutoff",
                 "e.available_at <= :cutoff"]
        args: dict[str, Any] = {"since": since, "cutoff": cutoff}
        if types:
            names = list(types)
            where.append("e.type IN (%s)" % ",".join(
                f":t{i}" for i in range(len(names))))
            args.update({f"t{i}": n for i, n in enumerate(names)})
        if entity:
            where.append("EXISTS (SELECT 1 FROM event_entities x"
                         " WHERE x.event_id = e.id AND x.entity = :entity)")
            args["entity"] = entity
        return self._rows(" AND ".join(where), args)

    def calendar(self, first: str, last: str,
                 as_of: Optional[str] = None) -> list[dict]:
        """What is scheduled between two dates, as known at `as_of`.

        The forward half of the same table. A calendar is not a different object
        from a history -- it is these rows read with observed_at ahead of the
        cutoff instead of behind it, which is why "the calendar was right" is a
        question this store can answer later.
        """
        cutoff = as_of or session.utc_iso()
        return self._rows(
            "e.observed_at >= :first AND e.observed_at <= :last"
            " AND e.available_at <= :cutoff",
            {"first": first, "last": f"{last}T23:59:59Z", "cutoff": cutoff})

    def counts(self, since: Optional[str] = None,
               as_of: Optional[str] = None) -> dict:
        """Rows by type, for the heartbeat and the summary line."""
        cutoff = as_of or session.utc_iso()
        where = ["available_at <= :cutoff"]
        args: dict[str, Any] = {"cutoff": cutoff}
        if since:
            where.append("observed_at >= :since")
            args["since"] = since
        cur = self.conn.execute(
            "SELECT type, COUNT(*) n, MAX(observed_at) newest,"
            "       MAX(ingested_at) last_ingest FROM events"
            f" WHERE {' AND '.join(where)} GROUP BY type ORDER BY type", args)
        return {r["type"]: {"n": r["n"], "newest": r["newest"],
                            "last_ingest": r["last_ingest"]}
                for r in cur.fetchall()}

    def sources(self) -> dict:
        """Per source: rows, newest event, last ingest. The freshness question."""
        cur = self.conn.execute(
            "SELECT source, COUNT(*) n, MAX(observed_at) newest,"
            "       MAX(ingested_at) last_ingest FROM events"
            " GROUP BY source ORDER BY source")
        return {r["source"]: {"n": r["n"], "newest": r["newest"],
                              "last_ingest": r["last_ingest"]}
                for r in cur.fetchall()}


def _main(argv: list[str]) -> int:
    import argparse
    p = argparse.ArgumentParser(description="The events table.")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("summary")
    sh = sub.add_parser("show")
    sh.add_argument("--type", default=None)
    sh.add_argument("--since", default=None)
    sh.add_argument("--limit", type=int, default=20)
    a = p.parse_args(argv)

    with EventStore() as ev:
        if a.cmd == "summary":
            counts = ev.counts()
            if not counts:
                print("no events stored")
                return 0
            print(f"{'type':<16}{'rows':>7}  newest event        last ingest")
            for t, c in counts.items():
                print(f"{t:<16}{c['n']:>7}  {str(c['newest'])[:19]:<19} "
                      f"{str(c['last_ingest'])[:19]}")
            print()
            print(f"{'source':<26}{'rows':>7}  newest event        last ingest")
            for s, c in ev.sources().items():
                print(f"{s:<26}{c['n']:>7}  {str(c['newest'])[:19]:<19} "
                      f"{str(c['last_ingest'])[:19]}")
            return 0

        since = a.since or (dt.date.today() - dt.timedelta(days=7)).isoformat()
        rows = ev.since(since, types=[a.type] if a.type else None)
        for r in rows[-a.limit:]:
            ents = ",".join(r["entities"][:6])
            print(f"{str(r['observed_at'])[:16]}  {r['type']:<14} "
                  f"{r['source']:<20} {r['title'][:72]}"
                  + (f"  [{ents}]" if ents else ""))
        print(f"\n{len(rows)} event(s) since {since}")
        return 0


if __name__ == "__main__":                                     # pragma: no cover
    import sys
    raise SystemExit(_main(sys.argv[1:]))
