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
    # ---- TYPES: a numeral whose unit word contradicts its figure is rejected ----
    #
    # The published weekly called a flag "thirteen-day-old" because 13 was in the
    # payload -- as the pin-row COUNT. Every figure existed and the sentence was
    # false, which is the class of error existence-checking cannot reach.
    from altdata.numeral_audit import types_of, type_of_key           # noqa: PLC0415
    rows = {"pin_rows_today": 13}
    r = audit("13 rows were logged", rows)
    check(r.passed, "'13 rows' against a count of 13 passes")
    r = audit("a 13-day-old flag", rows)
    check(not r.passed,
          "'13-day-old' against the same count FAILS -- the figure exists and the "
          "sentence calls it the wrong kind of thing")
    check(any(f.type_conflict for f in r.unmatched),
          f"and the failure names it a unit mismatch, not a missing figure "
          f"({r.reason()[:96]}...)")
    check("13" in r.reason() and "count" in r.reason(),
          "with the figure and the type the payload actually carries")

    # ONE COMPATIBLE MATCH IS ENOUGH: 13 as days somewhere makes the sentence true.
    r = audit("a 13-day-old flag", {"pin_rows_today": 13, "age_days": 13})
    check(r.passed,
          "the same sentence passes when the payload carries 13 as days too -- one "
          "compatible match is enough, because citing either field is citing "
          "something true")

    # A unit word the table does not know asserts nothing.
    r = audit("the 760 put wall", {"put_wall": 760})
    check(r.passed, "'760 put wall' passes: 'put' is not a unit word, and a table "
                    "of every adjective a report might use is a table nobody can "
                    "keep correct")
    # A percentile is not a percent.
    # Whole-number ordinals since H-1: "19.8th" now fails on its form alone, so
    # the type rule is exercised with the form a paragraph is allowed to write.
    r = audit("at the 20th percent", {"percentile": 19.8})
    check(not r.passed and r.unmatched and r.unmatched[0].type_conflict,
          "'20th percent' against a PERCENTILE fails ON TYPE -- the two are "
          "different claims and confusing them is what this table is for")
    r = audit("at the 20th percentile", {"percentile": 19.8})
    check(r.passed, "while the percentile itself passes")
    # An unconstrained field imposes nothing.
    r = audit("13 days", {"whatever": 13})
    check(r.passed,
          "a field whose name says nothing about its kind imposes nothing -- better "
          "to check less than to reject a true sentence on a guess")
    for key, want in (("pin_rows_today", "count"), ("age_days", "days"),
                      ("spot", "price"), ("percentile", "percentile"),
                      ("distance_pct", "percent"), ("z_score", "z"),
                      ("net_gex", "dollars"), ("vx_front_ratio", "ratio"),
                      ("nothing_in_particular", "any")):
        check(type_of_key(key) == want,
              f"type_of_key({key!r}) is {want!r}")
    check(types_of({"a": {"age_days": 4}, "b": [1.0]})[0][1] == "days",
          "types travel through nesting, and a list inherits its parent's field")

    # ---- ORDINALS: they were not extracted at all, so they were not audited ----
    f = extract("at its 19.8th percentile")
    check(len(f) == 1 and abs(f[0].value - 19.8) < 1e-9,
          f"'19.8th' extracts as 19.8 (got {[x.text for x in f]}) -- an ordinal "
          f"suffix is part of the number's presentation")
    check(f and f[0].unit_type == "percentile",
          "and the unit word after the ordinal is still read")
    check(not audit("at its 19.9th percentile", {"percentile": 19.8}).passed,
          "so a WRONG ordinal percentile now fails. Before this it passed: '19.8th' "
          "hit the trailing-letter guard, matched nothing, and every percentile "
          "either report wrote in ordinal form went unchecked")
    for t in ("0DTE gamma", "the 2s10s curve"):
        check(not extract(t),
              f"and the guard still rejects a digit fused to a word ({t!r})")

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


