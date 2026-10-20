"""
The Alpha Lab, Tranche 3 part 2 (alpha-lab-4; X-3.3, X-3.5) and CD-12 -- what has
no home in tools/validate_alpha.py. Synthetic stores only: no gate here reads the
live store, fetches or calls a model.

  A  ENGINE 6, EXTREMES REVERSION (X-3.3). On a synthetic close with injected
     shocks: a print is identified only against its own trailing window as known
     on its day (a shock the move screen's in-sample window would flag, with too
     little trailing history, is never counted); a bucket at n=29 prints
     "awaiting (n=29 of 30)" and trades nothing, and at n=30 it opens at the
     horizon its formation sample says and trades at it; later prints that would
     favour another horizon never move it; a changed spec no longer hashes to
     its manifest and is refused; the roster quotes the spec's sha256; the costs
     reproduce a hand figure; registered by manifest, the harness waits on the
     sample and counts nothing.
  B  THE GRAMMAR SEARCH (X-3.5). A fixture family of known size counts every
     candidate (the variant count rises by all of them before the first test);
     the manifest fixes the family's sha256, the count and the split, and refuses
     a changed family on resume; the candidate and wall-clock caps stop a step and
     the next resumes; the holdout is backtested only after the survivor list is
     frozen; a formation survivor that fails the holdout is not written; the
     survivor written is systematic, pre-registered by the search's manifest; a
     pending variable is skipped with its reason; the Lab report prints the line.
  C  RULING 5 OF 19 OCT 2026. Coverage: a fixture variable whose history starts
     four years before the holdout is pending with its date and its options are
     not candidates (N counts only what the run tests), one at six years joins,
     a series stored in 2024 for observations from 2010 starts in 2024, and the
     manifest records each; the dealer regime is pending on its captures'
     history. The cadence: the nightly step's cap leaves the 20-minute unit 3
     minutes spare and under 120 s it skips and prints why; a new run does not
     begin while one is unfinished, nor outside a month's first week; the search
     is the nightly loop's last step and the weekly loop's no longer. One lock:
     while another process holds it, a step does nothing.
  D  GRAMMAR v2 (alpha-lab-rules/v2). A v2 rule conditioned on a fixture state
     trades only where the state was knowable at the decision and matched; a
     state stored after the decision (late, or a later revision) is never read;
     an instrument-keyed z reads its own instrument; a v1 rule may not carry
     `when`; the registered translations' v1 rules replay identically as v1 and
     as v2; a conditioned candidate's trades in the search equal its v2 rule's
     backtest, trade for trade, and are not the base rule's filtered after the
     fact; the search's Conditions calls the grammar's reader; a conditioned
     survivor registers its v2 rule; the manifest's hash covers the grammar
     version; the proposer stays on v1.

    python tools/validate_alpha_lab_4.py
"""

from __future__ import annotations

import datetime as dt
import math
import os
import random
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

_TMP = gate_mkdtemp(prefix="validate_alpha_lab_4_")
os.environ["CHESTER_DB"] = os.path.join(_TMP, "store.sqlite")
os.environ.pop("ALPHA_DB", None)
for _k, _d in (("ALPHA_INBOX", "inbox"), ("ALPHA_OUTBOX", "outbox"),
               ("ALPHA_RESEARCH_DIR", "research"), ("ALPHA_REPORTS_DIR", "reports")):
    os.environ[_k] = os.path.join(_TMP, _d)

import yaml  # noqa: E402

from altdata import observations, session  # noqa: E402

observations.DEFAULT_DB = os.environ["CHESTER_DB"]

from alpha import manifest, pit  # noqa: E402
from alpha import search as search_mod  # noqa: E402
from alpha import hypotheses as hyp  # noqa: E402
from alpha.engines import reversion as rev  # noqa: E402
from alpha.ledger import Ledger  # noqa: E402
from alpha.research import workbench  # noqa: E402
from alpha.store import ReadOnlyStore  # noqa: E402

PASS = FAIL = 0
LINE = "=" * 78
ROSTER6 = REPO / "alpha" / "research" / "roster-2026-10-19-x3-3.yaml"


