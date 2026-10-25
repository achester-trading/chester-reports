"""
Signal triage Batch 15, session B (b56): items 74, 75, 77 and 78.

  A  ITEM 74, THE TFF LINE. ES (13874A) and NQ (209742) join the TFF pull; a
     fixture record's leveraged-fund net and its share of open interest by hand;
     the net short share's dual percentiles by hand (five years and the full
     history, each with its n); an unstored contract prints its reason.
  B  THE GAP PATHS AND QAI. FINRA's share of float prints as a listed gap; the
     prime-book figures never print as a line. Hedge-fund performance through
     QAI (ruling D22, 24 Oct 2026): unstored it prints its reason; on a fixture,
     the week's and four weeks' return and their dual percentiles by hand.
  C  THE SQUEEZE FLAG. On, off and not read on fixtures (ES's net short at or
     above its 90th with the Amihud stand-in at or above its 90th); its line in
     item 45's levels read and the Weekly's Positioning; report only.
  D  THE LEDGER (ST-R6.74b). The pre-registration's SHA-256; the rule's
     INSUFFICIENT, PASS and FAIL on fixtures; entry after the release; the first
     edition as written; the script opens its store read-only.
  E  ITEM 75, THE LAB LEDGER. The ratios by hand from a fixture row; "no ledger
     entry"; the template's disclosure and G3 status; the first row provisional
     with its URL; the mega-IPO watch "not yet public"; the Factor I hook.
  F  ITEM 77, CYBER PRESSURE. KEV's weekly counts by hand from a fixture
     catalogue (its seeding week left out of the percentiles); NVD's weekly
     counts through a fake fetch, paced; the joint flag on, off and not read;
     the Weekly's Ahead and the addendum's incidents section (its body, b60) carry it.
  G  ITEM 78, PROTOCOL BREADTH. The active and listed counts by hand; the dry
     run; the line's history-start label; the Monthly chapter's sub-section and
     the hand count's listed gap.
  H  THE NOTES AND RECORDS. The crypto-winters note cites a title and a URL per
     claim; the dated records (74's prime-book figures, 75's provisional S-1).
  I  HYGIENE. Every new key registered with its family and source; the rosters
     and run steps; no store write from this gate, no composite, market-state,
     register or vendor import in the new modules; no person's name, handle or
     email in the new code, config, ledgers, notes or appendix lines.

Synthetic fixtures only: no live store, no network, no model.

    python tools/validate_batch15_2.py
"""

from __future__ import annotations

import datetime as dt
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import gate_tmp  # noqa: E402

from altdata import ai_lab_ledger as al  # noqa: E402
from altdata import cyber_pressure as cp  # noqa: E402
from altdata import derived, observations  # noqa: E402
from altdata import hf_positioning as hf  # noqa: E402
from altdata import protocol_breadth as pb  # noqa: E402
from altdata import st_r5_rates as rt  # noqa: E402

PASS = FAIL = 0
LINE = "=" * 78
NOW = "2026-10-24T23:00:00+00:00"
NEW_CODE = [REPO / "altdata" / f for f in ("hf_positioning.py", "ai_lab_ledger.py",
                                          "cyber_pressure.py", "protocol_breadth.py")] + \
    [REPO / "daily_cascade" / "batch15_b2_block.py",
     REPO / "tools" / "calibration" / "st_r6_74b_short_extremes.py"]
NEW_CONFIG = [REPO / "config" / f for f in ("hf_positioning.yaml", "ai_lab_ledger.yaml",
                                           "cyber_pressure.yaml")]
NOTE = REPO / "docs" / "base-rate-notes" / "crypto-winters-protocol-shutdowns-2026-10.md"
LAB = REPO / "docs" / "ledgers" / "ai-lab-financials-ledger.md"
EDITION = REPO / "docs" / "ledgers" / "st-r6.74b-ledger-2026-10-23.md"


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


