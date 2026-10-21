"""
The opening setup, first half (decision D-3 of 18 Oct 2026; a44-opening-setup):
the elements that need only the dealer engine, the captures and the earnings
writer. OS-3, the volatility-regime lenses, lives in altdata/vol_event.py's lens
table (and, by ruling 2 of 18 Oct, three daily lines here, vol_lines).

THE SECOND HALF (a45-opening-setup-2): OS-8 profiles() the setup profiles (the
Weekly); OS-9 oi_builds_from_store() "Largest OI builds, side unknown" (the
anchor); OS-4 index_put_lines() for SPY and SPX (the anchor); OS-5
single_name_puts() (the Weekly). No side is ever inferred.

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
REPO = Path(__file__).resolve().parent.parent

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


# ITEM 54 (Batch 11, ruled 19 Oct 2026): LIKE FOR LIKE. The implied move and the
# realised distribution on the same horizon and the same measure -- the close x the
# 30-day ATM IV x sqrt(h/252) beside the absolute close-to-close move over h
# sessions in the gated regime (median, 80th, 95th, n). The high-low range stays
# only against the implied EXPECTED range of a high-low range (a random walk's,
# sqrt(8/pi) x sigma x sqrt(h/252)), and says so. Every sample is split: the test
# sample (live rows from the registration date) and the rest, "before
# registration, descriptive" -- the backfilled rows among them.
RW_RANGE = math.sqrt(8.0 / math.pi)
BEFORE = "before registration, descriptive"


def registered_on(cfg_scorecard: Optional[dict] = None) -> str:
    """The scorecard's registration date (its test sample starts here)."""
    if cfg_scorecard is None:
        from altdata import dealer_scorecard as dsc               # noqa: PLC0415
        cfg_scorecard = dsc.config()
    return str(cfg_scorecard.get("registered_on") or "2026-10-17")[:10]


def in_test(card: dict, reg: str) -> bool:
    """A live row on or after the registration date. A backfilled row never is."""
    return not card.get("backfilled") and str(card.get("session"))[:10] >= reg


def quantile(xs: list[float], q: float) -> float:
    """Linear interpolation between closest ranks (q in [0, 1])."""
    s = sorted(xs)
    if len(s) == 1:
        return s[0]
    pos = q * (len(s) - 1)
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def _gated(cards: list[dict], sign: Optional[str], cd: dict) -> list[int]:
    from . import dealer_block                                  # noqa: PLC0415
    return [i for i, c in enumerate(cards)
            if sign is not None and dealer_block.regime_sign(
                c.get("net_gex_morning"), c.get("net_to_gross_morning"), cd) == sign]


def realised_moves(cards: list[dict], sign: Optional[str], cd: dict, h: int,
                   reg: str) -> list[tuple[float, bool]]:
    """[(|close-to-close move| %, in the test sample)] over h sessions from each
    gated session: the h-th session's close over the first session's prior close."""
    cs = sorted((c for c in cards if c.get("session")), key=lambda c: str(c["session"]))
    out = []
    for i in _gated(cs, sign, cd):
        win = cs[i:i + h]
        p0, c1 = cs[i].get("prior_close"), (win[-1] if len(win) == h else {}).get("close")
        if len(win) < h or not p0 or c1 is None:
            continue
        out.append((100.0 * abs(float(c1) / float(p0) - 1.0), in_test(cs[i], reg)))
    return out


def realised_ranges(cards: list[dict], sign: Optional[str], cd: dict, h: int,
                    reg: str) -> list[tuple[float, bool]]:
    """[(high-low range %, in the test sample)] over h sessions from each gated
    session, over its prior close (the typical range, split by sample)."""
    cs = sorted((c for c in cards if c.get("session")), key=lambda c: str(c["session"]))
    out = []
    for i in _gated(cs, sign, cd):
        win = cs[i:i + h]
        if len(win) < h or not cs[i].get("prior_close"):
            continue
        hs, ls = [w.get("session_high") for w in win], [w.get("session_low") for w in win]
        if any(x is None for x in hs + ls):
            continue
        out.append((100.0 * (max(hs) - min(ls)) / float(cs[i]["prior_close"]),
                    in_test(cs[i], reg)))
    return out


def _counts(xs: list[tuple[float, bool]]) -> str:
    t = sum(1 for _, x in xs if x)
    return f"n={len(xs)}: {t} since registration, {len(xs) - t} {BEFORE}"


def net_gex_percentile(net: Optional[float], cards: list[dict]) -> Optional[dict]:
    """Net GEX's own-history percentile against the stored closes' net GEX (every
    scorecard row, either sample): the share at or below, with window and n."""
    hist = sorted(((str(c["session"])[:10], float(c["net_gex_close"])) for c in cards
                   if c.get("session") and c.get("net_gex_close") is not None))
    if net is None or not hist:
        return None
    vals = [v for _, v in hist] + [float(net)]
    pct = 100.0 * sum(1 for v in vals if v <= net) / len(vals)
    return {"pct": pct, "n": len(vals), "first": hist[0][0], "last": hist[-1][0]}


