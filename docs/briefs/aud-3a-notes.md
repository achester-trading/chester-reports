# AUD-3a: retrieval — the store against the registry, the units, the catalogue (session A, 14 Oct 2026)

Branch `aud-3a-catalogue`, from `origin/w-1-3c-weekly-polish` at **`fb67bf3`**, which had not moved. The branch is pushed only: nothing is merged, deployed or run on the box. It merges after Friday's merges and after aud-1, through a refresh paste.

It answers the data and architecture audit of 14 Oct (recommendations 12 and 15). The audit read main at `cc91752`; every finding was re-checked on this branch first.

**Ruled before building (14 Oct evening).** aud-1 changed `metrics_registry.yaml`, `CLAUDE.md` and the `Makefile`, which items 2, 3, 5 and 6 need. The ruling:
- The stay-out rule covers aud-1's code files. These three files are shared by every branch, so edit them and build in full.
- Keep away from the six registry entries aud-1 changed: `finra.short_volume`, `finra.total_volume`, `finra.short_exempt_volume` and `apewisdom.mentions`, `.rank`, `.upvotes`, all description-only changes. No edit on this branch falls inside them; I checked the diff's hunks against lines 1490–1615.
- The gate-count line and the Makefile list will conflict at the refresh whatever happens; update them here and the refresh recounts.

## The findings, re-checked on fb67bf3

| Audit finding | On this branch |
|---|---|
| Nothing checks the store against the registry | Confirmed. |
| `percent` covers yields, percentiles and returns (a percentile 40 → 55 reads +1,500 bp) | Confirmed. 210 metric entries used `percent`; 135 had no `delta_unit` override and took basis points, `regime.dimension_percentile` among them. |
| ^TNX and ^VIX typed as prices | Confirmed: both sat in `market_closes`, `units: price`, so their deltas were percent. |
| `pm.volume` mixes Kalshi contracts and Polymarket dollars | Confirmed, and so does `pm.open_interest` (Kalshi's open interest in contracts against Polymarket's liquidity in dollars). |
| The bars table's volume has no unit | Confirmed. |
| The resolver drops five bulk blocks, all 46 `overnight.*` keys among them | Confirmed: `event_columns`, `event_types`, `pin_log_columns`, `overnight_levels` and `overnight_percent_changes`. They declare neither `member_key` nor `members_are`, and `derived._load_registry` skipped any such block. `check_registry` read them as plain lists, so the two disagreed. |
| A row's source is free text; Polymarket rows under metrics declared Kalshi | Confirmed. Every `pm.*` entry said `source: kalshi`. The registry also named the backfill string as `<venue>_backfill`, while the writer stores `<venue>:backfill`. |
| No single place to list or search; 27 metrics without a description | Confirmed: 27, all `exposure.*`, `gates.*` and `portfolio.*`. The tip has **101** command modules (61 sources, 6 loggers, 34 under `altdata/`), not the audit's 33. The tree has grown since `cc91752`. |
| CLAUDE.md's counts stale | Confirmed, with the tip's own numbers. The tip says 20 signal series and the code has **27**; the audit said 24 at `cc91752`. It says 59 market symbols and the code has **106**; the audit said 27 printed against 81. The tip also prints five data gates while its Makefile lists six. |
| The architecture document's store sections and the README's link are stale | Confirmed. The architecture document still describes D1 as the system of record (Finding 7, Session 1 item 5, Session 5). The README names `docs/architecture-v3.md`, which does not exist. |
| The Gateway watchdog and the what-if tool share client id 18 | Confirmed. |
| The prediction-market last-price fallback has no range check | Confirmed. The mid was range-checked in `price()`; the fallback returned the last trade unchecked. |

Nothing was already fixed, so nothing was skipped.

## The fixes, each with its fixture

The gate is `tools/validate_audit_3a.py`: **72/0**, seven groups, A to G. The registry rules live in `tools/check_registry.py` (`aud3a_faults`). The units' end-to-end deltas extend `tools/validate_derived.py` as group H.

### 1. The store against the registry — `python -m tools.check_store_registry --db PATH`

