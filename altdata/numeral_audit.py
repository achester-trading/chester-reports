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
import math
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Optional

# ---------------------------------------------------------------------------
# NAMES, NOT FIGURES (Weekly edition 1, item 1)
# ---------------------------------------------------------------------------
# Declared in config/audit_vocabulary.yaml, which says why each is there. A
# declared token is masked out of the prose before extraction, so its numeral is
# never a figure: "the 30-year yield" withheld the 27 September Weekly on "30".
VOCABULARY_PATH = Path(__file__).resolve().parent.parent / "config" / \
    "audit_vocabulary.yaml"
_VOCAB: Optional[dict] = None
MONTHS = ("january", "february", "march", "april", "may", "june", "july",
          "august", "september", "october", "november", "december",
          "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct",
          "nov", "dec")


def vocabulary(path: Optional[Path] = None) -> dict:
    """The declared name tokens. An unreadable file declares nothing -- the
    audit then checks every numeral, which fails safe (withholds) rather than
    open."""
    global _VOCAB
    if _VOCAB is not None and path is None:
        return _VOCAB
    try:
        import yaml  # noqa: PLC0415
        v = yaml.safe_load((path or VOCABULARY_PATH).read_text(
            encoding="utf-8")) or {}
    except Exception:                                          # noqa: BLE001
        v = {}
    if path is None:
        _VOCAB = v
    return v


def mask_names(text: str, tokens: Optional[Iterable[str]] = None) -> str:
    """The prose with every declared name token blanked, position for position."""
    toks = list(tokens if tokens is not None
                else vocabulary().get("name_tokens") or [])
    out = text or ""
    for t in sorted((str(x) for x in toks), key=len, reverse=True):
        out = re.sub(r"(?<![\w-])" + re.escape(t) + r"(?![\w-])",
                     lambda m: " " * len(m.group(0)), out, flags=re.I)
    return out


def ordinal_suffix(n: int) -> str:
    """The English ordinal suffix: 1st 2nd 3rd 4th ... 11th 12th 13th ... 21st."""
    if 11 <= n % 100 <= 13:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def ordinal_error(f: "Figure") -> str:
    """Why an ordinal figure is written wrongly, or "" when it is right.

    H-1 item 3. A percentile in prose is a WHOLE-NUMBER ordinal -- "the 96th
    percentile" -- while the payload keeps 96.1, and the interval match already
    lets "96th" find 96.1. Weekly paragraphs kept writing "96.1th", which is
    neither English nor a number anyone reads that way; the audit had no rule.
    """
    m = re.search(r"(?<=\d)(st|nd|rd|th)$", f.text, flags=re.I)
    if not m:
        return ""
    num = f.text[:m.start()].replace(",", "").lstrip("-$ ")
    if "." in num:
        n = int(round(abs(f.value)))
        return (f"an ordinal on a non-integer -- write {n}{ordinal_suffix(n)} "
                f"and let the payload keep the decimals")
    try:
        n = int(num)
    except ValueError:
        return ""
    want = ordinal_suffix(n)
    if m.group(1).lower() != want:
        return f"the suffix disagrees with its number -- {n}{want}"
    return ""


# ---------------------------------------------------------------------------
# PERCENTILE ORDINALS ARE PRECOMPUTED (1 Oct 2026)
# ---------------------------------------------------------------------------
# H-1 made a percentile in prose a whole-number ordinal and left the rounding to
# the model, which TRUNCATED: 51.7 -> "51st", 68.6 -> "68th". The audit reads
# "51st" as 50.5-51.5, so the paragraph was withheld -- the 1 Oct Monthly on one
# figure, its dry run on four. Rounding is arithmetic, so it is done here, once:
# every percentile field in a narrative payload gets a sibling `<field>_ordinal`
# rounded to the nearest whole number HALF UP (51.7 -> 52nd, 32.5 -> 33rd, 96.1 ->
# 96th), the brief tells the model to copy it verbatim, and a percentile ordinal
# in prose passes ONLY if it equals one of those stored strings.
ORDINAL_FIELD = "_ordinal"


def percentile_ordinal(value: float) -> str:
    """The whole-number ordinal for a percentile, half up: 32.5 -> '33rd'."""
    n = int(math.floor(float(value) + 0.5))
    return f"{n}{ordinal_suffix(n)}"


