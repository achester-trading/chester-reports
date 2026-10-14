# W-1.3c — the Weekly polish from dry run #6 (session A, 14 Oct 2026)

Dry run #6 ran at 22:34 ET on 13 Oct (run `weekly-20261014T023429`, week ending
9 Oct). Eight of its ten sections printed commentary. This branch fixes the ten
things that run showed.

- **Branch:** `w-1-3c-weekly-polish`, cut from `main` at `cc91752`.
- **Status:** branch-only. Pushed and not merged. Nothing was deployed, and
  nothing ran on the box.
- **CI:**
  - **#376** on `11bfc0f` failed one check in `validate_stack_cadence`. It was
    fixed in `ecd3efc`; see "Found that the paste did not name", item 8.
  - **#377** on `ecd3efc` was still running when this file was committed; its
    result is in the session report.
  - Item 10's WeasyPrint page check runs only in CI.
- **Friday:** see part 3 below.

**The fixtures.** Every fixture quotes the run's own text. The text came from
the run's PDF (`weekly_tactical_2026-10-09 (1).pdf`, 13 Oct 22:42) and lives in
one new file, `tests/fixtures/weekly_run6_2026-10-13.json`. It holds:

- Plumbing's change column;
- the eight self-naming first sentences;
- the five dealer-gamma explainers;
- The read's opener;
- the précis;
- the subject line;
- the Ahead's withhold message;
- the candidate line.

The précis sentence about the book's own return had real figures. Words
replace them, so the repo carries no real position figures. Everything else is
verbatim.

**No new gate file.** The fixtures extend five existing gates:

- `validate_audit_fixes`, groups H and I;
- `validate_numeral_audit`, group L;
- `validate_weekly_opener`, group F;
- `validate_readability`, groups G and J;
- `validate_weekly_calendar`, group A.

**Fixture before code, shown afterwards.** The new gate files and the fixture
were copied onto a detached worktree of `cc91752`, the code before this branch,
and run there. They fail for the reasons dry run #6 showed:

- **`validate_audit_fixes`:** 10 failures, starting with run 6's own message:
  `'fell −$1bn the same day.': 'fell' with a rise`. Then a TypeError: the old
  `retry_prompt` takes no attempt count.
- **`validate_numeral_audit`:** an ImportError, because `ordinal` does not exist
  on main.
