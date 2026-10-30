# Learning Loop v2 — specification DRAFT

**Status: DRAFT for the operator's ruling.** Written 25 Oct 2026 (session B, B65) on branch `b65-learning-loop-v2` from `origin/b64-cloud-sessions-brief` (`f270731`). Docs only: no code, config, prompt, register or ledger is changed. Nothing in this brief grants a right, changes a weight, or puts a model in the execution path.

**What this answers.** On 24 Oct 2026 the operator asked whether the system's self-learning loop is best in class, and what else would make it learn, calibrate, critique itself, widen its knowledge and, above all, make better recommendations. The answer given in chat: the governance half is strong (pre-registration, point-in-time data, the deflated Sharpe, the hold-out, the change ladder, the sittings), while the learning half is deliberately slow and has seven gaps. This brief specifies the seven, in the shape of the 6f brief (`docs/briefs/6f-spec-draft-2026-10-24.md`).

**Sources read.**
- **Code:** `altdata/probability_ledger.py`, `altdata/grader.py`, `altdata/benchmark.py`, `register/scoreboard.py`, `altdata/dealer_scorecard.py`, `altdata/state_calibration.py`, `daily_cascade/outlooks.py`, `altdata/narratives.py`, `altdata/withheld_log.py`, `altdata/thesis_register.py`, `altdata/model_meter.py`, `alpha/loops/nightly.py`, `alpha/loops/weekly.py`, `alpha/loops/quarterly.py`, `alpha/allocate.py`, `alpha/promote.py`, `alpha_proposer/propose.py`, `config/alpha_constitution.yaml`, `config/alpha.yaml`.
- **Docs and orders:** `docs/alpha-lab.md`; the Alpha Lab change order of 12 Oct; the Enterprise Layer order of 27 Sep (R-1 to R-8, its section 1 mapping, section 3.4's ladder and attention budget, section 6's gates); `docs/ledgers/README.md`; 6f's sections 3 and 8; the Operating Doctrine's Part IX; the Reader's Guide's Part IX; the rulings of 24 Oct (morning, and the afternoon file on `origin/a61b-feed-repair`).
- **A departure in the reading:** the paste names "the Operating Doctrine Part V". Part V is Regime Switches. Measurement, learning and the adoption protocol are its **Part IX**, which is what was read, together with Rule 20 and Appendix D's ladder.

**Where the code and a document differ, the code wins**, and each difference is named where it falls.

---

## 1. What the loop is today, from the code

The system learns along one line and returns along three paths.

**The eight stages.**
1. **Feeds** write the store, each on its own clock.
2. **The store** keeps every row with its `available_at`, so any read can be made as of an instant.
3. **The object** (`regime.py`) turns the store into one market-state object per session; every report reads it.
4. **Reports** print what the object and the store say.
5. **The register** records decisions, taken, declined and draft alike.
6. **The ledger** holds every stated probability, its resolution criterion declared at emission.
7. **Grading** scores decisions and probabilities from stored prices only.
8. **The Doctrine's sittings** read the grades and change rules at the tier the change ladder names.

**The three return paths.**
- **Ratified config:** a sitting rules a value, and a session commits it.
- **The lab's evidence**, tabled at a sitting. The lab changes only its own sizes and weights.
- **The scans' proposals:** narrative proposals, intake drafts and the lab inbox, each behind a human gate.

*[Figure 1 placeholder: the loop as a ring of the eight stages, the three return paths drawn back from grading to config, the lab and the scans, each arrow labelled with the gate it crosses; the seven additions marked where they attach.]*

**The learning mechanisms, one by one.**

