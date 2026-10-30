# The Annual Structural Review

## How Every Paper in the Library Is Re-examined Once a Year, and What Makes the Review a Mechanism Rather Than an Intention

**Companion white paper — chester-reports library**
**Series placement:** Companion **XXXII** — System shelf, the protocol for the whole library, per the library guide, which is canonical for numerals; cross-references in this paper are by name
**Version:** 1.0 — 24 October 2026
**Status:** Draft 1, for the operator's review. The protocol, its questionnaire, its calendar, the standing register the library gate reads, and the gate check. No paper has yet been reviewed under it.

---

### Reader's note

The papers in this library are written to be timeless. Their mechanisms are meant to hold for years: what a credit spread prices, why dealers hedge the way they do, how a debt cycle turns. But the plumbing changes, the participants change, the relationships the papers rely on drift, and the technology that decides who provides liquidity changes fastest of all. A library that is never re-examined teaches its reader the market of the year it was written.

Before this protocol, the library's review was an intention: a "next edition" note in three papers and a mutation scan in one. Audit 2 proposed turning it into a mechanism, with four instruments, a schedule, a log, tripwires and a gate, and the operator approved the roster that reserved this numeral for it on 7 September 2026. This paper is that mechanism, written as a protocol. It says what a structural review asks of a paper, what the questionnaire is, when each paper is reviewed, what the standing register holds and how the gate reads it, and what the review is not.

Its rule of thumb is the audit's: *the absence of an edit is a recorded decision, not a default.* A paper that comes through the review with every mechanism holding gets a one-line log entry and no change. That line is the point.

**Prerequisites.** The library guide, for the roster and each paper's shelf; *Evidence and Inference*, for what it means to re-verify an empirical claim; and Audit 2's Part 4 standards, which every content paper is written to.

---

## Part I — What a Structural Review Asks

### 1. Four questions of every paper

A structural review asks four questions of a paper, in this order, and records an answer to each.

**Does its mechanism still hold?** A paper's timeless body rests on mechanisms: causal claims about why markets behave as they do. The review asks of each whether anything in the year contradicts it. A mechanism is not falsified by a bad year for the trades it implies. It is falsified when the cause it names stops producing the effect, or when a new cause produces the same effect in a way the paper cannot accommodate. The answer is recorded per mechanism: holding, strained, or broken.

**Are its empirical claims still true?** Every empirical claim a paper makes carries its sample period and its last-verified date, under the house presentation standard. The review re-verifies each one on the most recent window against the sample it was measured in, and records the result as *holding*, *weakening*, *broken* or *re-attached*. A broken claim is the review's first agenda item, because it is where a paper is now teaching something false.

**Is its dated appendix fresh?** Every level, probability or "today" read lives in a dated appendix with an as-of date. The review refreshes each figure from the store, so that the appendix carries this year's read and the body is untouched.

**Are its tactical applications still true, by horizon?** Each content paper closes with tactical applications across the seven horizons: what is tradeable, the edge, who is on the other side and why, why competition has not removed it, what would end it, the expression, the book and the report section. The review asks of each horizon whether the edge still exists and whether its counterparty is still there. An edge whose counterparty has left is gone, however good the mechanism.

The review ends with one decision per section: **reaffirm**, **amend**, **rewrite** or **retire**, each with its reason. A section reaffirmed is unchanged. One amended changes in place, with the masthead's version bumped. One to be rewritten is queued as a writing task. One retired is moved to the archive.

| Question | Unit | Answers |
|---|---|---|
| Does the mechanism hold? | Each mechanism in the body | Holding, strained, broken |
| Are the empirical claims true? | Each claim with its sample and date | Holding, weakening, broken, re-attached |
| Is the dated appendix fresh? | Each dated figure | Refreshed from the store, with its new as-of |
| Are the tactical applications true? | Each horizon | Edge present or gone; counterparty present or gone |
| The decision | Each section | Reaffirm, amend, rewrite, retire |

### 2. What the review is not

It is **not a re-forecast**. The appendices carry the year's read. The body changes only when a mechanism or an empirical claim has been shown to have changed, never because the year's market was different from the last.

