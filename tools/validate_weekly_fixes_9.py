#!/usr/bin/env python3
"""
WEEKLY-FIXES-9: the rest of the first live Weekly's faults (18 Oct 2026).

    python tools/validate_weekly_fixes_9.py

A code gate: synthetic fixtures in temporary stores. It never reads the live
store, fetches or calls a model, and renders nothing. The detail tables' key
grep (W8-12) runs on the fixture Weekly in validate_weekly_complete (group N).

  A  W8-3   THE FLIP'S WORDS: from the close-vs-flip column -- "crossed on Wed 14
            Oct, below since" when Wednesday to Friday closed below; "held" only
            touched and not crossed; the Tape's status takes them, so the
            writer's "held" is refused; the two flips are labelled by capture
  B  W8-7   THE BOOK B SCANNER: a TRY=X breakout is not scanned, with the
            reason; a stock with no stored volume neither; an FX pair takes no RS
            against SPY; the EURUSD case prints no R ("invalidation too near");
            the Pivots line prints both changes with the date
  C  W8-10  THE VOICES' MEASURE: the chop-range test reads the 10-year the store
            holds when the inflation anchor is absent; "not stored" never names a
            series the edition prints, and names what is missing when nothing is
  D  W8-11  THE BASKET'S MARKET CAP: a column of dashes is dropped with one line;
            a stored cap prints
  E  W8-12  DISPLAY NAMES: "mkt eido volume", "jgb 10y", "mkt vvix" and
            "shares outstanding (SQQQ)" print the repo's names; no ^ or =X
            symbol prints
  F  RULING 2: the technical appendix's audit note says the binding is
            conservative on purpose
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gate_tmp import mkdtemp  # noqa: E402

TMP = Path(mkdtemp("gate_weekly_fixes_9_"))
LINE = "=" * 78
PASS = FAIL = 0


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


_N = 0


def store(rows: list[dict]):
    from altdata import observations
    global _N
    _N += 1
    st = observations.ObservationStore(str(TMP / f"s{_N}.sqlite"))
    st.write_many(rows)
    return st


def row(key, day, value, avail=None, instrument=None):
    return {"registry_key": key, "instrument": instrument, "observed_at": str(day),
            "available_at": avail or f"{day}T21:00:00+00:00", "value": float(value),
            "source": "fixture", "availability_kind": "reconstructed"}


# ---------------------------------------------------------------------------
WEEK = ["2026-10-12", "2026-10-13", "2026-10-14", "2026-10-15", "2026-10-16"]


def sessions(sides, flip=774.67, touch=False):
    out = []
    for d, s in zip(WEEK, sides):
        c = flip + (3.0 if s == "above" else -3.0)
        hi, lo = (c + 1, c - 1) if not touch else (max(c, flip) + 0.5, min(c, flip) - 0.5)
        out.append({"session": d, "close_vs_flip": s, "flip": flip, "close": c,
                    "high": hi, "low": lo})
    return out


def group_a() -> None:
    head("A. W8-3: THE FLIP'S WORDS, FROM THE COLUMN")
    from daily_cascade import stack_prose, weekly_sections as wsec
    fw = wsec.flip_words(sessions(["above", "above", "below", "below", "below"]))
    check(fw["status"] == "crossed" and fw["words"] == "crossed on Wed 14 Oct, below since",
          f"Monday and Tuesday above, Wednesday to Friday below: '{fw['words']}'")
    fh = wsec.flip_words(sessions(["below"] * 5, touch=True))
    check(fh["status"] == "held" and fh["words"].startswith("held: touched"),
          f"every close below, a session touching it: held ('{fh['words']}')")
    fu = wsec.flip_words(sessions(["below"] * 5))
    check(fu["status"] == "untested", f"never touched, never crossed: untested ('{fu['words']}')")
    f2 = wsec.flip_words(sessions(["above", "below", "above", "below", "below"]))
    check(f2["words"] == "crossed 3 times in the week; last on Thu 15 Oct, below since",
          f"a chop across it says how often, and the last crossing ('{f2['words']}')")
    check(wsec.flip_words([]) is None, "no column, no words")
    tape = {"data": {"level_status": {"spy": [
        {"label": "gamma flip", "value": 774.67, "status": "held"},
        {"label": "put wall", "value": 760.0, "status": "untested"}]}},
        "subsections": [{"title": "Levels"}]}
    mech = {"data": {"sessions": sessions(["above", "above", "below", "below", "below"])}}
    wsec.apply_flip_words(tape, mech)
    lv = tape["data"]["level_status"]["spy"][0]
    check(lv["status"] == "crossed" and lv["week_words"].startswith("crossed on Wed")
          and tape["data"]["flip_week"]["side"] == "below",
          "the Tape's flip status takes the column's words, not one session's")
    rows = [{"symbol": "SPY", "name": "S&P 500"}]
    bad = stack_prose.level_status_faults("SPY's gamma flip at 774.67 held.",
                                          tape["data"]["level_status"], rows)
    ok = stack_prose.level_status_faults("SPY crossed below its gamma flip on Wednesday.",
                                         tape["data"]["level_status"], rows)
    check(bad and not ok,
          f"the writer's 'held' is refused against the column; 'crossed' passes ({bad[:1]})")
    cols = wsec.tape_table({"instruments": []})["levels_table"]["columns"]
    src = (REPO / "daily_cascade" / "weekly_sections.py").read_text(encoding="utf-8")
    check("Gamma flip (close capture)" in cols and '"Flip (morning capture)"' in src,
          "two captures, both labelled: the Tape's close capture, Mechanics' morning")
    book = {"instruments": [{"id": "spy", "label": "SPY", "kind": "price",
                             "frame": {"as_of": "2026-10-16", "last": 660.0},
                             "levels": []}]}
    cols2 = wsec.tape_table(book)["levels_table"]["columns"]
    check(cols2[-1] == "Gamma flip (close capture, Fri 16 Oct)",
          f"ruling 2: the close capture prints with its time -- the next session's "
          f"level; the words read the morning's ({cols2[-1]})")
    ws = (REPO / "daily_cascade" / "weekly_stack.py").read_text(encoding="utf-8")
    check("wsec.apply_flip_words(tape, mech)" in ws, "the Weekly applies it")


# ---------------------------------------------------------------------------
def inst(sym: str, closes: list[float], volume: bool = True) -> dict:
    days = [f"2026-{7 + i // 28:02d}-{1 + i % 28:02d}" for i in range(len(closes))]
    return {"symbol": sym, "key": f"yfinance.mkt_{sym.lower()}", "days": days,
            "close": closes, "high": [c * 1.001 for c in closes],
            "low": [c * 0.999 for c in closes], "has_range": False,
            "volume": ({d: 1e6 for d in days} if volume else {}), "vol_unit": "shares"}


def group_b() -> None:
    head("B. W8-7: THE BOOK B SCANNER")
    from altdata import book_b_scanner as bbs
    cfg = bbs.load_config()
    base = [30.0 + 0.01 * (i % 7) for i in range(80)] + [31.5, 31.6, 31.7]
    try_ = inst("TRY=X", base, volume=False)
    pv = bbs.detect(try_, cfg)
    check(not [p for p in pv if p["setup"] == "breakout"]
          and "TRY=X: a currency pair" in str(try_.get("breakout_skipped")),
          f"a TRY=X breakout is not scanned, with the reason ({try_.get('breakout_skipped')})")
    stock = inst("ABCD", base, volume=False)
    bbs.detect(stock, cfg)
    check("no stored volume" in str(stock.get("breakout_skipped")),
          f"a stock with no stored volume is not breakout-scanned ({stock.get('breakout_skipped')})")
    vol = inst("ABCD", base, volume=True)
    bbs.detect(vol, cfg)
    check(not vol.get("breakout_skipped"), "one with volume is scanned as before")
    bench = inst("SPY", [400 + i for i in range(83)])
    check(bbs.rs_percentile(inst("EURUSD=X", base), bench, 60) is None
          and bbs.rs_percentile(vol, bench, 60) is not None,
          "an FX pair takes no RS against SPY; a stock does")
    conf = bbs.confirm({"symbol": "EURUSD=X", "d": 1, "rs_pct": None},
                       {"positioning": {}, "tells": {}, "moves": None,
                        "top_bottom": {"available": False}, "alt_assets": set(),
                        "breaks": None}, cfg)
    check(conf[0]["text"] == "relative strength not read (a currency pair: no RS against SPY)",
          f"and says why ({conf[0]['text']})")
    # THE EURUSD "7.9R" CASE: an invalidation a few pips from the entry.
    ec = [1.0800 + 0.0005 * ((-1) ** i) for i in range(80)] + [1.0810]
    eu = inst("EURUSD=X", ec)
    E = len(ec) - 1
    entry = ec[E]
    pv = {"setup": "reclaim", "d": 1, "t": E, "level": entry - 0.0001,
          "level_label": "the 50-day", "inv_level": entry - 0.0001, "move": 0.0080,
          "base": None, "lost_sessions": 3, "volume_ratio": 2.0,
          "volume_unconfirmed": False}
    ctx = {"regime": {"macro": "Expansion", "gamma": None, "vol": None},
           "bench": bench, "positioning": {}, "tells": {}, "moves": None,
           "top_bottom": {"available": False}, "alt_assets": set(), "breaks": None,
           "calendar": None, "setups": {}, "capital": 300000.0}
    c = bbs.draft(eu, pv, ctx, cfg, "2026-10-16")
    a, _ = bbs.atr(eu, E, 14)
    old_r = (pv["level"] + pv["move"] - entry) / c["risk"]
    check(c["expected_r"] is None and str(c["r_note"]).startswith(
              "R not computed: invalidation too near")
          and "a currency pair's floor" in str(c["r_note"])
          and c["risk"] < 0.5 * a and old_r > 5,
          f"EURUSD: the invalidation {c['risk']:.4f} from the entry is inside a pair's "
          f"floor, half an ATR alone ({0.5 * a:.4f}; ruling 1); no R where "
          f"{old_r:.1f}R printed before")
    # RULING 1: the same distance, between half an ATR and 0.5% of price, is
    # R for a pair and no R for a stock.
    mid = dict(pv, level=entry - 0.0010, inv_level=entry - 0.0010)
    cm = bbs.draft(eu, mid, ctx, cfg, "2026-10-16")
    st_ = inst("ABCD", ec)
    cs = bbs.draft(st_, mid, ctx, cfg, "2026-10-16")
    check(0.5 * a < cm["risk"] < 0.005 * entry
          and isinstance(cm["expected_r"], float) and cs["expected_r"] is None
          and "the larger of half an ATR and 0.5% of price" in str(cs["r_note"]),
          f"an invalidation {cm['risk']:.4f} away, past half an ATR ({0.5 * a:.4f}) and "
          f"inside 0.5% ({0.005 * entry:.4f}): a pair prints {cm['expected_r']}R, a "
          f"stock no R (ruling 1)")
    from daily_cascade import book_b
    line = book_b.candidate_line(1, {**c, "score": 0.5, "rank": 1})
    check("R not computed: invalidation too near" in line and "R (the measured" not in line,
          "the candidate's line prints the note and no R")
    far = dict(pv, level=entry - 0.0100, inv_level=entry - 0.0100, move=0.0300)
    cf = bbs.draft(eu, far, ctx, cfg, "2026-10-16")
    check(isinstance(cf["expected_r"], float) and cf["r_note"] is None,
          f"beyond the floor R prints as before ({cf['expected_r']}R)")
    p = bbs.parameters_line(cfg)
    check("Changed 18 Oct 2026" in p and "no =X currency pair" in p
          and "for equities and ETFs the larger of 0.5 ATR and 0.5% of price, for a "
              "currency pair 0.5 ATR alone" in p,
          "the Pivots line prints both changes with the date, and both floors")
    flow = {"fired": 0, "reviewed": 0, "drafted": 0, "approved": 0,
            "decisions_open": 0, "passed_over": 0, "passed_candidates": []}
    note = book_b.subsections([], flow, {"skipped": {"breakout_not_scanned": [
        {"symbol": "TRY=X", "reason": try_["breakout_skipped"]}]}})[0]
    notes = (note[0] if isinstance(note, list) else note).get("notes") or []
    check(any(n.startswith("Not scanned for breakouts: TRY=X") for n in notes),
          "the block's note names who was not scanned, and why")


# ---------------------------------------------------------------------------
def group_c() -> None:
    head("C. W8-10: THE VOICES' MEASURE")
    from altdata import rates_shape as rs
    voice = [{"voice": "V", "claim": "a 5.0-5.5% chop", "test": "level_band",
              "band": [5.0, 5.5], "spiral_above": 5.5}]
    sh, so = {"state": None}, {"current": None}
    absent = {"inflation": {"state": "absent",
                            "reason": "CPI or the 10-year not stored for the trailing 10 years"}}
    with store([row("yfinance.mkt_tnx", "2026-10-15", 4.10),
                row("yfinance.mkt_tnx", "2026-10-16", 4.12)]) as st:
        lvl = rs.ten_year_level(st, "2026-10-18T09:00:00+00:00")
    v = rs.adjudicate(sh, so, absent, {"voices": voice}, lvl)[0]
    check(v["measure"].startswith("10-year 4.12% (Yahoo Finance, 2026-10-16)")
          and v["verdict"] == "not consistent" and "not stored" not in v["measure"],
          f"the anchor absent, the tape's 10-year is read and named ({v['measure']})")
    with store([row("fred.yield_10y", "2026-10-15", 4.11),
                row("yfinance.mkt_tnx", "2026-10-16", 4.12)]) as st:
        lvl2 = rs.ten_year_level(st, "2026-10-18T09:00:00+00:00")
    check(lvl2 == {"value": 4.12, "as_of": "2026-10-16", "source": "Yahoo Finance"},
          "the newer of FRED's and the tape's")
    none = rs.adjudicate(sh, so, absent, {"voices": voice}, None)[0]
    check(none["measure"] == ("the 10-year's latest close, for the 5-5.5% chop-range "
                              "test: no 10-year (FRED's or the tape's) at the cutoff")
          and none["verdict"] == "not testable yet",
          f"with nothing stored it names what is missing and for which test ({none['measure']})")
    ok = rs.adjudicate(sh, so, {"inflation": {"ten_year_pct": 4.3}}, {"voices": voice}, lvl)[0]
    check(ok["measure"].startswith("10-year 4.30%;"),
          "the anchor's own 10-year, where present, is read first and unlabelled as before")


# ---------------------------------------------------------------------------
def group_d() -> None:
    head("D. W8-11: THE BASKET'S MARKET CAP")
    from altdata import crypto_basket as cb
    t = {"columns": ["Name", "Market cap", "What pays"], "rows": [["A", "—", "x"]]}
    cb.drop_column(t, "Market cap")
    check(t == {"columns": ["Name", "What pays"], "rows": [["A", "x"]]},
          "drop_column removes the head and every row's cell")
    names = list(cb.names(cb.config()))
    sym = names[0]
    # Prices stored, no cap for any name: this morning's twelve dashes.
    with store([row(cb.price_key(sym), "2026-10-15", 10.0)]) as st:
        wb = cb.weekly_block(st, "2026-10-16", "2026-10-18T09:00:00+00:00")
    det = wb["detail"]
    tabs = det.get("tables") or []
    check(tabs and "Market cap" not in tabs[0]["columns"]
          and cb.MCAP_NOT_STORED in det["notes"],
          "a price stored but no cap for any name: the column is dropped, with one line")
    with store([]) as st:
        wb0 = cb.weekly_block(st, "2026-10-16", "2026-10-18T09:00:00+00:00")
    check(wb0["detail"].get("lines") and "not stored" in wb0["detail"]["lines"][0],
          "nothing stored at all: the one-line block, as weekly-fixes-7 ruled")
    with store([row(f"llama.mcap_{sym.lower()}", "2026-10-15", 2.3e9)]) as st:
        wb2 = cb.weekly_block(st, "2026-10-16", "2026-10-18T09:00:00+00:00")
    t2 = wb2["detail"]["tables"][0]
    i = t2["columns"].index("Market cap")
    check(t2["rows"][0][i] != "—" and cb.MCAP_NOT_STORED not in wb2["detail"]["notes"],
          f"a stored cap prints, and the column stays ({t2['rows'][0][i]})")


# ---------------------------------------------------------------------------
def group_e() -> None:
    head("E. W8-12: DISPLAY NAMES")
    import re
    from altdata import labels
    want = {"yfinance.mkt_eido_volume": "iShares MSCI Indonesia ETF (EIDO) volume",
            "mof.jgb_10y": "Japan 10-year (JGB)",
            "yfinance.mkt_vvix": "the VVIX (the VIX's own volatility)",
            "levetf.shares_outstanding": "leveraged-ETF shares outstanding",
            "yfinance.mkt_tnx": "10-year yield", "yfinance.mkt_eurchf": "EUR/CHF"}
    for k, v in want.items():
        got = labels.metric(k)
        check(got == v, f"{k} -> {got!r}")
    names = [labels.metric(f"yfinance.mkt_{s}") for s in ("tnx", "vvix", "eurchf", "tyx")]
    check(not any(re.search(r"\^|=X", n) for n in names),
          f"no ^ or =X symbol prints as a name ({names})")
    check(labels.metric("calc.some_new_metric") == "some new metric",
          "a key with no name anywhere keeps the plain form (and the grep in "
          "validate_weekly_complete N catches it in a table)")
    src = (REPO / "tools" / "validate_weekly_complete.py").read_text(encoding="utf-8")
    check("N. W8-12: THE DETAIL TABLES PRINT DISPLAY NAMES" in src,
          "the rendered detail tables are grepped for keys")


# ---------------------------------------------------------------------------
def group_f() -> None:
    head("F. RULING 2: THE APPENDIX'S AUDIT NOTE")
    from daily_cascade import stack as stack_mod
    rows = {r["quantity"]: r for r in
            (stack_mod.config().get("technical_appendix") or {}).get("rows") or []}
    a = rows.get("Numeral audit") or {}
    check("Deliberately conservative" in str(a.get("formula"))
          and "a spread between two series" in str(a.get("formula"))
          and "named nearest before it in its clause" in str(a.get("formula")),
          "the technical appendix says the binding is conservative on purpose")


def main() -> int:
    for g in (group_a, group_b, group_c, group_d, group_e, group_f):
        g()
    print(f"\n{PASS} passed, {FAIL} failed")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
