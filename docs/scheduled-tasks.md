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

Times are Eastern unless the scheduler holds the task in UTC, in which case
the UTC time is given with its Eastern equivalent in summer and winter.

**Where the output lands.** Every task's output lands in its own session in the
Claude app. Nothing reaches the repository unless a human commits it. The
"Delivers" column names the file a task produces where it produces one, at the
path it lands at once committed.

| Task | When | Delivers | Notes |
|---|---|---|---|
| JPM Guide to the Markets — quarterly read | 06:56 ET, the 6th of Jan, Apr, Jul and Oct | `docs/scans/jpm-gtm-YYYYqN.md` (e.g. [`jpm-gtm-2026q4.md`](scans/jpm-gtm-2026q4.md)) | Last ran 6 Oct 2026, a second read of the 4Q edition. Rulings: [`change-order-jpm-gtm-2026-10-03.md`](change-order-jpm-gtm-2026-10-03.md) |
| Monthly signal scan | 06:57 ET, the 25th of each month | `docs/scans/signal-scan-YYYY-MM.md` | Signal-triage batch 3, decision 7 |
| AI-risk consensus drift scan (pre-refresh) | 13:00 UTC on the 20th of even months (09:00 ET in summer, 08:00 ET in winter) | A read of drift in consensus on AI risk | Folds into the monthly signal scan once that is stable |
| Weekly crypto tech scan — Pearl (PRL) + new mechanisms | Saturdays 12:00 UTC (08:00 ET in summer, 07:00 ET in winter) | A weekly read of Pearl (PRL) and new crypto mechanisms | **Interim, due to retire.** Remove this row when it retires |
| Publication watch — reading shelf | 06:58 ET, the 12th and 27th of each month | A watch for new publications on the reading shelf | — |
