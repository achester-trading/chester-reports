"""
The grammar search (X-3.5; the change order's section 5).

    python -m alpha.search plan                     # the candidate count, no test
    python -m alpha.search coverage [--as-of ISO]   # each variable's history (read-only)
    python -m alpha.search run [--as-of ISO]        # one capped step (box write)

"Engine components -- signal families x conditioning variables x horizons x
instruments x exits -- enumerated and tested with every candidate counted in
variant_counts; survivors written to the register as `systematic` hypotheses,
pre-registered by the search's own manifest before its first backtest."

THE FAMILY is config/alpha_search.yaml's `family`. Each candidate is a rule in the
grammar v1 (alpha/rules.py), backtested point in time and net of the cost model
by rules.backtest. A conditioning option is "none" or one value of one variable:
the dials and the volatility regime (the stored market-state object's dials,
read, never recomputed), positioning (the stored CFTC net's z) and the funding
regime (crypto Tranche A's calc.funding_agg). A conditioned candidate is its base
rule's trades taken in that state only, as the grammar's own conditioning split
reads them. A variable marked `pending` (the dealer regime) is skipped, with its
reason printed.

COVERAGE (ruling 5(a) of 19 Oct 2026). A conditioning variable joins a run only
if its point-in-time history starts at least `coverage.min_years_before_holdout`
(5) years before the holdout's first day. It is evaluated at the run's start,
before the manifest, which records each variable's first date and whether it
passed. A variable's history starts on the first day any of its values was
KNOWABLE: the earliest, over its stored rows, of the later of the row's observed
day and its available_at's ET date -- so a series backfilled today without its
vintages starts today, and a stored market-state object starts when it was
computed, not on the session it describes. A variable that fails is pending
with "history from <date>"; its options are not candidates, and N counts only
the candidates the run tests. A `pending` variable (the dealer regime, ruling
5(b)) is evaluated the same way for the record, from its declared `history`
series, and never joins this family.

THE ORDER OF A RUN, each step before the next:
  0. COVERAGE, as above: the variables that join, and so the candidate list.
  1. THE MANIFEST (alpha/manifest.py), written and hashed before the first
     backtest: the family and its sha256, the full candidate count, the split
     (the holdout's first day), the deflation and the survivor rule.
  2. THE COUNT: the family's variant count is raised by the whole candidate
     count, so every candidate is deflated by N >= the number tried.
  3. FORMATION: each candidate's walk-forward over the trades that enter and exit
     before the holdout, against the constitution's gate at that N. The holdout
     is not backtested.
  4. THE FREEZE: the formation survivors' list, written and hashed.
  5. THE HOLDOUT: only then is each frozen survivor backtested over the holdout,
     against the pre-registered holdout rule.
  6. THE REGISTER: the survivors of both, as `systematic` hypotheses of the
     search's channel, pre-registered at the manifest's instant. Nothing else is
     written outside the lab's files and alpha.db's loop events.

THE CAPS. A step stops after `caps.max_candidates_per_run` candidates or its
wall-clock budget, and the next step resumes from the progress file. A resumed
run refuses a family that no longer hashes to its manifest.

THE CADENCE (ruling 5(c) of 19 Oct 2026). While a run is unfinished, its next
step is the LAST step of the nightly loop (alpha/loops/nightly.py; Mon-Fri 17:40,
chester-alpha-nightly.timer), its wall clock capped so the unit ends inside its
20-minute timeout with 3 minutes spare: the budget is the unit's timeout less
the spare less what the unit has already spent (scripts/run_alpha_nightly.sh
exports CHESTER_UNIT_STARTED), at most `caps.max_wall_seconds` (600 s); under
`cadence.min_step_seconds` (120 s) the step is skipped and says why. A new run
begins only in the first week of a month, and only once the previous run is
complete. Every step -- the nightly one and `python -m alpha.search run` --
holds one lock (files.lock on search/.lock), so two steps never hold the search
at once. No new timer; the weekly loop no longer steps it.
"""

from __future__ import annotations

import argparse
import datetime as dt
import itertools
import json
import os
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Callable, Optional

import yaml

from altdata import session

from . import config as acfg
from . import files, intake, manifest, pit, rules
from . import hypotheses as hyp
from . import validate as av

