# SR-37 and SR-38 — the AI FCF-transfer panel and the return attribution: session notes

Branch `sr-37-38-ai-fcf` from `origin/sr-43-49-rates-anchor` (8c07ab0). Spec:
signal-triage batch 4 (`docs/change-order-signal-triage-batch-4-2026-10-06.md`):

- the SR-37 and SR-38 entries;
- work rows ST4-01 and ST4-02;
- §6 placement.

The agenda for Audit #4 (`docs/briefs/audit-4-agenda.md`): Part III row 4, and
decision 8 (pulled ahead; the test dates are the late-October hyperscaler prints
and the 28 Oct FOMC).

Session A, 13 Oct 2026.

## Gates run

**Not run:** the full local suite (CI is the validate), and anything on the box.
I ran the gates this branch touches one at a time; all are green:

| Gate | Result |
|---|---|
| `validate_ai_fcf` (new) | 27/0 |
| `validate_official_sources` (the fundamentals writer) | 249/0 |
| `check_registry` | OK |
| `validate_config_refs` | 28/0 (with the new YAML tracked) |
| `validate_weekly_stack` | 68/0 |
| `validate_weekly_edits` | 89/0 |
| `validate_weekly_complete` | 56/0 |
| `validate_weekly` | 100/0 (1 skipped) |
| `validate_figure_budget` | 79/0 |
| `validate_readability` | 63/0 (the PDF is not validated here: no WeasyPrint) |
| `validate_stack_cadence` | 99/0 |
| `validate_monthly_stack` | 261/0 |
| `validate_monthly` | 350/0 (1 skipped) |
| `validate_rates_anchors` | 23/0 |
| `validate_gates` | 31/0 |
| `check_library` | 0 failures |

The Makefile carries the new gate. CLAUDE.md on this branch now reads fifty
code gates.

## What was built

**SR-37, the AI FCF-transfer panel** (`altdata/ai_fcf.py`,
`config/ai_fcf.yaml`).

- **The names.** The five hyperscalers (AMZN, GOOGL, META, MSFT, ORCL) and the
  four semiconductor names (NVDA, MU, AVGO, AMAT).
- **The source.** The quarterly cash-flow statements the fundamentals writer
  already stores (`yfinance.fund_<ticker>_operating_cash_flow` and `_capex`).
  The writer now also pulls NVDA, AVGO and AMAT; their twelve registry entries
  are added, none trigger-eligible.
- **Per name:** trailing twelve months from the latest four *consecutive*
  reported quarters (fiscal calendars kept):
  - FCF = operating cash flow + capex, with capex as published (negative);
  - the TTM one quarter earlier, where five quarters are stored.
- **Per side:** the sums, printed only when every name of the side is read;
  otherwise "k of n carry four reported quarters (missing …)".
- **Also printed:**
  - capex as a share of the hyperscalers' operating cash flow;
  - the semis' FCF over the hyperscalers' ("not defined" while the latter is at
    or below zero);
  - the defined state "hyperscaler aggregate free cash flow below zero: yes /
    no";
  - one row per name.
- **Labelled trailing** (batch-4 decision 2 as recommended). The source chart's
  forward series (BofA, via a16z Growth) is named as having no free feed.

**SR-38, the return attribution, the revision line, EY minus the bill**
(`altdata/return_attribution.py`).

- **The split:** ln(P1/P0) = ln(E1/E0) + ln(M1/M0), over the 12 months to the
  latest month the earnings are stored for. It uses Shiller's monthly S&P
  Composite price and trailing earnings, already stored, and is **labelled
  trailing**. It prints the price return, the earnings growth, the multiple's
  change, the P/E at each end, and earnings' share of the return in logs.
- **EY minus the 3-month bill:** the trailing earnings yield at the S&P 500's
  last close (^GSPC) against its latest trailing earnings, less DTB3, in
  percentage points.
- **The revision line.** The index's forward estimate is absent (below). The
  nine names' own consensus is logged nightly (`yf.forward_eps`). So the line
  prints their 4- and 13-week changes and the median, labelled "the nine AI
  names' consensus (not the index's)", with each window's coverage counted.
