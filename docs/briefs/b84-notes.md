# B84 notes: the Monthly's tape_rules, bare_delta and state_misstated withholds

Paste B84 (`docs/pastes/B84.md`), 28 Oct 2026. Branch
`b84-monthly-tape-delta-state`, base origin/main at `f380e12e`. Merges Thursday by
its own PR, after A88's, before the 23:30 ET freeze.

The evidence is the box's dry run of 28 Oct (main at `f380e12`), read from the
laptop copy of its log (outside the repo, not committed). Each section's both
attempts were read verbatim.

## Per section

### month_in_markets (bare_delta): class (iii)

- **Attempt 1:** withheld for the separator ("'83553.85' (write '83,553.85', as the
  tables print it)"); the retry fixed it.
- **Attempt 2:** withheld for "payrolls rose +29,000 against a 4.2% unemployment
  rate": "a change of 10,000 or more printed without its unit or scale (+29,000)
  -- copy its change_display or latest_level_display verbatim".
- **Cause:** the check is right. The display rule and `validate_monthly_frames`
  group A both hold the payroll change to "+29,000 jobs", and the bare integer is
  refused by design. The writer dropped the noun. The bare delta first appeared
  on attempt 2, the last one, so no retry ever told the writer which string to
  copy, and the retry message as written would not have said so either.
- **Fix:** the bare-delta reason now quotes the frame's own display for each bare
  figure, `prose.bare_hint`: "...; write '+29,000 jobs' for +29,000". This is the
  same as the separator message, which already quoted its form. Where the frame
  carries no display, it says to write the figure with its noun or scale. The
  check is unchanged.
- **Fixture:** `validate_monthly_frames` group F. The hint quotes '+29,000 jobs';
  the dry run's sentence shape through the writer is withheld with that hint.
- **Next dry run:** whenever the bare delta comes up on attempt 1, attempt 2 is
  told the exact string. If it comes up only on attempt 2, as on 28 Oct, the
  section is still withheld. That is right: the check stays.

### block:positioning:cftc (bare_delta): class (ii)

- **Both attempts:** "Net speculative contracts in 10-year note futures ran /
  stood at −964,293 as of 2026-10-20 ...", withheld "(−964,293) -- copy its
  change_display or latest_level_display verbatim".
- **Cause:** the block's data, `stack.positioning_history`, carried the raw
  `latest` (−964293.0) and no display form. The retry pointed at a field the
  block did not have, so attempt 2 repeated the bare level. A signed count of
  that size without its noun is the rule's case, so the check is right.
- **Fix:** `positioning_history` writes `latest_level_display` for a count series
  with a noun: "−964,293 contracts", through `stack.count_level_display`, which
  uses the bare-delta rule's own noun table. Series with no noun get none.
- **Fixture:** `validate_monthly_frames` group F. The display is built. The dry
  run's attempt-2 sentence is withheld, its retry naming '−964,293 contracts',
  and the draft that copies the form publishes.
- **Next dry run:** the block's frame carries the form, and a bare first draft's
  retry names it.

### summary:narratives (bare_delta): class (ii)

- **Both attempts:** "China's official gold holdings (SAFE) rose +740,000",
  withheld "(+740,000)".
- **Cause:** `safe.gold_reserves_oz` is stored as `units: count` and had no noun
  in `numeral_audit.DISPLAY_NOUNS`. Its display was the bare "+740,000", and the
  writer copied exactly what it was given. A change in troy ounces printed without
  "ounces" is a wrong sentence, so the check is right.
