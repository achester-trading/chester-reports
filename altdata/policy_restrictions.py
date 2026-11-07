"""
The AI policy-restriction ledger (signal-triage Batch 22 item 117, the order's 99;
section 0's O-2; paste B135, 6 Nov 2026).

One table in the register database, `policy_restrictions`, one row per measure at
one stage: federal bills, state and local statutes, ordinances, executive orders
and ballot measures, introduced, passed or enacted, with the capacity (MW) or
capex ($) at risk where estimable and the source link. A second row type,
`planned_build`, is the denominator: the projects the ledger tracks, with their
MW. A third, `reference`, holds an estimate (never a measure, never counted).

APPEND-ONLY. A row is never edited or deleted (triggers refuse both); a stage
change is a new row naming the row it `supersedes`. Every row enters PROPOSED.
The operator's accept-all writes one row of `policy_restriction_reviews` per
reviewed row, itself immutable; nothing in this module accepts or rejects on its
own (`review` is the operator's command, as the narrative register's confirm is).

THE WRITERS (no by-hand feed, the 10 Oct rule):
  - the news writer filters the titles of the items the daily voices scan has read
    (voice_scan_seen) by config/story_queries.yaml's `policy_restrictions` group;
  - the x-triage writer reads a digest's policy section, one row a line:
        url | jurisdiction | instrument | stage | date | title [| MW]
  - the seed: config/policy_restrictions.yaml's judgment drafts (rule 31).

THE FLAG (O-2): accepted, enacted-stage restrictions, not superseded, covering at
least 10% of tracked planned capacity (the accepted planned_build rows' MW).
Computed only when the denominator is non-empty; it prints "denominator: n
projects, X GW". Rights: an input line and a flag; no composite change.

    python -m altdata.policy_restrictions propose [--from D]   both writers
    python -m altdata.policy_restrictions seed                 the seed drafts
    python -m altdata.policy_restrictions show                 the ledger and the flag
    python -m altdata.policy_restrictions review accept|reject <id>... --by NAME
                                                               the operator's
"""

from __future__ import annotations

import datetime as dt
import functools
import logging
import re
import sqlite3
from pathlib import Path
from typing import Any, Iterable, Optional

log = logging.getLogger("altdata.policy_restrictions")

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / "config" / "policy_restrictions.yaml"
QUERIES = REPO / "config" / "story_queries.yaml"
ROW_TYPES = ("restriction", "planned_build", "reference")
INSTRUMENTS = ("federal bill", "state statute", "local statute", "ordinance",
               "executive order", "ballot measure", "unclassified")
STAGES = ("introduced", "passed", "enacted", "unclassified")
ORIGINS = ("seed", "news_scan", "x_triage")
DECISIONS = ("accepted", "rejected")
NO_ROWS = "no rows yet"

