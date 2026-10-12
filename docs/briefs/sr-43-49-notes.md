# SR-43 and SR-49 — the 10-year's anchors, the twin-deficit fit, the selloff-shape axis: session notes

Branch `sr-43-49-rates-anchor` from `origin/sr-36-basis-proxy` (556f426), which
stacks on AQ-3 parts 1 and 2. Spec: signal-triage batch 4
(`docs/change-order-signal-triage-batch-4-2026-10-06.md`):

- §4.1 and §4.2;
- the SR-43 and SR-49 entries;
- work rows ST4-08, ST4-09 and ST4-15;
- Audit #4 Part III row 3, "adjudicates the four-voice disagreement instead of
  narrating it".

Session A, 12 Oct 2026.

## Gates run

**Not run:** the full local suite (CI is the validate), and anything on the box.
I ran the gates this branch touches one at a time; all are green:

| Gate | Result |
|---|---|
| `validate_rates_anchors` (new) | 23/0 |
| `validate_basis_proxy` | 31/0 |
| `validate_regime` | 404/0 |
| `validate_aq3_series` | 73/0 |
| `validate_weekly_stack` | 68/0 |
| `validate_weekly_edits` | 89/0 |
| `validate_weekly_complete` | 56/0 |
| `validate_weekly` | 100/0 (1 skipped) |
| `validate_figure_budget` | 79/0 |
| `validate_readability` | 63/0 (the PDF is not validated here: no WeasyPrint) |
| `validate_stack_cadence` | 99/0 |
| `validate_monthly_stack` | 261/0 |
| `validate_monthly` | 350/0 (1 skipped) |
| `validate_config_refs` | 27/0 (after the fix below) |
| `check_registry` | OK |
| `validate_gates` | 31/0 |
| `check_library` | 0 failures |

**CI's first run, #301, failed `validate_config_refs`.** The twelve
`fred.oecd_10y_*` ids in `config/rates_anchors.yaml` were not registered. My
local run had passed only because the YAML was still untracked, and the gate
reads tracked files. The fix is a `fred_sr43` bulk block in
`metrics_registry.yaml`, the same way the AQ-3 FRED series are registered.

**CI's second run, #302, was cancelled.** `validate_session_calendar.sh` hit
the 10-minute job limit. The base has the same fault: `sr-36-basis-proxy`'s
last run, #289, was cancelled the same way. `aq-3-series-2` fixed it after
SR-36 branched:

- `01bbfa6`: the gate's stub runs only `-m altdata.session`, not every writer
  live;
- `242a3ad`: the job gets 20 minutes, a stopgap.

Both are cherry-picked here (`5a79969`, `72126ff`). `sr-36-basis-proxy`
itself still lacks them.

**One gate updated.** `validate_monthly_stack`'s "each bucket carries a written
takeaway" check now counts only the buckets. The two SR-43/49 blocks ride after
them with no paragraph of their own.

The Makefile carries the new gate. CLAUDE.md on this branch now reads forty-nine
code gates.

## What was built

**The OECD-yields fetcher** (ST4-09, shared with ST4-15). It is twelve OECD
10-year series added to the existing FRED pull, as `FRED_SR43_SERIES` in
`altdata/config.py`:

- the countries: US, CA, DE, FR, IT, ES, NL, BE, AU, NZ, CH, SE;
- the UK and Japan were already pulled;
- I checked every id against its FRED page on 12 Oct: each exists, and each
  reads "Percent, Not Seasonally Adjusted", monthly (Gotcha 2).

**SR-43, the 10-year's anchors** (`altdata/rates_anchors.py`,
`config/rates_anchors.yaml`). One line gives the 10-year against each anchor,
with the gap in bp and its sign.

- **The inflation anchor** is the trailing ten-year average of CPI YoY, from
  `fred.cpi`. It is labelled as a stand-in for Topdown Charts' unpublished model.
  - **The fit:** OLS of the month-end 10-year on the anchor, over the stored
    history (at least 120 months).
  - **The printed residual** is the 10-year minus the fitted yield, in bp. The
    gap to the anchor prints beside it.
- **The twin-deficit fit:**
  - **The cross-section:** general government balance plus current account
    (% GDP, same WEO year), against the latest OECD 10-year, across 14
    developed markets.
  - **The fit:** OLS with R², refit from the store as of the cutoff.
  - **The US reading:** fitted less paid, in bp.
  - **Where the inputs come from.** It reads the WEO writer's documented keys,
    `em.weo.fiscal_gdp.<iso3>` and `em.weo.ca_gdp.<iso3>`, from
    `altdata/sources/imf_weo.py` on `aq-9a-em-scorecard`.
  - **Built against a fixture of that output, as the paste allows.** The writer
    covers the 13 EM scorecard countries only, so no DM key will exist even
    after it merges.
  - **Degrading.** With fewer than 10 countries it prints "the twin-deficit fit
    needs 10 countries with WEO balances and a 10-year; k of 14 carry them".
- **The term premium:** ACM, unchanged.

**SR-49, the shape axis and the selloff's composition**
(`altdata/rates_shape.py`).

