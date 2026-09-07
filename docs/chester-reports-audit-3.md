# Chester Reports — Audit #3

## An End-to-End Re-evaluation of the Architecture and the Workplan

**Date:** 6 September 2026 · **Scope:** the entire system as documented, as reported by build sessions, and as it actually runs · **Status:** audit only; no changes made · **Auditor's disclosure:** the auditor authored most of the architecture under review. Where a finding indicts prior design, the design was mine.

**What this audit could and could not inspect.** The repository itself was not available to this review. The code-level findings below rest on the build sessions' own reports (which have been candid and specific) and on the documented design; a companion instruction for a repository-level pass appears in Section M. Everything else — the philosophy, the signal architecture, the horizon and regime design, the reports, the learning loop, the workplan — was inspected in full.

---

# A. Executive Assessment

**The headline, stated once and defended throughout:** this is a system with institutional-grade *safeguards* and near-zero *evidence*. It has a point-in-time store with three clocks, an immutable decision register, a metrics registry that refuses to let an unvalidated signal trigger, a Brookfield blocklist enforced at two layers, a validator family that has caught seven silent-failure defects in a week, and a written doctrine with a kill-switch ladder. It also has ~330,000 words of research, one production pipeline, one report that runs on a schedule, one paper trade, and **zero graded outcomes.** The documentation is roughly a year ahead of the code, and the code is roughly a year ahead of the evidence.

That is not a failure. It is the correct order for a system whose stated first principle is that nothing triggers until it has earned trust. But it means every score below must be read as a score of *design* on the left and of *demonstrated value* on the right, and the gap between the two is the audit's subject.

| Dimension | Design | Demonstrated | Explanation |
|---|---|---|---|
| Conceptual coherence | 8 | — | The Doctrine, the confluence rule, the horizon taxonomy and the trust matrix are mutually consistent and unusually explicit. Debt: three amendments to a "freeze" in 48 hours; seven planning documents |
| Investment usefulness | 6 | **2** | Nothing the system produced has yet been traded on a system-generated signal. The one trade was hand-reasoned and hand-placed. Usefulness is a hypothesis |
| Analytical rigor | 8 | 4 | The papers are rigorous *as reasoning*. No claim in them has been tested against the system's own data, because the system has almost none |
| Signal quality | — | **3** | 44 metrics and 138 bulk members registered; all `trigger_eligible: false`; the one measured base rate (pins) is 0/13. Quality is unmeasured, which is the honest state and the right default |
| Data integrity | 8 | **4** | The store is excellent by design. In practice (repository pass, 6 Sep): **the database is not in any backup — one copy, on one box**; the FRED dual-write swallows every SQLite error silently; no WAL or busy_timeout; migrated rows carry upper-bound timestamps; HTML editions untracked |
| Architecture | 7 | 5 | The declarative spine is right. The report layer does not exist; the market-state object exists only as a plan; the Daily Cascade — the consumer everything was built for — is a chat artifact |
| Software quality | — | **5** | The validator family is the best thing in the codebase. Against it (repository pass): no test framework; four validators — including the IV solver's and the calendar guard's — run in no CI; 34 `sys.path.insert` calls and `tools/` not a package; five copies of the .env parser and three of the secret redactor; a fixed bug preserved verbatim in a duplicate |
| Maintainability | 5 | 4 | One operator with hours a week; a 278KB controlling document; three sequencing schemes (Sessions −1…15, Parts 27–32, Tracks A–D) |
| Extensibility | 7 | 6 | The registry's `members_from` and the mechanism-group tagging are the right abstractions. Adding a report still requires writing a report |
| Usability | 4 | **3** | Until this weekend nothing pushed to the operator. The first automated email arrived today. The operator cannot answer "what runs when" without a document |
| Reporting quality | 7 | 4 | Chat-produced reports are well written and not graded, not delta-based, and not exception-first |
| Forecasting discipline | 7 | 3 | Every structure for grading exists on paper: register, shadow grader, Brier for scenarios. None has a single row |
| Calibration | — | **1** | No forecast has been scored. The pin log's 0/13 is the only calibration datum in the system |
| Risk awareness | 9 | 7 | The Doctrine, the ladder, the blocklist, DECISION_BLOCKED. Gap: the Doctrine is not enforced at the moment of order entry, which is manual and outside the register's gate |
| Cost efficiency | 8 | 8 | ~$45/month in data, ~€5 hosting, one subscription. The expensive resource is the operator's time, and the workplan spends it as if it were abundant |

**Overall: a 7 on design, a 3 on demonstrated value, and the entire remaining project is closing that gap without widening the design.** *The repository pass lowered two demonstrated scores: the data the design protects so carefully is backed up nowhere, and the report the system has shipped for four months has no defense against an invented number beyond an instruction to the model.*

---

# B. Current Architecture Map — how it actually works today

```
DATA SOURCES        yfinance chains (13) · Massive (SPX/SPCX chains) · FRED (59 series, dual-written)
                    · IBKR Gateway (portfolio, +5 paid feeds) · Polymarket/Kalshi (planned)
        ↓
INGESTION           EOD pass 16:10 ET on VPS (systemd) · IBKR sync every 30 min · Monthly fetchers (GitHub Actions)
        ↓
NORMALIZATION       session_date() helper · instrument_norm · registry-enforced column names · CI gate on drift
        ↓
STORAGE             data/chester.db — observations (observed/available/ingested) · decisions + immutable packets
                    · portfolio truth · pin log · chain snapshots zipped nightly; off-box backup (rclone: PLANNED)
        ↓
FEATURE CREATION    exposure_compute: 4 Greeks × 4 buckets · IV solver w/ gates · walls/flip/pin · base_rates (PLANNED)
        ↓
SIGNAL GENERATION   metrics_registry: 44 + 138 members, ALL trigger_eligible:false · mechanism groups declared
        ↓
ANALYSIS / MODELS   regime.py (PLANNED, D2) · CPI lead composite (designed) · tail watch table (designed)
        ↓
SYNTHESIS           Part 15 edge layer (designed) · confluence rule (designed; enforced only in decide.py's signal list)
        ↓
REGIME              three dials — Macro / Vol / Gamma (Doctrine; no code)
        ↓
PORTFOLIO / TRADE   decide.py: record/list/show/set-status; DECISION_BLOCKED on stale signals; Brookfield trigger
                    · order placement: MANUAL in paper TWS, outside the register's gate
        ↓
REPORTING           Monthly Macro (runs; cron-job.org → Actions) · Daily Cascade (CHAT ONLY — no code)
                    · Top & Bottom, Disruptive Themes, Alt Asset (chat only) · D4c close report (built today, not enabled)
        ↓
HUMAN DECISION      the operator, reading chat outputs; one paper trade placed by hand
        ↓
OUTCOME TRACKING    pin log (13 rows, 0 hits) · register (2 decision rows) · Portfolio Truth (9 rows) · shadow grader: NONE
        ↓
FEEDBACK / LEARNING none. No graded forecast, no calibration series, no rule ever revised on evidence
```

