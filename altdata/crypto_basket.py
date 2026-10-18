"""
The crypto long-shot basket -- measured, not narrated.
(docs/briefs/crypto-basket-brief-2026-10-12.md, ruled 12 Oct 2026.)

    python -m altdata.crypto_basket derive           # dilution and S-1, from the store
    python -m altdata.crypto_basket grade            # the falsifier states, printed
    python -m altdata.crypto_basket scan-items FILE  # ingest the Saturday scan's items

Twelve names in config/crypto_basket.yaml, each with what pays the token, a
falsifier and the operator's odds of 10x and 100x. This module reads the store
and the config and computes nothing a model decides:

  grade()             holds / strained / failed / not measured, with the rule
  dilution()          annual issuance over the value returned to holders
  weekly_block()      the reference table and the events-only read-path line
  monthly_block()     the Themes: digital basket block and its status lines
  quarterly_pages()   the half-page per name for the Quarterly's crypto chapter
  restate()           decision 3: the model's quarterly restatement, under rules

THE ODDS ARE THE OPERATOR'S. The reference column is the config's text, printed
byte-for-byte every quarter; a restatement prints beside it and is written to the
thesis register as an `alt_asset` entry labelled "model estimate", never to the
config. restate() runs inside the Quarterly only.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import math
import os
import re
import statistics
from pathlib import Path
from typing import Any, Callable, Optional

log = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "config" / "crypto_basket.yaml"
STATUSES = ("holds", "strained", "failed", "not measured")
EVENT_KINDS = ("move", "threshold", "dated_event", "scan_item")
SCAN_KINDS = ("exploit", "listing", "delisting", "fee_switch_vote", "unlock",
              "governance", "other")
SCAN_KEY = "scan.crypto_basket_item"
DILUTION_PREFIX = "calc.crypto_dilution_"
MODEL_LABEL = "model estimate"
REGISTER_SOURCE = "alt_asset"
# The move screen's rule, by name (c1-move-screen, altdata/move_screen.py,
# config/move_screen.yaml): log change over 1 and 5 observations, z against every
# such change in the last five years excluding today, population sd, flagged at
# |z| >= 2.5 with at least 500 observations. Computed here until that branch merges.
MOVE_SCREEN = {"sigma": 2.5, "history_days": 1826, "min_observations": 500,
               "horizons": (1, 5)}
# A measurable "moved" on the quarter for the restatement rule at this share.
MEASURABLE_MOVE = 0.25
# Dilution needs this much stored supply history to annualise.
DILUTION_MIN_DAYS = 30


# ---------------------------------------------------------------------------
# Config and the store
# ---------------------------------------------------------------------------
def config(path: Optional[Path] = None) -> dict:
    import yaml  # noqa: PLC0415
    return yaml.safe_load((path or CONFIG_PATH).read_text(encoding="utf-8")) or {}


def names(cfg: Optional[dict] = None) -> dict:
    return (cfg or config()).get("names") or {}


DILUTION_KEYS = [f"crypto_dilution_{s.lower()}" for s in names()]


def price_key(sym: str) -> str:
    return f"yfinance.crypto_{sym.lower()}"


def _pts(st: Any, key: str, as_of: Optional[str] = None,
         instrument: Optional[str] = None) -> list[tuple[str, float]]:
    out = []
    for r in st.as_of(key, as_of=as_of, instrument=instrument):
        v = r.get("value_num")
        if v is not None:
            out.append((str(r["observed_at"])[:10], float(v)))
    return sorted(out)


def _on_or_before(pts: list, day: str) -> Optional[tuple[str, float]]:
    best = None
    for d, v in pts:
        if d <= day:
            best = (d, v)
        else:
            break
    return best


def _minus(day: str, n: int) -> str:
    return (dt.date.fromisoformat(day) - dt.timedelta(days=n)).isoformat()


def _pct(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b in (None, 0):
        return None
    return 100.0 * (a / b - 1.0)


def _sum_window(pts: list, end: str, days: int) -> Optional[float]:
    lo = _minus(end, days)
    xs = [v for d, v in pts if lo < d <= end]
    return sum(xs) if xs else None


def _cutoff(as_of: Optional[str]) -> str:
    from . import session  # noqa: PLC0415
    return as_of or session.utc_iso(timespec="microseconds")


# ---------------------------------------------------------------------------
# Formats (one place, so the tables and the audit agree)
# ---------------------------------------------------------------------------
def fmt_usd(v: Optional[float]) -> str:
    if v is None:
        return "—"
    a = abs(v)
    for div, suf in ((1e12, "tn"), (1e9, "bn"), (1e6, "m"), (1e3, "k")):
        if a >= div:
            return f"${v / div:,.2f}{suf}"
    return f"${v:,.2f}" if a >= 1 else f"${v:.4g}"


def fmt_price(v: Optional[float]) -> str:
    if v is None:
        return "—"
    return f"${v:,.2f}" if v >= 1 else f"${v:.4g}"


def fmt_pct(v: Optional[float]) -> str:
    return "—" if v is None else f"{v:+.1f}%"


# ---------------------------------------------------------------------------
# What pays the token: the measurable's latest and its change
# ---------------------------------------------------------------------------
def _flow(key: str) -> bool:
    """Fees, revenue and holders revenue are daily FLOWS (summed over a window);
    TVL, caps and supply are LEVELS."""
    k = key.split(".", 1)[-1]
    return k.startswith(("fees_", "revenue_", "holders_revenue_"))


def measurable(sym: str, n: dict, st: Any, as_of: Optional[str], end: str,
               days: int = 7) -> dict:
    """{key, latest, change_pct, as_of, form, reason}: a flow as its sum over
    `days` against the `days` before; a level against `days` ago."""
    key = (n.get("measurable") or {}).get("key")
    if not key:
        return {"key": None, "reason": (n.get("measurable") or {}).get("note")
                or "no measurable series"}
    pts = _pts(st, key, as_of)
    pts = [p for p in pts if p[0] <= end]
    if not pts:
        return {"key": key, "reason": f"{key}: nothing stored at this cutoff"}
    last = pts[-1][0]
    if _flow(key):
        now = _sum_window(pts, last, days)
        then = _sum_window(pts, _minus(last, days), days)
        return {"key": key, "latest": now, "change_pct": _pct(now, then),
                "as_of": last, "form": f"{days}-day sum"}
    prev = _on_or_before(pts, _minus(last, days))
    return {"key": key, "latest": pts[-1][1],
            "change_pct": _pct(pts[-1][1], prev[1] if prev else None),
            "as_of": last, "form": "level"}


# ---------------------------------------------------------------------------
# Price, drawdown, the move screen
# ---------------------------------------------------------------------------
def price_row(sym: str, st: Any, as_of: Optional[str], end: str) -> dict:
    pts = [p for p in _pts(st, price_key(sym), as_of) if p[0] <= end]
    if not pts:
        return {"price": None, "reason": f"{price_key(sym)}: nothing stored"}
    d, v = pts[-1]
    w = _on_or_before(pts, _minus(d, 7))
    m = _on_or_before(pts, _minus(d, 30))
    q = _on_or_before(pts, _minus(d, 91))
    hi_d, hi = max(pts, key=lambda p: p[1])
    return {"price": v, "as_of": d,
            "week_pct": _pct(v, w[1] if w else None),
            "d30_pct": _pct(v, m[1] if m else None),
            "q_pct": _pct(v, q[1] if q else None),
            "high": hi, "high_on": hi_d, "history_from": pts[0][0],
            "drawdown_pct": _pct(v, hi)}


def move_z(pts: list[tuple[str, float]], cfg: Optional[dict] = None) -> dict:
    """The move screen's z on the last observation (see MOVE_SCREEN)."""
    c = {**MOVE_SCREEN, **(cfg or {})}
    out: dict = {"flagged": False, "z": {}, "n": len(pts)}
    if len(pts) < int(c["min_observations"]):
        out["reason"] = f"{len(pts)} observations, {c['min_observations']} needed"
        return out
    vals = [v for _, v in pts]
    days = [d for d, _ in pts]
    lo = _minus(days[-1], int(c["history_days"]))
    for h in c["horizons"]:
        hist = [math.log(vals[i] / vals[i - h])
                for i in range(h, len(vals) - 1)
                if days[i - h] >= lo and vals[i - h] > 0 and vals[i] > 0]
        if len(hist) < 2 or vals[-1 - h] <= 0:
            continue
        sd = statistics.pstdev(hist)
        if sd == 0:
            continue
        now = math.log(vals[-1] / vals[-1 - h])
        out["z"][h] = (now - statistics.fmean(hist)) / sd
    if out["z"]:
        h, z = max(out["z"].items(), key=lambda kv: abs(kv[1]))
        out.update({"max_abs_z": abs(z), "horizon": h, "sign": 1 if z > 0 else -1,
                    "flagged": abs(z) >= float(c["sigma"])})
    return out


