# B98 notes: the K&S family registry, family_ref, two leakage cases

Paste B98 (`docs/pastes/B98.md`), 31 Oct 2026. Branch `b98-ks-family-registry`,
base origin/b86-chain-8-assembly at `4e6814df`. Batch 19 item 99, accepted 27 Oct.
Merges after chain-8.

## The source, as read (31 Oct 2026)

- **SSRN** (`https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3247865`)
  answered HTTP 403 to the fetch, so the English PDF could not be read from it.
- **The contents** were read from the authors' own full Spanish edition,
  arXiv:1912.04492 (`https://arxiv.org/abs/1912.04492`). Its front matter says
  it is the translation of the English edition, and it numbers the same 20
  chapters and their sections. The text was extracted from the PDF's content
  streams; there was no PDF reader on the laptop.
- **Titles.** `title` in the registry is the section title put into English;
  `title_es` is the Spanish title as extracted. Re-read the English titles
  against the SSRN PDF when it is reachable. The section numbers are the
  paper's own.

## What is built

- **`config/alpha_families.yaml`: 63 entries.**
  - 61 K&S sections the lab could use, from chapters 3 (stocks), 4 (ETFs),
    5 (fixed income), 6 (indexes), 7 (volatility), 8 (FX), 9 (commodities),
    10 (futures), 14 (miscellaneous: TIPS, weather), 18 (crypto) and 19 (global
    macro).
  - Each entry has its section, title, a one-line house description and its
    asset classes.
  - Two house entries are marked `house: true`: `KS options` (item 100's premium
    sleeve) and `liquidity-sweep` (item 101(b)).
  - **Left out:** chapter 2's option structures (an options idea takes
    `KS options`), and structured assets, convertibles, tax arbitrage,
    distressed, real estate, cash and infrastructure, which the store does not
    hold. The overview sections ("Generalidades") are not strategies and are
    also out.
- **`family_ref`, an optional hypothesis field** (`alpha/hypotheses.py`
  `HYP_OPTIONAL`). A value not in the registry is refused.
  - It is **required on every hypothesis of an inbox batch** (the weekly-brief
    and sitting channels) written from **1 Nov 2026 00:00 ET**
    (`FAMILY_REF_REQUIRED_FROM`).
  - The daily proposer is not held to it yet: its prompt does not ask for the
    field (see "For the operator").
- **`alpha/families.py`** reads the registry. `family_ref_of(h)` is the
  hypothesis's own field, or its assignment; `count_key(h)` is what it is
  counted under.

## Deviation: the registered files are not edited

The paste asked for a `family_ref` line in each inbox and roster YAML. That
would change registered files:
- The first batch, `tests/fixtures/alpha/inbox/hypotheses-2026-10-14.yaml`, is
  pinned by its sha256. The five H-001 to H-005 translations bind to it, and
  validate_alpha, validate_alpha_proposer and validate_b48_scoreboard check the
  pin.
- The superseding batch, the B59 batch and the four rosters were registered on
  the box by manifest. A changed file is no longer the batch the register
  recorded.

So the assignments are in the registry's `assignments:` list, keyed by
(batch_id, local_id). Not a byte of a registered file changes, and the
superseding batch's H-001 to H-005 carry the same refs as the batch they
supersede. From the next batch on, each hypothesis carries `family_ref` itself.

## Where the count is computed, and what changed

- **The counter.** The count is `alpha/ledger.py`'s
  `variant_count` / `bump_variant`, over the `variant_counts` table, keyed by a
  family string.
- **The callers that count a hypothesis now pass `families.count_key(h)`.**
  Only the key they group by changed:
  - `hypotheses.Register.register`: the bump at registration (10.2 c);
  - `budget_errors`: the weekly brief's two-per-family-per-batch budget;
  - `family_week_count`: the proposer's weekly family count, which also
    matches a hypothesis whose spec carries the ref;
  - `alpha/loops/weekly.py` `_grammar_extend`: the deflated Sharpe's N;
  - `alpha/research/workbench.py` `run`: a grammar rule's counted variants,
    and so the N its validation run is deflated by, which RAS reads too.
