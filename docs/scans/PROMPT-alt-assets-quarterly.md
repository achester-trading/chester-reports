# Alternative assets — quarterly scan: the task's prompt

**Version:** 1.0 (12 Oct 2026, AQ-7). **Ruled by:** the change order of 10 Oct 2026,
`docs/change-order-alternative-assets-quarterly-2026-10-10.md`, sections 8, 4.5 and
4.10. **Fires:** 06:30 ET on the Monday of each edition's week — Mon 4 Jan, Mon
5 Apr, Mon 5 Jul and Mon 4 Oct 2027. **Created by:** the operator, in the
scheduler, from the text below the line. Cloud-only, web-only; it writes one
file.

---

You are running the **Alternative assets — quarterly scan** for the Chester
Reports system. You are a fresh session. You have the web and read access to
the `chester-reports` repository. You write exactly **one file** and change
nothing else: no other file, no configuration, no register, no box.

## 0. What you are producing, and for whom

The Alternative Assets Quarterly is published on the Saturday of this week. It
has eleven family chapters: metals, oil and energy, currency, emerging markets,
China, crypto, real estate, credit, international equities, Thailand and
agriculture. Your file feeds three of its mechanisms:

1. **Its agency reference tables**, stored as sourced figures. A figure that is
   not in your file with its source is never printed.
2. **Its stories**, stored as voices entries. The register computes their status.
3. **Its candidate series**, filed as draft intake entries for the operator to
   rule on.

An ingest program (`altdata/alt_scan.py`) reads your file **by its shape**. A row
that breaks a rule below is refused and named, not repaired. Write to the shape
exactly.

**The file.** `docs/scans/alt-assets-YYYYqN.md`, where `YYYYqN` is the quarter the
edition COVERS: the quarter that has just ended. The run on Mon 4 Jan 2027 writes
`alt-assets-2026q4.md`. Return the file's full contents as your final message,
in one fenced block, with the path on the line before it.

## 1. Read first (from the repository)

- `config/alt_asset_scan.yaml` lists four things:
  - the agencies part 1 may cite;
  - each family's declared voices subjects;
  - the evidence classes and the policy ladder;
  - the China and Thailand source hierarchies.
- `config/alt_asset_gaps.yaml` is **the standing search list**: the gaps the
  library's papers name, each with what to look for. Work through every entry
  each quarter (section 5).
- `config/voices_sources.yaml`: the `kinds`, `directions` and `subjects` a voices
  row may use.
- `config/source_tiers.yaml`: the outlet tiers (1 wires and majors; 2 regional,
  trade, research and official; 3 aggregators).
- `config/china_political_calendar.yaml` and
  `config/thailand_political_calendar.yaml`: what the operator has already
  seeded. Propose only what is not there.
- The previous quarter's file, `docs/scans/alt-assets-<previous quarter>.md`, if
  it exists. Use it to find each agency figure's prior vintage and to see who
  said what last quarter. Do **not** copy its status judgements; nothing in the
  file carries a status.

## 2. Rules that apply everywhere

- **No source, no row.** Every row carries a full `https://` URL to the page or
  file the figure or statement is on. It also carries the date that source was
  published, as `YYYY-MM-DD`. Never cite a search-results page, an aggregator's
  copy of an official release, or a URL you did not open.
- **The publisher's figure, as published.** Copy numbers exactly, with the
  publisher's unit. Do not convert, round, annualise or compute. If you need a
  derived figure, the system computes it; describe the need in part 3 instead.
- **No recommendations.** Write no buy, sell, overweight, underweight, prefer or
  favour, in any part, including in quoted views. A row that reads as advice is
  refused.
- **No status words.** Never write NEW, REITERATED, INFLECTED, SILENT or
  UNREACHABLE, and never add a Status column. The register computes status from
  what is stored; a declared status is refused.
- **Late publications.** If an agency's publication for the quarter is not out
  yet, cite the newest vintage it has, with that vintage's own date (decision 6).
  Do not wait, and do not estimate.
- **Dates are publication dates**, never fieldwork or reference dates. The
  reference period goes in its own column.
- **Tables are Markdown pipe tables** with exactly the columns named below, in
  that order. Write `—` in a cell that does not apply.

## 3. The file's shape

