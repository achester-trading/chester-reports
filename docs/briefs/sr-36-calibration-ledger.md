# SR-36 calibration ledger (ST-B3-14)

Generated 2026-10-11 by `python -m altdata.basis_proxy ledger`. Computed on 11 Oct 2026 on the laptop, from a scratch store loaded that evening from the public sources -- the CFTC TFF API (gpe5-46if, through altdata/sources/cftc.py's own category_rows), MOVE from Yahoo (^MOVE), SOFR from the New York Fed's API, IORB and the 10-year constant-maturity yield from the Federal Reserve Board's data download (PRATES RESBM_N.D; H.15 RIFLGFCY10_N.B -- the sources FRED republishes; fred.stlouisfed.org did not answer from the laptop) -- with c1-move-screen's altdata.move_screen loaded by path for SR-35. Nothing from the box. The box reproduces it after the first TFF pull with `python -m altdata.basis_proxy ledger` once c1-move-screen is merged. IORB starts 29 Jul 2021, so SOFR less IORB is absent in March 2020; no 10-year swap spread is stored.

Shares are the leveraged-fund net short as a percent of open interest (contract-weighted; DV01-weighted in brackets); percentiles are over the full history since 2010 knowable that week. Tiers per the 6 Oct ruling. Co-signal cells are the z of the change at that report Tuesday; ✓ is at 2σ (the swap spread either way). Descriptive; unvalidated, n=0.

## March 2020

**March 2020:** the unwind-watch flag lagged the stress readings: flag first on 2020-03-03, first stress reading 2020-02-25; level flag first on 2020-01-07 (absent: SOFR less IORB, the swap spread).

| Report Tuesday | Six-contract share | Pctile | Tier | 10-year share | Pctile | Tier | OI read | SR-35 | MOVE 1m | SOFR–IORB 2w | Swap spread | Watch |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2020-01-07 | 24.1% (27.6%) | 90th | elevated | 18.4% | 82nd | — | adding | no | -0.1σ | absent | absent | off |
| 2020-01-14 | 23.6% (27.3%) | 90th | — | 20.4% | 86th | — | covering | no | -1.0σ | absent | absent | off |
| 2020-01-21 | 23.5% (27.2%) | 89th | — | 21.4% | 89th | — | unchanged | no | +0.1σ | absent | absent | off |
| 2020-01-28 | 23.0% (26.4%) | 88th | — | 19.7% | 84th | — | unchanged | no | +1.1σ | absent | absent | off |
| 2020-02-04 | 22.7% (26.0%) | 88th | — | 20.1% | 85th | — | building | no | +0.9σ | absent | absent | off |
| 2020-02-11 | 22.8% (25.8%) | 88th | — | 19.1% | 83rd | — | building | no | +1.3σ | absent | absent | off |
| 2020-02-18 | 22.7% (25.6%) | 88th | — | 16.9% | 79th | — | building | no | +1.9σ | absent | absent | off |
| 2020-02-25 | 21.4% (23.8%) | 86th | — | 16.5% | 78th | — | covering | no | +3.0σ ✓ | absent | absent | off |
| 2020-03-03 | 23.9% (26.9%) | 90th | elevated | 19.1% | 83rd | — | adding | ✓ | +3.2σ ✓ | absent | absent | ON |
| 2020-03-10 | 21.5% (24.9%) | 86th | — | 18.5% | 81st | — | deleveraging | ✓ | +5.7σ ✓ | absent | absent | off |
| 2020-03-17 | 21.5% (24.5%) | 86th | — | 18.3% | 81st | — | deleveraging | ✓ | +4.3σ ✓ | absent | absent | off |
| 2020-03-24 | 21.8% (24.2%) | 87th | — | 20.2% | 86th | — | deleveraging | ✓ | +2.0σ ✓ | absent | absent | off |
| 2020-03-31 | 22.3% (24.2%) | 87th | — | 17.2% | 79th | — | deleveraging | no | -1.9σ | absent | absent | off |
| 2020-04-07 | 20.7% (23.4%) | 84th | — | 16.0% | 77th | — | deleveraging | no | -7.8σ | absent | absent | off |
| 2020-04-14 | 20.5% (23.0%) | 84th | — | 16.0% | 77th | — | covering | no | -5.5σ | absent | absent | off |
| 2020-04-21 | 21.0% (23.5%) | 85th | — | 15.7% | 76th | — | adding | no | -4.6σ | absent | absent | off |
| 2020-04-28 | 21.0% (23.1%) | 85th | — | 15.3% | 76th | — | unchanged | no | -2.2σ | absent | absent | off |
| 2020-05-05 | 21.9% (24.0%) | 87th | — | 18.0% | 81st | — | adding | no | -1.1σ | absent | absent | off |
| 2020-05-12 | 21.9% (23.6%) | 87th | — | 18.8% | 82nd | — | building | no | -1.1σ | absent | absent | off |
| 2020-05-19 | 21.2% (23.0%) | 85th | — | 19.4% | 84th | — | covering | no | -0.7σ | absent | absent | off |
| 2020-05-26 | 18.5% (20.4%) | 82nd | — | 16.3% | 77th | — | covering | no | -1.0σ | absent | absent | off |

## April 2025

**April 2025:** the unwind-watch flag did not fire; first stress reading 2025-04-01; level flag first on 2025-02-25 (absent: the swap spread).

| Report Tuesday | Six-contract share | Pctile | Tier | 10-year share | Pctile | Tier | OI read | SR-35 | MOVE 1m | SOFR–IORB 2w | Swap spread | Watch |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2025-02-25 | 32.1% (27.9%) | 93rd | elevated | 25.5% | 87th | — | covering | no | +0.6σ | -0.7σ | absent | off |
| 2025-03-04 | 37.0% (32.4%) | 97th | elevated | 30.2% | 94th | — | adding | no | +1.0σ | -1.4σ | absent | off |
| 2025-03-11 | 37.1% (32.6%) | 97th | elevated | 30.5% | 94th | — | unchanged | no | +1.2σ | -0.3σ | absent | off |
| 2025-03-18 | 37.6% (32.7%) | 97th | elevated | 32.7% | 96th | — | adding | no | +0.7σ | -0.7σ | absent | off |
| 2025-03-25 | 36.7% (32.2%) | 96th | elevated | 31.6% | 96th | — | covering | no | +0.3σ | +0.3σ | absent | off |
| 2025-04-01 | 38.1% (33.4%) | 97th | extreme | 33.5% | 97th | — | building | no | -0.1σ | +2.6σ ✓ | absent | off |
| 2025-04-08 | 38.5% (34.4%) | 98th | extreme | 38.3% | 98th | elevated | adding | no | +1.6σ | +2.3σ ✓ | absent | off |
| 2025-04-15 | 39.9% (35.3%) | 98th | extreme | 38.0% | 98th | elevated | adding | no | +1.3σ | -1.0σ | absent | off |
| 2025-04-22 | 40.2% (35.5%) | 98th | extreme | 37.6% | 98th | elevated | building | no | +1.4σ | -1.0σ | absent | off |
| 2025-04-29 | 40.3% (35.5%) | 98th | extreme | 37.6% | 98th | elevated | building | no | +0.9σ | +0.9σ | absent | off |
| 2025-05-06 | 40.8% (36.3%) | 99th | extreme | 40.8% | 99th | extreme | building | no | -1.2σ | +0.6σ | absent | off |
| 2025-05-13 | 39.2% (35.3%) | 97th | extreme | 37.6% | 98th | elevated | covering | no | -2.3σ | -1.9σ | absent | off |
| 2025-05-20 | 38.4% (34.7%) | 97th | elevated | 37.2% | 97th | elevated | unchanged | no | -1.7σ | -1.6σ | absent | off |
| 2025-05-27 | 37.4% (32.7%) | 96th | elevated | 36.7% | 97th | elevated | covering | no | -0.5σ | +0.9σ | absent | off |
| 2025-06-03 | 39.9% (34.7%) | 98th | extreme | 40.9% | 99th | extreme | unchanged | no | -0.1σ | +0.9σ | absent | off |
| 2025-06-10 | 40.2% (34.5%) | 98th | extreme | 41.1% | 99th | extreme | unchanged | no | -0.6σ | -0.9σ | absent | off |
| 2025-06-17 | 39.6% (34.0%) | 97th | extreme | 41.8% | 99th | extreme | unchanged | no | -0.0σ | -0.3σ | absent | off |
| 2025-06-24 | 39.6% (34.2%) | 97th | extreme | 38.9% | 98th | elevated | building | no | -0.5σ | +0.3σ | absent | off |

## Aug-Oct 2025 (the record and the ease)

**Aug-Oct 2025 (the record and the ease):** the unwind-watch flag did not fire; first stress reading 2025-07-01; level flag first on 2025-07-01 (absent: the swap spread).

| Report Tuesday | Six-contract share | Pctile | Tier | 10-year share | Pctile | Tier | OI read | SR-35 | MOVE 1m | SOFR–IORB 2w | Swap spread | Watch |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2025-07-01 | 39.5% (34.1%) | 97th | extreme | 40.3% | 98th | extreme | building | no | +0.0σ | +3.6σ ✓ | absent | off |
| 2025-07-08 | 39.7% (34.5%) | 97th | extreme | 41.8% | 100th | extreme | unchanged | no | -0.4σ | +1.5σ | absent | off |
| 2025-07-15 | 39.5% (34.3%) | 97th | elevated | 40.3% | 98th | extreme | unchanged | no | -0.1σ | -2.4σ | absent | off |
| 2025-07-22 | 38.8% (33.6%) | 96th | elevated | 40.0% | 98th | extreme | covering | no | -0.1σ | -1.8σ | absent | off |
| 2025-07-29 | 39.4% (34.3%) | 97th | elevated | 44.3% | 100th | extreme | adding | no | -0.2σ | -0.3σ | absent | off |
| 2025-08-05 | 39.1% (34.3%) | 96th | elevated | 43.8% | 100th | extreme | building | no | -0.0σ | +1.8σ | absent | off |
| 2025-08-12 | 39.3% (34.3%) | 96th | elevated | 43.6% | 100th | extreme | building | no | -0.8σ | -0.0σ | absent | off |
| 2025-08-19 | 39.1% (34.5%) | 96th | elevated | 45.3% | 100th | extreme | unchanged | no | -0.3σ | -0.3σ | absent | off |
| 2025-08-26 | 36.9% (31.9%) | 94th | elevated | 44.9% | 100th | extreme | unchanged | no | -0.3σ | +0.6σ | absent | off |
| 2025-09-02 | 41.9% (37.0%) | 99th | extreme | 48.5% | 100th | extreme | adding | no | +0.1σ | +1.5σ | absent | off |
| 2025-09-09 | 41.1% (35.9%) | 99th | extreme | 45.9% | 100th | extreme | covering | no | +0.1σ | +0.9σ | absent | off |
| 2025-09-16 | 40.4% (35.6%) | 98th | extreme | 44.4% | 100th | extreme | covering | no | -0.0σ | -0.0σ | absent | off |
| 2025-09-23 | 39.4% (34.9%) | 96th | elevated | 42.7% | 99th | extreme | covering | no | -0.2σ | -0.9σ | absent | off |
| 2025-09-30 | 38.1% (33.9%) | 94th | elevated | 41.7% | 98th | extreme | covering | no | -0.1σ | +2.9σ ✓ | absent | off |
| 2025-10-07 | 39.1% (34.7%) | 95th | elevated | 42.9% | 99th | extreme | adding | no | -0.5σ | +0.5σ | absent | off |
| 2025-10-14 | 38.7% (34.3%) | 95th | elevated | 43.2% | 99th | extreme | covering | no | +0.4σ | +1.7σ | absent | off |
| 2025-10-21 | 38.9% (34.7%) | 95th | elevated | 43.4% | 99th | extreme | building | no | +0.2σ | +2.2σ ✓ | absent | off |
| 2025-10-28 | 39.0% (34.6%) | 95th | elevated | 42.4% | 98th | extreme | unchanged | no | -0.5σ | +3.3σ ✓ | absent | off |
| 2025-11-04 | 39.2% (34.9%) | 96th | elevated | 42.0% | 98th | extreme | unchanged | no | -0.1σ | +0.5σ | absent | off |
| 2025-11-10 | 38.7% (34.4%) | 95th | elevated | 41.1% | 97th | extreme | unchanged | no | +0.2σ | -1.9σ | absent | off |
| 2025-11-18 | 38.0% (33.9%) | 94th | elevated | 40.9% | 96th | extreme | unchanged | no | +0.2σ | -5.0σ | absent | off |
| 2025-11-25 | 36.8% (32.5%) | 92nd | elevated | 39.0% | 95th | elevated | covering | no | +0.2σ | +1.5σ | absent | off |

## The 2026 compression

**The 2026 compression:** the unwind-watch flag lagged the stress readings: flag first on 2026-09-29, first stress reading 2026-03-24; level flag first on 2026-01-06 (absent: the swap spread).

| Report Tuesday | Six-contract share | Pctile | Tier | 10-year share | Pctile | Tier | OI read | SR-35 | MOVE 1m | SOFR–IORB 2w | Swap spread | Watch |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-01-06 | 39.8% (34.2%) | 97th | elevated | 42.2% | 98th | extreme | unchanged | no | -0.0σ | -0.0σ | absent | off |
| 2026-01-13 | 39.2% (34.1%) | 95th | elevated | 39.8% | 95th | elevated | covering | no | -0.5σ | -3.0σ | absent | off |
| 2026-01-20 | 37.8% (33.3%) | 93rd | elevated | 36.4% | 93rd | elevated | covering | no | +0.2σ | -1.5σ | absent | off |
| 2026-01-27 | 37.1% (33.1%) | 92nd | elevated | 37.9% | 94th | elevated | covering | no | -0.2σ | +0.5σ | absent | off |
| 2026-02-03 | 37.1% (33.0%) | 92nd | elevated | 38.0% | 94th | elevated | unchanged | no | -0.3σ | +1.2σ | absent | off |
| 2026-02-10 | 36.3% (32.6%) | 90th | elevated | 36.9% | 93rd | elevated | covering | no | +0.2σ | -0.3σ | absent | off |
| 2026-02-17 | 35.4% (32.2%) | 90th | — | 36.0% | 92nd | elevated | building | no | +0.8σ | +0.5σ | absent | off |
| 2026-02-24 | 33.4% (29.6%) | 89th | — | 33.3% | 91st | — | covering | no | +0.6σ | +0.9σ | absent | off |
| 2026-03-03 | 36.0% (32.1%) | 90th | elevated | 35.2% | 92nd | elevated | unchanged | no | +1.1σ | -0.3σ | absent | off |
| 2026-03-10 | 35.9% (32.9%) | 90th | elevated | 35.3% | 92nd | elevated | unchanged | no | +0.8σ | -0.8σ | absent | off |
| 2026-03-17 | 36.2% (33.2%) | 90th | elevated | 36.7% | 93rd | elevated | unchanged | no | +0.5σ | -1.2σ | absent | off |
| 2026-03-24 | 35.9% (33.0%) | 90th | — | 35.8% | 92nd | elevated | deleveraging | no | +2.1σ ✓ | -0.3σ | absent | off |
| 2026-03-31 | 35.3% (32.3%) | 89th | — | 38.0% | 94th | elevated | covering | no | +1.3σ | +0.7σ | absent | off |
| 2026-04-07 | 35.0% (32.3%) | 89th | — | 38.6% | 95th | elevated | covering | no | +0.1σ | -0.0σ | absent | off |
| 2026-04-14 | 34.8% (32.4%) | 89th | — | 38.7% | 95th | elevated | unchanged | no | -1.0σ | +0.7σ | absent | off |
| 2026-04-21 | 34.4% (32.0%) | 89th | — | 39.1% | 95th | elevated | unchanged | no | -2.3σ | +0.2σ | absent | off |
| 2026-04-28 | 34.4% (31.9%) | 89th | — | 39.0% | 95th | elevated | unchanged | no | -2.5σ | -0.5σ | absent | off |
| 2026-05-05 | 34.0% (32.0%) | 89th | — | 37.3% | 93rd | elevated | unchanged | no | -0.3σ | -0.3σ | absent | off |
| 2026-05-12 | 31.8% (30.2%) | 86th | — | 33.4% | 90th | — | covering | no | -0.2σ | -1.0σ | absent | off |
| 2026-05-19 | 30.8% (29.4%) | 85th | — | 33.5% | 90th | — | unchanged | no | +1.0σ | -2.7σ | absent | off |
| 2026-05-26 | 28.7% (27.7%) | 80th | — | 32.1% | 89th | — | covering | no | +0.4σ | +0.7σ | absent | off |
| 2026-06-02 | 33.2% (31.5%) | 88th | — | 36.9% | 92nd | elevated | adding | no | +0.1σ | +2.4σ ✓ | absent | off |
| 2026-06-09 | 32.9% (31.4%) | 88th | — | 37.7% | 93rd | elevated | covering | no | +0.6σ | -0.7σ | absent | off |
| 2026-06-16 | 33.0% (31.4%) | 88th | — | 39.1% | 95th | elevated | building | no | -0.7σ | -0.0σ | absent | off |
| 2026-06-23 | 32.4% (30.9%) | 87th | — | 36.8% | 92nd | elevated | unchanged | no | -0.6σ | -0.2σ | absent | off |
| 2026-06-30 | 32.5% (31.2%) | 87th | — | 37.5% | 93rd | elevated | unchanged | no | +0.1σ | -0.2σ | absent | off |
| 2026-07-07 | 33.3% (32.0%) | 88th | — | 37.7% | 93rd | elevated | adding | no | -0.1σ | +0.2σ | absent | off |
| 2026-07-14 | 33.3% (32.2%) | 88th | — | 39.4% | 95th | elevated | unchanged | no | +0.3σ | +0.2σ | absent | off |
| 2026-07-21 | 33.2% (32.2%) | 88th | — | 39.2% | 95th | elevated | covering | no | +0.5σ | -0.2σ | absent | off |
| 2026-07-28 | 32.9% (31.7%) | 87th | — | 40.6% | 96th | extreme | unchanged | no | +0.5σ | +0.5σ | absent | off |
| 2026-08-04 | 32.5% (31.5%) | 87th | — | 42.4% | 98th | extreme | unchanged | no | +0.7σ | +1.2σ | absent | off |
| 2026-08-11 | 31.5% (30.7%) | 85th | — | 39.6% | 95th | elevated | covering | no | -0.0σ | -0.3σ | absent | off |
| 2026-08-18 | 30.6% (30.0%) | 84th | — | 39.8% | 95th | elevated | unchanged | no | +0.1σ | -0.2σ | absent | off |
| 2026-08-25 | 27.0% (25.8%) | 77th | — | 34.4% | 90th | — | covering | no | -0.3σ | +0.5σ | absent | off |
| 2026-09-01 | 31.4% (30.8%) | 85th | — | 39.1% | 94th | elevated | adding | no | -0.2σ | +0.2σ | absent | off |
| 2026-09-08 | 30.3% (29.7%) | 83rd | — | 37.1% | 91st | elevated | covering | no | +0.2σ | -0.3σ | absent | off |
| 2026-09-15 | 28.4% (27.5%) | 78th | — | 34.7% | 89th | — | covering | no | +0.8σ | -1.0σ | absent | off |
| 2026-09-22 | 27.7% (26.9%) | 78th | — | 35.6% | 90th | elevated | unchanged | no | +0.3σ | -0.5σ | absent | off |
| 2026-09-29 | 27.4% (26.9%) | 77th | — | 35.9% | 90th | elevated | unchanged | ✓ | +2.0σ ✓ | -0.2σ | absent | ON |
| 2026-10-06 | 28.3% (26.7%) | 78th | — | 37.3% | 92nd | elevated | adding | no | +1.8σ | +0.7σ | absent | off |