def group_f() -> None:
    """Names, not figures (Weekly edition 1, item 1)."""
    print(f"\n{LINE}\nF. TENORS, INSTRUMENTS AND DAYS OF THE MONTH ARE NAMES\n{LINE}")
    from altdata import numeral_audit as na
    v = na.vocabulary()
    declared = {str(t).lower() for t in v.get("name_tokens") or []}
    want = {"2-year", "5-year", "10-year", "30-year", "3m", "0dte", "50-day",
            "200-day"}
    check(want <= declared, f"config/audit_vocabulary.yaml declares the tenor and "
                            f"instrument tokens ({sorted(declared)})")
    bare = {"week_ending": "2026-09-25", "yield": 4.81}
    for t in ("the 30-year yield at 4.81", "the 2-year, 5-year and 10-year",
              "the 3M bill", "0DTE flow", "the 50-day and 200-day averages"):
        r = audit(t, bare)
        check(r.passed, f"{t!r} passes against a payload holding none of its "
                        f"tenor numerals -- they are names")
    check(not audit("30 sessions", bare).passed,
          "while a bare 30 is still a figure and still fails when absent")
    check(not audit("a 7-year low", bare).passed,
          "and an undeclared N-year is checked: a 7-year low is a claim")
    days = {"as_of": "2026-09-27T00:36:02+00:00", "since": "2026-09-25"}
    check(sorted(na.payload_days(days)) == [25, 27],
          "a DATETIME contributes its day -- the \\b before 'T' dropped it, and "
          "the 28 September morning test was withheld on '27th' for that")
    for t in ("between the 25th and the 27th", "on 27 September",
              "on September 25"):
        r = audit(t, days)
        check(r.passed, f"{t!r}: a day in date form that the payload's dates "
                        f"carry is a name")
    for t, why in (("the 28th", "a day the payload's dates do not carry"),
                   ("the 27th percentile", "an ordinal with a unit word"),
                   ("up 27%", "a percent")):
        check(not audit(t, {"since": "2026-09-25", "x": 1.5}).passed,
              f"{t!r} is still a figure: {why}")


def group_g() -> None:
    """Ordinals (H-1 item 3)."""
    print(f"\n{LINE}\nG. A PERCENTILE IN PROSE IS A WHOLE-NUMBER ORDINAL\n{LINE}")
    from altdata import numeral_audit as na
    # "the 11th percentile" is a PERCENTILE ordinal, so since 1 Oct it must equal
    # a stored percentile's ordinal -- e_percentile 11.2 rounds to 11th. The
    # other ordinals here are counts and keep the plain match.
    P = {"percentile": 96.1, "a": 21.0, "b": 12.0, "c": 100.0, "d": 2.0,
         "e_percentile": 11.2, "f": 3.0, "g": 22.0, "h": 13.0}
    check([na.ordinal_suffix(n) for n in (1, 2, 3, 4, 11, 12, 13, 21, 22, 23, 101,
                                          111, 112)]
          == ["st", "nd", "rd", "th", "th", "th", "th", "st", "nd", "rd", "st",
              "th", "th"],
          "the suffix rule: 1st 2nd 3rd 4th, 11th 12th 13th, 21st 22nd 23rd, "
          "101st, 111th 112th")
    for t in ("at the 96th percentile", "the 21st", "the 12th", "the 100th",
              "the 2nd", "the 11th percentile", "the 3rd", "the 22nd", "the 13th"):
        check(audit(t, P).passed, f"{t!r} passes -- a whole-number ordinal "
                                  f"matches its payload value")
    for t, why in (("at the 96.1th percentile", "an ordinal on a non-integer"),
                   ("the 21th", "the suffix disagrees"),
                   ("the 12nd", "the suffix disagrees"),
                   ("the 11st", "the suffix disagrees"),
                   ("the 2th", "the suffix disagrees"),
                   ("the 13rd", "the suffix disagrees"),
                   ("the 22th", "the suffix disagrees")):
        r = audit(t, P)
        err = r.unmatched[0].ordinal_error if r.unmatched else ""
        check(not r.passed and why in err,
              f"{t!r} fails: {err[:60] or 'passed'}")
    r = audit("at the 96.1th percentile", P)
    check("write 96th" in r.reason(),
          f"the reason names the right form ({r.reason()[:90]})")


