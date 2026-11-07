"""
Item 119's event-vol pricing ledger (signal-triage Batch 22, the order's 101)
with Batch 23 item 124f's catalyst-class tags and the T, T+1, T+2 window (Batch
23 section 0, Q3; D-2). A129, 6 Nov 2026.

    python -m altdata.event_vol eod [--date D] [--dry-run]     # record T-1, resolve
    python -m altdata.event_vol show [--date D]
    python -m altdata.event_vol check-chains [--date D]        # V-101a, read-only
    python -m altdata.event_vol edition --source public|store [--date D]

PRE-REGISTERED before this code: docs/ledgers/event-vol-preregistration-2026-11.md,
whose SHA-256 config/event_vol.yaml and tools/validate_item_119.py hold. Every
rule below is that file's; this module applies it and may not change it.

THE EVENTS are the ranked scheduled events of six types (config/event_vol.yaml
`types`): FOMC, CPI, payrolls, refunding, elections (SPY) and the earnings of
the box's 13 (each name its own type, `earnings:<SYM>`).

DAY T is the first session whose close falls after the event; T-1 the session
before. An event whose time is not stored keeps T on its date and its headline
realised move spans T and T+1.

THE IMPLIED MOVE is read from the box's own captured chain only -- the last
capture of the underlying on T-1 at or before the capture cutoff (16:35 ET: the
16:10 capture of the 13, the vendor's 16:31 capture), so a report after the
close never leaks into it -- through Ahead's own helpers (daily_cascade/ahead.py
`straddle_expiry`, `atm_straddle`, `event_move`; Batch 11 item 57): the
at-the-money straddle to the first expiry after the event, over spot. Where that
expiry covers more than one session, the event day's share of variance is
separated by the term structure (`split`). FlashAlpha is never read (the 9 Oct
rule); no vendor figure is stored here.

THE REALISED MOVES are the store's closes: T, T+1 and T+2, signed, and the
headline (absolute, T-1 close to T close; to the T+1 close when the time is not
stored). Resolved when T+2 is stored.

THE PRINT AND THE FLAG (`clause`): Ahead prints the implied move beside the
type's median headline realised move over its resolved rows, "accruing (n=k of
20)" below 20; "cheap event vol" when the separated implied move sits below that
median at n of 20 or more. Ahead only. No pass rule (none stated); nothing here
enters a composite, a dial, the market-state object or the register.

THE LEDGER is `event_vol.ledger` in the observation store, one JSON row per
event (instrument = the event's id), a resolution a new vintage, never an
overwrite; the EOD pass runs `eod` after the vol-event ledger's resolve.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging
import math
import re
import sqlite3
import statistics
import sys
from pathlib import Path
from typing import Any, Optional

import yaml

log = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "config" / "event_vol.yaml"
LEDGER_KEY = "event_vol.ledger"
NO_CHAIN = "no chain"
NOT_SEPARABLE = "not separable"
CAPTURE_CUTOFF_ET = dt.time(16, 35)
CHEAP = "cheap event vol"
ITEM = "event-vol"
PASS_RULE = ("none stated -- the order names no pass rule (\"log-only until there are "
             "at least 20 events of each type\"); this first edition sets none "
             "(pre-registered: docs/ledgers/event-vol-preregistration-2026-11.md)")
RIGHTS = ("The Ahead line (the close and the Weekly) and the \"cheap event vol\" flag, "
          "in Ahead only; log-only until 20 resolved events of a type. Nothing enters a "
          "composite, a dial, the market-state object, a tell, a setup, a size or the "
          "register.")


def config(path: Optional[Path] = None) -> dict:
    with open(path or CONFIG_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def lf_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


# ---------------------------------------------------------------------------
# The events: type, day T, timing
# ---------------------------------------------------------------------------
def earnings_names() -> list[str]:
    from . import config as acfg                                # noqa: PLC0415
    return [s for s in acfg.SINGLE_NAMES]


def classify(title: str, cls: Optional[str] = None,
             cfg: Optional[dict] = None) -> Optional[tuple[str, str]]:
    """(type, underlying) for a ranked event, or None when it is not one of the
    six types. An earnings event of a name outside the 13 is None."""
    cfg = cfg or config()
    t = str(title or "")
    for name, spec in (cfg.get("types") or {}).items():
        if name == "earnings":
            m = re.match(spec["match"], t)
            if m and (cls is None or cls in spec["classes"] or cls == "earnings"):
                sym = m.group(1).upper()
                if sym in earnings_names():
                    return f"earnings:{sym}", sym
            continue
        if cls is not None and cls in (spec.get("classes") or []):
            if re.search(spec["match"], t, re.I) or name in ("fomc", "refunding",
                                                             "election"):
                return name, spec["underlying"]
        elif re.search(spec["match"], t, re.I) and not re.search(r"minutes", t, re.I):
            return name, spec["underlying"]
    return None


def base_type(typ: str) -> str:
    return typ.split(":")[0]


def timing_of(typ: str, time_text: Optional[str] = None,
              cfg: Optional[dict] = None) -> str:
    """"before", "after" or "unknown" against the close. An earnings row's own
    stated time decides it; else the type's."""
    cfg = cfg or config()
    spec = (cfg.get("types") or {}).get(base_type(typ)) or {}
    t = str(time_text or "").strip().lower()
    if base_type(typ) == "earnings":
        if not t or "not captured" in t or t in ("tbd", "unknown"):
            return "unknown"
        if re.search(r"after|amc|post-?market", t):
            return "after"
        if re.search(r"before|bmo|pre-?market", t):
            return "before"
        m = re.match(r"(\d{1,2}):(\d{2})", t)
        if m:
            return "before" if (int(m.group(1)), int(m.group(2))) < (16, 0) else "after"
        return "unknown"
    return str(spec.get("timing") or "unknown")


