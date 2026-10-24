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

import bisect as _bisect
import contextlib as _contextlib
import datetime as dt
import math
import re
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
    "percent": "bps",    # the undivided unit; check_registry refuses it on an entry
    "bps": "bps",
    # PERCENT, SPLIT BY MEANING (AUD-3a item 3, 14 Oct 2026). One word covered a
    # yield, a percentile, a return and a share, so a percentile moving 40 -> 55
    # read +1,500 bp. Each meaning is now its own unit, with its own delta rule:
    "percent_rate": "bps",     # a yield, rate or spread level: 4.45 -> 4.52 is +7 bp
    "percentile": "pts",       # an own-history rank, 0..100: 40 -> 55 is +15 pts
    "percent_return": "pp",    # a return, growth rate or distance: 1.2 -> 1.5 is +0.3 pp
    "percent_share": "pp",     # a share of a whole: 36% -> 45% of sectors is +9 pp
    "vol_pct": "pts",          # an annualised volatility in percent: 18 -> 20 is +2 pts
    "vol_index": "pts",        # a volatility index level (^VIX): 18 -> 20 is +2 pts
    # An index level that is neither a price nor a volatility (^SKEW; ruled 15 Oct
    # 2026): 140 -> 146 is +6 pts, where a percent change of it means nothing.
    "index_points": "pts",
    # Prices and index levels: moved in percent of themselves.
    "$": "percent",
    "price": "percent",
    "idx": "percent",
    "usd": "percent",
    "contract_ccy": "percent",
    "JPY": "percent",
    "CNY": "percent",
    "MXN": "percent",
    # The H.10 scan tier's quoted currencies (AQ-3 part 1), SR-46's EM six among
    # them (one copy each; Friday stitching): an exchange rate
    # moves in percent of itself, whatever it is quoted in.
    "CAD": "percent", "CHF": "percent", "SEK": "percent", "NOK": "percent",
    "DKK": "percent", "BRL": "percent", "ZAR": "percent", "KRW": "percent",
    "TWD": "percent", "INR": "percent", "SGD": "percent", "HKD": "percent",
    "MYR": "percent", "LKR": "percent", "VES": "percent", "THB": "percent",
    # Counts, levels and stocks: moved in their own units.
    "K": "raw",
    "N": "raw",          # a plain count (FRED "Number": IC4WSA, EXHOSLUSM495S)
    "B": "raw",
    "M": "raw",
    # A EURO stock in millions (ECBASSETSW; 6e-releases, ruling (a)5 of 16 Oct
    # 2026): "M" reads as dollars in the renderers, so the currency is the unit.
    "EUR_M": "raw",
    "hrs": "raw",
    "count": "raw",
    "shares": "raw",
    "days": "raw",
    "hours": "raw",
    "ratio": "raw",
    "fraction": "raw",
    "0/1": "raw",        # a 0/1 indicator (USREC); its change is the flip itself
}

# PERCENTAGE POINTS, for the one case `units` cannot separate on its own.
#
# `percent` covers two different things in this repo. A SPREAD quoted in percent
# moves in basis points, and that is the convention every rates desk uses: HY OAS
# 2.70 -> 2.72 is +2bp. A SHARE quoted in percent does not: breadth going from 36%
# of sectors to 45% is +9 POINTS, and reporting it as +900bp in a block a human
# reads fast is technically correct and actively misleading.
#
# So a metric may declare `delta_unit: pp` in the registry. It is an OVERRIDE and
# not a second rule: `units` still decides by default, the override must be
# written down per metric, and tools/validate_derived.py asserts that any value
# here is one of the declared units rather than a typo that silently falls back.
DELTA_UNIT_OVERRIDE = "delta_unit"
DELTA_UNITS_ALL = ("bps", "percent", "raw", "pp", "pts")

# HOW A LEVEL PRINTS, which the split must not move (AUD-3a item 3). The
# renderers format a level from its registry units -- "4.45%" for percent, a bare
# number for a price -- and every one of them compares against the OLD words. So
# each new unit names the word its level printed under before the split: the five
# percent meanings still print as percent, and the VIX, a price until then, still
# prints as one. A renderer reads `level_units()`, never the raw split unit.
LEVEL_UNITS: dict[str, str] = {
    "percent_rate": "percent",
    "percentile": "percent",
    "percent_return": "percent",
    "percent_share": "percent",
    "vol_pct": "percent",
    "vol_index": "price",
    "index_points": "price",
}


def level_units(units: Any) -> str:
    """The units word a level is formatted under: the split units map back to the
    word they printed as (LEVEL_UNITS); every other unit is itself."""
    u = str(units or "")
    return LEVEL_UNITS.get(u, u)


def level_units_of(key_or_entry: Any) -> str:
    """The units word one metric's level is formatted under. A block member whose
    unit member_units overrode prints under the word it had before the override
    (`level_as`: FRED's "%", the closes' "price"); every other entry under
    level_units() of its units. Renderers call this, never the raw unit."""
    e = (key_or_entry if isinstance(key_or_entry, dict)
         else registry_entry(str(key_or_entry))) or {}
    if e.get("level_as") is not None:
        return str(e["level_as"])
    return level_units(e.get("units"))

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
    # An annual table -- Damodaran's multiples, French's BE/ME -- is current for a
    # year. Without this it fell back to the monthly allowance and would read stale
    # eleven months in twelve (signal-triage order ST-2).
    "annual": 260,
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
    try:
        import yaml  # noqa: PLC0415
        with (REPO / "metrics_registry.yaml").open(encoding="utf-8") as fp:
            reg = yaml.safe_load(fp) or {}
    except Exception:
        _REGISTRY = {}
        return _REGISTRY
    _REGISTRY = resolve_registry(reg)
    return _REGISTRY


