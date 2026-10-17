"""
The dealer scorecard's pre-registered hypotheses and their rate printer (6b part
2; brief v2 section 5, ratified 16 Oct 2026; the registration
docs/ledgers/dealer-scorecard-preregistration-2026-10.md, dated 17 Oct 2026).

    from altdata import dealer_scorecard as dsc
    rows = dsc.score(cards, closes)          # per session, per hypothesis
    table = dsc.rates_table(rows)            # k/n, Wilson 95%, base rate, baseline

WHAT IT READS. The close's stored `dealer.scorecard_day` rows (stack_close.
scorecard_row), and SPY's daily closes for the flip-crossing outcome. Nothing is
fetched or written: the Weekly and the Monthly call these on rows they have read.

THE HYPOTHESES are the registration's, mirrored in config/reporting_stack.yaml
`dealer_scorecard` (the gate holds the two to each other and the registration to
its recorded SHA-256). Each has an ELIGIBILITY test, an OUTCOME, a BASE RATE (the
outcome's frequency over every session it can be evaluated on, eligible or not)
and a price-action BASELINE (the same outcome scored against a level with no
dealer content). An ineligible session is None, never False; an outcome that
needs sessions not yet stored is None (unresolved) until they are.

  H1 dampened        regime session (morning net-to-gross >= 0.10), positive
                     gamma: the session's range <= 0.8 x the implied one-day range
  H2 amplified       regime session, negative gamma: range >= 1.2 x implied
  H3a call wall held the high within 0.25% of the morning OTM call wall: the close
                     below it; baseline the nearest round number above
  H3b put wall held  the low within 0.25% of the morning OTM put gamma wall: the
                     close above it; baseline the nearest round number below
  H4 pinned          the monthly third-Friday expiry only (ruled 17 Oct): the close
                     within 0.25% of the morning peak-gamma strike; max pain the
                     control; baseline the nearest round number
  H5 flip crossing   the session's range contained the morning flip: the next
                     three sessions' realised vol above the prior ten's

HOW RATES PRINT (section 5.3). k/n with a Wilson 95% interval, the base rate and
the baseline beside it; sessions and episodes (a run of consecutive eligible
sessions is one episode) both counted. No count prints below 20 scored sessions,
and below 120 eligible sessions every rate says "no rate is a decision". The
formation and test windows (the first 120 eligible sessions, the next 120) are
reported; promotion is the registration's rule and nothing here grants a reading.
"""

from __future__ import annotations

import datetime as dt
import math
from typing import Any, Optional

Z95 = 1.959963984540054
HYPOTHESES = ("dampened", "amplified", "call_wall_held", "put_wall_held", "pinned",
              "flip_crossing")
LABELS = {"dampened": "H1 dampened", "amplified": "H2 amplified",
          "call_wall_held": "H3a call wall held", "put_wall_held": "H3b put wall held",
          "pinned": "H4 pinned", "flip_crossing": "H5 flip crossing"}


def config(cfg: Optional[dict] = None) -> dict:
    if cfg is None:
        from altdata import bars as bars_mod                    # noqa: PLC0415
        cfg = bars_mod.load_config()
    return dict(cfg.get("dealer_scorecard") or {})


# ---------------------------------------------------------------------------
# Small pieces
# ---------------------------------------------------------------------------
def third_friday(d: dt.date) -> dt.date:
    first = d.replace(day=1)
    return first + dt.timedelta(days=(4 - first.weekday()) % 7 + 14)


def is_monthly_expiry(day: str) -> bool:
    """The monthly third Friday (ruled 17 Oct 2026); weekly Fridays stay out."""
    d = dt.date.fromisoformat(day[:10])
    return d == third_friday(d)


def within(a: Optional[float], b: Optional[float], pct: float) -> Optional[bool]:
    if a is None or b in (None, 0):
        return None
    return abs(a / b - 1.0) * 100.0 <= pct


def implied_range(card: dict, vix: Optional[float] = None) -> Optional[float]:
    """spot x IV x sqrt(1/252): SPY's own ATM 30-day IV, else the VIX."""
    spot = card.get("prior_close") or card.get("close")
    iv = card.get("atm_iv_30d") or vix
    return spot * (iv / 100.0) * math.sqrt(1.0 / 252.0) if spot and iv else None


def round_above(x: float, step: float) -> float:
    return math.ceil(x / step) * step


def round_below(x: float, step: float) -> float:
    return math.floor(x / step) * step


def nearest_round(x: float, step: float) -> float:
    return round(x / step) * step


