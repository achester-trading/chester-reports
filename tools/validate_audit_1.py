"""
Validation gate for AUD-1 (the data and architecture audit of 14 Oct 2026,
ruled 09:27 ET) -- for what fits in no existing gate. No live store, no
network, no box: every check seeds its own temporary store.

  A  THE FRED COMPACTION (4b). A synthetic store with re-stamped FRED and
     derived rows, one real revision and a value that returns after it: the dry
     run counts and deletes nothing; --apply refuses without a backup, refuses a
     backup path that exists, and otherwise makes and checks its own backup
     first; it keeps the first of each run of identical values, never a
     revision, never a key outside its scope; the backup holds every row.
  B  THE INCREMENTAL RECOMPUTE (4d). market_features and surprise start from
     the newest day they have stored less their window, or from the beginning
     on an empty store, unless --from or --full says otherwise.
  C  THE EOD CAPTURE (5b, 5c, 5e). A chain expiry that comes back empty is
     retried; the completeness record fails below 12 of 13 symbols or 90% of
     the listed expiries and counts the vendor symbols apart; the close prints
     the gap and names a missing SPX; Massive without its key prints "Massive
     key not set" and raises nothing.
  D  THE MEME LOGGERS (3a, 3b, 3c). ApeWisdom's all-stocks filter is stored
     whole, every ticker on every page the payload declares; wallstreetbets
     stays the universe. Reg SHO keeps the universe plus every symbol at or above
     the liquidity floor, and fetches exactly the sessions missing from the last
     ten. The registry and the logger's description say so.

    python tools/validate_audit_1.py
"""

from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from altdata import observations  # noqa: E402
import gate_tmp                   # noqa: E402  -- removed at exit

PASS = FAIL = 0
LINE = "=" * 78


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


def _row(key, day, avail, value, inst=None, source="fred"):
    return {"registry_key": key, "instrument": inst, "observed_at": day,
            "available_at": avail, "value": value, "source": source}


def seed_restamped(path: str) -> None:
    """Five vintages of one FRED period: A A A, then a revision B, then A back."""
    rows = []
    t = ["2026-09-01T14:00:00+00:00", "2026-09-02T14:00:00+00:00",
         "2026-09-03T14:00:00+00:00", "2026-09-04T14:00:00+00:00",
         "2026-09-05T14:00:00+00:00"]
    for i, v in enumerate((4.10, 4.10, 4.10, 4.25, 4.10)):
        rows.append(_row("fred.yield_10y", "2026-08-29", t[i], v))
    # three re-stamps of an unchanged older period, and a single-vintage one
    for i in range(3):
        rows.append(_row("fred.yield_10y", "2026-08-28", t[i], 4.05))
    rows.append(_row("fred.ccc_oas", "2026-08-29", t[0], 9.1))
    # the derived keys that inherited the stamps
    for i in range(3):
        rows.append(_row("calc.yoy_cpi", "2026-08-01", t[i], 2.9, source="calc"))
        rows.append(_row("calc.surprise_vs_naive.cpi", "2026-08-01", t[i], 0.12,
                         source="calc"))
    # OUT OF SCOPE: a price re-read and a price-derived feature, left alone
    for i in range(3):
        rows.append(_row("yfinance.mkt_spy", "2026-08-29", t[i], 700.0,
                         source="yfinance"))
        rows.append(_row("calc.breadth_rsp_over_spy", "2026-08-29", t[i], 0.31,
                         source="calc"))
    with observations.ObservationStore(path) as st:
        st.write_many(rows)


