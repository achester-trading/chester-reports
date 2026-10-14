# W-1.2 — the Weekly's storyline tranche: session notes

Branch `w-1-2-storyline` from `origin/t3-5-monthly-frames` at 0efdce1. It stacks
on W-1.1 and T3.5 and merges after them. Spec: §3 of
`docs/change-order-weekly-storyline-2026-10-11.md` (items 2.1–2.8) and §8 ruling
5. Three points were settled on 11 Oct:

- the précis is a second pass over the ten finished commentaries;
- there are six verdict assets, volatility added;
- the stance call's horizon is one week.

Session A, 11 Oct 2026.

**Not run:** the full local suite (CI is the validate), and anything on the box.
I ran the gates this branch touches one at a time, plus the W-1.1 and T3.5
gates; all are green:

| Gate | Result |
|---|---|
| `validate_weekly_storyline` (new) | 30/0 |
| `validate_weekly_stack` | 68/0 |
| `validate_weekly_integrity` | 36/0 |
| `validate_weekly_edits` | 90/0 |
| `validate_weekly_complete` | 57/0 |
| `validate_weekly` | 100/0 |
| `validate_figure_budget` | 110/0 |
| `validate_no_filler` | 14/0 |
| `validate_edition_consistency` | 14/0 |
| `validate_monthly_frames` | 32/0 |
| `validate_monthly_stack` | 261/0 |
| `validate_monthly` | 350/0 |
| `validate_readability` | 63/0 |
| `validate_stack` | 66/0 |
| `validate_stack_cadence` | 99/0 |
| `validate_daily_close` | 102/0 |
| `validate_morning_anchor` | 71/0 |
| `validate_config_refs` | 25/0 |
| `validate_gates` | 31/0 |
| `check_library` | 0 failures |

## What was built

**2.1 The précis, written last** (`daily_cascade/precis.py`).

- **When it runs.** After `stack_prose.write` has written (or withheld) the ten
  commentaries.
- **What it reads.** Each section's claim and paragraph as they will print,
  marked published, withheld or empty, plus the prior edition's précis from the
  archive. It never reads the payload's tables.
- **The allowed set.** The union of the figures the commentaries cite is the
  only set of figures it may write. The frame hands that set over as
  `figures_you_may_cite`.
- **The reply.** The model replies in a fixed tagged form, which code parses:
  - TENSION, FOR, AGAINST;
  - six VERDICT lines (equities, rates, credit, the dollar, commodities,
    volatility), each exactly one of up / down / chop / transition, with each
    direction defined in the frame;
  - CONFIDENCE;
  - three or four CHANGE lines, each "series | date or window | what it would
    show";
  - OUTLOOK, asked for only when a prior précis exists;
  - STANCE;
  - one RELEVANCE line per present section.
- **The audit.** It is the précis's own:
  - every figure in its prose is in the allowed set;
  - the verdict vocabulary;
  - three or four CHANGE lines, each with a series and a recognisable window;
  - p in (0, 1), on the side of the equities verdict;
  - a relevance sentence for every present section, with no figure;
  - the style list and the id rule.

  One retry carries the faults; after that the précis is withheld and prints
  "(précis withheld — audit)".
- **Where it prints.** It opens the edition, before section 1. The read keeps
  its own commentary as section 1.
- **With no prior précis**, code prints the outlook line as "First edition with
  a précis."

**2.2 The stance line.**

- **The probability.** It comes from the précis frame as a number. The frame
  says the call is graded by Brier and must sit on the side of the equity
  verdict.
- **The ledger.** At publication it is written to `altdata/probability_ledger.py`
  as `weekly_stance`, with:
  - the horizon date: the week-ending date a week on;
  - a declared resolution criterion: SPY's close on the last session on or
    before the horizon against its close on the last session on or before this
    week's ending, with equal resolving 0;
  - the base close in the claim.
- **Dry runs** write to their own namespace, `dryrun.weekly_stance`, never the
  live source.
- **Grading.** When the next Weekly runs, every stance due in its namespace is
  resolved and scored by Brier (`precis.grade_stances`).
- **The printed line.** "SPY higher at the next Weekly: p = 0.xx (n=k,
  unvalidated)", where k is the count of graded entries in the namespace.

**2.3 The relevance sentence: the second design.** The sections are written
first. The précis then emits one relevance sentence per present section, and the
renderer prints it at the head of that section's commentary, before its claim.
I did not build the true two-pass loop (tension draft, then sections, then
précis); see Choices.

**2.4 Contradiction status lines** (`daily_cascade/storyline.py`). They are
code-written, so the misfit frame writes none. In the gap table, the last column
"What would close it" becomes "Status". Each open contradiction carries one of:

- **"resolved by <section>":** the configured section prints every row of the
  decomposition, and its commentary published. The cell links to `#sec-<id>`.
  The config is `storyline.contradiction_resolution`; the 9 Oct HY tension maps
  to Plumbing's CCC, investment-grade and high-yield rows.
- **"stale":** open for at least `stale_sessions` (20) sessions and no longer
  widening.
- **"carried — resolves when <the display label's closing condition>"**
  otherwise.

**2.5 The book's terms.** Section 10 ends with a code-written line built from
three things:

- **The regime band:** what it permits Book A, from the close payload's
  read-only `enforcement_block`.
