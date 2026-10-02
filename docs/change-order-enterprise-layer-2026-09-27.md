# Change Order — Enterprise Layer and Intraday Tactics

**Functions, not agents; a baseline before a verdict; tactics, not a fifth book**

| | |
|---|---|
| Status | **Rulings R-1, R-2, R-3 signed in chat 2026-09-27 18:21 ET** ("yes to all three"). **Rulings R-4…R-8 signed in chat 2026-10-02 14:52 ET** ("sign all"), item 0 of the Doctrine monthly. The work order in §8 is filed for Ari's word at Audit #4 (14–15 Oct); nothing in it starts before that word except EL-0 (filing, done). |
| Date | 2026-09-27 (evening) |
| Proposed by | Ari Chester, as two specifications: *Enterprise Trading Intelligence, Learning, Risk and Governance Architecture* and *Day Trading Layer (DTH-1)*, both filed verbatim under `docs/briefs/` (§9) |
| Contents | A mapping of both specifications onto the repository as it stands on 27 Sep 2026 (§1); eight rulings (§2); the additions specified literally enough for a session to build them (§3–§7); a work order with placements and hours (§8); filing and precedence (§9) |
| Encoding | **Post-Freeze Amendment #5 — Enterprise Layer and Intraday Tactics** (provisional number, confirmed at filing; the 19 Sep "#5" label was retired unused). Encodes as the next free architecture Part. |
| Precedence | Below Part 26 (Final Architecture Change Order), Part 28 (automation addendum), Part 30 (Track D and 30.2–30.4), the current change-orders edition and Amendment #4. Binds to the one-regime rule (`docs/market-state.md`) and to 30.4 (reports never fetch). **The two specifications are requirements documents cited by this order; they are not controlling and do not compete with Part 26.** |
| Supersedes | Nothing. Adds to Phase 5, 6b, Gate 1.5, the Doctrine monthly and Audit #4; leaves the execution order of Audit #3 §N unchanged. |
| Filing state | No Enterprise Layer or DTH-1 document exists in `docs/` on `main` at 61e9b4b (27 Sep 17:51 ET); `DTH-1` appears nowhere in the repository. This order is the first filing. |
| Binding on | Claude Code sessions executing §8 after Ari's word |

---

## §0 Summary

Both specifications are one programme, and most of it is already built here under other names. Part 26's decision governance, the three-clock store, the immutable packets and the register, the shadow grader and the Brier ledger, the claims registry and the paragraph audits, the narrative and signal-triage registers, the prediction-market specification, the Doctrine paper, the audit cadence and the deploy rules are §VII–§XIV, §XX–§XXI and §XXVI–§XXVII of the Enterprise specification, in production. The order therefore adopts the specifications as **a mapping plus six additions**, and it refuses the one design error both specifications repeat: turning functions into standing LLM agents.

The three rulings signed in chat:

- **R-1** The Enterprise Layer is a mapping plus additions. No standing agents. Two briefs run by sessions on a cadence (Doctrine, Red Team), three deterministic services (Evaluation, the cross-book risk roll-up, architecture metrics), one register (Research), and the existing pipeline plus the operator as orchestration.
- **R-2** DTH-1 is not a fifth book. It is an intraday expression-and-timing layer for Books B and C, plus at most two paper engines with stated mechanisms, N targets and kill criteria written before the first trade.
- **R-3** A benchmark book enters Phase 5: three static reference ledgers (cash, SPY, 60/40), marked daily, reported beside every book — the denominator for every later claim of value.

The build order of Audit #3 §N does not change: Phase 5 → cloud migration → 6b → 6d → 6e → 6f → Quarterly Structural + 6i → 6m → Audit #4. This order inserts roughly 20–30 session-hours into work already scheduled (Tranche A) and places the rest behind evidence gates (Tranche B).

---

## §1 Mapping — where each proposed function lives today

