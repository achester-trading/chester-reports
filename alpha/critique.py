"""
"WHY THIS COULD FAIL" (D43, ruled 31 Oct 2026; the assessment's section 5).

Every hypothesis carries a critique from a separate critic call that never sees
a result. The call itself is made outside alpha/ (alpha_proposer/critic.py,
through the model meter), because alpha/ imports no network library; this module
is its pure half, inside the lab:

  inputs(h)     what the critic may see: the hypothesis's text and its rule --
                INPUT_FIELDS, a whitelist -- and nothing else. No status, result,
                engine, validation, grade or ledger row reaches it (RESULT_FIELDS
                are named so the gate can prove their absence).
  check(doc)    a critique is two to five failure modes, each one of MODES (the
                closed vocabulary) with a sentence and, where it can, the stored
                series that would show it.
  ingest(...)   the critic's file, read from the lab's inbox by the nightly
                ingestion (alpha/inbox.py), stored in `hypothesis_critiques`,
                one per hypothesis, written once and never edited.

The lab promotes nothing on the strength of a critique: it is a record, graded
later by which mode the evidence matched (the quarterly meta-loop's page).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Optional

PREFIX = "critiques-"
SCHEMA = "alpha-lab-critiques/v1"
MODES = ("mechanism", "crowding", "cost", "regime", "data", "capacity", "execution")
INPUT_FIELDS = ("id", "title", "family", "horizon", "horizon_class", "mechanism",
                "rule_text", "rule_dsl", "universe", "instruments", "conditioning")
# Never an input: the register's verdicts and anything a run produced.
RESULT_FIELDS = ("status", "status_reason", "result", "engine_id", "superseded_by",
                 "expected", "expected_sign", "expected_size", "validated_metrics",
                 "grades", "fills", "edge_posterior", "net_return", "sharpe",
                 "deflated_sharpe", "expectancy", "n_signals")


def inputs(h: dict) -> dict:
    """The critic's whole view of one hypothesis."""
    out = {k: h.get(k) for k in INPUT_FIELDS if h.get(k) not in (None, "")}
    for k in ("instruments", "rule_dsl", "conditioning"):
        if isinstance(out.get(k), str):
            try:
                out[k] = json.loads(out[k])
            except ValueError:
                pass
    return out


def inputs_sha256(inp: dict) -> str:
    return hashlib.sha256(json.dumps(inp, sort_keys=True, default=str)
                          .encode("utf-8")).hexdigest()


def leaks(payload: Any) -> list[str]:
    """Every RESULT_FIELDS key found anywhere in a payload (the gate's check)."""
    found: list[str] = []

    def walk(x: Any) -> None:
        if isinstance(x, dict):
            for k, v in x.items():
                if k in RESULT_FIELDS:
                    found.append(k)
                walk(v)
        elif isinstance(x, (list, tuple)):
            for v in x:
                walk(v)
    walk(payload)
    return sorted(set(found))


def check(modes: Any) -> Optional[str]:
    """None when the critique is 2-5 modes from the vocabulary, each with a
    sentence; else why it is refused."""
    if not isinstance(modes, list) or not 2 <= len(modes) <= 5:
        return "a critique is a list of two to five failure modes"
    for m in modes:
        if not isinstance(m, dict) or m.get("mode") not in MODES:
            return f"a mode outside the vocabulary {MODES}: {m!r}"[:200]
        if not str(m.get("sentence") or "").strip():
            return f"mode {m.get('mode')} carries no sentence"
    return None


def critiqued(ledger) -> set[str]:
    return {r["hypothesis_id"] for r in ledger.q("SELECT hypothesis_id FROM hypothesis_critiques")}


def ingest(ledger, doc: dict, file_name: str, as_of: str) -> dict:
    """Store each critique in the file once; a hypothesis already critiqued, an
    unknown one or a malformed critique is refused and named."""
    out = {"stored": [], "refused": []}
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA:
        out["refused"].append({"why": f"not {SCHEMA}"})
        return out
    have = critiqued(ledger)
    for c in doc.get("critiques") or []:
        hid = str((c or {}).get("hypothesis_id") or "")
        why = check((c or {}).get("modes"))
        if not why and not ledger.one("SELECT 1 FROM hypotheses WHERE id=?", (hid,)):
            why = f"no hypothesis {hid}"
        if not why and hid in have:
            why = f"{hid} is already critiqued: a critique is written once"
        if why:
            out["refused"].append({"hypothesis_id": hid, "why": why})
            continue
        ledger._insert("hypothesis_critiques", {                     # noqa: SLF001
            "hypothesis_id": hid, "modes": json.dumps(c["modes"], sort_keys=True),
            "author": str(c.get("author") or "critic"), "model_id": doc.get("model_id"),
            "prompt_version": doc.get("prompt_version"),
            "inputs_sha256": str(c.get("inputs_sha256") or ""), "file_name": file_name,
            "as_of": as_of})
        have.add(hid)
        out["stored"].append(hid)
    return out
