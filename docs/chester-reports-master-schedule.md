# Chester Reports — Master Schedule

*Every session, every deferred item, total timing. Companion to the architecture
document, which holds the detail for each line here.*

**Grand total: ~196–207 hours nominal** (rebased from ~152 by the Final Change
Order — and to be re-based again after Sessions 5–6). But the first ~35 hours
build the trustworthy core that changes your life; the last
63 is optional forever.

---

# Do first — out of band, before Session −1

**1. FlashAlpha entitlement/methodology probe (0.75–1h, BEFORE Session −1).**
Promoted from the day-one verification list to its own gated step by the
Final Change Order: operating tier and mode (BASIC-SETTLED vs GROWTH-FLOW)
fixed and recorded before the logger is written; logger built to the verified
mode. Gate: raw history accumulating correctly.

**2. Monthly pipeline catch-up (~1h — the repo must be current before the VPS clones it).**
Upload the pending 6-file batch (Phase 2 yfinance, treasury_fiscal, narrative,
Treasury-updated run.py, requirements, render_md edit — use the Treasury
version of run.py); verify cron-job.org is on `0 6 1 * *` not a test
interval (interim only — retired once item 3 is proven); clean the 8 duplicate root files. Detail: architecture Part 24.

**3. VPS migration (~1.5–2h — flexible timing, phone-friendly).** Not a
first-night requirement: everything through Session 2 runs fine on the
laptop + existing setup, and nothing blocks until the Daily's VPS timers
(Part 28 A1) and the retirement of cron-job.org. Do it any evening within
the first week — it is deliberately doable entirely from the phone via
Termius (six-part walkthrough saved in the work-plan chat, 4 Sep): Termius
key → first login → lockdown (non-root user, key-only SSH, ufw;
second-tab test before closing the session) → minimal installs + Claude
Code on the box (subscription login BEFORE the .env exists — that ordering
is the billing-trap dodge) → hand the rest to Claude Code conversationally
(clone, venv, smoke test, .env chmod 600 with keys typed directly and never
pasted into chat, cron entries with git pull --ff-only + log + heartbeat,
staleness checker, one manual run) → prove with one cron-fired run, then
retire cron-job.org and drop the PAT calendar item. Ruling: architecture
Part 25. The VPS runs code, never edits it. Recovery note: Hetzner's
console has an emergency terminal that bypasses SSH — no lockdown mistake
is unrecoverable.

*Execution order is 1→6 by dependency, not by night: items 1–2 before Session −1; item 3 any evening in week one (phone-friendly); items 4–6 whenever — none blocks the build until Part 28's A1 needs the VPS timers.*

**4. Daily Cascade v12 batch (~1–1.5 hours).** FIRST: run-state inventory —
what fires today, from where, what dies when cron-job.org retires (Part 28
prerequisite). Then: tier→block rename, GEX into the 10AM open analysis,
"delta since prior report" field, refresh-vs-inherit labels. All
small, all in the existing JSX/pipeline, all higher-value done before the build
starts referencing them. Detail in architecture Part 20.

**5. Re-run Factor III in Disruptive Themes.** It is scored on a ceasefire that
collapsed seven weeks later and has carried full weight through a refresh cycle.
A stale input at full weight is worse than no input. ~1 hour, not a build task.

**6. Inventory the existing Tail Scan.** Part 16 of the architecture was written
without knowing Tail Scan exists with pandemic, nuclear, terror and cyber
domains. The 25 scenarios must **merge into it, not run beside it** — and
scenario 13 (cyberattack), which I flagged as an un-instrumented blind spot, is
probably already covered. ~30 minutes.

---

# Summary

