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

## A102 (1 Nov 2026): earnings dates and fundamentals from EDGAR, behind the switch

**Base.** `origin/a96-price-migration-fred` at `42e5e7f9` (A101 held, D49), on
this branch. The paste is `docs/pastes/A102.md`. Both families ship on
yfinance, so nothing printed changes.

### Fundamentals: the tag table

`config/edgar_xbrl.yaml` `fundamentals`. Each tag is an element of the FASB US
GAAP taxonomy (us-gaap), as EDGAR's company facts serve it, and each field's
`cite` names it beside the Yahoo row it replaces. The table has 5 fields and
10 tags, for 9 filers and 40 keys:

| Field | Tags, first wins | Note |
|---|---|---|
| `operating_cash_flow` | NetCashProvidedByUsedInOperatingActivities | Yahoo's "Operating Cash Flow" |
| `capex` | PaymentsToAcquirePropertyPlantAndEquipment, else PaymentsToAcquireProductiveAssets (Amazon's) | filed positive, stored **negative**, as Yahoo publishes it |
| `net_debt` | LongTermDebt (else LongTermDebtNoncurrent) less CashAndCashEquivalentsAtCarryingValue (else the restricted-cash total) | **not Yahoo's definition**: its Total Debt carries leases and commercial paper where filed there |
| `inventory` | InventoryNet | AMZN, GOOGL, MSFT and MU only, as Yahoo |
| `cogs` | CostOfGoodsAndServicesSold, else CostOfRevenue | Yahoo's "Cost Of Revenue" |

- **Keys.** `edgar.fund_<ticker>_<field>`, 40, the twins of Yahoo's 40 member for
  member (`edgar_xbrl.FUND_KEYS`). They never write over Yahoo's.
- **The frame.** These are quarters, observed_at the fiscal quarter's end. A 10-Q
  files its cash-flow lines year to date. A quarter not filed as three months is
  the year-to-date less the previous quarter's year-to-date from the same start;
  Q4 is the fiscal year less nine months.
- **Availability.** Each row is available at its filing's **acceptance** (the
  submissions index's `acceptanceDateTime` for the fact's accession), kind
  `observed`. A derived quarter takes the later of its two acceptances. A later
  filing restating a period is a revision row at its own acceptance. An accession
  missing from the index takes its `filed` day's end in ET, kind `reconstructed`.
  The history runs from `quarters_from` (2019-01-01); company facts serve back to
  about 2009.
- **Gaps by name.** None of the nine is an IFRS filer or a bank, so no name is
  listed as a taxonomy gap. A field a filer does not tag writes nothing and shows
  in the first pull's `keys_without_rows`. **Not probed live**: this paste made
  no EDGAR call, so whether each filer carries each tag is shown by the
  operator's dry run (below), not asserted here.
- **Registry.** The `bulk_imports` block `edgar_fundamentals` is A93's shape:
  `members_from: altdata.sources.edgar_xbrl.FUND_KEYS`, `status_extra:
  not_yet_sourced` (the registry's word for "pending"), `expected_members: 40`.
  `validate_audit_3a`'s NEW_KEY_BLOCKS declares it, placed away from A93's line so
  the two merges do not touch.

### Earnings dates: past from EDGAR, forward a listed gap

- **Past dates.** Written as events of type `earnings` under source `sec_edgar`.
  observed_at is the acceptance of the **8-K carrying item 2.02**. The quarter is
  the latest 10-Q/10-K period end before it, within 100 days.
- **Reported EPS.** Diluted EPS as first filed for that quarter as three months
  (EarningsPerShareDiluted, else EarningsPerShareBasicAndDiluted).
- **The cost of point-in-time.** The 8-K's press release carries no XBRL, so the
  EPS is knowable only at the periodic report. The event is written once that
  10-Q/10-K is accepted, available at the later instant. A report whose 10-Q is
  not yet in is not written yet. Large names file within days; the banks file
  their 10-Q about a month after the 8-K. **For the switch's paste:** the
  Weekly's "reported this week" block would lag by that gap. The alternative,
  a date-only event at the 8-K, means two rows per quarter or no EPS.
- **Q4.** A fourth quarter is rarely filed as three months, so it carries no EPS
  ("not filed as a quarter"). It is never the year less nine months, because EPS
  does not subtract.
- **The consensus was Yahoo's.** It came from `Ticker.calendar`'s
  "Earnings Average" and `get_earnings_dates`' EPS estimate, in
  `altdata/sources/earnings.py`. EDGAR has none, so **from the switch the
  surprise is a listed gap** (`eps_estimate` and `surprise_pct` null, `consensus`
  "not tracked (the consensus was Yahoo's; no keyless source)"). The paste's
  "the surprise come[s] from EDGAR" holds only for the reported EPS.
  `calc.earnings_surprise_pct` and `surprise_index`'s earnings z stop accruing at
  the switch.
- **The forward-date finding.** One look on 1 Nov 2026 at 13:09 UTC (08:09 ET):
  - Nasdaq's is the only exchange earnings calendar. www.nasdaq.com/robots.txt
    and its terms of use both timed out after 60 s to an automated client, so
    neither could be read, and nothing that cannot be read passes the 16 Oct rule.
  - NYSE publishes no earnings calendar.
  - The companies' investor-relations pages carry only their own dates.
  - So, as decision 10 says, the forward date is the listed gap: **"next report
    date: not tracked (no keyless source)"** from the switch.
    `price_sources.gap("earnings_dates", "next_date")` returns it. The Weekly's
    Ahead prints it once in its notes, and the Weekly payload's earnings block
    takes state `not_tracked` with it as the reason. Unswitched, nothing prints.

### The switch and the readers moved

- **`config/price_sources.yaml`, two families.**
  - `fundamentals` has 40 members `{yfinance, edgar}`, and its break label names
    the definitional change.
  - `earnings_dates` is an **events family**: its members name the events
    table's `source` (`history`: yfinance or sec_edgar; `next_date` and
    `consensus`: yfinance only, with their `gaps` lines).
