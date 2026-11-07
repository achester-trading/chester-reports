# B97 notes: the slow gates, runnable on the laptop

Paste B97 (`docs/pastes/B97.md`), 31 Oct 2026. Branch `b97-slow-gates`, base
origin/b86-chain-8-assembly at `4e6814df`. Merges after chain-8.

**The laptop recipe: run the group you touched, then push; CI runs the whole.**

    bash scripts/make.sh validate-group validate_stack            # list the groups
    bash scripts/make.sh validate-group validate_stack E          # run one
    python tools/validate_monthly_stack.py --group K,L            # or directly

## What changed

- **Groups.** Each of the five gates declares `GATE_GROUPS` and takes
  `--group <name>` (repeatable, or comma-separated) and `--list-groups`.
  - With no flag every group runs in the order it always did.
  - A selected group runs its own setup. Setup every group reads (the seeded
    store, the shared edition) runs once whatever is selected.
  - A header's timing line reads `  time  E at 10.5 s; D took 0.0 s`. It is new
    output and never starts with PASS or FAIL.
  - The tally lines and the exit code keep their form.
  - The helper is `tools/gate_groups.py`.
- **The runner's one field.** `tools/gate_list.py --groups <gate>` reads a
  gate's `GATE_GROUPS` as text, as it reads `GATE_KIND`.
  `scripts/make.sh validate-group <gate> [<group>]` checks the name against it.
  The target lists the groups when no group is given, and refuses an unknown
  group or a gate with none.
- **CI is unchanged.** The workflow and `make validate` run each gate whole, with
  no flag.
- **Group-mode setup hoisted.** Five reads that one group made and a later group
  also used were moved out of their group's guard, so a later group can run
  alone. Each is a pure read, so the values and the checks are the same:
  - `observations` in validate_stack (H, read by I);
  - `observations`, `inspect` and `tsubs` in validate_weekly_complete (B, read by
    C, H2 and J);
  - `vol` in validate_weekly_complete (D, read by J);
  - `cfg` in validate_weekly_storyline (D, read by F).

  Two group dependencies are declared instead:
  - validate_stack's E builds the thin store that G and H read, so it runs for
    `--group G` and `--group H` too, without E's checks.
  - validate_weekly_stack's G runs on through the T2.1 header, because T2.1
    reads the stores G writes. T2.1 is part of group G (`G: T2.1`).
- **The diff.** Read it with `git diff -w`: each guarded block is re-indented and
  otherwise unchanged. The diff shows the declaration, the flag, the guards,
  the marks, the five hoisted lines, the stack gate's fake clock and the cache
  install.

## The groups per gate

| Gate | Groups |
|---|---|
| validate_stack | A B C D E F G H M I V |
| validate_monthly_stack | A B C D E F N1 N2 N3 N4 N5 N6 N7 N8 N9 N10 O P H I J K L M G |
| validate_weekly_stack | A B C D E F G (with T2.1) H V |
| validate_weekly_complete | WF7 (M1 to M14) A B C D E F G H H2 I J K L N M |
| validate_weekly_storyline | A B C D E F G H |

## Timings on the laptop (12 cores; one gate at a time, foreground; limit 590 s)

| Gate | Before (base) | Slowest three before | Peak memory before | After (branch) | Slowest three after | Peak after |
|---|---|---|---|---|---|---|
| validate_stack | **stopped at 590 s** in E (setup 28 s) | E 351 s+, A 121 s, C 89 s | not reported (killed) | **20.7 s** | A 6.5 s, E 4.2 s, C 3.4 s | 169 MB |
| validate_monthly_stack | **stopped at 590 s** in M (setup 82 s) | K 152 s, C 151 s, L 74 s (P 74 s) | not reported (killed) | **54.4 s** | K 18.1 s, C 13.0 s, L 6.3 s | 248 MB |
| validate_weekly_stack | 141.3 s | A 72.9 s, V 3.9 s, G 3.2 s (setup 58 s) | 156 MB | 141.5 s | A 71.8 s, V 3.7 s, G 3.0 s | 157 MB |
| validate_weekly_complete | 125.7 s | A 66.0 s, G 49.2 s, L 3.6 s | 151 MB | 141.6 s | A 84.3 s, G 48.2 s, L 2.2 s | 154 MB |
| validate_weekly_storyline | 65.8 s | H 4.3 s, A 2.0 s (setup 59 s) | 155 MB | 68.2 s | H 4.2 s, A 1.8 s | 163 MB |

