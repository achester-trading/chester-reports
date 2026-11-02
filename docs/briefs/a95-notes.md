# A95 notes: the first stacked Monthly (1 Nov 2026), what it withheld, and the Letter's seven findings

**Branch.** `a95-monthly-first-edition`, from `origin/a97-weekly-readability` at
`d30238ed` (A97's tip, which holds main at `422ea697`, A88 and B84). It merges
on Wednesday with the rest, for the 1 Dec Monthly and the Weeklies before it.

**The evidence.** The run log is on the laptop, outside the repo, and is never
committed. Its last run started at 12:36:16 UTC and ended at 12:49:15 UTC
(`--skip-fetch`, rc 0, 779 s, delivered over SMTP). The edition's payload is on
the box, which this paste does not touch.

## Step 1: the tally

- **88 model calls:** 61 sections' first attempts and 27 retries. 11 sections
  published on the retry.
- **45 of 61 published:** 33 of the 48 body sections (5,790 words) and 12 of
  the 13 summary paragraphs. 6,916 prose words in all, about 33 minutes to read
  against the 55-minute target.

| Section | Status | Attempts | The reason (the last attempt's) |
|---|---|---|---|
| month_in_markets | withheld (bare_delta) | 2 | "+29,000" with no noun (attempt 1: "7580.07" without separators) |
| month_in_one_page | published | 2 | attempt 1: "77198.21" without separators |
| theme:liquidity_plumbing | withheld | 2 | $5.75tn bound to "Fed balance sheet" |
| theme:fiscal_dollar | withheld (tape_rules) | 2 | "3898.9" without separators (attempt 1: "4.0" bound to the broad dollar) |
| theme:fed_path | withheld | 2 | "4.2" bound to "level" (attempt 1: "4.2%" typed a price) |
| theme:credit_cycle | published | 1 | |
| theme:equity_positioning | published | 2 | attempt 1: +0.02 / 0.29 bound to the S&P 500 |
| theme:sentiment | withheld | 2 | 99, 19 and two inflation-expectation figures bound to Michigan sentiment |
| theme:geopolitics_reserve | withheld | 2 | 77.47 million bound to GC=F |
| looking_ahead | published | 1 | |
| our_read | published | 2 | attempt 1: the role audit on "closes ... 0.9" |
| pillar:1 | withheld | 2 | 1.94 million, +0.1 and +0.2 bound to the wrong rows (attempt 1: 4.2%, 61.8%, 59.2% typed a price) |
| pillar:2 | published | 2 | attempt 1: 67,000, 41,000, 5,000, 4,000 rescaled |
| pillar:3 | published | 2 | attempt 1: +$51.05bn / $999.73bn bound to reverse repo |
| pillar:4, 5, 6, 8 | published | 1 | |
| pillar:7 | withheld | 2 | −0.36% / 156.87 bound to USD/EUR (attempt 1: the reverse) |
| stack:tape | published | 1 | |
| stack:misfit | withheld (internal_vocabulary) | 2 | "the breadth dimension" (attempt 1: "69th") |
| stack:plumbing | published | 2 | attempt 1: "$7bn" |
| stack:positioning | withheld | 2 | 169,786, 39,402, 66,763 (unsigned, after "shed" and "fell") |
| stack:priced | withheld (tape_rules) | 2 | "hike" in a sentence naming a recession market |
| stack:narratives | published | 2 | attempt 1: 0.32% / 0.33% bound to "month" |
| stack:slow | published | 1 | |
| block:plumbing:yields | withheld (tape_rules) | 2 | "sharply" with no figure (attempt 1: "19, 18") |
| block:plumbing:macro, auctions | published | 1 | |
| block:plumbing:liquidity | withheld | 2 | $5.75tn bound to "H.4.1" |
| block:plumbing:metals | withheld | 2 | −5.43% bound to copper's label |
| block:plumbing:global | published | 2 | attempt 1: 21, 17, 1.67%, 0.73% |
| block:positioning:sectors, short, retail, tic | published | 1 | |
| block:positioning:cftc | published | 2 | attempt 1: −981,538 / −19,138 bare |
| block:positioning:alloc | published | 2 | attempt 1: filler |
| block:priced:fomc, breakevens, pm_fomc, pm_rest | published | 1 | |
| block:voices (three) | published | 1 | |
| block:slow:digital, energy | published | 1 | |
| block:slow:metals | withheld (tape_rules) | 2 | the role audit: SLV's average "since 2021-09-20 of 32.01" bound to "ended" |
| summary:read, tape, mechanics, misfit, plumbing, labour, positioning, narratives, reading, ahead, book | published | 1 | |
| summary:priced | withheld | 2 | −4.5 bound to "Yes" |
| summary:slow | published | 2 | attempt 1: +230.8% bound to "%" |

The log's "audit retry ... attempt 1 of 2 published" lines were WARNINGs; they
are INFO now.

## Step 2: the classification

Classes, as A88, B84 and A90 used them:

- **(i)** a false positive in the check, narrowed with a must-pass draft and a must-fail case;
- **(ii)** the draft is wrong and the check right: the fix goes to what the writer is given or to its instruction;
- **(iii)** the retry message does not name the fix.

**Binding** marks A88/A90's code, which this paste does not touch. The **W10-1**
column is what A97's fallback does with the section's second draft
(`a97_replay.py` over this log): 5 of the 16 would have published, with 6
markers.

| Section | Class | The sentence and the reason | Fix here | W10-1 |
|---|---|---|---|---|
| month_in_markets | (ii) + (iii) | "the S&P 500 ... 7580.07" without separators, then "payrolls for September rose by +29,000" with no noun. The second fault was in draft 1 too, but its retry heard only the first | Scorecard levels carry their separated display. **The retry hears every fault** | publishes, 1 of 13 withheld |
| theme:liquidity_plumbing | (i), binding | "Net liquidity, measured as the Fed balance sheet less ..., fell to $5.75tn": bound to the appositive's name | None (binding). A90's branch binds it to net liquidity, so it passes there | whole (first sentence) |
| theme:fiscal_dollar | (i), binding, then (ii) + (iii) | "registered in only 4.0 of the last thirteen weeks", bound to the broad dollar; then "the COMEX front-month future fell −6.87% to 3898.9", which was in draft 1 too | A raw level of 1,000 or more reaches the writer as "3,898.9". The retry hears every fault. The 4.0 is the binding's | whole (not a figure's fault) |
| theme:fed_path | (i), fixed in the data block; draft 2 binding | "the unemployment rate ticked up to 4.2%": the rate travelled as `latest_level`, typed a price | A rate or share (units "%") reaches the writer as `latest_pct`. Draft 1 now passes. Draft 2's "a level of 4.2" is the binding's, and A90 passes it | publishes, 1 of 11 |
| theme:sentiment | (i) sign; binding; draft 2 (ii) | "WallStreetBets mentions of SPY fell by 99": the move is a display string. "rose +10 bp to 3.5%" is bound to Michigan sentiment. Draft 2 wrote "rose by its change_bps_signed" | The sign rule reads display strings (99 and 19 pass). The binding cases stay. Draft 2 is a wrong draft | publishes, 2 of 12 |
| theme:geopolitics_reserve | (i), binding | "China's gold holdings rose by 740,000 ounces to 77.47 million ounces": bound to GC=F through the derived name "gold". A90 does not change it | None (binding); listed for its next paste | publishes, 1 of 11 |
| pillar:1 | (i) type; binding; draft 2 (ii) | Draft 1: "4.2%", "61.8%", "59.2%" typed a price, and 1.94 million bound to claims. Draft 2 swapped participation's +0.2 and employment-population's +0.1, a true (ii) | The percent fix cures draft 1's three. 1.94 million is the binding's. Draft 2 stays withheld | whole (2 of 5) |
| pillar:7 | (i), binding | "USD/EUR fell −1.48% to 1.12 ... JPY/USD fell −0.36% to 156.87": each bound to the other | None (binding). A90 unbinds both (rule 9), so it passes there | publishes, 1 of 4 |
| stack:misfit | (ii) + (iii) | "The breadth dimension corrected this month to broad": copied from the data, whose dimension item read "The breadth dimension moved from narrow to broad". Draft 1's "69th" (the text carried "percentile 68.6") was the only fault its retry heard | The item now reads "Our breadth read moved from ...". The retry hears every fault | whole (not a figure's fault) |
| stack:positioning | (i) | "10-year note futures shed 169,786 contracts", "gold futures positioning fell 39,402 contracts": the frame carries "−169,786 contracts" as a display string, which the falling-verb rule did not read, and the message named no fix | The sign rule reads a move's display string and a change column's cell. Draft 2 passes; a rising verb or no verb still fails, now naming the display | whole (first sentence) |
| stack:priced | (ii) + (iii) | "What the month priced is a Fed still seen ... to hike ..., and a recession market that ...". The rule is right. The message quoted "('hike')", so the retry's failing span was the first sentence holding "hike", a correct one, and the faulty sentence came back unchanged | The message quotes the faulty sentence and names the fix (separate sentences). The policy frame writes out the allowed phrasing | whole |
| block:plumbing:yields | (i) sign, then (ii) + (iii) | "the 30-year yield fell 19 bp": the table cell "−19 bp" was not read by the falling-verb rule. Then "a sharply wider CCC tier", no figure in the sentence, which was in draft 1 too | The sign rule reads change cells. The intensity message names the fix. The retry hears every fault | whole (not a figure's fault) |
| block:plumbing:liquidity | (i), binding | "Net liquidity at $5.75tn": bound to "H.4.1". A90's replay cannot rebuild this block's labels from the log | None (binding); listed | whole (first sentence) |
| block:plumbing:metals | (i), binding | "gold-over-copper fell −5.43% to 604": bound to copper's "$/lb" label | None (binding); listed | whole (first sentence) |
| block:slow:metals | (i) | "closed October at 44.60, ..., against its full-history average since 2021-09-20 of 32.01": the date's numerals restarted the role audit's gap, which lost "average" | A date's numerals no longer end the gap. Both drafts pass; an average after a date and called the close still fails | whole (first sentence) |
| summary:priced | (i), binding | "the base rate for a cut ... moved −4.5 pts": bound to a leg labelled "Yes" | None (binding); listed | whole (first sentence) |

**By cause:**

- **Units and scale.** "+29,000": (ii). The retry now hears it. The display
  with its noun was already in the message; the retry had never been told.
- **Machinery words.** "the breadth dimension": (ii), fixed at the data that
  carried the words.
- **Adverbs without figures.** "sharply": (ii); the message now names the fix.
- **Separators.** "7580.07", "3898.9": (ii). The writer now gets the separated
  form.
- **The policy-word rule.** (ii). The message is (iii), quoting the wrong
  sentence's word; now fixed.
- **The role audit's averages.** (i), across a date; narrowed.
- **Binding.** Nine sections' faults are A88/A90's, and this paste leaves them.
  A90's branch passes theme:liquidity_plumbing, pillar:7 and theme:fed_path's
  draft 2. It leaves theme:geopolitics_reserve,
  block:plumbing:liquidity, block:plumbing:metals, summary:priced, pillar:1's
  1.94 million and theme:sentiment's inflation expectations for the binding's
  next paste.
- **The retry heard only the first fault.** This lost four sections whose first
  draft carried the second fault too: month_in_markets, theme:fiscal_dollar,
  block:plumbing:yields and stack:misfit.

## Step 3: the fixes

**(i) Narrow rules,** in `altdata/numeral_audit.py`, outside the binding:

1. **The sign rule reads display strings.** `signed_fields` takes a move field
   whose value is a display string written with a minus
   ({"change": "−169,786 contracts"}), and a cell under a change column ("−19
   bp"), read through `extract()` as the prose is. So W-1.1a's "the verb carries
   the sign" applies to a frame's moves, and a sign error names the display to
   copy.
2. **The role audit's gap runs on across a date.** A date's figures are skipped
   without restarting the gap.

**(iii) Messages:**

3. **The one revision hears every fault the draft carries**
   (`monthly_macro/prose.py`: `draft_faults`, `with_also`, `ALSO`). The
   verdict and the withheld reason are unchanged. The other faults ride after
   the reason, for the retry alone, with their rules and failing spans.
4. **The policy-word message** quotes the sentence at fault, not the word, and
   names the fix (`daily_cascade/stack_prose.py`).
5. **The intensity-word message** names its fix.
6. **A published attempt logs at INFO** (`daily_cascade/audit_retry.py`).

**(ii) The writer's data and instructions:**

7. **A rate or share as a percent.** A series in units "%" reaches the writer
   as `latest_pct` (`prose._series`).
8. **Separators.** A raw level of 1,000 or more reaches the writer as its
   separated display: `latest_level_display` in `_series` (the raw value
   dropped, as T3.3 item 2 rules), and `start_level_display` /
   `end_level_display` beside the scorecard's values.
9. **The misfit item's words.** The dimension item reads "Our breadth read moved
   from ..." (`v2._dimension_items`).
10. **The policy frame** writes out the allowed phrasing, without figures.

**Fixtures.** `tests/fixtures/monthly_first_edition_2026-11-01.json` quotes the
drafts verbatim. It is run by:

- `validate_numeral_audit` group M: the sign display and the role audit, each
  with must-fail cases;
- `validate_monthly` group K: every fault reaches the retry; the policy span;
  the intensity message; the percent; the separators; the misfit words; the log
  level.

## Step 4: the replay

**The four counts:**

- 43 drafts;
- **31** replay identically on main and this branch;
- **12** have a changed verdict on at least one figure;
- **3** withheld sections newly pass (stack:positioning, block:slow:metals and
  theme:fed_path's draft 1);
- **0** sentences newly fail.

**How it works.** The script is `scratchpad/a95_replay.py`, uncommitted because
it needs the log. It runs every logged draft through main's `numeral_audit`
(the `422ea697` worktree) and this branch's.

**The payload each rule is replayed against.** There is no payload on the laptop,
so each rule is replayed against the payload that makes it fire most:

- **the role audit:** every figure held as an average only;
- **the sign rule:** each unsigned figure in turn held as a negative display
  string;
- **the percent share:** the pillar rows as main and the branch hand them over.

**The newly passing figures, by rule:**

- **The sign rule** (each after "fell", "shed", "down" or "slipped"; every one
  a negative move written with a falling verb, as W-1.1a allows):
  - theme:sentiment's 99 and 19 (both drafts);
  - pillar:2 draft 1's 67,000, 41,000, 5,000 and 4,000. That section still
    fails on "fell by 67,000" with no noun, under the bare-delta rule;
  - pillar:2's 24 and 27. These are numeric moves in the real slice, which
    main already accepts, so this is an artifact of the replay's display shape;
  - stack:plumbing's $7bn, where the frame carries "−$7bn";
  - stack:positioning's three figures (both drafts);
  - the yields block's 19 and 18;
  - block:plumbing:global's 21, 17, 1.67% and 0.73%.
- **The role audit:** block:slow:metals' 32.01 (both drafts). The 80th still
  shows only because the replay calls every figure an average; in the real
  payload it is a percentile.
- **The percent share:** theme:fed_path's and pillar:1's 4.2%, and pillar:1's
  61.8% and 59.2%.

The retry and data fixes cannot be replayed, because they change what the model
would write.

## Part 6: the Letter's findings

Seven places where the 1 Nov edition contradicts itself. Each is fixed, none by
removing a print. `docs/briefs/letter-findings.md` (created here; B102 had not
made it on main) carries the table.

| Row | Which side was right | The fix | The check |
|---|---|---|---|
| M1 | Section 4 | The summary's frame carries the counts; a summary denying them is withheld | `validate_monthly_frames` G |
| M2 | The themes' month (`v2.metric_month`) | The yields table's month-aligned prior (`v2.prior_target`, one rule) | `validate_monthly_frames` G |
| M3 | Both counters | The header names the ledger and the scenario-weight count | `validate_monthly_frames` G; `validate_audit_fixes` J's fixture line |
| M4 | "Against Book Z since 5 Sep" | One `book_z_sentence`; the ledgers labelled returns | `validate_monthly_frames` G |
| M5 | The Weekly's age | The Monthly passes the stored objects' dates | `validate_monthly_frames` G |
| M6 | The date-based table | `headline_form` by date across BLS's missing October 2025 | `validate_monthly_frames` G |
| M7 | Both (two series, one label) | FRED's VIX and dollar-yen labelled apart | `validate_monthly_frames` G (no label over two series) |

**For the merge sheet:**

- **Weekly code.** `daily_cascade/weekly_stack.py` (`change_over`,
  `plumbing_week`, `headline_form`) and `daily_cascade/open_note.py` are Weekly
  code. The Weekly passes no `month_aligned`, so its change is as before. Its
  release rows (and the open note's) now read CPI by date. That changes the
  Weekly's CPI year-on-year and prior, to the right figures, for any edition
  whose window spans October 2025.
- **A90's files.** A90 touches `numeral_audit.py`'s binding (lines 1598-1770)
  and `validate_audit_fixes.py`'s end. This branch touches `signed_fields`
  (near line 306) and `role_faults`, and puts its cases in
  `validate_numeral_audit`, `validate_monthly` and `validate_monthly_frames`,
  so the two should merge without conflict.

## Step 5: the gates

Run one at a time on the final code, in the foreground.
`validate_monthly_stack` outruns the 9-minute foreground limit; it ran whole,
alone, in the background with no other gate running, and finished.

| Gate | Result |
|---|---|
| `validate_numeral_audit` | 181/0 (group M added) |
| `validate_audit_fixes` | 135/1: the B84 expectation that fails identically on the unchanged base `d30238ed` (and on main); A91 updates it on A90's branch |
| `validate_monthly` | 370 passed, 1 failed, 1 skipped (group K added). The failure is the refunding-window case, which depends on today's date and fails identically on the base. The skip is the bash+flock rc mapping |
| `validate_monthly_frames` | 48/0 (group G added: M1-M7) |
| `validate_monthly_stack` | 267/0, whole (B97's group flag is not in this base) |
| `validate_readability` | 67/0 |
| `validate_weekly_readability` | 56/0 |
| `validate_weekly_edits` | 91/0 (`headline_form`) |
| `validate_secondary_notes` | 88/0 (the open note's release rows) |
| `validate_weekly` | 101/0, 1 skipped |
| `validate_weekly_calendar` | 44/0 |
| `validate_benchmark` | 32/0 |

No gate was added, so CLAUDE.md's counts are unchanged.