It is **not a rewrite on taste**. A paper whose prose has aged but whose mechanisms hold is reaffirmed, not polished. Style is the writing sessions' business, not the review's.

It is **not a decision about the books**. The review may find that a paper's tactical application at a horizon is gone. That finding goes to the Doctrine monthly, which decides what the books do about it, under the change ladder. The review informs a rule; it never changes one.

---

## Part II — The Four Instruments

The review reads four instruments. The first is written once per paper and maintained; the second and third are computed; the fourth is a session's written answers.

### 3. Instrument 1: the Assumptions and Falsifiers appendix

Every content paper carries an Assumptions and Falsifiers appendix in a fixed format, and it is what the review reads. Without it, the review is an essay. The appendix lists:
- **(a)** the mechanisms the paper treats as durable;
- **(b)** every empirical claim it relies on, with the sample period, the regime it was measured in and the date last verified;
- **(c)** for each, the falsifier: the observation that would mean the section is wrong;
- **(d)** the items from the standing register of what could change (Part V) that touch this paper;
- **(e)** an inventory of every dated figure in the paper's appendices, with the stored series it can be recomputed from.

Section (b) is the one the gate is meant to police. Audit 2 specifies that the library gate fails when a paper's (b) is missing. On 24 October 2026 two of the roster's papers carried the appendix at all, so the failing check is adopted in a form that binds new and reviewed papers and lists the rest (section 15). Until its review, an older paper without the appendix is reviewed by its review session reading the body for its claims, and the first output of that review is the appendix.

### 4. Instrument 2: the dated-figure recomputation

Every figure in a paper's dated appendices is recomputed annually from the point-in-time store, as of the review date, stored as an observation, and compared with the published value. A move beyond a stated tolerance is flagged for the review session. *Base Rates* already specifies this for its own tables; the protocol makes it the rule for every appendix. It is a computed step, not a session, and it is specified as a build target the review runs before its sessions. It is not built yet. Until it is, the review session refreshes the appendix by hand from the store, and says so in the log.

### 5. Instrument 3: the relationship health check

For each empirical claim in a paper's section (b), a rolling test on the most recent window against the sample the claim was measured in. Does credit still lead equities, and by how long? Does curve inversion still precede recession? Has the gold–real-rates relationship re-attached or stayed broken? Does the gap between implied and realised volatility still carry its premium? Does the closing auction's imbalance still predict the next open? Each test returns *holding*, *weakening*, *broken* or *re-attached*, with its numbers. Where the system already grades a claim, as the calibration ledgers grade proposed signals, the health check reads the ledger rather than re-testing. It is semi-automated: the tests are code, and the review session reads them.

### 6. Instrument 4: the structural scan

A session answers a fixed questionnaire in writing, once a year for the corpus and once for each paper. Its questions are in Part III.

| Instrument | Kind | Built? |
|---|---|---|
| 1. Assumptions and Falsifiers appendix | Written per paper, maintained | In two papers |
| 2. Dated-figure recomputation | Computed, before the sessions | Specified, not built |
| 3. Relationship health check | Semi-automated tests | Specified, not built; the calibration ledgers serve where they exist |
| 4. Structural scan | A session, a questionnaire | This paper |

---

## Part III — The Questionnaire

### 7. The adversarial questions

The scan opens with ten adversarial questions, asked of the corpus and then of each paper. They are meant to be uncomfortable, because the questions a library never asks are the ones its reader pays for.

1. What if the prevailing explanation is wrong?
2. What if a relationship thought stable stops working?
3. What if a major participant changes its behaviour?
4. What if technology changes who provides liquidity or information?
5. What if a currently insignificant asset class becomes systemic?
6. What if the next crisis resembles none we study?
7. What if a source of alpha disappears?
8. Where might new alpha emerge?
9. What is too small to notice today?
10. What does the corpus assume only because today's system makes it look natural?

Each answer is a paragraph, and an answer of "nothing" must say why. The last question is the hardest. Every library assumes the market its first papers described, and the assumptions that look most natural are the ones no review would think to question.

### 8. What are we not thinking about

