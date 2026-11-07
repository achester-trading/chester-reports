# Pre-registration: ST-R6.74b, leveraged funds' extreme net shorts in ES and the S&P 500 after

*Signal-triage Batch 15, item 74 (written as 67), part 3: "a base-rate ledger of
prior extreme short readings and their 5- and 20-day outcomes". Written 23 Oct
2026 by session B before any scoring code, and committed alone. This file is never
edited; its SHA-256 over the LF bytes is held by `tools/validate_batch15_2.py`
and printed at the head of every edition. A change to the rule is a new
pre-registration under a new name.*

## The question

When leveraged funds' net short in the E-mini S&P 500 future is at an extreme of
its own recent history, does the S&P 500 rise over the next 20 sessions by more
than it does after an ordinary week? That is the squeeze case: crowded shorts are
bought back into a rebound. The ledger asks only that. It grants no right.

## The data (stored history only)

- **Positioning:** the CFTC's Traders in Financial Futures report, futures only,
  contract 13874A (the E-mini S&P 500), the leveraged-funds category's net
  position as a share of open interest: `cftc.tff_lev_money_net_oi`, instrument
  `ES`, as the store holds it (`altdata/sources/cftc.py`). Weekly, the report
  Tuesday, from 13 Jun 2006.
- **Outcome:** the S&P 500's daily close, `yfinance.mkt_gspc`, as stored.
- **The store is opened read-only.** Nothing is fetched.

## The rule

1. **The short reading.** For each report week t, the net short share is the
   negative of the stored net share of open interest.
2. **Extreme.** Week t is extreme when its net short share is at or above the
   90th percentile of the same series over the 260 reports ending at week t (five
   years, week t included), as stored. A week with fewer than 156 reports behind
   it (three years) is not ranked.
3. **An episode** begins at an extreme week preceded by at least four consecutive
   ranked weeks that were not extreme. Only that first week counts.
4. **Entry.** The first stored S&P 500 close on or after the report's release day,
   the Friday after the report Tuesday (the CFTC's 15:30 ET release; the close
   that day is after it). No week is entered before the market could know it.
5. **Outcomes.** The percent change of the S&P 500 close from the entry to the
   close 5 sessions later and 20 sessions later. An episode without its 20th
   session stored is pending and not counted.
6. **The baseline.** The same two outcomes from every ranked report week's entry
   in the same sample, episodes included.

## The pass rule

- **INSUFFICIENT** with fewer than 12 counted episodes.
- **PASS** when both hold:
  - the median 20-session outcome after the episodes exceeds the baseline's
    median 20-session outcome by at least 1.0 percentage point; and
  - at least 60% of the episodes have a positive 20-session outcome.
- **FAIL** otherwise.

The 5-session outcome is reported beside the rule and is not part of it.

## What each edition prints

Its as-of, the store it read, the window (first and last report week ranked),
n (episodes counted and pending), the two medians and the share positive, the
baseline's medians, this file's SHA-256, the verdict under the rule above, and
the episodes as a CSV beside it (report week, release day, entry day, the net
short share and its percentile, the two outcomes).

## Rights

None. The verdict is a rule-31 draft for the operator's accept-all. Item 74's
squeeze-risk flag keeps a flag's rights whatever the verdict; any T&B or Book
modifier is a later ruling.
