# AQ-5 — the correlation layer: build notes (10 Oct 2026)

Branch `aq-5-correlation-layer`, not merged. Built against the Alternative Assets
Quarterly change order (`docs/change-order-alternative-assets-quarterly-2026-10-10.md`),
§5 rows "Stock–bond correlation anchor", "The former report's break logic" and
"Peer pairs", and §9 in full. The change order itself is not edited.

## What was built

| Piece | Where |
|---|---|
| Universe v1, windows, break, shift, aliases, named rows, peer pairs | `config/correlation.yaml` |
| The computation, the readers, the CLI | `altdata/correlation.py` |
| The daily write (last 14 days) | `altdata/market_features.py` — `compute()` calls the layer after the features, never fatal |
| Registry: 3 bulk blocks + 19 named entries, `rights_ceiling` vocabulary, `cross_asset_correlation` mechanism group | `metrics_registry.yaml` |
| The Weekly's one line | `daily_cascade/weekly_stack.py` `positioning_week` |
| The Monthly's Correlations block | `monthly_macro/stack.py` `correlations_block`, inserted in the slow layers after the base rates |
| The gate | `tools/validate_correlation_layer.py` (in the Makefile's list) |

### The universe

The former eighteen, in signals.py's order, plus SPY, TLT and VIX (`fred.vix`,
VIXCLS). All 21 are keyed. Six of them joined the price basket on this branch
(the follow-up of 10 Oct), and their history reads once the operator's price
backfill has run:

| id | series | note |
|---|---|---|
| gold, silver | `mkt_gld`, `mkt_slv` | the funds |
| copper | `mkt_copper_front` | HG=F front |
| oil | `mkt_uso` | USO, not CL=F: the front future's roll is a jump in its returns, and it printed below zero in April 2020 |
| natgas | `fred.natgas` | Henry Hub spot (DHHNGSP); lands the next morning |
| btc | `mkt_btc_usd` | read on common days, so its Monday return is Friday to Monday |
| us_re | `mkt_xlre` | |
| em | `mkt_eem` | |
| dxy, eur | `mkt_dxy`, `mkt_eurusd` | |
| jpy, cny | `mkt_usdjpy`, `mkt_usdcny` | **inverted**: the yen and the yuan, as the former report's assets were |
| spy, tlt | `mkt_spy`, `mkt_tlt` | |
| vix | `fred.vix` | VIXCLS, as ordered; lands the next morning |
| agri | `mkt_dba` | **new**: DBA, Invesco DB Agriculture (a futures fund, as the former report read it) |
| eth, sol, zec | `mkt_eth_usd`, `mkt_sol_usd`, `mkt_zec_usd` | **new**: ETH-USD, SOL-USD, ZEC-USD; continuous like BTC-USD, their bars stamped at the end of the UTC day. `zec.price_usd` (the shielded logger's CoinGecko snapshot) is not a close and is not used |
| intl_re | `mkt_vnqi` | **new**: VNQI, Vanguard Global ex-US Real Estate |
| china | `mkt_mchi` | **new**: MCHI, iShares MSCI China |

The six were added to `yfinance_source.SYMBOLS` in the basket's own pattern
(the registry's `market_close` and `market_actions` blocks now 59; the coins in
`CONTINUOUS_SYMBOLS` and in `tools/backfill_prices.py`'s `utc_day` rule, as
Bitcoin is). An asset without a feed would carry an `absent:` reason and join by
being given a `key`; PRL, the light-tier coins and uranium join that way.

The named rows read four more inputs: `mkt_gspc` (SPX), `mkt_qqq`, `mkt_efa` (the
"international" leg of US–international) and `fred.yield_10y` (as a change, not a
log return).

### The series (all `source: derived_state`, `observation_type: calculated`, `trigger_eligible: false`, `rights_ceiling: narrow_flag`, `added_date: 2026-10-10`)

- **The matrix.** `corr.<a>__<b>.60d` and `.252d` for all 210 pairs: 419 series.
  The SPY–TLT 60-day cell is **not written**: it is SR-9's
  `calc.corr_spy_tlt_60d`, computed the same way (the gate shows the two agree to
  the digit, value and availability), and read under that alias.
- **The shift flag.** `corr.<a>__<b>.shift`, 0/1, 210 series.
- **The break.** `corr.<asset>__{spy,tlt}.break` = 30-day minus 120-day
  correlation, 36 series. A break is |Δ| ≥ 0.30, "toward" when positive and
  "away" otherwise — signals.py's constants and rule, which the gate reads from
  signals.py's own source. The credit-sensitive escalation (us_re, intl_re, em,
  china breaking away from SPY) is a flag the Weekly prints; it escalates no
  trigger.
- **The named rows** (each its own registry entry, its paper's reading rule in
  the description): stock–bond SPX–TLT at 60d / 1y / 3y and SPX–10y at 60d / 1y;
  US–international 3y; BTC–SPY and BTC–QQQ (60d, 1y); gold–SPY; gold–DXY (the
  sign); oil–DXY (the sign); copper/gold against the 10-year (60d, 1y); the
  silver/gold ratio (SLV/GLD, a fund ratio); the average pairwise correlation.
  The 3-year SPX–TLT row carries §5's kill condition in `kill_condition`; no other
  row was given one, so none has one.
