# A78 notes: Batch 16 filed, the midterm table and the 3 Nov Ahead row

Session A, 26 Oct 2026. Branch `a78-batch-16-midterm`. It merges Wednesday 28 Oct
2026 by its own PR, after A61b and before the dry run (H6).

## Base

`origin/a61b-feed-repair` at **caa5f99fe27982b032bdeba40695cd8d2c8f5706** ("A75 notes:
CI queued, run 40155010604"). `origin/main` (41803980) is an ancestor of it.

Batch 15 (`a58-batch15-1`, 48caa512) is **not** on this base. It is on
a58-batch15-1 and the branches that follow it, which merge with chain-8. Its order
was read from 48caa512 for the shape. Its register line, its index line and
`tools/validate_batch15_1.py` are therefore not on this branch, so that gate was
not run (see needs-you 2).

## What was done

1. **The paste and the order, verbatim:** `docs/pastes/A78.md` and
   `docs/pastes/A78-attachment-round-7.md`. The attachment is the triage chat's file
   from Downloads, byte for byte. Committed first.
2. **The order, filed:** `docs/change-order-signal-triage-batch-16-2026-10-26.md`.
   It follows Batch 15's shape: a new header table, a §0 holding H1 to H7, then the
   order verbatim from §1 with H1's renumbering applied. The renumbering was made
   by a script, and every token it changed was listed and checked by hand. It
   changed 81 lines and made no false rewrites. Four misses, numbers ending a
   clause, were found and fixed. Two things were deliberately left alone:
   - the operator's quoted "82 accepted" stays verbatim and is annotated in place;
   - the Sources section's URLs are untouched.
3. **The register:**
   - The batch-orders cell gains Batch 16, added by hand.
   - Provisional rows **SR-60 to SR-64**, the next free numbers after SR-59 (SR-55
     and SR-58 are reserved). No remote branch uses any SR above 59. The rows are
     80(b)+90, 83(b), 88, 89(a) and 89(b), each "provisional, placed by Audit #5".
   - The amendments are recorded against their filed parents.
   - `docs/change-orders.md` gains its index line.
4. **The ledger:** `docs/ledgers/midterm-base-rate-2026-10-26.md` and its CSV, from
   `tools/calibration/midterm_base_rate.py --db <laptop store> --date 2026-10-26`.
   The computation is printed at the head with SHA-256 `8c8fa32c…`, and the CSV
   with `805487ec…`.
5. **The Ahead row:** `config/weekly_ahead.yaml` adds class `us_election` (tier 2)
   and `register_event_rows` for `cal.midterm_election_2026`.
   `daily_cascade/ahead.py` adds `odds_line()`, which reads the House and Senate
   watch ids from the store the Weekly opened (`db_path`), and `register_rows()`,
   which uses the named row. The base rate prints after the channel in "Why it
   matters". `daily_cascade/weekly_sections.py` is untouched, so the Transition
   count's line prints as before.
6. **The dated-appendix entry:** one entry, "For the Base Rates paper (Batch 16
   items 80(b) and 90)", pointing at the ledger beside Table 7. No paper body was
   edited.
7. **The gate:** `tools/validate_batch16_midterm.py` (27 checks, fixtures only),
   added to the Makefile. CLAUDE.md gains one paragraph. Its printed gate count goes
   from 134 to 135 code gates and from 131 to 132 Python, because
   `validate_audit_3a` holds that count to the Makefile.

## H1's mapping

Within the order, written 72–84 become filed 79–91, in order. Earlier items were
resolved by subject:

| Written | Filed | Subject |
|---|---|---|
| 64 | 72 | gold-ETF ownership (Batch 15) |
| 66 | 73 | gold event trigger (Batch 15) |
| 67 | 74 | hedge-fund squeeze (Batch 15) |
| 68 | 75 | AI-lab financials, the Anthropic S-1 (Batch 15) |
| 69 | 76 | CDS line, neocloud names (Batch 15) |
| 56 | 63 | AI capex chain (Batch 14 F1) |
| 58 | 65 | one big AI trade (Batch 14 F1) |
| 47, 16, 45, 46, 49, 51, 52 | unchanged | checked by subject against their orders' headings |
| "batch-5 item 12" (diesel vs CPI) | batch-4 item 12 | the diesel item is Batch 4's |
| "batch-5 item 25" (the 1994-vs-2011 shape) | batch-4 item 15, SR-49 | Batch 5's item 25 is AQR's sensitivities, not this |

**Unresolved: none.** The two batch-label corrections are resolutions by subject,
so they are listed for confirmation (needs-you 3).

## The ledger's headline figures (laptop store; the box recomputes)

The laptop store's S&P 500 closes run from 1927-12-30 to **2026-09-21**. The store
holds **no `fred.usrec`**, so the recession column reads "not stored" on all 19
rows.

- **The year's drawdown:**
  - Midterm years (n 19): median **−16.6%**, mean **−17.5%**.
  - The other 57 years, 1950–2025: median **−9.9%**, mean **−12.4%**.
- **Where the lows fell.** The low is the trough of the year's drawdown, as the
  computation pre-registers. It came before election day in **17 of 19** years:
  - **10 of 19** were in August to October;
  - the median low was **63** calendar days before election day;
  - the two after election day are 1978 (14 Nov) and 2018 (24 Dec).
- **From election day:**
  - median **+7.6%** at 3 months;
  - higher at 12 months in **19 of 19**, median **+14.5%**;
  - the other years from the same day were higher in **39 of 56**.
- **From the low (hindsight, as the caveat says):** higher at 12 months in 19 of 19,
  mean **+32.0%**.
