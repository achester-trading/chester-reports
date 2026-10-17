# Narrative register: disagreement pairs

A **disagreement pair** is two published views of one market question, each tied to a stored measure, and adjudicated on a fixed schedule. The signal-triage batches define them (Batch 5 item 26; Batch 6 items 35 and 42). Each entry records:
- the question;
- the two sides, with their named sources;
- the measure that adjudicates between them;
- the review cadence.

**Status.** The narrative register's code (`altdata/narratives.py`) holds stories, and its one human gate is the confirm step for a proposed story. It has no pair kind, so a pair cannot be a pending entry there.

Under the ruling of 16 October 2026, judgment drafts are committed as drafted and listed for Ari's accept-all. That is the status of every entry below until Ari accepts them. A pair does not grade itself and has no decision rights; its monthly adjudication is a line in the Monthly.

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
