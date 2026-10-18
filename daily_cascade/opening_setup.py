"""
The opening setup, first half (decision D-3 of 18 Oct 2026; a44-opening-setup):
the elements that need only the dealer engine, the captures and the earnings
writer. OS-3, the volatility-regime lenses, lives in altdata/vol_event.py's lens
table.

    gauge(...) / gauge_from_store(prior, cutoff, db_path, computed_dir)
        OS-2, the expected-movement gauge, in the 07:00 anchor's dealer-surface
        block: the regime word as the engine prints it, the one-sigma range from
        our own implied range around the last close, and the typical realised
        range at this reading from the scorecard's stored sessions by regime
        ("awaiting (n=k of 20)" below 20)
    most_active(st, sessions, now)
        OS-10, the ten most active names of the week by options volume from our
        captures, in the Weekly's Mechanics
    with_pricing(row, now, db_path)
        OS-11, an Ahead earnings row's last three reactions and its pricing word
        against the matrix's own implied move

REPORT-ONLY (D-4): no 0-100 score and no weights; every rank prints its window
and n; the regime word and the numbers, never CALM / NORMAL / WILD; a pricing word
is printed with its three figures and is never a recommendation. THE VENDOR IS
NEVER READ: every input is the engine's profile, our captures, our stored closes
and the earnings writer's events (a gate greps these modules for the vendor's
source id). Settings: config/opening_setup.yaml, session-set.
"""

from __future__ import annotations

import json
import logging
import math
import re
import sqlite3
import statistics
from pathlib import Path
from typing import Any, Optional

import yaml

log = logging.getLogger(__name__)

CONFIG = Path(__file__).resolve().parent.parent / "config" / "opening_setup.yaml"


def config() -> dict:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def _pct(v: float, dp: int = 1) -> str:
    return f"{v:.{dp}f}%"


# ---------------------------------------------------------------------------
# OS-2 -- the expected-movement gauge
# ---------------------------------------------------------------------------
def typical_range(cards: list[dict], sign: Optional[str], cfg_dealer: dict,
                  sessions: int = 5) -> tuple[Optional[float], int]:
    """(median realised range %, n) over the `sessions` stored sessions from each
    stored session whose gated morning regime matches `sign`: the highest high
    less the lowest low over them, over the first session's prior close."""
    from . import dealer_block                                  # noqa: PLC0415
    if sign is None:
        return None, 0
    cs = sorted((c for c in cards if c.get("session")), key=lambda c: str(c["session"]))
    out = []
    for i, c in enumerate(cs):
        if dealer_block.regime_sign(c.get("net_gex_morning"), c.get("net_to_gross_morning"),
                                    cfg_dealer) != sign:
            continue
        win = cs[i:i + sessions]
        if len(win) < sessions or not c.get("prior_close"):
            continue
        hs = [w.get("session_high") for w in win]
        ls = [w.get("session_low") for w in win]
        if any(x is None for x in hs + ls):
            continue
        out.append(100.0 * (max(hs) - min(ls)) / float(c["prior_close"]))
    return (statistics.median(out) if out else None), len(out)


