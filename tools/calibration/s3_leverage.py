"""
S-3's calibration ledger: the crypto leverage extreme (the crypto data-sources
order, 6 Oct 2026, S-3; the a47 chain, 19 Oct 2026).

THE ORDER'S GATE, AS IT STATES IT. The flag "crypto leverage -- crowded": funding
z > +2 with OI/market cap at a 90-day high. "Anatomy check on the Aug 2024, Feb
2025 and Oct 2025 unwinds and the May 2026 rush: the flag fires before the
drawdown's largest day in >= 3 of 4 with <= 2 false positives per year."

WHAT THE FIRST EDITION PRE-REGISTERS (the terms the order leaves open; ruling 2
of 17 Oct: a re-run applies them and may not change them):
  - funding: BTC perpetual funding on Hyperliquid, the daily mean of its hourly
    prints -- the one public funding history that covers all four windows (from
    May 2023). The order's OI-weighted aggregate across exchanges cannot be
    rebuilt before its open-interest legs, which are served forward only;
  - the z: each day's funding against the trailing 90 calendar days (60 days at
    least), point-in-time;
  - OI over market cap: OKX's BTC perpetual open interest in USD over BTC-USD's
    close, i.e. open interest in coins -- BTC's supply moves under 0.5% in 90
    days, so its 90-day high is OI/market cap's -- at or above its trailing
    90-day maximum (60 days at least). Only as far back as OKX serves history;
  - each window's "drawdown's largest day" is the largest one-day decline in
    BTC-USD's close in that calendar month (the May 2026 "rush" read the same
    way); "fires before" is the flag on any of the 10 calendar days before it;
  - a window is evaluable when both legs are computable on each of those 10
    days; fewer than 3 evaluable windows is INSUFFICIENT;
  - a false positive is a firing episode (fires merged across 10 days) not
    followed within 10 days by a 10% peak-to-trough decline in BTC's close,
    counted per year of evaluable days;
  - PASS: >= 3 of the 4 caught (of those evaluable, with >= 3 evaluable) and
    <= 2 false positives a year; else FAIL.
  The forward 5- and 20-day returns and drawdowns after each firing episode are
  printed beside it.

THE RIGHTS IT WOULD GRANT, STATED AND NOT GRANTED: the narrow flag in the 07:00
anchor's and the 16:45 close's crypto paragraph, and the 12:30 alert-only line
(daily_cascade/crypto_gate.py), which stays closed until config names a passing
ledger. A PASS reaches the register only as a rule-31 draft; nothing changes until
the operator accepts it. Nothing enters a composite.

Public sources only (tools/calibration/README.md): Hyperliquid's and OKX's public
APIs through the writers' own parsers, BTC-USD through the one yfinance import.
Never the store.

    python tools/calibration/s3_leverage.py [--box] [--out DIR] [--date D]
"""

from __future__ import annotations

import datetime as dt
import statistics
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import st7_common as C                                          # noqa: E402

ITEM = "S-3"
TITLE = "The crypto leverage extreme (funding z with open interest at a 90-day high)"
WINDOWS = {"Aug 2024 unwind": "2024-08", "Feb 2025 unwind": "2025-02",
           "Oct 2025 unwind": "2025-10", "May 2026 rush": "2026-05"}
LOOK = 90
MIN_OBS = 60
Z_MIN = 2.0
LEAD = 10
FP_DAYS, FP_DROP = 10, -0.10
MIN_EVALUABLE, MIN_CAUGHT, MAX_FP_YEAR = 3, 3, 2.0
HL_FROM = "2023-05-12"
PASS_RULE = ("The flag (funding z > +2 with OI/market cap at a 90-day high) fires "
             "before the drawdown's largest day in >= 3 of the 4 windows (the Aug 2024, "
             "Feb 2025 and Oct 2025 unwinds and the May 2026 rush) with <= 2 false "
             "positives per year (pre-registered here: Hyperliquid BTC funding, OKX "
             "open interest in coins, the month's largest one-day decline, a 10-day "
             "lead, a false positive is a firing episode with no 10% decline within 10 "
             "days; fewer than 3 evaluable windows is INSUFFICIENT).")


def _day(ms: int) -> str:
    return dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc).date().isoformat()


def load_public() -> dict:
    from altdata.ledgers import sources as S                    # noqa: PLC0415
    from altdata.sources import fut, hl                          # noqa: PLC0415
    now_ms = int(dt.datetime.now(dt.timezone.utc).timestamp() * 1000)
    start = int(dt.datetime.fromisoformat(HL_FROM + "T00:00:00+00:00").timestamp() * 1000)
    hourly = hl.funding_history(hl.Client(), "BTC", start, now_ms, max_pages=200)
    daily: dict[str, list[float]] = {}
    for ms, v in hourly:
        daily.setdefault(_day(ms), []).append(v)
    funding = sorted((d, statistics.mean(v)) for d, v in daily.items())
    oi: dict[str, float] = {}
    end = None
    for _ in range(60):
        p = {"instId": "BTC-USDT-SWAP", "period": "1D", "limit": "100"}
        if end:
            p["end"] = str(end)
        page = fut.okx_oi_history(fut._get(                     # noqa: SLF001
            f"{fut.OKX}/api/v5/rubik/stat/contracts/open-interest-history", p))
        if not page or (end and page[0][0] >= end):
            break
        for ms, v in page:
            oi[_day(ms)] = v
        end = page[0][0]
    return {"funding": funding, "oi_usd": sorted(oi.items()), "btc": S.yahoo("BTC-USD"),
            "retrieved": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}


