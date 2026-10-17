# weekly-fixes-7: the Weekly's fixes from dry run 7 (17 Oct 2026)

Branch `weekly-fixes-7` from `origin/main` at `de0c027` (post-friday-fixes merged).
It merges on **Monday, after docs-batch-9**, and the Tuesday stitch carries it
into the second chain. `writer-fixes-1` branches from its tip and merges after it.
Nothing here is a box write; every box step is printed below for Ari.

**Additions only against Monday's chain.** I ran a trial merge (`git merge-tree`,
which writes nothing) against `docs-batch-9`, `aud-3a-catalogue`,
`aud-3b-security-master`, `aud-3c-quality` and `aud-3d-fred-history`, and every
one is clean. Against `6b-dealer-1`, `6b-dealer-3` and `st-r5-audit` the one
conflict is `CLAUDE.md`. That conflict already exists between `origin/main` and
those branches; this branch does not touch `CLAUDE.md`. Two choices kept the
merges clean:

- The signed-zero rule sits beside `numeral_audit.py`'s other signed helpers,
  not at the end of the file, where aud-3b and st-r5 both append.
- The three `KNOWN` lines added to `tools/validate_systemd_units.py` for the
  Saturday unit's caps are **byte-identical** to aud-2's, so git takes them as
  the same change.

The critique (`docs/briefs/dryrun-weekly-run7-critique-2026-10-17.md`) is not in
the repo; the faults below are the paste's list.

## The faults and their fixes

### 1. Units: DEX and net GEX are dollars (the one real error)

**What the engine computes** (`tools/exposure_compute.py`, `_profile`):

- `notional = gamma x contracts x spot`, summed with the dealer sign into
  `net_gex`;
- `dex_strike += pos x delta x contracts`, so `dex_shares`, and
  `dex_notional = dex_shares x spot`.

The close's scorecard stores `net_gex_close = exp["net_gex"]` and
`dex_close = exp["dex_notional"]` (`daily_cascade/stack_close.py`).

**The decision.**

- **The printed DEX is dollars** (delta notional). 205.62bn / 763 ≈ 269m shares is
  `dex_shares`; the figure printed was `dex_shares x spot`.
- **The printed net GEX is gamma x OI x 100 x spot.** The registry has always
  called that `usd_per_point`: dollars of delta the hedge changes by for a $1
  move. One hundredth of it is shares per 1% move (`exposure.shares_per_1pct`).
  It was never shares per 1%.
- **The number is right and the label was wrong**, so only the label, the
  appendix and the gate change. The engine is untouched, as the coordination
  with session A's 6b-dealer-1 asked.

**The fix.**

- The table cell prints `+$205.62bn` / `−$0.34bn` (`weekly_sections.money_bn_signed`,
  rounded before the sign is taken).
- The appendix rows say "$ of delta per $1 move" and "$ (delta notional)".
- A new glossary entry, "net GEX, DEX", says both are dollars and what one
  hundredth of net GEX is.
- The registry already agreed (`exposure.net_gex: usd_per_point`,
  `exposure.dex_notional: usd`).
- I did not change the column heads: session A's hunk rewrites the line beside
  them, and a change there would conflict.

**The bounds gate** (`weekly_sections.dealer_bounds`, `validate_weekly_complete` M1):

- |DEX| ≤ sum of OI x 100 x spot.
- |net GEX per 1%| (net_gex x 0.01) ≤ sum of OI x 100 x spot x 0.01.

Both are in dollars, the units the series are stored in. On a fixture chain run
through the real `_profile`, both hold. The printed DEX also exceeds the *share*
bound (sum of OI x 100), which shows the old "shares" label was impossible.

### 2. The read's "Also this week": deduped

An attribution is stored once per story it supports, so the same quote reached
the bullets once per story. `weekly_sections.dedupe_attributions` keeps one per
(url, claim text, whitespace and case folded). Gate M2: six attributions (three
items, each twice) print three bullets, and no two share a url and claim.

### 3. Two "week" figures for the 10-year