SCHEMA = f"""
CREATE TABLE IF NOT EXISTS policy_restrictions (
    id            INTEGER PRIMARY KEY,
    row_type      TEXT NOT NULL CHECK (row_type IN {ROW_TYPES!r}),
    jurisdiction  TEXT NOT NULL,
    instrument    TEXT NOT NULL CHECK (instrument IN {INSTRUMENTS!r}),
    stage         TEXT NOT NULL CHECK (stage IN {STAGES!r}),
    stage_date    TEXT NOT NULL,
    title         TEXT NOT NULL,
    project       TEXT,
    capacity_mw   REAL CHECK (capacity_mw IS NULL OR capacity_mw >= 0),
    capex_usd     REAL CHECK (capex_usd IS NULL OR capex_usd >= 0),
    announced_date TEXT,
    source_url    TEXT NOT NULL CHECK (source_url LIKE 'http://%' OR source_url LIKE 'https://%'),
    source_kind   TEXT,
    origin        TEXT NOT NULL CHECK (origin IN {ORIGINS!r}),
    status        TEXT NOT NULL DEFAULT 'proposed' CHECK (status = 'proposed'),
    supersedes    INTEGER REFERENCES policy_restrictions(id),
    note          TEXT,
    proposed_at   TEXT NOT NULL,
    UNIQUE (source_url, row_type, stage, jurisdiction)
);
CREATE TABLE IF NOT EXISTS policy_restriction_reviews (
    row_id      INTEGER PRIMARY KEY REFERENCES policy_restrictions(id),
    decision    TEXT NOT NULL CHECK (decision IN {DECISIONS!r}),
    decided_by  TEXT NOT NULL,
    decided_at  TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS policy_restrictions_no_update
BEFORE UPDATE ON policy_restrictions
BEGIN SELECT RAISE(ABORT, 'policy_restrictions is append-only: a stage change is a new row'); END;
CREATE TRIGGER IF NOT EXISTS policy_restrictions_no_delete
BEFORE DELETE ON policy_restrictions
BEGIN SELECT RAISE(ABORT, 'policy_restrictions rows are never deleted'); END;
CREATE TRIGGER IF NOT EXISTS policy_restriction_reviews_no_update
BEFORE UPDATE ON policy_restriction_reviews
BEGIN SELECT RAISE(ABORT, 'a review is written once'); END;
CREATE TRIGGER IF NOT EXISTS policy_restriction_reviews_no_delete
BEFORE DELETE ON policy_restriction_reviews
BEGIN SELECT RAISE(ABORT, 'a review is never deleted'); END;
"""


@functools.lru_cache(maxsize=1)
def _cfg() -> dict:
    import yaml                                                 # noqa: PLC0415
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def config() -> dict:
    return _cfg()


def query_group() -> dict:
    import yaml                                                 # noqa: PLC0415
    return (yaml.safe_load(QUERIES.read_text(encoding="utf-8")) or {}).get(
        "policy_restrictions") or {}


def _now() -> str:
    from altdata import session                                 # noqa: PLC0415
    return session.utc_iso()


def connect(path: Optional[str] = None, readonly: bool = False) -> sqlite3.Connection:
    """The register database (the observation store's file, as the narrative
    register's). Read-only opens create nothing; a missing table reads empty."""
    from altdata import observations                            # noqa: PLC0415
    p = Path(path or observations.DEFAULT_DB)
    if readonly:
        conn = sqlite3.connect(f"file:{p.resolve().as_posix()}?mode=ro", uri=True)
        conn.execute("PRAGMA query_only = ON")
    else:
        p.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(p))
        conn.execute("PRAGMA busy_timeout = 30000")
        conn.executescript(SCHEMA)
    conn.row_factory = sqlite3.Row
    return conn


def _has_tables(conn) -> bool:
    return bool(conn.execute("SELECT 1 FROM sqlite_master WHERE "
                             "name='policy_restrictions'").fetchall())


# ---------------------------------------------------------------------------
# Writing: proposals only
# ---------------------------------------------------------------------------
class PolicyRowError(ValueError):
    pass


def validate(row: dict) -> list[str]:
    errs = []
    if row.get("row_type") not in ROW_TYPES:
        errs.append(f"row_type {row.get('row_type')!r} is not one of {ROW_TYPES}")
    if row.get("instrument") not in INSTRUMENTS:
        errs.append(f"instrument {row.get('instrument')!r} is not one of {INSTRUMENTS}")
    if row.get("stage") not in STAGES:
        errs.append(f"stage {row.get('stage')!r} is not one of {STAGES}")
    if not re.fullmatch(r"https?://\S+", str(row.get("source_url") or "")):
        errs.append("no source URL -- no row without one")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(row.get("stage_date") or "")):
        errs.append(f"stage_date {row.get('stage_date')!r} is not YYYY-MM-DD")
    for k in ("jurisdiction", "title"):
        if not str(row.get(k) or "").strip():
            errs.append(f"no {k}")
    if row.get("row_type") == "planned_build" and not row.get("project"):
        errs.append("a planned_build row names its project")
    return errs


