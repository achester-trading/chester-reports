"""
Validation gate for the correlation layer (AQ-5; change order 10 Oct 2026,
sections 5 and 9).

SEEDED, never sampled: every store here is a throwaway, written by this gate with
returns whose correlations are known by construction, so the verdict is about the
commit and is the same in CI, on the laptop and on the box. Nothing here opens the
live store.

  A  SHAPES. The universe is the former eighteen plus SPY, TLT and VIX, all 21
     keyed on symbols the price pass carries; an absent asset would say why; the registry's three bulk blocks hold exactly the
     members the config implies; every corr.* entry is calculated, a narrow flag
     at most, never trigger-eligible, dated, and family-declared; the 3-year
     stock-bond row carries section 5's kill condition; the peer table is
     peers.py's, pair for pair and word for word.
  B  THE ARITHMETIC. The rolling correlation is Pearson's (against
     statistics.correlation); an inverted quote reads as its own price; SPY-TLT
     at 60 days is SR-9's calc.corr_spy_tlt_60d to the digit, so the alias reads
     the same number the matrix would have written.
  C  NO NaN LEAKAGE. A flat stretch, a gap and a non-positive price are seeded;
     nothing stored is NaN or infinite, every correlation is inside [-1, 1], and
     a window over a flat leg writes nothing.
  D  THE BREAK THRESHOLD is signals.py's: |30d - 120d| >= 0.30, toward/away by
     sign, the four credit-sensitive assets; a seeded decoupling fires it and the
     escalation, and the Weekly prints one line.
  E  FLAGS OFF BELOW THE WINDOW. Short histories write no 60-day, 252-day,
     break or shift row; the shift's IQR arm is off below its minimum history;
     the sign arm fires on the twentieth session of a hold and not the
     nineteenth; a quiet week prints nothing in the Weekly.
  F  AS-OF NEVER LATER THAN THE CUTOFF. Every row computed at a cutoff is
     available at or before it, and observed on or before it.
  G  POINT IN TIME. A revision knowable only after the cutoff changes nothing
     computed at the cutoff; every stored value recomputes to the same number
     from only the rows knowable at its own available_at; a row's available_at
     is the latest of its inputs' (a late input makes a late row).
  H  WHERE IT PRINTS. The Weekly's Positioning carries the line only in a week
     something fired and only at the weekly cadence, and the line's shifts are
     the named rows' only (all-pairs shifts stay in the Monthly), two plus a
     count at most; the Monthly's slow layers
     carry the Correlations block -- the stock-bond rows in the triple form with
     the five-year column "until the lenses", the top shifts, and the surprise
     quadrant's hook named and empty.

    python tools/validate_correlation_layer.py
"""

from __future__ import annotations

import ast
import copy
import datetime as dt
import math
import random
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import numpy as np  # noqa: E402
import yaml  # noqa: E402

from altdata import correlation as C, derived, observations  # noqa: E402
from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = 0
FAIL = 0
LINE = "=" * 78
TD = gate_mkdtemp("corr_gate_")


def ok(m: str) -> None:
    global PASS
    PASS += 1
    print(f"  PASS  {m}")


def bad(m: str) -> None:
    global FAIL
    FAIL += 1
    print(f"  FAIL  {m}")


def check(c: bool, m: str) -> None:
    ok(m) if c else bad(m)


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


# ---------------------------------------------------------------------------
# Seeding
# ---------------------------------------------------------------------------
def weekdays(start: dt.date, n: int) -> list[str]:
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def avail(day: str, lag_days: int = 0, hour: int = 21) -> str:
    d = dt.date.fromisoformat(day) + dt.timedelta(days=lag_days)
    return f"{d.isoformat()}T{hour:02d}:00:00+00:00"


def store(name: str) -> observations.ObservationStore:
    return observations.ObservationStore(str(Path(TD) / f"{name}.db"))


def write_prices(st, key: str, days: list[str], rets: list[float],
                 start: float = 100.0, diff: bool = False, lag: int = 0,
                 hour: int = 21) -> None:
    v, rows = start, []
    for i, d in enumerate(days):
        if i:
            v = v + rets[i] if diff else v * math.exp(rets[i])
        rows.append({"registry_key": key, "instrument": None, "observed_at": d,
                     "available_at": avail(d, lag, hour), "value": v,
                     "source": "synthetic", "availability_kind": "reconstructed"})
    st.write_many(rows)


