"""
The levered-ETF close-flow estimate (signal-triage Batch 22 item 116, the order's
98.1; SR-77, provisional; A127, 6 Nov 2026). Settings and roster:
config/levered_etf.yaml.

    python -m altdata.close_flow estimate --slot 1500 [--date D] [--dry-run]
    python -m altdata.close_flow show [--date D]
    python -m altdata.close_flow per-move           # V-98c: $ per 1% move, from the roster

THE ESTIMATE. rebalance notional = sum over the funds of AUM x L x (L - 1) x r:
AUM the fund's assets at the prior session's close (levetf.aum, the newest row
observed before the day, at most `aum_max_age_days` old), L its leverage, r its
underlying's return from the prior close to the estimate's instant. A 3x fund
trades 6 x AUM x r, a -3x 12 x AUM x r. By bucket and in total, in dollars and as
a percent of the bucket's ADV (the 20-session average of the stored close x the
stored volume of the instruments driving the bucket, through the session before).

TWO ESTIMATES A SESSION, each stored as calc.close_flow.<bucket>, .total and their
_pct_adv, instrument = the slot, observed_at = the session, available_at = the
instant computed:
  1500  the 15:00 pass (scripts/run_close_flow.sh): the AUM writers are re-read
        first (non-fatal), then each underlying's last completed 5-minute bar at
        or before 15:00 ET from Yahoo, for basket symbols only (D33), against its
        stored prior close.
  1645  the 16:45 close (daily_cascade/stack.py, stored by stack_close): each
        underlying's stored close against its stored prior close.
  MSTR and COIN (D66 ruling 2, A127b) are read from the captured option chains,
  item 49's treasury read: the session's newest chain at or before the instant
  against the previous session's newest chain (the chain's spot, not the
  official close). SNDK has no chain: "gap: no keyless price".
History builds from the first live run; nothing is backfilled by hand.

THE FLAG (O-1): at 15:00, |the total| of $20bn or more. After 60 stored 15:00
sessions, the 90th percentile of the box's own history of |the total| in % of ADV,
by itself (flag_rule() counts the stored sessions and names the session the rule
changed on). Alert-only; no rights.

Report-only: nothing here enters a composite, the market-state object, the T&B
intake queue or a regime.
"""

from __future__ import annotations

import datetime as dt
import logging
import math
import sys
from pathlib import Path
from typing import Any, Callable, Optional

import yaml

from . import session

log = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / "config" / "levered_etf.yaml"
PREFIX = "calc.close_flow."
SOURCE = "close_flow"
SLOTS = ("1500", "1645")
TITLE = "Levered-ETF close flow (estimate)"
NOT_READ_D33 = "underlying not read (not in the price basket; D33 admits no new Yahoo symbol)"
# The captured chains' directory; None is chain_metrics.chain_dir() (a gate sets it).
CHAIN_BASE: Optional[Path] = None


def config(path: Optional[Path] = None) -> dict:
    return yaml.safe_load(Path(path or CONFIG).read_text(encoding="utf-8")) or {}


def bucket_ids(cfg: Optional[dict] = None) -> list[str]:
    return [b["id"] for b in (cfg or config())["buckets"]]


def store_keys(cfg: Optional[dict] = None) -> list[str]:
    """Every key this module stores: each bucket and the total, $ and % of ADV."""
    ids = bucket_ids(cfg) + ["total"]
    return [PREFIX + i for i in ids] + [PREFIX + i + "_pct_adv" for i in ids]


def factor(leverage: float) -> float:
    """L x (L - 1): 6 for 3x, 2 for 2x and -1x, 6 for -2x, 12 for -3x."""
    L = float(leverage)
    return L * (L - 1.0)