def next_session(d: dt.date) -> dt.date:
    from . import session                                       # noqa: PLC0415
    x = d
    for _ in range(10):
        x += dt.timedelta(days=1)
        if session.is_trading_session(x):
            return x
    raise RuntimeError(f"no session in the 10 days after {d}")


def day_t(event_date: str, timing: str) -> tuple[str, str]:
    """(T, T-1) as ISO dates (section 2 of the pre-registration)."""
    from . import session                                       # noqa: PLC0415
    d = dt.date.fromisoformat(str(event_date)[:10])
    if timing == "after":
        t = next_session(d)
    elif session.is_trading_session(d):
        t = d
    else:
        t = next_session(d)          # an event on a non-session day: the next session
    return t.isoformat(), session.previous_trading_session(t).isoformat()


# ---------------------------------------------------------------------------
# The implied move (section 3)
# ---------------------------------------------------------------------------
K = math.sqrt(2.0 / math.pi)


def capture_before(day: str, symbol: str, base: Optional[Path] = None,
                   cutoff: dt.time = CAPTURE_CUTOFF_ET) -> Optional[Path]:
    """The last capture of `symbol` in the session directory `day` taken at or
    before `cutoff` ET (the file's own fetched_at), or None."""
    from . import chain_metrics, session                        # noqa: PLC0415
    d = (base or chain_metrics.chain_dir()) / day
    if not d.is_dir():
        return None
    for p in sorted((x for x in d.glob(f"{symbol.upper()}_*.csv")
                     if "_quality" not in x.name), reverse=True):
        try:
            with open(p, encoding="utf-8") as fh:
                fh.readline()
                first = fh.readline().split(",")
            et = session.to_eastern(first[1])
        except Exception:                                       # noqa: BLE001
            continue
        if et.date().isoformat() == day and et.time() <= cutoff:
            return p
    return None


def sessions_covered(t_minus_1: str, expiry: str) -> int:
    from . import session                                       # noqa: PLC0415
    a, b = dt.date.fromisoformat(t_minus_1), dt.date.fromisoformat(str(expiry)[:10])
    n, x = 0, a
    while x < b:
        x += dt.timedelta(days=1)
        if session.is_trading_session(x):
            n += 1
    return n


