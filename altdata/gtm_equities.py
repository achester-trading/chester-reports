"""
The J.P. Morgan Guide batch, part 2 -- the equity items (17 Oct 2026).

    python -m altdata.gtm_equities show [--db PATH] [--as-of T]

The change order of 3 Oct 2026 (docs/change-order-jpm-gtm-2026-10-03.md) and the
rulings of 17 Oct:

  GTM-3   the concentration twin: the top 10's share of index market cap beside
          its share of index earnings, and the forward P/E of the top 10, of the
          other 490 and of the index against their own averages. Adopted through
          the Top & Bottom overlay's intake queue, one candidate at a time, so it
          is a REPORT-ONLY exhibit; its queue entry is a draft
          (config/tb_intake_queue.yaml) and grants nothing.
  GTM-4   the AI five-bucket decomposition (config/ai_buckets.yaml, slide 11)
          and the hyperscaler cash-flow bridge (operating cash flow less capex,
          from EDGAR's XBRL frames, beside the Guide's capex path). A modifier on
          Factor I, read by a human.
  GTM-10  the sector rows: each sector ETF's daily return against the 10-year's
          daily change, over one and five years, beside the Guide's sector
          figures. A modifier.

Every figure only the Guide has is a sourced figure (config/gtm.yaml, read through
altdata.gtm.sourced) with its slide and as-of, never recomputed. A measure whose
inputs are not ALL stored is not computed: its cell says what is missing and the
Guide's figure prints beside it, labelled -- never a partial computation presented
as the whole. Nothing here writes, fetches or calls a model; nothing enters a
composite, a trigger or the overlay.
"""

from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path
from typing import Optional

import yaml

from . import gtm

log = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent
BUCKETS_PATH = REPO / "config" / "ai_buckets.yaml"