# ---------------------------------------------------------------------------
# The arithmetic (pure; the gate drives it on a fixture roster)
# ---------------------------------------------------------------------------
def estimate(cfg: dict, aum: dict[str, Optional[float]],
             returns: dict[str, Optional[float]],
             adv: dict[str, Optional[float]],
             why_aum: Optional[dict[str, str]] = None,
             why_ret: Optional[dict[str, str]] = None) -> dict:
    """{buckets: [...], total: {...}, funds: [...], left_out: {ticker: why}}.

    `aum` by ticker (the prior close's), `returns` and `adv` by underlying id. A
    fund with no AUM or no return is left out and named; a bucket with no fund
    estimated is "not estimated"; a bucket's % of ADV needs its ADV."""
    why_aum, why_ret = why_aum or {}, why_ret or {}
    left: dict[str, str] = {}
    per_bucket: dict[str, dict] = {b["id"]: {"flow": 0.0, "n": 0, "funds": []}
                                   for b in cfg["buckets"]}
    funds_out = []
    for f in cfg["funds"]:
        t, u = f["ticker"], f["underlying"]
        ux = (cfg.get("underlyings") or {}).get(u) or {}
        if f.get("method") == "gap":
            left[t] = f"gap: {f.get('gap')}" + (
                f"; {ux.get('label') or u}: {ux['gap']}" if ux.get("gap") else "")
            continue
        a, r = aum.get(t), returns.get(u)
        if a is None:
            left[t] = why_aum.get(t) or "no AUM stored"
            continue
        if r is None:
            left[t] = why_ret.get(u) or f"no return for {u}"
            continue
        flow = a * factor(f["leverage"]) * r
        b = per_bucket[f["bucket"]]
        b["flow"] += flow
        b["n"] += 1
        b["funds"].append(t)
        funds_out.append({"ticker": t, "bucket": f["bucket"], "aum": a,
                          "leverage": f["leverage"], "r": r, "flow": flow})
    buckets, tot, tot_adv_ids = [], 0.0, []
    for b in cfg["buckets"]:
        x = per_bucket[b["id"]]
        advs = [adv.get(u) for u in b.get("adv") or []]
        badv = sum(v for v in advs if v) if advs and all(v for v in advs) else None
        est = x["n"] > 0
        buckets.append({"id": b["id"], "label": b["label"],
                        "flow": x["flow"] if est else None, "n": x["n"],
                        "funds": x["funds"], "adv": badv,
                        "pct_adv": (100.0 * x["flow"] / badv
                                    if est and badv else None)})
        if est:
            tot += x["flow"]
            tot_adv_ids += [u for u in b.get("adv") or [] if u not in tot_adv_ids]
    any_est = any(b["n"] for b in buckets)
    tadv_v = [adv.get(u) for u in tot_adv_ids]
    tadv = sum(tadv_v) if tadv_v and all(tadv_v) else None
    return {"buckets": buckets, "funds": funds_out, "left_out": left,
            "total": {"flow": tot if any_est else None, "adv": tadv,
                      "pct_adv": (100.0 * tot / tadv if any_est and tadv else None),
                      "n": sum(b["n"] for b in buckets)}}


def per_move(cfg: dict, aum: dict[str, Optional[float]], move: float = 0.01) -> dict:
    """V-98c: dollars of rebalance per `move` (1%) in every underlying at once,
    by bucket and in total, over the funds with an AUM. A 1% fall sells this."""
    rets = {u: move for u in cfg["underlyings"]}
    e = estimate(cfg, aum, rets, {})
    return {"total": e["total"]["flow"], "n": e["total"]["n"],
            "buckets": {b["id"]: b["flow"] for b in e["buckets"]},
            "left_out": e["left_out"]}


def rows(est: dict, slot: str, day: str, now: str) -> list[dict]:
    """The calc rows of one estimate: each estimated bucket and the total, $ and
    % of ADV, instrument = the slot."""
    out = []

    def put(key: str, v: Optional[float]) -> None:
        if v is not None and math.isfinite(v):
            out.append({"registry_key": PREFIX + key, "instrument": slot,
                        "observed_at": day, "available_at": now, "value": float(v),
                        "source": SOURCE})
    for b in est["buckets"]:
        put(b["id"], b["flow"])
        put(b["id"] + "_pct_adv", b["pct_adv"])
    put("total", est["total"]["flow"])
    put("total_pct_adv", est["total"]["pct_adv"])
    return out


