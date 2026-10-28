# Change order — Signal triage Batch 18 (item 98): the 23-hour equity session

| | |
|---|---|
| File | `docs/change-order-signal-triage-batch-18-2026-10-28.md` |
| Status | **RULED in chat** 28 Oct 2026, pending the operator's accept (given with paste B81). Filed 28 Oct 2026 by paste B81 with filing amendments K1 to K4 (§0). The paste is kept verbatim at `docs/pastes/B81.md`. |
| Encoding | Batch 18 of Post-Freeze Amendment #4. Batch 17 holds items 92–97 (paste A81, branch `a81-batch-17-filing`, unmerged), so this is item 98, its work IDs 98(a) to 98(c). Register number provisional, SR-68, placed by Audit #5 (K2). |
| Precedence | Below Part 26, the Enterprise Layer order and the dated change-orders edition; equal to the other Amendment #4 batches. |
| Supersedes | Nothing. |
| Totals | ≈ 1.5 session-evenings: one for 98(a), half for 98(b); 98(c) folded into the price migration (B68). No by-hand line. |
| Time-critical | Before the session's first night, Sunday 6 December 2026, if it starts on time (K1). Nothing for 1 Nov or 8 Nov. |
| Built by | Nothing yet. After Doctrine #2 (7–8 Nov 2026). |

---

## 0. Filing amendments (paste B81, 28 Oct 2026)

- **K1, the facts, read on 28 Oct 2026.** The paste asked for each fact to be read from the exchanges' own notices and the SEC's pages before filing. Results:

  | Fact as reported | Verdict | Source, date read |
  |---|---|---|
  | Nasdaq and NYSE Arca plan a night session, about 21:00–04:00 ET, Sunday to Thursday nights, so equities trade about 23 hours a day, 5 days a week | **Verified.** Nasdaq: the Night Session runs 21:00 to 04:00 ET the next calendar day, Sunday through Thursday, provided the next calendar day is a business day; the Day Session runs 04:00–20:00; the week runs Sunday 21:00 to Friday 20:00. NYSE Arca: a fourth session, the Overnight Session, 21:00 to 04:00, Sunday through Thursday, with a pause 20:00–21:00. Both say 23 hours a day, five days a week | SEC Release 34-105199 (Nasdaq, order approving SR-NASDAQ-2025-109), Federal Register 15 Apr 2026, govinfo.gov; NYSE Extended-Hours Trading FAQ v4.0 (August 2026), nyse.com; SEC Release 34-106378 (NYSE Arca, SR-NYSEARCA-2026-94, 15 Sep 2026), sec.gov. All read 28 Oct 2026 |
  | Target start Sunday 6 December 2026, subject to SEC approval | **Verified, corrected.** The core rule is approved for Nasdaq (34-105199, 10 Apr 2026). The start is conditional on more than approval: Nasdaq "would not commence operation of the Night Session unless the Equity Data Plans" confirm readiness, and must first file a rule change confirming it (else remove the rules within 18 months). NYSE Arca: "Subject to SEC approvals, the availability of the Securities Information Processors (SIPs), and the implementation of the Depository Trust and Clearing Corporation's (DTCC) modernization efforts, NYSE Arca plans to launch extended-hours trading on December 6, 2026"; its release 34-106378 says it "intends to offer" the session on 6 Dec 2026. Read as: target 6 Dec 2026, conditional on SIP readiness, DTCC and a confirming filing | As above |
  | The official opening and closing crosses are unchanged | **Verified.** Nasdaq: the Day Session "will continue to feature both the Nasdaq Opening Cross and the Nasdaq Closing Cross"; cross order types are not available at night. NYSE Arca continues to publish its official closing price after the Core Closing Auction at 16:00. Neither night session has an opening auction at 21:00; Arca's Early Session keeps its 04:00 auction | 34-105199; NYSE FAQ v4.0 |
  | Trades between 21:00 and midnight ET carry the next calendar day's trade date | **Verified for NYSE Arca, corrected in scope.** Trades 21:00–24:00 carry the next calendar day's trade date and go to DTCC with that clearing date; trades 00:00–04:00 carry the same calendar day's trade date. Nasdaq's approval order does not address trade dates (it records SIFMA raising trade-date harmonisation as a wider question); Nasdaq's rule on it is **unverified (reported 28 Oct)**: secondary summaries state the same rule, not read from a Nasdaq notice | NYSE FAQ v4.0; 34-105199; nasdaq.com's 23/5 hub timed out on two reads |
  | SIP/consolidated tape and DTCC clearing support overnight | **What the sources say.** SIP: Nasdaq will not start without the Equity Data Plans' confirmed readiness; NYSE Arca's start is subject to the SIPs' availability; Arca's overnight trades carry sale condition "T", are **not last-sale eligible**, and **count toward consolidated volume**. DTCC: Arca's start is subject to DTCC's modernisation; Nasdaq's order does not mention DTCC or NSCC. Neither source says the SIP or DTCC is ready | NYSE FAQ v4.0; 34-105199 |

  Two consequences carried into item 98 below: the trade-date trap covers only 21:00–24:00, though deriving the tag from the bar's UTC timestamp handles every hour the same way; and night prints are not last-sale eligible, so they can never set a regular-session high, low or close.

- **K2, the numbering.** Item 98, Batch 18. The register number is **SR-68**: on main the register ends at SR-59; Batch 16 (paste A78, branch `a78-batch-16-midterm`) takes SR-60 to SR-64 and Batch 17 (paste A81, branch `a81-batch-17-filing`) takes SR-65 to SR-67, both read at their tips on 28 Oct 2026; no other remote branch carries SR-68 or above. Whichever of A81 and B81 merges second keeps both register lines and both batch-orders entries.

