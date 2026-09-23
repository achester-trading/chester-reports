#!/usr/bin/env python3
"""
Validation gate for config/claims.yaml. (Audit row 6l; 26.5, 31.1, 31.4)

    python tools/validate_claims.py

WHAT IT ENFORCES, and why each one is the thing that would otherwise rot:

  A. THE FIVE FIELDS. id, value, source, date, review_date on every claim. A
     figure without a source is a rumour; without a date it cannot be replayed;
     without a review date it is permanent by accident.

  B. THE DATES ARE DATES, and review_date is after date. A review date that had
     already passed when the claim was written is a claim nobody intends to check.

  C. THE THREE-DENOMINATOR WARNING IS PRESENT AND VERBATIM, and every
     participant-map claim carries it. 31.4 requires the words, not a paraphrase,
     because the paraphrase is what produces the error the warning is about --
     and the check is on the TEXT rather than on the presence of a key.

  D. CITATION BY ID RESOLVES. Every `claim:<id>` in the register and every id
     named in code must exist. An unknown id must raise rather than render empty.

  E. NOTHING IS DELETED. Withdrawn and superseded claims keep their ids, so a
     report that cited one still resolves. A superseded claim names its successor.

  F. AN OVERDUE REVIEW IS A WARNING. This gate prints overdue claims and does NOT
     fail on them -- the heartbeat carries them, at WARNING, with the exit code
     untouched. A stale ownership share is a figure to recheck, not a broken
     pipeline, and an alarm that the pipeline cannot clear is one the reader
     learns to ignore.
"""

from __future__ import annotations

import datetime as dt
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from altdata import claims                                     # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LINE = "=" * 78
PASS = 0
FAIL = 0

# The clause 31.4 requires verbatim. Checked as a phrase rather than a whole
# paragraph so the warning can gain context without the gate blocking it -- but
# the four measurements and the multiplication have to be there in these words.
VERBATIM = (
    "Direct ownership of U.S. equity, global AUM by institution type, and "
    "equity-relevant AUM are three different measurements, and "
    "forced-flow footprint = equity exposure x turnover x rule-boundness is the "
    "fourth and the one the system sizes by."
)

ID_PATTERN = re.compile(r"^[a-z]{2,4}\.[a-z0-9_]+$")


def ok(msg: str) -> None:
    global PASS
    PASS += 1
    print(f"  PASS  {msg}")


def bad(msg: str) -> None:
    global FAIL
    FAIL += 1
    print(f"  FAIL  {msg}")


def check(cond: bool, msg: str) -> bool:
    (ok if cond else bad)(msg)
    return bool(cond)


def group_a(reg: dict) -> None:
    print(f"\n{LINE}\nA. EVERY CLAIM CARRIES THE FIVE FIELDS\n{LINE}")
    cl = reg["claims"]
    missing: dict[str, list[str]] = {}
    for cid, c in sorted(cl.items()):
        gone = [f for f in claims.REQUIRED_FIELDS if not c.get(f)]
        if gone:
            missing[cid] = gone
    check(not missing,
          f"all {len(cl)} claims carry id, value, source, date and review_date"
          + (f" -- missing: {missing}" if missing else ""))
    badid = [cid for cid in cl if not ID_PATTERN.match(cid)]
    check(not badid,
          f"every id matches <prefix>.<name> so a citation is recognisable as one"
          + (f" -- {badid}" if badid else ""))
    empty = [cid for cid, c in cl.items() if not str(c.get("value") or "").strip()]
    check(not empty, f"no claim has an empty value{f' -- {empty}' if empty else ''}")
    bad_status = {cid: c.get("status") for cid, c in cl.items()
                  if c.get("status") not in claims.STATUSES}
    check(not bad_status,
          f"every status is one of {claims.STATUSES}"
          + (f" -- {bad_status}" if bad_status else ""))


def group_b(reg: dict) -> None:
    print(f"\n{LINE}\nB. THE DATES ARE DATES, AND THE REVIEW IS AFTER THE TAKING\n{LINE}")
    problems = []
    for cid, c in sorted(reg["claims"].items()):
        d = claims._as_date(c.get("date"))                     # noqa: SLF001
        r = claims._as_date(c.get("review_date"))              # noqa: SLF001
        if d is None or r is None:
            problems.append((cid, f"unparseable ({c.get('date')} / "
                                  f"{c.get('review_date')})"))
        elif r <= d:
            problems.append((cid, f"review_date {r} is not after date {d}"))
    check(not problems, "every date parses and every review date follows its claim"
                        + (f" -- {problems}" if problems else ""))
    future = [cid for cid, c in reg["claims"].items()
              if (claims._as_date(c.get("date")) or dt.date(1900, 1, 1))  # noqa: SLF001
              > dt.date.today()]
    check(not future, f"no claim is dated in the future"
                      + (f" -- {future}" if future else ""))