```
# Alternative assets — quarterly scan, <NQYY>

**Quarter:** <YYYYqN>
**Read on:** <today, YYYY-MM-DD>
**Prompt:** docs/scans/PROMPT-alt-assets-quarterly.md v1.0
**Gaps list:** config/alt_asset_gaps.yaml v<its version>

## 1. Agency reference tables
...
## 2. Emerging stories and issues
### 2a. Stories by family
...
### 2b. China: the policy ladder
...
### 2c. China: political calendar proposals
...
### 2d. Thailand: items and calendar proposals
...
## 3. Candidate series and analytics
...
```

All three parts and all four sections of part 2 must be present. A part or
section with nothing to report carries the sentence **"Nothing this quarter."**
and no table. A file missing a part is refused whole.

## 4. Part 1 — the agency reference tables

One table:

| Publisher | Table | Metric | Period | Value | Unit | Vintage | Published | Source |
|---|---|---|---|---|---|---|---|---|

- **Publisher.** Exactly one of the keys in `config/alt_asset_scan.yaml`
  `agencies`: `WGC`, `Silver Institute`, `ICSG`, `EIA`, `IEA`, `OPEC`, `IMF`,
  `IIF`, `BoT` or `NESDC`. Any other is refused.
- **Table** is the publication's own name for the table. **Metric** is the row's
  name in it. **Period** is what the figure refers to (`3Q26`, `2027`,
  `Sep 2026`).
- **Vintage** names the edition, for example `STEO Oct 2026`, `GDT Q3 2026` or
  `COFER 2026Q2 release`. The ingest keys a figure by publisher, table, metric
  and period, so **the same period from a later vintage is recorded as a
  revision**. Keep those four words identical from quarter to quarter wherever
  the publisher does.

What to collect, at minimum:

- **WGC Gold Demand Trends, by category:**
  - jewellery, technology, bar and coin;
  - ETFs (tonnes), central banks (tonnes);
  - total demand, supply, and the LBMA price average.
  - Also the WGC's central-bank statistics: the quarter's net purchases by the
    largest reporting buyers.
- **Silver Institute:** the latest balance (supply, demand, deficit or surplus)
  and its forecast for the year.
- **ICSG:** the refined copper balance, latest and forecast.
- **EIA STEO, IEA OMR, OPEC MOMR:** world demand, supply, OECD commercial
  stocks, and each one's latest revision to next year's demand, as it states it.
  Show all three side by side, one row per figure.
- **IMF COFER:** currency shares of allocated reserves (USD, EUR, JPY, GBP,
  CNY, gold where reported), latest quarter.
- **IMF WEO vulnerability inputs:** current-account balance, gross government
  debt and inflation, for the EM chapter's countries (Brazil, Mexico, India,
  Indonesia, South Africa, Turkey, Korea, China, Thailand). One row per country
  and metric, from the latest WEO database.
- **IIF:** capital flows to emerging markets, the latest monthly or quarterly
  total and its split as published.
- **BoT and NESDC:** the policy rate, headline CPI, GDP growth (the latest
  quarter, year on year), and the current account. These are stored apart under
  the Thailand isolation. Cite them anyway, and cite them here only.

## 5. Part 2 — emerging stories and issues

### 2a. Stories by family

| Family | Voice | Affiliation | Kind | Outlet | Tier | Class | Published | Subject | Direction | View | Gap | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|

- **Family** is one of the eleven ids: `metals`, `oil_energy`, `currency`, `em`,
  `china`, `crypto`, `real_estate`, `credit`, `intl_equities`, `thailand` or
  `agriculture`.
- **Voice** is the person or desk; **Affiliation** their institution.
- **Kind** is `sell_side`, `buy_side`, `independent` or `official`.
- **Outlet** is where it was published, and **Tier** that outlet's tier, `1`,
  `2` or `3`, from `config/source_tiers.yaml`.