The SR-6 table had seven columns, so the renderer's six-column rule split it in
two, and the second table carried only the dates. Now:

- the window prints **inline**: "10y, week (7 Oct to 14 Oct)";
- the table has six columns;
- the sub-section adds the line "FRED's legs lag two sessions (to 14 Oct); the
  nominal week in the tape runs to 16 Oct." It counts sessions on the trading
  calendar, reads the tape's end from the `y10` bars, and prints only when the
  two windows differ.

The same table note named `altdata/rates_attribution.py`; it now says "the rates
attribution block's". Gates: M3, and `validate_batch3_a.py` updated (60/0).

### 4. Watching's age against section 4's

Watching printed `persistence_days`, while section 4 recounts the gap's run over
the stored objects (`state_dates`). Those are two counters, and the Watching one
was the stale one. Watching now reads `state_dates(...)[id]["sessions"]`, the
gap table's own counter, and falls back to `persistence_days` as the gap table
does. I left the misfit section's `dates=` line alone because session A rewrites
the line above it; Watching computes the same function separately. Gate M4: on a
fixture both print 15 and 13.

### 5. Resolved prediction-market questions

The store carries no resolved field (the fetchers keep open markets only). So
`prediction_markets.resolved()` decides from what is stored. A contract is
resolved when either:

- its decision date is before the edition's day; or
- its question names a monthly release and a month (CPI, core CPI, PCE, core
  PCE, payrolls, the unemployment rate), and that release's month is already in
  the store at the cutoff (`fred.core_cpi` for 2026-09 is there by 14 Oct).

A resolved contract prints "resolved: Yes/No" where the market gives an outcome
(a price at 99% or 1% and beyond); otherwise it **drops from the table**.
"Will Core CPI MoM be 0.2% in September?" at 51% drops. Gate M5: one resolved
and one live contract give one row; a settled one prints "resolved: Yes".

### 6. The book's opener, and "Stance:"

**The decision: the week's figure is computable, so it is printed.** Portfolio
Truth's NAV has daily marks and Book Z's ledgers are marked daily, so
`benchmark.week_line()` reads one window for all four: the NAV on or before the
prior week's close, to its newest. The book's "Against Book Z" item now reads
"on the week (… to …): the book +x%; cash …, SPY …, 60-40 …; excess …; since 5
Sep: …".

The audit is in force as well. `stack_prose.book_window_faults` withholds a book
paragraph that says "this week", "the week" or "week's" when the book's data
carries no week window. That case is a week where the NAV had no mark before the
week began.

"Terms:" in the book is now "**Stance:**" (`precis.terms_line`); "Terms" stays
the glossary box's name. Gates: M6, and `validate_weekly_storyline` E (30/0).

### 7. The précis's two lines

**The decision: both lines were true, of different stores.**

- "What changed in the outlook" compares with the **archived** editions, which
  carry no précis before the first live one.
- The stance line's n counts graded stances wherever they were recorded,
  **dry runs included** (`dryrun.weekly_stance`).

So in a dry run, n=1 and "first edition" sit side by side. The line now says
"First archived edition with a précis.", naming the store it read. In the first
live edition both will say "first". Gate M7; `validate_weekly_storyline` updated.

### 8. "The nine AI names" over five rows

The count is the config's list, in words ("nine" while the list has nine). Every
listed name has a row; a name with no stored estimate prints "not stored". Gate
M8: nine named, nine rows, four of them "not stored".

### 9. The Saturday price pull

The new `chester-prices-saturday.timer` and `.service` run
`scripts/run_prices_saturday.sh` on **Saturdays at 06:00 ET**: `git pull
--ff-only`, then `python -m altdata.feeds pull --only prices`.

- **The reason:** a continuous symbol's bar is stored once its UTC day ends, and
  Friday's ends at 20:00 ET, after the last weekday pull. The timer's comment
  and README's new section say so.
- **The pattern:** the crypto basket unit's (EnvironmentFile, the sandbox,
  ReadWritePaths).
