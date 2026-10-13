"""
SR-38 -- THE RETURN-ATTRIBUTION LENS, THE REVISION LINE, EY MINUS THE BILL
(signal-triage batch 4, ST4-02).

    from altdata import return_attribution as ra
    a = ra.attribution(st, cutoff)        # the 12-month split, EY minus the bill
    v = ra.revisions(st, cutoff)          # the forward-EPS revision line
    ra.attribution_lines(a); ra.revision_line(v)

    python -m altdata.return_attribution  # print both from the store

Config: config/ai_fcf.yaml (`attribution`, `revision`).

THE CLAIM BEING WATCHED (the entry's source, HSBC AM on a Bloomberg chart, 6 Oct
2026): the S&P 500 up ~10% YTD on blended forward EPS up ~28% and a forward P/E
down ~14% -- the resilience is earnings, not multiple.

THE SPLIT. Price = earnings x multiple, exact in logs:

    ln(P1/P0) = ln(E1/E0) + ln(M1/M0)

over the 12 months to the latest month the earnings are stored for. TRAILING
earnings (Shiller's monthly S&P Composite file: the month's average price and the
trailing twelve-month earnings), LABELLED trailing. Earnings's share of the
return is ln(E1/E0) / ln(P1/P0), printed only when the return is large enough to
divide by.

THE FORWARD SPLIT (13 Oct 2026). S&P DJI's forward twelve-month bottom-up
operating EPS, from the operator's monthly drop of sp-500-eps-est.xlsx
(altdata/sources/spdji.py; the host refuses non-browser clients, so nothing is
fetched). The same identity over the stored drops: the latest drop against the
one nearest twelve months before it -- or, until a drop that old is stored, the
earliest, with its span printed. One drop prints the forward EPS and the forward
P/E and says the split needs a second; none prints "awaiting the first drop".

EY MINUS THE BILL. The trailing earnings yield at the S&P 500's last close
(yfinance ^GSPC) against its latest stored trailing earnings, less the 3-month
bill (FRED DTB3), in percentage points. EY minus Baa needs a Baa yield, which is
not stored: named absent.

THE REVISION LINES. The INDEX's line (13 Oct 2026) reads S&P DJI's drops: the
latest drop's four forward quarters against the SAME four quarters in the drop
nearest one and three months before -- a revision, not the roll of the window
onto a later quarter -- and prints "awaiting the first drop" before one exists,
"revisions need a second" with one. The nine AI names' own consensus is logged
nightly (yf.forward_eps) and still prints beside it, labelled as the names':
their 4- and 13-week changes and the median, with how much history each window
has.

Report-only (batch 4): the revision line is a narrow-flag candidate after a
quarter of history; nothing here is a trigger or a book rule.
"""

from __future__ import annotations

import datetime as dt
import math
from statistics import median
from typing import Any, Optional

from .ai_fcf import load_config, tagged


def _pts(st, key: str, cutoff: Optional[str],
         instrument: Optional[str] = None) -> list[tuple[str, float]]:
    rows = {str(r["observed_at"])[:10]: float(r["value_num"])
            for r in st.as_of(key, cutoff, instrument) if r.get("value_num") is not None}
    return sorted(rows.items())


def _months_back(month: str, n: int) -> str:
    d = dt.date.fromisoformat(month)
    y, m = divmod(d.year * 12 + d.month - 1 - n, 12)
    return dt.date(y, m + 1, 1).isoformat()


