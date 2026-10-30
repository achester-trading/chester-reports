# A90 notes: the Monthly's binding after dry run #2 (with A91)

**Branch.** `a90-monthly-dryrun-2`, from origin/main at `422ea697` (A88 and B84
merged).

**Merge timing.** Ruled 29 Oct 2026 20:20 ET (D42.8): this branch does NOT merge
before the 1 Nov Monthly, which runs on main as it is. It merges next week.

**What A91 added.** A91 finished it on the branch: this note, one fixture
expectation, and the gates A90 could not finish before its 19:30 ET stop.

**Sources.** The evidence is the two dry-run logs, which are outside the repo and
never committed:

- dry run #1, 28 Oct, 41 of 61 published;
- dry run #2, 29 Oct, main at 422ea697, 48 of 61 published.

## The sections dry run #2 withheld

Classes: **(i)** a false positive in the check; **(ii)** the draft is wrong and the
check right; **(iii)** the retry message does not name the fix.

| Section | Class | Cause | Fix |
|---|---|---|---|
| theme:liquidity_plumbing | (i), A88's binding | "Net liquidity, the Fed balance sheet less reverse repo and Treasury cash, closed September at $5.78tn": the figure's clause names nothing, and the fallback took the name inside the comma-set appositive. A label printed twice also hid A88's derived names. | Bare-subject rule; uniqueness by series |
| theme:fed_path | (i) | "the 10-year breakeven" named no row ("10-year breakeven inflation"), and a row whose alias is the noise word "level" took "an index level of 130.9" | Last-word-less form; noise-word aliases dropped. Draft 2 now passes; draft 1 also fails on a unit and on bare "the 10-year" |
| theme:equity_positioning | (i), A88's binding | "the equal-weight measure" against "Equal-weight against cap-weight S&P 500" | The head also ends at against, versus, vs |
| theme:sentiment | (i), left alone | Paraphrases: "the Michigan 5-10 year gauge", "the NY Fed's 3-year consumer measure", "NVDA forum mentions" | None. No narrow rule names these. The unnamed-subject rule unbinds some figures; the section still fails on others |
| theme:geopolitics_reserve | (i) A88 and (ii) | Draft 1: A88's derived "Gold" (from "Gold, COMEX front-month future") catches "SAFE-reported gold holdings". Draft 2 prints "4186.7" without separators, which is a true (ii). | None (doubtful) |
| pillar:2 | (i) | "the 30-year Treasury" named no row; "a 7.03% mortgage rate" names its series after the figure | Last-word-less form; the attributive rule. Draft 2 now passes; draft 1 also has unsigned changes |
| stack:narratives | (ii) | Draft 1 cites percentile ordinals not in its slice; draft 2 names "the credit dimension" (internal vocabulary) | None |
| block:plumbing:yields | (i), outside these files | The direction audit pairs "the long end backed up / firmed" with 2s10s's fall; the long end did rise | None. `daily_cascade/direction.py` is not in this paste's files; listed |
| block:plumbing:global | (ii) | "the dollar firmer against all three" while USD/JPY fell 0.83% (the yen firmed) | None |
| block:slow:metals | unknown | "down 10.83 percent" is matched by no row in the block. A synthetic block passes; the real one cannot be seen from the laptop | None (needs the box's payload) |
| summary:tape | (ii) | It writes 40-week averages as closes (4,554.56, 277.22, 99.35). The binding withheld it for the wrong reason ("(DXY)" lost to "dollar index"). | With the tag rule the binding passes it and the role audit withholds it. The tape rules run only once the numeral audit passes (`monthly_macro/prose.py`), so the right check now does it; fixture group L holds both halves |
| summary:mechanics | (i), A88's binding | Draft 2: a comma inside "Implied correlation, 1 month (Cboe COR1M)" split the clause. Draft 1: the lone tag "(Cboe COR1M)" was demoted as if it were a qualifying bracket. | The comma-in-name rule; the lone-tag rule |
| summary:slow | (i), A88's binding | "PRL fees, 30 days" appears twice in the block, so A88 counted "PRL fees" as shared, and the "PRL" price row took the figure | Uniqueness counted by series |

**The seven that published on 28 Oct** (fed_path, equity_positioning, sentiment,
block:plumbing:global, block:slow:metals, summary:tape, summary:mechanics) cannot
be replayed as published drafts. The logs carry only withheld drafts.

## The rules A90 added (`altdata/numeral_audit.py`, `series_bindings` and its derivation)

1. **Uniqueness by series.** A derived name is unique when one SERIES (one label)
   carries it, however many times the block prints that label. The prose audit's
   payload is the slice plus every edition section, so labels repeat. This is
   also why A88's derived names were often inert on the box.
2. **Noise-word aliases.** A row alias that is only a noise word ("level") is no
   name.
3. **Head cut.** A label's head also ends at "against", "versus" or "vs".
4. **Last-word-less form.** A label of three or more words also goes by itself
   less its last word ("10-year breakeven", "30-year Treasury", "Brent crude").
5. **Comma inside a name.** It does not end a clause.
6. **Lone tag.** A bracket holding only a name is a tag naming the series, not a
   qualifier to step over.
7. **Attributive figure.** After "a" or "an", the name straight after a figure is
   its own ("a 7.03% mortgage rate").
8. **Bare subject.** A sentence opening on a bare name set off by a comma has that
   name for its subject; the appositive after it does not.
9. **THE UNNAMED SUBJECT.** A name before a figure does not bind it when, between
   the name and the figure, a bare tenor ("the 10-year") or a capitalised
   ticker-like word of three to five letters stands that matches no row ("WTI",
   "PCE"). The figure is then left to the plain match.

   This rule removed the three wrong bindings the others had created:
   - WTI's figures bound to Brent;
   - "the 10-year rose ... to 5.29%" bound to the 2-year;
   - core PCE's change bound to core CPI.

## The replay (uncommitted; it needs the logs)

**What it covers.** The 88 drafts the two logs carry in full, all withheld (52 and
36). Published drafts are not logged.

**How it works.** No payload exists on the laptop, so it compares which row each
bindable figure binds to under main's `numeral_audit.py` and under this branch's.
Rows are each section's real labels:
- pillars: `altdata/config.py`;
- themes: `config/monthly_themes.yaml`;
- other sections: the names the logs report.

**What it found.**

- **61 drafts bind identically**, so their verdict cannot change.
- **27 drafts have changed bindings.** Every change binds to the series the
  sentence names, or unbinds a figure main had bound to the wrong row. No
  binding changed to a wrong row.
- **Six sections newly pass** (their withheld drafts' only failures were
  bindings this branch fixes): liquidity_plumbing, fed_path (draft 2),
  equity_positioning, pillar:2 (draft 2), summary:slow, summary:mechanics.
- **Zero sections newly fail.**

**Fixtures.** `tests/fixtures/monthly_dryrun_2026-10-29.json`, run by
`validate_audit_fixes.py` group L:

- 11 logged cases pass and 10 must-fail cases fail;
- summary:tape passes the binding and is withheld by the role audit.

On main, 2 of the 11 pass and 5 of the 10 must-fail cases fail.

## Risk

**What the rule does.** Rule 9 leaves a figure to the plain match (the figure
need only exist somewhere in the payload) when an unnamed subject stands between
the nearest name and the figure.

**What a wrong figure would need to pass under it.** All three of these:

1. it sits after a bare tenor or a capitalised word naming no row;
2. it belongs to some other row in the block;
3. that row is not the one the unnamed subject means.

Example: "Brent crude surged ..., WTI rose +29.15%", where +29.15% is Brent's,
not WTI's.

**What it does not change.**

- A figure in its own clause with its own name binds exactly as before.
- A figure in no row fails the plain match as before.

**The guards.** Group L's must-fail cases show the rule does not fire without the
unnamed word:

- "Brent crude surged +11.66% to 97.18" still fails, bound to Brent;
- "Core CPI climbed +0.32%" still fails, bound to core CPI.

The A88 group K case "Nonfarm payrolls rose to 7.08 million" holds the same for a
derived name.

**The cost.** The rule trades a false positive, a correct sentence withheld, for
this narrower false negative: a figure misattributed only across an unnamed
subject.

## A91: the one fixture expectation

**The failure on main.** Main's CI run 40933353930 (422ea697) fails one gate,
`validate_audit_fixes.py`. A clean checkout of 422ea697 shows the same: 135
passed, 1 failed, on

> B84: looking_ahead's calendar ('closes the quarter ... on the 1st ... the 4th')
> passes the Monthly's role check; the role audit alone still binds the ordinals
> (its rule is unchanged)

**Why it failed.** A88 made the role audit's span end at a colon and skip a
date's numerals, so the role audit alone no longer binds those ordinals. B84's
mask in the Monthly's wiring is now belt and braces.

**The change.** The expectation now reads: the calendar passes the Monthly's role
check AND the role audit alone. A must-still-fail case sits beside it: "SPY
closed the month at 721.82." against the same fixture's 40-week average is
withheld. The audit is unchanged.

## Gates (A91, one at a time, foreground, laptop)

- `validate_audit_fixes.py`: 158/0 (group L included).
- `validate_readability.py`: 67/0.
- `validate_prediction_markets.py`: 52/0.
- `validate_stack.py`: 45 passed, 0 failed when the 10-minute foreground limit
  stopped it, in group E. Its alias case (group B) passed. CI runs it whole.
- From A90, before its stop:
  - `validate_numeral_audit.py`: 172/0;
  - `validate_monthly.py`: 360/0, 1 skipped;
  - `validate_monthly_frames.py`: 39/0.
