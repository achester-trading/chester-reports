"""
The AI capex chain (signal-triage Batch 14, item 63 -- written as 56; ST-R6.63a;
ruled 20 Oct 2026, filed with F1-F8; b52-batch14-a2). Reads the store as of the
cutoff and decides nothing.

    reference(cfg)                 BNP Paribas's $100 of AI capex (August 2026), the
                                   standing dated table, its caveat and its source
    relative(st, cutoff, cfg)      the monthly capex-chain relative-performance line:
                                   each bucket's proxy basket over the window,
                                   against SPY, ranked lead to lag, beside the
                                   hyperscalers' filed capex growth
    python -m altdata.capex_chain show [--as-of ISO] [--db PATH]

REPORT ONLY (the order's Rights). The weights are BNP's high-level estimates,
printed as BNP's and dated; nothing here scores a bucket, opens a flag or writes
anything. The proxies are config/capex_chain.yaml's, each with its reason.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "config" / "capex_chain.yaml"


def config(path: Optional[Path] = None) -> dict:
    import yaml  # noqa: PLC0415
    return yaml.safe_load(Path(path or CONFIG_PATH).read_text(encoding="utf-8")) or {}


# ---------------------------------------------------------------------------
# The reference table
# ---------------------------------------------------------------------------
def reference(cfg: Optional[dict] = None) -> dict:
    """The table as rows, with its date, source and caveat. The buckets sum to
    the table's `per` (100); a part's dollars sum to its bucket's."""
    cfg = cfg if cfg is not None else config()
    ref = cfg.get("reference") or {}
    rows = []
    for b in ref.get("buckets") or []:
        rows.append({"id": b["id"], "label": b["label"], "usd": float(b["usd"]),
                     "level": "bucket"})
        for p in b.get("parts") or []:
            rows.append({"id": p["id"], "label": p["label"], "usd": float(p["usd"]),
                         "level": "part", "of": b["id"]})
    memo = [{"id": m["id"], "label": m["label"], "usd": float(m["usd"]),
             "approx": bool(m.get("approx")), "note": m.get("note")}
            for m in ref.get("memo") or []]
    total = round(sum(r["usd"] for r in rows if r["level"] == "bucket"), 2)
    return {"title": ref.get("title"), "dated": str(ref.get("dated")),
            "source": " ".join(str(ref.get("source") or "").split()),
            "caveat": " ".join(str(ref.get("caveat") or "").split()),
            "per": float(ref.get("per") or 100), "rows": rows, "memo": memo,
            "total": total}


def reference_table(ref: dict) -> dict:
    """The table as the stack prints one: columns and rows of text."""
    out = []
    for r in ref["rows"]:
        label = r["label"] if r["level"] == "bucket" else f"  {r['label']}"
        share = r["usd"] / ref["per"] * 100.0
        out.append([label, f"${r['usd']:g}", f"{share:.1f}%"])
    for m in ref["memo"]:
        out.append([m["label"], f"{'about ' if m['approx'] else ''}${m['usd']:g}",
                    m.get("note") or ""])
    return {"columns": [f"Of ${ref['per']:g} of AI capex (BNP Paribas, {ref['dated']})",
                        "Dollars", "Share"], "rows": out}


# ---------------------------------------------------------------------------
# The relative line
# ---------------------------------------------------------------------------
def _closes(st, key: str, cutoff: str) -> list[tuple[str, float]]:
    return sorted((str(r["observed_at"])[:10], float(r["value_num"]))
                  for r in st.as_of(key, cutoff) if r.get("value_num") is not None)


def _months_back(day: str, months: int) -> str:
    d = dt.date.fromisoformat(day)
    y, m = d.year, d.month - months
    while m <= 0:
        y, m = y - 1, m + 12
    last = [31, 29 if y % 4 == 0 and (y % 100 or y % 400 == 0) else 28, 31, 30, 31,
            30, 31, 31, 30, 31, 30, 31][m - 1]
    return dt.date(y, m, min(d.day, last)).isoformat()