| Mechanism | Where it lives | What it grades | What it can change by itself | Sample, as the notes report it |
|---|---|---|---|---|
| Probability ledger | `altdata/probability_ledger.py`, `ProbabilityLedger.record`, `.resolve`, `.score_by_source` | every stated probability; Brier per row, per source, against the coin's 0.25 | nothing | the laptop store holds no rows (6f build notes: "k = 0 for every dial and horizon"); the box's counts are not in the repository |
| Base-rate outlooks | `daily_cascade/outlooks.py`, source `daily_close_outlook` | the empirical frequency of a declared rule, clamped short of certainty | nothing | accruing; no count in the notes |
| Grader | `altdata/grader.py`, `grade_one`, `run` | every decision, taken, declined and draft, from stored closes | nothing | "no cell has 10 graded decisions" (Doctrine #2 pack) |
| Scoreboard | `register/scoreboard.py`, `expectancy_13w`, `benchmarks_4q` | 13-week expectancy in R by book, regime and dial; the books against Book Z | nothing | "accruing (n=k)" below `min_n` 10 (b48 notes) |
| Benchmark book (Book Z) | `altdata/benchmark.py`, `compute_marks` | cash, SPY and 60/40, marked daily | nothing | marked since its start date |
| Dealer scorecard | `altdata/dealer_scorecard.py`, `rates_table` | k/n with Wilson intervals, against its base rate and baseline | nothing | "insufficient sessions" below 20 (the Monthly's dealer retrospective) |
| Dial calibration (6f) | `altdata/state_calibration.py`, source `market_state` | each dial's transition row, multi-class Brier against persistence and the uniform row | nothing | `uncalibrated (n = 0 of 30)` on the laptop store (6f build notes) |
| Narrative register | `altdata/narratives.py`, `validate_evidence`, `propose` | stories by state, scored on outcome once confirmed | nothing: confirming is the operator's | the proposals pin is six (chain-5) |
| Thesis register | `altdata/thesis_register.py` | the Quarterly's theses, by ordering and direction | nothing: drafts only | none resolved (no Quarterly yet) |
| Withheld log | `altdata/withheld_log.py`, `record_edition` | nothing; it records every withheld paragraph | nothing | per edition |
| Contradiction table | `config/market_state.yaml`, eight rows | nothing; it names disagreements on the object | nothing | every session |
| The Alpha Lab | `alpha/` | engines in ledger-paper: posteriors, kill rule, drift, deflated Sharpe | **its own sizes and weights only**: the nightly loop's `posterior_step`, `kill_step`, `allocate_step` and promotion at min_size, the weekly loop's bounded re-fit and rebalance, and the quarterly meta-loop's `meta_tighten` | engines below `min_signals` (100 daily) print "accruing"; engines 6 and 7 "awaiting (n=k of 30)" |

**The answer to "can it change itself":** outside the lab, nothing changes anything on its own authority. That is by design (R-7: "Research proposes and never promotes. Doctrine changes by a ladder of evidence."). Inside the lab, the loops change sizes and weights and never an engine's rules, and the meta-loop asks each quarter whether that learning earned its keep.

**One difference between the code and its own documentation.** `probability_ledger.py`'s schema allows a probability in [0, 1] (`CHECK (probability >= 0.0 AND probability <= 1.0)`), while `ProbabilityLedger.record` refuses 0 and 1 (`if not 0.0 < p < 1.0`, held by `tools/validate_grader.py`'s "NO CERTAINTIES (6c-3)"). The refusal is at the write path, not the schema. Writes go through `record`, so the rule holds in practice. A direct SQL insert would not be refused.

---

## 2. The seven additions

### 2.1 Decision quality as the headline

**The gap.** The ledger scores each source's Brier against a coin, and says in its own docstring why that is not enough: "Brier conflates calibration with resolution ... separating them needs the reliability/resolution/uncertainty decomposition, which needs an n this ledger will not have for a year ... the decomposition is named as owed rather than faked." The grader already grades declined and draft decisions ("Evidence and Inference's shadow-outcome argument"), and Book Z is marked daily. Nothing yet puts them together into one answer to whether the system is getting better.

**The mechanism.**
- **Murphy's decomposition** of the Brier score (reliability, resolution, uncertainty) over the ledger's resolved rows, by source family and by horizon bucket, with n beside each cell. It prints "accruing (n=k of 100)" below 100 resolved rows a cell. Reliability needs binned forecasts, and ten bins of ten is the least that says anything.
- **The counterfactual ledger, per book:**
  - the declined packets' graded outcomes (already in the grades, `_taken()` false);
  - the drafts' (the cost of abstention);
  - the stack's implied stance against Book Z's three ledgers.

  These are computed from the stored grades, never written by a model (R-4).
- **One line a month:** "is it getting better". The system Brier and its decomposition, and the system expectancy in R, each with its 13-week and 52-week trend and its n.

**Inputs:** the `probabilities` table (resolved rows); the grades (`GradeStore.all_grades`); `paper.benchmark` rows (`altdata/benchmark.py`); `register/scoreboard.py`'s `expectancy_13w`.

**Writes and prints.** No new table: it is computed at read. It prints in the Monthly's Lab report and in each Doctrine sitting's pack, and the Weekly's top gains nothing (its budget is ruled).

**Rights:** report-only. **Ladder:** not a rung, since it changes nothing; it is the evidence the rungs read. **Gate plan:** a code gate on fixtures, with a seeded ledger whose decomposition is known in closed form. **Hours:** 6. **Dependencies:** none.

### 2.2 Bounded online calibration

**The gap.** The ledger measures calibration and corrects nothing. A source that is reliably overconfident keeps being overconfident, and the sitting can only rule a new value by hand.

**The principle: the sitting ratifies rules, not values.** A sitting rules four things: the method, the band within which an adjustment may move, the minimum sample, and the switch. Inside that band the adjustment moves monthly without a sitting, and every move is a loop event.

**The mechanism.**
- **Recalibration of the ledger's probabilities,** per source. The method is chosen by sample:
  - **Platt scaling** (a two-parameter logistic map) from 100 resolved rows a source;
  - **isotonic regression** from 1,000, because isotonic overfits below that;
  - nothing below 100: the floor.

  The calibrated probability is a second column, printed beside the raw one and never instead of it. The raw forecast stays immutable, as the ledger's trigger requires.
- **Conformal prediction intervals** on the outlook ranges. The interval is the empirical quantile of past absolute errors at the declared coverage, with its n. Below 50 errors it is not printed.
- **Base rates as Bayesian posteriors** (Beta-binomial, as the lab's `posterior_step` already does for win rates), each with a ratified prior. The update is printed beside the frequentist rate the Reader's Guide 9.2 describes.
- **The band.** Each adjustment is confined to a ratified band, for example a calibrated probability within 0.10 of the raw one. A move to the band's edge is printed as "at band".

**Inputs:** `probabilities` (resolved rows by source); the outlook rows (`daily_close_outlook`); `baserate.*`.

**Writes and prints.** A `calibration` table beside `probabilities`: source, method, parameters, n and the band, all versioned. A loop event per monthly refit. The calibrated column prints in the Lab report, never in a report sentence.

**Before the first ratified band, nothing moves:** the table is computed and printed as "proposed, not ratified".

**Rights:** report-only; a calibrated probability reaches no packet, dial or band. **Ladder:** tier 3 ("a signal's weight, a panel, a modifier right", which needs "an offline calibration study with a dated ledger"). Each method and band is an amendment at a quarterly sitting.

**What the sitting sees before ratifying a band:** the source's reliability diagram with n, the method's out-of-sample Brier on a held-out third against the raw Brier, and the largest adjustment the band would have allowed over the history.

**Gate plan:** pre-registered per source in a dated ledger; the gate refuses a band without its ruling row. **Hours:** 8. **Dependencies:** 2.1; the floor of 100 resolved rows a source.

### 2.3 A forecaster ensemble into the ledger

**The gap.** The ledger's sources are code (outlooks, dials, theses) and the Monthly's weights. No forecaster answers the register's standing questions daily. And R-1 is right that "six LLM roles over one store and one model family are one perspective in six costumes". The independence it names comes from "time separation" and "different methods", which a scored ledger supplies and agents do not.

**The mechanism.**
- **N forecasters, at least two model providers,** each with its own prompt. A local model joins if the operator's local-AI plan lands.
- **Daily, each answers the open questions** as probabilities, before the outcome, without seeing the others' answers. Each answer is written to the ledger as its own source, `forecaster:<provider>:<prompt-id>`.
- **The aggregate** is the extremized mean of the log-odds, weighted by each forecaster's track record. The extremizing follows the forecasting-tournament result (Tetlock and Mellers' Good Judgment Project; Baron and others on extremizing aggregated probabilities). The aggregate is scored as its own source, `forecaster:aggregate`.
- **Equal weights until each forecaster has 100 resolved rows.** After that the weights follow each one's Brier, shrunk toward equal.

**Which questions.**
- The ledger's existing open claims whose criteria are mechanical: the dials' transitions (6f), the outlooks, the theses' 3-month calls.
- The narrative register's confirmed stories' implied outcomes.
- Nothing new is invented for them to answer. Every question has its resolution criterion already declared at emission.

**Cost.** One call per forecaster per day over a code-built packet, the proposer's shape (`alpha_proposer/packet.py`). Counted by `model_meter` in tokens, never dollars (AUD-2). No price is stored in the repository, so the ceiling is ruled in tokens a day (decision 4).

**Rights:** none. No forecaster output reaches a packet, a dial or a report sentence; only the ledger's own lines print it. **Ladder:** tier 3 for any use beyond the ledger. **Gate plan:**
- each forecaster's prompt is pre-registered by manifest (`alpha/manifest.py`'s pattern), and a changed prompt is a new source;
- a gate proves no forecaster import reaches a report writer, the register or the object.

