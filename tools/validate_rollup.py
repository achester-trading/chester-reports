#!/usr/bin/env python3
"""
Validation gate for EL-2: the cross-book exposure roll-up, made explicit.
(docs/change-order-enterprise-layer-2026-09-27.md §3.2; the Operating Doctrine
§4.5 and Rule 16.)

    python tools/validate_rollup.py

Against a TEMPORARY database with synthetic prices and a synthetic market-state
history. No network, no box, no register but its own.

  A  THE FOUR-PACKET ACCEPTANCE TEST, as the specification writes it: long NVDA,
     long QQQ, long NVDA again via options, short Nasdaq vol. Each is sensible
     alone. The gate answers approve, approve, resize, restructure, and its
     refusal of the fourth NAMES the technology and the vega concentration the
     four sum to -- and the technology cluster they are counted once in.
  B  THE LIMITS ARE CONFIG. Every limit the roll-up checks is read from
     config/risk_limits.yaml with its provenance, and moving one in a copy moves
     the gate's answer: no limit is a constant in code.
  C  THE VOCABULARY. The gate's outcomes are DTH §XIV's six words, each folds
     into a `review_changed` word, the register refuses any other, and the
     gate's verdict is recorded on the decision through decide.py.
  D  CORRELATED POSITIONS COUNTED ONCE (§4.5's heat rule). The Doctrine's own
     example -- two long technology names in Book B and a long Nasdaq call spread
     in Book C -- is one position; the same risk in three unrelated factors is
     three; the heat cap sums Books B-D and only those; offsetting legs earn no
     credit; a heat-book decision without its dollars at risk is delayed.
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import contextlib
import copy
import datetime as dt
import io
import json
import os
import random
import sys
from pathlib import Path

import os as _gt_os                                            # noqa: E402
import sys as _gt_sys                                          # noqa: E402
_gt_dir = _gt_os.path.dirname(_gt_os.path.abspath(__file__))
_gt_sys.path.insert(0, _gt_dir if _gt_os.path.basename(_gt_dir) == "tools"
                    else _gt_os.path.join(_gt_dir, "tools"))
from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_TMP = gate_mkdtemp(prefix="validate_rollup_")
DB = os.path.join(_TMP, "rollup.sqlite")
os.environ["CHESTER_DB"] = DB
os.environ.setdefault("CHESTER_STATE_DIR", _TMP)

import regime  # noqa: E402
from altdata import observations  # noqa: E402
from register import heat  # noqa: E402
from register.store import (GATE_OUTCOMES, GATE_TO_REVIEW, REVIEW_CHANGED,  # noqa: E402
                            Register, review_from_gate)
from packet_fixture import FALSIFIER, PACKET_CLI, PACKET_FULL  # noqa: E402

PASS = 0
FAIL = 0
LINE = "=" * 78


def check(c: bool, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


END = dt.date(2026, 9, 25)
# Each name's daily return is this multiple of SPY's, plus its own noise.
LOADINGS = {"spy": 1.0, "qqq": 1.2, "nvda": 2.0, "xlk": 1.3, "xle": 0.8,
            "xlf": 1.1, "iwm": 1.2, "tlt": -0.3}


def weekdays(n: int, end: dt.date = END) -> list[str]:
    out, d = [], end
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d -= dt.timedelta(days=1)
    return list(reversed(out))


def seed(store) -> None:
    """Synthetic closes for the basket, and an Expansion dial for the band."""
    rnd = random.Random(11)
    days = weekdays(300)
    px = {k: 100.0 for k in LOADINGS}
    rows = []
    for d in days:
        r = rnd.gauss(0.0004, 0.01)
        for k, b in LOADINGS.items():
            px[k] *= 1 + b * r + (0 if k == "spy" else rnd.gauss(0, 0.003))
            rows.append({"registry_key": f"yfinance.mkt_{k}", "instrument": None,
                         "observed_at": d, "available_at": f"{d}T21:00:00+00:00",
                         "value": round(px[k], 4), "source": "synthetic"})
    store.write_many(rows)
    for d in weekdays(12):
        obj = {"object": "market_state", "session": d,
               "computed_at": f"{d}T20:50:00+00:00",
               "dials": {"macro": {"state": "expansion"}}, "dimensions": {},
               "contradictions": []}
        store.write(regime.STORE_KEY, None, d, obj["computed_at"],
                    json.dumps(obj), source="derived_state")


def pkt(i, root, book, direction, notional, risk, fam="outright", vega=None):
    return {"id": f"p{i}", "instrument": root, "book": book,
            "direction": direction, "notional_usd": notional, "risk_usd": risk,
            "vega_usd": vega, "expression_family": fam, "leverage_form": "none"}


def scaled(p: dict, f: float) -> dict:
    """A packet accepted at a resize: its size, risk and vega all scale."""
    q = dict(p)
    for k in ("notional_usd", "risk_usd", "vega_usd"):
        if q.get(k) is not None:
            q[k] = q[k] * f
    return q


# The specification's four packets, at sizes a desk would call sensible.
FOUR = [
    pkt(1, "NVDA", "B", "long", 40000, 1200),                       # long NVDA
    pkt(2, "QQQ", "A", "long", 60000, None),                        # long QQQ
    pkt(3, "NVDA", "C", "long", 30000, 1500, fam="vertical_spread",
        vega=300),                                                  # NVDA again, via options
    pkt(4, "QQQ", "D", "short", 0.0, 2500, fam="iron_condor",
        vega=-2000),                                                # short Nasdaq vol
]


def run_four(store, lim=None):
    book, outs = [], []
    for p in FOUR:
        g = heat.gate(p, book, store, limits=lim)
        outs.append(g)
        if g["outcome"] == "approve":
            book.append(p)
        elif g["outcome"] == "resize":
            book.append(scaled(p, g["resize_factor"]))
    return outs, book


# ---------------------------------------------------------------------------
def group_a(store) -> None:
    print(f"{LINE}\nA. THE FOUR-PACKET ACCEPTANCE TEST (EL-2 §3.2)\n{LINE}")
    outs, book = run_four(store)
    for p, g in zip(FOUR, outs):
        print(f"        {p['instrument']:<5} book {p['book']} "
              f"{p['expression_family']:<16} -> {g['outcome']}"
              + (f" ({g['resize_factor']:.0%})" if g.get("resize_factor") else ""))
        for r in g["reasons"]:
            print(f"            - {r}")
    words = [g["outcome"] for g in outs]
    check(words == ["approve", "approve", "resize", "restructure"],
          f"each packet is sensible alone; summed, the gate answers approve, "
          f"approve, resize, restructure ({words})")
    third = outs[2]
    check(any("sector:technology" in r for r in third["reasons"])
          and 0.25 <= (third["resize_factor"] or 0) < 1,
          f"the third (NVDA again, via options) is resized to the room left "
          f"under the technology limit ({third['resize_factor']})")
    fourth = " | ".join(outs[3]["reasons"])
    check("vega" in fourth and "QQQ" in fourth,
          "the refusal of the fourth NAMES the vega concentration, in the "
          "underlying that carries it")
    check("concentration: technology" in fourth,
          "and NAMES the technology concentration the four sum to")
    check("technology counted once: NVDA (B), NVDA (C), QQQ (D)" in fourth,
          "and the technology cluster they are counted once in: NVDA (B), "
          "NVDA (C), QQQ (D) are one position")
    v = outs[3]["view_after"]
    check(set(v["beta_by_book_usd"]) == {"A", "B", "C", "D"},
          f"the roll-up sums across Books A-D "
          f"({', '.join(sorted(v['beta_by_book_usd']))})")
    check(v["vega_by_root_usd"].get("NVDA", 0) > 0
          and v["vega_by_root_usd"].get("QQQ", 0) < 0,
          "and every options expression's vega, signed, by underlying")
    check(abs(v["sectors_usd"].get("technology", 0)) > 0
          and v["net_beta_usd"] > 0 and "duration_usd_per_100bp" in v,
          "beta-adjusted notional vs SPY, sector and duration all summed")
    print("\n" + "\n".join("        " + ln for ln in
                           heat.format_view(v).splitlines()))


def group_b(store) -> None:
    print(f"{LINE}\nB. THE LIMITS ARE CONFIG\n{LINE}")
    lim = heat.load_limits()
    L = lim["limits"]
    check(L["sector_max_pct"]["value"] == 30
          and L["vega_max_pct_per_vol_pt"]["value"] == 0.5
          and L["duration_max_pct_per_100bp"]["value"] == 5
          and L["net_beta_over_band_top_pct"]["value"] == 15
          and L["net_beta_over_band_top_pct"]["source"] == "doctrine",
          "sector 30%, vega 0.5%/pt, duration 5%/100bp, net beta band top + 15 "
          "(the Doctrine's), as ratified")
    h = L.get("heat_max_pct") or {}
    check(h.get("value") == 6 and h.get("source") == "doctrine"
          and h.get("books") == ["B", "C", "D"] and not h.get("proposed"),
          "the heat cap is the Doctrine's: 6% of capital across Books B, C, D")
    c = L.get("cluster_max_pct") or {}
    cf = lim.get("common_factor") or {}
    check(c.get("value") == 1.5 and c.get("proposed") is True
          and cf.get("min_weight") == 0.5 and cf.get("proposed") is True,
          "one position's limit for a cluster (1.5%) and the common-factor rule "
          "(a sector at >= 50%) are in config, marked PROPOSED")
    for name, path, val, word in (
            ("vega", ("limits", "vega_max_pct_per_vol_pt"), 1.0, "approve"),
            ("sector", ("limits", "sector_max_pct"), 40, "approve")):
        moved = copy.deepcopy(lim)
        moved[path[0]][path[1]]["value"] = val
        outs, _ = run_four(store, moved)
        idx = 3 if name == "vega" else 2
        check(outs[idx]["outcome"] == word,
              f"moving the {name} limit in a copy moves the gate: packet "
              f"{idx + 1} -> {outs[idx]['outcome']}")
    moved = copy.deepcopy(lim)
    moved["limits"]["cluster_max_pct"]["value"] = 0.8
    outs, _ = run_four(store, moved)
    check(outs[2]["outcome"] in ("resize", "reject")
          and any("cluster:technology" in r for r in outs[2]["reasons"]),
          f"and the cluster limit binds where it is set: at 0.8% the NVDA "
          f"options packet is held by the technology cluster "
          f"({outs[2]['outcome']})")
    src = (REPO / "register" / "heat.py").read_text(encoding="utf-8")
    check("6000" not in src and "18000" not in src and "4500" not in src,
          "no limit's dollar figure is written into register/heat.py")


def group_c(store) -> None:
    print(f"{LINE}\nC. THE VOCABULARY, RECORDED IN review_changed\n{LINE}")
    check(GATE_OUTCOMES == ("approve", "resize", "restructure", "hedge", "delay",
                            "reject"),
          "the gate's outcomes are DTH §XIV's six words, in order")
    check(set(GATE_TO_REVIEW) == set(GATE_OUTCOMES)
          and set(GATE_TO_REVIEW.values()) <= set(REVIEW_CHANGED)
          and review_from_gate("restructure") == "restructured"
          and review_from_gate("approve") == "none",
          "each folds into a review_changed word (restructure -> restructured, "
          "approve -> none)")
    seen = set()
    cases = [
        (pkt(30, "SPY", "B", "long", 10000, 200), []),
        (pkt(31, "SPY", "B", "long", None, 200), []),
        (pkt(32, "QQQ", "D", "short", 0.0, 2000, fam="iron_condor", vega=-2500), []),
        (pkt(33, "SPY", "B", "long", 20000, 300),
         [pkt(34, "SPY", "A", "long", 280000, None)]),
        (pkt(35, "NVDA", "B", "long", 10000, 200),
         [pkt(36, "NVDA", "C", "long", 89000, 1000)]),
        (pkt(37, "NVDA", "B", "long", 30000, 200),
         [pkt(38, "NVDA", "C", "long", 70000, 1000)]),
    ]
    for cand, book in cases:
        seen.add(heat.gate(cand, book, store)["outcome"])
    check(seen == set(GATE_OUTCOMES),
          f"every one of the six is reachable, and nothing else is "
          f"({', '.join(sorted(seen))})")
    import tempfile
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        with Register(os.path.join(td, "v.db")) as reg:
            try:
                reg.record(instrument="SPY", direction="long", thesis="t",
                           edge_type="positioning", horizon="swing",
                           invalidation="x", status="draft",
                           gate_outcome="shrink")
                refused = False
            except ValueError:
                refused = True
            try:
                reg.record(instrument="SPY", direction="long", thesis="t",
                           edge_type="positioning", horizon="swing",
                           invalidation="x", status="draft",
                           review_changed="trimmed")
                refused2 = False
            except ValueError:
                refused2 = True
    check(refused and refused2,
          "the register refuses a gate outcome or a review_changed outside the "
          "vocabulary")

    # THROUGH THE OPERATOR'S CLI, on this gate's own temporary register: the
    # first three packets are open, the fourth is requested active, and the
    # gate's verdict is recorded on it.
    import decide
    decide.freshness.check_signals = lambda s, i: {
        "verdicts": [], "blocked": False, "blocked_reason": None, "stale": []}
    _, book = run_four(store)
    with Register(DB) as reg:
        for p in book:
            reg.record(instrument=p["instrument"], direction=p["direction"],
                       thesis="fixture", edge_type="positioning",
                       horizon="swing", invalidation="a close below 95",
                       status="active", book=p["book"],
                       notional_usd=p["notional_usd"], vega_usd=p["vega_usd"],
                       risk_usd=p["risk_usd"],
                       expression_family=p["expression_family"],
                       leverage_form="none", falsifiers=[FALSIFIER],
                       counter_thesis="fixture counter-thesis",
                       gate_outcome="approve", **PACKET_FULL)
    buf = io.StringIO()
    saved = sys.argv
    sys.argv = ["decide.py", "--db", DB, "record", "--instrument", "QQQ",
                "--direction", "short", "--thesis", "short Nasdaq vol into a calm tape",
                "--edge-type", "positioning", "--horizon", "swing",
                "--invalidation", "a close above 560", "--signals-used",
                "yfinance.mkt_qqq", "--status", "active", "--book", "D",
                "--expression-family", "iron_condor", "--leverage-form", "none",
                "--notional", "0", "--vega", "-2000", "--risk-usd", "2500",
                "--falsifier", FALSIFIER, "--counter-thesis", "vol is cheap",
                *PACKET_CLI, "--size", "4 condors"]
    try:
        with contextlib.redirect_stdout(buf):
            rc = decide.main()
    finally:
        sys.argv = saved
    out = buf.getvalue()
    with Register(DB) as reg:
        rows = [dict(r) for r in reg.conn.execute(
            "SELECT * FROM decisions WHERE instrument = 'QQQ' AND book = 'D'")]
    last = rows[-1] if rows else {}
    check("GATE: RESTRUCTURE" in out and "concentration: technology" in out
          and "vega" in out,
          f"decide.py prints the gate's refusal naming technology and vega "
          f"(rc {rc})")
    check(last.get("gate_outcome") == "restructure"
          and last.get("review_changed") == "restructured"
          and last.get("status") == "draft" and last.get("risk_usd") == 2500,
          f"and records it: gate_outcome restructure, review_changed "
          f"restructured, held at draft, risk_usd 2,500 "
          f"({last.get('gate_outcome')}, {last.get('review_changed')}, "
          f"{last.get('status')}, {last.get('risk_usd')})")


def group_d(store) -> None:
    print(f"{LINE}\nD. CORRELATED POSITIONS COUNTED ONCE (§4.5)\n{LINE}")
    ref = heat.load_reference()
    lim = heat.load_limits()
    check(heat.common_factor("NVDA", ref, lim) == "technology"
          and heat.common_factor("XLK", ref, lim) == "technology"
          and heat.common_factor("QQQ", ref, lim) == "technology"
          and heat.common_factor("SPY", ref, lim) == "SPY"
          and heat.common_factor("IWM", ref, lim) == "IWM",
          "NVDA, XLK and QQQ share the technology factor; SPY and IWM, with no "
          "sector at half their weight, are their own")
    # The Doctrine's example: two long technology names in Book B and a long
    # Nasdaq call spread in Book C. 1,800 at risk each, 0.6% of capital.
    tech = [pkt(40, "NVDA", "B", "long", 20000, 1800),
            pkt(41, "XLK", "B", "long", 20000, 1800)]
    g = heat.gate(pkt(42, "QQQ", "C", "long", 20000, 1800,
                      fam="vertical_spread", vega=150), tech, store)
    print(f"        QQQ call spread beside NVDA and XLK -> {g['outcome']}: "
          f"{g['reasons'][0]}")
    check(g["outcome"] == "resize" and g["resize_factor"] == 0.5
          and any("cluster:technology" in r for r in g["reasons"]),
          f"the Doctrine's example is ONE position: three 0.6% risks sum to "
          f"1.8% against one position's 1.5%, and the third fits at 50% "
          f"({g['outcome']}, {g.get('resize_factor')})")
    check(any("technology counted once: NVDA (B), XLK (B), QQQ (C)" in r
              for r in g["reasons"]),
          "and the refusal names the cluster's members")
    spread = [pkt(43, "NVDA", "B", "long", 20000, 1800),
              pkt(44, "XLE", "B", "long", 20000, 1800)]
    g = heat.gate(pkt(45, "TLT", "C", "long", 20000, 1800), spread, store)
    v = g["view_after"]
    check(g["outcome"] == "approve" and len(v["clusters"]) == 3
          and v["heat_usd"] == 5400,
          f"the same risk in three unrelated factors is three positions: heat "
          f"5,400 (1.8%), no cluster limit ({g['outcome']})")
    g = heat.gate(pkt(46, "QQQ", "C", "long", 20000, 1800),
                  [pkt(47, "NVDA", "B", "short", 20000, 1800),
                   pkt(48, "XLK", "B", "long", 20000, 1800)], store)
    check(g["view_after"]["clusters"]["technology"]["risk_usd"] == 5400
          and g["outcome"] != "approve",
          "an offsetting leg earns no credit: a short NVDA's risk adds to the "
          "technology cluster, gross")
    g = heat.gate(pkt(49, "QQQ", "A", "long", 20000, None), tech, store)
    v = g["view_after"]
    check(g["outcome"] == "approve" and v["heat_usd"] == 3600
          and v["clusters"]["technology"]["members"] == ["NVDA (B)", "XLK (B)"],
          "Book A is outside heat: its QQQ adds no risk and joins no cluster, "
          "and it needs no risk_usd")
    five = [pkt(50, "NVDA", "B", "long", 15000, 4000),
            pkt(51, "XLE", "B", "long", 15000, 4000),
            pkt(52, "TLT", "C", "long", 15000, 4000),
            pkt(53, "IWM", "C", "long", 15000, 4000)]
    g = heat.gate(pkt(54, "XLF", "D", "long", 15000, 4000), five, store)
    print(f"        a fifth unrelated 4,000 risk -> {g['outcome']}: "
          f"{g['reasons'][0]}")
    check(g["outcome"] == "resize" and g["resize_factor"] == 0.5
          and any(r.startswith("heat:") for r in g["reasons"])
          and any("concentration: heat" in r for r in g["reasons"]),
          f"the heat cap: five unrelated 4,000 risks are 20,000 against "
          f"18,000, and the fifth fits at 50%, named as heat "
          f"({g['outcome']}, {g.get('resize_factor')})")
    g = heat.gate(pkt(55, "NVDA", "B", "long", 15000, None), [], store)
    check(g["outcome"] == "delay" and "risk_usd" in g["reasons"][0],
          "a Book B-D decision without its dollars at risk is delayed, named")
    g = heat.gate(pkt(57, "TLT", "C", "long", 30000, 900), [], store)
    check(g["outcome"] == "approve"
          and g["view_after"]["duration_usd_per_100bp"] > 0,
          f"a rate instrument is classified by its duration, not delayed for "
          f"want of an equity sector ({g['outcome']})")
    v = heat.view([pkt(56, "NVDA", "B", "long", 15000, None)], store)
    check(any("risk_usd" in m for m in v["missing"]),
          "and an open one is listed as heat's missing input, never as zero risk")


def main() -> int:
    st = observations.ObservationStore(DB)
    try:
        seed(st)
        group_a(st)
        group_b(st)
        group_c(st)
        group_d(st)
    finally:
        st.close()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
