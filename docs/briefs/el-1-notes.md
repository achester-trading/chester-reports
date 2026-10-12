# EL-1 — the packet, Red Team v0, the setup catalogue, the refusal: build notes (12 Oct 2026)

Branch `el-1-packets`, from `origin/main` at `785fa19`, not merged. Built against
`docs/change-order-enterprise-layer-2026-09-27.md`:
- §3.1 (the packet fields);
- R-5 (Red Team's objective);
- §3.6 (the experiment's fields and the fixed kill criterion);
- §8 row EL-1;

and against `docs/briefs/enterprise-layer-spec-2026-09-27.md` §VII (the
Recommendation/Decision and Outcome objects) and §XI (falsifiability). The order
and the spec are not edited. Paper only: nothing here places or routes an order.
No register write was made. `decide.py record` and `set-status` stay the
operator's: this branch changes what a packet must contain, never who records it.

**What was already on main.** P5-B built §3.1's six columns:
- `setup_id`, `engine_id`, `horizon_alignment`, `review_changed`, `falsifiers`,
  `counter_thesis`;
- the alignment computed at entry;
- a refusal of DECISION_OK without falsifiers, invalidation and counter-thesis;
- a first `config/setups.yaml`.

This branch builds on that rather than beside it.

## What was built

**1. The packet fields** (`register/store.py`). These are added as nullable
columns through the register's existing migration, an ALTER on construction:
`mechanism`, `falsifier_date`, `expected_return`, `expected_downside`,
`entry_condition`, `risk_budget`, `benchmark`, `red_team`,
`red_team_review_minutes`, and the **outcome slot** (`outcome`, `outcome_at`).
The outcome slot is empty at entry and written by the grader, never by the
packet's author.

With the columns already there, the packet is the brief's list in full, as
`ENTRY_FIELDS`:
- thesis and mechanism;
- the falsifier (≥ 1, measurable) and its date;
- setup_id;
- expected return and downside;
- entry condition;
- invalidation;
- size (size, quantity or notional) and risk budget;
- horizon and benchmark;
- the Red Team line and its review time;
- the counter-thesis.

The decision timestamp (`decision_time`) and the `review_changed` slot already
existed. Every earlier row reads NULL, "not recorded".

**2. Red Team v0 at write time.** The packet is refused as DECISION_OK unless:
- `red_team` names the cheapest way the thesis could be wrong;
- `red_team_review_minutes` states the review time to check it, as a positive
  whole number.

The refusal quotes the rule, `RED_TEAM_RULE`: "Red Team v0 (R-5): a packet names
the cheapest way the conclusion could be wrong, at a stated cost in review time".
Those are R-5's own words, and the gate finds them in the filed order.

**3. `config/setups.yaml`, the catalogue.**
- **Kept:** every earlier family (packets cite them).
- **Each family is now an experiment (§3.6):** its mechanism in one paragraph;
  its base rate, cited by id (`baserate.*` or `claim:*`, the register's own
  citation rule) or "not yet"; the claimed edge; `target_n` 40; `kill: fixed`;
  and a status.
- **The kill criterion** is stated once, word for word from §3.6.
- **Seeded from the Weekly's tells**, drafted from the signal-triage register and
  the Dealer's Hand: `b_style_regime_pair` (SR-1), `b_consumer_rs_tell` (SR-5),
  and the dealer-regime setups `c_pin_fade` and `c_negative_gamma_continuation`.
- **All fifteen families are marked `stub`** for Doctrine #2.
- **No base rate is stored for any setup,** so every one reads "not yet".

**4. The write-time refusal, logged.**
- **A new immutable table, `packet_refusals`,** with rule, reason, source and
  payload. Its triggers refuse update and delete.
- **`Register.record()` logs before it raises** for:
  - an unknown `setup_id` (rule `unknown_setup`), refused on any write, draft
    included, because a packet keyed to a family the catalogue lacks can never
    be graded;
  - an incomplete DECISION_OK (rule `incomplete_packet`), naming every missing
    field in reading order.
- **`set_status`'s in-place promotion** is refused and logged the same way.
- **`decide.py record` and `set-status`** run the same rule (`packet_faults`)
  before the gate, print the reason, and log it on a real run. A dry run logs
  nothing.
- **`--setup` is no longer an argparse `choices` list:** an unknown setup is now
  a logged refusal, not a usage error with no record.
- **The blocklist is unchanged and first.** A Brookfield-complex instrument is
  refused before any other check, in Python and by the SQLite trigger, and the
  attempt is logged to `blocked_attempts`.
- **New `decide.py record` flags:** `--mechanism`, `--falsifier-date`,
  `--expected-return`, `--expected-downside`, `--entry-condition`,
  `--risk-budget`, `--benchmark`, `--red-team`, `--red-team-minutes`.
- **`set-status`** carries them forward. `show` reads "not recorded" for each on
  an earlier row.

**5. The gate:** `tools/validate_packets.py`, 37 checks, in the Makefile's list,
on temporary registers only. It shows:
- a complete packet passes, with the outcome slot empty;
- each of the fifteen removable fields, removed in turn, refuses, names itself
  and logs one refusal;
- both Red Team parts are required, with bad review times refused and the rule
  quoted;
- the falsifier is measurable and dated, the date not before the decision;
- the blocklist refuses first, and the raw-SQL trigger holds;
- an unknown setup refuses and is logged;
- the catalogue's fields and the fixed kill criterion, verbatim, with no earlier
  family removed;
- `decide.py` refuses with the reason and logs it;
- a pre-EL-1 register opens with its rows intact and every new field NULL;
- the refusal log is immutable.

**The fixtures.** Gates that record an active decision for other reasons (the
order gate, the grader, the Weekly, the register) now pass a complete packet from
`tools/packet_fixture.py`. They would otherwise be refused for a reason unrelated
to what they test.

**Gates re-run here:**

| Gate | Result |
|---|---|
| `validate_packets` | 37/0 |
| `validate_register` | 171/0 (2 skipped, as before) |
| `validate_enforce` | 48/0 |
| `validate_grader` | 62/0 |
| `validate_weekly_stack` | 68/0 |
| `validate_benchmark` | 24/0 |
| `validate_weekly_complete` | 56/0 |
| `validate_deploy` | 118/0 |
| `validate_gates` | 31/0 |

## What waits, and for what

- **Doctrine #2 (7–8 Nov):** the operator completes the fifteen stubs —
  mechanism, base rate (by id where one is stored), claimed edge — and sets each
  to `complete`.
- **The outcome slot's writer.** The grader writes `outcome`/`outcome_at` when a
  decision resolves (the spec's Outcome object). That writer is EL-8's or the
  grader's, not built here.
- **Drafts already on the register, and AQ-6's.** The thesis register writes
  drafts with no Red Team line or decision object. A draft records fine, but it
  becomes DECISION_OK only through a new, complete packet: `set-status` refuses
  to promote it, and logs that.
- **EL-2 (the roll-up)** reads the fields this branch fixes; nothing in it is
  built here.

## Choices made for the operator to overrule

1. **The brief's list over §3.1's minimum.** §3.1 says "Red Team v0 is these
   three required fields and nothing more" (falsifiers, counter-thesis,
   invalidation). The brief makes the whole decision object required at
   DECISION_OK and adds the two-part Red Team line (R-5's objective). Built as
   the brief says, with §3.1's three kept among them.
2. **The rule binds at DECISION_OK, not at every write.** A draft may be
   incomplete: abstentions, engines' proposals, gate-held and blocked requests.
   That is §3.1's wording ("refuses DECISION_OK without …"), and AQ-6's draft
   writer depends on it. An unknown setup_id is the exception, refused on any
   write.
3. **"Measurable" is checked mechanically.** At least one falsifier must name a
   level, count or date (a digit), and the falsifier carries a date not before
   the decision. Whether it is the right measure stays a human question.
4. **Size may come from `size`, `quantity` or `notional`;** the risk budget is
   its own required field.
5. **The review time is whole minutes.**

## Needs you

1. Make the whole decision object and the two-part Red Team line required at DECISION_OK (the brief), beyond §3.1's "these three required fields and nothing more"? yes / no
2. Keep the rule binding at DECISION_OK only, so drafts (abstentions, engines' and AQ-6's proposals) may be incomplete? yes / no
3. Complete the fifteen setup stubs at Doctrine #2 (mechanism, base rate by id, claimed edge), including whether the fixed kill criterion applies as written to `d_tail_hedge` (a budgeted insurance line) and to Book A's allocation setups? yes / no
4. Accept the mechanical "measurable" check (a falsifier names a digit, dated no earlier than the decision)? yes / no
5. Merge order, inside windows: this branch to main on its own (AQ-6's draft writer is unaffected; promoting its drafts needs a complete packet)? yes / no
