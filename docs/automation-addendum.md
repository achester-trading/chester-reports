# Automation Addendum — Full-Stack Report Automation
## Bringing Disruptive Themes and the Daily Cascade onto the Pipeline

**Addendum to `chester-reports-architecture-v3.md` (canonical — this document defers to it on any conflict) · Draft for integration · 4 September 2026**

---

## The Principle

Every report in the stack auto-generates on schedule from the VPS. The human gate moves from **production** to **decisions** — which is exactly the split the Final Architecture Change Order already draws: `REPORT_OK` is a property a pipeline can always achieve on its own; `DECISION_BLOCKED` governs anything that would become a trade. Automation of report production is therefore not a relaxation of the governing principle (*Claude writes rules, Claude is not in the execution path*) — reports are not orders.

One design pattern covers every open question in this addendum: **every pipeline ships with a publish gate, configurable per report.**

```
auto_publish: false   → pipeline runs, drafts, notifies; operator approves before publish
auto_publish: true    → pipeline runs, publishes, notifies
```

Same code path either way, same as Paper/Shadow/Live in the execution adapter. Every report starts gated (`false`); each gets flipped to `true` individually when its drafts have earned trust. No report is ever "manual" again — the worst case is "automated with a 10-minute review."

**Current automation state, for the record:**

| Report | Today | After this addendum |
|---|---|---|
| Disruptive Themes | Manual (bimonthly chat refresh) | Auto-drafted, review-gated |
| Monthly Macro | Full pipeline | Unchanged (migrates to VPS per Sep 3 ruling) |
| Top & Bottom | Full pipeline | Unchanged |
| Alternative Asset | Partial — synthetic fetchers | Completed — live fetchers |
| Daily Cascade | Hybrid — AI Populate + analyst | Full pipeline, block-by-block, gated setups |

---

## Part 1 · Daily Cascade Automation

The Daily is the straightforward one: it is the Monthly's pattern (fetch → store → constrained LLM narrative → render → state file) run nine times a day instead of once a month.

### Prerequisite — the standing one

Run status was last recorded as *unclear what's still running*. The out-of-band "Daily Cascade v12 batch" inventory happens **first**: what fires today, from where, and what dies when cron-job.org is retired. Nothing below is built on an unconfirmed pipeline.

### Schedule (VPS systemd timers, ET)

| Time | Run | Blocks emphasized | Model |
|---|---|---|---|
| 07:00 | Morning Brief | Direction, Backdrop + cross-report sync | Sonnet |
| 09:20 | Pre-Open Flow | Market Base | Sonnet |
| 10:00 | Open Analysis | Confirmation (incl. 10AM GEX refresh) | Sonnet |
| 12:00 | Midday Read | Confirmation | Sonnet |
| 15:00 | Into the Close | Execution (MOC, pin dynamics) | Sonnet |
| 16:30 | Close Debrief | Execution + carry-forward | Sonnet |
| 21:30 | Night Watch | Backdrop | Sonnet |
| Fri 18:00 | Weekly Reflection | Register-driven grading | Opus |
| Sun 21:30 | Weekly Forward Plan | Full-stack sync | Opus |

### Per-run pipeline

1. **Fetch** — yfinance intraday (the Phase 2 symbol set), the GEX logger's latest snapshot (Session −1 output; refresh-vs-inherit labeled per the architecture), `status.json` / `system_state.json`, the events ingest layer.
2. **Store** — every input lands in the point-in-time store with `available_at` before the LLM sees it. The validator runs; a failed check produces a report stamped `DATA DEGRADED` on the affected block rather than a silent gap.
3. **Narrative** — Claude generates block narratives constrained to the data box, same discipline as the Monthly: no figures outside the payload. The 4:30 debrief's catalyst-reaction carry-forward is computed from the store (prior run's report is an input), which closes the learning loop without an analyst in it.
4. **Render + publish** — house JSX/HTML; `daily_cascade_state.json` written; alerting on failure.

### The judgment fields — where the gate sits

Three Daily fields were analyst-only: setup design, conviction grading, and the reflection scoring. Disposition:

- **Setups and conviction** → LLM-drafted, and each drafted setup enters the **register as a draft recommendation** — `status: draft`, full Decision Packet, blocked from anything downstream until approved. This is the `DECISION_BLOCKED` semantic doing its job: the report publishes (`REPORT_OK`), the trade idea waits. Approval is a phone action.
- **Weekly Reflection grading** → genuinely automatable now, and *better* automated: grading setups against outcomes is precisely what the register plus the Session 15 grading harness does. The Friday report becomes a query with narrative on top — arguably the single biggest quality gain in this addendum, because automated grading has no memory of how the week felt.

### Cost, order of magnitude