CONFIG = acfg.REPO / "config" / "alpha_search.yaml"
SUBDIR = "search"
LOOP = "search"
FIT_ROWS, TEST_ROWS = 1, 10            # the workbench's, for a rule with nothing fitted
NONE = "none"
LOCK_NAME = ".lock"
_T0 = time.time()                      # the process's start, when the unit's is not exported


class FamilyChanged(ValueError):
    """The family no longer hashes to its run's manifest."""


def load_config(path: Optional[Path] = None) -> dict:
    return yaml.safe_load(Path(path or CONFIG).read_text(encoding="utf-8")) or {}


def spec_of(cfg: dict) -> dict:
    """What the manifest fixes: the family, the split, the deflation and the
    survivor rule, and the coverage rule that decides which variables join. The
    caps and the cadence are a run's limits, not the family."""
    return {k: cfg[k] for k in ("family", "split", "deflation", "survivor_rule",
                                "coverage") if k in cfg}


def family_sha256(cfg: dict) -> str:
    return manifest.batch_sha256(spec_of(cfg))


# ---------------------------------------------------------------------------
# The candidates
# ---------------------------------------------------------------------------
def variables(cfg: dict, joined: Optional[list[str]] = None) -> tuple[dict, dict]:
    """(active {name: spec}, pending {name: reason}). With `joined` (a run's
    coverage verdict), only those variables are active."""
    act, pend = {}, {}
    for name, v in (cfg["family"].get("conditioning") or {}).items():
        if v.get("pending"):
            pend[name] = str(v.get("reason") or "pending")
        elif joined is not None and name not in joined:
            pend[name] = "failed coverage"
        else:
            act[name] = v
    return act, pend


def options(cfg: dict, joined: Optional[list[str]] = None) -> list[Optional[tuple[str, str]]]:
    act, _ = variables(cfg, joined)
    return [None] + [(n, str(x)) for n, v in act.items() for x in v["values"]]


def cond_label(c: Optional[tuple[str, str]]) -> str:
    return NONE if c is None else f"{c[0]}={c[1]}"


def candidates(cfg: dict, joined: Optional[list[str]] = None) -> list[dict]:
    """Every candidate, in a fixed order: by base rule, then by conditioning.
    With `joined`, only the options of the variables that passed coverage."""
    f = cfg["family"]
    out = []
    for sig, h, sym, ex in itertools.product(sorted(f["signal_families"]),
                                             [int(x) for x in f["horizons"]],
                                             [str(s).upper() for s in f["instruments"]],
                                             sorted(f["exits"])):
        base = f"{sig}|h{h}|{sym}|{ex}"
        for c in options(cfg, joined):
            out.append({"id": f"{base}|{cond_label(c)}", "base": base, "signal": sig,
                        "horizon": h, "instrument": sym, "exit": ex, "cond": c})
    return out


def _fill(x: Any, sym: str) -> Any:
    if isinstance(x, str):
        return x.replace("{sym}", sym)
    if isinstance(x, list):
        return [_fill(v, sym) for v in x]
    if isinstance(x, dict):
        return {k: _fill(v, sym) for k, v in x.items()}
    return x


def base_rule(cfg: dict, cand: dict) -> dict:
    f = cfg["family"]
    sig = f["signal_families"][cand["signal"]]
    sym = cand["instrument"]
    return {"grammar": f["grammar"], "universe": [sym], "cadence": f["cadence"],
            "trigger": _fill(sig["trigger"], sym), "direction": sig["direction"],
            "instrument": sym, "entry": f["entry"],
            "exits": {"time": int(cand["horizon"]), **(f["exits"][cand["exit"]] or {})}}


def plan(cfg: dict, joined: Optional[list[str]] = None) -> dict:
    act, pend = variables(cfg, joined)
    f = cfg["family"]
    n_opt = len(options(cfg, joined))
    n = (len(f["signal_families"]) * n_opt * len(f["horizons"]) *
         len(f["instruments"]) * len(f["exits"]))
    return {"family": f["name"], "n_candidates": n, "signal_families": len(f["signal_families"]),
            "conditioning_options": n_opt, "horizons": len(f["horizons"]),
            "instruments": len(f["instruments"]), "exits": len(f["exits"]),
            "active": sorted(act), "pending": pend,
            "pending_lines": [f"{k}: skipped, pending -- {v}" for k, v in sorted(pend.items())]}


