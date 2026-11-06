# FRED and environment check, 5 Nov 2026

Read-only. Code read at `study/tail-days` 07ebeb6c. No code changed and nothing installed or upgraded. Nothing was queried on the box.

## 1. FRED missing days: dropped before any computation? Yes, on every production path

FRED's "." (API) and blank (CSV) rows never reach the observation store (`chester.db`), which every report, flag and percentile reads:
- `altdata/sources/fred.py:96-98` parses "." and "" to None. `altdata/store.py:164` writes only `v is not None` rows to the observation store.
- `altdata/fred_history.py:223-225` (the ALFRED backfill) and `:257` skip None.
- `altdata/observations.py:883-889` (`migrate_csv_store`) skips blanks and NaN.
- `altdata/ledgers/sources.py:41-42` (the calibration ledgers' fredgraph reader) skips "" and ".". `altdata/fx_charts.py:122-130` reads "." as NaN and drops it.

The CSV copy (`data_store/*.csv`) does keep blank rows, for example 8 in `hy_oas.csv`. Its readers (`Store.latest`, `Store.prior_n`, `fred.newest_stored`) all filter None, and no metric computes from it.

How n-day measures count, given the store has no gap rows:
- `derived.derived_forms` deltas (`derived.py:952-962`) step back k NYSE sessions and take the value on or before. Across a bond-market holiday this carries the prior day's value; it never produces a gap.
- `oneday_10y.one_day_changes` (`:68`) and `speed_attribution.attribute` (`:95`, `y[-1-horizon]`) count FRED observations. So a "3-session" move spans one extra calendar day when a bond holiday falls inside it. That is a definition, not a gap bug.
- `tb_harness.trigger` (`:233-247`, HY acceleration) uses calendar-day windows (365 and 30 days).

**Affected metric found: none in production.** The only affected code was `tools/studies/tail_days.py`, which pulled fredgraph directly and kept NaN rows; it was fixed in 07ebeb6c.

## 2. ICE BofA history

**Every reader reads stored history from the observation store; none re-pulls history from FRED per run.** The daily pull is incremental from the newest stored day (`fred.py:106-131`). FRED's window therefore limits only what a store first received. The committed laptop/CI CSVs already start on 2023-05-30 (`hy_oas`, `ig_oas`, `ccc_oas`, `bb_oas`; 794 rows). The `aa`, `bbb`, `aaa`, `em_corp`, `em_hy` and `euro_hy` OAS series are box-only.

| Reader | Window assumed | Over about three years, labelled as |
|---|---|---|
| Credit dimension, `regime.py:349` (`config/market_state.yaml:152`) | 5y (`window_days: 1826`) | No window label printed. **Flag:** it reads as a 5-year percentile. |
| Metric lenses, `derived.py:1280,1360` (spread family long window 20y; `aaa`/`euro_hy` "full") | 5y and 20y | Long form prints "(20y, n=…)". **Flag:** the compact form (`lens_cells.py:69`, used at `:149`) prints "(20y)" with no n. |
| Weekly W-chart `hy20` (`weekly_stack.py:2375`), Monthly M5 (`charts.py:731`) | 20y | Honest: the title says "twenty years asked; the store holds …". |
| T&B HY Spread Acceleration, `tb_harness.py:217-247` (`tb_episodes.yaml:123,159-162`) | 365/30-day rules; `exists_from` 1996 | Honest: unstored episodes print "not stored", and the config names the Baa proxy for them. |
| `vol_event.py:350`, `consistency.py:148`, `macro_6e.py:148`, `absorption.py:408`, `st_r5_rates.py:492-496`, `weekly_sections.py:1399-1405`, move screen (EM OAS) | Level and change; move screen 5y percentile | Short-window reads; the move screen's 5y is filled only if the store is. |
| `tools/calibration/st_r6_59c_bank_stress.py:65` | **Re-pulls** FRED public CSV | Prints "not served" before 2023 (`:264`). |

**Another hazard (CSV copy only).** `fred.pull(full=True)` and the `lookback_days` path pass `merge=False` (`fred.py:254-255`), which rewrites a series' CSV copy with only what FRED serves now. The observation store is append-only and keeps its history.

Run on the VPS (read-only; the DB path is `CHESTER_DB`, else `data/chester.db`):

```
cd ~/chester-reports && .venv/bin/python -c "import sqlite3,os; c=sqlite3.connect('file:'+os.environ.get('CHESTER_DB','data/chester.db')+'?mode=ro',uri=True); [print(*r) for r in c.execute(\"SELECT registry_key, MIN(observed_at), MAX(observed_at), COUNT(*), GROUP_CONCAT(DISTINCT source) FROM observations WHERE registry_key LIKE 'fred.%oas' AND value_num IS NOT NULL GROUP BY registry_key ORDER BY registry_key\")]"
```

## 3. Shared environment (`../chester-reports/.venv`, Python 3.14.3)

- **`pip check`:** "No broken requirements found."
- **Changed on 5 Nov 22:52-22:53 ET** (dist-info and every file dated then): arch 8.0.0, statsmodels 0.15.0, scipy 1.18.1, patsy 1.0.3, formulaic 1.2.2, interface_meta 2.0.1, narwhals 2.28.0, **wrapt 2.6.0.dev1 (a pre-release)**. The filesystem cannot show whether any of these replaced an older version. No other package's dist-info changed; numpy 2.5.2 and pandas 2.3.3 are dated 4 Sep 2026. No repo code imports any of the eight.
- **Against `requirements.txt`** (ranges, no lock file): every listed package installed is in range. These are requests 2.34.2, pandas 2.3.3, python-dateutil 2.9.0.post0, markdown 3.10.3, matplotlib 3.11.1, yfinance 0.2.66, lxml 6.1.3, anthropic 0.125.0, PyYAML 6.0.3, ib_async 2.1.0, xlrd 2.0.2 and jsonschema 4.26.0. **weasyprint is not installed.** That predates this session; the laptop venv cannot build PDFs.
