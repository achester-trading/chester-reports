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
    -- The probability-ledger row emitted when this evaluation moved the story
    -- INTO a state that carries a probability (6c-2.4). NULL otherwise.
    forecast_id    TEXT,
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
    bd = io.get("baseline_date")
    if bd is not None:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(bd)):
            errs.append(f"baseline_date {bd!r} is not YYYY-MM-DD")
        elif hdate is None or str(bd) >= str(hdate):
            errs.append("a baseline_date needs a later horizon_date -- a fixed "
                        "baseline is a dated window, both ends declared")
    if (spec.get("prediction_market_contracts") or []):
        errs.append("prediction_market_contracts must be empty until Part 27 v1 "
                    "exists")
    return errs


EVIDENCE_KINDS = ("earnings", "release_surprises", "headlines", "series_moves")


def validate_evidence(spec: dict) -> list[str]:
    """Every reason a CONFIG story's evidence rule is not usable. (6c-3)

    A seeded story must carry one: without evidence FOR, the consensus rule's
    `min_evidence_for` can never hold, and a story that cannot reach consensus
    is a story the register can never grade by its state. Each declared kind is
    checked for shape, and a headline rule is held to its own examples -- a
    pattern that does not score the title it was written for is a typo, and it
    would otherwise fail silently as "unscored" forever.
    """
    from . import derived  # noqa: PLC0415
    rules = spec.get("evidence") or {}
    errs: list[str] = []
    if not rules:
        return ["no evidence rule -- a story with no way to gather evidence FOR "
                "can never reach consensus"]
    for kind in rules:
        if kind not in EVIDENCE_KINDS:
            errs.append(f"evidence kind {kind!r} is not one of {EVIDENCE_KINDS}")
    for m, r in (rules.get("series_moves") or {}).items():
        r = r or {}
        if not derived.registry_entry(m):
            errs.append(f"series_moves metric {m!r} is not registered")
        if str(r.get("sign")) not in DIRECTIONS:
            errs.append(f"series_moves {m!r} sign {r.get('sign')!r} is not "
                        f"one of {DIRECTIONS}")
        if not 0 < float(r.get("percentile") or 0) < 50:
            errs.append(f"series_moves {m!r} percentile must be in (0, 50)")
    hr = rules.get("headlines") or {}
    if hr:
        if not spec.get("story_query"):
            errs.append("a headline rule needs the story's own story_query")
        phases = ("before", "after") if hr.get("calendar_claim") else (None,)
        pats = []
        for ph in phases:
            block = (hr.get(ph) or {}) if ph else hr
            if not (block.get("for") or []):
                errs.append(f"headlines{'.' + ph if ph else ''} declares no FOR "
                            f"pattern")
            pats += list(block.get("for") or []) + list(block.get("against") or [])
        pats += [hr["require"]] if hr.get("require") else []
        for p in pats:
            try:
                re.compile(p)
            except re.error as exc:
                errs.append(f"headline pattern {p!r} does not compile: {exc}")
        ex = hr.get("examples") or {}
        if not ex:
            errs.append("a headline rule declares no examples to be held to")
        want = {"for": 1, "against": -1, "unscored": 0,
                "before_for": 1, "after_for": 1,
                "before_against": -1, "after_against": -1}
        for label, title in ex.items():
            ph = label.split("_", 1)[0] if label.startswith(("before_",
                                                              "after_")) else None
            if label not in want:
                errs.append(f"headline example label {label!r} is not one of "
                            f"{sorted(want)}")
                continue
            try:
                got = score_headline(title, hr, ph)
            except re.error:
                continue
            if (got or 0) != want[label]:
                errs.append(f"headline example {label} {title!r} scores {got}, "
                            f"not {want[label]}")
    return errs


