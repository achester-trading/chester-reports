STITCH COMPLETE 65b242c 2026-10-21 00:16 ET

# chain-4: the fourth chain stitched into one branch (session B, 20 Oct 2026)

**What it is.** One branch, `chain-4`, carrying the fourth chain on top of main after chain-3's merge, so it merges as ONE pull request (chain-4 into main) on Wednesday evening. It carries `a50-dealer-store` (A50 and A51), `b48-scoreboard` (B48 and B49) and `a52-doctrine-2-pack` (A52 and A53, Batch 12), plus three small fixes, a fourth where a50 and b48 meet and a fifth for the evening note's timer (fix 5, pasted 21 Oct after the box refused it), the Master Guide refreshed to "as built", and one box sheet (`docs/briefs/chain-4-box-sheet.md`).

**All three branches are in.** `a52-doctrine-2-pack` was final at `cf59056` (the commit that fills A53's notes' CI table green: run 39497773952, 136/136) when its step came, and was still `cf59056` when checked again before Part 4.

**How it was made.** The method of `friday-stitching-notes.md` ("How it was done") and `chain-3-stitch-notes.md`:
- merges only, one `--no-ff` merge commit per tip, in the paste's order, each tip named; no rebase, squash or force-push, and nothing merged to main;
- conflicts resolved by keeping both sides;
- `metrics_registry.yaml` spliced, not hunk-resolved (below);
- the gate count recounted once, at the end, from the merged Makefile;
- after each merge, the method's gates, one at a time.

Branch-only: I pushed `chain-4` and nothing else, ran nothing on the box, and enabled, started or restarted no unit. I read session A's branches (`a50-dealer-store`, `a52-doctrine-2-pack`) and merged them; I pushed to neither. chester-meme was not opened.

## The order, as merged

**Base:** main at `f9ec9e3` ("Merge pull request #40 from achester-trading/chain-3"). chain-3's tip `4f004a4` is its ancestor, checked before the branch was cut. Every ref was fetched at 17:44 ET on 20 Oct (the first fetch, at 15:54 ET, found chain-3 not yet merged, and the stitch waited for it).

| Step | Branch | Tip merged | Base against chain-4 | Merge commit | Files resolved |
|---|---|---|---|---|---|
| 1 | a50-dealer-store | `9c99a49` (A51's green commit; final) | `0d22352` (a49's tip, inside chain-3) | `9676def` | CLAUDE.md (the count line), `tools/validate_a43_render.py` |
| 2 | b48-scoreboard | `47801f6` (B49's notes; B49 green at it; final) | `4f004a4` (chain-3's tip) | `694c47d` | Makefile |
| 3 | a52-doctrine-2-pack | `cf59056` (A53's notes' CI table, green; final) | `4f004a4` | `8c7d72d` | CLAUDE.md, Makefile, `altdata/config.py`, the architecture document, `docs/html/master-guide.html`, `metrics_registry.yaml`, `tools/validate_audit_3a.py`, `tools/validate_st_r5_t1_rest.py` |

## Every conflict and its resolution