def group_i() -> None:
    """1 Oct 2026: percentile ordinals are precomputed, half up, and copied."""
    print(f"\n{LINE}\nI. A PERCENTILE ORDINAL IS THE PAYLOAD'S, COPIED -- NEVER "
          f"ROUNDED BY THE WRITER\n{LINE}")
    import types
    from altdata import numeral_audit as na
    from daily_cascade import narrative as nv

    # The four percentiles the 1 Oct Monthly dry run's paragraph truncated.
    got = [na.percentile_ordinal(v) for v in (51.7, 68.6, 88.6, 32.5)]
    check(got == ["52nd", "69th", "89th", "33rd"],
          f"51.7, 68.6, 88.6 and 32.5 round half up to {got} -- not the "
          f"truncated 51st, 68th, 88th and 32nd")
    check([na.percentile_ordinal(v) for v in (96.1, 12.5, 11.49, 0.4, 100.0)]
          == ["96th", "13th", "11th", "0th", "100th"],
          "96.1 -> 96th, 12.5 -> 13th (half up, 11-13 keep th), 11.49 -> 11th")

    P = na.with_ordinals({"regime": {"dimensions": [
        {"dimension": "credit", "percentile": 51.7},
        {"dimension": "inflation", "percentile": 68.6}]},
        "alt": [{"metric": "fred.wti", "percentile": 88.6}],
        "vol": {"champion": {"pctile": 32.5, "ratio": 1.04}}, "sessions": 2})
    check(P["regime"]["dimensions"][0].get("percentile_ordinal") == "52nd"
          and P["vol"]["champion"].get("pctile_ordinal") == "33rd"
          and "ratio_ordinal" not in P["vol"]["champion"],
          "with_ordinals() puts `<field>_ordinal` beside every percentile field, "
          "at any depth, and beside nothing else")
    check(na.with_ordinals(P) == P, "and is idempotent")

    for text, want in (("credit sits at the 51st percentile", False),
                       ("credit sits at the 52nd percentile", True),
                       ("inflation is at its 68th percentile", False),
                       ("inflation is at its 69th percentile", True),
                       ("oil's percentile, the 88th, is high", False),
                       ("oil's percentile, the 89th, is high", True),
                       ("the front ratio's 32nd percentile", False),
                       ("the front ratio's 33rd percentile", True),
                       ("a 2nd session of it", True)):
        r = na.audit(text, P)
        check(r.passed == want,
              f"{text!r} {'passes' if want else 'is WITHHELD'}"
              + ("" if want else f" ({r.unmatched[0].ordinal_error[:70]}...)"
                 if r.unmatched else ""))
    r = na.audit("credit sits at the 51st percentile", P)
    check("_ordinal" in r.reason() and "52nd" in r.reason(),
          "the reason names the field to copy and the stored value nearest it")

    # THROUGH generate(), the funnel all four reports use: the model sees the
    # field, and a truncated ordinal withholds the paragraph.
    seen = {}

    class Resp:
        def __init__(self, t):
            self.content = [types.SimpleNamespace(type="text", text=t)]
            self.model = "fixture-model"
            self.stop_reason = "end_turn"

    class Client:
        def __init__(self, t):
            def create(**k):
                seen["prompt"] = k["messages"][0]["content"]
                return Resp(t)
            self.messages = types.SimpleNamespace(create=create)

    raw = {"regime": {"dimensions": [{"dimension": "credit", "percentile": 51.7}]}}
    kw = dict(system_prompt=nv.SYSTEM_PROMPT, max_chars=5000, one_paragraph=False,
              citable_ids=[])
    bad_ = nv.generate(raw, client=Client("Credit is at the 51st percentile."), **kw)
    check('"percentile_ordinal": "52nd"' in seen.get("prompt", ""),
          "generate() hands the model the payload WITH the ordinal field")
    check(not bad_.published and "51st" in (bad_.reason or ""),
          f"a truncated 51st is withheld ({bad_.state})")
    good = nv.generate(raw, client=Client("Credit is at the 52nd percentile."), **kw)
    check(good.published, f"the copied 52nd publishes ({good.state})")
    check("_ordinal" in nv.SYSTEM_PROMPT and "verbatim" in nv.SYSTEM_PROMPT.lower(),
          "and the brief tells the model to copy the _ordinal field verbatim")


