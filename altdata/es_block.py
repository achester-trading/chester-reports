"""
The standing three-timeframe ES block: the numbers. (ST-R6.45a, b and e;
Batch 6 item 45, ruled 15 Oct 2026; docs/briefs/st-r6-45-notes.md)

    from altdata import es_block
    blk = es_block.compute(store, "2026-10-16", as_of=cutoff, slot="morning")
    es_block.record(blk, lean, run_id, db_path=...)          # the ledger
    es_block.resolve_due(cutoff, db_path=...)                # its outcomes

    python -m altdata.es_block show --session 2026-10-16 [--slot morning|close]
    python -m altdata.es_block ledger [--sessions 5]

THREE WINDOWS, READ AGAINST EACH OTHER. session (the futures day's 5-minute
bars, 18:00 ET the evening before to 17:00 ET, or so far), swing (five sessions
on 2-hour bars built from the 5-minute bars) and position (63 sessions on daily
bars built from the same table). Each carries the price, VWAP (session) or a
trend line (swing, position), VP-1's POC, value area and nodes
(altdata/volume_profile.py -- this module never bins volume itself), MACD
(12,26,9) and money flow (14). The settings are config/es_block.yaml.

READS ONLY THE BARS TABLE, AS OF. Every bar comes through BarStore.read(as_of=)
-- the 06:45 overnight pull and the 16:10 bars feed write it; a report never
fetches (30.4). A window whose bars fall short of the bars table's
complete_share is absent with its reason, as VP-1's are.

THE CONTRACT. ES=F is Yahoo's continuous front month, unadjusted. The contract
in force is CME's rule (config contract) unless a pull recorded what Yahoo
reported (es_contract), and a window that spans a switch is shifted across it
by the gap at the switch (config roll_adjust), printed beside it.

THE LEDGER (45e). Each printed level and the read's lean, logged with the next
session's outcome -- held, broke or untested; resolved or unresolved -- by the
declared rules in config ledger. Report only: nothing here generates a setup.
The dealer levels in ES (45c) wait for the 6b engine.
"""

from __future__ import annotations

import datetime as dt
import logging
import math
import sqlite3
from pathlib import Path
from typing import Any, Optional

import yaml

from . import bars as bars_mod, session
from . import volume_profile as vp

log = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "config" / "es_block.yaml"

DEALER_PENDING = "dealer levels in ES: after the 6b engine"
SLOTS = ("morning", "close")
WINDOW_IDS = ("session", "swing", "position")

SCHEMA = """
CREATE TABLE IF NOT EXISTS es_contract (
    session        TEXT NOT NULL,     -- the futures session the pull was for
    recorded_at    TEXT NOT NULL,     -- UTC, the pull
    rule_contract  TEXT NOT NULL,     -- CME's rule: ESZ6
    roll_date      TEXT NOT NULL,     -- the rule contract's roll date
    yahoo_contract TEXT,              -- what Yahoo reported for ES=F, or NULL
    UNIQUE (session, recorded_at)
);
CREATE TABLE IF NOT EXISTS es_ledger (
    id             INTEGER PRIMARY KEY,
    printed_session TEXT NOT NULL,    -- the session the block was printed for
    slot           TEXT NOT NULL,     -- morning | close
    run_id         TEXT,
    kind           TEXT NOT NULL,     -- level | lean
    label          TEXT NOT NULL,     -- the level's sources, or 'lean'
    level          REAL,              -- the level (ES points), NULL for a lean
    side           TEXT,              -- above | below the price at print
    ref_price      REAL NOT NULL,     -- the last price at print
    lean           TEXT,              -- up | down | none (lean rows)
    contract       TEXT,
    target_session TEXT NOT NULL,     -- the session the outcome is read from
    printed_at     TEXT NOT NULL,
    outcome        TEXT,              -- held | broke | untested | resolved | unresolved | not_scored
    detail         TEXT,
    scored_at      TEXT,
    UNIQUE (printed_session, slot, kind, label)
);
"""


