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


# ---------------------------------------------------------------------------
# WHAT KIND OF NUMBER A FIGURE IS, AND WHY THE AUDIT HAS TO KNOW
# ---------------------------------------------------------------------------
#
# Existence was the only thing checked, and existence is not enough. The weekly's
# published paragraph called a flag "thirteen-day-old" because 13 was in the
# payload -- as the pin-row COUNT. Every figure in that sentence existed; the
# sentence was still false, and no amount of matching values catches it.
#
# So every payload figure carries a TYPE, taken from its field name, and a numeral
# in the prose whose adjacent unit word contradicts that type is rejected. "13
# rows" against a count of 13 passes; "13-day-old" against the same count does not.
#
# DETERMINISTIC, AND IT WITHHOLDS RATHER THAN REWRITING. A mismatch is reported
# with the figure, the unit word the prose used and the types the payload actually
# carries for that value -- it never edits the sentence, for the same reason the
# markdown check does not strip: a corrected paragraph is a sentence nobody wrote.
#
# A FIGURE MAY MATCH SEVERAL PAYLOAD VALUES, and the rule is that ONE compatible
# match is enough. 13 may be a count in one field and days in another, and a
# paragraph citing either is citing something true.
TYPE_COUNT = "count"
TYPE_DAYS = "days"
TYPE_PRICE = "price"
TYPE_PERCENTILE = "percentile"
TYPE_PERCENT = "percent"
TYPE_Z = "z"
TYPE_BP = "bp"
TYPE_DOLLARS = "dollars"
TYPE_RATIO = "ratio"
# The unconstrained type. A field whose name says nothing about its kind imposes
# nothing: better to check less than to reject a true sentence on a guess.
TYPE_ANY = "any"

# FIELD NAME -> TYPE, matched in order, first hit wins. Substrings rather than
# exact names, because a payload's field names are report fields and grow.
FIELD_TYPES: tuple[tuple[str, str], ...] = (
    ("percentile", TYPE_PERCENTILE),
    ("pctile", TYPE_PERCENTILE),
    ("z_score", TYPE_Z),
    ("threshold_z", TYPE_Z),
    ("magnitude", TYPE_Z),
    ("_bp$", TYPE_BP),
    ("_bps$", TYPE_BP),
    ("age_days", TYPE_DAYS),
    ("_days", TYPE_DAYS),
    ("^days_", TYPE_DAYS),
    ("^dte$", TYPE_DAYS),
    ("_pct$", TYPE_PERCENT),
    ("_pct_", TYPE_PERCENT),
    ("_percent", TYPE_PERCENT),
    ("^pct_", TYPE_PERCENT),
    # Dollar magnitudes. The same list precision.py rounds at bn/mm/k scale, and
    # it is imported from here so the two cannot disagree about what a dollar
    # figure is.
    ("dollar_gamma", TYPE_DOLLARS),
    ("net_gex", TYPE_DOLLARS),
    ("gex_per", TYPE_DOLLARS),
    ("notional", TYPE_DOLLARS),
    ("_pnl", TYPE_DOLLARS),
    ("expected_cost", TYPE_DOLLARS),
    ("commission", TYPE_DOLLARS),
    ("ratio", TYPE_RATIO),
    # Counts before prices: `pin_rows_today` and `n_5y` are counts, and `sessions`
    # anywhere in a name is a number of sessions.
    ("rows", TYPE_COUNT),
    ("count", TYPE_COUNT),
    ("sessions", TYPE_COUNT),
    # ANCHORED, because a two-character fragment matches anything. `n_` as a
    # substring classified `nothing_in_particular` as a count, which the gate
    # caught: a loose pattern here silently types every field it brushes past.
    ("^n_", TYPE_COUNT),
    ("_n$", TYPE_COUNT),
    ("emitted", TYPE_COUNT),
    ("resolved", TYPE_COUNT),
    ("total", TYPE_COUNT),
    ("figures_checked", TYPE_COUNT),
    # Prices and levels, in the instrument's own quote.
    ("spot", TYPE_PRICE),
    ("price", TYPE_PRICE),
    ("strike", TYPE_PRICE),
    ("wall", TYPE_PRICE),
    ("level", TYPE_PRICE),
    ("mark", TYPE_PRICE),
    ("cost", TYPE_PRICE),
    ("close", TYPE_PRICE),
    ("flip", TYPE_PRICE),
    ("max_pain", TYPE_PRICE),
    ("points", TYPE_PRICE),
)

