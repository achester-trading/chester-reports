# W-1.1 — the Weekly's integrity tranche: session notes

Branch `w-1-1-integrity` from `origin/main` at 785fa19. Spec: §2 of
`docs/change-order-weekly-storyline-2026-10-11.md` (items 1.0 to 1.7 and the
acceptance paragraph), with the five rulings of §8. Session A, 11 Oct 2026.

**The paste was cut off.** It ends partway through item 1.0e ("…carry its rule
into the read and book frames exactly as T3.4a carried the"). Everything after
that point was built from the change order's §2 text, not from the paste. If the
paste added detail to 1.1 to 1.7 beyond §2, it has not reached this branch.

**What was not run.** The full local gate suite was not run (the laptop is
short on memory); CI is the validate. The gates this branch touches were run
one at a time, all green: `validate_figure_budget` 110/0, `validate_no_filler`
14/0, `validate_edition_consistency` 14/0, `validate_weekly_integrity` 36/0,
`validate_weekly_stack` 68/0, `validate_weekly_complete` 57/0,
`validate_weekly_edits` 89/0, `validate_readability` 63/0,
`validate_stack_cadence` 99/0, `validate_stack` 66/0, `validate_daily_close`
102/0, `validate_monthly_stack` 261/0, `validate_monthly` 350/0,
`validate_weekly` 100/0, `validate_prediction_markets` 52/0,
`validate_config_refs` 25/0, `validate_gates` 31/0, `validate_secrets` 37/0,
`check_registry` OK, `check_library` 0 failures.

**The 9 Oct edition itself is not on the laptop.** No payload or edition JSON for
the week ending 9 Oct exists in this checkout, and the dry run (run id
weekly-20261011T155342) lives on the box. The fixtures here rebuild the 9 Oct
cases from the figures quoted in the change order. The explanations below come
from the code that printed each figure. Where an explanation needs the archived
edition to confirm, it says so.

## What was built

**1.0 The budget's second pass (T3.4c).** Built in `daily_cascade/figure_budget.py`,
`daily_cascade/stack_prose.py` and `altdata/derived.py`, wired in by
`weekly_stack.annotate_moves`.

- **Ranking by z.** `derived.period_change_z` computes the z of a row's 7-day
  change against every 7-day change in the series' trailing year, in the unit
  the row prints. That unit is a percent change for a price, a difference for
  a rate, a spread or a count.
  - With fewer than 60 such changes, the row ranks relative to its level, after
    the z-ranked rows, and the frame's `ranking` line names it. Weekly series
    have 52 a year, so they always fall back this way.
  - On the 9 Oct fixture, relative to level puts IG OAS −4 bp (5.0% of 0.80%)
    above CCC OAS +37 bp (3.9% of 9.60%). By z, CCC (+3.2) leads Plumbing and IG
    (−1.5) follows it. That is `validate_figure_budget` group H.
- **Allocation.** Config `figure_budget_sections.weekly` gives Plumbing,
  Positioning and What's priced a cap of 8 with `per_block: true`.
  - The top move of every sub-block that moved goes in first; the rest of the
    cap goes by z.
  - Plumbing's sub-blocks are its buckets, from `monthly_plumbing_buckets`.
  - The daily close stays at 6 because it has no entry.
  - The prompt's "cite at most N" and the paragraph guard both read the
    section's cap.
- **No filler.**
  - The parent frame's names now sit under the key "In the tables (do not
    enumerate)", and the frame and prompt ban "also moved", "all moved",
    "moved alongside" and "moved through the week".
  - `stack_prose.filler_faults` withholds a paragraph that matches the
    pattern, or that strings together three or more of the frame's series
    names, with a comma and no figure. The retry quotes the sentence.
  - The new gate is `tools/validate_no_filler.py`.
- **The four other frames.** The read, Mechanics, What doesn't fit and Ahead are
  each handed a budgeted frame on the Weekly, with a "move" defined per frame:
  - **The read:** the top figure of each section in turn, then the week's
    largest SPY session, then the rest by z. The sections' claims arrive with
    their figures masked. The press attributions arrive with figures and URLs
    stripped.
  - **Mechanics:** the daily move priced and realized first. Then sessions by
    actual range over implied. Then the VIX, realized, MOVE and SKEW week
    changes by z, from a new "Week" column on the Volatility table. Then the
    flip's move. Gamma-regime changes and flags are named, never quantified.
  - **What doesn't fit:** everything ranks on one scale. A gap counts at its
    |z|; an extreme at its percentile's normal-equivalent z (1st percentile =
    2.33); a prediction-market disagreement at 2 × gap ÷ threshold. A gap
    cites its z and its age, in sessions.
  - **Ahead:** the next FOMC meeting and its pricing, copied from What's
    priced's table. Then the graded-calls line. Then tier-1 events with a
    consensus or prior. A family of resolution contracts is one figure, its
    modal outcome, and the 18 Core CPI rows collapse into three families of six.
