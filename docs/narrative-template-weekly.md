# Weekly Tactical — Style and Coverage Specification

**For:** `daily_cascade/weekly_report.py` · **Rule:** long-form permitted, shipped only if the numeral audit passes. Every number must exist in the payload, at the precision the payload carries it. Nothing is a recommendation; the register's rule decides each position and the paragraph states the rule and the distance.

This anchor replaces the Friday Reflection and the Sunday Forward Plan. It is read once, on Sunday morning, before the week is planned.

## Coverage, in this order

1. **The week in state** — what changed over five sessions and what held. Dimension state changes against the *previous Friday's object*, dial moves, and the exceptions that opened, closed, or **opened and closed inside the week without showing at either end**. That last set is in the payload as `exceptions_intraweek_only` and it is the fact a weekly usually misses: "it moved twice and came back" is a different week from "nothing happened."
2. **The grades, and what their interval permits** — the week's graded decisions and the running expectancy. **Read the interval before the point.** An interval that spans zero permits nothing about the sign, and *Evidence and Inference* is explicit that the Doctrine's 30 and 50 thresholds are minima for the crudest question. A weekly that quotes a mean without its interval is the error that paper exists to prevent.
3. **Each open thesis, and what would change it** — for every open decision: the rule already written, the distance to it, the age. Then the operative sentence: *what would change this thesis*. Not what to do — what would have to be true for the position to be wrong.
4. **Where the vol dial's two legs disagree, and why it matters this week** — the champion (VX2/VX1, the curve) against the challenger (VIX3M/VIX, the proxy), and the week's count of agreeing and disagreeing sessions. The dual run's question is a count, not an opinion; the paragraph says what this week added to it.
5. **The week ahead** — releases that carry a tracked series, earnings in the universe, session events, and the dated claims. Dates are facts; what they mean for the open book is the paragraph's job.
6. **What is not sourced** — where the payload says `not_yet_sourced`, say so. Weekend developments are absent by construction until the events ingest lands, and a weekly that quietly omitted them would read identically on a quiet weekend and an uninstrumented one.

## Length

**Whatever the week needs. No word count, no paragraph count** — the operator's ruling. Several paragraphs are correct when the week had several things in it. On a week where nothing changed, three sentences saying so is correct and is better than five hundred words arriving at the same place.

What does not vary with length: print precision, the numeral audit, the model pin, and the rule that a figure the payload does not carry cannot be printed.

## Reference paragraph (week ending 18 September 2026)

Week ending Friday 18 September. One dimension moved in five sessions: volatility from normal to subdued, and nothing else changed state — the two dials that read at all held gamma negative and vol normal, and macro stayed absent because the growth and inflation members knowable at a Friday cutoff stop in May. No exception opened or closed, and none opened and closed inside the week either, so the quiet is real rather than an artefact of looking only at the endpoints. The term-structure legs agreed on all five sessions, both reading contango, which is the least informative agreement available: the champion sat at its 37th percentile and the proxy at its 95th, so they concur on the word and differ on whether the curve is ordinary or unusually steep — five more sessions on the record and the count that will eventually retire one of them is at 5–0 for the quarter. Nothing reached a grading horizon this week, which is the expected state of a register days old and not a result; the running expectancy is therefore still undefined, and the honest reading of an undefined expectancy is that nothing about the sign can be said. One decision is open and one is drafted: the open SPY position is flagged INVALIDATED with its mark 13.35 points above the 760 level its rule names, and what would change the thesis is the rule already written — a settled close below that level — not the distance, which has been positive all week. Next week carries no tracked FRED release and no earnings in the universe; the sessions classify as ordinary with no expiry and no month end. Weekend developments are not sourced: the events ingest is 6c, and until it lands this block is blank by construction rather than because the weekend was quiet.

## Style rules

- Plain declaratives. No headers inside the prose, no bullets.
- **No markdown, and the reference paragraph above is shown exactly as it should be emitted.** These reports are HTML: the renderer escapes what it is given, so `**bold**` reaches the reader as asterisks. The first weekly opened with a bold dateline because the example here carried one — the instruction and the example have to agree, and the example is the one the model copies.
- **The interval before the point**, wherever an expectancy or a Brier score appears.
- Name the mechanism, not the mood.
- **Do not restate a table row by row.** Every table is printed below the prose. Name a figure when it changed, when it is at an extreme, or when it disagrees with another.
- A sign is part of the numeral: `-0.02%`, not "down 0.02%".
- Never say buy, sell, add, trim, or hold.
- End on what next week tests, not on what the market will do.