**Hours:** 10, including a second provider's client behind `model_meter`. **Dependencies:** a second provider's key in `.env` (the operator's; R1's key list names `OPENAI_API_KEY`, but no code here calls it); 2.1, for the scoring cut.

**Where the code differs from the paste's assumption.** `altdata/model_meter.py` builds "the one Anthropic client". A second provider is new code, not a setting.

### 2.4 The critic loop with memory

**The gap.** The system records its failures in five places and reads them in none:
- withheld paragraphs (`withheld_log.record_edition`);
- hypotheses that failed (the lab's register, failures kept);
- calls graded wrong (the grades);
- incidents (`docs/incidents.md`, read by `altdata/system_metrics.py`);
- X claims contradicted at verification.

The X pilot's ledgers are files in the box's inbox, read by `daily_cascade/digital_addendum.py`'s `read_ledger`. No column for a verification verdict is read in code, so that leg is not found (Notes).

**The mechanism.**
- **An error corpus,** assembled nightly by code from the five sources into one dated file under the research directory. Each item carries its source, its instant and what was stated against what happened, from stored evidence only.
- **A weekly critic run:** one model call over the week's corpus and outcomes. It writes `critique-<date>.md` and, where it proposes a prompt or template change, a draft change order. Prompts and templates are configuration, so the change ladder applies: a tier-1 change is taken at the weekly review sitting, never between sittings.
- **The critic runs in chat,** as a scheduled task writing to Drive like the Saturday brief, not on the box (decision 6). It needs the library and the notes, which the box does not hold, and it costs the box's model budget nothing.
- **A retrieval index** over the library, the ledgers, the notes files and the scans, for the proposer, the critic and the Saturday brief. Local embeddings with a small open model (decision 7) keep every document on the system's own machines; an external embedding service would send the library out, which the sources rule does not cover.
- **EL-10's lessons register** is the durable home, with the order's schema: "lesson, evidence, effective N, regime, horizon, confidence, review date, production status". Its gate stands: "the first Quarterly Structural with ≥ 5 lessons to file; until then, lessons live in the Doctrine's dated appendix." The critic proposes lessons; it never files them.

**Rights:** none. The critic writes drafts. **Ladder:** its proposals take the tier of what they change. **Gate plan:** the corpus builder holds no model call (a code gate); the critic's prompt is versioned and pre-registered. **Hours:** 10 (corpus 3, critic task 2, the index 5). **Dependencies:** EL-10's gate for the register itself.

### 2.5 Bandit allocation in the lab

**The gap.** The lab's allocator (`alpha/allocate.py`, `weights`) is quarter-Kelly over posteriors, with the heat cap and correlated engines counted once. It re-weights weekly and does not explore: an engine with a wide posterior and a good mean is sized like one with a narrow posterior.

**The mechanism.**
- **Thompson sampling** over validated engines for the lab's paper capital. Each week, draw from each engine's expectancy posterior (the `edge_posterior` rows the nightly loop already writes), and weight by the share of draws in which the engine is best.
- **Within the constitution:** quarter-Kelly stays the size ceiling, as do the heat cap and the minimum-size rule. Strong priors come from each engine's validated expectancy.
- **A cap on reallocation:** at most a ruled share of the lab's capital moves in a week (decision 8).

**Why policy-gradient reinforcement learning on prices is rejected.**
- The constitution's `min_signals` is 100 for a daily engine. A year of daily data is about 252 decisions for one engine.
- Policy-gradient methods learn from many thousands of independent episodes. A daily market supplies one path, so at 252 a year those episodes would take decades.
- The variance of a policy-gradient estimate at that n is larger than any edge the Doctrine expects. A bandit over a handful of validated arms needs only that each arm's posterior be honest, which the nightly loop already maintains.

**What the quarterly meta-loop measures about it:** the same counterfactual it measures for a rebalance. That is the lab's return under Thompson weights against its return under the quarter-Kelly weights over the same stored returns. A negative quarter writes `meta_tighten` and halves the reallocation cap.

**Rights:** the lab's own, inside the constitution. **Ladder:** a constitution change is the operator's ruling, quoted with a hash row (`docs/alpha-lab.md`, "The hash ledger"); the cap is session-set in `config/alpha.yaml`. **Gate plan:** synthetic arms with known means in `tools/validate_alpha.py`'s style. **Hours:** 6. **Dependencies:** at least two engines past validation and `min_signals`, which no engine is yet. **Unbuildable until then:** with zero or one validated arm there is nothing to allocate between.

### 2.6 Value of information for data

**The gap.** The system records what it could not see: dimensions absent with their reasons (the object), "awaiting" legs (the lenses, the flags), the "not tracked" rows. It never asks which absence costs the most.

**The mechanism.** For each family of ledger error (by source and horizon), take the resolved rows whose emission recorded an absent dimension or an awaiting leg. Compare their Brier with the rows that had the input. The method is declared, not fitted: the difference in mean Brier, with its n and a bootstrap interval, by missing input. It also counts how often each input was missing at emission.

**Output:** a ranked list (input, rows affected, Brier difference, interval), which the scans and the source checks read as their search order. It prints in the Monthly's Lab report and the Doctrine pack.

**Inputs:** the `probabilities` rows; the stored objects' absent dimensions and their reasons (`regime.latest()`'s payload as stored); the outlooks' and lenses' "awaiting" stamps.

