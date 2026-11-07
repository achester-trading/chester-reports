# PROMPT — the Treasury refunding read (publication watch, reading shelf)

Batch 22 item 121 (A134, 7 Nov 2026). The forward TGA-path row in item 17's
block reads the assumed end-of-quarter cash balance of the latest quarterly
refunding **only** from a stored scan. Without one it prints "no refunding read
stored". This file is not a scan (`altdata/scans.py` skips `PROMPT-` files); it
tells the reading-shelf publication watch what to write when a refunding lands
(the first Monday of February, May, August and November, when Treasury posts
"Treasury Announces Marketable Borrowing Estimates").

Write `docs/scans/treasury-refunding-<YYYY>q<N>.md`, the quarter being the
one the statement opens, for the operator to commit. The shape is the scans
ingest's:

```markdown
# Treasury refunding read — <Month YYYY>

**Edition:** Marketable borrowing estimates of <D Month YYYY> — data as of <D Month YYYY>
**Read on:** <D Month YYYY>
**Source:** <the press release's URL on home.treasury.gov>

## 1. Reference table (as of <D Month YYYY, the statement's date>)

| Metric | Value |
|---|---|
| Assumed end-of-<Month> <YYYY> cash balance | $<n> billion |
| Assumed end-of-<Month> <YYYY> cash balance | $<n> trillion |
| Privately-held net marketable borrowing, <Mon>-<Mon> <YYYY> | $<n> billion |
```

Rules:
- **Quote the statement's own figures and words.** One row for each quarter the statement states an assumed end-of-quarter cash balance for. Write the metric exactly as "Assumed end-of-<Month> <YYYY> cash balance": `config/batch5_tranche_1.yaml` `forward_tga.metric_pattern` reads the quarter end from it.
- **Keep the table's own as-of.** It is the statement's date; the row prints it as "the refunding of <date>".
- **Nothing else goes in the reference table.** No reading of the figures, no advice.
- **Nothing is typed into the report by hand.** The figure reaches the report only through `python -m altdata.scans ingest`.
