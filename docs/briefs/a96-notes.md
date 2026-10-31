# A96 notes: the price sources' per-family switch, FRED's yields and dollar

**Branch.** `a96-price-migration-fred`, from origin/main at `422ea697`. It is
tranche 2b of the price-source migration:

- the brief is `docs/briefs/price-source-migration-brief-2026-10-25.md` on
  `b68-price-source-migration`;
- the paste names sections 3, 4 and 5 and decisions 4 and 5, all read; D38
  ruled the decisions.

**Merge timing.** It merges after chain-8. Every family ships on yfinance, so
nothing printed changes.

## What is built

**`config/price_sources.yaml`, one switch per family.** Each entry carries:

- `source`;
- the old and new keys per member;
- `break_label`;
- `switched_on`;
- the `parallel_run` record: started, sessions counted of 20, max gap, tolerance
  "to be measured on the overlap".

The families:

- **`us_yields`:** `y10` is `yfinance.mkt_tnx` or `fred.yield_10y` (DGS10); `y30`
  is `yfinance.mkt_tyx` or `fred.yield_30y` (DGS30).
- **`dollar_index`:** `dxy` is `yfinance.mkt_dxy` or `fred.dxy`. That key is
  DTWEXBGS; the brief wrote `fred.dxy_broad`, but the registry's key is `fred.dxy`.
- **Stubs for A93's families:** `us_index_funds`, `index_levels`,
  `futures_overnight`, `fx`. No reader is routed through these yet.

**`altdata/price_sources.py`, the one resolver.**

- `key(family, member)` returns the active key.
- In config, `"price:<family>.<member>"` resolves to the active key, and
  `"price:<family>.<member>@<source>"` is pinned to one source. A pinned reference
  is for a deliberate cross-source comparison: the Quarterly's "DXY against the
  broad dollar" chart and the inactive pairs.
- `resolve_tree()` resolves a loaded config.
- `break_label()`, `labels_for()` (each family once), `segments()` (the old key up
  to the switch, the new from it), `split_points()` and `plot_split()` (two series
  and a dashed break, never spliced), and `switch_date_of()`.
- `python -m altdata.price_sources` prints each family's source and keys.

## The readers moved

Each config's loader now resolves its references, so every consumer of the
loaded config moved at once.

**Code** (A96's line numbers):

| # | File | What moved |
|---|---|---|
| 1 | `altdata/bars.py:68` | `load_config()` resolves the tape. Every `bars.tape()` and `load_config()` consumer moves with it: `levels.compute`, `labels`, the Book B scanner, the storyline, the volume profile, the Weekly's tape table |
| 2 | `altdata/catalogue.py:80` | the catalogue's own read of the tape |
| 3 | `altdata/correlation.py:77` | `config()`, the universe's dollar |
| 4 | `altdata/attribution.py:144` | its own read of `config/correlation.yaml`'s universe |
| 5 | `tools/horizon_charts.py:97` and `:110` | `load_config()`, and its universe read |
| 6 | `monthly_macro/quarterly_items.py:65` | `load_config()` |
| 7 | `altdata/batch3.py:70` | `config()` (`buybacks.thirty_year_tape`) |
| 8 | `altdata/move_screen.py:742` | the 10-year companion line's series prefix |
| 9 | `altdata/rates_shape.py:246` | `TEN_YEAR_LEGS` is now `ten_year_legs()`: FRED and the active tape key, one leg once switched |
| 10 | `daily_cascade/consistency.py:144` | the y10 and y30 aliases |

**Config references** (nine):

| File | Change |
|---|---|
| `config/reporting_stack.yaml` | tape `daily` for y10, y30 and dxy |
| `config/correlation.yaml` | dxy |
| `config/horizon_charts.yaml` | dxy, twice |
| `config/quarterly_chapters.yaml` | dxy; the twin chart's DXY leg is pinned `@yfinance` |
| `config/batch3_tranche_a.yaml` | `thirty_year_tape` |

In all: ten code readers and nine config references. **No reader names the three
old keys.** The gate's grep over `daily_cascade/`, `monthly_macro/`, `altdata/`
and `config/` holds it, with four declared exemptions:

- `altdata/sources/yfinance_source.py`, the writer;
- `config/security_master.yaml`, the instrument's identity;
- `config/data_quality.yaml`'s existing ^TNX/DGS10 and ^TYX/DGS30 pairs, which
  check Yahoo against FRED by design;
- `config/price_sources.yaml`, the switch itself.

`tools/assign_families.py` still names the keys: it is a registry tool outside the
four directories, not a reader.

## The break label and the charts

**Where the label prints.** When a family is switched:

- the Weekly's tape table carries `break_labels`;
- `stack_render._table` prints each label once, directly beneath the table that
  holds the series' first figure.

Unswitched, the field is absent, so the HTML is unchanged.

**The charts:**

- The Quarterly's twin chart marks a switched leg's date with a dashed line, and
  its DXY leg stays ICE's, ending at the switch.
- `plot_split()` draws any other level chart's two series with the break.
- The horizon charts compute returns from the resolved key's own history (FRED's
  runs for decades), so no window splices two sources.

