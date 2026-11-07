"""
The AI infrastructure cash-cycle scorecard (signal-triage Batch 22 item 123, the
order's 105; section 0's O-4; V-105a to V-105d; paste B136, 6 Nov 2026).

A Factor I sub-panel, quarterly, in the Monthly's slow layers (config/stack_hooks/
monthly-slow-cash-cycle.yaml) and the Disruptive Themes refresh (themes_block);
the Weekly prints nothing. Eight rows, each declared in config/cash_cycle.yaml
with its formula and sources:

  1 cloud revenue growth         the segment's quarter on the year
  2 incremental segment margin   sum of four quarters' change in operating income
                                 over the same sum's change in revenue
  3 backlog                      RPO, its growth, its cover of four quarters' capex;
                                 dated records where a figure is only in the text
  4 capex against OCF            capex / OCF and FCF after leases, four quarters;
                                 the guide a dated record
  5 the financing ledger         the signal scan's proposed rows; confirmed at a
                                 sitting (O-4); "no confirmed rows" until then
  6 the private-credit window    folded into SR-16's Factor I lines
  7 GPU rental prices            "gap" with V-105a's candidates
  8 useful lives                 the round-7 watch's cross-reference

and the treadmill flag: capex growing faster than cloud revenue for two quarters
running while the four-quarter incremental margin falls.

READ FROM THE STORE ONLY (edgar.cc_* and edgar.seg_*, written by the edgar_xbrl
pull), each period's newest vintage known at the cutoff. Dated records print
"dated record". Rights: Factor I input lines and a flag; no composite change.
Nothing here fetches.

    python -m altdata.cash_cycle show [--as-of T] [--db PATH]   read-only
"""

from __future__ import annotations

import datetime as dt
import functools
import logging
import re
from pathlib import Path
from typing import Optional

log = logging.getLogger("altdata.cash_cycle")

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / "config" / "cash_cycle.yaml"
SCANS = REPO / "docs" / "scans"
TITLE = "Factor I: the AI infrastructure cash-cycle scorecard"
NO_CONFIRMED = "no confirmed rows"
GAP = "gap"
NOT_STORED = "not stored"
INSUFFICIENT = "insufficient"


@functools.lru_cache(maxsize=1)
def _cfg() -> dict:
    import yaml                                                 # noqa: PLC0415
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def config() -> dict:
    return _cfg()


def cc_key(t: str, f: str) -> str:
    return f"edgar.cc_{t.lower()}_{f}"


def seg_key(t: str, f: str) -> str:
    return f"edgar.seg_{t.lower()}_{f}"


# ---------------------------------------------------------------------------
# The arithmetic, on plain {period end: value} series
# ---------------------------------------------------------------------------
def year_before(series: dict[str, float], end: str, tol: int = 12) -> Optional[float]:
    """The value at the period end one year before `end` (within `tol` days:
    fiscal quarters end on a weekday or a month end)."""
    d = dt.date.fromisoformat(end)
    target = d.replace(year=d.year - 1) if not (d.month == 2 and d.day == 29) else \
        d.replace(year=d.year - 1, day=28)
    best = None
    for k, v in series.items():
        gap = abs((dt.date.fromisoformat(k) - target).days)
        if gap <= tol and (best is None or gap < best[0]):
            best = (gap, v)
    return None if best is None else best[1]


def growth(series: dict[str, float], end: Optional[str] = None) -> Optional[float]:
    if not series:
        return None
    end = end or max(series)
    prev = year_before(series, end)
    if prev in (None, 0) or end not in series:
        return None
    return series[end] / prev - 1


def incremental_margin(rev: dict[str, float], oi: dict[str, float],
                       end: Optional[str] = None, n: int = 4) -> Optional[float]:
    """Sum over the `n` quarters to `end` of the change in operating income on
    the year, over the same sum of the change in revenue. None without all 2n
    quarters, or a zero change in revenue."""
    ends = sorted(e for e in rev if e in oi and (end is None or e <= end))[-n:]
    if len(ends) < n:
        return None
    d_oi = d_rev = 0.0
    for e in ends:
        r0, o0 = year_before(rev, e), year_before(oi, e)
        if r0 is None or o0 is None:
            return None
        d_rev += rev[e] - r0
        d_oi += oi[e] - o0
    return None if d_rev == 0 else d_oi / d_rev