def split(full_frac: float, t1_days: int, pre: Optional[tuple[float, int]] = None,
          post2: Optional[tuple[float, int]] = None) -> dict:
    """The event day's share of the post-event expiry's variance, on the
    straddle convention (fraction of spot = K x sigma x sqrt(t)), t in calendar
    days over 365 as item 57's `event_move`. `pre` is (fraction, days) of an
    expiry settling after T-1 and before the event; `post2` the next expiry after
    the event's. Returns share and method; share None when not separable."""
    v1 = (full_frac / K) ** 2
    t1 = t1_days / 365.0
    if pre and pre[1] > 0 and t1_days > pre[1]:
        rate = (pre[0] / K) ** 2 / (pre[1] / 365.0)
        ev, method = v1 - rate * t1, "pre-event expiry's variance rate (item 57)"
    elif post2 and post2[1] > t1_days:
        v2, t2 = (post2[0] / K) ** 2, post2[1] / 365.0
        rate = (v2 - v1) / (t2 - t1)
        ev, method = v1 - rate * t1, "two post-event expiries, one base rate"
        if rate <= 0:
            return {"share": None, "method": f"{NOT_SEPARABLE}: the later expiry's "
                                             f"variance is not larger"}
    else:
        return {"share": None, "method": f"{NOT_SEPARABLE}: no second expiry"}
    if ev <= 0 or v1 <= 0:
        return {"share": None, "method": f"{NOT_SEPARABLE}: the event's variance is "
                                         f"not positive"}
    return {"share": round(min(1.0, ev / v1), 4), "method": method}


def implied_from_rows(rows: list[dict], event_date: str, timing: str,
                      t_minus_1: str, time_text: Optional[str] = None) -> dict:
    """The implied move from one capture's rows (section 3). The expiry is
    Ahead's rule as written: strictly after the event's date unless `time_text`
    says the event lands before the open (an 08:30 release), when the event
    date's own expiry counts."""
    from daily_cascade import ahead                             # noqa: PLC0415
    exps = sorted({str(r["expiry"])[:10] for r in rows if r.get("expiry")})
    ex = ahead.straddle_expiry(exps, event_date, time_text)
    if not ex:
        return {"reason": "no expiry after the event in the capture"}
    st = ahead.atm_straddle(rows, ex)
    if not st:
        return {"reason": f"no two-sided at-the-money quote on {ex}"}
    strad, spot = st
    frac = strad / spot
    full = 100.0 * frac
    n_sess = sessions_covered(t_minus_1, ex)
    out: dict[str, Any] = {"expiry": ex, "straddle": round(strad, 4),
                           "spot": round(spot, 4), "full_pct": round(full, 3),
                           "sessions_covered": n_sess}
    if n_sess <= 1:
        out.update(share=1.0, method="one-session expiry", event_pct=round(full, 3))
        return out
    d_ex = (dt.date.fromisoformat(ex) - dt.date.fromisoformat(t_minus_1)).days
    ed = str(event_date)[:10]
    # A pre-event expiry must settle after T-1 and BEFORE the event: earlier than
    # the event's date, or on it only when the event lands after the close.
    pre_ex = max((e for e in exps if t_minus_1 < e < ex
                  and (e < ed or (e == ed and timing == "after"))), default=None)
    pre = None
    if pre_ex:
        ps = ahead.atm_straddle(rows, pre_ex)
        if ps:
            pre = (ps[0] / ps[1], (dt.date.fromisoformat(pre_ex)
                                   - dt.date.fromisoformat(t_minus_1)).days)
    post2 = None
    if pre is None:
        nx = min((e for e in exps if e > ex), default=None)
        if nx:
            ns = ahead.atm_straddle(rows, nx)
            if ns:
                post2 = (ns[0] / ns[1], (dt.date.fromisoformat(nx)
                                         - dt.date.fromisoformat(t_minus_1)).days)
    sp = split(frac, d_ex, pre, post2)
    out.update(sp)
    out["event_pct"] = (round(full * math.sqrt(sp["share"]), 3)
                        if sp["share"] is not None else None)
    if sp["share"] is None:
        out["label"] = "includes non-event days"
    return out


def implied_move(symbol: str, event_date: str, timing: str, t_minus_1: str,
                 base: Optional[Path] = None, time_text: Optional[str] = None) -> dict:
    """The implied move from the T-1 capture of `symbol`, or {"reason": "no
    chain"}."""
    from . import chain_metrics                                 # noqa: PLC0415
    p = capture_before(t_minus_1, symbol, base)
    if not p:
        return {"reason": NO_CHAIN}
    rows = chain_metrics.load_rows(p)
    out = implied_from_rows(rows, event_date, timing, t_minus_1, time_text)
    out["capture"] = p.name
    return out


