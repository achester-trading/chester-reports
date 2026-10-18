"""
THE BOOK B SCANNER -- the Weekly's candidate list.
(docs/briefs/book-b-scanner-brief-2026-10-12.md, ruled 12 Oct 2026; the
Operating Doctrine section 4.2 and the regime card, section 5.2.)

    from altdata import book_b_scanner as bbs
    res = bbs.scan(ending, db_path, cutoff=now, calendar=..., walls=...)
    bbs.candidates(ending, db_path)            # the hook W-1.3a's block reads
    bbs.record_forecasts(res["candidates"], ending, now, db_path, dry_run=True)
    bbs.grade(db_path, ending, cutoff, dry_run=True)

    python -m altdata.book_b_scanner --ending 2026-10-09    # print, write nothing

Config: config/book_b_scanner.yaml. Run inside the Weekly's build over Friday's
close and nowhere else (decision 7). It READS the store; it fetches nothing, and
it writes only the ledger forecasts the Weekly asks it to (decision 6).

THE PIPELINE (the brief's section 3):

  1 UNIVERSE   every `yfinance.mkt_*` close series with >= 120 sessions, the
               companions (_high, _low, _volume, ...) and the index levels
               excluded; the earnings universe's names where the store carries
               them, the rest counted. A restricted instrument (the Brookfield
               list) is dropped HERE, before anything is computed for it -- the
               blocklist at write time, again at print time in the block.
  2 TREND      four conditions for each direction: the close against the 50-day,
               against the 200-day, the 50-day against the 200-day, higher highs
               and higher lows over 60 sessions (a long; the mirror for a short).
               Three of four is the primary trend. A candidate against it is
               "against the tape": a five-session time stop and no add.
  3 PIVOTS     breakout (a close through a base of N sessions with range <= R%,
               on volume >= V x its 20-session average); reclaim (a close back
               through a level lost within L sessions -- a base high, the 50-day,
               a wall the chain names -- on volume); failed breakdown (a close
               through the base low, back inside within F sessions). A short is
               the same pivot mirrored. Each fired in the week and still holds at
               Friday's close. The parameters print beside the candidate.
  4 CONFIRM    relative strength, positioning, a Weekly tell, a Top & Bottom
               overlay, the correlation break -- counted by code. One for a long
               (two after a T&B top signal); two for a short, AND the regime's
               permission. Unmet confirmations are the counter-thesis; a crowd on
               the same side is a WARNING.
  5 GATES      from the dials, read never recomputed: the Doctrine regime through
               the ratified mapping (register.heat.regime_band, with the crossing
               rule), the Volatility dial's multiplier, the Gamma dial's timing.
  6 SCORE      a weighted mean of five components on [0, 1]; ranked; the top ten
               print, the rest go to the reference tier.
  7 DRAFT      the register's draft fields, code-templated (no model).
  8 GRADING    every candidate, taken or not, a ledger forecast "reaches +1R
               before -1R within six weeks", resolved from stored closes.

Nothing here stages, sizes or places an order. The size printed is the
Doctrine's arithmetic on paper.
"""

from __future__ import annotations

import datetime as dt
import importlib
import json
import logging
import re
from pathlib import Path
from statistics import mean
from typing import Any, Optional

import yaml

from . import derived, observations, session
from .numeral_audit import ordinal

log = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "config" / "book_b_scanner.yaml"
DRY_RUN_NAMESPACE = "dryrun."
PIVOT_NAMES = {("breakout", "long"): "breakout from a base",
               ("breakout", "short"): "breakdown from a base",
               ("reclaim", "long"): "reclaim of a lost level",
               ("reclaim", "short"): "loss of a regained level",
               ("failed_breakdown", "long"): "failed breakdown",
               ("failed_breakdown", "short"): "failed breakout"}


