# digital-49-51b: the addendum's Phase 2 panels and item 49's series (17 Oct 2026)

**Branch and merge order.** `digital-49-51b`, session B, cut from the tip of
`crypto-tranche-a-2` (`a4d8390`), with its CI fix (`7e55cda`) merged in. It carries
Tranche A (parts 1 and 2) and the 6e line, and **merges after `crypto-tranche-a-2`,
in the second stitched chain.**

**What it builds** (Batch 8, `docs/change-order-signal-triage-batch-8-2026-10-17.md`):
- **ST-R6.51b,** the Digital Assets addendum's Phase 2 panels;
- **ST-R6.49a,** mNAV;
- **ST-R6.49b,** treasury net purchases.

**Rules kept.**
- Branch only: pushed, not merged, not deployed, nothing on the box.
- Paper only, with no order path. The Book D template, the obligations schedule
  (49.3) and the event preparation (49.7) are yours, by hand, and untouched.
- No key, no secret, no real position figure.
- Not touched: `.env`, the units on the box, the register, the trade ledgers,
  `chester-meme`, session A's branches.

## Step 0: the CI read

| Run | Branch, commit | Result |
|---|---|---|
| 39037767039 | `crypto-tranche-a-2`, `a4d8390` | **failed: 86 of 88 jobs passed** |

**The failure.** `tools/validate_weekly_edits.py` failed two checks; the second
failed job, `gates-passed`, only rolls them up.
1. Positioning was pinned at seven sub-sections, and the crypto flows block is the
   eighth.
2. The word "venue", banned in a rendered Weekly, appeared in two placeholder lines.

**The fix,** `7e55cda` on `crypto-tranche-a-2`, merged here: the lines say
"exchange", and the gate lists "Crypto flows" as the eighth sub-section. The fix's
own CI run is under "CI" below.

## ST-R6.49a: mNAV

**`altdata/sources/treasury.py`**, on the external roster before the derived writer,
and in the daily crypto run.

| Input | Source | Robots / terms | Fixture |
|---|---|---|---|
| `treasury.btc_holdings` (instrument = ticker, top 20) | BitcoinTreasuries.com's "Public Companies that Own Bitcoin" table, `treasuries.bitbo.io` | robots.txt allows it (only `/private/` and `/junk/` disallowed); no terms page | `tests/fixtures/treasury/bitbo_public_companies.html`: **the real page**, captured 17 Oct, trimmed to 25 rows. Strategy holds 848,250 BTC |
| `treasury.mstr_shares` | Strategy's filings' stated share count: EDGAR XBRL `dei:EntityCommonStockSharesOutstanding` | EDGAR requires a contact User-Agent; the repo's `CHESTER_SEC_CONTACT` (`edgar.py`) | `edgar_shares_mstr.json`: **not captured** (no contact in this session); SEC's documented `companyconcept` shape |
| `treasury.mstr_spot` | MSTR's spot from the session's newest **captured option chain** (MSTR is a watched name) | local files; nothing fetched | built in the gate |

- **Not read.** `www.strategy.com` answers this client 403, robots.txt included.
  **`bitcointreasuries.net`'s terms of service forbid scraping or extracting data by
  automated systems**, so it is not read, robots.txt notwithstanding.
- **`calc.mnav`** (instrument MSTR, in `crypto_derived.py`) is the order's
  definition: **market cap over the value of the BTC held**, spot × shares /
  (BTC held × the BTC close). Each input is taken as of the session.
- **The panel** prints:
  - the level;
  - the **1.2 watch line**;
  - **item 49's one flag**, "FLAG: at or below 1 on <date>", when the latest capture
    is at or below 1.0 (tested to print at 1.00 and not at 1.01);
  - dual percentiles once 60 sessions are stored, before that the level and
    "percentile from <date>".
- Nothing else derives from it, and it carries no composite weight.
- **The definition point is needs-you item 1.**

## ST-R6.49b: treasury net purchases and "who is buying"

