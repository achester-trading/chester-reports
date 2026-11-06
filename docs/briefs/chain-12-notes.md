# chain-12: the docs tranche (paste B113, 6 Nov 2026)

**Base.** `origin/main` at `bfd7e149`, chain-11's merge (PR #50); that merge is the
tip, so it is its own ancestor. Branch `chain-12`, new from it. The script is A105's
section 2 (`docs/briefs/a105-merge-week-script.md` on
`origin/a105-merge-week-rehearsal-2`), steps 22 to 25.

**Three merges landed; the fourth (b109) was aborted** on a conflict the script did
not see (below). No PR, no merge into main, no box. The names list was never set.

## The merges

| # | Step | Branch (tip) | Merge | Conflicts and resolution | Gates |
|---|---|---|---|---|---|
| 1 | 22 | b96-doctrine-2-pack-refresh (`d72af3ee`; B96, B104) | `21a07624` | `docs/briefs/doctrine-2-pack-2026-11.md`: **b96's side whole**, as recorded. Checked line by line: of main's 1,085 lines, only the four reading-time lines are missing from b96's, and b96 restates them for its larger pack | must-runs; `check_library` 0/0 |
| 2 | 23 | b100-hygiene (`d2c67e00`; B100, B107, B111, **and B124**) | `cc984a7d` | none. `registry-check.yml` parses | must-runs; `validate_deploy` 155/0, `validate_gates` passed |
| 3 | 24 | b102-readable-editions-register (`822b74db`; B102, B103) | `daeb113e` | the six recorded, resolved as recorded except the Reporting System paper's header (below) | must-runs; `check_library` 0/0, `check_master_guide` passed (1 warning) |
| — | 25 | b109-names-gate (`46da3bb5`; B109, B111 Part 4) | **aborted** | seventeen conflicts: the sixteen recorded plus `tools/validate_alpha.py` | — |

The must-runs at every merge: `stitch_counts`, `change_orders_index` and
`appendix_queue_index` (`--check`, then `--write` where needed), `validate_lenses`
(passed), `check_registry` (OK), `yaml_section_check` on the merge (no key moved
section).

## What differed from the script

- **Step 23 carries B124 too.** b100's tip holds B124's paste and notes, with
  `scripts/check_heartbeat_cron.sh` and `tools/validate_heartbeat_caller.sh`. They
  merged clean. The shell gate reaches the laptop's cap (A105 §4), so it is left
  to CI.
- **Step 24: the Reporting System paper's header.** The script took chain-8's
  Draft 4 header "since B102's side was the unchanged base". On b102's tip it is
  not: B103 (`f6bdc7c3`) appends three sentences to the Status line, recording the
  first reread (1 Nov 2026, Appendix F, no body text changed, next reread at Audit
  #5). The header is Draft 4's, with those three sentences appended to its Status
  line. No body text was edited. Appendix F follows the end list, identical to
  b102's (120 lines).
- **Step 24: `docs/change-orders.md`.** `change_orders_index --check` failed after
  the merge: b102 adds `change-order-readable-editions-2026-11-01.md` without an
  index line. `--write` added it (1 Nov 2026).
- **Step 24: the Master Guide's "Landing next" row.** B102's readable-editions row
  was written for chain-5's three-column table. It is added to chain-8's
  merge-order table in that table's four columns.
- **Step 25: aborted.** `tools/validate_alpha.py` conflicts. The script never saw
  this conflict because it rehearsed step 25 before A106 added b98 and b99 (22b,
  22c, now on main through chain-11). The hunk:
  - base `422ea697`: `f"holds no contracts until <the operator's name> confirms")`;
  - b109: `... until the operator confirms")`;
  - ours: the same "the operator" line (chain-7's D28 sweep), followed by b98's
    group W and B99's changes.

  "Ours" loses nothing of b109's. Under the paste's rule (abort, list, continue)
  it was not resolved. The other sixteen conflicting files were the recorded set:
  `registry-check.yml`, CLAUDE.md, the Makefile, `basis_proxy.yaml`,
  `listing_exchanges.yaml`, `prediction_markets.yaml`,
  `doctrine-2-proposals-st-l.md`, `dated-appendix-queue.md`, Figure 2, the two
  html files, `master-guide.md`, `chat-tasks.yaml`, `tools/figures/master_guide.py`,
  `validate_by_hand_audit.py` and `validate_digital_addendum.py`.

## The gates at the end (three merges)

| Gate | Result |
|---|---|
| `check_master_guide` | 0 failures, 1 warning (the Guide is as of 29 Oct, older than the 1 Nov order; refreshed at the next chain merge) |
| `check_library` | 27 papers, 0 failures, 0 warnings |
| `validate_names` | not on this tree (arrives with b109) |
| `validate_gates` | passed |
| `validate_deploy` | 155 passed, 0 failed |
| `stitch_counts --check` | 62 counts, 0 disagree |

**Counts, by the stitch tools: one hundred and sixty-six code gates (one hundred
and sixty-three Python, three shell) and eight data gates.** Main's count is
unchanged, since no merged branch adds a gate. b109's `validate_names` would make
it 167/164.

## Needs you

**b109's step.** Either:

- **(a)** rule the `validate_alpha.py` hunk "ours" and have a session re-merge b109
  onto chain-12 as recorded; or
- **(b)** merge main into b109 on its own branch after chain-12 lands, taking "ours"
  there, and then open its PR.

B114, the names sweep of the merged main, needs `validate_names`. So whichever you
choose has to land before B114.
