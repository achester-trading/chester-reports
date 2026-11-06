# Tail days 2016–2026: data replay

**Generated** 2026-11-05 22:14 ET by `tools/studies/tail_days.py` (branch `study/tail-days`). Companion to `docs/studies/tail-days-study-2026-11-05.md`. Study output only: no store, regime or report code was read or written.

## 0. Sources and coverage

| Series | Source | First obs. | Last obs. (as of) |
|---|---|---|---|
| ^GSPC | Yahoo Finance via `altdata.sources.yfinance_source._fetch_symbol` (split-adj., dividends beside) | 1927-12-30 | 2026-11-05 |
| ^VIX3M | Yahoo Finance via `altdata.sources.yfinance_source._fetch_symbol` (split-adj., dividends beside) | 2006-07-17 | 2026-11-05 |
| ^VVIX | Yahoo Finance via `altdata.sources.yfinance_source._fetch_symbol` (split-adj., dividends beside) | 2007-01-03 | 2026-11-05 |
| ^MOVE | Yahoo Finance via `altdata.sources.yfinance_source._fetch_symbol` (split-adj., dividends beside) | 2002-11-12 | 2026-11-05 |
| SPY | Yahoo Finance via `altdata.sources.yfinance_source._fetch_symbol` (split-adj., dividends beside) | 1993-01-29 | 2026-11-05 |
| RSP | Yahoo Finance via `altdata.sources.yfinance_source._fetch_symbol` (split-adj., dividends beside) | 2003-05-01 | 2026-11-05 |
| XLB | Yahoo Finance via `altdata.sources.yfinance_source._fetch_symbol` (split-adj., dividends beside) | 1998-12-22 | 2026-11-05 |
| XLC | Yahoo Finance via `altdata.sources.yfinance_source._fetch_symbol` (split-adj., dividends beside) | 2018-06-19 | 2026-11-05 |
| XLE | Yahoo Finance via `altdata.sources.yfinance_source._fetch_symbol` (split-adj., dividends beside) | 1998-12-22 | 2026-11-05 |
| XLF | Yahoo Finance via `altdata.sources.yfinance_source._fetch_symbol` (split-adj., dividends beside) | 1998-12-22 | 2026-11-05 |
| XLI | Yahoo Finance via `altdata.sources.yfinance_source._fetch_symbol` (split-adj., dividends beside) | 1998-12-22 | 2026-11-05 |
| XLK | Yahoo Finance via `altdata.sources.yfinance_source._fetch_symbol` (split-adj., dividends beside) | 1998-12-22 | 2026-11-05 |
| XLP | Yahoo Finance via `altdata.sources.yfinance_source._fetch_symbol` (split-adj., dividends beside) | 1998-12-22 | 2026-11-05 |
| XLRE | Yahoo Finance via `altdata.sources.yfinance_source._fetch_symbol` (split-adj., dividends beside) | 2015-10-08 | 2026-11-05 |
| XLU | Yahoo Finance via `altdata.sources.yfinance_source._fetch_symbol` (split-adj., dividends beside) | 1998-12-22 | 2026-11-05 |
| XLV | Yahoo Finance via `altdata.sources.yfinance_source._fetch_symbol` (split-adj., dividends beside) | 1998-12-22 | 2026-11-05 |
| XLY | Yahoo Finance via `altdata.sources.yfinance_source._fetch_symbol` (split-adj., dividends beside) | 1998-12-22 | 2026-11-05 |
| ^IXIC | Yahoo Finance via `altdata.sources.yfinance_source._fetch_symbol` (split-adj., dividends beside) | 1971-02-05 | 2026-11-05 |
| SPHB | Yahoo Finance via `altdata.sources.yfinance_source._fetch_symbol` (split-adj., dividends beside) | 2011-05-05 | 2026-11-05 |
| SPLV | Yahoo Finance via `altdata.sources.yfinance_source._fetch_symbol` (split-adj., dividends beside) | 2011-05-05 | 2026-11-05 |
| VIXCLS | FRED fredgraph CSV | 1990-01-02 | 2026-11-04 |
| BAMLH0A0HYM2 | FRED fredgraph CSV | 2023-11-06 | 2026-11-04 |
| BAMLC0A0CM | FRED fredgraph CSV | 2023-11-06 | 2026-11-04 |
| DGS10 | FRED fredgraph CSV | 1962-01-02 | 2026-11-04 |
| T10Y2Y | FRED fredgraph CSV | 1976-06-01 | 2026-11-05 |
| DTWEXBGS | FRED fredgraph CSV | 2006-01-02 | 2026-10-30 |

## 1. Condition replay

Each row is as of the close of the session k trading days before the tail day (T-k), on the ^GSPC trading calendar. Columns: SPX = ^GSPC close; ret% = that session's return; DD% = drawdown from the trailing 252-session closing high; RV20 = annualised stdev of the last 20 daily log returns; >2%/20 = sessions with |ret| > 2% in the last 20 (inclusive); VIX = FRED VIXCLS; VIX-RV = VIX less RV20; VIX/3M = VIXCLS ÷ ^VIX3M; HY, IG = ICE BofA OAS via FRED (BAMLH0A0HYM2, BAMLC0A0CM) in bp, HYΔ20 its change over 20 observations; 10yΔ3/Δ5 = DGS10 change in bp over 3/5 observations; 2s10s = FRED T10Y2Y in bp; MOVE = ^MOVE; $Δ5% = DTWEXBGS 5-observation change; RSP-SPY = 20-session total-return difference, pp; Sect>50d = sector SPDRs closing above their 50-session average / sectors with 50 sessions of history; Amihud pctl = SPY's 20-session mean of |ret| ÷ dollar volume, as a percentile of its own trailing 252 values (100 = least liquid). FRED values carry forward at most 5 calendar days; beyond that, "gap". OAS for a date is published the next morning.

Sources: Yahoo Finance via the repo's yfinance fetcher, last session 2026-11-05; FRED (FRED fredgraph CSV), each series' last observation in §0. As of 2026-11-05 22:14 ET.

### 1.1 T-1

