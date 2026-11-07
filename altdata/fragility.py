"""
The liquidity-fragility panel, its flag and the "liquidity" lens (signal-triage
Batch 14 item 71, written as 64; ST-R6.71a-c; ruled 20 Oct 2026 with filing
amendments F1-F8; a57-batch14-b1). Settings: config/fragility.yaml.

    python -m altdata.fragility show [--date D] [--as-of ISO]

THE PANEL (Mechanics), every figure from the store as of the cutoff:
  depth      SPY's Amihud illiquidity and its range per unit of volume (stored
             daily bars), each a 20-session mean in bp per $1bn traded, with dual
             percentiles; ES top-of-book depth "not tracked" (check 8).
  margin     FINRA margin debt (the existing writer), as a level and as a share
             of Z.1's all-sector equity market value, marked to SPX between
             releases, with dual percentiles of the share.
  rebalance  the leveraged-ETF close-rebalance estimate, AUM x L x (L - 1) x the
             day's return, over the funds the existing writer covers; each fund
             it does not cover is a listed gap.
  dealer     dealer gamma from 6b, as the close stored it (never recomputed).
THE FLAG: the depth arm (while depth is not tracked, the Amihud stand-in at or
above its 90th percentile, labelled) AND the forced-flow arm (the rebalance plus
negative dealer gamma's hedging, above its 90th). FLAG RIGHTS ONLY: no modifier
before the air-pocket ledger. The lens is a report-only row in item 52's table;
the levels read carries the flag's line.

Reads only; writes nothing; enters no composite and not the market-state object.
"""

from __future__ import annotations

import bisect
import datetime as dt
import math
import sys
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / "config" / "fragility.yaml"
TITLE = "Liquidity fragility"
STAND_IN = "the Amihud measure, standing in for depth"


def config(path: Optional[Path] = None) -> dict:
    import yaml                                                 # noqa: PLC0415
    return yaml.safe_load((path or CONFIG).read_text(encoding="utf-8"))


def _pts(st, key: str, cutoff: str, instrument: Optional[str] = None
         ) -> list[tuple[str, float]]:
    from . import st_r5_rates                                   # noqa: PLC0415
    return st_r5_rates._pts(st, key, cutoff, instrument)


def _lens(series: list[tuple[str, float]], years: int = 5) -> dict:
    from . import st_r5_rates                                   # noqa: PLC0415
    return st_r5_rates.lens(series, years)


def _lens_text(lz: dict) -> str:
    from . import st_r5_rates                                   # noqa: PLC0415
    return st_r5_rates.lens_text(lz)


def _upto(pts: list[tuple[str, float]], day: str) -> list[tuple[str, float]]:
    return [(d, v) for d, v in pts if d <= day]


# ---------------------------------------------------------------------------
# Depth: the Amihud measure and the range per unit of volume
# ---------------------------------------------------------------------------
def daily_depth(close: list, high: list, low: list, volume: list
                ) -> list[tuple[str, float, Optional[float]]]:
    """[(day, amihud, range)], bp per $1bn of dollar volume, on the days with a
    close, the prior close and a positive volume; range None without high/low."""
    c, h, l_, v = dict(close), dict(high), dict(low), dict(volume)
    days = sorted(c)
    out = []
    for prev, d in zip(days, days[1:]):
        vol = v.get(d)
        if not vol or vol <= 0 or not c[prev] or not c[d]:
            continue
        dv_bn = c[d] * vol / 1e9
        ret_bp = abs(math.log(c[d] / c[prev])) * 1e4
        rng = ((h[d] - l_[d]) / c[prev] * 1e4 / dv_bn
               if d in h and d in l_ and h[d] >= l_[d] else None)
        out.append((d, ret_bp / dv_bn, rng))
    return out


def rolling_mean(pts: list[tuple[str, Optional[float]]], n: int, min_n: int
                 ) -> list[tuple[str, float]]:
    """The mean of each day's last `n` values, where at least `min_n` of them exist."""
    out = []
    for i in range(len(pts)):
        w = [x for _, x in pts[max(0, i - n + 1):i + 1] if x is not None]
        if len(pts[max(0, i - n + 1):i + 1]) >= min_n and len(w) >= min_n:
            out.append((pts[i][0], sum(w) / len(w)))
    return out


