# The wealth-effect impulse against real consumption -- pre-registration (ST-R6.66c, Batch 14 item 66)

*Written and committed on 21 Oct 2026, before any of its scoring code, by session B on branch `b52-batch14-a2`. **Never edited.** A change is a new registration in a new dated file; this one stays as written, and `tools/validate_batch14_a2.py` holds it to its SHA-256. The spec is signal-triage Batch 14 (`docs/change-order-signal-triage-batch-14-2026-10-20.md`), item 66 (written as 59), ruling 3: "Build a calibration ledger against real consumption growth." Rights: report only, as ruled. A verdict grants nothing by itself; any later right is the operator's ruling.*

## What this registers

**One question.** Does a larger wealth-effect impulse come before faster real consumption growth? The order's item 66 calls the impulse the "loosening" leg of the rates-transmission cluster: equity gains reaching household spending.

## The definitions

**The impulse, month m** (the ledger's own measure, public sources only):
- **The share.** Z.1's households-and-nonprofits equities held directly and indirectly, as a percent of financial assets (FRED `BOGZ1FL153064486Q`, the public graph CSV, current vintage). FRED dates a quarter by its first day; its level is the quarter's end.
  - **Publication lag, as registered:** month m reads the latest quarter whose end is at least three full months before m's end. Z.1 is published about ten weeks after the quarter.
  - **No marking:** this ledger tests the Z.1 measure, not the stand-in the Monthly prints between releases.
- **The return.** SPX's year-on-year price return at m: Yahoo `^GSPC`, m's last close against the last close of the same month a year earlier.
- **The impulse** is the share (percent) times the return (percent), over 100: pp of household financial assets.

**The outcome, month m.** Real consumption growth over the next twelve months: BEA's real personal consumption expenditures, quantity index (FRED `DPCERA3M086SBEA`, monthly, current vintage), m+12 over m, in percent.

**The sample.** Every December from 1960 whose twelve forward months are published: one observation a year, non-overlapping.

## The test

- **The statistic:** Spearman's rank correlation, ρ, between the impulse and the outcome over the sample.
- **PASS** when all three hold:
  1. ρ ≥ 0.20 over the whole sample, with n ≥ 40;
  2. ρ > 0 in each half, split at the sample's median year (the earlier half takes the odd year);
  3. the median outcome of the impulse's top tercile exceeds that of its bottom tercile.
- **INSUFFICIENT** when n < 40.
- **FAIL** otherwise.

## How it prints

The ledger prints:
- its as-of, window, n, ρ over the whole sample and in each half;
- the terciles' median outcomes;
- the episodes as a CSV: each December's share, return, impulse and outcome.

The verdict prints as it is: INSUFFICIENT is a result.

## What this registration does not do

- **It grants nothing.** The impulse stays report-only whatever the verdict, and nothing enters a composite or the market-state object.
- **It claims no cause.** Equity returns and consumption both follow the business cycle, so a positive ρ is consistent with a common cause as well as a wealth effect. The ledger says so beside any verdict.
- **It reads current vintages.** No public source serves the first prints of all three series, and BEA's and Z.1's revisions are not undone. A box edition reads the same public sources.
- **It does not test the net-transmission line.** That line has no weights and is not scored.