- **Named absent, each with its reason:**
  - **The forward split:** S&P DJI's EPS-estimates spreadsheet answers every
    non-browser client with a 403, and a writer never passes for a browser
    (CLAUDE.md's AAII rule).
  - **EY minus Baa:** no Baa yield is stored.
  - **The AI complex's share of the index return:** no index weights are
    stored, and eight of the nine names' closes are not in the price basket.

**Where it prints**, as the entries place it (§5, and §6's table):

| Block | Section | Cadence |
|---|---|---|
| The revision line | Mechanics | Weekly |
| The FCF panel and the revision line | Mechanics | Monthly |
| The attribution and EY minus the bill | What's priced | Monthly |

- **The tag.** Every printed line carries "(descriptive; unvalidated, n=0)".
- **Format.** Each block is code-written, with no paragraph of its own.
- **Through the budget.** The printed figures ride in the section's data, so
  they reach the prose frame.
- **Rights.** Report-only: neither module reads or writes the market-state
  object, and nothing is a trigger or a book rule.

## Choices made for the operator to overrule

- **Placement follows the entries, not the paste.** The paste says Positioning
  & flows or Plumbing & rates, "as the entries place them". The entries place
  SR-37 in Mechanics and SR-38 in What's priced and Mechanics, and that is what
  is built. (Needs you 1.)
- **The attribution is the entry's, not the paste's.** The paste describes "what
  share of the index's return the AI complex explains". SR-38 specifies the
  earnings-against-multiple split. The entry's lens is built; the AI-complex
  share is named absent. (Needs you 2.)
- **Trailing earnings for the split.** The entry's forward split needs S&P DJI's
  forward EPS. The trailing split uses Shiller's file, which lags by a few
  months, so it reads "to June 2026" or similar, dated on the line. It is the
  same trailing-then-forward path decision 2 recommends for SR-37.
- **Sums only when a side is complete.** A partial sum of four of five
  hyperscalers would read as the aggregate and would understate the transfer.
- **The TTM needs consecutive quarters.** A gap of more than 100 days in the
  latest four refuses that name's TTM: three quarters do not stand in for four.
- **The SR-37 panel is Monthly only,** as the entry places it. The late-October
  prints land in the stored quarters as they file. The Monthly of 1 Nov reads
  them, and so does the Weekly once placed there (Needs you 5).

## Needs you

1. **Placement.** The paste says the blocks print in Positioning & flows or
   Plumbing & rates "as the entries place them". The entries place them
   elsewhere, and that is what is built:
   - SR-37's panel in Mechanics (Monthly);
   - SR-38's attribution and EY minus the bill in What's priced (Monthly);
   - SR-38's revision line in Mechanics (Weekly).

   Keep the entries' placement / move them (name where).
2. **The attribution's meaning.** The paste reads it as the AI complex's share of
   the index return; SR-38 reads it as the earnings-against-multiple split. The
   entry's split is built. The AI-complex share needs two things the store does
   not hold:
   - index weights;
   - the closes of eight of the nine names (only NVDA is in the price basket).

   Keep the entry's lens / also build the AI share (adds the eight names to the
   price basket and needs a weights source).
3. **The forward EPS source.** S&P DJI's spreadsheet refuses non-browser
   clients, so the forward split and the index revision line are absent. Two
   ways to get them:
   - an inbox reader like AAII's (you download `sp-500-eps-est.xlsx` into
     `~/chester-data/inbox/spdji` monthly; a reader parses it);
   - stay trailing until a free feed exists.

   Inbox / trailing.
4. **Three names join the fundamentals pull** (NVDA, AVGO, AMAT; twelve
   registry entries). They reach the box at the next pull after merge. Yes /
   no.
5. **The FCF panel in the Weekly.** The entry places it in the Monthly. The
   test dates are the late-October hyperscaler prints, which the Weekly of
   1 Nov would see first. Print it in the Weekly's Mechanics as well / Monthly
   only.