def group_a() -> None:
    head("A. THE FRED COMPACTION (AUD-1 4b)")
    from altdata import compact_fred as cf
    td = gate_tmp.mkdtemp("validate_audit_1_")
    db = os.path.join(td, "store.db")
    seed_restamped(db)
    with observations.ObservationStore(db) as st:
        before = st.conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
    lines: list[str] = []
    rc = cf.run(db, apply=False, out=lines.append)
    with observations.ObservationStore(db) as st:
        same = st.conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
    text = "\n".join(lines)
    check(rc == 0 and same == before and "nothing deleted" in text
          and "fred.yield_10y" in text and "calc.yoy_cpi" in text
          and "calc.surprise_vs_naive.cpi" in text,
          f"the dry run prints the rows per key that would go and deletes none "
          f"({before} rows before and after)")
    check(cf.run(db, apply=True, backup=None, out=lines.append) == 2,
          "--apply without --backup is refused")
    exists = os.path.join(td, "old.db")
    Path(exists).write_bytes(b"x")
    check(cf.run(db, apply=True, backup=exists, out=lines.append) == 2,
          "--apply naming a backup that already exists is refused: this run makes it")
    bk = os.path.join(td, "backup", "pre.db")
    lines.clear()
    rc = cf.run(db, apply=True, backup=bk, out=lines.append)
    text = "\n".join(lines)
    check(rc == 0 and "backup ok" in text and text.index("backup ok") < text.index("deleted"),
          "--apply makes and integrity-checks its backup before deleting anything")
    con = sqlite3.connect(bk)
    n_bk = con.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
    con.close()
    check(n_bk == before, f"the backup holds every row ({n_bk} of {before})")
    with observations.ObservationStore(db) as st:
        vs = [v["value_num"] for v in st.vintages("fred.yield_10y", "2026-08-29")]
        old = len(st.vintages("fred.yield_10y", "2026-08-28"))
        der = len(st.vintages("calc.yoy_cpi", "2026-08-01"))
        sur = len(st.vintages("calc.surprise_vs_naive.cpi", "2026-08-01"))
        spy = len(st.vintages("yfinance.mkt_spy", "2026-08-29"))
        brd = len(st.vintages("calc.breadth_rsp_over_spy", "2026-08-29"))
        one = len(st.vintages("fred.ccc_oas", "2026-08-29"))
        late = st.as_of("fred.yield_10y", as_of="2026-09-04T15:00:00+00:00")
    check(vs == [4.10, 4.25, 4.10],
          f"A A A B A keeps the first A, the revision B and the A after it: {vs}")
    check(old == 1 and der == 1 and sur == 1 and one == 1,
          "re-stamped FRED and derived periods keep one vintage each")
    check(spy == 3 and brd == 3,
          "keys outside the scope (prices, price-derived features) are untouched")
    check(late and late[-1]["value_num"] == 4.25,
          "a reader as of the revision's day still reads the revision")
    keys = cf.derived_keys()
    check("calc.yield_curve_2s10s" in keys and "calc.net_liquidity" in keys
          and "calc.breadth_rsp_over_spy" not in keys,
          f"the derived scope is market_features' FRED-derived keys ({len(keys)}), "
          f"not its price-derived ones")


def group_b() -> None:
    head("B. THE INCREMENTAL RECOMPUTE (AUD-1 4d)")
    from altdata import market_features as mf
    from altdata import surprise
    td = gate_tmp.mkdtemp("validate_audit_1_b_")
    db = os.path.join(td, "store.db")
    with observations.ObservationStore(db) as st:
        check(mf.default_first_day(st) is None and surprise.default_first_day(st) is None,
              "an empty store computes everything")
        st.write_many([_row("calc.yoy_cpi", "2026-09-01", "2026-09-02T00:00:00+00:00",
                            2.9, source="calc"),
                       _row("calc.surprise_vs_naive.cpi", "2026-08-01",
                            "2026-08-02T00:00:00+00:00", 0.1, source="calc")])
        check(mf.default_first_day(st) == "2026-05-04"
              and surprise.default_first_day(st) == "2026-04-03",
              f"each starts {mf.RECOMPUTE_WINDOW_DAYS} days before the newest day it "
              f"stored ({mf.default_first_day(st)}, {surprise.default_first_day(st)})")
    for mod in (mf, surprise):
        src = Path(mod.__file__).read_text(encoding="utf-8")
        check("if first_day is None and not full:" in src and "--full" in src,
              f"{mod.__name__}: --from and --full override the default start")