COLS = ("row_type", "jurisdiction", "instrument", "stage", "stage_date", "title",
        "project", "capacity_mw", "capex_usd", "announced_date", "source_url",
        "source_kind", "origin", "supersedes", "note")


def propose(conn, row: dict, origin: str) -> Optional[int]:
    """One PROPOSED row; None when the same source, type, stage and jurisdiction
    is already in the ledger. Raises PolicyRowError with every reason."""
    row = dict(row, origin=origin)
    errs = validate(row)
    if errs:
        raise PolicyRowError("; ".join(errs))
    try:
        cur = conn.execute(
            f"INSERT INTO policy_restrictions ({', '.join(COLS)}, status, proposed_at) "
            f"VALUES ({', '.join('?' * len(COLS))}, 'proposed', ?)",
            tuple(row.get(c) for c in COLS) + (_now(),))
    except sqlite3.IntegrityError as exc:
        conn.rollback()                 # never leave the write lock held
        if "UNIQUE" in str(exc):
            return None
        raise
    conn.commit()
    return cur.lastrowid


def seed(conn, cfg: Optional[dict] = None) -> dict:
    out = {"written": [], "present": [], "not_written": []}
    cfg = cfg or config()
    for r in cfg.get("seed") or []:
        rid = propose(conn, {k: r.get(k) for k in COLS if k in r}, "seed")
        (out["written"] if rid else out["present"]).append(r["title"])
    out["not_written"] = [x["item"] for x in cfg.get("not_written") or []]
    return out


def classify(title: str, cfg: Optional[dict] = None) -> tuple[str, str]:
    t = f" {title.lower()} "
    rules = (cfg or config()).get("classify") or {}

    def first(kind, default):
        for r in rules.get(kind) or []:
            if any(m in t for m in r["match"]):
                return r["value"]
        return default
    return first("instrument", "unclassified"), first("stage", "unclassified")


def matches(title: str, group: Optional[dict] = None) -> bool:
    g = group if group is not None else query_group()
    t = f" {str(title or '').lower()} "
    return (any(s in t for s in g.get("subject") or [])
            and any(a in t for a in g.get("action") or []))


def propose_from_news(conn, voices_conn, since: str, group: Optional[dict] = None
                      ) -> list[int]:
    """The news writer: the voices scan's seen items since `since` whose title
    matches the group, each proposed once with its URL."""
    g = group if group is not None else query_group()
    try:
        items = voices_conn.execute(
            "SELECT item_url, title, published_at, first_seen FROM voice_scan_seen "
            "WHERE COALESCE(published_at, first_seen) >= ? ORDER BY first_seen",
            (since,)).fetchall()
    except sqlite3.OperationalError:
        return []
    out = []
    for it in items:
        if len(out) >= int(g.get("cap_per_run") or 20):
            break
        title = it["title"] or ""
        if not matches(title, g):
            continue
        inst, stage = classify(title)
        rid = propose(conn, {
            "row_type": "restriction", "jurisdiction": "unclassified",
            "instrument": inst, "stage": stage,
            "stage_date": str(it["published_at"] or it["first_seen"])[:10],
            "title": title, "source_url": it["item_url"],
            "source_kind": "news (the voices scan's item)",
            "note": "proposed by the news writer: jurisdiction and stage for the operator"},
            "news_scan")
        if rid:
            out.append(rid)
    return out


DIGEST_ROW = re.compile(r"^\s*[-*]?\s*(https?://\S+)\s*\|(.+)$")


