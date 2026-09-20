"""
Standard derived forms -- ONE function, not one per report.

O.14. Every report that wants a delta, a percentile or a z-score calls
`derived_forms()` and gets the same arithmetic. The alternative is what this repo
already had: each report computing its own delta, each with its own idea of
whether a yield moves in basis points or percent, and no way to tell a
disagreement between two reports from a disagreement between two numbers.

-----------------------------------------------------------------------------
THE FOUR RULES THAT MAKE IT SAFE TO SHARE
-----------------------------------------------------------------------------

1. AS-OF CORRECT, ALWAYS. Every read goes through ObservationStore.as_of(),
   which filters on available_at and never on observed_at. An observation the
   system could not have known at the cutoff cannot change the answer. This is
   the rule tools/validate_derived.py proves rather than assumes: it writes a
   future-dated observation and asserts the result is byte-identical.

2. DELTA SEMANTICS COME FROM THE REGISTRY, NEVER FROM ONE FORMULA. A 10-year
   yield moving 4.45 -> 4.52 is +7 BASIS POINTS; SPY moving 640 -> 646 is
   +0.94 PERCENT; initial claims moving 221K -> 229K is +8 THOUSAND, raw. One
   formula for all three produces numbers that are wrong in two cases out of
   three and look plausible in all three.

   THE FIELD THIS READS IS `units`, NOT `observation_type`. The Phase 2 order
   said observation_type; in this repo that field's vocabulary is
   observed|calculated|inferred -- it records HOW a number came to exist, not
   what a change in it means. `units` (bps, percent, price, count, ratio, ...)
   is the field that carries the delta semantics, and for the 59 FRED series it
   resolves through the bulk import to altdata.config's own units. See
   docs/market-state.md, "Delta semantics".

3. A DELTA WHOSE LOOKBACK LANDS ON THE LEVEL'S OWN OBSERVATION IS None, NOT
   ZERO. Ask a monthly series for its 1-session change and the honest answer is
   "not measured over that span". Zero is a claim that it was measured and did
   not move, which is how a quarterly series ends up reported as the calmest
   thing in the book.

4. CONFIDENCE IS DERIVED, NEVER AUTHORED. It falls out of staleness against the
   registry's information_half_life and of n against the window. There is no
   argument to `derived_forms()` that sets it, deliberately: a confidence an
   author can set is a confidence that reports what the author hoped.

-----------------------------------------------------------------------------
WHAT COMES BACK
-----------------------------------------------------------------------------

    metric_id, instrument, as_of            what was asked
    level, observed_at, available_at        the newest knowable observation
    delta_1d / delta_5d / delta_20d         in delta_unit, or None (rule 3)
    delta_unit                              bps | percent | raw
    rate_of_change, rate_of_change_basis    delta_unit per session
    percentile, z_score                     over the window, own history
    extreme, extreme_rule                   percentile <=5 or >=95 by default
    confidence, confidence_reason           high | med | low
    n, window_requested_days, window_actual_days, first_observed
    staleness_sessions, staleness_allowance_sessions
    session_basis                           how sessions were counted

Usage:
    from altdata import derived
    d = derived.derived_forms("fred.hy_oas", as_of="2026-09-18T21:00:00+00:00")
"""

from __future__ import annotations

import datetime as dt
import math
import statistics
from pathlib import Path
from typing import Any, Optional

from . import observations, session

REPO = Path(__file__).resolve().parent.parent

CONVENTION_VERSION = "derived-forms-v1"

# The default own-history window. Five years is the audit's own choice (§K's
# percentile_5y) and it is long enough to contain one full rate cycle.
DEFAULT_WINDOW_DAYS = 1826

# ---------------------------------------------------------------------------
# DELTA SEMANTICS BY `units`. Rule 2.
#
# Keys are the units vocabularies of BOTH registries: metrics_registry.yaml's
# own list (bps, percent, price, ratio, ...) and the FRED members' shorter one
# (%, $, K, B, M, idx, hrs), which the bulk import passes through verbatim as
# `from_member`. Anything unlisted is `raw` AND SAYS SO in delta_unit_reason,
# because a silent default here is rule 2 quietly failing.
# ---------------------------------------------------------------------------
DELTA_UNITS: dict[str, str] = {
    # Rates and spreads: quoted in percent, moved in basis points.
    "%": "bps",
    "percent": "bps",
    "bps": "bps",
    # Prices and index levels: moved in percent of themselves.
    "$": "percent",
    "price": "percent",
    "idx": "percent",
    "usd": "percent",
    "contract_ccy": "percent",
    "JPY": "percent",
    "CNY": "percent",
    # Counts, levels and stocks: moved in their own units.
    "K": "raw",
    "B": "raw",
    "M": "raw",
    "hrs": "raw",
    "count": "raw",
    "shares": "raw",
    "days": "raw",
    "ratio": "raw",
    "fraction": "raw",
}

