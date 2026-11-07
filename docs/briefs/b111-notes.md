# B111 notes: B107's set built, make.sh's CR, the names gate's ruled exclusions

Paste B111 (`docs/pastes/B111.md`), 2 Nov 2026. Branch `b100-hygiene`, continued
from `origin/b100-hygiene` at `12d7f940` (B100 and B107). Part 4 is on
`b109-names-gate` and is recorded in that branch's `docs/briefs/b109-notes.md`.

## Part 1: the cache (ruling (b))

**What changed.** `.github/workflows/registry-check.yml`, in the gate job and the
data-gate job:
- `actions/cache@v4` restores the interpreter's whole tree (`env.pythonLocation`,
  site-packages included) after setup-python;
- **the key** is `gates-pkgs-<runner OS>-py<exact Python version>-<hashFiles('requirements.txt')>`.
  The repo has no lock file, so requirements.txt is the input. A new patch release
  of Python or any change to requirements.txt is a new key;
- `pip install -r requirements.txt` stays, as the miss path (`if: cache-hit != 'true'`).

`cache: pip` stays too. It keeps pip's downloads, which makes a miss cheaper; it
never skipped the install.

**What it will cost.**

| Run | Cost |
|---|---|
| **The first run after the change (the miss)** | As today for the jobs that start before the first save lands, plus a one-off save of the tree in each. Those are the first wave, about four to eight jobs at the run's parallelism (about 3.8, B107). Jobs that start after the save restore it, so most of the first run already hits. |
| **The second run (a hit)** | Each job restores instead of installing. The install's 20 s median becomes the restore time, expected at a few seconds. Set against B107's 53.2 job-minutes of install, that is about 40 to 45 job-minutes a run. The restore time is measured in the first hit's log, not assumed. |

**Branch scope.** GitHub caches are scoped by branch: a branch reads its own cache
and the default branch's. Until this merges, each branch's first run misses once.
After it reaches main, a branch's first run restores main's cache.

## Part 2: the docs-only filter (ruling (c)) and main's group (ruling (d))

**How the filter is expressed: one workflow; the first job decides.** `paths-ignore`
cannot express "only these paths", and it can only drop the whole workflow, never
narrow it. Two workflows would mean two required checks, and branch protection
points at one (`gates-passed`). So the enumerate job:
1. reads the push's changed files, `git diff --name-only <before> <after>`, after a
   depth-1 fetch of the old tip;
2. **all under `docs/briefs/` or `docs/pastes/`:** the code matrix is narrowed to
   the docs set, and the data matrix is `[]`, so the data-gate job is skipped;
3. **otherwise:** the full lists, as before.

**The docs set** is check_library, check_registry and check_master_guide. It is
taken from `make list-code` by exact name, so it cannot name a gate the Makefile
lacks.

**When the full set runs:**
- every pull request and every manual run;
- any push that touches a file outside those two folders;
- a push whose changed set cannot be read: a new branch (old tip all zeros), a
  force-push whose old tip is gone, or an empty diff.

**Checked locally on four change sets:**

| Change set | Scope |
|---|---|
| briefs and pastes | docs |
| briefs and a tool | full |
| empty | full |
| a whitepaper | full |

**Main's group.** B100's group gave each main push its own group (its run id). Now
every ref, main included, has one group per workflow and ref, and
`cancel-in-progress` stays false for main. GitHub keeps one running and one
pending run per group, and a new pending run replaces the older pending one. On
main, then:
- the run in progress always completes;
- of the runs queued behind it, only the newest is kept.

Branches keep B100's cancel-in-progress.

**The script's note.** `docs/briefs/a105-merge-week-script.md` is not on this base
(it is on `a105-merge-week-rehearsal-2`), so the line is recorded here for the sheet:

> **CI on main (B111(d)):** a merge's own run can be cancelled while pending by a
> later merge. Read the newest completed run for the merge commit (`gh run list
> --branch main --commit <sha> --status completed --limit 1`), not the run listed
> first. If the merge commit has no completed run because a later merge's run
> superseded it, the later run's verdict covers it.

## Part 3: `scripts/make.sh` (ruling (e))

**The cause.** On chain-8, b97 and A105's merged tree, `make.sh` reads its list as:

`gate_list() { "$PY" tools/gate_list.py --kind "$1" | tr -d ''; }`

The `''` is empty. The `\r` it held, probably a literal CR, did not survive the
`*.sh text eol=lf` normalisation, so nothing was stripped. That line is not on this
base: b100's `make.sh` still parses the Makefile, already through `tr -d '\r'`.

**The fix** goes where every version agrees. `run_gate` is byte-identical on b100,
chain-8, b97 and A105's tree.

- Before:

  ```
  run_gate() {
      case "$1" in
  ```

- After:

  ```
  IFS=$' \t\n\r'

  run_gate() {
      set -- "${1//$'\r'/}"
      case "$1" in
  ```

A CR is now a word separator in every list loop, so the printed names are clean,
and `run_gate` strips any CR left on a path. What runs is unchanged.

**Checks.**
- `bash -n scripts/make.sh`: OK.
- **On this branch, with a 60 s cap:**
  ```
  tools/check_registry.py                     PASS
  tools/validate_register.py                  PASS
  tools/validate_packets.py                   PASS
  ```
- **On A105's tree, in a throwaway worktree (since removed).** Before the fix,
  every path carried `^M`:
  ```
  tools/check_library.py^M                     FAIL
      | ...python.exe: can't open file '...check_library.py\r'
  ```
  This `make.sh` was then merged into it with `git merge-file`, cleanly, and run with
  a 60 s cap:
  ```
  tools/check_library.py                      PASS
  tools/check_master_guide.py                 PASS
  tools/check_registry.py                     PASS
  tools/validate_6e_rest.py                   PASS
  ```

**Merges.** `git merge-tree` of this branch against `b109-names-gate`,
`b97-slow-gates` and `b86-chain-8-assembly` gives no conflict in the workflow or
`make.sh`.

## Gates (one at a time)

| Gate | Tally |
|---|---|
| The workflows (actionlint and yamllint not installed: `yaml.safe_load`) | both parse; registry-check's jobs are enumerate, gate, data-gate, gates-passed |
| validate_gates (reads the workflow: group D) | 32/0 |
| bash -n scripts/make.sh | OK |
| check_registry | OK |
| validate_deploy | PASSED |
