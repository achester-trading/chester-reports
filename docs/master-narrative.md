# Market Intelligence System
## The Master Narrative

*A five-report architecture for reading markets across every time horizon — from the generational arc down to the next thirty minutes of tape.*

---

## How to Use These Reports

> **Read from the top down, act from the bottom up.** The slow reports tell you which way to lean; the fast reports tell you when to move.
>
> No single report is sufficient on its own — a daily setup that ignores the structural backdrop is a guess, and a structural thesis that never touches the tape is an opinion. The discipline is to let each horizon constrain the one beneath it: the Disruptive Themes Report sets the regime, the Monthly Macro Report sets the posture, the Top & Bottom Report flags the turn, the Alternative Asset Report confirms or contradicts from outside equities, and the Daily Cascade executes.
>
> When two horizons disagree, **the slower one wins on direction and the faster one wins on timing.** Your job is to hold all five in view at once and size your conviction to their agreement.

---

## The Five Reports at a Glance

| # | Horizon | Report | Cadence | Automation |
|---|---------|--------|---------|------------|
| 1 | Generational | **The Disruptive Themes Report** | Every 2 months / on regime shift | Manual writeup |
| 2 | Strategic | **The Monthly Macro Report** | Monthly + weekly delta | Full pipeline |
| 3 | Structural | **The Top & Bottom Report** | Monthly + weekly + event-driven | Full pipeline (view over Monthly) |
| 4 | Cross-Asset | **The Alternative Asset Report** | Weekly / on correlation break | Partial pipeline |
| 5 | Tactical | **The Daily Cascade** | Intraday | Hybrid (AI populate + analyst) |

---

## 1 · The Disruptive Themes Report
### *The Generational Frame*

**Function** — The longest lens in the system. It maps the structural, multi-year risks that define the entire distribution of possible outcomes: not what the market does next week, but what kind of era we are trading in.

It is built on **five structural factors** (the "Five-Force Framework" — the fifth was promoted from the former amplifier list as of the Q3 2026 refresh):

| | Factor | Focus |
|---|--------|-------|
| **I** | AI / Valuation | Concentration, capex cycle, multiple fragility |
| **II** | Fiscal / Debt | Deficits, the Treasury rollover wall, supply |
| **III** | Geopolitical / Geoeconomic | Economic warfare as the leading channel, kinetic conflict as the tail; carries the Hormuz divergence as a named indicator and the decade-horizon theater board (Taiwan foremost) |
| **IV** | Dollar / Liquidity | Reserve status, gold's structural reallocation, Fed independence |
| **V** | Monetary Architecture in Transition | The monetary system's form and plumbing in regime change — detail in the field guide |

Each factor receives the same **seven-element treatment**: the 101, historical context, a current-events dispatch, two-to-three-year probability-weighted paths, ten-year scenario families, an instrument panel, and factor couplings. Layered on top are the remaining **amplifier categories** and — most importantly — an **interaction matrix** tracing the compound pathways between factors, with the **yield channel identified as the common bus** across all five. The synthesis layer produces a scenario distribution with explicit probabilities and S&P drawdown ranges, plus a **composite score on the same −2…+2 band convention as the Top & Bottom Report** (as of the Q3 2026 refresh: −1.2, OVEREXTENDED, at the edge of TOP SIGNAL).

The report carries a **discipline stack** alongside the analysis: Steelman, What Would Change My Mind (in both directions), Calibration Check, External Calibration, Media Scan, and a Gaps Register. External lenses calibrate the framework: the WEF Global Risks Report, Ray Dalio's Big Debt Cycle (applied with critique, as a named lens), and a Broader Calibration Panel.

**Companion papers** (referenced by name, never numeral, per the library convention): *Foundations and Field Guide to the Five-Force Framework* is the report's deep-context companion — the decoder ring, factor chapters, composite machinery, and discipline-section rationale live there, so each bimonthly refresh can be read efficiently. *The Twenty-Five* carries the tail-scenario register — 25 scenarios organized by mechanism family, each with mutation tracking — which the report's tail assessment summarizes.

**What it answers** — *What is the shape of the era? Where are we in the long cycle, and what are the tail risks that would rewrite everything?*

**How often** — Every two months as a baseline, plus a forced refresh whenever a major structural input changes (a Fed leadership transition, a new WEF Global Risks Report, a geopolitical rupture). Annually calibrated against the WEF consensus to check for framework drift.

**Production:**

