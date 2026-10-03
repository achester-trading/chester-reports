"""
Prediction markets: Kalshi and Polymarket, read-only, public endpoints. (6d)

    python -m altdata.sources.prediction_markets pull [--dry-run]
    python -m altdata.sources.prediction_markets backfill --days 120 [--dry-run]

THE SPEC'S RULES, AS RECORDED 2 OCT 2026 (config/prediction_markets.yaml carries
them in full; docs/prediction-market-spec-v1.1.md is to be filed). Rights are
discovery, attention shock and disagreement only. Nothing here changes a scenario
weight, a narrative, a theme or a book, and nothing here is a trigger. One system
of record: the box's SQLite store, through ObservationStore. No key, no account.

WHAT IS STORED, per market, keyed by instrument `<venue>:<market id>`:
  pm.probability   the venue's implied probability (0..1)
  pm.volume        its cumulative traded volume
  pm.market        its description as JSON, written when it changes
with the three clocks: observed_at is the fetch instant, available_at the same
instant (ingest_instant), ingested_at the write.

THE PARSERS ARE SEPARATE FROM THE FETCH. `parse_kalshi_event()` and
`parse_polymarket_event()` take the venues' JSON and know nothing about the
network, so the gate feeds them fixtures. `pull()` takes an injectable `get`.

THE ONE-TIME BACKFILL is flagged on EVERY row: availability_kind
`reconstructed` and source `<venue>:backfill`, so no backfilled row can be read
as a live snapshot -- the calibration-archive gate counts live days only.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable, Optional

import yaml

from .. import observations, session

log = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = REPO / "config" / "prediction_markets.yaml"
KEYS = ("pm.probability", "pm.volume", "pm.market")
USER_AGENT = "chester-reports/1.0 (read-only research; no trading)"
PACING_SECONDS = 0.25


def load_config(path: Optional[Path] = None) -> dict:
    with open(path or CONFIG_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def http_get(url: str, timeout: float = 20.0) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                               "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:     # noqa: S310
        return json.load(r)


def _f(v: Any) -> Optional[float]:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if x == x else None


def price(bid: Optional[float], ask: Optional[float], last: Optional[float]
          ) -> tuple[Optional[float], str]:
    """THE VENUE'S PRICE (ruled 2 Oct 2026): the bid-ask mid where the venue
    quotes both sides of a live book, the last trade only as a fallback -- a last
    trade on a thin market can be hours old, the mid is the book now. Returns
    (probability, basis) and the basis is stored with the row."""
    if bid is not None and ask is not None and 0.0 <= bid <= ask <= 1.0 and ask > 0:
        return round((bid + ask) / 2.0, 4), "mid"
    return last, "last"


# ---------------------------------------------------------------------------
# Parsers -- venue JSON to market rows
# ---------------------------------------------------------------------------
def parse_kalshi_event(ev: dict, watch_id: str, match: str = "exact") -> list[dict]:
    """One Kalshi event (with nested markets) -> a row per market."""
    out = []
    e = ev.get("event") or ev
    for m in ev.get("markets") or e.get("markets") or []:
        last = _f(m.get("last_price_dollars"))
        if last is None:
            last = _f(m.get("last_price"))
            last = last / 100.0 if last is not None and last > 1 else last
        bid, ask = _f(m.get("yes_bid_dollars")), _f(m.get("yes_ask_dollars"))
        p, basis = price(bid, ask, last)
        out.append({
            "venue": "kalshi", "market_id": m.get("ticker"),
            "event_id": e.get("event_ticker") or m.get("event_ticker"),
            "watch_id": watch_id, "match": match,
            "question": m.get("title") or e.get("title"),
            "outcome": m.get("yes_sub_title") or m.get("subtitle") or "Yes",
            "event_title": e.get("title"),
            "probability": p, "price_basis": basis, "last": last,
            "bid": bid, "ask": ask,
            "volume": _f(m.get("volume_fp") or m.get("volume")),
            "open_interest": _f(m.get("open_interest_fp") or m.get("open_interest")),
            "close_at": m.get("close_time") or e.get("strike_date"),
            "decision_date": (e.get("strike_date") or "")[:10] or None,
            "criteria": m.get("rules_primary") or None,
        })
    return [r for r in out if r["market_id"] and r["probability"] is not None]


def parse_polymarket_event(ev: dict, watch_id: str, match: str = "exact"
                           ) -> list[dict]:
    """One Polymarket event -> a row per market (the YES side of each)."""
    out = []
    for m in ev.get("markets") or []:
        if m.get("closed"):
            continue
        try:
            prices = json.loads(m.get("outcomePrices") or "[]")
            outcomes = json.loads(m.get("outcomes") or "[]")
        except ValueError:
            continue
        if not prices:
            continue
        i = outcomes.index("Yes") if "Yes" in outcomes else 0
        # bestBid / bestAsk quote the market's FIRST outcome's token; the mid is
        # used only when that is the side stored.
        bid, ask = (_f(m.get("bestBid")), _f(m.get("bestAsk"))) if i == 0 \
            else (None, None)
        p, basis = price(bid, ask, _f(prices[i]))
        out.append({
            "venue": "polymarket", "market_id": m.get("conditionId") or m.get("id"),
            "event_id": ev.get("slug"), "watch_id": watch_id, "match": match,
            "question": m.get("question"),
            "outcome": m.get("groupItemTitle") or (outcomes[i] if outcomes else "Yes"),
            "event_title": ev.get("title"),
            "probability": p, "price_basis": basis, "last": _f(prices[i]),
            "bid": bid, "ask": ask,
            "volume": _f(m.get("volume")),
            "open_interest": _f(m.get("liquidity")),
            "close_at": m.get("endDate") or ev.get("endDate"),
            "decision_date": (m.get("endDate") or ev.get("endDate") or "")[:10] or None,
            "criteria": m.get("description") or ev.get("description") or None,
            "clob_token": (json.loads(m.get("clobTokenIds") or "[]") or [None])[i]
            if m.get("clobTokenIds") else None,
        })
    return [r for r in out if r["market_id"] and r["probability"] is not None]


# ---------------------------------------------------------------------------
# Resolving the watch list
# ---------------------------------------------------------------------------
def _kalshi_events(item: dict, base: str, get: Callable) -> list[dict]:
    k = item.get("kalshi") or {}
    if k.get("event"):
        return [get(f"{base}/events/{k['event']}?with_nested_markets=true")]
    if k.get("series"):
        d = get(f"{base}/events?" + urllib.parse.urlencode(
            {"series_ticker": k["series"], "status": "open",
             "with_nested_markets": "true", "limit": 50}))
        evs = sorted(d.get("events") or [],
                     key=lambda e: e.get("strike_date") or e.get("event_ticker") or "")
        return evs[:item["next_n"]] if item.get("next_n") else evs
    return []


def _poly_events(item: dict, base: str, get: Callable) -> list[dict]:
    p = item.get("polymarket") or {}
    if not p.get("query"):
        return []
    d = get(f"{base}/public-search?" + urllib.parse.urlencode(
        {"q": p["query"], "limit_per_type": 20, "events_status": "active"}))
    rx = re.compile(p.get("slug_pattern") or ".")
    evs = [e for e in d.get("events") or [] if rx.search(e.get("slug") or "")
           and not e.get("closed")]
    evs.sort(key=lambda e: e.get("endDate") or "")
    if item.get("next_n"):
        evs = evs[:item["next_n"]]
    full = []
    for e in evs:
        got = get(f"{base}/events?" + urllib.parse.urlencode({"slug": e["slug"]}))
        full.append((got or [e])[0] if isinstance(got, list) else e)
        time.sleep(PACING_SECONDS)
    return full


def discovery(cfg: dict, get: Callable, story_keywords: Optional[dict] = None
              ) -> list[dict]:
    """The highest-volume open markets whose titles match a story's keywords."""
    base = cfg["venues"]["polymarket"]["base"]
    kws = story_keywords or (cfg.get("discovery") or {}).get("keywords") or {}
    top = int((cfg.get("discovery") or {}).get("top_n") or 20)
    evs = get(f"{base}/events?" + urllib.parse.urlencode(
        {"closed": "false", "order": "volume", "ascending": "false", "limit": 200}))
    rows = []
    for e in evs or []:
        title = e.get("title") or ""
        story = next((sid for sid, words in kws.items()
                      if any(re.search(rf"\b{re.escape(w)}\b", title, re.I)
                             for w in words)), None)
        if story:
            for r in parse_polymarket_event(e, f"discovery:{story}", "loose"):
                rows.append(r)
    rows.sort(key=lambda r: -(r.get("volume") or 0))
    return rows[:top]