What it does:
- It opens the store with SQLite `mode=ro` and prints four lists:
  1. **stored and unregistered:** keys in `observations` and in the bars table that resolve to no registry entry and no non_metric;
  2. **registered, no rows;**
  3. **stale:** the newest `observed_at` is older than the key's own allowance, by `derived.staleness_allowance_of()`, which is the rule the reports' confidence uses;
  4. **source strings on no list** (item 4).
- Exit 0 means clean, 1 findings, 2 the store cannot be opened. It writes nothing.
- The bars table is read as `bars.<instrument>`, plus `bars.<instrument>.volume` where a bar carries volume.

Fixture: the gate seeds a synthetic store holding:
- a fresh FRED row;
- a `kalshi:backfill` row, a `polymarket` row and a `calc` row;
- a stale `yfinance.mkt_qqq` (31 sessions against an allowance of 1);
- an unregistered `bogus.key`;
- an `ig_oas` row whose source is `mystery_feed`;
- bars for SPY (with volume), y10 (volume 0) and an undeclared `zzz`.

The gate shows:
- each of the four lists exactly;
- exit 1 on that store, exit 0 on a clean one, and exit 2 on a missing file;
- a write through its connection refused as read-only;
- the store's bytes unchanged afterwards.

### 2. The resolver

- `derived.resolve_registry(reg)` is now a pure function, and `_load_registry` calls it.
- A block with neither `member_key` nor `members_are` names its members directly, as `check_registry` always read it.
- A `from_member` field on a string member takes the one individually registered metric whose leaf it is. This is how the pin log's columns are covered; otherwise the field is None, and the delta reason says "registered … with no units".
- Every resolved entry records its `bulk_block`.

All five blocks now expand: overnight 36 + 10, event columns 12, event types 6, pin-log columns 83. `check_registry` fails a block that expands to no key, and a member with no entry.

Fixture (gate group A): `overnight_levels` is pointed at an empty list and then at a module that does not exist; both fail `check_registry`.

### 3. The units, with no silent change to a printed number

**Percent split by meaning.** Each unit is declared in the registry's units vocabulary and in `derived.DELTA_UNITS`:

| Unit | Meaning | Delta |
|---|---|---|
| `percent_rate` | a yield, rate or spread level | bp |
| `percentile` | an own-history rank 0–100 | **pts** (new delta unit) |
| `percent_return` | a return, growth rate, change or distance | pp |
| `percent_share` | a share of a whole (of sectors, of GDP, of OI) | pp |
| `vol_pct` | an annualised volatility in percent | pts |
| `vol_index` | a volatility index level (^VIX) | pts |

- The 213 percent declarations (210 entries plus three bulk blocks) are now 68 `percent_rate`, 52 `percent_return`, 87 `percent_share`, 5 `vol_pct` and 1 `percentile`.
- `percent` stays in the vocabulary so a stored reference resolves, but `check_registry` refuses it on any metric or block.
- Existing `delta_unit: pp` overrides are kept as written, so none of their deltas moved.

**^TNX and ^VIX.**
- `market_closes` declares `member_units`: `yfinance.mkt_tnx` and `mkt_tyx` are `percent_rate`; `yfinance.mkt_vix` and `mkt_vix3m` are `vol_index`.
- `market_ohlc` declares the two yields' open, high and low as `percent_rate`.
- A `member_units` key that is no member fails `check_registry`.

**pm.volume per source.**
- `units: by_source`, `units_by_source: {kalshi: count, polymarket: usd}`, `delta_unit: raw`. The venue is in the instrument's prefix.
- `pm.open_interest` gets the same treatment.

**The bars table's volume per instrument.**
- `altdata/bars.py` declares `volume_unit(symbol)` by the rule `yfinance_source.VOLUME_UNITS` already follows: a future's volume is contracts (ES=F included), a crypto pair's is dollars, an ETF's is shares, and an index, currency pair or the dollar index has none.
- Four registry blocks resolve `bars.<id>` and `bars.<id>.volume`: `bars_prices` (y10 and y30 are `percent_rate`), `bars_volume_shares` (3), `bars_volume_contracts` (3) and `bars_volume_usd` (1).

