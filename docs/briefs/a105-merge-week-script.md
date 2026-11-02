# A105: the merge week, rehearsed a second time (Tue 3 and Wed 4 Nov 2026)

**Branch.** `a105-merge-week-rehearsal-2`, a throwaway: never merged, and deleted
after the real merges. No existing branch was touched. A99's branch stays as the
first pass's record.

**Base.** `origin/b86-chain-8-assembly` at `4e6814df`, the same as A99's.

**Main.** `422ea697`, unmoved since A99: nothing has merged.

**Fetched.** 2 Nov 2026, about 04:30 UTC (23:30 ET, 1 Nov), after A104 had
reported.

**Tip.** `d3f1995a`, the rehearsed result through b109. b88 was merged last and
aborted, by the rule (N2, A99's, unchanged).

## 1. The order as rehearsed, the tips, and the weekend's pastes

The planned order held. Nothing had to move.

| Step | Branch | Tip | The weekend's pastes in it |
|---|---|---|---|
| 0a | A91's `tools/validate_audit_fixes.py` change from `f8819b62`, alone | `c2dfa70f` | |
| 0b | `b85-gitattributes-lf` | `5cb338fa` | |
| 0c | `b101-date-drift-gates` | `666611e1` | B101, **B101b, B106** |
| 1 | chain-7 and chain-8 | in the base | |
| 2 | `a90-monthly-dryrun-2` | `f8819b62` | |
| 3 | `b95-cboe-held` | `2250b5cb` | |
| 4 | `a84-feed-summary-and-allowances` | `636b9173` | |
| 5 | `b81-batch-18-overnight-session` | `6256a67c` | |
| 6 | `b82-aaii-bearish-share` | `bd01fe67` | |
| 7 | `b85-crypto-derived-keys` | `f864e8f6` | |
| 8 | `b87-yields-direction` | `ec96ceec` | |
| 9 | `b89-cboe-terms-check` | `4e737488` | |
| 10 | `b90-nautilus-assessment` | `d7ab0ea8` | |
| 11 | `b91-batch-19-filing` | `96e97e08` | **B105** (Part 3) |
| 12 | `b92-batch-20-filing` | `30c16e1c` | |
| 13 | `b95-batch-21-filing` | `9aeeee9c` | **B108** (the placement pack) |
| 14 | `a92-dth1-box-pieces` | `fb3e9a30` | **A92b** |
| 15 | `a93-ibkr-daily-bars` | `5b2297ec` | |
| 16 | `a94-ll6-forecasters` | `d70205dd` | |
| 17 | `a96-price-migration-fred` | `d356e613` | A102; **A104**, whose dry runs were PENDING on the laptop (no SEC contact), so its tip carries notes only and no fallback |
| 17a | `fbd43be8`'s change, carried as in A99 | `f5b69245` | |
| 18 | `a97-weekly-readability` | `d30238ed` | |
| 19 | `a95-monthly-first-edition` | `a2737d15` | **A95** (the audit fixes and Part 6) |
| 20 | `a103-weekly-consistency` | `b3a1b9f5` | **A103** |
| 21 | `a98-paper-executor` | `73d12a1c` | |
| 22 | `b96-doctrine-2-pack-refresh` | `c23c6413` | **B104** (Part 12) |
| 23 | `b100-hygiene` | `12d7f940` | B100, **B107** (the CI-time audit brief) |
| 24 | `b102-readable-editions-register` | `f6bdc7c3` | **B102, B103** |
| 25 | `b109-names-gate` | `04439228` | **B109** |
| 26 | `b88-library-rehearsal` | `4c734105` | merged to show its conflicts, then **aborted** (N2) |

**All thirteen of the weekend's pastes were in their branches at fetch time:**
A95, A103, A92b, A104, B101b, B102, B103, B104, B105, B106, B107, B108, B109.
None had not reported.

- **A104** reported a stop. Its dry runs returned PENDING on the laptop, because
  `CHESTER_SEC_CONTACT` is unset there. Its branch holds the paste and that
  finding, and no fallback was built (see 6).

## 2. Per merge

**The stitch checklist ran at every merge:**

- the tools, `--check` then `--write`: `stitch_counts`, `change_orders_index`,
  `appendix_queue_index`;
- the must-run gates: `validate_lenses`, `check_registry` and
  `yaml_section_check` against both parents;
- the gates whose files the merge touched, one at a time in the foreground.

`validate_lenses` (passed), `check_registry` (OK) and `yaml_section_check` (no key
moved section) held at every merge, so the table leaves them out. `0a` and `17a`
are single commits, which `yaml_section_check` does not read.

**The resolutions A99 found recur unchanged:**

- **The batch-orders cell and the orders index** (b81, b91, b92, b95-batch-21):
  - `docs/change-orders.md`: both lines;
  - the register's cell: ours, then `change_orders_index --write`;
  - the SR blocks in order, SR-60 to SR-76 with no duplicate;
  - `docs/narrative-register-pairs.md`: both.
- **An A-branch built before S1** (a92, a93, a94, a96, a97, a98):
  - the Makefile: **ours**;
  - `GATE_KIND = "code"` added after the gate's `from __future__` line;
  - CLAUDE.md: **ours**, then `stitch_counts --write`.
- **No count was set by hand.**

| # | Branch (tip) | Merge | Conflicts and resolution | Code / Python gates | Gates run | Time |
|---|---|---|---|---|---|---|
| 0a | A91's change (`f8819b62`) | `c2dfa70f` | applied cleanly (`git show f8819b62 -- tools/validate_audit_fixes.py \| git apply --3way`) | 159 / 156 | `audit_fixes` 136/0 | 1 min |
| 0b | b85-gitattributes-lf | `d18ed6fa` | none. **Then the laptop's LF re-checkout: 133 files**, as A99 found (see below) | unchanged | must-runs | 1 min |
| 0c | b101-date-drift-gates | `caa80fea` | none (24 files, each gate's clock pinned) | unchanged | `monthly` passed (the refunding window now pinned), `voices`, `alpha_proposer`, `st_t5_render` passed, `batch15_1` 71/0 | 1 min |
| 2 | a90 | `689d4cbd` | none | unchanged | `audit_fixes` 158/0, `numeral_audit`, `monthly` passed | 1 min |
| 3 | b95-cboe-held | `1dcd53b9` | none | unchanged | `feed_repair` passed, `st_r4_t1b` 71/0 | 1 min |
| 4 | a84 | `dc0f5827` | none | unchanged | `b51_registry_html`, `feed_repair` passed | 1 min |
| 5 | b81 | `ccc4e0b3` | change-orders: both; register: the cell ours, then `--write`; SR-65 to 67, then 68 | unchanged | `check_library` 0 failures | 3 min |
| 6 | b82 | `bd00da8c` | none | unchanged | `official_sources` passed | 1 min |
| 7 | b85-crypto-derived-keys | `a412a194` | `derived.py` `DECLARED_STATUSES`: combined by hand, as A99 did (b95's `held` comment and value, b85's `declared_until` comment, one tuple); `metrics_registry.yaml` `member_overrides`: both | unchanged | `crypto_sources`, `feed_repair` passed, `audit_3a` 88/0, `b51_registry_html` passed | 4 min |
| 8 | b87 | `de41c255` | none | unchanged | `audit_fixes` 161/0 | 1 min |
| 9 | b89 | `62ef8794` | none (docs) | unchanged | must-runs | 1 min |
| 10 | b90 | `0bbeb78c` | none (docs) | unchanged | must-runs | 1 min |
| 11 | b91 (with B105) | `d42b80d1` | the register's cell: ours, then `--write`; pairs: both. SR-69 to 72 clean | unchanged | `check_library` 0 failures | 2 min |
| 12 | b92 | `7e93b9a3` | change-orders: both; the cell: ours, then `--write`. SR-73 to 75 clean | unchanged | `check_library` 0 failures | 2 min |
| 13 | b95-batch-21 (with B108) | `e6de6687` | change-orders: both; the cell: ours, then `--write`. SR-76 clean | unchanged | `check_library` 0 failures | 2 min |
| 14 | a92 (with A92b) | `a9758813` | the Makefile, GATE_KIND (`validate_dth1.py`), the count; `catalogue_commands.yaml`: both. **New, the watched overlap: `altdata/sources/aaii.py`.** b82's `rows_from_weekly(..., keys=KEYS)` against A92b's `weekly_rows()`; resolved to `weekly_rows(KEYS)`, so the weekly folder's union carries b82's two keys. `validate_official_sources`: b82's group V and A92b's group W both, `main()` listing `group_u, group_v, group_w`. `rclone_sync.sh` merged clean | 159/156 → 160/157 | `official_sources` passed (both groups), `dth1`, `backup`, `backups` passed, `audit_3a` 88/0, `gates` passed | 6 min |
| 15 | a93 | `a78eec0d` | the Makefile, GATE_KIND (`validate_ibkr_bars.py`), the count | → 161/158 | `audit_3a` 88/0, `ibkr_bars` passed, `quality` 48/0, `feed_repair` passed | 3 min |
| 16 | a94 | `bbbfb492` | the Makefile, GATE_KIND (`validate_ll6.py`), the count | → 162/159 | `deploy`, `ll6`, `secrets` passed, `audit_3a` 88/0 | 3 min |
| 17 | a96 (A96, A102, A104) | `241e90c7` | the Makefile, GATE_KIND (`validate_price_sources.py`), the count; **new: `metrics_registry.yaml`**, chain-8's `trend_breadth_signs` block against A102's `edgar_fundamentals` block, both kept (each is its own `bulk_imports` block). **Then `validate_price_sources` failed on N1**, as in A99 | → 163/160 | `price_sources`: one failure (N1) | 3 min |
| 17a | `fbd43be8`'s change, carried | `f5b69245` | cherry-picked from A99's branch | unchanged | `price_sources`, `gold_attribution`, `trend_breadth`, `weekly_gold_block` passed, `ai_fcf` 27/0, `weekly_calendar` 44/0, `quality` 48/0 | 2 min |
| 18 | a97 | `81557d86` | the Makefile, GATE_KIND (`validate_weekly_readability.py`), the count | → 164/161 | `weekly_readability`, `weekly_storyline`, `weekly_edits`, `system_metrics`, `b51_registry_html` passed | 3 min |
| 19 | a95 (on a97) | `0d8ae5b2` | **none.** The watched overlaps merged clean: `numeral_audit.py` (A95's `signed_fields` and `role_faults` beside A90's binding) and `validate_monthly.py` (B101b's clock beside A95's group K) | unchanged | `numeral_audit` passed, `audit_fixes` 161/0, `monthly` passed, `monthly_frames`, `readability`, `weekly_edits`, `secondary_notes`, `benchmark` passed | 4 min |
| 20 | a103 (on a95) | `8daf1c33` | **none.** The Weekly's checks beside A97's merged clean | unchanged | `weekly_readability`, `weekly` passed, `weekly_calendar` 44/0, `st_r4_t1` 49/0, `weekly_opener` 46/0, `weekly_fixes_8` passed | 3 min |
| 21 | a98 | `2b285e6c` | the Makefile, GATE_KIND (`validate_paper_exec.py`), the count | → 165/162 | `deploy`, `paper_exec`, `alpha`, `alpha_no_orders`, `alpha_proposer`, `secrets` passed, `audit_3a` 88/0 | 4 min |
| 22 | b96 (with B104) | `89086fa7` | the Doctrine #2 pack, 5 hunks: **b96's side whole**, as A99. Checked line by line: every one of the base's 1,086 lines is in b96's except the four reading-time lines, which b96 restates for its larger pack (D2-1 to D2-90, Parts 1 to 12) | unchanged | `check_library` 0 failures | 2 min |
| 23 | b100 (with B107) | `6c017bc8` | none | unchanged | `deploy`, `gates` passed | 1 min |
| 24 | b102 (B102, B103) | `eb6350c1` | **New.** See below | unchanged | `check_library` 0 failures, `check_master_guide` passed | 6 min |
| 25 | b109 | `d3f1995a` | **New, 16 files.** See below | → 166/163 | `names` passed (its self-test; the scan, with the list, found 71 hits: N3), `check_master_guide`, `check_library`, `by_hand_audit`, `digital_addendum`, `gates`, `deploy` passed | 12 min |
| 26 | b88 | aborted | five conflicts, the same as A99's (N2) | — | — | 1 min |

**b102 (step 24), six conflicts:**

- **`docs/briefs/letter-findings.md`: an add/add**, created on both sides.
  - B102 made it the defect register that D53 and the readable editions'
    contract name: one row per finding, with a status.
  - A95 and A103 made it the fix record.
  - Resolved by keeping both: B102's register first, with all fourteen M and W
    rows closed as "fixed (<branch>)", since both fixes merge at steps 19 and 20
    (the register's own rule: "a row closes when its session's fix merges").
  - A95's and A103's fix tables follow, under "The fixes, as the sessions filed
    them".
- **`docs/master-guide.md`:**
  - the close's checklist line: chain-8's "ten minutes", plus B102's new 18:05
    evening-triage line;
  - "Landing next": chain-8's merge-order table, with B102's readable-editions
    row added to it.
- **`docs/white-paper-library-guide.md`:** the Reporting System paper's line is
  chain-8's Draft 4, plus B102's sixth appendix.
- **`docs/whitepapers/reporting-system-whitepaper.md`:**
  - the header: chain-8's Draft 4, since B102's side was the unchanged base;
  - the end: chain-8's list items, then B102's Appendix F.
- **The two `docs/html/` files:** rebuilt from the `.md`.

**b109 (step 25), sixteen conflicts, all the names sweep against later edits.**
b109 swept main (`422ea697`). Chain-7, chain-8 and the other branches had already
replaced the same names in their own words under D38.

- **Ours, every hunk but two:** CLAUDE.md, the Makefile, three configs,
  `doctrine-2-proposals-st-l.md`, the appendix queue, `master-guide.md`,
  `chat-tasks.yaml`, `tools/figures/master_guide.py`, `validate_digital_addendum`,
  and the Guide's Figure 2.
  - The html files were then rebuilt, and Rates & Liquidity's `.md` too
    (check_library had failed on its stale edition).
  - `appendix_queue_index --write` regenerated the queue.
- **`.github/workflows/registry-check.yml`:** both sides added an `env:` to the
  gate step: S1 part 6's `GATE_ARGS` and B109's `CHESTER_NAMES_DENYLIST`. Two
  `env:` keys in one step is invalid YAML, so the two were joined in **one env
  block**. It parses.
- **`tools/validate_by_hand_audit.py`:** ours, with b109's test string (`"weights
  stay the operator's"`), because b109's change to the document text merged
  clean; with ours alone the gate failed.

**The final counts**, set by `tools/stitch_counts.py --write`: **one hundred and
sixty-six code gates (one hundred and sixty-three Python, three shell)** and
eight data gates.

- That is A99's 165 plus B109's `validate_names`.
- `stitch_counts --check` agrees on all 62 counts.
- The seven gates added since S1 each joined by `GATE_KIND`, with no Makefile
  line: A92's, A93's, A94's, A96's, A97's, A98's and B109's.

**A laptop-only step after b85-gitattributes-lf lands (as A99).**

- `.gitattributes` pins hash-pinned files LF, but a checkout made before the pin
  keeps CRLF on disk.
- The rehearsal's worktree had **133** such files. They were re-checked out from
  the index by name; afterwards `validate_batch15_1` is 71/0.
- The operator's laptop checkout needs the same, once:

  ```
  git ls-files --eol | grep "w/crlf" | grep "attr/.*eol=lf" | awk '{print $NF}' > lf.txt
  xargs -d '\n' rm -f -- < lf.txt && xargs -d '\n' git checkout -- < lf.txt
  ```

- CI and the box check out fresh and are unaffected.

## 3. Needs you

**N1. A96 must carry chain-8's three dollar-index readers before its PR**
(A99's N1, unchanged).

- After the merge, `validate_price_sources` fails on
  `config/gold_attribution.yaml:19`, `config/gold_event.yaml:37` and
  `config/trend_breadth.yaml:52`.
- `fbd43be8`'s change fixes it. It was carried again here as `f5b69245`.
- **Step 17a stands as ruled at A100:** once chain-8 is on main, merge main into
  a96, commit that change on a96, run `validate_price_sources`, then open a96's
  PR.

**N2. Two "Appendix B" sections in Foundations, on b88** (A99's N2, unchanged).
`docs/whitepapers/disruptive-themes-whitepaper.md` holds the base's A68 records
(line 574) and b88's dispatches split (line 618), both titled "Appendix B".
A99's recommendation stands: b88's split keeps B, and A68's records become C.
**The letters are yours,** at Foundations' library PR. b88 was aborted here.

**N3 (new). The names gate finds 71 hits in 42 files on the merged tree.**

- **The cause.** B109 swept main as it stood (`422ea697`). Branches merged
  afterwards bring lines its sweep never saw:
  - October's pastes;
  - Unix home paths in gate fixtures (`tools/validate_deploy.py`,
    `validate_morning_anchor.py`);
  - `docs/runbooks/restore.md`'s `adduser` line;
  - the workplan;
  - a ledger's preregistration.
- **How it was run.** `validate_names` with the operator's first name in the
  environment only (`CHESTER_NAMES_DENYLIST`, never written to a file).
- **Without the list** the gate runs its self-test and skips the scan, so CI is
  green until the repository secret is set.
- **Two things are yours to order:**
  - **(a)** after Wednesday's merges, a session paste re-runs B109's sweep on
    main;
  - **(b)** set the `CHESTER_NAMES_DENYLIST` secret only after it. Set before,
    the Gates workflow fails `validate_names` on every push.
- **One case for that sweep to decide.** The Unix home paths are the box's
  account name, not a byline: `/home/<user>/...` in the deploy gate's deny-list
  fixtures and the restore runbook. Either the sweep writes
  `/home/<user>/` there, or the gate learns a path allowance. That is a rule
  change, so it goes in the paste.

**Not needs-you, but on the day's checklist:**

- each A-branch's `GATE_KIND` line and the tool's count, as above;
- the laptop's LF re-checkout after step 0b;
- at step 14, `weekly_rows(KEYS)`;
- at step 24, the letter-findings composition;
- at step 25, the one env block in `registry-check.yml`.

## 4. The full gate run

**Completed on the laptop, every Python gate passing.**

- **`bash scripts/make.sh validate` said nothing about the code.** It used the
  right interpreter (b100's fix), but each gate path arrived with a trailing CR,
  so nearly every gate failed to open (section 6).
- **So the list was run gate by gate.** `tools/gate_list.py --kind code` with the
  CR stripped, each gate on the main checkout's venv, one at a time, 540 s each
  (`scratchpad/a105_full.sh`, uncommitted).
  - **All 163 Python code gates pass**: the list's 162 and the smoke test. That
    takes in `validate_monthly_stack` (286 s, passed; the laptop had cut it in
    A99), `validate_weekly_stack`, `validate_quarterly_stack`, `validate_stack`
    (422 s) and `validate_names` (its self-test).
  - About 40 minutes in all, with no failure and no gate stopped for memory.
- **The three shell gates:**
  - `validate_ibgateway_watchdog.sh` and `validate_session_calendar.sh` pass.
  - `validate_heartbeat_caller.sh` reached the laptop's 300-second cap with every
    check it printed passing. It is left to CI.
- **The data gates** report and do not count; on the laptop they print NOT
  VALIDATED (no store).
- **So the merged tree's code gates are green on the laptop**, main's B84 and
  the date-drift gates included. The one thing outside the run is N3's scan,
  which needs the list.

## 5. The box steps after the deploys, in merge order

Each step is the operator's, inside the operating windows. Sessions run none of
them. The list is A99's, plus the weekend's.

1. **b101 (B101, B101b, B106):** none. The gates' clocks are pinned in the gates.
2. **b95-cboe-held:** the hold takes effect at the merge (`held_since`
   2026-11-03). Nothing is run. Check the next 06:45 and EOD logs: the two Cboe
   readers return HELD and fetch nothing.
3. **a84:** no command. The feed summary prints at the next heartbeat.
4. **b82: the AAII bearish share's history.** Only if the history file has left
   the inbox:

   ```
   python -m altdata.sources.aaii --history
   ```

5. **b85: the DVOL backfill**, optional:

   ```
   python -m altdata.sources.deribit backfill --dry-run
   python -m altdata.sources.deribit backfill
   ```

6. **The XXX figures export** (D48(11)), before XXX's library PR. The script is
   section 11 of `docs/briefs/library-review-decisions-2026-10-30.md`, on b88.
7. **a92 with A92b: the DTH-1 ledger's new home and header, and the archive
   folders.**
   - **The ledger.** Keep the manual ledger in the main Drive at
     **`chester-cards/dth1-manual-ledger.csv`** (D52), no longer
     `chester-vendor-checks/dth1/`.
   - **Its header.** Either the canonical header, `date, time_et, instrument,
     side, entry, stop, target, contracts, risk_usd, exit, result_r, result_usd,
     status, rule_broken, notes`, or the old spellings (Date, Result R, Rule
     broken, Status). Open trades are marked `open` in status, and a result the
     statement must fill is marked "FILL FROM STATEMENT".
   - **The sweep** copies the ledger to
     `~/chester-data/inbox/dth1/dth1-manual-ledger.csv`.
   - **The archives (D54).** The sweep also copies `chester-letters/` and
     `chester-cards/` into `~/chester-data/inbox/letters/` and `cards/`, and the
     AAII task's `chester-vendor-checks/aaii/weekly/` into
     `~/chester-data/inbox/aaii/weekly/`. All three sit inside the encrypted
     backup.
   - **What to check.** No command. After the next nightly sweep, its log should
     show the dth1 inbox "ok", the two archive counts, the aaii weekly count, and
     the count of top-level Drive folders named `chester-x-digest` (1).
8. **a93: IBKR daily bars, after subscribing** (A99's step 7 unchanged). Add the
   conids by a session paste, then:

   ```
   python -m altdata.sources.ibkr_bars plan
   ```

   A paste then sets `enabled: true`. Then `pull` once after the close, then
   `backfill`, then the twenty-session parallel run.
9. **a94: Gemini's key and the budgets** (unchanged). Add `GEMINI_API_KEY` to the
   box's `.env` yourself; set the budgets by a paste; then:

   ```
   python -m altdata.forecasters status
   ```

10. **a96 with A102 and A104.**
    - The FRED families' parallel run, as A99's step 9.
    - **A102's EDGAR writers stay off** (`enabled: false`).
    - **A104's dry runs, still to do.** On the box, where the contact is set:

      ```
      python -m altdata.sources.edgar_xbrl fundamentals --dry-run
      python -m altdata.sources.edgar_xbrl earnings --dry-run
      ```

      Paste the output to a session for A104's Parts 2 and 3. Or put
      `CHESTER_SEC_CONTACT` in the laptop's `.env` and re-run A104 there.
11. **a97, a95, a103:** no box step beyond the deploy.
    - The first editions are the 8 Nov Weekly (A97, A103) and the 1 Dec Monthly
      (A95).
    - The Coverage table's read-only store check runs once per edition.
12. **a98: the paper executor**, by hand, dry first (A99's step 11, unchanged):

    ```
    python -m paper_exec status
    python -m paper_exec run
    ```

13. **b109: the names gate's list** (see N3 for the order).
    - The repository secret `CHESTER_NAMES_DENYLIST`, set only after the sweep
      of the merged main.
    - On the box: `CHESTER_NAMES_DENYLIST=<name>` in the environment the gates
      run under (`.env`).
14. **b96, b89, b90, b91 (with B105), b92, b95-batch-21 (with B108), b81, b87,
    a90, b85-gitattributes, b100 (with B107), b102 (B102, B103):** no box step.

## 6. What A99's script said that this pass changes

- **Step 0 gains b101** (B101, B101b and B106's pins). With it:
  - main's date-drift gates turn green on the merged tree: `validate_monthly`'s
    refunding window, `validate_voices`, `validate_alpha_proposer`,
    `validate_st_t5_render`;
  - A99's "main's B84 is fixed at step 0a" now holds with these beside it.
- **Steps 14, 19, 20 and 25 are new or changed:**
  - a92 now carries A92b, and meets b82 in `aaii.py` and in
    `validate_official_sources` (the resolutions are in section 2);
  - a95 and a103 follow a97 and merge clean;
  - b109's sweep conflicts in sixteen files, and its scan finds what the sweep
    could not see (N3).
- **Step 17 gains a registry conflict** (chain-8's `trend_breadth_signs` against
  A102's `edgar_fundamentals`: both). N1 is unchanged: a96 still lacks 17a.
- **Step 22 (b96)** now also carries B104's Part 12. The take-b96-whole rule
  holds. The base's lines are in b96's, except the four reading-time lines b96
  restates.
- **Steps 23 to 25 are new:** b100 (B107), b102 (B102, B103), b109.
- **The count** ends at 166 code gates (163 Python), not 165: B109's names gate.
- **The box steps:**
  - A92's ledger moves to `chester-cards/` with the cards' header, and the
    archive folders are new;
  - A104's dry runs are still the operator's, on the box (A99 listed none for
    A104; it did not exist);
  - B109's secret is new, with its ordering (N3).
- **A99's full-run problem is half fixed by b100.** A worktree now resolves the
  main checkout's `.venv`, so the right interpreter ran. But on this laptop the
  gate list still reached `scripts/make.sh` with a trailing CR on each path, so
  every gate but a few failed to open (`check_library.py\r`). The full run was
  therefore made gate by gate with the CR stripped (section 4). The CR is a fix
  for the next hygiene paste: `tr -d '\r'` where `make.sh` reads
  `tools/gate_list.py`.
- **Unchanged:** N2, the LF re-checkout and the A-branch pattern.

## 7. CI

CI_PLACEHOLDER
