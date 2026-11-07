# Earnings quality: the flag margin's calibration (Batch 22 item 122, O-3)

**Pre-registered 7 Nov 2026, before the calibration's run** (A134; Batch 22 item 122, the order's 104, and section 0's O-3: "calibrated so the flag fires in both 1999–2000 and 2006–07, false positives reported; if ambiguous, EPS growth at least 10 points above NIPA growth for two quarters running"). This head was committed alone, ahead of the code that runs it. Before writing it the session made one exploratory read of the public series at several whole margins (recorded in `docs/briefs/a134-notes.md`), so this head is not blind to the data; the selection rule below is fixed here, before the run that fills the Result, and is not tuned on that result. A run fills the Result section below the marker and never edits the head; `tools/validate_items_121_122.py` holds the hash printed here equal to `calibration.rule_sha256` in `config/earnings_quality.yaml`. A re-run against later data is a new dated file with this head unchanged.

> The earnings-quality flag's margin (Batch 22 item 122, O-3), pre-registered on 7 Nov 2026 before its run. SERIES: NIPA growth is the year-on-year percent change of FRED CPATAX (corporate profits after tax with IVA and CCAdj, quarterly, the latest vintage). EPS growth is the year-on-year percent change of Shiller's S&P Composite earnings (trailing twelve months, as reported) read at the quarter's last month; S&P operating EPS has no keyless source (S&P DJI's EPS file was withdrawn on 17 Oct 2026 and answers 403), so Shiller's reported series stands in and every print says so. GAP: EPS growth less NIPA growth, in percentage points. FIRE: quarter q fires at margin M when the gap is at least M in q and in the quarter before it (two quarters running). EPISODE: a maximal run of consecutive fired quarters. TARGETS: 1999-2000 (a fired quarter dated 1999Q1 to 2000Q4) and 2006-07 (2006Q1 to 2007Q4). CANDIDATES: M = 5, 6, ..., 30 whole points. ADMISSIBLE: a margin that fires in both targets. FALSE POSITIVE: an episode beginning in 1990Q1 or later none of whose quarters falls in either target window. SELECTION: the admissible margin with the fewest false-positive episodes. AMBIGUOUS: no margin admissible, or the fewest false-positive episodes shared by more than one margin; then the margin is 10 points (O-3) and the Result says why. BEA's domestic nonfinancial profits (FRED A463RC1Q027SBEA) are scored beside it at the chosen margin and never select. Report line and flag only: the flag enters no composite, the market-state object, a dial, a band or a packet.

| | |
|---|---|
| Window | 1990Q1 to the last quarter both series carry |
| Rule | as quoted above |
| Rule SHA-256 | `30174e18250c5c1cc3d85c82914ccae94348505b3170d008d23cfca4739aa8f9` (over the whitespace-normalised text of the quoted rule, as `altdata/earnings_quality.py` `rule_sha256` hashes it) |
| Sources | FRED CPATAX and A463RC1Q027SBEA (fredgraph CSV, keyless); Shiller's ie_data.xls (shillerdata.com) |
| Rights consequence | None. A report line and a flag (the order's Rights); the flag decides nothing. |

<!-- RESULT BELOW. The head above is pre-registered and never edited. -->

## Result

**Edition:** laptop run, 2026-11-07T13:16 UTC, public sources (FRED fredgraph CSV; Shiller's ie_data.xls), never the observation store. Quarters scored 1989Q4 to 2026Q2 (the gap needs both growth rates; the fire needs the quarter before). EPS is Shiller's trailing twelve months as reported, read at the quarter's last month; NIPA is the latest vintage, so the read is not point in time.

**Verdict: the margin is 15 points**, the one admissible margin with the fewest false-positive episodes.

At 15 points: 1999-2000 yes, 2006-07 yes; **4 false-positive episodes since 1990** (1995Q1 to 1995Q2, 2004Q1 to 2004Q3, 2010Q1 to 2011Q3, 2021Q4 to 2022Q2); 6 episodes in all, 19 fired quarters.

Admissible margins (fire in both targets): 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15.

| Margin (pts) | 1999-2000 | 2006-07 | Admissible | Episodes | False positives | Fired quarters |
|---|---|---|---|---|---|---|
| 5 | yes | yes | yes | 10 | 8 | 50 |
| 6 | yes | yes | yes | 10 | 8 | 46 |
| 7 | yes | yes | yes | 11 | 9 | 40 |
| 8 | yes | yes | yes | 11 | 9 | 39 |
| 9 | yes | yes | yes | 11 | 9 | 35 |
| 10 | yes | yes | yes | 11 | 9 | 34 |
| 11 | yes | yes | yes | 9 | 7 | 32 |
| 12 | yes | yes | yes | 9 | 7 | 28 |
| 13 | yes | yes | yes | 7 | 5 | 24 |
| 14 | yes | yes | yes | 7 | 5 | 23 |
| 15 | yes | yes | yes | 6 | 4 | 19 |
| 16 | yes | no | no | 5 | 4 | 16 |
| 17 | yes | no | no | 5 | 4 | 16 |
| 18 | yes | no | no | 5 | 4 | 15 |
| 19 | yes | no | no | 5 | 4 | 15 |
| 20 | yes | no | no | 5 | 4 | 15 |
| 21 | yes | no | no | 5 | 4 | 14 |
| 22 | yes | no | no | 5 | 4 | 14 |
| 23 | yes | no | no | 5 | 4 | 13 |
| 24 | yes | no | no | 4 | 3 | 12 |
| 25 | yes | no | no | 4 | 3 | 12 |
| 26 | yes | no | no | 4 | 3 | 12 |
| 27 | yes | no | no | 4 | 3 | 11 |
| 28 | yes | no | no | 4 | 3 | 10 |
| 29 | yes | no | no | 4 | 3 | 10 |
| 30 | yes | no | no | 4 | 3 | 10 |

**Beside it, never selecting:** BEA's domestic nonfinancial profits at 15 points: 1999-2000 yes, 2006-07 no, 5 false-positive episodes (6 in all).

**Reading the false positives.** Most fire in the first quarters of a recovery, when reported EPS rebounds off write-down-depressed troughs faster than NIPA profits, which exclude those write-downs: a known property of as-reported EPS against NIPA, and one an operating-EPS series would soften. The flag is a report line; it decides nothing.

| Source | URL |
|---|---|
| nipa | https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPATAX |
| nonfin | https://fred.stlouisfed.org/graph/fredgraph.csv?id=A463RC1Q027SBEA |
| eps | https://img1.wsimg.com/blobby/go/e5e77e0b-59d1-44d9-ab25-4763ac982e53/downloads/1449043e-a1ed-4e2e-8e9c-7b9a2a064493/ie_data.xls?ver=1791297298731 |

The per-quarter growth rates and gaps are in `earnings-quality-calibration-2026-11.csv` beside this file.
