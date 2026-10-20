"""
The hypothesis register (X-2.5; change order section 10).

Every idea the lab tests enters here first, BEFORE any backtest of it runs, and
stays here whatever happens to it. The register is alpha.db's `hypotheses` table
(with `hypothesis_batches` for the files they came in); a row is never deleted
and the idea it records -- title, mechanism, rule, family, source, channel and the
pre-registration instant -- is never rewritten (alpha/ledger.py's triggers). Its
status, result and links move:

  registered    in the grammar, ready for the harness
  needs_code    a rule in text only: queued for the research sitting, with why
  data_gap      an instrument or series the store cannot serve point-in-time
  screened_out  a duplicate of a registered idea, or over a budget -- with why
  testing       the harness has it
  passed        through X-1.6 (and, for a model idea, the model-idea rule)
  failed        did not pass: kept with its metrics, so it is not re-tried
                under a new name
  refined       superseded by a new pre-registered variant (`superseded_by`),
                counted against it
  promoted      written to `engines` at min_size (X-2.6)
  retired       an engine retired by the kill rule or by ruling

THE BATCH SCHEMA is the fixture file's, `alpha-lab-hypotheses/v1`
(tests/fixtures/alpha/inbox/hypotheses-2026-10-14.yaml): the batch fields
(schema, batch_id, source, proposer, channel, written_at, model_idea_rule,
inputs) and, per hypothesis, local_id, title, horizon_class, horizon_sessions,
family, mechanism, universe, rule_text, conditioning, expected, sample, data,
needs_code, rule_dsl, kill, state_at_registration. validate_batch() is the
schema check every channel's file passes through.

PRE-REGISTRATION IS AN INSTANT, AND IT IS NOT THE AUTHOR'S CLAIM. For a file
from Drive it is the file's Drive created time (the manifest, X-2.11); for a
file the daily proposer writes on the box, the manifest line it writes beside
it; for the workbench, the instant `new` registers it. The harness refuses to
run a hypothesis whose pre_registered_at is later than the run
(refuse_if_unregistered): a hypothesis written after its backtest is a variant,
not an idea.

EVERY HYPOTHESIS COUNTS (10.2 c). Registering one adds one to its family's
variant count, whatever becomes of it -- a screened-out duplicate is still a
trial the search made. Its first harness run is deflated by that count and does
not add again; each later run (a refit, a variant) does.
"""

from __future__ import annotations

import datetime as dt
import difflib
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable, Optional

import yaml

from . import blocklist

SCHEMA_ID = "alpha-lab-hypotheses/v1"
SOURCES = ("model", "operator", "chat", "sitting", "systematic", "tell")
FILE_SOURCES = ("model", "operator", "chat")
CHANNELS = ("daily-proposer", "weekly-brief", "workbench", "chat", "sitting",
            "importer", "search")
# X-3.6: the reports' tells enter through the importer (alpha/tells.py) only,
# as source `tell`; no file from Drive or the proposer may claim that source.
IMPORTER_SOURCES = ("tell",)
# X-3.5: the grammar search's survivors enter through alpha/search.py only, as
# source `systematic`, pre-registered by the search's own manifest.
SEARCH_SOURCES = ("systematic",)
HORIZON_CLASSES = ("short", "medium", "long")
STATUSES = ("registered", "needs_code", "data_gap", "screened_out", "testing",
            "passed", "failed", "refined", "promoted", "retired")
# Terminal for the harness: nothing re-runs these without a new variant.
CLOSED = ("screened_out", "failed", "refined", "retired")

BATCH_REQUIRED = ("schema", "batch_id", "source", "proposer", "channel",
                  "written_at", "model_idea_rule", "inputs", "hypotheses")
BATCH_OPTIONAL = ("human_record", "prompt_version", "model_id", "packet_sha256",
                  "notes")
HYP_REQUIRED = ("local_id", "title", "horizon_class", "horizon_sessions", "family",
                "mechanism", "universe", "rule_text", "conditioning", "expected",
                "sample", "data", "needs_code", "kill", "state_at_registration")
HYP_OPTIONAL = ("rule_dsl", "supersedes", "translation_note", "engine", "tell")