| | Detail |
|---|---|
| **Storage** | Navy-accordion JSX in the house style (Georgia serif, #0f2747), with standalone HTML and Markdown editions. Current: the Q3 2026 prototype with Factor V, the tail assessment, steelman, both-direction change-my-mind, calibration check, and media scan; the Master Refresh Prompt ships as an appendix of the report itself. The refresh also emits a `disruptive_themes_state.json` snippet (regime, composite, modal drawdown, top scenarios) for the System State Dashboard. |
| **Generation** | Manual writeup. Refresh by running the Master Refresh Prompt (carried in the report's own appendix) in a fresh chat. Claude rewrites the factor objects, recalibrates against external lenses, re-emits the report, and emits the state JSON snippet. |
| **Automation level** | **Manual.** No data pipeline — the five factors and amplifiers are research-driven prose, not metric-driven scoring (the composite is judgment-scored against stated bands, not computed). Inputs are external reports (WEF, Dalio, commentary) read by hand. The state-file write is one operator action every 60 days. A **programmatic refresh trigger** flags the dashboard when conditions warrant an early refresh: any Top & Bottom overlay ACTIVE for >30 days, persistent Alt Asset correlation break >30 days, Monthly composite drift >0.5 without a DT refresh, or DT regime ↔ Monthly Matrix modal scenario mismatch for >30 days. |

> This report changes slowly. That is the point — it is the bedrock the other four are built on.

---

## 2 · The Monthly Macro Report
### *The Strategic Posture*

**Function** — The operating posture for the month ahead, expressed as a single composite score across ten pillars: macro fundamentals, economic activity, dollar & global, inflation, sentiment & positioning, credit, equity structure, liquidity, geopolitical, and narrative. The composite maps to a regime label — **NEUTRAL · OVEREXTENDED · TOP SIGNAL · BOTTOM WATCH** — which in turn dictates position sizing for the entire month.

Pillar 5 (Sentiment & Positioning) decomposes into eight sub-clusters (5A through 5H), the last of which tracks **quarterly 13F smart-money positioning** — Berkshire's record $397B cash, Loeb's collapsed long book, Aschenbrenner's $8.46B AI hedge stack, Burry's doubled put position. It also carries crypto sentiment cross-checks (BTC/Gold ratio, Crypto Fear & Greed, stablecoin flows) — those same signals live in greater depth in the Alternative Asset Report; the Monthly's version is a summary cross-check, refreshed monthly.

Each pillar is organized into **clusters** (e.g. Pillar 2 breaks into 2A through 2F covering labor, growth nowcasts, leading indicators, housing complex, manufacturing/services surveys, and consumer stress). The cluster structure is what makes the report editable in surgical sections rather than as a monolithic document.

Pillar 10 (Narrative) is the qualitative commentary layer — aggregating Hartnett's Flow Show, Howard Marks memos, Lyn Alden, Gundlach, Bianco, Pozsar's old work, and curated X/Twitter macro voices into theme-organized synthesis.

#### Report Output Structure

The Monthly Macro Report's output is not just a composite score — it's a structured deliverable with five distinct sections:

| # | Section | What it carries |
|---|---|---|
| I | **Executive Summary** | Regime characterization, HEADWINDS / TAILWINDS / CROSS-CURRENT tables, market-impact synthesis explaining how the pillars combine |
| II | **Pillar Snapshot** | 10-pillar status grid distilled into a single scannable view |
| — | **10 Pillar Sections** | Each leads with a 4-paragraph narrative synthesis (regime → data story → cross-pillar connection → matrix implication), then supporting tables organized by cluster, then "What Changed Since Last Report" + "Watch in Next 30 Days" |
| III | **Macroeconomic Matrix** | Five probability-weighted scenarios with S&P drawdown ranges and bond/gold reactions — this is the structured forward view that feeds the translation table |
| IV | **Appendix** | A (Coverage diagnostics), B (Production pipeline roadmap), C (Illustrative Options-Trade Expressions — three trades: 3M SPX put spread, 6M GDX call spread, 12M TLT or QQQ put spread; parallels the Top & Bottom Report's Appendix D Options Portfolios) |

**Version history (recent):** v11 (May 29) expanded Cluster 2F (Consumer Stress) with mortgage delinquency, **subprime auto 60+ at a record 6.90%** (the single best early consumer-stress signal — preceded both 2007 and 2019 broad-consumer downturns), CC transition-to-delinquency, and surfaced a **K-shaped consumer reading** (bottom tier breaking, prime tier improving). This is conceptually parallel to the Top & Bottom Report's Private Credit Bifurcation trigger. v15 added Appendix C (Illustrative Options-Trade Expressions). **v16 (current)** was a QA pass — section numbering normalized (collapsed IV/V/VI into a single IV) and the methodology note refreshed.

**What it answers** — *How aggressive should I be this month? What is my default position size, which pillars are deteriorating, and what scenarios am I weighting?*

**How often** — Monthly, with the composite score and sector baseline refreshed on the first trading day. A weekly delta covering the five fast-moving pillars (3, 5, 6, 7, 10) runs each Sunday evening.

**Production:**

| | Detail |
|---|---|
| **Storage** | VPS pipeline at `/opt/macro-report/`. Source of truth is `data/timeseries.db` (SQLite). Output is a styled HTML file plus its canonical markdown source (latest: `monthly_macro_report_v16_2026-05-24.md` → `monthly_macro_report_2026-05-24.html`). The HTML uses native `<details>`/`<summary>` collapsible sections with a navy + serif aesthetic, mobile-responsive tables, and Expand-all/Collapse-all controls. The SQLite database is the central nervous system of the entire five-report architecture — every other report eventually reads from it. |
| **Generation** | Python fetchers (FRED API, yfinance, IBKR, lightweight scrapers for AAII, CFTC, alternative.me, Caldara-Iacoviello GPR, OpenInsider) pull data into SQLite. A master orchestrator stitches the payload and hands it to Claude Opus 4.7 via API with a prompt that constrains output to the data box — no figures introduced outside the JSON. The Weekly delta uses Sonnet 4.6 for cost. The build script renders both the canonical markdown and the styled HTML version. |
| **Automation level** | **Full pipeline.** Cron schedule: monthly on first Sunday 8pm ET; weekly on Sunday 8pm ET. Roughly 70% of metrics come from FRED API; 25% from yfinance/IBKR/free scrapes; the remaining 5% (SLOOS quarterly, paywalled desk notes, FMS details, **subprime auto ABS 60+ delinquency** — no clean free FRED series, requires light scrape from Wolf Street / Fitch / S&P or manual monthly entry, **Cluster 5H 13F filings** — `fetch_13f.py` quarterly per Phase 4 of the build plan) are manual entry slots in the orchestrator. A QC pass audits the writeup against the source JSON to flag hallucinations before delivery. |

> The Monthly Macro Report is the hinge of the whole system: slow enough to filter noise, fast enough to adapt to the cycle. It sets the standing baseline the Top & Bottom Report escalates within — and its SQLite database is the shared substrate every other report ultimately reads from. The Macroeconomic Matrix in Section III is the structured probabilistic forward view that the translation table's scenario rows ultimately reflect.

---

## 3 · The Top & Bottom Report
### *The Turn Detector*

**Function** — The system's early-warning siren for a major structural reversal, calling **both** tops and bottoms. Where the Disruptive Themes Report describes the era and the Monthly Macro Report describes the standing posture, the Top & Bottom Report does one thing with precision: it watches a fixed set of threshold triggers and tells you when the risk of a regime reversal is rising in either direction. The report integrates the **Hartnett framework** (Bull & Bear Indicator, FMS cash, melt-up completion triggers) as a structural input.

The composite is built from **eight categories** with weights tuned through backtesting:

| # | Category | Weight |
|---|---|---|
| 1 | Valuation | 17% |
| 2 | Momentum & Trend | 12% |
| 3 | Breadth | 15% |
| 4 | Sentiment & Positioning | 22% |
| 5 | Leading Indicators | 10% |
| 6 | Macro & Liquidity | 24% |
| 7 | AI Concentration (Mag 7 / NVIDIA / Semis) | 0% *(informational)* |
| 8 | Bank Stress | 0% *(informational)* |

Each of roughly 50 indicators is scored on a **−2 to +2 scale** through dedicated threshold functions. The weighted composite maps to a verdict: **TOP SIGNAL · OVEREXTENDED · NEUTRAL · CONSTRUCTIVE · BOTTOM SIGNAL**.

#### Three Parallel Signals — Composite-Independent Overlays

The major architectural feature of v3 Live: three overlays that fire **independently of the composite**, each designed to catch a specific failure mode of composite-style scoring documented in calibration testing.

| Overlay | Catches Failure Mode | Trigger Logic | Status (May 23, 2026) |
|---|---|---|---|
| **Concentration & Complacency** | Valuation tops the composite misses (2000, 2022) | 3+ of: Fwd P/E ≥20x · CAPE ≥30 · ERP ≤1.5% · Top-10 ≥25% · VIX ≤18 | **ACTIVE** — 5/5 firing |
| **HY Spread Acceleration** | Credit-cycle tops where absolute HY level still looks tight (2007) | HY acceleration off 12m trough · 30d HY/IG widening · IG OAS level | CLEAR — 0/4 firing |
| **Liquidity & Funding Stress** | Plumbing stress before it becomes credit stress (2019 repo, 2025 funding strains) | Fed net liquidity YoY · Bank reserves vs LCLOR · SOFR–IORB · ON-RRP · TGA volatility | CLEAR — 2/5 firing |

Each overlay is a **CONDITION**, not a timing signal. The 2024 yen-carry episode produced a Concentration fire even though no crash followed — the signal was correctly identifying that the market was expensive, just silent on when. The overlays' value is structural: they catch what the composite is mathematically prone to missing.

#### The Ten Triggers

Expanded from six to ten in v3 Live (each with an inverse threshold that arms a BOTTOM SIGNAL):

| # | Trigger | Top Signal | What it adds |
|---|---------|------------|---|
| 1 | SpaceX IPO | S-1 filed | Hartnett melt-up completion |
| 2 | OpenAI IPO | S-1 filed | Second Hartnett completion signal |
| 3 | CPI breaches 4% | approaching/exceeding | Forces Fed back to tightening |
| 4 | HY OAS > 350bp | crossing | Credit-market confirmation |
| 5 | % SPX > 200-DMA < 50% | breaking | Breadth deterioration at price highs |
| 6 | B&B Indicator > 8.0 | active | Hartnett sell signal armed |
| 7 | 2s10s Un-Inversion | post-inversion period | Recession typically follows un-inversion |
| 8 | Curve Re-Inversion | 3m10y or 2s10s flips back | Second-chance recession signal |
| 9 | Credit Spread Acceleration | 30d widening rate | Rate-of-change leads absolute levels at turns |
| 10 | Private Credit Bifurcation | private stressed vs public tight | New transmission channel not present pre-2020 |

Trigger states: **CLEAR / APPROACHING / TRIGGERED**. Roll-up status (CLEAR / WATCH / ALERT) is composite-based — exact trigger-count thresholds for each tier are **TBD pending verification against the live `compute_scorecard.py`**. Prior versions used CLEAR (0–1), WATCH (2), ALERT (3+) when the trigger set was six; whether the thresholds were scaled proportionally for the expanded ten-trigger set or held constant has not been confirmed in this document.

**What it answers** — *Is the regime about to turn — up or down? How many independent warning lights are on?*

**How often** — Three cadences. Monthly refresh on the first trading day after CPI/ISM/FMS data lands. Weekly refresh Sunday evening for the fast-moving inputs (Pillars 5, 6, 7). Event-driven on any FRED release that touches a threshold metric.

**Production:**

| | Detail |
|---|---|
| **Storage** | Lives inside the Monthly Macro Report's VPS pipeline at `/opt/macro-report/top_report/`. Outputs `/opt/macro-report/shared/status.json` (small payload consumed by the Daily Cascade) and archives full snapshots as `top_report/data/top_report_YYYY-MM-DD.json`. Footer label: **v3 Live**. |
| **Generation** | `compute_scorecard.py` (~700 lines, stdlib only) reads the Monthly's `timeseries.db`, runs every indicator through a `score_*` function, builds the eight categories, computes the weighted composite, evaluates the ten triggers AND the three parallel-signal overlays, and writes both output files. Two report-specific fetchers feed the metrics not in the Monthly DB: `fetch_bb_indicator.py` (ZeroHedge Hartnett mirror, manual override always wins), and `fetch_ipo_watch.py` (SEC EDGAR S-1 filings monitor for SpaceX and OpenAI). A Cloudflare Worker caches `status.json` for 60 seconds and serves it to the Daily Cascade. |
| **Automation level** | **Full pipeline — view over Monthly.** Most core indicators are read directly from the Monthly's SQLite (no duplicate fetching). Report-specific inputs are the B&B Indicator, IPO Watch, plus the overlay-specific series (SOFR–IORB, ON-RRP, bank reserves vs LCLOR, HY acceleration math). Hook in Monthly's `fetch_fred.py` triggers `compute_scorecard.run()` at the end of each fetch cycle, so `status.json` stays fresh whenever Monthly data lands. Unit tests guarantee the composite matches the React artifact's reading. |

The report ships with **four appendices** that give the reader the structural backing behind the headline composite:

- **Appendix A · Valuation Deep Dive** — Forward P/E, trailing P/E, CAPE, P/B across S&P/NDX/Dow with 5-yr, 25-yr, ATH, and typical-correction benchmarks. Includes implied SPX prices at prior bottoms (2022 / 2020 / 2009).
- **Appendix B · Prior Market Comparisons** — Side-by-side metric tables for the last four major tops (Jan 2022, Feb 2020, Oct 2007, Mar 2000) with "what's similar / different / may be structurally different" framing. Deliberately neutral on whether each precedent is a strong analog.
- **Appendix C · Threshold Reference** — Full five-band scoring ranges (−2 to +2) for every metric in the scorecard, so the reader can see not just where each indicator sits today but what level pushes it into the next band.
- **Appendix D · Options Portfolios** — Scenario-weighted 3-month, 6-month, and 12-month portfolios designed for positive probability-weighted expected return given the report's signals. Each portfolio defines max loss across all scenarios; no individual trade is all-weather (impossible), but the portfolio is.

> This is the report that earns its keep at the multi-day-to-multi-week horizon — the gap the Disruptive Themes Report (too slow) and the Daily Cascade (too fast) both miss. Because it's a view over the Monthly's database rather than its own pipeline, the same composite number flows guaranteed-consistent through all three reports that consume it. The three parallel signals are the structural innovation of v3 — they catch what composite scoring is mathematically prone to miss.

---

## 4 · The Alternative Asset Report
### *The View From Outside Equities*

**Function** — A multi-asset surveillance layer covering everything that is *not* US large-cap equity. Coverage spans precious metals (gold, silver), energy (oil, natural gas), industrial commodities (copper), crypto (BTC, ETH, SOL, ZEC), real estate (US REITs, international REITs), emerging markets and China, and non-US currencies (DXY, EUR, JPY, CNY).

For each asset it tracks **price and momentum across multiple horizons** (1W / 1M / 3M / 6M / 1Y / YTD), technicals (RSI, moving averages, trend), supply/demand drivers, institutional positioning (COT for futures-traded, ETF flows + corporate treasury for BTC, on-chain metrics for crypto generally, central bank flows for gold), consensus/outlook, and recent trading environment narrative.

Its most valuable output is the **cross-asset correlation matrix** — every asset mapped against US equities (SPY) and bonds (TLT), with rolling windows that reveal how correlations shift over time. Each pair flags divergence when recent correlation breaks from its textbook expectation (e.g. the engineered sample shows a gold/US-real-estate pair at −0.18 recent vs +0.12 historic). A correlation break here is often the earliest signal of a liquidity event, before it shows up in the equity tape.

**What it answers** — *What is the rest of the world telling me? Is the equity story confirmed or contradicted by gold, oil, crypto, the dollar, and credit-sensitive assets?*

**How often** — Weekly as a baseline, plus an immediate look whenever a key correlation breaks regime.

**Production:**

| | Detail |
|---|---|
| **Storage** | React JSX dashboard (`alt-asset-dashboard.jsx`) backed by `dashboard_data.json` and four supporting Python modules (`narratives_extended.py`, `cases_and_positioning.py`, source registries). Bloomberg-terminal-inspired aesthetic — dark background, sharp monospace, single hot accent color. Total artifact ~1.37 MB. Persistent storage via the artifact's storage API so notes and customizations survive across sessions. As of architecture v2.0, the weekly pipeline also emits `alt_asset_state.json` to `/opt/macro-report/shared/` (correlation regime, breaks, flags) for the System State Dashboard, and writes crypto sentiment values back to Monthly's `timeseries.db` so Pillar 5 reads from a single source. |
| **Generation** | Hybrid. The data schema and fetcher scaffolds exist (`altdata/sources/etf_flows.py`, etc.) for ETF flows, MicroStrategy/Strategy treasury purchases, whale wallets, exchange flow data via Farside Investors, Glassnode, CryptoQuant. Per-asset case bullets (bull/bear/flat) and trading environment narratives are written as durable structural prose in `cases_and_positioning.py`. Weekly LLM run via `weekly_scan.py` produces per-asset narrative updates (~$0.30/week Claude API cost). |
| **Automation level** | **Partial pipeline — explicitly the weakest link in the architecture.** Schema is production-ready. The structural prose is durable (good for months without rewrite). The live weekly news-scan layer — pulling from WGC, EIA, Glassnode, hyperscaler capex disclosures — is **not yet wired**; several fetchers currently return synthetic sample data. To get truly live correlation breaks and positioning updates, the server-side fetching/summarization pipeline needs to come online. The System State Dashboard surfaces `pipeline_health: "partial"` so the operator sees this every morning. Recommended next major automation work; see Architecture Improvements doc for the wiring spec. |

> Outside-the-equity-stack signals frequently lead equity moves. Gold crossing Treasuries as a share of global reserves, for example, is a Disruptive-Themes-grade signal that surfaces here first. The report's value is high even with partial automation, because the cross-asset correlation matrix is structural and the narratives are durable; the gap is the timeliness of the news-scan layer.

---

## 5 · The Daily Cascade
### *The Execution Layer*

**Terminology ruling (from the v17 work plan):** "**tiers**" refers exclusively to the five-report stack (Tier 0–5 in this document); the Daily Cascade's internal sections are "**blocks**" (Direction, Market Base, Confirmation, Backdrop, Execution in the v17 design). The two words are never interchangeable.

**Function** — The tactical engine. A sequence of reports through each session, each building on the last, that turns the strategic posture into specific, timed, dollar-sized trade setups.

| Time | Report | Focus |
|------|--------|-------|
| 07:00 AM | Morning Brief | Pre-market frame + cross-report sync |
| 09:20 AM | Pre-Open Flow | Global closes, gap setup |
| 10:00 AM | Open Analysis | First 30-min character |
| 12:00 PM | Midday Read | Morning scorecard |
| 03:00 PM | Into the Close | MOC, gamma pin dynamics |
| 04:30 PM | Close Debrief | Thesis grade, catalyst-reaction carry-forward |
| 09:30 PM | Night Watch | Asia open, overnight bias |

**Weekly bookends:**

| Time | Report | Focus |
|------|--------|-------|
| Fri 6:00 PM | Weekly Reflection | *Retrospective* — grade every setup |
| Sun 9:30 PM | Weekly Forward Plan | *Prospective* — the week-ahead playbook |

The 7AM Brief carries a **Cross-Report Coordination block** that pulls the Monthly Macro composite, the Top & Bottom trigger watch, and the prior week's delta into the day — so every tactical decision is anchored in the slower horizons. The 4:30 PM Debrief's catalyst-reaction analysis carries forward into the next morning's BLUF, closing the daily learning loop.

**What it answers** — *What exactly do I do today, when, at what size, and with what stop?*

**How often** — Intraday, every session, plus the Friday/Sunday weekly bookends.

**Production:**

| | Detail |
|---|---|
| **Storage** | React JSX artifact (currently v12), rendered as a single-file Claude artifact. Persistent storage via the artifact's `window.storage` API — every saved report is keyed by date + report ID and survives across sessions. Saved reports browseable through the History panel. |
| **Generation** | Hybrid. The **AI Populate** panel fires a Claude call with `web_search` tool to fetch live market data for each report (prices, yields, sectors, GEX, news, crypto). Returns a JSON payload with confidence scores per field. The 7AM Brief additionally fetches `status.json` from the Cloudflare Worker to surface Monthly composite + Top & Bottom trigger watch. FlashAlpha proxy is planned for authenticated GEX data (overrides web-search GEX estimates with confidence 95 when available). Analyst fills the narrative, setups, and rationale fields by hand. |
| **Automation level** | **Hybrid.** Data fields auto-populate with confidence badges (HIGH/MED/LOW). Setup design, conviction grading, profit-taking plans, and the retrospective scoring loop are analyst-driven. The 4:30 PM Debrief's catalyst-reaction carry-forward is the system's primary closed-loop learning mechanism — the inferred underlying bias becomes the prior for the next morning's BLUF. |

---

## Tier 0 · The System State Dashboard

*New in architecture v2.0.* The five reports are nested lenses, but operating them requires holding all five in view at once — and previously that meant mentally composing the system state from five separate artifacts. The dashboard is the meta-view that sits above all five reports.

**Function** — A single artifact that renders the current state of every report in the architecture, computes the implied position-sizing tier by walking the translation table's conflict-resolution rule, and surfaces any stale reports or cross-tier disagreements as actionable conflicts.

**Output structure:**

| Block | Content |
|---|---|
| **Conflict banner** | Any stale reports (red/amber based on age vs cadence), Monthly ↔ Top & Bottom verdict mismatches, pipeline-health advisories |
| **Sizing synthesis** | The headline — current position sizing recommendation (e.g. *"25-40% normal · no new longs"*) with the conflict-resolution walk-through showing which tier drove which adjustment |
| **Five report tiles** | One per tier (Disruptive Themes / Monthly / Top & Bottom / Alt Asset / Daily) with current state, version, last refresh, and staleness indicator |
| **What to do today** | Concrete actions synthesized from the state — which reports to refresh, which positions to trim, which signals to watch |

**Production:**

| | Detail |
|---|---|
| **Storage** | React JSX artifact (`system-state-dashboard.jsx`), reads from `/opt/macro-report/shared/system_state.json` via the existing Cloudflare Worker (extended with a `/system-state` route). Falls back to embedded mock data if the live source is unreachable. |
| **Generation** | The Worker serves an aggregated state file built by `/opt/macro-report/orchestrator/build_system_state.py`, which composes per-report state files (`disruptive_themes_state.json`, `monthly_macro_state.json`, `status.json`, `alt_asset_state.json`, `daily_cascade_state.json`) into a single canonical document. Each producer is wired separately — see the Architecture Improvements doc for the per-report write specs. |
| **Automation level** | **Pipeline + manual.** The Monthly Macro, Top & Bottom, Alt Asset, and Daily Cascade producers run automatically on their existing cadences. The Disruptive Themes producer is a manual prompt appendix — the refresh prompt now emits a `state.json` snippet alongside the HTML, which the operator drops on the VPS (one file write every 60 days). |

> The dashboard is the morning command center — glance at it before the 7AM Brief, and you have the entire system in view in 10 seconds rather than reconstructing it from five separate documents. It is also the artifact that finally connects Disruptive Themes and Alt Asset to the data spine — both reports now write state programmatically rather than relying on analyst memory.

---

## How They Fit Together

Think of the architecture as **five nested lenses with a meta-view sitting above them**:

```
   ┌──────── TIER 0 · System State Dashboard ────────┐
   │   meta-view · sizing synthesis · conflicts      │
   └─────────────────────┬───────────────────────────┘
                         │ reads
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ DISRUPTIVE THEMES · the era                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ MONTHLY MACRO · the posture                             │ │
│  │  ┌─────────────────────────────────────────────────┐   │ │
│  │  │ TOP & BOTTOM · the turn                          │   │ │
│  │  │  ┌──────────────────────────────────────────┐   │   │ │
│  │  │  │ ALT ASSETS · the lateral check            │   │   │ │
│  │  │  │  ┌───────────────────────────────────┐   │   │   │ │
│  │  │  │  │ DAILY CASCADE · the execution     │   │   │   │ │
│  │  │  │  └───────────────────────────────────┘   │   │   │ │
│  │  │  └──────────────────────────────────────────┘   │   │ │
│  │  └─────────────────────────────────────────────────┘   │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### The Information Flow *(top down)*

- **The Disruptive Themes Report** sets the regime and the tail risks. It defines what "normal" even means this era, and which structural pillars the faster reports should weight most heavily.
- **The Monthly Macro Report** translates the era into a single posture and position size for the month. Its composite score — and, critically, its SQLite database — is the standing baseline the daily reports actually consume.
- **The Top & Bottom Report** watches for the moment that posture needs to shift. Its triggers are drawn from the same structural concerns the Disruptive Themes Report names — sentiment, inflation, credit, breadth, concentration — but rendered as live thresholds rather than narrative. It escalates the Monthly's standing read when triggers fire between refreshes.
- **The Alternative Asset Report** runs alongside the equity stack as a lateral confirmation. When gold, oil, crypto, the dollar, or credit diverge from the equity story, the correlation matrix flags it — often before the Daily Cascade sees it in the tape.
- **The Daily Cascade** executes within all of the above. The 7AM Brief reads the Monthly composite and Top & Bottom trigger watch via `status.json`; setups are sized to the Monthly posture as escalated by Top & Bottom; the night and weekly reports re-sync everything.

### The Feedback Loop *(bottom up)*

Information does not only flow down. The fast reports feed the slow ones:

- The Daily **4:30 PM Debrief** grades each thesis and carries the catalyst reactions forward — the raw material of pattern recognition.
- The **Friday Weekly Reflection** aggregates the week's setups and produces a Weekly Delta: which Monthly Macro pillars moved. That delta is the bridge from the daily horizon back up to the Monthly.
- **Persistent divergences** between the Daily Cascade and the Monthly Macro Report are the trigger to refresh the Monthly early; persistent structural shifts surfaced in the Alternative Asset Report or the Top & Bottom Report are the trigger to refresh the Disruptive Themes Report.

### The Governing Rule

> When horizons disagree, the slower report wins on **direction** and the faster report wins on **timing.**
>
> A Disruptive Themes regime that reads *"late-cycle, fragile"* and a Daily Cascade that says *"positive gamma, buy the dip"* are not in conflict — you buy the dip (timing) while keeping size reduced and stops tight (direction).
>
> Size your conviction to the **agreement** across the five. Full size belongs only to the trade that all five horizons endorse at once.

---

## Interdependencies & The Skip-Gap Analysis

### The Central Substrate

The architecture has a **central node**: the Monthly Macro Report's SQLite database at `/opt/macro-report/data/timeseries.db`. This is the single source of truth that the Top & Bottom Report reads from as a view, and that the Daily Cascade consumes derivatives of via `status.json`. As of architecture v2.0, all five reports also write a state file to `/opt/macro-report/shared/`, which the System State Dashboard (Tier 0) aggregates into a single canonical `system_state.json`.

The updated dependency graph:

```
                    [Disruptive Themes] ─── disruptive_themes_state.json ──┐
                            │                                              │
                            │ (informs the era frame)                      │
                            ▼                                              │
                    [Monthly Macro] ─── timeseries.db ─── [Top & Bottom]   │
                            │                                    │         │
                            │ writes                  writes     │         │
                            ▼                            ▼       │         │
                  monthly_macro_state.json         status.json   │         │
                            │                            │       │         │
                            └────────────┬───────────────┘       │         │
                                         ▼                       │         │
                                  [Daily Cascade] ───────────────┘         │
                                         │                                 │
                                         │ writes                          │
                                         ▼                                 │
                              daily_cascade_state.json                     │
                                                                           │
                  [Alternative Asset] ─── alt_asset_state.json ────────────┤
                  (independent feed,                                       │
                   weekly + crypto writeback to SQLite)                    │
                                                                           ▼
                                  ┌──────────────────────────────────────────┐
                                  │   build_system_state.py aggregator       │
                                  │   → /shared/system_state.json            │
                                  └────────────┬─────────────────────────────┘
                                               │ served via Cloudflare Worker
                                               ▼
                                    [System State Dashboard · Tier 0]
                                       meta-view · sizing synthesis
```

Three reports — Monthly, Top & Bottom, Daily — share the SQLite substrate and are tightly coupled. Two reports — Disruptive Themes and Alternative Asset — operate in parallel to the spine but **now write programmatically** to the shared state directory (architecture v2.0 fix). The dashboard reads everything.

### What Each Report Consumes and Produces

| Report | Consumes | Produces | Read by |
|---|---|---|---|
| Disruptive Themes | External research (WEF, Dalio, commentary) | Generational regime + scenario distribution + `disruptive_themes_state.json` | System State Dashboard; analyst judgment (caps sizing) |
| Monthly Macro | FRED, yfinance, IBKR, scrapers, manual entries, Alt Asset crypto writeback | `timeseries.db` (SQLite) + monthly HTML report + `monthly_macro_state.json` | Top & Bottom Report; System State Dashboard; analyst |
| Top & Bottom | `timeseries.db` + B&B Indicator + IPO Watch | `status.json` + archived snapshots | Daily Cascade 7AM Brief; System State Dashboard |
| Alternative Asset | Independent fetchers (ETF flows, on-chain, COT) + manual narratives | Dashboard + correlation matrix + `alt_asset_state.json` + crypto writeback to Monthly's SQLite | System State Dashboard; Monthly Pillar 5 (crypto values) |
| Daily Cascade | `status.json` + AI Populate (web search) + FlashAlpha (planned) + manual analyst input | Saved daily/weekly artifacts + `daily_cascade_state.json` | Analyst execution; System State Dashboard |
| **System State Dashboard** (Tier 0) | All five state files via `build_system_state.py` aggregator | Sizing recommendation + conflict surface + actionable callout | Analyst (every morning) |

### The Skip-Gap Analysis

What breaks if you skip generating a given report?

**Skip the Disruptive Themes refresh** (every-two-months cadence missed):
- *Immediate impact:* None mechanical — no other report consumes it programmatically.
- *Drift risk:* The implicit "era" frame goes stale. After 3+ months without a refresh, you risk treating a regime-changing input (new Fed chair, fiscal regime break, new WEF Global Risks Report) as a passing headline rather than a structural shift. The Disruptive-Themes-grade signals from the Alt Asset Report (gold/Treasuries reserve flip, etc.) lose their interpretive anchor.
- *Recovery:* Annual WEF calibration check usually catches drift. Force a refresh whenever the Alt Asset or Top & Bottom report flags a structural shift the current Disruptive Themes regime doesn't explain.

**Skip the Monthly Macro run** (monthly cadence missed):
- *Immediate impact:* **Severe — the entire spine goes blind.** The Top & Bottom's `compute_scorecard.py` has nothing fresh to read. `status.json` either goes stale or fails to update. The Daily Cascade's 7AM Brief shows last month's composite and triggers, framed as current. The Weekly Delta has no new month-end baseline to compare against.
- *Drift risk:* If skipped a full month, the entire system is operating on stale fundamentals while the daily reports continue producing tactical setups against an outdated posture.
- *Recovery:* This is the one report you cannot afford to skip. The cron + manual orchestrator on the VPS is designed so it can run unattended; intervene only if a fetcher fails.

**Skip the Top & Bottom run** (monthly/weekly cadence missed):
- *Immediate impact:* **Significant.** The Daily 7AM Brief reads stale `status.json` — composite shown but trigger watch is stale. If a trigger threshold crossed since the last run, the Daily Cascade has no signal of it.
- *Drift risk:* The architecture exists specifically to catch turn-risk at the multi-day-to-multi-week horizon. Skipping the weekly Sunday refresh means trigger crossings during the week go un-flagged until the next monthly run.
- *Recovery:* Because the Top & Bottom is a view over the Monthly's DB, the recovery is fast — re-running `compute_scorecard.py` against fresh Monthly data takes seconds. Event-driven trigger evaluation (`fetch_fred.py` calls `compute_scorecard.run()` at the end of each cycle) provides automatic backup.

**Skip the Alternative Asset Report run** (weekly cadence missed):
- *Immediate impact:* Moderate. The lateral cross-check on the equity stack goes stale. Correlation breaks that would normally escalate caution one tier are missed.
- *Drift risk:* Highest-impact misses are during correlation regime changes. A gold/Treasuries reserve flip, a crypto-equity correlation break, or a dollar-equity decoupling that the report would have flagged becomes invisible to the system. The Daily Cascade continues executing within the Monthly's posture as if outside-the-stack signals don't exist.
- *Recovery:* Force a refresh whenever the Monthly's Pillar 3 (Dollar & Global) or Pillar 9 (Geopolitical) shows a meaningful weekly delta — these are the upstream signals that usually presage Alt Asset moves.

**Skip a Daily Cascade report** (any single intraday miss):
- *Immediate impact:* Localized. Skipping the 9:20 AM Pre-Open Flow means you enter the open without the global-handoff narrative; skipping the 4:30 PM Debrief means tomorrow's 7AM BLUF has no catalyst-reaction carry-forward.
- *Drift risk:* The two most expensive skips are the **4:30 PM Debrief** (breaks the catalyst-reaction learning loop) and the **Sunday 9:30 PM Forward Plan** (Monday opens without a week-ahead framework, week's setup proposals never get designed). Skipping intraday reports is recoverable; skipping the weekly bookends is not.
- *Recovery:* Same-day misses don't compound. Friday Weekly Reflection forgives most intraday gaps because it re-scores at the week-level. The weekly bookends are non-skippable.

### Summary: The Non-Skippable Reports

| Priority | Report | Why non-skippable |
|---|---|---|
| **Critical** | Monthly Macro Report | Substrate for everything downstream; skipping blinds the spine |
| **High** | Top & Bottom Report (weekly Sunday) | Trigger crossings happen between monthly refreshes; weekly catches them |
| **High** | Daily Cascade — Friday Weekly Reflection | Closes the week's setup-grading loop; no other report captures this |
| **High** | Daily Cascade — Sunday Weekly Forward Plan | Sets the week's strategic frame; Monday opens blind without it |
| **Medium** | Daily Cascade — 4:30 PM Debrief | Catalyst-reaction carry-forward feeds next morning's BLUF |
| **Lower** | Alternative Asset Report | Important lateral check, but the system survives a missed week |
| **Lowest** | Disruptive Themes Report | No mechanical downstream dependency; drift is the only risk |

The non-skippable ones cluster around the spine — Monthly + Top & Bottom — and the weekly bookends on the Daily. Everything else is recoverable. The **System State Dashboard** (Tier 0) is the operational check that catches skip-gaps before they compound: stale reports show up red on the dashboard the morning after they should have refreshed.

---

## Quarterly Calibration

*Added in architecture v2.0.* Every 90 days, a `quarterly_backtest.py` script runs the live `compute_scorecard.py` against the prior 8 quarters of `timeseries.db` data and produces a calibration report covering:

1. **Composite track** — does the system call known turns correctly when replayed against historical data?
2. **Pillar weight sensitivity** — would 5% shifts in any pillar weight change the call at known turning points?
3. **Overlay false-positive / false-negative rate** — across the three parallel signals (Concentration / HY Acceleration / Liquidity), how often did each fire ahead of an actual turn vs at a no-op moment?
4. **Trigger threshold appropriateness** — are the 10 triggers' thresholds tuned to current cycle conditions, or were they calibrated for a different volatility regime?

The output is a markdown report at `/opt/macro-report/top_report/calibration_YYYY-Q.md` reviewed by the operator. **Pillar weights and overlay thresholds are subject to quarterly recalibration based on this output.** Translation Table v2.3 includes this caveat in its conflict-resolution rule — the rule itself is stable, but the numerical thresholds within it evolve.

This closes the feedback loop that was previously absent: the system now learns from its own track record, not just from forward-looking analysis.

---

*Master Narrative · v1.5 — Synced with the Disruptive Themes companion paper "Foundations and Field Guide to the Five-Force Framework." Disruptive Themes section rewritten: five factors (Factor V, Monetary Architecture in Transition, promoted from the amplifier list), seven-element factor treatment, discipline stack (Steelman / both-direction Change-My-Mind / Calibration Check / External Calibration / Media Scan / Gaps Register), Dalio lens, composite on the −2…+2 band convention (Q3 2026: −1.2, OVEREXTENDED, edge of TOP SIGNAL), tail assessment backed by "The Twenty-Five," Master Refresh Prompt as report appendix. Tiers-vs-blocks terminology ruling added. Stray "Saeclum" naming removed. Note: papers are cross-referenced by name, never numeral, per the library-guide convention. Pins to translation table v2.4. Supersedes v1.4 — commit this version to docs/ in place of the v1.4 named in the Session 0 checklist. Where this document and chester-reports-architecture-v3.md disagree, architecture v3 is canonical.*