- **The comparison vocabulary.** `EXCESS_RULE` now sits in the read's and the
  book's prompts, the way T3.4a put the banned list into the frame. The excess
  fault quotes the sentence and the rule, so the retry is not the first the
  writer hears of it.
- **The events line.** `weekly_sections.attribution_text` handles the two
  claim shapes:
  - A claim that is a full sentence is quoted: `CNBC, on the move in oil:
    "Oil prices rose…"`.
  - A clause follows "attributed the move in oil to".

**1.1 Cross-table consistency.**

- `daily_cascade/consistency.py` adds `reconcile(ed)`, which reads the
  assembled edition only.
- Cells are keyed by `series|as-of|measure`, and a builder tags each fact it
  knows another table also prints:
  - the tape's week and session (canonical);
  - the overnight split's sessions and week;
  - the week by day's SPY and 10-year;
  - Plumbing's 10- and 30-year week.
- **Within one unit of the coarser cell's last decimal:** every cell prints the
  canonical value, and the log, kept on the edition as `consistency`, names
  each source.
- **Beyond that:** `EditionInconsistent`. `weekly_report._stacked` prints the
  mismatch, emits an `error` state record and exits 5 (ruling 1). This runs
  after the build and before the prose, so every frame copies the canonical
  figure.
- **The SPY fix:** the overnight split now compounds its legs unrounded, and
  its week is close to close from the same bars as the tape.
- Glossary entry: "the week's return". Gate:
  `tools/validate_edition_consistency.py`.

**1.2 Per-row as-of.**

- **Tape rows:** a price whose bar is older than the edition's session prints
  "(stale since <date>)" beside it. The edition's session is the latest bar
  among the non-continuous instruments, so Bitcoin's weekend bars do not set
  it.
- **No bar for the session:** an instrument that has an older bar prints that
  close, marked stale, with every move "—". Before, it dropped to "not yet
  tracked".
- **FX rows in Plumbing:** held to the last trading session on or before the
  run date.
- **Lagged series:** config `freshness.expected_lag` currently lists the two
  TIC series. They print "lag: monthly (July, released <date>)", and the TIC
  table's "Month" column is now "Period".
- `change_over` carries `available_at`. Ruling 2.

**1.3 Age versus status.**

- `weekly_sections.state_dates` reads every stored market-state object and
  returns the start of each state's *current* run:
  - "gap since": the first session above the line, i.e. the gap's age;
  - "open since";
  - "exception since", for contradictions and for extremes.
- The gap table's "Sessions open" column is now "Gap since · open since ·
  exception since", for example "gap since 2026-09-29 (9 sessions) · open since
  2026-09-30 · exception since 2026-10-05".
- The z column reads "z, five-year window (line)", with the window taken from
  `market_state.yaml`.
- The exceptions table gains an "Exception since" column.
- The glossary's gap z-score entry now states the window, and that the z
  measures cumulative divergence, not the week's move.
- What doesn't fit's note restricts "open n sessions" to the gap's age.

**1.4 Auction fields.**

- The writer already stored bid-to-cover and the indirect, direct and dealer
  shares of competitive accepted. Each now prints with its percentile among
  the same security's auctions over the trailing two years.
- The Weekly prints them in their own "Treasury auctions" table, columns
  Auction · Bid-to-cover · Indirect · Direct · Dealers · Tail vs when-issued.
  The Monthly keeps its bucket rows.
- **The tail is not stored.** The writer's docstring records why: no free
  source publishes the when-issued yield, so `auction.tail_bp` stays registered
  and unsourced. The table prints "not stored".
- `stack_prose.tail_faults` withholds "tail(ed)" in any sentence about an
  auction unless a stored tail is positive. "Tail-risk" is exempt.

**1.5 The prediction-market contract record.**

- **The writer** now stores `pm.bid`, `pm.ask`, `pm.last` and
  `pm.open_interest` (liquidity) beside the mid, all registered. `pm.market`
  carries a `rules_url` next to the existing rules text.
- **The retrieval instant** is each row's `observed_at` (= `available_at`), the
  fetch instant. The reader exposes it as `retrieved_at`.
- **The reader** computes `spread_points` and flags `illiquid` past
  `illiquid_spread_points: 10` in `config/prediction_markets.yaml`.
- **A meeting's legs** that sum outside the band print "Kalshi legs sum 108%",
  with each side's cell reading "68% (63% normalised)".