**`calc.treasury_net_purchases`** is a month's net BTC bought by the tracked
companies: holdings at the month's end less the prior month's end, over companies
present at both. The aggregator serves no history, so the series is
**forward-only**, and **the first complete month is November 2026**.

**The decomposition,** in the addendum's flows section beside the ETF rows, covers
the latest complete month in BTC:

| Leg | Source |
|---|---|
| ETF net flow | Each session's Farside total over that day's BTC close, summed |
| Treasury net purchases | `calc.treasury_net_purchases` |
| New supply mined | The change in chain-tip height between the month-end snapshots, × 3.125 |
| Residual | ETF + treasury − new supply (the session's definition, for your accept-all) |

A leg with no reading prints "not tracked" with its reason, and **the residual is
withheld**. Tested both ways.

## ST-R6.51b: the panels

Every panel reads the store by key, prints its data-as-of, and fetches nothing.
**An absent series is never a blank or a zero.** It prints one of:
- "awaiting the first pull": a built series with no row yet;
- "not tracked (<reason>)": nobody writes it;
- "awaiting EL-12": the dealer engine.

| Section | What it reads |
|---|---|
| 2 Tape | Prices, ranges and realised vol (the stored closes). DVOL (`deribit.dvol_*`). Funding per coin and total OI (`calc.funding_agg`, `calc.oi_usd`). **Basis: not tracked** (no basis series in Tranche A). **Liquidations: not tracked** (D-1). |
| 3 Flows | ETF weekly totals (`farside.*`), the stablecoin change (`llama.stable_total`), **who is buying** (49b). **Exchange net flows: not tracked** (no keyless series within robots). |
| 4 Mechanics | **MSTR mNAV** with its watch and flag lines (49a). **Skew and term structure: awaiting EL-12.** Deribit's book summary is keyless, but it carries no deltas, so a 25-delta skew needs a per-instrument call for each option. The paste's test (skew *and* term structure, keyless, within the time) fails on the skew, so both wait. **Crypto GEX: awaiting EL-12.** MSTR's implied moves to 11 Nov and 30 Nov, as Phase 1. |
| 5 On-chain | SR-29's row as it prints today (Tranche C computes it); the froth sample for Solana and Base, unscored ("not sampled" while GeckoTerminal's robots.txt refuses its API); **exchange balances: not tracked**. |
| 8 Ahead | Unchanged: 28 Oct the STRC vote; 11 Nov the MSCI announcement; 15 Nov the VanEck decision with its "15 Nov, to verify"; 30 Nov "implemented at the close of 30 Nov, effective 1 Dec"; Deribit's month-end expiries by rule; FOMC from the events store. |
| 1, 6, 7, 9 | As Phase 1 built them. |

**The narrative step** is the same model path. Its payload is the page's tables, so
the computed panels are its inputs. It runs under the existing numeral, style and
stance audits, plus a new **flag-word audit**: a read that names a flag the page
does not print is withheld. Tested both ways. The dated line for the paper's
appendix stays one line.

**The line budget.** Phase 1 printed **52** lines on the full fixture week; the
addendum's validator now holds the page to `max_lines: 52`. What the panels displace:
- the tape's four weekly-range lines fold into one;
- the two "date not published" lines merge into one;
- the mNAV cell carries its watch and flag lines;
- the "who is buying" table replaces the single treasury cell.

Words stay under 1,100 and five minutes.

## The MSTR/MSCI event watch (2 to 30 Nov)

**The key:** `calc.mnav`, instrument `MSTR`. Its inputs are `treasury.mstr_spot`,
`treasury.mstr_shares`, `treasury.btc_holdings` (MSTR) and `yfinance.mkt_btc_usd`.

**The read-only command** prints the latest of each, with dates, and whether the 1.2
and 1.0 lines are reached. It opens the store and writes nothing:

```
cd ~/chester-reports && .venv/bin/python -m altdata.sources.treasury show
```

## The gaps, and what would close each