def trailing(series: dict[str, float], n: int = 4, end: Optional[str] = None
             ) -> Optional[float]:
    ends = sorted(e for e in series if end is None or e <= end)[-n:]
    if len(ends) < n:
        return None
    # four consecutive quarters: no more than ~400 days end to end
    if (dt.date.fromisoformat(ends[-1]) - dt.date.fromisoformat(ends[0])).days > 300:
        return None
    return sum(series[e] for e in ends)


def treadmill(rev: dict[str, float], oi: dict[str, float], capex: dict[str, float],
              quarters: int = 2) -> dict:
    """Capex growing faster than cloud revenue, on the year, in each of the last
    `quarters` quarters, while the four-quarter incremental margin fell in each.
    'insufficient' without the quarters to say."""
    ends = sorted(e for e in rev if e in oi and e in capex)[-quarters:]
    if len(ends) < quarters:
        return {"state": INSUFFICIENT, "fired": False}
    checks = []
    for e in ends:
        cg, rg = growth(capex, e), growth(rev, e)
        prior = sorted(x for x in rev if x < e)
        im, im_prev = incremental_margin(rev, oi, e), (
            incremental_margin(rev, oi, prior[-1]) if prior else None)
        if None in (cg, rg, im, im_prev):
            return {"state": INSUFFICIENT, "fired": False}
        checks.append({"end": e, "capex_g": cg, "rev_g": rg, "im": im, "im_prev": im_prev,
                       "hit": cg > rg and im < im_prev})
    fired = all(c["hit"] for c in checks)
    return {"state": "ON" if fired else "off", "fired": fired, "checks": checks}


# ---------------------------------------------------------------------------
# The store
# ---------------------------------------------------------------------------
def series(st, key: str, as_of: Optional[str]) -> dict[str, float]:
    """{period end: the newest vintage's value known at `as_of`}."""
    out: dict[str, tuple[str, float]] = {}
    for r in st.as_of(key, as_of):
        v = r.get("value_num")
        if v is None:
            continue
        e, a = str(r["observed_at"])[:10], str(r["available_at"])
        if e not in out or a >= out[e][0]:
            out[e] = (a, float(v))
    return {e: v for e, (_a, v) in sorted(out.items())}


def scan_financing(as_of: Optional[str] = None, scans: Path = SCANS) -> dict:
    """The newest signal-scan file's "Financing" section: one proposed row a line,
    `- <id> | <ticker> | <structure> | <counterparty> | <amount> | <url>`; a line
    without its URL is not a row. O-4: proposed only; a row is confirmed when
    config's `financing_confirmed` names it."""
    files = sorted(p for p in scans.glob("signal-scan-*.md")
                   if not as_of or p.stem[-7:] <= str(as_of)[:7])
    if not files:
        return {"file": None, "proposed": []}
    text = files[-1].read_text(encoding="utf-8")
    body = re.split(r"(?mi)^#{1,3}\s*(?:\d+\.\s*)?financing\b.*$", text)
    rows = []
    if len(body) > 1:
        sec = re.split(r"(?m)^#{1,3}\s", body[1])[0]
        for ln in sec.splitlines():
            parts = [p.strip() for p in ln.strip().lstrip("-* ").split("|")]
            if len(parts) >= 6 and re.match(r"https?://", parts[5]):
                rows.append({"id": parts[0], "ticker": parts[1], "structure": parts[2],
                             "counterparty": parts[3], "amount": parts[4], "url": parts[5]})
    return {"file": files[-1].name, "proposed": rows}


def _bn(v: Optional[float]) -> str:
    if v is None:
        return NOT_STORED
    return f"{'−' if v < 0 else ''}${abs(v) / 1e9:,.1f}bn"