- **The other three:** `validate_weekly_opener` stops at `opener.terms_faults` (AttributeError); `validate_weekly_calendar` fails 4 (MSFT and GOOGL print "session not stated", `earnings_session`, the source's `release_at`); `validate_readability` fails the three-attempt check and stops at `precis.subject_claim` (AttributeError). On base Edge also reproduces item 10 (below).

## The ten

### 1. A sign before a currency symbol

**Cause.** Run 6 withheld Plumbing on `'fell −$1bn the same day.': 'fell' with
a rise`. The direction audit's figure pattern had no place for a currency
symbol between the sign and the digits. So it read a bare `1`. That matched the
`+1 bp` row (Japan 30-year), and the audit called "fell" a rise.

**The fix: three parsers now read a sign in front of `$ € £ ¥`** (a hyphen or
U+2212), with the magnitude suffix:

- **The direction audit** (`direction._NUM`) scales `bn`/`tn`/`m`/`k`, then
  compares against the table's value in the same currency.
- **The numeral audit** (`numeral_audit._FIGURE`) also reads a plus, kept
  positive.
- **The shared cell parser and figure counter** (`figure_budget.parse_figure`
  and `readability._FIG`). A currency is its own unit, so "−€1bn" is never a
  dollar.

**Fixtures** (validate_audit_fixes H, validate_numeral_audit L):

- "fell −$1bn" passes against run 6's own rows, and with a hyphen too.
- "rose −$1bn" fails.
- "+$82bn" reads as a rise: "rose" passes and "fell" fails.
- The euro, pound and yen signs read alike.
- Through the pipeline, run 6's clause publishes on the first attempt.

### 2. No re-explaining the terms box

**What was wrong.** The opener frame's worked example was itself a definition
of dealer gamma. Five sections copied it: The read, the tape, Mechanics,
Positioning and What's priced.

**The fix.** Two parts:

- **The frame.** The example now opens on a finding and explains why it
  matters. The frame names every term the box defines (`precis.TERM_NAMES`) and
  says never to define one again.
- **The gate.** `opener.terms_faults` compares each opener sentence with each
  entry in the terms box. An entry is one of its sentences or semicolon
  clauses. The comparison counts shared content words (stop words dropped,
  crude stem).

**The threshold, from the run-6 text:**

| Sentences | Stems shared with the box | Overlap |
|---|---|---|
| Run 6's five explainers | 7 to 11 | 0.29 to 0.48 |
| Run 6's other opener sentences | at most 4 | at most 0.20 |

So a sentence fails at **five or more shared stems and an overlap of 0.25 or
more**.

**Where it runs:**

- every section's text, on a cadence with an opener;
- the précis's relevance sentences.

**Fixtures** (validate_weekly_opener F):

- Run 6's read opener and all five explainers fail.
- An opener on the same week that explains its own finding passes.
- A draft that re-explains is withheld. Its retry is told the reason and the
  terms rule, and publishes.

### 3. The subject line

**The new rule, in order:**

1. On an edition with a précis, the subject is the précis's Takeaway without
   its label.
2. With no précis Takeaway, the stance line.
3. With neither, just "Weekly — w/e …".
4. Never an opener sentence.

The Takeaway is trimmed at a word boundary to the existing
`SUBJECT_CLAIM_CHARS`, which is 90. The close has no précis and keeps The
read's claim.

**On run 6** the subject becomes "Weekly — w/e 9 Oct — A market this narrow,
this undefended by rates or credit, and this quiet in realized…". It was the
dealer-gamma definition.

**Fixture:** validate_readability G.

### 4. No bold on the explainer

`stack_render.opener_html` prints the claim at the paragraph's weight, as a
`<span class="claim">`. The Markdown edition no longer wraps an opener's claim
in `**`.

**Fixture** (validate_weekly_opener F): in the rendered Weekly, the only bold
run inside any opener is "Takeaway:". That is 9 bold runs over 9 openers, plus
the Markdown edition.

The stance line under the précis is still bold. It is not an opener.

### 5. The finding first

**Where run 6's self-naming sentences came from.** All eight are the précis's
RELEVANCE sentences, which print first in each opener. The frame had asked for
"one sentence tying {title} to the tension". So the gate runs in two places:

- **in the précis's audit**, on each RELEVANCE sentence;
- **in the section audit**, on the writer's first sentence.

**The rule** (`opener.self_subject`) withholds a first sentence that:

- starts with a section name as printed, or with "This section" or "The
  section", possibly possessive ("The book's shortfall…");
- then has a reporting verb within twelve words, with no comma, colon,
  semicolon or dash in between. The verbs include shows, frames, locates,
  names, describes, notes, tracks, highlights and pinpoints.

**The frames now say the first sentence is the finding:** the opener frame,
the précis's RELEVANCE line, and the WEEK line.

**Fixtures** (validate_weekly_opener F):

- All eight run-6 sentences fail. The paste listed seven; What doesn't fit's
  "names…" is the eighth.
- The précis audit flags 8 of 8.
- Sentences about markets pass, even ones that name a section later.
- The pipeline withholds a self-naming Narratives draft and retries it with the
  reason and the rule, and it publishes.

### 6. Retries carry the reason

**Cause.** The Ahead's retries never heard why they were withheld. The
withhold message kept only its first four faults. `retry_prompt` then cut it
to 600 characters. The opener's faults come late in the list, after style,
budget and filler.

**The fix:**

- `opener.retry_note` feeds back the whole message (`retry_reason`, every
  fault). The edition's printed withhold line still keeps four.
- It adds the rule behind each kind of fault (`opener.RULES`): opener shape,
  the Takeaway, numeral, direction, filler, figure budget, terms, finding
  first, and the tension first.
- The section writer and the précis both use it.

**Attempts:**

| Writer | Before | Now |
|---|---|---|
| Weekly sections | 2 | 3 (`prose_attempts: 3` under `cadences.weekly`) |
| The précis | 2 | 3 (`precis.ATTEMPTS`) |
| The close | 2 | 2, no key |
| The Monthly | its own three | unchanged (`monthly_macro/prose.py`) |

**Fixtures:**

- **validate_audit_fixes I:**
  - A fake model that obeys the reason on attempt 2 publishes in 2 attempts.
  - One that never obeys is withheld after 3.
  - A fifth fault (run 6's Ahead Takeaway) reaches the retry whole, with the
    Takeaway, filler, budget and direction rules.
  - A numeral-audit withhold carries the numeral rule.
- **validate_weekly_opener F:** the précis retries with the tension-first rule
  and publishes on attempt 2.

### 7. Ordinals by code

**The helper.** `altdata.numeral_audit.ordinal()` rounds half up and is used
everywhere: 1st 2nd 3rd 11th 12th 13th 21st 92nd 103rd.
`percentile_ordinal` now delegates to it.

**Every hand-formatted ordinal now goes through it:**

- **the scanner's candidate line**, `book_b_scanner` RS: "RS 92th" is now
  "RS 92nd";
- **the auction table**: `weekly_sections._with_pct`. It used `int(p)`, which
  truncated, so 88.7 printed as 88th and now prints as 89th;
- **the VIX row**;
- **What doesn't fit's extremes**;
- **the Monthly's M5 chart**, labels and caption;
- **`tools/expression_check`**.

**Fixtures** (validate_numeral_audit L):

- the list above;
- half-up rounding;
- the scanner's own `confirm()` prints "RS 92nd percentile";
- a sweep finds no f-string writing a suffix by hand in `daily_cascade/`,
  `altdata/` or `monthly_macro/`.

### 8. The précis leads with the tension

**The frame.** The WEEK line asks for the first sentence to state the tension
in words, with at most one figure. The two or three figures that carry it
follow. The 150–250 word band is unchanged.

**The audit.** `precis.audit` withholds a first sentence with more than one
figure (`WEEK_FIRST_FIGURES = 1`), naming the sentence.

**Fixtures** (validate_weekly_opener F):

- Run 6's précis opened "SPY rose 1.16% this week and broke its gamma flip at
  775.54…", 9 figures. It fails.
- A tension-first rewrite of the same week passes, at 159 words.

### 9. Earnings timing

**Rendering.** Where the stored event has no release time, the Ahead now
prints "release time not captured" instead of "session not stated". Where it
has one, it prints pre-market, post-market or "during the session"
(`weekly_sections.earnings_session`, constant `RELEASE_NOT_CAPTURED`).

**The source, which this paste did not ask for.** The calendar route stores a
bare date. But yfinance's `get_earnings_dates` carries the unreported row's
timestamp. `earnings.events_for` now stores that timestamp beside the date as
`release_at`, when the forward date matches and the time is not midnight. The
Ahead prefers it over the date.

**Fixtures** (validate_weekly_calendar A):

- **MSFT**, a bare date: prints "release time not captured".
- **GOOGL**, a bare date with a stored 06:30 ET release time: prints
  pre-market.
- **`earnings_session` directly**, across the cases.
- **A fake yfinance:** stores `release_at` when the source has a time, and none
  when it does not.

### 10. The stance stays on page 1

**The fix:**

- The terms box no longer forces a page break before itself. It is kept whole
  (`break-inside: avoid`).
- The stance line prints directly under "What changed in the outlook", ahead of
  the outlook text.
- The six verdicts are a three-column grid instead of a six-line list.
- "What would change our mind" is three compact lines.
- The précis's headings carry ids (`verdicts`, `change`, `outlook`, `stance`)
  so WeasyPrint can say which page each landed on.

**Fixtures:**

- **validate_weekly_opener F (structure):** no break between the précis and the
  terms box, and the stance comes directly after the outlook heading, after the
  verdicts and the change lines.
- **validate_readability J (the PDF):** renders the head of run 6's Weekly
  through WeasyPrint. That is the header with its three changed-since lines,
  run 6's précis, the terms box and an opener. It checks that page 1's anchors
  include the précis, the verdicts, the change lines, the outlook and the
  stance. **It runs where WeasyPrint is installed: CI and the box.**

**This laptop cannot run WeasyPrint** (no GTK), so the check prints NOT
VALIDATED here. As a stand-in, the same page was printed with headless Edge
(Chromium, Letter, the print CSS):

| Code | Pages | Page 1 | Page 2 | Page 3 |
|---|---|---|---|---|
| Base `cc91752` | 3 | the précis through what would change our mind | the outlook and the stance, alone | the terms box |
| This branch | 2 | the précis, verdicts, change lines, outlook heading, the stance and the outlook text | the terms box | — |

The base render reproduces the run-6 fault. Chromium is not WeasyPrint, so CI
gives the binding answer.

## Gates

**Run locally:** the affected gates, not the full suite. CI is the full suite.

**Baseline.** The twelve below were first run at `cc91752` in a detached
worktree. All passed.

| Gate | On this branch |
|---|---|
| validate_numeral_audit | 167 passed, 0 failed |
| validate_readability | pass, 0 failed |
| validate_no_filler | pass, 0 failed |
| validate_figure_budget | pass, 0 failed |
| validate_weekly_opener | 46 passed, 0 failed |
| validate_weekly_stack | pass, 0 failed |
| validate_weekly_integrity | pass, 0 failed |
| validate_audit_fixes | 73 passed, 0 failed |
| validate_weekly_storyline | pass, 0 failed |
| validate_weekly_calendar | pass, 0 failed |
| validate_weekly_edits | pass, 0 failed |
| validate_book_b_scanner | pass, 0 failed |
| validate_monthly_stack | pass, 0 failed |
| validate_stack (the close) | pass, 0 failed |

`validate_readability` needed two fixture updates, both consequences of the
spec:

- The Read-duplicate check now counts three attempts.
- The Weekly subject check expects the précis Takeaway, not The read's claim.

The direction gate is the direction groups of `validate_audit_fixes` and
`validate_weekly_edits`; there is no separate file.

## Part 3 — where it goes on Friday

**Both orders merge without a conflict, and they end on the same tree.** The
proof ran on throwaway local branches `p3-a` and `p3-b`, never pushed and
deleted afterwards. Each step was a `git merge --no-ff` of the `origin/` tip, in
Friday's order (aq-5-correlation-layer → … → el-2-3-rollup):

- **(a) main `cc91752`, then this branch, then the 23:** all 24 merges clean.
- **(b) main, then the 23, then this branch:** all 24 merges clean.
- **The two final trees are identical:** `7ed861b`.

**But a clean merge is not a green one.** The affected gates were then run on
the merged tree, plus `validate_quarterly_stack` and `validate_batch3_a`.

- **Every gate passed except one:** `validate_numeral_audit` failed 1 check. It
  was item 7's sweep: no f-string writes an ordinal suffix by hand.
- **The culprit:** AQ-1 (`aq-1-quarterly-cadence`, seventh in Friday's order)
  brings `monthly_macro/quarterly.py:197`, written
  `f"{t['percentile']:.0f}th percentile"`. That prints "92th", "1th" and so on in
  the Quarterly's correlation table. It is the same defect as item 7, in code
  this branch cannot see.
- **The fix, proved on the merged tree** (local only): two lines in
  `monthly_macro/quarterly.py`. With it, `validate_numeral_audit`,
  `validate_quarterly_stack` and `validate_quarterly_gates` all pass.

  ```diff
  +from altdata.numeral_audit import ordinal
  ...
  -                         (f"{t['percentile']:.0f}th percentile"
  +                         (f"{ordinal(t['percentile'])} percentile"
  ```

**What the order changes:**

- **Under (a)**, the numeral gate is red on main from AQ-1's merge (the
  seventh) until the fix lands. Either 17 merges stay red, or the fix goes in
  mid-sequence, which the stitching notes' rule 5 forbids ("nothing else onto
  main").
- **Under (b)**, main stays green through all 23. Only this branch's merge goes
  red, and the two-line fix follows in the same step.

**Recommendation: (b). This branch merges last on Friday, then the two-line
quarterly fix as its own commit.**

That departs from the paste's rule, which says that if (a) is clean, this
branch goes first. (a) is clean only textually. Sunday's Weekly gets this branch
either way, because Friday's merges all land before Sunday. Your call: needs-you
6.

Nothing was resolved on this branch. There was no conflict, and the fix touches
a file that exists only on AQ-1's side.

## Found that the paste did not name

1. **The five definitions came from the frame.** The opener frame's worked
   example was a definition of dealer gamma, word for word the terms box's.
   Fixing the gate alone would have left the frame teaching the fault.
2. **The eight self-naming sentences are the précis's**, not the sections'.
   They are the RELEVANCE sentences, so the précis's frame and audit carried
   the fix (item 5).
3. **The auction table truncated its percentiles.** `int(88.7)` printed 88th.
   The shared helper rounds half up, as `percentile_ordinal` always has, so a
   few auction ordinals move by one.
4. **The earnings source never stored a release time**, although yfinance has
   one for the next report. It does now (item 9).
5. **`release_at` only lands on an event's first write.** The event store
   dedupes on a content hash that excludes the payload. A forward date first
   pulled without a time keeps "release time not captured" until the date
   changes. See needs-you 3.
6. **A plus sign is now part of a numeral-audit figure's text** ("+$82bn", not
   "$82bn"). The value is unchanged, and no gate depended on the old text.
7. **CRLF.** My patch scripts wrote CRLF on Windows. The files were normalised
   back to LF before the commit.
8. **My first push failed CI, and I fixed it.** CI #376 failed one check in
   `validate_stack_cadence`, a gate outside the local set. It reads a retry
   prompt for the literal `WITHHELD BY THE AUDIT: withheld: motive`, and my
   first retry note had reworded that line. The note now keeps the line
   verbatim and gives the attempt count on the line after.
9. **A code gate reads the laptop's real store.** `validate_weekly_stack`
   calls `book_week` directly with `db_path=None` and no week ending, so the
   Book B scanner opens the default database. Where one exists, as in this
   checkout, it logs `TypeError: '<=' not supported between 'str' and
   'NoneType'`. The error is caught and the gate passes. In a fresh worktree or
   CI there is no store, so nothing is logged. This predates this branch;
   CLAUDE.md says a code gate never reads the live store. It is not fixed here.

## Needs you

1. **Three attempts on the close?** The paste says every withhold-and-retry
   gets three attempts. I applied that to the Weekly, through `prose_attempts`
   in config, and to the précis. The close keeps two. A third close attempt
   costs one more model call per doubly-failed section in the 16:45 window.
   Add `prose_attempts: 3` under `cadences.daily` if you want it there too.
2. **The terms threshold is set from one run:** 5 shared stems and an overlap
   of 0.25. The margin over run 6's clean sentences is one stem and 0.05. If
   dry run #7 withholds a sentence that only shares a word or two with the box,
   the two constants are at the top of `opener.py`'s item 2 block.
3. **Release times for dates already stored.** Events written before this merge
   keep their bare date. A one-off re-pull of the forward earnings dates would
   fill them, but it would need the store's rows for those keys replaced, which
   is a box write. Say if you want that, or let them age out. Each is one week.
4. **The Edge stand-in is not WeasyPrint.** If CI's page-1 check fails on
   WeasyPrint's metrics, the next lever is the précis's own length. The ruled
   band is 150–250, and run 6's paragraph is 208 words.
5. **Run 6's book sentence in the précis** quoted the book's return against
   SPY. That is a real position figure printed in a dry-run edition. The
   fixture replaces it with words; the reports themselves were not changed for
   it.
6. **Friday's order.** I recommend (b): this branch last, then the two-line
   `quarterly.py` ordinal fix as its own commit. The paste's rule would put it
   first, because (a) merges without conflict, but (a) leaves the numeral gate
   red on main from AQ-1's merge onward. Rule (a) or (b). Either way, the fix
   commit is needed once both this branch and AQ-1 are on main.