def validate_hypotheses(spec: dict) -> list[str]:
    """Every reason a story's dated hypotheses are not emittable. (6c-3)"""
    from . import derived  # noqa: PLC0415
    errs: list[str] = []
    for hid, h in (spec.get("hypotheses") or {}).items():
        h = h or {}
        where = f"hypothesis {hid!r}"
        if not ID_PATTERN.match(str(hid)):
            errs.append(f"{where}: id is not a slug")
        if not str(h.get("claim") or "").strip():
            errs.append(f"{where}: no claim")
        if not derived.registry_entry(str(h.get("metric") or "")):
            errs.append(f"{where}: metric {h.get('metric')!r} is not registered")
        if h.get("comparison") not in COMPARISONS:
            errs.append(f"{where}: comparison {h.get('comparison')!r}")
        bd, hd = str(h.get("baseline_date") or ""), str(h.get("horizon_date") or "")
        if not (re.fullmatch(r"\d{4}-\d{2}-\d{2}", bd)
                and re.fullmatch(r"\d{4}-\d{2}-\d{2}", hd) and bd < hd):
            errs.append(f"{where}: needs baseline_date < horizon_date, both "
                        f"YYYY-MM-DD -- a hypothesis is decidable ex ante or not "
                        f"at all")
        pr = h.get("prior") or {}
        if pr.get("rule") not in PRIOR_RULES:
            errs.append(f"{where}: prior rule {pr.get('rule')!r} is not one of "
                        f"{PRIOR_RULES}")
        if not str(pr.get("table") or "").startswith("baserate."):
            errs.append(f"{where}: the prior must cite a stored base-rate table")
        try:
            if float(pr.get("k")) <= 0:
                raise ValueError
        except (TypeError, ValueError):
            errs.append(f"{where}: prior k must be a positive number")
        if not str(h.get("statement_cited") or "").strip():
            errs.append(f"{where}: cite the paper the statement comes from")
    return errs


def validate_config_story(nid: str, spec: dict, **kw) -> list[str]:
    """What seed() requires of a story declared in config: the definition, an
    evidence rule that can produce evidence FOR, and emittable hypotheses."""
    return (validate_definition(nid, spec, **kw) + validate_evidence(spec)
            + validate_hypotheses(spec))


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
            errs = validate_config_story(nid, spec, dims=dims, queries=queries)
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

    # 6c-3: headlines under the story's own query, signed by declared patterns.
    hr = rules.get("headlines") or {}
    if hr:
        query = spec.get("story_query")
        pivot = None
        if hr.get("calendar_claim"):
            pivot = calendar_date(ev_conn, str(hr["calendar_claim"]), cutoff)
        for eid, obs, title in ev_conn.execute(
                "SELECT id, observed_at, title FROM events WHERE type = 'headline' "
                " AND available_at <= ? AND observed_at >= ? AND observed_at <= ? "
                " AND json_extract(payload, '$.query') = ? ORDER BY id",
                (cutoff, since, cutoff, query)):
            if hr.get("calendar_claim") and pivot is None:
                unscored[str(eid)] = (f"calendar claim {hr['calendar_claim']} is "
                                      f"not in the events table at this cutoff")
                continue
            phase = (None if pivot is None else
                     ("before" if str(obs)[:10] < pivot else "after"))
            sgn = score_headline(title, hr, phase)
            if sgn is None:
                continue                   # not this rule's institution
            if sgn == 0:
                unscored[str(eid)] = "no declared pattern, or both, matched"
                continue
            (for_ids if sgn > 0 else against).append(eid)

    # 6c-3: the story's own prices, by the close report's move percentile.
    series_for: list[dict] = []
    series_against: list[dict] = []
    for metric, r in sorted((rules.get("series_moves") or {}).items()):
        mv = series_move(metric, r or {}, cutoff, store)
        if mv.get("sign") == 1:
            series_for.append(mv["item"])
        elif mv.get("sign") == -1:
            series_against.append(mv["item"])
        else:
            unscored[f"series:{metric}"] = mv["reason"]
    return {"for": sorted(set(for_ids)), "against": sorted(set(against)),
            "series_for": series_for, "series_against": series_against,
            "unscored": unscored, "window_days": window_days, "since": since}


