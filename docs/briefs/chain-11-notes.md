# chain-11 notes (A109, 5-6 Nov 2026): the build branches

**Base.** `origin/main` at `47238f50`, PR #49's merge of chain-10; chain-10's tip
`3d3e5ee3` is an ancestor. Fetched 22:29 ET on 5 Nov. Paste committed first as
`docs/pastes/A109.md` (`ff3f8337`).

**Order.** As A105 rehearsed steps 14-21 with 17a, plus A106's 22b and 22c. All ten
branches are in, with no merge aborted and no needs-you.

## The merges

| # | Step | Branch (tip) | Merge | Conflicts and resolution | Code / Python gates |
|---|---|---|---|---|---|
| 1 | 14 | a92-dth1-box-pieces (`fb3e9a30`, A92b) | `126d8bc5` | Makefile, CLAUDE.md, `aaii.py`, `catalogue_commands.yaml`, `validate_official_sources.py`, as rehearsed. Both sides of the last three were byte-identical to the rehearsal merge's (`a9758813`) parents, so its resolved files were taken: `weekly_rows(KEYS)`; groups U, V and W; both catalogue entries. GATE_KIND on `validate_dth1.py` | 159/156 → 160/157 |
| 2 | 15 | a93-ibkr-daily-bars (`5b2297ec`) | `469075dc` | Makefile, CLAUDE.md count; GATE_KIND on `validate_ibkr_bars.py` | → 161/158 |
| 3 | 16 | a94-ll6-forecasters (`2cfecbe0`, now with A120) | `9559be7b` | Makefile, CLAUDE.md count; GATE_KIND on `validate_ll6.py` | → 162/159 |
| 4 | 17 + 17a | a96-price-migration-fred (`bddb2979`: A96, A102, A104, A114, A115, and 17a) | `5957391f` | CLAUDE.md count only. The `metrics_registry.yaml` conflict was met and resolved at 17a on a96 | → 163/160 |
| 5 | 18 | a97-weekly-readability (`d30238ed`) | `e73e69f2` | Makefile, CLAUDE.md count; GATE_KIND on `validate_weekly_readability.py` | → 164/161 |
| 6 | 19 | a95-monthly-first-edition (`a2737d15`) | `4e190656` | none | unchanged |
| 7 | 20 | a103-weekly-consistency (`b3a1b9f5`) | `b9dda39e` | none | unchanged |
| 8 | 21 | a98-paper-executor (`73d12a1c`) | `8f956fda` | Makefile; CLAUDE.md's count hunk only (see below); GATE_KIND on `validate_paper_exec.py` | → 165/162 |
| 9 | 22b | b98-ks-family-registry (`dc8eeb12`, now with A113) | `a5014cab` | none | unchanged |
| 10 | 22c | b99-premium-sleeve (`da345be9`) | `0ea0945a` | CLAUDE.md's count hunk; `validate_premium_sleeve` joins by GATE_KIND | → 166/163 |

**Counts** are by `tools/stitch_counts.py --write` at every merge, never by hand.
The final count is **166 code gates (163 Python, 3 shell), 8 data gates**. The
rehearsal's 167 included b109's `validate_names`, which is not in this chain.
`stitch_counts --check` agrees on all 62 counts.

## Step 17a, on a96 (A100's ruling)

Done on `a96-price-migration-fred` itself, from its tip `9722f6ac`, and pushed:
- **`670ac6a7`: merge origin/main (`47238f50`) into a96.** Three conflicts:
  - the Makefile and CLAUDE.md, resolved to main's side (the chain's), then
    GATE_KIND on `validate_price_sources.py` and `stitch_counts --write` (160);
  - `metrics_registry.yaml`, both `bulk_imports` blocks kept, chain-8's
    `trend_breadth_signs` then A102's `edgar_fundamentals`, the rehearsal's order.
  - The laptop's LF re-checkout followed: 110 files.
- **`bddb2979`: fbd43be8's change**, the three dollar-index readers
  (`gold_attribution`, `gold_event`, `trend_breadth` and their configs) moved to
  the resolver. Applied cleanly.