def group_c() -> None:
    print(f"\n{LINE}\nC. THE EOD CAPTURE: RETRIES, COMPLETENESS, MASSIVE (AUD-1 5b, 5c, 5e)\n{LINE}")
    import contextlib
    import io
    import types
    import pandas as pd
    import altdata
    from altdata import chain_completeness as cc
    from altdata.sources import _base, massive_chain, options_chain

    # 5b: one expiry empty on the first try, rows on the second.
    good = pd.DataFrame({"strike": [100.0], "bid": [1.0], "ask": [1.2],
                         "lastPrice": [1.1], "volume": [5], "openInterest": [10],
                         "impliedVolatility": [0.2], "contractSymbol": ["X"]})
    tries = {"n": 0}

    class T:
        options = ("2026-11-20",)
        fast_info = {"last_price": 100.0}

        def option_chain(self, exp):
            tries["n"] += 1
            if tries["n"] == 1:
                return types.SimpleNamespace(calls=pd.DataFrame(), puts=pd.DataFrame())
            return types.SimpleNamespace(calls=good, puts=good)
    orig = (altdata.import_yfinance, _base.time.sleep, options_chain.time.sleep)
    altdata.import_yfinance = lambda: types.SimpleNamespace(Ticker=lambda s: T())
    _base.time.sleep = options_chain.time.sleep = lambda s: None
    try:
        rows, man = options_chain.fetch_symbol("SPY")
    finally:
        altdata.import_yfinance, _base.time.sleep, options_chain.time.sleep = orig
    check(tries["n"] == 2 and len(rows) == 2,
          f"an expiry that comes back empty is retried and captured (5b; "
          f"{tries['n']} tries, {len(rows)} rows)")
    # A night Yahoo serves nothing: retries stop after three dead expiries.
    dead = {"n": 0}

    class Dead:
        options = tuple(f"2026-11-{d:02d}" for d in range(1, 21))
        fast_info = {"last_price": 100.0}

        def option_chain(self, exp):
            dead["n"] += 1
            return types.SimpleNamespace(calls=pd.DataFrame(), puts=pd.DataFrame())
    altdata.import_yfinance = lambda: types.SimpleNamespace(Ticker=lambda s: Dead())
    _base.time.sleep = options_chain.time.sleep = lambda s: None
    try:
        rows, man = options_chain.fetch_symbol("SPY")
    finally:
        altdata.import_yfinance, _base.time.sleep, options_chain.time.sleep = orig
    g = options_chain.RETRY_GIVE_UP_AFTER
    check(dead["n"] == 3 * g + (20 - g) and not rows,
          f"20 empty expiries cost {dead['n']} calls, not 60: three tries for the "
          f"first {g}, then one each -- inside the EOD unit's 30 minutes")
    src = Path(options_chain.__file__).read_text(encoding="utf-8")
    check(src.count("retry_call(") >= 3,
          "the spot history, the expiry list and each chain all retry (5b)")

    # 5c: the completeness floors.
    uni = [f"S{i}" for i in range(13)]

    def summary(n_ok, listed=10, with_rows=10):
        return {"symbols": {s: ({"rows": 50, "expiries_fetched": listed,
                                 "expiries_with_rows": with_rows} if i < n_ok
                                else {"rows": 0}) for i, s in enumerate(uni)}}
    check(cc.completeness(summary(13), uni)["ok"], "13 of 13, every expiry: complete")
    r12 = cc.completeness(summary(12), uni)
    check(r12["ok"] and r12["symbols_missing"] == ["S12"],
          "12 of 13 is the floor and passes, the missing symbol named")
    r11 = cc.completeness(summary(11), uni)
    check(not r11["ok"] and cc.EXIT_INCOMPLETE == 5, "11 of 13 fails, exit 5")
    r89 = cc.completeness(summary(13, 100, 89), uni)
    check(not r89["ok"] and cc.completeness(summary(13, 100, 90), uni)["ok"],
          "89% of the listed expiries fails; 90% passes")
    vs = {"symbols": {"SPCX": {"rows": 7}, "SPX": {"rows": 0}}}
    rv = cc.completeness(summary(13), uni, vs, ["SPX", "SPCX"])
    check(rv["ok"] and rv["vendor"]["missing"] == ["SPX"],
          "the vendor symbols count apart: a missing SPX does not fail the capture")
    lines = cc.gap_lines(rv) + cc.gap_lines(r11)
    check(any("SPX" in ln for ln in lines) and any("S11" in ln for ln in lines),
          "the gap lines name the missing SPX and the missing symbols")
    with tempfile.TemporaryDirectory() as td:
        cc.write_completeness(rv, "2026-10-14", base_dir=td)
        back = cc.read_completeness("2026-10-14", base_dir=td)
        check(back == json_roundtrip(rv)
              and cc.read_completeness("2026-10-13", base_dir=td) is None,
              "the record round-trips beside the day's chains; a day without one reads None")
    psrc = (REPO / "daily_cascade" / "payload.py").read_text(encoding="utf-8")
    check("chain_completeness.read_completeness(resolved)" in psrc
          and "gap_lines(rec)" in psrc,
          "the close's payload reads the day's record into its warnings")
    esrc = (REPO / "run_eod.py").read_text(encoding="utf-8")
    check("--capture-only" in esrc and "return EXIT_INCOMPLETE" in esrc,
          "run_eod.py exits 5 on an incomplete capture")

    # 5e: no key -> a clean skip, said plainly.
    orig_cred = massive_chain.credentials
    massive_chain.credentials = lambda: (None, "https://example.invalid")
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            out = massive_chain.pull(symbols=["SPX", "SPCX"])
    except Exception as exc:                                  # noqa: BLE001
        out = {"raised": repr(exc)}
    finally:
        massive_chain.credentials = orig_cred
    check("Massive key not set" in buf.getvalue() and out.get("key_missing")
          and out.get("success") == 0,
          "no Massive key: prints 'Massive key not set', raises nothing (5e)")
    msrc = Path(massive_chain.__file__).read_text(encoding="utf-8")
    check("retry_call(" in msrc, "Massive's symbols take the same retries (5e)")