# ---------------------------------------------------------------------------
# Coverage (ruling 5(a)): which variables have the history to join a run
# ---------------------------------------------------------------------------
def history_series(v: dict) -> Optional[tuple[str, Optional[str]]]:
    """(store key, instrument) a variable's coverage is read from: the stored
    market-state object for a state variable, its own series for a z-score or a
    mean band, a pending variable's declared `history`."""
    if v.get("pending"):
        h = v.get("history") or {}
        return (str(h["key"]), h.get("instrument")) if h.get("key") else None
    if v.get("kind") == "state":
        return ("market_state", None)
    if v.get("key"):
        return (str(v["key"]), v.get("instrument"))
    return None


def history_from(store, key: str, instrument: Optional[str] = None) -> Optional[str]:
    """The first day any value of the series was knowable: the earliest, over
    its stored rows, of max(observed day, available_at's ET date)."""
    first = None
    for r in store.all_vintages(key, instrument):
        if r.get("value_num") is None and not r.get("value_text"):
            continue
        d = max(str(r["observed_at"])[:10], pit.et_date(str(r["available_at"])))
        if first is None or d < first:
            first = d
    return first


def years_before(day: str, years: int) -> str:
    d = dt.date.fromisoformat(day)
    try:
        return d.replace(year=d.year - int(years)).isoformat()
    except ValueError:                                        # 29 February
        return d.replace(year=d.year - int(years), day=28).isoformat()


def coverage(store, cfg: dict, hfrom: str) -> dict:
    """Each declared variable's history against the rule: {name: {key,
    instrument, first, required_by, passed, joined, line}}."""
    years = int((cfg.get("coverage") or {}).get("min_years_before_holdout", 5))
    need = years_before(hfrom, years)
    out = {}
    for name, v in (cfg["family"].get("conditioning") or {}).items():
        hs = history_series(v)
        first = history_from(store, *hs) if hs else None
        passed = first is not None and first <= need
        joined = passed and not v.get("pending")
        hist = f"history from {first}" if first else "no history stored"
        if v.get("pending"):
            line = f"{name}: pending -- {hist} (needs {need}); {v.get('reason') or 'pending'}"
        elif joined:
            line = f"{name}: joined -- {hist} (needs {need})"
        else:
            line = f"{name}: pending -- {hist} (needs {need})"
        out[name] = {"key": hs[0] if hs else None, "instrument": hs[1] if hs else None,
                     "first": first, "required_by": need, "passed": passed,
                     "joined": joined, "line": line}
    return out


def coverage_lines(cov: dict) -> list[str]:
    """Joined first, then pending, each by name."""
    return [cov[n]["line"] for n in sorted(cov, key=lambda n: (not cov[n]["joined"], n))]


# ---------------------------------------------------------------------------
# The conditioning variables, point in time
# ---------------------------------------------------------------------------
class Conditions:
    """Each active variable's value at a trade's decision, read as knowable then."""

    def __init__(self, store, cfg: dict, data: Optional[rules.Data] = None,
                 joined: Optional[list[str]] = None) -> None:
        self.store, self.data = store, data or rules.Data(store)
        self.act, _ = variables(cfg, joined)
        self._s: dict[tuple, pit.Series] = {}

    def _series(self, key: str, inst: Optional[str]) -> pit.Series:
        if (key, inst) not in self._s:
            self._s[(key, inst)] = pit.Series(self.store, key, inst)
        return self._s[(key, inst)]

    def value(self, name: str, day: str, t: str) -> Optional[str]:
        v = self.act[name]
        if v["kind"] == "state":
            return self.data.state(day, t, v["path"])
        xs = [x for d, x in self._series(v["key"], v.get("instrument")).known(t)
              if d <= day]
        if v["kind"] == "zscore":
            xs = xs[-int(v["window"]):]
            if len(xs) < int(v.get("min_rows") or v["window"]):
                return None
            sd = statistics.stdev(xs)
            if not sd:
                return None
            z = (xs[-1] - statistics.fmean(xs)) / sd
            b = v["bands"]
            return ("crowded_long" if z >= float(b["crowded_long"]) else
                    "crowded_short" if z <= float(b["crowded_short"]) else "neutral")
        if v["kind"] == "mean_band":
            xs = xs[-int(v["window"]):]
            if len(xs) < int(v["window"]):
                return None
            m = statistics.fmean(xs)
            b = v["bands"]
            return "on" if m >= float(b["on"]) else ("off" if m < float(b["off"])
                                                       else "between")
        raise ValueError(f"conditioning kind {v['kind']!r}")

    def of(self, trade: dict) -> dict:
        return {n: self.value(n, trade["signal_day"], trade["decided_at"]) for n in self.act}


