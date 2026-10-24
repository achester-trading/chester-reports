# a55-box-fixes: five defects the box evening of 20 Oct 2026 turned up (session A, 21 Oct 2026)

**Base and boundaries.** This branch is cut from **main's tip, `f9ec9e3`** ("Merge pull request #40 from achester-trading/chain-3").
- **It merges on its own, after chain-4 and a54-relative-volume.** When each is on main, main is merged into this branch with a merge commit, the gates are recounted, and the branch is pushed.
- **Branch only.** Pushed, nothing merged, nothing deployed, nothing run on the box, no unit enabled or started.
- **Only read:** session B's branches. chester-meme was not opened.
- **The specification** is the paste: each part quotes what the box printed on 20 Oct. Where the paste and the code differ, the code wins (listed below).

## The commits

| Commit | Part |
|---|---|
| `59c4537` | the FRED history's split |
| `e575e7a` | the notes' paragraph |
| `10a9e4c` | the BLS feeds |
| `605aa17` | the FOMC event rows |
| `71df842` | the requirements check |
| `e3002bc` | `tools/validate_a55_box_fixes.py`, the Makefile, CLAUDE.md, these notes |
| (round 2) | the FOMC history claim, its audit, the gate's groups F–H, these notes (Round 2 below) |

## Part 1: the FRED history's split

- **Finding.** `vintage_history()` took windows of exactly `MAX_VINTAGES` (2,000) of the series' vintage dates, each ending the day before the next window's first. FRED counts one more date in a real-time period than the window's own list holds. The box's refusal for `yield_30y` read "There are 2001 vintage dates in the specified real-time period: 2005-06-28 to 2014-04-21": the vintage in force at the period's start, it seems. So every window sized to the limit was one over, and every long daily series failed the same way.
- **Fix: a margin, not FRED's own count.**
  - `WINDOW_VINTAGES = MAX_VINTAGES - WINDOW_MARGIN` = **1,900** dates a request.
  - The 100-date margin covers FRED's extra date and any lag between the vintage-dates list and the observations endpoint.
  - A margin needs no extra request to ask FRED its count and cannot be wrong by one again.
- **The boundary rule is unchanged.** A window still ends the day before the next window's first vintage, so the windows partition the vintages (`fred_history.windows()`), and a value unchanged across a boundary is not a new row.
- **The reason is in the module's docstring.** `validate_fred_history`'s paging fixture now sets the window explicitly (25/0).

## Part 2: the evening note's paragraph

- **Finding.** The dry run's paragraph ran 170 words against the order's 150 (13% over). `note_common.prose` withheld it, as it must: a reply past the cap is withheld, never trimmed. The prompt asked for "at most 150 words", so the model wrote to the cap and overran.
- **The cap stays.** It is the order's (`docs/change-order-secondary-notes-2026-10-19.md`).
- **The order allows no revision for length.** It allows "the numeral audit and binding, the one-revision retry, and the withheld-with-reason behaviour". The one revision is `audit_retry`'s, for an audit refusal, and an overrun is not one. So nothing re-asks, and that is left alone.
- **Fix.** The prompt now aims below the cap and states both figures: "about {target} words … {cap} words is a hard cap: a paragraph past it is withheld, not printed".
  - The target is `TARGET_SHARE` of the cap, **0.8**: 120 of 150 (the weekday evening), 320 of 400 (Sunday), 200 of 250 (the open note).
  - **Why 80%:** the observed overrun was 13%, and aiming a fifth under the cap leaves it inside.
- **The open note** goes through the same `note_common.prose`, so the same target applies to it (checked).

## Part 3: the BLS news feeds

- **Finding.** BLS answers every request without a contact with HTTP 403 and an "Access Denied" page: "bot activity that doesn't conform to BLS usage policy is prohibited". That includes robots.txt and both feeds (`empsit.rss` and `cpi.rss`), whether the agent is the repo's generic one or its browser-like one.
  - The same requests carrying a contact in the User-Agent answer 200. This was checked with a reserved placeholder address, never committed.
  - BLS's robots.txt allows `/feed/`.
  - A user community confirms the same behaviour (an email in the User-Agent clears the 403).

  So the request was wrong, not refused.
- **Fix.** `altdata/sources/user_agent.py` gains `CONTACT_HOSTS`, the SEC and `bls.gov`. `for_url` gives a contact host the same contact form as the SEC: `edgar.user_agent()`, read at run time from `.env`'s `CHESTER_SEC_CONTACT`, never written in the tree.
  - `altdata/sources/news.py` sends it for the BLS feeds.
  - With no contact set, the feed reports **pending** with its reason and the request is not made, rather than failing.
  - **The rule stands:** no name or address in any committed file, fixture or User-Agent. `validate_secrets` passes (58/0).
