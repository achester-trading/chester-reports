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


def main() -> int:
    try:
        group_a()
    finally:
        shutil.rmtree(_TMP, ignore_errors=True)
    print(f"\n{PASS} passed, {FAIL} failed")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
