# B75 — the gold spine, Tranche A (Batch 16 items 87, 88(a), (c), (d)): build notes

**Branch** `b75-gold-spine`, from `origin/chain-7-main` at
`dfa14a5433c32018c586b56fdf3c04d318e27492`. Code and config, branch-only; merges with
chain-8 on 2 Nov for the 8 Nov Weekly. The paste is `docs/pastes/B75.md`. The order
was read from the attached file (`change-order-signal-triage-round-7-2026-10-26.md`,
entries 80 and 81 and cross-item note 1). Its filed numbers 87 and 88 are cited
throughout. The filing itself (A78) is not on this base.

**S1 is not on this base.** So:

- the gold section is a row in `config/reporting_stack.yaml`'s section list, not a
  `config/stack_hooks/` file;
- the gates go into the Makefile's list (code gates carry no `GATE_KIND`);
- CLAUDE.md's count was recounted by hand: on this base, 143 code gates (140 Python,
  3 shell) and 8 data gates. B73, which is not on this base, adds two more. Whichever
  merges second recounts.

## The keys and lenses

| Lens | Input (stored key) | Reading | Status on the box's registry |
|---|---|---|---|
| Trigger | `yfinance.mkt_gold_front` (GC=F) | the 1- and 5-day log change as a z on the move screen's five-year window and population sigma; fires at \|z\| ≥ 2 (ruled), lead horizon = the larger | stored |
| Real yield | `fred.tips_10y` (DFII10) | change over the lead horizon, bp | stored |
| Breakeven | `fred.breakeven_10y` (T10YIE) | change, bp | stored |
| Dollar | `yfinance.mkt_dxy` (DX-Y.NYB, filed 73's leg) | change, % | stored |
| Liquidation | `yfinance.mkt_gspc` (^GSPC); `yfinance.mkt_qqq` for the Nasdaq-100 | 20-session correlation of daily log returns, and the day's signs | stored. **Gap:** the Nasdaq-100 itself (no ^NDX or NQ=F key; QQQ read and labelled) |
| (liquidation) squeeze flag | filed item 74 | — | **not stored**: `hf_positioning.squeeze` computes at read and stores no key |
| Official bid | `config/gold_official_bid.yaml` (the operator's dated records) + `imf.ifs.gold_net_purchases_oz.chn` | the latest record on or before the day; the PBoC's monthly net purchase in tonnes | records: **no record** (empty, the operator's); IFS: stored |
| 60-day beta | gold and DFII10 | OLS of gold's daily log return (%) on DFII10's daily change (bp), the last 60 paired sessions, n printed; absent below 40 | stored |

The Weekly block's other inputs:

- **GVZ:** **not stored**. There is no key, and D33 adds no symbol.
- **ETF holdings:** `etf.gld_shares`, `etf.gld_tonnes`, `etf.iau_shares`, `etf.iau_tonnes`.
- **Filed 72's line:** `sec13f.gold_etf_holders`.
- **CFTC managed money:** `cftc.dis_managed_money_net` @ GOLD.
- **The exhaustion tells:** `fred.brent` and `fred.yield_10y`.
- **The LBMA writer:** not read. It has been off the roster since 9 Oct (403).
- **New keys** (source `gold_attribution`, registered, barred from the object):
  `gold.attr.real_yield`, `.breakeven`, `.dollar`, `.liquidation`, `.official_bid`
  (JSON on a fired day) and `gold.beta_real_60d` (JSON each session). They are JSON
  bodies, so the move screen never reads them as a level.
- **One departure:** the paste says "2σ (the move screen's own σ and window)", but the
  move screen flags at 2.5σ. The trigger uses the screen's sigma estimate and
  window, at the order's threshold of 2 (`config/gold_attribution.yaml`
  `trigger.sigma`).

## The two ledgers

- **`docs/ledgers/gold-exhaustion-preregistration-2026-10.md`**, never edited.
  SHA-256 over its LF bytes: `7883f4554bfa4fc463f96d3ca9d7afeacf2c0d7bcd3ffce4eac15b01ca133ade`,
  held by `tools/validate_weekly_gold_block.py`.
  - **Pass rule** (the order states none, so this is the first edition's): per tell,
    the mean +20-session gold return after a ticked week less after a clear week, by
    Welch t.
  - **INSUFFICIENT** under 30 weeks on either side; **PASS** at t ≥ 2.0; **FAIL**
    otherwise.
  - The +5 and +60 sessions print beside the +20 and decide nothing.
  - **Rights:** none.
- **`docs/ledgers/gold-exhaustion-ledger-2026-10-26.md`**, the first edition.
  - It was computed from this worktree's laptop store, which holds no gold front, so
    every tell is at 0 weeks, INSUFFICIENT.
  - It cites the hash above.
  - The box's edition is a box command (below).

## Where it prints

- **The daily close (88(d)):** `daily_cascade/stack.py` calls
  `gold_block.close_extras` after the gold event's lines. One sub-section, "Gold on
  exception", appears in Mechanics only on a 2σ day (the move and the five lenses in
  one line) or a session where an exhaustion tell flipped. Otherwise nothing.
  `stack_close.py` stores the session's beta row and a fired day's lens rows, never
  on a dry run.
- **The Weekly (88(a)):** the section `gold` (weekly depth deep, so 420 words; the
  stack's commentary path writes it, with its own note in `stack_prose.WEEKLY_NOTES`).
  - The 1 Nov Weekly prints the header and "First edition 8 Nov." with no prose and
    no chart.
  - Its content:
    - the tape table;
    - the attribution (the week's newest 2σ day in full, the others by date) and the
      beta;
    - positioning and flows at 1 week, 3 months and 12 months;
    - the official bid;
    - "Sell-side targets: not yet built (Tranche B).";
    - the checklist with its ledger's path;
    - GLD's dealer levels;
    - the block's own Ahead line, ranked from the calendar's rows by release class
      and importance tier.
- **The chart:** W13 (gold's close over two years, its 200-day, the record marked)
  joins the plan after W3, **inside** the ruled cap of 10, so the plan's last chart
  (W10, by default) is set aside on a gold week.
- **Fixture render:** about 11,000 characters of HTML through `stack_render.section_html`,
  and 684 words of lines and cells before prose (the lines and tables count no words
  in the budget).

## GLD in the exposure files (88(c))

- **The exception:** `config/exposure_universe.yaml` declares the hold (13, ruled 19
  Oct; the review in December) and the one exception, GLD. Its ruling is quoted and
  its Security Master id is **SM00022** (SPDR Gold Shares).
- **How it is read:** `config.exposure_exceptions()` reads that file and returns only
  a symbol with a ruling that is already captured (GLD is one of the paper bid's
  four) and not already held. `run_eod.py` Stage 2 computes it beside the 13.
- **What it gets:** its own exposure file under the engine's existing names (GEX,
  DEX, the walls, the flip), and its readings in the store through Stage 2b.
- **What it does not get:** the pin log and the completeness gate still take the 13.
- **The vendor line:** FlashAlpha's plan (`config/flashalpha.yaml`) does not serve
  GLD, so the vendor-comparison line says "not served".

## Gates

- `tools/validate_gold_attribution.py` (41 checks): the trigger by hand, the five
  lenses, the beta, the tells, the close on exception (a quiet day prints nothing, a
  2σ day the line), and the rows.
- `tools/validate_weekly_gold_block.py` (31 checks): placement, "not stored" on an
  empty store, the fixture block by hand, the first edition, the ledger hash, W13
  inside the cap, and the prose path.
- `tools/validate_gld_exposure.py` (17 checks): the hold stands, the exception is in
  config and not in code, the engine's fields, the Weekly's levels line, and the pin
  log and completeness gate keeping the 13.

## Box commands (for chain-8's box sheet)

    cd ~/chester-reports
    .venv/bin/python -m altdata.gold_attribution backfill --dry-run          # counts, writes nothing
    .venv/bin/python -m altdata.gold_attribution backfill --since 2021-01-01 # then writes (beta each session, lenses on fired days)
    .venv/bin/python -m altdata.gold_attribution show
    .venv/bin/python -m altdata.gold_attribution ledger --out docs/ledgers/gold-exhaustion-ledger-<date>.md
    # GLD's first capture: the next 16:10 EOD pass computes it (no new unit). Check:
    ls ~/chester-reports/data/computed/<session>/GLD_*_exposure.json

## Needs you

1. **Official-bid records:** the file is empty. The first record you enter (date,
   source, figure, outlet, url) is what the 8 Nov block prints.
2. **The chart cap:** W13 counts inside the ruled 10, so a gold week sets W10 aside.
   Say if you want the cap raised to 11 instead.
3. **The Nasdaq-100 leg:** it reads QQQ because no index key is stored. Accept that,
   or order an index source.
4. **The 2σ reading:** it uses the move screen's sigma at the order's 2, not the
   screen's own 2.5. Confirm.

- **Local runs:** the three new gates, check_registry, check_library, validate_audit_3a, validate_gates, check_master_guide, validate_figure_budget, validate_dealer_block, validate_daily_close, validate_weekly_complete, validate_weekly_edits and validate_st_r5_index pass. validate_monthly_stack failed once, on the registry sweep (gold.attr.* typed count); that is fixed (typed label), but its rerun and a wider Weekly batch were stopped by the laptop running low on memory, so CI is their check.
- **CI:** queued at `ac353f9`; the run id is in the report. The next paste on this branch reads the result once.

## Ruled (26 Oct 2026)

1. Official bid: the file stays empty; the 8 Nov block prints "no record yet"; the operator supplies the first dated record before 8 Nov.
2. The chart cap is 11 (`403454e`): W13 never sets another chart aside; the words stay 7,900.
3. The Nasdaq-100 leg through QQQ: accepted.
4. 2σ, as the order says: accepted.

- **CI round 2:** runs 40352607527 and 40377224688 failed on three gates the laptop had not run: validate_lenses (gold.attr.* had no family or exclusion; gold.beta_real_60d no family), validate_weekly_stack (expected ten sections; Gold is the eleventh) and validate_quarterly_stack (the Weekly-only gold section has no quarterly depth). Fixed in `64c5a51`. Locally all three pass, as do validate_monthly_stack, validate_audit_3a, check_registry, validate_weekly_complete, validate_weekly_edits, validate_stack_cadence and validate_weekly_gold_block. CI queued, run 40379206540.