def resolve_registry(reg: dict, by_block: Optional[dict] = None) -> dict:
    """Every key a registry dict declares, bulk members expanded, as
    {key: entry}. Pure: tools/check_registry.py runs it over the real registry
    and a gate over a synthetic one. `by_block`, given, collects
    {block id: [keys it expanded to]} -- an empty list is a block that resolves
    to nothing, the failure AUD-3a item 2 closes."""
    import importlib  # noqa: PLC0415
    out: dict[str, dict] = {}
    for key, m in (reg.get("metrics") or {}).items():
        if isinstance(m, dict):
            out[key] = dict(m)

    for bid, block in (reg.get("bulk_imports") or {}).items():
        if not isinstance(block, dict):
            continue
        members_from = block.get("members_from")
        prefix = block.get("key_prefix") or ""
        member_key = block.get("member_key")
        members_are = block.get("members_are")
        suffixes = list(block.get("member_suffixes") or [""])
        if not members_from:
            continue
        if by_block is not None:
            by_block.setdefault(bid, [])
        try:
            mod_path, attr = members_from.rsplit(".", 1)
            members = getattr(importlib.import_module(mod_path), attr)
        except Exception:
            continue
        # A member list is a sequence of objects with a named attribute (the 59
        # FRED SeriesSpec entries) OR a mapping whose VALUES are the store keys
        # (the 28-symbol price basket). The block says which; neither is guessed.
        if members_are == "values" and isinstance(members, dict):
            members = list(members.values())
        elif members_are == "keys" and isinstance(members, dict):
            members = list(members.keys())
        # A PLAIN LIST OF NAMES (AUD-3a item 2). A block with neither member_key
        # nor members_are names its members directly -- the overnight keys, the
        # events table's columns, the pin log's -- and check_registry has always
        # read it so. This resolver skipped it, so all 46 overnight.* keys and
        # three column blocks resolved to no entry and their deltas fell to raw.
        member_units = dict(block.get("member_units") or {})
        member_families = dict(block.get("member_families") or {})
        for mem in members or []:
            name = (getattr(mem, member_key, None) if member_key
                    else (mem if isinstance(mem, str) else None))
            if not name:
                continue
            entry = {k: v for k, v in block.items()
                     if k not in ("members_from", "member_key", "key_prefix",
                                  "expected_members", "description",
                                  "members_are", "member_suffixes",
                                  "mechanism_group_from_member",
                                  "mechanism_group_map", "member_units",
                                  "member_families")}
            entry["bulk_block"] = bid
            # `from_member` means "the member owns this field". A member named as
            # a string has no attributes: its units are the individually
            # registered metric's whose leaf it is (the pin log's columns), as
            # check_registry's coverage reads it -- or none, and the delta says so.
            for field in ("units", "native_horizon"):
                if entry.get(field) == "from_member":
                    if isinstance(mem, str):
                        entry[field] = _leaf_field(reg, mem, field)
                    else:
                        entry[field] = getattr(mem, field, None) or getattr(
                            mem, "freq" if field == "native_horizon" else field,
                            None)
            entry["freq"] = getattr(mem, "freq", None)
            for suffix in suffixes:
                key = prefix + str(name) + suffix
                e = dict(entry)
                # ONE MEMBER'S OWN UNITS (AUD-3a item 3): ^TNX is a yield and ^VIX
                # a volatility index inside a block of prices. Declared per store
                # key in the block, so the exception is visible in the registry.
                if key in member_families:            # 6e: a mixed block's member
                    e["family"] = member_families[key]
                if key in member_units:
                    # A member that owns its units (`from_member`: FRED's "%")
                    # keeps the word its level printed under before the override,
                    # since "%" prints bare where a metric's "percent" prints with
                    # its sign (15 Oct 2026). A block whose units are its own
                    # (the closes' price) maps through LEVEL_UNITS: ^TNX with %,
                    # as accepted on 15 Oct.
                    if block.get("units") == "from_member":
                        e["level_as"] = e.get("units")
                    e["units"] = member_units[key]
                out.setdefault(key, e)
                if by_block is not None:
                    by_block[bid].append(key)
    # THE LENS FIELDS (6e). The `families` map names a family per key (over a
    # block's, under a metric's own); `long_windows` the long percentile's window
    # per key; `lens_excluded` the series that are not levels, by key or block.
    inline = {k for k, m in (reg.get("metrics") or {}).items()
              if isinstance(m, dict) and m.get("family")}
    for key, fam in (reg.get("families") or {}).items():
        if key in out and key not in inline:
            out[key]["family"] = fam
    for key, lw in (reg.get("long_windows") or {}).items():
        if key in out:
            out[key]["long_window"] = lw
    excl = reg.get("lens_excluded") or {}
    for key, e in out.items():
        why = excl.get(key) or excl.get(e.get("bulk_block") or "\0")
        if why and not e.get("family"):
            e["lens_excluded"] = why
    # THE MARKET-STATE BAR (6f tranche 5; ruling 12a): every key an order keeps
    # out of the object carries `market_state: barred` and the order that bars it.
    import fnmatch  # noqa: PLC0415
    for bar in reg.get("market_state_barred") or []:
        pats = list(bar.get("keys") or [])
        for key, e in out.items():
            if any(fnmatch.fnmatchcase(key, g) for g in pats):
                e["market_state"] = "barred"
                e.setdefault("market_state_barred_by", []).append(
                    {"order": bar.get("order"), "rule": bar.get("rule"),
                     "instruments": bar.get("instruments")})
    return out


def market_state_barred(e: Optional[dict], instrument: Optional[str] = None) -> Optional[str]:
    """The order that bars this key (or this instrument of it) from the
    market-state object, or None (6f tranche 5)."""
    for b in (e or {}).get("market_state_barred_by") or []:
        inst = b.get("instruments")
        if not inst or (instrument is not None and instrument in inst):
            return str(b.get("order"))
    return None


def _leaf_field(reg: dict, name: str, field: str) -> Any:
    """`field` of the one registered metric whose dotted id ends in `name`, or
    None when no metric, or more than one, does."""
    hits = [m.get(field) for k, m in (reg.get("metrics") or {}).items()
            if isinstance(m, dict) and k.rsplit(".", 1)[-1] == name]
    return hits[0] if len(hits) == 1 else None


def registry_entry(metric_id: str) -> dict:
    return _load_registry().get(metric_id, {})


_FORWARD: Optional[dict] = None


def forward_dated(metric_id: str) -> Optional[str]:
    """The registry's reason a series may be dated after its publication (an
    effective date; W8-9), or None: metrics_registry.yaml `forward_dated`."""
    global _FORWARD
    if _FORWARD is None:
        try:
            import yaml  # noqa: PLC0415
            with (REPO / "metrics_registry.yaml").open(encoding="utf-8") as fp:
                _FORWARD = dict((yaml.safe_load(fp) or {}).get("forward_dated") or {})
        except Exception:                                       # noqa: BLE001
            _FORWARD = {}
    return _FORWARD.get(metric_id)


def delta_unit_for(metric_id: str) -> tuple[str, str]:
    """(delta_unit, why). Rule 2."""
    e = registry_entry(metric_id)
    override = e.get(DELTA_UNIT_OVERRIDE)
    if override:
        if override not in DELTA_UNITS_ALL:
            return "raw", (f"delta_unit {override!r} is not one of "
                           f"{DELTA_UNITS_ALL}; treated as raw")
        return override, f"registry delta_unit {override!r}"
    units = e.get("units")
    if units is None and e:
        return "raw", (f"{metric_id!r} is registered (bulk block "
                       f"{e.get('bulk_block')!r}) with no units; treated as raw")
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
    # `pp` and `raw` are both a plain difference; they differ only in what the
    # number is called, which is what a reader needs and the arithmetic does not.
    return round(level - past, 6)


