"""
The evening note, 21:30 ET Sunday to Thursday (docs/change-order-secondary-notes-
2026-10-19.md section 2, ruled 19 Oct 2026, 14:14 ET).

    python -m daily_cascade.evening_note [--date D] [--as-of ISO] [--dry-run] [--email]
        [--archive-dir DIR] [--db PATH] [--computed-dir DIR] [--no-narrative]

What has happened since the 16:45 close: US futures, after-hours earnings, Asia's
open, currencies, crypto, news and tonight's Book D drafts. It prepares tomorrow's
07:00 anchor and has NO RIGHTS over any book; its default line is "Nothing to do
tonight; the 07:00 anchor re-reads all of this."

THE SUNDAY EDITION (D7) adds the futures open against Friday and the weekend's
news in two parts: what is new since the 05:00 Weekly first, then Friday 16:45 to
Sunday 05:00.

Prose only when the gate opens on a weekday (at most 150 words; the thresholds are
session-set in config secondary_notes.evening), and always on Sunday (at most
400). READS THE STORE ONLY: altdata/note_fetch.py `evening` wrote it at 21:30.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import sqlite3
import sys
from pathlib import Path
from typing import Any, Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from daily_cascade import note_common as nc                       # noqa: E402

log = logging.getLogger("daily_cascade.evening_note")

REPORT = "evening_note"
DEFAULT_LINE = "Nothing to do tonight; the 07:00 anchor re-reads all of this."
FUTURES = (("es", "ES"), ("nq", "NQ"), ("rty", "RTY"))
ASIA = ("n225", "hsi", "sse", "kospi")
INDEX_FUNDS = {"SPY", "QQQ", "IWM"}


def is_sunday(day: str) -> bool:
    return dt.date.fromisoformat(day).weekday() == 6


def since_day(day: str) -> str:
    """The session the evening follows: today, or Friday on a Sunday."""
    from altdata import session                                 # noqa: PLC0415
    return session.last_trading_session(day).isoformat()


# ---------------------------------------------------------------------------
# Block 1: US futures (and the Sunday open against Friday)
# ---------------------------------------------------------------------------
def es_levels(printed: str, db_path=None) -> list[dict]:
    """The ES block's levels for tomorrow, as the 16:45 close printed them
    (es_ledger, slot close), read-only."""
    from altdata import observations                            # noqa: PLC0415
    p = Path(db_path or observations.DEFAULT_DB)
    if not p.exists():
        return []
    try:
        con = sqlite3.connect(f"{p.resolve().as_uri()}?mode=ro", uri=True)
        rows = con.execute("SELECT label, level, side FROM es_ledger WHERE printed_session"
                           " = ? AND slot = 'close' AND kind = 'level' ORDER BY level",
                           (printed,)).fetchall()
        con.close()
    except sqlite3.Error:
        return []
    return [{"label": r[0], "level": r[1], "side": r[2]} for r in rows if r[1] is not None]


def gauge(sess: str, cutoff: str, db_path=None) -> dict:
    from . import opening_setup                                 # noqa: PLC0415
    try:
        return (opening_setup.gauge_from_store(sess, cutoff, db_path) or {}).get("values") or {}
    except Exception:                                           # noqa: BLE001
        return {}


def futures_block(day: str, ref: str, cutoff: str, db_path=None, g: Optional[dict] = None
                  ) -> dict:
    from altdata import es_block                                # noqa: PLC0415
    now = nc.parse(cutoff)
    out = {"title": "US futures since the 16:00 cash close", "as_of": nc.hm_et(cutoff),
           "lines": [], "moves": {}}
    g = g if g is not None else gauge(ref, cutoff, db_path)
    sig = g.get("sigma_1_pct")
    for inst, label in FUTURES:
        bars = nc.read_bars(inst, nc.et(ref, "15:30"), now, cutoff, db_path)
        c16 = nc.last_ending_by(bars, nc.et(ref, "16:00"))
        halt = nc.last_ending_by(bars, nc.et(ref, "17:00"))
        last = nc.newest(bars)
        if not (c16 and last):
            out["lines"].append(f"{label}: no bars stored since the 16:00 close.")
            continue
        m16, mh = nc.pct(c16["close"], last["close"]), \
            (nc.pct(halt["close"], last["close"]) if halt else None)
        out["moves"][inst] = {"close_16": c16["close"], "halt": (halt or {}).get("close"),
                              "last": last["close"], "last_at": nc.hm_et(last["observed_at"]),
                              "move_16_pct": m16, "move_halt_pct": mh}
        out["lines"].append(
            f"{label} {last['close']:,.2f} at {nc.hm_et(last['observed_at'])}: "
            f"{nc.signed(m16)} from the 16:00 close {c16['close']:,.2f}"
            + (f", {nc.signed(mh)} from the last trade before the 17:00 halt "
               f"{halt['close']:,.2f}" if halt else "") + ".")
    es = out["moves"].get("es")
    if es and sig is not None:
        out["sigma_1_pct"] = round(float(sig), 2)
        inside = abs(es["move_16_pct"]) <= out["sigma_1_pct"]
        out["lines"].append(f"ES's move against the gauge's implied one-session move "
                            f"{out['sigma_1_pct']:.2f}% ({ref} close): "
                            f"{'inside' if inside else 'outside'}.")
    lv = es_levels(ref, db_path)
    if es and lv:
        px = es["last"]
        above = [x for x in lv if x["level"] > px]
        below = [x for x in lv if x["level"] <= px]
        parts = []
        if above:
            parts.append(f"next above {above[0]['level']:,.2f} ({above[0]['label']})")
        if below:
            parts.append(f"next below {below[-1]['level']:,.2f} ({below[-1]['label']})")
        out["lines"].append(f"ES against the levels the {ref} close printed: "
                            + "; ".join(parts) + ".")
        out["es_levels"] = lv
    elif es:
        out["lines"].append(f"ES levels from the {ref} close: not stored.")
    out["lines"].append(es_block.DEALER_PENDING[:1].upper() + es_block.DEALER_PENDING[1:] + " (ST-R6.45c waits on 6b).")
    return out


def sunday_open_block(fri: str, day: str, cutoff: str, db_path=None,
                      g: Optional[dict] = None) -> dict:
    """D7: the futures open against Friday."""
    now = nc.parse(cutoff)
    out = {"title": "The futures open against Friday", "as_of": nc.hm_et(cutoff),
           "lines": [], "moves": {}}
    g = g if g is not None else gauge(fri, cutoff, db_path)
    s1, s5 = g.get("sigma_1_pct"), g.get("sigma_5_pct")
    reopen = nc.et(day, "18:00")
    for inst, label in (*FUTURES, ("zn", "10-year note future (ZN)")):
        bars = nc.read_bars(inst, nc.et(fri, "15:30"), now, cutoff, db_path)
        c16 = nc.last_ending_by(bars, nc.et(fri, "16:00"))
        halt = nc.last_ending_by(bars, nc.et(fri, "17:00"))
        first = nc.first_from(bars, reopen)
        since = [b for b in bars if nc.parse(b["observed_at"]) >= reopen]
        if not (halt and first):
            out["lines"].append(f"{label}: Friday's last trade or Sunday's reopen is not stored.")
            continue
        hi, lo, last = max(b["high"] for b in since), min(b["low"] for b in since), \
            nc.newest(since)
        mv = {"close_16": (c16 or {}).get("close"), "halt": halt["close"],
              "open": first["open"], "high": hi, "low": lo, "last": last["close"],
              "open_pct": nc.pct(halt["close"], first["open"]),
              "since_pct": nc.pct(halt["close"], last["close"])}
        out["moves"][inst] = mv
        out["lines"].append(
            f"{label}: Friday {(c16 or {}).get('close', 'n/a')} at 16:00, {halt['close']:,.2f} "
            f"before the 17:00 halt; reopened {first['open']:,.2f} ({nc.signed(mv['open_pct'])}); "
            f"since then high {hi:,.2f}, low {lo:,.2f}, latest {last['close']:,.2f} "
            f"({nc.signed(mv['since_pct'])} against Friday).")
    if s1 is not None and "es" in out["moves"]:
        out["sigma_1_pct"], out["sigma_5_pct"] = round(float(s1), 2), \
            (round(float(s5), 2) if s5 is not None else None)
        out["lines"].append(
            f"Against the gauge as of Friday's close: implied one-session move "
            f"{out['sigma_1_pct']:.2f}%"
            + (f", five-session {out['sigma_5_pct']:.2f}%" if out["sigma_5_pct"] else "")
            + f"; ES's {nc.signed(out['moves']['es']['since_pct'])} is "
            f"{'inside' if abs(out['moves']['es']['since_pct'] or 0) <= out['sigma_1_pct'] else 'outside'}"
            " the one-session move.")
    jb = nc.read_bars("usdjpy", nc.et(fri, "15:30"), now, cutoff, db_path)
    jf = nc.last_ending_by(jb, nc.et(fri, "17:00"))
    jo = nc.first_from(jb, nc.et(fri, "17:00") + dt.timedelta(hours=24))
    if jf and jo:
        out["usdjpy_gap_pct"] = nc.pct(jf["close"], jo["open"])
        out["lines"].append(f"Dollar-yen's weekend gap: {jf['close']:,.2f} at Friday's New "
                            f"York close to {jo['open']:,.2f} at its open "
                            f"({nc.signed(out['usdjpy_gap_pct'])}).")
    else:
        out["lines"].append("Dollar-yen's weekend gap: not stored.")
    return out


# ---------------------------------------------------------------------------
# Block 2: after-hours earnings
# ---------------------------------------------------------------------------
def earnings_block(day: str, cutoff: str, db_path=None, universe=None) -> dict:
    from altdata import config as acfg, events as ev_mod, note_fetch, observations  # noqa
    out = {"title": "After-hours earnings", "as_of": nc.hm_et(cutoff), "lines": [],
           "names": []}
    uni = [s for s in (universe or acfg.chain_universe()) if s not in INDEX_FUNDS]
    uni = [s for s in uni if not _restricted(s)]
    names = note_fetch.after_hours_names(day, db_path, cutoff, uni)
    if not names:
        out["lines"].append("No captured name reports after the close today.")
        return out
    with ev_mod.EventStore(db_path) as ev:
        rep = {str((r.get("payload") or {}).get("symbol") or "").upper(): r.get("payload") or {}
               for r in ev.calendar(day, day, as_of=cutoff) if r.get("type") == "earnings"}
    with observations.ObservationStore(db_path) as st:
        for sym in names:
            row = {"symbol": sym}
            pl = rep.get(sym) or {}
            if pl.get("reported_eps") is not None:
                row["eps"], row["eps_estimate"] = pl.get("reported_eps"), pl.get("eps_estimate")
                eps = (f"EPS {row['eps']} against the analyst mean {row['eps_estimate']} "
                       "(yfinance)")
            else:
                eps = "EPS not yet served"
            ah = [r for r in st.as_of(note_fetch.AH_KEY, cutoff, sym)
                  if str(r["observed_at"])[:10] == day]
            if ah:
                rec = json.loads(ah[-1]["value_text"])
                row["ah_move_pct"], row["ah_at"] = rec.get("move_pct"), nc.hm_et(rec.get("at"))
                mv = f"after hours {nc.signed(row['ah_move_pct'])} at {row['ah_at']}"
            else:
                mv = "no after-hours price served"
            im = _implied(sym, day)
            row["implied"] = im
            out["names"].append(row)
            out["lines"].append(f"{sym}: {eps}; {mv}; {im or 'implied move not stored'}.")
    out["lines"].append("Never a recommendation.")
    return out


def _restricted(sym: str) -> bool:
    try:
        from register import instruments                        # noqa: PLC0415
        return instruments.restrictions().is_restricted(sym)
    except Exception:                                           # noqa: BLE001
        return False


def _implied(sym: str, day: str) -> Optional[str]:
    try:
        from . import ahead                                     # noqa: PLC0415
        return ahead.implied_move(sym, day, f"{day}T21:30:00+00:00", days_back=0)
    except Exception:                                           # noqa: BLE001
        return None


# ---------------------------------------------------------------------------
# Block 3: Asia's open
# ---------------------------------------------------------------------------
def asia_block(day: str, cutoff: str, db_path=None) -> dict:
    cfg = nc.config()["note_bars"]
    now = nc.parse(cutoff)
    out = {"title": "Asia's open", "as_of": nc.hm_et(cutoff), "lines": [], "moves": {}}
    for inst in ASIA:
        t = cfg.get(inst) or {}
        o = nc.local_open_et(day, t["tz"], t["open"])
        o_et = nc.hm_et(nc.iso(o))
        bars = nc.read_bars(inst, nc.et(day, "00:00") - dt.timedelta(days=4), now, cutoff,
                            db_path)
        prior = nc.last_ending_by(bars, o)
        after = [b for b in bars if nc.parse(b["observed_at"]) >= o]
        if o > now:
            out["lines"].append(f"{t['label']}: opens at {o_et}; not yet open.")
            continue
        if not after:
            out["lines"].append(f"{t['label']}: opened at {o_et}; no bars served yet "
                                "(Yahoo's delay).")
            continue
        last = nc.newest(after)
        if not prior:
            out["lines"].append(f"{t['label']}: its prior close is not stored.")
            continue
        mv = nc.pct(prior["close"], last["close"])
        out["moves"][inst] = {"prior": prior["close"], "last": last["close"], "move_pct": mv,
                              "at": nc.hm_et(last["observed_at"])}
        out["lines"].append(f"{t['label']} {last['close']:,.2f} at "
                            f"{nc.hm_et(last['observed_at'])}, {nc.signed(mv)} against its "
                            f"prior close {prior['close']:,.2f} (opened {o_et}).")
    return out


# ---------------------------------------------------------------------------
# Block 4: currencies
# ---------------------------------------------------------------------------
def currencies_block(day: str, ref: str, cutoff: str, db_path=None) -> dict:
    from altdata import observations                            # noqa: PLC0415
    from altdata.absorption import series                       # noqa: PLC0415
    from . import funding_hooks                                 # noqa: PLC0415
    now = nc.parse(cutoff)
    out = {"title": "Currencies", "as_of": nc.hm_et(cutoff), "lines": [], "moves": {},
           "hooks": []}
    quotes = {}
    for inst, sym, label in (("usdjpy", "JPY=X", "Dollar-yen"),
                             ("cnh", "CNH=X", "Dollar-yuan offshore")):
        bars = nc.read_bars(inst, nc.et(ref, "15:30"), now, cutoff, db_path)
        c16, last = nc.last_ending_by(bars, nc.et(ref, "16:00")), nc.newest(bars)
        if not (c16 and last):
            out["lines"].append(f"{label}: no bars stored since 16:00.")
            continue
        quotes[sym] = last["close"]
        mv = nc.pct(c16["close"], last["close"])
        out["moves"][inst] = {"close_16": c16["close"], "last": last["close"], "move_pct": mv}
        out["lines"].append(f"{label} {last['close']:,.4f} at {nc.hm_et(last['observed_at'])}, "
                            f"{nc.signed(mv)} since 16:00.")
    bj = (dt.date.fromisoformat(day) + dt.timedelta(days=1)).isoformat()
    try:
        with observations.ObservationStore(db_path) as st:
            fix = [(d, v) for d, v, _ in series(st, "cfets.cny_fix", cutoff) if d == bj]
            cny = [(d, v) for d, v, _ in series(st, "yfinance.mkt_usdcny", cutoff) if d < bj]
    except Exception:                                           # noqa: BLE001
        fix, cny = [], []
    if fix and cny:
        out["fix"] = {"date": bj, "fix": fix[-1][1], "cny_prev": cny[-1][1],
                      "vs_prev_pct": nc.pct(cny[-1][1], fix[-1][1])}
        out["lines"].append(f"The PBoC fix for {bj}: {fix[-1][1]:,.4f}, against the prior "
                            f"onshore close {cny[-1][1]:,.4f} ({cny[-1][0]}).")
    else:
        out["lines"].append(f"The PBoC fix for {bj}: not yet published or not stored.")
    ctx = {"day": bj, "quotes": quotes, **funding_hooks.context(bj, cutoff, db_path)}
    for fn in (funding_hooks.yen_unwind, funding_hooks.deval_trip):
        try:
            h = fn(ctx)
        except Exception as exc:                                # noqa: BLE001
            h = {"id": fn.__name__, "open": False, "why": f"{type(exc).__name__}"}
        out["hooks"].append({"id": h["id"], "open": bool(h.get("open"))})
        txt = (h.get("line") or "").replace("at 12:30", "at 21:30").replace(
            "12:30 quote", "21:30 quote") if h.get("open") else \
            f"{h['id'].replace('_', ' ')}: not tripped ({str(h.get('why')).replace('12:30', '21:30')})."
        out["lines"].append(txt + " Descriptive only; no new flag.")
    return out


# ---------------------------------------------------------------------------
# Block 5: crypto
# ---------------------------------------------------------------------------
def crypto_block(ref: str, cutoff: str, db_path=None) -> dict:
    from altdata import observations                            # noqa: PLC0415
    from altdata.absorption import series                       # noqa: PLC0415
    now = nc.parse(cutoff)
    out = {"title": "Crypto since 16:45", "as_of": nc.hm_et(cutoff), "lines": [], "moves": {}}
    for inst, label in (("btc", "BTC"), ("eth", "ETH")):
        bars = nc.read_bars(inst, nc.et(ref, "16:00"), now, cutoff, db_path)
        a, last = nc.last_ending_by(bars, nc.et(ref, "16:45")), nc.newest(bars)
        if not (a and last):
            out["lines"].append(f"{label}: no bars stored since 16:45.")
            continue
        mv = nc.pct(a["close"], last["close"])
        out["moves"][inst] = {"from": a["close"], "last": last["close"], "move_pct": mv}
        out["lines"].append(f"{label} {last['close']:,.0f}, {nc.signed(mv)} since 16:45.")
    try:
        with observations.ObservationStore(db_path) as st:
            for coin in ("BTC", "ETH"):
                f = series(st, "calc.funding_agg", cutoff, coin)
                if f:
                    out["lines"].append(f"{coin} perp funding, OI-weighted across exchanges "
                                        f"(annualised), as last stored ({f[-1][0]}): "
                                        f"{f[-1][1]:.2f}%.")
            etf = series(st, "farside.btc_total", cutoff)
    except Exception:                                           # noqa: BLE001
        etf = []
    fresh = etf and etf[-1][0] >= (dt.date.fromisoformat(ref) - dt.timedelta(days=3)).isoformat()
    from altdata import refusals                                # noqa: PLC0415
    gap = refusals.text("farside")
    out["lines"].append(f"ETF flows: {gap}." if gap else
                        f"ETF flows ({etf[-1][0]}): {etf[-1][1]:,.1f}." if fresh
                        else "ETF flows: gap.")
    return out


# ---------------------------------------------------------------------------
# Block 7: Book D
# ---------------------------------------------------------------------------
def book_d_block(day: str, cutoff: str, register_db: Optional[str] = None) -> dict:
    """Tonight's meme drafts, count and names, read-only. Decided at 07:00."""
    out = {"title": "Book D", "as_of": nc.hm_et(cutoff), "lines": [], "drafts": []}
    try:
        from register import store as rstore                    # noqa: PLC0415
        p = Path(register_db or rstore.DEFAULT_DB)
        con = sqlite3.connect(f"{p.resolve().as_uri()}?mode=ro", uri=True)
        rows = con.execute("SELECT ticker, direction, ingested_at FROM meme_drafts WHERE "
                           "review = 'awaiting' AND ingested_at >= ? AND ingested_at <= ? "
                           "ORDER BY ticker", (nc.iso(nc.et(day, "17:00")), cutoff)).fetchall()
        con.close()
    except Exception:                                           # noqa: BLE001
        out["lines"].append("Book D drafts: the meme ingest's table is not readable here.")
        return out
    out["drafts"] = [{"ticker": r[0], "direction": r[1]} for r in rows]
    out["count"] = len(rows)
    out["lines"].append(
        f"Tonight's Book D drafts: {len(rows)}"
        + (": " + ", ".join(f"{r[0]} ({r[1]})" for r in rows) if rows else "")
        + ". Decided at 07:00; this note only reads them.")
    return out


