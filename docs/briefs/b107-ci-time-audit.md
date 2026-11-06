# B107: the CI time audit (2 Nov 2026)

Paste B107 (`docs/pastes/B107.md`). Branch `b100-hygiene`, base `ac04309a`. This brief
is read-only against GitHub: `gh api` on `actions/runs` and `actions/runs/<id>/jobs`,
paginated, with the jobs' step times. Nothing was cancelled or re-run. Only job names
and times are copied, never job output. The workflow is not edited here; every option
below is a draft for the operator.

## Part 1: the measurement

### The runs read

| Run | Branch | Created (UTC) | Jobs | Conclusion | Queue to first job | Queue to first gate job | Wall (created to last job done) | Job-minutes |
|---|---|---|---|---|---|---|---|---|
| 41230301952 | a99-merge-week-rehearsal (green) | 2026-10-31 18:37 | 175 | success | 6.1 min | 13.6 min | 41.5 min | 134.5 |
| 40933353930 | main | 2026-10-29 18:42 | 145 | failure | 1.5 min | 14.1 min | 55.5 min | 116.7 |
| 41379176410 | b101-date-drift-gates | 2026-11-02 02:42 | 145 | failure | 0.1 min | 0.2 min | 10.6 min | 120.0 |
| 41381321307 | b102-readable-editions-register | 2026-11-02 03:07 | 145 | failure | 1.2 min | 1.4 min | 19.7 min | 118.1 |
| 41313799430 | a96-price-migration-fred | 2026-11-01 13:58 | 146 | failure | 0.1 min | 0.2 min | 10.3 min | 118.9 |
| 40987618896 | b86-chain-8-assembly | 2026-10-30 01:44 | 169 | failure | 16.1 min | 55.7 min | 74.0 min | 138.7 |

Every failure above includes the known `validate_audit_fixes` case. The b101 and b102
runs also fail `validate_alpha_proposer` (a calendar failure, which B106 pins). b102
and a96 also fail the three date-drift gates that B101 and B101b pinned.

### The ten slowest jobs, by median over the six runs

| Job | Median | Min | Max |
|---|---|---|---|
| tools/validate_stack.py | 532.5 s | 449 s | 581 s |
| tools/validate_monthly_stack.py | 494.5 s | 282 s | 513 s |
| tools/validate_prediction_markets.py | 268.5 s | 247 s | 276 s |
| tools/validate_readability.py | 192.5 s | 112 s | 206 s |
| tools/validate_quarterly_stack.py | 192.0 s | 158 s | 229 s |
| tools/validate_weekly_stack.py | 145.5 s | 112 s | 153 s |
| tools/validate_alpha.py | 126.5 s | 77 s | 136 s |
| tools/validate_weekly_complete.py | 125.0 s | 84 s | 135 s |
| tools/validate_alpha_lab_3.py | 106.5 s | 78 s | 129 s |
| tools/validate_quarterly_gates.py | 105.0 s | 63 s | 111 s |

- **Their share:** these ten take **27.7%** of the job-minutes, out of a median sum of
  137.8 job-minutes a run. The rest is spread over about 140 short jobs.
- **The most variable jobs** (range across the six runs):

  | Job | Range | Min | Max |
  |---|---|---|---|
  | validate_monthly_stack | 231 s | 282 s | 513 s |
  | validate_stack | 132 s | 449 s | 581 s |
  | validate_readability | 94 s | 112 s | 206 s |
  | validate_quarterly_stack | 71 s | 158 s | 229 s |
  | validate_alpha | 59 s | 77 s | 136 s |
  | validate_heartbeat_caller.sh | 57 s | 65 s | 122 s |
  | validate_alpha_lab_3 | 51 s | 78 s | 129 s |
  | validate_weekly_complete | 51 s | 84 s | 135 s |
  | validate_es_block | 50 s | 58 s | 108 s |
  | validate_quarterly_gates | 48 s | 63 s | 111 s |

### Where a job's minutes go (the green run's steps, 165 gate jobs)

| Step | Median per job | Total |
|---|---|---|
| Install dependencies (`pip install -r requirements.txt`) | 20.0 s | **53.2 job-min** |
| The gate itself | 3.0 s | 52.8 job-min |
| Set up Python | 2.0 s | 7.0 job-min |
| Check out repo | 2.0 s | 6.0 job-min |
| Set up job | 1.0 s | 2.0 job-min |

