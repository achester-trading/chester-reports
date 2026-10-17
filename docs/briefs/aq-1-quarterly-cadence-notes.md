# AQ-1 — the quarterly cadence: build notes (10 Oct 2026)

Branch `aq-1-quarterly-cadence`, built from the change order
`docs/change-order-alternative-assets-quarterly-2026-10-10.md`: §3 (one edition,
two paths; how the chapters sit in the stack) and §4.1 (the chapter template).
It is Tranche B, placed by the sitting. Not merged.

## What was built

**The fourth cadence, by configuration (the T2.6 design).**
`config/reporting_stack.yaml` gains the entries below, and
`daily_cascade/cadence.NAMES` now lists the fourth cadence.

- **`cadences: quarterly`.** Its settings:
  - the report is "the Quarterly";
  - the period noun is `quarter` and the column head "The quarter";
  - it uses the depth allowances `depth_words_quarterly`;
  - paragraphs, frames and guards follow the Monthly's shape;
  - there are two budgets: `read_budget` (90-minute target, `on_over: warn`) and
    `reference_budget` (unbudgeted);
  - `trim_to_budget: false`.
- **`budget: quarterly`.** `{words: null, charts: 40}`. That is three charts per
  chapter lead (33) plus the front matter's seven.
- **`reading_targets_minutes`.** Adds `quarterly: 90`.
- **Every front-matter section.** Each gains a `quarterly` depth and a
  `quarterly_tier`. The read section is `lead` and everything else is
  `reference`, because §3 says the read is the executive summary plus the lead
  pages. Reading is the Monthly's only, so it takes no quarterly depth.
- **`quarterly_chapters`.** The eleven families, each with:
  - its weight: deep, light, or `country` for Thailand;
  - its thesis-register family;
  - the correlation layer's asset ids.