# ---------------------------------------------------------------------------
# The realised moves (section 4)
# ---------------------------------------------------------------------------
def realised(closes: list[tuple[str, float]], t: str, timing: str) -> dict:
    """T, T+1, T+2 signed close-to-close returns (percent) and the headline
    absolute move; "pending" (None) where the session is not stored."""
    s = sorted((d[:10], float(v)) for d, v in closes)
    days = [d for d, _ in s]
    px = dict(s)
    if t not in px:
        return {"t": None, "t1": None, "t2": None, "headline": None, "resolved": False}
    i = days.index(t)
    if i == 0:
        return {"t": None, "t1": None, "t2": None, "headline": None, "resolved": False}

    def ret(j: int) -> Optional[float]:
        if j >= len(days):
            return None
        return round(100.0 * (px[days[j]] / px[days[j - 1]] - 1.0), 3)

    r = {"t": ret(i), "t1": ret(i + 1), "t2": ret(i + 2)}
    end = i + (1 if timing == "unknown" else 0)
    r["headline"] = (round(abs(100.0 * (px[days[end]] / px[days[i - 1]] - 1.0)), 3)
                     if end < len(days) else None)
    r["resolved"] = r["t2"] is not None and r["headline"] is not None
    return r


# ---------------------------------------------------------------------------
# The ledger rows
# ---------------------------------------------------------------------------
def event_id(typ: str, event_date: str) -> str:
    return f"{typ}:{str(event_date)[:10]}"