def window_return(pts: list[tuple[str, float]], months: int, min_sessions: int
                  ) -> Optional[dict]:
    """The latest close against the close on or before `months` earlier, in
    percent, with the sessions between; None when either end is missing or the
    window holds fewer than `min_sessions`."""
    if not pts:
        return None
    end_day, end = pts[-1]
    start_day = _months_back(end_day, months)
    base = [p for p in pts if p[0] <= start_day]
    inside = [p for p in pts if start_day < p[0] <= end_day]
    if not base or len(inside) < min_sessions or base[-1][1] <= 0:
        return None
    return {"from": base[-1][0], "to": end_day, "sessions": len(inside),
            "pct": round((end / base[-1][1] - 1.0) * 100.0, 2)}


def basket_return(st, keys: list[str], cutoff: str, months: int, min_sessions: int
                  ) -> dict:
    """Equal weight across a bucket's proxies, each its own price return."""
    legs, missing = [], []
    for k in keys:
        w = window_return(_closes(st, k, cutoff), months, min_sessions)
        (legs.append({"key": k, **w}) if w else missing.append(k))
    if not legs or missing:
        return {"pct": None, "legs": legs, "missing": missing,
                "reason": f"not enough history: {', '.join(missing)}"}
    return {"pct": round(sum(x["pct"] for x in legs) / len(legs), 2), "legs": legs,
            "missing": [], "to": max(x["to"] for x in legs)}


def capex_growth(st, cutoff: str, cfg: dict) -> dict:
    """The hyperscalers' filed capex, the latest fiscal year all of them have
    filed against the year before: the sum's growth, in percent. Read from
    EDGAR's annual frames; guidance is not tracked."""
    rel = cfg.get("relative") or {}
    key, names = rel.get("capex_key", "edgar.xbrl_capex"), list(rel.get("capex_names") or [])
    by: dict[str, dict[int, float]] = {}
    for n in names:
        for r in st.as_of(key, cutoff, n):
            if r.get("value_num") is not None:
                by.setdefault(n, {})[int(str(r["observed_at"])[:4])] = float(r["value_num"])
    years = sorted(set.intersection(*[set(v) for v in by.values()])) if by and \
        len(by) == len(names) else []
    gap = " ".join(str(rel.get("guidance_gap") or "").split())
    if len(years) < 2:
        held = sorted(by)
        return {"pct": None, "gap": gap,
                "reason": f"{key}: two common fiscal years not held for all of "
                          f"{', '.join(names)} (held: {', '.join(held) or 'none'})"}
    y1, y0 = years[-1], years[-2]
    s1 = sum(by[n][y1] for n in names)
    s0 = sum(by[n][y0] for n in names)
    return {"pct": round((s1 / s0 - 1.0) * 100.0, 1), "year": y1, "prior": y0,
            "names": names, "key": key, "gap": gap}


def guidance(st, cutoff: str, cfg: dict) -> dict:
    """The hyperscalers' capex guidance beside the filed capex (A66): each name's
    newest 10-Q or 10-K guidance sentence, read from the stored records
    (altdata/sources/edgar_guidance.py). Report only."""
    names = list((cfg.get("relative") or {}).get("capex_names") or [])
    try:
        from .sources import edgar_guidance                     # noqa: PLC0415
        return edgar_guidance.guidance_line(st, cutoff, names)
    except Exception as exc:                                    # noqa: BLE001
        return {"lines": [], "footnotes": [], "fault": f"{type(exc).__name__}: {exc}"}