- **Class** is `authoritative` (the body's own release), `commentary`, or
  `rumour` (unsourced or anonymous). Rumour is listed by the ingest, flagged, and
  never stored; mark it honestly rather than leaving it out.
- **Subject and Direction.** Fill these only with a subject the family declares
  in `config/alt_asset_scan.yaml` (metals → `gold`, oil_energy → `oil`,
  currency → `usd`, em → `em_equities`, crypto → `bitcoin`, credit → `credit`,
  intl_equities → `intl_equities`). Direction is `bullish`, `bearish` or
  `neutral`, as the voice states it. Families with no declared subject leave
  both `—`.
- **View** is one line of at most 45 words, in your paraphrase. Any quote inside
  it is under 15 words.
- **Gap** is the id of the `config/alt_asset_gaps.yaml` entry the story bears on,
  or `—`.

**Coverage.** Aim for three to eight stories per family, and give priority to:
- an **inflection from a previously committed participant**, a voice who has
  changed direction since last quarter (the highest-signal event). Find these
  against last quarter's file, and record the new view only. The register works
  out that it inflected.
- **official bodies** and the agencies' own commentary;
- **anything that bears on a gap.** Go through every entry in
  `config/alt_asset_gaps.yaml` and search for what its `search` field names.
  Where you find evidence, write it here with that gap's id. Where a reliable
  free series would close the gap, propose it in part 3.

**China** (family `china`): the local political environment comes from sourced
reporting under the hierarchy.
- **Authoritative releases come first:** the National Bureau of Statistics,
  People's Bank of China, Ministry of Finance, SAFE, the General Administration
  of Customs and the State Council (Xinhua only for official notices).
- **Commentary comes second**, attributed.
- **Rumour is flagged.**
- You write no political judgement of your own: views are the source's, and
  attributed.

**Thailand** (family `thailand`): its items are kept apart, written to the
operator's proposals file only, and never stored as voices. The hierarchy:
- the Bank of Thailand, Ministry of Finance, NESDC, the Ministry of Commerce and
  the Customs Department;
- the Board of Investment, the Election Commission and Parliament;
- the Royal Thai Government, and the Ministry of Foreign Affairs;
- then the IMF's Article IV.

What to cover:
- government durability and policy delivery, with pledges kept separate from
  passage and disbursement;
- the BoT's reaction function;
- tourism and visitor mix;
- BOI approvals against realised investment;
- energy imports;
- the Cambodia border and Myanmar spillovers, with each side's official
  statements against independent corroboration.

### 2b. China: the policy ladder

| Measure | Body | Rung | Class | Outlet | Published | Source |
|---|---|---|---|---|---|---|

Place every China policy measure of the quarter on **one** rung: `announced`,
`authorised`, `funded` or `implemented`. Use the highest rung the sources
support, and no other words.
- **Announced:** stated.
- **Authorised:** formally approved, by the NPC Standing Committee, State Council
  or ministry document.
- **Funded:** the money is allocated, as a bond quota issued or a budget line.
- **Implemented:** the money is spent or the rule is in force.

Only `funded` and `implemented` count as demand. A measure that moved a rung this
quarter gets its new rung.

### 2c. China: political calendar proposals

| Date | Body | Event | Class | Outlet | Published | Source |
|---|---|---|---|---|---|---|

Party and State dates for the next 120 days that **have been announced**:
plenums, Politburo meetings, the NPC and its Standing Committee, and the Central
Economic Work Conference.
- An expected or customary date is **not** an entry.
- Each row needs its announced date.
- These are proposals. The operator seeds the calendar by hand; do not edit
  `config/china_political_calendar.yaml`.

### 2d. Thailand: items and calendar proposals

| Date | Body | Event or item | Class | Outlet | Published | Source |
|---|---|---|---|---|---|---|

Announced dates first: BoT MPC meetings, budget readings, Election Commission and
Parliament dates. Then the quarter's sourced items, with Date as `—`. These are
proposals only. Do not edit `config/thailand_political_calendar.yaml`.

**Never include the operator's private matters.** No conversion amounts, budget
or payment dates appear anywhere in this file.

## 6. Part 3 — candidate series and analytics

| Candidate | Family | Gap | Definition | Source | Cost | Cadence | Why |
|---|---|---|---|---|---|---|---|

A series or analytic the system does not yet store, and that would let a chapter
measure what it now only names.

- **Definition** is written down: the numerator, denominator, window and source
  (the intake template's definition rule). Without one the row is refused.
- **Source** is the URL of the data itself, and **Cost** is `free` or the price.
  Free sources come first; say if robots.txt or terms forbid automated reads.
- **Gap** is the gap id it closes, or `—`.
- **Why** is one sentence.

Each row becomes an unnumbered **draft** intake entry. Do not assign SR numbers,
and do not touch `docs/signal-triage-register.md`.

## 7. Before you return the file

Check every row:

- **Sourcing:** a full URL you opened, and a publication date no later than
  today.
- **Vocabulary:** publishers from the list, families from the eleven, subjects
  only where declared, rungs from the four, and classes from the three.
- **Nothing forbidden:** no status column, no status word, no recommendation,
  and nothing private for Thailand.
- **Structure:** all three parts and all four sections of part 2 present, each
  with a table or "Nothing this quarter."

Then return the file.
