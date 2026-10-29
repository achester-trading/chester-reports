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


def ordinal(value: float) -> str:
    """THE ONE ORDINAL HELPER (W-1.3c item 7): a number as an English ordinal,
    rounded half up to the whole -- 1st 2nd 3rd 11th 12th 13th 21st 92nd 103rd.
    Every code-formatted percentile goes through it; dry run #6 printed "RS 92th
    percentile" from an f-string's hard-coded "th"."""
    n = int(math.floor(float(value) + 0.5))
    return f"{n}{ordinal_suffix(n)}"


def percentile_ordinal(value: float) -> str:
    """The whole-number ordinal for a percentile, half up: 32.5 -> '33rd'."""
    return ordinal(value)


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


# A percentile ordinal as a table cell prints it: the cell's opening ordinal,
# before its window in brackets or the word "percentile" -- never an ordinal in
# running text ("the 2nd session").
_PRINTED_ORDINAL = re.compile(
    r"(?:^|(?<=\s))\d{1,3}(?:st|nd|rd|th)(?=\s*(?:\(|percentile\b|$))", re.I)


def stored_ordinals(payload: Any, _depth: int = 0) -> set[str]:
    """Every percentile ordinal the payload carries or implies, lower-cased.

    The `_ordinal` strings themselves, and -- so a payload that never passed
    through with_ordinals() is judged by the same rule -- the ordinal of every
    percentile-typed value. Both are the same function of the same number.
    """
    out: set[str] = set()
    if _depth > 16:
        return out
    if isinstance(payload, str):
        # THE ORDINAL A TABLE PRINTS (T3.5 (c)): ORDINAL_RULE tells the writer to
        # copy an ordinal "from the table, or from its _ordinal field", and the
        # tables print "86th (5 years, n=59)" -- built by the same half-up rule
        # (monthly_macro.stack._ord). The audit now holds what the rule allows.
        out |= {m.group(0).lower() for m in _PRINTED_ORDINAL.finditer(payload)}
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
# weekly-fixes-7 item 12: THE SIGNED-ZERO RULE. A figure that rounds to zero
# carries no sign: "−$0bn", "-0", "+0.0 bp" print "0" or "unch". Dry run 7
# printed "−$0bn" for RRP and "−0" for short interest.
# ---------------------------------------------------------------------------
_SIGNED_ZERO = re.compile(
    r"(?<![\w.,])[+\-−–][$€£]?0(?:\.0+)?(?![\d.,]*[1-9])"
    r"(?:\s?(?:bn|tn|m|k|%|bp|pts?|points|pp))?(?![\w])")


def signed_zero_faults(text: str) -> list[str]:
    return [f"a signed zero {m.group(0).strip()!r}: print '0' or 'unch'"
            for m in _SIGNED_ZERO.finditer(str(text or ""))]


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
#
# EACH SERIES' OWN UNITS, NEVER AN ASSUMED SCALE (T3.3 item 1, the second box dry
# run of 10 Oct 2026). The Fed-path block printed initial jobless claims at
# "200.5 million": IC4WSA is published in plain Number (200,500 claims) and its
# SeriesSpec said "K", so the scaler multiplied by a thousand. The scaler already
# read the registry; the registry was wrong (claims, existing home sales) or the
# other way about (CMDEBT in millions, declared billions). FRED's own unit names
# are accepted beside the short codes, and a unit the table does not name has no
# display -- the figure prints as it stands rather than at a guessed scale.
#   N / Number      a plain count            200,500 -> "200.5 thousand"
#   K / Thousands   thousands (of persons)   159,040 -> "159.04 million"
#   M / Millions    millions of dollars    2,948,000 -> "$2.95tn"
#   B / Billions    billions of dollars       22,804 -> "$22.8tn"
SCALE_UNITS = {"usd": (1.0, True), "M": (1e6, True), "B": (1e9, True),
               "K": (1e3, False), "N": (1.0, False), "count": (1.0, False),
               "Number": (1.0, False), "Thousands": (1e3, False),
               "Millions": (1e6, True), "Billions": (1e9, True)}


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


# PLAIN COUNTS AND SMALL THOUSANDS PRINT AS THE INTEGER (T3.4a, the third box dry
# run). The bare-delta rule withheld "+29,000" (payrolls, a thousands-unit series)
# and "+42,984, −77,476" (CFTC contracts, plain counts) in three sections -- each
# a correct figure in its natural form. A plain count's change is the integer with
# separators, whatever its size; a thousands-unit change below ±1,000 thousand is
# the integer it stands for ("+29,000"); levels keep their scale ("159.04
# million"), and currency and scaled series are unchanged ("+$23.15bn").
COUNT_UNITS = ("N", "count", "Number", "contracts", "Contracts", "jobs",
               "persons", "Persons", "shares")
THOUSAND_UNITS = ("K", "Thousands")


def _signed_int(x: float) -> str:
    return (MINUS if x < 0 else "+") + f"{abs(x):,.0f}"


# THE INTEGER CARRIES ITS NOUN (T3.5 (a), Monthly dry run #4). The integer form
# "+29,000" was accepted by the audit only where the frame still carried the
# display under `change_display`; a frame that handed it on under another key (a
# parent's or a summary's figures_you_may_cite) left the integer bare, and the
# rule withheld it -- payrolls twice, CFTC once. The display now carries its
# noun ("+29,000 jobs", "+125,623 contracts"), the bare-delta rule accepts a
# figure followed by one of these nouns, and the two cannot disagree: the form
# the writer is told to copy is the form the gate passes. A series with no noun
# here keeps the plain integer, accepted as before.
DISPLAY_NOUNS = {
    "fred.nfp": "jobs", "fred.claims_4wk": "claims", "fred.lt_unemp": "people",
    "fred.job_openings": "openings", "fred.hires_total": "hires",
    "fred.layoffs": "layoffs", "fred.housing_starts": "starts",
    "fred.housing_starts_sf": "starts", "fred.housing_permits": "permits",
    "fred.existing_homes": "homes", "fred.new_homes": "homes",
    "cftc.": "contracts", "pm.volume": "contracts", "pm.open_interest": "contracts",
    "exposure.oi_": "contracts", "eia.": "barrels",
    # B84 (summary:narratives, the 28 Oct dry run): official gold in troy ounces,
    # stored as a plain count -- "+740,000" printed bare until it carried its noun.
    "safe.gold_reserves_oz": "ounces", "imf.ifs.gold_reserves_oz.": "ounces",
}
UNIT_NOUNS = {"shares": "shares", "contracts": "contracts", "Contracts": "contracts",
              "jobs": "jobs", "persons": "people", "Persons": "people"}
