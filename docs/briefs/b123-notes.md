# B123 notes: the Reporting System paper's Appendix A, drafted after the merge week

Paste B123 (`docs/pastes/B123.md`), 2 Nov 2026.
- **Branch:** `b102-readable-editions-register`, from `cf3f363c`.
- **Source tree:** `origin/a105-merge-week-rehearsal-2` at `b8023fba`. It was read through its worktree and never merged.
- **The draft:** `docs/briefs/reporting-system-appendix-a-draft-2026-11.md`.
- **The paper is not edited.**

## Two things to know before reading the table

**1. The 19 October appendix is on main, not on chain-2.** The paste says the
19 October appendix was "read from chain-2's ab27c07". Chain-2 at `ab27c074` holds an
older edition, "as of 9 October 2026". The 19 October text is on main (`422ea697`),
at line 862, and it names `ab27c07` as its source tree. So the diff below is against
main's text, which is the one the paste means.

**2. The rehearsed tree already has a newer edition.** It carries an "as of
24 October 2026" appendix, written from chain-7 and the feed repair. It arrives on
main with chain-8.

The draft starts from that edition's values, re-reads each value from the tree's
files, and marks it against 19 October. So many "(changed)" and "(new)" marks belong
to chain-7, not to this week's branches. The branch column says which.

## The sections drafted

| Section | Lines | (changed) | (new) |
|---|---|---|---|
| Heading and preface | 8 | 1 | 0 |
| Timers the deploy enables | 17 | 6 | 0 |
| Timers the operator enables | 16 | 3 | 2 |
| The calendar | 6 | 2 | 3 |
| Gates (with CI, the pins and the names gate) | 7 | 2 | 3 |
| Operating windows | 1 | 0 | 0 |
| The stack's budgets | 20 | 1 | 2 |
| Charts | 17 | 2 | 0 |
| Thresholds | 25 | 1 | 12 |
| Price-source families and the EDGAR gaps | 10 | 0 | 1 |
| Publication-lag families | 1 | 0 | 1 |
| DTH-1 | 7 | 0 | 1 |
| Dealer scorecard, calibration ledgers, vendor writer | 13 | 0 | 0 |
| Alpha Lab family registry | 1 | 0 | 1 |
| Risk limits and attention | 9 | 1 | 0 |
| Prose and audits | 4 | 3 | 0 |
| Sources | 13 | 5 | 2 |
| The source registry | 14 | 0 | 1 |
| Keys held, not pursued, pending | 18 | 1 | 2 |
| Refusals and declines | 24 | 1 | 0 |
| Superseded keys | 5 | 0 | 1 |
| Scans outside the repository | 13 | 1 | 0 |
| Pending the sitting | 15 | 0 | 0 |
| **Total** | **264 non-blank** | **30** | **32** |

A "(changed)" or "(new)" mark on a table row or a section's lead line covers that
row or section. The table below lists each one.

## Every changed or new line