| Phase | Sessions | Hours | What it buys |
|---|---|---|---|
| **v17** | −1 to 9 (13 blocks) | **~38** | A report you can trust, plus the news layer |
| **v17.5** | 5 items | **~7** | Unblocks and silent-failure fixes |
| **v18** | 10 to 15c (10 blocks) | **~32** | New pillars, crypto, feedback loops, scorecard |
| **v19** | 5 blocks | **~12** | Data pipes — breadth for everything after |
| **Deferred** | ~24 items | **~63** | Tail appendix (priority), depth, execution |
| **Change-order allowances** | folded into sessions | **~16–22** | Governance, contracts, learning MVP |
| **IBKR Gate 1.5 (new)** | 1 gate | **~4–6** | Expression & execution analytics |
| **Out-of-band batch** | probe · v12 · monthly catch-up · VPS · T&B plumbing | **~7** | Preconditions |

**Nominal total: ~196–207h** (was ~152; includes Part 27's ~3h and Part 28's ~13–17h automation track). Per the Final Change Order this
number is provisional by design: **rebase after Sessions 5–6** — several
allowances replace budgeted work, others hide unestimable complexity. The
number that matters more: **~35h from tonight to the trustworthy core**
(probe → out-of-band → Sessions 1–6 with their allowances → gates 1–5
passing).
| **Total (nominal)** | | **~196–207** | Rebase after Sessions 5–6 |

**Revised upward at every estimate: 130 → 142 → 152 → ~186 → ~200 nominal.** Scope grew each time:
the AI theme, Brookfield tracking, crypto in three places, Factor V, elections,
the four-bank frame, seasonality, the size ladder, options metrics, expiry
buckets, the edge layer, and the 25-scenario tail watch. **Assume this drifts
another 10% and plan accordingly** — the estimate has been low every time.

At three sessions/week: **v17 mid-October · v18 late November · v19 mid-December.**
The remaining backlog would run into mid-2027 and is not meant to be finished.

---

# v17 — the foundation (~38 hours)

| # | Session | Hrs | Gate |
|---|---|---|---|
| −1 | **GEX logger** — 15-symbol universe, raw payload, VPS cron (Part 25) | 1.5 | File appears tomorrow without you |
| 0 | **Claude Code setup** — install, CLAUDE.md, read-only first task | 1.5 | Repo map produced |
| 1 | **Clear the board** — scorecard hunt, 2 secrets, staged unit fixes, v16 freeze, D1 binding, model pinning | 2.5 | `never_run` cleared |
| 2 | **Registries + validator** — series, metrics (incl. `effective_n`, `kill_condition`, `themes`), `tracked_entities`, seasonality, commodity pass-through, surprise metrics, validation | 4.5 | Validator *fails* on v16 data |
| 3a | **Market data plumbing** — path-aware sampling, source abstraction | 2.0 | JPY flags `path_divergence` |
| 3b | **Rates and policy** — ACM term premium, Fed policy path + dispersion, funding stress and swap spreads, four-bank differentials | 3.25 | Policy path renders |
| 3c | **Fiscal and demand** — deficit ratio, 12m maturity share, TGA range, interest burden + coverage stress test, sectoral debt, Korea exports, TSMC revenue | 2.25 | R-vs-G on both bases |
| **5** | **The store** *(runs before 4 — see note)* — vintages, `policy_path`, `election_odds`, `index_members`, `narratives`, `expectations`, `tail_watch`, `tail_assessment`, restricted enforcement, GEX logger migration, local mirror sync | 5.25 | Renders with network off |
| **4** | **Provenance chain** — shared context, manifest-only generation, numeric audit (with numeral whitelist), directional check, completion enforcement, golden-file canary, three-line consensus requirement | 3.5 | 3 clean runs, empty *fact-level* canary diff |
| 6 | **Backfill** — ALFRED history, Shiller, percentiles, surprise ranking | 2.75 | Report cites percentiles |
| 7 | **Alerting and dormancy** — alerts, inverted heartbeat, degrade-don't-fail, welcome-back digest | 2.0 | Kill pipeline, get alerted |
| 8 | **Events ingest** — classifier, event chains (incl. funding-source split, Treasury Twist), election tracking, entity/theme/scenario tagging, `ai_deal_graph` | 4.75 | Yen chain renders |
| 9 | **Forward calendar and wire-in** — auto-populated calendar, Month in Events front matter, per-pillar injection | 2.0 | Global pillar cites intervention |

