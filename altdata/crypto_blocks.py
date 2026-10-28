"""
The crypto data layer's report blocks (CD-9's Weekly and Monthly parts; Batch 4
Tranche A part 2; crypto-tranche-a-2, 17 Oct 2026). Config:
config/crypto_sources.yaml `blocks`.

    weekly_block(st, now)       the Weekly's crypto flows block: a sub-section of
                                Positioning & flows, at most 12 lines, each with its
                                data-as-of. The order places it beside the Mechanism
                                Watch block, never inside it; that block (MW-10) is
                                not built, so this one stands alone in the section
    monthly_mechanics(st, now)  the Monthly's mechanics rows: Bitcoin's and
                                Ethereum's network health, the ETH supply-and-burn
                                gap, the SR-29 row (not tracked, CD-12)
    monthly_slow(st, now)       the Monthly's slow-layer rows: the Factor V
                                stablecoin rows (SR-20's amendment, S-1), the watch
                                names' fundamentals, VC raises, the next-90-day
                                unlock table

READ ONLY: every figure is read from the store by key, at the cutoff, with its
data-as-of. Nothing fetches at render. Every Monthly row is in the triple form
(latest, long-run average, percentile) with the dual percentiles (five years and
full history).

THE FLAGS NEVER PRINT. S-2's, S-3's and S-5's flags (calc.flag_*) are stored by
altdata/sources/crypto_derived.py with gate status "not passed"; no block here
reads a calc.flag_* key (tools/validate_crypto_sources.py holds that). Scorecards
and lenses print from day one: the DVOL band is a lens.

    daily_paragraph(st, now)    CD-9's daily part (the a47 chain, 19 Oct 2026): the
                                07:00 anchor's and the 16:45 close's crypto
                                paragraph under positioning and flows, at most six
                                computed lines -- the T-1 ETF flows with streak and
                                percentile (S-2), aggregate funding and the open
                                interest's change (S-3), the DVOL band (S-4), Fear &
                                Greed as one word. BEHIND A SWITCH, OFF
                                (`blocks.daily.enabled`): the order wires it only
                                after Track D's D4/D6, which nothing records as done.
                                BTC dominance is left out (it came from CoinGecko's
                                /global, retired), and the order's 21:45 ETF refresh
                                has no unit (no 21:45 report run exists)

The 12:30 line is daily_cascade/crypto_gate.py, registered in midday_gate's GATES
and closed until the S-3 ledger passes.

THE WEEKLY'S VOCABULARY: "venue" is banned in a rendered Weekly
(tools/validate_weekly_edits.py); the lines say "exchange".
"""

from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent
TITLE_WEEKLY = "Crypto flows"
NOT_TRACKED = "not tracked"
# SR-29 (CD-12; ruling 2 of 19 Oct 2026): bitcoin-data.com with the operator's free
# key (altdata/sources/btcdata.py). The fetcher is built and reads its key from
# .env; until the key is there the series prints not tracked. Rule 30 supersedes
# D-8's by-hand fallback, so there is no by-hand line.
SR29_KEY = "btcdata.lth_supply_share"
SR29_KEY_ENV = "BITCOIN_DATA_API_KEY"
SR29_NOT_TRACKED = f"not tracked ({SR29_KEY}): no key in .env ({SR29_KEY_ENV})"
SR29_AWAITING = f"awaiting the first pull ({SR29_KEY}; the key is in .env)"
SR29_CREDIT = "source: BGeometrics (bitcoin-data.com)"


def sr29_absent() -> str:
    """What SR-29 prints with no row knowable: not tracked without the key,
    awaiting the first pull with it. The key's presence only; never its value."""
    from altdata import secrets                                 # noqa: PLC0415
    try:
        have = secrets.present(SR29_KEY_ENV)
    except Exception:                                         # noqa: BLE001
        have = False
    return SR29_AWAITING if have else SR29_NOT_TRACKED


def _cfg() -> dict:
    from altdata.sources import _crypto as C                    # noqa: PLC0415
    return C.config()