**Where the label does not print yet.** Wired here are the tape table, through the
shared table renderer, and that chart. Another block that prints these series
reads the right key through the resolver, but prints the label only once it adds
`break_labels` to its table: the Plumbing panels and the close's lens lines. That
is listed for the switch's paste.

## The cross-source pairs

`config/data_quality.yaml` `inactive_pairs_fred`:

- dxy against DTWEXBGS, ^TNX against DGS10, ^TYX against DGS30;
- each pinned to its sources, `active: false`, tolerance "to be measured on the
  overlap";
- not read by the quality check.

The yields' first read is the existing active pairs' own measurement.

**Merge note.** A93's branch adds an `inactive_pairs` block for the IBKR family.
The two are separate keys in different places, to keep the merges apart, and may
be unified at the second merge.

**The registry.** `metrics_registry.yaml` is unchanged. The old keys'
`superseded_by` (fred.yield_10y, fred.yield_30y, fred.dxy) are written at the
switch, not before, since a superseded key reads as quiet in the store check. The
mapping is the switch file's members.

## The gate

`tools/validate_price_sources.py`, 24/0:

- **the default:** every moved reader gets the key it read before; the tape table
  carries no new field;
- **a switch:** the FRED keys, the dated label once beneath the table, the
  segments;
- **no hard code:** the grep with its four exemptions;
- **no splice:** two series and the break; no line crosses it;
- **pins and pairs.**

**Bookkeeping.** One Makefile line. The count goes from 135/132 to 136/133, by
hand: main has no stitch tools. A92 and A93 each make the same +1 on their own
branches, so the last of the three to merge sets 138/135. A catalogue line was
added for `altdata.price_sources`.

**Nothing printed changes.** The other gates (one at a time, foreground):

| Gate | Result |
|---|---|
| `validate_weekly_stack` | 83/0 |
| `validate_weekly_edits` | 91/0 |
| `validate_monthly` | 360/0, 1 skipped |
| `validate_monthly_stack` | 260 passed, 0 failed when the 10-minute foreground limit stopped it; CI runs it whole |
| `validate_quarterly_stack` | 94/0 |
| `validate_horizon_charts` | 73/0 |
| `validate_correlation_layer` | 75/0 |
| `validate_batch3_a` | 79/0 |
| `validate_move_screen` | 52/0 |
| `validate_quality` | 48/0 |
| `validate_audit_3a` | 88/0 |
| `check_registry` | OK |

## The operator, per family

The FRED series (DGS10, DGS30, DTWEXBGS) are already pulled every morning, so the
overlap exists from day one: a parallel run is counted, not built.

**To start a family's parallel run:**

1. A session paste moves the family's `inactive_pairs_fred` entries into
   `pairs.list`. A null tolerance prints "not measured" and never flags. The paste
   also sets `parallel_run.started` in `config/price_sources.yaml`.
2. On the box after 20 sessions:

   ```
   python -m altdata.quality measure --db data/chester.db
   ```

   It measures the pair's tolerance over the overlap, which the next paste writes
   into the pair with its reason.

**To switch it:**

1. A session paste sets the family's `source: fred` and `switched_on: <the first
   session>`. It adds `status_extra: superseded` and `superseded_by` to the old
   keys in the registry, and adds `break_labels` to any further block that prints
   the series. That is the one commit per family the brief's section 4 asks for.
2. On the box:

   ```
   python -m altdata.price_sources
   ```

   It must show the family on `fred`. Then run the Weekly's dry run
   (`scripts/run_weekly.sh` as the operator runs it): the tape table prints the
   series-change label beneath its first figure.

## What remains of tranche 2

- **The Cboe index files** (VIX family, VVIX, SKEW; 2 hours) are **held pending
  B89's Doctrine #2 ruling** on the Cboe readers' terms (D40 sends the existing
  Cboe readers to a terms check and a ruling). Nothing for them is built here.
- **The supersession and the Weekly's parallel-run line** (the brief's section
  4.4) are part of the 5 hours of checks, written with each family's switch.