# ---------------------------------------------------------------------------
# The payload
# ---------------------------------------------------------------------------
def build(day: Optional[str] = None, as_of: Optional[str] = None, db_path=None,
          run_id: Optional[str] = None, register_db=None, universe=None) -> dict:
    from altdata import session                                 # noqa: PLC0415
    day = day or session.session_date()
    cutoff = as_of or session.utc_iso(timespec="seconds")
    cfg = nc.config()
    ecfg = cfg.get("evening") or {}
    sunday = is_sunday(day)
    ref = since_day(day)
    g = gauge(ref, cutoff, db_path)
    blocks = []
    b_sun = sunday_open_block(ref, day, cutoff, db_path, g) if sunday else None
    b1 = futures_block(day, ref, cutoff, db_path, g)
    b2 = earnings_block(day, cutoff, db_path, universe) if not sunday else None
    b3 = asia_block(day, cutoff, db_path)
    b4 = currencies_block(day, ref, cutoff, db_path)
    b5 = crypto_block(ref, cutoff, db_path)
    mx = int(ecfg.get("news_max") or 8)
    if sunday:
        new = nc.news(nc.et(day, "05:00"), cutoff, max_n=mx, db_path=db_path)
        old = nc.news(nc.et(ref, "16:45"), cutoff, until=nc.et(day, "05:00"), max_n=mx,
                      db_path=db_path)
        nb = [{"title": "News since the 05:00 Weekly", "as_of": nc.hm_et(cutoff),
               "lines": nc.news_lines(new, "No stored item published since 05:00.")},
              {"title": "News from Friday 16:45 to Sunday 05:00", "as_of": nc.hm_et(cutoff),
               "lines": nc.news_lines(old, "No stored item published in the window.") + [
                   "Split by each source's stated publication time. Nothing ingests news "
                   "between Friday's 16:10 pass and this note's pass, so every item here "
                   "was ingested at 21:30 tonight."]}]
        news_ = {"since_weekly": new, "weekend": old}
    else:
        nw = nc.news(nc.et(day, ecfg.get("news_after") or "16:45"), cutoff, max_n=mx,
                     db_path=db_path)
        nb = [{"title": "News since 16:45", "as_of": nc.hm_et(cutoff),
               "lines": nc.news_lines(nw, "No stored item published since 16:45.")}]
        news_ = {"since_close": nw}
    b7 = book_d_block(day, cutoff, register_db)
    blocks = [b for b in (b_sun, b1, b2, b3, b4, b5, *nb, b7) if b]
    t = {k: float(ecfg.get(k) or 0) for k in ("es_nq_pct", "usdjpy_pct", "asia_pct")}
    fm = b1["moves"]
    gate = {
        "earnings_night": bool(b2 and b2["names"]),
        "futures": any(abs((fm.get(i) or {}).get("move_16_pct") or 0) > t["es_nq_pct"]
                       for i in ("es", "nq")),
        "usdjpy": abs((b4["moves"].get("usdjpy") or {}).get("move_pct") or 0) > t["usdjpy_pct"],
        "asia": any(abs(m.get("move_pct") or 0) > t["asia_pct"] for m in b3["moves"].values()),
        "hooks": any(h["open"] for h in b4["hooks"]),
        "sunday": sunday}
    budget_key = "evening_note_sunday" if sunday else "evening_note"
    return {"report": REPORT, "session": day, "next_session": _next(day), "reference": ref,
            "sunday": sunday, "as_of": cutoff, "run_id": run_id, "blocks": blocks,
            "futures": fm, "sunday_open": (b_sun or {}).get("moves"),
            "usdjpy_gap_pct": (b_sun or {}).get("usdjpy_gap_pct"),
            "earnings": (b2 or {}).get("names") or [], "asia": b3["moves"],
            "currencies": b4["moves"], "fix": b4.get("fix"), "crypto": b5["moves"],
            "news": news_, "book_d": b7.get("drafts") or [], "gate": gate,
            "gate_open": any(gate.values()), "thresholds": t,
            "budget": (cfg.get("budget") or {}).get(budget_key) or {"words": 150, "charts": 1},
            "reading_target_minutes": (cfg.get("reading") or {}).get(budget_key, 1)}


