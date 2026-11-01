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

## A100 (31 Oct 2026): chain-8's three readers of the dollar index

**The finding (A99).** On the merged tree, chain-8 brings three readers that
name `yfinance.mkt_dxy` directly:

- `config/gold_attribution.yaml:19`;
- `config/gold_event.yaml:37`;
- `config/trend_breadth.yaml:52`.

`validate_price_sources` group C greps `config/` for the old keys, so after a96
merges it fails 23/1.

**Why A100's resolver plan was not built.** The resolver keeps no list of
config paths: each config carries a `"price:<family>.<member>"` reference and
its own loader calls `resolve_tree()`. Chain-8's three loaders
(`altdata/gold_attribution.py`, `gold_event.py`, `trend_breadth.py`) call
`yaml.safe_load` directly. The gate also reads the files' text, which a rewrite
at load would not change. So the fix has to edit three configs and three
loaders, and those files exist only on chain-8.

**The ruling (A100, 31 Oct).** Once chain-8 is on main (Wednesday 4 Nov), main
is merged into a96 and A99's proven change (`fbd43be8` on
`a99-merge-week-rehearsal`) is committed on a96, before a96's PR. Each of the
three references becomes `"price:dollar_index.dxy"`, and each loader resolves
its tree. That is step 17a of `docs/briefs/a99-merge-week-script.md`. With it
the stitch needs no hand edit. Rehearsed, it gave `validate_price_sources` 24/0,
`gold_attribution` 41/0, `trend_breadth` 42/0 and `weekly_gold_block` 32/0.

## A101 (1 Nov 2026): stopped at the terms check -- nothing built

**The one read.** OKX's Terms of Service was read once, at
https://www.okx.com/en-us/help/terms-of-service, on 1 Nov 2026 at 02:13 UTC
(31 Oct, 22:13 ET), with the project's User-Agent. HTTP 200. The page reads
**"Updated: 29 October 2026"**.

**The clauses, quoted.**

- **8.1:** "... you will not copy, transmit, distribute, sell, license, reverse
  engineer, modify, publish, or participate in the transfer or sale of, create
  derivative works from, or in any other way, exploit any of our products and
  Services."
- **8.2(d):** "all rights not expressly granted in these Terms are reserved."
- **9.4:** "You may not use the OKX Platform or the Services for any commercial
  purpose unless otherwise explicitly authorized by OKX."

**Why A101 stopped.** The paste says to stop "if the clause on storage or
redistribution has changed".

- No baseline exists to compare against. When OKX was registered (17 Oct 2026,
  crypto-tranche-a-1), `source_registry.yaml` recorded its robots.txt reading
  and "public market-data endpoints, no key", but quoted no terms clause. No
  notes file records one either.
- The page changed on 29 Oct, after the registration.
- On its face, 8.1's "copy" and "create derivative works from" reads against
  storing OKX's candles and deriving marks from them. That is the question the
  Cboe terms raised (D45: held pending Doctrine #2).

So the clause cannot be shown unchanged. That is a ruling for the operator, not
a session's reading.

**Nothing was built.** No writer, key, switch family, pair or reader change, and
`metrics_registry.yaml`, `source_registry.yaml`, `config/price_sources.yaml` and
`config/data_quality.yaml` are untouched. Only the paste (`docs/pastes/A101.md`)
and this section are committed.

**Also for the operator: the same terms cover a live writer.** `perp_venues`
(`altdata/sources/fut.py`) already stores OKX's funding, open interest and
long/short ratio daily, live since 17 Oct. A ruling on 8.1 bears on it too:
leave it, or hold it as B95 held the Cboe readers. This branch does not touch
it.

**For the ruling, the options as the brief and D45 frame them:**

- (a) OKX's public market-data endpoints are read as permitted for own use
  despite 8.1, and A101 is built as specified;
- (b) hold OKX (both the candles and `perp_venues`) pending a terms check at
  Doctrine #2, as the Cboe readers are held;
- (c) crypto marks become a listed gap at the yfinance retirement, as the
  brief's decision 10 does for names OKX does not list. Coinbase stays a
  cross-check only: its terms bar valuations.

**The ruling (D49, 1 Nov 2026).** "A101 held; OKX's clauses 8.1 and 9.4 go to
Doctrine #2 under D2-74 beside the Cboe readers, with the perp-venues writer
running until the sitting."

- A101 stays unbuilt on this branch: no OKX candle writer, no crypto family in
  `config/price_sources.yaml`, no `okx.<asset>_close` keys, no pairs.
- `perp_venues` (`altdata/sources/fut.py`) keeps running unchanged until
  Doctrine #2 (7-8 Nov) rules; nothing here touches it.
- Doctrine #2's agenda item is D2-74: clauses 8.1 and 9.4 (quoted above), beside
  the Cboe readers held under D45.
- The crypto marks stay on yfinance meanwhile; nothing printed changes.
