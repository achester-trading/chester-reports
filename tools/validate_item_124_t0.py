#!/usr/bin/env python3
"""
Item 124, Tranche 0 (the tail-days order's 106i; ruled 6 Nov 2026, D60; A126).

    python tools/validate_item_124_t0.py

  A  THE ONE WINDOW LABEL. derived.window_label prints the asked window alone when
     the stored span covers it, "5y asked, 3.4y stored" when it does not, "3.4y/5y" in a
     compact cell. The lens forms, lens_cells' cells, derived_forms,
     delta_percentile, the regime's dimensions and session move, stack.triple,
     st_r5_rates and vol_event go through it. A source scan fails on a percentile
     window label built anywhere else, and is shown to fire.
  B  THE CSV NEVER SHRINKS BY ACCIDENT. A shorter rewrite is refused, logged and
     kept; allow_shrink=True is honoured; a merge is not refused; fred.pull merges
     on every path.
  C  ST-R6.59c READS THE STORE. load_store reads read-only; before the stored HY
     history the credit leg is Baa less the 10-year, each such row "proxy: Baa-10y";
     the pass rule is the first edition's, word for word.
  D  SESSIONS, NOT DAYS. oneday_10y's and speed_attribution's printed names count
     sessions ("10y D3 sessions"); the computations are unchanged.
  E  THE LONG-WINDOW CREDIT SERIES. fed_ebp parses the FEDS Notes CSV by column name
     (a fixture), flags its backfill (fed:backfill, ingest_instant), is an official
     writer, registered spread and barred from the object; the credit family's long
     window is calc.baa_less_10y (HY and IG keep their 5-year lens, honest); Baa-10y
     has its 5y and 20y lenses and a D20; tb_episodes' Baa key names it; the
     Monthly's EBP line says "not yet pulled" until a pull, then prints the month.

Fixtures only; a temporary store; the clock pinned. Nothing is fetched.
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: the gate list reads this declaration (tools/gate_list.py)

import ast
import datetime as dt
import logging
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "tools" / "calibration"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gate_tmp import mkdtemp  # noqa: E402

# THE GATE'S CLOCK (B106's rule): the fixtures end on 2026-11-06.
GATE_NOW = "2026-11-06T15:00:00+00:00"
TMP = Path(mkdtemp("gate_item_124_t0_"))
LINE = "=" * 78
PASSED = FAILED = 0


def pin_clock() -> None:
    from altdata import session
    session.utc_now = lambda: dt.datetime.fromisoformat(GATE_NOW)


def ok(m: str) -> None:
    global PASSED
    PASSED += 1
    print(f"  PASS  {m}")


def bad(m: str) -> None:
    global FAILED
    FAILED += 1
    print(f"  FAIL  {m}")


def check(c: bool, m: str) -> None:
    (ok if c else bad)(m)


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


def bdays(first: dt.date, last: dt.date) -> list[dt.date]:
    out, d = [], first
    while d <= last:
        if d.weekday() < 5:
            out.append(d)
        d += dt.timedelta(days=1)
    return out


def row(key, day, value, source="fixture"):
    return {"registry_key": key, "instrument": None, "observed_at": str(day),
            "available_at": f"{day}T21:00:00+00:00", "value": float(value),
            "source": source, "availability_kind": "reconstructed"}


END = dt.date(2026, 11, 5)


# ---------------------------------------------------------------------------
# A. The one window label
# ---------------------------------------------------------------------------
SCAN_ROOTS = ("altdata", "daily_cascade", "monthly_macro", "alpha", "register",
              "regime.py")
# A PERCENTILE'S WINDOW BUILT BY HAND: the shapes the helper replaced. Each is a
# label beside a percentile; derived.window_label is the one place a window is
# written. (A z-score's window or a calendar window is not a percentile's.)
FORBIDDEN = (
    (re.compile(r"shorter than \{[^}]*\} years"), "'shorter than N years'"),
    (re.compile(r"percentile of \{[^}]*\} years"), "'percentile of N years'"),
    (re.compile(r"of \{[^}]*\['years'\]\} years"), "'of N years' from a lens"),
    (re.compile(r"\{yrs\} years"), "'N years' beside a percentile"),
    (re.compile(r"f\"\{years\}y\""), "a bare f'{years}y' label"),
    (re.compile(r"percentile \"\s*f?\"\(\d+y\)"), "a literal '(5y)' after a percentile"),
    (re.compile(r"\{aw\}-day read"), "a window in days beside a percentile"),
    (re.compile(r"sessions, five years"), "'five years' beside a percentile"),
)


def label_faults(text: str, name: str = "<text>") -> list[str]:
    return [f"{name}: {why}" for rx, why in FORBIDDEN if rx.search(text)]


def scanned_files() -> list[Path]:
    out = []
    for r in SCAN_ROOTS:
        p = REPO / r
        if p.is_file():
            out.append(p)
        elif p.is_dir():
            out += [f for f in sorted(p.rglob("*.py"))
                    if "__pycache__" not in f.parts and "report" not in
                    f.relative_to(REPO).parts[1:2]]
    return out


def group_a() -> None:
    head("A. derived.window_label: the asked window, and the stored span when shorter")
    from altdata import derived
    from daily_cascade import lens_cells
    W = derived.window_label
    check(W(1826, 1826) == "5y" and W(1826, 1800) == "5y",
          f"a covered window prints alone ({W(1826, 1826)!r}; within a month: {W(1826, 1800)!r})")
    check(W(1826, 1250) == "5y asked, 3.4y stored",
          f"a short one says both: {W(1826, 1250)!r}")
    check(W(7305, 1250, compact=True) == "3.4y/20y",
          f"the compact form: {W(7305, 1250, compact=True)!r}")
    check(W("full", None, start="1986-01-02") == "full history from 1986-01-02",
          "the full history is never short")
    # D65: the label says "stored", and the flag-word audits are as they were
    from daily_cascade import dealer_block
    from monthly_macro import dealer as mdealer
    labels = [W(1826, d_) for d_ in (100, 400, 1250, 1800)] + [W(7305, 1250, compact=True)]
    check(not any(dealer_block.FLAG_WORD.search(x) or mdealer._FLAG_WORD.search(x)
                  for x in labels),
          f"no window label carries a flag word ({labels[2]!r})")
    check(all(rx.search(s_) for rx in (dealer_block.FLAG_WORD, mdealer._FLAG_WORD)
              for s_ in ("The call wall held on Wednesday.", "5y asked, 3.4y held")),
          "both flag-word audits catch 'held' again, after a year count too (no exemption)")
    # the lens forms on a three-year series
    s = [(d.isoformat(), 3.0 + (i % 9) * 0.01)
         for i, d in enumerate(bdays(dt.date(2023, 7, 3), END))]
    p = derived._pct_in_window(s, 3.05, END, 5)
    check(p["window"].startswith("5y asked, 3.") and p["window"].endswith("y stored")
          and p["window_compact"].endswith("/5y") and p["n"] == len(s),
          f"a percentile of five years over three: {p['window']!r}, n={p['n']}")
    f = {"pctile_5y": 40.0, "pctile_5y_ordinal": "40th", "pctile_5y_n": p["n"],
         "pctile_5y_window": p["window"], "pctile_5y_window_asked": p["asked_days"],
         "pctile_5y_window_held": p["held_days"]}
    short = lens_cells._pct_cell(f, "pctile_5y", True)
    long_ = lens_cells._pct_cell(f, "pctile_5y", False)
    check(re.fullmatch(r"40th \(3\.\dy/5y\)", short or "") is not None
          and "5y asked" in long_ and f"n={p['n']}" in long_,
          f"lens_cells: compact {short!r}; long {long_!r} (n kept)")
    # the call sites go through it
    src = {p: (REPO / p).read_text(encoding="utf-8") for p in (
        "regime.py", "daily_cascade/lens_cells.py", "monthly_macro/stack.py",
        "altdata/st_r5_rates.py", "altdata/vol_event.py", "altdata/derived.py")}
    check(all("window_label(" in t for t in src.values()),
          "regime, lens_cells, stack.triple, st_r5_rates, vol_event and the lens "
          "forms call derived.window_label")
    check('"window_label"' in src["regime.py"] and "window_label_5y" in src["regime.py"]
          and "window_label_5y" in (REPO / "daily_cascade/state_block.py").read_text(encoding="utf-8"),
          "the regime's dimensions and session move carry it, and the block prints it")
    # nothing builds a percentile's window by hand
    hits = [h for f_ in scanned_files()
            for h in label_faults(f_.read_text(encoding="utf-8"),
                                  str(f_.relative_to(REPO)))]
    check(not hits, f"no percentile window label built outside the helper "
                    f"({len(scanned_files())} files scanned){': ' + '; '.join(hits) if hits else ''}")
    # MUST FAIL: the scan fires on each shape
    probes = ['f"of {lz[\'years\']} years"', 'f"shorter than {lz[\'years\']} years"',
              'f"{years}y"', 'f"{yrs} years, n="', 'percentile "\n  f"(5y)',
              'f"the {aw}-day read is"', "f'sessions, five years'"]
    fired = [p_ for p_ in probes if label_faults(p_)]
    check(len(fired) == len(probes),
          f"must fail: the scan fires on each hand-built label ({len(fired)} of {len(probes)})")


# ---------------------------------------------------------------------------
# B. The CSV shrink guard
# ---------------------------------------------------------------------------
class _Catch(logging.Handler):
    def __init__(self):
        super().__init__()
        self.msgs: list[str] = []

    def emit(self, rec):
        self.msgs.append(rec.getMessage())


def group_b() -> None:
    head("B. The CSV never shrinks by accident; fred.pull merges on every path")
    from altdata.store import Store
    d = TMP / "csv"
    st = Store(str(d))
    catch = _Catch()
    logging.getLogger("altdata.store").addHandler(catch)
    full = [("2020-01-01", 1.0), ("2020-02-01", 2.0), ("2020-03-01", 3.0)]
    st.write_observations("fx", full, source="fred", dual_write=False)
    path = d / "fx.csv"
    before = path.read_bytes()
    st.write_observations("fx", [("2020-03-01", 3.5)], source="fred", dual_write=False)
    check(path.read_bytes() == before and len(st.refusals) == 1
          and any("refused to rewrite fx.csv" in m for m in catch.msgs),
          f"a shorter rewrite is refused, logged and kept ({st.refusals[:1]})")
    st.write_observations("fx", [("2020-02-01", 2.0), ("2020-03-01", 3.0)],
                          source="fred", dual_write=False)
    check(path.read_bytes() == before and len(st.refusals) == 2,
          "a rewrite starting later is refused too")
    st.write_observations("fx", [("2020-03-01", 3.5), ("2020-04-01", 4.0)],
                          source="fred", dual_write=False, merge=True)
    rows = path.read_text().strip().splitlines()[1:]
    check(len(rows) == 4 and len(st.refusals) == 2 and rows[0].startswith("2020-01-01"),
          "a merge keeps the history and is not refused (4 rows from 2020-01-01)")
    st.write_observations("fx", [("2020-03-01", 9.0)], source="fred", dual_write=False,
                          allow_shrink=True)
    rows = path.read_text().strip().splitlines()[1:]
    check(len(rows) == 1 and rows[0].startswith("2020-03-01,9.0"),
          "allow_shrink=True is honoured: the caller meant it")
    logging.getLogger("altdata.store").removeHandler(catch)
    # every write in fred.pull merges
    tree = ast.parse((REPO / "altdata/sources/fred.py").read_text(encoding="utf-8"))
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
             and getattr(n.func, "attr", "") == "write_observations"]
    merges = [next((k.value for k in c.keywords if k.arg == "merge"), None) for c in calls]
    check(calls and all(isinstance(m, ast.Constant) and m.value is True for m in merges),
          f"fred.pull's {len(calls)} write(s) pass merge=True on every path "
          f"(full=True and lookback_days included)")


# ---------------------------------------------------------------------------
# C. ST-R6.59c reads the store
# ---------------------------------------------------------------------------
def group_c() -> None:
    head("C. ST-R6.59c: the observation store, and Baa-10y before the stored HY")
    import st_r6_59c_bank_stress as bs
    from altdata import observations
    db = TMP / "bank.sqlite"
    st = observations.ObservationStore(str(db))
    days = bdays(dt.date(2005, 1, 3), dt.date(2025, 6, 30))
    rows = []
    for i, d in enumerate(days):
        crash = 1.0 - (0.25 if dt.date(2008, 9, 1) <= d <= dt.date(2008, 12, 31) else 0.0) \
            - (0.2 if dt.date(2023, 3, 6) <= d <= dt.date(2023, 4, 30) else 0.0)
        rows.append(row("yfinance.mkt_kre", d, 50.0 * crash + (i % 3) * 0.01))
        rows.append(row("yfinance.mkt_gspc", d, 1000.0 + i * 0.5))
        rows.append(row("calc.baa_less_10y", d, 200.0 + (i % 50)))
        if d >= dt.date(2023, 1, 3):
            rows.append(row("fred.hy_oas", d, 4.0 + (i % 20) * 0.01))
    st.write_many(rows)
    st.close()
    data = bs.load_store(str(db))
    check(len(data["kre"]) == len(days) and data["hy"][0][0] == "2023-01-03"
          and len(data["baa10y"]) == len(days) and data["origin"] == "store",
          "load_store reads each series from the store (KRE, ^GSPC, HY from 2023, Baa-10y)")
    check(db.stat().st_size > 0 and "read-only" in data["retrieved"],
          "the store is opened read-only (mode=ro)")
    r = bs.study(data, "laptop run, the observation store")
    proxied = [e for e in r["episodes"] if e.get("hy_basis") == bs.PROXY_LABEL]
    held = [e for e in r["episodes"] if e.get("hy_basis") == "HY OAS"]
    body = "\n".join(r["body"])
    check(proxied and all(e["start"] < "2023-01-03" for e in proxied)
          and "(proxy: Baa-10y)" in body,
          f"episodes before the stored HY read Baa-10y, labelled ({len(proxied)} rows)")
    check(all(e["start"] >= "2023-01-03" for e in held),
          f"episodes inside the HY history read HY OAS ({len(held)} rows)")
    first = sorted((REPO / "docs/ledgers").glob("st-r6.59c-ledger-*.md"))[0]
    check(bs.PASS_RULE in first.read_text(encoding="utf-8"),
          f"the pass rule is the first edition's, word for word ({first.name})")
    check("observation store" in r["sources"][0] and bs.STORE_KEYS["baa10y"] == "calc.baa_less_10y",
          "the edition names the store as its source")


# ---------------------------------------------------------------------------
# D. Sessions, not days
# ---------------------------------------------------------------------------
def group_d() -> None:
    head("D. The printed names count sessions where they count FRED observations")
    from altdata import oneday_10y as od, speed_attribution as sa
    y = [(d.isoformat(), 4.0 + (i % 5) * 0.01) for i, d in enumerate(bdays(dt.date(2026, 9, 1), END))]
    ch = od.one_day_changes(y)
    check(len(ch) == len(y) - 1 and round(ch[0][1], 6) == round((y[1][1] - y[0][1]) * 100, 6)
          and od.CHANGE_NAME == "10y D1 sessions",
          "one_day_changes: one change per stored observation, in bp; named '10y D1 sessions'")
    t = od.trigger(y, y[-1][0])
    check("one-session" in t["line"] and "one-day change" not in t["line"],
          f"the trigger's line counts sessions ({t['line'][:70]})")
    cfg = {"models": [], "start_tolerance_days": 4}
    att = sa.attribute({"yield": y}, y[-1][0], 3, cfg)
    check(att.get("name") == "10y D3 sessions",
          f"speed_attribution.attribute names its window: {att.get('name')!r}")
    check(f"10-year move ({att['name']})" in sa.table(att)["columns"],
          "the attribution table's move column prints the name")


# ---------------------------------------------------------------------------
# E. The long-window credit series
# ---------------------------------------------------------------------------
OAS_FAMILY = ("fred.hy_oas", "fred.ig_oas", "fred.bb_oas", "fred.ccc_oas", "fred.aa_oas",
              "fred.aaa_oas", "fred.bbb_oas", "fred.em_corp_oas", "fred.em_hy_oas",
              "fred.euro_hy_oas")
CSV = ("date,gz_spread,ebp,est_prob\n"
       "1973-01-01,1.13,-0.05,0.18\n"
       "2026-09-01,0.93,-0.38,0.09\n"
       "2026-10-01,1.00,-0.27,0.12\n")


def group_e() -> None:
    head("E. fed.ebp and fed.gz_spread; the credit long window; Baa-10y's lenses")
    import yaml
    from altdata import derived, feeds, observations
    from altdata.sources import fed_ebp
    from daily_cascade import credit_long_block as clb, lens_cells
    rows = fed_ebp.rows_from_csv(CSV, "2026-11-06T15:00:00+00:00", "observed")
    ks = sorted({r["registry_key"] for r in rows})
    check(ks == ["fed.ebp", "fed.gz_spread"] and len(rows) == 6
          and not any("est_prob" in r["registry_key"] for r in rows),
          "the CSV parses by column name: ebp and gz_spread, est_prob not stored")
    bf = fed_ebp.rows_from_csv(CSV, GATE_NOW, "ingest_instant", source=fed_ebp.BACKFILL_SOURCE)
    check(all(r["source"] == "fed:backfill" and r["availability_kind"] == "ingest_instant"
              and r["available_at"] == GATE_NOW for r in bf),
          "the backfill is flagged: fed:backfill, available at the pull instant")
    bad_csv = "Date,Spread\n2026-10-01,1.0\n"
    try:
        fed_ebp.rows_from_csv(bad_csv, GATE_NOW, "observed")
        check(False, "must fail: a renamed column is refused")
    except ValueError:
        check(True, "must fail: a file without the named columns is refused, never guessed")
    check("fed_ebp" in feeds.OFFICIAL_WRITERS and feeds.static_keys("fed_ebp") == fed_ebp.KEYS,
          "fed_ebp is an official writer; its KEYS are on the freshness roster")
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    src = yaml.safe_load((REPO / "source_registry.yaml").read_text(encoding="utf-8"))
    fam = {k: derived.family_of(k)[0] for k in fed_ebp.KEYS}
    check(all(f == "spread" for f in fam.values())
          and all(reg["metrics"][k]["units"] == "percent_rate" for k in fed_ebp.KEYS)
          and "fed" in (src.get("sources") or src),
          f"registered: family spread, percentage points with bp changes; source 'fed' ({fam})")
    barred = [b for b in reg["market_state_barred"] if "fed.ebp" in (b.get("keys") or [])]
    check(barred and all(derived.market_state_barred(derived.registry_entry(k)) for k in fed_ebp.KEYS),
          "barred from the market-state object")
    lc = derived.lens_config()
    clw = lc.get("credit_long_window") or {}
    check(clw.get("series") == "calc.baa_less_10y" and int(clw.get("years")) == 20
          and set(clw.get("members") or []) == set(OAS_FAMILY)
          and "calc.baa_less_10y" in (lc.get("d20_forms") or []),
          "config/metric_lenses.yaml: the credit family's long window is calc.baa_less_10y "
          "(20y), for all ten ICE BofA OAS series (D65)")
    from altdata import config as acfg
    reg_oas = sorted("fred." + s.key for s in acfg.FRED_PULL_SERIES
                     if s.fred_id.startswith("BAML") and s.key.endswith("_oas"))
    check(reg_oas == sorted(OAS_FAMILY),
          f"the members are every ICE BofA OAS series the registry carries ({len(reg_oas)})")
    tb = yaml.safe_load((REPO / "config/tb_episodes.yaml").read_text(encoding="utf-8"))
    tbi = tb.get("inputs") or {}
    check((tbi.get("baa_10y") or {}).get("key") == "calc.baa_less_10y",
          "config/tb_episodes.yaml's Baa proxy key names calc.baa_less_10y")
    # the lenses on a fixture store: HY three years, Baa-10y thirty
    st = observations.ObservationStore(str(TMP / "lenses.sqlite"))
    rr = []
    for i, d in enumerate(bdays(dt.date(1996, 1, 2), END)):
        rr.append(row("calc.baa_less_10y", d, 200.0 + (i % 60)))
    for i, d in enumerate(bdays(dt.date(2023, 7, 3), END)):
        rr.append(row("fred.hy_oas", d, 3.0 + (i % 30) * 0.01))
        rr.append(row("fred.euro_hy_oas", d, 3.5 + (i % 30) * 0.01))
    st.write_many(rr)
    hy = derived.lens_forms("fred.hy_oas", GATE_NOW, store=st)
    F = hy["forms"]
    check("5y asked" in str(F.get("pctile_5y_window")) and F.get("pctile_5y") is not None,
          f"HY OAS keeps its 5-year lens, its span honest: {F.get('pctile_5y_window')!r}")
    check(F.get("pctile_long_series") == "calc.baa_less_10y" and F.get("pctile_long") is not None
          and F.get("pctile_long_window") == "20y" and "D60" in str(F.get("pctile_long_basis"))
          and "percentiles_disagree" not in hy["flags"],
          f"HY's long column reads Baa-10y over 20 years, named "
          f"({F.get('pctile_long_ordinal')}, n={F.get('pctile_long_n')})")
    eu = derived.lens_forms("fred.euro_hy_oas", GATE_NOW, store=st)["forms"]
    check(eu.get("pctile_long_series") == "calc.baa_less_10y"
          and eu.get("pctile_long_window") == "20y" and "y stored" in str(eu.get("pctile_5y_window")),
          "euro HY (registry long_window 'full'): its long column reads Baa-10y too; its "
          "5-year lens is its own, the stored span printed (D65)")
    cell = lens_cells._pct_cell(F, "pctile_long", False) or ""
    check("of Baa less the 10-year" in cell, f"the long cell names the series: {cell!r}")
    baa = derived.lens_forms("calc.baa_less_10y", GATE_NOW, store=st)
    B = baa["forms"]
    check(baa["family"] == "spread" and B.get("pctile_5y_window") == "5y"
          and B.get("pctile_long_window") == "20y" and B.get("change_d20_bp") is not None,
          f"Baa-10y: its 5y and 20y lenses and a D20 ({B.get('change_d20_bp')} bp)")
    comp = lens_cells.compact(baa)
    check(comp.startswith("D20 ") and "(5y)" in comp and "(20y)" in comp,
          f"its compact cell: {comp!r}")
    # the Monthly's line
    check(clb.ebp_line(st, GATE_NOW) == clb.NOT_PULLED,
          "the Monthly's EBP line says 'not yet pulled' before the first pull")
    st.write_many([row("fed.ebp", "2026-10-01", -0.27, "fed:backfill"),
                   row("fed.gz_spread", "2026-10-01", 1.00, "fed:backfill"),
                   row("fed.ebp", "2026-09-01", -0.38, "fed:backfill"),
                   row("fed.gz_spread", "2026-09-01", 0.93, "fed:backfill")])
    line = clb.ebp_line(st, GATE_NOW)
    check("-0.27 pp for 2026-10" in line and "GZ spread 1.00 pp" in line
          and "Report only" in line,
          f"after a pull it prints the month: {line[:90]}")
    hook = yaml.safe_load((REPO / "config/stack_hooks/monthly-slow-credit-ebp.yaml")
                          .read_text(encoding="utf-8"))
    check(hook["cadence"] == "monthly" and hook["section"] == "slow"
          and hook["module"] == "daily_cascade.credit_long_block",
          "it joins the Monthly's slow layers through a hook, monthly only")
    st.close()


def main() -> int:
    pin_clock()
    group_a()
    group_b()
    group_c()
    group_d()
    group_e()
    print(f"\n{LINE}\n{PASSED} passed, {FAILED} failed\n{LINE}")
    print("VALIDATION PASSED" if not FAILED else "VALIDATION FAILED")
    return 0 if not FAILED else 1


if __name__ == "__main__":
    sys.exit(main())
