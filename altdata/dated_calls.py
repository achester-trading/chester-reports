"""
The dated public call -- an entry type of the narrative register (signal-triage
Batch 25 item 132, the order's 111; B139, the code half).

    python -m altdata.dated_calls list   [--db PATH]
    python -m altdata.dated_calls seed   [--db PATH]     # sync config/dated_calls.yaml
    python -m altdata.dated_calls grade  [--as-of T] [--db PATH]
    python -m altdata.dated_calls counts [--db PATH]

A viral, dated, falsifiable forecast, held with its claims (each with its own
date), the forecaster's incentive tags, its engagement at capture, and a score per
claim at that claim's expiry: hit, miss or unresolved.

- **Rows** live in the register's database beside `narratives`, in three tables:
  `dated_calls`, `dated_call_claims` and `dated_call_scores`. A call is never
  deleted (rejected instead), and a score is written once and never edited.
- **Definitions come from config, scores from the grading pass.** `seed` syncs a
  call's fields and claims from config/dated_calls.yaml every run; it never
  touches a score. A call's status is the operator's: it is `proposed` until the
  operator's accept-all is quoted into config.
- **The grading pass** (`grade_due`, run by the register's `resolve_due`) scores a
  claim once its date has passed and the store holds a close on or after it:
  hit or miss where the claim carries a rule (a level or a move, read from the
  observation store as known at the cutoff), `unresolved` otherwise, left for the
  operator, whose ruled score (`operator_score`) is written in its place when
  config carries one.
- **The two counts** (`count_rows`, in the features pass): rows captured per ET
  day by direction, `calc.viral_call_count.down` and `.up`, from the first
  captured row; nothing is stored before one exists ("no rows yet").

Register rows and an attention input: no forecast right, no scenario or theme
change, nothing enters the market-state object. No person's name or handle in a
row (the forecaster is described by kind).
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo

import yaml

from . import observations, session

log = logging.getLogger("altdata.dated_calls")

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "config" / "dated_calls.yaml"
ET = ZoneInfo("America/New_York")
SCORES = ("hit", "miss", "unresolved")
DIRECTIONS = ("down", "up")
STATUSES = ("proposed", "active", "rejected")
RULE_KINDS = ("move_on", "move_by", "level_by", "move_from_high")

SCHEMA = """
CREATE TABLE IF NOT EXISTS dated_calls (
    call_id        TEXT PRIMARY KEY,
    status         TEXT NOT NULL CHECK (status IN ('proposed', 'active', 'rejected')),
    direction      TEXT NOT NULL CHECK (direction IN ('down', 'up')),
    forecaster     TEXT NOT NULL,
    incentive_tags TEXT NOT NULL,
    engagement     TEXT NOT NULL,
    posted_at      TEXT NOT NULL,
    captured_at    TEXT NOT NULL,
    expiry         TEXT NOT NULL,
    admitted_by    TEXT,
    config_version TEXT,
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS dated_calls_no_delete
BEFORE DELETE ON dated_calls
BEGIN SELECT RAISE(ABORT, 'a dated call is not deletable; reject it instead'); END;

CREATE TABLE IF NOT EXISTS dated_call_claims (
    call_id   TEXT NOT NULL REFERENCES dated_calls(call_id),
    claim_id  TEXT NOT NULL,
    claim_day TEXT NOT NULL,
    text      TEXT NOT NULL,
    rule      TEXT,
    PRIMARY KEY (call_id, claim_id)
);

CREATE TABLE IF NOT EXISTS dated_call_scores (
    id        INTEGER PRIMARY KEY,
    call_id   TEXT NOT NULL,
    claim_id  TEXT NOT NULL,
    score     TEXT NOT NULL CHECK (score IN ('hit', 'miss', 'unresolved')),
    scored_by TEXT NOT NULL,
    scored_at TEXT NOT NULL,
    detail    TEXT NOT NULL,
    UNIQUE (call_id, claim_id)
);
CREATE TRIGGER IF NOT EXISTS dated_call_scores_immutable
BEFORE UPDATE ON dated_call_scores
BEGIN SELECT RAISE(ABORT, 'a score is the record; it is never edited'); END;
CREATE TRIGGER IF NOT EXISTS dated_call_scores_no_delete
BEFORE DELETE ON dated_call_scores
BEGIN SELECT RAISE(ABORT, 'a score is the record; it is never deleted'); END;
"""


def config(path: Optional[Path] = None) -> dict:
    return yaml.safe_load((path or CONFIG_PATH).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# The schema of a row (what the triage writes and the seed refuses)
# ---------------------------------------------------------------------------
def _d(x: Any) -> dt.date:
    return x if isinstance(x, dt.date) else dt.date.fromisoformat(str(x)[:10])


def validate_call(cid: str, c: dict, cfg: Optional[dict] = None) -> list[str]:
    """Why a call cannot enter the register; [] when it can."""
    cfg = cfg or config()
    cap = cfg.get("capture") or {}
    errs = []
    for f in ("status", "direction", "forecaster", "incentive_tags",
              "engagement_at_capture", "posted_at", "captured_at", "expiry", "claims"):
        if c.get(f) in (None, "", []):
            errs.append(f"{cid}: no {f}")
    if errs:
        return errs
    if c["status"] not in STATUSES:
        errs.append(f"{cid}: status {c['status']!r}")
    if c["direction"] not in DIRECTIONS:
        errs.append(f"{cid}: direction {c['direction']!r}")
    tags = c["incentive_tags"]
    for t in ("position_disclosed", "product_sold"):
        if t not in tags:
            errs.append(f"{cid}: incentive tag {t} missing")
    eng = c["engagement_at_capture"]
    views, reposts = eng.get("views"), eng.get("reposts")
    meets = ((views is not None and views >= cap.get("min_views", 10000))
             or (reposts is not None and reposts >= cap.get("min_reposts", 100)))
    if not meets and not c.get("admitted_by"):
        errs.append(f"{cid}: engagement below the capture threshold (O-111a) and no ruling admits it")
    cap_day = _d(c["captured_at"])
    ids = set()
    for k in c["claims"]:
        kid = k.get("id")
        if not kid or kid in ids:
            errs.append(f"{cid}: a claim without a unique id")
            continue
        ids.add(kid)
        if not k.get("date") or not k.get("text"):
            errs.append(f"{cid}:{kid}: a claim needs its date and its text")
            continue
        if (_d(k["date"]) - cap_day).days > int(cap.get("max_claim_days", 30)):
            errs.append(f"{cid}:{kid}: dated more than {cap.get('max_claim_days', 30)} days after capture")
        if _d(k["date"]) > _d(c["expiry"]):
            errs.append(f"{cid}:{kid}: dated after the call's expiry")
        r = k.get("rule")
        if r is not None:
            if r.get("kind") not in RULE_KINDS:
                errs.append(f"{cid}:{kid}: rule kind {r.get('kind')!r}")
            elif not r.get("metric"):
                errs.append(f"{cid}:{kid}: a rule names its metric")
            elif r["kind"] == "level_by" and ("below" in r) == ("above" in r):
                errs.append(f"{cid}:{kid}: level_by takes one of below or above")
            elif r["kind"] != "level_by" and r.get("pct") is None:
                errs.append(f"{cid}:{kid}: {r['kind']} takes pct")
            elif r["kind"] != "move_on" and not r.get("baseline_date"):
                errs.append(f"{cid}:{kid}: {r['kind']} takes baseline_date")
        if k.get("operator_score") not in (None, "hit", "miss"):
            errs.append(f"{cid}:{kid}: operator_score {k.get('operator_score')!r}")
    return errs


# ---------------------------------------------------------------------------
# The register's tables
# ---------------------------------------------------------------------------
def connect(db_path: Optional[str] = None) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path or observations.DEFAULT_DB))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def seed(db_path: Optional[str] = None, cfg: Optional[dict] = None,
         now: Optional[str] = None) -> dict:
    """Insert config calls not yet present; sync the definitions of those that
    are. Never writes a score. A refused call is named with its reasons."""
    cfg = cfg or config()
    now = now or session.utc_iso()
    out: dict[str, Any] = {"inserted": [], "synced": [], "refused": {}}
    conn = connect(db_path)
    try:
        for cid, c in (cfg.get("calls") or {}).items():
            errs = validate_call(cid, c, cfg)
            if errs:
                out["refused"][cid] = errs
                continue
            vals = (c["status"], c["direction"], c["forecaster"],
                    json.dumps(c["incentive_tags"], sort_keys=True),
                    json.dumps(c["engagement_at_capture"], sort_keys=True),
                    str(c["posted_at"]), str(c["captured_at"]), str(c["expiry"]),
                    c.get("admitted_by"), cfg.get("version"))
            have = conn.execute("SELECT 1 FROM dated_calls WHERE call_id = ?",
                                (cid,)).fetchone()
            if have:
                conn.execute(
                    "UPDATE dated_calls SET status=?, direction=?, forecaster=?, "
                    "incentive_tags=?, engagement=?, posted_at=?, captured_at=?, "
                    "expiry=?, admitted_by=?, config_version=?, updated_at=? "
                    "WHERE call_id=?", (*vals, now, cid))
                out["synced"].append(cid)
            else:
                conn.execute(
                    "INSERT INTO dated_calls (status, direction, forecaster, "
                    "incentive_tags, engagement, posted_at, captured_at, expiry, "
                    "admitted_by, config_version, created_at, updated_at, call_id) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (*vals, now, now, cid))
                out["inserted"].append(cid)
            for k in c["claims"]:
                conn.execute(
                    "INSERT INTO dated_call_claims (call_id, claim_id, claim_day, text, rule) "
                    "VALUES (?,?,?,?,?) ON CONFLICT(call_id, claim_id) DO UPDATE SET "
                    "claim_day=excluded.claim_day, text=excluded.text, rule=excluded.rule",
                    (cid, k["id"], str(k["date"]), k["text"],
                     json.dumps(k.get("rule"), sort_keys=True, default=str)
                     if k.get("rule") else None))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return out


# ---------------------------------------------------------------------------
# The scoring rule
# ---------------------------------------------------------------------------
def _closes(store: Any, metric: str, as_of: str) -> list[tuple[str, float]]:
    by: dict[str, float] = {}
    for r in store.as_of(metric, as_of):
        if r.get("value_num") is not None:
            by[str(r["observed_at"])[:10]] = float(r["value_num"])
    return sorted(by.items())


def score_claim(rule: Optional[dict], claim_day: str, store: Any, as_of: str,
                operator_score: Optional[str] = None) -> Optional[dict]:
    """{score, detail} once the claim's date has passed and can be read, else
    None (not yet). A claim without a rule is `unresolved` (the operator's)."""
    today = str(as_of)[:10]
    if today <= str(claim_day):
        return None
    if not rule:
        if operator_score:
            return {"score": operator_score, "by": "operator",
                    "detail": "the operator's ruled score"}
        return {"score": "unresolved", "by": "grading_pass",
                "detail": "no level or move the store can answer: left for the operator"}
    s = _closes(store, rule["metric"], as_of)
    day = str(claim_day)
    if not any(d >= day for d, _ in s):
        return None                                   # no close on or after the date yet
    kind = rule["kind"]
    pct = rule.get("pct")

    def reached(move: float) -> bool:
        return move <= pct if pct < 0 else move >= pct

    if kind == "move_on":
        i = next((j for j, (d, _) in enumerate(s) if d == day), None)
        if i is None or i == 0:
            return {"score": "unresolved", "by": "grading_pass",
                    "detail": f"{rule['metric']}: no close on {day} and the one before it"}
        mv = 100.0 * (s[i][1] / s[i - 1][1] - 1.0)
        return {"score": "hit" if reached(mv) else "miss", "by": "grading_pass",
                "detail": f"{rule['metric']} {mv:+.2f}% on {day} (against {pct:+g}%)"}
    base_day = str(rule["baseline_date"])
    before = [(d, v) for d, v in s if d <= base_day]
    window = [(d, v) for d, v in s if base_day < d <= day]
    if not before or not window:
        return {"score": "unresolved", "by": "grading_pass",
                "detail": f"{rule['metric']}: no baseline close on or before {base_day} "
                          f"or no close after it by {day}"}
    if kind == "level_by":
        if "below" in rule:
            hit = min(v for _, v in window) < float(rule["below"])
            what = f"low {min(v for _, v in window):,.2f} against below {float(rule['below']):,.0f}"
        else:
            hit = max(v for _, v in window) > float(rule["above"])
            what = f"high {max(v for _, v in window):,.2f} against above {float(rule['above']):,.0f}"
        return {"score": "hit" if hit else "miss", "by": "grading_pass",
                "detail": f"{rule['metric']} {what}, {base_day} to {day}"}
    if kind == "move_by":
        ref, ref_what = before[-1][1], f"the {before[-1][0]} close"
    else:                                              # move_from_high
        n = int(rule.get("high_sessions", 252))
        ref = max(v for _, v in before[-n:])
        ref_what = f"the high of the {min(n, len(before))} closes to {base_day}"
    ext = min(v for _, v in window) if pct < 0 else max(v for _, v in window)
    mv = 100.0 * (ext / ref - 1.0)
    return {"score": "hit" if reached(mv) else "miss", "by": "grading_pass",
            "detail": f"{rule['metric']} at most {mv:+.2f}% from {ref_what} by {day} "
                      f"(against {pct:+g}%)"}


def grade_due(as_of: Optional[str] = None, db_path: Optional[str] = None,
              cfg: Optional[dict] = None, store: Any = None) -> dict:
    """Score every claim whose date has passed, once. Idempotent. A rejected
    call is not graded."""
    cfg = cfg or config()
    cutoff = observations.canonical_instant(as_of or session.utc_iso(timespec="microseconds"))
    ops = {(cid, k["id"]): k.get("operator_score")
           for cid, c in (cfg.get("calls") or {}).items() for k in c.get("claims") or []}
    out: dict[str, Any] = {"scored": [], "waiting": 0}
    own = store is None
    store = store or observations.ObservationStore(db_path)
    conn = connect(db_path)
    try:
        rows = conn.execute(
            "SELECT k.call_id, k.claim_id, k.claim_day, k.rule FROM dated_call_claims k "
            "JOIN dated_calls c ON c.call_id = k.call_id "
            "LEFT JOIN dated_call_scores s ON s.call_id = k.call_id AND s.claim_id = k.claim_id "
            "WHERE c.status != 'rejected' AND s.id IS NULL ORDER BY k.call_id, k.claim_id"
        ).fetchall()
        for r in rows:
            res = score_claim(json.loads(r["rule"]) if r["rule"] else None,
                              r["claim_day"], store, cutoff,
                              ops.get((r["call_id"], r["claim_id"])))
            if res is None:
                out["waiting"] += 1
                continue
            conn.execute(
                "INSERT INTO dated_call_scores (call_id, claim_id, score, scored_by, "
                "scored_at, detail) VALUES (?,?,?,?,?,?)",
                (r["call_id"], r["claim_id"], res["score"], res["by"], cutoff, res["detail"]))
            out["scored"].append({"call_id": r["call_id"], "claim_id": r["claim_id"], **res})
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
        if own:
            store.close()
    return out


# ---------------------------------------------------------------------------
# The two counts (the features pass)
# ---------------------------------------------------------------------------
def _et_day(instant: str) -> str:
    t = dt.datetime.fromisoformat(str(instant).replace("Z", "+00:00"))
    if t.tzinfo is None:
        t = t.replace(tzinfo=dt.timezone.utc)
    return t.astimezone(ET).date().isoformat()


def _end_of_et_day(day: str) -> str:
    end = dt.datetime.combine(dt.date.fromisoformat(day), dt.time(23, 59, 59), ET)
    return end.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def count_rows(db: Any, as_of: Optional[str] = None, first_day: Optional[str] = None,
               cfg: Optional[dict] = None) -> list[dict]:
    """calc.viral_call_count.down and .up per ET day, from the first captured row
    to the as-of day, zeros included; [] while the register holds no row. Each
    day's count is knowable at that day's end (ET), or at the day's last capture
    when the as-of falls inside it."""
    cfg = cfg or config()
    keys = (cfg.get("counts") or {}).get("keys") or {}
    path = getattr(db, "path", None) or db
    try:
        conn = sqlite3.connect(f"file:{Path(str(path)).as_posix()}?mode=ro", uri=True)
        try:
            caps = conn.execute(
                "SELECT direction, captured_at FROM dated_calls WHERE status != 'rejected'"
            ).fetchall()
        finally:
            conn.close()
    except sqlite3.Error:
        return []                                     # no table yet: no rows yet
    cut = str(as_of or session.utc_iso())
    caps = [(d, c) for d, c in caps if str(c) <= cut]
    if not caps:
        return []
    by: dict[tuple[str, str], list[str]] = {}
    for d, c in caps:
        by.setdefault((_et_day(c), d), []).append(str(c))
    first = min(day for day, _ in by)
    last = _et_day(cut)
    out = []
    day = dt.date.fromisoformat(first)
    while day.isoformat() <= last:
        ds = day.isoformat()
        if not first_day or ds >= first_day:
            for direction in DIRECTIONS:
                got = by.get((ds, direction), [])
                avail = _end_of_et_day(ds)
                if ds == last and cut < avail:
                    avail = max(got) if got else cut
                out.append({"registry_key": keys[direction], "instrument": None,
                            "observed_at": ds, "available_at": avail,
                            "value": float(len(got)), "source": "calc",
                            "availability_kind": "observed"})
        day += dt.timedelta(days=1)
    return out


def count_line(store: Any, as_of: Optional[str], cfg: Optional[dict] = None) -> str:
    """The two counts as the attention input prints them: the newest day's, or
    'no rows yet'. No direction is read into them."""
    cfg = cfg or config()
    keys = cfg["counts"]["keys"]
    got = {}
    for d in DIRECTIONS:
        r = store.latest_as_of(keys[d], as_of)
        got[d] = r
    if not any(got.values()):
        return f"Viral calls captured: {cfg['counts']['no_rows']}."
    day = max(str(r["observed_at"])[:10] for r in got.values() if r)
    def v(d):
        return "0" if not got[d] else f"{int(got[d]['value_num'])}"
    return (f"Viral calls captured on {day}: crash calls {v('down')}, melt-up calls "
            f"{v('up')} (attention, no direction).")


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    import sys                                                  # noqa: PLC0415
    ap = argparse.ArgumentParser(description="The narrative register's dated public calls.")
    ap.add_argument("--db", default=None)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    sub.add_parser("seed")
    g = sub.add_parser("grade")
    g.add_argument("--as-of", default=None)
    sub.add_parser("counts")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if a.cmd == "seed":
        r = seed(a.db)
        print(f"inserted {r['inserted'] or 'none'}; synced {r['synced'] or 'none'}")
        for cid, why in r["refused"].items():
            print(f"REFUSED {cid}: {'; '.join(why)}")
        return 1 if r["refused"] else 0
    if a.cmd == "grade":
        r = grade_due(a.as_of, a.db)
        print(f"scored {len(r['scored'])}, waiting {r['waiting']}")
        for x in r["scored"]:
            print(f"  {x['call_id']}:{x['claim_id']} {x['score']} -- {x['detail']}")
        return 0
    if a.cmd == "counts":
        st = observations.ObservationStore(a.db)
        try:
            print(count_line(st, None))
        finally:
            st.close()
        return 0
    conn = connect(a.db)
    try:
        for c in conn.execute("SELECT * FROM dated_calls ORDER BY call_id").fetchall():
            n = conn.execute("SELECT count(*) FROM dated_call_claims WHERE call_id=?",
                             (c["call_id"],)).fetchone()[0]
            print(f"{c['call_id']:34} {c['status']:9} {c['direction']:5} "
                  f"expiry {c['expiry']}  claims {n}  {c['forecaster']}")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
