# A88 notes: the Monthly's numeral audit binds the series the prose names

Branch `a88-monthly-audit-binding`, from origin/main at `f380e12e` (the A85
merge). Laptop session, 28-29 Oct 2026. Nothing run on the box. The dry run's log
(`monthly-dryrun-2026-10-28.log`, outside the repo) was read in full and is not
committed.

## Part 0: the CI date bomb

`tools/validate_prediction_markets.py` section J built the close with the real
clock. Two places read it:

- `validate_stack.seed()` stamps the fixture's market state `as_of` with
  `session.utc_iso()`;
- `stack.build()` takes that as its cutoff.

From 29 Oct 2026 the fixture's 28 Oct meeting was in the past and the renderer
(rightly) dropped it, so three checks failed.

The fix pins `session.utc_now` to the fixture session's close (2026-09-30
20:45 UTC) from the seed to the build, and restores it after. The renderer's rule
is unchanged. 52/0. Commit `debc0c6a`.

## Part 1: the 14 sections, by cause

**How each case was reproduced.** The laptop has no dry-run payload and its store
cannot rebuild one. Each case is therefore the logged sentence over a synthetic
block in the rows' REAL labels:

- the pillars' from `altdata/config.py` FRED_SERIES descriptions;
- the themes' from `config/monthly_themes.yaml`;
- the blocks' from the audit's own messages.

Each block carries the figures the draft quotes, in the slice's own fields
(`latest_pct` for a rate, `latest_level_display` for a scaled level). On
f380e12e, 0 of the 19 cases pass. On this branch, 19 of 19 pass. They are
`tests/fixtures/monthly_dryrun_2026-10-28.json`, run by
`validate_audit_fixes.py` group K.

**The mechanism behind most of them.** `series_bindings` bound a figure to the
nearest preceding name in its sentence, else to any name after it. When the
prose's name for a series matched none of its row's aliases, the figure fell to
a neighbouring series' name, often one named later in another clause.

**Each case:**

- **theme:liquidity_plumbing**
  - **$5.78tn, +0.06% (a).** The row "Net liquidity (Fed balance sheet less
    reverse repo and Treasury cash)" has a bracket too long for the alias rule,
    so "Net liquidity" was no name at all. The nearest name was "Fed balance
    sheet" INSIDE the prose's parenthesis.
  - **+$23.15bn, $2.95tn (a).** The prose says "bank reserves"; the row is "Bank
    reserves at the Fed".
  - **Attempt 1's −1.56%, 157.25 (c).** These bound to the JGB yield, named after
    them in another clause.
  - Now passes.
- **theme:fiscal_dollar**
  - **+39, 5.64% (a).** The prose says "the 30-year"; "30-year" is unique in this
    block.
  - **+12.6, 0.89% (a).** The prose says "the term premium"; the row is "10-year
    term premium (NY Fed ACM model)".
  - **−68.53%, −$21.56bn (a)+(c).** The prose says "U.S."; the row says "US". The
    holdings row is named after them in another clause.
  - The log's "+2 more" are not printed; not reproduced.
  - The six now pass.
- **theme:geopolitics_reserve, −0.7%, 6.74 (a).** The prose says "the daily
  fixing"; the row is "Yuan daily fixing". Dollar-yuan is named after them in
  the same clause. Now passes.
- **pillar:1**
  - **159.04 million (a)+(c).** The prose says "nonfarm payrolls"; the row is
    "Nonfarm payrolls, total". U-3 is named after it in another clause.
  - **7.08 million, 5.19 million (a), not (b).** The prose says "job openings" and
    "hires"; the rows are "Job openings, total (JOLTS)" and "Hires level, total
    (JOLTS)". The name they actually bound to was "Quits rate", named later.
  - **Why the message read "JOLTS ... JOLTS".** Every JOLTS row's display name is
    its bracket. The shared alias JOLTS never appears in the prose.
  - Now passes.
