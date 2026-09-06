# Chester Reports — Architecture Review and Work Plan v3

*Pressure test of the v2 plan against four stated goals: durable time-series
assets, a self-learning feedback loop, hallucination resistance, ongoing checks,
and the nimbleness to add analysis over time.*

**Verdict: the v2 plan is sound on hallucination and checks, weak on durability,
and structurally unable to deliver the feedback loop as written.** Seven findings
below, then a revised architecture and a 16-session plan.

---

# Part 1 — Pressure test

## Finding 1 — No point-in-time data. Severity: critical.

**This one breaks the feedback loop outright.**

FRED data gets revised. Nonfarm payrolls get revised by six figures. GDP gets
revised twice. My v2 plan stores one value per series per date and overwrites on
refresh. That means when you grade September's call twelve months from now, you
grade it against numbers *nobody had in September*.

Your report said labor was cooling not breaking on a 4.10% U-3 and a 0.10 Sahm
reading. If those get revised to 4.40% and 0.35, the archived report looks wrong —
but the call was correct given what was knowable. You cannot distinguish a bad
judgment from a data revision, which means the feedback loop teaches you nothing.

**Fix:** vintage-aware storage. `observations` keyed on
`(series_id, as_of, vintage_date)` rather than `(series_id, as_of)`. FRED exposes
this through ALFRED — the same API with a `realtime_start` parameter. Store the
vintage you actually fetched, never overwrite, and add a `first_release` flag.
Every backtest then runs on first-release data, and revisions become their own
analyzable signal.

## Finding 2 — I told you to skip the backfill. Severity: high.

I wrote "skip historical backfill; log a TODO." That was wrong. A time-series
store with no history is a store that becomes useful in 2028.

Every series in your registry has decades of FRED history available in one call.
Backfilling costs one session and immediately enables percentile ranks, z-scores,
and regime classification — none of which your current report can compute. Right
now Pillar 6 says HY OAS at 2.69% is "at cycle tights" with nothing behind that
claim. With history it becomes "3rd percentile since 1997," which is a fact.

**Fix:** full backfill in the store session. It also gives your feedback loop 25
years of pseudo-history to calibrate thresholds against, instead of waiting.

## Finding 3 — Model and prompt drift are unlogged confounds. Severity: high.

Your narrative comes from a Claude API call. When you change models, or Anthropic
ships a new version, your output changes for reasons unrelated to markets. Twelve
months of graded calls spanning three model versions and eleven prompt edits
tells you nothing about your framework.

**Fix:** pin the model string explicitly per report version. Record
`model_id`, `prompt_version` (hash of the assembled prompt template), and
`git_sha` on every row of `runs`. Any analysis of report quality partitions on
these. Upgrade models deliberately, at version boundaries, and re-run the prior
month on both to see what changed.

## Finding 4 — The feedback loop as designed is a scoreboard, not a loop.
Severity: high.

Predicate grading tells you your hit rate. It does not change anything. A loop
requires a defined mechanism by which evidence alters behavior, and my v2 plan
never specified one.

Worse, the obvious mechanism is a trap. With monthly cadence you get 12
observations a year. Reweighting pillars on 12 observations is curve-fitting
noise, and it will feel like learning.

**Fix — and this is the honest part:** for the first two years, the feedback loop
should calibrate the *process*, not the *signal*. Three tiers:

- **Tier 1 (from month one) — narrative accountability.** Was every number
  correct? Was every causal claim backed by an event? Did flagged uncertainty
  turn out to matter? This is auditable immediately at n=1 and it is where the
  real errors are — the fabricated bear steepener would have been caught here.
- **Tier 2 (from month six) — predicate calibration.** Are your thresholds
  informative? A predicate that fires 95% of the time isn't a watch item. Prune
  and re-set thresholds on distributional grounds, not on outcome.
- **Tier 3 (year three onward) — signal weighting.** Only once n is large enough
  to mean something. Backfilled history helps here, but pseudo-history isn't the
  same as live calls; treat it as a prior, not evidence.

Each tier's changes get logged to a `calibration_log` table with date, rationale,
and what it replaced — so you can tell whether a change helped.

## Finding 5 — No alerting, and you have already gone dark once. Severity: high.

The largest durability risk in this system is not technical. Your last real work
was around June 11; the restart was in mid-August. Disruptive Themes went stale.
`monthly_macro` sat at `never_run` and nothing told you.

I deferred the dashboard to the backlog, which was reasonable — but I deferred
*alerting* with it, which was not. Those are different things. A dashboard
requires you to look; an alert finds you.

**Fix:** minimal alerting in v17, not the backlog. A failed run, a series past
`max_staleness_days`, or a validator hard-fail sends you an email or push. Ten
lines of code, and it is the difference between a two-month gap and a two-day one.

## Finding 6 — Adding analysis still requires writing code. Severity: medium.

You asked for nimbleness. My v2 plan gives you a series registry and a pillar
ordering config, but derived metrics and pillar composition are still Python. To
add "gold residual" or a new pillar you edit code, which means you only do it in
a session, which means you don't do it.

**Fix:** two more registries. A **metrics registry** — name, expression, inputs,
units, description — so derived metrics are declarative. And **pillar definitions
as config** — series list, metrics list, prompt template path, scoring rule. New
pillar becomes a YAML block plus a prompt file. New metric becomes three lines
you can add from your phone.

## Finding 7 — Store location is unresolved and the write path is fragile.
Severity: medium.

I said "SQLite committed to the repo." But GitHub Actions is what writes the data,
so Actions has to commit the database back to the repo on every run. That works
until two runs overlap, or a commit fails silently, and it makes every diff a
binary blob.

**Fix — pick one, deliberately:**

- **(a) Actions commits back.** Simplest. Fine at your scale. Add a lock and fail
  loudly on conflict. Recommended if you want to move fast.
- **(b) Cloudflare D1.** You already run the Worker and have touched the D1
  binding screen. Proper database, no commit dance, queryable from anywhere,
  same auth you already built. Slightly more setup, better long-term.
- **(c) Parquet in the repo, partitioned by series.** Diffable-ish, no server,
  good for analysis in pandas. Weakest for concurrent writes.

**Resolved: (b) D1 as system of record, plus (c) as a snapshot.**

D1 beats commit-back on every axis that matters — concurrent-write safety, no
multi-megabyte binary in every commit, queryable from the Worker you already run,
built-in backups. Its one weakness is analytical queries, and vintages make that
real: backfill plus daily market data plus every vintage puts `observations` in
the millions of rows.

So: D1 is the system of record, and each monthly run exports a **parquet snapshot
to the repo**. That gives you fast pandas analysis, offline development, and
disaster recovery if the Worker or the account ever goes away. Keep a local
SQLite mirror for development — identical schema, driver swap only.

---

# Part 2 — Revised architecture: the declarative spine

The organizing principle: **engines are code, everything else is config.** New
analysis should almost never require touching an engine.

```
┌─ REGISTRIES (config — you edit these) ─────────────────────┐
│  series_registry.yaml   what to fetch, units, bounds       │
│  metrics_registry.yaml  derived metrics as expressions     │
│  pillars.yaml           composition, order, prompt path    │
│  calendar.yaml          forward events                     │
│  prompts/*.md           one template per pillar            │
└────────────────────────────────────────────────────────────┘
                              ↓
┌─ ENGINES (code — rarely changes) ──────────────────────────┐
│  fetch     sources/base.py → fred, yfinance, sec, cboe...  │
│  compute   evaluates metrics_registry expressions          │
│  validate  bounds, staleness, invariants, provenance       │
│  narrate   assembles manifest → API → verifies output      │
│  render    HTML                                            │
│  grade     resolves predicates, writes calibration_log     │
└────────────────────────────────────────────────────────────┘
                              ↓
┌─ STORE (vintage-aware) ────────────────────────────────────┐
│  observations(series_id, as_of, vintage_date, value, ...)  │
│  runs(run_id, report, model_id, prompt_version, git_sha)   │
│  events / views / pillar_scores / predicates               │
│  calibration_log(date, tier, change, rationale, replaced)  │
└────────────────────────────────────────────────────────────┘
                              ↓
        five reports, each a query + a template
```

## The provenance chain — how hallucination is actually prevented

Four gates, each cheap, in order:

1. **Manifest-only generation.** The narrate engine builds an explicit fact
   manifest — every value the model is allowed to cite, with `series_id`,
   `as_of`, `value`, and vintage. The prompt states that no other number may
   appear.
2. **Numeric audit.** After generation, extract every numeral in the output and
   match it against the manifest. Unmatched number → regenerate that section.
   *This was in your original v5 roadmap as a "Claude audit step" and got lost —
   it is the highest-leverage anti-hallucination mechanism you had.*
3. **Directional check.** Every claim of movement verified against the computed
   delta. Catches the bear-steepener class of error.
4. **Attribution check.** No causal claim without a matching event record. Catches
   invented explanations.

Gates 2–4 are deterministic code, not model judgment. That matters: you should
not use an LLM as the only check on an LLM.

## Contracts between reports

Once five reports share a store, an upstream schema change silently breaks
downstream consumers. Each published extract (Alt Asset → `real-assets`,
Disruptive Themes Factor I → `internals`, Monthly Matrix → Top & Bottom verdict)
gets a versioned contract: a small schema file plus a test that fails the
producer's run if the shape changes. Cheap now, painful to retrofit.

---

# Part 3 — Work plan v3

Sixteen sessions. Changes from v2 are marked **[NEW]** or **[CHANGED]**.

## Session −1 — The GEX logger. Do this first, before anything else.
**~1 hour. [NEW]**

**The only asset in this system that compounds with time, and the only one you
cannot recover.** FlashAlpha historical replay is Alpha-tier. Every day the
snapshot does not run is a hole in a distribution you can never buy back at
Basic. Everything else on this list can be caught up; this cannot.

So it ships before the store, before Claude Code, before the units registry.

It needs none of the architecture:

- A standalone script hitting the summary endpoint (GEX + DEX + VEX + CHEX in one
  call) for SPX, SPY, QQQ, IWM
- Appends the **raw JSON response** to a dated file in the repo — not parsed
  fields; you will want columns you did not think to extract
- GitHub Actions cron, once daily after the close
- No database, no validation, no narrative. Append-only

When the store exists (Session 5), backfill it from the accumulated files and
point the logger at the store instead.

**Done when:** a file appears in the repo tomorrow without you doing anything.

## Session 0 — Get set up
**~1.5 hours.** Install Claude Code, clone the repo, write `CLAUDE.md`, run one
read-only task. *(Unchanged from v2 — see that plan for the CLAUDE.md draft, plus
add the registry conventions below.)*

## Session 1 — Clear the board, and decide the store
**~2.5 hours.**
1. Hunt `compute_scorecard.py` — all branches plus deleted history
   (`git log --all --diff-filter=D --name-only`).
2. Add `CHESTER_STATE_URL` and `CHESTER_STATE_TOKEN` repo secrets.
3. Upload the three staged unit-fix files as-is.
4. Tag `v16-final`; freeze HTML and raw data to `/reference/`; write the
   regeneration test.
5. **[NEW] Stand up the store backend** — D1 as system of record, parquet
   snapshot to the repo each run, local SQLite mirror for development. Decision
   is made (Finding 7); this session just creates the D1 binding and confirms the
   Worker can read and write it.
6. **[NEW] Pin the model string** and start recording `model_id`,
   `prompt_version`, `git_sha` on every run.

**Also in this session:** verify the ALERT trigger-count threshold against what
`compute_scorecard.py` actually computes, and update both documents that cite it
— a pending item carried from the reporting-cadence work.

**Done when:** `/system-state` shows a real timestamp and the regeneration test
passes.

## Session 2 — Series registry, metrics registry, validator
**~3 hours. [CHANGED — metrics registry added]**
1. `config/series_registry.yaml` — units, format, bounds, staleness limits.
   Nothing renders without an entry.
2. **[NEW]** `config/metrics_registry.yaml` — every derived metric as a
   declarative expression with inputs, units, description. Move all 12 existing
   derived metrics into it. Adding a metric becomes a config edit.

   **[NEW] Three fields beyond the obvious, per the methodology work:**
   - `effective_n` — *not* observation count. Johnston's 228 washouts sit in four
     clustered windows; RRE calibrates on four episodes. Record the real number.
   - `trigger_eligible` — false whenever `effective_n < 10`. Such a metric is a
     continuous conditioner, never a binary trigger. A threshold from four points
     is false precision, especially inside a composite already reading extended.
   - `kill_condition` + `added_date` — a written falsification condition at the
     time the metric is added. Without it, failed signals quietly vanish and the
     framework accumulates only confirmations.

   **First two entries, as proof the declarative design pays:**
   - **CCC−BB differential** — `BAMLH0A3HYC − BAMLH0A1HYBB`, percentile-ranked.
     Isolates tail-tier stress from market-wide level and neutralizes most
     duration and rate-beta contamination. Kill condition: CCC re-tightens 150bp
     while BB is flat. Standing caveat to document: the CCC index is not a fixed
     basket, so some fraction of any move is rating-migration accounting and
     cannot be separated from the index line.
   - **Fed SOMA Treasury holdings** — `TREAST`, weekly. Replaces any use of a
     fused "government holdings" figure. Intragovernmental holdings (~$7T, OASI,
     Medicare HI, federal retirement) are non-marketable special issues that
     never competed for private demand and are inert for liquidity purposes.
     Only SOMA is the monetary variable.

   **[NEW] Two more entries — commodity pass-through:**
   - **Commodity YoY vs. CPI YoY spread**, percentile-ranked. Note the
     construction trap in the widely-circulated version of this chart: it plots a
     cumulative index level against a year-over-year rate. A base-100 index rises
     forever under any positive inflation, so the gap widens mechanically and
     most of the apparent divergence is a units artifact. **Rate against rate.**
     Done correctly, commodities lead CPI by roughly 3–6 months with much higher
     amplitude — a real lead indicator.
   - **Pass-through residual** — regress core CPI on lagged commodity YoY, track
     the residual. When commodities surge and the residual stays flat,
     pass-through is broken and the surge is not an inflation signal. This is the
     version that carries information in the current data, where WTI fell 11%
     while sticky core kept grinding lower.

   Kill condition for both: commodity YoY leads CPI YoY by less than 2 months, or
   rolling five-year lead correlation drops below 0.3.

   **Correlation guard applies here specifically.** Your existing flexible CPI
   series is closely related. If |ρ| > 0.7 against it, these are narrative colour
   only, outside the composite.

   **Framing to reject in the narrative:** commodity prices are not "real
   inflation" against an understated official number. They are an input-cost
   basket; CPI weights shelter near a third and services near 60% because that is
   where households spend. Measure the pass-through relationship; do not import
   the conclusion.

   **[NEW] Seasonality — structural yes, calendar as conditioner only.**

   Two different things travel under one word, and only one is worth building on.

   **Structural calendar effects — a known participant is required to transact on
   a known date.** Most are already in the plan: options expiry cycles (the
   Weekend Synthesis clock), Treasury refunding and auctions, quarter- and
   year-end funding pressure, index rebalances, tax-loss selling and January
   reallocation. **The one genuine gap is buyback blackout windows** — roughly a
   quarter of the year with the largest price-insensitive equity bid stepped
   away, on dates you can compute from earnings calendars. Add it to
   `calendar.yaml`.

   **Calendar seasonality — "prices tend to do X in month Y."** Sell in May, the
   Santa rally, the September effect. Computed on overlapping annual observations,
   effective n under ten, public for decades, and most fail the threshold
   fragility test — shift the window a week and the effect disappears.

   Build it only in this form: a **percentile conditioner** showing the current
   month's historical return rank, the observation count, and the confidence
   interval. `trigger_eligible: false`. Rendered as context, never entering a
   composite, and never phrased as a forecast.

   **Crypto is the partial exception.** The four-year issuance schedule is a real
   mechanical cause, unlike the September effect. But halving-cycle analysis is
   still effective n of three or four, so it stays a conditioner too — with the
   difference noted in the narrative, since a real mechanism with thin data is a
   better bet than a thin mechanism with thin data.

   **[NEW] Premise expiry — distinct from data staleness.** Staleness rules cover how
old the *data* is. This covers whether the *premise* still holds. **Any score
resting on a discrete, reversible event — a ceasefire, an agreement, a policy
suspension — carries an explicit expiry date set at the time of scoring.** Past
expiry it reverts to the prior score or goes unscored; it never carries forward at
full weight on a collapsed premise.

Add `premise_expiry` and `premise_event` to the pillar and factor config. Slow
factors (valuation, demographics) do not need it; event-driven ones do.

*This is not hypothetical: a geopolitical factor scored on a ceasefire that
collapsed seven weeks later carried full weight through the following refresh
cycle. A stale input at full weight is worse than no input.*

**[NEW] Chokepoint and food-transmission cluster.** New domain, no current
coverage. Four inputs, scored separately:

- **Hormuz transit count** — IMF PortWatch, weekly, free. Score as a **ratio to
  the ~85/day pre-crisis baseline**, never as a level. *Caveat to document:* a
  material share of traffic runs with AIS off, and the understatement grows with
  risk — treat the series as a floor.
- **War-risk insurance premium, % of hull value** — market-priced, no narrative,
  prices the tail directly rather than inferring it from volumes. Reported near
  10% of hull value against ~0.05% pre-war. Not on FRED; Lloyd's List and broker
  circulars, likely a manual quarterly input.
- **Nitrogen complex — Tampa ammonia, NOLA urea, DAP.** *The one that fills a real
  analytical gap.* **Build as a lead indicator with an explicit lag, never as a
  coincident input.** Transmission runs fertilizer price → planting window →
  harvest → food CPI over two to three quarters, which means the CPI-based pillars
  structurally cannot see it coming. Scored coincidentally it adds nothing food
  CPI will not say later. Track the inputs, not anyone else's forecast of the
  output.
- **ONI / ENSO** — NOAA CPC, monthly, cheap. Carry it; do not lead with it.
  ENSO-to-yield-to-price is a long, noisy chain. *Correct the circulating figure
  before it enters anything:* the widely-quoted "69% El Niño probability" is the
  conditional probability of the largest event since 1950, not of an event
  occurring.

**[NEW] Registry convention: net, not gross.** Standardize on debt held by the
   public throughout. Gross flatters short-maturity issuers and distorts
   central-bank-heavy ones. Document the choice in the registry header.
3. `validate.py` — bounds (hard fail), staleness (tag + visible age), delta
   sanity, relationship invariants.
4. Resolve core PCE 3.29% vs. core CPI 2.47%.

**Done when:** the validator run against frozen v16 data **fails**.

## Session 3 — SPLIT INTO 3a / 3b / 3c
*This session accumulated too much to run in one sitting. Three thematic blocks.*

### Session 3a — Market data plumbing
**~2 hours.** Path-aware sampling with `path_divergence`; `sources/base.py` as
the single vendor interface.

### Session 3b — Rates and policy
**~2.75 hours.** NY Fed ACM term premium; Fed policy path; funding stress and
swap spreads; four-bank policy-differential frame.

### Session 3c — Fiscal and demand
**~1.5 hours.** Fiscal position and rollover; Korea 20-day exports; TSMC monthly
revenue.

**Rule for all three blocks: every new fetcher lands its `series_registry.yaml`
entry in the same session.** Session 2 makes the validator reject unregistered
series, and 3b/3c add roughly 25 of them. Deferred, you will spend 3c debugging
validation failures from 3b.

---

*Detail for all three blocks follows.*

**[NEW] Fed policy path (~45 min).** The report discusses Fed policy in every
pillar with no series measuring what the market prices. Start with the free and
durable layer: EFFR, IORB, target range (DFEDTARU/DFEDTARL) and SOFR from FRED,
plus **2Y minus EFFR** as a compact easing-priced proxy that works even when
everything else fails. Add the Cleveland Fed expected rate path. Attempt the ZQ
fed funds futures strip via yfinance; if the ticker does not resolve, defer the
full strip to IBKR Gate 1 rather than scraping CME. Lands as a policy sub-block
in `momentum`, alongside the curve and term premium.

**[NEW] Path dispersion, not just path level (~30 min).** If forward guidance is
being deliberately withdrawn, **the level of the expected path becomes less
informative and the disagreement around it becomes more informative.** Everything
else in this block measures the level. Add the width:

- Confidence width of the implied path, per meeting and at 12 months
- Dispersion across SEP dots
- Range of published dealer forecasts

**The read:** when guidance is withdrawn, path dispersion should structurally
widen. **If it does not, the market is still pricing an implicit reaction function
that no longer exists** — and that gap is both tradeable and exactly the kind of
thing this report should catch. Store dispersion in `policy_path` alongside the
level so both are vintage-tracked.

**[NEW] NFCI as reaction function, not just state description.** A Fed that judges
policy by financial conditions rather than by the funds rate makes NFCI an *input*
to policy, which makes easing conditions self-limiting: loose conditions justify
tighter policy, which tightens conditions. Read the current −0.56 that way in
`liquidity` — as a constraint on how dovish policy can be, not merely as a
description of how loose things are.

**[NEW] Term premium in this regime.** A central bank that refuses to pre-commit
raises term premium mechanically, since uncertainty about the path is what term
premium compensates for. **Rising ACM term premium + widening path dispersion +
unchanged inflation expectations is the signature of a guidance-withdrawal
regime** — and it must be distinguished from a fiscal-supply story, because they
imply different trades. The distinguishing test is breakevens: supply-driven term
premium tends to move with them, guidance-driven does not.

**Source discipline.** The guidance-withdrawal reading above originates in
commentary on a speech, and the leap from "conditions are not restrictive" to
"hikes are coming" is an interpretation, not a statement. **Log it as an
event-chain thesis with a data signature** — path dispersion widening, term
premium rising, NFCI-to-policy sensitivity increasing — and let the series confirm
or kill it rather than adopting it.

**[NEW] Competing theses on the same speech — the worked example.** Two
commentators read the same Jackson Hole remarks to opposite conclusions, and both
are consistent with the text:

| | Thesis A — guidance withdrawal | Thesis B — constrained hawkishness |
|---|---|---|
| Claim | Conditions not restrictive ⇒ hikes are live | Hawkish rhetoric is credibility maintenance under political pressure; words are uninformative about action |
| Binding constraint | Economics | Optics — cannot be *seen* dovish |
| **Path dispersion** | Widens | Widens |
| **Mean path** | **Shifts up** | **Barely moves** |
| Realized policy | Tightening bias | No change |

**They are separable in the data, and the separator is the mean path, not the
dispersion.** This is what the `policy_path` vintage surface is for, and it should
resolve within a few months.

**File both as chain theses, neither as the read.** Extract the *structural
claim* — "hawkish rhetoric under political constraint is uninformative about
action" — not the personality attribution. A mind-reading argument is
unfalsifiable by construction: assign someone a private intent differing from
their stated one and any subsequent action confirms it.

**And discount the weak evidence in both.** Word-frequency counts from a speech
about financial innovation are noise, and "no move this close to an election" is
asserted rather than argued — the Fed has moved in election years repeatedly.

**The general lesson for the views layer:** two credible readers, one speech,
opposite conclusions. **That is the case for tracking dispersion of views rather
than any single view** — and for `conviction` being a required field, so a
low-conviction satirical read does not sit at the same weight as a researched
one.

**[NEW] Funding stress and swap spreads (~45 min).** OIS forwards are largely
redundant with the fed funds path above — same information, different instrument.
**Swap spreads are not redundant and matter more.** Swap spread vs. Treasury is a
dealer balance-sheet and collateral gauge; negative spreads signal balance-sheet
constraint rather than credit risk. This speaks directly to the reserve-scarcity
watch your liquidity pillar flagged with RRP exhausted — today you would learn
about a funding event from a headline.

Constraint to work around: FRED's ICE swap rate series were discontinued, so
there is no free clean swap curve. Build the free layer now and label the gap:

- CME Term SOFR (1M / 3M / 6M / 12M), published daily
- SOFR–IORB and SOFR–EFFR spreads from FRED
- Repo fails and SRF usage (NY Fed) — these were Tier C in the fetcher backlog
  and belong here instead, since they answer the same question

A true swap curve needs a paid feed or IBKR. Flag it rather than scraping
something fragile.

**[NEW] Fiscal position and rollover (~45 min).** Three additions, all free:

- **Deficit ratio.** Pillar 8 currently carries outlays and debt/GDP but no
  deficit — and outlays alone cannot produce one. Add TTM receipts, outlays and
  deficit against nominal GDP, from the Monthly Treasury Statement.
- **Share of marketable debt maturing within 12 months** (MSPD). This is the raw
  half of consolidated rate-reset velocity, and it is cheap. **Ship it here; the
  consolidated version — net SOMA, add reserves at IORB — stays deferred.** It
  currently sits near a third, close to the highest share since 2010 outside the
  early pandemic months, which puts it at the center of the Treasury financing
  chain rather than in the backlog.
- **TGA range, not just level.** The informative property is variance: a $600B
  swing is a liquidity impulse independent of Fed policy. Track rolling range and
  realized volatility alongside the balance.

**[NEW] Policy-differential frame for `global` (~40 min).** Today `global` carries
EUR/USD and little else on the euro side — the report notes euro strength with no
euro-side rate series behind it. Rather than an ECB block, extend `global` to a
**four-bank differential frame**. For the Fed, ECB, BoJ and BoE, carry: policy
rate, real policy rate, 2y sovereign yield (the policy-expectations proxy), and
balance-sheet direction. **Render the differentials** — those drive capital flows,
not the levels. Same structure four times, which makes the BoE nearly free.

ECB-specific series to add, all free from ECB SDW or FRED:

- Deposit facility rate; ECB balance sheet; €STR
- HICP core
- **BTP–Bund and OAT–Bund spreads** — *the* ECB signal that transmits globally,
  because sovereign fragmentation is a systemic event. Not the policy rate.
- German 2y yield
- Euribor–OIS, for the euro-area bank channel — feeds the thin `banking` pillar
- PEPP and APP runoff pace: duration supply landing in an already heavy market

**Ranking, stated honestly so the report weights it correctly:** the ECB sits
third behind the Fed and BoJ for this system, and the reason is mechanical. The
Fed sets the global discount rate; the BoJ is the marginal supplier of the
world's funding currency and the largest foreign holder of Treasuries — which is
why the yen chain mattered. The ECB mostly transmits *into* the euro area rather
than out of it, and the euro is a reserve currency but not a funding currency at
yen scale.

**Not building:** an ECB scenario matrix. The Fed has one because Fed policy is a
first-order input to everything downstream. An ECB equivalent would be analysis
you would rarely act on.

**[NEW] Sectoral debt composition (~20 min).** Pillar 8 currently sees only the
government line. Add total non-financial debt to GDP **split by sector** —
household, non-financial corporate, government — from the Fed's Z.1. Free, same
source family as the rest of the fiscal work.

**Two things it gives you:**

- **Composition, not just level.** Government debt rising roughly 30 points of GDP
  since 2010 while household debt fell close to 30 is a fundamentally different
  regime from all sectors levering together. The aggregate ratio can be flat while
  the risk migrates entirely.
- **A better frame for R-vs-G.** Private-sector deleveraging capacity is what has
  been absorbing public issuance. **When household debt stops falling, that offset
  ends** — a checkable condition rather than a forecast, and a natural predicate.

**Two constructions to avoid**, both common in the popular version of this
argument. *Debt as a share of total financial assets* uses a market-priced
denominator that collapses exactly when you would need it — and on its own numbers
the ratio has risen, which argues against the thesis it is used to support. *Government
asset valuations* — gross resource estimates in particular — ignore extraction
cost, prices, timing and legal constraints, and are not collateral in any usable
sense.

**The underlying error to note in the narrative:** debt is serviced from cash
flows, not from the existence of assets. Household net worth does not service
Treasury debt without taxation, and the capacity to tax is a political variable
rather than an accounting one. That is exactly what the interest-burden ratio
below measures, which is why the two belong together.

**[NEW] Interest burden and coverage stress test (~30 min).** Pillar 8 carries
debt/GDP, outlays and R-vs-G but nothing on debt service. Both inputs come from
the Monthly Treasury Statement already being pulled above, so marginal cost is
near zero.

- **Net interest as a share of federal revenue.** Revenue is the correct
  denominator — it is what actually services the debt. Interest-to-GDP is the
  more common construction and it is weaker, because it flatters the US against
  countries with higher tax take. Revenue-based is the coverage ratio a credit
  analyst would apply to any other issuer.
- **Percentile against backfilled history**, once Session 6 lands.

**Why it belongs.** The current reading is roughly 18.5% of revenue with the
30-year near 5.2%, against a prior high of about 18.4% in 1991 when the 30-year
was near 8%. **Same burden at roughly half the rate** — the debt stock is doing
the work, and it is the cleanest single demonstration that the level of yields no
longer tells you much on its own.

**Coverage stress test — the derived metric worth building.** Take the share of
marketable debt maturing within 12 months (added above) and reprice it at current
market rates. **What does net interest as a share of revenue become?** That number
is the forward burden the current ratio is still converging toward, and it is the
fiscal cost side of the Treasury financing chain: buying back long bonds and
funding with bills lowers today's coupon while raising the reset speed.

**Vintage discipline.** Net interest and yields publish on different schedules;
the widely-circulated version of this chart pairs a December net-interest figure
with an August yield. **Render both as-of dates** — this is exactly what the
staleness tagging is for, and the series moves fast enough that the gap matters.

**[NEW] Analytical upgrade to Pillar 8's R-vs-G.** The current calculation uses an
effective real rate near 1.4%, which implicitly assumes slow repricing. With a
third of marketable debt repricing annually, the effective rate converges toward
the market rate far faster than a six-year WAM implies, so the ~70bp cushion is
more fragile than the arithmetic shows. **Report R on both bases — average
effective and marginal — and render the gap.** The gap is the actual signal.

**Done when:** August flags JPY/USD.

## Session 4 — The provenance chain
**[SEQUENCING: run AFTER Session 5.** The manifest is built from stored data. Built
before the store exists, this code gets rewritten in Session 5. Store first,
provenance on top.]
**~3 hours. [CHANGED — audit and canary added]**
1. Shared context block; reference, don't restate.
2. **[NEW] Manifest-only generation** — model may cite only what's in the manifest.
3. **[NEW] Numeric audit** — every numeral in output matched against manifest;
   regenerate on miss. *Restores the audit step from your v5 roadmap.*