- **The note** carries "<Venue> illiquid (spread N pts)" where it applies.
- **Cross-venue comparisons** already used `pm.probability`, which is the mid
  wherever both sides are quoted.
- **The rename.** "outside 10–90%" is now "favourite–longshot check: outside
  10–90%", and the legend reads it as a flag, not a verdict. Glossary entries
  added: favourite–longshot check, legs sum and normalised, illiquid, mid.

**1.6 Coincidence, not causation.**

- "on the back of", "in response to" and "reacting to" join the motive words
  in config.
- Quoted text is exempt from the motive check (`stack_prose.unquoted`).
- The read's frame lists the three allowed connectors. Its subtitle now reads
  "the week's five lines, and the events alongside each session", and its
  table note reads "Events alongside the session: …, not what caused it."

**1.7 Unvalidated tags.**

- Config `descriptive_classifications` lists six classifications: dealer flags,
  gamma regime, gap states, extremes, the favourite–longshot check and story
  states. Each has a `graded_source`, null today.
- `n` counts the resolved probability-ledger rows under that source, so it is
  0 until the scorecard grades the classification.
- Each section that prints one carries one footnote, for example "The dealer
  flags (pinned, held, amplified) and the gamma regime: (descriptive;
  unvalidated, n=0)."
- The glossary carries one entry per classification.

**Gates.** Three new gates (`validate_no_filler`, `validate_edition_consistency`,
`validate_weekly_integrity`) are in the Makefile, with CLAUDE.md's count updated
to fifty code gates. These existing gates were updated for the new
conventions:

- `validate_figure_budget`: groups H and I, and the renamed key;
- `validate_weekly_stack`: the favourite–longshot legend;
- `validate_weekly_edits`: the glossary term;
- `validate_readability`: the eight-figure sections, and the legs cell;
- `validate_weekly_complete`: the unrounded week, and the auctions table.

## Discrepancies found in the 9 Oct edition

1. **SPY's week, +1.16% in the tape and +1.17% in the overnight/cash split.**
   - The tape computes the last close over the last close before the week
     (`levels.instrument`, `wtd_change_pct`).
   - The split rounded each session's overnight and intraday return to two
     decimals, then compounded the rounded figures and printed their product as
     the week. The rounding drifts a hundredth often enough to show; the gate's
     constructed bars reproduce it (−0.75% against −0.76%).
   - Fixed to one convention, close to close, with the legs compounded
     unrounded. The consistency gate now catches any recurrence.
2. **An exception's age and its status, printed as one number.**
   - `contradiction_line` and the gap table printed `persistence_days`. That is
     the length of the run above the line, the gap's age. The gap had been
     measured for eight sessions and only became an exception this week, so
     the single count read as eight sessions of exception.
   - Fixed: three dates (item 1.3) and the prose rule.
3. **The gap z-score's window against the week's move.**
   - The gap z is today's standardised gap against that gap's own five-year
     history (`contradictions.py`): a cumulative divergence. The edition named
     neither the window nor what the z measures, so it read as the week's move.
   - Fixed in the column head and the glossary.
4. **Mixed dates, 7, 8 and 9 Oct, in one edition.** Each date is the series'
   own publication schedule, not an error:
   - the tape's bars are dated the session, 9 Oct;
   - FRED's daily series (OAS, yields' levels, SOFR) are published a day late,
     8 Oct;
   - the H.4.1 legs are Wednesday levels released Thursday;
   - the CFTC report is as of Tuesday;
   - TIC is two months behind.
   The fault was that the tape's rows carried no date and the lagged series
   were not told apart from stale ones. Fixed by item 1.2: every older row
   prints its date, a price prints "stale since", and TIC prints its declared
   lag.
5. **The Bitcoin bar.** Bitcoin is the tape's one continuous instrument, and
   yfinance dates its daily bar by the UTC day. `levels.instrument` takes a
   session's bar only when it is dated that session.
   - **If the bar was dated before the session:** the row dropped to "not yet
     tracked". Now it prints the last close, stale since its date.
   - **If the bar was the 9 Oct UTC bar fetched at 16:10 ET:** its "close" was
     the price at 20:10 UTC, an unfinished day. The edition printed a snapshot
     as a close.
   **Unconfirmed: needs the archived edition JSON.** The stale mark covers the
   first case. The second is the last item in "Needs you".
6. **"Legs sum 108%".**
   - Kalshi lists a meeting's outcomes as separate contracts. Their mids need
     not sum to one: each book's spread adds a little.
   - The disagreement rule compared the *normalised* odds with fed funds
     futures, while the table printed the *quoted* ones with only a "legs sum
     to 108%" note. A reader saw one number in the table and the rule acted on
     another.
   - Fixed by item 1.5: both print side by side, and the rule is unchanged.
