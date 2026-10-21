"""
Signal-triage Batch 13, item 61 (docs/change-order-signal-triage-batch-13-
2026-10-20.md, ruled 20 Oct 2026, D1-D5; session A's a54-relative-volume): OS-12,
relative options volume.

  A  THE RATIO at, below and above 1.5: 1.5x flags (at least), 1.49x does not, 1.6x
     does; under 20 stored sessions the ratio prints "provisional (n sessions)";
     no prior session, no ratio.
  B  THE READINGS over a synthetic store: the 19 names (the 17 and SPX, SPCX); the
     call/put split from the stored put share; the front-month IV change by OS-10's
     method; the close's table -- flagged names only, five rows at most, six
     columns, "volume, no side", the threshold's label -- and nothing on a quiet day.
  C  THE NEXT MORNING'S TAG AND THE NEXT CLOSE'S LINE (D4): yesterday's flags
     recomputed as of yesterday's 16:45 cutoff (a row knowable only after it does
     not count); OS-9's builds on the flag day's and the next session's captures
     decide "became an OI build": k became builds, m did not, a name without both
     captures said so; the tag is OS-9's Context word.
  D  NO SIDE INFERRED: every printed string carries no side word, and every row
     carries "volume, no side".
  E  THE LEDGER: the pre-registration on file at its SHA-256, "Never edited"; the
     scoring script opens no store and names it; its rule on fixtures (INSUFFICIENT,
     PASS, FAIL); the first edition on file, INSUFFICIENT.
  F  THE FLAT-FILE VOLUME (D5): the backfill's readings carry the day's total, call
     and put volume; the relative tolerance admits a 9% gap and refuses an 11% one;
     A48's four tolerances and the 10-session overlap unchanged; the captured
     reading wins on a shared session.
  G  CONFIGURATION AND PLACEMENT: the threshold, window and label; the close's
     table among the detail tables after the session's readings are stored; the
     next close's Mechanics item; the Weekly's table; the anchor's tag; registered.

Synthetic fixtures only: no live store, no network, no model, no real names.
"""

from __future__ import annotations

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
TD = Path(mkdtemp("batch13-gate-"))
LIVE_DB = REPO / "data" / "chester.db"
LIVE_DB_AT_START = LIVE_DB.exists()
PREREG = "docs/ledgers/relative-volume-preregistration-2026-10.md"
PREREG_SHA = "a1bd6de723afeedf53d2bfe13c382c43eb834de9bc7641fc9ca34bac0287fe4b"
SIDE_WORDS = re.compile(r"\b(bought|sold|buyers?|sellers?|bullish|bearish|long|short|"
                        r"opened by|bet|bets|hedger|speculator)\b", re.I)


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


def weekdays(end: str, n: int) -> list[str]:
    d, out = dt.date.fromisoformat(end), []
    while len(out) < n:
        if d.weekday() < 5:
            out.insert(0, d.isoformat())
        d -= dt.timedelta(days=1)
    return out


DAYS = weekdays("2026-10-16", 30)
FLAG_DAY, NEXT_DAY = DAYS[-2], DAYS[-1]


def seed(db: Path, spikes: dict, late: bool = False) -> None:
    """chain.options_volume for N1..N7 at 1,000 a session; on FLAG_DAY, N_k at its
    spike multiple. With `late`, a restated FLAG_DAY row for N7 is knowable only
    the next morning."""
    from altdata import observations
    rows = []
    for s in ("N1", "N2", "N3", "N4", "N5", "N6", "N7"):
        for d in DAYS:
            v = 1000.0 * (spikes.get(s, 1.0) if d == FLAG_DAY else 1.0)
            rows.append({"registry_key": "chain.options_volume", "instrument": s,
                         "observed_at": d, "available_at": f"{d}T20:31:00+00:00",
                         "value": v, "source": "chain_capture"})
            rows.append({"registry_key": "chain.put_share_volume", "instrument": s,
                         "observed_at": d, "available_at": f"{d}T20:31:00+00:00",
                         "value": 40.0, "source": "chain_capture"})
            rows.append({"registry_key": "chain.atm_iv_front", "instrument": s,
                         "observed_at": d, "available_at": f"{d}T20:31:00+00:00",
                         "value": 30.0 + (2.0 if d == FLAG_DAY else 0.0),
                         "source": "chain_capture"})
    if late:
        rows.append({"registry_key": "chain.options_volume", "instrument": "N7",
                     "observed_at": FLAG_DAY, "available_at": f"{NEXT_DAY}T13:00:00+00:00",
                     "value": 9000.0, "source": "chain_capture"})
    with observations.ObservationStore(str(db)) as st:
        st.write_many(rows)