def with_ordinals(payload: Any, _depth: int = 0) -> Any:
    """A copy of `payload` with `<field>_ordinal` beside every percentile field.

    A field is a percentile by its NAME, the same rule the type audit uses
    (type_of_key). Idempotent: an existing `_ordinal` sibling is left alone.
    """
    if _depth > 16:
        return payload
    if isinstance(payload, dict):
        out = {k: with_ordinals(v, _depth + 1) for k, v in payload.items()}
        for k, v in payload.items():
            if (isinstance(v, (int, float)) and not isinstance(v, bool)
                    and not str(k).endswith(ORDINAL_FIELD)
                    and type_of_key(str(k)) == TYPE_PERCENTILE
                    and f"{k}{ORDINAL_FIELD}" not in payload):
                out[f"{k}{ORDINAL_FIELD}"] = percentile_ordinal(v)
        return out
    if isinstance(payload, list):
        return [with_ordinals(v, _depth + 1) for v in payload]
    return payload


def stored_ordinals(payload: Any, _depth: int = 0) -> set[str]:
    """Every percentile ordinal the payload carries or implies, lower-cased.

    The `_ordinal` strings themselves, and -- so a payload that never passed
    through with_ordinals() is judged by the same rule -- the ordinal of every
    percentile-typed value. Both are the same function of the same number.
    """
    out: set[str] = set()
    if _depth > 16:
        return out
    if isinstance(payload, dict):
        for k, v in payload.items():
            if str(k).endswith(ORDINAL_FIELD) and isinstance(v, str):
                out.add(v.strip().lower())
            elif (isinstance(v, (int, float)) and not isinstance(v, bool)
                  and type_of_key(str(k)) == TYPE_PERCENTILE):
                out.add(percentile_ordinal(v))
            else:
                out |= stored_ordinals(v, _depth + 1)
    elif isinstance(payload, (list, tuple)):
        for v in payload:
            out |= stored_ordinals(v, _depth + 1)
    return out


# ---------------------------------------------------------------------------
# SIGNED MOVES ARE PRECOMPUTED (1 Oct 2026), the ordinals' pattern again
# ---------------------------------------------------------------------------
# "Gold fell 6.75%" withheld the Monthly's fiscal section twice in one afternoon:
# the payload holds -6.75 and the prose wrote the magnitude. The sign rule stays;
# what changes is that the writer no longer composes the display form. Every
# change, move, delta or return in a narrative payload gets a sibling
# `<field>_signed` -- "−6.75%", "+0.36%", "+12 bp" -- in the field's own unit,
# and the brief says to copy it verbatim. When the prose writes the magnitude
# unsigned anyway, the audit still withholds, and names the field to copy.
SIGNED_FIELD = "_signed"
MINUS = "−"
_MOVE_KEY = re.compile(r"(^|_)(change|delta|move|return|ret|chg)(_|$|\d)")
_SKIP_SUFFIXES = ("_unit", SIGNED_FIELD, ORDINAL_FIELD, "_why", "_reason")


def _is_move_key(key: str) -> bool:
    k = str(key).lower()
    return (bool(_MOVE_KEY.search(k)) and not k.endswith(_SKIP_SUFFIXES)
            and type_of_key(k) != TYPE_PERCENTILE)


def _move_unit(key: str, siblings: dict) -> str:
    """The display unit: from the field's name, then a sibling unit field
    (`delta_unit`, `change_unit` -- the registry's delta semantics), then none."""
    k = str(key).lower()
    if k.endswith(("_bps", "_bp")):
        return " bp"
    if k.endswith(("_pct", "_percent")) or "_pct_" in k:
        return "%"
    stem = k.rsplit("_", 1)[0] if "_" in k else k
    for cand in (f"{k}_unit", f"{stem}_unit", "delta_unit", "change_unit", "unit"):
        u = str(siblings.get(cand) or "").lower()
        if u in ("bps", "bp"):
            return " bp"
        if u in ("percent", "pct", "%"):
            return "%"
        if u:
            return ""
    return ""


def signed_display(value: float, unit: str = "") -> str:
    """'+0.36%', '−6.75%', '+12 bp', '0 bp'. The value is already rounded to
    print precision; this only writes it with its sign and unit."""
    v = float(value)
    mag = f"{abs(v):,.4f}".rstrip("0").rstrip(".")
    if v == 0:
        return f"{mag}{unit}"
    return f"{'+' if v > 0 else MINUS}{mag}{unit}"


