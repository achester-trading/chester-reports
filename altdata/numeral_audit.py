"""
D3 — the numeral audit. Every number in generated prose must exist in the payload.

-----------------------------------------------------------------------------
WHY THIS EXISTS BEFORE ANY PROSE DOES
-----------------------------------------------------------------------------
Architecture 32.5 keeps the Daily Cascade data-only until something can FAIL a
block for containing a number that is not in its payload. A Daily that can invent
a number is worse than no Daily: the numbers are the reason it is read, and one
fabricated figure that goes unnoticed retroactively devalues every correct one. So
the order is deliberate -- the audit ships first, the prose ships behind it, and
the prose is withheld rather than corrected when they disagree.

This is not a hallucination detector and does not try to be. It answers one
narrow, decidable question: does every numeral in this text correspond to a value
the payload actually holds? A model can still write a true number in a false
sentence, and nothing here would catch it. What it catches is the failure mode
that matters most and is cheapest to check.

-----------------------------------------------------------------------------
FORMATTING TOLERANCE, WHICH IS THE WHOLE DIFFICULTY
-----------------------------------------------------------------------------
Prose rounds. The payload holds 762.4500122070312 and the paragraph says 762.45,
and those are the same number reported at different precision. A tolerance that
is too tight fails every correct paragraph; one that is too loose lets a
transposed digit through.

So the tolerance is derived from HOW THE NUMBER WAS WRITTEN rather than being a
fixed epsilon: a figure printed to two decimals is matched against the interval
that rounds to it, [762.445, 762.455). "10.5bn" claims one decimal at 1e9 scale
and matches [10.45e9, 10.55e9). "760" claims units and matches [759.5, 760.5).
This is exactly what "within formatting tolerance" has to mean, and it has the
property that a transposed digit -- 762.54 for 762.45 -- lands outside the
interval and fails, while a rounding is inside it and passes.

-----------------------------------------------------------------------------
WHAT IS NOT A FIGURE
-----------------------------------------------------------------------------
Three kinds of numeral in real prose are not claims about payload values, and
treating them as such would make the audit fail on every correct paragraph:

  IDENTIFIERS   0DTE, 2s10s, SPX500, a digit fused to letters. Excluded by
                requiring a word boundary that is not a letter, except for the
                magnitude suffixes k/m/mm/b/bn, which ARE part of the number.
  DATES         "9 September 2026". Allowed when the component appears in a date
                the payload carries, so the session date can be written out
                without every paragraph failing on its own headline.
  ORDINALS AND SMALL COUNTS  "a third day", "the first two hits". These are
                spelled as words in the template's own style rules, and the audit
                matches the NUMERAL form only -- which is what makes the words
                permissible. A digit written as a digit is a claim and is checked.

-----------------------------------------------------------------------------
    from altdata.numeral_audit import audit
    result = audit(paragraph, payload)
    if not result.passed:
        ...  # ship the data-only edition; result.unmatched says which figures
"""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Optional

# Magnitude suffixes, longest first so "mm" wins over "m" and "bn" over "b".
# A MAGNITUDE IS PART OF THE NUMBER, SPELLED OUT OR NOT, and the word forms were
# missing. Both halves of that mattered.
#
# The permitted form was being rejected. The system prompt tells the model it may
# write "ten and a half billion" when the same value is printed in the tables, and
# the close report's own subject -- dollar gamma per 1% -- is a ten-digit number
# that no readable paragraph prints in full. On Tuesday's payload the model wrote
# "4.59 billion dollars of index per one percent move", the extractor read the
# figure as 4.59 against a payload holding 4,592,...,..., and a correct sentence
# was discarded.
#
# AND THE WRONG-BY-A-BILLION SENTENCE WAS PASSING. With the word ignored, "770
# billion dollars of gamma" extracted as 770 and matched SPY's price of 770.66.
# That is the failure this audit exists to prevent, and it was invisible in exactly
# the sentences the report is written to carry: a scale error is the one arithmetic
# mistake a reader cannot catch from context.
#
# Longest first in the alternation below: `billion` has to match before `b`.
SUFFIXES = (("trillion", 1e12), ("billion", 1e9), ("million", 1e6),
            ("thousand", 1e3),
            ("bn", 1e9), ("mm", 1e6), ("tn", 1e12), ("k", 1e3),
            ("b", 1e9), ("m", 1e6))

