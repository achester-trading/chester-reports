# Chester Reports — System Narrative

*What each report is for, how they fit together, and how analysis becomes a
tracked trade. Companion to the architecture review (v3); this is the "what and
why," that document is the "how and when."*

---

# Part 1 — Gap check against the prior architecture critique

Cross-referencing the earlier critique against the v3 architecture. Six of ten
items are captured, two are partially lost, and my own fresh pass found four more.

## Captured, and in most cases strengthened

| Prior item | Where it now lives |
|---|---|
| No single state-of-system view | Alerting (Session 7) pulled ahead of the dashboard — an alert finds you, a dashboard requires you to look |
| Crypto two-source reconciliation | Store fold-in (Session 5); one source of truth |
| Refresh staleness untracked | Staleness checks in the validator (Session 2) plus alerting |
| Alt Asset is the weakest link | Sessions 10–11, gated on a zero-synthetic-series disclosure |
| Backtest feedback loop absent | Session 15, restructured into three tiers with an anti-overfitting discipline |
| Appendix C manual | Becomes a query against the register (Part 7 of the architecture doc) |

## Partially lost — restored below

**The Monthly Matrix → Top & Bottom verdict mapping.** The v3 deferred list
compressed this to "Top & Bottom, 1–3 sessions" and dropped the mapping table.
It matters: if Monthly weights a pullback scenario at 45% and Top & Bottom reads
NEUTRAL, nothing currently says whether that is a conflict or a consistency.
Restored in Part 5 below.

**The Disruptive Themes programmatic refresh trigger.** "Refresh when something
doesn't fit" requires noticing, and Themes has already gone stale once. The
specific rule — any Top & Bottom overlay ACTIVE more than 30 days without
composite movement raises a refresh flag — belongs in the deferred spine-hook
session, not in your memory.

## Not captured anywhere — four new gaps

**1. Reports are mechanically disconnected from the spine, and v3 does not fully
fix it.** v3 gives you `pillar_scores` inside the Monthly report. It does not
give you a cross-report state table. Disruptive Themes and Alternative Asset
still reach the Daily Cascade only through analyst judgment, which means the
Daily can run technically correctly while missing context from two of five
reports.

**Fix:** add a `report_state` table to the store — one row per report per run:

```sql
report_state (
  report, run_id, as_of, refresh_cycle_days,
  headline_state,        -- regime / composite / verdict / flags
  detail_json,           -- overlays, factor states, flag list
  staleness_days,        -- computed
  confidence             -- derived from staleness, see Part 5
)
```

Every report writes one row. The Daily's coordination block reads all five, not
two. This is the actual spine, and it is a small addition to Session 5.

**2. No staleness precedence rule.** v3 tags stale data but never says what to do
when a fresh report and a stale one disagree. Rule in Part 5.

**3. The register has no "declined" state.** Recommendations you choose not to
take are data — arguably the most valuable data, because they tell you whether
your discretionary filter is adding or destroying value. Add `declined` as a
status with a required reason, and grade declined recommendations alongside taken
ones.

**4. Nothing maps regime to position size.** The analytical stack produces
direction and conviction; `execution-framework-v2` holds the expectancy ledger
and bracket rules. Between them there is no sizing function. A −1.0 composite and
a +0.5 composite should not produce the same position size, and today nothing
says how they differ. This belongs in the register layer as a `size_multiplier`
derived from composite score and overlay count.

---

# Part 2 — What the system is

Five analytical reports, one shared data spine, one trade register, and an
execution layer. The reports answer different questions at different time
horizons; the register is where their output becomes accountable; execution is
where it becomes money.

The organizing idea is **cascade, not consensus.** The reports are not five
opinions to be averaged. They are five resolutions of the same picture, from
structural to intraday, and each one constrains the next.