def gauge(profile: Optional[dict], last_close: Optional[tuple], iv: tuple,
          cards: list[dict], cfg: Optional[dict] = None,
          cfg_dealer: Optional[dict] = None) -> dict:
    """{line, values, constants}: the gauge as one line."""
    from . import dealer_block                                  # noqa: PLC0415
    cfg = cfg or config()
    g = cfg["gauge"]
    cd = cfg_dealer if cfg_dealer is not None else dealer_block.config()
    if not profile:
        return {"line": "Expected-movement gauge: no settled dealer profile for the prior "
                        "session.", "values": {}, "constants": []}
    o = profile.get("overall") or {}
    net, ntg = o.get("net_gex"), o.get("net_to_gross")
    word = dealer_block.regime(net, ntg, cd)
    sign = dealer_block.regime_sign(net, ntg, cd)
    vals: dict[str, Any] = {"session": profile.get("session_date")}
    head = f"Expected-movement gauge ({profile.get('symbol', 'SPY')}, the {profile.get('session_date')} settle): {word}"
    if ntg is not None and sign:
        head += f" (net-to-gross {ntg * 100:.0f}%)"
        vals["ntg_pct"] = ntg * 100
    iv_pct, iv_src = iv or (None, None)
    rng_s = "the one-sigma range: not read (no last close or no implied vol stored)"
    if last_close and iv_pct:
        d, c = last_close
        r = dealer_block.implied_range(c, iv_pct)
        vals.update(close=c, close_day=d, sigma=r, lower=c - r, upper=c + r, iv=iv_pct)
        if iv_src and "30-day" in iv_src:
            vals["iv_tenor_days"] = 30
        rng_s = (f"the one-sigma range from our implied range: {c - r:,.2f} to {c + r:,.2f} "
                 f"around the last close {c:,.2f} of {d} (±{r:.2f}, {iv_src} {iv_pct:.1f}%)")
    n_min, k = int(g["n_min"]), int(g["sessions"])
    med, n = typical_range(cards, sign, cd, k)
    vals.update(n=n, n_min=n_min, sessions=k)
    if sign is None:
        typ = "typical realised range at this reading: not read (the regime is not gated)"
    elif n >= n_min and med is not None:
        vals["typical"] = med
        typ = f"typical realised range at this reading: {med:.1f}% over {k} sessions (n={n})"
    else:
        typ = f"typical realised range at this reading: awaiting (n={n} of {n_min})"
    return {"line": f"{head}; {rng_s}; {typ}. Inferred, not observed; OI as of prior close.",
            "values": vals, "constants": [1]}


def gauge_from_store(prior: str, cutoff: str, db_path: Optional[str] = None,
                     computed_dir: Optional[str] = None) -> dict:
    """The gauge for the 07:00 anchor, read only. Never raises."""
    from altdata import observations                            # noqa: PLC0415
    from . import dealer_block                                  # noqa: PLC0415
    sym = config()["gauge"]["symbol"]
    try:
        profile = dealer_block.newest_settled(prior, sym, computed_dir)
    except Exception:                                           # noqa: BLE001
        profile = None
    try:
        with observations.ObservationStore(db_path) as st:
            cards = []
            for r in st.as_of("dealer.scorecard_day", cutoff, sym):
                try:
                    cards.append(json.loads(r["value_text"]))
                except (TypeError, ValueError):
                    continue
            lc = st.latest_as_of(f"yfinance.mkt_{sym.lower()}", cutoff)
            last = (str(lc["observed_at"])[:10], float(lc["value_num"])) if lc and \
                lc.get("value_num") is not None else None
            iv = dealer_block.implied_vol(st, cutoff)
        return gauge(profile, last, iv, cards)
    except Exception:                                           # noqa: BLE001
        log.warning("the expected-movement gauge faulted", exc_info=True)
        return {"line": "Expected-movement gauge: not read (its inputs faulted).",
                "values": {}, "constants": []}


# ---------------------------------------------------------------------------
# OS-3 every day (ruling 2 of 18 Oct on the a44 report): the three vol-regime
# lenses as three short lines beside the gauge -- level, percentile, window --
# from item 52's own lens functions; item 52's full table stays event-day only.
# ---------------------------------------------------------------------------
def _pv(ps) -> dict:
    """The percentiles by NAME (so the numeral audit's _ordinal siblings attach)
    and their n."""
    out = {}
    for i, (lab, p, n) in enumerate(ps or []):
        if p is not None:
            out[f"window{i}_percentile"], out[f"window{i}_n"] = p, n
    return out


def _audited(values: dict, day: str) -> dict:
    from altdata.numeral_audit import with_ordinals              # noqa: PLC0415
    return with_ordinals({**values, "as_of": day})


