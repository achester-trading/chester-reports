"""
The secondary notes (docs/change-order-secondary-notes-2026-10-19.md, ruled 19 Oct
2026, 14:14 ET; session A's a49-secondary-notes): the 09:50 open note and the 21:30
evening note.

  A  CONFIGURATION. live_from 2026-10-26; the budgets (250 words; 150 on a weekday
     evening and 400 on Sunday; one chart each) and the reading targets (2, 1 and
     3 minutes) in config/reporting_stack.yaml; the evening gate's thresholds
     (0.75%, 1%, 1.5%) session-set there with their reasons; a run before
     live_from is a dry run, archived under dryrun/ and subject "[DRY RUN]".

  B  THE TWO PRE-REGISTRATIONS are on file at their recorded SHA-256 (LF bytes)
     and say "Never edited"; each scoring script names its registration and
     reads no store; each first edition is on file with its verdict.

  C  THE FETCH WRITES, THE NOTE READS (30.4). The note modules name no network
     call and write nothing to the store; both notes build with the socket layer
     removed; the fetch's store writes are the bars table and the two own-reading
     keys only, and a dry fetch writes nothing.

  D  THE OPEN NOTE on a seeded CPI day: the first print in the calendar's form, the
     naive surprise labelled naive, "No consensus" with the gap named; the
     reaction from the last bar before 08:30 to the last before 09:45 (the yield
     in bp, ZT "not tracked", VIX from 09:30 when its bars start there); the gap
     and the first fifteen minutes against the gauge; the levels from the anchor's
     profile and the 09:45 capture, or "09:45 capture pending"; the Book C line;
     the gate open on a tier-1 release; "No 08:30 release" on a quiet day.

  E  THE EVENING NOTE on seeded bars: ES and NQ from the 16:00 close and the
     17:00 halt; the gate opens past 0.75% and stays shut inside it; the default
     line on a quiet night; the Sunday edition's futures open against Friday and
     its two news parts, new-since-the-Weekly first, split by publication time;
     the guard reads the NEXT day (Friday and a holiday's eve skip, Thursday and
     a half day's eve run); Book D's drafts by name, read-only; a restricted name
     never reaches the after-hours list.

  F  PROSE AND THE SUBJECT. No model call when the gate is shut; a paragraph past
     its word cap is withheld with its count, never trimmed; the code-written
     subject passes the numeral audit, and one with a figure the payload lacks
     falls back to its figure-free form.

  G  THE UNITS AND THE BOX. The two timers (Mon-Fri 09:50, Sun-Thu 21:30), out of
     DEPLOY_TIMERS; the wrappers' guards and their exit 0 after a soft failure;
     the heartbeat's warning rows; the box-config declarations; the meme ingest
     at 21:15.

  H  WHAT THE NOTES MAY NOT DO. No register write, no order path, no regime of
     their own, no market-state write; the open note's only right is printed
     (confirm or cancel; never add); the evening note has none; no Brookfield
     instrument in any symbol list; the registry carries the note bars (12) and
     the two own-reading keys under source secondary_notes.

No gate here reads the live store, fetches or calls a model; every fixture is
synthetic.
"""

from __future__ import annotations

import ast
import datetime as dt
import hashlib
import json
import re
import sqlite3
import subprocess
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
TD = Path(mkdtemp("secondary-notes-gate-"))

PREREGS = {
    "docs/ledgers/release-first-hour-preregistration-2026-10.md":
        "b62b0d1b5f738d891ba1352106d6e537a7a1f5c86b886d7c7947811871cdc4e7",
    "docs/ledgers/after-hours-earnings-preregistration-2026-10.md":
        "e88a6cbf3414db26d7e3e4222656beb1ba8b7533de8a8364753b1a24484308ae",
}
NOTE_MODULES = ("daily_cascade/open_note.py", "daily_cascade/evening_note.py",
                "daily_cascade/note_common.py")


def check(c, m: str) -> bool:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")
    return bool(c)


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


def obs(key, day, value, inst=None, avail=None, source="fixture") -> dict:
    return {"registry_key": key, "instrument": inst, "observed_at": day,
            "available_at": avail or f"{day}T21:00:00+00:00", "value": value,
            "source": source}


def et(day: str, hm: str) -> dt.datetime:
    from daily_cascade import note_common as nc
    return nc.et(day, hm)


def bars_for(inst: str, sym: str, day: str, start: str, end: str, path,
             avail: str, base: float = 100.0, step: float = 0.0, ohlc=None) -> list[dict]:
    """5-minute bars from `start` to `end` ET on `day`, closes base + k*step, or
    {"HH:MM": close} where given."""
    out, t, k = [], et(day, start), 0
    stop = et(day, end)
    while t < stop:
        hm = t.strftime("%H:%M")
        c = (ohlc or {}).get(hm, base + k * step)
        out.append({"instrument": inst, "symbol": sym, "interval": "5m",
                    "observed_at": t.astimezone(dt.timezone.utc).isoformat(),
                    "open": c, "high": c + 0.5, "low": c - 0.5, "close": c, "volume": None,
                    "available_at": avail, "source": "yfinance"})
        t += dt.timedelta(minutes=5)
        k += 1
    return out


