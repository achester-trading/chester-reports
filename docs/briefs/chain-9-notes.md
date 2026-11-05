# chain-9 notes (A107, 3 Nov 2026)

**Base.** `origin/main` at `422ea697`, fetched 06:20 ET on 3 Nov. Paste committed
first as `docs/pastes/A107.md` (`b09779f9`).

**Tip pushed:** steps 1-3 and these notes. **Step 4 (b97) is held as a needs-you**
(below).

## The merges

| Step | What | Commit | Conflicts |
|---|---|---|---|
| 1 | A91's `tools/validate_audit_fixes.py` change from `f8819b62`, alone (`git show f8819b62 -- tools/validate_audit_fixes.py \| git apply --3way`) | `34fdf647` | none; applied cleanly |
| 2 | merge `origin/b85-gitattributes-lf` (`5cb338fa`) | `f3249856` | none |
| 3 | merge `origin/b101-date-drift-gates` at `9de522f8` (B101, B101b, B106, A110's three pins, B126's notes) | `73e7f5ff` | none (30 files) |
| 4 | merge `origin/b97-slow-gates` (`267bd42b`) | **not pushed** | see the needs-you |

**After step 2, the laptop's LF re-checkout** (A105's section 2 step): 110 files
were CRLF on disk under an `eol=lf` attribute. They were re-checked out from the
index by name; afterwards there were none, and `git status` was clean. CI and the
box check out fresh.

## Needs you: b97 is built on chain-8, not main

`b97-slow-gates` was cut from `origin/b86-chain-8-assembly` at `4e6814df`
(B97's paste says so). Main does not hold chain-8, so a merge of b97 into chain-9
carries **210 commits and 477 files**: all of chain-7 and chain-8.

**Why the rehearsal did not show it.** A105's and A106's rehearsal tree was based
on b86, with chain-7 and chain-8 "in the base" (step 1). There, b97 was a 11-file
change and merged clean. A106's note that "at step 0 it meets fewer changes"
holds only on that base.

**B97 alone does not stand on main either.** Its own diff (`4e6814df..267bd42b`,
11 files) was tried with `git apply --3way --check` on chain-9:
- `tools/gate_list.py`, which B97 extends with `--groups`, does not exist on
  main. It is S1's (chain-8).
- The five gates it splits (`validate_stack`, `validate_monthly_stack`, and the
  three Weekly gates) conflict, because chain-8 changed them first.

The merge was made locally, inspected, and reset before any push. chain-9 holds
steps 1-3 only.

**Options for the operator:**
- (a) **Merge b97 after chain-8 lands on main**, as its own small PR. On a main
  that holds b86, b97's diff is the rehearsed 11 files.
- (b) **Merge b97 into chain-9 anyway.** chain-9 then *is* chain-8 plus step 0,
  and is not the small PR the plan intends.

Recommendation: (a). The slow gates' `--group` flag is a laptop convenience, and
CI runs every gate whole either way.

## The stitch checklist's must-runs, and the tools that are not on main

- `validate_lenses`: passed.
- `check_registry`: OK.
- `yaml_section_check` against both parents: run on `f3249856` and `73e7f5ff`, both
  "0 YAML files both sides touched; no key moved section". It was run from b86's
  copy in the session's scratch: the tool is S1's (chain-8) and not on main.
- `stitch_counts.py` is S1's too and not on main. No merge added a gate or
  touched CLAUDE.md's counts, and nothing conflicted, so there was nothing to
  write. `validate_audit_3a` (88/0), which holds the counts CLAUDE.md prints
  against the code, passes: **135 code gates (132 Python, 3 shell), 8 data
  gates**, unchanged from main.

## Gates, one at a time, on `73e7f5ff`

| Gate | Result |
|---|---|
| `validate_audit_fixes` | 136 passed, 0 failed (also 136/0 after step 1 alone; main's red since #46 is fixed) |
| `validate_monthly` | passed (one laptop skip: no bash+flock) |
| `validate_voices` | passed |
| `validate_st_t5_render` | 46 passed, 0 failed |
| `validate_alpha_proposer` | passed |
| `validate_batch15_1` | **not on this tree**: a chain-8 gate |
| `validate_stack --group` | **not run**: the flag is B97's, held above |

The other gates b101's merge touched, also one at a time:

| Gate | Passed/failed |
|---|---|
| `validate_thesis_register` | 66/0 |
| `validate_em_scorecard` | 63/0 |
| `validate_sr38_inbox` | 53/0 |
| `validate_a43_render` | 46/0 |
| `validate_alpha` | 257/0 |
| `validate_audit_1` | 48/0 |
| `validate_benchmark` | 32/0 |
| `validate_book_b_scanner` | 63/0 (run with UTF-8 console output; the cp1252 console cannot print its "≤") |
| `validate_claims` | 18/0 |
| `validate_dealer_vendor` | 28/0 |
| `validate_events` | 95/0 |
| `validate_morning_anchor` | 71/0 |
| `validate_narratives` | 103/0 |
| `validate_official_sources` | 340/0 |
| `validate_register` | 180/0, 2 skipped |
| `validate_security_master` | 102/0 |
| `validate_structure_compare` | 12/0, 1 skipped |
| `validate_audit_3a` | 88/0 |
| `validate_gates` | 32/0 |

`validate_stack` itself, which b101 also pinned, was not run whole: without
B97's fix it runs past the laptop's ten minutes. CI runs it.
