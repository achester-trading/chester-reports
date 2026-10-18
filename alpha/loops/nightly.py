"""
The nightly loop -- learn from the ledger (X-1.9; the brief's section 8, loop 1).

    python -m alpha.loops.nightly [--as-of ISO] [--store PATH] [--ledger PATH]

Weekdays after the daily close's capture (chester-alpha-nightly.timer, 17:40
ET), in order, each step its own try so one failure costs that step only:

  1. the hold-out months recorded, the registry's engines entered as candidates;
     then the INBOX (X-2.11): each new batch file ingested into the register,
     pre-registered at its manifest's created time, or refused with the reason;
     then THE HARNESS (X-2.9): each registered hypothesis through X-1.6, capped
     a night, and each model idea waiting on its post-cutoff screen again;
  2. PAPER: pending signals filled at the next stored bar's open (or a stored
     quote), open positions' exits walked bar by bar, closed ones graded; then
     the CARRY rows (X-3.2): each live carry engine's two-leg positions opened,
     accrued and closed in carry_book;
  3. MARK every open position at the latest stored close;
  4. the GOVERNOR: each engine's equity and the lab's, the three thresholds;
  5. the POSTERIORS: Beta-binomial on the win rate, normal-normal on the
     expectancy, both shrunk toward zero with the session-set strength
     (config/alpha.yaml shrinkage.prior_signals), recorded on every row;
  6. the KILL RULE, after an engine's min_signals graded signals;
  7. COST CALIBRATION: modelled against the stored quotes' spreads;
  8. ALLOCATOR WEIGHTS proposed from the posteriors and the realised covariance
     (the weekly loop applies them);
  9. ATTRIBUTION of the day's P&L by regime key (the stored dials' states, the
     volatility regime, the dealer regime, event days);
 10. the DRIFT CHECK against each engine's validated metrics;
 11. tonight's SIGNALS from the live engines, queued for tomorrow's fills;
 12. PROMOTION (X-2.6): each passed grammar hypothesis written to engines at
     min_size, trading from the next loop.

Every change is a loop_events row. This loop changes sizes and weights; it never
changes an engine's rules. It reads the store read-only, writes alpha.db only,
never runs inside a report's run, and a failure is written to loop_events and
touches nothing else.
"""

from __future__ import annotations

import argparse
import logging
import math
import sys
import traceback
from typing import Optional

from altdata import session

from .. import allocate, book, blocklist, governor
from .. import config as acfg
from .. import engine as engine_mod
from ..costs import CostModel
from ..ledger import LAB, Ledger
from ..paper import Paper
from ..store import ReadOnlyStore
from ..validate import holdout_months

log = logging.getLogger(__name__)
LOOP = "nightly"
HISTORY_START = "2000-01"


