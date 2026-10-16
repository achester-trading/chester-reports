# ST-R5 index — "What's carrying the index" (items 40, 29, 35) and the allocation block (item 30), Tranche 1: session notes

**Builds on `st-r5-rates`, and merges after it.** Branch `st-r5-index` from
`st-r5-rates` at `6c22103` (that branch's CI fix), which stacks on the stitched
chain (`aud-3b-security-master`, `2fb1048`). The merge order is:

1. the stitched chain;
2. `st-r5-rates`;
3. this branch.

It must not merge ahead of either. It carries `8ac992b`, the same change as
`st-r5-rates`' `39414dc` (store ids out of printed reasons): one content,
cherry-picked, so the merge takes it once. `st-r5-rates`' notes commit
`1dc5d69` is not on this branch.

Spec:

- **The Batch 6 order** (`docs/change-order-signal-triage-batch-6-2026-10-15.md`,
  on `docs-batch-6`): items 30, 35 and 40; section 4, rulings 2 and 3; section 8,
  verify item 7; section 11, filing note 5.
- **The Batch 5 order:** item 29; section 5, rulings 1 and 2.
- **The register:** SR-12, SR-37 and SR-38.
- **The 25 Sep order's integration rules.**

Session A, 16 Oct 2026. Branch only: pushed, not merged, not deployed, nothing on
the box.

## Needs you

1. **The first S&P DJI drop is still pending** (filing note 5). Until
   `sp-500-eps-est.xlsx` lands in `chester-vendor-checks/spdji`:
   - the forward legs of the decomposition print "awaiting the estimates
     workbook (drop pending)";
   - r−g and the revisions-turn flag print the same;
   - the read line falls back to the **trailing** version (Shiller), labelled
     with its earnings' as-of month.

   The flag needs two drops 28 days apart. The forward anchors fill as the drops
   age: twelve months needs a drop a year old, and the 12 Oct 2022 anchor needs
   one from then. Until then those anchors print "no S&P DJI drop stored on or
   before …".
2. **How g is defined is a choice for you to confirm.** The order says "the
   2-year-forward EPS CAGR from S&P DJI's estimates file". The reader stores the
   estimates block only; trailing actuals are not stored, and its layout is
   declared, not read off a file.
   - **As built:** g = E(quarters 5–8) / E(quarters 1–4) − 1, the growth the
     estimates imply into the second forward year, labelled so.
   - **The alternative:** a two-year CAGR from trailing actuals. It needs an
     actuals block declared in `config/spdji_eps.yaml`. That is safer after the
     first real drop shows the layout; the first drop is the reader's
     acceptance.
3. **What W11 displaces.** It sits before W10 in the Weekly's plan, and the ten
   charts fill the cap of 10.
   - **With a contradiction open:** W6 takes a slot and **W10 (prediction
     markets) is set aside**. Otherwise nothing is displaced.
   - **If you would rather keep W10:** move W11 after it, and W11 becomes the one
     set aside.
   - **The Monthly:** M11 makes twelve planned. Eleven render while M8 waits for
     scenario set #1, so **M11 displaces nothing**. Once M8 prints, twelve fill
     the cap exactly.
4. **Where r−g prints: the two orders disagree.** Batch 5's ruling 2 puts r−g in
   Mechanics, with the correlation cluster. Batch 6's ruling 2 and this paste put
   it in What's priced, under "What's carrying the index". Built as the later
   order says; one line moves if you rule otherwise.
5. **ICI is a listed gap.** ici.org answers this repo's agent with 403 at its CDN,
   robots.txt included (checked 16 Oct). A writer never passes for a browser.
   - **What would fill it:** an inbox drop, the S&P DJI pattern. That is a new
     writer behind D1c's write lock, and a habit for you.
   - **Meanwhile:** the AAII allocation survey, already registered by hand
     (`manual.aaii_*_pct`), is the monthly reading between Z.1 releases.
6. **D1c holds nothing back on this branch.** Every series rides an existing
   writer: the FRED pull (four series added), the S&P DJI inbox reader, and
   `tools/manual_input.py`. No new writer is built, so there is no
   `HELD_FOR_D1C` module here. ICI is the one source that would have been new
   (item 5).
7. **The session-set thresholds** are in "Thresholds" below. Overrule any in
   `config/st_r5_index.yaml`.
8. **Two by-hand drafts for you** (the register and the rule table are yours):
   below, under "Drafts".
9. **The Monthly asks the writer for a read of the allocation block.** This
   follows T3.1 item 10, every Positioning sub-section with figures gets one, so
   the model writes one more paragraph a month. It uses the standard scope:
   level, change on the prior quarter, its place in its own history.
   `validate_monthly_stack` holds it.

## Gates run

**Locally, one at a time, only the gates this branch writes or changes:**

| Gate | Result |
|---|---|
| `validate_st_r5_index` (new) | 56/0 |
| `validate_st_r5_rates` (reasons by name, not store id) | 69/0 |
| `validate_weekly_edits` (the chart plan, Positioning's eighth sub-section, What's priced's fourth) | 90/0 |
| `validate_monthly_stack` (twelve charts, M11's place, the allocation read) | 266/0 |
| `validate_audit_3a` (the FRED counts, four declared block members) | 83/0 |
| `check_registry` | OK |

Every other gate, and anything that renders a PDF, is left to CI.

**One fault found and fixed on both branches.** `validate_weekly_edits` refuses
any `fred.`/`yfinance.`/… id in a rendered edition. This branch's decomposition
reason named `yfinance.mkt_gspc`, and three of the rates cluster's reasons named
keys. All now name the series.

## CI

| Run | Commit | Result |
|---|---|---|
| 38904790271 | `0a55984` (the build) | failure, 92 of 94 jobs passed |
| 38905177161 | `e5677f4` (the notes) | failure, 92 of 94 jobs passed |

**The verdict: both failed on this branch's own change, and it is fixed.** In each
run the one failing gate was `validate_stack_cadence`, plus the `gates-passed`
roll-up that follows from it. Its check "positioning at 'monthly' prints no week
phrase" caught the allocation block's table note, which said Z.1 arrives "with
about a ten-week lag". A Monthly prints no week word. The note now says Z.1 is
"published about seventy days after the quarter ends". `validate_stack_cadence`
passes locally after the fix (99/0), and so does `validate_st_r5_index` (56/0).
The run for the fix commit is read once and recorded below.

## What was built, item by item

### ST-R5.40a — the standing decomposition (`altdata/st_r5_index.py` `decomposition`, `read_line`, `chart_series`)

- **The identity:** price = EPS × P/E, so ln(P1/P0) = ln(E1/E0) + ln(PE1/PE0),
  exactly. Each leg's log share of the move prints when |ln(P1/P0)| ≥ 0.01, SR-38's
  rule.
- **The data:**
  - **Price:** the S&P 500 close (`yfinance.mkt_gspc`).
  - **Forward EPS:** S&P DJI's bottom-up operating EPS from the operator's drops
    (`spdji.fwd12m_op_eps`). At an anchor, the drop on or before it.
  - **Trailing EPS:** Shiller's monthly trailing twelve months
    (`shiller.sp_earnings`), beside it because forward EPS carries item 29's
    revisions caveat.
  - Both are SR-38's series; its identity is reused, not rebuilt.
- **The anchors:** the 12 Oct 2022 low, twelve months, and year to date (the
  prior year's last close).
- **The carrier read:** names the leg whose log contribution runs with the price
  and is larger, or says that one leg works against the move.
- **Where it prints:**

  | Report | What |
  |---|---|
  | Weekly | twelve months and YTD, forward and trailing; chart **W11** (twelve months) |
  | Monthly | all three anchors with the log-share split; chart **M11** (since the low) |
  | Close | the one-line read only, in What's priced |

- **The chart:** the S&P 500, EPS and the P/E indexed to 100 at the anchor, one
  point per earnings observation and the latest close (`daily_cascade/charts.py`
  `index_carry`).
- **Fixtures:** hand-computed (gate A), and the chart's lines (gate E):

  | Anchor | S&P 500 | Forward EPS | Earnings' log share |
  |---|---|---|---|
  | Cycle low | 3600 → 7800 | 240 → 360 | 0.405465 / 0.773190 = **52.4%** |
  | Twelve months | 6000 → 7800 | 300 → 360 | 0.182322 / 0.262364 = **69.5%** |
  | Year to date | 6600 → 7800 | 315 → 360 | 0.133531 / 0.167054 = **79.9%** |

### ST-R4.29a — r−g and the revisions-turn flag (`growth`, `r_minus_g`)

- **r−g:** the 10-year (`fred.yield_10y`) less g, printed with the 10-year.
- **g:** from the latest drop. See needs-you item 2 for its definition.
- **The flag:** forward EPS "flat or falling" over 28 days while the 10-year is
  up.
  - **"Flat or falling"** is SR-38's constant-quarter revision
    (`return_attribution.index_revisions`): the same four quarters in the drop 28
    days earlier, so the window's roll never reads as a revision.
  - **Beside it:** the price–ULC gap's closing state, as the order's leading
    input.
- **Rai's regression is logged, not built.** It is a Bloomberg regression of
  daily SPX changes on daily 10-year changes, Apr–Oct 2026 (correlation −0.53,
  R² 0.28). It is supporting evidence for Batch 5 item 24's amendment: positive
  stock–bond return correlation at daily frequency. Item 24 is session B's,
  `st-r4-tranche-1`.
- **Fixtures** (gate B):
  - **g:** 392 / 355 − 1 = 10.42%; r−g = 5.05 − 10.42.
  - **The flag:** fires at revisions +0.25% with the 10-year +15 bp; not at
    +0.30%; not with the 10-year +9.9 bp.

### ST-R5.35a — the corporate-price/ULC gap (`price_ulc`, `margin_line`)

- **The legs**, both added to the FRED pull and each read off its FRED page on
  16 Oct:
  - PPI final demand less foods, energy and trade services: **WPSFD49116**, an
    index, monthly, SA, from Aug 2013. So the change on the year starts in Aug
    2014, and its percentiles say so.
  - Unit labor costs, nonfarm business: **ULCNFB**, an index, quarterly, SA,
    from 1947.
- **The gap:** PPI's change on the year less ULC's, in pp. ULC's latest quarter
  is carried forward to the next print and labelled so.
- **The flag:** closing from above, a leading input to item 29's flag.
- **The margin-source line** (pricing against cost) goes in the earnings block
  in season and in the sub-section outside it.
- **Not built now:** the "collision course" narrative line (drafted below) and
  the ledger, ST-R5.35b.
- **Fixtures** (gate C): +5.0% against +1.5% (Q2, carried) is +3.5 pp. The flag
  fires at 1.0 pp off the peak and not at 0.9.

### ST-R5.30a — the three-panel allocation block (`allocation`; amends SR-12)

- **Equities:** the Fed's own published share, **BOGZ1FL153064486Q**: households'
  directly and indirectly held corporate equities as a percent of financial
  assets, quarterly from 1945. Added to the FRED pull with `member_units:
  percent_share`, so it moves in pp.
- **Bonds and cash:** the existing Z.1 legs over **TFAABSHNO** (total financial
  assets, millions, added):
  - **Bonds:** debt securities directly held, `HNODSAQ027S`. Z.1 does not split
    fund shares by type, so bond funds are not in it; labelled.
  - **Cash:** currency, deposits and money funds, `DABSHNO`.
- **Percentiles:** each panel prints five years and full history, each with its
  window and n. A short history prints one, named as shorter.
- **The monthly reading:** AAII by hand; ICI a gap.
- **The equities panel's base rate:** "base rate: after ST-R5.30b".
- **Where it prints:** Positioning & flows, every cadence. An absent panel goes
  to the footnote, never to an empty row asking for a read.
- **Fixtures** (gate D): 106 quarters; n=20 for five years and n=106 for full
  history.

## Verify item 7 — answered

**The question:** does the Z.1 household equity-share construction match the
published forward-return studies?

**No, and the difference matters for ST-R5.30b, not for this block.**

- **The published predictor is a market-wide construct.** It is the
  aggregate-investor-allocation construct the entry cites (Livermore, 2013), and
  its forward ten-year regressions are run on it: the market value of all
  corporate equities over that value plus the debt liabilities of the
  real-economy borrowers.
- **Every component is on FRED,** each "Millions of U.S. Dollars", quarterly,
  checked 16 Oct:

  | Leg | Series |
  |---|---|
  | Equities | `NCBEILQ027S` + `FBCELLQ027S` |
  | Debt: households | `TCMILBSHNO` |
  | Debt: nonfinancial corporate | `TCMILBSNNCB` |
  | Debt: noncorporate | `TCMILBSNNB` |
  | Debt: federal | `FGTCMDODNS` |
  | Debt: state and local | `SLGTCMDODNS` |
  | Debt: rest of world | `DODFFSWCMI` |

  `DODFFSWCMI`'s page says "Seasonally Adjusted Annual Rate" though its title
  says Level; 30b should confirm it.
- **The household share is a different series.** `BOGZ1FL153064486Q` is one
  sector's portfolio weight. The two co-move, but the published regressions are
  not on it.
- **What was used:**
  - the live panel prints **the household share**, as ruled ("the Z.1 household
    share");
  - ST-R5.30b should regress on **the aggregate construct**, with the household
    share as a robustness row;
  - 30b is offline under the calibration rule and pulls FRED directly, so it
    needs no store series.
- **Not confirmed:** the original paper was not re-fetched this session. The
  construction is recorded from its published description, to be confirmed at
  30b against the paper's own values.

## Thresholds (session-set; `config/st_r5_index.yaml`)

| Threshold | Value | Reason |
|---|---|---|
| Revisions "flat or falling" | ≤ +0.25% over 28 days, same four quarters | inside the cent rounding of four quarterly estimates |
| 10-year "up" | ≥ +10 bp over 28 days | the rates cluster's own threshold, so one meaning of "up" |
| Gap "closing from above" | gap > 0 and ≥ 1.0 pp below its six-month peak | about a fifth of the entry's 3.5 pp gap, more than one PPI print's noise |
| Log share printed | when \|ln(P1/P0)\| ≥ 0.01 | SR-38's rule |

## Drafts (yours, by hand)

**Book A rule-table line** (item 30's Rights: "Book A modifier via the rule table
(long-horizon expected-return line)"), inactive until ST-R5.30b's ledger passes:

> A-n · Long-horizon expected return (SR-12 as amended by Batch 6 item 30). When
> the aggregate investor allocation to equities (Z.1, the 30b construct) is in
> its top decile of history, Book A's long-horizon expected-return line reads at
> the floor of its range and no new equity risk is added on valuation grounds;
> a cash-share spike (top decile) is recorded as a bottom-side confirm only.
> Status: drafted 16 Oct 2026; inactive until ST-R5.30b's ledger is filed.

**Narrative register line** (item 35; joins item 26's disagreement pair on the
bear side, against Boivin):

> "Collision course" — Budaghyan (BCA, public post, Oct 2026). Core corporate
> prices (PPI final demand less foods, energy and trade services) ~+5% on the
> year against unit labor costs ~+1.5%: the gap that lifts earnings is the
> inflation that lifts yields, so stocks and bonds are on a collision course.
> Bear side of "what's driving 5.3%" (item 26). Measured by ST-R5.35a's gap and
> its closing flag.

## A sample on the gate's fixtures

These are the gate's fixtures, not market data. Both drops are stored, so the
forward legs read. With no drop, the forward rows print "awaiting the estimates
workbook (drop pending)" and the read falls to trailing.

**The Weekly, What's priced: "What's carrying the index"** (chart W11 beside it)

| Anchor | EPS basis | From | S&P 500 | EPS change | P/E | EPS share (log) | P/E share (log) |
|---|---|---|---|---|---|---|---|
| Twelve months | forward | 2025-10-09 | +30.0% | +20.0% | 20.0 to 21.7 | 70% | 30% |
| Year to date | forward | 2025-12-31 | +18.2% | +14.3% | 20.9 to 21.7 | 80% | 20% |
| Twelve months | trailing | 2025-10-09 | +30.0% | +6.7% | 26.7 to 32.5 | 25% | 75% |
| Year to date | trailing | 2025-12-31 | +18.2% | +3.5% | 28.4 to 32.5 | 20% | 80% |

- What's carrying the index, twelve months (2025-10-09 to 2026-10-09): the S&P 500 +30.0%, forward EPS +20.0% and the forward P/E +8.3%, earnings 70% of it in log terms — earnings carry most of the gain.
- r−g -5.10 pp: the 10-year 5.05% (2026-10-09) against g 10.15%, the estimates' growth into the second forward year (2027Q4–2028Q3 over 2026Q4–2027Q3, S&P DJI drop of 2026-10-02).
- Revisions turn: forward EPS revised +0.25% since the 2026-09-04 drop while the 10-year moved +15 bp over 28 days; the price–ULC gap is closing from above (a leading input) (descriptive; unvalidated, n=0).
- Corporate price less unit labor cost, September 2026: +3.5 pp — PPI final demand less foods, energy and trade services +5.0% on the year, unit labor costs +1.5% (Q2 2026, carried forward to the next print); the gap at the 11th percentile of its stored history since 2026-01-01 (n=9; shorter than 5 years).
- The gap is closing from above: 1.0 pp below its 6-month peak of +4.5 pp, a leading input to the revisions-turn flag (descriptive; unvalidated, n=0).
- Margin source (2026-09): selling prices +5.0% against unit labor costs +1.5% on the year — pricing ahead of cost: the margin's source is price.

**The Monthly** prints the same lines, adds the "Since the 12 Oct 2022 low" rows
(forward +116.7% / +50.0% / 15.0 to 21.7 / 52% / 48%; trailing +116.7% / +26.3%
/ 18.9 to 32.5 / 30% / 70%), and carries M11 beside the block (bucket `carry`).

**Positioning & flows: "Investor allocation: equities, bonds and cash"**

| Panel | Share | Quarter | Change on the quarter | Percentile (window, n) |
|---|---|---|---|---|
| Equities (directly and indirectly held, % of financial assets) | 48.0% | Q2 2026 | +0.2 pp | 100th percentile of 5 years (n=20), 100th since 2000-01-01 (n=106) |
| Bonds (debt securities directly held, % of financial assets) | 4.8% | Q2 2026 | +0.0 pp | 5th percentile of 5 years (n=20), 1st since 2000-01-01 (n=106) |
| Cash (currency, deposits and money funds, % of financial assets) | 12.9% | Q2 2026 | +0.0 pp | 5th percentile of 5 years (n=20), 1st since 2000-01-01 (n=106) |

- Equities panel: base rate: after ST-R5.30b.
- Between Z.1 releases, the AAII asset-allocation survey (entered by hand, 2026-09-01): equities 68.0%, bonds 14.0%, cash 18.0%.
- ICI monthly: no free source the box may read -- ici.org answers this repo's agent with 403 at its CDN, robots.txt included (checked 16 Oct 2026), and a writer never passes for a browser.

**The close, What's priced:** the read line above, alone.

## Box commands (yours, inside a window: weekdays 09:05–15:40 or 17:20–23:30 ET, never 16:00–17:20)

Everything below runs only after this branch reaches main, behind the chain and
`st-r5-rates`. The wrappers pull main; no deploy and no unit change are needed.

```bash
# 1. The four new FRED series arrive with the 16:10 pull, each with its whole
#    history (BOGZ1FL153064486Q, TFAABSHNO, WPSFD49116, ULCNFB). To have them
#    before a Monthly, one pull by hand:
~/chester-reports/.venv/bin/python -m altdata.sources.fred

# 2. The S&P DJI workbook: download sp-500-eps-est.xlsx in a browser, drop it in
#    Drive chester-vendor-checks/spdji; the nightly sweep copies it. Before the
#    16:10 pull reads it, check the layout without writing:
~/chester-reports/.venv/bin/python -m altdata.sources.spdji --check ~/chester-data/inbox/spdji/sp-500-eps-est.xlsx

# 3. The AAII allocation survey, monthly, by hand (values are yours):
~/chester-reports/.venv/bin/python tools/manual_input.py manual.aaii_stocks_pct <PCT> <YYYY-MM-01> "AAII asset allocation survey, <month>"
~/chester-reports/.venv/bin/python tools/manual_input.py manual.aaii_bonds_pct <PCT> <YYYY-MM-01> "AAII asset allocation survey, <month>"
~/chester-reports/.venv/bin/python tools/manual_input.py manual.aaii_cash_pct <PCT> <YYYY-MM-01> "AAII asset allocation survey, <month>"

# 4. The block as the box sees it, and the registry check.
~/chester-reports/.venv/bin/python -m altdata.st_r5_index show
~/chester-reports/.venv/bin/python -m tools.check_store_registry --db ~/chester-reports/data/chester.db
```

## Files shared with the open branches

This branch's files over `st-r5-rates`:

| Branch | Shared files | Nature |
|---|---|---|
| `st-r5-rates` (mine) | every file it changed: this branch is built on it | sequential, no conflict; merge it first |
| `st-r6-es-block` (session B) | `CLAUDE.md`, `Makefile`, `config/catalogue_commands.yaml`, `daily_cascade/stack.py`, `daily_cascade/weekly_stack.py` | gate count and list; catalogue lines; mine are short hooks in `stack.build` (What's priced items), `priced_week`, `positioning_week`, `chart_plan`/`PLACE`/`chart_data`/`produce` (W11) |
| `st-r4-tranche-1` (session B) | `CLAUDE.md`, `Makefile`, `altdata/config.py`, `config/catalogue_commands.yaml`, `daily_cascade/stack.py`, `daily_cascade/weekly_stack.py`, `metrics_registry.yaml`, `monthly_macro/stack.py`, `tools/validate_audit_3a.py` | **both add to `FRED_SIGNAL_SERIES`** (its PPIDCS; my four, after `st-r5-rates`' two). After all three merge the counts are 27 + 2 + 4 + 1 = **34** in `FRED_SIGNAL_SERIES`, **136** in `FRED_PULL_SERIES`, and `expected_members` 34. Its `validate_audit_3a` already reads the count by regex; `NEW_BLOCK_MEMBERS` takes its key beside mine. The gate count: 84 + 1 + 1 + its own. |
| `6e-metric-lenses` (session B) | `CLAUDE.md`, `Makefile`, `metrics_registry.yaml` | gate count and list; registry entries in different blocks. When 6e merges, `st_r5_rates.lens` (which this branch reuses) should move onto 6e's `derived.lens_forms`. |
| `el-1-packets`, `el-2-3-rollup` | `CLAUDE.md`, `Makefile` (and `monthly_macro/stack.py` for el-2-3) | count and list; my Monthly hooks are in `priced_section` and `POSITIONING_READS` |

## Not named in the orders

1. **The rates cluster's store ids** in three printed reasons. Fixed on both
   branches (`39414dc` / `8ac992b`).
2. **The Monthly's allocation read** (needs-you item 9). It follows T3.1 item 10
   rather than this order.
3. **`metrics_registry.yaml`'s `fred_signal_triage` block** gains
   `mechanism_group_map "4": macro_inflation` for the PPI and ULC legs, and its
   first `member_units` entry (the equity share).
4. **The chart ends at the latest close.** Its last point carries the latest EPS
   forward to the latest close, so the price line ends where the read line's
   does.
5. **`config/reporting_stack.yaml`'s budget comments** now say what W11 and M11
   displace.