- **The Weekly gates finish inside the limit when run alone.** They were stopped
  this week when run beside other gates or under memory pressure. They gain the
  flag and the timing line only; no fix was asked for them.
- **The Weekly gates' setup is about 60 s.** It builds the shared edition once,
  so a Weekly group alone takes about 60–70 s. Their A groups carry it: the
  timing line falls after the shared produce.
- **Peak memory** is the gate process's peak working set, read in-process at
  exit. A gate stopped by the limit reports none.

## The two fixes

1. **validate_stack E: a real five-minute sleep.**
   - **Cause.** The first `bars.pull` in E (the feed stores the bars with the
     three clocks) passed a fixture fetcher but no clock. The full-session
     instruments (ES, 23 hours) never receive their final bar from the fixture,
     so the pull's retry loop slept in real time, 30 s at a time, until its
     300 s window ran out.
   - **Fix.** That pull now takes the same fake `Clock()` the next two pulls in
     E already used. The loop runs the same attempts, and the gate asserts the
     same things about SPY.
   - **Timing.** E took 351 s or more on the base and was stopped. With the
     fake clock alone it takes 77.9 s, and with the cache as well 4.2 s.
2. **validate_monthly_stack K, C and L: the configuration parsed every build.**
   - **Cause.** cProfile of one Monthly build: 20.5 s, of which 19.9 s is
     `yaml.safe_load`. That is 136 calls per build in pure-Python PyYAML, over
     the same unchanged config files. K and C each build two editions and L
     builds one.
   - **Fix.** `tools/gate_yaml_cache.py`, installed by the two long gates only.
     It parses each distinct text once per gate process:
     - it is keyed on the text itself, so a changed file is parsed again;
     - every hit is a deep copy, so a caller's mutation stays its own;
     - a refused text is never cached.
     No report path imports it. This is the "cache a fixture across checks"
     the paste names, for the parse of the config.
   - **Timing.** K took 152.1 s on the base, about 158 s on the branch with the
     cache off, and 18.1 s with it on. The whole gate went from stopped at
     590 s to 54.4 s.

No check was dropped or skipped, and no tolerance was widened.

## Whole runs: base against branch

The base was run on the laptop for the three Weekly gates. The base's two long
gates cannot finish on the laptop: they were stopped at 590 s above. A
background whole run of them was stopped by Claude Code for low system memory
and not restarted. Their base is therefore chain-8's own CI run at `4e6814df`,
run 40987618896: jobs 123847085560 (validate_stack) and 123847085361
(validate_monthly_stack). The comparison is line by line over every PASS/FAIL
line, with paths and timestamps normalised.

| Gate | Base | Branch | Check lines |
|---|---|---|---|
| validate_stack | 84 passed, 0 failed (CI) | 84 passed, 0 failed | same 84, in order; only the C1-C3 PNG byte counts (Linux fonts against Windows) and the run's date differ |
| validate_monthly_stack | 268 passed, 0 failed (CI) | 268 passed, 0 failed | same 268, in order; only the largest PNG's byte count differs |
| validate_weekly_stack | 83 passed, 0 failed (laptop) | 83 passed, 0 failed | identical, in order |
| validate_weekly_complete | 96 passed, 0 failed (laptop) | 96 passed, 0 failed | identical, in order |
| validate_weekly_storyline | 31 passed, 0 failed (laptop) | 31 passed, 0 failed | identical, in order |

**Every group alone passes, and the group tallies sum to the whole:**
- validate_stack: 11 groups, 84;
- validate_monthly_stack: 25 groups, 268;
- validate_weekly_stack: 9 groups, 83;
- validate_weekly_complete: 16 groups, 96;
- validate_weekly_storyline: 8 groups, 31.

**Gates touched by the runner's field:** validate_gates 32 passed, 0 failed;
validate_deploy 155 passed, 0 failed; validate_audit_3a 88 passed, 0 failed;
check_library 27 papers, 0 failures.
