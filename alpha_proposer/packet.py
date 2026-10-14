"""
The observation packet -- built by CODE from the store and alpha.db, both read
only, before the model sees anything (X-2.10b).

    build(store, ledger, as_of) -> dict

Fields, in the order the prompt presents them:

  session        the ET session date and the as-of instant
  moves          the price basket's one-day moves with a z-score against each
                 symbol's own trailing one-day moves (up to five years)
  screen         the |z| >= 2.5 prints among them. altdata.move_screen (the
                 store-wide screen, audit #4 item 1) is not built yet; until it
                 is, this is the packet's own screen over the price basket
  dealer         SPY's stored dealer series (net GEX, the gamma flip, the call
                 and put walls): the latest value and its change
  state          the stored market-state object: the dials, the open
                 contradictions, the exceptions -- read, never recomputed
  prediction     prediction-market probabilities that moved past the attention
                 shock threshold (config/prediction_markets.yaml, 10 points)
  calendar       scheduled releases in the next five sessions, as known now
  agenda         the lab's agenda of misses (agenda.json, X-2.4), when written
  register       every registered hypothesis's id, title, family, status and
                 rule hash -- failures included, results NOT included: the
                 proposer never sees a test result
  budgets        the daily proposer's family budget used this week, and today's
  dictionary     the stored series: key, first and last observed day, rows

Every figure in it is a stored value or arithmetic on stored values.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import statistics
from typing import Any, Optional

import yaml

from altdata import observations, session
from alpha import files, rules
from alpha import hypotheses as hyp

SIGMA = 2.5
Z_WINDOW = 1260
DEALER_KEYS = ("exposure.net_gex", "exposure.gamma_flip", "exposure.call_wall",
               "exposure.put_wall")


def _shock_points() -> float:
    try:
        cfg = yaml.safe_load((rules.REPO / "config" / "prediction_markets.yaml")
                             .read_text(encoding="utf-8")) or {}
    except OSError:
        return 10.0
    def find(d: Any) -> Optional[float]:
        if isinstance(d, dict):
            for k, v in d.items():
                if k == "attention_shock_points":
                    return float(v)
                f = find(v)
                if f is not None:
                    return f
        return None
    return find(cfg) or 10.0


def moves(store, as_of: str) -> list[dict]:
    t = observations.canonical_instant(as_of)
    day = session.session_date(as_of)
    data = rules.Data(store)
    out = []
    for sym, key in sorted(rules.price_symbols().items()):
        if not store.all_vintages(key):
            continue
        xs = data.series(key).known(day, t, Z_WINDOW + 1)
        if len(xs) < 61 or xs[-1][0] != day:
            continue
        r = [xs[i][1] / xs[i - 1][1] - 1 for i in range(1, len(xs)) if xs[i - 1][1]]
        hist, last = r[:-1], r[-1]
        sd = statistics.stdev(hist) if len(hist) > 2 else 0.0
        out.append({"symbol": sym, "close": round(xs[-1][1], 4),
                    "change_pct": round(last * 100, 3),
                    "z": round((last - statistics.fmean(hist)) / sd, 2) if sd else None,
                    "history_days": len(hist)})
    return out


def dealer(store, as_of: str) -> dict:
    out = {}
    for k in DEALER_KEYS:
        rows = store.as_of(k, as_of, "SPY") or store.as_of(k, as_of)
        vals = [r for r in rows if r.get("value_num") is not None]
        if not vals:
            continue
        last = vals[-1]
        prev = vals[-2] if len(vals) > 1 else None
        out[k] = {"day": str(last["observed_at"])[:10], "value": last["value_num"],
                  "change": (last["value_num"] - prev["value_num"]) if prev else None}
    return out


def state(store, as_of: str) -> dict:
    obj = store.market_state(as_of) or {}
    dials = {k: (v or {}).get("state") for k, v in (obj.get("dials") or {}).items()}
    return {"session": obj.get("session"), "dials": dials,
            "open_contradictions": obj.get("open_contradictions") or [
                c.get("id") for c in obj.get("contradictions") or [] if c.get("open")],
            "exceptions": [{k: e.get(k) for k in ("what", "threshold", "value", "since")}
                           for e in obj.get("exceptions") or []]}


def prediction(store, as_of: str) -> list[dict]:
    pts = _shock_points()
    out = []
    try:
        insts = store.instruments("pm.probability")
    except Exception:                                         # noqa: BLE001
        return out
    for inst in insts:
        rows = [r for r in store.as_of("pm.probability", as_of, inst)
                if r.get("value_num") is not None]
        if len(rows) < 2:
            continue
        a, b = float(rows[-2]["value_num"]), float(rows[-1]["value_num"])
        scale = 100.0 if max(abs(a), abs(b)) <= 1.0 else 1.0
        move = (b - a) * scale
        if abs(move) >= pts:
            out.append({"market": inst, "from": a, "to": b, "points": round(move, 1)})
    return out


def calendar(store, as_of: str) -> list[dict]:
    have = store.conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND "
                              "name='events'").fetchone()
    if not have:
        return []
    day = dt.date.fromisoformat(session.session_date(as_of))
    ahead, d = [], day
    while len(ahead) < 5:
        d += dt.timedelta(days=1)
        if session.is_trading_session(d):
            ahead.append(d.isoformat())
    rows = store.conn.execute(
        "SELECT observed_at, title FROM events WHERE type IN ('release','scheduled') "
        "AND substr(observed_at,1,10) BETWEEN ? AND ? AND available_at <= ? "
        "ORDER BY observed_at", (ahead[0], ahead[-1],
                                 observations.canonical_instant(as_of))).fetchall()
    return [{"day": str(r["observed_at"])[:10], "title": r["title"]} for r in rows]


def agenda() -> Optional[dict]:
    try:
        p = files.root("research_dir") / "agenda.json"
    except KeyError:
        return None
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except ValueError:
        return None


def register(ledger) -> list[dict]:
    if ledger is None:
        return []
    return [{"id": h["id"], "title": h["title"], "family": h["family"],
             "status": h["status"], "rule_hash": h["rule_hash"][:16]}
            for h in hyp.Register(ledger).all()]


def budgets(ledger, day: str) -> dict:
    if ledger is None:
        return {"families_this_week": {}}
    reg = hyp.Register(ledger)
    fams = sorted({h["family"] for h in reg.all()})
    used = {f: reg.family_week_count(f, day, channel="daily-proposer") for f in fams}
    return {"per_session_day": hyp.BUDGETS["daily-proposer"]["per_batch"],
            "per_family_per_week": hyp.BUDGETS["daily-proposer"]["per_family_per_week"],
            "families_this_week": {f: n for f, n in used.items() if n}}


def dictionary(store) -> list[dict]:
    rows = store.conn.execute(
        "SELECT registry_key, MIN(observed_at) AS first, MAX(observed_at) AS last, "
        "COUNT(*) AS n FROM observations WHERE value_num IS NOT NULL "
        "GROUP BY registry_key ORDER BY registry_key").fetchall()
    sym_by_key = {v: k for k, v in rules.price_symbols().items()}
    out = []
    for r in rows:
        k = r["registry_key"]
        out.append({"key": k, "symbol": sym_by_key.get(k), "first": str(r["first"])[:10],
                    "last": str(r["last"])[:10], "rows": r["n"]})
    return out


def build(store, ledger, as_of: str) -> dict:
    day = session.session_date(as_of)
    mv = moves(store, as_of)
    pkt = {
        "session": day, "as_of": as_of,
        "moves": mv,
        "screen": {"sigma": SIGMA, "source": "the packet's own screen over the price "
                   "basket (altdata.move_screen is not built yet)",
                   "prints": [m for m in mv if m["z"] is not None and abs(m["z"]) >= SIGMA]},
        "dealer": dealer(store, as_of),
        "state": state(store, as_of),
        "prediction": prediction(store, as_of),
        "calendar": calendar(store, as_of),
        "agenda": agenda(),
        "register": register(ledger),
        "budgets": budgets(ledger, day),
        "dictionary": dictionary(store),
    }
    return pkt


def sha256(pkt: dict) -> str:
    return hashlib.sha256(json.dumps(pkt, sort_keys=True, default=str)
                          .encode("utf-8")).hexdigest()
