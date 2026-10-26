"""
Signal-triage Batch 15, session A's part (items 72, 73 and 76;
docs/change-order-signal-triage-batch-15-2026-10-23.md, ruled 20 and 23 Oct 2026
with filing amendments G1-G6; a58-batch15-1).

  A  THE FILING: the order on file at its SHA-256, indexed in docs/change-orders.md
     after Batch 14 and in the signal-triage register's header.
  B  ITEM 72, THE 13F LINE: a fixture data set counted by hand -- originals, a
     RESTATEMENT, a NEW HOLDINGS amendment, an option, a principal amount, a 13F-NT,
     IAU's earlier CUSIP, the thousands rule before 3 Jan 2023; a partial quarter not
     written; a changed layout refused; the change from the prior quarter through a
     store round-trip; the absent path; WGC's flows a listed gap.
  C  ITEM 73, THE GOLD EVENT: the one-day arm and the five-day arm, the five-day
     threshold by hand; the attribution's legs by hand, "awaiting", "not tracked"
     (ETF flows) and the IMF IFS central-bank trend, absent on short history; the
     residual line's count; the ledger row, resolve's new vintage; the history
     pass's short-history note.
  D  ITEM 73, THE DM DRAWDOWN SCREEN: the drawdown and its 95th percentile by hand;
     a short-history index "not read"; the gap per missing index by name; the ETF
     proxies labelled; the local 10-year "not tracked" where no daily series is
     stored; Japan's carry and slow-money legs.
  E  ITEM 76: check 4 failed, so the whole item is a listed gap: no protection-
     demand line, no flag, no DTCC key; the AI-credit gap line amended to point at
     it and the dated records; the dated records in the appendix queue.
  F  PLACEMENT: the close's flag lines after item 52's and item 65's events, the
     ledger rows stored only off a dry run; the Weekly's and the Monthly's blocks;
     item 72 right after item 38's gold/equity ratio; the EOD resolve.
  G  REGISTRATION: every new key, block, source and command; NIKKEI225 in the FRED
     pull; no Brookfield instrument among the funds, indices or proxies.
  H  HYGIENE: no person's name, handle or email address in the new files or the
     appendix records; no composite, market-state, register or order import; no
     write to the live store.

Synthetic fixtures only: no live store, no network, no model.
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import ast
import datetime as dt
import hashlib
import io
import json
import math
import re
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gate_tmp import mkdtemp                                    # noqa: E402

LINE = "=" * 78
PASS = FAIL = 0
TD = Path(mkdtemp("batch15-1-gate-"))
LIVE_DB = REPO / "data" / "chester.db"


def _hash(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


LIVE_AT_START = _hash(LIVE_DB)
ORDER = "docs/change-order-signal-triage-batch-15-2026-10-23.md"
ORDER_SHA = "d5318a6d67d9d9a45d338aba32394547614a1f85333961e9c516310482f24e25"
NEW_MODULES = ("altdata/gold_13f.py", "altdata/gold_event.py", "altdata/dm_drawdown.py",
               "altdata/asset_event.py", "daily_cascade/batch15_a_block.py")
NEW_CONFIG = ("config/gold_13f.yaml", "config/gold_event.yaml", "config/dm_drawdown.yaml")
APPENDIX_HEAD = "## For the AI-credit watch and SR-16: CDS levels and AI borrowing (Batch 15 item 76)"


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


def weekdays(start: str, n: int) -> list[str]:
    d, out = dt.date.fromisoformat(start), []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def put(rows: list, key: str, day: str, v, inst=None, src: str = "fixture") -> None:
    rows.append({"registry_key": key, "instrument": inst, "observed_at": day,
                 "available_at": f"{day}T22:00:00+00:00", "value": v, "source": src})


def store(name: str, rows: list):
    from altdata import observations
    db = TD / f"{name}.db"
    with observations.ObservationStore(str(db)) as st:
        st.write_many(rows)
    return str(db)


def raises(fn, exc) -> bool:
    try:
        fn()
    except exc:
        return True
    except Exception:                                           # noqa: BLE001
        return False
    return False


# ---------------------------------------------------------------------------
# A. The filing
# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A  THE FILING")
    p = REPO / ORDER
    check(p.exists() and _hash(p) == ORDER_SHA,
          "the Batch 15 order is on file at its SHA-256 (filed byte for byte)")
    # The index and the register's cell, read through the tool that writes them
    # (S1 part 3); --check holds the committed files to it.
    import change_orders_index as coi                           # noqa: PLC0415
    co = coi.index_text(REPO)
    i14 = co.find("change-order-signal-triage-batch-14-2026-10-20.md")
    i15 = co.find("change-order-signal-triage-batch-15-2026-10-23.md")
    check(0 <= i14 < i15, "docs/change-orders.md indexes it after Batch 14")
    check(not coi.run(REPO, write=False),
          "and the committed index and cell are what the tool writes")
    reg = coi.register_text(REPO)
    hdr = next((ln for ln in reg.splitlines() if ln.startswith("| Batch orders")), "")
    check("[15](change-order-signal-triage-batch-15-2026-10-23.md)" in hdr
          and "items 72–78" in hdr, "the register's header lists Batch 15 (items 72-78)")


# ---------------------------------------------------------------------------
# B. Item 72: the 13F line
# ---------------------------------------------------------------------------
SUB_H = "ACCESSION_NUMBER\tFILING_DATE\tSUBMISSIONTYPE\tCIK\tPERIODOFREPORT"
COV_H = "ACCESSION_NUMBER\tREPORTCALENDARORQUARTER\tISAMENDMENT\tAMENDMENTTYPE"
INF_H = ("ACCESSION_NUMBER\tINFOTABLE_SK\tNAMEOFISSUER\tCUSIP\tVALUE\tSSHPRNAMT\t"
         "SSHPRNAMTTYPE\tPUTCALL")


def mkzip(name: str, sub: list, cov: list, inf: list, inf_header: str = INF_H) -> Path:
    p = TD / name
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("SUBMISSION.tsv", "\n".join([SUB_H] + ["\t".join(r) for r in sub]) + "\n")
        z.writestr("COVERPAGE.tsv", "\n".join([COV_H] + ["\t".join(r) for r in cov]) + "\n")
        z.writestr("INFOTABLE.tsv", "\n".join([inf_header] + ["\t".join(r) for r in inf]) + "\n")
    return p


GLD, IAU, IAU_OLD = "78463V107", "464285204", "464285105"


def q2_zip() -> Path:
    s = lambda acc, filed, typ, cik, per="30-JUN-2026": [acc, filed, typ, cik, per]
    sub = [s("Z1", "01-JUL-2026", "13F-HR", "9"),
           s("A1", "20-JUL-2026", "13F-HR", "0001"),
           s("B1", "21-JUL-2026", "13F-HR", "2"),
           s("C1", "22-JUL-2026", "13F-HR", "3"),
           s("D1", "23-JUL-2026", "13F-HR", "4"),
           s("E1", "10-JUL-2026", "13F-HR", "5"),
           s("E2", "01-AUG-2026", "13F-HR/A", "5"),
           s("F1", "15-JUL-2026", "13F-HR", "6"),
           s("F2", "10-AUG-2026", "13F-HR/A", "6"),
           s("G1", "24-JUL-2026", "13F-NT", "7"),
           s("H1", "25-JUL-2026", "13F-HR", "8"),
           s("L1", "26-JUL-2026", "13F-HR", "11", "31-DEC-2025"),
           s("Z2", "14-AUG-2026", "13F-HR", "10")]
    cov = [[a, "30-JUN-2026", "N", ""] for a in ("Z1", "A1", "B1", "C1", "D1", "E1", "F1",
                                                  "G1", "H1", "L1", "Z2")]
    cov += [["E2", "30-JUN-2026", "Y", "RESTATEMENT"], ["F2", "30-JUN-2026", "Y", "NEW HOLDINGS"]]
    i = lambda acc, cusip, val, typ="SH", pc="": [acc, "1", "X", cusip, str(val), "10", typ, pc]
    inf = [i("A1", GLD, 1_000_000), i("B1", IAU, 2_000_000), i("C1", GLD, 3_000_000),
           i("C1", IAU_OLD, 500_000), i("D1", GLD, 9_000_000, pc="Call"),
           i("E1", GLD, 100), i("E2", GLD, 4_000_000), i("F1", GLD, 1_500_000),
           i("F2", IAU, 250_000), i("G1", GLD, 6_000_000), i("H1", GLD, 7_000_000, typ="PRN"),
           i("L1", GLD, 5_000_000), i("Z1", "037833100", 42)]
    return mkzip("q2.zip", sub, cov, inf)


def q1_zip() -> Path:
    sub = [["Q1A", "01-APR-2026", "13F-HR", "1", "31-MAR-2026"],
           ["Q1B", "15-MAY-2026", "13F-HR", "2", "31-MAR-2026"]]
    cov = [["Q1A", "31-MAR-2026", "N", ""], ["Q1B", "31-MAR-2026", "N", ""]]
    inf = [["Q1A", "1", "X", GLD, "800000", "10", "SH", ""],
           ["Q1B", "1", "X", IAU, "1000000", "10", "SH", ""]]
    return mkzip("q1.zip", sub, cov, inf)


def group_b() -> None:
    head("B  ITEM 72: THE 13F LINE")
    from altdata import gold_13f as g13
    cfg = g13.config()
    data = g13.merge([g13.read_zip(q2_zip(), cfg), g13.read_zip(q1_zip(), cfg)])
    c = g13.count(data, cfg)
    q2 = c["2026-06-30"]["funds"]
    # By hand: GLD -- A 1.0m, C 3.0m, E 4.0m (the RESTATEMENT replaces E's 100), F
    # 1.5m; D's call, H's principal amount and G's 13F-NT are out.
    check(q2["GLD"] == {"holders": 4, "value_usd": 9_500_000.0},
          f"GLD Q2: 4 filers, $9.5m by hand (got {q2['GLD']})")
    # IAU -- B 2.0m, C 0.5m on the earlier CUSIP, F 0.25m by its NEW HOLDINGS amendment.
    check(q2["IAU"] == {"holders": 3, "value_usd": 2_750_000.0},
          f"IAU Q2: 3 filers, $2.75m, the earlier CUSIP and the NEW HOLDINGS amendment "
          f"counted (got {q2['IAU']})")
    check(q2["BOTH"] == {"holders": 5, "value_usd": 12_250_000.0},
          "either fund: 5 filers (C and F once each), $12.25m")
    check(c["2026-06-30"]["complete"] and c["2026-03-31"]["complete"]
          and not c["2025-12-31"]["complete"],
          "Q2 and Q1 are complete in the files; the late Q4 2025 filer's quarter is partial")
    rows = g13.rows(c, cfg, "2026-10-23T12:00:00+00:00")
    check({r["observed_at"] for r in rows} == {"2026-03-31", "2026-06-30"}
          and len(rows) == 12,
          "rows are written for the complete quarters only (2 quarters x 3 funds x 2 keys)")
    # The thousands rule: a filing before 3 Jan 2023.
    old = mkzip("old.zip", [["O1", "10-NOV-2022", "13F-HR", "1", "30-SEP-2022"]],
                [["O1", "30-SEP-2022", "N", ""]], [["O1", "1", "X", GLD, "500", "10", "SH", ""]])
    check(g13.read_zip(old, cfg)["holdings"]["O1"]["GLD"][0] == 500_000.0,
          "VALUE 500 filed 10 Nov 2022 is $500,000 (thousands before 3 Jan 2023)")
    bad = mkzip("bad.zip", [], [], [], inf_header="ACCESSION_NUMBER\tCUSIP\tVALUE")
    check(raises(lambda: g13.read_zip(bad, cfg), g13.LayoutError),
          "a data set whose INFOTABLE lacks a column is refused, not half-read")
    from altdata import observations
    db = store("g13", rows)
    with observations.ObservationStore(db) as st:
        r = g13.read(st, "2026-10-23T23:00:00+00:00", cfg)
        sub = g13.subsection(st, "2026-10-23T23:00:00+00:00", cfg)
    f = r["funds"]["GLD"]
    check(r["quarter"] == "2026-06-30" and f["d_holders"] == 3
          and f["d_value_usd"] == 8_700_000.0 and f["prior_quarter"] == "2026-03-31",
          "the change from the prior quarter: GLD +3 filers, +$8.7m on Q1")
    txt = " ".join(sub["lines"])
    check("Q2 2026" in txt and "GLD 4 filers" in txt and "either fund 5 filers" in txt
          and "+3 filers" in txt and "a quarter old" in txt,
          "the line names the quarter, the counts, the change and the 13F caveat")
    check(any("World Gold Council" in x and "NOT TRACKED" in x for x in sub["not_tracked"]),
          "WGC's regional flows print as a listed gap beside it (check 1)")
    db0 = store("g13-empty", [])
    with observations.ObservationStore(db0) as st:
        e = g13.subsection(st, "2026-10-23T23:00:00+00:00", cfg)
    check(e["data"]["gold_13f"]["state"] == "absent"
          and "no quarter loaded" in e["lines"][0], "the absent path, with its reason")
    check(g13.zip_links('<a href="/files/x/2026q1_form13f.zip">a</a>'
                        '<a href="/files/x/2026q1_form13f.zip">b</a>')
          == ["https://www.sec.gov/files/x/2026q1_form13f.zip"],
          "the fetch's link reader takes each data-set zip once")
    src = (REPO / "altdata" / "gold_13f.py").read_text(encoding="utf-8")
    check("edgar.user_agent()" in src and "@" not in re.sub(r"#.*", "", src),
          "the fetch identifies itself through edgar.py's CHESTER_SEC_CONTACT, no literal address")


# ---------------------------------------------------------------------------
# C. Item 73: the gold event
# ---------------------------------------------------------------------------
GDAYS = weekdays("2019-01-01", 2000)


def gold_series(spike: dict) -> list[tuple[str, float]]:
    v, out = 2000.0, []
    for i, d in enumerate(GDAYS):
        v *= spike.get(d, 1.005 if i % 2 == 0 else 1 / 1.005)
        out.append((d, v))
    return out


def group_c() -> None:
    head("C  ITEM 73: THE GOLD EVENT")
    from altdata import asset_event as ae, gold_event as ge, observations
    cfg = ge.config()
    check(ae.threshold(list(range(1, 21)), 95.0) == 19 and ae.threshold([], 95.0) is None,
          "the nearest-rank 95th percentile of 1..20 is 19, by hand")
    five = GDAYS[1700:1705]          # five sessions of +1%
    one = GDAYS[1800]                # one session of +3%
    spike = {d: 1.01 for d in five}
    spike[one] = 1.03
    gold = gold_series(spike)
    tr = ge.trigger(gold, five[-1], cfg)
    want = round(math.log(1.005) * 100, 2)
    check(tr["fired"] and tr["five_day_fired"] and not tr["one_day_fired"]
          and tr["five_day_threshold"] == want and tr["horizon"] == 5,
          f"the five-day arm: +1% five times is beyond the 95th percentile of the "
          f"alternating history, {want}% by hand (got {tr.get('five_day_threshold')})")
    check(tr["five_day_n"] > 1200 and not tr["five_day_short"],
          "its window is the five years before the day (a57's flag window)")
    tr1 = ge.trigger(gold, one, cfg)
    check(tr1["fired"] and tr1["one_day_fired"] and tr1["one_day_pct"] == 3.0
          and tr1["horizon"] == 1, "the one-day arm: +3.00% on the day, horizon one session")
    quiet = ge.trigger(gold, GDAYS[1600], cfg)
    check(not quiet["fired"], "a quiet day does not fire")
    short = ge.trigger(gold[:100], GDAYS[99], cfg)
    check(short["five_day_state"] == "not read" and "history short" in short["five_day_reason"],
          "with under a year of five-day changes the five-day arm is not read, and says so")
    prev = GDAYS[1799]
    rows: list = []
    for d, v in gold:
        put(rows, "yfinance.mkt_gold_front", d, v)
    put(rows, "fred.tips_10y", prev, 1.80)
    put(rows, "fred.tips_10y", one, 1.95)
    put(rows, "yfinance.mkt_dxy", prev, 100.0)
    put(rows, "yfinance.mkt_dxy", one, 99.0)
    put(rows, "fred.brent", prev, 80.0)              # not on the day: awaiting
    months = [f"{y}-{m:02d}-01" for y in (2023, 2024) for m in range(1, 13)]
    for i, mth in enumerate(months):
        put(rows, "imf.ifs.gold_net_purchases_oz.total", mth, 50_000.0 if i < 12 else 100_000.0)
    db = store("gold", rows)
    with observations.ObservationStore(db) as st:
        ev = ge.for_session(st, one, "2030-01-01T00:00:00+00:00", cfg)
    legs = {x["id"]: x for x in ev["attribution"]["legs"]}
    check(legs["real_10y"]["state"] == "computed" and legs["real_10y"]["change"] == 15.0,
          "the real 10-year leg: 1.80% to 1.95% is +15 bp, by hand")
    check(legs["dxy"]["change"] == -1.0, "DXY: 100 to 99 is -1.00%")
    check(legs["brent"]["state"] == "awaiting" and legs["brent"]["stored_through"] == prev,
          "Brent not stored on the day is awaiting, with how far it is stored")
    check(legs["etf_flows"]["state"] == "not tracked"
          and "WGC" in legs["etf_flows"]["reason"],
          "gold-ETF flows are not tracked (item 72's WGC line failed check 1)")
    cb = legs["central_banks"]
    check(cb["state"] == "computed" and cb["direction"] == "rising"
          and cb["last_t"] == round(1_200_000 / 32150.7466, 1)
          and cb["prior_t"] == round(600_000 / 32150.7466, 1),
          "the central-bank trend (IMF IFS): 12 months against 12, in tonnes, by hand")
    check(ev["attribution"]["residual"].startswith("Residual: 1 of 2 read legs")
          and "(DXY)" in ev["attribution"]["residual"],
          "the residual: of the two read legs only the dollar moved the mechanism's way")
    check(ev["state"] == "awaiting" and ev["line"].startswith("Gold event: +3.00% on the day"),
          "the event is awaiting while a market leg is; its line names the arm")
    cb_short = ge.central_bank_trend([(m, 1.0) for m in months[:10]], one, cfg)
    check(cb_short["state"] == "absent" and "fewer than 24" in cb_short["reason"],
          "the central-bank trend is absent on short history, with its reason")
    row = ge.ledger_row(ev, gold, "2030-01-01T00:00:00+00:00", cfg)
    b = json.loads(row["value"])
    f5 = round((gold[1805][1] / gold[1800][1] - 1) * 100, 2)
    check(row["registry_key"] == "gold.event_ledger" and row["instrument"] == one
          and b["outcomes"]["gold_5d_pct"] == f5,
          f"the ledger row, with gold's realised 5-session change by hand ({f5}%)")
    put(rows, "fred.brent", one, 84.0)
    db2 = store("gold2", rows)
    with observations.ObservationStore(db2) as st:
        series = ge.read_series(st, "2030-01-01T00:00:00+00:00", cfg)
    rs = ge.resolve_rows({one: b}, series, cfg, "2030-01-02T00:00:00+00:00")
    nb = json.loads(rs[0]["value"]) if rs else {}
    nl = {x["id"]: x for x in nb.get("legs") or []}
    check(len(rs) == 1 and nl["brent"]["change"] == 5.0 and nb["state"] == "computed",
          "resolve writes a new vintage once Brent lands (+5.00%), the event now computed")
    hist = ge.history({"gold": gold_series({GDAYS[300]: 1.03})[:400],
                       "central_banks": []}, cfg)
    check(hist and all(h.get("history_note") for h in hist),
          "the history pass on a short store says so on every row")


# ---------------------------------------------------------------------------
# D. Item 73: the DM drawdown screen
# ---------------------------------------------------------------------------
def group_d() -> None:
    head("D  ITEM 73: THE DM DRAWDOWN SCREEN")
    from altdata import dm_drawdown as dm, observations
    cfg = dm.config()
    days = GDAYS[:1600]
    v, nk = 60000.0, []
    for i, d in enumerate(days):
        v *= 0.98 if i >= 1594 else (1.005 if i % 2 == 0 else 1 / 1.005)
        nk.append((d, v))
    day = days[1599]
    tr = dm.trigger(nk, day, cfg)
    w20 = tr["windows"][20]
    # By hand: the day's close against the highest close of the 20 sessions
    # before it and the day (an alternating high, then six falls of 2%).
    want_dd = round((1 - nk[1599][1] / max(x for _, x in nk[1579:1600])) * 100, 4)
    want_q = round((1 - 1 / 1.005) * 100, 2)
    check(tr["fired"] and tr["lead"] == 20 and abs(w20["drawdown_pct"] - want_dd) < 0.01
          and w20["threshold_pct"] == want_q,
          f"six falls of 2% after an alternating high: a {want_dd:.2f}% drawdown from the 20-session high, beyond "
          f"the 95th percentile of {want_q}% by hand")
    check(tr["windows"][10]["fired"], "the 10-session window fires too; the lead is the longer")
    check(not dm.trigger(nk, days[1500], cfg)["fired"], "a quiet day does not fire")
    rows: list = []
    for d, x in nk:
        put(rows, "fred.nikkei225", d, x)
    start = days[1599 - 20]
    put(rows, "yfinance.mkt_usdjpy", start, 150.0)
    put(rows, "yfinance.mkt_usdjpy", day, 147.0)
    put(rows, "mof.jgb_10y", start, 1.50)
    put(rows, "mof.jgb_10y", day, 1.62)
    put(rows, "mof.jgb_30y", start, 3.00)
    put(rows, "mof.jgb_30y", day, 3.25)
    put(rows, "calc.jpy_unwind", day, 1.0)
    put(rows, "yfinance.mkt_gspc", days[1597], 6000.0)
    put(rows, "yfinance.mkt_gspc", days[1598], 5880.0)
    for d, x in nk[-100:]:
        put(rows, "yfinance.mkt_ewy", d, x / 1000.0)
    db = store("dm", rows)
    with observations.ObservationStore(db) as st:
        ev = dm.for_session(st, day, "2030-01-01T00:00:00+00:00", cfg)
    e = next(x for x in ev["events"] if x["id"] == "nikkei225")
    t = dict((r[0], r[1]) for r in e["attribution"]["table"]["rows"])
    check(t["USD/JPY"] == "-2.00%" and t["JGB 10-year (MoF)"] == "+12 bp",
          "Nikkei's legs by hand: USD/JPY -2.00%, the JGB 10-year +12 bp")
    check(t[f"{cfg['us_session']['label']} ({days[1598]})"] == "-2.00%",
          "the prior US session's move: 6,000 to 5,880 is -2.00%")
    check(t["yen unwind flag (SR-2)"].startswith("on")
          and t["30-year JGB (SR-32's early line; the family is a stub)"] == "+25 bp"
          and "absent" in t["hedged Japanese carry on Treasuries (SR-2)"],
          "Japan: the carry stack's stored flag, SR-32's early line +25 bp, a carry series not stored absent")
    check(all(x["id"] != "kospi" for x in ev["events"])
          and dm.trigger([(d, x) for d, x in nk[-100:]], day, cfg)["windows"][20]["state"]
          == "not read", "KOSPI's 100 stored sessions: not read, history short")
    gaps = " ".join(ev["gaps"])
    check(all(n in gaps for n in ("TOPIX", "DAX", "CAC 40", "FTSE 100"))
          and gaps.count("NOT TRACKED") == 4, "each missing index is a listed gap, by name")
    ids = {m["id"]: m for m in cfg["indices"]}
    check(ids["kospi"]["source_label"] == "ETF proxy: EWY"
          and ids["taiex"]["source_label"] == "ETF proxy: EWT"
          and ids["nikkei225"]["source_label"] == "FRED NIKKEI225",
          "Nikkei 225 is FRED's; KOSPI and TAIEX are labelled ETF proxy")
    check(all("not tracked" in ids[k]["local_10y_gap"] for k in ("kospi", "taiex"))
          and ids["kospi"]["capex_chain"] and ids["taiex"]["capex_chain"],
          "KOSPI's and TAIEX's 10-years are not tracked at a session horizon; both read item 63's line")
    rws = dm.ledger_rows(ev, {"nikkei225": nk}, "2030-01-01T00:00:00+00:00", cfg)
    check(len(rws) == 1 and rws[0]["instrument"] == f"nikkei225:{day}"
          and rws[0]["registry_key"] == "equity.dm_drawdown_ledger",
          "one ledger row per fired index and day")
    blk = dm.block(ev)
    check(blk and blk["table"]["columns"] == ["Index", "Leg", "Change"]
          and len(blk["not_tracked"]) == 4, "the block carries the table and the four gaps")


# ---------------------------------------------------------------------------
# E. Item 76: the whole-item gap
# ---------------------------------------------------------------------------
def group_e() -> None:
    head("E  ITEM 76: A LISTED GAP AND THE DATED RECORDS")
    from daily_cascade import absorption_block as ab
    import yaml
    line = ab.AI_CREDIT_LINE
    check(line.startswith("AI credit (the CDS and bond spreads of CoreWeave, Oracle and")
          and "Item 76's protection-demand line is a listed gap" in line
          and "dated records" in line,
          "a57's AI-credit gap line now points at item 76's gap and the dated records")
    cfg = yaml.safe_load((REPO / "config" / "ai_trade.yaml").read_text(encoding="utf-8"))
    check(" ".join(cfg["credit_watch_gap"].split()).startswith(line[:60]),
          "config/ai_trade.yaml carries the same amended line")
    reg = (REPO / "metrics_registry.yaml").read_text(encoding="utf-8")
    src = (REPO / "source_registry.yaml").read_text(encoding="utf-8")
    check(not re.search(r"^\s+dtcc[._]", reg, re.M) and "\n  dtcc" not in src
          and not (REPO / "altdata" / "cds_protection.py").exists(),
          "no protection-demand line, flag or DTCC key is built (check 4 failed)")
    q = (REPO / "docs" / "dated-appendix-queue.md").read_text(encoding="utf-8")
    sec = q[q.find(APPENDIX_HEAD):] if APPENDIX_HEAD in q else ""
    check(bool(sec) and "$1.09m" in sec and "$322k" in sec and "$226k" in sec
          and "$108k" in sec and "$101k" in sec and "Source line:" in sec
          and "As of: mid-October 2026" in sec,
          "the CDS levels are a dated record with a source line and an as-of date")
    check("$466bn" in sec and "$101bn" in sec and "As of: 20 Oct 2026" in sec,
          "the $466bn AI borrowing figure is a dated record (SR-16)")
    check("listed gap" in sec[:900], "the monthly rows are said to be a listed gap")


# ---------------------------------------------------------------------------
# F. Placement
# ---------------------------------------------------------------------------
def group_f() -> None:
    head("F  PLACEMENT")
    from altdata import observations
    from daily_cascade import batch15_a_block as blk, t1_rest_block
    rows: list = []
    gold = gold_series({GDAYS[1800]: 1.03})
    for d, v in gold:
        put(rows, "yfinance.mkt_gold_front", d, v)
    db = store("place", rows)
    cut = "2030-01-01T00:00:00+00:00"
    built = {"mechanics": {"subsections": [{"title": "Volatility event"}, {"title": "Other"}],
                           "items": [], "data": {}}}
    with observations.ObservationStore(db) as st:
        blk.close_extras(built, st, GDAYS[1800], cut)
        subs = built["mechanics"]["subsections"]
        check(subs[1]["title"] == "Gold and developed-market events"
              and "table" not in subs[1] and subs[1]["lines"][0].startswith("Gold event"),
              "the close: the flag line only, right after item 52's event")
        out = blk.store_rows(built["mechanics"]["data"], st, cut)
        check(len(out) == 1 and out[0]["registry_key"] == "gold.event_ledger"
              and "_gold_event" not in built["mechanics"]["data"],
              "the close's ledger row, taken out of the section's data")
        quiet = {"mechanics": {"subsections": [], "items": [], "data": {}}}
        blk.close_extras(quiet, st, GDAYS[1600], cut)
        check(quiet["mechanics"]["subsections"] == [], "a quiet session prints nothing")
        wk = blk.mechanics_subsections([{"title": "A"}], st, cut, GDAYS[1798], GDAYS[1802])
        g = next(x for x in wk if x["title"] == blk.GOLD_TITLE)
        check(g["table"]["rows"][0][0] == GDAYS[1800] and wk[0]["title"] == "A",
              "the Weekly's and the Monthly's gold block lists the period's event")
        dmb = next(x for x in wk if x["title"] == blk.DM_TITLE)
        check("No developed-market drawdown" in dmb["lines"][0]
              and len(dmb["not_tracked"]) == 4, "the DM block's quiet line, with the gaps")
        sl = blk.place_slow([{"title": t1_rest_block.GOLD_TITLE}, {"title": "Next"}], st, cut)
        check(sl[1]["title"] == "Institutional gold-ETF ownership (13F)",
              "item 72 prints right after item 38's gold/equity ratio")
    sc = (REPO / "daily_cascade" / "stack_close.py").read_text(encoding="utf-8")
    check("batch15_a_block.store_rows" in sc and "if _ae_rows and not dry_run" in sc,
          "the close stores the rows only off a dry run")
    ws = (REPO / "daily_cascade" / "weekly_stack.py").read_text(encoding="utf-8")
    ms = (REPO / "monthly_macro" / "stack.py").read_text(encoding="utf-8")
    cs = (REPO / "daily_cascade" / "stack.py").read_text(encoding="utf-8")
    check("batch15_a_block.mechanics_subsections" in ws
          and "batch15_a_block.mechanics_subsections" in ms
          and "batch15_a_block.place_slow" in ms and "batch15_a_block.close_extras" in cs,
          "the hooks: the close, the Weekly's and the Monthly's Mechanics, the Monthly's slow layers")
    eod = (REPO / "scripts" / "run_eod_cron.sh").read_text(encoding="utf-8")
    check("for AE in gold_event dm_drawdown" in eod and "WARN $AE resolve" in eod,
          "the EOD pass resolves both ledgers, warn-only")


# ---------------------------------------------------------------------------
# G. Registration
# ---------------------------------------------------------------------------
def group_g() -> None:
    head("G  REGISTRATION")
    import yaml
    from altdata import config
    from register import instruments
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    keys = ("gold.event_ledger", "equity.dm_drawdown_ledger", "sec13f.gold_etf_holders",
            "sec13f.gold_etf_value_usd")
    check(all(k in reg["metrics"] and k in reg["families"] for k in keys),
          "the four new keys are registered, each with its family")
    blk = reg["bulk_imports"].get("fred_batch15_a") or {}
    check(blk.get("members_from") == "altdata.config.FRED_BATCH15_A_SERIES"
          and blk.get("expected_members") == 1, "the FRED block for NIKKEI225")
    check(any(s.fred_id == "NIKKEI225" and s.key == "nikkei225"
              for s in config.FRED_PULL_SERIES), "NIKKEI225 is in the FRED pull")
    src = yaml.safe_load((REPO / "source_registry.yaml").read_text(encoding="utf-8"))["sources"]
    check(all(s in src for s in ("gold_event", "dm_drawdown", "sec_13f")),
          "the three source ids are registered")
    cmds = yaml.safe_load((REPO / "config" / "catalogue_commands.yaml").read_text(
        encoding="utf-8"))["commands"]
    check(all(c in cmds for c in ("altdata.gold_13f", "altdata.gold_event",
                                  "altdata.dm_drawdown")), "the three commands are catalogued")
    r = instruments.restrictions()
    names = ["GLD", "IAU", "EWY", "EWT", "NIKKEI225", "SPDR Gold Shares", "iShares Gold Trust"]
    check(not any(r.is_restricted(n) for n in names),
          "no Brookfield instrument among the funds, indices and proxies")


# ---------------------------------------------------------------------------
# H. Hygiene
# ---------------------------------------------------------------------------
PEOPLE = ("Dalio", "Marino", "Prehn", "Curzio", "Gadala", "Muur", "Radge", "Wanjun",
          "Chester", "Bessent")


def group_h() -> None:
    head("H  HYGIENE")
    texts = {p: (REPO / p).read_text(encoding="utf-8") for p in NEW_MODULES + NEW_CONFIG}
    q = (REPO / "docs" / "dated-appendix-queue.md").read_text(encoding="utf-8")
    texts["appendix"] = q[q.find(APPENDIX_HEAD):]
    hits = [f"{p}: {n}" for p, t in texts.items() for n in PEOPLE if n in t]
    hits += [f"{p}: \\bAri\\b" for p, t in texts.items() if re.search(r"\bAri\b", t)]
    check(not hits, f"no person's name in the new files or the appendix records ({hits})")
    mails = [p for p, t in texts.items()
             if re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", t) or re.search(r"(?<![\w$])@\w", t)]
    check(not mails, f"no email address or handle ({mails})")
    bad = []
    for p in NEW_MODULES:
        for node in ast.walk(ast.parse(texts[p])):
            names = ([a.name for a in node.names] if isinstance(node, ast.Import) else
                     [node.module or ""] + [a.name for a in node.names]
                     if isinstance(node, ast.ImportFrom) else [])
            bad += [f"{p}: {n}" for n in names
                    if re.search(r"regime|market_state|composite|register|order|ibkr|broker", n)]
    check(not bad, f"no composite, market-state, register or order import ({bad})")
    check(_hash(LIVE_DB) == LIVE_AT_START, "the live store is untouched by the gate")


def main() -> int:
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g, group_h):
        try:
            g()
        except Exception as exc:                                # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{LINE}\nvalidate_batch15_1: {PASS} passed, {FAIL} failed\n{LINE}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