- **`quarterly_template`.** The §4.1 items with their numbers, tiers and which
  weights carry them. There are 1 to 11 with 3a, so twelve sub-sections in all.
  - **Lead:** 1 (last quarter's theses, graded), 2 (theses), 3 (the quarter) and
    7 (the falsification tests).
  - **Light chapters:** 1–4, 7, 8 and 10.
  - **Thailand:** everything but 11.

**The run: one runner, not a parallel one.** The command is
`python -m monthly_macro.run --cadence quarterly [--dry-run] [--email]`.

- **The payload.** It is the Monthly's, built with `period="quarter"`:
  `v2.month_bounds` reads the previous calendar quarter, so a 9 Jan 2027 run
  covers 30 Sep to 31 Dec and is labelled 4Q26. Every builder that reads that
  window covers the quarter, and nothing labelled the quarter reads a month.
- **The front matter.** `monthly_macro.stack.build(..., cadence="quarterly")` is
  the Monthly's build: the same builders, `stack.assemble` at the quarterly
  depths, every printed phrase in the quarter's words. It skips the Monthly's
  Slow layers and Reading.
- **The chapters.** `monthly_macro/quarterly.py` builds the eleven chapters as
  the slow layers. Each is a shell on the template: every item prints "not yet
  built — AQ-2" in the stack's existing not-yet-tracked footnote, except the
  three hook items below.
- **The prose.** Written by the Monthly's machinery in the Quarterly's voice
  (`prose.voice`: report name, period, frames from config). The front matter
  gets the stack's sections and blocks; the Monthly v2 long-form sections are not
  asked for.
- **The executive summary.** One paragraph per chapter, built last from the
  finished chapters by `prose.summary_plan(ed, chapters)` and audited the same
  way.
- **Archive names.** `alt_asset_<date>.md`, `.html`, `_payload.json` and
  `_stack.json`. A dry run writes only to `reports/dryrun/`.
- **`--deliver-only`.** Works per cadence. `--from-payload` is refused for the
  Quarterly; there is no re-render yet.

**The hooks.** Each is named, and each degrades to "not yet" when its module is
absent. Neither branch is merged, so on this branch all three items print "not
yet".

| Item | Hook | Module | Tier |
|---|---|---|---|
| 1 · Last quarter's theses, graded | `thesis_graded` | `altdata.thesis_register.graded_table(quarter, family=…)` (AQ-6) | lead |
| 2 · Theses | `thesis_seed` | `altdata.thesis_register.seed_table(…, quarter=next)`, filtered to the chapter's family (AQ-6) | lead |
| 8 · Correlations | `correlation_rows` | `altdata.correlation.peer_table` and the `named` rows' `triple`, for the chapter's assets (AQ-5) | reference |

A hook whose module faults prints "FAULT (code, not data)" and never raises.
AQ-5 exposes no per-chapter function, so the hook builds the chapter's rows from
its peer table and named rows.

**Lead and reference.**
- **Order.** A chapter prints its lead items first, then a divider ("The
  reference"), then its reference items. The renderer gained the divider
  sub-section.
- **The header.** It prints "the read: n min; the whole edition: m min · target
  90 minutes for the read".
- **The read's time.** The executive summary, plus the lead-tier sections, plus
  every chapter's lead items. It counts prose at the house rate (250 words a
  minute, 20 seconds a chart), the same estimate every cadence uses.
- **Over 90 minutes.** The run logs a warning and the edition carries
  `read_warning`; nothing is withheld or cut.

**The state key.** A live run records under `alt_asset` (state/emit.py's
reserved key), with the chapter count and both reading times. A dry run records
nothing, as the Monthly's does.

**The unit and the timer.**
- **The files:** `deploy/systemd/chester-quarterly.service` and `.timer`, plus
  the wrapper `scripts/run_quarterly.sh`. The wrapper has run_monthly.sh's shape,
  with its own lock, status file and heartbeat.
- **The calendar:** `OnCalendar=Sat *-01,04,07,10-08..14 06:00 America/New_York`.
  The second Saturday after a quarter-end is always the second Saturday of
  January, April, July or October. `systemd-analyze calendar` on the box gives
  Sat 9 Jan 2027 06:00 ET first, then 10 Apr, 10 Jul and 9 Oct.
- **Shipped disabled:** the timer is not in `DEPLOY_TIMERS`. The self-deploy
  will copy the unit files but never enable them. The heartbeat watches a
  long-cadence timer only once it is enabled.

**Gate.** `tools/validate_quarterly_stack.py` is in the Makefile's list. It uses
the Monthly stack gate's synthetic store, with the clock at Sat 10 Oct 2026, so
the edition covers 3Q26. It checks:
- the cadence config is present and complete;
- the quarter window;
- **a dry run end to end:** the front matter from the stack and the eleven
  chapter shells, every section and item tiered, lead before reference, the
  summary's paragraph count equal to the chapter count, and the read's time from
  lead items only (3,000 words in a reference item leave it unchanged);
- the 90-minute warning;
- the header line;
- the hooks: absent, present via fixture modules, and faulting;
- the state key: a dry run records nothing and a live run records one;
- the unit and the timer.

## What AQ-2 fills

Every "not yet built — AQ-2" item of every chapter:
- the quarter in five lines with its three charts and the driver attribution;
- what's priced;
- structure;
- supply and demand;
- the analyses;
- the falsification-test lines;
- the emerging stories;
- the book (the draft slate);
- the ten questions.

Also AQ-2's:
- the confidence line and the what-changed line on each lead page;
- the coin page;
- the transmission map, and the rest of the front matter's charts (the horizon
  bars and the quilt are AQ-4, the heatmaps AQ-5);
- **threading the cadence's `Period` through each Monthly builder.** In AQ-1 the
  front matter's period words come from a text pass (`stack.period_words`), the
  same mechanism the module already uses to turn the Weekly's words into the
  Monthly's. The window under them is genuinely the quarter.

The Quarterly prints no charts yet (`chart_count` 0).

## Choices made in the build, for the operator to overrule

1. **The front matter's tiers:** the read is lead and everything else is
   reference. That follows from §3 (the read is the summary plus the chapters'
   lead pages); it is one key per section in config.
2. **Thailand's weight is `country`:** the full template less item 11, its
   isolation unchanged. Thailand's book item is AQ-2's.
3. **China is its own chapter beside EM:** as the brief lists it, deep, with
   assets `china` and `cny`.
4. **Light chapters' item 3a:** §4.1's "items 1–4" is read as including 3a,
   which sits between 3 and 4.
5. **Credit and Thailand carry no correlation assets:** AQ-5's universe has no
   credit or Thai asset, so their item 8 says so.

## For the operator

- **Enable the timer** after the December dry run, inside a window (box, by hand):
  ```
  systemctl --user enable --now chester-quarterly.timer
  ```
- **The December dry run on the box** (the operator's):
  ```
  cd ~/chester-reports
  .venv/bin/python -m monthly_macro.run --cadence quarterly --dry-run
  ```
  Add `--email` to receive it once under "[DRY RUN]". It writes only to
  `reports/dryrun/` and records no state.
- **To rule at the dry run:**
  - the chart cap (40, set in `budget: quarterly`);
  - the read's 90-minute target (`reading_targets_minutes: quarterly` and
    `cadences: quarterly: read_budget`);
  - the front matter's quarterly depths and tiers.