- **Caps:** percentages, per the 4 GB ruling of 17 Oct as session A applies it
  (`MemoryHigh=15%`, `MemoryMax=19%`, about 600M / 760M), and
  `OOMScoreAdjust=500`, because a price pull can be run again.
- It is in `DEPLOY_TIMERS`. The systemd gate passes (90/0). **I did not enable
  it.**

### 10. Item 40's forward leg: withdrawn

- `spdji.WITHDRAWN = "not tracked (source withdrawn)"`.
- The forward split line and the index revision line print it wherever no drop
  is stored, which is always, now.
- `spdji` is off `feeds.EXTERNAL_WRITERS`, so the heartbeat stops listing it as
  pending.
- `source_registry.yaml` `spdji` is `status: retired`, with the reason.
- The three `spdji.*` metrics carry `tracked: false` and
  `not_tracked_reason: source withdrawn`.
- The Weekly's text no longer names `chester-vendor-checks/spdji`.
- The parser and the forward-split code are kept, unchanged: nothing else of
  item 40 changes. The index cluster prints its trailing (Shiller) leg.

**One leftover, deliberately:** the sweep line `pull_inbox_file spdji
sp-500-eps-est.xlsx` in `scripts/rclone_sync.sh`, and `validate_backup.py`'s
check of it, stay. Monday's aud-2 rewrites exactly that part of the sweep and of
that gate, so removing them here would conflict. The line copies a file that
will never exist, so it is harmless. Part 2 (`audit-leftovers-1`) is built on
the sweep and removes it there. Gates: `validate_sr38_inbox.py` (53/0) and
`validate_ai_fcf.py` (27/0) updated.

### 11. Internal names in the reader's edition

**The rule** (`readability.internal_name_faults`) forbids, in a reader's line, a
file path, a branch, a Python exception and a symbol string (`EURCHF=X`, `HG=F`,
`^TNX`). A "not yet stored" line names the source and the date it starts,
through `readability.starts_line(source, now)`: "(Yahoo Finance, from 19 Oct)".
The date is the next NYSE session, when the daily writer next runs.

**Lines rewritten:**

- ECB legs (`EU_WRITER` is now "the ECB's data portal");
- EUR/CHF;
- Japan's reserves;
- FIMA repo;
- SOFR/IORB, copper and the FX rows;
- SR-6's table note.

