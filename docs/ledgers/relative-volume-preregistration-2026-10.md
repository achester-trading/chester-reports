# The relative-volume ledger (OS-12c) — pre-registration (October 2026)

*Written and committed on 20 Oct 2026, before any of its scoring code, by session A on branch `a54-relative-volume`. **Never edited.** A change is a new registration in a new dated file. The spec is the signal-triage Batch 13 order (`docs/change-order-signal-triage-batch-13-2026-10-20.md`), item 61, OS-12c and decisions D3 and D5, ruled 20 Oct 2026.*

## The question

Does a spike in a name's total options volume, against its own recent history, lead movement in that name? This is report-only. It grants nothing and builds no composite.

## The name-days

- **The names:** the chain names whose closes are public (the 17 of `config.chain_universe()`), each scored against its own history. SPX and SPCX are in the flag but not in this ledger, because their closes are not in the public sample.
- **The volume:** the session's total options volume, calls and puts, from the session's last capture (the close's reading, `altdata/chain_metrics.name_readings`).
- **The ratio:** that volume over the mean of the 20 stored sessions before it. A name-day with fewer than 20 sessions before it is provisional and is not scored.
- **Flagged:** a ratio of at least 1.5, the flag's own threshold (D2). **Unflagged:** a ratio under 1.5.

## The measures

Each over the next 5 sessions, from the name-day's close:
- **The absolute move:** the absolute value of the close 5 sessions on over the close on the day, less 1, in percent.
- **The change in implied vol:** the front-month ATM IV 5 sessions on, less the day's, in points, by OS-10's method (`chain_metrics.front_month_iv`).

A name-day missing either close, or the IV at either end, is not scored on that measure and is counted.

## The comparison

The comparison is against the same name's unflagged days.
- For each flagged name-day, its **excess** is its measure less the mean of the same name's unflagged name-days over the whole sample.
- The statistic is the mean excess across flagged name-days, with a one-sample t.

## The samples

Two samples, read apart and never pooled:
1. **The captures:** our own chain captures, from the first session the box stored to the edition's date.
2. **The flat files:** the D5 backfill's daily volume from Massive's day aggregates, two years once it has run.
   - Its rows are read apart from the captured ones.
   - It is scored in its own edition, from the flat files themselves (the backfill's own reader), never through the observation store.

## The pass rule

The absolute move is the measure that decides; the change in implied vol prints beside it and decides nothing.

A sample's verdict:
- **INSUFFICIENT** under 30 scored flagged name-days, or under 30 scored unflagged name-days, or under 5 names with a scored flagged day.
- **PASS** when the mean excess absolute move is above zero with t at least 2.0.
- **FAIL** otherwise.

The first edition reads the captures sample only.

## Rights

**None until it passes.** A PASS reaches the register only as a rule-31 draft (for the operator's accept-all). The flag earns a place in any score only if this ledger supports it and the operator so rules. Either way, the flag stays report-only and prints "volume, no side".
