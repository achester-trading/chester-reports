# ST-R6.74b ledger -- leveraged funds' extreme net shorts in ES and the S&P 500 after (item 74)

**Edition:** 2026-10-23, read-only from the store `chester.db` (stored history only; nothing fetched). A run against the box's store supersedes it (a new dated file).

**The pass rule is pre-registered**: `docs/ledgers/short-extremes-preregistration-2026-10.md`, SHA-256 `584442322783b3cf85ca6bb16c4a08b705ec36c8360f8323dcb4233273f90211`, committed alone before any scoring code and never edited.

| | |
|---|---|
| As of | 2026-10-23 |
| Window | none ranked; each week ranked against the 260 reports ending at it |
| n | 0 (pending 0; baseline 0 weeks) |
| Statistic | the S&P 500's median 20-session outcome after an episode's first week (ES's leveraged-fund net short at or above its 90th percentile of five years), against every ranked week's, and the share of episodes positive |
| Pass rule (as pre-registered) | INSUFFICIENT below 12 episodes; PASS when the episodes' median 20-session outcome beats the baseline's by at least 1.0 pp and at least 60% are positive; FAIL otherwise |
| Verdict | **INSUFFICIENT -- no ES rows in the store yet (the TFF pull adds ES from this build)** |
| Rights consequence | Grants nothing: the squeeze-risk flag keeps a flag's rights, and any T&B or Book modifier is the operator's ruling. The verdict reaches the register only as a rule-31 draft. |

## Results

- Episodes: median 20-session outcome —, 5-session —; — with a positive 20-session outcome.
- Baseline: median 20-session —, 5-session —.
- The episodes are in the CSV beside this file.