**What runs unattended today:** the EOD capture and Greeks; the IBKR sync and Gateway supervision; the heartbeat and (as of today) its email; the Monthly on an external button. **What does not:** every report the operator reads, every synthesis step, every regime assessment, every grade.

---

# C. Major Strengths — preserve without argument

1. **The point-in-time store with three clocks and the as-of join.** This is the one thing most retail systems never build and most institutional ones build wrong. The leakage test in CI is the proof it works.
2. **The immutable decision packet.** UPDATE/DELETE triggers, `superseded_by`, replay proven EXACT from Friday's packet. This is what makes a learning loop possible at all.
3. **The registry's refusal.** `trigger_eligible: false` as the default, `observation_type` and `half_life` as fields, DECISION_BLOCKED when a signal is stale. The system cannot currently trade on anything, and that is by design, and that design is correct.
4. **The validator family and its posture — assert, don't trust.** Directive-in-wrong-section, exec bits from the index, ExecStart resolved to tracked files, drift between installed and shipped units, the no-prose CI check. Seven silent failures caught in seven days. This is the most valuable engineering habit in the system.
5. **The self-computed exposure engine with a vendor cross-check** that caught two definitional bugs and one load-bearing floor. Independent computation plus independent verification is the pattern.
6. **The Brookfield restriction at two layers.** Python raise plus SQLite trigger, 29 roots, instrument normalization. A compliance control that would survive a code bug.
7. **The Doctrine's risk layer.** Dollars of risk not notional; the tier system tied to alignment; the kill-switch ladder; adds on confirmation only. This is a professional risk framework, and it is written down.
8. **The honesty conventions.** Source class on every figure, inferred/observed/calculated, "net could be out by $X" printed every run, the decidability table, the Base Rates card. The system tells the truth about what it does not know.
9. **The confluence rule** — mechanism groups vote once. It is the single most important defense against the correlated-signal failure that this audit's own Section 4 warns of.

---

# D. Major Weaknesses — ranked

**D1. The learning loop has no data and no near-term prospect of enough.** Zero graded outcomes. The shadow grader — the single largest multiplier of evidence available — is Track D step 5, behind four other steps. *Evidence and Inference* computed that even at full cadence the register decides five questions in three years. The system's core promise — that rules change on evidence — cannot be honored for at least a year, and the workplan spends the intervening hours on new signal families instead of on grading.

**D2. The Daily Cascade, the consumer everything was built for, does not exist.** Discovered this weekend. Every report the operator has ever read was produced by hand in a chat. The market-intelligence system has, until today, been a market-intelligence *conversation* with a data pipeline underneath it.

**D3. Signal proliferation ahead of signal validation.** Nine Doctrine families; 44 metrics plus 138 members; 25 tail scenarios; 5 disruptive factors; 11 macro pillars; Part 29's eight tactical additions (24–29 hours); Part 27's prediction-market engine; a crypto forecast at three horizons; a Thailand pillar. All correctly gated from triggering — and all consuming the operator's scarcest resource, which is the hours that could grade what exists.

**D4. The Doctrine is not enforced where it matters.** Order entry is manual in TWS. The register records the decision; nothing prevents an order that contradicts it, exceeds its size, or ignores a switch. The kill-switch ladder is a document. Gate 2 and the expression check are the mechanism, and both are behind the Daily build.

**D5. Planning sprawl.** Seven planning documents (architecture v3 at 278KB with 32 parts, narrative, roadmap, compressed plan, v17 build plan, work plan v2, master schedule), three sequencing schemes, a "controlling" change order amended three times in two days, and a nominal total of 229–246 hours against an operator with perhaps five a week. The plan is not a plan; it is a backlog with ambitions. *This is the auditor's own debt.*

**D6. The reports restate levels rather than surface change, and nothing is exception-first.** The Monthly is ~30 pages of pillars; the Daily blocks are narrative. There is no "what changed since last run," no percentile stamp on magnitudes, no alert that fires only on a threshold. D4a's heartbeat email is the first exception-based delivery in the system's life.

**D7. The market-state object does not exist.** Every report — when it existed as a chat — recreated its own worldview from the same inputs. `regime.py` is the seed and is unbuilt. Until it exists, the reports cannot be consistent with each other except by the author's memory.

**D8. Data lineage is designed but not closed.** The packet replays; the chain snapshots exist; but the migrated FRED rows carry an upper-bound `available_at` that the freshness check treats as stale, the HTML editions of the papers are outside version control, and no report claim can yet be traced to a raw observation because no report is generated from the store.

---

# E. Architectural Debt — where incremental additions accumulated

| Debt | How it accumulated | Cost |
|---|---|---|
| **32 architecture Parts, four "controlling" documents** | Each session's findings appended rather than folded; three post-freeze amendments | A new session must read 5,000 lines to know the rules |
| **Three sequencing schemes** | Sessions (−1…15) → Parts 27–32 → Tracks A–D; each re-sequenced the last | Nobody, including the author, can state the order without a table |
| **Eleven macro pillars feeding three regime dials** | The pillars were designed before the dials; the dials were designed in the Doctrine without revisiting the pillars | 11 inputs, 3 outputs, no stated mapping |
| **Five reports designed as peers** | Each added when a need appeared; the narrative's Part 5 was written to reconcile them after the fact | Disruptive Themes and Alt Asset reach the Daily only through the operator's memory |
| **25 tail scenarios** | Added one at a time as risks were noticed; the paper groups them into ~6 mechanism families | The tail watch tracks 25 states for ~6 mechanisms |
| **The alt-data chats' additions (Part 29)** | Eight ideas from separate conversations, each good, admitted as a set | 24–29 hours of build for zero graded families |
| **Two `-ALT-branch` paper duplicates, seven planning docs, untracked HTML** | Parallel authoring without a merge step | Confusion about which is canonical, on the very day the rule about canonicality was deleted three times |
| **The declarative spine designed, the report layer imagined** | Sessions 2–7 built the spine well; the consumer was assumed to exist | D2 (32.1): the Daily is a build, not a migration |

