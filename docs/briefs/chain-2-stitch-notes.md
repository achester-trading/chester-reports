STITCH PENDING CI

# chain-2: the second chain stitched into one branch (session A, 19 Oct 2026)

**What it is.** One branch, `chain-2`, carrying the whole second chain on top of Monday's line, so it merges as ONE pull request (chain-2 into main) on Tuesday 20 Oct, after Monday's six. Because it carries Monday's line itself, it merges cleanly whether or not every Monday PR lands.

**How it was made.**
- Merges only: one `--no-ff` merge commit per tip, in the paste's order, each tip taken as it stood when merged. Nothing was rebased, squashed or force-pushed, and nothing was merged to main.
- **Conflicts:** both sides kept wherever both added. Where both changed one behaviour differently, the later ruling by date was kept. Security Master ids: the earlier-merged side kept its ids, and the later side's instruments took the next free ids.
- **No fixture or gate was dropped.** Where a later ruling moved a figure, the check was kept and its expected value moved.
- **CLAUDE.md's count line** was recomputed once, at the end, from the merged Makefile.
- **Method:** `stitching-week-19-notes.md` and `friday-stitching-notes.md`. The registry was swept for duplicate keys after every merge that touched it, and every merge was audited for lines a resolution lost (below).

Branch-only: I pushed chain-2 and nothing else, ran nothing on the box, and enabled or started no unit. I only read session B's branches and merged them; I pushed none of them.

## The order, as merged

