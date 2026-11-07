#!/usr/bin/env python3
"""
Validation gate: item 119's event-vol pricing ledger (signal-triage Batch 22, the
order's 101) with Batch 23 item 124f's tags and the T, T+1, T+2 window (A129,
6 Nov 2026). Fixtures only: a fixture chain, a fixture store, a fixture
calendar; no network, no model, no live store, no vendor.

  A  THE PRE-REGISTRATION. docs/ledgers/event-vol-preregistration-2026-11.md
     hashes (LF bytes) to the SHA-256 this gate and config/event_vol.yaml hold;
     the pass rule is "none stated"; the minimum is 20.
  B  THE STRADDLE on a fixture chain: the T-1 capture at or before 16:35 ET is
     read and a later one never is; Ahead's expiry rule (an 08:30 release takes
     the event date's own expiry, a 14:00 one the next); the at-the-money
     straddle over spot; a name with no capture prints "no chain".
  C  THE VARIANCE SPLIT: a one-session expiry's share is 1; item 57's
     pre-event rate; the two-post-event-expiries method; "not separable" with
     the full move labelled "includes non-event days"; a pre-event expiry that
     settles after the event is never used.
  D  THE T, T+1, T+2 COLUMNS: day T for a before-close, an after-close and a
     non-session event; the three signed returns; the headline (one session,
     two when the time is not stored); "pending" until stored.
  E  THE FLAG AND THE ACCRUING GUARD: below 20 resolved rows "accruing (n=k of
     20)" and no flag; at 20 the flag fires below the median and not above it;
     an earnings row adds only the median and the flag to item 57's implied move.
  F  THE TAG VOCABULARY (124f): the config's two lists are the pre-
     registration's; item 52's ledger rows carry both fields, nullable; a tag
     outside the vocabulary is refused; the seeds are 26 rows (the twenty
     Morningstar days, 27 Feb 2020, the six openers, 5 Nov 2026 once), every
     tag valid, the five earlier openers marked V-106h; seeds never count.
  G  THE LEDGER ROUND TRIP on a fixture store: the EOD step records the row of
     an event whose T-1 is the day, never twice; a later EOD step resolves its
     T, T+1, T+2 as a new vintage; the newest vintage is read back read-only;
     Ahead's annotation reads it. No FlashAlpha import anywhere in the module.

    python tools/validate_item_119.py
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import ast
import datetime as dt
import hashlib
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

TD = Path(gate_mkdtemp("item_119_"))
LINE = "=" * 78
PASS = FAIL = 0
PREREG = REPO / "docs" / "ledgers" / "event-vol-preregistration-2026-11.md"
PREREG_SHA256 = "639d142c2d794c7e0e4552971c6a5de38bd61d4ecb2d5820357a059d33329e70"
# The clock is pinned to the fixture's day (B106): nothing here reads today.
GATE_NOW = "2026-11-11T21:20:00+00:00"
VOCAB_SCHEDULED = ["scheduled", "unscheduled"]
VOCAB_CLASS = ["policy shock", "policy response", "exogenous", "data print",
               "positioning unwind", "earnings", "political"]


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


def pin_clock() -> None:
    from altdata import session                                 # noqa: PLC0415
    session.utc_now = lambda: dt.datetime.fromisoformat(GATE_NOW)


# ---------------------------------------------------------------------------
# The fixture chain: SPY on Wed 11 Nov 2026, spot 500
# ---------------------------------------------------------------------------
CHAINS = TD / "chains"
COLS = ["symbol", "fetched_at", "spot", "expiry", "dte", "right", "strike", "bid",
        "ask", "last_price", "volume", "open_interest"]
# expiry -> at-the-money straddle (call and put mids each half of it)
STRADDLES = {"2026-11-12": 6.0, "2026-11-13": 8.0, "2026-11-16": 10.0}


def write_capture(day: str, stamp: str, fetched: str, scale: float = 1.0,
                  symbol: str = "SPY") -> None:
    d = CHAINS / day
    d.mkdir(parents=True, exist_ok=True)
    lines = [",".join(COLS)]
    for ex, s in STRADDLES.items():
        half = s * scale / 2
        dte = (dt.date.fromisoformat(ex) - dt.date.fromisoformat(day)).days
        for k in (495.0, 500.0, 505.0):
            for right in ("C", "P"):
                mid = half + (abs(k - 500.0) * 0.5 if (right == "C") == (k < 500)
                              else -abs(k - 500.0) * 0.1)
                lines.append(",".join(str(x) for x in (
                    symbol, fetched, 500.0, ex, dte, right, k, round(mid - 0.05, 4),
                    round(mid + 0.05, 4), mid, 10, 100)))
    (d / f"{symbol}_{stamp}.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")


def group_a(ev) -> None:
    head("A. THE PRE-REGISTRATION: ITS HASH, HELD TWICE; NONE STATED; 20")
    sha = hashlib.sha256(PREREG.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    cfg = ev.config()
    check(sha == PREREG_SHA256, f"the pre-registration hashes to the gate's SHA-256 ({sha[:12]})")
    check(cfg.get("preregistration_sha256") == PREREG_SHA256
          and cfg.get("preregistration") == PREREG.relative_to(REPO).as_posix(),
          "config/event_vol.yaml holds the same hash and names the file")
    check(ev.PASS_RULE.startswith("none stated"),
          "the pass rule is 'none stated', as the order states none")
    check(int(cfg.get("min_events")) == 20, "log-only until 20 events of a type")
    text = PREREG.read_text(encoding="utf-8")
    check("**None stated.**" in text and "T, T+1 and T+2" in text,
          "the file registers no pass rule and the T, T+1, T+2 window")


def group_b(ev) -> None:
    head("B. THE STRADDLE ON A FIXTURE CHAIN")
    write_capture("2026-11-11", "211000Z", "2026-11-11T21:10:00+00:00")
    write_capture("2026-11-11", "233000Z", "2026-11-11T23:30:00+00:00", scale=3.0)
    p = ev.capture_before("2026-11-11", "SPY", CHAINS)
    check(p is not None and p.name == "SPY_211000Z.csv",
          "the T-1 capture at or before 16:35 ET is read; the 18:30 one never is")
    imp = ev.implied_move("SPY", "2026-11-12", "before", "2026-11-11", CHAINS, "08:30")
    check(imp.get("expiry") == "2026-11-12" and abs(imp["full_pct"] - 1.2) < 1e-9,
          f"an 08:30 release takes the event date's own expiry: straddle 6.0 on 500 "
          f"= 1.2% ({imp.get('expiry')}, {imp.get('full_pct')})")
    imp2 = ev.implied_move("SPY", "2026-11-12", "before", "2026-11-11", CHAINS, "14:00")
    check(imp2.get("expiry") == "2026-11-13",
          "a 14:00 statement takes the first expiry after the date")
    check(ev.implied_move("NVDA", "2026-11-12", "unknown", "2026-11-11", CHAINS)
          == {"reason": ev.NO_CHAIN}, "a name with no capture prints 'no chain'")
    check(ev.capture_before("2026-11-10", "SPY", CHAINS) is None,
          "no capture on the session: nothing read")


def group_c(ev) -> None:
    head("C. THE EVENT DAY'S SHARE OF VARIANCE")
    imp = ev.implied_move("SPY", "2026-11-12", "before", "2026-11-11", CHAINS, "08:30")
    check(imp.get("sessions_covered") == 1 and imp.get("share") == 1.0
          and imp.get("event_pct") == imp.get("full_pct"),
          "a one-session expiry: share 1, the event move is the full move")
    s = ev.split(0.02, 4, pre=(0.01, 2))
    check(s["share"] is not None and abs(s["share"] - 0.5) < 1e-9
          and "item 57" in s["method"],
          f"item 57's pre-event rate: V1 less the pre rate over t1 (share {s['share']})")
    imp2 = ev.implied_move("SPY", "2026-11-12", "before", "2026-11-11", CHAINS, "14:00")
    # V = (f/K)^2; t1 = 2 days, t2 = 5; f1 = 8/500, f2 = 10/500: share =
    # 1 - (V2/V1 - 1) x t1 / (t2 - t1) = 1 - 0.5625 x 2/3 = 0.625.
    check(imp2.get("sessions_covered") == 2 and imp2.get("share") is not None
          and abs(imp2["share"] - 0.625) < 1e-4
          and abs(imp2["event_pct"] - 1.6 * math.sqrt(0.625)) < 1e-3
          and "two post-event expiries" in imp2["method"],
          f"a 14:00 event: the 12 Nov expiry settles after it, so the two post-event "
          f"expiries give the share ({imp2.get('share')}, {imp2.get('event_pct')})")
    bad = ev.split(0.01, 4, pre=(0.01, 2))
    check(bad["share"] is None and bad["method"].startswith(ev.NOT_SEPARABLE),
          "a non-positive event variance is 'not separable'")
    rows = [r for r in __import__("altdata.chain_metrics", fromlist=["x"]).load_rows(
        CHAINS / "2026-11-11" / "SPY_211000Z.csv") if r["expiry"] != "2026-11-16"]
    one = ev.implied_from_rows(rows, "2026-11-12", "before", "2026-11-11", "14:00")
    check(one.get("share") is None and one.get("event_pct") is None
          and one.get("label") == "includes non-event days",
          "no second expiry: the full move kept, labelled 'includes non-event days'")


def group_d(ev) -> None:
    head("D. DAY T AND THE T, T+1, T+2 COLUMNS")
    check(ev.day_t("2026-11-12", "before") == ("2026-11-12", "2026-11-11")
          and ev.day_t("2026-11-03", "after") == ("2026-11-04", "2026-11-03")
          and ev.day_t("2026-11-26", "before") == ("2026-11-27", "2026-11-25"),
          "T: the event's date before the close; the next session after it; the "
          "next session for an event on a holiday (Thanksgiving)")
    closes = [("2026-11-11", 100.0), ("2026-11-12", 102.0), ("2026-11-13", 101.0),
              ("2026-11-16", 103.02)]
    r = ev.realised(closes, "2026-11-12", "before")
    check(r["t"] == 2.0 and abs(r["t1"] + 0.98) < 1e-3 and abs(r["t2"] - 2.0) < 1e-3
          and r["headline"] == 2.0 and r["resolved"],
          f"T, T+1, T+2 signed and the one-session headline ({r})")
    u = ev.realised(closes, "2026-11-12", "unknown")
    check(u["headline"] == 1.0, "an event of unknown time: the headline spans T and T+1")
    p = ev.realised(closes[:3], "2026-11-12", "before")
    check(p["t2"] is None and not p["resolved"] and p["t1"] is not None,
          "T+2 not stored: pending, unresolved")


def group_e(ev) -> None:
    head("E. THE FLAG AND THE ACCRUING GUARD")
    imp = {"event_pct": 1.5, "full_pct": 1.5, "expiry": "2026-11-12", "share": 1.0}
    t, f = ev.clause("cpi", imp, {"cpi": (2.0, 19)})
    check(not f and "accruing (n=19 of 20)" in t and "implied ±1.5%" in t,
          f"below 20: accruing, no flag ({t})")
    t, f = ev.clause("cpi", imp, {"cpi": (2.0, 20)})
    check(f and ev.CHEAP in t and "±2.0% (n=20)" in t,
          f"at 20, implied below the median: cheap event vol ({t})")
    t, f = ev.clause("cpi", {**imp, "event_pct": 2.5}, {"cpi": (2.0, 25)})
    check(not f and ev.CHEAP not in t, "implied above the median: no flag")
    t, f = ev.clause("cpi", {"full_pct": 1.0, "expiry": "x", "share": None,
                             "event_pct": None}, {"cpi": (2.0, 25)})
    check(not f and "includes non-event days" in t,
          "an inseparable implied move is printed and never compared")
    t, f = ev.clause("earnings:NVDA", None, {}, with_implied=False)
    check(t == "median realised for its type: accruing (n=0 of 20)" and not f,
          "an earnings row adds only the median to item 57's implied move")
    t, f = ev.clause("cpi", {"reason": ev.NO_CHAIN}, {})
    check("no chain" in t and not f, "no chain: printed as such, no flag")


def group_f(ev) -> None:
    head("F. THE TAG VOCABULARY AND THE SEED ROWS (124f)")
    from altdata import vol_event as ve                         # noqa: PLC0415
    cfg = ev.config()
    check(cfg["tags"]["scheduled"] == VOCAB_SCHEDULED
          and cfg["tags"]["catalyst_class"] == VOCAB_CLASS,
          "the config's two lists are the pre-registration's, in its order")
    text = PREREG.read_text(encoding="utf-8")
    check(all(f"`{c}`" in text for c in VOCAB_CLASS + VOCAB_SCHEDULED),
          "every class is named in the pre-registration")
    fake = {"day": "2026-10-16", "trigger": {"direction": "up", "arms": {},
                                             "level": {"value": 20.0}},
            "lenses": {k: {"line": "x"} for k in ve.LENS_ORDER}}
    body = json.loads(ve.ledger_row(fake, GATE_NOW, None)["value"])
    check("scheduled" in body and "catalyst_class" in body
          and body["scheduled"] is None and body["catalyst_class"] is None,
          "item 52's ledger rows carry both fields, NULL until set")
    check(ve.tag_faults({"scheduled": None, "catalyst_class": None}) == []
          and ve.tag_faults({"catalyst_class": "sentiment"}) != []
          and ve.tag_faults({"scheduled": "maybe"}) != [],
          "NULL is allowed; a tag outside the vocabulary is refused")
    seeds = cfg["seeds"]
    days = [s["day"] for s in seeds]
    ms = [s for s in seeds if {"morningstar_worst", "morningstar_best"} & set(s["sets"])]
    worst = [s for s in seeds if "morningstar_worst" in s["sets"]]
    op = [s for s in seeds if "opener" in s["sets"]]
    check(len(seeds) == 26 and len(set(days)) == 26 and len(ms) == 20
          and len(worst) == 10 and len(op) == 6 and "2020-02-27" in days,
          f"26 seed rows: the twenty Morningstar days (ten worst), 27 Feb 2020, the "
          f"six openers, 5 Nov 2026 once ({len(seeds)}, {len(ms)}, {len(op)})")
    check(all(not ve.tag_faults(s) for s in seeds),
          "every seed's tags are in the vocabulary")
    early = [s for s in op if s["day"] != "2026-11-05"]
    check(len(early) == 5 and all("V-106h" in str(s["status"]) for s in early)
          and all(str(s["status"]).startswith("draft") for s in seeds),
          "every seed is a draft; the five earlier openers are marked V-106h")
    rows = ve.seed_rows(GATE_NOW)
    check(len(rows) == 26 and all(json.loads(r["value"])["seed"] for r in rows)
          and all(r["registry_key"] == ve.LEDGER_KEY for r in rows),
          "seed-tags writes 26 vol.event_ledger rows marked seed")
    st = ve.ledger_status([{"outcomes": {"resolved": True}},
                           {"seed": True, "outcomes": None}], ve.config())
    check(st.startswith("event ledger: 1 events, 1 resolved")
          and "(1 seed rows, not counted)" in st,
          "seed rows never count toward the 30-event right")


def group_g(ev) -> None:
    head("G. THE LEDGER ROUND TRIP ON A FIXTURE STORE; AHEAD READS IT")
    from altdata import events, observations                    # noqa: PLC0415
    db = str(TD / "store.db")
    with events.EventStore(db) as es:
        es.write_many([events.Event("scheduled", "2026-11-12T13:30:00+00:00",
                                    "claims_registry", "Consumer Price Index -- 2026-11-12"),
                       events.Event("scheduled", "2026-11-12T19:00:00+00:00",
                                    "claims_registry", "FOMC minutes -- 2026-11-12")],
                      available_at="2026-11-01T00:00:00+00:00")
    with observations.ObservationStore(db) as st:
        st.write_many([{"registry_key": "yfinance.mkt_spy", "instrument": None,
                        "observed_at": d, "available_at": f"{d}T21:05:00+00:00",
                        "value": v, "source": "yfinance"}
                       for d, v in (("2026-11-10", 99.0), ("2026-11-11", 100.0))])
    r1 = ev.eod("2026-11-11", GATE_NOW, db, CHAINS)
    check(r1["rows"] == 1 and r1["recorded"] == ["cpi:2026-11-12"],
          f"the EOD step on T-1 records the CPI row and not the minutes ({r1})")
    check(ev.eod("2026-11-11", "2026-11-11T21:30:00+00:00", db, CHAINS)["rows"] == 0,
          "a second run on the same day writes nothing")
    rows = ev.ledger_rows(db, "2026-11-11T21:40:00+00:00")
    b = rows[0] if rows else {}
    check(len(rows) == 1 and b["T"] == "2026-11-12" and b["T_minus_1"] == "2026-11-11"
          and abs(b["implied"]["event_pct"] - 1.2) < 1e-9
          and b["scheduled"] == "scheduled" and b["catalyst_class"] == "data print",
          "the row carries T, T-1, the implied event move and its default tags")
    with observations.ObservationStore(db) as st:
        st.write_many([{"registry_key": "yfinance.mkt_spy", "instrument": None,
                        "observed_at": d, "available_at": f"{d}T21:05:00+00:00",
                        "value": v, "source": "yfinance"}
                       for d, v in (("2026-11-12", 102.0), ("2026-11-13", 101.0),
                                    ("2026-11-16", 103.02))])
    r2 = ev.eod("2026-11-16", "2026-11-16T21:20:00+00:00", db, CHAINS)
    nb = ev.ledger_rows(db, "2026-11-16T21:40:00+00:00")
    rr = (nb[0] if nb else {}).get("realised") or {}
    check(r2["rows"] == 1 and rr.get("resolved") and rr.get("t") == 2.0
          and rr.get("headline") == 2.0,
          f"a later EOD step resolves T, T+1, T+2 as a new vintage ({rr})")
    old = ev.ledger_rows(db, "2026-11-11T21:40:00+00:00")
    check(old and not (old[0].get("realised") or {}).get("resolved"),
          "the earlier vintage is still the answer as of its own time")
    anns = ev.ahead_annotations([{"title": "Consumer Price Index", "date": "2026-11-12"},
                                 {"title": "FOMC minutes", "date": "2026-11-12"}],
                                "2026-11-11", db, "2026-11-16T21:40:00+00:00", CHAINS)
    check(anns[1] is None and anns[0] and "accruing (n=1 of 20)" in anns[0]["text"]
          and "implied ±1.2%" in anns[0]["text"] and not anns[0]["fired"],
          f"Ahead reads the ledger: accruing (n=1 of 20), the implied move ({anns[0]})")
    tree = ast.parse((REPO / "altdata" / "event_vol.py").read_text(encoding="utf-8"))
    mods = [n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)] + \
        [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
    check(not any("flashalpha" in m.lower() or "vendor" in m.lower() for m in mods),
          "no FlashAlpha or vendor import anywhere in the module (the 9 Oct rule)")


def main() -> int:
    pin_clock()
    print(f"the gate's clock is pinned to {GATE_NOW}")
    from altdata import event_vol as ev                         # noqa: PLC0415
    try:
        for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g):
            g(ev)
    finally:
        import shutil                                           # noqa: PLC0415
        shutil.rmtree(TD, ignore_errors=True)
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