| Line | 19 Oct value | Rehearsed value | File | Branch |
|---|---|---|---|---|
| Preface | chain-2 `ab27c07`; 13 files | the merge week's main, rehearsed at `b8023fba`; 5 more files, and the runbook | the paper | this draft |
| Anchor | the anchor | plus the DTH-1 rules checklist | `config/dth1.yaml` | a92-dth1-box-pieces (A92) |
| End-of-day pull | no 10-year ledger | plus the one-day 10-year ledger's resolution | the EOD unit, `oneday_10y.yaml` | chain-7 (via chain-8) |
| Daily close | the object; the close | plus the calibration rows | the close unit | chain-7, 6f (via chain-8) |
| Crypto basket | basket and data layer | plus GDELT, degree days, model watch, cyber lists, protocol counts | `scripts/run_crypto_basket.sh` | chain-7 (via chain-8) |
| Backup | the encrypted sweep | plus the DTH-1 ledger, the letters and cards archives, and AAII's weekly folder | `scripts/rclone_sync.sh` | a92-dth1-box-pieces (A92b) |
| Weekly | the Weekly | plus the digital-assets addendum | the Weekly unit | on main (6e-digital); the paper omitted it |
| Open note | absent | Weekdays 09:50 (new) | `chester-open-note.timer` | on main (a49), not in the paper |
| Alpha nightly | fill … learn | plus the grammar search, last | the unit | on main (alpha-lab-4) |
| Meme ingest | 21:45 | 21:15 | `chester-meme-ingest.timer` | on main (secondary notes) |
| Evening note | absent | Sun–Thu 21:30 (new) | `chester-evening-note.timer` | on main (a49) |
| Restore drill | a row, "never enabled" | units deleted, tool kept | `deploy/systemd/` | on main |
| Calendar | dry runs 23 and 28 Oct; freeze; 1 Nov | the merge week, 3–4 Nov; 1 Nov issued (Appendix F) | the runbook | b102 (B121) |
| Calendar: notes live | absent | live from 26 Oct (new) | `reporting_stack.yaml` `secondary_notes` | on main |
| Calendar: Doctrine #2, Audit #5 | absent | 7–8 Nov; week of 23 Nov (new) | the pack | b96 |
| Calendar: gold block | absent | Sundays from 8 Nov (new) | `reporting_stack.yaml`, `gold` | chain-8 (B75) |
| Gate count | 118 code (115 Python, 3 shell), 8 data | 167 code (164 Python, 3 shell), 8 data | `tools/gate_list.py`; `stitch_counts.py --check` 62/0 | the merge week (all chains) |
| Gate list | the Makefile | plus `tools/gate_list.py` | `tools/gate_list.py` | chain-8 |
| Pinned clocks | absent | one sentence (new) | `pin_clock()` | b101-date-drift-gates (B101) |
| Names gate | absent | list from the environment or a named file (new) | `tools/validate_names.py` | b109-names-gate (B109, B111 part 4) |
| CI | absent | cache, docs-only filter, main's group; groups pending (new) | `.github/workflows/registry-check.yml`; `config/ci_groups.yaml` | b100-hygiene (B111); B122 pending |
| Budgets | a sentence: close 1,000 words, 3 charts; Weekly 3,500, 10; Monthly 10,000, 12; Quarterly 40; targets 5, 20, 55, 90 minutes; addendum 5 minutes, 1,100 words | a table: close 2,250, 3, 10 min; Weekly 7,900, 11, 35; Monthly unchanged; addendum about 1,500, 7 min | `reporting_stack.yaml` `budget`, `reading_targets_minutes`; `digital_addendum.yaml` | chain-7 (B60, D19/D20); Weekly 11 charts from chain-8 (B75) |
| Budgets: notes' rows | absent | open 250, 1, 2 min; evening 150 (Sunday 400), 1, 1 min (Sunday 3) (new) | `reporting_stack.yaml` | on main |
| Runaway guard | absent | twice the ceiling, never past 7,000 characters (new) | `reporting_stack.yaml` | chain-7 (B60) |
| Evening paragraph gate | absent | 0.75%, 1.0%, 1.5%; always Sunday (new) | `reporting_stack.yaml` | on main |
| Weekly charts | W11 the second positioning panel; W12 fourth | W11 the standing decomposition; W12 fifth; W13 gold | `reporting_stack.yaml` | chain-7, chain-8 (B75) |
| Monthly charts | thirteen; M13, then M8 set aside | M0–M13; M13, M8, M9, M12 set aside | `reporting_stack.yaml` | chain-7 |
| Market-state object | v1.10, method 8; a contradiction closes on its first failing session | v2.0, method 11; closes after 2 failing | `market_state.yaml`; `regime.py` | chain-7 (6f, D27) |
| Vol dial's source | absent | Yahoo's VIX primary; dual run to 23 Dec; champion frozen by the hold (new) | `market_state.yaml`; `source_registry.yaml` `cboe` | b95-cboe-held (B95, D45) |
| Five added dimensions | absent | (new) | `market_state.yaml` | chain-7 |
| Per-horizon reads | absent | (new) | `market_state.yaml` | chain-7 |
| Calibration | absent | (new) | `altdata/state_calibration.py` | chain-7 |
| Volatile-day flag | absent | (new) | `vol_event.yaml` | on main (A51) |
| One-day 10-year | absent | (new) | `oneday_10y.yaml` | chain-7 |
| Gold event | absent | (new), its dollar leg through the resolver | `gold_event.yaml` | chain-7; resolver a96 |
| DM drawdown | absent | (new) | `dm_drawdown.yaml` | chain-7 |
| EM same-day rule | absent | 4 sigma; as of 16:45 (new; pending, a112) | `move_screen.yaml` | a112-em-shock-screen-amendment, not rehearsed |
| Relative volume | absent | 1.5× (new) | `opening_setup.yaml` | on main (OS-12) |
| Parallel pairs | absent | 49 inactive: 5 IBKR, 3 FRED, 41 EDGAR (new) | `data_quality.yaml` | a93, a96 (A96, A102) |
| Store "dead?" | absent | 3× allowance (new) | `tools/check_store_registry.py` | on main (b51) |
| Price-source families | absent | 8 families, all on Yahoo, no run started (new) | `config/price_sources.yaml` | a96-price-migration-fred (A96, A102) |
| Lag families | absent | 34 (new) | `config/publication_lags.yaml` | on main (b51, a61b), chain-7, chain-8 |
| DTH-1 | absent | (new) | `config/dth1.yaml` | a92 (A92, A92b) |
| Alpha families | absent | 63 (new) | `config/alpha_families.yaml` | b98-ks-family-registry (B98) |
| Attention | 7 packets; one sitting of 2 hours | plus "the third count uncapped" | `risk_limits.yaml` | chain-7 |
| Prose: revision | storyline fallback, three attempts | one revision everywhere; the notes added | the stack code | chain-7 |
| Prose: Monthly | "enforced by trimming" | a target, never trimmed (D20) | `reporting_stack.yaml` | chain-7 |
| Prose: voices | 60 calls, 10 days, 15 minutes | plus the open note's 120 s | `voices_sources.yaml` | on main (a49) |
| Price symbols | 115 | 127 | `yfinance_source.SYMBOLS` | on main and chain-7 |
| FRED pulled | 266 | 286 | `config.FRED_PULL_SERIES` | on main and chain-7, chain-8 |
| Official writers | 31 | 43 | `feeds.OFFICIAL_WRITERS` | chain-7, chain-8, the filing branches |
| External writers | 37 | 41 | `feeds.EXTERNAL_WRITERS` | as above |
| Voices | no count | 22 declared, 16 enabled | `voices_sources.yaml` | a61b (on main) |
| Lag and price-source rows | absent | 34; 8 (new) | as above | as above |
| Source registry | absent | 146 by status (115 on 19 Oct); 2 held (new) | `source_registry.yaml` | every chain; held: b95-cboe-held |
| Massive key | Massive | plus its flat-files pair | `CLAUDE.md` (R1) | on main |
| Bitcoin-data key | absent | (new) | `btcdata.py` | on main (alpha-lab-4) |
| Backup passphrase | absent | (new) | `scripts/rclone_crypt_env.sh` | on main |
| Refusals | the 17 Oct list | plus the Cboe hold, 9 refused, the EDGAR and Brazil gaps | `source_registry.yaml`; `price_sources.yaml` | a61b, b95-cboe-held, a96, a112 |
| Superseded keys | absent | (new) | the registry | a61b, chain-7 |
| Scans | to the X pilot and the Saturday brief | plus MSTR/MSCI, the ES cards and Sunday map, the Quarterly's scan; AAII's weekly folder; the register rows | `chat-tasks.yaml` | b102 (B102), a92 |