def ledger_body(typ: str, underlying: str, event: str, event_date: str,
                time_text: Optional[str], timing: str, t: str, t_minus_1: str,
                implied: dict, real: Optional[dict] = None,
                cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    spec = (cfg.get("types") or {}).get(base_type(typ)) or {}
    return {"id": event_id(typ, event_date), "type": typ, "underlying": underlying,
            "event": event, "event_date": str(event_date)[:10], "time": time_text,
            "timing": timing, "T": t, "T_minus_1": t_minus_1, "implied": implied,
            "realised": real or {"t": None, "t1": None, "t2": None, "headline": None,
                                 "resolved": False},
            # 124f: every row of this ledger is scheduled; the class defaults by
            # type and the operator may re-tag it.
            "scheduled": "scheduled", "catalyst_class": spec.get("default_class"),
            "tag_basis": "default by type"}


def store_row(body: dict, now: str) -> dict:
    return {"registry_key": LEDGER_KEY, "instrument": body["id"],
            "observed_at": body["event_date"], "available_at": now,
            "value": json.dumps(body, sort_keys=True, default=str),
            "source": "event_vol"}


def ledger_rows(db_path: Optional[str], cutoff: str) -> list[dict]:
    """The newest vintage of each event's row knowable at `cutoff`, read-only
    (mode=ro); [] with no store."""
    from . import observations                                  # noqa: PLC0415
    p = Path(db_path or observations.DEFAULT_DB)
    if not p.is_file():
        return []
    conn = sqlite3.connect(f"file:{p.as_posix()}?mode=ro", uri=True)
    try:
        cur = conn.execute(
            "SELECT instrument, value_text FROM observations WHERE registry_key = ? "
            "AND available_at <= ? ORDER BY available_at, id", (LEDGER_KEY, cutoff))
        newest: dict[str, str] = {}
        for inst, txt in cur.fetchall():
            if txt:
                newest[inst] = txt
    except sqlite3.Error:
        return []
    finally:
        conn.close()
    out = []
    for txt in newest.values():
        try:
            out.append(json.loads(txt))
        except ValueError:
            continue
    return out


# ---------------------------------------------------------------------------
# The statistic, the print and the flag (section 6)
# ---------------------------------------------------------------------------
def medians(rows: list[dict]) -> dict[str, tuple[Optional[float], int]]:
    """{type: (median headline realised move, n resolved)}."""
    by: dict[str, list[float]] = {}
    for r in rows:
        rr = r.get("realised") or {}
        if rr.get("resolved") and rr.get("headline") is not None:
            by.setdefault(r["type"], []).append(float(rr["headline"]))
    return {k: (statistics.median(v), len(v)) for k, v in by.items()}


def clause(typ: str, implied: Optional[dict], meds: dict,
           min_n: int = 20, with_implied: bool = True) -> tuple[str, bool]:
    """Ahead's text for one ranked event and whether the flag fires."""
    med, n = meds.get(typ, (None, 0))
    parts = []
    ev = (implied or {}).get("event_pct")
    if with_implied:
        if not implied or implied.get("reason"):
            parts.append(f"implied: {(implied or {}).get('reason') or NO_CHAIN}")
        elif ev is not None:
            parts.append(f"implied ±{ev:.1f}% "
                         + ("(event day's share of the straddle to "
                            f"{implied['expiry']})" if implied.get("share", 1) < 1
                            else f"(straddle to {implied['expiry']})"))
        else:
            parts.append(f"implied ±{implied['full_pct']:.1f}% (straddle to "
                         f"{implied['expiry']}; includes non-event days)")
    if n < min_n:
        parts.append(f"median realised for its type: accruing (n={n} of {min_n})")
        return "; ".join(parts), False
    parts.append(f"median realised for its type ±{med:.1f}% (n={n})")
    fired = ev is not None and ev < med
    if fired:
        parts.append(CHEAP)
    return "; ".join(parts), fired


def implied_latest(symbol: str, event_date: str, time_text: Optional[str],
                   timing: str, day: str, base: Optional[Path] = None,
                   back: int = 5) -> dict:
    """Ahead's implied move ahead of T-1: the newest capture at or before `day`
    (looking back `back` days), dated, by the same rules as the ledger's."""
    from . import chain_metrics                                 # noqa: PLC0415
    d = dt.date.fromisoformat(day)
    for k in range(back + 1):
        x = (d - dt.timedelta(days=k)).isoformat()
        p = capture_before(x, symbol, base)
        if p:
            out = implied_from_rows(chain_metrics.load_rows(p), event_date, timing, x,
                                    time_text)
            out["capture_day"] = x
            return out
    return {"reason": NO_CHAIN}


def ahead_annotations(events: list[dict], day: str, db_path: Optional[str],
                      cutoff: str, chain_base: Optional[Path] = None) -> list:
    """For Ahead (the close and the Weekly): one annotation per event dict
    ({title, cls, date, time, symbol, has_implied}) -- None when the event is not
    one of the six types, else {type, text, fired}. The medians are read once,
    read-only, from the ledger as known at `cutoff`; a store that is not passed
    reads nothing and every type prints "accruing (n=0 of 20)"."""
    cfg = config()
    min_n = int(cfg.get("min_events") or 20)
    meds = medians(ledger_rows(db_path, cutoff)) if db_path else {}
    out: list = []
    for ev in events:
        title = (f"{ev['symbol']} earnings" if ev.get("symbol")
                 and "earnings" in str(ev.get("cls") or ev.get("title") or "")
                 else str(ev.get("title") or ""))
        c = classify(title, ev.get("cls"), cfg)
        if not c:
            out.append(None)
            continue
        typ, und = c
        spec = (cfg.get("types") or {}).get(base_type(typ)) or {}
        tt = ev.get("time") if base_type(typ) == "earnings" else spec.get("time")
        tim = timing_of(typ, ev.get("time"), cfg)
        try:
            imp = (None if ev.get("has_implied") else
                   implied_latest(und, str(ev["date"])[:10], tt, tim, day, chain_base))
        except Exception:                                       # noqa: BLE001
            log.warning("event vol: implied move unavailable for %s", title,
                        exc_info=True)
            imp = {"reason": NO_CHAIN}
        txt, fired = clause(typ, imp, meds, min_n, with_implied=not ev.get("has_implied"))
        out.append({"type": typ, "text": txt, "fired": fired})
    return out


FLAG_NOTE = ("Cheap event vol (item 119): the implied move sits below the median "
             "realised move of its event type; log-only until 20 resolved events of a "
             "type, and printed in Ahead only.")


# ---------------------------------------------------------------------------
# The EOD step: record on T-1, resolve as T+2 lands
# ---------------------------------------------------------------------------
def calendar_events(db_path: Optional[str], first: str, last: str,
                    cutoff: str) -> list[dict]:
    """The stored calendar's scheduled rows between two dates, as known at the
    cutoff (altdata/events.py, read as the close's Ahead reads it)."""
    from . import events                                        # noqa: PLC0415
    try:
        with events.EventStore(db_path) as ev:
            return [r for r in ev.calendar(first, last, as_of=cutoff)
                    if r.get("type") in ("scheduled", "session_event")]
    except Exception:                                           # noqa: BLE001
        log.warning("calendar unavailable", exc_info=True)
        return []


def due(cal: list[dict], day: str, cfg: Optional[dict] = None) -> list[dict]:
    """The calendar's events of the six types whose T-1 is `day`."""
    cfg = cfg or config()
    out, seen = [], set()
    for r in cal:
        title = str(r.get("title") or "")
        c = classify(title.split(" -- ")[0], None, cfg)
        if not c:
            continue
        typ, und = c
        ed = str(r["observed_at"])[:10]
        tim = timing_of(typ, None, cfg)
        t, tm1 = day_t(ed, tim)
        if tm1 != day or event_id(typ, ed) in seen:
            continue
        seen.add(event_id(typ, ed))
        tt = ((cfg.get("types") or {}).get(base_type(typ)) or {}).get("time")
        out.append({"type": typ, "underlying": und, "event": title, "event_date": ed,
                    "timing": tim, "T": t, "T_minus_1": tm1, "time": tt})
    return out


def closes_of(st, symbol: str, cutoff: str) -> list[tuple[str, float]]:
    key = f"yfinance.mkt_{symbol.lower()}"
    try:
        from .sources import yfinance_source                    # noqa: PLC0415
        sk = yfinance_source.instrument(symbol).get("store_key")
        key = (sk if "." in sk else f"yfinance.{sk}") if sk else key
    except Exception:                                           # noqa: BLE001
        pass
    return [(str(r["observed_at"])[:10], float(r["value_num"]))
            for r in st.as_of(key, cutoff) if r.get("value_num") is not None]


def eod(day: str, now: str, db_path: Optional[str] = None,
        chain_base: Optional[Path] = None, dry_run: bool = False) -> dict:
    """Record the implied move of every event whose T-1 is `day`; resolve every
    open row whose sessions have landed. A new vintage, never an overwrite."""
    from . import observations                                  # noqa: PLC0415
    cfg = config()
    last = (dt.date.fromisoformat(day) + dt.timedelta(days=10)).isoformat()
    cal = calendar_events(db_path, day, last, now)
    have = {r["id"]: r for r in ledger_rows(db_path, now)}
    wrote = []
    for e in due(cal, day, cfg):
        if event_id(e["type"], e["event_date"]) in have:
            continue
        imp = implied_move(e["underlying"], e["event_date"], e["timing"],
                           e["T_minus_1"], chain_base, e.get("time"))
        wrote.append(ledger_body(e["type"], e["underlying"], e["event"],
                                 e["event_date"], e.get("time"), e["timing"], e["T"],
                                 e["T_minus_1"], imp, None, cfg))
    if have:
        with observations.ObservationStore(db_path) as st:
            for b in have.values():
                if (b.get("realised") or {}).get("resolved"):
                    continue
                rr = realised(closes_of(st, b["underlying"], now), b["T"], b["timing"])
                if rr != b.get("realised"):
                    wrote.append({**b, "realised": rr})
    if wrote and not dry_run:
        with observations.open_writer("event_vol", db_path) as st:
            st.write_many([store_row(b, now) for b in wrote])
    return {"recorded": [b["id"] for b in wrote if not (b.get("realised") or {}).get("t")],
            "rows": len(wrote), "dry_run": dry_run}


# ---------------------------------------------------------------------------
# V-101a: is the T-1 ATM straddle readable for SPX or SPY and each of the 13?
# ---------------------------------------------------------------------------
def check_chains(day: str, base: Optional[Path] = None) -> list[dict]:
    """For each name, the latest capture on or before `day` and whether an
    at-the-money straddle reads on its first expiry after the next session."""
    from . import chain_metrics, config as acfg                 # noqa: PLC0415
    from daily_cascade import ahead                             # noqa: PLC0415
    root = base or chain_metrics.chain_dir()
    out = []
    for sym in ["SPX"] + acfg.options_universe():
        p = None
        dirs = sorted((d.name for d in root.iterdir() if d.is_dir() and d.name <= day),
                      reverse=True) if root.is_dir() else []
        for d in dirs:
            p = chain_metrics.latest_capture(d, root, sym)
            if p:
                break
        if not p:
            out.append({"symbol": sym, "result": NO_CHAIN})
            continue
        rows = chain_metrics.load_rows(p)
        d0 = p.parent.name
        exps = sorted({str(r["expiry"])[:10] for r in rows if r.get("expiry")})
        nxt = next_session(dt.date.fromisoformat(d0)).isoformat()
        ex = ahead.straddle_expiry(exps, nxt, None)
        st = ahead.atm_straddle(rows, ex) if ex else None
        out.append({"symbol": sym, "capture": f"{d0}/{p.name}", "expiry": ex,
                    "result": ("readable: straddle {:.2f} on spot {:.2f} ({:.2f}%)".format(
                        st[0], st[1], 100 * st[0] / st[1]) if st else
                        "not readable: no two-sided at-the-money quote")})
    return out


# ---------------------------------------------------------------------------
# The first edition (and every later one): the ledger through write_ledger
# ---------------------------------------------------------------------------
def edition(rows: list[dict], seeds: list[dict], as_of: str, source_mode: str,
            sources: list[str], min_n: int = 20) -> dict:
    meds = medians(rows)
    types = sorted({r["type"] for r in rows} | {base_type(t) for t in
                                                (config().get("types") or {})})
    body = ["The ledger is log-only: no type holds 20 resolved events, so no median "
            "is compared and no flag fires." if all(n < min_n for _, n in meds.values())
            else "Types at 20 resolved events or more compare and flag.", "",
            "| Type | Resolved n | Median headline realised | Status |",
            "|---|---|---|---|"]
    for t in types:
        med, n = meds.get(t, (None, 0))
        body.append(f"| {t} | {n} | "
                    + (f"{med:.2f}%" if med is not None else "—")
                    + f" | {'compared' if n >= min_n else f'accruing (n={n} of {min_n})'} |")
    body += ["", "Rows (the store's ledger, then the seed rows, each marked):", "",
             "| Event | Type | Day T | Implied (event) | Share | T | T+1 | T+2 | Headline | "
             "Tags | Marked |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    eps = []

    def pc(v):
        return "pending" if v is None else f"{v:+.2f}%"

    for r in list(rows) + list(seeds):
        imp = r.get("implied") or {}
        rr = r.get("realised") or {}
        ev = imp.get("event_pct")
        itxt = (imp.get("reason") or imp.get("text")
                or (f"±{ev:.2f}%" if ev is not None else
                    (f"±{imp['full_pct']:.2f}% (includes non-event days)"
                     if imp.get("full_pct") is not None else "—")))
        share = imp.get("share")
        body.append(f"| {r['event']} | {r['type']} | {r['T']} | {itxt} | "
                    f"{'—' if share is None else f'{share:.2f}'} | {pc(rr.get('t'))} | "
                    f"{pc(rr.get('t1'))} | {pc(rr.get('t2'))} | "
                    f"{'pending' if rr.get('headline') is None else format(rr['headline'], '.2f') + '%'} | "
                    f"{r.get('scheduled')}, {r.get('catalyst_class')} | "
                    f"{r.get('mark', 'ledger row')} |")
        eps.append({"event": r["event"], "type": r["type"], "event_date": r["event_date"],
                    "T": r["T"], "implied_event_pct": ev, "implied_text": itxt,
                    "share": share, "real_t": rr.get("t"), "real_t1": rr.get("t1"),
                    "real_t2": rr.get("t2"), "headline": rr.get("headline"),
                    "scheduled": r.get("scheduled"),
                    "catalyst_class": r.get("catalyst_class"),
                    "mark": r.get("mark", "ledger row")})
    resolved = sum(1 for r in rows if (r.get("realised") or {}).get("resolved"))
    return {"item": ITEM,
            "title": ("Item 119's event-vol pricing: the T-1 implied move against the "
                      "realised T, T+1 and T+2 moves, by event type"),
            "as_of": as_of, "window": f"from the ledger's first row to {as_of}",
            "n": resolved,
            "statistic": ("per type: the median headline realised move over the resolved "
                          "rows, with n; the implied event move beside it"),
            "pass_rule": PASS_RULE,
            "verdict": "NO GATE IN THE ORDER -- log-only until 20 events of a type",
            "rights": RIGHTS, "sources": sources, "source_mode": source_mode,
            "body": body, "episodes": eps,
            "caveats": ["The implied move is read from the T-1 capture at or before "
                        "16:35 ET; a session with no capture records \"no chain\".",
                        "A seed row's implied move is the order's figure, never a chain "
                        "read: it is printed and never compared or counted.",
                        "Earnings dates are mostly stored without a time: those rows' "
                        "headline realised move spans T and T+1."]}


def seed_rows(source: str, db_path: Optional[str] = None) -> list[dict]:
    """The edition's seed rows (config `ledger_seeds`): the 2026 midterm, its
    implied move the order's figure, its realised moves from `source`."""
    cfg = config()
    out = []
    for s in cfg.get("ledger_seeds") or []:
        t, tm1 = day_t(s["event_date"], s["timing"])
        if source == "public":
            from .ledgers import sources as S                   # noqa: PLC0415
            closes = S.yahoo(s["underlying"])
        else:
            from . import observations                          # noqa: PLC0415
            with observations.ObservationStore(db_path) as st:
                closes = closes_of(st, s["underlying"], dt.datetime.now(
                    dt.timezone.utc).isoformat())
        body = ledger_body(s["type"], s["underlying"], s["event"], s["event_date"],
                           s.get("time"), s["timing"], t, tm1,
                           {"text": s["implied_text"]}, realised(closes, t, s["timing"]),
                           cfg)
        body["scheduled"], body["catalyst_class"] = s["scheduled"], s["catalyst_class"]
        body["mark"] = s["mark"]
        out.append(body)
    return out


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    from . import session                                       # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.event_vol")
    ap.add_argument("cmd", choices=["eod", "show", "check-chains", "edition"])
    ap.add_argument("--date", default=None)
    ap.add_argument("--db", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--source", choices=["public", "store"], default="store")
    a = ap.parse_args(argv)
    now = session.utc_iso()
    day = a.date or session.session_date()
    if a.cmd == "check-chains":
        for r in check_chains(day):
            print(f"{r['symbol']:6s} {r.get('capture', '-'):28s} {r['result']}")
        return 0
    if a.cmd == "eod":
        r = eod(day, now, a.db, dry_run=a.dry_run)
        print(f"event vol: {r['rows']} row(s) {'would be ' if a.dry_run else ''}written; "
              f"recorded {', '.join(r['recorded']) or 'none'}")
        return 0
    rows = ledger_rows(a.db, now)
    if a.cmd == "show":
        meds = medians(rows)
        for t, (m, n) in sorted(meds.items()):
            print(f"{t}: median {m:.2f}% (n={n})")
        print(f"{len(rows)} row(s) in {LEDGER_KEY}")
        return 0
    from .ledgers import write_ledger                           # noqa: PLC0415
    seeds = seed_rows(a.source, a.db)
    mode = ("laptop run, public sources" if a.source == "public"
            else "box run, the box's store")
    srcs = ([f"store: {LEDGER_KEY} (the box's ledger rows)"] if a.source == "store"
            else [f"store: {LEDGER_KEY} -- none on the laptop (the box's EOD pass "
                  f"writes it)"]) + \
        [f"seed realised moves: {'Yahoo daily closes' if a.source == 'public' else 'the store'}"
         f" of {', '.join(sorted({s['underlying'] for s in seeds}))}"]
    r = edition(rows if a.source == "store" else [], seeds, day, mode, srcs,
                int(config().get("min_events") or 20))
    md, cv = write_ledger(r, run_date=day)
    print(f"wrote {md.name}" + (f" and {cv.name}" if cv else ""))
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