def group_j() -> None:
    """1 Oct 2026: every move carries its signed display form, copied verbatim."""
    print(f"\n{LINE}\nJ. A MOVE IS COPIED FROM ITS `_signed` FIELD -- THE SIGN RULE "
          f"STANDS\n{LINE}")
    import types
    from altdata import numeral_audit as na
    from daily_cascade import narrative as nv
    M = na.MINUS

    check([na.signed_display(-6.75, "%"), na.signed_display(0.36, "%"),
           na.signed_display(12.0, " bp"), na.signed_display(0.0, " bp"),
           na.signed_display(-1234.5)]
          == [f"{M}6.75%", "+0.36%", "+12 bp", "0 bp", f"{M}1,234.5"],
          "the display forms: −6.75%, +0.36%, +12 bp, 0 bp, −1,234.5")
    P = na.with_signed({"scorecard": [
        {"label": "Gold (GLD)", "change_pct": -6.75},
        {"label": "10-year Treasury", "change_bps": 49.0},
        {"metric": "fred.wti", "delta_20d": 4.35, "delta_unit": "percent",
         "delta_percentile": 88.6}]})
    rows = P["scorecard"]
    check(rows[0].get("change_pct_signed") == f"{M}6.75%"
          and rows[1].get("change_bps_signed") == "+49 bp"
          and rows[2].get("delta_20d_signed") == "+4.35%"
          and "delta_percentile_signed" not in rows[2],
          "with_signed() puts `<field>_signed` beside every move, its unit from the "
          "name or the sibling delta_unit, and nothing beside a percentile")
    check(na.with_signed(P) == P, "and is idempotent")
    check(na.payload_numbers(f"{M}6.75%") == [-6.75],
          "the stored −6.75% reads as NEGATIVE, so it cannot excuse an unsigned "
          "6.75% in the prose")

    # GOLD'S MOVE FROM THE 1 OCT PAYLOAD, through generate().
    seen = {}

    class Resp:
        def __init__(self, t):
            self.content = [types.SimpleNamespace(type="text", text=t)]
            self.model = "fixture-model"
            self.stop_reason = "end_turn"

    class Client:
        def __init__(self, t):
            def create(**k):
                seen["prompt"] = k["messages"][0]["content"]
                return Resp(t)
            self.messages = types.SimpleNamespace(create=create)

    raw = {"month": "September 2026",
           "moves": [{"label": "Gold (GLD)", "change_pct": -6.75}]}
    kw = dict(system_prompt=nv.SYSTEM_PROMPT, max_chars=5000, one_paragraph=False,
              citable_ids=[])
    good = nv.generate(raw, client=Client(f"Gold fell {M}6.75% over September."),
                       **kw)
    check('"change_pct_signed": "' in seen.get("prompt", "")
          and f"{M}6.75%" in seen.get("prompt", ""),
          "generate() hands the model the signed form beside the move")
    check(good.published, f"gold's {M}6.75%, copied, publishes ({good.state})")
    bad_ = nv.generate(raw, client=Client("Gold fell 6.75% over September."), **kw)
    check(not bad_.published and "change_pct_signed" in (bad_.reason or ""),
          f"an unsigned 6.75% is WITHHELD, and the reason names the field to copy "
          f"({(bad_.reason or '')[:90]})")
    check("_signed" in nv.SYSTEM_PROMPT and "verbatim" in nv.SYSTEM_PROMPT,
          "and the brief tells the model to copy the _signed field verbatim")


