"""
The critic: "why this could fail", one call per new hypothesis (D43, ruled 31 Oct
2026; the assessment's section 5).

    python -m alpha_proposer            # the proposer, then this step

For each registered hypothesis without a critique, ONE model call sees the
hypothesis's text and its rule -- alpha.critique.inputs(), a whitelist -- and
nothing else: never a status, a result, a validation, a grade or a ledger row
(R-1's information partition: the critic sees the thesis, not the evidence). The
reply is two to five failure modes from the closed vocabulary
(alpha.critique.MODES), each with a sentence and, where it can, the stored series
that would show it.

  - METERED under the model meter (report "alpha_critic", the hypothesis id as the
    section), and BUDGETED: config/alpha.yaml `critic.daily_call_budget`, shipped
    at 0, so nothing is called until the operator raises it.
  - WRITTEN as the proposer writes, through out.py only: critiques-YYYY-MM-DD.yaml
    in the lab's inbox with its manifest line, and a line in the proposer's log.
    The nightly ingestion stores each critique beside its hypothesis, once
    (alpha/inbox.py, alpha/critique.py). This package never writes alpha.db.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Callable, Optional

import yaml

from altdata import session
from alpha import config as acfg
from alpha import critique

from . import out

REPORT = "alpha_critic"
PROMPT_VERSION = "critic-v1 (A98, 31 Oct 2026)"
MAX_TOKENS = 1500
SYSTEM = (
    "You are the critic of a trading hypothesis, before it is tested. You see its "
    "text and its rule only; you never see a result. List two to five ways it could "
    "fail. Each is one of these modes: mechanism (the story is wrong), crowding, "
    "cost (the edge is below costs), regime (it lives in one environment), data (an "
    "artefact of the series or its vintage), capacity, execution. For each give one "
    "sentence and, where you can, the stored series that would show it. Reply with "
    "JSON only: {\"modes\": [{\"mode\": \"...\", \"sentence\": \"...\", "
    "\"series\": \"...\"}]}")


def budget(cfg: Optional[dict] = None) -> int:
    cfg = cfg if cfg is not None else acfg.settings()
    return int(((cfg.get("critic") or {}).get("daily_call_budget")) or 0)


def calls_today(day: str, log_dir=None) -> int:
    p = out.log_root() if log_dir is None else log_dir
    f = p / f"alpha_proposer-{day[:7]}.jsonl"
    if not f.exists():
        return 0
    n = 0
    for ln in f.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(ln)
        except ValueError:
            continue
        n += int(r.get("kind") == "critic_call" and r.get("session") == day)
    return n


def uncritiqued(ledger) -> list[dict]:
    """Registered hypotheses with no critique, oldest first."""
    have: set = set()
    try:
        have = critique.critiqued(ledger)
    except Exception:                                           # noqa: BLE001
        pass                    # a ledger from before A98 has no critiques table
    return [h for h in ledger.q("SELECT * FROM hypotheses ORDER BY pre_registered_at, id")
            if h["id"] not in have]


def model_call(inp: dict) -> tuple[str, str]:
    """One metered call over the inputs; (text, model id)."""
    from altdata import model_meter                             # noqa: PLC0415
    from daily_cascade import narrative                         # noqa: PLC0415
    cl, why = model_meter.client()
    if cl is None:
        raise RuntimeError(f"no model client: {why}")
    model = narrative.DEFAULT_MODEL
    with model_meter.scope(report=REPORT, section=str(inp.get("id"))):
        resp = model_meter.create(cl, model=model, max_tokens=MAX_TOKENS, system=SYSTEM,
                                  messages=[{"role": "user", "content":
                                             json.dumps(inp, sort_keys=True, default=str)}])
    text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
    return text.strip(), (getattr(resp, "model", None) or model)


def parse(text: str) -> Any:
    m = re.search(r"\{.*\}", text or "", re.S)
    try:
        return (json.loads(m.group(0)) if m else {}).get("modes")
    except (ValueError, AttributeError):
        return None


def run(ledger, as_of: Optional[str] = None, *, cfg: Optional[dict] = None,
        call: Optional[Callable[[dict], tuple[str, str]]] = None, inbox=None,
        log_dir=None) -> dict:
    """At most the day's budget of calls; the critiques written as one inbox file.
    `call(inputs) -> (text, model id)` stands in for the model in the gate."""
    as_of = as_of or session.utc_iso()
    day = str(as_of)[:10]
    cap = budget(cfg)
    rec: dict = {"kind": "critic", "session": day, "budget": cap, "called": 0,
                 "written": [], "refused": []}
    if ledger is None:
        rec["state"] = "no ledger"
        return rec
    todo = uncritiqued(ledger)
    room = max(cap - calls_today(day, log_dir), 0)
    if room == 0:
        rec["state"] = (f"budget {cap}: no call made" if cap == 0 else
                        f"the day's {cap} call(s) are spent")
        rec["waiting"] = len(todo)
        out.append_log(rec, day[:7], log_dir)
        return rec
    call = call or model_call
    crits, model = [], None
    for h in todo[:room]:
        inp = critique.inputs(h)
        if critique.leaks(inp):                    # the partition, asserted at runtime
            rec["refused"].append({"hypothesis_id": h["id"], "why": "a result field"})
            continue
        try:
            text, model = call(inp)
        except Exception as exc:                                # noqa: BLE001
            rec["refused"].append({"hypothesis_id": h["id"], "why": f"call: {type(exc).__name__}"})
            continue
        rec["called"] += 1
        out.append_log({"kind": "critic_call", "session": day, "hypothesis_id": h["id"]},
                       day[:7], log_dir)
        modes = parse(text)
        why = critique.check(modes)
        if why:
            rec["refused"].append({"hypothesis_id": h["id"], "why": why})
            continue
        crits.append({"hypothesis_id": h["id"], "author": "critic", "modes": modes,
                      "inputs_sha256": critique.inputs_sha256(inp)})
    if crits:
        doc = {"schema": critique.SCHEMA, "written_at": as_of, "model_id": model,
               "prompt_version": PROMPT_VERSION, "critiques": crits}
        raw = yaml.safe_dump(doc, sort_keys=False, allow_unicode=True).encode("utf-8")
        name = f"{critique.PREFIX}{day}.yaml"
        out.write_batch(name, raw, inbox)
        out.append_manifest({"name": name, "sha256": hashlib.sha256(raw).hexdigest(),
                             "written_at": as_of}, inbox)
        rec["written"] = [c["hypothesis_id"] for c in crits]
        rec["file"] = name
    rec["state"] = "written" if crits else "nothing_written"
    out.append_log(rec, day[:7], log_dir)
    return rec
