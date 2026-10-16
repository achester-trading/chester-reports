# ST-R4 Tranche 1, part 1: the attribution cluster and the two real-economy series (session notes, 16 Oct 2026)

**This branch, `st-r4-tranche-1`, is cut from the tip of `st-r6-es-block`
(`4dd24ac`, after two CI fixes to that branch; see step 0). So it carries the
stitched chain (`aud-3b-security-master` and everything under it) and the ES
block. Merge order: the chain, then `st-r6-es-block`, then this branch.** Branch
only: pushed, not merged, not deployed, nothing run on the box.

Source: the Batch 5 change order (`docs/change-order-signal-triage-batch-5-2026-10-09.md`,
on main), items 17, 21, 23, 24 and 26; §5 cross-item rulings 1, 2 and 4; §9 verify
items 2, 5, 7, 8 and 10; SR-9 in `docs/signal-triage-register.md`, which item 24
amends. Tranche 1 only: the ledgers (17b, 19b, 20a, 25a) come later. Item 29
(r−g) is session A's, on `st-r5-index`; this branch names it once, as a companion
of item 24, and does not build it.

## Step 0: the two CI reads

**a. `st-r6-es-block`.** Run 38856776755 (`7254de9`) failed: 89 jobs passed, and
`validate_stack.py`, `validate_weekly_complete.py`, `validate_readability.py` and
the summary failed with one fault, an `UnboundLocalError` on `model_meter` in
`stack_close.produce()`. A local import later in the function made the name local
to all of it. Fixed in `44ab334`. Run 38900890862 (`44ab334`) failed: 91 passed,
and `validate_readability.py` and the summary failed. The ES block's absent note
and lines printed ISO dates outside a table. Fixed in `4dd24ac`: dates print as
"28 Sep", and the check was added to `validate_es_block.py` (69 checks). Both
causes were that branch's own. Both are recorded in `docs/briefs/st-r6-45-notes.md`.
`4dd24ac`'s own run is not separate from this branch's (see "CI" below).

**b. `6e-metric-lenses`.** Its last run, 38738521798 (15 Oct), failed. 82 jobs
passed; `validate_audit_3a.py` and the summary failed on one check: "a count in
words is read and caught too ('seventy-four code gates')". The gate's self-test
plants a stale count by replacing the literal string "seventy-five code gates".
6e's own new gate moved CLAUDE.md to "seventy-six", so the replacement found
nothing, planted nothing, and the check that the plant is caught failed. **It is
not 6e's own gate, and it is already fixed on the chain:** the stitched
`validate_audit_3a.py` plants with a regex over whatever count CLAUDE.md prints.
So 6e's red clears when 6e merges after the chain. Left for the 6e paste, as
ruled. The same fragility sat in the next check of that gate (the hard-coded
"27 more in FRED_SIGNAL_SERIES"), and this branch moves that count, so it is fixed
here the same way (a regex).

## What it builds on, and the build order

Cross-item ruling 1 makes the 10-year attribution the arbiter, so its extensions
come first. What the chain already held, and was reused:

- `altdata/rates_attribution.py` (DKW, Kim-Wright, ACM shares) and the
  `calc.attr_*` series in `market_features.py`.
- The ACM writer (`acm.term_premium_10y`, `acm.risk_neutral_yield_10y`,
  `acm.fitted_yield_10y`).
- The ECB convergence-yield writer (DE, FR, IT) and SR-30's OAT-Bund and
  BTP-Bund build (`altdata/batch3.py`, `daily_cascade/batch3_block.py`).
- `calc.net_liquidity` (dollars, every leg normalised) and SR-9's
  `calc.corr_spy_tlt_60d`.
- `batch3.dual_percentiles` (through `derived.percentile_of`).

| New | What |
|---|---|
| `config/batch5_tranche_1.yaml` | every threshold, the session-set ones marked |
| `altdata/batch5.py` | term_premium, fiscal_bark, stock_bond, net_liquidity, construction, verify; `python -m altdata.batch5 show / verify` |
| `daily_cascade/batch5_block.py` | the print: tables and code-written lines only |
| `altdata/sources/census_vip.py` | the Census writer, **HELD for D1c** |
| `tools/validate_st_r4_t1.py` | 48 checks on fixtures, in the Makefile |