def gauge(profile: Optional[dict], last_close: Optional[tuple], iv: tuple,
          cards: list[dict], cfg: Optional[dict] = None,
          cfg_dealer: Optional[dict] = None, premarket: Optional[float] = None,
          reg: Optional[str] = None) -> dict:
    """{line, lines, values, constants}: the gauge, a few short lines (item 54)."""
    from altdata.numeral_audit import ordinal                   # noqa: PLC0415
    from . import dealer_block                                  # noqa: PLC0415
    cfg = cfg or config()
    g = cfg["gauge"]
    cd = cfg_dealer if cfg_dealer is not None else dealer_block.config()
    reg = reg or registered_on()
    if not profile:
        msg = "Expected-movement gauge: no settled dealer profile for the prior session."
        return {"line": msg, "lines": [msg], "values": {}, "constants": []}
    o = profile.get("overall") or {}
    net, ntg = o.get("net_gex"), o.get("net_to_gross")
    word = dealer_block.regime(net, ntg, cd)
    sign = dealer_block.regime_sign(net, ntg, cd)
    vals: dict[str, Any] = {"session": profile.get("session_date")}
    head = (f"Expected-movement gauge ({profile.get('symbol', 'SPY')}, the "
            f"{profile.get('session_date')} settle): {word}")
    if ntg is not None and sign:
        head += f" (net-to-gross {ntg * 100:.0f}%)"
        vals["ntg_pct"] = ntg * 100
    pg = net_gex_percentile(net, cards)
    if pg:
        vals.update(net_gex_pct=pg["pct"], net_gex_pct_ordinal=ordinal(pg["pct"]),
                    net_gex_n=pg["n"], net_gex_first=pg["first"], net_gex_last=pg["last"])
        head += (f"; net GEX at the {ordinal(pg['pct'])} percentile of its own history "
                 f"({pg['first']} to {pg['last']}, n={pg['n']})")
    lines = [head + ". Inferred, not observed; OI as of prior close."]
    iv_pct, iv_src = iv or (None, None)
    n_min = int(g["n_min"])
    horizons = [int(x) for x in g.get("horizons") or [1, 5]]
    vals.update(n_min=n_min, iv=iv_pct)
    if not (last_close and iv_pct):
        lines.append("Implied moves: not read (no last close or no implied vol stored).")
        return {"line": " ".join(lines), "lines": lines, "values": vals, "constants": [1]}
    d, c = last_close
    vals.update(close=c, close_day=d)
    sig = {h: c * iv_pct / 100.0 * math.sqrt(h / 252.0) for h in horizons}
    for h in horizons:
        s_pct = 100.0 * sig[h] / c
        vals.update({f"sigma_{h}": sig[h], f"sigma_{h}_pct": s_pct})
        lab = "one-session" if h == 1 else f"{h}-session"
        imp = (f"Implied {lab} move: ±{sig[h]:.2f} (±{s_pct:.2f}%; the close {c:,.2f} x "
               f"{iv_src} {iv_pct:.1f}% x sqrt({h}/252))")
        mv = realised_moves(cards, sign, cd, h, reg)
        vals[f"realised_{h}_n"] = len(mv)
        vals[f"realised_{h}_n_test"] = sum(1 for _, x in mv if x)
        vals[f"realised_{h}_n_before"] = sum(1 for _, x in mv if not x)
        if sign is None:
            rl = "realised: not read (the regime is not gated)"
        elif len(mv) >= n_min:
            xs = [x for x, _ in mv]
            m, p80, p95 = quantile(xs, 0.5), quantile(xs, 0.8), quantile(xs, 0.95)
            vals.update({f"realised_{h}_median": m, f"realised_{h}_p80": p80,
                         f"realised_{h}_p95": p95})
            rl = (f"realised |close-to-close| over {h} session{'s' if h > 1 else ''} in "
                  f"{sign} gamma: median {m:.2f}%, 80th {p80:.2f}%, 95th "
                  f"{p95:.2f}% ({_counts(mv)})")
        else:
            rl = f"realised: awaiting (n={len(mv)} of {n_min}; {_counts(mv)})"
        lines.append(f"{imp}; {rl}.")
    # The high-low range, against the implied expected range of that measure.
    k = int(g["sessions"])
    rr = realised_ranges(cards, sign, cd, k, reg)
    exp_rng = RW_RANGE * iv_pct * math.sqrt(k / 252.0)
    vals.update(expected_range_pct=exp_rng, sessions=k, n=len(rr),
                range_n_test=sum(1 for _, x in rr if x),
                range_n_before=sum(1 for _, x in rr if not x))
    if sign is not None and len(rr) >= n_min:
        med = statistics.median(x for x, _ in rr)
        vals["typical"] = med
        lines.append(f"{k}-session high-low range: median {med:.1f}% ({_counts(rr)}) against "
                     f"an implied expected high-low range of {exp_rng:.1f}% (a random walk's "
                     f"at the same IV: sqrt(8/pi) x IV x sqrt({k}/252)).")
    elif sign is not None:
        lines.append(f"{k}-session high-low range: awaiting (n={len(rr)} of {n_min}; "
                     f"{_counts(rr)}); its implied expected range {exp_rng:.1f}%.")
    # The bands (item 55): each labelled by its horizon and its centre.
    centres = [("the last close", c)] + ([("the pre-market", premarket)] if premarket else [])
    for cname, cv in centres:
        parts = []
        for h in horizons:
            sh = cv * iv_pct / 100.0 * math.sqrt(h / 252.0)
            tag = "pm" if cname != "the last close" else "close"
            vals[f"band_{h}_{tag}_lower"], vals[f"band_{h}_{tag}_upper"] = cv - sh, cv + sh
            parts.append(f"{'one-session' if h == 1 else f'{h}-session'} {cv - sh:,.2f} to "
                         f"{cv + sh:,.2f}")
        lines.append(f"±1σ bands around {cname} {cv:,.2f}: " + "; ".join(parts) + ".")
    # The quantile labels and the formula's constants are printed numbers too.
    return {"line": " ".join(lines), "lines": lines, "values": vals,
            "constants": [1, 5, 8, 80, 95, 252]}


def gauge_from_store(prior: str, cutoff: str, db_path: Optional[str] = None,
                     computed_dir: Optional[str] = None,
                     premarket: Optional[float] = None) -> dict:
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
        return gauge(profile, last, iv, cards, premarket=premarket)
    except Exception:                                           # noqa: BLE001
        log.warning("the expected-movement gauge faulted", exc_info=True)
        msg = "Expected-movement gauge: not read (its inputs faulted)."
        return {"line": msg, "lines": [msg], "values": {}, "constants": []}


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
    sp_line = premium_split(series, day, rl.get("vrp"))
    if sp_line:
        out.append(sp_line)
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


# ITEM 53 (Batch 11, ruled 19 Oct 2026): THE VIX PREMIUM, SPLIT. One line in
# OS-3's realised lens: VIX less RV20 = (SPY's 30-day ATM IV less RV20), the
# at-the-money part, + (VIX less SPY's 30-day ATM IV), the wings. SPY's ATM IV
# stands for SPX's, labelled. It displaces nothing.
SPLIT_LABEL = "SPY's ATM IV as SPX's proxy"