- **Peer pairs.** peers.py's table, ported into the config pair for pair and
  word for word (the gate parses peers.py and compares). Each pair's divergence =
  its 60-day correlation minus its own full-history median:
  `correlation.peer_table()`, and `python -m altdata.correlation peers`. Not
  printed in the Weekly or the Monthly — the Quarterly prints it (§9).

### Readings this build had to choose (session-set, in `config/correlation.yaml`, one place each)

1. **"Crossing by more than its IQR."** The shift's first arm fires when
   |60d − 252d| exceeds the 60-day's own five-year interquartile range **and** the
   60-day sat on the other side of the 252-day at least once in the last 60
   sessions — it crossed, and has gone past by more than the IQR. Below 252
   60-day values the IQR is not taken and this arm is off; the sign arm still
   reads. (`shift.cross_lookback`, `shift.iqr_min`.)
2. **"A sign change held 20 sessions"** fires on the session the hold completes.
3. **The average pairwise correlation is the mean of absolute values.** The VIX,
   the dollar and TLT join a liquidation by moving against the rest; a signed mean
   would let them cancel the spike it exists to show. A day is written only when
   every pair whose history has begun contributes (a pair's value carries at most
   five sessions — VIXCLS lands the next morning).
4. **Windows are common sessions**: a pair is read on the days both series
   printed; a window is never partial.

## Where it prints

- **The Weekly** — Positioning & flows (the stack config's positioning section),
  a "Cross-asset correlations" sub-section with **one line**, only in a week a
  30-vs-120-day break or a **named-row shift** fired; otherwise nothing. Weekly
  cadence only. Ruled 10 Oct (follow-up): the line's shifts are the named rows'
  matrix pairs only — BTC–SPY, gold–SPY, gold–DXY, oil–DXY (`weekly.shift_pairs`
  in the config). All-pairs shifts leave the Weekly. The caps are ceilings: at
  most three breaks and two shifts, each then "and N more".
- **The Monthly** — a "Correlations" block in the slow layers: the stock–bond rows
  in the triple form (latest with its data-as-of / long-run average with its
  window / percentile over the store's full history / five-year percentile
  "until the lenses"), and the month's top five shifts **across all pairs** —
  the only place an all-pairs shift prints.
- **No chart** this round: the cap of 12 stands; the heatmap waits for AQ-1.

## What waits

- **6e (the metric lenses).** The five-year percentile column prints "until the
  lenses"; `long_window: until_the_lenses` on every entry; dual percentiles
  (five-year and full history) are §9's and come with 6e. Whether a correlation
  earns a family of its own is the lenses' question — the entries use `ratio`, so
  the brief's family vocabulary is unchanged.
- **AQ-1.** The full heatmaps at 60 days and one year; any chart.
- **Round 4 item 25 (the surprise quadrant).** `correlation.surprise_quadrant()`
  is the named hook; it returns `None` and the Monthly says the quadrant is not
  yet built. No stub data.
- **The CPI test itself** — the 3-year correlation against the 3-year average CPI
  across backfilled history — needs the long history the backfill writes; the
  series and its kill condition are in place.
- **The Quarterly** prints the peer divergences, the episodes and the Book A
  consequence.

## Point in time

Every input is read through `ObservationStore.as_of()`; every row's
`available_at` is the latest across every input row its window touched, and its
`availability_kind` the weakest. The gate recomputes stored values from only the
rows knowable at their own `available_at`, proves a post-cutoff revision changes
nothing at the cutoff, and that a re-run writes nothing.

One consequence to know: the FRED inputs (VIXCLS, Henry Hub, DGS10) migrated
history all carries the migration instant as its `available_at`, so every
backfilled row that reads one of them is dated no earlier than that instant. That
is the honest answer, not a bug — an as-of replay before the migration sees no
VIX, natgas or SPX–10y correlation.

## The box backfill — run by the operator, inside a window, after the merge

Code reaches the box at the next timer after a merge to main; the 16:10 price pass
then starts pulling the six new symbols (two years) and the daily correlation pass
writes the last 14 days on its own. The history is two one-shots, **in order**:
the six symbols' five-year price history first, so the correlation backfill
reads all 21 assets.

```bash
ssh vps
cd ~/chester-reports
# 1. The six new symbols' price history (five years)
.venv/bin/python tools/backfill_prices.py --years 5 --symbols DBA,ETH-USD,SOL-USD,ZEC-USD,VNQI,MCHI --dry-run
.venv/bin/python tools/backfill_prices.py --years 5 --symbols DBA,ETH-USD,SOL-USD,ZEC-USD,VNQI,MCHI
# 2. The correlation history, over all 21
.venv/bin/python -m altdata.correlation compute --backfill --dry-run   # counts only, writes nothing
.venv/bin/python -m altdata.correlation compute --backfill
.venv/bin/python -m altdata.correlation show                           # the named rows, the month's breaks and shifts
```

Idempotent: a second run writes zero rows (only a changed value makes a vintage).
On a synthetic store of the full v1 universe, 1,300 sessions (about five years)
backfilled in 19 s on the laptop and wrote about 189,000 rows; the daily pass's
share took about 5 s and adds roughly 385 rows a session. SPX's own history is
longer than five years where `mkt_gspc` was backfilled for the base rates, so the
SPX rows may take longer. Not in 16:00–17:20 ET.