| Changed | What |
|---|---|
| `altdata/sources/ecb_irs.py` | Greece added, optional |
| `altdata/batch3.py`, `config/batch3_tranche_a.yaml` | Greece-Bund as a third pair, untiered |
| `altdata/config.py` | PPIDCS in `FRED_SIGNAL_SERIES` |
| `metrics_registry.yaml`, `source_registry.yaml` | five keys, the census_vip source (held), GR on the ECB source |
| `config/catalogue_commands.yaml` | two entries |
| `daily_cascade/weekly_stack.py`, `monthly_macro/stack.py` | the hooks |
| `tools/validate_batch3_a.py` | Greece in its fixture, three checks |
| `tools/validate_audit_3a.py` | the regex plant; PPIDCS declared as a new block member |
| `CLAUDE.md`, `Makefile` | the counts and one paragraph |

## The items, their sources and their fixtures

**1. ST-R4.21b, the term premium printed (verify item 10).** It already printed,
but partly: ACM's 10-year level and change sit in the close's Plumbing
(`stack.plumbing_section`) and in the Weekly's Plumbing table (`PLUMB`), with no
percentile. So it is added where the attribution prints (Plumbing, beside batch
3's tenor table): the level, its change, and its percentile against 5 and 20
years, each with its **n and first date**. A window the store does not fill says
how many years it holds ("10.0 years stored"). ACM is the model, because the
store holds it daily. *Fixture (A):* ten years of daily prints; the 20-year cell
says 10.0 years stored; absent with its reason when nothing is stored.

**2. ST-R4.26a, the fiscal-bark flag.** This is a flag on ACM's own split,
nothing more. It looks at the six calendar months to the latest print. It fires
when ACM's fitted 10-year **rose** at least 25 bp and the term premium carried at
least 0.50 of that rise. The **divergence** fires when the term premium rose at
least 10 bp while the expected short rate (ACM's risk-neutral 10-year) fell at
least 10 bp. The quoted 10-year (FRED DGS10) move prints beside it, never divided.
*Fixtures (B):* a share of exactly 0.50 on a 30 bp rise fires; 0.49 does not; a
20 bp move has no share; a 100 bp rally never fires. The divergence fires at
+12/-11, and not at +9/-11 or +12/-9.

**3. ST-R4.24a/b, SR-9 amended.** SR-9's live reading, `calc.corr_spy_tlt_60d`,
was already the 60-day window. **The "existing 2-year window" did not exist in
code**: it was only SR-9's backlog validation gate, the scatter's 2-year rolling
correlation of weekly changes. So the 2-year window is the new piece. It is the
Pearson correlation of SPY and TLT weekly log returns over 104 weeks, absent below
78 weeks, computed at read time and not stored.

- **Live:** the flag is live when the 60-day reading is above +0.20.
- **Persistent:** when the 2-year window is also positive. SR-9's 5.25% level
  prior prints beside it ("treated as persistent").
- **Strength (24b),** read from the attribution's 60-session window:
  - *strong* when breakeven-led (the real yield's share of the nominal move is
    below 0.5);
  - *weak* when real-yield- or term-premium-led with inflation anchored (the
    10-year breakeven moved less than 15 bp over 60 sessions);
  - *moderate* when not anchored;
  - *unconditioned* with no attribution share.
- **Mechanics, Weekly and Monthly:** it prints in both, with one line naming its
  companions, the quadrant sub-state (item 25, later) and r−g (item 29, session
  A). **Not on the close:** the close's Mechanics builder (`stack.mechanics_section`)
  has no store handle, and threading one through is a change to the close I left
  out of this tranche. If wanted, it is one argument; see "Needs you".

*Fixtures (C):* 0.20 is not live and 0.21 is; the two-year window over 104 weeks;
the five strengths move the right way; 50 weeks is absent; the Mechanics print
names both companions.

**4. ST-R4.17a, net liquidity.** `calc.net_liquidity` already existed, so this
extends it. It adds the 4- and 13-week changes. Each change is split into its legs
in dollars: + Fed assets, − TGA, − RRP, with WALCL and WTREGEN in millions and
RRPONTSYD in billions (the units trap, CLAUDE.md 2). The legs sum to the change.
The leading leg is named with its meaning: TGA transient, RRP little left,
balance sheet durable. It prints in Plumbing and is report only: the modifier waits
for the 17b ledger. *Fixtures (D):* 13 weeks, +$215bn = Fed assets +$10bn, the
TGA's fall +$200bn, the RRP's +$5bn, residual 0. The 4 weeks are TGA-led. A short
series is absent.

**5. ST-R4.21a, Greece-Bund.** The ECB writer now asks for GR beside DE, FR and IT
(`IRS.M.GR.L.L40.CI.0000.EUR.N.Z`; checked 16 Oct: monthly from October 1992, 408
months to September 2026, one blank). Greece is **optional** in the writer's
missing-leg check, so a quiet Greek series can never take OAT-Bund down. The spread
is a third row in SR-30's table, "Greece-Bund, ECB monthly average (a watch
spread)", with its dual percentiles and no tier: the tier is OAT-Bund's alone,
even with `tiers_live`. It is not stored as a `calc.*` series. Like OAT-Bund in
SR-30's table, it is computed from the legs at read time. The sovereign scorecard
is by hand, for you. *Fixtures:* E (writer) and `validate_batch3_a.py` B (the
row, untiered even when wired live).

**6. ST-R4.23a, construction spending, real (verify item 8).** The two series:
data-center construction (real year over year, its share of private
nonresidential, level against 2019), and total construction **ex data centers**
(real year over year, level against 2019). Power prints too, for the XII note.
They are deflated by FRED's **PPIDCS** (PPI final demand: construction, index Nov
2009 = 100, seasonally adjusted, monthly; read off its FRED page 16 Oct: September
2026, 188.186). The paste names "PPI final-demand construction"; FRED's ID for it
is PPIDCS (or PPIFDC, not seasonally adjusted). It goes into
`FRED_SIGNAL_SERIES`, so the existing FRED pull fetches it; it is not a new
writer. The block prints in the Monthly's slow layers under Factor I. No rights
until the Disruptive Themes refresh rules.