# A candidate figure:
#   optional currency, digits with , separators, optional decimals,
#   optional magnitude suffix, optional percent.
# The trailing guard rejects a numeral fused to a word (0DTE, 2s10s) while
# allowing the suffixes above, which are part of the number rather than a word.
_FIGURE = re.compile(
    r"""(?<![\w.])            # not mid-token, not a decimal tail
        (?P<sign>-|minus\s)?  # a written minus counts
        \$?\s?
        (?P<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)
        # THE SPACE IS OPTIONAL AND THE WORD FORMS COME FIRST. "4.59bn" and
        # "4.59 billion" are the same claim. The trailing guard below is what makes
        # the single letters safe: in "to 750 both having moved", `b` matches and
        # then the guard fails on the 'o', so the figure falls back to no suffix.
        (?P<suffix>\s?(?:trillion|billion|million|thousand|bn|mm|tn|k|b|m))?
        (?P<pct>\s?%|\s?per\s?cent|\s?percent)?
        # TWO GUARDS, because one cannot do both jobs.
        #   (?!\.?\d)   rejects a figure that is really the head of a longer one
        #               -- "1.1" out of "1.1.1" is a version, not a claim.
        #   (?![A-Za-z_]) rejects a digit fused to a word: 0DTE, 2s10s.
        # A single `(?![\w.])` was tried and silently dropped the percent sign on
        # any figure ending a sentence -- "up 0.35%." backtracked to "0.35" and
        # lost the marker that makes it comparable to a stored fraction.
        (?!\.?\d)(?![A-Za-z_])
    """,
    re.X | re.I,
)


@dataclass
class Figure:
    """One numeral as written, with the interval it claims."""
    text: str
    value: float
    low: float
    high: float
    is_percent: bool
    position: int

    def __str__(self) -> str:                      # pragma: no cover - display
        return f"{self.text!r} (={self.value:g}, accepts [{self.low:g}, {self.high:g}))"


@dataclass
class AuditResult:
    passed: bool
    figures: list[Figure] = field(default_factory=list)
    unmatched: list[Figure] = field(default_factory=list)
    matched: list[tuple[Figure, float]] = field(default_factory=list)
    payload_values: int = 0

    @property
    def n_unmatched(self) -> int:
        return len(self.unmatched)

    def reason(self) -> str:
        """One line, suitable for the withheld-narrative note."""
        if self.passed:
            return (f"numeral audit passed: {len(self.figures)} figure(s) all "
                    f"found in the payload")
        bad = ", ".join(f.text for f in self.unmatched[:6])
        more = "" if self.n_unmatched <= 6 else f" (+{self.n_unmatched - 6} more)"
        return (f"numeral audit failed on {self.n_unmatched} figure(s): "
                f"{bad}{more}")


def _decimals(num_text: str) -> int:
    """Decimal places as WRITTEN, which is what sets the tolerance."""
    if "." not in num_text:
        return 0
    return len(num_text.split(".", 1)[1])


def _interval(value: float, num_text: str, scale: float) -> tuple[float, float]:
    """The interval of true values that would round to this written figure.

    Derived from the written precision rather than a fixed epsilon. A figure
    written to two decimals accepts a half-unit of the last place either side;
    one written to none accepts a half-unit of one. Scale is applied last so
    "10.5bn" accepts a half-unit at the 0.1bn place and not at 0.1.
    """
    try:
        d = Decimal(num_text.replace(",", ""))
    except InvalidOperation:                        # pragma: no cover
        return value, value
    half = float(Decimal(10) ** (-_decimals(num_text)) / 2)
    return (value - half * scale, value + half * scale)


def extract(text: str) -> list[Figure]:
    """Every numeral in the prose that constitutes a claim about a value."""
    out: list[Figure] = []
    for m in _FIGURE.finditer(text or ""):
        raw = m.group("num")
        try:
            base = float(raw.replace(",", ""))
        except ValueError:                          # pragma: no cover
            continue
        scale = 1.0
        suffix = (m.group("suffix") or "").strip().lower()
        if suffix:
            for s, mult in SUFFIXES:
                if suffix == s:
                    scale = mult
                    break
        value = base * scale
        if m.group("sign"):
            value = -value
        # The interval is symmetric about the value, so a negative needs no
        # special case: _interval works from the signed value directly.
        low, high = _interval(value, raw, scale)
        out.append(Figure(text=m.group(0).strip(), value=value,
                          low=min(low, high), high=max(low, high),
                          is_percent=bool(m.group("pct")),
                          position=m.start()))
    return out