def store(rows: list[dict]) -> str:
    db = str(Path(gate_tmp.mkdtemp("b15b2_")) / "obs.db")
    with observations.ObservationStore(db) as st:
        st.write_many(rows)
    return db


def obs(key, day, v, inst=None, src="fixture"):
    return {"registry_key": key, "instrument": inst, "observed_at": day,
            "available_at": day + "T21:00:00+00:00", "value": v, "source": src}


def tuesdays(n: int, start=dt.date(2006, 6, 13)) -> list[str]:
    return [(start + dt.timedelta(days=7 * i)).isoformat() for i in range(n)]


# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. ITEM 74, THE TFF LINE")
    from altdata.sources import cftc
    check(cftc.TFF_CONTRACTS.get("13874A") == "ES" and cftc.TFF_CONTRACTS.get("209742") == "NQ",
          "ES (13874A) and NQ (209742) join the TFF pull, by their CME tickers")
    rec = {"cftc_contract_market_code": "13874A", "report_date_as_yyyy_mm_dd":
           "2026-10-20T00:00:00.000", "open_interest_all": "2000000",
           "lev_money_positions_long": "300000", "lev_money_positions_short": "700000",
           "dealer_positions_long_all": "1", "dealer_positions_short_all": "1"}
    v = {r["registry_key"]: r for r in cftc.category_rows([rec], "tff", cftc.TFF_CONTRACTS,
                                                          cftc.TFF_CATEGORIES)}
    net = v["cftc.tff_lev_money_net"]
    check(net["instrument"] == "ES" and net["value"] == 300000 - 700000
          and v["cftc.tff_lev_money_net_oi"]["value"] == round(100 * -400000 / 2000000, 6)
          and net["available_at"].startswith("2026-10-23T19:30"),
          "a fixture record: net 300,000 - 700,000 = -400,000 contracts, -20.0% of open "
          "interest, available the Friday 15:30 ET")
    # Net short share series: 300 weeks, the last the largest short of five years.
    wk = tuesdays(300)
    oi = [-(5.0 + (i % 10)) for i in range(299)] + [-20.0]
    rows = [obs("cftc.tff_lev_money_net_oi", d, x, "ES") for d, x in zip(wk, oi)]
    rows += [obs("cftc.tff_lev_money_net", d, x * 1000, "ES") for d, x in zip(wk, oi)]
    db = store(rows)
    with observations.ObservationStore(db) as st:
        r = hf.read(st, NOW)
    es = next(c for c in r["contracts"] if c["instrument"] == "ES")
    short = [-x for x in oi]
    start = rt._years_back(wk[-1], 5)                           # noqa: SLF001
    win = [s for d, s in zip(wk, short) if d > start]
    check(es["state"] == "computed" and es["short_oi_pct"] == 20.0
          and es["lens"]["percentile_window"] == derived.percentile_of(win, 20.0) == 100.0
          and es["lens"]["n_window"] == len(win) and es["lens"]["n_full"] == 300
          and es["net"] == -20000.0,
          f"ES's net short share 20.0% is the 100th percentile of five years (n="
          f"{len(win)}) and of the stored history (n=300), by hand")
    nq = next(c for c in r["contracts"] if c["instrument"] == "NQ")
    check(nq["state"] == "absent" and "not stored" in hf.contract_line(nq),
          "NQ, unstored, prints its reason")
    t = hf.table(r)
    check(t["rows"][0][2] == "-20.0%" and "100th of 5 years" in t["rows"][0][3],
          "the table's row: the share and the dual percentile")