def _pc(v: Optional[float], nd: int = 1) -> str:
    return "n/a" if v is None else f"{v * 100:+.{nd}f}%"


def read(st, now: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    segs = {s["ticker"]: s for s in cfg["segments"]}
    out = {"filers": [], "as_of": now}
    for f in cfg["facts"]["filers"]:
        t = f["ticker"]
        g = {fld: series(st, cc_key(t, fld), now) for fld in cfg["facts"]["fields"]}
        row = {"ticker": t, "segment": None}
        if t in segs:
            rev = series(st, seg_key(t, "revenue"), now)
            oi = series(st, seg_key(t, "operating_income"), now)
            row["segment"] = {
                "label": segs[t]["label"], "end": max(rev) if rev else None,
                "growth": growth(rev), "im4": incremental_margin(rev, oi),
                "im1": incremental_margin(rev, oi, n=1),
                "quarters": len(rev),
                "treadmill": treadmill(rev, oi, g["capex"],
                                       int(cfg["treadmill"]["quarters"]))}
        rpo = g["rpo"]
        capex4, ocf4 = trailing(g["capex"]), trailing(g["operating_cash_flow"])
        flp4 = trailing(g["finance_lease_principal"])
        row.update({
            "rpo": rpo[max(rpo)] if rpo else None, "rpo_end": max(rpo) if rpo else None,
            "rpo_growth": growth(rpo) if rpo else None,
            "rpo_cover": (rpo[max(rpo)] / capex4) if rpo and capex4 else None,
            "capex4": capex4, "ocf4": ocf4,
            "capex_ocf": (capex4 / ocf4) if capex4 and ocf4 else None,
            "fcf_leases": (ocf4 - capex4 - (flp4 or 0.0)) if capex4 is not None
            and ocf4 is not None else None,
            "flp_stored": flp4 is not None,
            "capex_end": max(g["capex"]) if g["capex"] else None})
        out["filers"].append(row)
    out["financing"] = scan_financing(now)
    out["confirmed"] = list(cfg.get("financing_confirmed") or [])
    return out


# ---------------------------------------------------------------------------
# The prints
# ---------------------------------------------------------------------------
def private_credit_line(cfg: Optional[dict] = None) -> str:
    """Row 6, folded into SR-16's Factor I lines (V-105c)."""
    cfg = cfg or config()
    recs = [r for r in cfg.get("dated_records") or [] if r.get("row") == "private_credit"]
    und = [u["item"] for u in cfg.get("undated") or [] if u.get("row") == "private_credit"]
    ora = ("Oracle's spread: NOT TRACKED (no store key; no keyless single-name "
           "spread source)" if not cfg.get("oracle_spread_key")
           else f"Oracle's spread: {cfg['oracle_spread_key']}")
    parts = [ora] + [f"{r['text']} (dated record, {r['date']})" for r in recs] \
        + [f"{x}: no dated record filed" for x in und]
    return ("Private-credit window (item 123 row 6, folded into SR-16): "
            + "; ".join(parts) + ".")


def treadmill_line(r: dict) -> str:
    segs = [f for f in r["filers"] if f["segment"]]
    states = [f"{f['ticker']} {f['segment']['treadmill']['state']}" for f in segs]
    fired = [f["ticker"] for f in segs if f["segment"]["treadmill"]["fired"]]
    return ("Treadmill flag (capex, actual, growing faster than cloud revenue for two "
            "quarters running while the four-quarter incremental margin falls): "
            + ("ON for " + ", ".join(fired) if fired else "off") + " -- "
            + "; ".join(states) + ".")


def lines(r: dict, cfg: Optional[dict] = None) -> list[str]:
    cfg = cfg or config()
    fin = r["financing"]
    conf = [c for c in r["confirmed"]]
    recs = cfg.get("dated_records") or []
    out = [treadmill_line(r)]
    for rec in recs:
        if rec.get("row") in ("backlog", "capex_ocf"):
            out.append(f"{rec['ticker']}: {rec['text']} (dated record, {rec['date']}; "
                       f"{rec['url']}).")
    und = [u["item"] for u in cfg.get("undated") or [] if u.get("row") == "backlog"]
    if und:
        out.append("Backlog: " + "; ".join(f"{x}: no dated record filed" for x in und) + ".")
    out.append("Financing-structure ledger (O-4): "
               + (f"{len(conf)} confirmed" if conf else NO_CONFIRMED)
               + (f"; {len(fin['proposed'])} proposed in {fin['file']}, for a sitting"
                  if fin["file"] else "; no signal-scan file proposes any yet") + ".")
    out.append(private_credit_line(cfg))
    gp = cfg.get("gpu_rental") or {}
    out.append("GPU rental price index: " + GAP + " (V-105a: keyless candidates -- "
               + "; ".join(c["name"] for c in gp.get("candidates") or [])
               + " -- carry no writer until a source check reads their terms and "
                 "robots).")
    out.append("Useful lives: cross-referenced from the round-7 useful-life watch (Batch "
               "16 item 83(b)): its quarterly read is a listed gap (H3); no filer tags "
               "server useful life in XBRL (from the 10-K text: not tracked).")
    return out


def table(r: dict) -> dict:
    rows = []
    for f in r["filers"]:
        s = f["segment"]
        if s:
            grow = f"{_pc(s['growth'])} ({s['label']}, {s['end']})" if s["end"] else NOT_STORED
            im = (f"{s['im4'] * 100:.0f}¢ per $ (4q)" if s["im4"] is not None else
                  f"{INSUFFICIENT} ({s['quarters']} quarters as reported)")
            if s["im1"] is not None:
                im += f"; {s['im1'] * 100:.0f}¢ latest quarter"
        else:
            grow = im = "no cloud segment"
        bl = (f"{_bn(f['rpo'])} ({f['rpo_end']}); {_pc(f['rpo_growth'])} on the year"
              + (f"; covers {f['rpo_cover']:.1f}x four quarters' capex"
                 if f["rpo_cover"] else "")) if f["rpo"] is not None else \
            "RPO not tagged (see the dated records)"
        cx = (f"{f['capex_ocf']:.2f}x" if f["capex_ocf"] is not None else NOT_STORED)
        fcf = _bn(f["fcf_leases"]) + ("" if f["flp_stored"] or f["fcf_leases"] is None
                                      else " (finance-lease principal not stored)")
        rows.append([f["ticker"], grow, im, bl, cx, fcf,
                     f"EDGAR XBRL; capex to {f['capex_end'] or NOT_STORED}"])
    return {"columns": ["Company", "Cloud revenue growth", "Incremental margin",
                        "Backlog (RPO)", "Capex / OCF (4q)", "FCF after leases (4q)",
                        "Source and as-of"], "rows": rows}


def slow_subsection(st, now: str) -> Optional[dict]:
    """The Monthly's and the Themes refresh's Factor I sub-panel."""
    try:
        r = read(st, now)
        return {"title": TITLE, "table": table(r), "lines": lines(r),
                "paragraph_wanted": False, "not_tracked": [],
                "data": {"treadmill": {f["ticker"]: f["segment"]["treadmill"]["state"]
                                       for f in r["filers"] if f["segment"]}}}
    except Exception:                                           # noqa: BLE001
        log.warning("the cash-cycle scorecard faulted", exc_info=True)
        return None


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    import sys                                                  # noqa: PLC0415
    from altdata import session, trend_breadth                  # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.cash_cycle")
    ap.add_argument("cmd", choices=["show"])
    ap.add_argument("--as-of", default=None)
    ap.add_argument("--db", default=None)
    a = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    st = trend_breadth.open_ro(a.db)
    try:
        sub = slow_subsection(st, a.as_of or session.utc_iso())
    finally:
        st.conn.close()
    for row in (sub or {}).get("table", {}).get("rows", []):
        print(" | ".join(row))
    for ln in (sub or {}).get("lines", []):
        print(ln)
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