_DERIVED_PREFIXES = ("calc.naive_expectation.", "calc.surprise_vs_naive.")


def display_noun(key: Optional[str], units: str = "") -> Optional[str]:
    """The noun a count's or a small thousands change prints with: the series'
    own (DISPLAY_NOUNS, by key or key prefix; a derived naive-expectation or
    surprise series takes its source's), else the unit's (UNIT_NOUNS)."""
    k = str(key or "")
    for pre in _DERIVED_PREFIXES:
        if k.startswith(pre):
            k = "fred." + k[len(pre):]
    if k in DISPLAY_NOUNS:
        return DISPLAY_NOUNS[k]
    for pre, noun in DISPLAY_NOUNS.items():
        if pre.endswith((".", "_")) and k.startswith(pre):
            return noun
    return UNIT_NOUNS.get(str(units))


def change_display(value: float, units: str, key: Optional[str] = None) -> Optional[str]:
    """A CHANGE in its series' own form, SIGNED: '+$23.15bn' and '−7.2 million'
    from the scaler (T3.3 item 2); '+42,984' for a plain count and '+29,000' for a
    thousands-unit change below ±1,000 thousand (T3.4a) -- and, given the series'
    key, the integer with its noun: '+29,000 jobs', '+42,984 contracts' (T3.5).
    None where the level would have no display either."""
    u = str(units)
    noun = display_noun(key, u)
    tail = f" {noun}" if noun else ""
    if u in COUNT_UNITS:
        return _signed_int(float(value)) + tail
    if u in THOUSAND_UNITS and abs(float(value)) < 1000:
        return _signed_int(float(value) * 1000) + tail
    d = scaled_display(value, units)
    if d is None:
        return None
    return d if d.startswith(MINUS) or float(value) == 0 else "+" + d


def _noun_words() -> str:
    return "|".join(sorted({*DISPLAY_NOUNS.values(), *UNIT_NOUNS.values()},
                           key=len, reverse=True))


# NO BARE DELTA ABOVE 9,999 (T3.3 item 2). The Systemic Liquidity pillar printed
# "rose +23,154 to $2.95tn" -- bank reserves' change in raw millions, copied from
# the number beside the display form. A change that large means nothing without
# its scale, so a published paragraph may not carry one: a signed figure, or one
# after a change verb, of 10,000 or more with no currency sign, scale word,
# percent, basis points, points or a count's noun (T3.5: "jobs", "contracts")
# beside it is withheld, naming the display to copy instead.
_BARE_DELTA = re.compile(
    r"(?P<lead>(?:\b(?:rose|rising|fell|falling|added|adding|gained|lost|dropped|"
    r"declined|increased|decreased|climbed|slipped|shed|jumped|grew|shrank|"
    r"up|down|by)\s+)|[+−-])"
    r"(?P<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d{5,}(?:\.\d+)?)"
    r"(?!\s?(?:%|percent|per\s?cent|bps?\b|basis|pts\b|points?\b|"
    r"trillion|billion|million|thousand|tn\b|bn\b|mm\b|k\b|"
    r"(?:" + _noun_words() + r")\b))"
    # Not followed by more of a number -- a full stop or a clause's comma is not
    # one (T3.5: "+29,000." at a sentence's end, and "+29,000, the ...", passed
    # unseen).
    r"(?!\d|[.,]\d)", re.I)


_PLAIN_DISPLAY = re.compile(r"^[+−-]?\d{1,3}(?:,\d{3})+$|^[+−-]?\d+$")


def accepted_deltas(payload: Any, _depth: int = 0) -> set[float]:
    """The magnitudes of every plain-integer display form the payload carries
    (`change_display`, `change_signed`) -- a count's or a small thousands
    change's own printed form, which the audit accepts (T3.4a)."""
    out: set[float] = set()
    if _depth > 12:
        return out
    if isinstance(payload, dict):
        for k, v in payload.items():
            if (k in ("change_display", "change_signed") and isinstance(v, str)
                    and _PLAIN_DISPLAY.match(v.strip())):
                out.add(abs(float(v.strip().lstrip("+−-").replace(",", ""))))
            else:
                out |= accepted_deltas(v, _depth + 1)
    elif isinstance(payload, (list, tuple)):
        for v in payload:
            out |= accepted_deltas(v, _depth + 1)
    return out


def bare_deltas(text: Optional[str], accepted: Any = ()) -> list[str]:
    """Every change of 10,000 or more printed with no unit or scale beside it --
    except a figure the payload's own display form prints that way (`accepted`,
    from accepted_deltas): a plain count or a thousands-unit change."""
    out = []
    ok = {abs(float(x)) for x in accepted or ()}
    for m in _BARE_DELTA.finditer(text or ""):
        before = (text or "")[max(0, m.start("num") - 2):m.start("num")]
        if "$" in before:
            continue
        n = float(m.group("num").replace(",", ""))
        if n >= 10000 and n not in ok:
            out.append(m.group(0).strip())
    return out


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

# THE SERIES-KIND EQUIVALENCE (W-1.1a item 1, the Weekly dry run of 12 Oct). A
# value the payload types as a price -- because its field is named `level`,
# `priced` or `mark` -- may be a yield, a rate, a probability, an implied move, a
# volatility or a spread, and those are written as percents: "the 10-year at
# 4.05%", "19% of a 25 bp hike". Where the value's row declares its SERIES KIND
# (a `series_kind` field, or a registry `key` whose kind metrics_registry.yaml's
# `series_kinds` block declares), the unit word may be the one that kind is
# written in: percent for all six, basis points for a change in a yield, rate or
# spread, points for a change in a probability. A price stays strict: "SPY at
# 0.93%" against a price of 0.93 still fails, and the message names the kind
# it used.
KIND_UNITS: dict[str, tuple[str, ...]] = {
    "yield": (TYPE_PERCENT, TYPE_BP),
    "rate": (TYPE_PERCENT, TYPE_BP),
    "spread": (TYPE_PERCENT, TYPE_BP),
    "probability": (TYPE_PERCENT, TYPE_PRICE),
    "implied_move": (TYPE_PERCENT,),
    "volatility": (TYPE_PERCENT,),
}
_KIND_KEYS = ("key", "metric_id", "registry_key")
_REGISTRY_KINDS: Optional[dict] = None


def registry_kinds() -> dict:
    """{metric id: series kind} from metrics_registry.yaml's `series_kinds`."""
    global _REGISTRY_KINDS
    if _REGISTRY_KINDS is None:
        try:
            import yaml                                         # noqa: PLC0415
            path = Path(__file__).resolve().parent.parent / "metrics_registry.yaml"
            reg = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            _REGISTRY_KINDS = {str(k): str(v) for k, v in
                               (reg.get("series_kinds") or {}).items()}
        except Exception:                                       # noqa: BLE001
            _REGISTRY_KINDS = {}
    return _REGISTRY_KINDS


