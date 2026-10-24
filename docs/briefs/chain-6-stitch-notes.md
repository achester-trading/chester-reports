STITCH COMPLETE: CI green at `79cd140` (run 40055201097, 147/147 jobs); every later commit changes notes only (a58's third tip and these notes). Must not merge before the 1 Nov Monthly.

# chain-6: the four post-Monthly branches stitched into one (session B, 23-24 Oct 2026)

**What it is.** One branch, `chain-6`, carrying the four branches built for after the 1 Nov Monthly, so they merge as ONE pull request with every conflict already resolved:
- a57-batch14-b1 (Batch 14 items 65 and 71);
- b55-batch14-b2 (items 62, 67, 68);
- b56-batch15-2 (Batch 15 items 74, 75, 77, 78);
- a58-batch15-1 (Batch 15 filed; items 72, 73, 76).

**chain-6 MUST NOT merge before the 1 Nov Monthly.** chain-5 merges to main on Saturday, which makes chain-6 a clean descendant of main.

**How it was made.** The method of chain-5's stitch:
- merges only, one `--no-ff` merge commit per tip, in the paste's order, each "Merge <branch> into chain-6 (sixth chain, 23 Oct)";
- no rebase, no squash, no force-push;
- each conflict resolved once, as the union where the sides add different things;
- the Master Guide's HTML rebuilt with its builder, never hunk-resolved;
- the gate count recounted from the merged Makefile.

**Branch-only.** I pushed `chain-6` and nothing else. No pull request, no merge anywhere, nothing on the box, no unit, no register write, no `.env`. Its own worktree is `../chester-chain6`; session A's `../chester-a57` was not touched.

## The order, as merged

**Base:** `origin/chain-5` at `6fa2024`. Every ref was fetched at 22:33 ET on 23 Oct, a58 again immediately before its merge and before the final push.

| Step | Branch | Tip merged | Its own CI | Merge commit | Files resolved |
|---|---|---|---|---|---|
| 1 | b55-batch14-b2 | `505d834` | green, run 40050394809 at `eb22e79`, 144/144 (tip notes-only) | `141e953` | none: chain-5 is its base |
| 2 | b56-batch15-2 | `1758a80` (carries a57 `711631b`) | green, run 40053101584 at `c9b7247`, 144/144 (tip notes-only) | `3dfc128` | CLAUDE.md, Makefile, `altdata/config.py`, `config/catalogue_commands.yaml`, the architecture document, `docs/dated-appendix-queue.md`, `tools/validate_audit_3a.py`, `tools/validate_st_r5_t1_rest.py` |
| 3 | a57-batch14-b1 | `711631b` | green, run 40042147115 at `ccac489` (its notes) | **none: a no-op** ("Already up to date": `711631b` is an ancestor through b56's merge `c48c8a1`) | — |
| 4 | a58-batch15-1 | `e219bc8` | **red**: its latest run, 40049370749, failed `validate_secrets` and `validate_st_t2_rates` (a58's own; recorded, not fixed here). A had pushed no fix when it was merged | `9614a68` | CLAUDE.md, Makefile, `altdata/config.py`, the architecture document, the queue, the Master Guide and its HTML, `metrics_registry.yaml`, `tools/validate_prices.py`, `tools/validate_st_r5_t1_rest.py` |
| fix 1 | — | — | — | `d9e0da9` | `tools/validate_batch14_b2.py` (below) |
| 4b | a58-batch15-1, again | `1194a12` (A59: the fix of its two red gates; it moved between the first merge and the final push) | its run 40054872472 queued when merged | `9bc67c0` | none: a clean merge (`validate_secrets`, `dm_drawdown`, its config and notes) |
| 4c | a58-batch15-1, a third time | `a27ca1d` (A59's notes: its round 2 CI green, run 40054872472, 145/145; it moved as chain-6's CI was recorded) | the fix's run 40054872472 green | `eae6a18` | none: a58's notes only |

## Every conflict and its resolution

| File | How |
|---|---|
| `Makefile` | the gate lines' union: `validate_batch14_b2`, `validate_batch14_b1`, `validate_batch15_2`, `validate_batch15_1`, each once |
| CLAUDE.md | each branch's paragraph kept; the config list names each new FRED list (`FRED_HOUSEHOLDS_SERIES` 1, `FRED_BATCH14_B1_SERIES` 4, `FRED_BATCH15_A_SERIES` 1); `FRED_PULL_SERIES, 283`; the worded gate count recounted from the Makefile (below) |
| `altdata/config.py` | both lists' definitions kept; `FRED_PULL_SERIES` the union, `+ FRED_HOUSEHOLDS_SERIES + FRED_BATCH14_B1_SERIES + FRED_BATCH15_A_SERIES` |
| `tools/validate_st_r5_t1_rest.py` | the FRED pin at 283, its comment naming each addition |
| the architecture document's store box | "The pull walks 283 FRED series ... and 126 market symbols", each branch named |
| `tools/validate_audit_3a.py` | `NEW_KEY_BLOCKS` the union: `fred_households` and `fred_batch14_b1` |
| `config/catalogue_commands.yaml` | every module line from both sides |
| `docs/dated-appendix-queue.md` | every append kept, in commit order: b55's NAR record, b56's prime-book and S-1 records, then a58's item 76 records |
| `metrics_registry.yaml`, `tools/validate_prices.py` | the basket blocks at 126 symbols, 106 volume units and 96 shares on both sides (a58 had merged chain-5 itself), so chain-6's side was kept |
| `docs/master-guide.md` | Table 7a with every row (b56's ST-R6.74b row; ST-R6.66c's once); a58's rows merged cleanly |
| `docs/html/master-guide.html` | rebuilt with `tools/build_paper_html.py` |

**Conflicts with a recursive merge base.** a58's merge with chain-6 had two common ancestors, so git wrote nested nine-character markers inside the base section. The resolver read only the seven-character markers, so the nested ones were dropped with the base.

**Fix 1 (what the stitch broke).** `validate_batch14_b2` checked that b55's NAR record ends the appendix queue. With b56's and a58's appends after it, it no longer does. The check now asks that it follow the entries before it, with its source line inside its section.

## The final counts

| Count | Value | From |
|---|---|---|
| Code gates | **137** (134 Python, 3 shell), 8 data gates | chain-5's 133 + one each from a57, b55, b56 and a58, recounted by listing the Makefile (`validate_audit_3a` reads the same) |
| `FRED_PULL_SERIES` | **283** | 277 + b55's 1 + a57's 4 + a58's 1 |
| Security Master `next_id` | **215** | b52's SM00205-212 and a57's SM00213-214; b55, b56 and a58 add none |
| Symbols (`yfinance_source.SYMBOLS`) | **126** | 124 + a57's AIQ and SPXT |

## The gates run locally on the stitched tree

| Gate | Result |
|---|---|
| `validate_audit_3a` | 88/0 |
| `check_registry` | OK |
| `check_library` | 0 failures, 0 warnings |
| `check_master_guide` | 0/0 |
| `validate_st_r5_t1_rest` | 103/0 |
| `validate_prices` | 101/0 |
| `validate_security_master` | 102/0 |
| `validate_narratives` | 103/0 |
| `validate_batch14_b1` | 67/0 |
| `validate_batch14_b2` | 55/0, after fix 1 |
| `validate_batch15_2` | 57/0 |
| `validate_batch15_1` | 69/1 |
| `validate_secrets`, `validate_st_t2_rates` (after a58's fix) | 58/0, 71/0 |

`validate_batch15_1`'s one failure is local only. It holds the Batch 15 order at its SHA-256, and the laptop's checkout converts the file to CRLF (`git ls-files --eol`: index LF, working tree CRLF); CI reads the LF bytes. The stack gates are left to CI.

## The CI rounds

| Round | Run | On | Result |
|---|---|---|---|
| 1 | 40055201097 | `79cd140` | **Green: 147 of 147 jobs** (the stack gates and `smoke_test` among them). The run of the superseded push `8985c3f` (40055143011) was cancelled. Also run locally on the stitched tree: `validate_weekly_edits` 91/0, `validate_monthly` 359/0, `validate_st_t1_rest` 34/0, `validate_digital_addendum` 94/0, `validate_weekly_complete` 96/0, `validate_daily_close` 102/0, `validate_quarterly_stack` 94/0, `validate_backups` passed |

## The box sheet

`docs/briefs/chain-6-box-sheet.md` gathers the four branches' box commands in the order they must run after the merge. Dry runs come first and the ledgers' box editions are written outside the checkout, each step with its expected output.

## Needs you

1. **The post-Monthly pull request**: yes or no to opening chain-6 into main after the 1 Nov Monthly, once chain-5 is on main and chain-6's CI is green.
2. **The box sheet**: yes or no to running it, in its order, after that merge.
