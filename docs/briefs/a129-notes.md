# A129 notes: item 119 (the event-vol pricing ledger) with item 124f

Paste A129, 6 Nov 2026, session A. Branch `a129-item-119-event-vol` from `origin/main` at `ee04ba21`, which includes b114-names-sweep's merge (PR #52). The paste is `b49c29c4`; the pre-registration is `ac1522c6`, committed before any code. Merges Monday in chain-13.

## Orders

- **Batch 22 item 119** (the body's 101): `docs/change-order-signal-triage-batch-22-2026-11-05.md`.
- **Batch 23 item 124f** (the body's 106f) with D-2, and section 0's Q3 (the T, T+1, T+2 window from the start): `docs/change-order-signal-triage-batch-23-2026-11-06.md`.

Both are on `origin/b129-five-filings`. The seed dates are the study's: `docs/studies/tail-days-study-2026-11-05.md` section 1 and `tail-days-2016-2026-data.md` Part 5, on branch `study/tail-days`.

## The pre-registration

`docs/ledgers/event-vol-preregistration-2026-11.md`, SHA-256 (LF bytes) `639d142c2d794c7e0e4552971c6a5de38bd61d4ecb2d5820357a059d33329e70`. Held by `config/event_vol.yaml` (`preregistration_sha256`) and `tools/validate_item_119.py` group A.

- **The events:** six types. FOMC, CPI, payrolls, refunding and elections read SPY. Earnings covers the 13's ten single names, each its own type `earnings:<SYM>`.
- **Day T:** the first session whose close follows the event. A date-only earnings row keeps T on its date, and its headline realised move spans T and T+1.
- **The implied move** comes from the T−1 capture at or before 16:35 ET:
  - the straddle is taken to the first expiry after the event, by Ahead's own `straddle_expiry` rule;
  - the event day's share of variance comes from item 57's pre-event rate, else from the two post-event expiries, else "not separable".
- **The realised moves:** T, T+1 and T+2, signed, plus the headline.
- **The tags:** two, nullable.
- **The rule:** median by type, log-only to 20; no pass rule ("none stated"); the flag in Ahead only.

## What was built

| Piece | Where |
|---|---|
| The ledger, its EOD step, Ahead's annotation, V-101a's check, the edition | `altdata/event_vol.py`, `config/event_vol.yaml` |
| The EOD pass's step (after the vol-event resolve; warn-only) | `scripts/run_eod_cron.sh` |
| The Weekly's Ahead: the event-vol clause in the consensus cell, the flag's footnote | `daily_cascade/ahead.py` `build()` |
| The close's Ahead: the same clause on each typed event's line | `daily_cascade/stack.py` `ahead_section()` |
| 124f on item 52's ledger: `scheduled` and `catalyst_class` on every new row (NULL until set), `tag_faults`, `seed_rows`, `seed-tags [--dry-run]`; seeds never count | `altdata/vol_event.py` |
| The midterm ledger's 2026 row, beside the sample | `tools/calibration/midterm_base_rate.py` (`row_in_progress`, `in_progress_clause`), `docs/ledgers/midterm-base-rate-2026-11-06.md` |
| The headline copied into config | `config/weekly_ahead.yaml` `register_event_rows` (ledger 2026-11-06) |
| Registry | `metrics_registry.yaml` (`event_vol.ledger`, label units, lens-excluded, barred from the market-state object); `source_registry.yaml` (`event_vol`) |
| Catalogue | `config/catalogue_commands.yaml` `altdata.event_vol` |
| First edition | `docs/ledgers/event-vol-ledger-2026-11-06.md` and its episodes CSV |
| Gate | `tools/validate_item_119.py`, 41/0; `tools/validate_batch16_midterm.py` gains group E (36/0) |

**Reuse, not a second reader.** The straddle, the expiry rule and item 57's event-only move are Ahead's (`daily_cascade/ahead.py`). `event_vol` calls them, and adds the cutoff on the capture and the two-post-expiry split.

One rule in item 57's existing earnings code is not changed here. Its pre-event expiry may be the event date's own expiry even when the report lands before the open, which would subtract event variance. The ledger's own rule refuses such an expiry (it must settle before the event). Item 57's reader is left as it is, and listed for the operator.

## V-101a: is the T−1 ATM straddle readable?

Checked on the laptop's captures (the newest: 4 and 5 Sep 2026; the box's captures are the ledger's), with `python -m altdata.event_vol check-chains`:

| Name | Capture | Expiry read | Result |
|---|---|---|---|
| SPX | 2026-09-05 (vendor, Massive) | 2026-09-09 | **not readable**: the vendor capture carries last prices only, no bid or ask, so no mid |
| SPY | 2026-09-04 | 2026-09-09 | readable: straddle 5.05 on 770.24 (0.66%) |
| QQQ | 2026-09-04 | 2026-09-09 | readable: 7.09 on 718.96 (0.99%) |
| IWM | 2026-09-04 | 2026-09-09 | readable: 2.72 on 295.97 (0.92%) |
| NVDA | 2026-09-04 | 2026-09-09 | readable: 5.55 on 230.36 (2.41%) |
| AAPL | 2026-09-04 | 2026-09-09 | readable: 7.73 on 319.97 (2.41%) |
| MSFT | 2026-09-04 | 2026-09-09 | readable: 8.57 on 499.70 (1.72%) |
| AMZN | 2026-09-04 | 2026-09-09 | readable: 5.40 on 258.51 (2.09%) |
| META | 2026-09-04 | 2026-09-09 | readable: 15.68 on 616.77 (2.54%) |
| GOOGL | 2026-09-04 | 2026-09-09 | readable: 6.50 on 338.46 (1.92%) |
| TSLA | 2026-09-04 | 2026-09-09 | readable: 10.80 on 354.08 (3.05%) |
| MSTR | 2026-09-04 | 2026-09-11 | readable: 11.15 on 142.80 (7.81%) |
| COIN | 2026-09-04 | 2026-09-11 | readable: 11.97 on 184.64 (6.49%) |
| ASTS | 2026-09-04 | 2026-09-11 | readable: 4.30 on 62.31 (6.90%) |

**V-101a holds on SPY**, the paste's "SPX or SPY", and on all 13. SPX's vendor chain is not usable for a straddle until its tier carries quotes, so the macro events are recorded on SPY. The box's own check is `check-chains --date <today>`, read-only (box steps).

The 13 are captured by the yfinance chain fetcher, not Massive. The price migration retires yfinance between 22 Dec and 8 Jan. Whatever replaces the chain capture must keep bid and ask, or this ledger's implied side stops ("no chain").

## V-101b and the 2026 midterm row

- **The midterm ledger's new edition**, `midterm-base-rate-2026-11-06.md`, is a laptop run on the laptop's store, which ends 21 Sep 2026.
- **Its computation is unchanged:** `8c8fa32c…`, nineteen completed years.
- **The 2026 row prints beside the sample:**
  - the drawdown to date is −9.1% through 21 Sep (27 Jan → 30 Mar);
  - the election-day close and the two sessions after are "not stored";
  - the implied move is "about 1.2% (order's figure)".
- **The headline** carries the row only once both post-election sessions are stored. This edition's headline is the 28 Oct one with its edition date changed, and that is what `config/weekly_ahead.yaml` now copies. The box's re-run writes a new edition whose headline carries the 2026 clause, and the session that files it copies that in.
- **The realised moves from public closes,** in the event-vol ledger's first edition (seed row, SPY): 4 Nov **+1.65%**, 5 Nov **−4.41%**, 6 Nov pending (Yahoo's bar not yet in). The S&P 500 itself moved +1.58% and −4.36% (A128's V-100a read, and the order).

## The event-vol ledger's first edition

`docs/ledgers/event-vol-ledger-2026-11-06.md`: n 0, log-only, "none stated", every type "accruing (n=0 of 20)". Its one row is the 2026 midterm seed:
- T = 4 Nov, because the results land after the close;
- the implied move is the order's figure, printed and never compared;
- the realised moves are from Yahoo's SPY: +1.65% and −4.41%, the third session pending, headline 1.65%;
- the tags are scheduled and political.

The store's ledger starts with the box's first EOD step after the merge.

## The seed rows (124f; judgment drafts for the operator's accept-all, rule 31)

There are 26 rows in `config/event_vol.yaml` `seeds`, each `status: draft`:
- the twenty Morningstar days (ten worst, ten best);
- 27 Feb 2020;
- the six calm-surface openers.

5 Nov 2026 is both a Morningstar day and an opener, so it is one row naming both sets. The five earlier openers' catalysts are the study's own, from memory, and are marked "draft (V-106h)". The classes are this session's drafts:

| Day | Sets | Scheduled | Class |
|---|---|---|---|
| 2018-12-26 | Morningstar best | unscheduled | positioning unwind |
| 2020-02-24 | opener | unscheduled | exogenous (V-106h) |
| 2020-02-27 | the S&P's ninth-worst | unscheduled | exogenous |
| 2020-03-02, 03-10, 03-13, 03-17, 03-24, 03-26 | Morningstar best | unscheduled | policy response |
| 2020-04-06 | Morningstar best | unscheduled | exogenous |
| 2020-03-09, 03-11, 03-12, 03-16, 03-18, 04-01 | Morningstar worst | unscheduled | exogenous |
| 2020-06-11 | Morningstar worst | unscheduled | positioning unwind |
| 2022-11-10 | Morningstar best | scheduled | data print |
| 2025-04-03 | Morningstar worst | scheduled | policy shock |
| 2025-04-04 | Morningstar worst | unscheduled | policy shock |
| 2025-04-09 | Morningstar best | unscheduled | policy response |
| 2026-11-05 | Morningstar worst and opener | unscheduled | political |
| 1991-11-15 | opener | unscheduled | political (V-106h) |
| 2007-02-27 | opener | unscheduled | exogenous (V-106h) |
| 2016-06-24 | opener | scheduled | political (V-106h) |
| 2018-10-10 | opener | unscheduled | positioning unwind (V-106h) |

`seed-tags` writes only days the ledger does not already hold. If item 52 fired on 5 Nov 2026, that fired row stays as it is, untouched, and the operator tags it.

## Gates (one at a time, foreground)

| Gate | Result |
|---|---|
| validate_item_119 | 41/0 |
| validate_vol_event | 50/0 |
| validate_batch16_midterm | 36/0 (group E added) |
| validate_weekly_calendar (the Ahead gate as the Makefile names it) | 44/0 |
| validate_ledgers_b6 | 41/0 |
| check_registry | OK |
| validate_gates | 32/0 |
| check_library | 27 papers, 0 failures, 0 warnings (after rebuilding the Master Guide's HTML) |

Also run, all clean:
- validate_audit_3a 88/0, validate_outliers 37/0, validate_config_refs 148/0, validate_numeral_audit 181/0;
- validate_stack 84/0, validate_weekly_stack 83/0;
- validate_deploy 155/0 (the EOD wrapper), validate_names 20/0;
- validate_opening_setup 61/0, validate_weekly_complete 96/0, validate_prices 101/0;
- validate_security_master 102/0, validate_secrets 58/0;
- check_master_guide 0 failures (Table 7a lists the three new ledger files);
- validate_ai_fcf 27/0 (with UTF-8 output: the laptop console's cp1252 cannot print its minus sign, a local artefact).

The full suite (`bash scripts/make.sh validate`) did not finish inside ten minutes on the laptop. 27 gates had passed when it stopped, and CI runs the whole list.

**Counts** (`stitch_counts.py --write`): 168 code gates (165 Python, 3 shell), 8 data gates.

## Box steps (the operator's)

1. After chain-13's merge, the EOD pass records and resolves the ledger on its own (`event_vol eod`, warn-only). To see it first:
   - `python -m altdata.event_vol eod --dry-run`;
   - `python -m altdata.event_vol check-chains` (V-101a on the box's captures; read-only).
2. The seed rows: `python -m altdata.vol_event seed-tags --dry-run`, then without `--dry-run`, after the accept-all.
3. The midterm ledger's box edition:
   - run `python tools/calibration/midterm_base_rate.py --box --date <D>`;
   - its 2026 row and headline clause fill from the box's store;
   - the next session copies the headline into `config/weekly_ahead.yaml`.
4. The event-vol ledger's box edition: `python -m altdata.event_vol edition --source store --date <D>`.

## For the operator

- **Accept-all (rule 31):** the 26 seed rows' classes, and the default class per type (fomc policy response, cpi and payrolls data print, refunding policy shock, election political, earnings earnings).
- **Item 57's pre-event expiry,** above: left unchanged.
- **The A128 branch's correction.** Its CI run 42307899426 failed two gates A128's list did not name, check_master_guide and validate_prices. Both were fixed in `d3847cb7` on `a127-item-116-close-flow` and pushed before this paste began. That branch's check_library prints one warning, the Master Guide's HTML edition being older than its Markdown; it is a warning only, and chain-13's stitch rebuilds the HTML.