def collect(cfg: Optional[dict] = None, get: Optional[Callable] = None) -> dict:
    """Every watched and discovered market, parsed. Fetches; writes nothing.

    Never raises: a venue that fails is reported per watch item and the rest are
    collected -- an outage is a stated absence, not a dead pull.
    """
    cfg = cfg or load_config()
    get = get or http_get
    kb, pb = cfg["venues"]["kalshi"]["base"], cfg["venues"]["polymarket"]["base"]
    rows: list[dict] = []
    report: dict[str, Any] = {"items": {}, "errors": {}}
    for item in cfg.get("watch_list") or []:
        got = {"kalshi": 0, "polymarket": 0}
        match = item.get("match") or "exact"
        for venue, fetch, parse, base in (
                ("kalshi", _kalshi_events, parse_kalshi_event, kb),
                ("polymarket", _poly_events, parse_polymarket_event, pb)):
            try:
                for ev in fetch(item, base, get):
                    new = parse(ev, item["id"], match)
                    rows += new
                    got[venue] += len(new)
            except Exception as exc:                            # noqa: BLE001
                report["errors"][f"{item['id']}:{venue}"] = \
                    f"{type(exc).__name__}: {exc}"[:200]
            time.sleep(PACING_SECONDS)
        report["items"][item["id"]] = got
    try:
        disc = discovery(cfg, get)
        rows += disc
        report["discovery"] = len(disc)
    except Exception as exc:                                    # noqa: BLE001
        report["errors"]["discovery"] = f"{type(exc).__name__}: {exc}"[:200]
    seen, uniq = set(), []
    for r in rows:
        k = (r["venue"], r["market_id"])
        if k not in seen:
            seen.add(k)
            uniq.append(r)
    return {"rows": uniq, "report": report}


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------
META_FIELDS = ("watch_id", "venue", "event_id", "event_title", "question",
               "outcome", "close_at", "decision_date", "criteria", "match",
               "clob_token")
