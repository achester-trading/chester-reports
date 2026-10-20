"""
The research workbench (X-2.9; change order 10.1, ruled 14 Oct 04:13 CT).

The operator's own ideas, and ideas brought to the chat and written into exact
rules there, enter the same pipeline as the lab's:

  new     pre-registers them: the instant `new` writes them to the register is
          their pre_registered_at (source operator or chat; channel workbench
          or chat). A rule in the grammar registers; a rule in text registers
          needs_code and is queued for the research sitting.
  run     puts a registered rule through X-1.6 unchanged (alpha/validate.py):
          point-in-time, walk-forward with the embargo, the hold-out kept for
          the final check, deflated by its family's variant count, the minimum
          sample. A model idea must also pass the model-idea rule's screen
          (alpha/promote.py). The result is written to the register.
  report  writes a one-page verdict to alpha/research/reports/<id>.md: edge after
          costs, the deflated Sharpe, results by regime key, the variants tried,
          the hold-out check -- ending in reject, refine (a new pre-registered
          variant, `supersedes: <id>`, counted against the original) or promote
          to paper (minimum size, the loop's ordinary path).

A Book B setup or a sitting idea may be tested the same way. The verdict is
evidence for the sitting, never an instruction to it.

COUNTING. A hypothesis counted one variant when it registered. Its first run
counts one more for each conditioning value and each drop or replace variant,
BEFORE the base is scored, so the base is deflated by everything the run tries;
the base itself is not counted twice. A re-run of the unchanged rule on more data
counts nothing new: a changed rule is a new hypothesis.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any, Optional

from altdata import session

from .. import config as acfg
from .. import files, intake, manifest, promote, rules
from .. import hypotheses as hyp
from .. import validate as av

FIT_ROWS, TEST_ROWS = 1, 10
HISTORY_FIRST = "1990-01-02"


class QueuedForSitting(RuntimeError):
    """A rule in text only: the research sitting writes the code for it."""


def new(ledger, store, doc: Any, source: str = "operator",
        as_of: Optional[str] = None, file_name: Optional[str] = None) -> dict:
    """Pre-register an idea now. `doc` is a v1 batch, one hypothesis, or a list
    of them; a bare hypothesis is wrapped in a workbench batch."""
    now = as_of or session.utc_iso(timespec="microseconds")
    if source not in ("operator", "chat"):
        raise ValueError("the workbench registers the operator's ideas and the "
                         "chat's (source operator or chat); a model's go through "
                         "the inbox")
    if isinstance(doc, dict) and doc.get("schema") == hyp.SCHEMA_ID:
        batch = doc
        if batch.get("source") not in ("operator", "chat"):
            raise ValueError(f"a workbench batch's source is operator or chat, not "
                             f"{batch.get('source')!r}")
    else:
        items = doc if isinstance(doc, list) else [doc]
        stamp = dt.datetime.fromisoformat(now).strftime("%Y%m%dT%H%M%S")
        batch = {"schema": hyp.SCHEMA_ID, "batch_id": f"wb-{stamp}-{source}",
                 "source": source, "proposer": source,
                 "channel": "workbench" if source == "operator" else "chat",
                 "written_at": now, "model_idea_rule": False,
                 "inputs": [file_name or "workbench"], "hypotheses": items}
    errs = hyp.validate_batch(batch)
    if errs:
        raise ValueError("the batch fails the v1 schema: " + "; ".join(errs[:8]))
    if hyp.Register(ledger).batch(batch["batch_id"]):
        raise ValueError(f"batch {batch['batch_id']} is already registered")
    # X-3: THE MANIFEST FIRST (alpha/manifest.py), then the register at its
    # instant; the batch row carries the manifest's sha256.
    m = manifest.write(batch, now)
    out = intake.admit(ledger, store, batch, m["written_at"], now,
                       file_name=m["name"], file_sha256=m["sha256"],
                       created_time=m["written_at"])
    out["manifest"] = m
    return out


def _rows(trades: list[dict]) -> list[dict]:
    return [{"day": t["signal_day"], "decided_at": t["decided_at"],
             "available_at": t["available_at"], "net": t["net"]} for t in trades]


def _strategy(family: str, horizon: str) -> av.Strategy:
    # A grammar rule has no free parameter: its numbers were fixed when it was
    # written, so the fit returns nothing and the walk-forward tests the rule as
    # registered, window by window, with the embargo and the hold-out intact.
    return av.Strategy(family=family, horizon=horizon, fit=lambda rows: {},
                       returns=lambda rows, p: [float(r["net"]) for r in rows])


def _span(store, cmp: rules.Compiled, as_of: str) -> tuple[str, str]:
    data = rules.Data(store)
    firsts = [data.series(rules.resolve(s)).days[:1] for s in cmp.instruments]
    first = min((f[0] for f in firsts if f), default=HISTORY_FIRST)
    return first, session.session_date(as_of)


def run(ledger, store, hid: str, as_of: Optional[str] = None) -> dict:
    """One harness run of a registered hypothesis; its result in the register."""
    as_of = as_of or session.utc_iso(timespec="microseconds")
    reg = hyp.Register(ledger)
    h = reg.get(hid)
    if h and h["status"] == "needs_code":
        raise QueuedForSitting(f"{hid} is needs_code ({h.get('status_reason')}): "
                               f"queued for the research sitting")
    hyp.refuse_if_unregistered(h, as_of)
    manifest.check(ledger, h, as_of)
    if h["status"] == "data_gap":
        raise QueuedForSitting(f"{hid} is a data gap ({h.get('status_reason')})")
    first_run = h["status"] == "registered"
    if (h.get("spec") or {}).get("engine"):
        return run_engine(ledger, store, h, as_of, first_run)
    cmp = rules.compile_rule(h["rule_dsl"], store)
    con, cfg = acfg.constitution(), acfg.settings()
    family = h["family"]
    if first_run:
        n_var = len(cmp.variants)
        for _ in range(n_var):
            ledger.bump_variant(family, as_of)
        reg.set_status(hid, "testing", as_of, "the harness has it")
    first, last = _span(store, cmp, as_of)
    data = rules.Data(store)
    bt = rules.backtest(cmp, store, first, last, data=data)
    trades = bt["trades"]
    strat = _strategy(family, cmp.horizon)
    min_size = float(rules.settings().get("costed_size", 0.01))
    res = av.run(ledger, hid, strat, _rows(trades), as_of, FIT_ROWS, TEST_ROWS,
                 min_size=min_size, con=con, cfg=cfg, count_variant=False)
    by_regime: dict[str, list] = {}
    for t in trades:
        key = store.regime_key(t["decided_at"], t["signal_day"])
        by_regime.setdefault(key, []).append(t)
    variants = []
    for v in cmp.variants:
        if v["kind"] in ("drop", "replace"):
            vc, drop = rules.variant_rule(cmp, v)
            vt = rules.backtest(vc, store, first, last, drop=drop, data=data)["trades"]
            variants.append({"name": v["name"], "kind": v["kind"],
                             "summary": rules.summarise(vt)})
    for k, s in rules.by_variant(cmp, trades).items():
        variants.append({"name": k, "kind": "split", "summary": s})
    screen = promote.model_rule_screen(h, trades, cmp.horizon)
    passed = bool(res["passed"]) and screen["ok"]
    m = res["metrics"]
    result = {
        "run_at": as_of, "span": [first, last], "n_trades": len(trades),
        "summary": rules.summarise(trades), "passed": passed,
        "standard_gate": {"passed": res["passed"], "reasons": res["reasons"]},
        "metrics": {k: m[k] for k in ("n_signals", "expectancy", "sr_ann",
                                       "deflated_sharpe", "dsr_prob", "n_trials",
                                       "holdout_n", "holdout_expectancy",
                                       "min_signals", "deflated_sharpe_min")},
        "by_regime": {k: rules.summarise(v) for k, v in sorted(by_regime.items())},
        "variants": variants, "model_rule": screen, "skipped": bt["skipped"],
        "horizon": cmp.horizon,
    }
    if passed:
        status, why = "passed", "through X-1.6" + (" and the model-idea screen"
                                                    if screen["applies"] else "")
    elif res["passed"] and not screen["ok"]:
        status, why = ("testing", screen["why"]) if screen.get("pending") else \
            ("failed", screen["why"])
    else:
        status, why = "failed", "; ".join(res["reasons"]) or "failed"
    reg.set_status(hid, status, as_of, why, result=result)
    return {"id": hid, "status": status, "reason": why, "result": result}


ENGINE_WINDOWS = {"weekly": (52, 13), "daily": (60, 20)}


def _summ(x: list) -> dict:
    import statistics                                           # noqa: PLC0415
    return {"n": len(x), "mean_net": statistics.fmean(x) if x else None,
            "hit_rate": (sum(1 for v in x if v > 0) / len(x)) if x else None}


def run_engine(ledger, store, h: dict, as_of: str, first_run: bool) -> dict:
    """A CODED engine's hypothesis (the roster): its coverage check first -- a
    store that cannot reach the minimum sample makes it a data gap, said so --
    then X-1.6 unchanged on the engine's own point-in-time rows and strategy.
    On a first run the engine's fitting grid is counted (each further grid point
    one more variant, beyond the one its registration counted) before scoring."""
    from .. import engine as engine_mod                         # noqa: PLC0415
    reg = hyp.Register(ledger)
    hid, eid = h["id"], h["spec"]["engine"]
    entry = next((e for e in engine_mod.registered() if e["id"] == eid), None)
    if entry is None:
        raise QueuedForSitting(f"{hid}: engine {eid} is not registered")
    eng = engine_mod.load(entry)
    cov = eng.coverage(store, as_of) if hasattr(eng, "coverage") else {"ok": True}
    if not cov.get("ok") and cov.get("wait"):
        # X-3.2: a history window the manifest states and the store has not yet
        # met. Nothing runs and nothing is counted; the hypothesis stays
        # registered, so the nightly harness looks again once the window fills.
        if h.get("status_reason") != cov.get("why"):
            reg.set_status(hid, "registered", as_of, cov.get("why"))
        return {"id": hid, "status": "insufficient_history", "reason": cov.get("why"),
                "result": {"coverage": cov}}
    if not cov.get("ok"):
        reg.set_status(hid, "data_gap", as_of, cov.get("why"),
                       result={"coverage": cov, "run_at": as_of})
        return {"id": hid, "status": "data_gap", "reason": cov.get("why"),
                "result": {"coverage": cov}}
    if not (hasattr(eng, "refit_rows") and hasattr(eng, "strategy")):
        raise QueuedForSitting(f"{hid}: engine {eid} has no harness hooks")
    if first_run:
        for _ in range(max(0, int(getattr(eng, "grid_size", 1)) - 1)):
            ledger.bump_variant(eng.family, as_of)
        reg.set_status(hid, "testing", as_of, "the harness has it")
    rows = eng.refit_rows(store, as_of)
    strat = eng.strategy()
    fit_rows, test_rows = ENGINE_WINDOWS.get(eng.horizon, (60, 20))
    res = av.run(ledger, eid, strat, rows, as_of, fit_rows, test_rows,
                 min_size=eng.min_size, count_variant=False)
    final = res.get("final_params") or {}
    nets = list(strat.returns(rows, final)) if rows else []
    by_regime: dict[str, list] = {}
    for r, x in zip(rows, nets):
        by_regime.setdefault(store.regime_key(r["decided_at"], r["day"]), []).append(x)
    m = res["metrics"]
    result = {"run_at": as_of, "engine": eid, "coverage": cov, "n_trades": len(rows),
              "span": [rows[0]["day"], rows[-1]["day"]] if rows else [None, None],
              "summary": _summ(nets), "passed": res["passed"],
              "standard_gate": {"passed": res["passed"], "reasons": res["reasons"]},
              "metrics": {k: m[k] for k in ("n_signals", "expectancy", "sr_ann",
                                             "deflated_sharpe", "dsr_prob", "n_trials",
                                             "holdout_n", "holdout_expectancy",
                                             "min_signals", "deflated_sharpe_min")},
              "final_params": final, "ranges": res.get("ranges"),
              "by_regime": {k: _summ(v) for k, v in sorted(by_regime.items())},
              "variants": [], "model_rule": {"applies": False},
              "horizon": eng.horizon}
    status = "passed" if res["passed"] else "failed"
    why = "through X-1.6" if res["passed"] else "; ".join(res["reasons"])
    reg.set_status(hid, status, as_of, why, result=result, engine_id=eid)
    return {"id": hid, "status": status, "reason": why, "result": result}


def verdict(h: dict) -> tuple[str, str]:
    """reject | refine | promote to paper | queued, with the reason."""
    st = h["status"]
    if st in ("needs_code", "data_gap"):
        return "queued", f"{st}: {h.get('status_reason')}"
    r = h.get("result") or {}
    if st in ("passed", "promoted"):
        return "promote to paper", ("passed the harness; the loop promotes it at "
                                    "minimum size")
    if st == "registered" or not r:
        return "not yet run", "run it first: python -m alpha.research run " + h["id"]
    exp = (r.get("metrics") or {}).get("expectancy") or 0.0
    reasons = (r.get("standard_gate") or {}).get("reasons") or []
    if exp > 0 and not any("expectancy after costs" in x for x in reasons):
        return "refine", ("positive expectancy after costs but " + "; ".join(reasons)
                          + ". A refinement is a NEW pre-registered variant "
                          f"(supersedes: {h['id']}), counted against this one")
    return "reject", "; ".join(reasons) or (h.get("status_reason") or "")


def _pct(x: Optional[float], digits: int = 2) -> str:
    return "n/a" if x is None else f"{x * 100:+.{digits}f}%"


def _rate(x: Optional[float]) -> str:
    return "n/a" if x is None else f"{x * 100:.0f}%"


def _cell(s: str) -> str:
    return str(s).replace("|", "\\|")


def render_report(h: dict) -> str:
    r = h.get("result") or {}
    m = r.get("metrics") or {}
    s = r.get("summary") or {}
    v, why = verdict(h)
    lines = [f"# {h['id']}: {h['title']}", "",
             f"**Verdict: {v}.** {why}", "",
             "This verdict is evidence for the sitting, never an instruction to it.", "",
             "| | |", "|---|---|",
             f"| Family | {h['family']} (variants counted: {m.get('n_trials', 'n/a')}) |",
             f"| Source / channel | {h['source']} / {h['channel']} |",
             f"| Pre-registered | {h['pre_registered_at']} |",
             f"| Status | {h['status']} ({h.get('status_reason') or ''}) |",
             f"| Rule | {'grammar v1 (' + str(h.get('rule_origin')) + ')' if h.get('rule_dsl') else 'text only'} |",
             ""]
    if r:
        lines += ["## Edge after costs", "",
                  f"- Trades: {r.get('n_trades')} over {r['span'][0]} to {r['span'][1]}; "
                  f"out-of-sample signals {m.get('n_signals')} (minimum {m.get('min_signals')}).",
                  f"- Expectancy after costs a trade: {_pct(m.get('expectancy'), 3)}; "
                  f"hit rate {_rate(s.get('hit_rate'))}; mean cost {_pct(s.get('mean_cost'), 3)}.",
                  f"- Deflated Sharpe: {m.get('deflated_sharpe', 0):.2f} against "
                  f"{m.get('deflated_sharpe_min')} (probabilistic {m.get('dsr_prob', 0):.2f}; "
                  f"annualised Sharpe {m.get('sr_ann', 0):.2f}).",
                  f"- Hold-out (every fourth month, never fitted): n {m.get('holdout_n')}, "
                  f"expectancy {_pct(m.get('holdout_expectancy'), 3)}.", ""]
        mr = r.get("model_rule") or {}
        if mr.get("applies"):
            lines += ["## The model-idea rule (10.2 b)", "",
                      f"- After {promote.MODEL_CUTOFF}: n {mr.get('post_n')}, expectancy "
                      f"{_pct(mr.get('post_mean'), 3)} -- {mr.get('why')}.",
                      f"- Paper period before the allocator may raise it: "
                      f"{mr.get('paper_signals_required')} signals at minimum size.", ""]
        lines += ["## By regime key", "", "| Regime | n | Expectancy | Hit rate |",
                  "|---|---:|---:|---:|"]
        for k, x in (r.get("by_regime") or {}).items():
            lines.append(f"| {_cell(k)} | {x.get('n', 0)} | {_pct(x.get('mean_net'), 3)} | "
                         f"{_rate(x.get('hit_rate'))} |")
        lines += ["", "## Variants tried", "", "| Variant | Kind | n | Expectancy |",
                  "|---|---|---:|---:|"]
        for x in r.get("variants") or []:
            ss = x.get("summary") or {}
            lines.append(f"| {_cell(x['name'])} | {x['kind']} | {ss.get('n', 0)} | "
                         f"{_pct(ss.get('mean_net'), 3)} |")
        if not r.get("variants"):
            lines.append("| none declared | | | |")
        lines.append("")
        reasons = (r.get("standard_gate") or {}).get("reasons") or []
        if reasons:
            lines += ["## Why the standard gate did not pass", ""] + \
                [f"- {x}" for x in reasons] + [""]
    lines += ["## The idea as registered", "", f"**Mechanism.** {h['mechanism']}", "",
              f"**Rule.** {h['rule_text']}", ""]
    return "\n".join(lines)


def report(ledger, hid: str, out_dir=None) -> str:
    """Write the one-page verdict; returns its path."""
    h = hyp.Register(ledger).get(hid)
    if not h:
        raise KeyError(hid)
    d = Path(out_dir) if out_dir else files.root("reports_dir")
    return str(files.write_text(d / f"{hid}.md", render_report(h)))
