# A98 notes: the paper executor's first tranche (D43)

**Branch.** `a98-paper-executor`, from origin/main at `422ea697`. It merges after
chain-8.

**Read first, whole:** `docs/briefs/phase-4-paper-engine-assessment-2026-10.md`
(on `b90-nautilus-assessment`), then `alpha/ledger.py`, `paper.py`, `costs.py`,
`governor.py`, `altdata/ibkr_clients.py` and `altdata/sources/ibkr_portfolio.py`.

**Commits:**

| Commit | What |
|---|---|
| `17bee192` | the paste |
| `9f14e342` | Part 1, the package |
| `f4d721f9` | Part 2, the two safeguards |
| this commit | Part 3, CLAUDE.md's paragraph and these notes |

**Nothing connected and nothing was sent.** No live connection was made from the
laptop. Every fixture runs on a fake gateway.

## The dependency decision

**`ib_async`, already in `requirements.txt` (`ib_async>=1.0,<3.0`).** Gate 1's
portfolio sync uses it too. No dependency is added. It is imported lazily, so the
gate and a box without it import the package cleanly.

## What is built

### Part 1 · `paper_exec/`, outside `alpha/` (D43 b)

| File | What it does |
|---|---|
| `config.py` | the config, the state directory (`$CHESTER_STATE_DIR/paper_exec`, else `~/.chester/paper_exec`) and the mode: off, dry or send |
| `client.py` | the paper port, then the paper accounts |
| `contracts.py` | MES through the Security Master's `ibkr_conid` |
| `orders.py` | the bracket check and the size |
| `state.py` | the kill switch, the reconciliation block, the pauses and the order log |
| `reconcile.py` | the gateway against the ledger |
| `fills.py` | fills into the lab's ledger |
| `executor.py` | the pass, and the one send path |
| `__main__.py` | `status`, `run`, `clear-kill`, `resume` |

`config/paper_exec.yaml` holds its settings. `altdata/ibkr_clients.py` gains
`paper_exec: 21`, the id the assessment proposed and one no other tool uses (A93
took 27).

**The safety rules, each proved by a fixture** (`tools/validate_paper_exec.py`):

| Rule | Group | Proved |
|---|---|---|
| Paper port only | B | 4001 and 7496 refused before any connection |
| Paper account only | B | a non-DU account, a mixed list or none: disconnected and `LiveAccount` raised before any order object is built; the reason logged |
| Ships off | A | `enabled: false`: the gateway is never constructed; `status` prints "paper executor off"; `connect()` refuses on its own |
| Dry by default | C | enabled without `dry_run` is dry; nothing is built at the gateway; the log holds contract, side, size, entry, stop and target; sending needs both flags (`enabled: true`, `dry_run: false`) |
| Brackets only | D | no stop, no target, a stop on the wrong side or no entry: refused; the send path refuses one child, a lone parent, or a child not tied to its parent; a whole bracket goes as three tied orders |
| Size and contract | E | ES refused by contract; NQ refused; a missing conid skipped and named; the ceiling; a halved engine halves (3 to 1, 1 to 0); a halted lab or frozen engine sends nothing; the Doctrine's heat cap (6% of $300,000) cuts the size, open risk counted; the governor read from the ledger |
| Kill switch | F | a kill file: nothing connects; sticky after the file is removed; a clear needs the operator's reason and is recorded; a kill written mid-loop stops the very next send |

**The rest of Part 1:**

- **Fill capture, in the expectancy schema** (group G).
  - A paper fill is a `fills` row with `source = paper_exec`, the venue's order
    id and the fill's own time, and the commission as its cost.
  - A parent's fill opens the position with its bracket's stop. A child's fill
    closes it and grades it by the lab's own rule (net over notional), so a
    paper trade's `net_return` is in the backtest's unit.
  - A fill is never written twice.
- **Reconciliation at start** (group H).
  - The gateway's net positions are compared with the ledger's open paper
    positions, and every open order with the executor's order log.
  - A mismatch, such as a position the ledger does not hold or an order the
    executor did not send, stops sending and is named in state and in `status`.
  - A clean run clears the block.
- **One ordering found while writing the fixtures.** The executor's own fills
  are captured *before* reconciling. A fill since the last pass moves the
  gateway's position, and comparing first would read every fill as a mismatch
  (group G holds it).

**`alpha/ledger.py`, the paper-fill fields.**

- `source` (default `'model'`), `venue_order_id` and `venue_fill_time`: in the
  schema for a new ledger, added by `ADD COLUMN` to an older one. Its rows stay
  and read as `'model'` (group G).
- A trigger refuses a `paper_exec` row without the venue fields.
- **`fill_kind`'s CHECK is not widened.** That would mean rebuilding `fills` on
  the box's live ledger. A paper fill is recorded as `'quote'`, an executed price
  and never a modelled bar, and is told apart by `source`.

**Boundaries** (group I):

- the order calls sit in the one send path (`executor._send`, and `bracketOrder`
  in `run`), held by AST;
- `alpha/` never imports the package;
- client id 21 is unique;
- no unit or timer.

**The deny list.** CLAUDE.md requires a new order entry point to arrive already
denied, so `.claude/settings.json` denies `paper_exec run`, `clear-kill` and
`resume`. `tools/validate_deploy.py` gains the matching must-deny cases under
"order placement"; additions only.

### Part 2 · the two D43 safeguards

**(a) The edge-decay pause, `paper_exec/pause.py`** (group J).

- **The sample:** an engine's last 20 closed paper trades.
- **The backtest fields:** `engines.validated_metrics.expectancy` (the harness's
  expectancy per trade after costs, `alpha/validate.py`), `.sd` and
  `.n_signals`.