- **The 17 Oct ruling** ("the SEC alone gets the contact form") is extended to a second host by this paste. That extension is listed for you below.

## Part 4: the FOMC event rows

- **Finding.** The claims writer (`altdata/events_ingest.claims_events`) stores each FOMC meeting as a `scheduled` event with source **`claims_registry`**. `alpha/event_rates.release_days` read only source **`claims`**, so it found none: n = 0 in every bucket. `validate_alpha_lab_3`'s fixture seeds `claims`, which matched the reader and never the writer, so the gate passed throughout.
- **Fix.** The reader takes both, `claims_registry` (the writer's) and `claims` (the older spelling a fixture carries). `validate_alpha_lab_3` passes (65/0).
- **This is session B's code:** the change is one SQL filter in `alpha/event_rates.py`, listed for B.
- **The gap, round 1.** The claims register held the 2026 and 2027 meetings only (`cal.fomc_2026`, `cal.fomc_2027`), so the fix found this year's past decisions: six before 20 Oct. FRED's target-range series mark a decision day only when the target changed, so they cannot stand in for every meeting.
- **Closed in round 2:** the history is entered as a claim, as ruled (Round 2, Part 3 below).

## Part 5: the requirements check

- **Finding.** chain-3 added `jsonschema` to `requirements.txt`. `make deploy` does not pip install, so the Security Master export refused to write until the package was installed by hand on 20 Oct.
- **Fix.** `altdata/requirements_check.py` compares each requirement's name and specifier with the installed distribution through `importlib.metadata`: no network, no install, no import of the package.
  - **How it reads lines:** a requirement whose environment marker does not apply is skipped, and a URL requirement is counted, not checked.
  - **Exit:** 0 when everything is satisfied, 1 otherwise, with one line naming what is missing or out of range and the fix, `.venv/bin/pip install -r requirements.txt`.
  - **The heartbeat** (`scripts/check_heartbeat_cron.sh`) prints that line as a WARNING after the listings check, and never changes the verdict or the exit code. `CHESTER_SKIP_REQUIREMENTS_CHECK` skips it.
- **On the laptop** it found `weasyprint` missing: a true finding, and harmless, since the PDF says it was not built.

## Every session-set value, with its reason

| Value | Setting | Reason |
|---|---|---|
| `fred_history.WINDOW_MARGIN` | 100 (windows of 1,900) | FRED counts one more than the window holds; a margin cannot be wrong by one again and needs no extra request |
| `note_common.TARGET_SHARE` | 0.8 | the observed overrun was 13%; aiming a fifth under the cap leaves it inside |
| The BLS contact | `CHESTER_SEC_CONTACT`, the same one the SEC gets | BLS refuses an unidentified bot; one contact for the project, never in the tree |

## Where the paste and the code differ

1. **Part 3:** "a User-Agent BLS's policy asks for … as the voices scan's is". The voices scan sends the SEC contact to SEC hosts only, and the 17 Oct ruling keeps the contact form for the SEC alone. This branch adds bls.gov to those hosts, reusing the same `.env` contact rather than a new variable.
2. **Part 4:** "fix it where the store holds the dates". The store held 2026–27 only, so the earlier meetings were a gap until round 2 entered them.
3. **Part 5:** "importlib.metadata against each requirement's name and specifier". The specifier is evaluated with `packaging`, which pip's own environment carries. Where `packaging` is absent, the requirement is counted as unchecked, never as satisfied.

## The box commands, dry runs first (the operator's)

```
cd ~/chester-reports
# Part 1 -- what failed on 20 Oct, then the backfill again after the merge (rows already stored are skipped):
grep FAILED ~/logs/fred_history.log
.venv/bin/python -m altdata.fred_history backfill --all --dry-run
.venv/bin/python -m altdata.fred_history backfill --all
# Part 3 -- the contact the BLS feeds need is CHESTER_SEC_CONTACT in .env (already set
# for the SEC if EDGAR reads); then one news pull, the probe first:
.venv/bin/python -m altdata.events_ingest probe --only news
.venv/bin/python -m altdata.events_ingest pull --only news
# Part 5 -- the check, then the fix if it names anything:
.venv/bin/python -m altdata.requirements_check
.venv/bin/pip install -r requirements.txt
# Round 2 -- the claims writer (the FOMC history), the probe first:
.venv/bin/python -m altdata.events_ingest probe --only claims
.venv/bin/python -m altdata.events_ingest pull --only claims
# Part 4 and round 2 -- then the base rates:
.venv/bin/python -m alpha.event_rates show
.venv/bin/python -m alpha.event_rates compute
# Round 2 -- the audit's first run (read-only: one page read, nothing written):
.venv/bin/python -m altdata.fomc_audit check
```

- **Run these inside the windows.**
- **`events_ingest probe` is the pull's dry run.** Round 1 said the pull had none, which was wrong.
- **`alpha.event_rates` has no dry run.** `show` prints the stored base rates first; `compute` writes `alpha.db`.
- **`altdata.fomc_audit check` only reads.** It reads one page and writes nothing.

## The gate and the checks

- **The gate:** `tools/validate_a55_box_fixes.py`, a new gate, 18 checks, groups A–E, synthetic fixtures only.
- **What it covers:**
  - **(A)** a fake ALFRED that counts one more than the window and refuses past 2,000: the old split refused, the new one never; every vintage in exactly one window; no row invented at a boundary;
  - **(B)** a 170-word draft withheld with its reason, and each prompt target under its cap;
  - **(C)** bls.gov a contact host: pending with no contact, the contact sent with one, no address in the tree;
  - **(D)** the writer's `claims_registry` FOMC rows found;
  - **(E)** an absent requirement named, one out of range named, a satisfied one not; the heartbeat block warning only.
- **Changed and run locally:**
  - `validate_a55_box_fixes` 18/0;
  - `validate_fred_history` 25/0;
  - `validate_secondary_notes` 87/0;
  - `validate_secrets` 58/0;
  - `validate_alpha_lab_3` 65/0;
  - `validate_audit_3a` 88/0, with `altdata.requirements_check`'s catalogue line.
- **Left to CI:** the heartbeat's shell gates.
- **The count:** 126 code gates (123 Python, three shell), counted on main's base. Chain-4 and a54 each add one, so the recount at the merges sets it. Round 2 extends this gate and adds none.

## The CI rounds

| Round | Run | Result |
|---|---|---|
| A55 | 39542406552 | **green, 136/136 jobs** (`e3002bc`), in one round |
| A55 round 2 | (below, in the closing message) | |

## Files shared with chain-4 and a54-relative-volume

- **chain-4** (main plus `a52-doctrine-2-pack`): `CLAUDE.md` (the gate count), `Makefile` (one gate line each), `config/catalogue_commands.yaml` (one line each).
- **a54-relative-volume:** `CLAUDE.md` and `Makefile`, likewise.

## For session B

`alpha/event_rates.py`, `release_days`: the FOMC query reads source `IN ('claims_registry', 'claims')` in place of `= 'claims'`. Its tests keep their shape.

## Round 2 (21 Oct 2026): Ari's rulings on the two A55 decisions

### The rulings, as ruled

1. **The BLS contact.** Ruled 21 Oct 2026, 00:41 ET: "accepted as you built it. bls.gov gets the same contact as the SEC, read from .env at run time and never written to a file; this extends the 17 Oct ruling, which gave it to the SEC alone." Ari will make a permanent alias address for automated requests and put it in `.env` himself.
2. **The FOMC history.** Ruled 21 Oct 2026, 00:41 ET: "the history is entered once as a claim, and a check audits it every so often."

### Part 1: a55's CI

Run 39542406552 on `e3002bc` is **green, 136/136 jobs** (the table above). Nothing needed fixing.

### Part 2: every sender of a contact, and its `.env` key

There is **one key, `CHESTER_SEC_CONTACT`**, read through `altdata/secrets` by `edgar.contact()` and wrapped by `edgar.user_agent()`. Every sender below reads it there and nowhere else, so one line in `.env` changes all of them. No value is written here. No code was changed for this part.

| Sender | What it sends to | What it does when the key is empty |
|---|---|---|
| `altdata/sources/edgar.py` `filing_events` | sec.gov filings (the events ingest's `edgar` source) | `not_configured` with its reason; no request is made (EDGAR dormant) |
| `altdata/sources/edgar_xbrl.py` | sec.gov XBRL company facts | `pending`, "not configured"; no request |
| `altdata/sources/fundamentals.py` `_edgar_context` | sec.gov ticker→CIK map | no EDGAR request; rows take the write instant |
| `altdata/sources/treasury.py` (`treasury.mstr_shares`) | sec.gov share count | a listed gap; mNAV prints "not tracked" |
| `altdata/sources/voices_scan.py` `Fetcher` (any voices source on an SEC host) and its 13F read | sec.gov | an SEC-hosted source is refused (`PermissionError`: the generic agent is not sent to it) and lists as unreachable with that reason; the 13F read is `not_configured` |
| `altdata/sources/news.py` press feeds, through `user_agent.for_url` (`bls_empsit`, `bls_cpi`) | www.bls.gov/feed/ | `pending`, "the host asks for a contact in the User-Agent, and CHESTER_SEC_CONTACT is not set"; no request |

Every other outbound request carries the generic or browser-like project agent (`altdata/sources/user_agent.py`), with no contact.

Two notes for the alias:
- **The voices scan's `Fetcher`** routes by `is_sec_host`, not `is_contact_host`. So a voices source on bls.gov would get the browser-like agent and BLS's 403. No voices source is on bls.gov today (`config/voices_sources.yaml`).
- **`altdata/releases.py`** still records www.bls.gov's release files as refused ("refuses a client that…"). With a contact, those files may now answer. That reader was not changed (round 2 changes no code for the contact); it is listed below.

### Part 3: the FOMC history and its audit

**The source check (the 16 Oct standing rule).**
- **robots.txt:** www.federalreserve.gov serves none (`/robots.txt` answers 404), so no path is disallowed.
- **Terms:** the site policy (`federalreserve.gov/disclaimer.htm`) reads: "Unless otherwise indicated, information on Board's website is in the public domain and may be copied and distributed without permission. Please cite to the Board as the source of the information." It has no rule against automated reads.
- **Access:** every page answered 200 to the repo's generic agent. There is no key, registration or browser pretence.
- **Verdict:** the check passes. The history is a cited claim, and the audit is built in full.

**The history: `cal.fomc_history` in `config/claims.yaml`**, beside `cal.fomc_2026` and `cal.fomc_2027`.
- **What it holds:** **239 policy statements, 4 Feb 1994 to 10 Dec 2025: 225 scheduled, 14 after an unscheduled meeting or conference call.**
- **Each row** carries its statement date, its kind, the Board page it was read from (`fomchistorical<year>.htm` for 1994–2020, `fomccalendars.htm` for 2021–2025) and the statement's path.
- **Why 1994:** the stored price history `event_rates` reads is SPY, from 29 Jan 1993, and the FOMC published no statement before 4 Feb 1994. So "back to the start of the stored price history" is the first statement, which also covers "to 2000".
- **What a row is:** a meeting the page links to a Statement ("Press Release" on some pre-1999 pages). Before May 1999 the Committee announced only a change, so 1994–1998 hold 14 rows.
- **The dates were checked against the statements.** Each row's date is the release date printed on the statement itself, read for all 239.
  - **One link was misdated:** the 27–28 Jun 2007 meeting links its statement as `20070618a`, and the statement prints June 28, 2007. The row carries 28 June.
  - Six meetings or calls released their statement the next day (17 Aug 2007, 22 Jan, 11 Mar and 8 Oct 2008, 11 Oct 2019, 3 Mar 2020), and those rows carry the statement's day.
- **Left out, and the claim says so:**
  - conference calls and meetings with no statement;
  - the cancelled meeting of 17–18 Mar 2020;
  - the notation votes of 19, 23 and 31 Mar 2020 and 22 Aug 2025, which are votes, not meetings. The 23 Mar 2020 one carried a policy statement, so it is named in needs-you.
- **The claims writer.** `altdata/events_ingest.claims_events` reads `detail.statements` when a claim carries it, and still parses a year's calendar from its value. One `scheduled` event per statement, source `claims_registry`, key `fomc-<date>`, at the existing 18:00 UTC convention (only the date is read downstream). The value text holds no "Mon DD" pattern, so the FOMC-minutes rule derives nothing from it.

**What `alpha.event_rates` then finds.**
- **Inside the stored price window** (SPY from 29 Jan 1993) to 20 Oct 2026, it finds **243 FOMC events**: the history's 239 less two Sunday statements (9 May 2010, 15 Mar 2020; `release_days` keeps trading sessions only), plus this year's six past decisions.
- **Counted on the laptop** through the writer and the session calendar. The box's own count follows its claims pull.
- **The engine's rows** still leave out an event whose inputs became knowable more than five sessions after it. That is judged by the price and surprise rows' availability, not by the claim's entry date.

**The audit: `altdata/fomc_audit.py`, `python -m altdata.fomc_audit check`.**
- **Report-only.** It reads `fomccalendars.htm` and compares every year on it with the file's FOMC dates (the history's statements and each `cal.fomc_<year>`'s decision days).
- **What it names:**
  - **MISSING:** a published meeting the file lacks;
  - **CHANGED:** the file and the page each hold a different date in the same month;
  - **SOON:** the file's last meeting is under 183 days away;
  - **UNREADABLE:** the page could not be read. SOON still prints from the file alone.
- **What it skips:** notation votes and cancelled meetings, as the claim does.
- **It writes nothing.** Exit 0 clean, 1 a finding, 2 unreadable.
- **Where it runs:** inside the existing **heartbeat** (`scripts/check_heartbeat_cron.sh`, 08:30 ET daily), on the first of the month only, so no new unit. Its lines print as WARNINGs and never change the verdict or the exit code. `CHESTER_SKIP_FOMC_AUDIT` skips it, and `CHESTER_FOMC_AUDIT_TODAY` sets the day for a test.
- **Against the live page on 21 Oct** (saved, and read once): **clean**. The file's 2021–2027 dates match every meeting the Board publishes, the last is 8 Dec 2027, and SOON would first fire in June 2027.

### Part 4: the gate

`tools/validate_a55_box_fixes.py` is **extended**, not a new gate: groups F–H added, 31 checks (18 before), synthetic fixtures only, no network.
- **(F)** The history's rows and citations: 239, ascending and unique, from 4 Feb 1994; 14 unscheduled; every row with its page and statement; June 2007 at its printed date; no notation vote; the writer emits one event per row.
- **(G)** The audit's four outcomes on a synthetic calendar page: a missing meeting, a changed date, an unreadable page with the six-month line still printed, and the six-month warning. A clean page reads clean. The heartbeat runs the audit on the first only, warning and never verdict, and the audit writes nothing.
- **(H)** `event_rates` counting FOMC events from a synthetic claims file, through the writer into a scratch events table, with a Sunday statement skipped.

**Changed and run locally:** `validate_a55_box_fixes` 31/0, `validate_claims` 18/0, `validate_events` 95/0, `validate_audit_3a` 88/0 (the audit's catalogue line). The heartbeat's shell gates are left to CI.

**Shared files, added in round 2:** `config/claims.yaml` (chain-4 and a54 do not touch it), `altdata/events_ingest.py` (nor this), `scripts/check_heartbeat_cron.sh` (nor this), `config/catalogue_commands.yaml` (chain-4, one line each).

### Every session-set value in round 2, with its reason

| Value | Setting | Reason |
|---|---|---|
| The history's start | 4 Feb 1994, the first statement | the stored price window starts 29 Jan 1993 (SPY), and there is no statement before 1994 |
| What a row is | a meeting the page links to a statement; notation votes and cancelled meetings out | the ruling's "meeting that ended in a policy statement", applied mechanically |
| A row's date | the release date printed on the statement | the URL's date is wrong once (June 2007) |
| `fomc_audit.SIX_MONTHS_DAYS` | 183 | the Board posts the next year by summer; six months leaves several monthly runs to enter it before the rate path's four-meeting look-ahead runs past the file |
| The audit's cadence | the first of each month, inside the heartbeat | "monthly, inside an existing scheduled job"; the heartbeat is where warnings are read |
| The audit's time limit | 120 s (`timeout`) | the heartbeat must not hang on a slow page |
| `cal.fomc_history.review_date` | 2027-10-21 | a year; the monthly audit is the working check |

### Where the paste and the code differ (round 2)

1. **"The claims file the claims writer already reads".** The writer parsed only one year's value text, so it now also reads `detail.statements` (one branch in `claims_events`).
2. **"back to at least the start of the stored price history (to 2000 if…)".** The price history starts in 1993 and statements in 1994, so the history starts at the first statement.
3. **"a check audits it every so often … monthly".** It runs on the first of the month from the heartbeat, which runs daily. No unit was added.

## Needs you

1. **The alias address:** put it in `.env` as `CHESTER_SEC_CONTACT` (the one key; the senders are listed above). Name only, never in a file.
2. **`altdata/releases.py`'s BLS release files:** they are recorded as refused and may answer with the contact. Say if you want them moved to the contact host in a later order.
3. **The 23 Mar 2020 notation vote:** it carried a policy statement, and it is left out because it was not a meeting. Say if you want it in.
4. **The box commands** above, probes first, after the merge.
5. **The merge:** after chain-4 and a54-relative-volume, then main into this branch with a merge commit and a recount.