```
STRUCTURAL   Disruptive Themes    ── what world are we in?
    ↓
CYCLICAL     Monthly Macro        ── what is the macro state?
    ↓
TIMING       Top & Bottom         ── are we near an extreme?
    ↓
EXPRESSION   Alternative Asset    ── where is the best expression?
    ↓
EXECUTION    Daily Cascade        ── what do I do today?
    ↓
             TRADE REGISTER       ── what did we recommend, and did it work?
    ↓
             EXECUTION (IBKR)     ── staged, then paper, then live
```

---

# Part 3 — The five reports

## 1. Disruptive Themes — the structural frame

**Horizon:** multi-year. **Cadence:** quarterly, plus event-triggered.
**Question:** what regime are we in, and is it changing?

Four factors: AI maturation, valuation, geopolitical confrontation, and the
dollar/debt/liquidity complex. Its output is a regime characterization, not a
signal — it tells you which playbook applies, not when to act.

**How it is used:** it sets the prior. When Themes says the regime is fragile,
tactical constructive signals get smaller size and tighter stops, not ignored.
Themes escalates; it does not override.

**Current weakness:** refreshes are informal and it has gone stale. The
programmatic trigger above fixes that.

**Factor V — Monetary Architecture in Transition.** Crypto, stablecoins, CBDCs,
tokenization and the debasement trade as expressions of one structural force. Not
named "crypto": the other factors are forces, and an asset class alongside them
would bias the analysis toward price. Carries the adoption ledger — security,
quantum, emerging use cases, regulation — as tailwinds and headwinds with
falsification conditions.

**The tail scenario appendix.** Twenty-five scenarios, one page each: mechanism,
why now, transmission through the pillars, effect on positioning, historical
analogue, and what would retire it. Static, reviewed annually. **The monthly
standing table says where each scenario stands; this says what each scenario is.**
Without it the table is twenty-five labels.

**Writes to spine:** `disruptive_themes_regime`, persists 60 days.

## 2. Monthly Macro — the state of the world

**Horizon:** 1–12 months. **Cadence:** monthly.
**Question:** what is the macro state, across every transmission channel?

Eleven pillars — labor, momentum, liquidity, inflation, sentiment, credit,
internals, global, sovereign, real assets, banking — plus an events layer, a
forward calendar, and a scenario matrix.

**How it is used:** this is the reference document. It is not a trading signal
and should not be read as one. Its job is to be *right about the state* and
explicit about what would change the read. Everything downstream inherits its
framing.

**Writes to spine:** `monthly_composite`, pillar scores, scenario weights.

## 3. Top & Bottom — the turn detector

**Horizon:** weeks to months. **Cadence:** monthly, weekly during stress.
**Question:** are we near a tradeable extreme?

Ten triggers, three overlays (Concentration & Complacency, HY Spread
Acceleration, Liquidity & Funding Stress), Valuation weighted at 17%, plus the
Reinhart & Rogoff gap-patch. Calibrated against 13 historical episodes; better at
bottoms than tops, with the 2007 top judged structurally uncatchable.

**How it is used:** this is the timing authority. Monthly says what is true; Top
& Bottom says whether it is priced. When they conflict, that is information, not
error — see Part 5.

**Writes to spine:** `verdict`, `active_overlays`, `trigger_count`.

## 4. Alternative Asset — the expression layer

**Horizon:** weeks. **Cadence:** weekly.
**Question:** given the macro read, where is the best expression, and what
correlations are breaking?

Eighteen assets across metals, crypto, commodities, and real estate. Its unique
contribution is the correlation matrix — a gold that correlates with equities
means something entirely different from a gold that correlates with TIPS.

**How it is used:** once the macro read and the timing are set, this determines
*which instrument*. It also produces the earliest warning of regime change,
because correlation structure breaks before price does.

**Writes to spine:** `alt_asset_flags` — correlation breaks, oversold extremes.

## 5. Daily Cascade — execution

**Horizon:** intraday to one week. **Cadence:** daily.
**Question:** given everything above, what do I do today?

