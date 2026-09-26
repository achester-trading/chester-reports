"""
The narrative register -- the stories the market is trading, as dated entities.

    python -m altdata.narratives list
    python -m altdata.narratives show fiscal_dominance
    python -m altdata.narratives seed            # sync config/narratives.yaml
    python -m altdata.narratives confirm <id>    # THE human gate (operator only)
    python -m altdata.narratives reject <id>

6c-2, Audit #3 §I and §F item 11, Daily Cascade v2 Part 0.4.

-----------------------------------------------------------------------------
A SEPARATE TABLE FROM THE DECISION REGISTER, ON PURPOSE
-----------------------------------------------------------------------------
The decision register is the operator's: it is what the system is graded against,
so nothing automated writes a decision (the deny list in .claude/settings.json and
the register's own write-time checks). This table is different in kind -- it
records what the MARKET believes, not what the operator decided -- so the sessions
may write it: seeds from config, state transitions on declared rules, and model
PROPOSALS. It lives in the same database for the same WAL and backup, and shares
nothing else with the decision register.

THE ONE HUMAN GATE is confirmation. A model may propose a story from the events; a
proposal sits at `status: proposed`, is never evaluated, and so can never reach
consensus, until the operator runs `confirm`. The Weekly prints that line beside
every pending proposal. `confirm` and `reject` are denied to unattended sessions in
.claude/settings.json beside the decision-register writes, so the gate is enforced
rather than remembered.

-----------------------------------------------------------------------------
WHAT A ROW HOLDS
-----------------------------------------------------------------------------
    narrative_id, name, status (active | proposed | rejected), state (emerging |
    consensus | contested | fading), direction, opened, last_changed,
    evidence_for[] and evidence_against[] as EVENT IDS, linked_dimensions
    {dimension: "+"|"-"}, linked_instruments[], prediction_market_contracts[]
    (empty until Part 27), implied_outcome {claim, metrics, comparison, quorum,
    horizon}, story_query, and the proposal's provenance.

DEFINITIONS COME FROM CONFIG, STATE FROM THE RULES. A seed syncs a config story's
name, direction, links and implied outcome every time it runs; it never touches
state, evidence, opened or last_changed, which only the transition rules write.
So a config edit changes what a story IS without rewriting what it has DONE.
"""

from __future__ import annotations

import json
import logging
import re
import sqlite3
from pathlib import Path
from typing import Any, Iterable, Optional

from . import observations, session

log = logging.getLogger("altdata.narratives")

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "config" / "narratives.yaml"
STORY_QUERIES_PATH = REPO / "config" / "story_queries.yaml"

STATES = ("emerging", "consensus", "contested", "fading")
STATUSES = ("active", "proposed", "rejected")
DIRECTIONS = ("+", "-")
COMPARISONS = ("up", "down", "magnitude_up", "magnitude_down")
ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]{2,47}$")

# The command the Weekly prints and the operator runs. Declared once so the printed
# line and the CLI cannot drift apart.
CONFIRM_COMMAND = "python -m altdata.narratives confirm {id}"
REJECT_COMMAND = "python -m altdata.narratives reject {id}"

SCHEMA = """
CREATE TABLE IF NOT EXISTS narratives (
    narrative_id     TEXT PRIMARY KEY,
    name             TEXT NOT NULL,
    status           TEXT NOT NULL,
    state            TEXT NOT NULL,
    direction        TEXT NOT NULL,
    opened           TEXT,
    last_changed     TEXT,
    evidence_for     TEXT NOT NULL DEFAULT '[]',
    evidence_against TEXT NOT NULL DEFAULT '[]',
    linked_dimensions TEXT NOT NULL,
    linked_instruments TEXT NOT NULL DEFAULT '[]',
    prediction_market_contracts TEXT NOT NULL DEFAULT '[]',
    implied_outcome  TEXT NOT NULL,
    story_query      TEXT,
    origin           TEXT NOT NULL,
    proposed_at      TEXT,
    proposed_by      TEXT,
    proposal_basis   TEXT NOT NULL DEFAULT '[]',
    decided_at       TEXT,
    decided_by       TEXT,
    config_version   TEXT,
    created_at       TEXT NOT NULL,
    updated_at       TEXT NOT NULL,
    CHECK (status IN ('active', 'proposed', 'rejected')),
    CHECK (state IN ('emerging', 'consensus', 'contested', 'fading'))
);

-- A PROPOSAL CANNOT BE ANYTHING BUT EMERGING. The rules never evaluate a proposed
-- story, so this is already true by construction; the trigger makes it true by
-- schema too, so a bug in a transition writer cannot promote an unconfirmed story.
CREATE TRIGGER IF NOT EXISTS narratives_proposal_stays_emerging
BEFORE UPDATE OF state ON narratives
WHEN NEW.status != 'active' AND NEW.state != 'emerging'
BEGIN SELECT RAISE(ABORT, 'only an active (confirmed) narrative changes state'); END;

-- THE REGISTER IS THE RECORD. A rejected proposal stays, with who rejected it.
CREATE TRIGGER IF NOT EXISTS narratives_no_delete
BEFORE DELETE ON narratives
BEGIN SELECT RAISE(ABORT, 'a narrative is not deletable; reject it instead'); END;
"""