- **V11, chat against ledger:**

  | Figure | Chat | Ledger |
  |---|---|---|
  | 1974 | −35% | −37.6% |
  | 2022 | −27% | −25.4% |
  | 1986 | ≈ −9% | −9.4% |
  | 2006 | ≈ −8% | −7.7% |
  | 2014 | ≈ −7% | −7.4% |
  | Midterm years | ≈ 17–19% | mean −17.5% |
  | All years since 1980 | ≈ 14% | mean −14.1% |
  | Lows in late summer to October | "usually" | 10 of 19 |
  | 12 months from the low | ≈ +30% | +32.0% |
  | 2026 to date | −9% through 30 Sep | −9.1% through 21 Sep |

## The tier mapping

The calendar has three tiers: 1 moves every market, 3 moves one. The order uses a
1–5 significance scale with 5 highest. The mapping used is **5 → 1, 4 → 2,
1–3 → 3**. The midterm is significance 4, so it goes in **tier 2**, through its own
class `us_election`. That is the tier the register event already printed at, and
every tier prints.

## Gates run locally

All were run with the main checkout's venv, because the worktree has none:

| Gate | Result |
|---|---|
| `validate_batch16_midterm` | 27/0 |
| `validate_weekly_complete` | 96/0 |
| `validate_weekly_calendar` | 44/0, after one check was updated (below) |
| `check_registry` | OK, exit 0 |
| `check_library` | 27 papers, 0 failures, 0 warnings |
| `validate_audit_3a` | 88/0; the gate count was bumped |
| `validate_base_rates` | 76/0 |
| `validate_monthly` | 359/0, 1 skipped |
| `validate_secrets` | 58/0 |

`validate_batch15_1` is not on this base and was not run (needs-you 2).

The `validate_weekly_calendar` check that was updated is the midterm register row's
class. That check now accepts the class `register_event_rows` names (`us_election`)
in place of the generic `register_event`. The date and the one-row count are
unchanged.

## CI

CI in progress at push, run 40333495867 (Gates), on 62e19d19. The next paste on this branch reads it.

## Box steps, Wednesday 28 Oct 2026 (ruling 1 of A78's needs-you)

These run after A78 merges and before the dry run. The box runs steps 1, 2 and 4.
The box never edits the repo, so step 3 is not a box command.

```
# 1. Trial run into a scratch directory; nothing in docs/ledgers is touched
python tools/calibration/midterm_base_rate.py --box --date 2026-10-28 --out /tmp/midterm-trial
#    check: n 19, the recession column says yes/no rather than "not stored",
#    and the as-of date is the latest close

# 2. The real run, OUTSIDE the checkout (where the wealth ledger's box edition
#    lives too), so git pull --ff-only is never blocked
python tools/calibration/midterm_base_rate.py --box --date 2026-10-28 --out ~/chester-data/ledgers/

# 4. Check
python tools/validate_batch16_midterm.py
```

**Step 3, the copy-back, is done by a session paste on main after the box run.**
The operator copies the dated ledger and its CSV from `~/chester-data/ledgers/` back to the laptop. A short
paste then commits them and makes three changes:

- the "> " headline line from `docs/ledgers/midterm-base-rate-2026-10-28.md`
  goes into `config/weekly_ahead.yaml`, under `register_event_rows` ->
  `cal.midterm_election_2026`, as `base_rate`;
- that entry's `ledger:` field points at the new file;
- the `LEDGER` constant in `tools/validate_batch16_midterm.py` points at the new
  file.

That paste is merged and deployed before the dry run. The 26 Oct ledger is
never edited.

Two cautions for the sheet:

- **Step 4 on the box still checks the 26 Oct ledger.** The `LEDGER` constant
  changes only in step 3's paste, so step 4 on the box shows that the gate
  passes, not that the new ledger matches. The paste's own run of the gate is
  the check that the new ledger and the config match.
- **Step 2 writes outside the checkout** (ruled 26 Oct 2026). The two files land in
  `~/chester-data/ledgers/`, never in the box's `docs/ledgers/`. That means no
  untracked file is in the way when step 3's commit adds the same paths, and the
  box's `git pull --ff-only` is never blocked.

## Needs-you (five)

1. **The recession column needs the box.** `fred.usrec` is not in the laptop's
   store, so the laptop ledger's flag reads "not stored". The box holds the FRED
   pull. A box run is the operator's:
   `python tools/calibration/midterm_base_rate.py --box --date <D>`.
   It writes a new dated ledger; this one is never edited. The session that files
   it copies the new headline into `config/weekly_ahead.yaml`, and the gate holds
   the two together.
2. **The merge order with Batch 15.** Batch 15's register line and index line sit
   on a58-batch15-1 and chain-8, and this branch adds the Batch 16 lines to the same
   cell and table. Whichever merges second keeps both lines. Every branch that adds
   a gate also bumps CLAUDE.md's count, so that needs a recount too.
3. **Confirm two H1 resolutions and one definition:**
   - "batch-5 item 12" was read as batch-4 item 12, and "batch-5 item 25" as
     batch-4 item 15 (SR-49).
   - The "year's low" is the trough of the year's drawdown, not the calendar year's
     lowest close. The lowest close put 1950's and 1954's lows in early January.
     The lowest close's date is kept in the CSV.
4. **The odds path is proved on fixtures only.** The laptop store holds no
   prediction-market rows, so the venues' outcome labels for `house_control` and
   `senate_control` were not seen. The row matches the declared side's stem
   ("democrat") in the outcome or the question. The 28 Oct dry run is the first real
   render. If it prints "Kalshi not stored" beside a stored market, the label did
   not match.
5. **The 2026-to-date figure.** The laptop store ends 21 Sep, so the V11 row for
   2026 compares −9.1% through 21 Sep with the chat's −9% through 30 Sep. The box
   edition will run later.