| Tail day | side | T ret | T-1 date | SPX | ret% | DD% | RV20 | >2%/20 | VIX | VIX-RV | VIX/3M | VVIX | HY | HYΔ20 | IG | 10yΔ3 | 10yΔ5 | 2s10s | MOVE | $Δ5% | RSP-SPY | Sect>50d | Amihud pctl |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2020-03-16 | worst | -11.98 | 2020-03-13 | 2711.02 | 9.29 | -19.9 | 70.0 | 12 | 57.83 | -12.2 | 1.197 | 171.3 | gap | gap | gap | 18 | 20 | 45 | 138.4 | 3.19 | -3.58 | 0/11 | 100 |
| 2020-03-12 | worst | -9.51 | 2020-03-11 | 2741.38 | -4.89 | -19.0 | 50.8 | 10 | 53.90 | 3.1 | 1.215 | 146.9 | gap | gap | gap | 8 | -20 | 32 | 127.8 | 1.26 | -2.85 | 0/11 | 93 |
| 2020-03-09 | worst | -7.60 | 2020-03-06 | 2972.37 | -1.71 | -12.2 | 36.2 | 7 | 41.94 | 5.8 | 1.183 | 127.2 | gap | gap | gap | -28 | -39 | 25 | 125.2 | -0.80 | -1.66 | 1/11 | 82 |
| 2020-06-11 | worst | -5.89 | 2020-06-10 | 3190.14 | -0.53 | -5.8 | 19.6 | 2 | 27.57 | 8.0 | 0.932 | 116.5 | gap | gap | gap | -16 | -2 | 58 | 60.0 | -0.61 | 5.09 | 11/11 | 62 |
| 2025-04-04 | worst | -5.97 | 2025-04-03 | 5396.52 | -4.84 | -12.2 | 25.7 | 3 | 30.02 | 4.3 | 1.096 | 119.5 | 401 | 102 | 106 | -17 | -32 | 35 | 112.0 | -1.29 | 1.59 | 2/11 | 92 |
| 2020-03-18 | worst | -5.18 | 2020-03-17 | 2529.19 | 6.00 | -25.3 | 85.4 | 14 | 75.91 | -9.4 | 1.163 | 194.4 | gap | gap | gap | 14 | 26 | 55 | 109.8 | 3.88 | -3.94 | 0/11 | 100 |
| 2020-03-11 | worst | -4.89 | 2020-03-10 | 2882.23 | 4.94 | -14.9 | 48.7 | 9 | 47.30 | -1.4 | 1.199 | 138.8 | gap | gap | gap | -16 | -26 | 26 | 123.7 | 1.21 | -2.19 | 0/11 | 89 |
| 2025-04-03 | worst | -4.84 | 2025-04-02 | 5670.97 | 0.67 | -7.7 | 19.9 | 2 | 21.51 | 1.6 | 1.003 | 118.4 | 342 | 54 | 96 | -7 | -15 | 29 | 106.4 | 0.11 | 2.14 | 4/11 | 87 |
| 2020-04-01 | worst | -4.41 | 2020-03-31 | 2584.59 | -1.60 | -23.7 | 96.9 | 16 | 53.54 | -43.3 | 1.108 | 152.9 | gap | gap | gap | -13 | -14 | 47 | 83.9 | -2.37 | -5.34 | 0/11 | 100 |
| 2026-11-05 | worst | -4.36 | 2026-11-04 | 7688.62 | 1.58 | -1.7 | 12.9 | 0 | 16.61 | 3.7 | 0.884 | 90.4 | 332 | 23 | 91 | -4 | -15 | 32 | 93.9 | 0.28 | 7.38 | 7/11 | 100 |
| 2025-04-09 | best | +9.52 | 2025-04-08 | 4982.77 | -1.57 | -18.9 | 32.1 | 3 | 52.33 | 20.3 | 1.261 | 170.9 | 457 | 135 | 118 | 20 | 9 | 55 | 139.9 | 0.34 | -0.18 | 0/11 | 91 |
| 2020-03-24 | best | +9.38 | 2020-03-23 | 2237.40 | -2.93 | -33.9 | 86.8 | 16 | 61.59 | -25.2 | 1.087 | 167.9 | gap | gap | gap | -42 | 3 | 48 | 135.4 | 4.29 | -6.08 | 0/11 | 99 |
| 2020-03-13 | best | +9.29 | 2020-03-12 | 2480.64 | -9.51 | -26.7 | 59.5 | 11 | 75.47 | 15.9 | 1.318 | 155.1 | gap | gap | gap | 34 | -4 | 38 | 152.6 | 3.17 | -3.01 | 0/11 | 96 |
| 2020-04-06 | best | +7.03 | 2020-04-03 | 2488.65 | -1.51 | -26.5 | 96.3 | 16 | 46.80 | -49.5 | 1.044 | 143.5 | gap | gap | gap | -8 | -10 | 39 | 65.0 | 1.65 | -5.52 | 0/11 | 100 |
| 2020-03-26 | best | +6.24 | 2020-03-25 | 2475.56 | 1.15 | -26.9 | 95.0 | 16 | 63.95 | -31.0 | 1.188 | 171.9 | gap | gap | gap | -4 | -30 | 54 | 87.1 | 0.51 | -4.46 | 0/11 | 100 |
| 2020-03-17 | best | +6.00 | 2020-03-16 | 2386.13 | -11.98 | -29.5 | 81.1 | 13 | 82.69 | 1.6 | 1.221 | 207.6 | gap | gap | gap | -9 | 19 | 37 | 124.5 | 3.20 | -3.92 | 0/11 | 100 |
| 2022-11-10 | best | +5.54 | 2022-11-09 | 3748.57 | -2.08 | -21.8 | 26.4 | 7 | 26.09 | -0.3 | 0.935 | 90.1 | gap | gap | gap | -5 | 2 | -49 | 124.4 | -1.04 | 2.34 | 6/11 | 88 |
| 2018-12-26 | best | +4.96 | 2018-12-24 | 2351.10 | -2.71 | -19.8 | 24.4 | 6 | 36.07 | 11.7 | 1.251 | 111.9 | gap | gap | gap | -3 | -12 | 19 | 66.0 | -0.20 | -1.37 | 0/11 | 87 |
| 2020-03-10 | best | +4.94 | 2020-03-09 | 2746.56 | -7.60 | -18.9 | 44.5 | 8 | 54.46 | 10.0 | 1.265 | 137.2 | gap | gap | gap | -48 | -56 | 16 | 163.7 | 0.32 | -2.07 | 0/11 | 87 |
| 2020-03-02 | best | +4.60 | 2020-02-28 | 2954.22 | -0.82 | -12.8 | 24.9 | 3 | 40.11 | 15.2 | 1.344 | 125.7 | gap | gap | gap | -20 | -33 | 27 | 109.7 | 0.52 | -1.10 | 0/11 | 78 |

