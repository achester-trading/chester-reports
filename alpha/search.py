"""
The grammar search (X-3.5; the change order's section 5).

    python -m alpha.search plan                     # the candidate count, no test
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

THE ORDER OF A RUN, each step before the next:
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

THE CAPS. A step stops after `caps.max_candidates_per_run` candidates or
`caps.max_wall_seconds`, and the next step resumes from the progress file. A
resumed run refuses a family that no longer hashes to its manifest. The weekly
loop begins a run in the first week of each month and resumes an unfinished one
on any week (alpha/loops/weekly.py), so its line lands in the Monthly's Lab
report. No new timer.
"""

from __future__ import annotations

import argparse
import datetime as dt
import itertools
import json
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


class FamilyChanged(ValueError):
    """The family no longer hashes to its run's manifest."""


def load_config(path: Optional[Path] = None) -> dict:
    return yaml.safe_load(Path(path or CONFIG).read_text(encoding="utf-8")) or {}


def spec_of(cfg: dict) -> dict:
    """What the manifest fixes: the family, the split, the deflation and the
    survivor rule. The caps are a run's limits, not the family."""
    return {k: cfg[k] for k in ("family", "split", "deflation", "survivor_rule")}


def family_sha256(cfg: dict) -> str:
    return manifest.batch_sha256(spec_of(cfg))


# ---------------------------------------------------------------------------
# The candidates
# ---------------------------------------------------------------------------
def variables(cfg: dict) -> tuple[dict, dict]:
    """(active {name: spec}, pending {name: reason})."""
    act, pend = {}, {}
    for name, v in (cfg["family"].get("conditioning") or {}).items():
        if v.get("pending"):
            pend[name] = str(v.get("reason") or "pending")
        else:
            act[name] = v
    return act, pend


def options(cfg: dict) -> list[Optional[tuple[str, str]]]:
    act, _ = variables(cfg)
    return [None] + [(n, str(x)) for n, v in act.items() for x in v["values"]]


def cond_label(c: Optional[tuple[str, str]]) -> str:
    return NONE if c is None else f"{c[0]}={c[1]}"


def candidates(cfg: dict) -> list[dict]:
    """Every candidate, in a fixed order: by base rule, then by conditioning."""
    f = cfg["family"]
    out = []
    for sig, h, sym, ex in itertools.product(sorted(f["signal_families"]),
                                             [int(x) for x in f["horizons"]],
                                             [str(s).upper() for s in f["instruments"]],
                                             sorted(f["exits"])):
        base = f"{sig}|h{h}|{sym}|{ex}"
        for c in options(cfg):
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


def plan(cfg: dict) -> dict:
    act, pend = variables(cfg)
    f = cfg["family"]
    n_opt = len(options(cfg))
    n = (len(f["signal_families"]) * n_opt * len(f["horizons"]) *
         len(f["instruments"]) * len(f["exits"]))
    return {"family": f["name"], "n_candidates": n, "signal_families": len(f["signal_families"]),
            "conditioning_options": n_opt, "horizons": len(f["horizons"]),
            "instruments": len(f["instruments"]), "exits": len(f["exits"]),
            "active": sorted(act), "pending": pend,
            "pending_lines": [f"{k}: skipped, pending -- {v}" for k, v in sorted(pend.items())]}


# ---------------------------------------------------------------------------
# The conditioning variables, point in time
# ---------------------------------------------------------------------------
class Conditions:
    """Each active variable's value at a trade's decision, read as knowable then."""

    def __init__(self, store, cfg: dict, data: Optional[rules.Data] = None) -> None:
        self.store, self.data = store, data or rules.Data(store)
        self.act, _ = variables(cfg)
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


