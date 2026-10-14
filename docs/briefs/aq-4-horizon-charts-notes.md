# AQ-4: the horizon bars, the quilt and the roll-yield row — notes (10 Oct 2026)

Branch `aq-4-horizon-charts`, from `origin/main` at `989b49b`, not merged. Change
order "Alternative Assets Quarterly" §7, and §3's "the tape" in the front matter.

## What was built

| Piece | Where |
|---|---|
| The tool: reads the store as of a date, never fetches | `tools/horizon_charts.py` |
| Universe copy, families and hues, horizons, quilt classes, roll-yield hook | `config/horizon_charts.yaml` |
| DBC (broad commodities) in the price feed | `altdata/sources/yfinance_source.py`, `metrics_registry.yaml` (54 members), `tools/validate_prices.py` |
| The gate, on a synthetic store (72 checks) | `tools/validate_horizon_charts.py`, in the Makefile's list |

```
python -m tools.horizon_charts --as-of YYYY-MM-DD --out <dir> [--db <store>]
```

It writes these files to `<dir>`:

- **`bars_20y.png`, `bars_5y.png`, `bars_1y.png`.**
  - Total return over 20 years (annualised), 5 years (annualised) and one year.
  - Assets ranked within each chart. Thin horizontal bars with direct labels, one
    axis.
  - Each family has one fixed hue, never cycled: metals, energy, currency, EM and
    China, crypto, real estate, credit, international, agriculture, and SPY with
    TLT.
  - A footnote lists which assets are total return and which are price return, and
    which assets were not drawn and why.
- **`horizon_table.md`:** QTD and YTD for every asset, with its first stored date.
  This is the table beneath the bars.
- **`frame_<family>.png`:** one 20-year log chart per family.
  - Each member is rebased to 100 at its first point in the window.
  - The 5-year and 1-year windows are shaded and labelled.
  - The style follows M1/M2's long frame.
  - A family with nothing stored writes no PNG; its JSON entry says why.
- **`quilt.png`:** calendar-year total returns, ranked within each year, over 15
  years for the ten classes. The current year's column is headed "YTD".
- **`roll_yield.md`:** the roll-yield row (see below).
- **`horizon_charts.json`:** every figure plotted.
  - Bars: asset, horizon, value, the printed label, start and end dates, return
    kind, and whether the figure is "since inception".
  - Also: what was not drawn and why, the QTD/YTD table, the frames' members, the
    quilt's cells as drawn, and the roll-yield rows.
  - Each bar's value is read back from the drawn bar. The run stops if a drawn
    value differs from the computed one, so the Quarterly's tables and the numeral
    audit read the numbers the charts show.

Every figure carries its as-of date and the store cutoff.

**As of D** means every observation dated on or before D that was knowable by
D+1 at 06:00 UTC. That covers D's New York closes (stamped 20:20 or 21:20 UTC) and
D's coin bars (end of the UTC day plus 20 minutes), and nothing later.

### Rulings made in the session (each in the config, each changeable in one place)

- **Total return is built from the close and the stored dividends.** The price
  feed never stores the adjusted close (`yfinance_source.py` explains why). So a
  fund's total return reinvests each dividend at its ex-date close. The arithmetic
  is the adjusted close's, applied to rows that never restate.
- **Price return** applies to:
  - copper: the HG=F front future, so the roll is in its return;
  - natural gas: Henry Hub spot;
  - the coins;
  - the dollar index, the euro, the yen and the yuan. The yen and the yuan are
    inverted, as in AQ-5.
- **"Since inception".** A series whose first stored close is more than 7 days
  after the horizon's start (`grace_days`) prints "since <first stored date>". The
  bar is hatched and shows the series' annualised return over its own life. Under
  a year it shows the cumulative return and says "not annualised". It is never a
  padded or truncated bar.
  - A start value more than 10 days older than the date it stands for
    (`stale_days`) counts as a gap, and no bar is drawn.
- **The universe.**
  - When `config/correlation.yaml` (AQ-5) is present, the universe is read from
    it, VIX skipped. Until then the tool uses its own copy of the same twenty
    assets.
  - On main, the own copy carries AQ-5's six (DBA, ETH, SOL, ZEC, VNQI, MCHI) as
    absent rather than naming keys the registry does not hold yet
    (`validate_config_refs`). Once AQ-5 merges, its file supplies their keys and
    they draw.
  - An asset in that file without a family row in `horizon_charts.yaml` is
    refused rather than guessed.
  - PRL, uranium and the crypto light tier are carried as absent, with their
    reasons.
- **Assets outside the quarterly universe.** HYG, LQD (credit) and EFA
  (international) are included because credit and international equities have no
  universe member, and a family frame needs one.
- **Broad commodities is DBC.** The store held no commodity index; GUNR is
  producers' equity. DBC joins the price feed as one line, in the pattern AQ-5
  used for its six symbols. No index is synthesised.
- **Cash** is FRED DTB3, which is quoted on a discount basis. Each quote is
  converted to its bond-equivalent yield, 365d / (360 − 91d), and compounded over
  calendar days.

## The deep history: box commands (the operator, after the merge, inside the windows)