def realised_vol(closes: list[float]) -> Optional[float]:
    """Annualised close-to-close realised vol, percent; None under two returns."""
    rets = [math.log(b / a) for a, b in zip(closes, closes[1:]) if a and b]
    if len(rets) < 2:
        return None
    m = sum(rets) / len(rets)
    var = sum((r - m) ** 2 for r in rets) / (len(rets) - 1)
    return math.sqrt(var * 252.0) * 100.0


def wilson(k: int, n: int, z: float = Z95) -> Optional[tuple[float, float]]:
    """The Wilson score interval for k successes in n, as fractions."""
    if n <= 0:
        return None
    p = k / n
    den = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, centre - half), min(1.0, centre + half)


# ---------------------------------------------------------------------------
# Scoring one session
# ---------------------------------------------------------------------------
def score_card(card: dict, closes: dict[str, float], cfg: dict,
               vix: Optional[float] = None) -> dict:
    """{hypothesis: {"eligible", "outcome", "base", "baseline", "control"}} for
    one stored row. `closes` maps session date -> SPY close (the flip-crossing
    outcome and its baseline's moving average)."""
    wall_pct = float(cfg.get("wall_pct", 0.25))
    pin_pct = float(cfg.get("pin_pct", 0.25))
    lo_r, hi_r = float(cfg.get("dampened_ratio", 0.8)), float(cfg.get("amplified_ratio", 1.2))
    step = float(cfg.get("round_step", 5.0))
    ntg_min = float(cfg.get("net_to_gross_min", 0.10))
    close, hi, lo = card.get("close"), card.get("session_high"), card.get("session_low")
    prior = card.get("prior_close")
    imp = implied_range(card, vix)
    rng = (hi - lo) if None not in (hi, lo) else None
    ratio = (rng / imp) if rng is not None and imp else None
    ntg = card.get("net_to_gross_morning")
    regime = None if ntg is None else ntg >= ntg_min
    net_m = card.get("net_gex_morning")
    out: dict[str, dict] = {}

    # H1, H2: regime sessions, by the morning's sign.
    for h, sign, test in (("dampened", 1, lambda r: r <= lo_r),
                          ("amplified", -1, lambda r: r >= hi_r)):
        elig = (None if regime is None or net_m is None else
                (regime and (net_m > 0 if sign > 0 else net_m < 0)) or None)
        out[h] = {"eligible": elig,
                  "outcome": (test(ratio) if elig and ratio is not None else None),
                  "base": (test(ratio) if ratio is not None else None),
                  # Baseline: filled by score() -- the threshold met again the
                  # session after it was met (vol clustering, no dealer content).
                  "baseline": None}

    # H3: the morning OTM walls, approached.
    for h, wall_key, side in (("call_wall_held", "call_wall_otm_morning", 1),
                              ("put_wall_held", "put_wall_otm_morning", -1)):
        w = card.get(wall_key)
        ext = hi if side > 0 else lo
        appr = within(ext, w, wall_pct)
        elig = True if appr else None
        held = (None if close is None or w is None else
                (close < w if side > 0 else close > w))
        rn = (None if prior is None else
              (round_above(prior, step) if side > 0 else round_below(prior, step)))
        rn_appr = within(ext, rn, wall_pct)
        out[h] = {"eligible": elig, "outcome": held if elig else None,
                  # Base rate: a session's close retreats from its extreme by at
                  # least the approach band -- any touched level would read held.
                  "base": (None if None in (close, ext) or not ext else
                           (abs(close / ext - 1.0) * 100.0 >= wall_pct)),
                  "baseline": ((close < rn if side > 0 else close > rn)
                               if rn_appr and close is not None else None)}

    # H4: the monthly third Friday only.
    sess = str(card.get("session"))[:10]
    peak, mp = card.get("peak_gex_strike_morning"), card.get("max_pain")
    elig = True if is_monthly_expiry(sess) else None
    out["pinned"] = {"eligible": elig,
                     "outcome": within(close, peak, pin_pct) if elig else None,
                     "base": within(close, peak, pin_pct),
                     "control": within(close, mp, pin_pct) if elig else None,
                     "baseline": (within(close, nearest_round(close, step), pin_pct)
                                  if elig and close is not None else None)}

    # H5: the next three sessions' realised vol against the prior ten's.
    days = sorted(closes)
    elig = True if card.get("flip_in_range") else None
    fwd = _flip_outcome(sess, days, closes)
    ma_hit = _range_contains_ma(sess, days, closes, hi, lo)
    out["flip_crossing"] = {"eligible": elig, "outcome": fwd if elig else None,
                            "base": fwd,
                            # Baseline: the session's range contained the 20-day
                            # moving average (a price level with no dealer content).
                            "baseline": fwd if ma_hit else None}
    return out