- **K3, the citations the item carries.** D33 is the yfinance ruling of 24 Oct 2026 (`docs/briefs/rulings-2026-10-24-evening.md`): no new yfinance symbols. B68 is the price-source migration brief (branch `b68-price-source-migration`). D38 and D41 are cited as the paste gives them; D38 is the rulings of 25 Oct 2026 cited by the library branches, and no rulings file on main or on any branch read records its text, so whether D38 states the price migration's terms is a needs-you. DTH-1 is the chat-side card (`docs/briefs/dth-1-spec-2026-09-27.md`).

- **K4, nothing built, no source added.** The filing adds no feed, key, symbol, gate or timer. 98(c) names the source the build will try; the build runs the 16 Oct 2026 sources check before it stores a night bar.

---

Item 98 is REPORT_OK-class. It changes no composite weight, no T&B pillar weight and no regime rule, and creates no regime tag. Nothing prints without a stored source.

---

## 1. Rulings at a glance

| Item | Short name | Ruling | Kind | Sessions | By hand |
|---|---|---|---|---|---|
| 98 | The 23-hour equity session | 28 Oct 2026, pending the operator's accept | ADOPT: cadence unchanged; three adjustments (a)–(c) | 1.5 session-evenings | — |

---

## 2. Entries

### 98 · The 23-hour equity session — cadence unchanged, three adjustments

**Question.** On 28 Oct 2026 the operator asked how the exchanges' move to near-24-hour equity trading should change the reporting cadence.

**Ruling.** The reporting cadence does not change. The 07:00 anchor, the 09:50 open note, the 12:30 alert, the 16:45 close and the 21:30 evening note keep their times, because the official crosses and the regular session are unchanged (K1) and the Weekly and the Monthly are calendar-based. Three adjustments, built after Doctrine #2, before the session's first night if it starts on time:

**98(a) Session-aware bars.** The bars feed and everything that reads it (the volume profile, the opening-range state, relative volume, the close) tag each bar as night (21:00–04:00), pre (04:00–09:30), regular (09:30–16:00) or post (16:00–20:00), and every regular-session statistic reads the regular tag only. The trade-date trap: bars from 21:00 to midnight ET carry the next day's trade date at the venue (K1); the store keeps the bar's own UTC timestamp and derives the session tag from it, never from the venue's trade date. A gate on fixtures proves a 21:30 ET bar is tagged night and is not counted in that day's regular-session figures, nor in the next day's.

**98(b) The overnight read.** The 07:00 anchor and the 21:30 evening note read SPY and QQQ overnight prices beside ES once the night session exists, and the evening note's dealer-flip distance is recomputed from the overnight SPY price as well as ES. Until night bars are stored, both print "overnight equities not stored" rather than nothing.

**98(c) The source.** Night bars come from Interactive Brokers (the existing gateway) under the price migration's terms (D38, B68); no new source without the 16 Oct sources check, and no yfinance symbol (D33). If IBKR does not serve night-session bars for SPY/QQQ, 98(a)–(b) stay a listed gap with that reason.

**Not changed.** The Weekly and Monthly schedules; the DTH-1 card times (chat-side, D41); the alert thresholds.

**Placement.** Provisional SR row (SR-68), "provisional, placed by Audit #5"; phase after Doctrine #2; estimate one session-evening for (a), half for (b), (c) folded into the price migration.

---

## 3. Work order

1. 98(c) first, inside the price migration: whether the gateway serves night-session bars for SPY and QQQ, read once the session exists; the sources check filed with its verdict.
2. 98(a): the session tag on the bars table and its readers, with the fixture gate.
3. 98(b): the anchor's and the evening note's overnight lines, "overnight equities not stored" until 98(c) stores a bar.

---

## 4. Verify items

| | What | When |
|---|---|---|
| V1 | Whether the 6 Dec 2026 start holds: Nasdaq's confirming rule filing, the Equity Data Plans' readiness, DTCC's modernisation | Before the build; again in the week of 30 Nov |
| V2 | Nasdaq's trade-date rule for 21:00–24:00 from a Nasdaq notice (unverified, K1) | Before 98(a) is built |
| V3 | Whether IBKR serves night-session bars for SPY and QQQ (98(c)) | Once the session exists |
| V4 | D38's text, for the price migration's terms 98(c) cites (K3) | Needs-you |

---

## 5. Registers

- **Signal-triage register:** SR-68, provisional, placed by Audit #5; the batch-orders cell gains Batch 18.
- **Change orders index:** one line, 28 Oct 2026.
- No narrative, voices or disagreement entry: the item has no outside author.

---

## 6. Sources (read 28 Oct 2026)

- SEC Release No. 34-105199 (10 Apr 2026), order approving SR-NASDAQ-2025-109, Federal Register 15 Apr 2026: https://www.govinfo.gov/content/pkg/FR-2026-04-15/html/2026-07259.htm
- SEC Release No. 34-106378 (15 Sep 2026), NYSE Arca SR-NYSEARCA-2026-94: https://www.sec.gov/files/rules/sro/nysearca/2026/34-106378.pdf
- NYSE Extended-Hours Trading FAQ, v4.0, August 2026: https://www.nyse.com/publicdocs/nyse/NYSE_Extended_Hours_Trading_FAQ.pdf
- Nasdaq 23/5 Trading Information Hub, https://www.nasdaq.com/23-5-trading: timed out on two reads; not relied on.

---

## 7. Sign-off

| When | What | Words |
|---|---|---|
| 28 Oct 2026 | The cadence unchanged; 98(a)–(c) after Doctrine #2 | The ruling as given with paste B81, pending the operator's accept |

Open at filing: the operator's accept; SR-68 and the batch number (audit); V1–V4.
