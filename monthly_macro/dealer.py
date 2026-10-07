"""
The Monthly's Mechanics: the dealer retrospective. (reporting-stack brief 1.2; T3)

    from monthly_macro import dealer
    retro = dealer.retrospective(store, "2026-09-01", "2026-09-30", cutoff, cfg)

HOW THE MARKET BEHAVED AGAINST DEALER POSITIONING, READ, NEVER RECOMPUTED. The
close stores one `dealer.scorecard_day` row per session (stack_close.scorecard_row);
this module reads the month's rows and nothing else. Each session's flags are the
Weekly's own rule (daily_cascade.weekly_sections.flags_for, thresholds in
config/reporting_stack.yaml `dealer_flags`), so a session is "pinned" in the
Monthly exactly when it was pinned in its Weekly:

  pinned       the close within pinned_pct of max pain
  held         the morning call wall (or put wall) touched within wall_pct and
               the close inside it
  amplified    the morning flip crossed and the actual range at least
               amplified_range_ratio times the implied one-day range
  IV check     SPY's own ATM IV and the VIX more than iv_vix_check_points apart

THE MONTH'S COUNTS AND HIT RATES are counts of those flags over the sessions on
which the flag could be computed (a flag a card cannot support is None, never
False). Below MIN_SESSIONS scored sessions the counts are not printed as rates:
the section says "insufficient sessions (n=...)" and the prose is not asked for.

THE PROSE MAY USE A FLAG WORD ONLY WHERE THE FLAG SAYS SO. flag_word_faults()
holds the Mechanics paragraph to the per-session table: a sentence that says
pinned, held or amplified must name a session whose flag is set, or carry that
flag's own count for the month.
"""

from __future__ import annotations

import datetime as dt
import json
import re
from typing import Any, Optional

from daily_cascade import weekly_sections as wsec

KEY = "dealer.scorecard_day"
# T3 (Ari, 7 Oct 2026): "insufficient sessions" below 20. The brief's section
# 1.2 wrote 15; the T3 instruction is the later ruling and governs.
MIN_SESSIONS = 20

FLAGS = (("pinned", "pinned"), ("call_wall_held", "call wall held"),
         ("put_wall_held", "put wall held"), ("amplified", "amplified"))


def cards(st, first: str, last: str, cutoff: str,
          symbol: str = "SPY") -> list[dict]:
    """The month's stored scorecard rows, one per session (the latest stored
    for a session wins), in session order."""
    by: dict[str, dict] = {}
    for r in st.as_of(KEY, cutoff, symbol):
        day = str(r["observed_at"])[:10]
        if not (first <= day <= last):
            continue
        try:
            c = json.loads(r["value_text"])
        except (TypeError, ValueError):
            continue
        c.setdefault("session", day)
        by[day] = c
    return [by[d] for d in sorted(by)]


def _rate(hit: int, n: int) -> Optional[float]:
    return round(100.0 * hit / n, 1) if n else None


def _bn(v: Optional[float]) -> str:
    return "—" if v is None else f"{v / 1e9:+,.2f}bn"


def _g(v: Optional[float], fmt: str = "{:,.2f}") -> str:
    return "—" if v is None else fmt.format(v)


def _day(d: str) -> str:
    try:
        x = dt.date.fromisoformat(str(d)[:10])
        return f"{x.day} {x.strftime('%b')}"
    except ValueError:
        return str(d)