def depth_read(bars: dict, day: str, cfg: dict) -> dict:
    d = daily_depth(_upto(bars["close"], day), _upto(bars["high"], day),
                    _upto(bars["low"], day), _upto(bars["volume"], day))
    n, mn = int(cfg["mean_sessions"]), int(cfg["min_sessions_in_mean"])
    am = rolling_mean([(x, a) for x, a, _ in d], n, mn)
    rg = rolling_mean([(x, r) for x, _, r in d], n, mn)
    out: dict[str, Any] = {}
    for name, s in (("amihud", am), ("range", rg)):
        if not s or s[-1][0] != day:
            out[name] = {"state": "absent",
                         "reason": ("no SPY volume stored" if not d else
                                    f"no {n}-session mean on {day} (last "
                                    f"{s[-1][0] if s else 'none'})")}
            continue
        lz = _lens(s, int(cfg["flag"]["window_years"]))
        out[name] = {"state": "computed", "value": round(s[-1][1], 3), "as_of": day,
                     "lens": lz, "lens_text": _lens_text(lz)}
    return out


# ---------------------------------------------------------------------------
# Margin debt
# ---------------------------------------------------------------------------
def _quarter_end(first_day: str) -> str:
    d = dt.date.fromisoformat(first_day[:10])
    m = d.month + 3
    y = d.year + (m - 1) // 12
    m = (m - 1) % 12 + 1
    return (dt.date(y, m, 1) - dt.timedelta(days=1)).isoformat()


def _at_or_before(pts: list[tuple[str, float]], day: str) -> Optional[tuple[str, float]]:
    """The last point on or before `day` in a list sorted by day."""
    j = bisect.bisect_right(pts, (day, math.inf)) - 1
    return pts[j] if j >= 0 else None


def margin_share_series(debit: list, mv: list, spx: list, scale: float
                        ) -> list[tuple[str, float, bool]]:
    """[(month end, share %, marked)]: margin debt over the latest Z.1 quarter at or
    before the month's end, that quarter marked to SPX from its end to the month's
    end ("marked" when the month is not the quarter's own end)."""
    q = [(_quarter_end(d), v) for d, v in mv]
    out = []
    for d, debt in debit:
        qq = _at_or_before(q, d)
        if not qq or not debt:
            continue
        s0, s1 = _at_or_before(spx, qq[0]), _at_or_before(spx, d)
        marked = qq[0][:7] != d[:7]
        if marked and (not s0 or not s1):
            continue
        cap = qq[1] * scale * ((s1[1] / s0[1]) if marked else 1.0)
        out.append((d, debt / cap * 100.0, marked))
    return out


def margin_read(debit: list, mv: list, spx: list, cfg: dict, day: str) -> dict:
    m = cfg["margin"]
    debit = _upto(debit, day)
    if not debit:
        return {"state": "absent", "reason": "FINRA margin debt not stored"}
    last_d, last_v = debit[-1]
    yr = _at_or_before(debit, f"{int(last_d[:4]) - 1:04d}{last_d[4:]}")
    out: dict[str, Any] = {"state": "computed", "month": last_d[:7],
                           "level_bn": round(last_v / 1e9, 1),
                           "yoy_pct": (round((last_v / yr[1] - 1) * 100, 1)
                                       if yr and yr[0][:7] != last_d[:7] and yr[1] else None)}
    sh = margin_share_series(debit, _upto(mv, day), _upto(spx, day),
                             float(m["market_value_scale"]))
    if not sh or sh[-1][0] != last_d:
        out["share"] = {"state": "absent",
                        "reason": "no Z.1 equity market value at or before the month"
                        if not mv else "SPX not stored to mark the quarter"}
        return out
    lz = _lens([(d, s) for d, s, _ in sh], int(cfg["flag"]["window_years"]))
    out["share"] = {"state": "computed", "value": round(sh[-1][1], 2),
                    "marked": sh[-1][2], "lens": lz, "lens_text": _lens_text(lz)}
    return out


