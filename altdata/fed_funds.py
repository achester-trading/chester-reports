"""
The rate path: fed funds futures to the implied rate after each FOMC meeting. (6d)
(docs/briefs/reporting-stack-brief-2026-10-02.md 2.4)

    python -m altdata.fed_funds pull [--dry-run]     # the 16:10 eod feed
    python -m altdata.fed_funds path [--as-of ...]   # print the stored path

THE CONTRACTS. The CBOT 30-day fed funds future for month M settles at 100 minus
the month's AVERAGE daily effective fed funds rate. yfinance serves each month as
`ZQ<code><yy>.CBT` (code F G H J K M N Q U V X Z for Jan..Dec); probed 2 Oct 2026,
it served ZQV26 (Oct 2026) through ZQM27 (Jun 2027), ten contracts, plus the
front continuous ZQ=F. The pull asks for the next CONTRACT_MONTHS and stores what
answers, keyed by instrument `YYYY-MM`.

THE ARITHMETIC (the standard meeting-day weighting, the one CME's FedWatch uses).
For a meeting whose decision lands on day d of a month with N days, the old rate
holds for days 1..d and the new rate for days d+1..N, so

    avg(M) = (d * pre + (N - d) * post) / N,    avg(M) = 100 - price(M).

Meetings are taken in order. Each one's POST rate is, when the following month
holds no meeting, simply that month's average -- nothing moves inside it:

    post = 100 - price(M+1)                                   (forward step)

and otherwise solved from the meeting month itself, given the pre rate:

    post = (N * avg(M) - d * pre) / (N - d)                   (backward step)

A meeting's PRE rate is the previous meeting's post rate. For the FIRST meeting
it is the month before's average when that month held no meeting and its
contract is stored; else it is solved from the meeting month given a
forward-step post:  pre = (N * avg(M) - (N - d) * post) / d.

The implied change at a meeting is post - pre in basis points; the implied
probability of a 25 bp move is |change| / 25, capped at one (a move larger than
25 bp is then "more than one step"). Gated against a hand-computed fixture in
tools/validate_prediction_markets.py.

FEWER THAN FOUR MEETINGS RETRIEVABLE -> the path prints "not yet tracked" and the
venue odds stand alone (brief 2.4).
"""

from __future__ import annotations

import calendar
import datetime as dt
import logging
from typing import Any, Callable, Optional

from . import derived, observations, session

log = logging.getLogger(__name__)

KEY = "fedfunds.futures_price"
MONTH_CODES = "FGHJKMNQUVXZ"
CONTRACT_MONTHS = 10
MIN_MEETINGS = 4


def symbol(year: int, month: int) -> str:
    return f"ZQ{MONTH_CODES[month - 1]}{year % 100:02d}.CBT"


def months_from(day: dt.date, n: int) -> list[tuple[int, int]]:
    y, m, out = day.year, day.month, []
    for _ in range(n):
        out.append((y, m))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def meeting_days(path=None) -> list[dt.date]:
    """FOMC decision days from the claims registry (cal.fomc_*)."""
    from . import claims as claims_mod                          # noqa: PLC0415
    reg = (claims_mod.load(path) or {}).get("claims") or {}
    out = []
    for cid, c in reg.items():
        if cid.startswith("cal.fomc"):
            for d in (c.get("detail") or {}).get("decision_days") or []:
                out.append(d if isinstance(d, dt.date) else dt.date.fromisoformat(str(d)))
    return sorted(set(out))


