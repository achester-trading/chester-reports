# Close Narrative — Style and Coverage Specification

**For:** `daily_cascade/narrative.py` · **Rule:** one paragraph, above the tables, shipped only if the numeral audit passes. Every number in the paragraph must exist in the payload. Nothing in the paragraph is a recommendation; the packet's rule decides the position, and the paragraph says so.

## Coverage, in this order

1. **The regime** — spot versus the flip, and how many consecutive sessions on that side.
2. **The hedge flow** — dollars dealers must trade per 1% move, and its change versus the prior session.
3. **The corridor** — put wall, call wall, their movement since the prior session, and where gamma and put delta concentrate.
4. **What the vol complex says** — VIX level and change, term structure, implied versus realized — and what it does *not* say.
5. **The position** — for each open decision: fill, current close, distance to invalidation in points and percent, and the single decision that matters (the rule, not a feeling).
6. **The system's scorecard** — the pin tally to date at the declared tolerance; the cross-check status when present; any live test the day's data creates.

## Reference paragraph (9 September 2026)

**Wednesday, 9 September — SPY close 762.45.** The market spent a third day below the gamma flip, and the structure around it tightened rather than eased: dealers now have to sell about ten and a half billion dollars of index for every one percent decline, up from six and a half on Tuesday, while the call wall dropped from 780 to 775 and the put wall stayed at 760 with the largest concentration of both gamma and put delta sitting on it. Read together, that is a corridor whose ceiling is descending, whose floor is heavily defended, and whose occupant is a hedging flow that accelerates moves instead of damping them — the configuration in which a modest push turns into a fast one. Nothing in the vol complex says panic: VIX in the mid-teens, term structure still in contango if barely, realized volatility low. What it says is *fragile* — the tape is calm because it hasn't been tested, not because it's supported. For the position, the takeaway is narrow and unambiguous: the thesis is alive by two and a half points and the 760 level is doing double duty as the market's support and your exit, so the only decision that matters is the settled close tonight, and it should be made by the rule written Saturday rather than by how the corridor feels. For the system, the takeaway is that after three sessions the pin log has its first two hits at a tolerance nobody touched, the flip has been confirmed twice against an outside vendor and the difference between them turned out to be 0DTE rather than error, and the 760 strike is now a live test of whether the wall the engine computed is the wall the market defends.

## Style rules

- Plain declaratives. No headers inside the paragraph. No bullets.
- Numbers may be written as words ("ten and a half billion") only when the payload value is also printed elsewhere on the page; the audit matches the numeral form.
- Name the mechanism, not the mood: "dealers must sell X per 1%" rather than "the market feels heavy."
- The position sentence states the rule and the distance. It never says buy, sell, add, or trim.
- End on the system, not the market: what today's data tested, and what it will test tomorrow.
- Length: what the coverage needs. On a quiet day, four sentences is correct.