**Base:** `weekly-fixes-9` at `8d1569c` (Monday's line: main `de0c027`, the chain of nine at aud-3b-security-master `110fb31`, weekly-fixes-7, writer-fixes-1, weekly-fixes-8 at its stitch `e202312`, weekly-fixes-9 with its rulings commit).

| Step | Branch | Tip merged | Merge commit | Files resolved |
|---|---|---|---|---|
| 1 | weekly-fixes-8 | `69a1ac4` | `3b27f1a` | none (clean) |
| 1 | docs-batch-7 | `7b4f821` | `3959eb1` | none |
| 1 | docs-batch-8 | `1388967` | `42a0a92` | none |
| 1 | docs-batch-9 | `e20df42` | `c481c22` | none |
| 2 | st-r5-rates | `1dc5d69` | `8dbb65a` | CLAUDE.md (count) |
| 2 | st-r5-index | `1867bbe` | `94f641e` | CLAUDE.md (count) |
| 2 | st-r5-audit | `c60c458` | `dc1c24e` | `tools/validate_batch3_a.py` |
| 3 | a45-opening-setup-2 | `525acc5` | `e706834`, fix `4045789` | `config/reporting_stack.yaml`, `daily_cascade/weekly_sections.py`, `daily_cascade/weekly_stack.py`, `tools/validate_weekly_complete.py` |
| 4 | st-r6-es-block | `2e83766` | `5f0d8b5` | CLAUDE.md, `morning_payload.py`, `morning_render.py`, `weekly_stack.py` |
| 4 | st-r4-tranche-1b | `866c67f` | `95a7c73`, fix `4a188fd` | twelve files (below) |
| 4 | sm-schema-1-1 | `6c8c666` | `7f89de6`, fix `c292e25` | `altdata/ticker_history.py` |
| 5 | st-t5-render | `ef9014c` | `9b816c1` | eighteen files (below) |
| — | the count, and the gates the stitch moved | | `9e0c8bf` and after | CLAUDE.md, the architecture box, `validate_audit_3a.py`, and the fixes listed under "Gates" |

**st-t5-render** was `ef9014c` when fetched immediately before its merge (the paste's list predates it). It was fetched again immediately before the push and was still `ef9014c`, so only one tip of it is merged.

## Every conflict and its resolution

### Step 2

- **CLAUDE.md** (st-r5-rates, st-r5-index): the gate-count line only; recomputed at the end.
- **`tools/validate_batch3_a.py`** (st-r5-audit):
  - My side carries weekly-fixes-7 item 11's newer check: the eu-stress block names its source and start date, never a file or branch.
  - st-r5-audit's side carries the old three-line check plus its whole SR-30 daily group (`group_b_daily`, the Webstat export tests).
  - **Kept** the newer check and the whole daily group. 77/0, and 79/0 after step 4.

### Step 3 (a45, my line, into Monday's line)

- **`config/reporting_stack.yaml`, the technical appendix's formula table:**
  - **Hunk 1:** weekly-fixes-9 changed the Net GEX and DEX rows (units "$ of delta per $1 move"), and my line changed the credit-spread row (FRED serves the OAS series from 17 Oct 2023, so studies before that read a labelled proxy; ruled 18 Oct). Each side changed different rows, so all three were taken: my OAS row and weekly-fixes-9's GEX and DEX rows.
  - **Hunk 2:** both added, both kept: ruling 2's numeral-audit row, and F-3's four vendor-convention rows. This is the ruled "keep both sides" of the appendix.
- **`daily_cascade/weekly_stack.py`:** weekly-fixes-9 computes `mech` once (W8-3's flip words read it); my line passed `computed_dir` and `ending` to `mechanics_week`. Kept weekly-fixes-9's single call and gave it my two arguments.
- **`daily_cascade/weekly_sections.py`:**
  - **Hunk 1:** weekly-fixes-9's `flip_words` and `apply_flip_words`, and 6b's `_capture_before_close` and `_gated_regime`. Both kept.
  - **Hunk 2:** **one column list changed two ways.** weekly-fixes-9 renamed "Flip" to "Flip (morning capture)"; 6b part 1 renamed "Call / put wall" to "OTM call / put wall" (the walls are the out-of-the-money ones, ruled 16 Oct). Kept both renames: "Flip (morning capture)", "OTM call / put wall".
- **`tools/validate_weekly_complete.py`:** weekly-fixes-9's group N and my group M call. Both kept.
- **Fix `4045789`:** `validate_opening_setup`'s two branch-scope checks diffed `origin/a43-render...HEAD`. On the stitch, HEAD carries session B's Weekly builders, so they now read my line's own range, `origin/a43-render...origin/a45-opening-setup-2`.

### Step 4

**st-r6-es-block.** Four files, every hunk an addition on both sides; all kept.
- CLAUDE.md: the ES block's paragraph beside 6b, ST-4 to ST-10 and the opening setup.
- `morning_payload.py`: the ST-10 lines and the opening setup, then the ES block.
- `morning_render.py`: one import line, the union.
- `weekly_stack.py`: the Mechanics hooks, then the ES weekly panel.

**st-r4-tranche-1b.** Twelve files:

| File | Resolution |
|---|---|
| CLAUDE.md | The counts as unions over the base: 67 signal series (64 + 3), 169 pulled (166 + 3), 115 symbols (111 + 4). The gate count was recomputed at the end |
| `altdata/feeds.py` | The official-writer tuple, the union: the by-hand audit's `ons_cpi`, `statcan_cpi`, `bdf_webstat`, then Tranche 1b's `census_vip` and `cboe_indices` |
| `altdata/batch3.py` | Tranche 1b's Greece leg and pair (`gr_bund`, a watch spread), with weekly-fixes-7's `EU_WRITER` ("the ECB's data portal") |
| `config/narratives.yaml` | Two new top-level blocks, both kept: the GTM `disagreements`, and Tranche 1b's committed `proposals` |
| `config/security_master.yaml` | **Ids renumbered**, see below. `next_id` 204 |
| `daily_cascade/weekly_stack.py`, `monthly_macro/stack.py` | Every hook kept. In the Monthly, Tranche 1b's batch-5 plumbing joins the assignment line and Batch 6 / GTM / ST-6 follow it |
| `metrics_registry.yaml` | Spliced (diff3 alone would have interleaved fields): see below |
| `tools/validate_audit_3a.py` | `NEW_BLOCK_MEMBERS`, the union. The stale-count plant takes Tranche 1b's regex form, which plants over whatever count is printed |
| `tools/validate_batch3_a.py` | **A semantic choice**, see below |
| `tools/validate_prices.py` | 115 symbols; `VOLUME_UNITS` 95 (91 + 3 + 1) |
| `tools/validate_weekly_edits.py` | Positioning in nine sub-sections: Tranche 1b's "Treasury moves by session", and Batch 6 item 30's allocation block |

- **The Security Master renumbered.** Both sides gave SM00195 onward to different instruments:
  - the chain: SM00195 ^VIX9D, SM00196 ^VIX6M, SM00197 TIP, SM00198 MUB, SM00199 MBB;
  - Tranche 1b: SM00195 ^DSPX, SM00196 ^COR1M, SM00197 ^COR3M, SM00198 ZN=F.

  The chain merged first and keeps its ids. Tranche 1b's four became **SM00200 ^DSPX, SM00201 ^COR1M, SM00202 ^COR3M, SM00203 ZN=F**, and `next_id` is 204.
  - The only other reference on Tranche 1b's side is its notes' sentence, which now names the new ids and the old.
  - None of these ids has reached main, so nothing published is renumbered.
  - The master holds 203 entries with 203 distinct ids.
- **The registry:**
  - Tranche 1b kept the SR-16/21/23 manual keys the by-hand audit removed, and added two FlashAlpha manual keys. The audit's removal stands (below).
  - `fred_signal_triage` expects 67 members.
  - Both baskets expect 115, with Tranche 1b's `member_units` for DSPX and the COR indexes kept.
  - **A duplicate key the sweep caught:** `fred_signal_triage` had two `member_units` maps, mine (the household and debt-service shares) and Tranche 1b's (the GDP contributions). YAML keeps only the last, which would have dropped mine silently. They are now one map.
- **SEMANTIC CHOICE 1: the FlashAlpha cross-check is not a by-hand key** (ST-R4.18b, `manual.flashalpha_implied_corr` and `_realized_corr`).
  - The by-hand audit (ruled 16 Oct 2026, CLAUDE.md standing rule 3) leaves one manual key, `manual.global_pmi`, plus item 47's line. This one has no explicit yes, and the same ruling bars a vendor value from any flag.
  - Dropped: the two registry entries and the config's `manual:` block. The panel then prints no FlashAlpha row.
  - **Gate kept, its check inverted:** `validate_st_r4_t1b`'s fixture still stores the two figures, and the check now holds that no by-hand FlashAlpha row prints. Its units check names the other keys.
  - **Ruled 19 Oct 2026 (ruling 2): it stays retired.** No by-hand keys under the by-hand audit, and no vendor value in any flag; the vendor writer stores what the API serves.
- **SEMANTIC CHOICE 2: Greece-Bund's live-tier check.**
  - Tranche 1b put its Greece check inside the monthly live-tier test. The by-hand audit's SR-30 (daily OAT-Bund, 16 Oct) retired that test: a monthly series never tiers.
  - Kept the newer form and moved Greece's check into the daily group (fix `4a188fd`). Greece prints "untiered (monthly)" beside the daily OAT-Bund.

**sm-schema-1-1.** `altdata/ticker_history.py`.

**SEMANTIC CHOICE 3: the new-listing start date.**
- **The two rulings:**
  - my side carried the 15 Oct ruling (c5175a1): a new listing starts on the snapshot date, except after a missed morning, when it starts the day after the previous snapshot with `from_known: false`;
  - sm-schema-1-1 carries the **16 Oct ruling** (aud-3b Needs-you 9, relayed from the chester-meme side): every new listing starts the day after the previous snapshot, and "`from_known` stays true".
- **Kept the later ruling** (fix `c292e25`).
- **The code:** the master's known date still wins, and a reused ticker's new holder still opens on the snapshot date. The missed-morning helper is gone.
- **`validate_security_master` group L:** every fixture kept, the expected values moved. After a one-day or three-day gap the start is the day after the previous snapshot with `from_known` true; across a weekend (Fri 23 to Mon 26) it is Sat 24. 95/0.

### Step 5: st-t5-render (session B's line)

Eighteen files. st-t5-render's notes give the resolution for `monthly_macro/charts.py` and `tools/validate_monthly_stack.py`, applied as written:

| File | Resolution |
|---|---|
| CLAUDE.md | B's three new series lists (25 in FRED_6E_SERIES, 45 in FRED_RELEASES_SERIES, 29 in FRED_GROUP_B_SERIES); FRED_PULL_SERIES 268 (169 + 228 − 129); B's roster sentence kept and recounted from the code (37 external writers, not 27) |
| Makefile | Both data gates: `validate_vendor_divergence.py` and `validate_backup_crypt.py`, so eight data gates |
| `altdata/feeds.py` | Every official writer, in order: the chain's, then B's crypto writers with `crypto_derived` last (its comment requires it); both roster blocks: the vendor writer's and the PRL's |
| `altdata/ledgers/__init__.py` (both added it) | B's version: the same file plus ruling 2 of 17 Oct (a pass rule pre-registered by the first edition), which my copy predated byte for byte |
| `config/catalogue_commands.yaml` | Every command line, both sides |
| `morning_payload.py`, `morning_render.py` | The vol-event reader and the ES lines, then B's meme line |
| `daily_cascade/weekly_stack.py` | Plumbing: every hook, then 6e's lens table and inflation block |
| `monthly_macro/stack.py` | The assignment with batch 5, then B's inflation block where B put it ("after the buckets"), then Batch 6 / GTM / ST-6 |
| `monthly_macro/charts.py` | `ORDER` = the chain's twelve + M13; `ALL = ORDER + ("M12",)`; `DROP_ORDER` = ("M13",) + the chain's; `PLACE` carries M12 and M13 |
| `tools/validate_monthly_stack.py` | The chain's cap and count checks, extended. At a cap of 11 with all thirteen drawn, M13 then M8 are set aside. M13 is never drawn on the fixture, so it is never in `bad`. The ORDER pin is 13 with M13 last |
| `metrics_registry.yaml` | The lens-family map: both sides' entries. **The sweep caught 13 duplicate `family:` keys** on bulk blocks, AQ-8a's (10 Oct) beside 6e's (15 Oct). 6e's line was kept in every pair. They agree except `paper_bid_risk_reversal`, AQ-8a's `ratio` against 6e's `conditions` with its ambiguity note: **6e's `conditions` kept** (the later assignment, `tools/assign_families.py`). Also dropped: 21 family lines naming manual keys the by-hand audit removed (B's map still had them; check_registry failed on them) |
| `tools/validate_audit_3a.py` | B's extended `NEW_KEY_BLOCKS` and the chain's `NEW_BLOCK_MEMBERS` |
| `tools/validate_secrets.py` | B's group I (rclone's variables) and my group J (the User-Agent rule), both run |
| `tools/validate_security_master.py` | The docstring: my 16 Oct wording of L and B's group M |
| `tools/validate_weekly_edits.py` | Positioning in ten sub-sections: + B's "Crypto flows" last |
| `docs/narrative-register-pairs.md`, `docs/warsh-matrix-lines.md` (both added) | Joined as B's own note asks: one header, every entry kept. B's item-46 line replaces my placeholder for it |

**A loss the audit caught, and fixed before the commit.**
- My conflict helper's "both" mode first dropped any line of the second side that also appeared in the first. In code that silently removes a repeated `try:` or `return None`.
- It failed loudly once, in `morning_payload.py`. I then fixed the helper, recreated the four files resolved that way in this merge, and resolved them again.
- I wrote a loss audit and ran it over every merge commit (`git show` of both parents, the base and the merge). It lists each line whose count in the merge falls below what the two sides added. Every line it lists is a deliberate resolution named in this file; no addition was lost.

### CI round 1 (run 39205188783 on `5722fb1`: six gates failed, all where the two lines meet), fixed in `abf6b7d`

| Gate | Failure | Resolution |
|---|---|---|
| `validate_releases_b` (B's), `validate_st_r5_t1_rest` (mine) | **Two FRED series pulled twice.** WPSFD49116 under my `ppi_fd_core_ts` (ST-R5.35a, 16 Oct) and B's `ppi_fd_core_ex_trade` (Group B); `fed_interest_payments`, the same key and id, in my GTM-12 list and B's 6e list | **SEMANTIC CHOICE 4.** One spec per series. WPSFD49116 keeps B's key, because ruling 7 of 18 Oct (the later) holds every PPI key to the release family's 20-year window, which my "full" override contradicted. My ST-R5.35a reader (`config/st_r5_index.yaml` `ppi_key`) now reads `fred.ppi_fd_core_ex_trade`, and its fixture follows. `fed_interest_payments` keeps 6e-rest's spec (16 Oct, the earlier, as the Friday stitch kept AQ-3's over c1's); GTM-12 reads the same key. FRED_SIGNAL_SERIES is 65, FRED_PULL_SERIES 266, and no key or id appears twice. The registry block, the audit's member set, CLAUDE.md and the architecture box follow |
| `validate_weekly_fixes_8` (B's) | W8-6's `ai_names` preferred `config/ai_buckets.yaml` when it existed. GTM-4's buckets list members for the hyperscalers only, so NVDA lost its AI clause | The buckets' members **join** the Weekly's own list rather than replace it (`daily_cascade/ahead.py`) |
| `validate_backups` (B's) | Three of my writers (`edgar_xbrl`, `fiscaldata`, `sp500_members`) opened the store directly; audit-leftovers' rule is `open_writer` | All three open it through `observations.open_writer(__name__)` |
| `validate_lenses` (B's) | Four series arrived after 6e's family pass with no family: 6b's call and put gamma masses, the raw-signed DEX, and EL-5's `state.gap_pct` | Families added: the three exposures `quantity`, the gap `ratio` |
| `validate_st_r5_index` (mine) | It pinned the Monthly's plan at twelve charts | Thirteen planned, M13 last and set aside first; without M13, M8 is still the one set aside at a cap of 12 |

**Not run locally, by the paste's rule.** Windows reported low memory and stopped the background run of these gates after the edits had applied. I did not retry: the edits passed a syntax and YAML parse and went to CI.

### CI round 2 (run 39207080387 on `abf6b7d`: three gates failed), fixed with Part 0 of the 19 Oct paste

| Gate | Failure | Resolution |
|---|---|---|
| `validate_weekly_fixes_8` (B's) | Its fixture still pinned the buckets **replacing** the Weekly's list, the behaviour round 1 changed | The check now holds the join: the fixture's buckets plus the Weekly's own `earnings.ai_names` |
| `validate_st_r5_index` (mine) | It looked for `fred.ppi_fd_core_ex_trade` in the top-level `families` and `long_windows` maps; since semantic choice 4 the key is Group B's | The check reads the key's family from its block's `member_families` (`release`) and holds that it carries **no** long-window override, so ruling 7's release window applies |
| `validate_lenses` (B's) | CI printed four keys; the full list was **80**: EL-5's state vector, the vendor writer's stored values, the opening setup's `chain.*`, 6b's exposures, Tranche 1b's Census and Cboe series, SR-6's attribution, three FRED keys and four rule-30 "not tracked" calcs, all of which arrived in the union after 6e's family pass | **41 families**, each the one its unit carries elsewhere in the registry (fraction and shares `ratio`, a strike or range `price`, vol `conditions`, dollars and counts `quantity`, bp `spread`, a yield `rate`, the FRED contributions and PPI `release`). **35 exclusions with their reasons:** the three EL-5 signs and the hours count; the opening setup's expiry label; the four rule-30 keys; and the vendor's 26 stored values, which ruling 2 keeps out of any flag, so none is lensed |

The acceptances of 19 Oct (ruling 3) re-pinned one hash, `validate_st_t3_calib`'s SR-8 entry, and two gates (`validate_st_t2_rates` H, `validate_st_t3_calib` K) now read the drafted or the accepted header. Run locally, one at a time: `validate_weekly_fixes_8` 67/0, `validate_st_r5_index` 58/0, `validate_st_t2_rates` 71/0, `validate_st_t3_calib` 88/0, `validate_deploy` 154/0 (the mechanism watch's pair, ruling 5). `validate_lenses` is CI's.

## The rulings of 19 Oct, applied on chain-2 (Part 0 of the 19 Oct paste)

- **Ruling 2:** the FlashAlpha by-hand cross-check stays retired (semantic choice 1 above; its Needs-you item closed).
- **Ruling 3, the acceptances (00:38 ET, rule 31):** in `docs/signal-triage-register.md`, the eleven gate statuses (ST-8: SR-1, 2, 4, 5, 13, 14; ST-7: SR-12, 15, 21, 22, 23) now read "*Accepted as drafted (rule 31), 19 Oct 2026; the register status above is unchanged:*", the form of GTM-21's of 17 Oct, and the four dated notes (SR-4's and SR-8's FRED notes, SR-21's, SR-22's) end "Accepted 19 Oct 2026." The false-bottom audit's proposal is "Accepted onto the Doctrine #2 agenda, 19 Oct 2026; a proposal until the sitting rules." The register statuses are unchanged; nothing is promoted and no right changes.
- **Ruling 5:** `altdata.mechanism_watch promote` and `reject` are denied with their verbs whole in `.claude/settings.json`, beside the narratives pair, held by two `MUST_DENY` shapes in `validate_deploy` (one local with `--confirm`, one over ssh) and named in CLAUDE.md's deny table. The read-only `review` stays open. Ari approved the settings edit at the laptop.
- **Ruling 7, the state directory:** `chester-restore-test` gains `-%h/state` and a declared Environment drop-in in `box-config.allow`. The audit of every unit chain-2 adds or changes is in the box sheet, unit by unit. It found one more real split: **chain-2 sandboxes `chester-auction` (AUD-2) with no `~/state` write path, while the box's declared drop-in points it at `~/state`**, so its status and lock would have landed on a read-only path. Fixed, with `chester-daily-close` (changed here) and `chester-ibkr-sync` (the same gap since main's AUD-2 sandbox; not otherwise changed here), each given `-%h/state`. A new group in `validate_systemd_units` holds the rule, with a plant that removes the restore test's line.
- **Ruling 8, the lab outbox:** `push_lab_outbox` copies to `<outbox remote>:chester-lab-outbox/` (`LAB_OUTBOX_FOLDER`), never under `chester-vendor-checks`; the inbox pulls are unchanged. `alpha/outbox.py`, `alpha/loops/weekly.py`, `docs/alpha-lab.md`, `docs/briefs/alpha-research-sitting-template.md` and README section 11's table say so; `validate_backups` group J and `validate_alpha` hold the path.
- **The box sheet**, corrected for rulings 6, 7 and 8 and for the order of the backup migration (C1 to C3 and C4's names before the merge; main's sweep reads only `CHESTER_RCLONE_REMOTE` and `CHESTER_RCLONE_FLAGS`, checked in main's `scripts/rclone_sync.sh`).

## The counts, recomputed once from the merged Makefile

**One hundred and eighteen code gates (one hundred and fifteen Python, three shell) and eight data gates.** Recounted on the tip after CI round 2, from `scripts/make.sh list` and the code; CLAUDE.md's count line and directory block and the architecture document's store box print the same figures.

The other counts CLAUDE.md prints, from the code:

| Count | Value |
|---|---|
| Signal series (`FRED_SIGNAL_SERIES`) | 65 |
| FRED series pulled (`FRED_PULL_SERIES`, no id twice) | 266 |
| Market symbols (`yfinance_source.SYMBOLS`) | 115 |
| Official writers (`feeds.OFFICIAL_WRITERS`) | 31 |
| External writers (`feeds.EXTERNAL_WRITERS`) | 37 |
| Loggers (`loggers.load_all()`) | 7 |

The architecture document's store box carries the same figures. `validate_audit_3a`'s word parser stopped at ninety-nine, so it now reads "one hundred and eighteen", and a check of that is added. Its stale-symbols plant replaces whatever count is printed rather than a hard-coded "106".

## Gates

**Fixes the stitch needed, all to code where two lines meet:**
- **`altdata/ledgers/st_r5_31b.py` and `st_r5_44b.py` (mine)** opened the store themselves. B's `validate_ledgers_b6` holds the package to one store read, so both now open it through `sources.open_store()`, beside `store()`.
- `validate_opening_setup` (fix `4045789`); `validate_batch3_a` (fix `4a188fd`); `validate_security_master` (fix `c292e25`).
- `validate_audit_3a` and check_registry (the 21 family lines).
- **Round 2, `781c9fe`:**
  - `validate_secrets`' User-Agent rule (mine) lists B's `treasury.py`, which sends EDGAR's contact only to `data.sec.gov` for Strategy's share count;
  - `validate_dealer_block` reads thirteen planned charts, with M13 set aside before M8;
  - `validate_by_hand_audit`: the lens-excluded map drops the two manual keys the audit removed, and the Warsh file's item 46 takes the file's "Item N" heading with B's id kept beside it.

**Run locally, one at a time:**

| Gate | Result | Gate | Result |
|---|---|---|---|
| check_registry | OK | validate_audit_3a | 88/0 |
| validate_alpha (its fixture clock) | 257/0 | validate_weekly_complete | 96/0 |
| validate_monthly | 359/0 (1 skipped) | validate_weekly_edits | 91/0 |
| validate_monthly_stack | 266/0 | validate_weekly_stack | 83/0 |
| validate_batch3_a | 79/0 | validate_prices | 101/0 |
| validate_security_master | 102/0 | validate_st_r4_t1 | 49/0 |
| validate_st_r4_t1b | 61/0 | validate_secrets | 58/0 |
| validate_st_t5_render | 46/0 | validate_st_t5_prl | 61/0 |
| validate_opening_setup | 43/0 | validate_es_block | 69/0 |
| validate_a43_render | 46/0 | validate_weekly_fixes_9 | 39/0 |
| validate_crypto_basket | 93/0 | validate_figure_budget | 123/0 |
| validate_vol_event | 50/0 | validate_dealer_block | 133/0 |
| validate_by_hand_audit | 17/0 | validate_official_sources | 336/0 |
| validate_ledgers_b6 | 41/0 | validate_st_t1_rest | 34/0 |
| validate_gates | 32/0 | validate_feeds_scheduled | 19/0 |
| validate_narratives | 103/0 | | |

Two tracebacks printed by passing gates, both already on the parent lines and not new at the stitch:
- `validate_weekly_stack`: `book_b.register_rows` meets the gate's refusal of the default store and falls back to no rows, as designed.
- `validate_crypto_basket`: AQ-5's correlation block on a fixture without month bounds, caught and printed "not tracked".

Every other gate is CI's.

**CI.**

CI-TABLE

## Containment

`git merge-base --is-ancestor origin/<tip> chain-2`, run before the push, answers **yes for every tip**:

| Tip | SHA | In chain-2 |
|---|---|---|
| weekly-fixes-9 | `8d1569c` | yes |
| weekly-fixes-8 | `69a1ac4` | yes |
| docs-batch-7 | `7b4f821` | yes |
| docs-batch-8 | `1388967` | yes |
| docs-batch-9 | `e20df42` | yes |
| st-r5-rates | `1dc5d69` | yes |
| st-r5-index | `1867bbe` | yes |
| st-r5-audit | `c60c458` | yes |
| a45-opening-setup-2 | `525acc5` | yes |
| st-r6-es-block | `2e83766` | yes |
| st-r4-tranche-1b | `866c67f` | yes |
| sm-schema-1-1 | `6c8c666` | yes |
| st-t5-render | `ef9014c` | yes |
| aud-3b-security-master | `110fb31` | yes |
| main | `de0c027` | yes |
| alpha-lab-1, alpha-lab-2 | (through a45) | yes |

## Needs you

1. ~~**The FlashAlpha by-hand cross-check (ST-R4.18b).**~~ **Closed: ruled 19 Oct 2026 (ruling 2), it stays retired.**
2. **The Saturday brief (chat-side).** Its prompt must read the lab's verdicts and agenda from Drive `chester-lab-outbox/` (ruling 8), no longer `chester-vendor-checks/lab-outbox/`. Yours to update in chat.
3. **The rest** is in the box sheet (`docs/briefs/chain-2-box-sheet.md`), each decision marked ⚑.