- **No trial is lost.** A `family_ref` with no stored row yet starts from the
  counts stored under the old families its hypotheses came from
  (`variant_count`'s fallback).
- **A split family over-counts.** Where an old family split across refs (for
  example `events`: §19.5, §3.2 and §7.4), each ref starts from that family's
  whole count. That deflates harder, never softer.
- **Unchanged:** an engine's own re-fits (`weekly.refit`, `validate.walk_forward`,
  `run_engine`'s grid) and the grammar search still count under the engine
  family or `search-v1`, until an engine carries a `family_ref` (B99's will).
- **Three existing checks re-keyed.** Each read a hypothesis's count under the
  old family name. They now read it under the hypothesis's `count_key`; the
  assertion is the same:
  - validate_alpha group N, "registering counts one variant in each family";
  - validate_alpha group P, H-004's "N n0 -> n0+1" and "a re-run counts
    nothing new";
  - validate_alpha_lab_4, E-6's "counts nothing beyond the registration's one".
- **The one-to-one fixture.** validate_alpha group W builds a registry that
  maps each old family to its own ref. It registers all 24 hypotheses, and the
  counts by ref equal the counts by old family (15 families, 24 variants).

## The assignment table (24 hypotheses)

| Batch | Hypothesis | family | family_ref | Reason |
|---|---|---|---|---|
| 2026-10-14 weekly-01 and its 2026-10-20 supersession | H-001 CPI-day straddle | event-vol | KS §7.4 volatility risk premium | Sells an iron fly into the print; the mechanism names an event premium earned more often than paid. §2.45 (the structure) and §19.5 (the announcement) also fit, but the mechanism names the premium |
| same | H-002 Defensive leadership in an up week | rotation-tell | KS §4.1 sector momentum rotation | The signal is which sector ETFs lead the week; K&S's sector-leadership family |
| same | H-003 Dealer gamma decides which pivot works | pivot-regime | KS §3.14 support and resistance | Tests the scanner's level setups (failed breakdowns against breakouts) by gamma regime; the setups are the level family. The mean-reversion reading (§3.9) is the conditioning, not the trade |
| same | H-004 Credit quality split | credit-quality | KS §19.4 global fixed-income strategy | Times HYG against IEF on a spread signal. A weak fit: K&S has no credit-spread timing section, and §19.4 is the nearest (bond and credit exposure set by macro and spread signals) |
| same | H-005 Term premium sets the direction | rates-trend | KS §19.2 fundamental macro momentum | TLT's direction from the driver of the yield move (term premium against the rate path); the mechanism names a fundamental driver's persistence |
| 2026-10-24 b59 | H-B59-1 Conflict surge, then volatility | geopolitical-attention | KS §19.5 economic announcements | Dated news-event counts trading volatility. K&S's only news section, §18.3, is crypto sentiment; §19.5 is the event-driven macro family |
| same | H-B59-2 A cold week lifts natural gas | weather-demand | KS §14.3 weather risk | Degree-day demand against gas: the section's own subject |
| same | H-B59-3 Model releases, then semis lag | ai-release-watch | KS §19.5 economic announcements | A dated count of public releases trading a relative move; event-driven, like H-B59-1 |
| 2026-10-14 roster | E-1 Defined-risk short volatility, long gamma | vrp | KS §7.4 volatility risk premium | The mechanism is the volatility premium; the dealer regime conditions it |
| same | E-2a Time-series momentum | trend | KS §4.6 multi-asset trend following | Each tradable's own past return across a multi-asset ETF basket (time series, not ranked) |
| same | E-2b Ranked momentum | trend | KS §3.1 price momentum | Winners against losers by ranked trailing return (cross-sectional) |
| same | E-3 Prediction markets converge on futures | pm-futures | KS §6.2 cash and carry arbitrage | Two prices for one outcome converge; K&S's convergence-of-two-prices family. A weak fit: no K&S section prices event contracts |
| 2026-10-17 roster | E-4a CPI or payroll drift | events | KS §19.5 economic announcements | The section's own subject |
| same | E-4b FOMC drift with positioning | events | KS §19.5 economic announcements | A scheduled announcement's next-session drift |
| same | E-4c Earnings drift in the 29 names | events | KS §3.2 earnings momentum | Post-announcement drift: the section's own subject |
| same | E-4d Volatility crush after a print | events | KS §7.4 volatility risk premium | Sells the event's implied volatility; the premium family |
| same | E-5 Delta-neutral perp funding | carry | KS §6.2 cash and carry arbitrage | Short perpetual against long spot, collecting the basis and funding: cash and carry |
| 2026-10-19 engine-6 | E-6 2.5 sigma prints fade | reversion | KS §10.3 contrarian trading | Each series fades its own extreme move (time series); not §3.9's cross-sectional demeaning |
| 2026-10-19 engine-7 | E-7 09:45 gamma regime and the open's sign | intraday_dealer | KS §10.3 contrarian trading | Continue-or-reverse conditioned on market activity (the dealers' hedging), §10.3.1's variant; the gamma regime is the activity measure |

H-001 to H-005 appear twice, under the batch and its supersession, with the same
refs: 24 rows in all.

## The rules doc and the paper

- **`docs/alpha-lab-rules.md` section 15, "Families."** It states the registry,
  the required `family_ref` from the next inbox batch, the count keyed on it and
  the two leakage cases.
  - There was no section named a leakage list. The two cases start one, each
    stated as a breach of section 5, Point-in-time.
  - **HP-filter look-ahead:** the two-sided trend at day t is solved over the
    whole sample, so it moves when later days arrive. The grammar has no HP
    transform.
  - **The unfinished candle:** a bar's close is not known until the bar has
    closed and been stored. A `this_close` rule decides at 15:50 ET and reads
    yesterday's close, and a run whose reads post-date its decision is void.
- **The paper.** The order's "XVIII" is item 91(e)'s *Building and Validating a
  Systematic Book*, which the library guide numbers **XIX**. The guide is
  canonical for numerals, and its XVIII is *The Operating Doctrine*.
  - The paper had no reference list, and ML4T was not in it on any branch:
    item 91(e)'s "brief amendment, by hand" was never made.
  - So a "References" list is appended after its appendix, with both entries:
    ML4T (item 91(e)) and K&S (item 99(c)). No sentence in the body changes.
  - Its HTML edition was rebuilt, since check_library refuses a stale build.

## Gates (one at a time, on this branch)

| Gate | Tally |
|---|---|
| validate_alpha | 271 passed, 0 failed (group W new, 14 checks; three checks re-keyed) |
| validate_alpha_lab_4 | 65 passed, 0 failed (one check re-keyed) |
| validate_alpha_lab_3 | 65 passed, 0 failed |
| validate_alpha_proposer | 42 passed, 0 failed |
| validate_alpha_no_orders | 74 passed, 0 failed |
| validate_b45_chain3 | 29 passed, 0 failed |
| check_library | 27 papers, 0 failures, 0 warnings |
| check_registry | OK |

**Group W** covers:
- the registry's shape and the two house entries;
- all 24 hypotheses mapped, and the registered files unchanged;
- `family_ref` validated, and required from the cutover;
- the one-to-one fixture, and the carry-over;
- the HP filter's look-ahead shown on a random walk (the two-sided trend at day
  200 moves by 1.16 when later days arrive), with the grammar refusing an HP
  transform;
- the unfinished candle read at 15:50 ET against 17:40, and voided by
  `check_pit`;
- the rules doc's section.

## For the operator

- **The daily proposer.** Its prompt does not yet ask for `family_ref`, so its
  ideas count under their `family` until it does. A one-line prompt change is
  for a later paste: it changes the prompt's version.
- **On the box.** The box's stored counts under the old families stay as they
  are and are never rewritten. Each ref's first count starts from them.
- **Weak fits.** H-004 (§19.4) and E-3 (§6.2) are named in the table above. A
  ruling may move either.
