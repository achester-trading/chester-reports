# Narrative register: disagreement pairs

A **disagreement pair** is two published views of one market question, each tied to a stored measure, and adjudicated on a fixed schedule. The signal-triage batches define them (Batch 5 item 26; Batch 6 items 35 and 42). Each entry records:
- the question;
- the two sides, with their named sources;
- the measure that adjudicates between them;
- the review cadence.

**Status.** The narrative register's code (`altdata/narratives.py`) holds stories, and its one human gate is the confirm step for a proposed story. It has no pair kind, so a pair cannot be a pending entry there.

Under the ruling of 16 October 2026, judgment drafts are committed as drafted and listed for Ari's accept-all. That is the status of every entry below until Ari accepts them. A pair does not grade itself and has no decision rights; its monthly adjudication is a line in the Monthly.

## what_driving_5_3 — "What's driving 5.3%" (Batch 5 item 26)

The pair itself is session B's item-26 draft (`st-r4-tranche-1` notes), and its body is added there. This branch adds one entry to it.

**Bear side, added 16 October 2026 (Batch 6 item 35).**
- **The view:** "Collision course", Arthur Budaghyan (BCA Research, public post, October 2026).
- **The claim:** core corporate prices are about +5% on the year against unit labor costs of about +1.5%. Core corporate prices here are PPI final demand less foods, energy and trade services. The gap that lifts earnings is the inflation that lifts yields, so stocks and bonds are on a collision course.
- **Side:** it joins the pair's bear side, against Boivin.
- **Measured by:** ST-R5.35a's corporate-price/ULC gap and its closing flag.

## more_hikes_vs_market_tightening — "More hikes" against "the market does the tightening" (Batch 6 item 42)

**Added 16 October 2026.**

- **Side A, "More hikes"** (Callum Thomas, Topdown Charts): composite inflation expectations are turning up, and the Fed follows with a lag.
- **Side B, "The market does the tightening"** (Ruth Carson, Bloomberg; Orchard, T. Rowe Price): the long end's rise does the Fed's work.
- **Adjudicated monthly.** The composite expectations z's direction over three months (ST-R5.42a) is read against the market-does-the-tightening flag (ST-R5.34a):
  - the composite rising with the flag off scores for side A;
  - the composite flat or falling with the flag on scores for side B;
  - both rising, or both off, is a draw and is said to be one.
- **Review:** monthly.