NAMES = ["N1", "N2", "N3", "N4", "N5", "N6", "N7"]


# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. THE RATIO AT, BELOW AND ABOVE 1.5")
    from daily_cascade import relative_volume as rv
    hist = [(d, 1000.0) for d in DAYS[:-1]]

    def r(v):
        return rv.ratio(hist + [(DAYS[-1], v)], DAYS[-1])
    at, below, above = r(1500.0), r(1490.0), r(1600.0)
    check(rv.is_flag(at, 1.5) and not rv.is_flag(below, 1.5) and rv.is_flag(above, 1.5),
          "1.5x flags (at least 1.5), 1.49x does not, 1.6x does")
    check(abs(at["ratio"] - 1.5) < 1e-12 and at["n"] == 20 and not at["provisional"]
          and "provisional" not in rv.ratio_text(at),
          "the average is the 20 sessions before the day; 20 stored: not provisional")
    short = rv.ratio([(d, 1000.0) for d in DAYS[:7]] + [(DAYS[7], 2000.0)], DAYS[7])
    check(short["provisional"] and short["n"] == 7
          and rv.ratio_text(short).endswith("provisional (7 sessions)"),
          f"under 20 sessions: 'provisional (n sessions)' ({rv.ratio_text(short)})")
    check(rv.ratio([(DAYS[0], 1000.0)], DAYS[0]) is None
          and rv.ratio(hist, "2027-01-04") is None,
          "no prior session, or no reading on the day: no ratio")


def group_b() -> None:
    head("B. THE READINGS AND THE CLOSE'S TABLE")
    from altdata import config as acfg, observations
    from daily_cascade import relative_volume as rv
    check(rv.names() == acfg.chain_universe() + sorted(acfg.massive_universe())
          and len(rv.names()) == 19 and {"SPX", "SPCX"} <= set(rv.names()),
          "the 19 names: the 17 of chain_universe() and SPX, SPCX from the Massive chains")
    db = TD / "b.db"
    seed(db, {"N1": 3.0, "N2": 2.5, "N3": 2.0, "N4": 1.8, "N5": 1.6, "N6": 1.5, "N7": 1.2})
    cut = rv.close_cutoff(FLAG_DAY)
    with observations.ObservationStore(str(db)) as st:
        rs = rv.readings(st, FLAG_DAY, cut, syms=NAMES)
        fl = rv.flagged(st, FLAG_DAY, cut, syms=NAMES)
        tab = rv.close_table(st, FLAG_DAY, cut, syms=NAMES)
        quiet = rv.close_table(st, DAYS[-5], rv.close_cutoff(DAYS[-5]), syms=NAMES)
    by = {r["symbol"]: r for r in rs}
    check([r["symbol"] for r in fl] == ["N1", "N2", "N3", "N4", "N5", "N6"]
          and not by["N7"]["flag"], "six flagged (1.5x and over), N7 at 1.2x not")
    check(by["N1"]["iv_change"] == 2.0 and rv.split_text(by["N1"]["put_share"])
          == "calls 60% / puts 40%",
          "the front-month IV change (the last two stored readings) and the call/put split")
    rows = tab["table"]["rows"]
    check(len(rows) == 5 and tab["data"]["flagged"] == 6 and len(tab["table"]["columns"]) == 6
          and all(r[-1] == "volume, no side" for r in rows) and rows[0][0] == "N1",
          "the close's table: flagged names only, five rows at most, six columns, highest first")
    check("session-set, provisional, frozen 30 days from 2026-10-20" in tab["legend"]
          and "6 flagged, 5 shown" in tab["legend"],
          "the legend carries the threshold's label and the count shown")
    check(quiet is None, "a session with no flag prints no table")


def _caps(base: Path, day: str, sym: str, oi: float) -> None:
    from validate_opening_setup import _csv
    _csv(base / day / f"{sym}_201000Z.csv",
         [("2026-11-20", 30, "C", 100.0, 1.0, 1.2, 1.1, 5000, oi,
           f"{day}T20:10:00+00:00", 100.0)])


