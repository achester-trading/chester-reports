# Change Order — Reading shelf: rulings D1–D3 and eight shelf additions

| | |
|---|---|
| Status | **Adopted 2026-10-08 in chat** (Ari: "build me a change order with these additions"); D1–D3 ruled 2026-10-05 09:08–09:10 ET. Apply to `main` (the T2.2 merge is complete). Strike any item below before applying if Ari says so. |
| Amends | `docs/briefs/reading-shelf-brief-2026-10-05.md` (the controlling brief for the Publication watch and the Monthly's Reading chapter), `docs/reading/watchlist.json`, `docs/attention-log.md` |
| Owner | Ari Chester |
| Binding on | The Claude Code session applying this order; the T3 session building the Reading chapter (week of 19 Oct) |
| Precedence | Below Part 26, the change orders, Amendments #3–#5, the reporting-stack brief, the metric-lenses brief and `docs/change-order-jpm-gtm-2026-10-03.md`; equal to and amending the reading-shelf brief. The shelf has no decision rights. |
| Scheduled task | "Publication watch — reading shelf" (12th and 27th, 06:58 ET): its fallback shelf copy was updated 8 Oct 2026 to match §3 below, so this order needs no task change. |

## 1. What this order does

1. Records the three decisions the brief left open, as ruled on 5 Oct.
2. Confirms the summary-paragraph form of the Reading chapter (already in the repo copy of the brief as of 5 Oct 09:03 ET; restated in §2 so an older pasted copy cannot mislead).
3. Adds eight publications to the shelf: Fidelity (two), Bridgewater, PIMCO (two), UBS Year Ahead, Morgan Stanley outlooks, Blackstone Ten Surprises. The shelf goes from 48 items (18 deep / 17 skim / 13 list after D3) to **56 items: 19 deep / 22 skim / 15 list**.
4. Adds the attention-log lines for both rulings.

Nothing here touches code, the store, the Monthly renderer or any other chapter. The T3 build estimate for the chapter stays at about 4 hours.

## 2. Rulings recorded (5 Oct 2026)

| # | Decision | Ruling | Reasoning recorded |
|---|---|---|---|
| D1 | Where the Reading chapter sits in the Monthly's stack | **Immediately after narratives, before ahead** | Outside views sit together; "due next month" leads into ahead. Declined: last chapter after the book; a separate appendix. |
| D2 | Watch cadence | **The 12th and the 27th** | The 27th feeds the 1st compile; the 12th catches the refunding, BIS QR and mid-month releases within a week; two files a month fits the attention budget. Declined: weekly; 10th/20th/28th. |
| D3 | Depth tiers | **ECB and BoE stability reports promoted to deep; Hussman and Pew kept at list** | SR-29 (EU sovereign stress) and the gilt market justify full reads twice a year each. |

Clarification of 5 Oct 08:59 ET, restated: every deep and skim register entry carries a `summary` — a reader's preview paragraph of the document itself (deep 150–250 words, skim 80–150, list items none): what the edition covers, key findings with figures and as-of dates, the authors' argument stated as theirs, what changed from the prior edition, and the two or three exhibits worth the reader's time. Plain text, no stance or recommendation of ours. The Reading chapter prints the hyperlinked title line and then the paragraph verbatim; list items print the title line and the one-liner. The renderer never rewrites or trims a stored summary; the numeral audit does not apply to it.

## 3. Shelf additions

Append these eight objects to the `items` array of `docs/reading/watchlist.json` (keep the file's existing key order and formatting), then set `"version": "2026-10-08"`. Depth counts in the `_about` line are not stored, so nothing else changes in the file.

```json
{"id": "fidelity-qmu", "publication": "Quarterly Market Update (with the monthly Business Cycle Update)", "publisher": "Fidelity Investments, Asset Allocation Research Team", "group": "chartbook", "cadence": "quarterly; business-cycle update monthly", "expected": {"months": [1, 4, 7, 10], "window": "two to three weeks after quarter-end"}, "depth": "skim", "index_url": "https://institutional.fidelity.com/advisors/insights", "feeds": "Business-cycle clock (early/mid/late/recession by country) as a regime lens; chartbook comparison with the JPM GTM; search 'Fidelity Quarterly Market Update' with the quarter. Added by change order 8 Oct 2026."},
{"id": "fidelity-timmer", "publication": "Jurrien Timmer chart posts (Director of Global Macro)", "publisher": "Fidelity Investments", "group": "voices", "cadence": "weekly posts; register the month's most-cited", "expected": {"months": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], "window": "register once a month"}, "depth": "list", "index_url": "https://x.com/TimmerFidelity", "feeds": "Secular-cycle, CAPE-vs-earnings and liquidity reads; voices register. If the posts cannot be fetched, register nothing rather than guess. Added by change order 8 Oct 2026."},
{"id": "bridgewater-research", "publication": "Public research and Ray Dalio's posts", "publisher": "Bridgewater Associates / Ray Dalio", "group": "voices", "cadence": "irregular", "expected": "irregular", "depth": "skim", "index_url": "https://www.bridgewater.com/research-and-insights", "feeds": "Factor IV and the Debt Cycles paper (long-term debt cycle, 'how countries go broke'); Daily Observations is paywalled and is not a source. Added by change order 8 Oct 2026."},
{"id": "pimco-secular", "publication": "Secular Outlook", "publisher": "PIMCO", "group": "plumbing", "cadence": "annual", "expected": {"months": [6], "window": "June, after the May Secular Forum"}, "depth": "deep", "index_url": "https://www.pimco.com/us/en/insights", "feeds": "Rates, term premium, fiscal dominance and the neutral rate over three to five years; plumbing & rates; What's priced. Search 'PIMCO Secular Outlook' with the year. Added by change order 8 Oct 2026."},
{"id": "pimco-cyclical", "publication": "Cyclical Outlook", "publisher": "PIMCO", "group": "plumbing", "cadence": "three to four times a year", "expected": {"months": [1, 4, 7, 10], "window": "irregular within the month"}, "depth": "skim", "index_url": "https://www.pimco.com/us/en/insights", "feeds": "Six-to-twelve-month rates and credit view; plumbing & rates; voices register. Added by change order 8 Oct 2026."},
{"id": "ubs-year-ahead", "publication": "Year Ahead", "publisher": "UBS Global Wealth Management, Chief Investment Office", "group": "chartbook", "cadence": "annual", "expected": {"months": [11], "window": "mid-November"}, "depth": "skim", "index_url": "https://www.ubs.com/global/en/wealth-management/insights/chief-investment-office.html", "feeds": "House view and scenario set for the coming year; voices register; consensus marker. Search 'UBS Year Ahead' with the year. Added by change order 8 Oct 2026."},
{"id": "ms-outlook", "publication": "Global Strategy Mid-Year and Year-Ahead Outlooks (public summaries)", "publisher": "Morgan Stanley Research", "group": "chartbook", "cadence": "semi-annual", "expected": {"months": [5, 6, 11], "window": "mid-May to June; mid-November"}, "depth": "skim", "index_url": "https://www.morganstanley.com/ideas", "feeds": "House view, year-end index targets and rate paths; voices register; consensus marker. Added by change order 8 Oct 2026."},
{"id": "blackstone-ten-surprises", "publication": "Ten Surprises", "publisher": "Blackstone (Joe Zidle, continuing Byron Wien)", "group": "voices", "cadence": "annual", "expected": {"months": [1], "window": "first half of January"}, "depth": "list", "index_url": "https://www.blackstone.com/insights/", "feeds": "January consensus marker — what a large private-markets house calls non-consensus; voices register only. Added by change order 8 Oct 2026."}
```

Also apply D3 in the same file: set `"depth": "deep"` on `ecb-fsr` and `boe-fsr`, and append `; promoted to deep by ruling D3, 5 Oct 2026` to each one's `feeds` string.

## 4. Brief edits (`docs/briefs/reading-shelf-brief-2026-10-05.md`)

1. **Status row** — append after the last sentence: `**Ruled 2026-10-05 09:10 ET in chat:** D1 after narratives, before ahead; D2 the 12th and 27th; D3 ECB and BoE stability reports promoted to deep, Hussman and Pew kept. **Amended 2026-10-08** by docs/change-order-reading-shelf-2026-10-08.md: eight shelf additions; tiers now 19 deep, 22 skim, 15 list across 56 items.`
2. **§2** — replace the heading and table with the §2 table of this order (heading: `## 2. Decisions (ruled in chat, 5 Oct 2026, one at a time)`; columns `# | Decision | Ruling | Reasoning recorded`).
3. **§4, watchlist paragraph** — after "No insurance-industry reporting (ruling 5 Oct 2026)." add: `Eight publications added 8 Oct 2026 (Fidelity QMU and Timmer, Bridgewater/Dalio, PIMCO Secular and Cyclical, UBS Year Ahead, Morgan Stanley outlooks, Blackstone Ten Surprises); the Apollo/Slok daily, BlackRock BII and Vanguard outlooks stay off the shelf.`
4. **§6, the paste** — change `applying the decisions D1–D3 as recorded in the brief's status row (defaults if unruled)` to `applying the decisions D1–D3 as ruled in the brief's §2 (the chapter goes immediately after narratives and before ahead)`.
5. If the pasted copy of the brief predates the 5 Oct 08:59 clarification (no `summary` field in §4's schema), apply the clarification in §2 of this order to §3 item 10, §4 (add the `summary` line to the schema) and §5 (title line plus paragraph), and raise §6's estimate from 3.5 to 4 hours. The repo copy already has these.

## 5. Attention log (`docs/attention-log.md`)

Append two lines, never editing past ones:

```
| 2026-10-05 | ruling | 6 | Reading shelf D1–D3 ruled (09:08–09:10 ET): chapter after narratives; watch on the 12th and 27th; ECB/BoE FSRs promoted to deep |
| 2026-10-08 | ruling | — | Reading shelf: eight publications added (Fidelity ×2, Bridgewater, PIMCO ×2, UBS Year Ahead, Morgan Stanley outlooks, Blackstone Ten Surprises); change order filed |
```

## 6. Apply and verify

1. On `main`, after `git pull`: apply §3, §4 and §5 as written. No other file changes.
2. Verify both JSON files parse and the counts match: `python -c "import json;d=json.load(open('docs/reading/watchlist.json'));import collections;print(len(d['items']),collections.Counter(i['depth'] for i in d['items']))"` → expected `56 Counter({'skim': 22, 'deep': 19, 'list': 15})`; and `python -c "import json;json.load(open('docs/reading/register.json'))"` → no output.
3. Commit as one commit: `Reading shelf: D1-D3 rulings, eight shelf additions, attention log (change order 2026-10-08)`; push `main`.
4. Expected session time: about 20 minutes. First report-back: the verification line from step 2.

## 7. Not changed by this order

The register (`docs/reading/register.json`) — no new editions are registered here; the watch's first run on 12 Oct does that. The scheduled task — already carries the eight items and D3 in its fallback shelf copy (updated 8 Oct 2026). The T3 chapter build — unchanged, about 4 hours, week of 19 Oct, first printing 1 Nov.