# THE BUDGETS (10.2 c), per channel. The daily proposer's weekly family budget
# is a register-wide count (family_week_count), checked by the proposer before
# it writes and by the ingestion again.
BUDGETS = {
    "weekly-brief": {"short": 5, "medium": 5, "per_family_per_batch": 2},
    "daily-proposer": {"per_batch": 3, "per_family_per_week": 2},
    "sitting": {"per_batch": 5},
}

TICKER = re.compile(r"^[A-Z][A-Z0-9.\-=^]{0,11}$")
TITLE_SIMILAR = 0.85
REPO = Path(__file__).resolve().parent.parent
TRANSLATIONS = REPO / "alpha" / "research" / "translations"


class PreRegistrationViolation(ValueError):
    """The harness was asked to run a hypothesis registered after the run."""


# ---------------------------------------------------------------------------
# Instants
# ---------------------------------------------------------------------------
def instant(v: Any) -> Optional[str]:
    """An ISO instant with a zone, in UTC; None if it is not one. A naive time
    is refused: a pre-registration instant without a zone is no instant."""
    if v is None:
        return None
    if isinstance(v, dt.datetime):
        d = v
    else:
        try:
            d = dt.datetime.fromisoformat(str(v).strip().replace("Z", "+00:00"))
        except ValueError:
            return None
    if d.tzinfo is None:
        return None
    return d.astimezone(dt.timezone.utc).isoformat(timespec="microseconds")


# ---------------------------------------------------------------------------
# The schema
# ---------------------------------------------------------------------------
def load_batch(text: str) -> Any:
    return yaml.safe_load(text)


def validate_batch(doc: Any) -> list[str]:
    """Every way a batch fails the v1 schema, as messages; [] is valid."""
    if not isinstance(doc, dict):
        return ["the file is not a YAML mapping"]
    err: list[str] = []
    for k in BATCH_REQUIRED:
        if k not in doc:
            err.append(f"missing batch field {k}")
    for k in doc:
        if k not in BATCH_REQUIRED + BATCH_OPTIONAL:
            err.append(f"unknown batch field {k}")
    if doc.get("schema") != SCHEMA_ID:
        err.append(f"schema is {doc.get('schema')!r}, not {SCHEMA_ID}")
    if not isinstance(doc.get("batch_id"), str) or not doc.get("batch_id"):
        err.append("batch_id is not a non-empty string")
    if doc.get("channel") == "importer":
        if doc.get("source") not in IMPORTER_SOURCES:
            err.append(f"the importer's source is one of {IMPORTER_SOURCES}, not "
                       f"{doc.get('source')!r}")
    elif doc.get("channel") == "search":
        if doc.get("source") not in SEARCH_SOURCES:
            err.append(f"the search's source is one of {SEARCH_SOURCES}, not "
                       f"{doc.get('source')!r}")
    elif doc.get("source") not in FILE_SOURCES:
        err.append(f"source {doc.get('source')!r} is not one of {FILE_SOURCES}")
    if doc.get("channel") not in CHANNELS:
        err.append(f"channel {doc.get('channel')!r} is not one of {CHANNELS}")
    if instant(doc.get("written_at")) is None:
        err.append("written_at is not an ISO instant with a zone")
    if not isinstance(doc.get("model_idea_rule"), bool):
        err.append("model_idea_rule is not true or false")
    elif doc.get("source") == "model" and not doc["model_idea_rule"]:
        err.append("a model batch carries model_idea_rule: true (10.2 b)")
    if not isinstance(doc.get("inputs"), list):
        err.append("inputs is not a list")
    hyps = doc.get("hypotheses")
    if not isinstance(hyps, list) or not hyps:
        err.append("hypotheses is not a non-empty list")
        return err
    seen = set()
    for i, h in enumerate(hyps):
        tag = f"hypotheses[{i}]"
        if not isinstance(h, dict):
            err.append(f"{tag} is not a mapping")
            continue
        tag = f"{tag} ({h.get('local_id')})"
        for k in HYP_REQUIRED:
            if k not in h:
                err.append(f"{tag}: missing {k}")
        for k in h:
            if k not in HYP_REQUIRED + HYP_OPTIONAL:
                err.append(f"{tag}: unknown field {k}")
        lid = h.get("local_id")
        if not isinstance(lid, str) or not lid:
            err.append(f"{tag}: local_id is not a string")
        elif lid in seen:
            err.append(f"{tag}: local_id repeated in the batch")
        seen.add(lid)
        for k in ("title", "family", "mechanism", "rule_text"):
            if k in h and (not isinstance(h[k], str) or not h[k].strip()):
                err.append(f"{tag}: {k} is not a non-empty string")
        if h.get("horizon_class") not in HORIZON_CLASSES:
            err.append(f"{tag}: horizon_class {h.get('horizon_class')!r} is not one "
                       f"of {HORIZON_CLASSES}")
        hs = h.get("horizon_sessions")
        if not isinstance(hs, int) or isinstance(hs, bool) or hs < 1:
            err.append(f"{tag}: horizon_sessions is not a positive integer")
        if "universe" in h and not isinstance(h["universe"], (list, str)):
            err.append(f"{tag}: universe is not a list or a description")
        if "conditioning" in h and not isinstance(h["conditioning"], list):
            err.append(f"{tag}: conditioning is not a list")
        for c in h.get("conditioning") or []:
            if not isinstance(c, dict) or not c.get("name"):
                err.append(f"{tag}: a conditioning entry has no name")
        for k in ("sample", "data"):
            if k in h and not isinstance(h[k], dict):
                err.append(f"{tag}: {k} is not a mapping")
        if "needs_code" in h and not isinstance(h["needs_code"], bool):
            err.append(f"{tag}: needs_code is not true or false")
        if h.get("rule_dsl") is not None and not isinstance(h["rule_dsl"], dict):
            err.append(f"{tag}: rule_dsl is not a mapping")
        if "tell" in h:
            t = h["tell"]
            if doc.get("channel") != "importer":
                err.append(f"{tag}: only the importer's hypotheses carry `tell`")
            elif not isinstance(t, dict) or not all(t.get(k) for k in (
                    "kind", "id", "hash", "cited")):
                err.append(f"{tag}: tell carries kind, id, hash and cited")
    return err