- **`altdata/price_sources.py`.**
  - `gap()` returns a member's gap line.
  - `events_clause()` is the one filter, in SQL. Unswitched, it excludes EDGAR's
    earnings rows. Switched on D, it keeps Yahoo's rows before D and EDGAR's from
    D, never both. A source the family does not name, such as a gate's fixture,
    passes either way.
  - `event_ok()` is its mirror for a row in hand.
  - The CLI prints a gap line in place of a missing key.
- **The readers.** One central move covers about ten readers, and nine direct SQL
  reads in six files carry the clause.

| # | Where | What moved |
|---|---|---|
| 1 | `altdata/events.py` `EventStore._rows` | every `since()`/`calendar()` reader: `earnings_moves.record_due`, `events_block`, `evening_note`, `story_block`, `surprise` (the real surprise), `relative_volume`, `volatile_day`, `weekly_payload` (the earnings-ahead rows), `opening_setup`'s calendar read |
| 2 | `daily_cascade/weekly_sections.py` | the week's calendar rows; `earnings_season` (both counts); `earnings_block`, the Weekly's earnings block |
| 3 | `daily_cascade/weekly_stack.py` | the story status's earnings dates |
| 4 | `daily_cascade/opening_setup.py` | `reactions()`, OS-11's last three reactions in the Ahead |
| 5 | `altdata/narratives.py` | the earnings evidence |
| 6 | `altdata/pe_dispersion.py` | `_eps` |
| 7 | `alpha/event_rates.py` | `earnings_rows`, the lab's earnings base rates (the resolver is not on the lab's import blocklist) |
| 8 | `altdata/ai_fcf.py` | `_key()` through `price_sources.key("fundamentals", ...)`. A name no writer carries reads as missing, as before |
| 9 | `config/narratives.yaml` | the capex story's four metrics, as `price:fundamentals.*`, resolved by `narratives.load_config()` |

- **The rest of the paste's list needs no move.** `capex_chain` reads EDGAR's
  annual `edgar.xbrl_capex` already; `eps_overshoot` names no source (F3); the
  forward-date half of the Ahead is the gap line above.
- **`altdata/events.py` was not in the paste's shared files.** It is where the
  readers' common read lives, the analogue of A96 moving a config's loader.
  `write_many` gains `availability_kind` (default unchanged) so the backfill
  stamps EDGAR's acceptances `observed`.
- **For the switch's paste:** resolving the capex story's metrics in
  `narratives.load_config()` means a switch re-seeds that story with EDGAR's keys.
  Whether a forecast already emitted should resolve against the key it was
  emitted on is a narrative-ledger question.

### The writer and the pairs