# ---------------------------------------------------------------------------
# The run's files
# ---------------------------------------------------------------------------
def run_id(cfg: dict, as_of: str) -> str:
    return f"{cfg['family']['name']}-{pit.et_date(as_of)[:7]}"


def holdout_from(as_of: str, months: int) -> str:
    """The first day of the month `months` whole months before the run's month."""
    d = dt.date.fromisoformat(pit.et_date(as_of)[:7] + "-01")
    y, m = d.year, d.month - int(months)
    while m <= 0:
        y, m = y - 1, m + 12
    return f"{y:04d}-{m:02d}-01"


def _dir(rid: str) -> Path:
    return files.root("research_dir") / SUBDIR / rid


def progress_path(rid: str) -> Path:
    return _dir(rid) / "progress.json"


def load_progress(rid: str) -> Optional[dict]:
    p = progress_path(rid)
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None


def save_progress(st: dict) -> None:
    files.write_text(progress_path(st["run_id"]),
                     json.dumps(st, indent=1, sort_keys=True, default=str) + "\n")


def lock_path() -> Path:
    return files.root("research_dir") / SUBDIR / LOCK_NAME


def unfinished(cfg: dict) -> Optional[dict]:
    """The newest run of this family not yet done, if any."""
    root = files.root("research_dir") / SUBDIR
    if not root.is_dir():
        return None
    for p in sorted(root.glob(f"{cfg['family']['name']}-*/progress.json"), reverse=True):
        st = json.loads(p.read_text(encoding="utf-8"))
        if st.get("stage") != "done":
            return st
    return None


def start(ledger, store, cfg: dict, as_of: str) -> dict:
    """Steps 0 to 2: coverage, the manifest, then the count. Nothing is
    backtested."""
    rid = run_id(cfg, as_of)
    if load_progress(rid):
        raise FileExistsError(f"search run {rid} already exists; it is resumed, never "
                              f"restarted")
    hfrom = holdout_from(as_of, int(cfg["split"]["holdout_months"]))
    cov = coverage(store, cfg, hfrom)
    joined = sorted(n for n, c in cov.items() if c["joined"])
    cands = candidates(cfg, joined)
    doc = {"batch_id": rid, "kind": "grammar-search", "family_sha256": family_sha256(cfg),
           "spec": spec_of(cfg), "coverage": cov, "joined": joined,
           "n_candidates": len(cands), "holdout_from": hfrom,
           "candidates": [c["id"] for c in cands], "hypotheses": []}
    m = manifest.write(doc, as_of)
    n_trials = ledger.bump_variant(cfg["family"]["name"], as_of, by=len(cands))
    st = {"run_id": rid, "family": cfg["family"]["name"], "manifest": m["name"],
          "manifest_sha256": m["sha256"], "manifest_at": m["written_at"],
          "family_sha256": doc["family_sha256"], "n_candidates": len(cands),
          "holdout_from": hfrom, "n_trials": n_trials, "stage": "formation",
          "coverage": cov, "joined": joined, "done": {}, "survivors": [], "frozen_sha256": None, "holdout": {},
          "registered": {}, "started_at": as_of}
    save_progress(st)
    ledger.event(LOOP, "search_start", as_of, None,
                 after={k: st[k] for k in ("run_id", "n_candidates", "n_trials",
                                           "holdout_from", "manifest_sha256", "joined")})
    return st


def check_family(cfg: dict, st: dict) -> None:
    have = family_sha256(cfg)
    doc = manifest.read(st["manifest"])
    on_file = (doc or {}).get("batch", {}).get("family_sha256")
    if doc is None or doc.get("batch_sha256") != st["manifest_sha256"]:
        raise FamilyChanged(f"run {st['run_id']}: its manifest {st['manifest']} is "
                            f"missing or no longer hashes to what the run recorded")
    if have != on_file:
        raise FamilyChanged(f"run {st['run_id']}: the family hashes to {have}, not the "
                            f"{on_file} its manifest fixed -- a changed family is a new "
                            f"search, never a resumed one")