def budget_errors(doc: dict) -> list[tuple[Optional[str], str]]:
    """Over-budget hypotheses as (local_id, why); (None, why) refuses the batch.
    The weekly brief: at most 5 short and 5 medium, at most 2 per family per
    batch. The daily proposer: at most 3 a batch (its weekly family budget is
    the register's, family_week_count)."""
    ch = doc.get("channel")
    hyps = [h for h in doc.get("hypotheses") or [] if isinstance(h, dict)]
    out: list[tuple[Optional[str], str]] = []
    if ch == "weekly-brief":
        b = BUDGETS[ch]
        by_class: dict[str, int] = {}
        by_fam: dict[str, int] = {}
        for h in hyps:
            c = h.get("horizon_class")
            by_class[c] = by_class.get(c, 0) + 1
            if c in ("short", "medium") and by_class[c] > b[c]:
                out.append((h.get("local_id"), f"over the weekly brief's {b[c]} "
                            f"{c}-term hypotheses a batch"))
                continue
            f = h.get("family")
            by_fam[f] = by_fam.get(f, 0) + 1
            if by_fam[f] > b["per_family_per_batch"]:
                out.append((h.get("local_id"), f"over {b['per_family_per_batch']} "
                            f"of family {f} in one batch"))
    elif ch in ("daily-proposer", "sitting"):
        if len(hyps) > BUDGETS[ch]["per_batch"]:
            out.append((None, f"{len(hyps)} hypotheses: over the {ch}'s "
                        f"{BUDGETS[ch]['per_batch']} a batch"))
    return out


# ---------------------------------------------------------------------------
# Identity: the rule hash and the title, for duplicates
# ---------------------------------------------------------------------------
def _canon(v: Any) -> Any:
    if isinstance(v, dict):
        return {str(k): _canon(x) for k, x in sorted(v.items())
                if k not in ("name", "note", "notes", "why", "label")}
    if isinstance(v, list):
        return [_canon(x) for x in v]
    if isinstance(v, str):
        return v.strip().upper() if TICKER.match(v.strip().upper()) else v.strip().lower()
    return v


def normalise_text(s: str) -> str:
    s = re.sub(r"[^a-z0-9.%+\-<>= ]+", " ", str(s or "").lower())
    return re.sub(r"\s+", " ", s).strip()


