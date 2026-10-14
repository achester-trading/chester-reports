# W-1.1a — the audit fixes from the Weekly dry run of 12 Oct: session notes

Branch `w-1-1a-audit-fixes` from `main` at 7754d0d (the T3.5 merge). Spec: Ari's
paste of 13 Oct (six items). Inputs: the dry run of 12 Oct 22:21 ET (run
weekly-20261013T021911), as quoted in the paste. That archive is on the box, so
the fixtures rebuild its figures from the paste's quotes
(`tests/fixtures/weekly_run5_2026-10-12.json`). Session A, 13 Oct 2026.

**The first copy of the paste was cut off** partway through "WHAT THE DRY RUN
SHOWED". Ari resent it whole, and this branch is built from the full text.

## Gates run

**Not run:** the full local suite (CI is the validate), and anything on the box.
I ran the gates this branch touches one at a time:

| Gate | Result |
|---|---|
| `validate_audit_fixes` (new) | 51/0 |
| `validate_numeral_audit` | 159/0 (one case changed, below) |
| `validate_figure_budget` | 110/0 (one check changed, below) |
| `validate_edition_consistency` | 14/0 |
| `validate_readability` | 63/0 (the PDF is not validated here: no WeasyPrint) |
| `validate_no_filler` | 19/0 (group E added) |
| `validate_weekly_integrity` | 36/0 |
| `validate_weekly_stack` | 68/0 (fixture aligned, below) |
| `validate_weekly_complete` | 57/0 |
| `validate_weekly_edits` | 89/0 |
| `validate_weekly` | 100/0 (1 skipped) |
| `validate_stack_cadence` | 99/0 |
| `validate_stack` | 66/0 |
| `validate_daily_close` | 102/0 |
| `validate_monthly_frames` | 32/0 |
| `validate_monthly_stack` | 261/0 (three checks changed, below) |
| `validate_monthly` | 350/0 (1 skipped) |
| `validate_prediction_markets` | 52/0 |
| `validate_secrets` | 37/0 |
| `check_registry` | OK |
| `validate_config_refs` | 26/0 (with the new YAML tracked) |
| `validate_gates` | 31/0 |
| `check_library` | 0 failures |

The Makefile carries the new gate. CLAUDE.md now reads fifty-two code gates
(forty-nine Python).

## What each of the six changed

**1. Unit kinds.** The four withheld figures were true. They were typed wrong:
the budget's frames filed them under the keys `priced` and `level`, and the
audit types any field whose name contains "price" or "level" as a price.

- **At the source** (`daily_cascade/figure_budget.py`):
  - Mechanics' cite reads `implied_daily_move_pct` and
    `realized_daily_move_pct`.
  - Ahead's FOMC cite (`fomc_cite`) reads `implied_rate_pct` (3.92%),
    `move_probability_pct` (19%), `move_increment_bp` (25 bp) and `direction`.
  - Each cite also carries `series_kind`.
- **In the audit** (`altdata/numeral_audit.py`):
  - A unit written beside a figure inside a payload string now wins over the
    field's name (`string_types`), as it already did for table cells. So the
    old frames pass too: "0.93% priced" is a percent.
  - The series-kind equivalence is explicit (`KIND_UNITS`). A price-typed value
    whose row declares a yield, rate, spread, probability, implied move or
    volatility may be written as a percent. Its change may be written in bp
    (yield, rate, spread) or pts (probability).
  - The kind comes from the row's `series_kind`, or from its registry `key`
    through the new `series_kinds` block in `metrics_registry.yaml` (36
    series). The vocabulary is `vocabularies.series_kind`. `check_registry`
    holds each kind to the vocabulary and each key to a registered series.
  - A price written as a percent still fails. Every type-conflict message now
    ends "series kind: <kind>", or "none declared".

**2. The book's budget.**

- The book joins Mechanics, What doesn't fit and Ahead as a budgeted frame on
  the Weekly (`figure_budget.book_frame`, `stack_prose.BUDGETED_FRAMES`). The
  read already has its own budgeted frame.
- The cap is the section's computed cap (`section_cap`), not a literal.
- The frame offers the Book Z line first, as one group, then the register's
  counts and the attention table.
- The frame's `cap_note` and the prompt's "THE BOOK'S CAP" state the cap, say
  the line counts as one, and say the tables carry the rest.
- The paragraph count (`figures_cited` / `figure_faults` with `groups`) counts
  the Book Z line's figures once, however many the paragraph copies. On the
  run-5 shape the paragraph counts 2 against 6.

**3. The direction audit** (new, `daily_cascade/direction.py`; lexicon in
`config/direction_lexicon.yaml`; sign conventions in the registry's new
`quote_conventions` block).

- It runs inside `stack_prose.write` beside the other prose checks, and
  withholds with the message style asked for. The run-5 paragraph gives exactly
  "direction audit failed on 1 clause: 'the dollar softened' against DXY
  +0.27%".