def group_h() -> None:
    """G-1: a numeral beside a named level must be THAT level, for that symbol."""
    print(f"\n{'=' * 78}\nH. THE LABEL AUDIT -- A LEVEL PRINTED UNDER THE WRONG NAME\n"
          f"{'=' * 78}")
    import json
    from altdata import numeral_audit as na
    from daily_cascade import payload as pm
    fx = json.loads((REPO / "tests" / "fixtures" / "close_narrative_2026-09-30.json")
                    .read_text(encoding="utf-8"))
    para, payload = fx["paragraph"], fx["payload"]
    consts = pm.NARRATIVE_UNIT_CONSTANTS
    r = na.audit(para, payload, extra_values=consts)
    bad = [f.text.strip() for f in r.unmatched]
    check(not r.passed and bad == ["760"] and r.unmatched[0].label_conflict,
          f"the 30 Sep paragraph is WITHHELD on exactly one figure, the 760 printed "
          f"as the put wall ({r.reason()})")
    check("745" in r.unmatched[0].label_conflict
          and "max_pain" in r.unmatched[0].label_conflict
          and "invalidation_level" in r.unmatched[0].label_conflict,
          "and the reason names the put wall's real value and the two names 760 "
          "does hold")
    fixed = para.replace("with the put wall at 760 sitting",
                         "with the invalidation level at 760 sitting")
    r2 = na.audit(fixed, payload, extra_values=consts)
    check(r2.passed and len(r2.figures) == 18,
          f"the corrected clause passes, all 18 figures ({r2.reason()})")
    check("745 put wall's" in para and na.audit(
              "leaving the 745 put wall's new alignment", payload).passed,
          "the same paragraph's '745 put wall' -- a number BEFORE its label -- passes")

    # A shared number passes only under a name that holds it.
    p = {"exposure": [{"symbol": "SPY", "put_wall": 745.0, "call_wall": 785.0,
                       "max_pain": 760.0, "gamma_flip": 768.9167,
                       "peak_abs_gex_strike": 745.0, "put_wall_change": 15.0},
                      {"symbol": "QQQ", "put_wall": 760.0, "call_wall": 800.0}],
         "portfolio": {"positions": [{"instrument": "SPY@ARCA.USD",
                                      "invalidation_level": 760.0,
                                      "avg_cost": 771.25}]}}
    for text, want, why in (
            ("SPY max pain at 760", True, "760 under max pain, which holds it"),
            ("the SPY invalidation level at 760", True, "under invalidation"),
            ("the SPY put wall at 760", False, "under put wall, which is 745"),
            ("the SPY gamma flip at 768.92", True, "a flip within print precision"),
            ("the SPY gamma flip at 768.99", False, "a flip outside print precision"),
            ("the SPY 745 put wall", True, "a number written before its label"),
            ("the SPY peak gamma at the 745 strike", True,
             "a bare strike: any strike-valued field"),
            ("the SPY put wall jumped 15 points to 745", True,
             "a CHANGE beside the label is skipped; the level after it is checked"),
            ("the SPY put wall jumped 15 points to 760", False,
             "and the level after the change is still held to the name"),
            ("QQQ's put wall at 760", True,
             "the symbol is the one the sentence names: QQQ's put wall IS 760"),
            ("the SPY put wall moved, and 760 is the line", True,
             "a clause boundary ends the binding: 760 is not the put wall here"),
    ):
        rr = na.audit(text, p)
        check(rr.passed is want, f"{text!r}: {'passes' if want else 'fails'} -- "
                                 f"{why}" + ("" if want else f" ({rr.reason()})"))
    for text, want, why in (
            ("the call wall dropped from 780 to 775", True,
             "FROM 780 is the previous call wall; TO 775 is the call wall"),
            ("the call wall dropped from 775 to 780", False,
             "and swapped, both are wrong"),
    ):
        rr = na.audit(text, {"call_wall": 775.0, "prior_call_wall": 780.0})
        check(rr.passed is want, f"{text!r}: {'passes' if want else 'fails'} -- "
                                 f"{why}" + ("" if want else f" ({rr.reason()})"))
    check(na.audit("the put wall at 760", {"rows": [{"max_pain": 760.0}]}).passed,
          "a payload that carries no put wall at all leaves the label unchecked -- "
          "the plain match still applies")


def main() -> int:
    print(f"{LINE}\nD3 numeral audit -- the precondition for any generated "
          f"sentence\n{LINE}")
    group_a()
    group_b()
    group_c()
    group_d()
    group_e()
    group_f()
    group_g()
    group_h()
    group_i()
    group_j()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
