# Friday stitching: notes (session A, 13–14 Oct 2026)

Friday's merge set is stitched onto main as it stood after the seven merges of
13 Oct (`cc91752`). The stitching is cumulative and in Friday's order:

- branch 1 received `origin/main`;
- each later branch received the one before it, so branch *k* carries main and
  branches 1 to *k*−1.

Friday's merge of branch *k* onto main, with 1 to *k*−1 already merged, is
therefore clean.

## How it was done

- **Merges only.** Every step is a `git merge` with a merge commit. Nothing was
  rebased or force-pushed, and nothing was merged to main.
- **Commit message.** "Merge <predecessor> into <branch> (Friday stitching,
  13 Oct)".
- **Conflicts were resolved by keeping both sides:**
  - CLAUDE.md's gate count is the sum;
  - the Makefile's gate lists are concatenated;
  - `feeds.py` keeps every writer;
  - `weekly_stack.py` and `monthly_macro/stack.py` keep every hook;
  - `reporting_stack.yaml` and `prose.py` keep both sides' keys;
  - the library guide keeps both entries;
  - `validate_prices.py`'s symbol counts and continuous set are the union.
- **`metrics_registry.yaml` was spliced, not hunk-resolved, from branch 8 on.**
  diff3 aligned one branch's new entries with another's field by field, so
  keeping both hunks would have interleaved two entries' fields. The file is
  the predecessor's whole file, with the branch's own changes against the
  merge base applied at their base anchors. Every block stays whole, and the
  counts it shares with other branches were set to the union.
- **Gates run after each merge, one at a time:**
  - the branch's own gate or gates;
  - `check_registry`, `validate_prices`, `validate_gates`,
    `validate_config_refs`, `validate_weekly_stack`, `validate_monthly_stack`
    and `validate_audit_fixes`;
  - any gate a conflicted file feeds;
  - a duplicate-key sweep over `metrics_registry.yaml`, `source_registry.yaml`
    and `config/*.yaml`.

  YAML lets a second copy of a key silently replace the first, which is how
  `imf_ifs` was caught.
- **CLAUDE.md's count against the Makefile.** On main, CLAUDE.md's gate count
  is the Makefile's `PY_VALIDATORS` plus one. That offset is carried unchanged,
  so each count below is the sum of both sides. The final count is
  **seventy-six code gates (seventy-three Python, three shell)**.
- **The Master Guide** (added 19 Oct 2026, master-guide): after the last merge of
  a chain, refresh the Guide's dated parts (its "As of" line, Tables 1, 2, 7 and 9,
  Landing next), regenerate its figures with `tools/figures/master_guide.py`,
  rebuild its HTML edition, and run `tools/check_master_guide.py`.
- **The proof.** On a throwaway branch from `origin/main`, the 23 branches
  merge in order with `--no-ff` and **no conflict**. The resulting tree is
  identical to `el-2-3-rollup`'s. The branch was deleted and never pushed.

## Per branch

"Fix" is a separate commit after the merge. Fixes made inside a merge commit
are named in the row. CI is the run on the branch's pushed stitching tip.

