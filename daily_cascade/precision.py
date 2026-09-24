"""
Print precision: the model never sees a figure the report would not print.

    from daily_cascade import precision
    payload = precision.apply(payload)        # idempotent
    precision.violations(payload)             # [] when it conforms

-----------------------------------------------------------------------------
THE RULE, AND THE FAILURE IT REMOVES
-----------------------------------------------------------------------------

The numeral audit already forgives rounding: a paragraph printing 45.3 against a
payload holding 45.2951 passes, because the audit compares an interval. That is
necessary and it is not sufficient, because it leaves the model looking at
45.2951 -- and a model handed 45.2951 prints 45.2951. Three of the published
samples did exactly that, and the result reads as a measurement to four decimal
places of a percentile computed over 1,254 sessions. The number is true and the
precision is a fiction.

The report itself never prints it that way: the state block prints percentiles at
one decimal, prices at two, moves at two. So the payload the model sees is now
carried AT THE PRECISION THE REPORT PRINTS, which makes the false-precision
sentence unwritable rather than merely discouraged. A rule the prompt asks for is
a rule the model follows most of the time; a figure absent from the payload is a
figure the audit rejects every time.

It also closes a subtler mismatch. With the payload at full precision the prose
and the tables disagreed on sight -- the paragraph said 45.2951 and the table
beside it said 45.3 -- and a reader cannot tell whether that is rounding or two
different numbers.

-----------------------------------------------------------------------------
THE DECLARED PRECISIONS
-----------------------------------------------------------------------------

    percentile          1 dp    the state block's own format (pctf)
    anything _pct       2 dp    a move or a distance in percent
    dollar magnitudes   2 dp AT THE bn/mm/k SCALE, in dollars
    everything else     2 dp    prices, points, ratios, z-scores

DOLLAR MAGNITUDES KEEP THEIR UNITS AND LOSE THEIR TAIL. 4,590,394,967 becomes
4,590,000,000 -- still dollars, still comparable to any other dollar figure,
rounded to what "4.59 billion" means. It is deliberately NOT converted to 4.59
with a unit label: the audit extracts "4.59 billion" from prose as 4.59e9, so a
payload holding 4.59 would fail the very sentence this exists to permit.

Integers are unaffected: round(24796, 2) is 24796. Booleans are not numbers and
are left alone -- `spot_above_flip` is a fact, not a figure.

-----------------------------------------------------------------------------
WHY A KEY-NAME TABLE AND NOT THE REGISTRY
-----------------------------------------------------------------------------

The registry knows a metric's units, and for a metric id that would be the right
source. A narrative payload is not metric ids: it is `spot`, `call_wall`,
`distance_pct`, `net_gex` -- report fields assembled from several metrics and from
the register. So the precision is declared here against the field names, in one
table, and anything unmatched takes the 2 dp default rather than passing through
at full precision. A default that let an unknown field through would make this
module optional the first time somebody added one.
"""

from __future__ import annotations

from typing import Any

from altdata import numeral_audit

PERCENTILE_DP = 1
PERCENT_DP = 2
DEFAULT_DP = 2
SCALED_DP = 2

# Largest first: a figure of 4.59e9 is a billion figure, not a thousand one.
SCALES: tuple[tuple[str, float], ...] = (("bn", 1e9), ("mm", 1e6), ("k", 1e3))

# DOLLAR MAGNITUDES, declared by name. Each is a dollar amount large enough that
# the report prints it scaled, and the model is expected to write it as "4.59
# billion" or "$4.59bn" rather than as ten digits.
DOLLAR_MAGNITUDE_KEYS = frozenset({
    "dollar_gamma_per_1pct",
    "prior_dollar_gamma_per_1pct",
    "dollar_gamma_change",
    "net_gex",
    "gex_per_1pct",
    "notional",
    "unrealized_pnl",
    "realized_pnl",
    "expected_cost",
})

# Fields whose precision is fixed by what they are rather than by their name's
# shape. Kept short on purpose: a long list here is a report that has stopped
# having conventions.
EXPLICIT_DP: dict[str, int] = {
    "z_score": 2,
    "magnitude": 2,
    "threshold_z": 1,
}