# pm.probability's value_text names the basis of its value_num ("mid"/"last");
# a JSON string because a row holds one number.


def to_observations(rows: list[dict], fetched_at: str, run_id: Optional[str] = None,
                    backfill: bool = False) -> list[dict]:
    out = []
    for r in rows:
        inst = f"{r['venue']}:{r['market_id']}"
        src = f"{r['venue']}:backfill" if backfill else r["venue"]
        kind = "reconstructed" if backfill else "ingest_instant"
        base = {"instrument": inst, "observed_at": r.get("observed_at") or fetched_at,
                "available_at": r.get("available_at") or fetched_at, "source": src,
                "run_id": run_id, "availability_kind": kind}
        out.append({**base, "registry_key": "pm.probability",
                    "value": r["probability"]})
        if not backfill:
            out.append({**base, "registry_key": "pm.price_basis",
                        "value": r.get("price_basis") or "last"})
        if r.get("volume") is not None:
            out.append({**base, "registry_key": "pm.volume", "value": r["volume"]})
        if not backfill:
            meta = {k: r.get(k) for k in META_FIELDS if r.get(k) is not None}
            out.append({**base, "registry_key": "pm.market",
                        "value": json.dumps(meta, sort_keys=True)})
    return out


def pull(store: Optional[observations.ObservationStore] = None,
         get: Optional[Callable] = None, dry_run: bool = False,
         run_id: Optional[str] = None, now: Optional[str] = None) -> dict:
    got = collect(get=get)
    fetched = now or session.utc_iso()
    obs = to_observations(got["rows"], fetched, run_id)
    out = {"markets": len(got["rows"]), "observations": len(obs),
           **got["report"], "dry_run": dry_run}
    if dry_run:
        return out
    own = store is None
    st = store or observations.ObservationStore()
    try:
        # pm.market only when it changed: one description per market, not one a
        # pull, so its history is a list of real revisions.
        keep = []
        for o in obs:
            if o["registry_key"] == "pm.market":
                prev = st.latest_as_of("pm.market", instrument=o["instrument"])
                if prev and prev.get("value_text") == o["value"]:
                    continue
            keep.append(o)
        out["written"] = st.write_many(keep)
    finally:
        if own:
            st.close()
    return out


