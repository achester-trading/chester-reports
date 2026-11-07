# Vol-state calibration (item 124c(i)), 2026-11

*Written once by `python -m altdata.vol_state ledger`; refreshed yearly by the Annual Structural Review as a new dated file, never edited by hand. Signal-triage Batch 23 item 124c(i) (the order's 106c(i)); paste B134.*

**Pre-registered:** the rule, the sample and the computation below, with its SHA-256. A re-run applies it and may not change it.

| | |
|---|---|
| As of | 2026-11-05 |
| Sample | sessions with a decile, 1990-12-28 to 2026-11-05; n = 9,019 with 10 sessions after them |
| Sources | ^GSPC, ^VIX3M and ^VVIX through the yfinance writer's reader (Yahoo Finance); VIXCLS from FRED's public graph CSV (the laptop's first edition; the box's run from the store supersedes it) |
| Rule | the unweighted mean of the available input percentiles (at least two); the decile is its bin (config/vol_state.yaml, session-set) |
| Statistic | P(|return| ≥ 3% within the next 10 sessions \| decile), Wilson 95%; decile transitions at 5 and 20 sessions |
| Pass rule | none: the order grants a daily line and the sizing input, and states no gate |
| Unconditional rate | 11.4% |
| Computation SHA-256 | `be6efc27ab14f9cc9fd8bb2c4f5297e3c5a85c19fe2c2c77e3b23bffefad6ddd` |

## The computation

<!-- computation:begin -->
```text
THE INPUTS, per S&P 500 session, as of its close:
  vix      VIX: FRED VIXCLS, Yahoo's ^VIX close where FRED has not published
  rv20     the sample standard deviation of the S&P 500's 20 daily log returns
           ending the day, times sqrt(252), in percent
  term     VIX over VIX3M, from 3 January 2007
  vvix     VVIX, from 3 January 2012
  bigmove  the count of sessions with |simple return| >= 2% among the 20
           ending the day
A level is carried at most five calendar days over a gap; an input before its
first day, or holding fewer than 252 values, is n/a.

THE PERCENTILE: an input's share of its own values from its first day to the
day, the day included, that are at or below the day's value (expanding, point
in time).

THE RULE (session-set, config/vol_state.yaml): the score is the unweighted mean
of the available percentiles (at least two); the decile is the score's bin, 1
below 10 up to 10 at 90 and above. No weight is fitted.

THE CALIBRATION, from 2 January 1990: for every session with a decile and ten
sessions after it, whether any of the next ten sessions' |simple return| is 3%
or more; per decile, n, the share, and its Wilson 95% interval. The sessions
overlap, so the interval is narrower than independent draws would give.
THE TRANSITIONS: per decile today, the share of sessions whose decile five and
twenty sessions on is the same, higher and lower, and the full matrix.
```
<!-- computation:end -->

## P(|return| ≥ 3% within 10 sessions | decile)

| Decile | n | hits | P | 95% interval |
|---|---|---|---|---|
| 1 | 0 | 0 | n/a | n/a–n/a |
| 2 | 106 | 3 | 2.8% | 1.0%–8.0% |
| 3 | 1,338 | 25 | 1.9% | 1.3%–2.7% |
| 4 | 1,543 | 14 | 0.9% | 0.5%–1.5% |
| 5 | 1,234 | 25 | 2.0% | 1.4%–3.0% |
| 6 | 1,118 | 53 | 4.7% | 3.6%–6.1% |
| 7 | 1,001 | 73 | 7.3% | 5.8%–9.1% |
| 8 | 817 | 167 | 20.4% | 17.8%–23.3% |
| 9 | 924 | 238 | 25.8% | 23.0%–28.7% |
| 10 | 938 | 434 | 46.3% | 43.1%–49.5% |

## Transitions, 5 sessions on

| Decile today | same | higher | lower | →1 | →2 | →3 | →4 | →5 | →6 | →7 | →8 | →9 | →10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | n/a | n/a | n/a | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2 | 33% | 67% | 0% | 0 | 35 | 47 | 13 | 0 | 6 | 3 | 2 | 0 | 0 |
| 3 | 64% | 32% | 4% | 0 | 55 | 855 | 297 | 71 | 39 | 20 | 1 | 0 | 0 |
| 4 | 50% | 25% | 25% | 0 | 10 | 370 | 773 | 269 | 77 | 28 | 11 | 3 | 2 |
| 5 | 42% | 23% | 35% | 0 | 3 | 53 | 372 | 524 | 191 | 64 | 19 | 7 | 4 |
| 6 | 41% | 27% | 32% | 0 | 3 | 11 | 70 | 272 | 458 | 206 | 76 | 19 | 5 |
| 7 | 42% | 19% | 39% | 0 | 0 | 2 | 13 | 87 | 286 | 424 | 142 | 44 | 3 |
| 8 | 39% | 27% | 34% | 0 | 0 | 0 | 5 | 10 | 52 | 214 | 318 | 169 | 49 |
| 9 | 49% | 20% | 31% | 0 | 0 | 0 | 0 | 1 | 10 | 45 | 230 | 456 | 182 |
| 10 | 74% | 0% | 26% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 18 | 227 | 693 |

## Transitions, 20 sessions on

| Decile today | same | higher | lower | →1 | →2 | →3 | →4 | →5 | →6 | →7 | →8 | →9 | →10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | n/a | n/a | n/a | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2 | 10% | 90% | 0% | 0 | 11 | 33 | 24 | 12 | 16 | 9 | 1 | 0 | 0 |
| 3 | 41% | 56% | 3% | 0 | 39 | 549 | 328 | 176 | 109 | 66 | 30 | 26 | 15 |
| 4 | 32% | 40% | 27% | 0 | 27 | 393 | 500 | 283 | 169 | 96 | 42 | 21 | 9 |
| 5 | 23% | 27% | 50% | 0 | 14 | 233 | 365 | 280 | 162 | 84 | 53 | 25 | 14 |
| 6 | 20% | 31% | 49% | 0 | 12 | 88 | 189 | 254 | 222 | 132 | 107 | 55 | 57 |
| 7 | 22% | 26% | 52% | 0 | 2 | 34 | 100 | 156 | 229 | 224 | 102 | 97 | 56 |
| 8 | 17% | 35% | 47% | 0 | 1 | 6 | 30 | 57 | 136 | 158 | 140 | 186 | 103 |
| 9 | 27% | 23% | 49% | 0 | 0 | 2 | 7 | 15 | 61 | 160 | 209 | 253 | 217 |
| 10 | 50% | 0% | 50% | 0 | 0 | 0 | 0 | 1 | 13 | 67 | 128 | 262 | 467 |

## The config table

Copied into `config/vol_state.yaml` `calibration.deciles`; `tools/validate_item_124_c1.py` holds the two equal.

<!-- config:begin -->
```yaml
1: {hi: null, lo: null, n: 0, p: null, t20: null, t5: null}
2:
  hi: 0.0799
  lo: 0.0097
  n: 106
  p: 0.0283
  t20: {higher: 0.8962, lower: 0.0, same: 0.1038}
  t5: {higher: 0.6698, lower: 0.0, same: 0.3302}
3:
  hi: 0.0274
  lo: 0.0127
  n: 1338
  p: 0.0187
  t20: {higher: 0.5605, lower: 0.0291, same: 0.4103}
  t5: {higher: 0.3199, lower: 0.0411, same: 0.639}
4:
  hi: 0.0152
  lo: 0.0054
  n: 1543
  p: 0.0091
  t20: {higher: 0.4026, lower: 0.2727, same: 0.3247}
  t5: {higher: 0.2528, lower: 0.2463, same: 0.501}
5:
  hi: 0.0297
  lo: 0.0138
  n: 1234
  p: 0.0203
  t20: {higher: 0.2748, lower: 0.4976, same: 0.2276}
  t5: {higher: 0.2304, lower: 0.346, same: 0.4236}
6:
  hi: 0.0615
  lo: 0.0364
  n: 1118
  p: 0.0474
  t20: {higher: 0.3145, lower: 0.4866, same: 0.1989}
  t5: {higher: 0.2732, lower: 0.3179, same: 0.4089}
7:
  hi: 0.0907
  lo: 0.0584
  n: 1001
  p: 0.0729
  t20: {higher: 0.255, lower: 0.521, same: 0.224}
  t5: {higher: 0.1888, lower: 0.3876, same: 0.4236}
8:
  hi: 0.2334
  lo: 0.1782
  n: 817
  p: 0.2044
  t20: {higher: 0.3537, lower: 0.4749, same: 0.1714}
  t5: {higher: 0.2668, lower: 0.3439, same: 0.3892}
9:
  hi: 0.2867
  lo: 0.2304
  n: 924
  p: 0.2576
  t20: {higher: 0.2348, lower: 0.4913, same: 0.2738}
  t5: {higher: 0.197, lower: 0.3095, same: 0.4935}
10:
  hi: 0.4947
  lo: 0.431
  n: 938
  p: 0.4627
  t20: {higher: 0.0, lower: 0.5021, same: 0.4979}
  t5: {higher: 0.0, lower: 0.2612, same: 0.7388}
```
<!-- config:end -->

## Caveats

- The sessions overlap (a ten-session window per day), so the Wilson intervals are narrower than independent draws would give.
- The inputs enter at different dates (VIX/VIX3M from 2007, VVIX from 2012), so the score averages three inputs before 2007 and four before 2012: the same decile is a slightly different state across the sample.
- A base rate to read beside the day's state, not a forecast.
