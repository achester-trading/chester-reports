"""
The weekly loop (X-2.4; the brief's section 8, loop 2) -- re-validate, re-fit
within bounds, rebalance, and write the research agenda.

    python -m alpha.loops.weekly [--as-of ISO] [--ledger PATH] [--store PATH]

Sunday after the Weekly's run (chester-alpha-weekly.timer, 06:00 ET). In order,
each step its own try, every change a loop_events row:

  1. WALK-FORWARD, EXTENDED BY THE WEEK. Each live or halved engine's
     out-of-sample record is extended to the week's last session and its
     metrics recorded (`walk_forward`). A grammar engine's rule is fixed, so
     this is its whole step.
  2. RE-FIT WITHIN THE VALIDATED RANGES. A coded engine that exposes the
     re-fit hooks (Engine.refit_rows / strategy) is re-estimated on its fit
     window; the new parameters are accepted ONLY if every one lies inside the
     ranges the engine was validated over AND the deflated out-of-sample metric
     on the embargoed window improves on the current parameters'. Every re-fit
     is one more variant of the family, accepted or not. A parameter that wants
     to leave its range is NOT moved: it is logged as a hypothesis (the
     register, source systematic) for the gate. A frozen engine (halved or
     stopped) is never re-fitted (the constitution's refit.frozen_in_drawdown).
  3. THE ALLOCATOR'S REBALANCE: the nightly loop's latest proposed weights
     applied (X-1.7).
  4. THE RESEARCH AGENDA, alpha/research/agenda.md and agenda.json, from the
     residuals: losses by regime, instrument and day; the move screen's prints
     without a position; the engines' pairwise correlation (crowding); the
     backtest-to-paper gap per engine; and the register's open queue
     (needs_code, data_gap). A copy goes to the outbox for the Saturday brief.
  5. THE VERDICTS (X-2.11): lab-verdicts-YYYY-MM-DD.md into the outbox.
  6. THE GRAMMAR SEARCH (X-3.5; alpha/search.py): a run begins in the first week
     of each month and an unfinished one resumes on any week, one capped step a
     week (candidates and wall clock, config/alpha_search.yaml); its line
     reaches the Monthly's Lab report. No new timer.

It reads the store read-only and alpha.db, and writes alpha.db and, through
alpha/files.py, the agenda and the outbox only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import math
import statistics
import sys
import traceback
from typing import Optional

from altdata import session

from .. import book, files, governor, promote, rules, screen
from .. import search as search_mod
from .. import config as acfg
from .. import engine as engine_mod
from .. import hypotheses as hyp
from .. import validate as av
from ..ledger import Ledger
from ..store import ReadOnlyStore
from . import quarterly

log = logging.getLogger(__name__)
LOOP = "weekly"
AGENDA_WEEKS = 4


def week_days(as_of: str) -> list[str]:
    """The sessions of the seven days to as_of."""
    end = dt.date.fromisoformat(session.session_date(as_of))
    out, d = [], end - dt.timedelta(days=7)
    while d <= end:
        if session.is_trading_session(d):
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


# ---------------------------------------------------------------------------
# 1-2. Walk-forward and the bounded re-fit
# ---------------------------------------------------------------------------
def _loaded(ledger: Ledger, registry_path=None) -> dict[str, engine_mod.Engine]:
    entries = list(engine_mod.registered(registry_path)) + promote.register_engines(ledger)
    out = {}
    for e in entries:
        eng = engine_mod.load(e)
        refit = latest_refit(ledger, eng.engine_id)
        if refit:
            eng.params.update(refit)
        out[eng.engine_id] = eng
    return out


def latest_refit(ledger: Ledger, engine_id: str) -> Optional[dict]:
    """The parameters of the last accepted, unreversed re-fit."""
    r = ledger.one("SELECT after FROM loop_events WHERE engine=? AND kind='refit_accepted'"
                   " AND reversed_by IS NULL ORDER BY id DESC LIMIT 1", (engine_id,))
    return json.loads(r["after"]).get("params") if r else None


def _in_ranges(params: dict, ranges: dict) -> list[str]:
    out = []
    for k, v in params.items():
        rg = ranges.get(k)
        if rg and isinstance(v, (int, float)) and not isinstance(v, bool) and \
                not (float(rg[0]) <= float(v) <= float(rg[1])):
            out.append(f"{k}={v} outside its validated range {rg}")
    return out


def walk_forward(ledger: Ledger, store: ReadOnlyStore, as_of: str,
                 registry_path=None) -> dict:
    con, cfg = acfg.constitution(), acfg.settings()
    engines = _loaded(ledger, registry_path)
    done: dict[str, dict] = {}
    for e in ledger.engines(("live", "halved")):
        eng = engines.get(e["id"])
        if eng is None:
            continue
        if str(e["id"]).startswith("HYP-"):
            done[e["id"]] = _grammar_extend(ledger, store, e, as_of)
            continue
        if not (hasattr(eng, "refit_rows") and hasattr(eng, "strategy")):
            ledger.event(LOOP, "walk_forward", as_of, e["id"],
                         after={"why": "no re-fit hooks: the engine's record extends "
                                       "through the nightly loop's grades"})
            continue
        if not av.refit_allowed(e, con):
            ledger.event(LOOP, "refit_skipped", as_of, e["id"],
                         after={"why": "frozen: no re-fitting inside a drawdown"})
            done[e["id"]] = {"refit": "frozen"}
            continue
        # X-3.7: the cadence in force (the quarterly meta-loop slows it after a
        # quarter whose loop contribution was negative)
        due, why = quarterly.refit_due(ledger, e["id"], as_of)
        if not due:
            ledger.event(LOOP, "refit_skipped", as_of, e["id"], after={"why": why})
            done[e["id"]] = {"refit": "not_due"}
            continue
        done[e["id"]] = refit(ledger, store, eng, e, as_of, con, cfg)
    return {"walk_forward": done}


def _grammar_extend(ledger, store, e: dict, as_of: str) -> dict:
    h = hyp.Register(ledger).get(e["id"])
    cmp = rules.compile_rule(h["rule_dsl"])
    last = session.session_date(as_of)
    data = rules.Data(store)
    first = min((data.series(rules.resolve(s)).days[:1] or [last])[0]
                for s in cmp.instruments)
    tr = rules.backtest(cmp, store, first, last, data=data)["trades"]
    x = [t["net"] for t in tr]
    n_trials = max(1, ledger.variant_count(h["family"]))
    ds = av.deflated_sharpe(x, n_trials, acfg.periods_per_year(cmp.horizon))
    out = {"n": len(x), "expectancy": ds["mean"], "deflated_sharpe": ds["deflated_sharpe"],
           "through": last, "n_trials": n_trials}
    ledger.event(LOOP, "walk_forward", as_of, e["id"], after=out)
    return out


def refit(ledger, store, eng, e: dict, as_of: str, con: dict, cfg: dict) -> dict:
    """One bounded re-fit. Counts one variant whatever it decides."""
    strat: av.Strategy = eng.strategy()
    rows = sorted(eng.refit_rows(store, as_of), key=lambda r: r["day"])
    av.check_pit(rows)
    every = av.holdout_every(con)
    rows = [r for r in rows if not av.is_holdout(r["day"], every)]
    gap = int(con["validation"]["embargo_horizons"]) * av.HORIZON_ROWS[e["horizon"]]
    test_n = int(getattr(eng, "refit_test_rows", 52))
    if len(rows) < test_n + gap + 20:
        ledger.event(LOOP, "refit_skipped", as_of, e["id"],
                     after={"why": f"too few rows ({len(rows)}) for a re-fit"})
        return {"refit": "skipped"}
    fit, test = rows[:-(test_n + gap)], rows[-test_n:]
    n_trials = ledger.bump_variant(e["family"], as_of)
    current = dict(eng.params)
    proposed = strat.fit(fit)
    ppy = acfg.periods_per_year(e["horizon"], cfg)
    cur = av.deflated_sharpe(list(strat.returns(test, current)), n_trials, ppy)
    new = av.deflated_sharpe(list(strat.returns(test, proposed)), n_trials, ppy)
    # X-3.7: the validated ranges, or the meta-loop's narrowed ones in force
    ranges = quarterly.effective_ranges(ledger, e, as_of)
    outside = _in_ranges(proposed, ranges)
    base = {"current": current, "proposed": proposed, "n_trials": n_trials,
            "current_dsr": cur["deflated_sharpe"], "proposed_dsr": new["deflated_sharpe"],
            "test": [test[0]["day"], test[-1]["day"]], "embargo_rows": gap}
    if outside:
        hid = _wants_out(ledger, e, proposed, outside, as_of)
        ledger.event(LOOP, "refit_out_of_range", as_of, e["id"],
                     after={**base, "outside": outside, "hypothesis": hid},
                     counterfactual={"params": proposed})
        return {"refit": "out_of_range", "hypothesis": hid}
    if new["deflated_sharpe"] > cur["deflated_sharpe"] and proposed != current:
        ledger.event(LOOP, "refit_accepted", as_of, e["id"], before={"params": current},
                     after={**base, "params": proposed},
                     counterfactual={"params": current})
        return {"refit": "accepted", "params": proposed}
    ledger.event(LOOP, "refit_rejected", as_of, e["id"], before={"params": current},
                 after={**base, "why": "the deflated out-of-sample metric did not improve"},
                 counterfactual={"params": proposed})
    return {"refit": "rejected"}


def _wants_out(ledger, e: dict, proposed: dict, outside: list[str], as_of: str) -> str:
    """A parameter that wants to leave its range is a NEW idea, through the gate:
    registered as a systematic hypothesis, never moved."""
    now = hyp.instant(as_of)
    batch = {"schema": hyp.SCHEMA_ID, "batch_id": f"refit-{e['id']}-{now[:19]}",
             "source": "systematic", "proposer": "the weekly loop",
             "channel": "sitting", "written_at": now, "model_idea_rule": False,
             "inputs": [f"engine {e['id']} re-fit"], "hypotheses": []}
    h = {"local_id": "R-1",
         "title": f"{e['id']} with parameters outside its validated ranges ({now[:10]})",
         "horizon_class": "short", "horizon_sessions": 5, "family": e["family"],
         "mechanism": f"The weekly re-fit of {e['id']} wanted parameters outside the "
                      f"ranges it was validated over: {'; '.join(outside)}. A new "
                      f"range is a new engine, through the gate.",
         "universe": "the engine's universe",
         "rule_text": f"{e['id']} at {json.dumps(proposed, sort_keys=True)}",
         "conditioning": [], "expected": {"sign": "positive_expectancy_after_costs"},
         "sample": {"min_independent_signals": acfg.min_signals(e["horizon"])},
         "data": {"in_store": [], "gaps": []}, "needs_code": True,
         "kill": "constitution", "state_at_registration": "; ".join(outside)}
    batch["hypotheses"] = [h]
    reg = hyp.Register(ledger)
    reg.record_batch(batch, now, as_of)
    return reg.register(h, batch, now, as_of, "needs_code",
                        "an engine's re-fit outside its validated ranges: a new "
                        "engine, coded and validated through the gate")


def meta_loop(ledger: Ledger, store: ReadOnlyStore, as_of: str,
              registry_path=None) -> dict:
    """X-3.7: the last closed quarter's review, when one is due and not yet
    made (quarterly.adjust is idempotent per quarter)."""
    q = quarterly.due_quarter(ledger, as_of)
    if not q:
        return {"meta_loop": None}
    rv = quarterly.review(ledger, store, q, _loaded(ledger, registry_path))
    adj = quarterly.adjust(ledger, rv, as_of)
    return {"meta_loop": {"quarter": q, "net_contribution": rv["net_contribution"],
                          "adjusted": bool(adj)}}


# ---------------------------------------------------------------------------
# 3. The rebalance (X-1.7)
# ---------------------------------------------------------------------------
def rebalance(ledger: Ledger, as_of: str) -> dict:
    day = session.session_date(as_of)
    if governor.lab_status(ledger) == "halted":
        ledger.event(LOOP, "rebalance_skipped", as_of, None,
                     after={"why": "the lab is halted for the operator's review"})
        return {"day": day, "applied": {}, "skipped": "lab halted"}
    last = ledger.one("SELECT MAX(day) AS d FROM allocations WHERE kind='proposed' "
                      "AND day<=?", (day,))
    if not last or not last["d"]:
        return {"day": day, "applied": {}, "skipped": "nothing proposed"}
    proposed = ledger.q("SELECT * FROM allocations WHERE kind='proposed' AND day=?",
                        (last["d"],))
    before = {}
    for p in proposed:
        r = ledger.one("SELECT weight FROM allocations WHERE engine_id=? AND "
                       "kind='applied' AND day<? ORDER BY day DESC LIMIT 1",
                       (p["engine_id"], day))
        before[p["engine_id"]] = r["weight"] if r else None
    applied = {}
    for p in proposed:
        ledger.put("allocations", {"engine_id": p["engine_id"], "day": day,
                                   "kind": "applied", "weight": p["weight"],
                                   "cluster": p["cluster"],
                                   "detail": f"applied from the {last['d']} proposal",
                                   "as_of": as_of})
        applied[p["engine_id"]] = p["weight"]
    ledger.event(LOOP, "rebalance", as_of, None, before=before,
                 after={"weights": applied, "proposed_on": last["d"]},
                 counterfactual={"weights": before})
    return {"day": day, "applied": applied, "proposed_on": last["d"]}


# ---------------------------------------------------------------------------
# 4. The research agenda
# ---------------------------------------------------------------------------
def _corr(a: dict, b: dict) -> Optional[float]:
    common = sorted(set(a) & set(b))
    if len(common) < 10:
        return None
    x, y = [a[d] for d in common], [b[d] for d in common]
    try:
        return statistics.correlation(x, y)
    except statistics.StatisticsError:
        return None


def agenda(ledger: Ledger, store: Optional[ReadOnlyStore], as_of: str) -> dict:
    day = session.session_date(as_of)
    since = (dt.date.fromisoformat(day) - dt.timedelta(weeks=AGENDA_WEEKS)).isoformat()
    losses = ledger.q(
        "SELECT g.engine_id, g.day, g.regime_key, g.net_pnl, p.instrument FROM grades g "
        "JOIN positions p ON p.id = g.position_id WHERE g.net_pnl < 0 AND g.day >= ? "
        "ORDER BY g.day", (since,))
    def group(key: str) -> list[dict]:
        acc: dict[str, list] = {}
        for r in losses:
            acc.setdefault(str(r[key]), []).append(r["net_pnl"])
        return sorted(({key: k, "n": len(v), "net_pnl": round(sum(v), 2)}
                       for k, v in acc.items()), key=lambda z: z["net_pnl"])
    unpositioned = []
    if store is not None:
        data = rules.Data(store)
        for d in week_days(as_of):
            held = {r["instrument"] for r in ledger.q(
                "SELECT instrument FROM positions WHERE substr(opened_at,1,10)<=? AND "
                "(closed_at IS NULL OR substr(closed_at,1,10)>=?)", (d, d))}
            for m in screen.prints(screen.moves(store, as_of, d, data)):
                if m["symbol"] not in held:
                    unpositioned.append(m)
    live = ledger.engines(("live", "halved"))
    rets = {e["id"]: book.daily_returns(ledger, e["id"]) for e in live}
    pairs = []
    ids = sorted(rets)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            c = _corr(rets[a], rets[b])
            if c is not None:
                pairs.append({"a": a, "b": b, "correlation": round(c, 3)})
    thr = float((acfg.settings().get("allocator") or {}).get("correlation_threshold", 0.7))
    gap = []
    for e in live:
        vm = e.get("validated_metrics") or {}
        x = book.graded_returns(ledger, e["id"])
        gap.append({"engine": e["id"], "backtest_expectancy": vm.get("expectancy"),
                    "paper_expectancy": statistics.fmean(x) if x else None,
                    "paper_n": len(x),
                    "gap": (statistics.fmean(x) - vm["expectancy"])
                    if x and vm.get("expectancy") is not None else None})
    queue = [{"id": h["id"], "title": h["title"], "status": h["status"],
              "why": h.get("status_reason")}
             for h in hyp.Register(ledger).all(["needs_code", "data_gap"])]
    return {"as_of": as_of, "week_to": day, "window_weeks": AGENDA_WEEKS,
            "losses_by_regime": group("regime_key"),
            "losses_by_instrument": group("instrument"),
            "losses_by_day": group("day"),
            "screen_prints_without_a_position": unpositioned,
            "screen_source": "alpha/screen.py (altdata.move_screen is not built yet)",
            "engine_correlation": pairs, "crowding_threshold": thr,
            "crowded": [p for p in pairs if abs(p["correlation"]) >= thr],
            "backtest_to_paper_gap": gap, "research_queue": queue}


def render_agenda(a: dict) -> str:
    def pct(x):
        return "–" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x * 100:+.3f}%"
    out = [f"# Alpha Lab research agenda, week to {a['week_to']}", "",
           f"Written by the weekly loop at {a['as_of']} from alpha.db and the store. The "
           f"residuals of the last {a['window_weeks']} weeks, for the research sitting "
           f"and the Saturday brief: where the lab lost, what moved that it did not "
           f"trade, how crowded its engines are, how far paper is from the backtest, "
           f"and the queue of ideas waiting for code or data.", ""]
    for title, key, col in (("Losses by regime", "losses_by_regime", "regime_key"),
                            ("Losses by instrument", "losses_by_instrument", "instrument"),
                            ("Losses by day", "losses_by_day", "day")):
        out += [f"## {title}", ""]
        rows = a[key]
        if not rows:
            out += ["No losing trade graded in the window.", ""]
            continue
        out += [f"| {col} | n | net P&L (lab $) |", "|---|---:|---:|"]
        out += [f"| {str(r[col]).replace('|', chr(92) + '|')} | {r['n']} | {r['net_pnl']:,.2f} |"
                for r in rows] + [""]
    out += ["## The move screen's prints without a position", "",
            f"Source: {a['screen_source']}.", ""]
    if a["screen_prints_without_a_position"]:
        out += ["| Day | Symbol | Move | z |", "|---|---|---:|---:|"]
        out += [f"| {m['day']} | {m['symbol']} | {m['change_pct']:+.2f}% | {m['z']:+.1f} |"
                for m in a["screen_prints_without_a_position"]] + [""]
    else:
        out += ["None this week.", ""]
    out += ["## Crowding: the engines' pairwise correlation", ""]
    if a["engine_correlation"]:
        out += ["| Engine | Engine | Correlation |", "|---|---|---:|"]
        out += [f"| {p['a']} | {p['b']} | {p['correlation']:+.2f} |"
                for p in a["engine_correlation"]]
        out += ["", f"At or above {a['crowding_threshold']}: "
                    f"{len(a['crowded'])} pair(s), counted as one by the allocator.", ""]
    else:
        out += ["Fewer than two engines with ten common days.", ""]
    out += ["## Backtest to paper", ""]
    if a["backtest_to_paper_gap"]:
        out += ["| Engine | Backtest expectancy | Paper expectancy | Paper n | Gap |",
                "|---|---:|---:|---:|---:|"]
        out += [f"| {g['engine']} | {pct(g['backtest_expectancy'])} | "
                f"{pct(g['paper_expectancy'])} | {g['paper_n']} | {pct(g['gap'])} |"
                for g in a["backtest_to_paper_gap"]] + [""]
    else:
        out += ["No live engine.", ""]
    out += ["## The research queue", ""]
    if a["research_queue"]:
        out += ["| Id | Title | Status | Why |", "|---|---|---|---|"]
        out += [f"| {q['id']} | {q['title']} | {q['status']} | "
                f"{str(q['why'] or '').replace('|', '/')[:240]} |"
                for q in a["research_queue"]] + [""]
    else:
        out += ["Empty.", ""]
    return "\n".join(out)


def write_agenda(ledger: Ledger, store, as_of: str) -> dict:
    a = agenda(ledger, store, as_of)
    md = render_agenda(a)
    rd = files.root("research_dir")
    files.write_text(rd / "agenda.md", md)
    files.write_text(rd / "agenda.json", json.dumps(a, indent=1, sort_keys=True,
                                                    default=str))
    ob = files.write_text(files.root("outbox") / f"lab-agenda-{a['week_to']}.md", md)
    ledger.event(LOOP, "agenda_written", as_of, None,
                 after={"agenda": str(rd / "agenda.md"), "outbox": str(ob),
                        "losses": len(a["losses_by_day"]),
                        "unpositioned_prints": len(a["screen_prints_without_a_position"]),
                        "crowded": len(a["crowded"]),
                        "queue": len(a["research_queue"])})
    return {"agenda": str(rd / "agenda.md")}


# ---------------------------------------------------------------------------
# 5. The verdicts (X-2.11)
# ---------------------------------------------------------------------------
def verdicts(ledger: Ledger, as_of: str) -> dict:
    """lab-verdicts-YYYY-MM-DD.md into the outbox, for the sweep to copy up to
    Drive's lab-outbox, where the Saturday brief reads it."""
    from .. import outbox                                       # noqa: PLC0415
    path = outbox.write(ledger, as_of)
    ledger.event(LOOP, "verdicts_written", as_of, None, after={"path": path})
    return {"verdicts": path}