def series_kind_of(d: dict, inherited: Optional[str] = None) -> Optional[str]:
    """A row's declared series kind: its own `series_kind`, else its registry
    key's, else its parent's."""
    k = d.get("series_kind")
    if isinstance(k, str) and k:
        return k
    for f in _KIND_KEYS:
        v = d.get(f)
        if isinstance(v, str) and v in registry_kinds():
            return registry_kinds()[v]
    return inherited


def kinds_of(value, key: str = "", kind: Optional[str] = None
             ) -> list[tuple[float, str, Optional[str]]]:
    """Every numeric leaf as (value, type, series kind) -- types_of() with the
    series kind of the row each value sits in."""
    if isinstance(value, dict):
        here = series_kind_of(value, kind)
        out: list[tuple[float, str, Optional[str]]] = []
        for k, v in value.items():
            if k == "series_kind":
                continue
            out.extend(kinds_of(v, k, here))
        return out
    if isinstance(value, (list, tuple, set)):
        out = []
        for v in value:
            out.extend(kinds_of(v, key, kind))
        return out
    return [(v, t, kind) for v, t in types_of(value, key)]


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


# A TABLE CELL CARRIES ITS OWN UNIT. Every table's cells sit in lists under the
# key `rows`, and `rows` types as a count -- so "1,011 bp" in Plumbing's table was
# a count of 1,011, and a paragraph quoting "1,011 bp" was withheld as a unit
# mismatch (the first live T2.3 render: Plumbing, Mechanics and The read all
# withheld). A cell's figure now takes the unit written beside it: % a percent, bp
# a basis-point figure, pts or points a price, a dollar sign or a scale word (k,
# bn, tn, thousand...) carries its own and imposes none. A figure with no unit
# word stays a count, as before -- and an ISO date in a cell keeps the date reading.
#
# TWO UNITS THE CELLS PRINT THAT THIS READ AS COUNTS (T3.2 item 3, the first real
# Monthly dry run, 10 Oct 2026). The word "percent" -- the slow layers' 20-day
# change prints "−5.40 percent" -- is a percent, as "%" is. And a PAIR sharing
# one unit -- the prediction markets' "+35.5 / +38.0 pts", Kalshi then
# Polymarket -- is two figures in that unit: the first took none, so 35.5 was a
# count and "up 35.5 points" was withheld as a unit mismatch. Each figure now has
# the type it truly has; a figure with no unit word anywhere is still a count.
_ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}(?:[T ][\d:.+Z-]*)?")
_CELL_FIGURE = re.compile(
    r"""(?P<lead>\$?)[-+\u2212]?\$?\d[\d,]*(?:\.\d+)?
        (?P<scale>\s?(?:trillion|billion|million|thousand|tn|bn|mm|k)\b)?
        (?P<unit>\s?(?:%|percent\b|per\s?cent\b|bps?\b|pts\b|points?\b))?""",
    re.X | re.I)
# "a / b unit": the first of a pair takes the unit written after the second;
# "a / — unit" (one venue unpriced) the unit written after the dash.
_CELL_PAIR = re.compile(r"\s*/\s*$")
_CELL_PAIR_DASH = re.compile(
    r"\s*/\s*[—–-]\s*(?P<unit>%|percent\b|per\s?cent\b|bps?\b|pts\b|points?\b)",
    re.I)


def _unit_kind(unit: str) -> str:
    unit = (unit or "").strip().lower()
    if unit == "%" or unit.startswith("per"):
        return TYPE_PERCENT
    if unit.startswith("bp"):
        return TYPE_BP
    if unit in ("pts", "point", "points"):
        return TYPE_PRICE
    return TYPE_COUNT


def _cell_kind(m: "re.Match") -> str:
    unit = (m.group("unit") or "").strip().lower()
    if unit == "%" or unit.startswith("per"):
        return TYPE_PERCENT
    if unit.startswith("bp"):
        return TYPE_BP
    if unit in ("pts", "point", "points"):
        return TYPE_PRICE
    if m.group("lead") or "$" in m.group(0) or m.group("scale"):
        return TYPE_ANY
    return TYPE_COUNT


def cell_types(text: str) -> list[tuple[float, str]]:
    """The figures in one table cell, each typed by the unit written beside it
    -- or, for the first of an "a / b unit" pair, after its partner."""
    out: list[tuple[float, str]] = []
    for d in _ISO_DATE.findall(text):
        out += [(v, TYPE_COUNT) for v in payload_numbers(d)]
    rest = _ISO_DATE.sub(" ", text)
    ms = list(_CELL_FIGURE.finditer(rest))
    kinds = [_cell_kind(m) for m in ms]
    for i in range(len(ms) - 1, -1, -1):
        if kinds[i] != TYPE_COUNT or ms[i].group("unit"):
            continue
        if (i + 1 < len(ms) and ms[i + 1].group("unit")
                and _CELL_PAIR.match(rest[ms[i].end():ms[i + 1].start()])):
            kinds[i] = kinds[i + 1]
            continue
        dash = _CELL_PAIR_DASH.match(rest, ms[i].end())
        if dash:
            kinds[i] = _unit_kind(dash.group("unit"))
    for m, kind in zip(ms, kinds):
        out += [(v, kind) for v in payload_numbers(m.group(0).strip())]
    return out


def string_types(text: str, key: str = "") -> list[tuple[float, str]]:
    """The figures in one payload string: each typed by the unit written beside
    it (a cell's rule), else by the string's field."""
    base = type_of_key(key)
    out: list[tuple[float, str]] = []
    for d in _ISO_DATE.findall(text):
        out += [(v, base) for v in payload_numbers(d)]
    rest = _ISO_DATE.sub(" ", text)
    for m in _CELL_FIGURE.finditer(rest):
        kind = _cell_kind(m)
        if kind == TYPE_COUNT and not m.group("unit"):
            kind = base
        out += [(v, kind) for v in payload_numbers(m.group(0).strip())]
    return out