# ONE ROW PER STORY PER SESSION: the inputs the rules read, the condition each rule
# met, and the state before and after. It is the record the replay gate recomputes
# (6c-2.5) -- every input here is a function of stored events and stored objects
# at `cutoff`, so a row that does not reproduce is a rule that read something it
# should not have.
EVAL_SCHEMA = """
CREATE TABLE IF NOT EXISTS narrative_evaluations (
    id             INTEGER PRIMARY KEY,
    narrative_id   TEXT NOT NULL,
    session        TEXT NOT NULL,
    cutoff         TEXT NOT NULL,
    evaluated_at   TEXT NOT NULL,
    rules_version  TEXT NOT NULL,
    state_before   TEXT NOT NULL,
    state_after    TEXT NOT NULL,
    transition     TEXT,
    inputs         TEXT NOT NULL,
    conditions     TEXT NOT NULL,
    runs           TEXT NOT NULL,
    run_id         TEXT,
    UNIQUE (narrative_id, session)
);
CREATE INDEX IF NOT EXISTS narrative_eval_asof
    ON narrative_evaluations (narrative_id, evaluated_at);

CREATE TRIGGER IF NOT EXISTS narrative_evaluations_immutable
BEFORE UPDATE ON narrative_evaluations
BEGIN SELECT RAISE(ABORT, 'an evaluation is the record; it is never edited'); END;
"""

JSON_FIELDS = ("evidence_for", "evidence_against", "linked_dimensions",
               "linked_instruments", "prediction_market_contracts",
               "implied_outcome", "proposal_basis")


class NarrativeError(ValueError):
    """A write the register refuses. The message says why."""


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
def load_config(path: Optional[Path] = None) -> dict:
    import yaml  # noqa: PLC0415
    with (path or CONFIG_PATH).open(encoding="utf-8") as fp:
        return yaml.safe_load(fp) or {}


def story_queries() -> dict:
    import yaml  # noqa: PLC0415
    try:
        with STORY_QUERIES_PATH.open(encoding="utf-8") as fp:
            return (yaml.safe_load(fp) or {}).get("queries") or {}
    except OSError:
        return {}


def dimension_names() -> list[str]:
    """The object's dimensions -- the only names a narrative may link to."""
    import sys  # noqa: PLC0415
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    import regime  # noqa: PLC0415
    return list((regime.load_config().get("dimensions") or {}).keys())


def probability_for(state: str, cfg: Optional[dict] = None) -> Optional[float]:
    """The probability a state asserts, or None where it asserts nothing."""
    cfg = cfg if cfg is not None else load_config()
    p = (cfg.get("probability_by_state") or {}).get(state)
    return None if p is None else float(p)


# ---------------------------------------------------------------------------
# Validation -- the same checks for a seed and a proposal
# ---------------------------------------------------------------------------
def validate_definition(nid: str, spec: dict, *, dims: Optional[list] = None,
                        queries: Optional[dict] = None) -> list[str]:
    """Every reason a definition is not writable. Empty means writable."""
    from . import derived  # noqa: PLC0415
    errs: list[str] = []
    if not ID_PATTERN.match(nid or ""):
        errs.append(f"id {nid!r} is not a lower-case slug (a-z, 0-9, _; 3-48)")
    if not str(spec.get("name") or "").strip():
        errs.append("no name")
    if not str(spec.get("direction") or "").strip():
        errs.append("no direction -- a story that claims nothing cannot be graded")
    dims = dims if dims is not None else dimension_names()
    links = spec.get("linked_dimensions") or {}
    if not isinstance(links, dict) or not links:
        errs.append("no linked_dimensions -- agreement with the data is how a "
                    "state is earned, and a story linked to nothing can never earn one")
    else:
        for d, sign in links.items():
            if d not in dims:
                errs.append(f"linked dimension {d!r} is not one of the object's "
                            f"{dims}")
            if str(sign) not in DIRECTIONS:
                errs.append(f"linked dimension {d!r} direction {sign!r} is not "
                            f"one of {DIRECTIONS}")
    q = spec.get("story_query")
    queries = queries if queries is not None else story_queries()
    if q and q not in queries:
        errs.append(f"story_query {q!r} is not declared in "
                    f"config/story_queries.yaml")
    io = spec.get("implied_outcome") or {}
    if not str(io.get("claim") or "").strip():
        errs.append("implied_outcome has no claim")
    metrics = list(io.get("metrics") or [])
    if not metrics:
        errs.append("implied_outcome names no metric -- nothing to resolve against")
    for m in metrics:
        if not derived.registry_entry(m):
            errs.append(f"implied_outcome metric {m!r} is not registered")
    if io.get("comparison") not in COMPARISONS:
        errs.append(f"implied_outcome comparison {io.get('comparison')!r} is not "
                    f"one of {COMPARISONS}")
    try:
        quorum = int(io.get("quorum") or 1)
    except (TypeError, ValueError):
        quorum = 0
    if not 1 <= quorum <= max(1, len(metrics)):
        errs.append(f"implied_outcome quorum {io.get('quorum')!r} must be 1.."
                    f"{len(metrics)}")
    hd, hdate = io.get("horizon_days"), io.get("horizon_date")
    if (hd is None) == (hdate is None):
        errs.append("implied_outcome needs exactly one of horizon_days and "
                    "horizon_date")
    elif hd is not None and not (isinstance(hd, int) and 1 <= hd <= 730):
        errs.append(f"horizon_days {hd!r} must be an integer 1..730")
    elif hdate is not None and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(hdate)):
        errs.append(f"horizon_date {hdate!r} is not YYYY-MM-DD")
    if (spec.get("prediction_market_contracts") or []):
        errs.append("prediction_market_contracts must be empty until Part 27 v1 "
                    "exists")
    return errs