# ---------------------------------------------------------------------------
# Confidence -- rule 4
# ---------------------------------------------------------------------------
def probability_points(level: Optional[float], past: Optional[float]
                       ) -> Optional[float]:
    """A change in a 0..1 probability, in PERCENTAGE POINTS (6d).

    Here and not in the caller because this module is the one place a delta is
    computed: a venue's 0.62 -> 0.74 is +12.0 points, never "+19%" (the relative
    change a `fraction` would otherwise invite) and never +0.12 printed as if it
    were points."""
    if level is None or past is None:
        return None
    return round((float(level) - float(past)) * 100.0, 2)


def rate_bp_change(level_pct: Optional[float], past_pct: Optional[float]
                   ) -> Optional[float]:
    """A change in a rate quoted in percent, in basis points (6d rate path)."""
    if level_pct is None or past_pct is None:
        return None
    return round((float(level_pct) - float(past_pct)) * 100.0, 2)


def staleness_allowance(metric_id: str) -> tuple[Optional[int], str]:
    """How many sessions this metric may go unrefreshed before it is stale."""
    return staleness_allowance_of(registry_entry(metric_id), metric_id)


PUBLICATION_LAGS_PATH = REPO / "config" / "publication_lags.yaml"
_LAGS: Optional[list[dict]] = None


def publication_lags(path: Optional[Path] = None) -> list[dict]:
    """config/publication_lags.yaml's families (b51, 21 Oct 2026), loaded once."""
    global _LAGS
    if path is not None:
        import yaml  # noqa: PLC0415
        return list((yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {})
                    .get("families") or [])
    if _LAGS is None:
        try:
            _LAGS = publication_lags(PUBLICATION_LAGS_PATH)
        except OSError:
            _LAGS = []
    return _LAGS


_FRED_IDS: Optional[dict[str, str]] = None


def _fred_ids() -> dict[str, str]:
    global _FRED_IDS
    if _FRED_IDS is None:
        from . import config  # noqa: PLC0415
        _FRED_IDS = {f"fred.{s.key}": s.fred_id for s in config.FRED_PULL_SERIES}
    return _FRED_IDS


def publication_lag(e: dict, metric_id: str,
                    families: Optional[list[dict]] = None) -> tuple[int, Optional[str]]:
    """(sessions, family id) of the first family that matches the key: by its
    FRED id or its store key, globbed, and by the entry's freq where the family
    names one. (0, None) when none does."""
    import fnmatch  # noqa: PLC0415
    fams = publication_lags() if families is None else families
    if not fams or not metric_id:
        return 0, None
    freq = str((e or {}).get("freq") or (e or {}).get("native_horizon") or "")
    fid = _fred_ids().get(metric_id) if metric_id.startswith("fred.") else None
    for f in fams:
        if f.get("freq") and f["freq"] != freq:
            continue
        if (fid and any(fnmatch.fnmatchcase(fid, g) for g in f.get("fred_ids") or [])) \
                or any(fnmatch.fnmatchcase(metric_id, g) for g in f.get("keys") or []):
            return int(f.get("lag_sessions") or 0), f.get("id")
    return 0, None


def staleness_allowance_of(e: dict, metric_id: str = "") -> tuple[Optional[int], str]:
    """The same rule over an entry already resolved (tools/check_store_registry.py
    resolves a registry of its own and reads it here, so the store check and the
    reports' confidence cannot hold two staleness rules).

    A SOURCE'S PUBLICATION LAG (b51, 21 Oct 2026) is added to the cadence's
    allowance where config/publication_lags.yaml names its family: the age of a
    key is counted from its observation date, and a source that publishes a
    week or two months after it is not stale for doing so."""
    base, why = _cadence_allowance(e)
    if base is None:
        return base, why
    lag, fam = publication_lag(e, metric_id)
    if lag:
        return base + lag, f"{why}, plus {lag} sessions' publication lag ({fam})"
    return base, why


def _cadence_allowance(e: dict) -> tuple[Optional[int], str]:
    hl = (e or {}).get("information_half_life")
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
# ---------------------------------------------------------------------------
# THE RUN-SCOPED ROW CACHE
# ---------------------------------------------------------------------------
# WHAT IT DOES NOT DO, first, because that is what makes it safe: it does not
# compute a single derived form. The arithmetic stays in derived_forms() and there
# is exactly one implementation of it. All this does is answer the AS-OF QUESTION
# from memory instead of from SQLite -- and that question was the whole cost.
#
# The measurement that motivated it: one market-state object took 3.0s, of which
# 0.77s was fifty as_of() queries and 0.67s was reading the object history. The
# as_of join is a correlated subquery per row, so a backfill asked it 1,300 times
# per metric over the same rows -- 9,247 of them for yfinance.mkt_vix.
#
# HOW IT STAYS AS-OF CORRECT, which is the only thing that matters here:
#
#   * Rows are loaded in AVAILABILITY order and folded in as they become
#     knowable. A row is visible to a cutoff if and only if its available_at is
#     at or before it -- the same test the SQL makes, on the same canonicalised
#     strings.
#   * Per period it keeps the rows at the GREATEST visible available_at, which is
#     what the correlated subquery selects. Ties are kept as a list rather than
#     collapsed, because the store's uniqueness key includes `source` and two
#     sources may legitimately hold one period at one instant -- as_of() returns
#     both, so this returns both.
#   * A cutoff EARLIER than the last one asked rebuilds from scratch. A backfill
#     walks forward, so the fast path is the normal one and going backwards is
#     correct rather than fast.
#
# `tools/validate_derived.py` group E compares cached against uncached forms over
# a sample of metrics and dates. That comparison is the contract: a cache that
# returns anything but what the query returns is a cache that rewrites history.
class RowCache:
    """One series' vintages, loaded once, joined as-of in memory."""

    def __init__(self, store: observations.ObservationStore) -> None:
        self.store = store
        self._rows: dict[tuple, list[dict]] = {}
        self._state: dict[tuple, dict] = {}
        self.loads = 0
        self.hits = 0

    def rows(self, metric_id: str, cutoff: str,
             instrument: Optional[str] = None) -> list[dict]:
        key = (metric_id, instrument)
        if key not in self._rows:
            self._rows[key] = self.store.all_vintages(metric_id, instrument)
            self._state[key] = {"i": 0, "cutoff": "", "by_day": {}, "days": []}
            self.loads += 1
        self.hits += 1
        cut = observations.canonical_instant(cutoff)
        st = self._state[key]
        if cut < st["cutoff"]:
            st.update({"i": 0, "cutoff": "", "by_day": {}, "days": []})
        rows, by_day, days = self._rows[key], st["by_day"], st["days"]
        i = st["i"]
        while i < len(rows) and str(rows[i]["available_at"]) <= cut:
            r = rows[i]
            day = str(r["observed_at"])
            held = by_day.get(day)
            if held is None:
                by_day[day] = [r]
                _bisect.insort(days, day)
            else:
                avail = str(r["available_at"])
                best = str(held[0]["available_at"])
                if avail > best:
                    by_day[day] = [r]
                elif avail == best:
                    held.append(r)
            i += 1
        st["i"], st["cutoff"] = i, cut
        out: list[dict] = []
        for day in days:
            out.extend(by_day[day])
        # The source tier between rows at one instant (audit-leftovers-2), the
        # same rule as_of() applies, so the cache still answers what the query does.
        return observations.prefer_tier(out, metric_id)