- **The shape:**
  - **correlated:** the daily-filled panel (the US, the Bund, the JGB) has a mean
    pairwise correlation of weekly 10-year changes of at least 0.5 over 13 weeks,
    and every market is higher;
  - **divergent:** a focal sovereign (FR, IT, ES, the UK or Japan) is up at least
    25 bp over 3 months while the Bund's change is at or below 0;
  - **mixed:** otherwise;
  - **not read**, with a reason, when too few series are stored.
- **The composition.** Every non-overlapping 20-session 10-year rise of at least
  25 bp in the stored five years gets:
  - the moves in the 10-year breakeven, the TIPS real yield and the ACM term
    premium;
  - each move's share of the rise;
  - a label: breakeven-led, real-yield-led or term-premium-led, from the
    largest move;
  - a five-year count by label.
- **The four voices, adjudicated.** Each dated claim (batch-4 Appendix B) is read
  against its measure by a declared rule. The verdict is one of: consistent, not
  consistent, not settled, not testable yet, or outside these measures.
  - **Diebel:** read against the shape axis.
  - **Courtial:** read against the fit's gap, at least +25 bp.
  - **Visseau:** read against the 10-year inside 5.0–5.5%; above it, a
    term-premium-led selloff reads as the spiral path.
  - **Sarmaya, "the Fed blinks":** "outside these measures". The fed funds path
    is What's priced's.

**Where it prints.** Plumbing & rates gets two blocks, after SR-36's basis watch:

- the anchors line and the shape line;
- the four voices' table, with "Verdicts by declared rule, not opinion".

Every line carries "(descriptive; unvalidated, n=0)". The section's data carries
the printed figures for its frame, so they reach the prose through the budget.
The Monthly carries both blocks after its six buckets.

## Choices made for the operator to overrule

- **Not on `rates.driver`.** The paste and the batch-4 order put the shape axis
  "on `rates.driver`". That sub-state was withdrawn from the market-state object
  on 30 Sep, after failing its calibration gate twice. `config/market_state.yaml`
  is back at v1.10, and `tools/validate_regime.py` group L asserts the rates
  dimension declares no driver. I built the axis and the composition as a
  report-only descriptive block beside `altdata/rates_attribution.py`.
  `regime.py` imports neither module, and the gate checks that. The rights are
  the same: report-only, no trigger, no book rule.
- **The composition labels the largest leg.** It is not a calibrated cell. The
  old driver's cells failed their gate, and these labels are tagged unvalidated
  and decide nothing.
- **The weekly panel is the three daily 10-years.** The OECD series are monthly
  and carry no weekly change, so the "G7+ weekly" correlation runs on the US, the
  Bund and the JGB. The focal-sovereign test uses the monthly series.
- **The thresholds are session-set:**
  - correlated at a mean correlation of at least 0.5 with every market higher;
  - divergent at a focal rise of at least 25 bp against a Bund change of at
    most 0 over 3 months;
  - a selloff is at least 25 bp in 20 sessions;
  - the fit needs at least 10 countries.
- **The 14 countries** are the US, Canada, the UK, Germany, France, Italy, Spain,
  the Netherlands, Belgium, Japan, Australia, New Zealand, Switzerland and
  Sweden. Courtial's own list is not published.
- **The voices' rules.** Visseau's claim covers both his chop and spiral paths,
  so either reads "consistent". Sarmaya's has no test in these measures and says
  so rather than being forced into a verdict.
- **The interim figure.** No interim Courtial 5.8%-vs-5.3% figure is printed
  (batch-4 §8 decision 4). The fit prints its own number when its inputs exist,
  and says it cannot otherwise.

## Needs you

1. **The shape axis lives outside the market-state object.** Batch 4 puts it on
   `rates.driver`, which was withdrawn on 30 Sep. Keep it as a descriptive block
   (built), or rule a v1.13 / method-11 sub-state with its own pre-registered
   gate? Keep the block / rule the sub-state.
2. **The WEO writer's country list.** The twin-deficit fit needs WEO balances
   for the 14 developed markets, and `imf_weo.py` on `aq-9a-em-scorecard` pulls
   the 13 EM scorecard countries only. Extend that writer's COUNTRIES with the
   14 DMs (one line there plus their registry entries), or give the DMs a writer
   of their own? Extend / separate.
3. **Twelve new FRED series on the box's pull** (the OECD 10-year monthlies).
   They reach the box at the next pull after merge. Yes / no.
4. **Keep the session-set thresholds** (0.5 correlation; +25 bp focal against a
   Bund at or below 0 over 3 months; 25 bp in 20 sessions; 10 countries)? Yes /
   no, or name the changes.
5. **Sarmaya's "Fed blinks"** reads "outside these measures". Leave it, or point
   it at the fed funds path in What's priced? Leave / point it.
6. **`sr-36-basis-proxy` lacks `aq-3-series-2`'s session-calendar fix**
   (`01bbfa6`, `242a3ad`), so its CI is cancelled at the 10-minute limit. I
   cherry-picked both here and left SR-36's branch untouched. Rebase SR-36 on
   `aq-3-series-2`, or let the merge order carry the fix? Rebase / merge order.
