# B100 notes: make.sh in a worktree; one CI run per branch

Paste B100 (`docs/pastes/B100.md`), 1 Nov 2026. Branch `b100-hygiene`, base
origin/main at `422ea697`. It merges with the small fixes next week.

## Part 1: scripts/make.sh's interpreter

**The order.** `resolve_py`:
1. `$PYTHON`, when set;
2. `.venv` in this tree: `.venv/bin/python`, then `.venv/Scripts/python.exe`;
3. `.venv` in the main checkout. That is the parent of
   `git rev-parse --git-common-dir`, for a worktree with none of its own;
4. otherwise it stops with exit 2 and says what it looked for. There is no
   fallback to a bare `python`: a system Python lacks PyYAML and pandas, and A99
   met exactly that from a worktree.

`list` and `validate-fast` print the interpreter and which rule chose it.

**As printed (1 Nov 2026):**

| Where | `interpreter:` line |
|---|---|
| A fresh worktree (`git worktree add`, no `.venv`, Makefile checked out CRLF) | `/c/Users/arich/projects/chester-reports/.venv/Scripts/python.exe  (the main checkout's .venv (/c/Users/arich/projects/chester-reports))` |
| The same worktree, `validate-fast` | the same line, then `== tools/check_registry.py`, `== tools/validate_register.py` ... on that interpreter |
| A tree with its own `.venv` (this session's checkout) | `.venv/Scripts/python.exe  (this tree's .venv)` |
| A tree shaped like the box (`.venv/bin/python` in the checkout) | `.venv/bin/python  (this tree's .venv)` |
| `PYTHON=/usr/bin/false` | `/usr/bin/false  ($PYTHON)` |
| A repository with no `.venv` anywhere | `scripts/make.sh: no interpreter with the repo's dependencies.` with what it looked for, exit 2 |

- **The main checkout and the box are unchanged.** Each has its own `.venv`, so
  rule 2 picks the path the old rule picked: `.venv/bin/python` on the box,
  `.venv/Scripts/python.exe` on the laptop. Only the old last branch, a bare
  `python`, is gone.
- **Line endings.** `list` from the fresh worktree printed 147 lines with 0
  carriage-return bytes. Main's `mk_list` already strips `\r` from the Makefile
  lists (`tr -d '\r'`), and that is kept.
- **For the stitch with chain-8.** On `b86-chain-8-assembly`, S1's
  `gate_list()` reads `tr -d ''`, which deletes nothing. Its `\r` was lost,
  which is probably the stray line endings A99 saw. When this branch meets
  chain-8's `make.sh`, keep `resolve_py` and make that line `tr -d '\r'`.

## Part 2: the workflow's concurrency block

Added to `.github/workflows/registry-check.yml` between `on:` and `jobs:`.
Nothing else in the workflow changes. Verbatim:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref == 'refs/heads/main' && format('main-{0}', github.run_id) || github.ref }}
  cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}
```

- **Branches.** A branch's runs share one group (the workflow and the ref), so
  a new push cancels that branch's older queued or running run. A pull request's
  ref is its own (`refs/pull/N/merge`).
- **main never cancels.** Each push to main is its own group, keyed by its run
  id, and `cancel-in-progress` is false there. A single shared main group would
  not have been enough: GitHub cancels a pending run in a group when a newer one
  queues, so a third push would cancel the second's waiting run.
- **No gate expectation changes.** No gate pins the workflow's content or hash.
  `tools/validate_gates.py` reads its matrix (group D) and
  `tools/validate_deploy.py` refuses a `-latest` runner; both pass unchanged.

## Gates (one at a time, foreground)

| Gate | Tally |
|---|---|
| validate_deploy | 154 passed, 0 failed |
| validate_gates | 32 passed, 0 failed |
| check_registry | OK |