# ---------------------------------------------------------------------------
# STALENESS ALLOWANCE BY information_half_life, in SESSIONS.
#
# `until_next_release` is the interesting one: it has no fixed length, it is the
# series' own cadence. So it resolves through the member's `freq` rather than
# guessing, which is why a monthly series is not called stale four days after
# its print and a daily one is.
# ---------------------------------------------------------------------------
HALF_LIFE_SESSIONS: dict[str, Optional[int]] = {
    "intraday": 1,
    "session": 1,
    "week": 5,
    "to_next_expiry": 21,
    "month": 21,
    "permanent": None,          # never stale; a graded outcome does not decay
}

FREQ_SESSIONS: dict[str, int] = {
    "daily": 2,                 # one session's grace: FRED posts next morning
    "weekly": 8,
    "monthly": 32,
    "quarterly": 95,
}

# n against the window. Declared, so "thin" means the same thing everywhere.
N_AMPLE = 250
N_ADEQUATE = 60
N_THIN = 20

EXTREME_LOW = 5.0
EXTREME_HIGH = 95.0


# ---------------------------------------------------------------------------
# Registry resolution
# ---------------------------------------------------------------------------
_REGISTRY: Optional[dict] = None


def _load_registry() -> dict:
    """metrics_registry.yaml, with the bulk imports resolved to real members.

    A FRED series is registered by a BULK BLOCK, not by a line of its own -- the
    registry says so explicitly, to avoid two lists of 59 things drifting. So a
    resolver that only reads `metrics:` would find no entry for fred.hy_oas and
    fall back to a default, which is rule 2 failing silently on 59 of the
    system's series.
    """
    global _REGISTRY
    if _REGISTRY is not None:
        return _REGISTRY
    out: dict[str, dict] = {}
    try:
        import yaml  # noqa: PLC0415
        with (REPO / "metrics_registry.yaml").open(encoding="utf-8") as fp:
            reg = yaml.safe_load(fp) or {}
    except Exception:
        _REGISTRY = out
        return out

    for key, m in (reg.get("metrics") or {}).items():
        if isinstance(m, dict):
            out[key] = dict(m)

    for block in (reg.get("bulk_imports") or {}).values():
        if not isinstance(block, dict):
            continue
        members_from = block.get("members_from")
        prefix = block.get("key_prefix") or ""
        member_key = block.get("member_key")
        if not members_from or not member_key:
            continue
        try:
            import importlib  # noqa: PLC0415
            mod_path, attr = members_from.rsplit(".", 1)
            members = getattr(importlib.import_module(mod_path), attr)
        except Exception:
            continue
        for mem in members or []:
            name = getattr(mem, member_key, None)
            if not name:
                continue
            entry = {k: v for k, v in block.items()
                     if k not in ("members_from", "member_key", "key_prefix",
                                  "expected_members", "description",
                                  "mechanism_group_from_member",
                                  "mechanism_group_map")}
            # `from_member` means "the member owns this field".
            for field in ("units", "native_horizon"):
                if entry.get(field) == "from_member":
                    entry[field] = getattr(mem, field, None) or getattr(
                        mem, "freq" if field == "native_horizon" else field, None)
            entry["freq"] = getattr(mem, "freq", None)
            out.setdefault(prefix + str(name), entry)
    _REGISTRY = out
    return out


def registry_entry(metric_id: str) -> dict:
    return _load_registry().get(metric_id, {})


def delta_unit_for(metric_id: str) -> tuple[str, str]:
    """(delta_unit, why). Rule 2."""
    e = registry_entry(metric_id)
    units = e.get("units")
    if units is None:
        return "raw", (f"no registry entry for {metric_id!r}; treated as raw -- "
                       f"register the metric to give its deltas a meaning")
    du = DELTA_UNITS.get(str(units))
    if du is None:
        return "raw", (f"units {units!r} is not in the delta-semantics table; "
                       f"treated as raw")
    return du, f"units {units!r}"


# ---------------------------------------------------------------------------
# Session arithmetic
# ---------------------------------------------------------------------------
def _as_date(v: Any) -> dt.date:
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    return dt.date.fromisoformat(str(v)[:10])