def types_of(value, key: str = "") -> list[tuple[float, str]]:
    """Every numeric leaf as (value, type). The typed form of payload_numbers()."""
    out: list[tuple[float, str]] = []
    if isinstance(value, bool):
        return out
    if isinstance(value, (int, float)):
        return [(float(value), type_of_key(key))]
    if isinstance(value, str) and (key or "").lower() == "rows":
        return cell_types(value)
    if isinstance(value, str):
        # A numeral inside a string is a payload figure (see payload_numbers), and
        # its type is the string's field -- a level quoted inside an invalidation
        # rule is still a level.
        # A UNIT WRITTEN BESIDE IT WINS (W-1.1a item 1). "0.93% priced" under
        # the key `priced` is a percent, and "19% of a 25 bp hike" a percent and
        # a basis-point figure: the field's name typed all three as prices and
        # the 12 Oct dry run withheld Mechanics and Ahead over it. A figure with
        # no unit beside it keeps its field's type, as before.
        return string_types(value, key)
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
        (?P<sign>-|−|\+|minus\s)?  # a written minus counts; U+2212 is one too
        # A SIGN BEFORE ANY OF FOUR CURRENCY SYMBOLS (W-1.3c item 1): "−€1bn" was
        # read as +1bn, its sign stranded in front of a symbol the pattern did
        # not know. A plus is read, and the figure stays positive.
        [$€£¥]?\s?
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
    # Filled when the figure sits in a sentence that names a series and is not
    # that series' own figure (W8-2): "5.52% is bound to XLK but belongs to QQQ".
    bind_conflict: str = ""
    # The series kind whose unit let a price-typed value be written as a
    # percent, bp or pts (W-1.1a item 1); empty when no equivalence was used.
    series_kind: str = ""

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
                   or f.scale_error or f.label_conflict or f.bind_conflict)
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
        binds = sum(1 for f in self.unmatched if f.bind_conflict)
        if binds:
            tail += (f"; {binds} of them bound to the wrong series' row rather than "
                     f"a missing figure")
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
        if m.group("sign") and m.group("sign") != "+":
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
_VP_NAMES = (("poc", r"(?:POC|point\s+of\s+control)", "point of control"),
             ("vah", r"(?:VAH|value[\s-]area\s+high)", "value-area high"),
             ("val", r"(?:VAL|value[\s-]area\s+low)", "value-area low"))
_VP_QUALIFIERS = (
    ("prior_session", r"(?:(?:prior|previous)\s+session's|yesterday's)",
     "prior session's"),
    ("prior_week", r"(?:prior|previous|last)\s+week's", "prior week's"),
    ("prior_month", r"(?:prior|previous|last)\s+month's", "prior month's"),
    ("session", r"(?:session's|today's)", "session's"),
    ("week", r"(?:this\s+)?week's", "week's"),
    ("month", r"(?:this\s+)?month's", "month's"))


def _vp_labels() -> list[tuple[str, tuple[str, ...], str]]:
    """The profile's label rows: each window's qualified names, then the bare."""
    out = [(rf"\b{q}\s+{n}\b", (f"vp_{w}_{f}",), f"{qn} {name}")
           for w, q, qn in _VP_QUALIFIERS for f, n, name in _VP_NAMES]
    out += [(rf"\b{n}\b", tuple(f"vp_{w}_{f}" for w, _, _ in _VP_QUALIFIERS), name)
            for f, n, name in _VP_NAMES]
    return out


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
    # THE VOLUME PROFILE (VP-1, altdata/volume_profile.py): a qualified name binds
    # to its window only; a bare one to that field in any window. Prior windows
    # first, so "the prior week's VAH" is never read as "the week's VAH".
    *_vp_labels(),
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


# ---------------------------------------------------------------------------
# THE SERIES BINDING (W8-2, weekly-fixes-8, 18 Oct 2026). A FIGURE IN A SENTENCE
# THAT NAMES A SERIES MUST BE THAT SERIES' OWN.
# ---------------------------------------------------------------------------
# The Weekly of 18 Oct wrote "Technology (XLK) falling 5.52%": 5.52 was QQQ's
# week, XLK fell 7.70. And "JPY futures positioning slipped 1.6 points of open
# interest": -1.6 was the leveraged funds' four-week-change z, not a share of
# open interest. Both figures exist in the payload, so the plain match passed
# them. The binding reads the section's data block for its series -- every row
# with a label (a table's first cell, or a dict's label, name, series, contract,
# symbol...) and the names it goes by (the label, a ticker in its brackets, the
# name before them, its symbol, its declared aliases) -- and binds each figure to
# the alias nearest it in its sentence. The figure must then be one that row
# holds, under a field whose kind agrees with the unit written beside it. A
# figure that belongs to another series' row fails, naming both; a figure the
# bound row lacks and no other row holds is left to the plain match (a spread
# between two series, say), and a sentence that names no series is untouched.
_ROW_LABEL_KEYS = ("label", "name", "series", "title", "contract", "symbol",
                   "ticker", "instrument", "underlying", "fund", "sector")
_BRACKET = re.compile(r"\(([^()]{1,24})\)")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'(])|;\s*")
_OF_OI = re.compile(r"\s*(?:percentage\s+)?(?:%|points?|pts|percent)?\s*of\s+"
                    r"(?:the\s+)?open\s+interest", re.I)
_Z_KEY = re.compile(r"(^|_)z($|_)|z_?score")


def _bound_type(key: str) -> str:
    """A field's kind for the binding: the audit's own, and a z where the name
    carries one (`change_z_4w`, `level_z`), which the plain audit leaves untyped."""
    t = type_of_key(key)
    if t == TYPE_ANY and _Z_KEY.search((key or "").lower()):
        return TYPE_Z
    return t


def _aliases_of(label: str) -> list[str]:
    """The names a row's label goes by: the label, each ticker in its brackets,
    and the name before them ("Technology (XLK)" -> itself, XLK, Technology)."""
    lab = re.sub(r"\s+", " ", str(label or "")).strip()
    if not lab or len(lab) < 2 or re.fullmatch(r"[\d\s.,:%+\-−/]+", lab):
        return []
    out = [lab]
    out += [m.strip() for m in _BRACKET.findall(lab) if len(m.strip()) >= 2]
    head = _BRACKET.sub("", lab).strip()
    if head and head != lab and len(head) >= 2:
        out.append(head)
    # "JPY futures" and "CFTC JPY": the row's own symbol is found by its key.
    return out


def _col_key(name: str) -> str:
    """A column head as a field name: "Four-week change z" -> four_week_change_z."""
    return re.sub(r"[^a-z0-9]+", "_", str(name or "").lower()).strip("_")


def _typed(v: Any, key: str) -> list[tuple[float, str, str]]:
    """(value, field, kind) for one scalar: a number by its field, a string's
    figures by the unit written beside them, else by its field."""
    if isinstance(v, bool) or v is None:
        return []
    if isinstance(v, (int, float)):
        return [(float(v), key, _bound_type(key))]
    if isinstance(v, str):
        base = _bound_type(key)
        return [(x, key, base if t in (TYPE_ANY, TYPE_COUNT) and base != TYPE_ANY else t)
                for x, t in string_types(v, key)]
    return []