# ---------------------------------------------------------------------------
# The flag and its dated switch (O-1)
# ---------------------------------------------------------------------------
def _percentile(xs: list[float], p: float) -> float:
    s = sorted(xs)
    if len(s) == 1:
        return s[0]
    k = (len(s) - 1) * p / 100.0
    lo, hi = math.floor(k), math.ceil(k)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def flag_rule(history: list[tuple[str, float]], cfg: dict) -> dict:
    """The rule in force for a session, from the stored 15:00 history BEFORE it:
    [(session, total % of ADV)]. Fewer than `after_sessions` stored sessions: the
    dollar threshold. From then on: the percentile of |the history|, and `since`,
    the session after the one that completed the count -- the switch, dated."""
    fl = cfg["flag"]
    sw = fl["switch"]
    need = int(sw["after_sessions"])
    hist = sorted((d, v) for d, v in history if v is not None)
    if len(hist) < need:
        return {"basis": "dollars", "threshold": float(fl["dollar_threshold"]),
                "stored": len(hist), "after_sessions": need, "since": None}
    since = next_session(hist[need - 1][0])
    thr = _percentile([abs(v) for _, v in hist], float(sw["percentile"]))
    return {"basis": "pct_adv", "threshold": thr, "percentile": float(sw["percentile"]),
            "stored": len(hist), "after_sessions": need, "since": since}


def next_session(day: str) -> str:
    d = dt.date.fromisoformat(day) + dt.timedelta(days=1)
    while not session.is_trading_session(d):
        d += dt.timedelta(days=1)
    return d.isoformat()


def flag(total: dict, rule: dict) -> dict:
    """{fired, value, line}: |the 15:00 total| at or over the rule's threshold."""
    v = total.get("flow") if rule["basis"] == "dollars" else total.get("pct_adv")
    if v is None:
        return {"fired": None, "value": None, "rule": rule,
                "line": "Close-flow flag (15:00): not read -- no 15:00 estimate."}
    fired = abs(v) >= rule["threshold"]
    if rule["basis"] == "dollars":
        cond = (f"|{usd(v)}| {'>=' if fired else '<'} the "
                f"${rule['threshold'] / 1e9:,.0f}bn threshold (O-1; the percentile "
                f"rule from the {_ord(rule['after_sessions'])} stored session, "
                f"{rule['stored']} stored)")
    else:
        cond = (f"|{v:+.1f}% of ADV| {'>=' if fired else '<'} the "
                f"{_ord(rule['percentile'])} percentile of the box's own 15:00 history, "
                f"{rule['threshold']:.1f}% (n={rule['stored']}; in force since "
                f"{rule['since']}, O-1)")
    side = "buying" if (total.get("flow") or 0) > 0 else "selling"
    word = f"FIRED ({side} into the close)" if fired else "not fired"
    return {"fired": fired, "value": v, "rule": rule,
            "line": f"Close-flow flag (15:00): {word} -- {cond}. Alert-only; no rights."}


def _ord(p: float) -> str:
    from .numeral_audit import ordinal                          # noqa: PLC0415
    return ordinal(p)


def usd(v: Optional[float]) -> str:
    if v is None:
        return "—"
    s = "+" if v > 0 else ("-" if v < 0 else "")
    return f"{s}${abs(v) / 1e9:,.1f}bn"


# ---------------------------------------------------------------------------
# Reading the store (point in time, as of the cutoff)
# ---------------------------------------------------------------------------
def _pts(st, key: str, cutoff: str, instrument: Optional[str] = None
         ) -> list[tuple[str, float]]:
    return sorted((str(r["observed_at"])[:10], float(r["value_num"]))
                  for r in st.as_of(key, cutoff, instrument)
                  if r.get("value_num") is not None)


def prior_aum(st, cfg: dict, day: str, cutoff: str) -> tuple[dict, dict]:
    """({ticker: AUM at the newest close before `day`}, {ticker: why not})."""
    max_age = int(cfg.get("aum_max_age_days") or 5)
    out, why = {}, {}
    for f in cfg["funds"]:
        if f.get("method") == "gap":
            continue
        pts = [(d, v) for d, v in _pts(st, cfg["aum_key"], cutoff, f["ticker"]) if d < day]
        if not pts:
            why[f["ticker"]] = "no AUM stored"
            continue
        d, v = pts[-1]
        if (dt.date.fromisoformat(day) - dt.date.fromisoformat(d)).days > max_age:
            why[f["ticker"]] = f"AUM {d} older than {max_age} days"
            continue
        out[f["ticker"]] = v
    return out, why


