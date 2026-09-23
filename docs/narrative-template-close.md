# Close Narrative — Style and Coverage Specification

**For:** `daily_cascade/narrative.py` · **Rule:** one paragraph, above the tables, shipped only if the numeral audit passes. Every number in the paragraph must exist in the payload. Nothing in the paragraph is a recommendation; the packet's rule decides the position, and the paragraph says so.

## Coverage, in this order

1. **The regime** — spot versus the flip, and how many consecutive sessions on that side.
2. **The hedge flow** — dollars dealers must trade per 1% move, and its change versus the prior session.
3. **The corridor** — put wall, call wall, their movement since the prior session, and where gamma and put delta concentrate.
4. **What the vol complex says** — VIX level and change, term structure, implied versus realized — and what it does *not* say.
5. **The position** — for each open decision: fill, current close, distance to invalidation in points and percent, and the single decision that matters (the rule, not a feeling).
6. **The exceptions** — the open set by count, and the two most extreme named. These are the object's own findings about the *market*: five-year extremes on a member, and contradictions held past their declared session count. The table below the paragraph carries the full set; the paragraph says how many are open and which two are furthest from the middle of their distribution.
7. **The system's scorecard** — the pin tally to date at the declared tolerance; the cross-check status when present; any live test the day's data creates.

### The paragraph does not restate a table

The eight dimensions, the six contradiction rows and the pin tally are printed in full below the paragraph. Reciting them adds nothing a reader could not read there, and it crowds out the only thing prose can do, which is say what the configuration **means**.

Name a dimension when it **changed**, when it sits at an **extreme**, or when it **disagrees** with another. Otherwise say what the set of them amounts to. *A sentence listing every percentile in order is a failed paragraph even when every figure in it is correct* — and the published samples were failing this way before it was written down: one spent eighty words on "breadth is narrow at the 27.4 percentile, credit is easy at 92.4, growth expanding at 93.5, inflation stable at 64.1, liquidity ample at 96.4, rates high at the 100th percentile, trend flat at 55.9, volatility subdued at 14.9" and had no room left to say that nothing in that configuration had moved in a week.

The reference paragraph above is the register. It names four figures and spends the rest of its length on what they imply.

## Reference paragraph (9 September 2026)

Wednesday, 9 September — SPY close 762.45. The market spent a third day below the gamma flip, and the structure around it tightened rather than eased: dealers now have to sell about ten and a half billion dollars of index for every one percent decline, up from six and a half on Tuesday, while the call wall dropped from 780 to 775 and the put wall stayed at 760 with the largest concentration of both gamma and put delta sitting on it. Read together, that is a corridor whose ceiling is descending, whose floor is heavily defended, and whose occupant is a hedging flow that accelerates moves instead of damping them — the configuration in which a modest push turns into a fast one. Nothing in the vol complex says panic: VIX in the mid-teens, term structure still in contango if barely, realized volatility low. What it says is *fragile* — the tape is calm because it hasn't been tested, not because it's supported. For the position, the takeaway is narrow and unambiguous: the thesis is alive by two and a half points and the 760 level is doing double duty as the market's support and your exit, so the only decision that matters is the settled close tonight, and it should be made by the rule written Saturday rather than by how the corridor feels. For the system, the takeaway is that after three sessions the pin log has its first two hits at a tolerance nobody touched, the flip has been confirmed twice against an outside vendor and the difference between them turned out to be 0DTE rather than error, and the 760 strike is now a live test of whether the wall the engine computed is the wall the market defends.

## Print precision — the model never sees a figure the report would not print

The payload handed to the model is carried **at the precision the report prints**, and the numeral audit compares at that precision. This is a rule about the payload, not about the prose: a figure the model cannot see is a figure it cannot print.

| Field | Precision | Why |
|---|---|---|
| Percentiles | 1 dp | What the state block prints. A percentile over 1,254 sessions quoted to four decimals is a fiction with a true number inside it |
| Anything in percent — a move, a distance | 2 dp | `-0.02%`, not `-0.0155%` |
| Dollar magnitudes — hedge flow, net gamma, P&L | 2 dp **at the bn/mm/k scale**, still in dollars | `4,590,000,000`, which is what "4.59 billion" means. Kept in dollars because the audit reads "4.59 billion" from prose as 4.59e9 |
| Everything else — prices, points, ratios, z-scores | 2 dp | The report's own convention |

Integers are untouched; a count of 24,796 sessions is exact. The transform is idempotent and is applied both where the payload is assembled and again at the model boundary, so no caller can put a full-precision figure in front of the model by forgetting a step.

**The failure this removes.** The audit already forgives rounding, so a paragraph printing 45.3 against a payload holding 45.2951 passed — which left the model *looking at* 45.2951, and a model handed 45.2951 prints it. Three published samples did. The paragraph then disagreed with the table beside it in the fourth decimal, and a reader cannot tell rounding from two different numbers. `daily_cascade/precision.py` declares the table; `tools/validate_daily_close.py` fails the build on any payload figure carried at more precision than its rule allows.

## Style rules

- Plain declaratives. No headers inside the paragraph. No bullets.
- **No markdown, and the reference paragraph above is shown exactly as it should be emitted.** These reports are HTML: the renderer escapes what it is given, so `**bold**` reaches the reader as asterisks. The first weekly opened with a bold dateline because the example here carried one — the instruction and the example have to agree, and the example is the one the model copies.
- Numbers may be written as words ("ten and a half billion") only when the payload value is also printed elsewhere on the page; the audit matches the numeral form.
- Name the mechanism, not the mood: "dealers must sell X per 1%" rather than "the market feels heavy."
- The position sentence states the rule and the distance. It never says buy, sell, add, or trim.
- End on the system, not the market: what today's data tested, and what it will test tomorrow.
- Length: what the coverage needs. On a quiet day, four sentences is correct.
