"""
The Alpha Lab, Tranche 3 part 1 (alpha-lab-3; X-3.6, X-3.1, X-3.2) -- what has
no home in tools/validate_alpha.py. Synthetic stores only: no gate here reads the
live store, fetches or calls a model.

  A  PRE-REGISTRATION BY MANIFEST. The manifest is written before the register;
     the harness refuses a hypothesis whose batch carries none (a fixture without
     one fails), one dated after the run, and one whose manifest file was edited
     after registration; the workbench's `new` writes one.
  B  TELLS AS HYPOTHESES (X-3.6). Every quote in config/alpha_tells.yaml is in its
     cited section; a fixture set of tells registers once, a second import writes
     nothing, a changed tell is a new registration with the old one marked
     superseded; a quote not in its section, an ungraded or undeclared forecast
     source and the move screen are not imported, each with its reason; every
     import hypothesis is needs_code, counted by source in the lab line and the
     Lab report; nothing is tested.
  C  THE EVENT BASE RATES (X-3.1, first half) reproduce a hand figure on a fixture
     of four CPI releases: n, the mean first-session drift, its hit rate, the
     VIX's mean change and its crush rate, the surprise buckets, the ALFRED day
     and the dedupe; a bucket that cannot be read prints "awaiting".
  D  THE ENGINES END TO END (X-3.1, X-3.2) on a fixture store through the
     walk-forward, the cost model and the deflated Sharpe as X-1 built them,
     registered by manifest: events_macro and events_pead run and are graded;
     events_crush is a data gap; crypto_carry refuses below its history window
     (nothing run, nothing counted) and runs once it is met; nothing is promoted.
     The carry hook books the paper book's crypto rows (venue, legs, funding
     accrued) and book.cum_pnl reads them.
  E  NOTHING ELSE WRITTEN. After the importer, the base rates, the engines and a
     full nightly run, the store's sha256 is unchanged and the candidate, packet,
     dial, band, tell and narrative tables diff empty; no SQL in alpha/ writes any
     of them; the 29 names match the price feed's EARNINGS_SYMBOLS.

    python tools/validate_alpha_lab_3.py
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import random
import re
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

_TMP = gate_mkdtemp(prefix="validate_alpha_lab_3_")
os.environ["CHESTER_DB"] = os.path.join(_TMP, "store.sqlite")
os.environ.pop("ALPHA_DB", None)
for _k, _d in (("ALPHA_INBOX", "inbox"), ("ALPHA_OUTBOX", "outbox"),
               ("ALPHA_RESEARCH_DIR", "research"), ("ALPHA_REPORTS_DIR", "reports")):
    os.environ[_k] = os.path.join(_TMP, _d)

import yaml  # noqa: E402

from altdata import observations, session  # noqa: E402

observations.DEFAULT_DB = os.environ["CHESTER_DB"]

from alpha import book, event_rates, lab_line, manifest, pit, report, tells  # noqa: E402
from alpha import hypotheses as hyp  # noqa: E402
from alpha.engines import carry as carry_mod  # noqa: E402
from alpha.engines import events as events_mod  # noqa: E402
from alpha.ledger import Ledger  # noqa: E402
from alpha.loops import nightly  # noqa: E402
from alpha.research import workbench  # noqa: E402
from alpha.store import ReadOnlyStore  # noqa: E402

PASS = FAIL = 0
LINE = "=" * 78
ROSTER = REPO / "alpha" / "research" / "roster-2026-10-17-x3.yaml"


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


def sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def close(a, b, tol=1e-6) -> bool:
    return a is not None and b is not None and abs(a - b) <= tol


def sessions(first: str, last: str) -> list[str]:
    d, d1, out = dt.date.fromisoformat(first), dt.date.fromisoformat(last), []
    while d <= d1:
        if session.is_trading_session(d):
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def at(day: str, hhmm: str = "20:20") -> str:
    return f"{day}T{hhmm}:00+00:00"


def nxt_day(day: str, n: int = 1) -> str:
    return (dt.date.fromisoformat(day) + dt.timedelta(days=n)).isoformat()


def put(rows, key, day, value, avail, instrument=None, kind=None) -> None:
    r = {"registry_key": key, "instrument": instrument, "observed_at": day,
         "available_at": avail, "value": value, "source": "synthetic"}
    if kind:
        r["availability_kind"] = kind
    rows.append(r)


def events_schema(con: sqlite3.Connection) -> None:
    from altdata import events                                  # noqa: PLC0415
    con.executescript(events.SCHEMA)


def add_event(con, type_, observed, avail, title, entity=None, payload=None,
              source="synthetic") -> None:
    cur = con.execute(
        "INSERT INTO events (content_hash, type, observed_at, available_at, ingested_at,"
        " source, title, payload) VALUES (?,?,?,?,?,?,?,?)",
        (f"{type_}-{title}-{observed}", type_, observations.canonical_instant(observed)
         if "T" in observed else observed, observations.canonical_instant(avail),
         observations.canonical_instant(avail), source, title,
         json.dumps(payload) if payload is not None else None))
    if entity:
        con.execute("INSERT INTO event_entities (event_id, entity) VALUES (?,?)",
                    (cur.lastrowid, entity))


def write_store(path: str, rows: list[dict]) -> None:
    st = observations.ObservationStore(path)
    st.write_many(rows)
    st.close()


# ---------------------------------------------------------------------------
# The fixtures
# ---------------------------------------------------------------------------
HAND_EVENTS = {  # day: (first-session o->c %, next-session o->c %, VIX before, VIX on)
    "2024-02-13": (1.0, -1.0, 15.0, 13.0),
    "2024-03-12": (2.0, 0.5, 16.0, 15.0),
    "2024-04-10": (-1.0, 1.5, 14.0, 16.0),
}
ALFRED_DAY = "2024-05-15"


def build_hand(path: str) -> None:
    """Four CPI releases with known moves: three in the events table and one
    from ALFRED's first vintage; a fifth ALFRED vintage on an events-table day
    is deduplicated."""
    days = sessions("2024-01-02", "2024-06-28")
    rows: list[dict] = []
    vix = {d: 15.0 for d in days}
    oc = {d: 0.0 for d in days}
    for d, (f, n, vb, vo) in HAND_EVENTS.items():
        oc[d] = f
        oc[pit.next_session(d)] = n
        vix[pit.prev_session(d)] = vb
        vix[d] = vo
    for d in days:
        put(rows, "yfinance.mkt_spy_open", d, 100.0, at(d))
        put(rows, "yfinance.mkt_spy", d, 100.0 * (1 + oc[d] / 100), at(d))
        put(rows, "yfinance.mkt_vix", d, vix[d], at(d))
    for d, s in zip(HAND_EVENTS, (0.2, 0.1, -0.3)):
        put(rows, "calc.surprise_vs_naive.cpi", d[:8] + "01", s, at(d, "12:30"))
    # ALFRED: the April print first published 15 May (a new event), and March's
    # first published on an events-table day (deduplicated).
    put(rows, "fred.cpi", "2024-04-01", 313.0, at(ALFRED_DAY, "12:30"), kind="observed")
    put(rows, "fred.cpi", "2024-03-01", 312.0, at("2024-04-10", "12:30"), kind="observed")
    write_store(path, rows)
    con = sqlite3.connect(path)
    events_schema(con)
    for d in HAND_EVENTS:
        add_event(con, "release", at(d, "12:30"), at(nxt_day(d, -20), "12:00"),
                  f"CPI {d}", "fred.cpi")
    con.commit()
    con.close()


EARN_NAMES = ["AAPL", "MSFT", "NVDA", "JPM", "XOM", "WMT", "PG", "V", "MA", "HD"]


def build_engine_store(path: str, seed: int = 7) -> dict:
    rng = random.Random(seed)
    rows: list[dict] = []
    days = sessions("2009-01-02", "2024-12-31")
    cpi_days, nfp_days = [], []
    y, m = 2009, 2
    while (y, m) <= (2024, 12):
        d = dt.date(y, m, 12)
        while not session.is_trading_session(d):
            d += dt.timedelta(days=1)
        cpi_days.append(d.isoformat())
        f = dt.date(y, m, 1)
        while f.weekday() != 4 or not session.is_trading_session(f):
            f += dt.timedelta(days=1)
        nfp_days.append(f.isoformat())
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    surprise = {d: rng.choice([-1, 1]) * (0.05 + abs(rng.gauss(0, 0.2))) for d in cpi_days}
    planted = {pit.next_session(d): (0.6 if s > 0 else -0.6) for d, s in surprise.items()}
    px = 100.0
    for d in days:
        o = px * (1 + rng.gauss(0, 0.002))
        r = planted.get(d, 0.0) / 100 + rng.gauss(0, 0.002)
        c = o * (1 + r)
        put(rows, "yfinance.mkt_spy_open", d, o, at(d))
        put(rows, "yfinance.mkt_spy", d, c, at(d))
        put(rows, "yfinance.mkt_vix", d, 15 + rng.gauss(0, 1), at(d))
        px = c
    for d, s in surprise.items():
        put(rows, "calc.surprise_vs_naive.cpi", d[:8] + "01", round(s, 4), at(d, "12:30"))
    for d in days[::5]:
        if d >= "2010-01-01":
            put(rows, "cftc.noncomm_net", d, rng.gauss(0, 1e5), at(d, "19:30"), "SP500")
    for d in days[-60:]:
        put(rows, "exposure.net_gex", d, 1.5e9, at(d, "20:30"), "SPY")
    # earnings: ten names, quarterly, knowable the morning after
    edays = sessions("2012-01-02", "2024-12-31")
    earn = []
    for sym in EARN_NAMES:
        key = f"yfinance.mkt_{sym.lower()}"
        sp = 50.0
        quarters = {edays[i] for i in range(30, len(edays) - 30, 63)}
        drift_left, sign = 0, 0
        for d in edays:
            if d in quarters:
                sign = rng.choice([-1, 1])
                earn.append((sym, d, sign * (1 + abs(rng.gauss(0, 3)))))
                drift_left = 22
            r = rng.gauss(0, 0.01) + (sign * 0.0015 if drift_left else 0.0)
            drift_left = max(0, drift_left - 1)
            sp *= 1 + r
            put(rows, key, d, sp, at(d))
    # crypto: S-3 and the venues, every calendar day, knowable the next morning
    d0, d1 = dt.date(2021, 6, 1), dt.date(2024, 12, 31)
    k = d0
    btc, eth = 35000.0, 2500.0
    while k <= d1:
        ds, av = k.isoformat(), at(nxt_day(k.isoformat()), "01:00")
        block = ((k - d0).days // 182) % 2
        for coin in ("BTC", "ETH"):
            f = (16.0 if block == 0 else 1.0) + rng.gauss(0, 0.5)
            put(rows, "calc.funding_agg", ds, f, av, coin)
            put(rows, "calc.leverage_z", ds, 0.5, av, coin)
            put(rows, "hl.funding", ds, f + 1.0, av, coin)
            put(rows, "fut.funding_okx", ds, f, av, coin)
        btc *= 1 + rng.gauss(0, 0.03)
        eth *= 1 + rng.gauss(0, 0.04)
        put(rows, "yfinance.mkt_btc_usd", ds, btc, at(ds, "23:59"))
        put(rows, "yfinance.mkt_eth_usd", ds, eth, at(ds, "23:59"))
        k += dt.timedelta(days=1)
    # dials (the market-state object) for a few sessions
    for d in days[-5:]:
        put(rows, "market_state", d, json.dumps({"dials": {"macro": {"state": "x"}}}),
            at(d, "21:00"))
    write_store(path, rows)
    con = sqlite3.connect(path)
    events_schema(con)
    for d in nfp_days:
        add_event(con, "release", at(d, "12:30"), at(nxt_day(d, -20), "12:00"),
                  f"Payrolls {d}", "fred.nfp")
    for d in cpi_days:
        add_event(con, "release", at(d, "12:30"), at(nxt_day(d, -20), "12:00"),
                  f"CPI {d}", "fred.cpi")
    for d in [x for x in days if x >= "2023-01-01"][20::31][:16]:
        add_event(con, "scheduled", at(d, "18:00"), at("2022-12-01", "12:00"),
                  f"FOMC statement -- {d}", payload={"kind": "fomc"}, source="claims")
    for sym, d, s in earn:
        add_event(con, "earnings", d, at(d, "23:00"), f"{sym} reported",
                  payload={"symbol": sym, "surprise_pct": round(s, 3)}, source="yfinance")
    from altdata import probability_ledger                      # noqa: PLC0415
    con.executescript(probability_ledger.SCHEMA)
    for i, (src, brier) in enumerate([("monthly_macro", 0.2), ("monthly_macro", None),
                                      ("weekly_stance", None), ("mystery_source", 0.1)]):
        con.execute("INSERT INTO probabilities (probability_id, source, claim, probability,"
                    " emitted_at, horizon_date, resolution_criterion, brier, "
                    "method_version) VALUES (?,?,?,?,?,?,?,?,?)",
                    (f"p{i}", src, f"claim {i}", 0.5, "2026-01-01T00:00:00+00:00",
                     "2026-01-31", "a criterion", brier, "v1"))
    # the tables no lab path may write: narratives, and stand-ins for the
    # candidate, packet, band and tell records
    for t in ("narratives", "book_b_candidates", "decision_packets", "book_a_bands",
              "weekly_tells"):
        con.execute(f"CREATE TABLE IF NOT EXISTS {t} (id INTEGER PRIMARY KEY, body TEXT)")
        con.execute(f"INSERT INTO {t} (body) VALUES ('fixture row')")
    con.commit()
    con.close()
    return {"sessions": len(days), "cpi": len(cpi_days), "earn": len(earn)}


def table_hashes(path: str, tables) -> dict:
    con = sqlite3.connect(f"file:{Path(path).as_posix()}?mode=ro", uri=True)
    out = {}
    for t in tables:
        rows = con.execute(f"SELECT * FROM {t} ORDER BY 1").fetchall()
        out[t] = hashlib.sha256(repr(rows).encode()).hexdigest()
    md = con.execute("SELECT registry_key, observed_at, value_text FROM observations "
                     "WHERE registry_key='market_state' ORDER BY observed_at").fetchall()
    out["dials (market_state)"] = hashlib.sha256(repr(md).encode()).hexdigest()
    con.close()
    return out


# ---------------------------------------------------------------------------
STORE = os.environ["CHESTER_DB"]
HAND = os.path.join(_TMP, "hand.sqlite")


def group_a() -> None:
    head("A. PRE-REGISTRATION BY MANIFEST")
    st = ReadOnlyStore(STORE)
    lg = Ledger(os.path.join(_TMP, "alpha_a.db"))
    try:
        doc = yaml.safe_load(ROSTER.read_text(encoding="utf-8"))
        out = manifest.register(lg, st, doc, as_of="2021-12-01T15:00:00+00:00")
        m = out["manifest"]
        p = Path(m["path"])
        body = json.loads(p.read_text(encoding="utf-8"))
        check(p.is_file() and body["batch_sha256"] == manifest.batch_sha256(doc)
              and body["written_at"] == hyp.instant("2021-12-01T15:00:00+00:00"),
              "the roster's manifest is written first: the batch as registered, its "
              "sha256 and its instant")
        reg = hyp.Register(lg)
        b = reg.batch(doc["batch_id"])
        hs = [reg.get(h) for h in out["registered"].values()]
        check(b["file_sha256"] == m["sha256"] and all(
            h["pre_registered_at"] == m["written_at"] for h in hs) and len(hs) == 5,
              "every hypothesis is pre-registered at the manifest's instant, the batch "
              "row carrying its sha256 (5 of 5)")
        h = hs[0]
        check(manifest.check(lg, h, "2022-01-01T00:00:00+00:00")["kind"] == "manifest_file",
              "the harness's check accepts a manifest dated before the run")
        try:
            manifest.check(lg, h, "2021-11-30T00:00:00+00:00")
            ok = False
        except manifest.NoManifest:
            ok = True
        check(ok, "a run before the manifest's instant is refused")
        # a fixture WITHOUT a manifest: a batch row with no created time and no hash
        bare = {"batch_id": "no-manifest", "source": "operator", "channel": "workbench",
                "schema": hyp.SCHEMA_ID, "hypotheses": []}
        lg._insert("hypothesis_batches", {
            "batch_id": "no-manifest", "schema": hyp.SCHEMA_ID, "source": "operator",
            "channel": "workbench", "pre_registered_at": "2021-12-01T00:00:00+00:00",
            "model_idea_rule": 0, "n_hypotheses": 1, "as_of": "t"})
        hh = dict(doc["hypotheses"][0], local_id="X-1",
                  title="A fixture idea with no manifest at all, for the refusal")
        hh.pop("engine", None)
        hid = reg.register(hh, bare, "2021-12-01T00:00:00+00:00", "t", "registered")
        try:
            workbench.run(lg, st, hid, "2022-01-01T00:00:00+00:00")
            ok, why = False, ""
        except hyp.PreRegistrationViolation as exc:
            ok, why = isinstance(exc, manifest.NoManifest), str(exc)
        check(ok and "carries no manifest" in why,
              "a hypothesis whose batch carries no manifest is refused by the harness "
              "before its first backtest")
        # an edited manifest
        body["batch"]["hypotheses"][0]["title"] = "edited after registration"
        body["batch_sha256"] = "0" * 64
        p.write_text(json.dumps(body), encoding="utf-8")
        try:
            manifest.check(lg, h, "2022-01-01T00:00:00+00:00")
            ok = False
        except manifest.NoManifest as exc:
            ok = "edited" in str(exc)
        check(ok, "a manifest edited after registration is refused")
        # the workbench writes one
        idea = dict(doc["hypotheses"][1], local_id="W-1",
                    title="A workbench idea registered with its own manifest")
        idea.pop("engine", None)
        o2 = workbench.new(lg, st, idea, "operator", as_of="2021-12-02T15:00:00+00:00")
        check(Path(o2["manifest"]["path"]).is_file() and reg.batch(
            o2["batch_id"])["file_sha256"] == o2["manifest"]["sha256"],
              "the workbench's `new` writes the manifest before the register")
    finally:
        st.close()
        lg.close()


def _setups_copy(path: Path, change: bool = False) -> Path:
    doc = yaml.safe_load((REPO / "config" / "setups.yaml").read_text(encoding="utf-8"))
    if change:
        doc["setups"]["b_breakout"]["claimed_edge"] = "a changed claim, for the gate"
    path.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True),
                    encoding="utf-8")
    return path


def group_b() -> None:
    head("B. TELLS AS HYPOTHESES (X-3.6)")
    cfg = tells.load_config()
    bad = []
    for t in tells.collect(cfg, None):
        if t.get("cite"):
            why = tells.verify_quote(t["cite"])
            if why:
                bad.append(f"{t['id']}: {why}")
    for k, v in (cfg.get("forecast_sources") or {}).items():
        why = tells.verify_quote(v["cite"])
        if why:
            bad.append(f"{k}: {why}")
    dsec = tells.section_text(REPO / cfg["doctrine_file"], cfg["doctrine"]["section"]) or ""
    if tells._norm(cfg["doctrine"]["framing_quote"]) not in tells._norm(dsec):
        bad.append("the Doctrine's framing quote")
    check(not bad, "every quote in config/alpha_tells.yaml is word for word in its cited "
          "section of the paper (or the register) as committed" + (f": {bad[:3]}" if bad else ""))
    st = ReadOnlyStore(STORE)
    lp = os.path.join(_TMP, "alpha_b.db")
    lg = Ledger(lp)
    sp = _setups_copy(Path(_TMP) / "setups.yaml")
    try:
        r1 = tells.import_tells(lg, st, "2026-10-18T03:00:00+00:00", setups_path=sp)
        c = tells.counts(lg)
        check(c == {"weekly": 4, "doctrine": 10, "setup": 15, "forecast": 1},
              f"one import registers the fixture set: Weekly 4, Doctrine 10 (the ten "
              f"matrix rows and nothing else, ruling 1 of 18 Oct), setups 15, "
              f"forecasts 1 -- got {c}")
        refused = {x["id"]: x["why"] for x in r1["refused"]}
        check("weekly:move-screen" in refused and "no paper states" in
              refused["weekly:move-screen"],
              "the move screen is not imported: no paper states its mechanism")
        check("forecast:mystery-source" in refused and
              "forecast:weekly-stance" not in [*r1["registered"], *refused],
              "a graded source no paper is declared for is refused; an ungraded one is "
              "not a source yet")
        reg = hyp.Register(lg)
        hs = [h for h in reg.all() if h["source"] == "tell"]
        check(all(h["status"] == "needs_code" and h["channel"] == "importer"
                  and h["title"].endswith("after costs?") for h in hs) and len(hs) == 30,
              "every tell is registered as a question, needs_code, through the importer "
              "-- nothing is tested")
        h0 = next(h for h in hs if h["spec"]["tell"]["id"] == "setup:b_breakout")
        check("Quoted from docs/whitepapers/operating-doctrine-whitepaper.md, section "
              "\"4.2 Book B\"" in h0["mechanism"] and h0["horizon_sessions"] == 30
              and "pivotal point" in h0["mechanism"],
              "a setup's mechanism is quoted from the Doctrine's section, cited, with "
              "its book's horizon (B: 30 sessions)")
        m = manifest.manifest_of(lg, h0)
        check(m and m["kind"] == "manifest_file" and m["instant"] <= h0["pre_registered_at"],
              "the import's manifest is on file, dated at the registration")
        mdoc = json.loads(Path(r1["manifest"]["path"]).read_text(encoding="utf-8"))["batch"]
        check("declared by session B" in str(mdoc.get("notes")) and
              "Book D's 21 sessions" in str(mdoc.get("notes")) and
              "setup:d_forced_flow" in str(mdoc.get("notes")),
              "the manifest states Book D's 21 sessions as session B's declared horizon "
              "(ruling 2 of 18 Oct)")
        n_rows = lg.one("SELECT COUNT(*) AS n FROM hypotheses")["n"]
        n_batches = lg.one("SELECT COUNT(*) AS n FROM hypothesis_batches")["n"]
        r2 = tells.import_tells(lg, st, "2026-10-19T03:00:00+00:00", setups_path=sp)
        check(not r2["registered"] and r2["batch_id"] is None and
              lg.one("SELECT COUNT(*) AS n FROM hypotheses")["n"] == n_rows and
              lg.one("SELECT COUNT(*) AS n FROM hypothesis_batches")["n"] == n_batches,
              "a second import writes nothing: no batch, no manifest, no row")
        _setups_copy(sp, change=True)
        r3 = tells.import_tells(lg, st, "2026-10-20T03:00:00+00:00", setups_path=sp)
        new_id = r3["registered"].get("setup:b_breakout")
        old = reg.get(h0["id"])
        check(list(r3["registered"]) == ["setup:b_breakout"] and old["status"] == "refined"
              and old["superseded_by"] == new_id and "superseded" in old["status_reason"],
              "a changed tell is a new registration; the old one is marked superseded "
              "(status refined, superseded_by set)")
        check(tells.counts(lg)["setup"] == 15, "and the count by source still counts it once")
        bad_cite = {"file": "docs/whitepapers/operating-doctrine-whitepaper.md",
                    "section": "4.2 Book B", "quote": "a sentence the Doctrine never wrote"}
        check(tells.verify_quote(bad_cite) is not None,
              "a quote that is not in its section is refused")
        lg.close()
        line = lab_line.weekly_line("2026-10-20T22:00:00+00:00", lp)
        check(line.startswith(lab_line.NOT_LIVE) and "tells 30 (Weekly 4, Doctrine 10, "
              "setups 15, forecasts 1)" in line,
              f"the Weekly's lab line counts the tells by source: {line!r}")
        lr = Ledger(lp, read_only=True)
        page = report.render(lr, "2026-10", "2026-10-20T22:00:00+00:00")
        lr.close()
        check("## 7. The tells imported as hypotheses" in page and "| setup | 15 |" in page,
              "the monthly Lab report prints the count by source")
        none = Ledger(os.path.join(_TMP, "alpha_empty.db"))
        none.close()
        check(lab_line.weekly_line("2026-10-20T22:00:00+00:00",
                                   os.path.join(_TMP, "alpha_empty.db")) == lab_line.NOT_LIVE,
              "with no tell registered the line is unchanged")
    finally:
        st.close()
        try:
            lg.close()
        except Exception:                                     # noqa: BLE001
            pass


def group_c() -> None:
    head("C. THE EVENT BASE RATES (X-3.1): A HAND FIGURE")
    build_hand(HAND)
    st = ReadOnlyStore(HAND)
    cfg = event_rates.load_config()
    try:
        ev = event_rates.macro_rows(st, cfg, "2024-06-28T23:00:00+00:00")
        cpi = ev["cpi"]
        check([r["day"] for r in cpi] == list(HAND_EVENTS) + [ALFRED_DAY]
              and cpi[-1]["event_source"] == "alfred"
              and cpi[2]["event_source"] == "events",
              "release days: three from the events table, one from ALFRED's first "
              "vintage; an ALFRED vintage on an events-table day is deduplicated")
        rates = event_rates.base_rates(st, cfg, "2024-06-28T23:00:00+00:00")

        def row(ev_, kind, bucket, measure):
            return next((r for r in rates if r["event"] == ev_ and r["bucket_kind"] == kind
                         and r["bucket"] == bucket and r["measure"] == measure), None)
        a = row("cpi", "all", "all", "first_session_drift_pct")
        # by hand: (+1.0 + 2.0 - 1.0 + 0.0) / 4 = +0.50%; 2 of 4 above zero
        check(a and a["n"] == 4 and close(a["mean"], 0.5, 1e-9) and close(a["hit_rate"], 0.5)
              and a["first_day"] == "2024-02-13" and a["last_day"] == ALFRED_DAY,
              "CPI first-session drift: n 4, mean +0.50%, hit rate 50%, window 2024-02-13 "
              "to 2024-05-15 -- the hand figure")
        v = row("cpi", "all", "all", "vix_change_pts")
        # (-2 - 1 + 2 + 0) / 4 = -0.25 points; 2 of 4 fell (a crush)
        check(v and close(v["mean"], -0.25, 1e-9) and close(v["hit_rate"], 0.5),
              "the VIX's change: mean -0.25 points, a crush in 2 of 4")
        nx = row("cpi", "all", "all", "next_session_drift_pct")
        check(nx and close(nx["mean"], (-1.0 + 0.5 + 1.5 + 0.0) / 4, 1e-9),
              "the next session's drift (what the engine trades): mean +0.25%")
        pos = row("cpi", "surprise", "positive, size unknown", "first_session_drift_pct")
        neg = row("cpi", "surprise", "negative, size unknown", "first_session_drift_pct")
        check(pos and pos["n"] == 2 and close(pos["mean"], 1.5, 1e-9) and neg
              and neg["n"] == 1 and close(neg["mean"], -1.0, 1e-9),
              "by the naive surprise's sign: positive n 2 at +1.50%, negative n 1 at "
              "-1.00% (size unknown under 8 prior surprises)")
        aw = row("cpi", "positioning", event_rates.AWAITING, "first_session_drift_pct")
        dl = row("cpi", "dealer", event_rates.AWAITING, "first_session_drift_pct")
        check(aw and aw["n"] == 0 and "CFTC" in aw["note"] and dl and "6b" in dl["note"],
              "positioning and the dealer regime print 'awaiting' with the reason where "
              "the store holds no row")
        im = row("earnings", "implied_vs_realised", event_rates.AWAITING, "reaction_pct")
        check(im and "not stored" in im["note"],
              "earnings' implied move against realised prints 'awaiting': no implied "
              "move is stored")
        lg = Ledger(os.path.join(_TMP, "alpha_c.db"))
        event_rates.write(lg, rates, "2024-06-28T23:00:00+00:00")
        event_rates.write(lg, rates, "2024-06-28T23:30:00+00:00")
        n = lg.one("SELECT COUNT(*) AS n FROM event_base_rates")["n"]
        page = "\n".join(report.tranche_3(lg, "2024-06-30"))
        lg.close()
        check(n == len(rates) and "## 8. The system's own event base rates" in page
              and "| cpi | all | first_session_drift_pct | 4 | 2024-02-13 to 2024-05-15 | "
              "+0.50% | 50% |" in page,
              "written to alpha.db once a day (a re-run replaces it) and printed as rows "
              "of the Lab report with n and the window")
    finally:
        st.close()


def group_d() -> None:
    head("D. THE ENGINES END TO END (X-3.1, X-3.2): NO PROMOTION")
    st = ReadOnlyStore(STORE)
    lp = os.path.join(_TMP, "alpha_d.db")
    lg = Ledger(lp)
    try:
        doc = yaml.safe_load(ROSTER.read_text(encoding="utf-8"))
        out = manifest.register(lg, st, doc, as_of="2021-12-01T15:05:00+00:00")
        ids = out["registered"]
        reg = hyp.Register(lg)
        check(sorted(out["statuses"].values()) == ["registered"] * 5,
              f"the roster registers by manifest, all five ready: {out['statuses']}")
        early = "2022-01-14T23:00:00+00:00"
        v0 = lg.variant_count("carry")
        r = workbench.run(lg, st, ids["E-5"], early)
        check(r["status"] == "insufficient_history" and "insufficient history" in r["reason"]
              and reg.get(ids["E-5"])["status"] == "registered"
              and lg.variant_count("carry") == v0,
              f"below its window the carry engine runs nothing, counts nothing and stays "
              f"registered: {r['reason'][:90]}")
        late = "2025-01-10T23:00:00+00:00"
        r5 = workbench.run(lg, st, ids["E-5"], late)
        m5 = (r5["result"].get("metrics") or {})
        check(r5["status"] in ("passed", "failed") and m5.get("n_signals", 0) > 0
              and m5.get("n_trials", 0) >= 1 and "deflated_sharpe" in m5,
              f"once the window is met it runs through the walk-forward, the costs and "
              f"the deflated Sharpe: {r5['status']}, n {m5.get('n_signals')}, DSR "
              f"{m5.get('deflated_sharpe', 0):.2f}")
        vcfg = yaml.safe_load(carry_mod.CONFIG.read_text(encoding="utf-8"))
        fees = [*vcfg["perp_venues"].values(), vcfg["spot_leg"]]
        check(all(f.get("fee_basis") in ("venue_schedule", "third_party") for f in fees)
              and all("THIRD-PARTY, dated" in f["source"] for f in fees
                      if f["fee_basis"] == "third_party")
              and vcfg["spot_leg"]["taker_bps"] == 60.0,
              "every venue fee states its basis, the venue's schedule or a dated, "
              "labelled third-party figure; Coinbase's 60 bp stands (ruling 3 of 18 Oct)")
        eng5 = carry_mod.CarryEngine()
        rows5 = eng5.refit_rows(st, late)
        on = [x for x in rows5 if x["on"]]
        check(on and all(x["venue"] == "hyperliquid" for x in on),
              "the switch turns ON in the high-funding blocks and holds the venue paying "
              "the most (Hyperliquid, +1 point over OKX in the fixture)")
        cost = eng5.leg_cost("hyperliquid", 40000.0, 2000.0)
        check(cost > (60 + 4.5) / 1e4,
              f"a motion on both legs costs the dated fees (spot 60 bp, Hyperliquid "
              f"4.5 bp) plus the perp class's spread and slippage: {cost * 1e4:.1f} bp")
        r4 = workbench.run(lg, st, ids["E-4a"], late)
        m4 = (r4["result"].get("metrics") or {})
        check(r4["status"] in ("passed", "failed") and m4.get("n_signals", 0) > 0,
              f"events_macro runs end to end on the CPI and payroll fixture: "
              f"{r4['status']}, n {m4.get('n_signals')}, expectancy "
              f"{(m4.get('expectancy') or 0) * 100:+.3f}%, DSR "
              f"{m4.get('deflated_sharpe', 0):.2f}")
        rp = workbench.run(lg, st, ids["E-4c"], late)
        mp = (rp["result"].get("metrics") or {})
        check(rp["status"] in ("passed", "failed") and mp.get("n_signals", 0) > 0,
              f"events_pead runs end to end on the earnings fixture: {rp['status']}, n "
              f"{mp.get('n_signals')}")
        rc = workbench.run(lg, st, ids["E-4d"], late)
        check(rc["status"] == "data_gap" and "volatility" in rc["reason"],
              "events_crush is a data gap: no tradable volatility instrument is stored")
        rf = workbench.run(lg, st, ids["E-4b"], late)
        check(rf["status"] in ("insufficient_history", "failed", "passed"),
              f"events_fomc is run or waits on its short FOMC history: {rf['status']}")
        eng = events_mod.EventEngine({"kind": "macro"})
        rows = eng.refit_rows(st, late)
        from alpha import validate as av                        # noqa: PLC0415
        try:
            av.check_pit(rows)
            pit_ok = True
        except av.PointInTimeViolation:
            pit_ok = False
        check(pit_ok and rows and all(x["day"] > x["decided_day"] for x in rows),
              "every engine row is point in time: knowable at its decision, traded the "
              "session after")
        live = lg.q("SELECT id FROM engines WHERE status='live'")
        promo = lg.one("SELECT COUNT(*) AS n FROM loop_events WHERE kind='promotion'")["n"]
        check(not live and promo == 0,
              "nothing is promoted by a run: promotion is the gate's, through the nightly "
              "loop's promote step")
        # the paper book's crypto rows: the hook the nightly loop calls for a live
        # carry engine, called here directly (no engine is made live by a gate)
        eng5.engine_id = "crypto_carry"
        first_fri = "2023-06-30"           # inside the fixture's high-funding block
        o = eng5.carry(lg, st, at(first_fri, "23:00"), 5000.0)
        check(o["opened"] and {x["venue"] for x in o["opened"]} == {"hyperliquid"},
              f"live, the carry hook opens two-leg rows on the decision day: {o['opened']}")
        eng5.carry(lg, st, at("2023-07-07", "23:00"), 5000.0)
        cb = lg.q("SELECT * FROM carry_book ORDER BY id")
        acc = lg.one("SELECT COUNT(*) AS n, SUM(accrued) AS s FROM carry_accruals")
        check(cb and all(abs(c["spot_qty"] + c["perp_qty"]) < 1e-12 for c in cb)
              and acc["n"] >= 6 and acc["s"] > 0 and cb[0]["funding_accrued"] > 0
              and "basis" in (cb[0]["basis_note"] or ""),
              f"its rows carry the venue, equal and opposite legs, the funding accrued "
              f"day by day ({acc['n']} accruals) and the basis note")
        pnl = book.cum_pnl(lg, "crypto_carry", "2023-07-07")
        check(close(pnl, sum(float(a["accrued"]) for a in lg.q(
            "SELECT accrued FROM carry_accruals WHERE day<='2023-07-07'"))
                    - sum(c["entry_costs"] for c in cb), 1e-6),
              "book.cum_pnl reads them: funding accrued less the entry costs")
    finally:
        st.close()
        lg.close()


def group_e() -> None:
    head("E. NOTHING ELSE WRITTEN")
    tables = ("narratives", "book_b_candidates", "decision_packets", "book_a_bands",
              "weekly_tells", "probabilities", "events")
    before_sha = sha(STORE)
    before = table_hashes(STORE, tables)
    lp = os.path.join(_TMP, "alpha_e.db")
    st = ReadOnlyStore(STORE)
    lg = Ledger(lp)
    try:
        tells.import_tells(lg, st, "2026-10-18T03:05:00+00:00",
                           setups_path=_setups_copy(Path(_TMP) / "setups_e.yaml"))
        event_rates.write(lg, event_rates.base_rates(st, event_rates.load_config(),
                                                     "2025-01-10T23:00:00+00:00"),
                          "2025-01-10T23:00:00+00:00")
        manifest.register(lg, st, yaml.safe_load(ROSTER.read_text(encoding="utf-8")),
                          as_of="2021-12-01T15:10:00+00:00")
    finally:
        st.close()
        lg.close()
    summ = nightly.run("2025-01-10T23:00:00+00:00", STORE, lp)
    check(isinstance(summ, dict) and not summ.get("failures"),
          f"a full nightly run on the fixture completes, no step failing "
          f"(failures: {summ.get('failures') if isinstance(summ, dict) else summ})")
    check(sha(STORE) == before_sha,
          "the store's sha256 is unchanged after the importer, the base rates, the "
          "roster and a nightly run")
    after = table_hashes(STORE, tables)
    check(after == before, "the candidate, packet, dial, band, tell and narrative tables "
          "(and the probability ledger and events) diff empty")
    pat = re.compile(r"(INSERT|UPDATE|DELETE|REPLACE)\b[^\"']{0,60}\b(decision_packets|"
                     r"packet_refusals|narratives|narrative_\w+|probabilities|observations|"
                     r"events|event_entities|candidates?|bands?|dials?|tells?)\b", re.I)
    hits = []
    for p in sorted((REPO / "alpha").rglob("*.py")):
        for i, ln in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if pat.search(ln):
                hits.append(f"{p.name}:{i}")
    check(not hits, "no SQL in alpha/ writes a candidate, packet, dial, band, tell, "
          "narrative or anything of the store" + (f": {hits[:4]}" if hits else ""))
    cfg = event_rates.load_config()
    src = (REPO / "altdata" / "sources" / "yfinance_source.py").read_text(encoding="utf-8")
    m = re.search(r"EARNINGS_SYMBOLS: frozenset\[str\] = frozenset\(\{(.*?)\}\)", src, re.S)
    names = set(re.findall(r'"([A-Z.\-]+)"', m.group(1))) if m else set()
    check(set(cfg["earnings"]["universe"]) == names and len(names) == 29,
          "config/alpha_events.yaml's 29 names are the price feed's EARNINGS_SYMBOLS")


def main() -> int:
    print(f"{LINE}\nLAYER X, THE ALPHA LAB -- TRANCHE 3 PART 1 (SYNTHETIC STORES)\n{LINE}")
    info = build_engine_store(STORE)
    print(f"  fixture store: {info}")
    for g in (group_a, group_b, group_c, group_d, group_e):
        g()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
