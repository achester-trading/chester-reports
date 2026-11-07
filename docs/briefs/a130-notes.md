# A130 notes: DTH-1's constant-dollar-risk sizing (item 124g(ii); D63's D8)

Paste A130, 6 Nov 2026, session A. Branch `a130-item-124-dth1-sizing` from `origin/main` at `ee04ba21`, which includes b114-names-sweep's merge. The paste is `23bcf7f3`. Merges Monday in chain-13.

## Orders

- **Batch 23 item 124g(ii)** (the body's 106g(ii)), on `origin/b129-five-filings`.
- **The day-trading rules' rule 8.** Until paste B140 files that order (branch `b140-dth1-rules`), it is the operator's chat ruling D63's D8: "structure sets the stop; the ATR multiple is its floor; size = fixed dollar risk / stop distance".
- **a92's DTH-1 pieces**, read first: `docs/briefs/a92-notes.md`, `config/dth1.yaml`, `altdata/dth1_ledger.py`, the 07:00 anchor's checklist in `daily_cascade/morning_payload.py` and `morning_render.py`, and `tools/validate_dth1.py`.

## The module's interface (`altdata/dth1_sizing.py`)

| Function | What it returns |
|---|---|
| `account_base(path=None, on=None, cfg=None)` | `{base, as_of, file}` from the newest dated row on or before `on`, read by header name (date; account_base / base / equity / account_value); otherwise `{reason, file}`: "account base not found in chester-cards (dth1-account-base.csv)", a missing column named, or no dated row |
| `atr(daily, n=14)` | `(ATR, n)`: the mean of the last n true ranges (`daily_cascade/volatile_day.true_ranges`) |
| `atr_from_store(day, cutoff, db_path, n=14)` | `{atr, n}` from ES's complete sessions before `day`, through the volatile-day flag's own reader (`volatile_day._es_inputs`); `{atr: None, reason}` otherwise |
| `vol_state_k()` | None: 124c(i)'s vol state is not built. It is the hook that will set k |
| `k_value(cfg)` | `(k, source)`: the vol state's when built, else config's 1.0 with "the vol state (124c(i)): not built" |
| `stop_distance(structural, atr, k)` | `{distance, floor, floor_applied}`: max(structural, k × ATR); the floor alone with no stop named; the structural stop alone, "unfloored", with no ATR |
| `contracts(risk_usd, distance, cfg, instrument="ES")` | `{instrument, contracts, risk_at_size}`: floor(risk ÷ (distance × point value)); MES (`rounded_from: ES`) when ES rounds to zero; "below one MES contract" when MES does too; "no base" without a risk |
| `size(base, atr, structural=None, instrument="ES", cfg=None)` | the whole computation for one stop: risk, daily limit, k, floor, distance, contracts |
| `plan_block(day, cutoff, db_path, base_path=None, cfg=None)` | the anchor's block: `{enabled, title, lines, table}` |
| `plan_text(block)`, `plan_html(block)` | the two editions |
| CLI: `python -m altdata.dth1_sizing [--date D]` | prints the day's block |
| CLI: `python -m altdata.dth1_sizing --stop POINTS [--instrument ES\|MES]` | sizes one stop |

**Config** (`config/dth1.yaml` `sizing`, every value session-set):

| Setting | Value |
|---|---|
| `risk_fraction` | 0.01 |
| `daily_limit_fraction` | 0.02 |
| `atr_sessions` | 14 |
| `k` | 1.0 |
| `candidates_atr` | [1.0, 1.5, 2.0] |
| `point_value` | ES 50, MES 5 |
| `base_path` | `~/chester-data/inbox/cards/dth1-account-base.csv` |

**Where the base comes from.** The paste puts the base in the Drive ledger folder, chester-cards. The nightly sweep already copies that whole folder into the cards inbox (`scripts/rclone_sync.sh`, `pull_folder chester-cards cards`, from A92b). The file therefore arrives with no change to the sweep or to `validate_backup`'s list of named files. It is never read from the repo.

**No order path.** The module imports no broker, order, register or `paper_exec` module, and uses no order identifier. The gate proves this from the source and in a fresh interpreter, on validate_alpha_no_orders' pattern.

## The plan block's print on the fixture

These figures are invented, the gate's synthetic fixture: a base of 50,000 as of 6 Nov and an ATR of 20.00 over 14 sessions.

```
DTH-1 sizing (constant dollar risk)
  Risk per trade $500 (1% of the base as of 2026-11-06); daily limit $1,000 (2%).
  ES ATR(14) 20.00 points (n=14); the floor is k x ATR = 20.00 points (k 1: config, session-set; the vol state (124c(i)): not built). The stop is the structure's, never tighter than the floor.
  Stop distance (points) | ES contracts | MES contracts | Risk at that size
  1 x ATR = 20.00 | 0 (MES below) | 5 | $500
  1.5 x ATR = 30.00 | 0 (MES below) | 3 | $450
  2 x ATR = 40.00 | 0 (MES below) | 2 | $400
  Sizes only: nothing here places an order; the stop is the structure's.
```

With no base file, the block is one line: "account base not found in chester-cards (dth1-account-base.csv)". It prints after a92's checklist, in both the HTML and the text edition. The base figure itself is never printed; the gate checks that.

## D41 and this paste

D41 (A92) put sizes "on the chat-side card only, never in a box report". 124g(ii) explicitly orders the 07:00 plan's DTH-1 block to print the sizing table, with risk in dollars from the base. That supersedes D41 for this block only, and `config/dth1.yaml`'s header says so. The rest of D41 stands:
- the Weekly prints aggregates only;
- no trade, entry or order appears in any box report;
- the ledger never enters the repo.

## The manual ledger's two columns

- **`atr_at_entry`:** documented in the canonical header, never read or printed.
- **`floor_applied`:** read when the column exists. The Weekly's aggregate line adds "The ATR floor set the stop in k of n." Without the column, nothing is printed.

Both are nullable. The operator may fill them.

## Item 3: the halve-size line

**No line retired.** a92 carried no "halve size after a bottom-decile day" rule: not in `config/dth1.yaml`'s checklist, not in `altdata/dth1_ledger.py`, not in a92's notes. Gate group G holds that.

The volatile-day protocol's "all sizes halved" (Doctrine 5.5, `config/vol_event.yaml`) is a different rule: it fires on the volatile-day flag, not on a bottom-decile day. It was printed and never applied, and is untouched here.

## Gates (one at a time, foreground)

| Gate | Result |
|---|---|
| validate_item_124_g2 | 40/0 |
| validate_dth1 (a92's) | 27/0 |
| validate_morning_anchor (a92's other gate: the checklist in the anchor) | 71/0 |
| validate_alpha_no_orders | 76/0 |
| validate_ibkr_portfolio | 63/0 |
| check_registry | OK |
| validate_gates | 32/0 |
| check_library | 27 papers, 0 failures, 0 warnings |

Also run, all clean: validate_audit_3a 88/0, validate_names 20/0, validate_secrets 58/0, validate_weekly_stack 83/0, validate_config_refs 148/0, validate_numeral_audit 181/0, validate_backup 89/0, validate_outliers 37/0.

**Counts** (`stitch_counts.py --write`): 168 code gates (165 Python, 3 shell), 8 data gates.

## Box steps (the operator's)

1. Put `dth1-account-base.csv` in the private Drive folder chester-cards, with header `date,account_base` and one row per change of base. The nightly sweep's cards copy brings it to `~/chester-data/inbox/cards/`.
2. Until it lands, the 07:00 block prints "account base not found in chester-cards (dth1-account-base.csv)".
3. To see the table first: `python -m altdata.dth1_sizing --date <D>` (read-only).