Eight reports, dealer positioning, session structure, a 7AM coordination block.

**How it is used:** this is the only report that produces actionable orders. Its
7AM block must surface all five reports' state — currently it reads two.

**Writes to spine:** `daily_macro_risk`, plus recommendations to the register.

### 5a. The tail watch — across all reports

Twenty-five scenarios with named first-mover series and thresholds, checked
mechanically. **Cadence follows how fast the scenario moves, not how important it
is.** Five daily in the Cascade, eight weekly in Weekend Synthesis, nine monthly
in Monthly Macro, two quarterly in Themes. One — a cyberattack on settlement
infrastructure — sits on the list with no tripwire, documented as a blind spot
because price-based indicators fail by construction there.

Dormant scenarios do not print. Only elevated or triggered rows appear, which
most weeks means an empty section.

Monthly Macro additionally carries the **standing assessment**: all 25 with
probability band, outlook, and change from prior — one compact table, narrative
only for what moved.

### 5b. Weekend Synthesis — the swing horizon

**Horizon:** 1–3 weeks. **Cadence:** Friday 1800.
**Question:** what is the thesis for the next two to three weeks?

This is the Friday Weekly Reflection, reframed. It already carries weekly thesis
review, Monthly Macro delta, GEX/vol weekly reset and the correlation matrix —
the retrospective half. The addition is the forward half: a swing thesis with
levels, invalidation, and sizing.

**Why it matters:** nothing else owned 1–3 weeks. Daily runs to next session,
Top & Bottom fires on structural extremes in months, Alternative Asset answers
*which instrument* rather than *which direction*. This is where dealer
positioning and macro regime overlap, and plausibly where the edge is.

**Clock:** the options expiry cycle, not the calendar. Monthly and quarterly
OpEx, and charm/vanna decay into expiry, reset gamma positioning on roughly a
three-week rhythm.

**Writes to spine:** `swing_thesis`, plus `horizon: swing` recommendations.

---

# Part 4 — The trade register

Every report produces trade expressions. Until now none of them were tracked in
one place, graded, or checked against each other.

**The register is the accountability layer.** It sits between analysis and
execution and answers four questions nothing else can:

1. **Are our ideas good?** Graded thesis outcome, separate from P&L.
2. **Do our reports contradict each other?** Cross-report conflict detection,
   scoped within a horizon.
3. **Is our discretion adding value?** Declined recommendations, graded.
4. **Do we have an edge, or just a view?** Every predicate and recommendation is
   tagged `agree` or `diverge` against consensus at creation, and graded
   separately. **Consensus-agreeing hits earn nothing — they are already in the
   price.** Divergent hits are the actual edge measure, and this is the single
   most informative number the system produces about itself.

**Lifecycle:** `proposed → active | declined | expired` → `closed | invalidated`.
Declined requires a reason. Expired means the entry never triggered, which is
different from being wrong.

**What it feeds:** the expectancy ledger in `execution-framework-v2` — one
ledger, not two — plus Monthly Appendix C, which stops being manual and becomes a
query filtered to the current regime read.

**Sizing.** The register carries a `size_multiplier` derived from composite score
and active overlay count. This is the missing link between "the system is
bearish" and "how much do I put on."

---

# Part 5 — How they fit: conflict and precedence

## Domain precedence

When reports disagree, authority is by domain, not by recency:

| Domain | Authority | Rationale |
|---|---|---|
| Structural regime | Disruptive Themes | Only report on that horizon |
| Macro framing | Monthly Macro | Full transmission-channel coverage |
| Timing / extremes | Top & Bottom | Purpose-built and backtested |
| Instrument selection | Alternative Asset | Correlation and relative value |
| Structure (strikes, expiry) | Top & Bottom Appendix D | Engineered portfolios; Monthly Appendix C is illustrative thesis expression |
| Swing thesis, 1–3 weeks | Weekend Synthesis | Only report on that horizon; expiry-cycle aware |
| Entry, stops, sizing | Daily Cascade + `execution-framework-v2` | Only layer with live market structure |

