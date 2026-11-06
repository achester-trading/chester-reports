# close-flow ledger -- Item 116's levered-ETF close flow: the top decile by % of ADV, the last 30 minutes, the next open, +1 and +5

**Edition:** 2026-11-06, laptop run, public sources. A re-run against the box's store supersedes it (a new dated file).

**The pass rule is pre-registered** (ruled 17 Oct 2026): the rule the order states; where it states none, the rule the first (laptop) edition wrote is the registration. A box re-run may not change it, only apply it.

| | |
|---|---|
| As of | 2026-11-06 |
| Window | the close-flow history is the box's store's alone; a public run holds none (k = 0); the seeds' returns to 2026-11-06 |
| n | 0 |
| Statistic | per measure over the events: n, the mean, the median and the mean with the flow; the share of next-open gaps against the flow |
| Pass rule (as the order states it) | none stated -- the order names no pass rule; log-only until about 20 events (pre-registered: docs/ledgers/close-flow-preregistration-2026-11.md) |
| Verdict | **ACCRUING (n=0 of 20). NO GATE IN THE ORDER -- base rate recorded. The order names this study but states no pass rule; none is supplied here, by judgment or otherwise. A gate, if one is wanted, is the operator's to pre-register.** |
| Rights consequence | None: the ledger grants nothing. It enters no composite, flag table, the T&B intake queue or the market-state object, and changes neither the 15:00 flag nor the DTH-1 draft setup. |

## Sources and vintages

- the close-flow history: the box's store only (calc.close_flow.*, instrument 1645); a public run holds none
- daily opens and closes: Yahoo SMH, QQQ, SPY, IWM through the one yfinance import
- 5-minute bars: Yahoo, the last 60 days only
- read 2026-11-06T22:43:50+00:00

## Results

**Accruing (n=0 of 20).** 0 stored 16:45 session(s); below 20 no decile, and so no event, is defined. A public run holds no close-flow history: it is the box's store's alone, from the first live run (6 Nov 2026).

| Row | Session | Flow | % of ADV | Marked | Index | Last 30 min | Next open | +1 | +5 | SPY last 30 | SPY next open | SPY +1 | SPY +5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2026-06-05 | -$55.0bn | n/a | seed, order's figure | SPY | not available | +0.79% | +0.23% | +0.57% | not available | +0.79% | +0.23% | +0.57% |
| 2 | 2026-11-05 | -$52.0bn | n/a | seed, order's figure; estimate, unconfirmed (V-98a open) | SMH | -1.22% | +5.74% | +3.62% | pending | -0.28% | +0.25% | +0.31% | pending |

The seed rows' flows are the order's figures (MS's estimates), entered as judgment drafts for the operator's accept-all (rule 31). Every return comes from the series named under Sources; nothing else in a seed row is entered by hand.

## Caveats

- V-98a (the 5 Nov tally against MS's $52bn) is open: row 2 is an estimate, unconfirmed.
- The decile is recomputed at every edition, so a session can enter or leave the set as the history grows.
- SMH has no 5-minute bars in the store; a semiconductors-led event's last 30 minutes print 'not stored' (SPY's beside it).

The episodes are in `close-flow-ledger-2026-11-06-episodes.csv`, beside this file.
