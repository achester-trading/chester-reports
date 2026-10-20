# b48-scoreboard: the Card's scoreboard, measurement only (session B, 20 Oct 2026)

**What it is.** Rows 5, 12 and 13 of the Master Guide's Table 8, built as measurement only (ruled 19 Oct 2026, late evening: "accept all" on the four decisions sent at 23:35 ET). Doctrine #2 (7-8 Nov) may still amend how the figures are used.
- **The score:** the rolling thirteen-week expectancy, by book and by regime.
- **The benchmarks:** over four quarters, the active books against Book A alone and against Book Z's static 60/40.
- **The Weekly's top:** heat, net exposure, the score and the rule-break count, above anything about the market.
- **The Monthly:** the register month prints the by-book-and-regime cut beside its overall figure.

**Branch.** `b48-scoreboard`, from chain-3's final tip, `4f004a4` (its STITCH COMPLETE commit). It merges on its own, after chain-3. Branch-only: pushed, not merged, not deployed, nothing run on the box, no unit touched.

**Rules kept.**
- The register, the grades, the trade ledgers and the store are opened read-only. `register/scoreboard.py` opens every database `mode=ro` and holds no write statement, and the gate holds both.
- No regime is computed: the regime is the stamp the order gate stored at entry.
- No order path, no decision right, nothing into a composite or the market-state object, no by-hand line, no vendor value.
- Percentages only, never dollars.
- The fixtures are synthetic: every instrument is `SYNTH`, every figure is invented, and no real position figure is in any committed file.

## Part 0: what the register actually stores for each decision

Read from `register/store.py` (the `decisions`, `rule_breaks` and `decision_packets` tables), `tools/decide.py` (`_gate_detail`), `altdata/grader.py` (`grades`), `register/heat.py`, `register/pnl.py`, `altdata/executions.py`, `altdata/benchmark.py`, the Monthly's `register_month_block` (`monthly_macro/payload.py`) and `detail_tables` (`monthly_macro/stack.py`), and the Weekly's `book_week` and `render` (`daily_cascade/weekly_stack.py`).