### 1.2 T-5

| Tail day | side | T ret | T-5 date | SPX | ret% | DD% | RV20 | >2%/20 | VIX | VIX-RV | VIX/3M | VVIX | HY | HYΔ20 | IG | 10yΔ3 | 10yΔ5 | 2s10s | MOVE | $Δ5% | RSP-SPY | Sect>50d | Amihud pctl |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2020-03-16 | worst | -11.98 | 2020-03-09 | 2746.56 | -7.60 | -18.9 | 44.5 | 8 | 54.46 | 10.0 | 1.265 | 137.2 | gap | gap | gap | -48 | -56 | 16 | 163.7 | 0.32 | -2.07 | 0/11 | 87 |
| 2020-03-12 | worst | -9.51 | 2020-03-05 | 3023.94 | -3.39 | -10.7 | 36.0 | 7 | 39.62 | 3.6 | 1.216 | 119.7 | gap | gap | gap | -18 | -38 | 33 | 97.0 | -0.49 | -1.66 | 1/11 | 80 |
| 2020-03-09 | worst | -7.60 | 2020-03-02 | 3090.23 | 4.60 | -8.7 | 30.2 | 4 | 33.42 | 3.2 | 1.206 | 114.7 | gap | gap | gap | -23 | -28 | 26 | 104.9 | -0.50 | -1.46 | 0/11 | 79 |
| 2020-06-11 | worst | -5.89 | 2020-06-04 | 3112.35 | -0.34 | -8.1 | 19.9 | 2 | 25.81 | 5.9 | 0.895 | 109.9 | gap | gap | gap | 16 | 12 | 63 | 61.2 | -1.42 | 6.46 | 11/11 | 69 |
| 2025-04-04 | worst | -5.97 | 2025-03-28 | 5580.94 | -1.97 | -9.2 | 21.0 | 2 | 21.65 | 0.7 | 0.984 | 102.4 | 347 | 60 | 94 | -4 | 2 | 38 | 96.8 | 0.12 | 2.00 | 2/11 | 94 |
| 2020-03-18 | worst | -5.18 | 2020-03-11 | 2741.38 | -4.89 | -19.0 | 50.8 | 10 | 53.90 | 3.1 | 1.215 | 146.9 | gap | gap | gap | 8 | -20 | 32 | 127.8 | 1.26 | -2.85 | 0/11 | 93 |
| 2020-03-11 | worst | -4.89 | 2020-03-04 | 3130.12 | 4.22 | -7.6 | 34.7 | 6 | 31.99 | -2.7 | 1.163 | 114.0 | gap | gap | gap | -11 | -31 | 35 | 89.6 | -0.53 | -1.21 | 3/11 | 79 |
| 2025-04-03 | worst | -4.84 | 2025-03-27 | 5693.31 | -0.33 | -7.3 | 21.0 | 2 | 18.69 | -2.4 | 0.940 | 89.5 | 327 | 46 | 91 | 4 | 14 | 41 | 91.0 | 0.30 | 1.16 | 2/11 | 92 |
| 2020-04-01 | worst | -4.41 | 2020-03-25 | 2475.56 | 1.15 | -26.9 | 95.0 | 16 | 63.95 | -31.0 | 1.188 | 171.9 | gap | gap | gap | -4 | -30 | 54 | 87.1 | 0.51 | -4.46 | 0/11 | 100 |
| 2026-11-05 | worst | -4.36 | 2026-10-29 | 7720.39 | -0.30 | -1.3 | 10.2 | 0 | 17.20 | 7.0 | 0.888 | 98.0 | 326 | 2 | 89 | -2 | 2 | 37 | 93.5 | 0.32 | 4.58 | 8/11 | 98 |
| 2025-04-09 | best | +9.52 | 2025-04-02 | 5670.97 | 0.67 | -7.7 | 19.9 | 2 | 21.51 | 1.6 | 1.003 | 118.4 | 342 | 54 | 96 | -7 | -15 | 29 | 106.4 | 0.11 | 2.14 | 4/11 | 87 |
| 2020-03-24 | best | +9.38 | 2020-03-17 | 2529.19 | 6.00 | -25.3 | 85.4 | 14 | 75.91 | -9.4 | 1.163 | 194.4 | gap | gap | gap | 14 | 26 | 55 | 109.8 | 3.88 | -3.94 | 0/11 | 100 |
| 2020-03-13 | best | +9.29 | 2020-03-06 | 2972.37 | -1.71 | -12.2 | 36.2 | 7 | 41.94 | 5.8 | 1.183 | 127.2 | gap | gap | gap | -28 | -39 | 25 | 125.2 | -0.80 | -1.66 | 1/11 | 82 |
| 2020-04-06 | best | +7.03 | 2020-03-30 | 2626.65 | 3.35 | -22.4 | 97.1 | 17 | 57.08 | -40.1 | 1.114 | 157.7 | gap | gap | gap | -18 | -6 | 47 | 90.7 | -2.25 | -4.66 | 0/11 | 100 |
| 2020-03-26 | best | +6.24 | 2020-03-19 | 2409.39 | 0.47 | -28.8 | 86.3 | 15 | 72.00 | -14.3 | 1.036 | 181.8 | gap | gap | gap | 39 | 24 | 68 | 141.1 | 3.79 | -4.91 | 0/11 | 100 |
| 2020-03-17 | best | +6.00 | 2020-03-10 | 2882.23 | 4.94 | -14.9 | 48.7 | 9 | 47.30 | -1.4 | 1.199 | 138.8 | gap | gap | gap | -16 | -26 | 26 | 123.7 | 1.21 | -2.19 | 0/11 | 89 |
| 2022-11-10 | best | +5.54 | 2022-11-03 | 3719.89 | -1.06 | -22.4 | 27.1 | 7 | 25.30 | -1.8 | 0.948 | 79.2 | gap | gap | gap | 4 | 18 | -57 | 136.3 | 1.16 | 2.45 | 6/11 | 85 |
| 2018-12-26 | best | +4.96 | 2018-12-18 | 2546.16 | 0.01 | -13.1 | 22.6 | 4 | 25.58 | 3.0 | 1.070 | 103.6 | gap | gap | gap | -9 | -7 | 17 | 59.4 | -0.29 | -0.66 | 0/11 | 91 |
| 2020-03-10 | best | +4.94 | 2020-03-03 | 3003.37 | -2.81 | -11.3 | 31.3 | 5 | 36.82 | 5.5 | 1.220 | 116.7 | gap | gap | gap | -28 | -31 | 31 | 103.0 | -0.64 | -1.00 | 0/11 | 78 |
| 2020-03-02 | best | +4.60 | 2020-02-24 | 3225.89 | -3.35 | -4.7 | 18.3 | 1 | 25.03 | 6.7 | 1.142 | 112.7 | gap | gap | gap | -18 | gap | 12 | 86.9 | gap | -0.47 | 2/11 | 82 |