# ---------------------------------------------------------------------------
# Item 3: the falsifier grader
# ---------------------------------------------------------------------------
def grade(sym: str, n: dict, st: Any, as_of: Optional[str] = None,
          on: Optional[str] = None, params: Optional[dict] = None) -> dict:
    """{status, rule, detail}: the falsifier's state on day `on` (default: the
    cutoff's day). FAILED when the threshold is crossed (or the date passes
    without the condition); STRAINED within the band of it, or past half the time
    to its date with no progress toward it; NOT MEASURED, with the reason, where
    the falsifier has no series or no threshold."""
    p = {"strained_band": 0.10, **(params or {})}
    f = n.get("falsifier") or {}
    on = on or _cutoff(as_of)[:10]
    if not f.get("measured"):
        return {"status": "not measured", "rule": None,
                "detail": f"not measured — {f.get('reason') or 'no series'}"}
    pts = [x for x in _pts(st, f["series"], as_of) if x[0] <= on]
    kind = f.get("kind")
    if not pts:
        return {"status": "not measured", "rule": None,
                "detail": f"not measured — {f['series']}: nothing stored at this "
                          f"cutoff"}
    if kind == "level_by_date":
        base_d, base = pts[0]
        last_d, last = pts[-1]
        thr = float(f["threshold"])
        ratio = last / base if base else None
        rule = (f"failed at {thr:g}x the {base_d} level by {f['date']}; strained "
                f"within {p['strained_band']:.0%} of it")
        if ratio is None:
            return {"status": "not measured", "rule": rule,
                    "detail": "not measured — the baseline is zero"}
        detail = f"{ratio:.2f}x the {base_d} level on {last_d}"
        if on > f["date"]:
            st_ = "failed" if ratio >= thr else "holds"
            return {"status": st_, "rule": rule, "detail": detail + " (date passed)"}
        if ratio >= thr:
            return {"status": "failed", "rule": rule, "detail": detail}
        if ratio >= thr * (1 - p["strained_band"]):
            return {"status": "strained", "rule": rule, "detail": detail}
        return {"status": "holds", "rule": rule, "detail": detail}
    if kind == "event_then_level":
        ev = f["event_date"]
        w = int(f.get("window_days") or 30)
        pre = _sum_window(pts, _minus(ev, 1), w)
        last_d = pts[-1][0]
        now = _sum_window(pts, last_d, w)
        rule = (f"failed if the {w}-day fee sum on {f['date']} is below the {w} "
                f"days to {_minus(ev, 1)}; strained within "
                f"{p['strained_band']:.0%} above it, or past half the time to "
                f"{f['date']} with no rise")
        if pre is None or now is None:
            return {"status": "not measured", "rule": rule,
                    "detail": "not measured — no fee history before the event"}
        if on < ev:
            return {"status": "holds", "rule": rule,
                    "detail": f"before the {ev} event; {w}-day fees "
                              f"{fmt_usd(now)}"}
        detail = (f"{w}-day fees {fmt_usd(now)} against {fmt_usd(pre)} before "
                  f"{ev} ({fmt_pct(_pct(now, pre))})")
        if on >= f["date"]:
            return {"status": "failed" if now < pre else "holds", "rule": rule,
                    "detail": detail + " (date reached)"}
        half = (dt.date.fromisoformat(ev)
                + (dt.date.fromisoformat(f["date"]) - dt.date.fromisoformat(ev)) / 2)
        if now < pre * (1 + p["strained_band"]):
            return {"status": "strained", "rule": rule, "detail": detail}
        if on >= half.isoformat() and now <= pre:
            return {"status": "strained", "rule": rule, "detail": detail}
        return {"status": "holds", "rule": rule, "detail": detail}
    if kind == "switch":
        w = int(f.get("window_days") or 30)
        last_d = pts[-1][0]
        now = _sum_window(pts, last_d, w) or 0.0
        on_ = now > 0
        rule = (f"the switch is on when the {w}-day sum is above zero"
                + ("" if f.get("date") else "; undated, so it cannot fail until "
                   "a date is set"))
        detail = (f"switch {'ON' if on_ else 'off'}: {w}-day value to holders "
                  f"{fmt_usd(now)} to {last_d}")
        if on_:
            return {"status": "holds", "rule": rule, "detail": detail}
        if f.get("date") and on > f["date"]:
            return {"status": "failed", "rule": rule, "detail": detail}
        return {"status": "holds", "rule": rule, "detail": detail}
    return {"status": "not measured", "rule": None,
            "detail": f"not measured — falsifier kind {kind!r} has no rule"}