# ---------------------------------------------------------------------------
# Formation, the freeze, the holdout, the register
# ---------------------------------------------------------------------------
def _strategy(family: str, horizon: str) -> av.Strategy:
    return av.Strategy(family=family, horizon=horizon, fit=lambda rows: {},
                       returns=lambda rows, p: [float(r["net"]) for r in rows])


def _rows(trades: list[dict]) -> list[dict]:
    return [{"day": t["signal_day"], "decided_at": t["decided_at"],
             "available_at": t["available_at"], "net": t["net"]} for t in trades]


def taken(trades: list[dict], conds: list[dict], c: Optional[tuple[str, str]]) -> list[dict]:
    if c is None:
        return list(trades)
    return [t for t, v in zip(trades, conds) if v.get(c[0]) == c[1]]


def formation_verdict(trades: list[dict], horizon: str, n_trials: int,
                      family: str) -> dict:
    con = acfg.constitution()
    need = acfg.min_signals(horizon, con)
    floor = float(con["validation"]["deflated_sharpe_min"])
    if not trades:
        return {"passed": False, "n": 0, "n_trials": n_trials,
                "why": "no trades in formation"}
    wf = av.walk_forward(_rows(trades), _strategy(family, horizon), FIT_ROWS, TEST_ROWS, con)
    ppy = av.signal_rate(wf["test_days"], len(wf["oos"]),
                         acfg.periods_per_year(horizon, acfg.settings()))
    ds = av.deflated_sharpe(wf["oos"], n_trials, ppy)
    why = []
    if ds["n"] < need:
        why.append(f"sample {ds['n']} < min_signals {need}")
    if ds["mean"] <= 0:
        why.append("expectancy after costs <= 0")
    if ds["deflated_sharpe"] < floor:
        why.append(f"deflated Sharpe {ds['deflated_sharpe']:.2f} < {floor}")
    return {"passed": not why, "n": ds["n"], "expectancy": ds["mean"],
            "deflated_sharpe": ds["deflated_sharpe"], "sr0": ds["sr0"],
            "n_trials": n_trials, "why": "; ".join(why) or "passed"}


def holdout_verdict(trades: list[dict], cfg: dict) -> dict:
    k = int(cfg["survivor_rule"]["min_holdout_trades"])
    x = [float(t["net"]) for t in trades]
    m = statistics.fmean(x) if x else None
    ok = len(x) >= k and m is not None and m > 0
    return {"passed": ok, "n": len(x), "mean_net": m,
            "why": ("passed" if ok else
                    f"{len(x)} holdout trades (need {k})" if len(x) < k else
                    "holdout mean net of costs <= 0")}


def _first_day(data: rules.Data, sym: str) -> str:
    ds = data.series(rules.resolve(sym)).days
    return ds[0] if ds else "1990-01-02"


def freeze(st: dict) -> None:
    surv = sorted(c for c, r in st["done"].items() if r.get("passed"))
    st["survivors"] = surv
    st["frozen_sha256"] = manifest.batch_sha256({"run_id": st["run_id"], "survivors": surv})
    files.write_text(_dir(st["run_id"]) / "survivors.json",
                     json.dumps({"run_id": st["run_id"], "survivors": surv,
                                 "sha256": st["frozen_sha256"]}, indent=1) + "\n")
    st["stage"] = "frozen"