def retrospective(st, first: str, last: str, cutoff: str, cfg: dict,
                  vix_key: Optional[str] = None) -> dict:
    """{sessions, counts, rates, insufficient, table, ranges_table, lines}."""
    fc = cfg.get("dealer_flags") or {}
    vk = vix_key or fc.get("implied_vol_key") or "yfinance.mkt_vix"
    vix = {str(r["observed_at"])[:10]: r["value_num"] for r in st.as_of(vk, cutoff)
           if r.get("value_num") is not None}
    rows = []
    for c in cards(st, first, last, cutoff):
        f = wsec.flags_for(c, vix.get(str(c["session"])[:10]), cfg)
        rows.append({"session": str(c["session"])[:10],
                     "gamma_regime": c.get("gamma_regime"),
                     "net_gex_morning": c.get("net_gex_morning"),
                     "net_gex_close": c.get("net_gex_close"),
                     "flip_morning": c.get("flip_morning"),
                     "flip_crossed": c.get("flip_crossed"),
                     "max_pain": c.get("max_pain"),
                     "session_return_pct": c.get("session_return_pct"),
                     "session_range_pct": c.get("session_range_pct"),
                     "realized_vol_pct": c.get("realized_vol_5m_ann_pct"),
                     "implied_range": f["implied_range"],
                     "actual_range": f["actual_range"],
                     "iv_source": f.get("iv_source"),
                     "iv_check": bool(f.get("iv_check")),
                     "spy_iv": f.get("spy_iv"), "vix": f.get("vix"),
                     "close_vs_flip": f["close_vs_flip"],
                     "flags": {k: f[k] for k, _ in FLAGS}})
    n = len(rows)
    counts: dict[str, Any] = {
        "sessions": n,
        "positive_gamma": sum(1 for r in rows if r["gamma_regime"] == "positive"),
        "negative_gamma": sum(1 for r in rows if r["gamma_regime"] == "negative"),
        "flip_crossed": sum(1 for r in rows if r["flip_crossed"]),
        "iv_check": sum(1 for r in rows if r["iv_check"])}
    rates: dict[str, Any] = {}
    for k, _ in FLAGS:
        scored = [r for r in rows if r["flags"][k] is not None]
        hit = sum(1 for r in scored if r["flags"][k])
        counts[k] = hit
        counts[f"{k}_scored"] = len(scored)
        rates[k] = _rate(hit, len(scored))

    # THE RANGE ON FLIP-CROSSING SESSIONS AGAINST THE OTHERS (brief 1.2), and the
    # month's largest move with that morning's regime and net GEX.
    def mean(xs):
        xs = [x for x in xs if x is not None]
        return round(sum(xs) / len(xs), 3) if xs else None
    crossed = [r["session_range_pct"] for r in rows if r["flip_crossed"]]
    other = [r["session_range_pct"] for r in rows if r["flip_crossed"] is False]
    counts["range_pct_flip_crossed"] = mean(crossed)
    counts["range_pct_flip_held"] = mean(other)
    moves = [r for r in rows if r["session_return_pct"] is not None]
    big = max(moves, key=lambda r: abs(r["session_return_pct"])) if moves else None
    counts["largest_move"] = ({"session": big["session"],
                               "return_pct": big["session_return_pct"],
                               "gamma_regime": big["gamma_regime"],
                               "net_gex_morning": big["net_gex_morning"]}
                              if big else None)
    by_regime = {}
    for g in ("positive", "negative"):
        rs = [r for r in rows if r["gamma_regime"] == g]
        by_regime[g] = {"sessions": len(rs),
                        "actual_range_mean": mean([r["actual_range"] for r in rs]),
                        "implied_range_mean": mean([r["implied_range"] for r in rs])}
    counts["range_by_regime"] = by_regime
    insufficient = n < MIN_SESSIONS

    table_rows, range_rows = [], []
    for r in rows:
        set_flags = [lab for k, lab in FLAGS if r["flags"][k]]
        table_rows.append([_day(r["session"]), r["gamma_regime"] or "—",
                           _bn(r["net_gex_morning"]), _bn(r["net_gex_close"]),
                           _g(r["flip_morning"]),
                           "yes" if r["flip_crossed"] else
                           ("no" if r["flip_crossed"] is False else "—")])
        range_rows.append([_day(r["session"]), _g(r["max_pain"]),
                           _g(r["implied_range"]) + (
                               f" (SPY IV {r['spy_iv']:.1f}, VIX {r['vix']:.1f}: check)"
                               if r["iv_check"] else
                               " (VIX as proxy)" if r["iv_source"] == "VIX as proxy"
                               else ""),
                           _g(r["actual_range"]), r["close_vs_flip"] or "—",
                           ", ".join(set_flags + (["check"] if r["iv_check"] else []))
                           or "none"])
    if insufficient:
        summary = None
        lines = [f"insufficient sessions (n={n}): the month's counts and hit rates "
                 f"need {MIN_SESSIONS} scored sessions"]
    else:
        summary = [
            ["Sessions scored", n, "—"],
            ["Positive / negative net GEX", f"{counts['positive_gamma']} / "
                                            f"{counts['negative_gamma']}", "—"],
            ["Morning flip crossed", counts["flip_crossed"], "—"]]
        for k, lab in FLAGS:
            summary.append([lab[0].upper() + lab[1:],
                            f"{counts[k]} of {counts[f'{k}_scored']}",
                            "—" if rates[k] is None else f"{rates[k]:.1f}%"])
        summary.append(["IV check (SPY IV against the VIX)", counts["iv_check"], "—"])
        lines = []
        if counts["range_pct_flip_crossed"] is not None \
                and counts["range_pct_flip_held"] is not None:
            lines.append(f"Mean session range: {counts['range_pct_flip_crossed']:.2f}% "
                         f"on flip-crossing sessions against "
                         f"{counts['range_pct_flip_held']:.2f}% on the others.")
        if big:
            lines.append(f"Largest move: {_day(big['session'])}, "
                         f"{big['session_return_pct']:+.2f}%, net GEX that morning "
                         f"{_bn(big['net_gex_morning'])} "
                         f"({big['gamma_regime'] or 'regime not stored'}).")
    return {"sessions": rows, "counts": counts, "rates": rates,
            "insufficient": insufficient, "min_sessions": MIN_SESSIONS,
            "table": {"columns": ["Session", "Gamma regime", "Net GEX, morning",
                                  "Net GEX, close", "Flip", "Flip crossed"],
                      "rows": table_rows},
            "ranges_table": {"columns": ["Session", "Max pain", "Implied range",
                                         "Actual range", "Close vs flip", "Flags"],
                             "rows": range_rows},
            "summary_table": ({"columns": ["The month", "Count", "Hit rate"],
                               "rows": summary} if summary else None),
            "lines": lines}


