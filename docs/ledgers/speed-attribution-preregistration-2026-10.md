# The 10-year speed flag's attribution against what followed -- pre-registration (ST-R6.65a, Batch 14 item 65)

*Written and committed on 23 Oct 2026, before any of its scoring code, by session A on branch `a57-batch14-b1`. **Never edited.** A change is a new registration in a new dated file; this one stays as written, and `tools/validate_batch14_b1.py` holds it to its SHA-256. The spec is signal-triage Batch 14 (`docs/change-order-signal-triage-batch-14-2026-10-20.md`), item 65 (written as 58), ruling 1: "Run the 10-year attribution automatically on speed-flag days, with its own event ledger (the item-52 pattern applied to rates)." Rights: none new. The speed flag's existing rights stand and the attribution is a report (F5). A verdict grants nothing by itself; any later right is the operator's ruling.*

## What this registers

**One question.** When the 10-year's speed flag fires, does the leg that carried the move -- expected short rates or the term premium, as the term-structure models split it -- tell us whether the move continues over the next 20 sessions?

The live ledger (`rates.speed_event_ledger`, written by the close) accrues from the first flag after this branch merges. This registration fixes how that ledger, and its laptop first edition from public history, are scored.

## The definitions

**The flag (SR-35, as `config/move_screen.yaml` states it on 23 Oct 2026).** On a Treasury session D, the 10-year's 10-session and 21-session changes, in basis points, each as a z:
- the change ending on D, less the mean of the same horizon's changes ending on the sessions before D whose start falls within 7,305 calendar days before D, over their population standard deviation;
- at least 30 observations of the yield up to D.

The flag fires on D when either |z| is 2.0 or more. Its **lead horizon** is the one with the larger |z|.

**An episode** is a flag day with no flag day in the 21 sessions before it: the first day of a run.

**The attribution** (as `altdata/speed_attribution.py` computes it):
- **The move:** the 10-year's change over the lead horizon to D, in basis points.
- **Each model:** its 10-year term premium's change over the same sessions, read only when the model has an observation on D (F5), and its start is the model's observation on or before the start session, at most 4 calendar days before it.
- **The premium share** is the model's term-premium change over the move. The model says the term premium carried the move above one half, expected short rates below one half.
- **The episode's leg** is the leg on which every model read agrees. When they disagree the episode is "disagree"; when none is read, "unread".
- **The models:** KW (the Federal Reserve Board's three-factor model, FRED `THREEFYTP10`) and ACM (the New York Fed's, `ACMTP10` of its daily workbook). DKW splits the real yield and is not read.

**The outcome.** The 10-year's change from D to the 20th session after it. The move **continued** when that change is non-zero and has the move's sign. The 5-session change is printed beside it and does not enter the rule.

**The sample.** Every episode from 2 January 1990, when the KW series begins, to the last D with 20 sessions after it.

**The sources (laptop first edition):** the public sources, current vintages.
- FRED's graph CSV for `DGS10` and `THREEFYTP10`;
- the New York Fed's ACM workbook, read by the writer's own parser.

## The test

- **The statistic:** the continuation share of the episodes the term premium carried, against that of the episodes expected short rates carried.
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
- the episodes as a CSV: the day, the lead horizon and z, the move, each model's premium share and leg, the episode's leg, the 5- and 20-session outcomes.

The verdict prints as it is: INSUFFICIENT and FAIL are results.

## What this registration does not do

- **It grants nothing.** The speed flag keeps its rights; the attribution stays a report whatever the verdict. Nothing enters a composite or the market-state object.
- **It reads current vintages.** Both models are re-estimated as they go, so a historical premium share is not the one a reader saw on the day; the live ledger, which records each day's own read, is what removes that.
- **It claims no cause.** A share is a model's decomposition of one market's prices, and the two models are two decompositions of the same yields, not independent witnesses.