| Step | File | Where the lines met | Resolution |
|---|---|---|---|
| 1 | CLAUDE.md | the gate-count line (main 125, a50 122) | Kept main's line; recounted once at the end |
| 1 | `tools/validate_a43_render.py` | the same fix made twice: chain-3's R2 (`32d8baa`) read the vendor rows at a fixed `2099-01-01`, a50's A50 round 1 (`bb33cd5`) at `AFTER_RUN` (now plus a day) | a50's `AFTER_RUN`, both reads; the constant is defined in the merged file. One fix, not two |
| 2 | Makefile | a50's gate line and b48's at the same anchor | Both kept |
| 3 | CLAUDE.md | the layout's FRED line: a50's `FRED_NOTES_SERIES` (1, RSAFS) and a53's `FRED_BANK_STRESS_SERIES` (10), each on 266 | Both named; `FRED_PULL_SERIES` is the union, **277** |
| 3 | Makefile | b48's line and a53's `validate_batch12` | All three gate lines kept |
| 3 | `altdata/config.py` | both lists at one anchor, and the union's two lines | Both lists kept whole; `FRED_PULL_SERIES` adds `FRED_NOTES_SERIES + FRED_BANK_STRESS_SERIES` |
| 3 | `tools/validate_audit_3a.py` | `NEW_KEY_BLOCKS`: `fred_notes` and `fred_bank_stress` | Both kept |
| 3 | `tools/validate_st_r5_t1_rest.py` | the `FRED_PULL_SERIES` pin: 267 (a50) and 276 (a53) | 277, the union, with both histories in its comment (103/0) |
| 3 | the architecture document | its store box: 267 FRED (a50) and 276 FRED, 116 symbols (a53) | 277 FRED and 116 symbols, naming both additions |
| 3 | `metrics_registry.yaml` | a50's `fred_notes` block and a53's `fred_bank_stress` block, both inserted after `fred_group_b`'s last line | **The splice:** each block kept whole, a50's then a53's, at that one anchor; neither touches the other's fields. The duplicate-key sweep found nothing |
| 3 | `docs/html/master-guide.html` | the `source-sha256` meta (build output) | Rebuilt from the merged `.md` inside the merge commit, then again in Part 3 |

**The files the paste expected to meet, and what happened to each.**

| File | Result |
|---|---|
| `daily_cascade/weekly_stack.py` | Merged clean at step 2: a50 changed four lines against b48's base (the Ahead matrix's store path), b48 added the scoreboard at `produce`'s tail and `render`'s head. Both checked present; `validate_weekly_stack` 83/0 |
| `metrics_registry.yaml`'s counts | No count line shared: a50 and a53 each added a block with its own `expected_members` |
| `tools/validate_audit_3a.py` | Step 3, above |
| `docs/change-orders.md`, the signal-triage register's header | Merged clean: only a53 changed them against the base (Batch 12's filing) |
| `docs/master-guide.md` | Merged clean at steps 2 and 3: b48's Table 8 rows and stamp lines, a52's Part 8 link and a53's two Table 7a rows sit at different anchors |
| `monthly_macro/stack.py` | Merged clean: b48's register month and a53's bank-stress sub-section at different anchors |

## The fixes, by commit

