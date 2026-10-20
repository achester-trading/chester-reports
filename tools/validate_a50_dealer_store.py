"""
a50-dealer-store (session A, 19 Oct 2026): decisions 9 and 10 of 19 Oct 15:59 ET
and the fix from A48's local-run note.

  A  THE WRITER. One synthetic profile per slot (09:45, 12:30 intraday; 16:10
     settled) becomes rows of the seven keys: instrument the symbol, observed_at
     the slot's ET instant, available_at the file's computed_at (never the write
     instant), source dealer_capture:<the capture's id>; the regime word is the
     gate's (net-to-gross at least 0.10, else "indeterminate"); a re-store is a
     no-op, a dry run writes nothing and creates no file. Refused: a
     vendor-gamma profile, a *_gex.json, a restricted (Brookfield) symbol, a
     capture outside every slot.

  B  WHERE IT RUNS. The 09:45 capture stores its profiles after compute when it
     is named a store; given its own out_dir without one it stores nothing. The
     EOD pass's Stage 2b sits after Stage 2 and before Stage 3; the step never
     raises. No unit and no timer of its own.

  C  THE BACKFILL reads the files on disk, dry run first: counts, the first and
     last session, nothing written dry; then the rows, once.

  D  THE READERS. alpha/event_rates.py's dealer bucket reads the stored word:
     the word knowable at the decision, "awaiting" before the first capture's
     computed_at and past max_age_days; base_rates' awaiting row still names 6b.
     The coverage reader's rule (the first day any value was knowable, over
     exposure.net_gex for SPY) finds the captures' first session; the VRP
     engine's coverage counts the dealer sessions.

  E  REGISTRATION. Every key is registered (metrics_registry.yaml), the word
     lens-excluded and trigger-ineligible, dealer_capture a registered source
     whose variant reads back as its id, the backfill's line in the catalogue.
     The writer opens no vendor file and names no vendor source.

  F  THE 09:45 BARS (decision 10). QQQ and IWM join the open fetch beside SPY, as
     the tape's own registered bars; a fetch at 09:47 stores each one's completed
     bars to 09:45.

  G  THE AHEAD MATRIX'S STORE PATH (A48's note). with_pricing reads only the
     store it is named: given none, it reads nothing even when the default store
     holds rows; the Ahead matrix passes its path and the Weekly passes the store
     it opened. A gate run never creates data/chester.db.

Synthetic fixtures only: no live store, no network, no model, no real names.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gate_tmp import mkdtemp                                    # noqa: E402

LINE = "=" * 78
PASS = FAIL = 0
TD = Path(mkdtemp("a50-dealer-store-gate-"))
LIVE_DB = REPO / "data" / "chester.db"
LIVE_DB_AT_START = LIVE_DB.exists()
DAY = "2026-10-19"
RUN = {"09:45": "dealer_capture_0945_fixture", "12:30": "dealer_capture_1230_fixture",
       "16:10": "eod_fixture"}


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


def profile(sym: str, slot: str, net: float, ntg: float, day: str = DAY,
            **extra) -> dict:
    """A synthetic computed profile: fetched a minute after the slot, computed two
    minutes after (UTC, EDT)."""
    h, m = (int(x) for x in slot.split(":"))
    f = dt.datetime.fromisoformat(f"{day}T{h + 4:02d}:{m:02d}:00+00:00") \
        + dt.timedelta(minutes=1)
    c = f + dt.timedelta(minutes=1)
    rec = {"symbol": sym, "fetched_at": f.isoformat(), "computed_at": c.isoformat(),
           "session_date": day, "spot": 600.0 + net / 1e9,
           "capture": "settled_eod" if slot == "16:10" else "intraday",
           "gamma_source": "computed", "run_id": RUN[slot],
           "overall": {"net_gex": net, "net_to_gross": ntg, "gamma_flip": 590.0,
                       "call_wall_otm": 610.0, "put_wall_otm": 580.0}}
    rec.update(extra)
    return rec


def write(base: Path, rec: dict, name: str | None = None) -> Path:
    d = base / rec["session_date"]
    d.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.fromisoformat(rec["fetched_at"]).strftime("%H%M%SZ")
    p = d / (name or f"{rec['symbol']}_{stamp}_exposure.json")
    p.write_text(json.dumps(rec), encoding="utf-8")
    return p


def rows(db: Path, where: str = "1=1", args: tuple = ()) -> list[dict]:
    con = sqlite3.connect(str(db))
    con.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in con.execute(
            f"SELECT * FROM observations WHERE {where} ORDER BY registry_key, observed_at",
            args)]
    finally:
        con.close()


# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. THE WRITER")
    from altdata import dealer_store as ds
    base = TD / "computed_a"
    am = write(base, profile("SPY", "09:45", 2e9, 0.30))
    mid = write(base, profile("SPY", "12:30", -1e9, 0.05))
    eod = write(base, profile("SPY", "16:10", -3e9, 0.40))
    vend = write(base, profile("QQQ", "09:45", 1e9, 0.3, gamma_source="vendor"))
    old = write(base, profile("IWM", "09:45", 1e9, 0.3), name="IWM_134600Z_gex.json")
    bn = write(base, profile("BN", "09:45", 1e9, 0.3))
    off = write(base, profile("IWM", "09:45", 1e9, 0.3,
                              fetched_at=f"{DAY}T15:10:00+00:00"))
    db = TD / "a.db"
    dry = ds.store_paths([am, mid, eod], str(db), dry_run=True)
    check(dry["rows"] == 21 and dry["written"] == 0 and not db.exists(),
          f"a dry run counts 21 rows (seven keys x three captures) and writes nothing, "
          f"creating no file ({dry['rows']}, {dry['written']})")
    res = ds.store_paths([am, mid, eod, vend, old, bn, off], str(db))
    f = {k.split("/", 1)[1]: v for k, v in res["files"].items()}
    check(res["written"] == 21 and f[am.name] == f[mid.name] == f[eod.name] == "ok",
          f"three captures, 21 rows written ({res['written']})")
    check(f[vend.name].startswith("vendor-supplied gamma")
          and f[old.name] == "not one of our engine's exposure files"
          and f[bn.name] == "restricted instrument"
          and f[off.name] == "no declared slot within the tolerance",
          f"refused with their reasons: vendor gamma, a *_gex.json, a restricted "
          f"symbol, a capture outside every slot ({[f[p.name] for p in (vend, old, bn, off)]})")
    got = rows(db)
    check({r["registry_key"] for r in got} == set(ds.KEYS) and len(ds.KEYS) == 7
          and {r["instrument"] for r in got} == {"SPY"},
          f"the seven keys, instrument the symbol ({sorted({r['registry_key'] for r in got})})")
    obs = sorted({r["observed_at"] for r in got})
    check(obs == [f"{DAY}T09:45:00-04:00", f"{DAY}T12:30:00-04:00", f"{DAY}T16:10:00-04:00"],
          f"observed_at is the slot's ET instant on the session ({obs})")
    recs = {RUN[s]: json.loads(p.read_text(encoding="utf-8"))
            for s, p in (("09:45", am), ("12:30", mid), ("16:10", eod))}
    from altdata.observations import canonical_instant
    check(all(r["available_at"] == canonical_instant(recs[r["source"].split(":", 1)[1]]
                                                     ["computed_at"]) for r in got)
          and {r["source"] for r in got} == {f"dealer_capture:{v}" for v in RUN.values()}
          and all(r["ingested_at"] != r["available_at"] for r in got),
          "available_at is each file's computed_at, never the write instant; the source "
          "is dealer_capture:<the capture's run id>")
    words = {r["observed_at"][11:16]: r["value_text"] for r in got
             if r["registry_key"] == ds.WORD_KEY}
    check(words == {"09:45": "positive gamma", "12:30": "indeterminate",
                    "16:10": "negative gamma"},
          f"the word is the gate's: positive at 0.30, indeterminate at 0.05 (below "
          f"0.10), negative at 0.40 ({words})")
    from daily_cascade import dealer_block as dbk
    cfg = dbk.config()
    check(ds.regime_word(1.0, 0.10, cfg) == "positive gamma"
          and ds.regime_word(-1.0, 0.0999, cfg) == "indeterminate"
          and ds.regime_word(None, 0.5, cfg) is None
          and float(cfg.get("net_to_gross_min")) == 0.10,
          "at the 0.10 boundary the word passes; just below it is indeterminate; no word "
          "without both inputs (dealer_block.regime, RULED)")
    num = {(r["registry_key"], r["observed_at"][11:16]): r["value_num"] for r in got}
    check(num[("exposure.net_gex", "16:10")] == -3e9
          and num[("exposure.net_to_gross", "12:30")] == 0.05
          and num[("exposure.gamma_flip", "09:45")] == 590.0
          and num[("exposure.call_wall_otm", "09:45")] == 610.0
          and num[("exposure.put_wall_otm", "09:45")] == 580.0
          and num[("exposure.spot", "09:45")] == 602.0,
          "net GEX, net-to-gross, the flip, the OTM walls and the spot, as the profile "
          "carries them")
    again = ds.store_paths([am, mid, eod], str(db))
    check(again["written"] == 0 and len(rows(db)) == 21,
          "a re-store of the same files is a no-op (the store's vintage key)")
    no_id = profile("SPY", "09:45", 1e9, 0.3)
    no_id.pop("run_id")
    p = write(TD / "computed_a2", no_id)
    r2, why = ds.rows_for(no_id, p, cfg)
    check(why is None and r2 and r2[0]["source"] == f"dealer_capture:{p.stem}",
          "without a run id, the capture's id is the file's stem")


def group_b() -> None:
    head("B. WHERE IT RUNS")
    from altdata import dealer_capture as dc, dealer_store as ds
    base = TD / "computed_b"
    p = write(base, profile("SPY", "09:45", 2e9, 0.3))
    saved = dc.compute_written
    try:
        dc.compute_written = lambda summary, syms, out_dir=None, run_id=None: {
            "SPY": str(p)}
        pull = lambda **k: {"success": 1, "total": 1, "symbols": {}}   # noqa: E731
        db = TD / "b.db"
        res = dc.run("0945", symbols=["SPY"], pull=pull, out_dir=str(base),
                     db_path=str(db))
        check(res["stored"].get("written") == 7 and len(rows(db)) == 7
              and res["stored"]["files"] == {f"{DAY}/{p.name}": "ok"},
              f"the 09:45 capture stores its profile after compute ({res['stored']})")
        res2 = dc.run("0945", symbols=["SPY"], pull=pull, out_dir=str(base))
        check(res2["stored"] == {"skipped": "out_dir given without a store path"}
              and LIVE_DB.exists() == LIVE_DB_AT_START,
              "given its own out_dir and no store path, it stores nothing (no default "
              "store opened)")
    finally:
        dc.compute_written = saved
    bad = ds.store_after_compute([str(p)], str(TD))           # a directory, not a db
    check("error" in bad, f"the step never raises: a store that cannot open is an error "
                          f"line ({bad.get('error', '')[:60]})")
    src = (REPO / "run_eod.py").read_text(encoding="utf-8")
    i2, i2b, i3 = (src.find("# ---- Stage 2: compute"), src.find("# ---- Stage 2b"),
                   src.find("# ---- Stage 3: pin log"))
    check(0 < i2 < i2b < i3 and "dealer_store.store_after_compute(" in src[i2b:i3]
          and "return" not in src[i2b:i3],
          "the EOD pass's Stage 2b sits after compute and before the pin log, and "
          "never ends the run")
    csrc = (REPO / "altdata" / "dealer_capture.py").read_text(encoding="utf-8")
    check(csrc.find("compute_written(summary") < csrc.find("store_after_compute("),
          "the capture stores after compute")
    units = " ".join(f.read_text(encoding="utf-8", errors="replace")
                     for f in (REPO / "deploy" / "systemd").glob("*"))
    check("dealer_store" not in units and "dealer-store" not in units,
          "no unit and no timer of its own")


def group_c() -> None:
    head("C. THE BACKFILL")
    from altdata import dealer_store as ds
    base = TD / "computed_c"
    for d in ("2026-10-15", "2026-10-16", DAY):
        write(base, profile("SPY", "16:10", 1e9, 0.3, day=d))
        write(base, profile("QQQ", "09:45", -1e9, 0.2, day=d))
    (base / "notes").mkdir()
    db = TD / "c.db"
    dry = ds.backfill(str(base), str(db), dry_run=True)
    check(dry["dry_run"] and dry["files"] == 6 and dry["stored_files"] == 6
          and dry["rows"] == 42
          and dry["written"] == 0 and not db.exists()
          and dry["first_session"] == "2026-10-15" and dry["last_session"] == DAY,
          f"the dry run counts six files, 42 rows, 15 Oct to 19 Oct, and writes nothing "
          f"({dry})")
    live = ds.backfill(str(base), str(db), dry_run=False)
    check(live["written"] == 42 and ds.backfill(str(base), str(db), dry_run=False)
          ["written"] == 0, "then the rows, once; a second run writes none")
    part = ds.backfill(str(base), str(db), since="2026-10-16", until="2026-10-16")
    check(part["files"] == 2, "--from and --to bound the sessions read")
    src = (REPO / "altdata" / "dealer_store.py").read_text(encoding="utf-8")
    check('add_parser("backfill"' in src and '"--dry-run"' in src,
          "python -m altdata.dealer_store backfill [--dry-run] is the command")


def group_d() -> None:
    head("D. THE READERS")
    from altdata import dealer_store as ds, observations
    from alpha import event_rates as er
    from alpha.engines import vrp
    base = TD / "computed_d"
    files = [write(base, profile("SPY", "16:10", -2e9, 0.3, day="2026-10-15")),
             write(base, profile("SPY", "09:45", 2e9, 0.3, day="2026-10-16")),
             write(base, profile("SPY", "16:10", 1e9, 0.05, day="2026-10-16"))]
    db = TD / "d.db"
    ds.store_paths(files, str(db))
    cfg = er.load_config() if hasattr(er, "load_config") else None
    import yaml
    cfg = cfg or yaml.safe_load((REPO / "config" / "alpha_events.yaml")
                                .read_text(encoding="utf-8"))
    dcfg = cfg["dealer"]
    check(dcfg.get("regime_word") == ds.WORD_KEY and dcfg.get("instrument") == "SPY",
          "the bucket reads exposure.regime_word for SPY, by name")
    with observations.ObservationStore(str(db)) as st:
        w = er.regime_words(st, dcfg["regime_word"], dcfg["instrument"])
        b = lambda c: er.dealer_bucket(w, c, cfg)                       # noqa: E731
        check(b("2026-10-15T20:00:00+00:00") == er.AWAITING
              and b("2026-10-15T23:00:00+00:00") == "negative gamma",
              "awaiting before the first capture's computed_at; the 16:10 word after it")
        check(b("2026-10-16T14:00:00+00:00") == "positive gamma"
              and b("2026-10-16T23:00:00+00:00") == "indeterminate",
              "the newest word knowable at the decision: the 09:45 by mid-morning, the "
              "16:10 after the close")
        check(b("2026-10-22T23:00:00+00:00") == er.AWAITING,
              "awaiting past max_age_days (3)")
        firsts = sorted(max(str(r["observed_at"])[:10], str(r["available_at"])[:10])
                        for r in st.all_vintages("exposure.net_gex", "SPY"))
        check(firsts and firsts[0] == "2026-10-15",
              "the coverage reader's rule over exposure.net_gex for SPY finds the "
              f"captures' first session ({firsts[:1]}): the dealer stays pending in "
              "search-v1, its history's clock started")
        cov = vrp.DealerVRPEngine({}).coverage(st, "2026-10-17T00:00:00+00:00")
        check(cov["per_underlying"]["SPY"]["dealer_sessions"] == 2,
              f"the VRP engine's coverage counts the stored dealer sessions "
              f"({cov['per_underlying']['SPY']})")
    src = (REPO / "alpha" / "event_rates.py").read_text(encoding="utf-8")
    body = src[src.find("def dealer_bucket"):src.find("# The events, measured")]
    check("net_to_gross" not in body and "> 0" not in body,
          "the bucket computes no regime: it reads the stored word")


def group_e() -> None:
    head("E. REGISTRATION")
    from altdata import dealer_store as ds, derived, source_ids
    import yaml
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    mets = reg.get("metrics") or {}
    check(all(k in mets for k in ds.KEYS), f"every key is registered ({len(ds.KEYS)})")
    w = mets.get(ds.WORD_KEY) or {}
    check(w.get("units") == "label" and w.get("trigger_eligible") is False
          and ds.WORD_KEY in (reg.get("lens_excluded") or {})
          and w.get("source") == "dealer_capture",
          "the word: units label, trigger-ineligible, lens-excluded, source dealer_capture")
    check(all(derived.registry_entry(k) for k in ds.KEYS),
          "and each resolves in the store registry (derived.registry_entry)")
    check("dealer_capture" in source_ids.ids()
          and source_ids.canonical("dealer_capture:eod_fixture") == "dealer_capture",
          "dealer_capture is a registered source; its variant reads back as its id")
    cat = yaml.safe_load((REPO / "config" / "catalogue_commands.yaml")
                         .read_text(encoding="utf-8"))
    check("altdata.dealer_store" in json.dumps(cat),
          "the backfill's line in the catalogue's commands")
    src = re.sub(r'"""[\s\S]*?"""', "", (REPO / "altdata" / "dealer_store.py")
                 .read_text(encoding="utf-8"))
    check(not re.search(r"flashalpha|massive|data/vendor|vendor_", src, re.I),
          "the writer opens no vendor file and names no vendor source")
    check(not re.search(r"register|ledger|market_state|composite|place_?order", src, re.I)
          or "register import instruments" in src,
          "and imports only the blocklist from the register: no ledger, no market-state "
          "write, no order path")


def group_f() -> None:
    head("F. THE 09:45 BARS (decision 10)")
    from altdata import bars as bars_mod, note_fetch
    check({"spy", "qqq", "iwm"} <= set(note_fetch.OPEN_IDS),
          f"SPY, QQQ and IWM are in the open fetch ({note_fetch.OPEN_IDS})")
    syms = note_fetch.symbols()
    tape = {t["id"] for t in bars_mod.load_config().get("tape") or []}
    check(syms.get("qqq") == "QQQ" and syms.get("iwm") == "IWM"
          and {"qqq", "iwm"} <= tape and {"bars.qqq", "bars.iwm"} <= set(bars_mod.BAR_PRICE_KEYS),
          "they are the tape's own registered bars (bars.qqq, bars.iwm)")
    now = dt.datetime(2026, 10, 20, 13, 47, tzinfo=dt.timezone.utc)      # 09:47 ET

    def fake(sym, start, end, prepost=False):
        out, t = [], dt.datetime(2026, 10, 20, 13, 30, tzinfo=dt.timezone.utc)
        while t < end:
            out.append({"observed_at": t.isoformat(), "open": 1.0, "high": 1.0,
                        "low": 1.0, "close": 1.0})
            t += dt.timedelta(minutes=5)
        return out
    db = TD / "f.db"
    noop = lambda *a, **k: {"state": "faked"}                  # noqa: E731
    r = note_fetch.open_fetch("2026-10-20", now, str(db), fetcher=fake,
                              steps={"releases": lambda d, p: [], "news": noop,
                                     "voices": noop, "fred": noop})
    con = sqlite3.connect(str(db))
    got = {i: (n, last) for i, n, last in con.execute(
        "SELECT instrument, COUNT(*), MAX(observed_at) FROM bars "
        "WHERE instrument IN ('spy','qqq','iwm') GROUP BY instrument")}
    con.close()
    check(set(got) == {"spy", "qqq", "iwm"}
          and all(v == (3, "2026-10-20T13:40:00+00:00") for v in got.values())
          and r["bars"].get("qqq") == 3,
          f"a fetch at 09:47 stores each one's completed bars to 09:45 (09:30, 09:35, "
          f"09:40; the 09:45 bar is in progress) ({got})")


def group_g() -> None:
    head("G. THE AHEAD MATRIX'S STORE PATH")
    from altdata import observations
    from daily_cascade import ahead, opening_setup as OS
    seeded = TD / "default.db"
    with observations.ObservationStore(str(seeded)) as st:
        st.write_many([{"registry_key": "yfinance.mkt_nvda", "instrument": None,
                        "observed_at": d, "available_at": f"{d}T21:00:00+00:00",
                        "value": v, "source": "yfinance"}
                       for d, v in (("2026-07-01", 100.0), ("2026-07-02", 105.0))])
    saved = observations.DEFAULT_DB
    row = {"symbol": "NVDA", "event": "NVDA earnings", "date": "2026-10-28",
           "consensus": "EPS 1.20 (analyst mean)", "implied_move": "", "cls": "earnings"}
    opened = []
    real = OS._ro                                               # noqa: SLF001
    try:
        observations.DEFAULT_DB = str(seeded)
        OS._ro = lambda p: opened.append(p) or real(p)         # noqa: SLF001
        out = OS.with_pricing(dict(row), "2026-10-17T21:00:00+00:00")
        check("reactions: not stored" in out["consensus"] and not opened,
              "given no store, with_pricing reads nothing, even with the default store "
              "seeded")
        OS.with_pricing(dict(row), "2026-10-17T21:00:00+00:00", str(TD / "named.db"))
        check(opened == [str(TD / "named.db")] and not (TD / "named.db").exists(),
              "given a path it opens that path only, read-only")
        opened.clear()
        saved_er = ahead.earnings_row
        ahead.earnings_row = lambda r, cfg, now, base: dict(r)
        try:
            cal = {"rows": [dict(row)], "window": ["2026-10-26", "2026-10-30"],
                   "routine": []}
            ahead.build(cal, {"week_ending": "2026-10-23"}, {}, "2026-10-23T22:00:00+00:00",
                        db_path=str(TD / "ahead.db"))
            check(opened == [str(TD / "ahead.db")],
                  f"the Ahead matrix passes its store path to with_pricing ({opened})")
        finally:
            ahead.earnings_row = saved_er
    finally:
        observations.DEFAULT_DB = saved
        OS._ro = real                                           # noqa: SLF001
    asrc = (REPO / "daily_cascade" / "ahead.py").read_text(encoding="utf-8")
    wsrc = (REPO / "daily_cascade" / "weekly_stack.py").read_text(encoding="utf-8")
    check("opening_setup.with_pricing(r, now, db_path)" in asrc
          and "pos=pos.get(\"data\"), now=now, db_path=str(st.path))" in wsrc
          and "db_path=db_path)" in wsrc[wsrc.find("ah = ahead.build("):][:400],
          "every caller names its store: the Weekly passes the store it opened")


def main() -> int:
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g):
        try:
            g()
        except Exception as exc:                                # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    head("THE GATE RUN")
    check(LIVE_DB.exists() == LIVE_DB_AT_START,
          f"this gate run created no data/chester.db ({'present before' if LIVE_DB_AT_START else 'absent before and after'})")
    print(f"\n{PASS} passed, {FAIL} failed")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