def group_b() -> None:
    head("B. THE GAP PATHS")
    r = hf.read(_EmptyStore(), NOW)
    ls = hf.lines(r)
    check(any(l.startswith("FINRA short interest as a share of float for the S&P 500: "
                           "NOT TRACKED") for l in ls)
          and not any("performance proxy: NOT TRACKED" in l for l in ls),
          "FINRA's share of float prints as a listed gap; the performance gap is gone (D22)")
    check(any(l.startswith("Hedge-fund performance (QAI, replication proxy): not stored yet")
              for l in ls),
          "QAI unstored: the performance line prints its reason")
    # QAI: 1,600 sessions, a gentle drift, the last session a 3% jump.
    days = [(dt.date(2020, 1, 1) + dt.timedelta(days=i)).isoformat() for i in range(1600)]
    px = [100.0 * (1 + 0.0002 * i + 0.002 * ((i % 7) - 3)) for i in range(1599)]
    px.append(px[-1] * 1.03)
    with observations.ObservationStore(store([obs("yfinance.mkt_qai", d, p)
                                              for d, p in zip(days, px)])) as st:
        rq = hf.read(st, NOW)
    p = rq["performance"]
    closes = list(zip(days, px))
    wk = [(closes[i][0], (closes[i][1] / closes[i - 5][1] - 1) * 100) for i in range(5, 1600)]
    fw = [(closes[i][0], (closes[i][1] / closes[i - 20][1] - 1) * 100) for i in range(20, 1600)]
    start = rt._years_back(days[-1], 5)                         # noqa: SLF001
    w5 = [v for d, v in wk if d > start]
    check(p["state"] == "computed" and abs(p["legs"]["week"]["pct"] - wk[-1][1]) < 1e-9
          and abs(p["legs"]["four_weeks"]["pct"] - fw[-1][1]) < 1e-9
          and p["legs"]["week"]["lens"]["percentile_window"] == derived.percentile_of(w5, wk[-1][1])
          and p["legs"]["week"]["lens"]["n_full"] == len(wk)
          and p["legs"]["four_weeks"]["lens"]["n_full"] == len(fw),
          f"QAI: the week {wk[-1][1]:+.2f}% and four weeks {fw[-1][1]:+.2f}%, each ranked "
          f"against every rolling return of its length (five years and n={len(wk):,} full), by hand")
    pl = hf.performance_line(p)
    check(pl.startswith("Hedge-fund performance (QAI, replication proxy): the week +")
          and "four weeks" in pl and pl.endswith("Report only.")
          and pl in hf.lines(rq),
          "the line is labelled a replication proxy, report only, beside the CFTC line")
    joined = " ".join(ls)
    check("five to one" not in joined and "prime" not in joined.lower()
          and "99th" not in joined,
          "the prime-book figures never print as a line (a dated record only, G3)")


class _EmptyStore:
    path = None

    def as_of(self, *a, **k):
        return []

    def instruments(self, *a, **k):
        return []


def _r(pct_short):
    lz = {"percentile_window": pct_short, "percentile_full": pct_short, "n_window": 260,
          "n_full": 900, "from": "2006-06-13", "same": False, "years": 5}
    return {"years": 5, "squeeze_cfg": {"arm_instrument": "ES", "net_short_pct": 90,
                                        "depth_pct": 10},
            "contracts": [{"instrument": "ES", "state": "computed", "lens": lz}]}


def _depth(p):
    return {"amihud": {"state": "computed", "lens": {"percentile_window": p}}}


def group_c() -> None:
    head("C. THE SQUEEZE FLAG")
    on = hf.squeeze(_r(93.0), _depth(95.0))
    off1 = hf.squeeze(_r(85.0), _depth(95.0))
    off2 = hf.squeeze(_r(93.0), _depth(50.0))
    nr = hf.squeeze(_r(93.0), None)
    edge = hf.squeeze(_r(90.0), _depth(90.0))
    check(on["state"] == "on" and off1["state"] == "off" and off2["state"] == "off"
          and nr["state"] == "not read" and edge["state"] == "on",
          "on at a 93rd-percentile net short with the Amihud stand-in at its 95th (depth "
          "below its 10th); off with either arm short; not read without the depth read; "
          "on at exactly 90/90")
    check(on["line"].startswith("The squeeze-risk flag is ON") and "Report only" in on["line"]
          and "Amihud" in on["line"] and hf.es_line(on).startswith("Squeeze risk: "),
          "its line names the stand-in and says report only; the levels-read line")
    sc = (REPO / "daily_cascade" / "stack_close.py").read_text(encoding="utf-8")
    ws = (REPO / "daily_cascade" / "weekly_stack.py").read_text(encoding="utf-8")
    check("batch15_b2_block.es_squeeze_line(_sst, sess, cutoff)" in sc
          and sc.index("es_squeeze_line") > sc.index("batch14_b1_block.levels_line"),
          "item 45's levels read carries it, after item 71's fragility line")
    check("batch15_b2_block.positioning_subsection(st, now)" in ws,
          "the Weekly's Positioning & flows carries the line's block")