def load_config(path: Optional[Path] = None) -> dict:
    with open(path or CONFIG_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _d(x: Any) -> dt.date:
    return x if isinstance(x, dt.date) else dt.date.fromisoformat(str(x)[:10])


def next_trading_session(day: Any) -> dt.date:
    d = _d(day)
    for _ in range(10):
        d += dt.timedelta(days=1)
        if session.is_trading_session(d):
            return d
    raise RuntimeError(f"no trading session in the 10 days after {day}")


# ---------------------------------------------------------------------------
# The contract in force (45a)
# ---------------------------------------------------------------------------
def _quarterlies(year: int, cfg: dict) -> list[tuple[int, int, str]]:
    months = {int(k): str(v) for k, v in (cfg.get("contract") or {}).get(
        "months", {3: "H", 6: "M", 9: "U", 12: "Z"}).items()}
    return [(year, m, months[m]) for m in sorted(months)]


def contract_for(day: Any, cfg: Optional[dict] = None) -> dict:
    """The contract CME's rule puts in force for the futures session `day`:
    the first quarterly whose roll date is after it. {contract, expiry,
    roll_date, next, next_roll_date}."""
    cfg = cfg or load_config()
    back = int((cfg.get("contract") or {}).get("roll_days_before_expiry", 8))
    d = _d(day)
    seq = []
    for y in (d.year, d.year + 1):
        for yy, m, code in _quarterlies(y, cfg):
            exp = session._third_friday(yy, m)                    # noqa: SLF001
            seq.append({"contract": f"ES{code}{yy % 10}", "expiry": exp.isoformat(),
                        "roll_date": (exp - dt.timedelta(days=back)).isoformat()})
    for i, c in enumerate(seq):
        if d.isoformat() < c["roll_date"]:
            nxt = seq[i + 1]
            return {**c, "next": nxt["contract"], "next_roll_date": nxt["roll_date"]}
    raise RuntimeError(f"no ES contract for {d}")                  # unreachable


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def record_contract(conn: sqlite3.Connection, day: str, yahoo: Optional[str],
                    recorded_at: str, cfg: Optional[dict] = None) -> dict:
    """The pull's record of the contract in force (the overnight pull writes it)."""
    ensure_schema(conn)
    c = contract_for(day, cfg)
    conn.execute("INSERT OR IGNORE INTO es_contract VALUES (?,?,?,?,?)",
                 (day, recorded_at, c["contract"], c["roll_date"], yahoo))
    conn.commit()
    return {**c, "yahoo_contract": yahoo}


def _normalise_yahoo(s: Optional[str]) -> Optional[str]:
    """ESZ26.CME / ESZ6 / ESZ2026 -> ESZ6. None for anything else."""
    if not s:
        return None
    t = str(s).upper().split(".")[0]
    if len(t) >= 4 and t.startswith("ES") and t[2] in "HMUZ" and t[3:].isdigit():
        return f"ES{t[2]}{t[3:][-1]}"
    return None


def yahoo_contracts(conn: Optional[sqlite3.Connection], sessions: list[str],
                    as_of: Optional[str]) -> dict[str, str]:
    """{session: Yahoo's reported contract}, from pulls recorded by `as_of`."""
    if conn is None:
        return {}
    have = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND "
                        "name='es_contract'").fetchone()
    if not have or not sessions:
        return {}
    q = ("SELECT session, yahoo_contract FROM es_contract WHERE yahoo_contract IS NOT "
         "NULL AND session >= ? AND session <= ?")
    args: list[Any] = [min(sessions), max(sessions)]
    if as_of:
        q += " AND recorded_at <= ?"
        args.append(as_of)
    out = {}
    for s, y in conn.execute(q + " ORDER BY recorded_at", args):
        n = _normalise_yahoo(y)
        if n:
            out[s] = n
    return out


def contracts_of(sessions: list[str], conn=None, as_of: Optional[str] = None,
                 cfg: Optional[dict] = None) -> dict[str, dict]:
    """{session: {contract, source}}: Yahoo's report where a pull recorded one,
    CME's rule otherwise."""
    yh = yahoo_contracts(conn, sessions, as_of)
    out = {}
    for s in sessions:
        if s in yh:
            out[s] = {"contract": yh[s], "source": "yahoo"}
        else:
            out[s] = {"contract": contract_for(s, cfg)["contract"], "source": "rule"}
    return out