# ---------------------------------------------------------------------------
# Dilution: annual issuance over the value returned to holders
# ---------------------------------------------------------------------------
def dilution(sym: str, st: Any, as_of: Optional[str] = None) -> dict:
    """{ratio, issuance_usd, returned_usd, reason}. Issuance is the annualised
    change in stored circulating supply valued at the latest price; the value
    returned is DefiLlama's holders revenue (buybacks, burns AND distributions --
    DefiLlama does not split them) over the last 365 days, annualised when the
    store holds less. Not measured, with the reason, when a leg is absent."""
    s = sym.lower()
    sup = _pts(st, f"llama.supply_{s}", as_of)
    hr = _pts(st, f"llama.holders_revenue_{s}", as_of)
    px = _pts(st, price_key(sym), as_of)
    why = []
    if len(sup) < 2:
        why.append(f"circulating supply: {len(sup)} stored day(s)")
    else:
        span = (dt.date.fromisoformat(sup[-1][0])
                - dt.date.fromisoformat(sup[0][0])).days
        if span < DILUTION_MIN_DAYS:
            why.append(f"circulating supply: {span} day(s) of history, "
                       f"{DILUTION_MIN_DAYS} needed")
    if not hr:
        why.append("buybacks and burns: DefiLlama serves no holders revenue "
                   "for it" if not names().get(sym, {}).get("llama_slug")
                   else "buybacks and burns: no holders revenue stored")
    if not px:
        why.append("price: nothing stored")
    if why:
        return {"ratio": None, "reason": "not measured — " + "; ".join(why)}
    span = (dt.date.fromisoformat(sup[-1][0]) - dt.date.fromisoformat(sup[0][0])).days
    issued = (sup[-1][1] - sup[0][1]) * 365.0 / span * px[-1][1]
    last = hr[-1][0]
    window = [v for d, v in hr if d > _minus(last, 365)]
    hspan = min(365, (dt.date.fromisoformat(last)
                      - dt.date.fromisoformat(hr[0][0])).days + 1)
    returned = sum(window) * 365.0 / max(hspan, 1)
    if returned <= 0:
        return {"ratio": None, "issuance_usd": issued, "returned_usd": returned,
                "reason": "not measured — nothing returned to holders (the ratio "
                          "has no denominator)"}
    return {"ratio": issued / returned, "issuance_usd": issued,
            "returned_usd": returned, "as_of": max(sup[-1][0], last),
            "reason": None}


def write_dilution(store: Any = None, as_of: Optional[str] = None) -> dict:
    """calc.crypto_dilution_<sym> for every measurable name, at the latest day."""
    from . import observations as obs, session  # noqa: PLC0415
    own = store is None
    db = store or obs.ObservationStore()
    rows, out = [], {}
    try:
        now = session.utc_iso(timespec="microseconds")
        for sym in names():
            d = dilution(sym, db, as_of)
            out[sym] = d.get("ratio") if d.get("ratio") is not None else d["reason"]
            if d.get("ratio") is not None:
                rows.append({"registry_key": f"{DILUTION_PREFIX}{sym.lower()}",
                             "instrument": None, "observed_at": d["as_of"],
                             "available_at": now, "value": d["ratio"],
                             "source": "derived_state", "availability_kind": "ingest_instant"})
        n = db.write_many(obs.drop_unchanged(db, rows))
    finally:
        if own:
            db.close()
    return {"written": n, "names": out}


def write_stable_impulse(store: Any = None) -> dict:
    """S-1: calc.stable_impulse_30d / _90d, the percent change of
    llama.stable_total over 30 and 90 days, every stored day, stamped with the
    input's own available_at."""
    from . import observations as obs  # noqa: PLC0415
    own = store is None
    db = store or obs.ObservationStore()
    try:
        raw = [r for r in db.as_of("llama.stable_total") if r.get("value_num")]
        pts = [(str(r["observed_at"])[:10], float(r["value_num"]),
                r["available_at"]) for r in raw]
        series = [(d, v) for d, v, _ in pts]
        rows = []
        for n in (30, 90):
            for d, v, av in pts:
                prev = _on_or_before(series, _minus(d, n))
                if not prev or prev[0] < _minus(d, n + 5):
                    continue
                rows.append({"registry_key": f"calc.stable_impulse_{n}d",
                             "instrument": None, "observed_at": d,
                             "available_at": av, "value": _pct(v, prev[1]),
                             "source": "derived_state", "availability_kind": "ingest_instant"})
        n_w = db.write_many(obs.drop_unchanged(db, rows))
    finally:
        if own:
            db.close()
    return {"written": n_w, "computed": len(rows)}