| Specification | In the repository now | Gap |
|---|---|---|
| Evidence object, point-in-time integrity (Ent. §VII, §XIII; DTH §V) | observations with three clocks (observed / available_at / ingested_at), as-of joins, vintage rule; claims registry cited by id | none |
| Hypothesis and forecast objects (Ent. §VII, §XI) | narrative register with evidence rules; probability ledger; midterm hypotheses with priors shrunk to unconditional | falsifiers are per story, not a required field on every material hypothesis (EL-1 adds them to packets; the register's stories keep their evidence rules) |
| Decision and outcome objects (Ent. §VII, §XIV; DTH §XVII) | immutable Decision Packets; register v17; shadow grader at horizon; cuts | packets lack `setup_id`, `engine_id`, `horizon_alignment`, `review_changed`, `falsifiers`, `counter_thesis` (EL-1) |
| Learning object (Ent. §VII) | prose in the Doctrine, the change orders and the audits | **missing** — a lessons register; gated on having lessons (§6, EL-10) |
| Independent Evaluation and attribution (Ent. §IV, §XXIII; DTH §XVI, §XX) | the grader, deterministic; Brier refuses 0/1; expectancy ledger (execution-framework-v2) | attribution taxonomy and counterfactual labels (EL-8, at Gate 1.5) |
| Enterprise Risk (Ent. §V, §VI, §XVI; DTH §XI, §XIV) | Books A–D; Phase 5's order gate at entry and heat/factor view (next in the queue) | the roll-up must be explicitly cross-book (EL-2); the alignment tag (EL-1); the benchmark book (EL-3) |
| Research and signal promotion (Ent. §III, §XX; DTH §XIX, §XXI) | signal-triage register SR-1…SR-27, intake template, narrow-flag / modifier / base-rate rights, backtest before any panel, offline calibration studies with dated ledgers | a scan cadence, as a session brief not an agent (EL-11, gated); anomalies become an intake type, not a library (§7) |
| Doctrine and structural change (Ent. §II, §XVIII, §XIX) | Doctrine paper; Doctrine monthly (first 3–4 Oct); Annual Structural Review (Audit 2); dated appendices policed by the library gate; Amendments #1–#4 | the five-tier change ladder is not written down (EL-4); attention budget (EL-4) |
| Red Team (Ent. §VI, §IX; DTH §XIII) | Bull Rebuttal gate; contradiction table; audits that withhold | no pre-decision adversarial step on material packets (EL-1 for v0; EL-9 for v1, gated) |
| Architecture and governance (Ent. §I, §XXIII) | twenty code gates and a data gate; drift check; allowlist and deny list; never-restart; change orders binding sessions; this chat; the audits | a monthly system block (uptime, completeness, cost, incidents) and an incidents file (EL-6); the simplification question in every audit brief (EL-7) |
| Orchestration (Ent. §III) | the cascade; REPORT_OK vs DECISION_BLOCKED; the register; the operator | none — named here, not built |
| Controlled learning, change authority, human governance (Ent. §XII, §XXVI, §XXVII) | champion/challenger; ten completion gates; IBKR Gates 1–3; register writes are the operator's | none |
| Prediction markets (Ent. §XXI; DTH §V) | `docs/prediction-market-spec-v1.1.md`, calibration-archive gate | none — the specification is stricter than the proposal |
| Cross-horizon state (Ent. §V; DTH §II) | market-state object v1 (8 dimensions, 3 dials); Books A–D as the horizon ladder; state v2 planned (6f) | per-horizon reads arrive with 6f; the alignment tag records the relationship from now (EL-1) |
| Session state (DTH §VI) | 6b intraday slots (09:15, 10:30, 15:00, 21:45), capture-instant T | 6b's state vector is fixed to DTH §VI's measurable variables (EL-5) |
| Alpha engines, expected-return layer, frontier synthesis (DTH §VII–§X) | Daily Cascade; the Dealer's Hand; the LLM called only when a gate opens | two paper engines, gated (EL-12); no ML expected-return models before N; no model calls at intraday cadence (§7) |
| Execution and TCA (DTH §XV, §XVI) | IBKR Gateway path; Phase 5 order gate; Gate 1.5 expression/execution analytics | execution tactics for Book B/C packets (EL-13); TCA fields are Gate 1.5's |
| Edge Ledger (DTH §XVIII) | — | a **view** over graded packets grouped by `setup_id`, not a store (EL-1 supplies the key; the view arrives with the first Quarterly) |
| Quarterly and annual review (Ent. §XXII–§XXV; DTH §XXII, §XXIV) | Audit #4 (14–15 Oct); Quarterly Structural + 6i; Annual Structural Review | metrics where computable (EL-6); per-agent reviews only if agents exist, and none do |

The 22 Enterprise deliverables (Ent. §XXIX) and the 20 DTH deliverables (DTH §XXVI) collapse into this section, §3–§7, and the documents the table names. Nothing else is produced "before implementation".

---

## §2 Rulings

**R-1 Functions, not agents.** Six LLM roles over one store and one model family are one perspective in six costumes; the Enterprise specification's own §IX says five agents repeating the same evidence are not five confirmations, and then builds five of them. Independence that exists comes from deterministic measurement (a grader cannot be persuaded), time separation (the forecast is on the ledger before the outcome), information partition (a reviewer that sees the evidence and not the thesis) and different methods (a naive baseline). Agents add none of these and add prompts to version, calls to pay for and self-evaluations to verify. Signed.

**R-2 DTH-1 is tactics, not a book.** The base rate for individual day trading is one-sided in the literature (Taiwan: well under 1% of day traders reliably profitable after costs; Brazil: roughly 97% of persistent day traders lost money), the Doctrine was written against the operator's own past self on volatile days, and a part-time operator on L1 data has no structural edge below the spread and the latency of a 4 GB box. Of DTH §VII's ten engines, opening-range momentum, VWAP mean reversion, volume/flow microstructure and most gap plays are crowded retail edges that do not survive DTH §XXVII's own cost question; they re-enter as *execution tactics* for decisions already approved. Engines with a mechanism for this operator are dealer-positioning/0DTE regimes, volatility dislocation and scheduled events; relative value/dispersion is Book C. Signed.

**R-3 The benchmark book.** Ent. §XVII asks what happens when a component is removed, and nothing in the system can answer what happens when the whole system is removed. Three static ledgers — cash, SPY, 60/40 — marked daily, are the denominator for every claim of value and should have preceded the first graded decision. Signed.

**R-4 Evaluation stays code.** Scores are computed; a paragraph may comment on them under the same audits; an LLM never writes counterfactual attribution, which is hindsight narrative by construction (Ent. §XIV). "Missed opportunities" are graded only against setups the system flagged and then declined — abstentions on the register — never against the universe of things that went up, or the metric rewards activity and repeals Ent. §XV. Signed.

**R-5 Red Team's objective.** Not skepticism maximised (Ent. §XXIII scores false objections) but *the cheapest way the conclusion could be wrong, at a stated cost in review time*. v0 is a packet rule enforced at write time (§3.1). v1 is a blinded model pass on material packets only — Book A changes and Book B above a size threshold — gated on decision volume (§6). Signed.

**R-6 The attention budget.** Neither specification budgets the scarcest input: every "governed approval" is the operator's time. The Doctrine gains an attention budget (§3.4). Anything beyond it queues; the Weekly prints the count used. Signed.

**R-7 Organizing principle, revised.** *Code establishes facts and measures outcomes. Books decide within their horizons. The state object holds the market view per horizon and never collapses them. Risk keeps the portfolio alive. Research proposes and never promotes. Doctrine changes by a ladder of evidence. Review asks what each part earned against a baseline. The operator governs, and the operator's attention is the budget everything else spends.* This replaces Ent. §I in the Doctrine's report section. Signed.

**R-8 Precedence.** Part 26 stays controlling. Both specifications are filed as requirements documents (§9) that this order cites; a future amendment may cite them; neither is edited to match the build. Signed.

---

## §3 Additions specified for sessions

### §3.1 Packet fields (EL-1) — in Phase 5, with the order gate

Six fields on the Decision Packet, all recorded at entry and immutable afterwards. The register refuses `DECISION_OK` without the last three, at write time, the way it refuses a Brookfield-related security.

| Field | Type | Definition |
|---|---|---|
| `setup_id` | slug | The setup family, from a new `config/setups.yaml` that starts with one entry per canonical setup family the Doctrine names per book, plus `unclassified`. `unclassified` is allowed and counted in the Weekly. This is the Edge Ledger's key. |
| `engine_id` | slug | The producer of the draft: `daily_cascade`, `weekly`, `monthly`, `operator`, or a registered paper engine id (§3.6). |
| `horizon_alignment` | enum `aligned` / `neutral` / `counter` | Computed at entry from the packet's direction against the sign of the market-state object's **trend** dimension for the packet's session: `aligned` if the same sign, `counter` if opposite, `neutral` if the dimension is absent or reads flat. Recorded, never recomputed. A second field, `alignment_weekly`, is added at 6f when the state object carries per-horizon reads; not before. |
| `review_changed` | enum `none` / `resized` / `restructured` / `hedged` / `delayed` / `rejected` | Set when a review — the operator now, the blinded pass later — changed the packet before entry. Default `none`. Ent. §XXII's "did the Red Team materially alter decisions" is a count over this field. |
| `falsifiers` | list, ≥ 1 | Observable evidence that would show the thesis wrong, stated before entry. |
| `counter_thesis` | one sentence | The other side's case, written from the evidence rather than from the thesis; the operator writes it for now. |

`invalidation` already exists on the packet and is reused. Red Team v0 is these three required fields and nothing more.

### §3.2 Cross-book exposure roll-up (EL-2) — Phase 5's heat/factor view, made explicit

The heat/factor view sums, across Books A–D and every options expression, at least: beta-adjusted notional (against SPY), sector exposure, duration for rate instruments, and vega for options. Limits are parameters in config; the order gate at entry reads the roll-up and refuses or resizes against the limits (DTH §XIV's approve / resize / restructure / hedge / delay / reject vocabulary is the gate's outcome enumeration, recorded in `review_changed`). The Enterprise specification's NVDA / QQQ / NVDA / short-Nasdaq-vol example is the acceptance test: four sensible packets that sum to a technology and vega concentration the gate must name.

### §3.3 Book Z — the benchmark ledgers (EL-3) — in Phase 5, beside the 6k paper tools

Three static reference portfolios, marked at every 16:45 close pass from the observation store, stored as `paper.benchmark` rows keyed by (session, ledger):

| Ledger | Definition |
|---|---|
| `cash` | Daily accrual at the 3-month T-bill yield (FRED `DTB3`). The NO TRADE book. |
| `spy` | SPY buy-and-hold from the start date. |
| `sixty_forty` | 60% SPY / 40% AGG, rebalanced on the first session of each month. Add AGG to the price registry if absent. |

Start date: the register's first packet date, or 1 Sep 2026 if earlier. Reporting: one line beside each book's paper equity in the Weekly and the Monthly — "vs cash / SPY / 60-40" — and Ent. §XVII's ablation question is answered against these three from then on. Marks are point-in-time: a benchmark row is never recomputed from a later vintage.

### §3.4 Doctrine additions (EL-4) — the Doctrine monthly, 3–4 Oct

Three sections for the Doctrine paper, decided at the session:

**(a) The change ladder** (Ent. §XVIII, written down):

| Tier | What changes | Evidence required | Authority | Reviewed |
|---|---|---|---|---|
| 1 Immediate tactical learning | a tactic, a threshold inside a book | one graded outcome, recorded | operator | weekly |
| 2 Regime-specific adaptation | a rule conditioned on a regime | ≥ N graded outcomes within the regime, the unconditional base rate beside the conditional (Base Rates convention) | operator, at the Doctrine monthly | monthly |
| 3 Medium-term relationship change | a signal's weight, a panel, a modifier right | an offline calibration study with a dated ledger; Red Team | amendment | quarterly |
| 4 Structural market change | a market-state dimension, a book's mandate | two independent lines of evidence, a mechanism, survival of one Annual Structural Review | amendment with the Annual review | annual |
| 5 Durable market principle | a white-paper claim in the timeless body | the full ladder below it satisfied; a dated premise-expiry line in the paper | Annual review only | annual |

A short-horizon anomaly cannot climb the ladder faster than one tier per review cadence.

**(b) The attention budget.** Proposed defaults for the session to confirm or change: at most five packet approvals per week; one review sitting per week of at most two hours; both counts printed by the Weekly; anything beyond queues to the next week. The budget is a rule, not a target.

**(c) The intraday rung.** R-2 recorded: Books A–D stand; intraday is a tactics layer for Books B and C and two paper engines under §3.6; no fifth book.

### §3.5 6b's state vector (EL-5) — within 6b

The intraday session state captured at each 6b slot is DTH §VI's list as measurable variables only: gap (overnight change, gap-fill fraction), opening-range high/low/break status, VWAP relation, breadth (the sector-ETF proxy already computed), realized versus implied volatility, VIX term structure (the champion and challenger legs), dealer positioning where the store has it, event proximity (hours to the next scheduled release from the events table), volume versus its 20-session average, and the alignment of the day's direction with the trend dimension. No narrative labels. Its consumers are the Daily Cascade and the Weekly; no engine reads it until EL-12.

### §3.6 Two paper engines (EL-12) — gated, §6

Each engine is an experiment with, before its first trade: a mechanism in one paragraph; the unconditional base rate of its setup beside its claimed conditional edge; a target N; a kill criterion. The kill criterion is fixed: **retired when, after N ≥ 40 graded paper trades, expectancy after modeled costs is ≤ 0 or its Brier is worse than the unconditional base rate's; never resized before N.** Candidates, in order: dealer-positioning/0DTE regimes (the Dealer's Hand, Part V); one scheduled-event engine (releases, earnings). Each registers an `engine_id`.

