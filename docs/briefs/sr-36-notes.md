# SR-36 — the Treasury basis-trade proxy (ST-B3-12) and its calibration ledger (ST-B3-14): session notes

Branch `sr-36-basis-proxy` from `origin/aq-3-series-2` at 8c20241. It stacks on
session B's CFTC work (the disaggregated and TFF writer), which this branch
extends rather than duplicates. Spec:

- the SR-36 entry and rows ST-B3-12 and ST-B3-14 of
  `docs/change-order-signal-triage-batch-3-2026-10-02.md`;
- the 6 Oct rulings (§7 decisions 8 and 9);
- Audit #4 Part III row 2.

Session A, 11 Oct 2026.

**Report-only.** No overlay wiring, no trigger and no book rule. Daily wiring
waits for D4/D6, as the order says.

**Not run:** the full local suite (CI is the validate), and anything on the box.
The gates this branch touches were run one at a time, all green:

| Gate | Result |
|---|---|
| `validate_basis_proxy` (new) | 31/0 |
| `validate_aq3_series` | 73/0 |
| `validate_weekly_stack` | 68/0 |
| `validate_weekly` | 100/0 |
| `validate_weekly_edits` | 89/0 |
| `validate_weekly_complete` | 56/0 |
| `validate_stack` | 66/0 |
| `validate_stack_cadence` | 99/0 |
| `validate_readability` | 63/0 |
| `validate_monthly_stack` | 261/0 |
| `validate_figure_budget` | 79/0 |
| `validate_daily_close` | 102/0 |
| `validate_config_refs` | 25/0 |
| `validate_gates` | 31/0 |
| `check_registry` | OK |
| `check_library` | 0 failures |

## What was built

### The writer

`altdata/sources/cftc.py` is session B's TFF writer, extended, not a second one.
`TFF_CONTRACTS` gains the six CBOT Treasury futures, with codes read from the
CFTC's `gpe5-46if` dataset on 11 Oct:

| Ticker | Code |
|---|---|
| TU | 042601 |
| FV | 044601 |
| TY | 043602 |
| TN | 043607 |
| US | 020601 |
| WN | 020604 |

- **Instrument.** Each row is stored under the CME ticker. The existing
  `cftc.tff_*` keys carry it: long, short, net and their `_oi` shares for
  dealers, asset managers, leveraged funds and other reportables, plus open
  interest.
- **The registry.** Descriptions now name the Treasuries. No new keys were
  added.
- **The backfill.** The writer reads each contract's whole history on every
  pull, so the next scheduled CFTC pull is the backfill. The API serves
  2006-06-13 onward for TU, FV, TY and US, WN from 2010-03-02, and TN from
  2016-03-08.
- **Code 020604** printed "LONG-TERM U.S. TREASURY BONDS" from 2010 to 2016.
  That is the Ultra bond under its launch name. It is noted at the code.

### The proxy

`altdata/basis_proxy.py`, with `config/basis_proxy.yaml`.

- **(a) The leveraged-fund net short.** Summed across the six contracts as a
  share of their combined open interest, both contract-weighted and
  DV01-weighted.
  - DV01 per contract is a config table, labelled "CTD-duration approximation,
    session-set 11 Oct 2026". It is computed as notional × the CTD's approximate
    modified duration × 0.0001, with the CTD taken at par.
  - CME publishes contract specifications, not a standing DV01.
- **(b) The asset-manager net long**, the mirror, with the same two weightings.
- **(c)** Both shares per contract.
- **(d) The OI-change read.** This is a code-written label: the week's change in
  the aggregate leveraged net short against the change in open interest. A
  change under 1% of the prior level is flat.

  | Short | OI | Label |
  |---|---|---|
  | Down | Down | deleveraging |
  | Down | Flat or up | covering |
  | Up | Up | building |
  | Up | Flat or down | adding |
  | Flat | — | unchanged |

- **(e) Percentiles.** Five-year and full history, both for the aggregate and
  for the 10-year.