def premium_split(series: dict, day: str, vrp: Optional[float]) -> Optional[dict]:
    """The split line, or None when the VIX premium or SPY's IV is not stored."""
    vix = dict(series.get("vix") or []).get(day)
    iv = dict(series.get("spy_iv30") or []).get(day)
    if vrp is None or vix is None or iv is None:
        return None
    rv20 = vix - vrp
    atm, wings = iv - rv20, vix - iv
    return {"line": f"The VIX premium, split: VIX less RV20 {vrp:+.1f} = the at-the-money "
                    f"part {atm:+.1f} (SPY's 30-day ATM IV {iv:.1f} less RV20 {rv20:.1f}) + "
                    f"the wings {wings:+.1f} (VIX {vix:.1f} less SPY's ATM IV); "
                    f"{SPLIT_LABEL}, as of {day}.",
            "values": {"vrp": vrp, "atm": atm, "wings": wings, "iv": iv, "rv20": rv20,
                       "vix": vix, "as_of": day},
            "constants": [20, 30]}


def vol_lines_from_store(prior: str, cutoff: str, db_path: Optional[str] = None) -> list[dict]:
    from altdata import observations, vol_event as ve           # noqa: PLC0415
    try:
        with observations.ObservationStore(db_path) as st:
            series = ve.read_series(st, cutoff)
            series["spy_iv30"] = [(str(r["observed_at"])[:10], float(r["value_num"]))
                                  for r in st.as_of("chain.spy_atm_iv_30d", cutoff)
                                  if r.get("value_num") is not None]
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


# THE PRE-MARKET LINE (ruling 4 of 19 Oct 2026; ruling 3 of 18 Oct had held it
# back). ES's overnight print, put in SPY's terms through the SAME session basis
# the 23-hour chart (W7, daily_cascade/charts.py) uses -- SPY's 09:30 open over
# ES's 09:30 open -- applied the other way, ES to SPY. No new conversion method:
# the basis is W7's, read from the newest session before this one that has both
# opens (at 07:00 the day's own 09:30 has not happened). "Not available" when ES
# has no overnight bar, or no session carries both opens.
PREMARKET_LINE = "Pre-market (ES)"
# SPX AND SPCX (ruling 4 of 19 Oct 2026): their rows print, from the vendor's
# 16:31 chains, but every cell that needs a solved IV -- the chance in the money
# and the IV itself -- prints this, until tools/validate_iv_solver.py admits them.
SOLVER_GATED = "awaiting the solver gate"
# OS-12's tag in OS-9's Context column (Batch 13 item 61, D4).
VOLUME_FLAG_TAG = "volume flag yesterday"
PREMARKET_NA = "Pre-market (ES): not available ({why})."


def premarket(es5: list, spy5: list, session_day: str) -> dict:
    """{line, values}: ES's latest overnight print for `session_day` in SPY's
    terms at W7's session basis. Never raises on missing data."""
    from .charts import es_at_open, es_overnight                # noqa: PLC0415
    on = es_overnight(es5 or [], session_day)
    if not on:
        return {"line": PREMARKET_NA.format(why="ES has no overnight bar"), "values": {}}
    es_last = on[-1]["close"]
    days = sorted({str(b["observed_at"])[:10] for b in (spy5 or [])
                   if str(b["observed_at"])[:10] < session_day}, reverse=True)
    for d in days:
        # es_at_open reads the 09:30 ET bar's open of any 5-minute series.
        s_open, e_open = es_at_open(spy5, d), es_at_open(es5 or [], d)
        if s_open and e_open:
            basis = s_open / e_open
            spy = es_last * basis
            return {"line": (f"{PREMARKET_LINE}: ES's overnight print {es_last:,.2f} "
                             f"puts SPY at about {spy:,.2f}, at the {d} session's "
                             f"basis (SPY's 09:30 open over ES's, as the 23-hour chart "
                             f"scales it). Inferred, not a SPY trade."),
                    "values": {"es": es_last, "spy": spy, "basis": basis,
                               "basis_session": d}}
    return {"line": PREMARKET_NA.format(
        why="no session before this one carries both SPY's and ES's 09:30 opens"),
        "values": {"es": es_last}}


def premarket_from_store(session_day: str, cutoff: str,
                         db_path: Optional[str] = None) -> dict:
    """The pre-market line for the 07:00 anchor, from the bars the 06:45 job
    stored, read as of the cutoff. Never a fetch; never raises."""
    import datetime as dt                                       # noqa: PLC0415
    from altdata import bars as bars_mod                        # noqa: PLC0415
    try:
        session_day = str(session_day)[:10]
        first = (dt.date.fromisoformat(session_day) - dt.timedelta(days=10)).isoformat()
        with bars_mod.BarStore(db_path) as bst:
            es5 = bst.read("es", "5m", first, cutoff, cutoff)
            spy5 = bst.read("spy", "5m", first, cutoff, cutoff)
        return premarket(es5, spy5, session_day)
    except Exception:                                           # noqa: BLE001
        log.warning("the pre-market line faulted", exc_info=True)
        return {"line": PREMARKET_NA.format(why="its inputs faulted"), "values": {}}


def lines_html(b: Optional[dict]) -> str:
    """A small titled block of code-written lines (H6's clusters)."""
    from html import escape                                     # noqa: PLC0415
    if not b or not b.get("lines"):
        return ""
    return (f'<p style="font-size:12px;margin:6px 0 2px 0"><b>{escape(b["title"])}</b></p>'
            + "".join(f'<p style="font-size:12px;margin:2px 0">{escape(x)}</p>'
                      for x in b["lines"]))


def gauge_html(g: Optional[dict]) -> str:
    from html import escape                                     # noqa: PLC0415
    if not g or not g.get("line"):
        return ""
    # Item 54: the gauge is a few short lines; the pre-market line one.
    return "".join(f'<p style="font-size:13px;margin:6px 0">{escape(x)}</p>'
                   for x in (g.get("lines") or [g["line"]]))