def hypothesis_of(cfg: dict, cand: dict, fr: dict, ho: dict) -> dict:
    dsl = base_rule(cfg, cand)
    c = cand["cond"]
    sig = cfg["family"]["signal_families"][cand["signal"]]
    h = {"local_id": cand["id"].replace("|", "_").replace("=", "-"),
         "title": f"Search {cfg['family']['name']}: {cand['signal']} on {cand['instrument']}, "
                  f"{cand['horizon']} sessions, {cand['exit']}, {cond_label(c)}",
         "horizon_class": "short" if cand["horizon"] <= 10 else "medium",
         "horizon_sessions": int(cand["horizon"]), "family": cfg["family"]["name"],
         "mechanism": (f"A survivor of the grammar search {cfg['family']['name']} "
                       f"(X-3.5): found by enumeration, not by an argument. It passed "
                       f"the deflated gate in formation at N={fr['n_trials']} and the "
                       f"pre-registered holdout test ({ho['n']} trades, mean net "
                       f"{ho['mean_net']:+.5f}). Its mechanism is for the research "
                       f"sitting to state or refute."),
         "universe": [cand["instrument"]],
         "rule_text": (f"{json.dumps(dsl, sort_keys=True)}; taken only when "
                       f"{cond_label(c)}" if c else json.dumps(dsl, sort_keys=True)),
         "conditioning": ([] if c is None else
                          [{"name": c[0], "value": c[1],
                            "what": cfg["family"]["conditioning"][c[0]]["what"]}]),
         "expected": {"sign": "positive_expectancy_after_costs"},
         "sample": {"formation_n": fr["n"], "holdout_n": ho["n"]},
         "data": {"search_run": cand["id"], "direction": sig["direction"]},
         "needs_code": c is not None, "kill": "constitution",
         "state_at_registration": "a search survivor; pre-registered by the search's "
                                  "manifest before its first backtest"}
    if c is None:
        h["rule_dsl"] = dsl
    return h


def register_survivors(ledger, store, cfg: dict, st: dict, as_of: str) -> dict:
    by = {c["id"]: c for c in candidates(cfg, st.get("joined"))}
    hyps =[hypothesis_of(cfg, by[cid], st["done"][cid], st["holdout"][cid])
            for cid in st["survivors"] if st["holdout"].get(cid, {}).get("passed")]
    if not hyps:
        return {"registered": {}, "statuses": {}}
    doc = {"schema": hyp.SCHEMA_ID, "batch_id": st["run_id"], "source": "systematic",
           "proposer": "alpha/search.py", "channel": "search",
           "written_at": st["manifest_at"], "model_idea_rule": False,
           "inputs": [f"config/alpha_search.yaml family {st['family']} "
                      f"(sha256 {st['family_sha256']})",
                      f"manifest {st['manifest']}"], "hypotheses": hyps}
    errs = hyp.validate_batch(doc)
    if errs:
        raise ValueError("the survivors' batch fails the v1 schema: " + "; ".join(errs[:6]))
    return intake.admit(ledger, store, doc, st["manifest_at"], as_of,
                        file_name=st["manifest"], file_sha256=st["manifest_sha256"],
                        created_time=st["manifest_at"])


def step(ledger, store, as_of: str, cfg: Optional[dict] = None,
         clock: Callable[[], float] = time.monotonic,
         max_candidates: Optional[int] = None, max_wall: Optional[float] = None,
         begin: bool = True) -> dict:
    """One capped step of the current run: start it (when `begin`), or resume.
    Every step holds the search's one lock; a second step while one holds it
    does nothing and says so."""
    cfg = cfg or load_config()
    with files.lock(lock_path()) as held:
        if not held:
            why = "another search step holds the lock"
            ledger.event(LOOP, "search_skipped", as_of, None, after={"why": why})
            return {"search": None, "search_skipped": why}
        return _step(ledger, store, as_of, cfg, clock, max_candidates, max_wall, begin)