def attribution(st, cutoff: Optional[str] = None, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or load_config()
    a = cfg.get("attribution") or {}
    out: dict[str, Any] = {"tag": cfg.get("tag") or "", "absent": a.get("absent") or {},
                           "split": None, "ey": None}
    p = dict(_pts(st, a.get("price_key") or "shiller.sp_price", cutoff))
    e = dict(_pts(st, a.get("earnings_key") or "shiller.sp_earnings", cutoff))
    n = int(a.get("months") or 12)
    both = sorted(m for m in set(p) & set(e) if e[m] > 0 and p[m] > 0)
    end = next((m for m in reversed(both) if _months_back(m, n) in both), None)
    if end is None:
        out["split_reason"] = ("the stored S&P price and trailing earnings do not span "
                               f"{n} months")
    else:
        start = _months_back(end, n)
        lp = math.log(p[end] / p[start])
        le = math.log(e[end] / e[start])
        lm = lp - le
        out["split"] = {"start": start, "end": end, "months": n,
                        "price_pct": 100 * (math.exp(lp) - 1),
                        "earnings_pct": 100 * (math.exp(le) - 1),
                        "multiple_pct": 100 * (math.exp(lm) - 1),
                        "earnings_share": (le / lp) if abs(lp) >= 0.01 else None,
                        "pe_start": p[start] / e[start], "pe_end": p[end] / e[end]}
    # EY minus the bill, at the index's last close.
    idx = _pts(st, a.get("index_key") or "yfinance.mkt_gspc", cutoff)
    bill = _pts(st, a.get("bill_key") or "fred.tbill_3m", cutoff)
    if e and idx and bill:
        em = max(e)
        ey = 100.0 * e[em] / idx[-1][1]
        out["ey"] = {"ey_pct": ey, "index": idx[-1][1], "index_day": idx[-1][0],
                     "earnings_month": em, "bill_pct": bill[-1][1],
                     "bill_day": bill[-1][0], "gap_pp": ey - bill[-1][1]}
    else:
        out["ey_reason"] = "the index close, the trailing earnings or the bill is not stored"
    out["forward"] = forward(st, cutoff, cfg)
    return out


# ---------------------------------------------------------------------------
# THE FORWARD SERIES -- S&P DJI's drops (altdata/sources/spdji.py)
# ---------------------------------------------------------------------------
def _awaiting() -> str:
    from .sources import spdji                                  # noqa: PLC0415
    return spdji.AWAITING


def forward(st, cutoff: Optional[str] = None, cfg: Optional[dict] = None) -> dict:
    """The forward split from the stored drops, or why it is not read."""
    cfg = cfg or load_config()
    f = cfg.get("forward") or {}
    drops = _pts(st, f.get("forward_key") or "spdji.fwd12m_op_eps", cutoff)
    if not drops:
        return {"state": "awaiting", "reason": _awaiting()}
    idx = _pts(st, (cfg.get("attribution") or {}).get("index_key")
               or "yfinance.mkt_gspc", cutoff)

    def close_on(day: str) -> Optional[tuple[str, float]]:
        got = [x for x in idx if x[0] <= day]
        return got[-1] if got else None
    end_day, e1 = drops[-1]
    out: dict[str, Any] = {"state": "one_drop", "drops": len(drops), "end": end_day,
                           "eps_end": e1}
    p1 = close_on(end_day)
    if p1 and e1 > 0:
        out.update({"index_end": p1[1], "index_end_day": p1[0], "pe_end": p1[1] / e1})
    if len(drops) < 2:
        return out
    # The start: the drop nearest twelve months before the latest; until one is
    # that old, the earliest, and the line prints the span it covers.
    months = int(f.get("months") or 12)
    target = _months_back(end_day[:8] + "01", months)
    older = drops[:-1]
    full = any(d[0][:7] <= target[:7] for d in older)
    start = (min(older, key=lambda d: abs((dt.date.fromisoformat(d[0])
                                           - dt.date.fromisoformat(target)).days))
             if full else older[0])
    p0 = close_on(start[0])
    out.update({"state": "split" if (p0 and p1) else "no_index", "start": start[0],
                "eps_start": start[1], "full_year": full,
                "span_days": (dt.date.fromisoformat(end_day)
                              - dt.date.fromisoformat(start[0])).days})
    if p0 and p1 and start[1] > 0 and e1 > 0:
        lp, le = math.log(p1[1] / p0[1]), math.log(e1 / start[1])
        out.update({"price_pct": 100 * (math.exp(lp) - 1),
                    "earnings_pct": 100 * (math.exp(le) - 1),
                    "multiple_pct": 100 * (math.exp(lp - le) - 1),
                    "pe_start": p0[1] / start[1]})
    else:
        out["state"] = "no_index"
    return out


def forward_line(fw: dict, tag: str) -> str:
    if fw["state"] == "awaiting":
        return f"The forward split: {fw['reason']} {tag}."
    head = (f"S&P 500 forward twelve-month operating EPS (S&P DJI, bottom-up, as of "
            f"{fw['end']}): ${fw['eps_end']:.2f}")
    if fw.get("pe_end"):
        head += (f", a forward P/E of {fw['pe_end']:.1f} at the "
                 f"{fw['index_end_day']} close")
    if fw["state"] == "one_drop":
        return f"{head}; the forward split needs a second drop {tag}."
    if fw["state"] == "no_index":
        return (f"{head}; the forward split is not read: no S&P 500 close is stored "
                f"on or before {fw['start']} {tag}.")
    span = ("12 months" if fw["full_year"] else
            f"{fw['span_days']} days (the stored drops' span, not yet twelve months)")
    return (f"{head}. Over {span} from the {fw['start']} drop: price "
            f"{fw['price_pct']:+.1f}%, of which forward earnings "
            f"{fw['earnings_pct']:+.1f}% and the forward multiple "
            f"{fw['multiple_pct']:+.1f}% (forward P/E {fw['pe_start']:.1f} to "
            f"{fw['pe_end']:.1f}) {tag}.")


def index_revisions(st, cutoff: Optional[str] = None,
                    cfg: Optional[dict] = None) -> dict:
    """The latest drop's four forward quarters against the same four quarters in
    an earlier drop, per window -- a revision, never the window's roll."""
    import json as _json                                        # noqa: PLC0415
    cfg = cfg or load_config()
    f = cfg.get("forward") or {}
    recs = [(str(r["observed_at"])[:10], r.get("value_text"))
            for r in st.as_of(f.get("drop_key") or "spdji.eps_drop", cutoff)]
    recs = [x for x in recs if x[1]]
    if not recs:
        return {"state": "awaiting", "reason": _awaiting(), "windows": {}}
    end_day, rec = recs[-1]
    four = _json.loads(rec).get("forward_quarters") or []
    qkey = f.get("quarter_key") or "spdji.op_eps_est_q"
    by_q = {q: dict(_pts(st, qkey, cutoff, q)) for q in four}
    now = [by_q[q].get(end_day) for q in four]
    level = sum(now) if four and all(v is not None for v in now) else None
    out: dict[str, Any] = {"state": "one_drop" if len(recs) < 2 else "read",
                           "end": end_day, "quarters": four, "windows": {},
                           "level": level}
    if len(recs) < 2:
        return out
    days = [d for d, _ in recs[:-1]]
    for lab, n in (f.get("revision_windows_days")
                   or {"1-month": 28, "3-month": 91}).items():
        ref = (dt.date.fromisoformat(end_day) - dt.timedelta(days=int(n))).isoformat()
        base = [d for d in days if d <= ref]
        if not base:
            out["windows"][lab] = {"pct": None, "why": "no drop that old"}
            continue
        then = [by_q[q].get(base[-1]) for q in four]
        if level is None or any(v is None for v in then) or not sum(then):
            out["windows"][lab] = {"pct": None, "since": base[-1],
                                   "why": f"the {base[-1]} drop lacks one of the "
                                          f"four quarters"}
            continue
        out["windows"][lab] = {"pct": 100.0 * (level / sum(then) - 1),
                               "since": base[-1]}
    return out


def index_revision_line(ix: dict, tag: str) -> str:
    if ix["state"] == "awaiting":
        return f"S&P 500 forward-EPS revisions: {ix['reason']} {tag}."
    qs = f"{ix['quarters'][0]} to {ix['quarters'][-1]}" if ix["quarters"] else "—"
    head = (f"S&P 500 forward-EPS revisions (S&P DJI, bottom-up, the four quarters "
            f"{qs}, as of {ix['end']})")
    if ix["state"] == "one_drop":
        return f"{head}: the first drop; revisions need a second {tag}."
    parts = [f"{lab} {w['pct']:+.1f}% (since the {w['since']} drop)"
             if w.get("pct") is not None else f"{lab} not read ({w['why']})"
             for lab, w in ix["windows"].items()]
    return f"{head}: " + "; ".join(parts) + f" {tag}."


def _month_name(m: str) -> str:
    return dt.date.fromisoformat(m).strftime("%B %Y")


def attribution_lines(a: dict) -> list[str]:
    tag, out = a["tag"], []
    s = a.get("split")
    if s:
        share = ("" if s["earnings_share"] is None else
                 f"; earnings growth is {100 * s['earnings_share']:.0f}% of the "
                 f"return in logs")
        out.append(f"The S&P 500 over the {s['months']} months to "
                   f"{_month_name(s['end'])}: price {s['price_pct']:+.1f}%, of which "
                   f"trailing earnings {s['earnings_pct']:+.1f}% and the multiple "
                   f"{s['multiple_pct']:+.1f}% (trailing P/E {s['pe_start']:.1f} to "
                   f"{s['pe_end']:.1f}){share} {tag}.")
    else:
        out.append(f"The return split is not read: {a.get('split_reason')} {tag}.")
    y = a.get("ey")
    if y:
        out.append(f"Trailing earnings yield {y['ey_pct']:.2f}% (the S&P 500 at its "
                   f"{y['index_day']} close against the trailing earnings to "
                   f"{_month_name(y['earnings_month'])}) less the 3-month bill "
                   f"{y['bill_pct']:.2f}% ({y['bill_day']}): {y['gap_pp']:+.2f} "
                   f"percentage points {tag}.")
    else:
        out.append(f"Earnings yield less the bill is not read: {a.get('ey_reason')}.")
    fw = a.get("forward") or {"state": "awaiting", "reason": _awaiting()}
    out.append(forward_line(fw, tag))
    ab = a.get("absent") or {}
    out.append(("Trailing, not forward. " if fw["state"] == "awaiting" else
                "The twelve-month split above is trailing. ")
               + "Not available: "
               + "; ".join(ab[k] for k in ("ey_minus_baa", "ai_share") if ab.get(k))
               + ".")
    return tagged(out, tag)


def revisions(st, cutoff: Optional[str] = None, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or load_config()
    r = cfg.get("revision") or {}
    key = r.get("key") or "yf.forward_eps"
    wins = r.get("windows_days") or {"4-week": 28, "13-week": 91}
    end = (cutoff or dt.datetime.now(dt.timezone.utc).isoformat())[:10]
    names = []
    for sym in r.get("names") or []:
        pts = [x for x in _pts(st, key, cutoff, sym) if x[0] <= end]
        row: dict[str, Any] = {"symbol": sym, "n": len(pts)}
        if pts:
            row["level"], row["day"] = pts[-1][1], pts[-1][0]
            for lab, days in wins.items():
                ref = (dt.date.fromisoformat(pts[-1][0])
                       - dt.timedelta(days=int(days))).isoformat()
                base = [v for d, v in pts if d <= ref]
                row[lab] = (100.0 * (pts[-1][1] / base[-1] - 1)
                            if base and base[-1] else None)
        names.append(row)
    med = {lab: (median([n[lab] for n in names if n.get(lab) is not None])
                 if any(n.get(lab) is not None for n in names) else None)
           for lab in wins}
    have = {lab: sum(1 for n in names if n.get(lab) is not None) for lab in wins}
    return {"names": names, "median": med, "covered": have, "of": len(names),
            "windows": list(wins), "tag": cfg.get("tag") or "",
            "index": index_revisions(st, cutoff, cfg)}


def revision_line(v: dict) -> str:
    parts = []
    for lab in v["windows"]:
        m = v["median"].get(lab)
        parts.append(f"{lab} median {m:+.1f}% ({v['covered'][lab]} of {v['of']} names)"
                     if m is not None else
                     f"{lab} not read (no name has the history)")
    return (f"Forward-EPS revisions, the nine AI names' consensus (not the index's): "
            + "; ".join(parts) + f" {v['tag']}.")


def revision_table(v: dict) -> Optional[dict]:
    rows = [[n["symbol"], f"{n['level']:.2f}" if n.get("level") is not None else "—",
             *[f"{n[lab]:+.1f}%" if n.get(lab) is not None else "—"
               for lab in v["windows"]], n.get("day") or "—"]
            for n in v["names"] if n["n"]]
    if not rows:
        return None
    return {"columns": ["Name", "Forward EPS", *[f"{lab} change" for lab in v["windows"]],
                        "As of"], "rows": rows}


def data(a: dict, v: Optional[dict] = None) -> dict:
    s, y = a.get("split") or {}, a.get("ey") or {}
    out = {"basis": "trailing",
           "price_pct": None if not s else round(s["price_pct"], 1),
           "earnings_pct": None if not s else round(s["earnings_pct"], 1),
           "multiple_pct": None if not s else round(s["multiple_pct"], 1),
           "ey_minus_bill_pp": None if not y else round(y["gap_pp"], 2),
           "tag": a["tag"]}
    fw = a.get("forward") or {}
    out["forward_eps"] = None if fw.get("eps_end") is None else round(fw["eps_end"], 2)
    out["forward_pe"] = None if fw.get("pe_end") is None else round(fw["pe_end"], 1)
    if fw.get("state") == "split":
        out["forward_split"] = {k: round(fw[k], 1) for k in
                                ("price_pct", "earnings_pct", "multiple_pct")}
    if v:
        out["revision_median"] = {k: None if m is None else round(m, 1)
                                  for k, m in v["median"].items()}
        out["index_revision"] = index_revision_data(v)
    return out


def index_revision_data(v: dict) -> dict:
    return {lab: None if w.get("pct") is None else round(w["pct"], 1)
            for lab, w in ((v.get("index") or {}).get("windows") or {}).items()}


def _main() -> int:
    from . import observations                                  # noqa: PLC0415
    with observations.ObservationStore() as st:
        a, v = attribution(st), revisions(st)
    for ln in attribution_lines(a) + [index_revision_line(v["index"], v["tag"]),
                                      revision_line(v)]:
        print(ln.encode("ascii", "replace").decode())
    return 0


if __name__ == "__main__":                                      # pragma: no cover
    raise SystemExit(_main())