def group_d() -> None:
    print(f"\n{LINE}\nD. THE MEME LOGGERS (AUD-1 3a, 3b, 3c)\n{LINE}")
    import datetime as dt
    import json
    from altdata.loggers import borrow

    orig = (borrow._get, borrow.universe)
    borrow.universe = lambda: ["SPY", "AAPL"]
    fetched: list[str] = []

    def ape(url, limit=0):
        fetched.append(url)
        page = int(url.rsplit("/", 1)[1])
        if "all-stocks" in url:
            res = [{"ticker": f"Z{page}{i}", "mentions": 10 + i, "rank": i, "upvotes": 1}
                   for i in range(3)]
            if page == 1:
                res.append({"ticker": "AAPL", "mentions": 99, "rank": 1, "upvotes": 5})
            return json.dumps({"pages": 3, "results": res}).encode()
        return json.dumps({"pages": 9, "results": [
            {"ticker": "SPY", "mentions": 7, "rank": 2, "upvotes": 1},
            {"ticker": "GME", "mentions": 50, "rank": 1, "upvotes": 9}]}).encode()

    try:
        td = gate_tmp.mkdtemp("validate_audit_1_d_")
        with observations.ObservationStore(os.path.join(td, "store.db")) as st:
            borrow._get = ape
            out = borrow.pull_apewisdom(store=st, pause=0)
            insts = set(st.instruments(borrow.MENTIONS_KEY))
            all_pages = sorted(u for u in fetched if "all-stocks" in u)
            check(len(all_pages) == 3 and {"Z10@all-stocks", "Z31@all-stocks",
                                           "AAPL@all-stocks"} <= insts,
                  f"3a: all-stocks is read on every page the payload declares (3) "
                  f"and every ticker is stored, tracked or not ({len(all_pages)} pages)")
            wsb = {i for i in insts if i.endswith("@wallstreetbets")}
            check(wsb == {"SPY@wallstreetbets"}
                  and sum(1 for u in fetched if "wallstreetbets" in u) == borrow.APEWISDOM_PAGES,
                  f"3a: wallstreetbets stays the tracked universe, {borrow.APEWISDOM_PAGES} pages "
                  f"({sorted(wsb)})")
            check(out["state"] == "ok" and dict(out["feeds"]).get("all-stocks") == 10,
                  f"3a: the summary counts the whole feed ({out['feeds']})")

            # 3b: the floor.
            rows = [{"symbol": "SPY", "total_volume": 10.0},
                    {"symbol": "BIG", "total_volume": float(borrow.REGSHO_MIN_TOTAL_VOLUME)},
                    {"symbol": "THIN", "total_volume": borrow.REGSHO_MIN_TOTAL_VOLUME - 1.0},
                    {"symbol": "NONE", "total_volume": None}]
            kept = [r["symbol"] for r in borrow.regsho_keep(rows, {"SPY"})]
            check(kept == ["SPY", "BIG"],
                  f"3b: the universe whatever its volume, plus every symbol at the "
                  f"{borrow.REGSHO_MIN_TOTAL_VOLUME:,}-share floor ({kept})")

            # 3b: the last ten sessions, the missing ones only.
            last = dt.date(2026, 10, 13)
            have = ["2026-10-13", "2026-10-09", "2026-10-02"]
            st.write_many([{"registry_key": borrow.SHORT_VOLUME_TOTAL_KEY,
                            "instrument": "SPY", "observed_at": d,
                            "available_at": f"{d}T23:00:00+00:00", "value": 1.0,
                            "source": "finra", "availability_kind": "ingest_instant"}
                           for d in have])
            missing = borrow.regsho_missing_sessions(st, last)
            check(len(missing) == 7 and not set(have) & set(missing)
                  and missing[0] == "2026-09-30" and "2026-10-12" in missing,
                  f"3b: of the last ten sessions to 13 Oct, the seven not stored "
                  f"({missing})")
            fetched.clear()

            def regsho(url, limit=0):
                fetched.append(url)
                ymd = url.rsplit("CNMSshvol", 1)[1][:8]
                return ("Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market\n"
                        f"{ymd}|SPY|5|0|10|Q\n{ymd}|BIG|600000|0|2000000|Q\n"
                        f"{ymd}|THIN|9|0|99|Q\n").encode()
            borrow._get = regsho
            res = borrow.pull_regsho_missing(store=st, last=last)
            days = sorted(u.rsplit("CNMSshvol", 1)[1][:8] for u in fetched)
            check(days == sorted(m.replace("-", "") for m in missing)
                  and res["state"] == "ok" and res["names"] == 14,
                  f"3b: exactly the missing sessions are fetched, two names each "
                  f"({len(days)} files, {res['names']} names)")
            check(borrow.regsho_missing_sessions(st, last) == [],
                  "3b: a second night finds nothing missing")
            check(set(st.instruments(borrow.SHORT_VOLUME_KEY)) == {"SPY", "BIG"},
                  "3b: a name below the floor and outside the universe is not stored")
    finally:
        borrow._get, borrow.universe = orig

    reg = (REPO / "metrics_registry.yaml").read_text(encoding="utf-8")
    check("at least 1,000,000 shares of FINRA-reported total volume" in reg
          and "every ticker on every page ApeWisdom serves" in reg,
          "3c: the registry describes the new instrument sets")
    check("1,000,000" in borrow.SPEC.description and "all-stocks" in borrow.SPEC.description,
          "3c: the logger's own description says the same")


def json_roundtrip(d: dict) -> dict:
    import json
    return json.loads(json.dumps(d))


def main() -> int:
    print(f"{LINE}\nAUD-1, THE FIXES WITH NO OTHER GATE\n{LINE}")
    for g in (group_a, group_b, group_c, group_d):
        try:
            g()
        except Exception as exc:                              # noqa: BLE001
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
