# High-beta / low-vol divergence ledger: pre-registration (November 2026)

**Item 118, the order's 100** (signal-triage Batch 22, `docs/change-order-signal-triage-batch-22-2026-11-05.md` on `b129-five-filings`). It amends the crowding family. Ruled 5 Nov 2026 ("accept all", 23:24 ET), and built by A128 on 6 Nov 2026.

This file was committed before any of the ledger's code. Its SHA-256 is held by `tools/validate_item_116.py` and by `config/crowding.yaml` (`hb_lv.ledger.preregistration_sha256`). It is never edited: a change is a new dated file, with its own hash.

## The series

- **The S&P 500:** the index's daily close (`yfinance.mkt_gspc`; Yahoo `^GSPC`).
- **SPHB and SPLV:** the daily closes of the Invesco S&P 500 High Beta ETF and Low Volatility ETF (`yfinance.mkt_sphb`, `yfinance.mkt_splv`). They are the ETF proxies for the two indices the order's chart reads, since StockCharts' SPHB:SPLV is a ratio of these ETFs.
- **The ratio:** SPHB's close over SPLV's close on the same session (`calc.hb_lv_ratio`). Its 1-day change, in percent, is the ratio against its previous session's value (`calc.hb_lv_ratio_chg_1d`).

## The event (the flag)

A session is an event when both of these hold:
- the S&P 500's close-to-close change is **+0.5% or more**;
- the ratio's 1-day change is **−2.0% or less**.

Every such session is an event. Sessions inside 20 sessions of a previous event are kept, and flagged in the CSV as overlapping, so their forward windows share days. The edition prints how many overlap.

## The measures

The S&P 500's forward returns after each event, close to close:
- the next session (+1);
- the fifth session (+5);
- the twentieth session (+20).

They run through the event-study utility (`altdata/event_study.py`; Batch 16 item 91(a)). A window that has not closed yet prints "pending" and is not counted.

## The statistic

For each horizon, over the events:
- n;
- the mean and the median;
- the share negative.

The same three figures are printed beside them over every session in the same window, as the base rate. These are recorded, never judged.

## The pass rule

**None stated.** The order names no pass rule ("the flag earns rights only after an event-study backtest"), so none is set here, by judgment or otherwise. The first edition is the backtest and sets no rule. A gate, if one is wanted, is the operator's to pre-register in a new file.

## The window

From SPHB's and SPLV's listing (5 May 2011, their first common session) to the run's as-of.

## The first row: 4 Nov 2026 (V-100a)

The order enters 4 Nov 2026 by hand as the first ledger row, subject to V-100a: the S&P 500 must have closed up at least 0.5% that day. The order already gives SPHB/SPLV as −2.7%.

- The ledger reads both conditions from its own series.
- It writes the 4 Nov row, marked "the order's day (V-100a checked)", only when both hold.
- If they do not hold, the row is not written and the edition says so.
- The row is the backtest's own event for that session, never a second copy.

## The sources

- **A store run (the box):** the three keys above.
- **A public run (the laptop's first edition):** Yahoo's daily closes for `^GSPC`, `SPHB` and `SPLV` through the one yfinance import (`altdata/ledgers/sources.py`).

## Rights

**None.** The flag prints in the close's "what doesn't fit" with "no rights until the backtest". This ledger is that backtest, and it grants nothing by itself:
- it enters no composite, flag table, the Top & Bottom intake queue or the market-state object;
- it never opens the decision register and never writes the store.

`python -m altdata.ledgers run hb-lv-divergence [--source public|store]` writes `docs/ledgers/hb-lv-divergence-ledger-<date>.md` and its CSV.