def calendar_date(ev_conn: sqlite3.Connection, claim_id: str, cutoff: str
                  ) -> Optional[str]:
    """The date of a claims-registry calendar event, as knowable at `cutoff`."""
    r = ev_conn.execute(
        "SELECT observed_at FROM events WHERE type = 'scheduled' "
        " AND json_extract(payload, '$.claim_id') = ? AND available_at <= ? "
        "ORDER BY available_at DESC, id DESC LIMIT 1", (claim_id, cutoff)).fetchone()
    return str(r[0])[:10] if r else None


def score_headline(title: Optional[str], rule: dict,
                   phase: Optional[str] = None) -> Optional[int]:
    """+1 FOR, -1 AGAINST, 0 unscored, None when `require` does not match.

    Declared patterns only. Pure, so the validator can hold each rule to the
    examples it declares.
    """
    t = str(title or "")
    req = rule.get("require")
    if req and not re.search(req, t):
        return None
    pats = rule.get(phase) if phase else rule
    pats = pats or {}
    f = any(re.search(p, t) for p in pats.get("for") or [])
    a = any(re.search(p, t) for p in pats.get("against") or [])
    return 1 if f and not a else (-1 if a and not f else 0)


def series_move(metric: str, rule: dict, cutoff: str, store: Any) -> dict:
    """{sign, item} for a move at or beyond the declared percentile, else a reason.

    The same delta_percentile the close report prints, so the evidence and the
    WHAT CHANGED block cannot disagree about whether a move was large.
    """
    from . import derived  # noqa: PLC0415
    horizon = int(rule.get("horizon") or 5)
    pct = float(rule.get("percentile") or 10)
    want = 1 if str(rule.get("sign", "+")) == "+" else -1
    d = derived.delta_percentile(metric, as_of=cutoff, horizon=horizon,
                                 store=store)
    if d.get("percentile") is None:
        return {"sign": 0, "reason": f"{metric}: "
                f"{d.get('absent_reason') or 'no move percentile'}"}
    age, _ = derived.sessions_between(str(d["to_date"])[:10], str(cutoff)[:10])
    if age > int(rule.get("max_age_sessions") or 3):
        return {"sign": 0, "reason": f"{metric}: last print {d['to_date']}, {age} "
                f"sessions before the cutoff -- stale, not counted"}
    p = float(d["percentile"])
    moved = 1 if p >= 100.0 - pct else (-1 if p <= pct else 0)
    if moved == 0:
        return {"sign": 0, "reason": f"{metric}: {horizon}-observation move at "
                f"percentile {p:.1f}, inside {pct:g}..{100 - pct:g}"}
    item = {"id": f"{metric}@{d['to_date']}/{horizon}", "metric": metric,
            "from_date": d.get("from_date"), "to_date": d.get("to_date"),
            "change": d.get("change"), "delta_unit": d.get("delta_unit"),
            "percentile": p, "n": d.get("n")}
    return {"sign": 1 if moved == want else -1, "item": item}