def _dict_values(d: dict) -> list[tuple[float, str, str]]:
    """A labelled dict's own figures: its scalars, and one nested dict's."""
    out: list[tuple[float, str, str]] = []
    for k, v in d.items():
        k = str(k)
        if k in _ROW_LABEL_KEYS or k == "aliases":
            continue
        if isinstance(v, dict):
            for kk, vv in v.items():
                out += _typed(vv, f"{k}.{kk}")
        else:
            out += _typed(v, k)
    return out


def series_rows(payload: Any, _out: Optional[list] = None) -> list[dict]:
    """[{"aliases": [...], "name": short name, "values": [(value, field, kind)]}]
    for every labelled row in a data block: a dict with a label field, or a
    table's row (its first cell the label, each cell typed by its column)."""
    out = [] if _out is None else _out
    if isinstance(payload, dict):
        cols, trows = payload.get("columns"), payload.get("rows")
        if isinstance(cols, list) and isinstance(trows, list):
            keys = [_col_key(c) for c in cols]
            for r in trows:
                if not (isinstance(r, (list, tuple)) and r and isinstance(r[0], str)):
                    continue
                names = _aliases_of(r[0])
                vals = [t for i, c in enumerate(r[1:], 1)
                        for t in _typed(c, keys[i] if i < len(keys) else "cell")]
                if names and vals:
                    short = next((m.strip() for m in _BRACKET.findall(r[0])), None)
                    out.append({"aliases": names, "values": vals,
                                "name": short or names[-1]})
        names: list[str] = []
        for k in _ROW_LABEL_KEYS:
            v = payload.get(k)
            if isinstance(v, str):
                names += _aliases_of(v)
        sym = _row_symbol(payload)
        if sym:
            names.append(sym)
        names += [str(a) for a in (payload.get("aliases") or [])
                  if isinstance(a, str) and len(a) >= 2]
        vals = _dict_values(payload)
        if names and vals:
            short = next((m.strip() for n in names for m in _BRACKET.findall(n)), None)
            out.append({"aliases": list(dict.fromkeys(names)), "values": vals,
                        "name": sym or short or names[0]})
        for v in payload.values():
            if isinstance(v, (dict, list, tuple)):
                series_rows(v, out)
    elif isinstance(payload, (list, tuple)):
        for v in payload:
            if isinstance(v, (dict, list, tuple)):
                series_rows(v, out)
    return out


def _holds(values: list[tuple[float, str]], f: "Figure") -> list[str]:
    """(field, kind) of each of `values` that holds the figure, either sign, or
    its percent form for a percent figure."""
    out = []
    for v, k, t in values:
        for c in (v, -v) + ((v * 100.0, -v * 100.0) if f.is_percent else ()):
            if f.low <= c < f.high or abs(c - f.value) <= 1e-9:
                out.append((k, t))
                break
    return out


def _bindable(f: "Figure") -> bool:
    """A measured figure -- a percent, a decimal, or one with a unit word --
    rather than a count, a year or a day."""
    return bool(f.is_percent or "." in f.text or f.unit_type in
                (TYPE_BP, TYPE_PRICE, TYPE_PERCENT, TYPE_Z, TYPE_DOLLARS))


_CURRENCY_NAMES: Optional[dict] = None


def currency_names() -> dict:
    """{ISO code: the name the prose uses} from metrics_registry.yaml's
    `quote_conventions` (EUR/USD: base euro, quote dollar), the registry's one
    declaration of what the prose calls each leg of a pair."""
    global _CURRENCY_NAMES
    if _CURRENCY_NAMES is None:
        _CURRENCY_NAMES = {}
        try:
            import yaml                                         # noqa: PLC0415
            path = Path(__file__).resolve().parent.parent / "metrics_registry.yaml"
            reg = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            for q in (reg.get("quote_conventions") or {}).values():
                legs = str(q.get("pair") or "").split("/")
                if len(legs) == 2:
                    for code, name in zip(legs, (q.get("base"), q.get("quote"))):
                        if re.fullmatch(r"[A-Z]{3}", code) and isinstance(name, str):
                            _CURRENCY_NAMES.setdefault(code, name)
        except Exception:                                       # noqa: BLE001
            _CURRENCY_NAMES = {}
    return _CURRENCY_NAMES


# THE NAMES THE PROSE USES (A88, 28 Oct 2026). The Monthly's dry run withheld
# correct sections because the prose named a series by a short form its row's
# label does not carry: "nonfarm payrolls" for "Nonfarm payrolls, total", "the
# 10-year yield" for "10-year Treasury yield", "bank reserves" for "Bank
# reserves at the Fed", "the euro" for "USD/EUR exchange rate". Each label also
# goes by: its head (before a comma, a bracket or " at/of/for/in/on "), each of
# those without the issuer and noise words below, without its leading tenor or
# first word where two or more words remain, its leading tenor ("2-year"), and
# the registry's name for a currency in an ISO pair. A derived form binds only
# where it is unique to one row in the block; shared, it is no name at all.
_ALIAS_NOISE = re.compile(r"\b(?:the|treasury|total|rate|level)\b", re.I)
_ALIAS_HEAD = re.compile(r",\s|\s(?:at|of|for|in|on)\s")
_ALIAS_TENOR = re.compile(r"^(\d+-(?:year|month|week|day))\b\s*", re.I)
_ALIAS_PAIR = re.compile(r"\b([A-Z]{3})/([A-Z]{3})\b")


def _derived_aliases(label: str) -> list[str]:
    lab = re.sub(r"\s+", " ", str(label or "")).strip()
    bare = re.sub(r"\s*\([^()]*\)", "", lab).strip()
    forms: list[str] = []
    for base in (bare, _ALIAS_HEAD.split(bare, 1)[0].strip()):
        clean = re.sub(r"\s+", " ", _ALIAS_NOISE.sub(" ", base)).strip(" ,")
        for form in (base, clean):
            forms.append(form)
            rest = _ALIAS_TENOR.sub("", form)
            if rest != form:
                forms.append(rest)
            words = form.split(" ")
            if len(words) >= 3:
                forms.append(" ".join(words[1:]))
    t = _ALIAS_TENOR.match(bare)
    if t:
        forms.append(t.group(1))
    names = currency_names()
    for m in _ALIAS_PAIR.finditer(lab):
        forms += [names[c] for c in m.groups() if c in names]
    # An acronym that ends the label is also its words: "Chicago Fed NFCI" is
    # "the Chicago Fed's National Financial Conditions Index".
    last = bare.split(" ")[-1] if bare else ""
    if re.fullmatch(r"[A-Z]{3,6}", last) and len(bare.split(" ")) > 1:
        forms.append(_ACRONYM + last)
    return [f for f in dict.fromkeys(forms)
            if f != lab and len(f) >= 3 and re.search(r"[A-Za-z]", f)]


