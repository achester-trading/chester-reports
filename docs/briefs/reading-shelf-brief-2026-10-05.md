# Reading shelf brief — the Publication watch and the Monthly's Reading chapter

| | |
|---|---|
| Status | Drafted 2026-10-05 in answer to "pull and read these as they are published; consider what emerging themes, new insights or new analytics to add; list them in their own chapter of the Monthly with hyperlinks; skip the insurance reporting." The scheduled task exists (created 5 Oct); the chapter is built in **T3, second half** (week of 19 Oct) and first prints in the **1 Nov Monthly**. Three decisions below are taken in chat. |
| Owner | Ari Chester |
| Binding on | The scheduled task "Publication watch — reading shelf"; the Claude Code session building T3's second half; Phase B (voices) |
| Precedence | Below Part 26, the change orders, Amendments #3–#5, the reporting-stack brief, the metric-lenses brief and `docs/change-order-jpm-gtm-2026-10-03.md`. The shelf has no decision rights. A publication's figures print in the Monthly only as sourced figures (URL stored); a publication's recommendations never print; the watch's own recommendations never print — they are governance candidates ruled in chat. |

## 1. What this is

A standing mechanism with two halves.

**The watch.** A scheduled task fires twice a month (the 12th and the 27th, 06:58 ET, cloud-only, web sources only). It checks the shelf — the publications in `docs/reading/watchlist.json` — for editions published since the register's last entry for each, reads the new ones to the depth the watchlist sets, and delivers one file, `docs/scans/reading-watch-YYYY-MM-DD.md`, plus a short chat summary. The file carries the reads, the framework candidates in the signal-triage intake template, an emerging-themes roll-up, the new analytics seen, voices entries, and — as a fenced JSON block at the end — the register additions. Ari places the file in `docs/scans/` and commits, as with the other scans.

**The chapter.** The Monthly gains a chapter, **Reading**, rendered from `docs/reading/register.json`: every shelf edition published in the Monthly's month, hyperlinked, with its publisher, date, a **summary paragraph** of the report's key findings and major themes (so the reader knows what to expect before opening it), and a link to its scan where one exists; then the shelf items due before the next Monthly. Nothing else — no candidates, no rulings, no stance of ours. (Clarified 5 Oct 2026 08:59 ET: a robust paragraph per report, not a one-liner.)

The JPM Guide to the Markets keeps its own deep-read task; the watch registers each GTM edition and links the scan.

## 2. Decisions (taken in chat, one at a time)

| # | Decision | Default applied until ruled | Alternative |
|---|---|---|---|
| D1 | Where the Reading chapter sits in the Monthly's stack | Immediately after **narratives** (the voices register's chapter) and before **ahead** — the two chapters that carry outside views sit together, and "due next month" leads naturally into ahead | Last chapter, after **the book**, as a slow layer |
| D2 | Watch cadence | **12th and 27th** — the 27th run catches month-end publications ahead of the 1st compile; the 12th catches the refunding (first Wednesday), BIS QR and most mid-month releases within a week | Weekly (Wednesdays): tighter "as published", four files a month to place instead of two |
| D3 | Depth tiers as set in the watchlist | 16 deep, 18 skim, 13 list, as filed | Promote ECB/BoE FSRs to deep; drop Hussman and Pew from the shelf |

## 3. The watch — output contract

File name `reading-watch-YYYY-MM-DD.md` (the run date). Sections, in order:

1. **Bottom line** (≤150 words): what was published since the last run, and the one or two themes that recur across sources.
2. **Reads** — one subsection per deep item: *The read* (≤200 words, desk register, specific figures with as-of dates); *What's new in this edition* (chapters, exhibits, measures or definitions added, retired or changed versus the prior edition — a new exhibit from a major desk is itself a signal of what they think matters); *Candidates* (0–3, in the intake template: Source · Claim as shown · Claim as logged · Measure (series, definition, windows: five-year plus a per-family long window) · Rights (narrow flag / modifier / base-rate row / voices entry / disagreement entry / discard) · Wiring (stack section and report) · Gate · Proposed ruling: ADOPT (new SR, provisional number) / AMEND SR-nn or GTM-nn / LOG ONLY / DISCARD).
3. **Skims** — one paragraph per skim item: what it says, what changed from the prior edition, whether anything merits a candidate (if so, the template).
4. **Listed** — a table for list items: publication · edition · published · URL · the headline figures that matter to the framework (for Z.1: household equity allocation share; for SLOOS: net tightening by category; for the FMS: cash level, most-crowded trade, biggest tail risk; and so on).
5. **Emerging themes** — any theme appearing in two or more shelf sources in this run or across the last three runs: the theme in one line, the sources, which Disruptive Themes factor or stack section it belongs to, whether the framework already carries it (SR or GTM number), and a proposed treatment — theme-watch entry (TW-n, provisional) / new analytic / amendment / none. The watch does not score themes; it proposes.
6. **New analytics seen** — measures, decompositions or exhibits in these publications that the framework lacks and could compute: the measure, who publishes it, the data it needs and whether that data is free (FRED, yfinance, a public sheet) or by hand, and the stack section it would serve. Each becomes a candidate or a LOG line.
7. **Voices** — one entry per letter or desk note read: name, outlet, date, stance in one line, status versus the prior edition (new / unchanged / shifted, and how). Sourced; under "no stored source, not printed".
8. **Due before the next run** — shelf items whose expected window falls before the next run date, with the index URL.
9. **Sources** — markdown links to everything used.
10. **Register additions** — a fenced block tagged `json reading-register-additions`: an array of register entries (schema in §4) for every edition found, at every depth, including editions found but not read (status `listed`). For every deep and skim item the entry carries the **summary** paragraph that the Monthly prints: deep 150–250 words, skim 80–150 words, list items none (the `line` only). The summary is a reader's preview of the document itself — what this edition covers, its key findings with the specific figures and their as-of dates, its major themes and the argument the authors make (stated as theirs: "the BIS argues…"), what changed from the prior edition, and the two or three exhibits or sections worth the reader's time. Desk register, plain declaratives, no bullets, no markdown. It carries no stance, recommendation or candidate of ours — those live in the watch file, never in the register.

Rules carried from the other scans: paraphrase, at most one quote under 15 words per source; every figure carries its as-of date; no trade ideas, no position advice; nothing in the file has decision rights; say in a few words when a source could not be reached rather than guessing; web sources only — no email, Drive, Docs or any personal or connected data source; the task does not write to the repository, create change orders, docs or artifacts, write to memory or schedule anything. Rulings are taken in chat; adopted items become that month's change-order batch, numbered with the signal-triage register (SR-36 onward, assigned at the audit that places the batch).

## 4. The register and the watchlist

`docs/reading/watchlist.json` — the shelf. One object per publication: `id`, `publication`, `publisher`, `group` (chartbook · plumbing · history · positioning · ai · internal-order · voices), `cadence`, `expected` (months and the usual window, or "irregular"), `depth` (deep · skim · list), `index_url`, `feeds` (what in the framework it serves). Editing this file edits the shelf; the task carries a copy as its fallback and prefers the repo's when it can read it. No insurance-industry reporting (ruling 5 Oct 2026).

`docs/reading/register.json` — the editions. One object per edition:

```
id            <watch_id>-<edition>, e.g. fed-fsr-2026-11
watch_id      the watchlist id
publication   title with edition, as printed
publisher
group         copied from the watchlist
edition       e.g. "November 2026", "4Q 2026", "2027"
as_of         data as-of date, or null
published     publication date (the date the information became available)
url           the document's URL — required to print
read_on       date read, or null
scan          docs/scans/<file>.md[#anchor], or null
status        read | listed | pending
line          one sentence, desk register, no stance (prints for list items; the summary's lead elsewhere)
summary       the preview paragraph (deep 150–250 words, skim 80–150, null for list items) — key findings with
              figures and as-of dates, major themes, the authors' argument as theirs, what changed from the prior
              edition, which exhibits to read; plain text, no stance or recommendation of ours
themes        [] — short tags
candidates    [] — candidate ids raised from it
```

Entries are never deleted; a corrected entry supersedes with a new id suffix. `tools/reading_register.py add docs/scans/reading-watch-YYYY-MM-DD.md` extracts the JSON block and appends entries whose id is not already present; `tools/reading_register.py check` validates both files (ids unique, every printed entry has a URL, every watch_id exists, dates parse) and runs under `make validate`.