# ---------------------------------------------------------------------------
# The prose may say pinned, held or amplified only where the flag says so
# ---------------------------------------------------------------------------
_FLAG_WORD = re.compile(r"\b(pinned|pinning|held|amplif(?:ied|ies|y|ying))\b", re.I)
_MONTHS = "Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"
_DATE = re.compile(rf"\b(\d{{1,2}})\s(?:{_MONTHS})[a-z]*\b|\b(?:{_MONTHS})[a-z]*\s"
                   rf"(\d{{1,2}})\b|\b\d{{4}}-\d{{2}}-(\d{{2}})\b")


def _kind(word: str) -> str:
    w = word.lower()
    if w.startswith("pin"):
        return "pinned"
    if w.startswith("amplif"):
        return "amplified"
    return "held"


def flag_word_faults(text: Optional[str], retro: dict) -> list[str]:
    """Sentences using a flag word without a flagged session or the flag's count."""
    rows = retro.get("sessions") or []
    days = {int(r["session"][8:10]): r for r in rows}
    c = retro.get("counts") or {}
    counts = {"pinned": {c.get("pinned")},
              "held": {c.get("call_wall_held"), c.get("put_wall_held"),
                       (c.get("call_wall_held") or 0) + (c.get("put_wall_held") or 0)},
              "amplified": {c.get("amplified")}}
    out = []
    for s in re.split(r"(?<=[.!?])\s+", text or ""):
        words = {_kind(m.group(1)) for m in _FLAG_WORD.finditer(s)}
        if not words:
            continue
        named = [int(next(g for g in m.groups() if g)) for m in _DATE.finditer(s)]
        nums = {int(x) for x in re.findall(r"(?<![\d.])(\d{1,2})(?![\d.%])", s)}
        for w in words:
            if named:
                bad = [d for d in named if d in days and not _set(days[d], w)]
                if bad or not any(d in days for d in named):
                    out.append(f"'{w}' on a session whose flag is not set: "
                               f"'{s[:80]}'")
            elif not (nums & {x for x in counts[w] if x is not None}):
                out.append(f"'{w}' with no flagged session or the month's count: "
                           f"'{s[:80]}'")
    return out


def _set(row: dict, kind: str) -> bool:
    f = row.get("flags") or {}
    if kind == "held":
        return bool(f.get("call_wall_held") or f.get("put_wall_held"))
    return bool(f.get(kind))
