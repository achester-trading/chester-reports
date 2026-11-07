# event-vol ledger -- Item 119's event-vol pricing: the T-1 implied move against the realised T, T+1 and T+2 moves, by event type

**Edition:** 2026-11-06, laptop run, public sources. A re-run against the box's store supersedes it (a new dated file).

**The pass rule is pre-registered** (ruled 17 Oct 2026): the rule the order states; where it states none, the rule the first (laptop) edition wrote is the registration. A box re-run may not change it, only apply it.

| | |
|---|---|
| As of | 2026-11-06 |
| Window | from the ledger's first row to 2026-11-06 |
| n | 0 |
| Statistic | per type: the median headline realised move over the resolved rows, with n; the implied event move beside it |
| Pass rule (as the order states it) | none stated -- the order names no pass rule ("log-only until there are at least 20 events of each type"); this first edition sets none (pre-registered: docs/ledgers/event-vol-preregistration-2026-11.md) |
| Verdict | **NO GATE IN THE ORDER -- log-only until 20 events of a type** |
| Rights consequence | The Ahead line (the close and the Weekly) and the "cheap event vol" flag, in Ahead only; log-only until 20 resolved events of a type. Nothing enters a composite, a dial, the market-state object, a tell, a setup, a size or the register. |

## Sources and vintages

- store: event_vol.ledger -- none on the laptop (the box's EOD pass writes it)
- seed realised moves: Yahoo daily closes of SPY

## Results

The ledger is log-only: no type holds 20 resolved events, so no median is compared and no flag fires.

| Type | Resolved n | Median headline realised | Status |
|---|---|---|---|
| cpi | 0 | — | accruing (n=0 of 20) |
| earnings | 0 | — | accruing (n=0 of 20) |
| election | 0 | — | accruing (n=0 of 20) |
| fomc | 0 | — | accruing (n=0 of 20) |
| payrolls | 0 | — | accruing (n=0 of 20) |
| refunding | 0 | — | accruing (n=0 of 20) |

Rows (the store's ledger, then the seed rows, each marked):

| Event | Type | Day T | Implied (event) | Share | T | T+1 | T+2 | Headline | Tags | Marked |
|---|---|---|---|---|---|---|---|---|---|---|
| US midterm election, 3 Nov 2026 | election | 2026-11-04 | about 1.2% (order's figure) | — | +1.65% | -4.41% | pending | 1.65% | scheduled, political | seed, order's figure (V-101b) |

## Caveats

- The implied move is read from the T-1 capture at or before 16:35 ET; a session with no capture records "no chain".
- A seed row's implied move is the order's figure, never a chain read: it is printed and never compared or counted.
- Earnings dates are mostly stored without a time: those rows' headline realised move spans T and T+1.

The episodes are in `event-vol-ledger-2026-11-06-episodes.csv`, beside this file.
