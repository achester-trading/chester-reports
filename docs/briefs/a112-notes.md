# A112 notes: D2-90 built (the EM shock screen's amendment, ruled 2 Nov 2026)

Paste A112 (`docs/pastes/A112.md`), 2 Nov 2026. Branch
`a112-em-shock-screen-amendment`, from `origin/main` at `422ea697`. It merges
after the merge week, refreshed then. The ruling accepts (a) to (d) of B105's
draft (`docs/briefs/b91-notes.md` Part 3, on `b91-batch-19-filing`).

**Why this file holds the "as built" record.** The paste names b91-notes Part 4
for it, but `docs/briefs/b91-notes.md` exists only on b91's branch. Creating it
on main would collide (add/add) when b91 merges, so the record is here. B91's
Part 4 can point to this file when b91 next moves.

## (a) The threshold and the dating

**The rule as built** (`altdata/move_screen.py`, `config/move_screen.yaml`):

- `classify` also returns `countries_same_day`: each country with a member whose
  1-day z is at `em.same_day_sigma` (4.0) or more, in either direction, as every
  flag here is.
- `contagion_states` opens a shock on a session:
  - for its one country, when the session is idiosyncratic (exactly one country
    flagged), as built;
  - for each `countries_same_day` country, whatever the other countries do, a
    mixed session included.
- **A systemic session opens no single-country shock.** It is contagion
  already. That is option (i) of B105's draft, "systemic excepted".
  - **Confirmed by the operator, 2 Nov 2026, after A112 reported:** "your
    reading stands — a systemic session opens no single-country shock (it is
    already contagion); the 4-sigma same-day rule applies on idiosyncratic and
    mixed sessions only." The build already does this; no code changed.
