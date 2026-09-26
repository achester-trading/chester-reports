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
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
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