# ---------------------------------------------------------------------------
# The store
# ---------------------------------------------------------------------------
class NarrativeRegister:
    """The narratives table, in the same database as the observations."""

    def __init__(self, path: Optional[str] = None) -> None:
        self.path = Path(path or observations.DEFAULT_DB)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.execute("PRAGMA busy_timeout = 5000")
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)
        self.conn.executescript(EVAL_SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "NarrativeRegister":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # -- reads --------------------------------------------------------------
    @staticmethod
    def _row(r: sqlite3.Row) -> dict:
        d = dict(r)
        for f in JSON_FIELDS:
            try:
                d[f] = json.loads(d.get(f) or ("{}" if f in (
                    "linked_dimensions", "implied_outcome") else "[]"))
            except (TypeError, ValueError):
                d[f] = {} if f in ("linked_dimensions", "implied_outcome") else []
        return d

    def get(self, nid: str) -> Optional[dict]:
        r = self.conn.execute("SELECT * FROM narratives WHERE narrative_id = ?",
                              (nid,)).fetchone()
        return self._row(r) if r else None

    def all(self, status: Optional[str] = None) -> list[dict]:
        if status:
            cur = self.conn.execute(
                "SELECT * FROM narratives WHERE status = ? ORDER BY narrative_id",
                (status,))
        else:
            cur = self.conn.execute("SELECT * FROM narratives ORDER BY narrative_id")
        return [self._row(r) for r in cur.fetchall()]

    def pending(self) -> list[dict]:
        return self.all("proposed")

    # -- seed -----------------------------------------------------------------
    def seed(self, cfg: Optional[dict] = None, today: Optional[str] = None) -> dict:
        """Insert config stories not yet present; sync definitions of those that are.

        Never writes state, evidence, opened or last_changed of an existing row --
        those belong to the rules. A new story is `active`, `emerging`, opened
        today, with no evidence.
        """
        cfg = cfg if cfg is not None else load_config()
        now = session.utc_iso()
        day = today or session.session_date()
        dims, queries = dimension_names(), story_queries()
        out = {"inserted": [], "synced": [], "refused": {}}
        for nid, spec in (cfg.get("narratives") or {}).items():
            spec = spec or {}
            errs = validate_definition(nid, spec, dims=dims, queries=queries)
            if errs:
                out["refused"][nid] = errs
                log.warning("narrative %s not seeded: %s", nid, "; ".join(errs))
                continue
            defn = _definition_columns(spec)
            have = self.get(nid)
            if have is None:
                self.conn.execute(
                    "INSERT INTO narratives (narrative_id, name, status, state, "
                    " direction, opened, last_changed, linked_dimensions, "
                    " linked_instruments, prediction_market_contracts, "
                    " implied_outcome, story_query, origin, config_version, "
                    " created_at, updated_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (nid, defn["name"], "active", "emerging", defn["direction"],
                     day, None, defn["linked_dimensions"],
                     defn["linked_instruments"],
                     defn["prediction_market_contracts"],
                     defn["implied_outcome"], defn["story_query"], "config",
                     cfg.get("version"), now, now))
                out["inserted"].append(nid)
            elif have.get("origin") == "config":
                self.conn.execute(
                    "UPDATE narratives SET name=?, direction=?, "
                    " linked_dimensions=?, linked_instruments=?, "
                    " prediction_market_contracts=?, implied_outcome=?, "
                    " story_query=?, config_version=?, updated_at=? "
                    "WHERE narrative_id=?",
                    (defn["name"], defn["direction"], defn["linked_dimensions"],
                     defn["linked_instruments"],
                     defn["prediction_market_contracts"], defn["implied_outcome"],
                     defn["story_query"], cfg.get("version"), now, nid))
                out["synced"].append(nid)
        self.conn.commit()
        return out

    # -- proposals ------------------------------------------------------------
    def propose(self, nid: str, spec: dict, basis_event_ids: Iterable[int], *,
                proposed_by: str, events_db: Optional[str] = None) -> dict:
        """Write one proposal, or raise NarrativeError with every reason.

        A proposal must cite the events it was drawn from, and every one of them
        must exist: a story proposed from nothing stored is a story nobody can
        trace, and the scan's rule is that every claim traces to an event.
        """
        errs = validate_definition(nid, spec)
        if self.get(nid) is not None:
            errs.append(f"{nid!r} already exists in the register")
        name = str(spec.get("name") or "").strip().lower()
        if name and any(r["name"].strip().lower() == name for r in self.all()):
            errs.append(f"a narrative named {spec.get('name')!r} already exists")
        basis = sorted({int(x) for x in (basis_event_ids or [])})
        if not basis:
            errs.append("no basis events -- a proposal must cite the stored events "
                        "it was drawn from")
        else:
            from . import events as ev_mod  # noqa: PLC0415
            with ev_mod.EventStore(events_db) as ev:
                found = {r[0] for r in ev.conn.execute(
                    "SELECT id FROM events WHERE id IN (%s)"
                    % ",".join("?" * len(basis)), basis)}
            missing = [b for b in basis if b not in found]
            if missing:
                errs.append(f"basis events {missing} are not in the events table")
        if not str(proposed_by or "").strip():
            errs.append("no proposed_by -- a proposal records who made it")
        if errs:
            raise NarrativeError("; ".join(errs))
        defn = _definition_columns(spec)
        now = session.utc_iso()
        self.conn.execute(
            "INSERT INTO narratives (narrative_id, name, status, state, direction, "
            " opened, last_changed, linked_dimensions, linked_instruments, "
            " prediction_market_contracts, implied_outcome, story_query, origin, "
            " proposed_at, proposed_by, proposal_basis, created_at, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (nid, defn["name"], "proposed", "emerging", defn["direction"], None,
             None, defn["linked_dimensions"], defn["linked_instruments"],
             defn["prediction_market_contracts"], defn["implied_outcome"],
             defn["story_query"], "proposal", now, proposed_by, json.dumps(basis),
             now, now))
        self.conn.commit()
        return self.get(nid)

    def confirm(self, nid: str, *, by: str, today: Optional[str] = None) -> dict:
        """THE HUMAN GATE. proposed -> active, opened today, emerging."""
        row = self._pending_or_raise(nid)
        now = session.utc_iso()
        self.conn.execute(
            "UPDATE narratives SET status='active', opened=?, decided_at=?, "
            " decided_by=?, updated_at=? WHERE narrative_id=?",
            (today or session.session_date(), now, by, now, nid))
        self.conn.commit()
        log.info("narrative %s confirmed by %s", nid, by)
        return self.get(nid) or row

    def reject(self, nid: str, *, by: str) -> dict:
        row = self._pending_or_raise(nid)
        now = session.utc_iso()
        self.conn.execute(
            "UPDATE narratives SET status='rejected', decided_at=?, decided_by=?, "
            " updated_at=? WHERE narrative_id=?", (now, by, now, nid))
        self.conn.commit()
        return self.get(nid) or row

    def _pending_or_raise(self, nid: str) -> dict:
        row = self.get(nid)
        if row is None:
            raise NarrativeError(f"no narrative {nid!r}")
        if row["status"] != "proposed":
            raise NarrativeError(f"{nid!r} is {row['status']}, not a pending "
                                 f"proposal -- only a proposal is confirmed or "
                                 f"rejected")
        return row


