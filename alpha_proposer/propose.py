"""
The daily proposer (X-2.10b; change order 10.2 a and c).

On the box, after the nightly loop (chester-alpha-proposer.timer, 18:10 ET on
session days): ONE model call over a code-built observation packet, at most
three hypotheses, written as one batch file into the lab's inbox for the next
nightly loop to ingest. In order:

  1. ONCE A SESSION DAY. If the proposer's manifest already holds a line for
     today's session, nothing is done.
  2. THE PACKET, by code (alpha_proposer/packet.py), from the store and
     alpha.db, both opened read-only.
  3. ONE MODEL CALL, through the client the reports use
     (daily_cascade.narrative._client) at the model id from the same config
     (daily_cascade.narrative.DEFAULT_MODEL), the prompt
     config/alpha_proposer_prompt.md at its recorded version. Thinking off.
  4. THE CODE'S CHECKS, each proposal on its own, before anything is written:
     the v1 schema; the blocklist; the store's instruments; the rule compiled
     against the store (a rule the grammar refuses is kept as text, needs_code);
     duplicates against the WHOLE register, failures included (the normalised
     rule hash, or a title at 0.85 similarity) and against each other; the
     budgets -- three a session day, two a family a week.
  5. THE BATCH: proposals-YYYY-MM-DD.yaml in alpha-lab-hypotheses/v1, channel
     daily-proposer, source model, model_idea_rule true, carrying the prompt
     version, the model id and the packet's sha256; then its manifest line
     (name, sha256, written_at) -- the ingestion's proof of the bytes and of
     the instant.

IT NEVER SEES A TEST RESULT: the packet carries the register's titles, statuses
and rule hashes, never a result, and this package imports no harness, no
workbench and no backtest. It imports no order gate and no broker module, and
writes nowhere but the inbox and its own log (alpha_proposer/out.py;
tools/validate_alpha_proposer.py).
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Optional

import yaml

from altdata import session
from alpha import hypotheses as hyp
from alpha import intake, rules

from . import out, packet

REPO = Path(__file__).resolve().parent.parent
PROMPT_PATH = REPO / "config" / "alpha_proposer_prompt.md"
RULES_DOC = REPO / "docs" / "alpha-lab-rules.md"
MAX_TOKENS = 6000
CHANNEL = "daily-proposer"


def prompt_version(path: Optional[Path] = None) -> str:
    first = Path(path or PROMPT_PATH).read_text(encoding="utf-8").splitlines()[0]
    m = re.search(r"prompt_version:\s*([\w.\-]+)", first)
    if not m:
        raise ValueError("the proposer's prompt carries no prompt_version on its first line")
    return m.group(1)


def build_prompt(pkt: dict, path: Optional[Path] = None) -> tuple[str, str]:
    text = Path(path or PROMPT_PATH).read_text(encoding="utf-8")
    text = re.sub(r"^<!--.*?-->\s*", "", text, flags=re.S)       # the version line
    text = re.sub(r"^<!--.*?-->\s*", "", text, flags=re.S)       # the header comment
    system, _, user = text.partition("\nUSER\n")
    system = system.replace("SYSTEM\n", "", 1).replace(
        "{{RULES}}", RULES_DOC.read_text(encoding="utf-8"))
    user = user.replace("{{PACKET}}", json.dumps(pkt, indent=1, default=str))
    return system.strip(), user.strip()


def model_id() -> str:
    from daily_cascade import narrative                         # noqa: PLC0415
    return narrative.DEFAULT_MODEL


def client():
    from daily_cascade import narrative                         # noqa: PLC0415
    return narrative._client()


def call(cl, model: str, system: str, user: str) -> tuple[str, str]:
    """(text, the model id the reply records)."""
    kwargs: dict = {"model": model, "max_tokens": MAX_TOKENS, "system": system,
                    "messages": [{"role": "user", "content": user}],
                    "thinking": {"type": "disabled"}}
    try:
        resp = cl.messages.create(**kwargs)
    except TypeError:
        kwargs.pop("thinking")
        resp = cl.messages.create(**kwargs)
    text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
    return text.strip(), (getattr(resp, "model", None) or model)


def parse(text: str) -> list[dict]:
    m = re.search(r"```(?:yaml|yml)?\s*\n(.*?)```", text, re.S)
    body = m.group(1) if m else text
    doc = yaml.safe_load(body) or {}
    hs = doc.get("hypotheses") if isinstance(doc, dict) else doc
    return [h for h in hs or [] if isinstance(h, dict)]


def _normalise(h: dict, i: int) -> dict:
    h = dict(h)
    h["local_id"] = f"P-{i}"
    h.setdefault("conditioning", [])
    h.setdefault("kill", "constitution")
    h.setdefault("data", {})
    h.setdefault("sample", {"min_independent_signals": 40})
    if not isinstance(h.get("rule_dsl"), dict):
        h.pop("rule_dsl", None)
    h["needs_code"] = "rule_dsl" not in h
    return h


def check(props: list[dict], store, ledger, day: str) -> tuple[list[dict], list[dict]]:
    """The code's checks. (accepted, rejected-with-reasons); never raises."""
    reg = hyp.Register(ledger) if ledger is not None else None
    budget = hyp.BUDGETS[CHANNEL]
    accepted: list[dict] = []
    rejected: list[dict] = []
    fam_used: dict[str, int] = {}
    for i, raw in enumerate(props, start=1):
        h = _normalise(raw, i)
        why = None
        probe = {"schema": hyp.SCHEMA_ID, "batch_id": "probe", "source": "model",
                 "proposer": "probe", "channel": CHANNEL,
                 "written_at": "2026-01-01T00:00:00+00:00", "model_idea_rule": True,
                 "inputs": [], "hypotheses": [h]}
        errs = hyp.validate_batch(probe)
        if errs:
            why = "schema: " + "; ".join(errs[:4])
        elif hyp.blocked(h):
            why = f"blocked instrument(s) {hyp.blocked(h)}: never written"
        if why is None:
            gaps = intake.instrument_gaps(h, store)
            if gaps:
                why = "not in the store: " + "; ".join(gaps)
        if why is None and "rule_dsl" in h:
            try:
                # the proposer stays on grammar v1 (alpha-lab-4): a v2 rule is text
                if h["rule_dsl"].get("grammar") != rules.GRAMMAR:
                    raise rules.RuleError([f"the proposer writes {rules.GRAMMAR} only"])
                rules.compile_rule(h["rule_dsl"], store)
            except rules.RuleError as exc:
                h["translation_note"] = ("the proposer's rule_dsl did not compile ("
                                         + "; ".join(exc.errors[:4]) + "); kept as text")
                h.pop("rule_dsl")
                h["needs_code"] = True
        if why is None:
            dup = reg.duplicate_of(h) if reg else None
            if dup:
                why = f"duplicate: {dup[1]}"
            else:
                for a in accepted:
                    if hyp.rule_hash(a) == hyp.rule_hash(h) or \
                            hyp.title_similarity(a["title"], h["title"]) >= hyp.TITLE_SIMILAR:
                        why = f"duplicate of this batch's {a['local_id']}"
                        break
        if why is None and len(accepted) >= budget["per_batch"]:
            why = f"over the {budget['per_batch']} a session day"
        if why is None:
            f = h["family"]
            used = (reg.family_week_count(f, day, channel=CHANNEL) if reg else 0) \
                + fam_used.get(f, 0)
            if used >= budget["per_family_per_week"]:
                why = f"over {budget['per_family_per_week']} of family {f} this week"
        if why:
            rejected.append({"local_id": h["local_id"], "title": h.get("title"),
                             "why": why})
            continue
        fam_used[h["family"]] = fam_used.get(h["family"], 0) + 1
        accepted.append(h)
    for k, h in enumerate(accepted, start=1):
        h["local_id"] = f"P-{k}"
    return accepted, rejected