### §3.7 System-metrics block and incidents (EL-6) — Monthly, then Quarterly

A block in the Monthly, computed by code:

| Metric | Source |
|---|---|
| Uptime | share of `verdict=ok` lines in the heartbeat log for the month |
| Feed completeness | fresh / expected across the feed families at month end, from the freshness roster |
| Incidents | count and list from `docs/incidents.md` (new; dated lines; first two entries in §9) |
| Model cost | tokens per report from the narrative step, if the pipeline records usage; otherwise "not recorded" until it does |
| Withheld drafts | count from the withheld-drafts log |

The same block is Quarterly Structural's opening table. Ent. §XXIV's question — *if we rebuilt today, what would we remove, combine, automate, simplify or add?* — is added verbatim to the standing brief of every audit (EL-7), beginning with Audit #4.

### §3.8 Attribution taxonomy and counterfactual labels (EL-8) — at Gate 1.5

Every graded packet carries one primary attribution from DTH §XVI — `signal` / `expression` / `sizing` / `execution` / `override` / `noise` — assigned by rule from the grader's measures (path, excursion, fill versus arrival) and never by a paragraph. Every abstention and declined draft carries a counterfactual label from DTH §XX — `executable` / `approximately_executable` / `theoretical` — assigned at the time of the abstention, not at the time of grading.