## 5. The Reading chapter — rendering spec (T3)

Title: **Reading**. Placement per D1. Rendered in both the Markdown and the HTML editions of the Monthly from `docs/reading/register.json` and `docs/reading/watchlist.json`, with no LLM call.

**Published this month.** Entries with `published` in (previous Monthly's as-of, this Monthly's as-of], status `read` or `listed`, grouped by `group` in the watchlist's group order. An entry with a `summary` renders as a title line and a paragraph:

> **[publication](url)** — publisher · published D Mon YYYY (data as of D Mon YYYY where `as_of` differs) · [scan](scan) where a scan exists
>
> *summary paragraph, as stored*

An entry without a `summary` (list depth) renders as the title line followed by *line* on the same line. The GTM entry links its own scan and carries the summary the GTM task's scan provides. An entry without a URL is not printed, and the chapter's footnote counts how many were withheld ("1 entry withheld: no stored source"). No candidates, rulings, themes or stances print here; `themes` may print as plain tags under the paragraph if D1's ruling says so — default off. The summary is stored text, printed verbatim: the renderer escapes it, never rewrites it, and the numeral audit does not apply to it (its figures are the publication's, carried with their as-of dates).

**Due before the next Monthly.** From the watchlist: items whose expected window falls in the coming month, as `publication — publisher (usual window)`, linked to `index_url`. Irregular items are not listed.

**Gates.** `tools/reading_register.py check` in `make validate`; the numeral audit does not apply (no figures are generated here); the chapter must render with an empty month (prints "Nothing on the shelf was published this month." and the due list).

Reading time: with summaries, a typical month (five to ten editions) runs 1,000–2,000 words — five to eight minutes inside the Monthly's forty. A heavy month (April and October, when the IMF, BoJ, Fed and chartbook editions cluster) may double that; the chapter prints the chartbook and plumbing groups first so the reader can stop.

## 6. Build

In T3's second half (week of 19 Oct), about **4 hours** of session time: the two JSON files and their loader (0.5 h), `tools/reading_register.py add|check` with its `make validate` hook, including the summary-length check by depth (1 h), the chapter renderer for Markdown and HTML with the title-plus-paragraph form, the withheld-count footnote and the empty-month case (2 h), a fixture-month test and the dry-run check (0.5 h). No new data sources, no LLM call, no store writes.

The paste for that session (Ari's own line goes on top; expected run time about 4 hours of session work, first report-back after about an hour):

```
Read docs/briefs/reading-shelf-brief-2026-10-05.md in full, then build §4 and §5 exactly as specified, applying the decisions D1–D3 as recorded in the brief's status row (defaults if unruled). Create tools/reading_register.py with `add <watch-file>` and `check` (ids unique, URL present on every printable entry, watch_id exists, dates parse, summary present for deep and skim items and absent for list items, summary within the length bands), wire `check` into make validate, and add the Reading chapter to the Monthly renderer in both editions, placed per D1: title line plus the stored summary paragraph for entries that carry one, title line plus the one-liner for list items, the withheld-count footnote, the due-next-month list, and the empty-month case. Use docs/reading/register.json and docs/reading/watchlist.json as committed. Test against a fixture month containing the jpm-gtm-2026q4 entry (which carries a summary) and against an empty month. Do not call any LLM for this chapter, do not rewrite or trim stored summaries, do not touch the store, and do not change any other chapter. Report back after the loader and tool are in with the gate passing, then after the renderer, with the rendered chapter for the fixture month pasted in the report.
```

## 7. Standing rules

- The shelf is read for the framework's benefit; it does not trade. No entry, theme or analytic gains rights except through a ruling in chat and the register.
- A theme the watch raises twice without a ruling stays a proposal; it is not escalated by repetition.
- The watch's reads are inputs to the Monthly signal scan on the 25th, not a replacement for it; the two may cite each other.
- Insurance and reinsurance reporting stays off the shelf unless Ari puts it on.
- After each run, Ari places the watch file and runs `tools/reading_register.py add`; until the tool exists (T3), entries are added by hand or wait.