def load_config(path: Optional[Path] = None) -> dict:
    with open(path or CONFIG_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def source_name(dry_run: bool, cfg: Optional[dict] = None) -> str:
    """A dry run writes under its own namespace, never the live source."""
    src = ((cfg or load_config()).get("grading") or {}).get("source") \
        or "book_b_candidate"
    return (DRY_RUN_NAMESPACE if dry_run else "") + src


# ---------------------------------------------------------------------------
# 1. The universe
# ---------------------------------------------------------------------------
def _pts(st, key: str, cutoff: Optional[str], ending: str,
         instrument: Optional[str] = None) -> list[tuple[str, float]]:
    rows = {str(r["observed_at"])[:10]: float(r["value_num"])
            for r in st.as_of(key, cutoff, instrument)
            if r.get("value_num") is not None}
    return sorted((d, v) for d, v in rows.items() if d <= ending)


def symbol_of(key: str, cfg: dict) -> str:
    from .sources import yfinance_source as yf                  # noqa: PLC0415
    rev = {v: k for k, v in yf.SYMBOLS.items()}
    tail = key[len("yfinance."):] if key.startswith("yfinance.") else key
    return rev.get(tail) or tail.removeprefix("mkt_").upper().replace("_", "-")


def _restricted(symbol: str) -> bool:
    try:
        from register import instruments                        # noqa: PLC0415
        return instruments.restrictions().is_restricted(symbol)
    except Exception:                                           # noqa: BLE001
        return True                     # the list unreadable: refuse, never risk it


def earnings_names() -> list[str]:
    try:
        from .sources import earnings                           # noqa: PLC0415
        return earnings.universe()
    except Exception:                                           # noqa: BLE001
        return []


def _session_volume_5m(bst, tape_id: str, ending: str, cutoff: Optional[str],
                       min_bars: int) -> dict[str, float]:
    """Session volume summed from the tape set's 5-minute bars, complete
    sessions only."""
    first = (dt.date.fromisoformat(ending) - dt.timedelta(days=200)).isoformat()
    by: dict[str, list] = {}
    for b in bst.read(tape_id, "5m", first, ending + "T23:59:59+00:00", cutoff):
        if b.get("volume") is not None:
            by.setdefault(str(b["observed_at"])[:10], []).append(float(b["volume"]))
    return {d: sum(v) for d, v in by.items() if len(v) >= min_bars}


def _volume_unit(symbol: str) -> Optional[str]:
    """The stored volume's unit (yfinance_source.VOLUME_UNITS): shares, count
    (futures contracts) or usd (crypto)."""
    from .sources import yfinance_source as yf                  # noqa: PLC0415
    return yf.VOLUME_UNITS.get(symbol, "shares")


def dollar_volume(inst: dict, j: int) -> Optional[float]:
    """Session j's traded dollars, where the stored unit gives one: shares x the
    close, or a volume already quoted in dollars. A futures volume is contracts,
    and contracts x the close misses the contract's multiplier, so it gives none."""
    v = inst["volume"].get(inst["days"][j])
    if v is None:
        return None
    unit = inst.get("vol_unit") or "shares"
    return v if unit == "usd" else None if unit == "count" else inst["close"][j] * v


def load_universe(st, ending: str, cutoff: Optional[str], cfg: dict,
                  bst=None) -> tuple[list[dict], dict]:
    u = cfg.get("universe") or {}
    pref = (str(u.get("price_namespace") or "yfinance") + "."
            + str(u.get("price_prefix") or "mkt_"))
    comp = tuple(u.get("companion_suffixes") or ())
    excl = set(u.get("exclude") or [])
    need = int(u.get("min_sessions") or 120)
    vcfg = (cfg.get("pivots") or {}).get("volume") or {}
    tape = {}
    try:
        from . import bars as bars_mod                          # noqa: PLC0415
        tape = {t.get("daily"): t["id"] for t in bars_mod.tape() if t.get("daily")}
    except Exception:                                           # noqa: BLE001
        pass
    keys = [k for k in st.keys() if k.startswith(pref) and not k.endswith(comp)]
    out, skipped = [], {"short_history": [], "restricted": [], "excluded": [],
                        "earnings_not_stored": []}
    for key in sorted(keys):
        sym = symbol_of(key, cfg)
        if sym in excl:
            skipped["excluded"].append(sym)
            continue
        if _restricted(sym):
            skipped["restricted"].append(sym)
            continue
        closes = _pts(st, key, cutoff, ending)
        if len(closes) < need:
            skipped["short_history"].append(sym)
            continue
        days = [d for d, _ in closes]
        hi = dict(_pts(st, key + "_high", cutoff, ending))
        lo = dict(_pts(st, key + "_low", cutoff, ending))
        vol = dict(_pts(st, key + "_volume", cutoff, ending))
        vsrc = "stored" if vol else None
        vunit = _volume_unit(sym) if vol else None
        if not vol and bst is not None and key in tape:
            vol = _session_volume_5m(bst, tape[key], ending, cutoff,
                                     int(vcfg.get("min_5m_bars") or 70))
            vsrc = "5-minute bars" if vol else None
            vunit = "shares" if vol else None
        out.append({"symbol": sym, "key": key, "days": days,
                    "close": [v for _, v in closes],
                    "high": [hi.get(d, c) for d, c in closes],
                    "low": [lo.get(d, c) for d, c in closes],
                    "has_range": bool(hi and lo), "volume": vol, "vol_source": vsrc,
                    "vol_unit": vunit})
    have = {i["symbol"] for i in out} | set(skipped["short_history"])
    skipped["earnings_not_stored"] = sorted(s for s in earnings_names()
                                            if s not in have)
    return out, skipped


# ---------------------------------------------------------------------------
# 2. Trend
# ---------------------------------------------------------------------------
def sma(vals: list[float], n: int, i: int) -> Optional[float]:
    return None if i + 1 < n else sum(vals[i - n + 1:i + 1]) / n


def atr(inst: dict, i: int, n: int) -> tuple[Optional[float], str]:
    """The average true range at i; without a stored range, the average
    absolute close-to-close change, named as such."""
    c = inst["close"]
    if i < n:
        return None, "none"
    if inst["has_range"]:
        trs = [max(inst["high"][j] - inst["low"][j], abs(inst["high"][j] - c[j - 1]),
                   abs(inst["low"][j] - c[j - 1])) for j in range(i - n + 1, i + 1)]
        return sum(trs) / n, "ATR"
    return (sum(abs(c[j] - c[j - 1]) for j in range(i - n + 1, i + 1)) / n,
            "average close-to-close change")


def trend(inst: dict, i: int, cfg: dict) -> dict:
    t = cfg.get("trend") or {}
    c = inst["close"]
    f, s = sma(c, int(t.get("fast_ma") or 50), i), sma(c, int(t.get("slow_ma") or 200), i)
    lb = int(t.get("lookback") or 60)
    half = lb // 2
    hh = hl = lh = ll = None
    if i + 1 >= lb:
        a, b = inst["high"][i - lb + 1:i - half + 1], inst["high"][i - half + 1:i + 1]
        la, lb_ = inst["low"][i - lb + 1:i - half + 1], inst["low"][i - half + 1:i + 1]
        hh, hl = max(b) > max(a), min(lb_) > min(la)
        lh, ll = max(b) < max(a), min(lb_) < min(la)
    conds_long = [f is not None and c[i] > f, s is not None and c[i] > s,
                  f is not None and s is not None and f > s, bool(hh and hl)]
    conds_short = [f is not None and c[i] < f, s is not None and c[i] < s,
                   f is not None and s is not None and f < s, bool(lh and ll)]
    k = int(t.get("min_agree") or 3)
    up, down = sum(conds_long), sum(conds_short)
    state = "up" if up >= k else "down" if down >= k else "none"
    return {"state": state, "agree": {"long": up, "short": down},
            "fast": f, "slow": s, "slow_read": s is not None}


# ---------------------------------------------------------------------------
# 3. The pivots
# ---------------------------------------------------------------------------
def base_before(inst: dict, i: int, cfg: dict, cap_high: Optional[float] = None,
                floor_low: Optional[float] = None) -> Optional[dict]:
    """The longest base ending at i - 1 (N sessions, N in [min, max]) whose range
    is at most R% of the close at i - 1; None if none qualifies.

    `cap_high` / `floor_low`: only windows whose high stays below (low stays
    above) the given close -- the base a close at i actually broke out of. A
    longer window reaching back into older, higher prices is a different base,
    and the close did not clear it."""
    b = (cfg.get("pivots") or {}).get("base") or {}
    lo_n, hi_n = int(b.get("min_sessions") or 20), int(b.get("max_sessions") or 60)
    r = float(b.get("max_range_pct") or 10.0)
    end = i - 1
    best = None
    for n in range(lo_n, hi_n + 1):
        start = end - n + 1
        if start < 0:
            break
        h, l = max(inst["high"][start:end + 1]), min(inst["low"][start:end + 1])
        if (cap_high is not None and h >= cap_high) or \
                (floor_low is not None and l <= floor_low):
            break                     # windows nest: a longer one only widens
        rp = 100.0 * (h - l) / inst["close"][end]
        if rp <= r:
            best = {"n": n, "high": h, "low": l, "range_pct": rp, "end": end}
    return best


def volume_ratio(inst: dict, i: int, cfg: dict) -> Optional[float]:
    v = (cfg.get("pivots") or {}).get("volume") or {}
    n = int(v.get("average_sessions") or 20)
    vol, days = inst["volume"], inst["days"]
    if days[i] not in vol:
        return None
    prior = [vol[d] for d in days[max(0, i - 3 * n):i] if d in vol][-n:]
    if len(prior) < n or not mean(prior):
        return None
    return vol[days[i]] / mean(prior)


def _volume_ok(inst: dict, i: int, cfg: dict) -> tuple[bool, Optional[float], bool]:
    """(passes, ratio, unconfirmed). No stored volume: passes unconfirmed, or
    fails under `strict`."""
    v = (cfg.get("pivots") or {}).get("volume") or {}
    ratio = volume_ratio(inst, i, cfg)
    if ratio is None:
        return (str(v.get("when_absent") or "unconfirmed") != "strict", None, True)
    return ratio >= float(v.get("multiple") or 1.5), ratio, False


def is_fx(symbol: str) -> bool:
    """A currency pair, as the store names it (yfinance's =X)."""
    return str(symbol or "").upper().endswith("=X")


def breakout_skip(inst: dict) -> Optional[str]:
    """Why the breakout template does not scan this instrument, or None (W8-7)."""
    if is_fx(inst.get("symbol")):
        return (f"{inst.get('symbol')}: a currency pair -- the breakout template "
                f"scans no =X pair (managed currencies among them)")
    if not any(v for v in (inst.get("volume") or {}).values()):
        return f"{inst.get('symbol')}: no stored volume -- the breakout template needs it"
    return None


def _crossed(c, t, lvl, d) -> bool:
    """The close at t crossed the level in direction d (+1 up, -1 down)."""
    return (c[t] - lvl(t)) * d > 0 and (c[t - 1] - lvl(t - 1)) * d <= 0


def detect(inst: dict, cfg: dict, walls: Optional[list] = None) -> list[dict]:
    """Every pivot that fired in the last `fire_sessions` and still holds."""
    pv = cfg.get("pivots") or {}
    c, hi, lo = inst["close"], inst["high"], inst["low"]
    E = len(c) - 1
    fire = int(pv.get("fire_sessions") or 5)
    L = int((pv.get("reclaim") or {}).get("window_sessions") or 10)
    F = int((pv.get("failed_breakdown") or {}).get("window_sessions") or 5)
    held = int((pv.get("reclaim") or {}).get("held_sessions") or 5)
    fast = int((cfg.get("trend") or {}).get("fast_ma") or 50)
    out: list[dict] = []
    skip = breakout_skip(inst)
    if skip:
        inst["breakout_skipped"] = skip
    for t in range(E, max(E - fire, 1), -1):
        # BREAKOUT (long) / BREAKDOWN (short) from the base the close cleared.
        for d in (() if skip else (1, -1)):
            b = base_before(inst, t, cfg, cap_high=c[t] if d > 0 else None,
                            floor_low=c[t] if d < 0 else None)
            if not b:
                continue
            lvl, inv = (b["high"], b["low"]) if d > 0 else (b["low"], b["high"])
            if _crossed(c, t, lambda _j: lvl, d) and (c[E] - lvl) * d > 0:
                ok, vr, unconf = _volume_ok(inst, t, cfg)
                if ok:
                    out.append({"setup": "breakout", "d": d, "t": t, "level": lvl,
                                "level_label": "the base " + ("high" if d > 0
                                                              else "low"),
                                "inv_level": inv, "move": b["high"] - b["low"],
                                "base": b, "volume_ratio": vr,
                                "volume_unconfirmed": unconf})
        # FAILED BREAKDOWN (long) / FAILED BREAKOUT (short): a close through the
        # base's edge at s, back inside at t within F sessions. The earliest s
        # first: the breakdown dates from the first close through the base.
        for s in range(max(t - F, 1), t):
            for d in (1, -1):
                # The base the close at s pierced: its low above that close (a
                # failed breakdown), its high below it (a failed breakout).
                bs = base_before(inst, s, cfg, cap_high=c[s] if d < 0 else None,
                                 floor_low=c[s] if d > 0 else None)
                if not bs:
                    continue
                edge = bs["low"] if d > 0 else bs["high"]
                if ((c[s] - edge) * d < 0 and _crossed(c, t, lambda _j: edge, d)
                        and all((c[j] - edge) * d < 0 for j in range(s, t))
                        and (c[E] - edge) * d > 0):
                    ext = (min(lo[s:t + 1]) if d > 0 else max(hi[s:t + 1]))
                    out.append({"setup": "failed_breakdown", "d": d, "t": t,
                                "level": edge, "level_label": "the base "
                                + ("low" if d > 0 else "high"),
                                "inv_level": ext, "move": bs["high"] - bs["low"],
                                "base": bs, "pierced_on": inst["days"][s],
                                "back_in": t - s, "volume_ratio": None,
                                "volume_unconfirmed": False})
        # RECLAIM (long) / LOSS (short) of a level lost (regained) within L.
        levels = []
        if "fast_ma" in (pv.get("reclaim") or {}).get("levels", ["fast_ma"]):
            levels.append(("the 50-day", lambda j: sma(c, fast, j) or float("nan")))
        bL = base_before(inst, t - L, cfg) if t - L > 0 else None
        if bL:
            levels.append(("a base high", lambda _j, v=bL["high"]: v))
        for lab, val in walls or []:
            levels.append((lab, lambda _j, v=float(val): v))
        for lab, lvl in levels:
            if lvl(t) != lvl(t):                                # nan: too short
                continue
            for d in (1, -1):
                if not (_crossed(c, t, lvl, d) and (c[E] - lvl(E)) * d > 0):
                    continue
                # Lost within L, after holding it `held` closes: a level the
                # close chopped across was never held.
                lost = [s for s in range(t - 1, max(t - L - 1, 0), -1)
                        if _crossed(c, s, lvl, -d) and s - held >= 0
                        and all((c[j] - lvl(j)) * d > 0 for j in range(s - held, s))]
                if not lost:
                    continue
                s = lost[0]
                ok, vr, unconf = _volume_ok(inst, t, cfg)
                if not ok:
                    continue
                ext = min(lo[s:t + 1]) if d > 0 else max(hi[s:t + 1])
                out.append({"setup": "reclaim", "d": d, "t": t, "level": lvl(t),
                            "level_label": lab, "inv_level": lvl(t),
                            "move": abs(lvl(t) - ext), "base": base_before(inst, t, cfg),
                            "lost_sessions": t - s, "volume_ratio": vr,
                            "volume_unconfirmed": unconf})
    return out


# ---------------------------------------------------------------------------
# 4. Confirmations
# ---------------------------------------------------------------------------
def _ratio_series(a: dict, b: dict) -> list[tuple[str, float]]:
    bm = dict(zip(b["days"], b["close"]))
    return [(d, v / bm[d]) for d, v in zip(a["days"], a["close"]) if bm.get(d)]


def rs_percentile(inst: dict, bench: Optional[dict], n: int) -> Optional[float]:
    if not bench or inst["symbol"] == bench["symbol"] or is_fx(inst["symbol"]):
        return None              # W8-7: an FX pair takes no RS against SPY
    r = _ratio_series(inst, bench)
    if len(r) < n:
        return None
    w = [v for _, v in r[-n:]]
    return derived.percentile_of(w, w[-1])


def positioning(st, sym: str, cutoff: Optional[str], ending: str,
                cfg: dict) -> Optional[dict]:
    """The instrument's contract as a two-year level z, signed so that + is the
    crowd long the instrument; None where none is mapped or stored."""
    p = (cfg.get("confirmations") or {}).get("positioning") or {}
    m = (p.get("map") or {}).get(sym)
    if not m:
        return None
    since = (dt.date.fromisoformat(ending)
             - dt.timedelta(days=int(p.get("window_days") or 730))).isoformat()
    key = m.get("key") or f"cftc.tff_{m['tff']}_net_oi"
    pts = [v for d, v in _pts(st, key, cutoff, ending, m["contract"]) if d >= since]
    if len(pts) < 20:
        return None
    z = derived.z_of(pts[:-1], pts[-1])
    if z is None:
        return None
    return {"z": z * float(m.get("sign", 1)), "contract": m["contract"]}


def _by_symbol(insts: list[dict]) -> dict:
    return {i["symbol"]: i for i in insts}


def tells(insts: list[dict], cfg: dict) -> dict[tuple[str, int], list[str]]:
    """(symbol, direction) -> the Weekly tells that name it."""
    t = (cfg.get("confirmations") or {}).get("tells") or {}
    by = _by_symbol(insts)
    out: dict[tuple[str, int], list[str]] = {}

    def name(sym, d, label):
        out.setdefault((sym, d), []).append(label)

    avg_n = int(t.get("style_average_sessions") or 200)
    off = float(t.get("style_off_high_pct") or 8.0)
    for p in t.get("style_pairs") or []:
        g, v = by.get(p["growth"]), by.get(p["value"])
        if not g or not v:
            continue
        r = [x for _, x in _ratio_series(g, v)]
        if len(r) < avg_n:
            continue
        avg, top = mean(r[-avg_n:]), max(r[-252:])
        lab = f"the style-regime pair ({p['growth']}/{p['value']})"
        if r[-1] < avg or r[-1] < top * (1 - off / 100.0):
            name(p["value"], 1, lab + ", value side")
            name(p["growth"], -1, lab + ", value side")
        else:
            name(p["growth"], 1, lab + ", growth side")
            name(p["value"], -1, lab + ", growth side")
    n, k = int(t.get("ratio_average_sessions") or 50), int(t.get("ratio_change_sessions") or 20)
    for q in t.get("consumer_ratios") or []:
        a, b = by.get(q["num"]), by.get(q["den"])
        if not a or not b:
            continue
        r = [x for _, x in _ratio_series(a, b)]
        if len(r) < max(n, k + 1):
            continue
        avg = mean(r[-n:])
        den = q.get("name_den", True)
        if r[-1] > avg and r[-1] > r[-1 - k]:
            name(q["num"], 1, q["label"])
            if den:
                name(q["den"], -1, q["label"])
        elif r[-1] < avg and r[-1] < r[-1 - k]:
            name(q["num"], -1, q["label"])
            if den:
                name(q["den"], 1, q["label"])
    return out


def move_flags(st, insts: list[dict], sessions: list[str], cutoff: Optional[str],
               cfg: dict) -> Optional[dict[tuple[str, int], str]]:
    """The move screen's 2.5-sigma prints on an instrument's close in the week,
    read by name; None while the screen is not on this branch."""
    t = (cfg.get("confirmations") or {}).get("tells") or {}
    try:
        ms = importlib.import_module(str(t.get("move_screen_module")
                                         or "altdata.move_screen"))
    except ImportError:
        return None
    sig = float(t.get("move_sigma") or 2.5)
    keys = {i["key"]: i["symbol"] for i in insts}
    out: dict[tuple[str, int], str] = {}
    for day in sessions:
        try:
            res = ms.read(st, day, cutoff)
        except Exception:                                       # noqa: BLE001
            res = None
        for f in (res or {}).get("flags") or []:
            sym = keys.get(f.get("series"))
            z = f.get(f"z{f.get('lead_horizon') or 1}")
            if sym and isinstance(z, (int, float)) and abs(z) >= sig:
                out[(sym, 1 if z > 0 else -1)] = (f"the move screen's {z:+.1f}σ print "
                                                  f"({day})")
    return out


def top_bottom(st, cutoff: Optional[str], ending: str, cfg: dict) -> dict:
    """The T&B signal and overlays, read by key; absent until a writer stores
    them."""
    tb = (cfg.get("confirmations") or {}).get("top_bottom") or {}
    out: dict[str, Any] = {"available": False, "signal": None, "overlay": {}}
    try:
        sig = [r for r in st.as_of(tb.get("signal_key") or "tb.signal", cutoff)
               if str(r["observed_at"])[:10] <= ending]
        if sig:
            out["available"] = True
            out["signal"] = (json.loads(sig[-1].get("value_text") or "{}") or {}
                             ).get("signal")
        key = tb.get("overlay_key") or "tb.overlay"
        for sym in st.instruments(key):
            r = [x for x in st.as_of(key, cutoff, sym)
                 if str(x["observed_at"])[:10] <= ending and x.get("value_num") is not None]
            if r:
                out["available"] = True
                out["overlay"][sym] = float(r[-1]["value_num"])
    except Exception:                                           # noqa: BLE001
        log.warning("the Top & Bottom keys are unreadable", exc_info=True)
    return out


def correlation_breaks(st, cutoff: Optional[str], sessions: list[str],
                       cfg: dict) -> Optional[dict[str, float]]:
    """symbol -> the break's delta against SPY in the week, read by name from
    the correlation layer; None while the layer is not on this branch."""
    cb = (cfg.get("confirmations") or {}).get("correlation_break") or {}
    try:
        corr = importlib.import_module(str(cb.get("module") or "altdata.correlation"))
        ccfg = corr.config()
    except Exception:                                           # noqa: BLE001
        return None
    sym_of = {}
    for a in ccfg.get("universe") or []:
        if a.get("key"):
            sym_of[a["id"]] = symbol_of(a["key"], cfg)
    out = {}
    first = sessions[0] if sessions else "0000"
    for aid in corr.break_assets(ccfg):
        key = corr.break_key(aid, cb.get("benchmark") or "spy")
        rows = [r for r in st.as_of(key, cutoff) if first <= str(r["observed_at"])[:10]
                and r.get("value_num") is not None]
        hits = [float(r["value_num"]) for r in rows if corr.is_break(r["value_num"], ccfg)]
        if hits:
            out[sym_of.get(aid, aid)] = hits[-1]
    return out


def confirm(c: dict, ctx: dict, cfg: dict) -> list[dict]:
    """Each confirmation family for the candidate: met True / False, or None
    where the family cannot be read for it."""
    cc = cfg.get("confirmations") or {}
    sym, d = c["symbol"], c["d"]
    out = []
    rs = c.get("rs_pct")
    r = cc.get("relative_strength") or {}
    if rs is None:
        out.append({"family": "relative strength", "met": None,
                    "text": ("relative strength not read (a currency pair: no RS "
                             "against SPY)" if is_fx(sym) else
                             "relative strength not read (the benchmark itself)")})
    else:
        met = rs >= float(r.get("long_min_pct") or 80) if d > 0 \
            else rs <= float(r.get("short_max_pct") or 20)
        out.append({"family": "relative strength", "met": met,
                    # W-1.3c item 7: the shared helper, never a fixed "th".
                    "text": f"RS {ordinal(rs)} percentile against SPY over "
                            f"{int(r.get('sessions') or 60)} sessions"})
    pz = ctx["positioning"].get(sym)
    thr = float((cc.get("positioning") or {}).get("crowded_z") or 1.5)
    if pz is None:
        out.append({"family": "positioning", "met": None,
                    "text": "positioning not mapped or not stored"})
    else:
        z = pz["z"] * d                    # + : the crowd on the candidate's side
        if z >= thr:
            out.append({"family": "positioning", "met": False, "warning": True,
                        "text": f"positioning crowded the same way ({pz['contract']} "
                                f"z {pz['z']:+.1f})"})
        elif z <= -thr:
            out.append({"family": "positioning", "met": True,
                        "text": f"positioning crowded the other way ({pz['contract']} "
                                f"z {pz['z']:+.1f})"})
        else:
            out.append({"family": "positioning", "met": False,
                        "text": f"positioning not crowded ({pz['contract']} "
                                f"z {pz['z']:+.1f})"})
    named = list(ctx["tells"].get((sym, d)) or [])
    mv = (ctx["moves"] or {}).get((sym, d))
    if mv:
        named.append(mv)
    out.append({"family": "a Weekly tell", "met": bool(named),
                "text": ("a Weekly tell names it: " + "; ".join(named)) if named
                else "no Weekly tell names it"})
    tb = ctx["top_bottom"]
    if not tb["available"]:
        out.append({"family": "a Top & Bottom overlay", "met": None,
                    "text": "no Top & Bottom report yet"})
    else:
        ov = tb["overlay"].get(sym)
        out.append({"family": "a Top & Bottom overlay",
                    "met": ov is not None and ov * d > 0,
                    "text": "a Top & Bottom overlay reads in the direction"
                    if ov is not None and ov * d > 0
                    else "no Top & Bottom overlay in the direction"})
    if sym in ctx["alt_assets"]:
        br = ctx["breaks"]
        if br is None:
            out.append({"family": "the correlation break", "met": None,
                        "text": "the correlation layer is not on this branch"})
        else:
            out.append({"family": "the correlation break", "met": sym in br,
                        "text": (f"a correlation break against SPY ({br[sym]:+.2f})"
                                 if sym in br else "no correlation break")})
    return out


# ---------------------------------------------------------------------------
# 5. The regime
# ---------------------------------------------------------------------------
def regime_read(st, cutoff: Optional[str], cfg: dict) -> dict:
    """The three dials in the Doctrine's words, read from the stored object."""
    rg = cfg.get("regime") or {}
    out: dict[str, Any] = {"macro": None, "vol": None, "gamma": None,
                           "macro_state": None}
    try:
        from register import heat                               # noqa: PLC0415
        band = heat.regime_band(st, cutoff)
        out["macro"], out["macro_state"] = band.get("regime"), band.get("dial_state")
    except Exception:                                           # noqa: BLE001
        log.warning("the regime band is unreadable", exc_info=True)
    try:
        import regime as regime_mod                             # noqa: PLC0415
        obj = regime_mod.latest(cutoff, st) or {}
        dials = obj.get("dials") or {}
        out["vol"] = (rg.get("vol_map") or {}).get((dials.get("vol") or {}).get("state"))
        out["gamma"] = (rg.get("gamma_map") or {}).get(
            (dials.get("gamma") or {}).get("state"))
    except Exception:                                           # noqa: BLE001
        log.warning("the market-state object is unreadable", exc_info=True)
    return out


def short_permitted(reg: dict, cfg: dict) -> tuple[bool, str]:
    rg = cfg.get("regime") or {}
    if reg.get("macro") in (rg.get("short_macro") or []):
        return True, f"the Macro regime ({reg['macro']}) permits shorts"
    if reg.get("vol") in (rg.get("short_vol") or []):
        return True, f"the Volatility dial ({reg['vol']}) permits shorts"
    return False, (f"no short in {reg.get('macro') or 'an unread Macro regime'}, "
                   f"{reg.get('vol') or 'an unread Volatility dial'}, "
                   f"{reg.get('gamma') or 'an unread Gamma dial'} "
                   f"(Doctrine 4.2)")


def multiplier(reg: dict, cfg: dict) -> tuple[float, str]:
    rg = cfg.get("regime") or {}
    vm = (rg.get("vol_multiplier") or {})
    m, why = 1.0, []
    if reg.get("vol") in vm:
        m *= float(vm[reg["vol"]])
        why.append(f"Volatility {reg['vol']} {float(vm[reg['vol']]):g}")
    if reg.get("macro") == "Transition":
        t = float(rg.get("transition_multiplier") or 0.5)
        m *= t
        why.append(f"Transition {t:g}")
    return min(m, 1.0), (", ".join(why) or "no dial read: 1")


# ---------------------------------------------------------------------------
# 6-7. Score, rank and the draft
# ---------------------------------------------------------------------------
def score(comp: dict, cfg: dict) -> float:
    w = (cfg.get("score") or {}).get("weights") or {}
    tot = sum(float(w.get(k, 1.0)) for k in comp)
    return round(sum(float(w.get(k, 1.0)) * v for k, v in comp.items()) / tot, 4) \
        if tot else 0.0


def _f(x: float) -> str:
    return f"{x:,.2f}"


def candidate_id(ending: str, sym: str, direction: str, setup: str) -> str:
    return "bb-" + re.sub(r"[^a-z0-9]+", "-",
                          f"{ending}-{sym}-{direction}-{setup}".lower()).strip("-")


def _catalyst(sym: str, calendar: Optional[list], ending: str) -> tuple:
    """The instrument's own earnings in the coming six weeks, else the week
    ahead's first tier-1 release, else none."""
    rows = sorted(calendar or [], key=lambda r: str(r.get("date")))
    own = [r for r in rows if str(r.get("symbol") or "").upper() == sym.upper()]
    if own:
        return f"{sym} earnings", str(own[0]["date"])[:10]
    top = [r for r in rows if r.get("tier1") and not r.get("symbol")]
    if top:
        return str(top[0]["event"]), str(top[0]["date"])[:10]
    return None, None


def volume_readings(inst: dict, E: int, base: Optional[dict], entry: float,
                    risk: float, d: int, cfg: Optional[dict] = None) -> dict:
    """VP-1 item 9: two readings from DAILY bars, printed beside the candidate
    and used by nothing else -- the score, the gates, the timing and the grading
    do not read them. Whether they matter is H-006's question, not this module's.

      the base's POC        from the base's own N sessions
      the nearest HVN       between the entry and the +1R target, from the last
                            scanner_hvn_sessions sessions; its price and distance,
                            or "none"

    Both through altdata/volume_profile.py, at its daily bin width, and both
    "approximated from daily bars"."""
    from . import volume_profile as vp                          # noqa: PLC0415
    vcfg = vp.load_config()
    vol = inst.get("volume") or {}

    def rows(a: int, b: int) -> list[dict]:
        return [{"observed_at": inst["days"][j], "high": inst["high"][j],
                 "low": inst["low"][j], "close": inst["close"][j],
                 "volume": vol.get(inst["days"][j])} for j in range(max(0, a), b + 1)]
    out: dict[str, Any] = {"note": vp.DAILY_NOTE, "base_poc": None, "hvn": None}
    if not inst.get("has_range", True):
        why = "no daily high and low stored"
        out.update(base_text=f"base POC not computed ({why})",
                   hvn_text=f"not computed ({why})")
        return out
    if base:
        bp = vp.daily_profile(rows(base["end"] - base["n"] + 1, base["end"]), vcfg)
        out["base_poc"] = bp.get("poc")
        out["base_text"] = (f"base POC {_f(bp['poc'])}" if bp.get("poc") is not None
                            else f"base POC not computed ({bp.get('absent')})")
    else:
        out["base_text"] = "base POC not computed (no base)"
    n = int(vcfg.get("scanner_hvn_sessions", 252))
    hp = vp.daily_profile(rows(E - n + 1, E), vcfg)
    if hp.get("poc") is None:
        out["hvn_text"] = f"not computed ({hp.get('absent')})"
        return out
    target = entry + d * risk
    lo, hi = sorted((entry, target))
    between = [h for h in hp["hvn"] if lo < h <= hi] if d > 0 else \
        [h for h in hp["hvn"] if lo <= h < hi]
    if not between:
        out["hvn_text"] = "none"
        return out
    h = min(between, key=lambda x: abs(x - entry))
    out["hvn"] = float(h)
    out["hvn_distance_pct"] = round(100.0 * abs(h - entry) / entry, 2)
    out["hvn_text"] = f"{_f(h)} ({out['hvn_distance_pct']:.1f}% from the entry)"
    return out


def draft(inst: dict, pv: dict, ctx: dict, cfg: dict, ending: str) -> dict:
    """One candidate in the register's draft shape, plus what prints beside it."""
    E = len(inst["close"]) - 1
    d = pv["d"]
    direction = "long" if d > 0 else "short"
    pcfg = cfg.get("pivots") or {}
    a, akind = atr(inst, E, int(pcfg.get("atr_sessions") or 14))
    buf = float(pcfg.get("invalidation_buffer_atr") or 0.25) * (a or 0.0)
    entry = inst["close"][E]
    inv = pv["inv_level"] - d * buf
    risk = (entry - inv) * d
    tr = trend(inst, E, cfg)
    against = (tr["state"] == "down" and d > 0) or (tr["state"] == "up" and d < 0)
    target = pv["level"] + d * pv["move"]
    # W8-7: no R off an invalidation nearer than the floor.
    floor = max(float(pcfg.get("r_floor_atr") or 0.5) * (a or 0.0),
                float(pcfg.get("r_floor_pct") or 0.5) / 100.0 * abs(entry))
    r_note = (None if risk >= floor else
              "R not computed: invalidation too near (within "
              f"{_f(floor)}, the larger of half an ATR and 0.5% of price)")
    r_mult = (target - entry) * d / risk if risk > 0 and r_note is None else None
    dc = cfg.get("draft") or {}
    mult, mwhy = multiplier(ctx["regime"], cfg)
    risk_pct = float(dc.get("risk_pct") or 0.75) * mult
    cap = ctx["capital"]
    risk_usd = round(cap * risk_pct / 100.0, 2)
    notional = risk_usd / (risk / entry) if risk > 0 else None
    # Liquidity: dollar ADV over 20 sessions against the position's notional.
    sc = cfg.get("score") or {}
    vols = [x for x in (dollar_volume(inst, j) for j in range(max(0, E - 19), E + 1))
            if x is not None]
    adv = mean(vols) if len(vols) >= 10 else None
    share = float(sc.get("max_adv_share") or 0.01)
    if adv and notional:
        liq = min(1.0, share / (notional / adv)) if notional / adv > share else 1.0
    else:
        liq = float(sc.get("liquidity_when_absent") or 0.5)
    b = pv.get("base")
    rng = float(((pcfg.get("base") or {}).get("max_range_pct")) or 10.0)
    nmax = int(((pcfg.get("base") or {}).get("max_sessions")) or 60)
    base_q = (max(0.0, 1 - b["range_pct"] / rng) * min(1.0, b["n"] / nmax)) if b else 0.0
    c = {"symbol": inst["symbol"], "d": d, "rs_pct": rs_percentile(
        inst, ctx["bench"], int(((cfg.get("confirmations") or {})
                                 .get("relative_strength") or {}).get("sessions") or 60))}
    confs = confirm(c, ctx, cfg)
    met = [x for x in confs if x["met"]]
    warns = [x["text"] for x in confs if x.get("warning")]
    unmet = [x for x in confs if x["met"] is False and not x.get("warning")]
    unread = [x for x in confs if x["met"] is None]
    comp = {"trend": tr["agree"][direction] / 4.0, "base": round(base_q, 4),
            "confirmations": min(1.0, len(met) / float(sc.get("full_confirmations") or 3)),
            "regime": float((((cfg.get("regime") or {}).get("alignment") or {})
                             .get(ctx["regime"].get("macro") or "") or {})
                            .get(direction, 0.5)),
            "liquidity": round(liq, 4)}
    setup = pv["setup"]
    vr = pv.get("volume_ratio")
    vtxt = (f"{vr:.1f}× volume" if vr is not None
            else "volume not stored — the volume leg unconfirmed"
            if pv.get("volume_unconfirmed") else None)
    name = PIVOT_NAMES[(setup, direction)]
    bp = pcfg.get("base") or {}
    vm = float((pcfg.get("volume") or {}).get("multiple") or 1.5)
    if setup == "breakout":
        head = (f"{name} of {b['n']} sessions (range {b['range_pct']:.1f}% of price) "
                f"through {_f(pv['level'])}" + (f" on {vtxt}" if vtxt else ""))
        params = (f"N {b['n']} (of {bp.get('min_sessions')}–{bp.get('max_sessions')}), "
                  f"range {b['range_pct']:.1f}% ≤ R {rng:g}%, "
                  + (f"volume {vr:.1f}× ≥ V {vm:g}×" if vr is not None
                     else f"V {vm:g}× not testable (volume not stored)"))
    elif setup == "reclaim":
        head = (f"{name}: {pv['level_label']} ({_f(pv['level'])}), "
                f"{'lost' if d > 0 else 'regained'} {pv['lost_sessions']} session(s) "
                f"earlier" + (f", on {vtxt}" if vtxt else ""))
        params = (f"L {int((pcfg.get('reclaim') or {}).get('window_sessions') or 10)} "
                  f"({'lost' if d > 0 else 'regained'} {pv['lost_sessions']} before), "
                  + (f"volume {vr:.1f}× ≥ V {vm:g}×" if vr is not None
                     else f"V {vm:g}× not testable (volume not stored)"))
    else:
        head = (f"{name}: a close {'below' if d > 0 else 'above'} the {b['n']}-session "
                f"{pv['level_label'].removeprefix('the ')} ({_f(pv['level'])}) on "
                f"{pv['pierced_on']}, back {'above' if d > 0 else 'below'} it in "
                f"{pv['back_in']} session(s)")
        params = (f"N {b['n']}, range {b['range_pct']:.1f}% ≤ R {rng:g}%, "
                  f"F {int((pcfg.get('failed_breakdown') or {}).get('window_sessions') or 5)}"
                  f" (back in {pv['back_in']})")
    thesis = "; ".join([head] + [x["text"] for x in confs
                                 if x["family"] in ("relative strength", "positioning")
                                 and x["met"] is not None])
    counter = "; ".join(warns + [f"unmet: {x['text']}" for x in unmet]
                        + [f"not read: {x['text']}" for x in unread]) or "none recorded"
    ts = int((cfg.get("trend") or {}).get("against_tape_time_stop") or 5) if against \
        else int(dc.get("time_stop_sessions") or 15)
    # THE CARD'S WORDS (Doctrine 5.2, the Gamma dial's Book B timing column),
    # with the state they were read under.
    gamma = ctx["regime"].get("gamma") or ""
    timing = ((cfg.get("regime") or {}).get("timing") or {}).get(gamma)
    cat, cat_date = _catalyst(inst["symbol"], ctx["calendar"], ending)
    # Doctrine/brief: the base low (breakout), the reclaimed level (reclaim),
    # the breakdown low (failed breakdown); mirrored for a short.
    inv_label = {"breakout": "the base " + ("low" if d > 0 else "high"),
                 "reclaim": pv["level_label"],
                 "failed_breakdown": "the breakdown low" if d > 0
                 else "the breakout high"}[setup]
    inv_txt = (f"{_f(inv)} ({inv_label} {_f(pv['inv_level'])}, "
               f"{'less' if d > 0 else 'plus'} a quarter of the {akind})")
    return {
        "candidate_id": candidate_id(ending, inst["symbol"], direction, setup),
        "instrument": inst["symbol"], "direction": direction,
        "thesis": thesis, "edge": dc.get("edge") or "trend and momentum",
        "horizon": f"{dc.get('horizon') or 'one to six weeks'}; time stop {ts} sessions",
        "size": (f"{risk_pct:.2f}% of capital at risk ({float(dc.get('risk_pct') or 0.75):g}%"
                 f" × {mult:g}: {mwhy}) = ${risk_usd:,.0f} of the ${cap:,.0f} paper "
                 f"capital"),
        # THE DOLLARS AT RISK, BY CODE (scanner follow-up 5, ruled with EL-2/3):
        # entry to invalidation at the printed size, on the paper capital in
        # config/risk_limits.yaml -- so a candidate the sitting takes is never
        # delayed at the order gate for a missing risk_usd.
        "risk_usd": risk_usd,
        "invalidation": inv_txt, "counter_thesis": counter,
        "setup_id": ctx["setups"].get(setup), "score": None,
        "catalyst": cat, "catalyst_date": cat_date, "decision_id": None,
        # Printed beside the candidate; not the register's fields.
        "pivot": setup, "entry": entry, "invalidation_level": inv,
        "expected_r": None if r_mult is None else round(r_mult, 2),
        "r_note": r_note,
        "against_tape": against, "time_stop": ts, "no_add": against,
        "trend": tr["state"], "warnings": warns, "entry_timing": timing,
        "entry_timing_state": gamma or None,
        "parameters": params, "confirmations": confs, "components": comp,
        "met": len(met), "risk": risk, "key": inst["key"], "pivot_day":
        inst["days"][pv["t"]],
        # VP-1 item 9: printed as one clause on the candidate line; the score,
        # the gates, the timing and the grading never read it.
        "volume_profile": volume_readings(inst, E, b, entry, risk, d)}


def gate(c: dict, ctx: dict, cfg: dict) -> Optional[str]:
    """None when the candidate stands; else why it is refused."""
    cc = cfg.get("confirmations") or {}
    reg = ctx["regime"]
    if reg.get("vol") == "Crisis":
        return "Book B is closed in a Crisis Volatility dial (the card)"
    if c["risk"] <= 0:
        return "the close is beyond its own invalidation"
    if c["direction"] == "short":
        ok, why = short_permitted(reg, cfg)
        if not ok:
            return why
        need = int(cc.get("short_needs") or 2)
    else:
        top = ctx["top_bottom"].get("signal") == "top"
        need = int(cc.get("long_needs_after_top" if top else "long_needs")
                   or (2 if top else 1))
    if c["met"] < need:
        return f"{c['met']} confirmation(s) of the {need} a {c['direction']} needs"
    return None


def timing_refusal(c: dict, cfg: dict) -> Optional[str]:
    """The card's timing as a gate (ruled 13 Oct 2026): None when the Gamma
    dial's state allows an entry; else the refusal, in the card's words. Read
    after gate(), so only a candidate that would otherwise stand is refused
    here -- and that one is still written to the ledger and graded."""
    rg = cfg.get("regime") or {}
    st = c.get("entry_timing_state")
    if st and st in (rg.get("refuse_timing") or []):
        return (f"the Gamma dial's {st}: “{c.get('entry_timing')}” "
                f"(the regime card, Doctrine 5.2)")
    return None


def graded(res: dict) -> list[dict]:
    """Every candidate the ledger grades: the standing ones and those refused
    on the card's timing alone."""
    return list(res.get("candidates") or []) + [
        r for r in res.get("refused") or [] if r.get("graded")]


# ---------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------
def scan(ending: str, db_path: Optional[str] = None, *, cutoff: Optional[str] = None,
         calendar: Optional[list] = None, walls: Optional[dict] = None,
         sessions: Optional[list] = None, regime: Optional[dict] = None,
         cfg: Optional[dict] = None) -> dict:
    """Every candidate the week's closes produce, ranked, with the refused and
    the skipped counted. Reads only."""
    cfg = cfg or load_config()
    cutoff = cutoff or (ending + "T23:59:59+00:00")
    try:
        from register.store import setup_ids                    # noqa: PLC0415
        declared = set(setup_ids())
    except Exception:                                           # noqa: BLE001
        declared = set()
    setups = {k: v for k, v in (cfg.get("setups") or {}).items() if v in declared}
    from . import bars as bars_mod                              # noqa: PLC0415
    with observations.ObservationStore(db_path) as st, \
            bars_mod.BarStore(db_path) as bst:
        insts, skipped = load_universe(st, ending, cutoff, cfg, bst)
        sess = sessions or sorted({d for i in insts for d in i["days"][-5:]})[-5:]
        by = _by_symbol(insts)
        bench_sym = symbol_of(((cfg.get("confirmations") or {}).get("relative_strength")
                               or {}).get("benchmark") or "yfinance.mkt_spy", cfg)
        try:
            from register.heat import load_limits               # noqa: PLC0415
            capital = float(((load_limits().get("capital_usd") or {}).get("value"))
                            or 300000)
        except Exception:                                       # noqa: BLE001
            capital = 300000.0
        ctx = {"regime": regime if regime is not None else regime_read(st, cutoff, cfg),
               "bench": by.get(bench_sym), "tells": tells(insts, cfg),
               "moves": move_flags(st, insts, sess, cutoff, cfg),
               "top_bottom": top_bottom(st, cutoff, ending, cfg),
               "breaks": correlation_breaks(st, cutoff, sess, cfg),
               "positioning": {i["symbol"]: positioning(st, i["symbol"], cutoff,
                                                        ending, cfg) for i in insts},
               "alt_assets": set((cfg.get("universe") or {}).get("alt_assets") or []),
               "calendar": calendar, "setups": setups, "capital": capital}
    cands, refused, undeclared = [], [], 0
    for inst in insts:
        pvs = detect(inst, cfg, (walls or {}).get(inst["symbol"]))
        if inst.get("breakout_skipped"):
            skipped.setdefault("breakout_not_scanned", []).append(
                {"symbol": inst["symbol"], "reason": inst["breakout_skipped"]})
        best: dict[int, dict] = {}
        # One pivot per direction: the latest; on the same session the more
        # specific -- a base cleared, then a base's edge failed, then a level.
        order = ["breakout", "failed_breakdown", "reclaim"]
        for pv in sorted(pvs, key=lambda p: (-p["t"], order.index(p["setup"]))):
            best.setdefault(pv["d"], pv)
        for pv in best.values():
            if pv["setup"] not in setups:
                undeclared += 1
                continue
            c = draft(inst, pv, ctx, cfg, ending)
            why = gate(c, ctx, cfg)
            if why:
                refused.append({**c, "refused": why})
                continue
            c["score"] = score(c["components"], cfg)
            why = timing_refusal(c, cfg)
            if why:
                refused.append({**c, "refused": why, "graded": True})
                continue
            cands.append(c)
    cands.sort(key=lambda c: (-c["score"], c["instrument"], c["direction"]))
    for n, c in enumerate(cands, start=1):
        c["rank"] = n
    top = int((cfg.get("score") or {}).get("print_top") or 10)
    return {"ending": ending, "config_version": cfg.get("version"),
            "candidates": cands, "printed": cands[:top], "reference": cands[top:],
            "refused": refused, "skipped": skipped, "undeclared_setups": undeclared,
            "universe_n": len(insts), "regime": ctx["regime"],
            "top_bottom_signal": ctx["top_bottom"].get("signal"),
            "hooks": {"move_screen": ctx["moves"] is not None,
                      "correlation_break": ctx["breaks"] is not None,
                      "top_bottom": ctx["top_bottom"]["available"]},
            "parameters": parameters_line(cfg)}


def candidates(ending: str, db_path: Optional[str] = None, **kw) -> list[dict]:
    """THE HOOK W-1.3a's block reads: every standing candidate, ranked."""
    return scan(ending, db_path, **kw)["candidates"]


def parameters_line(cfg: dict) -> str:
    pv = cfg.get("pivots") or {}
    b, v = pv.get("base") or {}, pv.get("volume") or {}
    return (f"Pivots as set: base N {b.get('min_sessions')}–{b.get('max_sessions')} "
            f"sessions, range R ≤ {b.get('max_range_pct')}% of price, volume V ≥ "
            f"{v.get('multiple')}× its {v.get('average_sessions')}-session average, "
            f"reclaim window L {(pv.get('reclaim') or {}).get('window_sessions')}, "
            f"failed-breakdown window F "
            f"{(pv.get('failed_breakdown') or {}).get('window_sessions')}; "
            f"invalidation a quarter of the average true range beyond its level "
            f"(session-set from the Technical Indicators paper; "
            f"{cfg.get('version')}). Changed {pv.get('changed') or 'n/a'}: the "
            f"breakout template scans no instrument without volume and no =X "
            f"currency pair, and a pair takes no RS against SPY; R is computed only "
            f"beyond an invalidation floor of the larger of "
            f"{pv.get('r_floor_atr', 0.5):g} ATR and {pv.get('r_floor_pct', 0.5):g}% "
            f"of price.")


# ---------------------------------------------------------------------------
# 8. Grading
# ---------------------------------------------------------------------------
_CRIT = re.compile(r"^(?P<key>\S+) closes after (?P<start>\d{4}-\d{2}-\d{2}): "
                   r"the first close at or (?P<dir>above|below) (?P<up>[\d.]+) "
                   r"resolves 1; the first close at or (?:above|below) "
                   r"(?P<down>[\d.]+) resolves 0")


def criterion(c: dict, ending: str, horizon: str) -> str:
    up = c["entry"] + (c["risk"] if c["direction"] == "long" else -c["risk"])
    down = c["entry"] - (c["risk"] if c["direction"] == "long" else -c["risk"])
    w1, w0 = ("above", "below") if c["direction"] == "long" else ("below", "above")
    return (f"{c['key']} closes after {ending}: the first close at or {w1} {up:.4f} "
            f"resolves 1; the first close at or {w0} {down:.4f} resolves 0; neither "
            f"by {horizon} resolves 0")


def record_forecasts(cands: list[dict], ending: str, emitted_at: str,
                     db_path: Optional[str], dry_run: bool,
                     cfg: Optional[dict] = None) -> list[str]:
    """Every candidate, taken or not, a forecast under its setup and id
    (decision 6). Restricted instruments never reach here (dropped at load),
    and are refused again at the write."""
    from . import probability_ledger as pl                      # noqa: PLC0415
    cfg = cfg or load_config()
    g = cfg.get("grading") or {}
    hz = (dt.date.fromisoformat(ending)
          + dt.timedelta(days=int(g.get("horizon_days") or 42))).isoformat()
    ids = []
    with pl.ProbabilityLedger(db_path) as led:
        for c in cands:
            if _restricted(c["instrument"]):
                continue
            ids.append(led.record(
                source=source_name(dry_run, cfg),
                claim=(f"Book B candidate {c['candidate_id']} ({c['setup_id']}): "
                       f"{c['instrument']} {c['direction']} from {c['entry']:.4f} on "
                       f"{ending} reaches +1R before -1R within six weeks"),
                probability=float(g.get("probability") or 0.5), horizon_date=hz,
                emitted_at=emitted_at, emitted_by="altdata.book_b_scanner",
                resolution_criterion=criterion(c, ending, hz)))
    return ids


def grade(db_path: Optional[str], ending: str, cutoff: Optional[str] = None,
          dry_run: bool = False, cfg: Optional[dict] = None) -> list[dict]:
    """Resolve every open candidate forecast in this namespace that the stored
    closes to `ending` decide: a barrier touched, or the horizon passed."""
    from . import probability_ledger as pl                      # noqa: PLC0415
    cfg = cfg or load_config()
    src = source_name(dry_run, cfg)
    out = []
    with pl.ProbabilityLedger(db_path) as led, \
            observations.ObservationStore(db_path) as st:
        for r in led.all_rows():
            if r["source"] != src or r.get("outcome") is not None:
                continue
            m = _CRIT.match(r["resolution_criterion"] or "")
            if not m:
                continue
            up, down = float(m["up"]), float(m["down"])
            sign = 1 if m["dir"] == "above" else -1
            outcome, note = None, None
            for d, v in _pts(st, m["key"], cutoff, min(ending, r["horizon_date"])):
                if d <= m["start"]:
                    continue
                if (v - up) * sign >= 0:
                    outcome, note = 1, f"+1R ({up:g}) first, {d}"
                    break
                if (v - down) * sign <= 0:
                    outcome, note = 0, f"-1R ({down:g}) first, {d}"
                    break
            if outcome is None and ending >= r["horizon_date"]:
                outcome, note = 0, f"neither by {r['horizon_date']}"
            if outcome is not None:
                out.append(led.resolve(r["probability_id"], outcome, note=note,
                                       resolved_at=session.utc_iso()))
    return out


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    ap = argparse.ArgumentParser(description="The Book B scanner (prints only).")
    ap.add_argument("--ending", required=True)
    a = ap.parse_args(argv)
    res = scan(a.ending)
    print(res["parameters"])
    for c in res["printed"]:
        print(f"{c['rank']}. {c['instrument']} {c['direction']} — {c['thesis']} "
              f"(score {c['score']:.2f})")
    print(f"universe {res['universe_n']}; candidates {len(res['candidates'])}; "
          f"refused {len(res['refused'])}")
    return 0


if __name__ == "__main__":                                      # pragma: no cover
    import sys
    raise SystemExit(_main(sys.argv[1:]))