- **pillar:2**
  - **5.29%, 4.88%, +54 (a).** The prose says "the 10-year yield" and "the
    2-year".
  - **1.4 million (a)+(c).** The prose says "building permits"; existing home
    sales are named after it in another clause.
  - **Attempt 2 now passes.** Its "respectively" clause binds nothing; see the
    rules.
  - **Attempt 1's "+39 ... 5.64%" STILL FAILS.** The prose says a bare "the
    30-year" in a block that also holds the 30-year mortgage rate. "30-year" is
    not unique to one row there, so by the paste's rule it is not an alias, and
    the figure falls to the nearest name before it, "2-year". The audit
    withholds rather than guess which 30-year was meant.
  - So the section publishes on a draft that says "the 30-year yield", as attempt
    2 did.
- **pillar:3, −5.65%, −0.52 (a).** The prose says "the Chicago Fed's National
  Financial Conditions Index"; the row is "Chicago Fed NFCI". Now passes.
- **pillar:4**
  - **+0.88 (a).** The prose says "flexible CPI"; the row is "Flexible CPI, 1-mo
    ann".
  - **+0.03 (c).** It bound to "core CPI" inside "sticky core CPI".
  - **Attempt 1's +0.65% (c).** A "respectively" list.
  - Now passes.
- **pillar:7, the euro / yen / yuan (a).** The rows are "USD/EUR exchange rate"
  and the like. The prose's names come from the registry's `quote_conventions`.
  Now passes.
- **stack:slow, +272.0%, −44.3% (a)+(c).** The prose says "PRL's fees" and
  "ZEC's fees"; the rows are "PRL fees, 30 days" and "ZEC fees, 30 days". Both
  bound to "Zcash's shielded share of supply", named after them. Now passes.
- **block:plumbing:yields, "18" (not (a)-(d)).** This is a plain-match failure
  ("2s10s at 29 bp, down 18 bp"): the figure is in no row of the block, not bound
  to a wrong one. Without the block it cannot be told whether the draft or the
  block's change is off.
  - It is outside the binding fix and is left as it is.
  - **Needs the box's payload to classify.**
- **block:plumbing:liquidity, $5.80tn (a)+(c).** "Net liquidity" is no name (the
  long bracket). Bank reserves, whose bracket is "H.4.1", are named after it in
  another clause. Now passes.
- **block:positioning:sectors, −3.27% (c).** "(XLY/XLP)" straight after the
  figure is its own tag; it bound to the nearer "(IWM/SPY)" before it. Now passes.
- **summary:plumbing, +6 (a).** Two rows are called SOFR less IORB, one with a
  long bracket that left it nameless. Now passes.
- **summary:slow, +272.0% (a).** The prose says "PRL fees"; the row is "PRL fees,
  30 days", and it bound to the "PRL" row. Now passes.
- **our_read, the role audit (d), all three.**
  - "1" is the day in "1 October 2026".
  - "20" is "its 20-day average".
  - "0.5" is "the 0.65 and 0.5 weights".

  Now passes.

**pillar:3** published on its second attempt in the dry run. Its first attempt
is the pillar:3 case above.

## Part 2: the rules changed (`altdata/numeral_audit.py`, the binding and the role span only)

**The binding:**

1. **Derived names.** A row's label also goes by:
   - its head (before a comma, a bracket, or " at/of/for/in/on ");
   - each of those without the issuer and noise words: the, Treasury, total,
     rate, level;
   - without its leading tenor, or its first word, where two or more words
     remain;
   - its leading tenor ("2-year");
   - the registry's currency names for an ISO pair in it;
   - the words of an acronym that ends it.

   Each binds only where it is unique to one row in the block. A form equal to
   another row's own name joins that row's group, as same-named rows already
   bind together.
2. **The registry's aliases.** The registry declares currency names in
   `quote_conventions` (pair, base, quote), which is where "euro", "yen" and
   "yuan" come from. Its `aliases` lists there are keyed by yfinance pairs that
   the Monthly's FRED rows do not carry, so they are not used.
