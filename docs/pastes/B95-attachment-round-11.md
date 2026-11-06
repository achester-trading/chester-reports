# Change order — signal triage, round 11 (item 115; Batch 21, provisional)

| | |
|---|---|
| **File** | `docs/change-order-signal-triage-batch-21-2026-10-30.md` |
| **Status** | RULED 30 Oct 2026 (in chat); filing pending |
| **Encoding** | Batch 21 of Post-Freeze Amendment #4, provisional (Batch 20 = items 111–114). If Batch 21 or item 115 is taken, apply the collision fix used for Batches 15–19. SR number assigned at the audit that places this batch. |
| **Precedence** | Below Part 26, the Enterprise Layer order and the dated change-orders edition; equal to the other Amendment #4 batches. |
| **Totals** | ≈ 2.5 h of sessions · no by-hand work (the Grok automation and the chat-side triage run themselves) |

REPORT_OK-class: no path to DECISION_BLOCKED, no composite or T&B weight change, no regime tag. X items keep the rights item 50 gave them: attention and rumour-tracking only, never measurement.

## 115 · The evening X read — AMEND item 50

**Origin.** The operator's request (30 Oct): news and rumours that break after the close should reach the evening report the same day, not the next morning.

**What exists from 30 Oct (chat-side, outside the repo).**
- A Grok automation at 17:40 ET, daily except Saturday. It searches X for posts since 06:00 ET and writes `x-digest-evening-YYYY-MM-DD.md` to the Drive folder `chester-x-digest` (format "E v1").
- A chat-side scheduled task at 18:05 ET. It triages that digest (incentive tags, a credibility read per rumour, up to four primary-source checks), adds chapter-E rows to the shared rumour ledger, and writes `x-triage-evening-YYYY-MM-DD.md` to `chester-vendor-checks/x-triage`, with the headings Quality / What broke / Rumours / Verification / Voices / Ruling. It also pushes a summary to the operator.

**Decision (the box piece).**
- **(a) Inbox.** The nightly sweep pulls the day's `x-triage-evening-YYYY-MM-DD.md` into `~/chester-data/inbox/x-triage/`, the same way the AAII file arrives. A pull at about 18:30 ET (or inside the evening note's own run) is needed so the 21:30 note sees it the same day: the build states which, and adds no new unit unless it must.
- **(b) The block.** An "X after hours" block in the 21:30 evening note (Sun–Thu):
  - up to five "What broke" lines, each with its posted time in ET, the outlet or handle type, and its incentive tag;
  - the rumours, each labelled *unverified*, *confirmed* or *denied*, with the primary source when resolved;
  - one line of verification results.
  - Text is copied from the triage file. The note's model never paraphrases it into a market claim, and the numeral audit treats every figure in the block as quoted, not as the system's measure.
  - No file: "X evening read not available". A file older than today prints nothing.
- **(c) Rights.** The block is report-only. It changes no regime, flag, score or decision. A rumour never enters a ledger of the system's own, other than the rumour ledger, whose base rates are what Audit #5 reads.
- **(d) Gate.** A fixtures-only gate:
  - the block renders from a synthetic triage file;
  - a stale or absent file prints the stated line;
  - no figure in the block reaches the numeral audit's allowed set as a measure;
  - no person's name passes (handles only, as in the file).
- **Hours:** 2.5. **Placement:** Tranche B, after 8 Nov; Audit #5 places it.

## Sign-off

| Date / time (ET) | Item | Ruling as stated |
|---|---|---|
| 30 Oct 2026, 08:06 | 115 (the evening scan and the evening-note block) | "Yes" |