def vol_lines(series: dict, day: Optional[str]) -> list[dict]:
    """[{line, values, constants}] x 3: the VIX against 20-day realised, term-
    structure stress, the short-term spike. An absent input says so."""
    from altdata import vol_event as ve                         # noqa: PLC0415
    if not day:
        return [{"line": "Volatility regime: no VIX stored for the session.",
                 "values": {}, "constants": []}]
    cfg = ve.config()
    rl = ve.lens_realised(series.get("vix") or [], series.get("spx") or [], day, cfg)
    tm = ve.lens_term(series, day, cfg)
    sp = ve.lens_spike(series, day, cfg)
    out = []
    if rl.get("vrp") is not None:
        ps = rl.get("vrp_percentiles") or []
        out.append({"line": f"VIX against 20-day realised: {rl['vrp']:+.1f} points ("
                            f"{ve.pct_text(ps)}), as of {day}.",
                    "values": _audited({"vrp": rl["vrp"], **_pv(ps)}, day),
                    "constants": [20, 1, 5]})
    else:
        out.append({"line": f"VIX against 20-day realised: {rl.get('line', 'awaiting')}.",
                    "values": {}, "constants": [20]})
    if tm.get("state") == "computed":
        p3, p6 = tm.get("percentiles_3m") or [], tm.get("percentiles_6m") or []
        out.append({"line": f"Term-structure stress: VIX3M/VIX {tm['ratio_3m']:.3f} ("
                            f"{ve.pct_text(p3)}); VIX6M/VIX {tm['ratio_6m']:.3f} ("
                            f"{ve.pct_text(p6)}), as of {day}.",
                    "values": _audited({"r3": tm["ratio_3m"], "r6": tm["ratio_6m"],
                                        "vix3m": _pv(p3), "vix6m": _pv(p6)}, day),
                    "constants": [3, 6, 1, 5]})
    else:
        out.append({"line": f"Term-structure stress: {tm.get('line', 'awaiting')}.",
                    "values": {}, "constants": [3, 6, 9]})
    if sp.get("state") == "computed":
        ps = sp.get("percentiles") or []
        out.append({"line": f"Short-term spike: VIX9D/VIX {sp['ratio_9d']:.3f} ("
                            f"{ve.pct_text(ps)}), as of {day}.",
                    "values": _audited({"r9": sp["ratio_9d"], **_pv(ps)}, day),
                    "constants": [9, 1, 5]})
    else:
        out.append({"line": f"Short-term spike: {sp.get('line', 'awaiting')}.",
                    "values": {}, "constants": [9]})
    return out


def vol_lines_from_store(prior: str, cutoff: str, db_path: Optional[str] = None) -> list[dict]:
    from altdata import observations, vol_event as ve           # noqa: PLC0415
    try:
        with observations.ObservationStore(db_path) as st:
            series = ve.read_series(st, cutoff)
        days = [d for d, _ in series.get("vix") or [] if d <= prior]
        return vol_lines(series, days[-1] if days else None)
    except Exception:                                           # noqa: BLE001
        log.warning("the vol-regime lines faulted", exc_info=True)
        return [{"line": "Volatility regime: not read (its inputs faulted).",
                 "values": {}, "constants": []}]


def vol_lines_html(lines: Optional[list]) -> str:
    from html import escape                                     # noqa: PLC0415
    if not lines:
        return ""
    return "".join(f'<p style="font-size:12px;margin:2px 0">{escape(x["line"])}</p>'
                   for x in lines)


# Ruling 3 of 18 Oct: the pre-market line ("ES pre-market implies SPY about x")
# prints only if 6b part 3's ES conversion already ran from ES to SPY without new
# code. It does not -- altdata/dealer_es.py carries SPY's levels TO ES -- so the
# line prints nothing, and the notes list it.
PREMARKET_LINE = None


def gauge_html(g: Optional[dict]) -> str:
    from html import escape                                     # noqa: PLC0415
    if not g or not g.get("line"):
        return ""
    return f'<p style="font-size:13px;margin:6px 0">{escape(g["line"])}</p>'


# ---------------------------------------------------------------------------
# OS-10 -- the most-active names
# ---------------------------------------------------------------------------
def _series(st, key: str, now: str, inst=None) -> list[tuple[str, float]]:
    out: dict[str, float] = {}
    for r in st.as_of(key, now, inst) or []:
        if r.get("value_num") is not None:
            out[str(r["observed_at"])[:10]] = float(r["value_num"])
    return sorted(out.items())