def group_c() -> None:
    head("C. THE NEXT MORNING'S TAG AND THE NEXT CLOSE'S LINE (D4)")
    from altdata import chain_metrics as cm, observations
    from daily_cascade import opening_setup as OS, relative_volume as rv
    from validate_opening_setup import _FakeSolver
    cm._solver = lambda: _FakeSolver                            # noqa: SLF001
    db = TD / "c.db"
    seed(db, {"N1": 3.0, "N2": 2.0, "N3": 1.7}, late=True)
    with observations.ObservationStore(str(db)) as st:
        got = rv.flagged_yesterday(st, FLAG_DAY, syms=NAMES)
        base = TD / "chains"
        _caps(base, FLAG_DAY, "N1", 1000)
        _caps(base, NEXT_DAY, "N1", 7000)               # +6,000: a build over the floor
        _caps(base, FLAG_DAY, "N2", 1000)
        _caps(base, NEXT_DAY, "N2", 1100)               # +100: under the floor
        line = rv.next_close_line(st, FLAG_DAY, NEXT_DAY, base=base, syms=NAMES)
    check(got == {"N1", "N2", "N3"},
          "yesterday's flags recomputed as of its 16:45 cutoff; N7's restatement, "
          "knowable only the next morning, does not count")
    check(line.startswith("Yesterday's flagged names: 1 became OI builds, 1 did not (N1 did)")
          and "1 without both captures (N3)" in line and "volume, no side" in line,
          f"the next close's line: k became builds, m did not, the rest said so ({line})")
    b = rv.became_builds(FLAG_DAY, NEXT_DAY, {"N1", "N2"}, base=TD / "chains")
    check(b == {"N1": True, "N2": False} and OS.oi_floor("N1", OS.config()) == 500,
          "OS-9's builds on the flag day's and the next session's captures, at its floor")
    check(OS.VOLUME_FLAG_TAG == "volume flag yesterday",
          "the anchor's tag in OS-9's Context column")


def group_d() -> None:
    head("D. NO SIDE INFERRED")
    from altdata import observations
    from daily_cascade import relative_volume as rv
    db = TD / "d.db"
    seed(db, {"N1": 3.0})
    with observations.ObservationStore(str(db)) as st:
        tab = rv.close_table(st, FLAG_DAY, rv.close_cutoff(FLAG_DAY), syms=NAMES)
        wk = rv.weekly_subsection(st, DAYS[-5:], rv.close_cutoff(NEXT_DAY), syms=NAMES,
                                  ledger_dir=TD)
    strings = ([tab["legend"]] + [c for r in tab["table"]["rows"] for c in r]
               + wk["lines"] + [wk["table_note"]])
    bad = [s for s in strings if SIDE_WORDS.search(str(s))]
    check(not bad, f"no printed string infers a side ({bad[:2] or 'none'})")
    check(all(r[-1] == "volume, no side" for r in tab["table"]["rows"])
          and "Volume, no side" in wk["table_note"],
          "every row and the Weekly's note say 'volume, no side'")
    check(wk["table"]["rows"] == [["N1", "1"]] and any("no edition yet" in x for x in wk["lines"]),
          "the Weekly: flags per name, and the ledger to date ('no edition yet' when none)")


def group_e() -> None:
    head("E. THE LEDGER")
    raw = (REPO / PREREG).read_bytes().replace(b"\r\n", b"\n")
    check(hashlib.sha256(raw).hexdigest() == PREREG_SHA and b"Never edited" in raw,
          "the pre-registration on file at its SHA-256 (LF bytes), 'Never edited'")
    src = (REPO / "tools" / "calibration" / "os12c_relative_volume.py").read_text(encoding="utf-8")
    check(not re.search(r"ObservationStore|from altdata import .*observations|regime\.", src)
          and PREREG in src, "the scoring script opens no store and names its registration")
    import os12c_relative_volume as L
    days = weekdays("2026-10-16", 80)

    def data(spike_move: float, names: int = 6):
        vol, closes, iv = {}, {}, {}
        for k in range(names):
            s = f"N{k}"
            vol[s] = [(d, 3000.0 if i % 10 == 5 else 1000.0) for i, d in enumerate(days)]
            px, cl = 100.0, []
            for i, d in enumerate(days):
                px *= (1 + (spike_move if (i - 5) % 10 in (1, 2, 3) and i % 2 == 0 else 0.001))
                cl.append((d, px))
            closes[s], iv[s] = cl, {d: 30.0 for d in days}
        return {"volume": vol, "closes": closes, "iv": iv, "sessions": len(days)}
    few = L.study(data(0.0, names=2), "fixture")
    check(few["verdict"].startswith("INSUFFICIENT"), f"two names: INSUFFICIENT ({few['verdict'][:60]})")
    hi = L.study(data(0.03), "fixture")
    check(hi["verdict"].startswith("PASS"), f"spikes before larger moves: PASS ({hi['verdict']})")
    lo = L.study(data(0.0), "fixture")
    check(lo["verdict"].startswith("FAIL"), f"spikes before no larger moves: FAIL ({lo['verdict']})")
    led = (REPO / "docs" / "ledgers" / "os-12c-ledger-2026-10-20.md").read_text(encoding="utf-8")
    check("| Verdict | **INSUFFICIENT" in led and "| n | 0 |" in led,
          "the first edition on file: INSUFFICIENT, n 0 (no captures on the laptop), a result")