### 1.3 T-20

| Tail day | side | T ret | T-20 date | SPX | ret% | DD% | RV20 | >2%/20 | VIX | VIX-RV | VIX/3M | VVIX | HY | HYΔ20 | IG | 10yΔ3 | 10yΔ5 | 2s10s | MOVE | $Δ5% | RSP-SPY | Sect>50d | Amihud pctl |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2020-03-16 | worst | -11.98 | 2020-02-14 | 3380.16 | 0.18 | 0.0 | 13.2 | 0 | 13.68 | 0.5 | 0.883 | 98.2 | gap | gap | gap | 0 | 0 | 17 | 62.4 | -0.07 | -1.64 | 10/11 | 65 |
| 2020-03-12 | worst | -9.51 | 2020-02-12 | 3379.45 | 0.65 | 0.0 | 13.4 | 0 | 13.74 | 0.3 | 0.895 | 96.7 | gap | gap | gap | 3 | -4 | 18 | 63.5 | 0.23 | -1.50 | 10/11 | 74 |
| 2020-03-09 | worst | -7.60 | 2020-02-07 | 3327.71 | -0.54 | -0.5 | 13.4 | 0 | 15.47 | 2.1 | 0.950 | 96.0 | gap | gap | gap | -2 | 8 | 18 | 65.6 | 0.67 | -1.37 | 9/11 | 67 |
| 2020-06-11 | worst | -5.89 | 2020-05-13 | 2820.00 | -1.75 | -16.7 | 27.9 | 6 | 35.28 | 7.4 | 0.966 | 142.8 | gap | gap | gap | -5 | -8 | 48 | 57.6 | -0.06 | -1.30 | 7/11 | 83 |
| 2025-04-04 | worst | -5.97 | 2025-03-07 | 5770.20 | 0.55 | -6.1 | 16.0 | 0 | 23.37 | 7.4 | 1.035 | 115.7 | 297 | 30 | 89 | 10 | 8 | 33 | 104.4 | -1.79 | 2.57 | 4/11 | 75 |
| 2020-03-18 | worst | -5.18 | 2020-02-19 | 3386.15 | 0.47 | 0.0 | 13.2 | 0 | 14.38 | 1.2 | 0.909 | 95.9 | gap | gap | gap | -3 | -6 | 14 | 68.0 | 0.43 | -1.47 | 10/11 | 69 |
| 2020-03-11 | worst | -4.89 | 2020-02-11 | 3357.75 | 0.17 | 0.0 | 13.3 | 0 | 15.18 | 1.9 | 0.941 | 97.0 | gap | gap | gap | -6 | -2 | 18 | 64.9 | 0.37 | -1.17 | 10/11 | 67 |
| 2025-04-03 | worst | -4.84 | 2025-03-06 | 5738.52 | -1.78 | -6.6 | 15.9 | 0 | 24.87 | 9.0 | 1.049 | 120.8 | 299 | 33 | 88 | 13 | 0 | 33 | 108.9 | -1.45 | 1.74 | 4/11 | 76 |
| 2020-04-01 | worst | -4.41 | 2020-03-04 | 3130.12 | 4.22 | -7.6 | 34.7 | 6 | 31.99 | -2.7 | 1.163 | 114.0 | gap | gap | gap | -11 | -31 | 35 | 89.6 | -0.53 | -1.21 | 3/11 | 79 |
| 2026-11-05 | worst | -4.36 | 2026-10-08 | 7765.36 | -0.47 | -0.7 | 10.1 | 0 | 15.41 | 5.3 | 0.852 | 87.7 | 315 | 45 | 82 | -9 | -2 | 47 | 100.7 | -0.28 | -2.62 | 3/11 | 54 |
| 2025-04-09 | best | +9.52 | 2025-03-12 | 5599.30 | 0.49 | -8.9 | 18.0 | 1 | 24.23 | 6.2 | 1.024 | 115.9 | 320 | 55 | 96 | 0 | 4 | 31 | 104.1 | -0.50 | 2.32 | 0/11 | 75 |
| 2020-03-24 | best | +9.38 | 2020-02-25 | 3128.21 | -3.03 | -7.6 | 20.5 | 2 | 27.85 | 7.3 | 1.167 | 121.0 | gap | gap | gap | -19 | -22 | 13 | 87.4 | 0.55 | -0.75 | 2/11 | 79 |
| 2020-03-13 | best | +9.29 | 2020-02-13 | 3373.94 | -0.16 | -0.2 | 13.4 | 0 | 14.15 | 0.7 | 0.902 | 99.2 | gap | gap | gap | 5 | -4 | 17 | 63.5 | 0.21 | -1.40 | 10/11 | 73 |
| 2020-04-06 | best | +7.03 | 2020-03-09 | 2746.56 | -7.60 | -18.9 | 44.5 | 8 | 54.46 | 10.0 | 1.265 | 137.2 | gap | gap | gap | -48 | -56 | 16 | 163.7 | 0.32 | -2.07 | 0/11 | 87 |
| 2020-03-26 | best | +6.24 | 2020-02-27 | 2978.76 | -4.42 | -12.0 | 25.1 | 3 | 39.16 | 14.1 | 1.309 | 118.0 | gap | gap | gap | -8 | -22 | 19 | 92.6 | 0.10 | -0.62 | 0/11 | 79 |
| 2020-03-17 | best | +6.00 | 2020-02-18 | 3370.29 | -0.29 | -0.3 | 13.2 | 0 | 14.83 | 1.6 | 0.921 | 101.0 | gap | gap | gap | -6 | -4 | 14 | 67.7 | 0.21 | -1.56 | 10/11 | 65 |
| 2022-11-10 | best | +5.54 | 2022-10-13 | 3669.91 | 2.60 | -23.5 | 26.1 | 5 | 31.94 | 5.8 | 1.004 | 101.3 | gap | gap | gap | gap | 14 | -50 | 155.1 | 0.38 | -0.23 | 1/11 | 88 |
| 2018-12-26 | best | +4.96 | 2018-11-26 | 2673.45 | 1.55 | -8.8 | 18.7 | 1 | 18.90 | 0.2 | 0.940 | 92.2 | gap | gap | gap | 1 | 1 | 23 | 51.5 | 0.55 | 2.38 | 3/11 | 98 |
| 2020-03-10 | best | +4.94 | 2020-02-10 | 3352.09 | 0.73 | 0.0 | 13.5 | 0 | 15.04 | 1.6 | 0.932 | 96.8 | gap | gap | gap | -10 | 2 | 19 | 68.1 | 0.39 | -1.68 | 9/11 | 74 |
| 2020-03-02 | best | +4.60 | 2020-01-31 | 3225.52 | -1.77 | -3.1 | 11.8 | 0 | 18.84 | 7.0 | 1.011 | 105.6 | gap | gap | gap | -14 | -19 | 18 | 73.0 | 0.15 | -1.20 | 6/11 | 52 |