def small_cfg(**over) -> dict:
    """A four-asset universe on the real config's rules, for the fast groups."""
    c = copy.deepcopy(C.config())
    c["universe"] = [
        {"id": "gold", "label": "Gold", "key": "t.gold", "former": True},
        {"id": "em", "label": "EM", "key": "t.em", "former": True},
        {"id": "jpy", "label": "Yen", "key": "t.usdjpy", "former": True, "invert": True},
        {"id": "spy", "label": "SPY", "key": "t.spy"},
        {"id": "tlt", "label": "TLT", "key": "t.tlt"},
        {"id": "china", "label": "China", "former": True, "absent": "no feed"},
    ]
    c["extra_inputs"] = [{"id": "y10", "label": "10y", "key": "t.y10",
                          "transform": "diff"}]
    c["named"] = [{"key": "corr.t.spy_y10.60d", "a": "spy", "b": "y10", "window": 60,
                   "label": "SPY-10y"}]
    c["ratios"] = [{"key": "corr.t.gold_over_em", "num": "gold", "den": "em"}]
    c["aliases"] = {}
    c["peers"] = {}
    c.update(over)
    return c


def seed_small(st, n: int, decouple_em_last: int = 0, seed: int = 7,
               flat_gold: tuple = (), bad_tlt_day: int = -1,
               late_y10: bool = False) -> list[str]:
    rnd = random.Random(seed)
    days = weekdays(dt.date(2023, 1, 2), n)
    f = [rnd.gauss(0, 0.01) for _ in days]
    spy = [x + rnd.gauss(0, 0.004) for x in f]
    em = [0.9 * x + rnd.gauss(0, 0.004) for x in f]
    if decouple_em_last:
        for i in range(n - decouple_em_last, n):
            em[i] = rnd.gauss(0, 0.01)
    gold = [0.2 * x + rnd.gauss(0, 0.01) for x in f]
    for i in flat_gold:
        gold[i] = 0.0
    tlt = [-0.4 * x + rnd.gauss(0, 0.008) for x in f]
    jpy = [-0.3 * x + rnd.gauss(0, 0.005) for x in f]
    y10 = [0.05 * x * 100 + rnd.gauss(0, 0.03) for x in f]
    write_prices(st, "t.spy", days, spy)
    write_prices(st, "t.em", days, em)
    write_prices(st, "t.gold", days, gold)
    write_prices(st, "t.usdjpy", days, jpy, start=150.0)
    write_prices(st, "t.y10", days, y10, start=4.0, diff=True,
                 lag=1 if late_y10 else 0, hour=13 if late_y10 else 21)
    write_prices(st, "t.tlt", days, tlt)
    if bad_tlt_day >= 0:
        st.write_many([{"registry_key": "t.tlt", "instrument": None,
                        "observed_at": days[bad_tlt_day],
                        "available_at": avail(days[bad_tlt_day], 0, 22),
                        "value": -1.0, "source": "synthetic"}])
    return days


def by(rows: list[dict]) -> dict[tuple, dict]:
    return {(r["registry_key"], r["observed_at"]): r for r in rows}


# ---------------------------------------------------------------------------
# A. Shapes
# ---------------------------------------------------------------------------
FORMER = ["gold", "silver", "copper", "oil", "natgas", "agri", "btc", "eth", "sol",
          "zec", "us_re", "intl_re", "em", "china", "dxy", "eur", "jpy", "cny"]