def group_f() -> None:
    head("F. THE FLAT-FILE VOLUME (D5)")
    from altdata import flatfile_history as ffh
    import massive_flatfiles_backfill as bf
    rows = [{"right": "C", "volume": 600.0}, {"right": "P", "volume": 400.0}]
    rd = bf.readings(rows)
    check(rd["chain.options_volume"] == 1000.0 and rd["chain.call_volume"] == 600.0
          and rd["chain.put_volume"] == 400.0 and rd["chain.put_share_volume"] == 40.0,
          "the backfill's readings carry the day's total, call and put volume")
    cap = {d: 1000.0 for d in DAYS[:12]}
    check(ffh.admitted(cap, {d: 1090.0 for d in cap}, "chain.options_volume")
          and not ffh.admitted(cap, {d: 1110.0 for d in cap}, "chain.options_volume")
          and not ffh.admitted(dict(list(cap.items())[:9]), {d: 1000.0 for d in DAYS[:9]},
                               "chain.call_volume"),
          "the relative tolerance: a 9% gap admitted, an 11% gap refused, under 10 sessions none")
    check(ffh.TOLERANCE == {"chain.iv30_atm": 1.5, "chain.skew_25d_put": 1.5,
                            "chain.rr_25d": 2.0, "chain.put_share_volume": 5.0}
          and ffh.MIN_OVERLAP == 10
          and ffh.VOLUME_TOLERANCE_REL == {"chain.options_volume": 0.10,
                                           "chain.call_volume": 0.10,
                                           "chain.put_volume": 0.10},
          "A48's four tolerances and the 10-session overlap unchanged; the volume keys a "
          "dated addition beside them")
    rs = ([{"observed_at": d, "value_num": 1000.0, "source": "chain_capture"} for d in DAYS[:12]]
          + [{"observed_at": d, "value_num": 1050.0, "source": ffh.SOURCE} for d in DAYS[:12]]
          + [{"observed_at": "2024-01-02", "value_num": 800.0, "source": ffh.SOURCE}])
    m, note = ffh.merged(rs, "chain.options_volume")
    check(m[DAYS[0]] == 1000.0 and m["2024-01-02"] == 800.0 and note,
          "the captured reading wins on a shared session; the admitted history joins before it")


def group_g() -> None:
    head("G. CONFIGURATION AND PLACEMENT")
    from daily_cascade import relative_volume as rv
    c = rv.config()
    check(c["threshold"] == 1.5 and c["window"] == 20 and c["max_rows"] == 5
          and c["earnings_sessions"] == 10
          and c["label"] == "session-set, provisional, frozen 30 days from 2026-10-20",
          "the threshold 1.5, the 20-session window, five rows, 10 sessions, the label")
    sc = (REPO / "daily_cascade" / "stack_close.py").read_text(encoding="utf-8")
    i_rec, i_os, i_det = (sc.find("chain_metrics.record_session(sess, st)"),
                          sc.find("_rv.close_table(st, sess"), sc.find('ed["detail"].append(os12)'))
    check(0 < i_rec < i_os < i_det, "the close's table is read after the session's readings "
                                    "are stored, and prints among the detail tables")
    sk = (REPO / "daily_cascade" / "stack.py").read_text(encoding="utf-8")
    dw = (REPO / "daily_cascade" / "dealer_weekly.py").read_text(encoding="utf-8")
    os_ = (REPO / "daily_cascade" / "opening_setup.py").read_text(encoding="utf-8")
    check('item("mech:os12_outcome"' in sk and "_rv.weekly_subsection(st, week, cutoff)" in dw
          and "tg.setdefault(s, []).append(VOLUME_FLAG_TAG)" in os_,
          "the next close's Mechanics item, the Weekly's table, the anchor's OS-9 tag")
    from altdata import derived
    check(all(derived.registry_entry(k) for k in ("chain.options_volume", "chain.call_volume",
                                                 "chain.put_volume")),
          "the volume keys registered")
    yml = (REPO / "config" / "opening_setup.yaml").read_text(encoding="utf-8")
    blk = yml[yml.find("relative_volume:"):yml.find("# OS-11")]
    check(blk and not re.search(r"\b(score|weight)", blk, re.I),
          "no score or weight in OS-12's config block")


def main() -> int:
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g):
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