def iv_rank(hist: list[float], x: float) -> Optional[float]:
    lo, hi = min(hist), max(hist)
    return None if hi == lo else 100.0 * (x - lo) / (hi - lo)


def iv_pctile(hist: list[float], x: float) -> float:
    return 100.0 * sum(1 for h in hist if h <= x) / len(hist)


def most_active(st, sessions: list[str], now: str, cfg: Optional[dict] = None,
                names: Optional[list[str]] = None) -> dict:
    """The Weekly's table: the week's ten most active names by options volume."""
    from altdata import chain_metrics as cm, config as acfg     # noqa: PLC0415
    from altdata.numeral_audit import ordinal                   # noqa: PLC0415
    cfg = cfg or config()
    m = cfg["most_active"]
    syms = names or acfg.chain_universe()
    week = set(sessions)
    vol: dict[str, float] = {}
    for s in syms:
        v = sum(x for d, x in _series(st, cm.VOL_KEY, now, s) if d in week)
        if v > 0:
            vol[s] = v
    top = sorted(vol, key=lambda s: -vol[s])[:int(m["top"])]
    rows, data = [], []
    for s in top:
        iv = _series(st, cm.FRONT_IV_KEY, now, s)
        hist = [x for _, x in iv]
        cur = iv[-1] if iv else None
        rank = iv_rank(hist, cur[1]) if cur and len(hist) > 1 else None
        pctl = iv_pctile(hist, cur[1]) if cur else None
        chg = (iv[-1][1] - iv[-2][1]) if len(iv) > 1 else None
        window = f"{iv[0][0]} to {iv[-1][0]}, n={len(iv)}" if iv else "none stored"
        px = [x for d, x in _series(st, f"yfinance.mkt_{s.lower()}", now) if d in week]
        imp = (100.0 * cur[1] / 100.0 * math.sqrt(int(m["week_sessions"]) / 252.0)
               if cur else None)
        real = (100.0 * (max(px) - min(px)) / px[0]) if len(px) > 1 and px[0] else None
        rows.append([s, f"{vol[s]:,.0f}",
                     f"{cur[1]:.1f}%" if cur else "not stored",
                     (f"rank {rank:.0f}, {ordinal(pctl)} percentile ({window})"
                      if rank is not None else f"one reading ({window})" if cur else "—"),
                     f"{chg:+.1f} pts" if chg is not None else "n/a",
                     (f"implied ±{imp:.1f}% against realised {real:.1f}%"
                      if imp is not None and real is not None else "n/a")])
        data.append({"symbol": s, "volume": vol[s], "iv": cur[1] if cur else None,
                     "rank": rank, "percentile": pctl, "n": len(iv), "iv_change": chg,
                     "implied_week_pct": imp, "realised_week_pct": real})
    first = min((d for s in syms for d, _ in _series(st, cm.FRONT_IV_KEY, now, s)), default=None)
    lines = ([f"The week's most active names by options volume, of {len(syms)} captured "
              f"names (our own captures; the universe's names and SPY, QQQ, IWM). Ranks and percentiles are over "
              f"our stored history only, which starts {first}: each prints its window and "
              f"n. Report-only: no score, no weight."]
             if top else ["No options volume stored for the week's sessions."])
    return {"title": "Most active names (options volume), the week",
            "table": {"columns": ["Name", "Options volume", "Front-month ATM IV",
                                  "IV rank and percentile (window, n)", "One-day IV change",
                                  "IV against the week's range"], "rows": rows} if rows else None,
            "lines": lines, "paragraph_wanted": False, "data": {"most_active": data},
            "table_note": ("Read from the store as of the cutoff; nothing fetched. No "
                           "chart, no paragraph (opening setup OS-10).")}


# ---------------------------------------------------------------------------
# OS-11 -- the earnings rows' pricing
# ---------------------------------------------------------------------------
def _ro(db_path: Optional[str]) -> Optional[sqlite3.Connection]:
    """A read-only connection to the store, or None when there is no file."""
    from altdata import observations                            # noqa: PLC0415
    p = Path(db_path or observations.DEFAULT_DB)
    if not p.is_file():
        return None
    return sqlite3.connect(f"file:{p.as_posix()}?mode=ro", uri=True)


