# Chain-10: the filing and data branches (B112, 5 Nov 2026)

**Branch.** `chain-10`, new, from `origin/main` at `7460ab92`. That is chain-8's
merge (PR #48), and `b86-chain-8-assembly` at `9afea764` is its ancestor. Chain-9
(PR #47, `2fac29d5`) is under it.

**Plan.** A105's script, section 2, steps 2 to 13
(`docs/briefs/a105-merge-week-script.md` on `origin/a105-merge-week-rehearsal-2`,
`b8023fba`). Each step is one merge commit.

**After every merge:**

- the must-runs:
  - `stitch_counts`, `change_orders_index` and `appendix_queue_index`, each with
    `--check`;
  - `validate_lenses`;
  - `check_registry`;
  - `yaml_section_check` against both parents;
- the gates the script names for that step.

Every gate ran one at a time, in the foreground.

**Merged:** all twelve; nothing was aborted, and no needs-you was raised.

## The merges

| Step | Branch (tip) | Merge | Conflicts and resolution | Gates |
|---|---|---|---|---|
| — | the paste | `4f3b90c9` | — | must-runs clean |
| 2 | a90-monthly-dryrun-2 (`08757f97`) | `e5d04324` | none | `audit_fixes` 171/0, `numeral_audit` 172/0, `monthly` 377/0 (1 skipped) |
| 3 | b95-cboe-held (`2250b5cb`) | `83d57e0e` | none | `feed_repair` 59/0, `st_r4_t1b` 71/0 |
| 4 | a84-feed-summary-and-allowances (`636b9173`) | `4528a1ee` | none | `b51_registry_html` 25/0, `feed_repair` 59/0 |
| 5 | b81-batch-18-overnight-session (`6256a67c`) | `6980438d` | change-orders: both; the register's cell: ours, then `--write`; SR-65 to 67, then SR-68 | `check_library` 0 failures |
| 6 | b82-aaii-bearish-share (`bd01fe67`) | `486792ff` | none | `official_sources` 377/0 |
| 7 | b85-crypto-derived-keys (`f864e8f6`) | `06a2677d` | `derived.py` `DECLARED_STATUSES` combined by hand (b95's `held` comment, b85's `declared_until` comment, one tuple with `held`); `metrics_registry.yaml` `member_overrides`: both | `crypto_sources` 123/0, `feed_repair` 59/0, `audit_3a` 88/0, `b51_registry_html` 25/0 |
| 8 | b87-yields-direction (`ec96ceec`) | `9b54cc1f` | none | `audit_fixes` 174/0 |
| 9 | b89-cboe-terms-check (`4e737488`) | `47142fd9` | none (docs) | must-runs |
| 10 | b90-nautilus-assessment (`d7ab0ea8`) | `5258b067` | none (docs) | must-runs |
| 11 | b91-batch-19-filing (`96e97e08`, with B105) | `6107dd6c` | the cell: ours, then `--write`; pairs: both; SR-69 to 72 clean | `check_library` 0 failures |
| 12 | b92-batch-20-filing (`30c16e1c`) | `ce513107` | change-orders: both (see below); the cell: ours, then `--write`; SR-73 to 75 clean | `check_library` 0 failures |
| 13 | b95-batch-21-filing (`c72f4f38`, with B108 and B115) | `a870cf00` | change-orders: both (see below); the cell: ours, then `--write`; SR-76 clean | `check_library` 0 failures |

At every merge:

- the three tools' `--check` agreed;
- `validate_lenses` passed and `check_registry` was OK;
- `yaml_section_check` found no key that moved section.

## What differed from the rehearsal

**Two tips had moved since A105 fetched.**

- **a90: `f8819b62` became `08757f97`, adding A111.**
  - A111 is the first edition's binding sections: `validate_audit_fixes.py`,
    `tests/fixtures/monthly_binding_2026-11-01.json`, `a90-notes.md` and its
    paste.
  - It merged clean beside chain-9's A91 fix.
  - `audit_fixes` reads 171/0 at step 2 and 174/0 after b87, against the
    rehearsal's 158/0 and 161/0. The extra checks are A111's.
- **b95-batch-21-filing: `9aeeee9c` became `c72f4f38`, adding B115.**
  - B115 edits the placement pack, b108's notes and one register line, SR-60's
    status cell.
  - That line merged clean, and the merged register carries B115's text.

**The index line's date is the tool's.** At step 11, `change_orders_index --write`
rewrote Batch 19's index date from 30 Oct to 29 Oct, the date in the order's
filename. The rehearsal tree has the same line.

- At step 11 the rewrite was amended into the merge commit, because
  `docs/change-orders.md` had been left unstaged.
- At steps 12 and 13 the "both lines" rule therefore met two different Batch 19
  lines (ours "29 Oct", theirs "30 Oct"), and at step 13 two Batch 20 lines as
  well.
- Each new order's line was kept once and the stale duplicates were dropped;
  `--write` then set the dates. The table holds one line per order, Batch 18 to
  21, then the weekly-readability order.

**The laptop's LF re-checkout** (the script's step after 0b) was needed in this
worktree: 24 files, re-checked out from the index by name before step 2.

## Counts

All counts are read from the tools, never set by hand:

| Measure | Value | Source |
|---|---|---|
| Code gates | 159: 156 Python (`gate_list --kind code` 155, plus `smoke_test.py`) and 3 shell | `gate_list` |
| Data gates | 8 | `gate_list` |
| CLAUDE.md's counts | 61 of 61 agree | `stitch_counts --check` |
| `validate_gates` | 32/0 | the gate |

None of the twelve branches adds a gate, so the counts are main's, the same as the
rehearsal's through step 13.

## Not done here

Chain-10 is not opened as a PR and is not merged into main. Nothing was run on the
box, and no existing branch was touched.