The second pass is the "what are we not thinking about" pass. Three forced inputs keep it from becoming an exercise in inspiration.

**The mutation scan.** The Twenty-Five's ten mutations beyond its listed tails become a living list, re-run against the year's events, with each mutation promoted to a listed tail, kept, or retired.

**The size scan.** Any market, structure or participant class that crossed a stated threshold in the year is a candidate subject: a notional, a share of volume or a share of ownership. A market that was too small to matter last year and is not this year is the clearest kind of thing a library misses.

**The register's own anomalies.** Trades that worked or failed for reasons no paper explains are the library's most honest gap detector, and the decision register records them. The review reads the year's graded decisions for outcomes the papers cannot account for.

### 9. The per-paper record

For each paper the scan records, in the review log:
- each mechanism's word (holding, strained, broken);
- each empirical claim's word from the health check (holding, weakening, broken, re-attached);
- the dated appendix refreshed, with the figures that moved past tolerance;
- each horizon's tactical application, present or gone;
- the answers to the questions that touch the paper;
- the standing-register items that touch it, and whether any tripwire crossed;
- the decision per section, with its reason;
- the version the paper leaves at, and the date of the next review.

The masthead owns the version, and the guide copies it. A review that changes nothing still records the review date, so the clock restarts.

---

## Part IV — The Calendar

### 10. January for the corpus; the papers across the year

Audit 2 scheduled the whole review in January. This protocol keeps January for the corpus and spreads the papers across the year, for two reasons. A review of thirty papers in one month would be thirty shallow reviews, because the attention budget allows one sitting of two hours a week, and three or four papers fit a sitting. And a library reviewed all at once ages all at once; one reviewed across the year always has a part that is fresh.

**January: the corpus pass.** The dated-figure recomputation and the health check run for every paper. The corpus questionnaire is answered. The papers are ranked by how many broken or weakening claims each carries, and a paper with a broken claim is pulled forward into the month after January, whatever its scheduled month.

**February to December: the papers.** Two or three papers a month, grouped so that papers which cite each other are reviewed together. Each paper's month is its `review_month` in the standing register.

| Month | Papers |
|---|---|
| January | The corpus pass: Instruments 2 and 3 for every paper; the corpus questionnaire; the ranking |
| February | Tops and Bottoms, Base Rates, Evidence and Inference |
| March | The Monthly manual, Rates and Liquidity, Credit |
| April | Currencies, Energy, Metals |
| May | Digital Assets, International Equities, Emerging Markets |
| June | Equities, Positioning and Flows, Earnings |
| July | Volatility, the Dealer's Hand, Options as Expression |
| August | The Daily Cascade, Technical Indicators, Price, Time, and Edge |
| September | Disruptive Themes, the Twenty-Five, and Debt Cycles when it joins the roster |
| October | Portfolio Construction, the Operating Doctrine, the Systematic Book |
| November | The Reporting System, and the T&B Manual when it joins |
| December | This protocol; spare capacity for papers pulled forward |

The first cycle runs in 2027. The calendar is set so that no paper on the roster today passes thirteen months without a review in the first cycle. The oldest paper, Tops and Bottoms (May 2026), falls in February.

### 11. Off-cycle: the tripwires

Any item in the standing register whose indicator crosses its threshold triggers the review of the papers it touches, within the month. The Doctrine's rule that changes are made only at the monthly session is preserved: the tripwire opens the question, and the monthly session decides. A tripwire review covers only the sections the register item touches, and records itself in the log like any other.

---

## Part V — The Standing Register

### 12. One file, read by the gate

The standing register is one file, `docs/reading/structural-review-register.yaml`, and the library gate reads it. It holds two lists.

**The papers.** One row per paper on the roster: its numeral and file, the version and its date as the guide and masthead carry them, the date of its last structural review (empty while it has never had one), the month of its annual review, its status, and where its last review's log lives. The file was seeded on 24 October 2026 from the guide's at-a-glance rows and each paper's masthead. Every paper's status is "never reviewed", because no review has been held under this protocol. Each row is written on one line, so the gate can read it without a parser.