def _peers_py() -> dict:
    tree = ast.parse((REPO / "altdata" / "report" / "peers.py").read_text(
        encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                getattr(t, "id", None) == "PEERS" for t in node.targets):
            return ast.literal_eval(node.value)
    return {}


def _signals_py() -> dict:
    tree = ast.parse((REPO / "altdata" / "report" / "signals.py").read_text(
        encoding="utf-8"))
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            name = getattr(node.targets[0], "id", None)
            if name in ("CORR_BREAK_DELTA", "CORR_SHORT_WIN", "CORR_BASELINE_WIN",
                        "CREDIT_SENSITIVE"):
                out[name] = ast.literal_eval(node.value)
    return out


def group_a() -> None:
    head("A. SHAPES: THE UNIVERSE, THE REGISTRY, THE PEER TABLE")
    cfg = C.config()
    ids = [a["id"] for a in cfg["universe"]]
    check(ids == FORMER + ["spy", "tlt", "vix"],
          "the universe is the former eighteen, in order, plus SPY, TLT and VIX")
    check(len(C.assets(cfg)) == 21 and not C.absent_assets(cfg),
          "all 21 keyed: DBA, ETH-USD, SOL-USD, ZEC-USD, VNQI and MCHI joined the "
          "price basket for agri, eth, sol, zec, intl_re and china")
    from altdata.sources import yfinance_source as yfs            # noqa: PLC0415
    basket = {f"yfinance.{v}" for v in yfs.SYMBOLS.values()}
    check(all(a["key"] in basket for a in C.assets(cfg)
              if a["key"].startswith("yfinance.")),
          "every yfinance key in the universe is a symbol on the price pass")
    vix = next(a for a in cfg["universe"] if a["id"] == "vix")
    check(vix.get("key") == "fred.vix", "VIX is VIXCLS (fred.vix)")
    check(all(a.get("former") for a in cfg["universe"] if a["id"] in FORMER)
          and not any(a.get("former") for a in cfg["universe"]
                      if a["id"] in ("spy", "tlt", "vix")),
          "`former` marks exactly the eighteen")
    gone = C.absent_assets(cfg)
    check(all(isinstance(a.get("absent"), str) and a["absent"] for a in gone),
          f"every asset without a feed says why ({', '.join(a['id'] for a in gone)})")
    check(all(a.get("key") or a.get("absent") for a in cfg["universe"]),
          "every member has a key or a reason, never neither")
    unreg = [a["key"] for a in C.assets(cfg) + list(cfg.get("extra_inputs") or [])
             if not derived.registry_entry(a["key"])]
    check(not unreg, f"every input key is a registered series ({unreg or 'all'})")

    n = len(C.assets(cfg))
    npairs = n * (n - 1) // 2
    mw = cfg["windows"]["matrix"]
    check(len(C.pairs(cfg)) == npairs, f"{npairs} pairs from {n} present assets")
    check(len(C.PAIR_SERIES) == npairs * len(mw) - len(cfg.get("aliases") or {}),
          f"the matrix is every pair at {mw} less the aliases "
          f"({len(C.PAIR_SERIES)})")
    check(len(C.SHIFT_SERIES) == npairs, f"one shift flag per pair ({npairs})")
    nb = len(C.break_assets(cfg)) * len(cfg["break"]["benchmarks"])
    check(len(C.BREAK_SERIES) == nb, f"one break per former asset and benchmark ({nb})")

    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    bulk = reg.get("bulk_imports") or {}
    for bid, attr in (("correlation_matrix", C.PAIR_SERIES),
                      ("correlation_shift_flags", C.SHIFT_SERIES),
                      ("correlation_breaks", C.BREAK_SERIES)):
        b = bulk.get(bid) or {}
        check(b.get("expected_members") == len(attr) and b.get("members_are") == "keys",
              f"{bid}: expected_members {b.get('expected_members')} == {len(attr)}")
    al = cfg.get("aliases") or {}
    for k, target in al.items():
        check(derived.registry_entry(target) and f"corr.{k}" not in C.PAIR_SERIES,
              f"alias {k} -> {target}: registered, and not written twice")

    vocab = reg.get("vocabularies") or {}
    rights = set(vocab.get("rights_ceiling") or [])
    fams = set(vocab.get("family") or [])
    keys = (list(C.PAIR_SERIES) + list(C.SHIFT_SERIES) + list(C.BREAK_SERIES)
            + [x["key"] for x in cfg.get("named") or []]
            + [x["key"] for x in cfg.get("ratios") or []]
            + [cfg["average_pairwise"]["key"]]
            + [f"corr.{k}" for k in cfg.get("named_pairs") or []])
    probs = []
    for k in keys:
        e = derived.registry_entry(k)
        why = []
        if not e:
            why.append("unregistered")
        else:
            if e.get("trigger_eligible") is not False:
                why.append("trigger_eligible not false")
            if e.get("rights_ceiling") != "narrow_flag" or "narrow_flag" not in rights:
                why.append(f"rights_ceiling {e.get('rights_ceiling')!r}")
            if e.get("observation_type") != "calculated":
                why.append("not calculated")
            if e.get("family") not in fams:
                why.append(f"family {e.get('family')!r}")
            if str(e.get("added_date")) != "2026-10-10" or not e.get("long_window"):
                why.append("added_date/long_window")
            if e.get("mechanism_group") != "cross_asset_correlation":
                why.append("mechanism_group")
        if why:
            probs.append(f"{k}: {', '.join(why)}")
    check(not probs, f"all {len(keys)} corr.* series: calculated, narrow flag, "
          f"trigger_eligible false, dated, family-declared"
          + (f" -- {probs[:4]}" if probs else ""))
    named = [x["key"] for x in cfg.get("named") or []] + \
        [f"corr.{k}" for k in cfg.get("named_pairs") or []] + \
        [x["key"] for x in cfg.get("ratios") or []] + [cfg["average_pairwise"]["key"]]
    nodesc = [k for k in named if "Reading rule" not in str(
        (reg["metrics"].get(k) or {}).get("description") or "")
        and k != cfg["average_pairwise"]["key"]]
    check(not nodesc, f"every named row is its own entry with its reading rule "
          f"({nodesc or 'all'})")
    kc = str((reg["metrics"].get("corr.stock_bond.spx_tlt.756d") or {})
             .get("kill_condition") or "")
    check("three-year average CPI" in kc and "drop the inflation" in kc,
          "the 3-year stock-bond row carries section 5's kill condition")
    others = [k for k in named if k != "corr.stock_bond.spx_tlt.756d"
              and (reg["metrics"].get(k) or {}).get("kill_condition")]
    check(not others, "no other row invents a kill condition the order did not rule")

    pp = _peers_py()
    port = {a: [(p["peer"], p["rationale"]) for p in v]
            for a, v in (cfg.get("peers") or {}).items()}
    want = {a: [(p["asset_id"], p["rationale"]) for p in v] for a, v in pp.items()}
    check(bool(pp) and port == want,
          f"config peers are peers.py's PEERS: {len(want)} assets, "
          f"{sum(len(v) for v in want.values())} pairs, order and rationale "
          f"identical")
    check(all(a in ids and p in ids for a, v in port.items() for p, _ in v),
          "every peer pair names two universe members")


# ---------------------------------------------------------------------------
# B. Arithmetic
# ---------------------------------------------------------------------------
def group_b() -> None:
    head("B. THE ARITHMETIC: PEARSON, INVERSION, THE SR-9 ALIAS")
    rnd = random.Random(3)
    x = np.array([rnd.gauss(0, 1) for _ in range(400)])
    y = 0.5 * x + np.array([rnd.gauss(0, 1) for _ in range(400)])
    for w in (30, 60, 252):
        rc = C.rolling_corr(x, y, w)
        worst = max(abs(rc[i] - statistics.correlation(list(x[i:i + w]),
                                                         list(y[i:i + w])))
                    for i in range(0, len(rc), 7))
        check(len(rc) == 400 - w + 1 and worst < 1e-9,
              f"{w}-window rolling correlation is Pearson's (max error {worst:.1e})")
    check(len(C.rolling_corr(x[:59], y[:59], 60)) == 0,
          "fewer returns than the window: nothing")
    sa = {"2026-01-0%d" % i: (100.0 + i, "a", None) for i in range(1, 6)}
    sb = {"2026-01-0%d" % i: (100.0 + i * i, "a", None) for i in range(1, 6)}
    r1 = C.returns(sa, sb)
    r2 = C.returns(sa, sb, ia=True)
    check(np.allclose(r1.x, -r2.x) and np.allclose(r1.y, r2.y),
          "an inverted quote's returns are the negated returns (yen per dollar -> yen)")
    rd = C.returns(sa, sb, "diff", "log_return")
    check(np.allclose(rd.x, [1.0] * 4), "a yield's return is its change in its units")

    from altdata import market_features as mf                   # noqa: PLC0415
    st = store("alias")
    days = weekdays(dt.date(2024, 1, 1), 160)
    rnd = random.Random(11)
    f = [rnd.gauss(0, 0.01) for _ in days]
    write_prices(st, "yfinance.mkt_spy", days, [v + rnd.gauss(0, 0.005) for v in f])
    write_prices(st, "yfinance.mkt_tlt", days, [-0.5 * v + rnd.gauss(0, 0.005)
                                                for v in f])
    ref = {r["observed_at"]: r for r in mf.rates_rows(st)
           if r["registry_key"] == "calc.corr_spy_tlt_60d"}
    c = small_cfg()
    c["universe"] = [{"id": "spy", "label": "SPY", "key": "yfinance.mkt_spy"},
                     {"id": "tlt", "label": "TLT", "key": "yfinance.mkt_tlt"}]
    c["named"], c["ratios"] = [], []
    r = C.Inputs(st, None, c)
    sa, _, _ = r.series("spy")
    sb, _, _ = r.series("tlt")
    mine = C.corr_series(C.returns(sa, sb), 60)
    diff = max(abs(round(mine[d][0], 6) - ref[d]["value"]) for d in ref)
    same_av = all(observations.canonical_instant(mine[d][1])
                  == observations.canonical_instant(ref[d]["available_at"]) for d in ref)
    check(set(mine) == set(ref) and diff == 0.0 and same_av,
          f"SPY-TLT 60d equals calc.corr_spy_tlt_60d on {len(ref)} days, value and "
          f"availability, so the alias reads what the matrix would have written")
    check(C.stored_key("corr.spy__tlt.60d") == "calc.corr_spy_tlt_60d",
          "the matrix cell spy__tlt.60d is read under its alias")
    st.close()


# ---------------------------------------------------------------------------
# C. No NaN leakage
# ---------------------------------------------------------------------------
def group_c() -> None:
    head("C. NO NaN LEAKAGE: A FLAT LEG, A GAP, A NON-POSITIVE PRICE")
    st = store("nan")
    flat = tuple(range(100, 170))
    seed_small(st, 420, flat_gold=flat, bad_tlt_day=200)
    st.conn.execute("DELETE FROM observations WHERE registry_key='t.em' AND "
                    "observed_at IN (SELECT observed_at FROM observations WHERE "
                    "registry_key='t.em' ORDER BY observed_at LIMIT 5 OFFSET 300)")
    st.conn.commit()
    cfg = small_cfg()
    rows = C.compute_rows(st, cfg=cfg)
    vals = [r["value"] for r in rows]
    check(all(isinstance(v, float) and math.isfinite(v) for v in vals),
          f"{len(rows)} rows, none NaN or infinite")
    corr_rows = [r for r in rows if r["registry_key"].endswith(("60d", "252d"))
                 and not r["registry_key"].startswith("corr.t.")]
    check(all(-1.0 <= r["value"] <= 1.0 for r in corr_rows),
          "every correlation is inside [-1, 1]")
    days = weekdays(dt.date(2023, 1, 2), 420)
    flat_window_end = days[169]
    hit = [r for r in rows if r["registry_key"] == "corr.gold__em.60d"
           and r["observed_at"] == flat_window_end]
    check(not hit, "a window over a flat leg writes nothing (its correlation is "
          "undefined, not zero)")
    tlt_days = [r["observed_at"] for r in rows if r["registry_key"] == "corr.spy__tlt.60d"]
    check(any(d < days[200] for d in tlt_days) and any(d > days[262] for d in tlt_days),
          "a non-positive price is skipped, not carried: SPY-TLT windows are written "
          "on both sides of it, every one finite")
    st.close()


# ---------------------------------------------------------------------------
# D. The break
# ---------------------------------------------------------------------------
def group_d() -> None:
    head("D. THE BREAK: signals.py's THRESHOLD, DIRECTION AND ESCALATION")
    sp = _signals_py()
    cfg = C.config()
    check(sp.get("CORR_BREAK_DELTA") == cfg["break"]["delta"] == 0.30
          and sp.get("CORR_SHORT_WIN") == cfg["windows"]["break_short"] == 30
          and sp.get("CORR_BASELINE_WIN") == cfg["windows"]["break_long"] == 120,
          "0.30, 30 days and 120 days -- signals.py's constants, read from its source")
    check(set(sp.get("CREDIT_SENSITIVE") or []) == set(cfg["break"]["credit_sensitive"]),
          "the credit-sensitive set is signals.py's (us_re, intl_re, em, china)")
    check(C.is_break(0.30) and C.is_break(-0.30) and not C.is_break(0.2999)
          and not C.is_break(None),
          "|delta| >= 0.30 is a break; 0.2999 is not; None is not")
    check(C.direction(0.4) == "toward" and C.direction(-0.4) == "away"
          and C.direction(0.0) == "away",
          "positive is toward, otherwise away (signals.py, zero included)")

    st = store("break")
    days = seed_small(st, 300, decouple_em_last=30)
    cfg = small_cfg()
    rows = C.compute_rows(st, cfg=cfg)
    st.write_many(rows)
    last = by(rows).get(("corr.em__spy.break", days[-1]))
    check(last is not None and last["value"] <= -0.30,
          f"EM decoupled from SPY for 30 sessions: 30d - 120d = "
          f"{last and last['value']:+.2f}, a break away")
    calm = by(rows).get(("corr.em__spy.break", days[200]))
    check(calm is not None and abs(calm["value"]) < 0.30,
          f"while EM tracked SPY the delta was {calm and calm['value']:+.2f}: no break")
    now, then = avail(days[-1], 0, 23), avail(days[-6], 0, 23)
    b = C.breaks_between(st, then, now, cfg)
    check(any(x["asset"] == "em" and x["benchmark"] == "spy" and x["direction"] == "away"
              for x in b), "breaks_between finds it in the week")
    check(C.credit_escalation(b, cfg) == ["em"],
          "EM breaking away from SPY is the credit-sensitive escalation")
    line = C.weekly_line(st, now, then, cfg)
    check(line is not None and line["text"].startswith("Correlations: ")
          and "credit-sensitive decoupling from SPY: EM" in line["text"]
          and line["text"].count("\n") == 0,
          f"the Weekly's one line: {line and line['text']!r}")
    st.close()


# ---------------------------------------------------------------------------
# E. Flags off below the window
# ---------------------------------------------------------------------------
def _c(days: list[str], vals: list[float]) -> dict:
    return {d: (v, avail(d), None) for d, v in zip(days, vals)}


def group_e() -> None:
    head("E. FLAGS OFF BELOW THE WINDOW")
    for n, want, absent in ((60, [], ["60d", "252d", "break", "shift"]),
                            (100, ["60d"], ["252d", "break", "shift"]),
                            (125, ["60d", "break"], ["252d", "shift"]),
                            (250, ["60d", "break"], ["252d", "shift"])):
        st = store(f"short{n}")
        seed_small(st, n)
        rows = C.compute_rows(st, cfg=small_cfg())
        kinds = {r["registry_key"].rsplit(".", 1)[-1] for r in rows}
        check(all(k in kinds for k in want) and not any(k in kinds for k in absent),
              f"{n} sessions ({n - 1} returns): writes {want or 'no window'}; "
              f"none of {absent}")
        if n == 100:
            line = C.weekly_line(st, avail(weekdays(dt.date(2023, 1, 2), n)[-1], 0, 23),
                                 "2023-01-01T00:00:00+00:00", small_cfg())
            check(line is None, "a week where nothing can fire prints nothing")
        st.close()

    cfg = small_cfg()
    hold = cfg["shift"]["sign_hold"]
    days = weekdays(dt.date(2020, 1, 1), 300)
    c252 = _c(days, [0.0001] * 300)
    vals = [0.2] * 250 + [-0.2] * 50
    ev = C.shift_eval(_c(days, vals), c252, cfg)
    on = [i for i, d in enumerate(days) if ev[d]["flag"] and "sign" in ev[d]["rule"]]
    check(on == [250 + hold - 1],
          f"the sign arm fires on the {hold}th session of the hold and not before "
          f"(fired at index {on})")
    short = {d: v for d, v in list(_c(days, vals).items())[:200]}
    ev2 = C.shift_eval(short, c252, cfg)
    check(all(e["iqr"] is None for e in ev2.values())
          and not any(e["rule"] in ("crossing", "crossing and sign") for e in ev2.values()),
          f"below {cfg['shift']['iqr_min']} 60-day values the IQR arm is off")
    rnd = random.Random(5)
    base = [0.3 + rnd.gauss(0, 0.02) for _ in range(290)]
    vals3 = base + [0.9] * 10
    long252 = _c(days, [0.5] * 300)
    ev3 = C.shift_eval(_c(days, vals3), long252, cfg)
    e = ev3[days[-1]]
    check(e["flag"] and e["rule"].startswith("crossing") and e["score"] > 1,
          f"a 60-day that crossed the 252-day and is {e['gap']:+.2f} past it "
          f"(IQR {e['iqr']:.2f}) is a crossing shift")
    no_cross = C.shift_eval(_c(days, [0.9] * 300), long252, cfg)[days[-1]]
    check(not no_cross["flag"],
          "a 60-day far from the 252-day that never crossed it is not a crossing")
    missing252 = C.shift_eval(_c(days, vals), {}, cfg)
    check(missing252 == {}, "no 252-day value, no shift row")


# ---------------------------------------------------------------------------
# F / G. As-of and point in time
# ---------------------------------------------------------------------------
def group_fg() -> None:
    head("F. AS-OF NEVER LATER THAN THE CUTOFF")
    st = store("pit")
    days = seed_small(st, 420, late_y10=True)
    cfg = small_cfg()
    cut_day = days[380]
    cutoff = avail(cut_day, 0, 23)
    rows = C.compute_rows(st, as_of=cutoff, cfg=cfg)
    cut = observations.canonical_instant(cutoff)
    late = [r for r in rows if observations.canonical_instant(r["available_at"]) > cut]
    future = [r for r in rows if r["observed_at"] > cut_day]
    check(rows and not late and not future,
          f"{len(rows)} rows at {cut_day}: none available after the cutoff, none "
          f"observed after it")

    head("G. POINT IN TIME")
    before = by(rows)
    st.write_many([{"registry_key": "t.em", "instrument": None,
                    "observed_at": days[370], "available_at": avail(days[400]),
                    "value": 1e6, "source": "revision"}])
    after = by(C.compute_rows(st, as_of=cutoff, cfg=cfg))
    check(after == before,
          "a wild revision knowable only after the cutoff changes nothing computed "
          "at it, to the digit")
    full = C.compute_rows(st, cfg=cfg)
    fb = by(full)
    moved = [k for k, r in fb.items() if k in before and r["value"] != before[k]["value"]]
    check(moved and all(observations.canonical_instant(fb[k]["available_at"])
                        >= observations.canonical_instant(avail(days[400]))
                        for k in moved),
          f"computed after the revision, the {len(moved)} rows it moved are dated "
          f"no earlier than the revision")
    st.write_many(full)
    rnd = random.Random(2)
    sample = rnd.sample(full, 60) + [r for r in full
                                     if r["registry_key"].endswith(("shift", "break"))][-20:]
    bad_rows = []
    cache: dict[str, dict] = {}
    for r in sample:
        a = r["available_at"]
        if a not in cache:
            cache[a] = by(C.compute_rows(st, as_of=a, cfg=cfg))
        again = cache[a].get((r["registry_key"], r["observed_at"]))
        if again is None or again["value"] != r["value"]:
            bad_rows.append((r["registry_key"], r["observed_at"]))
    check(not bad_rows,
          f"{len(sample)} stored values each recompute to the same number from only "
          f"the rows knowable at their own available_at"
          + (f" -- {bad_rows[:3]}" if bad_rows else ""))
    y_row = fb.get(("corr.t.spy_y10.60d", days[300]))
    check(y_row is not None and observations.canonical_instant(y_row["available_at"])
          == observations.canonical_instant(avail(days[300], 1, 13)),
          "a row reading a next-morning input (the 10-year at 13:00 next day) is "
          "available when that input was, not at the close")
    av_rows = [r for r in full if r["registry_key"] == C.config()["average_pairwise"]["key"]]
    check(bool(av_rows) and all(0.0 <= r["value"] <= 1.0 for r in av_rows),
          f"the average pairwise |correlation| is written ({len(av_rows)} days) "
          f"inside [0, 1]")
    res = C.compute(store=st, backfill=True)
    check(res["written"] == 0 and res["changed"] == 0,
          f"a re-run writes nothing ({res['computed']} recomputed, 0 changed): "
          f"no vintage for an unchanged value")
    st.close()


# ---------------------------------------------------------------------------
# H. Where it prints
# ---------------------------------------------------------------------------
def seed_universe(st, n: int, decouple: bool) -> list[str]:
    cfg = C.config()
    rnd = random.Random(21)
    days = weekdays(dt.date(2024, 1, 1), n)
    f = [rnd.gauss(0, 0.01) for _ in days]
    keys = [a["key"] for a in C.assets(cfg)] + [a["key"] for a in cfg["extra_inputs"]]
    for k in sorted(set(keys)):
        beta = rnd.uniform(-0.8, 0.8)
        rets = [beta * x + rnd.gauss(0, 0.008) for x in f]
        if decouple and k == "yfinance.mkt_eem":
            # EM tracks SPY, then turns against it for the last 30 sessions.
            rets = [0.9 * x + rnd.gauss(0, 0.003) for x in f[:-30]] + \
                   [-0.5 * x + rnd.gauss(0, 0.006) for x in f[-30:]]
        if k == "yfinance.mkt_spy":
            rets = [x + rnd.gauss(0, 0.003) for x in f]
        diff = k == "fred.yield_10y"
        write_prices(st, k, days, [r * 10 for r in rets] if diff else rets,
                     start=4.0 if diff else 100.0, diff=diff)
    return days


def group_h() -> None:
    head("H. WHERE IT PRINTS: THE WEEKLY'S LINE, THE MONTHLY'S BLOCK")
    from daily_cascade import weekly_stack as ws                  # noqa: PLC0415
    from monthly_macro import stack as ms                         # noqa: PLC0415
    st = store("universe")
    days = seed_universe(st, 400, decouple=True)
    res = C.compute(store=st, backfill=True)
    check(res["written"] > 0, f"the full v1 universe computes ({res['written']} rows)")
    now, then = avail(days[-1], 0, 23), avail(days[-6], 0, 23)
    pos = ws.positioning_week(st, now, then)
    subs = [s for s in pos["subsections"] if s.get("title") == "Cross-asset correlations"]
    cd = pos["data"].get("correlations") or {}
    check(len(subs) == 1 and len(subs[0]["lines"]) == 1
          and subs[0]["lines"][0].startswith("Correlations: ")
          and any(b["asset"] == "em" and b["benchmark"] == "spy"
                  and b["direction"] == "away" for b in cd.get("breaks") or [])
          and cd.get("credit_sensitive_away") == ["em"]
          and "credit-sensitive decoupling from SPY: Emerging markets"
          in subs[0]["lines"][0],
          f"the Weekly's Positioning carries one line in a week a break fired: "
          f"{subs and subs[0]['lines'][0][:110]!r}")
    check(bool(cd) and all(isinstance(s["pair"], list) for s in cd["shifts"]),
          "the line's breaks and shifts are in the section's data")
    # THE WEEKLY'S SCOPE (ruled 10 Oct 2026): breaks, and shifts on the named
    # rows only. All-pairs shifts are the Monthly's top five.
    named = set(C.weekly_shift_pairs())
    check(named == {("btc", "spy"), ("gold", "spy"), ("gold", "dxy"), ("oil", "dxy")}
          and all(f"{a}__{b}.60d" in (C.config().get("named_pairs") or [])
                  or f"{b}__{a}.60d" in (C.config().get("named_pairs") or [])
                  for a, b in named),
          "the Weekly's shift pairs are the named rows' matrix pairs (BTC-SPY, "
          "gold-SPY, gold-DXY, oil-DXY)")
    all_sh = C.shifts_between(st, then, now)
    outside = [x for x in all_sh if tuple(x["pair"]) not in named]
    check(bool(outside) and all(tuple(x["pair"]) in named for x in cd["shifts"]),
          f"{len(outside)} all-pairs shift(s) fired outside the named rows this "
          f"week; the line carries none of them ({len(cd['shifts'])} named)")
    c2 = copy.deepcopy(C.config())
    c2["weekly"]["shift_pairs"] = [f"{a}__{b}" for a, b in
                                   (x["pair"] for x in outside[:3])]
    l2 = C.weekly_line(st, now, then, c2) or {}
    got = {tuple(x["pair"]) for x in l2.get("shifts") or []}
    want = {tuple(x["pair"]) for x in outside[:3]}
    cap = c2["weekly"]["shifts_shown"]
    check(got == want and cap == 2
          and (len(want) <= cap or f"and {len(want) - cap} more" in l2.get("text", "")),
          f"a pair the config names does reach the line; shifts cap at {cap} plus a "
          f"count ({len(want)} named: {l2.get('text', '')[-90:]!r})")
    c3 = copy.deepcopy(C.config())
    c3["weekly"]["shift_pairs"] = []
    l3 = C.weekly_line(st, now, then, c3) or {}
    check(not l3.get("shifts") and bool(l3.get("breaks")),
          "with no named shift the line still reports the week's breaks")
    mon = ws.positioning_week(st, now, then, cadence="monthly")
    check(not any(s.get("title") == "Cross-asset correlations"
                  for s in mon["subsections"]),
          "the Monthly's Positioning never carries the Weekly's line")
    st.close()

    quiet = store("universe_quiet")
    qdays = seed_universe(quiet, 110, decouple=False)
    C.compute(store=quiet, backfill=True)
    qpos = ws.positioning_week(quiet, avail(qdays[-1], 0, 23), avail(qdays[-6], 0, 23))
    check(not any(s.get("title") == "Cross-asset correlations"
                  for s in qpos["subsections"]),
          "a week with no break and no shift prints nothing at all")
    quiet.close()

    st = store("universe")
    month_then = avail(days[-22], 0, 23)
    blk = ms.correlations_block(st, now, month_then)
    t = blk["table"]
    check(blk["title"] == "Correlations" and t["columns"] == ms.CORR_COLUMNS
          and len(t["rows"]) == 4
          and any("three years" in x and "no correlation stored" in x
                  for x in blk["not_tracked"]),
          f"the stock-bond rows in the triple form ({len(t['rows'])} rows; the "
          f"three-year row, 756 sessions, is not yet full and says so)")
    check(all(r[-1] == "until the lenses" for r in t["rows"])
          and all("(" in r[1] and r[1].endswith(")") for r in t["rows"]),
          "each row prints its data-as-of; the five-year column reads "
          "'until the lenses'")
    tops = (blk.get("tables") or [{}])[0].get("rows") or []
    check(len(tops) <= 5 and len(blk["data"]["shifts"]) == len(tops),
          f"the top shifts, at most five ({len(tops)} of "
          f"{blk['data']['shifts_flagged']} flagged)")
    check(any("surprise quadrant" in x and "item 25" in x for x in blk["not_tracked"])
          and C.surprise_quadrant(st, now) is None,
          "the surprise quadrant's hook is named and returns no data")
    slow = ms.slow_layers({"as_of": now, "report_date": days[-1]}, {}, st, now)
    check(any(s.get("title") == "Correlations" for s in slow["subsections"])
          and slow["data"].get("correlations") is not None,
          "the slow layers carry the Correlations block and its data")
    check(not any(s.get("charts_rendered") or s.get("charts")
                  for s in slow["subsections"] if s.get("title") == "Correlations"),
          "no chart in this round (the cap of 12 stands)")
    st.close()


def main() -> int:
    for g in (group_a, group_b, group_c, group_d, group_e, group_fg, group_h):
        try:
            g()
        except Exception as exc:                                 # noqa: BLE001
            import traceback
            traceback.print_exc()
            bad(f"{g.__name__} crashed: {type(exc).__name__}: {exc}")
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("FAILED")
        return 1
    print("PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
