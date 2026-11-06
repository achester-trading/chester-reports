"""
The audit's leftovers, part 2 (audit-leftovers-2, 17 Oct 2026; the data and
architecture audit of 14 Oct, items 12, 14 and 15). On fixture stores of its own --
no network, no live store, no model:

  A  THE MARKS. `quality record` after a pull: a 10-sigma jump, a split-like
     halving and a cross-source disagreement each become one row in
     data_quality_flags with its reason; the normal fixture writes none; the
     observations are byte-for-byte the values they were (marked, never
     altered); a second record writes nothing; the table refuses UPDATE and
     DELETE; "n outliers" prints for the freshness check and the heartbeat.
  B  THE SETTINGS AND THE WIRING. The sigma and the window are listed per family
     and a family's line is the one a key takes; the check covers every FRED
     block and the closes; the EOD pass and the 06:45 pass record after their
     pulls; the heartbeat carries quality=<n> and never sets a verdict from it.
  C  REGISTERED SOURCE IDS. A store opened through open_writer() refuses a row
     whose source is free text and takes a registered id or <id>:<variant>; a
     store opened for a gate's fixture is not refused; every writer module's
     literal source resolves; every pm.* metric declares both venues.
  D  THE TIER IN THE AS-OF JOIN. Two sources at one as-of: as_of(),
     latest_as_of() and the row cache return the higher tier and say what they
     chose it over; equal tiers keep both; a newer vintage still wins; Kalshi
     and Polymarket rows under their own instruments read as before.
  E  THE ZEC LOGGER. aud-1 already holds back the unfinished UTC day (5d): the
     check is still in the logger, through the price feed's bar-finished rule.

    python tools/validate_outliers.py
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import copy
import datetime as dt
import hashlib
import io
import math
import random
import re
import sqlite3
import sys
from contextlib import redirect_stdout
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gate_tmp import mkdtemp                                    # noqa: E402

from altdata import observations, quality, source_ids          # noqa: E402

PASS = FAIL = 0
LINE = "=" * 78
DAY = "2026-10-14"
TD = Path(mkdtemp("validate_outliers_"))


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


def bdays(end: str, n: int) -> list[str]:
    d, out = dt.date.fromisoformat(end), []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d -= dt.timedelta(days=1)
    return out[::-1]


def walk(seed, n, sd, start, log=True):
    rnd = random.Random(seed)
    v, out = start, []
    for _ in range(n):
        v = v * math.exp(rnd.gauss(0, sd)) if log else v + rnd.gauss(0, sd)
        out.append(round(v, 6))
    return out


def rows(key, days, vals, source="fixture"):
    return [{"registry_key": key, "instrument": None, "observed_at": d,
             "available_at": f"{d}T21:00:00+00:00", "value": v, "source": source}
            for d, v in zip(days, vals)]


def cfg_measured() -> dict:
    """The live config with the two pairs measured (a fixture's tolerance)."""
    c = copy.deepcopy(quality.load_config())
    for p in c["pairs"]["list"]:
        if p["id"] == "tnx_dgs10":
            p["tolerance"] = 0.05                 # 5 bp
        if p["id"] == "vix_vixcls":
            p["tolerance"] = 0.10
    return c


def seed(path: str, *, bad: bool) -> None:
    """260 sessions. With `bad`: SPY jumps 10 sigma, QQQ halves (a split-like
    print), and ^TNX disagrees with DGS10 by 30 bp on the day."""
    days = bdays(DAY, 260)
    spy, qqq = walk(1, 260, 0.01, 500.0), walk(2, 260, 0.012, 400.0)
    y10, vix = walk(3, 260, 0.03, 4.2, log=False), walk(4, 260, 0.04, 18.0)
    if bad:
        ch = [math.log(b / a) for a, b in zip(spy[-62:-2], spy[-61:-1])]
        sd = (sum((c - sum(ch) / len(ch)) ** 2 for c in ch) / (len(ch) - 1)) ** 0.5
        spy[-1] = round(spy[-2] * math.exp(10 * sd), 6)
        qqq[-1] = round(qqq[-2] / 2.0, 6)
    tnx = list(y10)
    if bad:
        tnx[-1] = round(y10[-1] + 0.30, 6)
    st = observations.ObservationStore(path)
    try:
        st.write_many(rows("yfinance.mkt_spy", days, spy))
        st.write_many(rows("yfinance.mkt_qqq", days, qqq))
        st.write_many(rows("fred.yield_10y", days, y10))
        st.write_many(rows("yfinance.mkt_tnx", days, tnx))
        st.write_many(rows("yfinance.mkt_vix", days, vix))
        st.write_many(rows("fred.vix", days, vix))
    finally:
        st.close()


def obs_digest(path: str) -> str:
    c = sqlite3.connect(path)
    try:
        rs = c.execute("SELECT registry_key, observed_at, available_at, value_num, "
                       "source FROM observations ORDER BY 1, 2, 3, 5").fetchall()
    finally:
        c.close()
    return hashlib.sha256(repr(rs).encode()).hexdigest()


def group_a() -> None:
    head("A. THE MARKS: A ROW PER FLAG, NEVER AN EDIT")
    bad, good = str(TD / "bad.db"), str(TD / "good.db")
    seed(bad, bad=True)
    seed(good, bad=False)
    cfg = cfg_measured()
    before = obs_digest(bad)
    r = quality.record(bad, DAY, cfg, now="2026-10-14T21:30:00+00:00")
    keys = {(f["kind"], f.get("key") or f.get("id")) for f in r["flags"]}
    check(("outlier", "yfinance.mkt_spy") in keys,
          "a 10-sigma jump on SPY is marked")
    check(("outlier", "yfinance.mkt_qqq") in keys,
          "a split-like halving on QQQ is marked")
    check(("pair", "tnx_dgs10") in keys,
          "^TNX 30 bp from DGS10 against a 5 bp tolerance is marked")
    check(("outlier", "yfinance.mkt_tnx") in keys,
          "and the same 30 bp print is a 10-sigma move on ^TNX's own history: both marks")
    c = sqlite3.connect(bad)
    try:
        got = c.execute(f"SELECT kind, registry_key, reason FROM {quality.FLAGS_TABLE} "
                        f"WHERE day = ?", (DAY,)).fetchall()
    finally:
        c.close()
    check(r["recorded"] == len(r["flags"]) == len(got) == 4
          and all(x[2].startswith("Data check") for x in got),
          f"each flag is one row with its reason ({len(got)} rows)")
    check(obs_digest(bad) == before,
          "the observations are unchanged: every value stands as stored")
    r2 = quality.record(bad, DAY, cfg, now="2026-10-14T22:00:00+00:00")
    check(r2["recorded"] == 0, "a second record of the day writes nothing new")
    c = sqlite3.connect(bad)
    try:
        for stmt, what in ((f"UPDATE {quality.FLAGS_TABLE} SET reason = 'x'", "UPDATE"),
                           (f"DELETE FROM {quality.FLAGS_TABLE}", "DELETE")):
            try:
                c.execute(stmt)
                refused = False
            except sqlite3.DatabaseError:
                refused = True
            check(refused, f"the flags table refuses {what}")
    finally:
        c.close()
    rg = quality.record(good, DAY, cfg)
    check(rg["flags"] == [] and rg["recorded"] == 0,
          "the normal fixture marks nothing")
    n = quality.outliers_count(bad)
    line = quality.outliers_line(n)
    check(n and n["n"] == 4 and line.startswith("data check: 4 outliers on 2026-10-14"),
          f"the count line: '{line}'")
    check(quality.outliers_line(quality.outliers_count(good)).startswith(
        "data check: 0 outliers"), "a clean day prints 0 outliers")
    check(quality.outliers_count(str(TD / "none.db")) is None
          and "no record yet" in quality.outliers_line(None),
          "no record yet says so")
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = quality.main(["outliers", "--db", bad])
    check(rc == 0 and buf.getvalue().startswith("data check: 4 outliers"),
          "`quality outliers` prints the line and exits 0")
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = quality.main(["record", "--db", bad, "--date", DAY])
    check(rc == 0 and "3 flagged" in buf.getvalue() and "Data check" in buf.getvalue(),
          "`quality record` lists each mark for the run log and exits 0 (3 under the "
          "live config, whose pairs wait for the box's measurement)")


def group_b() -> None:
    head("B. THE SETTINGS AND THE WIRING")
    cfg = quality.load_config()
    fams = (cfg.get("outliers") or {}).get("families") or {}
    from altdata import derived
    check(set(fams) == set(derived.FAMILIES)
          and all("sigma" in v and "window" in v for v in fams.values()),
          f"the sigma and the window are listed for each of the {len(fams)} families")
    c = copy.deepcopy(cfg)
    c["outliers"]["families"]["release"] = {"sigma": 4, "window": 24}
    check(quality.params_for("fred.u3_rate", c) == (4.0, 24)
          and quality.params_for("yfinance.mkt_spy", c) == (6.0, 60),
          "a family's line is the one its keys take (a release at 4 and 24 here; "
          "SPY, a price, at 6 and 60)")
    blocks = set(cfg["outliers"]["blocks"])
    check({"market_closes", "fred_6e", "fred_releases", "fred_macro"} <= blocks,
          "the check covers the closes and every FRED block, 6e and releases included")
    eod = (REPO / "scripts" / "run_eod_cron.sh").read_text(encoding="utf-8")
    ovn = (REPO / "scripts" / "fetch_overnight.sh").read_text(encoding="utf-8")
    check(0 < eod.index("-m altdata.feeds pull") < eod.index("-m altdata.quality record"),
          "the EOD pass records after its price and FRED pull")
    check(0 < ovn.index("-m altdata.feeds pull --early") < ovn.index("-m altdata.quality record"),
          "the 06:45 pass records after its FRED pull")
    hb = (REPO / "scripts" / "check_heartbeat_cron.sh").read_text(encoding="utf-8")
    check("quality=$QUALITY_STATE" in hb and "quality=%s" in hb
          and not re.search(r"if .*QUALITY_STATE", hb),
          "the heartbeat carries quality=<n> in its line and status, never a verdict")
    feeds_src = (REPO / "altdata" / "feeds.py").read_text(encoding="utf-8")
    check("quality.outliers_line(quality.outliers_count(" in feeds_src,
          "the freshness check prints the count")


def group_c() -> None:
    head("C. REGISTERED SOURCE IDS ON EVERY ROW")
    path = str(TD / "src.db")
    st = observations.open_writer("validate_outliers", path)
    row = {"registry_key": "yfinance.mkt_spy", "instrument": None,
           "observed_at": DAY, "available_at": f"{DAY}T21:00:00+00:00", "value": 1.0}
    try:
        try:
            st.write_many([dict(row, source="Yahoo Finance (scraped)")])
            refused = False
        except observations.UnregisteredSource as exc:
            refused = "source_registry.yaml" in str(exc)
        check(refused, "a scheduled writer's free-text source is refused, named")
        n = st.write_many([dict(row, source="yfinance"),
                           dict(row, source="kalshi:backfill",
                                registry_key="pm.probability", instrument="kalshi:X")])
        check(n == 2, "a registered id and <id>:<variant> are written")
        try:
            st.write_many([dict(row, source="ibkr", registry_key="ibkr.auction_x")])
            alias_refused = False
        except observations.UnregisteredSource:
            alias_refused = True
        check(alias_refused, "a declared alias is for reading history, never for a new write")
    finally:
        st.close()
    plain = observations.ObservationStore(str(TD / "plain.db"))
    try:
        check(plain.write_many([dict(row, source="fixture")]) == 1,
              "a gate's own fixture store (not opened as a writer) is not refused")
    finally:
        plain.close()
    lits: dict[str, list[str]] = {}
    files = sorted((REPO / "altdata" / "sources").glob("*.py")) + sorted(
        (REPO / "altdata" / "loggers").glob("*.py"))
    files += [p for p in sorted((REPO / "altdata").glob("*.py"))
              if "open_writer(" in p.read_text(encoding="utf-8")]
    for p in files:
        t = p.read_text(encoding="utf-8")
        found = re.findall(r'"source":\s*"([^"]+)"', t) + re.findall(
            r'^SOURCE\s*=\s*"([^"]+)"', t, re.M)
        # ObservationStore.write(..., source="...") -- the loggers' probe rows.
        for call in re.findall(r"\bdb\.write\((?:[^()]|\([^()]*\))*\)", t, re.S):
            found += re.findall(r'\bsource="([^"]+)"', call)
        for s in found:
            lits.setdefault(s, []).append(p.name)
    off = {s: f for s, f in lits.items() if source_ids.writable(s) is None}
    check(not off, f"every writer's literal source is a registered id "
          f"({len(lits)} strings; off the list: {off or 'none'})")
    import yaml
    m = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))["metrics"]
    # pm.implied is RESERVED, written by nothing (aud-3a pins it Kalshi-only).
    pm = {k: v for k, v in m.items() if k.startswith("pm.") and k != "pm.implied"}
    check(pm and all(set(v.get("sources") or []) == {"kalshi", "polymarket"}
                     for v in pm.values()),
          f"every pm.* metric the venues write declares both ({len(pm)}; pm.implied "
          f"is reserved and written by nothing)")
    pmw = (REPO / "altdata" / "sources" / "prediction_markets.py").read_text(encoding="utf-8")
    check('src = f"{r[\'venue\']}:backfill" if backfill else r["venue"]' in pmw
          and source_ids.writable("polymarket") == "polymarket",
          "Polymarket's rows carry their own registered id, polymarket")