_ACRONYM = "acronym:"


def _alias_rx(a: str) -> "re.Pattern":
    """A name as a pattern: a ticker by its case, a phrase in any case, a
    phrase's first word in its possessive ("PRL's fees" for "PRL fees"), and an
    acronym as its capitalised words."""
    if a.startswith(_ACRONYM):
        return re.compile(r"(?<![\w-])" + r"\s+".join(
            ch + r"[a-z]+" for ch in a[len(_ACRONYM):]) + r"(?![\w-])")
    flags = 0 if re.fullmatch(r"[A-Z0-9.=^\-]{2,8}", a) else re.I
    first, sp, rest = a.partition(" ")
    body = (re.escape(first) + r"(?:['’]s)?\s" + re.escape(rest)
            if sp and re.fullmatch(r"[\w.&-]+", first) else re.escape(a))
    return re.compile(r"(?<![\w-])" + body + r"(?![\w-])", flags)


# THE CLAUSE (A88). A figure binds first to a name in brackets straight after it
# ("-3.27% (XLY/XLP)"), then to a name in its own clause -- the one before it
# first, the nearest of those, and a name inside a bracket that closes before the
# figure only when no other is there (the bracket qualifies the name before it:
# "Net liquidity (the Fed balance sheet less ...) ended at") -- then to one after
# it in the clause, and only then to the nearest name before it in the sentence.
# A name AFTER the figure in another clause never binds it. A clause ends at a
# comma (not one between digits), a semicolon, a colon, a dash or " - "; a
# bracket does not end one. A clause that says "respectively" pairs its lists by
# order, so its figures bind to nothing and are left to the plain match.
_BIND_CLAUSE = re.compile(r"[;:—–]|,(?!\d)|\s-\s")
_RESPECTIVELY = re.compile(r"\brespectively\b", re.I)


def _enclosed(text: str, start: int, end: int) -> bool:
    """Is position `start` inside a bracket that closes before `end`?"""
    depth = 0
    for ch in text[start:end]:
        depth += (ch == "(") - (ch == ")")
        if depth < 0:
            return True
    return False


def series_bindings(text: str, figures: list["Figure"], payload: Any
                    ) -> list[tuple["Figure", str]]:
    """(figure, why) for each figure bound to a series whose row does not hold
    it: "5.52% is bound to XLK but belongs to QQQ"."""
    rows = series_rows(payload)
    if not rows or not figures:
        return []
    by_alias: dict[str, list[dict]] = {}
    for r in rows:
        for a in r["aliases"]:
            by_alias.setdefault(a, []).append(r)
    derived: dict[str, list[dict]] = {}
    for r in rows:
        for lab in list(r["aliases"]):
            for a in _derived_aliases(lab):
                if a in by_alias:
                    # Another row's own name: the rows share it, as rows that
                    # carry one name already do ("SOFR less IORB" twice).
                    if all(x is not r for x in by_alias[a]):
                        by_alias[a].append(r)
                elif all(x is not r for x in derived.get(a, [])):
                    derived.setdefault(a, []).append(r)
    by_alias.update({a: rs for a, rs in derived.items() if len(rs) == 1})
    alias_rx = [(_alias_rx(a), a) for a in sorted(by_alias, key=len, reverse=True)]
    bounds = [0] + [m.end() for m in _SENTENCE_END.finditer(text)] + [len(text) + 1]
    out = []
    for f in figures:
        if not _bindable(f):
            continue
        lo = max(b for b in bounds if b <= f.position)
        hi = min(b for b in bounds if b > f.position)
        end = f.position + len(f.text)
        c_lo = max([lo] + [m.end() for m in _BIND_CLAUSE.finditer(text, lo, f.position)])
        c_hi = next((m.start() for m in _BIND_CLAUSE.finditer(text, end, hi)), hi)
        if _RESPECTIVELY.search(text, c_lo, c_hi):
            continue
        tag = re.match(r"\s*\(", text[end:hi])
        tag_hi = text.find(")", end, hi) if tag else -1
        hits, taken = [], []
        for rx, a in alias_rx:
            for m in rx.finditer(text, lo, hi):
                if any(m.start() < e and s < m.end() for s, e in taken):
                    continue       # inside a longer alias already found
                if m.start() <= f.position < m.end():
                    continue       # the figure is part of the name ("S&P 500")
                taken.append((m.start(), m.end()))
                before = m.end() <= f.position
                d = f.position - m.end() if before else m.start() - end
                if tag and end < m.start() and m.end() <= tag_hi:
                    tier = 0                         # its own tag: "(XLY/XLP)"
                elif c_lo <= m.start() < c_hi:
                    tier = (2 if _enclosed(text, m.start(), f.position) else 1) \
                        if before else 3
                elif before:
                    tier = 5 if _enclosed(text, m.start(), f.position) else 4
                else:
                    continue                         # after it, in another clause
                hits.append((tier, d, m.group(0), a))
        if not hits:
            continue
        _, _, _, alias = min(hits)
        mine = by_alias[alias]
        mine_ids = {id(r) for r in mine}
        said = mine[0]["name"]
        fields = [k for r in mine for k in _holds(r["values"], f)]
        want = (TYPE_PERCENT if _OF_OI.match(text, f.position + len(f.text))
                else f.unit_type)
        if fields:
            if want == TYPE_ANY:
                continue
            allowed = {want, TYPE_ANY}
            if not _OF_OI.match(text, f.position + len(f.text)):
                allowed |= set(COMPATIBLE.get(want, ()))
            if any(t in allowed for _, t in fields):
                continue
            k0, t0 = fields[0]
            unit = ("a share of open interest"
                    if _OF_OI.match(text, f.position + len(f.text)) else want)
            out.append((f, f"{f.text.strip()} is bound to {said} but is its {k0} "
                           f"(a {t0}), not {unit}"))
            continue
        others = [r for r in rows if id(r) not in mine_ids and _holds(r["values"], f)]
        if others:
            names = list(dict.fromkeys(r["name"] for r in others))
            out.append((f, f"{f.text.strip()} is bound to {said} but belongs to "
                           f"{' and '.join(names[:2])}"))
    return out


_DOWN: Optional[set] = None