def group_d() -> None:
    head("D. THE LEDGER (ST-R6.74b)")
    check(hf.prereg_sha256() == hf.PREREG_SHA256
          == "584442322783b3cf85ca6bb16c4a08b705ec36c8360f8323dcb4233273f90211",
          "the pre-registration's SHA-256 over its LF bytes is the registered one")

    def fixture(n_weeks: int, steps: bool):
        wk = tuesdays(n_weeks)
        oi = []
        for i in range(n_weeks):
            oi.append(-30.0 if i % 8 == 0 else -(10.0 + (i % 7) * 0.1))
        days = []
        d0 = dt.date(2006, 6, 1)
        last = dt.date.fromisoformat(wk[-1]) + dt.timedelta(days=60)
        while d0 <= last:
            days.append(d0.isoformat())
            d0 += dt.timedelta(days=1)
        px = [100.0] * len(days)
        ev = hf.episodes(list(zip(wk, oi)), list(zip(days, px)))
        if steps:
            import bisect
            for e in ev["episodes"]:
                k = bisect.bisect_left(days, e["release"])
                for j in range(k + 1, len(px)):
                    px[j] += 5.0
        return list(zip(wk, oi)), list(zip(days, px))

    net, spx = fixture(400, True)
    res = hf.ledger(net, spx)
    r = res["result"]
    e0 = res["episodes"][0]
    check(e0["entry"] == e0["release"] == hf.release_day(e0["week"])
          and dt.date.fromisoformat(e0["release"]).weekday() == 4,
          f"entry is the first close on or after the Friday release ({e0['week']} -> "
          f"{e0['entry']})")
    check(all(res["ranked"][i]["week"] >= tuesdays(400)[155] for i in range(len(res["ranked"])))
          and len(res["ranked"]) == 400 - 155,
          "only weeks with 156 reports behind them are ranked")
    check(r["verdict"] == "PASS" and r["n"] >= 12 and r["share_positive"] == 1.0
          and r["lift_pp"] >= 1.0,
          f"PASS on a fixture where every episode is followed by a rise: n {r['n']}, "
          f"lift {r.get('lift_pp')} pp, all positive")
    net2, spx2 = fixture(400, False)
    r2 = hf.ledger(net2, spx2)["result"]
    check(r2["verdict"] == "FAIL" and r2["n"] >= 12 and r2.get("lift_pp") == 0.0,
          f"FAIL on the same weeks with a flat index (lift {r2.get('lift_pp')} pp)")
    net3, spx3 = fixture(200, True)
    r3 = hf.ledger(net3, spx3)["result"]
    check(r3["verdict"] == "INSUFFICIENT" and r3["n"] < 12,
          f"INSUFFICIENT under 12 episodes (n {r3['n']})")
    quiet = [e for e in res["ranked"] if e["extreme"] and e not in res["episodes"]]
    check(not quiet, "every extreme week here opens an episode (seven quiet weeks between)")
    ed = EDITION.read_text(encoding="utf-8")
    check("| Verdict | **INSUFFICIENT" in ed and hf.PREREG_SHA256 in ed and "| n | 0 (" in ed
          and "rule-31 draft" in ed,
          "the first edition: INSUFFICIENT, n 0 (the laptop store holds no ES rows yet), "
          "with the pre-registration's hash, a rule-31 draft")
    src = (REPO / "tools" / "calibration" / "st_r6_74b_short_extremes.py").read_text(encoding="utf-8")
    check("mode=ro" in src and "http" not in src.split('"""', 2)[2],
          "the script reads its store read-only and fetches nothing")