def adv_by_underlying(st, cfg: dict, day: str, cutoff: str) -> dict[str, Optional[float]]:
    """20-session average dollar volume through the session before `day`."""
    n, m = int(cfg.get("adv_sessions") or 20), int(cfg.get("adv_min_sessions") or 15)
    out: dict[str, Optional[float]] = {}
    for u, x in cfg["underlyings"].items():
        k = x.get("store_key")
        if not k:
            out[u] = None
            continue
        close = dict(_pts(st, k, cutoff))
        vol = [(d, v) for d, v in _pts(st, k + "_volume", cutoff) if d < day]
        dv = [close[d] * v for d, v in vol[-n:] if d in close and v > 0]
        out[u] = sum(dv) / len(dv) if len(dv) >= m else None
    return out


def _chain(symbol: str, day: str, at_or_before: str) -> Optional[tuple[float, str]]:
    from .sources.treasury import chain_spot                    # noqa: PLC0415
    return chain_spot(day, CHAIN_BASE, symbol, at_or_before=at_or_before)


def chain_return(x: dict, day: str, at_or_before: str,
                 max_age: Optional[dt.timedelta] = None
                 ) -> tuple[Optional[float], Optional[str], dict]:
    """(r, why not, used): the session's newest captured chain spot at or before
    the instant against the previous session's newest (D66 ruling 2)."""
    sym = x["chain"]
    now = _chain(sym, day, at_or_before)
    if not now:
        return None, f"no captured {sym} chain on {day} by the estimate's instant", {}
    if max_age is not None:
        at = dt.datetime.fromisoformat(at_or_before.replace("Z", "+00:00"))
        got = dt.datetime.fromisoformat(now[1].replace("Z", "+00:00"))
        got = got if got.tzinfo else got.replace(tzinfo=dt.timezone.utc)
        if at - got > max_age:
            return None, (f"the newest {sym} chain ({now[1]}) is older than "
                          f"{int(max_age.total_seconds() // 60)} minutes"), {}
    prev_day = session.previous_trading_session(day).isoformat()
    prev = _chain(sym, prev_day, at_or_before)
    if not prev or not prev[0]:
        return None, f"no captured {sym} chain on {prev_day}", {}
    return now[0] / prev[0] - 1.0, None, {
        "symbol": sym, "source": "captured chain spot (not the official close)",
        "fetched_at": now[1], "price": now[0], "prior_fetched_at": prev[1],
        "prior_price": prev[0]}


def close_returns(st, cfg: dict, day: str, cutoff: str) -> tuple[dict, dict]:
    """16:45: {underlying: the day's close against the prior stored close}; a
    chain underlying, its chain spot."""
    rets, why = {}, {}
    for u, x in cfg["underlyings"].items():
        k = x.get("store_key")
        if x.get("gap"):
            why[u] = x["gap"]
            continue
        if x.get("chain"):
            r, w, _ = chain_return(x, day, cutoff)
            if r is None:
                why[u] = w
            else:
                rets[u] = r
            continue
        if not k:
            why[u] = NOT_READ_D33
            continue
        pts = _pts(st, k, cutoff)
        today = [v for d, v in pts if d == day]
        prev = [v for d, v in pts if d < day]
        if not today or not prev or not prev[-1]:
            why[u] = f"no stored close for {day} and the session before ({k})"
            continue
        rets[u] = today[-1] / prev[-1] - 1.0
    return rets, why


def _et(day: str, hm: str) -> dt.datetime:
    h, m = (int(x) for x in hm.split(":"))
    return dt.datetime.combine(dt.date.fromisoformat(day), dt.time(h, m),
                               tzinfo=session._eastern_tz())     # noqa: SLF001