**The changes.** Audit 2's table of what could change, each row naming the change, the papers it touches and a measurable tripwire, with a status word: *watching* (no measurement stored yet), *quiet*, *near* or *crossed*. The first version is the audit's fifteen rows, from AI changing research and agents trading, through tokenisation and private markets, to entirely new asset classes. Every row is "watching" on 24 October 2026, because no tripwire's indicator is yet stored and measured. Turning each tripwire into a stored series is work for the review's first January.

The register is the library's answer to the warning not to let the existing papers define the boundaries of what is studied. It lists what lies outside them, reviewed on a schedule, with a rule for when something outside becomes a subject.

### 13. Who writes it

A review session writes the register when it reviews a paper: the review date, the status and the log. A writing session never does. A new version of a paper moves the row's version and version date, through the guide's own update. It does not move the review date, because a new version is not a review. The register is otherwise edited only by a ruling.

| Field | Written by | When |
|---|---|---|
| version, version_date | The session that publishes a new version | With the masthead and the guide row |
| last_reviewed, status, log | The review session | At the review |
| review_month | A ruling | When the calendar changes |
| changes[].status | The review session | At the January pass, or on a tripwire |

---

## Part VI — The Gate

### 14. What the gate checks

The library gate gains one check, the fifteenth, which reads the register on every run:
- a paper on the roster with no row in the register is a **warning**;
- a paper whose review clock has passed **thirteen months** is a **warning**. The clock runs from the last review, or from the version date while the paper has never been reviewed;
- a register row naming a paper the roster does not have is a **warning**.

These are the warnings Audit 2 specifies: "library-check warns when any paper's last-reviewed date is more than thirteen months old". They are warnings, not failures, because a late review is a debt to be paid, not a broken library.

### 15. The appendix rule

Audit 2 also specifies that the gate **fails** when a paper's Assumptions and Falsifiers section (b) is missing. The rule is adopted (decision 52, ruled 25 October 2026), in a form that does not fail the library for a debt it has known about since September. A paper with no Assumptions and Falsifiers appendix fails the gate if its first version is dated on or after 26 October 2026, or if the standing register shows it reviewed at least once. Every other paper without the appendix is listed in one warning, and its first review pays the debt. The first version date is the earliest date on the masthead's Version line, or the register's version date if earlier. The check reads the appendix's heading rather than section (b) alone, because the papers that carry the appendix label its sections differently. A fixture pair holds the rule: a new paper without the appendix fails, an old one warns.

| Check | Effect | State |
|---|---|---|
| A roster paper has a register row | Warning if not | Adopted (check 15) |
| A paper reviewed within thirteen months | Warning if not | Adopted (check 15) |
| A register row names a roster paper | Warning if not | Adopted (check 15) |
| A paper's Assumptions and Falsifiers appendix exists | Failure if first dated on or after 26 Oct 2026, or once reviewed; otherwise one warning listing the papers | Adopted (check 15, decision 52) |

---

## Part VII — The Log

### 16. One file per review

Each review writes a log, one file per paper per review, in the library's review folder, holding the per-paper record of Part III. The corpus pass writes one log of its own, with the questionnaire's answers, the mutation, size and anomaly scans, and the ranking. A tripwire review writes a log naming its tripwire. The register's `log` field points at the latest.

The log is the review's only product apart from the edits it decides, and it is the thing a reader consults to know whether a paper's claims were checked this year, by whom and with what result. A paper whose log says every claim held and nothing changed has been reviewed as surely as one rewritten.

| Log | Written | Holds |
|---|---|---|
| The corpus log | Each January | The questionnaire's corpus answers; the three scans; the ranking |
| A paper's log | In its review month | The per-paper record; the decision per section |
| A tripwire log | Within the month of a crossing | The tripwire, the sections touched, the decision |

## Part VIII — A Review, Worked Through

### 17. One paper, one month

What follows is how a review of one paper runs, using *Credit* in its March slot as the example. It is illustrative: it describes the steps and the kinds of finding, not a result, because no review has been held.