**No silent change to a printed number.**
- A level is formatted from its units, and every renderer compared against the old words. So `derived.level_units()` maps each split unit back to the word it printed under: the five percent meanings print as percent, and `vol_index` prints as price, as the VIX did.
- The renderers now read it in `daily_cascade/stack.py`, `weekly_stack.py` (4 sites) and `events_block.py`, and in `monthly_macro/quarterly_items.py`, `v2.py` and `payload.py`.

#### Every metric whose delta rule changed, with one fixture delta before and after

The gate freezes fb67bf3's rule for all 2,454 keys it resolved (`tests/fixtures/aud3a_delta_rules_fb67bf3.json`) and fails any key whose rule moved and is not declared here.

| Metric | Unit now | Rule then → now | Fixture pair | Delta then | Delta now |
|---|---|---|---|---|---|
| `yfinance.mkt_tnx` (+ `_open`, `_high`, `_low`) | percent_rate | percent → bps | 4.25 → 4.32 | +1.6471% | +7 bp |
| `yfinance.mkt_tyx` (+ `_open`, `_high`, `_low`) | percent_rate | percent → bps | 4.80 → 4.75 | −1.0417% | −5 bp |
| `yfinance.mkt_vix` | vol_index | percent → pts | 18 → 20 | +11.1111% | +2 pts |
| `yfinance.mkt_vix3m` | vol_index | percent → pts | 20 → 21.5 | +7.5% | +1.5 pts |
| `regime.dimension_percentile` | percentile | bps → pts | 40 → 55 | +1,500 bp | +15 pts |
| `chain.spy_atm_iv_30d` | vol_pct | bps → pts | 16 → 18.5 | +250 bp | +2.5 pts |
| `calc.vol_spy_realized_20d` | vol_pct | bps → pts | 12 → 14 | +200 bp | +2 pts |
| `zec.realized_vol_20d` | vol_pct | bps → pts | 80 → 95 | +1,500 bp | +15 pts |
| `calc.trend_spy_vs_50d` | percent_return | bps → pp | 1.2 → 1.5 | +30 bp | +0.3 pp |
| `calc.trend_spy_vs_200d` | percent_return | bps → pp | 4.0 → 3.5 | −50 bp | −0.5 pp |
| `calc.trend_spy_ma20_slope` | percent_return | bps → pp | 0.8 → 1.1 | +30 bp | +0.3 pp |
| `calc.stable_impulse_30d` | percent_return | bps → pp | 2.0 → 2.6 | +60 bp | +0.6 pp |
| `calc.stable_impulse_90d` | percent_return | bps → pp | 5.0 → 4.0 | −100 bp | −1.0 pp |
| `french.hml` | percent_return | bps → pp | −0.5 → 1.2 | +170 bp | +1.7 pp |
| `french.ind49_ret_vw` | percent_return | bps → pp | 1.0 → −2.0 | −300 bp | −3.0 pp |
| `grade.return_pct` | percent_return | bps → pp | 0.5 → 2.5 | +200 bp | +2.0 pp |
| `grade.mae_close_pct` | percent_return | bps → pp | −1.0 → −2.5 | −150 bp | −1.5 pp |
| `aaii.bull_bear_spread` | percent_share | bps → pp | 10 → 4 | −600 bp | −6 pp |
| `manual.cbo_deficit_path` | percent_share | bps → pp | 5.9 → 6.2 | +30 bp | +0.3 pp |

That makes 25 keys, counting the OHLC companions. The other 188 reclassified declarations keep their rule: the rate ones stay in bp, and those with a `pp` override stay in pp.

**164 keys resolve for the first time.** Each had no entry at fb67bf3, and so no rule (raw, "no registry entry"):
- 46 `overnight.*`: the 10 percent changes are `percent_return`, so pp; the 36 levels are price, so percent;
- the 14 bar keys;
- 12 event columns, 6 event types and 83 pin-log columns. The columns take the unit of the metric whose leaf they are, or none.

**Re-rendered fixtures (text and HTML, no PDF).** I rendered the Daily close, the Weekly and the Monthly from their own gates' seeds, before any change and again after all of them, and diffed the printed text with the clock line, the archive path and the ledger hash filtered out:
- run-to-run noise on two "before" renders: those three lines only;
- **printed lines changed by AUD-3a: none, on all three editions.**