def _pts(st, key: str, now: str, inst: Optional[str] = None) -> list[tuple[str, float]]:
    out = []
    for r in st.as_of(key, now, inst):
        if r.get("value_num") is not None:
            out.append((str(r["observed_at"])[:10], float(r["value_num"])))
    return sorted(out)


def _at(pts: list, day: str) -> Optional[tuple[str, float]]:
    best = None
    for p in pts:
        if p[0] <= day:
            best = p
    return best


def _minus(day: str, n: int) -> str:
    return (dt.date.fromisoformat(day[:10]) - dt.timedelta(days=n)).isoformat()


def bn(v: Optional[float], sign: bool = False) -> str:
    if v is None:
        return "—"
    s = f"{'+' if sign and v > 0 else ''}{'-' if v < 0 else ''}"
    a = abs(v)
    if a >= 1e12:
        return f"{s}${a / 1e12:,.2f}tn"
    if a >= 1e9:
        return f"{s}${a / 1e9:,.1f}bn"
    return f"{s}${a / 1e6:,.1f}m"


def short(day: Optional[str]) -> str:
    if not day:
        return "—"
    d = dt.date.fromisoformat(day[:10])
    return f"{d.day} {d:%b} {d.year}"


# ---------------------------------------------------------------------------
# The Weekly
# ---------------------------------------------------------------------------
def band(pct_full: Optional[float], cfg: dict) -> str:
    b = (cfg.get("s4") or {}).get("band") or {}
    if pct_full is None:
        return "band from 60 days of store"
    if pct_full <= float(b.get("compressed", 20)):
        return "compressed"
    if pct_full >= float(b.get("stressed", 80)):
        return "stressed"
    return "normal"


def etf_line(st, coin: str, now: str, today: str) -> list:
    pts = _pts(st, f"farside.{coin}_total", now)
    label = f"{coin.upper()} spot ETF flows, the week"
    from altdata import refusals                                # noqa: PLC0415
    gap = refusals.text("farside")
    if gap:
        return [label, gap, "—"]
    if not pts:
        return [label, "not stored (Farside: see the notes)", "—"]
    last = pts[-1][0]
    if last < _minus(today, 5):
        # STALE, WITH ITS DATE: never an empty cell, never a zero.
        return [label, f"STALE: last good {short(last)}", short(last)]
    wk = [v for d, v in pts if _minus(today, 7) < d <= today]
    stk = _pts(st, "calc.etf_streak", now, coin)
    sv = int(stk[-1][1]) if stk and stk[-1][0] == last else None
    streak = ("" if sv is None else
              f"; streak {abs(sv)} {'inflow' if sv > 0 else 'outflow'} session"
              f"{'s' if abs(sv) != 1 else ''}" if sv else "; streak 0")
    return [label, f"{bn(sum(wk), True)} over {len(wk)} session"
                   f"{'s' if len(wk) != 1 else ''}{streak}", short(last)]


def z_note(st, key: str, inst: str, now: str, z_from: str) -> str:
    """Ruling 5 of 17 Oct: the aggregate's z-score prints from mid-December."""
    if now[:10] < z_from:
        return f"; z-score from {short(z_from)}"
    z = _pts(st, key, now, inst)
    return f"; z {z[-1][1]:+.1f}" if z else "; z needs 60 days of store"