def _step(ledger, store, as_of: str, cfg: dict, clock: Callable[[], float],
          max_candidates: Optional[int], max_wall: Optional[float], begin: bool) -> dict:
    st = load_progress(run_id(cfg, as_of))
    if st is None or st.get("stage") == "done":
        st = unfinished(cfg) or st
    if st is None:
        if not begin:
            return {"search": None}
        st = start(ledger, store, cfg, as_of)
    if st["stage"] == "done":
        return {"search": summary(cfg, st, None)}
    check_family(cfg, st)
    joined = st.get("joined")
    caps = cfg.get("caps") or {}
    cap_n = int(max_candidates if max_candidates is not None
                else caps.get("max_candidates_per_run", 400))
    cap_s = float(max_wall if max_wall is not None else caps.get("max_wall_seconds", 600))
    t0 = clock()
    tested, stopped = 0, None
    data = rules.Data(store)
    conds = Conditions(store, cfg, data, joined)
    last_f = pit.prev_session(st["holdout_from"])
    if st["stage"] == "formation":
        todo: dict[str, list[dict]] = {}
        for c in candidates(cfg, joined):
            if c["id"] not in st["done"]:
                todo.setdefault(c["base"], []).append(c)
        for base, cs in todo.items():
            if tested >= cap_n:
                stopped = "candidates"
                break
            if clock() - t0 >= cap_s:
                stopped = "wall_clock"
                break
            cs = cs[:cap_n - tested]
            cmp = rules.compile_rule(base_rule(cfg, cs[0]))
            first = _first_day(data, cs[0]["instrument"])
            trades = rules.backtest(cmp, store, first, last_f, data=data)["trades"] \
                if first <= last_f else []
            trades = [t for t in trades if t["exit_day"] < st["holdout_from"]]
            cv = [conds.of(t) for t in trades]
            for c in cs:
                st["done"][c["id"]] = formation_verdict(taken(trades, cv, c["cond"]),
                                                        cmp.horizon, st["n_trials"],
                                                        st["family"])
                tested += 1
            save_progress(st)
        if stopped is None and len(st["done"]) >= st["n_candidates"]:
            freeze(st)
            save_progress(st)
    if st["stage"] == "frozen":
        # the holdout, touched only now that the survivor list is frozen
        by = {c["id"]: c for c in candidates(cfg, joined)}
        last = session.session_date(as_of)
        for cid in st["survivors"]:
            if cid in st["holdout"]:
                continue
            c = by[cid]
            cmp = rules.compile_rule(base_rule(cfg, c))
            trades = rules.backtest(cmp, store, st["holdout_from"], last, data=data)["trades"]
            trades = [t for t in trades if t["signal_day"] >= st["holdout_from"]]
            st["holdout"][cid] = holdout_verdict(taken(trades, [conds.of(t) for t in trades],
                                                       c["cond"]), cfg)
        out = register_survivors(ledger, store, cfg, st, as_of)
        st["registered"] = out.get("registered") or {}
        st["stage"] = "done"
        st["finished_at"] = as_of
        save_progress(st)
    s = summary(cfg, st, stopped, tested)
    ledger.event(LOOP, "search_progress", as_of, None, after=s)
    return {"search": s}


def summary(cfg: dict, st: dict, stopped: Optional[str], tested: int = 0) -> dict:
    p = plan(cfg, st.get("joined"))
    done = len(st["done"])
    held = sum(1 for v in st["holdout"].values() if v.get("passed"))
    passed = sum(1 for v in st["done"].values() if v.get("passed"))
    line = (f"grammar search {st['run_id']}: {done} of {st['n_candidates']} candidates "
            f"tested; {passed} passed the deflated gate in formation"
            + (f", {held} the holdout, {len(st['registered'])} registered"
               if st["stage"] == "done" else "")
            + f"; deflated by N={st['n_trials']} (family {st['family']})")
    if stopped:
        line += (f"; stopped at the {'candidate' if stopped == 'candidates' else 'wall-clock'}"
                 f" cap, resumes at the next nightly loop")
    cov = st.get("coverage") or {}
    return {"run_id": st["run_id"], "stage": st["stage"], "tested": done,
            "tested_this_step": tested, "n_candidates": st["n_candidates"],
            "n_trials": st["n_trials"], "survivors_formation": passed,
            "survivors_holdout": held, "registered": len(st["registered"]),
            "stopped": stopped, "joined": list(st.get("joined") or []),
            "coverage": coverage_lines(cov) if cov else [],
            "pending": [] if cov else p["pending_lines"], "line": line}


# ---------------------------------------------------------------------------
# The cadence (ruling 5(c)): the nightly loop's last step
# ---------------------------------------------------------------------------
def step_budget(cfg: dict, now: Optional[float] = None,
                started: Optional[float] = None) -> float:
    """Seconds this step may run: the unit's timeout, less the spare, less what
    the unit has spent already, at most the step's own cap."""
    cad = cfg.get("cadence") or {}
    if started is None:
        env = os.environ.get("CHESTER_UNIT_STARTED", "")
        try:
            started = float(env) if env else _T0
        except ValueError:
            started = _T0
    spent = max(0.0, (time.time() if now is None else now) - started)
    left = (float(cad.get("unit_timeout_seconds", 1200))
            - float(cad.get("spare_seconds", 180)) - spent)
    return min(float((cfg.get("caps") or {}).get("max_wall_seconds", 600)), left)


