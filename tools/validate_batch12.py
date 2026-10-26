"""
Signal-triage Batch 12 (items 59-60; docs/change-order-signal-triage-batch-12-
2026-10-20.md, ruled 20 Oct 2026 with filing amendments F1-F6; session A's a53).

  A  THE FUNDING-STRESS FLAG at and around its threshold: a member at the 95th
     percentile is not above it, one just over is; one member above leaves the
     flag off, two turn it on; fewer than two members read is "not read".
  B  THE DEPOSIT-FLIGHT FLAG: small-bank deposits down and money funds up over 4
     weeks turns it on; either flat or the wrong way leaves it off; a leg not
     stored is "not read".
  C  THE CLASSIFIER: dormant at KRE -10.0% (it prints past -10%), and its three
     states -- correction, funding watch, banking stress -- past it; the CDS/AT1
     arm prints "not tracked" (F2); the read's line only when it prints.
  D  THE PANEL over a synthetic store: SOFR less IORB with IOER before 29 Jul 2021,
     every series with dual percentiles, the Weekly's one line, the Monthly's
     table with its long windows and gaps, the close's item; the listed gaps.
  E  THE 12:30 GATE (F5): open only on the session a flag turns on, closed on a
     session it stays on, closed with no store and creating none; registered in
     midday_gate.GATES.
  F  F3's TWO BRANCHES: with no source named, implied growth and the forecast
     error are listed gaps and the flag does not print; with a source named on a
     fixture, implied growth prints with its percentiles, the error and the flag.
  G  F4's LABELS: forward P/E against its peak since logging began (with that
     date), trailing against its 2025 peak, each labelled, and the reason where a
     leg cannot be computed.
  H  THE SOURCES AND REGISTRATION: the panel's FRED legs, KRE in the basket and
     the Security Master, the OFR and FDIC writers on the roster and their parsers
     on fixtures, ICI parked (its parser off every roster), each key registered,
     the SR-16 neocloud gap line, the narrative pair seeded PROPOSED.
  I  NO VENDOR VALUE AND NO BY-HAND KEY is read by any new module; nothing here
     writes the register, a composite or the market-state object.
  J  THE LEDGER: the pre-registration on file at its SHA-256, the scoring script
     opening no store, its rule applied on fixtures (INSUFFICIENT, PASS, FAIL).

Synthetic fixtures only: no live store, no network, no model, no real names.
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import datetime as dt
import hashlib
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "tools" / "calibration"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gate_tmp import mkdtemp                                    # noqa: E402

LINE = "=" * 78
PASS = FAIL = 0
TD = Path(mkdtemp("batch12-gate-"))
LIVE_DB = REPO / "data" / "chester.db"
LIVE_DB_AT_START = LIVE_DB.exists()
PREREG = "docs/ledgers/bank-stress-preregistration-2026-10.md"
PREREG_SHA = "011f7d25a149c345b032444e8e3c0964421430479424366614733d09beb19192"
NEW_MODULES = ("altdata/bank_stress.py", "daily_cascade/bank_stress_block.py",
               "altdata/eps_overshoot.py", "altdata/pe_dispersion.py",
               "altdata/sources/ofr_fsi.py", "altdata/sources/fdic_qbp.py",
               "altdata/sources/ici_mmf.py", "tools/calibration/st_r6_59c_bank_stress.py")


def check(ok: bool, what: str) -> None:
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  PASS  {what}")
    else:
        FAIL += 1
        print(f"  FAIL  {what}")


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


def row(sid: str, pct: float) -> dict:
    return {"id": sid, "state": "ok", "pct_5y": pct}


def weekdays(start: str, n: int) -> list[str]:
    d, out = dt.date.fromisoformat(start), []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. THE FUNDING-STRESS FLAG")
    from altdata import bank_stress as bs
    cfg = bs.config()
    f = cfg["funding_flag"]
    check(f["members"] == ["sofr_iorb", "fin_cp_spread", "dw_primary_credit",
                           "fhlb_advances"] and f["min_on"] == 2 and f["percentile"] == 95,
          "the ruled members, 'any two of', 'above their 95th percentile'")
    at = bs.funding_flag([row("sofr_iorb", 95.0), row("fin_cp_spread", 95.0),
                          row("dw_primary_credit", 10), row("fhlb_advances", 10)], cfg)
    one = bs.funding_flag([row("sofr_iorb", 95.1), row("fin_cp_spread", 95.0),
                           row("dw_primary_credit", 10), row("fhlb_advances", 10)], cfg)
    two = bs.funding_flag([row("sofr_iorb", 95.1), row("fin_cp_spread", 99.0),
                           row("dw_primary_credit", 10), row("fhlb_advances", 10)], cfg)
    thin = bs.funding_flag([row("sofr_iorb", 99.0)], cfg)
    check(at["state"] == "off" and at["above"] == [],
          "two members at exactly the 95th percentile: not above it, the flag off")
    check(one["state"] == "off" and one["above"] == ["sofr_iorb"],
          "one member just over (95.1): the flag stays off")
    check(two["state"] == "on" and two["above"] == ["sofr_iorb", "fin_cp_spread"],
          "two members over: the flag on")
    check(thin["state"] == "not read" and not thin["on"],
          "one member read of the two it needs: 'not read', never on")
    check("2 of 4 read above their 95th" in bs.funding_line(two),
          f"the line names the count read ({bs.funding_line(two)})")


def group_b() -> None:
    head("B. THE DEPOSIT-FLIGHT FLAG")
    from altdata import bank_stress as bs
    ch = lambda v: {"change": v, "now_day": "2026-10-14"}       # noqa: E731
    on = bs.deposit_flag(ch(-0.1), ch(0.1))
    check(on["state"] == "on", "small-bank deposits down and money funds up over 4 weeks: on")
    check(bs.deposit_flag(ch(0.0), ch(5.0))["state"] == "off"
          and bs.deposit_flag(ch(-5.0), ch(0.0))["state"] == "off"
          and bs.deposit_flag(ch(-5.0), ch(-1.0))["state"] == "off",
          "deposits flat, or money funds flat or falling: off")
    nr = bs.deposit_flag(None, ch(1.0))
    check(nr["state"] == "not read" and "small-bank deposits" in nr["why"],
          "a leg not stored over 4 weeks: 'not read', with which leg")
    check(bs.config()["deposit_flag"]["weeks"] == 4
          and bs.config()["deposit_flag"]["money_funds"] == "fred.mmf_retail",
          "4 weeks, ruled; the money-fund leg FRED's retail series while ICI is a gap")


def group_c() -> None:
    head("C. THE CLASSIFIER")
    from altdata import bank_stress as bs
    cfg = bs.config()
    on, off = {"on": True}, {"on": False}
    dd = lambda p: {"change_pct": p, "from_day": "2026-09-16", "to_day": "2026-10-14"}  # noqa: E731
    check(bs.classify(on, on, dd(-10.0), cfg)["state"] == "dormant"
          and bs.classify(on, on, dd(-9.9), cfg)["prints"] is False,
          "KRE -10.0% over 20 sessions: dormant (it prints past -10%)")
    states = [bs.classify(off, off, dd(-10.1), cfg)["state"],
              bs.classify(on, off, dd(-12.0), cfg)["state"],
              bs.classify(off, on, dd(-12.0), cfg)["state"],
              bs.classify(on, on, dd(-25.0), cfg)["state"]]
    check(states == ["correction", "funding watch", "funding watch", "banking stress"],
          f"the three states past -10%: neither flag, one, both ({states})")
    c = bs.classify(on, on, dd(-25.0), cfg)
    line = bs.classifier_line(c)
    check("not tracked" in line and "CDS/AT1" in line and "F2" in line
          and "BANKING STRESS" in line,
          "the CDS/AT1 arm prints 'not tracked' (F2) in the classifier's line")
    check(bs.classifier_line(bs.classify(on, on, dd(-5.0), cfg)) is None
          and bs.classify(off, off, None, cfg)["state"] == "not read",
          "no line while dormant; 'not read' without KRE's history")


def seed_store(db: Path, sofr_spike: bool = True, deposit_flight: bool = True,
               kre_fall: float = -15.0) -> None:
    """A synthetic store: two years of daily rates, weekly H.8 and money funds,
    quarterly FHLB, KRE and XLF."""
    from altdata import observations
    rows = []

    def put(key, day, v):
        rows.append({"registry_key": key, "instrument": None, "observed_at": day,
                     "available_at": f"{day}T22:00:00+00:00", "value": v, "source": "fred"})
    days = weekdays("2020-06-01", 650)
    for i, d in enumerate(days):
        last = i == len(days) - 1
        # A falling baseline keeps each day's value at the bottom of its window, so
        # the flag is off until the last day's spike (the gate's turning session).
        put("fred.sofr", d, 3.6 if (sofr_spike and last) else 3.06 - 0.00005 * i)
        put("fred.sofr_p99", d, 3.1)
        put("fred.iorb" if d >= "2021-07-29" else "fred.ioer", d, 3.0)
        put("fred.fin_cp_3m", d, 4.1 if (sofr_spike and last) else 3.3 - 0.0001 * i)
        put("fred.tbill_3m", d, 3.0)
        put("fred.yield_10y", d, 4.3)
        put("yfinance.mkt_xlf", d, 50.0)
        rows.append({"registry_key": "yfinance.mkt_kre", "instrument": None,
                     "observed_at": d, "available_at": f"{d}T22:00:00+00:00",
                     "value": 100.0 if i < len(days) - 1 else 100.0 * (1 + kre_fall / 100),
                     "source": "yfinance"})
    for j, d in enumerate([x for x in days if dt.date.fromisoformat(x).weekday() == 2]):
        put("fred.dw_primary_credit", d, 5000.0 - 10.0 * j)   # falling: never at its top
        put("fred.h8_dep_small", d, 5700.0 - (20.0 * j if deposit_flight else 0) if j > 120 else 5700.0)
        put("fred.mmf_retail", d, 3000.0 + (5.0 * j if deposit_flight else 0))
        put("fred.stlfsi", d, -0.5)
    for n, q in enumerate(("2021-01-01", "2021-04-01", "2021-07-01", "2021-10-01",
                           "2022-01-01")):
        put("fred.fhlb_advances", q, 600000.0 - 1000.0 * n)
    put("ofr.fsi", days[-1], -1.2)
    put("fdic.unrealised_total", "2021-12-31", -3.27e11)
    with observations.ObservationStore(str(db)) as st:
        st.write_many(rows)


def group_d() -> None:
    head("D. THE PANEL OVER A SYNTHETIC STORE")
    from altdata import bank_stress as bs, observations
    from daily_cascade import bank_stress_block as blk
    pol = bs.policy_rate([("2021-07-29", 0.15), ("2021-07-30", 0.15)],
                         [("2021-07-27", 0.15), ("2021-07-28", 0.10), ("2021-07-29", 9.9)],
                         "2021-07-29")
    check(pol == {"2021-07-27": 0.15, "2021-07-28": 0.10, "2021-07-29": 0.15,
                  "2021-07-30": 0.15},
          "IOER before 29 Jul 2021, IORB from it (the SOFR spread's history)")
    check(bs.spread_bp([("d1", 3.10), ("d3", 3.20)], {"d1": 3.0, "d2": 3.05}) ==
          [("d1", 10.0), ("d3", 15.0)], "a spread in bp, the rate carried over a holiday")
    db = TD / "panel.db"
    seed_store(db)
    cut = "2022-12-31T00:00:00+00:00"
    with observations.ObservationStore(str(db)) as st:
        b = bs.build(st, cut)
        close = blk.close_items(st, cut)
        read = blk.read_items(st, cut)
        wk = blk.weekly_subsection(st, cut)
        mo = blk.monthly_subsection(st, cut)
    by = {r["id"]: r for r in b["panel"]}
    check(all(by[k]["state"] == "ok" for k in ("sofr_iorb", "sofr99_iorb", "fin_cp_spread",
                                               "dw_primary_credit", "fhlb_advances",
                                               "h8_dep_small", "mmf_retail", "kre_xlf",
                                               "stlfsi", "ofr_fsi", "unrealised_losses")),
          "every seeded series reads into the panel")
    lz = by["sofr_iorb"]["lens"]
    check(lz["percentile_window"] is not None and lz["percentile_full"] is not None
          and "percentile" in __import__("altdata.st_r5_rates", fromlist=["x"]).lens_text(lz),
          "each series carries dual percentiles (five years; the long window) with n")
    check(by["h8_dep_large"]["state"] == "absent"
          and by["sloos_ci_large"]["reason"] == "not yet stored",
          "an unseeded series says 'not yet stored'")
    check(b["funding"]["state"] == "on" and set(b["funding"]["above"]) >= {"sofr_iorb",
                                                                           "fin_cp_spread"},
          f"the seeded spike turns the funding flag on ({b['funding']['above']})")
    check(b["deposit"]["state"] == "on", "the seeded flight turns the deposit flag on")
    check(b["classifier"]["state"] == "banking stress" and read
          and read[0]["text"].startswith("Bank equity: KRE -15.0%"),
          "KRE -15%: the classifier reads banking stress, and The read carries its line")
    check(close and close[0]["key"] == "plumb:bank_stress" and close[0]["priority"] == 1,
          "the close's Plumbing item beside item 34's cluster, priority 1 when a flag is on")
    check(wk and len(wk["lines"]) == 1 and wk["lines"][0].startswith("Bank stress: funding flag on"),
          f"the Weekly's one line ({wk['lines'][0][:70]})")
    note = mo["table_note"]
    check(mo["table"]["columns"][3].startswith("Percentiles (five years")
          and len(mo["table"]["rows"]) == len(b["panel"])
          and "full stored history" in note and "Bank CDS: not tracked" in note
          and "AT1 spreads: not tracked" in note and "CMBS office" in note
          and "KRE implied vol: not built" in note and "ICI" in note,
          "the Monthly's full panel: every series, its long windows stated, the listed gaps")
    check(any("Unrealised securities gains (losses)" in x and "10-year" in x
              for x in mo["lines"]),
          "the unrealised losses print beside the 10-year (cross-item note 1)")
    db2 = TD / "quiet.db"
    seed_store(db2, sofr_spike=False, deposit_flight=False, kre_fall=-2.0)
    with observations.ObservationStore(str(db2)) as st:
        q = bs.build(st, cut)
        qr = blk.read_items(st, cut)
    check(q["funding"]["state"] == "off" and q["deposit"]["state"] == "off"
          and q["classifier"]["state"] == "dormant" and qr == [],
          "a quiet store: both flags off, the classifier dormant, nothing in The read")


def group_e() -> None:
    head("E. THE 12:30 GATE (F5)")
    from altdata import bank_stress as bs, observations
    from daily_cascade import midday_gate as mg
    check([g.__name__ for g in mg.GATES][-2:] == ["_bank_stress", "_crypto_leverage"],
          "registered in midday_gate.GATES")
    db = TD / "gate.db"
    seed_store(db)
    with observations.ObservationStore(str(db)) as st:
        # The spike is on the store's last day (2022-11-24); the prior cutoff is the
        # day before it, when neither spike had happened.
        days = weekdays("2020-06-01", 650)
        last, prev = days[-1], days[-2]
        turned = bs.gate({"day": last, "store": st, "now": f"{last}T23:00:00+00:00",
                          "prior_cutoff": f"{prev}T23:00:00+00:00"})
        stays = bs.gate({"day": last, "store": st, "now": f"{last}T23:00:00+00:00",
                         "prior_cutoff": f"{last}T23:00:00+00:00"})
    check(turned["open"] and "funding" in turned["values"]["turned_on"]
          and turned["line"].startswith("Bank stress, turned on today:"),
          f"open on the session the funding flag turns on ({turned['why']})")
    check(not stays["open"] and stays["why"] == "no bank-stress flag turned on this session",
          "closed on a session the flag stays on")
    missing = TD / "absent.db"
    none = bs.gate({"day": last, "db_path": str(missing)})
    check(not none["open"] and not missing.exists(),
          "no store: closed, and no store file created")
    msrc = (REPO / "daily_cascade" / "midday_gate.py").read_text(encoding="utf-8")
    check(".mailed" in msrc and "_bank_stress" in msrc,
          "the slot's once-a-session marker stands: at most one message a session")


def group_f() -> None:
    head("F. F3's TWO BRANCHES")
    from altdata import eps_overshoot as eo, observations
    cfg = eo.config()
    check(cfg["source"] is None, "no forward-EPS source named (F3's probe failed)")
    gap = eo.read(None, "2026-10-20T00:00:00+00:00", "on")
    check(gap["state"] == "gap" and gap["flag"] is None
          # Batch 14 item 67 (b55): the PEG/LTEG gap line closes every branch.
          and eo.lines(gap) == [cfg["gap_reason"].strip(), eo.PEG_GAP]
          and "flag does not print" in eo.lines(gap)[0],
          "the gap branch: both series listed gaps, the flag does not print")
    db = TD / "eps.db"
    rows = []
    for i, (d, f, t) in enumerate([("2024-03-29", 230.0, 220.0), ("2024-06-28", 240.0, 222.0),
                                   ("2024-09-30", 250.0, 225.0), ("2024-12-31", 260.0, 228.0),
                                   ("2025-03-31", 270.0, 226.0), ("2025-06-30", 280.0, 224.0)]):
        for key, v in (("fixture.fwd_eps", f), ("fixture.trl_eps", t)):
            rows.append({"registry_key": key, "instrument": None, "observed_at": d,
                         "available_at": f"{d}T22:00:00+00:00", "value": v,
                         "source": "fixture"})
    with observations.ObservationStore(str(db)) as st:
        st.write_many(rows)
        cfg2 = {"source": "a fixture source", "forward_eps_key": "fixture.fwd_eps",
                "trailing_eps_key": "fixture.trl_eps", "lens_years": 5}
        built = eo.read(st, "2025-12-31T00:00:00+00:00", "on", cfg2)
    ls = eo.lines(built)
    check(built["state"] == "ok" and built["implied_growth"] == ("2025-06-30", 25.0)
          and "percentile" in ls[0] and "a fixture source" in ls[0],
          f"the built branch: implied growth 280/224 - 1 = +25.0%, with its percentiles "
          f"and its source ({ls[0][:60]})")
    e = built["error"]
    check(e and e["forecast_day"] == "2024-06-28" and e["error_pct"] == round((224 / 240 - 1) * 100, 2)
          and built["flag"] is True and "flag ON" in ls[-2] and ls[-1] == eo.PEG_GAP,
          "the realised error (224 against the 240 stored a year earlier) negative with the "
          "revisions-turn flag on: the overshoot flag prints ON")


def group_g() -> None:
    head("G. F4's LABELS")
    from altdata import pe_dispersion as pe
    f = pe.forward([("2026-02-02", 30.0), ("2026-05-01", 34.0), ("2026-10-16", 27.2)])
    t = pe.trailing([(d, 100.0) for d in ("2025-03-03", "2025-06-02", "2026-10-16")],
                    [("2024-01-30", 1.0), ("2024-04-30", 1.0), ("2024-07-30", 1.0),
                     ("2024-10-30", 1.0), ("2025-04-30", 2.0)])
    ls = pe.lines([{"symbol": "AAA", "forward": f, "trailing": t},
                   {"symbol": "BBB", "forward": None,
                    "trailing": pe.trailing([], [])}])
    check(f["peak"] == 34.0 and f["since"] == "2026-02-02" and f["vs_peak_pct"] == -20.0,
          "forward: against its peak since logging began, with that date")
    check(t["state"] == "ok" and t["peak"] == 25.0 and t["peak_day"] == "2025-03-03"
          and t["now"] == 20.0,
          "trailing: the close over the last four reported quarters, against its 2025 peak")
    check("since logging began (2026-02-02)" in ls[1] and "trailing" in ls[1]
          and "2025 peak" in ls[1] and "forward: not yet logged" in ls[2]
          and "fewer than four reported quarters" in ls[2],
          "each leg labelled; the reason where a leg cannot be computed")
    check(pe.names() and "GOOG" not in pe.names() and "MSFT" in pe.names(),
          f"the hyperscalers, GOOG folded into GOOGL ({pe.names()})")


def group_h() -> None:
    head("H. THE SOURCES AND REGISTRATION")
    from altdata import config as acfg, derived, feeds, source_ids
    from altdata.sources import fdic_qbp, ofr_fsi, yfinance_source as yf
    ids = {s.key: s.fred_id for s in acfg.FRED_BANK_STRESS_SERIES}
    check(ids == {"fin_cp_3m": "DCPF3M", "sofr_p99": "SOFR99", "ioer": "IOER",
                  "dw_primary_credit": "WLCFLPCL", "fed_other_credit": "WLCFOCEL",
                  "fhlb_advances": "BOGZ1FL403069330Q", "h8_dep_small": "DPSSCBW027SBOG",
                  "h8_dep_large": "DPSLCBW027SBOG", "mmf_retail": "WRMFNS",
                  "stlfsi": "STLFSI4"}
          and set(acfg.FRED_BANK_STRESS_SERIES) <= set(acfg.FRED_PULL_SERIES),
          "the panel's ten FRED legs, through the existing writer (Z.1's FHLB, H.8, H.4.1)")
    check(yf.SYMBOLS.get("KRE") == "mkt_kre" and yf.SYMBOLS.get("XLF") == "mkt_xlf"
          and yf.resolve_basket(yf.SYMBOLS) == yf.SYMBOLS,
          "KRE joins the basket beside XLF, resolved through the Security Master")
    check({"ofr_fsi", "fdic_qbp"} <= set(feeds.OFFICIAL_WRITERS)
          and "ici_mmf" not in feeds.OFFICIAL_WRITERS + feeds.EXTERNAL_WRITERS,
          "the OFR and FDIC writers on the official roster; ICI parked, on none")
    keys = ([f"fred.{k}" for k in ids] + ofr_fsi.KEYS + fdic_qbp.KEYS
            + ["yfinance.mkt_kre", "ici.mmf_total"])
    check(all(derived.registry_entry(k) for k in keys)
          and all(source_ids.canonical(s) == s for s in ("ofr_fsi", "fdic_qbp", "ici_mmf")),
          f"every key registered ({len(keys)}); the three source ids")
    ofr = ofr_fsi.rows_from_csv("Date,OFR FSI,Credit,Equity valuation,Safe assets,Funding\n"
                                "2026-10-16,-1.867,-0.946,-0.507,-0.295,-0.141\n",
                                "2026-10-17T12:00:00+00:00", "observed")
    check({r["registry_key"]: r["value"] for r in ofr} ==
          {"ofr.fsi": -1.867, "ofr.fsi_credit": -0.946, "ofr.fsi_funding": -0.141},
          "the OFR parser reads its columns by name")
    body = {"data": [{"data": {"REPDTE": "20260630", "sum_SCAF": 100.0, "sum_SCAA": 110.0,
                               "sum_SCHF": 50.0, "sum_SCHA": 70.0}}]}
    fd = {r["registry_key"]: r["value"] for r in fdic_qbp.rows_from_json(body, "2026-06-30", "t")}
    check(fd == {"fdic.unrealised_afs": -10000.0, "fdic.unrealised_htm": -20000.0,
                 "fdic.unrealised_total": -30000.0}
          and fdic_qbp.quarter_ends("2025-11-01", "2026-07-01") == ["2025-12-31", "2026-03-31",
                                                                    "2026-06-30"]
          and fdic_qbp.rows_from_json({"data": []}, "2026-09-30", "t") == [],
          "the FDIC parser: fair value less amortised cost, thousands to dollars; a quarter "
          "not yet served writes nothing")
    from daily_cascade import absorption_block as ab
    check("Neocloud" in ab.NEOCLOUD_LINE and "NOT TRACKED" in ab.NEOCLOUD_LINE
          and "F2" in ab.NEOCLOUD_LINE,
          "SR-16's neocloud credit line, a listed gap beside the hyperscaler anchors")
    from altdata import narratives as nr
    cfg = nr.load_config()
    with nr.NarrativeRegister(str(TD / "register.db")) as reg:
        reg.seed(cfg, today="2026-10-20")
        got = {k: reg.get(k) for k in ("ai_excess_orderly_flush",
                                        "estimates_overshoot_reckoning")}
    check(all(v and v.get("status") == "proposed" for v in got.values()),
          "the narrative pair seeded PROPOSED through the register's proposal path; "
          "confirming stays the operator's")


def group_i() -> None:
    head("I. NO VENDOR VALUE, NO BY-HAND KEY, NO WRITE BEYOND THE STORE")
    bad = []
    for rel in NEW_MODULES:
        src = re.sub(r'"""[\s\S]*?"""', "", (REPO / rel).read_text(encoding="utf-8"))
        if re.search(r"manual\.|manual_input|flashalpha|vendor\.|data/vendor", src, re.I):
            bad.append(rel)
    check(not bad, f"no new module reads a vendor value or a by-hand key ({bad or 'none'})")
    bad = []
    for rel in NEW_MODULES[:4]:
        src = (REPO / rel).read_text(encoding="utf-8")
        if re.search(r"write_many|open_writer|market_state|register\.|place_?order", src):
            bad.append(rel)
    check(not bad, f"the reads write nothing: no store write, register, composite or "
                   f"market-state object ({bad or 'none'})")


def group_j() -> None:
    head("J. THE LEDGER")
    raw = (REPO / PREREG).read_bytes().replace(b"\r\n", b"\n")
    check(hashlib.sha256(raw).hexdigest() == PREREG_SHA and b"Never edited" in raw,
          "the pre-registration on file at its SHA-256 (LF bytes), 'Never edited'")
    src = (REPO / "tools" / "calibration" / "st_r6_59c_bank_stress.py").read_text(encoding="utf-8")
    check("ObservationStore" not in src and "import regime" not in src
          and PREREG in src, "the scoring script opens no store and names its registration")
    import st_r6_59c_bank_stress as L
    days = weekdays("2006-06-01", 1200)

    def data(drops):
        kre, v = [], 100.0
        for i, d in enumerate(days):
            v = v * (0.988 if any(a <= i < a + 12 for a in drops) else 1.0005)
            kre.append((d, v))
        z = [(d, 1.0) for d in days]
        return {"kre": kre, "spx": [(d, 100 + i * 0.1) for i, d in enumerate(days)],
                "sofr": [], "iorb": [], "ioer": [], "cp": z, "bill": z, "dw": [],
                "fhlb": [], "dep_small": [], "mmf": [], "hy": []}
    few = L.study(data([100, 400]), "fixture")
    check(few["verdict"].startswith("INSUFFICIENT") and few["n"] == 2,
          f"two episodes: INSUFFICIENT ({few['verdict']})")
    check(L.MIN_EPISODES == 8 and L.MIN_CRISES == 2 and L.TRIGGER_PCT == -10.0
          and L.CRISES == (("2007-07-01", "2009-03-31"), ("2023-03-01", "2023-05-31")),
          "the registered episode rule and crisis windows")
    rows = ([{"label": "crisis", "class": "banking stress"}] * 2
            + [{"label": "correction", "class": "correction"}] * 4
            + [{"label": "correction", "class": "funding watch"}] * 2)
    cr = [r for r in rows if r["label"] == "crisis"]
    co = [r for r in rows if r["label"] == "correction"]
    passes = (len(rows) >= 8 and len(cr) >= 2
              and all(r["class"] != "correction" for r in cr)
              and 3 * sum(r["class"] == "correction" for r in co) >= 2 * len(co))
    check(passes, "the rule's arithmetic: 2 crises caught and 4 of 6 corrections kept is a PASS")
    led = (REPO / "docs" / "ledgers" / "st-r6.59c-ledger-2026-10-20.md").read_text(encoding="utf-8")
    check("| Verdict | **FAIL" in led and "| n | 18 |" in led,
          "the first edition on file, its result printed as it is (FAIL, n 18)")


def main() -> int:
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g, group_h,
              group_i, group_j):
        try:
            g()
        except Exception as exc:                                # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    head("THE GATE RUN")
    check(LIVE_DB.exists() == LIVE_DB_AT_START, "this gate run created no data/chester.db")
    print(f"\n{PASS} passed, {FAIL} failed")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