def relative(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    """Each bucket's basket against the benchmark over the window, ranked lead to
    lag; buckets without history are listed with their reason."""
    cfg = cfg if cfg is not None else config()
    rel = cfg.get("relative") or {}
    months, mins = int(rel.get("window_months", 3)), int(rel.get("min_sessions", 55))
    bench_key = rel.get("benchmark", "yfinance.mkt_spy")
    bench = window_return(_closes(st, bench_key, cutoff), months, mins)
    ref = {b["id"]: b["label"] for b in ((cfg.get("reference") or {}).get("buckets") or [])}
    out: dict[str, Any] = {"window_months": months, "benchmark": bench_key,
                           "bench": bench, "buckets": [], "absent": [],
                           "capex": capex_growth(st, cutoff, cfg),
                           "guidance": guidance(st, cutoff, cfg),
                           "report_only": True}
    for bid, p in (cfg.get("proxies") or {}).items():
        if bid == "memo":
            continue
        r = basket_return(st, list(p.get("keys") or []), cutoff, months, mins)
        if r["pct"] is None or bench is None:
            out["absent"].append({"id": bid, "label": ref.get(bid, bid),
                                  "reason": r.get("reason") if r["pct"] is None
                                  else f"the benchmark ({bench_key}) lacks the window"})
            continue
        out["buckets"].append({"id": bid, "label": ref.get(bid, bid), "pct": r["pct"],
                               "vs_bench_pp": round(r["pct"] - bench["pct"], 2),
                               "keys": [x["key"] for x in r["legs"]], "to": r["to"]})
    out["buckets"].sort(key=lambda b: -b["vs_bench_pp"])
    return out


def _date(d: str) -> str:
    x = dt.date.fromisoformat(d[:10])
    return f"{x.day} {x.strftime('%b %Y')}"


def relative_lines(r: dict) -> list[str]:
    """The line, code-written: the leader and the laggard, then each bucket."""
    n = r["window_months"]
    out = []
    if r["buckets"]:
        lead, lag = r["buckets"][0], r["buckets"][-1]
        out.append(
            f"AI capex chain, {n} months to {_date(lead['to'])} against SPY "
            f"({r['bench']['pct']:+.1f}%): {lead['label'].lower()} leads "
            f"({lead['vs_bench_pp']:+.1f} pp), {lag['label'].lower()} lags "
            f"({lag['vs_bench_pp']:+.1f} pp). Report only; the weights are BNP's "
            f"estimates and are not used to score a bucket.")
        out.append("By bucket: " + "; ".join(
            f"{b['label'].lower()} {b['pct']:+.1f}% ({b['vs_bench_pp']:+.1f} pp)"
            for b in r["buckets"]) + ".")
    else:
        out.append(f"AI capex chain: not enough stored history for any bucket over "
                   f"{n} months.")
    for a in r["absent"]:
        out.append(f"{a['label']}: {a['reason']}.")
    c = r["capex"]
    if c.get("pct") is not None:
        out.append(f"Against it, the hyperscalers' filed capex ({', '.join(c['names'])}; "
                   f"EDGAR, annual): {c['pct']:+.1f}% in fiscal {c['year']} on "
                   f"{c['prior']}. {c['gap'][0].upper()}{c['gap'][1:]}.")
    else:
        out.append(f"Against it, the hyperscalers' filed capex: not stored "
                   f"({c['reason']}). {c['gap'][0].upper()}{c['gap'][1:]}.")
    g = r.get("guidance") or {}
    parts = g.get("lines") or []
    if g.get("fault"):
        out.append(f"Their capex guidance from the filings: not read ({g['fault']}).")
    elif parts and all(p.endswith(" not stored") for p in parts):
        out.append(f"Their capex guidance from the filings (10-Q, 10-K): not stored "
                   f"for {', '.join(p[:-len(' not stored')] for p in parts)}.")
    elif parts:
        out.append("Their capex guidance from the filings: " + "; ".join(parts)
                   + ". Report only; each figure is extracted from the filing's own "
                     "sentence, its URL in the notes.")
    return out


def relative_notes(r: dict) -> list[str]:
    """The guidance's footnotes: each filing's form, date, accession and URL."""
    return [f"Guidance source, {n}" for n in ((r.get("guidance") or {}).get("footnotes") or [])]


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m altdata.capex_chain")
    ap.add_argument("cmd", choices=["show"])
    ap.add_argument("--as-of")
    ap.add_argument("--db")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    from altdata import observations, session  # noqa: PLC0415
    ref = reference()
    print(f"{ref['title']} ({ref['dated']}): {ref['caveat']}")
    for row in reference_table(ref)["rows"]:
        print("  " + " | ".join(row))
    with observations.ObservationStore(a.db) as st:
        for ln in relative_lines(relative(st, a.as_of or session.utc_iso())):
            print(ln)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