def conditions(inputs: dict, rules: dict) -> dict:
    """Which rules' conditions hold on these inputs. Pure: no store, no clock."""
    att, agr, evd = inputs["attention"], inputs["agreement"], inputs["evidence"]
    short_n = int((rules.get("attention_sessions") or {}).get("short", 5))
    long_n = int((rules.get("attention_sessions") or {}).get("long", 20))
    share = agr.get("share")
    # Event ids and series moves count alike: each is one declared fact.
    n_for = len(evd["for"]) + len(evd.get("series_for") or [])
    n_against = len(evd["against"]) + len(evd.get("series_against") or [])
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
                # A STORY ENTERING A STATE THAT CLAIMS SOMETHING IS A FORECAST.
                # Emitted before the evaluation row so the row can name it.
                forecast_id = None
                if rule and after != before:
                    forecast_id = emit_forecast(nid, row, after, day, cutoff, cfg,
                                                store, db_path, run_id)
                now = session.utc_iso(timespec="microseconds")
                reg.conn.execute(
                    "INSERT INTO narrative_evaluations (narrative_id, session, "
                    " cutoff, evaluated_at, rules_version, state_before, "
                    " state_after, transition, inputs, conditions, runs, run_id, "
                    " forecast_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (nid, day, cutoff, now, rules_version(cfg, nid), before, after,
                     rule, json.dumps(inputs, sort_keys=True, default=str),
                     json.dumps(conds, sort_keys=True),
                     json.dumps(runs, sort_keys=True), run_id, forecast_id))
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
                          "to": after, "rule": rule, "forecast_id": forecast_id,
                          "alert_path": cfg.get("transition_alert_path",
                                                "report_only")}
                    out["transitions"].append(tr)
                    log.info("narrative %s: %s -> %s (%s)", nid, before, after,
                             rule)
            # DATED HYPOTHESES, independent of state: each active story's are
            # entered once, before their window opens (6c-3).
            out["hypotheses"] = {}
            for row in reg.all("active"):
                nid = row["narrative_id"]
                spec = (cfg.get("narratives") or {}).get(nid) or {}
                if spec.get("hypotheses") and not (row.get("opened")
                                                   and row["opened"] > day):
                    out["hypotheses"][nid] = emit_hypotheses(
                        nid, spec, day, cutoff, store, db_path, run_id)
    finally:
        store.close()
    # THE SAME PASS RESOLVES WHAT IS DUE. A forecast whose horizon has passed is
    # scored here and by the grader (altdata.grader.run); both call one resolver,
    # which is idempotent, so running twice resolves once.
    try:
        out["resolution"] = resolve_due(cutoff, db_path=db_path)
    except Exception as exc:                                   # noqa: BLE001
        out["resolution"] = {"error": f"{type(exc).__name__}: {exc}"}
    return out


# ===========================================================================
# 6c-2.4 -- GRADING: every claiming state enters the probability ledger
# ===========================================================================
# The register grades its own state machine. A story that ENTERS a state carrying a
# probability (config: probability_by_state -- consensus 0.70, fading 0.30) emits
# one forecast at that instant: its implied outcome, with the horizon measured from
# the entry, a resolution criterion that is MACHINE-READABLE and declared at
# emission, and the baseline value of every metric as knowable at that cutoff.
# Emerging and contested emit nothing (see the config for why).
#
# RESOLUTION READS THE STORE, never a judgement: for each metric, the latest
# observation dated after the baseline's own date and on or before the horizon,
# compared with the baseline under the declared comparison; the outcome is 1 when
# at least `quorum` metrics meet it. A metric with no newer observation by the
# horizon is waited on for RESOLUTION_GRACE_DAYS -- a quarterly filing lands weeks
# after its quarter -- and then counted as not met, which is stated on the row.
LEDGER_SOURCE = "narrative_register"
CRITERION_KIND = "narrative-implied-outcome-v1"
RESOLUTION_GRACE_DAYS = 45


def horizon_of(io: dict, day: str) -> str:
    import datetime as dt  # noqa: PLC0415
    if io.get("horizon_date"):
        return str(io["horizon_date"])
    return (dt.date.fromisoformat(day)
            + dt.timedelta(days=int(io.get("horizon_days") or 0))).isoformat()


def emit_forecast(nid: str, row: dict, state: str, day: str, cutoff: str,
                  cfg: dict, store: Any, db_path: Optional[str],
                  run_id: str) -> Optional[str]:
    """One ledger row for a story entering a claiming state, or None."""
    from . import probability_ledger  # noqa: PLC0415
    p = probability_for(state, cfg)
    if p is None:
        return None
    io = row.get("implied_outcome") or {}
    baseline = {}
    # A FIXED baseline_date (6c-3) is read at RESOLUTION, as the close on or
    # before that date -- the outcome is a dated window, not "since emission".
    if not io.get("baseline_date"):
        for m in io.get("metrics") or []:
            last = store.latest_as_of(m, as_of=cutoff)
            baseline[m] = (None if not last or last.get("value_num") is None else
                           {"observed_at": str(last["observed_at"])[:10],
                            "value": float(last["value_num"])})
    criterion = {"kind": CRITERION_KIND, "narrative_id": nid, "state": state,
                 "claim": io.get("claim"), "metrics": io.get("metrics"),
                 "comparison": io.get("comparison"),
                 "quorum": int(io.get("quorum") or 1),
                 "horizon_date": horizon_of(io, day), "baseline": baseline,
                 "grace_days": RESOLUTION_GRACE_DAYS}
    if io.get("baseline_date"):
        criterion["baseline_date"] = str(io["baseline_date"])
    with probability_ledger.ProbabilityLedger(db_path) as led:
        return led.record(
            source=LEDGER_SOURCE,
            claim=f"[{nid}] {io.get('claim')}",
            probability=p, horizon_date=criterion["horizon_date"],
            resolution_criterion=json.dumps(criterion, sort_keys=True),
            scenario_set=f"narrative:{nid}", emitted_at=cutoff,
            emitted_by=run_id)