def digest_policy_rows(body: str) -> list[dict]:
    """A digest's policy section: url | jurisdiction | instrument | stage | date |
    title [| MW]. A line without a URL, or with a field outside the vocabularies,
    is not a row (it is skipped, never repaired)."""
    out = []
    for line in body.splitlines():
        m = DIGEST_ROW.match(line)
        if not m:
            continue
        parts = [p.strip() for p in m.group(2).split("|")]
        if len(parts) < 5:
            continue
        juris, inst, stage, date, title = parts[:5]
        mw = None
        if len(parts) > 5 and parts[5]:
            try:
                mw = float(parts[5].replace(",", ""))
            except ValueError:
                mw = None
        row = {"row_type": "restriction", "jurisdiction": juris,
               "instrument": inst.lower(), "stage": stage.lower(), "stage_date": date,
               "title": title, "capacity_mw": mw, "source_url": m.group(1),
               "source_kind": "the X digest's policy section (its linked source)"}
        if not validate(row):
            out.append(row)
    return out


def propose_from_digests(conn, inbox: Path, since: str, until: str, cutoff: str
                         ) -> list[int]:
    """The x-triage writer: every digest from `since` to `until`, its policy
    section's rows proposed once each."""
    from daily_cascade import digital_addendum as da            # noqa: PLC0415
    out = []
    for _day, p in da.digest_files(inbox / "x-digest", since, until, cutoff):
        sec = da.digest_sections(p.read_text(encoding="utf-8"))
        body = next((v for k, v in sec.items() if k.startswith("policy")), "")
        for row in digest_policy_rows(body):
            rid = propose(conn, row, "x_triage")
            if rid:
                out.append(rid)
    return out


def review(conn, ids: Iterable[int], decision: str, by: str) -> list[int]:
    """THE OPERATOR'S accept-all: one immutable review row per proposed row."""
    if decision not in DECISIONS:
        raise PolicyRowError(f"decision {decision!r} is not one of {DECISIONS}")
    if not str(by or "").strip():
        raise PolicyRowError("a review records who made it")
    done = []
    for i in ids:
        if not conn.execute("SELECT 1 FROM policy_restrictions WHERE id=?", (i,)).fetchall():
            raise PolicyRowError(f"no row {i}")
        try:
            conn.execute("INSERT INTO policy_restriction_reviews VALUES (?,?,?,?)",
                         (int(i), decision, by, _now()))
            done.append(int(i))
        except sqlite3.IntegrityError:
            conn.rollback()
            raise PolicyRowError(f"row {i} is already reviewed") from None
    conn.commit()
    return done


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------
def rows(conn, as_of: Optional[str] = None) -> list[dict]:
    """Every row with its review state as known at `as_of` (proposed until a
    review is written)."""
    if not _has_tables(conn):
        return []
    q = ("SELECT r.*, v.decision, v.decided_at FROM policy_restrictions r LEFT JOIN "
         "policy_restriction_reviews v ON v.row_id = r.id")
    out = []
    for r in conn.execute(q + " ORDER BY r.id").fetchall():
        d = dict(r)
        if as_of and d["proposed_at"] > as_of:
            continue
        if d.get("decided_at") and as_of and d["decided_at"] > as_of:
            d["decision"] = None
        d["state"] = d.get("decision") or "proposed"
        out.append(d)
    return out


def flag(conn, as_of: Optional[str] = None, cfg: Optional[dict] = None) -> dict:
    """O-2. The denominator first: no accepted planned_build row, no flag."""
    cfg = cfg or config()
    thr = float(cfg["flag"]["threshold"])
    rs = rows(conn, as_of)
    acc = [r for r in rs if r["state"] == "accepted"]
    superseded = {r["supersedes"] for r in acc if r.get("supersedes")}
    builds = [r for r in acc if r["row_type"] == "planned_build" and r.get("capacity_mw")]
    denom = sum(float(r["capacity_mw"]) for r in builds)
    enacted = [r for r in acc if r["row_type"] == "restriction" and r["stage"] == "enacted"
               and r["id"] not in superseded]
    covered = sum(float(r["capacity_mw"] or 0) for r in enacted)
    base = {"threshold": thr, "review_date": cfg["flag"].get("review_date"),
            "n_rows": len(rs), "proposed": sum(1 for r in rs if r["state"] == "proposed"),
            "enacted": len(enacted), "projects": len(builds), "gw": denom / 1000.0,
            "stages": {s: sum(1 for r in acc if r["row_type"] == "restriction"
                              and r["stage"] == s and r["id"] not in superseded)
                       for s in ("introduced", "passed", "enacted")}}
    if not builds or denom <= 0:
        return {**base, "computed": False, "fired": False, "share": None,
                "denominator": "denominator: none (no accepted planned_build row); "
                               "the flag is not computed"}
    share = covered / denom
    return {**base, "computed": True, "share": share, "fired": share >= thr,
            "denominator": f"denominator: {len(builds)} projects, {denom / 1000.0:.1f} GW"}