| # | Branch | Merge | Files resolved | Collapsed / cross-branch fixes | CI |
|---|---|---|---|---|---|
| 1 | aq-5-correlation-layer ← main | `57ceaf5`, fix `02d9bd5` | metrics_registry.yaml (both vocab entries; basket 87), validate_prices.py (87), CLAUDE.md (silent → 58/55) | AQ-5's ETH, SOL and ZEC fell to "shares" under main's volume units: now `VOLUME_USD`. Registry: shares 68, usd 4; volume total 75. `validate_book_b_scanner`: GLD's correlation break reads "unmet" where the layer exists | #346 ✅ (#345, the merge alone, failed on that check) |
| 2 | aq-8a-gold-residual ← 1 | `dc91d88` | weekly_stack.py (`plumbing_week` takes `yudd_line` and `auction_block`; the YUDD line and the auctions table), metrics_registry.yaml, CLAUDE.md (→ 59/56) | In the merge commit: main's registry sweep in `validate_monthly_stack` read AQ-8a's yields-up/dollar-down week counts as yields. The regex is now `\byields?\b(?!-)` | #348 ✅ |
| 3 | aq-6-thesis-register ← 2 | `bfd0476` | CLAUDE.md (layout rows both; 60/57), Makefile, monthly_macro/stack.py (`thesis_seed` and the metals block; the slow layer's data keeps `theses_seed` and `correlations`) | — | #349 ✅ |
| 4 | imf-ifs-gold ← 3 | `d55f53b`, fix `0fba959` | none textual | **`imf_ifs` in source_registry.yaml twice**: AQ-8a's `not_yet_sourced` placeholder and this branch's live writer. Kept the live entry. `validate_attribution` accepts the source live; AQ-8a's metric stays `not_yet_sourced` (ruling 2). The branch had added a gate without counting it, so the count is set to the true 61/58 | #351 ✅ |
| 5 | aq-4-horizon-charts ← 4 | `ea444c2` | CLAUDE.md (62/59), metrics_registry.yaml (basket 88 with DBC), validate_prices.py | DBC's volume is shares: shares 69, volume total 76 | #352 ✅ |
| 6 | aq-9a-em-scorecard ← 5 | `c8a426b` | CLAUDE.md (63/60), Makefile, feeds.py (`imf_ifs`, then AQ-9a's four and `em_lenses` last, as its comment requires), monthly_macro/stack.py | — | #353 ✅ |
| 7 | aq-1-quarterly-cadence ← 6 | `62e4929` | CLAUDE.md (64/61), Makefile, reporting_stack.yaml (AQ-1's quarterly keys plus main's new "read" subtitle), prose.py (`voice(ed)` and `summary_figures()`) | In the merge commit: the quarterly cadence gains `summary_figures: 3`, main's T3.4 key, which AQ-1's gate requires | #354 ✅ |
| 8 | aq-3-series-1 ← 7 | `d562599` | Makefile, feeds.py, validate_prices.py (90), metrics_registry.yaml (spliced), CLAUDE.md (→ 65/62) | RB=F and HO=F are futures, so they go in `VOLUME_FUTURES`: contracts 5, volume total 78 | #355 ✅ |
| 9 | aq-3-series-2 ← 8 | `d9c6d37` | feeds.py, validate_prices.py (93), metrics_registry.yaml (spliced; shares 72) | In the merge commit: `validate_aq3_series` no longer hard-codes the basket at 58, since `validate_prices` owns the count | #356 ✅ |
| 10 | sr-36-basis-proxy ← 9 (worktree `../chester-sr36`) | `09ebf68` | CLAUDE.md (66/63), Makefile, weekly_stack.py (the YUDD line, the auctions table and SR-36's line; the basis data in the section's data; positioning: main's two z columns plus SR-36's line) | Carries aq-3-series-2's session-calendar fix by merge order (the SR-43/49 notes' Needs you 6) | #357 ✅ |
| 11 | sr-43-49-rates-anchor ← 10 | `3838c97` | CLAUDE.md (67/64), Makefile, config.py (`FRED_SR43_SERIES` and `GLD_EXPENSE_RATIO`), weekly_stack.py | — | #358 ✅ |
| 12 | sr-37-38-ai-fcf ← 11 | `556ac2f` | CLAUDE.md (68/65), Makefile | — | #359 ✅ |
| 13 | sr-38-inbox ← 12 | `f7a90a8` | CLAUDE.md (69/66), Makefile, **deploy/systemd/chester-backup.service** (`ReadWritePaths` gains both `inbox/spdji` and `inbox/etf`), validate_backup.py (two copyto lines; the unit may write the three inboxes and nothing else) | — | #360 ✅ |
| 14 | b3-tranche-a ← 13 | `7d17dcb` | CLAUDE.md (70/67), feeds.py, yfinance_source.py, weekly_sections.py, weekly_stack.py, monthly_macro/stack.py, validate_monthly_stack.py (both branches made the same bucket filter), validate_prices.py (94; continuous set of eight), metrics_registry.yaml (spliced) | In the merge commit, two fixes. (a) Main's Weekly Ahead wants every calendar row to carry a class with a channel, so Tranche A's rows now carry `cls`, under four classes declared in `config/weekly_ahead.yaml` (ruling 3). (b) `validate_batch3_a`'s filler check reads batch 3's own sub-sections only (ruling 1) | #361 ✅ |
| 15 | aq-2-chapters-1 ← 14 | `a139aa5`, fix `3d8c8ec` | none textual | `validate_quarterly_stack`: with AQ-4 present the long frame is drawn, and with AQ-5 and AQ-8a present item 6 reads the store. The checks ask `quarterly_items.module()` which branches are present | #362 ✅ |
| 16 | aq-2-chapters-2 ← 15 | `1473c02`, fix `707cb76` | none textual | The same, for the IMF IFS, SLOOS and AQ-3 part 1 hooks: "nothing stored" once the keys are registered | #363 ✅ |
| 17 | aq-7-quarterly-scan ← 16 | `e0dde3f` | Makefile, CLAUDE.md (→ 71/68) | — | #364 ✅ |
| 18 | c1-move-screen ← 17 (worktree `../chester-c1`) | `b834c26` | CLAUDE.md (72/69), Makefile, config.py, derived.py, stack.py, weekly_stack.py (`misfit_week` takes `screen` and `dates`/`st`/`now`; `em_week` and `tag_facts`; main's précis page), validate_prices.py (106; volume total 91), metrics_registry.yaml (spliced; FRED signal 27, shares 82) | **SR-46's six EM currencies were already AQ-3's keys**, with the same keys and FRED ids: usd_brl, zar, inr, krw and twd in `FRED_FX_SCAN_SERIES`, usd_thb in `FRED_THAILAND_SERIES`. Kept AQ-3's copies and dropped c1's six; c1's two EM OAS stay. `derived.py`'s unit map has each currency once | #365 ✅ |
| 19 | crypto-basket ← 18 | `1c52636` | yfinance_source.py, weekly_stack.py, monthly_macro/stack.py, validate_prices.py (continuous: four coins, four FX pairs and the twelve basket symbols), metrics_registry.yaml (spliced), CLAUDE.md (→ 73/70) | In the merge commit: **two `volume_series()` functions**. The crypto branch's, defined later, silently replaced main's and would have stopped the market basket's volume. Now one function covers both baskets under main's zero rule. The crypto parser's own volume lines, an undefined name after the merge, are removed. `validate_crypto_basket` holds both baskets | #366 ✅ |
| 20 | aq-10-validators ← 19 | `a279e37` | Makefile, validate_quarterly_stack.py (AQ-10's kill-state column plus the presence-aware hooks), CLAUDE.md (→ 74/71) | `validate_quarterly_gates` passes 95/0 with **0 skipped**: all seven "activates on merge" checks now run | #367 ✅ |
| 21 | lib-aq14-em-paper ← 20 (worktree `../chester-reports-library`) | `c564582` | white-paper-library-guide.md: the masthead line, twenty-seven documents; total 426,000 words (main's 408,000 plus the EM paper's ~18,000). `check_library`: 27 papers, 0/0 | — | #368 ✅ |
| 22 | el-1-packets ← 21 | `544c115`, fix `acb0786` | none textual; CLAUDE.md → 75/72 | — | #369 |
| 23 | el-2-3-rollup ← 22 | `8020a18`, fix `79b2dba` | none textual; CLAUDE.md → 76/73 | — | #370 |

This notes file is one commit on aq-10-validators. It was then merged forward
into 21, 22 and 23, so each still carries everything before it, and the proof
was re-run on those tips. Those CI numbers are in the session report.

## Should be ruled before Friday

1. **SR-43/49's anchors line trips the bare-figure filler rule.** Checked
   against `stack_prose.filler_faults`, the line reads: "The 10-year's anchors:
   … ACM term premium 1.03% (as of 2026-10-09). (descriptive; unvalidated,
   n=0)". Neither the rule nor the line was changed. Batch 3's gate now checks
   only its own sub-sections.
   - Rewrite the line (SR-43/49's owner).
   - Or exempt code-written tagged lines from the filler rule.
2. **AQ-8a's `imf.ifs_official_gold_oz`** is still `not_yet_sourced`, while
   imf-ifs-gold now writes `imf.ifs.gold_reserves_oz.*` for each country.
   - Point the two-bid decomposition's official leg at the writer's series.
   - Or keep it `not_yet_sourced` until AQ-8a's own follow-up.
3. **The Ahead classes for Tranche A's calendar rows (session-set):**
   - `boj_decision`, tier 2;
   - `treasury_buyback`, `jgb_auction` and `weekly_release`, tier 3.

   Each has a channel line and amplifiers. Keep, or retier.
4. **The backup unit changes** (`chester-backup.service` `ReadWritePaths`).
   - After the merges, the self-deploy copies the unit. It is the sweep's
     oneshot, so no restart should be pending. If the heartbeat names
     `restart_pending`, the restart is yours.
   - `~/chester-data/inbox/spdji` and `~/chester-data/inbox/etf` must exist
     (`mkdir -p` once), or their pulls are skipped.
5. **Keep Friday's order, and nothing else onto main first.**
   - Branch *k* already carries 1 to *k*−1. Merging out of order would bring
     the earlier branches in with it, unreviewed in that position.
   - A merge to main after `cc91752` and before Friday would need these merges
     redone from where it lands.
   - el-1 and el-2-3 are last, so dropping them after Audit #4 leaves the other
     21 untouched.
6. **The basket is now 106 symbols**, plus the twelve crypto-basket coins on
   their own pull.
   - Each branch's notes carry its own backfill command for its new symbols.
     Run them after Friday's merges, inside the windows.
   - The eod pull grows from 81 symbols to 106: under a minute more at its
     0.5-second pacing plus the fetches, inside `chester-eod.service`'s timeout.
7. **The crypto basket's volume now follows main's zero rule.** A day Yahoo
   reports 0 is not stored, where the crypto branch stored it. MW-7's turnover
   test reads gaps as absent, not as zero turnover.

## Not done here

- No full `make validate` locally. Each merge ran the gates above, and CI ran
  the full list on every pushed tip.
- Nothing was run on the box, and no unit was started, stopped or restarted.
- `.env`, the ledgers and the register's live tables were not touched.

**A worktree slip, reported.** `../chester-reports-t3` was listed on
`sr-38-inbox` at the start but had since moved to `alpha-lab-1`, presumably
another session's work. My merge script switched it to `sr-38-inbox` before I
saw that.

- I aborted the merge there and put the worktree back on `alpha-lab-1` at
  `70dbfe8`. It was clean, and nothing was lost.
- `sr-38-inbox`'s merge was done in the main checkout instead.
- The script now refuses to switch a sibling worktree's branch.