def reactions(conn, symbol: str, before: str, now: str, n: int = 3) -> list[dict]:
    """The last `n` reports before `before` with their next-session reaction: the
    close before the report date to the close after it (the Weekly's earnings
    block's rule); "not stored" where a close is missing."""
    rows = conn.execute(
        "SELECT observed_at, payload FROM events WHERE type = 'earnings' AND "
        "observed_at < ? AND available_at <= ?", (before, now)).fetchall()
    reps = []
    for obs, payload in rows:
        try:
            pl = json.loads(payload or "{}")
        except ValueError:
            continue
        if str(pl.get("symbol") or "").upper() == symbol.upper() and \
                pl.get("reported_eps") is not None:
            reps.append(str(obs)[:10])
    reps = sorted(set(reps))[-n:]
    closes = dict(conn.execute(
        "SELECT substr(observed_at, 1, 10), value_num FROM observations WHERE "
        "registry_key = ? AND available_at <= ? AND value_num IS NOT NULL "
        "ORDER BY observed_at, available_at", (f"yfinance.mkt_{symbol.lower()}", now)).fetchall())
    days = sorted(closes)
    out = []
    for d in reps:
        b = next((closes[x] for x in reversed(days) if x < d), None)
        a = next((closes[x] for x in days if x > d), None)
        out.append({"date": d, "reaction_pct": (100.0 * (a / b - 1.0) if a and b else None)})
    return out


def pricing_word(implied: Optional[float], reacts: list[Optional[float]],
                 band: float = 0.20) -> tuple[Optional[str], Optional[float]]:
    """("elevated" | "muted" | "in line", the median absolute reaction) against
    the implied move, on three stored reactions; (None, None) when fewer."""
    xs = [abs(x) for x in reacts if x is not None]
    if implied is None or len(xs) < 3:
        return None, (statistics.median(xs) if xs else None)
    med = statistics.median(xs)
    if med == 0:
        return None, med
    if implied >= med * (1 + band):
        return "elevated", med
    if implied <= med * (1 - band):
        return "muted", med
    return "in line", med


MOVE_RE = re.compile(r"±\s*([\d.]+)%")


def with_pricing(r: dict, now: str, db_path: Optional[str] = None,
                 cfg: Optional[dict] = None) -> dict:
    """An Ahead earnings row with its last three reactions and pricing word
    appended to its consensus cell, the implied move being the matrix's own."""
    cfg = cfg or config()
    e = cfg["earnings"]
    sym = r.get("symbol") or str(r.get("event") or "").split(" ")[0]
    m = MOVE_RE.search(str(r.get("implied_move") or ""))
    implied = float(m.group(1)) if m else None
    try:
        conn = _ro(db_path)
    except sqlite3.Error:
        conn = None
    if conn is None:
        txt = "; last three reactions: not stored"
        return {**r, "pricing": {"reactions": [], "word": None},
                "consensus": f"{r.get('consensus') or '—'}{txt}"}
    try:
        reacts = reactions(conn, sym, str(r.get("date"))[:10], now, int(e["reactions"]))
    finally:
        conn.close()
    figs = [x["reaction_pct"] for x in reacts]
    cells = [f"{x:+.1f}%" if x is not None else "not stored" for x in figs]
    cells += ["not stored"] * (int(e["reactions"]) - len(cells))
    word, med = pricing_word(implied, figs, float(e["band"]))
    txt = f"; last three reactions: {', '.join(cells)}"
    if word:
        txt += (f"; pricing {word}: implied ±{implied:.1f}% against a median absolute "
                f"reaction of {med:.1f}% (a fifth either way is in line; not a "
                f"recommendation)")
    elif implied is not None:
        txt += "; pricing: not read (three reactions are not stored)"
    return {**r, "consensus": f"{r.get('consensus') or '—'}{txt}",
            "pricing": {"reactions": reacts, "word": word, "median": med,
                        "implied": implied}}
