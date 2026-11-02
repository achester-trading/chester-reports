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

## A111 (2 Nov 2026): the first edition's six binding sections

**Base.** `origin/a90-monthly-dryrun-2` at `f8819b62`. A95's branch is not merged
in. Its replay table (`docs/briefs/a95-notes.md` on `a95-monthly-first-edition`)
was read for the combined count.

**The evidence.** The 1 Nov run log, on the laptop, outside the repo, as A95
read it.

- The edition's data blocks are on the box, so each section was rebuilt:
  - its rows' real labels: themes from `config/monthly_themes.yaml`, pillar 1
    from `altdata/config.py`, the plumbing blocks from
    `weekly_sections.plumbing_rows`, and summary:priced from the log's own names;
  - each row holding the values its draft quotes.
- Run through main's audit (`422ea697`), the rebuilt blocks reproduce every
  message the log printed for the six sections, word for word.
- The script is `scratchpad/a111_six.py`, uncommitted because it needs the log.

### The six sections

| Section | The sentence | Figure | Bound to (main) | Belongs to | On A90's tip | Class | The fix |
|---|---|---|---|---|---|---|---|
| block:plumbing:liquidity | "Net liquidity at $5.75tn fell −$24bn in October against bank reserves at $2.89tn" | $5.75tn | H.4.1 (bank reserves, after the figure in its clause: main knew "Net liquidity" only as a derived name the table row and the data row shared) | Net liquidity (Fed balance sheet less TGA and RRP) | **passes** (A90: a derived name unique to one series binds even when printed twice) | (i) | none needed here |
| summary:priced | "the base rate for a cut at the 17 March 2027 FOMC meeting fell −4.5 pts" | −4.5 | Yes (the recession rows' bracket name, the nearest name before, in another clause) | FOMC 2027-03-17: cut | **passes** (A90 rule 9: "FOMC" stands between, naming no row, so the figure goes to the plain match) | (i) | none needed here. **Not an unplaced figure:** the row holds it |
| block:plumbing:metals | "while gold-over-copper fell −5.43% to 604" | −5.43% | Copper, front future ($/lb; a growth gauge), the sentence's first name | Gold over copper (rises when growth fears rise) | fails | (i) | **A phrase's words may be joined by hyphens** (`_alias_rx`) |
| theme:geopolitics_reserve | "China's gold holdings rose by 740,000 ounces to 77.47 million ounces" | 77.47 million | GC=F, through its derived name "gold" | China's official gold holdings (SAFE) | fails | (i) | **A name of four or more words also goes by itself without one inner word**, unique to one series ("China's gold holdings"). **Not an unplaced figure:** the SAFE row holds it |
| pillar:1 | "even as the ranks of those unemployed 27 weeks or longer grew by +14,000 people to 1.94 million" | 1.94 million | Initial claims, 4-week avg, the nearest name before, in another clause | Unemployed 27+ weeks | fails | (i) | **"27+ weeks" also goes by "27 weeks"** |
| theme:sentiment | "the Michigan 5-10 year measure rose +10 bp to 3.5%" | +10, 3.5% (both drafts) | University of Michigan consumer sentiment, the nearest name before, across the colon | Michigan 5-10 year inflation expectations | fails (the NY Fed's +6.3 and 3.25% pass there, by rule 9's tenor) | (i) | **A name also goes by its words up to its tenor**, a word before it at least ("Michigan 5-10 year") |

**The pattern A95 named in the plumbing block** was in the matcher, not the
data block. The writer was given net liquidity under its own name, with its
display string.

**One retry message improved, (iii).** "77.47 million is bound to SAFE but
belongs to SAFE" named neither series: the two SAFE rows share the bracket's
short name. Where another series goes by the same short name, the message now
gives each row's whole label ("bound to China's foreign-exchange reserves
(SAFE) but belongs to China's official gold holdings (SAFE)"). Message only; no
verdict changes.

**What did not change.**

- Every new name binds only where it is unique to one series, as A88's
  derived names do.
- No check was loosened. A figure bound to its own row is checked against that
  row, value and kind, as before.
- The writer's data blocks (`monthly_macro/stack.py`, `prose.py`) are
  unchanged: no class (ii) was found among the six.
- **Sentiment and pillar 1 still need A95.** On this branch alone their figures
  bind to the right rows, but:
  - 3.5% and 3.25% (and pillar 1's 4.2%, 61.8% and 59.2%) still fail the
    percent type, because a "%" row reaches the writer as `latest_level`. A95's
    `latest_pct` fixes that.
  - Sentiment's 99 and 19 need A95's sign rule.
  - Checked: those figures fail the same way on A90's tip, bound or not.

### The fixtures

`tests/fixtures/monthly_binding_2026-11-01.json`, run by
`validate_audit_fixes.py` group M:

- 4 must-pass cases, each a logged sentence over its rebuilt block;
- 8 must-fail cases beside them:
  - copper given gold over copper's change, and the reverse through the
    hyphenated name;
  - the gold future given China's holdings, and China's reserves given them;
  - initial claims given the long-term unemployed's level, and the reverse;
  - Michigan sentiment given its expectations;
  - the Michigan 5-10 year measure given the NY Fed's figures;
- the message check.

On A90's tip, 0 of the 4 pass, and 3 of the 8 must-fail cases pass because the
names they use are not recognised there. On this branch all 4 pass and all 8
fail.

### The replay

`scratchpad/a111_replay.py`, uncommitted (it needs the log). A90's method: each
bindable figure's row under main, A90's tip and this branch, with rows in the
sections' real labels.

- **43 drafts** in the log.
- **23 bind identically** under all three.
- **11 have changed bindings against A90's tip** (20 against main).
- **Sections that newly pass:**
  - against A90's tip: block:plumbing:metals and theme:geopolitics_reserve, both
    drafts;
  - against main, this branch with A90's work: also block:plumbing:liquidity
    and summary:priced, both drafts.
- **0 newly fail.**

**Every changed binding, against A90's tip** (A90 → this branch). Each now
binds to the series its sentence names:

- theme:sentiment: +10 and 3.5% (draft 1), and 3.5 percent (draft 2):
  University of Michigan consumer sentiment → Michigan 5-10 year inflation
  expectations;
- theme:sentiment, both drafts: 0.02 and 2.48 (unbound → SPY short interest,
  days to cover), "SPY short-interest days-to-cover rose by 0.02 to 2.48";
- theme:geopolitics_reserve, both drafts: 77.47 million, GC=F → China's
  official gold holdings (SAFE);
- pillar:1, both drafts: 1.94 million, Initial claims → Unemployed 27+ weeks;
- block:plumbing:metals, both drafts: −5.43%, Copper → Gold over copper;
- theme:fiscal_dollar, both drafts: −22.1 and 0.66% (unbound → 10-year term
  premium (NY Fed ACM model)), "the NY Fed's term-premium estimate fell ...,
  down −22.1 bp to 0.66%";
- theme:equity_positioning, draft 1: +0.02 and 0.29, S&P 500 → Equal-weight
  against cap-weight S&P 500, "The equal-weight-against-cap-weight S&P 500
  reading ticked up +0.02 to 0.29".

**The newly bound figures could newly fail on kind.** 0.66% and 3.5% are now
bound to their own rows. Over those rows as this base hands them over (a "%"
level as `latest_level`, typed a price), both fail. A90's tip fails them the
same way, through the plain match's percent check ("written as percent but the
payload carries this value as ['price']"). So no verdict changes, and A95's
`latest_pct` cures both.

### The combined count

The 16 sections the edition withheld, judged per figure on the logged drafts
under A95's branch, A90's tip and this branch together. **11 publish from a
logged draft:**

| Section | Whose fix |
|---|---|
| theme:liquidity_plumbing | A90 |
| pillar:7 | A90 |
| block:plumbing:liquidity | A90 |
| summary:priced | A90 |
| theme:fed_path (draft 1) | A95 |
| stack:positioning (draft 2) | A95 |
| block:slow:metals | A95 |
| block:plumbing:metals | A111 |
| theme:geopolitics_reserve | A111 |
| theme:sentiment (draft 1) | A95 for 99, 19 and the two percents; A90 for the NY Fed's; A111 for Michigan's |
| pillar:1 (draft 1) | A95 for the three percents; A111 for 1.94 million |

The five others are class (ii): the drafts are wrong. A95's fixes to the writer
and the retry act in the next run, not on these drafts:

- month_in_markets;
- theme:fiscal_dollar;
- stack:misfit;
- stack:priced;
- block:plumbing:yields.

pillar:1's draft 1 is cut at "argue against compl" in the log. Its figures are
all before the cut.

### Gates (one at a time)

| Gate | Tally |
|---|---|
| `validate_numeral_audit.py` | passed |
| `validate_audit_fixes.py` | 171 passed, 0 failed (group M included) |
| `validate_monthly.py` | 359 passed, 1 failed, 1 skipped |
| `validate_monthly_frames.py` | passed |
| `validate_monthly_stack.py` | 267 passed, 0 failed (whole, 537 s; the first 590 s run hit its cap) |

**The one `validate_monthly` failure is the date drift B101 and B101b fixed on
b101.** It is the refunding window ({'November': True, 'December–January':
False}), and it fails the same on A90's untouched tip, 359/1/1. It started with
November. b101 merges at step 0 of the merge week.

B97's `--group` flag is not on this base, so `validate_monthly_stack` ran whole.