- **Gates on a96:**

  | Gate | Passed/failed |
  |---|---|
  | `validate_price_sources` | **65/0** (A99's N1 is closed) |
  | `validate_gold_attribution` | 41/0 |
  | `validate_trend_breadth` | 42/0 |
  | `validate_weekly_gold_block` | 32/0 |
  | `validate_ai_fcf` | 27/0 |
  | `validate_weekly_calendar` | 44/0 |
  | `validate_quality` | 54/0 |

  `yaml_section_check` on `670ac6a7` touched 6 files and moved no key.

## Resolutions that differed from the script

- **CLAUDE.md at a98 (and b99): the conflict hunk resolved to ours, not the whole
  file.** a98 adds a CLAUDE.md paragraph ("The paper executor is outside the lab,
  paper only, and ships off") that auto-merges outside the count's conflict. A
  whole-file `checkout --ours` would have dropped it. Only the count hunk was taken
  from ours; the paragraph is kept, as in the rehearsal's tree.
- **a92 through a97** changed nothing in CLAUDE.md but the count line (each was
  checked), so whole-file ours lost nothing there.
- **a96's registry conflict moved from the chain merge to 17a**, because a96 now
  carries main. Same resolution, met one merge earlier.

## Gates, one at a time

At every merge:
- the three tools' `--check` (stitch counts, the orders index, the appendix
  queue);
- `yaml_section_check` on the merge (no key moved section at any step);
- `validate_lenses` (49/0);
- `check_registry` (OK).

| After | Gates (passed/failed) |
|---|---|
| a92 | official_sources 381/0, dth1 27/0, backup 89/0, backups 29/0, audit_3a 88/0, gates 32/0 |
| a93 | audit_3a 88/0, ibkr_bars 28/0, quality 48/0, feed_repair 59/0 |
| a94 | deploy 155/0, ll6 22/0, secrets 58/0, audit_3a 88/0, prediction_markets 52/0 (red on a94 alone; A88's pin is on main) |
| a96 | price_sources 65/0, gold_attribution 41/0, trend_breadth 42/0, weekly_gold_block 32/0, ai_fcf 27/0, quality 54/0, audit_3a 88/0 |
| a97 | weekly_readability 56/0, weekly_storyline 31/0, weekly_edits 91/0, system_metrics 21/0, b51_registry_html 25/0 |
| a95 | numeral_audit 181/0, audit_fixes 174/0, monthly 388/0 (1 skip), monthly_frames 48/0, readability 67/0, weekly_edits 91/0, secondary_notes 88/0, benchmark 32/0 |
| a103 | weekly_readability 64/0, weekly 101/0 (1 skip), weekly_calendar 44/0, st_r4_t1 49/0, weekly_opener 46/0, weekly_fixes_8 68/0 |
| a98 | deploy 155/0, paper_exec 70/0, alpha 257/0, alpha_no_orders 74/0, alpha_proposer 44/0, secrets 58/0, audit_3a 88/0 |
| b98 | alpha_lab_4 65/0, alpha_proposer 52/0, check_library 0 failures |
| b99 | premium_sleeve 36/0, alpha 271/0, alpha_lab_3 65/0, alpha_lab_4 65/0, alpha_no_orders 76/0, alpha_proposer 52/0, ll6 22/0, paper_exec 70/0, gates 32/0, audit_3a 88/0, check_library 0 failures |

**At the end, by group** (`bash scripts/make.sh validate-group <gate> <group>`,
one at a time):
- `validate_stack`, 11 groups: A 13, B 8, C 13, D 8, E 12, F 6, G 4, H 2, M 6, I 3,
  V 9. **84 passed, 0 failed.**
- `validate_monthly_stack`, 25 groups: A 9, B 3, C 12, D 13, E 5, F 6, N1 4, N2 8,
  N3 7, N4 11, N5 7, N6 6, N7 3, N8 8, N9 7, N10 10, O 16, P 44, H 14, I 11, J 10,
  K 27, L 20, M 6, G 1. **268 passed, 0 failed.**

## The box steps

None are new. The A-branches' box steps are A105 section 5's, in its order.
They are the operator's, inside the windows.
