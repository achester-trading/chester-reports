# The bank-stress base rate (ST-R6.59c) — pre-registration (October 2026)

*Written and committed on 20 Oct 2026, before any of its scoring code, by session A on branch `a52-doctrine-2-pack` (paste A53). **Never edited.** A change is a new registration in a new dated file. The spec is the signal-triage Batch 12 order (`docs/change-order-signal-triage-batch-12-2026-10-20.md`), item 59, ruling 5, with filing amendments F1–F6, ruled 20 Oct 2026.*

## The question

When bank equity falls more than 10% in 20 sessions, does the correction-vs-crisis classifier (`altdata/bank_stress.py`) tell the episodes that became banking stress (2007–08, March 2023) from the drawdowns that stayed corrections, and what followed each class for the S&P 500? Report-only: it grants nothing and builds no composite.

## The episodes

- **The equity leg:** KRE (SPDR S&P Regional Banking ETF), daily closes, from its first session in 2006. BKX is not used.
- **The trigger:** KRE's close against its close 20 sessions earlier at or below −10%.
- **One episode per cluster:** an episode starts on the first session the trigger holds and ends after 60 sessions in which it has not held again; a later trigger inside that run belongs to the same episode.
- **The named crises:** an episode whose start lies between 2007-07-01 and 2009-03-31, or between 2023-03-01 and 2023-05-31, is a crisis episode. Every other episode is a correction episode.

## The classification, point in time

Each episode is classified on its start session and on each of the 20 sessions after it, with each input read as it was knowable on that session:

- **The funding-stress flag:** any two of SOFR less IORB, the 90-day AA financial CP rate less the 3-month bill, the discount window's primary credit and FHLB advances above their 95th percentile over the five years before the session.
  - Where a member has no history yet, it is not read. SOFR starts in April 2018, so before 2018 at most three members can be read, and the flag still needs two.
  - FHLB advances (Z.1, quarterly) count from 75 days after their quarter-end, the Financial Accounts' lag.
  - IOER stands for IORB before 29 July 2021.
- **The deposit-flight flag:** small-bank H.8 deposits falling over 4 weeks while money-fund assets rise over the same 4 weeks.
  - **History:** FRED's weekly retail money-fund series (`WRMFNS`) stands in for ICI's total, labelled. ICI's file refuses an identified client.
  - **When weekly data counts:** a weekly series counts from the Friday after its reference week, the publication lag.
- **The state:** neither flag on is correction; one is funding watch; both are banking stress. Bank CDS and AT1 spreads are not tracked (F2).
- **An episode's class** is the most severe state it reaches between its start and 20 sessions after it.

## The outcomes

- **The S&P 500:** the forward 63- and 252-session return from the episode's start, from `^GSPC` closes, price only.
- **High yield:** the ICE BofA US high-yield OAS change over the same horizons, only where FRED serves the spread for the dates. FRED serves those spreads for recent years only, so the HY leg prints "not served" for any episode it cannot reach, and is counted as such.

## The pass rule

The classifier PASSES when all three hold:

1. **At least 8 episodes in all, and at least 2 crisis episodes.** Under that, the verdict is **INSUFFICIENT**.
2. **Every crisis episode** reaches funding watch or banking stress.
3. **At least two-thirds of the correction episodes** stay correction.

Otherwise it **FAILS**.

The forward S&P 500 returns by class are printed with each class's n and are not part of the pass rule.

## The samples

- **The first edition:** a laptop run from public sources only: FRED's keyless series (DCPF3M, DTB3, SOFR, IORB, IOER, WLCFLPCL, BOGZ1FL403069330Q, DPSSCBW027SBOG, WRMFNS and BAMLH0A0HYM2) and Yahoo's daily closes for KRE and `^GSPC`. It is labelled as such.
- **A box re-run** reads the box's store and supersedes the first edition in a new dated file. It may not change this rule, only apply it.

## Rights

**None until it passes.** A PASS reaches the register only as a rule-31 draft (for the operator's accept-all). Even then, the T&B overlay intake-queue entry (ST-R6.59d, the Liquidity & Funding Stress family) waits for "T&B full" and its place in the queue, one at a time, as the 25 Sep order rules. The flags and the classifier keep their report-only rights either way.