### 1.4 Medians across the ten worst and the ten best days

Median of the available values; n is the count of non-gap values behind each median (shown when below 10). Sect>50d is the median share in percent.

| Group | offset | SPX | ret% | DD% | RV20 | >2%/20 | VIX | VIX-RV | VIX/3M | VVIX | HY | HYΔ20 | IG | 10yΔ3 | 10yΔ5 | 2s10s | MOVE | $Δ5% | RSP-SPY | Sect>50d | Amihud pctl |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ten worst | T-1 | 2927.30 | 0.07 | -13.6 | 42.4 | 8 | 44.62 | 2.3 | 1.136 | 133.0 | 342 (n=3) | 54 (n=3) | 96 (n=3) | -10 | -15 | 34 | 110.9 | 0.20 | -1.93 | 5% | 93 |
| ten worst | T-5 | 3101.29 | -0.33 | -9.0 | 32.4 | 5 | 32.70 | 3.2 | 1.175 | 114.3 | 327 (n=3) | 46 (n=3) | 91 (n=3) | -4 | -24 | 36 | 95.2 | 0.21 | -1.33 | 14% | 90 |
| ten worst | T-20 | 3379.80 | 0.18 | -0.6 | 13.4 | 0 | 15.44 | 2.0 | 0.945 | 97.6 | 299 (n=3) | 33 (n=3) | 88 (n=3) | -3 | -2 | 26 | 66.8 | -0.06 | -1.34 | 73% | 71 |
| ten best | T-1 | 2484.64 | -2.39 | -24.2 | 52.0 | 10 | 53.39 | 5.8 | 1.236 | 149.3 | 457 (n=1) | 135 (n=1) | 118 (n=1) | -6 | -7 | 38 | 124.5 | 0.51 | -2.54 | 0% | 94 |
| ten best | T-5 | 2927.30 | 0.24 | -14.0 | 33.7 | 7 | 39.38 | 0.1 | 1.128 | 122.8 | 342 (n=1) | 54 (n=1) | 96 (n=1) | -13 | -7 (n=9) | 28 | 108.1 | 0.11 (n=9) | -1.33 | 0% | 88 |
| ten best | T-20 | 3288.81 | -0.23 | -8.2 | 18.3 | 1 | 21.56 | 6.0 | 1.008 | 103.4 | 320 (n=1) | 55 (n=1) | 96 (n=1) | -8 (n=9) | -4 | 18 | 80.2 | 0.27 | -0.97 | 23% | 77 |

## 2. Two-sided tail base rates, ^GSPC since 1950

Source: ^GSPC daily closes through `altdata.sources.yfinance_source._fetch_symbol` (Yahoo Finance, price return), 1950-01-03 to 2026-11-05, n = 19,334 sessions; VIX from FRED VIXCLS (FRED fredgraph CSV). Pulled 2026-11-05 22:14 ET.

Full-sample thresholds: bottom decile ≤ -1.00%, top decile ≥ 1.05%. Rolling definition: the 10th/90th percentile of the trailing 2,520 sessions ending the day before (point in time); first rolling day 1960-01-15. Latest rolling thresholds: ≤ -1.10% / ≥ 1.15%.

### 2.1 Two-sided follow-through: P(opposite-tail day within h sessions)

h counts sessions after the conditioning day (T+1 … T+h). "Any day" is the unconditional rate over the same sample, for comparison.

| Definition | Conditioning day | n | h=1 | h=5 | h=10 | any day h=1 | any day h=5 | any day h=10 |
|---|---|---|---|---|---|---|---|---|
| full sample | bottom-decile → top-decile | 1,933 | 16.9% | 62.8% | 82.3% | 10.0% | 37.6% | 56.8% |
| full sample | top-decile → bottom-decile | 1,934 | 11.7% | 46.5% | 65.5% | 10.0% | 35.7% | 53.1% |
| rolling 10y | bottom-decile → top-decile | 1,800 | 15.8% | 61.1% | 83.1% | 10.6% | 39.1% | 59.0% |
| rolling 10y | top-decile → bottom-decile | 1,782 | 9.9% | 45.6% | 65.6% | 10.7% | 37.5% | 55.2% |

### 2.2 Forward returns after a bottom-decile day (close T to close T+h)

| Conditioning | h | n | mean | median | 10th pct | 90th pct | share > 0 |
|---|---|---|---|---|---|---|---|
| all days (baseline) | 1 | 19,333 | +0.04% | +0.05% | -1.00% | +1.05% | 53% |
| all days (baseline) | 5 | 19,329 | +0.18% | +0.30% | -2.33% | +2.52% | 57% |
| all days (baseline) | 20 | 19,314 | +0.73% | +1.07% | -4.28% | +5.29% | 62% |
| bottom decile, full sample | 1 | 1,933 | +0.01% | +0.01% | -1.60% | +1.50% | 50% |
| bottom decile, full sample | 5 | 1,932 | +0.28% | +0.30% | -3.16% | +3.73% | 55% |
| bottom decile, full sample | 20 | 1,929 | +0.98% | +1.33% | -5.73% | +7.16% | 62% |
| bottom decile, rolling 10y | 1 | 1,800 | -0.04% | -0.05% | -1.60% | +1.45% | 48% |
| bottom decile, rolling 10y | 5 | 1,799 | +0.23% | +0.22% | -3.23% | +3.74% | 54% |
| bottom decile, rolling 10y | 20 | 1,797 | +0.79% | +1.14% | -6.13% | +7.18% | 59% |
| top decile, full sample | 1 | 1,934 | +0.09% | +0.08% | -1.13% | +1.42% | 54% |
| top decile, full sample | 5 | 1,933 | +0.20% | +0.39% | -2.88% | +3.05% | 57% |
| top decile, full sample | 20 | 1,933 | +0.88% | +1.39% | -4.88% | +6.24% | 63% |

