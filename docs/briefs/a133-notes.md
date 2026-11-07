# A133 notes: item 124e, the illiquidity / price-impact proxy as a core input

Paste A133, 6 Nov 2026, session A. Branch `a133-item-124-illiquidity` from `origin/main` at `ee04ba21`. The paste is `76003bfb`. It merges Monday in chain-13 or in the week's second chain.

## The order

Batch 23 item 124e (the body's 106e) and section 0's Q3, on `origin/b129-five-filings`. Q3 is D-1 as amended: "ES volume comes from the stored ES bars or Massive's futures tier, never a new yfinance dependency (yfinance retires 22 Dec 2026 – 8 Jan 2027 under the price migration); a gap if neither carries volume."

Item 71's fragility panel already held SPY's Amihud measure. **This item extends it and never duplicates it.** The new code sits in `altdata/fragility.py` beside `daily_depth` and `rolling_mean`, which it reuses.

## Where ES volume came from

**The stored ES bars** (`altdata.bars`, the ES block's source).
- The 5-minute bars are summed per complete session, roll-adjusted as the ES block and the volatile-day flag read them.
- Volume is in contracts, and dollar volume is close × contracts × $50.
- Massive's futures tier was not needed: the bars carry volume, because `altdata.bars` writes Yahoo's `Volume` column for ES=F in contracts (its `volume_unit` "count").
- No yfinance import is added: the bars are already stored. The gate checks it.

**Limits and the gap.**
- **Depth of history.** The ES history starts with the bars writer: a 60-day backfill, then each session. So ES's three-year percentile prints with its real n, about 60 to 90 sessions on the box today, until the history fills. Each percentile prints its n beside it, so a short window is never hidden.
- **The gap path.** With no ES bars stored, or bars carrying no volume, ES prints "gap: no keyless volume" with the reason. The laptop's store has no bars table, so the laptop prints the gap; the box reads its bars.
- **After yfinance retires.** The bars writer itself reads yfinance today. When the price migration replaces it (22 Dec – 8 Jan), the replacement must keep ES volume, or this leg falls to the gap.
- **Speed.** The ES read starts at the first stored ES bar, since each session is one read of about 50 ms. A three-year window asked of a store with months of bars reads only those months.

## The new keys

| Key | What | Written by |
|---|---|---|
| `calc.amihud_spy_3y_pct` | SPY's 20-session Amihud mean, percentile over the last 756 sessions | the features pass (`altdata/market_features.py`) |
| `calc.amihud_spy_1y_pct` | the same over 252 | the same |
| `calc.amihud_es_3y_pct` | ES's, over 756 | the same |
| `calc.amihud_es_1y_pct` | ES's, over 252 | the same |

**Registration and writing.**
- **Registry.** Units percentile, family ratio (as `regime.dimension_percentile`), source `derived_state`. The SPY keys name their inputs. All four are barred from the market-state object (`calc.amihud_*`, a new `market_state_barred` entry).
- **Who writes.** `fragility.feature_rows()` returns the rows, and the features pass writes them, so `fragility.py` still writes nothing (group H's rule for item 71's reads). A measure not computed writes nothing.
- **Who reads.** 124c(ii) reads the keys only if its test passes, and nothing else does.

## The prints

- **The close's tape:** one line, from `batch14_b1_block.close_extras`. For example:

  > Illiquidity (Amihud, 20-session mean; three-year percentile, one-year in brackets): SPY 72nd (n 756) [1y 100th, n 252]; ES gap: no keyless volume (no ES bars stored). SPY quoted spread: not tracked (no captured quote carries SPY's own bid and ask).

- **The Weekly's Positioning & flows:** the same figures as a row table, SPY and ES, three-year and one-year with n, and the spread line, after trend breadth.
- **SPY's quoted spread: not tracked.** The captured chain carries options quotes and the underlying's spot, not its bid and ask. Massive's tier carries SPX and SPCX options only.

## Settings (`config/fragility.yaml` `amihud`, session-set)

| Setting | Value |
|---|---|
| windows | 1y 252 sessions, 3y 756 |
| `es_multiplier` | 50 |
| `spread_gap` | the spread's line |

## Gates (one at a time, foreground)

| Gate | Result |
|---|---|
| validate_batch14_b1 | 83/0 (group I added) |
| validate_es_block | 69/0 |
| validate_stack (whole: its groups are letters, none named tape) | 84/0 |
| validate_weekly_stack (whole: no positioning group) | 83/0 |
| check_registry | OK |
| validate_gates | 32/0 |
| check_library | 27 papers, 0 failures, 0 warnings |

Also run, all clean:
- validate_lenses 49/0, validate_regime 524/0 (the bar), validate_audit_3a 88/0;
- validate_names 20/0, validate_monthly_stack 268/0;
- validate_outliers 37/0, validate_config_refs 148/0, validate_stitch_tools 21/0.

No gate was added, so the counts are unchanged (`stitch_counts --check`: 0 disagree).

## Box steps

None required. The features pass writes the four keys at its next run. The ES leg fills as the stored ES bars accrue sessions.
