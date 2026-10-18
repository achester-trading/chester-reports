# tools/calibration/

Offline calibration studies — one script per gate in the Signal Triage Register
(`docs/signal-triage-register.md`), named `sr<nn>_<topic>.py` (for example
`sr06_09_17_driver.py`). The rule is §1.10 of
`docs/change-order-signal-triage-2026-09-25.md`, signed 2026-09-26.

## The offline-calibration rule

- **Scripts pull full history directly** — FRED, ALFRED first-print vintages,
  yfinance, Ken French, TIC archives — from the source, every run.
- **They never read the observation store as-of.** As-of history in the store
  begins 30 May 2026 and stays there until ALFRED ingestion (O.16); every gate
  needs decades. Do not import `ObservationStore`, `regime` or `derived_forms`
  here.
- **No exception remains.** Between 30 Sep and its withdrawal the same day, a
  script could import `regime.driver_cell` so the rates-driver ledger
  calibrated the rule the object ran. The cell and its script are withdrawn
  (the script is in git at `118b552`, beside its two ledgers). A redesigned
  cell starts from a fresh pre-registration and a fresh ruling on what it may
  import. `tools/validate_regime.py` group L fails if any script here opens the
  store or touches `regime`.
- **Ledgers are dated.** Output goes to `docs/ledgers/`, dated in the filename,
  one file per run, never edited afterwards.
- **Only live flags read the store.** Nothing in this directory is a writer: no
  script writes to the store, the registry or `config/`. A threshold a ledger
  settles reaches `config/market_state.yaml` through the session that adopts it.

Scripts here are not gates in `make validate` and nothing schedules them; they
are run by hand when their register entry's study is due.

## The studies

- **ST-7** (st-t2-rates): `sr12_bond_alloc.py`, `sr15_valuation.py`,
  `sr21_divergence.py`, `sr22_auctions.py`, `sr23_net_supply.py`, over
  `st7_common.py`.
- **ST-8** (st-t3-calib): `sr01_sr13_style.py` (two ledgers),
  `sr05_consumer_credit.py` (`--alfred` reads first prints with the key, the
  box edition), `sr14_em_dollar.py`, `sr02_yen_unwind.py`, `sr04_cny_fix.py`,
  over `st8_common.py`. SR-1's rule arithmetic is `altdata/style_regime.py`, the
  one definition its Monthly panel reads too.

A threshold a passing ledger admits goes to config with the ledger named beside
it (`admitted_by:`), by the session that adopts it; `tools/validate_st_t3_calib.py`
refuses a config that names no ledger or one that did not pass.