def group_c(reg: dict) -> None:
    print(f"\n{LINE}\nC. THE THREE-DENOMINATOR WARNING, VERBATIM (31.4)\n{LINE}")
    w = (reg["warnings"] or {}).get("three_denominators") or {}
    text = " ".join(str(w.get("text") or "").split())
    check(text == " ".join(VERBATIM.split()),
          "the warning text is verbatim -- 31.4 requires the words, because the "
          "paraphrase is what produces the error it warns about")
    check("forced-flow footprint" in text and "turnover" in text
          and "rule-boundness" in text,
          "and it names the fourth measurement, which is the one the system "
          "sizes by")
    pf = {cid: c for cid, c in reg["claims"].items() if cid.startswith("pf.")}
    without = [cid for cid, c in pf.items()
               if "three_denominators" not in (c.get("warnings") or [])]
    check(pf and not without,
          f"all {len(pf)} participant-map claims carry the warning"
          + (f" -- {without} do not" if without else ""))
    # And the warning is actually delivered by cite(), not merely declared.
    sample = claims.cite(sorted(pf)[0])
    check(any("three different measurements" in t for t in sample["warnings"]),
          f"and cite({sorted(pf)[0]!r}) returns it with the figure, so a report "
          f"cannot print the share without it")


def group_d(reg: dict) -> None:
    print(f"\n{LINE}\nD. CITATION BY ID RESOLVES, AND AN UNKNOWN ID RAISES\n{LINE}")
    try:
        claims.get("br.no_such_claim_at_all")
        bad("an unknown id raises UnknownClaimError")
    except claims.UnknownClaimError as exc:
        ok(f"an unknown id raises rather than rendering empty "
           f"({str(exc)[:60]}...)")
    c = claims.cite(sorted(reg["claims"])[0])
    check(c.get("source") and c.get("as_of"),
          "cite() returns the value WITH its source and its as-of date -- a figure "
          "that arrives without them is a retyped figure by the time it is printed")

    # Every claim: id referenced anywhere in the repo's code or config must exist.
    referenced: set[str] = set()
    for path in list((REPO / "tools").glob("*.py")) + \
            list((REPO / "altdata").rglob("*.py")) + \
            list((REPO / "daily_cascade").glob("*.py")) + \
            list((REPO / "register").glob("*.py")):
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:                                      # noqa: BLE001
            continue
        for m in re.finditer(r"claim:([a-z]{2,4}\.[a-z0-9_]+)", text):
            referenced.add(m.group(1))
    unknown = sorted(r for r in referenced if r not in reg["claims"])
    check(not unknown,
          f"every claim:<id> referenced in code resolves "
          f"({len(referenced)} referenced)" + (f" -- {unknown}" if unknown else ""))


def group_e(reg: dict) -> None:
    print(f"\n{LINE}\nE. NOTHING IS DELETED, AND A SUPERSESSION NAMES ITS HEIR\n{LINE}")
    sup = {cid: c for cid, c in reg["claims"].items()
           if c.get("status") == "superseded"}
    orphan = {cid: c.get("superseded_by") for cid, c in sup.items()
              if not c.get("superseded_by")
              or c.get("superseded_by") not in reg["claims"]}
    check(not orphan,
          f"every superseded claim names an existing successor "
          f"({len(sup)} superseded)" + (f" -- {orphan}" if orphan else ""))
    check(all(c.get("value") for c in reg["claims"].values()),
          "and a withdrawn or superseded claim keeps its value, so a report that "
          "cited it still resolves rather than rendering a hole")


def group_f(reg: dict) -> None:
    print(f"\n{LINE}\nF. AN OVERDUE REVIEW IS A WARNING, NOT A FAILURE\n{LINE}")
    rows = claims.overdue()
    for r in rows[:10]:
        print(f"  WARN  {r['id']} -- review {r['review_date']}, "
              f"{r['days_overdue']} days overdue")
    ok(f"{len(rows)} claim(s) overdue; this gate reports and does not fail on "
       f"them -- the heartbeat carries them at WARNING with the exit code "
       f"untouched")
    # The property that makes that safe: overdue() cannot raise.
    try:
        claims.overdue(as_of=dt.date(2999, 1, 1))
        ok("overdue() answers for any date without raising, so the heartbeat "
           "cannot be taken down by the claims file")
    except Exception as exc:                                   # noqa: BLE001
        bad(f"overdue() raised: {type(exc).__name__}: {exc}")
    far = claims.overdue(as_of=dt.date(2999, 1, 1))
    check(len(far) >= len(reg["claims"]) - 2,
          f"and in 2999 nearly every claim is overdue ({len(far)} of "
          f"{len(reg['claims'])}), so the check is not vacuously quiet")


def main() -> int:
    print(f"{LINE}\nclaims.yaml -- the cited figures (6l)\n{LINE}")
    reg = claims.load()
    print(f"  {len(reg['claims'])} claims, {len(reg['warnings'])} standing "
          f"warnings, version {reg['version']}")
    for fn in (group_a, group_b, group_c, group_d, group_e, group_f):
        fn(reg)
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