**How the feeds backfill today.**

- **Prices.** The nightly price pull reads `LOOKBACK_PERIOD = "2y"`. The one-shot
  `tools/backfill_prices.py` read 5 years (`--years 5`) and stamps reconstructed
  availability.
- **yfinance periods.** yfinance takes only fixed periods (1y, 2y, 5y, 10y, ytd,
  max), so "25y" is not one of them. `--period max` is the one pass that reaches
  25 years: it gives the full history wherever it exists, which for these symbols
  is 25 years or the instrument's whole life.
- **Re-running is safe.** Rows already stored are ignored (`INSERT OR IGNORE`).
- **FRED.** The FRED pull reads 1,500 days (about 4 years), so natural gas and the
  3-month bill also need one deeper pull.

**1. Prices: the universe on main, plus DBC.** About two minutes:

```
cd ~/chester-reports && git pull --ff-only
.venv/bin/python tools/backfill_prices.py --period max --symbols GLD,SLV,HG=F,USO,BTC-USD,XLRE,EEM,DX-Y.NYB,EURUSD=X,JPY=X,CNY=X,SPY,TLT,HYG,LQD,EFA,DBC
```

**2. AQ-5's six, once `aq-5-correlation-layer` is merged.** Until then the backfill
refuses them as "not in the basket" (exit 2), so this is a separate command:

```
.venv/bin/python tools/backfill_prices.py --period max --symbols DBA,ETH-USD,SOL-USD,ZEC-USD,VNQI,MCHI
```

**3. FRED natural gas and the 3-month bill, about 26 years.** This reads
`FRED_API_KEY` from the box's environment, which is already set:

```
.venv/bin/python -c "from altdata import config; from altdata.store import Store; from altdata.sources import fred; print(fred.pull(Store(), lookback_days=9500, series=[s for s in config.FRED_PULL_SERIES if s.key in ('natgas', 'tbill_3m')]))"
```

One caveat on step 3: FRED rows are stamped with the instant they are written. So
the deep history is visible to any as-of date on or after the pull, which covers
every Quarterly from January 2027, but not to an as-of date before it. The next
nightly FRED pull rewrites those two CSVs back to 1,500 days. The observation store
keeps the deep rows, because it never deletes.

**4. Read it back:**

```
.venv/bin/python -m tools.horizon_charts --as-of 2026-09-30 --out ~/chester-data/horizon/3q26
```

The last line it prints names every figure still shown "since" its first stored
date. After steps 1 to 3, the "since" figures left should be only the genuinely
young instruments:

- **At 20 years:** the coins, DBA (2007), HYG (2007), VNQI (2010), MCHI (2011) and
  XLRE (2015).
- **In the quilt:** Bitcoin before 2015 and XLRE before 2016.

Until the backfill runs, the tool prints "since <first stored date>" for most of
the 20-year bars. The gate checks that this is how it behaves.

## What waits on 6b (the curve)

- **The roll-yield row** is built: `roll_yield()` in the tool and the `roll_yield:`
  block in the config.
- **Rows:** WTI, natural gas, copper, corn, wheat and soybeans. Gold and silver are
  excluded because GLD and SLV hold metal, not futures.
- **Formula:** the annualised roll yield is ln(front / second) × 365 / days between
  expiries. A positive value means backwardation.
- **What it reads:** `curve.<id>.m1`, `curve.<id>.m2` and `curve.<id>.m1_m2_days`.
  If the days series is missing, it uses the declared spacing in months.
- **Until 6b and ST-B3-13 store those series,** every row prints "not tracked — the
  curve arrives with 6b" (the named hook, `CURVE_HOOK = "6b"`). No contract is
  fetched on this branch.
- **When 6b lands:** it writes those keys, or renames them in the config. Nothing in
  the tool changes.

## What waits on AQ-1 (the chart slots)

- **What this branch produces:** PNGs, two tables and the JSON. It places nothing
  in an edition.
- **What AQ-1 will do:** the quarterly cadence places them in the front matter's
  tape (the bars, the table, the quilt) and in each chapter's "The quarter" (the
  family's three bars and its long frame).
- **What AQ-1 decides:**
  - whether the per-chapter bars are slices of the three charts, or per-family
    redraws from the same JSON;
  - the email and HTML size rules (M-series: 2×, ≤150 KB, SVG beside);
  - whether these count toward a chart cap.
- **What AQ-1 can call:** the `draw_*` functions take the computed result, so AQ-1
  can call them through the stack's chart primitives instead of the CLI.
- **The cross-asset volatility table** (§10A, AQ-4 in §11's work order) is not on
  this branch. The order for this branch did not include it.

## Merge notes

- **AQ-5** (`aq-5-correlation-layer`) also edits `yfinance_source.SYMBOLS`, the
  registry's two `expected_members` lines and `validate_prices`' symbol count.
  Whichever merges second needs those three counts set to 60 (53 + six + DBC). The
  first `--period max` command above can then include AQ-5's six.
- **CLAUDE.md's gate count** is now forty-seven code gates (forty-four Python).
  Other branches that add a gate change the same line.