def run(as_of: Optional[str] = None, ledger_path=None, store_path=None,
        registry_path=None) -> dict:
    as_of = as_of or session.utc_iso(timespec="microseconds")
    out: dict = {}
    failures: list[str] = []
    with Ledger(ledger_path) as lg:
        try:
            st: Optional[ReadOnlyStore] = ReadOnlyStore(store_path)
        except Exception as exc:                              # noqa: BLE001
            st = None
            lg.event(LOOP, "failure", as_of, None,
                     after={"step": "open_store", "error": f"{type(exc).__name__}: {exc}"})
            failures.append("open_store")
        steps = []
        if st is not None:
            # X-3.7: the quarter just closed, reviewed once inside its window,
            # before this week's re-fits read the bounds it may set
            steps.append(("meta_loop", lambda: meta_loop(lg, st, as_of, registry_path)))
            steps.append(("walk_forward",
                          lambda: walk_forward(lg, st, as_of, registry_path)))
        steps += [("rebalance", lambda: rebalance(lg, as_of)),
                  ("agenda", lambda: write_agenda(lg, st, as_of)),
                  ("verdicts", lambda: verdicts(lg, as_of))]
        if st is not None:
            # X-3.5: last, so a capped search never delays the week's own steps
            steps.append(("search", lambda: search_mod.weekly(lg, st, as_of)))
        try:
            for name, fn in steps:
                try:
                    out.update(fn())
                except Exception as exc:                      # noqa: BLE001
                    log.exception("weekly: %s failed", name)
                    failures.append(name)
                    lg.event(LOOP, "failure", as_of, None,
                             after={"step": name, "error": f"{type(exc).__name__}: {exc}",
                                    "trace": traceback.format_exc()[-1500:]})
        finally:
            if st is not None:
                st.close()
        lg.event(LOOP, "run", as_of, None, after={**out, "failures": failures})
        return {**out, "failures": failures}


def _main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="The Alpha Lab's weekly loop")
    ap.add_argument("--as-of")
    ap.add_argument("--ledger")
    ap.add_argument("--store")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    out = run(a.as_of, a.ledger, a.store)
    print(f"alpha weekly {out.get('day', '')}: applied={out.get('applied')} "
          f"failures={out.get('failures')}")
    return 1 if out.get("failures") else 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
