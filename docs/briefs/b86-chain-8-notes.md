# B86 notes: chain-8 assembled on a rehearsal branch

Paste B86 (`docs/pastes/B86.md`), 29 Oct 2026. Branch `b86-chain-8-assembly`, a
throwaway: the real chain-8 branch is cut from it next week. No existing branch was
touched.

## Next week's order

1. **chain-7 into main.** B83's script (`docs/briefs/b83-rehearsal-notes.md`), now
   with main at `422ea697`. Merge 0 below rehearsed main's three later merges (A85,
   A88, B84) against it: three conflicts, exactly as B83 predicted.
2. **chain-8.** Cut from this branch's tip; its merges are numbered below. **a71 and
   a79 are not on it**: each waits on a needs-you.
3. **Then, on their own, in this order:**

| Branch | Tip | Expected conflicts after chain-8 (`git merge-tree` against this tip) |
|---|---|---|
| a84-feed-summary-and-allowances | `636b9173` | none |
| b81-batch-18-overnight-session | `6256a67c` | `docs/change-orders.md` (the index line: run `tools/change_orders_index.py --write`); `docs/signal-triage-register.md`, where B81's SR-68 block sits beside a81's SR-65 to SR-67 block (keep both; SR-68 stays the next free number), and the batch-orders cell (`--write`) |
| b82-aaii-bearish-share | `bd01fe67` | none |
| b85-crypto-derived-keys | `ea32b154` | none |
| b85-gitattributes-lf | `5cb338fa` | none. Merge it early: it ends validate_batch15_1's Windows-only hash failure |

## Membership

| # | Branch (tip) | It carries | Source for "chain-8" |
|---|---|---|---|
| 1 | s1-stitch-refactor (`6ed16538`) | the stitch tools | a77 is built on it (`a77-6i-notes.md` line 5: "Base: origin/s1-stitch-refactor"); the paste: tools first |
| 2 | a71-audit-leftovers (`6d8af770`) | a65 to a70 | `a65-6f-tranche4-notes.md` :67 "The box sheet line (chain-8)"; `a66-capex-guidance-notes.md` :154 "for the chain-8 box sheet", :9 and `a71-audit-leftovers-notes.md` :3 "Nothing here merges before the 1 Nov Monthly" |
| 3 | b70-quarterly-readers-2 (`c0238982`) | b63 to b69 | `b69-quarterly-readers-1-notes.md` :112 and `b70-quarterly-readers-2-notes.md` :78 "Box commands, for chain-8's box sheet" |
| 4 | a79-6i-tranches-3-4 (`8e1bed1b`) | a77 | `a77-6i-notes.md` :7 and `a79-6i-3-4-notes.md` :7 "This branch merges after the 1 Nov Monthly"; :137 / :99 "for chain-8's box sheet" |
| 5 | a80-learning-loop-ll2-ll4 (`56e89f90`) | b73 | `b73-learning-loop-ll1-notes.md` :4, :171 "for chain-8's box sheet"; `a80-learning-loop-notes.md` :7 "merges after the 1 Nov Monthly" |
| 6 | b75-gold-spine (`c91f8582`) | — | D37 ("gold spine Tranche A ... merge with chain-8 on 2 Nov for the 8 Nov Weekly"); `b75-gold-spine-notes.md` :4 |
| 7 | b76-trend-breadth (`9fb558d9`) | — | D37; `b76-trend-breadth-notes.md` :4 "merges with chain-8 on 2 Nov" |
| 8 | a81-batch-17-filing (`6d03c611`) | — | the operator's ruling of 29 Oct (B86's needs-you): joins chain-8 last |
| 9 | b58-sources-check (`b55b8dca`) | — | the operator's ruling of 29 Oct: joins chain-8 last, after a81 |

**No document states an order among 1 to 7.** The order used is S1 first (the
paste), then the stacks.

**Not in chain-8:**
- **The library papers** (XXVII, XXIX, XXX, XXXI, XXXII, phase-3a, ei-figures).
  D30: "merges by its own PR after review"; D38: "XXVII merges first". That is
  the library line, never through a chain.
- **b79:** D39.
- **a84, b81, b82, b85:** the paste.
- **a58, b55, b56:** already on chain-7.

## Base

- `origin/b83-chain-7-rehearsal` at `fa1c83f4`.
- Main had moved, to `422ea697` (A85 `f380e12e`, A88 `42a1203b`, B84
  `422ea697`), so it was merged in first (merge 0).

## The merges

Counts are by `tools/stitch_counts.py` throughout, and the gate list by S1's
declarations. Gate tallies are from runs one at a time in the foreground. "CRLF"
means validate_batch15_1's hash check on a Windows checkout, which b85-gitattributes-lf
fixes; CI on Linux passes it.