**Sequencing note:** Session 5 runs before Session 4. The provenance manifest is
built from stored data; built first, it gets rewritten. Numbering is kept for
continuity with the architecture document.

**Overrun risk:** Session 8. Event classification taxonomies need iteration —
budget a second pass if the first output is noisy. Session 9's forward calendar
is independent of the events classifier and can be pulled earlier if 8 runs long;
only the wire-in half depends on it.

**Standing rule:** every new fetcher lands its `series_registry.yaml` entry in the
same session. The validator rejects unregistered series from Session 2 onward.

### ▶ SHIP v17

---

# v17.5 — elevated backlog (~7 hours)

*Passed the elevation test: unblocks something scheduled, accumulates
unrecoverable data, or closes a silent-failure path.*

| Item | Hrs | Why |
|---|---|---|
| Auction results + TIC holdings | 2.0 | Confirming series for the Treasury chain — it can't falsify itself without them |
| Nowcasts — GDPNow, WEI, Cleveland | 1.0 | Momentum pillar runs on a months-old GDP print |
| Disruptive Themes spine hook + refresh trigger | 2.0 | Silent failure; Themes has gone stale once |
| Daily Cascade audit | 1.5 | Can't confirm what's running; gates register and IBKR |
| Stablecoin issuer attestations | 0.5 | History is scattered — start logging early |

---

# v18 — pillars and feedback (~32 hours)

| # | Session | Hrs |
|---|---|---|
| 10 | **Alt Asset yfinance** — all 18 assets behind the source interface | 2.0 |
| 11 | **Alt Asset remaining sources + contract** — flows, funding, MVRV, CPPI, CMBS; versioned extract | 2.5 |
| 12 | **Pillars as config + `real-assets`** — slugs, `pillars.yaml`, `consensus_source`, gold residual, two-bid decomposition, effective float, stock-bond correlation | 4.0 |
| 12.5 | **`global` extensions** — THB and Thailand set, politics sub-block | 1.0 |
| 13 | **`internals`** — breadth, dispersion, Silverblatt, Mag 7 earnings-vs-cap share, single-name GEX, four-rung size ladder, SPHB/SPLV correlation | 3.5 |
| 13.5 | **Crypto build** — CoinGlass Hobbyist fetcher, DeFiLlama, the eight metrics, two-bid decomposition | 3.5 |
| 14 | **AI financing + dealer gamma** — SEC XBRL, financing block, `sentiment` build, expiry-bucket decomposition, NVDA concentration + commitments, views ingest incl. Brookfield, crypto and official-sector sources | 5.0 |
| 15a | **Weekend Synthesis build** *(previously unbudgeted)* — swing horizon reframe, thesis tracking and state machine, running forecast tables, crypto commentator scan | 3.0 |
| 15b | **Scorecard and predicates** — Section 0, predicate emission with basis, effective n and `vs_consensus`, daily grading harness | 3.25 |
| 15c | **Reflection and guards** — cross-report reflection, coverage-gap scan, correlation guard, tail assessment generation, divergence-split grading, confidence/regime/timing/discretionary logging | 3.75 |

### ▶ SHIP v18

---

# v19 — data pipes (~12 hours)

**Why this comes before the rest of the backlog.** Not because the data compounds
— COT, FINRA margin, AAII/NAAIM, ICI, FRA-OIS, 13F and EIA all publish free
history, so building them later loses nothing. (The pipes that *do* compound —
GEX, stablecoin attestations, prediction-market odds — are already in v17 and
v17.5.)