def with_signed(payload: Any, _depth: int = 0) -> Any:
    """A copy of `payload` with `<field>_signed` beside every move field.
    Idempotent: an existing `_signed` sibling is left alone."""
    if _depth > 16:
        return payload
    if isinstance(payload, dict):
        out = {k: with_signed(v, _depth + 1) for k, v in payload.items()}
        for k, v in payload.items():
            if (isinstance(v, (int, float)) and not isinstance(v, bool)
                    and _is_move_key(str(k))
                    and f"{k}{SIGNED_FIELD}" not in payload):
                out[f"{k}{SIGNED_FIELD}"] = signed_display(v, _move_unit(k, payload))
        return out
    if isinstance(payload, list):
        return [with_signed(v, _depth + 1) for v in payload]
    return payload


def signed_fields(payload: Any, _depth: int = 0) -> list[tuple[float, str, str]]:
    """(value, field, signed display) for every NEGATIVE move the payload carries
    -- the only case where an unsigned figure can be the right magnitude with the
    wrong sign."""
    out: list[tuple[float, str, str]] = []
    if _depth > 16:
        return out
    if isinstance(payload, dict):
        for k, v in payload.items():
            if (isinstance(v, (int, float)) and not isinstance(v, bool)
                    and v < 0 and _is_move_key(str(k))):
                out.append((float(v), f"{k}{SIGNED_FIELD}",
                            str(payload.get(f"{k}{SIGNED_FIELD}")
                                or signed_display(v, _move_unit(k, payload)))))
            else:
                out.extend(signed_fields(v, _depth + 1))
    elif isinstance(payload, (list, tuple)):
        for v in payload:
            out.extend(signed_fields(v, _depth + 1))
    return out


# ---------------------------------------------------------------------------
# SCALED FIGURES ARE PRECOMPUTED (1 Oct 2026), the third time the same pattern
# ---------------------------------------------------------------------------
# The writer kept rescaling large figures itself -- "373 billion", "162 thousand",
# "1.45 trillion" -- from series stored in millions, thousands or dollars, and
# the audit withheld the section each time. The display form is now computed by
# the caller that knows the series' unit (`<field>_display`: "$7.51bn",
# "$1.2tn", "159.33 million"), the brief says to copy it verbatim, and an
# unmatched scaled figure is withheld with the field named.
DISPLAY_FIELD = "_display"
# Registry `units` -> (multiplier to the base unit, is it dollars).
SCALE_UNITS = {"usd": (1.0, True), "M": (1e6, True), "B": (1e9, True),
               "K": (1e3, False), "count": (1.0, False)}


def scaled_display(value: float, units: str) -> Optional[str]:
    """'$7.51bn', '−$68.5bn', '$1.2tn', '159.33 million'; None when the value is
    small enough to print as it stands, or the units have no scale."""
    spec = SCALE_UNITS.get(str(units))
    if not spec:
        return None
    mult, dollars = spec
    x = float(value) * mult
    sign = MINUS if x < 0 else ""
    a = abs(x)
    if dollars:
        for word, m in (("tn", 1e12), ("bn", 1e9), ("mm", 1e6)):
            if a >= m:
                mag = f"{a / m:,.2f}".rstrip("0").rstrip(".")
                return f"{sign}${mag}{word}"
        return None
    for word, m in (("billion", 1e9), ("million", 1e6), ("thousand", 1e3)):
        if a >= m:
            mag = f"{a / m:,.2f}".rstrip("0").rstrip(".")
            return f"{sign}{mag} {word}"
    return None


def display_fields(payload: Any, _depth: int = 0) -> list[tuple[float, str, str]]:
    """(value, field, display) for every `_display` string the payload carries."""
    out: list[tuple[float, str, str]] = []
    if _depth > 16:
        return out
    if isinstance(payload, dict):
        for k, v in payload.items():
            if str(k).endswith(DISPLAY_FIELD) and isinstance(v, str):
                nums = payload_numbers(v)
                if nums:
                    out.append((nums[0], str(k), v))
            else:
                out.extend(display_fields(v, _depth + 1))
    elif isinstance(payload, (list, tuple)):
        for v in payload:
            out.extend(display_fields(v, _depth + 1))
    return out