# ---------------------------------------------------------------------------
# OS-10 -- the most-active names
# ---------------------------------------------------------------------------
def _series(st, key: str, now: str, inst=None) -> list[tuple[str, float]]:
    """A name's stored readings, oldest first. D4 (Batch 11): rows from the
    flat-file backfill join only where altdata.flatfile_history admits them (their
    overlap with our captures agrees within the pre-registered tolerance); a
    captured reading wins on a shared session."""
    from altdata import flatfile_history as ffh                 # noqa: PLC0415
    out, _ = ffh.merged(ffh.rows_both(st, key, now, inst), key)
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
    gated = set(acfg.massive_universe())
    syms = names or (acfg.chain_universe() + sorted(gated))
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
        if s in gated:
            # SPX and SPCX (ruling 4 of 19 Oct 2026): volume from the vendor's
            # chains; every IV cell awaits the solver gate.
            rows.append([s, f"{vol[s]:,.0f}", SOLVER_GATED, SOLVER_GATED, "n/a", "n/a"])
            data.append({"symbol": s, "volume": vol[s], "iv": None,
                         "solver_gated": True})
            continue
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
              f"names (our own captures; the universe's names and SPY, QQQ, IWM; SPX and SPCX "
              f"from the vendor's chains, their IV awaiting the solver gate). Ranks and percentiles are over "
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
    block's rule); "not stored" where a close is missing. A store without the
    events table reads as nothing stored, never a fault."""
    try:
        rows = conn.execute(
            "SELECT observed_at, payload FROM events WHERE type = 'earnings' AND "
            "observed_at < ? AND available_at <= ?", (before, now)).fetchall()
    except sqlite3.Error:
        return []
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
    try:
        closes = dict(conn.execute(
            "SELECT substr(observed_at, 1, 10), value_num FROM observations WHERE "
            "registry_key = ? AND available_at <= ? AND value_num IS NOT NULL "
            "ORDER BY observed_at, available_at",
            (f"yfinance.mkt_{symbol.lower()}", now)).fetchall())
    except sqlite3.Error:
        closes = {}
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


def stored_moves(conn, symbol: str, now: str, n: int = 3) -> list[dict]:
    """Item 57's records (calc.earnings_move): the implied move at the close before
    each past report and the realised move after it, newest last."""
    try:
        rows = conn.execute(
            "SELECT observed_at, value_text FROM observations WHERE registry_key = ? "
            "AND instrument = ? AND available_at <= ? ORDER BY observed_at",
            ("calc.earnings_move", symbol.upper(), now)).fetchall()
    except sqlite3.Error:
        return []
    out = []
    for d, txt in rows:
        try:
            out.append({"date": str(d)[:10], **json.loads(txt or "{}")})
        except ValueError:
            continue
    return out[-n:]


def msci_events(now: str) -> list[str]:
    """Item 57 (item 49): the MSCI index events in the hand-seeded digital-asset
    calendar from `now` on, each its date and the event's first clause."""
    try:
        doc = yaml.safe_load((REPO / "config" / "digital_asset_calendar.yaml")
                             .read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return []
    out = []
    for e in doc.get("entries") or []:
        if str(e.get("body")) == "MSCI" and str(e.get("date")) >= now[:10]:
            out.append(f"{e['date']} ({str(e.get('event') or '').split(',')[0]})")
    return out


def with_pricing(r: dict, now: str, db_path: Optional[str] = None,
                 cfg: Optional[dict] = None) -> dict:
    """An Ahead earnings row with up to eight reactions (config), n printed, and
    the pricing word on their median (n of 3 or more; else "n=k, no word"),
    appended to its consensus cell, the implied move being the matrix's own (Batch
    11 item 57); the stored implied-against-realised records beside them; and,
    for MSTR, the MSCI index events stored in the digital-asset calendar."""
    cfg = cfg or config()
    e = cfg["earnings"]
    n_max, n_min = int(e["reactions"]), int(e.get("word_min_n", 3))
    sym = r.get("symbol") or str(r.get("event") or "").split(" ")[0]
    m = MOVE_RE.search(str(r.get("implied_move") or ""))
    implied = float(m.group(1)) if m else None
    try:
        conn = _ro(db_path)
    except sqlite3.Error:
        conn = None
    reacts, moves = [], []
    if conn is not None:
        try:
            reacts = reactions(conn, sym, str(r.get("date"))[:10], now, n_max)
            moves = stored_moves(conn, sym, now)
        finally:
            conn.close()
    figs = [x["reaction_pct"] for x in reacts]
    avail = [x for x in figs if x is not None]
    k = len(avail)
    if avail:
        txt = (f"; reactions (n={k}, up to {n_max}): "
               + ", ".join(f"{x:+.1f}%" for x in avail))
    else:
        txt = "; reactions: not stored"
    word, med = pricing_word(implied, avail, float(e["band"]))
    if word and k >= n_min:
        txt += (f"; pricing {word}: implied ±{implied:.1f}% against a median absolute "
                f"reaction of {med:.1f}% (n={k}; a fifth either way is in line; not a "
                f"recommendation)")
    elif implied is not None:
        txt += f"; pricing: n={k}, no word"
    if moves:
        txt += "; implied against realised at past prints: " + ", ".join(
            f"{x['date']} ±{x['implied_pct']:.1f}% vs {x['realised_pct']:+.1f}%"
            for x in moves if x.get("implied_pct") is not None
            and x.get("realised_pct") is not None)
    if sym.upper() == "MSTR":
        ev = msci_events(now)
        if ev:
            txt += "; MSCI index events: " + "; ".join(ev)
    return {**r, "consensus": f"{r.get('consensus') or '—'}{txt}",
            "pricing": {"reactions": reacts, "word": word if k >= n_min else None,
                        "median": med, "implied": implied, "n": k,
                        "stored_moves": moves}}


# ===========================================================================
# THE SECOND HALF (a45-opening-setup-2, 18 Oct 2026): OS-8, OS-9, OS-4, OS-5.
# No score, no weight, NO SIDE: the OI-build table is "Largest OI builds, side
# unknown" and never infers who bought; the put-volume measures are "put volume
# and OI build, no side" and feed nothing but their own rows.
# ===========================================================================
NO_SIDE = "put volume and OI build, no side"
OI_TITLE = "Largest OI builds, side unknown"


def _hist_read(st, key: str, now: str, inst: str) -> tuple[Optional[tuple], list]:
    s = _series(st, key, now, inst)
    return (s[-1] if s else None), s


def _rank_text(s: list[tuple[str, float]], x: float) -> str:
    from altdata.numeral_audit import ordinal                   # noqa: PLC0415
    hist = [v for _, v in s]
    win = f"{s[0][0]} to {s[-1][0]}, n={len(s)}"
    r = iv_rank(hist, x) if len(hist) > 1 else None
    if r is None:
        return f"one reading ({win})"
    return f"rank {r:.0f}, {ordinal(iv_pctile(hist, x))} percentile ({win})"


def _latest_text(st, key: str, now: str, inst: str) -> Optional[str]:
    rows = [r for r in st.as_of(key, now, inst) or [] if r.get("value_text")]
    return rows[-1]["value_text"] if rows else None


# ---------------------------------------------------------------------------
# OS-8 -- the setup profiles
# ---------------------------------------------------------------------------
def iv30_less_rv20(st, now: str, sym: str) -> list[tuple[str, float]]:
    """Item 56: the 30-day IV less 20-session realised, matched by date."""
    from altdata import chain_metrics as cm                     # noqa: PLC0415
    rv = dict(_series(st, cm.RV20_KEY, now, sym))
    return [(d, v - rv[d]) for d, v in _series(st, cm.IV30_KEY, now, sym) if d in rv]


IV30_RV = "iv30_less_rv20"


def profiles(st, now: str, names: Optional[list[str]] = None,
             cfg: Optional[dict] = None) -> dict:
    """The Weekly's four-row table: the flattest and the steepest 25-delta put
    skew, the highest and the lowest 30-day IV against 20-day realised (Batch 11
    item 56: the 30-day constant-maturity IV, no longer the front month's)."""
    from altdata import chain_metrics as cm, config as acfg     # noqa: PLC0415
    syms = names or acfg.chain_universe()
    reads: dict[str, dict] = {}
    for s in syms:
        last, hist = _hist_read(st, cm.SKEW_KEY, now, s)
        if last:
            reads.setdefault(cm.SKEW_KEY, {})[s] = (last, hist)
        hist = iv30_less_rv20(st, now, s)
        if hist:
            reads.setdefault(IV30_RV, {})[s] = (hist[-1], hist)
    rows, data = [], []
    spec = (("Flattest 25-delta put skew", cm.SKEW_KEY, min),
            ("Steepest 25-delta put skew", cm.SKEW_KEY, max),
            ("Highest 30-day IV against 20-day realised", IV30_RV, max),
            ("Lowest 30-day IV against 20-day realised", IV30_RV, min))
    for label, key, pick in spec:
        got = reads.get(key) or {}
        if not got:
            rows.append([label, "—", "not stored", "—", "—"])
            continue
        s = pick(got, key=lambda n: got[n][0][1])
        (d, v), hist = got[s]
        rows.append([label, s, f"{v:+.1f} vol points", _rank_text(hist, v),
                     _latest_text(st, cm.FRONT_EXP_KEY, now, s) or "not stored"])
        data.append({"profile": label, "symbol": s, "value": v, "as_of": d, "n": len(hist)})
    return {"title": "Setup profiles (front month)",
            "table": {"columns": ["Profile", "Name", "Figure", "Rank and percentile "
                                  "(window, n)", "Front-month expiry used"], "rows": rows},
            "lines": [f"Across {len(syms)} captured names (our own captures; SPY, QQQ and "
                      f"IWM among them): the 25-delta put skew is the solved put IV at -25 "
                      f"delta less the ATM IV, and IV against realised is the 30-day "
                      f"constant-maturity ATM IV less 20-session realised, both in vol points. Each rank is over the "
                      f"name's own stored history, its window and n printed. Report-only."],
            "paragraph_wanted": False, "data": {"setup_profiles": data},
            "table_note": "Read from the store; nothing fetched. No chart, no paragraph (OS-8)."}


# ---------------------------------------------------------------------------
# ITEM 56 -- the per-name volatility table (the Weekly's technical appendix)
# ---------------------------------------------------------------------------
def _rank_pct(hist: list[tuple[str, float]], x: float) -> str:
    from altdata.numeral_audit import ordinal                   # noqa: PLC0415
    vals = [v for _, v in hist]
    if len(vals) < 2:
        return "one reading"
    return f"{ordinal(iv_pctile(vals, x))}"


def per_name_table(st, now: str, names: Optional[list[str]] = None) -> dict:
    """Batch 11 item 56: one row per captured name (17): the 30-day IV with its IV
    rank and IV percentile, the 25-delta put skew and the risk reversal with their
    percentiles, IV less RV20, RV20 and RV60, each against the name's own stored
    history, window and n printed. Descriptive words only; no strategy label."""
    from altdata import chain_metrics as cm, config as acfg     # noqa: PLC0415
    syms = names or acfg.chain_universe()
    rows = []
    for s in syms:
        iv = _series(st, cm.IV30_KEY, now, s)
        sk = _series(st, cm.SKEW_KEY, now, s)
        rr = _series(st, cm.RR_KEY, now, s)
        ivr = iv30_less_rv20(st, now, s)
        rv20 = _series(st, cm.RV20_KEY, now, s)
        rv60 = _series(st, cm.RV60_KEY, now, s)
        if not any((iv, sk, rr, rv20)):
            rows.append([s, "not stored", "—", "—", "—", "—", "—", "—"])
            continue
        win = f"{iv[0][0]} to {iv[-1][0]}, n={len(iv)}" if iv else "—"
        ivc = (f"{iv[-1][1]:.1f}% (rank {iv_rank([v for _, v in iv], iv[-1][1]):.0f}, "
               f"{_rank_pct(iv, iv[-1][1])} percentile)" if len(iv) > 1 else
               f"{iv[-1][1]:.1f}% (one reading)" if iv else "—")
        f = lambda ser: (f"{ser[-1][1]:+.1f} ({_rank_pct(ser, ser[-1][1])}, n={len(ser)})"  # noqa: E731
                         if ser else "—")
        rows.append([s, ivc, win, f(sk), f(rr), f(ivr),
                     f"{rv20[-1][1]:.1f}%" if rv20 else "—",
                     f"{rv60[-1][1]:.1f}%" if rv60 else "—"])
    return {"title": "Per-name volatility (the 30-day IV)",
            "table": {"columns": ["Name", "30-day IV (IV rank, IV percentile)",
                                  "Window, n", "25-delta put skew (percentile, n)",
                                  "Risk reversal (percentile, n)", "IV less RV20 (percentile, n)",
                                  "RV20", "RV60"], "rows": rows},
            "lines": [f"{len(syms)} captured names; each figure against the name's own "
                      f"stored history (our captures), its window and n printed; vol points "
                      f"for the skew, the risk reversal and IV less RV20. Descriptive only."],
            "paragraph_wanted": False}


# ---------------------------------------------------------------------------
# OS-9 -- the largest OI builds, side unknown
# ---------------------------------------------------------------------------
def bs_itm_prob(spot: float, strike: float, iv: float, t: float, r: float,
                right: str) -> Optional[float]:
    """The Black-Scholes probability of finishing in the money: N(d2) for a call,
    N(-d2) for a put."""
    if not (spot and strike and iv and t) or t <= 0 or iv <= 0:
        return None
    d2 = (math.log(spot / strike) + (r - 0.5 * iv * iv) * t) / (iv * math.sqrt(t))
    n = 0.5 * (1.0 + math.erf((d2 if right == "C" else -d2) / math.sqrt(2.0)))
    return n


def _mid(r: dict) -> Optional[float]:
    b, a = r.get("bid"), r.get("ask")
    if b is not None and a is not None and a >= b and a > 0:
        return (a + b) / 2.0
    return r.get("last_price") or None


def decile_tag(hist: list[float], x: float, n_min: int = 10) -> Optional[str]:
    """"top" / "bottom" when x is in its history's top or bottom decile."""
    if len(hist) < n_min:
        return None
    p = iv_pctile(hist, x)
    return "top" if p >= 90.0 else "bottom" if p <= 10.0 else None


def name_tags(sym: str, day: str, closes: list[float], skew: list[float],
              ivrv: list[float], earnings_days: list[str], cfg: dict) -> list[str]:
    """Context tags from our data only (config/opening_setup.yaml oi_builds.tags)."""
    import datetime as dt                                       # noqa: PLC0415
    t = cfg["oi_builds"]["tags"]
    out = []
    d0 = dt.date.fromisoformat(day)
    if any(0 < (dt.date.fromisoformat(e) - d0).days <= int(t["earnings_days"])
           for e in earnings_days):
        out.append("EARNINGS")
    c = closes[-int(t["extreme_sessions"]):]
    if len(c) >= int(t["extreme_sessions"]) and c[-1]:
        if c[-1] >= max(c) * (1 - t["extreme_pct"] / 100.0):
            out.append("1M HIGH")
        elif c[-1] <= min(c) * (1 + t["extreme_pct"] / 100.0):
            out.append("1M LOW")
    n = int(t["move_sessions"])
    if len(closes) > n and closes[-1 - n]:
        mv = 100.0 * (closes[-1] / closes[-1 - n] - 1.0)
        if mv >= t["move_pct"]:
            out.append("MOMENTUM")
        elif mv <= -t["move_pct"]:
            out.append("SELLOFF")
    if skew and decile_tag(skew, skew[-1], int(t["decile_n_min"])) == "top":
        out.append("HIGH SKEW")
    if ivrv:
        dtag = decile_tag(ivrv, ivrv[-1], int(t["decile_n_min"]))
        if dtag == "bottom":
            out.append("CHEAP VOL")
        elif dtag == "top":
            out.append("VOL CRUSH")
    return out


def oi_floor(sym: str, cfg: Optional[dict] = None) -> int:
    """Batch 11 item 58, D6 (provisional, session-set): 2,000 contracts for SPY,
    QQQ and IWM (and SPX, an index), 500 for a single name."""
    f = ((cfg or config()).get("oi_builds") or {}).get("floor") or {}
    idx = [str(x).upper() for x in f.get("index_names") or ["SPY", "QQQ", "IWM", "SPX"]]
    return int(f.get("index", 2000) if sym.upper() in idx else f.get("single", 500))


def builds_for(sym: str, prev: list[dict], cur: list[dict], r: float,
               gated: bool = False, floor: int = 0) -> list[dict]:
    """Every positive OI change with its premium estimate and ITM probability.
    `gated` (SPX, SPCX): no IV is solved and no probability computed; the row
    carries `solver_gated` and its cell prints SOLVER_GATED."""
    from altdata import chain_metrics as cm                     # noqa: PLC0415
    ch = [c for c in cm.oi_changes(prev, cur) if c["oi_change"] > 0
          and c["oi_change"] >= floor]
    if not ch:
        return []
    ivs: dict = {}
    if not gated:
        try:
            solved = cm._solver().solve_chain(cur, r)["rows"]   # noqa: SLF001
            ivs = {(x["expiry"], x["strike"], x["right"]): x.get("solved_iv")
                   for x in solved}
        except Exception:                                       # noqa: BLE001
            ivs = {}
    out = []
    for c in ch:
        mid = _mid(c)
        iv = ivs.get((c["expiry"], c["strike"], c["right"]))
        t = (c.get("dte") or 0) / 365.0
        out.append({"symbol": sym, "expiry": c["expiry"], "strike": c["strike"],
                    "right": c["right"], "oi_change": c["oi_change"], "mid": mid,
                    "premium": None if mid is None else mid * c["oi_change"] * 100.0,
                    "iv": iv, "spot": c.get("spot"), "dte": c.get("dte"),
                    "solver_gated": gated, "volume_day": c.get("volume_before"),
                    "oi_vol_pct": (100.0 * c["oi_change"] / c["volume_before"]
                                   if c.get("volume_before") else None),
                    "p_itm": bs_itm_prob(c.get("spot"), c["strike"], iv, t, r, c["right"])
                    if iv else None})
    return out


def merge_spreads(builds: list[dict]) -> list[dict]:
    """Two builds of equal size on one name and expiry print as one line, "spread
    (legs equal)"; the rest stay single. Largest first."""
    builds = sorted(builds, key=lambda b: -b["oi_change"])
    used, out = set(), []
    for i, b in enumerate(builds):
        if i in used:
            continue
        mate = next((j for j in range(i + 1, len(builds)) if j not in used
                     and builds[j]["symbol"] == b["symbol"]
                     and builds[j]["expiry"] == b["expiry"]
                     and builds[j]["oi_change"] == b["oi_change"]), None)
        if mate is not None:
            used.add(mate)
            out.append({**b, "legs": [b, builds[mate]], "spread": True})
        else:
            out.append({**b, "legs": [b], "spread": False})
    return out


def oi_build_table(builds: list[dict], tags: dict[str, list[str]], cfg: dict) -> dict:
    rows = []
    for b in merge_spreads(builds)[:int(cfg["oi_builds"]["rows"])]:
        legs = b["legs"]
        strike = " / ".join(f"{x['strike']:g}" for x in legs)
        typ = " / ".join("call" if x["right"] == "C" else "put" for x in legs)
        prem = [x["premium"] for x in legs if x["premium"] is not None]
        pit = [x["p_itm"] for x in legs if x["p_itm"] is not None]
        ov = [x.get("oi_vol_pct") for x in legs]
        rows.append([b["symbol"] + (" -- spread (legs equal)" if b["spread"] else ""),
                     b["expiry"], strike, typ, f"{b['oi_change']:+,.0f}"
                     + (" each" if b["spread"] else ""),
                     " / ".join(f"{v:.0f}%" if v is not None else "n/a" for v in ov),
                     f"${sum(prem) / 1e6:,.2f}m" if prem else "n/a",
                     SOLVER_GATED if b.get("solver_gated") else
                     " / ".join(f"{p * 100:.0f}%" for p in pit) if pit else "n/a",
                     str(b.get("dte")), ", ".join(tags.get(b["symbol"]) or []) or "—"])
    return {"columns": ["Name", "Expiry", "Strike", "Type", "OI change",
                        "OI change, % of the day's volume", "Premium (est.)",
                        "Chance in the money", "Days", "Context"],
            "rows": rows}


def oi_builds_from_store(prior: str, cutoff: str, db_path: Optional[str] = None,
                         base: Optional[Path] = None, names: Optional[list[str]] = None,
                         cfg: Optional[dict] = None) -> dict:
    """OS-9 for the 07:00 anchor: our own two most recent captures per name --
    the 17 names, and SPX and SPCX from the vendor's chains (ruling 4 of 19 Oct
    2026), whose chance in the money awaits the solver gate."""
    import datetime as dt                                       # noqa: PLC0415
    from altdata import chain_metrics as cm, config as acfg, events as ev_mod, \
        observations                                            # noqa: PLC0415
    cfg = cfg or config()
    gated = set(acfg.massive_universe())
    syms = names or (acfg.chain_universe() + sorted(gated))
    root = Path(base) if base else cm.chain_dir()
    builds, tags = [], {}
    try:
        with observations.ObservationStore(db_path) as st:
            for s in syms:
                day = next((d for d in sorted((x.name for x in root.iterdir() if x.is_dir()
                                               and x.name <= prior), reverse=True)
                            if cm.latest_capture(d, root, s)), None) if root.is_dir() else None
                if not day:
                    continue
                cur_p, prev_p = cm.latest_capture(day, root, s), cm.previous_capture(day, s, root)
                if not prev_p:
                    continue
                builds += builds_for(s, cm.load_rows(prev_p), cm.load_rows(cur_p),
                                     acfg.RISK_FREE_RATE, gated=s in gated,
                                     floor=oi_floor(s, cfg))
                closes = [v for _, v in _series(st, f"yfinance.mkt_{s.lower()}", cutoff)]
                skew = [v for _, v in _series(st, cm.SKEW_KEY, cutoff, s)]
                ivrv = [v for _, v in _series(st, cm.IV_RV_KEY, cutoff, s)]
                tags[s] = (closes, skew, ivrv, day)
            # OS-12 (Batch 13 item 61, D4; a54): the names the prior session's close
            # flagged on relative volume, recomputed as of its close cutoff.
            try:
                from . import relative_volume as _rv            # noqa: PLC0415
                vol_flags = _rv.flagged_yesterday(st, prior, syms=syms)
            except Exception:                                   # noqa: BLE001
                log.warning("OS-12's tag faulted", exc_info=True)
                vol_flags = set()
        earn: dict[str, list[str]] = {}
        try:
            d0 = dt.date.fromisoformat(prior)
            with ev_mod.EventStore(db_path) as ev:
                for r in ev.calendar(prior, (d0 + dt.timedelta(days=15)).isoformat(),
                                     as_of=cutoff):
                    if r.get("type") != "earnings":
                        continue
                    pl = r.get("payload") or {}
                    if isinstance(pl, str):
                        pl = json.loads(pl or "{}")
                    earn.setdefault(str(pl.get("symbol") or "").upper(), []).append(
                        str(r["observed_at"])[:10])
        except Exception:                                       # noqa: BLE001
            earn = {}
        tg = {s: name_tags(s, v[3], v[0], v[1], v[2], earn.get(s, []), cfg)
              for s, v in tags.items()}
        for s in vol_flags:
            tg.setdefault(s, []).append(VOLUME_FLAG_TAG)
        tab = oi_build_table(builds, tg, cfg)
    except Exception:                                           # noqa: BLE001
        log.warning("the OI-build table faulted", exc_info=True)
        tab = {"columns": [], "rows": []}
    return {"title": OI_TITLE, "table": tab,
            "note": ("From our own two most recent captures per name; open interest is "
                     "each capture's prior settlement, so a build is yesterday's. The "
                     "premium is the later mid x the OI change x 100; the chance in the "
                     "money is Black-Scholes on our solver's IV; SPX's and SPCX's read "
                     f"\"{SOLVER_GATED}\" until the IV solver's gate admits them. The "
                     "Context tags' history thresholds are "
                     f"{cfg['oi_builds']['tags'].get('label') or 'session-set'} "
                     "(config/opening_setup.yaml). Only builds of 2,000 contracts or more "
                     "(SPY, QQQ, IWM, SPX) or 500 (single names) print (provisional), and "
                     "each shows its OI change as a share of the session's volume in that "
                     "contract. Who opened the position is not known: side unknown.")}


def oi_builds_html(b: Optional[dict]) -> str:
    from html import escape                                     # noqa: PLC0415
    if not b or not (b.get("table") or {}).get("rows"):
        return ""
    t = b["table"]
    head = "".join(f"<th style=\"text-align:left;padding:2px 6px\">{escape(c)}</th>"
                   for c in t["columns"])
    body = "".join("<tr>" + "".join(f"<td style=\"padding:2px 6px\">{escape(str(c))}</td>"
                                    for c in r) + "</tr>" for r in t["rows"])
    return (f"<h3 style=\"font-size:13px;margin:10px 0 4px 0\">{escape(b['title'])}</h3>"
            f"<table style=\"font-size:11px;border-collapse:collapse\"><thead><tr>{head}"
            f"</tr></thead><tbody>{body}</tbody></table>"
            f"<p style=\"font-size:11px;color:#64748b\">{escape(b['note'])}</p>")


# ---------------------------------------------------------------------------
# OS-4 -- the index put-volume proxy (the anchor)
# ---------------------------------------------------------------------------
def index_put_lines(st, cutoff: str, symbols=("SPY", "SPX")) -> list[dict]:
    from altdata import chain_metrics as cm                     # noqa: PLC0415
    from altdata.numeral_audit import with_ordinals             # noqa: PLC0415
    out = []
    for s in symbols:
        v_last, v_hist = _hist_read(st, cm.PUT_VOL_KEY, cutoff, s)
        o_last, o_hist = _hist_read(st, cm.PUT_OI_KEY, cutoff, s)
        if not v_last:
            out.append({"line": f"{s}: put share of volume not stored; {NO_SIDE}.",
                        "values": {}, "constants": []})
            continue
        vals = {"put_share_volume": v_last[1], "as_of": v_last[0],
                "volume_percentile": iv_pctile([x for _, x in v_hist], v_last[1]),
                "volume_n": len(v_hist), "volume_from": v_hist[0][0]}
        parts = [f"puts {v_last[1]:.1f}% of the session's volume "
                 f"({_pct_window([x for _, x in v_hist], v_last[1], v_hist)})"]
        if o_last:
            vals.update(put_share_oi_build=o_last[1],
                        build_percentile=iv_pctile([x for _, x in o_hist], o_last[1]),
                        build_n=len(o_hist), build_from=o_hist[0][0])
            parts.append(f"puts {o_last[1]:.1f}% of the day's OI build "
                         f"({_pct_window([x for _, x in o_hist], o_last[1], o_hist)})")
        else:
            parts.append("the OI build not stored")
        out.append({"line": f"{s}, {v_last[0]}: " + "; ".join(parts) + f"; {NO_SIDE}.",
                    "values": with_ordinals(vals), "constants": []})
    return out


def _pct_window(hist: list[float], x: float, s: list[tuple]) -> str:
    from altdata.numeral_audit import ordinal                   # noqa: PLC0415
    return (f"{ordinal(iv_pctile(hist, x))} percentile, {s[0][0]} to {s[-1][0]}, "
            f"n={len(s)}")


def index_put_lines_from_store(cutoff: str, db_path: Optional[str] = None) -> list[dict]:
    from altdata import observations                            # noqa: PLC0415
    try:
        with observations.ObservationStore(db_path) as st:
            return index_put_lines(st, cutoff)
    except Exception:                                           # noqa: BLE001
        log.warning("the index put lines faulted", exc_info=True)
        return []


# ---------------------------------------------------------------------------
# OS-5 -- the single-name put-volume proxy (the Weekly)
# ---------------------------------------------------------------------------
def single_name_puts(st, now: str, names: Optional[list[str]] = None,
                     n_min: int = 5) -> dict:
    """The equal-weighted z across the captured single names of each name's put
    share of volume against its own history; the three highest and lowest."""
    from altdata import chain_metrics as cm, config as acfg     # noqa: PLC0415
    syms = names or list(acfg.SINGLE_NAMES)
    zs = []
    for s in syms:
        last, hist = _hist_read(st, cm.PUT_VOL_KEY, now, s)
        xs = [v for _, v in hist]
        if not last or len(xs) < n_min:
            continue
        m = statistics.fmean(xs)
        sd = statistics.stdev(xs)
        if sd:
            zs.append({"symbol": s, "share": last[1], "z": (last[1] - m) / sd, "n": len(xs),
                       "from": hist[0][0], "to": hist[-1][0]})
    if not zs:
        return {"title": "Single-name put share of volume", "table": None,
                "lines": [f"Single-name put share of volume: awaiting (no name has {n_min} "
                          f"stored sessions); {NO_SIDE}."],
                "paragraph_wanted": False, "data": {"single_name_puts": []}}
    ew = statistics.fmean(z["z"] for z in zs)
    lo, hi = min(z["from"] for z in zs), max(z["to"] for z in zs)
    ns = sorted(z["n"] for z in zs)
    srt = sorted(zs, key=lambda z: -z["z"])
    pick = srt[:3] + [z for z in srt[-3:] if z not in srt[:3]]
    rows = [[z["symbol"], f"{z['share']:.1f}%", f"{z['z']:+.2f}",
             f"{z['from']} to {z['to']}, n={z['n']}"] for z in pick]
    return {"title": "Single-name put share of volume",
            "table": {"columns": ["Name", "Put share of volume", "z against its own history",
                                  "Window, n"], "rows": rows},
            "lines": [f"Equal-weighted z of the put share of volume across {len(zs)} captured "
                      f"single names: {ew:+.2f} (each name against its own history, {lo} to "
                      f"{hi}, n={ns[0]} to {ns[-1]} sessions); {NO_SIDE}."],
            "paragraph_wanted": False,
            "data": {"single_name_puts": zs, "equal_weighted_z": ew},
            "table_note": ("The three highest and the three lowest names. Report-only: this "
                           "feeds nothing but its own rows (OS-5).")}
