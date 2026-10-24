# The one-day 10-year trigger's attribution against what followed -- pre-registration (D15)

*Written and committed on 24 Oct 2026, before any of its scoring code, by session B on branch `b59-trigger-sources`. **Never edited.** A change is a new registration in a new dated file; this one stays as written, and `tools/validate_b59.py` holds it to its SHA-256. The spec is the rulings of 24 Oct 2026, D15: "one-day 10y move trigger (|d10y| beyond five-year 97.5th pct, two-sided) runs the attribution; own pre-registered ledger; report-only". It follows the shape of the speed flag's registration (`docs/ledgers/speed-attribution-preregistration-2026-10.md`, ST-R6.65a). Rights: none. The trigger is a report; a verdict grants nothing by itself, and any later right is the operator's ruling.*

## What this registers

**One question.** When the 10-year moves further in one session than its five-year 97.5th percentile of one-day moves, does the leg that carried the move -- expected short rates or the term premium, as the term-structure models split it -- tell us whether the move continues over the next 5 sessions?

The live ledger (`rates.oneday_event_ledger`, written by the close) accrues from the first trigger after this branch merges. This registration fixes how that ledger, and its laptop first edition from public history, are scored.

## The definitions

**The trigger.** On a Treasury session D (a day with a stored 10-year observation, FRED `DGS10`):
- **the one-day change** is the 10-year on D less the 10-year on the stored observation before D, in basis points;
- **the window** is the absolute one-day changes ending on the stored days before D and after the same calendar day five years before D;
- **the threshold** is the window's 97.5th percentile, by linear interpolation (`altdata/derived.percentile_at`);
- the window must hold **at least 1,000 changes**, else the trigger is not read on D.

The trigger **fires** on D when the absolute one-day change is greater than the threshold, on either sign.

**An episode** is a trigger day with no trigger day in the 5 sessions before it: the first day of a cluster.

**The attribution** (as `altdata/speed_attribution.attribute` computes it, over one session):
- **The move:** the 10-year's change from the session before D to D, in basis points.
- **Each model:** its 10-year term premium's change over the same session, read only when the model has an observation on D (F5 of the speed flag's ruling), and its start is the model's observation on or before the session before D, at most 4 calendar days before it.
- **The premium share** is the model's term-premium change over the move. The model says the term premium carried the move above one half, expected short rates below one half.
- **The episode's leg** is the leg on which every model read agrees. When they disagree the episode is "disagree"; when none is read, "unread".
- **The models:** KW (the Federal Reserve Board's three-factor model, FRED `THREEFYTP10`) and ACM (the New York Fed's, `ACMTP10` of its daily workbook). DKW splits the real yield and is not read.

**The outcome.** The 10-year's change from D to the 5th session after it. The move **continued** when that change is non-zero and has the move's sign. The 20-session change is printed beside it and does not enter the rule.

**The sample.** Every episode from 2 January 1990, when the KW series begins, to the last D with 20 sessions after it.

**The sources (laptop first edition):** the public sources, current vintages.
- FRED's graph CSV for `DGS10` and `THREEFYTP10`;
- the New York Fed's ACM workbook, read by the writer's own parser.

## The test

- **The statistic:** the 5-session continuation share of the episodes the term premium carried, against that of the episodes expected short rates carried.
- **PASS** when all three hold:
  1. each group holds at least 15 episodes;
  2. the two shares differ by at least 0.15;
  3. the difference has the same sign in each half of the sample. The halves are split at the median episode date, the earlier half taking the odd episode, and a half where either group is empty fails this condition.
- **INSUFFICIENT** when either group holds fewer than 15 episodes.
- **FAIL** otherwise.

## How it prints

The ledger prints:
- its as-of, window and n (the episodes in the two groups);
- each group's continuation share and k, and each half's difference;
- the counts of "disagree" and "unread" episodes;
- the episodes as a CSV: the day, the one-day move and its threshold, each model's premium share and leg, the episode's leg, the 5- and 20-session outcomes.

The verdict prints as it is: INSUFFICIENT and FAIL are results. It reaches the register only as a rule-31 draft.

## What this registration does not do

- **It grants nothing.** The trigger is a report whatever the verdict. Nothing enters a composite or the market-state object.
- **It reads current vintages.** Both models are re-estimated as they go, so a historical premium share is not the one a reader saw on the day; the live ledger, which records each day's own read, is what removes that.
- **It claims no cause.** A share is a model's decomposition of one market's prices, and the two models are two decompositions of the same yields, not independent witnesses.
- **It is not the speed flag.** SR-35's flag and its ledger (ST-R6.65a) stand as they are; a day may fire both, and each ledger scores its own episodes.
