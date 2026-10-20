"""
Promotion on the loop's authority (X-2.6), with the model-idea rule (change
order 10.2 b, ruled 14 Oct 04:22 CT).

A hypothesis that passes X-1.6 is written to `engines` at min_size and begins
trading paper at the next loop; the Weekly's lab line and the monthly Lab report
name it; the operator may retire any engine by ruling (a loop_events row with
source=operator). A hypothesis with source MODEL must ALSO:

  1. show non-negative expectancy after costs on data after 2026-07-01 -- the
     model's knowledge runs to mid-2026, so its backtest before then is a screen
     on data it may have seen; after then it is not (model_rule_screen);
  2. run 1.5 x min_signals at minimum size in paper before the allocator may
     raise it (allocator_floor): its backtest screens, its forward paper record
     judges.

A screen with no trade after the cutoff yet is PENDING, not failed: the
hypothesis stays `testing` and the next run looks again.
"""

from __future__ import annotations

import math
import statistics
from typing import Optional

from . import config as acfg

MODEL_CUTOFF = "2026-07-01"
MODEL_PAPER_MULTIPLE = 1.5


def is_model(h: dict) -> bool:
    return h.get("source") == "model" or bool(h.get("model_idea_rule"))


def paper_signals_required(horizon: str, model: bool,
                           con: Optional[dict] = None) -> int:
    n = acfg.min_signals(horizon, con)
    return int(math.ceil(n * MODEL_PAPER_MULTIPLE)) if model else n


def model_rule_screen(h: dict, trades: list[dict], horizon: str) -> dict:
    """The model-idea rule's first half, on a harness run's trades."""
    if not is_model(h):
        return {"applies": False, "ok": True, "why": "not a model idea"}
    post = [float(t["net"]) for t in trades if str(t["signal_day"]) >= MODEL_CUTOFF]
    need = paper_signals_required(horizon, True)
    base = {"applies": True, "cutoff": MODEL_CUTOFF, "post_n": len(post),
            "post_mean": statistics.fmean(post) if post else None,
            "paper_signals_required": need}
    if not post:
        return {**base, "ok": False, "pending": True,
                "why": f"no trade after {MODEL_CUTOFF} yet: the screen waits for one"}
    if base["post_mean"] < 0:
        return {**base, "ok": False, "pending": False,
                "why": f"expectancy after costs after {MODEL_CUTOFF} is negative"}
    return {**base, "ok": True, "pending": False,
            "why": f"non-negative expectancy after costs after {MODEL_CUTOFF}"}


GRAMMAR_CLASS = "alpha.engines.grammar:GrammarEngine"


def promote_passed(ledger, as_of: str, min_size: Optional[float] = None) -> list[dict]:
    """Every PASSED hypothesis with a grammar rule -> a live engine at min_size,
    trading from the next loop; the hypothesis `promoted`. On the loop's own
    authority (X-2.6): one loop_events row each, source loop."""
    from . import hypotheses as hyp                             # noqa: PLC0415
    from . import rules                                         # noqa: PLC0415
    size = float(min_size if min_size is not None
                  else rules.settings().get("costed_size", 0.01))
    reg = hyp.Register(ledger)
    out = []
    for h in reg.all(["passed"]):
        eid = (h.get("spec") or {}).get("engine") or h["id"]
        if not h.get("rule_dsl") and eid == h["id"]:
            continue
        eng = ledger.engine(eid)
        if eng is None:
            continue                     # the harness writes the pass record first
        model = is_model(h)
        vm = dict(eng.get("validated_metrics") or {})
        vm.update({"hypothesis": h["id"], "model_idea": model,
                   "paper_floor_signals": paper_signals_required(eng["horizon"], model)})
        esize = float(eng["min_size"]) if eid != h["id"] else size
        ledger.set_engine(eid, as_of, status="live", frozen=False,
                          validated_metrics=vm, min_size=esize)
        reg.set_status(h["id"], "promoted", as_of,
                       f"promoted to paper at min_size {esize}", engine_id=eid)
        ledger.event("promote", "promotion", as_of, eid,
                     before={"status": eng["status"]},
                     after={"status": "live", "min_size": esize, "hypothesis": h["id"],
                            "model_idea": model,
                            "paper_floor_signals": vm["paper_floor_signals"]},
                     counterfactual={"status": eng["status"]})
        out.append({"engine": eid, "model_idea": model,
                    "paper_floor_signals": vm["paper_floor_signals"]})
    return out


def register_engines(ledger) -> list[dict]:
    """Registry-style entries for the promoted grammar engines alpha.db names --
    the second naming place, the register's, which promotion needs (the loop
    cannot commit config/alpha_engines.yaml)."""
    from . import hypotheses as hyp                             # noqa: PLC0415
    reg = hyp.Register(ledger)
    out = []
    for e in ledger.engines():
        if not str(e["id"]).startswith("HYP-"):
            continue
        h = reg.get(e["id"])
        if not h or not h.get("rule_dsl"):
            continue
        out.append({"id": e["id"], "class": GRAMMAR_CLASS, "family": h["family"],
                    "horizon": e["horizon"], "min_size": e["min_size"],
                    "params": {"hypothesis_id": h["id"], "rule": h["rule_dsl"]}})
    return out


def retire(ledger, engine_id: str, as_of: str, ruling: str) -> None:
    """The operator retires an engine BY RULING (X-2.6): a loop_events row with
    source=operator quoting the ruling. Its positions exit at the next stored
    bar's open (the nightly loop's retired-engine path)."""
    if not ruling.strip():
        raise ValueError("a retirement quotes the operator's ruling")
    e = ledger.engine(engine_id)
    if e is None:
        raise KeyError(engine_id)
    ledger.set_engine(engine_id, as_of, status="retired", frozen=True)
    ledger.event("operator", "kill", as_of, engine_id, before={"status": e["status"]},
                 after={"status": "retired", "ruling": ruling},
                 counterfactual={"status": e["status"]}, source="operator")
    from . import hypotheses as hyp                             # noqa: PLC0415
    if hyp.Register(ledger).get(engine_id):
        hyp.Register(ledger).set_status(engine_id, "retired", as_of,
                                        f"retired by ruling: {ruling}",
                                        engine_id=engine_id, source="operator")


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    import sys                                                  # noqa: PLC0415
    from altdata import session                                 # noqa: PLC0415
    from .ledger import Ledger                                  # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m alpha.promote",
                                 description="The operator's retirement by ruling")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("retire")
    r.add_argument("engine")
    r.add_argument("--ruling", required=True)
    ap.add_argument("--ledger")
    a = ap.parse_args(argv)
    with Ledger(a.ledger) as lg:
        retire(lg, a.engine, session.utc_iso(timespec="microseconds"), a.ruling)
    print(f"{a.engine}: retired by ruling", file=sys.stdout)
    return 0


if __name__ == "__main__":
    import sys as _sys
    raise SystemExit(_main(_sys.argv[1:]))