- **The tiers** (ruled 6 Oct).
  - **The 10-year:** 35% elevated, 40% extreme.
  - **The aggregate:** its own full-history 90th and 97th percentiles, nearest
    rank, computed from the history knowable that week. They are never fixed
    numbers.
- **The basis-unwind watch: a coincidence flag only.** It needs a level flag on
  either series plus at least two of the four co-signals:
  - **SR-35**, hooked by name: `altdata.move_screen.companion_10y`, from
    c1-move-screen. It is absent on this branch until that merges.
  - **MOVE's** 21-session change at 2σ against five years of such changes.
  - **SOFR less IORB:** the 10-session widening at 2σ. The sponsored-repo
    volume series is not stored.
  - **The 10-year swap spread's** two-week change: absent, because no swap
    spread is stored.

  A co-signal that is absent is named and never counts either way.

### The two Weekly lines

These are code-written, never prose, and each ends "(descriptive; unvalidated,
n=0)".

- **Positioning & flows:** under the CFTC table, the 10-year and six-contract
  shares with their tiers, the full-history percentile and the OI read. The
  line is four figures.
- **Plumbing & rates:** a one-line sub-section with the watch, its level flag,
  the co-signals that are on and the ones that are absent. The line is three
  figures.

Both lines fit inside the Weekly's cap of six figures, and each section's data
carries what its line prints.

### The fence

- **The rule.** `stack_prose.basis_faults`, run inside `style_faults` so every
  paragraph check (close, Weekly, Monthly) applies it, withholds a sentence
  matching the config's `banned_patterns`. Those cover "hedge funds are short
  bonds", funds or speculators "are short" Treasuries or duration, a bet on
  yields, and a squeeze.
- **The frame.** `BASIS_NOTE` is in the Positioning and Plumbing frames. It
  states the fragility reading and the ban.

### The gate

`tools/validate_basis_proxy.py` runs on a synthetic TFF history, stored through
the writer's own `category_rows`. It checks:

- the writer's codes;
- the share arithmetic, both weightings and per contract, by hand;
- the tiers at and just under each line;
- the OI read's four cases and the flat one;
- the coincidence flag: a level flag plus two is on, plus one is off, and four
  with no level flag is off;
- the absent co-signals named;
- the two Weekly lines inside the budget with the tag;
- the banned readings withheld and the fragility reading passed;
- the ledger's led, coincided and lagged lines, and four dated episodes.

The gate is in the Makefile, and CLAUDE.md now reads forty-eight code gates.

## The calibration ledger

The full dated tables, session by session through each episode, are in
`docs/briefs/sr-36-calibration-ledger.md`. That file is generated by `python -m
altdata.basis_proxy ledger`.

**Provenance.** The box's store does not hold the TFF Treasuries yet: B's writer
is new, and this branch adds the contracts. So the ledger was computed on the
laptop on 11 Oct, from a scratch store loaded that evening from public sources:

| Series | Source |
|---|---|
| TFF | The CFTC API, parsed by the writer's own `category_rows` |
| MOVE | Yahoo `^MOVE` |
| SOFR | The New York Fed's API |
| IORB | The Federal Reserve Board's PRATES release (RESBM_N.D) |
| The 10-year yield | The Board's H.15 (RIFLGFCY10_N.B) |

- IORB and the 10-year come from the Board, which is FRED's source;
  fred.stlouisfed.org did not answer from the laptop.
- SR-35 came from c1-move-screen's `move_screen.py`, loaded by path and not
  copied into this tree.
- Nothing came from the box.
- The box reproduces the ledger after its next CFTC pull, once c1-move-screen is
  merged.

**Checks against the order's own figures.** The 10-year leveraged net short
reads 44.9% of OI on 26 Aug 2025; the order says ~45%, the record. It reads
35.9% on 29 Sep 2026; the order says ~36%.

