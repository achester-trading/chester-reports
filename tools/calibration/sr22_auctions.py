"""
SR-22 -- coupon auctions 2009 to 2026 against the next sessions' 10-year moves
(signal-triage ST-7; st-t2-rates, 18 Oct 2026).

    python tools/calibration/sr22_auctions.py [--box] [--out DIR] [--date D]

THE REGISTER'S GATE (docs/signal-triage-register.md, SR-22). "~1,000 coupon
auctions 2009-2026; forward 1m and 3m 10y change conditional on top-decile
tails. Pass for the contrarian read: median forward 3m change negative with
>= 60% hit rate. Otherwise stress flag only."

G-32 (ruled, docs/change-order-signal-triage-2026-09-25.md) supplies what the
register cannot: no free source serves the when-issued yield, so there is no
tail. Until there is, ABS_STRESS is bid-to-cover in its bottom decile on two
consecutive coupon auctions, or dealer takedown above 20%, and "ST-7 tests those
two, plus a pseudo-tail (high yield minus the prior close's constant-maturity
yield) as a candidate only". So:
  * THE VERDICT is the register's rule applied to ABS_STRESS as the live flag
    computes it: altdata.absorption.abs_stress, the function ST-4's features
    pass runs, called here on the whole history (per tenor, the bottom decile of
    that tenor's own covers up to and including the auction; 10 auctions before
    the first decile; TIPS in the sequence as the live rule has them).
  * Its two legs are printed under the same rule, for reading only.
  * THE PSEUDO-TAIL is a candidate row: a nominal coupon's high yield less the
    previous session's constant-maturity yield at its original term (DGS2, 3, 5,
    7, 10, 20, 30), top decile of its tenor's own pseudo-tails through that
    auction (20 before the first). Its line grants nothing whatever it reads,
    because the morning's market move is inside it.

WHAT THE FIRST EDITION PRE-REGISTERS, where the register is silent: the forward
change is DGS10 from the auction day's close to 21 and 63 observations later,
in bp; a hit is a fall; "top decile" is a reading at or above the 90th
percentile of its own history; the floor is 30 flagged auctions with 63
sessions forward. Every flagged auction is an observation (the register counts
auctions), and the number of distinct months they fall in is printed beside it,
because auctions of one week share one forward window.

Point in time: auction results are never revised (the writer's own docstring),
and the constant-maturity yields are not revised. TreasuryDirect's API serves
the whole history from 2009, so the laptop's edition reads the same records the
box stores; nothing here needs the box's vintages. The query uses the renamed
date field (competitiveAuctionCloseDate) and reads the old and the new field
names, as writer-fixes-1 found them on 17 Oct.
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import st7_common as C                                           # noqa: E402

ITEM = "SR-22"
START = 2009
H1, H3 = 21, 63
FLOOR = 30
HIT = 0.60
DECILE = 90.0
MIN_TAIL_HISTORY = 20
NOMINAL = ("Note", "Bond")
CMT = {"2-Year": "DGS2", "3-Year": "DGS3", "5-Year": "DGS5", "7-Year": "DGS7",
       "10-Year": "DGS10", "20-Year": "DGS20", "30-Year": "DGS30"}
URL = "https://www.treasurydirect.gov/TA_WS/securities/search"
# Old and new names (TreasuryDirect's rename, Oct 2026), the first non-empty read.
FIELDS = {"day": ("competitiveAuctionCloseDate", "auctionDate"),
          "dealer": ("primaryDealersCompetitiveParAwarded", "primaryDealerAccepted"),
          "competitive": ("subtotalCompetitiveParAwardedInsideOfOfferingAmount",
                          "competitiveAccepted")}


def field(rec: dict, name: str):
    for k in FIELDS[name]:
        if rec.get(k) not in (None, ""):
            return rec[k]
    return None


def _num(v):
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return None


def auctions_from_records(records: list[dict]) -> list[dict]:
    """One row per held coupon auction: day, type, term, cover, dealer share,
    high yield."""
    out, seen = [], set()
    for rec in records:
        typ = str(rec.get("type") or rec.get("securityType") or "").strip()
        if typ not in ("Note", "Bond", "TIPS"):
            continue
        day = str(field(rec, "day") or "")[:10]
        btc = _num(rec.get("bidToCoverRatio"))
        term = str(rec.get("originalSecurityTerm") or rec.get("securityTerm") or "").strip()
        if btc is None or len(day) != 10 or not term or (typ, term, day) in seen:
            continue
        seen.add((typ, term, day))
        comp, dealer = _num(field(rec, "competitive")), _num(field(rec, "dealer"))
        out.append({"day": day, "type": typ, "term": term, "btc": btc,
                    "dealer": dealer / comp if comp and dealer is not None else None,
                    "high_yield": _num(rec.get("highYield"))})
    return sorted(out, key=lambda r: (r["day"], r["type"], r["term"]))


def load_public() -> dict:
    from altdata.ledgers import sources as S
    from altdata.sources._base import http_get_json
    recs = []
    for y in range(START, dt.date.today().year + 1):
        recs += http_get_json(URL, params={
            "startDate": f"{y}-01-01", "endDate": f"{y}-12-31",
            "dateFieldName": "competitiveAuctionCloseDate", "format": "json"},
            timeout=90)
    return {"auctions": auctions_from_records(recs),
            "cmt": {t: S.fred(s) for t, s in CMT.items()}}


def flags(auctions: list[dict]) -> dict[tuple, dict]:
    """{(day, instrument): {abs_stress, two_low, dealer}} from the live rule."""
    from altdata import absorption
    btc, dealer = {}, {}
    for a in auctions:
        inst = f"{a['type']}:{a['term']}"
        btc.setdefault(inst, []).append((a["day"], a["btc"], ""))
        if a["dealer"] is not None:
            dealer.setdefault(inst, []).append((a["day"], a["dealer"], ""))
    out = {}
    for d, inst, flag, trace, _ in absorption.abs_stress(btc, dealer):
        out[(d, inst)] = {"abs_stress": bool(flag),
                          "two_low": "previous coupon auction too" in trace,
                          "dealer": "> 20%" in trace}
    return out


def pseudo_tails(auctions: list[dict], cmt: dict) -> dict[tuple, tuple]:
    """{(day, instrument): (pseudo-tail bp, top decile)} for nominal coupons."""
    out, hist = {}, {}
    for a in auctions:
        s = cmt.get(a["term"])
        if a["type"] not in NOMINAL or s is None or a["high_yield"] is None:
            continue
        j = C.index_on_or_before(s, (dt.date.fromisoformat(a["day"])
                                     - dt.timedelta(days=1)).isoformat())
        if j is None:
            continue
        tail = 100.0 * (a["high_yield"] - s[j][1])
        h = hist.setdefault(a["term"], [])
        h.append(tail)
        top = (len(h) > MIN_TAIL_HISTORY
               and 100.0 * sum(1 for x in h if x < tail) / len(h) >= DECILE)
        out[(a["day"], f"{a['type']}:{a['term']}")] = (tail, top)
    return out


def evaluate(events: list[dict]) -> dict:
    done = [e for e in events if e["d10_3m_bp"] is not None]
    m3 = C.median([e["d10_3m_bp"] for e in done])
    hit = C.share([e["d10_3m_bp"] < 0 for e in done])
    m1 = C.median([e["d10_1m_bp"] for e in events if e["d10_1m_bp"] is not None])
    months = len({e["day"][:7] for e in done})
    if len(done) < FLOOR:
        word = C.INSUFFICIENT
    else:
        word = C.PASS if (m3 is not None and m3 < 0 and hit >= HIT) else C.FAIL
    return {"n": len(done), "months": months, "m1": m1, "m3": m3, "hit": hit,
            "word": word}


def study(d: dict, mode: str) -> dict:
    auc = d["auctions"]
    ten = d["cmt"]["10-Year"]
    fl = flags(auc)
    pt = pseudo_tails(auc, d["cmt"])
    rows = []
    for a in auc:
        key = (a["day"], f"{a['type']}:{a['term']}")
        i = C.index_on_or_before(ten, a["day"])
        f = fl.get(key, {})
        t = pt.get(key)
        rows.append({"day": a["day"], "instrument": key[1], "bid_to_cover": a["btc"],
                     "dealer_share": None if a["dealer"] is None else round(a["dealer"], 4),
                     "high_yield": a["high_yield"],
                     "pseudo_tail_bp": None if t is None else round(t[0], 1),
                     "pseudo_tail_top_decile": bool(t and t[1]),
                     "abs_stress": bool(f.get("abs_stress")),
                     "leg_two_low_covers": bool(f.get("two_low")),
                     "leg_dealers_over_20": bool(f.get("dealer")),
                     "d10_1m_bp": None if i is None or C.fwd_change(ten, i, H1) is None
                     else round(100 * C.fwd_change(ten, i, H1), 1),
                     "d10_3m_bp": None if i is None or C.fwd_change(ten, i, H3) is None
                     else round(100 * C.fwd_change(ten, i, H3), 1)})
    nominal = [r for r in rows if r["instrument"].split(":")[0] in NOMINAL]
    sets = {"ABS_STRESS (the live flag; the verdict)": [r for r in rows if r["abs_stress"]],
            "  leg: bottom-decile cover on two consecutive coupon auctions":
                [r for r in rows if r["leg_two_low_covers"]],
            "  leg: dealer takedown above 20%": [r for r in rows if r["leg_dealers_over_20"]],
            "Pseudo-tail, top decile (candidate only)":
                [r for r in rows if r["pseudo_tail_top_decile"]],
            "Every coupon auction (unconditional)": rows}
    ev = {k: evaluate(v) for k, v in sets.items()}
    main = ev["ABS_STRESS (the live flag; the verdict)"]
    if main["word"] == C.INSUFFICIENT:
        verdict = (f"{C.INSUFFICIENT} -- {main['n']} flagged auctions with 63 "
                   f"sessions forward, below the floor of {FLOOR}; no rate prints")
    else:
        verdict = (f"{main['word']} -- "
                   + ("the contrarian read" if main["word"] == C.PASS else "stress flag only")
                   + f": median 3m change {C.f2(main['m3'], 1, ' bp')}, falls in "
                   f"{C.sh(main['hit'])} of {main['n']} (rule: median < 0 and >= 60%)")
    cand = ev["Pseudo-tail, top decile (candidate only)"]
    body = [f"Coupon auctions held {auc[0]['day'] if auc else 'n/a'} to "
            f"{auc[-1]['day'] if auc else 'n/a'}: {len(rows)} (nominal {len(nominal)}, "
            f"TIPS {len(rows) - len(nominal)}).",
            "",
            "| Set | Flagged with 3m forward | Distinct months | Median 1m (bp) | Median 3m (bp) | Falls, 3m | Rule |",
            "|---|---|---|---|---|---|---|"]
    for k, e in ev.items():
        rule = ("n/a" if k.startswith("Every") else e["word"])
        body.append(f"| {k} | {e['n']} | {e['months']} | {C.f2(e['m1'], 1)} | "
                    f"{C.f2(e['m3'], 1)} | {C.sh(e['hit'])} | {rule} |")
    body += ["", f"The pseudo-tail candidate reads **{cand['word']}** under the same "
             "rule; as a candidate it grants nothing, and a real tail needs a "
             "when-issued source (G-32)."]
    last = max((r["day"] for r in rows if r["d10_3m_bp"] is not None), default=None)
    return {
        "item": ITEM, "title": "coupon auction absorption against the 10-year's next three months",
        "as_of": f"{auc[-1]['day'] if auc else 'n/a'} (latest auction); last with 63 "
                 f"sessions forward {last}",
        "window": f"{auc[0]['day'] if auc else 'n/a'} to {auc[-1]['day'] if auc else 'n/a'}",
        "n": main["n"],
        "statistic": "median forward 21- and 63-session change in DGS10 after flagged "
                     "auctions, and the share that fell over 63",
        "pass_rule": ("the register's: median forward 3m 10y change negative with "
                      ">= 60% hit rate, else stress flag only; on ABS_STRESS as G-32 "
                      "defines it, the pseudo-tail a candidate. Pre-registered by "
                      f"this first edition: DGS10 close to close, floor {FLOOR}"),
        "verdict": verdict,
        "rights": ("PASS: the contrarian read, the overlay queue's position #2 after "
                   "the gate, and an input to rule A-3. FAIL: the stress flag only "
                   "(narrow, display). " + C.RIGHTS_NOTE),
        "sources": ["TreasuryDirect securities search API (no key), "
                    "dateFieldName=competitiveAuctionCloseDate, one request a year "
                    f"from {START}; results never revised",
                    "FRED graph CSV (no key): DGS2, DGS3, DGS5, DGS7, DGS10, DGS20, DGS30",
                    "ABS_STRESS: altdata.absorption.abs_stress, the live rule"],
        "source_mode": mode, "body": body, "episodes": rows,
        "caveats": ["The box re-run reads the same public sources (the calibration "
                    "rule), not the store.",
                    "Auctions of one week share most of a 63-session window, so the "
                    "flagged auctions are not independent; the distinct-month count "
                    "is beside each set."]}


if __name__ == "__main__":
    raise SystemExit(C.cli(ITEM, load_public, study))
