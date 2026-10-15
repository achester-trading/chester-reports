"""
The verdicts outbox (X-2.11; change order 10.2 d).

The weekly loop writes ~/chester-data/outbox/lab/lab-verdicts-YYYY-MM-DD.md
(config/alpha.yaml files.outbox; $ALPHA_OUTBOX), and the nightly sweep copies
that folder up to <remote>:chester-vendor-checks/lab-outbox/ (copy, never sync),
where the Saturday brief reads it. One file a week, dated by the weekly run:

  1. every hypothesis received, screened or tested in the seven days to the run:
     id, title, source, channel, and its status in words -- registered,
     screened out (with the reason), needs_code, data_gap, testing, failed (with
     the metric), refine, promoted -- with n, the deflated Sharpe, the
     expectancy after costs and the slice after 2026-07-01;
  2. the engines live;
  3. the lab line.

Read from alpha.db; written through alpha/files.py only.
"""

from __future__ import annotations

import datetime as dt
import json
from typing import Optional

from altdata import session

from . import files, lab_line, promote
from . import hypotheses as hyp

WORDS = {"registered": "registered", "screened_out": "screened out",
         "needs_code": "needs_code", "data_gap": "data_gap", "testing": "testing",
         "passed": "passed", "failed": "failed", "refined": "refine",
         "promoted": "promoted", "retired": "retired"}


def _since(as_of: str, days: int = 7) -> str:
    end = dt.datetime.fromisoformat(hyp.instant(as_of))
    return (end - dt.timedelta(days=days)).isoformat(timespec="microseconds")


def week_hypotheses(ledger, as_of: str) -> list[dict]:
    """Hypotheses registered, or whose status moved, in the seven days to as_of."""
    since, end = _since(as_of), hyp.instant(as_of)
    reg = hyp.Register(ledger)
    ids = {r["id"] for r in ledger.q("SELECT id FROM hypotheses WHERE written_at>? "
                                     "AND written_at<=?", (since, end))}
    for ev in ledger.q("SELECT after FROM loop_events WHERE kind IN "
                       "('hypothesis_registered','hypothesis_status') AND written_at>? "
                       "AND written_at<=?", (since, end)):
        try:
            ids.add(json.loads(ev["after"])["id"])
        except (ValueError, KeyError, TypeError):
            pass
    return [h for h in (reg.get(i) for i in sorted(ids)) if h]


def _f(x: Optional[float], pct: bool = False) -> str:
    if x is None:
        return "–"
    return f"{x * 100:+.3f}%" if pct else f"{x:.2f}"


def status_words(h: dict) -> str:
    st = WORDS.get(h["status"], h["status"])
    r = h.get("result") or {}
    why = h.get("status_reason") or ""
    if h["status"] == "failed" and r:
        reasons = (r.get("standard_gate") or {}).get("reasons") or [why]
        mr = r.get("model_rule") or {}
        if mr.get("applies") and not mr.get("ok") and not mr.get("pending"):
            reasons = reasons + [mr.get("why", "")]
        return f"failed: {'; '.join(x for x in reasons if x)}"
    if h["status"] in ("screened_out", "needs_code", "data_gap", "testing") and why:
        return f"{st}: {why}"
    return st


def render(ledger, as_of: str) -> str:
    day = session.session_date(as_of)
    hs = week_hypotheses(ledger, as_of)
    out = [f"# Alpha Lab verdicts, week to {day}", "",
           f"Written by the weekly loop at {as_of} from alpha.db. Every hypothesis "
           f"received, screened or tested in the seven days to the run, then the "
           f"engines live and the lab line. Evidence for the Saturday brief, never "
           f"an instruction to it.", "",
           "## Hypotheses this week", ""]
    if not hs:
        out.append("None received, screened or tested this week.")
    else:
        out += ["| Id | Title | Source | Channel | Status | n | Deflated Sharpe | "
                f"Expectancy after costs | After {promote.MODEL_CUTOFF} |",
                "|---|---|---|---|---|---:|---:|---:|---|"]
        for h in hs:
            r = h.get("result") or {}
            m = r.get("metrics") or {}
            mr = r.get("model_rule") or {}
            post = (f"n {mr.get('post_n')}, {_f(mr.get('post_mean'), True)}"
                    if mr.get("applies") else "–")
            cell = lambda s: str(s).replace("|", "\\|").replace("\n", " ")  # noqa: E731
            out.append(f"| {h['id']} ({h['local_id']}) | {cell(h['title'])} | "
                       f"{h['source']} | {h['channel']} | {cell(status_words(h))} | "
                       f"{m.get('n_signals', r.get('n_trades', '–')) if r else '–'} | "
                       f"{_f(m.get('deflated_sharpe')) if r else '–'} | "
                       f"{_f(m.get('expectancy'), True) if r else '–'} | {post} |")
    live = ledger.engines(("live", "halved"))
    out += ["", "## Engines live", ""]
    if not live:
        out.append("None.")
    else:
        out += ["| Engine | Family | Horizon | Status | Validated deflated Sharpe |",
                "|---|---|---|---|---:|"]
        for e in live:
            vm = e.get("validated_metrics") or {}
            out.append(f"| {e['id']} | {e['family']} | {e['horizon']} | {e['status']} | "
                       f"{_f(vm.get('deflated_sharpe'))} |")
    out += ["", "## The lab line", "", lab_line.weekly_line(as_of, ledger.path), ""]
    return "\n".join(out)


def write(ledger, as_of: str) -> str:
    day = session.session_date(as_of)
    p = files.root("outbox") / f"lab-verdicts-{day}.md"
    return str(files.write_text(p, render(ledger, as_of)))