- **A currency's direction:** a directional word within three words of a
  currency is read against that currency's own index where the section prints
  one (the dollar's is the DXY). Otherwise it is read against a pair it is
  quoted in, through `quote_conventions`: EUR/USD up = euro firmer and dollar
  softer; USD/JPY up = dollar firmer and yen weaker.
- **A figure's direction:** for a cited figure that matches a change the
  section's tables print, the nearest directional word in its clause must
  agree with the sign. Spreads widen up; curves steepen up.
- **Not checked:**
  - a clause with no directional word;
  - a figure after "to" or "at", which is a level, not a change.

**4. Readability.**

- **(a) The sign after a verb.** `readability.unsign_after_verbs` rewrites a
  signed figure after an agreeing lexicon verb to its unsigned form ("fell -3
  bp" prints "fell 3 bp"). It runs after every audit and counts each rewrite,
  per section in `ed["prose"][sid]["unsigned_rewrites"]` and in total in
  `ed["unsigned_rewrites"]`. A verb that disagrees with its sign is left for
  the direction audit, which has already withheld it.
  - The numeral audit's sign rule accepts the unsigned size after a falling
    verb. Without that, the frame's new rule ("fell 3 bp") would be withheld
    as a dropped sign.
- **(b) Stances.** `readability.stance_faults` flags "bullish" or "bearish" +
  on/about/for + a macro variable (inflation, growth, rates, yields, the
  economy, the labour market, employment, GDP). It also flags "marked broke"
  and "marked held".
- **The rules in the frames.** `stack_prose.RULES` (every section, every
  cadence) now carries:
  - the verb rule;
  - "broke"/"held", never "marked broke";
  - no stance on a macro variable.

**5. A ceiling, not a quota.**

- `stack_prose.CEILING_RULE` closes both `RULES` and `READ_RULES`, so every
  section frame and The read carry it. It is plain text with no format
  placeholder, so the Monthly's templates, which split and reformat `RULES`,
  are unaffected.
- `filler_faults` now also withholds a sentence of six words or fewer carrying
  exactly one figure and no comparison word ("Real Estate added +1.96%.").
  `validate_no_filler` group E holds it.

**6. Derived series and aliases.**

- **Derived series** (`weekly_sections.aligned_legs`): SOFR less IORB, CCC less
  BB and gold over copper each take both legs on the latest date both legs
  have, now and at the period's start, and print that date. The 2s10s is
  already `calc.yield_curve_2s10s`, which `market_features` computes same-day
  only, and its row prints its own as-of.
- **Dates in the frames:** a row's "As of" now travels with its figure into the
  frame (`table_moves` → `cite` → `as_of`).
- **Prose rules:** `RULES` says "the front" and "the front end" mean the 2-year.
  It also says to join two figures in one sentence only where they share an
  as-of, and otherwise to give each its date.
- **Consistency** (`daily_cascade/consistency.py`):
  - `ALIASES` maps one instrument to its series ids: y2, y10, y30 and HY OAS.
  - `reconcile_aliases(ed, charts)` compares the tape's level cells (now tagged
    `level`) with the charts' declared `levels`. At one date they must agree
    within tolerance, else `EditionInconsistent` and exit 5, as ruling 1. At
    different dates they are not compared, and each is logged.
  - A chart caption must carry its source and date. W3's caption now reads
    "10-year 5.28% (FRED, 2026-10-07)", polished to "7 Oct", and W3 declares
    its levels.
  - It runs in `weekly_stack.produce` after the charts are built, before
    anything prints.

## The fixtures

- **The store:** `tests/fixtures/weekly_run5_2026-10-12.json` holds every
  figure the paste quotes: the four unit-kind figures, the book paragraph and
  its Book Z line, the Plumbing paragraph, the signed-after-verb text, the
  stance and "marked broke" lines, the bare sentence, and the two 10-year
  figures.
- **The gate:** `tools/validate_audit_fixes.py` reads that file and holds each
  rule (groups A–F). Two of its checks run the prose pipeline end to end
  against a fake model.
- **The fixture cases, as asked:**
  - **Units:** the four run-5 figures pass, and a price written as a percent
    fails.
  - **The book:** the run-5 book payload comments.
  - **Direction:** "dollar softened" fails, "firmed" passes, and "EUR/USD fell
    0.43%, the dollar firmer" passes.
  - **Filler:** "Real Estate added +1.96%." fails, and the longer sentence
    passes.
  - **Aliases:** 5.244% on 9 Oct against 5.28% on 7 Oct passes, and one date
    with a 4 bp gap fails.

## Found that the paste did not name

1. **"60-40" counted as two figures.** `readability.figures` read the benchmark's
   name as "60" and "40" in every Book Z sentence. That is part of why the book
   counted nine. It is now a name (`_NOT_FIGURES`). In the fixture's rebuild of
   the run-5 paragraph, nine figures by the old count are seven real ones, and
   all seven are in the Book Z line. The archived paragraph would confirm the
   split.
2. **The four figures were not special.** Any frame string under a key
   containing "price", "level" or "mark" typed every number in it as a price,
   including the parent frames' level cites ("level": "4.05%"). The string-unit
   rule in item 1 fixes the class, not the four.
3. **The numeral-audit gate asserted the opposite of item 4.** It held "Gold fell
   6.75%" to be withheld. That case is changed: "fell 6.75%" publishes, while
   "rose 6.75%" for a fall and an unsigned figure with no verb ("Gold's move was
   6.75%") stay withheld. `validate_monthly_stack` held the same rule in three
   checks ("WTI fell 6.03%", "It fell $100bn", "Kalshi's hold fell 14.0
   points"). Each now tests a dropped sign with no verb to carry it ("WTI's move
   was 6.03%", "moved 14.0 points"), which still fails, and the falling-verb form,
   which now passes.
4. **The shared Weekly fixture held two different 10-year yields on one date.**
   `validate_weekly_stack.seed` stored FRED's 10-year at 4.06% on the day the
   tape's bars read 4.289% (and the 30-year at 4.53% against 4.789%): a 23 bp
   gap the alias check correctly refused. The fixture's FRED close now equals
   the tape's. No assertion depended on the old value.
5. **The new rules are shared beyond the Weekly.**
   - **Daily close:** it runs through the same `stack_prose.write`, so the
     direction audit, the stance check, the sign rewrite and the bare-figure
     filler rule apply there too.
   - **Monthly:** its section prose (`monthly_macro/prose.py`) takes the new
     `RULES` text (so its prompts carry the rules), but it calls none of the new
     checks. That is Needs you 3.
6. **The bare-figure rule reaches claim lines.** A terse claim such as "SPY fell
   1.2%." is now filler and is withheld once, then retried with the reason.
   That is Needs you 2.

## Choices made for the operator to overrule

- **Two series of one instrument agree within 3 bp at one date, not at
  printed precision.** ^TNX (the CBOE's close) and DGS10 (the Fed's H.15
  constant maturity) are two measurements and routinely differ by a basis
  point or two on the same day. Printed precision would fail the live run on
  that. A 4 bp gap fails (the fixture). For the Sunday Weekly the two rarely
  share a date anyway, since FRED's Friday arrives on Monday.
- **The currency index wins over the pair.** "The dollar softened" is read
  against the DXY where the section prints it, and only otherwise against
  EUR/USD or USD/JPY. That is the message the paste asked for.
- **The lexicon's extra words.** Besides the paste's list, the lexicon has the
  comparatives (firmer, softer, stronger, weaker, higher, lower), "up" and
  "down" (but not "up front"), and a few verbs (advanced, increased, declined,
  retreated). "The dollar firmer" needs them.
- **Points for a probability's change** are already the price type the audit
  allowed; the explicit table lists them anyway.
- **bp for a change** is allowed against a price-typed value of a bp kind
  whichever way it is signed. Value matching is unchanged.
- **"The front" rule and the date rule sit in the shared `RULES`**, not in a
  Plumbing-only note, so the read and the other sections are held to them too.
- **The stance check** reads "bullish/bearish" + on/about/for/over + a named
  macro variable. "Bullish on equities" is not flagged.

## W-1.2 and W-1.3 after this merges

All three branches merge cleanly onto main alone. Onto this branch they
conflict, and each conflict is resolved by keeping both sides:

- **W-1.2:** one conflict, in `charts.py` (W3's caption).
- **W-1.3a and W-1.3b:** three each.
  - `charts.py`: keep the FRED source and their spans/titles.
  - `stack_prose.py`: the import line and the fault chain, so keep both
    `direction` and `opener_mod`.
  - CLAUDE.md: the gate count, which is the sum.

After the merge, rerun `validate_audit_fixes`, `validate_no_filler` and W-1.3a's
opener gate together, because W-1.3a's opener and the bare-figure rule both
read short sentences.

## Needs you

1. **The alias tolerance.** Keep 3 bp between two series of one instrument on
   one date, or hold them to printed precision (the paste's literal reading,
   which would fail a live run on a 1–2 bp ^TNX/DGS10 difference)? 3 bp /
   printed precision.
2. **The bare-figure rule and claim lines.** It applies to every sentence,
   claim lines included, so "SPY fell 1.2%." as a claim is withheld once and
   retried. Keep / exempt the claim line.
3. **The Monthly's prose path.** The Monthly's prompts now carry the rules, but
   `monthly_macro/prose.py` does not run the direction audit, the stance check
   or the sign rewrite. Wire them in the next tranche? Yes / no.
4. **A Weekly dry run after merge** on the 9 Oct data (yours, on the box) is the
   acceptance for all six. The fixtures rebuild the run-5 figures from the
   paste; only the archived edition can show nothing else in it trips the new
   checks.