def group_d() -> None:
    head("D. THE SOURCE TIER IN THE AS-OF JOIN")
    path = str(TD / "tier.db")
    st = observations.ObservationStore(path)
    t1, t2 = f"{DAY}T21:00:00+00:00", f"{DAY}T22:00:00+00:00"
    base = {"registry_key": "fred.vix", "instrument": None}
    try:
        st.write_many([
            dict(base, observed_at="2026-10-13", available_at=t1, value=20.0, source="yfinance"),
            dict(base, observed_at="2026-10-13", available_at=t1, value=20.5, source="fred"),
            dict(base, observed_at="2026-10-14", available_at=t1, value=21.0, source="fred"),
            dict(base, observed_at="2026-10-14", available_at=t2, value=21.4, source="yfinance"),
            dict(base, observed_at="2026-10-12", available_at=t1, value=19.0, source="calc"),
            dict(base, observed_at="2026-10-12", available_at=t1, value=19.1, source="derived_state"),
        ])
        rs = st.as_of("fred.vix", as_of="2026-10-15T00:00:00+00:00")
        by = {}
        for r in rs:
            by.setdefault(r["observed_at"], []).append(r)
        d13 = by.get("2026-10-13") or []
        check(len(d13) == 1 and d13[0]["source"] == "fred" and d13[0]["value_num"] == 20.5
              and d13[0].get("tier") == "A0" and d13[0].get("tier_over") == ["yfinance (C)"],
              "two sources at one as-of: FRED (A0) is kept over Yahoo (C), and says so")
        d14 = by.get("2026-10-14") or []
        check(len(d14) == 1 and d14[0]["source"] == "yfinance" and d14[0]["value_num"] == 21.4,
              "a newer vintage still wins: the tier decides only between sources at one instant")
        d12 = by.get("2026-10-12") or []
        check(len(d12) == 2 and not any(r.get("tier_over") for r in d12),
              "equal tiers keep both rows, as the join did before")
        st.write_many([dict(base, observed_at="2026-10-15", available_at=f"2026-10-15T21:00:00+00:00",
                            value=22.0, source=s) for s in ("yfinance", "fred")])
        la = st.latest_as_of("fred.vix", as_of="2026-10-16T00:00:00+00:00")
        check(la and la["source"] == "fred" and la["value_num"] == 22.0,
              "latest_as_of() takes the higher tier at the newest period's instant")
        from altdata import derived
        with derived.row_cache(st) as cache:
            cr = cache.rows("fred.vix", "2026-10-16T00:00:00+00:00")
        check([(r["observed_at"], r["source"]) for r in cr]
              == [(r["observed_at"], r["source"]) for r in st.as_of(
                  "fred.vix", as_of="2026-10-16T00:00:00+00:00")],
              "the row cache answers what the query answers, tier rule included")
        pm = [dict(registry_key="pm.probability", instrument=i, observed_at=DAY,
                   available_at=t1, value=v, source=s)
              for i, v, s in (("kalshi:FED-DEC", 0.61, "kalshi"),
                              ("polymarket:0xfed", 0.58, "polymarket"))]
        st.write_many(pm)
        k = st.as_of("pm.probability", instrument="kalshi:FED-DEC")
        p = st.as_of("pm.probability", instrument="polymarket:0xfed")
        check(len(k) == 1 and k[0]["source"] == "kalshi" and len(p) == 1
              and p[0]["source"] == "polymarket" and not k[0].get("tier_over"),
              "Kalshi and Polymarket rows sit under their own instruments: the tier rule "
              "changes neither read (no Polymarket-under-Kalshi read on this store)")
    finally:
        st.close()
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = observations._main(["as-of", "fred.vix", "--db", path,  # noqa: SLF001
                                 "--as-of", "2026-10-14T23:00:00+00:00"])
    out = buf.getvalue()
    check(rc == 0 and "2026-10-13  20.5  source=fred (A0)  chosen over yfinance (C)" in out,
          "`observations as-of` prints which source it chose, read-only")


def group_e() -> None:
    head("E. THE ZEC LOGGER'S UNFINISHED DAY (aud-1 5d)")
    src = (REPO / "altdata" / "loggers" / "shielded.py").read_text(encoding="utf-8")
    check("drop_incomplete_bars(ZEC_SYMBOL" in src and "AUD-1 5d" in src,
          "the ZEC logger holds back the unfinished UTC bar through the price feed's "
          "bar-finished rule (already fixed by aud-1; nothing changed here)")


def main() -> int:
    print(f"{LINE}\naudit-leftovers-2: marks, source ids, the tier rule\n{LINE}")
    for g in (group_a, group_b, group_c, group_d, group_e):
        try:
            g()
        except Exception as exc:                              # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