**Before the session.** The January pass has already run *Credit*'s dated figures through the recomputation and its claims through the health check. The session opens with three things in hand: the paper's Assumptions and Falsifiers appendix; the recomputation's list of appendix figures that moved past tolerance; and the health check's word for each claim in section (b). Suppose the health check reads one claim as *weakening*: that a spread's percentile regime still dates the default cycle the way it did before private credit grew.

**The mechanisms.** The session reads the paper's durable mechanisms (what a spread prices, the lending-standards cycle, the credit lead over equities) against the year. None is contradicted by the year's events, so each is marked *holding*. One is marked *strained*: the private-credit growth the standing register tracks under its private-markets item has moved part of the default cycle off the public market, where the paper's indicators cannot see it. Strained is not broken. It is a finding the decision must answer.

**The claims.** The weakening claim is examined against its sample. It was measured before private credit was large, so the regime it was measured in is not today's. The finding is recorded in the paper's words, with its numbers from the health check, and the falsifier in section (c) is checked: has the observation that would mean the section is wrong occurred? Suppose it has not, yet. The claim stays, with its weakening recorded and its last-verified date moved.

**The appendix.** Every dated figure is refreshed from the store. Two moved past tolerance; each is replaced with its new value and as-of date. The body is untouched.

**The tactical applications.** For each of the seven horizons, the session asks whether the edge and its counterparty remain. Suppose the months horizon's edge depends on a forced seller who still exists, and the days horizon's on a liquidity provider whose share has fallen. The first is marked *present*; the second is marked *present, counterparty thinning*, and goes to the Doctrine monthly as a finding, not a change.

**The questionnaire.** Of the ten adversarial questions, three touch the paper most. What if a relationship thought stable stops working (the weakening claim)? What if a currently insignificant asset class becomes systemic (private credit's share)? What does the paper assume only because today's system makes it look natural (that defaults are observable on the public market)? Each gets a paragraph.

**The decision.** Section by section: most are *reaffirmed*. The section on the default cycle is *amended*, with a paragraph naming the private-credit channel and pointing to the private-markets register item. The masthead's version moves from 1.0 to 1.1, and the guide copies it. Nothing is rewritten or retired.

**The record.** The log is written, the register row gains its review date, status "reviewed: amended" and the log's path, and the next review falls in the following March. The private-markets item's status moves from *watching* to *near*, so the January pass measures it first.

The whole review is one sitting of under two hours, inside the attention budget, because the computation was done before the session and the questionnaire tells the session what to ask. That is what makes the review a mechanism: the expensive part runs without the operator, and the operator's two hours go on the judgments only a reader can make.

---

## Appendix A — Dated: The Register at Seeding (as of 24 October 2026)

*From `docs/reading/structural-review-register.yaml` as seeded. Every paper: never reviewed. Every change: watching.*

### A.1 What the seeding found (24 October 2026)

- Twenty-eight papers rowed, from the guide's at-a-glance rows and the mastheads. The oldest version date is Tops and Bottoms, May 2026, whose thirteen-month warning would fall in June 2027. Its review month is February 2027.
- Two papers on open library branches (Debt Cycles, Regimes, and Environments; the T&B Manual) are noted for rowing at their merge.
- Two of the roster's papers carry an Assumptions and Falsifiers appendix: *Price, Time, and Edge* and the Reporting System.
- Instruments 2 and 3 are specified and not built.

### A.2 The first cycle (as of 24 October 2026)

The corpus pass in January 2027; the papers from February to December 2027, by the calendar of Part IV.

---

## Appendix B — Assumptions and Falsifiers

**Mechanisms this protocol assumes.**
1. *A library's mechanisms outlast its figures.* Falsified if a year's reviews amend more mechanisms than they refresh figures: the body would then be dated, not timeless.
2. *A recorded "no change" is worth recording.* Falsified if no review ever reaffirms a section; the protocol would then be a rewrite cycle in disguise.
3. *Spreading the papers across the year keeps each review deep.* Falsified if the monthly reviews run short of the questionnaire's per-paper record.

**Empirical claims.** None. The protocol makes no claim about markets.

**Standing-register items touching this paper.** All of them, since the register is this paper's subject.

**Dated figures in this paper.** None in the body; the seeding's facts are in Appendix A.