# THE UNIT WORD A PARAGRAPH USED -> THE TYPE IT ASSERTS. Only words that genuinely
# name a unit; an adjective next to a number asserts nothing and is ignored, which
# is why this table is short rather than a vocabulary of everything a report says.
UNIT_TYPES: dict[str, str] = {
    "row": TYPE_COUNT, "rows": TYPE_COUNT,
    "session": TYPE_COUNT, "sessions": TYPE_COUNT,
    "decision": TYPE_COUNT, "decisions": TYPE_COUNT,
    "name": TYPE_COUNT, "names": TYPE_COUNT,
    "figure": TYPE_COUNT, "figures": TYPE_COUNT,
    "day": TYPE_DAYS, "days": TYPE_DAYS, "day-old": TYPE_DAYS,
    "percentile": TYPE_PERCENTILE, "pctile": TYPE_PERCENTILE,
    "percent": TYPE_PERCENT,
    "bp": TYPE_BP, "bps": TYPE_BP, "basis": TYPE_BP,
    "dollar": TYPE_DOLLARS, "dollars": TYPE_DOLLARS,
    "point": TYPE_PRICE, "points": TYPE_PRICE, "pts": TYPE_PRICE,
    "ratio": TYPE_RATIO,
}

# WHAT A UNIT WORD WILL ACCEPT BESIDES ITS OWN TYPE. Two equivalences, each with a
# reason rather than for convenience:
#
#   points  <- z   a z-score is spoken of in "points" often enough that rejecting
#                  it would be pedantry about a word rather than about a number.
#   percent <- percentile is NOT here, deliberately: "the 19th percent" and "the
#                  19th percentile" are different claims and confusing them is the
#                  error this whole table exists to catch.
COMPATIBLE: dict[str, tuple[str, ...]] = {
    TYPE_PRICE: (TYPE_Z,),
}


def type_of_key(key: str) -> str:
    """The type a field name declares. TYPE_ANY when it declares nothing.

    A pattern may be anchored: `^x` matches a prefix, `x$` a suffix, `^x$` the whole
    name, and anything else is a substring. The anchors exist because a
    two-character fragment as a substring types every field it brushes past -- `n_`
    called `nothing_in_particular` a count until the gate said so.
    """
    k = (key or "").lower()
    for frag, kind in FIELD_TYPES:
        if frag.startswith("^") and frag.endswith("$"):
            hit = k == frag[1:-1]
        elif frag.startswith("^"):
            hit = k.startswith(frag[1:])
        elif frag.endswith("$"):
            hit = k.endswith(frag[:-1])
        else:
            hit = frag in k
        if hit:
            return kind
    return TYPE_ANY


def types_of(value, key: str = "") -> list[tuple[float, str]]:
    """Every numeric leaf as (value, type). The typed form of payload_numbers()."""
    out: list[tuple[float, str]] = []
    if isinstance(value, bool):
        return out
    if isinstance(value, (int, float)):
        return [(float(value), type_of_key(key))]
    if isinstance(value, str):
        # A numeral inside a string is a payload figure (see payload_numbers), and
        # its type is the string's field -- a level quoted inside an invalidation
        # rule is still a level.
        return [(v, type_of_key(key)) for v in payload_numbers(value)]
    if isinstance(value, dict):
        for k, v in value.items():
            out.extend(types_of(v, k))
        return out
    if isinstance(value, (list, tuple, set)):
        for v in value:
            out.extend(types_of(v, key))
        return out
    return out


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
        # AN ORDINAL SUFFIX IS PART OF THE NUMBER'S PRESENTATION, and without it
        # nothing was audited: "19.8th" hit the trailing letter guard below, matched
        # NOTHING, and `audit("at its 19.9th percentile", {"percentile": 19.8})`
        # returned True. Every percentile either paragraph wrote in ordinal form --
        # and they write most of them that way -- was unchecked.
        (?P<ord>st|nd|rd|th)?
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
    # The type the prose ASSERTED by the word next to the numeral, or TYPE_ANY when
    # it asserted nothing. Checked against the type of the payload value it matched.
    unit_type: str = "any"
    # Filled by audit() when a value matched but its type contradicted the unit.
    type_conflict: str = ""

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
        # A TYPE CONFLICT IS NAMED AS ONE. "failed on 13" sends a reader looking
        # for a missing figure; the figure was there and the sentence called it the
        # wrong kind of thing, which is a different fix.
        def label(f) -> str:
            return f"{f.text} ({f.type_conflict})" if f.type_conflict else f.text

        bad = ", ".join(label(f) for f in self.unmatched[:6])
        more = "" if self.n_unmatched <= 6 else f" (+{self.n_unmatched - 6} more)"
        kinds = sum(1 for f in self.unmatched if f.type_conflict)
        tail = (f"; {kinds} of them a unit mismatch rather than a missing figure"
                if kinds else "")
        return (f"numeral audit failed on {self.n_unmatched} figure(s): "
                f"{bad}{more}{tail}")


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