def reaction(st, day: str, cfg: Optional[dict] = None) -> dict[str, Optional[float]]:
    """The one-day move on `day`, per reaction series, from the store (None
    when either close is not stored)."""
    out = {}
    for spec in (cfg or config()).get("reaction") or []:
        try:
            pts = sorted((str(r["observed_at"])[:10], float(r["value_num"]))
                         for r in st.as_of(spec["key"]) if r.get("value_num") is not None)
        except Exception:                                       # noqa: BLE001
            pts = []
        days = [d for d, _ in pts]
        v = None
        if day in days:
            i = days.index(day)
            if i > 0 and pts[i - 1][1]:
                v = (pts[i][1] / pts[i - 1][1] - 1) * 100
        out[spec["id"]] = v
    return out


def flag_line(f: dict) -> str:
    if f["n_rows"] == 0:
        return f"AI policy restrictions (item 117): {NO_ROWS}."
    if not f["computed"]:
        return (f"AI policy restrictions (item 117): {f['enacted']} enacted restriction(s) "
                f"accepted; {f['denominator']}; {f['proposed']} row(s) proposed, "
                f"awaiting the operator's review.")
    state = "ON" if f["fired"] else "off"
    return (f"AI policy restrictions (item 117): flag {state} -- enacted restrictions "
            f"cover {f['share'] * 100:.1f}% of tracked planned capacity (threshold "
            f"{f['threshold'] * 100:.0f}%, reviewed {f['review_date']}); "
            f"{f['denominator']}; {f['proposed']} row(s) proposed.")


def factor_lines(conn, as_of: Optional[str] = None) -> list[str]:
    """The Factor I input line and the Factor VI (Internal Order) input line."""
    f = flag(conn, as_of)
    s = f["stages"]
    rs = [r for r in rows(conn, as_of) if r["row_type"] == "restriction"
          and r["state"] == "accepted"]
    latest = max(rs, key=lambda r: (r["stage_date"], r["id"]), default=None)
    vi = (f"Factor VI (Internal Order), AI-restriction politics: accepted measures by "
          f"stage -- introduced {s['introduced']}, passed {s['passed']}, enacted "
          f"{s['enacted']}"
          + (f"; latest: {latest['title']} ({latest['stage']}, {latest['stage_date']})"
             if latest else "") + ".")
    if f["n_rows"] == 0:
        vi = f"Factor VI (Internal Order), AI-restriction politics: {NO_ROWS}."
    fl = flag_line(f).removeprefix("AI policy restrictions (item 117): ")
    return [f"Factor I input, AI policy restrictions (item 117): {fl}", vi]


def table(conn, st, as_of: Optional[str] = None, limit: int = 10) -> Optional[dict]:
    """The restriction rows, newest stage first, with the reaction column: the
    one-day move on the stage date from the store ("not stored" otherwise)."""
    rs = [r for r in rows(conn, as_of) if r["row_type"] != "planned_build"]
    if not rs:
        return None
    rs = sorted(rs, key=lambda r: (r["stage_date"], r["id"]), reverse=True)[:limit]
    cfg = config()
    labels = [s["label"] for s in cfg.get("reaction") or []]

    def pc(v):
        return "not stored" if v is None else f"{v:+.2f}%"
    out = []
    for r in rs:
        rx = reaction(st, r["stage_date"], cfg) if st is not None else {}
        out.append([str(r["id"]), r["state"], r["jurisdiction"], r["instrument"],
                    r["stage"], r["stage_date"], r["title"],
                    *[pc(rx.get(s["id"])) for s in cfg.get("reaction") or []],
                    r["source_url"]])
    return {"columns": ["Row", "Review", "Jurisdiction", "Instrument", "Stage", "Date",
                        "Measure", *[f"Reaction: {x}" for x in labels], "Source"],
            "rows": out}


