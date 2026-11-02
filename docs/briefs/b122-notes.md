# B122 notes: the CI jobs grouped

Paste B122 (`docs/pastes/B122.md`), 2 Nov 2026. Branch `b122-ci-job-grouping`, new,
from origin/main at `422ea697`. It merges in the week after the merge week, once
B111's cache has had its first hit. No gate changed, and none left CI.

## The base, and which hunks will meet

**Why b100 is merged in.** The paste asks for the grouping on top of b100's workflow
shape, and the B107 brief it extends exists only on `b100-hygiene`. So the branch
merged `origin/b100-hygiene` (`72406edd`) after the paste's commit, and its
workflow is b100's with the grouping on top. b100 reaches main first (chain-12,
Wed), so when this branch merges, b100's hunks are already shared ancestry.

**Trial merges, `git merge-tree`, all clean:**
- the whole rehearsed week (`a105-merge-week-rehearsal-2`);
- `b86-chain-8-assembly`;
- `b97-slow-gates`;
- `b109-names-gate`.

Each of these touches the workflow, the Makefile or `validate_gates`, and none of
their hunks meets this branch's. **On the trial-merged tree** (a scratch worktree,
removed):
- `validate_gates` passes 38/0;
- its 163 code gates (from `tools/gate_list.py --kind code`) fall into 20 jobs, with
  1 gate (`validate_b59.py`) in the default group.

**B109's secret line.** It sits in the lone-gate job's run step, keyed on
`matrix.gate`. `validate_names.py` is listed alone, so the line reaches it unchanged
when b109 lands.

## The design

**`config/ci_groups.yaml` places each gate.**
- `alone`: each runs in its own job, as before. These are B107's ten slowest,
  `validate_session_calendar.sh` (its 20-minute allowance) and `validate_names.py`
  (its secret).
- `groups`: eight subsystems, by ordered fnmatch patterns on the file name; the first
  match wins.
- `default`: `other`, for a gate no pattern matches, so a new gate never leaves CI.
- `docs_set`: B111's docs-only three, run as one job named `docs`.

**`tools/ci_groups.py` makes and runs the matrix.** It reads the gate list from
stdin (`make list-code`), so it keeps no list of its own:
- `matrix [--docs]` gives the two JSON lines for `$GITHUB_OUTPUT`;
- `--by-group` prints every job with its gates;
- `run <group>` runs the group's gates one at a time (python, or bash for `.sh`).
  - Each gate's whole output is folded in the log.
  - It prints `PASS|FAIL  <gate>  (<tally>; exit n; s)`, with the tally read from
    the gate's own stdout.
  - It writes a table to the job summary and exits 1 if any gate failed.
  - Each gate keeps a ten-minute limit.

The paste names `tools/gate_list.py --by-group`. That file is not on main (it
arrives with chain-8), so the generator is its own tool, and it reads whatever
`make list-code` prints, before and after the week.

**The workflow.**
- `enumerate` emits `alone` and `groups` as well as `gates` and `data`. It gains a
  setup-python and a PyYAML install, because the runner's own python3 may lack it.
- `gate` runs the lone gates.
- A new `group` job runs the groups, with the same checkout, interpreter and B111
  cache.
- `gates-passed` needs `enumerate`, `gate` and `group`. Each must succeed; the one
  exception is a job skipped because its list was empty (the docs-only push has no
  lone gates).
- B111's docs-only filter and both concurrency groups are unchanged.

## The groups, on main's 135 code gates (19 jobs)

| Job | Gates |
|---|---|
| alone (each its own job) | 11: validate_stack, validate_monthly_stack, validate_prediction_markets, validate_readability, validate_quarterly_stack, validate_weekly_stack, validate_alpha, validate_weekly_complete, validate_alpha_lab_3, validate_quarterly_gates, validate_session_calendar.sh |
| library-and-guide | 8 |
| box-and-deploy | 19 |
| weekly | 12 |
| reports | 13 |
| register-and-books | 22 |
| dealer-and-tape | 15 |
| rates-and-releases | 24 |
| sources-and-quality | 11 |

**Group times, from the green run.** Each gate's job time, less about 28 s of
per-job setup, puts the longest group, weekly, at about 4.9 minutes of gate time.
`validate_stack` alone takes 8.2, so the critical path does not move. The gate time
in all comes to about 53.8 minutes, against B107's measured 52.8.

## The validate_gates case (group E)

- Every code gate is in exactly one job: 135 in 19, none missing, none repeated.
- No job is empty.
- The docs set is three code gates.
- **Must-fail:** a gate in no job and a gate in two jobs are both reported.
- The workflow's matrices come from `ci_groups.py`.
- `gates-passed` needs both code jobs, and checks `needs.group.result`.

`validate_gates`: 38/0.

## The computed saving

The figures are B107's per-step totals; the assumptions are stated in the brief's
Part 5.

| Code jobs | Jobs | Job-minutes | Wall at 3.8 at once | Wall, idle pool |
|---|---|---|---|---|
| Measured (B107) | 165 | 121.0 | about 32 | about 9 |
| B111's cache only | 165 | about 81 | about 21 | about 9 |
| Cache and groups | about 20 | about 56 | about 15 | about 9 |

## Proof, local

- **YAML:** the workflow and `config/ci_groups.yaml` parse (`yaml.safe_load`;
  actionlint is not installed).
- **`--by-group`** prints every gate once: 135 on main, 163 on the merged tree.
- **One fast group's run,** through the job's own command:
  ```
  PASS  tools/check_registry.py  (OK -- every emitted field is declared, every metric names a known source,; exit 0; 1 s)
  PASS  tools/validate_numeral_audit.py  (172 passed, 0 failed; exit 0; 1 s)
  PASS  tools/validate_horizon_charts.py  (73 passed, 0 failed; exit 0; 20 s)
  PASS  tools/validate_figure_budget.py  (123 passed, 0 failed; exit 0; 19 s)
  PASS  tools/validate_library_st_l.py  (17 passed, 0 failed; exit 0; 0 s)
  PASS  tools/validate_b51_registry_html.py  (25 passed, 0 failed; exit 0; 5 s)
  PASS  tools/check_library.py  (27 papers checked -- 0 failures, 0 warnings; exit 0; 1 s)
  PASS  tools/check_master_guide.py  (12 passed, 0 failed; exit 0; 0 s)
  group library-and-guide: 8 of 8 gates passed
  ```
- **A gate that cannot run:** `FAIL  tools/validate_no_such_gate.py ...; exit 2`, and
  the group exits 1.
- **The docs matrix:** `alone=[]`, `groups=["docs"]`, and its three gates pass.
- **Other gates:** validate_deploy PASSED, check_registry OK.

## CI

This push's run is the grouped workflow's first proof, read once; the run id and its
state are in the report. B111's cache is branch-scoped, so this branch's first run
installs once per job.
