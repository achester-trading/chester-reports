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