- **The install costs as much as the gates.** It takes 40% of the green run's 134.5
  job-minutes, as much as all the gates together.
- **150 of the 175 jobs finish in under a minute.** The median of the fastest twenty
  is **24 s**, almost all of it the fixed per-job cost.

### Wall time against job-minutes; queue time

- **Parallelism.** The green run spent 134.5 job-minutes in 41.5 minutes of wall
  time, 35.3 of them after its first job started. That is a parallelism of
  **3.8 jobs at once** while it ran.
- **The 10-minute runs.** b101's and a96's runs (about 120 job-minutes each) took 10
  to 11 minutes of wall time. They started at once, on an otherwise idle evening, so
  their parallelism was about 11.
- **The difference is queue, not the gates.** On the busy evenings of 29–31 Oct:
  - main's run waited 14.1 minutes for its first gate job;
  - chain-8's waited 55.7 minutes;
  - the green rehearsal waited 13.6 minutes.

  A run's own critical path is bounded by `validate_stack` (about 9 minutes). The
  rest of the wall is other runs' jobs ahead of it in the account's pool.

## Part 2: what the workflow does now (`.github/workflows/registry-check.yml` on `b100-hygiene`)

- **One job per gate.** `enumerate` reads `make list-code` and `make list-data`, and
  the `gate` job is a matrix over every code gate (`matrix: gate: ${{
  fromJson(needs.enumerate.outputs.gates) }}`, line 89 on). There are no groups.
  Data gates are a second matrix that skips under Actions, and `gates-passed` is
  the one required check.
- **Caching.** `actions/setup-python@v6` with `cache: pip` (lines 102 and 150). That
  caches pip's downloads, not an installed environment. Each job still runs
  `python -m pip install --upgrade pip` and `pip install -r requirements.txt`
  (lines 110–111 and 152–153), which is the 20 s median above. No venv or data
  fixture is cached.
- **When it runs.** Every push to every branch (`push: branches: ['**']`, line 28),
  every pull request and `workflow_dispatch`. There is no path filter and no
  schedule. `monthly-report.yml` is `workflow_dispatch` only.
- **Concurrency** (B100, lines 38–40):
  ```
  concurrency:
    group: ${{ github.workflow }}-${{ github.ref == 'refs/heads/main' && format('main-{0}', github.run_id) || github.ref }}
    cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}
  ```
  A branch's superseded runs are cancelled. main is excluded: each push to main is a
  group of its own and always completes.
- **Timeouts.** 10 minutes a job; 20 for `validate_session_calendar.sh` (line 85).
- **The slow gates run whole.** The matrix runs `python <gate>` with no arguments,
  and the Makefile names no `--group`. B97's `--group` flags and its two fixes (the
  fake clock in `validate_stack`'s group E, the YAML cache in
  `validate_monthly_stack`) are on `b97-slow-gates`, not yet on main or on this
  branch. On the laptop they took the two gates from past 590 s to 20.7 s and
  54.4 s.

## Part 3: the options (drafts; the workflow is not edited)

Savings are per run, from Part 1. Wall savings assume the green run's parallelism of
3.8 unless stated.