def _is_percentile_ordinal(f: "Figure", text: str) -> bool:
    """An ordinal the prose uses AS a percentile: typed so, or with the word
    beside it ("its percentile, the 51st"). Other ordinals -- "the 2nd session"
    -- are counts and keep the plain match."""
    if not re.search(r"\d(st|nd|rd|th)$", f.text.strip(), flags=re.I):
        return False
    if f.unit_type == TYPE_PERCENTILE:
        return True
    span = text[max(0, f.position - 40):f.position + len(f.text) + 40]
    return bool(re.search(r"percentile", span, flags=re.I))


def payload_days(payload: Any, _depth: int = 0) -> set[int]:
    """Every day-of-month in the payload's date and datetime fields."""
    out: set[int] = set()
    if _depth > 12 or isinstance(payload, bool):
        return out
    if isinstance(payload, str):
        for m in _ISO.finditer(payload):
            out.add(int(m.group(3)))
    elif isinstance(payload, dict):
        for k, v in payload.items():
            out |= payload_days(k, _depth + 1) | payload_days(v, _depth + 1)
    elif isinstance(payload, (list, tuple, set)):
        for v in payload:
            out |= payload_days(v, _depth + 1)
    elif isinstance(payload, (dt.date, dt.datetime)):
        out.add(payload.day)
    return out


def _is_day_name(f: "Figure", text: str, days: set[int]) -> bool:
    """A day-of-month in DATE FORM whose day the payload's dates carry."""
    if f.unit_type != "any" or f.is_percent or f.value != int(f.value):
        return False
    d = int(f.value)
    if not 1 <= d <= 31 or d not in days:
        return False
    if re.search(r"\d(st|nd|rd|th)$", f.text, flags=re.I):
        return True
    after = text[f.position + len(f.text):f.position + len(f.text) + 12].lower()
    before = text[max(0, f.position - 12):f.position].lower()
    mon = "|".join(MONTHS)
    return bool(re.match(rf"\s+(?:of\s+)?(?:{mon})\b", after)
                or re.search(rf"\b(?:{mon})\.?\s+$", before))

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
    # A DISPLAY FORM CARRIES ITS OWN UNIT ("$7.51tn", "159.33 million"), so the
    # field imposes none -- "latest_level_display" is not a price because its
    # name contains "level". First, because first hit wins.
    ("_display$", TYPE_ANY),
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
        (?P<sign>-|−|minus\s)?  # a written minus counts; U+2212 is one too
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
    # Filled by audit() when the figure is an ORDINAL written wrongly (H-1 item 3):
    # a suffix on a non-integer ("96.1th") or one that disagrees with its number
    # ("21th", "12nd"). A form error, independent of whether the value matched.
    ordinal_error: str = ""
    # Filled by audit() when the figure is printed beside a named level (put
    # wall, flip, max pain, ...) and the payload holds that level at a different
    # value for that symbol (G-1). The figure exists -- under another name.
    label_conflict: str = ""
    # Filled when an UNSIGNED figure is the magnitude of a negative move the
    # payload carries: names the `_signed` field the writer should have copied.
    sign_error: str = ""
    # Filled when a large figure matches nothing but is near a `_display` form
    # the payload carries: names the field the writer should have copied.
    scale_error: str = ""

    def __str__(self) -> str:                      # pragma: no cover - display
        return f"{self.text!r} (={self.value:g}, accepts [{self.low:g}, {self.high:g}))"


@dataclass
class AuditResult:
    passed: bool
    figures: list[Figure] = field(default_factory=list)
    unmatched: list[Figure] = field(default_factory=list)
    matched: list[tuple[Figure, float]] = field(default_factory=list)
    payload_values: int = 0
    # Numerals read as NAMES: day-of-month tokens the payload's dates carry.
    # (Declared name tokens never become figures at all.)
    names: list[Figure] = field(default_factory=list)

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
            why = (f.type_conflict or f.ordinal_error or f.sign_error
                   or f.scale_error or f.label_conflict)
            return f"{f.text} ({why})" if why else f.text

        bad = ", ".join(label(f) for f in self.unmatched[:6])
        more = "" if self.n_unmatched <= 6 else f" (+{self.n_unmatched - 6} more)"
        kinds = sum(1 for f in self.unmatched if f.type_conflict)
        tail = (f"; {kinds} of them a unit mismatch rather than a missing figure"
                if kinds else "")
        labels = sum(1 for f in self.unmatched if f.label_conflict)
        if labels:
            tail += (f"; {labels} of them a level printed under the wrong name "
                     f"rather than a missing figure")
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