# ---------------------------------------------------------------------------
# The one-time backfill
# ---------------------------------------------------------------------------
def backfill_rows(meta: dict, get: Callable, days: int, end: dt.date) -> list[dict]:
    """Daily history for one stored market, from the venue. Flag set by caller."""
    start = end - dt.timedelta(days=days)
    rows = []
    if meta.get("venue") == "kalshi":
        series = str(meta.get("event_id") or "").split("-")[0]
        tick = meta["market_id"]
        d = get("https://api.elections.kalshi.com/trade-api/v2/series/"
                f"{series}/markets/{tick}/candlesticks?" + urllib.parse.urlencode(
                    {"start_ts": int(dt.datetime.combine(start, dt.time()).timestamp()),
                     "end_ts": int(dt.datetime.combine(end, dt.time()).timestamp()),
                     "period_interval": 1440}))
        for c in d.get("candlesticks") or []:
            px = _f(((c.get("price") or {}).get("close_dollars"))
                    or (c.get("price") or {}).get("close"))
            if px is not None and px > 1:
                px /= 100.0
            if px is None:
                continue
            day = dt.datetime.fromtimestamp(int(c["end_period_ts"]),
                                            dt.timezone.utc).date()
            rows.append({"day": day, "probability": px})
    elif meta.get("venue") == "polymarket" and meta.get("clob_token"):
        d = get("https://clob.polymarket.com/prices-history?" + urllib.parse.urlencode(
            {"market": meta["clob_token"], "interval": "max", "fidelity": 1440}))
        for h in d.get("history") or []:
            day = dt.datetime.fromtimestamp(int(h["t"]), dt.timezone.utc).date()
            if start <= day <= end:
                rows.append({"day": day, "probability": _f(h.get("p"))})
    return [r for r in rows if r["probability"] is not None]


def backfill(days: int = 120, store: Optional[observations.ObservationStore] = None,
             get: Optional[Callable] = None, dry_run: bool = False) -> dict:
    """Daily history for every market already stored, flagged as backfill."""
    get = get or http_get
    own = store is None
    st = store or observations.ObservationStore()
    out: dict[str, Any] = {"markets": 0, "rows": 0, "errors": {}, "dry_run": dry_run}
    try:
        end = session.session_date_obj()
        obs = []
        for inst in st.instruments("pm.market"):
            r = st.latest_as_of("pm.market", instrument=inst)
            try:
                meta = {**json.loads(r["value_text"]),
                        "market_id": inst.split(":", 1)[1]}
                hist = backfill_rows(meta, get, days, end)
            except Exception as exc:                            # noqa: BLE001
                out["errors"][inst] = f"{type(exc).__name__}: {exc}"[:160]
                continue
            out["markets"] += 1
            for h in hist:
                when = f"{h['day'].isoformat()}T21:00:00+00:00"
                obs += to_observations([{"venue": meta["venue"],
                                         "market_id": meta["market_id"],
                                         "probability": h["probability"],
                                         "observed_at": when, "available_at": when}],
                                       when, backfill=True)
            time.sleep(PACING_SECONDS)
        out["rows"] = len(obs)
        if not dry_run:
            out["written"] = st.write_many(obs)
    finally:
        if own:
            st.close()
    return out


def _main(argv: list[str]) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Prediction markets (6d), read-only.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pull")
    p.add_argument("--dry-run", action="store_true")
    b = sub.add_parser("backfill")
    b.add_argument("--days", type=int, default=120)
    b.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO)
    res = pull(dry_run=a.dry_run) if a.cmd == "pull" else \
        backfill(a.days, dry_run=a.dry_run)
    print(json.dumps(res, indent=2, default=str))
    return 0


if __name__ == "__main__":                                      # pragma: no cover
    import sys
    raise SystemExit(_main(sys.argv[1:]))