def kind_of(key: str) -> str:
    """`percentile` | `percent` | `dollar` | `default`, from the field name.

    DERIVED FROM THE AUDIT'S TYPE TABLE, not from a second list of names. The audit
    needs a finer answer than rounding does -- it distinguishes a count from days
    from a price -- and rounding needs only the three cases that have their own
    precision. Two tables would drift, and the drift would be invisible: a field
    the audit called dollars and this called default would round to two decimals and
    then be checked as a dollar figure.
    """
    k = (key or "").lower()
    if k in DOLLAR_MAGNITUDE_KEYS:
        return "dollar"
    t = numeral_audit.type_of_key(k)
    if t == numeral_audit.TYPE_PERCENTILE:
        return "percentile"
    if t == numeral_audit.TYPE_PERCENT:
        return "percent"
    if t == numeral_audit.TYPE_DOLLARS:
        return "dollar"
    return "default"


def dp_for(key: str) -> int:
    k = (key or "").lower()
    if k in EXPLICIT_DP:
        return EXPLICIT_DP[k]
    kind = kind_of(key)
    if kind == "percentile":
        return PERCENTILE_DP
    if kind == "percent":
        return PERCENT_DP
    return DEFAULT_DP


def round_scaled(v: float, dp: int = SCALED_DP) -> float:
    """A dollar magnitude rounded to `dp` at its own bn/mm/k scale, in dollars.

    Below a thousand there is no scale to round at and the value takes the ordinary
    2 dp: a $412.50 commission is a number the report prints in full.
    """
    for _, mult in SCALES:
        if abs(v) >= mult:
            return round(round(v / mult, dp) * mult, dp)
    return round(v, DEFAULT_DP)


def round_value(key: str, v: float) -> float:
    if kind_of(key) == "dollar":
        return round_scaled(v)
    return round(v, dp_for(key))


def apply(value: Any, key: str = "") -> Any:
    """The payload with every numeric leaf at its declared precision.

    Idempotent, and that matters more than it looks: `narrative.generate()` calls
    it on whatever it is handed, so no caller can put a full-precision payload in
    front of the model by forgetting a step. A transform that had to run exactly
    once would be a rule enforced by remembering.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return round_value(key, value)
    if isinstance(value, dict):
        return {k: apply(v, k) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        # THE PARENT'S KEY TRAVELS INTO A LIST, because a list of percentiles is a
        # list of percentiles. Without it, `[45.2951, 12.3456]` under a key named
        # `percentiles` would take the default and keep a decimal it should not.
        return [apply(v, key) for v in value]
    return value


def violations(value: Any, key: str = "", path: str = "") -> list[dict]:
    """Every numeric leaf carried at more precision than its rule allows.

    Returns the path, the value and what it should have been, so a failure names
    the field rather than the count. Used by the gate; a build whose narrative
    payload has any of these is a build putting a figure in front of the model that
    the report would not print.
    """
    out: list[dict] = []
    if isinstance(value, bool) or isinstance(value, int):
        return out
    if isinstance(value, float):
        want = round_value(key, value)
        if want != value:
            out.append({"path": path or key, "value": value, "expected": want,
                        "kind": kind_of(key), "dp": dp_for(key)})
        return out
    if isinstance(value, dict):
        for k, v in value.items():
            out.extend(violations(v, k, f"{path}.{k}" if path else k))
        return out
    if isinstance(value, (list, tuple)):
        for i, v in enumerate(value):
            out.extend(violations(v, key, f"{path}[{i}]"))
        return out
    return out


def describe() -> str:
    """One line for a log or a gate header."""
    return (f"print precision: percentile {PERCENTILE_DP}dp, percent "
            f"{PERCENT_DP}dp, dollars {SCALED_DP}dp at bn/mm/k, default "
            f"{DEFAULT_DP}dp; {len(DOLLAR_MAGNITUDE_KEYS)} dollar fields declared")