def _next(day: str) -> Optional[str]:
    from altdata import es_block                                # noqa: PLC0415
    try:
        return es_block.next_trading_session(day).isoformat()
    except Exception:                                           # noqa: BLE001
        return None


def subject_of(p: dict) -> tuple[str, str]:
    es = (p.get("futures") or {}).get("es") or {}
    if p["sunday"]:
        so = (p.get("sunday_open") or {}).get("es") or {}
        n = len(((p.get("news") or {}).get("since_weekly") or {}).get("items") or [])
        lead = (f"ES {so['since_pct']:+.1f}% vs Friday" if so.get("since_pct") is not None
                else "ES not stored")
        return (f"Sunday night: {lead}; {n} items since the Weekly",
                "Sunday night: the futures open")
    if not p["gate_open"]:
        return "Evening note: quiet", "Evening note: quiet"
    parts = []
    if es.get("move_16_pct") is not None:
        parts.append(f"ES {es['move_16_pct']:+.1f}% since 16:00")
    big = [e for e in p.get("earnings") or [] if e.get("ah_move_pct") is not None]
    if big:
        e = max(big, key=lambda x: abs(x["ah_move_pct"]))
        parts.append(f"{e['symbol']} {e['ah_move_pct']:+.1f}% after hours")
    j = (p.get("currencies") or {}).get("usdjpy") or {}
    if p["gate"].get("usdjpy") and j.get("move_pct") is not None:
        parts.append(f"dollar-yen {j['move_pct']:+.1f}%")
    return "Evening note: " + "; ".join(parts or ["a gate opened"]), "Evening note: a gate opened"