def _trail(series: dict, day: str, n: int) -> list[float]:
    d = dt.date.fromisoformat(day)
    out = []
    for k in range(1, n + 1):
        x = (d - dt.timedelta(days=k)).isoformat()
        if x in series:
            out.append(series[x])
    return out


def legs(funding: dict, oi_coins: dict, day: str) -> Optional[tuple[float, bool]]:
    """(funding z, OI at its 90-day high) on `day`, or None when either leg lacks
    its history."""
    if day not in funding or day not in oi_coins:
        return None
    fh, oh = _trail(funding, day, LOOK), _trail(oi_coins, day, LOOK)
    if len(fh) < MIN_OBS or len(oh) < MIN_OBS:
        return None
    sd = statistics.pstdev(fh)
    z = 0.0 if sd == 0 else (funding[day] - statistics.mean(fh)) / sd
    return z, oi_coins[day] >= max(oh)


def largest_down_day(btc: dict, month: str) -> Optional[tuple[str, float]]:
    days = sorted(d for d in btc if d.startswith(month))
    best = None
    for d in days:
        prev = (dt.date.fromisoformat(d) - dt.timedelta(days=1)).isoformat()
        if prev in btc:
            r = btc[d] / btc[prev] - 1.0
            if best is None or r < best[1]:
                best = (d, r)
    return best


def _window(btc: dict, day: str, n: int) -> tuple[Optional[float], Optional[float]]:
    d0 = dt.date.fromisoformat(day)
    path = [btc[x] for x in ((d0 + dt.timedelta(days=k)).isoformat() for k in range(n + 1))
            if x in btc]
    end = (d0 + dt.timedelta(days=n)).isoformat()
    if day not in btc or end not in btc:
        return None, None
    peak, mdd = path[0], 0.0
    for p in path:
        peak = max(peak, p)
        mdd = min(mdd, p / peak - 1.0)
    return btc[end] / btc[day] - 1.0, mdd