_CACHE: Optional[RowCache] = None


@_contextlib.contextmanager
def row_cache(store: observations.ObservationStore):
    """Cache every series this block reads, then drop it.

    A context manager rather than a switch, because a cache with no end is a
    process that answers yesterday's question: the store is appended to by other
    passes, and a cached series outliving the run it was loaded for would hide
    rows written after it. Nested use reuses the outer cache.
    """
    global _CACHE
    if _CACHE is not None:
        yield _CACHE
        return
    _CACHE = RowCache(store)
    try:
        yield _CACHE
    finally:
        _CACHE = None


def cache_stats() -> Optional[dict]:
    return (None if _CACHE is None else
            {"series_loaded": _CACHE.loads, "queries_served": _CACHE.hits})


def _rows_as_of(metric_id: str, cutoff: str,
                store: observations.ObservationStore,
                instrument: Optional[str] = None) -> list[dict]:
    """The as-of rows, from the cache when a run has one open."""
    if _CACHE is not None and _CACHE.store is store:
        return _CACHE.rows(metric_id, cutoff, instrument)
    return store.as_of(metric_id, as_of=cutoff, instrument=instrument)


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
        rows = _rows_as_of(metric_id, cutoff, st, instrument)
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


def delta_percentile(metric_id: str, as_of: Optional[str] = None,
                     window: Optional[int] = None,
                     horizon: int = 1,
                     store: Optional[observations.ObservationStore] = None,
                     instrument: Optional[str] = None) -> dict:
    """Where the latest n-observation CHANGE sits among that window's changes.

    NOT the same question as derived_forms()' `percentile`, and the difference is
    the one a reader of the close report needs. `percentile` places the LEVEL: SPY
    at the 98th percentile of five years means it is near its high. This places the
    MOVE: a -1.4% session at the 7th percentile of five years of sessions means the
    day was unusual. A report that printed only the first would say the market is
    high on a day it fell hard, and say nothing about the fall.

    It lives here because this module is the one place a delta, a percentile or a
    z-score is computed, and because it must use THE SAME window rule and THE SAME
    as-of join as everything else -- a move percentile measured over a different
    window than the level percentile printed beside it would be two numbers
    pretending to share a denominator.

    The change is in the metric's own delta unit, from delta_unit_for(): percent of
    level for a price, basis points for a spread. So the distribution and the
    latest change are always in the same unit as each other.
    """
    rows = series_as_of(metric_id, as_of=as_of, window=window, store=store,
                        instrument=instrument)
    unit, unit_reason = delta_unit_for(metric_id)
    out: dict[str, Any] = {"metric_id": metric_id, "horizon": horizon,
                           "delta_unit": unit, "delta_unit_reason": unit_reason,
                           "n": 0, "change": None, "percentile": None}
    if len(rows) < horizon + 2:
        out["absent_reason"] = (
            f"{len(rows)} observation(s) in the window; a {horizon}-observation "
            f"change needs at least {horizon + 2} to have a distribution to sit in")
        return out
    changes: list[float] = []
    for i in range(horizon, len(rows)):
        a, b = rows[i - horizon][1], rows[i][1]
        ch = _delta_in_unit(a, b, unit)
        if ch is not None:
            changes.append(ch)
    if not changes:
        out["absent_reason"] = "no change could be expressed in the delta unit"
        return out
    out.update({
        "n": len(changes),
        "change": round(changes[-1], 4),
        "from_date": rows[-1 - horizon][0],
        "to_date": rows[-1][0],
        "percentile": percentile_of(changes, changes[-1]),
        "z_score": (round(z_of(changes, changes[-1]), 4)
                    if z_of(changes, changes[-1]) is not None else None),
        "window_days": window,
        "distribution": {"p5": round(percentile_at(changes, 5), 4),
                         "median": round(percentile_at(changes, 50), 4),
                         "p95": round(percentile_at(changes, 95), 4)},
    })
    return out


def extreme_side(exception: dict) -> dict:
    """Which tail an `extreme` exception sits in: {percentile, side, label}.

    Weekly edition 1, item 3. "fred.rrp at a five-year extreme" does not say
    whether the drain is at its lowest or its highest in five years, and those
    are opposite readings of liquidity. The side comes from the exception's own
    percentile against its own declared rule ("percentile <= 5 or >= 95"), so a
    changed threshold changes the label with it. A contradiction exception has
    no side and returns {}.
    """
    if (exception or {}).get("kind") != "extreme":
        return {}
    v = exception.get("value")
    if not isinstance(v, (int, float)):
        return {}
    rule = str(exception.get("threshold") or "")
    lo = re.search(r"<=\s*([\d.]+)", rule)
    hi = re.search(r">=\s*([\d.]+)", rule)
    lo_v = float(lo.group(1)) if lo else 5.0
    hi_v = float(hi.group(1)) if hi else 95.0
    side = "low" if v <= lo_v else ("high" if v >= hi_v else "inside")
    mark = {"low": f"\u2264{lo_v:g}", "high": f"\u2265{hi_v:g}",
            "inside": f"inside {lo_v:g}..{hi_v:g}"}[side]
    return {"percentile": round(float(v), 1), "side": side,
            "label": f"{float(v):.1f} ({mark})"}