def close_on_or_before(store: Any, metric: str, day: str, as_of: str
                       ) -> Optional[dict]:
    """{observed_at, value} of the last print dated on or before `day`,
    knowable at `as_of`. The rule tools/base_rates.close_on_or_before applies."""
    rows = [r for r in store.as_of(metric, as_of=as_of)
            if str(r["observed_at"])[:10] <= str(day)[:10]
            and r.get("value_num") is not None]
    if not rows:
        return None
    return {"observed_at": str(rows[-1]["observed_at"])[:10],
            "value": float(rows[-1]["value_num"])}


def _complete_through(store: Any, metric: str, day: str, as_of: str) -> bool:
    """Whether a print dated AFTER `day` is knowable -- so the close on or before
    it can no longer be superseded by a late row for that date."""
    return any(str(r["observed_at"])[:10] > str(day)[:10]
               for r in store.as_of(metric, as_of=as_of))


# ---------------------------------------------------------------------------
# 6c-3 -- DATED HYPOTHESES: the base rate as prior, entered once, ex ante
# ---------------------------------------------------------------------------
HYPOTHESIS_KIND = "narrative-dated-hypothesis-v1"
PRIOR_RULES = ("shrink_to_unconditional",)


def _dig(d: Any, path: str) -> Any:
    for part in str(path).split("."):
        if not isinstance(d, dict):
            return None
        d = d.get(part)
    return d


def hypothesis_prior(prior: dict, table: Optional[dict]) -> dict:
    """The prior and everything a reader needs to weigh it, or why there is none.

    shrink_to_unconditional: (hits + k * p0) / (n + k), p0 the unconditional
    rate of the same window. The raw rate, both n, k and the binomial p of the
    conditional count under p0 travel with it. A result of 0 or 1 is refused
    -- the ledger refuses it anyway, and a certainty from a finite sample is
    the claim Evidence and Inference exists to forbid.
    """
    if not table:
        return {"probability": None,
                "reason": f"{prior.get('table')} is not stored at this cutoff -- "
                          f"tools/base_rates.py compute has not run with it"}
    cond = _dig(table, prior.get("conditional")) or {}
    unc = _dig(table, prior.get("unconditional")) or {}
    n, hits, p0 = cond.get("n"), cond.get("hits"), unc.get("hit_rate")
    if not n or hits is None or p0 is None:
        return {"probability": None,
                "reason": f"{prior.get('table')} carries no complete "
                          f"{prior.get('conditional')} / {prior.get('unconditional')}"}
    k = float(prior.get("k"))
    p = round((float(hits) + k * float(p0)) / (float(n) + k), 4)
    out = {"probability": p, "rule": prior.get("rule"), "k": k,
           "table": prior.get("table"),
           "table_computed_at": table.get("computed_at"),
           "table_method": table.get("method_version"),
           "conditional": {"field": prior.get("conditional"), "n": n,
                           "hits": hits, "hit_rate": cond.get("hit_rate"),
                           "binomial_p_vs_unconditional":
                               cond.get("binomial_p_vs_all_years")},
           "unconditional": {"field": prior.get("unconditional"),
                             "n": unc.get("n"), "hit_rate": p0}}
    if not 0.0 < p < 1.0:
        return {**out, "probability": None,
                "reason": f"the rule gives {p}; no ledger row carries 0 or 1"}
    return out