# ---------------------------------------------------------------------------
# Bars: read, roll-adjust, aggregate
# ---------------------------------------------------------------------------
def _expected_until(first: str, last: str, expected: int, as_of: Optional[str]) -> int:
    """The 5-minute bars a session should hold by `as_of`: its full count, or
    the bars that had closed by then."""
    if not as_of:
        return expected
    a = dt.datetime.fromisoformat(first)
    cut = dt.datetime.fromisoformat(as_of.replace("Z", "+00:00"))
    if cut.tzinfo is None:
        cut = cut.replace(tzinfo=dt.timezone.utc)
    done = int((cut - a).total_seconds() // 300)
    return max(0, min(expected, done))


def read_sessions(store, sessions: list[str], as_of: Optional[str],
                  instrument: str = "es") -> list[dict]:
    """[{session, bars, n, expected}] through the bars table's as-of read."""
    out = []
    for s in sessions:
        first, last, expected = bars_mod.session_window(instrument, s)
        rows = store.read(instrument, "5m", first, last, as_of)
        out.append({"session": s, "bars": rows, "n": len(rows),
                    "expected": _expected_until(first, last, expected, as_of)})
    return out


def roll_adjust(per: list[dict], contracts: dict[str, dict]) -> tuple[list[dict], list[dict]]:
    """Shift bars before each contract switch by the gap at it (additive): the
    first bar after the switch opens at the new contract's price, so the gap
    between it and the last bar before it is the calendar spread. Returns the
    sessions with adjusted copies of their bars, and the rolls."""
    rolls = []
    shift = [0.0] * len(per)
    for i in range(1, len(per)):
        a, b = per[i - 1], per[i]
        ca = contracts.get(a["session"], {}).get("contract")
        cb = contracts.get(b["session"], {}).get("contract")
        if not ca or not cb or ca == cb:
            continue
        before = next((x for x in reversed(per[:i]) if x["bars"]), None)
        if not before or not b["bars"]:
            rolls.append({"session": b["session"], "from": ca, "to": cb, "gap": None,
                          "note": "no bars on one side of the switch: not adjusted"})
            continue
        gap = float(b["bars"][0]["open"]) - float(before["bars"][-1]["close"])
        for j in range(i):
            shift[j] += gap
        rolls.append({"session": b["session"], "from": ca, "to": cb,
                      "gap": round(gap, 2)})
    out = []
    for k, x in zip(shift, per):
        if k:
            bars = [{**r, **{f: float(r[f]) + k for f in ("open", "high", "low", "close")}}
                    for r in x["bars"]]
        else:
            bars = x["bars"]
        out.append({**x, "bars": bars})
    return out, rolls


def buckets(bars: list[dict], hours: int, session_day: str) -> list[dict]:
    """The session's 5-minute bars as `hours`-hour bars anchored at 18:00 ET the
    evening before (the futures day's open); the day's last bucket is short."""
    if not bars:
        return []
    tz = session._eastern_tz()                                    # noqa: SLF001
    start = dt.datetime.combine(_d(session_day) - dt.timedelta(days=1), dt.time(18, 0),
                                tzinfo=tz)
    groups: dict[int, list[dict]] = {}
    for r in bars:
        t = dt.datetime.fromisoformat(r["observed_at"])
        groups.setdefault(int((t - start).total_seconds() // (hours * 3600)), []).append(r)
    out = []
    for k in sorted(groups):
        g = groups[k]
        out.append(_ohlcv(g, (start + dt.timedelta(hours=hours * k)).astimezone(
            dt.timezone.utc).isoformat()))
    return out


def _ohlcv(g: list[dict], observed_at: str) -> dict:
    vol = [r.get("volume") for r in g]
    return {"observed_at": observed_at, "open": float(g[0]["open"]),
            "high": max(float(r["high"]) for r in g),
            "low": min(float(r["low"]) for r in g),
            "close": float(g[-1]["close"]),
            "volume": None if any(v is None for v in vol) else float(sum(vol)),
            "available_at": max(str(r["available_at"]) for r in g),
            "source": g[0].get("source")}


def daily_bar(x: dict) -> Optional[dict]:
    return _ohlcv(x["bars"], x["session"]) if x["bars"] else None


# ---------------------------------------------------------------------------
# Indicators: pure
# ---------------------------------------------------------------------------
def ema(vals: list[float], n: int) -> list[Optional[float]]:
    """Exponential mean, seeded with the simple mean of the first n values."""
    out: list[Optional[float]] = [None] * len(vals)
    if len(vals) < n:
        return out
    k = 2.0 / (n + 1)
    e = sum(vals[:n]) / n
    out[n - 1] = e
    for i in range(n, len(vals)):
        e = vals[i] * k + e * (1 - k)
        out[i] = e
    return out


def macd(closes: list[float], fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    """MACD line, signal and histogram at the last bar, and the histogram one
    bar earlier (to say whether it is turning)."""
    need = slow + signal - 1
    if len(closes) < need:
        return {"absent": f"MACD needs {need} bars (n={len(closes)})"}
    f, s = ema(closes, fast), ema(closes, slow)
    line = [a - b for a, b in zip(f, s) if a is not None and b is not None]
    sig = ema(line, signal)
    hist = [m - g for m, g in zip(line, sig) if g is not None]
    return {"macd": line[-1], "signal": sig[-1], "hist": hist[-1],
            "hist_prev": hist[-2] if len(hist) > 1 else None, "n": len(closes)}


def money_flow(bars: list[dict], period: int = 14) -> dict:
    """The money flow index over the last `period` bars (needs period + 1)."""
    if len(bars) < period + 1:
        return {"absent": f"money flow needs {period + 1} bars (n={len(bars)})"}
    if any(b.get("volume") is None for b in bars[-(period + 1):]):
        return {"absent": "volume not stored for every bar"}
    tp = [(float(b["high"]) + float(b["low"]) + float(b["close"])) / 3 for b in bars]
    pos = neg = 0.0
    for i in range(len(bars) - period, len(bars)):
        flow = tp[i] * float(bars[i]["volume"])
        if tp[i] > tp[i - 1]:
            pos += flow
        elif tp[i] < tp[i - 1]:
            neg += flow
    if pos + neg == 0:
        return {"value": 50.0, "n": len(bars)}
    return {"value": 100.0 if neg == 0 else 100.0 - 100.0 / (1.0 + pos / neg),
            "n": len(bars)}


def vwap(bars: list[dict]) -> Optional[float]:
    num = den = 0.0
    for b in bars:
        v = b.get("volume")
        if not v:
            continue
        num += (float(b["high"]) + float(b["low"]) + float(b["close"])) / 3 * float(v)
        den += float(v)
    return num / den if den else None


def trend(closes: list[float]) -> dict:
    """Least-squares line through the closes, one point per bar."""
    n = len(closes)
    if n < 3:
        return {"absent": f"a trend line needs 3 bars (n={n})"}
    xm, ym = (n - 1) / 2, sum(closes) / n
    sxx = sum((i - xm) ** 2 for i in range(n))
    sxy = sum((i - xm) * (y - ym) for i, y in enumerate(closes))
    slope = sxy / sxx
    fit = [ym + slope * (i - xm) for i in range(n)]
    sst = sum((y - ym) ** 2 for y in closes)
    sse = sum((y - f) ** 2 for y, f in zip(closes, fit))
    return {"slope": slope, "value": fit[-1], "r2": (1 - sse / sst) if sst else 1.0,
            "n": n}


# ---------------------------------------------------------------------------
# The windows (45b)
# ---------------------------------------------------------------------------
def _sessions_back(day: Any, n: int) -> list[str]:
    return vp.trailing_sessions(day, n)


def _complete(per: list[dict], share: float) -> Optional[str]:
    n = sum(x["n"] for x in per)
    exp = sum(x["expected"] for x in per)
    if not exp:
        return "no bars expected in the window by the cutoff"
    if n / exp < share:
        short = [f"{x['session']} ({x['n']} of {x['expected']})" for x in per
                 if not x["expected"] or x["n"] / x["expected"] < share]
        return f"bars incomplete (n={n} of {exp})" + (
            f"; below the share: {', '.join(short)}" if short else "")
    srcs = sorted({str(b.get("source") or "unknown") for x in per for b in x["bars"]})
    if len(srcs) > 1:
        return f"bars from more than one source ({', '.join(srcs)}); never mixed"
    return None


def _ind(cfg: dict) -> tuple[dict, int]:
    m = cfg.get("macd") or {}
    return ({"fast": int(m.get("fast", 12)), "slow": int(m.get("slow", 26)),
             "signal": int(m.get("signal", 9))},
            int((cfg.get("money_flow") or {}).get("period", 14)))


def _r(x: Optional[float], dp: int = 2) -> Optional[float]:
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(x, dp)


def _ind_block(bars: list[dict], cfg: dict) -> dict:
    m, mf = _ind(cfg)
    mc = macd([float(b["close"]) for b in bars], **m)
    mfi = money_flow(bars, mf)
    out = {"macd": ({k: _r(v) if isinstance(v, float) else v for k, v in mc.items()})}
    out["money_flow"] = (_r(mfi["value"], 1) if "value" in mfi else None)
    if "absent" in mfi:
        out["money_flow_absent"] = mfi["absent"]
    return out


def _profile(bars: list[dict], daily: bool, vcfg: dict) -> dict:
    if daily:
        return vp.summary(vp.daily_profile(bars, vcfg))
    return vp.summary(vp.profile(bars, float((vcfg.get("bin_bps") or {}).get(
        "five_minute", 5)), vcfg))


def session_window(store, day: str, as_of: Optional[str], cfg: dict, vcfg: dict,
                   share: float, conn=None) -> dict:
    """The futures day's 5-minute bars (so far), with a warmup session before it
    for the indicators."""
    warm = int((cfg.get("warmup_sessions") or {}).get("session", 1))
    sessions = _sessions_back(day, 1 + warm)
    per = read_sessions(store, sessions, as_of, cfg.get("instrument", "es"))
    per, rolls = roll_adjust(per, contracts_of(sessions, conn, as_of, cfg))
    cur = per[-1]
    why = _complete([cur], share)
    if why:
        return {"window": "session", "absent": why, "sessions": [day]}
    bars = cur["bars"]
    allb = [b for x in per if x["session"] != day and _complete([x], share) is None
            for b in x["bars"]] + bars
    out = {"window": "session", "sessions": [day], "n_bars": len(bars),
           "open": _r(float(bars[0]["open"])), "high": _r(max(float(b["high"]) for b in bars)),
           "low": _r(min(float(b["low"]) for b in bars)), "last": _r(float(bars[-1]["close"])),
           "last_bar_at": bars[-1]["observed_at"], "vwap": _r(vwap(bars)),
           "profile": _profile(bars, False, vcfg), **_ind_block(allb, cfg)}
    out["change"] = _r(out["last"] - out["open"])
    if rolls:
        out["rolls"] = rolls
    return out


def swing_window(store, day: str, as_of: Optional[str], cfg: dict, vcfg: dict,
                 share: float, conn=None) -> dict:
    w = cfg.get("windows", {}).get("swing", {})
    n, hours = int(w.get("sessions", 5)), int(w.get("bar_hours", 2))
    warm = int((cfg.get("warmup_sessions") or {}).get("swing", 10))
    sessions = _sessions_back(day, n + warm)
    per = read_sessions(store, sessions, as_of, cfg.get("instrument", "es"))
    per, rolls = roll_adjust(per, contracts_of(sessions, conn, as_of, cfg))
    win = per[-n:]
    why = _complete(win, share)
    if why:
        return {"window": "swing", "absent": why, "sessions": [x["session"] for x in win]}
    two = [b for x in win for b in buckets(x["bars"], hours, x["session"])]
    warm2 = [b for x in per[:-n] if x["bars"] and _complete([x], share) is None
             for b in buckets(x["bars"], hours, x["session"])]
    five = [b for x in win for b in x["bars"]]
    out = {"window": "swing", "sessions": [x["session"] for x in win],
           "bar_hours": hours, "n_bars": len(two),
           "open": _r(two[0]["open"]), "high": _r(max(b["high"] for b in two)),
           "low": _r(min(b["low"] for b in two)), "last": _r(two[-1]["close"]),
           "trend": {k: (_r(v, 3) if isinstance(v, float) else v)
                     for k, v in trend([b["close"] for b in two]).items()},
           # The profile from the 5-minute bars beneath the 2-hour bars: VP-1's
           # rule, never a coarser one.
           "profile": _profile(five, False, vcfg), **_ind_block(warm2 + two, cfg)}
    out["change"] = _r(out["last"] - out["open"])
    rolls = [r for r in rolls if r["session"] in out["sessions"]]
    if rolls:
        out["rolls"] = rolls
    return out


def position_window(store, day: str, as_of: Optional[str], cfg: dict, vcfg: dict,
                    share: float, conn=None) -> dict:
    w = cfg.get("windows", {}).get("position", {})
    n, need = int(w.get("sessions", 63)), int(w.get("min_sessions", 35))
    sessions = _sessions_back(day, n)
    per = read_sessions(store, sessions, as_of, cfg.get("instrument", "es"))
    per, rolls = roll_adjust(per, contracts_of(sessions, conn, as_of, cfg))
    # A session counts when its own bars reach the share; the rest are named.
    kept = [x for x in per if x["expected"] and _complete([x], share) is None]
    dropped = [x["session"] for x in per if x not in kept and x["n"]]
    daily = [daily_bar(x) for x in kept]
    daily = [b for b in daily if b]
    if len(daily) < need:
        return {"window": "position", "absent": f"{len(daily)} complete sessions of "
                f"{n} stored; the position window needs {need}",
                "n_sessions": len(daily), "sessions_wanted": n}
    out = {"window": "position", "n_sessions": len(daily), "sessions_wanted": n,
           "first_session": daily[0]["observed_at"], "n_bars": len(daily),
           "open": _r(daily[0]["open"]), "high": _r(max(b["high"] for b in daily)),
           "low": _r(min(b["low"] for b in daily)), "last": _r(daily[-1]["close"]),
           "trend": {k: (_r(v, 3) if isinstance(v, float) else v)
                     for k, v in trend([b["close"] for b in daily]).items()},
           "profile": _profile(daily, True, vcfg), **_ind_block(daily, cfg)}
    out["change"] = _r(out["last"] - out["open"])
    if dropped:
        out["sessions_dropped"] = dropped
    if rolls:
        out["rolls"] = rolls
    return out


def prior_session_reference(store, day: str, as_of: Optional[str], cfg: dict,
                            vcfg: dict, share: float, conn=None) -> dict:
    """At 07:00: the prior FULL futures session's POC and value area, as
    reference levels for the day (verify item 11, as proposed)."""
    prev = session.previous_trading_session(_d(day)).isoformat()
    per = read_sessions(store, [prev, day], as_of, cfg.get("instrument", "es"))
    per, rolls = roll_adjust(per, contracts_of([prev, day], conn, as_of, cfg))
    x = per[0]
    why = _complete([x], share)
    if why:
        return {"window": "prior_session", "absent": why, "sessions": [prev]}
    out = {"window": "prior_session", "sessions": [prev],
           "profile": _profile(x["bars"], False, vcfg),
           "last": _r(float(x["bars"][-1]["close"]))}
    if rolls:
        out["rolls"] = rolls
    return out


# ---------------------------------------------------------------------------
# The levels that matter
# ---------------------------------------------------------------------------
def _candidates(windows: dict) -> list[tuple[float, str]]:
    out: list[tuple[float, str]] = []
    names = {"session": "session", "swing": "swing", "position": "position",
             "prior_session": "prior session"}
    for wid, w in windows.items():
        if not w or w.get("absent"):
            continue
        nm = names.get(wid, wid)
        p = w.get("profile") or {}
        if not p.get("absent"):
            for f, lab in (("poc", "POC"), ("vah", "value-area high"),
                           ("val", "value-area low")):
                if p.get(f) is not None:
                    out.append((float(p[f]), f"{nm} {lab}"))
            if wid in ("swing", "position"):
                for h in p.get("hvn") or []:
                    out.append((float(h), f"{nm} high-volume node"))
                for lv in p.get("lvn") or []:
                    out.append((float(lv), f"{nm} low-volume node"))
        if w.get("vwap") is not None:
            out.append((float(w["vwap"]), f"{nm} VWAP"))
        t = w.get("trend") or {}
        if t.get("value") is not None:
            out.append((float(t["value"]), f"{nm} trend line"))
        # The swing and position ranges' edges: at a new high the levels above
        # would otherwise be none.
        if wid in ("swing", "position"):
            for f in ("high", "low"):
                if w.get(f) is not None:
                    out.append((float(w[f]), f"{nm} {f}"))
    return out


def levels(windows: dict, last: Optional[float], cfg: dict) -> dict:
    """The nearest `above` and `below` levels to the last price, merged when
    within merge_points, each with every source that put it there."""
    lc = cfg.get("levels") or {}
    n_up, n_dn = int(lc.get("above", 3)), int(lc.get("below", 3))
    tol = float(lc.get("merge_points", 2.0))
    if last is None:
        return {"above": [], "below": []}
    cands = sorted(_candidates(windows))
    merged: list[dict] = []
    for px, lab in cands:
        if merged and px - merged[-1]["_hi"] <= tol:
            g = merged[-1]
            g["_px"].append(px)
            g["_hi"] = px
            if lab not in g["sources"]:
                g["sources"].append(lab)
        else:
            merged.append({"_px": [px], "_hi": px, "sources": [lab]})
    rows = []
    for g in merged:
        px = round(sum(g["_px"]) / len(g["_px"]), 2)
        rows.append({"price": px, "sources": g["sources"],
                     "label": " / ".join(g["sources"]),
                     "distance": round(px - last, 2),
                     "side": "above" if px > last else "below"})
    above = sorted([r for r in rows if r["side"] == "above"], key=lambda r: r["price"])
    below = sorted([r for r in rows if r["side"] == "below"], key=lambda r: -r["price"])
    return {"above": above[:n_up], "below": below[:n_dn]}


# ---------------------------------------------------------------------------
# The block
# ---------------------------------------------------------------------------
def compute(store, day: Any, as_of: Optional[str] = None, slot: str = "close",
            conn: Optional[sqlite3.Connection] = None,
            cfg: Optional[dict] = None, vcfg: Optional[dict] = None,
            share: Optional[float] = None) -> dict:
    """The block for the futures session `day`, read as of `as_of`. `slot`
    "morning" adds the prior full session's reference levels. Never raises: a
    fault is an absent block with its reason."""
    cfg = cfg or load_config()
    day = _d(day).isoformat()
    if slot not in SLOTS:
        raise ValueError(f"slot {slot!r} not in {SLOTS}")
    try:
        vcfg = vcfg or vp.load_config()
        share = vp.complete_share() if share is None else share
        if conn is None:
            conn = getattr(store, "conn", None)
        wins = {"session": session_window(store, day, as_of, cfg, vcfg, share, conn),
                "swing": swing_window(store, day, as_of, cfg, vcfg, share, conn),
                "position": position_window(store, day, as_of, cfg, vcfg, share, conn)}
        if slot == "morning":
            wins["prior_session"] = prior_session_reference(store, day, as_of, cfg,
                                                            vcfg, share, conn)
    except Exception as exc:                                    # noqa: BLE001
        log.warning("es block failed", exc_info=True)
        return {"state": "absent", "slot": slot, "session": day, "as_of": as_of,
                "reason": f"{type(exc).__name__}: {exc}"[:200],
                "dealer": DEALER_PENDING}
    sw = wins["session"]
    last = sw.get("last")
    if last is None:
        for wid in ("swing", "position"):
            if not wins[wid].get("absent"):
                last = wins[wid].get("last")
                break
    present = [w for w in WINDOW_IDS if not wins[w].get("absent")]
    c = contracts_of([day], conn, as_of, cfg)[day]
    rule = contract_for(day, cfg)
    out = {"state": "ok" if len(present) == 3 else ("partial" if present else "absent"),
           "slot": slot, "session": day, "as_of": as_of,
           "contract": {"in_force": c["contract"], "source": c["source"],
                        "rule": rule["contract"], "roll_date": rule["roll_date"],
                        "next": rule["next"], "next_roll_date": rule["next_roll_date"],
                        "agree": c["contract"] == rule["contract"]},
           "windows": wins, "last": last, "last_bar_at": sw.get("last_bar_at"),
           "levels": levels(wins, last, cfg),
           "dealer": DEALER_PENDING,
           "reasons": [f"{w}: {wins[w]['absent']}" for w in wins if wins[w].get("absent")]}
    if not present:
        out["reason"] = "; ".join(out["reasons"])
    return out


# ---------------------------------------------------------------------------
# The ledger (45e)
# ---------------------------------------------------------------------------
def target_session(printed_session: str, slot: str) -> str:
    """The session a print is scored on: the session the 07:00 block opens, or
    the one after the 16:45 block's."""
    if slot == "morning":
        return printed_session
    return next_trading_session(printed_session).isoformat()


def record(block: dict, lean: Optional[str], run_id: Optional[str],
           db_path: Optional[str] = None, conn: Optional[sqlite3.Connection] = None,
           printed_at: Optional[str] = None) -> int:
    """Each printed level and the lean, logged unscored. Idempotent per
    (session, slot, kind, label): a re-run of the same edition writes nothing."""
    if block.get("state") == "absent" or block.get("last") is None:
        return 0
    own = conn is None
    conn = conn or sqlite3.connect(str(db_path or bars_mod.observations.DEFAULT_DB))
    try:
        ensure_schema(conn)
        sess, slot = block["session"], block["slot"]
        tgt = target_session(sess, slot)
        at = printed_at or session.utc_iso()
        con = (block.get("contract") or {}).get("in_force")
        rows = []
        for side in ("above", "below"):
            for lv in (block.get("levels") or {}).get(side) or []:
                rows.append((sess, slot, run_id, "level", lv["label"], lv["price"], side,
                             block["last"], None, con, tgt, at))
        # A read that was withheld or not written stated no lean: no lean row,
        # rather than a "none" nobody said.
        if lean in ("up", "down", "none"):
            rows.append((sess, slot, run_id, "lean", "lean", None, None, block["last"],
                         lean, con, tgt, at))
        cur = conn.executemany(
            "INSERT OR IGNORE INTO es_ledger (printed_session, slot, run_id, kind, label,"
            " level, side, ref_price, lean, contract, target_session, printed_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", rows)
        conn.commit()
        return cur.rowcount
    finally:
        if own:
            conn.close()


def _instant(s: str) -> dt.datetime:
    t = dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def after(bars: list[dict], printed_at: Optional[str]) -> list[dict]:
    """The bars that opened at or after the print."""
    if not printed_at:
        return bars
    cut = _instant(printed_at)
    return [b for b in bars if _instant(b["observed_at"]) >= cut]


def since_morning(store, day: str, as_of: Optional[str], last: Optional[float],
                  conn: Optional[sqlite3.Connection] = None,
                  cfg: Optional[dict] = None) -> Optional[dict]:
    """What changed since the 07:00 print (the 16:45 block): the price against
    the morning's, and the morning's levels and lean scored IN MEMORY on the
    bars since -- "so far", never written; the ledger's own outcome is scored
    by resolve_due. None when no 07:00 print was logged."""
    cfg = cfg or load_config()
    conn = conn or getattr(store, "conn", None)
    if conn is None or last is None or not conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='es_ledger'").fetchone():
        return None
    rows = conn.execute("SELECT kind, label, level, side, ref_price, lean, printed_at "
                        "FROM es_ledger WHERE printed_session=? AND slot='morning' "
                        "ORDER BY id", (day,)).fetchall()
    if not rows:
        return None
    bars = after(read_sessions(store, [day], as_of, cfg.get("instrument", "es"))[0]["bars"],
                 rows[0][6])
    ref = float(rows[0][4])
    out: dict[str, Any] = {"ref_price": ref, "change": round(float(last) - ref, 2),
                           "levels": [], "lean": None, "lean_so_far": None}
    for kind, label, level, side, _, lean, _ in rows:
        if kind == "lean":
            out["lean"] = lean
            if bars:
                out["lean_so_far"] = score_lean(bars, lean, ref, cfg)[0]
        elif bars:
            out["levels"].append({"label": label, "level": level, "side": side,
                                  "so_far": score_level(bars, float(level), side, cfg)[0]})
    return out


def score_level(bars: list[dict], level: float, side: str, cfg: dict) -> tuple[str, str]:
    """held | broke | untested, by config ledger's rules."""
    lc = cfg.get("ledger") or {}
    touch, brk = float(lc.get("touch_points", 1.0)), float(lc.get("break_points", 0.5))
    for b in bars:
        c = float(b["close"])
        if (side == "above" and c > level + brk) or (side == "below" and c < level - brk):
            return "broke", f"a 5-minute bar closed at {c:g} at {b['observed_at']}"
    tested = any(float(b["high"]) >= level - touch and float(b["low"]) <= level + touch
                 for b in bars)
    if tested:
        return "held", "tested and no bar closed through it"
    return "untested", "no bar came within the touch distance"


def score_lean(bars: list[dict], lean: str, ref: float, cfg: dict) -> tuple[str, str]:
    """resolved | unresolved | not_scored, by config ledger's rule."""
    if lean not in ("up", "down"):
        return "not_scored", "the lean was none"
    pct = float((cfg.get("ledger") or {}).get("lean_min_move_pct", 0.25))
    last = float(bars[-1]["close"])
    move = (last - ref) / ref * 100
    ok = move >= pct if lean == "up" else move <= -pct
    return ("resolved" if ok else "unresolved",
            f"the session's last bar closed {last:g}, {move:+.2f}% from {ref:g}")


def resolve_due(as_of: str, db_path: Optional[str] = None, store=None,
                conn: Optional[sqlite3.Connection] = None,
                cfg: Optional[dict] = None, share: Optional[float] = None) -> dict:
    """Score every unscored row whose target session has its bars by `as_of`.
    A scored row is never rewritten."""
    cfg = cfg or load_config()
    own_conn, own_store = conn is None, store is None
    conn = conn or sqlite3.connect(str(db_path or bars_mod.observations.DEFAULT_DB))
    store = store or bars_mod.BarStore(db_path)
    share = vp.complete_share() if share is None else share
    out = {"scored": 0, "waiting": 0}
    try:
        ensure_schema(conn)
        today = session.to_eastern(as_of).date().isoformat()
        rows = conn.execute("SELECT id, kind, level, side, ref_price, lean, "
                            "target_session, printed_session, printed_at FROM es_ledger "
                            "WHERE outcome IS NULL AND target_session <= ?",
                            (today,)).fetchall()
        cache: dict[str, Any] = {}
        for rid, kind, level, side, ref, lean, tgt, printed, at in rows:
            if tgt not in cache:
                per = read_sessions(store, [tgt], as_of, cfg.get("instrument", "es"))
                cons = contracts_of([printed, tgt], conn, as_of, cfg)
                same = cons[printed]["contract"] == cons[tgt]["contract"]
                cache[tgt] = (per[0]["bars"] if per[0]["bars"] and same
                              and _complete(per, share) is None else
                              ("roll" if per[0]["bars"] and not same else None))
            bars = cache[tgt]
            if isinstance(bars, list):
                # Only what traded after the print: a 07:00 print is not scored
                # on the overnight bars it was read from.
                bars = after(bars, at)
            if bars == "roll":
                conn.execute("UPDATE es_ledger SET outcome='not_scored', detail=?, "
                             "scored_at=? WHERE id=?",
                             ("the contract rolled between the print and the session",
                              as_of, rid))
                out["scored"] += 1
                continue
            if not bars:
                out["waiting"] += 1
                continue
            if kind == "level":
                oc, det = score_level(bars, float(level), side, cfg)
            else:
                oc, det = score_lean(bars, lean, float(ref), cfg)
            conn.execute("UPDATE es_ledger SET outcome=?, detail=?, scored_at=? "
                         "WHERE id=? AND outcome IS NULL", (oc, det, as_of, rid))
            out["scored"] += 1
        conn.commit()
        return out
    finally:
        if own_conn:
            conn.close()
        if own_store:
            store.close()


def ledger_summary(conn: sqlite3.Connection, sessions: list[str]) -> dict:
    """The ledger over the printed sessions: counts by kind and outcome."""
    have = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND "
                        "name='es_ledger'").fetchone()
    out = {"levels": {}, "leans": {}, "n_prints": 0}
    if not have or not sessions:
        return out
    q = ("SELECT kind, COALESCE(outcome, 'pending'), COUNT(*) FROM es_ledger WHERE "
         "printed_session >= ? AND printed_session <= ? GROUP BY 1, 2")
    for kind, oc, n in conn.execute(q, (min(sessions), max(sessions))):
        out["levels" if kind == "level" else "leans"][oc] = n
    out["n_prints"] = conn.execute(
        "SELECT COUNT(DISTINCT printed_session || slot) FROM es_ledger WHERE "
        "printed_session >= ? AND printed_session <= ?",
        (min(sessions), max(sessions))).fetchone()[0]
    return out


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    import json                                                 # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.es_block")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("show", help="compute the block from the store and print it")
    s.add_argument("--session", default=None)
    s.add_argument("--slot", default="close", choices=SLOTS)
    s.add_argument("--as-of", default=None)
    s.add_argument("--db", default=None)
    lg = sub.add_parser("ledger", help="the ledger's counts over recent sessions")
    lg.add_argument("--sessions", type=int, default=5)
    lg.add_argument("--db", default=None)
    a = ap.parse_args(argv)
    if a.cmd == "show":
        day = a.session or session.last_trading_session().isoformat()
        with bars_mod.BarStore(a.db) as st:
            print(json.dumps(compute(st, day, a.as_of, a.slot), indent=2, default=str))
        return 0
    day = session.last_trading_session()
    sess = vp.trailing_sessions(day, a.sessions)
    conn = sqlite3.connect(str(a.db or bars_mod.observations.DEFAULT_DB))
    try:
        print(json.dumps(ledger_summary(conn, sess), indent=2))
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(_main(sys.argv[1:]))