| Gap | What would close it |
|---|---|
| Strategy's share count (and so mNAV) | `CHESTER_SEC_CONTACT` in the box's `.env`, the EDGAR writer's existing variable. If it is already set, nothing is needed. |
| Strategy's dashboard | `www.strategy.com` admitting a keyless client |
| Other treasury companies' mNAV | Their share counts and prices; out of scope for Phase 2 |
| Exchange net flows and balances | A keyless series within robots; none found |
| Basis | A futures-basis series (not in Tranche A) |
| Liquidations | D-1 (CoinGlass) stays No |
| 25-delta skew, term structure, crypto GEX | EL-12, the dealer engine |

## Gates (locally)

| Gate | Result |
|---|---|
| `tools/validate_digital_addendum.py` (Phase 2: absent states, mNAV and its flag at 1.0 and not 1.01, "who is buying" sums and withholds, the 52-line budget, the flag-word audit) | **94/94** |
| `tools/validate_crypto_sources.py` (+ group N, the treasury writer) | **103/103** |
| `tools/validate_official_sources.py` | 297/297 |
| `tools/validate_crypto_basket.py` | 93/93 |
| `tools/validate_audit_3a.py`, `validate_config_refs.py`, `validate_lenses.py` | 83/83, 56/56, 49/49 |
| `check_registry`, `check_library` | OK, 0 failures |

No gate reads the live store, fetches or calls a model. The Weekly and Monthly gates
render PDFs, so CI runs them.

## Box commands, for Ari (after Thursday's merge, inside a window; printed, not run)

```
cd ~/chester-reports
# The first treasury pull (seconds): holdings, the share count if CHESTER_SEC_CONTACT
# is set, MSTR's spot from the captured chains; then mNAV.
.venv/bin/python -m altdata.sources.treasury
.venv/bin/python -m altdata.sources.crypto_derived
.venv/bin/python -m altdata.sources.treasury show          # read-only
# The 25 Oct dry-run page (it also builds on its own in that Sunday's run):
.venv/bin/python -m daily_cascade.digital_addendum render --week-ending 2026-10-23 --no-narrative
```

## Files shared with open branches

**Session A's** (`6b-dealer-2`, `vol-event-52`, `6b-dealer-3`, and the chain they
stand on). All are additions; at a conflict, keep both sides:
- `CLAUDE.md`: one paragraph; the gate count is not changed;
- `metrics_registry.yaml`;
- `source_registry.yaml`;
- `altdata/feeds.py`: the `EXTERNAL_WRITERS` tail;
- `config/catalogue_commands.yaml`;
- `tools/validate_audit_3a.py`;
- `scripts/run_crypto_basket.sh`.

The Weekly's and Monthly's builders are not touched on this branch.

**The 6e and crypto line:** `daily_cascade/digital_addendum.py`,
`config/digital_addendum.yaml`, `altdata/sources/crypto_derived.py`,
`tools/validate_digital_addendum.py`, `tools/validate_crypto_sources.py`.

## Needs you

1. **mNAV's definition.** The order says market cap over BTC value. On that basic
   definition Strategy reads about **0.83** today, already below the **1.0 flag
   line**, so the flag will print on the first capture.
   - Strategy's own headline mNAV, and the aggregators', is
     **enterprise-value-based**: about 1.04 on 17 Oct (bitcointreasuries.net shows
     EV 1.04, basic 0.83, diluted 0.84).
   - If the 1.2 and 1.0 lines were set against the EV figure, rule that I switch the
     numerator to EV. That adds debt and preferreds, which need a keyless source of
     their own.
2. **`CHESTER_SEC_CONTACT`.** Is it set on the box? Without it, mNAV prints "not
   tracked (the share count …)".
3. **The "who is buying" residual** (ETF + treasury − new supply), for your
   accept-all.
4. **The 52-line budget,** and what the panels displaced, for your accept-all.
5. **Skew and term structure stay "awaiting EL-12".** The keyless book summary
   carries no deltas.

## CI

This branch's push, and the `crypto-tranche-a-2` fix (`7e55cda`), are each read
once and recorded here.