def emit_hypotheses(nid: str, spec: dict, day: str, cutoff: str, store: Any,
                    db_path: Optional[str], run_id: str) -> dict:
    """Enter each dated hypothesis once, before its window opens.

    IDEMPOTENT by scenario_set (`hypothesis:<story>:<id>`): a hypothesis is one
    forecast, and re-emitting it on every close would be the same claim scored
    many times. EX ANTE OR NOT AT ALL: a hypothesis whose baseline date has
    arrived is not emitted -- a forecast of a window already open is partly an
    observation -- and the reason is returned for the close pass to print.
    """
    from . import probability_ledger  # noqa: PLC0415
    out: dict[str, Any] = {"emitted": [], "held": {}}
    hyps = spec.get("hypotheses") or {}
    if not hyps:
        return out
    with probability_ledger.ProbabilityLedger(db_path) as led:
        have = {r["scenario_set"] for r in led.conn.execute(
            "SELECT scenario_set FROM probabilities WHERE source = ?",
            (LEDGER_SOURCE,))}
        for hid, h in sorted(hyps.items()):
            sset = f"hypothesis:{nid}:{hid}"
            if sset in have:
                continue
            if str(cutoff)[:10] >= str(h["baseline_date"]):
                out["held"][hid] = (f"window opened {h['baseline_date']}; not "
                                    f"emitted at {str(cutoff)[:10]} -- ex ante "
                                    f"or not at all")
                continue
            table_rows = store.as_of(str((h.get("prior") or {}).get("table")),
                                     as_of=cutoff)
            table = json.loads(table_rows[-1]["value_text"]) if table_rows else None
            pr = hypothesis_prior(h.get("prior") or {}, table)
            if pr.get("probability") is None:
                out["held"][hid] = pr["reason"]
                continue
            criterion = {"kind": HYPOTHESIS_KIND, "narrative_id": nid,
                         "hypothesis": hid, "claim": " ".join(
                             str(h["claim"]).split()),
                         "metrics": [h["metric"]], "comparison": h["comparison"],
                         "quorum": 1, "baseline_date": str(h["baseline_date"]),
                         "horizon_date": str(h["horizon_date"]),
                         "baseline": {}, "grace_days": RESOLUTION_GRACE_DAYS,
                         "prior": pr,
                         "statement_cited": h.get("statement_cited"),
                         "claims_cited": list(h.get("claims_cited") or [])}
            pid = led.record(
                source=LEDGER_SOURCE, claim=f"[{nid}:{hid}] {criterion['claim']}",
                probability=pr["probability"],
                horizon_date=criterion["horizon_date"],
                resolution_criterion=json.dumps(criterion, sort_keys=True),
                scenario_set=sset, emitted_at=cutoff, emitted_by=run_id)
            out["emitted"].append({"hypothesis": hid, "probability_id": pid,
                                   "probability": pr["probability"]})
            log.info("hypothesis %s:%s entered at %.4f", nid, hid,
                     pr["probability"])
    return out


def _meets(comparison: str, base: float, now: float) -> bool:
    if comparison == "up":
        return now > base
    if comparison == "down":
        return now < base
    if comparison == "magnitude_up":
        return abs(now) > abs(base)
    if comparison == "magnitude_down":
        return abs(now) < abs(base)
    raise ValueError(f"unknown comparison {comparison!r}")


