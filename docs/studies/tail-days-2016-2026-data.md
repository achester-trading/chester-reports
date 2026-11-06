# Tail days 2016–2026: data replay

**Generated** 2026-11-05 23:00 ET from data pulled 2026-11-05 22:12 ET by `tools/studies/tail_days.py` (branch `study/tail-days`). Companion to `docs/studies/tail-days-study-2026-11-05.md`. Study output only: no store, regime or report code was read or written.

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
| QQQ | Yahoo Finance via `altdata.sources.yfinance_source._fetch_symbol` (split-adj., dividends beside) | 1999-03-10 | 2026-11-05 |
| VIXCLS | FRED fredgraph CSV | 1990-01-02 | 2026-11-04 |
| BAMLH0A0HYM2 | FRED fredgraph CSV | 2023-11-06 | 2026-11-04 |
| BAMLC0A0CM | FRED fredgraph CSV | 2023-11-06 | 2026-11-04 |
| DGS10 | FRED fredgraph CSV | 1962-01-02 | 2026-11-04 |
| T10Y2Y | FRED fredgraph CSV | 1976-06-01 | 2026-11-05 |
| DTWEXBGS | FRED fredgraph CSV | 2006-01-02 | 2026-10-30 |
| DTB3 | FRED fredgraph CSV | 1954-01-04 | 2026-11-04 |
| BAA10Y | FRED fredgraph CSV | 1986-01-02 | 2026-11-04 |
| EBP | Federal Reserve FEDS Notes CSV (https://www.federalreserve.gov/econres/notes/feds-notes/ebp_csv.csv) | 1973-01 | 2026-10 |

## 1. Condition replay

Each row is as of the close of the session k trading days before the tail day (T-k), on the ^GSPC trading calendar. Columns: SPX = ^GSPC close; ret% = that session's return; DD% = drawdown from the trailing 252-session closing high; RV20 = annualised stdev of the last 20 daily log returns; >2%/20 = sessions with |ret| > 2% in the last 20 (inclusive); VIX = FRED VIXCLS; VIX-RV = VIX less RV20; VIX/3M = VIXCLS ÷ ^VIX3M; HY, IG = ICE BofA OAS via FRED (BAMLH0A0HYM2, BAMLC0A0CM) in bp, HYΔ20 its change over 20 observations; 10yΔ3/Δ5 = DGS10 change in bp over 3/5 observations; 2s10s = FRED T10Y2Y in bp; MOVE = ^MOVE; $Δ5% = DTWEXBGS 5-observation change; RSP-SPY = 20-session total-return difference, pp; Sect>50d = sector SPDRs closing above their 50-session average / sectors with 50 sessions of history; Amihud pctl = SPY's 20-session mean of |ret| ÷ dollar volume, as a percentile of its own trailing 252 values (100 = least liquid). FRED values carry forward at most 5 calendar days; beyond that, "gap". OAS for a date is published the next morning.

Sources: Yahoo Finance via the repo's yfinance fetcher, last session 2026-11-05; FRED (FRED fredgraph CSV), each series' last observation in §0. As of 2026-11-05 22:12 ET.

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
| 2020-03-02 | best | +4.60 | 2020-02-24 | 3225.89 | -3.35 | -4.7 | 18.3 | 1 | 25.03 | 6.7 | 1.142 | 112.7 | gap | gap | gap | -18 | -21 | 12 | 86.9 | 0.84 | -0.47 | 2/11 | 82 |

### 1.3 T-20

| Tail day | side | T ret | T-20 date | SPX | ret% | DD% | RV20 | >2%/20 | VIX | VIX-RV | VIX/3M | VVIX | HY | HYΔ20 | IG | 10yΔ3 | 10yΔ5 | 2s10s | MOVE | $Δ5% | RSP-SPY | Sect>50d | Amihud pctl |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2020-03-16 | worst | -11.98 | 2020-02-14 | 3380.16 | 0.18 | 0.0 | 13.2 | 0 | 13.68 | 0.5 | 0.883 | 98.2 | gap | gap | gap | 0 | 0 | 17 | 62.4 | -0.07 | -1.64 | 10/11 | 65 |
| 2020-03-12 | worst | -9.51 | 2020-02-12 | 3379.45 | 0.65 | 0.0 | 13.4 | 0 | 13.74 | 0.3 | 0.895 | 96.7 | gap | gap | gap | 3 | -4 | 18 | 63.5 | 0.23 | -1.50 | 10/11 | 74 |
| 2020-03-09 | worst | -7.60 | 2020-02-07 | 3327.71 | -0.54 | -0.5 | 13.4 | 0 | 15.47 | 2.1 | 0.950 | 96.0 | gap | gap | gap | -2 | 8 | 18 | 65.6 | 0.67 | -1.37 | 9/11 | 67 |
| 2020-06-11 | worst | -5.89 | 2020-05-13 | 2820.00 | -1.75 | -16.7 | 27.9 | 6 | 35.28 | 7.4 | 0.966 | 142.8 | gap | gap | gap | -5 | -8 | 48 | 57.6 | -0.06 | -1.30 | 7/11 | 83 |
| 2025-04-04 | worst | -5.97 | 2025-03-07 | 5770.20 | 0.55 | -6.1 | 16.0 | 0 | 23.37 | 7.4 | 1.035 | 115.7 | 297 | 30 | 89 | 10 | 8 | 33 | 104.4 | -1.79 | 2.57 | 4/11 | 75 |
| 2020-03-18 | worst | -5.18 | 2020-02-19 | 3386.15 | 0.47 | 0.0 | 13.2 | 0 | 14.38 | 1.2 | 0.909 | 95.9 | gap | gap | gap | -5 | -3 | 14 | 68.0 | 0.36 | -1.47 | 10/11 | 69 |
| 2020-03-11 | worst | -4.89 | 2020-02-11 | 3357.75 | 0.17 | 0.0 | 13.3 | 0 | 15.18 | 1.9 | 0.941 | 97.0 | gap | gap | gap | -6 | -2 | 18 | 64.9 | 0.37 | -1.17 | 10/11 | 67 |
| 2025-04-03 | worst | -4.84 | 2025-03-06 | 5738.52 | -1.78 | -6.6 | 15.9 | 0 | 24.87 | 9.0 | 1.049 | 120.8 | 299 | 33 | 88 | 13 | 0 | 33 | 108.9 | -1.45 | 1.74 | 4/11 | 76 |
| 2020-04-01 | worst | -4.41 | 2020-03-04 | 3130.12 | 4.22 | -7.6 | 34.7 | 6 | 31.99 | -2.7 | 1.163 | 114.0 | gap | gap | gap | -11 | -31 | 35 | 89.6 | -0.53 | -1.21 | 3/11 | 79 |
| 2026-11-05 | worst | -4.36 | 2026-10-08 | 7765.36 | -0.47 | -0.7 | 10.1 | 0 | 15.41 | 5.3 | 0.852 | 87.7 | 315 | 45 | 82 | -9 | -2 | 47 | 100.7 | -0.28 | -2.62 | 3/11 | 54 |
| 2025-04-09 | best | +9.52 | 2025-03-12 | 5599.30 | 0.49 | -8.9 | 18.0 | 1 | 24.23 | 6.2 | 1.024 | 115.9 | 320 | 55 | 96 | 0 | 4 | 31 | 104.1 | -0.50 | 2.32 | 0/11 | 75 |
| 2020-03-24 | best | +9.38 | 2020-02-25 | 3128.21 | -3.03 | -7.6 | 20.5 | 2 | 27.85 | 7.3 | 1.167 | 121.0 | gap | gap | gap | -19 | -22 | 13 | 87.4 | 0.55 | -0.75 | 2/11 | 79 |
| 2020-03-13 | best | +9.29 | 2020-02-13 | 3373.94 | -0.16 | -0.2 | 13.4 | 0 | 14.15 | 0.7 | 0.902 | 99.2 | gap | gap | gap | 5 | -4 | 17 | 63.5 | 0.21 | -1.40 | 10/11 | 73 |
| 2020-04-06 | best | +7.03 | 2020-03-09 | 2746.56 | -7.60 | -18.9 | 44.5 | 8 | 54.46 | 10.0 | 1.265 | 137.2 | gap | gap | gap | -48 | -56 | 16 | 163.7 | 0.32 | -2.07 | 0/11 | 87 |
| 2020-03-26 | best | +6.24 | 2020-02-27 | 2978.76 | -4.42 | -12.0 | 25.1 | 3 | 39.16 | 14.1 | 1.309 | 118.0 | gap | gap | gap | -8 | -22 | 19 | 92.6 | 0.10 | -0.62 | 0/11 | 79 |
| 2020-03-17 | best | +6.00 | 2020-02-18 | 3370.29 | -0.29 | -0.3 | 13.2 | 0 | 14.83 | 1.6 | 0.921 | 101.0 | gap | gap | gap | -7 | -1 | 14 | 67.7 | 0.03 | -1.56 | 10/11 | 65 |
| 2022-11-10 | best | +5.54 | 2022-10-13 | 3669.91 | 2.60 | -23.5 | 26.1 | 5 | 31.94 | 5.8 | 1.004 | 101.3 | gap | gap | gap | 8 | 21 | -50 | 155.1 | 0.68 | -0.23 | 1/11 | 88 |
| 2018-12-26 | best | +4.96 | 2018-11-26 | 2673.45 | 1.55 | -8.8 | 18.7 | 1 | 18.90 | 0.2 | 0.940 | 92.2 | gap | gap | gap | 1 | -1 | 23 | 51.5 | 0.60 | 2.38 | 3/11 | 98 |
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
| ten best | T-5 | 2927.30 | 0.24 | -14.0 | 33.7 | 7 | 39.38 | 0.1 | 1.128 | 122.8 | 342 (n=1) | 54 (n=1) | 96 (n=1) | -13 | -11 | 28 | 108.1 | 0.48 | -1.33 | 0% | 88 |
| ten best | T-20 | 3288.81 | -0.23 | -8.2 | 18.3 | 1 | 21.56 | 6.0 | 1.008 | 103.4 | 320 (n=1) | 55 (n=1) | 96 (n=1) | -7 | -3 | 18 | 80.2 | 0.27 | -0.97 | 23% | 77 |

## 2. Two-sided tail base rates, ^GSPC since 1950

Source: ^GSPC daily closes through `altdata.sources.yfinance_source._fetch_symbol` (Yahoo Finance, price return), 1950-01-03 to 2026-11-05, n = 19,334 sessions; VIX from FRED VIXCLS (FRED fredgraph CSV). Pulled 2026-11-05 22:12 ET.

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

Source: ^GSPC price return (no dividends) via `altdata.sources.yfinance_source`, 1990-01-02 to 2026-11-05, n = 9,280. Exposure = min(1.5, max(0.25, 0.12² / RV²₂₀)), RV₂₀ the annualised sample variance of the last 20 daily log returns, set at the close and held over the next session. Cash and borrowing earn and cost zero; Sharpe is on excess-of-zero returns. Cost case: 2bp × |Δexposure| each day. Pulled 2026-11-05 22:12 ET.

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

## Part 4. Vol-standardised tail base rates, ^GSPC since 1950

Parts 4–7 are numbered as the study's §6 cites them, apart from §§0–4 above.

Source: ^GSPC (Yahoo Finance via `altdata.sources.yfinance_source`, 1927-12-30 to 2026-11-05). Data pulled 2026-11-05 22:12 ET (cache `~/.cache/chester-study/tail_days`).

Standardisation. GARCH(1,1), constant mean, normal errors, fitted by `arch` 8.0.0 on daily ^GSPC returns from 1950-01-03 through each year-end and applied, with those parameters fixed, to the following year: σ_T is the one-step-ahead forecast made at T-1's close. First applied year 1955 (1950–54 is the first fit). Latest fit (through 2025-12-31, applied to 2026): ω = 0.0119, α = 0.0937, β = 0.8954, α+β = 0.9892. Cross-check: σ_T = sample standard deviation of the 20 daily returns ending T-1. z_T = r_T / σ_T (raw return, not demeaned). Deciles on each series' own full-sample thresholds; Part 2's rolling-10y definition is not repeated, because standardising already removes the level of vol.

Matched sample: 1955-01-03 to 2026-11-05, n = 18,083.

### Part 4.1 P(opposite-tail day within h sessions | tail day)

| Series | bottom-decile threshold | n bottom days | P(top ≤1) | P(top ≤5) | P(top ≤10) | any day ≤1 | any day ≤5 | any day ≤10 | n top days | P(bottom ≤5), given top | any day ≤5 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| raw, Part 2 sample (1950–) | ≤ -1.00% | 1,933 | 16.9% | 62.8% | 82.3% | 10.0% | 37.6% | 56.8% | 1,933 | 46.5% | 35.7% |
| raw, matched sample (1955–) | ≤ -1.02% | 1,808 | 16.8% | 62.8% | 82.0% | 10.0% | 37.5% | 56.7% | 1,808 | 46.8% | 35.8% |
| GARCH-standardised | ≤ -1.21σ | 1,808 | 9.3% | 49.7% | 74.4% | 10.0% | 41.9% | 67.9% | 1,808 | 30.6% | 38.6% |
| RV20-standardised | ≤ -1.29σ | 1,808 | 11.3% | 51.6% | 75.0% | 10.0% | 41.3% | 66.9% | 1,808 | 32.0% | 37.8% |

### Part 4.2 Clustering against a shuffled baseline

Share of top-decile days with a bottom-decile day within ±5 sessions (Part 2.4's statistic). Shuffled: the same series permuted 1,000 times (seed 20261105), mean and 2.5–97.5% range. "If independent" is Part 2.4's 1 − (1 − p)^10.

| Series | top-decile days | share near a bottom-decile day | shuffled mean | shuffled 95% range | if independent | excess over shuffled |
|---|---|---|---|---|---|---|
| raw, Part 2 sample (1950–) | 1,934 | 72.6% | 65.1% | 62.9–67.5% | 65.1% | +7.5pp |
| raw, matched sample (1955–) | 1,809 | 72.9% | 65.2% | 62.7–67.7% | 65.1% | +7.6pp |
| GARCH-standardised | 1,809 | 60.3% | 65.1% | 62.8–67.6% | 65.1% | -4.9pp |
| RV20-standardised | 1,809 | 60.8% | 65.2% | 62.7–67.8% | 65.1% | -4.4pp |

### Part 4.3 Forward returns after a bottom-decile day

Raw: close T to close T+h, percent. Standardised: the h-session log return divided by σ_{T+1}·√h, σ_{T+1} being the forecast known at T's close under the same definition (GARCH or RV20), in σ units. "Bottom decile" is each series' own (raw rows: raw deciles; standardised rows: deciles of z). Columns: n | mean | median | 10th | 90th | share > 0.

| Conditioning | h | raw: n | mean % | median % | 10th % | 90th % | >0 | std: n | mean σ | median σ | 10th σ | 90th σ | >0 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| raw, Part 2 sample (1950–): all days | 1 | 19,333 | +0.04 | +0.05 | -1.00 | +1.05 | 53% | — | — | — | — | — | — |
| raw, Part 2 sample (1950–): all days | 5 | 19,329 | +0.18 | +0.30 | -2.33 | +2.52 | 57% | — | — | — | — | — | — |
| raw, Part 2 sample (1950–): all days | 20 | 19,314 | +0.73 | +1.07 | -4.28 | +5.29 | 62% | — | — | — | — | — | — |
| raw, Part 2 sample (1950–): bottom decile | 1 | 1,933 | +0.01 | +0.01 | -1.60 | +1.50 | 50% | — | — | — | — | — | — |
| raw, Part 2 sample (1950–): bottom decile | 5 | 1,932 | +0.28 | +0.30 | -3.16 | +3.73 | 55% | — | — | — | — | — | — |
| raw, Part 2 sample (1950–): bottom decile | 20 | 1,929 | +0.98 | +1.33 | -5.73 | +7.16 | 62% | — | — | — | — | — | — |
| raw, matched sample (1955–): all days | 1 | 18,082 | +0.03 | +0.05 | -1.02 | +1.06 | 53% | — | — | — | — | — | — |
| raw, matched sample (1955–): all days | 5 | 18,078 | +0.17 | +0.29 | -2.38 | +2.56 | 56% | — | — | — | — | — | — |
| raw, matched sample (1955–): all days | 20 | 18,063 | +0.69 | +1.04 | -4.37 | +5.32 | 61% | — | — | — | — | — | — |
| raw, matched sample (1955–): bottom decile | 1 | 1,808 | +0.01 | +0.02 | -1.63 | +1.54 | 51% | — | — | — | — | — | — |
| raw, matched sample (1955–): bottom decile | 5 | 1,807 | +0.28 | +0.30 | -3.25 | +3.76 | 55% | — | — | — | — | — | — |
| raw, matched sample (1955–): bottom decile | 20 | 1,804 | +0.93 | +1.27 | -5.90 | +7.18 | 61% | — | — | — | — | — | — |
| GARCH-standardised: all days | 1 | 18,082 | +0.03 | +0.05 | -1.02 | +1.06 | 53% | 18,082 | +0.03 | +0.06 | -1.22 | +1.25 | 53% |
| GARCH-standardised: all days | 5 | 18,078 | +0.17 | +0.29 | -2.38 | +2.56 | 56% | 18,078 | +0.08 | +0.17 | -1.27 | +1.32 | 56% |
| GARCH-standardised: all days | 20 | 18,063 | +0.69 | +1.04 | -4.37 | +5.32 | 61% | 18,063 | +0.15 | +0.29 | -1.23 | +1.38 | 61% |
| GARCH-standardised: bottom decile | 1 | 1,808 | -0.05 | -0.04 | -1.35 | +1.17 | 48% | 1,808 | -0.11 | -0.05 | -1.50 | +1.19 | 48% |
| GARCH-standardised: bottom decile | 5 | 1,807 | +0.16 | +0.16 | -2.79 | +3.08 | 54% | 1,807 | +0.02 | +0.09 | -1.34 | +1.36 | 54% |
| GARCH-standardised: bottom decile | 20 | 1,804 | +0.64 | +1.01 | -4.90 | +6.36 | 60% | 1,804 | +0.11 | +0.26 | -1.37 | +1.38 | 60% |
| RV20-standardised: all days | 1 | 18,082 | +0.03 | +0.05 | -1.02 | +1.06 | 53% | 18,082 | +0.04 | +0.07 | -1.30 | +1.35 | 53% |
| RV20-standardised: all days | 5 | 18,078 | +0.17 | +0.29 | -2.38 | +2.56 | 56% | 18,078 | +0.09 | +0.18 | -1.38 | +1.44 | 56% |
| RV20-standardised: all days | 20 | 18,063 | +0.69 | +1.04 | -4.37 | +5.32 | 61% | 18,063 | +0.17 | +0.30 | -1.33 | +1.52 | 61% |
| RV20-standardised: bottom decile | 1 | 1,808 | -0.04 | -0.02 | -1.23 | +1.15 | 49% | 1,808 | -0.11 | -0.04 | -1.75 | +1.44 | 49% |
| RV20-standardised: bottom decile | 5 | 1,807 | +0.15 | +0.15 | -2.66 | +2.95 | 54% | 1,807 | +0.02 | +0.10 | -1.58 | +1.57 | 54% |
| RV20-standardised: bottom decile | 20 | 1,804 | +0.65 | +0.98 | -4.81 | +6.18 | 60% | 1,804 | +0.13 | +0.30 | -1.60 | +1.63 | 60% |

## Part 5. Calm-surface openers, ^GSPC since 1990

Source: ^GSPC (Yahoo Finance via `altdata.sources.yfinance_source`, 1927-12-30 to 2026-11-05); FRED VIXCLS (FRED fredgraph CSV, 1990-01-02 to 2026-11-04); SPY (Yahoo Finance via `altdata.sources.yfinance_source`, 1993-01-29 to 2026-11-05); RSP (Yahoo Finance via `altdata.sources.yfinance_source`, 2003-05-01 to 2026-11-05); QQQ (Yahoo Finance via `altdata.sources.yfinance_source`, 1999-03-10 to 2026-11-05); XLB (Yahoo Finance via `altdata.sources.yfinance_source`, 1998-12-22 to 2026-11-05); XLC (Yahoo Finance via `altdata.sources.yfinance_source`, 2018-06-19 to 2026-11-05); XLE (Yahoo Finance via `altdata.sources.yfinance_source`, 1998-12-22 to 2026-11-05); XLF (Yahoo Finance via `altdata.sources.yfinance_source`, 1998-12-22 to 2026-11-05); XLI (Yahoo Finance via `altdata.sources.yfinance_source`, 1998-12-22 to 2026-11-05); XLK (Yahoo Finance via `altdata.sources.yfinance_source`, 1998-12-22 to 2026-11-05); XLP (Yahoo Finance via `altdata.sources.yfinance_source`, 1998-12-22 to 2026-11-05); XLRE (Yahoo Finance via `altdata.sources.yfinance_source`, 2015-10-08 to 2026-11-05); XLU (Yahoo Finance via `altdata.sources.yfinance_source`, 1998-12-22 to 2026-11-05); XLV (Yahoo Finance via `altdata.sources.yfinance_source`, 1998-12-22 to 2026-11-05); XLY (Yahoo Finance via `altdata.sources.yfinance_source`, 1998-12-22 to 2026-11-05). Data pulled 2026-11-05 22:12 ET (cache `~/.cache/chester-study/tail_days`).

Definition: ^GSPC return in the bottom 1% of sessions since 1990-01-02 (threshold ≤ -3.11%, n = 9,280 sessions, 93 days), with FRED VIXCLS at the prior session's close below 20 and no session with |return| ≥ 2% among the 20 before T.

Of the 93 bottom-1% days: 9 had VIX < 20 at T-1; 10 had no 2% day in the prior 20 sessions; **6 had both** (the calm-surface openers). **1 of them fell 4% or more**: 2026-11-05 (-4.36%).

### Part 5.1 The openers

| # | Date | ^GSPC ret | VIX at T-1 | largest abs. ret, prior 20 | ≤ −4%? |
|---|---|---|---|---|---|
| 1 | 1991-11-15 | -3.66% | 13.96 | 1.38% | no |
| 2 | 2007-02-27 | -3.47% | 11.15 | 0.76% | no |
| 3 | 2016-06-24 | -3.59% | 17.25 | 1.34% | no |
| 4 | 2018-10-10 | -3.29% | 15.95 | 0.82% | no |
| 5 | 2020-02-24 | -3.35% | 17.08 | 1.77% | no |
| 6 | 2026-11-05 | -4.36% | 16.61 | 1.82% | yes |

### Part 5.2 Part 1 condition rows at T-1

Columns as Part 1 (§1). HY and IG OAS print "gap" before 6 Nov 2023 (FRED's window).

| Opener | T-1 date | SPX | ret% | DD% | RV20 | >2%/20 | VIX | VIX-RV | VIX/3M | VVIX | HY | HYΔ20 | IG | 10yΔ3 | 10yΔ5 | 2s10s | MOVE | $Δ5% | RSP-SPY | Sect>50d | Amihud pctl |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1991-11-15 | 1991-11-14 | 397.15 | -0.07 | -0.1 | 8.8 | 0 | 13.96 | 5.2 | gap | gap | gap | gap | gap | -6 | -16 | 175 | gap | gap | gap | gap | gap |
| 2007-02-27 | 2007-02-26 | 1449.37 | -0.13 | -0.7 | 6.3 | 0 | 11.15 | 4.9 | 0.915 | 70.3 | gap | gap | gap | -6 | -6 | -14 | 61.6 | 0.08 | 1.89 | 8/9 | 2 |
| 2016-06-24 | 2016-06-23 | 2113.32 | 1.34 | -0.7 | 7.9 | 0 | 17.25 | 9.4 | 0.936 | 104.7 | gap | gap | gap | 7 | 17 | 96 | 74.0 | -1.76 | 0.64 | 10/10 | 3 |
| 2018-10-10 | 2018-10-09 | 2880.34 | -0.14 | -1.7 | 6.3 | 0 | 15.95 | 9.7 | 0.959 | 103.9 | gap | gap | gap | 6 | 12 | 33 | 53.5 | 0.73 | -1.23 | 4/11 | 5 |
| 2020-02-24 | 2020-02-21 | 3337.75 | -1.05 | -1.4 | 13.9 | 0 | 17.08 | 3.2 | 0.970 | 104.9 | gap | gap | gap | -9 | -15 | 12 | 74.5 | 0.56 | -0.91 | 10/11 | 76 |
| 2026-11-05 | 2026-11-04 | 7688.62 | 1.58 | -1.7 | 12.9 | 0 | 16.61 | 3.7 | 0.884 | 90.4 | 332 | 23 | 91 | -4 | -15 | 32 | 93.9 | 0.28 | 7.38 | 7/11 | 100 |

### Part 5.3 Internals at T-1, as percentiles of their own history

Each value is as of T-1's close and its percentile is the share of the series' own values on or before T-1 that are at or below it (expanding history from the series' first observation; Amihud over the trailing 252 and 756 values). RSP-SPY and QQQ-SPY: 20-session total-return difference, pp (RSP from 2003, QQQ from 1999). Sector dispersion: cross-sectional standard deviation of the sector SPDRs' 20-session total returns, pp, computed when at least 9 sectors have 20 sessions of history (9 until XLRE in 2015, 11 from XLC in 2018). Amihud: SPY's 20-session mean of |ret| ÷ dollar volume (100 = least liquid).

| Opener | T-1 | RSP-SPY pp | pctl | QQQ-SPY pp | pctl | sector disp. pp | pctl | n sectors | Amihud 1y pctl | Amihud 3y pctl |
|---|---|---|---|---|---|---|---|---|---|---|
| 1991-11-15 | 1991-11-14 | gap | gap | gap | gap | gap | gap | gap | gap | gap |
| 2007-02-27 | 2007-02-26 | +1.89 | 96 | +1.24 | 63 | 3.02 | 42 | 9 | 2 | 1 |
| 2016-06-24 | 2016-06-23 | +0.64 | 71 | -1.42 | 26 | 1.84 | 17 | 10 | 3 | 13 |
| 2018-10-10 | 2018-10-09 | -1.23 | 8 | -1.61 | 23 | 3.28 | 63 | 11 | 5 | 3 |
| 2020-02-24 | 2020-02-21 | -0.91 | 14 | +2.00 | 76 | 2.60 | 44 | 11 | 76 | 82 |
| 2026-11-05 | 2026-11-04 | +7.38 | 100 | -7.34 | 2 | 8.24 | 99 | 11 | 100 | 72 |

### Part 5.4 What followed

T+1: close T to close T+1, and that session's high-low range ÷ close T. T+1..T+5: close T to close T+5, and the highest high less the lowest low over the five sessions ÷ close T. Top decile is Part 2's full-sample threshold (≥ 1.05%), looked for in T+1..T+5. "gap" where the sessions have not happened yet.

| Opener | ret T | ret T+1 | range T+1 | ret T+1..5 | range T+1..5 | top-decile day within 5? |
|---|---|---|---|---|---|---|
| 1991-11-15 | -3.66% | +0.68% | 1.49% | -1.69% | 2.84% | no |
| 2007-02-27 | -3.47% | +0.56% | 1.38% | -0.26% | 3.00% | yes |
| 2016-06-24 | -3.59% | -1.81% | 1.95% | +3.22% | 5.74% | yes |
| 2018-10-10 | -3.29% | -2.06% | 3.04% | +0.84% | 3.82% | yes |
| 2020-02-24 | -3.35% | -3.03% | 3.97% | -4.21% | 12.13% | yes |
| 2026-11-05 | -4.36% | gap | gap | gap | gap | gap |

A top-decile day followed within 5 sessions after **4 of 5** openers with five sessions of history.

## Part 6. Vol-managed exposure against a matched constant mix, ^GSPC since 1990

Source: ^GSPC (Yahoo Finance via `altdata.sources.yfinance_source`, 1927-12-30 to 2026-11-05); FRED DTB3 (FRED fredgraph CSV, 1954-01-04 to 2026-11-04). Data pulled 2026-11-05 22:12 ET (cache `~/.cache/chester-study/tail_days`).

1990-01-02 to 2026-11-05, n = 9,280. The vol-managed rule is Part 3's. The constant mix holds the rule's average exposure, 0.9025, rebalanced at each close; its turnover is the drift back to target. T-bill return: FRED DTB3 at T-1 (discount-basis annual %, carried at most 5 days), compounded to a 252-day year. Sharpe (rf = 0) is Part 3's definition; the next column is the same ratio on returns in excess of DTB3. Worst 20-session = the lowest close-to-close return over any 20 sessions. Costs: 2bp × turnover each day (buy and hold: one purchase). Price return, no dividends, as Part 3.

| Strategy | costs | Ann. return (CAGR) | Ann. vol | Sharpe (rf = 0) | Sharpe (excess of DTB3) | Max drawdown | Worst 20-session | Avg exposure | Ann. turnover |
|---|---|---|---|---|---|---|---|---|---|
| Buy and hold | none | 8.59% | 17.97% | 0.55 | 0.40 | -56.8% | -30.9% | 1.00 | 0.0x |
| Buy and hold | 2bp | 8.59% | 17.97% | 0.55 | 0.40 | -56.8% | -30.9% | 1.00 | 0.0x |
| Vol-managed, cash at zero (Part 3) | none | 6.46% | 12.01% | 0.58 | 0.36 | -36.5% | -11.0% | 0.90 | 9.5x |
| Vol-managed, cash at zero (Part 3) | 2bp | 6.25% | 12.01% | 0.57 | 0.34 | -36.8% | -11.0% | 0.90 | 9.5x |
| Constant mix 0.90, cash at zero | none | 7.88% | 16.21% | 0.55 | 0.38 | -52.7% | -28.2% | 0.90 | 0.2x |
| Constant mix 0.90, cash at zero | 2bp | 7.87% | 16.21% | 0.55 | 0.38 | -52.7% | -28.2% | 0.90 | 0.2x |
| Vol-managed, cash and borrowing at DTB3 | none | 6.68% | 12.01% | 0.60 | 0.38 | -32.7% | -11.0% | 0.90 | 9.5x |
| Vol-managed, cash and borrowing at DTB3 | 2bp | 6.48% | 12.01% | 0.58 | 0.36 | -33.0% | -11.0% | 0.90 | 9.5x |
| Constant mix 0.90, rest in DTB3 | none | 8.16% | 16.21% | 0.56 | 0.40 | -52.6% | -28.2% | 0.90 | 0.2x |
| Constant mix 0.90, rest in DTB3 | 2bp | 8.15% | 16.21% | 0.56 | 0.40 | -52.6% | -28.2% | 0.90 | 0.2x |

### Part 6.1 Vol-managed exposure path, 2026-10-26 to the latest session

RV20 and the exposure it sets are as of each session's close; "held" is the exposure carried through that session (set at the prior close). The last row's set exposure applies to the next session.

| Date | ^GSPC ret | RV20 (ann.) | exposure set at close | exposure held |
|---|---|---|---|---|
| 2026-10-26 | +0.70% | 9.9% | 1.46 | 1.46 |
| 2026-10-27 | +0.60% | 10.1% | 1.41 | 1.46 |
| 2026-10-28 | +0.28% | 10.1% | 1.41 | 1.41 |
| 2026-10-29 | -0.30% | 10.2% | 1.39 | 1.41 |
| 2026-10-30 | -1.82% | 11.8% | 1.04 | 1.39 |
| 2026-11-02 | -0.51% | 11.5% | 1.08 | 1.04 |
| 2026-11-03 | +0.36% | 11.4% | 1.11 | 1.08 |
| 2026-11-04 | +1.58% | 12.9% | 0.86 | 1.11 |
| 2026-11-05 | -4.36% | 20.2% | 0.35 | 0.86 |

## Part 7. Credit substitute: BAA10Y and the excess bond premium

Source: FRED BAA10Y (FRED fredgraph CSV, 1986-01-02 to 2026-11-04); Federal Reserve excess bond premium (FEDS Notes CSV, https://www.federalreserve.gov/econres/notes/feds-notes/ebp_csv.csv, 1973-01 to 2026-10). Data pulled 2026-11-05 22:12 ET (cache `~/.cache/chester-study/tail_days`).

BAA10Y (Moody's seasoned Baa corporate yield less the 10-year Treasury, percent, shown in bp) on the Part 1 calendar: the value at T-k's date, carried at most 5 days. Δ20 = change over the 20 FRED observations before T-1's value. EBP: the Federal Reserve's excess bond premium (Gilchrist–Zakrajšek, percentage points) and GZ spread for the calendar month before T; the CSV is the current vintage, not what was published at the time.

| Tail day | side | BAA10Y T-1 bp | Δ20 at T-1 bp | BAA10Y T-5 bp | BAA10Y T-20 bp | EBP month | EBP pp | GZ spread pp |
|---|---|---|---|---|---|---|---|---|
| 2020-03-16 | worst | 330 | +125 | 293 | 204 | 2020-02 | -0.15 | 1.99 |
| 2020-03-12 | worst | 299 | +94 | 252 | 206 | 2020-02 | -0.15 | 1.99 |
| 2020-03-09 | worst | 255 | +50 | 244 | 205 | 2020-02 | -0.15 | 1.99 |
| 2020-06-11 | worst | 286 | -54 | 299 | 343 | 2020-05 | +0.41 | 2.52 |
| 2025-04-04 | worst | 189 | +30 | 173 | 161 | 2025-03 | -0.00 | 1.12 |
| 2020-03-18 | worst | 349 | +144 | 299 | 205 | 2020-02 | -0.15 | 1.99 |
| 2020-03-11 | worst | 293 | +87 | 247 | 205 | 2020-02 | -0.15 | 1.99 |
| 2025-04-03 | worst | 173 | +16 | 168 | 159 | 2025-03 | -0.00 | 1.12 |
| 2020-04-01 | worst | 393 | +145 | 413 | 247 | 2020-03 | +1.19 | 3.82 |
| 2026-11-05 | worst | 152 | +6 | 149 | 148 | 2026-10 | -0.27 | 1.00 |
| 2025-04-09 | best | 200 | +32 | 173 | 165 | 2025-03 | -0.00 | 1.12 |
| 2020-03-24 | best | 431 | +218 | 349 | 219 | 2020-02 | -0.15 | 1.99 |
| 2020-03-13 | best | 320 | +114 | 255 | 205 | 2020-02 | -0.15 | 1.99 |
| 2020-04-06 | best | 392 | +137 | 389 | 293 | 2020-03 | +1.19 | 3.82 |
| 2020-03-26 | best | 413 | +193 | 401 | 227 | 2020-02 | -0.15 | 1.99 |
| 2020-03-17 | best | 338 | +134 | 293 | 205 | 2020-02 | -0.15 | 1.99 |
| 2022-11-10 | best | 233 | +6 | 219 | 228 | 2022-10 | +0.11 | 1.68 |
| 2018-12-26 | best | 235 | +17 | 226 | 216 | 2018-11 | +0.16 | 1.79 |
| 2020-03-10 | best | 293 | +88 | 248 | 206 | 2020-02 | -0.15 | 1.99 |
| 2020-03-02 | best | 238 | +30 | 213 | 213 | 2020-02 | -0.15 | 1.99 |

Context: BAA10Y since 1990 has median 213bp, 90th percentile 315bp; its last observation is 2026-11-04 at 152bp.

### Part 7.1 Earliest observation FRED serves

| Series | Via | First obs. | Last obs. | n |
|---|---|---|---|---|
| BAMLH0A0HYM2 | FRED fredgraph CSV, pulled 2026-11-05 22:12 ET | 2023-11-06 | 2026-11-04 | 786 |
| BAMLC0A0CM | FRED fredgraph CSV, pulled 2026-11-05 22:12 ET | 2023-11-06 | 2026-11-04 | 785 |
| BAA10Y | FRED fredgraph CSV, pulled 2026-11-05 22:58 ET | 1986-01-02 | 2026-11-04 | 10,211 |

<!-- NEW-PARTS-CHANGE -->
## What the new parts change

Claims in `docs/studies/tail-days-study-2026-11-05.md` (draft 2, commit 73227981) set against Parts 4–7. Hand-written; the script keeps this section when it is re-run.

**Supported**

1. **§3.1: 5 Nov 2026 is an outlier for the VIX era.** Since 1990 there are 93 bottom-1% days (≤ −3.11%); 6 came with VIX < 20 at T-1 and no 2% day in the prior 20 sessions, and 5 Nov 2026 is the only one of the six at −4% or worse (Part 5). The opener class exists (1991, 2007, 2016, 2018, Feb 2020) but at its size the day has no precedent.
2. **§3.3: most of the conditional follow-through is the vol forecast.** On GARCH-standardised returns, P(top within 5 | bottom) falls from 62.8% (raw) to 49.7%, against 41.9% on any day; RV20 gives 51.6% against 41.3%. The two-sided clustering statistic goes from 72.6% against 65.1% shuffled (raw) to 60.3% against 65.1%, below the shuffled baseline (Part 4.1–4.2). What survives is a modest one-way residual (bottom → top, about +8pp over the any-day rate), not two-sided co-location.
3. **§3.4 / 106g(i): vol management is a drawdown tool.** Against a constant mix at the rule's own average exposure (0.90): max drawdown −36.5% against −52.7%, worst 20 sessions −11.0% against −28.2% (Part 6).
4. **§3.6: one −4.4% day cuts the rule from 0.86 to about 0.35.** Exposure set at the 5 Nov close is 0.35 on RV20 of 20.2% (Part 6.1).
5. **106i: FRED's ICE BofA history starts 6 Nov 2023; BAA10Y starts 2 Jan 1986.** Confirmed on the fredgraph CSV pulled 5 Nov 22:12–22:58 ET (Part 7.1). The EBP CSV is reachable (1973-01 to 2026-10).
6. **§3.1 / §2E: credit gave no warning before 5 Nov 2026.** BAA10Y at T-1 was 152bp, +6bp over 20 observations, against a post-1990 median of 213bp; the October 2026 EBP was −0.27 (Part 7). For contrast, BAA10Y had already widened +50bp in 20 observations before 9 Mar 2020 and +16 to +30bp before 3–4 Apr 2025.
7. **§3.2: the 2026 internals were extreme.** At 4 Nov: RSP-SPY 100th percentile of its history, QQQ-SPY 2nd, sector dispersion 99th (Part 5.3).

**Contradicted or qualified**

8. **§0 item 4 and §3.3: "forward returns after a bottom-decile day are at or above the all-day baseline."** True raw (20-day mean +0.93% against +0.69% on the matched sample). After standardising, bottom-decile days are followed by roughly baseline drift (+0.64% against +0.69% raw; +0.11σ against +0.15σ GARCH) and a slightly negative next day (−0.05%, 48% positive). "Above baseline" is a vol-regime artefact; "no worse than baseline" holds. The wider-outcomes claim survives in σ units, more so on RV20 (10th percentile −1.60σ against −1.33σ) than on GARCH (−1.37σ against −1.23σ).
9. **§3.2 / 106c(ii): stressed internals as the tell before an opener.** It held in 2026 only. Before the five earlier openers, RSP-SPY ranged from the 8th to the 96th percentile, sector dispersion from the 17th to the 63rd, and the Amihud 1-year percentile was 2–5 in three of them (liquid, not thin) and 76 in Feb 2020 (Part 5.3). "Calm surface, stressed internals" describes 5 Nov 2026; Part 5's history does not show it as the general signature of an opener.
10. **106c(ii): "no sizing right until its ledger holds 20 openers, which will take years."** At 6 openers in 36 years (one per six years), 20 would take over a century on this definition. The threshold needs a looser opener definition or a different gate.
11. **106e: SPY's Amihud "at its one-year high."** 100th on one year, 72nd on three (Part 5.3), which supports the draft's caveat that the 1-year extreme partly reflects volume migration; the 3-year read is the one to carry.
12. **§3.4: "part of the return gap is simply lower average exposure."** About a third of it: buy and hold 8.59%, the matched constant mix 7.88%, vol-managed 6.46% (cash at zero). The rule gives up a further 1.4 points a year beyond its exposure level. On returns in excess of T-bills its Sharpe is lower than both (0.38 against 0.40 with cash and the mix both at DTB3), so 106g(i)'s "about Sharpe-neutral" holds only on Part 3's rf = 0 definition.
13. **106a: "63% vs 38% … and 73% vs 65%" as the printed figures.** They are correct raw, but Part 4 shows they mostly measure vol clustering; the table should print the standardised pair beside them (49.7% against 41.9%; 60.3% against 65.1%).

**Note on Parts 1–3.** This run drops the blank holiday rows that fredgraph's CSV now returns as NaN. That fills a few Part 1 "gap" cells (10yΔ5 and $Δ5% on 2020-03-02 T-5 and 2022-11-10 T-20, among others) and moves some 10y and dollar Δ cells by a few bp or tenths, because Δ-over-n now counts values rather than holiday rows. No figure the draft 2 study quotes changed; Parts 2 and 3 are unchanged.

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