- **Fix:** `DISPLAY_NOUNS` gains `safe.gold_reserves_oz` and
  `imf.ifs.gold_reserves_oz.` → "ounces". The display is now "+740,000 ounces",
  and the bare-delta rule passes that form (it accepts the table's nouns).
- **Fixture:** `validate_monthly_frames` group F. The noun is on both keys. The dry
  run's sentence is still withheld, and the same sentence with the display
  copied passes.
- **Next dry run:** the summary's cited figure reads "+740,000 ounces".

### theme:sentiment (state_misstated): class (i)

- **Both attempts:** "...both measures of inflation expectations pushed higher ...
  That combination, depressed sentiment alongside rising inflation expectations,
  ...", withheld "inflation is called rising, stored stable".
- **Cause:** the state check's "before" form (`narrative.state_contradictions`)
  reads "rising inflation" as a claim about the inflation dimension. The sentence
  says the expectations rose (Michigan +10 bp, the NY Fed +6.3 bp), which is true,
  and says nothing of the dimension's state. This is a false positive.
- **Fix:** narrow. The "before" form no longer matches when the name heads
  "expectation(s)" (`NOT_THE_STATE`). Every other form, and every other phrase,
  is unchanged. The check lives in `daily_cascade/narrative.py`, not
  `monthly_macro/prose.py` or `stack.py`, so that is the file edited.
- **Fixture:** `validate_monthly`. The dry run's sentence passes, while "rising
  inflation" and "inflation is rising" against a stored stable still fail.
- **Next dry run:** the sentence publishes. The true state ("stable") sits in the
  payload's market states, `prose._market_states`.

### looking_ahead (tape_rules): class (i)

- **Attempt 2:** "December closes the quarter with its own concentration of risk:
  ISM Manufacturing on the 1st, ISM Services on the 3rd, payrolls on the 4th ...",
  withheld "role audit failed on 2 figures -- ... 'closes ... 1st': 1st is Bitcoin
  fee, one-hour tier (sat/vB)'s Long-run average ...; 'closes ... 4th': 4th is
  10-year yield's 40-week average".
- **Cause:** the tape_rules outcome is the T3.6 role audit (M1), reached through
  `prose.t36_faults`. "Closes" is the verb "ends", and 1st and 4th are days of the
  month, which can never be a close. This is a false positive.
- **Fix:** in the Monthly's wiring, not in the role audit. `t36_faults` blanks every
  ordinal that is not a percentile's (no "percentile" within 40 characters)
  before calling `numeral_audit.role_faults`. `role_faults` is untouched (A88's).
- **Fixture:** `validate_audit_fixes` group J. The dry run's sentence passes
  `t36_faults`, while `role_faults` alone still binds it, so its rule is shown
  unchanged. "SPY closed September 2026 at 721.82" against a 40-week average of
  721.82 is still withheld, beside a masked ordinal too.
- **Next dry run:** the calendar paragraph publishes.

### stack:tape (tape_rules): class (ii)

- **Attempt 1:** "SPY closed September 2026 at 721.82, QQQ at 670.83, and IWM at
  277.22, with the 10-year yield at 4.48 against the 30-year at 5.02. DXY ended the
  month at 99.35. ...". Withheld by the numeral audit's binding ("5.02 is bound to
  10-year yield but belongs to 30-year yield"), which is A88's series binding.
- **Attempt 2:** the same paragraph. Withheld as filler ("'DXY ended the month at
  99.35.'") and by the role audit: nine figures, every one a 40-week average
  written as a close.
- **Cause:** the draft is wrong. QQQ's 670.83 is its 40-week average, and
  month_in_markets prints QQQ's September close as 739.77. The likely reason is
  the data. `level_book` reads the level list at the month-end session, and
  `levels.instrument` sets the long frame's close (`frame.last`) only when the
  bars store holds a daily bar dated exactly that session. The draft cites no
  close at all, only the nine averages, which fits every close having been null.
  That cannot be confirmed from the laptop.
- **Fix:** a long-frame row with no close now carries `close_absent` ("no
  month-end close is stored for this market: write no close for it"). The tape's
  frame note says that a null close means no close this month: never "closed",
  "ended" or "at" beside an average; name the average as one, or leave the
  market out. The role audit and the filler rule are unchanged.
- **Fixture:** `validate_audit_fixes` group J. A null close carries
  `close_absent`, a held close does not, and the tape's note names it.
- **Next dry run:** either the closes are held and the writer cites them, or
  they are absent and the writer cites the averages as averages. Attempt 1's
  5.02 binding is A88's.

**Verify on the box:** whether the tape's `long_frame` closes were null in the
dry run. Read the edition JSON under `reports/dryrun/`: `sections[id=tape].data.
long_frame[*].close`. If they were, why the bars store has no daily bar at
2026-09-30 is a separate question, for the level list and not for this paste.

## Gates

Run one at a time, in the foreground:

| Gate | Tally |
|---|---|
| validate_monthly | 360 passed, 0 failed, 1 skipped (run_monthly.sh rc mapping: no bash+flock on the laptop) |
| validate_monthly_frames (the Monthly prose frames' gate) | 39 passed (group F new, 7 checks) |
| validate_numeral_audit (DISPLAY_NOUNS touched) | 172 passed |
| validate_stack | 84 passed |
| validate_readability | 67 passed |
| validate_audit_fixes (owns the role checks) | 106 passed (3 new) |
| validate_narratives (owns state_contradictions) | 103 passed |
| validate_monthly_stack (stack.py) | not finished: the laptop stopped the run for low memory after 72 lines of output, with no FAIL among them; CI runs it |

## Against A88

A88 owns `numeral_audit.series_bindings` and the role audit, and its branch was
not pushed when this was written. B84 touches neither function:

- In `altdata/numeral_audit.py`, only `DISPLAY_NOUNS` changed (two entries),
  which is the bare-delta rule's table.
- The ordinal masking sits in `monthly_macro/prose.py` `t36_faults`, before the
  call to `role_faults`.

If A88 changes `role_faults` to read dates or ordinals itself, the mask is
redundant but harmless. If A88 edits `prose.t36_faults` or the bare-delta branch
of `write_all`, the PRs will touch the same lines, and B84 merges second.