# ---------------------------------------------------------------------------
# The leveraged-ETF rebalance and dealer gamma: the forced flow
# ---------------------------------------------------------------------------
def rebalance_series(aum: dict[str, list], proxies: dict[str, list], funds: list[dict],
                     max_age: int) -> list[tuple[str, float, list[str]]]:
    """[(day, $ estimate, funds read)]: sum over the funds of the prior session's
    AUM x L x (L - 1) x the index proxy's close-to-close return on the day."""
    rets: dict[str, dict[str, float]] = {}
    for key, pts in proxies.items():
        rets[key] = {pts[i][0]: pts[i][1] / pts[i - 1][1] - 1.0
                     for i in range(1, len(pts)) if pts[i - 1][1]}
    days = sorted(set().union(*[set(r) for r in rets.values()])) if rets else []
    idx = {t: ([d for d, _ in pts], [v for _, v in pts]) for t, pts in aum.items()}
    out = []
    for d in days:
        total, used = 0.0, []
        for f in funds:
            r = rets.get(f["proxy"], {}).get(d)
            ds, vs = idx.get(f["ticker"]) or ([], [])
            j = bisect.bisect_left(ds, d) - 1          # the last AUM strictly before d
            prior = (ds[j], vs[j]) if j >= 0 else None
            if r is None or not prior or (dt.date.fromisoformat(d)
                                          - dt.date.fromisoformat(prior[0])).days > max_age:
                continue
            L = float(f["leverage"])
            total += prior[1] * L * (L - 1.0) * r
            used.append(f["ticker"])
        if used:
            out.append((d, total, used))
    return out


def forced_flow(reb: list[tuple[str, float, list[str]]], gamma: dict[str, float],
                spy_ret: dict[str, float]) -> list[tuple[str, float, bool]]:
    """[(day, $ forced flow, dealer read)]: |the rebalance| plus, where dealer gamma
    was stored for the day and is negative, |gamma $ per 1%| x |the day's move, %|."""
    out = []
    for d, total, _ in reb:
        g, r = gamma.get(d), spy_ret.get(d)
        dealer = (max(0.0, -g) * abs(r) * 100.0) if (g is not None and r is not None) else None
        out.append((d, abs(total) + (dealer or 0.0), dealer is not None))
    return out


def flow_read(st_series: dict, cfg: dict, day: str) -> dict:
    lv = cfg["leveraged_etfs"]
    funds = lv["covered"]
    reb = [x for x in rebalance_series(st_series["aum"], st_series["proxies"], funds,
                                       int(lv["aum_max_age_days"])) if x[0] <= day]
    spy = _upto(st_series["proxies"].get(cfg["spy"]["close"]) or [], day)
    spy_ret = {spy[i][0]: spy[i][1] / spy[i - 1][1] - 1.0
               for i in range(1, len(spy)) if spy[i - 1][1]}
    gamma = dict(_upto(st_series["gamma"], day))
    out: dict[str, Any] = {"gaps": lv.get("not_covered") or []}
    g = gamma.get(day)
    out["dealer"] = ({"state": "absent", "reason": f"no 6b dealer gamma stored for {day}"}
                     if g is None else
                     {"state": "computed", "value": g,
                      "regime": "negative" if g < 0 else "positive" if g > 0 else "flat",
                      "stored_n": len(gamma)})
    if not reb or reb[-1][0] != day:
        out["rebalance"] = {"state": "absent",
                            "reason": ("no leveraged-ETF AUM stored" if not any(
                                st_series["aum"].values()) else
                                f"no estimate on {day} (an AUM or a close missing)")}
        out["forced"] = {"state": "absent", "reason": out["rebalance"]["reason"]}
        return out
    d, total, used = reb[-1]
    yrs = int(cfg["flag"]["window_years"])
    lz_r = _lens([(x, abs(v)) for x, v, _ in reb], yrs)
    out["rebalance"] = {"state": "computed", "value": total, "funds": used,
                        "lens": lz_r, "lens_text": _lens_text(lz_r)}
    ff = forced_flow(reb, gamma, spy_ret)
    lz_f = _lens([(x, v) for x, v, _ in ff], yrs)
    out["forced"] = {"state": "computed", "value": ff[-1][1], "dealer_read": ff[-1][2],
                     "lens": lz_f, "lens_text": _lens_text(lz_f)}
    return out