def already_today(day: str, inbox: Optional[Path] = None) -> bool:
    p = Path(inbox or out.inbox_root()) / out.MANIFEST
    if not p.is_file():
        return False
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if str(r.get("session")) == day:
            return True
    return False


def run(store, ledger, as_of: Optional[str] = None, cl=None, model: Optional[str] = None,
        inbox: Optional[Path] = None, log_dir: Optional[Path] = None) -> dict:
    """One proposer run. Returns what it did; writes only the inbox and its log."""
    as_of = as_of or session.utc_iso(timespec="microseconds")
    day = session.session_date(as_of)
    rec: dict[str, Any] = {"as_of": as_of, "session": day}
    try:
        if already_today(day, inbox):
            rec.update(state="skipped", why="already proposed for this session")
            return rec
        pkt = packet.build(store, ledger, as_of)
        rec["packet_sha256"] = packet.sha256(pkt)
        version = prompt_version()
        rec["prompt_version"] = version
        system, user = build_prompt(pkt)
        if cl is None:
            cl, why = client()
            if cl is None:
                rec.update(state="unavailable", why=why)
                return rec
        model = model or model_id()
        try:
            text, used_model = call(cl, model, system, user)
        except Exception as exc:                              # noqa: BLE001
            rec.update(state="call_failed", why=f"{type(exc).__name__}: {exc}")
            return rec
        rec["model_id"] = used_model
        try:
            props = parse(text)
        except Exception as exc:                              # noqa: BLE001
            rec.update(state="unparseable", why=f"{type(exc).__name__}: {exc}",
                       reply=text[:2000])
            return rec
        accepted, rejected = check(props, store, ledger, day)
        rec.update(proposed=len(props), rejected=rejected)
        if not accepted:
            rec.update(state="nothing_written")
            return rec
        written_at = session.utc_iso(timespec="microseconds")
        batch = {"schema": hyp.SCHEMA_ID,
                 "batch_id": f"{day}-daily-proposer",
                 "source": "model", "proposer": used_model, "channel": CHANNEL,
                 "written_at": written_at, "model_idea_rule": True,
                 "inputs": [f"observation packet sha256 {rec['packet_sha256']}"],
                 "prompt_version": version, "model_id": used_model,
                 "packet_sha256": rec["packet_sha256"], "hypotheses": accepted}
        errs = hyp.validate_batch(batch)
        if errs:
            rec.update(state="schema_failed", why=errs[:6])
            return rec
        data = ("# Alpha Lab hypothesis batch, written by the daily proposer.\n"
                + yaml.safe_dump(batch, sort_keys=False, allow_unicode=False)).encode("utf-8")
        name = f"proposals-{day}.yaml"
        p = out.write_batch(name, data, inbox)
        out.append_manifest({"name": name, "sha256": hashlib.sha256(data).hexdigest(),
                             "written_at": written_at, "session": day,
                             "prompt_version": version, "model_id": used_model},
                            inbox)
        rec.update(state="written", file=str(p), written=[h["title"] for h in accepted])
        return rec
    finally:
        try:
            out.append_log(rec, day[:7], log_dir)
        except Exception:                                     # noqa: BLE001
            pass