# ---------------------------------------------------------------------------
# The Saturday scan's items on a name
# ---------------------------------------------------------------------------
def scan_items(st: Any, since: str, until: str, as_of: Optional[str] = None,
               sym: Optional[str] = None) -> list[dict]:
    """The scan's items on one name (or every basket name), dated in
    (since, until]. Read per name: the item's name is the row's instrument."""
    out = []
    for s in ([sym] if sym else list(names())):
        for r in st.as_of(SCAN_KEY, as_of=as_of, instrument=s):
            d = str(r["observed_at"])[:10]
            if not (since < d <= until) or not r.get("value_text"):
                continue
            try:
                it = json.loads(r["value_text"])
            except ValueError:
                continue
            out.append({**it, "date": d, "name": s})
    return sorted(out, key=lambda x: (x["date"], x["name"]))


def ingest_scan_items(path: Path, store: Any = None, dry_run: bool = False) -> dict:
    """The Saturday scan's basket items, from a YAML list the scan writes:
    [{name: AERO, kind: listing, title: ..., url: ..., date: YYYY-MM-DD}].
    Each must name a basket symbol, a kind from SCAN_KINDS, a URL and a date;
    anything else is refused whole."""
    import yaml  # noqa: PLC0415
    from . import observations as obs, session  # noqa: PLC0415
    items = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or []
    basket = names()
    errs, rows = [], []
    now = session.utc_iso(timespec="microseconds")
    for i, it in enumerate(items):
        bad = [k for k in ("name", "kind", "title", "url", "date") if not it.get(k)]
        if bad:
            errs.append(f"item {i}: missing {', '.join(bad)}")
            continue
        if it["name"] not in basket:
            errs.append(f"item {i}: {it['name']!r} is not a basket name")
        if it["kind"] not in SCAN_KINDS:
            errs.append(f"item {i}: kind {it['kind']!r} not in {SCAN_KINDS}")
        if not re.match(r"^https?://", str(it["url"])):
            errs.append(f"item {i}: url is not a URL")
        try:
            dt.date.fromisoformat(str(it["date"]))
        except ValueError:
            errs.append(f"item {i}: date {it['date']!r} is not YYYY-MM-DD")
        rows.append({"registry_key": SCAN_KEY, "instrument": it["name"],
                     "observed_at": str(it["date"]), "available_at": now,
                     "value": json.dumps({k: it[k] for k in ("kind", "title", "url")},
                                         sort_keys=True),
                     "source": "saturday_scan", "availability_kind": "ingest_instant"})
    if errs:
        return {"written": 0, "refused": errs}
    if dry_run:
        return {"written": 0, "would_write": len(rows)}
    own = store is None
    db = store or obs.ObservationStore()
    try:
        return {"written": db.write_many(rows)}
    finally:
        if own:
            db.close()


# ---------------------------------------------------------------------------
# Item 5: the Weekly
# ---------------------------------------------------------------------------
def tag_moves(table: dict, data: list[dict], col: int, field: str,
              measure: str) -> None:
    """Tag each name's printed move for the consistency gate
    (daily_cascade/consistency.py: a table's `facts`, keyed series|as-of|measure):
    the same move printed anywhere else in the edition must agree with it."""
    for r, d in enumerate(data):
        if d.get("as_of") and d.get(field) is not None:
            table.setdefault("facts", []).append(
                {"row": r, "col": col, "canonical": True,
                 "key": f"crypto_{d['name'].lower()}|{str(d['as_of'])[:10]}|{measure}"})


def weekly_events(st: Any, ending: str, as_of: Optional[str] = None,
                  cfg: Optional[dict] = None) -> list[dict]:
    """What happened this week to a basket name -- and nothing when nothing did:
    a move past the screen's 2.5 sigma, a falsifier threshold crossed, a dated
    event due, a scan item."""
    cfg = cfg or config()
    start = _minus(ending, 7)
    params = cfg.get("grader") or {}
    ev: list[dict] = []
    for sym, n in names(cfg).items():
        pts = [p for p in _pts(st, price_key(sym), as_of) if p[0] <= ending]
        for day in sorted({d for d, _ in pts if d > start}):
            z = move_z([p for p in pts if p[0] <= day])
            if z.get("flagged"):
                ev.append({"kind": "move", "name": sym, "date": day,
                           "z": z["max_abs_z"] * z["sign"], "horizon": z["horizon"],
                           "text": f"{sym} moved {z['max_abs_z']:.1f}σ over "
                                   f"{z['horizon']} day{'s' if z['horizon'] > 1 else ''}"
                                   f" to {day} ({'up' if z['sign'] > 0 else 'down'})"})
                break
        g0 = grade(sym, n, st, as_of, on=start, params=params)
        g1 = grade(sym, n, st, as_of, on=ending, params=params)
        if g1["status"] == "failed" and g0["status"] != "failed":
            ev.append({"kind": "threshold", "name": sym, "date": ending,
                       "text": f"{sym}'s falsifier failed ({g1['detail']})"})
        f = n.get("falsifier") or {}
        e_day = f.get("event_date")
        if e_day and start < e_day <= _minus(ending, -7):
            ev.append({"kind": "dated_event", "name": sym, "date": e_day,
                       "text": f"{sym}: {f.get('event')} on {e_day}"})
    for it in scan_items(st, start, ending, as_of):
        ev.append({"kind": "scan_item", "name": it["name"], "date": it["date"],
                   "text": f"{it['name']}: {it['kind'].replace('_', ' ')} — "
                           f"{it['title']}", "url": it.get("url")})
    return sorted(ev, key=lambda e: (e["date"], e["name"], e["kind"]))


def weekly_line(events: list[dict]) -> Optional[str]:
    """The read path's one line, or None: silence when nothing happened."""
    if not events:
        return None
    return "Crypto basket: " + "; ".join(e["text"] for e in events) + "."


MCAP_NOT_STORED = ("Market cap: not stored for any name yet (DefiLlama's coin "
                   "service, written by the 17:25 ET basket run); the column "
                   "prints once a cap is stored.")