# ---------------------------------------------------------------------------
# The flag
# ---------------------------------------------------------------------------
def flag(depth: dict, flow: dict, cfg: dict) -> dict:
    """The depth arm (the stand-in while depth is not tracked) and the forced-flow
    arm; on only when both are; "not read" when either arm has no reading."""
    f = cfg["flag"]
    am, fo = depth.get("amihud") or {}, flow.get("forced") or {}
    arm_d = (None if am.get("state") != "computed" else
             (am["lens"].get("percentile_window") or 0) >= float(f["amihud_pct"]))
    arm_f = (None if fo.get("state") != "computed" else
             (fo["lens"].get("percentile_window") or 0) > float(f["forced_flow_pct"]))
    on = bool(arm_d and arm_f)
    state = "not read" if arm_d is None or arm_f is None else ("on" if on else "off")
    parts = []
    parts.append("depth arm: " + ("not read" if arm_d is None else
                                  f"{STAND_IN}, {_ord(am['lens'].get('percentile_window'))} "
                                  f"percentile of {f['window_years']} years "
                                  f"({'at or above' if arm_d else 'below'} the "
                                  f"{_ord(f['amihud_pct'])})"))
    parts.append("forced-flow arm: " + ("not read" if arm_f is None else
                                        f"{_ord(fo['lens'].get('percentile_window'))} "
                                        f"percentile ({'above' if arm_f else 'not above'} "
                                        f"the {_ord(f['forced_flow_pct'])}"
                                        + ("" if fo.get("dealer_read") else
                                           "; the leveraged-ETF arm alone, no dealer gamma "
                                           "stored for the session") + ")"))
    word = {"on": "ON", "off": "off", "not read": "not read"}[state]
    return {"state": state, "on": on, "depth_arm": arm_d, "flow_arm": arm_f,
            "line": f"The fragility flag is {word}: " + "; ".join(parts)
                    + ". Flag rights only; no modifier before the air-pocket ledger."}


def _ord(p: Optional[float]) -> str:
    from . import st_r5_rates                                   # noqa: PLC0415
    return st_r5_rates.ordinal(p)


def _usd(v: Optional[float]) -> str:
    if v is None:
        return "—"
    a = abs(v)
    s = "-" if v < 0 else "+"
    return f"{s}${a / 1e9:,.2f}bn" if a >= 1e8 else f"{s}${a / 1e6:,.0f}m"


# ---------------------------------------------------------------------------
# The read, the panel, the lens and the levels-read line
# ---------------------------------------------------------------------------
def read_series(st, cutoff: str, cfg: dict) -> dict:
    s, m, lv, dl = cfg["spy"], cfg["margin"], cfg["leveraged_etfs"], cfg["dealer"]
    proxies = {k: _pts(st, k, cutoff) for k in {f["proxy"] for f in lv["covered"]}
               | {s["close"]}}
    return {"bars": {"close": proxies[s["close"]], "high": _pts(st, s["high"], cutoff),
                     "low": _pts(st, s["low"], cutoff),
                     "volume": _pts(st, s["volume"], cutoff)},
            "debit": _pts(st, m["debit"], cutoff), "mv": _pts(st, m["market_value"], cutoff),
            "spx": _pts(st, m["spx"], cutoff),
            "aum": {f["ticker"]: _pts(st, lv["aum_key"], cutoff, f["ticker"])
                    for f in lv["covered"]},
            "proxies": proxies,
            "gamma": _pts(st, dl["key"], cutoff, dl["instrument"])}