def buckets_config(path: Optional[Path] = None) -> dict:
    with open(path or BUCKETS_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _day(cutoff: str) -> str:
    return str(cutoff)[:10]


def _back(day: str, days: int) -> str:
    return (dt.date.fromisoformat(day) - dt.timedelta(days=days)).isoformat()


def _share_classes() -> dict:
    """The one share-class map (config/st_r5_t1_rest.yaml), so GTM-3's top 10
    and item 31's are the same ten issuers."""
    from . import st_r5_t1_rest as tr                           # noqa: PLC0415
    return (tr.config().get("concentration") or {}).get("share_classes") or {}


def _at_or_before(pts: list[tuple[str, float]], day: str,
                  max_age_days: Optional[int] = None) -> Optional[tuple[str, float]]:
    """The newest (day, value) on or before `day`, within the age bound."""
    hit = None
    for d, v in pts:
        if d <= day:
            hit = (d, v)
        else:
            break
    if hit and max_age_days is not None and hit[0] < _back(day, max_age_days):
        return None
    return hit


# ---------------------------------------------------------------------------
# The constituent store, by day
# ---------------------------------------------------------------------------
def weights_by_day(st, key: str, cutoff: str) -> dict[str, dict[str, float]]:
    """{day: {ticker: weight %}} for every holdings day knowable at the cutoff."""
    out: dict[str, dict[str, float]] = {}
    if st is None:
        return out
    try:
        tickers = st.instruments(key)
    except Exception:                                          # noqa: BLE001
        return out
    for tk in tickers:
        for d, v in gtm.points(st, key, cutoff, tk):
            out.setdefault(d, {})[tk] = v
    return out


def top_issuers(weights_pct: dict[str, float], classes: dict,
                n: int) -> list[tuple[str, float, list[str]]]:
    """[(issuer, weight %, [its tickers])], the n largest by weight; a second
    share class counts with its first."""
    by: dict[str, list] = {}
    for tk, w in weights_pct.items():
        iss = classes.get(tk, tk)
        e = by.setdefault(iss, [0.0, []])
        e[0] += w
        e[1].append(tk)
    ranked = sorted(by.items(), key=lambda kv: (-kv[1][0], kv[0]))
    return [(iss, round(e[0], 6), sorted(e[1])) for iss, e in ranked[:n]]


# ---------------------------------------------------------------------------
# GTM-3: the concentration twin
# ---------------------------------------------------------------------------
def twin_on(weights_pct: dict[str, float], top: list, trailing: dict[str, float],
            forward: dict[str, float], idx_trailing_pe: Optional[float],
            idx_forward_pe: Optional[float]) -> dict:
    """One day's twin from that day's inputs. `trailing` and `forward` are each
    name's P/E on the day ({ticker: x}); a name without one is missing.

    Cap share over P/E is earnings share, so with every weight a fraction of the
    index:  earnings share of the top 10 = sum(w_i / PE_i) x PE_index, and the
    top 10's forward P/E = W / sum(w_i / fPE_i). The other 490 back the top 10
    out of the index: (1 - W) / (1 / fPE_index - sum(w_i / fPE_i))."""
    names = [tk for _, _, tks in top for tk in tks]
    w = {tk: weights_pct[tk] / 100.0 for tk in names}
    W = sum(w.values())
    out = {"cap_share": round(100 * W, 4), "names": names}
    miss_t = [tk for tk in names if not trailing.get(tk) or trailing[tk] <= 0]
    miss_f = [tk for tk in names if not forward.get(tk) or forward[tk] <= 0]
    out["missing_trailing"], out["missing_forward"] = miss_t, miss_f
    out["earn_share"] = None
    if not miss_t and idx_trailing_pe:
        out["earn_share"] = round(100 * sum(w[tk] / trailing[tk] for tk in names)
                                  * idx_trailing_pe, 4)
    out["pe_top"] = out["pe_other"] = None
    out["pe_index"] = round(idx_forward_pe, 4) if idx_forward_pe else None
    if not miss_f:
        inv = sum(w[tk] / forward[tk] for tk in names)
        out["pe_top"] = round(W / inv, 4) if inv > 0 else None
        if idx_forward_pe and idx_forward_pe > 0:
            rest = 1.0 / idx_forward_pe - inv
            out["pe_other"] = round((1 - W) / rest, 4) if rest > 0 else None
    return out


def _index_pe_series(st, cutoff: str, c: dict) -> tuple[dict, list, list]:
    """(the S&P 500's closes by day, Shiller's earnings by month, S&P DJI's
    forward EPS by day)."""
    closes = dict(gtm.points(st, c["index_close_key"], cutoff))
    earn = [(d[:7], v) for d, v in gtm.points(st, c["shiller_earnings_key"], cutoff)]
    fwd = gtm.points(st, c["index_forward_eps_key"], cutoff)
    return closes, earn, fwd


def _index_close(closes: dict, day: str) -> Optional[tuple[str, float]]:
    return _at_or_before(sorted(closes.items()), day, 7)


def concentration_twin(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or gtm.config()
    c = cfg["concentration_twin"]
    days = weights_by_day(st, c["weight_key"], cutoff)
    if not days:
        return {"state": "absent", "absent_reason":
                "no SPY holdings are stored (the constituent writer)"}
    classes = _share_classes()
    n = int(c["top_n"])
    max_age = int(c["max_age_days"])
    closes, earn, fwd_eps = _index_pe_series(st, cutoff, c)
    pe_cache: dict[tuple[str, str], list] = {}

    def pe_pts(key: str, tk: str) -> list:
        if (key, tk) not in pe_cache:
            pe_cache[(key, tk)] = gtm.points(st, key, cutoff, tk)
        return pe_cache[(key, tk)]

    series = []
    for day in sorted(days):
        top = top_issuers(days[day], classes, n)
        names = [tk for _, _, tks in top for tk in tks]
        tr = {tk: (_at_or_before(pe_pts(c["trailing_pe_key"], tk), day, max_age)
                   or (None, None))[1] for tk in names}
        fw = {tk: (_at_or_before(pe_pts(c["forward_pe_key"], tk), day, max_age)
                   or (None, None))[1] for tk in names}
        ic = _index_close(closes, day)
        e = [x for x in earn if x[0] <= day[:7]]
        f = _at_or_before(fwd_eps, day, 45)
        idx_tpe = ic[1] / e[-1][1] if ic and e and e[-1][1] > 0 else None
        idx_fpe = ic[1] / f[1] if ic and f and f[1] > 0 else None
        t = twin_on(days[day], top, tr, fw, idx_tpe, idx_fpe)
        t.update(day=day, issuers=[i for i, _, _ in top],
                 index_earnings_month=e[-1][0] if e else None,
                 index_forward_eps_day=f[0] if f else None,
                 index_close_day=ic[0] if ic else None)
        series.append(t)
    latest = series[-1]
    age = (dt.date.fromisoformat(_day(cutoff))
           - dt.date.fromisoformat(latest["day"])).days
    if age > max_age:
        return {"state": "absent", "absent_reason":
                f"the newest holdings are of {latest['day']}, {age} days old"}
    own = {}
    for k in ("pe_top", "pe_other", "pe_index"):
        h = [(s["day"], s[k]) for s in series if s.get(k)]
        own[k] = ({"average": round(sum(v for _, v in h) / len(h), 4), "n": len(h),
                   "from": h[0][0], "to": h[-1][0],
                   "short": len(h) < int(c["min_own_history_days"]),
                   "pct_of_average": (round(100 * latest[k] / (sum(v for _, v in h)
                                                               / len(h)), 2)
                                      if latest.get(k) else None)}
                  if h else None)
    return {"state": "ok", "day": latest["day"], "latest": latest, "own": own,
            "days": len(series)}


def consensus_names(cfg: Optional[dict] = None, db_path: Optional[str] = None,
                    cutoff: Optional[str] = None) -> list[str]:
    """The names the consensus log adds for GTM-3 and GTM-4: the declared ones
    (the hyperscaler bucket's members outside its universe) and the tickers of
    the newest holdings' top `consensus_top_n` issuers. Never raises; with no
    store it is the declared list alone."""
    cfg = cfg or gtm.config()
    c = cfg["concentration_twin"]
    out = list(c.get("consensus_static") or [])
    try:
        from . import observations, session                    # noqa: PLC0415
        cut = cutoff or session.utc_iso(timespec="microseconds")
        with observations.ObservationStore(db_path) as st:
            from . import st_r5_t1_rest as tr                   # noqa: PLC0415
            h = tr.holdings(st, cut, c["weight_key"])
        for _, _, tks in top_issuers(h["weights_pct"], _share_classes(),
                                     int(c.get("consensus_top_n", 12))):
            out += tks
    except Exception:                                          # noqa: BLE001
        log.info("consensus_names: the holdings are not readable; the declared "
                 "names only", exc_info=True)
    seen, res = set(), []
    for tk in out:
        if tk not in seen:
            seen.add(tk)
            res.append(tk)
    return res


# ---------------------------------------------------------------------------
# GTM-4: the AI buckets and the hyperscaler cash-flow bridge
# ---------------------------------------------------------------------------
def _closes(st, cfg: dict, tk: str, cutoff: str) -> list[tuple[str, float]]:
    pts = gtm.points(st, cfg["ai_buckets"]["close_key"], cutoff, tk)
    if pts:
        return pts
    return gtm.points(st, f"yfinance.mkt_{tk.lower().replace('-', '_')}", cutoff)


def bucket_reads(st, cutoff: str, cfg: Optional[dict] = None,
                 bcfg: Optional[dict] = None) -> dict:
    """Each bucket's weight, year-to-date price return and NTM P/E, computed only
    where every member is stored; else None with what is missing."""
    cfg = cfg or gtm.config()
    bcfg = bcfg or buckets_config()
    a = cfg["ai_buckets"]
    from . import st_r5_t1_rest as tr                           # noqa: PLC0415
    h = tr.holdings(st, cutoff, a["weight_key"]) if st is not None else \
        {"day": None, "weights_pct": {}}
    day = h["day"]
    rows = []
    for b in bcfg.get("buckets") or []:
        r = {"id": b["id"], "label": b["label"], "definition": b["definition"],
             "weight": None, "ytd": None, "ntm_pe": None, "missing": {}}
        mem = b.get("members")
        if not mem:
            r["reason"] = b.get("members_reason") or "no members declared"
            rows.append(r)
            continue
        if not day:
            r["reason"] = "no SPY holdings are stored"
            rows.append(r)
            continue
        w = {tk: h["weights_pct"].get(tk) for tk in mem}
        r["missing"]["weight"] = [tk for tk, v in w.items() if v is None]
        if not r["missing"]["weight"]:
            r["weight"] = round(sum(w.values()), 4)
        start = f"{int(day[:4]) - 1}-12-31"
        rets, miss = {}, []
        for tk in mem:
            pts = _closes(st, cfg, tk, cutoff)
            end = _at_or_before(pts, day, 7)
            base = _at_or_before(pts, start, 7)
            if not end or not base or base[1] <= 0:
                miss.append(tk)
                continue
            rets[tk] = end[1] / base[1] - 1
        r["missing"]["ytd"] = miss
        if not miss and not r["missing"]["weight"]:
            # Market-weighted from the start of the year: each member's starting
            # weight is today's over its growth, so the composite is the change
            # in the members' combined value.
            w0 = {tk: w[tk] / (1 + rets[tk]) for tk in mem}
            r["ytd"] = round(100 * sum(w0[tk] * rets[tk] for tk in mem)
                             / sum(w0.values()), 4)
        fpe, missf = {}, []
        for tk in mem:
            x = _at_or_before(gtm.points(st, a["forward_pe_key"], cutoff, tk), day, 7)
            if not x or x[1] <= 0:
                missf.append(tk)
            else:
                fpe[tk] = x[1]
        r["missing"]["ntm_pe"] = missf
        if not missf and not r["missing"]["weight"]:
            r["ntm_pe"] = round(sum(w.values()) / sum(w[tk] / fpe[tk] for tk in mem), 4)
        rows.append(r)
    complete = all(r["weight"] is not None for r in rows)
    total = None
    if complete:
        seen = {tk for b in bcfg["buckets"] for tk in (b.get("members") or [])}
        total = round(sum(h["weights_pct"].get(tk, 0.0) for tk in seen), 4)
    return {"day": day, "rows": rows, "total_weight": total}


def frame_year(end: str) -> int:
    """The calendar frame a fiscal year sits in: the year of its midpoint."""
    return (dt.date.fromisoformat(end[:10]) - dt.timedelta(days=182)).year


def cash_flow_bridge(st, cutoff: str, cfg: Optional[dict] = None,
                     bcfg: Optional[dict] = None) -> dict:
    """Per calendar frame from the first year: the five filers' operating cash
    flow, capex and the difference, in dollars, only where every filer has both;
    else the year names who lacks what."""
    cfg = cfg or gtm.config()
    bcfg = bcfg or buckets_config()
    a = cfg["ai_buckets"]
    br = bcfg["bridge"]
    filers = [f["ticker"] for f in br["filers"]]
    vals: dict[str, dict[int, dict[str, float]]] = {"ocf": {}, "capex": {}}
    for field, key in (("ocf", a["ocf_key"]), ("capex", a["capex_key"])):
        for tk in filers:
            for d, v in gtm.points(st, key, cutoff, tk):
                vals[field].setdefault(frame_year(d), {})[tk] = v
    last = int(_day(cutoff)[:4]) - 1
    years = sorted(set(range(int(br["first_year"]), last + 1))
                   | {y for y in set(vals["ocf"]) | set(vals["capex"])
                      if y >= int(br["first_year"])})
    rows = []
    for y in years:
        o, cx = vals["ocf"].get(y, {}), vals["capex"].get(y, {})
        lack = {"ocf": [tk for tk in filers if tk not in o],
                "capex": [tk for tk in filers if tk not in cx]}
        r = {"year": y, "lack": lack, "ocf": None, "capex": None, "fcf": None,
             "filers_ocf": len(o), "filers_capex": len(cx)}
        if not lack["ocf"]:
            r["ocf"] = sum(o.values())
        if not lack["capex"]:
            r["capex"] = sum(abs(v) for v in cx.values())
        if r["ocf"] is not None and r["capex"] is not None:
            r["fcf"] = r["ocf"] - r["capex"]
        rows.append(r)
    stored = any(r["filers_ocf"] or r["filers_capex"] for r in rows)
    return {"state": "ok" if stored else "absent", "rows": rows, "filers": filers,
            "absent_reason": None if stored else
            "no XBRL frames are stored (altdata.sources.edgar_xbrl; it needs the "
            "SEC contact)"}


# ---------------------------------------------------------------------------
# GTM-10: the sector rows
# ---------------------------------------------------------------------------
def rate_correlation(closes: list[tuple[str, float]], rate: list[tuple[str, float]],
                     window: int, min_coverage: float) -> dict:
    """The correlation of the last `window` sessions' daily price returns with
    the 10-year's daily change in basis points, on the days both are stored."""
    rets = [(d1, p1 / p0 - 1) for (d0, p0), (d1, p1) in zip(closes, closes[1:])
            if p0 > 0][-window:]
    rd = dict(rate)
    days = sorted(rd)
    prev = {days[i]: days[i - 1] for i in range(1, len(days))}
    xs, ys = [], []
    for d, r in rets:
        if d in rd and d in prev:
            xs.append(r)
            ys.append(100 * (rd[d] - rd[prev[d]]))
    need = int(round(window * min_coverage))
    c = gtm.pearson(xs, ys) if len(xs) >= need else None
    return {"corr": round(c, 4) if c is not None else None, "n": len(xs),
            "window": window, "reached": len(xs) >= need,
            "from": rets[0][0] if rets else None, "to": rets[-1][0] if rets else None}


def sector_rows(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or gtm.config()
    s = cfg["sector_rows"]
    rate = gtm.points(st, s["rate_key"], cutoff)
    rows = []
    for etf, sid in s["sectors"].items():
        cl = gtm.points(st, f"yfinance.mkt_{etf.lower()}", cutoff)
        r = {"etf": etf, "sector_id": sid}
        for name, win in s["windows"].items():
            r[name] = rate_correlation(cl, rate, int(win), float(s["min_coverage"]))
        rows.append(r)
    return {"rows": rows, "rate_key": s["rate_key"], "index_row": s["index_row"]}


# ---------------------------------------------------------------------------
# Everything, once per cutoff
# ---------------------------------------------------------------------------
def build(st, cutoff: str, db_path: Optional[str] = None,
          cfg: Optional[dict] = None) -> dict:
    cfg = cfg or gtm.config()
    db_path = db_path or (str(st.path) if getattr(st, "path", None) else None)
    return {"sourced": gtm.sourced(cutoff, db_path, cfg) if db_path else {},
            "twin": concentration_twin(st, cutoff, cfg),
            "buckets": bucket_reads(st, cutoff, cfg),
            "bridge": cash_flow_bridge(st, cutoff, cfg),
            "sectors": sector_rows(st, cutoff, cfg)}


def _main(argv: list[str]) -> int:
    import argparse  # noqa: PLC0415
    import json  # noqa: PLC0415
    from . import observations, session  # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.gtm_equities")
    ap.add_argument("cmd", choices=["show"])
    ap.add_argument("--db", default=None)
    ap.add_argument("--as-of", default=None)
    a = ap.parse_args(argv)
    cut = a.as_of or session.utc_iso(timespec="microseconds")
    with observations.ObservationStore(a.db) as st:
        b = build(st, cut, a.db)
    b.pop("sourced", None)
    print(json.dumps(b, indent=2, default=str, sort_keys=True)[:20000])
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(_main(sys.argv[1:]))
