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
| (this commit) | `tools/validate_a55_box_fixes.py`, the Makefile, CLAUDE.md, these notes |

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
- **The gap.** The claims register holds the 2026 and 2027 meetings only (`cal.fomc_2026`, `cal.fomc_2027`), so the fix finds this year's past decisions: six before 20 Oct.
  - **The meetings before 2026 are a listed gap.** The source that would fill them is the Board's historical FOMC calendar (federalreserve.gov), which no writer here fetches.
  - FRED's target-range series mark a decision day only when the target changed, so they cannot stand in for every meeting.

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
2. **Part 4:** "fix it where the store holds the dates". The store holds 2026–27 only, so the earlier meetings are a gap.
3. **Part 5:** "importlib.metadata against each requirement's name and specifier". The specifier is evaluated with `packaging`, which pip's own environment carries. Where `packaging` is absent, the requirement is counted as unchecked, never as satisfied.

## The box commands, dry runs first (the operator's)

```
cd ~/chester-reports
# Part 1 -- what failed on 20 Oct, then the backfill again after the merge (rows already stored are skipped):
grep FAILED ~/logs/fred_history.log
.venv/bin/python -m altdata.fred_history backfill --all --dry-run
.venv/bin/python -m altdata.fred_history backfill --all
# Part 3 -- the contact the BLS feeds need is CHESTER_SEC_CONTACT in .env (already set
# for the SEC if EDGAR reads); then one news pull:
.venv/bin/python -m altdata.events_ingest pull --only news
# Part 4 -- after the merge:
.venv/bin/python -m alpha.event_rates compute
# Part 5 -- the check, then the fix if it names anything:
.venv/bin/python -m altdata.requirements_check
.venv/bin/pip install -r requirements.txt
```

Run these inside the windows. `events_ingest pull --only news` and `event_rates compute` write; there is no dry-run flag on either.

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
- **The count:** 126 code gates (123 Python, three shell), counted on main's base. Chain-4 and a54 each add one, so the recount at the merges sets it.

## Files shared with chain-4 and a54-relative-volume

- **chain-4** (main plus `a52-doctrine-2-pack`): `CLAUDE.md` (the gate count), `Makefile` (one gate line each), `config/catalogue_commands.yaml` (one line each).
- **a54-relative-volume:** `CLAUDE.md` and `Makefile`, likewise.

## For session B

`alpha/event_rates.py`, `release_days`: the FOMC query reads source `IN ('claims_registry', 'claims')` in place of `= 'claims'`. Its tests keep their shape.

## Needs you

1. **The BLS contact:** confirm that bls.gov may receive the same contact form as the SEC (the 17 Oct ruling extended), or name another.
2. **The FOMC meetings before 2026:** a listed gap. Rule whether the historical calendar is entered as a claim, or fetched by a new writer.
3. **The box commands** above, dry runs first, after the merge.
4. **The merge:** after chain-4 and a54-relative-volume, then main into this branch and a recount.