Seven Sonnet runs and two weekly Opus runs: on the order of **$1–2/day, a few tens of dollars a month**. Verify against current API pricing at build time; the tier-mix (Sonnet intraday, Opus for the two synthesis runs) is the lever if it runs hot.

---

## Part 2 · Disruptive Themes Automation

The hard one, because the report's value is partly the *thinking* — and an auto-generated steelman of your own auto-generated thesis is a weaker discipline than one you wrote. The design automates everything mechanical and puts the review gate exactly where the judgment is.

### The bimonthly pipeline (plus trigger-fired early runs)

**Stage 1 — Instrument panels (fully automatic).** Every factor's instrument panel refreshes from the store: yields and curve, gold and reserve-share series, DXY, HY OAS, concentration metrics, GPR index. Gaps already named in the gaps register (PortWatch transits, war-risk quotations, the nitrogen complex) stay flagged as unfetched until their fetchers exist — the panel renders with explicit `GAP` cells rather than pretending.

**Stage 2 — Research pass (automatic, API web search).** A scheduled Claude run with web search compiles, per factor: the current-events dispatch (the newspaper-style section, anchored to run date), the media scan, and updates to the external lenses (new WEF releases, relevant Dalio material). Output is structured notes with citations, stored — not yet prose in the report.

**Stage 3 — Draft refresh (automatic, Opus).** The Master Refresh Prompt — already the report's own appendix, which is what makes this stage possible — runs against Stage 1 + Stage 2 output plus the prior report. It rewrites the factor objects, proposes composite and scenario-probability changes **as explicit deltas with stated rationale** ("Factor III −0.1 → −0.3 because…"), and drafts the discipline sections.

**Stage 4 — Review gate (`auto_publish: false`, and I'd argue permanently).** The operator reviews a diff view: prior vs proposed, factor by factor, composite delta highlighted. The composite score and scenario probabilities are **champion/challenger** in the Change Order's sense — the auto-proposed score is the challenger; your standing score is the champion; disagreement is surfaced, and promotion is your click. The steelman and change-my-mind sections arrive drafted but the review step is where you actually argue with them. Expected operator time: **30–60 minutes per refresh**, down from the better part of a day.

**Stage 5 — Publish + state.** On approval: report renders, `disruptive_themes_state.json` emits, dashboard updates.

### The early-refresh trigger goes live

The programmatic drift conditions already in the Master Narrative (overlay ACTIVE >30 days, correlation break >30 days, Monthly composite drift >0.5, regime↔matrix mismatch) stop being dashboard advisories and become **job triggers**: any firing schedules an out-of-cycle Stage 1–3 run and notifies. The bimonthly cadence becomes a floor, not a ceiling.

### Why this report keeps its gate

Recommendation, stated plainly: flip Daily and Alt Asset to `auto_publish: true` when earned, but leave Disruptive Themes gated indefinitely. It is the report that caps sizing for the entire stack, it refreshes six times a year, and its composite is judgment-scored by design. Sixty minutes of forced argument with a drafted steelman, six times a year, is not an automation failure — it is the one place in the stack where the human is the feature.

---

## Part 3 · Alternative Asset Completion

Not redesigned here — the schema and scaffolds exist and the architecture already carries the plan. This addendum just makes it explicit that "automation for all reports" **includes retiring the synthetic fetchers** (numpy seed 7 is still generating the dashboard's numbers): the ETF-flow, COT, on-chain, and news-scan layers come live per the existing source catalog, the weekly run writes real correlation flags, and `pipeline_health` flips from `partial` to `full`. Until then the weakest-link disclosure stands.

---

## Part 4 · Sequencing and Operator Decisions

**Sequencing into the master schedule** (indicative; the schedule doc governs):

1. Daily Cascade inventory (out-of-band item, already listed) — confirm what runs today
2. Daily runs migrate to VPS timers alongside the general Sep 3 migration — **the same migration work, one report at a time**
3. Daily narrative generation + register-draft wiring (~2–3 sessions, after the store and grading harness)
4. DT Stages 1–3 pipeline (~2 sessions) + review-gate UI (~1 session)
5. Alt Asset live fetchers (existing plan, unchanged)

**The two decisions that are yours, not the spec's:**

1. **Publish-gate defaults after the trust period** — proposed: Daily `true`, Alt Asset `true`, Monthly `true` (already effectively is), Top & Bottom `true` (already is), Disruptive Themes `false` forever. Overridable per report at any time.
2. **Whether drafted Daily setups auto-enter the register** as `draft` recommendations (proposed: yes — it is what makes the Weekly Reflection's automated grading complete) or stay report-only until manually registered.

---

*Addendum draft · 4 September 2026 · Defers to architecture v3 on conflict; intended for commit to `docs/` and integration as an architecture Part. The Brookfield restriction applies to every automated recommendation path described here, enforced at register write-time as elsewhere.*