def _unit_after(text: str, end: int, is_percent: bool) -> str:
    """The type asserted by the unit word next to a numeral, or TYPE_ANY.

    Reads the FIRST word after the figure, skipping one space or hyphen, so
    "13-day-old" and "13 days" both land on a days assertion. A percent sign on the
    numeral itself asserts percent without needing a word.

    Anything that is not in UNIT_TYPES asserts nothing: "760 put wall" says nothing
    about 760's type, and a table of every adjective a report might use would be a
    table nobody could keep correct.
    """
    if is_percent:
        return TYPE_PERCENT
    tail = text[end:end + 24].lower()
    m = re.match(r"[\s\-]?([a-z][a-z\-]*)", tail)
    if not m:
        return TYPE_ANY
    word = m.group(1)
    if word in UNIT_TYPES:
        return UNIT_TYPES[word]
    # "day-old" arrives as one hyphenated token; "basis points" needs the first
    # word only, which UNIT_TYPES already maps.
    head = word.split("-")[0]
    return UNIT_TYPES.get(head, TYPE_ANY)


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
                          position=m.start(),
                          unit_type=_unit_after(text or "", m.end(),
                                                bool(m.group("pct")))))
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
        # A NUMERAL INSIDE A PAYLOAD STRING IS A PAYLOAD FIGURE.
        #
        # The weekly's first run found this. The register's invalidation is free
        # text -- "a settled close below the put wall at 760" -- and both briefs
        # require the paragraph to STATE THE RULE AS WRITTEN. The model did, and the
        # audit rejected the 760 inside it, because only dates were being read out
        # of strings. The same happened to the FOMC claim, whose value is "2026 FOMC
        # meeting dates: Jan 27-28, Mar 17-18, ...": citing a meeting date by
        # quoting the claim failed on the claim's own contents.
        #
        # THIS WIDENS THE REFERENCE SET, and the widening is exactly bounded by what
        # the payload contains: a number is admitted only because the payload
        # carries that text, and the report prints that text. What it does NOT admit
        # is arithmetic over it -- the same run wrote "21 to 25 September" from a
        # window of 21 to 27, and 25 was correctly rejected.
        # Deduplicated: an ISO date yields its parts from _from_date_string and
        # again from extract(), and a reference set is a membership test -- the
        # duplicates cost nothing and make the list unreadable in a failure.
        seen = _from_date_string(payload)
        for f in extract(payload):
            if f.value not in seen:
                seen.append(f.value)
        return seen
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
    typed = types_of(payload)
    if extra_values:
        values.extend(float(v) for v in extra_values)
        # A DECLARED UNIT CONSTANT IS TYPELESS. The 1 in "per 1% decline" belongs to
        # the metric's definition rather than to any field, so it imposes nothing
        # and satisfies any unit word -- the alternative would be rejecting the very
        # sentence extra_values exists to permit.
        typed = typed + [(float(v), TYPE_ANY) for v in extra_values]
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
            continue
        # THE TYPE CHECK. A value matched; does the word the prose put next to it
        # agree with what that value IS? One compatible match is enough -- 13 may be
        # a count in one field and days in another, and citing either is true.
        if f.unit_type != TYPE_ANY:
            kinds = {k for v, k in typed
                     if f.low <= v < f.high or abs(v - f.value) <= 1e-9}
            allowed = {f.unit_type, TYPE_ANY} | set(
                COMPATIBLE.get(f.unit_type, ()))
            if kinds and not (kinds & allowed):
                f.type_conflict = (
                    f"written as {f.unit_type} but the payload carries this value "
                    f"as {sorted(kinds)}")
                unmatched.append(f)
                continue
        matched.append((f, hit))

    return AuditResult(passed=not unmatched, figures=figures,
                       unmatched=unmatched, matched=matched,
                       payload_values=len(values))
