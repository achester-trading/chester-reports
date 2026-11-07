# B139: items 131 and 132's code half, the HY bifurcation line and the dated public call (7 Nov 2026)

Paste B139 (`docs/pastes/B139.md`). Batch 25 items 131 and 132 (the order's 110
and 111), section 0's S3, S4 (O-111a) and S6, on `origin/b129-five-filings`. Its
`run_after` was amended by the operator from B137 to B136, which has reported;
B137 waits on the library-phase-3a merge.

**The base.** `origin/a126-item-124-tranche-0` at `caf6507a` (as expected).
`b139-items-131-132` is a new branch from it, because item 131 reads A126's
`derived.window_label`. It merges in chain-13 after A126.

## Item 131: the bifurcation line

- **The line.** `altdata/credit_bifurcation.py` (`config/credit_bifurcation.yaml`).
  It prints as a data sub-section with no paragraph in Plumbing & rates:
  - the close's `plumbing_section`;
  - the Weekly's and the Monthly's `plumbing_week`.
- **On the gate's fixture** (invented figures):

  > Credit bifurcation (as of 2026-11-04): cycle -- HY OAS 360 bp (+1 bp), Baa less the 10-year 152 bp (+0 bp); idiosyncratic -- CCC/HY OAS 3.75x, 100th percentile of 5y asked, 3.4y stored (n=895), CCC less BB +40 bp. Changes over 20 observations. Report only.

- **The ratio** is computed at read from `fred.ccc_oas` over `fred.hy_oas` on
  their common days; no new series is stored. Its percentile is over its own
  history inside five years asked. The window prints through A126's
  `window_label`: "5y asked, 3.4y stored", because FRED serves ICE's OAS for
  three years.
- **CCC less BB** is `calc.ccc_bb_oas_bp`'s change over the same 20 observations
  as the cycle series.
- **The composition clause** prints only when a stored scan row carries it: a
  scan family `credit-ccc`, metric "Share of the CCC index below $60", through
  the scans ingest with its URL and as-of. None is stored, so the clause is
  omitted. Sector concentration and distressed-exchange counts have no keyless
  source: a gap, as the order rules.
- **Rights.** A report line: no flag, and nothing enters the credit dimension.
  The dimension's members are unchanged (HY, BB, CCC, IG; CCC was already one)
  and `regime.py` reads none of it.
- **Not here.** Item 123's row-6 seed is B136's dated record. The narrative
  entries the order names under 110 ("lend to each other like 1929", the
  neocloud shakeout) are not in this paste's work list and are not drafted here.

## Item 132: the dated public call

**The entry type** (`config/dated_calls.yaml` `entry_type`; `altdata/dated_calls.py`).
Its rows sit in the register's database beside `narratives`, in three tables:
`dated_calls`, `dated_call_claims` and `dated_call_scores`.

| Field | What it holds |
|---|---|
| `call_id` | a stable id |
| `status` | proposed, active or rejected; proposed until the operator's accept-all |
| `direction` | down (a crash call) or up (a melt-up call) |
| `forecaster` | described by kind, never named, no handle |
| `incentive_tags` | `position_disclosed` and `product_sold` |
| `engagement_at_capture` | views and reposts, each null when not recorded |
| `posted_at`, `captured_at`, `expiry` | the call's dates |
| `claims` | each with its own date, its text, and a rule when the store can answer it |
| score | per claim at its date: hit, miss or unresolved |

**The scoring rule.** The register's grading pass, `narratives.resolve_due`,
calls `dated_calls.grade_due`. A claim is scored once, after its date, when the
store holds a close on or after that date.
- **A claim with a rule** is scored hit or miss from stored closes as known at
  the cutoff. There are four rule kinds:
  - `move_on`: one day's move;
  - `move_by`: any close through the date against a baseline close;
  - `level_by`: a level crossed by the date;
  - `move_from_high`: a fall from the high of N closes to the baseline.
- **A claim with no rule** is `unresolved`, left for the operator. When config
  carries an `operator_score`, from a ruling, that score is written in its place.
- **Scores are permanent.** Each is written once; a trigger refuses any edit or
  delete. A call cannot be deleted either: it is rejected instead.

**Seeding.** `python -m altdata.narratives seed` also seeds the calls, and
`python -m altdata.dated_calls seed|grade|counts|list` runs each step alone.

**Row one, a judgment draft for accept-all.**
- `x_funnel_15day_2026_11_05`: "an X membership-funnel account", direction down.
  It discloses a short position and sells a paid membership community.
- It is captured from the chat's screenshots of 6 Nov (07:53 ET) and expires
  20 Nov 2026. It holds 17 claims, as the order lists them.
