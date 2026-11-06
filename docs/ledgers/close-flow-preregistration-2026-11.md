# Close-flow calibration ledger: pre-registration (November 2026)

**Item 116, the order's 98.2** (signal-triage Batch 22, `docs/change-order-signal-triage-batch-22-2026-11-05.md` on `b129-five-filings`). SR-77 is provisional. Ruled 5 Nov 2026 ("accept all", 23:24 ET), and built by A128 on 6 Nov 2026.

This file was committed before any of the ledger's code. Its SHA-256 is held by `tools/validate_item_116.py` and by `config/levered_etf.yaml` (`ledger.preregistration_sha256`). It is never edited: a change is a new dated file, with its own hash.

## The event

**The series.** The event is read from the box's stored 16:45 close-flow estimate (`altdata/close_flow.py`):
- `calc.close_flow.total_pct_adv`, instrument `1645`: the total in % of ADV;
- `calc.close_flow.total`, instrument `1645`: the total in dollars;
- the buckets' `calc.close_flow.<bucket>`, instrument `1645`.

**The event.** An event is a stored session whose |total in % of ADV| is in the **top decile** of the stored sessions.
- The cut is the 90th percentile of |`total_pct_adv`| over every stored 16:45 session up to the run's as-of. It interpolates linearly between order statistics (`altdata/ledgers` `quantile`).
- A session at or above the cut is an event.
- The cut is recomputed at every edition, so a session can enter or leave the set as the history grows. Each edition prints the cut it used.
- The flow's sign is recorded: positive is buying into the close, negative is selling.

**Below 20 stored sessions** the ledger prints "accruing (n=k of 20)" and defines no event. A decile of fewer than 20 sessions is not a decile.

**The bucket's index.** Each event is measured on the index ETF of the bucket with the largest |flow| among the four index buckets, beside SPY for every row:

| Bucket | ETF |
|---|---|
| Semiconductors | SMH |
| Nasdaq 100 | QQQ |
| S&P 500 | SPY |
| Russell 2000 | IWM |

The "other index and sector funds" and single-stock buckets count in the total. They are never the measured index.

## The measures

Each measure is computed for the bucket's index and for SPY, through the event-study utility (`altdata/event_study.py`; Batch 16 item 91(a)).

1. **The last-30-minute return.** The close of the last 5-minute bar of the session against the open of the bar 30 minutes before the close (15:30 to 16:00 ET; 12:30 to 13:00 on an early close), from the 5-minute bars. An instrument with no stored 5-minute bars prints "not stored". Today SMH has none; SPY, QQQ and IWM do.
2. **The gap at the next open.** The next session's opening price against the event session's close. The opening price is the first 5-minute bar's open in a store run, and Yahoo's daily open in a public run.
3. **The 1-day forward return.** The next session's close against the event session's close.
4. **The 5-day forward return.** The fifth session's close against the event session's close. A window that has not closed yet prints "pending".

Each measure is also printed signed by the flow (the return times the sign of the flow), so that "with the flow" and "against it" read the same way on buying and selling days.

## The statistic

For each measure, over the events:
- n;
- the mean and the median;
- the share of events whose gap at the next open runs against the flow (the reversal the DTH-1 draft setup describes, 98.3).

These are recorded, never judged.

## The pass rule

**None stated.** The order names no pass rule, so none is set here, by judgment or otherwise. The ledger is log-only until it holds about 20 events. A gate, if one is wanted, is the operator's to pre-register in a new file.

## The two seed rows

These are judgment drafts from the order's figures (rule 31: listed for the operator's accept-all). They are rows one and two. They are not stored sessions: they count toward neither the 20 nor the decile.

| Row | Session | Flow (the order's figure) | Marked |
|---|---|---|---|
| 1 | 5 Jun 2026 | −$55bn (MS's estimate; "the $55bn sold on 5 Jun 2026") | seed, order's figure |
| 2 | 5 Nov 2026 | −$52bn (MS's estimate at the 1pm prices) | seed, order's figure; estimate, unconfirmed (V-98a open) |

- **Each seed's index:** the order's largest named bucket. For 5 Nov 2026 that is semiconductors ($21bn), so SMH. Where the order gives no split (5 Jun 2026) the index is SPY.
- **No % of ADV is computed for a seed,** because the order's figure is in dollars.
- **The returns come from the same series as every other row.** Nothing in a seed row is entered by hand except the flow, its sign and its label.

## The sources

- **A store run (the box):** the keys above; `yfinance.mkt_smh`, `mkt_qqq`, `mkt_spy` and `mkt_iwm`; and the bars table's 5-minute SPY, QQQ and IWM bars.
- **A public run (the laptop's first edition):** the close-flow history exists only in the box's store, so a public run defines no event ("accruing (n=0 of 20)"). It computes the seeds' measures from Yahoo's daily closes and opens, and from Yahoo's 5-minute bars where Yahoo still serves them, which is the last 60 days. Otherwise the measure prints "not available".

## Rights

**None.** The ledger grants nothing:
- it enters no composite, flag table, the Top & Bottom intake queue or the market-state object;
- it changes neither the 15:00 flag nor the DTH-1 draft setup;
- it never opens the decision register and never writes the store.

`python -m altdata.ledgers run close-flow [--source public|store]` writes `docs/ledgers/close-flow-ledger-<date>.md` and its CSV.