def group_e() -> None:
    head("E. ITEM 75, THE LAB LEDGER")
    fx = """## Entries

| Lab | Period | Period end | Reported | Status | Revenue ($bn) | Revenue a year earlier ($bn) | Compute and infrastructure ($bn) | Net loss ($bn) | Non-cash financing charges ($bn) | Forward commitments ($bn) | TTM revenue ($bn) | Top-two customers (% of revenue) | Source | URL |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Lab A | Q1 2026 | 2026-03-31 | 2026-05-01 | filed | 10 | 4 | 6 | 12 | 5 | 300 | 30 | 25 | fixture | https://example.org/a |
| Lab A | Q4 2025 | 2025-12-31 | 2026-02-01 | filed | 8 | 3 | 5 | 10 | 4 | 280 | 25 | 30 | fixture | https://example.org/b |
| Lab B | Q1 2026 | 2026-03-31 | 2026-05-02 | filed | 1 | | | | | | | | fixture | no url |
"""
    rows = al.parse(fx)
    check(len(rows) == 2 and rows[0]["revenue"] == 10.0,
          "two rows parsed; the row without a URL is refused")
    m = al.measures(al.latest(rows))
    check(m == {"growth_pct": 150.0, "compute_share_pct": 60.0, "burn_ex_noncash_bn": 7.0,
                "commitments_over_ttm": 10.0, "top_two_pct": 25.0},
          "the latest row's ratios by hand: 10/4-1 = +150%; 6/10 = 60%; 12-5 = 7bn; "
          "300/30 = 10.0x; 25%")
    ue, s16 = al.unit_economics_line(rows), al.sr16_line(rows)
    check("+150% on the year" in ue and "60% of revenue" in ue and "$7.0bn" in ue
          and "10.0x TTM revenue" in s16,
          "item 47's line and SR-16's entry print them")
    check(al.unit_economics_line([]).endswith("no ledger entry.")
          and al.sr16_line([]).endswith("no ledger entry."),
          "\"no ledger entry\" otherwise")
    real = al.load()
    t = LAB.read_text(encoding="utf-8")
    check(len(real) == 1 and real[0]["status"] == "provisional"
          and real[0]["url"].startswith("https://") and real[0]["ttm_revenue"] is None,
          "the first row: provisional, cited, TTM revenue not in the entry")
    check("not computed (TTM revenue not in the entry)" in al.sr16_line(real),
          "so commitments over TTM revenue is not computed, and says why")
    check("**Disclosure.**" in t and "the company that builds Claude" in t
          and "takes no view on the company" in t
          and "Entries come from filings only" in t
          and "Press reports are never a source for an entry" in t
          and "listed gap" not in t
          and "stays a provisional dated record until\n  the S-1 is on EDGAR" in t.replace("\r\n", "\n"),
          "the template carries the order's disclosure and ruling D21's status (filings "
          "only, press never, the first row provisional until the S-1 is on EDGAR)")
    ipo = al.ipo_watch_lines()
    check(ipo and all(s.count("not yet public") == 3 for s in ipo) and "SPCX" in ipo[0],
          "the mega-IPO watch beside SPCX: float, inclusion and lock-ups \"not yet public\"")
    ab = (REPO / "daily_cascade" / "absorption_block.py").read_text(encoding="utf-8")
    check("ai_lab_lines()" in ab, "Factor I's lines carry them (report only)")