## Staleness precedence

Confidence decays with age. A report past **1.5× its refresh cycle** is advisory
only and cannot win a conflict in its own domain. Past **2×**, it is excluded
from the coordination block entirely and raises an alert.

This is why `report_state` carries `refresh_cycle_days` and computes
`staleness_days` — the rule needs to be mechanical, not remembered.

## Matrix-to-verdict mapping

The Monthly scenario matrix and the Top & Bottom verdict describe the same world
at different resolutions. The mapping table defines, for each Monthly scenario,
the expected Top & Bottom verdict range and the action when they diverge.

The general rule: **a mismatch is escalation, not error.** Monthly weighting a
pullback heavily while Top & Bottom reads NEUTRAL means the macro case is not yet
priced — which is either early or wrong, and the overlays usually tell you which.
Sustained divergence beyond one cycle triggers a Disruptive Themes refresh, on
the theory that a persistent cyclical/timing mismatch is often a structural
signal in disguise.

---

# Part 6 — Execution

Four gates, covered in detail in the architecture document. The governing
principle: **Claude writes rules, Claude is not in the execution path.** Signals
become orders through deterministic code, never through generated text.

Gate 1 is read-only broker sync, which is what makes the register's expectancy
ledger measured rather than theoretical. Gate 2 is paper, minimum three months,
and the test is whether realized expectancy matches what the register predicted.
Gates 3 and 4 are separated by months, not sessions.

---

# Part 7 — What to check when something feels wrong

| Symptom | First place to look |
|---|---|
| Reports disagree and you can't tell who's right | `report_state` staleness — one of them is probably past 1.5× |
| A number looks implausible | Validator log; check the series registry entry |
| The narrative asserts causation you don't recognize | Events table — is there a matching record, or did it fabricate? |
| A pillar hasn't changed in months | Registry audit — is the series actually updating, or is it stale-and-silent? |
| Recommendations keep losing | Grade thesis and P&L separately before concluding anything |
| The system feels stale generally | Disruptive Themes refresh trigger; check overlay duration |

---

# Part 8 — The single largest risk

It is not technical. This system has one operator, and it has already gone dark
once — roughly two months, during which Themes went stale and the monthly
pipeline sat at `never_run` with nothing to say so.

Every architectural choice above that looks like overhead — alerting in v17
rather than the backlog, auto-populated calendars, mechanical staleness rules,
declared precedence instead of remembered convention — exists to reduce what the
system needs from you to keep running. Build for the version of yourself who is
busy for six weeks.

## Dormancy: frozen vs. rotting

Most of the stack freezes safely. FRED keys do not expire, the repo sits there,
D1 keeps its rows, and because the trigger is cron-job.org rather than a GitHub
scheduled workflow, it sidesteps the rule that disables cron after 60 days of
repo inactivity.

What rots: cron-job.org disables jobs after repeated failures; yfinance breaks
silently and returns nulls rather than errors; a pinned model can be deprecated;
and alerts only help if someone reads them — a failure email on day 3 of a
six-week absence is not a safety mechanism.

The architectural answers, all in Session 7: an **inverted heartbeat**, where a
successful run pings an external monitor and the *absence* of pings raises the
alarm; **degrade-don't-fail**, so a run missing a fifth of its series publishes
with visible gaps instead of erroring into silence; and a **welcome-back digest**
summarizing what ran, what broke, what resolved, and what went stale.

**One thing is genuinely unrecoverable.** FlashAlpha historical replay is
Alpha-tier, so every day the GEX snapshot does not run is a hole in a
distribution that cannot be bought back at Basic. Everything else can be caught
up on return. That is why the logger is Session −1 — an hour of work, before the
store, before Claude Code, before anything.
