# A66: the hyperscalers' capex guidance from their filings (items 26 and 63), 24 Oct 2026 overnight

This adds the hyperscalers' forward-looking capex GUIDANCE as a sourced record, read from their own 10-Q and 10-K filings. Two existing reads are filled from it:
- item 63's capex-chain line ("Against it, the hyperscalers' filed capex");
- item 26's "hyperscaler capex-guidance revisions" (Batch 5's ruling: "Hyperscaler capex-guidance revisions as a Factor I series if absent").

A61b repaired the writer for FILED capex (`edgar_xbrl`); this reader is separate and builds on the same contact and publication helpers.

Branch-only. Nothing merged, the box not touched, no units, no secrets, no `.env` read. Nothing here merges before the 1 Nov Monthly.

## Base

`a66-capex-guidance` branches from `origin/a65-6f-tranche4` at its tip, `ea82ace8`. That tip carries chain-7.

## Part 1: the source check

The sources rule of 16 Oct: EDGAR only, keyless, the contact User-Agent, at most 10 requests a second, a stated pause.

| What | Read 24 Oct 2026 | Result |
|---|---|---|
| **The fair-access policy** (https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data) | "Current max request rate: 10 requests/second." "Please declare your user agent in request headers". "The SEC does not allow botnets or automated tools to crawl the site." | Programmatic reads within the policy, with a declared contact, at one request a second. The reader makes 10 requests a pull at most and crawls nothing. |
| **The API's terms** (https://www.sec.gov/edgar/sec-api-documentation) | "These APIs do not require any authentication or API keys to access." The submissions file holds each entity's "current filing history" at `https://data.sec.gov/submissions/CIK##########.json`. | Keyless. |
| **www.sec.gov/robots.txt** | `Disallow: /cgi-bin` and named `/Archives/` subpaths (`/Archives/bin`, `/Archives/etc`, `/Archives/usr`, three under `/Archives/edgar/vprr/`). `/Archives/edgar/data` is explicitly allowed. | Primary documents allowed. |
| **data.sec.gov/robots.txt** | HTTP 404: no robots file. | No rule; the submissions index allowed. |
| **efts.sec.gov/robots.txt** (full-text search) | HTTP 403 to the documentation fetch, which sends no contact. Consistent with EDGAR's own rule. Not retried. | **Not used.** The reader needs no search: each filer's submissions index names its newest 10-Q or 10-K and its primary document directly. |
| **The filing deadlines** (the lag family) | Form 10-Q, General Instruction A.1 (sec.gov/about/forms/form10-q.pdf): "40 days after the end of the fiscal quarter for large accelerated filers and accelerated filers". Form 10-K, General Instruction A.(2)(a) (form10-k.pdf): "60 days after the end of the fiscal year covered by the report ... for large accelerated filers". | Family `sec_periodic_filings`, below. |

**The CIKs** are config/ai_buckets.yaml's `bridge` filers (the EDGAR XBRL writer's), cached in `config/edgar_guidance.yaml`:

| Filer | CIK |
|---|---|
| AMZN | 1018724 |
| GOOGL | 1652044 |
| META | 1326801 |
| MSFT | 789019 |
| ORCL | 1341439 |

**The filing index and the primary document.**
- The index is `filings.recent` in the submissions JSON, with `form`, `accessionNumber`, `filingDate`, `reportDate`, `acceptanceDateTime` and `primaryDocument`.
- The document is `https://www.sec.gov/Archives/edgar/data/<cik>/<accession, no dashes>/<primaryDocument>`.

### The laptop's probe: not run

**`CHESTER_SEC_CONTACT` is not set in this session's environment.** I checked whether it was set without printing it. The one call that would have read it through the secrets loader (from `.env`) was refused by the session's permission check, and I did not try another way round. EDGAR serves no request without a contact address (`altdata/sources/edgar.py`: "every request with `chester-reports/1.0` returns 403"), and a session never invents one. So **no filing was requested from the laptop, for any of the five.** No guidance sentence was found, quoted or extracted from a live filing.

The reader is held on fixtures instead (the gate, below). The box's dry run is the first real read: the commands are at the end.

## Part 2: the reader, `altdata/sources/edgar_guidance.py`

For each filer, each run:

1. **The submissions index**, one request: its newest 10-Q or 10-K.
2. **If that accession is not the one already stored,** the primary document, one request. An unchanged accession asks for nothing more.
3. **The text.** The document's visible text and its MD&A section: Item 2 of a 10-Q, Item 7 of a 10-K, up to Item 3 or 7A. The table of contents repeats the headings, so of several matches the longest span is the section. When it is not located, the whole document is read and the record says so.
4. **The sentences.** Kept when the sentence holds:
   - a capex term: "capital expenditures", or the filer's own (Amazon's "cash capital expenditures", Meta's "capital expenditures, including principal payments on finance leases", Microsoft's "property and equipment");
   - AND a forward marker: "expect", "anticipate", "plan", "intend", or a fiscal-year phrase ("fiscal 2027", "full year 2026") for a year still ahead of the filing date.
   - The filer's fiscal-year end decides "ahead": Microsoft June, Oracle May, the rest December.
   - A bare year in a date ("September 30, 2026") is not a marker. The gate's past-tense fixture caught that.
5. **The record.** Company, form, accession, filing date, period, URL, section, and every kept sentence verbatim. A sentence over 400 characters is stored as the 400-character window around its capex term, marked `truncated`.
6. **The pace.** A one-second pause between requests, the contact User-Agent on each, and `max_retries` 1, so nothing is retried.
7. **Failures.** A 4xx or a failure makes that filer STALE with its reason. All filers failing is a STALE run.

**Stored.** Both rows are dated the filing date, with the vintage the filing's acceptance instant:
- **`edgar.capex_guidance.<ticker>`:** the figure, US$ bn, unit `usd_bn` (new in the vocabulary and `derived.DELTA_UNITS`, moved in percent). It is the primary sentence's figure: high confidence first, then the furthest fiscal year ahead. It is written only beside its record.
- **`edgar.capex_guidance_record.<ticker>`:** the record, JSON, unit `label`. A filing with no guidance sentence still writes its record, with the note "no guidance sentence in the filing", so the next pull knows the accession was read.

**Registered.** Ten registry keys. Source `edgar_guidance` in `source_registry.yaml` (tier A0, primary_fact). A catalogue line.

## Part 3: the extraction rules (session-set, `config/edgar_guidance.yaml`)

| Rule | Pattern (any of) | Figure | Label |
|---|---|---|---|
| `range` | "$X to $Y billion", "$X billion to $Y billion", "between $X and $Y billion", "$X-$Y billion" (hyphen or dash), "in the range of ..." | the midpoint; both ends kept | "midpoint of range" |
| `approximate` | "approximately / about / roughly / around $X billion" | X | "approximately" |
| `stated` | any other "$X billion" | X | "stated" |

The rules run in that order, and a span one rule consumed is not read again.

- **Confidence.** High when the sentence yields exactly one figure and names exactly one year; otherwise low, keeping the first figure and the first year ahead.
- **No figure.** The record holds the sentence and "guidance quoted, figure not extracted".
- **Millions** ("$500 million") are not read as guidance.
- **Every value is session-set:** the markers, the terms, the 400-character cap, the one-second pause, the rules and their order.

## Part 4: where it prints (report only)

- **Item 63, the capex chain's line** (`altdata/capex_chain.py`, the Monthly's what's priced), after the filed-capex line:
  - The line: "Their capex guidance from the filings: META guidance for FY2026: $71 bn (midpoint of range, high confidence), from the 10-Q of 22 Oct 2026; AMZN not stored; ...".
  - The notes, per filing: form, date, accession, URL.
  - With nothing stored: "Their capex guidance from the filings (10-Q, 10-K): not stored for AMZN, GOOGL, META, MSFT, ORCL."
  - `config/capex_chain.yaml`'s comment and `guidance_gap` no longer say guidance is untracked.
  - `validate_batch14_a2`'s check moves from "not tracked" to the not-stored text.
- **Item 26** (`altdata/batch5.py` `capex_guidance_revisions`, printed in `daily_cascade/batch5_block.py` beside the fiscal-bark flag):
  - The change between each filer's two newest filings, where both carry a figure for the same fiscal year: "META raised FY2026 guidance from $68 bn (10-Q of 30 Jul 2026) to $71 bn (10-Q of 22 Oct 2026, +4.4%)".
  - Across fiscal years it prints "not comparable: FY2026 then FY2027". With fewer than two filings stored, it says so.
  - The flag itself still reads ACM's split only and does not read the revisions.
- **The Quarterly.** Energy's question 7, "Did the hyperscalers raise or cut capex guidance this quarter?", now reads the five `edgar.capex_guidance.*` keys. They were `series: []` before.

## Part 5: the gate, and the counts

**`tools/validate_edgar_guidance.py`, 39/0.** Five groups:
- **A, the sentence finder** on a fixture 10-Q: past the table of contents, positive and negative sentences, the filer's own term, a year ahead, the 400-character cap, no MD&A.
- **B, each rule by hand:** four range phrasings to their midpoints, approximate, stated, high and low confidence, "figure not extracted", millions.
- **C, the pull against a fake EDGAR:**
  - no contact gives PENDING and no request;
  - the contact User-Agent is sent with `max_retries` 1;
  - one request per document and a one-second pause;
  - the figure beside its record, at the filing date and the acceptance instant;
  - an unchanged accession is not fetched again;
  - a refusal is STALE with its reason and never retried.