**The Census reader is a new writer, so it is HELD for D1c**, on session A's
pattern (`altdata/sources/redfin.py`, `st-r5-rates`). `HELD_FOR_D1C = True`:
`pull()` fetches nothing, writes nothing and returns HELD with its reason. It is on
no feeds roster, and `source_registry.yaml` lists it `status: held`. The slow-layer
block prints "not read — the Census writer is held until D1c's write lock lands".
*Fixtures:*
- **F (the writer):** held, the HTTP reader is poisoned and nothing is written.
  Unheld, it writes into a temporary store. Columns are read by name; a blank
  pre-2014 data-center month and a pre-2002 power zero are skipped, never stored as
  zero.
- **G (the series, by hand):** data centers real +62.5%, nominal +69.9% and
  +441.7% against 2019; ex data centers real -3.5%; share 11.0%; held prints why.

**7. The display.**
- The attribution extensions and net liquidity print in Plumbing (Weekly and
  Monthly); 24 in Mechanics (Weekly and Monthly); Greece-Bund in SR-30's table;
  23 in the Monthly's slow layers.
- Tables and code-written lines only: no paragraph, nothing a model writes. Every
  date outside a table prints as "9 Oct" (`validate_readability`'s rule).
- **Registered with their units** (AUD-3a): `ecb.irs_10y_gr` percent_rate; the
  four `census.vip_*` as usd (millions in the description: the registry refuses
  the FRED-list unit `M` on a single entry); `fred.ppi_construction` through its
  list (idx).
- **The catalogue:** `altdata.batch5` and `altdata.sources.census_vip`, and the
  ECB line names Greece.

## The session-set thresholds, for Ari

All are in `config/batch5_tranche_1.yaml`, marked `session-set`.

| Threshold | Value | Reason |
|---|---|---|
| Fiscal bark: minimum six-month rise | 25 bp | a share of a small move is noise with a large number on it; the attribution's own 5 bp floor, scaled to six months |
| Fiscal bark: term-premium share | 0.50 | "the larger leg", the attribution's own definition, not a tuned number |
| Fiscal bark: divergence | 10 bp each way | big enough not to fire on model wobble |
| Stock-bond: live above | +0.20 (60-day) | above zero by a margin, so a reading wandering around zero does not flicker |
| Stock-bond: two-year minimum | 78 of 104 weeks | three quarters of the window |
| Stock-bond: inflation anchored | 10-year breakeven moved < 15 bp in 60 sessions | — |
| Stock-bond: led cut | 0.5 | the attribution's definition |
| Term premium percentiles | 5 and 20 years | batch 3's pair |

## Verify items

- **2. What drove the September net-liquidity upturn.** On fixtures it is
  answered by construction: a TGA-led September reads TGA-led, and group D holds
  that. From the stored data, the box command `python -m altdata.batch5 verify`
  prints the September window's legs in dollars (`item_2_september`), command 2
  below. Not answered here: the committed store ends on 28 May 2026.
- **5. The 5.25% cross in the week of 5 Oct 2026, from FRED DGS10.** The committed
  snapshot (`data_store/yield_10y.csv`) ends on 28 May 2026, so it cannot answer.
  The same command prints every DGS10 print from 25 Sep to 16 Oct
  (`item_5_dgs10`) and those at or above 5.25 (`item_5_crossed`). The appendix
  line below waits on it.
- **7. "Economy at war" context.** Not sourced. Held as narrative, as the item
  rules, and not printed anywhere.
- **8. The Census VIP data-center line.** Answered (16 Oct). The Census
  time-series API now refuses requests without a key, and a session creates no
  keys, so the writer reads the keyless workbooks
  (`census.gov/construction/c30/xlsx/privsatime.xlsx` and `totsatime.xlsx`).
  - "Data center" is its own private nonresidential type, under Office, monthly,
    seasonally adjusted annual rate (and not seasonally adjusted in
    `privtime.xlsx`).
  - It runs from **January 2014**: 152 months to August 2026, which is 84,950
    SAAR, preliminary. It is blank before 2014. Last-Modified is 1 October 2026.
  - Total construction runs from January 1993. Its detailed types run from 2002
    only; the workbook's footnote says so, and the cells print 0 before then.
- **10. The term premium printed?** Partly (level and change, no percentile);
  now with its dual percentiles. Hyperscaler capex-guidance revisions are not
  tracked: SR-38's line is forward-EPS revisions, not capex guidance. So item 26's
  capex series stays by hand, as ruled. XI coverage (20), XIII implied correlation
  (18) and the Factor IV fiscal impulse (22) belong to items outside this tranche
  and were not checked.

## The by-hand drafts, for Ari

**26, the narrative-register disagreement pair "what's driving 5.3%".** Draft:
`id: what_driving_5_3; kind: disagreement; side_a: fiscal -- the term premium is
the long end pricing debt (Kovač, TAAI; Hartnett, BofA); side_b: capital
competition -- private demand for capital repricing the expected path and r*
(Boivin, BlackRock Investment Institute; Rai); adjudicator: the fiscal-bark flag
on the 10-year attribution, monthly -- side A when the term premium carried at
least half of the six-month rise, side B when the expected short rate did;
review: monthly.`

**26, hyperscaler capex-guidance revisions, quarterly by hand.** One row per
hyperscaler per quarter:

| Company | Quarter | Prior guide | New guide | Revision % | Call date | Source URL |
|---|---|---|---|---|---|---|

Boivin's "+30% in H1 2026" is the reference to check against.

**26, the reading shelf.** Add to `docs/reading/watchlist.json` through the
shelf's change-order mechanism: "BlackRock Investment Institute -- weekly
commentary, midyear and year-ahead outlooks", tag house view, and AQR
(Alternative Thinking, Cliff's Perspectives) per §8.

**24, the dated appendix line** (waits on verify item 5): "The 10-year Treasury
yield (FRED DGS10) closed at or above 5.25% in the week of 5 Oct 2026 — [dates and
closes from `altdata.batch5 verify`] — the first time since 2002; verified from
FRED, not from the chart."

**24, the Book A rule-table edit** (A-1, amended; yours, and the rule table is
not touched here): "While the stock-bond flag is live, Treasury duration loses
hedge status. Replacement diversifiers per the item-25 map: T-bills, gold,
commodities, trend-following, defined-outcome option structures. Strength
strong (breakeven-led): full substitution. Moderate: partial. Weak (real-yield-
or term-premium-led, inflation anchored): duration kept, sized down. The flag's
threshold and strength rules are config/batch5_tranche_1.yaml's."

**23, the XII power disagreement note.** "Census VIP, August 2026 (preliminary,
SAAR): total power construction +8.5% nominal year over year, against data
centers +73.2% (the poster's real figures: +4.1% and +64.5%). Power is growing at
a fraction of the data-center pace, which cuts against XII's power-buildout
thesis. Logged as a disagreement, not resolved." Also the base-rate note:
manufacturing's fall is mostly the CHIPS and IRA fab boom rolling off, a base
effect, which is why the level against 2019 prints beside the year over year.

**21, the sovereign scorecard.** Yours, quarterly, from the IMF Fiscal Monitor and
the OECD. Columns: GFN/GDP, interest-to-revenue, weighted average maturity,
foreign-held share and primary balance, for US, DE, FR, IT, GR, JP and UK.
Nothing drafted beyond the layout.

## Box commands, for Ari (inside a window; nothing here was run on the box)

No unit file changed, so there is nothing to deploy or restart. PPIDCS and Greece
arrive at the next scheduled pulls after the merge.

1. Optional first pulls, so the rows are there before the next timers (two
   fetches, so they are yours):
   `ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.sources.ecb_irs | tail -20'`
   `ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.feeds pull --only fred | tail -20'`
2. Verify items 2 and 5 from the stored data (reads only):
   `ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.batch5 verify'`
3. What the blocks would print today (reads only):
   `ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.batch5 show | head -120'`
4. The Census writer stays held. After your D1c ruling, lifting it is two edits
   (`HELD_FOR_D1C = False`, and `census_vip` in `altdata/feeds.py`
   EXTERNAL_WRITERS), then a first pull:
   `ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.sources.census_vip'`

## Files shared with the open branches

`st-r5-index` has no remote branch yet, so it could not be compared.

| Shared with | Files | At merge |
|---|---|---|
| `st-r5-rates` (session A) | `altdata/config.py` | both add FRED signal series; mine sits mid-list, theirs at the end |
| `st-r5-rates` | `metrics_registry.yaml` | `fred_signal_triage.expected_members`: theirs 29, mine 28; together 30 |
| `st-r5-rates` | `CLAUDE.md` counts | `FRED_SIGNAL_SERIES` 29 / 28, so 30; `FRED_PULL_SERIES` 131 / 130, so 132; the gate count |
| `st-r5-rates` | `tools/validate_audit_3a.py` | `NEW_BLOCK_MEMBERS` (take the union); the stale-count plant (take my regex) |
| `st-r5-rates` | `daily_cascade/weekly_stack.py`, `monthly_macro/stack.py` | one hook each, in different functions |
| `st-r5-rates` | `source_registry.yaml`, `config/catalogue_commands.yaml`, `Makefile` | appends in different places |
| `6e-metric-lenses` | `CLAUDE.md`, `Makefile`, `metrics_registry.yaml` | the gate count; registry entries in different places |
| `docs-batch-6` | none | |

## CI

Locally, only the gates this branch writes or changes were run, one at a time:
- `tools/validate_st_r4_t1.py`: 48 passed, 0 failed.
- `tools/validate_batch3_a.py`: 62 passed, 0 failed.
- `tools/validate_audit_3a.py`: 83 passed, 0 failed.
- `tools/check_registry.py`: OK.
- On `st-r6-es-block`, `tools/validate_es_block.py`: 69 passed.

This branch's CI run is read once, after the push; see the session report.

## Needs you

1. **D1c.** The Census writer is the third held writer, after Redfin and MBA on
   `st-r5-rates`. One ruling lifts all three. The construction block prints its
   hold until then, so item 23 cannot print on 1 Nov unless the hold is lifted.
2. **The session-set thresholds above**, the fiscal-bark three and the
   stock-bond four above all.
3. **Item 24 on the close.** It is in the Weekly's and Monthly's Mechanics but
   not on the close: the close's Mechanics builder has no store. Say if it should
   be there, and it is one argument to thread.
4. **The by-hand drafts:** the disagreement pair, capex revisions, the shelf
   addition, the appendix line (after verify item 5), the Book A rule-table edit,
   the XII note and the scorecard.
5. **Run box command 2** for verify items 2 and 5.
6. **6e's red** clears when 6e merges after the chain: nothing for 6e to fix.