def evaluate(series: dict, day: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    depth = depth_read(series["bars"], day, cfg)
    margin = margin_read(series["debit"], series["mv"], series["spx"], cfg, day)
    flow = flow_read(series, cfg, day)
    fl = flag(depth, flow, cfg)
    return {"day": day, "depth": depth, "margin": margin, "flow": flow, "flag": fl,
            "es_depth_gap": " ".join(str(cfg["es_depth_gap"]).split())}


def build(st, day: str, cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    return evaluate(read_series(st, cutoff, cfg), day, cfg)


def _cell(x: dict, fmt) -> tuple[str, str]:
    if x.get("state") != "computed":
        return "—", x.get("reason") or "not read"
    return fmt(x), x.get("lens_text") or ""


def panel(ev: dict) -> Optional[dict]:
    """The Mechanics sub-section, or None when no depth proxy can be read (no SPY
    volume stored): the panel prints nothing it cannot measure."""
    d, m, f = ev["depth"], ev["margin"], ev["flow"]
    if d["amihud"].get("state") != "computed":
        return None
    rows = []
    v, p = _cell(d["amihud"], lambda x: f"{x['value']:.2f} bp per $1bn")
    rows.append(["SPY Amihud illiquidity, 20-session mean (the stand-in for depth)", v, p])
    v, p = _cell(d["range"], lambda x: f"{x['value']:.2f} bp per $1bn")
    rows.append(["SPY daily range per $1bn traded, 20-session mean", v, p])
    rows.append(["ES top-of-book depth", "NOT TRACKED", "section 5 check 8: no free source"])
    if m.get("state") == "computed":
        rows.append([f"FINRA margin debt ({m['month']})", f"${m['level_bn']:,.1f}bn",
                     "—" if m.get("yoy_pct") is None else f"{m['yoy_pct']:+.1f}% on the year"])
        sh = m.get("share") or {}
        v, p = _cell(sh, lambda x: f"{x['value']:.2f}%" + (" (marked)" if x["marked"] else ""))
        rows.append(["Margin debt, share of Z.1 equity market value", v, p])
    else:
        rows.append(["FINRA margin debt", "—", m.get("reason") or "not read"])
    rb = f["rebalance"]
    v, p = _cell(rb, lambda x: _usd(x["value"]))
    rows.append(["Leveraged-ETF close rebalance, estimate "
                 f"({', '.join(rb.get('funds') or []) or 'no fund read'})", v,
                 (p + " (of its size)") if rb.get("state") == "computed" else p])
    dl = f["dealer"]
    rows.append(["Dealer gamma, SPY all expiries (6b, as stored)",
                 _usd(dl["value"]) + " per 1%" if dl.get("state") == "computed" else "—",
                 dl.get("regime") or dl.get("reason")])
    v, p = _cell(f["forced"], lambda x: _usd(x["value"]).lstrip("+"))
    rows.append(["Forced flow: the rebalance plus negative dealer gamma x the move", v, p])
    gaps = "; ".join(f"{'/'.join(g['tickers'])} ({g['issuer']}, {g['index']}): {g['reason']}"
                     for g in f.get("gaps") or [])
    lines = [ev["flag"]["line"], ev["es_depth_gap"] + "."]
    if gaps:
        lines.append("Leveraged ETFs not covered, a listed gap each: " + gaps + ".")
    return {"title": TITLE, "paragraph_wanted": False, "lines": lines,
            "table": {"columns": ["Measure", "Latest", "Percentiles or note"],
                      "rows": rows},
            "table_note": ("Every figure from the store as of the cutoff; percentiles "
                           "rank on five years and the full stored history. Report-only "
                           "but for the flag, whose rights are a flag's."),
            "data": {"fragility": {"flag": ev["flag"]["state"], "day": ev["day"]}}}


def lens(ev: dict) -> dict:
    """The report-only "liquidity" row for item 52's lens table."""
    am, fo = ev["depth"].get("amihud") or {}, ev["flow"].get("forced") or {}
    a = (f"{STAND_IN} {am['value']:.2f} bp per $1bn ({_ord(am['lens'].get('percentile_window'))} "
         f"percentile of five years)" if am.get("state") == "computed" else
         "the Amihud stand-in not read")
    b = (f"forced flow {_usd(fo['value']).lstrip('+')} "
         f"({_ord(fo['lens'].get('percentile_window'))} percentile)"
         if fo.get("state") == "computed" else "forced flow not read")
    return {"state": ev["flag"]["state"], "as_of": ev["day"],
            "line": f"{a}; {b}; the fragility flag {ev['flag']['state']} (report only)"}


def levels_line(ev: dict) -> str:
    """The flag's line in item 45's levels read."""
    return f"Liquidity: {ev['flag']['line']}"


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    from . import observations, session                         # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.fragility")
    ap.add_argument("cmd", choices=["show"])
    ap.add_argument("--date", default=None)
    ap.add_argument("--as-of", default=None)
    a = ap.parse_args(argv)
    cutoff = a.as_of or session.utc_iso()
    day = a.date or session.session_date()
    with observations.ObservationStore() as st:
        ev = build(st, day, cutoff)
    pn = panel(ev)
    if not pn:
        print(f"{day}: no SPY volume stored; the panel prints nothing")
        return 0
    for r in pn["table"]["rows"]:
        print(" | ".join(str(x) for x in r))
    for ln in pn["lines"]:
        print(ln)
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