def _flip_outcome(sess: str, days: list[str], closes: dict) -> Optional[bool]:
    if sess not in closes:
        return None
    i = days.index(sess)
    if i < 10 or i + 3 >= len(days):
        return None
    prior = realised_vol([closes[d] for d in days[i - 10:i + 1]])
    nxt = realised_vol([closes[d] for d in days[i:i + 4]])
    return None if prior is None or nxt is None else nxt > prior


def _range_contains_ma(sess, days, closes, hi, lo) -> bool:
    if sess not in closes or None in (hi, lo):
        return False
    i = days.index(sess)
    if i < 20:
        return False
    ma = sum(closes[d] for d in days[i - 20:i]) / 20.0
    return lo <= ma <= hi


def score(cards: list[dict], closes: dict[str, float], cfg: Optional[dict] = None,
          vix: Optional[dict[str, float]] = None) -> list[dict]:
    """Each stored row scored, in session order, with H1/H2's baseline filled
    in: persistence with no dealer content -- the outcome's threshold met at a
    session, given it was met at the session before. `cfg` is the
    `dealer_scorecard` block (read from the config when None)."""
    c = cfg if cfg is not None else config()
    rows = []
    for card in sorted(cards, key=lambda x: str(x.get("session"))):
        day = str(card.get("session"))[:10]
        rows.append({"session": day,
                     "h": score_card(card, closes, c, (vix or {}).get(day))})
    for prev, cur in zip(rows, rows[1:]):
        for h in ("dampened", "amplified"):
            if prev["h"][h]["base"] and cur["h"][h]["base"] is not None:
                cur["h"][h]["baseline"] = cur["h"][h]["base"]
    return rows


# ---------------------------------------------------------------------------
# The rate printer
# ---------------------------------------------------------------------------
def rate(rows: list[dict], h: str, cfg: Optional[dict] = None) -> dict:
    """k/n with its Wilson interval, the base rate and the baseline, sessions and
    episodes, the floors, and the formation/test position, for one hypothesis."""
    c = cfg or {}
    floor = int(c.get("print_floor_sessions", 20))
    decide = int(c.get("decision_floor_eligible", 120))
    form = int(c.get("formation_sessions", 120))
    elig = [r for r in rows if r["h"][h]["eligible"]]
    scored = [r for r in elig if r["h"][h]["outcome"] is not None]
    k = sum(1 for r in scored if r["h"][h]["outcome"])
    n = len(scored)
    base = [r["h"][h]["base"] for r in rows if r["h"][h]["base"] is not None]
    bl = [r["h"][h]["baseline"] for r in rows if r["h"][h].get("baseline") is not None]
    episodes = 0
    prev = False
    for r in rows:
        on = bool(r["h"][h]["eligible"])
        episodes += int(on and not prev)
        prev = on
    out: dict[str, Any] = {"hypothesis": h, "label": LABELS[h], "k": k, "n": n,
                           "eligible": len(elig), "episodes": episodes,
                           "base_rate": (sum(base) / len(base)) if base else None,
                           "base_n": len(base),
                           "baseline": (sum(bl) / len(bl)) if bl else None,
                           "baseline_n": len(bl),
                           "printable": n >= floor, "decision": len(elig) >= decide}
    out["interval"] = wilson(k, n) if out["printable"] else None
    e = len(elig)
    out["phase"] = (f"forming: {e} of {form} eligible sessions" if e < form else
                    f"testing: {min(e - form, form)} of {form}" if e < 2 * form else
                    "formation and test complete: promotion by the registration's rule")
    return out


def rate_line(r: dict) -> str:
    """One printed line. Below the printing floor, the count of scored sessions
    and nothing else; below the decision floor, 'no rate is a decision'."""
    if not r["printable"]:
        return (f"{r['label']}: {r['n']} scored sessions, under the printing floor "
                f"of 20 ({r['phase']}).")
    lo, hi = r["interval"]
    pct = lambda v: "n/a" if v is None else f"{v * 100:.0f}%"   # noqa: E731
    s = (f"{r['label']}: {r['k']}/{r['n']} ({pct(r['k'] / r['n'])}, 95% interval "
         f"{pct(lo)}–{pct(hi)}); base rate {pct(r['base_rate'])} (n={r['base_n']}); "
         f"baseline {pct(r['baseline'])} (n={r['baseline_n']}); {r['n']} sessions, "
         f"{r['episodes']} episodes; {r['phase']}")
    return s + ("." if r["decision"] else "; no rate is a decision.")


def rates_table(rows: list[dict], cfg: Optional[dict] = None) -> dict:
    """The six registered tests, one line each."""
    rs = [rate(rows, h, cfg) for h in HYPOTHESES]
    return {"rates": rs, "lines": [rate_line(r) for r in rs],
            "registered": len(HYPOTHESES), "promoted": 0}