def drop_column(table: dict, name: str) -> None:
    """Remove one column, by its head, from a table and every row."""
    cols = table.get("columns") or []
    if name not in cols:
        return
    i = cols.index(name)
    table["columns"] = cols[:i] + cols[i + 1:]
    table["rows"] = [r[:i] + r[i + 1:] for r in table.get("rows") or []]


def weekly_block(st: Any, ending: str, as_of: Optional[str] = None,
                 cfg: Optional[dict] = None) -> dict:
    """{detail, line, events, data}: the reference tier's two tables (each at
    most six columns) and the events-only line."""
    cfg = cfg or config()
    prows, mrows, data = [], [], []
    for sym, n in names(cfg).items():
        pr = price_row(sym, st, as_of, ending)
        mc = [p for p in _pts(st, f"llama.mcap_{sym.lower()}", as_of) if p[0] <= ending]
        me = measurable(sym, n, st, as_of, ending, 7)
        prows.append([sym, fmt_price(pr.get("price")), fmt_pct(pr.get("week_pct")),
                      fmt_pct(pr.get("d30_pct")), fmt_pct(pr.get("drawdown_pct")),
                      pr.get("as_of") or "not stored"])
        mrows.append([sym, fmt_usd(mc[-1][1]) if mc else "—",
                      me.get("key") and me["key"].split(".", 1)[1].rsplit("_", 1)[0]
                      .replace("_", " ") or "not measured",
                      fmt_usd(me.get("latest")) if me.get("key") else "—",
                      fmt_pct(me.get("change_pct")),
                      me.get("as_of") or (mc[-1][0] if mc else "—")])
        data.append({"name": sym, **{k: pr.get(k) for k in (
            "price", "week_pct", "d30_pct", "drawdown_pct", "as_of")},
            "market_cap": mc[-1][1] if mc else None,
            "measurable": me.get("key"), "measurable_latest": me.get("latest"),
            "measurable_change_pct": me.get("change_pct")})
    events = weekly_events(st, ending, as_of, cfg)
    detail = {"title": "The crypto basket",
              "table": {"columns": ["Name", "Price", "Week", "30 days",
                                    "From its high", "As of"], "rows": prows},
              "tables": [{"columns": ["Name", "Market cap", "What pays the token",
                                      "Latest (7 days)", "Change", "As of"],
                          "rows": mrows}],
              "notes": ["Prices from Yahoo at the symbol the basket config resolved; "
                        "market cap from DefiLlama's coin service; what pays the "
                        "token from DefiLlama, a 7-day sum for fees and revenue, the "
                        "level for TVL. The odds are the operator's and print in "
                        "the Quarterly."]}
    tag_moves(detail["table"], data, 2, "week_pct", "week")
    tag_moves(detail["table"], data, 3, "d30_pct", "30d")
    # W8-11 (weekly-fixes-9): the market-cap column printed "—" for all twelve.
    # No column of dashes: until a cap is stored the column is dropped, with one
    # line saying so.
    if not any(x.get("market_cap") is not None for x in data):
        drop_column(detail["tables"][0], "Market cap")
        detail["notes"].insert(0, MCAP_NOT_STORED)
    # weekly-fixes-7 item 14: every row of both tables "not stored" -> one line,
    # with the date of the first pull (the basket's writers run daily, 17:25 ET).
    if not any(x.get("price") is not None or x.get("market_cap") is not None
               or x.get("measurable_latest") is not None for x in data):
        first = (dt.date.fromisoformat(str(as_of or ending)[:10])
                 + dt.timedelta(days=1))
        detail = {"title": detail["title"],
                  "lines": [f"crypto basket: not stored; first pull "
                            f"{first.day} {first:%b}"]}
    return {"detail": detail, "line": weekly_line(events), "events": events,
            "data": data}


# ---------------------------------------------------------------------------
# Item 5: the Monthly (Themes: digital)
# ---------------------------------------------------------------------------
def monthly_block(st: Any, now: str, cfg: Optional[dict] = None) -> dict:
    """The basket at month resolution: price, month %, cap, drawdown, dilution;
    what pays the token over 30 days; a status line per name."""
    cfg = cfg or config()
    end = now[:10]
    prows, mrows, lines, data = [], [], [], []
    params = cfg.get("grader") or {}
    for sym, n in names(cfg).items():
        pr = price_row(sym, st, now, end)
        mc = _pts(st, f"llama.mcap_{sym.lower()}", now)
        me = measurable(sym, n, st, now, end, 30)
        dl = dilution(sym, st, now)
        g = grade(sym, n, st, now, params=params)
        prows.append([sym, fmt_price(pr.get("price")), fmt_pct(pr.get("d30_pct")),
                      fmt_usd(mc[-1][1]) if mc else "—",
                      fmt_pct(pr.get("drawdown_pct")),
                      f"{dl['ratio']:.2f}" if dl.get("ratio") is not None else "—"])
        mrows.append([sym, me.get("key") and me["key"].split(".", 1)[1]
                      .rsplit("_", 1)[0].replace("_", " ") or "not measured",
                      fmt_usd(me.get("latest")) if me.get("key") else "—",
                      fmt_pct(me.get("change_pct")), me.get("as_of") or "—"])
        lines.append(f"{sym}: {g['status']}"
                     + (f" — {g['detail']}" if g["status"] != "not measured"
                        else f" — {g['detail'].split('— ', 1)[-1]}")
                     + (f" (rule: {g['rule']})" if g.get("rule") else "") + ".")
        data.append({"name": sym, "status": g["status"], "dilution": dl.get("ratio"),
                     "dilution_reason": dl.get("reason"), "as_of": pr.get("as_of"),
                     "price": pr.get("price"), "month_pct": pr.get("d30_pct")})
    table = {"columns": ["Name", "Price", "Month", "Market cap", "From its high",
                         "Dilution"], "rows": prows}
    tag_moves(table, data, 2, "month_pct", "30d")
    mcap_note = []
    if not any(r[3] != "—" for r in prows):            # W8-11
        drop_column(table, "Market cap")
        mcap_note = [MCAP_NOT_STORED]
    return {"title": "Themes: digital — the crypto basket",
            "phase": "block:slow:crypto_basket",
            "table": table,
            "tables": [{"columns": ["Name", "What pays the token", "Latest (30 days)",
                                    "Change", "As of"], "rows": mrows}],
            "lines": lines, "not_tracked": [],
            "notes": mcap_note + ["Dilution is a year's issuance (the change in stored "
                      "circulating supply, at today's price) over the value "
                      "returned to holders (DefiLlama's holders revenue: buybacks, "
                      "burns and distributions); not measured where a leg is "
                      "absent. Status is each name's falsifier, graded by rule."],
            "data": {"rows": data}}


