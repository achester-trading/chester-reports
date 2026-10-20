# Change order — Signal triage Batch 13 (item 61): relative options volume

| | |
|---|---|
| File | `docs/change-order-signal-triage-batch-13-2026-10-20.md` |
| Status | **RULED 20 Oct 2026** ("accept all", decisions D1 to D5, §4). |
| Encoding | Batch 13 of Post-Freeze Amendment #4. It was sent as "candidate item 59 (a Batch 11 follow-on)", but item 59 is now Batch 12's (bank stress, filed today), so it is filed as **item 61**. Work IDs: OS-12a to OS-12d (it joins the opening setup's blocks). |
| Built by | Session A (paste A54), after A53, on its own branch `a54-relative-volume`. It merges after chain-4. |

---

## 1. The check, as asked: is it already built?

No block prints a name's total options volume against its own trailing average:
- **OS-4** prints the index put share of volume, against its own history.
- **OS-5** prints the single-name put share of volume, as a z against each name's own history.
- **OS-9** prints the OI change as a share of the session's volume (Batch 11 item 58), and sees open interest only the next day.
- **OS-10**, the closest, ranks the week's ten most active names by **absolute** options volume, in the Weekly.

So this is a new item, placed beside OS-10. It adds same-day activity, which OS-9 cannot see until the next morning. The data is already stored: `chain.options_volume` per name per session from the box's own chains, and the put share of volume (`chain.put_share_volume`). Together these give the call and put split. SPX and SPCX take their volume from their Massive chains, as OS-10 does. No new feed is needed.

## 2. The item

**The idea.** Flag names whose total options volume today is unusually high against their own recent history. This shows where attention is arriving before price or open interest confirm it.

**The metric (OS-12a).** For each of the 17 chain names: the session's total options volume divided by its trailing 20-session average, split into calls and puts. It uses the settled end-of-day volume from the box's own chains. Until a name has 20 stored sessions, it prints "provisional (n sessions)".

**The flag (OS-12b).**
- **Threshold:** at least 1.5 times the average. This is provisional and session-set, frozen for 30 days, then reviewed.
- **Beside each flagged name:** the put/call split, and the day's change in front-month ATM IV (OS-10's method).
- **Label:** "volume, no side". No side is ever inferred.
- **Earnings:** a report within 10 sessions is shown (OS-11).

**What became of the volume (D4).** Whether the flagged volume became new positions or was churn is only knowable the next morning, when OS-9 sees the open interest. So it prints then, in two places:
- the 07:00 anchor's OS-9 table tags each name flagged the day before ("volume flag yesterday");
- the next close's block prints one line: "yesterday's flagged names: k became OI builds, m did not".

**The ledger (OS-12c).** Pre-registered before any scoring code, and never edited.
- **The comparison:** each flagged name-day against the next 5 sessions' absolute move and the change in implied vol, against the same name's unflagged days.
- **The aim:** to test whether a volume spike leads movement in our names.
- **The pass rule:** stated in the registration.
- **Rights:** the flag earns a place in any score only if the ledger supports it.

**History (D5, OS-12d).** The D4 flat-file backfill (Batch 11, `tools/massive_flatfiles_backfill.py`) is extended to also store each name's daily total, call and put volume, under its flat-file source.
- **Read apart:** its rows are kept apart from the captured rows, under the same rule as A48's pre-registered agreement. Volume's tolerance is session-set and stated.
- **Use:** once Ari has added the flat-file keys and run the backfill, the ledger's first edition can read two years. Until then it accrues from the captures.

**Placement.**
- **The 16:45 close:** flagged names only, five rows at most, as a table. It is data, so it is outside the word budget.
- **The 07:00 anchor:** the OS-9 tag.
- **The Weekly:** the count of flags per name, and the ledger to date.

**Rights.** Report only. No score, no composite, no weights, and no side inferred.

**December note.** If the universe widens in December, this flag becomes more useful: a spike in a name outside today's list is exactly what it would be for.

## 3. Work

| Task | Description | Session hours (order's estimate) |
|---|---|---|
| OS-12a | The metric, from stored volume, with the "provisional (n)" label | 0.75 |
| OS-12b | The flag, the close's table, the anchor's OS-9 tag and the next close's line | 1 |
| OS-12c | The ledger's pre-registration and first edition (captures; flat files once run) | 0.75 |
| OS-12d | The flat-file backfill's volume rows | 0.5 |

## 4. Decisions, ruled 20 Oct 2026 ("accept all")

- **D1:** a new item (61), not an amendment. No OS block prints volume against each name's own trailing average. It sits beside OS-10.
- **D2:** a 1.5× threshold against the 20-session average, provisional and frozen for 30 days.
- **D3:** the volume-spike ledger is pre-registered.
- **D4:** whether the volume became open interest prints the next morning (the OS-9 tag) and in the next close's line, because it cannot be known at 16:45 on the flag day.
- **D5:** the flat-file backfill also stores daily volume, read apart from the captures, so the ledger can use two years once Ari runs it.