3. **(b), shared names.** A name several rows share keeps binding to all of them
   as a group. It is not "binds to none": that would let a figure belonging to
   another series pass, and the dry run's JOLTS failures were not caused by the
   shared name.
4. **The clause (c).** A figure binds to the first of these that it finds:
   - a name in brackets straight after it;
   - a name in its own clause: before it first, nearest; then a name inside a
     bracket that closes before the figure; then a name after it;
   - the nearest name before it in the sentence.

   A name after it in another clause never binds it. A clause ends at a comma
   (not between digits), a semicolon, a colon, a dash or " - ". A bracket does
   not end one: "Technology (XLK) fell 7.70% while the Nasdaq 100 (QQQ) fell
   5.52%" keeps each figure on its own name.
5. **"respectively".** A clause that says it pairs its lists by order, so its
   figures bind to nothing and the plain match reads them.
6. **Possessives.** A phrase's first word may be possessive ("PRL's fees").

**The role audit (d):**

7. **What is skipped.** A close-word no longer reads:
   - a date's numerals ("1 October 2026", "October 1", "2026-10-21");
   - a numeral followed by -day, -week, -month, -year or -session;
   - a figure the prose calls a weight, probability, odds or chance that the
     payload also carries as one.

   A bare 0.5 after "closed" is still read.
8. **The span.** It ends at a semicolon, colon, dash or bracket, but NOT at a
   comma. "closes September with gold at 4,554.56, SPY at 721.82 and QQQ at
   670.83" is the list case the audit exists for, and its run-5 fixture requires
   all three.

**Unchanged:** no figure-matching tolerance moved, and no existing fixture's
verdict changed.

## The must-still-fail cases (group K)

**Binding:**

- payrolls given the openings figure (a derived name binds);
- the 10-year yield given the 2-year's level;
- the euro given the yen's level;
- hires given the openings figure in its own clause;
- "(XLY/XLP)" given IWM/SPY's figure (the own tag);
- net liquidity, outside the bracket, given reserves' level;
- the spelled-out NFCI given its leverage subindex's change.

On f380e12e, five of these seven passed, so the binding now catches wrong figures
it used to miss as well as releasing right ones.

**Role:** "SPY closed at 721.82 on 1 October 2026" (a real average beside a date),
and "the spread closed the month at 0.5" (0.5 not called a weight).

## Overlap with session B (B84)

B84 takes looking_ahead's and stack:tape's role failures, and they run through
the same `role_faults`. The date rule here covers "December 31st" (a month and a
day) but not a bare "the 1st". A merge of B84 after this branch should expect
`role_faults` to have moved.

## Gates (one at a time, foreground, laptop)

- `validate_prediction_markets.py`: 52/0 (Part 0, and again after Part 2).
- `validate_audit_fixes.py`: 133/0, with group K.
- `validate_numeral_audit.py`: 172/0.
- `validate_weekly_fixes_8.py`: 67/0, with W8-2's cases all holding: "5.52% is
  bound to XLK but belongs to QQQ", the open-interest share, the semicolon
  clause.
- `validate_readability.py`: 67/0.
- `validate_monthly.py`: 359/0, 1 skipped.
- `validate_stack.py`: 73 passed, 0 failed when the 10-minute foreground limit
  stopped it. It had reached groups A-I and M; its alias case (group B, "the
  10-year yield ... week high") passed. The volume-profile group and the summary
  did not run on the laptop, so CI's run is the whole one.
- The Monthly's prose gate is `validate_audit_fixes.py`'s groups G-K
  (`monthly_macro/prose.py` is exercised there); there is no separate one.

## Re-audit of the logged drafts

19 of the 19 reproduced cases pass. The two not reproduced:

- block:plumbing:yields' "18", a plain-match failure;
- fiscal_dollar's unprinted "+2 more".

Pillar:2's first draft still fails on its bare "the 30-year". The whole drafts
could not be re-audited against their real payloads, which the laptop does not
have. The box's next dry run is that check.
