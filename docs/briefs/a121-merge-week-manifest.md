# A121: the merge-week manifest (3 Nov 2026, read before the 17:20 window)

Session A, read-only. Branch `a121-merge-week-manifest` off origin/main at
`422ea697`. Paste committed first as `docs/pastes/A121.md`. Nothing on any chain
member was changed.

**Sources.**
- The rehearsed SHAs are A105's table and A106's additions:
  `docs/briefs/a105-merge-week-script.md` section 1, on
  origin/a105-merge-week-rehearsal-2.
- The CI rows are `gh run list --branch <b> --limit 1` and the run's failed jobs.
- A conflict forecast takes the files a moved branch changed since its rehearsed
  SHA and intersects them with the files every other member of its chain changes
  against main (`git diff --name-only origin/main...<member>`). Each overlap was
  then trial-merged pairwise with `git merge-tree --write-tree`, which writes no
  branch and no worktree.

## Part 1: tonight's CI (the branches pushed 2-3 Nov)

| Branch | Tip | Run at the tip | Conclusion | Failed jobs, classified |
|---|---|---|---|---|
| a96-price-migration-fred (A114, A115) | `9722f6ac` | 41560022224 | failure | validate_monthly, validate_voices, validate_st_t5_render, validate_alpha_proposer: known (date drift); validate_audit_fixes: known (no A91 fix) |
| a116-clock-reads-gate | `ad3ecd68` | 41567752203 | failure | the same five, all known |
| a117-attention-ledger-pending | `450455af` | 41568264074 | failure | the same five, all known |
| a112-em-shock-screen-amendment (A118) | `ac8b23c7` | 41568488585 | failure | the same five, all known |
| a119-clock-burn-down-1 | `18a24e94` | 41570583971 | failure | the same five, all known |
| a94-ll6-forecasters (A120) | `2cfecbe0` | 41570798100 | failure | the four date-drift gates: known; validate_prediction_markets: known, see below |
| b101-date-drift-gates (A110's pins) | `9de522f8` | 41585481382 | queued at the read | B126's run before it, 41573502772 (`1ce709d6`), failed only validate_audit_fixes: known |

**No new red tonight.** a94's `validate_prediction_markets` is not on the paste's
known list, but it is not new either:
- **It predates A120.** It was the only red on a94's first run, 41006558043 on
  30 Oct, and it fails the same three checks on b85-gitattributes-lf and
  b85-crypto-derived-keys: "What's priced prints the rate path ()", "and each
  meeting's venue odds beside the futures' implied move", and "What doesn't fit
  carries the venue-vs-futures disagreement ()".
- **The cause is the clock.** A88 Part 0 pinned that gate's section J clock on
  main (`debc0c6a`), after those branches' bases.
- **It passes where it will land.** It passes on main, and in the rehearsed tree
  under all four of A110's clocks. It goes away on merge.

## Part 2: the manifest

| Chain | Member | Tip now | Rehearsed | Moved (pastes) | CI at the tip | Failed jobs |
|---|---|---|---|---|---|---|
| chain-9 | A91 cherry-pick f8819b62 | `f8819b62` | `c2dfa70f (cherry-picked)` | n/a (a commit) | n/a | - |
| chain-9 | b85-gitattributes-lf | `5cb338fa` | `5cb338fa` | no | 40935942734 failure | validate_prediction_markets |
| chain-9 | b101-date-drift-gates | `9de522f8` | `666611e1` | yes (A110, B126 (4 commits)) | 41585481382 queued | - |
| chain-9 | b97-slow-gates | `267bd42b` | `267bd42b` | no | 41267671490 failure | validate_audit_fixes, validate_st_t5_render, validate_monthly |
| chain-8 | b86-chain-8-assembly | `faac8c48` | `4e6814df (merge-base)` | yes (B110 (2 commits)) | 41521347896 failure | validate_alpha_proposer, validate_audit_fixes, validate_monthly, validate_st_t5_render, validate_voices |
| chain-10 | a90-monthly-dryrun-2 | `08757f97` | `f8819b62` | yes (A111 (2 commits)) | 41543014216 failure | validate_monthly, validate_voices, validate_alpha_proposer, validate_st_t5_render |
| chain-10 | b95-cboe-held | `2250b5cb` | `2250b5cb` | no | 41226280639 failure | validate_audit_fixes |
| chain-10 | a84-feed-summary-and-allowances | `636b9173` | `636b9173` | no | 40934628000 failure | validate_audit_fixes |
| chain-10 | b81-batch-18-overnight-session | `6256a67c` | `6256a67c` | no | 40934966390 failure | validate_audit_fixes |
| chain-10 | b82-aaii-bearish-share | `bd01fe67` | `bd01fe67` | no | 40935187264 failure | validate_audit_fixes |
| chain-10 | b85-crypto-derived-keys | `f864e8f6` | `f864e8f6` | no | 40987510422 failure | validate_prediction_markets |
| chain-10 | b87-yields-direction | `ec96ceec` | `ec96ceec` | no | 40989128804 failure | validate_audit_fixes |
| chain-10 | b89-cboe-terms-check | `4e737488` | `4e737488` | no | 41008607718 failure | validate_audit_fixes |
| chain-10 | b90-nautilus-assessment | `d7ab0ea8` | `d7ab0ea8` | no | 41008986256 failure | validate_audit_fixes |
| chain-10 | b91-batch-19-filing | `96e97e08` | `96e97e08` | no | 41382168405 failure | validate_monthly, validate_audit_fixes, validate_voices, validate_st_t5_render, validate_alpha_proposer |
| chain-10 | b92-batch-20-filing | `30c16e1c` | `30c16e1c` | no | 41007464093 failure | validate_audit_fixes |
| chain-10 | b95-batch-21-filing | `c72f4f38` | `9aeeee9c` | yes (B115 (2 commits)) | 41531183755 failure | validate_monthly, validate_voices, validate_audit_fixes, validate_st_t5_render, validate_alpha_proposer |
| chain-11 | a92-dth1-box-pieces | `fb3e9a30` | `fb3e9a30` | no | 41385905283 failure | validate_monthly, validate_voices, validate_audit_fixes, validate_st_t5_render, validate_alpha_proposer |
| chain-11 | a93-ibkr-daily-bars | `5b2297ec` | `5b2297ec` | no | 40987766993 failure | validate_audit_fixes |
| chain-11 | a94-ll6-forecasters | `2cfecbe0` | `d70205dd` | yes (A120 (2 commits)) | 41570798100 failure | validate_monthly, validate_prediction_markets, validate_voices, validate_st_t5_render, validate_alpha_proposer |
| chain-11 | a96-price-migration-fred | `9722f6ac` | `d356e613` | yes (A115, A114, A104 (6 commits)) | 41560022224 failure | validate_monthly, validate_audit_fixes, validate_voices, validate_st_t5_render, validate_alpha_proposer |
| chain-11 | a97-weekly-readability | `d30238ed` | `d30238ed` | no | 41223209504 failure | validate_audit_fixes |
| chain-11 | a95-monthly-first-edition | `a2737d15` | `a2737d15` | no | 41383386271 failure | validate_voices, validate_monthly, validate_audit_fixes, validate_st_t5_render, validate_alpha_proposer |
| chain-11 | a103-weekly-consistency | `b3a1b9f5` | `b3a1b9f5` | no | 41385508986 failure | validate_voices, validate_audit_fixes, validate_monthly, validate_st_t5_render, validate_alpha_proposer |
| chain-11 | a98-paper-executor | `73d12a1c` | `73d12a1c` | no | 41224982846 failure | validate_audit_fixes |
| chain-11 | b98-ks-family-registry | `dc8eeb12` | `f0343d55` | yes (A113 (2 commits)) | 41546496953 failure | validate_alpha_proposer, validate_audit_fixes, validate_monthly, validate_st_t5_render, validate_voices |
| chain-11 | b99-premium-sleeve | `da345be9` | `da345be9` | no | 41271301354 failure | validate_audit_fixes, validate_monthly, validate_st_t5_render |
| chain-12 | b96-doctrine-2-pack-refresh | `c17742cf` | `c23c6413` | yes (B125, B120, B118 (6 commits)) | 41573351937 failure | validate_monthly, validate_audit_fixes, validate_voices, validate_st_t5_render, validate_alpha_proposer |
| chain-12 | b100-hygiene | `d2c67e00` | `12d7f940` | yes (B124, B111 (4 commits)) | 41573060851 failure | validate_monthly, validate_audit_fixes, validate_voices, validate_st_t5_render, validate_alpha_proposer |
| chain-12 | b102-readable-editions-register | `822b74db` | `f6bdc7c3` | yes (B123, B121 (4 commits)) | 41559927287 failure | validate_monthly, validate_voices, validate_audit_fixes, validate_st_t5_render, validate_alpha_proposer |
| chain-12 | b109-names-gate | `46da3bb5` | `04439228` | yes (B111 (1 commits)) | 41523453994 failure | validate_monthly, validate_audit_fixes, validate_voices, validate_st_t5_render, validate_alpha_proposer |

**Counts:**
- **Members:** 31, one of them the A91 commit `f8819b62`, cherry-picked
  as `c2dfa70f` and fixed.
- **Moved since the rehearsal:** 11.
- **Red at the tip:** 29, all known. One more is queued
  (b101-date-drift-gates).
- **Overlaps forecast:** 6 moved branches
  overlap a chain-mate's files. Every one of those overlaps trial-merges clean.

## Part 3: the three lists

### Branches that moved since the rehearsal
- **b101-date-drift-gates** (chain-9): `666611e1` to `9de522f8`; A110, B126 (4 commits).
- **b86-chain-8-assembly** (chain-8): `4e6814df` to `faac8c48`; B110 (2 commits).
- **a90-monthly-dryrun-2** (chain-10): `f8819b62` to `08757f97`; A111 (2 commits).
- **b95-batch-21-filing** (chain-10): `9aeeee9c` to `c72f4f38`; B115 (2 commits).
- **a94-ll6-forecasters** (chain-11): `d70205dd` to `2cfecbe0`; A120 (2 commits).
- **a96-price-migration-fred** (chain-11): `d356e613` to `9722f6ac`; A115, A114, A104 (6 commits).
- **b98-ks-family-registry** (chain-11): `f0343d55` to `dc8eeb12`; A113 (2 commits).
- **b96-doctrine-2-pack-refresh** (chain-12): `c23c6413` to `c17742cf`; B125, B120, B118 (6 commits).
- **b100-hygiene** (chain-12): `12d7f940` to `d2c67e00`; B124, B111 (4 commits).
- **b102-readable-editions-register** (chain-12): `f6bdc7c3` to `822b74db`; B123, B121 (4 commits).
- **b109-names-gate** (chain-12): `04439228` to `46da3bb5`; B111 (1 commits).

### Reds at the tip

Every red is a known class. The jobs:

- b85-gitattributes-lf: validate_prediction_markets (known (clock; A88's pin on main, debc0c6a, after this base))
- b97-slow-gates: validate_audit_fixes (known (no A91 fixture fix)); validate_st_t5_render (known (date drift; b101's pins)); validate_monthly (known (date drift; b101's pins))
- b86-chain-8-assembly: validate_alpha_proposer (known (date drift; b101's pins)); validate_audit_fixes (known (no A91 fixture fix)); validate_monthly (known (date drift; b101's pins)); validate_st_t5_render (known (date drift; b101's pins)); validate_voices (known (date drift; b101's pins))
- a90-monthly-dryrun-2: validate_monthly (known (date drift; b101's pins)); validate_voices (known (date drift; b101's pins)); validate_alpha_proposer (known (date drift; b101's pins)); validate_st_t5_render (known (date drift; b101's pins))
- b95-cboe-held: validate_audit_fixes (known (no A91 fixture fix))
- a84-feed-summary-and-allowances: validate_audit_fixes (known (no A91 fixture fix))
- b81-batch-18-overnight-session: validate_audit_fixes (known (no A91 fixture fix))
- b82-aaii-bearish-share: validate_audit_fixes (known (no A91 fixture fix))
- b85-crypto-derived-keys: validate_prediction_markets (known (clock; A88's pin on main, debc0c6a, after this base))
- b87-yields-direction: validate_audit_fixes (known (no A91 fixture fix))
- b89-cboe-terms-check: validate_audit_fixes (known (no A91 fixture fix))
- b90-nautilus-assessment: validate_audit_fixes (known (no A91 fixture fix))
- b91-batch-19-filing: validate_monthly (known (date drift; b101's pins)); validate_audit_fixes (known (no A91 fixture fix)); validate_voices (known (date drift; b101's pins)); validate_st_t5_render (known (date drift; b101's pins)); validate_alpha_proposer (known (date drift; b101's pins))
- b92-batch-20-filing: validate_audit_fixes (known (no A91 fixture fix))
- b95-batch-21-filing: validate_monthly (known (date drift; b101's pins)); validate_voices (known (date drift; b101's pins)); validate_audit_fixes (known (no A91 fixture fix)); validate_st_t5_render (known (date drift; b101's pins)); validate_alpha_proposer (known (date drift; b101's pins))
- a92-dth1-box-pieces: validate_monthly (known (date drift; b101's pins)); validate_voices (known (date drift; b101's pins)); validate_audit_fixes (known (no A91 fixture fix)); validate_st_t5_render (known (date drift; b101's pins)); validate_alpha_proposer (known (date drift; b101's pins))
- a93-ibkr-daily-bars: validate_audit_fixes (known (no A91 fixture fix))
- a94-ll6-forecasters: validate_monthly (known (date drift; b101's pins)); validate_prediction_markets (known (clock; A88's pin on main, debc0c6a, after this base)); validate_voices (known (date drift; b101's pins)); validate_st_t5_render (known (date drift; b101's pins)); validate_alpha_proposer (known (date drift; b101's pins))
- a96-price-migration-fred: validate_monthly (known (date drift; b101's pins)); validate_audit_fixes (known (no A91 fixture fix)); validate_voices (known (date drift; b101's pins)); validate_st_t5_render (known (date drift; b101's pins)); validate_alpha_proposer (known (date drift; b101's pins))
- a97-weekly-readability: validate_audit_fixes (known (no A91 fixture fix))
- a95-monthly-first-edition: validate_voices (known (date drift; b101's pins)); validate_monthly (known (date drift; b101's pins)); validate_audit_fixes (known (no A91 fixture fix)); validate_st_t5_render (known (date drift; b101's pins)); validate_alpha_proposer (known (date drift; b101's pins))
- a103-weekly-consistency: validate_voices (known (date drift; b101's pins)); validate_audit_fixes (known (no A91 fixture fix)); validate_monthly (known (date drift; b101's pins)); validate_st_t5_render (known (date drift; b101's pins)); validate_alpha_proposer (known (date drift; b101's pins))
- a98-paper-executor: validate_audit_fixes (known (no A91 fixture fix))
- b98-ks-family-registry: validate_alpha_proposer (known (date drift; b101's pins)); validate_audit_fixes (known (no A91 fixture fix)); validate_monthly (known (date drift; b101's pins)); validate_st_t5_render (known (date drift; b101's pins)); validate_voices (known (date drift; b101's pins))
- b99-premium-sleeve: validate_audit_fixes (known (no A91 fixture fix)); validate_monthly (known (date drift; b101's pins)); validate_st_t5_render (known (date drift; b101's pins))
- b96-doctrine-2-pack-refresh: validate_monthly (known (date drift; b101's pins)); validate_audit_fixes (known (no A91 fixture fix)); validate_voices (known (date drift; b101's pins)); validate_st_t5_render (known (date drift; b101's pins)); validate_alpha_proposer (known (date drift; b101's pins))
- b100-hygiene: validate_monthly (known (date drift; b101's pins)); validate_audit_fixes (known (no A91 fixture fix)); validate_voices (known (date drift; b101's pins)); validate_st_t5_render (known (date drift; b101's pins)); validate_alpha_proposer (known (date drift; b101's pins))
- b102-readable-editions-register: validate_monthly (known (date drift; b101's pins)); validate_voices (known (date drift; b101's pins)); validate_audit_fixes (known (no A91 fixture fix)); validate_st_t5_render (known (date drift; b101's pins)); validate_alpha_proposer (known (date drift; b101's pins))
- b109-names-gate: validate_monthly (known (date drift; b101's pins)); validate_audit_fixes (known (no A91 fixture fix)); validate_voices (known (date drift; b101's pins)); validate_st_t5_render (known (date drift; b101's pins)); validate_alpha_proposer (known (date drift; b101's pins))

- b101-date-drift-gates: queued at the read (A110's pins); its previous run
  failed validate_audit_fixes only (known).

**What clears them.**
- **The date drift:** b101's pins, which step 0 merges first. The four gates
  pass on b101 (B126, 41573502772) and on the rehearsed tree.
- **validate_audit_fixes:** A91's fixture fix, in step 0 too.
- **validate_prediction_markets:** A88's pin, already on main.

### Conflict forecasts by chain

Each moved branch's changed files, against each chain-mate's files changed
against main, file by file. "Trial merge" is `git merge-tree` of the two tips.

**chain-9.**

- b101-date-drift-gates against b97-slow-gates: `tools/validate_em_scorecard.py`, `tools/validate_sr38_inbox.py`, `tools/validate_thesis_register.py`

**chain-8.**

- b86-chain-8-assembly: none.

**chain-10.**

- a90-monthly-dryrun-2 against b87-yields-direction: `tools/validate_audit_fixes.py`
- b95-batch-21-filing against b81-batch-18-overnight-session: `docs/signal-triage-register.md`
- b95-batch-21-filing against b91-batch-19-filing: `docs/signal-triage-register.md`
- b95-batch-21-filing against b92-batch-20-filing: `docs/signal-triage-register.md`

**chain-11.**

- a94-ll6-forecasters: none.
- a96-price-migration-fred against a93-ibkr-daily-bars: `config/data_quality.yaml`
- a96-price-migration-fred against a94-ll6-forecasters: `config/data_quality.yaml`
- a96-price-migration-fred against b98-ks-family-registry: `config/data_quality.yaml`, `tools/validate_quality.py`
- a96-price-migration-fred against b99-premium-sleeve: `config/data_quality.yaml`, `tools/validate_quality.py`
- b98-ks-family-registry against b99-premium-sleeve: `docs/alpha-lab-rules.md`, `docs/briefs/b98-notes.md`, `tools/validate_alpha_proposer.py`

**chain-12.**

- b96-doctrine-2-pack-refresh: none.
- b100-hygiene against b109-names-gate: `.github/workflows/registry-check.yml`
- b102-readable-editions-register: none.
- b109-names-gate: none.

**Trial merges of every overlap above:**
- **Clean:**
  - b101 + b97;
  - a90 + b87;
  - b95-batch-21 + each of b81, b91 and b92;
  - b98 + b99;
  - b100 + b109.
- **a96 against a93, a94, b98 and b99:** conflicts in `Makefile`, and with some
  of them in `CLAUDE.md`, `metrics_registry.yaml` or shared docs
  (`docs/master-guide.md`, `docs/signal-triage-register.md` and others). None
  of those files is one a96 changed since the rehearsal.
  - The same four merges with a96 at its rehearsed SHA `d356e613` give the
    **identical** conflict lists. So they are the pairwise collisions the
    rehearsal already resolved in merge order, not new ones.
  - a96's two new overlaps, `config/data_quality.yaml` (A115's pairs) and
    `tools/validate_quality.py` (A115's group G2), merge clean.

**Net:** no conflict at assembly is forecast that the rehearsal did not already
meet.

## Gates

| Gate | Result |
|---|---|
| `check_registry` | OK |