## What Thursday's refresh must re-check

Each line is a date or SHA the refresh reads again; it is not a value to rewrite.

1. **The heading's "as of" and the preface.** Write **the day chain-12 merges**: Wednesday 4 November 2026 if it merges as the runbook plans, else that day. Replace "the second rehearsal at `b8023fba`" with **main's SHA after chain-12** (and after B114's names sweep, if it lands first).
2. **The gate count.** 167 code and 8 data, as `stitch_counts --check` reads on main. A106 counted 167 where the sheet said 166 (`b121-notes.md`). Re-count, and add any gate the week's real merges add, such as B122's, if it lands first.
3. **`held_since`.** Both Cboe rows say `"2026-11-03"`, "the date of the merge". If chain-10 merges on another day, the field and its sentence change.
4. **`switched_on` and `parallel_run.started`.** All eight families read `null` and `0 of 20`. If a family's run starts before the refresh, its row changes.
5. **`ibkr_bars` (disabled)** and **the inactive pairs**: whether the operator has enabled A93's writer.
6. **A112.** Its lines are marked "pending, a112". Drop the marks if it has merged; drop the lines if it has not.
7. **B122.** The CI line says the groups are pending. Change it if `b122-ci-job-grouping` has merged.
8. **The registry's counts.** 146 sources by status, from the rehearsed tree. Re-count on main; the week's real merges may resolve a row differently.
9. **The calendar's dates:** the gold block from 8 November; the sitting on 7–8 November; the MSTR/MSCI watch's November schedule.
10. **Started dates:** the X pilot (17 October), the notes (live 26 October), the term-structure dual run (to 23 December).

## The index

The draft is a brief, not a paper. `docs/white-paper-library-guide.md` lists papers
only, and nothing under `docs/briefs/` has a line in it, so **no index needs a line**.
The paper's own Appendix A is replaced at the refresh, by the dated-appendix rule.

## Gates

See the report. Run one at a time: check_library and check_registry.
