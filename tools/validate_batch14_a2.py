#!/usr/bin/env python3
"""
Validation gate: signal triage Batch 14, Part A2 -- items 63 and 66 (written as 56
and 59; ruled 20 Oct 2026 with F1-F8; b52-batch14-a2). Synthetic fixtures only; no
network, no model, no live store.

  A  THE REFERENCE TABLE. BNP Paribas's $100 (August 2026): the buckets sum to 100,
     each bucket's parts to the bucket, wafer-fab equipment about 8 inside semis;
     dated, sourced, and its caveat ("high-level estimates") printed with it.
  B  THE PROXIES. Every bucket maps to basket keys with a reason; every key is in
     the price basket and registered; no Brookfield instrument; the single names
     are CAPEX_CHAIN_SYMBOLS, equities and not earnings names.
  C  THE RELATIVE LINE. On a synthetic store: each bucket's equal-weight basket over
     the window against SPY, ranked lead to lag; a bucket without history listed
     with its reason; the hyperscalers' filed capex growth beside it and guidance
     "not tracked"; no ISO date in a printed line.
  D  THE IMPULSE. Z.1's share times SPX's year-on-year return; the quarter's own
     share at its quarter-end, the share marked to SPX between releases (labelled),
     by its formula; absent with its reason.
  E  THE NET-TRANSMISSION LINE. The four legs side by side, each saying how it is
     scaled; none weighted or summed; the K-shape gap named.
  F  THE LEDGER. The pre-registration is held to its SHA-256; the study applies it
     (INSUFFICIENT below n 40; a fixture built to pass passes and one built to fail
     fails); the script opens no store.
  G  NO VENDOR VALUE, NO BY-HAND KEY, AND THE WIRING. The new modules read neither;
     the Monthly calls the three blocks; JDI Research's voices source is declared
     under F4 (its feed, its kind, its tier).

    python tools/validate_batch14_a2.py
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "tools" / "calibration"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

TD = Path(gate_mkdtemp("batch14_a2_"))
LINE = "=" * 78
PASS = FAIL = 0
PREREG = REPO / "docs" / "ledgers" / "wealth-effect-preregistration-2026-10.md"
PREREG_SHA = "2358f4ceec95c81144e7a8255bffa1a152914bf309f5022884dd37b73a3cecc5"
CUT = "2026-10-21T00:00:00+00:00"
ISO = re.compile(r"\b20\d\d-\d\d-\d\d\b")


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


def sessions(start: str, end: str) -> list[str]:
    d, e, out = dt.date.fromisoformat(start), dt.date.fromisoformat(end), []
    while d <= e:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def write_series(st, key: str, days: list[str], values: list[float], inst=None) -> None:
    for d, v in zip(days, values):
        st.write(key, inst, d, f"{d}T21:00:00+00:00", v, "fixture")


def ramp(days: list[str], start: float, total_pct: float) -> list[float]:
    """Closes growing geometrically by total_pct over the whole span."""
    n = len(days) - 1
    g = (1.0 + total_pct / 100.0) ** (1.0 / max(n, 1))
    return [start * g ** i for i in range(len(days))]


def group_a() -> None:
    from altdata import capex_chain as cc                       # noqa: PLC0415
    head("A. THE REFERENCE TABLE: BNP PARIBAS'S $100, DATED AUGUST 2026")
    ref = cc.reference()
    b = {r["id"]: r["usd"] for r in ref["rows"] if r["level"] == "bucket"}
    parts: dict[str, float] = {}
    for r in ref["rows"]:
        if r["level"] == "part":
            parts[r["of"]] = parts.get(r["of"], 0.0) + r["usd"]
    check(b == {"semis": 50.0, "power": 20.0, "networking": 15.0, "cooling": 7.5,
                "facilities": 7.5} and ref["total"] == 100.0,
          f"the five buckets as BNP sets them, summing to $100 ({b})")
    check(parts == {"semis": 50.0, "power": 20.0}
          and {r["id"]: r["usd"] for r in ref["rows"] if r["level"] == "part"}
          == {"accelerators": 25.0, "memory": 15.0, "cpus_servers": 10.0,
              "grid_generation": 10.0, "distribution": 6.5, "onsite_routing": 3.5},
          "each bucket's parts sum to the bucket (semis 25/15/10, power 10/6.5/3.5)")
    m = {x["id"]: x for x in ref["memo"]}
    check(m.get("wfe", {}).get("usd") == 8.0 and m["wfe"]["approx"]
          and "lithography" in (m["wfe"].get("note") or ""),
          "wafer-fab equipment about $8 inside semis, roughly half of it lithography")
    check(ref["dated"] == "2026-08" and "BNP Paribas" in ref["source"]
          and "high-level estimates" in ref["caveat"],
          f"dated {ref['dated']}, sourced to BNP Paribas, its caveat with it")
    tbl = cc.reference_table(ref)
    check("BNP Paribas, 2026-08" in tbl["columns"][0] and len(tbl["rows"]) == 12,
          "the table prints its source and date in its head, eleven rows and the memo")
    from daily_cascade import capex_chain_block as cb            # noqa: PLC0415
    s = cb.slow_subsection()
    check(s and "high-level estimates" in s["lines"][0] and s["paragraph_wanted"] is False,
          "Factor I's exhibit prints the caveat beside the table, no paragraph")


def group_b() -> None:
    import yaml                                                 # noqa: PLC0415
    from altdata import capex_chain as cc, derived, security_master  # noqa: PLC0415
    from altdata.sources import yfinance_source as yf           # noqa: PLC0415
    head("B. THE PROXIES: EACH BUCKET MAPPED, EVERY KEY IN THE BASKET AND REGISTERED")
    cfg = cc.config()
    prox = cfg["proxies"]
    buckets = [b["id"] for b in cfg["reference"]["buckets"]]
    check(all(prox.get(b, {}).get("keys") and prox[b].get("reason") for b in buckets)
          and prox["memo"]["wfe"]["keys"],
          f"every bucket has its proxies and a reason ({buckets})")
    keys = set()
    for b, p in prox.items():
        for k in p.get("keys") or []:
            keys.add(k)
        for sub in (p.get("parts") or {}).values():
            keys |= set(sub["keys"])
        if b == "memo":
            for sub in p.values():
                keys |= set(sub["keys"])
    basket = {f"yfinance.{v}" for v in yf.SYMBOLS.values()}
    res = derived.resolve_registry(yaml.safe_load(
        (REPO / "metrics_registry.yaml").read_text(encoding="utf-8")))
    check(keys <= basket and all(k in res for k in keys),
          f"every proxy key is a basket close and registered ({sorted(keys - basket)} "
          f"outside)")
    want = {"semis": ["yfinance.mkt_smh"], "networking": ["yfinance.mkt_anet"],
            "cooling": ["yfinance.mkt_vrt"], "facilities": ["yfinance.mkt_pave"],
            "power": ["yfinance.mkt_grid", "yfinance.mkt_xlu"]}
    check(all(prox[b]["keys"] == v for b, v in want.items())
          and prox["semis"]["parts"]["memory"]["keys"] == ["yfinance.mkt_mu"],
          "the mapping: SMH; MU for memory; GRID and XLU; ANET; VRT; PAVE")
    from register import instruments                            # noqa: PLC0415
    rev = {f"yfinance.{v}": s for s, v in yf.SYMBOLS.items()}
    restricted = [rev[k] for k in keys if instruments.restrictions().is_restricted(rev[k])]
    check(not restricted, f"no Brookfield instrument among the proxies ({restricted or 'none'})")
    m = security_master.load() if hasattr(security_master, "load") else security_master.Master()
    eq = {s for s in yf.CAPEX_CHAIN_SYMBOLS
          if m.resolve(s, "yahoo")["asset_class"] == "equity"}
    check(eq == set(yf.CAPEX_CHAIN_SYMBOLS) and not (set(yf.CAPEX_CHAIN_SYMBOLS)
                                                    & set(yf.EARNINGS_SYMBOLS)),
          "the single names are equities in the master and not earnings names")


def capex_store(name: str, with_vrt: bool = True):
    from altdata import observations                            # noqa: PLC0415
    st = observations.ObservationStore(str(TD / f"{name}.db"))
    days = sessions("2026-06-01", "2026-10-20")
    rets = {"yfinance.mkt_spy": 4.0, "yfinance.mkt_smh": 15.0,
            "yfinance.mkt_mu": 30.0, "yfinance.mkt_grid": 10.0, "yfinance.mkt_xlu": 2.0,
            "yfinance.mkt_anet": -5.0, "yfinance.mkt_pave": 1.0}
    if with_vrt:
        rets["yfinance.mkt_vrt"] = 8.0
    for k, r in rets.items():
        write_series(st, k, days, ramp(days, 100.0, r))
    for n, a, b in (("AMZN", 80.0, 120.0), ("GOOGL", 50.0, 90.0), ("META", 40.0, 70.0),
                    ("MSFT", 60.0, 80.0), ("ORCL", 10.0, 40.0)):
        st.write("edgar.xbrl_capex", n, "2024-12-31", "2025-02-15T00:00:00+00:00", a, "fixture")
        st.write("edgar.xbrl_capex", n, "2025-12-31", "2026-02-15T00:00:00+00:00", b, "fixture")
    return st


def group_c() -> None:
    from altdata import capex_chain as cc                       # noqa: PLC0415
    head("C. THE RELATIVE LINE: LEAD TO LAG AGAINST SPY, BESIDE FILED CAPEX")
    st = capex_store("cc")
    try:
        r = cc.relative(st, CUT)
    finally:
        st.close()
    order = [b["id"] for b in r["buckets"]]
    check(order[0] == "semis" and order[-1] == "networking"
          and [a["id"] for a in r["absent"]] == [],
          f"ranked lead to lag (semis first, networking last: {order})")
    semis = r["buckets"][0]
    sp = r["bench"]["pct"]
    check(abs(semis["vs_bench_pp"] - (semis["pct"] - sp)) < 1e-9 and r["bench"]["sessions"] >= 55,
          f"each bucket is its basket less SPY, in pp (semis {semis['pct']:+.2f}% against "
          f"{sp:+.2f}%)")
    power = next(b for b in r["buckets"] if b["id"] == "power")
    check(power["keys"] == ["yfinance.mkt_grid", "yfinance.mkt_xlu"],
          "a bucket's basket is equal weight across its proxies (power: GRID and XLU)")
    c = r["capex"]
    check(c["pct"] == round((400.0 / 240.0 - 1) * 100, 1) and c["year"] == 2025,
          f"the hyperscalers' filed capex: the five names' sum, fiscal 2025 on 2024 "
          f"({c['pct']:+.1f}%)")
    lines = cc.relative_lines(r)
    check(any("not tracked" in x and "guidance" in x.lower() for x in lines)
          and "leads" in lines[0] and "lags" in lines[0] and not any(ISO.search(x) for x in lines),
          "the line names the leader and the laggard, says guidance is not tracked, and "
          "prints no ISO date")
    st2 = capex_store("cc_gap", with_vrt=False)
    try:
        r2 = cc.relative(st2, CUT)
    finally:
        st2.close()
    check([a["id"] for a in r2["absent"]] == ["cooling"]
          and "not enough history" in r2["absent"][0]["reason"],
          "a bucket without stored history is listed with its reason, never ranked")


def z1_store(name: str, with_share: bool = True):
    from altdata import observations                            # noqa: PLC0415
    st = observations.ObservationStore(str(TD / f"{name}.db"))
    days = sessions("2024-01-02", "2026-09-30")
    write_series(st, "yfinance.mkt_gspc", days, ramp(days, 4000.0, 40.0))
    if with_share:
        for q, v in (("2025-10-01", 40.0), ("2026-01-01", 41.0), ("2026-04-01", 42.0)):
            st.write("fred.hh_equity_share", None, q, "2026-09-15T00:00:00+00:00", v, "fixture")
    return st


def group_d() -> None:
    from altdata import transmission as tr                      # noqa: PLC0415
    head("D. THE IMPULSE: Z.1'S SHARE x SPX ON THE YEAR, MARKED BETWEEN RELEASES")
    check(tr.quarter_end("2026-04-01") == "2026-06-30" and tr.quarter_end("2025-10-01")
          == "2025-12-31", "a FRED quarter dated its first day ends three months on")
    st = z1_store("z1")
    try:
        w = tr.impulse(st, CUT)
    finally:
        st.close()
    by = {x["month"]: x for x in w["series"]}
    jun, sep = by["2026-06"], by["2026-09"]
    check(not jun["marked"] and jun["share_pct"] == 42.0,
          "at a quarter's end the impulse reads the quarter's own share (June: 42.0%)")
    check(sep["marked"] and sep["quarter_end"] == "2026-06-30",
          "between releases the share is marked, from the quarter's end, and labelled")
    from altdata import st_r5_rates as rt                       # noqa: PLC0415
    st = z1_store("z1b")
    try:
        px = dict(rt._pts(st, "yfinance.mkt_gspc", CUT))        # noqa: SLF001
    finally:
        st.close()
    me = tr.month_ends(sorted(px.items()))
    jun_c = [v for d, v in me if d[:7] == "2026-06"][0]
    sep_c = [v for d, v in me if d[:7] == "2026-09"][0]
    want = tr.marked(42.0, sep_c / jun_c - 1.0)
    check(abs(sep["share_pct"] - round(want, 3)) < 1e-9 and sep["share_pct"] > 42.0,
          f"the mark is s(1+r)/(1+sr), the rest of the balance sheet flat "
          f"({sep['share_pct']:.3f}%)")
    check(abs(sep["impulse_pp"] - sep["share_pct"] * sep["spx_yoy_pct"] / 100) < 2e-3
          and w["lens"]["n"] == len(w["series"]),
          "the impulse is the share times the year-on-year return over 100, in pp, with "
          "its percentiles' n")
    line = tr.impulse_line(w)
    check("marked to SPX" in line and "percentile" in line and "n=" in line,
          "the printed line labels the mark and carries its percentile with its n "
          "(rt.lens_text, the cluster's own form)")
    st = z1_store("z1c", with_share=False)
    try:
        w0 = tr.impulse(st, CUT)
    finally:
        st.close()
    check(w0["absent"] and "Z.1" in w0["reason"] and "not built" in tr.impulse_line(w0),
          "without the Z.1 share it is not built, with its reason")
    check("ICI" in w["ici_gap"] and "403" in w["ici_gap"],
          "ICI's allocation proxy is named a listed gap, with the refusal")


def group_e() -> None:
    from altdata import transmission as tr                      # noqa: PLC0415
    from daily_cascade import transmission_block as tb          # noqa: PLC0415
    head("E. THE NET-TRANSMISSION LINE: SIDE BY SIDE, NO WEIGHTS")
    st = z1_store("net")
    days = sessions("2024-01-02", "2026-09-30")
    write_series(st, "fred.ccc_oas", days, [8.0 + (i % 50) / 25 for i in range(len(days))])
    write_series(st, "fred.bb_oas", days, [2.0] * len(days))
    try:
        b = tr.net(st, CUT)
        sub = tb.subsection(st, CUT)
    finally:
        st.close()
    items = [x["item"] for x in b["legs"]]
    check(items == [34, 36, 41, 66] and all(x["scale"] for x in b["legs"]),
          f"four legs, each saying how it is scaled ({items})")
    check(b["legs"][0]["scale"].startswith("a flag") and "percentile" in b["legs"][2]["scale"]
          and "percentile" in b["legs"][3]["scale"],
          "the tightening flag is read as a flag; the level legs by their own history")
    lines = tr.net_lines(b)
    check("no leg is weighted or summed" in lines[0] and not any(
        re.search(r"\bnet (score|index|total)\b", x) for x in lines),
          "the line says no leg is weighted or summed, and prints no net figure")
    check(b["read_count"] <= 3 and "K-shape" in lines[-1]
          and sub and sub["not_tracked"] == [b["k_shape_gap"]],
          "the count is of legs read, and the K-shape panel is named a listed gap")
    check(any(x.startswith("Item 36") and "not read" in x for x in lines),
          "a leg without its data (Redfin) reads 'not read', never zero")


def group_f() -> None:
    import st_r6_66c_wealth_effect as L                         # noqa: PLC0415
    head("F. THE LEDGER: PRE-REGISTERED, HELD BY ITS SHA-256, APPLIED")
    raw = PREREG.read_bytes().replace(b"\r\n", b"\n")
    check(hashlib.sha256(raw).hexdigest() == PREREG_SHA,
          f"the pre-registration is unchanged (sha256 {hashlib.sha256(raw).hexdigest()[:12]})")
    text = raw.decode("utf-8")
    check("Never edited" in text and "0.20" in text and "n ≥ 40" in text
          and L.RHO_MIN == 0.20 and L.MIN_N == 40 and L.FIRST_YEAR == 1960,
          "the script's constants are the registration's (rho 0.20, n 40, from 1960)")

    def fixture(years: int, sign: float) -> dict:
        share = [(f"{y}-{m:02d}-01", 30.0) for y in range(1955, 1960 + years + 2)
                 for m in (1, 4, 7, 10)]
        # Consumption in year y+1 follows the index's return in year y, with sign:
        # the ledger's outcome is the NEXT twelve months.
        spx, pce, lvl, p, prev = [], [], 100.0, 100.0, 0.0
        for i, y in enumerate(range(1958, 1960 + years + 2)):
            r = ((i * 37) % 11 - 5) / 50.0
            g = 0.02 + sign * prev * 0.1
            for mo in range(1, 13):
                spx.append((f"{y}-{mo:02d}-28", lvl * (1 + r) ** (mo / 12)))
                pce.append((f"{y}-{mo:02d}-01", p * (1 + g) ** (mo / 12)))
            lvl *= (1 + r)
            p *= (1 + g)
            prev = r
        return {"share": share, "pce": pce, "spx": spx, "retrieved": "fixture"}

    r_small = L.study(fixture(20, 1.0), "fixture")
    check(r_small["verdict"].startswith("INSUFFICIENT") and r_small["n"] < 40,
          f"under n 40 the verdict is INSUFFICIENT (n {r_small['n']})")
    r_pass = L.study(fixture(60, 1.0), "fixture")
    r_fail = L.study(fixture(60, -1.0), "fixture")
    check(r_pass["verdict"].startswith("PASS") and r_fail["verdict"].startswith("FAIL"),
          f"a fixture built to pass passes ({r_pass['verdict'][:30]}) and one built to fail "
          f"fails ({r_fail['verdict'][:30]})")
    from altdata import ledgers                                 # noqa: PLC0415
    check(not ledgers.ledger_faults(r_pass) and r_pass["pass_rule"] == L.PASS_RULE
          and "grants" in r_pass["rights"],
          "the result is a ledger (as-of, window, n), the rule is the registration's, and "
          "the rights grant nothing")
    first = REPO / "docs" / "ledgers" / "st-r6.66c-ledger-2026-10-21.md"
    check(first.is_file() and ledgers.registered_rule("ST-R6.66c") == L.PASS_RULE,
          "the laptop first edition is on file and registers the same rule")
    src = (REPO / "tools" / "calibration" / "st_r6_66c_wealth_effect.py").read_text(encoding="utf-8")
    check("ObservationStore" not in src and "observations" not in src
          and "regime" not in src, "the script opens no store and reads no market state")


def group_g() -> None:
    import yaml                                                 # noqa: PLC0415
    head("G. NO VENDOR VALUE, NO BY-HAND KEY; THE WIRING; THE VOICES ENTRY (F4)")
    files = ["altdata/capex_chain.py", "altdata/transmission.py",
             "daily_cascade/capex_chain_block.py", "daily_cascade/transmission_block.py",
             "tools/calibration/st_r6_66c_wealth_effect.py", "config/capex_chain.yaml",
             "config/transmission.yaml"]
    bad = [f for f in files if re.search(r"vendor\.|flashalpha|manual_input|by_hand\b|"
                                         r"massive\.", (REPO / f).read_text(encoding="utf-8"),
                                         re.I)]
    check(not bad, f"no vendor key and no by-hand key in the new modules ({bad or 'none'})")
    ms = (REPO / "monthly_macro" / "stack.py").read_text(encoding="utf-8")
    check("transmission_block.subsection(st, now)" in ms
          and "capex_chain_block.priced_subsection(st, now)" in ms
          and __import__('daily_cascade.stack_hooks').stack_hooks.wired("monthly", "slow", "daily_cascade.capex_chain_block", "slow_subsection", []),
          "the Monthly calls the three: Plumbing's loosening leg, what's priced, Factor I")
    vs = yaml.safe_load((REPO / "config" / "voices_sources.yaml").read_text(encoding="utf-8"))
    j = [s for s in vs["sources"] if s.get("id") == "jdi_research"]
    from altdata import source_tiers                            # noqa: PLC0415
    check(j and j[0]["method"] == "rss" and j[0]["default_kind"] == "independent"
          and "research seller with open positions" in j[0]["note"]
          and source_tiers.tier_of("x - JDI Research") == 2
          and "linkedin" not in json.dumps(j[0]).lower(),
          "JDI Research's own feed, kind independent with the ruled tag, tier 2; no "
          "LinkedIn read")


def main() -> int:
    try:
        group_a()
        group_b()
        group_c()
        group_d()
        group_e()
        group_f()
        group_g()
    finally:
        import shutil                                           # noqa: PLC0415
        shutil.rmtree(TD, ignore_errors=True)
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
