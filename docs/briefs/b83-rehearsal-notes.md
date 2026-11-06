# B83 rehearsal notes: chain-7's post-Monthly merge

Paste B83 (`docs/pastes/B83.md`), 28 Oct 2026. Branch `b83-chain-7-rehearsal`, a
throwaway: never merged, deleted after Monday's real merge. No other branch was
touched.

This is the script for Monday's merge of chain-7-main into main (D31).

## What was merged

- **chain-7-main:** `dfa14a54` (unmoved since the paste).
- **main:** `8166d430`, which holds A61b (`9fd6bd40`, with A83's FEEDS line) and
  A78 (`8166d430`, PR #43). The merge base is `efe02994`.
- **A85 was not on main** when the rehearsal ran. Its branch,
  `a85-midterm-copyback` at `4b8d9d2d`, was previewed with `git merge-tree`
  against the merged result, which writes nothing to the tree. Its three
  conflicts are in their own section below.

The merge commit is `9ddcca77`, made with `git merge --no-ff origin/main` and no
rebase.

## Conflicts with main at 8166d430, and their resolutions

| File | Hunk | Rule | Resolution |
|---|---|---|---|
| `Makefile` | the gate list: chain-7's five gates (`validate_batch14_b2`, `_batch14_b1`, `_batch15_2`, `_batch15_1`, `_b59`) against A78's `validate_batch16_midterm` | additive, Makefile gate lines | both kept, chain-7's first |
| `docs/change-orders.md` | Batch 15's index line against Batch 16's | additive, index lines | both, in date order (15, then 16) |
| `docs/dated-appendix-queue.md` | chain-7's four sections (item 36's housing record; items 74, 75 and 76) against A78's Base Rates section (items 80(b) and 90) | additive, the dated-appendix queue | both, chain-7's first |
| `docs/signal-triage-register.md` | the batch-orders cell: chain-7 adds 15, A78 adds 16 | additive, register cells | spliced to "... [14] (...), [15] (...), and [16] (...)". The SR rows did not conflict: chain-7 adds none past SR-59, and A78's SR-60 to SR-64 merged clean |
| `docs/master-guide.md` | the ledger table: chain-7's `oneday-10y-preregistration-2026-10.md` against A78's `midterm-base-rate-2026-10-26.md` | additive | both kept, and the table's alphabetical order restored (midterm, then oneday) |
| `CLAUDE.md` | (1) the gate count: chain-7 says 140 (137 Python), main 135 (132), base 134 (131) | counts by the S1 tool, never by hand | chain-7's line kept as a placeholder, then rewritten by `stitch_counts --write` (see Counts) |
| `CLAUDE.md` | (2) the build text: chain-7's B2, b59 and Batch 15 session B paragraphs against A78's Batch 16 midterm paragraph | additive | both, chain-7's first |
| `docs/html/master-guide.html` | build output | build output is regenerated, never merged | rebuilt from the merged `.md` with `tools/build_paper_html.py docs/master-guide.md`; it carries both new ledger rows |

Seven files and eight hunks. None was code, so nothing needed a decision.

## Counts

The S1 stitch tools are on neither side of this merge. They exist only on
`s1-stitch-refactor`, `a77-6i-tranches-1-2-5` and `a79-6i-tranches-3-4`.

- **`tools/stitch_counts.py`** was copied from `origin/s1-stitch-refactor` into
  `tools/` for the run and deleted afterwards (not committed). It imports this
  tree's own `validate_audit_3a`, whose `code_counts`, `PRINTED_COUNTS`,
  `ARCH_COUNTS`, `TENS` and `number` it needs, and all are present here.
- **`tools/gate_list.py`** cannot run here: it reads `GATE_KIND` declarations
  that no gate on either side carries yet. The Makefile is still the gate list,
  and `validate_audit_3a` counts from it.

`stitch_counts --check` found 59 counts, of which two disagreed. `--write` moved
these, and a second `--check` read 0 disagreeing and 0 faults:

| Where | Count | Before (chain-7) | After |
|---|---|---|---|
| CLAUDE.md | code gates | one hundred and forty | one hundred and forty-one |
| CLAUDE.md | Python gates | one hundred and thirty-seven | one hundred and thirty-eight |

Every other count (the FRED lists, the writers, the symbols, the registry's bulk
blocks, the architecture box) was unchanged.

**Monday:** if S1 has merged by then, run its tools from the tree. If not, copy
`stitch_counts.py` in the same way.

## Gates

Run one at a time, in the foreground.

| Gate | Why | Result |
|---|---|---|
| validate_batch16_midterm | Makefile, dated-appendix queue, change-orders | 27 passed |
| validate_batch15_1 | Makefile, change-orders, register | 69 passed, **1 failed**, see below |
| validate_batch15_2 | Makefile, register | 60 passed |
| validate_batch14_b1 | Makefile | 68 passed |
| validate_batch14_b2 | Makefile, dated-appendix queue | 57 passed |
| validate_batch14_a1 | dated-appendix queue | 30 passed |
| validate_b59 | Makefile | 83 passed |
| validate_a43_render | register | 46 passed |
| validate_st_t3_calib | register | 88 passed |
| check_library | CLAUDE.md, docs links | 0 failures, 0 warnings |
| check_registry | standing | OK |
| check_master_guide | master guide | 0 failures, **1 warning**, see below |
| validate_audit_3a | CLAUDE.md counts | 88 passed |

- **validate_batch15_1's one failure is not the merge's.** "The Batch 15 order is
  on file at its SHA-256" hashes the working-tree file. On the Windows laptop git
  checks it out with CRLF (281 CRs), so the hash differs. The committed blob
  hashes to the pinned `d5318a6d...`, and the merge did not touch the file.
  Linux CI reads LF and passes. No fix.
- **check_master_guide's warning:** the Guide is as of 23 Oct 2026, older than
  the newest change order (26 Oct). This is not a merge break; it is the chain
  merge's own refresh (see Monday's steps).