- **The SE is the difference's:** √(sd_paper²/20 + (sd/√n_signals)²). Neither
  sample's noise is ignored, and it reduces to the assessment's s/√N when the
  backtest's own error is small.
- **The trip:** z ≤ −2.0 at n ≥ 20. Below 20 it reads "accruing (n=k)".
- **What a trip does:** writes the pause and its figures to state, stops that
  engine's sends, and prints in `status`.
- **It never clears itself.** Twenty good trades later it is still paused.
  Resuming is the operator's (`python -m paper_exec resume --engine X --reason`,
  denied to sessions), and the resume is recorded.
- **The fixture's arithmetic:** mean −0.0094 against +0.0040, SE about 0.0025,
  z about −5.3.

**(b) "Why this could fail"** (group K).

- **Why it is split in two.** `alpha/` may import no network library
  (`validate_alpha_no_orders`), so the call cannot live in the lab's
  registration path itself. It is built as the assessment's section 5 placed it.
- **The pure half, `alpha/critique.py`:**
  - the input whitelist (the hypothesis's text and rule);
  - `RESULT_FIELDS` named, with a leak check;
  - the closed vocabulary of seven modes, two to five per critique;
  - `ingest()` into a new write-once table, `hypothesis_critiques`. This is
    beyond the paste's "fill fields only", and it is the place "beside the
    hypothesis".
- **The call, `alpha_proposer/critic.py`:**
  - one call per uncritiqued hypothesis, through `model_meter` (report
    `alpha_critic`, the hypothesis id as section);
  - budget `config/alpha.yaml` `critic.daily_call_budget`, **0 shipped**;
  - written as the proposer writes, through `out.py` only: an inbox file with its
    manifest line;
  - it runs after the proposer in `python -m alpha_proposer`. There is no new
    timer.
- **Storage.** The nightly ingestion (`alpha/inbox.py`) checks the proposer's
  sha256 and stores the critique.
- **What the gate proves:**
  - the inputs carry no result field: a failed hypothesis's status and result
    never reach the call;
  - zero budget means no call;
  - the day's calls count against the budget;
  - stored once, never updated, a second one refused;
  - the vocabulary;
  - the metering.
- **Timing.** A hypothesis can run the night it is registered, before the critic
  writes, so a critique can post-date its run. The partition still holds: the
  critic never sees the result.

## Gates

Each ran one at a time, in the foreground.

| Gate | Result |
|---|---|
| `validate_paper_exec` | 70/0 (one Makefile line; count 136/133) |
| `validate_alpha` | 257/0 |
| `validate_alpha_no_orders` | 74/0 |
| `validate_alpha_proposer` | 44/0 |
| `validate_alpha_lab_3` | 65/0 |
| `validate_alpha_lab_4` | 65/0 |
| `validate_secrets` | 58/0 |
| `validate_deploy` | 154/0 (no new unit) |
| `check_registry` | OK |
| `validate_audit_3a` | 88/0 |
| `check_library` | 0 failures |

**Merge-order recount.** A92, A93, A96, A97 and A98 each add one gate on their
own branches, so the last to merge sets 140/137. A93 also adds a line to
`altdata/ibkr_clients.py` (`bars: 27`). The two lines sit apart, so the merge
takes both.

## The box steps after the merge

1. **The conid, as A93.**
   - The Security Master holds no MES entry today, so the first run skips MES
     and names it.
   - The operator gives a session MES's front-month contract (its conid, read in
     the Gateway or TWS), and a session paste adds the entry with
     `ibkr_conid`, with its SM id.
   - MES rolls quarterly, so the conid changes at each roll. The roll rule is
     the next tranche's.
2. **The first dry run.** The paper Gateway must be up on 4002.
   - In `config/paper_exec.yaml` the operator sets `enabled: true` and leaves
     `dry_run: true`.
   - Then, on the box:

     ```
     python -m paper_exec status
     python -m paper_exec run
     ```

     `status` should show "paper executor dry". `run` connects read-only, checks
     the DU account, captures nothing and reconciles. It builds and logs
     whatever the lab's pending MES signals ask, into `orders.jsonl` in the state
     directory, and sends nothing.
   - Today the lab emits no MES signal with an entry price, so the first dry run
     should log no bracket. The intents' source is the next tranche's.
3. **To send.** The operator sets `dry_run: false`, by hand: both flags. A
   session never sets either. The status line then reads "sending to the paper
   account".
4. **The kill and the resume.**
   - `touch ~/.chester/paper_exec/kill` stops sending at once.
   - `python -m paper_exec clear-kill --reason "..."` clears it.
   - `python -m paper_exec resume --engine X --reason "..."` lifts a decay
     pause.

## What the next tranche holds

- **The loop and its timer.** A unit, its memory cap as a percentage of the box,
  and `DEPLOY_TIMERS` held back until a witnessed clean start, as the Gateway's
  is. The pass is called on a cadence, and resting brackets are tracked to their
  fills.
- **The intents' source.** The engines' MES signals with an entry price. Then
  the Book C handoff: the Doctrine's 1000-report right to confirm or cancel the
  07:00 drafts, with paper fills read back to the register's predicted
  expectancy (Gate 2's test).
- **The futures model.** MES's contract chain, expiry calendar and roll rule,
  from `altdata/es_block.py`'s CME rule.
- **The implementation-shortfall line.** Each paper fill against the lab's
  modelled fill for the same signal, and the cost pause at +50% over 20 fills
  (the assessment's section 4).
- **The pause's pre-registration.** `config/alpha_decay.yaml`, its sha256 quoted
  by each engine's roster entry. This tranche keeps N and z in
  `config/paper_exec.yaml`.
- **The critic's grading.** The share of failures whose mode was listed in
  advance, in the quarterly page, and the batch schema's v2 field on the
  proposer's own hypotheses.
