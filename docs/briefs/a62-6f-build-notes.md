# A62: 6f tranches 1, 3 and 5, the market-state object v2 (session A)

**Branch-only, overnight. Nothing here merges before the 1 Nov Monthly.** The spec is `docs/briefs/6f-spec-draft-2026-10-24.md`, ruled 24 Oct 2026: all twelve decisions accepted as recommended (D27, `docs/briefs/rulings-2026-10-24.md`). This branch builds:

- tranche 1, the schema and the five buildable dimensions;
- tranche 3, `tail_families` and `debt_cycle_branch`;
- tranche 5, the bar gate.

Tranche 2 (calibration) is A63. Tranche 4 (`alignment_weekly`) waits for the register's schema change.

## Base and commits

- **Base:** `a62-6f-build` from `origin/a61-rulings-1024` at `4a663a3`. It carries chain-6 and the rulings, and its CI was green (runs 40112619226 and 40112648140).
- **The spec:** `origin/a60-6f-spec` (`755d8aa`) merged with one merge commit (`9436b21`), clean.
- **Worktree:** `../chester-a57`. A61b used its own.
- **Security Master:** no new instrument, so no id is taken (from 221, D28, when one is).

| Commit | What |
|---|---|
| `9436b21` | Merge a60-6f-spec. |
| `8e8b210` | Part 0: the spec's status line, "RULED 24 Oct 2026 (D27): all twelve decisions as recommended", and the pointer to the rulings log under section 9. Nothing else in the spec changed. |
| (next) | Parts 1–4: the build, the gate, these notes. |

## The method and config bumps

- **Config:** `market-state-v1.10` → **`market-state-v2.0`**. The spec's v1.13 is folded into this one bump, so the calibration sample (A63) is split once, not twice.
- **Method:** `market-state-method-8` → **`market-state-method-11`**. 9 and 10 stay retired. The source hash is pinned at `1664e465a940aadc` (`python -m regime method --update`), and method-11 is recorded in the audit ledger's method row (`docs/chester-reports-audit-3.md`), which `validate_regime` requires.
- **Schema:** `market-state-v2`. No reader checks the schema string (grep); the only pins were the gates' own (`validate_regime`, and `validate_st_r5_t1_rest`'s v1.10, now v2.0).
- **v1 keeps working.** Every v1 field keeps its name and meaning: the eight dimensions, the three dials (the macro dial still reads growth and inflation only), the eight contradiction rows. The v2 content is additive.
- **Replay.** Objects before method-11 are reported as superseded by the replay gate, and the box re-backfills under method-11 after the merge (the box commands).

## Tranche 1: the schema and the five dimensions (rulings 1a–6a)

**New ways a dimension may be declared** (`regime.compute_dimension`, `score_member`):
- **`transform: change_12m_pct`.** A member read as its change on the observation nearest a year earlier (within 45 days), percent, ranked within the window. Staleness and confidence stay the stored series' own.
- **`window_days: full`, with `also_window_days`.** The full stored history, with the five-year read beside it as `percentile_5y` (ruling 4a).
- **`band_mode: absolute`.** Bands on the primary's LEVEL (`min_value`), ending in a floor no level falls through; members judged on `member_bands` (percentile 66/33 of the same states) (ruling 3a).
- **`buildable: false`, with `not_buildable_reason`.** Declared, absent, saying what it waits for (rulings 1a, 5a).
- **`instrument`** on a member (the CFTC contract, the ETF).

**The dimensions:**

| Dimension | Primary (polarity) | Bands | Members | Fixture read (the gate, by hand) |
|---|---|---|---|---|
| positioning | `finra.margin_debit`, 12-month change (+1) | percentile 66/33 | `cftc.tff_lev_money_net`[TY], `levetf.aum`[TQQQ] | +24.61% on the year: **crowded** |
| sentiment | `aaii.bull_bear_spread` (+1) | percentile 66/33 | `chain.spy_put_call_volume` (−1), `fred.uoM_sent` | at its five-year low: **fearful** |
| valuation | `shiller.cape` (+1), full history | percentile 66/33 | `fred.hh_equity_share` | the 51st percentile of 360 months: **fair**; five-year read 1.7 beside it |
| funding_stress | `calc.sofr_iorb_bp` (+1) | absolute: stressed ≥ 10 bp, watch ≥ 0 | `calc.cp_bill_bp`, `fred.stlfsi`, `tic.fima_repo` | 12 bp: **stressed**; −3 bp calm, 0 bp watch |
| policy | `calc.policy_2y_minus_effr_bp` (+1) | absolute: tightening priced ≥ +25 bp, on hold ≥ −25 | `calc.fed_mkt_gap_12m`, `calc.real_policy_rate` | +30 bp: **tightening priced**; −30 easing, +10 on hold |
| earnings | — | — | — | **not buildable yet**: no public keyless index forward-EPS series (S&P DJI withdrawn 17 Oct) |
| geopolitical | — | — | — | **not buildable yet**: no admitted keyless risk index; GDELT's keys (b59) are report-only by D26 |