**Merge 0: origin/main** (`c015b2a4`)
- Conflicts, as B83 previewed for A85:
  - `docs/attention-log.md`: chain-7's three rows, then A85's D35-D41 row; A85's
    copy of the D28-D29 row is dropped.
  - `docs/master-guide.md`'s ledger table: midterm 10-26, 10-28, then oneday;
    66c-28 after 66c-21.
  - `docs/html/master-guide.html`: rebuilt.
- Counts: 59, 0 disagree, none moved.
- Gates: check_master_guide, check_library, validate_batch16_midterm 27,
  validate_numeral_audit 172, validate_monthly_frames 39.

**Merge 1: s1-stitch-refactor** (`516ff684`)
- `Makefile`: S1's form, so the list is the gates' `GATE_KIND`. The one gate on
  our side S1's list lacked, `validate_batch16_midterm` (A78, from main), gains
  its declaration.
- `CLAUDE.md`: 141 → 143 code gates, 138 → 140 Python.
- The dated-appendix queue moves to S1's one file per entry. A78's Base Rates
  entry (from main) gains its entry file, byte for byte, so the generated index
  equals the merged queue (15 entries).
- Gates: validate_gates, validate_stitch_tools, validate_stack_hooks,
  validate_audit_3a 88, check_master_guide, check_library, check_registry,
  validate_deploy, validate_batch16_midterm, validate_batch14_a1, validate_batch14_b2
  pass; validate_batch15_1 70/1 (CRLF).
- validate_monthly_stack did not finish on the laptop in ten minutes, with no FAIL
  in its output; CI runs it.

**a71-audit-leftovers: merged, then ABORTED.** See needs-you 1.
- Before the stop, every conflict was resolved:
  - CLAUDE.md, the Makefile, the master guide's HTML;
  - A68's queue, applied to S1's entry files (preface; six entries kept; eight
    moved records' files removed; A78's kept);
  - validate_batch14_a1, 15_1 and 15_2, where A68's logic now reads the queue
    through `queue_text`;
  - `GATE_KIND` on validate_audit_leftovers and validate_edgar_guidance;
  - counts 143 → 145 code gates.
- All of it is saved as a patch for the rerun. Gates at the stop:
  - validate_6f_calibration, validate_audit_leftovers, validate_batch14_a1 and
    14_a2, validate_batch15_2, validate_edgar_guidance, validate_secrets,
    validate_security_master and validate_stitch_tools pass;
  - validate_batch15_1 69/2: CRLF, and "the committed index and cell are what
    the tool writes".

**Merge 2: b70-quarterly-readers-2** (`e21a3535`, fixed by `068a72aa`)
- `Makefile`: S1's form; validate_quarterly_readers_1 and _2 gain `GATE_KIND`.
- `CLAUDE.md`: 143 → 145 code gates, 140 → 142 Python.
- Gates: validate_quarterly_readers_1 48, _2 30, validate_audit_3a 88,
  validate_st_r5_t1_rest, check_registry, validate_feeds_scheduled,
  validate_b51_registry_html, validate_quarterly_stack, check_library,
  check_master_guide.
- **A silent misplacement, fixed in `068a72aa`.** git appended b69/b70's 88 family
  lines after main's `member_overrides` block, with no conflict marker, so those
  keys lost their family (validate_lenses failed). They were moved back to the
  end of `families`. Monday: check `families` after this merge (run
  validate_lenses).

**a79-6i-tranches-3-4: merged, then ABORTED.** See needs-you 2.
- Before the stop, resolved:
  - the 6i brief (ours, b63's plus its CI line);
  - `altdata/config.py`: both new lists (b69's OVX, a79's DBAA and BAA) and both
    in the union, FRED pull 284 → 286;
  - `config/quarterly_chapters.yaml`: a row-level three-way merge, no row changed
    on both sides;
  - validate_audit_3a's blocks (fred_6i and fred_6i3);
  - validate_st_r5_t1_rest's count (286, the code's own);
  - CLAUDE.md and the architecture box (286; 149 code gates).
- Saved as a patch. Gates at the stop:
  - validate_quarterly_readers_1 and _2, validate_tb_harness, _tb_harness_fpr,
    validate_themes_panels, validate_stack_hooks, validate_st_r5_t1_rest,
    validate_audit_3a, check_registry, validate_fred_history and
    validate_quarterly_stack pass;
  - validate_lenses failed on merge 2's misplacement (fixed since);
  - **validate_quarterly_rows_6i failed.**

**Merge 3: a80-learning-loop-ll2-ll4** (`d082820a`)
- `Makefile`: S1's form; validate_decision_quality, _error_corpus, _postmortems
  and _value_of_information gain `GATE_KIND`.