### 2.3 Bottom-decile days by VIX regime at T-1 (from 1990)

Bottom decile on the full-sample threshold. VIX is FRED VIXCLS at the prior session's close.

| VIX at T-1 | h | n | mean | median | 10th pct | 90th pct | share > 0 |
|---|---|---|---|---|---|---|---|
| VIX < 20 | 1 | 429 | +0.03% | +0.14% | -1.15% | +1.11% | 57% |
| VIX < 20 | 5 | 428 | +0.26% | +0.39% | -2.35% | +2.71% | 59% |
| VIX < 20 | 20 | 425 | +0.72% | +1.23% | -4.20% | +5.21% | 65% |
| VIX 20–30 | 1 | 493 | +0.09% | +0.10% | -1.68% | +1.74% | 54% |
| VIX 20–30 | 5 | 493 | +0.46% | +0.62% | -3.25% | +4.29% | 57% |
| VIX 20–30 | 20 | 493 | +0.91% | +1.89% | -6.38% | +7.24% | 60% |
| VIX 30–45 | 1 | 156 | +0.40% | +0.33% | -2.44% | +3.28% | 56% |
| VIX 30–45 | 5 | 156 | +0.89% | +1.51% | -5.05% | +6.20% | 65% |
| VIX 30–45 | 20 | 156 | +3.33% | +4.63% | -6.21% | +11.58% | 75% |
| VIX > 45 | 1 | 46 | +0.97% | +0.62% | -5.46% | +8.16% | 59% |
| VIX > 45 | 5 | 46 | +1.11% | +0.53% | -7.64% | +11.14% | 57% |
| VIX > 45 | 20 | 46 | +3.87% | +0.81% | -8.90% | +17.94% | 59% |

| VIX at T-1 | n bottom-decile days | P(top within 1) | P(top within 5) | P(top within 10) | share of all sessions in bucket that are bottom-decile |
|---|---|---|---|---|---|
| VIX < 20 | 428 | 11.9% | 56.3% | 79.0% | 7.4% |
| VIX 20–30 | 493 | 22.5% | 79.5% | 95.5% | 18.3% |
| VIX 30–45 | 156 | 38.5% | 89.7% | 100.0% | 25.1% |
| VIX > 45 | 46 | 45.7% | 95.7% | 100.0% | 40.0% |

### 2.4 Clustering: share of top-decile days within 5 sessions (either side) of a bottom-decile day

| Window | Definition | top-decile days | within ±5 of a bottom-decile day | share | if independent |
|---|---|---|---|---|---|
| 1950–2026 | full sample | 1,934 | 1,405 | 72.6% | 65.1% |
| 1950–2026 | rolling 10y | 1,782 | 1,284 | 72.1% | 62.4% |
| Nov 2016–Nov 2026 | full sample | 314 | 250 | 79.6% | 69.2% |
| Nov 2016–Nov 2026 | rolling 10y | 261 | 211 | 80.8% | 67.3% |

"If independent" is 1 − (1 − p)^10, the chance that a day has at least one bottom-decile day among its ten neighbours when bottom-decile days fall at random with that window's frequency p.

### 2.5 Check: Morningstar's "8 of the 10 best days within a week of a worst day" (S&P 500, Nov 2016–Nov 2026)

Window 2016-11-07 to 2026-11-05 (n = 2,513). "Within a week" = within 5 sessions either side.

| Rank | ^GSPC best day | ret | nearest top-10 worst day | sessions apart | in Morningstar's best list? |
|---|---|---|---|---|---|
| 1 | 2025-04-09 | +9.52% | 2025-04-04 | 3 | yes |
| 2 | 2020-03-24 | +9.38% | 2020-03-18 | 4 | yes |
| 3 | 2020-03-13 | +9.29% | 2020-03-12 | 1 | yes |
| 4 | 2020-04-06 | +7.03% | 2020-04-01 | 3 | yes |
| 5 | 2020-03-26 | +6.24% | 2020-04-01 | 4 | yes |
| 6 | 2020-03-17 | +6.00% | 2020-03-16 | 1 | yes |
| 7 | 2022-11-10 | +5.54% | 2025-04-03 | 599 | yes |
| 8 | 2018-12-26 | +4.96% | 2020-02-27 | 294 | yes |
| 9 | 2020-03-10 | +4.94% | 2020-03-09 | 1 | yes |
| 10 | 2020-03-02 | +4.60% | 2020-02-27 | 2 | yes |

**^GSPC: 8 of 10 best days sit within 5 sessions of a top-10 worst day.**

| Rank | ^GSPC worst day | ret | in Morningstar's worst list? |
|---|---|---|---|
| 1 | 2020-03-16 | -11.98% | yes |
| 2 | 2020-03-12 | -9.51% | yes |
| 3 | 2020-03-09 | -7.60% | yes |
| 4 | 2025-04-04 | -5.97% | yes |
| 5 | 2020-06-11 | -5.89% | yes |
| 6 | 2020-03-18 | -5.18% | yes |
| 7 | 2020-03-11 | -4.89% | yes |
| 8 | 2025-04-03 | -4.84% | yes |
| 9 | 2020-02-27 | -4.42% | no |
| 10 | 2020-04-01 | -4.41% | yes |

On Morningstar's own twenty dates (as listed in the study): **8 of 10** best days sit within 5 sessions of one of the 10 worst days on the S&P 500 trading calendar.

## 3. Vol-managed exposure backtest, ^GSPC since 1990

Source: ^GSPC price return (no dividends) via `altdata.sources.yfinance_source`, 1990-01-02 to 2026-11-05, n = 9,280. Exposure = min(1.5, max(0.25, 0.12² / RV²₂₀)), RV₂₀ the annualised sample variance of the last 20 daily log returns, set at the close and held over the next session. Cash and borrowing earn and cost zero; Sharpe is on excess-of-zero returns. Cost case: 2bp × |Δexposure| each day. Pulled 2026-11-05 22:14 ET.

