"""
The system's own event base rates (X-3.1, first half: "the system's own event base
rates first; the engine second").

    python -m alpha.event_rates compute [--as-of ISO] [--store PATH] [--ledger PATH]
    python -m alpha.event_rates show    [--ledger PATH]

FROM THE STORE, READ-ONLY, INTO alpha.db ONLY (the `event_base_rates` table). For
CPI, payrolls and FOMC (config/alpha_events.yaml):

  first_session_drift_pct   SPY's open-to-close return in the first session after
                            the print: the release day for an 08:30 print, the
                            next session for a 14:00 statement
  next_session_drift_pct    SPY's open-to-close return in the first session the
                            lab's nightly loop can enter after the print became
                            knowable (what engine 4 trades)
  vix_change_pts            the VIX's close on the event day less the close
                            before it, in points: the volatility crush is a fall

each over every event and again by bucket: the surprise's sign and size, stored
positioning (the CFTC speculative net's two-year z), and the dealer regime (the
regime word each capture's gate stored, exposure.regime_word, read by name;
"awaiting" where the key has no row). And for earnings in the
29-name universe: the drift 1 and 20 sessions after, by the sign of the real
(vs consensus) surprise, and the realised reaction; the implied move against it
prints "awaiting" (no implied move is stored).

Every row carries n, the window (first and last event day) and its unit. A hit
rate is the share above zero for a drift and the share below zero (a crush) for
the VIX. A bucket with no event prints nothing; a bucket that cannot be read
prints "awaiting" with the reason. A naive surprise is labelled naive everywhere:
it is not a consensus surprise and is never quoted as one (altdata/surprise.py).

THE EVENTS. Release days come from the events table (rows of type release or
scheduled carrying the series' entity, at or before the cutoff) and, for the
history before the table, from the first vintage of the series' ALFRED rows
(availability_kind observed: the first publication's instant). FOMC days come
from the claims rows (kind fomc). Each event's inputs are read as they were
first published; its decision instant is the first nightly loop at or after all
of them were knowable (alpha/pit.py), and an event whose inputs became knowable
more than `stale_sessions` sessions after it (a backfill ingested later) is left
out of the engine's rows and counted.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import statistics
import sys
from pathlib import Path
from typing import Any, Optional

import yaml

from altdata import session

from . import config as acfg
from . import pit

CONFIG = acfg.REPO / "config" / "alpha_events.yaml"
MACRO = ("cpi", "payrolls", "fomc")
STALE_SESSIONS = 5
AWAITING = "awaiting"


def load_config(path: Optional[Path] = None) -> dict:
    return yaml.safe_load(Path(path or CONFIG).read_text(encoding="utf-8")) or {}


# ---------------------------------------------------------------------------
# The event days
# ---------------------------------------------------------------------------
def _events(store, sql: str, args: tuple) -> list[dict]:
    have = store.conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND "
                              "name='events'").fetchone()
    if not have:
        return []
    return [dict(r) for r in store.conn.execute(sql, args).fetchall()]


def release_days(store, ev: dict, cutoff: str) -> list[dict]:
    """[{day, source, known_at}] for one macro event, ascending, deduplicated
    within five days (the events table's day wins over an ALFRED-derived one)."""
    c = pit.canon(cutoff)
    out: dict[str, dict] = {}
    if ev.get("claims_kind"):
        for r in _events(store, "SELECT observed_at, available_at, payload FROM events "
                         "WHERE type='scheduled' AND source='claims' AND "
                         "observed_at<=?", (c,)):
            try:
                kind = (json.loads(r["payload"] or "{}") or {}).get("kind")
            except ValueError:
                kind = None
            if kind == ev["claims_kind"]:
                d = pit.et_date(r["observed_at"])
                out[d] = {"day": d, "source": "events:claims",
                          "known_at": pit.canon(r["available_at"])}
    elif ev.get("entity"):
        for r in _events(store, "SELECT e.observed_at, e.available_at FROM events e "
                         "JOIN event_entities x ON x.event_id=e.id WHERE "
                         "x.entity=? AND e.type IN ('release','scheduled') AND "
                         "e.observed_at<=?", (ev["entity"], c)):
            d = pit.et_date(r["observed_at"])
            out[d] = {"day": d, "source": "events", "known_at": pit.canon(r["available_at"])}
        if ev.get("series"):
            s = pit.Series(store, ev["series"])
            for period in s.days:
                fv = s.first_vintage(period)
                if not fv or fv[2] != "observed" or fv[1] > c:
                    continue
                d = pit.et_date(fv[1])
                if any(abs((_d(d) - _d(x)).days) <= 5 for x in out):
                    continue
                out[d] = {"day": d, "source": "alfred", "known_at": fv[1]}
    return [out[d] for d in sorted(out) if session.is_trading_session(_d(d))]


def _d(day: str) -> dt.date:
    return dt.date.fromisoformat(day[:10])


# ---------------------------------------------------------------------------
# The conditioners
# ---------------------------------------------------------------------------
def surprise_series(store, ev: dict) -> tuple[Optional[pit.Series], str]:
    """The release's surprise series and what it is. The CONSENSUS surprise
    (ST-R6.48f, calc.consensus_surprise.<id>, read by key name) where a row is
    stored; else the declared fallback (the naive surprise, labelled so); else
    none."""
    ck = ev.get("consensus_surprise")
    if ck:
        cs = pit.Series(store, ck)
        if cs:
            return cs, (f"consensus: actual less the stored consensus ({ck}, the "
                        f"surprise index, ST-R6.48f)")
    if ev.get("surprise"):
        return pit.Series(store, ev["surprise"]), str(ev.get("surprise_kind") or "")
    return None, str(ev.get("surprise_kind") or "")


def surprise_for(sur: pit.Series, day: str) -> Optional[dict]:
    """The surprise first published on the release day or within four days
    after it (a live pull lands the next morning), with its size against the
    previous surprises' spread."""
    if not sur:
        return None
    best = None
    for period in sur.days:
        fv = sur.first_vintage(period)
        if not fv:
            continue
        lag = (_d(pit.et_date(fv[1])) - _d(day)).days
        if 0 <= lag <= 4 and (best is None or lag < best[0]):
            best = (lag, period, fv)
    if best is None:
        return None
    _, period, (value, avail, _) = best
    return {"period": period, "value": value, "available_at": avail}


def size_bucket(sur: pit.Series, s: dict, cfg: dict) -> str:
    sz = cfg.get("surprise_size") or {}
    prior = [sur.first_vintage(p)[0] for p in sur.days if p < s["period"]
             and sur.first_vintage(p)][-int(sz.get("window", 24)):]
    sign = "positive" if s["value"] > 0 else ("negative" if s["value"] < 0 else "zero")
    if sign == "zero":
        return "zero"
    if len(prior) < int(sz.get("min_prior", 8)):
        return f"{sign}, size unknown"
    sd = statistics.stdev(prior)
    big = sd > 0 and abs(s["value"]) / sd >= float(sz.get("large_sd", 1.0))
    return f"{sign}, {'large' if big else 'small'}"


def positioning_bucket(cot: pit.Series, cutoff: str, cfg: dict) -> str:
    p = cfg.get("positioning") or {}
    if not cot:
        return AWAITING
    since = (_d(pit.et_date(cutoff))
             - dt.timedelta(days=int(p.get("window_days", 730)))).isoformat()
    xs = [v for _, v in cot.known(cutoff, since=since)]
    if len(xs) < int(p.get("min_rows", 52)):
        return AWAITING
    sd = statistics.stdev(xs)
    z = (xs[-1] - statistics.fmean(xs)) / sd if sd else 0.0
    cz = float(p.get("crowded_z", 1.5))
    return "crowded long" if z >= cz else ("crowded short" if z <= -cz else "neutral")


DEALER_WORDS = ("positive gamma", "negative gamma", "indeterminate")


def regime_words(store, key: Optional[str], instrument: Optional[str]) -> dict:
    """{day: [(available_at, word)]}: the regime word as the capture's gate stored
    it (altdata/dealer_store.py, decision 9 of 19 Oct 2026), every vintage by
    day in availability order. The bucket reads the word; it computes none."""
    out: dict[str, list[tuple[str, str]]] = {}
    if store is None or not key:
        return out
    for r in store.all_vintages(key, instrument):
        w = r.get("value_text")
        if w:
            out.setdefault(str(r["observed_at"])[:10], []).append(
                (pit.canon(r["available_at"]), str(w)))
    for v in out.values():
        v.sort(key=lambda x: x[0])
    return out


def dealer_bucket(words: dict, cutoff: str, cfg: dict) -> str:
    """The newest stored regime word knowable at `cutoff`, within max_age_days;
    "awaiting" where none is."""
    d = cfg.get("dealer") or {}
    c = pit.canon(cutoff)
    known = [(day, ok[-1][1]) for day in sorted(words)
             for ok in [[x for x in words[day] if x[0] <= c]] if ok]
    if not known:
        return AWAITING
    day, w = known[-1]
    if (_d(pit.et_date(cutoff)) - _d(day)).days > int(d.get("max_age_days", 3)):
        return AWAITING
    return w if w in DEALER_WORDS else AWAITING


# ---------------------------------------------------------------------------
# The events, measured
# ---------------------------------------------------------------------------
class Prices:
    """SPY's closes and opens and the VIX, newest vintage (descriptive)."""

    def __init__(self, store, cfg: dict) -> None:
        k = cfg["price"]["key"]
        self.close, self.open = pit.Series(store, k), pit.Series(store, f"{k}_open")
        self.vix = pit.Series(store, cfg["vix"]["key"])

    def oc(self, day: str) -> Optional[float]:
        o, c = self.open.latest(day), self.close.latest(day)
        return (c / o - 1) * 100 if o and c else None


def macro_rows(store, cfg: dict, cutoff: str, prices: Optional[Prices] = None) -> dict:
    """{event: [row]} -- every release with its measures and buckets. A row's
    `decided_at` is the first nightly loop after its inputs were all knowable;
    `trade_day` the next session; `stale` true when that is more than
    STALE_SESSIONS sessions after the event."""
    px = prices or Prices(store, cfg)
    pc = cfg.get("positioning") or {}
    dc = cfg.get("dealer") or {}
    cot = pit.Series(store, pc.get("key"), pc.get("instrument")) if pc else None
    words = regime_words(store, dc.get("regime_word"), dc.get("instrument")) if dc else {}
    out: dict[str, list] = {}
    for name in MACRO:
        ev = (cfg.get("events") or {}).get(name)
        if not ev:
            continue
        sur, sur_kind = surprise_series(store, ev)
        rows = []
        for e in release_days(store, ev, cutoff):
            day = e["day"]
            pre_open = str(ev.get("time", "08:30")) < "09:30"
            first = day if pre_open else pit.next_session(day)
            s = surprise_for(sur, day) if sur is not None else None
            avail = [px.close.avail(day) or pit.canon(cutoff)]
            if s:
                avail.append(s["available_at"])
            dday, decided = pit.nightly_after(max(avail))
            trade = pit.next_session(dday)
            stale = _sessions_between(day, dday) > STALE_SESSIONS
            prev = pit.prev_session(day)
            vc, vp = px.vix.latest(day), px.vix.latest(prev)
            if s and sur:
                sb = size_bucket(sur, s, cfg)
            else:
                sb = AWAITING
            rows.append({
                "event": name, "day": day, "event_source": e["source"],
                "first_session": first, "trade_day": trade, "decided_at": decided,
                "available_at": max(avail), "stale": bool(stale),
                "surprise": s["value"] if s else None, "surprise_bucket": sb,
                "surprise_kind": sur_kind,
                "positioning_bucket": positioning_bucket(cot, decided, cfg),
                "dealer_bucket": dealer_bucket(words, decided, cfg),
                "first_session_drift_pct": px.oc(first),
                "next_session_drift_pct": px.oc(trade),
                "trade_open": px.open.latest(trade),
                "vix_change_pts": (vc - vp) if vc is not None and vp is not None else None})
        out[name] = rows
    return out


def _sessions_between(a: str, b: str) -> int:
    n, d = 0, a
    while d < b:
        d = pit.next_session(d)
        n += 1
    return n


def earnings_rows(store, cfg: dict, cutoff: str) -> list[dict]:
    ec = cfg.get("earnings") or {}
    uni = set(ec.get("universe") or [])
    hs = [int(h) for h in ec.get("drift_sessions") or [1, 20]]
    out = []
    for r in _events(store, "SELECT observed_at, available_at, payload FROM events "
                     "WHERE type='earnings' AND observed_at<=?", (pit.canon(cutoff),)):
        try:
            p = json.loads(r["payload"] or "{}") or {}
        except ValueError:
            continue
        sym, sp = p.get("symbol"), p.get("surprise_pct")
        if sym not in uni or sp is None:
            continue
        from . import rules                                     # noqa: PLC0415
        key = rules.price_symbols().get(sym.upper())
        if not key:
            continue
        closes = pit.Series(store, key)
        day = pit.et_date(r["observed_at"])
        # The first close by which a report before the open and one after the
        # close are both public: the session after the report day.
        e1 = (pit.next_session(day) if session.is_trading_session(_d(day))
              else pit.on_or_after_session(day))
        c0 = closes.latest(e1)
        before = closes.latest(pit.prev_session(day))
        row = {"symbol": sym, "day": day, "entry_day": e1, "surprise_pct": float(sp),
               "available_at": pit.canon(r["available_at"]),
               "reaction_pct": abs(c0 / before - 1) * 100 if c0 and before else None}
        for h in hs:
            d, ch = e1, None
            for _ in range(h):
                d = pit.next_session(d)
            ch = closes.latest(d)
            row[f"drift_{h}_pct"] = (ch / c0 - 1) * 100 if c0 and ch else None
        dday, decided = pit.nightly_after(max(row["available_at"],
                                              closes.avail(e1) or row["available_at"]))
        row.update(decided_at=decided, trade_day=pit.next_session(dday),
                   stale=_sessions_between(e1, dday) > STALE_SESSIONS, key=key)
        out.append(row)
    return sorted(out, key=lambda x: (x["day"], x["symbol"]))


# ---------------------------------------------------------------------------
# The base rates
# ---------------------------------------------------------------------------
MEASURES = {"first_session_drift_pct": ("pct", "up"), "next_session_drift_pct": ("pct", "up"),
            "vix_change_pts": ("vix_pts", "down")}


def _rate(event: str, kind: str, bucket: str, measure: str, rows: list[dict],
          note: str = "") -> dict:
    unit, way = MEASURES.get(measure, ("pct", "up"))
    xs = [(r["day"], r[measure]) for r in rows if r.get(measure) is not None]
    vals = [x for _, x in xs]
    hit = (sum(1 for v in vals if (v > 0 if way == "up" else v < 0)) / len(vals)
           if vals else None)
    return {"event": event, "bucket_kind": kind, "bucket": bucket, "measure": measure,
            "n": len(vals), "first_day": xs[0][0] if xs else None,
            "last_day": xs[-1][0] if xs else None,
            "mean": statistics.fmean(vals) if vals else None, "hit_rate": hit,
            "hit_means": "share above zero" if way == "up" else "share below zero (a crush)",
            "unit": unit, "note": note}


def base_rates(store, cfg: dict, cutoff: str) -> list[dict]:
    rows = macro_rows(store, cfg, cutoff)
    out = []
    for name, rs in rows.items():
        ev = cfg["events"][name]
        for m in MEASURES:
            out.append(_rate(name, "all", "all", m, rs))
            for kind in ("surprise", "positioning", "dealer"):
                col = f"{kind}_bucket"
                buckets = sorted({r[col] for r in rs})
                note = ((rs[0].get("surprise_kind") if rs else None)
                        or ev.get("surprise_kind", "")) if kind == "surprise" else ""
                if not rs or buckets == [AWAITING]:
                    why = {"surprise": ev.get("surprise_kind"),
                           "positioning": "no CFTC speculative net with two years of rows",
                           "dealer": "6b's stored regime word (exposure.regime_word) has no row "
                                     "knowable at the decision"}[kind]
                    out.append({**_rate(name, kind, AWAITING, m, []), "note": why})
                    continue
                for b in buckets:
                    out.append(_rate(name, kind, b, m, [r for r in rs if r[col] == b],
                                     note))
    er = earnings_rows(store, cfg, cutoff)
    hs = (cfg.get("earnings") or {}).get("drift_sessions") or [1, 20]
    for h in hs:
        m = f"drift_{h}_pct"
        out.append(_rate("earnings", "all", "all", m, er))
        for b, f in (("positive surprise", lambda r: r["surprise_pct"] > 0),
                     ("negative surprise", lambda r: r["surprise_pct"] < 0)):
            out.append(_rate("earnings", "surprise", b, m, [r for r in er if f(r)],
                             "real surprise: the analyst mean (yfinance)"))
    out.append({**_rate("earnings", "all", "realised reaction", "reaction_pct", er),
                "hit_rate": None, "hit_means": "",
                "note": "the absolute move from the close before the report to the "
                        "first close after it"})
    out.append({**_rate("earnings", "implied_vs_realised", AWAITING, "reaction_pct", []),
                "note": (cfg.get("earnings") or {}).get("implied_move") or AWAITING})
    return out


def write(ledger, rates: list[dict], as_of: str) -> int:
    day = session.session_date(as_of)
    for r in rates:
        ledger._upsert("event_base_rates", {
            "computed_on": day, "event": r["event"], "bucket_kind": r["bucket_kind"],
            "bucket": r["bucket"], "measure": r["measure"], "n": r["n"],
            "first_day": r["first_day"], "last_day": r["last_day"], "mean": r["mean"],
            "hit_rate": r["hit_rate"], "hit_means": r.get("hit_means") or "",
            "unit": r["unit"], "note": r.get("note") or "", "as_of": as_of})
    ledger.event("event_rates", "base_rates", as_of, None,
                 after={"rows": len(rates), "day": day})
    return len(rates)


def latest(ledger) -> list[dict]:
    r = ledger.one("SELECT MAX(computed_on) AS d FROM event_base_rates")
    if not r or not r["d"]:
        return []
    return ledger.q("SELECT * FROM event_base_rates WHERE computed_on=? ORDER BY event, "
                    "measure, bucket_kind, bucket", (r["d"],))


def fmt(x: Any, unit: str) -> str:
    if x is None:
        return "n/a"
    return f"{x:+.2f} pts" if unit == "vix_pts" else f"{x:+.2f}%"


def table(rows: list[dict]) -> list[str]:
    """The Lab report's rows: event, bucket, measure, n, window, mean, hit rate."""
    out = ["| Event | Bucket | Measure | n | Window | Mean | Hit rate |",
           "|---|---|---|---:|---|---:|---:|"]
    for r in rows:
        win = f"{r['first_day']} to {r['last_day']}" if r["n"] else (r["note"] or "")
        hit = "n/a" if r["hit_rate"] is None else f"{r['hit_rate'] * 100:.0f}%"
        b = r["bucket"] if r["bucket_kind"] == "all" else f"{r['bucket_kind']}: {r['bucket']}"
        out.append(f"| {r['event']} | {b} | {r['measure']} | {r['n']} | "
                   f"{win.replace('|', '/')} | {fmt(r['mean'], r['unit'])} | {hit} |")
    return out


def _main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="python -m alpha.event_rates")
    ap.add_argument("--store")
    ap.add_argument("--ledger")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compute", help="the base rates, into alpha.db (box write)")
    c.add_argument("--as-of")
    sub.add_parser("show", help="the latest base rates")
    a = ap.parse_args(argv)
    from .ledger import Ledger                                  # noqa: PLC0415
    if a.cmd == "show":
        with Ledger(a.ledger, read_only=True) as lg:
            print("\n".join(table(latest(lg))))
        return 0
    from .store import ReadOnlyStore                            # noqa: PLC0415
    as_of = a.as_of or session.utc_iso(timespec="microseconds")
    with Ledger(a.ledger) as lg:
        st = ReadOnlyStore(a.store)
        try:
            n = write(lg, base_rates(st, load_config(), as_of), as_of)
        finally:
            st.close()
        print("\n".join(table(latest(lg))))
    print(f"{n} rows written")
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