def can_begin(cfg: dict, as_of: str) -> tuple[bool, str]:
    """A new run begins only in a month's first week, and only once the previous
    run is complete."""
    if unfinished(cfg) is not None:
        return False, "a run is unfinished; it is resumed, and no new run begins"
    if int(pit.et_date(as_of)[8:10]) > int((cfg.get("cadence") or {})
                                           .get("begin_by_day", 7)):
        return False, "a new run begins only in the first week of a month"
    return True, ""


def nightly(ledger, store, as_of: str, cfg: Optional[dict] = None,
            budget: Optional[float] = None,
            clock: Callable[[], float] = time.monotonic) -> dict:
    """The nightly loop's last step: resume an unfinished run, or begin one in a
    month's first week, inside the unit's budget; under the minimum, skip and
    say why."""
    cfg = cfg or load_config()
    have = unfinished(cfg)
    if have is None:
        ok, why = can_begin(cfg, as_of)
        mine = load_progress(run_id(cfg, as_of))
        if not ok or (mine is not None and mine.get("stage") == "done"):
            return {"search": None}
    b = step_budget(cfg) if budget is None else float(budget)
    floor = float((cfg.get("cadence") or {}).get("min_step_seconds", 120))
    if b < floor:
        why = (f"search step skipped: {max(b, 0.0):.0f} s left of the unit's budget "
               f"(timeout less {int((cfg.get('cadence') or {}).get('spare_seconds', 180))}"
               f" s spare), under the {floor:.0f} s minimum")
        print(why)
        ledger.event(LOOP, "search_skipped", as_of, None, after={"why": why, "budget": b})
        return {"search": None, "search_skipped": why}
    return step(ledger, store, as_of, cfg, clock=clock, max_wall=b,
                begin=have is None)


def _main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="python -m alpha.search")
    ap.add_argument("--store")
    ap.add_argument("--ledger")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("plan", help="the candidate count and the pending variables")
    cv = sub.add_parser("coverage", help="each variable's history against the rule "
                                         "(read-only; writes nothing)")
    cv.add_argument("--as-of")
    r = sub.add_parser("run", help="one capped step of the current run (box write)")
    r.add_argument("--as-of")
    r.add_argument("--max-candidates", type=int)
    r.add_argument("--max-seconds", type=float)
    a = ap.parse_args(argv)
    cfg = load_config()
    if a.cmd == "plan":
        p = plan(cfg)
        print(f"family {p['family']} (sha256 {family_sha256(cfg)}): at most "
              f"{p['n_candidates']} candidates = {p['signal_families']} signal families x "
              f"{p['conditioning_options']} conditioning options x {p['horizons']} horizons "
              f"x {p['instruments']} instruments x {p['exits']} exits; a run tests only "
              f"the options of the variables that pass coverage at its start")
        for ln in p["pending_lines"]:
            print("  " + ln)
        return 0
    from .store import ReadOnlyStore                            # noqa: PLC0415
    as_of = a.as_of or session.utc_iso(timespec="microseconds")
    if a.cmd == "coverage":
        st = ReadOnlyStore(a.store)
        try:
            hfrom = holdout_from(as_of, int(cfg["split"]["holdout_months"]))
            cov = coverage(st, cfg, hfrom)
        finally:
            st.close()
        joined = sorted(n for n, c in cov.items() if c["joined"])
        print(f"holdout from {hfrom}; a run starting now would test "
              f"{len(candidates(cfg, joined))} candidates")
        for ln in coverage_lines(cov):
            print("  " + ln)
        return 0
    from .ledger import Ledger                                  # noqa: PLC0415
    with Ledger(a.ledger) as lg:
        st = ReadOnlyStore(a.store)
        try:
            ok, why = can_begin(cfg, as_of)
            if not ok and unfinished(cfg) is None:
                print(f"no search run: {why}")
            out = step(lg, st, as_of, cfg, max_candidates=a.max_candidates,
                       max_wall=a.max_seconds, begin=ok)
        finally:
            st.close()
    print(out["search"]["line"] if out.get("search")
          else out.get("search_skipped") or "no search run")
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