SYSTEM_EXTRA = ("The evening note covers 16:45 to 21:30 and has no rights over any book: "
                "never suggest an action. On Sunday it covers the futures open against "
                "Friday and the weekend's news, what is new since the 05:00 Weekly first; say "
                "for each item whether the futures open is consistent with it, as a "
                "description, never a cause.")


def render(p: dict, prose_text: Optional[str], chart_src: Optional[str]) -> tuple[str, str]:
    intro = [f"{'Sunday night' if p['sunday'] else 'Evening'} {p['session']}, ahead of "
             f"{p.get('next_session')}; as of {nc.hm_et(p['as_of'])}. No rights over any book.",
             "Sources: Yahoo 5-minute bars (delayed by up to 15 minutes; Asia's indices "
             "by up to 20); the CFETS fix; the agencies' feeds; the voices scan."]
    if not p["gate_open"]:
        intro.append(DEFAULT_LINE)
    footer = [f"Reading target {p['reading_target_minutes']} minutes; estimated "
              f"{p.get('reading_minutes', 'n/a')}. Prose: {p.get('prose_state')}."]
    title = f"{'Sunday night' if p['sunday'] else 'Evening note'}, {p['session']}"
    return (nc.page(title, intro, p["blocks"], prose_text, footer, chart_src),
            nc.text_page(title, intro, p["blocks"], prose_text, footer))