| Fix | Commit | What changed |
|---|---|---|
| The recount | `93b223b` | CLAUDE.md: **one hundred and twenty-eight code gates (one hundred and twenty-five Python, three shell)** and eight data gates, from the merged Makefile (below) |
| 1 | `988bd81` | The Master Guide's glossary said the dealer scorecard has "six pre-registered tests", where Part 5 says seven. The registrations hold seven: H1, H2, H3a, H3b, H4 and H5 (17 Oct, `dealer-scorecard-preregistration-2026-10.md`) and H6, the level clusters (19 Oct, `-h6.md`, one hypothesis scored as H6s and H6f). The glossary now says seven and names them |
| 2 | `7dce016` | SR-8: the register's status line (and its summary-table row) read "ADOPTED — audit pending" after `false-bottom-audit-2026.md` recorded **FAIL** (1 element discriminates, the rule needs 2; n 16). Corrected to "ADOPTED — audit failed (…)", linking the ledger, with a dated line under it: "*Factual correction, 20 Oct 2026 (chain-4):* … The ledger's verdict is the record." The Guide's Part 5 loses its "still reads audit pending" parenthetical. No right changes: Book A rule A-2 waits for the monthly, as the ledger says |
| 3 | `cdcca98` | `config/setups.yaml`, `b_style_regime_pair`: the comment "SR-1's ledger (Base Rates) is not yet stored" now reads that it is stored (`sr-1-ledger-2026-10-18.md`, PASS, n 6), the base rate completed at Doctrine #2. A comment only; `base_rate: not yet` unchanged |
| 4 | `2c60f9a` | **The volatile-day flag joins the entry stamp and the score's cuts** (B49's needs-you 3), below |
| 5 | `3be1d7c` | **The evening note's timer** (pasted 21 Oct 2026). On the box (systemd 255) on 20 Oct, `systemctl --user enable chester-evening-note.timer` refused the unit with "bad unit file setting": `OnCalendar=Sun..Thu 21:30` runs backwards, because systemd orders the week Monday to Sunday. `validate_secondary_notes` pinned the same string, so the gates passed it. **The timer** now reads `OnCalendar=Mon..Thu,Sun 21:30 America/New_York`, the same five evenings the secondary-notes order rules (its Description and comments unchanged). **The same line** in `validate_secondary_notes`'s pin (88/0) and the Master Guide's Table 1 row; figure 2 regenerated (the evening note now reads as a five-evening job on the clock, as the meme ingest's `Mon..Fri,Sun` does); the HTML edition rebuilt; `check_master_guide` 0/0. a49's dated notes stay as the record they are. **`validate_systemd_units`** refuses a backwards weekday range (`..` or `-`) in any `OnCalendar=` under `deploy/systemd/`, with four self-test fixtures (`Sun..Thu` and `Fri-Mon` refused; `Mon..Thu,Sun` and `Mon..Fri,Sun` pass), 166/0 on the laptop. **systemd-analyze:** CI's runner is `ubuntu-24.04`, which ships systemd and `systemd-analyze`, so the gate also runs `systemd-analyze calendar` on every `OnCalendar=` there; where the tool is absent (the Windows laptop) it prints NOT RUN and counts nothing. **The box sheet** gains T1, the enable step after the merge |

### Fix 4, the volatile-day flag at entry

**Read from a51's `daily_cascade/volatile_day.py` output as printed, never computed.**
- **Where the printed flag lives.** The 09:50 open note already archives its payload JSON, with the settled flag in it. The 07:00 anchor archived only its HTML, so a live anchor now also archives the flag it printed, `morning_anchor_<session>_volatile_day.json`, beside the HTML (`volatile_day.sidecar_json`). A dry run writes none, and `reports/dryrun/` is never read.
- **The reader.** `volatile_day.printed(day, at)` reads the day's live edition from the reports archive. The open note's settled flag comes first, else the anchor's. An edition archived after the entry instant is not read. With no edition, the state is None with its reason. It re-reads no arm and opens no store (the gate holds this by source).
- **The stamp.** `heat.regime_band`, which the order gate already calls at entry, carries `volatile_day` ("raised" / "not raised"), `volatile_day_settled` and `volatile_day_source`, or `volatile_day_reason`. `decide._gate_detail` keeps them in the decision's existing `gate_detail` JSON field. **No schema change, no migration, no new write path.**
- **The cuts.** `register/scoreboard.DIALS` gains the flag. `expectancy_13w` cuts `by_volatile_day`: an absent stamp prints "(flag not printed at entry)", and a decision from before chain-4 prints "not stamped". The Monthly's register month prints "By the volatile-day flag at entry: …".
- **Fixtures:** `validate_b48_scoreboard` group G (14 checks, 69/0), on synthetic fixtures. They cover:
  - the anchor's flag read unsettled;
  - an open-note dry run ignored;
  - the settled open note winning over the anchor;
  - a late-archived edition skipped;
  - the absent day named;
  - the read-only source check;
  - the live-path-only sidecar;
  - the regime read, the entry record, the cut and its line, and the Monthly's line.
- **Rights unchanged.** The flag is printed, never applied. No size, packet or decision right changes, and nothing enters a composite or the market-state object.

## Part 3: the Master Guide, as built on chain-4

