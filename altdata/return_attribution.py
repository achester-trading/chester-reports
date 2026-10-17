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
trailing twelve-month earnings), LABELLED trailing: the entry's forward split
needs S&P DJI's forward operating EPS, which no writer can read (the site
refuses every non-browser client; a writer never passes for a browser), so it is
named absent rather than substituted. Earnings's share of the return is
ln(E1/E0) / ln(P1/P0), printed only when the return is large enough to divide
by.

EY MINUS THE BILL. The trailing earnings yield at the S&P 500's last close
(yfinance ^GSPC) against its latest stored trailing earnings, less the 3-month
bill (FRED DTB3), in percentage points. EY minus Baa needs a Baa yield, which is
not stored: named absent.

THE REVISION LINE. The index's forward estimate is the absent S&P DJI series. The
nine AI names' own consensus is logged nightly (yf.forward_eps), so the line
prints their 4- and 13-week changes and the median -- labelled as the names', not
the index's -- and says how much history each window has.

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
    return out


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
    ab = a.get("absent") or {}
    out.append("Trailing, not forward. Not available: "
               + "; ".join(ab[k] for k in ("forward_eps", "ey_minus_baa", "ai_share")
                           if ab.get(k)) + ".")
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
            "absent": ((cfg.get("attribution") or {}).get("absent") or {})
            .get("forward_eps")}


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
    if v:
        out["revision_median"] = {k: None if m is None else round(m, 1)
                                  for k, m in v["median"].items()}
    return out


def _main() -> int:
    from . import observations                                  # noqa: PLC0415
    with observations.ObservationStore() as st:
        a, v = attribution(st), revisions(st)
    for ln in attribution_lines(a) + [revision_line(v)]:
        print(ln.encode("ascii", "replace").decode())
    return 0


if __name__ == "__main__":                                      # pragma: no cover
    raise SystemExit(_main())