The real reason: **fetchers are cheap, mechanical and low-risk.** One either works
or it does not. No design decisions, nothing that can be subtly wrong for months
the way a scoring rule can. Ideal for a session with an hour and low energy, and
it broadens what every later analysis can draw on.

**Condition, or v19 is a data dump:** every fetcher names its pillar and the
question it answers *before* it is built. Twelve series with no rendering home
just makes the report longer.

| # | Block | Hrs | Feeds |
|---|---|---|---|
| 16 | **Positioning** — CFTC COT across equity index/rates/dollar, FINRA margin debt | 2.5 | `sentiment` |
| 17 | **Survey and flows** — AAII, NAAIM, Investors Intelligence, ICI weekly | 2.5 | `sentiment` |
| 18 | **Funding remainder** — FRA-OIS, CP spreads, nowcast extras | 2.0 | `liquidity` |
| 19 | **Holdings and uncertainty** — 13F via EDGAR, GPR / EPU / TPU indices | 2.5 | `internals`, `global` |
| 20 | **Commodity and structure** — EIA weekly petroleum and gas, Baker Hughes rigs, off-exchange volume share | 2.5 | `real-assets`, `internals` |

### ▶ SHIP v19

---

# AUTHORITATIVE SCHEDULE DELTA (Final Change Order, 3 Sep 2026)

*Fold into existing sessions — no new phases. Hours are incremental planning
allowances, not promises. **Rebase the whole schedule after Sessions 5–6**:
several allowances replace budgeted work, others expose unestimable
complexity; do NOT mechanically add to the ~152h total.*

