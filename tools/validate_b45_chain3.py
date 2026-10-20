#!/usr/bin/env python3
"""
Validation gate: b45-chain3 -- session B's third-chain branch (19 Oct 2026), where
no existing gate is the home. On fixtures; no network, no model, no live store.

  A  RULING 6 OF 19 OCT 2026. An assessed mechanism-watch entry is posted to the
     narrative register as a PROPOSED story through its existing proposal path,
     with its factor's implied outcome and horizon, citing its source stored as a
     headline event; nothing is confirmed, and the entry's grade moves from
     "awaiting its posting" to "proposed"; a refused posting keeps the entry
     pending with its reason. Each of the seven feeds carries its terms-read date;
     the Monthly line names a feed read 93 days before its as-of and not one read
     92. The PRL part reads exactly its allowed keys -- calc.prl_*, and the
     explorer's pearl.chain_* and the basket's PRL price directly -- and no
     calc.prl_* key copies them.
  B  X-3.4, ENGINE 7 (alpha/engines/intraday_dealer.py): see its section below.
  C  R7 (19 Oct 2026): the posting templates accepted, and a posted story's base
     rate beside its grade -- the share of the stored history's 182-day windows in
     which the linked instrument closed higher, with the span and n, as of the
     grade; on a synthetic close series counted by hand, the point-in-time cut,
     no clause on a pending entry, and both render paths.

    python tools/validate_b45_chain3.py
"""

from __future__ import annotations

import datetime as dt
import os
import socket
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

TD = Path(gate_mkdtemp("b45_chain3_"))
os.environ["CHESTER_DB"] = str(TD / "store.sqlite")
os.environ.pop("ALPHA_DB", None)
for _k, _d in (("ALPHA_INBOX", "inbox"), ("ALPHA_OUTBOX", "outbox"),
               ("ALPHA_RESEARCH_DIR", "research"), ("ALPHA_REPORTS_DIR", "reports")):
    os.environ[_k] = str(TD / _d)
os.environ["CHESTER_UNIT_STARTED"] = "0"
PASS = FAIL = 0
LINE = "=" * 78


def _no_connect(*a, **k):
    raise OSError("validate_b45_chain3: no network in a code gate")


socket.socket.connect = _no_connect                             # type: ignore[method-assign]
socket.create_connection = _no_connect                          # type: ignore[assignment]


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


