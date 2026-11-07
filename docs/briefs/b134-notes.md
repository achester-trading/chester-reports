# B134: item 124c(i), the vol-state read (6 Nov 2026)

Paste B134 (`docs/pastes/B134.md`). Batch 23 item 124c(i) (the order's 106c(i))
on `origin/b129-five-filings`. Its rights are a daily line and the sizing input to
item 124g. There is no regime, no dial and no composite.

**The base.** `origin/main` at `ee04ba21`. `b134-item-124-vol-state` is a new
branch from it.

## What was built

- **`altdata/vol_state.py`** has five inputs, each a percentile over its own
  stored history (expanding, point in time, with 252 values needed):
  - VIX: `fred.vix`, with Yahoo's `yfinance.mkt_vix` filling the close's own
    day before FRED publishes; FRED wins wherever both exist;
  - the S&P 500's 20-day realised vol, from `yfinance.mkt_gspc`;
  - VIX/VIX3M, from `yfinance.mkt_vix3m`, from 2007;
  - VVIX, from `yfinance.mkt_vvix`, from 2012;
  - the count of |return| ≥ 2% sessions in the last 20.
- **The rule** (`config/vol_state.yaml`, session-set) takes the unweighted mean of
  the available percentiles, at least two of them. The decile is its bin. No
  weight is fitted.
- **The stored keys** (source `calc`) are:
  - `calc.vol_state.decile`;
  - `calc.vol_state.vix_pct`, `rv20_pct`, `term_pct`, `vvix_pct` and
    `bigmove_pct`.

  They are computed in the features pass after the trend breadth, over recent
  days only; the history is `python -m altdata.vol_state backfill`, the
  operator's to run, dry run first. They are registered under the new mechanism
  group `vol_state` and barred from the market-state object (`calc.vol_state.*`
  in `market_state_barred`).
- **The ledger**, `docs/ledgers/vol-state-calibration-2026-11.md`, is written
  once by `python -m altdata.vol_state ledger`.
  - Its head is pre-registered, with the computation's SHA-256
    `be6efc27ab14f9cc9fd8bb2c4f5297e3c5a85c19fe2c2c77e3b23bffefad6ddd`.
  - The laptop's store holds none of the five keys, so this edition is the
    public run: Yahoo through the writer's reader and FRED's graph CSV, through
    5 Nov 2026. The box's run from the store would be a new dated file.
  - Its config table is copied into `config/vol_state.yaml`
    `calibration.deciles`, and the gate holds the two equal.
- **The print** (`daily_cascade/vol_state_block.py`):
  - **The close:** one Mechanics block after item 52's (and after item 65's,
    which sits directly after it), every session. It holds:
    - the decile;
    - the five inputs with their percentiles and windows;
    - P(|r| ≥ 3% within 10) for this decile, with its n and interval;
    - the 5- and 20-session transition odds;
    - the hook's ATR multiple.
  - **The Weekly:** one row of the week's deciles.
- **The hook.** `vol_state_k(decile)` returns config's ATR multiple, and None
  with no state.
  - A130's module is not on any remote branch yet, so this builds the provider
    it will read by that name.
- **The window label.** A126's `derived.window_label` is on A126's branch, not
  main. The block calls it when it exists (chain-13 merges A126 first) and
  otherwise prints the same full-history words.

## The calibration (from 1990; as of 5 Nov 2026; unconditional 11.4%)

| Decile | n | P(\|r\| ≥ 3% within 10) | 95% interval | Same decile, 5 on / 20 on |
|---|---|---|---|---|
| 1 | 0 | n/a | | |
| 2 | 106 | 2.8% | 1.0–8.0% | 33% / 10% |
| 3 | 1,338 | 1.9% | 1.3–2.7% | 64% / 41% |
| 4 | 1,543 | 0.9% | 0.5–1.5% | 50% / 32% |
| 5 | 1,234 | 2.0% | 1.4–3.0% | 42% / 23% |
| 6 | 1,118 | 4.7% | 3.6–6.1% | 41% / 20% |
| 7 | 1,001 | 7.3% | 5.8–9.1% | 42% / 22% |
| 8 | 817 | 20.4% | 17.8–23.3% | 39% / 17% |
| 9 | 924 | 25.8% | 23.0–28.7% | 49% / 27% |
| 10 | 938 | 46.3% | 43.1–49.5% | 74% / 50% |

**Decile 1 is empty.** A mean of five percentiles never falls below 10, so the
declared bins leave it unused, and the low deciles are thin (decile 2 has 106
sessions). Ranking the score against its own history would spread the deciles
evenly. That is a rule change for the operator, not a fit, so it is left as
declared and flagged here.

**The state on 5 Nov 2026** was decile 9 (score 87.7). Its percentiles: VIX 89,
realised vol 81, VIX/VIX3M 97, VVIX 98, big-move count 73. The hook gives 2.5.
That is from the public series; the stored state begins when the operator runs
the backfill.

## The hook's table (session-set)

| Decile | 1–5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|
| ATR multiple | 1.5 | 1.75 | 2.0 | 2.25 | 2.5 | 3.0 |

## The gates

| Gate | Result |
|---|---|
| `validate_item_124_c1` (new; clock pinned) | 42 passed, 0 failed |
| `validate_vol_event` | PASSED |
| `validate_stack` (in full: its groups are letters, not section names) | 84 passed, 0 failed |
| `validate_weekly_stack` (in full) | 83 passed, 0 failed |
| `check_registry` | OK |
| `validate_gates` | 32 passed, 0 failed |
| `check_library` | 27 papers, 0 failures, 0 warnings |

Run as well, because the edits touch them: `validate_audit_3a` 88/0,
`validate_regime` 524/0, `validate_monthly_stack` 268/0,
`validate_trend_breadth` 42/0 and `validate_batch14_b1` 68/0.

**One file outside the paste's list.** `validate_audit_3a` holds CLAUDE.md's
gate count, so CLAUDE.md's count moves from 167 to 168 code gates (165 Python).
Nothing else in CLAUDE.md changed.

**Also touched:**
- `config/catalogue_commands.yaml`, one line for `altdata.vol_state`;
- `altdata/market_features.py`, the features-pass call;
- `daily_cascade/stack.py` and `daily_cascade/weekly_stack.py`, the two print
  calls.

## A correction to B133's notes

B133's notes say `validate_narratives` "is not in the Makefile's list under that
name". It is a listed gate: gates declare themselves with `GATE_KIND`, and
`tools/gate_list.py` builds the list from those declarations. The B133 branch
was not pushed a second time to fix the line.

## CI

Read once after the push.

**B142.** CI run 42325423633 was red on `check_master_guide`:
"[ledgers] vol-state-calibration-2026-11.md is not in Table 7". Its row is now in
Table 7a, verdict "diagnostic" (the ledger prints no verdict row: its pass rule is
"none"). The Guide's "As of" line is left for chain-13's refresh.