### §3.9 Execution tactics for Books B and C (EL-13) — after Phase 5's order gate and 6b

A Book B or C packet, already approved, has its entry and exit timed intraday by rule from the 6b session state — VWAP relation, opening-range status, gap behaviour — with OCO brackets in paper through the IBKR path. The tactic is recorded on the packet; Gate 1.5's TCA measures it (arrival price, slippage, decision-to-order latency). This is where DTH §VII's opening-range and VWAP content earns a living.

---

## §4 What Audit #4 takes from this order (EL-7)

1. §1 as a section of the audit, updated to the repository as it stands on 14 Oct.
2. The simplification question, verbatim, as a standing item.
3. The system-metrics block's first reading.
4. The DTH-1 scope ruling re-examined with 6b's first captures in hand: which of the two engines, if either, is built first.
5. The amendment number confirmed and the architecture Part written.

---

## §5 Not built

Six standing agents. An orchestration layer as software beyond the cascade and the register. Per-agent quarterly self-evaluations. The 42 "before implementation" deliverables as separate documents. A fifth book. Ten alpha engines. ML expected-return models before any engine reaches N. Model calls at intraday cadence (the LLM is called when a gate opens; the rule stands). A 24-hour intelligence function (the 06:45 and 07:00 anchors and the 21:45 slot are it). A separate DTH risk governor (the order gate at entry is the governor; intraday limits are its parameters). A separate anomaly library (an anomaly is an SR intake type). LLM-written counterfactuals. Automatic promotion of anything.