def intraday_returns(st, cfg: dict, day: str, cutoff: str, now: dt.datetime,
                     fetcher: Optional[Callable] = None) -> tuple[dict, dict, dict]:
    """15:00: ({underlying: r}, {underlying: why not}, {underlying: price used}).
    The last completed 5-minute bar at or before 15:00 ET against the stored
    prior close. Basket symbols only (D33)."""
    if fetcher is None:
        from .note_fetch import yf_fetcher as fetcher            # noqa: PLC0415
    at = _et(day, cfg["slots"]["1500"]["at"])
    # AN EARLY CLOSE (13:00 ET) has rebalanced before 15:00: read the close.
    close_at = dt.datetime.combine(dt.date.fromisoformat(day), session.close_time_et(day),
                                   tzinfo=session._eastern_tz())  # noqa: SLF001
    at = min(at, close_at)
    max_age = dt.timedelta(minutes=int((cfg.get("intraday") or {})
                                       .get("max_bar_age_minutes") or 15))
    chain_age = dt.timedelta(minutes=int((cfg.get("chain_spot") or {})
                                         .get("max_age_minutes_1500") or 180))
    rets, why, used = {}, {}, {}
    for u, x in cfg["underlyings"].items():
        sym, k = x.get("yahoo"), x.get("store_key")
        if x.get("gap"):
            why[u] = x["gap"]
            continue
        if x.get("chain"):
            r, w, info = chain_return(x, day, min(now, at).isoformat(), chain_age)
            if r is None:
                why[u] = w
            else:
                rets[u], used[u] = r, info
            continue
        if not sym or not k:
            why[u] = NOT_READ_D33
            continue
        prev = [v for d, v in _pts(st, k, cutoff) if d < day]
        if not prev or not prev[-1]:
            why[u] = f"no stored prior close ({k})"
            continue
        try:
            bars = fetcher(sym, _et(day, "09:30"), min(now, at + dt.timedelta(minutes=5)))
        except Exception as exc:                                # noqa: BLE001
            why[u] = f"intraday read failed: {type(exc).__name__}: {exc}"[:160]
            continue
        done = []
        for b in bars:
            end = dt.datetime.fromisoformat(b["observed_at"]) + dt.timedelta(minutes=5)
            if end <= at and end <= now:
                done.append((end, float(b["close"])))
        if not done or at - max(done)[0] > max_age:
            why[u] = f"no completed 5-minute bar within {max_age} of 15:00 ({sym})"
            continue
        end, px = max(done)
        rets[u] = px / prev[-1] - 1.0
        used[u] = {"symbol": sym, "bar_end": end.isoformat(), "price": px,
                   "prior_close": prev[-1]}
    return rets, why, used


def history_1500(st, day: str, cutoff: str) -> list[tuple[str, float]]:
    return [(d, v) for d, v in _pts(st, PREFIX + "total_pct_adv", cutoff, "1500")
            if d < day]


def stored(st, day: str, cutoff: str, slot: str, cfg: Optional[dict] = None) -> dict:
    """A stored estimate, rebuilt from its calc rows: {bucket id: ($, % ADV)}."""
    cfg = cfg or config()
    out = {}
    for i in bucket_ids(cfg) + ["total"]:
        f = [v for d, v in _pts(st, PREFIX + i, cutoff, slot) if d == day]
        p = [v for d, v in _pts(st, PREFIX + i + "_pct_adv", cutoff, slot) if d == day]
        out[i] = (f[-1] if f else None, p[-1] if p else None)
    return out


def for_close(st, day: str, cutoff: str, cfg: Optional[dict] = None) -> dict:
    """The 16:45 estimate from stored closes, in memory (the close stores it)."""
    cfg = cfg or config()
    aum, why_a = prior_aum(st, cfg, day, cutoff)
    rets, why_r = close_returns(st, cfg, day, cutoff)
    est = estimate(cfg, aum, rets, adv_by_underlying(st, cfg, day, cutoff), why_a, why_r)
    est.update({"slot": "1645", "day": day})
    return est


def flag_for(st, day: str, cutoff: str, cfg: Optional[dict] = None) -> dict:
    """The 15:00 flag as of `cutoff`: the stored 15:00 total against the rule the
    history before the day sets."""
    cfg = cfg or config()
    s = stored(st, day, cutoff, "1500", cfg)["total"]
    return flag({"flow": s[0], "pct_adv": s[1]},
                flag_rule(history_1500(st, day, cutoff), cfg))