4. Directional check against computed deltas.
5. Completion enforcement — token budget, punctuation check, retry, visible
   `[TRUNCATED]`.
6. **[NEW] Golden-file canary** — run the pipeline against frozen inputs and diff
   the output. Catches prompt drift and model drift on every change.

   **Diff extracted facts and directional claims, not text.** LLM output is not
   byte-identical across runs even at temperature zero, so a text diff would fail
   this gate permanently. Compare the structured extraction: which numbers were
   cited, which direction each claim asserted, which sections rendered.

**Whitelist before you build the numeric audit.** Every year, date, percentage,
section number and ordinal in the narrative is a numeral. Without excluding those
classes up front the audit regenerates endlessly and looks like a bad idea when
the problem is the tokenizer.

**Done when:** three clean runs, and the canary's fact-level diff is empty across
an unrelated code change.

## Session 5 — Vintage-aware store
**~3 hours. [CHANGED — vintages added]**
Tables per Part 2. `observations` keyed on `(series_id, as_of, vintage_date)`
with a `first_release` flag. Never overwrite. `store.py` as the only module
touching the DB. Fold in the Alt Asset crypto writeback.

**Local mirror sync.** D1 is the system of record; the offline test cannot pass
without a populated local SQLite copy. Build the sync step explicitly — it is
small, and it is exactly the kind of omission that eats a session.

**Done when:** the report renders with networking off, and a revised series shows
both vintages.

### **[NEW] Also in this session: the `election_odds` table**

```sql
election_odds (run_id, vintage_date, market_id, race, outcome,
               probability, volume, source)
```

Same vintage pattern as `policy_path` and `observations` — store the full
distribution per run so you can chart how a race repriced over months. **The
change is the signal; the level is context.**

### **[NEW] Also in this session: archive rendered narratives**

```sql
narratives (run_id, report, section, rendered_text, published_at)
```

The retrospective in Session 15 audits what the report *said*, and that requires
keeping it. Store every rendered section verbatim. Cheap, and impossible to
reconstruct later.

### **[NEW] Also in this session: point-in-time index constituents**

The vintage design versions *data revisions*. It does not version *index
membership*, and that is a separate survivorship problem.

Session 13's ex-Mag7 EPS work would silently use today's membership — excluding
Lehman, Bear, Enron, WorldCom, Countrywide, GM, Kodak, Sears. The bias is worst
precisely where signals fire hardest, so any constituent-level result computed
without this is unverified.

```sql
index_members (index_name, as_of, ticker, weight, action)
```

Snapshot membership monthly from here forward; source history where you can.

### **[NEW] Also in this session: the `policy_path` table**

Store the **full implied path per run**, not a headline number:

```sql
policy_path (run_id, vintage_date, meeting_date,
             implied_rate, cut_probability, source)
```

Same vintage pattern as `observations`. This gives you a surface — meeting date ×
vintage — so you can chart how a given meeting has repriced over months. The
*shift* is the signal; the level is only context. Feed the largest repricing into
the surprise ranking (Session 6), and use the path to score which scenario in
your Fed scenario matrix the market is actually pricing.

### **[NEW] Also in this session: start the FlashAlpha snapshot logger**

**~40 minutes. Do not defer this to Session 14.**

FlashAlpha historical replay lives on `historical.flashalpha.com` and is
**Alpha-tier only** ($1,199–1,499/mo). You are on Basic. That means the dealer
positioning history you need cannot be bought — it has to be accumulated.

So start accumulating it the day the store exists. A daily snapshot script
writing GEX / DEX / VEX / CHEX into `observations` is roughly 40 lines. In twelve
months you own the distribution that answers the question your email cannot:
**is −$3.27B NetGEX extreme or ordinary?** Every day of delay is a day of
distribution you cannot buy back at this tier.

Build the `sentiment` pillar later. Start the clock now.

**Universe.** Define it as a config constant, not inline — you will extend it.

| Tier | Symbols | Feeds |
|---|---|---|
| **Daily core** | SPX, SPY, QQQ, IWM | `sentiment`, `internals` |
| | **HYG, LQD** | **`credit` — see below** |
| | TLT | `momentum`, policy path |
| | GLD, SLV, IBIT, USO | `real-assets`, two-bid decomposition |
| | NVDA, SMH | `internals`, AI financing |
| **Daily rotating (3/day)** | rest of Mag 7, XLF, KRE, FXI, EEM, FXY | `banking`, `global` |
| **Weekly sweep** | sector ETFs, remainder | as tagged |

~15–18 calls/day against a 100 cap.

**HYG and LQD are the highest-value addition on this list.** The credit pillar
runs entirely on OAS levels, which are spot measures with no forward component.
HYG put skew has historically moved ahead of spreads, and with CCC currently the
one pillar dissenting from the sanguine consensus, a leading indicator against it
is worth more than anything else here.

Everything in this universe shares one property: **options history is as unbuyable
at Basic tier as the index's.** That is why the universe is set now rather than
when each pillar gets built.

**[NEW] Normalize to dollar gamma per 1% — store it as the primary series.**
Raw notional GEX is not comparable across a 20% move in the underlying, and that
matters more here than for anyone with a purchased backtest: **you are building
the history yourself, so an unnormalized series quietly corrupts every percentile
rank you later compute from it.** The email digest already reports dealer shock in
shares and dollars per 1% move — store that, and treat raw notional as derived.

Apply per bucket as well, so 0DTE and monthly gamma are comparable on the same
axis.

**[NEW] Pin logging — the highest-value addition in this session.**

Every day, record whether the close landed within a defined tolerance of peak GEX
and of max pain. **Tolerance is declared in advance and never revised after the
fact.** Log every day, hit or miss.

```sql
pin_log (date, symbol, close, peak_gex_strike, max_pain_strike,
         tolerance_bps, pinned_gex, pinned_maxpain, expiry_type)
```

**Why this matters more than another metric:** gamma commentary is universally
asserted at effective n = 0 — everyone claims pinning, nobody publishes a base
rate. **After a year you have a measured pin rate**, segmented by expiry type,
gamma regime, and 0DTE share. That converts the pillar's central claim from
theory into calibration, and it is the one place in this system where you could
plausibly know something the commentariat does not.

Pair with the effective-n discipline: until the sample is meaningful, the pin
read stays a conditioner. Once it is, the base rate itself becomes the threshold.

**[NEW] Intraday sampling — build it, label it correctly.**

Snapshot at 09:30, 11:00, 14:00 and 15:30 for SPX and SPY.

**The honest caveat, written into the output:** Basic tier serves *settled*
morning open interest, frozen for the session. Four intraday calls therefore
return the same positioning profile against a moving spot. **What you are
measuring is spot traversing a static profile** — distance to flip, wall
proximity, magnet strength — not positioning evolution. That is genuinely useful
and it is not what it would be called if mislabelled.

True intraday positioning evolution requires the Growth-tier flow endpoint
(effective OI, which drifts as positions fill, exit and roll). Note the
limitation in the pillar; do not imply otherwise.

**[NEW] Day-one verification list — now executed as the gated out-of-band
probe (schedule item 1, per Part 26) — run once there, do not repeat here:**

1. Does the per-strike payload carry expiry? *(determines whether buckets cost
   calls)*
2. Which tier returns the Indic module endpoints?
3. **Is customer-vs-dealer flow polarity exposed at Basic?** *(it changes the
   interpretation of every gamma reading entirely — flow-signed vs. assumed-sign;
   expected to be Growth, but confirm rather than assume)*
4. Actual rate limit — 100/day or 250/day
5. Which liquidation and Indic endpoints your key actually returns

**Liquidity floor — a hard rule.** Below a threshold, a symbol is excluded from
skew and OI percentile calculations entirely. Confident-looking percentiles on
thin books are worse than no metric.

**Use FlashAlpha's own Options Liquidity (bid/ask tightness) metric rather than
building an OI threshold.** It is already computed, and spread tightness is a
better gate than volume alone.

**Four glossary metrics worth capturing beyond the headline exposures:**

- **Options Liquidity** — the liquidity floor above
- **IV Dispersion (surface roughness)** — **use as a data-quality gate, not an
  analytic.** A rough surface means stale or illiquid quotes, so that snapshot's
  GEX deserves less confidence. Wire into the validator: high roughness downgrades
  confidence on everything derived from that day. Nothing else in the system
  catches a bad options day.
- **OI Concentration (Herfindahl)** — positioning concentrated in few strikes
  means the regime changes discontinuously rather than decaying. The strike-level
  twin of expiry-bucket concentration.
- **OI-Weighted DTE** — one number for whether positioning is short or long
  dated. Good single line for the Weekend Synthesis.

**Skip or defer:** Gamma Squeeze (threshold flag, conditioner at best), Dealer
Alignment (opaque composite), per-symbol Vol of Vol (VVIX covers the index case).

**Tier note:** exposure analytics, first-order Greeks, max pain and most
volatility analytics derive from per-strike OI, IV and Greeks, so they should be
Basic. Live Flow (Live GEX Shift, Top Unusual Flow, Smart-Money Tilt) is Growth;
the 0DTE suite and VRP are likely gated too. **Verify against the dashboard on day
one** rather than trusting this mapping.

**Discipline for adding symbols later:** each needs a stated question it answers
and a named pillar it feeds. Otherwise the universe grows to fifty tickers and
the pillar becomes a data dump.

**FXY caveat:** a weak proxy, since the real FX options market is OTC. Log it,
label it.

**Store the raw per-strike response, not just headline numbers.** Beyond wanting
fields you did not think to extract, this is what lets you compute **expiry
buckets locally for free** — if the payload carries expiry per strike, you never
pay a call per bucket. Verify on day one; it determines the budget.

**If the API requires a call per expiry**, fifteen symbols × five buckets is 75
calls and you are at the cap. In that case: full decomposition daily on **SPX,
SPY, QQQ only**, aggregate for the rest.

## Session 6 — Backfill
**~2 hours. [NEW — was a deferred TODO]**
Full FRED history for every registry series via ALFRED, first-release flagged.
Then add percentile rank and z-score as registry metrics, so "at cycle tights"
becomes "3rd percentile since 1997."

**[NEW] Also in this session: Shiller ingest and the surprise ranking.**

- **Shiller CAPE data** (free, Yale) — unblocks Re-Rating Exhaustion, which
  decomposes cumulative price return into earnings growth vs. multiple expansion.
  It measures *how the advance was financed* rather than where the multiple sits,
  which is the more answerable question.
- **Surprise ranking** — with history in hand, rank every series by how unusual
  its level and its month-over-month move are. **Lead the report with the five
  most anomalous and let quiet pillars say so in two lines.** Your v16 output
  gave all ten pillars equal length whether or not anything happened in them.
  This single change does more for insight than the next ten fetchers.

**Done when:** every series has history, and the report cites percentiles.

## Session 7 — Alerting and dormancy resilience
**~2 hours. [CHANGED — scoped for multi-week absences]**

The design assumption is not "Ari checks daily." It is **"Ari may be gone for six
weeks and the system must still be alive when he returns."** Four pieces.

### 1. Basic alerting
Failed run, stale series, or validator hard-fail sends email or push.

### 1b. Content assertions — the failure alerting misses

**Silent success is the real risk.** A lapsed API key or a changed endpoint
returns HTTP 200 with an empty payload. The run succeeds, the heartbeat pings,
and you log nothing for weeks.

Assert on content, not exit code: observation count increased, series count
within expected range, no series returning null for N consecutive runs.

### 2. Inverted heartbeat
A failed pipeline cannot alert you about its own failure — that is the flaw in
alerting alone. Each successful run pings an external uptime monitor
(healthchecks.io, Cronitor, any of them). **When the pings stop, the monitor
notifies you.** Absence of signal becomes the alert, which is the only kind that
survives a dead pipeline.

### 3. Degrade, do not fail
A run missing 20% of its series should still publish, clearly labeled with what
is absent, rather than erroring out. Reserve hard-fail for genuinely
unpublishable states.

Rationale: a hard-fail validator plus nobody watching equals months of nothing.
Partial output with visible gaps is strictly better than silence.

### 4. Welcome-back digest
On the first run after a gap exceeding two cycles, generate one artifact: what
ran, what failed and when, which predicates resolved while you were away, what is
now stale, and what changed most in the data. Cheap to build, and the difference
between resuming and re-deriving.

**Done when:** you can kill the pipeline deliberately and receive an alert
without touching anything.

### Known rot risks to design against

| Risk | Behavior | Mitigation |
|---|---|---|
| cron-job.org disables jobs after repeated failures | Trigger dies permanently, silently | Heartbeat catches it |
| yfinance breaks | Returns nulls, not errors | Validator range checks + degrade-don't-fail |
| Pinned model deprecated | API call fails outright | Heartbeat; check model status on return |
| Secrets or tokens expire | Auth failure mid-run | Heartbeat |

**What does not rot:** FRED keys, the repo, D1 rows, the store. And note that
your trigger is cron-job.org firing `workflow_dispatch` rather than a GitHub
scheduled workflow — which sidesteps GitHub's rule disabling cron schedules after
60 days of repo inactivity. Accidental good design; keep it.

## Session 8 — Events ingest
**~3 hours, possibly two passes.** GDELT plus primary RSS from Treasury, Fed,
BoJ, USTR, OPEC, EIA. Domain, salience, persistence, affected series, expected
direction. Classification via a Claude API step.

### **[NEW] Election and policy-throughput tracking**

US midterms are roughly ten weeks out, which is why this belongs in v17 rather
than the backlog.

**Track priced probabilities, not polls.** Kalshi and Polymarket both expose
APIs, and a priced probability is mechanically comparable to everything else in
the system — the fed funds path, breakevens, credit spreads. Polls are a
different kind of object with a worse record. This keeps the report in its
existing frame: what the market prices, not what anyone thinks.

**Track policy channels, not parties.** The market-relevant variable is almost
never which side wins — it is throughput. Divided vs. unified government, and
then the dated consequences: expiring tax provisions, tariff authority,
appropriations deadlines, debt-ceiling timing, Fed appointments. The appointments
channel connects directly to the Fed scenario matrix.

**The sharpest read: let the options market price it.** An election date inside an
expiry cycle shows up as a kink in the vol term structure. With VIX term
structure and the Session −1 logger you can measure *how much the market thinks
the election matters* rather than forming a view. Tradeable, and politically
neutral.

**Neutrality discipline — tighter here than anywhere else in the system.** A
market report that opines on political outcomes becomes punditry, and the bias
leaks into the pillars. **Rule: probabilities are data, implications are
conditional.** *If divided government, then the tariff channel does X.* Never
advocacy, never a forecast of who wins. Write this into the pillar prompt
explicitly.

**Log the conditionals as predicates** so conditional claims get graded like
everything else. **Apply the liquidity floor** — thin prediction-market contracts
are manipulable and noisy, so below a volume threshold they are excluded rather
than reported with false confidence. Conditioner, not trigger.

**Dates and dated legislative deadlines go in the forward calendar** (Session 9).
Structural-regime consequences go to Disruptive Themes. Not the weekly —
probabilities move too slowly for that cadence.

### **[NEW] Event chains — where the insight actually lives**

Atomic event records are not enough. Policy arrives as *campaigns*: linked
actions where each step creates the conditions for the next, and the sequence
means more than any element.

```sql
event_chains (chain_id, name, thesis, status, opened, closed)
-- events gain: chain_id, sequence
expected_next (chain_id, description, trigger_condition,
               confirming_series, expected_direction, resolved)
```

**Worked example — the current Treasury financing campaign:** yen intervention
(reducing pressure on Japan to sell Treasuries) → long-bond buybacks doubled →
TGA drawdown to fund them → bill issuance to replenish → stablecoin issuers as
the hoped-for absorber → possible Fed bill purchases to defend the funds-rate
peg. Six linked steps, one thesis.

**Three readings only the chain produces:**

1. **Consolidated maturity is shortening.** Retiring 10–30y paper while funding
   with bills is duration reduction financed by floating-rate liabilities — the
   live test case for consolidated rate-reset velocity.
2. **It is a stealth easing.** Buybacks plus TGA drawdown plus Fed bill purchases
   add liquidity without a rate cut, so the fed funds path *understates* the
   impulse. **Render policy-rate expectations and effective liquidity impulse as
   separate lines** — they can point in opposite directions.
3. **Stablecoin supply becomes a fiscal variable.** If issuers are the marginal
   bill buyer, their growth is Treasury financing capacity, and stalled growth
   removes the absorber. Bridges `real-assets` to `sovereign`.

**[NEW] Funding source is a chain attribute, not a detail.** The same buyback
operation has opposite liquidity signs depending on how it is funded:

| Funded by | Nature | System liquidity |
|---|---|---|
| New bill issuance | Debt management — a maturity swap | Roughly neutral |
| **TGA drawdown** | Cash leaves the Fed and enters the banking system | **Adds reserves** |

Almost no commentary makes this distinction, and it is **checkable**: TGA drawdown
against reserve growth, both already pulled in Session 3c. Add `funding_source` to
the chain's buyback leg with reserve growth as the confirming series.

**[NEW] Name the sub-chain: the "Treasury Twist."** Buy back long-dated bonds,
issue short-dated instead — no debt repaid, only reshaped. It has a label, a
mechanism, and dated operations, which makes it a chain rather than an event. **Its
consequence is exactly what consolidated rate-reset velocity measures**: a lower
long rate today, paid for with a larger short-dated stock that reprices at
whatever the future decides. The metric is the cost accounting for the policy.

**One caution to carry in the narrative.** A common reading is that the bond
market dismissed the operation as too small while gold and bitcoin rallied hard on
it. Both cannot be literally true of the same announcement. The coherent version:
bonds priced the *mechanical* effect correctly as trivial, hard assets priced the
*precedent*. That is an interpretation, not something the price action proves —
treat it as a chain thesis, not a fact. **And note the tension the bullish version
skips:** physical gold demand at multi-year lows while gold rallies is the paper
bid moving without the structural bid, which is the fragile-rally state in the
`real-assets` two-bid decomposition, not confirmation of a debasement regime.

**Data footprint, in sequence:** TIC holdings (did Japan actually sell?) → buyback
operation results and ACM term premium → TGA and bank reserves → bill share of
issuance and auction tails → stablecoin supply and issuer bill holdings from
attestations → TREAST and SOMA bill composition, with EFFR–IORB as the tell on
the peg.

**[NEW] Stated policy objectives are predicates.** A published target is a
falsifiable claim with a date and a series attached — a 3% deficit goal against a
6% realized figure, stated WAM intentions, declared buyback program scope. Log
announced objectives into `predicates` the way you log your own watch items, with
`source: official` to keep them separable at grading time. Tracking the gap
between stated and realized policy is cheap, and it is the kind of thing a
monthly report is uniquely well-placed to do.

**Discipline: a chain thesis is a hypothesis with a data signature, not a fact.**
Announcements are reported claims until the footprint appears in the series.
`expected_next` rows carry trigger conditions and confirming series, so they
convert directly into predicates and feed the Session 9 calendar.

**Framing to carry in the Treasury chain narrative:** buybacks address *supply and
liquidity*, while the impairment in duration demand is behavioural — retiring
off-the-run bonds funded by bills does not rebuild the reason an asset-liability
investor wanted duration in the first place. If the stock-bond correlation stays
positive, Treasuries are not doing the job that made them a core holding, and
volatility-weighted allocators reduce the position regardless of yield. Cross-check
against the correlation series in `real-assets` rather than asserting it.

**Commentary requirement:** for any open chain, the narrative renders chain state
explicitly — what has happened, which footprint has and has not appeared, what is
expected next, and what would falsify the thesis. This is the one place the
report is allowed to be forward-looking, because the forward claim is tied to a
named, checkable condition.

## Session 9 — Forward calendar and wire-in
**~2 hours. [CHANGED — auto-populate where possible]**
`calendar.yaml`, but **auto-populated wherever a source exists** — FOMC and BoJ
dates are published, BLS/BEA release calendars are downloadable, earnings dates
come from an API. Hand-maintain only tariff and legal deadlines. A hand-kept
calendar is a staleness trap and you have already been bitten by one.

Then: "The Month in Events" as front matter *before* the executive synthesis, and
per-pillar event injection.

**Done when:** August re-runs with the yen intervention up top and the global
pillar citing it.

### ▶ SHIP v17 — Sessions −1 through 9

## Session 10 — Alt Asset real data
**~2 hours.** yfinance fetcher across all 18 assets, behind the source interface.

## Session 11 — Alt Asset remaining sources and contract
**~2.5 hours. [CHANGED — contract added]**
ETF flows, stablecoin supply, funding and OI, CME basis, MVRV, COT, CPPI, CMBS
OAS. Write to the store. **[NEW]** Publish the extract with a versioned schema
contract and a producer-side test.

**Done when:** the weakest-link disclosure lists zero synthetic series.

## Session 12 — Pillars as config, plus `real-assets`
**~3 hours. [CHANGED — pillar composition becomes config]**
1. **[NEW]** `pillars.yaml` defines each pillar fully: slug, display order,
   series list, metrics list, prompt template path, scoring rule. Prompts move to
   `prompts/<slug>.md`. Adding a pillar becomes a YAML block plus a file.
2. Desk commentary demotes to a section.
3. `real-assets` pillar from the Session 11 extract — metals, crypto, commodities,
   real estate. Gold residual, copper/gold, BTC vs. net liquidity, correlation
   matrix.

EM equity to `internals`; EM sovereign spreads to `credit`.

**[NEW] Stock-bond correlation — the anchor of the correlation matrix.**

The matrix already runs alts against SPX, 10Y and DXY at 60d and 1y. **Add SPX vs.
TLT and SPX vs. 10Y at the same windows, percentile-ranked.** One more row, no new
machinery.

**Why it earns the row.** It is the precondition for the gold bid being decomposed
below: if Treasuries stop hedging equities, diversification demand has to go
somewhere, and that is a structural driver of both the official and paper bids in
this pillar. It also feeds `sovereign` — in a positive-correlation regime duration
is a risk-add rather than a hedge, which changes what term premium is compensating
for.

**The mechanism is real; the threshold is not.** Inflation and supply shocks push
stocks and bonds down together (positive correlation); growth and demand shocks
make bonds rally as stocks fall (negative). Causal, well-established, and the
reason 60/40 worked for two decades and stopped in 2022.

But the widely-circulated "4% CPI decides the sign" framing is a fitted boundary
and fragile. Above 6% CPI the historical correlations still range roughly 0.1 to
0.6; below 4% they range −0.6 to +0.6. **The defensible claim is that high
inflation makes negative correlation rare and low inflation makes it possible** —
weaker and more useful than a threshold.

**Effective n is under five.** Monthly points since 1970 look like 600+
observations, but 3-year rolling windows on both axes overlap heavily and the real
unit is the inflation regime, of which there have been about four.
`trigger_eligible: false`. Render the correlation level and percentile; never
render a CPI threshold as a rule.

**Kill condition:** if the 3y correlation shows no relationship to the 3y average
CPI level across the backfilled history, drop the inflation framing and keep the
correlation as a standalone series.

**[NEW] Options positioning on real assets — the two-bid decomposition.**

This upgrades the gold residual rather than sitting beside it. The residual
already isolates what real rates and the dollar do not explain; **split that
residual into its two sources:**

- **Official bid** — central bank purchases (WGC quarterly, IMF IFS).
  Price-insensitive, slow, persistent.
- **Paper bid** — net call−put open interest, ETF shares outstanding, 25-delta
  risk reversal, all computable from the Session −1 logger.

**The divergence is the signal.** Paper surging while official is flat reads as a
fragile rally. Official accumulating while paper is absent reads as a durable
base. Two checkable states, and better than either component alone.

Apply the same construction to silver, crude and the crypto ETFs where the
official-bid analogue exists.

**Read skew conditionally, never directionally.** Crowded call positioning has
historically marked local exhaustion about as often as breakouts. Crowded calls
with price extended after a run is exhaustion risk; crowded calls with price
breaking from a base is continuation. Set `trigger_eligible: false` — it modifies
conviction, it does not generate signals.

**[NEW] Effective float — the third dimension.** The two-bid decomposition
measures *who is buying*. This measures *how much is actually available to buy*,
and it is what makes reallocation sensitivity comparable across assets.

**Reallocation sensitivity = incremental flow ÷ effective float.**

| Asset | Effective float = total stock minus |
|---|---|
| Gold | Central bank holdings, jewelry, and ETF-locked supply |
| Bitcoin | Long-term-holder supply (CoinGlass provides this), lost coins, ETF and treasury-company holdings |
| Silver | Industrial-consumed supply — genuinely destroyed, unlike gold |

**Why this construction rather than the popular one.** The widely-circulated
version compares a reallocation figure to *annual demand* and produces a large
multiple. That is a stock-versus-flow error: gold is not consumed, so incremental
buying draws from the existing above-ground stock, not from mine supply plus
recycling. Stated correctly it is a claim on the stock — meaningful, but not a
multiple of anything. **State it as elasticity, never as a multiple.**

Two further constraints to note in the narrative: global financial wealth is not
reallocatable — pension mandates, insurance regulatory capital and indexed
mandates rule most of it out — and **the elasticity is symmetric.** The same
illiquidity that amplifies inflows amplifies exits, which the bullish version of
this argument never mentions.

**Scope limit.** The framing holds where the asset is large enough for
reallocation to be a fraction of it. Applied to small-cap assets the arithmetic
produces absurd numbers, which is the signal that the model has stopped applying —
there the binding variables are liquidity depth and regulatory tolerance, not
allocation share. Render reallocation sensitivity only above a market-cap floor.

**Limitation to label, not bury:** GLD options proxy for gold options. COMEX
futures options are larger and OTC larger still, and CME coverage is Growth-tier.
Say so in the output.

**Kill condition:** if call−put OI percentile shows no relationship to forward
20-day returns in either direction after twelve months, drop it.

**[NEW] Disruption–price divergence — a physical-vs-priced surprise measure.**
Derived, not fetched: PortWatch transits ÷ baseline against Brent. This belongs to
the edge layer (Part 15) as much as to `real-assets` — it is an
expectation-versus-outcome measure where the *expectation* is physical reality and
the *outcome* is what the market has priced. **Currently at an extreme**, which is
the interesting fact, not the closure itself.

**[NEW] Cross-pillar wiring: commodity pass-through.** The two metrics defined in
Session 2 render in `inflation` as the pass-through read, while the underlying
commodity complex lives here in `real-assets`. This is the first explicit bridge
between those two pillars, and it is exactly the kind of connection the pillar
structure otherwise hides. Tag both metrics to both pillars in `pillars.yaml`;
render the detail once and reference it from the other rather than duplicating.

The monthly read this produces: *commodities are doing X, pass-through is /
is not showing up in core, therefore the inflation risk is / is not real.* That
sentence is currently absent from the report and is one of the more useful things
it could say.

## Session 12.5 — `global` pillar: THB and the Thailand set
**~45 min. [NEW] Fold into Session 12; listed separately for clarity.**

Add the Thai baht alongside DXY, EUR, JPY and CNY in `global` — FRED `DEXTHUS`
or yfinance. **Not** in `real-assets`: that pillar's logic is real assets as an
inflation and debasement expression, and a currency pair does not belong to it.

Add the rate context, not just spot, so the carry differential is visible rather
than inferred: BoT policy rate, Thai CPI, Thailand 10Y. Spot alone tells you
nothing about why it moved.

**[NEW] Politics sub-block.** The `election_odds` data renders here: priced
probabilities with their month-over-month change, the policy-throughput mapping
(divided vs. unified, and the dated channels each implies), and the vol
term-structure kink around election dates. Conditional implications only —
the neutrality rule from Session 8 applies verbatim.

**[NEW] Thailand standing block — a recurring paragraph in the Monthly.**
Rationale: a THB-denominated property asset in Nan province. This is exposure
monitoring, not trade generation.

**One paragraph plus a five-line data strip. Hard cap.** The temptation with a
personal-interest section is to let it grow; it earns one paragraph because the
exposure is one asset.

**Data strip, all free:**

| Line | Series | Source |
|---|---|---|
| Currency | THB/USD level, 3m change, `path_divergence` flag | FRED `DEXTHUS` / yfinance |
| Rates | BoT policy rate, and the differential vs. Fed | BoT |
| Inflation | Thai CPI YoY | BoT / TradingEconomics |
| Growth | Thai GDP or exports YoY | NESDC |
| External | **FX reserves (level + 95th-pct drawdown flag)**, current account | BoT |

**The narrative paragraph covers what the strip cannot:**

- **Political and government development** — coalition stability, leadership
  changes, constitutional court actions, royal transition context. Thailand's
  political risk is episodic rather than continuous, and its history of coups and
  court-driven government dissolutions makes this the *primary* risk to monitor,
  ahead of the currency. Sourced through the events layer: tag events
  `country: thailand`, salience-filtered.
- **Property-relevant policy** — foreign ownership rules, land regulation, tax
  changes affecting foreign holders. Rare but material when they occur; these are
  calendar and event items, not series.
- **Baht-specific drivers** — tourism recovery, rice exports, regional capital
  flows, and the gold linkage already flagged for testing in the correlation
  matrix.

**Reading discipline:** most months this paragraph should say *"no material
change"* in one sentence plus the strip. **A personal-exposure section that
manufactures narrative every month trains you to skip it** — the same
only-what-changed rule as everywhere else, applied more strictly because the
temptation runs the other way.

**Escalation rule — percentile-based, not a fixed percentage.** A fixed 5% would
be a ~3-sigma event for a managed float that the BoT actively suppresses — the
rule would fire once in several years and be decorative, while missing the 3%
move that matters precisely *because* the management failed. Escalate on any of:

1. **Monthly THB move beyond the 95th percentile** of rolling 3-year monthly
   moves — self-calibrating to the vol regime, no manual review
2. **`path_divergence` fires on THB** — the intervention-and-snapback pattern the
   yen just demonstrated
3. **BoT FX reserves drawdown beyond its own 95th percentile.** *The early
   warning.* A managed currency's stress appears in reserves before spot, because
   the management absorbs it — reserves falling while spot is calm is the signal;
   the spot move is the late confirmation
4. **Political events at salience 4+** (already relative by construction)

Any trigger promotes the block from Monthly to Weekend Synthesis until resolved.
The property does not trade, but conversion and remittance timing might — and
note the asymmetry: baht *weakness* cheapens future remittances, so escalation
watches for **disorder, not direction**.

**Two follow-ons:**