def _down_verb_before(text: str, pos: int) -> bool:
    """Is the word before position `pos` (allowing "by") a falling verb of the
    direction lexicon (config/direction_lexicon.yaml)?"""
    global _DOWN
    if _DOWN is None:
        try:
            import yaml                                         # noqa: PLC0415
            lex = yaml.safe_load((Path(__file__).resolve().parent.parent / "config"
                                  / "direction_lexicon.yaml").read_text(
                                      encoding="utf-8")) or {}
            _DOWN = {str(w).lower() for w in lex.get("down") or []}
        except Exception:                                       # noqa: BLE001
            _DOWN = set()
    m = re.search(r"([A-Za-z]+)\s+(?:by\s+)?$", text[:pos])
    return bool(m) and m.group(1).lower() in _DOWN


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
    series_typed = kinds_of(payload)
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
        # "23.4 POINTS OF OPEN INTEREST" IS A SHARE (W8-2): the unit is the
        # phrase, not its first word, so it asserts a percent and not a price.
        if _OF_OI.match(masked, f.position + len(f.text)):
            f.unit_type = TYPE_PERCENT
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
                # THE VERB CARRIES THE SIGN (W-1.1a item 4): "fell 3 bp" for
                # -3 is the move as written after a falling verb, not a dropped
                # sign. The direction audit holds the verb to the sign.
                if neg and _down_verb_before(masked, f.position):
                    matched.append((f, -neg[0]))
                    continue
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
                # THE SERIES-KIND EQUIVALENCE (W-1.1a item 1): a price-typed
                # value in a row whose kind is written in this unit.
                skinds = {sk for v, t, sk in series_typed
                          if t == TYPE_PRICE
                          and (f.low <= v < f.high or abs(v - f.value) <= 1e-9)}
                ok = sorted(sk for sk in skinds if sk
                            and f.unit_type in KIND_UNITS.get(sk, ()))
                if ok:
                    f.series_kind = ok[0]
                    matched.append((f, hit))
                    continue
                named = ", ".join(sorted(sk for sk in skinds if sk)) or "none declared"
                f.type_conflict = (
                    f"written as {f.unit_type} but the payload carries this value "
                    f"as {sorted(kinds)}; series kind: {named}")
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

    # THE SERIES BINDING (W8-2): in a sentence that names a series, a figure
    # must be that series' own. Only matched figures: an unmatched one fails
    # already.
    ok_ids = {id(f) for f, _ in matched}
    for f, why in series_bindings(text or "", [f for f in figures if id(f) in ok_ids],
                                  payload):
        f.bind_conflict = why
        matched = [(g, h) for g, h in matched if g is not f]
        unmatched.append(f)

    return AuditResult(passed=not unmatched, figures=figures,
                       unmatched=unmatched, matched=matched,
                       payload_values=len(values), names=names)


# ---------------------------------------------------------------------------
# THE ROLE AUDIT (T3.6 M1, the Monthly dry run of 13 Oct 2026)
# ---------------------------------------------------------------------------
#
# The executive summary wrote "Gold closed the month at 4,554.56 ... IWM at
# 277.22 ... the dollar held at 99.35", and section 2 "closes September with gold
# at 4,554.56, SPY at 721.82 and QQQ at 670.83". Every figure existed: each was a
# 40-week AVERAGE in the long-frame table. The numeral audit matched them, and the
# label audit (above) checks a figure printed beside a NAMED level, not a figure
# bound to a close by the verb. So every figure the payload offers now carries its
# ROLE -- close, average, percentile, change, level -- taken from its field name
# or its table column, and a figure bound to a close-word ("closed at", "the
# close", "ended the month at") must be one the payload holds AS A CLOSE. A figure
# the payload holds only as an average under a close-word is withheld, and the
# retry hears which average it was.
ROLE_CLOSE, ROLE_AVERAGE = "close", "average"
ROLE_PERCENTILE, ROLE_CHANGE, ROLE_LEVEL = "percentile", "change", "level"
_CLOSE_KEYS = {"close", "last", "end_level", "month_end_close", "close_level",
               "last_close", "level_close", "prior_close", "end"}
_LABEL_KEYS = ("market", "name", "series", "label", "symbol", "instrument")
FIELD_NAMES = {"ma_40w": "40-week average", "ma_10m": "10-month average",
               "ma_20m": "20-month average", "ma_20d": "20-day average",
               "ma_50d": "50-day average", "ma_200d": "200-day average",
               "close": "close", "end_level": "month-end close"}


def role_of_key(key: str) -> Optional[str]:
    k = str(key).lower()
    if k in _CLOSE_KEYS or k.endswith("_close"):
        return ROLE_CLOSE
    if k.startswith("ma_") or any(w in k for w in ("average", "avg", "mean")):
        return ROLE_AVERAGE
    if "percentile" in k:
        return ROLE_PERCENTILE
    if _is_move_key(k):
        return ROLE_CHANGE
    if "level" in k or k in ("value", "latest"):
        return ROLE_LEVEL
    return None


def role_of_column(head: str) -> Optional[str]:
    h = str(head).lower()
    if "average" in h or "moving" in h:
        return ROLE_AVERAGE
    if "close" in h:
        return ROLE_CLOSE
    if "percentile" in h:
        return ROLE_PERCENTILE
    if any(w in h for w in ("move", "change", "the month", "week", "year to date")):
        return ROLE_CHANGE
    if "level" in h or "last" in h:
        return ROLE_LEVEL
    return None


_CELL_NUM = re.compile(r"^[+−-]?\$?(\d[\d,]*(?:\.\d+)?)")


def roles(payload: Any, _label: Optional[str] = None, _out: Optional[list] = None,
          _depth: int = 0) -> list[tuple[float, str, str]]:
    """(value, role, where) for every figure the payload offers with a role:
    each numeric field by its name, each table cell by its column's head."""
    out = [] if _out is None else _out
    if _depth > 12:
        return out
    if isinstance(payload, dict):
        label = next((str(payload[k]) for k in _LABEL_KEYS
                      if isinstance(payload.get(k), str)), _label)
        cols = payload.get("columns")
        if isinstance(cols, list) and isinstance(payload.get("rows"), list):
            for row in payload["rows"]:
                if not isinstance(row, (list, tuple)) or not row:
                    continue
                name = str(row[0])
                for j, cell in enumerate(row[1:], start=1):
                    if j >= len(cols):
                        break
                    role = role_of_column(cols[j])
                    m = _CELL_NUM.match(str(cell).strip()) if role else None
                    if m:
                        out.append((float(m.group(1).replace(",", "")), role,
                                    f"{name}'s {cols[j]}"))
        for k, v in payload.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                role = role_of_key(k)
                if role:
                    name = FIELD_NAMES.get(str(k), str(k).replace("_", " "))
                    out.append((abs(float(v)) if role == ROLE_CHANGE else float(v),
                                role, f"{label}'s {name}" if label else name))
            elif isinstance(v, (dict, list, tuple)):
                roles(v, label, out, _depth + 1)
    elif isinstance(payload, (list, tuple)):
        for v in payload:
            roles(v, _label, out, _depth + 1)
    return out