# ---------------------------------------------------------------------------
# A. Ruling 6
# ---------------------------------------------------------------------------
def group_a() -> None:
    from altdata import mechanism_watch as mw, narratives as nr
    from monthly_macro import prl_part
    head("A. RULING 6 OF 19 OCT 2026: POSTED AS PROPOSED, THE FEEDS' TERMS, THE PRL READS")
    db = str(TD / "a.sqlite")
    with mw.Register(db) as r:
        mid = r.add_candidate({"name": "Lumen", "stage": "mainnet",
                               "mechanism_class": "proof of useful work"},
                              origin="llm_draft", prefilter={"hits": ["fixture"]},
                              at="2026-10-24T14:00:00+00:00")
        e1 = r.add_entry("Lumen: a useful-work chain reached mainnet.", "I",
                         "https://example.org/lumen", mid, "2026-10-24T14:00:00+00:00")
        e2 = r.add_entry("Ferrum: a reserve token backed by a commodity basket.", "V",
                         "the scan", None, "2026-10-24T14:00:00+00:00")
        check(r.conn.execute("SELECT grade FROM mechanism_watch_entries WHERE id=?",
                             (e1,)).fetchone()[0] == mw.GRADE_PENDING == "awaiting its posting",
              "a drafted entry waits at 'awaiting its posting' (no G-29 scale)")
        bad = {"factors": {"I": {"direction": "x", "linked_dimensions": {"nonsense": "+"},
                                 "implied_outcome": {"claim": "x", "metrics": ["no.key"],
                                                     "comparison": "up", "quorum": 1,
                                                     "horizon_days": 182}}}}
        refused = mw.post_entries(r, db, cfg=bad)
        row = r.conn.execute("SELECT grade, narrative_id, post_note FROM "
                             "mechanism_watch_entries WHERE id=?", (e1,)).fetchone()
        check(refused["posted"] == [] and row[0] == mw.GRADE_PENDING and row[1] is None
              and "not registered" in (row[2] or ""),
              "a posting the narrative register refuses leaves the entry pending, with "
              "the reason")
        out = mw.post_entries(r, db, at="2026-10-24T15:00:00+00:00")
        ents = {x["id"]: dict(x) for x in r.conn.execute(
            "SELECT * FROM mechanism_watch_entries").fetchall()}
        cand = r.conn.execute("SELECT grade FROM mechanism_watch WHERE id=?",
                              (mid,)).fetchone()[0]
    with nr.NarrativeRegister(db) as g:
        stories = {s["narrative_id"]: s for s in g.all()}
    n1, n2 = ents[e1]["narrative_id"], ents[e2]["narrative_id"]
    s1, s2 = stories.get(n1), stories.get(n2)
    io1 = s1["implied_outcome"] if s1 else {}
    check(len(out["posted"]) == 2 and s1 and s2
          and s1["status"] == s2["status"] == "proposed"
          and s1["origin"] == "proposal" and s1["opened"] is None,
          f"both entries are posted as PROPOSED stories through the existing proposal "
          f"path ({n1}, {n2}); nothing is confirmed")
    check(io1.get("metrics") == ["yfinance.mkt_nvda"] and io1.get("horizon_days") == 182
          and s2["implied_outcome"]["metrics"] == ["yfinance.mkt_btc_usd"]
          and "Lumen" in s1["name"] and "Lumen: a useful-work chain" in s1["direction"],
          "each carries its factor's implied outcome and horizon (Factor I: NVDA up over "
          "182 days; Factor V: BTC-USD up), the entry's text as its direction")
    from altdata import events as ev_mod
    with ev_mod.EventStore(db) as es:
        basis = es.conn.execute("SELECT type, url FROM events WHERE id IN (%s)" % ",".join(
            str(int(x)) for s in (s1, s2) for x in (s["proposal_basis"]
                                                     if isinstance(s["proposal_basis"], list)
                                                     else __import__("json").loads(
                                                         s["proposal_basis"] or "[]")))
        ).fetchall()
    check(len(basis) == 2 and all(b[0] == "headline" for b in basis)
          and ("https://example.org/lumen",) in [(b[1],) for b in basis],
          "each proposal cites its source, stored first as a headline event")
    check(ents[e1]["grade"] == ents[e2]["grade"] == mw.GRADE_PROPOSED == "proposed"
          and cand == "proposed" and ents[e1]["posted_at"].startswith("2026-10-24"),
          "the entries and the candidate move from 'awaiting its posting' to 'proposed'")
    with mw.Register(db) as r:
        again = mw.post_entries(r, db)
    check(again["posted"] == [] and again["refused"] == [],
          "a posted entry is never posted twice")
    src = (REPO / "altdata" / "mechanism_watch.py").read_text(encoding="utf-8")
    check(".confirm(" not in src and ".reject(" not in src.replace("def reject", ""),
          "nothing in the posting confirms or rejects: the narrative register's gate is "
          "the operator's")

    from altdata.mechanism_scan import config as scan_config
    feeds = scan_config().get("feeds") or []
    check(len(feeds) == 7 and all(f.get("terms_read") for f in feeds),
          "each of the seven feeds carries its terms-read date in the catalogue")
    fx = [{"id": "old", "terms_read": "2026-07-19"}, {"id": "edge", "terms_read": "2026-07-20"},
          {"id": "new", "terms_read": "2026-10-18"}, {"id": "none"}]
    line = prl_part.feeds_terms_line("2026-10-20T21:00:00+00:00", fx)
    check(line and "old (read 2026-07-19)" in line and "edge" not in line
          and "new" not in line and "none (no date)" in line
          and prl_part.feeds_terms_line("2026-10-20T21:00:00+00:00", fx[2:3]) is None,
          f"the Monthly line names a feed read 93 days before its as-of and not one "
          f"read 92: {line}")

    from altdata import prl
    allowed = prl_part.allowed_reads()
    seen: list = []
    real = prl_part._latest                                     # noqa: SLF001
    prl_part._latest = lambda st, k, at: seen.append(k)         # noqa: SLF001
    try:
        prl_part.read(None, "2026-10-20T21:00:00+00:00", "2026-09-20T21:00:00+00:00")
    finally:
        prl_part._latest = real                                 # noqa: SLF001
    direct = {prl.HEIGHT_KEY, prl.SUPPLY_KEY, prl.DIFFICULTY_KEY, "yfinance.crypto_prl"}
    check(set(seen) == set(allowed.values())
          and direct <= set(seen)
          and all(k.startswith("calc.prl_") for k in set(seen) - direct),
          "the PRL part reads exactly its allowed keys: calc.prl_*, and pearl.chain_* and "
          "the basket's PRL price directly")
    copies = [k for k in prl.KEYS.values()
              if k in ("calc.prl_height", "calc.prl_supply", "calc.prl_difficulty",
                       "calc.prl_price", "calc.prl_volume")]
    check(not copies and "ruling 6 of 19 Oct 2026" in (REPO / "monthly_macro" /
                                                       "prl_part.py").read_text(encoding="utf-8"),
          "no calc.prl_* key copies the explorer's rows or the price; the docstring "
          "states the ruling")