- **The property position belongs in the trade register, not a pillar.** It is a
  position, not a market observation. Record it with the currency mismatch
  explicit — THB-denominated asset, USD income and liabilities — so it shows up
  in exposure aggregation rather than living only in your head.
- **Test the gold linkage once the correlation matrix exists (Session 12).** THB
  has historically shown sensitivity to gold through domestic trading flows. If
  that holds in your data, it connects Thailand exposure to `real-assets` in a
  way that is not obvious from the pillar structure. Test it; do not assume it.

## Session 13 — `internals`
**~3 hours.** RSP/SPY, top-10 weight, breadth, implied correlation, dispersion,
IWD/IWF, small/large, SMH/IGV, EM vs. DM. Silverblatt earnings file and forward
EPS revisions. Mag 7 earnings share vs. cap share; S&P ex-Mag7 EPS growth.

**[NEW]** Add single-name GEX from the Session 5 logger — NVDA and the rest of
Mag 7. Basic tier covers all 6,000+ optionable equities, so concentration risk
gets a dealer-positioning dimension that nothing else in your stack provides.

**[NEW] Full size ladder, not just small-vs-large (~20 min).** IWM/SPY alone is a
muddy signal: it blends risk appetite, rate sensitivity and profitability.
Roughly 40% of the Russell 2000 has negative earnings and small caps carry more
floating-rate debt, so that ratio often reads as a rates trade wearing a
risk-appetite costume. Four rungs separate them:

| Rung | Construction | Reads |
|---|---|---|
| Mega vs. large | Top-10 weight, RSP/SPY | Pure concentration; currently an AI-trade proxy |
| Large vs. mid | SPY/MDY | **Cleanest breadth signal** — mid-caps are profitable and less rate-levered, so this is genuine narrowing rather than a credit story |
| Mid vs. small | MDY/IWM | Mostly rates and credit quality — the profitability cliff sits here |
| Small profitable vs. unprofitable | **S&P 600 vs. Russell 2000** | S&P 600 requires positive earnings for inclusion; Russell 2000 does not. **The best free proxy for junk-equity risk appetite available** |

**The reason to build it: it is the equity-side confirmation of the credit read.**
Unprofitable small caps and CCC borrowers are largely the same companies seen
through different instruments. CCC widening *and* the profitable-vs-unprofitable
small-cap spread widening is confirmation; divergence means one market is wrong,
which is worth knowing. CCC is currently the one pillar dissenting from the
sanguine consensus, so a second instrument on the same question has real value.

**[NEW] High-beta vs. low-vol correlation — a realized dispersion measure
(~15 min).** Rolling 45-day correlation of SPHB and SPLV returns,
percentile-ranked. Three lines of code.

**Read it as dispersion, not correlation.** Both are long-only equity indices, so
they normally correlate near +0.8 — both are mostly beta. When the correlation
goes deeply negative, market direction has stopped explaining returns and factor
rotation is doing all the work: investors are actively selling one to buy the
other. That is an extreme in realized factor dispersion.

**Why it belongs next to implied correlation and dispersion:** those measure the
same phenomenon through options and are forward-looking, while this is realized
and backward-looking. **The gap between them is more informative than either
alone.**

**Cross-check against the size ladder.** A violent low-vol-versus-high-beta
rotation is a de-grossing signature, and it should also appear in the
profitable-vs-unprofitable small-cap spread, since unprofitable small caps are
high beta. Both firing together means the rotation is real; only one firing
suggests a factor-construction artifact.

**Effective n under five.** The historical episodes number five or six, several
clustered within the last year and therefore not independent — and the record is
mixed, with some preceding tops and others preceding nothing.
`trigger_eligible: false`, conditioner only, and never rendered as a top signal.

**Run the correlation guard on the mega-vs-large line specifically** — it may
exceed 0.7 against top-10 weight, in which case keep one and drop the other.

## Session 14 — AI financing and dealer gamma
**~3 hours. [CHANGED — scoped to Basic-tier access]**
1. SEC XBRL frames fetcher — capex, FCF, receivables, DSO.
2. AI financing block in `credit`: hyperscaler capex vs. operating cash flow,
   depreciation lengthening, NVDA DSO, vendor financing, neocloud spreads,
   data-center ABS, IG tech issuance.

   **[NEW] Three additions from the 10-Q, all reachable by the same XBRL
   fetcher:**

   - **Receivable concentration, not just the level.** Roughly five direct
     customers now account for about 70% of NVDA receivables, on a balance up
     ~64% to $63B in six months. **Concentration is the risk** — it is direct
     counterparty exposure to a handful of capex budgets. Track customer count at
     50% and at 70% of receivables, plus the balance's growth rate.
   - **Purchase commitments vs. quarterly revenue — the bullwhip ratio.** Roughly
     $530B committed against $96B sold, with the supply-and-capacity portion
     jumping from ~$119B to ~$279B in one quarter. **These are off-balance-sheet
     obligations, so they appear in none of the ratios above.** Track the ratio as
     a time series; the 2021–22 cycle on the same measure shows what an unwind
     looks like.
   - **The three early-warning lines**, logged as predicates with thresholds:
     inventory (up ~48% since January), receivables aging, and gross margin
     against the guided trough. **Deterioration appears here before it appears in
     revenue.**

   **Framing for the narrative:** the supplier has shifted cycle risk from its
   customers onto its own balance sheet, funded partly with ~$25B of new debt.
   That is a credit story, which is why it belongs in this pillar rather than in
   `internals`.

   **Apply the same three metrics to the other AI-exposed names** as the theme
   develops — concentration, off-balance-sheet commitments and inventory are
   generic supply-chain stress measures, not NVDA-specific ones.
3. Build the `sentiment` pillar on the history the Session 5 logger has been
   accumulating since v17 — GEX, DEX, VEX, CHEX, flip distance, wall positions,
   with percentile ranks once you have enough observations.
4. **Use SPX, not just SPY.** Index symbols are gated to Basic and above, so you
   already have access and are not using it. SPX notional gamma dwarfs SPY's;
   reading SPY alone understates index dealer positioning. Your current email
   digest is SPY-only.
5. Add CBOE put/call, SKEW, VVIX, VIX term structure. Together this takes
   `sentiment` from two live series to a dozen.

### **[NEW] Expiry-bucket decomposition — buckets map to report horizons**

Reading aggregate GEX for a swing thesis is a category error: 0DTE gamma is
enormous in notional and gone by the close. **Each report reads the bucket
matching its horizon.**

| Bucket | Drives | Report |
|---|---|---|
| 0DTE | Intraday pinning and reversion | Daily Cascade |
| 1 week | Current-week range | Daily / Weekend |
| Monthly (OpEx cycle) | **1–3 week regime** | **Weekend Synthesis** |
| 3m+ | Structural positioning | Monthly `sentiment` |

**Four derived metrics per bucket:**

1. **0DTE share of total GEX.** High share = intraday mean-reversion regime with
   little multi-day information content.
2. **Flip level per bucket.** Near-dated and all-expiry flips often diverge and
   mean different things — one is the intraday battleground, the other the regime
   level.
3. **Charm decay profile.** CHEX concentrated in near expiries measures how much
   delta must be mechanically re-hedged into expiry. The pin driver.
4. **Post-expiry profile — the standout.** Recompute the surface excluding the
   expiring bucket: *what does the board look like next Monday?* Directly the
   swing thesis input, tied to the expiry-cycle clock specified for Weekend
   Synthesis, and almost nobody computes it.

Plus **bucket concentration** as a fragility read: gamma concentrated in a single
expiry means the regime changes discontinuously on that date rather than decaying.

**Treat the horizon-to-movement link as a test, not an assumption.** Does 0DTE
share predict realized intraday range? Does post-expiry gamma predict next-week
range? Log from Session −1, test when n permits.

**Write the sign-convention caveat into the pillar prompt.** Standard GEX signing
treats calls as positive and puts as negative — an assumption about who is
buying. Flow-signed polarity would resolve it and is Growth-tier. State the
assumption in the output rather than implying it is settled.

## Session 15 — Close the loop
**~3 hours. [CHANGED — this is now a real loop, not a scoreboard]**
1. Predicate emission — `{series_id, operator, threshold, deadline, prose}`.
2. **[NEW]** Grade predicates **daily** against the store, not monthly. A 30-day
   predicate checked daily tells you whether it triggered and reverted — path
   information a month-end check discards.
3. **[NEW]** Tier 1 narrative audit as a monthly automated report: numbers
   correct, claims sourced, uncertainty flagged.
4. **[NEW]** `calibration_log` table and a written quarterly review protocol —
   what you're allowed to change at what evidence threshold, per the three tiers
   in Finding 4.
6. **[NEW] Correlated-confirmation guard.** Before any metric enters a composite,
   measure its correlation against the existing pillar sub-score. **|ρ| > 0.7 →
   narrative colour only, outside the composite.** External agreement built on
   variables you already score is not independent evidence; this is the specific
   mechanism by which a valuation-heavy composite talks itself into staying wrong
   longer.

   **Run this against my own additions, not just new candidates.** Internals
   dispersion against sentiment VIX, and the gold residual against real rates
   already carried in inflation and momentum, are both plausible failures.
7. **[NEW] Predicate basis requirement.** Every predicate records the basis for
   its threshold and its effective n. Several thresholds in the current report —
   240K claims, 200bp BB, 11.5% CCC — are round numbers the narrative model
   produced, with no stated derivation.
8. **[NEW] Confidence on pillar scores.** A −2 to +2 score with a label like
   OVEREXTENDED implies precision the signal class may not support. Index-level
   top detection appears to lift the odds of a large drawdown from roughly 42% to
   62% — real, but a distribution shift rather than a turn call, and possibly a
   structural ceiling rather than a calibration gap. Scores carry a confidence
   derived from effective n, and top-side language reads as probability shift.
9. **[NEW] Threshold fragility audit.** For each trigger, how far does the
   threshold move before a calibration episode reclassifies? Any trigger where a
   <5% shift flips an episode is tuned, not calibrated.

### **[NEW] Section 0 — the Monthly scorecard**

The Monthly report opens with its own accountability. Order: **Scorecard → Month
in Events → Executive Synthesis.** First because it frames how much to trust what
follows, and because it is the section most likely to be skipped if buried.

**Critical constraint: the pillar narratives must not see the scorecard.** A model
that reads "we were too bearish last month" before writing this month's view will
drift dovish regardless of the data. That is performance-chasing at the narrative
layer, and it is subtle enough to be invisible in the output. Render it for the
reader; keep it out of the pillar prompts.

**Deterministic half — grade engine, no LLM:**
- Recommendations by horizon: count, closed, hit rate, average return, expectancy
- **The 2×2** — right thesis/made money, right thesis/lost money, wrong
  thesis/made money, wrong thesis/lost money. The off-diagonals carry the
  information; *wrong thesis making money* is the most dangerous cell in the
  system, because it rewards a broken process
- Predicate resolution, overall and by pillar
- Declined recommendations and how they would have performed
- Swing thesis revisions per cycle
- Hedging share and anticipated-surprise share

**LLM half — half a page, tightly constrained:**
- Prompted with the *losing* calls and *wrong* claims specifically, never the wins
- Must lead with the worst call of the month
- Must name one thing the framework got wrong and one it missed entirely
- **Forbidden from claiming improvement without a number**

**Every figure renders against trailing-12-month and observation count.** One
month at monthly cadence is n=1. Without the trailing column a good month reads
as skill, and you will act on it.

### **[NEW] Cross-report reflection**

The loop covers **every** report, not just Monthly. Same harness, one artifact:
Daily recommendations, swing theses, Top & Bottom verdicts against forward
returns, Monthly predicates, and Disruptive Themes regime calls on an annual
clock. Generated by the grading engine — not a report anyone writes.

**Prerequisite I missed earlier: archive the rendered narrative.** The store holds
data and predicates but not what the report actually said. **You cannot audit
commentary you did not keep**, and re-deriving it would produce today's model's
version of last quarter's reasoning. Archive every rendered report verbatim,
keyed to `run_id`, in the same session that builds the store.

**Three checks:**
1. **Numbers** — every figure against the vintage that existed *at publication*,
   so revisions never count against the call.
2. **Claims** — causal assertions against the event record and subsequent data.
3. **Hedging** — the share of claims that were falsifiable at all. A report that
   says "could go either way" is never wrong and never useful. Expect this one
   to sting.

### **[NEW] Four more loops — log now, analyse at n**

**The principle: separate logging from analysis.** All four need data that cannot
be reconstructed later, and none can say anything before roughly month eighteen.
Add the columns now — they are columns, not projects — and schedule the analysis
for when n permits. Same argument as the GEX logger.

**1. Confidence calibration.** *The largest remaining gap.* Everything grades hit
rate; nothing grades whether stated conviction matches realized frequency. If
high-conviction calls hit at the same rate as low-conviction ones, conviction is
noise — and conviction drives `size_multiplier`. Log stated confidence on every
recommendation and predicate; produce a reliability curve and Brier score once
n permits. **This is the loop that makes sizing evidence-based rather than felt.**

**2. Regime-conditional performance.** Overall hit rate is close to useless. Hit
rate *by regime* is where the learning is — the system may be good in trending
liquidity and poor in chop. Pillar scores and regime labels are already stored;
stamp every recommendation and predicate with the regime in effect at the time.
Changes *when* you trade, not only what.

**3. Timing error decomposition.** Right but three weeks early is a different
failure from wrong, and only one is fixable. Log signed time-to-resolution.
Systematic earliness means delay entry and widen invalidation; wrongness means
stop. Cheap, and likely to explain a large share of swing-horizon results.

**4. System versus discretionary.** Log trades taken that the system never
recommended, flagged `origin: discretionary`. **The gap between system-generated
and self-generated performance is the actual question about whether any of this
is worth building**, and nothing else measures it.

**Explicitly deferred, and not for lack of merit:** input ablation (recompute
pillar scores with each series removed to find which ones actually move the
output — powerful, but wait until the annual prune proves insufficient); prompt
A/B testing on the hedging and falsifiability metrics; external benchmark
comparison against a naive rule, so the loops are not purely self-referential;
and signal-decay tracking via rolling IC, since a metric that worked for two
years and stopped is a different case from one that never worked.

**A closing caution on all of this.** There are now roughly fifteen loops in the
system. Measurement is not free — each one is maintenance, and the operator is
the scarce resource. Resist adding a sixteenth until at least one of these has
changed a decision.

### **[NEW] Coverage-gap scan — detecting what the framework is missing**

The events layer gives this nearly free. Every event is classified with
`affected_series`. **High-salience events that map to no series are blind spots.**

```sql
coverage_gaps (event_id, salience, theme_cluster, first_seen, occurrences)
```

Aggregate unmapped high-salience events over 90 days, cluster by theme, and
review quarterly. A recurring untagged theme is a candidate metric or pillar —
driven by what actually happened, not by speculation about what might matter.

**Anticipated-surprise share.** The Session 6 surprise ranking produces the
month's five largest anomalies. What fraction had a predicate pointing at them?
Consistently unanticipated surprises mean the forward-looking layer is watching
the wrong things — measurable rather than a feeling.

**Both feed the quarterly calibration review**, where a recurring gap either
becomes a registry entry or is explicitly declined with a reason.
5. Pillar scores −2 to +2 persisted with rationale.

### ▶ SHIP v18 — Sessions 10–15

---

# Part 4 — Operating cadence

The architecture only stays durable if the maintenance is scheduled.

| Cadence | What | Time |
|---|---|---|
| **Every run** | Validator, canary diff, numeric audit, alerting — all automated | 0 |
| **Monthly** | Read the cross-report reflection: numbers, claims, hedging share, and what resolved across all five reports. Fix what it flags. | 30 min |
| **Quarterly** | Calibration review: predicate hit rates, threshold pruning, prompt edits — **plus the coverage-gap cluster list and anticipated-surprise share.** Each recurring gap either becomes a registry entry or is declined with a reason. Log every change. | 2.5 hours |
| **Semiannual** | Model upgrade evaluation — re-run prior month on old and new, diff, decide deliberately at a version boundary. | 1 hour |
| **Annual** | Registry audit: which series never moved the read? Which pillars never changed a decision? Cut them. | 2 hours |

The annual cut matters more than it sounds. Systems like this accrete metrics and
never shed them, and the report gets longer and less useful every year.

---

# Part 5 — Deferred backlog

## v17.5 — elevated. ~3 sessions, run after v17 ships, before v18.

**The elevation test:** an item leaves the backlog only if it (a) unblocks
something already scheduled, (b) accumulates data you cannot buy back later, or
(c) closes a silent-failure path. **Coverage alone is never a reason.**

That test disqualifies most of the fetcher backlog by design — CFTC, FINRA, AAII,
NAAIM and ICI all publish free history, so waiting costs a query and nothing else.
It also protects Top & Bottom, banking, dashboard and Tier D from being pulled
forward on enthusiasm.

Four items pass:

1. **Auction results + TIC foreign holdings** — *unblocks.* These are the first
   two confirming series in the Treasury financing chain. Session 8 builds a
   chain whose thesis is "Japan will not need to sell, bills get absorbed";
   without auction tails, bid-to-cover, indirect share and TIC, the chain cannot
   confirm or falsify itself. ~1 session.
2. **Nowcasts — GDPNow, NY Fed WEI, Cleveland Fed inflation** — *unblocks.* The
   momentum pillar currently leans on a GDP print months stale. ~0.5 session.
3. **Disruptive Themes spine hook and programmatic refresh trigger** —
   *silent failure.* Same class as alerting: any Top & Bottom overlay ACTIVE
   beyond 30 days without composite movement raises a refresh flag. Themes has
   gone stale once already. ~1 session.
4. **Daily Cascade audit** — *silent failure, and a prerequisite.* You cannot
   currently confirm what is running or from where, and this gates both the trade
   register and IBKR Gate 2. ~0.5–1 session.

**Borderline, called in favor:** stablecoin issuer bill holdings from
attestations. Attestation history is scattered and awkward to reconstruct, which
makes it closer to the GEX case than the FRED case — start the log early even
though the analysis lands later.

---

## The rest

