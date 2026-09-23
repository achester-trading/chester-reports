"""
Validation gate for D3, the numeral audit.

This gate decides whether the Daily Cascade is ever allowed to contain a
sentence. Architecture 32.5 keeps the reports data-only until something can FAIL
a block for carrying a number that is not in its payload, so the audit is the
precondition for prose and this file is the precondition for the audit. A
permissive audit is worse than none: it would license prose while proving
nothing, and the first fabricated figure would arrive with a green gate behind it.

So the seeded failures matter more than the passing case. Three are required by
the change order and all three are here, plus the ones that turned out to matter
while it was being written:

  A  EXTRACTION. What is a figure and what is not. 0DTE and 2s10s are
     identifiers; a version string is not a claim; a percent at the end of a
     sentence keeps its percent sign; separators and signs survive.
  B  FORMATTING TOLERANCE. A rounded figure passes and a TRANSPOSED one fails,
     which is the property the whole design turns on. Derived from the written
     precision, so 762.45 accepts a half-unit of the last place and nothing more.
  C  THE THREE SEEDED FAILURES. An invented number, a transposed digit, a stale
     prior-day value.
  D  WHAT MUST NOT BE MATCHABLE. Booleans are not 1. A number inside an
     arbitrary string is not a licence to print digits. Depth is bounded.
  E  THE RESULT CONTRACT. pass/fail, the unmatched list, and a one-line reason
     fit for the withheld-narrative note.

    python tools/validate_numeral_audit.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from altdata.numeral_audit import audit, extract, payload_numbers  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = 0
FAIL = 0
LINE = "=" * 78

# The payload the reference paragraph in docs/narrative-template-close.md is
# written against, reduced to what its numbers come from.
PAYLOAD = {
    "session": "2026-09-09",
    "spy": {"close": 762.4500122070312, "prior_close": 759.98},
    "flip": 771.4,
    "call_wall": 775.0,
    "prior_call_wall": 780.0,
    "put_wall": 760.0,
    "dollar_gamma_per_1pct": 10_512_000_000.0,
    "prior_dollar_gamma_per_1pct": 6_480_000_000.0,
    "vix": 14.8,
    "pin_hits": 2,
    "distance_points": 2.45,
    "distance_pct": 0.0037,
}
# The 1 in "per 1% decline" belongs to the metric's definition, not to the
# market. Declared by the caller; see audit()'s docstring.
UNITS = [1.0]


def ok(m: str) -> None:
    global PASS
    PASS += 1
    print(f"  PASS  {m}")


def bad(m: str) -> None:
    global FAIL
    FAIL += 1
    print(f"  FAIL  {m}")


def check(c: bool, m: str) -> None:
    ok(m) if c else bad(m)


def texts(figs) -> list[str]:
    return [f.text for f in figs]


def group_a() -> None:
    print(f"{LINE}\nA. EXTRACTION -- what is a figure, and what is not\n{LINE}")

    f = extract("0DTE gamma and the 2s10s curve and SPX500 are not figures.")
    check(not f, f"identifiers are not figures ({texts(f)})")

    f = extract("Version 1.1.1 of the convention.")
    check(not f, f"a version string is not a figure ({texts(f)})")

    f = extract("up 0.35%.")
    check(len(f) == 1 and f[0].is_percent,
          "a percent ending a sentence KEEPS its percent sign -- a single "
          "combined guard silently dropped it, which made a stored fraction "
          "unmatchable")

    # A SPELLED-OUT MAGNITUDE IS PART OF THE NUMBER, in both directions.
    # A NUMERAL IN A PAYLOAD STRING IS CITABLE; ARITHMETIC OVER IT IS NOT.
    rule = {"invalidation": "a settled close below the put wall at 760"}
    r = audit("the rule is a settled close below 760", rule)
    check(r.passed,
          "a figure inside a payload STRING is citable -- both briefs require the "
          "paragraph to state the rule as written, and the register's invalidation "
          "is free text")
    r = audit("the rule is a settled close below 755", rule)
    check(not r.passed,
          "while a near miss is still rejected: the string admits its own contents "
          "and nothing else")
    window = {"window": ["2026-09-21", "2026-09-27"]}
    r = audit("the week runs 21 to 25 September", window)
    check(not r.passed,
          "and arithmetic over a payload string is NOT admitted -- the weekly's "
          "first run inferred '21 to 25' from a window ending the 27th, and 25 was "
          "correctly rejected")

    f = extract("about 4.59 billion dollars of index per one percent move")
    check(len(f) >= 1 and abs(f[0].value - 4.59e9) < 1e7,
          f"'4.59 billion' extracts at 1e9 scale (got "
          f"{f[0].value if f else None}) -- the form the system prompt permits, "
          f"and the only readable register for a ten-digit dollar figure")
    f = extract("4.59bn of index")
    check(len(f) == 1 and abs(f[0].value - 4.59e9) < 1e7,
          "and the attached form still does")
    # The hole this closes: with the word ignored, a wrong-by-a-billion sentence
    # matched a price.
    r = audit("770 billion dollars of gamma", {"spot": 770.66})
    check(not r.passed,
          "'770 billion dollars' does NOT match a spot of 770.66 -- a scale error "
          "is the one arithmetic mistake a reader cannot catch from context")
    r = audit("spot 770.66", {"spot": 770.66})
    check(r.passed, "while the plain figure still matches")
    # And the single-letter suffixes must not eat the next word.
    f = extract("the put wall to 750 both having moved higher")
    check(len(f) == 1 and f[0].value == 750.0,
          f"'750 both' is 750 and not 750 billion (got "
          f"{f[0].value if f else None}) -- the trailing guard rejects a letter "
          f"fused to a word")
    f = extract("13 pin rows and 8 dimensions")
    check([x.value for x in f] == [13.0, 8.0],
          "and ordinary counts are unaffected")

    f = extract("1,234,567 shares")
    check(len(f) == 1 and abs(f[0].value - 1234567) < 1e-9,
          "thousands separators survive")

    f = extract("down -2.5 points")
    check(len(f) == 1 and abs(f[0].value + 2.5) < 1e-9
          and f[0].low < -2.5 < f[0].high,
          "a signed figure keeps its sign and its interval stays symmetric")

    for text, expect in (("$10.5bn", 1.05e10), ("$10.5mm", 1.05e7),
                         ("250k", 2.5e5), ("1.2tn", 1.2e12)):
        f = extract(f"about {text} of it")
        check(len(f) == 1 and abs(f[0].value - expect) < expect * 1e-9,
              f"{text} scales to {expect:g}")

    # A suffix is part of the number; a word after it is not.
    f = extract("10 bnormal readings")
    check(len(f) == 1 and abs(f[0].value - 10) < 1e-9,
          "a word merely starting with a suffix letter is not a magnitude "
          f"({texts(f)} -> {f[0].value if f else None})")


def group_b() -> None:
    print(f"\n{LINE}\nB. FORMATTING TOLERANCE, derived from the written precision\n{LINE}")

    r = audit("SPY close 762.45.", PAYLOAD, extra_values=UNITS)
    check(r.passed,
          "762.45 matches a stored 762.4500122070312 -- prose rounds and that "
          "is not a discrepancy")

    r = audit("SPY close 762.54.", PAYLOAD, extra_values=UNITS)
    check(not r.passed,
          "762.54 does NOT match it -- a transposed digit is outside the "
          "interval that rounds to the written figure")

    r = audit("The flip sat at 771.", PAYLOAD, extra_values=UNITS)
    check(r.passed, "771 (no decimals) matches a stored 771.4: half a unit")

    r = audit("The flip sat at 772.", PAYLOAD, extra_values=UNITS)
    check(not r.passed, "772 does not -- 771.4 is outside [771.5, 772.5)")

    # The scale must apply to the tolerance too, or a billion-scale figure
    # accepts a half-unit of 0.1 and nothing ever matches.
    r = audit("Dealers must sell $10.5bn per 1% decline.", PAYLOAD,
              extra_values=UNITS)
    check(r.passed, "$10.5bn matches 10,512,000,000 -- the tolerance scales")
    r = audit("Dealers must sell $10.4bn per 1% decline.", PAYLOAD,
              extra_values=UNITS)
    check(not r.passed, "$10.4bn does not -- 10.512bn is outside [10.35, 10.45)bn")

    # A fraction stored as 0.0037 is written 0.37%.
    r = audit("alive by 0.37%", PAYLOAD, extra_values=UNITS)
    check(r.passed, "0.37% matches a stored fraction of 0.0037")
    r = audit("alive by 0.37", PAYLOAD, extra_values=UNITS)
    check(not r.passed,
          "but a BARE 0.37 does not -- only a figure marked as a percent may "
          "match a hundredth, or every number could match something")


def group_c() -> None:
    print(f"\n{LINE}\nC. THE THREE SEEDED FAILURES\n{LINE}")

    # (1) A number from nowhere.
    r = audit("The hedge flow is $88.4bn per 1% decline.", PAYLOAD,
              extra_values=UNITS)
    check(not r.passed and any("88.4" in f.text for f in r.unmatched),
          f"INVENTED: $88.4bn is unmatched ({texts(r.unmatched)})")

    # (2) Two digits swapped -- the failure a loose tolerance would pass, and
    # the reason the interval is derived from the written precision.
    r = audit("SPY close 762.54.", PAYLOAD, extra_values=UNITS)
    check(not r.passed and any("762.54" in f.text for f in r.unmatched),
          f"TRANSPOSED: 762.54 for 762.45 is unmatched ({texts(r.unmatched)})")

    # (3) Yesterday's number presented as today's. The audit cannot know which
    # field a figure was meant to be, so this is only caught when the stale
    # value is genuinely absent from the payload -- which is the case the
    # narrative payload is built for: it carries the CURRENT session's values
    # plus explicitly named prior-session ones, and nothing else.
    today_only = {"session": "2026-09-09",
                  "spy": {"close": 762.4500122070312}}
    r = audit("SPY close 759.98 today.", today_only)
    check(not r.passed and any("759.98" in f.text for f in r.unmatched),
          f"STALE: a prior-day close absent from the payload is unmatched "
          f"({texts(r.unmatched)})")

    # And the honest limit, stated rather than hidden: when the payload DOES
    # carry the prior close (it must, to write a delta), a stale figure is a
    # real number in the payload and this audit passes it. Catching that needs a
    # field-aware check, which this is deliberately not.
    r = audit("SPY close 759.98 today.", PAYLOAD, extra_values=UNITS)
    check(r.passed,
          "LIMIT, recorded: with prior_close in the payload a stale figure "
          "passes -- the audit checks existence, not which field was meant")

    # The reference paragraph's own numbers, all of them, in one go.
    ref = ("Wednesday, 9 September 2026 -- SPY close 762.45. Dealers must sell "
           "about $10.5bn of index per 1% decline, up from $6.48bn on Tuesday, "
           "while the call wall dropped from 780 to 775 and the put wall stayed "
           "at 760. VIX 14.8. The thesis is alive by 2.45 points, 0.37%, and "
           "the pin log has 2 hits.")
    r = audit(ref, PAYLOAD, extra_values=UNITS)
    check(r.passed,
          f"the template's reference paragraph passes in full "
          f"({len(r.figures)} figures){'' if r.passed else ': ' + r.reason()}")


def group_d() -> None:
    print(f"\n{LINE}\nD. WHAT MUST NOT BECOME MATCHABLE\n{LINE}")

    check(payload_numbers({"flag": True, "other": False}) == [],
          "booleans are not numbers -- True is not 1 in any sentence, and "
          "admitting it would let a stray 1 match any flag")

    vals = payload_numbers({"run_id": "morning_anchor-20260919T163010Z"})
    check(vals == [],
          f"digits inside an arbitrary string are NOT payload values ({vals}) "
          f"-- a run id would otherwise license printing any of its digits")

    vals = payload_numbers({"session": "2026-09-09"})
    check(sorted(vals) == [9.0, 9.0, 2026.0],
          f"but an ISO DATE contributes its parts ({sorted(vals)}), so a "
          f"paragraph may open with its own dateline")

    r = audit("SPY close 762.45 on 9 September 2026.", PAYLOAD,
              extra_values=UNITS)
    check(r.passed, "which is exactly what the dateline needs")

    deep = {"a": {"b": {"c": {"d": {"e": 5.0}}}}}
    check(5.0 in payload_numbers(deep), "nested values are reachable")
    cyc: dict = {"x": 1.0}
    cyc["self"] = cyc
    try:
        payload_numbers(cyc)
        ok("a self-referencing payload is bounded rather than fatal")
    except RecursionError:
        bad("a self-referencing payload raised RecursionError")


def group_e() -> None:
    print(f"\n{LINE}\nE. THE RESULT CONTRACT\n{LINE}")
    r = audit("SPY close 762.45.", PAYLOAD, extra_values=UNITS)
    check(r.passed is True and r.n_unmatched == 0, "a pass reports no unmatched")
    check("passed" in r.reason(), f"and a readable reason ({r.reason()!r})")

    r = audit("Closes of 1.23 and 4.56 and 7.89.", PAYLOAD, extra_values=UNITS)
    check(r.passed is False and r.n_unmatched == 3,
          f"three bad figures report as three ({r.n_unmatched})")
    reason = r.reason()
    check(reason.startswith("numeral audit failed on 3 figure"),
          f"the reason counts them, for the one-line withheld note ({reason!r})")
    check(all(f.text in reason for f in r.unmatched),
          "and names them, so the failure is actionable without the log")

    # Never raises: a broken audit must not be able to take the report down.
    for weird in (None, "", "no numbers here"):
        try:
            audit(weird, PAYLOAD)
            ok(f"audit({weird!r}) returns rather than raising")
        except Exception as e:  # noqa: BLE001
            bad(f"audit({weird!r}) raised {type(e).__name__}")
    try:
        audit("1.0", None)
        ok("a null payload returns rather than raising")
    except Exception as e:  # noqa: BLE001
        bad(f"a null payload raised {type(e).__name__}")


def main() -> int:
    print(f"{LINE}\nD3 numeral audit -- the precondition for any generated "
          f"sentence\n{LINE}")
    group_a()
    group_b()
    group_c()
    group_d()
    group_e()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