- **The writer.** `altdata/sources/edgar_xbrl.py` (no new SEC caller; it is
  already on `validate_secrets` group J's list).
  - It makes one companyfacts call and one submissions call per name, through
    `edgar.user_agent()`.
  - **The request rate is not in `user_agent.py`**, which carries the header
    only. So the caller paces itself (`request_pause_s` 0.15 s, under the SEC's
    ten a second), and the gate holds it.
  - Both parts ship **`enabled: false`**. The daily `pull()` adds them only once
    enabled.
  - `python -m altdata.sources.edgar_xbrl fundamentals|earnings [--dry-run]` is
    the operator's command for one part; its first run is the backfill.
- **The pairs.** `config/data_quality.yaml` `inactive_pairs_edgar` holds 41
  pairs: 40 company-quarter pairs pinned Yahoo against EDGAR, and one events
  pair (report day and EPS). All are inactive with tolerance "to be measured on
  the overlap", and the quality check does not read them. Yahoo is restated and
  EDGAR as first filed, and net debt differs by definition, so a gap is measured,
  not assumed away.

### The operator's steps

1. **The dry runs** (on the box, `CHESTER_SEC_CONTACT` set):

   ```
   python -m altdata.sources.edgar_xbrl fundamentals --dry-run
   python -m altdata.sources.edgar_xbrl earnings --dry-run
   ```

   The first names any key without rows: a filer that does not carry a tag,
   which the next paste lists as a gap by name. The second counts the events and
   names the symbols with no CIK.
2. **The backfill and the parallel run.** The same two commands without
   `--dry-run`. Then a session paste sets both `enabled: true` and
   `parallel_run.started`, and moves the pairs into the quality check.
3. **Measure, then switch.** After 20 sessions:
   `python -m altdata.quality measure --db data/chester.db`. Fundamentals change
   quarterly, so the overlap is a season's filings, not 20 rows. Then the switch:
   `source: edgar`, `switched_on`, and the registry's supersession, as section 4
   asks.

### Gates (one at a time, foreground)

| Gate | Result |
|---|---|
| `validate_price_sources` | 59/0 (24 before: groups F, G and H and the EDGAR pairs added) |
| `check_registry` | OK |
| `validate_lenses` | passed |
| `validate_secrets` | passed |
| `validate_ai_fcf` | 27/0 (the TSM case first failed; `_key` now falls back) |
| `validate_gtm` (the EDGAR gate) | passed |
| `validate_st_t1_rest`, `validate_official_sources` | passed |
| `validate_batch12`, `validate_events`, `validate_narratives` | passed |
| `validate_opening_setup` | passed |
| `validate_weekly_calendar` | 44/0 |
| `validate_weekly_complete`, `validate_weekly_stack`, `validate_weekly`, `validate_weekly_storyline` | passed |
| `validate_weekly_edits` | passed (check 9 first caught the gate's temporary directories; now `gate_tmp`) |
| `validate_quarterly_stack` | passed |
| `validate_alpha`, `validate_alpha_lab_3`, `validate_alpha_no_orders` | passed |
| `validate_a48_batch11`, `validate_secondary_notes` | passed |
| `validate_quality` | 48/0 |
| `validate_audit_3a` | 88/0 (after declaring the block) |
| `validate_monthly` | 359 passed, 1 failed, 1 skipped. **The same on the unchanged tip** (`42e5e7f9`): the refunding-window case, which depends on today's date (November), not on A102 |
| `validate_stack` | stopped at the 9-minute foreground limit; CI runs it whole |
| `validate_monthly_stack` | not run on the laptop (it was stopped for time on A96 too); CI runs it |

No gate was added, so CLAUDE.md's counts are unchanged.

## A104 (2 Nov 2026): A102's EDGAR dry runs on the laptop -- PENDING, no request made

The paste names `docs/briefs/a102-notes.md`, but A102's notes are the section
above in this file, so A104's section sits here beside them.

**Base.** `origin/a96-price-migration-fred` at `1ee24f78` (A102).

**The header check.** `edgar.user_agent()` builds the SEC header as
`chester-reports/1.0 (<contact>)`. The contact is `CHESTER_SEC_CONTACT`, read
through `altdata/secrets.get` from the environment or `.env`, so it is
configuration and never a literal in code. On the laptop it is **unset**, so
there is no header at all and the caller sends nothing to sec.gov (the 16 Oct
rule: no SEC request without the operator's contact).

**Part 1, the dry runs, as written** (2 Nov 2026, about 04:00 UTC, from the
branch's venv):

```
$ python -m altdata.sources.edgar_xbrl fundamentals --dry-run
edgar_xbrl: PENDING -- not configured: CHESTER_SEC_CONTACT is unset, and EDGAR serves no request without a contact (nothing written; nothing stored yet)
{"reason": "not configured: CHESTER_SEC_CONTACT is unset, and EDGAR serves no request without a contact", "run_id": null, "session": "2026-11-01", "source": "edgar_xbrl", "status": "PENDING", "written": 0}
(1 s; 0 requests)

$ python -m altdata.sources.edgar_xbrl earnings --dry-run
(the same PENDING line and record; 0 s; 0 requests)
```

**Parts 2 and 3 were not run.**

- With no request made there are no rows, so there is no gap to name, no
  alternate tag to look up in a company's facts, and no earnings dating to read.
- `config/edgar_xbrl.yaml` and the fixtures are unchanged. No fallback was added
  and no `validate_price_sources` case, since a fallback without the dry run's
  evidence would be a guess.
- I did not set a contact. The address is the operator's, and the paste allows
  no source but A102's caller.

**What is needed, the operator's choice:**

- **(a)** Put `CHESTER_SEC_CONTACT` in the laptop's `.env` (the same value as the
  box's), and a session re-runs A104 from Part 1.
- **(b)** Run the two commands on the box, where the contact is set, and paste
  the output to a session for Parts 2 and 3.

**Gates.** None run. No code, config or fixture changed: this commit holds the
paste and this section only.