| Session | Addition | Allowance | Gate |
|---|---|---|---|
| Before −1 | Entitlement/methodology probe | 0.75–1h | Tier/mode fixed |
| −1 | Logger aligned to verified mode | within | History correct |
| 2 | Signal rights, mechanism groups, source registry, time fields | 1.5–2h | Schema validates |
| 3b | Rates data-semantics contract | 1h | Clocks/auction rules enforced |
| 5 | Decision Packet, register, label types, Security Master | 2–3h | Exact replay |
| 6 | Point-in-time forensic harness + research-validity framework | 2–3h | Leakage audit passes |
| 8 | Event timestamp/source-hierarchy/causality contract | 1–1.5h | Event-chain gates |
| 13.5 | Crypto provider semantics/coverage audit | 1–1.5h | Leverage state reproducible |
| 14 | XBRL semantics + Desk Views Engine | 2–3h | Traceable, gradeable calls |
| 15a | Lessons-before-decision + post-expiry dealer state | 1–1.5h | Swing packet reproducible |
| 9 / 15a / 15c (+Monthly renderer) | Prediction Market Intelligence Engine (Part 27, amendment #1) | ~3h total | Confirmed-shock rule + resolution-criteria rule enforced |
| 15b–c | Error decomposition, abstention, counterfactuals, champion/challenger | 2–3h | Learning MVP live |
| 16 | CFTC TFF semantics/risk normalization | 0.75–1h | Tue/Fri rules enforced |
| 19 | Institutional positioning + survivorship-resistant panels | 1.5–2.5h | Populations distinct |
| IBKR Gate 1 | Portfolio Truth + reconciliation | existing+ | Book is canonical |
| **IBKR Gate 1.5 (NEW)** | Risk, What-If, expression & execution analytics | **4–6h** | Trade Card sees real economics |

**Automation track (Part 28, amendment #2)** — sequenced after its
prerequisites, not a new phase:

| Item | Depends on | Allowance |
|---|---|---|
| A1 · Daily runs → VPS timers | Part 25 migration | within migration |
| A2 · Daily narrative + register-draft wiring | S5 store, 15b harness | ~6–8h |
| A3 · DT Stages 1–3 + review-gate UI | S5, S9 events, S15c | ~7–9h |
| A4 · Alt Asset live fetchers | existing S11 scope | unchanged |

# Deferred backlog (~63 hours)

*Carry-over from Daily Cascade production chat (3 Sep): analytical detail for
Daily items lives in the Daily Cascade WP Ch. 24 (canonical backlog); lines
here are scheduling pointers only.*

- Retail-segment options positioning, free proxies (DIX, small-lot P/C,
  Nasdaq RTAT) as a §06 sub-row — ~2h. Detail: Ch. 24, Tier 2 item 14.
- Cboe Open-Close customer-bucket feed — paid; **gated on the free-proxy item
  proving signal value**. ~3h if triggered. Detail: Ch. 24, Tier 3 item 16.
- ASTS filing-stage playbook into §22 scenario library. Detail: Ch. 24,
  Tier 3 item 22.

*Carry-over from T&B session (3 Sep):*

- T&B liquidity-overlay plumbing + overlays into status.json — ~2h out-of-band
  (interim; the store becomes the single source for these series at Session 5,
  T&B then reads from it — never two copies long-term).
- Continuous backtest harness (backtest_scorecard.py vs VPS timeseries.db) —
  deferred; the real false-positive-rate measurement behind the overlay
  thresholds.

*Carry-over from Monthly build chat (3 Sep):*

- Mitigation B — two-repo split, private outputs repo (~30–45 min).
- Phase 3 sentiment scrapers (BofA B&B, NAAIM, AAII, OpenInsider);
  news API layer (Pillar 10); Phase 4 13F via EDGAR — fold into S14/S27 scope.
- QRA parsing → marginal issuance mix (follow-on to bill share).
- Conditional Prediction-Market Atlas + confidence-modification right as
  champion/challenger — deferred until the PM resolution archive accumulates
  (Part 27).

*Build-week additions (5 Sep, approved in-session):*

- Trading-calendar guard in session_date() — holiday/weekend skip with logged
  non_session exit (BEFORE Mon 16:10: Labor Day would otherwise capture stale
  chains). ~30 min.
- Greeks extension: exposure_compute.py — GEX/DEX/VEX/CHEX per strike ×
  4 expiry buckets, dealers-hand-v1 signs, per-bucket DEX expiration-release
  line, mechanism_group=dealer_chain_derived (one cluster, never four votes,
  per 26.9). Backfill from 2026-09-04 chains. ~1 session.
- Intraday cadence (after Tuesday's first autonomous settled capture proves
  clean): 09:45 full chain re-fetch (captures the day's 0DTE structure),
  12:30 spot re-evaluation (no fetch; distance-to-flip, active walls, 0DTE
  decay), 16:10 settled capture unchanged and sole writer of history/pin
  rows. Intraday output to a separate intraday/ path labeled
  profile_reval vs chain_refresh — never mingled with settled history.
  Precursor to Part 28 A1's nine-run schedule. ~1–2h incl. two VPS timers.
- **Calendar: renew the cron-job.org PAT April 2027** — only if the Actions
  fallback is still alive by then; drops entirely once the VPS migration
  (out-of-band 1b) is proven.


Sequenced by value, not by order added. **Not meant to be completed** — it is a
menu, and the elevation test governs what leaves it.

## Priority deferred — do these first

| Item | Hrs | Why it ranks |
|---|---|---|
| **Chokepoint / supply-corridor domain in Tail Scan** | 2.5 | New domain with no current coverage: Hormuz, Suez/Bab el-Mandeb, Panama draft, Taiwan Strait — each with transit counts, war-risk premium, affected commodity complex. Generic structure so it persists after any single crisis. |
| **Tail scenario appendix — 25 scenarios, Disruptive Themes** | 6–8 (≈2–3 of your attention) | **The standing tail table is 25 labels without it.** Static document, written once, reviewed annually. Batches of five by tier, starting with Tier E. Do it after v17 has run once — you will write a better version having seen which scenarios you keep wanting context on. Structure in architecture Part 16c. |

## Analysis that changes what the report says (~16 hrs)

| Item | Hrs |
|---|---|
| Re-Rating Exhaustion into Valuation | 2.5 |
| Consolidated rate-reset velocity (net SOMA, reserves at IORB) | 3.0 |
| Total shareholder yield vs. real 10Y | 2.0 |
| Foreign share of debt held by public (TIC) | 1.5 |
| Threshold fragility audit across ten triggers | 2.0 |
| Daily Cascade conditioners — ON range percentile, open location | 1.5 |
| AI theme depth — N-PORT parsing, CBRE/JLL, interconnect queues | 3.5 |

## Reports and wiring (~19 hrs)

| Item | Hrs |
|---|---|
| Top & Bottom — scorecard, matrix-to-verdict mapping, Appendix D | 5.0 |
| Banking pillar — SLOOS, SCOOS, H.8, FDIC, BDC price-to-NAV | 4.5 |
| Full Horizon 2 gamma wiring into Daily Cascade | 4.5 |
| Desk views ingest — full source set | 2.5 |
| Dashboard live wiring | 4.0 |
| Daily Cascade store migration | 1.5 |
| Brookfield bond spreads and preferred yields | 1.0 |

## Execution track (~21 hrs)

| Item | Hrs |
|---|---|
| Trade register — schema, conflict detection, sizing, swing tracking | 5.0 |
| IBKR source implementation | 2.5 |
| **Gate 1** — read-only sync, positions and marks into store | 5.0 |
| **Gate 2** — paper trading, full OCO brackets, 3-month minimum dwell | 7.0 |
| Gates 3–4 | *A decision, not a build* |

---

# Calendar

Assuming a Monday start.

| Pace | v17 | +v17.5 | +v18 | +v19 | Deferred |
|---|---|---|---|---|---|
| 2/wk (~5 hrs) | 7 wks | +1.5 | +4 | +2.5 | +11 |
| **3/wk (~7.5 hrs)** | **4.5 wks** | **+1** | **+3** | **+1.5** | **+7.5** |
| Intensive (1/day) | 2.5 wks | +3 days | +2 wks | +1 wk | +5 wks |

At three per week: **v17 early October · v17.5 mid-October · v18 mid-November ·
v19 early December.** The remaining backlog would run to roughly mid-2027 if
pursued in full, which it should not be.

---

# What to do if the plan compresses

Real life will interrupt this. Priority order if you get less time than planned:

1. **Session −1** — one hour, and the only unrecoverable asset in the system
2. **Sessions 1, 2, 3a** — clears `never_run`, stops the unit bugs, fixes the
   sampling that hid the yen. ~8 hours total and the report is honest
3. **Sessions 5, 6** — the store and history; everything downstream needs them
4. **Session 4** — stops the narrative fabricating
5. **Session 7** — makes the next gap two days instead of two months

Those five stopping points each leave the system in a coherent state. Everything
after Session 7 is genuine improvement rather than repair.

---

# Cost and subscription management

**Two separate budgets. Do not conflate them.**

| Budget | Covers | Rough cost |
|---|---|---|
| **Claude subscription** | Claude Code during build sessions | Pro ~$17–20/mo; Max 5x ~$100/mo |
| **Anthropic API** | The pipeline's narrative step, billed per token | Low single digits/mo, rising to low double digits with daily event classification |
| **FlashAlpha Basic** | Options and dealer positioning | Existing |

**Start on Pro.** Sessions here are 2–3 hours, three times a week — not all-day
agentic coding. Pro will feel tight in a long session but is workable. Both Pro
and Max support pay-per-token overflow, so a spike does not force an upgrade, and
moving to Max later is a click. *(Third-party figures; confirm at
anthropic.com/pricing.)*

## Checkpoints, by session

**Session 0 — before your first long session**
- ☐ **Commit the documents to GitHub first.** Create `docs/` and
  `docs/whitepapers/` in the chester-reports repo and commit: the three
  planning documents (architecture v3 — CANONICAL, master schedule, system
  narrative), the white-paper library guide, the tail-scenarios reference,
  Translation Table v2.3 and Master Narrative v1.4 (rescue from the cadence
  chat before deleting it), and every white paper as `.md` (canonical) with
  `.html` as the reading edition. Then `wc -w` the three unmeasured papers and
  fix the guide. This comes first because CLAUDE.md will point at `docs/`, and
  a plan that isn't in the repo doesn't exist for Claude Code.
- ☐ **Check whether `ANTHROPIC_API_KEY` is set in your shell.** If it is, Claude
  Code authenticates via API key and bills API rates *instead of* your
  subscription. You will have that key set for the pipeline, so this will
  probably catch you. Verify which mode Claude Code is running in before you
  start.
- ☐ Write `CLAUDE.md`. **The single biggest usage lever in this plan** — without
  it, every session re-discovers your repo structure, which is pure burned
  context.
- ☐ Locate Settings → Usage. It is the only place that shows real remaining
  limits.

**Sessions 3a–3c, 10–11, and all of v19 — model selection**
- ☐ **Run these on Sonnet, not Opus.** Fetchers are mechanical; they do not need
  the expensive model, and you choose per task. This is most of your session
  count.

**Sessions 4, 8, 15 — the ones that warrant Opus**
- ☐ Provenance chain, event classification, and the feedback loop involve real
  design judgment. Spend the budget here.

**Session 8 — API cost inflection**
- ☐ Event classification runs daily once live, not monthly. Watch the first
  week's API spend and set a monthly cap in the console before it runs
  unattended.

**End of week 2 — the plan decision**
- ☐ If you have hit session limits mid-work more than twice, upgrade to Max 5x.
  Otherwise stay on Pro. Do not pre-buy capacity for a build you will finish in
  ten weeks.

**Monthly, ongoing**
- ☐ Review API spend against the report's value. If narrative generation ever
  exceeds ~$30/mo, the prompts are too long — that is a design signal, not a
  billing problem.

## Habits that stretch the budget

- Let Claude Code read files; do not paste them into chat
- Branch per session and keep sessions scoped — long meandering sessions burn
  context on re-orientation
- Plan mode before large changes: cheaper to review a plan than to undo an
  implementation
- Pause non-critical work when the terminal shows a limit warning rather than
  pushing through

---

# Two structural cautions

**The registry is the single point of coupling.** Twelve later sessions depend on
the schema defined in Session 2. Give it an explicit `schema_version` field and a
migration path from the start, and accept that v1 will be wrong in ways you
cannot predict now.

**Report length is the biggest unaddressed risk to clarity.** The monthly now
carries: Section 0 scorecard, Month in Events, eleven pillars, the AI theme view,
the Brookfield entity block, a seasonality conditioner, and appendices. **Make the
surprise ranking a hard word budget, not guidance** — lead with the five most
anomalous, quiet pillars get two lines and say so. Otherwise v18 ships at 10,000
words and stops being read, which would undo everything else in this plan.

---

# The standing rule

**The elevation test:** an item leaves the deferred backlog only if it unblocks
something scheduled, accumulates data that cannot be bought later, or closes a
silent-failure path. Coverage alone is never a reason.

**And the closing caution from Session 15:** there are roughly fifteen feedback
loops in this system. Do not add a sixteenth until one of them has changed a
decision. The point of all of it is a different trade, or a trade not taken.

**A note on value density.** The early additions to this plan — the validator,
vintages, the events layer, the provenance chain — were load-bearing; the system
does not work without them. The later ones — elections, seasonality, the size
ladder — are all defensible and none of them change what the system fundamentally
does. That decline is the signal to stop designing and start building. **The plan
is complete. Further additions should wait until something in it has run.**
