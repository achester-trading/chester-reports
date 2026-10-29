#!/usr/bin/env python3
"""
Validation gate: signal triage Batch 16, items 80(b) and 90 -- the midterm
base-rate table and the 3 Nov 2026 row in the Weekly's Ahead (paste A78, 26 Oct
2026). Fixtures only; no network, no model, no live store.

  A  THE LEDGER. docs/ledgers/midterm-base-rate-2026-10-26.md: the computation
     printed at its head hashes to the SHA-256 recorded beside it, which is the
     script's own; the CSV hashes to its recorded SHA-256; nineteen rows, 1950 to
     2022, none missing, every field filled; the headline's midterm figures are
     the CSV's.
  B  THE ARITHMETIC. study() on a synthetic series: election day by rule, the
     drawdown and its trough, the low against election day in sessions and days,
     the forward returns, the recession flag (and "not stored" without it).
  C  THE AHEAD ROW. config/weekly_ahead.yaml carries the ledger's headline
     verbatim; on a fixture store with the House and Senate markets, the 3 Nov row
     prints "US midterm election" at tier 2 with each venue's odds as its
     consensus and the base rate beside its channel; with no odds stored it prints
     "odds not stored"; a week without the date has no row.
  D  NO NAME OF A PERSON in the new code, config, ledger or appendix line
     (H5), checked against digests so this gate carries none either.

    python tools/validate_batch16_midterm.py
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "tools" / "calibration"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402
import midterm_base_rate as mbr                                 # noqa: E402

TD = Path(gate_mkdtemp("batch16_midterm_"))
LINE = "=" * 78
PASS = FAIL = 0
LEDGER = REPO / "docs" / "ledgers" / "midterm-base-rate-2026-10-28.md"
CSV = LEDGER.with_suffix(".csv")
CLAIM = "cal.midterm_election_2026"
# The first 16 hex of the SHA-256 of each lower-cased name in the order's voices
# register and sources (H5): the gate holds digests, never the names.
NAME_DIGESTS = {
    "014e3f1f20764cc5", "08e486faf56b304c", "09adea004144f250", "2af232623b04ce98",
    "2dbe33913ae5d6b1", "34550715062af006", "3a9094e2fcd927af", "424865ff0e73c522",
    "434eb8457a2b1452", "44b5aa11f3e96ea2", "4c617e204d9c1bf3", "4d63fb753eae6df6",
    "4db16eb962f33f6f", "52610e3505010dec", "57b379df03af9918", "8a8f7e714c97426a",
    "960f984285701c6d", "a86989534125eaaf", "b9dd960c1753459a", "d7feb900e6b02c9a"}


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


def lf_sha(p: Path) -> str:
    """A committed text file's SHA-256 as written (LF), whatever the checkout
    did to its line ends."""
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. THE LEDGER: ITS COMPUTATION AND ITS CSV HOLD THEIR HASHES; 19 ROWS")
    md = LEDGER.read_text(encoding="utf-8").replace("\r\n", "\n")
    block = md.split(mbr.BEGIN, 1)[1].split(mbr.END, 1)[0]
    text = block.split("```text\n", 1)[1].rsplit("\n```", 1)[0] + "\n"
    rec = re.search(r"\| Computation SHA-256 \| `([0-9a-f]{64})` \|", md)
    check(rec and hashlib.sha256(text.encode("utf-8")).hexdigest() == rec.group(1),
          "the computation printed at the head hashes to the SHA-256 beside it")
    check(rec and rec.group(1) == mbr.computation_sha256(),
          "and that is the script's own pre-registered computation")
    rc = re.search(r"\| CSV SHA-256 \| `([0-9a-f]{64})` \(([^)]+)\) \|", md)
    check(rc and rc.group(2) == CSV.name and lf_sha(CSV) == rc.group(1),
          f"the CSV ({CSV.name}) hashes to its recorded SHA-256")
    with open(CSV, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    years = [int(r["year"]) for r in rows]
    check(years == list(range(1950, 2023, 4)) and len(rows) == 19,
          f"nineteen midterm years, 1950 to 2022, none missing ({len(rows)} rows)")
    must = (["drawdown_pct", "low_date", "election_day", "low_to_election_sessions",
             "low_to_election_days", "recession"]
            + [f"from_low_{k}m_pct" for k in mbr.HORIZONS]
            + [f"from_election_{k}m_pct" for k in mbr.HORIZONS])
    check(all(r.get(k) not in (None, "") for r in rows for k in must),
          "every row carries the drawdown, the low, its place against election "
          "day, eight forward returns and the recession flag")
    check(all(r["election_day"] == mbr.election_day(int(r["year"])).isoformat()
              for r in rows) and all(r["recession"] in ("yes", "no", mbr.NOT_STORED)
                                     for r in rows),
          "election day by rule on every row; the flag is yes, no or not stored")
    check(all(float(r["drawdown_pct"]) <= 0 and r["peak_date"] <= r["trough_date"]
              == r["low_date"] for r in rows),
          "each drawdown is a fall from a peak to a later trough, and the trough "
          "is the row's low")
    s = mbr.summary(rows, [{"drawdown_pct": 0.0}])
    line = md.split("\n> ", 1)[1].split("\n", 1)[0]
    want = (f"median {mbr.pc(s['mid_median'])} (mean {mbr.pc(s['mid_mean'])})",
            f"before election day in {s['low_before']} of 19, {s['low_aug_oct']} "
            f"of them in August to October",
            f"higher 12 months later in {s['e12_up']} of {s['e12_n']}, median "
            f"{mbr.pc(s['e12_median'])}", "n = 19.")
    check(all(w in line for w in want),
          "the headline's midterm figures are the CSV's, recomputed")
    oth = re.search(r"\| Other years \| (\d+) \| (\S+) \| (\S+) \|", md)
    check(oth and f"against {oth.group(3)} (mean {oth.group(2)}) in the "
          f"{oth.group(1)} other years" in line,
          "and its other-years figures are the ledger's comparison table's")
    check("The order (chat)" in md and "V11" in md,
          "the order's chat figures print beside the ledger's (V11)")


# ---------------------------------------------------------------------------
def weekdays(a: str, b: str) -> list[str]:
    d, e, out = dt.date.fromisoformat(a), dt.date.fromisoformat(b), []
    while d <= e:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def group_b() -> None:
    head("B. THE ARITHMETIC, ON A SYNTHETIC SERIES")
    check(mbr.election_day(2026) == dt.date(2026, 11, 3)
          and mbr.election_day(2022) == dt.date(2022, 11, 8)
          and mbr.election_day(1950) == dt.date(1950, 11, 7),
          "election day is the first Tuesday after the first Monday in November")
    days = weekdays("1950-01-02", "2024-12-31")
    px = []
    for d in days:
        v = 100.0
        if "1950-06-01" <= d <= "1950-07-14":
            v = 100.0 - 20.0 * (dt.date.fromisoformat(d)
                                - dt.date(1950, 6, 1)).days / 43
        elif "1950-07-14" < d <= "1950-08-31":
            v = 80.0
        elif d > "1950-08-31":
            v = 120.0
        px.append((d, v))
    usrec = [(f"{y}-{m:02d}-01", 1.0 if y == 1954 else 0.0)
             for y in range(1950, 2025) for m in range(1, 13)]
    r = mbr.study(px, usrec)
    rows = {w["year"]: w for w in r["rows"]}
    w = rows[1950]
    check(len(r["rows"]) == 19 and r["last_complete"] == 2024,
          "nineteen midterm years from a series ending 2024")
    check(abs(w["drawdown_pct"] + 20.0) < 1e-6 and w["low_date"] == "1950-07-14"
          and w["peak_date"] < w["low_date"],
          f"1950's drawdown is the fixture's -20% and its trough the low "
          f"({w['drawdown_pct']}, {w['low_date']})")
    ed_i = days.index("1950-11-07")
    check(w["low_to_election_days"] == (dt.date(1950, 11, 7)
                                        - dt.date(1950, 7, 14)).days
          and w["low_to_election_sessions"] == ed_i - days.index("1950-07-14"),
          "the low against election day in calendar days and in sessions")
    check(abs(w["from_low_1m_pct"]) < 1e-9 and abs(w["from_low_3m_pct"] - 50.0) < 1e-6
          and abs(w["from_election_12m_pct"]) < 1e-9,
          "forward returns to the last session on or before the date k months on")
    check(rows[1954]["recession"] == "yes" and w["recession"] == "no"
          and mbr.study(px, None)["rows"][0]["recession"] == mbr.NOT_STORED,
          "the recession flag: yes, no, and 'not stored' without the series")
    check(all(abs(rows[y]["drawdown_pct"]) < 1e-9 for y in rows if y != 1950)
          and len(r["others"]) == 75 - 19,
          "the flat years draw nothing down; 56 other years, 1950 to 2024")


# ---------------------------------------------------------------------------
def pm_store(name: str, with_odds: bool):
    from altdata import observations                            # noqa: PLC0415
    st = observations.ObservationStore(str(TD / f"{name}.db"))
    if not with_odds:
        return st
    at = "2026-10-30T20:10:00+00:00"

    def mk(inst, venue, wid, outcome, p):
        meta = {"watch_id": wid, "venue": venue, "outcome": outcome,
                "question": f"{wid} fixture", "event_id": inst}
        st.write("pm.market", inst, at, at, json.dumps(meta, sort_keys=True),
                 venue, availability_kind="ingest_instant")
        st.write("pm.probability", inst, at, at, p, venue,
                 availability_kind="ingest_instant")
    mk("kalshi:CONTROLH-2026-D", "kalshi", "house_control", "Democratic Party", 0.62)
    mk("kalshi:CONTROLH-2026-R", "kalshi", "house_control", "Republican Party", 0.38)
    mk("polymarket:house-d", "polymarket", "house_control", "Democratic", 0.60)
    mk("kalshi:CONTROLS-2026-D", "kalshi", "senate_control", "Democratic Party", 0.35)
    mk("polymarket:senate-d", "polymarket", "senate_control", "Democratic", 0.33)
    return st


def ahead_row(db_path, week_ending="2026-10-31"):
    from daily_cascade import ahead                             # noqa: PLC0415
    a = ahead.build({}, {"week_ending": week_ending}, None,
                    "2026-11-01T09:00:00+00:00", db_path=db_path)
    return next((r for r in a["rows"] if r.get("claim") == CLAIM), None), a


def group_c() -> None:
    import yaml                                                 # noqa: PLC0415
    head("C. THE AHEAD ROW: TIER 2, THE ODDS AS ITS CONSENSUS, THE BASE RATE")
    cfg = yaml.safe_load((REPO / "config" / "weekly_ahead.yaml")
                         .read_text(encoding="utf-8"))
    n = (cfg.get("register_event_rows") or {}).get(CLAIM) or {}
    md = LEDGER.read_text(encoding="utf-8").replace("\r\n", "\n")
    line = md.split("\n> ", 1)[1].split("\n", 1)[0]
    check(n.get("base_rate") == line and n.get("ledger") ==
          LEDGER.relative_to(REPO).as_posix(),
          "the config carries the ledger's headline verbatim, and names the ledger")
    tier = (cfg["classes"].get(n.get("cls")) or {}).get("tier")
    check(n.get("significance") == 4 and tier == 2,
          "significance 4 maps to tier 2 (5 -> 1, 4 -> 2, 1-3 -> 3)")
    st = pm_store("odds", True)
    st.close()
    r, a = ahead_row(str(TD / "odds.db"))
    check(r is not None and r["event"] == "US midterm election"
          and r["date"] == "2026-11-03" and r["tier"] == 2,
          f"the row prints for Tue 3 Nov at tier 2 ({r and r['event']})")
    cons = (r or {}).get("consensus") or ""
    check("Democrats winning the House: Kalshi 62%, Polymarket 60%" in cons
          and "Democrats winning the Senate: Kalshi 35%, Polymarket 33%" in cons
          and "(as of 2026-10-30)" in cons,
          f"the consensus column is the stored odds, both venues, both chambers "
          f"({cons})")
    why = (r or {}).get("why") or ""
    check(why.startswith("control of Congress") and line in why,
          "the why-it-matters line, with the base rate beside it")
    trow = next((t for t in a["table"]["rows"] if t[1] == "US midterm election"), None)
    check(trow is not None and trow[0].startswith("Tue 3 Nov") and trow[2] == 2
          and trow[3] == cons,
          "and the rendered table row carries the day, the tier and the odds")
    st = pm_store("empty", False)
    st.close()
    r2, _ = ahead_row(str(TD / "empty.db"))
    r3, _ = ahead_row(None)
    check(r2 and r2["consensus"] == "odds not stored" and r3
          and r3["consensus"] == "odds not stored",
          "no odds stored (an empty store, or none passed): 'odds not stored'")
    r4, _ = ahead_row(None, week_ending="2026-11-07")
    check(r4 is None, "the following week has no midterm row")


# ---------------------------------------------------------------------------
def group_d() -> None:
    head("D. NO NAME OF A PERSON IN THE NEW CODE, CONFIG, LEDGER OR APPENDIX LINE")
    q = (REPO / "docs" / "dated-appendix-queue.md").read_text(encoding="utf-8")
    entry = q.split("Batch 16 items 80(b) and 90", 1)
    files = {"tools/calibration/midterm_base_rate.py": None,
             "daily_cascade/ahead.py": None, "config/weekly_ahead.yaml": None,
             LEDGER.relative_to(REPO).as_posix(): None,
             CSV.relative_to(REPO).as_posix(): None}
    hits = []
    for f in files:
        words = set(re.findall(r"[a-z]+", (REPO / f).read_text(encoding="utf-8")
                               .lower()))
        hits += [f for w in words
                 if hashlib.sha256(w.encode()).hexdigest()[:16] in NAME_DIGESTS]
    check(len(entry) == 2, "the dated-appendix entry is in the queue")
    if len(entry) == 2:
        words = set(re.findall(r"[a-z]+", entry[1].split("\n## ", 1)[0].lower()))
        hits += ["appendix entry" for w in words
                 if hashlib.sha256(w.encode()).hexdigest()[:16] in NAME_DIGESTS]
    check(not hits, f"none of the order's named people appears ({sorted(set(hits))})")


def main() -> int:
    try:
        group_a()
        group_b()
        group_c()
        group_d()
    finally:
        import shutil                                           # noqa: PLC0415
        shutil.rmtree(TD, ignore_errors=True)
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