7. **IG OAS −4 bp outranked CCC OAS +37 bp** in Plumbing's frame, which is why
   the prose read "no stress" in the week of the CCC widening. The cause was
   relative-to-level ranking. Fixed by z ranking (item 1.0b).
8. **Positioning spent its six figures on sector returns.**
   - Six sector moves of 3–6% each outranked every CFTC row, which has no
     level column to scale by.
   - Fixed by the cap of 8 with one figure per sub-block (item 1.0c).
9. **Filler sentences** such as "the 10-year, 30-year and 2-year all moved
   alongside…". The frame's also-moved list was offered as content. Fixed by
   the heading, the ban and the gate (item 1.0d).
10. **"attributed the move in oil to Oil prices rose…".** The stored claim was a
    whole sentence, pasted after "to". Fixed: a sentence is quoted, a clause
    follows "to".
11. **The 30-year auction's "tail".** No when-issued yield is stored, so the
    edition could not know whether the auction tailed. What it does know: a
    7% dealer take, which now prints with its two-year percentile. The prose
    may no longer say "tailed" without a stored tail.

## Choices made for the operator to overrule

- **The z of a weekly change.**
  - **The window:** overlapping 7-calendar-day changes, each ending on an
    observation in the trailing 365 days, centred on their mean. The change
    order says "trailing-year weekly changes ≥ 60". Non-overlapping weekly
    changes give 52 a year, so they could never reach 60. I read the floor as
    implying overlapping windows; a weekly series still falls back.
  - **The order:** z-ranked rows rank ahead of relative-ranked ones; the two
    scales are not compared with each other.
- **Plumbing's sub-blocks** are the Monthly's buckets
  (`monthly_plumbing_buckets`), read at the Weekly's cadence. Positioning's
  and What's priced's are their sub-sections.
- **The four frames' definitions of a move:**
  - their priority orders, as described under item 1.0 above;
  - What doesn't fit's common scale (percentile → normal-equivalent z;
    disagreement → 2 × gap ÷ threshold);
  - the read takes each section's top figure first, then SPY's biggest day;
  - the frame caps are the cadence's six, with no overrides for these four.
- **The filler list rule:** three or more of the frame's own series names, at
  least one comma, no figure in the sentence. The pattern rule fires even in
  a sentence that carries a figure ("Gold rose +2.10%; silver also moved").
- **The consistency gate compares tagged facts only:** the tape, the split,
  the week by day and Plumbing's 10- and 30-year. It is not a scan of every
  number in the edition. Tolerance is one unit in the coarser cell's last
  decimal, and the tape is canonical.
- **"Stale" is measured against the last trading session** on or before the
  run date (FX, Plumbing). For the tape, it is the latest non-continuous
  instrument's bar.
- **The three dates are labelled "gap since · open since · exception since".**
  The change order says "gap since · pending since · exception since". A row
  goes pending on the very session its gap first crosses the line, so
  "pending since" is always the same date as "gap since". The middle date
  that differs is when it opened.
- **The read's daily table was not retitled.** I set the read's subtitle
  ("…and the events alongside each session") and the table note instead,
  because a section's main table has no heading of its own in the renderer.
- **The tail is not approximated.** The writer's existing design says so in
  as many words. Instead, "tail" is withheld in auction sentences.
- **Illiquid means a spread over 10 points**
  (`config/prediction_markets.yaml`). The glossary quotes the 10.
- **The descriptive classifications** are the six listed under 1.7, with n
  from the probability ledger by `graded_source`.
- **The Monthly's block frames keep their `also_moved` key and get no filler
  ban.** The Weekly's parent frames, and the Monthly's parent frames, use the
  new heading.

## Needs you

1. **A proxy tail for the 10- and 30-year?** It would be the auction's high
   yield less the 13:00 ET 5-minute bar of ^TNX / ^TYX (already in the bars
   table), printed as "vs the 13:00 secondary yield (proxy)". This reverses the
   writer's documented "nothing here approximates one". Yes / no.
2. **Keep 10 points as the illiquid spread threshold?** Yes / no.
3. **Keep the middle date as "open since"** rather than the change order's
   "pending since", for the reason above? Yes / no.
4. **Should the Monthly's block frames take the "In the tables (do not
   enumerate)" heading and the filler audit too?** It is the same fault in
   another frame, and would be the next tranche's. Yes / no.
5. **Hold Bitcoin's tape row to the 16:00 ET price** rather than yfinance's
   UTC-day bar, if the 9 Oct edition JSON confirms the bar was a 20:10 UTC
   snapshot? Yes / no.