# ---------------------------------------------------------------------------
# B. Engine 7
# ---------------------------------------------------------------------------
def _sessions(first: str, n: int) -> list[str]:
    from altdata import session
    out, d = [], dt.date.fromisoformat(first)
    while len(out) < n:
        if session.is_trading_session(d):
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def _utc(day: str, hhmm: str) -> str:
    from zoneinfo import ZoneInfo
    from altdata import observations
    h, m = (int(x) for x in hhmm.split(":"))
    local = dt.datetime.combine(dt.date.fromisoformat(day), dt.time(h, m),
                                ZoneInfo("America/New_York"))
    return observations.canonical_instant(local.isoformat())


def build_engine7(root: Path, db: str, days: list[str], late: str = "") -> None:
    """SPY each session: open 100, the 09:45 capture's spot 100.2 (an up move) in a
    positive gamma regime, the 09:50 bar opens 100.2, the 12:30 bar 100.0, the
    close 99.9: a reversal. `late`'s capture is computed at 10:20, after the
    deadline."""
    import json
    import sqlite3
    from altdata import bars as bars_mod, observations
    rows, bar_rows = [], []
    for d in days:
        rows += [{"registry_key": "yfinance.mkt_spy_open", "instrument": None,
                  "observed_at": d, "available_at": _utc(d, "16:20"), "value": 100.0,
                  "source": "synthetic"},
                 {"registry_key": "yfinance.mkt_spy", "instrument": None,
                  "observed_at": d, "available_at": _utc(d, "16:20"), "value": 99.9,
                  "source": "synthetic"}]
        for k in range(78):                                     # 09:30 .. 15:55
            t = (dt.datetime(2000, 1, 1, 9, 30) + dt.timedelta(minutes=5 * k)).strftime("%H:%M")
            px = 100.2 if t < "12:30" else 100.0
            bar_rows.append(("spy", "SPY", "5m", _utc(d, t), px, px, px, px, 1000.0,
                             _utc(d, "16:12"), _utc(d, "16:12"), "synthetic"))
        dd = root / d
        dd.mkdir(parents=True, exist_ok=True)
        chain = dd / "SPY_chain.csv"
        chain.write_text("symbol,dte,volume\nSPY,0,600\nSPY,7,300\nSPY,30,100\n",
                         encoding="utf-8")
        comp = "10:20" if d == late else "09:47"
        (dd / "SPY_134600Z_exposure.json").write_text(json.dumps({
            "symbol": "SPY", "fetched_at": _utc(d, "09:46"), "computed_at": _utc(d, comp),
            "spot": 100.2, "capture": "intraday", "source_chain": str(chain),
            "overall": {"net_gex": 1.5e9, "net_to_gross": 0.3}}), encoding="utf-8")
    st = observations.ObservationStore(db)
    st.write_many(rows)
    st.close()
    con = sqlite3.connect(db)
    con.executescript(bars_mod.SCHEMA)
    con.executemany("INSERT OR IGNORE INTO bars (instrument, symbol, interval, observed_at, "
                    "open, high, low, close, volume, available_at, ingested_at, source) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", bar_rows)
    con.commit()
    con.close()


