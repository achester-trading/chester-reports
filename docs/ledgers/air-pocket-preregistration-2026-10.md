# The air pockets against the fragility panel -- pre-registration (ST-R6.71d, Batch 14 item 71)

*Written and committed on 23 Oct 2026, before any of its scoring code, by session A on branch `a57-batch14-b1`. **Never edited.** A change is a new registration in a new dated file; this one stays as written, and `tools/validate_batch14_b1.py` holds it to its SHA-256. The spec is signal-triage Batch 14 (`docs/change-order-signal-triage-batch-14-2026-10-20.md`), item 71 (written as 64), ruling 4: "A base-rate ledger on the air pockets of February 2018, August 2024 and April 2025, built from the free proxies." Rights: the fragility flag's are a flag's; "any T&B or Book C modifier comes only after the ledger." A verdict grants nothing by itself; any later right is the operator's ruling.*

## What this registers

**Two questions.**
1. Did the panel read fragile on the sessions before the three air pockets?
2. Across every session, is an SPY fall more frequent after the flag is on than after it is off?

## The definitions

**SPY's daily bars:** Yahoo's daily open, high, low, close and volume for SPY, unadjusted closes. The dollar volume is the close times the shares traded.

**The depth arm (the stand-in).** Depth is not tracked (check 8), so the arm reads SPY's Amihud measure as the stand-in:
- **each session's value:** the absolute log return, close to close, in basis points, per $1bn of dollar volume;
- **the measure:** the mean of the last 20 sessions' values, with at least 15 present;
- **the arm is on** when the measure's percentile is 90 or more. The percentile ranks the measure among its own values on the sessions within the five calendar years before it, the session itself included, counting values at or below it.

**The forced-flow arm, the leveraged-ETF estimate alone.** Dealer gamma has no history before 6b's store, so it is left out of this ledger and the arm is labelled.
- **Each session's estimate:** the sum, over ProShares' TQQQ (3), SQQQ (-3), QLD (2), UPRO (3), SPXU (-3), SSO (2) and SDS (-2), of:
  - the fund's assets under management on its last NAV date before the session, at most 5 calendar days before it;
  - times L x (L - 1);
  - times the index proxy's close-to-close return on the session (QQQ for the Nasdaq-100 funds, SPY for the S&P 500 funds).
- **The arm is on** when the estimate's absolute value has a percentile above 90, ranked as above.

**The flag** is on when both arms are on.

**The three air pockets.** In each of February 2018, August 2024 and April 2025, the first session whose SPY close-to-close fall is 2.5% or more. "The sessions before" are the five sessions before it.

**The base-rate outcome.** A session is followed by a fall when any of the next five sessions has an SPY close-to-close fall of 2.5% or more.

**The sample:**
- **from** 2 January 2015, so that every leveraged fund above has five years of history;
- **to** the last session with five sessions after it;
- **a session counts** when both arms can be read on it.

**The sources (laptop first edition):** the public sources.
- Yahoo daily bars for SPY and QQQ, through the project's one yfinance import;
- ProShares' keyless NAV history files, read by the writer's own parser.

The margin share is printed for each air pocket and does not enter the rule. It is FINRA's margin statistics workbook and FRED's `BOGZ1LM893064105Q`, as the panel computes it.

## The test

- **INSUFFICIENT** when fewer than 20 sessions in the sample have the flag on.
- **PASS** when both hold:
  1. the flag is on in at least one of the five sessions before at least two of the three air pockets;
  2. the share of flag-on sessions followed by a fall is at least twice the share of flag-off sessions followed by one.
- **FAIL** otherwise.

## How it prints

The ledger prints:
- **its as-of, window and n** (the sample's sessions; flag-on and flag-off, each with k);
- **for each air pocket:** the session; each of the five sessions before with the Amihud measure and its percentile, the estimate and its percentile, and the two arms and the flag; and the margin debt's share of market value in the latest month published before it, with the month;
- **for context, outside the rule:** the share followed by a fall after sessions whose 20-session realised volatility of SPY is at its own 90th percentile or above (ranked as above). It is printed because both arms rise with volatility, so part of any lift is volatility clustering;
- **the sessions** as a CSV.

The verdict prints as it is: INSUFFICIENT and FAIL are results.

## What this registration does not do

- **It grants nothing.** The flag keeps a flag's rights; no T&B or Book C modifier follows from a verdict without the operator's ruling. Nothing enters a composite or the market-state object.
- **It does not test depth.** The Amihud measure stands in for depth because depth is not tracked; a verdict is about the stand-in.
- **It leaves dealer gamma out.** It has no history before 6b's store. The live flag adds it where stored; this ledger does not.
- **Three pockets are not a sample.** Question 1 is a record of three readings. Question 2 is the base rate.