| Episode | Weeks | Level flag first | First stress reading | Unwind watch first | Weeks ON |
|---|---|---|---|---|---|
| March 2020 (7 Jan – 26 May 2020) | 21 | 2020-01-07 | 2020-02-25 | 2020-03-03 | 1 |
| April 2025 (25 Feb – 24 Jun 2025) | 18 | 2025-02-25 | 2025-04-01 | — | 0 |
| Aug–Oct 2025 (1 Jul – 25 Nov 2025) | 22 | 2025-07-01 | 2025-07-01 | — | 0 |
| The 2026 compression (6 Jan – 6 Oct 2026) | 40 | 2026-01-06 | 2026-03-24 | 2026-09-29 | 1 |

The four episode lines, as the ledger prints them:

- **March 2020:** the unwind-watch flag lagged the stress readings: flag first on 2020-03-03, first stress reading 2020-02-25; level flag first on 2020-01-07 (absent: SOFR less IORB, the swap spread).
- **April 2025:** the unwind-watch flag did not fire; first stress reading 2025-04-01; level flag first on 2025-02-25 (absent: the swap spread).
- **Aug-Oct 2025 (the record and the ease):** the unwind-watch flag did not fire; first stress reading 2025-07-01; level flag first on 2025-07-01 (absent: the swap spread).
- **The 2026 compression:** the unwind-watch flag lagged the stress readings: flag first on 2026-09-29, first stress reading 2026-03-24; level flag first on 2026-01-06 (absent: the swap spread).

No reading beyond those lines. Whether the overlay queue entry exists is the
operator's call under ruling 9.

## Choices made for the operator to overrule

- **The DV01 table is session-set**, a CTD-duration approximation:

  | Contract | DV01, $ per bp |
  |---|---|
  | TU | 38 |
  | FV | 42 |
  | TY | 62 |
  | TN | 85 |
  | US | 120 |
  | WN | 190 |

  These are not CME figures, and they are fixed rather than tracking the CTD.
  The DV01-weighted share prints beside the contract-weighted one.
- **The aggregate's tier is on the contract-weighted share**, the one that
  compares with the 10-year's share of OI. The DV01-weighted share is printed
  but not tiered.
- **Its full history starts 2 Mar 2010**, the first week with WN. The
  aggregate is five contracts until TN joins on 8 Mar 2016.
- **The OI read uses the net short**, not the gross. It is the same series the
  shares are made of.
- **"Stress readings" in the ledger's line are MOVE, SOFR less IORB and the swap
  spread at 2σ.** The Liquidity & Funding Stress overlay is not built, so its
  "own stress readings" have no code. SR-35 counts toward the watch but not as a
  stress reading.
- **An episode's "first" is the first report Tuesday in its window.** A stress
  reading already present when the window opens counts at the window's first
  week. That is what happened in Aug–Oct 2025, where the window opens with SOFR
  less IORB at 2σ.
- **The funding co-signal fires on quarter-end SOFR prints.** April 2025's first
  stress reading, 1 Apr, is the 31 Mar quarter-end. The rule as written does not
  exclude month- or quarter-end sessions.
- **The 10-year can read above the "record".** It reads 48.5% on 2 Sep 2025,
  above the cited ~45%: open interest drops at the September roll. The tier
  reads the share as printed.
- **Only stored series count.** IORB starts 29 Jul 2021, so March 2020 has no
  funding read. IOER was not stored under the IORB key.

## Needs you

1. **Keep the session-set DV01 table?** The alternative is your own figures per
   contract. Yes / no.
2. **Exclude month- and quarter-end sessions from the SOFR-less-IORB
   co-signal?** Yes / no.
3. **Store IOER (2008–2021) as its own series**, so March 2020 has a funding
   read beside SOFR? Yes / no.
4. **Source a 10-year swap spread**, so the fourth co-signal can exist? It is
   absent in every episode today. Yes / no.
5. **Tier the aggregate on the contract-weighted share, as built?** The
   alternative is the DV01-weighted one. Yes / no.