- `CLAUDE.md`: 145 → 149 code gates, 142 → 146 Python.
- Gates: the four new ones, validate_book_b_scanner 63 (with
  `PYTHONIOENCODING=utf-8`: its PASS lines print a ≤ the Windows console cannot),
  validate_narratives, validate_thesis_register, validate_claims, validate_grader,
  check_registry, validate_lenses, validate_audit_3a 88, validate_weekly_storyline.

**Merge 4: b75-gold-spine** (`e4a2dbd2`)
- `metrics_registry.yaml`: market_state_barred, B73's and B75's rows both.
- The master guide's ledger table: the gold rows before the midterm rows; its HTML
  rebuilt.
- CLAUDE.md: B73's and B75's paragraphs both; 149 → 152 code gates, 146 → 149
  Python.
- `Makefile`: S1's form; validate_gld_exposure, _gold_attribution and
  _weekly_gold_block gain `GATE_KIND`.
- Gates: those three, validate_stack_hooks, validate_stack_cadence,
  validate_weekly_edits, check_registry, validate_lenses, check_master_guide,
  validate_audit_3a 88, validate_daily_close, validate_weekly_stack.

**Merge 5: b76-trend-breadth** (`29dedca7`)
- `metrics_registry.yaml`: three same-place insertions, both sides kept.
- validate_audit_3a: fred_6i and trend_breadth_signs.
- CLAUDE.md: 152 → 153 code gates, 149 → 150 Python.
- The Makefile: S1's form.
- A merge break, fixed: validate_trend_breadth's "the gate is in the Makefile's
  list" read the Makefile, which since S1 names no paths. It now reads
  `gate_list.makefile_text()`, as S1 converted every other gate's same check.
- Gates: validate_trend_breadth, validate_audit_3a 88, check_registry,
  validate_lenses, validate_weekly_edits, validate_derived, validate_weekly_stack.
  validate_monthly_stack's run is unconfirmed: its output file was overwritten by
  a later gate's; CI runs it.

**Merge 6: a81-batch-17-filing** (`a8d216c4`)
- The register's batch-orders cell: S1's tool wrote it (14, 15, 16 and 17). The
  index line and SR-65 to SR-67 merged clean.
- Gates: check_library, check_master_guide, validate_narratives,
  validate_batch14_b2; validate_batch15_1 70/1 (CRLF).

**Merge 7: b58-sources-check** (`e8a39f0f`)
- No conflict: one brief added.
- check_library passes.

**Counts across the assembly**, from chain-7's rehearsal to this tip:
- code gates 141 → 153 (Python 138 → 150; shell 3; data 8);
- FRED_PULL_SERIES 283 → 284 (b69's OVX; a79's two would make it 286);
- every other printed count unchanged.

`stitch_counts --check` reads 60 counts, 0 disagree, and both indexes agree with
the tree.

## Needs you

1. **a71 waits on the order index's file pattern.** S1's
   `tools/change_orders_index.py` indexes only `change-order-*-YYYY-MM-DD.md`.
   A70's record order is `change-order-amendment-3-2026-09-13-record.md`, so
   `--write` drops its row, and validate_batch15_1's "the committed index and cell
   are what the tool writes" fails while the hand row stays. Either rename A70's
   file to end in its date (it is linked from the index and A70's notes), or widen
   S1's `ORDER_RX` to allow a `-record` suffix. Then rerun the a71 merge from the
   saved resolution.
2. **a79 waits on validate_quarterly_rows_6i's pins.**
   - A77's gate pins, family by family, the "not stored" rows that 6i-1
     classified, with later switches recorded in `LATER_SWITCHED` and the
     arithmetic "230 less the rows switched, plus the two remainders".
   - b69/b70's readers switched 15 of those rows: oil 5, agriculture 5, crypto 4,
     currency 1. They left three split remainders: "Crude skew", "RWA holder
     count" and "WASDE production and trade lines".
   - The merged counts move to oil 20, currency 17, crypto 63, agriculture 11.
   - Recording that means extending `LATER_SWITCHED` and the remainder
     arithmetic, which is a change to session A's gate. Who makes it, and does it
     land on a79 before chain-8?
3. **Merge 2's silent misplacement** shows a textual merge of
   `metrics_registry.yaml` can move family lines into the wrong map with no
   conflict marker. Should validate_lenses be in every chain stitch's must-run
   list? It is in this script.
4. **The Master Guide's refresh** ("As of", tables, Landing next) is the chain
   merge's job and was not done here. The guide is as of 23 Oct.

## The saved resolutions

Patches of each aborted merge's resolved index, outside the repo (session B's
scratchpad, `a71-merge-resolution.patch` and `a79-merge-resolution.patch`). Rerun:
`git merge --no-ff --no-commit origin/<branch>`, then
`git apply --index --3way <patch>`. Rebase the patch by hand if the tip has moved.