def group_b() -> None:
    import copy
    from alpha.engines import intraday_dealer as E
    from alpha.store import ReadOnlyStore
    head("B. X-3.4, ENGINE 7: INTRADAY DEALER REGIMES")
    cfg = E.load_config()
    check(E.spec_sha256(cfg) == cfg["spec_sha256"]
          and cfg["spec_sha256"] in (REPO / "alpha" / "research" /
                                     "roster-2026-10-19-x3-4.yaml").read_text(encoding="utf-8"),
          "the spec hashes to the sha256 the roster's E-7 quotes")
    bad = copy.deepcopy(cfg)
    bad["spec"]["data_gate"]["min_formation_sessions"] = 20
    try:
        E.check_spec(bad)
        refused = False
    except E.SpecChanged:
        refused = True
    check(refused, "a changed spec is refused")

    days = _sessions("2026-06-01", 37)
    root29, db29 = TD / "c29", str(TD / "e29.sqlite")
    build_engine7(root29, db29, days[:29])
    st = ReadOnlyStore(db29)
    try:
        eng = E.IntradayDealerEngine({"computed_dir": str(root29)})
        as_of = _utc(days[28], "20:00")
        sc = eng.scan(st, as_of)
        rows29 = eng.refit_rows(st, as_of)
    finally:
        st.close()
    check(list(sc) == ["SPY:positive:+"] and sc["SPY:positive:+"]["line"]
          == "awaiting (n=29 of 30)" and rows29 == [],
          f"at n=29 the bucket awaits and trades nothing: "
          f"{sc.get('SPY:positive:+', {}).get('line')}")

    root, db = TD / "c37", str(TD / "e37.sqlite")
    build_engine7(root, db, days, late=days[34])
    st = ReadOnlyStore(db)
    try:
        eng = E.IntradayDealerEngine({"computed_dir": str(root)})
        as_of = _utc(days[-1], "20:00")
        caps = E.captures("SPY", eng.spec, root)
        sc = eng.scan(st, as_of)
        trades = eng.refit_rows(st, as_of)
        one = eng.session_row(st, "SPY", caps[days[0]], as_of)
        lines = eng.lines(st, as_of)
        sigs = eng.signal(as_of, st)
    finally:
        st.close()
    b = sc["SPY:positive:+"]
    check(b["open"] and b["side"] == "reversal" and b["exit"] == "exit_close"
          and b["trades"] and b["open_after"] == days[29],
          f"at n=30 it opens on its formation sample: {b['line']}")
    check(len(trades) == 6 and all(t["day"] > days[29] for t in trades)
          and days[34] not in [t["day"] for t in trades],
          f"it trades only the sessions after its formation ({len(trades)}: 7 later "
          f"sessions less the one whose capture was late)")
    check(days[34] not in caps and len(caps) == 36,
          "a capture computed after its decision deadline (10:20 against 10:15) is never "
          "read: that session has no decision")
    check(one["entry_bar"] >= one["decided_at"] and one["entry"] == 100.2
          and one["entry_bar"] == _utc(days[0], "09:50"),
          "the entry is the first stored 5-minute bar at or after the decision (09:50 "
          "against a 09:47 decision), never a price observed before it")
    c = eng.cost(500.0)
    check(abs(c - 0.0023) < 1e-12 and abs(one["cost"] - eng.cost(100.2)) < 1e-15,
          f"costs reproduce a hand figure: 2 x (1.5 + 5 + 5) bp = 23 bp at $2,000 of "
          f"capital ({c * 1e4:.2f} bp)")
    want = -(99.9 / 100.2 - 1.0) - eng.cost(100.2)
    check(abs(one["net"]["reversal|exit_close"] - want) < 1e-12
          and abs(one["zero_dte_share"] - 0.6) < 1e-12 and one["zero_dte_label"] == "no side",
          "a session's net is the move against the entry less costs, by hand; the 0DTE "
          "share (600 of 1,000) is recorded, labelled no side")
    check(any(ln.startswith("vwap: not tracked") for ln in lines)
          and any(ln.startswith("opening_range: not tracked") for ln in lines)
          and any("listed, not built" in ln for ln in lines) and sigs == [],
          "VWAP and the opening range print not tracked with the writer listed; no "
          "signal is queued (the nightly loop cannot act at 09:45)")

    class Spy(dict):
        def __init__(self, base):
            super().__init__(base)
            self.read: list = []

        def get(self, k, d=None):
            self.read.append(k)
            return super().get(k, d)

        def __getitem__(self, k):
            self.read.append(k)
            return super().__getitem__(k)
    real = os.environ
    spy = Spy(real)
    spy["FLASHALPHA_API_KEY"] = "sentinel-not-a-key"
    os.environ = spy                                            # type: ignore[assignment]
    try:
        st = ReadOnlyStore(db)
        try:
            E.IntradayDealerEngine({"computed_dir": str(root)}).scan(st, as_of)
        finally:
            st.close()
    finally:
        os.environ = real                                       # type: ignore[assignment]
    src = (REPO / "alpha" / "engines" / "intraday_dealer.py").read_text(encoding="utf-8")
    check(not any("FLASHALPHA" in str(k).upper() for k in spy.read)
          and "flashalpha" not in src.lower().replace("no flashalpha key", "")
          and "data/vendor" not in src.replace("no data/vendor file", ""),
          "no FlashAlpha key is read and no vendor file opened: the engine reads our own "
          "captures only")