0. **From the methodology work** — sequenced, ~4 sessions:
   - **Re-Rating Exhaustion** into Valuation (Shiller ingest lands in Session 6).
     *Note on the popular bubble-vs-boom framing:* "a bubble is when price
     detaches from earnings" is true but not decision-useful, since it is only
     diagnosable in hindsight — Cisco's forward EPS was also rising through 1999,
     and the divergence became obvious after earnings stopped, not before. Charts
     making that comparison also index both series to a chosen start date, which
     makes "earnings kept pace" partly a function of where you begin. **RRE is the
     quantitative version of the same question**, applied to the index rather than
     one name, which is why it is the metric to build.
   - **Consolidated rate-reset velocity** — the most construction work of the
     set, and the most original. Stated WAM near six years understates
     consolidated rate sensitivity: SOMA-held Treasuries are financed by reserves
     paying IORB, so roughly $4.3T of nominally long paper reprices daily. Use
     *share maturing within 12 months* rather than the mean, net out SOMA, add
     reserves at IORB. **The gap between stated WAM and consolidated reset
     velocity is where the signal lives.** Fits the Liquidity & Funding Stress
     overlay.
   - **Total shareholder yield vs. real 10Y** — dividend plus net buyback yield
     against the real 10-year, replacing the "% of names yielding more than the
     10-year" construction, which is a rate chart in equity costume. Keep it as
     an allocation and flow indicator, never a valuation input. **Worth
     elevating: it is a marginal-buyer metric with real duration and surplus
     implications, and the one series here that sits directly in your
     professional expertise.**
   - **Foreign share of debt held by public** (TIC) — foreign holdings roughly
     flat in dollars while total debt nearly doubled. Who absorbed the difference
     is the substantive question.
   - **Aggregate duration supply vs. demand** — `duration_supply_balance`, a
     conditioner in `sovereign`, `trigger_eligible: false`. The September 2026
     global yield synchronisation (JGB 10y at 3% first time since 1996, gilts at
     multi-decade highs, bunds/OATs at 2008–11 highs, UST 30y ~5.27%) is best
     read as one repricing of a shared discount rate, and the mechanism is the
     issuance pool: sovereign net coupon supply PLUS record corporate issuance
     ($4.9T global 2026, +14%; hyperscaler data-centre bonds $220B YTD, >2x the
     prior full year) drawing on the same buyers, while net foreign private
     Treasury demand prints near zero ($16.6B in June). Build as a quarterly
     three-line read: (1) supply — UST net coupon issuance ex-Fed + IG gross
     issuance (SIFMA), (2) demand proxies — TIC net foreign private purchases,
     ICI bond-fund flows, bank H.8 securities, stablecoin bill absorption
     (bills netted OUT of the supply line: the bill/coupon mix is the Twist
     chain's variable, and bills have their own buyer), (3) the balance,
     percentile-ranked against 2010+. **Reading rules written in advance:**
     hyperscaler issuance double-counts with the AI-financing block — same
     fact, two lenses; tag `ai`, never count twice in confluence. And the
     JGB leg escalates to scenario 11, not here: domestic repatriation by the
     largest foreign holder is its own tripwire with its own series (TIC
     Japan, hedged-yield spread), and this metric only conditions the
     backdrop it happens in.
   - **Threshold fragility audit** across the ten Top & Bottom triggers — reuses
     the existing calibration harness.
   - **Daily Cascade only:** overnight range percentile and open location vs. ON
     high/low. Both documented, both available at 9:30, neither requiring session
     narrative. Not a Top & Bottom input.
   - **Do not build:** bull-run percentage-gain comparisons, the raw
     dividend-yield-count metric, any CAPE-threshold binary, and session-rotation
     classification unless it beats an ON-range-plus-open-location baseline on
     500+ days with rules declared in advance.

1. **Fetcher backlog Tiers A–B, remainder of C** — ~3 sessions. Auction results,
   GDPNow / NY Fed WEI / Cleveland Fed nowcasts, Indeed Job Postings, CFTC COT
   across equity index, rates and dollar, FINRA margin debt, AAII / NAAIM /
   Investors Intelligence, ICI weekly flows, FRA-OIS, CP spreads.
   *Reduced from 4 sessions: Session 3 absorbed the Daily Treasury Statement,
   SOFR–IORB, SRF usage and repo fails — most of Tier C, which was the part that
   confirms the reserve-scarcity call.*
2. **Top & Bottom** — 1–3 sessions, sized by the Session 1 finding.
3. **Banking pillar** — 2 sessions.
4. **Full Horizon 2 wiring** — 2 sessions. Session 14 delivers the data.
5. **Desk views ingest** — 1 session.
6. **Dashboard live wiring** — 2 sessions. Alerting already shipped in Session 7,
   so this is now genuinely optional.
7. **Disruptive Themes spine hook** — 1 session.
8. **IBKR source implementation** — 1 session, when the execution track needs it.
9. **Daily Cascade audit and store migration** — 2 sessions.
10. **Off-exchange volume share** — 0.5 session. FINRA ATS data, free, at its
    native two-to-four-week lag. **Market-structure conditioner only, never
    directional.** `trigger_eligible: false`.

    *Why it is narrow:* off-exchange volume is majority retail wholesaler
    internalization, and print side is not counterparty direction — both sides
    are anonymous by construction. Reading it as institutional accumulation is
    the standard error in this category. The lag also rules out anything
    tactical.

    *What it is good for:* when off-exchange share spikes, lit-book liquidity is
    thinner than headline volume suggests, and dealer hedging flows into a thin
    lit book move price more. That is a real interaction with the gamma work in
    `sentiment`, and it feeds `internals` as a structure read.

    *Explicitly not built:* block-print detection, sweep inference, and any
    "dark pool sentiment" score. For the underlying question — institutional
    positioning — 13F, CFTC COT, ETF creations/redemptions and dealer DEX all
    answer it directly rather than by inference from anonymized prints.

11. **Tier D fetchers** — 2 sessions. 13F via SEC EDGAR (quarterly), GPR / EPU /
    Trade Policy Uncertainty indices, EIA weekly petroleum and gas storage, Baker
    Hughes rig count.

**Backlog total: ~22–24 sessions, roughly 45–50 hours.** The trade register
(Part 7, ~2 sessions) and IBKR Gates 1–2 (Part 8, ~5 sessions) sit outside this
count and are sequenced separately.

---

# Part 6 — Timing

**Sessions −1 through 15 total roughly 48 hours.** The per-session headlines above
sum to about 43, but several sessions absorbed additions after their headline was
written — the realistic figure is 48.

| Segment | Sessions | Hours |
|---|---|---|
| **v17** | −1 through 9 | **~31** |
| **v18** | 10 through 15 | **~17** |
| **Total** | | **~48** |

Where the growth landed since the 32-hour v2 estimate: Session 3 is now the
largest single block at ~4.75 hours (policy path, funding stress and swap
spreads, fiscal position), Session 5 at ~4 (vintages, GEX logger, `policy_path`,
`index_members`), Session 8 at ~4 (event chains), Session 6 at ~2.75 (Shiller,
surprise ranking), Session 2 at ~3.5 (methodology fields, commodity metrics).

| Pace | v17 | v18 |
|---|---|---|
| 2 sessions/week (~5 hrs) | 6 weeks | +3.5 weeks |
| **3 sessions/week (~7.5 hrs)** | **4 weeks** | **+2.5 weeks** |
| Intensive (1/day) | 11 days | +6 days |

At three per week from Monday: **v17 by early October, v18 by late October.**

**Split Session 3** if it runs long — 3a for sampling, source abstraction and term
premium; 3b for policy path, funding stress and fiscal. Four-plus hours is more
than one sitting.

The deferred backlog is a separate ~45–50 hours and is not counted here.

**Three risks worth naming.**

- **Session 8 overrun.** Event classification taxonomies need iteration. Budget a
  second pass.
- **Overfitting the feedback loop.** The failure mode isn't that it won't work —
  it's that it will feel like it's working at n=12. The three-tier discipline in
  Finding 4 exists to stop that. Hold it.
- **You are the single point of failure.** Everything above assumes you keep
  showing up, and you have already gone dark once — roughly two months, during
  which Themes went stale and the pipeline sat at `never_run` with nothing to say
  so. The architectural response is Session 7: an inverted heartbeat so absence of
  signal is itself the alert, degrade-don't-fail so partial output beats silence,
  and a welcome-back digest so returning is resuming rather than re-deriving.
  Build for the version of yourself who is busy for six weeks.

**If you only have an hour before you go quiet, spend it on Session −1.** The
current system will not self-heal — `monthly_macro` is still at `never_run` with
the secrets unadded, so several weeks away means returning to exactly this state.
The GEX logger is the one thing that makes the gap cost less than it otherwise
would.

**The one thing not to cut:** the validator and the numeric audit. A durable asset
built on unverified numbers isn't durable, it's just long-lived.

---

# Part 7 — Trade recommendation register

**Status: long-term roadmap. ~2 sessions, immediately after Session 15.**

Every report already produces trade expressions — Monthly Appendix C, Top &
Bottom Appendix D, Daily Cascade signals — and none of them are tracked in one
place, graded, or checked against each other. The register fixes that.

It is structurally the `predicates` table with P&L attached, so it reuses the
Session 15 grading harness rather than building a second one.

## Horizon taxonomy — the absorption mechanism

Thirteen documents stay thirteen documents. What makes the system readable is that
every report writes into one register with an explicit `horizon`, and **the
register is the surface you read.**

| Horizon | Window | Owner |
|---|---|---|
| `intraday` | 0–1 day | Daily Cascade |
| `swing` | **1–3 weeks** | **Weekend Synthesis — the gap** |
| `positional` | 1–3 months | Top & Bottom |
| `strategic` | 3–12 months | Monthly Macro |
| `structural` | 1 yr+ | Disruptive Themes |

**The swing horizon was uncovered.** Daily runs to next session; Top & Bottom
fires on structural extremes measured in months; Alternative Asset is weekly
cadence but answers *which instrument*, not *which direction over ten sessions*.
This is likely where the real edge sits, since it is where dealer positioning and
macro regime overlap.

**Fill it by elevating Friday, not by adding a report.** The Friday 1800 Weekly
Reflection already carries the right inputs — weekly thesis review, Monthly Macro
delta, GEX/vol weekly reset, correlation matrix. Reframe it from retrospective to
**swing-horizon setter**: it looks back *and* sets a 1–3 week thesis with levels,
invalidation, and sizing. A sixth report means a sixth cadence to maintain, and
cadence is what decays first during a gap.

**Make it expiry-aware.** The clock at this horizon is the options cycle, not the
calendar — monthly and quarterly OpEx, and charm/vanna decay into expiry, reset
gamma positioning on roughly a three-week rhythm. Where are we in the cycle, what
rolls off, what does the profile look like after. The Session −1 logger already
collects what this needs.

## Swing thesis tracking — the daily/weekly handshake

The Friday thesis is carried, checked, and where necessary revised by the daily
reports. Four rules make that work rather than degenerate.

**1. Invalidation is defined Friday, never mid-week.** A price level or a named
series crossing, written down before the position exists. Judged fresh each
morning, it drifts toward whatever the tape looks like.

**2. Three states, checked mechanically.**

| State | Meaning |
|---|---|
| `INTACT` | Thesis and levels holding |
| `STRAINED` | Moved against, invalidation not triggered |
| `INVALIDATED` | The pre-set condition fired |

The pipeline computes the state from the level. The narrative reports it; it does
not decide it.

**3. Revision creates a new record.** The Friday recommendation gets
`superseded_by` and stays in the register exactly as written. Overwriting
destroys the grading trail. Three distinct cases, graded differently:
*invalidated* (thesis wrong), *evolved* (thesis intact, levels shift),
*superseded* (new information, different thesis).

**4. Revision has a bar, or the swing horizon collapses into the daily one.**
This is the real failure mode: the value of a 1–3 week view is that you do not
re-decide every morning. Revision requires the invalidation trigger firing or a
named calendar event — not a change in feel. Revisions happen at the 7AM brief
only, never intraday.

**Process metric: revisions per cycle.** Three or four revisions in fifteen
sessions means the Friday process is producing noise, not theses. Track it before
concluding the swing horizon does not work.

**Grade the original on its own terms.** A thesis exited early that would have
worked is a different failure from a thesis that was wrong, and only the register
can tell you which one recurs.

**Daily render:** thesis, session N of ~15, state, distance to invalidation,
what changed, and what would have to happen today to flip it.

## Reactive intraday recommendations

**Three distinct acts, only two of them permitted intraday:**

| Act | Intraday? |
|---|---|
| Mark swing thesis `INVALIDATED` | **Yes** — the level broke; computed, not judged |
| Write a replacement swing thesis | **No** — waits for next 7AM or Friday |
| Issue a new `intraday` recommendation | **Yes**, under the constraints below |

The third is a different horizon, not a revision. It does not touch the swing
thesis, which stays invalidated until its normal revision point.

**Four constraints, or this becomes "whenever it feels exciting":**

1. **Mechanical triggers, defined in advance** — gap beyond a multiple of
   expected move, open outside the overnight range, gamma flip crossed at the
   open, or a calendar event that fired overnight. The system proposes only on a
   trigger, never on general volatility.
2. **Cooling-off window** — nothing in the first 30 minutes. Opening prints are
   noisy and reverse often; midday is the right slot, not 9:35.
3. **Capped size, one per day** — half normal size, hard limit of one, none at all
   if the daily loss limit is already touched. A reactive trade immediately after
   a thesis breaks is where revenge trading lives.
4. **Tagged `origin: reactive`**, graded separately from day one.

**On the fourth.** The expectation is that reactive trades underperform planned
ones — that is the usual finding, and it would be invisible inside a blended hit
rate. But it is an empirical question about this operator, not about traders in
general. Build it, instrument it, and let six months of data decide whether it
stays. If reactive trades earn their keep you will know; if they do not, you will
have evidence rather than a suspicion you keep overriding.

## Design rule: recommendations and positions are separate tables

The register tracks *ideas*. The broker tracks *fills*. They join on `rec_id`.
Collapsing them into one table is the mistake that makes both unusable — you lose
the ability to ask "how good are our ideas" separately from "how well do we
execute," and those are different problems with different fixes.

## Schema

```sql
recommendations (
  rec_id, source_report, run_id, date,
  instrument, structure,          -- outright / spread / QS / defined-outcome
  direction, thesis_ref,          -- the pillar, trigger, or factor that produced it
  conviction, horizon,
  entry_ref, invalidation, target,
  status,                         -- proposed / active / closed / invalidated / expired
  superseded_by, closed_reason
)

positions (
  position_id, rec_id, broker_order_id,
  opened_at, closed_at, fills, realized_pnl, unrealized_pnl
)
```

## Cross-report conflict detection

This is the value that only a *cross-report* register delivers, and it is the
main reason to build it.

Monthly says up-in-quality within credit. Daily Cascade takes a short-vol
expression. Top & Bottom fires a risk-off trigger. Today nothing reconciles
those, and you would only discover the contradiction from the P&L.

The register runs three checks on every new recommendation:
- **Contradiction** — opposing direction on the same or closely proxied exposure,
  **within a horizon**
- **Duplication** — same trade arriving from two reports, which double-sizes if
  taken twice
- **Correlated stacking** — several recommendations expressing one underlying
  bet (long credit, short vol, and long small-caps are one trade in a drawdown)

**Correction to an earlier version of this rule.** Contradictions were originally
scoped across all reports. That is wrong once horizons are explicit: being
tactically long inside a strategically bearish regime is normal — it is the term
structure of the book, not an error. **Flag contradictions within a horizon;
across horizons, flag only when aggregate exposure or correlated stacking crosses
a limit.**

**Grade expectancy separately by horizon.** You may be good at one and poor at
another, and a blended number hides precisely the thing worth knowing.

## Two constraints

- **Feed the existing expectancy ledger in `execution-framework-v2`, do not
  duplicate it.** Two ledgers means two answers.
- **Appendix C stops being manual.** It becomes a query against the register,
  filtered to the current regime read.

## Grading

Same harness as predicates, one extra dimension. A predicate asks *did the
threshold trigger*. A recommendation asks that plus *what did it earn*. Grade
both, and keep them separate in the output — a right thesis that lost money and a
wrong thesis that made money are different failures, and averaging them teaches
you nothing.

---

# Part 8 — IBKR execution

**Status: long-term roadmap, gated. Gate 1 ~2 sessions, Gate 2 ~3 sessions.
Gates 3–4 are a decision, not a build.**

## The governing principle

From `execution-framework-v2`, and it is the right one: **Claude writes rules,
Claude is not in the execution path.** Signals → deterministic rules → orders. No
LLM output ever becomes an order. Everything below preserves that.

## The architectural fact to confront first

**IB Gateway must run persistently.** Your entire stack is serverless — GitHub
Actions plus cron-job.org, nothing always-on. Execution requires a VPS or a
machine at home that stays up, monitored, patched, and reachable.

That is a genuinely different operational commitment from everything else in this
document, and it should be a deliberate decision rather than something you drift
into. Budget for the host, the monitoring, and the failure modes of a box you now
depend on.

## Prerequisite

Daily Cascade's run status was last recorded as *unclear what's still running*.
**Do not route orders off a pipeline whose execution you cannot confirm.** Before
Gate 2, Daily Cascade must be on the store, covered by alerting, and passing the
validator.

## Gate 1 — Read-only sync

`ib_insync` connection. Account, positions, and marks into the store. **No order
capability in the code at all** — not disabled, not commented out, absent.

Worth building early regardless of whether you ever automate: it gives the
register live mark-to-market and turns the expectancy ledger from theoretical
into measured.

## Gate 2 — Paper

Orders to the IBKR paper account off Daily Cascade signals, full OCO brackets per
`execution-framework-v2`. **Minimum three months of dwell.**

The test is not whether it places orders correctly. It is whether realized paper
expectancy matches what the register predicted. If those diverge, the problem is
upstream in signal quality, and going live would only fund the discovery.

## Gate 3 — Live with approval

System stages orders; you approve each one from your phone. This gate exists to
surface the trades the rules produce that you would never have taken — and there
will be some.

## Gate 4 — Live automated

Non-negotiable constraints, all of them, before a single unattended order:

- **Instrument whitelist** — explicit, not a rule
- **Max position size** and max gross exposure
- **Max daily loss kill switch**, evaluated on every fill
- **Market-hours guard**
- **Staleness guard wired to the validator** — no orders on data that failed a
  check. This is where the Session 2 work pays off in a way that matters
- **Idempotent client order IDs** derived from `rec_id` + date, so a retry can
  never double-fill
- **Reconciliation loop** — broker positions vs. expected positions, halt on any
  mismatch
- **Dead-man switch** reachable from your phone, and tested

## Sequencing

Gate 1 slots naturally after the register (Part 7) — it is what makes the
register's P&L real. Gate 2 waits on the Daily Cascade prerequisite. Gates 3 and
4 should be separated by months, not sessions.

---

# Part 9 — FlashAlpha: working within Basic tier

## What you have

Basic covers GEX, DEX, VEX, CHEX per strike, key levels, all Greeks, IV, index
symbols (SPX, VIX), and the full 6,000+ equity and ETF universe. Rate limit is
either 100/day or 250/day depending on which FlashAlpha page you read — **check
your dashboard and design for 100.**

## What you do not have

| Feature | Tier | Implication |
|---|---|---|
| Historical replay (`historical.flashalpha.com`) | Alpha, $1,199–1,499/mo | **Build your own history instead — see Session 5** |
| Live flow GEX on effective OI | Growth | Your data is settled morning OI, frozen for the session |
| Flow-signed polarity | Growth | Sign convention stays an assumption |
| CME futures (ES, NQ, gold, crypto) | Growth | Use ETF proxies instead |
| 0DTE analytics suite | Growth | Email digest gives you 0DTE share; API does not |
| SVI vol surfaces, VRP | Alpha | Skip |

## The workarounds that matter

**History → build it.** Covered in Session 5. This is the single most important
adaptation, and it is free apart from the calls you are already making.

**CME futures → ETF proxies.** Gold and crypto dealer positioning is out of reach
via CME on Basic, but GLD, SLV, IBIT, USO and TLT are ordinary ETFs and fully
covered. You get the same read through the proxy, with a basis caveat. This feeds
`real-assets`, not just `sentiment`.

**Settled OI → say so.** Your snapshot is morning OI frozen for the session. That
is fine for a monthly report and a real limitation for intraday execution. Label
it in the output; do not let the narrative imply intraday freshness.

## Request budget at 100/day

| Cadence | Universe | Calls |
|---|---|---|
| Daily EOD | SPX, SPY, QQQ, IWM + 5 rotating single names | ~9 |
| Intraday (3×) | SPX, SPY | ~6 |
| Weekly sweep | Sector ETFs + GLD, SLV, IBIT, USO, TLT | ~10 (once) |
| **Typical day** | | **~15–17** |

The efficiency trick: the **summary endpoint returns GEX, DEX, VEX and CHEX in a
single call.** Never make four calls where one does. That budget leaves ~80%
headroom for ad-hoc work and retries.

## Upgrade triggers — so you do not pay early

- **Growth (~$239–299/mo)** is justified by the *execution* track, not the monthly
  report: intraday polling cadence, 0DTE analytics, flow-signed GEX, CME futures.
  That is a Gate 2 conversation (Part 8), not a v17 one.
- **Alpha (~$1,199–1,499/mo)** is justified only by backtesting depth — and by the
  time that matters, the Session 5 logger will have built you a year of your own
  history for free. Reassess then, not now.

## Correction to an earlier note

Two things in the v2 plan were wrong and are corrected here. First, "no report
produces dealer gamma data" — it arrives by email daily, it simply is not in the
store. Second, the Session 14 risk that FlashAlpha's API shape was unknown is
retired: there is a REST API, a Python SDK (`pip install flashalpha`), typed SDKs
in five languages, and an MCP server. The real constraint was never access. It is
tier.

---

# Part 10 — The AI theme: cross-cutting treatment

Currently the AI trade is covered in fragments across four pillars and nowhere as
a coherent whole. This is the fix.

## The mechanism: a theme view, not a twelfth pillar

The declarative registry already tags metrics to pillars. **Add a `themes:` field**
and render a cross-cutting section that assembles every metric tagged `ai`,
wherever it lives. No duplicated series, one place to read the whole trade.

```yaml
- id: NVDA_DSO
  pillar: credit
  themes: [ai]
```

The same mechanism serves future themes without further architecture.

## Five gaps, and where each lands

### 1. Pre-IPO and private marks — `real-assets`, Disruptive Themes

SpaceX, Anthropic, OpenAI, xAI, Databricks. More trackable than assumed:

- **N-PORT filings** — mutual funds holding private positions file marks
  quarterly. The most rigorous free source of private valuations.
- **Closed-end vehicles** — DXYZ, ARK Venture NAV and premium/discount to NAV.
  The premium is itself a sentiment read on private AI.
- **Secondary marketplaces** — Forge, EquityZen indicative pricing.
- **Tender offers and SPV rounds** — arrive through the events layer.

Builds on the existing SPCX analysis and the ASTS overhang tracker; makes it
systematic rather than ad hoc.

### 2. Chip demand — `internals`, Disruptive Themes

**The demand-side counterweight to a capex story built on announcements.**

- **Korea 20-day exports**, published three times monthly, semis broken out. Free,
  fast, and a genuine leading indicator.
- **TSMC monthly revenue** — monthly, free.
- SIA billings, ASML bookings, Taiwan export orders, HBM commentary.

### 3. Physical buildout — `real-assets`, `momentum`

- Data-center vacancy and absorption (CBRE, JLL, quarterly)
- **Power interconnect queue lengths** — the real constraint, and the one that
  turns a capex plan into a delivery date that slips
- Utility capex guidance; transformer and turbine lead times
- Already in plan: PJM/ERCOT power prices, uranium, DLR/EQIX

### 4. Labor impact — `labor`

**Under-built, and the two-sided question is measurable.** Construction,
electrical and technician employment rising while entry-level white-collar hiring
falls:

- BLS employment by sector and occupation
- Indeed postings by category (already Tier A)
- WARN notices, with AI-attributed filings tagged
- **Entry-level hiring rate** — the cleanest single series for the displacement
  side

No other part of the report does this analysis, and it is the part with the
broadest economic consequence.

### 5. Interdependence and circularity — Disruptive Themes, `credit`

**The standout gap. Nothing currently maps it.**

Chipmakers take stakes in customers who buy chips; hyperscalers fund labs that
buy their compute; vendor financing recycles revenue between a small number of
counterparties.

```sql
ai_deal_graph (deal_id, counterparty_a, counterparty_b, deal_type,
               announced_value, term, announced_date, circular_flag,
               source_url)
```

`deal_type`: equity stake, compute commitment, chip supply, revenue share,
vendor financing, capacity prepayment.

**The derived metric that matters: share of a company's revenue attributable to
counterparties it has invested in.** That single number is the cleanest available
tell for whether this is demand or financed demand — and it is the question the
whole AI trade turns on.

Pairs directly with the existing AI financing block in `credit` (hyperscaler
capex vs. operating cash flow, depreciation lengthening, NVDA DSO, neocloud
spreads, data-center ABS).

## Coverage by report

| Report | AI treatment |
|---|---|
| **Disruptive Themes** | Owns the structural thesis (Factor I), the deal graph, pre-IPO marks |
| **Monthly Macro** | AI theme view assembling tagged metrics; financing in `credit`, concentration in `internals`, buildout in `real-assets`, displacement in `labor` |
| **Top & Bottom** | Concentration & Complacency overlay (exists) |
| **Alternative Asset** | Uranium, power, data-center REITs, pre-IPO vehicles |
| **Weekend / Daily** | NVDA and SMH gamma, earnings dates, deal-announcement events |

## Sequencing

Most of this is registry tagging plus fetchers, not new architecture:

- **Session 2** — add the `themes:` field; tag existing AI metrics
- **Session 3** — Korea exports, TSMC revenue (~30 min, both trivial)
- **Session 8** — `ai_deal_graph` as an event-chain domain; deals are events with
  counterparties
- **Session 13/14** — theme view rendering; labor block
- **Deferred** — N-PORT parsing, CBRE/JLL, interconnect queues

**One caution.** This theme will attract more series than any other, because
everything looks AI-adjacent right now. The correlation guard and the annual
prune apply with full force here — tag a metric `ai` only when the AI read
actually changes because of it.

---

# Part 11 — Tracked entities: Brookfield

A named-entity tracker, built generically so it serves future counterparties too.

## Hard restriction — implement first

**No trade recommendations are generated for any instrument in the Brookfield
complex.** Diagnostic and strategic coverage only.

```yaml
# config/tracked_entities.yaml
brookfield:
  restricted: true          # register refuses recommendations
  instruments: [BN, BAM, BIP, BIPC, BEP, BEPC, BBU, BNT, BPYPP, BPYPO]
```

The register enforces this at write time — a recommendation tagged to a
restricted entity is rejected, not warned. Enforce it in code rather than in a
prompt: a narrative instruction is a suggestion, a schema constraint is a rule.
Any instrument added to the complex inherits the flag.

Rationale: Ari works within the structure (Argo → Clearbrook → Brookfield Wealth
Solutions → BAM). He has stated he will not trade Brookfield-related securities;
the restriction makes that structural rather than a matter of discipline.

## What to track

**The complex, not the ticker.** Stress surfaces in different vehicles at
different times, and BAM alone shows little.

| Instrument | Why |
|---|---|
| BN, BAM | Parent and manager; the FRE-vs-carry split lives here |
| BIP / BIPC, BEP / BEPC | Infrastructure and renewables — the AI-power adjacency |
| BBU, BNT | Business services, wealth solutions (Ari's own chain) |
| **Property preferreds** | **The canary — these moved hard during office stress while parent equity stayed calm** |

**Stress instruments, in order of usefulness:**

1. **Preferred prices and yields** on the property complex
2. **Credit spreads on Brookfield entity bonds** — for a leveraged manager this
   leads equity
3. **Discount to stated NAV** — BN publishes its own plan value; the gap measures
   how much the market disbelieves management's marks
4. **Fee-related earnings vs. carried interest** — FRE is the annuity, carry is
   cyclical; the mix shift shows which way the model is bending
5. **Fundraising pace, dry powder, realizations** — flywheel health
6. Short interest; BAM/BN options skew if they clear the liquidity floor

## Shareholder letters and strategic themes

Route through the `views` ingest (Session 14). Sources: Flatt's quarterly letter,
investor day materials, supplementals, and Oaktree's Marks memos — already on
that source list.

**Store structured themes, never the text:** what is emphasized, what has dropped
out since last quarter, where capital is being directed, which segments get
defended. **The quarter-over-quarter change in emphasis is the signal** — a theme
quietly disappearing from the letter says more than a theme being added.

## Rendering

- **Weekly news scan** — Brookfield-tagged events, preferred and credit moves,
  any stress flag
- **Monthly** — full entity block: performance across the complex, NAV discount,
  FRE/carry mix, fundraising, and the strategic-theme delta from the latest
  letter

Tag events `entity: brookfield` in the events layer so both surfaces filter from
one source.

## Build

- **Session 2** — `tracked_entities.yaml`; registry entries for the instruments
- **Session 5** — `restricted` enforcement in the register schema
- **Session 8** — entity tagging in the events classifier
- **Session 14** — letter and theme extraction via the views ingest
- **Deferred** — bond spreads and preferred yields if a free source proves
  awkward; start with equity and preferred prices, which are straightforward

The structure is generic. Adding a second tracked entity later is a YAML block.

---

# Part 12 — Crypto

Crypto is a core part of the trading approach, not one of eighteen alt assets.
This is the full treatment.

## Sources

**CoinGlass Hobbyist ($29/mo, personal use only).** Subscribe at Session 11, not
before — the Alt Asset pipeline is synthetic until then, and all-time daily
history comes with the tier, so nothing is lost by waiting.

*Verified:* aggregated liquidation history is on all tiers, 4h+ interval on
Hobbyist. *Confirmed absent:* the modelled liquidation heatmap is Professional
only ($699/mo) — do not upgrade for it. *Unverified, check day one:* the Indic
module endpoints (BTC vs M2, correlations, SOPR, Coinbase premium), and the
liquidation map / max-pain variants.

**Free supplements:**

| Source | Gives you |
|---|---|
| **DeFiLlama** | No key needed. TVL, stablecoin supply by chain, DEX volumes, bridge flows, yields. Best free crypto source there is, and covers on-chain structure CoinGlass does not |
| **Hyperliquid public API** | Whale positions without paying for Startup. Raw and awkward, fully public on-chain |
| **mempool.space** | Fees, hashrate, mempool depth |
| **CME public settlement** | Basis calculation for metric 2 below |
| **Dune free tier** | ETF flow cross-check |

*Skip:* Farside (bot-blocked), Glassnode free tier (too limited to matter).

## The eight metrics

1. **Leverage regime composite — the heatmap substitute.** Aggregated OI +
   OI-weighted funding + top-trader position ratio + realized liquidation
   asymmetry into one read: how much forced flow is latent and which side it sits
   on. Not as good as the modelled heatmap; answers the same question. The direct
   analogue of dealer cushion.
2. **Funding-versus-basis carry spread.** Perp funding against CME basis and
   borrow rates. Funding well above basis is speculative leverage rather than
   institutional carry — separates retail froth from the basis trade. Few people
   construct this.
3. **Coin-margin vs. stablecoin-margin OI share.** Coin-margined positions are
   structurally reflexive: collateral falls with price, so liquidations cascade
   harder. Rising coin-margin share is a fragility signal. CoinGlass splits these
   in the aggregated OI endpoints.
4. **Two-bid decomposition — reuse the gold framing directly.** Structural bid:
   ETF flows, exchange balance drawdown, long-term-holder supply. Speculative
   bid: OI, funding, taker skew. Divergence is the signal. The apparatus already
   exists in `real-assets`.
5. **Exchange OI concentration (Herfindahl).** Venue-level twin of options OI
   concentration; concentration means single-venue failure risk.
6. **Spot vs. futures CVD divergence.** Spot CVD rising while futures CVD is flat
   = real accumulation rather than leveraged chase. The quality-of-bid question,
   answered directly.
7. **Liquidation asymmetry, percentile-ranked.** Long vs. short liquidation
   dollars over rolling windows. Directional spikes mark capitulation and squeeze
   exhaustion.
8. **Pre-computed, otherwise self-built:** BTC vs. US M2 growth (this *is* the
   BTC-vs-net-liquidity metric), BTC correlations to SPY/GLD/TLT/QQQ, LTH/STH
   SOPR and realized price, Coinbase premium, options-to-futures OI ratio.

**Discipline: the cycle indicators are conditioners, never triggers.** AHR999,
Puell, Pi Cycle, RHODL, 200-week heatmap, Bull Market Peak are calibrated on
three or four cycles — effective n under five. Set `trigger_eligible: false` on
all of them. They are the crypto equivalent of a CAPE threshold binary.

## Weekly commentator scan — Weekend Synthesis

Routes through the `views` ingest with crypto-specific sources. **Store the
structured call, never the prose:** who said what, at what level, with what
conviction, and whether it changed from their prior.

**The signal is who changed their mind, not who is loudest.** A persistent bull
turning cautious is information; a permabull repeating themselves is not. Track
`changed_from_prior` and surface only the deltas.

Pair with the week's events so the scan explains what happened rather than
listing opinions about it.

## Running forecast — 12 months, 3 years, 5 years

Held in Weekend Synthesis, revised on evidence rather than on schedule.

```sql
crypto_forecast (vintage_date, horizon, asset, low, base, high,
                 probabilities, drivers_json, changed_from_prior, rationale)
```

**Four rules that keep this from becoming untestable narrative:**

1. **Ranges with probabilities, never point estimates.** A point estimate at
   three years is theatre.
2. **Every horizon names its drivers, and each driver maps to a tracked series.**
   The forecast is then a function of things you measure, not a mood. When a
   driver moves, you know whether the forecast should.
3. **Vintage-stored, like everything else.** Chart how the 12-month range has
   moved over time. **The path of the forecast is more informative than its
   current level** — a range that drifts with spot is following price, not
   forecasting it, and the vintage record is the only way to catch that.
4. **Form the new estimate from drivers before looking at the prior.** Same
   anchoring problem as the Section 0 scorecard: seeing your last forecast biases
   the update toward it. Derive, then compare, then log the delta and why.

**Grade by horizon, honestly:**

- **12 months** — gradeable within the system's life. Goes in `predicates` and
  gets scored like anything else.
- **3 and 5 years** — not gradeable on any useful timescale. **Treat them as
  scenario frames rather than forecasts**, and grade the *drivers* instead: did
  the adoption, regulatory, and liquidity conditions the scenario assumed
  actually materialize? That is answerable in twelve months even when the price
  call is not.

## Where crypto renders

| Report | Content |
|---|---|
| **Daily Cascade** | Funding, OI, liquidation asymmetry, leverage regime composite — same slot as the gamma read |
| **Weekend Synthesis** | Positioning reset, whether leverage rebuilt over the week, commentator scan, forecast review |
| **Monthly `real-assets`** | Two-bid decomposition, BTC vs. M2, correlations, structural flows |
| **Alternative Asset** | Full asset-level deep dive |

## Build

- **Session 11** — CoinGlass fetcher, DeFiLlama, metrics 1–8 into the registry
- **Session 12** — `real-assets` rendering, two-bid decomposition
- **Session 14** — crypto sources into the views ingest
- **Deferred** — Hyperliquid public API for whale positions; mempool.space

---

# Part 13 — Disruptive Themes: Factor V, Monetary Architecture in Transition

**On the name.** Not "crypto." The existing factors are *forces* — AI maturation,
valuation, geopolitical confrontation, the dollar/debt complex. An asset class
sitting alongside those is a category error, and it would bias the analysis
toward price. The force is the transition in monetary architecture; crypto,
stablecoins, CBDCs, tokenization and the debasement trade are its expressions.

Quarterly cadence, structural horizon. **This section is about regime, not
price** — price lives in `real-assets` and the Alternative Asset report.

## The four structural questions

Everything below serves one of these. If a metric answers none of them, it
belongs in the monthly report instead.

1. **Is crypto becoming monetary infrastructure, or staying a speculative asset
   class?** Stablecoin settlement volume and Treasury holdings argue
   infrastructure; perp OI and funding argue asset class. Both are true at once;
   the *mix* is the regime.
2. **Does the debasement thesis get expressed in gold or in bitcoin?** They
   compete for the same flow. Relative share is measurable and it moves.
3. **Is the leverage structure becoming more or less reflexive?** Coin-margin
   share, DAT company leverage, restaking depth.
4. **Does Bitcoin's security budget work at scale?** The longest-horizon question
   and the one nobody prices.

## A. Monetary architecture

- **Stablecoins as Treasury demand.** Already central to the Treasury financing
  chain in Session 8 — issuers as the marginal bill buyer. Track aggregate
  supply, issuer reserve composition from attestations, and share of T-bill
  market. **This is the single most important crypto-macro linkage in the
  system**, and it runs through `sovereign`, not `real-assets`.
- **Stablecoin dollarization in EM.** Supply growth by chain and region as a
  capital-flight and shadow-dollarization channel. Connects to `global`.
- **Tokenized Treasuries and money funds.** BUIDL and peers — AUM, issuer mix,
  yield vs. TradFi equivalents.
- **CBDC vs. private stablecoin.** Policy direction by jurisdiction; treat as an
  event-chain rather than a series.
- **Regulatory perimeter.** Stablecoin reserve requirements, issuer licensing,
  bank custody permissions. Each becomes a dated calendar item.

## B. Institutional plumbing

- ETF structural flows and AUM; ETF options open interest as the institutional
  hedging read
- **Corporate treasury holders and their financing.** MSTR and imitators are a
  *credit* story: convertible maturities, ATM issuance, mNAV premium/discount.
  A DAT company trading below NAV with converts maturing is a forced-seller
  setup. Route to `credit`, not `real-assets`
- Custody, prime brokerage, and bank access changes
- Basis-trade capacity — CME OI and basis level as the institutional carry gauge
- Allocation policy: pension, endowment, sovereign wealth disclosures

## C. Technology and protocol economics

- **ETH staking yield as the crypto risk-free rate.** The discount rate for the
  whole space, and almost nobody frames it that way. Track against Treasury real
  yields — the spread is the risk premium for the asset class
- L2 fee capture and economics; sequencer revenue
- **Restaking depth** — leverage layered on staking, the DeFi analogue of
  rehypothecation
- **Bitcoin security budget.** Fee revenue vs. block subsidy across halvings. If
  fees do not scale, security degrades on a decade horizon. Structural, unpriced,
  and exactly what a quarterly report should carry
- Quantum exposure — long-dated, low probability, non-zero, worth a standing line

## D. Reflexivity and leverage structure

- Miner economics: hashprice, cost curves, capitulation signals, treasury sales
- Coin-margin vs. stablecoin-margin OI share (Part 12, metric 3)
- DAT company leverage and mNAV
- Perp market structure: funding regime, OI concentration by venue

## E. Geopolitical and energy

- Nation-state holdings and strategic reserve policy
- Sanctions evasion and enforcement actions
- **Mining geography and power politics — and the direct link to Factor I.**
  Miners and AI data centers compete for the same interconnect queues, the same
  power contracts, and increasingly the same sites. Several miners have converted
  to AI hosting. **This is the concrete bridge between Factor I and Factor V**,
  and it is measurable through interconnect queues, PPA announcements, and miner
  revenue mix
- Tax treatment changes by jurisdiction

## F. Cross-asset competition

- **Gold vs. BTC share of the debasement trade.** Both two-bid decompositions
  already exist (Parts 12 and the `real-assets` design); compare the
  *speculative* bid in each. Flow rotating between them is the signal
- Crypto vs. AI equities as the retail risk-appetite outlet — correlation and
  relative flow
- Correlation regime with equities and net liquidity: is crypto trading as
  liquidity beta or as a debasement hedge this quarter? The answer changes, and
  naming it is the pillar's job

## G. Adoption ledger — the tailwinds and headwinds that decide the thesis

Sections A–F describe the current state. **This one tracks what would change it.**
Structured as a standing ledger, not prose, so items persist across quarters and
get graded rather than forgotten.

```sql
adoption_factors (factor_id, direction, category, description,
                  status, evidence_series, first_logged, last_moved,
                  probability_band, time_horizon)
```

`direction`: tailwind / headwind. `status`: emerging / building / stalled /
resolved. Every factor names the evidence that would move it.

### Security — the headwind that compounds quietly

- **Protocol and bridge exploits.** Dollar value and count by quarter, and
  critically *whether losses are trending down as a share of TVL*. A maturing
  system loses less per dollar secured; a fragile one does not
- **Custody and exchange failures.** Proof-of-reserves adoption, auditor quality,
  insurance capacity
- **Smart contract risk in the restaking stack** — layered leverage means a
  single exploit propagates
- **Stablecoin depeg events**, including near-misses. Depegs are the fastest path
  from crypto stress to the Treasury market given the reserve linkage
- **Consensus-level incidents** — reorgs, client bugs, validator concentration

### Quantum — long-dated, low probability, non-zero

The right posture is neither dismissal nor alarm. Track the timeline, not the
threat.

- Logical qubit counts and error-correction milestones from the major programs
- **NIST post-quantum standard adoption in the protocols themselves** — this is
  the real series. The threat is bounded by migration speed, not by qubit count
- Estimated vulnerable supply — coins in address types exposed to a public-key
  attack, which is a computable number
- Migration proposals and their governance status

**The tell to watch is the gap** between capability milestones and protocol
migration progress. A widening gap is the headwind; a closing one retires it.
Set `probability_band` explicitly and revise it only on milestone evidence, never
on commentary.

### Emerging use cases — the tailwinds

Track adoption metrics, not announcements. **A partnership press release is not
a use case; settlement volume is.**

- **Payments and settlement** — stablecoin transaction volume net of exchange
  flow, merchant and remittance corridors, B2B settlement
- **Tokenized real-world assets** — Treasuries, credit, funds, private markets.
  AUM and issuer mix
- **Collateral use** — crypto accepted as collateral in TradFi repo and lending
- **Prediction markets** — already relevant to your election tracking, and one of
  the few consumer use cases with genuine product-market fit
- **Machine-to-machine and agent payments** — the direct Factor I bridge, and
  early enough that the signal is developer activity rather than volume
- **Privacy tooling** under regulatory pressure — adoption vs. enforcement

### Sovereign gold reserves — flows and one ratio, never levels

**Levels are close to useless here.** The US at ~8,133 tonnes has been static
since roughly 1971; Germany, Italy and France are similarly legacy Bretton Woods
positions rather than decisions. Ranking them is a history lesson. The countries
that carry information are the dynamic ones — China, Russia, Poland, Turkey,
India.

**Three constructions:**

1. **Quarterly net purchases by country.** The aggregate already feeds the
   official bid in `real-assets`; what this adds is the **composition**. Buying
   concentrated in sanctioned or sanction-exposed economies is a
   reserve-diversification story. Broad-based buying including allied central
   banks is a debasement story. **Same aggregate tonnage, entirely different
   regime** — and only the country split distinguishes them.
2. **Gold as a share of total reserves — the ratio that matters.** Poland at 582
   tonnes means little; Poland moving from single digits toward 20% of reserves
   is a stated policy shift. It also sizes the remaining runway: China near 2,300
   tonnes sits under 10% of reserves against 70%+ for the US and Germany. **That
   convergence gap is the structural bid, and it is computable rather than
   speculative.**
3. **Reported vs. estimated holdings.** China reports in irregular chunks and
   market estimates run above official figures. The gap is itself a signal about
   willingness to disclose.

**Data caution:** IMF IFS reporting lags and is voluntary, so a labelled quarter
is not a single date across countries. **Tag as-of per country** — precisely what
the staleness rules exist for.

**Cadence and placement:** quarterly and structural, so it lives here in Factor V
as sovereign reserve behaviour. Only the aggregate flows to the monthly
`real-assets` official bid. Not in weekly or daily — nothing at those horizons
turns on it.

Sources: IMF IFS and World Gold Council, both free. ~30 minutes.

### Regulatory — cuts both ways, so track direction not sentiment

Market structure legislation, accounting treatment, bank capital rules, ETF
approvals for new assets, tax treatment, and enforcement posture. Each entry
carries a jurisdiction and a dated milestone into the forward calendar.

### The discipline that makes this useful

**Every factor gets a falsification condition and a review date when it is
logged.** Without that, the ledger becomes a list of things that sound important
and never resolve — which is the failure mode of every "risks and opportunities"
section ever written.

The quarterly review asks only two questions per factor: *did the evidence move?*
and *should the probability band change?* Items that have not moved in four
quarters get archived rather than restated.

## Output

Factor V writes `disruptive_themes_regime` with a crypto component, on the same
60-day persistence as the rest of Themes. The regime label answers question 1:
**infrastructure-leaning, asset-leaning, or contested.**

It also feeds the 3- and 5-year scenario frames in Weekend Synthesis (Part 12) —
those scenarios' *drivers* are drawn from this section, which is what makes them
gradeable when the price call is not.

## Build

- **Session 23** (Disruptive Themes spine hook, v17.5) — Factor V scaffold and
  the regime field
- **Session 11–12** — the series that feed it, most already in Part 12
- **Deferred** — security budget modelling, restaking depth, tokenized-Treasury
  AUM tracking

**One discipline note.** This section will attract more content than any other in
Themes, because crypto generates enormous commentary volume. The four structural
questions are the filter: **if a metric does not move an answer to one of them,
it goes in the monthly report instead.**

---

# Part 13b — Disruptive Themes: format retention

**Ruling: the existing report's structure is retained wholesale.** All new
material from Parts 13, 16, 19 slots *into* it. The pipeline builds to this
template, not to the prototype's simplified one.

## Retained verbatim from the existing report

- **Per-factor structured object:** Thesis → Mechanism → Impact → Timing →
  Indicators → **What would prove this wrong** → WEF cross-reference
- **Composite risk score**, −2.0 to +2.0, with the existing bands: NEUTRAL
  (+0.5 to −0.5) · OVEREXTENDED (−0.5 to −1.2) · TOP SIGNAL (below −1.2) ·
  BOTTOM WATCH (rising into positive). Prior runs: −1.0 both May and June.
- **Three external calibration lenses:** WEF cross-reference, Dalio Lens,
  five-tier Broader Calibration Panel
- **Bull case steelman** — this *is* the adversarial function of Part 14,
  already native to the report
- **"What would change my mind" — 3–5 lowering AND 3–5 raising.** Both
  directions, always
- **Calibration check** — has the framework signaled alert for quarters without
  a correction? (It has: OVEREXTENDED since at least May)
- **Broad Media Scan** — retained, and formally connected to the coverage-gap
  scan (Session 15c): the scan's unmapped themes feed the same
  `coverage_gaps` table. *Convergence note: the June scan's three blind spots —
  stablecoins/dollarization, power-grid constraints, AI labor displacement —
  are now Factor V, the buildout block, and the labor block.*
- **Format:** React JSX artifact, navy #0f2747 accordions via native HTML5
  details/summary (the iOS fix), Georgia serif, no colored callouts, component
  vocabulary (Section, Sub, Lead, P, B, Pull, CurrentRead, List, KV, Table,
  Quote), JSX→HTML transformer for desktop, Master Refresh Prompt as appendix
- **Cadence:** every two months + event-driven, trigger phrase "run the refresh"

## Where the new material slots in

| New element | Slot |
|---|---|
| Factor V — Monetary Architecture (Part 13) | Fifth factor object, same structure |
| Premise expiry (`premise_event`, `premise_expiry`) | New field on every factor header |
| "What would prove this wrong" | Maps to kill conditions — same concept, keep the report's wording |
| Tech discontinuity theses (Part 19) | New section beside the calibration lenses |
| Tail assessment deltas (Part 16b extract) | New section, deltas only |
| Adoption ledger movers | Inside Factor V |
| Tail scenario appendix (Part 16c) | Report appendix, beside the Master Refresh Prompt |
| Data gaps register | Appendix, until empty |
| Chokepoint cluster + disruption-price divergence | Factor III indicators |

## Facts the next real run inherits from the June 11 baseline

Composite −1.0 OVEREXTENDED (unchanged across two runs). Factor III had
*improved* in June (ceasefire holding, Brent $86 off the $138 February peak) —
the August premise collapse reverses that, which is exactly what the premise-
expiry field now records. Factor IV was intensifying: May PPI 6.5% (four-year
high), rate-hike pricing emerging, Warsh's first FOMC then imminent. AI capex
$660–770B for 2026 with debt funding accelerating. CAPE ~40.75–41.6. **The
prototype's PPI omission matters: a four-year-high PPI print belongs in the
commodity pass-through and inflation-reacceleration (scenario 16) readings.**

---

# Part 13c — Two cross-report rules carried from the cadence work

**Options output reconciliation.** Monthly Appendix C is *pedagogical* —
illustrative defined-risk structures that teach how a view would be expressed.
Top & Bottom Appendix D is *engineered* — sized portfolios meant to be acted on.
They serve different purposes and must never contradict: if Appendix C illustrates
a bearish expression while Appendix D holds a bullish book, one of them is wrong,
and the conflict-detection rule applies. State the distinction in both appendices.

**Weakest-link disclosure, generalized.** Originally an Alternative Asset
requirement: the report names its least-trusted input explicitly. **Every report
now does this** — one line in the appendix naming the series or section the
reader should trust least and why. Same spirit as the gaps register, applied to
what *is* built rather than what is not.

**Artifacts to preserve from that chat before it is deleted:** Master Narrative
v1.4 (superseded by the system-narrative document, but the lineage is worth
keeping) and **Translation Table v2.3** — the mapping of each report's score onto
a common risk scale, which the precedence rules do not replace. Commit both to
`docs/` first.

---

# Part 14 — The review protocol

**Calendar item added 3 Sep 2026, downgraded by Part 25:** the fine-grained
GitHub PAT behind cron-job.org expires ~May 2027 and fails silently. Under the
VPS ruling (Part 25) cron-job.org is retired and this matters **only if the
Actions fallback is kept alive** — keep an April 2027 reminder until the VPS
migration is proven, then drop it.

The feedback loops are built into the system. **This is the discipline layer that
makes sure they get read.** Four cadences, each with a written agenda and a stored
output — a review that produces no artifact did not happen.

All outputs go to `calibration_log` with a date and a rationale.

## Monthly — 30 minutes

**Input:** the cross-report reflection artifact, generated automatically.

1. Numbers: any figure wrong against the vintage that existed at publication?
2. Claims: any causal assertion without a matching event record?
3. **Hedging share** — what fraction of claims were falsifiable at all? Trend it.
4. What resolved: predicates, swing theses, chain expectations.
5. Fix what it flags. Log anything changed.

**One question to answer in writing each month:** *what did the report say that I
would not have said myself?* If the answer is "nothing" for three months running,
the system is an expensive mirror.

## Quarterly — 4 hours

**Tier 1 and 2 calibration only.** Signal weighting stays locked until year three
(Finding 4).

1. Predicate hit rate — overall, by pillar, trailing twelve months
2. **Threshold pruning** — any predicate firing >90% or <10% of the time is not a
   watch item. Re-set on distributional grounds, not on outcome
3. Coverage-gap cluster list — each recurring gap becomes a registry entry or is
   **declined with a written reason**
4. Anticipated-surprise share — did the forward layer point at the month's biggest
   moves?
5. Correlation guard — re-run against any metric added this quarter
6. Factor V adoption ledger — did evidence move? Archive anything static for four
   quarters
7. Crypto forecast — derive from drivers *first*, then compare to prior
8. Prompt edits, with before/after on the hedging and falsifiability metrics

## Semiannual — 2 hours

**Architecture and adversarial review.**

1. Model upgrade evaluation — re-run the prior month on old and new, diff, decide
   deliberately at a version boundary
2. Schema review — what does the registry need that it cannot express?
3. **What broke, and what silently did not run?**
4. **What is unused?** Any series that has never changed a pillar score, any
   report section never referenced in a decision
5. Cost review — API spend, subscriptions, hours against value

### The adversarial session — the part a solo operator has to manufacture

A desk has a risk manager whose job is to say you are wrong, and colleagues with
different books arguing back. **Every loop in this system is self-administered:
you set the thresholds, you grade the results, you decide what to prune.** That is
the structural weakness, and it does not fix itself.

Twice a year, spend an hour arguing the other side in writing:

- **Steelman the opposite of your current regime read.** Not caveats — the actual
  best case against.
- **Which of my metrics would a skeptic call overfitted?** Name three.
- **Where am I confusing a mechanism I understand with an edge I have?**
- **What would I have to see to abandon the framework entirely?**
- **What has the system told me that I overrode — and was I right to?**

Bring the output to a session with an AI or a colleague explicitly instructed to
argue against it. Store the result.

## Annual — 3 hours

1. **Registry prune.** Which series never moved a read? Cut them. Systems like this
   accrete metrics and never shed them, and the report gets longer and less useful
   every year
2. Horizon review — expectancy by horizon; is the swing book earning its time?
3. Confidence calibration — does stated conviction match realized frequency?
4. **System vs. discretionary** — the uncomfortable one
5. **The strategic question, answered in writing:** given the hours this costs, is
   it worth continuing in its current form? What would I build differently now?

## First-run review — after the first complete monthly cycle

Do not wait for the quarterly. After the first full v17 run: what broke, what was
wrong, what was unreadable, what did you skip reading and why. That last one is
the most informative and the easiest to skip.

---

# Part 15 — The edge layer: expectation, consensus, and divergence

**The gap this closes.** Everything else in this system answers *what is true*.
Almost nothing answers *what is mispriced*. Those diverge constantly — the report
can be right that credit is deteriorating and lose money, because the market
already knew. This part is the difference between an information system and an
edge.

Total cost is roughly 4 hours across existing sessions, because most of the data
is already being pulled for other reasons.

## A. Expectation vs. outcome

### The table — Session 5

```sql
expectations (series_id, release_date, expected, expected_source,
              realized, surprise, surprise_z, vintage_date)
```

`surprise_z` standardizes against that series' own historical surprise
distribution, so a 0.1% CPI miss and a 50K payroll miss are comparable.

### Where expectations come from — most already in the plan

| Domain | Expectation source | Status |
|---|---|---|
| GDP | Atlanta Fed GDPNow | **v17.5 — reframe as the baseline** |
| Inflation | Cleveland Fed nowcast | **v17.5 — same** |
| Activity | NY Fed WEI | **v17.5 — same** |
| Longer-horizon macro | Philadelphia Fed SPF (quarterly, free, survey-based) | New, trivial |
| Fed policy | `policy_path` prior vintage vs. realized | **Already built — free** |
| Treasury supply | When-issued vs. awarded yield = the tail | **v17.5 auction results** |
| Earnings | Forward EPS revisions | **Session 13 Silverblatt** |
| Inflation expectations | Breakevens vs. realized CPI | **Already have both** |
| Event risk | ATM straddle implied move vs. realized | **Session −1 logger** |

**The nowcasts change role rather than get added.** They were elevated in v17.5 as
fresher data. They are more valuable as the *expectation baseline* against which
realized prints are measured. Same fetcher, different use.

### Derived metrics — Session 2 registry

1. **Pillar surprise index** — rolling standardized surprise per pillar. The
   report stops saying "labor is cooling" and starts saying "labor is cooling
   faster than priced," which is a trade rather than an observation.
2. **Surprise vs. price response** — *the sharpest one.* Did the market move as
   much as the surprise implies? Systematic under-response is where edge lives;
   over-response is where fading lives. Requires the path-aware sampling from
   Session 3a, which you already have.
3. **Policy path revision** — the monetary surprise, free from the existing
   vintage table.
4. **Auction tail** — the supply/demand surprise.
5. **Implied vs. realized around events** — the event risk premium.

## B. Consensus and divergence

**The second gap: the report has no explicit view of what the market believes.**
Prices are consensus; the report tracks prices without ever naming the narrative
it would be betting against.

### Per-pillar requirement — Sessions 4 and 12

Each pillar renders three lines, and the prompt requires all three:

- **Consensus** — what the market prices and what desks are saying. Sourced from
  the views ingest, priced expectations (policy path, breakevens, forwards), and
  positioning (COT, AAII/NAAIM, put/call — v19)
- **Our read**
- **The difference, and what it rests on** — or an explicit statement that there
  is none

Add `consensus_source` to each pillar's config so this is mechanical rather than
improvised.

### The guard — this matters more than the feature

**Forcing a divergence statement risks manufacturing contrarianism.** "We agree
with consensus" must be a valid, unpenalized answer, and the pillar prompt should
say so explicitly.

Track **divergence rate** — the share of pillars where the read differs from
consensus. Diverging everywhere is posturing; diverging nowhere means the report
is a well-organized summary. Neither extreme is a healthy reading, and the trend
matters more than the level.

## C. The grading change — where this pays off

**Split every predicate and recommendation by whether it agreed with consensus at
the time.** Add `vs_consensus: agree | diverge | n/a` to `predicates` and
`recommendations`, set at creation.

Then grade separately:

- **Consensus-agreeing hits earn nothing.** Being right alongside everyone is
  already in the price.
- **Divergent hits are the actual edge measure**, and divergent misses are the
  real cost of the framework.

**This is the single most informative number the system can produce about
itself**, and nothing currently measures it. A 70% overall hit rate composed
entirely of consensus agreement is a 0% edge. A 45% hit rate on divergent calls
with good payoff asymmetry may be a business.

## Build

- **Session 2** — surprise metrics into the registry
- **Session 4** — the three-line consensus requirement in the pillar prompt, plus
  the explicit permission to agree
- **Session 5** — `expectations` table; `vs_consensus` on predicates and
  recommendations
- **Session 12** — `consensus_source` per pillar in `pillars.yaml`
- **Session 15b/c** — divergence-split grading, divergence rate tracking
- **v17.5** — SPF added alongside the nowcasts

**One caution.** This layer will make the report harder to write and easier to be
wrong in public. That is the point. A report that never states what it believes
the market has missed cannot be graded on anything that matters.

---

# Part 16 — The tail watch table

**The point is not the scenario list.** Anything on a list is priceable; the real
tail is absent from any list we could write. The value is that **each scenario has
a named first-mover series with a threshold**, checked mechanically every run. It
converts speculation about what could happen into a tripwire that fires without
anyone remembering to look.

## Schema — Session 5

```sql
tail_watch (scenario_id, name, category, first_mover_series,
            threshold, direction, confirming_series, cadence,
            owning_report, status, last_fired, notes)
```

`status`: dormant / elevated / triggered. `cadence` sets how often the check
runs, which is set by **how fast the scenario would move**, not by how important
it is.

## The table

### Tier A — daily checks, Daily Cascade

Fast-moving, and the report would be wrong within hours if it missed them.

| # | Scenario | First mover | Also watch |
|---|---|---|---|
| 1 | **Funding-market accident** | SOFR–IORB spread | SRF usage, repo fails, reserves < $2.8T |
| 2 | **Yen carry unwind** | USD/JPY `path_divergence` | JGB 30y, cross-asset correlation spike |
| 7 | **Hormuz / energy shock** | WTI and Brent intraday range | Curve shape, breakevens |
| 19 | **LDI-style forced deleveraging** | Long-end realized vol | Term premium spike, correlation spike |
| 20 | **Index concentration accident** | Single-name gamma on top-10 | Top-10 weight, implied correlation |

### Tier B — weekly checks, Weekend Synthesis

| # | Scenario | First mover | Also watch |
|---|---|---|---|
| 3 | **AI capex halt** | NVDA inventory, purchase commitments | Hyperscaler capex/OCF, Korea 20-day exports |
| 4 | **Stablecoin depeg at scale** | Aggregate stablecoin supply | Issuer attestations, bill yields |
| 5 | **European sovereign fragmentation** | OAT–Bund, BTP–Bund | ECB commentary, Euribor–OIS |
| 6 | **Private credit mark event** | BDC price-to-NAV | CCC OAS, PIK share |
| 9 | **Failed Treasury auction** | Auction tails, indirect share | Term premium, bill share of issuance |
| 14 | **CRE credit cascade** | CMBS OAS by tier | KRE skew, bank CRE delinquencies |

### Tier C — monthly checks, Monthly Macro

| # | Scenario | First mover | Also watch |
|---|---|---|---|
| 10 | **Fed independence** | Breakevens vs. term premium divergence | DXY, gold paper bid |
| 11 | **Japanese repatriation** | TIC Japan holdings | JGB 30y, hedged-yield spreads |
| 12 | **China property / LGFV event** | CNY, copper/gold | China export prices |
| 15 | **EM debt crisis + dollar squeeze** | EM sovereign OAS | DXY path, cross-currency basis |
| 16 | **Inflation reacceleration forcing hikes** | Sticky core CPI | 5y5y, policy path dispersion |
| 17 | **Insurance / reinsurance capital event** | Cat bond spreads | Reinsurer equity, renewal pricing |

**On 16:** the report is *least* positioned for this one, because the entire
framework currently assumes a disinflation path. That asymmetry is a reason to
watch it more closely, not less.

**On 17:** tracked through public market instruments — cat bond spread indices,
reinsurer equity, published renewal pricing — so it runs on the same footing as
every other line here and requires no personal judgement to populate.

### Tier D — quarterly, Disruptive Themes

| # | Scenario | First mover | Also watch |
|---|---|---|---|
| 8 | **Taiwan** | Taiwan export orders | TSMC revenue, SMH, shipping and insurance rates |
| 18 | **Cryptographic break in settlement** | Post-quantum migration progress vs. capability milestones | Custody and clearing standards adoption |

### Tier E — market-structure failures (21–25)

**A distinct category worth naming.** Scenarios 1–20 are mostly shocks to the
world. These five are failures of a **price-insensitive buyer** — sovereign funds,
passive flows, stablecoin issuers, IG mandates, ETF authorized participants.
Arguably the more dangerous class, because standard macro indicators say nothing
about them and the withdrawal is mechanical rather than sentiment-driven: it does
not reverse when things look cheap.

| # | Scenario | First mover | Also watch | Cadence |
|---|---|---|---|---|
| 21 | **Sovereign wealth forced selling** | Oil vs. Gulf fiscal breakevens | SWF disclosure changes, sovereign fund AUM | Monthly (C) |
| 22 | **Passive-flow reversal** | ICI weekly flows | Net passive creation, retirement-account net flows | Monthly (C) |
| 23 | **Stablecoin regulatory reversal** | Legislative and rulemaking calendar | Issuer reserve composition, bill holdings | Weekly (B) |
| 24 | **BBB downgrade cascade** | BBB share of IG | Ratings-action counts, BBB–BB spread | Monthly (C) |
| 25 | **ETF wrapper liquidity failure** | HYG / JNK premium-discount to NAV | Creation-redemption activity, underlying vs. wrapper spread | Weekly (B) |

**On 23:** this is the mirror of scenario 4. Not a depeg — a rule change forcing
issuers to divest reserves or restricting issuance. If issuers are the marginal
bill buyer the Treasury chain assumes, a regulatory reversal removes that bid
directly.

**On 24:** roughly half of investment grade sits at BBB, and downgrade to high
yield triggers mandate-driven forced selling. Structurally the same mechanism as
the CCC dissent already in `credit`, at far larger notional.

**On 25:** the tell is premium-to-NAV dislocation in less liquid underlyings —
high yield, bank loans, EM debt. It **precedes** the price break rather than
following it, which is what makes it worth watching rather than merely observing.

### RECONCILIATION REQUIRED — an existing Tail Scan component

**Part 16 was written without knowledge that a Tail Scan already exists**, with
domains for pandemic, nuclear, terror and cyber. **Do not run both.** First task
on Monday, before Session −1:

1. Inventory what Tail Scan actually covers and at what cadence
2. Map the 25 scenarios here onto its existing domains; most will fit
3. **Scenario 13 (cyberattack) is likely already instrumented** — I flagged it as
   an un-instrumented blind spot, which may simply be wrong
4. Add the missing domain from the methodology work: **commodity chokepoint /
   supply corridor** — Hormuz, Suez/Bab el-Mandeb, Panama draft, Taiwan Strait,
   each with transit counts, war-risk premium and affected commodity complex
5. Keep the structure generic so the domain persists after any single crisis
   resolves — not a bespoke Hormuz tracker

### CORRECTION — scenario 7 is mis-specified

Scenario 7 is listed as a dormant tail risk. **It is a current condition.** The
strait has been effectively shut for roughly six months, PortWatch recorded 3
transits on 23 Aug 2026 against an ~85/day pre-crisis baseline, and Gulf exports
are down roughly 47%. Brent is near $89.

**The tail is not the closure. The tail is the divergence closing.** Re-specify:

| | Old (wrong) | Corrected |
|---|---|---|
| Scenario | Hormuz closes | **Disruption–price divergence resolves violently** |
| First mover | WTI/Brent intraday range | **PortWatch transits ÷ baseline, against Brent** |
| Also watch | Curve, breakevens | War-risk premium, freight rates, spare capacity |

Two readings, and the metric's job is to force a choice rather than assume one:
**adaptation** (shadow fleet, dark transits, pipeline routing, demand destruction
have genuinely absorbed it) or **mispricing** (a chokepoint that has failed twice
in six months is being underwritten at a normalised premium). If the gap persists
another two quarters, adaptation strengthens and the chokepoint's weight should
be cut. **Write the resolution down either way.**

### Under-instrumented — acknowledge rather than fake

| # | Scenario | Why |
|---|---|---|
| 13 | **Cyberattack on financial infrastructure** | Settlement stops *before* prices move, so price-based indicators fail by construction. No adequate free leading series exists. **Log it as a known blind spot rather than attaching a weak proxy.** |

## Rules

1. **Cadence follows speed, not importance.** Taiwan is higher impact than a
   BDC discount and gets checked far less often, because the first-mover series
   only updates quarterly.
2. **Every row names a series that already exists in the plan.** No row is added
   without one. A scenario with no tripwire is commentary.
3. **`elevated` is a state, not a call.** A tripwire firing changes the report's
   language and tightens the relevant predicate. It does not generate a trade —
   that runs through the register, sized by the normal rules.
4. **All twenty are conditioners.** `trigger_eligible: false` throughout. These
   are low-probability scenarios with effective n of roughly zero; treating a
   tripwire as a signal would be the worst overfitting in the system.
5. **Review quarterly**, in the calibration session: which fired, which fired
   falsely, which scenario has become ordinary enough to retire, what belongs on
   the list that is not.
6. **Keep the blind-spot list visible.** Item 13 stays on the table with no
   tripwire, so the gap is documented rather than forgotten.

## Build

- **Session 5** — the `tail_watch` table
- **Session 15c** — the check runs each cycle and writes status
- **Rendering** — Tier A into the Daily 7AM block, Tier B and E-weekly into
  Weekend Synthesis, Tier C and E-monthly into the Monthly front matter beside
  Month in Events, Tier D into Themes
- **Deferred** — cat bond spread and reinsurer instruments; Taiwan shipping and
  war-risk insurance rates; Gulf fiscal breakevens; sovereign fund disclosures

## Part 16b — The standing tail assessment (Monthly Macro)

**Placement decision: Monthly Macro, not Disruptive Themes.** Cadence decides it —
quarterly means up to three months between reviews of a scenario whose probability
may have moved in a week, and half the list has daily or weekly first-movers.

**This does not duplicate the tripwires.** They are different functions:

| | Tripwire (Part 16) | Assessment (here) |
|---|---|---|
| Nature | Mechanical, data-only | Deliberate, includes judgement |
| Cadence | Every run, per report | Monthly, all 20 in one place |
| Output | Status flag | Probability band, outlook, delta |

The assessment **consumes** tripwire status rather than re-deriving it.

### Schema

```sql
tail_assessment (run_id, scenario_id, horizon,
                 probability_band, outlook, tripwire_status,
                 data_state, desk_view, news_state,
                 rationale, changed_from_prior, change_driver)
```

**Bands, not point estimates** — effective n on these is roughly zero, and a point
probability would be false precision. Over a stated **12-month horizon**:
remote (<2%) · low (2–10%) · moderate (10–25%) · elevated (>25%).

### The three qualitative inputs

**1. Official-sector risk assessments — the best free source for exactly this.**
These bodies publish vulnerability assessments as their job: IMF Global Financial
Stability Report, Fed Financial Stability Report, OFR Annual Report and
short-term funding monitor, BIS Quarterly, ESRB. Route through the existing
`views` ingest. They are more rigorous than sell-side on tail risk and carry no
book.

**2. Desk and banking commentary** — the views ingest sources already planned,
plus bank earnings-call credit commentary and SLOOS. Store the structured view,
never the prose.

**3. News** — the events layer, filtered by a new `scenario_id` tag on events.
One tag field, no new pipeline.

### Change tracking — the discipline that makes it worth doing

**Form the new assessment before looking at the prior.** Same anchoring rule as
the Section 0 scorecard and the crypto forecast: derive, then compare, then log
the delta.

**A change requires a named cause** in `change_driver` — a data move, a dated
event, or a published view that shifted. *"Feels riskier"* is not a cause and the
field rejects it.

**Track assessment stability as a process metric.** Probabilities swinging every
month means the process is noise; probabilities that never move means the section
is decorative. Neither extreme is healthy, and the trend tells you which failure
you have.

### Grading — honestly

Twelve-month horizons are nominally gradeable, but base rates near zero mean
almost everything resolves as "did not happen," which teaches nothing.

**So grade the ordering and the direction, not the levels.** Did scenarios you
elevated actually see their first-mover series deteriorate over the following
three to six months? That is checkable, and it measures whether the assessment
process has any information content. Log it with the other Tier 1 process
metrics.

### Rendering — and the length budget

**One compact table, twenty-five rows:** scenario, band, direction of change,
tripwire status. That is the whole standing section.

**Narrative only for scenarios that changed band or fired a tripwire** — typically
three or four a month, at a few sentences each. **Hard cap: one page.** Twenty
narrative paragraphs monthly would be unread within a quarter, which is the
failure mode this system can least afford.

### Build

- **Session 5** — `tail_assessment` table; `scenario_id` on events
- **Session 14** — official-sector sources into the views ingest
- **Session 15c** — assessment generation, delta logic, stability metric

## Part 16c — The tail scenario appendix (Disruptive Themes)

**Priority: high. Deferred by sequence, not by importance.** The monthly table
tells you where each scenario stands. **This tells you what each scenario is.**
Without it the standing table degrades into twenty-five labels you half-remember,
which is the failure mode this section exists to prevent.

Mechanisms do not change month to month — only probabilities do. So this is a
**static document, written once and reviewed annually**, living in the repo and
read through rather than regenerated.

### Structure — roughly one page per scenario

1. **Mechanism.** The causal chain, stated plainly. Not "funding stress" but:
   reserves fall → dealers ration balance sheet → repo rates spike → leveraged
   positions unwind into a thin market.
2. **Why now.** The structural condition making it live in *this* cycle rather
   than in general.
3. **Transmission.** Which pillars it hits, in what order, over what timescale.
4. **What it does to positioning.** Which trades break, which hedges work, what
   stops functioning. *(Written by Ari — this depends on the actual book and
   horizons, and a generic version is worse than none.)*
5. **Historical analogue, and how this differs.** The second half matters more.
6. **What would retire it.** The condition under which it stops being live.
7. **Cross-reference:** first-mover series and tripwire threshold, so the
   appendix and the standing table are visibly the same object at two
   resolutions.

### How to do it

**Batches of five, by tier, one sitting each.** Keeps mechanisms comparable within
a batch. **Start with Tier E** — market-structure failures are the least covered
in ordinary commentary and the least likely to already be in your head.

Effort: ~6–8 hours total, but most is drafting and reading rather than original
work. Per scenario, roughly 15 minutes of your attention. **Two to three hours of
real effort across several sessions.**

**Do it in a fresh session with this document attached, or in Claude Code once
`docs/` exists** — so the output lands in the repo as a file rather than as chat
text to be moved.

**Timing: after v17 has run at least once.** You will write a better version once
you have seen which scenarios you keep wanting more context on.

---

# Part 17 — The CPI lead composite

**The principle:** find the physical or contractual step that *precedes* the
price, and track that instead of the price. The nitrogen complex in Session 3c is
one instance. This generalises it across the whole index.

**The construction rule that makes it a system rather than a list:** every
component stores its **stated lag** explicitly, and the report renders the
lag-adjusted projection alongside the current print. **A lead indicator scored
coincidentally is worth nothing.**

## Components, by CPI weight

### Shelter — the single largest improvement available

Roughly a third of CPI, entering with a 9–12 month lag **by construction**: BLS
samples leases on a six-month rotation and most leases reset annually. This is
mechanical, not noise, and it means a third of the index is knowable three
quarters early.

| Series | Lag to CPI shelter | Source |
|---|---|---|
| Cleveland Fed New Tenant Repeat Rent | ~4 quarters | Free |
| Zillow observed rent | ~4 quarters | Free |
| Apartment List new lease | ~4 quarters | Free |

### Wages — the contractual channel

- **Atlanta Fed Wage Growth Tracker** — leads unit labour costs
- **Union contract settlements** — literally forward-looking, setting wages two
  to three years ahead. Public-sector settlement data and major private contracts
  are published and **almost nobody tracks them as an inflation input**

### Health insurance — mechanically predictable

CPI uses a retained-earnings proxy updated annually, which makes the component
knowable a year ahead once source data publishes. **State insurance rate filings
are public** and lead premiums, which lead the CPI component.

### Trade and tariffs

- Import price indices → core goods
- **Tariff effective dates** — pure lead information. A scheduled rate change is a
  dated future CPI input, and it is already in `calendar.yaml`
- Freight rates → landed cost, ~2 quarters

### Realized-vs-expected 10-year gap — expectations-side conditioner

`realized_10y_vs_expected_10y` — trailing 10-year annualized CPI (currently
~3.3%) minus the 10-year inflation swap or breakeven (~2.4%). Both inputs are
already fetched or trivially computed from CPIAUCSL + T10YIE. Renders in
`inflation` as one line. `trigger_eligible: false`.

**Why it earns a slot.** The trailing series is a queue: each new ~3% monthly
print replaces a ~2% print rolling off from 2016–17, so realized 10y rises
mechanically for years, near-independent of incoming data. Experienced
inflation is one input to household and wage-setter expectations, so a
persistent positive gap is a slow de-anchoring pressure — the expectations-side
companion to scenario 16.

**The trap, written into the metric so it is never misread:** the gap has TWO
closing paths, and the second is mechanical. The 2021–22 spike prints (peaks
~9%) exit the 10-year window in 2031–32, at which point realized 10y falls
sharply with no change in anyone's beliefs. **Maintain a rolloff calendar
alongside the level** — what the trailing series will do over the next 12–24
months on flat 2.5% / 3.0% / 3.5% assumptions — and grade the gap against that
counterfactual, not against zero. A rising gap that merely matches the rolloff
arithmetic is not news; a breakeven that starts chasing the realized line IS
(that is de-anchoring, and it escalates to the Warsh thesis-B evidence list).
The commentariat version of this chart ("the gap must close, therefore
expectations must rise") skips the second path; this metric exists partly so
the reports never repeat that error.

### Medical and pharma

Published list price changes and PBM formulary decisions lead CPI medical
components by quarters.

### Goods

- **PPI by stage of processing** — intermediate-to-finished spread. Classic lead,
  free on FRED
- **Manheim used vehicle values** → CPI used cars, ~2 months. Auction volumes and
  lease returns lead Manheim
- **Nitrogen complex** → food CPI, 2–3 quarters (Session 3c)

## The composite

Weighted implied CPI three to nine months forward, built from each component with
its lag applied and weighted by CPI basket share.

```sql
cpi_lead (run_id, component, raw_value, stated_lag_months,
          cpi_weight, lag_adjusted_contribution, as_of)
```

Render **three horizons** — 3, 6 and 9 months — since components have different
lags and the composite's coverage of the basket changes with horizon. State the
covered share at each horizon; a projection covering 40% of the basket is a
different object from one covering 80%.

## Why this is an edge-layer metric, not just a data addition

**Plot the composite against breakevens and the Cleveland Fed nowcast.** The gap
is a direct expectation-versus-outcome measure: what the physical and contractual
pipeline implies, against what the market prices.

That is the Part 15 construction applied to the largest macro series there is,
and it is where this stops being an information system and becomes a view.

## Cautions

- **Lags are estimates, not constants.** The shelter lag has shifted with lease
  behaviour. Store the lag as a parameter, review it annually, and log changes.
- **Do not double-count.** Several components overlap with existing pillar
  series. Run the correlation guard before anything enters a composite.
- **`trigger_eligible: false` on the composite.** It is a projection, and
  projections condition the read rather than firing signals.
- **Kill condition:** if the 6-month composite shows no relationship to realized
  CPI over the backfilled history, the lag structure is wrong — fix the lags or
  drop the composite. Do not keep it as decoration.

## Build

- **Session 3c** — shelter series (highest value, ~30 min), PPI stage of
  processing, Manheim
- **Session 6** — backfill, then fit and validate the lag structure against
  history. **The composite cannot be built before this** — the lags need to be
  estimated, not assumed
- **v19** — wage settlements, health rate filings, import prices, freight
- **Deferred** — PBM and pharma list pricing

---

# Part 18 — Replacing news consumption

**Stated goal:** the reporting system replaces most daily news reading.

**Achievable for roughly 80%.** The remaining 20% should not be replaced, and
saying which is which is the whole design.

## The two functions of news consumption

| Function | Can the system replace it? |
|---|---|
| **Situational awareness** — knowing what happened | **Yes.** This is what the events layer does, and it does it better: filtered, tagged to series, deduplicated, no clickbait |
| **Serendipity** — encountering what you did not know to look for | **Partly.** The coverage-gap scan is the closest thing, and it needs strengthening for this purpose |

## The design tension, and the resolution

Everything else in this system optimises for **selectivity** — surprise ranking,
only-what-changed rendering, hard word budgets. "Replace my news" pulls toward
**comprehensiveness**, and comprehensiveness is how a report becomes unread.

**Resolution: ingest wide, rank hard, render narrow.** Broader intake with
tighter filtering — not more output.

## What has to change

### 1. A daily events digest — the missing surface

Events currently render only in the Monthly front matter and per-pillar. **To stop
reading news you need a daily surface**, which is the Daily Cascade 7AM block.

Add: overnight and prior-session events above a salience threshold, each with
what moved and which pillar it touches. Target **8–12 items, hard cap 15.**

### 2. Explainer depth on high-salience events

An event record is date, domain, salience, affected series. **News gives you
context that a record does not.** For salience 4–5, the classifier generates two
to three sentences: what this is, why it matters, what it changes. Not a summary
of the article — the *significance*, which is the part you actually read for.

### 3. Wider ingest, harder ranking

Current sources are macro-tagged and narrow. Broaden intake — general wires,
sector press, regional coverage — and let the salience filter do the work.
**Ingest ten times as much, render the same amount.**

### 4. Monthly coverage-gap surfacing

The gap scan currently runs quarterly. **For this purpose it must surface
monthly** — unmapped high-salience events are precisely the things your taxonomy
did not anticipate, which is exactly what you would otherwise get from browsing.

### 5. A completeness audit — the only way to know it is safe

**Run parallel for three months before stopping.** Each week, scan news as usual
and log anything material the system missed. That produces a **miss rate**, and
the miss rate is what tells you whether to taper.

```sql
coverage_audit (week, manual_items_logged, system_surfaced,
                missed_count, missed_detail, category)
```

Target: **under 5% miss on material items for three consecutive months** before
reducing manual reading. Categories of misses tell you what to fix — a pattern of
misses in one domain is a source gap, scattered misses are a threshold problem.

## What not to replace

- **Primary sources on positions you actually hold.** Filings, transcripts,
  central bank statements. The system points at them; read them yourself.
- **One or two commentators whose *reasoning* improves yours.** Not for their
  conclusions — for the argument structure. That is a different activity from
  awareness and the system cannot do it.
- **Anything in your professional domain.** The system has no edge there and you
  do.

## Honest limitation

**The system cannot surface what it was never told to look for.** The coverage-gap
scan catches recurring blind spots, but a genuinely novel category appears first
as one unmapped event and looks like noise. **That is the residual case for some
unstructured reading** — not much, and not daily, but not zero.

## Build

- **Session 9** — daily events digest into the Cascade 7AM block
- **Session 8** — explainer generation for salience 4–5; wider source list
- **Session 15c** — monthly coverage-gap surfacing; `coverage_audit` table
- **Post-v17** — run the three-month parallel audit before tapering

---

# Part 19 — Technological discontinuity tracking

**Three domains — AI capability, quantum, cyber — where change can arrive as a
step function rather than a trend.** Lives in Disruptive Themes; feeds the tail
watch; refreshes on events, not just on schedule.

## The two rules that make this workable

**1. Score verified capability, never announcements.** These domains have the
worst signal-to-noise in the system: quantum "breakthroughs" arrive quarterly and
mostly evaporate under replication; AI capability claims systematically overstate.
Every tracked milestone carries a **verification standard defined in advance** —
independent replication, benchmark under stated conditions, deployed use — and
the score moves on verification, not the press release. Without this rule the
tracker is a hype index.

**2. Event-driven refresh — the mirror of premise expiry.** Quarterly cadence
alone defeats the purpose: a verified capability event triggers immediate
reassessment of the domain thesis and any dependent tail scenarios. A step change
that waits eleven weeks for the next scheduled review was not worth tracking.

## Sources — literature, correctly instrumented

**Journals are the wrong primary feed for two of the three domains.** Frontier AI
appears on arXiv, in lab releases and benchmark results months before journals —
and increasingly never reaches journals, since frontier labs stopped publishing
their best work. Cyber capability appears in CVE and incident data. **Quantum is
the exception:** Nature and Science still carry the milestone papers.

| Feed | Domain | Cost |
|---|---|---|
| **arXiv API** — cs.AI, cs.CR, quant-ph; filtered by citation velocity, not volume | All three | Free |
| Benchmark leaderboards and standardized evals | AI | Free |
| Lab and vendor releases (via events layer, salience-filtered) | AI, quantum | Free |
| **NIST PQC migration status** | Quantum, cyber | Free |
| Nature / Science milestone papers | Quantum | Free |
| CISA KEV catalog; patch-to-exploit interval | Cyber | Free |
| **Cyber insurance loss ratios and pricing** — underwriters putting capital behind a risk assessment; market-priced, no narrative | Cyber | Free (NAIC, carrier reports) |
| Chainalysis ransomware payment data | Cyber | Free annual |

The arXiv filter matters: volume in these categories is enormous and mostly
noise. **Citation velocity and replication attempts within 90 days** are the
selection signal, not abstract counts.

## Domain 1 — AI capability (extends Factor I)

Factor I currently tracks the *economics* — capex, revenue, jobs, circularity.
**The step-change risk is technical, and nothing tracks it.**

- **Capability milestones with verification standards** — autonomous task
  horizon, verified benchmark jumps, deployed autonomy in regulated domains
- **Cost curves** — training and inference cost per capability level. *The
  economic transmission runs through cost, not capability:* a capability that
  becomes 100x cheaper is the step change even when the frontier is static
- **Diffusion lag** — frontier capability vs. enterprise deployment. The gap is
  where the economic impact timing lives
- **The abrupt-change tripwire:** any verified capability event that moves a
  named tail scenario (3, 13, 20) triggers immediate reassessment

## Domain 2 — Quantum (promoted from the crypto ledger to domain status)

The migration-gap metric from Factor V generalises and remains the spine:
**capability milestones vs. post-quantum migration progress, and the gap between
them.**

- Logical qubits and error-correction milestones — *verified only*
- NIST PQC adoption in: settlement systems, custody, banking infrastructure, and
  the major protocols
- **Estimated vulnerable value** — assets secured by exposed cryptography, a
  computable number
- The positive branch — materials, chemistry, optimization — tracked at low
  intensity: real, slow, and currently without economic transmission

## Domain 3 — Cyber (merges with the existing Tail Scan domain)

Reconcile with Tail Scan first (see Part 16). Then add what it likely lacks:

- **Cyber insurance pricing and loss ratios** — *the best single series in this
  domain.* Market-priced, capital-backed, and directly in Ari's professional
  wheelhouse without requiring his judgement to populate
- Patch-to-exploit interval trend — **the AI-offense tell.** If AI-discovered
  vulnerabilities are changing attack economics, this interval compresses first
- KEV additions per quarter; ransomware payment volumes
- Systemic concentration: cloud, CDN and identity-provider dependence — the
  single-point-of-failure map for scenario 13

## The standing thesis — one per domain

Same machinery as the crypto forecast (Part 12): vintage-stored, drivers mapped
to observables, derived before looking at the prior, revised on verified events
with `change_driver` named.

```sql
tech_thesis (vintage_date, domain, thesis_summary, drivers_json,
             economic_transmission, time_horizon, confidence,
             changed_from_prior, change_driver)
```

**Each thesis must state its economic transmission explicitly** — which pillars,
which assets, over what horizon — or it is commentary. "Quantum matters" is not a
thesis; "PQC migration lagging capability by >N years puts $X of secured value at
repricing risk, transmitted through custody and settlement trust" is.

**Grade the drivers, not the vision** — same rule as the 3–5 year crypto frames.
Did the milestones the thesis expected actually verify, on roughly the expected
timeline?

## Rendering

- **Disruptive Themes** — the three theses, full treatment, quarterly plus
  event-driven
- **Monthly** — one line per domain in the tail assessment table; narrative only
  on verified events
- **Tail watch** — scenarios 3, 13, 18, 20 consume the verified-event stream

## Build

- **Session 8** — arXiv and NIST feeds into the events layer; verification-status
  field on capability events
- **Session 15c** — `tech_thesis` table, event-driven refresh trigger
- **Deferred** — cyber insurance series, patch-to-exploit tracking, vulnerable-
  value estimate (folds into the Tail Scan reconciliation)

---

# Part 20 — Daily Cascade: the five blocks

## Naming: "blocks" inside the Daily, "tiers" for the report stack

Two five-part systems existed under one word. **Resolved:**

| Term | Refers to | Members |
|---|---|---|
| **Tier** | The report stack (Translation Table) | Disruptive Themes → Monthly Macro → Top & Bottom → Alternative Asset → Daily Cascade |
| **Block** | Sections within the Daily Cascade | Direction · Market Base · Confirmation · Backdrop · Execution |

Rename in the v12 JSX: `TierBanner` → `BlockBanner`, `TIER_LABELS` → `BLOCK_LABELS`,
`tier:` → `block:` in section metadata, and the narrative summary fields
(`narr_direction` etc.) keep their keys but the heading reads "by block". The OPS
strip is unchanged — it still gets no banner, because operational status is a
quiet system check rather than analysis.

Cheap to do now, genuinely confusing later when a session note says "Tier 3."

## The five blocks as the 7AM skeleton

**The 7AM brief inherits the block structure.** Not for consistency alone — the
frame turns out to be the right skeleton for everything designed in this
document, which is reasonable evidence it was well constructed.

| Block | Descriptor | What lands here |
|---|---|---|
| **1 · Direction** | The standing read | Swing thesis state (INTACT / STRAINED / INVALIDATED) with session N of ~15 and distance to invalidation · **cross-report state, all five reports** (currently only two) · any tail tripwire that has escalated |
| **2 · Market Base** | Where we stand | Yesterday's carry-forward · overnight cascade · levels · positioning inherited from the close |
| **3 · Confirmation** | Does the evidence agree | **Expiry-bucket GEX** (0DTE share, per-bucket flip, distance to flip, post-expiry profile) · dealer hedging per 1% · **crypto funding, OI, liquidation asymmetry, leverage regime composite** · breadth · momentum |
| **4 · Backdrop** | Context that shapes but does not time | **Overnight events digest, 8–12 items with explainers** · macro catalysts and the forward calendar · **tail watch, Tier A tripwires — dormant ones do not print** · financial news synthesis · dollar and FX · yields |
| **5 · Execution** | Where analysis resolves into trades | Trade setups and thesis · open scenario planning · **reactive intraday trigger status** (mechanical trigger, 30-minute cooling-off, capped size, one per day) |
| **OPS** | Quiet system check, no banner | Validator warnings · staleness flags · pipeline run status · heartbeat |

## Two rules carried into the block structure

**Escalation moves items up, not down.** A tail tripwire lives in Backdrop while
dormant and moves to Direction when it fires. A swing thesis moves from Direction
to Execution only when invalidated and being replaced. Nothing renders in two
blocks at once.

**Dormant content does not print.** Most mornings Backdrop's tail section is
empty, and that is the correct output. The narrative summary still writes one
paragraph per block, and "nothing in this block changed" is a complete paragraph.

## White paper §2.8 disposition — dealer-reporting refinements

Five of the six deferred refinements in the Daily Cascade white paper are already
in this document (charm/vanna in Session −1; pin log, dollar-gamma-per-1%
normalization, intraday sampling with the settled-OI caveat, and the flow-split
verification question, all above). Disposition of the remainder plus the three
intraday-report improvements from the same review:

**Build now, out-of-band with the block rename (~45 min total):**

1. **GEX into the 10AM open analysis.** The open is when 0DTE positioning
   crystallizes and dealer hedging is most observable, and the 10AM report
   currently does not fetch it. One additional parallel call inside existing rate
   limits — the white paper's Priority 1, and correctly so.
2. **"Delta since prior report" field** at the top of the dealer section in every
   intraday report: net GEX change, call-wall shift, gamma-flip drift, 0DTE share
   decay since the prior read. Diffs against stored snapshots the logger already
   keeps — no new data. **This is what makes flip-drift monitoring (white paper
   rule 2.7.5) operational rather than aspirational: you cannot track drift you
   do not display.**
3. **Refresh-vs-inherit labeling**, riding along with the delta field: net GEX,
   flip, walls, max pain refresh every report; JHEQX collar levels and structural
   monthly walls carry from 7AM and are labelled as carried; 0DTE fields always
   refresh. Staleness tagging applied intraday.

**Split — the vendor cross-check** (the paper's "single highest-value
refinement"):

- **Cheap now (Session −1):** recompute GEX independently from FlashAlpha's own
  per-strike payload and diff against their reported aggregate. Validates their
  aggregation and sign conventions — this is the check that catches a silent
  methodology change — and costs nothing given the raw payload is stored anyway.
  Log the recompute spread; alert past a declared threshold.
- **Deferred — a true second source.** Another subscription, or self-building
  from delayed CBOE chains: real money or real hours for poor quality. The
  self-recompute captures most failure modes that matter; a second vendor waits
  until a disagreement actually needs adjudicating.

**Already reading rules, not build items:** white paper rules 2.7.5–2.7.8
(flip-drift, the GEX-up-skew-up divergence flag, late-day 0DTE expiry, quarterly
proximity) live in the paper and condition how the pillar prompt is written in
Session 14 — they do not need separate construction.

## Build

- **Out-of-band batch** — tier→block rename + 10AM GEX + delta field +
  refresh-vs-inherit labels (~1 hour total)
- **Session 9** — events digest into Block 4; block-mapped rendering
- **Session 14** — expiry buckets into Block 3
- **Session 13.5** — crypto positioning into Block 3
- **Session 15a** — swing thesis state into Block 1
- **Session 15c** — tail tripwires into Block 4 with escalation to Block 1
- **Out-of-band** — the tier→block rename in the v12 JSX, ~15 minutes

---

# Part 21 — Build log: changes absorbed from the altdata chat (3 Sep 2026)

*Development has started; this part records changes made in the Alt Asset build
chat so this document stays canonical. Paper numerals in that chat are
per-chat labels — canonical mapping: their VIII = Currencies (V), their XI =
Credit (VI), their XIII = Volatility (XI). Cross-reference by NAME in all
future work.*

## Alt Asset weekly — §7 Volatility Regime (new)

Between macro backdrop (§6) and per-asset surveillance (renumbered 7→8). The
Volatility paper's operational core, implemented: five-state classification
(deep calm / normal low-vol / elevated–pre-transition / high-vol / crisis)
from joint VIX level + VIX/VIX3M term-structure ratio, with a live count of
computable regime tells against the paper's three-or-more transition
threshold. Honesty preserved in-render: four of eight tells (skew, implied
correlation, gamma flip, yen vol) need options-surface data the free tier
lacks — stated, with a pointer to the paper.

**Design ruling worth keeping:** VIX is deliberately NOT a 19th asset row —
spot isn't investable and long-vol products bleed roll. It enters as regime
context that gates adds and sizing everywhere else. This is the
regime-not-position principle applied at the schema level.

**altdata pipeline (no schema bump):** FRED_SERIES += VIXCLS, VXVCLS;
optional `sources/yf_vol.py` (^MOVE, ^VVIX, lazy, no-op degrade);
`analytics.vol_regime(store)` with own-history percentiles (≥250 obs), SPY 1M
realized, implied-minus-realized, tells counter, None-safe; §7 renderer.
One-time backfill: `python -m altdata.run --only fred yf_vol --lookback 1200`.

**v17 hook:** Session 11's Alt Asset extract contract now carries
`vol_regime_state` into the store — the Weekend Synthesis and Monthly consume
the classification rather than recomputing it. Dashboard banner deferred to
the next jsx schema bump (still v5).

## FX chart refresh module

`report/fx_charts.py` + `fx_anchors.py`: regenerates the Currency paper's
eight figures from real daily history (fredgraph.csv → FRED API → yfinance →
packaged anchors, captions name the source), idempotent re-injection into the
HTML. The Currency paper gained the chart set + "Long View in Pictures"
(thirty-year envelopes, five-year detail per major, envelope-vs-gold, range
table). **Pattern to reuse:** paper figures regenerated from live data by a
pipeline module is the right template for any paper chart that dates.

## Credit paper renumbering

"Rates as a Trade, Not a Policy" inserted as §29 (curve trades, term premium,
TIPS/breakevens, swap spreads, futures basis, common-bus table); prior 29–39
→ 30–40. The paper is now 40 sections; word count to re-measure at next
commit.

---

# Part 22 — Build log: Daily Cascade production carry-over (3 Sep 2026)

*Source: the Daily Cascade production chat (v12 previews, both companion
papers). Per-chat numeral "IX" = The Dealer's Hand (canonical XIII).*

## Shipped structural changes (previews production-ready pending live data)

- **FRI 1800 Weekly Reflection = 14 sections**, incl. a multi-timeframe candle
  section (daily/4-week/6-month; conflicts resolve upward — higher frame sets
  size, lower frame sets entry), Monthly Macro Delta (10 pillars WoW), a
  SpaceX IPO Weekly Tracker, and Weekend Watchlist (risk-event flags only;
  Weekend Homework retired). **Standing rule: review/reflection sections
  always render last.**
- **0700 gains §24 SpaceX IPO Watch** under a new Single-Name Watch banner:
  daily trigger monitor (filing news, secondary mark >5% W/W, ASTS >3% gap vs
  sector, principal commentary, Starlink disclosures); default read is a
  10-second checkbox. The preview labels this banner "Tier 6" — **rename to a
  block per Part 20** in the same v12 batch.
- All 8 preview files carry accordion JS and passed the pre-production audit.

## New standing pattern — single-name overhang monitor

For any held position whose dominant risk is a non-price event: a daily
checkbox in 0700 + a W/W tracker in FRI 1800. SpaceX/ASTS is the first
instance. Deferred: ASTS filing-stage playbook wired into §22's scenario
library (canonical detail: Daily Cascade WP Ch. 24, Tier 3 item 22).

## PRODUCTION GATE (precondition, not a feature)

Audit found synthetic backdrop values, at least one signal-inverting (§15
margin debt shown $878B vs actual ~$1.4–1.5T record regime, +50% YoY).
**Every Tier-4/backdrop row requires a live feed and a freshness stamp before
the Daily Cascade is trusted in production, and §15 thresholds must be rebuilt
on the current regime.** Merge with Sessions 2–3 plumbing, not new hours.

## Rule upgrade — confluence by cluster (§22–23 setups)

Four independent daily voting clusters: dealer mechanics · participation ·
macro pricing · price structure (sentiment = context; slow-leverage = out of
horizon). **A full-size setup requires ≥3 of 4 clusters confirming and none
contradicting; section counts within a cluster add color, not votes.** Sits
beside the Part 13c cross-report rules.

## Backlog governance

The Daily Cascade WP's **Ch. 24 is the canonical analytical backlog** for
Daily refinements (3 tiers, 22 ranked items; sequencing: measurement before
features, subtraction before addition, paid data only after free data proves
the strategy). This document and the schedule hold one-line scheduling
pointers only. **Reconciliation flags:** Ch. 24 Tier 1's outcome-logging
layer (pin rates, signal outcomes, base rates, expectancy) IS the v17/v18
register + pin log — one system, never scheduled twice; "live Tier 4 feeds"
IS the production gate above merged into existing plumbing; GEX vendor
cross-check and indicator de-duplication are already in Session −1 and the
Technical Indicators paper's cluster rule respectively.

**Handoff note reconciliation (6 Sep 2026) — Dealer's Hand v1.1 Part V
pointers, with build-weekend status:**
- DEX split by bucket (0DTE vs monthly) — **DONE** in the Greeks extension
  (`exposure_compute.py`, four buckets, expiration-release ladder).
- Flip-stack width (monthly flip − 0DTE flip, pts and % of spot) — now
  **cheap (~30 min)** since per-bucket flips exist; add as an exposure
  output and a Daily §06 delta-table row. Detail: Dealer's Hand Ch. 18.4/21.4.
- Wall-migration flag (held/migrated on first test, per bucket, per session)
  — **deferred**, ~2h, needs the intraday cadence (first-test timing).
  Detail: Dealer's Hand Ch. 20.2/21.4.
- Rename checklist: the 0700 "Tier 6 · Single-Name Watch" banner joins the
  v12 tier→block rename task (out-of-band item 4 / D0) — never renamed
  ad hoc.
- Retail-positioning lines (~2h + ~3h contingent) — **merged into Part 29.3
  (RTAT10)**; not scheduled twice.
- The production gate above maps to built machinery: freshness stamps =
  `available_at` + `freshness.check_signals`; D4 adopts it as an acceptance
  criterion — no Daily block publishes on a payload lacking a live,
  fresh source.

---

# Part 23 — Build log: Top & Bottom session (3 Sep 2026)

*Scoring engine v8, parallel-signal architecture, report v13, white paper in
three formats. The calibration findings summarized in the library guide are
now production code.*

## Calibration → weights → the number that changed

`calibrate_thresholds.py` runs 13 hand-keyed episodes through the production
score functions (episode-level classification, not a continuous backtest).
Original weights: tops 0/3, bottoms 4/6, controls 4/4. v8 rebalance
(Valuation 0.12→0.17, Macro 0.29→0.24, others unchanged, sum 1.00) moves the
2000 top to OVEREXTENDED (−0.52) in calibration and **May 2026 from −0.51 to
−0.60** — deeper into OVEREXTENDED. A weight sweep proved rebalancing alone
cannot catch 2007/2022-type tops: tops are idiosyncratic by trigger
(valuation / credit / policy), bottoms rhyme. Hence:

## The three parallel overlays (independent of the composite; fire at 3+)

| Overlay | Top type | Triggers | State (3 Sep) |
|---|---|---|---|
| Concentration & Complacency | 2000/2022 valuation | FwdPE≥20 · CAPE≥30 · ERP≤1.5% · Top10≥25% · VIX≤18 | **5/5 ACTIVE** (known false-fire Aug 2024 — condition, not timing) |
| HY Spread Acceleration | 2007 credit | HY ≥+50% off 12m low · 30d HY ≥+40bp · 30d IG ≥+15bp · IG ≥110bp | 0/4 CLEAR (HY +8% off low — cycle young) |
| Liquidity & Funding Stress | 2019/2020 plumbing | NetLiq YoY ≤−10% accel · reserves ≤$3.15T · SOFR−IORB ≥+5bp 5d · RRP ≤$200B · |TGAΔ| ≥$200B | 2/5 CLEAR (reserves $3.05T, RRP $130B firing) |

New Leading indicator #8: `score_hy_acceleration` (% off trailing-12m HY OAS
low; +1 quiet / 0 early / **−2 at +50–100% = the top signal** / +1 blown out —
the non-monotonic banding is deliberate: fully blown out is bottom fuel, not
top risk). Tests: 67 pass, weight and delta assertions updated to v8.

## Report v13 and the appendix map

BLUF −0.60 (prior −0.51). Parallel Signals strip under BLUF + three
collapsible detail sections. Appendices relettered: A Valuation Deep Dive ·
**B Prior Market Comparisons (new)** — Jan 2022 / Feb 2020 / Oct 2007 / Mar
2000 vs today, each with similar/different/unresolved framing; the stated
takeaway: *today = 2000 valuation + 2007 policy + 2022 concentration, with no
visible trigger* · C Threshold Reference · **D Options Portfolios (rebuilt)**
— scenario-weighted (3M EV +0.6%/DD −2.6%; 6M +1.8%/−3.2%; 12M +3.6%/−2.4%),
probability weights the load-bearing assumption, payoffs illustrative. The
Part 13c reconciliation rule (Monthly App. C pedagogical vs T&B App. D
engineered) survives the relettering unchanged. Desktop standalone HTML
pattern validated (jsx→CDN React+Babel, ~117KB, static snapshot).

## Reconciliation flag — one fetch layer for funding series

The Liquidity overlay's inputs (IORB, SOFR, RRP, reserves, TGA) are the SAME
series as the Monthly's funding tripwires and scenario 1's first movers. The
T&B pipeline (`fetch_monthly_v6.py`) and the v17 store must not maintain two
copies long-term: **build once in the store (Session 5), have T&B read from
it; the ~80-line plumbing below is the interim.**

## Scheduled from this session's pending list

1. Liquidity overlay production plumbing (~80 lines, interim) — out-of-band ~1h
2. Concentration + HY-accel overlays computed production-side into status.json — ~1h, same batch
3. **Continuous backtest harness** (`backtest_scorecard.py` vs VPS
   timeseries.db) — the real false-positive-rate measurement; calibration is
   episode-level only. Deferred, elevation test: it unblocks honest overlay
   thresholds.
4. Declined-for-now: fully-offline 400KB HTML, live-fetch proxy HTML,
   adjustable portfolio weights, white-paper charts (revisit after v17).

---

# Part 24 — Build log: Monthly Macro production handoff (May–3 Sep 2026)

*Source: the Monthly Macro build chat. This is the as-built record of the
pipeline that v17 extends — several v17 sessions now start from further ahead
than the plan assumed.*

## As-built pipeline (repo `achester-trading/chester-reports`, public)

`altdata/` (config with 59 FRED SeriesSpec entries · CSV store **already
carrying provenance + as_of per observation** · fred.py with pacing and
retry) · `monthly_macro/` (compute.py with 12 derived metrics · run.py ·
markdown/HTML writers) · workflow_dispatch-only Actions workflow ·
smoke_test.py. **v17 implication:** Session 5's store work is a migration
(CSV→SQLite, keep the provenance model), not a greenfield build; Session 4's
provenance layer partially exists.

**Mitigation A applied:** reports are artifact-only (90-day retention),
workflow `contents: read` — analysis stays out of the public repo while code
stays visible. **Mitigation B open (~30–45 min):** two-repo split with a
private outputs repo via the GitHub API.

## The scheduler is load-bearing and external

*(Superseded by Part 25 once the VPS migration is proven — retained here as
the as-built record and the fallback recipe.)* GitHub's native cron never
fired reliably in controlled tests; the `schedule:` block was removed.
**cron-job.org is the sole scheduler**, POSTing
to the workflow_dispatch API (`{"ref":"main"}`, four headers, success = HTTP
204) on `0 6 1 * *`. Two operational facts: verify the schedule isn't still
on its test interval, and **the PAT behind it expires ~May 2027 and fails
silently** — renewal is now a Part 14 calendar item, and the OPS heartbeat
(Part 20) is the backstop that would notice a missed run.

## Model tiering and fallback (API pipeline costs, distinct from Claude Code)

Opus for the monthly narrative (~14 calls/mo, ~$0.20/report); Sonnet for the
daily cascade (5–6 calls/day, ~$75–150/yr cached); combined ~$60–90/yr —
tier-mixing beats all-Opus (~$600/yr) and beats all-Sonnet on synthesis
quality. **Graceful degradation is the pattern to keep:** if the API fails,
`[NARRATIVE PLACEHOLDER]` survives and the run completes — a bad API day
produces a data-only report, never a failed workflow.

## Treasury bill share — Pillar 8's new lever (first response to the inverted regime)

New source `treasury_fiscal.py`: MSPD table 1 via the Fiscal Data API (no
key; 4th business day for prior month-end). Series: `tsy_bills_outstanding`,
`tsy_marketable_total`, `tsy_bills_share`. **TBAC reference range 15–20%;
current ~21.6% — already above range**, consistent with the bill-heavy
strategy; the signal to watch is *reversal*, which pushes duration back to
the market. Known limitation stated in-metric: this is the **stock** share
(direction over 3–12 months), not marginal issuance — QRA parsing is the
follow-on candidate. Design note to reuse: security-class labels matched by
case-insensitive substring with every distinct label logged at INFO, so a
Treasury relabel is a one-line fix instead of a silent-failure hunt.
**Cross-links:** this is the Twist chain's own variable (Part 4/events) and
the reason `duration_supply_balance` nets bills out of its supply line.

## The inverted-regime ruling and two new watch items

The Rate paper's operational claim, adopted: the front end is pinned by a
divided committee while the long end reprices on fiscal supply — **the QRA
now rivals the FOMC statement** and the framework treats it accordingly
(events layer salience, forward calendar). Two additions:

1. **30Y auction tail as a T&B trigger candidate** — tail ≥ +3bp is the most
   concrete real-time evidence of financing stress; wire into the Trigger
   Watchlist beside scenario 9's first movers (same series, two consumers,
   one fetch).
2. **30Y-vs-HY contradiction as a standing watch line** — a long bond near
   5.2% and HY near its 5th-percentile tights cannot both be right;
   resolution shows up first in CCC−BB dispersion. One line in Monthly
   Pillar 6 and the T&B report; `trigger_eligible: false`.

## Report-structure facts to preserve (v16 canon)

Watch-in-30-days renders each event as a bold unbulleted sub-header with
overshoot/undershoot bullets beneath. Cluster 2F now splits consumer stress
by tier and surfaced the **K-shaped consumer read** — subprime auto 60+ at a
record while prime bank-card delinquency sits at a two-year low; aggregates
conceal it, the subprime series are the ones that matter. Pillar 10's desk
commentary runs three tiers with NEW/INFLECTED/REITERATED flags and the
weighting rule: **flow observation heavily, capital commitment moderately,
forecasts lightly.** Gated blanks render as **B**.

## Gotchas — copy into CLAUDE.md verbatim at Session 0

Web uploader flattens zips (type full paths in Create-new-file instead) ·
hidden files invisible by default (Cmd+Shift+.) · TextEdit rich-text corrupts
.py · blank line required between a bold label and a bullet list · one
leading space in __init__.py breaks import · **WALCL is millions, RRP/TGA
are billions — normalize before net liquidity** · FRED deprecates ~1–2
series/yr silently (gold moved to GLD via yfinance) · secrets protocol: never
paste keys/tokens/full curl into chat, replace with XXX (two PAT leaks
occurred, both rotated).

## Immediate and backlog (scheduled)

**Next action — the 6-file upload batch** (Phase 2 yfinance 27 symbols,
treasury_fiscal.py, narrative.py, Treasury-updated run.py, requirements,
render_md Pillar 8 edit) — Phases 2 and 5 were written but never uploaded.
Then: repo-root duplicate cleanup · verify cron-job.org schedule · Mitigation
B · Phase 3 sentiment scrapers · news API (Pillar 10) · Phase 4 13F/EDGAR ·
QRA parsing. Still-manual-in-v1 flags (sentiment specifics, valuation
specifics, banking, commentary) remain honest placeholders in renders.

---

# Part 25 — Runtime ruling: the Hetzner VPS

## The ruling

**The VPS is the primary runtime and scheduler for every pipeline. GitHub
stays the single source of truth for code. Actions is retained as a manual
fallback only (`workflow_dispatch`, zero cost to keep). cron-job.org is
retired once the migration is proven.**

Three open problems this closes at once: the external-scheduler dependency
and its silently-expiring PAT (Part 14 item downgraded); Mitigation B, which
existed only because outputs needed hiding from a public Actions repo —
outputs now live on the box; and the artifact 90-day retention dance. It also
unifies the runtime: the T&B backtest harness already targets
`timeseries.db` on this box, so continuous data collection and report
generation share one machine, one secrets store, one heartbeat.

## The standing rule

**The VPS runs code; it never edits code.** All changes happen against the
repo (locally or via Claude Code), get committed, and the box pulls before
each run (`git pull --ff-only` at the top of every cron entry). A server with
uncommitted edits is two versions of the truth, and everything in this system
is against that.

## Migration plan (~1.5–2h, out-of-band; sequence in the schedule)

1. **Lockdown (~20 min):** non-root user, key-only SSH, password login off,
   firewall on. The one security-relevant step.
2. **Runtime (~15 min):** Python 3.11+, git, clone, venv,
   `pip install -r requirements.txt`, `smoke_test.py` green.
3. **Secrets (~10 min):** `.env` with FRED + Anthropic keys, `chmod 600`,
   `.gitignore` verified. Secrets live on the box, never in the repo — the
   Part 24 secrets protocol applies verbatim.
4. **Cron + heartbeat (~20 min):** monthly line first (`0 6 1 * *`), Daily
   Cascade's eight daily lines when v17 reaches them; every run appends to a
   log and touches a heartbeat file; a checker alerts on staleness. **This is
   the OPS block's data source — with a box you own, the heartbeat is
   mandatory, not decorative: a dead VPS is the same silent-failure class as
   the expired PAT.**
5. **Prove, then retire:** one manual run, one cron-triggered run, outputs
   verified — then cron-job.org is deleted and Part 24's dispatch recipe
   becomes the documented fallback.

## Claude Code on the box

Claude Code can be installed on the VPS itself and used for server work
conversationally — venv setup, cron entries, heartbeat script, debugging in
place. This is the recommended path for steps 2–4: supervise rather than
type. The Session 0 auth rules apply there too (subscription login, watch
the `ANTHROPIC_API_KEY` billing trap — the key WILL be in the box's
environment for the pipeline, so use a login shell without it for
interactive sessions or verify the auth mode with `/status`).

## What deliberately does not move

Report *reading* stays wherever it is convenient (outputs can push to a
private repo or be served later — decide when needed, not now). Actions
stays as the one-click manual rerun path. And code review, sessions, and all
v17 build work stay in the repo workflow — the VPS is downstream of all of
it.

---

# Part 26 — FINAL ARCHITECTURE CHANGE ORDER (controlling)

*Source: "Chester Reports — Final Architecture Change Order for Claude"
(docx, 3 Sep 2026). **This part controls wherever it conflicts with Parts
1–25.** The companion review (v10, continuous-learning edition) is a
technical reference for detailed audits and rationale only — it is NOT an
independent requirements list and adds no scope on its own. Commit both docx
files to `docs/reviews/`. After this part: broad architecture design is
FROZEN. Future parts are build logs or principal-directed amendments
(Part 27 is the first); live evidence, not design
enthusiasm, elevates backlog items.*

## 26.1 Governing objective

OBSERVE → INTERPRET → DECIDE → EXECUTE → MEASURE → DIAGNOSE → LEARN →
RE-TEST → UPDATE. **The reports are views over the system; better decisions
are the product.**

## 26.2 Non-negotiable changes (MUST)

1. **Decision-centric state model.** Market State, Opportunity State,
   Portfolio State, Decision State are first-class objects; reports render
   from them. Horizons stored explicitly — a bearish structural regime, a
   neutral swing state, and a tactical one-day rebound coexist without
   averaging.
2. **Point-in-time correctness.** Every material record carries
   `available_at`; one canonical as-of join engine; historical computation
   sees only information available at the time.
3. **Immutable Decision Packet** per material recommendation/run:
   run_id, decision_time, available_at_cutoff, data manifest hash, source/
   registry/metric versions, code git hash, prompts, model versions,
   rendered outputs. **A historical run must replay exactly from it.**
4. **Minimal decision register lands in v17** (not v18): every serious
   recommendation, abstention, operator TAKE/DECLINE/MODIFY, and market
   snapshot logged immediately.
5. **Research-validity governance** (26.6). Nothing is promoted because it
   won after many tries.
6. **Security Master:** one canonical instrument identity layer (ticker/
   CUSIP/ISIN/FIGI/IBKR conid/vendor IDs, currency, multiplier, underlying/
   expiry/strike, corporate actions, futures rolls). Required for correct
   point-in-time joins and IBKR reconciliation.
7. **Decision eligibility ≠ report eligibility.** A report may publish
   degraded (`REPORT_OK`); a recommendation depending on missing/stale
   inputs is `DECISION_BLOCKED`.
8. **Ground truth ≠ LLM labels.** Labels typed deterministic /
   human_verified / model_consensus / llm_inferred; LLM interpretation is
   never silently promoted to fact, learning ground truth, or policy.
9. **Champion/challenger:** the LLM may diagnose and propose continuously;
   production thresholds, signal rights, source weights, prompts, and model
   versions change only by explicit promotion with a change log.
10. **Freeze further broad design** after this part plus the complex-data
    contracts.

## 26.3 Canonical flow and state semantics

RAW PAYLOADS → FACTS (point-in-time, normalized) → FEATURES (deterministic)
→ CLAIMS/HYPOTHESES (typed epistemically) → MARKET STATE → OPPORTUNITY →
DECISION → EXECUTION → OUTCOMES → LEARNING. Deterministic wherever feasible
(facts, transforms, mechanical regimes); Claude's interpretive state is
separate and labeled. **Blind-generation rule:** form the current
market-state interpretation blind to the prior narrative; compare only
after.

## 26.4 Universal Data Semantics Contract (every complex source)

OBSERVATION_TYPE (observed/calculated/inferred) · OBSERVATION_PERIOD ·
SOURCE_TIMESTAMP · AVAILABLE_AT · FETCHED_AT · timezones + exchange
calendar/session date (UTC canonical storage) · REVISION_POLICY · UNITS ·
METHODOLOGY_VERSION · ENTITLEMENT/TIER. **Signal independence:** confluence
counts independent *mechanisms*; each signal classified independent-
mechanism / independent-measurement / correlated-echo. **Signal rights:**
every signal has native horizon + information half-life; outside them it may
display as context but cannot affect a decision.

## 26.5 Epistemic and hallucination controls

Data-bearing numbers in prose originate from fact/metric objects — Claude
references fact IDs, the renderer inserts values. Numeric/directional audits
and golden-file canaries remain as secondary controls. Event narrative
statements typed FACT / INTERPRETATION / EXPECTED FOOTPRINT / CAUSAL
ATTRIBUTION; a matching event record is association, not causality. **The
white-paper library stays OUT of runtime context** — operationalized through
a compact claims registry (claims + falsifiers + supporting/contradicting
evidence links).

## 26.6 Research validity (the overfitting safeguard)

research_register: hypothesis_stated_before_test, mechanism_id, primary
metric/horizon/threshold, benchmark, development vs validation samples,
variants_attempted (ALL of them), status. Rules: pre-register primaries ·
frozen holdout no optimization touches · walk-forward as primary evidence ·
purging/embargo for overlapping horizons · challengers must beat simple
baselines by a meaningful margin · regime-conditioned granularity requires
adequate effective n — stay broad rather than invent precision.

## 26.7 Continuous learning engine

Every decision is a learning example (state, signals + quality, hypotheses,
consensus, portfolio, recommendation, confidence, **edge_type**, expression,
outcome at multiple horizons, error decomposition). Edge types: information /
expectation / structural / positioning / liquidity / behavioral / carry /
convexity / timing / execution — so the system learns WHICH edges it has,
not one hit rate. Lessons stored with evidence n, scope, contradictions,
expiry; analogue retrieval is mechanism-first, point-in-time only, itself a
versioned model that must prove it helps. Error decomposition: forecast /
timing / expression / sizing / execution / exit / process — **never downweight
a signal for an expression, execution, or operator-override loss.** Grade
serious NO-TRADEs and misses; counterfactuals labeled fully_executable /
approximately_executable / theoretical_only. Independent evaluation: the
model that recommended does not control its scoreboard.

## 26.8 Signal additions (closed list) and the moratorium

**No new generic sentiment surveys, oscillators, valuation metrics, broad
liquidity composites, crypto-cycle indicators, geopolitical indices, or
news-sentiment scores** absent a demonstrated live decision gap. The nine
sanctioned families: Treasury intermediation pressure (1, swing conditioner)
· basis-trade stress (2, risk/size/tail) · mortgage convexity/MBS basis (3,
rates conditioner) · FX-hedged Treasury attractiveness (4, global/rates) ·
TRACE transactional credit breadth (5, swing) · rates vol surface (6,
expression/risk) · consumer-credit dispersion (7, monthly) · cross-asset
shock ownership (8, diagnostic) · reaction-function drift (9, high-value
edge/transition).

## 26.9 Complex-data mechanism contracts (v10 = implementation spec)

Required conclusions, binding: **Dealer** — settled OI vs effective OI vs
flow polarity separated; four Greeks ≠ four votes; entitlement probe before
the logger; independent recomputation. **Treasury/rates** — supply,
intermediation capacity, funding, positioning, price response separated;
mixed clocks labeled; auction tail requires timestamped WI; indirect bidder
≠ foreign buyer. **Events** — occurred/published/first_seen/classified
times; GDELT is discovery, not clock of record; canonical events ≠ source
articles. **CFTC** — Tuesday state/Friday knowledge; classes ≠ intent;
futures-only ≠ delta-adjusted; risk-normalize. **SEC/XBRL** — context,
units, taxonomy, accession, amendments preserved; no forced cross-company
comparability. **Crypto** — venue universe/units/weighting/coverage stored;
ONE leverage state, not raw-vote counting. **TRACE** — explicit traded-issue
denominator; customer-side semantics; duration contamination separated.
**Vol surface** — canonical skew/event-premium/expected-move/VRP
construction; quote-quality gates; constant maturity ≠ actual expiry.

## 26.10 Source intelligence

Tiers A0 (machine-readable primary) → A1 → B (global wires) → C (specialist/
local) → D (desks) → E; **lower tiers never overwrite higher-tier facts.**
`source_registry.yaml` with geography, domain, latency, timestamp
reliability, license, allowed reports, epistemic role. Desk Views Engine:
track stance/target/mechanism CHANGES; unchanged repetition compresses;
grade only `gradeable_call=true` (direction/range + horizon + reference
date); stable Core Panel + rotating Challenger Panel — recent accuracy never
eliminates dissent. Institutional Positioning Engine (CFTC, OFR/Form PF,
13F, 13D/G, N-PORT, TIC, regulator intel) with populations kept distinct.
Manager panels: ex-ante inclusion, retain closed/failed managers
(survivorship). BIS becomes a core Monthly source; JP/EU/UK/CN get
first-class local primaries. **Global Capital Flow is a state vector, never
one summed score.**

## 26.11 IBKR: four read-only services + Gate 1.5

Before any order authority, IBKR is: Portfolio Truth (positions, marks,
NAV, margin, buying power) · Portfolio Risk (actual Greeks + factor/currency
exposures) · Expression Intelligence (bid/ask, IV, What-If commission/
margin) · Execution Evaluation (fills, arrival price, slippage). **Gate 1.5
(new, between read-only sync and paper trading):** join live positions to
recommendation IDs or classify discretionary/legacy/hedge/unmatched;
aggregate real book Greeks; What-If previews; permit **RESEARCH-VALID /
EXPRESSION-INVALID** when live economics destroy the trade; capture fills so
performance decomposes thesis → entry → expression → execution → exit →
costs. LLM outside order construction/submission at every gate.

## 26.12 Output discipline deltas

**Daily:** render what changed + minimum standing context; freshness/age on
every non-live input; dealer regime/ladder/local-map/delta/quality; rates
with explicitly lagged CFTC/dealer context; credit classified healthy /
rates-driven / hidden deterioration / liquidity stress / recovery;
REPORT_OK / DECISION_BLOCKED rendered. **Weekend:** owns 1–3 weeks; uses
POST-EXPIRY dealer state, not Friday's expiring headline GEX; event-chain
advances/contradictions and failed expected footprints; **retrieve lessons/
analogues before finalizing the swing thesis**; INTACT/STRAINED/INVALIDATED
with revisions as new records. **Monthly/Asset:** surprise ranking + hard
word budgets; international primary matrix by construction; capital-flow/
positioning/BIS as structural context, never tactical triggers; every major
thesis states market expectation, Chester read, difference, evidence basis,
what changes the view.

## 26.13 Portfolio and trade governance

Thin portfolio-risk engine pulled FORWARD: aggregate beta, duration/
long-yield, growth, inflation, USD, credit, liquidity, vol, momentum,
AI-theme, crypto, commodity exposures; simple book-level shocks before any
optimization. **The composite does not size trades until live calibration
shows score predicts outcomes.** Confidence decomposed (data / mechanism /
history / independence / timing / execution). Every recommendation states
edge type, horizon, catalyst, payoff, invalidation, portfolio interaction,
expression economics. **Abstention is explicitly graded.**

## 26.14 Completion gates — v17 is not trustworthy until all ten

1 point-in-time store + one as-of join path · 2 Security Master for all v17
instruments · 3 signal rights/horizons/mechanism groups/source semantics
validated · 4 decision register + Decision Packet from first live
recommendation · 5 deterministic factual rendering + audits · 6 dealer
logger under VERIFIED entitlement/methodology · 7 rates/event contracts
enforced · 8 heartbeat + REPORT_OK/DECISION_BLOCKED logic · 9 naive
benchmarks logged from day one · 10 learning memory + champion/challenger
change log initialized.

## 26.15 Explicit deferrals (until evidence)

Fine-tuning · granular auto-reweighting at small n · unattended IBKR
execution · Alpha-tier flow polarity (unless ambiguity proves costly) ·
paid data without a demonstrated recurring decision gap · **additional white
papers or indicator families** (planned papers XVI–XVIII remain as
documentation work, not architecture) · a single Global Capital Flow score ·
granular analogue rules before live examples · behavioral conclusions about
the operator without observed decision data.

## 26.16 Acceptance test (before declaring frozen)

1 **Replayability** — reproduce an earlier run exactly from its Packet.
2 **No-leakage** — historical episodes use only information available then.
3 **Decision governance** — a missing critical dependency blocks the trade
while the report still publishes. 4 **Learning governance** — an
LLM-proposed rule change stays a challenger until explicit promotion.
5 **Execution realism** — a valid thesis is rejected on real IBKR spread/
margin/commission/concentration.

## 26.17 Standing instructions to the build

Preserve strong existing architecture unless this part changes it · never
independently expand scope; surface conflicts, prefer the simplest
implementation that satisfies the gate · verify vendor docs before coding
against them; store entitlement/methodology versions · most of this part is
storage/governance/validation, NOT new report sections · deterministic code
for arithmetic/scoring/joins/rendering/orders; LLM for synthesis, hypothesis
generation, comparison, post-mortems · update the Master Schedule each
session with actuals and discovered dependencies · after v17 runs live,
observed decision gaps — not enthusiasm — elevate the backlog.

---

# Part 27 — Prediction Market Intelligence Engine (post-freeze amendment #1)

*Principal-directed addition, 4 Sep 2026. Recorded as the first amendment
after the Part 26 freeze — admitted as a SOURCE-intelligence layer under
§26.10 (a source with signal rights), not a new signal family; §26.8's
moratorium stands. The bar for amendment #2 is a demonstrated live decision
gap. Scope: modest, cross-cutting, read-only — no venue accounts, no
prediction-market trading.*

## Purpose — three extractions

1. **Market-implied event probabilities and their changes** — probability,
   1d/7d change, volume, depth, time-to-resolution, cross-venue dispersion.
   Changes in probability and participation outrank levels. These are
   market-implied beliefs, never facts and never mere "sentiment."
2. **Emerging-risk discovery** — ingest newly created and fastest-growing
   contracts; classify: already-covered / existing tail scenario /
   known-issue-with-material-Δp / genuinely new / noise-entertainment.
   Serious new issues feed `coverage_gap` and the tail-scenario review. The
   quantitative twin of the Broad Media Scan, which already validated the
   discovery pattern.
3. **Disagreement as signal** — cross-venue dispersion, parent/child and
   mutually-exclusive-set inconsistencies, conditional-market
   inconsistencies, and PM-vs-conventional (rates, options, surveys, desk
   consensus). Investigate disagreement; never blindly average venues.

## Derived metric — Prediction-Market Attention Shock

Factors: new-market creation, Δp velocity, volume acceleration, liquidity
growth, related-market proliferation, cross-venue confirmation. **It
identifies what people are suddenly willing to bet on; it never establishes
that the thing is true.** **Quarantine rule (hardening beyond the source
memo):** a shock is CONFIRMED only with cross-venue agreement OR
volume+liquidity above declared thresholds; single-venue thin-market shocks
render as UNCONFIRMED and cannot create a coverage_gap alone — thin books
get painted to manufacture narratives.

## Storage (per tracked market)

market_id · venue · question · **resolution_source +
resolution_criteria_text (verbatim)** · **economic_question_match:
exact|proxy|loose** · created_at · close_at · probability · Δp_1d · Δp_7d ·
volume · open_interest · bid_ask · depth · resolution_clarity ·
liquidity_quality · market_age · manipulation_risk · **bias_zone flag
(p<10% or p>90% — documented longshot-bias region; use changes, distrust
levels)** · related_event_id · mechanism_id · native_horizon · available_at.
Data Semantics Contract (§26.4) applies in full.

**Hard rule: no contract maps to a tail scenario without the resolution
criteria read.** Contracts resolve on technicalities; "ceasefire"
definitional disputes are the canonical case and directly touch scenario 7.

## Signal rights (v1 — narrower than the source memo)

MAY: describe market-implied probability · measure expectation changes ·
identify emerging risks · create coverage gaps (confirmed shocks only) ·
update tail-scenario STATE (probability histories beside our bands).
MAY NOT: establish occurrence · establish causality · trigger a trade ·
**modify thesis confidence** — that is a production-policy right and enters
as a champion/challenger candidate only after the resolution archive shows
venue/topic calibration (26.2.9). The chain is always: probability shock →
primary sources + market footprint → corroborate → update thesis.

## Reporting

**Daily (Backdrop block):** only changes materially touching a live thesis,
scheduled event, portfolio exposure, or tail scenario. **Weekend:** largest
Δp, newly active serious markets, cross-venue disagreements, new coverage
gaps. **Monthly/Tail:** probability histories per major scenario, rendered
BESIDE our scenario bands — market-implied vs Chester state, divergence
noted, neither auto-defers. **First consumer: the midterms (~9 weeks) —
election probabilities are these venues' strongest suit.**

## Continuous learning

Archive full probability path + resolution for every tracked market. Over
time: calibration by bucket / venue / topic / liquidity; whether Δp beats
levels; whether disagreement predicts; whether PM-vs-conventional divergence
carries incremental edge. End state: a **Conditional Prediction-Market
Atlas** — reliability by venue×topic — which is also the promotion evidence
for the confidence-modification right. Atlas is deferred by construction
(needs resolutions to accumulate).

## Build placement

Fetchers (Polymarket + Kalshi public APIs; movers + new-market endpoints)
extend Session 9's events layer (~+1h). Classifier + coverage-gap wiring in
Session 15c (~+1h). Weekend section in 15a (~+0.5h). Tail-history lines in
the Monthly renderer (~+0.5h). Calibration archive: schema now, evaluation
deferred. **~3h total inside existing sessions; nothing enters v17's core
gates.**

---

# Part 28 — Full-stack report automation (post-freeze amendment #2)

*Source: "Automation Addendum — Full-Stack Report Automation" (4 Sep 2026),
committed to `docs/` as the source document; this part is the operative
integration and controls on conflict. Classed as principal-directed
amendment #2 — consistent with the Part 26 freeze because it adds NO new
signals or indicators, only production automation built from primitives the
architecture already has: the publish gate is the Paper/Shadow/Live pattern,
drafted setups are register entries, the DT composite proposal is
champion/challenger. The human gate moves from production to decisions —
reports are not orders, and the Brookfield restriction binds every automated
recommendation path at register write-time as everywhere else.*

## 28.1 The universal pattern — the publish gate

Every report pipeline ships with `auto_publish: false|true`, per report, same
code path either way. Everything starts gated (drafts + notification;
operator approves); each report is flipped individually when its drafts have
earned trust. Worst case for any report is "automated with a 10-minute
review" — no report is ever manual again.

**Standing defaults (proposed in the addendum, adopted here; overridable per
report at any time):** Daily → true when earned · Alt Asset → true when
earned · Monthly and Top & Bottom → true (already effectively are) ·
**Disruptive Themes → false permanently** — it caps sizing for the whole
stack, refreshes six times a year, and its composite is judgment-scored by
design; sixty minutes of forced argument with a drafted steelman is the one
place in the stack where the human is the feature.

## 28.2 Daily Cascade — the Monthly's pattern, nine times a day

VPS systemd timers (ET): 0700 Morning Brief (Direction/Backdrop + cross-
report sync) · 0920 Pre-Open (Market Base) · 1000 Open (Confirmation, 10AM
GEX) · 1200 Midday (Confirmation) · 1500 Into the Close (Execution — MOC,
pin) · 1630 Debrief (Execution + carry-forward computed FROM THE STORE,
prior run as input — the learning loop closes without an analyst) · 2130
Night Watch (Backdrop) · Fri 1800 Weekly Reflection (**register-driven
grading — the Friday report becomes a query with narrative on top; automated
grading has no memory of how the week felt**) · Sun 2130 Forward Plan.
Sonnet intraday, Opus for the two weekly syntheses; order-of-magnitude
$1–2/day — verify pricing at build time.

Per-run: fetch (yfinance intraday set, GEX logger snapshot with
refresh-vs-inherit labels, state files, events ingest) → point-in-time store
with `available_at` BEFORE the LLM sees anything → validator (failures stamp
the affected block `DATA DEGRADED`, never a silent gap) → constrained block
narratives (no figures outside the payload) → render + state file + alerting.

**The judgment fields:** drafted setups and conviction enter the register as
`status: draft` with a full Decision Packet — `REPORT_OK` publishes,
`DECISION_BLOCKED` holds the trade idea until a phone-action approval.
**Decision recorded (addendum decision #2): yes — drafted Daily setups
auto-enter the register as drafts**; it is what makes the Friday grading
complete.

**Prerequisite, restated:** the run-state inventory (what fires today, from
where, what dies when cron-job.org retires) happens inside out-of-band item
4 before any of this is built on an unconfirmed pipeline.

## 28.3 Disruptive Themes — automate the mechanical, gate the judgment

Bimonthly pipeline + trigger-fired early runs: **Stage 1** instrument panels
auto-refresh from the store, gaps render as GAP cells, never pretended.
**Stage 2** scheduled research pass (API web search): per-factor dispatch,
media scan, external-lens updates — structured cited notes, stored, not yet
prose. **Stage 3** Opus draft via the Master Refresh Prompt (already the
report's own appendix — which is what makes this stage possible): factor
objects rewritten, composite and scenario-probability changes proposed as
EXPLICIT DELTAS with rationale. **Stage 4** review gate, permanently
`auto_publish: false`: diff view prior-vs-proposed; the auto score is the
challenger, the standing score is the champion, promotion is the operator's
click; 30–60 minutes per refresh, down from the better part of a day.
**Stage 5** publish + state + dashboard on approval.

**Early-refresh triggers go live:** the Master Narrative's drift conditions
(overlay ACTIVE >30d, correlation break >30d, Monthly composite drift >0.5,
regime↔matrix mismatch) become job triggers scheduling out-of-cycle Stage
1–3 runs. Bimonthly becomes a floor, not a ceiling.

## 28.4 Alternative Asset — completion, not redesign

"Automation for all reports" includes retiring the synthetic fetchers (numpy
seed 7 still feeds the dashboard): ETF-flow, COT, on-chain and news-scan
layers go live per the existing source catalog; `pipeline_health` flips
`partial` → `full`; the weakest-link disclosure stands until then.

## 28.5 Sequencing (the schedule governs)

A1 Daily runs onto VPS timers — inside the Part 25 migration, one report at
a time · A2 Daily narrative + register-draft wiring — ~2–3 sessions
(~6–8h), AFTER the store (S5) and grading harness (15b) · A3 DT Stages 1–3
+ review-gate UI — ~3 sessions (~7–9h) · A4 Alt Asset live fetchers —
existing Session 11 scope, unchanged.

---

# Part 29 — Change Order #3: Eight Tactical Additions (post-freeze amendment #3)

*Principal-directed, 5 Sep 2026, ruled item by item in session. Admitted
under §26.10 as sources, entities, composites, and one register book —
**no new signal family**; §26.8's moratorium holds. Every item was reviewed
against a written external recommendation and adapted on the same four
rules: (1) regime state machines with declared thresholds replace weighted
0–100 composites; (2) correlated confirmation counts once (§26.9); (3) no
unsourced metric enters the registry — substitutes or `not_yet_sourced`;
(4) paid data only after free data demonstrates a named gap. Five
weighted composites were declined (yen, cohort, PMSS, ICS, MCC).*

## 29.0 Shared primitive — response per unit of stimulus

Four items independently reduce to the same computation: **how much
response a unit of stimulus buys, and whether that ratio is deteriorating.**
MOC absorption (price displacement / normalized imbalance), Dell
revision-velocity vs price-velocity, meme attention divergence (price
response / mention surge), and PM–asset divergence (asset move /
probability move). Implement once as `response_ratio(stimulus, response,
window)` with a declared baseline and a deterioration flag; the four
items call it. `observation_type: calculated`.

## 29.1 Yen Carry Stress Monitor → composite in the `global` pillar

Four-state regime machine — NORMAL / ELEVATED / UNWIND / SYSTEMIC —
escalated by the count of active **mechanism groups (one vote each)**:
FX velocity (USDJPY, AUDJPY, EURJPY 5d/20d yen-appreciation, declared
2/4/6% first cuts with percentile calibration vs 1998 and Aug 2024) ·
positioning (CFTC TFF leveraged-fund JPY, percentile vs 3y/5y — joins with
Session 16) · FX vol (**FXY options through the exposure engine**: IV and
skew as the risk-reversal analog) · Japan rates/BoJ (MOF daily JGB CSV;
BoJ-decision probability **from Part 27 contracts**) · risk-asset
confirmation (Nikkei + NDX + SOX + HY OAS as ONE group) · plumbing (MOVE,
dealer gamma regime, cross-asset correlation). ORANGE needs three groups,
RED five. Carry-unwind vs capital-repatriation distinguished as separate
lines. Dropped as unsourceable: CTA/vol-control estimates, Treasury depth.
Rendered as a Weekend/Tail "funding-stress view" over EXISTING pieces — not
a new category. Rights: sizing conditioner + tail-state input; may raise a
hedge-review flag; never triggers. Horizon swing; half-life session
(velocity) / weekly (positioning). Language kept verbatim: *"an amplifier
of global deleveraging, not a stand-alone crash signal."*

## 29.2 Speculative Cohort Monitor → `internals` + Session 14 + `tracked_entities`

Membership by declared screen, not by list — three rules feeding ONE cohort
registry: momentum-fundamental (12m return and multiple-expansion share
above thresholds), retail-attention (29.3), meme-lifecycle (29.7). Exited
names kept (Session 19 survivorship rule). Seed: DELL, NVDA, SMCI, AVGO,
HPE. Dell's declared role: **bellwether for hyperscaler capex converting to
realized server revenue/backlog** — `kill_condition`: backlog conversion
stalls. Per name, two clocks: quarterly fundamentals (events ingest; backlog
from filings tagged `inferred` where qualitative) and daily/weekly crowding
(engine call skew, OI concentration, 0DTE share, IV percentile; FINRA short
interest biweekly; cross-name correlation). Core computation: **return
attribution — estimate-revision change × multiple change** — and the
second-derivative flag (revision velocity decelerating while price velocity
accelerates). **Forward-only:** nightly logging of consensus EPS / forward
P/E starts now; decomposition reads `insufficient_history` until Q4.
Cycle-maturity read = leaders-vs-adjacents multiple-expansion spread.
Declined: 0–10 Speculative Temperature; "narrative simplification" and
social attention unless sourced (29.3 sources it).

## 29.3 Retail Trading Activity → `sentiment` family, source #5

Nasdaq Data Link **RTAT10** (free; daily top-10 retail activity share +
−100/+100 sentiment; **history to 2016 — the rare historied source**;
percentiles seed day one; backtestable vs 2021/2022). Registry flag
`sample: top10_censored` on every derived metric — head of the
distribution, never market-wide breadth. Derived: concentration,
persistence (consecutive days in top 10), new-entrant shock, price/retail
divergence (via 29.0), meme-cohort heat (merged into 29.2's registry).
Institutional-vs-retail waits for Session 19 13F. Nasdaq enters the source
registry as an adapter with per-dataset probes **on demand against a named
gap** — the standing "discover and test premium samples" crawler is
declined as a data-shopping loop; 26.2.9 champion/challenger is the
evaluation engine. Caveats recorded: Nasdaq aggregates central-bank data
FRED serves better; legacy WIKI is discontinued.

## 29.4 Market-on-Close → intraday cadence + pin log + T&B

Absorption is the metric (indicative-price displacement per unit of
normalized imbalance, via 29.0); raw imbalance is display only. Price × flow
four-regime matrix (confirmed accumulation / bearish divergence / confirmed
distribution / bullish divergence) is the state. **Event classification
table** in `altdata/session.py` beside the holiday table: NORMAL /
MONTH_END / QUARTER_END / INDEX_REBALANCE / OPEX / TRIPLE_WITCHING /
ETF_REBALANCE — a reconstitution-day imbalance is never discretionary flow.
Data: **IBKR auction-imbalance ticks through the Gateway** (probe first) for
the universe, SPY/QQQ/IWM, and sector ETFs (XLK, XLF, XLI, XLE, XLV, XLU,
XLP, XLY) as the rotation proxy; opening-auction ticks free from the same
path. `not_yet_sourced`: market-wide auction breadth, constituent-weighted
flow. New cadence: **15:50–16:00 sampler at ~30s** on the VPS (absorption
needs the curve). Forward-only; 5d/20d CAP readable in weeks. Four
strategies registered as dated **hypotheses**, not builds: Absorption
Reversal, Pressure Continuation, Price/Flow Divergence, Sector Rotation.
Rights: execution-horizon conditioner, overnight-persistence read; CAP
feeds T&B once historied; never triggers. Confluence note: MOC flow and
dealer gamma are genuinely independent mechanisms — two votes. Declined:
ICS ±100 composite.

## 29.5 Privacy-Coin Theme → Alt Asset crypto block sub-theme

ZEC price/realized vol/beta to BTC (yfinance), share of crypto cap,
**shielded-pool transaction share** (Zcash explorer API — the use-vs-
speculation metric; probe first), hashrate/difficulty, exchange-listing
count as the regulatory gauge, XMR as the delisted peer, Part 27 contracts
where they exist. Existing family.

## 29.6 Digital-Asset-Treasury entity type → `tracked_entities`; CYPH as instance #2

Generalize the MSTR template: holdings, cost basis, **fully-diluted share
count with warrants and ATM as first-class fields**, mNAV, premium/discount,
**asset-per-fully-diluted-share as the primary KPI** (total holdings are a
vanity metric under an ATM). CYPH adds mining hashrate share with implied
monthly production under a declared share-decay assumption, and the
treasury → mining → issuance loop as a named reflexivity flag. Every figure
from the source analysis (323,394 ZEC, $341.83 basis, 107.8M shares, 43.29M
warrant, 4.2 GSol/s, $33.3M) enters the **claims registry (26.5)** as a claim
with its filing as source, verified via EDGAR before any report cites it.
DAT premium across vehicles = third cohort membership signal. CYPH joins the
chain universe subject to the liquidity floor. Rights: crypto conditioner;
DAT premium feeds T&B as a sentiment extreme; the cohort sizing cap applies
to any personal position.

## 29.7 Meme / Crowding Lifecycle → cohort layer + **opportunistic book**

**Lifecycle state machine replaces the MCC composite:** dormant → emerging →
ignition → acceleration → squeeze → euphoria → exhaustion → unwind →
dead-cat, transitions declared on three axes — attention velocity (Δ, Δ²
mentions), positioning tightness (SI, CTB change, availability change),
price/volume response. **Each phase carries permitted expressions:** long
squeeze only in ignition/acceleration; shorts only in exhaustion/unwind
with borrow improving; **DO_NOT_SHORT flag** whenever CTB rises or
availability falls, regardless of valuation. Attention divergence (29.0) is
the exhaustion tell. Sources, free tier first: ApeWisdom (discovery, mention
acceleration), FINRA (semi-monthly SI anchor + Reg SHO daily short volume,
with "daily short volume ≠ short interest" encoded), **IBKR borrow data via
the Gateway as a time series** (shortable shares, fee rate — the
tradability layer no vendor reproduces), Massive volume anomalies, the
exposure engine (call skew, 0DTE share). ORTEX unlocks only when a logged
case shows FINRA's lag cost a setup; Quiver, X, Reddit-direct, Stocktwits
declined. Discovery is a funnel (ApeWisdom movers + volume anomalies + short-
volume spikes → ~a dozen candidates → enriched), never a universe scan.
Board: a small block in Part 28's 07:00 and 09:20 runs, allowed to say "no
candidates." Breadth of names in ignition-or-later feeds T&B as cycle
maturity.

**Register rules for the opportunistic book (condition of admission):**
`book: opportunistic`, `edge_type: behavioral`, horizon intraday/swing;
declared sizing cap in config (per-name and aggregate % of NAV — numbers
set by the principal, not at 09:31); **short invalidation includes borrow
conditions** (CTB above X or availability below Y invalidates even if price
hasn't moved); **meme shorts default to defined-risk** — a bare short is
flagged by the expression check with the unbounded-loss note; attention
metrics `half_life: intraday` so DECISION_BLOCKED refuses entries on stale
mentions; the three strategies (squeeze long, exhaustion short,
attention-divergence short) register as hypotheses graded through
close_decision.

## 29.8 Prediction Market Engine — phase 2 (extends Part 27)

Adopted from the fuller brief: **cross-asset divergence engine** (PM
repriced → expected transmission → observed response → divergence, via
29.0; the five candidate explanations logged as the investigation template;
never assume the PM is right) · **canonical-event abstraction** above
contracts (where resolution-criteria-verbatim lives) · **asset transmission
map** as declared config extending Session 8's event chains, quarterly
review — not "learning" · **news-divergence classification** (NEWS_CONFIRMED
/ NEWS_LED / PREDICTION_MARKET_LED / FLOW_DRIVEN / UNEXPLAINED) · **lead/lag
analysis** in the calibration archive — the test that can retire a
venue-category. **ForecastEx via the IBKR Gateway** as a third real-money
venue, read-only. Declined: PMSS 0–100 and EVENT_IMPACT 0–100 (impact = a
declared tier from transmission-map reach); 1H/6H horizons and continuous
polling (daily/weekly/monthly ΔP; intraday only inside a declared event
window); eight dedicated tables (snapshots are observations in the store;
maps are config); Tier-2 venues as confirmation (Metaculus, Manifold,
PredictIt = discovery only); weight-tuning monthly review (26.2.9 instead).
**Gated on Part 27 v1 running through one live event**, so the transmission
map's first entry is an observed case.

## 29.9 Build order and hours

Ordering rule: **forward-only loggers start first** (every day unlogged is
lost); probes before wiring; nothing displaces Tuesday's debut check.

| # | Item | Hrs | Gate / dependency |
|---|---|---|---|
| 1 | RTAT10 fetcher + 2016 backfill + derived metrics (29.3) | 2 | free key; historied — do first |
| 2 | Cohort registry + nightly consensus logging + return attribution (29.2) | 2 | starts the estimate-history clock |
| 3 | Probes: IBKR imbalance ticks (29.4) and IBKR borrow fields (29.7) | 1 | Gateway, read-only |
| 4 | `response_ratio` primitive (29.0) | 1 | — |
| 5 | Yen monitor v0 — five groups, FXY chains, JGB CSV (29.1) | 2–3 | positioning joins with S16 (+1h pull-forward) |
| 6 | Meme v0 — ApeWisdom, FINRA, borrow series, funnel, lifecycle, board, register rules (29.7) | 4–5 | probes in #3 |
| 7 | ZEC theme block + DAT entity template + CYPH instance (29.5–29.6) | 4–5 | explorer probe; EDGAR claims verification |
| 8 | MOC sampler + event table + pin-log column (29.4) | 2.5 | probe in #3 positive |
| 9 | PM phase 2 (29.8) | 5–7 | Part 27 v1 + one live event |
| | **Total** | **~24–29h** | none enters v17's core gates |

**Blocklist reminder:** nothing here touches the Brookfield restriction —
every candidate from every funnel passes the register trigger like any
other instrument.

---

# Part 30 — Audit #2 (5 Sep 2026): findings after the build weekend, and Track D

*Second architecture-and-quality audit, run after ~20 hours of build and
three amendments. Scope: durability, stability, extensibility, accuracy;
whether reporting talks to every part; data efficiency; whether the system
yields trackable recommendations with a closed learning loop even when
trades are not placed. Findings are rulings, not suggestions.*

## 30.1 Durability — three real gaps, all cheap

1. **Off-box backup does not exist.** The nightly chain zip lands in
   `~/backups/chains` — on the same disk as the data. Ruling: enable
   Hetzner's server backups (one console click, ~20% of the box price) AND
   an `rclone` nightly sync of `data/` + `~/backups/` + `~/state/` to cloud
   storage. The point-in-time store is now the system's memory; it must
   survive the box.
2. **yfinance is a single point of failure for the exposure engine** — an
   unofficial API that breaks periodically, carrying 13 of 15 symbols'
   chains and every price. Ruling: **Massive becomes the primary chain
   source for all 15 symbols** (Starter already serves all US-listed
   options; `massive_chain.py` exists), yfinance demoted to fallback and
   cross-check. Solver IV then feeds every symbol identically — which also
   collapses the `greeks_source` split. ~1h.
3. **SQLite under concurrent writers.** The timer roster now includes EOD,
   heartbeat, Portfolio Truth every 30 min, Gateway watchdog, and — coming —
   intraday, MOC sampler, and seven Daily runs. Multiple writers on one
   SQLite file produce `database is locked` failures that look like data
   gaps. Ruling: WAL journal mode, `busy_timeout`, and a repo-wide write
   lock (`flock` on a store lockfile, the EOD wrapper's pattern) before any
   new writer ships. ~30 min.

## 30.2 Stability — holding, two rules to keep it that way

The weekend's failure classes (UTC-vs-session date ×3, mtime-vs-observation
×2, silently-ignored systemd directives ×5, timestamp-precision ×2,
run_id-precision ×2) were all *identity and time* bugs, all caught by tests
or deployment, never by reading. Two standing rules: **(a)** every new
writer and every new source passes through `session_date()`, canonical
microsecond UTC, and `run_id`-on-write — no exceptions, enforced by the
registry gate; **(b)** every shipped systemd directive is asserted by the
validator (the unknown-directive trap stays).

## 30.3 Accuracy — one missing gate blocks the Daily

Numbers in the store are gated (solver, cross-check, data-quality, replay).
**Prose is not.** The Daily's LLM narrative has no anti-fabrication guard
yet — Session 4's numeral whitelist against the payload is unbuilt. Ruling:
**Session 4-lite ships before any Daily narrative publishes** — payload-
constrained generation (the Monthly's pattern), a numeral audit that fails
the block if a number appears that isn't in its payload, and a directional
check. A Daily that can invent a number is worse than no Daily.

## 30.4 Extensibility — proven, one consolidation

The registry-plus-store pattern absorbed eight additions without a schema
change; entity types (DAT) and the cohort registry (three membership rules)
generalize. Consolidation: **reports never fetch.** Fetchers are timers that
write the store; every report block queries the store as-of. This is the
data-efficiency rule — one pull per source per cadence, shared by all nine
Daily runs, the Weekend, the Monthly, and T&B — and the leakage rule at
once. Any block found fetching is a defect.

## 30.5 The learning loop — closed in code except one link

Present: register + immutable packets + set-status supersession +
DECISION_BLOCKED freshness + expression check + close_decision with the 26.7
decomposition + pin-log calibration. **Missing: automated outcomes.** Ruling
— Session 15b-lite: **every decision gets a shadow outcome at its horizon
from stored prices — taken, declined, and draft alike** — so abstentions and
unplaced drafts are graded exactly as trades are (this is what makes the
loop learn "even if trades are not placed"); taken decisions additionally
reconcile to Portfolio Truth fills. Plus a `hypotheses` table (Part 29
registers seven) with the same grading path. The Friday Weekly Reflection
is then a query over this table with narrative on top — Part 28's "biggest
quality gain" made real.

## 30.6 Reporting integration — the Backdrop needs a regime spine

Every block reads the store, but the Daily's Backdrop and T&B both need a
**macro regime state** that nothing computes yet. Ruling: `regime.py` —
a declared-threshold state from series already in the store (net liquidity,
HY OAS, curve, realized/implied vol, breadth from yfinance, dealer gamma
regime) writing `regime_state` as an observation with its own
`available_at`. Regime-lite feeds the Daily immediately and seeds the full
T&B (Sessions 10–14), which refines rather than replaces it.

## 30.7 Track D — the Daily-first sequence (~15–18h to a running Daily with Friday/Sunday and a closed loop)

| # | Step | Hrs | Delivers |
|---|---|---|---|
| D0 | Daily run-state inventory (out-of-band 4, still open); retire cron-job.org | 0.5 | nothing built on an unconfirmed pipeline |
| D1 | Durability trio: Hetzner backups + rclone off-box; Massive primary for all chains; SQLite WAL + write lock | 2 | the memory survives; one chain source; no locked-DB gaps |
| D2 | `regime.py` — macro regime state from the store | 2 | Backdrop spine; T&B seed |
| D3 | Session 4-lite — payload-constrained narrative + numeral audit | 3 | prose can't fabricate |
| D4 | Daily Cascade pipeline — block payload builders (Part 20) reading the store, render, `daily_cascade_state.json`, drafted setups → `decide.py` drafts, two VPS timers first (07:00, 16:30), the rest of Part 28's nine added as each block earns trust; `auto_publish: false` | 3–4 | the Daily runs |
| D5 | 15b-lite — shadow outcomes for every decision + hypotheses table + Friday Weekly Reflection (register-driven grading, Opus) | 3 | the loop closes |
| D6 | 15a-lite — Sunday Forward Plan: register state + regime + calendar + Part 27 v1 movers + lessons-before-decision | 2–3 | Friday/Sunday cadence complete |

**Then, in this order:** Part 29 items 1–4 (RTAT10, cohort logging, IBKR
probes, `response_ratio`) · intraday cadence (gated on Tuesday's debut +
capture-instant T) · T&B full (Sessions 10–14) for the mature regime ·
remaining v17 core (S1/S2 leftovers, S3b, ALFRED, alert delivery) · Part
29 items 5–9 · Part 28 A1/A3 · Sessions 8–9 with Part 27 v1.

Everything above D-track reuses built components — `narrative.py`, the
store, `decide.py`, Portfolio Truth, the exposure engine — which is why the
estimate is short. Nothing here loosens a gate.

## 30.8 IBKR market-data layer — ruling on the "$18.70 package"

*Reviewed against an external recommendation to subscribe IBKR's
non-professional feed bundle. The provider-role split it proposes is
already this architecture's practice; the ruling is about which feeds fill
a NAMED gap (moratorium rule 4) and which parts of the proposal are
re-architecture in disguise.*

**Provider roles (affirmed, and encoded as source-registry precedence
rows):** Massive = securities system of record (equities, options, history,
whole-market scans) · IBKR = portfolio/execution truth (authoritative) +
real-time cross-asset + auction flow + live-quote validation · FRED = macro
· Nasdaq Data Link = specialty, on-demand. Never silently average; provenance
per observation — already law.

**Feeds approved, each tied to a consumer that already exists:**
- **NYSE / NYSE Arca / NYSE MKT order imbalances ($3.00)** — required for
  the auction ticks Part 29.4 planned to probe; the probe would fail without
  the entitlement. Cheapest possible fill of a named gap. **Nasdaq Closing
  Cross (NOII) remains a marked GAP** until a route is found — NYSE-family
  data is never presented as market-wide.
- **CFE Enhanced (VIX futures, $4.50) + CBOE Streaming Indexes ($3.50)** —
  fill four of the Volatility paper's eight regime tells that were
  `not_yet_sourced`: VIX term structure (VX1/VX2/VX3 slope, contango →
  backwardation as a declared state machine), VVIX, skew indexes. Feed
  `regime.py` (D2) and the tail watch. The state transitions, not the
  level, are the object.
- **CME L1 ($1.55)** — ES/NQ/RTY overnight returns, gaps, and cash/futures
  basis for the Daily's Market Base block and the 07:00 Morning Brief.
- **OPRA L1 ($1.50)** — real-time option quotes for the **intraday cadence
  only** (09:45 0DTE refresh, where Massive's 15-minute delay bites);
  Massive stays the options warehouse — no second one.
- **FX ($0)** — USDJPY/AUDJPY/EURJPY intraday for the yen monitor's velocity
  group during stress; JPY=X daily remains the EOD source.

**Deferred (no named consumer at EOD resolution yet):** CBOT, NYMEX, COMEX
— yfinance's delayed continuous futures serve the rates, energy, and metals
pillars at daily cadence; revisit when an intraday consumer names them.
Approved spend: **~$12.55/month now**, full $18.70 when the deferred three
earn a consumer. Data-sharing from the live account to paper stays on.

**Ops constraint to encode:** IBKR market-data *lines* are capped (100
concurrent by default; more cost money). CAP-SPX at full constituent breadth
is infeasible on that budget; Part 29.4's scope stands — universe + index
ETFs + sector ETFs, with SPY's own auction and Arca ETF flows as the
market-wide proxy. The line budget is a registry-level fact, not a
surprise for the sampler to discover.

**Adopted as additions the proposal surfaced:**
1. **Executions, fills, and commissions into Portfolio Truth** (read-only)
   — enables **execution-quality analytics** in D5: slippage vs
   decision-time price, implementation shortfall, fill-vs-limit — which is
   what makes the 26.7 decomposition's *execution error* measurable rather
   than estimated. Gate 1.5's stated purpose, finally with data.
2. **Portfolio-impact line** — every regime change and alert annotated
   with the held book's sensitivity (beta, net delta/gamma from Portfolio
   Truth × the exposure engine): "what does this mean for what we own."
   Small, and it makes the Daily read as advice to a portfolio rather than
   commentary on a market.
3. **Standard derived forms as a registry convention** — level, own-history
   percentile, z, momentum, acceleration, divergence, regime, anomaly,
   confidence — computed by one generic function for any registered metric
   (the `response_ratio` pattern generalized). Not a new layer: a
   convention over the store.
4. **ETF-vs-underlying closing-flow divergence** (Arca) as a 29.4 metric.

**Declined:** the proposed layer stack (raw → normalization → domain
engines → standard signal layer → cross-asset fusion → master system) as a
rebuild — the store, registry, pillars, `regime.py`, and T&B already *are*
those layers under other names; "auction flow as a new signal family" —
Part 29.4 admitted it as a flow/execution conditioner and that
classification holds; CAP-* aggregates beyond the line budget. The
"independent witnesses" principle (§20) is affirmed as a restatement of
§26.9 — it is already the rule that made five composites unnecessary.

---

# Part 31 — Library additions and the report changes they require (6 Sep 2026)

*Three papers were written after Audit #2 — Base Rates, International Equities, and the two Draft-1 editions of Positioning & Flows and Building and Validating a Systematic Book. Papers are reference, not code, and most of what they contain changes nothing. This part records only the places where a paper obliges the SYSTEM to change: a new series to log, a new field, a new report line, or a rights entry. Everything else in those papers is consumed by reading.*

## 31.1 Base Rates → a computed reference, not a static document

**The problem the paper creates.** A base rate cited in a decision packet must be replayable as of the date it was cited, or the packet's replay guarantee is void the first time a table is updated. A paper's tables are prose; the register needs observations.

**Ruling.** `tools/base_rates.py` computes the paper's Part I and Part II tables from series already in the store — return distributions at four frequencies with p25/median/p75, intra-year drawdown distribution, drawdown frequency and duration by depth band, streak and gap statistics, correlation by regime, VIX distribution — and writes each as an observation with `available_at`, `registry_key: baserate.*`, `observation_type: calculated`, `native_horizon: strategic`, `half_life: permanent`, `revision_policy: recomputed`, `trigger_eligible: false`. Recomputed annually by a scheduled job and on any methodology change. **A base rate that moves by more than a declared tolerance on recomputation is flagged for review** — a changing base rate is itself information. Figures the system cannot compute (the pre-1970 episodes, the international drawdowns, the literature citations) enter the **claims registry (26.5)** with their sources, not the observation store.

**Report consequences.**
- Every report that states a magnitude gains the option of stating its percentile against the base rate — "a 2.1% decline, 88th percentile of daily moves" — and the Daily's Backdrop block adopts it as a standing convention.
- The Top & Bottom report's top-side language carries the **bear-rally base rate** (three to five 5%+ counter-trend rallies inside a −20% decline; p75 of the largest is +16%), because that governs how a top call is *held* rather than made.
- The `decide.py` packet gains an optional `base_rate_cited` field, so a variant-perception thesis records the consensus it departs from.

## 31.2 Base Rates Part IV → the long-cycle tail scenario, with two branches

**Ruling.** The tail watch gains a standing scenario, **long-cycle debt resolution**, with two mutually exclusive branches that share antecedents and have opposite instrumentation:

| Branch | Destroys | Protects | Distinguishing tell |
|---|---|---|---|
| Deflationary liquidation | Equities, credit, real estate | Long governments of the solvent sovereign, cash, gold after revaluation | Falling inflation with rising real yields; currency strengthening |
| Inflationary repression | **Bonds and cash in real terms** | Gold, commodities, real assets, equities partially | Nominal yields capped below inflation; persistent negative real yields; gold rising against real yields |

The observables are already in the store or are cheap to add: federal debt/GDP and its full-employment trajectory, the structural deficit, **net interest as a share of revenue**, the foreign-official share of issuance absorption, term premium behavior when growth expectations fall, real yields versus inflation, and gold against real yields. **Ruling: these are read together as one mechanism state, not as separate pillar rows** — a `regime.debt_cycle_state` output of the regime engine (D2), with `observation_type: inferred` and the honest counter-case (no demonstrated debt/GDP threshold; Japan at twice the ratio; the reserve-currency exception) carried in the registry note.

**And the sizing consequence, which is the operative one:** the Doctrine's duration sleeve is a *deflation* hedge specifically, and the two branches want opposite instruments. Book A's Contraction band raises duration for the first branch and is the wrong instrument for the second. The tail-hedge budget's expression therefore depends on which branch the state reads — recorded as a rule so the choice is not made under stress.

## 31.3 International Equities → three concrete system changes

**(a) Overnight gap attribution — a new Backdrop line, and the cheapest win in the paper.** The 07:00 report currently reports the gap. It will now attribute it: the Tokyo session's close-to-close move, the European session's move at the time of writing, the futures move outside both, and the release or headline in whichever window dominated. Data: index futures continuous series plus the regional index closes, all available today. New metrics `overnight.gap_attribution_*`, `observation_type: calculated`, `half_life: session`, rights: Backdrop context only — **may not generate a Book C setup.**

**(b) Country-fund premium to stale NAV as a live read on the coming session.** For the tracked country and regional funds, premium to last-published NAV is computed at the U.S. close. The registry entry is explicit that this is **a timing artifact, not a mispricing** — `observation_type: observed`, `half_life: intraday`, with a note that a stop placed on a country fund is triggered by exactly this artifact. Rights: Backdrop context; Book B expression warning when an international candidate's stop sits inside the typical artifact range.

**(c) The hedging decision becomes a register field.** A hedged and an unhedged instrument on the same market are **two different instruments**, never interchangeable. `decide.py` gains a `currency_exposure` field (`unhedged` / `hedged` / `n_a`) that is mandatory for any non-USD-denominated underlying, and the expression check flags an unhedged international position whose thesis makes no mention of the currency — the Rule 11 test applied to the leg the ticker hides.

**Universe consequence.** The chain-capture universe gains no symbols by default; the international candidates are Book A and Book B instruments read from price series, not options. Should an international ETF ever enter Book C, it passes the liquidity floor like anything else.

## 31.4 Positioning & Flows → the participant map as registry facts

The paper's Tables A–C (beneficial ownership by sector; cross-cutting attributes; who trades and when they are forced) enter the **claims registry** with their sources and a review date — not the observation store, because they are cited estimates rather than computed series. The registry note carries the paper's three-denominator warning verbatim: direct ownership of U.S. equity, global AUM by institution type, and equity-relevant AUM are three different measurements, and **forced-flow footprint = equity exposure × turnover × rule-boundness** is the fourth and the one the system sizes by.

The discretionary holders' failure-mode signatures (platform degrossing, redemption waves, liability-driven collateral calls, currency-hedge rebalancing, market-maker withdrawal) each become a `mechanism_group` in the registry so the confluence guard counts them once. **Market-maker withdrawal is not a separate metric** — it is what the absorption measurement already detects, and the registry says so rather than creating a second reading of one fact.

## 31.5 Systematic Book → two obligations on the build

**(a) The shadow-outcome grader is confirmed as the closing link (Track D step 5), with the scope the paper states:** every decision is graded at its horizon from stored prices — **taken, declined, and draft alike** — and taken decisions are additionally reconciled to the fill. This is what makes abstention a row with a number in it and what turns drafted-but-untraded packets into a calibration series for the report that drafted them.

**(b) The failure-class rules become validator obligations.** The paper's Chapter 13 catalogue is promoted from narrative to standing rules already recorded in Part 30.2, with one addition it makes explicit: **a safety property is verified by reading the enforcing code, not the comment that describes it** — the rule that came from the client library's read-only flag doing nothing of the kind. Any future docstring asserting an enforcement guarantee cites the line that enforces it.

## 31.6 What none of these papers change

No new signal family; the Part 26 freeze holds. No metric in any of the four papers is `trigger_eligible`. Seasonality is `trigger_eligible: false` **permanently and by construction** rather than pending evidence, because a calendar effect has no counterparty story that survives Rule 6 — the presidential-cycle conditional enters as a dated register hypothesis instead. And the international sleeve, the debt-cycle branches, and the base rates are all *conditioners and references*: they inform a thesis, size an expectation, and set the bar for a variant view. None of them generates a packet.

## 31.7 Hours

| Item | Hrs | Gate |
|---|---|---|
| `base_rates.py` + registry entries + annual job + drift flag | 2–3 | after D2 (needs the store's series) |
| `regime.debt_cycle_state` branch logic + observables | 1.5 | inside D2 |
| Overnight gap attribution | 1 | with D4's Backdrop block |
| Country-fund premium series | 0.5 | with D4 |
| `currency_exposure` field + expression check rule | 0.5 | immediate; `decide.py` exists |
| Claims-registry entries for the cited tables | 1 | needs the claims registry (S14 dependency) |
| Top & Bottom extended episode set + bear-rally language | 2 | with T&B (S10–14) |
| **Total** | **~8.5–9.5h** | folded into Track D and T&B, not a new track |
