# AQ-8a — the gold residual, the driver attribution, the two-bid's first parts, yields-up/dollar-down: build notes (10 Oct 2026)

Branch `aq-8a-gold-residual`, from `origin/main` at `9788535`, not merged. Built
against the Alternative Assets Quarterly change order
(`docs/change-order-alternative-assets-quarterly-2026-10-10.md`), §5 rows "Gold
residual", "Driver attribution", "Two-bid decomposition" and
"Yields-up/dollar-down", read with §4.2 and §4.4. The change order itself is not
edited. AQ-5's correlation layer (`aq-5-correlation-layer`, unmerged) is the model
for this branch's conventions and the owner of the universe the driver
attribution reads; this branch will merge beside it.

## What was built

| Piece | Where |
|---|---|
| Windows, factors, the hooks, the regime splits, the two-bid rules | `config/attribution.yaml` |
| Gold residual, driver attribution, sign stability, yields-up/dollar-down; readers; CLI | `altdata/attribution.py` |
| The paper bid from the captured chains; the two-bid state; CLI | `altdata/paper_bid.py` |
| GLD, SLV, IBIT, USO captured nightly (`PAPER_BID_SYMBOLS`, `chain_universe()`) | `altdata/config.py`, `run_eod.py` stage 1 and new stage 1c |
| The nightly compute (last 3 months, last 6 weeks), after the chains | `scripts/run_eod_cron.sh` |
| Registry: 9 entries, 6 bulk blocks, 2 mechanism groups, the `rights_ceiling` vocabulary, IMF IFS not_yet_sourced | `metrics_registry.yaml`, `source_registry.yaml` |
| The Monthly: the metals block, the driver table, the fiscal_dollar line | `monthly_macro/stack.py` (`gold_two_bid`, `driver_attribution_block`), `config/monthly_themes.yaml` (v4) |
| The Weekly: one Plumbing line when the flag fired | `daily_cascade/weekly_stack.py` `plumbing_week` |
| The gate | `tools/validate_attribution.py` (in the Makefile's list) |

### The gold residual — `calc.gold_residual.*`

Gold's monthly log return regressed on the 10-year real yield's monthly change
(`fred.tips_10y`, DFII10, in percentage points) and the broad dollar's monthly
log return (`fred.dxy`, DTWEXBGS), over a rolling 36 months. Four series:
`residual` (this month's return less the window's fit, in log-return percent),
`explained_share` (R²), `beta_real_yield`, `beta_dollar`. Gold is
`yfinance.mkt_gold_front` (GC=F), with `yfinance.mkt_gld` for any month the front
has no return. That is the fallback `config/reporting_stack.yaml` already
declares, and each return is taken within one series, never across the two. The
Monthly prints the four in the triple form: latest, long-run average and
percentile over the store's own history, with a five-year column reading "until
the lenses". Kill state: none ruled (§5: —).

### The driver attribution — `calc.driver_attribution.<family>.*`

The same method for every family in the correlation layer's universe
(`config/correlation.yaml`, its members with a `key`). Each family is read on its
own transform and inversion: yen and yuan inverted, as AQ-5 does. Its monthly
return is regressed on four factors over a rolling 60 months:

- the real-yield change;
- the broad dollar;
- the growth surprise, `calc.surprise_vs_naive.nfp`;
- the inflation surprise, `calc.surprise_vs_naive.core_cpi`.

Per family and month it stores:

- `explained_share`;
- `residual`;
- `loading.<factor>`, standardised (beta × the factor's sd ÷ the return's sd, so
  the four compare);
- `sign_stable.<factor>`.

The Monthly prints one table: family, explained share, the largest loading, the
residual's sign this month, and the sign-stability state.

- **The surprises are aligned to the month they printed in.** September's
  payrolls surprise is a factor for October. The factor uses the reference month
  plus one, not the stored `available_at`, because migrated FRED rows carry the
  pull time as their availability, which would put a decade of surprises in one
  month. The gate shows the fit is materially worse without the lag.
- **The two hooks are named and empty, with no stub data behind either.**
  - `attribution.quadrant_factors()` returns None until round 4 item 25 lands;
    its factors then replace the two naive surprises.
  - `config driver_attribution.supply_proxy` is empty for every family. A store
    key there joins that family's regression as a fifth factor.
- **The kill condition.** The §5 text sits in each driver block's
  `kill_condition`. The check is computed and printed, and nothing acts on it:
  - a factor is *stable* when its loading has one sign over the whole five-year
    window and in both halves of every testable regime split;
  - a factor whose sign is not stable reads "no stable sign (kill condition met;
    not acted on)";
  - a family with no split long enough reads *untestable* and writes no sign row.

### The two-bid decomposition, the parts that start now

- **Paper leg.** `calc.paper_bid.<symbol>.net_call_put_oi` and `.rr_25d`, for
  GLD, SLV, IBIT and USO.
  - **Source:** each session's close-nearest capture (`exposure_compute.newest_chains`),
    the capture the SPY exposure fields read.
  - **Delta:** the same Black-Scholes delta from the chain's own IV.
  - **Net OI:** contracts over every expiry after the session's own. The
    session's own expiry is excluded, by the 5 Sep settled-capture ruling.
  - **Risk reversal:** each expiry's 25-delta call IV less its 25-delta put IV,
    interpolated in delta and taken from expiries of 7 days or more. The 30-day
    figure is linear in days between the expiries either side of 30, or the
    nearest expiry where none brackets it.
  - **Timing:** `available_at` is the capture's `fetched_at`. Written by
    `run_eod.py` stage 1c, which is never fatal.
  - **Kill condition:** the twelve-month condition on call-put OI is in its
    block's `kill_condition`, dated today. Its state reads "kill test waits: n
    of 12 months".