def weekly_block(st, now: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or _cfg()
    bc = cfg.get("blocks") or {}
    today = now[:10]
    z_from = str(bc.get("z_from") or "2026-12-15")
    rows: list[list] = []

    # 1. S-1: stablecoin supply, 7 and 30 days
    s = _pts(st, "llama.stable_total", now)
    if s:
        d, v = s[-1]
        w7, w30 = _at(s, _minus(d, 7)), _at(s, _minus(d, 30))
        rows.append(["Stablecoin supply", f"{bn(v)}; {bn(v - w7[1], True) if w7 else '—'} "
                     f"in 7 days, {bn(v - w30[1], True) if w30 else '—'} in 30", short(d)])
    else:
        rows.append(["Stablecoin supply", NOT_TRACKED, "—"])
    # 2-3. S-2: ETF flows
    rows.append(etf_line(st, "btc", now, today))
    rows.append(etf_line(st, "eth", now, today))
    # 4-5. S-3: funding, the week's change
    for coin in ("BTC", "ETH"):
        f = _pts(st, "calc.funding_agg", now, coin)
        lab = f"{coin} perp funding, OI-weighted (annualised)"
        if not f:
            rows.append([lab, "from the first day two exchanges report open interest", "—"])
            continue
        d, v = f[-1]
        w = _at(f, _minus(d, 7))
        rows.append([lab, f"{v:.2f}%" + (f", {v - w[1]:+.2f} pts on the week" if w else "")
                     + z_note(st, "calc.leverage_z", coin, now, z_from), short(d)])
    # 6. S-3: open interest
    oi = _pts(st, "calc.oi_usd", now)
    if oi:
        d, v = oi[-1]
        w = _at(oi, _minus(d, 7))
        rows.append(["Perp open interest, BTC + ETH", bn(v) + (
            f", {100 * (v / w[1] - 1):+.1f}% on the week" if w and w[1] else ""), short(d)])
    else:
        rows.append(["Perp open interest, BTC + ETH",
                     "from the first day every exchange reports it", "—"])
    # 7-8. S-4: the DVOL band (a lens)
    for coin in ("BTC", "ETH"):
        dv = _pts(st, f"deribit.dvol_{coin.lower()}", now)
        lab = f"{coin} implied vol (DVOL)"
        if not dv:
            rows.append([lab, NOT_TRACKED, "—"])
            continue
        d, v = dv[-1]
        pf = _at(_pts(st, "calc.dvol_pct_full", now, coin), d)
        rows.append([lab, f"{v:.1f}, {band(pf[1] if pf and pf[0] == d else None, cfg)}",
                     short(d)])
    # 9. hashrate and difficulty
    hr = _pts(st, "mempool.hashrate", now)
    df = _pts(st, "mempool.difficulty", now)
    if hr:
        d = hr[-1][0]
        cur = [v for x, v in hr if _minus(d, 7) < x <= d]
        prev = [v for x, v in hr if _minus(d, 14) < x <= _minus(d, 7)]
        txt = f"{sum(cur) / len(cur) / 1e18:,.0f} EH/s (7-day mean)"
        if prev:
            txt += f", {100 * (sum(cur) / len(cur) / (sum(prev) / len(prev)) - 1):+.1f}% on the week"
        if len(df) >= 2:
            txt += f"; last difficulty adjustment {100 * (df[-1][1] / df[-2][1] - 1):+.2f}% ({short(df[-1][0])})"
        rows.append(["Bitcoin hashrate and difficulty", txt, short(d)])
    else:
        rows.append(["Bitcoin hashrate and difficulty", NOT_TRACKED, "—"])
    # 10. the fee tier
    fees = {t: _pts(st, "mempool.fee_rate", now, t) for t in ("fastest", "hour", "economy")}
    if fees["fastest"]:
        d = fees["fastest"][-1][0]
        rows.append(["Bitcoin fee tier (sat/vB)", ", ".join(
            f"{t.replace('_', ' ')} {fees[t][-1][1]:g}" for t in fees if fees[t]), short(d)])
    else:
        rows.append(["Bitcoin fee tier (sat/vB)", NOT_TRACKED, "—"])
    # 11. S-5: the froth line, unscored
    froth_from = str(bc.get("froth_from") or "2027-01-15")
    parts, d0 = [], None
    for net in (cfg.get("gt") or {}).get("networks") or ["solana", "base"]:
        np_ = [r for r in st.as_of("gt.new_pools_24h", now, net) if r.get("value_num") is not None]
        tv = [r for r in st.as_of("gt.trending_vol_24h", now, net) if r.get("value_num") is not None]
        if np_:
            parts.append(f"{net} {int(np_[-1]['value_num'])} new pools")
            d0 = max(d0 or "", str(np_[-1]["observed_at"])[:10])
        if tv:
            fb = " (DexScreener fallback)" if str(tv[-1].get("source")).startswith("dexscreener") else ""
            parts.append(f"{net} trending volume {bn(tv[-1]['value_num'])}{fb}")
            d0 = max(d0 or "", str(tv[-1]["observed_at"])[:10])
    rows.append([f"Froth gauge (unscored until {short(froth_from)})",
                 "; ".join(parts) if parts else
                 "not sampled yet: awaiting the first GeckoTerminal pull", short(d0)])
    # 12. the total and dominance (CoinPaprika, ruling 2)
    cap = _pts(st, "paprika.total_mcap_usd", now)
    dom = _pts(st, "paprika.btc_dominance", now)
    if cap or dom:
        d = (dom or cap)[-1][0]
        rows.append(["Crypto market cap; BTC dominance",
                     f"{bn(cap[-1][1]) if cap else '—'}; "
                     f"{dom[-1][1]:.1f}%" if dom else f"{bn(cap[-1][1])}; {NOT_TRACKED}",
                     short(d)])
    else:
        rows.append(["Crypto market cap; BTC dominance", NOT_TRACKED, "—"])
    rows = rows[:int(bc.get("weekly_max_lines") or 12)]
    return {"title": TITLE_WEEKLY,
            "table": {"columns": ["Measure", "The week", "Data as of"], "rows": rows},
            "paragraph_wanted": False,
            "notes": ["Scorecards and lenses only; S-2, S-3 and S-5 wait for their "
                      "offline gates. CoinPaprika's figures: Powered by Coinpaprika."],
            "data": {"crypto_flows": [{"measure": r[0], "value": r[1], "as_of": r[2]}
                                      for r in rows]}}


# ---------------------------------------------------------------------------
# The daily paragraph (CD-9's daily part)
# ---------------------------------------------------------------------------
TITLE_DAILY = "Crypto (positioning and flows)"


def daily_enabled(cfg: Optional[dict] = None) -> bool:
    cfg = cfg or _cfg()
    return bool(((cfg.get("blocks") or {}).get("daily") or {}).get("enabled"))


def fng_word(v: Optional[float], cfg: dict) -> Optional[str]:
    """Fear & Greed in the publisher's own label, by the session-set bands (`blocks.daily.fng_words`:
    [upper bound, word], ascending)."""
    if v is None:
        return None
    for hi, w in ((cfg.get("blocks") or {}).get("daily") or {}).get("fng_words") or []:
        if v <= float(hi):
            return str(w)
    return None


def _etf_daily(st, coin: str, now: str, today: str, stale_days: int) -> str:
    from altdata.numeral_audit import ordinal                   # noqa: PLC0415
    lab = f"{coin.upper()} spot ETF flows (T-1)"
    pts = _pts(st, f"farside.{coin}_total", now)
    from altdata import refusals                                # noqa: PLC0415
    gap = refusals.text("farside")
    if gap:
        return f"{lab}: {gap}."
    if not pts:
        return f"{lab}: not stored (Farside refuses the laptop; the box is untested)."
    d, v = pts[-1]
    if d < _minus(today, stale_days):
        return f"{lab}: STALE, last good {short(d)}."
    stk = _at(_pts(st, "calc.etf_streak", now, coin), d)
    sv = int(stk[1]) if stk and stk[0] == d else None
    streak = ("" if sv is None else "; streak 0" if sv == 0 else
              f"; streak {abs(sv)} {'inflow' if sv > 0 else 'outflow'} "
              f"session{'s' if abs(sv) != 1 else ''}")
    pc = _at(_pts(st, "calc.etf_5d_pct", now, coin), d)
    pct = (f"; the 5-day sum at the {ordinal(pc[1])} percentile since January 2024"
           if pc and pc[0] == d else "; the 5-day sum's percentile needs 20 sums")
    return f"{lab}: {bn(v, True)} on {short(d)}{streak}{pct}."


def daily_paragraph(st, now: str, cfg: Optional[dict] = None) -> dict:
    """The six lines, read from the store by key at `now`; computed, no model
    words. Never reads a flag (the flags wait for their ledgers)."""
    cfg = cfg or _cfg()
    bc = cfg.get("blocks") or {}
    dc = bc.get("daily") or {}
    today = now[:10]
    z_from = str(bc.get("z_from") or "2026-12-15")
    lines: list[str] = []
    # 1-2. S-2: the T-1 ETF flows, with the streak and the 5-day sum's percentile
    for coin in ("btc", "eth"):
        lines.append(_etf_daily(st, coin, now, today, int(dc.get("stale_days") or 4)))
    # 3. S-3: aggregate funding, OI-weighted, annualised
    parts, d0 = [], None
    for coin in ("BTC", "ETH"):
        f = _pts(st, "calc.funding_agg", now, coin)
        if f:
            parts.append(f"{coin} {f[-1][1]:.2f}%"
                         + z_note(st, "calc.leverage_z", coin, now, z_from))
            d0 = max(d0 or "", f[-1][0])
    lines.append("Perp funding, OI-weighted across exchanges (annualised): "
                 + ("; ".join(parts) + f" ({short(d0)})." if parts else
                    "from the first day two exchanges report open interest."))
    # 4. S-3: the open interest's change on the day
    oi = _pts(st, "calc.oi_usd", now)
    if len(oi) >= 2 and oi[-2][1]:
        (d1, v1), (_, v0) = oi[-1], oi[-2]
        lines.append(f"Perp open interest, BTC + ETH: {bn(v1)}, "
                     f"{100 * (v1 / v0 - 1):+.1f}% on the day ({short(d1)}).")
    elif oi:
        lines.append(f"Perp open interest, BTC + ETH: {bn(oi[-1][1])} ({short(oi[-1][0])}); "
                     f"the change needs a second day.")
    else:
        lines.append("Perp open interest, BTC + ETH: from the first day every exchange "
                     "reports it.")
    # 5. S-4: the DVOL band, a lens
    parts, d0 = [], None
    for coin in ("BTC", "ETH"):
        dv = _pts(st, f"deribit.dvol_{coin.lower()}", now)
        if dv:
            d, v = dv[-1]
            pf = _at(_pts(st, "calc.dvol_pct_full", now, coin), d)
            parts.append(f"{coin} {v:.1f}, {band(pf[1] if pf and pf[0] == d else None, cfg)}")
            d0 = max(d0 or "", d)
    lines.append("Implied vol (DVOL): " + ("; ".join(parts) + f" ({short(d0)})."
                                          if parts else f"{NOT_TRACKED}."))
    # 6. Fear & Greed, in the publisher's label
    fg = _pts(st, "fng.value", now)
    w = fng_word(fg[-1][1], cfg) if fg else None
    lines.append(f"Fear & Greed: {w} ({short(fg[-1][0])})." if w else
                 f"Fear & Greed: {NOT_TRACKED}.")
    lines = lines[:int(dc.get("max_lines") or 6)]
    return {"title": TITLE_DAILY, "lines": lines, "paragraph_wanted": False,
            "notes": ["Computed from the store; scorecards and lenses only. The S-2 "
                      "and S-3 flags wait for their ledgers. BTC dominance is left out: "
                      "it came from CoinGecko's /global, which is retired. Fear & "
                      "Greed's word bands are session-set."],
            "data": {"crypto_daily": lines}}


def daily_paragraph_from_store(now: str, db_path: Optional[str] = None,
                               cfg: Optional[dict] = None) -> Optional[dict]:
    """The paragraph for the anchor, or None while the switch is off. Never
    raises."""
    from altdata import observations                            # noqa: PLC0415
    cfg = cfg or _cfg()
    if not daily_enabled(cfg):
        return None
    try:
        with observations.ObservationStore(db_path) as st:
            return daily_paragraph(st, now, cfg)
    except Exception:                                           # noqa: BLE001
        log.warning("the crypto paragraph faulted", exc_info=True)
        return {"title": TITLE_DAILY, "lines": ["Crypto: not read (its inputs faulted)."],
                "paragraph_wanted": False}


def daily_html(b: Optional[dict]) -> str:
    from html import escape                                     # noqa: PLC0415
    if not b or not b.get("lines"):
        return ""
    return (f"<h3 style=\"font-size:13px;margin:10px 0 4px 0\">{escape(b['title'])}</h3>"
            + "".join(f'<p style="font-size:12px;margin:2px 0">{escape(x)}</p>'
                      for x in b["lines"]))


# ---------------------------------------------------------------------------
# The Monthly
# ---------------------------------------------------------------------------
DUAL_COLUMNS = ["Series", "Latest (data as of)", "Long-run average",
                "Percentile, 5 years", "Percentile, full history"]


def dual_row(st, key: str, now: str, label: str, inst: Optional[str] = None,
             dp: int = 2, transform=None) -> Optional[list]:
    """One row in the triple form, with both percentiles and their n."""
    from altdata import derived                                  # noqa: PLC0415
    pts = _pts(st, key, now, inst)
    if transform:
        pts = transform(pts)
    if not pts:
        return None
    d, v = pts[-1]
    as_of_day = dt.date.fromisoformat(now[:10])
    mean = sum(x for _, x in pts) / len(pts)

    def pc(years):
        p = derived._pct_in_window(pts, v, as_of_day, years)    # noqa: SLF001
        n = p.get("n") or 0
        if p.get("pct") is None or n < 20:
            return f"— (n={n})"
        return f"{derived._ord(p['pct'])} (n={n:,})"             # noqa: SLF001
    fmt = (lambda x: bn(x)) if abs(v) >= 1e6 else (lambda x: f"{x:,.{dp}f}")
    return [label, f"{fmt(v)} ({d})", f"{fmt(mean)} (since {pts[0][0]}, n={len(pts):,})",
            pc(5), pc("full")]


def monthly_mechanics(st, now: str) -> dict:
    rows, lines = [], []
    spec = [("mempool.hashrate", None, "Bitcoin hashrate (H/s)"),
            ("mempool.difficulty", None, "Bitcoin difficulty"),
            ("mempool.fee_rate", "hour", "Bitcoin fee, one-hour tier (sat/vB)"),
            ("blockscout.gas_gwei", "average", "Ethereum gas, average (gwei)"),
            ("blockscout.tx_count", None, "Ethereum transactions a day"),
            ("blockscout.utilization", None, "Ethereum utilisation (%)")]
    nt = []
    for key, inst, lab in spec:
        r = dual_row(st, key, now, lab, inst)
        if r:
            rows.append(r)
        else:
            nt.append(f"{lab}: no observation knowable at this cutoff")
    lines.append("ETH supply and burn: not tracked -- Etherscan's ethsupply2 needs "
                 "ETHERSCAN_API_KEY, not registered; no keyless source within robots "
                 "serves it (Blockscout's figure disagrees with the known supply).")
    sr29 = dual_row(st, SR29_KEY, now, "BTC long-term-holder supply share (%), SR-29")
    if sr29:
        rows.append(sr29)
        lines.append(f"BTC long-term-holder supply (SR-29): read the 3-month change with "
                     f"price context, not the level; {SR29_CREDIT}.")
    else:
        lines.append(f"BTC long-term-holder supply (SR-29): {sr29_absent()}.")
    return {"title": "Crypto network health", "table": {"columns": DUAL_COLUMNS,
                                                         "rows": rows},
            "lines": lines, "not_tracked": nt, "paragraph_wanted": False}


def _sum30(pts: list) -> list:
    """Daily flows -> trailing 30-day sums, one a day."""
    out, days = [], [d for d, _ in pts]
    vals = dict(pts)
    for i, d in enumerate(days):
        lo = _minus(d, 30)
        win = [vals[x] for x in days[:i + 1] if x > lo]
        if len(win) >= 25:
            out.append((d, sum(win)))
    return out


def unlock_table(now: str, path: Optional[Path] = None) -> dict:
    """The next 90 days' token unlocks, from the Security Master's
    unlock_schedule field (DS-21, reference data entered by hand). Until a
    schedule is entered, one line says so; never a guess."""
    import yaml                                                  # noqa: PLC0415
    p = path or (REPO / "config" / "security_master.yaml")
    rows = []
    try:
        sm = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        sm = {}
    end = (dt.date.fromisoformat(now[:10]) + dt.timedelta(days=90)).isoformat()
    for ent in (sm.get("instruments") or sm.get("entries") or []):
        for u in (ent or {}).get("unlock_schedule") or []:
            d = str(u.get("date"))[:10]
            if now[:10] <= d <= end:
                rows.append([d, ent.get("symbol") or ent.get("id"), u.get("amount"),
                             u.get("share_of_supply"), u.get("source")])
    rows.sort()
    sub = {"title": "Token unlocks, next 90 days", "paragraph_wanted": False}
    if rows:
        sub["table"] = {"columns": ["Date", "Name", "Tokens", "Share of supply",
                                    "Source"], "rows": rows}
    else:
        sub["lines"] = ["No schedules entered (the Security Master's unlock_schedule "
                        "field holds none)."]
    return sub


def monthly_slow(st, now: str, cfg: Optional[dict] = None) -> list[dict]:
    cfg = cfg or _cfg()
    out = []
    # Factor V: the stablecoin rows (SR-20's amendment, S-1)
    fv, nt = [], []
    for key, inst, lab in (("llama.stable_total", None, "Stablecoin supply, total"),
                           ("calc.stable_impulse_30d", None, "Change over 30 days (%)"),
                           ("calc.stable_impulse_90d", None, "Change over 90 days (%)"),
                           *[("calc.stable_share", ch, f"Share on {ch} (%)")
                             for ch in ("Ethereum", "Tron", "Solana", "Base")]):
        r = dual_row(st, key, now, lab, inst)
        (fv.append(r) if r else nt.append(f"{lab}: no observation knowable at this cutoff"))
    out.append({"title": "Factor V: stablecoins, the private-dollar leg (SR-20, S-1)",
                "table": {"columns": DUAL_COLUMNS, "rows": fv}, "not_tracked": nt,
                "paragraph_wanted": False,
                "notes": ["A scorecard, no rights: not read as a liquidity signal "
                          "until a gate says otherwise."]})
    # The watch names' fundamentals: fees and revenue as 30-day sums
    wr, wnt = [], []
    from altdata.sources import llama                             # noqa: PLC0415
    names = [n["sym"] for n in (cfg.get("watch_names") or [])]
    names += [s for s in ("AAVE", "PRL") if s in llama.basket()]
    for sym in names:
        for kind in ("fees", "revenue"):
            key = f"llama.{kind}_{sym.lower()}"
            r = dual_row(st, key, now, f"{sym} {kind}, 30 days", transform=_sum30)
            if r:
                pts = _sum30(_pts(st, key, now))
                prev = _at(pts, _minus(pts[-1][0], 30))
                r[2] = (f"{100 * (pts[-1][1] / prev[1] - 1):+.1f}% on the prior 30 days"
                        if prev and prev[1] else "—")
                wr.append(r)
            else:
                wnt.append(f"{sym} {kind}: not stored at this cutoff")
    out.append({"title": "Watch names: what pays the token",
                "table": {"columns": ["Series", "30-day sum (data as of)",
                                      "Change on the prior 30 days",
                                      "Percentile, 5 years", "Percentile, full history"],
                          "rows": wr},
                "not_tracked": wnt, "paragraph_wanted": False})
    out.append({"title": "VC raises, trailing three months",
                "lines": ["Not available: the endpoint is paywalled (DefiLlama /raises "
                          "answers 402, 17 Oct 2026)."], "paragraph_wanted": False})
    out.append(unlock_table(now))
    return out