def start(ledger, cfg: dict, as_of: str) -> dict:
    """Steps 1 and 2: the manifest, then the count. Nothing is backtested."""
    rid = run_id(cfg, as_of)
    if load_progress(rid):
        raise FileExistsError(f"search run {rid} already exists; it is resumed, never "
                              f"restarted")
    cands = candidates(cfg)
    hfrom = holdout_from(as_of, int(cfg["split"]["holdout_months"]))
    doc = {"batch_id": rid, "kind": "grammar-search", "family_sha256": family_sha256(cfg),
           "spec": spec_of(cfg), "n_candidates": len(cands), "holdout_from": hfrom,
           "candidates": [c["id"] for c in cands], "hypotheses": []}
    m = manifest.write(doc, as_of)
    n_trials = ledger.bump_variant(cfg["family"]["name"], as_of, by=len(cands))
    st = {"run_id": rid, "family": cfg["family"]["name"], "manifest": m["name"],
          "manifest_sha256": m["sha256"], "manifest_at": m["written_at"],
          "family_sha256": doc["family_sha256"], "n_candidates": len(cands),
          "holdout_from": hfrom, "n_trials": n_trials, "stage": "formation",
          "done": {}, "survivors": [], "frozen_sha256": None, "holdout": {},
          "registered": {}, "started_at": as_of}
    save_progress(st)
    ledger.event(LOOP, "search_start", as_of, None,
                 after={k: st[k] for k in ("run_id", "n_candidates", "n_trials",
                                           "holdout_from", "manifest_sha256")})
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
    by = {c["id"]: c for c in candidates(cfg)}
    hyps = [hypothesis_of(cfg, by[cid], st["done"][cid], st["holdout"][cid])
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
    """One capped step of the current run: start it (when `begin`), or resume."""
    cfg = cfg or load_config()
    st = load_progress(run_id(cfg, as_of)) or unfinished(cfg)
    if st is None:
        if not begin:
            return {"search": None}
        st = start(ledger, cfg, as_of)
    if st["stage"] == "done":
        return {"search": summary(cfg, st, None)}
    check_family(cfg, st)
    caps = cfg.get("caps") or {}
    cap_n = int(max_candidates if max_candidates is not None
                else caps.get("max_candidates_per_run", 400))
    cap_s = float(max_wall if max_wall is not None else caps.get("max_wall_seconds", 600))
    t0 = clock()
    tested, stopped = 0, None
    data = rules.Data(store)
    conds = Conditions(store, cfg, data)
    last_f = pit.prev_session(st["holdout_from"])
    if st["stage"] == "formation":
        todo: dict[str, list[dict]] = {}
        for c in candidates(cfg):
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
        by = {c["id"]: c for c in candidates(cfg)}
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
    p = plan(cfg)
    done = len(st["done"])
    held = sum(1 for v in st["holdout"].values() if v.get("passed"))
    passed = sum(1 for v in st["done"].values() if v.get("passed"))
    line = (f"grammar search {st['run_id']}: {done} of {st['n_candidates']} candidates "
            f"tested; {passed} passed the deflated gate in formation"
            + (f", {held} the holdout, {len(st['registered'])} registered"
               if st["stage"] == "done" else "")
            + f"; deflated by N={st['n_trials']} (family {st['family']})")
    if stopped:
        line += f"; stopped at the {'candidate' if stopped == 'candidates' else 'wall-clock'} cap, resumes next week"
    return {"run_id": st["run_id"], "stage": st["stage"], "tested": done,
            "tested_this_step": tested, "n_candidates": st["n_candidates"],
            "n_trials": st["n_trials"], "survivors_formation": passed,
            "survivors_holdout": held, "registered": len(st["registered"]),
            "stopped": stopped, "pending": p["pending_lines"], "line": line}


def weekly(ledger, store, as_of: str, cfg: Optional[dict] = None) -> dict:
    """The weekly loop's step: begin a run in the first week of a month, else
    resume an unfinished one, else nothing."""
    cfg = cfg or load_config()
    first_week = int(pit.et_date(as_of)[8:10]) <= 7
    have = load_progress(run_id(cfg, as_of)) or unfinished(cfg)
    if have is None and not first_week:
        return {"search": None}
    return step(ledger, store, as_of, cfg, begin=first_week)


def _main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="python -m alpha.search")
    ap.add_argument("--store")
    ap.add_argument("--ledger")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("plan", help="the candidate count and the pending variables")
    r = sub.add_parser("run", help="one capped step of the current run (box write)")
    r.add_argument("--as-of")
    r.add_argument("--max-candidates", type=int)
    r.add_argument("--max-seconds", type=float)
    a = ap.parse_args(argv)
    cfg = load_config()
    if a.cmd == "plan":
        p = plan(cfg)
        print(f"family {p['family']} (sha256 {family_sha256(cfg)}): {p['n_candidates']} "
              f"candidates = {p['signal_families']} signal families x "
              f"{p['conditioning_options']} conditioning options x {p['horizons']} horizons "
              f"x {p['instruments']} instruments x {p['exits']} exits")
        for ln in p["pending_lines"]:
            print("  " + ln)
        return 0
    from .ledger import Ledger                                  # noqa: PLC0415
    from .store import ReadOnlyStore                            # noqa: PLC0415
    as_of = a.as_of or session.utc_iso(timespec="microseconds")
    with Ledger(a.ledger) as lg:
        st = ReadOnlyStore(a.store)
        try:
            out = step(lg, st, as_of, cfg, max_candidates=a.max_candidates,
                       max_wall=a.max_seconds)
        finally:
            st.close()
    print(out["search"]["line"] if out.get("search") else "no search run")
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
