# The Alpha Lab's rule grammar, v1

**Grammar id:** `alpha-lab-rules/v1`. Built 14 October 2026 for item X-2.10a, with the amendments of 14 October (change order section 10). The interpreter is `alpha/rules.py` and its settings are in `config/alpha_rules.yaml`.

**What it is for.** A hypothesis in a batch file can carry its rule twice:
- in words, as `rule_text`, which is always required;
- in this grammar, as `rule_dsl`.

A rule written in the grammar runs through the lab's harness the night it is registered, with no code written for it. A rule in words alone registers as `needs_code` and waits for the research sitting.

**Who this page is for.** Anyone writing a hypothesis without reading the code, including the Saturday brief. Each section below says what you may write, what it means, and what the lab will refuse.

## 1. The shape of a rule

```yaml
rule_dsl:
  grammar: alpha-lab-rules/v1
  universe: [SPY]                  # what the rule may trade
  cadence: friday_close            # when it decides
  trigger:                         # ALL of these must hold
    - {series: SPY, transform: pct_change, n: week, op: ">=", value: 1.0}
    - {series: {ratio: [RSP, SPY]}, transform: percentile, w: 1260, op: "<=", value: 10}
  direction: short                 # long | short | {if, then, else}
  instrument: SPY                  # a symbol, or a pair
  entry: next_open                 # this_close | next_open | next_close
  exits:
    stop: {pct: 2}                 # optional
    target: {r: 1}                 # optional
    time: 5                        # required: sessions
  cooldown: 0                      # optional: sessions after a trigger with no new one
  conditioning: []                 # optional: the counted variants
```

**Every key, and nothing else.**
- These keys are allowed: `grammar`, `universe`, `cadence`, `trigger`, `direction`, `instrument`, `entry`, `exits`, `cooldown`, `conditioning`, `cost_class` and `note`.
- An unknown key is an error, not ignored.
- `note` is free text and is never read.

## 2. Series: what a condition reads

A series is one of three things:

| You write | It reads |
|---|---|
| A **price symbol**: `SPY`, `XLU`, `HYG`, `TLT`, `BTC-USD` | that symbol's stored daily close |
| A **registry key**: `fred.ccc_oas`, `fred.yield_10y`, `acm.term_premium_10y`, `calc.net_liquidity` | that series, exactly as `metrics_registry.yaml` registers it |
| A **combination**: `{ratio: [RSP, SPY]}` or `{spread: [fred.ccc_oas, fred.bb_oas]}` | `a / b` or `a − b`, on the days both are stored |

**Price symbols.** These are the basket the price feed stores, about 80 symbols. The list is `SYMBOLS` in `altdata/sources/yfinance_source.py`.

**Fields.** A condition may ask for `field: open | high | low | volume` instead of the close.
- Only **nine symbols store an open, high and low**: SPY, QQQ, IWM, ^TNX, ^TYX, DX-Y.NYB, GC=F, CL=F and BTC-USD.
- Every other symbol is **closes only**. Asking for its high is an error.

**Registry keys.** Use the key exactly as registered. FRED series are `fred.<key>`, using the keys in `altdata/config.py`:
- credit spreads: `fred.hy_oas`, `fred.ig_oas`, `fred.ccc_oas`, `fred.bb_oas`;
- yields: `fred.yield_10y`, `fred.yield_2y`;
- and the rest of the Monthly's set.

The other families are prefixed `acm.`, `calc.`, `exposure.` and so on.

**A key the registry does not hold is an error. A key the store holds no rows for is a data gap.** Neither is ever replaced by a substitute.

## 3. Transforms: what a condition computes

Each condition is a series, a transform, and a comparison:

```yaml
{series: <series>, transform: <transform>, <its parameter>, op: <op>, value: <number>}
```

`op` is one of `>`, `>=`, `<`, `<=`, `==` or `!=`. `value` is a number.

| Transform | Parameter | Computes |
|---|---|---|
| `level` | — | the latest value |
| `change` | `n` | latest − the value n observations earlier, in the series' own units. Add `units: bp` for a percent series in basis points (×100). |
| `pct_change` | `n` | (latest ÷ the value n observations earlier − 1) × 100 |
| `zscore` | `w` | (latest − mean) ÷ standard deviation, over the last `w` observations |
| `percentile` | `w` | the latest value's percentile, 0 to 100, within the last `w` observations |
| `rank` | `set`, `n` | the series' rank by `pct_change` over `n`, within a named set. 1 is the strongest. |
| `crosses_above` / `crosses_below` | `other` (a series or a number) | 1 if the series crossed `other` on the latest observation, else 0. It takes no `op`. |
| `max` / `min` | `n` | the highest or lowest of the last `n` observations. Used mostly for stops. |