def sessions_between(start: Any, end: Any) -> tuple[int, str]:
    """Trading sessions from `start` (exclusive) to `end` (inclusive).

    THE CALENDAR ONLY COVERS 2026-2027. altdata/session.py carries the holiday
    table for the years the system has actually run, and the store's history
    reaches back to 2022 -- so a backfill asking about 2023 gets a calendar that
    does not know the answer. Rather than pretend, this counts weekdays and says
    which basis it used, applying the holiday table only over the years it
    covers. A basis stamped on the row is a caveat a reader can act on; a silent
    fallback is a number nobody can check.
    """
    a, b = _as_date(start), _as_date(end)
    if b <= a:
        return 0, "same_session"
    n = 0
    used_calendar = False
    used_weekdays = False
    day = a + dt.timedelta(days=1)
    guard = 0
    while day <= b and guard < 20000:
        guard += 1
        if session.calendar_covers(day):
            used_calendar = True
            if session.is_trading_session(day):
                n += 1
        else:
            used_weekdays = True
            if day.weekday() < 5:
                n += 1
        day += dt.timedelta(days=1)
    basis = ("calendar" if used_calendar and not used_weekdays else
             "weekdays" if used_weekdays and not used_calendar else "mixed")
    return n, basis


def _back_n_sessions(end: Any, n: int) -> dt.date:
    """The date n trading sessions before `end`."""
    day = _as_date(end)
    left = n
    guard = 0
    while left > 0 and guard < 20000:
        guard += 1
        day -= dt.timedelta(days=1)
        if session.calendar_covers(day):
            if session.is_trading_session(day):
                left -= 1
        elif day.weekday() < 5:
            left -= 1
    return day


# ---------------------------------------------------------------------------
# The statistics
# ---------------------------------------------------------------------------
def percentile_of(values: list[float], x: float) -> Optional[float]:
    """Percent of the window's observations at or below x.

    The plain empirical definition, stated here because there are several and a
    percentile whose definition is not written down cannot be replayed. Ties
    count as "at or below", so a series sitting at its own maximum reads 100.
    """
    if not values:
        return None
    le = sum(1 for v in values if v <= x)
    return round(100.0 * le / len(values), 4)


def z_of(values: list[float], x: float) -> Optional[float]:
    if len(values) < 2:
        return None
    try:
        sd = statistics.stdev(values)
    except statistics.StatisticsError:
        return None
    if sd == 0 or not math.isfinite(sd):
        return None
    return round((x - statistics.fmean(values)) / sd, 4)


def _delta(level: float, past: float, unit: str) -> Optional[float]:
    if past is None or level is None:
        return None
    if unit == "bps":
        return round((level - past) * 100.0, 4)
    if unit == "percent":
        if past == 0:
            return None
        return round(100.0 * (level - past) / abs(past), 4)
    return round(level - past, 6)


# ---------------------------------------------------------------------------
# Confidence -- rule 4
# ---------------------------------------------------------------------------
def staleness_allowance(metric_id: str) -> tuple[Optional[int], str]:
    """How many sessions this metric may go unrefreshed before it is stale."""
    e = registry_entry(metric_id)
    hl = e.get("information_half_life")
    if hl == "until_next_release":
        freq = e.get("freq") or e.get("native_horizon")
        n = FREQ_SESSIONS.get(str(freq))
        if n is None:
            return FREQ_SESSIONS["monthly"], (
                f"half_life until_next_release with freq {freq!r} unknown; "
                f"allowed the monthly cadence")
        return n, f"until_next_release at {freq} cadence"
    if hl in HALF_LIFE_SESSIONS:
        return HALF_LIFE_SESSIONS[hl], f"half_life {hl!r}"
    return FREQ_SESSIONS["monthly"], (
        f"half_life {hl!r} not in the table; allowed the monthly cadence")


def confidence_of(staleness: Optional[int], allowance: Optional[int],
                  n: int) -> tuple[str, str]:
    """(high|med|low, why). Declared table, no author input."""
    if staleness is None:
        return "low", "no observation in the window"
    if allowance is None:
        fresh, verdict = True, "half_life permanent -- staleness cannot apply"
    elif staleness <= allowance:
        fresh, verdict = True, f"fresh ({staleness} <= {allowance} sessions)"
    elif staleness <= 3 * allowance:
        fresh, verdict = False, f"stale ({staleness} > {allowance} sessions)"
    else:
        return "low", (f"very stale: {staleness} sessions since the last "
                       f"observation, against an allowance of {allowance}")
    if n < N_THIN:
        return "low", f"{verdict}; n={n} is below {N_THIN}"
    if fresh and n >= N_AMPLE:
        return "high", f"{verdict}; n={n}"
    if n < N_ADEQUATE:
        return "low", f"{verdict}; n={n} is below {N_ADEQUATE}"
    return "med", f"{verdict}; n={n}"