def resolve_one(criterion: dict, store: Any, as_of: str) -> dict:
    """(outcome or None, detail). None means: not resolvable yet."""
    import datetime as dt  # noqa: PLC0415
    horizon = criterion["horizon_date"]
    today = str(as_of)[:10]
    if today < horizon:
        return {"outcome": None, "reason": "horizon not reached"}
    grace_end = (dt.date.fromisoformat(horizon)
                 + dt.timedelta(days=int(criterion.get("grace_days") or 0))
                 ).isoformat()
    met, detail, missing = 0, {}, []
    for m in criterion.get("metrics") or []:
        if criterion.get("baseline_date"):
            base = close_on_or_before(store, m, criterion["baseline_date"], as_of)
        else:
            base = (criterion.get("baseline") or {}).get(m)
        if not base:
            missing.append(m)
            detail[m] = ("no close on or before the baseline date"
                         if criterion.get("baseline_date") else
                         "no baseline at emission")
            continue
        rows = [r for r in store.as_of(m, as_of=as_of)
                if base["observed_at"] < str(r["observed_at"])[:10] <= horizon
                and r.get("value_num") is not None]
        if criterion.get("baseline_date"):
            # The dated form reads the close ON OR BEFORE the horizon, the same
            # rule tools/base_rates.py used to compute the prior; not "the last
            # print after the baseline", which a late-arriving row could move.
            rows = rows[-1:]
            if (rows and today < grace_end
                    and not _complete_through(store, m, horizon, as_of)):
                return {"outcome": None, "reason": f"{m} has no print after "
                        f"{horizon} yet, so the close on it is not final",
                        "detail": detail}
        if not rows:
            missing.append(m)
            detail[m] = "no observation after the baseline by the horizon"
            continue
        now = float(rows[-1]["value_num"])
        ok = _meets(criterion["comparison"], base["value"], now)
        met += int(ok)
        detail[m] = {"baseline": base, "at_horizon": {
            "observed_at": str(rows[-1]["observed_at"])[:10], "value": now},
            "met": ok}
    if missing and today < grace_end:
        return {"outcome": None, "reason": f"waiting on {missing} until "
                                           f"{grace_end}", "detail": detail}
    quorum = int(criterion.get("quorum") or 1)
    return {"outcome": int(met >= quorum), "met": met, "quorum": quorum,
            "missing_counted_unmet": missing, "detail": detail}


def resolve_due(as_of: Optional[str] = None, db_path: Optional[str] = None
                ) -> dict:
    """Resolve every narrative forecast whose horizon has passed. Idempotent."""
    from . import probability_ledger  # noqa: PLC0415
    cutoff = observations.canonical_instant(
        as_of or session.utc_iso(timespec="microseconds"))
    out = {"resolved": [], "waiting": []}
    store = observations.ObservationStore(db_path)
    try:
        with probability_ledger.ProbabilityLedger(db_path) as led:
            for r in led.due(cutoff):
                if r["source"] != LEDGER_SOURCE:
                    continue
                crit = json.loads(r["resolution_criterion"])
                res = resolve_one(crit, store, cutoff)
                if res["outcome"] is None:
                    out["waiting"].append({"probability_id": r["probability_id"],
                                           "reason": res["reason"]})
                    continue
                done = led.resolve(r["probability_id"], res["outcome"],
                                   note=json.dumps(res, sort_keys=True,
                                                   default=str)[:2000],
                                   resolved_at=cutoff)
                out["resolved"].append(done)
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
    sub.add_parser("resolve", help="resolve narrative forecasts past horizon")
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
        for nid, h in (r.get("hypotheses") or {}).items():
            for e in h["emitted"]:
                print(f"  HYPOTHESIS  : {nid}:{e['hypothesis']} entered at "
                      f"{e['probability']:.4f} ({e['probability_id'][:12]})")
            for hid, why in h["held"].items():
                print(f"  held        : {nid}:{hid} -- {why}")
        return 0
    if a.cmd == "replay":
        r = replay(a.db)
        print(f"replayed {r['compared']}: {r['matched']} exact, "
              f"{len(r['mismatches'])} mismatched, {r['other_version']} under "
              f"another rules version")
        for m in r["mismatches"][:20]:
            print(f"  MISMATCH {m['narrative_id']} {m['session']}: {m['fields']}")
        return 1 if r["mismatches"] else 0
    if a.cmd == "resolve":
        r = resolve_due(db_path=a.db)
        print(f"resolved {len(r['resolved'])}, waiting {len(r['waiting'])}")
        for x in r["resolved"]:
            print(f"  {x['probability_id'][:12]} p={x['probability']:.2f} "
                  f"outcome={x['outcome']} brier={x['brier']:.4f}")
        for x in r["waiting"]:
            print(f"  waiting {x['probability_id'][:12]}: {x['reason']}")
        return 0
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