## A85, previewed (main had not taken it)

`git merge-tree` of `a85-midterm-copyback` (`4b8d9d2d`, based on main
`8166d430`) against this merge gives three conflicts. All are additive:

| File | Hunk | Resolution on Monday |
|---|---|---|
| `docs/attention-log.md` | chain-7 rewrote the D28-D29 row ("D1–D27 are the row above") and added the D1-D27 and D30-D34 rows; A85 keeps the base's D28-D29 wording and adds the D35-D41 row (27 Oct) | chain-7's three rows as they stand, then A85's D35-D41 row; A85's copy of the D28-D29 row is dropped (chain-7's supersedes it) |
| `docs/master-guide.md` | the ledger table, where chain-7's `oneday-10y-preregistration` meets A85's `midterm-base-rate-2026-10-28.md` (the box's re-run, a second dated edition; the 10-26 row stays) | both: midterm 10-26, midterm 10-28, then oneday |
| `docs/master-guide.md` | the ST-R6 rows, where chain-7's 65a, 71d and 74b meet A85's `st-r6.66c-ledger-2026-10-28.md` | both; 66c-28 goes directly after the existing 66c-21 row, which is where chain-7's table already keeps 66c |
| `docs/html/master-guide.html` | build output | rebuilt from the merged `.md` |

A85 also changes `tools/validate_batch16_midterm.py` and
`config/weekly_ahead.yaml`. Neither conflicts; run `validate_batch16_midterm`
again after A85 lands. A85 adds no gate, so the counts above hold.

## Monday's steps

1. `git fetch`; state chain-7-main's and main's SHAs. Expect main to hold A85 by
   then.
2. `git merge --no-ff origin/main` into chain-7-main's merge branch.
3. Resolve the eight hunks above and A85's three, by the same rules.
4. Run `stitch_counts --check`, then `--write`; then `--check` again.
5. Refresh the Master Guide as a chain merge requires: its "As of" line, its
   tables and Landing next. Then rebuild `docs/html/master-guide.html`.
   check_master_guide's warning should clear.
6. Run the gates in the table above, plus `validate_batch16_midterm` after A85.
   Expect validate_batch15_1's SHA check to fail on a Windows checkout only.

## Needs you

1. **The S1 tools are not on main or chain-7.** Monday's "counts by the S1 tool"
   means either S1 (`s1-stitch-refactor`) merges first, or the stitcher copies
   `stitch_counts.py` in as this rehearsal did. Which is it?
2. **The Master Guide's refresh** (step 5) is a chain-merge task, and this
   rehearsal did not do it. It needs its "As built" line written for chain-7.
3. **validate_batch15_1's SHA check fails on any Windows checkout**, because git
   checks the order out with CRLF. The gate's rule is not changed here (B83 fixes
   only what the merge broke). A `.gitattributes` `-text` or `eol=lf` line for
   pinned files would remove it; is that wanted?