---

## §6 Evidence gates (Tranche B)

| Item | Gate |
|---|---|
| EL-9 Red Team v1 — blinded model pass on material packets (evidence shown, thesis withheld), output recorded in `review_changed` | Gate 1.5 complete **and** ≥ 30 graded packets on the register |
| EL-10 Lessons register — the Learning Object as a table (lesson, evidence, effective N, regime, horizon, confidence, review date, production status) | the first Quarterly Structural with ≥ 5 lessons to file; until then, lessons live in the Doctrine's dated appendix |
| EL-11 Research-scan cadence — a monthly session brief that proposes SR intake entries and nothing else | Amendment #4 Tranches 1–4 worked down |
| EL-12 The two paper engines (§3.6) | Phase 5 deployed, 6b's first 20 sessions of captures in the store, Gate 1.5's TCA live |
| EL-13 Execution tactics (§3.9) | Phase 5's order gate deployed and 6b live |
| `alignment_weekly` | 6f (state object v2) |

---

## §7 Reconciliations with the two specifications

- Ent. §III's orchestration exists as plumbing; the specification's warning against a final overriding LLM is already honoured and is restated in the Doctrine's report section.
- Ent. §V's example table mixes market state with an instruction ("sell-the-rip"). State stays state; actions live in the books.
- Ent. §VI's domain-to-enterprise channel is the SR intake template; an anomaly from any engine or slot is an intake entry of type `anomaly`, with recurrence counted on the register. No library.
- DTH §II's "strategic directional view" is the trend dimension now and the per-horizon reads at 6f; it is a prior in the sense of §3.1's tag, never a command, and DTH §XXIII's test of whether it adds value is the Quarterly's table of graded packets by `horizon_alignment`.
- DTH §XV's hard controls are the deploy rules, the order gate and the register's write-time refusals; REPORT_OK versus DECISION_BLOCKED is already the split.
- Both specifications' quarterly review lists apply to functions, by the metrics in §3.7 and the Brier ledger. "Did the Red Team materially alter decisions" is the count of `review_changed ≠ none`.

