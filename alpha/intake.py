"""
Admitting a batch into the register -- the one path every channel takes
(the workbench's `new`, X-2.9; the inbox, X-2.11; the research sitting).

    admit(ledger, store, doc, pre_registered_at, as_of, ...)

The batch has already passed the schema check and, for a file, the inbox's
checks on its times. Here, hypothesis by hypothesis and in this order:

  1. A BLOCKED INSTRUMENT is refused: never registered, logged in inbox_log.
  2. OVER A BUDGET (10.2 c) -> screened_out, with the budget it broke. The
     weekly brief: 5 short, 5 medium, 2 a family a batch. The daily proposer:
     3 a batch, 2 a family a week.
  3. A DUPLICATE of anything in the register, failures included (the
     normalised rule hash, or a title at 0.85 similarity) -> screened_out.
  4. THE RULE. In the grammar (the batch's own rule_dsl, else a committed
     translation bound to this file's sha256): compiled against the store ->
     registered; a series or instrument the store does not hold -> data_gap;
     a rule the grammar refuses -> needs_code with the compiler's reasons. A
     translation that says the grammar cannot express it, or a rule in text
     only -> needs_code, queued for the research sitting.
  5. AN INSTRUMENT the store does not hold -> data_gap.

Every admitted hypothesis -- screened out or not -- counts in its family's
variants (10.2 c). Nothing here runs a test.
"""

from __future__ import annotations

from typing import Optional

from . import blocklist, rules
from . import hypotheses as hyp


def instrument_gaps(h: dict, store) -> list[str]:
    """The named instruments the store holds no prices for."""
    out = []
    sym = rules.price_symbols()
    for t in hyp.tickers(h):
        key = sym.get(t)
        if key is None:
            out.append(f"{t} is not a stored price symbol")
        elif store is not None and not store.all_vintages(key):
            out.append(f"the store holds no prices for {t} ({key})")
    return out


def admit(ledger, store, doc: dict, pre_registered_at: str, as_of: str,
          file_name: Optional[str] = None, file_sha256: Optional[str] = None,
          created_time: Optional[str] = None,
          modified_time: Optional[str] = None,
          translations_root=None) -> dict:
    """Register a batch's hypotheses. Returns {registered: {local_id: id},
    statuses: {local_id: status}, refused: [{local_id, reason}]}."""
    reg = hyp.Register(ledger)
    reg.record_batch(doc, pre_registered_at, as_of, file_name, file_sha256,
                     created_time, modified_time)
    over = {lid: why for lid, why in hyp.budget_errors(doc) if lid}
    out = {"batch_id": doc["batch_id"], "registered": {}, "statuses": {},
           "refused": []}
    day = pre_registered_at[:10]
    for h in doc["hypotheses"]:
        lid = h["local_id"]
        bad = hyp.blocked(h)
        if bad:
            why = (f"restricted instrument(s) {', '.join(bad)}: the Brookfield complex "
                   f"never reaches the register")
            ledger._insert("inbox_log", {
                "file_name": file_name or doc["batch_id"], "file_sha256": file_sha256,
                "batch_id": doc["batch_id"], "local_id": lid, "verdict": "refused",
                "reason": why, "created_time": created_time,
                "modified_time": modified_time, "as_of": as_of})
            out["refused"].append({"local_id": lid, "reason": why})
            continue
        status, reason, dsl, origin = "registered", None, None, None
        if lid in over:
            status, reason = "screened_out", over[lid]
        elif doc["channel"] == "daily-proposer" and reg.family_week_count(
                h["family"], day, channel="daily-proposer") >= \
                hyp.BUDGETS["daily-proposer"]["per_family_per_week"]:
            status, reason = "screened_out", (
                f"over the daily proposer's {hyp.BUDGETS['daily-proposer']['per_family_per_week']}"
                f" of family {h['family']} a week")
        if status == "registered":
            tr = None
            if isinstance(h.get("rule_dsl"), dict):
                dsl, origin = h["rule_dsl"], "batch"
            else:
                tr = hyp.translation_for(doc["batch_id"], lid, file_sha256,
                                         translations_root)
                if tr and isinstance(tr.get("rule_dsl"), dict):
                    dsl, origin = tr["rule_dsl"], "translation"
            dup = reg.duplicate_of({**h, "rule_dsl": dsl})
            if dup:
                status, reason = "screened_out", f"duplicate: {dup[1]}"
            elif dsl is not None:
                try:
                    rules.compile_rule(dsl, store)
                except rules.RuleError as exc:
                    gaps = [m for m in exc.errors if "data gap" in m]
                    if gaps:
                        status, reason = "data_gap", "; ".join(gaps)
                    else:
                        status, reason = "needs_code", ("the grammar refused the rule: "
                                                        + "; ".join(exc.errors[:6]))
            elif tr and tr.get("needs_code_reason"):
                status = "needs_code"
                reason = " ".join(str(tr["needs_code_reason"]).split())
            else:
                status, reason = "needs_code", ("the rule is in text only: queued for "
                                                "the research sitting")
            if status in ("registered", "needs_code"):
                gaps = instrument_gaps({**h, "rule_dsl": dsl}, store)
                if gaps:
                    status, reason = "data_gap", "; ".join(gaps)
        try:
            hid = reg.register(h, doc, pre_registered_at, as_of, status, reason,
                               rule_dsl=dsl, rule_origin=origin)
        except blocklist.BlockedInstrument as exc:
            out["refused"].append({"local_id": lid, "reason": str(exc)})
            continue
        out["registered"][lid] = hid
        out["statuses"][lid] = status
    return out