def _definition_columns(spec: dict) -> dict:
    io = dict(spec.get("implied_outcome") or {})
    io["quorum"] = int(io.get("quorum") or 1)
    return {
        "name": str(spec.get("name")).strip(),
        "direction": " ".join(str(spec.get("direction")).split()),
        "linked_dimensions": json.dumps(
            {str(k): str(v) for k, v in (spec.get("linked_dimensions") or {}).items()},
            sort_keys=True),
        "linked_instruments": json.dumps(list(spec.get("linked_instruments") or [])),
        "prediction_market_contracts": json.dumps(
            list(spec.get("prediction_market_contracts") or [])),
        "implied_outcome": json.dumps(
            {k: (" ".join(v.split()) if isinstance(v, str) else v)
             for k, v in io.items()}, sort_keys=True),
        "story_query": spec.get("story_query"),
    }


# ===========================================================================
# 6c-2.2 -- STATE TRANSITIONS ON DECLARED RULES
# ===========================================================================
def rules_version(cfg: dict, nid: str) -> str:
    """A hash of everything that decides this story's transitions.

    The rules block, the state probabilities, and the story's own definition and
    evidence rules. An evaluation records it, and the replay compares only rows made
    under the current one -- the regime's method-version argument: a deliberate
    change of rule is not a regression, and a replay that could not tell them apart
    would be switched off.
    """
    import hashlib  # noqa: PLC0415
    spec = (cfg.get("narratives") or {}).get(nid)
    blob = json.dumps({"rules": cfg.get("rules"), "spec": spec},
                      sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def _sessions_back(day: str, n: int) -> list[str]:
    """The `n` trading sessions ending at `day`, oldest first."""
    import datetime as dt  # noqa: PLC0415
    out = [day]
    d = dt.date.fromisoformat(day)
    while len(out) < n:
        d = session.previous_trading_session(d)
        out.append(d.isoformat())
    return list(reversed(out))


def _window_count(by_day: dict[str, int], sessions: list[str],
                  prior_session: str) -> int:
    """Headlines dated after `prior_session` and on or before the window's last.

    A weekend's headlines belong to the Monday window, because that is the session
    they were first knowable in; counting by calendar day would drop them.
    """
    last = sessions[-1]
    return sum(n for d, n in by_day.items() if prior_session < d <= last)


def attention(ev_conn: sqlite3.Connection, query: Optional[str], day: str,
              cutoff: str, short: int, long: int) -> dict:
    """Headline counts for the story's declared query, and their Δ and Δ².

    The windows are the last `short` and `long` sessions; Δ is a window against the
    one before it, Δ² is that change against the previous change. Every count is
    of rows knowable at `cutoff`.
    """
    out = {"query": query, "short_sessions": short, "long_sessions": long}
    if not query:
        out.update({"short": 0, "long": 0, "reason": "no story query declared"})
        return out
    span = _sessions_back(day, 3 * long + 1)
    earliest = span[0]
    by_day: dict[str, int] = {}
    for (obs,) in ev_conn.execute(
            "SELECT observed_at FROM events WHERE type = 'headline' "
            " AND available_at <= ? AND observed_at >= ? AND observed_at <= ? "
            " AND json_extract(payload, '$.query') = ?",
            (cutoff, earliest, cutoff, query)):
        d = session.session_date(obs)
        by_day[d] = by_day.get(d, 0) + 1

    def win(n: int, k: int) -> int:
        """The k-th window of n sessions back (0 = the latest)."""
        end = len(span) - 1 - k * n
        sess = span[end - n + 1:end + 1]
        return _window_count(by_day, sess, span[end - n])

    s0, s1, s2 = win(short, 0), win(short, 1), win(short, 2)
    l0, l1, l2 = win(long, 0), win(long, 1), win(long, 2)
    out.update({"short": s0, "long": l0,
                "delta_short": s0 - s1, "delta2_short": (s0 - s1) - (s1 - s2),
                "delta_long": l0 - l1, "delta2_long": (l0 - l1) - (l1 - l2)})
    return out


def agreement(obj: Optional[dict], links: dict) -> dict:
    """The share of linked dimensions pointing the way the story says.

    A dimension that is absent or flat is counted neither way. None when none is
    counted: undefined, not zero -- zero would read as the data disagreeing.
    """
    out: dict[str, Any] = {"object_session": None, "object_computed_at": None,
                           "agree": [], "disagree": [], "uncounted": {}}
    if not obj:
        out["share"] = None
        out["reason"] = "no market-state object at this cutoff"
        return out
    out["object_session"] = obj.get("session")
    out["object_computed_at"] = obj.get("computed_at")
    dims = obj.get("dimensions") or {}
    for d, want in sorted(links.items()):
        dd = dims.get(d) or {}
        got = dd.get("direction")
        if dd.get("state") is None:
            out["uncounted"][d] = "absent"
        elif got not in DIRECTIONS:
            out["uncounted"][d] = f"direction {got!r}"
        elif got == want:
            out["agree"].append(d)
        else:
            out["disagree"].append(d)
    n = len(out["agree"]) + len(out["disagree"])
    out["share"] = None if n == 0 else round(len(out["agree"]) / n, 4)
    return out


def _surprise_sign(store: Any, metric: str, event_day: str,
                   cutoff: str) -> Optional[int]:
    """The sign of the naive surprise for `metric`'s latest period on or before the
    release date, as knowable at `cutoff`. None when there is none."""
    from . import surprise  # noqa: PLC0415
    key = surprise.surprise_key(metric.split(".", 1)[1])
    rows = [r for r in store.as_of(key, as_of=cutoff)
            if str(r["observed_at"])[:10] <= event_day
            and r.get("value_num") is not None]
    if not rows:
        return None
    v = float(rows[-1]["value_num"])
    return 0 if v == 0 else (1 if v > 0 else -1)


def evidence(ev_conn: sqlite3.Connection, spec: dict, cutoff: str,
             window_days: int, store: Any) -> dict:
    """Event ids FOR and AGAINST, by the story's declared rules only."""
    import datetime as dt  # noqa: PLC0415
    rules = spec.get("evidence") or {}
    since = (dt.date.fromisoformat(cutoff[:10])
             - dt.timedelta(days=window_days)).isoformat()
    for_ids: list[int] = []
    against: list[int] = []
    unscored: dict[str, str] = {}

    er = rules.get("earnings") or {}
    if er:
        want = 1 if str(er.get("sign", "+")) == "+" else -1
        syms = {str(s).upper() for s in er.get("symbols") or []}
        for eid, payload in ev_conn.execute(
                "SELECT id, payload FROM events WHERE type = 'earnings' "
                " AND available_at <= ? AND observed_at >= ? AND observed_at <= ? "
                "ORDER BY id", (cutoff, since, cutoff)):
            p = json.loads(payload or "{}")
            if str(p.get("symbol") or "").upper() not in syms:
                continue
            s = p.get("surprise_pct")
            if not isinstance(s, (int, float)) or s == 0:
                unscored[str(eid)] = "no signed consensus surprise"
                continue
            (for_ids if (1 if s > 0 else -1) == want else against).append(eid)

    rs = rules.get("release_surprises") or {}
    for metric, sign in sorted(rs.items()):
        want = 1 if str(sign) == "+" else -1
        for eid, obs in ev_conn.execute(
                "SELECT e.id, e.observed_at FROM events e JOIN event_entities x "
                " ON x.event_id = e.id WHERE e.type = 'release' AND x.entity = ? "
                " AND e.available_at <= ? AND e.observed_at >= ? "
                " AND e.observed_at <= ? ORDER BY e.id",
                (metric, cutoff, since, cutoff)):
            sgn = _surprise_sign(store, metric, str(obs)[:10], cutoff)
            if not sgn:
                unscored[str(eid)] = f"no signed naive surprise for {metric}"
                continue
            (for_ids if sgn == want else against).append(eid)
    return {"for": sorted(set(for_ids)), "against": sorted(set(against)),
            "unscored": unscored, "window_days": window_days, "since": since}


def conditions(inputs: dict, rules: dict) -> dict:
    """Which rules' conditions hold on these inputs. Pure: no store, no clock."""
    att, agr, evd = inputs["attention"], inputs["agreement"], inputs["evidence"]
    short_n = int((rules.get("attention_sessions") or {}).get("short", 5))
    long_n = int((rules.get("attention_sessions") or {}).get("long", 20))
    share = agr.get("share")
    n_for, n_against = len(evd["for"]), len(evd["against"])
    a_long, a_short = att.get("long", 0), att.get("short", 0)
    rate_s = a_short / short_n
    rate_l = a_long / long_n

    c = rules.get("consensus") or {}
    consensus = (a_long >= int(c.get("min_attention_long", 0))
                 and share is not None
                 and share >= float(c.get("min_agreement", 1.0))
                 and n_for >= int(c.get("min_evidence_for", 1))
                 and (not c.get("evidence_for_must_exceed_against", True)
                      or n_for > n_against))
    k = rules.get("contested") or {}
    data_disagrees = share is not None and share <= float(k.get("max_agreement", 0))
    evidence_disagrees = (n_against >= int(k.get("min_evidence_against", 1))
                          and n_against >= n_for)
    contested = (a_long >= int(k.get("min_attention_long", 0))
                 and (data_disagrees or evidence_disagrees))
    f = rules.get("fading") or {}
    fading = (a_long > 0
              and rate_s < float(f.get("max_short_to_long_rate", 0)) * rate_l
              and (not f.get("require_short_delta_negative", True)
                   or att.get("delta_short", 0) < 0))
    r = rules.get("revive") or {}
    revive = (a_long >= int(r.get("min_attention_long", 0)) and a_long > 0
              and rate_s >= float(r.get("min_short_to_long_rate", 1.0)) * rate_l)
    return {"consensus": bool(consensus), "contested": bool(contested),
            "fading": bool(fading), "revive": bool(revive)}


# From each state, the transitions the rules allow, IN PRIORITY ORDER. Contested
# before consensus from emerging: a story the data or the evidence is already
# arguing with does not get to be consensus first. Contested before fading from
# consensus: a live argument is news, a quietening is not.
TRANSITIONS = {
    "emerging": (("contested", "contested"), ("consensus", "consensus")),
    "consensus": (("contested", "contested"), ("fading", "fading")),
    "contested": (("consensus", "consensus"), ("fading", "fading")),
    "fading": (("revive", "emerging"),),
}


def next_state(state: str, conds: dict, runs: dict, persistence: int
               ) -> tuple[str, Optional[str]]:
    """(state after, the rule that moved it) -- or (state, None)."""
    for cond, target in TRANSITIONS.get(state, ()):
        if conds.get(cond) and runs.get(cond, 0) >= persistence:
            return target, cond
    return state, None


def _runs(prior: list[dict], conds: dict) -> dict:
    """Consecutive evaluations, ending now, in which each condition held."""
    out = {}
    for name, now in conds.items():
        n = 1 if now else 0
        if now:
            for p in reversed(prior):
                if (p.get("conditions") or {}).get(name):
                    n += 1
                else:
                    break
        out[name] = n
    return out


def compute_inputs(nid: str, spec: dict, row: dict, day: str, cutoff: str,
                   cfg: dict, *, ev_conn: sqlite3.Connection, obj: Optional[dict],
                   store: Any) -> dict:
    """Everything the rules read for one story at one cutoff. Replayable."""
    rules = cfg.get("rules") or {}
    sess = rules.get("attention_sessions") or {}
    return {
        "attention": attention(ev_conn, row.get("story_query"), day, cutoff,
                               int(sess.get("short", 5)), int(sess.get("long", 20))),
        "agreement": agreement(obj, row.get("linked_dimensions") or {}),
        "evidence": evidence(ev_conn, spec, cutoff,
                             int(rules.get("evidence_window_days", 60)), store),
    }


def _prior_evaluations(conn: sqlite3.Connection, nid: str, before: str
                       ) -> list[dict]:
    out = []
    for r in conn.execute(
            "SELECT * FROM narrative_evaluations WHERE narrative_id = ? "
            " AND session < ? ORDER BY session", (nid, before)):
        d = dict(r)
        for f in ("inputs", "conditions", "runs"):
            d[f] = json.loads(d[f])
        out.append(d)
    return out


def evaluate(session_day: Optional[str] = None, as_of: Optional[str] = None, *,
             db_path: Optional[str] = None, run_id: Optional[str] = None,
             cfg: Optional[dict] = None, obj: Optional[dict] = None) -> dict:
    """Evaluate every ACTIVE story for one session. Idempotent per session.

    Runs in the close pass after the object is stored, so agreement reads the
    object for the session being evaluated. A story already evaluated for this
    session is left as it is: the first evaluation is the record.
    """
    import sys  # noqa: PLC0415
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    import regime  # noqa: PLC0415
    from . import events as ev_mod  # noqa: PLC0415

    cfg = cfg if cfg is not None else load_config()
    day = session_day or session.last_trading_session().isoformat()
    cutoff = observations.canonical_instant(
        as_of or session.utc_iso(timespec="microseconds"))
    run_id = run_id or session.new_run_id("narratives")
    rules = cfg.get("rules") or {}
    persistence = int(rules.get("persistence_sessions", 3))
    out: dict[str, Any] = {"session": day, "cutoff": cutoff, "run_id": run_id,
                           "evaluated": [], "skipped": {}, "transitions": []}
    store = observations.ObservationStore(db_path)
    try:
        if obj is None:
            obj = regime.latest(as_of=cutoff, store=store)
        with NarrativeRegister(db_path) as reg, ev_mod.EventStore(db_path) as ev:
            out["seeded"] = reg.seed(cfg)
            for row in reg.all("active"):
                nid = row["narrative_id"]
                spec = (cfg.get("narratives") or {}).get(nid) or {}
                if reg.conn.execute(
                        "SELECT 1 FROM narrative_evaluations WHERE narrative_id=? "
                        " AND session=?", (nid, day)).fetchone():
                    out["skipped"][nid] = "already evaluated for this session"
                    continue
                if row.get("opened") and row["opened"] > day:
                    out["skipped"][nid] = f"opened {row['opened']}, after {day}"
                    continue
                inputs = compute_inputs(nid, spec, row, day, cutoff, cfg,
                                        ev_conn=ev.conn, obj=obj, store=store)
                conds = conditions(inputs, rules)
                prior = _prior_evaluations(reg.conn, nid, day)
                runs = _runs(prior, conds)
                before = prior[-1]["state_after"] if prior else row["state"]
                after, rule = next_state(before, conds, runs, persistence)
                now = session.utc_iso(timespec="microseconds")
                reg.conn.execute(
                    "INSERT INTO narrative_evaluations (narrative_id, session, "
                    " cutoff, evaluated_at, rules_version, state_before, "
                    " state_after, transition, inputs, conditions, runs, run_id) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (nid, day, cutoff, now, rules_version(cfg, nid), before, after,
                     rule, json.dumps(inputs, sort_keys=True, default=str),
                     json.dumps(conds, sort_keys=True),
                     json.dumps(runs, sort_keys=True), run_id))
                reg.conn.execute(
                    "UPDATE narratives SET state=?, evidence_for=?, "
                    " evidence_against=?, last_changed=COALESCE(?, last_changed), "
                    " updated_at=? WHERE narrative_id=?",
                    (after, json.dumps(inputs["evidence"]["for"]),
                     json.dumps(inputs["evidence"]["against"]),
                     day if rule else None, now, nid))
                reg.conn.commit()
                out["evaluated"].append(nid)
                if rule:
                    tr = {"narrative_id": nid, "session": day, "from": before,
                          "to": after, "rule": rule,
                          "alert_path": cfg.get("transition_alert_path",
                                                "report_only")}
                    out["transitions"].append(tr)
                    log.info("narrative %s: %s -> %s (%s)", nid, before, after,
                             rule)
    finally:
        store.close()
    return out