---

## §8 Work order

| ID | Item | Placement | Hours |
|---|---|---|---|
| EL-0 | File this order and the two briefs; create `docs/incidents.md` with the two entries in §9 | H-1's session, before its own items | 0.5 |
| EL-1 | Packet fields and Red Team v0 (§3.1), `config/setups.yaml`, write-time refusal, gate | Phase 5 | 4–6 |
| EL-2 | Cross-book roll-up explicit, limits in config, the four-packet acceptance test (§3.2) | Phase 5 (within the heat/factor view) | +2–4 |
| EL-3 | Book Z ledgers, marks, reporting lines (§3.3) | Phase 5, beside 6k | 4–6 |
| EL-4 | Doctrine sections (§3.4), decided at the session, applied by a library session | Doctrine monthly, 3–4 Oct | 2–3 |
| EL-5 | 6b state vector fixed to §3.5 | 6b | +0–2 |
| EL-6 | System-metrics block, incidents file, Quarterly opening table (§3.7) | after 6b, with Quarterly Structural + 6i | 4–6 |
| EL-7 | Audit #4 items (§4) | Audit #4, 14–15 Oct | 1 |
| EL-8 | Attribution taxonomy and counterfactual labels (§3.8) | Gate 1.5 | 4–6 |
| EL-9 | Red Team v1 | gated (§6) | 8–12 |
| EL-10 | Lessons register | gated (§6) | 6–8 |
| EL-11 | Research-scan cadence | gated (§6) | 3 per scan |
| EL-12 | Two paper engines | gated (§6) | 15–20 each |
| EL-13 | Execution tactics | gated (§6) | 10–15 |

Tranche A (EL-0…EL-7): ≈ 20–30 h, all inside work already scheduled. Tranche B (EL-8…EL-13): ≈ 65–95 h, none of it before its gate. By hand: the three rulings (done), the Doctrine session's decisions on §3.4(b), the Audit #4 rulings.

---

## §9 Filing

- `docs/change-order-enterprise-layer-2026-09-27.md` — this order.
- `docs/briefs/enterprise-layer-spec-2026-09-27.md` — the Enterprise specification, verbatim, requirements document.
- `docs/briefs/dth-1-spec-2026-09-27.md` — the DTH-1 specification, verbatim, requirements document.
- `docs/incidents.md` — created by EL-0 with two entries:
  - **INC-1 2026-09-27** — the off-box backup never ran under its unit: `CHESTER_RCLONE_REMOTE` was never set on the box (every 02:30 sweep since deploy ended `no_remote rc=1`), and with it set the snapshot failed because the unit starts in `$HOME` (`ModuleNotFoundError: altdata`). Found by hand 27 Sep; by-hand copy taken 16:04 UTC; drop-in `remote.conf` added by hand; fix B-1 at 61e9b4b; first unit-run proof due 28 Sep 02:30 ET. Monitoring gap: the heartbeat's verdict line had no `backup=` field (H-1 adds it).
  - **INC-2 2026-09-27** — narrative prompts were truncated silently from first light until 27 Sep 11:02 ET (style guide cut at 6,000 characters, payload at 12,000); every close since 23 Sep and the first Weekly were written from a partial brief. Editions stand as published (each passed the audits); first whole-brief editions are 28 Sep 07:00 and 16:45. Fix W-1 item 7 at 1846815; a gate now confirms every template and the full Weekly payload reach the model whole.

Precedence and numbering as in the header. Rulings R-1…R-8 are signed (R-1…R-3 on 27 Sep; R-4…R-8 on 2 Oct); §8 is filed for Ari's word at Audit #4.