# (?!\d), not \b: a datetime "2026-09-27T00:36" has a word character after the
# day, and \b there silently dropped the date parts of every timestamp -- the
# morning test of 28 September was withheld on "27th" for exactly that.
_ISO = re.compile(r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)")


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


# ---------------------------------------------------------------------------
# THE LABEL AUDIT (G-1). A NUMBER BESIDE A NAMED LEVEL MUST BE THAT LEVEL.
# ---------------------------------------------------------------------------
# The 30 Sep close said "the put wall at 760 sitting N points ... away". The
# payload's SPY put wall was 745.00; 760.00 was SPY's max pain and the position's
# invalidation level. The numeral audit passed it, because 760 exists in the
# payload -- under two other names. A value that is TRUE UNDER ANOTHER NAME is a
# false sentence, and it is the failure the plain match cannot see.
#
# So when a numeral is printed beside a named level, it must equal a value the
# payload stores UNDER THAT NAME, for the symbol the sentence is about, within
# print precision. A number shared by two names passes only under a name that
# holds it. (label pattern, the field names that hold it, the name printed.)
LEVEL_LABELS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    (r"\bpeak(?:\s+absolute)?\s+(?:gamma|gex)(?:\s+strike)?\b",
     ("peak_abs_gex_strike", "peak_gex_strike"), "peak gamma"),
    (r"\bput[\s-]wall\b", ("put_wall",), "put wall"),
    (r"\bcall[\s-]wall\b", ("call_wall",), "call wall"),
    (r"\b(?:gamma[\s-])?flip(?:[\s-](?:line|level|point))?\b",
     ("gamma_flip",), "gamma flip"),
    (r"\bmax(?:imum)?[\s-]pain\b", ("max_pain",), "max pain"),
    (r"\binvalidation(?:[\s-]level)?\b", ("invalidation_level",), "invalidation"),
    # THE TAPE'S LEVEL TYPES (reporting-stack T1, altdata/levels.py). A level
    # printed under one of these names must be that instrument's listed level.
    (r"\b(?:prior|previous|yesterday's)\s+close\b", ("prior_close",), "prior close"),
    (r"\b(?:session|day's|intraday)\s+high\b", ("session_high",), "session high"),
    (r"\b(?:session|day's|intraday)\s+low\b", ("session_low",), "session low"),
    (r"\bVWAP\b", ("vwap",), "VWAP"),
    (r"\bweek(?:'s|ly)?\s+high\b", ("week_high",), "week high"),
    (r"\bweek(?:'s|ly)?\s+low\b", ("week_low",), "week low"),
    (r"\b20-day(?:\s+(?:moving\s+)?average)?\b", ("ma_20d",), "20-day average"),
    (r"\b50-day(?:\s+(?:moving\s+)?average)?\b", ("ma_50d",), "50-day average"),
    (r"\b200-day(?:\s+(?:moving\s+)?average)?\b", ("ma_200d",), "200-day average"),
    (r"\b52-week\s+high\b", ("high_52w",), "52-week high"),
    (r"\b52-week\s+low\b", ("low_52w",), "52-week low"),
    (r"\b40-week(?:\s+(?:moving\s+)?average)?\b", ("ma_40w",), "40-week average"),
    (r"\b10-month(?:\s+(?:moving\s+)?average)?\b", ("ma_10m",), "10-month average"),
    (r"\b20-month(?:\s+(?:moving\s+)?average)?\b", ("ma_20m",), "20-month average"),
    (r"\b(?:average|avg\.?)\s+cost\b|\bcost\s+basis\b", ("avg_cost",),
     "average cost"),
    # A bare "strike" is any strike-valued field: the walls, max pain and the
    # peak-gamma strike are all strikes, and "the 761 strike" is true of any.
    (r"\bstrike\b", ("peak_abs_gex_strike", "peak_gex_strike", "put_wall",
                     "call_wall", "max_pain", "strike"), "strike"),
)
_LABEL_RES = [(re.compile(p, re.I), f, n) for p, f, n in LEVEL_LABELS]
# A figure followed by one of these is a CHANGE, not a level: "jumped 11.00 points
# to 761.00" names the wall's move and then the wall.
_CHANGE_AFTER = re.compile(r"\s*(?:points?|pts|bps?|basis|%|per\s?cent|percent)\b",
                           re.I)
_CLAUSE_END = re.compile(r"[.;:,()—–]|\s-\s")
_BIND_WINDOW = 60          # characters after a label within which its level sits
_SYMBOL_KEYS = ("symbol", "instrument", "underlying", "ticker")