def state_as_of(conn: sqlite3.Connection, nid: str, cutoff: str
                ) -> Optional[str]:
    """The story's state as it was knowable at `cutoff`, or None if unknowable.

    From the evaluations, which carry their own instant -- never from the
    register row, which holds only the latest state. A story with no evaluation
    yet is in its opening state, emerging.
    """
    r = conn.execute(
        "SELECT state_after FROM narrative_evaluations WHERE narrative_id = ? "
        " AND evaluated_at <= ? ORDER BY evaluated_at DESC, id DESC LIMIT 1",
        (nid, observations.canonical_instant(cutoff))).fetchone()
    return r[0] if r else "emerging"


def transitions_since(since: str, as_of: Optional[str] = None,
                      db_path: Optional[str] = None) -> list[dict]:
    """Every state change evaluated after `since` and knowable at `as_of`."""
    cutoff = observations.canonical_instant(as_of or session.utc_iso(
        timespec="microseconds"))
    with NarrativeRegister(db_path) as reg:
        return [dict(r) for r in reg.conn.execute(
            "SELECT narrative_id, session, state_before, state_after, transition, "
            "       evaluated_at FROM narrative_evaluations "
            "WHERE transition IS NOT NULL AND evaluated_at > ? "
            "  AND evaluated_at <= ? ORDER BY evaluated_at",
            (observations.canonical_instant(since), cutoff))]