- A country qualifying both ways opens one shock, not two.
- Each shock row now carries `opened_by` ("single country" or "same-day 1-day
  move").
- Below 4 sigma nothing changes: the exactly-one rule stays.

**October's fixture**, the reading's stored states for 19-30 Oct
(`validate_move_screen.py` group J):

| | Shocks |
|---|---|
| As built | India 23 Oct; Brazil 27 Oct; Brazil 28 Oct |
| As ruled | India 23 Oct; **Brazil 26 Oct** (mixed session, opened by EWZ's z1 of −12.38); Brazil 27 Oct; Brazil 28 Oct |

One firing is added, Brazil dated 26 Oct, as the ruling expects.

- The fixture also holds the edges:
  - a 3.9-sigma move on a mixed session opens nothing;
  - a systemic session opens none.
- The reading holds no other country's z1, so their extra firings, if any, are
  not counted. `python -m altdata.move_screen compute --day` gives them on the
  box.

## (a) Each past session as of its own close

**The mechanism.**

- `contagion` classifies each past session in its window as of that session's
  own close-report instant, `session_close_cutoff(day)`: `em.classify_as_of`,
  16:45 ET, in UTC. Where the run's cutoff is earlier, it uses that.
- Members and spreads are read through the store's as-of join at that instant.
  A row that arrived later is invisible to that session: H.10's weekly batch, a
  restatement, a backfill.
- The session being run is classified at the run's own cutoff, as before.
- Each day carries `classified_as_of`. Each shock row, and so each stored
  `screen.em_contagion` row, carries the instant its session was classified as
  of.
- So a stored shock says what its session's close could know. No later run can
  date a shock from rows that close could not see.

**The proof** (group K): a synthetic store of four countries' ETFs.

- EWZ falls 20% on 27 Oct, but its rows from that day are written late
  (available 30 Oct 12:00Z).
- Read with the late rows, 27 Oct is Brazil alone. As of its own close it was
  quiet.
- A run on 30 Oct dates no shock 27 Oct. The late rows first count on 30 Oct,
  the first close that could know them.
- Every shock's `classified_as_of` is its own session's close, and the stored
  rows carry it.

**What this changes in a report.** The 26 Oct run's view of 20 and 21 Oct (B105:
mixed as stored, Indonesia-alone shocks as reclassified) now matches what those
closes stored. A shock first seen on a later run, as Brazil 7 Oct was on the
21 Oct run, no longer appears.

## (b) The FX source: the check, and the gap

**The candidate.** The Banco Central do Brasil's SGS time-series service, its
public JSON API (`api.bcb.gov.br/dados/serie/bcdata.sgs.<n>/dados`), the daily
PTAX USD/BRL sale rate.

**The series number.** 1, by the open-data portal's dataset name, "Taxa de
cambio - Livre - Dolar americano (venda) - diario". It is to be confirmed by the
one sample request when the check passes; no request was made.

**The check, 2 Nov 2026**, all with the project's generic User-Agent:

| Request | Answer |
|---|---|
| `https://api.bcb.gov.br/robots.txt` | 404: no robots file, so no rule for the API host |
| `https://www.bcb.gov.br/robots.txt` | 200: `Allow: /` for every agent; only SharePoint `_catalogs`, `Lists`, `Forms` and `_layouts` paths are disallowed |
| `https://dadosabertos.bcb.gov.br/robots.txt` | 200: disallows the portal's own `/api/`, `/revision/`, `/dataset/rate/` and dataset history pages, `Crawl-Delay: 10`; nothing about the SGS host |
| The terms page: the portal's dataset page for series 1 | **HTTP 502 twice** (an error page, 5,015 bytes) |

**The result: not passed.** The licence could not be read, so the 16 Oct check
stops at the terms, and by (b) the build stops at the gap:

- no sample request;
- nothing stored;
- **no inactive pair declared**. It would have gone in
  `config/data_quality.yaml`'s `inactive_pairs`, in A93's shape, since A96's
  `config/price_sources.yaml` is not on main.

`source_registry.yaml` gains `bcb_sgs` with `status: candidate`,
`allowed_reports: []` and `implemented_by: none`. Its licence field records the
check as above.

**The third attempt (A118, 3 Nov 2026), outcome (3): unreachable again.** One
terms fetch and one robots fetch, with the project's generic User-Agent:

| Request | Answer |
|---|---|
| The terms page (the same URL as A112's) at 02:48:06 UTC | **HTTP 502**, the same 5,015-byte error page |
| `https://api.bcb.gov.br/robots.txt` at 02:48:07 UTC | 404: still no robots file |

The candidate stays `status: candidate` with its licence "terms unread". Nothing
was fetched beyond those two requests: no sample request was made, nothing was
stored, and no pair was declared. The check waits for the portal. A later paste
can try the page again, or read the BCB's own terms of use on www.bcb.gov.br,
whose robots allows `/`. Nothing here scrapes around the 502.

**The next step, by a later paste.** Read the terms (the portal page, or the
BCB's own terms of use), then make the one sample request (record its first
rows' dates). Then declare `fred.usd_brl` against it as an inactive pair,
enabled false.

**A merge note for that paste.** A93 adds an `inactive_pairs:` block to
`config/data_quality.yaml` (family `us_index_funds`). A second family must join
it as a list, not as a second key.

## (c) Brazil's local rates: a listed gap

- **The candidates:** the same SGS service's policy-rate series (Selic) and a
  DI-pre swap tenor.
- **What would use them:**
  - the EM screen, as Brazil's third member (rates, which no sigma on FX or
    equity sees, and the channel of October's loss);
  - 105(b)'s EM local bonds for `em_scorecard`.
- No key, no writer, nothing by hand. Recorded in `bcb_sgs`'s caveats and here.

## (d) Rights: unchanged

The screen stays report-only:

- Its shocks print as lines (`contagion_line`). The idiosyncratic line is a
  candidate for the narrative register, whose write is the operator's.
- **The gate that already checks this** is `validate_move_screen.py` group E:
  "the screen writes nothing to any register".
- **The case added beside it:** no regime, dial, register, weight or lab module
  reads the EM screen or its shocks. It searches `altdata/regime.py`,
  `config/market_state.yaml`, `altdata/state_vector.py`, `register/` and
  `alpha/` for `em_contagion`, `countries_same_day`, `same_day_sigma`,
  `screen.em`, `contagion_states` and `em_screen(`. None is found.

## Gates (one at a time)

| Gate | Tally |
|---|---|
| `validate_move_screen.py` | 67 passed, 0 failed (52 before; groups J and K and the rights case new) |
| `validate_official_sources.py` | passed |
| `validate_quality.py` | 48 passed, 0 failed (no inactive pair added) |
| `check_registry.py` | OK |
| `validate_stack.py --group` | not run: B97's `--group` flag is on the rehearsed tree, not on main |

## A118 gates (one at a time, 2 Nov 2026 evening)

No pair was declared, so the quality config is unchanged; `validate_quality` was
run anyway as the pair's gate.

| Gate | Result |
|---|---|
| `validate_official_sources` | 340 passed, 0 failed |
| `validate_quality` | 48 passed, 0 failed |
| `check_registry` | OK |