def _read_conn(st) -> Optional[sqlite3.Connection]:
    try:
        return connect(str(st.path), readonly=True)
    except Exception:                                           # noqa: BLE001
        return None


def slow_subsection(st, now: str) -> Optional[dict]:
    """The Monthly's slow layers (config/stack_hooks/monthly-slow-policy-
    restrictions.yaml): the two input lines, no paragraph."""
    conn = _read_conn(st)
    if conn is None:
        return None
    try:
        lines = factor_lines(conn, now)
        tbl = table(conn, st, now)
    finally:
        conn.close()
    return {"title": "AI policy-restriction ledger (Factors I and VI)", "table": tbl,
            "paragraph_wanted": False, "lines": lines, "not_tracked": []}


def close_extras(built: dict, st) -> None:
    """The close's Narratives: one line, only on a day the flag is ON."""
    sec = built.get("narratives")
    conn = _read_conn(st) if sec is not None else None
    if conn is None:
        return
    try:
        f = flag(conn)
    finally:
        conn.close()
    if f.get("fired"):
        from daily_cascade.stack import item                    # noqa: PLC0415
        sec.setdefault("items", []).append(item("narr:policy_restrictions",
                                                flag_line(f), 1, f["share"]))


def weekly_narratives(sec: dict, st, now: str) -> None:
    """The Weekly's Narratives: the flag's line every week, ON or off."""
    conn = _read_conn(st)
    if conn is None:
        return
    try:
        f = flag(conn, now)
    finally:
        conn.close()
    sec.setdefault("subsections", []).append(
        {"title": "AI policy-restriction ledger", "paragraph_wanted": False,
         "lines": [flag_line(f)]})


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    import sys                                                  # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.policy_restrictions")
    ap.add_argument("cmd", choices=["propose", "seed", "show", "review"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--db", default=None)
    ap.add_argument("--from", dest="since", default=None)
    ap.add_argument("--by", default=None)
    a = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    if a.cmd == "show":
        conn = connect(a.db, readonly=True)
        for r in rows(conn):
            print(f"{r['id']:>4} {r['state']:9} {r['row_type']:13} {r['stage']:11} "
                  f"{r['stage_date']} {r['jurisdiction']}: {r['title']} ({r['source_url']})")
        print(flag_line(flag(conn)))
        return 0
    conn = connect(a.db)
    if a.cmd == "seed":
        print(seed(conn))
    elif a.cmd == "propose":
        # The seed drafts first: idempotent, so the box's first run writes them
        # PROPOSED and every later run finds them present.
        sd = seed(conn)
        since = a.since or (dt.date.today() - dt.timedelta(
            days=int(query_group().get("window_days") or 3))).isoformat()
        news = propose_from_news(conn, conn, since)
        from daily_cascade import digital_addendum as da        # noqa: PLC0415
        dig = propose_from_digests(conn, da.inbox_dir(), since,
                                   dt.date.today().isoformat(), _now())
        print(f"proposed: {len(sd['written'])} seed, {len(news)} from the news scan, "
              f"{len(dig)} from the digests")
    else:
        if not a.args or a.args[0] not in ("accept", "reject") or not a.by:
            raise SystemExit("review accept|reject <id>... --by NAME")
        done = review(conn, [int(x) for x in a.args[1:]],
                      "accepted" if a.args[0] == "accept" else "rejected", a.by)
        print(f"reviewed: {done}")
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