- **The book's position:** its net beta against the band's midpoint, which gives
  "cautious", "leaning in" or "at the midpoint".
- **Three observables:** the first three what-would-change items from 2.1(d).

**2.6 Collapse by default, expand in reference.**

- **Silent and unreachable voices** become one line ("Voices: 14 silent, 2
  unreachable."); their rows move to the reference tables.
- **A family of prediction-market resolutions** on one day in Ahead becomes one
  row: "N outcomes; modal: <outcome>", with its probability. The family is the
  question with its strike removed. Every outcome moves to the reference tables.
- **An exception that restates a five-year extreme of a series the tape prints**
  becomes one line, "<label> -- the tape prints it.". The tape's series come
  from the tape config's `daily` and `fallback` keys.
- **The terms box** prints verbatim in full every week as page 2: after the
  précis, before section 1, with a print page break before it.
- **The reference tables** print after the last section, under "Detail tables".

**2.7 Tape and mechanics de-duplicated.**

- The week by day moves from The read, and the SPY overnight split from the
  tape, into Mechanics. They are the only daily session tables.
- The tape's named-levels table moves to the reference tables.
- These moves are layout only and run after the prose. The read's frame and the
  consistency gate's tags still see the tables where they were built.

**2.8 Presentation.**

- **One-line chart titles.** The Weekly's small multiples (W3, W4, W8, W9, W10)
  have one-line titles; each panel is titled by its series, and the span and
  dates move to the caption.
- **Every table row carries its unit.** The tape's Last prices print with the
  tape config's new `unit` ("$668.40", "98.10 index"). The RTAT10 row names its
  score, the WallStreetBets row its count, and a small TIC figure its dollar
  sign. `storyline.unitless_rows` finds none on the fixture.
- **The named-levels rule** is unchanged: at most three levels, per T3.4b.

**The gate.** `tools/validate_weekly_storyline.py` (30 checks) runs on the
Weekly's fixture payload with a scripted writer. It covers every item the brief
lists:

- the précis comes after the sections and opens the edition;
- its figures are within the sections' cited set, a draft citing another is
  withheld and the retry publishes;
- six verdicts, the confidence line, 3–4 items each with a series and a window,
  the outlook line both ways;
- the stance in the dry-run ledger, with `weekly_stance` and the horizon, and
  graded by Brier;
- a relevance sentence at the head of every present commentary;
- every contradiction's status, with resolved, stale and carried each reached;
- the terms line, and the terms box verbatim;
- the three collapses;
- the daily table in Mechanics only;
- no two-line titles, and units on every row.

Gates updated to the new layout: `validate_weekly_integrity` ($ prices),
`validate_weekly_edits` (the week by day and levels moved; W8's span in its
caption), and `validate_weekly_complete` (the overnight split in Mechanics). The
Makefile carries the new gate, and CLAUDE.md now reads fifty-two code gates.

## Choices made for the operator to overrule

- **2.3 is the second design**, the précis emitting the relevance sentences.
  The two-pass loop would add a third model call per section-frame change, and
  it would hand the sections a tension written before any section existed. The
  second design ties each section to the tension the précis actually found.
- **The verdict directions:**
  - rates: the 10-year yield;
  - credit: high-yield spreads, so "up" is wider;
  - the dollar: DXY;
  - commodities: oil and gold;
  - volatility: the VIX.

  "Chop" is range-bound; "transition" is a regime change.
- **The précis has its own audit, not the payload numeral audit.** The allowed
  set is figures only; dates do not count as figures, and a CHANGE window must
  name a weekday, a month, an ISO date or "this week / by / before / through /
  until / next".
- **Matching is lenient on the plus sign.** A cited figure matches its allowed
  form with the "+" and the spacing ignored ("25 bp" matches "+25 bp").
- **The dry-run namespace is a source prefix**, `dryrun.weekly_stance`, in the
  same ledger database. The live count and the live Brier never read it.
- **The stance resolves on yfinance's SPY daily close.** Equal resolves 0
  ("higher" is the claim).
- **"Stale" is 20 sessions open and not widening**, a session-set threshold in
  config.
- **The resolved-by map** names the section and the rows that answer each gap.
  There are three entries, from the 9 Oct lesson, and the map is
  session-set.
- **The modal outcome of a family is its highest-probability row**, W-1.1's rule
  for Ahead's frame. For a ladder of "above X" contracts that is the lowest
  strike.
- **The tape's levels table** is the reference tier's first table. The tape's
  read path keeps prices, moves, the trend columns and breadth.
- **The terms box sits before section 1** as page 2. The print CSS breaks before
  it; email shows it inline.

## Needs you

1. **Keep the second design for 2.3** (the précis writes the relevance
   sentences) rather than a tension draft before the sections? Yes / no.
2. **Keep the six verdict directions as defined?** Credit "up" means wider
   spreads, and rates "up" means a higher 10-year yield. Yes / no.
3. **Keep the dry-run stance as a source namespace in the same ledger,** rather
   than a separate dry-run ledger file? Yes / no.
4. **Keep "stale" at 20 sessions open and not widening?** Yes / no.
5. **Keep the modal outcome of a resolution family as its likeliest row?** The
   alternative is the median strike of a ladder. Yes / no.