# ---------------------------------------------------------------------------
# The 15:00 pass
# ---------------------------------------------------------------------------
def refresh_aum(dry_run: bool = False) -> dict:
    """Both AUM writers, non-fatal: the 15:00 estimate wants the prior close's AUM,
    which ProShares posts the evening before and the others the morning of."""
    out = {}
    if dry_run:
        return {"skipped": "dry run"}
    for name in ("proshares", "levered_etf"):
        try:
            from importlib import import_module                 # noqa: PLC0415
            r = import_module(f"altdata.sources.{name}").pull()
            out[name] = {"status": r.get("status"), "written": r.get("written"),
                         "not_read": r.get("not_read")}
        except Exception as exc:                                # noqa: BLE001
            out[name] = {"status": "error", "reason": f"{type(exc).__name__}: {exc}"[:200]}
    return out


def run_1500(day: Optional[str] = None, dry_run: bool = False, db_path=None,
             fetcher: Optional[Callable] = None, now: Optional[dt.datetime] = None,
             refresh: bool = True) -> dict:
    from . import observations                                  # noqa: PLC0415
    from .sources.levered_etf import assert_unrestricted        # noqa: PLC0415
    cfg = config()
    assert_unrestricted([f["ticker"] for f in cfg["funds"]])
    now = now or dt.datetime.now(dt.timezone.utc)
    day = day or session.session_date()
    summary: dict[str, Any] = {"slot": "1500", "day": day,
                               "aum": refresh_aum(dry_run) if refresh else "not refreshed"}
    cutoff = now.isoformat()
    st = (observations.ObservationStore(db_path) if dry_run
          else observations.open_writer("close_flow", db_path))
    try:
        aum, why_a = prior_aum(st, cfg, day, cutoff)
        rets, why_r, used = intraday_returns(st, cfg, day, cutoff, now, fetcher)
        est = estimate(cfg, aum, rets, adv_by_underlying(st, cfg, day, cutoff),
                       why_a, why_r)
        fl = flag(est["total"], flag_rule(history_1500(st, day, cutoff), cfg))
        out_rows = rows(est, "1500", day, session.utc_iso())
        if out_rows and not dry_run:
            st.write_many(out_rows)
    finally:
        st.close()
    summary.update({"total": est["total"], "flag": fl["line"], "fired": fl["fired"],
                    "buckets": {b["id"]: b["flow"] for b in est["buckets"]},
                    "left_out": est["left_out"], "prices": used,
                    "written": 0 if dry_run else len(out_rows)})
    return summary


def per_move_now(db_path=None, cutoff: Optional[str] = None) -> dict:
    """V-98c from the store: the newest AUM of every roster fund."""
    from . import observations                                  # noqa: PLC0415
    cfg = config()
    with observations.ObservationStore(db_path) as st:
        aum = {}
        for f in cfg["funds"]:
            pts = _pts(st, cfg["aum_key"], cutoff or session.utc_iso(), f["ticker"])
            if pts and f.get("method") != "gap":
                aum[f["ticker"]] = pts[-1][1]
    return per_move(cfg, aum)


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    import json                                                 # noqa: PLC0415
    ap = argparse.ArgumentParser(description="the levered-ETF close-flow estimate")
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("estimate", help="the 15:00 estimate (the 15:00 pass)")
    e.add_argument("--slot", choices=["1500"], default="1500")
    e.add_argument("--date")
    e.add_argument("--dry-run", action="store_true")
    e.add_argument("--db")
    s = sub.add_parser("show", help="the stored estimates and the flag for a session")
    s.add_argument("--date")
    s.add_argument("--db")
    p = sub.add_parser("per-move", help="V-98c: $ per 1% move from the stored AUM")
    p.add_argument("--db")
    a = ap.parse_args(argv)
    if a.cmd == "estimate":
        out = run_1500(a.date, a.dry_run, a.db)
        print(json.dumps(out, indent=2, default=str))
        return 0
    if a.cmd == "per-move":
        print(json.dumps(per_move_now(a.db), indent=2, default=str))
        return 0
    from . import observations                                  # noqa: PLC0415
    day = a.date or session.session_date()
    with observations.ObservationStore(a.db) as st:
        cut = session.utc_iso()
        print(json.dumps({"1500": stored(st, day, cut, "1500"),
                          "1645": stored(st, day, cut, "1645"),
                          "flag": flag_for(st, day, cut)["line"]}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    sys.exit(_main(sys.argv[1:]))