---

# F. Missing Capabilities — ranked by expected information value

1. **Outcome grading for every decision (taken, declined, drafted).** Multiplies evidence 3–4×; grades the reports as well as the trades. Without it nothing else can be evaluated. *Highest value in the system, by a wide margin.*
2. **A canonical market-state object** — the dimensions, each with state / direction / rate of change / percentile / confidence / horizon / supporting / contradicting. The substrate every report reads instead of recomputing.
3. **Exception-first delivery** — thresholds, percentile crossings, correlation breaks, regime-transition probability, positioning extremes — pushed, not fetched. D4a began it.
4. **A contradiction table** — price vs breadth, equities vs credit, prediction markets vs assets, vol vs tail probability, macro vs cyclicals. Part 15's edge layer specifies most of it; nothing computes it.
5. **Portfolio-level heat and factor view** — the Doctrine specifies the cap across books at a common factor; nothing computes net beta-equivalent exposure, factor overlap, or crowding across the register's open decisions.
6. **Probability calibration ledger** — Brier and calibration for every scenario weight, tail probability, and prediction-market read the system emits. The 25 scenarios have carried probabilities for months with no scoring.
7. **Change-based metrics** — level, change, rate of change, percentile, z-score, extreme flag as standard derived forms for every registered metric (Part 30's "standard derived forms" convention, unbuilt).
8. **Order-entry enforcement** — the register's gate at the point of execution; the expression check's refusals made binding; Gate 2.
9. **Dispersion and cross-sectional opportunity** — the system is almost entirely index-level; the cohort monitor is the only cross-sectional instrument and it is unbuilt.
10. **Expectations vs realized** — the surprise metrics in the registry backlog; the economic-surprise machinery that would let the Monthly say "versus what was expected" rather than "versus last month."

11. **A narrative register and the news scan as a stored, graded function** — added on review; see Section I. Stories tracked as dated entities with state and evidence, graded on their implied outcomes.

*Not missing, and not to be added:* insider-activity feeds, order-book depth, alternative data beyond what is scheduled. See Section P.

---

# G. Redundant / Low-Value Components — delete or consolidate

| Component | Verdict | Reason |
|---|---|---|
| Six of the seven planning documents | **Merge into one** | One roadmap with one status ledger. The architecture doc becomes a reference, frozen at Part 32, with new decisions as short dated addenda that *replace* text rather than append |
| Top & Bottom as a standalone report | **Subordinate** | It is a state variable — a verdict and a composite — that belongs in the market-state object and prints inside the Monthly and the Weekly. Its research value is the paper, not the report |
| Alternative Asset as a standalone report | **Merge into Monthly** | A section, not a document; its metals/energy/digital content already has a paper each |
| Disruptive Themes as a monthly | **Quarterly** | Structural by definition; the paper's factor states move on quarters, and its own refresh flag was designed because it went stale as a monthly |
| 25 tail scenarios as 25 states | **Collapse to mechanism families** with the 25 as instances | The paper already groups them; the watch table should track families with instance detail |
| 11 macro pillars as peers | **Subordinate to the three dials** with a stated mapping | Pillars are inputs; dials are the regime. State which pillars feed which dial and at what weight, and stop printing eleven scores |
| Part 29.5 privacy-coin theme | **Keep** (operator's ruling, 6 Sep) | Judged a potential structural theme; the shielded-pool logger is forward-only and cheap |
| Part 29.6 DAT entity type | **Retire** | Zero contribution to the four books' edges |
| Part 29.4 MOC absorption, 29.7 meme lifecycle | **Defer the build; start the logging now** (operator's ruling) | The auction-tick sampler and the borrow/FINRA/attention series are forward-only loggers — an hour each, and the history is irreplaceable. The state machines and hypotheses wait for graded decisions and are built against a year of data instead of none |
| Part 27 v1 + 29.8 prediction-market phase 2 | **Defer; phase 2 retire** | The v1 changes-over-levels idea is sound; phase 2 (cross-asset divergence engine, ForecastEx) is a research project |
| Session 12.5 Thailand / THB pillar | **Remove from the pillars; becomes a standalone quarterly report** (spec: `thailand-monitor-spec.md`), deferred to after Phase 5 | Personal-finance decision support, isolated from the dials and the register |
| Crypto running forecast at 12m/3y/5y | **Retire the forecast; keep the metrics** | Ungradeable at the long horizons within the system's life; the eight metrics are useful, the forecast is a narrative |
| The dashboard (never built) | **Do not build** | Email is the dashboard. A dashboard requires the operator to look; the system's principle is that it finds him |
| The `-ALT-branch` duplicates | **Delete** | Already excluded from upload; remove from outputs |
| FlashAlpha Basic ($) | Already retired | Correct |
| cron-job.org | Retiring | Correct sequencing (prove, then delete) |

---

# H. Ideal End-State Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│ DATA LAYER            sources registry · fetchers · point-in-time store  │
│                       (observed / available / ingested) · snapshots      │
│                       · off-box backup · lineage: every row has a source │
├─────────────────────────────────────────────────────────────────────────┤
│ FEATURE / SIGNAL      metrics registry (the contract) · standard derived │
│ LAYER                 forms (level, Δ, rate, percentile, z, extreme)      │
│                       · mechanism groups · base rates as observations    │
├─────────────────────────────────────────────────────────────────────────┤
│ MARKET-STATE /        ONE object, recomputed daily: ~12 dimensions ×     │
│ REGIME LAYER          {state, direction, rate, percentile, confidence,   │
│                       horizon, supporting[], contradicting[]}            │
│                       + three dials + transition risk + contradiction    │
│                       table + debt-cycle branch state                    │
├─────────────────────────────────────────────────────────────────────────┤
│ ANALYTICAL / CAUSAL   causal chains as declared paths through the state  │
│ LAYER                 object (macro→policy→rates→liquidity→positioning   │
│                       →factor→microstructure); the edge layer (priced    │
│                       vs expected); scenario weights with Brier scoring; │
│                       the narrative register (stories as dated, graded   │
│                       entities over stored events)                       │
├─────────────────────────────────────────────────────────────────────────┤
│ OPPORTUNITY & RISK    setups drafted from the state object (not from     │
│ LAYER                 reports); heat & factor view across open decisions │
│                       ; tail budget state; exception detector            │
├─────────────────────────────────────────────────────────────────────────┤
│ TRADE / PORTFOLIO     the register (unchanged) · expression check binding│
│ LAYER                 · order gate at entry (Gate 2) · Portfolio Truth   │
├─────────────────────────────────────────────────────────────────────────┤
│ REPORTING & ALERTING  4 canonical outputs + alerts, ALL rendered from    │
│                       the state object + register; LLM writes prose     │
│                       over a payload; numeral audit before send; email  │
├─────────────────────────────────────────────────────────────────────────┤
│ OUTCOME / LEARNING    shadow grader (every decision) · Brier ledger ·    │
│ LAYER                 error decomposition · champion/challenger · the    │
│                       decidability table as the review's expectations   │
└─────────────────────────────────────────────────────────────────────────┘
```

Three rules make the diagram binding rather than decorative. **No report computes.** Every figure a report prints is read from the state object or the register with its provenance. **No signal reaches a report except through a mechanism group**, and no group votes twice. **No prose is generated without a payload and no payload is sent without a numeral audit.**

---

# I. Ideal Report Architecture

Five documents replaced by four canonical outputs plus alerts, each answering the seven questions (what changed, why it matters, what the market believes, where the disagreement is, what to watch, is there a trade, what would change the view).

| Output | Cadence | Decision it supports | Content rule | Replaces |
|---|---|---|---|---|
| **Daily State** | 07:00 ET, and a data-only close edition at 16:30 | The day's regime stamp; Book C setups; does anything need attention | **Deltas first.** Overnight gap attributed; dials; changes since yesterday/week; exceptions; drafted setups into the register as `draft`. Nothing published on a stale source | Daily Cascade's 9 runs (the intraday reads become *alerts*, not reports) |
| **Weekly Tactical** | Sunday | Book B and C stance for the week; the Friday reflection folded in | The week's graded decisions and rule breaks; the state object's week-over-week; the setups list; the calendar | Friday Reflection + Sunday Plan |
| **Monthly Regime & Allocation** | First weekend | Book A's bands; the dials; the scenario weights and their scores | Half the current Monthly's length; pillars *subordinated* to dials; every scenario weight printed with last month's and its Brier to date; Top & Bottom verdict and Alt Asset as sections | Monthly Macro + Alt Asset + Top & Bottom report |
| **Quarterly Structural** | Quarter-end | Structural positioning; the tail budget; theme states | Disruptive Themes' factor states; tail-family states; the library guide's executive summary rewritten; the international sleeve's hypotheses reviewed | Disruptive Themes + tail scan + guide summary |
| **Alerts** | On exception | Immediate attention | Fires on: threshold crossings, percentile extremes, regime-transition probability, contradiction-table entries, heartbeat/drift, portfolio-impact of a move. Silent otherwise | The intraday runs; the dashboard that was never built |

**Length rule — restated after review (6 Sep):** there are **no word counts.** The budget for *repetition* is zero — background lives in the papers, and a metric whose half-life exceeds the report's cadence is not reprinted, only its change — but the budget for *insight* is whatever the insight needs. The 07:00 news scan, the Sunday reflection, and the monthly and quarterly run as long as the analysis warrants. The one discipline that replaces a word count: **the insight goes at the top and the depth follows** — the first screen answers "what changed and does it matter," so a long report can be stopped after a screen without losing the decision, and a short one cannot bury it. The conditionals and the close anchor are terse by design, because they are deltas; if one runs long, the exception gate has failed.

**The daily cadence, as ruled (6 Sep) — three anchors, five conditionals plus Sunday:**

| Slot | Kind | Unique content |
|---|---|---|
| **07:00** | Anchor | Tokyo closed, Europe four hours in, overnight complete; the regime stamp; **the news and narrative scan (below)**; folds in 21:45 |
| 09:15 | Conditional | 08:30 releases with 45 minutes of reaction; SPX global-hours tape complete; publishes on a tier-1/2 release, a futures move past threshold, or a dial change |
| 10:30 | Conditional | Opening range complete; 10:00 releases in; live 0DTE gamma from the 09:45 capture; breadth, TICK, VIX change |
| 15:00 | Conditional | The predictable last-hour flows computed before they happen — leveraged-ETF rebalance from the day's return, vol-control exposure change, pin distance; FOMC reaction on Fed days; the trade-into-the-close read |
| **16:45** | Anchor | Cash close, MOC outcome, ES settlement, the first fifteen minutes of after-hours earnings reactions, post-close futures drift; folds in 09:15, 10:30, 15:00 |
| 21:45 | Conditional | ES reopen (nearly four hours), Tokyo open, Shanghai/HK open at 21:30, Chinese releases; USD/JPY and JGBs for the yen monitor |
| **Sunday 05:00** | Anchor (Weekly) | Friday's data, the week's grades and rule breaks, the calendar, weekend developments to that point |
| Sunday 21:45 | Conditional | ES reopen, Asia open, weekend policy announcements and the market's first reaction |

The 12:30 chain capture keeps running for data and feeds an alert only. **The LLM is called only when an exception gate opens**; a conditional with nothing to say costs a query and produces one line.

**The news and narrative scan — a first-class function, not an afterthought.** The audit's first draft under-weighted this, and the operator corrected it. Markets trade stories, and a system that reads only numbers is blind to the variable that moves positioning before the numbers confirm it. The rule is not "no narrative"; it is **"narrative with the same discipline as signals."**

- **Ingested, not fetched at render.** Headlines, releases, speeches, filings, and prediction-market moves enter the store through the events-ingest layer with timestamps (Part 18's "replacing news consumption" design, built rather than described). The 07:00 scan reads stored events; it does not search at render time, so what it says is reproducible and gradeable.
- **A narrative register.** Each story the market is trading is a tracked entity — *AI capex durability*, *fiscal dominance*, *the yen carry*, *the midterm cycle* — with a state (emerging / consensus / contested / fading), a direction, the evidence for and against, the market-state dimensions and prediction-market contracts it links to, and a date. Narratives are graded like forecasts: did the outcome the story implied occur at the horizon the story implied?
- **The 07:00 anchor's narrative block** is where the long-form commentary lives: which stories gained or lost force overnight, which are consensus and which contested, where the market's story and the data disagree (the contradiction table, read as narrative), and what would change each. The Sunday reflection carries the week's narrative arc; the Monthly the regime's; the Quarterly the structural themes'.
- **Where the LLM belongs.** This is the layer where a reasoning model earns its cost — synthesis across domains, hypothesis generation, explaining an anomaly — over a payload of stored events and state, with every numeral audited and every claim traceable to a stored event or an observation.


---

# J. Canonical Signal Taxonomy

```
observation           one row in the store: source, timestamps, value, quality flag
   ↓
metric                registered: observation_type, native_horizon, half_life, revision_policy,
                      trigger_eligible, mechanism_group, standard derived forms
   ↓
mechanism group       the unit that votes — e.g. dealer_chain_derived, index_rebalance, carry_funding
   ↓
signal family         the Doctrine's nine: macro regime · valuation · positioning extremes ·
                      trend/momentum · variant perception · thematic · event reaction ·
                      dealer positioning · session structure  (+ forced flows, mispriced optionality
                      as Book D's two)
   ↓
market dimension      the state object's rows: growth · inflation · policy · rates · liquidity ·
                      credit · trend · breadth · volatility · positioning · sentiment · valuation ·
                      earnings · funding stress · geopolitical · tail
   ↓
horizon-specific view intraday · 1–5d · 1–4w · 1–3m · 3–12m · 1–3y · structural — a signal reaches
                      only the horizons its native_horizon and half_life permit
   ↓
opportunity / risk set drafted setups and flagged risks, each naming its family, its mechanism
                      groups (voted once), its horizon, and what is already priced
```

**Classification per signal, required in the registry** (most fields exist; two are added): *economic mechanism* (exists as `rationale`), *leading/coincident/lagging*, *directional/confirmatory/contextual/risk-warning* (new), *regime dependence* (exists), *falsifier* (new — `kill_condition`, already in the backlog), *crowding/decay susceptibility* (new). **Redundancy rule:** any two metrics sharing a mechanism group are one signal; any two in different groups that correlate above a stated threshold over a year are flagged as suspected redundancy and reviewed.

---

# K. Canonical Market-State Model

One object, recomputed by the EOD pass, versioned, and stored as an observation with `available_at`:

```
market_state:
  as_of, version
  dials: macro {state, since, transition_prob}, vol {…}, gamma {…}
  dimensions[16]:
    growth: {state: expanding|slowing|contracting, direction: +/−/0, rate_of_change, 
             percentile_5y, confidence: high|med|low, horizon: 1-3m,
             supporting: [metric_ids], contradicting: [metric_ids], last_changed}
    …
  contradictions[]: {pair, magnitude, since, persistence_days}
  debt_cycle_branch: {state: none|deflationary|inflationary, confidence, observables}
  tail_families[]: {family, state, probability, brier_to_date}
  exceptions[]: {what, threshold, value, since}
```

**Rules.** Every report reads this and only this for its regime content. A dimension changes state only on a declared rule, and every change is an event the alerts may fire on. *Contradicting* is never empty by omission — the object records "none found" as a positive claim. Confidence derives from staleness and sample, never from the author. And the object is graded: each dial's state at t is scored against the realized regime at t+horizon, which is the calibration series the trust matrix's regime rows require.

---

# L. Learning / Calibration Framework — how the system would know it is improving

The structures exist on paper; this section states what "improving" would mean in numbers.

| Series | Computed from | Improving means |
|---|---|---|
| **Shadow expectancy by owning report, by regime** | shadow grader over drafts and declines | The intervals narrow and the sign stabilizes; a report whose drafts grade negative in a regime loses that regime's publish right |
| **Decline hit-rate** | graded declines | Falls toward the taken hit-rate — the veto is neither too loose nor too tight |
| **Brier score of every emitted probability** | scenario weights, tail probabilities, PM reads | Falls; and is *reported beside the probability* so the reader discounts it correctly |
| **Dial calibration** | dial state vs realized regime at horizon | Transition calls become earlier without more false positives |
| **Rule-break count** | register | Trends to zero — the Doctrine's own gate for Book D |
| **Estimate drift** | schedule vs actual hours | Runs backward, as it did this week |
| **Numeral-audit failure rate** | D3 over every narrative | Falls; a narrative that fails the audit is the LLM confound made visible |
| **The decidability table, revisited** | *Evidence and Inference* Ch. 13 | At each quarterly review, the predicted "decidable / suggestive / never" is compared with what the register could actually decide |

**Hindsight-bias controls:** grades computed by code from stored prices, never by the operator; the error decomposition filled in before the P&L is visible; superseded packets frozen. **The single most important rule:** no signal's weight, no trust-matrix cell, and no rule changes except at a session, on a printed sample size, with the challenger having run.

---

# M. Software / Data Refactoring Plan — prioritized

## M.0 Repository pass — findings (Claude Code, read-only, @ 30bc12b, 17,753 lines, 8 packages)

*Verified by execution or by reading the enforcing code. The full pass is in `docs/audit-3-repository-pass.md`; this section carries what changes the plan.*

**P0 — data loss or silent corruption**

| # | Finding | Fix |
|---|---|---|
| P0-1 | `data/chester.db` is gitignored and **excluded from `backup_chains`** — observations, register, immutable packets have exactly one copy, on one VPS | Add the DB and `pin_log.csv` to the nightly zip *and* land the rclone sweep over `data/` |
| P0-2 | `altdata/store.py:85` — `except Exception: pass` swallows every SQLite failure; the dual-write can be dead for weeks while the CSV looks healthy. *The exact defect the heartbeat work was built to eliminate, still live in the FRED path* | Log at WARNING; write a `dual_write_failed` counter the heartbeat reads |
| P0-3 | No `journal_mode=WAL`, no `busy_timeout`, on either connection; `flock` guards scripts, never the DB; `ibkr-sync` (16:30 ±90s) and `daily-close` (16:30 ±120s) aim at the same minute | `PRAGMA journal_mode=WAL; PRAGMA busy_timeout=5000` in both `__init__`s (D1c); the cadence ruling's move of the close to 16:45 separates the timers as well |

**P1 — a wrong number reaches a report**

| # | Finding | Fix |
|---|---|---|
| P1-1 | `quality_gates.newest_chains` still carries **both halves of the capture-selection bug fixed in `exposure_compute`** — preserved verbatim in a duplicate; dormant only because the caller passes rows in | Delete the duplicate; import `exposure_compute.newest_chains` |
| P1-2 | **No numeral audit exists.** The Monthly's sole defense against a fabricated figure is the system-prompt sentence "Never invent numbers"; the prompt is truncated Markdown, not a payload; output is checked only for non-emptiness | D3, before any further narrative ships |
| P1-3 | `validate_iv_solver.py` and `validate_session_calendar.sh` — the largest module and the calendar guard — run in **no CI** | Add both to `registry-check.yml` |
| P1-4 | No unit has `EnvironmentFile=`; no wrapper sources `.env`; `FRED_API_KEY` and `CHESTER_STATE_TOKEN` are `os.environ`-only → **D4d's state emit cannot fire on the box** and will log "not set" on every run | `EnvironmentFile=-%h/chester-reports/.env` on the units that need it |
| P1-5 | `render.money()` raises on a non-numeric value and nothing catches it — one bad field destroys the nightly report and its archive (confirmed by execution) | Return the dash on `ValueError`/`TypeError` |

**P2 — structural** (34 `sys.path.insert`; `tools/` not a package and `altdata` importing upward from it; five `.env` parsers and three `redact()`s; six "newest file" walk-backs with three ranking rules; no test framework — 11 bespoke validators, no shared runner; `smoke_test.py` in no workflow; `register/store.py:213` swallows `OperationalError`; symbol identity parsed from filenames in three places) **and P3 — hygiene** (dead `gex_compute.py` shim; CLAUDE.md's layout stale; `monthly-report.yml` still has no `schedule:` — D4b unbuilt; twelve `logging.basicConfig`s; CI's PyYAML-only install an undeclared invariant; `CHAIN_DIR` the one non-overridable path).

**The pattern the pass named, and the audit adopts as its engineering thesis:** this repository catches silent failures *after* they bite and asserts against them permanently — six classes, each with a validator proved to fail on its defect. Every P0 and P1 above is the same shape one step earlier: a failure path that exists, has no assertion, and would announce itself only as missing data. The Phase 0 work is to move the assertion in front of the failure.

## M.1 Prioritized changes (revised against the repository pass)


*Findings from the sessions' reports; the repository pass below will extend them.*

1. **P0 — The database into the backup, tonight** (P0-1), then rclone off-box. The store is the system, and it currently has one copy.
2. **P0 — WAL + busy_timeout on both connections** (P0-3); the close report to 16:45 per the cadence ruling.
3. **P0 — The dual-write stops failing silently** (P0-2): log, counter, heartbeat reads it.
4. **P1 — The five P1s in one session:** dedupe `newest_chains`; add the two missing validators to CI; `EnvironmentFile=` on the units; the render guard; and D3's numeral audit scheduled as the next narrative work — no new prose ships before it.
5. **P1 — A single `make validate`** running every validator, and CI gates that run independently.
4. **P1 — Commit the HTML editions and regenerate-and-diff them in CI.** The "canonical for reading" rule is a discipline about files git has never seen.
5. **P1 — One planning document.** Merge; freeze the architecture at Part 32 as reference; new decisions as replacing addenda.
6. **P1 — Standard derived forms as a registry convention** (level/Δ/rate/percentile/z/extreme) computed by one function, not per-report.
7. **P1 — ALFRED backfill of the migrated FRED rows** so the freshness check stops treating history as stale.
8. **P2 — Model pinning per report and a model-version column on every narrative artifact** (Finding 3 of Audit #1, still open).
9. **P2 — Secrets audit** (Session 1 leftover), now that SMTP credentials live on the box.
10. **P2 — Independent-gates CI matrix** (`fail-fast: false`), per the TODO written today.

**The repository-level pass has been run** (M.0 above). The instruction that produced it, for the record:

> Produce a software-engineering audit of this repository, changing nothing. Report: module boundaries and their coupling; every writer to data/chester.db and whether a lock protects it; test coverage by module; every place a secret is read and how; every hard-coded path, format, or vendor assumption; every place an LLM is called and whether the call is gated by a payload and a numeral audit; every script not executed by any timer or workflow; duplicated logic across modules; and the ten most brittle lines. Rank findings P0–P3 with a one-line fix each. Do not fix anything.

---

# N. Migration Roadmap

**Classification of existing components**

| KEEP | KEEP BUT REFACTOR | MERGE | REPLACE | RETIRE | NEW |
|---|---|---|---|---|---|
| store · register · packets · registry · validators · exposure engine · Portfolio Truth · heartbeat · Doctrine · library | Monthly (halve; subordinate pillars; deltas) · CLAUDE.md as the single durable rules file · TODO as the single backlog | six planning docs → one · T&B + Alt Asset → Monthly sections · Friday + Sunday → Weekly · Themes + tail scan → Quarterly | chat-produced Daily → generated Daily State · nine intraday runs → alerts · 25 scenarios → families | Thailand pillar · privacy-coin theme · DAT entity · crypto long forecast · dashboard · ALT duplicates | state object · shadow grader · Brier ledger · contradiction table · heat view · order gate · exception detector |

**Phases, re-sequenced for an operator with limited hours** — the governing principle is *evidence before expansion*:

*Ruled 6 Sep: execution order is **Phase 0 → 1 → 3 → 2 → 4 → 5 → 6** — delivery first, the grader immediately after (it needs drafted setups to grade, and the 07:00 anchor produces them), the state object once there is something to read it. 6a loggers and 6b slots run alongside Phases 1–2.*

| Phase | Content | Hours | Exit criterion |
|---|---|---|---|
| **0 — Safeguards (now)** | WAL + lock · off-box backup · independent CI gates · HTML tracked · one planning doc | 5 | A dead pipeline is noticed within a day; a lost box loses nothing |
| **1 — Deliver (this month)** | D4c data-only close report enabled · D4f morning brief · alerts for heartbeat, drift, exceptions | 8 | The operator receives two emails a day he did not produce |
| **2 — State (next)** | regime.py → the market-state object v1 with 8 dimensions · standard derived forms · contradiction table v1 | 8 | Every report reads the object; the Daily prints "what changed" |
| **3 — Grade (before anything new)** | Shadow grader over drafts, declines, takes · Brier ledger for scenario weights · numeral audit | 8 | Every decision has a grade at its horizon; the first calibration number exists |
| **4 — Consolidate reports** | Weekly Tactical · Monthly halved with Brier beside every weight · Quarterly Structural | 10 | Five documents become four outputs plus alerts |
| **5 — Enforce** | Order gate at entry · expression check binding · heat/factor view | 6 | An order that contradicts the register cannot be placed without an override recorded |
| **6 — Expand, on evidence** | Part 27 v1 · Part 29 items 1–4 · intraday cadence · cohort monitor — **each admitted only when Phase 3 has graded the family it extends** | as earned | 150 graded decisions across two regimes before any new family triggers |

**Phase 6, itemized (ruled 6 Sep) — ~91 hours; loggers first, delivery second, analysis on logged data last and gated:**

| Sub-phase | Items | Hrs | Gate |
|---|---|---|---|
| 6a Forward-only loggers | RTAT10 · nightly consensus/revision log · IBKR auction-tick sampler (29.4 logging) · borrow/FINRA/ApeWisdom series (29.7 logging) · shielded-pool explorer (29.5) | 6 | None — start in Phase 1 |
| 6b Intraday slots | capture-instant T + 09:45/12:30 captures · 09:15 · 10:30 · 15:00 · 21:45 · Sunday 21:45 | 10 | Phase 1; Tuesday clean capture |
| 6c Events, calendar, edge layer, **narrative register** | events ingest with consensus/actual/surprise (S8) · forward calendar (S9) · surprise metrics · Part 15 edge layer · narrative register and the 07:00 scan over stored events | 14 | Phase 2 |
| 6d Prediction markets v1 | Polymarket + Kalshi · changes-over-levels, attention shock, venue disagreement · weekend probability-delta proxy | 4 | 6c |
| 6e Macro completeness | S3a market data · S3b rates & policy · S3c fiscal & demand · CPI lead composite · ALFRED backfill | 12 | Phase 2 |
| 6f State object v2, tail families | 16 dimensions with transition probabilities · dial calibration · tail families (~6) with Brier · debt-cycle branch | 8 | Phase 3 |
| 6g Cross-sectional and funding | speculative-cohort monitor (29.2 analysis) · yen carry monitor (29.1) | 8 | 6a has a quarter of history |
| 6h Analysis on logged data | MOC absorption hypotheses (29.4) · meme lifecycle machine (29.7) · privacy-coin theme analysis (29.5) · `response_ratio` (29.0) | 10 | **150 graded decisions across two regimes; ≥ 6 months of 6a history** |
| 6i Report completions | T&B harness with the extended episode set · Themes refresh automated for the Quarterly · Alt Asset live fetchers | 10 | Phase 4 |
| 6j Execution gates | Gate 2 (Read-Only off, What-If, fills reconciled) · Gate 3 (brackets from packets with approval) · execution analytics | 8 | Phase 5; a month of validated paper refusals |
| 6k Tools from the papers | `base_rates.py` · `structure_compare.py` on live vol · `currency_exposure`, `expression_family`, `leverage_form` rules | 5 | Phase 2 |
| 6l Claims registry | cited tables with sources and review dates | 2 | None |
| 6m Thailand Monitor | fetchers, quarterly report, four alerts, payment-dates table | 4 | After everything above |
| **Phase 6 total** | | **~91** | |
| **Grand total, Phases 0–6** | | **~136** | |

6a and 6b run alongside Phases 1–2 — they are logging and delivery, and every week of delay in a logger is a week of history lost. 6h is the only sub-phase with a hard evidence gate.

**Total to the end of Phase 5: ~45 hours.** The current plan's nominal 229–246 reaches the same place after ~120 and then spends the rest on Phase 6 before Phase 3 has produced a number. **The re-sequencing does not add work; it moves grading from step 5 of Track D to before every expansion, and it deletes roughly 60 hours of Phase 6 outright.**

---

# O. Top 20 Recommendations — ranked

1. Build the shadow grader before any new signal family. (P0; 4h; depends on D4c's payload; highest information value in the system)
2. Enable D4c tonight and D4f this week — receive the system's output by email, daily. (P0; done/3h)
3. WAL + write lock, off-box backup, independent CI gates. (P0; 3h)
4. One planning document; architecture frozen as reference. (P0; 2h; the auditor's own debt)
5. Build the market-state object from `regime.py`; every report reads it. (P1; 4h)
6. Deltas and percentiles as the Daily's first block; levels as an appendix. (P1; 2h)
7. Brier-score every scenario weight and print it beside the weight. (P1; 2h)
8. Subordinate the eleven pillars to the three dials with a stated mapping. (P1; 2h)
9. Collapse the 25 tail scenarios into mechanism families with instances. (P1; 1h)
10. Merge Top & Bottom and Alt Asset into the Monthly; halve the Monthly. (P1; 3h)
11. Order gate at entry — Gate 2 — with overrides recorded. (P1; 4h)
12. Contradiction table v1: six pairs, computed from the state object, alert on persistence. (P1; 3h)
13. Heat and factor view across open decisions. (P2; 3h)
14. Standard derived forms as one function. (P2; 2h)
15. Commit HTML editions; regenerate-and-diff in CI. (P2; 1h)
16. ALFRED backfill. (P2; 3h)
17. Model pinning and a model-version column on every narrative. (P2; 1h)
18. Retire Thailand pillar, privacy-coin theme, DAT entity, crypto long forecast. (P2; 0h — deletion)
19. Secrets audit now that SMTP lives on the box. (P2; 1h)
20. Part 27 v1 only, after Phase 3, as the first *new* family admitted on the new rule. (P4; 3h)

---

# P. Top 10 Things to Stop Doing

1. **Stop adding signal families before one is graded.** Part 29's eight, Part 27's two phases, the cohort monitor — all wait for Phase 3.
2. **Stop amending the frozen architecture with appendices.** Replace text; do not append parts.
3. **Stop maintaining seven planning documents.** One.
4. **Stop producing reports in chat.** Every report the operator reads is generated from the store or it is not a report.
5. **Stop restating levels.** A metric whose half-life exceeds the report's cadence is not reprinted; only its change is.
6. **Stop treating tail scenarios as 25 peers.** Families with instances.
7. **Stop building the Thailand pillar, the privacy-coin theme, the DAT template, and the crypto three-horizon forecast** inside the trading system.
8. **Stop designing the dashboard.** Email is the dashboard.
9. **Stop authoring code on the box.** Four exceptions in a day; two were justified. The deploy key is a recovery path.
10. **Stop estimating in nominal hours against a 230-hour backlog.** Estimate in phases with exit criteria, and let Phase 6 be earned.

---

# Q. Unknowns — questions this audit cannot answer

1. **Whether any of the nine signal families has an edge.** Zero graded decisions. The only calibration datum is 0/13 pins — an honest start and no information.
2. **What the code actually looks like** — coupling, coverage, brittleness. The repository pass in Section M answers this.
3. **Whether the operator will read two emails a day.** The system's usefulness is bounded by this, and it is untested.
4. **How the dials behave across a regime change** — none has occurred inside the register's life. *Evidence and Inference* says this cut will be thin for years.
5. **Whether the Read-Only-off gate (Gate 2) can be reached** — it requires a month of validated paper refusals, and the refusals require the order gate, which is Phase 5.
6. **The true cost of the LLM layer at nine runs a day** — unmeasured because the runs do not exist; the exception-first design in Section I should cut it by most.
7. **Whether the pin log's tolerance (25 bps) is right** — declared, never tuned, correctly; but a base rate of zero says nothing about the tolerance until n is large.
8. **Whether the 0DTE-in-EOD exclusion is complete** — the intraday cadence that would prove it is unbuilt.

---

# The Final Question

*If I inherited this system today and my own capital depended on the quality of its decisions for the next ten years:*

**I would preserve** the point-in-time store, the immutable register, the registry's refusal to trigger, the validator family's posture, the exposure engine with its cross-check, the Brookfield restriction, the Doctrine's risk layer, and the honesty conventions. These are worth more than everything else combined, and most trading systems — retail or institutional — never build them. I would also preserve the library, and stop adding to it: twenty-four papers is a curriculum, not a backlog.

**I would tear down** the planning sprawl — seven documents to one, 32 parts to a frozen reference — and the report layer as designed: five peer reports become four outputs and alerts, all generated from a state object none of them currently has. I would tear down the pretense that a 230-hour backlog is a plan for someone with five hours a week.

**I would rebuild** the consumer side around three things in this order: *delivery* (the operator receives the system's output without asking), *state* (one market-state object every output reads), and *grading* (every decision, taken or not, scored by code at its horizon). Nothing else in the roadmap matters until those three exist, because until they do the system is a well-instrumented pipeline feeding a conversation.

**I would refuse to add** any new signal family, data vendor, asset-class module, or report until 150 decisions have been graded across two regimes — and I would write that refusal into the registry as a rule rather than into a document as an intention, because the last three days show that intentions in documents get amended. I would refuse the prediction-market divergence engine, the meme lifecycle machine, the privacy-coin theme, the DAT template, and the Thailand pillar, not because they are wrong but because each is a claim to know something interesting, and the Doctrine's own first distinction — knowing something interesting versus having a repeatable edge — says that interesting things belong in papers and edges belong in the register, and the register is empty.

The candid summary: **the system's design is better than its evidence by a wide margin, its safeguards are better than its delivery, and its plan is larger than its operator.** The fix for all three is the same — grade before you expand, deliver before you design, and cut the plan to what closes the loop.

---

# Appendix — Log of Data and Analyses Removed from the System (6 Sep 2026)

*Every item retired by this audit, with the reason and where the idea is archived so it can be revived if the evidence changes. Nothing on this list was deleted from the documentation; each remains in the architecture document at the part cited.*

| Item | Was | Reason retired | Archived at | Revival condition |
|---|---|---|---|---|
| Prediction-market phase 2 — cross-asset divergence engine, canonical-event abstraction, ForecastEx via Gateway | Part 29.8 (~6h) | A research project on top of an unbuilt v1; no consumer until the tail table has a graded probability column | Architecture Part 29.8 | PM v1 (6d) live for two quarters with a Brier series |
| DAT entity type — CYPH instance, fully-diluted-share-per-ZEC KPI | Part 29.6 (~3h) | Zero contribution to the four books' edges; single-instance template | Architecture Part 29.6 | A second instance with a register decision attached |
| Crypto running forecast at 12m / 3y / 5y | Part 12 (~4h) | Ungradeable at the long horizons within the system's life; a narrative, not a metric. **The eight crypto metrics are kept** | Architecture Part 12 | Never as a forecast; the 12-month horizon may return as a graded scenario weight |
| Thailand / THB as a global pillar feeding the dials | Session 12.5 | Personal-finance context inside a regime input; **becomes a standalone quarterly report (6m)** | Architecture Session 12.5; `thailand-monitor-spec.md` | — (relocated, not removed) |
| The dashboard | Various; never built | Requires the operator to look; email is the dashboard; alerts find him | Narrative Part 1 (alerting pulled ahead of dashboard) | Never |
| 25 tail scenarios as 25 peer states | Part 16 tail watch table | Collapsed to ~6 mechanism families with the 25 as instances; Brier per family | Architecture Part 16; *The Twenty-Five* paper | — (restructured, not removed) |
| 11 macro pillars as peer scores | Sessions 12–13, Monthly | Subordinated to the three dials with a stated mapping; pillar scores no longer printed as eleven peers | Architecture Session 12 | — (restructured) |
| Top & Bottom as a standalone report | Session 10–14, narrative Part 5 | A state variable — verdict and composite — inside the state object, printed in Monthly and Weekly; **the paper and the calibration harness are kept** | Architecture Part 23; *Tops and Bottoms* paper | — (subordinated) |
| Alternative Asset as a standalone report | Sessions 10–11 | A Monthly section; its fetchers are kept (6i) | Architecture Sessions 10–11 | — (merged) |
| Disruptive Themes as a monthly | Part 13 | Quarterly; structural by definition; went stale as a monthly | Architecture Parts 13, 13b | — (re-cadenced) |
| The nine intraday Daily runs as reports | Part 28 | Replaced by three anchors and five conditionals; the LLM called only on exception | Architecture Part 28 | — (restructured) |
| v18 / v19 / deferred backlog (~45h of items) | Part 5 deferred; master schedule | Claims without evidence infrastructure; each may be re-proposed individually against the 6h gate | Architecture Part 5; master schedule v18/v19 rows | Individually, on a graded family it extends |
| Six of seven planning documents | narrative, roadmap, compressed plan, v17 build plan, work plan v2, master schedule | Merged into one roadmap with one status ledger; the architecture frozen as reference at Part 32 | The documents themselves, retained read-only | Never |
| The `-ALT-branch` paper duplicates | outputs | Superseded by the canonical editions | Deleted from outputs | Never |
| Hard word counts on reports | Audit #3 first draft, Section I | Replaced by "zero budget for repetition, insight as long as it needs, insight first" | This audit | Never |
| FlashAlpha Basic | Part 9 | Self-computed exposure engine replaced it; vendor kept as an occasional cross-check only | Architecture Part 9 | Never as a data source |
| cron-job.org | Part 24 | Replaced by a `schedule:` block; deleted after the 1 October run proves the replacement | Architecture Part 32.1 | Never |

*Kept on review, against the audit's first draft:* Part 29.5 privacy-coin theme (operator's ruling — potential structural theme; logger only until 6h); Part 29.4 and 29.7 loggers (start in 6a; analysis gated in 6h); the news and narrative scan (elevated to a first-class function, Section I).