class Run:
    def __init__(self, ledger: Ledger, store: ReadOnlyStore, as_of: str,
                 registry_path=None, con: Optional[dict] = None,
                 cfg: Optional[dict] = None) -> None:
        self.ledger, self.store, self.as_of = ledger, store, as_of
        self.day = session.session_date(as_of)
        self.con = con or acfg.constitution()
        self.cfg = cfg or acfg.settings()
        self.registry_path = registry_path
        self.costs = CostModel()
        self.paper = Paper(ledger, store, self.costs)
        self.engines: dict[str, engine_mod.Engine] = {}
        self.failures: list[str] = []
        self.summary: dict = {"day": self.day, "as_of": as_of}

    # -- the steps ----------------------------------------------------------
    def step(self, name: str, fn) -> None:
        try:
            fn()
        except Exception as exc:                              # noqa: BLE001
            self.failures.append(name)
            log.exception("nightly: %s failed", name)
            self.ledger.event(LOOP, "failure", self.as_of, None,
                              after={"step": name, "error": f"{type(exc).__name__}: {exc}",
                                     "trace": traceback.format_exc()[-1500:]})

    def setup(self) -> None:
        every = int(self.con["holdout_months"]["every"])
        self.ledger.record_holdout(holdout_months(HISTORY_START, self.day, every),
                                   self.con["holdout_months"]["rule"], self.as_of)
        from .. import promote                                  # noqa: PLC0415
        entries = list(engine_mod.registered(self.registry_path))
        entries += promote.register_engines(self.ledger)      # promoted grammar rules
        from .weekly import latest_refit                        # noqa: PLC0415
        for entry in entries:
            eng = engine_mod.load(entry)
            refit = latest_refit(self.ledger, eng.engine_id)
            if refit:                     # the weekly loop's accepted re-fit (X-2.4)
                eng.params.update(refit)
            if hasattr(eng, "bind_ledger"):
                eng.bind_ledger(self.ledger)
            if hasattr(eng, "bind_store"):
                eng.bind_store(self.store)
            self.engines[eng.engine_id] = eng
            if self.ledger.engine(eng.engine_id) is None:
                self.ledger.upsert_engine(eng.engine_id, eng.family, eng.horizon,
                                          "candidate", eng.min_size, self.as_of,
                                          kill_rule=eng.kill_rule or None)
                self.ledger.event(LOOP, "registered", self.as_of, eng.engine_id,
                                  after={"status": "candidate", "family": eng.family,
                                         "horizon": eng.horizon})

    def promote_step(self) -> None:
        """X-2.6: every passed grammar hypothesis -> live at min_size, trading from
        the next loop; a model's idea floored at 1.5 x min_signals."""
        from .. import promote                                  # noqa: PLC0415
        done = promote.promote_passed(self.ledger, self.as_of)
        self.summary["promoted"] = [d["engine"] for d in done]

    def harness_step(self) -> None:
        """THE HARNESS, NIGHTLY (X-2.9, 10.2): each REGISTERED hypothesis -- a
        rule in the grammar or a registered engine -- through X-1.6, oldest
        first, at most `research.max_runs_per_night` a night (config/alpha.yaml);
        and each one `testing` whose model-idea screen waits for data after the
        cutoff, again. A needs_code or data_gap idea waits for the sitting."""
        from .. import hypotheses as hyp                         # noqa: PLC0415
        from ..research import workbench                         # noqa: PLC0415
        cap = int((self.cfg.get("research") or {}).get("max_runs_per_night", 10))
        reg = hyp.Register(self.ledger)
        todo = [h for h in reg.all(["registered"])
                if h.get("rule_dsl") or (h.get("spec") or {}).get("engine")]
        todo += [h for h in reg.all(["testing"])
                 if ((h.get("result") or {}).get("model_rule") or {}).get("pending")]
        ran = {}
        for h in todo[:cap]:
            try:
                out = workbench.run(self.ledger, self.store, h["id"], self.as_of)
                ran[h["id"]] = out["status"]
            except (hyp.PreRegistrationViolation, workbench.QueuedForSitting) as exc:
                ran[h["id"]] = f"not run: {exc}"
        self.summary["harness"] = ran
        if len(todo) > cap:
            self.ledger.event(LOOP, "harness_queue", self.as_of, None,
                              after={"ran": len(ran), "waiting": len(todo) - cap})

    def inbox_step(self) -> None:
        """X-2.11: every new batch in the Drive inbox (and the proposer's), once."""
        from .. import inbox                                    # noqa: PLC0415
        res = inbox.ingest(self.ledger, self.store, self.as_of)
        self.summary["inbox"] = {k: len(v) for k, v in res.items()}

    def trading(self) -> list[dict]:
        return self.ledger.engines(("live", "halved"))

    def capital_for(self, engine_id: str) -> float:
        e = self.ledger.engine(engine_id)
        return book.capital(self.ledger, e, self.day, self.cfg) if e else 0.0

    def paper_step(self) -> None:
        force = {}
        if governor.lab_status(self.ledger) == "halted":
            last = self.ledger.one("SELECT as_of FROM loop_events WHERE kind='lab_halt'"
                                   " ORDER BY id DESC LIMIT 1")
            force["*"] = ("lab_halt", last["as_of"])
        for e in self.ledger.engines(("validation", "retired")):
            if self.ledger.open_positions(e["id"]):
                ev = self.ledger.one("SELECT as_of, kind FROM loop_events WHERE engine=?"
                                     " AND kind IN ('stop','kill') ORDER BY id DESC "
                                     "LIMIT 1", (e["id"],))
                if ev:
                    force[e["id"]] = ("governor_stop" if ev["kind"] == "stop" else "kill",
                                      ev["as_of"])
        opened = self.paper.fill_pending(self.as_of, self.capital_for)
        closed = self.paper.evaluate_exits(self.as_of, self.engines, force)
        self.summary.update(opened=len(opened), closed=len(closed))
        if opened or closed:
            self.ledger.event(LOOP, "paper", self.as_of, None,
                              after={"opened": opened, "closed": closed})

    def carry_step(self) -> None:
        """X-3.2: the paper book's crypto rows -- each live carry engine opens,
        accrues and closes its carry_book rows (paper only)."""
        if governor.lab_status(self.ledger) == "halted":
            return
        done = {}
        for e in self.trading():
            eng = self.engines.get(e["id"])
            if eng is not None and hasattr(eng, "carry"):
                done[e["id"]] = eng.carry(self.ledger, self.store, self.as_of,
                                          self.capital_for(e["id"]))
        if done:
            self.summary["carry"] = done

    def mark_step(self) -> None:
        self.summary["marked"] = self.paper.mark(self.as_of)

    def governor_step(self) -> None:
        ids = {e["id"] for e in self.ledger.engines(("live", "halved", "validation"))}
        ids |= {r["engine_id"] for r in self.ledger.q(
            "SELECT DISTINCT engine_id FROM positions")}
        cap, pnl = {}, {}
        for eid in sorted(ids):
            e = self.ledger.engine(eid)
            if not e:
                continue
            cap[eid] = book.capital(self.ledger, e, self.day, self.cfg)
            pnl[eid] = book.pnl_on(self.ledger, eid, self.day)
        g = governor.step(self.ledger, self.as_of, self.day, pnl, cap, self.con, self.cfg)
        self.summary.update(pnl=pnl, governor=g["transitions"],
                            lab_drawdown=g["equity"][LAB]["drawdown"])

    def posterior_step(self) -> None:
        sh = self.cfg.get("shrinkage") or {}
        n0 = float(sh.get("prior_signals", 20))
        p0 = float(sh.get("prior_win_rate", 0.5))
        for e in self.ledger.engines():
            x = book.graded_returns(self.ledger, e["id"])
            if not x:
                continue
            n = len(x)
            wins = sum(1 for v in x if v > 0)
            a, b = p0 * n0 + wins, (1 - p0) * n0 + (n - wins)
            mean = sum(x) / n
            sd = (sum((v - mean) ** 2 for v in x) / (n - 1)) ** 0.5 if n > 1 else 0.0
            post = {"engine_id": e["id"], "day": self.day, "n": n, "wins": wins,
                    "win_alpha": a, "win_beta": b, "win_mean": a / (a + b),
                    "exp_mean": n * mean / (n + n0),
                    "exp_sd": sd / math.sqrt(n + n0) if sd else 0.0,
                    "raw_expectancy": mean, "prior_strength": n0,
                    "prior_win_rate": p0, "prior_exp_mean": 0.0, "as_of": self.as_of}
            before = self.ledger.one("SELECT n, win_mean, exp_mean FROM edge_posterior "
                                     "WHERE engine_id=? AND day<? ORDER BY day DESC "
                                     "LIMIT 1", (e["id"], self.day))
            self.ledger.put("edge_posterior", post)
            if not before or before["n"] != n:
                self.ledger.event(LOOP, "posterior", self.as_of, e["id"], before=before,
                                  after={k: post[k] for k in ("n", "win_mean",
                                                              "exp_mean", "exp_sd",
                                                              "prior_strength")})

    def kill_step(self) -> None:
        k = self.con["kill"]
        for e in self.ledger.engines(("live", "halved")):
            need = acfg.min_signals(e["horizon"], self.con)
            x = book.graded_returns(self.ledger, e["id"])
            if len(x) < need:
                continue
            mean = sum(x) / len(x)
            sd = (sum((v - mean) ** 2 for v in x) / (len(x) - 1)) ** 0.5
            ppy = float((e.get("validated_metrics") or {}).get("periods_per_year")
                        or acfg.periods_per_year(e["horizon"], self.cfg))
            sr = (mean / sd * math.sqrt(ppy)) if sd else 0.0
            dsr = float((e.get("validated_metrics") or {}).get("deflated_sharpe") or 0.0)
            why = []
            if mean <= float(k["expectancy_at_or_below"]):
                why.append(f"expectancy after costs {mean:.5f} <= 0")
            if sr < float(k["realised_sharpe_below_deflated_multiple"]) * dsr:
                why.append(f"realised Sharpe {sr:.2f} < "
                           f"{k['realised_sharpe_below_deflated_multiple']} x {dsr:.2f}")
            if why:
                self.ledger.set_engine(e["id"], self.as_of, status="retired",
                                       frozen=True)
                self.ledger.event(LOOP, "kill", self.as_of, e["id"],
                                  before={"status": e["status"]},
                                  after={"status": "retired", "why": why, "n": len(x)},
                                  counterfactual={"status": e["status"]})

    def cost_step(self) -> None:
        win = int((self.cfg.get("cost_calibration") or {}).get("window_days", 60))
        import datetime as dt                                   # noqa: PLC0415
        since = (dt.date.fromisoformat(self.day) - dt.timedelta(days=win)).isoformat()
        rows = self.ledger.q("SELECT engine_id, cost_class, reference_price, "
                             "stored_quote FROM fills WHERE substr(filled_at,1,10)>=?",
                             (since,))
        groups: dict[tuple, list] = {}
        for r in rows:
            groups.setdefault((r["engine_id"], r["cost_class"]), []).append(r)
        import json                                             # noqa: PLC0415
        for (eid, cc), fs in sorted(groups.items()):
            mod, sto = [], []
            for f in fs:
                if not f["stored_quote"]:
                    continue
                q = json.loads(f["stored_quote"])
                mid = (q["bid"] + q["ask"]) / 2
                if mid <= 0:
                    continue
                sto.append((q["ask"] - q["bid"]) / mid * 1e4)
                mod.append(self.costs.modelled_spread_bps(cc, mid))
            m = sum(mod) / len(mod) if mod else None
            s = sum(sto) / len(sto) if sto else None
            row = {"engine_id": eid, "cost_class": cc, "day": self.day,
                   "n": len(sto), "modelled_bps": m, "stored_bps": s,
                   "ratio": (s / m) if (m and s is not None) else None,
                   "as_of": self.as_of}
            self.ledger.put("cost_calibration", row)
            self.ledger.event(LOOP, "cost_calibration", self.as_of, eid,
                              after={k: row[k] for k in ("cost_class", "n",
                                                         "modelled_bps", "stored_bps",
                                                         "ratio")})

    def allocate_step(self) -> None:
        engines = self.trading()
        if not engines:
            return
        rets = {e["id"]: book.daily_returns(self.ledger, e["id"]) for e in engines}
        graded = {e["id"]: len(book.graded_returns(self.ledger, e["id"])) for e in engines}
        res = allocate.weights(engines, rets, graded, self.con, self.cfg)
        before = {r["engine_id"]: r["weight"] for r in self.ledger.q(
            "SELECT engine_id, weight FROM allocations WHERE kind='proposed' AND day<?"
            " AND day=(SELECT MAX(day) FROM allocations WHERE kind='proposed' AND day<?)",
            (self.day, self.day))}
        for eid, w in res["weights"].items():
            self.ledger.put("allocations", {
                "engine_id": eid, "day": self.day, "kind": "proposed",
                "weight": w["weight"], "cluster": w["cluster"], "detail": w["why"],
                "as_of": self.as_of})
        self.ledger.event(LOOP, "weights_proposed", self.as_of, None, before=before,
                          after={"weights": {k: v["weight"] for k, v in
                                             res["weights"].items()},
                                 "kelly_fraction": res["kelly_fraction"],
                                 "correlation_threshold": res["correlation_threshold"],
                                 "heat_cap": res["heat_cap"],
                                 "clusters": res["clusters"]},
                          counterfactual={"weights": before})

    def attribution_step(self) -> None:
        key = self.store.regime_key(self.as_of, self.day)
        pnl = self.summary.get("pnl") or {}
        wrote = {}
        for eid, v in sorted(pnl.items()):
            n = self.ledger.one("SELECT COUNT(*) AS n FROM grades WHERE engine_id=? "
                                "AND day=?", (eid, self.day))["n"]
            self.ledger.put("attribution", {"engine_id": eid, "day": self.day,
                                            "regime_key": key, "pnl": v, "n": n,
                                            "as_of": self.as_of})
            wrote[eid] = v
        if wrote:
            self.ledger.event(LOOP, "attribution", self.as_of, None,
                              after={"regime_key": key, "pnl": wrote})

    def drift_step(self) -> None:
        d = self.cfg.get("drift") or {}
        win, band = int(d.get("window_signals", 60)), float(d.get("band_se", 2.0))
        for e in self.ledger.engines(("live", "halved")):
            vm = e.get("validated_metrics") or {}
            if not vm or vm.get("deflated_sharpe") is None:
                continue
            x = book.graded_returns(self.ledger, e["id"], last=win)
            if len(x) < 10:
                continue
            mean = sum(x) / len(x)
            sd = (sum((v - mean) ** 2 for v in x) / (len(x) - 1)) ** 0.5
            ppy = float(vm.get("periods_per_year") or 252)
            sr = mean / sd if sd else 0.0
            se = math.sqrt((1 + 0.5 * sr * sr) / len(x)) * math.sqrt(ppy)
            lower = float(vm["deflated_sharpe"]) - band * se
            if sr * math.sqrt(ppy) < lower:
                self.ledger.event(LOOP, "drift_flag", self.as_of, e["id"],
                                  after={"realised_sharpe": sr * math.sqrt(ppy),
                                         "validated_deflated_sharpe": vm["deflated_sharpe"],
                                         "lower_band": lower, "n": len(x)})

    def signal_step(self) -> None:
        if governor.lab_status(self.ledger) == "halted":
            return
        queued, refused = [], []
        for e in self.trading():
            eng = self.engines.get(e["id"])
            if eng is None:
                continue
            cap = self.capital_for(e["id"])
            for sig in eng.signal(self.as_of, self.store):
                try:
                    blocklist.refuse(sig.instrument.id)
                except blocklist.BlockedInstrument as exc:
                    refused.append({"engine": e["id"], "instrument": sig.instrument.id,
                                    "why": str(exc)})
                    continue
                frac = float(eng.size(sig, cap))
                queued.append(self.paper.queue(e["id"], sig, frac))
        if queued or refused:
            self.ledger.event(LOOP, "signals", self.as_of, None,
                              after={"queued": queued, "refused": refused})
        self.summary.update(queued=len(queued), refused=len(refused))

    def run(self) -> dict:
        for name, fn in (("setup", self.setup), ("inbox", self.inbox_step),
                         ("harness", self.harness_step),
                         ("paper", self.paper_step), ("carry", self.carry_step),
                         ("mark", self.mark_step), ("governor", self.governor_step),
                         ("posterior", self.posterior_step), ("kill", self.kill_step),
                         ("cost_calibration", self.cost_step),
                         ("allocate", self.allocate_step),
                         ("attribution", self.attribution_step),
                         ("drift", self.drift_step), ("signals", self.signal_step),
                         ("promote", self.promote_step)):
            self.step(name, fn)
        self.summary["failures"] = self.failures
        self.ledger.event(LOOP, "run", self.as_of, None,
                          after={k: v for k, v in self.summary.items() if k != "pnl"})
        return self.summary


def run(as_of: Optional[str] = None, store_path=None, ledger_path=None,
        registry_path=None) -> dict:
    """One nightly run. Never raises: a store that will not open is a failure
    event in the ledger and a non-empty `failures`."""
    as_of = as_of or session.utc_iso(timespec="microseconds")
    with Ledger(ledger_path) as lg:
        try:
            st = ReadOnlyStore(store_path)
        except Exception as exc:                              # noqa: BLE001
            lg.event(LOOP, "failure", as_of, None,
                     after={"step": "open_store", "error": f"{type(exc).__name__}: {exc}"})
            return {"as_of": as_of, "failures": ["open_store"]}
        try:
            return Run(lg, st, as_of, registry_path).run()
        finally:
            st.close()


def _main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="The Alpha Lab's nightly loop")
    ap.add_argument("--as-of")
    ap.add_argument("--store")
    ap.add_argument("--ledger")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    out = run(a.as_of, a.store, a.ledger)
    print(f"alpha nightly {out.get('day', '')}: failures={out.get('failures')}")
    return 1 if out.get("failures") else 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