def group_f() -> None:
    head("F. ITEM 77, CYBER PRESSURE")
    cat = {"vulnerabilities": [{"dateAdded": d} for d in
                               ["2021-11-03"] * 5 + ["2026-10-05", "2026-10-07",
                                                     "2026-10-12", "2026-10-18"]]}
    wkly = cp.kev_weekly(cat, dt.date(2026, 10, 24))
    check(wkly["2021-11-01"] == 5 and wkly["2026-10-05"] == 2 and wkly["2026-10-12"] == 2
          and "2026-10-19" not in wkly and wkly["2025-01-06"] == 0,
          "KEV by hand: 5 in the seeding week, 2 and 2 in October's weeks, zeros "
          "between, the incomplete week left out")
    calls = []

    def fake(url, params=None):
        calls.append((url, params))
        if "cisa" in url:
            return cat
        return {"totalResults": 10 + len(calls)}
    slept = []
    out = cp.weekly(dry_run=True, force=True, today="2026-10-24", fetch=fake,
                    sleep=slept.append)
    nvd = [c for c in calls if "nvd" in c[0]]
    check(len(nvd) == 8 and len(slept) == 7 and all(s == 6.5 for s in slept)
          and nvd[0][1]["cvssV3Severity"] == "CRITICAL"
          and nvd[-1][1]["pubStartDate"] == "2026-10-12T00:00:00.000"
          and not out["failed"],
          "NVD re-read for 8 complete weeks, CRITICAL (9.0 or higher), 6.5 s apart, "
          "through a fake fetch")
    sk = cp.weekly(dry_run=True, today="2026-10-22", fetch=fake)
    check("skipped" in sk, "it reads on Saturdays and skips itself otherwise")
    weeks = [(dt.date(2021, 11, 1) + dt.timedelta(days=7 * i)).isoformat() for i in range(260)]
    rows = [obs(cp.KEV_KEY, d, 300 if i == 0 else (3 + i % 5)) for i, d in enumerate(weeks)]
    rows += [obs(cp.NVD_KEY, d, 20 + i % 9) for i, d in enumerate(weeks)]
    rows[-1]["value"] = 50
    rows[259]["value"] = 50
    db = store(rows)
    with observations.ObservationStore(db) as st:
        r = cp.read(st, NOW)
    check(r["kev"]["lens"]["n_full"] == 259 and r["flag"]["state"] == "on"
          and r["kev"]["count"] == 50 and r["nvd"]["count"] == 50,
          "the seeding week left out of KEV's percentiles (n 259); both at their highest "
          "in the same week: the flag is ON")
    rows2 = list(rows)
    rows2[-1] = dict(rows2[-1], value=22)
    with observations.ObservationStore(store(rows2)) as st:
        r2 = cp.read(st, NOW)
    check(r2["flag"]["state"] == "off", "with NVD's week ordinary, the flag is off")
    with observations.ObservationStore(store(rows[:260])) as st:
        r3 = cp.read(st, NOW)
    check(r3["flag"]["state"] == "not read" and "not read" in cp.lines(r3)[-1],
          "with NVD unstored: not read")
    ls = cp.lines(r)
    check(ls[-1].startswith("Cyber-pressure flag ON") and "never a tripwire" in ls[-1]
          and "provisional" in ls[1] and cp.incidents_line(r).startswith("Cyber pressure"),
          "the lines: provisional NVD weeks labelled, the flag report-only, the "
          "incidents cross-reference")
    ws = (REPO / "daily_cascade" / "weekly_stack.py").read_text(encoding="utf-8")
    da = (REPO / "daily_cascade" / "digital_addendum.py").read_text(encoding="utf-8")
    check("batch15_b2_block.cyber_subsection(st, now)" in ws
          and "batch15_b2_block.incidents_body(st, cutoff)" in da
          and 'secs["incidents"]["tables"] += b15["tables"]' in da,
          "the Weekly's Ahead carries the line; the addendum's incidents section "
          "carries the read and its table in its body (D19/D20, b60; no Drive link)")
    check("drive.google" not in (REPO / "daily_cascade" / "batch15_b2_block.py").read_text(
        encoding="utf-8"), "no link to Drive")