- **D, where it prints:** item 63's line and notes; item 26's revision by hand (68 to 71 bn); "not comparable"; point in time; the Quarterly's question 7.
- **E, the contract:** ten keys registered with their units; the lag family quotes the SEC and its lag is in bound (allowance 95 + 14); no person's name; no transcript or search source in the code.

**The lag family `sec_periodic_filings`** (`config/publication_lags.yaml`): quarterly, lag 14, bound 16.
- A record is dated its filing.
- The longest stretch between filings is the third quarter's 10-Q to the 10-K: a quarter plus the 10-K's 20 extra days (60 against 40), about 14 sessions.
- All five filers are large accelerated filers.

**Registered in the Makefile.** CLAUDE.md's gate line is recounted by `validate_audit_3a`, which holds it against the code: **one hundred and forty code gates (one hundred and thirty-seven Python, three shell)**, from 139 (136).

**Gates run locally:**
- `validate_edgar_guidance` 39/0;
- `validate_official_sources` 340/0;
- `validate_batch14_a2` 40/0;
- `validate_b51_registry_html` 25/0;
- `validate_st_r4_t1` 49/0;
- `validate_audit_3a` 88/0;
- `validate_quarterly_stack` 94/0;
- `validate_secrets` 58/0;
- `validate_6f_calibration` 42/0;
- `check_registry` OK;
- `check_library` 0 failures.

## Differences from the brief

1. **Keyed by filing date, not by the guided fiscal year.**
   - **Why.** `_publication.write_rows` (A61b's call shape) refuses a row dated after today as a parse error. An observation dated a future year-end would also hide from every as-of level read, including the Quarterly's quarter move.
   - **So:** `edgar.capex_guidance.<ticker>` is dated its filing, its vintage the acceptance instant, and the guided fiscal year is the record's. Item 26 compares only two filings that guide the same year.
2. **No full-text search.** The submissions index answers "the newest 10-Q or 10-K" in one request a filer. efts.sec.gov's robots.txt answered 403 to a contactless fetch, so it was not read further.
3. **Item 26 is two things in the order.** The flag (ACM's term-premium split, built in ST-R4.26a) and "hyperscaler capex-guidance revisions" as a Factor I series. The revisions print beside the flag; the flag does not read them. The order planned the revisions "by hand quarterly from earnings calls". Rule 30 and this brief replace that with the filings, and calls are not read.
4. **The laptop probe was not run** (Part 1).

## Files shared

Shared with other branches, so expect stitch conflicts:
- `metrics_registry.yaml`, `source_registry.yaml`, `config/publication_lags.yaml`, `config/catalogue_commands.yaml`;
- `altdata/derived.py` (one unit);
- `altdata/capex_chain.py`, `config/capex_chain.yaml`, `daily_cascade/capex_chain_block.py`;
- `altdata/batch5.py`, `daily_cascade/batch5_block.py`;
- `config/quarterly_chapters.yaml` (one line);
- `tools/validate_batch14_a2.py` (one check);
- the Makefile, CLAUDE.md (the count).

## The box commands (for the chain-8 box sheet; the operator's, after the merge, inside the windows)

```
cd ~/chester-reports && .venv/bin/python -m altdata.sources.edgar_guidance dry-run
cd ~/chester-reports && .venv/bin/python -m altdata.sources.edgar_guidance
cd ~/chester-reports && .venv/bin/python -m altdata.sources.edgar_guidance show
```

- **The dry run** makes the same 10 requests at one a second and prints each filer's form, date, accession, URL and every kept sentence with its extraction. It writes nothing.
- **Read it before the pull.** Each quoted sentence must be the filing's own words, and any "low" confidence needs a look.
- **The pull** writes the records and figures. **`show`** prints item 63's line and item 26's revisions from the store.
- **Not scheduled.** No timer runs this writer yet.

## CI

| Run | On | Result |
|---|---|---|
| read once after the push | the A66 tip | see the report |

## Needs you (at most five)

1. **The first real read is the box's dry run.** The laptop has no contact in its environment. Confirm the five quoted sentences, or their absence, before the first pull writes.
2. **Which pass runs it.** Filings come quarterly, so a weekly slot is enough (for instance beside the Weekly's pulls). That is a schedule change, yours to name.
3. **A filer that guides only on its call** files nothing to read. The record will say "no guidance sentence in the filing" each quarter, and the line prints it. It does not fall back to a transcript.
4. **The extraction rules and markers are session-set** (Part 3), and the 400-character window is the brief's. Ratify or amend at Doctrine #2.