def replay(db_path: Optional[str] = None, cfg: Optional[dict] = None) -> dict:
    """Recompute every stored evaluation from stored events and objects.

    Inputs, conditions, runs and the state after must match EXACTLY. Rows made
    under a different rules_version are counted and skipped, not compared.
    """
    import sys  # noqa: PLC0415
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    import regime  # noqa: PLC0415
    from . import events as ev_mod  # noqa: PLC0415
    cfg = cfg if cfg is not None else load_config()
    rules = cfg.get("rules") or {}
    persistence = int(rules.get("persistence_sessions", 3))
    out = {"compared": 0, "matched": 0, "mismatches": [], "other_version": 0}
    store = observations.ObservationStore(db_path)
    try:
        with NarrativeRegister(db_path) as reg, ev_mod.EventStore(db_path) as ev:
            rows = [dict(r) for r in reg.conn.execute(
                "SELECT * FROM narrative_evaluations ORDER BY narrative_id, session")]
            for r in rows:
                nid = r["narrative_id"]
                if r["rules_version"] != rules_version(cfg, nid):
                    out["other_version"] += 1
                    continue
                row = reg.get(nid) or {}
                spec = (cfg.get("narratives") or {}).get(nid) or {}
                obj = regime.latest(as_of=r["cutoff"], store=store)
                inputs = compute_inputs(nid, spec, row, r["session"], r["cutoff"],
                                        cfg, ev_conn=ev.conn, obj=obj, store=store)
                conds = conditions(inputs, rules)
                prior = _prior_evaluations(reg.conn, nid, r["session"])
                runs = _runs(prior, conds)
                before = prior[-1]["state_after"] if prior else r["state_before"]
                after, rule = next_state(before, conds, runs, persistence)
                got = {"inputs": json.loads(json.dumps(inputs, sort_keys=True,
                                                       default=str)),
                       "conditions": conds, "runs": runs, "state_before": before,
                       "state_after": after, "transition": rule}
                want = {"inputs": json.loads(r["inputs"]),
                        "conditions": json.loads(r["conditions"]),
                        "runs": json.loads(r["runs"]),
                        "state_before": r["state_before"],
                        "state_after": r["state_after"],
                        "transition": r["transition"]}
                out["compared"] += 1
                if got == want:
                    out["matched"] += 1
                else:
                    diff = sorted(k for k in want if got.get(k) != want[k])
                    out["mismatches"].append({"narrative_id": nid,
                                              "session": r["session"],
                                              "fields": diff})
    finally:
        store.close()
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _operator() -> str:
    import getpass  # noqa: PLC0415
    try:
        return f"operator:{getpass.getuser()}"
    except Exception:                                          # noqa: BLE001
        return "operator"