def group_g() -> None:
    head("G. ITEM 78, PROTOCOL BREADTH")
    plist = [{"tvl": 5.0}, {"tvl": 0}, {"tvl": None}, {"deadFrom": "2025-01-01", "tvl": 9.0},
             {"deprecated": True, "tvl": 3.0}, {"tvl": 1.5}]
    c = pb.counts(plist)
    check(c == {"total": 6, "listed": 4, "active": 2},
          "by hand: 6 protocols, 4 neither dead nor deprecated, 2 of them with TVL above zero")
    d = pb.daily(dry_run=True, fetch=lambda: plist, at="2026-10-23T21:25:00+00:00")
    check(d["counts"] == c and [r["value"] for r in d["rows"]] == [4, 2]
          and d["rows"][0]["source"] == "defillama" and d["rows"][0]["observed_at"] == "2026-10-23",
          "the dry run: two rows, source defillama, the pull's UTC day")
    rows = [obs(pb.ACTIVE_KEY, f"2026-{m:02d}-{dd:02d}", v) for m, dd, v in
            ((9, 20, 5400), (10, 1, 5450), (10, 23, 5485))]
    rows += [obs(pb.LISTED_KEY, "2026-10-23", 7904)]
    with observations.ObservationStore(store(rows)) as st:
        r = pb.read(st, NOW)
    ln = pb.line(r)
    check(r["start"] == "2026-09-20" and r["change_30d"] == 5485 - 5400 and r["days"] == 3
          and "History from 2026-09-20" in ln and "today's list only" in ln
          and "7,904 listed" in ln,
          f"the line states its history start and the change since the day 30 days back "
          f"({ln[:70]}...)")
    check("history starts at the first pull" in pb.line({"state": "absent"}),
          "unread: it says the history starts at the first pull")
    from daily_cascade import batch15_b2_block as blk
    with observations.ObservationStore(store(rows)) as st:
        sub = blk.protocol_subsection(st, NOW)
    ms = (REPO / "monthly_macro" / "stack.py").read_text(encoding="utf-8")
    check(sub and sub["lines"][1].startswith("The monthly count of protocol shutdowns from "
                                             "compiled lists: a listed gap")
          and "batch15_b2_block.protocol_subsection(st, now)" in ms,
          "the Monthly's digital chapter carries it, with the hand count's listed gap")


def group_h() -> None:
    head("H. THE NOTES AND RECORDS")
    t = NOTE.read_text(encoding="utf-8")
    bullets = [p for p in re.split(r"\n\s*\n", t) if p.lstrip().startswith("- **20")]
    check(len(bullets) == 3 and all("Source:" in b and re.search(r"https?://\S+", b)
                                    and re.search(r"\"[^\"]{10,}\"", b) for b in bullets),
          "three episodes, each with a quoted title and a URL")
    paras = re.split(r"\n\s*\n", t)
    dates = re.compile(r"\b\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w* "
                       r"\d{4}\b|\b(?:19|20)\d\d(?:-\d\d)?\b|\b[Ii]tem \d+\b|\bG\d\b|"
                       r"ST-R6\.\d+\w*|\(written as \d+")
    figs = [x for x in paras if not x.startswith(("#", "*Signal"))
            and re.search(r"\d", re.sub(r"https?://\S+", "", dates.sub("", x)))]
    check(figs and all(re.search(r"https?://", x) for x in figs),
          f"every paragraph with a figure carries its source URL ({len(figs)} such)")
    check("No published count of protocol shutdowns for 2022-23 was found" in t,
          "a comparison no source supports is said to be missing")
    q = (REPO / "docs" / "dated-appendix-queue.md").read_text(encoding="utf-8")
    # A68 (24 Oct 2026) moved item 74's record into Positioning and Flows' dated
    # Appendix B; item 75's stays in the queue until the S-1 is on EDGAR.
    pf = (REPO / "docs" / "whitepapers" / "positioning-and-flows-whitepaper.md").read_text(
        encoding="utf-8")
    p74 = pf.split("Batch 15 item 74)")[-1]
    p75 = q.split("(Batch 15 item 75)")[-1]
    check("Dated 22 Oct 2026" in p74 and "five to one" in p74 and "https://" in p74,
          "item 74's prime-book figures: one dated record, cited")
    check("PROVISIONAL" in p75 and "EDGAR" in p75 and "https://" in p75,
          "item 75's S-1 figures: one dated record, provisional, cited")