def _root(sym: Any) -> Optional[str]:
    s = str(sym or "").strip()
    return s.split("@")[0].split(".")[0].upper() if s else None


def _symbol_rows(payload: Any, _out: Optional[list] = None) -> list[dict]:
    """Every dict in the payload, with the symbol it is about (or None)."""
    out = [] if _out is None else _out
    if isinstance(payload, dict):
        out.append(payload)
        for v in payload.values():
            _symbol_rows(v, out)
    elif isinstance(payload, (list, tuple)):
        for v in payload:
            _symbol_rows(v, out)
    return out


def _row_symbol(d: dict) -> Optional[str]:
    for k in _SYMBOL_KEYS:
        if d.get(k):
            return _root(d[k])
    return None


def _label_values(rows: list[dict], fields: tuple[str, ...],
                  symbol: Optional[str]) -> list[tuple[float, str]]:
    out = []
    for d in rows:
        if symbol and _row_symbol(d) != symbol:
            continue
        for k, v in d.items():
            name = str(k)
            if (name in fields or ("strike" in fields and name.endswith("_strike"))) \
                    and isinstance(v, (int, float)) and not isinstance(v, bool):
                out.append((float(v), name))
    return out


def label_bindings(text: str, figures: list["Figure"]) -> list[tuple["Figure", str, tuple]]:
    """(figure, printed name, field names) for every figure printed beside a level."""
    out = []
    taken: set[int] = set()
    spans = []
    for rx, fields, name in _LABEL_RES:
        for m in rx.finditer(text):
            if any(m.start() < e and s < m.end() for s, e, *_ in spans):
                continue          # inside a longer label already found
            spans.append((m.start(), m.end(), fields, name))
    spans.sort()
    for i, (s, e, fields, name) in enumerate(spans):
        before = [f for f in figures
                  if 0 <= s - (f.position + len(f.text)) <= 2
                  and text[f.position + len(f.text):s].strip(" -") == ""]
        if before:
            f = before[-1]
            out.append((f, name, fields))
            taken.add(id(f))
            continue
        nxt = spans[i + 1][0] if i + 1 < len(spans) else len(text)
        for f in figures:
            if f.position < e or f.position - e > _BIND_WINDOW or f.position >= nxt:
                continue
            if _CLAUSE_END.search(text[e:f.position]):
                break
            if f.is_percent or _CHANGE_AFTER.match(text, f.position + len(f.text)):
                continue
            # "dropped FROM 780 to 775": the figure after `from` is the level's
            # previous value, held to the level's prior name (prior_call_wall);
            # the scan goes on, and the figure after `to` is the level itself.
            if re.search(r"\bfrom\s*$", text[max(e, f.position - 8):f.position], re.I):
                out.append((f, f"previous {name}",
                            tuple(f"{p}{x}" for x in fields
                                  for p in ("prior_", "previous_"))))
                continue
            out.append((f, name, fields))
            break
    return out


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
    masked = mask_names(text)
    days = payload_days(payload)
    figures, names = [], []
    for f in extract(masked):
        (names if _is_day_name(f, masked, days) else figures).append(f)
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

    ordinals = stored_ordinals(payload)
    signed = signed_fields(payload)
    displays = display_fields(payload)
    for f in figures:
        # A WRONGLY WRITTEN ORDINAL FAILS WHATEVER IT MATCHES (H-1 item 3).
        f.ordinal_error = ordinal_error(f)
        if f.ordinal_error:
            unmatched.append(f)
            continue
        # A PERCENTILE ORDINAL IS COPIED, NEVER ROUNDED BY THE WRITER: it passes
        # only if it equals a stored `_ordinal` (half up), so a truncated "51st"
        # for 51.7 fails even though 51 is near it.
        if _is_percentile_ordinal(f, masked):
            norm = re.sub(r"[^0-9a-z]", "", f.text.lower())
            if norm not in ordinals:
                n = int(re.match(r"\d+", norm).group()) if re.match(r"\d+", norm) \
                    else 0
                near = sorted(ordinals, key=lambda o: abs(
                    int(re.match(r"\d+", o).group()) - n)
                    if re.match(r"\d+", o) else 999)[:1]
                f.ordinal_error = (
                    f"a percentile ordinal must be copied from the payload's "
                    f"`_ordinal` field (rounded half up) -- {norm} is not one"
                    + (f"; the nearest stored is {near[0]}" if near else ""))
                unmatched.append(f)
                continue
            matched.append((f, f.value))
            continue
        pool = list(values) + (pct_values if f.is_percent else [])
        hit = next((v for v in pool if f.low <= v < f.high), None)
        if hit is None:
            # An integer written with no decimals is also accepted as an exact
            # count of something in the payload -- a session tally of 2 is the
            # number 2, and the interval test already covers it, but a value of
            # exactly f.high (a boundary) would otherwise be missed.
            hit = next((v for v in pool if abs(v - f.value) <= 1e-9), None)
        if hit is None:
            # THE SIGN RULE, WITH THE FIX NAMED. An unsigned magnitude of a
            # negative move -- "fell 6.75%" for -6.75 -- is still withheld; the
            # reason says which `_signed` field holds the form to copy.
            if f.value > 0:
                neg = next(((v, fld, disp) for v, fld, disp in signed
                             if f.low <= -v < f.high), None)
                if neg:
                    f.sign_error = (f"the payload's value is negative -- copy "
                                    f"`{neg[1]}` verbatim: {neg[2]}")
            # A RESCALED LARGE FIGURE: name the display form nearest it.
            if not f.sign_error and abs(f.value) >= 1e3:
                near = sorted(((abs(abs(f.value) / abs(v) - 1), fld, disp)
                               for v, fld, disp in displays if v),
                              key=lambda t: t[0])[:1]
                if near and near[0][0] <= 1.0:
                    f.scale_error = (f"a scaled figure is copied, never "
                                     f"rescaled -- copy `{near[0][1]}` verbatim: "
                                     f"{near[0][2]}")
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

    # THE LABEL AUDIT (G-1): a matched figure beside a named level must be that
    # level, for the symbol the sentence is about. Only matched figures are
    # checked -- an unmatched one already fails -- and a level the payload does
    # not carry under any name is left to the plain match, so an edition whose
    # payload has no exposure rows is not withheld for a field it never had.
    rows = _symbol_rows(payload)
    symbols = {s for s in (_row_symbol(d) for d in rows) if s}
    # ALIASES. A row may declare the names prose calls it by ("10-year", "gold",
    # "WTI"), so a level printed after "the 10-year's week high" is held to the
    # 10-year's row and not to the last ticker the paragraph happened to name.
    alias_res = []
    for d in rows:
        sym_d = _row_symbol(d)
        for a in (d.get("aliases") or []) if sym_d else []:
            alias_res.append((re.compile(r"(?<![\w-])" + re.escape(str(a))
                                         + r"(?![\w-])", re.I), sym_d))
    ok_ids = {id(f) for f, _ in matched}
    # The UNMASKED text, same length: a level label like "20-day average" is a
    # declared name token and is blanked in `masked`, which would hide the label.
    for f, name, fields in label_bindings(text or "", figures):
        if id(f) not in ok_ids:
            continue
        sym, at = None, -1
        for m in re.finditer(r"\b[A-Z][A-Z0-9.]{0,6}\b", masked[:f.position]):
            if m.group(0) in symbols:
                sym, at = m.group(0), m.start()
        for rx, sym_d in alias_res:
            for m in rx.finditer((text or "")[:f.position]):
                if m.start() > at:
                    sym, at = sym_d, m.start()
        held = _label_values(rows, fields, sym)
        if not held:
            continue
        if any(f.low <= v < f.high or abs(v - f.value) <= 1e-9 for v, _ in held):
            continue
        others = sorted({k for d in rows
                         if (not sym or _row_symbol(d) == sym)
                         for k, v in d.items()
                         if isinstance(v, (int, float)) and not isinstance(v, bool)
                         and (f.low <= float(v) < f.high
                              or abs(float(v) - f.value) <= 1e-9)})
        vals = ", ".join(f"{v:g}" for v in sorted({v for v, _ in held}))
        f.label_conflict = (
            f"printed as the {name}{' of ' + sym if sym else ''}, which the payload "
            f"holds as {vals}"
            + (f"; {f.text.strip()} is {', '.join(others)}" if others else ""))
        matched = [(g, h) for g, h in matched if g is not f]
        unmatched.append(f)

    return AuditResult(passed=not unmatched, figures=figures,
                       unmatched=unmatched, matched=matched,
                       payload_values=len(values), names=names)
