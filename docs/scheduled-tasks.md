# Scheduled tasks (chat-side)

A register of the scheduled tasks that run on the chat side, in the scheduler,
rather than on the box. One row each. Started 6 Oct 2026 under L-1.

**What this register is for.** The box's schedule is declared in
`deploy/systemd/` and enabled from `DEPLOY_TIMERS` in
`scripts/deploy_remote.sh`. These tasks are not declared anywhere in the
repository, so this file is where they are written down. Each row gives what
the task delivers and where its output lands.

**The prompts live in the scheduler, not here.** This register records what each
task delivers and where it lands. It does not hold a copy of the prompt, so the
two cannot drift.

**None of these tasks has decision rights.** Each one reads and reports. None
writes to the register, changes a report's configuration, edits a paper, or
runs anything on the box. Whatever a task finds, a human acts on it through the
normal channels (a change order, a commit, an operator's register write).

All times are Eastern.

| Task | When (ET) | Delivers | Lands in | Notes |
|---|---|---|---|---|
| JPM Guide to the Markets — quarterly read | 06:56, the 6th of Jan, Apr, Jul and Oct | The quarter's read of J.P. Morgan's *Guide to the Markets* | `docs/scans/jpm-gtm-YYYYqN.md` (e.g. [`jpm-gtm-2026q4.md`](scans/jpm-gtm-2026q4.md)) | Rulings on what it reads and how: [`change-order-jpm-gtm-2026-10-03.md`](change-order-jpm-gtm-2026-10-03.md) |
| Monthly signal scan | 06:57, the 25th of each month | A monthly scan for signals | *to confirm* | — |
| AI-risk consensus-drift scan | the 20th of even months (time *to confirm*) | A read of drift in consensus on AI risk | *to confirm* | — |
| Saturday crypto mechanism scan | Saturdays (time *to confirm*) | A weekly read of crypto mechanisms | *to confirm* | **Interim, due to retire.** Remove this row when it retires |
| Reading-shelf publication watch | 06:58, the 12th and 27th of each month | A watch for new publications on the reading shelf | *to confirm* | — |

A cell marked *to confirm* has not been checked against the scheduler. Fill it
from the scheduler's own entry rather than from memory.