| Option | Saving, job-min | Saving, wall | Risk | Recommendation |
|---|---|---|---|---|
| (a) **Cache the installed environment** (`actions/cache` on the venv or site-packages, keyed on the hash of `requirements.txt` and the Python version; `cache: pip` stays) | About 45 of 134.5. The install drops from a 20 s median to a restore of a few seconds, in about 165 jobs | About 12 min on a busy pool; about 1–2 min on an idle one | Low. A changed `requirements.txt` changes the key. An unpinned transitive upgrade waits for the key to change, which is today's behaviour inside a week anyway | **Monday** |
| (b) **Group the small gates into a few jobs** (for example, the 140 gates under a minute in about ten jobs, each running its list with `make validate`'s keep-going loop) | About 56 at today's 24 s floor (140 × 24 s); about 16 after (a) | About 4 min after (a) | Medium. The per-gate check names in the UI go, and a reader must open the job log to see which gate failed. The keep-going loop must stay so one failure hides none (the workflow's own header). Isolation is kept, since each gate is its own process | **Later (Doctrine #2 or Audit #5),** after (a) shows what remains |
| (c) **The slowest gates on main and nightly only** (`validate_stack`, `validate_monthly_stack`, `validate_prediction_markets`, `validate_readability`, `validate_quarterly_stack`, `validate_weekly_stack`), the rest on every push | About 30 per branch push (their medians sum to about 1,825 s) | The critical path falls from about 9 to about 2–3 min on an idle pool | **High.** A branch would not know before its PR whether it broke the stacked reports, the prediction-market lines or the readability budgets: the four reports themselves | **Not recommended.** Merging B97 does most of this without losing coverage (see (f)) |
| (d) **A path filter for docs-only pushes** | About 118 per docs-only push (145 jobs down to about 4) | The whole run, about 10–55 min | Medium as asked. Several code gates read docs: `validate_audit_3a` (CLAUDE.md's counts), `validate_alt_asset_scan` (`docs/scheduled-tasks.md`), `validate_official_sources` (the register), `check_library` and `check_master_guide` (the papers, the Guide). A filter on `docs/**` or `*.md` would let a docs push break them unseen. Low if narrowed to `docs/briefs/**` and `docs/pastes/**`, which no code gate reads | **Monday, narrowed:** a push touching only `docs/briefs/**` and `docs/pastes/**` runs check_library, check_registry and check_master_guide |
| (e) **Cancel superseded runs on main during the merge week** | Up to about 120 per superseded push. Of twenty-odd pushes in two days, most would be superseded | Large. The queue is what the merge week waits on | Medium. A red introduced mid-sequence is seen only at the last run, so bisecting needs a re-run. A99's script reads CI once per merge and would see `cancelled` for every superseded run: it must read the newest run on main and treat `cancelled` as "superseded" | **Monday, the gentle form:** one main group with `cancel-in-progress: false`, so a running run completes and only the newest pending run is kept (GitHub cancels older pending runs in a group). A99's script reads the newest completed run after the last merge of a batch |
| (f) **Merge B97's two fixes early in the week** (`b97-slow-gates`) | About 14 job-min a run, if CI matches the laptop (about 532 + 494 s falling to about 21 + 54 s) | The critical path falls from about 9 min to the next slowest job (about 4.5 min, prediction markets) | Low. B97 changed no check, and its whole-run tallies matched the base | **Monday,** as the first merge of the week |
| (f2) **The known-red job** `validate_audit_fixes` fails on every run until A91's fix | none | none | It costs no time, but it turns every run red, so a new red reads as noise | Land A91's fix in Tuesday's first small PR, as planned |

**The recommended Monday set** (none changes any gate's verdict):
1. B97's fixes merged first (f);
2. the installed-environment cache (a);
3. the narrow docs path filter (d, `docs/briefs/**` and `docs/pastes/**` only);
4. one pending-deduplicating group for main (e, the gentle form), with A99's script
   reading the newest completed run.

Together, (a) and (f) take about 59 of a run's 134.5 job-minutes, and (e) removes most
of the merge week's superseded main runs outright.

**For Doctrine #2 or later:**
- grouping the small gates (b), once (a) shows the floor that remains;
- any narrowing of what a branch push runs (c), which the brief does not recommend.

## Part 4: built (B111, 2 Nov 2026)

Ruled 2 Nov 2026 from Part 3's recommended set. Built on `b100-hygiene`, which
merges in Tuesday's first small PR. Details are in `docs/briefs/b111-notes.md`.

| Ruling | What was built |
|---|---|
| (a) B97 first | Nothing to build: the merge sheet places it in the first small PR |
| (b) the package cache | `actions/cache@v4` on the interpreter's tree (`env.pythonLocation`), keyed `gates-pkgs-<OS>-py<exact version>-<hash of requirements.txt>`, in the gate and data-gate jobs; `pip install` runs only on a miss |
| (c) the docs-only push | The enumerate job reads the push's changed files and, when all are under `docs/briefs/` or `docs/pastes/`, narrows the matrix to check_library, check_registry and check_master_guide, with no data gates |
| (d) one pending run for main | main shares one concurrency group and never cancels in progress, so the newest pending run replaces older pending ones |
| (e) `make.sh`'s CR | `run_gate` strips a CR from each path, and CR is a word separator in the list loops |

Not taken: the slow gates on main only.