def _main(argv: list[str]) -> int:
    import argparse  # noqa: PLC0415
    import sys  # noqa: PLC0415
    ap = argparse.ArgumentParser(description="The narrative register.")
    ap.add_argument("--db", default=None)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    sh = sub.add_parser("show")
    sh.add_argument("id")
    sub.add_parser("seed")
    for name in ("confirm", "reject"):
        c = sub.add_parser(name)
        c.add_argument("id")
    evp = sub.add_parser("evaluate", help="the close pass's step: one session")
    evp.add_argument("--session", default=None)
    evp.add_argument("--as-of", default=None)
    sub.add_parser("replay", help="recompute every stored evaluation")
    tp = sub.add_parser("transitions")
    tp.add_argument("--since", default="1970-01-01T00:00:00Z")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if a.cmd == "evaluate":
        r = evaluate(a.session, a.as_of, db_path=a.db)
        print(f"session {r['session']} cutoff {r['cutoff']} run {r['run_id']}")
        print(f"  evaluated   : {', '.join(r['evaluated']) or 'none'}")
        for nid, why in r["skipped"].items():
            print(f"  skipped     : {nid} ({why})")
        for t in r["transitions"]:
            print(f"  TRANSITION  : {t['narrative_id']} {t['from']} -> {t['to']} "
                  f"({t['rule']}; alert {t['alert_path']})")
        return 0
    if a.cmd == "replay":
        r = replay(a.db)
        print(f"replayed {r['compared']}: {r['matched']} exact, "
              f"{len(r['mismatches'])} mismatched, {r['other_version']} under "
              f"another rules version")
        for m in r["mismatches"][:20]:
            print(f"  MISMATCH {m['narrative_id']} {m['session']}: {m['fields']}")
        return 1 if r["mismatches"] else 0
    if a.cmd == "transitions":
        for t in transitions_since(a.since, db_path=a.db):
            print(f"{t['session']}  {t['narrative_id']:24} {t['state_before']} -> "
                  f"{t['state_after']}  ({t['transition']})")
        return 0
    with NarrativeRegister(a.db) as reg:
        try:
            if a.cmd == "seed":
                r = reg.seed()
                print(f"inserted {r['inserted'] or 'none'}; synced "
                      f"{r['synced'] or 'none'}")
                for nid, why in r["refused"].items():
                    print(f"REFUSED {nid}: {'; '.join(why)}")
                return 1 if r["refused"] else 0
            if a.cmd == "confirm":
                r = reg.confirm(a.id, by=_operator())
                print(f"confirmed {a.id}: active, {r['state']}, opened {r['opened']}")
                return 0
            if a.cmd == "reject":
                reg.reject(a.id, by=_operator())
                print(f"rejected {a.id}")
                return 0
            if a.cmd == "show":
                r = reg.get(a.id)
                if r is None:
                    print(f"no narrative {a.id!r}")
                    return 1
                print(json.dumps(r, indent=2, sort_keys=True, default=str))
                return 0
        except NarrativeError as exc:
            print(f"REFUSED: {exc}", file=sys.stderr)
            return 2
        rows = reg.all()
    if not rows:
        print("the register is empty -- `python -m altdata.narratives seed`")
        return 0
    for r in rows:
        print(f"{r['narrative_id']:24} {r['status']:9} {r['state']:10} "
              f"opened {r['opened'] or '-':10}  for {len(r['evidence_for'])} "
              f"against {len(r['evidence_against'])}  {r['name']}")
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
