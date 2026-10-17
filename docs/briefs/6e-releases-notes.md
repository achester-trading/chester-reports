# 6e-releases: Batch 7 items 46 and 48, Group A, with the cross-cutting lenses (session notes, 16 Oct 2026)

**This branch, `6e-releases`, is cut from the tip of `6e-rest` (`6378d36`: `9cefce1`
plus its notes commit; `9cefce1`'s CI was green, so no fix was needed). It is
session B's own line, so it carries 6e part 1 (`6e-metric-lenses`) and `6e-rest`,
and merges after both, in the second stitched chain.** The merge order is:

1. the stitched chain (and the Friday list);
2. `6e-metric-lenses`;
3. `6e-rest`;
4. this branch.

Branch only: pushed, not merged, not deployed, nothing run on the box. Every box
step is printed below for Ari.

Spec: the filed Batch 7 order (`docs/change-order-signal-triage-batch-7-2026-10-16.md`
on `docs-batch-7`): items 46 and 48 in full, section 3, verify items 2 and 4, filing
notes 1, 2, 3, 6 and 9. The 1 Oct metric-lenses brief, which item 48 amends. The 25
Sep order's section 7 and R28. Session A's `st-r5-t1-rest` notes (item 32's form).
The rulings of 16 Oct listed in the paste.

## Step 0: the CI reads

| Branch | Run | Commit | Result |
|---|---|---|---|
| `6e-rest` | 38977476616 | `9cefce1` | **success, 85 of 85 jobs** |
| `st-r4-tranche-1b` | 38977257824 | `96342c1` | **success, 95 of 95 jobs** |

**The verdict: both green.** Each run was read once, with `gh run list --branch
<branch> --limit 3`, and its numbers were added to the branch's own notes: `6e-rest`
in `6378d36` and `st-r4-tranche-1b` in `866c67f`. Both are pushed. Neither run
failed, so nothing needed fixing first.

## What it builds

All of it reads the observation store **as of the cutoff**
(`altdata/releases.py`), so every figure and flag is the one the knowable
vintages support. Nothing new is written by the lenses; they are recomputed at
render time from stored series. Thresholds and lists are in `config/releases.yaml`.

**Flags exist only where the order names them:**
- lens 2: diffusion under 50 for three months;
- lens 3: persistent negative revisions;
- lens 4: permanent job losers rising year over year;
- item 46b: the pass-through flag.

Every other lens is report-only. A flag is True, False or None, and None carries
`withheld` with its reason. That is **the vintage rule** (lens 22): a flag that
needs a print not yet published at the cutoff is withheld. It is never evaluated
on whatever happens to be stored. No flag is a market-state input (R28).

### ST-R6.46a: the CPI decomposition panel (item 46)

- **Contributions:** for each of energy, food, core goods, shelter and core
  services ex shelter, its basket weight times its own month-on-month change, in
  percentage points of the headline.
  - The weights are BLS relative importance for December 2025, rounded to sum to
    one. They are the same weights as the CPI lead composite's.
  - The residual against the headline prints, because relative importance drifts
    each month.
- **Core services ex shelter (supercore):** BLS publishes no index for it. It is
  built from core services (CUSR0000SASLE) less shelter at their weights:
  (0.61 × core services m/m − 0.355 × shelter m/m) / 0.255.
- **The middle of the distribution:** the Cleveland Fed median and 16% trimmed
  mean, MEDCPIM158SFRBCLE and TRMMEANCPIM158SFRBCLE (two new FRED series). Each
  prints the month and its three-month average.
- **Diffusion:** the unweighted share of 24 CPI categories rising faster than 4%
  annualised on the month.
  - The categories are non-overlapping expenditure classes from FRED's CPI
    component series. 20 are new; rent, owners' equivalent rent, used cars and
    airline fares were already stored or are in the basket.
  - If fewer than 18 of the 24 printed for the month, no share is printed and
    the reason is.
- **Where it prints:** the full panel is in the inflation block. That block now
  prints in the Monthly's Plumbing, after the six buckets, as well as the Weekly's.
  The close's CPI-day line (lens 24, below) reads the same decomposition.
- **Fixtures** (`tools/validate_releases.py` group A):
  - each contribution and supercore by hand;
  - the residual;
  - the median and trimmed mean with their three-month averages;
  - 10 of 24 categories hot (41.7%);
  - 17 printed is under the minimum, so no share;
  - a piece without the month's print carries its reason and no sum is claimed.

### ST-R6.46b: the pass-through basket and flag (item 46)

- **The basket:** airline fares (CUSR0000SETG01), transportation services
  (CUSR0000SAS4) and the truck-transportation PPI (PCU484484), all new FRED series.
  Equally weighted, because the order gives no weights.
  - Its three-month annualised change is computed over the months all three legs
    printed.
- **The flag fires** when an energy spike falls within the last three months and,
  one to three months after it, the basket's three-month annualised change exceeds
  its value at the spike month by the threshold.
  - An energy spike is CPI energy up at least 4.0% in a month.
  - The acceleration threshold is 10 points.
- **Withheld** when a month in the window lacks a leg. In practice that is the
  truck PPI, which can publish after CPI. The flag then waits for that vintage.
- **Item 32's printed state (ruling (d)):** `releases.item32_state()` turns item
  32's supply-shock signature into a printed state.
  - While item 32 reads a supply shock, the state is "supply shock, contained"
    until this flag fires, and "supply shock, propagating" after.
  - With no supply shock, item 32's own line stands.
  - Item 32 is report-only, on session A's `st-r5-t1-rest`
    (`altdata/st_r5_t1_rest.py` `oil_shock`). That module is not on this branch, so
    the inflation block prints "item 32's classifier (st-r5-t1-rest) is not on this
    branch".
  - `releases.item32_read()` imports the module when it is present. **At the
    stitch** the switch is live with no edit here. Session A's
    `t1_rest_block.py` oil line can also print `releases.item32_state(...)`
    beside its signature; that is one line on their file, for the stitch.
- **Fixtures** (group B):
  - with the spike threshold set to 3.0 for the fixture, a spike at +3.0% and
    not at +2.99%;
  - the flag fires with the threshold set at the fixture's acceleration and not
    0.0001 above it;
  - the September PPI withheld means the flag is withheld;
  - item 32's state, all five cases.

### ST-R6.48a: the employment lenses 1-6 (item 48)

| Lens | What prints | Source | Flag |
|---|---|---|---|
| 1 Cyclical core payrolls | private less private education and health, the month and three-month average, beside the headline | USPRIV, USEHS (new); PAYEMS (stored) | report only |
| 2 Diffusion, 1 and 3 months | **the share of STATES adding jobs** (see gaps) | SMS00000000000000021 / 22 (new, FRED State and Metro) | under 50 for three consecutive months, on the 1-month index |
| 3 Revisions as a signal | the two-month net revision at each release, from the stored vintages | PAYEMS's vintages (ALFRED backfill and later pulls) | negative at each of the last three releases |
| 3 Birth-death contribution | a listed gap | — | — |
| 4 Unemployment by flow | permanent job losers, three-month average against a year earlier; prime-age participation and its 12-month change; the Sahm rule; continuing against initial claims over 13 weeks (the hiring-freeze read) | LNS13026638, LNS11300060, ICSA, CCSA (new); `calc.sahm_rule` (stored) | permanent losers up ≥ 20% on the year |
| 5 Leading pieces | temp help (3-month change, year over year), aggregate weekly hours (3-month annualised, year over year), the JOLTS quits rate and its 12-month change, openings per unemployed | TEMPHELPS, AWHI, UNEMPLOY (new); JTSQUR, JTSJOL (stored) | report only |
| 6 Wages | the ECI (private wages, year over year), the Atlanta Fed tracker beside average hourly earnings, the job-switcher premium (switchers less stayers) | ECIWAG, ECIALLCIV, the tracker's switcher and stayer series (new); the tracker and AHE (stored) | report only |

**The net revision, by hand:** this release's change over the two months before
its newest month, less the same change as the previous vintage printed it. For
example, (1180 − 1000) − (1200 − 1000) = −20.

**Fixtures** (groups C and C2):
- cyclical core −30k against a +40k headline;
- diffusion: under 50 three months fires; 50.0 exactly does not; two months does
  not; a missing month is withheld;
- permanent losers fire at +20.0% and not at +19.99%;
- the hiring-freeze read;
- every leading and wage figure by hand;
- the three net revisions by hand (−20, −10, −10), so the flag fires; a positive
  third (+10) clears it.

### ST-R6.48b: the CPI lenses 7-11 (item 48)

- **7, the shelter lead:** Zillow's ZORI and Apartment List's national rent, each
  year over year now and twelve months earlier, beside CPI shelter, rent and OER.
  - This also **closes the CPI lead composite's shelter gap** (ruling (a)3).
    `config/macro_6e.yaml`'s shelter component now reads `zillow.zori_us`, year
    over year, lag 12, scale 1, unvalidated like the rest.
  - One lead per component (the correlation guard). Zillow rather than Apartment
    List because its history is longer, so the kill test reaches 60 months sooner.
  - The composite now covers **80%** of the basket at 3 and 6 months (44.5%
    before). At 9 months it is shelter alone, 35.5%. Food and energy remain
    uncovered, each with its reason.
  - `validate_6e_rest` group B is re-pinned to these figures by hand. It also
    checks that without Zillow stored, the 9-month horizon names the unstored
    lead, not a lag.
- **8, supercore:** three and six months annualised, and year over year.
- **9, sticky against flexible:** both Atlanta Fed series were already stored
  (`sticky_cpi`, `flex_cpi`). Goods (CUSR0000SAC, new) against services (stored),
  year over year and three-month annualised.
- **10, the base-effect ladder:** year over year for each of the next three months,
  if month on month runs at its trailing three-month average, given the months
  dropping out. For CPI and core.
- **11, the CPI-PCE wedge:** `calc.core_cpi_pce_gap` (6e-rest), with the three
  weight differences named:
  - shelter about 35% of CPI against 15% of PCE;
  - medical care about 7% against 17%;
  - financial services under 1% against about 8%.
- **Fixtures** (group D):
  - Zillow +3.0% now and a year earlier; Apartment List absent with its reason;
    the new-tenant gap named;
  - supercore at both horizons by hand;
  - sticky, flexible, goods and services;
  - **the ladder against a hand computation**, with Oct-Dec 2025's 0.4, 0.1 and
    0.2 dropping out at a 0.3% pace;
  - the wedge with its weights.

### ST-R6.48c: the cross-cutting lenses 21-24

- **21:** six months annualised (or the six-month change in pp, for a rate-like
  release) now prints beside three months, for every release series. It is in
  `derived.lens_forms` and the lens column "6m ann. / 6m chg", so the Monthly v2
  tables and the Weekly's and close's lens tables carry it alike. Fixture: group F.
- **22, first print against revised:**
  - FRED series carry AUD-3d's first-publication stamps from ALFRED.
  - The two new readers stamp each file's Last-Modified (observed), or the write
    instant where none is sent.
  - No series is pulled from the BLS directly (see gaps), so none needs its own
    stamps.
  - Fixtures (group E):
    - the diffusion flag reads August's first print (49.5, FLAG on 20 Sep) and its
      revision once knowable (50.5, no flag on 5 Oct);
    - the revision flag is withheld before the third release's vintage and read
      after it;
    - the basket's months stop where the PPI's do.
- **23, surprise:** "no consensus" prints, as 6e-rest does, in the lens cell and in
  every release-day line. Fixtures: groups F and G.
- **24, "what moved the print":** one line per release on its day, in item 46's
  voice.
  - The releases are CPI, the employment report, JOLTS and the ECI.
  - A release's day is the ET date its headline's newest print first became
    available.
  - The line is **code-written** from the release's own lens figures, for
    example: "CPI for Sep 2026: +0.6% on the month (…); what moved it: energy
    +0.32 pp; …; median CPI 2.8% annualised; … (surprise: no consensus)."
  - It rides the close's Plumbing as a first-priority item. That is the path the
    close's existing narrative step already reads, under its existing audits.
    **No new model path.**
  - It is code-written, not model-written, because the close's Plumbing is
    usually light (no paragraph). A model-written line would need the new path
    the paste rules out.
  - Fixture (group G): the line on CPI day and nothing the next day; the
    employment report's line on its day; the item in the close's Plumbing at
    priority 1.

### The display (item 6 of the paste)

- **The inflation block** (`daily_cascade/inflation_block.py`, Plumbing & rates).
  Its panels, in order:
  - the CPI lead composite;
  - the CPI-PCE gap;
  - **the decomposition** (item 46);
  - **the CPI lenses** (7-11);
  - a reserved `ppi` slot for Group B.

  It prints in the Weekly, as before, and now in the Monthly's Plumbing after the
  six buckets. Tables and code-written lines only.
- **The labour block** (`daily_cascade/labour_block.py`) is a **new Monthly-only
  section, "Labour", after Plumbing & rates** (filing note 6).
  - It is declared in `config/reporting_stack.yaml` at `monthly: medium` and at
    no other cadence.
  - The Monthly builds it after assembly and places it by config order, the way
    it handles the Reading chapter. So the close and the Weekly lay out the ten
    sections as before.
  - It has two tables: payrolls; and flows, leading pieces and wages. The flags'
    rows carry FLAG, "no flag" or "withheld", with reasons as lines.
- **Budgets:**
  - The labour block asks for no paragraph. Its claim line is code-written from
    the flags, at most 40 words (pinned in group G), and is its whole budget cost.
  - `trim_to_budget` takes those words from the lowest-priority paragraph inside
    the 10,000. **What it displaces:** at most 40 words of the lowest-priority
    paragraph, and nothing else.
  - No chart: the Monthly's 12 are unchanged.
  - The Monthly has no table cap in config, and tables count no words
    (`stack.section_words`).
  - The inflation panels add no prose word and no chart (`validate_6e_rest` group
    E, now over all four panels).
- **What it gains:**
  - the Monthly gains the five panels and the labour section;
  - the Weekly gains the decomposition and CPI-lens panels;
  - the close gains one line on a release day.
- **The report template edit map:** the 25 Sep order, section 7, has three new
  rows (inflation block, Labour section, the close's release-day line) at
  `docs/change-order-signal-triage-2026-09-25.md` lines 822-824.
- **Gates that pin the section list, updated:**
  - `validate_monthly_stack` group A: labour after Plumbing, at medium (left to
    CI; it touches PDF rendering);
  - `validate_quarterly_stack`: Reading and Labour are the Monthly's only (94 of
    94 locally).

## The readers added, and the sources that stayed gaps

The rule that decided each: **Ari's standing rule of 16 Oct (b)**. Prefer public,
easy sources. Pursue no registration, phone check or portal that will not load;
the answer is a keyless alternative or a listed gap. Beside it stand **ruling
(a)5** (build a keyless path where one reads within robots) and **the repo's
robots rule** (a writer obeys robots.txt with its wildcards).

| Source | Outcome | Why |
|---|---|---|
| FRED, 45 new series (`FRED_RELEASES_SERIES`) | **on the existing pull** (199 series) | filing note 2: almost everything is on FRED. Every id, first and latest observation and unit was read off FRED on 16 Oct |
| Zillow ZORI | **new reader**, `altdata/sources/rent_indices.py` | files.zillowstatic.com's robots.txt carries no rule; national row from Jan 2015 |
| Apartment List | **same reader** | the research page allows it (robots: Allow /); the month's file is linked there and served from assets.ctfassets.net (robots 404, no rules); national "overall" from Jan 2017 |
| Cleveland Fed rate path | **new reader**, `altdata/sources/clevfed_rules.py` (ruling (a)5) | the keyless file is the **simple monetary policy rules'** prescribed path (median, quartiles, range by quarter); robots disallows /errors/* only. Stored as the rules' path, never as market pricing: `clevfed.rules_start`, `rules_median_4q`, `rules_median_8q`, `rules_iqr_4q` (the width) |
| ECB balance sheet | **on the FRED pull** (ECBASSETSW), ruling (a)5 | 6e-rest's gap was the unit, not the access. A new registry unit `EUR_M` (raw changes) carries the euro stock; family quantity |
| BLS API (api.bls.gov), keyless v1 | **not used** | it answers keylessly, but its robots.txt is `User-agent: * / Disallow: /`, and so is data.bls.gov's. The repo's rule is to obey robots.txt, so it is not a reader |
| CES industry diffusion indexes (CES0500000021/22) | **listed gap**; the keyless stand-in is FRED's State and Metro diffusion (the share of states adding jobs), printed under that name | on the BLS API only. **Lens 2's flag reads the stand-in: needs-you 1** |
| Birth-death contribution | **listed gap** | published on www.bls.gov, which answers 403 to this project's agent: BLS requires a contact address in the User-Agent, and this project never sends one |
| BLS new-tenant rent index | **listed gap** | the same: www.bls.gov/pir/new-tenant-rent.htm and www.bls.gov/robots.txt both answer 403 (checked 16 Oct). FRED does not carry it |
| Other section 1 gaps from 6e-rest | **stay listed** | Term SOFR, swap spreads, the ZQ strip, the 12-month maturity share and the rest: no keyless path found within robots (ruling (a)5) |

Both readers are new and **not held** (the D1c ruling of 16 Oct).
- `rent_indices` is on `feeds.EXTERNAL_WRITERS`; `clevfed_rules` is on
  `OFFICIAL_WRITERS`.
- Their `KEYS` are literal, so the roster reads them from source.
- Each checks robots on every pull, and a refusal writes nothing.
- Fixtures (group H): both files parsed (the national row only; a blank cell
  skipped, never zero); the Cleveland rules file; robots allowing and refusing;
  a refused pull is STALE and writes nothing.

## Session-set values, with their reasons

All in `config/releases.yaml`, each with its reason beside it. Values the order
itself gives are not listed here: 4% annualised, under 50 for three months, within
three months, the 12-month shelter lead, and the three-month ladder.

| Value | Set | Reason |
|---|---|---|
| Energy spike | CPI energy ≥ +4.0% m/m | 9.1% of months since 2000 (29 of 319; the 90th percentile is +3.85%), read off FRED's CPIENGSL on 16 Oct; Sep 2026's +5.2% clears it |
| Basket acceleration | ≥ 10 points of 3-month annualised, at the spike against 1-3 months after | the order's one-to-three-month lag. The basket is noisy (airfares): the three-month change in its 3-month annualised rate has a standard deviation of 10.4 points outside 2020-22 (Apr 2004 - Sep 2026), and 10 points is reached in about one month in six |
| Basket weights | equal | the order gives none, and no leg is the anchor |
| Diffusion minimum | 18 of 24 categories | three quarters, or the share is not printed |
| Lens 2 flag series | the 1-month index | three consecutive months is the persistence; the 3-month span already averages |
| Revisions "persistent" | negative at each of the last 3 releases | a quarter of releases |
| Permanent losers' rise | 3-month average ≥ +20% on the year | measured on LNS13026638: monthly noise 4.7% (s.d. outside recessions), so the 3-month average carries it; +10% is reached in 18% of non-recession months, +20% in 8%; +20% fired in Dec 2007 (+24.2%) and not in Sep 2007 (+13.9%) |
| Hiring-freeze read | continuing ≥ +5% over 13 weeks with initial within ±5% (4-week averages) | a quarter of weekly prints; 5% is about one s.d. of the 13-week change outside recessions since 2000 (5.6% continuing, 6.1% initial); continuing reaches it in 8% of those weeks. Report-only |
| Ladder pace | the trailing 3-month average m/m | the most recent run-rate |
| Decomposition weights | BLS relative importance, Dec 2025 | the composite's; the residual prints the drift |
| Shelter in the composite | Zillow, yoy, lag 12, scale 1 | the architecture's ~4 quarters; one lead a component |
| Draft pair rule (below) | "half the categories"; the median read on its 3-month average | so one month's median does not decide it |

## Verify items

- **2. The BLS API's coverage of the new-tenant rent index's history.** It could
  not be answered within the rules, and the index is a listed gap.
  - The API host's robots.txt disallows every agent.
  - The index's own page on www.bls.gov answers 403 to this project's agent: BLS
    asks for a contact address in the User-Agent, and this project never sends
    one.
  - FRED does not carry it.
  - What is known is from the architecture's table (Part 17): it leads CPI shelter
    by about four quarters and is free.
  - The two published rent indices close the composite's shelter gap in its place.
    Zillow's runs from Jan 2015 and Apartment List's from Jan 2017, both read on 16
    Oct.
- **4. Whether the Cleveland Fed median and trimmed mean were already pulled.**
  They were not; filing note 1 is confirmed. Both are now on the FRED pull
  (MEDCPIM158SFRBCLE, TRMMEANCPIM158SFRBCLE, percent change at annual rate, from
  1983). The Atlanta Fed sticky CPI was already pulled, and so was the flexible
  CPI (`flex_cpi`, FLEXCPIM157SFRBATL), which the order expected to add.

## Drafts committed, for Ari's accept-all

Judgment drafts under ruling (c), committed as drafted. Neither touches the
narrative register or the decision register; the register's confirm step stays
Ari's.

| Draft | File and line |
|---|---|
| The disagreement pair, Monchau ("an energy shock, contained") against Budaghyan ("broad acceleration"), adjudicated monthly by median CPI and diffusion | `docs/narrative-register-pairs.md:13` |
| The Warsh-matrix line: an energy shock with a softening labour market | `docs/warsh-matrix-lines.md:18` |
| The amendment note on the metric-lenses brief (item 48) | `docs/briefs/metric-lenses-brief-2026-10-01.md:46` |
| The three template-map rows | `docs/change-order-signal-triage-2026-09-25.md:822-824` |

- **`docs/narrative-register-pairs.md`** is session A's file on `st-r5-fixes`; it
  is not on this line. This branch creates it with session A's header verbatim
  and one entry. At the stitch the two add/add copies join as one header plus
  every entry.
- **`docs/warsh-matrix-lines.md`** was to be created by session A on
  `st-r5-audit`, which did not exist when this was written. So it is created here
  in a matching shape (header, status, one entry), as the paste says, and the
  file says so.

## Box commands, for Ari (inside a window; nothing here was run on the box)

These run after this branch merges, which is after the chain, `6e-metric-lenses`
and `6e-rest`. No unit file changed. The 45 FRED series and both readers run at
the next scheduled pull (the readers ride `altdata.feeds pull`). The history is
backfilled once:

1. The 45 FRED series at their first publication. Dry run first:
   `ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.fred_history backfill --series cpi_energy,cpi_food,cpi_core_services,cpi_commodities,cpi_median,cpi_trimmed_mean,cpi_airline_fares,cpi_transport_services,ppi_truck_freight,payrolls_private,payrolls_edu_health,unemployed_level,claims_initial,claims_continuing,permanent_job_losers,lfpr_prime_age,temp_help,agg_weekly_hours,eci_total,eci_wages,atl_wage_switchers,atl_wage_stayers,diffusion_states_1m,diffusion_states_3m,ecb_assets,cpi_c_food_home,cpi_c_food_away,cpi_c_alcohol,cpi_c_gasoline,cpi_c_electricity,cpi_c_utility_gas,cpi_c_apparel,cpi_c_new_vehicles,cpi_c_vehicle_parts,cpi_c_medical_goods,cpi_c_tobacco,cpi_c_household,cpi_c_personal_care,cpi_c_lodging,cpi_c_water_trash,cpi_c_professional_med,cpi_c_hospital,cpi_c_vehicle_repair,cpi_c_tuition,cpi_c_video_audio --dry-run | tail -40'`
   then the same without `--dry-run`. Lens 3 (revisions) reads PAYEMS's
   vintages, so check `nfp` was in AUD-3d's backfill. If it was not, add `nfp` to
   this list.
2. **Optional:** the two readers' first pulls now rather than at the next
   scheduled pull (each writes):
   `ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.sources.rent_indices | tail -20'`
   and
   `ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.sources.clevfed_rules | tail -20'`
3. The CPI lead composite over the stored history, now that shelter has its lead.
   Dry run first:
   `ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.market_features compute --from 2015-01-01 --dry-run | tail -20'`
   then the same without `--dry-run`, after step 2 or the scheduled pull.
4. What the lenses read today (reads only):
   `ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.releases show | head -200'`

## Gates, locally, one at a time

| Gate | Result |
|---|---|
| `tools/validate_releases.py` (new) | **61 passed, 0 failed**. Groups A-H as above |
| `tools/validate_6e_rest.py` (extended) | **34 passed, 0 failed**. B: the composite with shelter's lead, by hand (80%, 35.5% at nine months), and the unstored-lead reason. D: five panels, the two filled and Group B's empty |
| `tools/validate_lenses.py` | **49 passed, 0 failed** (the release column gains "6m ann." after "3m ann.", so its pin holds) |
| `tools/validate_audit_3a.py` | **83 passed, 0 failed**. NEW_KEY_BLOCKS gains `fred_releases`; the readers' keys are registered one by one; CLAUDE.md's counts |
| `tools/validate_quarterly_stack.py` (edited) | **94 passed, 0 failed** |
| `tools/check_registry.py` | OK |
| `tools/check_library.py` | 0 failures, 0 warnings |

**Left to CI:**
- `validate_monthly_stack`, whose group A I edited (it touches PDF rendering);
- `validate_official_sources`, over every writer on the rosters;
- the Weekly and close render gates;
- `validate_figure_budget`, `validate_edition_consistency` and every other gate.

No gate read the live store, fetched or called a model.

The CI run on the push is read once and recorded below.

**CLAUDE.md:**
- seventy-eight code gates (seventy-five Python);
- `FRED_RELEASES_SERIES` 45, `FRED_PULL_SERIES` 199;
- a paragraph on the release lenses.

The Makefile gains the gate; the catalogue gains `altdata.releases` (its read-only
`show`) and the two readers. The family assignments are regenerated:
- 2,717 keys (2,666 before);
- 287 ambiguous, three of them new: the two state diffusion indexes (release, or
  conditions) and the ECB balance sheet (quantity, or release).

## Files shared with the open branches

Each open branch was compared with its merge base on main. The files below are
touched by this branch and by session A's `st-r5-fixes`, `st-r5-t1-rest`,
`st-r5-index` and `st-r5-rates`, and by session B's `st-r4-tranche-1b`. Most of that
overlap is the stitched chain they all carry. This branch's own edits to them:

| File | This branch's edit | Expected conflict |
|---|---|---|
| `altdata/feeds.py` | one name at the end of `OFFICIAL_WRITERS` and of `EXTERNAL_WRITERS` | the tuples' last lines (st-r4-tranche-1b adds `census_vip` and `cboe_indices` there): keep every name |
| `altdata/config.py` | `FRED_RELEASES_SERIES` after `FRED_6E_SERIES`; the union line gains it | the union line, if another branch adds a list: keep every list |
| `metrics_registry.yaml` | the `fred_releases` block before `fred_aq3`; six metric entries before `bulk_imports:` | insertion points only |
| `source_registry.yaml`, `config/catalogue_commands.yaml` | two sources; three commands | insertion points only |
| `config/reporting_stack.yaml` | the labour row after Plumbing | none expected |
| `monthly_macro/stack.py` | the inflation block after Plumbing's buckets; `labour_section`; `by_id` | the Plumbing tail, if another branch appends a sub-section there: keep both |
| `daily_cascade/stack.py` | the release-day items in the close's Plumbing | the same tail |
| `altdata/derived.py` | `EUR_M` in `DELTA_UNITS`; lens 21's six-month forms | none expected |
| `tools/validate_monthly_stack.py`, `tools/validate_quarterly_stack.py` | the labour section in the pinned order; Reading and Labour excluded from the front matter | if another branch adds a Monthly section, both insertions stand |
| `tools/validate_audit_3a.py`, `CLAUDE.md`, `Makefile` | the counts, the block, the gate line | the counts are recounted at the stitch, as every branch's are |
| `docs/narrative-register-pairs.md` | add/add with `st-r5-fixes` | one header, every entry |
| `docs/warsh-matrix-lines.md` | add/add with `st-r5-audit` once it exists | the same |

**Item 32's switch at the stitch:**
- `altdata/releases.py` imports `altdata.st_r5_t1_rest` when present. No conflict;
  the switch goes live when the two meet.
- One optional line on session A's `daily_cascade/t1_rest_block.py` would print
  the state beside item 32's signature. The inflation block already prints it.

`chester-meme`, `.env`, the units, the registers and the ledgers: untouched.

## Where Group B attaches

Group B (PPI lenses 12-14, GDP lenses 15-20) is the next paste on this line.
- **PPI (12-14):** the inflation block's reserved `ppi` slot. Its FRED legs go in a
  new list beside `FRED_RELEASES_SERIES`: the intermediate-demand stages 1-4,
  portfolio-management fees, airfares, healthcare services and trade services.
  Its thresholds go in a `ppi:` section of `config/releases.yaml`.
- **GDP (15-20):** the Monthly's Slow layers (the order's placement), as a builder
  beside the labour block's form.
  - Final sales to private domestic purchasers, the investment split, GDI-GDP,
    NIPA profits, real disposable income ex transfers and the saving rate are on
    FRED.
  - GDPNow and the NY Fed nowcast are new readers, each to be checked against
    robots first.
- **Lens 24:** a `ppi` and a `gdp` row in `config/releases.yaml` `releases`, and a
  line builder each in `releases.release_day_lines`.
- **Lens 21:** already applies to every release series by family.

## Needs you

1. **Lens 2's source.** The order's CES industry diffusion indexes are on the BLS
   API only, and its robots.txt disallows every agent. The flag reads FRED's
   State and Metro index (the share of states adding jobs) in their place, printed
   under that name. Accept the stand-in, or rule that the BLS API is read despite
   its robots.txt (an exception to the repo's rule, which is yours to make).
2. **The session-set values** above, above all the pass-through thresholds
   (+4.0%, 10 points) and the permanent-losers +20%.
   - I first set the pass-through at +3.0% and 2 points, and permanent losers at
     +10%, with reasons I had not checked.
   - Read against FRED's history before commit:
     - +3.0% is the top 17% of months;
     - 2 points is inside the basket's normal noise;
     - +10% fires in 18% of non-recession months.
   - Both now carry the measured figures.
   - On the live September print the basket's 3-month annualised rate is 19.2%.
3. **The Cleveland Fed "rate path" is the policy-rules path**, not a market-implied
   one; it is stored and printed as such. Confirm that is what ruling (a)5 meant.
4. **The release-day line is code-written**, not model-written, to keep to "no new
   model path". Say if you wanted the existing narrative step itself to write it.
5. **The drafts** listed above, for your accept-all.
6. **The labour block's place** (its own Monthly section after Plumbing) and
   **its budget cost** (its claim, ≤ 40 words).
7. **Birth-death and the new-tenant rent index** stay gaps unless a source without
   the contact-address requirement exists.

## CI

The run on this branch's push is read once and recorded here.

| Run | Commit | Result |
|---|---|---|
| 38993064152 (Gates, push) | 0fcad0e | green: 86 of 86 jobs succeeded, 7m37s, read 17 Oct 2026 |

`validate_monthly_stack`, left to CI because it renders, passed there.