# ---------------------------------------------------------------------------
# The arithmetic
# ---------------------------------------------------------------------------
def implied_path(prices: dict[str, float], meetings: list[dt.date],
                 today: dt.date, n_meetings: int = 6) -> dict:
    """prices: {"YYYY-MM": futures price}. Returns the path and its absences."""
    avg = {k: 100.0 - float(v) for k, v in prices.items() if v is not None}
    upcoming = [m for m in meetings if m >= today][:n_meetings]
    mkey = lambda y, m: f"{y:04d}-{m:02d}"                      # noqa: E731
    meeting_months = {mkey(m.year, m.month) for m in meetings}

    def nxt(y, m):
        return (y + 1, 1) if m == 12 else (y, m + 1)

    def prv(y, m):
        return (y - 1, 12) if m == 1 else (y, m - 1)
    out: list[dict] = []
    pre: Optional[float] = None
    for i, md in enumerate(upcoming):
        k = mkey(md.year, md.month)
        N = calendar.monthrange(md.year, md.month)[1]
        d = md.day
        if k not in avg:
            break
        ny, nm = nxt(md.year, md.month)
        nk = mkey(ny, nm)
        forward = nk not in meeting_months and nk in avg
        if i == 0:
            py, pm = prv(md.year, md.month)
            pk = mkey(py, pm)
            if pk in avg and pk not in meeting_months:
                pre, how_pre = avg[pk], f"{pk} average"
            elif forward:
                post_f = avg[nk]
                pre = (N * avg[k] - (N - d) * post_f) / d
                how_pre = f"solved from {k} given {nk}"
            else:
                break
        else:
            how_pre = "previous meeting's post rate"
        if forward:
            post, how = avg[nk], f"{nk} average"
        else:
            if N == d:
                break
            post, how = (N * avg[k] - d * pre) / (N - d), f"solved from {k}"
        ch = derived.rate_bp_change(post, pre)
        out.append({"meeting": md.isoformat(), "pre_pct": round(pre, 4),
                    "post_pct": round(post, 4), "change_bp": ch,
                    "move_probability_25bp": round(min(1.0, abs(ch) / 25.0), 3),
                    "direction": "hike" if ch > 0 else ("cut" if ch < 0 else "hold"),
                    "post_from": how, "pre_from": how_pre})
        pre = post
    start = out[0]["pre_pct"] if out else None
    for r in out:
        r["cumulative_bp"] = derived.rate_bp_change(r["post_pct"], start)
    tracked = len(out) >= MIN_MEETINGS
    res: dict[str, Any] = {"meetings": out, "tracked": tracked,
                           "contracts": sorted(avg)}
    if not tracked:
        res["reason"] = (f"not yet tracked: {len(out)} of the next {MIN_MEETINGS} "
                         f"meetings retrievable from the stored contracts")
    elif out:
        last = out[min(len(out), MIN_MEETINGS) - 1]
        c = last["cumulative_bp"]
        word = "hikes" if c > 0 else "cuts"
        res["sentence"] = (
            f"the market prices {abs(c):.0f} bp of {word} by "
            f"{dt.date.fromisoformat(last['meeting']).strftime('%B %Y')}")
    return res


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------
def stored_prices(st: observations.ObservationStore, as_of: Optional[str] = None
                  ) -> tuple[dict[str, float], Optional[str]]:
    prices, newest = {}, None
    for inst in st.instruments(KEY):
        r = st.latest_as_of(KEY, as_of, inst)
        if r and r.get("value_num") is not None:
            prices[inst] = r["value_num"]
            d = str(r["observed_at"])[:10]
            newest = max(newest or d, d)
    return prices, newest


def path_as_of(as_of: Optional[str] = None, store=None) -> dict:
    own = store is None
    st = store or observations.ObservationStore()
    try:
        prices, newest = stored_prices(st, as_of)
    finally:
        if own:
            st.close()
    today = dt.date.fromisoformat((as_of or session.utc_iso())[:10])
    res = implied_path(prices, meeting_days(), today)
    res["as_of"] = newest
    if res.get("sentence") and newest:
        res["sentence"] += f" (fed funds futures, as of {newest})"
    return res


def pull(store=None, fetcher: Optional[Callable] = None, dry_run: bool = False,
         run_id: Optional[str] = None) -> dict:
    """The next CONTRACT_MONTHS settlements into the store. Never raises."""
    if fetcher is None:
        import yfinance as yf                                   # noqa: PLC0415

        def fetcher(sym):
            return yf.Ticker(sym).history(period="5d", interval="1d")
    today = session.session_date_obj()
    fetched = session.utc_iso()
    rows, served, failed = [], [], {}
    for y, m in months_from(today, CONTRACT_MONTHS):
        sym = symbol(y, m)
        try:
            h = fetcher(sym)
            if h is None or len(h) == 0:
                failed[sym] = "no bars served"
                continue
            px = float(h["Close"].iloc[-1])
            day = h.index[-1].date().isoformat()
            served.append(sym)
            rows.append({"registry_key": KEY, "instrument": f"{y:04d}-{m:02d}",
                         "observed_at": day, "available_at": fetched, "value": px,
                         "source": "yfinance", "run_id": run_id,
                         "availability_kind": "ingest_instant"})
        except Exception as exc:                                # noqa: BLE001
            failed[sym] = f"{type(exc).__name__}: {exc}"[:120]
    out = {"served": served, "failed": failed, "dry_run": dry_run}
    if not dry_run and rows:
        own = store is None
        st = store or observations.ObservationStore()
        try:
            out["written"] = st.write_many(rows)
        finally:
            if own:
                st.close()
    return out


def _main(argv: list[str]) -> int:
    import argparse
    import json
    ap = argparse.ArgumentParser(description="Fed funds futures and the rate path.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pull")
    p.add_argument("--dry-run", action="store_true")
    q = sub.add_parser("path")
    q.add_argument("--as-of", default=None)
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO)
    res = pull(dry_run=a.dry_run) if a.cmd == "pull" else path_as_of(a.as_of)
    print(json.dumps(res, indent=2, default=str))
    return 0


if __name__ == "__main__":                                      # pragma: no cover
    import sys
    raise SystemExit(_main(sys.argv[1:]))