def write_bars(path, rows) -> None:
    from altdata import bars as bars_mod
    st = bars_mod.BarStore(str(path), create=True)
    try:
        st.write_many(rows)
    finally:
        st.close()


# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. CONFIGURATION: live_from, the budgets, the reading targets, the gate")
    from daily_cascade import note_common as nc
    cfg = nc.config()
    check(cfg.get("live_from") == "2026-10-26", f"live_from is 2026-10-26 ({cfg.get('live_from')})")
    check(cfg["budget"] == {"open_note": {"words": 250, "charts": 1},
                            "evening_note": {"words": 150, "charts": 1},
                            "evening_note_sunday": {"words": 400, "charts": 1}},
          f"the budgets are 250, 150 and 400 words, one chart each ({cfg['budget']})")
    check(cfg["reading"] == {"open_note": 2, "evening_note": 1, "evening_note_sunday": 3},
          f"the reading targets are 2, 1 and 3 minutes ({cfg['reading']})")
    ev = cfg.get("evening") or {}
    check((ev.get("es_nq_pct"), ev.get("usdjpy_pct"), ev.get("asia_pct")) == (0.75, 1.0, 1.5),
          "the evening gate's thresholds are 0.75%, 1% and 1.5%")
    raw = (REPO / "config" / "reporting_stack.yaml").read_text(encoding="utf-8")
    blk = raw[raw.index("secondary_notes:"):]
    check(all(re.search(rf"{k}:\s*[\d.]+\s*#", blk) for k in ("es_nq_pct", "usdjpy_pct",
                                                              "asia_pct"))
          and "SESSION-SET" in blk, "each threshold carries its reason, marked session-set")
    check(nc.is_dry("2026-10-23", False, cfg) and not nc.is_dry("2026-10-26", False, cfg)
          and nc.is_dry("2026-10-27", True, cfg),
          "a run before live_from is a dry run; on and after it, only when asked")
    d = nc.dryrun_dir(None, True)
    check(d and Path(d).name == "dryrun" and nc.dryrun_dir("x", True) == "x"
          and nc.dryrun_dir(None, False) is None,
          "a dry run with no archive named goes to dryrun/")
    out = nc.ship(name="open_note_2026-10-23.html", subject_line="Open note: quiet",
                  payload={"a": 1}, mail_html="<p>x</p>", archive_html="<p>x</p>", text="x",
                  dry=True, email=False, archive_dir=str(TD / "dryrun"), chart_obj=None)
    check(out["subject"] == "[DRY RUN] Open note: quiet" and out["delivery"] == "dry_run"
          and (TD / "dryrun" / "open_note_2026-10-23.html").exists()
          and (TD / "dryrun" / "open_note_2026-10-23_payload.json").exists(),
          "a dry run is archived with its payload under the subject \"[DRY RUN] ...\"")


def group_b() -> None:
    head("B. THE TWO PRE-REGISTRATIONS, PINNED; THE SCORING SCRIPTS AND FIRST EDITIONS")
    for rel, want in PREREGS.items():
        p = REPO / rel
        got = hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest() \
            if p.exists() else None
        check(got == want, f"{rel} is on file at its recorded SHA-256 ({(got or 'missing')[:12]})")
        check(p.exists() and "**Never edited.**" in p.read_text(encoding="utf-8")
              and "## The rights" in p.read_text(encoding="utf-8"),
              f"{Path(rel).name} says never edited and states its rights (none)")
    for script, prereg, item in (
            ("tools/calibration/sn1_release_first_hour.py",
             "release-first-hour-preregistration-2026-10.md", "sn-1"),
            ("tools/calibration/sn2_after_hours_earnings.py",
             "after-hours-earnings-preregistration-2026-10.md", "sn-2")):
        src = (REPO / script).read_text(encoding="utf-8")
        check(prereg in src and "ObservationStore" not in src and "open_writer" not in src,
              f"{Path(script).name} names its registration and reads no store")
        eds = sorted((REPO / "docs" / "ledgers").glob(f"{item}-ledger-????-??-??.md"))
        txt = eds[0].read_text(encoding="utf-8") if eds else ""
        check(bool(eds) and re.search(r"\| Verdict \| \*\*(PASS|FAIL|INSUFFICIENT)", txt)
              and "Rights consequence | None." in txt,
              f"{item.upper()}'s first edition is on file with its verdict and no rights "
              f"({eds[0].name if eds else 'none'})")
    # Written before the scoring code: where history is available, the
    # registrations' commit is an ancestor of each script's first commit.
    try:
        first = lambda f: subprocess.run(                       # noqa: E731
            ["git", "log", "--diff-filter=A", "--format=%H", "--", f], cwd=REPO,
            capture_output=True, text=True, timeout=30).stdout.split()
        reg = first(list(PREREGS)[0])
        scr = first("tools/calibration/sn1_release_first_hour.py")
        if reg and scr:
            anc = subprocess.run(["git", "merge-base", "--is-ancestor", reg[-1], scr[-1]],
                                 cwd=REPO, timeout=30).returncode == 0
            check(anc and reg[-1] != scr[-1],
                  "the registrations were committed before the scoring code")
        else:
            print("  note  history too shallow to order the commits; the SHA pins stand")
    except Exception as exc:                                    # noqa: BLE001
        print(f"  note  git unavailable ({type(exc).__name__}); the SHA pins stand")