**What else changed:**
- **SKEW:** `yfinance.mkt_skew` joins volatility as a member (ruling 2a). There is no tail dimension.
- **The CP-bill series (ruling 6a):** `calc.cp_bill_bp`, financial CP 90-day AA (`fred.fin_cp_3m`) less the 3-month bill (`fred.tbill_3m`), bp. It is computed in `altdata/macro_6e.py` beside `calc.sofr_iorb_bp` (same-day only) and registered. Both legs are already pulled keyless.
- **`horizons{}` (the spec's section 6):** the trend dimension's members at the three book horizons (daily C `calc.trend_spy_ma20_slope`, weekly B `calc.trend_spy_vs_50d`, monthly A `calc.trend_spy_vs_200d`). Each is banded 66/33 with persistence 2 (a turn waits two sessions, as a dimension's does). Never collapsed, and read by nothing that acts.
- **The symmetric close:** a contradiction row closes after two failing sessions, as it opens after two (ruled for v1.13 at Audit #4). Between them the row stays open, `open_state: closing`, and keeps its `since`.

**The laptop's store** (`data/chester.db`, 20 KB) holds none of these series. On it every new dimension reads absent with "no observation for the primary member … knowable at …", and earnings and geopolitical read their not-buildable reasons. The reads above are the gate's fixtures; the box's first reads are the box commands.

## Tranche 3: tail_families and debt_cycle_branch (rulings 10a, 11a)

**`tail_families[]`** has the Twenty-Five's seven mechanism families (A–G with their scenarios), never summed: no tail index, which the gate checks. Each family carries:
- **its state:** `watch` when a stored first-mover series reads extreme, `quiet` when every one is read and none is, `not read` when none is stored;
- **probability `none`**, with its reason;
- **Brier `none`** ("no probability emitted");
- **rights `report_only`.**

"Extreme" is `derived`'s declared rule: at or past the 5th or 95th percentile of five years. That rule is session-set, because the paper's tripwires are prose; it stands in and says so.

| Family | First movers |
|---|---|
| A | SOFR–IORB, the 30-year, FIMA repo |
| B | HY and CCC OAS |
| C | RSP over SPY |
| D | Brent |
| E | 5y5y breakeven, the 12-month fed-market gap |
| F | gold, the TIPS 10-year |
| G | leveraged-ETF AUM |

**`debt_cycle_branch`** has state `none` and confidence `none`. The reason is that the rule awaits Paper XXVII's diagnostic. Its observables print read-only, each a level with its five-year percentile: the deficit's share of GDP, the 10-year real yield, the 10-year breakeven and gold.

**Where they print:** `daily_cascade/state_v2_block.py`, reading the stored object (never recomputing).
- **The Monthly's slow layers:** the families' table and the debt-cycle block, after item 72's 13F line.
- **The Weekly:** one line ("Tail families on watch: … (7 families; an extreme first mover, never a probability; report only)").

**The close:** the five new dimensions print in its detail tables through `state_block.detail_tables()`, which already iterates the object's dimensions.

## Tranche 5: the bar (ruling 12a)

**The field.** `metrics_registry.yaml` gains the section `market_state_barred`, one entry per barring order: its order, its rule, its key patterns, and its instruments where only some instruments of a key are barred. `derived.resolve_registry` sets `market_state: barred` and `market_state_barred_by` on each key. `derived.market_state_barred(entry, instrument)` returns the order that bars it.

**The seeded orders:**
1. 25 Sep order, MW-2/R9: `calc.prl_*` (9 keys).
2. 25 Sep order, 2.3.6 SR-19: `calc.neg_beta_share_*` (0 keys on this base; seeded so the bar holds when they land).
3. ST-3's withdrawal (30 Sep): `calc.attr_*` (20).
4. ST-5, held by `validate_st_t2_rates` group L: the nine funding-currency keys (9).
5. Batch 11 §1, and the registry ruling of 19 Oct: `vendor.*`, `dealer.vendor_*` (26).
6. The prediction-market rights: `pm.*` (9).
7. Batch 14 F5, items 62–71: `rates.speed_event_ledger`, the three `fred.ppi_*` lines, `fred.z1_equities_mv`, `fred.households`, `shiller.real_home_price`, AIQ and SPXT, and the eight capex-chain proxies (SMH MU AMD GRID ANET VRT PAVE ASML) (17).
8. Batch 14 F5 item 71 with D13 (A61): `levetf.*` for QID, UDOW, SDOW, URTY and SRTY only (3 keys, instrument-level).
9. Batch 15 §1, items 72, 73, 77 and 78: `sec13f.*`, `gold.event_ledger`, `equity.dm_drawdown_ledger`, `fred.nikkei225`, `cyber.*`, `defillama.protocols_*` (9).
10. Batch 15 item 74 (`config/hf_positioning.yaml`): the `cftc.tff_lev_money_*` keys for ES and NQ only (4, instrument-level).
11. D22 (A61): `yfinance.mkt_qai` (1).
12. D15 and D26 (b59-trigger-sources, `pending`): `rates.oneday_event_ledger`, `gdelt.*`, `noaa.*`, `ai.model_release*` (0 on this base, 13 when b59 lands).

**The barred-keys count: 107 on this base** (100 whole keys, 7 barred for named instruments only), and 120 with b59's.

**The check** (`validate_regime` group V2): no barred key, and no barred instrument of an admitted key, is a member of any dimension, a dial's leg or a horizon read. A trap config with a barred key (`fred.nikkei225`) and a barred instrument (`cftc.tff_lev_money_net`[ES]) is caught, both.

## The gates

**No new gate.** `validate_regime` gains group V2 (23 checks), and CLAUDE.md's worded gate count is unchanged. That count, recounted on this base, is **137 code gates (134 Python, three shell)**, as chain-6 carries it. CLAUDE.md's description of the object now reads "fifteen dimensions, three dials and an eight-row contradiction table (v2, 6f: …)", which `validate_audit_3a` checks against the config.

**Gates updated for v2:**
- `validate_regime`: group C now declares fifteen dimensions and checks not-buildable and absolute-band dimensions by their own rules; group V2 is new.
- `validate_st_r5_t1_rest`: the config pin is now v2.0.

**Local runs:**

| Gate | Result |
|---|---|
| validate_regime | 516 / 0 |
| validate_st_r5_t1_rest | 103 / 0 |
| validate_st_t2_rates | 71 / 0 (group L: regime and contradictions name no ST-5 key) |
| validate_6e_rest | 34 / 0 |
| validate_derived | 52 / 0 |
| validate_audit_3a | 88 / 0 |
| validate_monthly | 359 / 0, 1 skipped |
| validate_weekly_complete | 96 / 0 |
| validate_alpha | 257 / 0 |
| validate_narratives | 103 / 0 |
| validate_stack | 84 / 0 |
| check_registry | OK |
| validate_regime_store | the data gate, NOT VALIDATED on the laptop (no objects) |

## The CI rounds

| Round | Run | On | Result |
|---|---|---|---|
| 1 | 40117517223 | `1309c81` | **failure, four gates, all this branch's** (fixed in round 2) |
| 2 | read once after the push | the fix | see the report |

Round 1's four failures, all this branch's:

- **`validate_numeral_audit`.** `state_v2_block.py` wrote an ordinal suffix by hand. It now uses `numeral_audit.ordinal()`.
- **`validate_weekly_stack`.** Two causes:
  - Thirteen keys the object v2 names had no display label in `config/display_labels.yaml`; they are added. CI's message showed only four, as the gate prints the first four.
  - The gate's id regex was lower-case only, so it read `fred.uoM_sent` as `fred.uo`; capitals are admitted.
  - Also, `state_v2_block` no longer opens the default store when a caller holds none.
- **`validate_config_refs`.** The bar named b59's `rates.oneday_event_ledger` literally, a key not registered on this base. The pattern is now the glob `rates.oneday_event_*`, which matches nothing until b59 lands.
- **`validate_b45_chain3`.** The narrative register's refusal now lists fifteen dimensions, and `mechanism_watch.note_refused` cut the note at 300 characters before the reason that followed. The cut is now 600.

Locally after the fix: validate_numeral_audit 172/0, validate_weekly_stack 83/0, validate_config_refs 120/0, validate_b45_chain3 29/0, validate_regime 516/0.

## Every session-set value, with its reason

| Value | Set to | Reason |
|---|---|---|
| Positioning's transform | twelve months, matched within 45 days | the year FINRA's own release compares; a month either side covers its month-end dating |
| Positioning's ETF member | TQQQ | the largest fund the writer covers |
| Positioning's CFTC member | the 10-year note (TY) | the basis trade's crowding |
| Positioning's short-interest member | not added | its instrument keying was not verified; listed below |
| funding_stress members, policy members | percentile 66/33 of the dimension's states | their units differ from the primary's, so they cannot share its absolute bands |
| Valuation's five-year read | 1,826 days | v1's window, printed beside the full history |
| Horizons' persistence | 2 sessions | v1's default; the spec |
| Tail families' state rule | an extreme first mover | the paper's tripwires are prose; derived's declared extreme rule stands in and says so |
| Tail families' first movers | as the spec's section 4 table | only stored keys; the paper's other first movers are not stored |
| The debt-cycle observables | the four stored ones the spec names | the term premium is barred (ST-3) and is not among them |

## Where the spec and the code differ

1. **The CFE term structure** stays as v1 runs it: the champion/challenger dual to 23 Dec 2026 (the spec's 1.4, item 2). Nothing changed.
2. **Positioning's short interest.** The spec's `finra.short_interest` on SPY is not a member: the key is instrument-keyed and its SPY instrument was not verified on this base.
3. **The tail families' state.** The spec's "past its declared tripwire" is built as "an extreme reading on a first mover": the reference file gives no machine-readable tripwire.
4. **Absent everywhere on the laptop.** On the laptop's empty store all thirteen computed dimensions read absent. The fixture reads in this file are the gate's, not the market's.

## Files shared with b59-trigger-sources and a61b-feed-repair

**b59-trigger-sources:**
- `metrics_registry.yaml`: b59 adds its keys; this branch adds `market_state_barred` and `calc.cp_bill_bp`. Different places; its keys are pre-barred.
- `CLAUDE.md`: b59 likely moves the gate count; this branch changes the object sentence only.
- The Makefile only if b59 adds a gate.

**a61b-feed-repair** (cut from main):
- `metrics_registry.yaml`: a61b adds `member_overrides` before `forward_dated:`, and so does this branch's `market_state_barred`. **A stitch conflict to resolve by keeping both sections.**
- `altdata/derived.py`: a61b edits `resolve_registry`'s end and `staleness_allowance_of`; this branch edits `resolve_registry`'s end. **A conflict at the same spot; keep both blocks.**
- `CLAUDE.md`: a61b changes the gate line, this branch the object sentence.

## The box commands (the operator's; after the merge, which is after the 1 Nov Monthly)

```
cd ~/chester-reports
# Tranche 0's checks (the spec's section 8), read-only:
.venv/bin/python -m regime range                 # the supportable window: how far as-of history reaches
.venv/bin/python -m regime method                # method-11, pinned 1664e465a940aadc
.venv/bin/python - <<'EOF'                       # how many as-of-correct objects per dial state
import collections, json, sqlite3, os
db = os.path.expanduser("~/chester-data/chester.db")
c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
n = collections.Counter()
for (v,) in c.execute("SELECT value_text FROM observations WHERE registry_key='market_state'"):
    o = json.loads(v); d = o.get("dials") or {}
    for k in ("macro", "vol", "gamma"):
        n[(k, (d.get(k) or {}).get("state"), o.get("method_version"))] += 1
for k, v in sorted(n.items(), key=str): print(k, v)
EOF
# The v2 object, computed and printed, NOT stored:
.venv/bin/python -c "import regime; o=regime.compute(); print({n: d.get('state') for n, d in o['dimensions'].items()}); print(o['horizons']); print([(f['family'], f['state']) for f in o['tail_families']])"
# Then the re-backfill under method-11 (writes market_state vintages; dry run first where it offers one):
.venv/bin/python -m regime backfill --no-resume
```

## Needs you (at most five; yes or no each)

1. **The tail families' state rule:** a family reads `watch` when one of its first movers reads extreme (the 5th or 95th percentile of five years), because the paper's tripwires are prose. Keep it until the paper's tripwires are written as numbers? Yes / no.
2. **The re-backfill under method-11 after the merge** (the box commands), with the replay gate passing on the box before the next close? Yes / no.
3. **Positioning's members:** TY for the CFTC leg, TQQQ for the ETF leg, and no short-interest member until its SPY keying is verified? Yes / no.
4. **The stitch with a61b:** keep both registry sections (`member_overrides`, `market_state_barred`) and both `resolve_registry` blocks? Yes / no.
5. **The CP-bill series on the 16:10 pass from the merge,** a derived series of two FRED legs already pulled? Yes / no.