- **Official leg.** China's `safe.gold_reserves_oz` is read now.
  `imf.ifs_official_gold_oz` is registered `not_yet_sourced` under a declared
  `imf_ifs` source, with no writer, because the ruling is pending.
- **The two states print only when both legs hold 12 months.** Until then the
  metals block's line says which leg waits and how many months it holds.
  - **Fragile rally:** GLD's call-put OI and risk reversal both at or above the
    80th percentile of their own history, with China's 3-month change exactly
    zero.
  - **Durable base:** both paper readings at or below the 50th percentile, with
    China accumulating.
  - **Neither:** any other combination.
  - **Not printed:** SLV, USO and IBIT accrue their paper leg with no official
    leg declared, so they have no state yet.

### Yields-up/dollar-down — `calc.yields_up_dollar_down.*`

One series under both papers' names, in every registry description: Currencies
§19 "yields-up/dollar-down" and the Rates paper's S10/S29 "credibility
repricing".

- **The flag:** weekly (weeks ending Friday), 1 when DGS10 rose and DTWEXBGS fell
  over the week.
- **Beside it:** `yield_change_bp` and `dollar_change_pct`.
- **Recurrence:** `recurrence_13w`, the flagged weeks in the trailing 13. It is
  written once 13 weeks are held.
- **Persistence:** `persistence_weeks`, the consecutive flagged weeks. It is
  written once the run's start is in the history, and is 0 in an unflagged week.

Narrow flag, not trigger-eligible. The Monthly's fiscal_dollar theme carries the
recurrence as its line. The Weekly prints one line in Plumbing, and only when a
flagged week became knowable that week; otherwise it prints nothing.
DTWEXBGS posts about a week late, so the week named is usually the one before.

## Readings this session set (each named in `config/attribution.yaml`, one place to change)

- **A month or week is read only once its last print is final.** The print must
  fall on the last calendar day, or a later print must exist. The row's
  `available_at` is the later of that print's and the proving print's, so there
  is no tolerance to tune. A month ending on a Sunday is read on its Friday once
  Monday's print is in.
- **The regime splits.** §5 names "the regime splits" without defining them.
  - Real yields rising or falling: the 12-month change in DFII10.
  - Core CPI inflation above or below its own median over the window. This is an
    own-history split, never a CPI threshold, and uses the surprise's one-month
    lag.
  - A half must hold at least 18 months to be tested.
- **The two-bid numbers.** Surging is the 80th percentile, absent the 50th. The
  official leg reads the change over 3 prints: above zero is accumulating, zero
  is flat, below zero is selling.

## Why the four symbols are capture-only

They are captured with the 13 in stage 1 and read only by stage 1c. They are not
in `options_universe()`, so they enter no exposure profile, no pin log, no dealer
table and no consensus log. The pin statistics and the close's tables stay the
13's. `--symbols` narrows them away, as it does the vendor two. The extra capture
adds roughly a minute to the 16:10 pass, against its 30-minute ceiling.

## What waits

- **IMF IFS official holdings.** A ruling on the source is pending. It is
  registered not_yet_sourced, with no writer.
- **GLD holdings in tonnes.** A feeds-writer item for a later order, named in the
  metals block's not-tracked list.
- **Round 4 item 25, the surprise quadrant.** It replaces the two naive surprises
  through `quadrant_factors()`.
- **The metric lenses (6e).** They supply the five-year percentile column and each
  series' `long_window`. Until then percentiles are over the store's full history.
- **AQ-1, the quarterly cadence.** The Quarterly prints these analyses in full.
  This branch prints the monthly rows only.
- **AQ-10, the kill-condition gate.** It runs the twelve-month forward-return test
  on call-put OI once the series holds twelve months; until then the state reads
  "waits".
- **The family supply proxies.** A named hook, empty in v1.
- **AQ-5's universe.** The driver attribution reads `config/correlation.yaml` and
  computes nothing until AQ-5 is merged. Its Monthly table says so. Merge AQ-5
  first, or re-run the backfill after it lands (it is idempotent).

## Merge notes

- **`metrics_registry.yaml` vocabulary.** This branch carries AQ-5's
  `rights_ceiling` vocabulary lines byte for byte, at the same place, so the two
  merge as one change. The new mechanism groups (`factor_attribution`,
  `paper_bid`) and the bulk blocks sit away from AQ-5's additions. A trial merge
  of `origin/aq-5-correlation-layer` into this branch was clean, and this
  branch's gate and the registry gate passed on the result (in the run report).
- **The driver blocks carry no `expected_members`.** Their members are AQ-5's
  keyed universe, whose deliberate count is that layer's `correlation_matrix`
  block. A second count of the same list could only disagree with it.
- **`monthly_macro/stack.py`.** The new functions sit after `detail_tables`, away
  from AQ-5's `correlations_block`. The slow layers' two calls sit in lines AQ-5
  does not touch.
- **CLAUDE.md is not edited on this branch,** to stay clear of AQ-5's edit to the
  same repo-layout lines. Two lines go in at the merge: `attribution.py` and
  `paper_bid.py` in the layout, and the gate count.

## Box commands (the operator, after the merge; inside the windows)

The one-shot backfill, idempotent (only changed values are written):

```
cd ~/chester-reports && git pull --ff-only
.venv/bin/python -m altdata.attribution compute --backfill
.venv/bin/python -m altdata.attribution show
```

Run it once more after AQ-5 merges, if AQ-5 lands second, to write the driver
attribution's history. The paper bid has no history to backfill, because chains
are not retrievable. It accrues from the first EOD pass after the merge, and the
nightly stage writes it. `python -m altdata.paper_bid show` reads it back.