The fixtures print none of the 25 keys' deltas. So the delta table above, and the frozen rule fixture behind it, is what holds the change. On the box the moves will show where those keys print: the VIX's change in points; the volatility dimension's `direction_reason` naming "pts/session"; the move screen reading the VIX by difference rather than log return, because `move_screen` picks log for a percent delta. The regime's states and directions cannot move, because direction is the sign of the rate of change and percentiles are unit-free.

### 4. Source ids

`altdata/source_ids.py` `canonical(stored)` reads a stored string, in order:
1. an id in `source_registry.yaml` is itself;
2. a string in the new top-level `stored_aliases` table is the id it names there (the table is empty until the box's store has been read; see needs-you);
3. `<id>:<variant>` is the id (`kalshi:backfill`, `fred:csv_migrated`);
4. anything else is off the list: `None`, printed by the store check.

Stored rows are never rewritten.

Supporting registry changes:
- `source_registry.yaml` gains `calc`, the string every `calc.*` row carries (tier `derived`, `own_computation`).
- The eight `pm.*` metrics both venues write declare `sources: [kalshi, polymarket]`. `check_registry` fails an unknown id in `sources`, or a `sources` list that omits `source`.
- The registry's backfill string now reads `<venue>:backfill`, as the writer stores it.

Fixture (group D): the id, variant, alias and off-list cases. A source check reads the writer's own f-string.

### 5. The catalogue — `python -m altdata.catalogue`

- **`list`:** filtered by `--domain` (the source's domains), `--kind` (metric or bulk, or a declared `series_kind` or family), `--source` (`source` or `sources`) and `--cadence` (freq, else native horizon).
- **`search TEXT`:** over ids, descriptions (a bulk member's is its block's) and aliases (`config/display_labels.yaml` and the tape's aliases).
- **`show ID [--db PATH]`:** every registry field; the resolved units, the level's print word and the delta rule; the staleness allowance; the block; the writer modules; the `python -m` commands that run them; and with `--db`, the row count and first and newest observation, read-only.
- **`commands`:** the declared table `config/catalogue_commands.yaml`, **102 lines** (the 101 modules, plus the catalogue itself). Each line is the module's own docstring's first sentence, shortened, with a domain assigned. `altdata.feeds` declares `fred` and `yfinance`, the two writers it runs that have no command of their own.
- The gate fails a command module with no line, and a line naming a module that is gone.

**The 27 descriptions** are written from the code that computes each metric:
- `tools/exposure_compute.py` for the walls, notionals, per-strike splits, bucket shares and OI structure;
- `tools/quality_gates.py` for the two gates;
- `altdata/sources/ibkr_portfolio.py`'s `ACCOUNT_TAGS` for the seven account fields.

The code made every meaning clear, so **no description is "description pending"**. The gate fails a metric with none.

### 6. The docs

- **CLAUDE.md:**
  - 27 signal series, plus "43 in five smaller lists (FX scan 18, SLOOS 5, AQ-3 7, SR-43 12, Thailand 1)", and the union of 129;
  - 106 market symbols, keyed `yfinance.mkt_<sym>`;
  - 75 code gates (72 Python, 3 shell) and six data gates;
  - a paragraph on the catalogue, the store check and the split units.
- **The counts gate** (group F) compares 13 printed counts with the code's: FRED 59, signal 27, smaller lists 43, union 129, symbols 106, data_store CSVs 59, code gates 75, Python 72, shell 3, data gates 6, dimensions 8, dials 3, contradiction rows 8.
  - Counts written in words are read.
  - A sentence reworded so its count cannot be found fails rather than passing unchecked.
  - The gate shows the audit's own stale "20 more in FRED_SIGNAL_SERIES" being caught.
- **The architecture document:**
  - "The store as built (AUD-3a, 14 Oct 2026)" after Part 2's diagram;
  - dated "as built" notes under Finding 7, Session 1 item 5 and Session 5;
  - the planning text left as it was written.
- **The README** names `docs/chester-reports-architecture-v3.md`, and the catalogue.
- `check_library`: 27 papers, 0 failures, 0 warnings.

### 7. Client ids and the price range

**Client ids.**
- `altdata/ibkr_clients.py` holds them all: portfolio sync 17, watchdog 18, costs 19, **what-if 20** (was 18), auction 23, borrow 25.
- The what-if tool, `tools/decide.py`'s preview default, the sync, the costs tool and the auction logger read from it.
- The gate checks:
  - that the table's ids are unique;
  - that the two shell defaults (`ibgateway_watchdog.sh` 18, `sync_ibkr.sh` 17) and `altdata/loggers/borrow.py`'s literal 25 agree with the table. borrow.py is aud-1's file, so its literal stays;
  - that no `client_id` literal in `altdata/` or `decide.py` is outside the table.
- `validate_ibkr_whatif` now pins 20.

**The price range.**
- `prediction_markets.VENUE_PRICE_RANGE` (both venues 0..1) and `in_range()`.
- A last trade outside its venue's range is dropped and logged on the live parse (both venues) and in the backfill. A market left with no price is skipped, as before.
- The mid's own check is unchanged.

## Box commands, for Ari (none run here)

After this branch reaches main, inside a window (weekdays 09:05–15:40 or 17:20–23:30 ET; never 16:00–17:20):

    cd ~/chester-reports && .venv/bin/python -m tools.check_store_registry --db data/chester.db

It is read-only:
- SQLite `mode=ro`, so no row, table or file content changes.
- The live store is WAL, so its `-wal` and `-shm` already exist while the units hold it open, and the check adds nothing.
- On a quiescent WAL file, a read-only open leaves SQLite's `-shm` index and an empty `-wal`, which hold no data.

What the output means:
- **Exit 0** means lists 1, 3 and 4 are empty.
- **List 1, stored and unregistered:** a writer is storing a key the registry does not know. Register it, or declare it a non_metric.
- **List 2, registered with no rows:** read, never gated. The registry also declares what lives outside these two tables (the exposure profiles, the pin log, the register's grades), so this list is long by design. Its namespace counts are the thing to read: a namespace expected in the store but missing from it is a writer that never ran.
- **List 3, stale:** each key with its newest date, sessions since, and the allowance it broke.
- **List 4, sources on no list:** each stored source string `source_ids` cannot read as an id. Each needs a `stored_aliases` line with its reason, or a source registered.
- **Exit 1** means any of lists 1, 3 and 4 holds a finding. **Exit 2** means the store could not be opened.
- Add `--verbose` for list 2 key by key.

## Three catalogue commands, with their output on fixtures

`search` and `list` read the registry. `show --db` reads the gate's fixture store, seeded as in item 1.

    $ python -m altdata.catalogue search "the VIX"
    calc.vix3m_over_vix      VIX3M divided by VIX: the ratio of three-month to one-month IMPLIED VOLATILITY OF THE INDEX. IT IS NOT THE VX
    corr.avg_pairwise.60d    The mean ABSOLUTE 60-day correlation across every pair in the universe -- the liquidation signature (II S2, M1
    fred.vix                 The 59 FRED series behind the Monthly Macro report. Enumerated in code with key, units, freq and pillar; dupli
    yfinance.mkt_vix         Daily closes for the 40-symbol market basket, keyed yfinance.mkt_<sym> (ST-2 added IVW IVE IWF IWD VWO ACWX EM
    (4 matches)

    $ python -m altdata.catalogue list --source polymarket
    pm.ask             fraction    raw  kalshi,polymarket  daily
    pm.bid             fraction    raw  kalshi,polymarket  daily
    pm.last            fraction    raw  kalshi,polymarket  daily
    pm.market          label       raw  kalshi,polymarket  daily
    pm.open_interest   by_source   raw  kalshi,polymarket  daily
    pm.price_basis     label       raw  kalshi,polymarket  daily
    pm.probability     fraction    raw  kalshi,polymarket  daily
    pm.volume          by_source   raw  kalshi,polymarket  daily
    (8 keys)

    $ python -m altdata.catalogue show pm.volume --db fixture.db
    pm.volume
      6d: a venue market's cumulative traded volume (contracts on Kalshi, USD on Polymarket), same instrument key as pm.probability. ...
      units               : by_source
      delta_unit          : raw
      delta_rule          : registry delta_unit 'raw'
      staleness_allowance : 1
      domains             : ['prediction_markets']
      writers             : ['altdata/sources/prediction_markets.py']
      commands            : ['python -m altdata.sources.prediction_markets']
      registry fields:
        source                  : kalshi
        sources                 : ['kalshi', 'polymarket']
        units_by_source         : {'kalshi': 'count', 'polymarket': 'usd'}
        ...
      store               : 1 rows, first 2026-10-14, newest 2026-10-14

The column spacing above is shortened. The store check on the same fixture lists `bars.zzz`, `bars.zzz.volume` and `bogus.key` (list 1), `yfinance.mkt_qqq` (list 3: newest 2026-08-31, 31 sessions, allowed 1) and `'mystery_feed'` (list 4), and exits 1. On the clean fixture it prints CLEAN and exits 0.

## Files shared with the named branches

My files are intersected with each branch's own changes since fb67bf3 (`git diff --name-only fb67bf3...origin/<branch>`).

| Branch | Shared files | What to expect at the refresh |
|---|---|---|
| aud-1-data-fixes | `CLAUDE.md`, `Makefile`, `metrics_registry.yaml` | The gate-count line and the gate list conflict, as ruled. The registry should merge clean: aud-1's six entries are untouched here, and none of my edits is within them. |
| aud-2-ops-security | `CLAUDE.md`, `Makefile`, `altdata/loggers/auction.py`, `daily_cascade/weekly_stack.py` | auction.py: aud-2 adds the Gateway stand-aside and I changed `_connect`'s default to the table, in different functions. weekly_stack.py: aud-2's `@metered` decorator against my `level_units` lines, in different functions. |
| alpha-lab-2 | `CLAUDE.md`, `Makefile`, `daily_cascade/weekly_stack.py` | The count line and list; weekly_stack.py in different places. |
| vp-1-volume-profile | `CLAUDE.md`, `Makefile`, `daily_cascade/stack.py`, `daily_cascade/weekly_stack.py`, `metrics_registry.yaml` | VP-1's 18 entries use `units: price` (no `percent`) and sit at the end of `metrics:`; my bars blocks are in `bulk_imports`. |
| t3-6-monthly-polish | `CLAUDE.md`, `monthly_macro/v2.py` | v2.py: T3.6's resolved-row fields against my one `level_units` line. |
| The Security Master branch (AUD-3b) | not pushed | I touched nothing of `altdata/security_master.py`, `config/security_master.yaml` or `data/reference/`. |

No named branch adds an entry with the now-refused `units: percent`; I checked each branch's registry diff. A branch that adds one later will fail `check_registry` until it picks a split unit.

**Left for after aud-1 merges**, because they live in aud-1's files:
- **The as-of join and source ids.** On this branch the join reads no tier. aud-1's `observations.py` adds a query that returns `source`; reading it through `source_ids.canonical()` comes after that merge.
- **borrow.py's client id.** `altdata/loggers/borrow.py` carries its client id literal (25). The gate holds it to the table, and moving it to read the table comes after aud-1.
- **Registry lookups in yfinance_source.py and observations.py.** No change was needed there for this item.

## Not named in the paste, so chosen here

1. **^TYX and ^VIX3M join ^TNX and ^VIX** as the same cases (the 30-year yield; the three-month VIX). ^VVIX, ^MOVE and ^SKEW are left as prices; see needs-you.
2. **`pm.open_interest`** is declared per source like `pm.volume`.
3. **Points get their own delta unit, `pts`,** apart from `pp`. The arithmetic is the same plain difference, and every renderer prints `pp` and `pts` alike (no `%` or `bp` suffix), so no printed form moved.
4. **`level_units()`** keeps every level's printed form. A split unit prints under its old word, and the VIX still prints as a price.
5. **Existing `delta_unit: pp` overrides are kept**, not removed as redundant, so each exception stays visible in the diff.
6. **`percent` stays in the vocabulary, refused on entries,** so a stored or archived reference still resolves.
7. **List 2 of the store check is printed, not gated.** It also leaves out the three format blocks (pin-log columns, event columns, event types), whose members are columns and vocabulary values, never stored keys.
8. **A read-only open of a WAL store leaves `-shm` and an empty `-wal`.** The gate asserts exactly that, plus the database's bytes unchanged. `immutable=1` would avoid them but would read past a live WAL's newest rows.
9. **`calc` is registered as a source**, rather than aliased to an id that would misstate it.
10. **The bars keys are `bars.<id>` and `bars.<id>.volume`.** They are registry identities for a table not keyed by `registry_key`.
11. **The catalogue's `show`** names both the writer modules (`implemented_by`) and the commands that run them. A writer such as `yfinance_source` has no `python -m` of its own and is run by `altdata.feeds`.
12. **The architecture document gets dated "as built" notes**, not a rewrite of its planning sessions.
13. **`delta_unit_for`'s reason** now says "registered … with no units" for a known key with no units, instead of "no registry entry".
14. **`tools/check_store_registry.py` is a declared non-gate.** The paste names the command `tools.check_store_registry`, and `validate_gates` takes every `tools/check_*` or `tools/validate_*` file for a gate. It is an operator's check of a named store, so it is not in the Makefile's list. `validate_gates` gains a `NOT_GATES` table with each tool's reason, and fails an entry that does not exist or is also listed as a gate. Making it a data gate instead would have had it read the live store.

## Needs you

1. **FRED's own `%` members keep basis points.** Their units are `altdata/config.py`'s `%` and resolve through the FRED blocks. Most are yields, rates and spreads, where bp is right. About 18 are shares or rates of change, where pp is the convention:
   - labour: U-3, participation, employment–population, quits;
   - delinquency: mortgage, card, auto and CRE delinquency, and card charge-offs;
   - inflation: sticky, sticky core and flexible CPI;
   - fiscal: debt/GDP;
   - credit: the five SLOOS net-tightening series.

   Moving them changes the Monthly's printed changes for those series. Rule: move them to pp (per-member units in the FRED blocks), or keep bp.
2. **^VVIX, ^MOVE and ^SKEW** are still prices, so their deltas are percent. VVIX and MOVE are volatility indexes like the VIX (points); SKEW is an index. Rule: `vol_index` for VVIX and MOVE, or leave all three.
3. **Off-list source strings the box will likely print** (list 4). Read from the writers' code:
   - `ibkr`, written by the auction, borrow, costs and what-if paths, so ambiguous between `ibkr_paper`, `ibkr_stock_loan` and the market-data ids;
   - `daily_close`;
   - `book_z`;
   - `alt_asset:<family>` (`alt_asset` is no id);
   - `narrative_register`;
   - `paper_bid_chain`.

   I declared no alias: the box's own list should be read first. Then each string gets either a `stored_aliases` line with its reason or a registered source. Which?
4. **The VIX's move-screen basis changes** from log return to difference, because `move_screen` reads log for a percent delta. It is the screen's own rule applied to the VIX's new unit. Flags on the VIX could differ at the margin. Keep, or pin the VIX to log?
5. **^TNX's level would now print with a `%`** wherever a renderer formats it from registry units, because `percent_rate` prints as percent and it was a price before. No fixture shows it; the tape prints the 10-year from its own config, as a yield with `%`. Accept, or give ^TNX a level word of its own?
6. **The merge order** stays as set: Friday, then aud-1, then this branch through a refresh. The refresh recounts CLAUDE.md's gate line, which conflicts with every branch.

## Gates (run locally, one at a time: only those written or changed here)

| Gate | Result |
|---|---|
| validate_audit_3a (new) | 72/0 |
| check_registry (extended: `aud3a_faults`) | OK |
| validate_derived (group H added) | 52/0 |
| validate_ibkr_whatif (pins 20) | 54/0 |
| validate_gates (the `NOT_GATES` table, after CI #410) | 32/0 |
| check_library | 27 papers, 0 failures, 0 warnings |

Every other gate is left to CI, as the paste asked, given the laptop's memory with both sessions running. Windows raised no low-memory warning, and no local gate was killed.

## CI

- **#410** (`fed7ce8`) **failed one gate, `validate_gates`:** "every validator in tools/ is in the Makefile's list (['tools/check_store_registry.py'])". The tool is named like a gate and is not one. Fixed by the declared `NOT_GATES` table (item 14 above). Every other gate passed.
- The fix's run: see the reply.