**Choosing `n` and `w`:**
- `n` is a count of the series' own stored observations, or the word `week`.
- `week` means "since the last observation of the previous week". A weekly change on a Friday then runs from last Friday's close, and a holiday week is still one week.
- `w` is at least 10.
- Five years of daily data is `w: 1260`.

**Named sets** for `rank` are in `config/alpha_rules.yaml`: `sectors` (the eleven SPDR funds), `styles`, `broad` and `rates_credit`.
- A member with no stored price at a date is left out of the ranking at that date.
- XLRE before October 2015 and XLC before June 2018 therefore rank nowhere, and nothing has to say so.

**Not enough history means no signal.** A condition whose series has fewer stored observations than its window needs does not hold, and the backtest counts it as "insufficient history".

## 4. Cadence: when a rule decides

| `cadence` | It decides on |
|---|---|
| `daily_close` | every session |
| `friday_close` | the last session of each ISO week: Friday, or Thursday when Friday is a holiday |
| `{release: <label>, at: day_before}` | the session before each scheduled release |
| `{release: <label>, at: day_of}` | the release day's session |

**Release labels** are the `label` values in `config/release_calendar.yaml`. Examples are `CPI`, `Payrolls (employment situation)`, `FOMC statement`, `PCE (personal income and outlays)`, `GDP` and `PPI`. The release dates come from the store's events table, read as they were known at the time.

## 5. Point-in-time: what the rule may know, and when

**A rule decides at an instant, and reads only what was knowable by then.** Every stored value carries the instant it became available (`available_at`), and the grammar reads each series at its latest vintage knowable by the decision instant.

**The two decision instants:**
- **17:40 ET** on the cadence day. This is the nightly loop's hour, after the close's capture, and it applies to `next_open` and `next_close` entries.
- **15:50 ET** for a `this_close` entry, before the close it fills at.

**What that means for each kind of series:**
- **A close-based trigger.** The day's close is knowable at about 16:20. It can therefore decide a `next_open` or `next_close` entry, but not a `this_close` one.
- **A `this_close` rule** reads the previous session's closes.
- **A FRED series** is published the next morning. A rule on the 17:40 close therefore reads yesterday's OAS, not today's.

**Every trade the backtest produces records two instants:** its decision instant and the latest availability of anything it read. The harness voids a run in which the second is later than the first.

## 6. Direction and instrument

**Direction** is one of these:
- `long`
- `short`
- `{if: <condition>, then: long|short, else: long|short}`, which decides each trade by a condition at the same instant. This expresses a two-sided rule.

**The instrument** is one of these:
- **A symbol in the rule's `universe`.**
- **A pair:** `{pair: {long: IEF, short: HYG, weight: equal | vol_matched, n: 60}}`.
  - Long the pair means long the `long` leg and short the `short` leg. `direction: short` reverses both.
  - `vol_matched` weights each leg by the inverse of its realised daily volatility over the last `n` sessions.
  - The weights sum to one, and the pair's return is per unit of gross.

**A Brookfield-complex instrument is refused**, in the universe or anywhere else, by the system's own rule. It never reaches the register.

## 7. Entry

| `entry` | Fills at | Needs |
|---|---|---|
| `this_close` | the close of the cadence day | the trigger to be knowable by 15:50 ET (see section 5) |
| `next_open` | the open of the next session with a stored open | a stored open: one of the nine symbols in section 2 |
| `next_close` | the close of the next session | a stored close |

A signal with no stored price within five sessions is dropped and counted as dropped.

## 8. Exits

`exits.time` is required. `stop` and `target` are optional.

**`time: <n>`** is a number of sessions.
- An open entry counts its entry session as session 1, and exits at the close of session n.
- A close entry exits at the close n sessions after the entry.

**`stop`** is one of these:
- `{pct: 2}`: 2% against the entry price.
- `{atr: 1.5, n: 20}`: 1.5 times the average true range over the last 20 sessions, measured at the decision. For a close-only instrument, the true range is the absolute close-to-close move.
- **A series level**, measured at the decision. For example, `{series: SPY, field: high, transform: max, n: week}` is the week's highest stored high.
- A pair's stop is in `pct` of the pair's return.

**`target`** is `{pct: <x>}` or `{r: <x>}`. R is the distance from the entry to the stop, so a target in R needs a stop.

**How exits are checked, bar by bar:**
1. A bar that **opens through** the stop or the target exits at that open.
2. A bar whose **range touches** the stop or the target exits at that level. When one bar touches both, the stop wins, because a daily bar does not say which came first.
3. For a **close-only instrument**, both are checked on closes and filled at the breaching close. The trade records that this happened.
4. The **time stop** exits at the close.

An open entry already beyond its stop exits at once, at the entry price.

**One position at a time.** A trigger while a position is open is ignored, and so is a trigger inside the `cooldown`.