def study(d: dict, mode: str) -> dict:
    # A day not yet over (the retrieval day, UTC) is partial: left out.
    today = str(d.get("retrieved") or dt.date.today().isoformat())[:10]
    funding = {k: v for k, v in d["funding"] if k < today}
    btc = dict(d["btc"])
    oi_coins = {k: v / btc[k] for k, v in d["oi_usd"] if btc.get(k) and k < today}
    days = sorted(set(funding) & set(oi_coins))
    state = {x: legs(funding, oi_coins, x) for x in days}
    evaluable = [x for x, s in state.items() if s is not None]
    fired = {x for x in evaluable if state[x][0] > Z_MIN and state[x][1]}

    win_rows = []
    for name, month in WINDOWS.items():
        ld = largest_down_day(btc, month)
        if not ld:
            win_rows.append({"window": name, "largest_day": None, "evaluable": False,
                             "caught": False, "fire_days": ""})
            continue
        lead = [(dt.date.fromisoformat(ld[0]) - dt.timedelta(days=k)).isoformat()
                for k in range(1, LEAD + 1)]
        ev = all(state.get(x) is not None for x in lead)
        hits = [x for x in lead if x in fired]
        win_rows.append({"window": name, "largest_day": ld[0],
                         "largest_day_return": round(ld[1], 4), "evaluable": ev,
                         "caught": ev and bool(hits), "fire_days": " ".join(sorted(hits))})
    # Firing episodes, merged across 10 days; false positives and forward paths.
    eps, cur = [], None
    for x in sorted(fired):
        if cur and (dt.date.fromisoformat(x) - dt.date.fromisoformat(cur["last"])).days <= LEAD:
            cur["last"] = x
        else:
            cur = {"first": x, "last": x}
            eps.append(cur)
    ep_rows = []
    for e in eps:
        r5, m5 = _window(btc, e["first"], 5)
        r20, m20 = _window(btc, e["first"], 20)
        _, mfp = _window(btc, e["first"], FP_DAYS)
        ep_rows.append({"first": e["first"], "last": e["last"],
                        "ret_5d": None if r5 is None else round(r5, 4),
                        "mdd_5d": None if m5 is None else round(m5, 4),
                        "ret_20d": None if r20 is None else round(r20, 4),
                        "mdd_20d": None if m20 is None else round(m20, 4),
                        "false_positive": None if mfp is None else mfp > FP_DROP})
    years = len(evaluable) / 365.25
    fps = sum(1 for e in ep_rows if e["false_positive"])
    fp_year = fps / years if years else None
    n_ev = sum(1 for w in win_rows if w["evaluable"])
    caught = sum(1 for w in win_rows if w["caught"])
    line = (f"{caught} of {n_ev} evaluable windows caught (of 4); {len(ep_rows)} firing "
            f"episodes over {len(evaluable)} evaluable days "
            f"({evaluable[0] if evaluable else '-'} to {evaluable[-1] if evaluable else '-'}), "
            f"{fps} false positives, "
            f"{'n/a' if fp_year is None else f'{fp_year:.1f}'} a year")
    if n_ev < MIN_EVALUABLE:
        verdict = (f"{C.INSUFFICIENT} ({line}; the open-interest leg's public history "
                   f"starts {d['oi_usd'][0][0] if d['oi_usd'] else '-'}, so fewer than "
                   f"{MIN_EVALUABLE} windows can be judged)")
    elif caught >= MIN_CAUGHT and fp_year is not None and fp_year <= MAX_FP_YEAR:
        verdict = f"{C.PASS} ({line})"
    else:
        verdict = f"{C.FAIL} ({line})"
    as_of = days[-1] if days else "none"
    body = [f"- Funding: Hyperliquid BTC, {len(funding)} days "
            f"({d['funding'][0][0] if d['funding'] else '-'} to "
            f"{d['funding'][-1][0] if d['funding'] else '-'}).",
            f"- Open interest: OKX BTC-USDT perpetual, {len(d['oi_usd'])} days "
            f"({d['oi_usd'][0][0] if d['oi_usd'] else '-'} to "
            f"{d['oi_usd'][-1][0] if d['oi_usd'] else '-'}), in coins at BTC-USD's close.",
            f"- {line}."]
    for w in win_rows:
        body.append(f"- {w['window']}: largest one-day decline {w['largest_day'] or 'n/a'}"
                    + (f" ({C.pct(w.get('largest_day_return'))})" if w.get("largest_day") else "")
                    + ("; " + ("caught" if w["caught"] else "not caught") if w["evaluable"]
                       else "; not evaluable (a leg lacks its 90-day history)"))
    for e in ep_rows:
        body.append(f"- Fired {e['first']} to {e['last']}: 5 days {C.pct(e['ret_5d'])} "
                    f"(drawdown {C.pct(e['mdd_5d'])}), 20 days {C.pct(e['ret_20d'])} "
                    f"(drawdown {C.pct(e['mdd_20d'])})"
                    + ("; a false positive" if e["false_positive"] else ""))
    csv_rows = ([{"kind": "window", **{k: w.get(k) for k in
                 ("window", "largest_day", "largest_day_return", "evaluable", "caught",
                  "fire_days")}, "first": None, "last": None, "ret_5d": None,
                  "mdd_5d": None, "ret_20d": None, "mdd_20d": None, "false_positive": None}
                 for w in win_rows]
                + [{"kind": "firing", "window": None, "largest_day": None,
                    "largest_day_return": None, "evaluable": None, "caught": None,
                    "fire_days": None, **e} for e in ep_rows])
    return {"item": ITEM, "title": TITLE, "as_of": as_of,
            "window": f"{evaluable[0] if evaluable else '-'} to "
                      f"{evaluable[-1] if evaluable else '-'} (both legs evaluable)",
            "n": n_ev,
            "statistic": "windows caught of the four (the flag on within 10 days before "
                         "the month's largest one-day decline) and firing episodes with no "
                         "10% decline within 10 days, a year",
            "pass_rule": PASS_RULE, "verdict": verdict,
            "rights": ("Would grant: the narrow flag \"crypto leverage -- crowded\" in the "
                       "07:00 anchor's and the 16:45 close's crypto paragraph, and the "
                       "12:30 alert-only line (no setup rights). This ledger grants "
                       "nothing; the 12:30 gate stays closed. " + C.RIGHTS_NOTE),
            "sources": [f"Hyperliquid public info API, fundingHistory (BTC), retrieved "
                        f"{d.get('retrieved', '-')}",
                        "OKX public API, rubik open-interest-history (BTC-USDT-SWAP, 1D)",
                        "Yahoo Finance BTC-USD daily closes (the one yfinance import)"],
            "source_mode": mode, "body": body, "episodes": csv_rows,
            "caveats": ["One exchange's funding and one's open interest stand in for "
                        "the order's OI-weighted aggregate, whose other legs are served "
                        "forward only; the store's aggregate (calc.funding_agg, "
                        "calc.oi_mcap) matures from mid-December 2026.",
                        "The May 2026 'rush' is read by the same rule as the unwinds; "
                        "if the order meant a rally, a ruling says so before a re-run."]}


if __name__ == "__main__":
    raise SystemExit(C.cli(ITEM, load_public, study))