# ---------------------------------------------------------------------------
# The one function
# ---------------------------------------------------------------------------
def derived_forms(metric_id: str, as_of: Optional[str] = None,
                  window: Optional[int] = None,
                  store: Optional[observations.ObservationStore] = None,
                  instrument: Optional[str] = None) -> dict:
    """Level, deltas, rate of change, percentile, z, extreme, confidence, n.

    `window` is a number of CALENDAR DAYS of own history, defaulting to the
    registry's `derived_window_days` for the metric and then to five years. When
    the store holds less than the window, what exists is used and
    window_actual_days records it -- a short history is a caveat, not a failure,
    and refusing to compute would mean no report could print anything until the
    store was five years old.
    """
    cutoff = as_of or session.utc_iso(timespec="microseconds")
    own = store is None
    st = store or observations.ObservationStore()
    e = registry_entry(metric_id)
    try:
        rows = st.as_of(metric_id, as_of=cutoff, instrument=instrument)
    finally:
        if own:
            st.close()

    req_window = int(window or e.get("derived_window_days")
                     or DEFAULT_WINDOW_DAYS)
    du, du_why = delta_unit_for(metric_id)
    lo, hi = EXTREME_LOW, EXTREME_HIGH
    override = e.get("extreme_percentiles")
    extreme_rule = f"percentile <= {lo} or >= {hi} (default)"
    if isinstance(override, (list, tuple)) and len(override) == 2:
        lo, hi = float(override[0]), float(override[1])
        extreme_rule = f"percentile <= {lo} or >= {hi} (registry override)"

    out: dict[str, Any] = {
        "metric_id": metric_id,
        "instrument": instrument,
        "as_of": cutoff,
        "convention_version": CONVENTION_VERSION,
        "delta_unit": du,
        "delta_unit_reason": du_why,
        "window_requested_days": req_window,
        "extreme_rule": extreme_rule,
        "registered": bool(e),
        "level": None, "observed_at": None, "available_at": None,
        "delta_1d": None, "delta_5d": None, "delta_20d": None,
        "rate_of_change": None, "rate_of_change_basis": None,
        "percentile": None, "z_score": None, "extreme": None,
        "n": 0, "window_actual_days": 0, "first_observed": None,
        "staleness_sessions": None, "staleness_allowance_sessions": None,
        "session_basis": None,
        "confidence": "low", "confidence_reason": "no observations",
    }

    series = [(str(r["observed_at"])[:10], r["value_num"], r["available_at"])
              for r in rows if r.get("value_num") is not None]
    if not series:
        out["absent_reason"] = (
            f"no numeric observation for {metric_id!r} knowable at {cutoff}")
        return out
    series.sort(key=lambda t: t[0])

    as_of_day = _as_date(cutoff)
    start_day = as_of_day - dt.timedelta(days=req_window)
    windowed = [(d, v, a) for d, v, a in series if _as_date(d) >= start_day]
    if not windowed:                    # every observation predates the window
        windowed = series[-1:]

    level_day, level, level_avail = windowed[-1]
    values = [v for _, v, _ in windowed]

    allowance, allow_why = staleness_allowance(metric_id)
    stale, basis = sessions_between(level_day, as_of_day)
    conf, conf_why = confidence_of(stale, allowance, len(values))

    out.update({
        "level": level,
        "observed_at": level_day,
        "available_at": level_avail,
        "n": len(values),
        "first_observed": windowed[0][0],
        "window_actual_days": (as_of_day - _as_date(windowed[0][0])).days,
        "percentile": percentile_of(values, level),
        "z_score": z_of(values, level),
        "staleness_sessions": stale,
        "staleness_allowance_sessions": allowance,
        "staleness_basis": allow_why,
        "session_basis": basis,
        "confidence": conf,
        "confidence_reason": conf_why,
    })
    pct = out["percentile"]
    out["extreme"] = None if pct is None else bool(pct <= lo or pct >= hi)

    # Deltas. Rule 3: a lookback that resolves to the level's own observation is
    # None. `by_day` is built over the FULL series, not the window, so a 20-
    # session lookback still works on the window's first day.
    by_day = {d: v for d, v, _ in series}
    days_sorted = [d for d, _, _ in series]
    for label, k in (("delta_1d", 1), ("delta_5d", 5), ("delta_20d", 20)):
        target = _back_n_sessions(as_of_day, k).isoformat()
        prior = None
        for d in reversed(days_sorted):
            if d <= target:
                prior = d
                break
        if prior is None or prior == level_day:
            continue
        out[label] = _delta(level, by_day[prior], du)
        out[f"{label}_from"] = prior

    for label, k in (("delta_20d", 20), ("delta_5d", 5), ("delta_1d", 1)):
        if out.get(label) is not None:
            out["rate_of_change"] = round(out[label] / k, 6)
            out["rate_of_change_basis"] = f"{label} over {k} sessions"
            break

    return out


def _main(argv: list[str]) -> int:
    import argparse
    import json
    p = argparse.ArgumentParser(description="Standard derived forms for a metric.")
    p.add_argument("metric_id")
    p.add_argument("--as-of", default=None)
    p.add_argument("--window", type=int, default=None)
    p.add_argument("--instrument", default=None)
    a = p.parse_args(argv)
    print(json.dumps(derived_forms(a.metric_id, a.as_of, a.window,
                                   instrument=a.instrument),
                     indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