**Rights:** report-only. **Ladder:** none: it changes a search order, which is the operator's. **Gate plan:** a fixture where one missing input carries all the error. **Hours:** 5. **Dependencies:** 2.1; a ledger row must record what was missing at emission, which only the market-state rows do today. Other sources need a `missing_inputs` field at emission (one line each).

### 2.7 Automated post-mortems and Red Team v1's path

**The gap.** The Doctrine's 9.2 asks six categorical questions of every closed packet, stamped by the operator at the weekly session. Nothing prepares the evidence for that stamping.

**The mechanism.**
- **A post-mortem file per graded miss,** written from stored evidence only, in three parts: what was knowable at entry (the packet, the object, the store as of entry); what the system said (the packet's thesis, falsifiers, counter-thesis); what happened (the grade).
- **Code writes all three parts.** A model may only shorten them into one paragraph, behind the numeral audit. It never names a cause.

  This is narrower than the paste, deliberately. R-4 rules: "an LLM never writes counterfactual attribution, which is hindsight narrative by construction." A model-written post-mortem that explains a miss is that, so the explaining stays with the operator's six answers.
- **Filed against a lesson** in the register (2.4), as evidence, never as a cause.

**Red Team v1 (EL-9).** A "blinded model pass on material packets (evidence shown, thesis withheld), output recorded in `review_changed`", gated on "Gate 1.5 complete **and** ≥ 30 graded packets on the register". The register's current count is below that ("no cell has 10 graded decisions").

What would let it run sooner without moving the gate: run the blinded pass in shadow on every material packet from now on, writing its output to a file and never to `review_changed`. By the time the gate opens, its record against the outcomes already exists, and the sitting rules on evidence instead of a promise. The gate's 30 is the operator's ruling to amend, not this brief's.

**Rights:** none. **Ladder:** EL-9 is gated as ruled. **Gate plan:** the post-mortem's three parts are code-built and checked against the stored rows; the shadow pass writes nowhere but its file. **Hours:** 6. **Dependencies:** graded misses; Gate 1.5 for EL-9 itself.

---

## 3. Rights and boundaries

| Addition | May write | May never write | Gate that proves it | Switched off by |
|---|---|---|---|---|
| 2.1 Decision quality | nothing (computed at read) | packets, dials, bands, tells, narratives, rights, production prompts | a code gate on a closed-form fixture | removing its Lab-report hook |
| 2.2 Calibration | the `calibration` table; loop events | the raw probability; any packet, dial, band or report sentence | a gate refusing a band without its ruling row | its `enabled: false` in config |
| 2.3 Forecasters | ledger rows under `forecaster:*` | anything outside the ledger | an import gate (no report writer, register or object) | the scheduled task's switch; its timer is the operator's |
| 2.4 Critic | the corpus file; critique files; draft change orders | prompts or templates in production; the lessons register | the corpus builder's no-model gate | the chat task's switch |
| 2.5 Bandit | `alpha.db` weights, inside the constitution | anything outside `alpha.db` | `validate_alpha_no_orders`, `validate_alpha` | `config/alpha.yaml` reverting to quarter-Kelly |
| 2.6 Value of information | nothing (computed at read) | as 2.1 | a fixture gate | its hook |
| 2.7 Post-mortems | post-mortem files; the shadow Red Team's file | `review_changed` before EL-9's gate; any cause | a gate checking each part against stored rows | its step's switch |

---

## 4. Frontier-model use

**Where a model earns its keep in this loop.**
- **Forecasting into a graded ledger (2.3):** the model's output is scored, so its value is measured, not assumed.
- **Critique (2.4)** of prose and templates against outcomes.
- **Extraction:** the scans' cited notes.
- **Hypothesis generation:** the proposer, already behind the model-idea rule.
- **Shortening a code-built post-mortem (2.7).**
- **Retrieval-grounded reading** of the system's own record.

**Where a model is barred.**
- The execution path: no order, gate or broker module, already held by the deny list and `validate_alpha_no_orders`.
- Any figure in a report: the numeral audit.
- Any right, band, dial or tell.
- Counterfactual attribution (R-4).

**Model choice and cost, by addition.** The operator's standing preference is Opus on scheduled tasks. The meter counts tokens, so the cost is stated in calls; the tokens per call are measured in the first week of each addition.

| Addition | Model | Calls |
|---|---|---|
| 2.1, 2.2, 2.5, 2.6 | none: code | 0 |
| 2.3 Forecasters | Opus for the Anthropic forecasters; the second provider's frontier model; a local model if the plan lands | N a day, one per forecaster (N = 3 recommended: decision 4) |
| 2.4 Critic | Opus, in chat | one a week |
| 2.4 Retrieval index | a local embedding model | none on the meter |
| 2.7 Post-mortem shortening | the narrative step's model (`daily_cascade.narrative.DEFAULT_MODEL`) | one per graded miss |

---

## 5. How to tell it is working

| Metric | Minimum sample before it is read | Where |
|---|---|---|
| System Brier and its decomposition | 100 resolved rows a cell | Lab report; sitting pack |
| System expectancy in R | the scoreboard's `min_n` 10 a cell; the Doctrine's 30 for a trust change, 50 for a tier | Lab report; Weekly top (existing) |
| Calibrated against raw Brier, out of sample | 100 rows a source (Platt), 1,000 (isotonic) | Lab report |
| The forecaster aggregate against its best single forecaster | 100 resolved rows each | Lab report |
| Bandit against quarter-Kelly (the meta-loop's counterfactual) | one whole quarter, two validated arms | the Quarterly's lab page |
| Value-of-information ranks, stable month to month | 30 affected rows an input | Lab report |
| Post-mortems filed against lessons | five lessons (EL-10's gate) | the Doctrine's dated appendix until then |

**What each monthly sitting reads:** the "is it getting better" line, the calibration table marked proposed or ratified, the forecasters' scores, the value-of-information list and the count of post-mortems by outcome.

**What would show v2 is not earning its keep.** The quarterly meta-loop's question, applied to v2: did each addition improve the score it was built to improve, against its own counterfactual, over the quarter?
- A calibration that does not beat raw out of sample is withdrawn.
- An aggregate that does not beat its best member is withdrawn.
- A bandit that loses to quarter-Kelly is capped.
- A critic whose proposals the weekly sitting adopts at zero over a quarter is stopped.

---

## 6. The work order

| Tranche | What | Hours | Depends on | Starts | One paste? |
|---|---|---|---|---|---|
| LL-1 | 2.1: the decomposition, the counterfactual ledger, the monthly line | 6 | nothing | after the 1 Nov Monthly | yes |
| LL-2 | 2.6: value of information; the `missing_inputs` field at emission | 5 | LL-1 | after LL-1 | yes |
| LL-3 | 2.4a: the error corpus (code) | 3 | nothing | after the 1 Nov Monthly | with LL-2 |
| LL-4 | 2.7: code-built post-mortems; the shadow Red Team file | 6 | graded misses exist | after LL-3 | yes |
| LL-5 | 2.4b: the critic as a chat task; 2.4c: the local retrieval index | 7 | LL-3; decision 7 | after LL-3 | yes |
| LL-6 | 2.3: the forecasters (a second provider's client behind the meter, manifests, the aggregate) | 10 | decision 4; the operator's key | after the rulings | yes |
| LL-7 | 2.2: calibration (the table, Platt, conformal, posteriors) | 8 | LL-1; **waits for n:** 100 resolved rows a source before any band is proposed | built after LL-1, prints "proposed" | yes |
| LL-8 | 2.5: the bandit | 6 | **waits for n:** two engines past `min_signals` (100 daily) and validation | when two arms exist | yes |
| | **Total** | **51** | | | |

**What can start after the 1 Nov Monthly:** LL-1 and LL-3, about 9 hours, both code with no prompt, so they can run the week of 2 Nov beside 6f's tranches.

**What waits for sample sizes:**
- LL-7's bands, until 100 resolved rows a source;
- LL-8, until two validated arms;
- EL-9's live pass, until Gate 1.5 and 30 graded packets;
- EL-10's register, until the first Quarterly Structural with five lessons.

---

## 7. DECISIONS FOR ARI

**1. Build 2.1 first.** Options: (a) 2.1 first, then 2.6 and the corpus; (b) the forecasters first; (c) all seven in parallel. **Recommend (a).** Every later addition is judged by 2.1's line, so building it first means each later one arrives with its own yardstick. It needs no model call and no new sample. The forecasters (b) would start scoring before anything could say whether the system as a whole is improving.

**2. The recalibration method and its floor.** Options: (a) Platt from 100 resolved rows a source, isotonic from 1,000, nothing below 100; (b) isotonic only; (c) none until a year of rows. **Recommend (a).** Platt's two parameters are the most a hundred rows can carry, and isotonic's flexibility needs an order of magnitude more before it stops fitting noise. A floor stated now keeps the first adjustment from being argued case by case.

**3. The calibration band.** Options: (a) a calibrated probability within 0.10 of the raw one, ratified per source at a quarterly sitting; (b) 0.05; (c) no band, the method's output as is. **Recommend (a).** The band is what makes "the sitting ratifies rules, not values" safe: the method moves monthly, and its reach is ruled. 0.05 would hide most real miscalibration at these sample sizes. No band is tier 3 without the tier.

**4. The forecasters: how many, which providers, and the daily ceiling.** Options: (a) three, two on Opus with distinct prompts and one on a second provider, at a ceiling of three calls a day; (b) five across three providers; (c) Opus only. **Recommend (a).** Two providers is the least that answers R-1's "one model family". Three keeps the cost to three calls a day, and the aggregate has something to extremize. (c) is R-1's costume problem exactly. (b) can follow once (a)'s aggregate beats its best member.

**5. Forecasters see nothing of each other.** Options: (a) strictly independent, each from the same code-built packet; (b) a second round in which each sees the others' answers. **Recommend (a).** Independence is the ensemble's whole value, and a second round converges the answers before they are scored. The tournament evidence on extremizing assumes independent judgments.

**6. Where the critic runs.** Options: (a) in chat, as a scheduled task writing to Drive; (b) on the box, through `model_meter`. **Recommend (a).** It reads the library and the notes, which live in the repository and not on the box. Its proposals go to a human sitting anyway. The box's model budget stays on the reports.

**7. Local embeddings.** Options: (a) yes: a small open embedding model on the laptop or the box, the index a file the critic and the proposer read; (b) an external embedding service; (c) no index. **Recommend (a).** An external service sends the library and the ledgers out of the system, which no sources rule covers. A local index costs a one-time build and nothing per query. (c) leaves the critic reading the week's corpus with no memory beyond it.

**8. The bandit's reallocation cap.** Options: (a) at most 10% of the lab's capital a week; (b) 25%; (c) no cap beyond the constitution. **Recommend (a).** Thompson sampling at small n swings, and the meta-loop needs a quarter of small, attributable moves to measure it. The cap is session-set, so it can widen on evidence.

**9. Post-mortems: nightly or weekly.** Options: (a) weekly, the Saturday before the Sunday session, one file per graded miss of the week; (b) nightly, as each grade lands. **Recommend (a).** The Doctrine stamps post-mortems at the weekly session, so a nightly file waits there anyway. Weekly batching keeps the operator's attention budget to one sitting.

**10. Red Team v1 in shadow before its gate.** Options: (a) run the blinded pass in shadow now, to a file, never to `review_changed`; (b) wait for EL-9's gate as ruled. **Recommend (a).** It leaves the gate where the operator put it, and it means the gate opens on a track record instead of a promise. The cost is one model call per material packet, and material packets are few.

**11. The model's part in a post-mortem.** Options: (a) code builds all three parts, and a model may only shorten them, never naming a cause; (b) a model writes the post-mortem from the evidence, as the paste proposes. **Recommend (a).** R-4 bars a model from counterfactual attribution, and explaining a miss is attribution. The operator's six categorical answers are the cause field, and the model's job is to make the evidence quick to read.

---

## Notes

**What could not be found in the code.**
- **A store of X claims contradicted at verification.** The X pilot's ledgers are read from the box's inbox by `daily_cascade/digital_addendum.py` (`read_ledger`), and no verification-verdict column is read in code. 2.4's corpus takes that leg only if the triage file carries one.
- **The probability ledger's and the register's counts on the box.** The notes report the laptop's (empty) and the Doctrine #2 pack's ("no cell has 10 graded decisions"). The first tranche should print the box's.
- **Any stored price per model call.** The meter counts tokens (AUD-2); section 4 states cost in calls for that reason.
- **The "Doctrine Part V"** the paste names is Regime Switches. Measurement and learning are Part IX, which was read instead.

**Already built, in part, among the seven.**
- **2.1:** its inputs are built. The grader grades declined and draft decisions (the shadow outcomes); Book Z is marked; the scoreboard computes expectancy. Only the decomposition and the assembly are new.
- **2.5:** the posteriors it samples from are built (`posterior_step`).

**Unbuildable now.**
- **2.5** has fewer than two validated arms.
- **2.2's bands** are below the floor of 100 resolved rows a source.
- **EL-9's live pass** is below its ruled gate.

**The figure placeholder (section 1):** the loop drawn as a ring of the eight stages, feeds to Doctrine. The three return paths are drawn back from grading into ratified config, the lab and the scans, each arrow labelled with the gate it crosses (a sitting, the constitution, a human confirmation). The seven additions are marked at the stage each attaches to.

- **CI:** CI queued, run 40146406646 (at `67e40a5`). The next paste that touches this branch reads the result once.
