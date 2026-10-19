"""
SR-8 -- the false-bottom audit (signal-triage ST-9; st-t3-calib, 18 Oct 2026).

    python tools/calibration/sr08_false_bottoms.py [--box] [--out DIR] [--date D]

THE REGISTER'S GATE (docs/signal-triage-register.md, SR-8). "Replay the bottom
side rally-by-rally through 2000-02, 2007-09 (Mar 2008), 1973-74 and 2022 (Mar;
Jun-Aug); count false bottoms. Score each confirmation element on whether it
separates those from Oct 2002, Mar 2009, Oct 1974 and Oct 2022. Elements that
discriminate enter the gate; elements that don't are dropped." The confirmation
set: "Breadth thrust in the first weeks; leadership by new groups rather than the
most-shorted prior leaders; HY spreads tightening through the rally; VIX term
structure back in contango; a successful retest." The fuel metrics: margin debt,
leveraged-ETF AUM, short interest. The time prior: "bears off valuation peaks run
two to three years". The gate: "Once the T&B top side has fired and price is below
a falling 200-day, the bottom threshold rises and two of the confirmation set are
required before Book A re-enters."

THE T&B BOTTOM SIDE IS NOT BUILT IN THIS REPO, so "the bottom side" is replayed
as the register's own object, the rally that looked like a bottom in real time.
WHAT THIS FIRST EDITION PRE-REGISTERS:
  * A CANDIDATE BOTTOM is a close that is the lowest since the bear's peak and
    from which the index closes at least 10% higher before it closes lower. A
    FALSE BOTTOM is a candidate later undercut inside the bear; the TRUE BOTTOM is
    the bear's final low. The bears (peak to final low, S&P 500 closes):
    1973-01-11 to 1974-10-03, 2000-03-24 to 2002-10-09, 2007-10-09 to 2009-03-09,
    2022-01-03 to 2022-10-12. Scoring is on the S&P 500; the Nasdaq Composite
    (2000-03-10 to 2002-10-09) is replayed for its count only, beside the
    register's sourced five.
  * THE STATE at each trough: below a falling 200-day (the 200-session mean under
    its value 20 sessions earlier). The top side's having fired is not replayable
    (T&B is not built), so the state is printed and not required.
  * EACH ELEMENT is read at the trough plus 30 sessions (the "first weeks"), or the
    session before an undercut if that comes first -- what was knowable then:
      breadth_industries  French's 49 industries, the breadth-thrust form: the 10-session
                          mean of the share of industries up reaches 0.615 within
                          10 sessions of being at or below 0.40 (a PROXY for the
                          held breadth keys, reaching 1926)
      breadth_sectors     the held calc.breadth_sector_above_50d's arithmetic on
                          the SPDR sector ETFs: at or below 20% within 5 sessions
                          of the trough, at or above 80% by the read
      breadth_rsp_spy     the held calc.breadth_rsp_over_spy: RSP/SPY higher at
                          the read than at the trough
      new_leadership      French's 49 industries: at most 2 of the rally's top 10
                          (trough to read) were top 10 in the 252 sessions before
                          the bear's peak (prior leaders; "most-shorted" has no
                          keyless history, so this is a PROXY)
      credit_tightening   Moody's Baa less the 10-year Treasury (DBAA - DGS10
                          daily from 1986; BAA - GS10 monthly before) lower at the
                          read than at the trough: a PROXY for HY OAS, whose FRED
                          history no longer reaches the episodes
      vix_contango        the held calc.vix3m_over_vix: VIX3M over VIX above 1 at
                          the read
      retest              within 126 sessions and before any undercut, a pullback
                          of at least 5% from the rally's high that holds above the
                          trough, then a 5% rise off that low
      margin_spent        FINRA margin debit's 12-month change at or below -20% in
                          the last month published (month-end plus 25 days) before
                          the trough
      short_fuel          SPY's FINRA days-to-cover at the last settlement
                          published (plus 8 days) before the trough at or above the
                          80th percentile of the 26 before it
      time_prior          18 months or more since the bear's peak at the trough
    and leveraged-ETF AUM is a LISTED GAP: no keyless history is known.
  * AN ELEMENT DISCRIMINATES when, where it is testable, it fires at >= 75% of the
    true bottoms (at least 2 testable) and at <= one third of the false bottoms
    (at least 3 testable). Fewer testable: NOT TESTABLE, with the date before
    which it cannot be read. Otherwise it DOES NOT DISCRIMINATE and is dropped.
  * THE AUDIT'S VERDICT: PASS when at least two elements discriminate (the gate
    asks two of the set); FAIL when fewer do; INSUFFICIENT when fewer than two are
    testable at all.

Sources, keyless and within terms: Yahoo daily closes (^GSPC, ^IXIC, ^VIX,
^VIX3M, the SPDR sector ETFs, RSP, SPY) through altdata.import_yfinance; Kenneth
French's 49 industry portfolios, daily and value-weighted (free for research use;
the vintage printed); FRED's graph CSV (DBAA, DGS10, BAA, GS10); FINRA's monthly
margin statistics file through altdata/sources/finra.py; FINRA's anonymous
consolidated short-interest API through altdata/loggers/borrow.py.
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import st8_common as C                                           # noqa: E402

ITEM = "SR-8"
NAME = "false-bottom-audit-2026"
BEARS = {"1973-74": ("1973-01-11", "1974-10-03"), "2000-02": ("2000-03-24", "2002-10-09"),
         "2007-09": ("2007-10-09", "2009-03-09"), "2022": ("2022-01-03", "2022-10-12")}
NASDAQ = ("2000-03-10", "2002-10-09")
RALLY = 0.10
READ = 30
SMA, SLOPE = 200, 20
ZW_N, ZW_LO, ZW_HI = 10, 0.40, 0.615
SECT_LO, SECT_HI, SECT_NEAR = 0.20, 0.80, 5
LEAD_TOP, LEAD_MAX, LEAD_PRIOR = 10, 2, 252
RETEST_DAYS, RETEST_PCT = 126, 0.05
MARGIN_CUT, MARGIN_LAG = -0.20, 25
SI_LAG, SI_N, SI_Q = 8, 26, 0.80
TIME_MONTHS = 18
TPR_MIN, FPR_MAX, TRUE_MIN, FALSE_MIN = 0.75, 1 / 3, 2, 3
SECTORS = ("XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY", "XLRE", "XLC")
ELEMENTS = {
    "breadth_industries": ("breadth thrust", "French 49 industries, the breadth-thrust form (proxy)"),
    "breadth_sectors": ("breadth thrust", "calc.breadth_sector_above_50d's arithmetic"),
    "breadth_rsp_spy": ("breadth thrust", "calc.breadth_rsp_over_spy"),
    "new_leadership": ("leadership by new groups", "French 49 industries (proxy)"),
    "credit_tightening": ("HY spreads tightening", "Moody's Baa less the 10-year (proxy)"),
    "vix_contango": ("VIX term structure in contango", "calc.vix3m_over_vix"),
    "retest": ("a successful retest", "S&P 500 closes"),
    "margin_spent": ("fuel: margin debt", "finra.margin_debit"),
    "short_fuel": ("fuel: short interest", "finra.short_interest_days_to_cover (SPY)"),
    "time_prior": ("the time prior", "months since the bear's peak"),
}
GAPS = {"leveraged_etf_aum": "leveraged-ETF AUM: no keyless history known (issuer daily "
                             "files carry today's holdings, not a history); a listed gap, "
                             "no key pursued"}
SOURCED_8 = ("the register's cited chart (Nasdaq 2000-02, 19 Sep 2026): five rallies of "
             "12-45% inside a 78% decline, each a bottom in real time; and the Tops & "
             "Bottoms paper (docs/whitepapers/tops-and-bottoms-whitepaper.md): fewer than "
             "one in five NYSE issues above their 200-day at the 1974 low; the 1929-30 "
             "rally of +46% the archetype")


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------
def french_daily(text: str) -> dict[str, dict[str, float]]:
    """{YYYY-MM-DD: {industry: return, percent}} from the daily VW section."""
    sec = next(v for k, v in C.french_sections(text).items()
               if k.startswith("Average Value Weighted Returns -- Daily"))
    head, out = sec[0], {}
    for cells in sec[1:]:
        if len(cells[0]) != 8 or not cells[0].isdigit():
            continue
        day = f"{cells[0][:4]}-{cells[0][4:6]}-{cells[0][6:]}"
        row = {}
        for j, name in enumerate(head[1:], start=1):
            try:
                v = float(cells[j])
            except (ValueError, IndexError):
                continue
            if v not in (-99.99, -999.0):
                row[name] = v
        out[day] = row
    return out


def load_public() -> dict:
    from altdata.ledgers import sources as S
    from altdata.loggers import borrow
    from altdata.sources import finra, french
    from altdata.sources._base import http_get_response
    data, _ = http_get_response(french.BASE + "49_Industry_Portfolios_daily_CSV.zip",
                                timeout=180)
    text = french._unzip(data)                                  # noqa: SLF001
    margin = sorted((r["observed_at"][:10], float(r["value"])) for r in finra._produce()  # noqa: SLF001
                    if r["registry_key"] == "finra.margin_debit")
    si = []
    for a, b in (("2017-12-01", "2019-12-31"), ("2020-01-01", "2021-12-31"),
                 ("2022-01-01", "2023-12-31")):
        si += [(str(r.get("settlementDate"))[:10], float(r["daysToCoverQuantity"]))
               for r in borrow._si_rows("SPY", limit=500, start=a, end=b)  # noqa: SLF001
               if r.get("daysToCoverQuantity") not in (None, "")]
    return {"spx": C.yahoo_close("^GSPC"), "ixic": C.yahoo_close("^IXIC"),
            "vix": C.yahoo_close("^VIX"), "vix3m": C.yahoo_close("^VIX3M"),
            "sectors": {s: C.yahoo_close(s) for s in SECTORS},
            "rsp": C.yahoo_close("RSP"), "spy": C.yahoo_close("SPY"),
            "ind": french_daily(text), "french_vintage": french.crsp_vintage(text),
            "dbaa": S.fred("DBAA"), "dgs10": S.fred("DGS10"),
            "baa": C.monthly_last(S.fred("BAA")), "gs10": C.monthly_last(S.fred("GS10")),
            "margin": margin, "si": sorted(set(si))}


# ---------------------------------------------------------------------------
# The replay
# ---------------------------------------------------------------------------
def candidates(px: C.Daily, peak: str, low: str) -> list[dict]:
    """The bear's candidate bottoms, oldest first: each a new low since the peak
    followed by a >= 10% rise before a lower close. The final low is the true one."""
    days = [d for d, _ in px]
    i0, i1 = days.index(peak), days.index(low)
    out, run = [], float("inf")
    for i in range(i0, i1 + 1):
        c = px[i][1]
        if c >= run:
            continue
        run = c
        hi, hi_i, under = c, i, None
        for k in range(i + 1, len(px)):
            if px[k][1] < c:
                under = k
                break
            if px[k][1] > hi:
                hi, hi_i = px[k][1], k
            if under is None and i == i1 and k - i > 252:
                break
        if hi >= c * (1 + RALLY):
            out.append({"i": i, "trough": days[i], "close": c, "rally_pct": hi / c - 1,
                        "rally_peak": days[hi_i], "undercut_i": under,
                        "undercut": days[under] if under is not None else None,
                        "kind": "true" if i == i1 else "false"})
    return out


def below_falling_200(px: C.Daily, i: int) -> Optional[bool]:
    if i < SMA + SLOPE:
        return None
    sma = sum(v for _, v in px[i - SMA + 1:i + 1]) / SMA
    sma0 = sum(v for _, v in px[i - SLOPE - SMA + 1:i - SLOPE + 1]) / SMA
    return px[i][1] < sma and sma < sma0


def read_index(c: dict) -> int:
    """The session the elements are read at: the trough plus 30, or the one
    before the undercut."""
    r = c["i"] + READ
    return min(r, c["undercut_i"] - 1) if c["undercut_i"] is not None else r


# ---------------------------------------------------------------------------
# The elements: each returns (fires, value, note) or None when not testable
# ---------------------------------------------------------------------------
def _at(s: C.Daily, day: str) -> Optional[float]:
    j = C.on_or_before(s, day)
    return s[j][1] if j is not None else None


def el_breadth_industries(d: dict, t: str, r: str):
    days = sorted(k for k in d["ind"] if k <= r)
    if not days or days[0] > t:
        return None
    share = [(k, sum(1 for v in d["ind"][k].values() if v > 0) / max(1, len(d["ind"][k])))
             for k in days[-(READ + 40):]]
    m = [(share[i][0], sum(x for _, x in share[i - ZW_N + 1:i + 1]) / ZW_N)
         for i in range(ZW_N - 1, len(share))]
    best = None
    for i, (k, v) in enumerate(m):
        if k < t:
            continue
        lo = min(x for _, x in m[max(0, i - ZW_N):i + 1])
        if v >= ZW_HI and lo <= ZW_LO:
            return True, v, f"thrust on {k} (from {lo:.2f} to {v:.2f})"
        best = max(best or 0, v)
    return False, best, "no thrust"


def _sector_share(d: dict, day: str) -> Optional[float]:
    n = up = 0
    for s in d["sectors"].values():
        j = C.on_or_before(s, day)
        if j is None or j < 49:
            continue
        sma = sum(v for _, v in s[j - 49:j + 1]) / 50
        n += 1
        up += s[j][1] > sma
    return up / n if n >= 9 else None


def el_breadth_sectors(d: dict, t: str, r: str, near: list[str]):
    lo = [x for x in (_sector_share(d, k) for k in near) if x is not None]
    hi = _sector_share(d, r)
    if not lo or hi is None:
        return None
    return (min(lo) <= SECT_LO and hi >= SECT_HI), hi, f"from {min(lo):.0%} to {hi:.0%}"


def el_breadth_rsp_spy(d: dict, t: str, r: str):
    a0, b0, a1, b1 = (_at(d["rsp"], t), _at(d["spy"], t), _at(d["rsp"], r), _at(d["spy"], r))
    if None in (a0, b0, a1, b1) or d["rsp"][0][0] > t:
        return None
    ch = (a1 / b1) / (a0 / b0) - 1
    return ch > 0, ch, f"RSP/SPY {ch:+.1%}"


def _cum(d: dict, a: str, b: str) -> dict[str, float]:
    g: dict[str, float] = {}
    for k in sorted(x for x in d["ind"] if a < x <= b):
        for ind, v in d["ind"][k].items():
            g[ind] = g.get(ind, 1.0) * (1 + v / 100.0)
    return g


def el_new_leadership(d: dict, t: str, r: str, peak: str):
    days = sorted(d["ind"])
    if not days or days[0] > peak:
        return None
    j = max(0, days.index(max(x for x in days if x <= peak)) - LEAD_PRIOR)
    prior = _cum(d, days[j], peak)
    rally = _cum(d, t, r)
    common = set(prior) & set(rally)
    if len(common) < 2 * LEAD_TOP:
        return None
    top_p = set(sorted(common, key=lambda k: -prior[k])[:LEAD_TOP])
    top_r = sorted(common, key=lambda k: -rally[k])[:LEAD_TOP]
    ov = len(top_p & set(top_r))
    return ov <= LEAD_MAX, ov, f"{ov} of the rally's top {LEAD_TOP} were prior leaders"


def el_credit(d: dict, t: str, r: str):
    if t >= d["dbaa"][0][0]:
        a0, a1 = _at(d["dbaa"], t), _at(d["dbaa"], r)
        g0, g1 = _at(d["dgs10"], t), _at(d["dgs10"], r)
        if None in (a0, a1, g0, g1):
            return None
        ch = 100 * ((a1 - g1) - (a0 - g0))
        return ch < 0, ch, f"Baa less 10y {ch:+.0f} bp (daily)"
    m0, m1 = t[:7], r[:7]
    if m0 == m1:
        m1 = C.madd(m0, 1)
    try:
        ch = 100 * ((d["baa"][m1] - d["gs10"][m1]) - (d["baa"][m0] - d["gs10"][m0]))
    except KeyError:
        return None
    return ch < 0, ch, f"Baa less 10y {ch:+.0f} bp (monthly, {m0} to {m1})"


def el_vix(d: dict, t: str, r: str):
    if d["vix3m"][0][0] > t:
        return None
    a, b = _at(d["vix3m"], r), _at(d["vix"], r)
    if a is None or not b:
        return None
    return a / b > 1, a / b, f"VIX3M/VIX {a / b:.2f}"


def el_retest(px: C.Daily, c: dict):
    i, low = c["i"], c["close"]
    end = min(len(px) - 1, i + RETEST_DAYS)
    if c["undercut_i"] is not None:
        end = min(end, c["undercut_i"] - 1)
    hi, pull_lo, pulled = low, None, False
    for k in range(i + 1, end + 1):
        v = px[k][1]
        if not pulled:
            hi = max(hi, v)
            if hi > low * (1 + RETEST_PCT) and v <= hi * (1 - RETEST_PCT):
                pulled, pull_lo = True, v
        else:
            pull_lo = min(pull_lo, v)
            if v >= pull_lo * (1 + RETEST_PCT):
                return True, k - i, f"held above the trough; confirmed {px[k][0]}"
    return False, None, "no successful retest before the undercut or 126 sessions"


def el_margin(d: dict, t: str):
    m = [(x, v) for x, v in d["margin"]
         if (dt.date.fromisoformat(x) + dt.timedelta(days=MARGIN_LAG)).isoformat() <= t]
    if len(m) < 13:
        return None
    ch = m[-1][1] / m[-13][1] - 1
    return ch <= MARGIN_CUT, ch, f"margin debit {ch:+.0%} over 12 months to {m[-1][0][:7]}"


def el_short(d: dict, t: str):
    s = [(x, v) for x, v in d["si"]
         if (dt.date.fromisoformat(x) + dt.timedelta(days=SI_LAG)).isoformat() <= t]
    if len(s) < SI_N + 1:
        return None
    from altdata import ledgers
    q = ledgers.quantile([v for _, v in s[-SI_N - 1:-1]], SI_Q)
    return s[-1][1] >= q, s[-1][1], f"SPY days to cover {s[-1][1]:.1f} against {q:.1f}"


def el_time(peak: str, t: str):
    p, x = dt.date.fromisoformat(peak), dt.date.fromisoformat(t)
    mo = (x.year - p.year) * 12 + x.month - p.month
    return mo >= TIME_MONTHS, mo, f"{mo} months since the peak"


def score(d: dict, px: C.Daily, c: dict, peak: str) -> dict:
    days = [x for x, _ in px]
    t, r = c["trough"], days[read_index(c)]
    near = days[max(0, c["i"] - SECT_NEAR):c["i"] + SECT_NEAR + 1]
    return {"breadth_industries": el_breadth_industries(d, t, r),
            "breadth_sectors": el_breadth_sectors(d, t, r, near),
            "breadth_rsp_spy": el_breadth_rsp_spy(d, t, r),
            "new_leadership": el_new_leadership(d, t, r, peak),
            "credit_tightening": el_credit(d, t, r),
            "vix_contango": el_vix(d, t, r),
            "retest": el_retest(px, c),
            "margin_spent": el_margin(d, t),
            "short_fuel": el_short(d, t),
            "time_prior": el_time(peak, t), "_read": r}


def judge_element(rows: list[dict], key: str) -> dict:
    tr = [r[key] for r in rows if r["kind"] == "true" and r[key] is not None]
    fa = [r[key] for r in rows if r["kind"] == "false" and r[key] is not None]
    tpr = C.share([x[0] for x in tr]) if tr else None
    fpr = C.share([x[0] for x in fa]) if fa else None
    if len(tr) < TRUE_MIN or len(fa) < FALSE_MIN:
        word = "NOT TESTABLE"
    elif tpr >= TPR_MIN and fpr <= FPR_MAX:
        word = "DISCRIMINATES"
    else:
        word = "DOES NOT DISCRIMINATE"
    untested = sorted(r["trough"] for r in rows if r[key] is None)
    return {"true_n": len(tr), "true_fires": sum(1 for x in tr if x[0]),
            "false_n": len(fa), "false_fires": sum(1 for x in fa if x[0]),
            "tpr": tpr, "fpr": fpr, "word": word,
            "not_testable_before": None if not untested else
            min((r["trough"] for r in rows if r[key] is not None), default="never")}


def audit_word(j: dict) -> str:
    disc = [k for k, v in j.items() if v["word"] == "DISCRIMINATES"]
    testable = [k for k, v in j.items() if v["word"] != "NOT TESTABLE"]
    if len(testable) < 2:
        return C.INSUFFICIENT
    return C.PASS if len(disc) >= 2 else C.FAIL


# ---------------------------------------------------------------------------
def doctrine_proposal(disc: list[str]) -> list[str]:
    """The register's candidate rule, worded to what the audit found: it asks two
    confirmations only when the audited set has two to ask for."""
    s = ", ".join(disc) if disc else "none"
    need = ("two confirmations from the audited set" if len(disc) >= 2 else
            "confirmation from the audited set, in a number the monthly sets")
    out = ["**A proposal for the Doctrine monthly of 7-8 Nov, drafted under rule 31. "
           "It grants nothing, and its number is the monthly's to assign.**", "",
           "> *In a declared bear regime a rally is a mechanism, not a signal. Book A "
           f"re-entry requires the bottom composite plus {need} ({s}), read in the "
           "rally's first six weeks. Size on the assumption that a bear rally and a new "
           "bull are indistinguishable in real time.*", "",
           "The register's candidate text is kept, with the change the audit supplies: "
           "'confirmation' names the audited set rather than the register's five, "
           "because elements that did not discriminate are dropped."]
    if len(disc) < 2:
        out.append(f"The audit found {len(disc)} element(s) that discriminate, so the "
                   "register's 'two of the confirmation set' has no second member: "
                   "whether the raised threshold stands alone, or the one element with "
                   "it, is the monthly's decision, not this ledger's.")
    return out


def study(d: dict, mode: str) -> dict:
    rows, counts = [], {}
    for name, (peak, low) in BEARS.items():
        cs = candidates(d["spx"], peak, low)
        counts[name] = sum(1 for c in cs if c["kind"] == "false")
        for c in cs:
            sc = score(d, d["spx"], c, peak)
            rows.append({"bear": name, "index": "S&P 500", "trough": c["trough"],
                         "kind": c["kind"], "close": round(c["close"], 2),
                         "rally_pct": round(c["rally_pct"], 4), "rally_peak": c["rally_peak"],
                         "undercut": c["undercut"], "read_at": sc.pop("_read"),
                         "below_falling_200d": below_falling_200(d["spx"], c["i"]), **sc})
    nq = candidates(d["ixic"], *NASDAQ)
    j = {k: judge_element(rows, k) for k in ELEMENTS}
    word = audit_word(j)
    disc = [k for k, v in j.items() if v["word"] == "DISCRIMINATES"]
    verdict = (f"{word} -- {len(disc)} element(s) discriminate"
               + (f" ({', '.join(disc)})" if disc else "")
               + f"; {sum(counts.values())} false bottoms and 4 true across the four bears "
               f"(S&P 500); rule: >= 2 discriminate, each firing at >= 75% of testable "
               f"true bottoms and <= one third of testable false ones")
    body = ["**The replay** (S&P 500 closes; a candidate is a new bear low followed by "
            "a 10% rally before a lower close):", "",
            "| Bear | Trough | Kind | Rally | Rally peak | Undercut | Below a falling 200-day |",
            "|---|---|---|---|---|---|---|"]
    for r in rows:
        body.append(f"| {r['bear']} | {r['trough']} | {r['kind']} | {C.pct(r['rally_pct'])} | "
                    f"{r['rally_peak']} | {r['undercut'] or '-'} | "
                    f"{'n/a' if r['below_falling_200d'] is None else 'yes' if r['below_falling_200d'] else 'no'} |")
    body += ["", "False bottoms by bear: " + "; ".join(f"{k} {v}" for k, v in counts.items())
             + f". Nasdaq Composite 2000-02, the same rule: "
             f"{sum(1 for c in nq if c['kind'] == 'false')} false bottoms ("
             + ", ".join(f"{c['trough']} {C.pct(c['rally_pct'], 0)}" for c in nq
                         if c["kind"] == "false") + ").", "",
             "**The scores** (each element read at the trough plus 30 sessions, or before "
             "an undercut):", "",
             "| Element | Register's item | Key | True bottoms firing | False bottoms "
             "firing | Not testable before | Word |",
             "|---|---|---|---|---|---|---|"]
    for k, (item, key) in ELEMENTS.items():
        e = j[k]
        body.append(f"| {k} | {item} | {key} | {e['true_fires']} of {e['true_n']} | "
                    f"{e['false_fires']} of {e['false_n']} | "
                    f"{e['not_testable_before'] or 'testable throughout'} | **{e['word']}** |")
    for k, why in GAPS.items():
        body.append(f"| {k} | fuel: leveraged-ETF AUM | none | - | - | never (a gap) | "
                    f"**LISTED GAP** |")
    body += ["", "**Each candidate's reads:**", "",
             "| Trough | Kind | " + " | ".join(ELEMENTS) + " |",
             "|---|---|" + "---|" * len(ELEMENTS)]
    for r in rows:
        cells = []
        for k in ELEMENTS:
            x = r[k]
            cells.append("n/t" if x is None else ("yes" if x[0] else "no"))
        body.append(f"| {r['trough']} | {r['kind']} | " + " | ".join(cells) + " |")
    kept = [k for k in ELEMENTS if j[k]["word"] == "DISCRIMINATES"]
    dropped = [k for k in ELEMENTS if j[k]["word"] == "DOES NOT DISCRIMINATE"]
    untest = [k for k in ELEMENTS if j[k]["word"] == "NOT TESTABLE"]
    body += ["", "## The gate specification", "",
             "- **State:** the T&B top side has fired and the S&P 500 is below a falling "
             "200-day (the 200-session mean under its value 20 sessions earlier).",
             "- **Then:** the bottom threshold rises (its level is T&B's, set at T&B full) "
             f"and two of the confirmation set are required, read at the trough plus "
             f"{READ} sessions.",
             f"- **The set (elements that discriminate):** {', '.join(kept) or 'none'}.",
             f"- **Dropped (do not discriminate):** {', '.join(dropped) or 'none'}.",
             f"- **Not testable on our n:** {', '.join(untest) or 'none'}; and "
             f"{'; '.join(GAPS.values())}.",
             ("- **Two of the set cannot bind**: fewer than two elements discriminate, so "
              "the register's 'two of the confirmation set' has no set to count; the "
              "Doctrine monthly decides what stands in its place." if len(kept) < 2 else
              "- **Two of the set** is satisfiable: the set has "
              f"{len(kept)} members."),
             "- **Wiring:** none. The stub (config/tb_false_bottom_gate.yaml) is read by "
             "no module until T&B full (ST-11).", "",
             "## The Doctrine rule proposal", ""] + doctrine_proposal(kept) + [
             "", f"**Sourced comparison, not episodes of ours:** {SOURCED_8}."]
    csv_rows = []
    for r in rows:
        x = {k: r[k] for k in ("bear", "index", "trough", "kind", "close", "rally_pct",
                               "rally_peak", "undercut", "read_at", "below_falling_200d")}
        for k in ELEMENTS:
            v = r[k]
            x[f"{k}_fires"] = None if v is None else v[0]
            x[f"{k}_value"] = None if v is None or v[1] is None else round(float(v[1]), 4)
        csv_rows.append(x)
    return {
        "item": ITEM, "title": "the false-bottom audit: the bottom side, rally by rally",
        "as_of": f"S&P 500 {d['spx'][-1][0]}; French {d['french_vintage']}; FINRA margin "
                 f"{d['margin'][-1][0][:7]}",
        "window": "; ".join(f"{k} {a} to {b}" for k, (a, b) in BEARS.items())
                  + f"; Nasdaq {NASDAQ[0]} to {NASDAQ[1]} (count only)",
        "n": len(rows),
        "statistic": "false bottoms per bear; each confirmation element's firing rate at "
                     "the true bottoms against the false ones",
        "pass_rule": ("the register's: elements that discriminate enter the gate, those "
                      "that don't are dropped. Pre-registered by this first edition: an "
                      "element discriminates at >= 75% of >= 2 testable true bottoms and "
                      "<= one third of >= 3 testable false ones; the audit PASSes with >= 2 "
                      "discriminating (the gate asks two)"),
        "verdict": verdict,
        "rights": ("PASS: the gate specification above is what ST-11 wires at T&B full, "
                   "and the Doctrine proposal goes to the monthly. FAIL or INSUFFICIENT: "
                   "the specification stands as written, with its gaps, and the monthly "
                   "decides. Book A rule A-2 changes nothing until then. " + C.RIGHTS_NOTE),
        "sources": ["Yahoo daily closes (altdata.import_yfinance): ^GSPC, ^IXIC, ^VIX, "
                    "^VIX3M, " + ", ".join(SECTORS) + ", RSP, SPY",
                    f"Kenneth French data library (no key; free for research use): "
                    f"49_Industry_Portfolios_daily_CSV.zip, value-weighted daily returns; "
                    f"vintage {d['french_vintage']}",
                    "FRED graph CSV (no key): DBAA, DGS10, BAA, GS10 (ICE BofA HY OAS is "
                    "served only from 2023-10, so it reaches no episode)",
                    "FINRA margin statistics, margin-statistics.xlsx (no key), through "
                    "altdata/sources/finra.py; Customer Margin Balances from 1997",
                    "FINRA consolidated short interest API (anonymous) through "
                    "altdata/loggers/borrow.py; SPY from 2017-12-29"],
        "source_mode": mode, "body": body, "episodes": csv_rows,
        "caveats": ["Each element is read with what was published by its read date; the "
                    "French file is restated with each CRSP update.",
                    "The S&P 500 and French's industries are price and total-return "
                    "series respectively; the replay is on the index's closes.",
                    "Four true bottoms is the register's own n; no element can score "
                    "better than 4 of 4 there, and a 1974 or 2002 read is often not "
                    "testable on the held keys."]}


def write(r: dict, out: Optional[str], name: str, date: str) -> None:
    from altdata import ledgers
    import csv
    import io
    faults = ledgers.ledger_faults(r)
    if faults:
        raise ValueError(f"not a ledger: {faults}")
    d = Path(out) if out else C.REPO / "docs" / "ledgers"
    d.mkdir(parents=True, exist_ok=True)
    cv = d / f"{name}-episodes.csv"
    r["csv_name"] = cv.name
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(r["episodes"][0]), lineterminator="\n")
    w.writeheader()
    w.writerows(r["episodes"])
    cv.write_text(buf.getvalue(), encoding="utf-8", newline="\n")
    md = d / f"{name}.md"
    md.write_text(ledgers.render(r, date), encoding="utf-8", newline="\n")
    print(f"{r['item']}: {r['verdict']}  (n {r['n']}; as of {r['as_of']})")
    print(f"  wrote {md} and {cv.name}")


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="SR-8 false-bottom audit (ST-9)")
    ap.add_argument("--box", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--date", help="the box edition's date (default today)")
    a = ap.parse_args(argv)
    r = study(load_public(), C.BOX if a.box else C.LAPTOP)
    day = a.date or dt.date.today().isoformat()
    write(r, a.out, NAME if not a.box else f"{NAME}-box-{day}", day)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
