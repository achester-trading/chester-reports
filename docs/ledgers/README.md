# Calibration Ledgers

This directory holds the dated results of the offline calibration studies that
gate the entries of the [Signal Triage Register](../signal-triage-register.md).
The rule is §1.10 of the
[signal-triage change order](../change-order-signal-triage-2026-09-25.md)
("Calibration is offline"), signed 2026-09-26.

## The offline-calibration rule

- **Scripts pull full history directly.** Every validation gate runs as a script
  under `tools/calibration/` that fetches the whole history it needs — FRED,
  ALFRED vintages, yfinance, Ken French, TIC archives — straight from the
  source.
- **They never read the observation store as-of.** The store's as-of history
  begins 30 May 2026, the CSV-to-SQLite migration instant, and stays there until
  ALFRED ingestion (O.16) gives the older rows a real `available_at`. Every gate
  in the register needs decades, so a gate that replayed the store would be
  measuring four months.
- **Ledgers are dated.** One file per study, dated in its name
  (`rates-driver-2026-09.md`, `false-bottom-audit-2026.md`). A rerun writes a new dated ledger; an
  old one is never edited to match. The Base Rates paper cites them from its
  dated appendix.
- **Only live flags read the store.** A flag that fires in a report reads the
  observation store as-of, like every other live figure. A ledger does not, and
  a live flag never reads a ledger at run time — thresholds a ledger settles are
  copied into `config/market_state.yaml` by the session that adopts them.

## What every ledger states

Data source and vintage · sample and episodes · statistic · pass or fail against
the gate written in the register entry. A failed gate updates that entry's
status to `DEFERRED — gate failed` with the statistic; a signal that survives
only on revised data is logged here and gets no rights.