- Its engagement is not recorded in the order. It is admitted by the order's
  ruling ("row one"), not by the O-111a threshold.
- Six claims carry a rule:
  - Day 1's Nasdaq-100 -6.4%;
  - -20% by day 7 (11 Nov);
  - the S&P 500 -10%;
  - bitcoin under $70,000;
  - chips -38% from the top;
  - Korea -44%.

  The other eleven are the operator's.
- **The session's readings, for the operator to amend at accept-all:**
  - the moves are measured from the 4 Nov close (the close before day 1);
  - "from the top" means the high of the 252 closes to 4 Nov, and Korea's -44% is
    read the same way;
  - the proxies are QQQ for the Nasdaq-100, SMH for chips and EWY for Korea.

**The two counts.** `calc.viral_call_count.down` and `.up` count rows captured per
ET day by direction, from the register's rows; rejected rows are excluded.
- The features pass writes them (`market_features`, after the 6e rows; never
  fatal), with zeros from the first captured row. A day's count is knowable at
  that day's ET end.
- With no rows, nothing is stored and the line prints "no rows yet".
- Both keys are registered (narrative group, count, quantity), trigger-ineligible
  and barred from the market-state object.

**O-111a** (S4, D62) is in config: 10,000 views or 100 reposts at capture, claims
within 30 days. Its review date is 6 Dec 2026, one month after the ruling; the
order says "after one month of rows".

## The Capitulation Count change (item 97; V-111d)

**V-111d, read 7 Nov 2026** on `origin/b79-capitulation-count`, whose
`config/capitulation_count.yaml` is version capitulation-count-1. Its five
families are vix, put_call, gamma, short_interest and flows. None is a
social-attention input, so the two inputs are new, not an extension.

**B79 is not merged and not on this base,** so its config file is not here. The two
inputs are declared in `config/dated_calls.yaml` `capitulation_count_inputs`:
- `viral_crash_calls` reads `calc.viral_call_count.down`;
- `viral_melt_up_calls` reads `calc.viral_call_count.up`.

Each is `direction: none`, `scores: false` and prints "no rows yet" when empty.
The count's points are unchanged.

**For chain-13's stitch, once B79 is in:** move that block unchanged into
`config/capitulation_count.yaml` as `attention_inputs:`, just before
"97(a) the count".
- **Tested.** On a scratch worktree of `origin/b79-capitulation-count` with the
  block inserted there, `validate_capitulation_count` ran 58/0 and
  `validate_capitulation_feeds` ran 25/0. The worktree was removed and nothing
  was committed to B79's branch.
- **Not done.** Printing the inputs in the count's block (`capitulation_block.py`)
  is not in this paste.

## The gates

| Gate | Result |
|---|---|
| `validate_items_131_132` (new; clock pinned) | 56 passed, 0 failed |
| `validate_item_124_t0` (A126's) | 45 passed, 0 failed |
| `validate_narratives` | 103 passed, 0 failed |
| the Capitulation Count's (`validate_capitulation_count`, on B79's tree with the block) | 58 passed, 0 failed |
| `validate_stack --group A` (Plumbing) | 13 passed, 0 failed |
| `check_registry` | OK |
| `validate_gates` | 32 passed, 0 failed |
| `check_library` | 27 papers, 0 failures, 0 warnings |

Run as well, all with 0 failed:

| Gate | Passed |
|---|---|
| `validate_audit_3a` | 88 |
| `validate_lenses` | 49 |
| `validate_regime` | 524 |
| `validate_stack_cadence` | 104 |
| `validate_attribution` | 85 |
| `validate_basis_proxy` | 31 |
| `validate_batch3_a` | 79 |
| `validate_rates_anchors` | 23 |
| `validate_st_r5_rates` | 72 |
| `validate_6e_rest` | 34 |
| `validate_batch14_b2` | 57 |
| `validate_st_t5_render` | 46 |
| `validate_weekly_stack` | 83 |
| `validate_monthly_stack` | 268 |
| `validate_weekly_complete` | 96 |
| `validate_secrets` | 58 |
| `validate_capitulation_feeds` (B79's tree) | 25 |

**Outside the paste's file list:**
- `config/catalogue_commands.yaml`: two lines;
- `metrics_registry.yaml`: the two keys and their bar;
- `altdata/market_features.py`: the counts' call;
- CLAUDE.md's gate count, 167 to 168.

**For chain-13's merge:**
- **The gate count.** B134, B135 and B136 each also move CLAUDE.md's count to
  168, so after all four the count is 171 code gates (168 Python).
- **The proposals pin.** `validate_batch14_b2`'s pin stays at seven here, since
  this branch adds no proposal.

## CI

Read once after the push.
