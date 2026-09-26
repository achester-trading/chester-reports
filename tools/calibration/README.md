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
- **Ledgers are dated.** Output goes to `docs/ledgers/`, dated in the filename,
  one file per run, never edited afterwards.
- **Only live flags read the store.** Nothing in this directory is a writer: no
  script writes to the store, the registry or `config/`. A threshold a ledger
  settles reaches `config/market_state.yaml` through the session that adopts it.

Scripts here are not gates in `make validate` and nothing schedules them; they
are run by hand when their register entry's study is due.
