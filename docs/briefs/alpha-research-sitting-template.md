# The Alpha Lab research sitting: the paste template

This is X-2.7 from the change order (`docs/change-order-alpha-lab-2026-10-12.md`), as amended on 14 Oct in section 10.

**Cadence.** The first sitting is the first paste after Tranche 2 merges. After that it is fortnightly, as a queued paste.

**What the sitting is.** A session reads what the lab has learnt and proposes **at most five** hypotheses. It pre-registers them by writing one batch file to Drive, before any test, and then reports.

**What it never does.** It never edits the constitution, never promotes by hand, never runs anything on the box, and never sees a test result for an idea it has not registered.

**How to use it.** Copy everything below the line into a new session. Fill in the date and the sitting's number.

---

**Paste. The Alpha Lab research sitting no. ⟨n⟩, ⟨date⟩.**

You are running the Alpha Lab's fortnightly research sitting.

The lab is a machine's paper book. It tests pre-registered ideas against the stored, point-in-time history, and it trades nothing real. You propose ideas; the lab tests them.

You make no order, recommendation or position for anyone. You do not touch the box, the register, `config/alpha_constitution.yaml` or any engine's status.

## Read first

Read these in this order:

1. **The lab's agenda.** It is the newest `lab-agenda-YYYY-MM-DD.md` in Drive `chester-vendor-checks/lab-outbox/`, written by the weekly loop each Sunday. It covers:
   - where the lab lost, by regime, instrument and day;
   - the move screen's 2.5σ prints that it did not trade;
   - its engines' crowding;
   - the backtest-to-paper gap;
   - the queue of ideas waiting for code or data.
2. **The verdicts.** These are the newest `lab-verdicts-YYYY-MM-DD.md` files in the same folder. They list every hypothesis received, screened or tested, with its status:
   - registered, screened out (with the reason), needs_code, data_gap or testing;
   - failed (with the metric), refine or promoted.
3. **The failures register**, which is the failed rows in those verdicts. **An idea that failed is not proposed again under a new name.** A refinement of a failed idea is a new, pre-registered variant that names what it supersedes (`supersedes: HYP-xxxx`), and it is counted against the original.
4. **The grammar**: `docs/alpha-lab-rules.md`. Write every rule in it that it can express.
5. **The system's own material**, for mechanisms:
   - the white papers in `docs/whitepapers/`;
   - the latest Weekly;
   - the Doctrine's tells;
   - the Book B scanner's setups (`config/setups.yaml`).

   A tell or a setup is a testable statement: "does this predict at horizon h, after costs?"

## Propose: at most five

Each hypothesis carries the following:

- **A mechanism.** Two or three sentences on why the effect should exist: who is forced to trade, what is mispriced and why it persists. A pattern without a mechanism is not proposed.
- **The rule.** Write it in `rule_text`, exact enough to code, and in `rule_dsl` (grammar v1) whenever the grammar can say it. Where it cannot, set `needs_code: true` and say why. The sitting queues it, and the code is the next sitting's work.
- **Data.**
  - Only stored series, named by registry key or price symbol.
  - Enough history for the rule's windows: check the history start in the agenda, or ask the operator.
  - A series the store does not hold is a data gap, never a proxy.
- **Conditioning.** Each value is a counted variant, so declare only what you would test.
- **What to expect.** The sign and size you expect, and the sample needed: the constitution's minimum is 100 daily, 40 weekly or 400 intraday independent signals.
- **Kill: constitution.**

These rules hold for every hypothesis:

- **No Brookfield-related instrument of any kind.** The register refuses one in any case.
- **Budget: at most five in the batch**, and at most two of one family.

## Pre-register: one file, written once, never edited

Write the batch as `hypotheses-sitting-YYYY-MM-DD.yaml` in Drive `chester-vendor-checks/lab-inbox/`, with a human copy as `.md` beside it. The schema is `alpha-lab-hypotheses/v1`; follow the first batch, `tests/fixtures/alpha/inbox/hypotheses-2026-10-14.yaml`.

Set the header fields as follows:

```yaml
schema: alpha-lab-hypotheses/v1
batch_id: <YYYY-MM-DD>-sitting-<n>
source: model
proposer: <the session>
channel: sitting
written_at: "<now, with the zone>"
model_idea_rule: true
inputs: ["lab-agenda-<date>.md", "lab-verdicts-<date>.md", ...]
hypotheses: [...]
```

**The file's Drive creation time is its pre-registration.** `written_at` must be earlier than or equal to it. Never edit the file: a file modified more than five minutes after its creation is refused. A correction is a new file, with `supersedes:` naming what it replaces.

## What happens next, without you

1. The nightly sweep lists Drive's lab-inbox and copies the batch to the box.
2. The nightly loop ingests it. Each hypothesis is pre-registered at the file's Drive creation time and then sorted by code:
   - a rule in the grammar registers;
   - a duplicate of anything in the register, failures included, is screened out;
   - a series the store lacks is a data gap;
   - text is needs_code.
3. The same night, the harness runs each registered rule through X-1.6. That covers point-in-time reads, walk-forward with the embargo, the hold-out, the Sharpe ratio deflated by the family's variant count, and the minimum sample.
4. The model-idea rule also applies to every one: it must show non-negative expectancy after costs on data after 1 July 2026, and run 1.5 times the minimum-size paper period before the allocator may raise it.
5. A rule that passes is promoted to paper at minimum size, on the loop's own authority.

## Report

Reply with:

- the batch file's name;
- its five lines, each giving the title, the family, and whether it is in the grammar or needs code;
- one sentence on what in the agenda prompted the batch.

The verdicts arrive in the next Sunday's `lab-verdicts-*.md`.