| Field the Card needs | Stored? | Where, and how |
|---|---|---|
| **Book** | Yes | `decisions.book`, A to D. Nullable for rows that predate Phase 5a; required of an active decision since then |
| **Setup** | Yes | `decisions.setup_id`, checked against `config/setups.yaml` at write. Nullable before EL-1 |
| **Regime stamp at entry** | **In part** | `decisions.gate_detail` (JSON), written once by the order gate at `decide.py record`: `regime.regime` (the Doctrine regime the Macro dial maps to, Transition by the crossing rule), `regime.dial_state` (the Macro dial's state), `band`, `cap_pct`, `mapping_version`. **Not stored:** the Volatility and Gamma dials and the volatile-day flag, which Appendix B's stamp names. The grade carries `spy_gamma_sign`, read at grading, not at entry |
| **Risk at entry, in the Card's percentages** | **No** | No percentage or size tier is stored. `risk_budget` is free text. `heat.view()` computes each open decision's risk in dollars from its structured size and invalidation, or an options expression's defined loss, when it is read. The share of capital is over the declared capital in `config/risk_limits.yaml`. `grades.dollars_at_risk` is the grader's figure at grading |
| **Entry** | **In part** | `decision_time`, `quantity`, `notional_usd`, `direction`. **No entry fill price** is on the decision. Portfolio Truth's average cost (`portfolio.position_avg_cost`) stands in for it at the exit (`register/pnl.py`). The executions table holds fills by instrument and time, with no decision id |
| **Exit** | Yes, for a closed decision | `exit_price`, `exit_time`, `exit_currency`, `exit_fx_to_usd`, `close_reason`. `pnl.realised()` computes the P&L from them and Portfolio Truth's quantity and cost before the exit |
| **Graded result** | Yes | `grades` (immutable; a re-grade is a new row): `r_multiple` (the thesis) and `r_multiple_ruled` (what a rule-following operator got, the expectancy's unit), `return_pct`, `mae_close_pct`, `invalidation_hit`, `operator_action`, `method_version`. The decision's EL-1 `outcome` slot is written by the grader |
| **Rule breaks** | Yes | `rule_breaks` (immutable): `session`, `kind` (nine kinds), `decision_id`, `reason` |

## What was built

| File | What |
|---|---|
| `register/scoreboard.py` | `expectancy_13w`, `benchmarks_4q` and `weekly_top`, with their line formatters, and `python -m register.scoreboard show`. One function each, read by the Weekly and the Monthly alike |
| `config/scoreboard.yaml` | The session-set values below |
| `daily_cascade/weekly_stack.py` | `produce()` stores `ed["scoreboard"]`. `render()` prints `scoreboard_html()` at the very top, above the précis, which is about the market. The block is code-written and sits outside the word budget |
| `monthly_macro/payload.py`, `monthly_macro/stack.py` | The register month carries the score and the benchmarks. Its detail table prints the thirteen-week line, the cut by regime at entry and the four-quarter line beside the overall figure, plus a book-and-regime table |
| `tools/validate_b48_scoreboard.py` | The gate, on synthetic fixtures (37/0). In the Makefile: one hundred and twenty-six code gates, one hundred and twenty-three Python. CLAUDE.md's count follows (`validate_audit_3a` 88/0) |
| CLAUDE.md | One paragraph |
| `docs/master-guide.md` and its HTML | Table 8's rows 5, 12 and 13 read "Built (b48-scoreboard), measurement only; Doctrine #2 may amend". Part 5's score bullets, Part 7's Sunday line and one Table 7b row ("measurement", not a signal, so in none of the headline counts). `check_master_guide` passes. The HTML is rebuilt with Aptos |

**How each figure is read:**
- **The score.**
  - It reads the grader's rows for decisions the operator took (TAKE or MODIFY). Every decision is a paper decision: sessions never place orders.
  - It takes one grade per decision, its latest, graded inside the thirteen weeks to the as-of and knowable at the as-of.
  - It is measured in ruled R, by `decisions.book` and by `gate_detail.regime.regime`. A decision with no stamp is named "(no regime stamp at entry)", never assigned one.
  - The unit, the window and n and the 95% interval print before the mean (`tools/cuts.py`'s `interval`).
- **Heat and net exposure.**
  - Both come from `heat.view()` over the open decisions: the register's own heat calculator, with its correlated clusters and its betas computed from stored closes. Each prints as a share of capital beside its cap.
  - Heat is Books B, C and D's open risk to invalidation, cap `heat_max_pct`.
  - Net exposure is the beta-adjusted notional of every book, cap the band top plus 15.
  - Any input the view could not find is named on the line.
- **The rule-break count.** The `rule_breaks` table: this week's sessions, and the total to date.
- **The benchmarks.**
  - The active books (B, C, D) and Book A alone are each shown as the realised P&L of their taken decisions closed in the window, over the declared capital.
  - The 60/40 is Book Z's stored `sixty_forty` marks over the same window, read from its first mark where Book Z began later.

## Every session-set value, with its reason (for Ari)

| Value | Set to | Reason |
|---|---|---|
| `score.min_n` | **10** | Below it a cell prints "accruing (n=k)". At a spread near 1R, n=10 gives a 95% interval of about ±0.6R, already wider than any edge the Doctrine expects, so a figure below that would be read as a result. The Doctrine's 30 (a regime) and 50 (a book) are thresholds for *changing* a trust level or a size tier, not for printing |
| `score.weeks` | 13 | The Card's "rolling thirteen weeks", in calendar weeks to the as-of |
| What counts as a paper decision | operator action TAKE or MODIFY | The grader also grades declined and drafted decisions, which measure the filter, not the book. The score is the book's |
| Which grade counts | the decision's latest, by its grade date | Grades are immutable and a re-grade is a new row; counting both would weigh one decision twice |
| `benchmarks.window_days` | 365 | "Four quarters" |
| The benchmarks' basis | realised P&L over the declared capital (`config/risk_limits.yaml`, 300,000 as declared; printed only as percentages) | The register's only P&L is `pnl.realised()`. A NAV by book does not exist |

## What prints "not built", and why

- **Book A alone, or the active books, while either holds an open decision.** The register stores no entry fill per decision, so an open position cannot be marked from it. The figure is withheld rather than printed on the closed decisions alone, which would flatter or damn it at random.
- **A closed decision with no exit or no Portfolio Truth cost.** "realised P&L missing for <id>: <what>", from `pnl.realised()`'s own reasons.
- **An empty register or store.** "no taken decision in Book …", "no grades table on the store yet", "no rule_breaks table on the register yet", "no Book Z mark is stored".
- **Not attempted, so named here, not printed:**
  - The regime cut uses the Doctrine regime only. The Volatility and Gamma dials and the volatile-day flag are not stamped at entry, so no cut by them exists. Stamping them is a register write path, and outside this branch.
  - The Doctrine compares the books "on a risk-adjusted basis", and the Systematic Book paper "after tax". The figures here are raw percentages: no risk adjustment or tax is computed. Doctrine #2 may say which.
  - Long against short, printed separately (D:816), is not cut.

## Files shared with chain-3 and a50-dealer-store

- **chain-3** (this branch's base):
  - CLAUDE.md: the count line and one paragraph;
  - the Makefile: one line;
  - `daily_cascade/weekly_stack.py`: `produce` and `render`;
  - `monthly_macro/payload.py` and `stack.py`: the register month;
  - `docs/master-guide.md` and its HTML: Table 8, Part 5, Part 7, Table 7b.
- **a50-dealer-store** (session A's, at `9c99a49` when read): CLAUDE.md, the Makefile, `daily_cascade/weekly_stack.py` and `tools/validate_audit_3a.py` are also changed there. Each will meet at the count line and the gate list. `weekly_stack.py` meets only if a50 also edits `produce`'s tail or `render`'s head.

## Needs you

1. **`score.min_n` = 10.** Accept, or name another.
2. **The benchmarks' basis**: realised P&L over the declared capital, withheld while a book holds an open decision. Accept, or rule how an open position is marked: an entry fill stored per decision is a register write path.
3. **The regime stamp's other dials**: stamping the Volatility and Gamma dials and the volatile-day flag at entry would let the cut follow Appendix B's full stamp. That is a write to the order gate's record, so it is yours to order.
4. **Risk-adjusted and after-tax comparison, and long against short**: for Doctrine #2.

## CI

| Round | Run | On | Result | Fix |
|---|---|---|---|---|
| 1 | 39369182460 | `6982dd4` | 135 of 136 jobs green; `validate_readability` failed: "Weekly: no '(s)', no '+-', no ISO date outside a table". The scoreboard's lines printed "open decision(s)" and ISO window dates | The lines print "1 open decision" / "3 open decisions" and dates as "1 Oct 2026"; the gate gains the same check (37/0) |
| 2 | @@RUN2@@ | @@SHA2@@ | @@RES2@@ | |