Commit `0c0dc69`. As of 20 October 2026, "as built on chain-4".
- **Landing next:** every item chain-4 carries reads as built, with where it is described, and no branch waits.
- **The cards:**
  - the anchor: the volatile-day flag's four arms, printed, never applied, archived as printed;
  - the open note: the settled-flag block and its prose gate;
  - the close: the bank-stress item and the classifier's line;
  - the Weekly: the bank-stress line;
  - the Monthly: the bank-stress panel, the P/E dispersion lines, and the register month's cuts by the stamped dials and the flag.
- **Part 4:**
  - 33 official writers (OFR FSI, FDIC; ICI a listed gap, FRED's retail series in its place);
  - 277 FRED series;
  - 116 symbols (KRE);
  - the bank-stress flags, display only;
  - the dealer store and the 09:45 bars;
  - engine 7's bars;
  - the superseding batch.
- **Part 5 and Tables 7a and 7b:**
  - Part 5's counts move from 21 gated verdicts to **22 (1 passed, 13 failed, 8 insufficient; 12 accruing)**, with ST-R6.59c's FAIL. a53's notes left this to the chain refresh.
  - Table 7a already carried a53's two rows.
  - Table 7b gains three rows: the bank-stress flags and classifier (failed by their ledger), the volatile-day flag (untested, printed), and item 60's listed gaps. The scoreboard row gains the stamped cuts.
- **Tables 1, 2 and 9:**
  - Table 1 is unchanged, because chain-4 adds or changes no timer; a note under it says so.
  - Table 2 is unchanged (no chat task changed).
  - Table 9 is unchanged (no paper added, renumbered or resized; `check_library` reports no stale word total after b48's two change-record lines).
- **Parts 6, 7 and 8, and the glossary:** the stamp as built. Part 8 already links the Doctrine #2 pack (a52). The calendar links the pack for 7–8 November and adds 28 October, the Monthly's last dry run, which a53 asks chain-4 to precede.
- **Figures 2 and 5:** regenerated, no change.
- **The HTML edition:** rebuilt (Aptos).
- **Checks:** `check_master_guide` 0/0; `check_library` 27 papers, 0/0.

## The counts, recomputed once

From the merged Makefile at the end: **one hundred and twenty-eight code gates (one hundred and twenty-five Python, three shell) and eight data gates**. The three new gates are `validate_a50_dealer_store`, `validate_b48_scoreboard` and `validate_batch12`, on chain-3's 125. CLAUDE.md's count line (`93b223b`) is the only place that prints it, and `validate_audit_3a` holds it (88/0 after the recount).

The other counts that met:
- **`FRED_PULL_SERIES`: 277.** That is 266, plus a50's RSAFS, plus a53's ten. The count appears in CLAUDE.md, the architecture document and `validate_st_r5_t1_rest`.
- **Only a53 moved the other counts:** the basket to 116, the official writers to 33, and the volume units.

## The gates

Run locally after each merge, one at a time, as the method lists them. Every exit is the gate's own.

| After | Gates | Result |
|---|---|---|
| 1 (a50) | `validate_a50_dealer_store`, `validate_a43_render` (its conflict), `check_registry`, `validate_prices`, `validate_gates`, `validate_config_refs`, `validate_weekly_stack`, `validate_audit_fixes`, `validate_audit_3a`; the duplicate-key sweep (84 files, 0) | all pass except `validate_audit_3a` 87/1, the count line only (expected until the recount). **`validate_monthly_stack` ran past ten minutes locally and was stopped** (it renders); left to CI |
| 2 (b48) | `validate_b48_scoreboard`, `validate_a50_dealer_store`, `validate_a47_chain3`, the method's seven less the Monthly stack; the sweep (85, 0) | all pass |
| 3 (a52) | `validate_batch12` 57/0, `validate_st_r5_t1_rest` 103/0, `validate_dealer_block` 134/0, `validate_security_master` 102/0, `validate_narratives` 103/0, `validate_numeral_audit` 172/0 (the gates a53's changed files feed), `check_registry`, `validate_prices` 101/0, `validate_gates` 32/0, `validate_config_refs` 107/0, `validate_audit_fixes` 103/0, `validate_weekly_stack` 83/0, `check_master_guide` 0/0, `check_library` 0/0, `validate_audit_3a`; the sweep (87, 0) | all pass except `validate_audit_3a`: the count line only (126 printed, 128 in the code), fixed in `93b223b` (88/0) |
| Fix 4 | `validate_b48_scoreboard` 69/0, and the gates its files feed: `validate_a50_dealer_store` 72/0, `validate_enforce` 49/0, `validate_morning_anchor` 71/0, `validate_secondary_notes` 88/0, `validate_book_b_scanner` 63/0, `validate_numeral_audit` 172/0, `validate_secrets` 58/0, `validate_system_metrics` 21/0 | pass. `validate_book_b_scanner`'s first run died printing "≤" to the Windows console (cp1252); re-run with `PYTHONIOENCODING=utf-8`, 63/0. A laptop quirk, not a fault: CI is Linux |
| Part 3 | `check_master_guide` 0/0, `check_library` 0/0 | pass |

Every other gate, and anything that renders a PDF (the Monthly stack among them), was left to CI.

## The CI rounds

| Round | Run | On | Result |
|---|---|---|---|
| 1 | 39523575613 | `ea68f77` (the fixes, the Guide, these notes and the box sheet) | **failed**, 136 of 138 jobs green: `validate_st_t3_calib` (and the summary job `gates-passed`). Two of its pins hash the signal-triage register's Index table (35 rows) and SR-8's entry, and fix 2 had corrected both. Re-pinned with a dated note in `784da5d` (the correction stands; no other row or entry changed), 88/0 locally |
| 2 | 39541999251 | `65b242c` (fix 5, the re-pin, these notes) | **green**, 138/138 jobs: every code gate, the data gates (each reports, never sets the exit code), the shell gates and the smoke test. `validate_systemd_units` 199/0 on the runner, where `systemd-analyze calendar` parsed all 33 `OnCalendar=` specs under `deploy/systemd/`, the evening note's `Mon..Thu,Sun 21:30 America/New_York` among them |

## What stayed out, and why

- **Nothing of the three branches.** All three are in, at their final tips.
- **Session A's needs-you items not ruled in this paste**, listed below. This paste applies only the four fixes.
- **The ledger edition for ST-R6.59c on the box:** none asked. It reads public sources only, so the laptop's first edition stands (box sheet D).
- **a53's in-order differences** (ICI → FRED's retail series, KRE only, the classifier in the Monthly's panel, the dispersion as lines) stand as a53 built them; the code wins over the order (a53's notes, section 6).

## Needs you

1. **The box sheet,** `docs/briefs/chain-4-box-sheet.md`, for the merge evening, with T1: enable the evening note's timer once the fixed unit has been copied. It covers the dealer-store backfill, the RSAFS history, Batch 12's first pulls and the superseding batch's registration, dry runs first. If chain-3's sheet has not run yet, run it first.
2. **The pull request** (base main, compare chain-4), to open on Wednesday afternoon. a53 asks that it land before the Monthly's last dry run on 28 October.
3. **Fix 4's new archive file:** a live 07:00 anchor now writes `reports/morning_anchor_<session>_volatile_day.json` beside its HTML. That is the flag as printed, which the order gate reads at entry. Say if it should live elsewhere.
4. **A51's session-set values:** the index-mover rule and `min_atr_sessions` 15. Confirm or replace.
5. **a53's (Batch 12):**
   - KRE's implied vol: add KRE to the capture universe, or keep it a gap.
   - ICI: keep FRED's retail series in its place, or name another keyless total.
   - The session-set values (a53 section 5).
   - ST-R6.59c's FAIL (n 18), a rule-31 draft for your accept-all.
   - The narrative pair, after the next seed: confirm or reject.
6. **a52's pack:** read it before 7 November; it is the agenda's first page.