def group_i() -> None:
    head("I. HYGIENE")
    keys = [cp.KEV_KEY, cp.NVD_KEY, pb.LISTED_KEY, pb.ACTIVE_KEY]
    fams = {k: derived.family_of(k)[0] for k in keys}
    check(all(derived.registry_entry(k) for k in keys) and set(fams.values()) == {"quantity"},
          f"the four new keys are registered, each a quantity ({fams})")
    import yaml
    sr = yaml.safe_load((REPO / "source_registry.yaml").read_text(encoding="utf-8"))
    srcs = sr.get("sources") or sr
    check(all(s in srcs for s in ("cisa_kev", "nvd", "defillama", "cftc")),
          "their sources are registered ids (cisa_kev, nvd; defillama and cftc already)")
    fd = (REPO / "altdata" / "feeds.py").read_text(encoding="utf-8")
    sh = (REPO / "scripts" / "run_crypto_basket.sh").read_text(encoding="utf-8")
    check("_cyb.ROSTER" in fd and "_pb.ROSTER" in fd
          and "altdata.cyber_pressure weekly" in sh and "altdata.protocol_breadth daily" in sh,
          "both are steps of the crypto basket's run and on the freshness roster; no new "
          "timer")
    units = list((REPO / "deploy" / "systemd").glob("*cyber*")) + \
        list((REPO / "deploy" / "systemd").glob("*protocol*"))
    check(not units, "no unit file")
    src = "\n".join(p.read_text(encoding="utf-8") for p in NEW_CODE)
    imports = "\n".join(l for l in src.splitlines() if re.match(r"\s*(from|import)\s", l))
    check(not re.search(r"regime|market_state|composite|register|manual_input|flashalpha|vendor",
                        imports),
          "no composite, market-state, register, by-hand or vendor import in the new modules")
    check(not re.search(r"\bINSERT\b|\.execute\(\s*\"(?:INSERT|UPDATE|DELETE)", src),
          "no direct SQL write in them (the writers go through open_writer)")
    mine = "\n".join([src] + [p.read_text(encoding="utf-8") for p in NEW_CONFIG] + [
        NOTE.read_text(encoding="utf-8"), LAB.read_text(encoding="utf-8"),
        EDITION.read_text(encoding="utf-8"),
        (REPO / "docs" / "ledgers" / "short-extremes-preregistration-2026-10.md").read_text(encoding="utf-8"),
        # item 74's record, where A68 moved it (Positioning and Flows, Appendix B),
        # and item 75's, still in the queue.
        (REPO / "docs" / "whitepapers" / "positioning-and-flows-whitepaper.md").read_text(
            encoding="utf-8").split("Batch 15 item 74)")[-1],
        (REPO / "docs" / "dated-appendix-queue.md").read_text(encoding="utf-8").split(
            "(Batch 15 item 75)")[-1]])
    people = (r"Dalio|Marino|Prehn|Curzio|Gadala|Muur|Wanjun|Radge|Mark Wilson|Civita|"
              r"Hollerith|Howley|Kim Jong|Lamont")
    check(not re.search(people, mine), "no person's name in the new code, config, ledgers, "
                                       "notes or appendix lines")
    check(not re.search(r"(?<![\w./])@[A-Za-z_]\w+|[\w.+-]+@[\w-]+\.[a-z]{2,}", mine),
          "no handle and no email address")
    before = Path(observations.DEFAULT_DB)
    check(not before.exists() or before.stat().st_mtime < _START,
          "this gate wrote no store but its own temporary ones (the default database "
          "untouched)")


_START = 0.0


def main() -> int:
    global _START
    import time
    _START = time.time()
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g, group_h,
              group_i):
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