def payload_numbers(payload: Any, _depth: int = 0) -> list[float]:
    """Every number reachable in the payload, plus what dates contribute.

    Recursive over dicts and lists because a payload is a tree and a figure may
    legitimately come from any leaf of it. Booleans are excluded: True is not the
    number 1 in any sentence a reader would write, and admitting it would let a
    stray "1" match any flag in the payload.
    """
    vals: list[float] = []
    if _depth > 12:                                 # pragma: no cover - guard
        return vals
    if isinstance(payload, bool):
        return vals
    if isinstance(payload, (int, float)):
        return [float(payload)]
    if isinstance(payload, str):
        return _from_date_string(payload)
    if isinstance(payload, dict):
        for v in payload.values():
            vals.extend(payload_numbers(v, _depth + 1))
        return vals
    if isinstance(payload, (list, tuple, set)):
        for v in payload:
            vals.extend(payload_numbers(v, _depth + 1))
        return vals
    if isinstance(payload, (dt.date, dt.datetime)):
        return [float(payload.year), float(payload.month), float(payload.day)]
    return vals


_ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")


def _from_date_string(s: str) -> list[float]:
    """Year, month and day of any ISO date in a string.

    So a paragraph may open "Wednesday, 9 September 2026" without failing on its
    own headline. Only DATES contribute: an arbitrary number inside an arbitrary
    string would turn every id and hash in the payload into a licence to print
    any digits at all.
    """
    out: list[float] = []
    for m in _ISO.finditer(s or ""):
        y, mo, d = (int(g) for g in m.groups())
        out.extend([float(y), float(mo), float(d)])
    return out


def _derived(values: Iterable[float]) -> list[float]:
    """Representations a writer may legitimately use for the same quantity.

    A fraction stored as 0.0037 is written "0.37%"; a ratio stored as 1.5 may be
    written "150%". Both are the same fact at a different scale, so the percent
    form of every value is admitted -- but ONLY for figures the prose marked as a
    percent, so a bare number cannot match a hundredth of something unrelated.
    """
    return [v * 100.0 for v in values]


def audit(text: str, payload: Any, *,
          extra_values: Optional[Iterable[float]] = None) -> AuditResult:
    """Does every numeral in `text` correspond to a value in `payload`?

    `extra_values` is for UNIT CONSTANTS -- numbers that belong to a metric's
    definition rather than being claims about the market. The canonical one is
    the 1 in "dealers must sell $10.5bn per 1% decline": the metric IS
    dollar_gamma_per_1pct, so that 1 is part of what the quantity means and no
    payload holds it as a value. Without a way to declare it, a correct paragraph
    would be withheld over a unit.

    The style rules answer this a second way -- the template's reference
    paragraph writes "one percent" in words, and the audit only checks numerals --
    so a caller has both routes. Declaring the constant is the better one,
    because it keeps the prose natural and the exemption visible in code rather
    than resting on the model remembering to spell a number out.

    Kept in the CALLER and not in this module: a general numeral audit has no
    business knowing what a gamma metric is denominated in, and a hard-coded
    allowance of "1" here would let any stray 1 in any paragraph pass forever.

    Returns pass/fail plus the figures that could not be matched. Never raises:
    a broken audit must not be able to take the report down with it, and an audit
    that cannot run is handled by the caller as a failure to publish prose rather
    than as an exception.
    """
    figures = extract(text)
    values = payload_numbers(payload)
    if extra_values:
        values.extend(float(v) for v in extra_values)
    pct_values = _derived(values)

    matched: list[tuple[Figure, float]] = []
    unmatched: list[Figure] = []

    for f in figures:
        pool = list(values) + (pct_values if f.is_percent else [])
        hit = next((v for v in pool if f.low <= v < f.high), None)
        if hit is None:
            # An integer written with no decimals is also accepted as an exact
            # count of something in the payload -- a session tally of 2 is the
            # number 2, and the interval test already covers it, but a value of
            # exactly f.high (a boundary) would otherwise be missed.
            hit = next((v for v in pool if abs(v - f.value) <= 1e-9), None)
        if hit is None:
            unmatched.append(f)
        else:
            matched.append((f, hit))

    return AuditResult(passed=not unmatched, figures=figures,
                       unmatched=unmatched, matched=matched,
                       payload_values=len(values))