## 9. Conditioning: the counted variants

Each conditioning entry has a `name`. **Every value it lists is one variant**, and every variant counts in the family's variant count, which deflates the Sharpe ratio.

| Form | The variants |
|---|---|
| `{name, state: dials.gamma.state, values: [positive, negative]}` | the base trades split by the stored market-state object's value at the decision. The path reads into the object: `dials.<dial>.state`, and so on. |
| `{name, condition: <condition>}` | the base trades split by whether a condition held at the decision: two variants, true and false |
| `{name, drop: <index>}` | the rule without trigger condition `<index>` (counting from 0), run on its own |
| `{name, replace: {instrument: ...}}` | the rule with its instrument, entry, exits or direction swapped, run on its own |

## 10. Costs

**Every trade is costed by the lab's cost model** (`config/alpha_costs.yaml`), at the size a new engine enters paper at: 1% of the lab's notional. A round trip pays:
- half the spread each way;
- slippage each way;
- commission each way;
- borrow on a short over the days held.

The cost is never at the mid. A symbol's cost class is ETF unless `config/alpha_rules.yaml` names it otherwise, or the rule sets `cost_class`.

## 11. What happens after you write it

**What ingestion does.** The ingestion compiles the rule against the store.
- **A grammar error, or a series the store does not hold:** the hypothesis registers as `needs_code` or `data_gap`, with the reason.
- **A rule that compiles:** it registers as `registered`.

**What the harness does.** The nightly loop puts each newly registered rule through the validation harness (X-1.6), unchanged, the night it is registered. The workbench (`python -m alpha.research run <id>`) does the same on demand. The harness applies:
- point-in-time;
- walk-forward with the embargo;
- the hold-out months removed and kept for the final check;
- the Sharpe ratio deflated by the family's variant count;
- the minimum sample.

**The model-idea rule.** A rule with source `model` must also pass two further tests (10.2 b):
- non-negative expectancy after costs on data after 1 July 2026;
- 1.5 times the minimum-size paper period before the allocator may raise it.

## 12. The first batch, as translated

The first batch (`hypotheses-2026-10-14.yaml`, H-001 to H-005) carried its rules in words only. Three are translated into the grammar by committed files under `alpha/research/translations/2026-10-14-claude-weekly-01/`. Each file is bound to the batch file's sha256 and states every substitution it made. The other two remain `needs_code`, with the reason.

**H-002, defensive leadership in an up week.** It reads the Friday close, so it enters at Monday's open rather than "at the Friday close":

```yaml
cadence: friday_close
trigger:
  - {series: SPY, transform: pct_change, n: week, op: ">=", value: 1.0}
  - {series: XLU, transform: rank, set: sectors, n: week, op: "<=", value: 3}
  - {series: XLP, transform: rank, set: sectors, n: week, op: "<=", value: 3}
  - {series: {ratio: [RSP, SPY]}, transform: percentile, w: 1260, op: "<=", value: 10}
direction: short
instrument: SPY
entry: next_open
exits: {stop: {series: SPY, field: high, transform: max, n: week}, time: 5}
conditioning:
  - {name: without_rsp_spy_condition, drop: 3}
```

**H-004, the credit quality split.** The store holds no duration, so the duration match is a volatility match. HYG and IEF are close-only, so the entry is the next close:

```yaml
cadence: daily_close
trigger:
  - {series: {spread: [fred.ccc_oas, fred.bb_oas]}, transform: change, n: 20, units: bp, op: ">=", value: 40}
  - {series: fred.ig_oas, transform: change, n: 20, units: bp, op: "<=", value: 5}
direction: long
instrument: {pair: {long: IEF, short: HYG, weight: vol_matched, n: 60}}
entry: next_close
exits: {time: 20}
cooldown: 20
```

**H-005, the term premium at a long-end extreme.** It is two-sided:

```yaml
cadence: friday_close
trigger:
  - {series: fred.yield_10y, transform: percentile, w: 1260, op: ">=", value: 95}
direction:
  if: {series: acm.term_premium_10y, transform: change, n: 20, op: ">", value: 0}
  then: short
  else: long
instrument: TLT
entry: next_close
exits: {stop: {atr: 1.5, n: 20}, time: 40}
```

**The two left in words:**
- **H-001**, the CPI-day straddle, needs option prices. The grammar reads no option quote.
- **H-003**, gamma and pivots, needs the Book B scanner's setup definitions. They are code, not a condition on one stored series.

## 13. What v1 cannot say, deliberately

- **Option structures and option prices.** These are the VRP engine's, in code.
- **Intraday bars.** Grammar v1 is daily.
- **Parameters fitted by the harness.** A grammar rule's numbers are fixed when it is written. A different number is a new, pre-registered variant.
- **Any reference to a figure the store does not hold.** That is a data gap, never a proxy.