_CLOSE_WORD = re.compile(
    r"\b(?:clos(?:ed|es|ing)\b|the\s+close\b|month[- ]end\s+close|"
    r"(?:ended|finished|settled)\b)", re.I)
_OTHER_ROLE = re.compile(r"\b(?:average|averages|mean|percentile|high|low|from|"
                         r"range|band|between)\b", re.I)
_SENTENCE = re.compile(r"(?<=[.!?])\s+")
# A88 (d): what a close-word's span skips, and where it ends. The span runs to a
# semicolon, a colon, a dash or a bracket; a comma continues it, because the list
# ("closes September with gold at 4,554.56, SPY at 721.82") is the case the audit
# exists for.
_ROLE_SPAN_END = re.compile(r"[;:—–()]|\s-\s")
_MONTH_RX = "(?:" + "|".join(sorted(MONTHS, key=len, reverse=True)) + r")\.?(?![a-z])"
_DATE_PHRASE = re.compile(
    r"\b\d{1,2}(?:st|nd|rd|th)?\s+" + _MONTH_RX + r"(?:,?\s+\d{4})?\b"
    r"|\b" + _MONTH_RX + r"\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s+\d{4})?\b"
    r"|\b" + _MONTH_RX + r"\s+\d{4}\b|\b\d{4}-\d{2}-\d{2}\b", re.I)
_WINDOW_AFTER = re.compile(r"(?:st|nd|rd|th)?-(?:day|week|month|year|session)s?\b", re.I)
# A weight is skipped only where the prose calls it one ("the 0.65 and 0.5
# weights") and the payload carries it as one: a bare 0.5 after "closed" is read.
_WEIGHT_AFTER = re.compile(r"(?:\s+(?:and|or|to)\s+[+−-]?\d[\d.,]*%?)*\s+"
                           r"(?:weights?|probabilit(?:y|ies)|odds|chances?)\b", re.I)


def _weights(payload: Any, _depth: int = 0) -> list[float]:
    """Every value the payload carries as a probability or a weight."""
    out: list[float] = []
    if _depth > 12:
        return out
    if isinstance(payload, dict):
        for k, v in payload.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool) \
                    and re.search(r"probab|weight", str(k), re.I):
                out.append(abs(float(v)))
            elif isinstance(v, (dict, list, tuple)):
                out += _weights(v, _depth + 1)
    elif isinstance(payload, (list, tuple)):
        for v in payload:
            out += _weights(v, _depth + 1)
    return out


def _tolerance(text: str) -> float:
    num = re.sub(r"[^\d.]", "", text)
    dec = len(num.split(".", 1)[1]) if "." in num else 0
    return 0.5 * 10 ** -dec + 1e-9


def role_faults(text: Optional[str], payload: Any) -> list[str]:
    """[] or one fault line: every figure a close-word binds to that the payload
    holds only as an average. Within a sentence, a close-word binds the figures
    after it -- "closes September with gold at 4,554.56, SPY at 721.82" -- unless
    another role's word stands between ("its 40-week average of ..."). A figure
    that is a change (a percent, bp or points) is not a close and is not read."""
    rs = roles(payload)
    if not rs or not text:
        return []
    weights = _weights(payload)
    bad = []
    for sent in _SENTENCE.split(text):
        m = _CLOSE_WORD.search(sent)
        if not m:
            continue
        stop = _ROLE_SPAN_END.search(sent, m.end())
        span_end = stop.start() if stop else len(sent)
        dates = [d.span() for d in _DATE_PHRASE.finditer(sent)]
        figs = [f for f in extract(sent) if m.end() <= f.position < span_end]
        prev = m.end()
        for f in figs:
            gap = sent[prev:f.position]
            prev = f.position + len(f.text)
            if f.is_percent or _CHANGE_AFTER.match(sent, f.position + len(f.text)):
                continue
            if _OTHER_ROLE.search(gap):
                continue
            # A88 (d): a day of the month or a year ("1 October 2026"), a
            # window's length ("its 20-day average") and a weight or probability
            # the payload types as one are not the figure the close-word names.
            if any(s <= f.position < e for s, e in dates) \
                    or _WINDOW_AFTER.match(sent, f.position + len(f.text)) \
                    or (_WEIGHT_AFTER.match(sent, f.position + len(f.text))
                        and any(abs(w - abs(f.value)) <= 1e-9 for w in weights)):
                continue
            tol = _tolerance(f.text)
            held = [(r, w) for v, r, w in rs if abs(v - abs(f.value)) <= tol]
            if held and not any(r == ROLE_CLOSE for r, _ in held) \
                    and any(r == ROLE_AVERAGE for r, _ in held):
                where = next(w for r, w in held if r == ROLE_AVERAGE)
                bad.append(f"'{m.group(0)} ... {f.text}': {f.text} is {where}, an "
                           f"average, not a close")
    if not bad:
        return []
    return [f"role audit failed on {len(bad)} figure{'' if len(bad) == 1 else 's'} -- "
            f"'closed at' and 'the close' bind to a close, never to an average: "
            + "; ".join(bad)]


# ---------------------------------------------------------------------------
# THE DISPLAY FORM OF A LARGE FIGURE (T3.6 M9)
# ---------------------------------------------------------------------------
# The dry run printed "83553.85" and "7651.54" where the tables print
# "83,553.85": prose copies the payload's display string, thousands separators
# included. A figure of four or more integer digits printed without them is
# withheld, and the retry hears the form to copy. A year (1900-2100, no
# decimals) and a name that carries digits are not figures.
_RAW_LARGE = re.compile(r"(?<![\w.,/$-])(\d{4,})(\.\d+)?(?![\w,]|\.\d)")


def separator_faults(text: Optional[str]) -> list[str]:
    bad = []
    for m in _RAW_LARGE.finditer(text or ""):
        whole, frac = m.group(1), m.group(2) or ""
        if not frac and 1900 <= int(whole) <= 2100 and len(whole) == 4:
            continue
        bad.append(f"'{m.group(0)}' (write '{int(whole):,}{frac}', as the tables "
                   f"print it)")
    if not bad:
        return []
    return ["a large figure printed without its thousands separators -- copy the "
            "display string the tables print: " + "; ".join(bad)]