def percentile_at(values: list[float], q: float) -> float:
    """The q-th percentile by linear interpolation -- the inverse of percentile_of.

    percentile_of() answers "where does x sit"; this answers "what value sits at
    q". Both are needed and they are not each other's inverse by accident: the
    empirical definition of one is a counting rule and of the other an
    interpolation, so a round trip is not exact and neither is wrong.
    """
    s = sorted(values)
    if not s:
        return float("nan")
    if len(s) == 1:
        return float(s[0])
    pos = (q / 100.0) * (len(s) - 1)
    lo = int(pos // 1)
    hi = min(lo + 1, len(s) - 1)
    return float(s[lo] + (s[hi] - s[lo]) * (pos - lo))


def long_run_average(metric_id: str, as_of: Optional[str] = None,
                     store: Optional[observations.ObservationStore] = None,
                     instrument: Optional[str] = None) -> dict:
    """The mean of EVERY observation knowable at the cutoff, with its span.

    The slow layers' middle term (T3; the JPM Guide's latest / long-run average /
    percentile triple). Until the metric lenses (6e) declare each family's
    `long_window`, "long run" means the store's full history, and the span is
    returned so a report prints the window beside the average rather than
    implying a century the store may not hold. Each observed day counts once, at
    its newest vintage knowable at the cutoff -- the same as-of join as every
    other form here.
    """
    cutoff = as_of or session.utc_iso(timespec="microseconds")
    own = store is None
    st = store or observations.ObservationStore()
    try:
        rows = _rows_as_of(metric_id, cutoff, st, instrument)
    finally:
        if own:
            st.close()
    vals = sorted((str(r["observed_at"])[:10], float(r["value_num"]))
                  for r in rows if r.get("value_num") is not None)
    if not vals:
        return {"metric_id": metric_id, "mean": None, "n": 0, "first_observed": None,
                "last_observed": None,
                "absent_reason": f"no numeric observation for {metric_id!r} "
                                 f"knowable at {cutoff}"}
    return {"metric_id": metric_id, "mean": sum(v for _, v in vals) / len(vals),
            "n": len(vals), "first_observed": vals[0][0],
            "last_observed": vals[-1][0]}


# THE z OF A PERIOD'S CHANGE (W-1.1 item 1.0b, ruled 11 Oct 2026). Ranking a
# week's moves relative to their level favoured low-level series: IG OAS -4 bp on
# a 0.80% level outranked CCC OAS +37 bp on 9.6%, and Plumbing's prose read "no
# stress" in the week of the CCC blow-out. A move is now ranked by how unusual it
# is for ITS OWN series: the change over the period against every same-length
# change in the trailing year, in the unit the table prints (bp for a rate or a
# spread, percent for a price, the raw unit otherwise). Fewer than
# CHANGE_Z_MIN_N such changes and the z is not computed: the caller ranks that
# move relative to its level and says so.
CHANGE_Z_MIN_N = 60


def change_in_unit(a: float, b: float, unit: str, level_units: str = "") -> Optional[float]:
    """b minus a as a table prints it: "bp" (a percent level x100, a bps level
    as is), "%" (relative), anything else the raw difference."""
    if unit == "bp":
        return (b - a) * (1.0 if str(level_units) in ("bps", "bp") else 100.0)
    if unit == "%":
        return None if not a else 100.0 * (b / a - 1.0)
    return b - a


def period_change_z(series: list[tuple[str, float]], end_day: str, unit: str,
                    level_units: str = "", days: int = 7, trailing_days: int = 365,
                    min_n: int = CHANGE_Z_MIN_N) -> dict:
    """{z, change, n, basis, reason} for the `days`-day change to `end_day`.

    Every observation in the trailing year (to the period's start) is the end of
    one historical change: its value less the value latest known `days` earlier.
    A daily series gives about 250 overlapping weekly changes; a weekly series 52,
    which is under the floor -- `basis` "relative" and the reason say so."""
    pts = sorted((str(d)[:10], float(v)) for d, v in series if v is not None)
    pts = [p for p in pts if p[0] <= end_day[:10]]
    if len(pts) < 2:
        return {"z": None, "change": None, "n": 0, "basis": "relative",
                "reason": "fewer than two observations"}
    end = _as_date(end_day)

    def at_or_before(day: dt.date) -> Optional[float]:
        v = None
        for d, x in pts:
            if d <= day.isoformat():
                v = x
            else:
                break
        return v
    start_val = at_or_before(end - dt.timedelta(days=days))
    change = (change_in_unit(start_val, pts[-1][1], unit, level_units)
              if start_val is not None else None)
    lo = (end - dt.timedelta(days=trailing_days + days)).isoformat()
    hist = []
    for d, x in pts:
        if d < lo or d > (end - dt.timedelta(days=days)).isoformat():
            continue
        prev = at_or_before(_as_date(d) - dt.timedelta(days=days))
        if prev is None:
            continue
        c = change_in_unit(prev, x, unit, level_units)
        if c is not None:
            hist.append(c)
    if change is None:
        return {"z": None, "change": None, "n": len(hist), "basis": "relative",
                "reason": "no value a period before the last"}
    if len(hist) < min_n:
        return {"z": None, "change": round(change, 4), "n": len(hist),
                "basis": "relative",
                "reason": f"{len(hist)} trailing-year changes, fewer than {min_n}"}
    z = z_of(hist, change)
    return {"z": None if z is None else round(z, 2), "change": round(change, 4),
            "n": len(hist), "basis": "z" if z is not None else "relative",
            "reason": None if z is not None else "the trailing changes do not vary"}


def _delta_in_unit(a: float, b: float, unit: str) -> Optional[float]:
    """b minus a, expressed in the declared delta unit."""
    if unit == "percent":
        return None if not a else 100.0 * (b / a - 1.0)
    if unit == "bps":
        return (b - a) * 100.0
    if unit == "pp":
        return b - a
    return b - a


def series_as_of(metric_id: str, as_of: Optional[str] = None,
                 window: Optional[int] = None,
                 store: Optional[observations.ObservationStore] = None,
                 instrument: Optional[str] = None) -> list[tuple[str, float]]:
    """The windowed (day, value) series behind derived_forms(), oldest first.

    Exposed because the contradiction table needs two aligned series and not two
    summaries -- and it must use THE SAME window rule and THE SAME as-of join, or
    a divergence would be measured over a period neither leg's percentile was.
    """
    cutoff = as_of or session.utc_iso(timespec="microseconds")
    own = store is None
    st = store or observations.ObservationStore()
    try:
        rows = _rows_as_of(metric_id, cutoff, st, instrument)
    finally:
        if own:
            st.close()
    e = registry_entry(metric_id)
    req = int(window or e.get("derived_window_days") or DEFAULT_WINDOW_DAYS)
    start = _as_date(cutoff) - dt.timedelta(days=req)
    out = [(str(r["observed_at"])[:10], float(r["value_num"]))
           for r in rows if r.get("value_num") is not None
           and _as_date(r["observed_at"]) >= start]
    out.sort()
    return out


# ---------------------------------------------------------------------------
# THE METRIC LENSES (6e; the brief of 1 Oct 2026, ratified at the Doctrine
# monthly of 3-4 Oct, item 6). Each family of metrics is measured its own way:
# a 20-session change on a monthly release is noise, a level percentile on a
# quantity that trends says little, and a five-year percentile reads a 10-year
# yield as "100th" while it sits far below its long history.
#
#   price       returns 1m / 3m / 12m / YTD; drawdown from the 52-week high
#               with the correction and bear flags; 20-day realized volatility
#               and its percentile; the percentile of the 12-month return
#   rate        bp changes 1m / 3m / 12m; level percentiles
#   spread      level percentiles; bp changes 1m / 3m; the widening flag
#   release     year over year, 3- and 6-month annualized (6m: Batch 7 lens
#               21); the surprise against
#               consensus where one is held; a revision line when the latest
#               vintage changed a prior print
#   quantity    year-over-year change; the 3-month change in units; direction
#   conditions  level percentile; z-score; spike against the 1-year average
#   ratio       level percentile; 3-month trend
#
# THE RULES. Dual percentiles (five years and the family's long window, each
# with its window and n); the move's own percentile through delta_percentile();
# point-in-time only (every form reads the as-of join, and a revision line the
# vintages knowable at the cutoff); units from the registry; a form that cannot
# be computed carries its reason in `reasons`, never a blank or a zero; every
# percentile carries its precomputed `_ordinal` (numeral_audit's one helper).
# ---------------------------------------------------------------------------
LENS_VERSION = "lenses-v1"
FAMILIES = ("price", "rate", "spread", "release", "quantity", "conditions", "ratio")

# RATIFIED 4 Oct 2026 (docs/briefs/doctrine-monthly-2026-10-minutes.md item 6).
CORRECTION_PCT = -10.0                     # 6a: from the 52-week high
BEAR_PCT = -20.0                           # 6a
# 6b: per series, bp in three months -- config/metric_lenses.yaml, each with its
# basis (ratified, or session-set under the 16 Oct ruling (d)4).
LENS_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "metric_lenses.yaml"
_LENS_CFG: Optional[dict] = None


def lens_config() -> dict:
    global _LENS_CFG
    if _LENS_CFG is None:
        import yaml  # noqa: PLC0415
        with open(LENS_CONFIG_PATH, encoding="utf-8") as fh:
            _LENS_CFG = yaml.safe_load(fh) or {}
    return _LENS_CFG


def widening_threshold(metric_id: str) -> tuple[Optional[float], Optional[str]]:
    w = (lens_config().get("widening_bp_3m") or {}).get(metric_id)
    return (float(w["bp"]), w.get("basis")) if w else (None, None)


DISAGREEMENT_POINTS = 30.0                 # 6d: pctile_5y against pctile_long
# 6c: the long window by family, in years or "full"; quantities carry none; the
# registry's long_windows map overrides per series, with its reason.
LONG_WINDOW = {"spread": 20, "conditions": 20, "rate": "full", "release": 20,
               "ratio": 20, "price": "full", "quantity": None}
INFLATION = re.compile(r"(^|\.)(cpi|core_cpi|pce|core_pce|sticky_cpi|sticky_core|flex_cpi"
                       r"|breakeven)")   # 6c: inflation full history
UNEMPLOYMENT = re.compile(r"(^|\.)(u3_rate|unemployment)")   # 6e: + a level percentile
DIRECTION_RULE = ("rising when the 1-month and 3-month changes are both above zero, "
                  "falling when both are below, turning otherwise (session-set, 15 Oct)")
PCT_LEVEL_UNITS = ("%", "percent", "percent_rate", "percent_share", "fraction")
NOT_LEVEL_UNITS = ("boolean", "label", "date", "0/1", "by_source", "None", "")


def family_of(metric_id: str) -> tuple[Optional[str], str]:
    """(family, why) from the registry: a family the entry carries, or None
    with the reason (not a level series, or not registered)."""
    e = registry_entry(metric_id)
    if not e:
        return None, f"{metric_id} is not registered"
    if e.get("family") in FAMILIES:
        if str(e.get("units")) in NOT_LEVEL_UNITS:
            return None, (f"declared family {e['family']}, but units {e.get('units')!r}: "
                          f"not a level series (listed for the operator)")
        return e["family"], "registry family"
    if e.get("lens_excluded"):
        return None, f"not a level series: {e['lens_excluded']}"
    return None, f"{metric_id} carries no family in the registry"


def long_window_of(metric_id: str, family: Optional[str]) -> tuple[Any, str]:
    """(years | "full" | None, why), the registry override first (6c)."""
    e = registry_entry(metric_id)
    v = e.get("long_window")
    if v is not None and str(v) != "until_the_lenses":
        m = re.fullmatch(r"(\d+)\s*([yd]?)", str(v).strip())
        if str(v) == "full":
            return "full", "the registry's long_window override"
        if isinstance(v, (int, float)):
            return float(v), "the registry's long_window override"
        if m:
            n = float(m.group(1)) / (365.25 if m.group(2) == "d" else 1.0)
            return n, f"the registry's long_window override ({v})"
        fam_lw = LONG_WINDOW.get(family or "")
        return fam_lw, (f"the registry's long_window {v!r} is not a window; 6c's "
                        f"{family} default (listed for the operator)")
    if family == "release" and INFLATION.search(metric_id):
        return "full", "6c: inflation, full history"
    lw = LONG_WINDOW.get(family or "")
    return lw, f"6c: the {family} family's long window"


def _ord(p: Optional[float]) -> Optional[str]:
    if p is None:
        return None
    from .numeral_audit import percentile_ordinal  # noqa: PLC0415
    return percentile_ordinal(p)


def _months_back(day: dt.date, n: int) -> dt.date:
    y, m = divmod(day.year * 12 + (day.month - 1) - n, 12)
    m += 1
    last = (dt.date(y + (m == 12), m % 12 + 1, 1) - dt.timedelta(days=1)).day
    return dt.date(y, m, min(day.day, last))


def _at_or_before(days: list[str], vals: list[float], day: str) -> Optional[tuple[str, float]]:
    i = _bisect.bisect_right(days, day) - 1
    return (days[i], vals[i]) if i >= 0 else None


def _pct_in_window(series: list[tuple[str, float]], level: float, as_of_day: dt.date,
                   years: Any) -> dict:
    if years is None:
        return {"pct": None, "n": 0, "window": None,
                "reason": "the family carries no long window (6c: quantities none)"}
    if years == "full":
        vals = [v for _, v in series]
        start = series[0][0] if series else None
        label = f"full history from {start}"
    else:
        lo = (as_of_day - dt.timedelta(days=int(round(365.25 * float(years))))).isoformat()
        vals = [v for d, v in series if d >= lo]
        label = f"{years}y"
    if len(vals) < 2:
        return {"pct": None, "n": len(vals), "window": label,
                "reason": f"{len(vals)} observation(s) in the {label} window"}
    return {"pct": percentile_of(vals, level), "n": len(vals), "window": label,
            "reason": None}


def _change(now: float, past: Optional[float], kind: str, bp_scale: float) -> Optional[float]:
    if past is None:
        return None
    if kind == "pct":
        return None if past == 0 else round(100.0 * (now / past - 1.0), 4)
    if kind == "bp":
        return round((now - past) * bp_scale, 4)
    return round(now - past, 6)


def lens_forms(metric_id: str, as_of: Optional[str] = None,
               store: Optional[observations.ObservationStore] = None,
               consensus: Optional[dict] = None) -> dict:
    """The family's forms for one series at `as_of`, point-in-time.

    `consensus`, given, is {period: value} for the release surprise; without it
    the surprise reads a `consensus` value from the events table's release rows
    where one is stored, and otherwise prints its reason."""
    cutoff = as_of or session.utc_iso(timespec="microseconds")
    fam, fam_why = family_of(metric_id)
    e = registry_entry(metric_id)
    units = level_units_of(e) or None
    out: dict[str, Any] = {"metric_id": metric_id, "family": fam, "family_basis": fam_why,
                           "as_of": cutoff, "lens_version": LENS_VERSION, "units": units,
                           "level": None, "observed_at": None, "forms": {}, "reasons": {},
                           "flags": {}}
    if fam is None:
        out["reasons"]["family"] = fam_why
        return out
    own = store is None
    st = store or observations.ObservationStore()
    try:
        rows = _rows_as_of(metric_id, cutoff, st)
        vint = ([r for r in st.all_vintages(metric_id)
                 if str(r["available_at"]) <= observations.canonical_instant(cutoff)]
                if fam == "release" else [])
        mv = (delta_percentile(metric_id, as_of=cutoff, horizon=21, store=st)
              if fam == "price" else {})
    finally:
        if own:
            st.close()
    series = sorted((str(r["observed_at"])[:10], float(r["value_num"]))
                    for r in rows if r.get("value_num") is not None)
    if not series:
        out["reasons"]["level"] = f"no numeric observation knowable at {cutoff}"
        return out
    days = [d for d, _ in series]
    vals = [v for _, v in series]
    level_day, level = series[-1]
    as_of_day = _as_date(cutoff)
    ld = dt.date.fromisoformat(level_day)
    out.update(level=level, observed_at=level_day)
    F, R = out["forms"], out["reasons"]
    bp_scale = 1.0 if str(e.get("units")) in ("bps", "bp") else 100.0

    def back(months: int) -> Optional[float]:
        hit = _at_or_before(days, vals, _months_back(ld, months).isoformat())
        return hit[1] if hit and hit[0] < level_day else None

    def put(name: str, value: Any, why: str) -> None:
        F[name] = value
        if value is None:
            R[name] = why

    def percentiles(long_years: Any, long_why: str) -> None:
        p5 = _pct_in_window(series, level, as_of_day, 5)
        pl = _pct_in_window(series, level, as_of_day, long_years)
        for tag, p in (("pctile_5y", p5), ("pctile_long", pl)):
            put(tag, p["pct"], p["reason"] or "")
            F[f"{tag}_n"], F[f"{tag}_window"] = p["n"], p["window"]
            F[f"{tag}_ordinal"] = _ord(p["pct"])
        F["pctile_long_basis"] = long_why
        if p5["pct"] is not None and pl["pct"] is not None:
            out["flags"]["percentiles_disagree"] = abs(p5["pct"] - pl["pct"]) >= DISAGREEMENT_POINTS
        else:
            R["percentiles_disagree"] = "needs both percentiles"

    lw, lw_why = long_window_of(metric_id, fam)
    need = "no observation a full period before the latest"

    if fam == "price":
        for tag, m in (("return_1m", 1), ("return_3m", 3), ("return_12m", 12)):
            put(tag, _change(level, back(m), "pct", 1), need)
        ye = _at_or_before(days, vals, dt.date(ld.year - 1, 12, 31).isoformat())
        put("return_ytd", _change(level, ye[1] if ye else None, "pct", 1),
            "no close at the end of last year")
        yr = [v for d, v in series if d >= (ld - dt.timedelta(days=365)).isoformat()]
        hi = max(yr)
        dd = round(100.0 * (level / hi - 1.0), 4) if hi else None
        put("drawdown_52w", dd, "no 52-week high")
        if dd is not None:
            out["flags"]["correction"] = dd <= CORRECTION_PCT
            out["flags"]["bear"] = dd <= BEAR_PCT
        rets = [math.log(vals[i] / vals[i - 1]) for i in range(1, len(vals))
                if vals[i] > 0 and vals[i - 1] > 0]
        if len(rets) >= 21:
            def rv(xs: list[float]) -> float:
                return round(statistics.stdev(xs) * math.sqrt(252) * 100.0, 4)
            cur = rv(rets[-20:])
            lo5 = len(rets) - min(len(rets), 1260)
            hist = [rv(rets[i - 20:i]) for i in range(max(20, lo5), len(rets) + 1)]
            put("realized_vol_20d", cur, "")
            F["realized_vol_20d_pctile"] = percentile_of(hist, cur)
            F["realized_vol_20d_pctile_n"] = len(hist)
            F["realized_vol_20d_pctile_ordinal"] = _ord(F["realized_vol_20d_pctile"])
        else:
            put("realized_vol_20d", None, f"{len(rets)} daily returns; 20 needed")
        r12 = []
        for i, d in enumerate(days):
            hit = _at_or_before(days, vals, _months_back(dt.date.fromisoformat(d), 12).isoformat())
            if hit and hit[0] < d and hit[1]:
                r12.append(100.0 * (vals[i] / hit[1] - 1.0))
        if F.get("return_12m") is not None and len(r12) >= 2:
            F["return_12m_pctile"] = percentile_of(r12, F["return_12m"])
            F["return_12m_pctile_n"] = len(r12)
            F["return_12m_pctile_window"] = "full history (6c)"
            F["return_12m_pctile_ordinal"] = _ord(F["return_12m_pctile"])
        else:
            R["return_12m_pctile"] = "needs a 12-month return and a history of them"
        put("move_1m_pctile", mv.get("percentile"), mv.get("absent_reason") or "")
        F["move_1m_pctile_n"] = mv.get("n")
        F["move_1m_pctile_ordinal"] = _ord(mv.get("percentile"))
    elif fam in ("rate", "spread"):
        months = (1, 3, 12) if fam == "rate" else (1, 3)
        for m in months:
            put(f"change_{m}m_bp", _change(level, back(m), "bp", bp_scale), need)
        percentiles(lw, lw_why)
        if fam == "spread":
            th, basis = widening_threshold(metric_id)
            ch = F.get("change_3m_bp")
            if th is None:
                R["widening"] = "no widening threshold for this series in config/metric_lenses.yaml"
            elif ch is None:
                R["widening"] = need
            else:
                out["flags"]["widening"] = ch >= th
                F["widening_threshold_bp"] = th
                F["widening_threshold_basis"] = basis
    elif fam == "release":
        pct_like = str(e.get("units")) in PCT_LEVEL_UNITS or units in PCT_LEVEL_UNITS
        kind = "pp" if pct_like else "pct"
        put("yoy", _change(level, back(12), kind, 1), need)
        F["yoy_unit"] = "pp" if pct_like else "%"
        b3, b6 = back(3), back(6)
        if pct_like:
            put("change_3m", _change(level, b3, "pp", 1), need)
            F["change_3m_unit"] = "pp"
            # Batch 7 lens 21 (6e-releases): six months beside three, every release.
            put("change_6m", _change(level, b6, "pp", 1), need)
        else:
            ann = (round(100.0 * ((level / b3) ** 4 - 1.0), 4)
                   if b3 and b3 > 0 and level > 0 else None)
            put("annualized_3m", ann, need)
            ann6 = (round(100.0 * ((level / b6) ** 2 - 1.0), 4)
                    if b6 and b6 > 0 and level > 0 else None)
            put("annualized_6m", ann6, need)
        if UNEMPLOYMENT.search(metric_id):
            percentiles(lw, lw_why)            # 6e: a level percentile added
        cons = (consensus or {}).get(level_day)
        sc = lens_config().get("surprise") or {}
        if cons is None and consensus is None:
            # Ruling (d)6, 16 Oct 2026: no free consensus source; nothing guessed.
            F["surprise_state"] = sc.get("state", "no consensus")
            R["surprise"] = sc.get("reason", "no consensus")
        elif cons is None:
            R["surprise"] = f"no consensus held for {level_day}"
        else:
            F["surprise"] = round(level - float(cons), 6)
            F["consensus"] = float(cons)
        rev = _revision_line(vint, level_day, pct_like, units)
        if rev:
            F["revision"] = rev
        else:
            R["revision"] = "the latest vintage changed no prior print"
    elif fam == "quantity":
        put("yoy_pct", _change(level, back(12), "pct", 1), need)
        put("change_3m_units", _change(level, back(3), "raw", 1), need)
        F["change_3m_units_unit"] = units
        c1 = _change(level, back(1), "raw", 1)
        c3 = F.get("change_3m_units")
        if c1 is None or c3 is None:
            R["direction"] = need
        else:
            F["direction"] = ("rising" if c1 > 0 and c3 > 0 else
                              "falling" if c1 < 0 and c3 < 0 else "turning")
            F["direction_rule"] = DIRECTION_RULE
    elif fam == "conditions":
        percentiles(lw, lw_why)
        lo5 = (as_of_day - dt.timedelta(days=1826)).isoformat()
        w5 = [v for d, v in series if d >= lo5]
        put("z_5y", z_of(w5, level), f"{len(w5)} observation(s) in five years")
        yr = [v for d, v in series if d >= (ld - dt.timedelta(days=365)).isoformat()]
        avg = statistics.fmean(yr) if yr else None
        put("spike_vs_1y_avg_pct", round(100.0 * (level / avg - 1.0), 4) if avg else None,
            "no 1-year average")
    elif fam == "ratio":
        percentiles(lw, lw_why)
        put("trend_3m", _change(level, back(3), "raw", 1), need)
        if F.get("trend_3m") is not None:
            F["trend_3m_direction"] = ("up" if F["trend_3m"] > 0 else
                                       "down" if F["trend_3m"] < 0 else "flat")
    # THE LENSES OTHER ORDERS BIND TO 6e (16 Oct 2026). A gap whose sign is the
    # finding (the core CPI less core PCE gap) flags the flip and dates it.
    if metric_id in (lens_config().get("sign_flip") or []):
        out["flags"]["sign_flipped"] = level < 0
        since = None
        for d, v in reversed(series):
            if (v < 0) != (level < 0):
                break
            since = d
        F["sign_since"] = since
    # The 10-year's anchors and fair value (Batch 4 section 4.1, SR-43): read
    # from altdata/rates_anchors.py, which owns the fits; printed as forms here.
    if metric_id in (lens_config().get("anchored_rates") or []):
        _anchor_forms(out, cutoff, store)
    out["forms_shown"] = [k for k in F if not k.endswith(("_n", "_window", "_ordinal",
                                                          "_basis", "_unit", "_rule"))]
    return out


def _anchor_forms(out: dict, cutoff: str,
                  store: Optional[observations.ObservationStore]) -> None:
    """The SR-43 inflation anchor and the 10-year's fair value as rate-family
    forms: the gap to the trailing ten-year CPI average, the inflation fit's and
    the twin-deficit fit's fitted yields and their gaps, the term premium. Each
    absent part carries its reason; the tag says what the fits are."""
    from . import rates_anchors  # noqa: PLC0415
    F, R = out["forms"], out["reasons"]
    own = store is None
    st = store or observations.ObservationStore()
    try:
        r = rates_anchors.read(st, cutoff)
    finally:
        if own:
            st.close()
    F["anchors_tag"] = r.get("tag")
    ia, fa, tp = r.get("inflation") or {}, r.get("fiscal") or {}, r.get("term_premium")
    if ia.get("state") == "ok":
        F["inflation_anchor_pct"] = round(ia["anchor_pct"], 4)
        F["inflation_anchor_gap_bp"] = round(ia["gap_bp"], 1)
        if ia.get("fitted_pct") is not None:
            F["fair_value_inflation_pct"] = round(ia["fitted_pct"], 4)
            F["fair_value_inflation_gap_bp"] = round(ia["residual_bp"], 1)
        else:
            R["fair_value_inflation_pct"] = ia.get("fit_note") or "no fit"
    else:
        R["inflation_anchor_gap_bp"] = ia.get("reason") or "absent"
        R["fair_value_inflation_pct"] = ia.get("reason") or "absent"
    if fa.get("state") == "ok" and fa.get("us_fitted_pct") is not None:
        F["fair_value_fiscal_pct"] = round(fa["us_fitted_pct"], 4)
        F["fair_value_fiscal_gap_bp"] = round(fa["gap_bp"], 1)
        F["fair_value_fiscal_n"] = fa.get("n")
    else:
        R["fair_value_fiscal_pct"] = fa.get("reason") or "the US is not in the fit"
    if tp:
        F["term_premium_pct"] = tp["pct"]
    else:
        R["term_premium_pct"] = "the ACM term premium is not stored"


_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def _revision_line(vint: list[dict], latest_period: str, pct_like: bool,
                   units: Optional[str]) -> Optional[str]:
    """"Aug revised 3.1% -> 3.3%" when the vintage that brought the latest print
    also changed a prior one. Reads only vintages knowable at the cutoff, and
    never rewrites a published figure: both numbers are stored vintages."""
    if not vint:
        return None
    first_avail = min((str(r["available_at"]) for r in vint
                       if str(r["observed_at"])[:10] == latest_period), default=None)
    if first_avail is None:
        return None
    by: dict[str, list[tuple[str, float]]] = {}
    for r in vint:
        if r.get("value_num") is not None:
            by.setdefault(str(r["observed_at"])[:10], []).append(
                (str(r["available_at"]), float(r["value_num"])))
    lines = []
    for period in sorted(by)[-4:-1]:
        vs = sorted(by[period])
        before = [v for a, v in vs if a < first_avail]
        now = [v for a, v in vs if a >= first_avail]
        if before and now and now[-1] != before[-1]:
            mon = _MONTHS[int(period[5:7]) - 1]
            fmt = (lambda x: f"{x:.1f}%") if pct_like else (lambda x: f"{x:,.1f}")
            lines.append(f"{mon} revised {fmt(before[-1])} -> {fmt(now[-1])}")
    return "; ".join(lines) or None


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