# ---------------------------------------------------------------------------
# C. R7: a posted story's base rate
# ---------------------------------------------------------------------------
# SYNTHETIC closes, not market data: six "NVDA" closes two months apart. By hand,
# with the grade on 2026-01-15 and a 182-day horizon, four windows have ended:
#   2025-01-01 100 -> 2025-07-02, last close 2025-07-01  95   lower
#   2025-03-01  90 -> 2025-08-30, last close 2025-07-01  95   higher
#   2025-05-01 110 -> 2025-10-30, last close 2025-09-01 120   higher
#   2025-07-01  95 -> 2025-12-30, last close 2025-11-01 105   higher
# 2025-09-01's window ends 2026-03-02, after the grade. 3 of 4: 75%.
# A 2025-12-01 close of 50 made available on 2026-02-01 (after the grade) would
# turn the last window lower if it were read.
SYNTH_CLOSES = (("2025-01-01", 100.0), ("2025-03-01", 90.0), ("2025-05-01", 110.0),
                ("2025-07-01", 95.0), ("2025-09-01", 120.0), ("2025-11-01", 105.0))


def group_c() -> None:
    from altdata import mechanism_watch as mw, observations
    from monthly_macro import prl_part
    head("C. R7: A POSTED STORY'S BASE RATE BESIDE ITS GRADE")
    db = str(TD / "c.sqlite")
    with observations.ObservationStore(db) as st:
        st.write_many([{"registry_key": "yfinance.mkt_nvda", "instrument": None,
                        "observed_at": d, "available_at": f"{d}T21:00:00+00:00",
                        "value": v, "source": "yfinance"} for d, v in SYNTH_CLOSES]
                      + [{"registry_key": "yfinance.mkt_nvda", "instrument": None,
                          "observed_at": "2025-12-01",
                          "available_at": "2026-02-01T21:00:00+00:00",
                          "value": 50.0, "source": "yfinance"}])
    graded = "2026-01-15T15:00:00+00:00"
    with mw.Register(db) as r:
        mid = r.add_candidate({"name": "Lumen", "stage": "mainnet",
                               "mechanism_class": "proof of useful work"},
                              origin="llm_draft", prefilter={"hits": ["fixture"]},
                              at="2026-01-15T14:00:00+00:00")
        e1 = r.add_entry("Lumen: a useful-work chain reached mainnet.", "I",
                         "https://example.org/lumen", mid, "2026-01-15T14:00:00+00:00")
        e2 = r.add_entry("Ferrum: a reserve token backed by a commodity basket.", "V",
                         "the scan", None, "2026-01-15T14:00:00+00:00")
        r.mark_posted(e1, "mwatch_fixture_e1", graded)
    t = mw.posting_config()["factors"]["I"]
    with mw.Register(db, readonly=True) as reg:
        br = mw.base_rate(reg.conn, t, graded)
        late = mw.base_rate(reg.conn, t, "2026-02-02T15:00:00+00:00")
        ents = reg.month("0000-00-00", "9999-12-31")["entries"]
        clause = mw.entry_base_rate(reg.conn, [e for e in ents if e["id"] == e1][0])
        pending = mw.entry_base_rate(reg.conn, [e for e in ents if e["id"] == e2][0])
        md = mw.render(reg.all(), ents, as_of="2026-01-31", conn=reg.conn)
    check(br["n"] == 4 and br["higher"] == 3 and br["share"] == 0.75
          and br["first"] == "2025-01-01" and br["last"] == "2025-07-01"
          and br["instrument"] == "NVDA" and br["horizon_days"] == 182,
          f"the share, n and span are the hand count: 3 of 4 windows, 75%, starts "
          f"2025-01-01 to 2025-07-01 ({br})")
    check(late["n"] == 4 and late["higher"] == 2,
          "point in time: the close made available after the grade is not read as of "
          "the grade, and is read once it is knowable (2 of 4 then)")
    want = ("base rate: NVDA closed higher over 182 days in 75% of 4 windows "
            "(starts 2025-01-01 to 2025-07-01; as of 2026-01-15)")
    check(clause == want, f"the clause is code-written: {clause}")
    check(pending is None and md.count(want) == 2,
          "a pending entry prints no base rate; the register view prints it beside the "
          "posted entry's grade and the candidate's Grade cell")
    with observations.ObservationStore(db) as st:
        part = prl_part.build(st, "2026-01-31T21:00:00+00:00",
                              "2025-12-31T21:00:00+00:00", db_path=db)
    lines = [l for p in part if p.get("title") == prl_part.TITLE_ENTRIES
             for l in p["lines"]]
    check(any(f"proposed ({want}) as mwatch_fixture_e1" in l for l in lines)
          and not any("base rate" in l for l in lines if "Ferrum" in l),
          "the Monthly's entries list prints it beside the posted entry's grade, and not "
          "beside the pending one")
    empty = mw.base_rate(None, t, graded)
    check(mw.base_rate_clause(empty).startswith("base rate: awaiting history (NVDA"),
          f"with no stored window it says so: {mw.base_rate_clause(empty)}")


def main() -> int:
    try:
        group_a()
        group_b()
        group_c()
    finally:
        import shutil                                           # noqa: PLC0415
        shutil.rmtree(TD, ignore_errors=True)
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