| Strategy | Ann. return (CAGR) | Ann. vol | Sharpe (rf = 0) | Max drawdown | Mean exposure | Ann. turnover |
|---|---|---|---|---|---|---|
| Buy and hold | 8.59% | 17.97% | 0.55 | -56.8% | 1.00 | 0.0x |
| Vol-managed, no costs | 6.46% | 12.01% | 0.58 | -36.5% | 0.90 | 9.5x |
| Vol-managed, 2bp/turnover | 6.25% | 12.01% | 0.57 | -36.8% | 0.90 | 9.5x |

Exposure held on each of the twenty dates (set at T-1's close):

| Date | Side | ^GSPC ret | Exposure held | Strategy ret (no costs) |
|---|---|---|---|---|
| 2025-04-09 | best | +9.52% | 0.25 | +2.38% |
| 2020-03-24 | best | +9.38% | 0.25 | +2.35% |
| 2020-03-13 | best | +9.29% | 0.25 | +2.32% |
| 2020-04-06 | best | +7.03% | 0.25 | +1.76% |
| 2020-03-26 | best | +6.24% | 0.25 | +1.56% |
| 2020-03-17 | best | +6.00% | 0.25 | +1.50% |
| 2022-11-10 | best | +5.54% | 0.25 | +1.39% |
| 2018-12-26 | best | +4.96% | 0.25 | +1.24% |
| 2020-03-10 | best | +4.94% | 0.25 | +1.23% |
| 2020-03-02 | best | +4.60% | 0.25 | +1.15% |
| 2020-03-16 | worst | -11.98% | 0.25 | -3.00% |
| 2020-03-12 | worst | -9.51% | 0.25 | -2.38% |
| 2020-03-09 | worst | -7.60% | 0.25 | -1.90% |
| 2020-06-11 | worst | -5.89% | 0.38 | -2.22% |
| 2025-04-04 | worst | -5.97% | 0.25 | -1.49% |
| 2020-03-18 | worst | -5.18% | 0.25 | -1.30% |
| 2020-03-11 | worst | -4.89% | 0.25 | -1.22% |
| 2025-04-03 | worst | -4.84% | 0.36 | -1.76% |
| 2020-04-01 | worst | -4.41% | 0.25 | -1.10% |
| 2026-11-05 | worst | -4.36% | 0.86 | -3.76% |

Median exposure: best days 0.25, worst days 0.25. Sum of strategy returns on the ten worst -20.1% vs buy-and-hold -64.6%; on the ten best +16.9% vs +67.5%.

## 4. Spot checks against the study's approximate figures

Source: as §0. Each line is a figure the study marks (approx.) or states, and what the pulled data shows.

| Study figure | Data | Source |
|---|---|---|
| 2018: S&P ~20% below the 20 Sep high at the 24 Dec low | -19.8% (close to close, 20 Sep 2018 close 2930.75, 24 Dec 2351.10) | ^GSPC |
| 2018: VIX ~36 at the low | VIXCLS 24 Dec 2018 = 36.07 | VIXCLS |
| 2018: HY OAS ~530–540bp at the low | gap bp | BAMLH0A0HYM2 |
| 2020: VIX ~14 at the 19 Feb high | VIXCLS 19 Feb 2020 = 14.38 | VIXCLS |
| 2020: HY OAS 350 → ~1,090bp by 23 Mar | 19 Feb gap bp → 23 Mar gap bp | BAMLH0A0HYM2 |
| 2020: −12% week 24–28 Feb, VIX ~14 → ~40 | ^GSPC 21 Feb→28 Feb -11.5%; VIX 21 Feb 17.08 → 28 Feb 40.11 | ^GSPC, VIXCLS |
| 2020: 23 Mar low 2,191 intraday | 23 Mar close 2237.40 (intraday low not pulled) | ^GSPC |
| 2020: VIX ~27 → 40 around 11 Jun | VIX 10 Jun 27.57, 11 Jun 40.79 | VIXCLS |
| 2022: 25% bear market to the 12 Oct low | -25.4% from the Jan 2022 closing high | ^GSPC |
| 2022: VIX ~26 and falling before 10 Nov | VIX 9 Nov 26.09, 3 Nov 25.30 | VIXCLS |
| 2025: S&P ~8–10% below 19 Feb peak on 2 Apr | -7.7% | ^GSPC |
| 2025: VIX ~21–22 on 2 Apr | VIX 2 Apr 21.51 | VIXCLS |
| 2025: HY OAS ~260 → ~460bp by 7 Apr | 19 Feb 268 bp → 7 Apr 461 bp | BAMLH0A0HYM2 |
| 2025: VIX 45 → ~60 intraday 7 Apr | VIX close 4 Apr 45.31, 7 Apr 46.98, 8 Apr 52.33 | VIXCLS |
| 2025: 10y ~3.9% → ~4.5% in three sessions (8–9 Apr) | DGS10 4 Apr 4.01%, 9 Apr 4.34%, 11 Apr 4.48% | DGS10 |
| 2026: 5 Nov −4.4% (Morningstar), S&P −4.1% intraday | ^GSPC 5 Nov 2026 -4.36% | ^GSPC |
| Pattern: 8 of 10 best days within a week of a worst day | ^GSPC's own top/bottom 10: 8 of 10; on the study's twenty dates: 8 of 10 | ^GSPC, §2.5 |
| §3.1: first-day shocks came with VIX already 2–3x its February level | 9 Mar 2020: T-1 VIX 41.94 vs Feb 2020 median 15.47 (2.7x); 3 Apr 2025: T-1 VIX 21.51 vs Feb 2025 median 15.96 (1.3x) | VIXCLS |
| 2020: 11 Jun came after a 45% rally | 23 Mar close → 8 Jun close +44.5% | ^GSPC |
| 2025: 10y 3-session move into 9 Apr | DGS10 04-03 4.06%, 04-04 4.01%, 04-07 4.15%, 04-08 4.26%, 04-09 4.34%, 04-10 4.40%, 04-11 4.48% | DGS10 |
| 2026: 22 Oct −2.6% on AI-capex fears; 30 Oct "worst day since June" | ^GSPC 22 Oct -1.21%, 30 Oct -1.82%; ^IXIC 22 Oct -2.60%, 30 Oct -2.86% | ^GSPC, ^IXIC |
| 2026: Nasdaq −11% from the 6 Oct record at 5 Nov; October its worst month in over a year | ^IXIC 5 Nov close -11.9% from its 2026 closing high (2026-10-06); October 2026 -5.3% | ^IXIC |
| 2026 (context): S&P 500 in October | ^GSPC October 2026 -0.9% | ^GSPC |
| 2026: 4 Nov index up while SPHB/SPLV fell 3.4% | ^GSPC 4 Nov +1.58%; SPHB/SPLV 4 Nov -2.73% | ^GSPC, SPHB, SPLV |
| 2026: 5 Nov is the tenth-worst day of the decade (Morningstar) | on ^GSPC it ranks 11 of 2,513 (1 = worst); 27 Feb 2020 (-4.42%) is ^GSPC's ninth | ^GSPC |

<!-- CONTRADICTS -->
## 5. What the data contradicts

Claims in `docs/studies/tail-days-study-2026-11-05.md` (draft 1) that the numbers above do not support. Hand-written from §§1–4; the script keeps this section when it is re-run.

1. **§3.1 "the regime always was [forecastable]… in every completed episode the market was already in an elevated-vol, negative-gamma, forced-flow regime at least a day before the worst days."** Not true of 5 Nov 2026 on any price measure here: at T-1 VIX 16.61, RV20 12.9%, VIX/VIX3M 0.884 (contango), drawdown −1.7%, no 2% day in 20 sessions, 7 of 11 sectors above their 50-day (§1.1). The 3 Apr 2025 shock is weak support too: T-1 VIX 21.51, VIX/VIX3M 1.003, RV20 19.9%. The only stretched readings before 5 Nov 2026 were SPY's Amihud percentile (100) and RSP beating SPY by 7.4pp in 20 sessions, a rotation out of the mega-caps. These are not the elevated-vol regime the study describes. The claim holds for the ten best days and for the worst days from 11 Mar 2020 onward. It does not hold for the first day of an episode.
2. **§3.1 "the first-day shocks… came with VIX already 2–3x its February level."** True for 9 Mar 2020 (41.94 against a February median of 15.47, 2.7x). False for 3 Apr 2025: 21.51 against 15.96, 1.3x (§4).
3. **§2E "22 Oct −2.6% on AI-capex fears" and "worst day since June" on 30 Oct.** These are Nasdaq Composite moves (−2.60%, −2.86%). The S&P 500 fell −1.21% and −1.82%, and was −0.9% for October against the Nasdaq's −5.3%. Read the 2026 conditions as a Nasdaq/semis episode. Do not read them as an index-wide one.
4. **§2E "4 Nov: index up while SPHB/SPLV fell 3.4%."** SPHB/SPLV's close-to-close total-return ratio fell 2.73% on 4 Nov while ^GSPC rose 1.58%. The direction is confirmed. The 3.4% is not, though it may be an intraday or price-only figure.
5. **§2D "S&P ~8–10% below [the 19 Feb peak] on 2 Apr."** It was −7.7% close to close, just outside the stated range.
6. **§2D "10y ~3.9% → ~4.5% in three sessions" (8–9 Apr 2025).** DGS10 went 4.01% (4 Apr) → 4.34% (9 Apr) over three sessions and reached 4.48% only on 11 Apr, five sessions later. That is +33bp in three sessions, not about +60bp. The ~3.9% start is an intraday level that FRED's constant-maturity series does not show.
7. **§2C "VIX ~26 and falling" before 10 Nov 2022.** It fell over the month (31.94 at T-20) but not over the week before: 25.30 on 3 Nov, 26.09 on 9 Nov.
8. **§1 "5 Nov 2026 (−4.4%) as the tenth-worst day."** That holds on Morningstar's index. On the S&P 500, 5 Nov 2026 (−4.36%) ranks 11th of the decade. 27 Feb 2020 (−4.42%) is 9th and 1 Apr 2020 (−4.41%) is 10th. The study's numbering note covers the size gap but not the change of membership.
9. **§3.7 "the vol-managed result… improves risk-adjusted returns."** It barely does on ^GSPC since 1990. The Sharpe ratio is 0.58 against 0.55 before costs and 0.57 after 2bp per unit of turnover. Return is 6.46% (6.25% after costs) against 8.59% for buy-and-hold. The real gain is in drawdown: −36.5% against −56.8%. The rule did step down in the tail regimes: exposure was 0.25 on 18 of the 20 dates. That cut the ten worst days' sum from −64.6% to −20.1%, but also the ten best days' from +67.5% to +16.9%, so the rule lost slightly more over the twenty dates than buy-and-hold did (−3.2% against +2.9%, summed simple returns). It held 0.86 into 5 Nov 2026 because realised vol was low. It is a drawdown tool, not a Sharpe tool, and it gives no protection on an episode's first day (see item 1).
10. **106g's premise that size should halve after a bottom-decile day.** The base rates do not support a directional reason for it. After a bottom-decile day, mean and median forward returns are at or above the all-day baseline at 5 and 20 sessions: 20-day mean +0.98% against +0.73%, and +3.33% when VIX was 30–45 at T-1 (§2.2–2.3). The opposite tail is more likely too: a top-decile day within 5 sessions has a 62.8% chance against 37.6% unconditionally, and 89.7–95.7% when VIX is above 30. Only dispersion supports the halving: the 20-day 10th percentile is −5.73% against −4.28%. Any halving rule should state that its basis is dispersion and not drift.
11. **§1 "Eight of the ten best days sit within a week of a worst day because they are the same phenomenon."** The 8 of 10 count is reproduced (§2.5). At decile level, though, clustering is only moderately above chance: 72.6% of top-decile days sit within ±5 sessions of a bottom-decile day, against 65.1% if bottom-decile days were placed at random (79.6% against 69.2% in the Nov 2016–Nov 2026 window). The extreme-tail co-location is real. The general "same phenomenon" reading is stronger at the extremes than across the tails.

**Not testable here (gaps, not contradictions):**
- Every HY and IG OAS figure before 6 Nov 2023 (§2A 530–540bp; §2B 350 → 1,090bp). FRED now serves only the last three years of the ICE BofA series. No FRED API key was available to this run, so the public CSV was used, and it carries the same window.
- Intraday levels (2,191 on 23 Mar 2020; VIX ~60 on 7 Apr 2025).
- All positioning, flow, dealer-gamma and catalyst claims.