def main(argv=None) -> int:
    from altdata import session                                 # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m daily_cascade.evening_note")
    ap.add_argument("--date")
    ap.add_argument("--as-of")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--email", action="store_true")
    ap.add_argument("--archive-dir")
    ap.add_argument("--db")
    ap.add_argument("--no-narrative", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO if a.verbose else logging.WARNING)
    day = a.date or session.session_date()
    cfg = nc.config()
    dry = nc.is_dry(day, a.dry_run, cfg)
    email = a.email or (dry and not a.dry_run)
    archive_dir = nc.dryrun_dir(a.archive_dir, dry)
    run_id = session.new_run_id(REPORT)
    p = build(day, a.as_of, a.db, run_id)
    return finish(p, cfg, dry=dry, email=email, archive_dir=archive_dir,
                  narrative=not a.no_narrative, run_id=run_id, db_path=a.db)


def finish(p: dict, cfg: dict, *, dry: bool, email: bool, archive_dir, narrative: bool,
           run_id: str, prose_fn=None, db_path=None) -> int:
    budget = p["budget"]
    pr = {"state": "gate closed", "text": None, "reason": "no gate opened"}
    if p["gate_open"] and narrative:
        pr = (prose_fn or nc.prose)(p, report=REPORT, words_cap=int(budget["words"]),
                                    run_id=run_id, extra=SYSTEM_EXTRA,
                                    model=(cfg.get("evening") or {}).get("model"))
    elif p["gate_open"]:
        pr = {"state": "skipped", "text": None, "reason": "--no-narrative"}
    p["prose_state"] = pr["state"] + (f" ({pr['reason']})" if pr.get("reason") else "")
    ch = None
    if int(budget.get("charts") or 0) >= 1 and (p["sunday"] or p["gate_open"]):
        start = nc.et(p["session"], "18:00") if p["sunday"] else nc.et(p["session"], "16:00")
        bars = nc.read_bars("es", start, nc.parse(p["as_of"]), p["as_of"], db_path)
        ch = nc.chart(bars, f"ES since {'the 18:00 reopen' if p['sunday'] else '16:00'} "
                      "(5-minute)", f"evening_note_{p['session']}_es")
    p["reading_minutes"] = nc.reading_minutes(p["blocks"], pr.get("text"), 1 if ch else 0)
    subj, fb = subject_of(p)
    subj, audited = nc.subject(subj, p, fb)
    p["subject_audited"] = audited
    name = f"evening_note_{p['session']}.html"
    mail, text = render(p, pr.get("text"), f"cid:{ch['cid']}" if ch else None)
    arch, _ = render(p, pr.get("text"), nc.data_uri(ch["png"]) if ch else None)
    if pr["state"] not in ("published", "gate closed", "skipped"):
        from altdata import withheld_log                         # noqa: PLC0415
        withheld_log.record(REPORT, name, [("prose", f"{pr['state']}: {pr['reason']}")],
                            archive_dir)
    p.pop("budget", None)
    out = nc.ship(name=name, subject_line=subj, payload=p, mail_html=mail, archive_html=arch,
                  text=text, dry=dry, email=email, archive_dir=archive_dir, chart_obj=ch)
    print(f"evening note {p['session']}: {out.get('delivery')} -> {out.get('archive_path')}; "
          f"subject {out.get('subject')!r}; prose {p['prose_state']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