# ---------------------------------------------------------------------------
# Item 4: the odds restatement (decision 3, ruled as the alternative)
# ---------------------------------------------------------------------------
class RestatementRefused(ValueError):
    """A restatement that breaks decision 3's rules is not written."""


ONE_CLAUSE = re.compile(r"^[^.;:!?\n]{3,160}\.?$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def reference_odds(n: dict) -> dict:
    """The operator's original, exactly as hand-seeded: the reference column."""
    o = n.get("odds") or {}
    return {"10x": o.get("operator_10x"), "100x": o.get("operator_100x"),
            "dated": str(o.get("dated")), "source": o.get("source")}


def quarter_of(day: str) -> str:
    d = dt.date.fromisoformat(day[:10])
    return f"{d.year}Q{(d.month - 1) // 3 + 1}"


def quarter_bounds(q: str) -> tuple[str, str]:
    y, n = int(q[:4]), int(q[-1])
    start = dt.date(y, 3 * (n - 1) + 1, 1)
    end = (dt.date(y + (n == 4), (3 * n) % 12 + 1, 1) - dt.timedelta(days=1))
    return start.isoformat(), end.isoformat()


def named_changes(sym: str, n: dict, st: Any, as_of: Optional[str],
                  q_start: str, q_end: str, params: Optional[dict] = None) -> list[str]:
    """The quarter's changes a restatement may move on: a falsifier's state, a
    measurable past MEASURABLE_MOVE, a scan item (exploit, listing, a fee-switch
    vote)."""
    out = []
    g0 = grade(sym, n, st, as_of, on=q_start, params=params)
    g1 = grade(sym, n, st, as_of, on=q_end, params=params)
    if g0["status"] != g1["status"]:
        out.append(f"falsifier {g0['status']} to {g1['status']}")
    key = (n.get("measurable") or {}).get("key")
    if key:
        pts = [p for p in _pts(st, key, as_of) if p[0] <= q_end]
        if _flow(key):
            a, b = _sum_window(pts, q_end, 30), _sum_window(pts, q_start, 30)
        else:
            a = pts[-1][1] if pts else None
            prev = _on_or_before(pts, q_start)
            b = prev[1] if prev else None
        ch = _pct(a, b)
        if ch is not None and abs(ch) >= 100 * MEASURABLE_MOVE:
            out.append(f"{key} {ch:+.0f}% on the quarter")
    for it in scan_items(st, q_start, q_end, as_of, sym):
        out.append(f"{it['kind'].replace('_', ' ')}: {it['title']}")
    return out


def _range(s: Any) -> Optional[tuple[float, float]]:
    s = str(s or "").replace("%", "").replace("−", "-").strip()
    try:
        if s.startswith("~"):
            v = float(s[1:])
            return v, v
        if s.startswith("<"):
            return 0.0, float(s[1:])
        if "–" in s or "-" in s[1:]:
            a, b = re.split(r"[–-]", s, maxsplit=1)
            return float(a), float(b)
        return float(s), float(s)
    except ValueError:
        return None


def validate_restatement(row: dict, prior: dict, changes: list[str]) -> None:
    """Decision 3's rules, enforced. Raises RestatementRefused."""
    if not DATE_RE.match(str(row.get("dated") or "")):
        raise RestatementRefused("an undated odds row is refused: every "
                                 "restatement carries the date it was made")
    for k in ("10x", "100x"):
        r = _range(row.get(k))
        if r is None or not (0 <= r[0] <= r[1] <= 100):
            raise RestatementRefused(f"odds of {k} {row.get(k)!r} are not a "
                                     f"percentage or range between 0 and 100")
    moved = (row.get("10x"), row.get("100x")) != (prior.get("10x"), prior.get("100x"))
    if not moved:
        return
    if not changes:
        raise RestatementRefused("no measurable moved this quarter, so the odds "
                                 "may not move: print 'unchanged — no measurable "
                                 "moved'")
    reason = str(row.get("reason") or "").strip()
    if not reason:
        raise RestatementRefused("a move without a reason is refused")
    if not ONE_CLAUSE.match(reason):
        raise RestatementRefused(f"the reason must be one clause: {reason!r}")
    if row.get("change") not in changes:
        raise RestatementRefused(f"the move names {row.get('change')!r}, which is "
                                 f"not one of this quarter's changes: {changes}")


def restate(sym: str, n: dict, st: Any, quarter: str, prior: Optional[dict],
            propose: Callable[..., dict], quarterly_run: Optional[str],
            as_of: Optional[str] = None, params: Optional[dict] = None,
            today: Optional[str] = None) -> dict:
    """One name's restatement for `quarter`. Runs inside the Quarterly only:
    `quarterly_run` is the Quarterly run's id, and nothing restates without it.
    With no named change the model is not asked and the row reads "unchanged --
    no measurable moved"."""
    if not quarterly_run:
        raise RestatementRefused("the restatement runs inside the Quarterly only")
    ref = reference_odds(n)
    prior = prior or {"10x": ref["10x"], "100x": ref["100x"]}
    q_start, q_end = quarter_bounds(quarter)
    changes = named_changes(sym, n, st, as_of, q_start, q_end, params)
    dated = today or _cutoff(as_of)[:10]
    if not changes:
        row = {"10x": prior["10x"], "100x": prior["100x"], "dated": dated,
               "reason": "unchanged — no measurable moved", "change": None,
               "direction": "unchanged"}
        validate_restatement(row, prior, changes)
        return {**row, "quarter": quarter, "changes": [], "name": sym}
    got = propose(sym=sym, reference=ref, prior=prior, changes=changes, name=n)
    row = {"10x": got.get("10x"), "100x": got.get("100x"),
           "dated": got.get("dated", dated), "reason": got.get("reason"),
           "change": got.get("change")}
    validate_restatement(row, prior, changes)
    a, b = _range(row["10x"]), _range(prior["10x"])
    row["direction"] = ("unchanged" if a == b else
                        "up" if sum(a) > sum(b) else "down")
    if row["direction"] == "unchanged" and not row.get("reason"):
        row["reason"] = "unchanged — no measurable moved"
    return {**row, "quarter": quarter, "changes": changes, "name": sym}


def register_entry(row: dict, n: dict, run_id: str) -> dict:
    """The thesis-register entry for one restatement, in aq-6's shape
    (altdata/thesis_register.py on aq-6-thesis-register: ledger source
    `alt_asset:<family>`, a scenario set `<family>-<quarter>-<kind>`), labelled
    "model estimate" and emitted by the model. Graded next quarter on the
    DIRECTION of the move against the named measurable."""
    sym = row["name"]
    fam = f"crypto_basket.{sym.lower()}"
    return {"source": f"{REGISTER_SOURCE}:{fam}", "family": fam,
            "quarter": row["quarter"], "scenario_set": f"{fam}-{row['quarter']}-odds",
            "label": MODEL_LABEL, "emitted_by": "model", "run_id": run_id,
            "claims": [{"claim": f"{n.get('name')} ({sym}) rises tenfold",
                        "odds": row["10x"]},
                       {"claim": f"{n.get('name')} ({sym}) rises a hundredfold",
                        "odds": row["100x"]}],
            "dated": row["dated"], "direction": row["direction"],
            "reason": row["reason"], "change": row.get("change"),
            "graded_against": (n.get("measurable") or {}).get("key")
            or (n.get("falsifier") or {}).get("series"),
            "resolution": "next quarter: does the named measurable move in the "
                          "direction the odds moved",
            "reference": reference_odds(n)}


def dry_run_path() -> Path:
    """THE DRY-RUN NAMESPACE: the thesis register's entries land here until
    aq-6-thesis-register merges -- a file beside the state, never the register."""
    base = Path(os.environ.get("CHESTER_DRYRUN_DIR")
                or Path(os.environ.get("CHESTER_STATE_DIR")
                        or Path.home() / "state") / "dryrun")
    return base / "alt_asset" / "crypto_basket_restatements.jsonl"


def write_entries(entries: list[dict], path: Optional[Path] = None) -> Path:
    p = path or dry_run_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fp:
        for e in entries:
            fp.write(json.dumps(e, sort_keys=True, ensure_ascii=False) + "\n")
    return p


def read_entries(path: Optional[Path] = None) -> list[dict]:
    p = path or dry_run_path()
    if not p.exists():
        return []
    return [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines() if ln]


def model_proposer(model: Optional[str] = None) -> Callable[..., dict]:
    """The model's restatement: one call per name with a named change, asked for
    JSON {"10x", "100x", "change", "reason"}. Every answer passes
    validate_restatement before it is used."""
    def propose(sym, reference, prior, changes, name) -> dict:
        from daily_cascade import narrative  # noqa: PLC0415
        client, why = narrative._client()
        if client is None:
            raise RestatementRefused(f"model unavailable: {why}")
        prompt = (
            f"Restate the odds that {name.get('name')} ({sym}) rises 10x and 100x "
            f"over five to ten years. The operator's reference of "
            f"{reference['dated']}: 10x {reference['10x']}, 100x {reference['100x']}. "
            f"Last quarter's: 10x {prior['10x']}, 100x {prior['100x']}. What pays "
            f"the token: {(name.get('measurable') or {}).get('pays')}. This "
            f"quarter's measurable changes: {json.dumps(changes)}. Move the odds "
            f"only on one of those changes. Answer JSON only: "
            f'{{"10x": "a-b%", "100x": "a-b%", "change": "<one of the changes, '
            f'verbatim>", "reason": "<one clause>"}}.')
        from . import model_meter                                # noqa: PLC0415
        with model_meter.scope(section="crypto_basket"):
            resp = model_meter.create(
                client,
                model=model or os.environ.get("CRYPTO_BASKET_MODEL",
                                              narrative.DEFAULT_MODEL),
                max_tokens=300, messages=[{"role": "user", "content": prompt}])
        text = "".join(b.text for b in resp.content
                       if getattr(b, "type", None) == "text")
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            raise RestatementRefused("the model's answer was not JSON")
        return json.loads(m.group(0))
    return propose


def restate_quarter(st: Any, quarter: str, quarterly_run: str,
                    propose: Optional[Callable[..., dict]] = None,
                    as_of: Optional[str] = None, path: Optional[Path] = None,
                    cfg: Optional[dict] = None) -> list[dict]:
    """Every name's restatement for the quarter, written to the dry-run
    namespace. Called by the Quarterly's run, with its run id; a refused row is
    kept as the refusal, and the name prints its prior odds."""
    cfg = cfg or config()
    prior_by = {}
    for e in read_entries(path):
        if e.get("quarter", "") < quarter:
            prior_by[e["family"]] = {"10x": e["claims"][0]["odds"],
                                     "100x": e["claims"][1]["odds"]}
    out, entries = [], []
    for sym, n in names(cfg).items():
        fam = f"crypto_basket.{sym.lower()}"
        try:
            row = restate(sym, n, st, quarter, prior_by.get(fam),
                          propose or model_proposer(), quarterly_run, as_of,
                          cfg.get("grader"))
        except RestatementRefused as exc:
            out.append({"name": sym, "quarter": quarter, "refused": str(exc)})
            continue
        out.append(row)
        entries.append(register_entry(row, n, quarterly_run))
    if entries:
        write_entries(entries, path)
    return out


def odds_table(n: dict, restated: Optional[dict] = None) -> dict:
    """The three columns: the reference (the operator's original, printed
    unchanged), the model's restatement, and the operator's own when seeded."""
    ref = reference_odds(n)
    cols = ["Odds", f"Reference, {ref['dated']}"]
    rows = [["10×", ref["10x"]], ["100×", ref["100x"]]]
    if restated:
        cols.append(f"Model estimate, {restated.get('dated')}")
        if restated.get("refused"):
            rows[0].append("refused")
            rows[1].append("refused")
        else:
            rows[0].append(restated["10x"])
            rows[1].append(restated["100x"])
    op = n.get("operator_restatement")
    if op:
        cols.append(f"Operator, {op.get('dated')}")
        rows[0].append(op.get("10x"))
        rows[1].append(op.get("100x"))
    return {"columns": cols, "rows": rows}


# ---------------------------------------------------------------------------
# Item 5: the Quarterly's basket tier, half a page per name
# ---------------------------------------------------------------------------
# MW-7 AS §4.6 APPLIES IT: the roster is refreshed on executable depth and
# turnover, never on market cap alone, and only the operator changes a tier (MW-6).
# No numeric bar is set for the basket tier; the figures print and the call is his.
MW7 = ("MW-7 (§4.6): promote, demote or remove on executable depth and turnover, "
       "never on market cap alone; the operator decides (MW-6), and no numeric bar "
       "is set for the basket tier.")


def turnover(sym: str, st: Any, as_of: Optional[str], q_start: str,
             q_end: str) -> dict:
    """Mean daily volume over mean market cap, the quarter: MW-7's turnover."""
    vol = [v for d, v in _pts(st, price_key(sym) + "_volume", as_of)
           if q_start <= d <= q_end]
    cap = [v for d, v in _pts(st, f"llama.mcap_{sym.lower()}", as_of)
           if q_start <= d <= q_end]
    if not vol or not cap:
        return {"turnover": None,
                "reason": "not measured — " + ("no stored volume" if not vol
                                                 else "no stored market cap")}
    return {"turnover": statistics.fmean(vol) / statistics.fmean(cap),
            "days": len(vol)}


def quarterly_pages(st: Any, quarter: str, restated: Optional[dict] = None,
                    as_of: Optional[str] = None, cfg: Optional[dict] = None
                    ) -> list[dict]:
    """One half-page per name: the thesis and odds (quoted, dated), the
    measurables' quarter, the falsifier's state, dilution, US access, the scan's
    stories on the name, and MW-7 applied on executable depth and turnover. PRL
    carries SR-10's signposts as its falsifier set and no coin page."""
    cfg = cfg or config()
    q_start, q_end = quarter_bounds(quarter)
    params = cfg.get("grader") or {}
    pages = []
    for sym, n in names(cfg).items():
        pr = price_row(sym, st, as_of, q_end)
        me = measurable(sym, n, st, as_of, q_end, 91)
        g = grade(sym, n, st, as_of, on=q_end, params=params)
        dl = dilution(sym, st, as_of)
        to = turnover(sym, st, as_of, q_start, q_end)
        stories = scan_items(st, _minus(q_start, 1), q_end, as_of, sym)
        f = n.get("falsifier") or {}
        lines = [f"Thesis (the operator's, {reference_odds(n)['dated']}): "
                 f"“{n.get('thesis')}”",
                 f"What pays the token: “{(n.get('measurable') or {}).get('pays')}”"
                 + (f" — {me['form']} {fmt_usd(me.get('latest'))} to "
                    f"{me.get('as_of')}, {fmt_pct(me.get('change_pct'))} on the "
                    f"quarter" if me.get("key") and me.get("latest") is not None
                    else f" — {me.get('reason')}"),
                 f"Price {fmt_price(pr.get('price'))}, "
                 f"{fmt_pct(pr.get('q_pct'))} on the quarter, "
                 f"{fmt_pct(pr.get('drawdown_pct'))} from its high"
                 + (f" ({pr.get('high_on')})" if pr.get("high_on") else ""),
                 f"Falsifier: {g['status']} — {g['detail'].split('— ', 1)[-1]}"
                 + (f" (rule: {g['rule']})" if g.get("rule") else ""),
                 "Dilution: " + (f"{dl['ratio']:.2f}" if dl.get("ratio") is not None
                                 else dl["reason"]),
                 f"US access: {n.get('us_access')}",
                 "The scan's stories: " + ("; ".join(
                     f"{s['date']} {s['kind'].replace('_', ' ')}: {s['title']}"
                     for s in stories) or "none stored this quarter"),
                 f"MW-7: turnover "
                 + (f"{to['turnover']:.1%} a day" if to.get("turnover") is not None
                    else to["reason"])
                 + "; executable depth not measured — order-book depth has no free "
                   "source. " + MW7]
        if f.get("kind") == "signposts":
            lines.insert(4, f"Signposts: {f.get('signposts')}; no coin page "
                            f"(demoted from deep tier, 12 Oct 2026)")
        pages.append({"title": f"{n.get('name')} ({sym})", "name": sym,
                      "table": odds_table(n, (restated or {}).get(sym)),
                      "lines": lines,
                      "quotes": {"case_for": n.get("case_for"),
                                 "case_against": n.get("case_against")},
                      "data": {"status": g["status"], "dilution": dl.get("ratio"),
                               "turnover": to.get("turnover")}})
    return pages


# ---------------------------------------------------------------------------
def _main(argv: list[str]) -> int:
    import argparse  # noqa: PLC0415
    import sys  # noqa: PLC0415
    ap = argparse.ArgumentParser(description="The crypto basket.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("derive")
    sub.add_parser("grade")
    si = sub.add_parser("scan-items")
    si.add_argument("file")
    si.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    from . import observations as obs  # noqa: PLC0415
    if a.cmd == "derive":
        print("dilution:", write_dilution())
        print("stable impulse:", write_stable_impulse())
        return 0
    if a.cmd == "scan-items":
        r = ingest_scan_items(Path(a.file), dry_run=a.dry_run)
        print(r)
        return 1 if r.get("refused") else 0
    with obs.ObservationStore() as st:
        for sym, n in names().items():
            g = grade(sym, n, st)
            print(f"  {sym:<7} {g['status']:<13} {g['detail']}")
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