def rule_hash(h: dict) -> str:
    """The normalised rule's sha256: the grammar's form where it has one (names
    and notes dropped, keys sorted, tickers upper-cased), else the rule text with
    case, punctuation and spacing normalised. Two batches proposing the same rule
    in different words of grammar hash the same."""
    dsl = h.get("rule_dsl")
    if isinstance(dsl, dict) and dsl:
        body = "dsl:" + json.dumps(_canon(dsl), sort_keys=True, default=str)
    else:
        body = "text:" + normalise_text(h.get("rule_text") or "")
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def title_similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, normalise_text(a), normalise_text(b)).ratio()


def tickers(h: dict) -> list[str]:
    """The instruments a hypothesis names: its universe where it is a list of
    tickers, and its rule's instruments where it has a rule in the grammar."""
    out: list[str] = []
    uni = h.get("universe")
    if isinstance(uni, list):
        out += [str(x).strip().upper() for x in uni if TICKER.match(str(x).strip().upper())]
    dsl = h.get("rule_dsl")
    if isinstance(dsl, dict):
        from . import rules                                     # noqa: PLC0415
        out += rules.instruments(dsl)
    seen, uniq = set(), []
    for t in out:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    return uniq


def blocked(h: dict) -> list[str]:
    """Each Brookfield-complex instrument the hypothesis names, by the system's
    own rule; a blocked instrument never reaches the register."""
    out = []
    for t in tickers(h):
        if blocklist.check(t) is not None:
            out.append(t)
    for t in (h.get("title"), h.get("rule_text")):
        for w in re.findall(r"\b[A-Z]{1,5}(?:\.[A-Z])?\b", str(t or "")):
            if blocklist.check(w) is not None and w not in out:
                out.append(w)
    return out


# ---------------------------------------------------------------------------
# Translations: a text rule put into the grammar after registration, before test
# ---------------------------------------------------------------------------
def translation_for(batch_id: str, local_id: str, file_sha256: Optional[str],
                    root: Optional[Path] = None) -> Optional[dict]:
    """A committed translation of a batch's text rule into the grammar, bound
    to the exact file by its sha256: alpha/research/translations/<batch_id>/
    <local_id>.yaml. It carries the rule and a note of every substitution it
    made -- or, for a rule the grammar cannot express, `needs_code_reason`. It
    never changes the pre-registration instant, and a translation for a
    different file's bytes is not applied."""
    p = Path(root or TRANSLATIONS) / batch_id / f"{local_id}.yaml"
    if not p.is_file():
        return None
    doc = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    if doc.get("batch_sha256") and file_sha256 and \
            str(doc["batch_sha256"]).lower() != str(file_sha256).lower():
        return None
    if doc.get("local_id") != local_id:
        return None
    if not isinstance(doc.get("rule_dsl"), dict) and not doc.get("needs_code_reason"):
        return None
    return doc


# ---------------------------------------------------------------------------
# The register
# ---------------------------------------------------------------------------
def _j(v: Any) -> Optional[str]:
    return None if v is None else json.dumps(v, sort_keys=True, default=str)


def _expected_sign(exp: Any) -> Optional[int]:
    s = json.dumps(exp, default=str).lower()
    if "negative" in s or "underperform" in s or "falls" in s:
        return -1
    if "positive" in s:
        return 1
    return None


