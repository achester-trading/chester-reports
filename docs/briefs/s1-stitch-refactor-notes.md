# S1 — the stitch refactor: session notes

Branch `s1-stitch-refactor`, base `origin/chain-7-main` at `dfa14a54`. One commit
per part; no merge, no PR, no box.

## Parts, their checks and results

| Part | Commit | Output-equivalence check | Result |
|---|---|---|---|
| 1 `tools/stitch_counts.py` | `baa55452` | `--check` against the base, then `--write` | 59 counts agree; `--write` changes nothing |
| 2 `GATE_KIND` in every gate; `tools/gate_list.py` | `74547900` | the gate set before and after | identical, 148 gates (137 Python code, 3 shell, 8 data); CLAUDE.md unchanged |
| 2 follow-up: `gate_list.makefile_text()` | `35f2453d` | the 11 gates that grep the Makefile for their own path | all 11 pass |
| 3 `tools/change_orders_index.py` | `31341c9a` | `--write` on the base | changes nothing |
| 4 the appendix queue split; `tools/appendix_queue_index.py` | `60b56f26` | the regenerated index against the old file | byte for byte except the generated-by line (15,617 bytes) |
| 5 stack hooks; `tools/validate_stack_hooks.py` | `19e5dc94` | `slow_layers()` snapshot before and after | identical (`cmp`); validate_stack_hooks 15/0 |
| 6 `check_master_guide` staleness as warnings, `--strict` on `chain-*` / `*-main` | `819ff32b` | the gate normal and `--strict`, its self-test | 0/0 both; self-test 14/0; check_library 0/0; validate_gates 32/0 |
| 7 `tools/validate_stitch_tools.py`; the recount | `13c7993e` | `stitch_counts.py --write` | the one count change below; validate_stitch_tools 19/0 |

No part changed a rendered byte, so none was reverted.

**Hook files:** 5 under `config/stack_hooks/` (all Monthly, slow, after
`inline:sourced_figures`), plus `_anchors.yaml`.

**Gate count:** before, one hundred and forty code gates (one hundred and
thirty-seven Python, three shell) and eight data gates; after, one hundred and
forty-two code gates (one hundred and thirty-nine Python, three shell) and eight
data gates. The two new gates are validate_stack_hooks and validate_stitch_tools.

**Local runs, one at a time in the foreground** (an earlier background run was
stopped for low memory after two gates; none needed "CI only"): validate_6e_rest
34/0, validate_events 95/0, validate_monthly_stack 267/0,
validate_quarterly_stack 94/0, validate_releases 61/0, validate_releases_b 76/0,
validate_st_t5_prl 62/0, validate_st_t5_render 46/0, validate_stack_cadence
104/0, validate_weekly 101/0 (1 skipped: fixture grades empty),
validate_st_r4_t1b 61/0, validate_st_r4_t1 49/0, validate_batch14_a1 30/0,
validate_batch14_a2 40/0, validate_batch14_b2 57/0; validate_audit_3a 88/0,
validate_deploy 155/0, check_registry OK. `validate_batch15_1` reports one hash
fault that is CRLF-only on this checkout and was there on the base (the committed
blob matches its pinned SHA); CI is Linux.

CI is read once after the push and reported with the run id.

## Needs-you

1. **Gate order is sorted by path**, not the Makefile's old hand order.
   `make validate` and CI run the same set in a different order.
2. **The orders index keeps hand-written summaries.** `change_orders_index.py`
   writes a new order's row from its first heading and leaves every existing
   row's summary as written.
3. **Part 5 is a partial migration.** Only the five append-only Monthly
   slow-layer tail hooks moved. The other inline hooks in the three stacks stay
   inline: their positions are computed and they pass data to each other.
4. **Make's `$(shell tools/gate_list.py ...)` lists are untested locally**:
   there is no `make` on the laptop. `scripts/make.sh` and CI's `make list-code`
   / `list-data` exercise the same tool.
5. **`check_library` check 10 was relaxed** (a file outside the paste's list):
   it now warns rather than fails on the Master Guide's built edition, so it
   agrees with `check_master_guide`; `registry-check.yml` reaches the gate list
   through `make list-code`.

## The stitch checklist (added at the chain-8 assembly, B86b; D42.12, 29 Oct 2026)

After **every** merge at a stitch, including a merge that reports no conflict:

1. Resolve the conflicts by the repo's rules. Additive lines keep both sides.
   A gate added by a branch built before S1 gets `GATE_KIND` in its own file,
   never a Makefile line.
2. Run the tools, `--check` then `--write`:
   - `tools/stitch_counts.py`, the counts;
   - `tools/change_orders_index.py`, the orders index and the register's
     batch-orders cell;
   - `tools/appendix_queue_index.py`, the dated-appendix queue, one file per
     entry.
3. **Must run, whatever the conflicts were:**
   - `tools/validate_lenses.py` and `tools/check_registry.py`;
   - `python tools/yaml_section_check.py <merge>`. It diffs every YAML file both
     parents touched against both parents and lists any key that left a
     top-level section a parent had it in for a section that parent did not
     use.

   **A block that moved section is a stop.** Move it back, then rerun step 3.
4. Run the gates whose files the merge touched, one at a time.

Why step 3 exists: at the chain-8 assembly the b70 merge (`e21a3535`) put b69/b70's
88 `families` lines inside `member_overrides`, with no conflict marker. git
appended them after the wrong anchor once main's `member_overrides` block sat
between the two. The keys lost their family, and only validate_lenses noticed.
`yaml_section_check.py e21a3535` reports those 88 keys; the fix was `068a72aa`.
