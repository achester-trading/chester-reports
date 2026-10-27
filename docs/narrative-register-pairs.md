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

## energy_contained_vs_broad — "An energy shock, contained" against "broad acceleration" (Batch 7 item 46)

**Added 16 October 2026 (6e-releases, session B). A draft for Ari's accept-all.**

- **The question:** is September 2026's CPI an energy shock that stays in energy, or the start of a broader acceleration?
- **Side A, "An energy shock, contained"** (Charles-Henry Monchau, Syz, public post on the September 2026 CPI; Schwab chart of BLS data as of 30 September 2026). Headline CPI rose 0.6% on the month, and gasoline (+9.1%) was roughly half of it. Rent rose 0.2% and owners' equivalent rent 0.3%; dairy, meat and medical goods fell. The question is pass-through into airfares, shipping and business prices.
- **Side B, "Broad acceleration"** (Arthur Budaghyan, BCA Research, "Collision course", October 2026; Batch 6 item 35). Core corporate prices run near +5% on the year, so inflation is broader than core CPI shows.
- **Adjudicated monthly** by the two measures the order names, median CPI and diffusion (`altdata/releases.py` `decomposition`). Each month:
  - side A scores when the Cleveland Fed median's three-month average (annualised) does not rise from the previous month's and fewer than half of the 24 categories run above 4% annualised;
  - side B scores when the median's three-month average rises and half or more of the categories run above 4%;
  - anything else is a draw, and is said to be one.
- **The pass-through flag** (item 46b) is printed beside the verdict and does not score: it says whether the shock is spreading through the energy-sensitive basket, which is what side A's own question asks.
- **Review:** monthly, in the Monthly's inflation block.
- **Session-set in this draft:** the "half of the categories" line (50%), and "does not rise" read on the three-month average so one month's median does not decide it.

## private_credit_watch — Moody's "positive watch" against the Credit paper's bifurcation (Batch 17 item 95)

**Added 26 October 2026 (paste A81, filing). A draft for the operator's accept-all.**

- **The question:** is the private-credit risk receding, or bifurcating?
- **Side A, "Receding"** (Moody's Analytics, "What Could Go Wrong", as of 25 October 2026): "private credit craters" sits on the matrix's positive watch, its likelihood falling.
- **Side B, "Bifurcating"** (the Credit paper's bifurcation thesis).
- **Measured by** the testable statement the order names: private-credit BDC marks and non-accruals over the next two quarters. The adjudicating series and its rule are the building paste's (Batch 17, SR-66).
- **Review:** quarterly, for two quarters.

## Narrative claims logged from Batch 17 (not stories; no implied outcome yet)

**Added 26 October 2026 (paste A81, filing).** Claims the order sends to the narrative register. Neither is a story in `config/narratives.yaml`: a story needs an implied outcome on a stored series, which is a building paste's work, and neither carries a right.

- **The 200-year real-rate claim** (item 94; an unattributed public post, author pending V4): a real premium near 3% "aligns with a 200-year average" of about 2% real return plus about 1% term premium. It stays here until sourced (V3: Homer and Sylla, or Jordà, Schularick and Taylor); it never prints as a figure before then.
- **"A higher probability of lower returns into 2027"** (item 92; an independent macro analyst, Global Business Cycle Framework): global liquidity momentum at its current level preceded a negative SPX YoY return within a year in three episodes since 2015 (n = 3). The analyst's read, logged; SR-65's proxy and V6 test the episodes from the store.