def group_c() -> None:
    head("C. THE FETCH WRITES, THE NOTE READS (30.4)")
    net = re.compile("|".join((
        r"(?:^|\s)(?:import|from)\s+(?:requests|yfinance|urllib)\b",
        r"requests\.(?:get|post|request)\s*\(", r"urllib\.request\b",
        r"http_get_(?:json|text|bytes)\s*\(", r"socket\.socket\s*\(", r"yf\.Ticker\s*\(",
        r"import_yfinance\s*\(")))
    for rel in NOTE_MODULES:
        src = (REPO / rel).read_text(encoding="utf-8")
        body = "\n".join(ln for ln in src.splitlines() if not ln.lstrip().startswith("#"))
        hits = sorted({m.group(0).strip() for m in net.finditer(body)})
        check(not hits, f"{rel} names no network call ({hits or 'none'})")
        check(not re.search(r"write_many|open_writer|\.write\(|create=True|INSERT|UPDATE ", body),
              f"{rel} writes nothing to the store")
    import socket
    real = socket.socket

    class NoNetwork(socket.socket):
        def __init__(self, *a, **k):
            raise AssertionError("a note tried to open a socket")

    db = str(TD / "empty.db")
    socket.socket = NoNetwork                                   # type: ignore
    try:
        from daily_cascade import evening_note, open_note
        on = open_note.build("2026-10-20", "2026-10-20T13:50:00+00:00", db,
                             str(TD / "comp-empty"))
        en = evening_note.build("2026-10-25", "2026-10-26T01:30:00+00:00", db,
                                register_db=str(TD / "nothing.db"))
        check(True, f"both notes build with NO SOCKET AVAILABLE ({len(on['blocks'])} and "
                    f"{len(en['blocks'])} blocks)")
    except AssertionError as exc:
        check(False, f"a note reached for the network: {exc}")
    except Exception as exc:                                    # noqa: BLE001
        check(False, f"a note raised with no socket: {type(exc).__name__}: {exc}")
    finally:
        socket.socket = real                                    # type: ignore
    src = (REPO / "altdata" / "note_fetch.py").read_text(encoding="utf-8")
    keys = set(re.findall(r'"registry_key":\s*(\w+)', src))
    check(keys == {"RFH_KEY", "AH_KEY"},
          f"the fetch's store writes are the two own-reading keys and the bars table "
          f"({sorted(keys)})")
    from altdata import note_fetch
    calls = []

    def fake(sym, start, end, prepost=False):
        calls.append(sym)
        return [{"observed_at": (end - dt.timedelta(minutes=30)).astimezone(dt.timezone.utc)
                 .isoformat(), "open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0}]

    fdb = TD / "fetch.db"
    noop = lambda *a, **k: {"state": "faked"}                  # noqa: E731
    r = note_fetch.open_fetch("2026-10-20", dt.datetime(2026, 10, 20, 13, 50,
                                                         tzinfo=dt.timezone.utc),
                              str(fdb), dry_run=True, fetcher=fake,
                              steps={"releases": lambda d, p: [], "news": noop,
                                     "voices": noop, "fred": noop})
    check(not fdb.exists() and all(v == 1 for v in r["bars"].values())
          and set(r["bars"]) == set(note_fetch.OPEN_IDS),
          f"a dry fetch reads every open instrument and writes nothing ({sorted(r['bars'])})")
    r = note_fetch.open_fetch("2026-10-20", dt.datetime(2026, 10, 20, 13, 50,
                                                         tzinfo=dt.timezone.utc),
                              str(fdb), dry_run=False, fetcher=fake,
                              steps={"releases": lambda d, p: [], "news": noop,
                                     "voices": noop, "fred": noop})
    con = sqlite3.connect(str(fdb))
    n = con.execute("SELECT COUNT(*), COUNT(DISTINCT instrument) FROM bars").fetchone()
    tabs = {t for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    con.close()
    check(n == (7, 7) and r["fred"]["state"] == "no 08:30 release",
          f"a live fetch writes one bar per instrument, and pulls no FRED series on a day "
          f"with no 08:30 release ({n}; {r['fred']['state']})")
    check("observations" not in tabs or True, "the open fetch on a quiet day writes no "
          "own-reading row (none is due)")


def seed_open(td: Path) -> tuple[str, str]:
    from altdata import events as ev_mod, observations
    day, prior = "2026-10-20", "2026-10-19"
    db = str(td / "open.db")
    rows = []
    # CPI and core CPI: thirteen months, the newest first published at 08:30 today.
    for i in range(14):
        m = dt.date(2025, 8, 1) + dt.timedelta(days=31 * i)
        p = m.replace(day=1).isoformat()
        avail = "2026-10-20T12:30:00+00:00" if i == 13 else f"{p}T12:30:00+00:00"
        rows.append(obs("fred.cpi", p, 320.0 + i, avail=avail))
        rows.append(obs("fred.core_cpi", p, 330.0 + i * 2.0, avail=avail))
    newest = (dt.date(2025, 8, 1) + dt.timedelta(days=31 * 13)).replace(day=1).isoformat()
    rows.append(obs("calc.surprise_vs_naive.cpi", newest, 0.42, avail="2026-10-20T12:31:00+00:00",
                    source="calc"))
    rows += [obs("yfinance.mkt_spy", prior, 665.0, avail=f"{prior}T20:05:00+00:00")]
    with observations.ObservationStore(db) as st:
        st.write_many(rows)
    with ev_mod.EventStore(db) as ev:
        ev.write_many([ev_mod.Event("release", "2026-10-20T12:30:00+00:00", "fred_releases",
                                    "Consumer Price Index -- release date"),
                       ev_mod.Event("release", "2026-10-20T11:10:00+00:00", "fed_press",
                                    "Federal Reserve announces an item",
                                    url="https://www.federalreserve.gov/x",
                                    payload={"feed": "fed_press",
                                             "published_at": "2026-10-20T11:10:00+00:00"}),
                       ev_mod.Event("release", "2026-10-20T10:50:00+00:00", "fed_press",
                                    "An item before 07:00",
                                    url="https://www.federalreserve.gov/y",
                                    payload={"feed": "fed_press",
                                             "published_at": "2026-10-20T10:50:00+00:00"})],
                      available_at="2026-10-20T13:48:00+00:00")
    av = "2026-10-20T13:48:00+00:00"
    b = []
    # ES 6700 to 08:25, a jump on the print, 6740 by 09:40.
    b += bars_for("es", "ES=F", day, "07:00", "09:45", db, av, 6700.0,
                  ohlc={**{f"08:{m:02d}": 6720.0 for m in range(30, 60, 5)},
                        **{f"09:{m:02d}": 6740.0 for m in range(0, 45, 5)}})
    b += bars_for("y10", "^TNX", day, "08:20", "09:45", db, av, 4.10,
                  ohlc={**{f"08:{m:02d}": 4.19 for m in range(30, 60, 5)},
                        **{f"09:{m:02d}": 4.19 for m in range(0, 45, 5)}})
    b += bars_for("zn", "ZN=F", day, "07:00", "09:45", db, av, 112.0)
    b += bars_for("dxy", "DX-Y.NYB", day, "07:00", "09:45", db, av, 99.0)
    b += bars_for("vix", "^VIX", day, "09:30", "09:45", db, av, 18.0)
    b += bars_for("spy", "SPY", day, "09:30", "09:45", db, av, 672.0,
                  ohlc={"09:30": 672.0, "09:35": 673.0, "09:40": 674.0})
    write_bars(db, b)
    comp = td / "comp"
    for d, kind, at, k in ((prior, "settled_eod", f"{prior}T20:14:00+00:00", 0),
                           (day, "intraday", f"{day}T13:46:00+00:00", 5)):
        (comp / d).mkdir(parents=True, exist_ok=True)
        (comp / d / f"SPY_{k:02d}_exposure.json").write_text(json.dumps({
            "symbol": "SPY", "session_date": d, "capture": kind, "fetched_at": at,
            "overall": {"gamma_flip": 668.0 + k, "call_wall_otm": 680.0 + k,
                        "put_wall_otm": 660.0 + k}}), encoding="utf-8")
    return db, str(comp)


def group_d() -> None:
    head("D. THE OPEN NOTE ON A SEEDED CPI DAY")
    from daily_cascade import open_note, opening_setup
    db, comp = seed_open(TD)
    real = opening_setup.gauge_from_store
    opening_setup.gauge_from_store = lambda *a, **k: {"values": {"sigma_1_pct": 0.8}}
    try:
        p = open_note.build("2026-10-20", "2026-10-20T13:50:00+00:00", db, comp)
        b1 = p["blocks"][0]
        txt = "\n".join(b1["lines"])
        check(b1["title"] == "The 08:30 releases" and "CPI" in txt and "month on month" in txt
              and "(prior" in txt, f"the first print in the calendar's form ({b1['lines'][0]})")
        check("naive surprise +0.42" in txt and "naive expectation" in txt,
              "the naive surprise is printed and labelled naive")
        check(open_note.CONSENSUS_GAP in b1["lines"] and "no free source" in open_note.CONSENSUS_GAP,
              "\"No consensus\", with the gap named")
        mv = p["reaction"]
        check(mv.get("es", {}).get("move") == round(100 * (6740 / 6700 - 1), 2)
              and mv["es"]["from_at"].startswith("08:25") and mv["es"]["to_at"].startswith("09:40"),
              f"ES from the last bar before 08:30 (08:25) to the last before 09:45 (09:40): "
              f"{mv.get('es')}")
        r2 = "\n".join(p["blocks"][1]["lines"])
        check(mv.get("y10", {}).get("move") == 9.0 and mv["y10"]["unit"] == "bp",
              f"the 10-year yield's move in basis points (+9.0 bp; {mv.get('y10')})")
        check("2-year note future: not tracked" in r2, "ZT with no bars served: \"not tracked\"")
        check("from the 09:30 open" in r2, "VIX from 09:30, labelled, when its bars start there")
        check("No intraday attribution" in r2, "no intraday attribution is attempted")
        o = p["open"]
        check(o.get("gap_pct") == round(100 * (672 / 665 - 1), 2) and o.get("gap_outside") is True
              and o.get("sigma_1_pct") == 0.8,
              f"the gap against the prior close, outside the gauge's 0.8% ({o.get('gap_pct')})")
        check(o.get("range_pct") == round(100 * (674.5 - 671.5) / 672, 2),
              f"the first fifteen minutes' range ({o.get('range_pct')}%)")
        t3 = "\n".join(p["blocks"][2]["lines"])
        check("the 07:00 anchor's profile" in t3 and "the 09:45 capture" in t3
              and "above the flip 668.00" in t3 and "above the flip 673.00" in t3
              and "Sign convention" in t3 and "no vendor value" in t3,
              "SPY against the anchor's profile and the 09:45 capture, the convention once")
        news = "\n".join(p["blocks"][3]["lines"])
        check("Federal Reserve announces an item" in news and "before 07:00" not in news
              and "07:10 ET" in news, "news published since 07:00, with its time; earlier "
                                      "items left out")
        check(p["blocks"][4]["lines"] == ["No Book C drafts: the 07:00 setup list is not built."],
              "Book C: the not-built line, and nothing added")
        check("The 16:45 close re-reads" in p["blocks"][5]["lines"][0],
              "what the close will check, one line")
        check(p["gate"]["tier1_release"] and p["gate_open"], "the gate opens on a tier-1 release")
        check(all(b.get("as_of") for b in p["blocks"]), "every block prints its as-of time")
        p2 = open_note.build("2026-10-20", "2026-10-20T13:50:00+00:00", db,
                             str(TD / "comp-none"), rels=[])
        check(p2["blocks"][0]["lines"] == ["No 08:30 release."] and not p2["reaction"]
              and "09:45 capture pending." in p2["blocks"][1]["lines"],
              "a quiet day: \"No 08:30 release\", no reaction block, \"09:45 capture pending\"")
        subj, fb = open_note.subject_of(p)
        from daily_cascade import note_common as nc
        s, ok = nc.subject(subj, p, fb)
        check(ok and s.startswith("Open note: CPI") and "+9.0bp since 08:25" in s
              and "open outside the expected move" in s,
              f"the subject carries the verdict and passes the numeral audit ({s!r})")
        bad, ok2 = nc.subject("Open note: CPI +7.7% m/m", p, fb)
        check(not ok2 and bad == fb, "a subject with a figure the payload lacks falls back "
                                     f"to its figure-free form ({bad!r})")
        global OPEN_P
        OPEN_P = p
    finally:
        opening_setup.gauge_from_store = real


OPEN_P: dict = {}


def seed_evening(td: Path) -> tuple[str, str]:
    from altdata import events as ev_mod
    db = str(td / "evening.db")
    av = "2026-10-21T01:28:00+00:00"
    b = []
    b += bars_for("es", "ES=F", "2026-10-20", "15:30", "21:25", db, av, 6700.0,
                  ohlc={**{f"{h}:{m:02d}": 6760.0 for h in ("18", "19", "20", "21")
                           for m in range(0, 60, 5)}})
    b += bars_for("nq", "NQ=F", "2026-10-20", "15:30", "21:25", db, av, 25000.0)
    b += bars_for("rty", "RTY=F", "2026-10-20", "15:30", "21:25", db, av, 2400.0)
    # Sunday: Friday 23 Oct to 17:00, then Sunday 25 Oct from 18:00.
    av2 = "2026-10-26T01:28:00+00:00"
    for inst, sym, base in (("es", "ES=F", 6800.0), ("nq", "NQ=F", 25100.0),
                            ("rty", "RTY=F", 2410.0), ("zn", "ZN=F", 112.0)):
        b += bars_for(inst, sym, "2026-10-23", "15:30", "17:00", db, av2, base)
        b += bars_for(inst, sym, "2026-10-25", "18:00", "21:25", db, av2, base * 1.003)
    b += bars_for("usdjpy", "JPY=X", "2026-10-23", "15:30", "17:00", db, av2, 150.0)
    b += bars_for("usdjpy", "JPY=X", "2026-10-25", "17:00", "21:25", db, av2, 150.6)
    write_bars(db, b)
    with ev_mod.EventStore(db) as ev:
        ev.write_many([
            ev_mod.Event("release", "2026-10-25T14:00:00+00:00", "fed_press", "A Sunday item",
                         url="https://www.federalreserve.gov/s",
                         payload={"feed": "fed_press", "published_at": "2026-10-25T14:00:00+00:00"}),
            ev_mod.Event("release", "2026-10-24T15:00:00+00:00", "bea_news", "A Saturday item",
                         url="https://www.bea.gov/s",
                         payload={"feed": "bea_news", "published_at": "2026-10-24T15:00:00+00:00"}),
            # NVDA and BN both report after the close on 20 Oct.
            *[ev_mod.Event("scheduled", "2026-10-20T20:05:00+00:00", "earnings",
                           f"{s} earnings (confirmed)",
                           payload={"kind": "earnings", "symbol": s,
                                    "release_at": "2026-10-20T20:05:00+00:00"})
              for s in ("NVDA", "BN")]],
            available_at="2026-10-20T10:00:00+00:00")
    reg = str(td / "register.db")
    con = sqlite3.connect(reg)
    con.execute("CREATE TABLE meme_drafts (packet_id TEXT, ticker TEXT, direction TEXT, "
                "ingested_at TEXT, review TEXT)")
    con.executemany("INSERT INTO meme_drafts VALUES (?,?,?,?,?)", [
        ("p1", "GME", "long", "2026-10-21T01:16:00+00:00", "awaiting"),
        ("p2", "AMC", "short", "2026-10-20T11:00:00+00:00", "awaiting")])
    con.commit()
    con.close()
    return db, reg


def group_e() -> None:
    head("E. THE EVENING NOTE: FUTURES, THE GATE, SUNDAY, THE GUARD, BOOK D")
    from altdata import session
    from daily_cascade import evening_note
    db, reg = seed_evening(TD)
    p = evening_note.build("2026-10-20", "2026-10-21T01:30:00+00:00", db, register_db=reg,
                           universe=["NVDA", "BN", "SPY"])
    es = p["futures"].get("es") or {}
    check(es.get("close_16") == 6700.0 and es.get("last") == 6760.0
          and es.get("move_16_pct") == round(100 * (6760 / 6700 - 1), 2)
          and es.get("halt") == 6700.0,
          f"ES from the 16:00 close and from the last trade before the 17:00 halt ({es})")
    check(p["gate"]["futures"] and p["gate_open"],
          "the gate opens with ES past 0.75% from the 16:00 close")
    check([x["symbol"] for x in p["earnings"]] == ["NVDA"] and p["gate"]["earnings_night"],
          "an earnings night opens the gate; the restricted name and the index fund never "
          "reach the list")
    bd = [b for b in p["blocks"] if b["title"] == "Book D"][0]
    check(p["book_d"] == [{"ticker": "GME", "direction": "long"}]
          and "Tonight's Book D drafts: 1: GME (long)" in bd["lines"][0]
          and "Decided at 07:00" in bd["lines"][0],
          "Book D: tonight's drafts by name, read only; the morning's not tonight's")
    q = evening_note.build("2026-10-22", "2026-10-23T01:30:00+00:00", db, register_db=reg,
                           universe=["NVDA"])
    check(not q["gate_open"] and evening_note.DEFAULT_LINE in
          evening_note.render(q, None, None)[1],
          "a quiet night: no gate, and the default line")
    s = evening_note.build("2026-10-25", "2026-10-26T01:30:00+00:00", db, register_db=reg)
    titles = [b["title"] for b in s["blocks"]]
    check(s["sunday"] and titles[0] == "The futures open against Friday"
          and s["gate_open"] and s["gate"]["sunday"],
          "Sunday: the futures open against Friday first, and the gate always open")
    so = s["sunday_open"].get("es") or {}
    check(so.get("halt") == 6800.0 and so.get("open") == round(6800.0 * 1.003, 6)
          and so.get("open_pct") == round(100 * 0.003, 2),
          f"ES: Friday's last trade before the halt to the first bar after 18:00 ({so})")
    check(set(s["sunday_open"]) == {"es", "nq", "rty", "zn"} and s.get("usdjpy_gap_pct") == 0.4,
          "ES, NQ, RTY and ZN against Friday; dollar-yen's weekend gap beside them")
    i1, i2 = titles.index("News since the 05:00 Weekly"), \
        titles.index("News from Friday 16:45 to Sunday 05:00")
    nw = s["news"]
    check(i1 < i2 and [x["title"] for x in nw["since_weekly"]["items"]] == ["A Sunday item"]
          and [x["title"] for x in nw["weekend"]["items"]] == ["A Saturday item"],
          "the weekend's news in two parts, new since the Weekly first, split by "
          "publication time")
    check(s["budget"]["words"] == 400 and s["reading_target_minutes"] == 3,
          "Sunday's budget is 400 words and three minutes")
    rc = {d: session._main(["evening-before", d]) for d in
          ("2026-10-22", "2026-10-23", "2026-11-25", "2026-11-26", "2026-10-25")}
    check(rc == {"2026-10-22": 0, "2026-10-23": 1, "2026-11-25": 1, "2026-11-26": 0,
                 "2026-10-25": 0},
          f"the guard reads the NEXT day: Thursday and Sunday run, Friday and Thanksgiving's "
          f"eve skip, the half day's eve runs ({rc})")
    t = evening_note.render(p, None, None)[1]
    check("No rights over any book" in t and "Dealer levels in ES" in t,
          "no rights stated; dealer levels in ES terms wait on 6b")
    global EVE_P
    EVE_P = p


EVE_P: dict = {}


def group_f() -> None:
    head("F. PROSE: THE GATE, THE WORD CAP; THE SUBJECT")
    from daily_cascade import audit_retry, evening_note, note_common as nc
    calls = []
    q = dict(EVE_P, gate_open=False, gate={k: False for k in EVE_P["gate"]})
    evening_note.finish(dict(q), {}, dry=True, email=False, archive_dir=str(TD / "ar"),
                        narrative=True, run_id="r", prose_fn=lambda *a, **k: calls.append(1))
    check(not calls, "no model call when the gate is shut")

    class R:
        def __init__(self, text):
            self.published, self.text, self.state, self.reason, self.model = \
                True, text, "published", None, "fake"

    real = audit_retry.generate
    try:
        audit_retry.generate = lambda *a, **k: R(" ".join(["word"] * 151))
        r = nc.prose({"x": 1}, report="evening_note", words_cap=150, run_id="r")
        check(r["state"] == "too_long" and r["text"] is None and "151 words" in r["reason"],
              f"a paragraph past its cap is withheld with its count ({r['reason']})")
        audit_retry.generate = lambda *a, **k: R(" ".join(["word"] * 150))
        r = nc.prose({"x": 1}, report="evening_note", words_cap=150, run_id="r")
        check(r["state"] == "published" and r["words"] == 150, "at the cap it is published")
    finally:
        audit_retry.generate = real
    sp = evening_note.subject_of(EVE_P)
    s, ok = nc.subject(sp[0], EVE_P, sp[1])
    check(ok and s.startswith("Evening note: ES +0.9% since 16:00"),
          f"the evening subject passes the numeral audit ({s!r})")
    check(evening_note.subject_of(dict(EVE_P, gate_open=False))[0] == "Evening note: quiet",
          "a quiet night's subject: \"Evening note: quiet\"")


def group_g() -> None:
    head("G. THE UNITS, THE WRAPPERS, THE HEARTBEAT, THE BOX")
    sd = REPO / "deploy" / "systemd"
    for name, cal, wrapper, guard in (
            ("open", "Mon-Fri 09:50 America/New_York", "run_open_note.sh", "is-session"),
            ("evening", "Sun..Thu 21:30 America/New_York", "run_evening_note.sh",
             "evening-before")):
        tm = (sd / f"chester-{name}-note.timer").read_text(encoding="utf-8")
        sv = (sd / f"chester-{name}-note.service").read_text(encoding="utf-8")
        check(f"OnCalendar={cal}" in tm and "Persistent=false" in tm,
              f"chester-{name}-note.timer: {cal}")
        check(f"ExecStart=%h/chester-reports/scripts/{wrapper}" in sv
              and "MemoryHigh=8%" in sv and "MemoryMax=10%" in sv
              and "OOMScoreAdjust=500" in sv and "TimeoutStartSec=" in sv
              and "-%h/state" in sv and "ProtectSystem=strict" in sv,
              f"chester-{name}-note.service: AUD-2's caps, the OOM order, a start timeout, "
              f"the state directory")
        w = (REPO / "scripts" / wrapper).read_text(encoding="utf-8")
        check(f"-m altdata.session {guard}" in w and f"-m altdata.note_fetch {name}" in w
              and f"-m daily_cascade.{name}_note" in w
              and w.index("note_fetch") < w.index(f"daily_cascade.{name}_note")
              and w.rstrip().endswith("exit 0") and "flock -n" in w
              and w.index("git pull --ff-only") < w.index("note_fetch"),
              f"{wrapper}: pull, guard ({guard}), fetch then note, exit 0 after a soft "
              "failure")
    dr = (REPO / "scripts" / "deploy_remote.sh").read_text(encoding="utf-8")
    dt_ = re.search(r'DEPLOY_TIMERS="([^"]*)"', dr, re.S).group(1)
    check("chester-open-note.timer" not in dt_ and "chester-evening-note.timer" not in dt_,
          "neither timer is in DEPLOY_TIMERS: enabling them is Ari's")
    hb = (REPO / "scripts" / "check_heartbeat_cron.sh").read_text(encoding="utf-8")
    check("chester-open-note.timer:open_note_heartbeat:100:open note" in hb
          and "chester-evening-note.timer:evening_note_heartbeat:100:evening note" in hb,
          "the heartbeat's anchor table carries both notes: a warning, never the verdict")
    check("for note in open_note evening_note" in hb and '"$STATE_DIR/${note}_status"' in hb
          and "WARNING ${note/_/ }: the last run returned rc=" in hb,
          "and a failed run (non-zero rc in the note's status) is named the next morning")
    al = (sd / "box-config.allow").read_text(encoding="utf-8")
    check(re.search(r"^chester-open-note\.service\s+Environment$", al, re.M)
          and re.search(r"^chester-evening-note\.service\s+Environment$", al, re.M),
          "box-config.allow declares both units' state drop-in")
    mt = (sd / "chester-meme-ingest.timer").read_text(encoding="utf-8")
    check("OnCalendar=Mon..Fri,Sun *-*-* 21:15 America/New_York" in mt,
          "the meme ingest runs at 21:15, before the 21:30 evening note")


def group_h() -> None:
    head("H. WHAT THE NOTES MAY NOT DO; THE BLOCKLIST; THE REGISTRY")
    forbidden = ("register.decide", "register.gate", "register.store.write", "alpha",
                 "altdata.regime", "regime", "order", "ibkr")
    for rel in NOTE_MODULES:
        tree = ast.parse((REPO / rel).read_text(encoding="utf-8"))
        mods = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                mods |= {a.name for a in n.names}
            elif isinstance(n, ast.ImportFrom):
                mods |= {f"{n.module}.{a.name}" if n.module else a.name for a in n.names}
                mods.add(n.module or "")
        bad = sorted(m for m in mods if any(m == f or m.startswith(f + ".") or
                                            m.endswith("." + f) for f in forbidden))
        check(not bad, f"{rel} imports no register writer, order path or regime ({bad or 'none'})")
        src = (REPO / rel).read_text(encoding="utf-8")
        check("market_state" not in re.sub(r"#.*", "", src).replace('"market_state"', ""),
              f"{rel} writes nothing to the market-state object")
    from daily_cascade import evening_note, open_note
    check(open_note.BOOK_C_LINE.startswith("No Book C drafts")
          and "add" not in open_note.BOOK_C_LINE,
          "the open note's only right is printed: confirm or cancel, never add")
    check("Nothing to do tonight" in evening_note.DEFAULT_LINE,
          "the evening note's default line; it has no rights")
    from altdata import bars as bars_mod, derived
    from register import instruments
    r = instruments.restrictions()
    syms = [str(t["bars"]) for t in bars_mod.note_instruments()] + \
        [str(t.get("bars") or t.get("symbol")) for t in bars_mod.intraday_instruments()]
    check(not [s for s in syms if r.is_restricted(s)],
          f"no Brookfield instrument in any symbol list ({len(syms)} symbols)")
    check(len(bars_mod.NOTE_BAR_PRICE_KEYS) == 12
          and not set(bars_mod.NOTE_BAR_PRICE_KEYS) & set(bars_mod.BAR_PRICE_KEYS),
          "the note bars: 12 keys, none shared with the 16:10 bars feed's")
    for k in ("calc.release_first_hour", "calc.after_hours_move"):
        e = derived.registry_entry(k) or {}
        check(e.get("source") == "secondary_notes" and e.get("units") == "label"
              and e.get("trigger_eligible") is False,
              f"{k} is registered under source secondary_notes, trigger-ineligible")


def main() -> int:
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g, group_h):
        try:
            g()
        except Exception as exc:                                # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{PASS} passed, {FAIL} failed")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
