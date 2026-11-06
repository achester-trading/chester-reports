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
| FlashAlpha vendor pull — Wednesday close | Wednesdays 16:25 ET | One JSON of FlashAlpha's settled-close SPY/QQQ exposure numbers in the operator's Drive folder chester-vendor-checks | **Retired** at chain-2's merge (20 Oct, D7) and deleted from the scheduler; the box's 16:25 vendor writer and its divergence gate took its place. Row kept for the history. Cross-check only; FlashAlpha is never a data source. Definitions: [ledgers/gex-scale-flashalpha-2026-10-09.md](ledgers/gex-scale-flashalpha-2026-10-09.md) |
| FlashAlpha vendor reconcile — Thursday morning | Thursdays 07:05 ET | A reconciliation row appended to chester-vendor-checks/flashalpha-ledger.md in Drive, emailed to the operator; rows are pasted into docs/ledgers/ by a session when convenient | **Retired** at chain-2's merge (20 Oct, D7) and deleted from the scheduler; the box's 16:25 vendor writer and its divergence gate took its place. Row kept for the history |
| AAII weekly read — Thursday | Thursdays 12:10 ET | one file a week, chester-vendor-checks/aaii/weekly/YYYY-MM-DD.csv in Drive, since 24 Oct (week ending, bull, neutral, bear, spread, source, retrieval instant, cross-check against AAII’s weekly article); the older aaii-weekly.csv is read-only history | the box’s nightly rclone sweep still pulls only aaii-weekly.csv into the inbox (the weekly/ folder is not swept yet: a gap for the merge week, docs/briefs/b102-notes.md); the writer unions it with the history; id trig_01CUGkyHUbvRXVYswkuSFVr7; first run 15 Oct 2026 |
| Alternative assets — quarterly scan | 06:30 ET on the Monday of each edition's week: Mon 4 Jan, 5 Apr, 5 Jul and 4 Oct 2027 (cloud-only, web-only) | `docs/scans/alt-assets-YYYYqN.md`, for the quarter just ended (the 4 Jan run writes `alt-assets-2026q4.md`). It reads `config/alt_asset_scan.yaml`, `config/alt_asset_gaps.yaml` (the standing search list), `config/voices_sources.yaml`, `config/source_tiers.yaml`, the two political calendars and the previous quarter's scan | **Not yet created. The operator creates it** from [`scans/PROMPT-alt-assets-quarterly.md`](scans/PROMPT-alt-assets-quarterly.md) (the text below its line). A human commits the file; `python -m altdata.alt_scan ingest` then writes the operator's calendar proposals and the draft intake entries beside it, and every Monthly run stores its figures and voices. Rulings: [`change-order-alternative-assets-quarterly-2026-10-10.md`](change-order-alternative-assets-quarterly-2026-10-10.md) §8 (AQ-7) |
| X digest triage, morning | 07:17 ET daily | Drive chester-vendor-checks/x-triage/x-triage-YYYY-MM-DD.md; the ledgers x-attention-ledger.csv, x-attention-ledger-eqmacro.csv, x-voices-ledger.csv, x-rumour-ledger.csv; a push | Reads the two morning Grok digests (A, crypto, 06:00; B, equity-vol and macro, 06:15). The box's sweep copies the ledgers in; the Digital Assets addendum reads them; the ES day-trading card reads the day's triage file. Attention, voices and rumour tracking only. Pilot, to item 50's decision point at Doctrine #2 (7-8 Nov) |
| Grok X digest, evening (the operator's automation) | 17:40 ET, Sunday to Friday | Drive chester-x-digest/x-digest-evening-YYYY-MM-DD.md (format E v2, with the Principals section) | **The operator's, not yet created** (outside Claude): blocked on 1 Nov, the operator's Grok plan allows two automations and both are taken by the morning digests; needs a third slot (a plan change) or a swap. Read by the evening X triage |
| X digest triage, evening | 18:05 ET, Sunday to Friday | Drive chester-vendor-checks/x-triage/x-triage-evening-YYYY-MM-DD.md; chapter-E rows in x-rumour-ledger.csv; a push | Planned: created 30 Oct, paused 1 Nov until its Grok input exists. For the 21:30 evening note's 'X after hours' block (item 115, Tranche B after 8 Nov, not built; the sweep does not yet pull the evening file). Report-only |
| Weekly Letter | 06:12 ET, Sundays | A private page with the charts and the PDF; the text edition Drive chester-letters/weekly-letter-YYYY-MM-DD.html; a row on the Letters index page; an email with the links; a push | Reads the Weekly's email (Sunday 05:10), last Sunday's text edition and the latest Monthly Letter. No rights: a reading of the edition, every figure copied from it. Nothing in the repo or on the box reads it. Order: [`change-order-readable-editions-2026-11-01.md`](change-order-readable-editions-2026-11-01.md) |
| Monthly Letter | 10:43 ET, the 1st of each month | The same four things, as monthly-letter-YYYY-MM.html | Reads the Monthly's email (the 1st, 07:40), the previous Monthly Letter and the latest Weekly Letter. No rights, as the Weekly Letter. First edition, October 2026, written by hand on 1 Nov; first scheduled run 1 Dec |
| ES day-trading card (DTH-1's manual edition) | 08:15 and 15:15 ET, weekdays | Drive chester-cards/card-YYYY-MM-DD-am.html and -pm.html; an email; a push | Reads the 07:00 anchor, the 09:50 open note and the 12:30 alert (email), the operator's settings and ledger in chester-cards/, the day's morning X triage file, the options vendor's levels (a cross-check, never a source) and named web pages. The operator's private tool: the system never reads a card, and Claude places no orders |
| ES Sunday map | 18:48 ET, Sundays | Drive chester-cards/map-YYYY-MM-DD.html; an email; a push | Reads the Weekly and the Weekly Letter (email), chester-cards/, the vendor's levels and named web pages. The operator's only; no rights, as the card |
| Alpha Lab Saturday brief | 07:50 ET, Saturdays | Drive chester-vendor-checks/lab-inbox/ (at most five short-term and five medium-term hypotheses) | Reads the lab's verdicts and agenda in Drive chester-lab-outbox/. Read by alpha/inbox.py, pre-registered at the file's Drive creation time. Hypotheses for the lab only; never a candidate, packet or trade |
| MSTR / MSCI event watch | 07:10 ET, weekdays 2-30 Nov (Thanksgiving skipped); the post-effective read on 1 Dec is not yet scheduled (a one-shot to be created in late November) | Drive chester-vendor-checks/mstr-msci-watch/mstr-msci-watch.csv, and a short push | Reads the index review's public notices. Read by the Digital Assets addendum's dated calendar. No rights (a read). Retires after the 1 Dec post-effective read |