def check(c: bool, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


def close(a, b, tol=1e-9) -> bool:
    return a is not None and b is not None and abs(a - b) <= tol


def sessions(first: str, last: str) -> list[str]:
    d, d1, out = dt.date.fromisoformat(first), dt.date.fromisoformat(last), []
    while d <= d1:
        if session.is_trading_session(d):
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def at(day: str, hhmm: str = "20:20") -> str:
    return f"{day}T{hhmm}:00+00:00"


def write_store(path: str, rows: list[dict]) -> None:
    st = observations.ObservationStore(path)
    st.write_many(rows)
    st.close()


# ---------------------------------------------------------------------------
# A. Engine 6
# ---------------------------------------------------------------------------
REV_KEY = "yfinance.mkt_gld"
EARLY_SHOCK = 300                      # under 500 trailing changes: never a print
FIRST_SHOCK, EVERY, FORMED, AFTER = 520, 25, 30, 5
DOWN = -0.05


def rev_fixture() -> tuple[list[str], list[float], list[int]]:
    """GLD's synthetic close: bounded noise (never 2.5 sigma by itself), an early
    shock, then 35 down-shocks. The first 30 recover 72% over sessions 2-5 (half
    reversed at 5, 10 and 20, not at 1); the last 5 bounce 80% the next session
    and give it back by the fifth (half reversed at 1 only)."""
    days = sessions("2015-01-02", "2021-12-31")
    rnd = random.Random(11)
    chg = [rnd.uniform(-0.006, 0.006) for _ in days]
    chg[0] = 0.0
    shocks = [FIRST_SHOCK + EVERY * k for k in range(FORMED + AFTER)]

    def shape(s: int, late: bool) -> None:
        for j in range(0, 21):
            chg[s + j] = 0.0
        chg[s] = DOWN
        if late:
            chg[s + 1] = 0.04
            for j in range(2, 6):
                chg[s + j] = -0.009
        else:
            for j in range(2, 6):
                chg[s + j] = 0.009
    shape(EARLY_SHOCK, False)
    for k, s in enumerate(shocks):
        shape(s, k >= FORMED)
    px, lv = [], math.log(100.0)
    for c in chg:
        lv += c
        px.append(math.exp(lv))
    return days, px, shocks


def build_rev_store(path: str) -> tuple[list[str], list[int]]:
    days, px, shocks = rev_fixture()
    rows = [{"registry_key": REV_KEY, "instrument": None, "observed_at": d,
             "available_at": at(d), "value": v, "source": "synthetic"}
            for d, v in zip(days, px)]
    write_store(path, rows)
    return days, shocks


def dec(day: str) -> str:
    return pit.nightly_after(at(day))[1]


def group_a() -> None:
    head("A. ENGINE 6, EXTREMES REVERSION (X-3.3)")
    sp = os.path.join(_TMP, "rev.sqlite")
    days, shocks = build_rev_store(sp)
    st = ReadOnlyStore(sp)
    eng = rev.ReversionEngine({"symbols": ["GLD"]})
    eng.engine_id, eng.min_size = "reversion", 0.02
    try:
        cfg = rev.load_config()
        roster = yaml.safe_load(ROSTER6.read_text(encoding="utf-8"))
        h6 = roster["hypotheses"][0]
        check(rev.spec_sha256(cfg) == cfg["spec_sha256"] == h6["data"]["spec_sha256"]
              and cfg["spec_sha256"] in " ".join(roster["inputs"])
              and h6["engine"] == "reversion" and h6["family"] == cfg["spec"]["family"],
              "the spec hashes to the sha256 the config and the roster's E-6 both quote, "
              "and the roster names the engine and its variant_counts family")
        sp_ = cfg["spec"]
        check(sp_["data_gate"]["min_formation_prints"] == 30
              and sp_["reversal"]["horizons_sessions"] == [1, 5, 10, 20]
              and sp_["print"]["sigma"] == 2.5 and sp_["min_reversal_share"] == 0.5
              and all(k in sp_ for k in ("bucket", "horizon_rule", "instruments",
                                         "costs", "exit", "entry")),
              "the spec pre-registers the bucket, the gate (30), the reversal measure "
              "(1, 5, 10, 20), the horizon rule, the instruments, the costs and the exit")

        late = dec(days[-1])
        sc = eng.scan(st, late)
        down = sc.get("GLD:-") or {}
        pdays = {x["day"] for x in down.get("prints", [])}
        check(days[EARLY_SHOCK] not in pdays
              and pdays == {days[s] for s in shocks},
              f"the down-prints are exactly the 35 shocks identified point in time: "
              f"{len(pdays)} found")
        # the in-sample reading the move screen prints would have counted it
        p = rev._Points(pit.Series(st, REV_KEY))
        allc = p.chg[1:]
        mu = sum(allc) / len(allc)
        sd = math.sqrt(sum((c - mu) ** 2 for c in allc) / len(allc))
        z_in = (p.chg[EARLY_SHOCK] - mu) / sd
        trail = EARLY_SHOCK - 1
        check(abs(z_in) >= 2.5 and trail < sp_["print"]["min_observations"]
              and days[EARLY_SHOCK] not in pdays,
              f"a print identified only in-sample is never counted: the early shock is "
              f"{z_in:.1f} sigma against the whole window, but has {trail} trailing "
              f"changes as known on its day (under 500)")
        # z as known on the day, not with the later shocks in its spread
        x0 = next(x for x in down["prints"] if x["day"] == days[shocks[0]])
        check(x0["decided_at"] == dec(days[shocks[0]]) and x0["available_at"] <= x0["decided_at"]
              and abs(x0["z"]) > abs(z_in),
              f"each print is decided at its own nightly instant against its trailing "
              f"window: the first shock is {x0['z']:.1f} sigma then, against "
              f"{z_in:.1f} for the same size of move in-sample")

        # n = 29 and n = 30
        a29 = dec(days[shocks[FORMED - 1] + 19])
        s29 = eng.scan(st, a29)["GLD:-"]
        sig29 = eng.signal(dec(days[shocks[FORMED - 1]]), st)
        check(not s29["open"] and s29["line"] == "awaiting (n=29 of 30)"
              and not sig29 and not eng.refit_rows(st, a29),
              f"at n=29 the bucket prints \"{s29['line']}\" and trades nothing")
        a30 = dec(days[shocks[FORMED - 1] + 20])
        s30 = eng.scan(st, a30)["GLD:-"]
        check(s30["open"] and s30["horizon"] == 5 and s30["fades"]
              and close(s30["shares"][5], 1.0) and close(s30["shares"][1], 0.0)
              and s30["open_at"] == a30,
              f"at n=30 it opens at the horizon its formation says: {s30['line']}")
        d30 = days[shocks[FORMED]]
        sig = eng.signal(dec(d30), st)
        check(len(sig) == 1 and sig[0].direction == 1 and sig[0].params["horizon"] == 5
              and sig[0].params["time_stop_date"] == pit.next_session(d30, 6)
              and sig[0].instrument.cost_class == "etf",
              f"the next print after formation trades at the frozen horizon: long GLD "
              f"(a fade), 5 sessions, time stop {sig[0].params['time_stop_date'] if sig else None}")
        check(not eng.signal(dec(days[shocks[FORMED - 1]]), st)
              and all(r["print_day"] not in s30["formation_days"]
                      for r in eng.refit_rows(st, late)),
              "a formation print is never traded")

        # later prints favour another horizon; the frozen one does not move
        fin = sc["GLD:-"]
        post = [x for x in fin["prints"] if x["decided_at"] > fin["open_at"]]
        best_post = max((1, 5, 10, 20), key=lambda h: sum(x["reversed"][h] for x in post))
        check(fin["horizon"] == 5 and fin["formation_days"] == s30["formation_days"]
              and best_post == 1 and len(post) == AFTER,
              f"the horizon never moves: the {len(post)} later prints reverse at 1 "
              f"session, and the bucket stays at {fin['horizon']}")
        rows = eng.refit_rows(st, late)
        check(len(rows) == AFTER and all(r["horizon"] == 5 and r["direction"] == 1
                                         and r["fill_at"] == "close" for r in rows),
              f"every traded print uses the frozen horizon from the next close: "
              f"{len(rows)} trades")
        ups = sc.get("GLD:+") or {}
        check(ups.get("line") == f"awaiting (n={AFTER} of 30)",
              f"the up-print bucket is its own: \"GLD:+ {ups.get('line')}\"")

        import contextlib                                       # noqa: PLC0415
        import hashlib                                          # noqa: PLC0415
        import io                                               # noqa: PLC0415
        before = hashlib.sha256(Path(sp).read_bytes()).hexdigest()
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = rev._main(["lines", "--store", sp, "--as-of", late])
        out_l = buf.getvalue()
        check(rc == 0 and "GLD:- open: horizon 5 sessions" in out_l
              and "GLD:+ awaiting (n=5 of 30)" in out_l
              and hashlib.sha256(Path(sp).read_bytes()).hexdigest() == before,
              "`python -m alpha.engines.reversion lines` prints each bucket's state and "
              "leaves the store as it was (the box's dry run)")

        bad = Path(_TMP) / "alpha_reversion_changed.yaml"
        c2 = yaml.safe_load(rev.CONFIG.read_text(encoding="utf-8"))
        c2["spec"]["reversal"]["horizons_sessions"] = [1, 5, 10]
        bad.write_text(yaml.safe_dump(c2), encoding="utf-8")
        try:
            rev.ReversionEngine({"config": str(bad), "symbols": ["GLD"]}).scan(st, late)
            refused = False
        except rev.SpecChanged:
            refused = True
        check(refused, "a changed spec no longer hashes to its manifest's sha256 and is "
                       "refused")

        # the costs, by hand: etf, $2,000 of capital (min_size 0.02 of 100,000)
        r0 = rows[0]
        one = 1.5e-4 + 5e-4 + 1.0 / 2000.0        # half spread, no-ADV slip, $1 min
        check(close(r0["cost"], 2 * one, 1e-12) and close(eng.cost("etf", 1, 150.0, 7),
                                                         0.0023, 1e-12),
              f"a long's cost reproduces the hand figure: 2 x (1.5 + 5 + 5) bp = 23 bp "
              f"({r0['cost'] * 1e4:.2f} bp)")
        check(close(eng.cost("etf", -1, 150.0, 7), 0.0023 + 50e-4 * 7 / 365, 1e-12),
              "a short adds its borrow: 50 bp a year over 7 calendar days")
        check(close(r0["ret"], (r0["exit_price"] / r0["price"] - 1), 1e-12)
              and r0["day"] > r0["decided_day"],
              "a trade's return runs from the next session's close to the horizon's, "
              "decided before it is filled")

        # registered by manifest, the harness waits on the sample
        lp = os.path.join(_TMP, "alpha_a.db")
        lg = Ledger(lp)
        try:
            out = manifest.register(lg, st, roster, as_of="2014-12-01T15:05:00+00:00")
            hid = out["registered"]["E-6"]
            v0 = lg.variant_count("reversion")
            r = workbench.run(lg, st, hid, late)
            cov = (r.get("result") or {}).get("coverage") or {}
            check(r["status"] == "insufficient_history" and v0 == 1
                  and lg.variant_count("reversion") == v0
                  and hyp.Register(lg).get(hid)["status"] == "registered"
                  and "GLD:- open: horizon 5 sessions" in " | ".join(cov.get("lines", [])),
                  f"registered by manifest, the harness waits on the sample and counts "
                  f"nothing beyond the registration's one: {r['reason'][:80]}")
        finally:
            lg.close()
    finally:
        st.close()


# ---------------------------------------------------------------------------
# B. The grammar search
# ---------------------------------------------------------------------------
SEARCH_AS_OF = "2024-07-02T22:00:00+00:00"       # the first week of July 2024
HOLD_FROM = "2023-07-01"                         # 12 whole months before July 2024


def search_cfg() -> dict:
    """A fixture family of known size: 2 signal families x (none + 2 values of one
    state variable; the dealer regime pending) x 1 horizon x 2 instruments x 1
    exit = 12 candidates."""
    import copy                                                 # noqa: PLC0415
    cfg = copy.deepcopy(search_mod.load_config())
    f = cfg["family"]
    f["signal_families"] = {k: f["signal_families"][k] for k in ("trend_63", "dip_20")}
    f["horizons"] = [5]
    f["instruments"] = ["GLD", "TLT"]
    f["exits"] = {"time_only": {}}
    f["conditioning"] = {"volatility": {**f["conditioning"]["volatility"],
                                        "values": ["normal", "crisis"]},
                         "dealer": f["conditioning"]["dealer"]}
    return cfg


def build_search_store(path: str) -> None:
    """GLD rises steadily throughout; TLT rises until the holdout, then falls.
    The market-state object is stored each session from the start, available
    that evening, so the volatility dial's history passes coverage."""
    days = sessions("2018-01-02", "2024-06-28")
    rnd = random.Random(5)
    rows = []
    for key, turns in (("yfinance.mkt_gld", False), ("yfinance.mkt_tlt", True)):
        lv = math.log(100.0)
        for d in days:
            drift = -0.002 if (turns and d >= HOLD_FROM) else 0.002
            lv += drift + rnd.uniform(-0.002, 0.002)
            rows.append({"registry_key": key, "instrument": None, "observed_at": d,
                         "available_at": at(d), "value": math.exp(lv),
                         "source": "synthetic"})
    import json                                                 # noqa: PLC0415
    for d in days:
        rows.append({"registry_key": "market_state", "instrument": None, "observed_at": d,
                     "available_at": at(d, "21:30"), "source": "synthetic",
                     "value": json.dumps({"dials": {"vol": {"state": "subdued"}}})})
    write_store(path, rows)


def group_b() -> None:
    head("B. THE GRAMMAR SEARCH (X-3.5)")
    sp = os.path.join(_TMP, "search.sqlite")
    build_search_store(sp)
    st = ReadOnlyStore(sp)
    cfg = search_cfg()
    lg = Ledger(os.path.join(_TMP, "alpha_b.db"))
    seen: list[tuple[str, str]] = []
    real_bt = search_mod.rules.backtest

    def spy_bt(cmp, store, first, last, drop=None, data=None):
        seen.append((first, last))
        return real_bt(cmp, store, first, last, drop=drop, data=data)
    search_mod.rules.backtest = spy_bt
    try:
        p = search_mod.plan(cfg)
        cands = search_mod.candidates(cfg)
        check(p["n_candidates"] == 12 == len(cands) == len({c["id"] for c in cands})
              and p["conditioning_options"] == 3,
              f"a fixture family of known size: 2 x 3 x 1 x 2 x 1 = {p['n_candidates']} "
              f"candidates, each enumerated once")
        why_d = "the dealer regime is not in search-v1 (ruling 5(b) of 19 Oct 2026)"
        check(p["pending"] == {"dealer": why_d}
              and not any("dealer" in c["id"] for c in cands)
              and p["pending_lines"] == [f"dealer: skipped, pending -- {why_d}"],
              "a pending variable is skipped, with its reason printed")
        real = search_mod.load_config()
        check(real["family"]["conditioning"]["dealer"].get("pending") is True
              and {"dials", "positioning", "funding", "volatility"}
              <= set(real["family"]["conditioning"])
              and real["caps"] == {"max_candidates_per_run": 400, "max_wall_seconds": 600}
              and real["coverage"]["min_years_before_holdout"] == 5
              and real["family"]["conditioning"]["dealer"]["history"]
              == {"key": "exposure.net_gex", "instrument": "SPY"}
              and {k: real["cadence"][k] for k in ("step_in", "unit_timeout_seconds",
                                                    "spare_seconds", "min_step_seconds",
                                                    "begin_by_day")}
              == {"step_in": "nightly", "unit_timeout_seconds": 1200, "spare_seconds": 180,
                  "min_step_seconds": 120, "begin_by_day": 7},
              "the shipped family conditions on the dials, positioning, the funding and "
              "the volatility regime, the dealer regime pending on its captures' history; "
              "caps 400 candidates and 600 s; coverage 5 years; the nightly cadence with "
              "3 minutes spare and a 120 s floor (ruling 5)")

        s1 = search_mod.step(lg, st, SEARCH_AS_OF, cfg, max_candidates=4)["search"]
        prog = search_mod.load_progress(s1["run_id"])
        mf = manifest.read(prog["manifest"])
        check(mf is not None and mf["batch"]["n_candidates"] == 12
              and mf["batch"]["family_sha256"] == search_mod.family_sha256(cfg)
              and mf["batch"]["holdout_from"] == HOLD_FROM
              and mf["written_at"] == hyp.instant(SEARCH_AS_OF) == prog["manifest_at"],
              f"the manifest is written before the first backtest and fixes the family's "
              f"sha256, the count (12) and the split (holdout from {HOLD_FROM})")
        check(lg.variant_count("search-v1") == 12 == prog["n_trials"]
              and all(v["n_trials"] == 12 for v in prog["done"].values()),
              "the family's variant count rises by the whole candidate count, and every "
              "candidate is deflated by N=12")
        check(s1["stopped"] == "candidates" and s1["tested"] == 4
              and prog["stage"] == "formation",
              f"the candidate cap stops the step: {s1['line']}")
        clock = iter([0.0, 0.0, 1e6, 1e6, 1e6])
        s2 = search_mod.step(lg, st, SEARCH_AS_OF, cfg, clock=lambda: next(clock),
                             max_wall=5.0)["search"]
        check(s2["stopped"] == "wall_clock" and 4 < s2["tested"] < 12,
              f"the wall-clock cap stops it too, after resuming where it stopped: "
              f"{s2['tested']} of 12")
        import copy                                             # noqa: PLC0415
        changed = copy.deepcopy(cfg)
        changed["family"]["horizons"] = [5, 10]
        try:
            search_mod.step(lg, st, SEARCH_AS_OF, changed)
            refused = False
        except search_mod.FamilyChanged:
            refused = True
        check(refused, "the manifest's hash refuses a changed family on resume")
        check(all(last < HOLD_FROM for _, last in seen),
              f"in formation the holdout is never backtested: {len(seen)} backtests, "
              f"each ending before {HOLD_FROM}")
        n_bt = len(seen)
        s3 = search_mod.step(lg, st, SEARCH_AS_OF, cfg)["search"]
        prog = search_mod.load_progress(s3["run_id"])
        surv = prog["survivors"]
        hold_bt = seen[n_bt:]
        check(s3["stage"] == "done" and len(prog["done"]) == 12
              and set(surv) == {"trend_63|h5|GLD|time_only|none",
                                "trend_63|h5|TLT|time_only|none"}
              and prog["frozen_sha256"]
              and any(first == HOLD_FROM for first, _ in hold_bt),
              f"resumed to the end: {len(surv)} formation survivors frozen, and only then "
              f"the holdout backtested")
        ho = prog["holdout"]
        check(ho["trend_63|h5|GLD|time_only|none"]["passed"]
              and not ho["trend_63|h5|TLT|time_only|none"]["passed"],
              f"the holdout test: GLD passes ({ho['trend_63|h5|GLD|time_only|none']['n']} "
              f"trades), TLT fails ({ho['trend_63|h5|TLT|time_only|none']['why']})")
        rows = lg.q("SELECT * FROM hypotheses ORDER BY id")
        check(len(rows) == 1 and rows[0]["source"] == "systematic"
              and "GLD" in rows[0]["title"] and prog["registered"],
              "a formation survivor that fails the holdout is not written; the one that "
              "passes is registered, source systematic")
        h = hyp.Register(lg).get(rows[0]["id"])
        try:
            m = manifest.check(lg, h, SEARCH_AS_OF)
            ok = m["kind"] == "manifest_file" and m["sha256"] == prog["manifest_sha256"]
        except manifest.NoManifest:
            ok = False
        check(ok and h["status"] == "registered" and h["pre_registered_at"] == prog["manifest_at"],
              "it is pre-registered by the search's manifest, at the manifest's instant, "
              "and the harness's manifest check accepts it")
        check(lg.one("SELECT COUNT(*) AS n FROM engines")["n"] == 0
              and not lg.q("SELECT 1 FROM loop_events WHERE kind IN ('promotion', "
                           "'validation_pass')"),
              "nothing else is written: no engine row, no promotion")
        bad = {**search_mod.load_config()}
        doc = {"schema": hyp.SCHEMA_ID, "batch_id": "x", "source": "operator",
               "proposer": "x", "channel": "search", "written_at": SEARCH_AS_OF,
               "model_idea_rule": False, "inputs": [], "hypotheses": [{}]}
        check(any("the search's source" in e for e in hyp.validate_batch(doc)) and bad,
              "the search channel takes source systematic only")
        from alpha import report                                # noqa: PLC0415
        lines = report.search_lines(lg, "2024-07-31")
        check(lines[0] == "## 10. The grammar search"
              and "12 of 12 candidates tested" in lines[2]
              and "1 registered" in lines[2] and "N=12" in lines[2]
              and any("dealer: pending -- no history stored" in x for x in lines)
              and any("passed volatility" in x for x in lines),
              f"the Monthly's Lab report prints the line: {lines[2][:110]}")
        later = "2024-08-13T22:00:00+00:00"
        check(search_mod.nightly(lg, st, later, cfg, budget=600) == {"search": None},
              "past the first week with no run unfinished, the nightly step does nothing")
    finally:
        search_mod.rules.backtest = real_bt
        st.close()
        lg.close()



# ---------------------------------------------------------------------------
# C. Ruling 5 of 19 Oct 2026: coverage, the nightly cadence, the lock
# ---------------------------------------------------------------------------
C_AS_OF = "2024-07-02T22:00:00+00:00"           # holdout from 2023-07-01; needs 2018-07-01


def coverage_cfg(name: str) -> dict:
    """1 signal family x (none + 3 bands of each z variable) x 1 x 1 x 1: a
    variable at six years joins, one at four years and one backfilled today
    without vintages do not."""
    import copy                                                 # noqa: PLC0415
    cfg = copy.deepcopy(search_mod.load_config())
    f = cfg["family"]
    f["name"] = name
    f["signal_families"] = {"trend_63": f["signal_families"]["trend_63"]}
    f["horizons"], f["instruments"], f["exits"] = [5], ["GLD"], {"time_only": {}}
    z = {"kind": "zscore", "window": 20, "min_rows": 10,
         "bands": {"crowded_long": 1.5, "crowded_short": -1.5},
         "values": ["crowded_long", "neutral", "crowded_short"]}
    f["conditioning"] = {
        "six_years": {**z, "what": "fixture, observed from 2017-07-03, each knowable 3 days on",
                      "key": "cftc.noncomm_net", "instrument": "SP500"},
        "four_years": {**z, "what": "fixture, observed from 2019-07-01, each knowable 3 days on",
                       "key": "cftc.noncomm_net", "instrument": "NASDAQ100"},
        "backfilled": {**z, "what": "fixture, observed from 2010, stored in 2024",
                       "key": "calc.funding_agg"},
        "dealer": f["conditioning"]["dealer"]}
    return cfg


def build_coverage_store(path: str) -> None:
    rows = []
    for inst, first in (("SP500", "2017-07-03"), ("NASDAQ100", "2019-07-01")):
        d = dt.date.fromisoformat(first)
        while d.isoformat() <= "2024-06-25":
            rows.append({"registry_key": "cftc.noncomm_net", "instrument": inst,
                         "observed_at": d.isoformat(),
                         "available_at": at((d + dt.timedelta(days=3)).isoformat()),
                         "value": float(d.toordinal() % 97), "source": "synthetic"})
            d += dt.timedelta(days=7)
    d = dt.date(2010, 1, 4)
    while d.isoformat() <= "2024-06-25":
        rows.append({"registry_key": "calc.funding_agg", "instrument": None,
                     "observed_at": d.isoformat(), "available_at": at("2024-06-26"),
                     "value": 5.0, "source": "synthetic"})
        d += dt.timedelta(days=7)
    for d in sessions("2024-04-01", "2024-06-28"):              # 6b's captures, recent
        rows.append({"registry_key": "exposure.net_gex", "instrument": "SPY",
                     "observed_at": d, "available_at": at(d), "value": 1.0e9,
                     "source": "synthetic"})
    write_store(path, rows)


def group_c() -> None:
    import subprocess                                           # noqa: PLC0415
    head("C. RULING 5 OF 19 OCT 2026: COVERAGE, THE NIGHTLY CADENCE, ONE LOCK")
    sp = os.path.join(_TMP, "coverage.sqlite")
    build_coverage_store(sp)
    st = ReadOnlyStore(sp)
    lg = Ledger(os.path.join(_TMP, "alpha_c.db"))
    try:
        # (a) coverage, before the manifest
        cfg = coverage_cfg("search-cov")
        s0 = search_mod.start(lg, st, cfg, C_AS_OF)
        mf = manifest.read(s0["manifest"])["batch"]
        cov = mf["coverage"]
        check(cov["six_years"]["first"] == "2017-07-06" and cov["six_years"]["passed"]
              and cov["six_years"]["joined"]
              and cov["six_years"]["required_by"] == "2018-07-01",
              f"a variable whose history starts six years before the holdout joins: "
              f"{cov['six_years']['line']}")
        check(cov["four_years"]["first"] == "2019-07-04" and not cov["four_years"]["passed"]
              and cov["four_years"]["line"]
              == "four_years: pending -- history from 2019-07-04 (needs 2018-07-01)",
              f"one at four years is pending with its date: {cov['four_years']['line']}")
        check(cov["backfilled"]["first"] == "2024-06-26" and not cov["backfilled"]["joined"],
              "a series observed from 2010 but stored only in 2024 starts in 2024: "
              "history is what was knowable, not what was observed")
        check(cov["dealer"]["first"] == "2024-04-01" and not cov["dealer"]["joined"]
              and "pending -- history from 2024-04-01" in cov["dealer"]["line"],
              f"the dealer regime's pending reason is its captures' history (ruling 5(b)): "
              f"{cov['dealer']['line']}")
        ids = mf["candidates"]
        check(mf["n_candidates"] == 4 == len(ids) == s0["n_candidates"]
              and mf["joined"] == ["six_years"]
              and not any(x in i for i in ids for x in ("four_years", "backfilled", "dealer")),
              f"the manifest records both, and only the joined variable's options are "
              f"candidates: {ids}")
        check(lg.variant_count("search-cov") == 4 == s0["n_trials"],
              "N counts only the candidates the run tests (4, not 13)")
        check(s0["manifest_at"] == hyp.instant(C_AS_OF)
              and not lg.q("SELECT 1 FROM loop_events WHERE kind='search_progress'"),
              "coverage is evaluated at the run's start, before the manifest and before "
              "any backtest")

        # (c) the budget
        c = search_mod.load_config()
        grid = [(spent, search_mod.step_budget(c, now=1000.0 + spent, started=1000.0))
                for spent in (0, 300, 420, 600, 840, 900, 950, 1100)]
        check(dict(grid)[0] == 600 and dict(grid)[420] == 600 and dict(grid)[600] == 420
              and dict(grid)[900] == 120
              and all(spent + b <= 1200 - 180 for spent, b in grid),
              f"the step's cap leaves the unit 3 minutes inside its 20-minute timeout: "
              f"{grid}")
        os.environ["CHESTER_UNIT_STARTED"] = "1000"
        try:
            env_b = search_mod.step_budget(c, now=1500.0)
        finally:
            os.environ.pop("CHESTER_UNIT_STARTED", None)
        check(env_b == 520, f"the unit's start is read from CHESTER_UNIT_STARTED: {env_b}")
        wrapper = (REPO / "scripts" / "run_alpha_nightly.sh").read_text(encoding="utf-8")
        check('export CHESTER_UNIT_STARTED="${CHESTER_UNIT_STARTED:-$(date +%s)}"' in wrapper
              and wrapper.index("export CHESTER_UNIT_STARTED") < wrapper.index("git pull --ff-only >>"),
              "the nightly wrapper exports the unit's start before its pull")
        import contextlib                                       # noqa: PLC0415
        import io                                               # noqa: PLC0415
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            sk = search_mod.nightly(lg, st, C_AS_OF, cfg, budget=70)
        ev = lg.q("SELECT after FROM loop_events WHERE kind='search_skipped'")
        check(sk["search"] is None and "under the 120 s minimum" in sk["search_skipped"]
              and "70 s left" in buf.getvalue() and len(ev) == 1,
              f"under 120 s the step is skipped and prints why: {buf.getvalue().strip()}")
        seen: list[dict] = []
        real_step = search_mod.step

        def spy(ledger, store, as_of, cfg=None, **kw):
            seen.append({"as_of": as_of, **kw})
            return {"search": None}
        search_mod.step = spy
        try:
            search_mod.nightly(lg, st, C_AS_OF, cfg, budget=333)
            nxt = "2024-08-05T22:00:00+00:00"                  # August's first week
            search_mod.nightly(lg, st, nxt, cfg, budget=600)
            fresh = coverage_cfg("search-none")
            out_wk3 = search_mod.nightly(lg, st, "2024-08-20T22:00:00+00:00", fresh,
                                         budget=600)
        finally:
            search_mod.step = real_step
        check(seen[0]["max_wall"] == 333 and seen[0]["begin"] is False,
              "an unfinished run's step is capped at the budget the nightly loop has left")
        check(seen[1]["begin"] is False and seen[1]["as_of"] == nxt
              and search_mod.load_progress("search-cov-2024-08") is None
              and search_mod.can_begin(cfg, nxt)[0] is False
              and "unfinished" in search_mod.can_begin(cfg, nxt)[1],
              "a new run does not begin while one is unfinished, even in a month's first "
              "week: the unfinished one is resumed")
        check(out_wk3 == {"search": None} and len(seen) == 2
              and search_mod.can_begin(fresh, "2024-08-20T22:00:00+00:00")
              == (False, "a new run begins only in the first week of a month")
              and search_mod.can_begin(fresh, "2024-08-06T22:00:00+00:00") == (True, ""),
              "nor outside a month's first week; in it, with nothing unfinished, one may")
        nl = (REPO / "alpha" / "loops" / "nightly.py").read_text(encoding="utf-8")
        wk = (REPO / "alpha" / "loops" / "weekly.py").read_text(encoding="utf-8")
        check(nl.index('("promote", self.promote_step)') < nl.index('("search", self.search_step)')
              and "search_mod.nightly" in nl and "search_mod" not in wk,
              "the search is the nightly loop's last step, and the weekly loop no longer "
              "steps it")

        # (c) one lock for every search step
        lp = search_mod.lock_path()
        code = ("import os,sys; sys.path.insert(0, sys.argv[1]); "
                "from alpha import files; from pathlib import Path\n"
                "with files.lock(Path(sys.argv[2])) as h:\n"
                "    print('held' if h else 'refused', flush=True); sys.stdin.read()\n")
        holder = subprocess.Popen([sys.executable, "-c", code, str(REPO), str(lp)],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
                                  env={**os.environ})
        try:
            first_line = holder.stdout.readline().strip()
            blocked = search_mod.step(lg, st, C_AS_OF, cfg, max_candidates=1)
            with search_mod.files.lock(lp) as mine:
                in_proc = mine
        finally:
            holder.stdin.close()
            holder.wait(timeout=30)
        check(first_line == "held" and blocked == {
            "search": None, "search_skipped": "another search step holds the lock"}
              and in_proc is False,
              "while another process holds the search's lock, a step does nothing and "
              "says why: two steps never hold the search at once")
        with search_mod.files.lock(lp) as again:
            with search_mod.files.lock(lp) as second:
                pair = (again, second)
        check(pair == (True, False),
              "the lock is released when its holder ends, and a second handle in one "
              "process is refused too")
    finally:
        st.close()
        lg.close()


# ---------------------------------------------------------------------------
# D. Grammar v2's state condition (alpha-lab-rules/v2)
# ---------------------------------------------------------------------------
V2_DAYS = ("2019-01-02", "2022-12-30")


def build_v2_store(path: str) -> dict:
    """GLD rising with noise; a market-state object each session whose vol state
    is "calm" on even ISO weeks and "storm" on odd ones, stored that evening --
    except: every 7th session's object is stored only the NEXT day (after the
    decision), and every 11th session's first vintage says "storm" and a later
    one, stored after the decision, says "calm". The CFTC net under two
    instruments with different paths."""
    import json                                                 # noqa: PLC0415
    days = sessions(*V2_DAYS)
    rnd = random.Random(11)
    rows, late, revised = [], set(), set()
    lv = math.log(100.0)
    for i, d in enumerate(days):
        lv += 0.0015 + rnd.uniform(-0.004, 0.004)
        rows.append({"registry_key": "yfinance.mkt_gld", "instrument": None,
                     "observed_at": d, "available_at": at(d), "value": math.exp(lv),
                     "source": "synthetic"})
        wk = dt.date.fromisoformat(d).isocalendar()[1]
        state = "calm" if wk % 2 == 0 else "storm"
        nxt = (dt.date.fromisoformat(d) + dt.timedelta(days=1)).isoformat()
        if i % 7 == 3:
            late.add(d)
            rows.append({"registry_key": "market_state", "instrument": None,
                         "observed_at": d, "available_at": at(nxt, "13:00"),
                         "source": "synthetic",
                         "value": json.dumps({"dials": {"vol": {"state": state}}})})
        elif i % 11 == 5:
            revised.add(d)
            rows.append({"registry_key": "market_state", "instrument": None,
                         "observed_at": d, "available_at": at(d, "21:30"),
                         "source": "synthetic",
                         "value": json.dumps({"dials": {"vol": {"state": "storm"}}})})
            rows.append({"registry_key": "market_state", "instrument": None,
                         "observed_at": d, "available_at": at(nxt, "13:00"),
                         "source": "synthetic",
                         "value": json.dumps({"dials": {"vol": {"state": "calm"}}})})
        else:
            rows.append({"registry_key": "market_state", "instrument": None,
                         "observed_at": d, "available_at": at(d, "21:30"),
                         "source": "synthetic",
                         "value": json.dumps({"dials": {"vol": {"state": state}}})})
    d = dt.date(2018, 1, 2)
    k = 0
    while d.isoformat() <= V2_DAYS[1]:
        rows.append({"registry_key": "cftc.noncomm_net", "instrument": "SP500",
                     "observed_at": d.isoformat(), "available_at": at(
                         (d + dt.timedelta(days=3)).isoformat()),
                     "value": 1000.0 * math.sin(k / 5.0), "source": "synthetic"})
        rows.append({"registry_key": "cftc.noncomm_net", "instrument": "NASDAQ100",
                     "observed_at": d.isoformat(), "available_at": at(
                         (d + dt.timedelta(days=3)).isoformat()),
                     "value": 50.0 * k, "source": "synthetic"})
        d += dt.timedelta(days=7)
        k += 1
    write_store(path, rows)
    return {"late": late, "revised": revised}


def group_d() -> None:
    import copy                                                 # noqa: PLC0415
    import json                                                 # noqa: PLC0415
    from alpha import rules                                     # noqa: PLC0415
    head("D. GRAMMAR v2: THE STATE CONDITION (alpha-lab-rules/v2)")
    sp = os.path.join(_TMP, "v2.sqlite")
    plan_ = build_v2_store(sp)
    st = ReadOnlyStore(sp)
    try:
        base = {"grammar": rules.GRAMMAR_V2, "universe": ["GLD"], "cadence": "daily_close",
                "trigger": [{"series": "GLD", "transform": "pct_change", "n": 5,
                             "op": ">", "value": -100}],
                "direction": "long", "instrument": "GLD", "entry": "next_close",
                "exits": {"time": 3}}
        cond = {**base, "when": [{"kind": "state", "path": "dials.vol.state",
                                  "values": ["calm"]}]}
        data = rules.Data(st)
        bt = rules.backtest(rules.compile_rule(cond), st, "2019-03-01", V2_DAYS[1],
                            data=data)
        trades = bt["trades"]
        ms = {}
        for r in st.all_vintages("market_state"):
            ms.setdefault(str(r["observed_at"])[:10], []).append(
                (str(r["available_at"]), json.loads(r["value_text"])["dials"]["vol"]["state"]))
        ok_known = all(any(a <= t["decided_at"] and v == "calm"
                           for a, v in ms[t["signal_day"]])
                       and max(a for a, v in ms[t["signal_day"]] if a <= t["decided_at"])
                       <= t["available_at"]
                       for t in trades)
        check(len(trades) > 50 and ok_known
              and all(t["when"] == {"state:dials.vol.state": "calm"} for t in trades),
              f"a v2 rule conditioned on a fixture state trades only where the state was "
              f"knowable at the decision and matched ({len(trades)} trades; each trade's "
              f"available_at covers the state it read)")
        on_late = [t for t in trades if t["signal_day"] in plan_["late"]]
        on_rev = [t for t in trades if t["signal_day"] in plan_["revised"]]
        calm_late = [d for d in plan_["late"]
                     if ms[d][0][1] == "calm" and "2019-03-01" <= d]
        check(not on_late and not on_rev and calm_late
              and bt["skipped"].get("when: no value knowable at the decision", 0) > 0,
              f"a state stored after the decision is never read: none of the "
              f"{len(calm_late)} calm sessions whose object was stored the next day "
              f"trades, nor a session whose later revision says calm")
        free = rules.backtest(rules.compile_rule(base), st, "2019-03-01", V2_DAYS[1],
                              data=data)["trades"]
        check(len(free) > len(trades) and not any("when" in t for t in free),
              f"without `when` the same rule trades every eligible session "
              f"({len(free)} trades)")

        # the instrument-keyed z
        zit = {"kind": "zscore", "key": "cftc.noncomm_net", "instrument": "SP500",
               "window": 20, "min_rows": 10,
               "bands": {"crowded_long": 1.0, "crowded_short": -1.0},
               "values": ["crowded_long", "neutral", "crowded_short"]}
        day, t = "2021-06-15", rules.decision_instant("2021-06-15", "next_close")
        got, av = rules.when_value(zit, data, day, t)
        xs = [x for x in st.all_vintages("cftc.noncomm_net", "SP500")
              if str(x["available_at"]) <= t and str(x["observed_at"])[:10] <= day]
        vals = [float(x["value_num"]) for x in sorted(xs, key=lambda r: r["observed_at"])][-20:]
        import statistics                                       # noqa: PLC0415
        z = (vals[-1] - statistics.fmean(vals)) / statistics.stdev(vals)
        want = "crowded_long" if z >= 1 else ("crowded_short" if z <= -1 else "neutral")
        nq, _ = rules.when_value({**zit, "instrument": "NASDAQ100"}, data, day, t)
        check(got == want and nq == "crowded_long" and av <= t,
              f"an instrument-keyed z reads its own instrument: SP500's z {z:+.2f} -> "
              f"{got}; NASDAQ100's steady climb -> {nq}")
        try:
            rules.compile_rule({**base, "grammar": rules.GRAMMAR, "when": cond["when"]})
            v1_when = False
        except rules.RuleError as exc:
            v1_when = any("grammar v2" in e for e in exc.errors)
        try:
            rules.compile_rule({**base, "when": [{**zit, "key": "no.such_key"}]})
            badkey = False
        except rules.RuleError:
            badkey = True
        check(v1_when and badkey,
              "a v1 rule may not carry `when`, and a `when` key must be registered")
    finally:
        st.close()

    # v1 replays identically: the registered translations' rules on the Tranche 2
    # fixture store, as v1 and relabelled v2
    sys.path.insert(0, str(REPO / "tests" / "fixtures" / "alpha"))
    import fixture_store                                        # noqa: PLC0415
    fp = os.path.join(_TMP, "fixture_v1.sqlite")
    fixture_store.build(fp)
    fs = ReadOnlyStore(fp)
    try:
        tdir = REPO / "alpha" / "research" / "translations" / "2026-10-14-claude-weekly-01"
        same, n_tr, names = True, 0, []
        for f in sorted(tdir.glob("H-*.yaml")):
            doc = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
            dsl = doc.get("rule_dsl")
            if not isinstance(dsl, dict):
                continue
            c1 = rules.compile_rule(dsl, fs)
            c2 = rules.compile_rule({**dsl, "grammar": rules.GRAMMAR_V2}, fs)
            a = rules.backtest(c1, fs, "2023-01-02", "2026-09-30")
            b = rules.backtest(c2, fs, "2023-01-02", "2026-09-30")
            same = same and a["trades"] == b["trades"] and a["skipped"] == b["skipped"]
            n_tr += len(a["trades"])
            names.append(f.stem)
        check(same and n_tr > 0 and len(names) >= 3,
              f"v1 replays identically: {', '.join(names)}'s registered rules backtest to "
              f"the same {n_tr} trades as v1 and as v2 with no `when`")
    finally:
        fs.close()

    # the search: a conditioned candidate's trades are its v2 rule's
    sp2 = os.path.join(_TMP, "search_v2.sqlite")
    build_search_store(sp2)
    import json as _json                                        # noqa: PLC0415
    st2 = observations.ObservationStore(sp2)
    rows = []
    for i, d in enumerate(sessions("2018-01-02", "2024-06-28")):
        rows.append({"registry_key": "market_state", "instrument": None, "observed_at": d,
                     "available_at": at(d, "21:35"), "source": "synthetic",
                     "value": _json.dumps({"dials": {"vol": {
                         "state": "normal" if (i // 15) % 2 else "crisis"}}})})
    st2.write_many(rows)
    st2.close()
    st = ReadOnlyStore(sp2)
    lg = Ledger(os.path.join(_TMP, "alpha_d.db"))
    seen: list = []
    real_bt = search_mod.rules.backtest

    def spy(cmp, store, first, last, drop=None, data=None):
        out = real_bt(cmp, store, first, last, drop=drop, data=data)
        seen.append((copy.deepcopy(cmp.dsl), first, last, out["trades"]))
        return out
    try:
        cfg = search_cfg()
        cfg["family"]["name"] = "search-v2"
        cfg["family"]["conditioning"]["volatility"]["values"] = ["normal", "crisis"]
        check(cfg["family"]["grammar"] == rules.GRAMMAR_V2
              and search_mod.load_config()["family"]["grammar"] == "alpha-lab-rules/v2",
              "the search's family is on grammar v2 before its first run")
        search_mod.rules.backtest = spy
        s = search_mod.step(lg, st, SEARCH_AS_OF, cfg)["search"]
        search_mod.rules.backtest = real_bt
        prog = search_mod.load_progress(s["run_id"])
        cid = "trend_63|h5|GLD|time_only|volatility=normal"
        c = next(x for x in search_mod.candidates(cfg, prog["joined"]) if x["id"] == cid)
        rule = search_mod.rule_of(cfg, c)
        used = next(tr for dsl, first, last, tr in seen
                    if dsl == rule and last < HOLD_FROM)
        indep = real_bt(rules.compile_rule(rule), st, search_mod._first_day(   # noqa: SLF001
            rules.Data(st), "GLD"), pit.prev_session(HOLD_FROM))["trades"]
        indep = [t for t in indep if t["exit_day"] < HOLD_FROM]
        base_tr = [t for t in real_bt(rules.compile_rule(search_mod.base_rule(cfg, c)), st,
                                      "2018-01-02", pit.prev_session(HOLD_FROM))["trades"]
                   if t["exit_day"] < HOLD_FROM]
        filt = [t for t in base_tr if search_mod.Conditions(st, cfg).value(
            "volatility", t["signal_day"], t["decided_at"]) == "normal"]
        used_f = [t for t in used if t["exit_day"] < HOLD_FROM]
        check(rule["when"] == [{"name": "volatility", "kind": "state",
                                "path": "dials.vol.state", "values": ["normal"]}]
              and used_f == indep and len(indep) > 0,
              f"a conditioned candidate's trades in the search equal its v2 rule's "
              f"backtest, trade for trade ({len(indep)} formation trades)")
        check([t["signal_day"] for t in filt] != [t["signal_day"] for t in indep],
              f"and they are the rule's own trades, not the base rule's filtered after "
              f"the fact ({len(filt)} filtered against {len(indep)})")
        calls: list = []
        real_wv = rules.when_value

        def wv(*a, **k):
            calls.append(a[0]["name"])
            return real_wv(*a, **k)
        rules.when_value = wv
        try:
            v = search_mod.Conditions(st, cfg).value("volatility", "2020-03-02",
                                                     rules.decision_instant("2020-03-02",
                                                                            "next_close"))
        finally:
            rules.when_value = real_wv
        src = (REPO / "alpha" / "search.py").read_text(encoding="utf-8")
        check(calls == ["volatility"] and v in ("normal", "crisis")
              and "statistics.stdev" not in src and "pit.Series(" not in src,
              "one reader: the search's Conditions calls the grammar's when_value and has "
              "no z or band arithmetic of its own")
        h = search_mod.hypothesis_of(cfg, c, {"n_trials": 12, "n": 40},
                                     {"n": 12, "mean_net": 0.001})
        doc = {"schema": hyp.SCHEMA_ID, "batch_id": "d", "source": "systematic",
               "proposer": "alpha/search.py", "channel": "search",
               "written_at": SEARCH_AS_OF, "model_idea_rule": False, "inputs": [],
               "hypotheses": [h]}
        rules.compile_rule(h["rule_dsl"], st)
        check(h["needs_code"] is False and h["rule_dsl"] == rule
              and not hyp.validate_batch(doc),
              "a conditioned survivor registers its v2 rule (rule_dsl, needs_code false), "
              "and it compiles against the store")
        mf = manifest.read(prog["manifest"])["batch"]
        v1cfg = copy.deepcopy(cfg)
        v1cfg["family"]["grammar"] = rules.GRAMMAR
        check(mf["grammar"] == "alpha-lab-rules/v2"
              and mf["spec"]["family"]["grammar"] == "alpha-lab-rules/v2"
              and search_mod.family_sha256(v1cfg) != search_mod.family_sha256(cfg)
              == mf["family_sha256"],
              "the manifest's hash covers the grammar version: the same family on v1 "
              "hashes differently")
    finally:
        search_mod.rules.backtest = real_bt
        st.close()
        lg.close()

    pr = (REPO / "alpha_proposer" / "propose.py").read_text(encoding="utf-8")
    prompt = (REPO / "config" / "alpha_proposer_prompt.md").read_text(encoding="utf-8")
    check('h["rule_dsl"].get("grammar") != rules.GRAMMAR' in pr
          and "alpha-lab-rules/v2" not in prompt and rules.GRAMMAR == "alpha-lab-rules/v1",
          "the proposer stays on v1: its prompt names v1 only, and a v2 rule_dsl from it "
          "is kept as text")

def main() -> int:
    try:
        group_a()
        group_b()
        group_c()
        group_d()
    finally:
        shutil.rmtree(_TMP, ignore_errors=True)
    print(f"\n{PASS} passed, {FAIL} failed")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