**The renderer's net** (`readability.reader_safe`) is applied to every
not-tracked and section line, and to "Chart unavailable: …". It turns an
exception into "the last read failed" and drops a path or branch parenthesis.
This catches what a stored STALE reason carries (dry run 7's `HTTPError`).

The footer's run id prints to the second (`stack_render.run_id_display`). The
stored id keeps its microseconds, and the archive line keeps its path. Gate M11.

### 12. The small fixes

- **Volatility:** MOVE's and SKEW's Context is their five-year percentile, as the
  VIX's is, and an "As of" column carries every row's date. The section data
  carries `move_percentile_5y` and `skew_percentile_5y`, so the numeral audit
  finds them.
- **Signed zeros** are fixed at the source: every formatter now rounds before
  taking the sign.
  - `stack._signed`: "0 bp".
  - `stack._change`: a sub-unit raw change keeps two places ("−0.12" days to
    cover, which printed "−0"); one that still rounds to zero is "unch".
  - `weekly_sections._bn_change` and `batch3_block._usd_bn_signed`: "unch".
  - `batch3_block._bp`: "0.0 bp".
  - `readability._pts`: "0.0".

  `numeral_audit.signed_zero_faults` is the rule, and the prose audit chain
  withholds a paragraph that prints one.
- **Voices:** one line. The collapse adds "n unreachable" to "Voices this week:
  …" instead of printing a second line, and keeps the old line only where there
  is no status item.
- **The footnote rule:** `readability.fold_repeated_gaps` turns a gap phrase in
  two or more cells into one footnote and blank cells. It is applied to the
  earnings table ("revenue not stored") and Ahead ("release time not captured").
- **JST in ET:** `calendar_config.to_et` converts at row creation. "12:35 JST" on
  20 Oct prints "23:35 (12:35 JST)" on Mon 19 Oct, under both "Time (ET)" heads.
  The BoJ's "about 12:00 JST" converts the same way.
- **"Read in Plumbing & rates"** replaces "resolved by". The status vocabulary
  is now `("read in", "carried", "stale")`, because the line never checked that
  the gap had closed.

Gate M12.

### 13. Charts (within the existing budgets)

- **Positioning gauges:** each panel is titled with its series' short name
  (`charts.short_title`: before any parenthesis, at most 24 characters). The
  long names stay in the caption.
- **Leadership bars:** a bar within 70% of the longest carries its label inside
  itself, in white.
- **Odds chart:** the legend sits below the plot (the figure is 0.6in taller).
  The fed-funds ticks read "Oct 28" (`charts.meeting_label`).
- **Page breaks:** no CSS forced a break. Figures avoid breaking inside, so a
  tall chart moved whole to the next page and left the previous one half blank.
  Two changes:
  - print CSS caps a chart's height at 95mm (about a third of a Letter page), so
    a figure fits the rest of a page far more often;
  - the two SPY charts (W1, W2) print **half width, side by side**, in a
    two-cell table (`stack_render.charts_seq_html`; email-safe).

The word count is unchanged. Whether the page count falls is for the next dry
run's PDF, which CI and the box render, not this laptop. Gate M13 renders the
W5, W9 and W10 fixtures.

### 14. Tables of gaps

- The crypto basket with nothing stored prints one line: "crypto basket: not
  stored; first pull 17 Oct" (the day after the as-of, since its writers run
  daily).
- The general rule (`readability.collapse_gap_detail`, applied to every Weekly
  detail table): a reference table whose every cell after the row's name is a
  gap prints "<title>: not stored."

Gate M14.

## Gates

| Gate | Run | Result |
|---|---|---|
| `validate_weekly_complete.py`, new group M (M1–M14), run alone | local | 32 passed, 0 failed |
| `validate_weekly_storyline.py` | local | 30 / 0 |
| `validate_batch3_a.py` | local | 60 / 0 |
| `validate_sr38_inbox.py` | local | 53 / 0 |
| `validate_ai_fcf.py` | local | 27 / 0 |
| `validate_systemd_units.py` | local | 90 / 0 |
| `check_registry.py` | local | OK |
| the whole of `validate_weekly_complete.py`, and every other gate | CI | see below |

No gate reads the live store, fetches or calls a model.

## Box commands, for Ari (after Monday's merge; printed, not run)

The self-deploy enables `chester-prices-saturday.timer` at its next tick after
the merge, because it is in `DEPLOY_TIMERS`. To confirm, inside a window:

```
ssh vps systemctl --user list-timers chester-prices-saturday.timer
```

If it is not listed after an hour, the operator's enable (a unit command, yours):

```
ssh vps 'systemctl --user daemon-reload && systemctl --user enable --now chester-prices-saturday.timer'
```

Its first run is Saturday 24 Oct, 06:00 ET. The Sunday 25 Oct Weekly should then
print Friday's FX and Bitcoin as current.

## Files shared with the open branches

Session A's 6b line (`6b-dealer-1/2/3`) touches the mechanics table and the
appendix. The exact lines on this branch:

| File | This branch's lines | Session A's |
|---|---|---|
| `daily_cascade/weekly_sections.py` | `dealer_week`'s `bn()` body, 379–383; the rest are other functions (watching 771–784, `_bn_change` 1053, plumbing/FX lines 1240/1270/1311, volatility 1355–1404, earnings 1598–1607) and the appended helpers from 1609 | `flags_for`, and `dealer_week`'s `rows.append`, columns and `scored` lines (from about 389) |
| `config/reporting_stack.yaml` | `technical_appendix` rows 605–606; storyline comment 616 | `dealer_flags` / `dealer_block` blocks |
| `daily_cascade/weekly_stack.py` | `build`: the Book Z lines 1848–1851, the Watching call 1878–1881, the detail collapse 1967–1970 | `mechanics_week`, the `mechanics` line of `built`, `chart_plan` / `PLACE`, `produce` |
| `daily_cascade/stack_prose.py` | the new audits 524–547; one line after `excess_faults` in `write()` (1053–1054) | `SECTION_NOTES`, `section_prompt`, one line after `filler_faults` in `write()` |
| `daily_cascade/charts.py` | `bars_chart` and the new helpers 385–440, `z_panel` 597–621, `w10` 831–868 | `index_carry`, `dealer_chart` (from about 984) |
| `metrics_registry.yaml` | the three `spdji.*` entries 1309–1343 | new `exposure.*` / `dealer.*` entries |
| `tools/validate_weekly_complete.py` | `weekly_fixes_7()` before `main` (146–459), one call line (468) | the docstring (42–47) and the end of `main` |
| `tools/validate_systemd_units.py` | `KNOWN` 95–98, identical to aud-2's | — |

Trial merges with each are clean apart from the `CLAUDE.md` conflict that main
already has with them, and, since the CI fix, one in `tools/validate_batch3_a.py`
against `st-r5-audit` / `6b-dealer-3`. The ECB-legs check had to stop pinning
the branch name (item 11), and st-r5 inserts `group_b_daily()` on the next line.
For the Tuesday stitch, keep this branch's check, then st-r5's call.

## Needs you

1. **Nothing to approve before Monday's merge.** The timer enables itself at
   the self-deploy after the merge.
2. **Item 10's sweep line** goes in Part 2, not here (above). Nothing for you to
   do.
3. **The page count** is for the 25 Oct dry run's PDF to show.

## CI

| Run | Commit | Result |
|---|---|---|
| 39071512524 (Gates, push) | `cf2b6d9` | **failed: 78 of 82 gate jobs passed** |

**The four failures, all fixed on this branch:**

1. `validate_readability.py`: TypeError. `readability.PRINT_CSS` is a
   %-format string, and item 13's `max-width: 100%` needed `100%%`.
2. `validate_batch3_a.py`, two checks that pinned the old text:
   - the ECB legs' not-stored line named the branch (now the source and the
     date, as item 11 rules);
   - the MoF reserves row's date. Item 12 now prints it in ET: Mon 9 Nov 08:50
     JST is **Sun 8 Nov, 18:50 EST** (US daylight time ends 1 Nov), "the evening
     before in New York", as the config's own note says.
3. `validate_weekly_stack.py`, two checks:
   - "basis points whole" pinned `−0 bp`, the signed zero item 12 removes; it
     now pins `0 bp`;
   - "one audited call per section" counted 11 calls for 9, two retries. The
     book's time-word audit (item 6) fired on the fake model's paragraph. It was
     **too broad**: the book's tables carry week figures of their own (trades,
     sitting time), so a "this week" about those needs nothing. The audit now
     fires only on a sentence that states the book's *performance* (a return, a
     benchmark, "excess") with a week word, when the book's data carries no
     week window.
4. `validate_audit_fixes.py`: run 5's real book paragraph, "The book held its
   ground relative to cash on the week", over figures since 1 Oct, is exactly
   dry run 7's fault, so the audit withheld it. The gate's fixture now carries
   the week's window beside since-inception, as the pipeline prints it from
   this branch, and the paragraph publishes for the reasons that gate tests.

Locally after the fix: `validate_batch3_a` 60/0, `validate_audit_fixes` 73/0,
`validate_weekly_stack` 70/0, group M 32/0. `validate_readability` renders PDFs,
so it is left to CI.

| Run | Commit | Result |
|---|---|---|
| 39072463041 (Gates, push) | `a5e38e5` | **passed: 82 of 82 gate jobs** (76 code, 6 data) |

Read once; green. (`writer-fixes-1`, which carries this branch, is green too: run
39072731374.)