class Register:
    """The register over one Ledger (alpha.db)."""

    def __init__(self, ledger) -> None:
        self.lg = ledger

    # -- reads ----------------------------------------------------------------
    def get(self, hid: str) -> Optional[dict]:
        r = self.lg.one("SELECT * FROM hypotheses WHERE id=?", (hid,))
        return self._decode(r) if r else None

    def by_local(self, batch_id: str, local_id: str) -> Optional[dict]:
        r = self.lg.one("SELECT * FROM hypotheses WHERE batch_id=? AND local_id=?",
                        (batch_id, local_id))
        return self._decode(r) if r else None

    def all(self, statuses: Optional[Iterable[str]] = None) -> list[dict]:
        rows = [self._decode(r) for r in self.lg.q("SELECT * FROM hypotheses ORDER BY id")]
        if statuses is not None:
            want = set(statuses)
            rows = [r for r in rows if r["status"] in want]
        return rows

    def batch(self, batch_id: str) -> Optional[dict]:
        return self.lg.one("SELECT * FROM hypothesis_batches WHERE batch_id=?",
                           (batch_id,))

    @staticmethod
    def _decode(r: dict) -> dict:
        r = dict(r)
        for k in ("universe", "instruments", "rule_dsl", "conditioning", "expected",
                  "sample", "data", "kill_rule", "spec", "result"):
            if r.get(k):
                try:
                    r[k] = json.loads(r[k])
                except ValueError:
                    pass
        r["needs_code"] = bool(r.get("needs_code"))
        r["model_idea_rule"] = bool(r.get("model_idea_rule"))
        return r

    def next_id(self) -> str:
        r = self.lg.one("SELECT id FROM hypotheses ORDER BY id DESC LIMIT 1")
        n = int(r["id"].split("-")[1]) + 1 if r else 1
        return f"HYP-{n:04d}"

    def duplicate_of(self, h: dict) -> Optional[tuple[str, str]]:
        """(register id, why) when the whole register -- failures included --
        already holds this rule (its normalised hash) or this title (similarity
        at or above TITLE_SIMILAR)."""
        rh = rule_hash(h)
        for r in self.lg.q("SELECT id, title, rule_hash, status FROM hypotheses ORDER BY id"):
            if r["rule_hash"] == rh:
                return r["id"], f"the same rule as {r['id']} ({r['status']})"
            sim = title_similarity(h.get("title") or "", r["title"])
            if sim >= TITLE_SIMILAR:
                return r["id"], (f"the title matches {r['id']} ({r['status']}) at "
                                 f"{sim:.2f}")
        return None

    def family_week_count(self, family: str, day: str, channel: Optional[str] = None) -> int:
        """Hypotheses of `family` registered in the ISO week of `day`."""
        d = dt.date.fromisoformat(day[:10])
        mon = (d - dt.timedelta(days=d.weekday())).isoformat()
        sun = (d + dt.timedelta(days=6 - d.weekday())).isoformat()
        sql = ("SELECT COUNT(*) AS n FROM hypotheses WHERE family=? AND "
               "substr(pre_registered_at,1,10) BETWEEN ? AND ?")
        args: list = [family, mon, sun]
        if channel:
            sql += " AND channel=?"
            args.append(channel)
        return int(self.lg.one(sql, args)["n"])

    # -- writes ---------------------------------------------------------------
    def record_batch(self, doc: dict, pre_registered_at: str, as_of: str,
                     file_name: Optional[str] = None, file_sha256: Optional[str] = None,
                     created_time: Optional[str] = None,
                     modified_time: Optional[str] = None) -> None:
        self.lg._insert("hypothesis_batches", {
            "batch_id": doc["batch_id"], "schema": doc["schema"],
            "file_name": file_name, "file_sha256": file_sha256,
            "source": doc["source"], "channel": doc["channel"],
            "proposer": doc.get("proposer"),
            "batch_written_at": instant(doc.get("written_at")),
            "created_time": created_time, "modified_time": modified_time,
            "pre_registered_at": pre_registered_at,
            "model_idea_rule": int(bool(doc.get("model_idea_rule"))),
            "inputs": _j(doc.get("inputs")),
            "prompt_version": doc.get("prompt_version"), "model_id": doc.get("model_id"),
            "packet_sha256": doc.get("packet_sha256"),
            "n_hypotheses": len(doc.get("hypotheses") or []), "as_of": as_of})

    def register(self, h: dict, batch: dict, pre_registered_at: str, as_of: str,
                 status: str, reason: Optional[str] = None,
                 rule_dsl: Optional[dict] = None, rule_origin: Optional[str] = None,
                 bump: bool = True) -> str:
        """Write one hypothesis. Counts it in its family's variants (10.2 c)."""
        if status not in STATUSES:
            raise ValueError(f"status {status!r}")
        for t in blocked(h):
            raise blocklist.BlockedInstrument(
                f"{h.get('local_id')}: restricted instrument {t} -- never registered")
        dsl = rule_dsl if rule_dsl is not None else h.get("rule_dsl")
        spec = dict(h)
        hid = self.next_id()
        sample = h.get("sample") if isinstance(h.get("sample"), dict) else {}
        exp = h.get("expected")
        self.lg._insert("hypotheses", {
            "id": hid, "batch_id": batch["batch_id"], "local_id": h["local_id"],
            "title": h["title"], "family": h["family"],
            "horizon_class": h.get("horizon_class"),
            "horizon_sessions": h.get("horizon_sessions"),
            "horizon": f"{h.get('horizon_class')}:{h.get('horizon_sessions')}",
            "mechanism": " ".join(str(h["mechanism"]).split()),
            "universe": _j(h.get("universe")), "instruments": _j(tickers({**h, "rule_dsl": dsl})),
            "rule_text": " ".join(str(h["rule_text"]).split()),
            "rule_dsl": _j(dsl), "rule_origin": rule_origin or ("batch" if dsl else None),
            "rule_hash": rule_hash({**h, "rule_dsl": dsl}),
            "conditioning": _j(h.get("conditioning")), "expected": _j(exp),
            "expected_sign": _expected_sign(exp), "expected_size": None,
            "sample": _j(sample), "sample_needed": sample.get("min_independent_signals"),
            "data": _j(h.get("data")), "needs_code": int(bool(h.get("needs_code"))),
            "kill_rule": _j(h.get("kill")),
            "state_at_registration": " ".join(str(h.get("state_at_registration") or "").split()),
            "spec": _j(spec), "source": batch["source"], "channel": batch["channel"],
            "proposer": batch.get("proposer"),
            "model_idea_rule": int(bool(batch.get("model_idea_rule"))),
            "pre_registered_at": pre_registered_at, "status": status,
            "status_reason": reason, "result": None,
            "supersedes": h.get("supersedes"), "superseded_by": None,
            "engine_id": None, "as_of": as_of})
        if bump:
            n = self.lg.bump_variant(h["family"], as_of)
        else:
            n = self.lg.variant_count(h["family"])
        self.lg.event("register", "hypothesis_registered", as_of, None,
                      after={"id": hid, "batch_id": batch["batch_id"],
                             "local_id": h["local_id"], "family": h["family"],
                             "status": status, "reason": reason,
                             "pre_registered_at": pre_registered_at,
                             "variant_count": n, "rule_origin": rule_origin})
        sup = h.get("supersedes")
        if sup and self.get(sup):
            why = (f"superseded by {hid}: the tell changed" if batch["source"] == "tell"
                   else f"refined into {hid}")
            self.set_status(sup, "refined", as_of, why, superseded_by=hid)
        return hid

    def set_status(self, hid: str, status: str, as_of: str,
                   reason: Optional[str] = None, result: Any = None,
                   superseded_by: Optional[str] = None,
                   engine_id: Optional[str] = None, source: str = "loop") -> None:
        if status not in STATUSES:
            raise ValueError(f"status {status!r}")
        before = self.get(hid)
        if before is None:
            raise KeyError(hid)
        fields = {"status": status, "status_reason": reason}
        if result is not None:
            fields["result"] = _j(result)
        if superseded_by is not None:
            fields["superseded_by"] = superseded_by
        if engine_id is not None:
            fields["engine_id"] = engine_id
        sets = ", ".join(f"{k}=:{k}" for k in fields)
        from .ledger import utc_now                               # noqa: PLC0415
        self.lg.conn.execute(f"UPDATE hypotheses SET {sets}, as_of=:as_of, "
                             f"written_at=:w WHERE id=:id",
                             {**fields, "as_of": as_of, "w": utc_now(), "id": hid})
        self.lg.conn.commit()
        self.lg.event("register", "hypothesis_status", as_of, engine_id,
                      before={"id": hid, "status": before["status"]},
                      after={"id": hid, "status": status, "reason": reason},
                      source=source)


def refuse_if_unregistered(hyp: Optional[dict], run_as_of: str) -> None:
    """The harness's guard (X-2.5): no run on a hypothesis that is not in the
    register, or whose pre_registered_at is later than the run."""
    if not hyp:
        raise PreRegistrationViolation("no such hypothesis in the register: a rule "
                                       "is registered before it is run")
    pre = instant(hyp.get("pre_registered_at"))
    run = instant(run_as_of)
    if pre is None or run is None:
        raise PreRegistrationViolation(f"{hyp.get('id')}: an instant is unreadable "
                                       f"(pre_registered_at {hyp.get('pre_registered_at')!r}, "
                                       f"run {run_as_of!r})")
    if pre > run:
        raise PreRegistrationViolation(
            f"{hyp.get('id')}: pre-registered at {pre}, after the run at {run} -- a "
            f"hypothesis written after its backtest is a variant, not an idea")
    if hyp.get("status") in CLOSED:
        raise PreRegistrationViolation(
            f"{hyp.get('id')} is {hyp['status']}: closed ideas are not re-run; "
            f"a change is a new, pre-registered variant")
