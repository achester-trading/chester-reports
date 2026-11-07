# A116 notes: the clock-reads gate

2 Nov 2026, session A. Branch `a116-clock-reads-gate` off origin/main at
`422ea697`. Paste committed first as `docs/pastes/A116.md`. It merges the week
after the merge week.

## The rule

The code under test reads the clock through `altdata.session`, so that pins,
replays and the as-of discipline hold. `tools/validate_clock_reads.py` scans
`altdata/`, `daily_cascade/`, `monthly_macro/`, `weekly*`, `alpha/`,
`paper_exec/` and `scripts/`, excluding `altdata/session.py` itself and all of
tools/ (the gates' pins are B106's and B110's business). `weekly*` and
`paper_exec/` do not exist on main; they are globbed, so a package of that name
is scanned the day it lands.

**A direct read** is any of these, resolved through the file's own imports
(`import datetime as dt`, `from time import time`, `import pandas as pd`):
- `datetime.now()`, `.utcnow()`, `.today()`;
- `date.today()`;
- `time.time()`, `time.time_ns()`;
- `pandas.Timestamp.now()`, `.utcnow()`, `.today()`;
- `pandas.Timestamp("now")`, `pandas.to_datetime("now")`, `numpy.datetime64("now")`.

The scan is by AST, so a string or comment mentioning "now" is no hit, and a
dated parse (`Timestamp("2026-11-02")`) is no hit.

## The allowlist

`config/clock_reads_allowlist.yaml` matches an entry by its calls and their
counts, never by line, since lines drift. Each entry keeps B106's lines for
reference, plus a one-line `burn_down` note. Gate verdicts:
- a read beyond an entry's count fails the gate, printed as file:line and call;
- an entry with no read left is reported "burned down, remove from the
  allowlist" and does not fail;
- an entry with fewer reads than listed is reported "partly burned down".

**The count.** The stitch tools are not on main, so the scan's first run on
main is the count:
- **57 direct reads in 41 files.** These are B106's inventory exactly, every
  read on the line B106 gave, so no module's read has moved since 1 Nov.
- **B106's 42nd file,** `register/heat.py` (line 151), is outside the paste's
  packages. It is listed apart under `b106_outside_scope`, never scanned, so the
  burn-down list stays B106's whole inventory.

**The hit count on main equals the allowlist: 57 reads in 41 files.**

**Two notes for the burn-down pastes:**
- **`date.today()` is the machine's date, UTC on the box,** where session's
  dates are ET. The two differ from 20:00 to 24:00 ET, so each such conversion
  must say whether the ET date is meant, and prove its output where a gate
  renders text.
- **Duration reads should move to `time.monotonic()`.** `alpha/search.py` and
  `altdata/loggers/auction.py` use `time.time()` for a duration (a wall budget,
  a polling deadline). The scan does not count `monotonic()`; route those reads
  through `altdata.session` only where the deadline must follow a pin.

**The first five burn-down notes, as examples:**

| Module | Burn-down note |
|---|---|
| alpha/ledger.py | the lab's write instant: `session.utc_iso('microseconds')`, identical text; validate_alpha's store-hash proof must hold |
| alpha/report.py | the CLI's default month: `session.session_date()[:7]` |
| alpha/search.py | the step's wall budget (`_T0` and `spent`): a duration, so `time.monotonic()`; the unit's own start is exported when present, so keep that path |
| altdata/basis_proxy.py | the ledger's run date: `session.session_date()` (an ET date where `date.today()` is the machine's; same on the laptop, differs 20:00-24:00 ET on the UTC box) |
| altdata/chain_metrics.py | both CLI windows' start: `session.session_date_obj() - timedelta(days)`; check the ET-vs-local date on the box |

## The three proofs

The proofs ran on a scratch copy of the scanned packages through the gate's own
`scan()`, `compare()` and `report()`. The worktree was not touched: this
session's permissions refused an edit-and-revert of a module in place.

| Proof | Result |
|---|---|
| 1. the tree as on main | 0 new, 0 burned down: the gate passes |
| 2. a scratch `altdata/_a116_scratch.py` calling `datetime.datetime.now()` | fails: `NEW READ  altdata/_a116_scratch.py:5  datetime.datetime.now  (0 allowlisted, 1 found)` |
| 3. `altdata/claims.py`'s one read replaced with a fixed date | passes, and says `burned down, remove from the allowlist: altdata/claims.py` |

Group C of the gate holds the same three behaviours on scratch sources, plus
"partly burned down", so they are proved on every run.

## Wiring

- **Makefile:** one line in `PY_VALIDATORS`, after `validate_quality`.
  `validate-fast` runs that same list, so the gate joins the fast set.
- **CLAUDE.md:** the gate counts go to one hundred and thirty-six code gates
  (one hundred and thirty-three Python, three shell).
- No module's clock read changed. The burn-down starts with A119.

## Gates (one at a time)

| Gate | Result |
|---|---|
| `validate_clock_reads` | 9 passed, 0 failed |
| `validate_gates` | 32 passed, 0 failed |
| `check_registry` | OK |
| `validate_audit_3a` | 88 passed, 0 failed (run as well: it reads CLAUDE.md's counts) |

## A124 (3 Nov 2026): the gate scans the whole tree

Base `ad3ecd68`. Paste committed first as `docs/pastes/A124.md`.

**The scanned set** is now every .py file in the repository, less these
exclusions, each named with its reason in the gate's header:

| Excluded | Why |
|---|---|
| `tools/` | the gates and the operator's tools; the gates pin their clocks on purpose (B106's and B110's business) |
| `tests/` | tests and their fixtures, dated on purpose |
| `smoke_test.py` | the synthetic-store smoke test, a test |
| `docs/` | documents |
| `.git/`, `.venv/`, `venv/`, `.claude/`, `build/`, `node_modules/`, `__pycache__/` | version control, interpreters, the session harness's scratch worktrees, build output, vendored packages |
| `altdata/session.py` | the one place the clock is read (as before) |

**What the wider scan adds:** `register/` (8 files), `alpha_proposer/` (5),
`state/` (2), and the root modules `run_eod.py`, `regime.py` and
`contradictions.py`. In all, 389 files are scanned.

**The new finding, one:**

| Module | Reads | Group (A119's rule) |
|---|---|---|
| register/heat.py | 1 (`datetime.datetime.now`, line 151) | IN: the rehearsed merge-week tree leaves it alone |

It joins the allowlist in A116's shape: source "A124 scan", reason "pending
burn-down", group IN, calls with counts, B106's line, and a burn-down note.
A119 has already converted it on its own branch, so the entry burns down when
A119 merges. The `b106_outside_scope` block is gone, because nothing is listed
apart any more. register/, alpha_proposer/, state/ and the root modules hold no
other direct read.

**The totals:**

| | A116 | A124 |
|---|---|---|
| Files scanned | the seven named packages | 389, the whole tree less the exclusions |
| Modules with a direct read | 41 | 42 |
| Direct reads | 57 | 58 |
| Allowlisted | 57 in 41 | 58 in 42 |

**The proofs** ran on a scratch copy of the scanned tree, as A116's did:
1. the copy as it stands: 0 new, 0 burned down; the gate passes;
2. a scratch `register/_a124_scratch.py` calling `time.time()`, outside A116's
   packages: it fails, `NEW READ  register/_a124_scratch.py:5  time.time`;
3. register/heat.py's read removed: the gate passes and says "burned down,
   remove from the allowlist: register/heat.py".

Group A gains three checks:
- each A124 entry is pending burn-down with its group;
- nothing is listed apart;
- tools/ and tests/ are never scanned (207 files).

No module was converted, and no behaviour changed.

| Gate | Result |
|---|---|
| validate_clock_reads | 11 passed, 0 failed |
| validate_gates | 32 passed, 0 failed |
| check_registry | OK |

## A119 (2 Nov 2026): the burn-down's first group

*Folded in by A132 (6 Nov 2026) from the copy of this file on `a119-clock-burn-down-1` (at `900add11`), verbatim; that copy is deleted on a119, so the one file is this one.*

**Where this section lives.** This file is a copy of A116's
`docs/briefs/a116-notes.md` from origin/a116-clock-reads-gate, made because the
file is not on main. A116's text above is unchanged; only this section is new.
When both branches merge, the second to land takes this section into the one
file.

Branch `a119-clock-burn-down-1` off origin/main at `422ea697`. Paste committed
first as `docs/pastes/A119.md`. The allowlist was read from A116's branch, not
merged.

### The selection

The test was `git diff --stat origin/main...origin/a105-merge-week-rehearsal-2
-- <module>` over the 42 modules of B106's inventory: 41 allowlisted, plus
`register/heat.py`, listed apart.

**OUT, 8 modules: the rehearsed tree changes them**, so they wait for the week
after:

| Module | Rehearsed change |
|---|---|
| alpha/ledger.py | 63 lines |
| altdata/events.py | 20 lines |
| altdata/mechanism_watch.py | 5 lines |
| altdata/security_master.py | 2 lines |
| altdata/sources/aaii.py | 137 lines |
| altdata/sources/fed_calendar.py | 2 lines |
| altdata/sources/voices_scan.py | 11 lines |
| daily_cascade/morning_payload.py | 10 lines |

**IN, 34 modules: the rehearsed tree leaves them alone.** All were converted:
- alpha/report.py, alpha/search.py;
- altdata/: basis_proxy, chain_metrics, claims, events_ingest, fomc_audit,
  fred_history, fx_charts, meme_ingest, note_fetch, paper_bid,
  return_attribution, sm_export, voices;
- altdata/ledgers/: `__init__`, `__main__`, st_r5_31b, st_r5_44b;
- altdata/loggers/auction.py;
- altdata/report/: `__main__`, export, generate, signals, weekly_scan;
- altdata/sources/: _crypto, bdf_webstat, llama, news, ons_cpi, overnight,
  statcan_cpi, upcoming_auctions;
- register/heat.py.

### The conversion: same value, same tz

| Was | Now |
|---|---|
| `datetime.now(timezone.utc)` (or `tz=`) | `session.utc_now()`, which is that call |
| `datetime.now(ET)` | `session.utc_now().astimezone(ET)`, the same instant in the module's own ET |
| `datetime.utcnow()` (naive) | `session.utc_now().replace(tzinfo=None)` |
| `date.today()` | `session.local_today()` (new, below) |
| `time.time()` | `session.utc_now().timestamp()` |

**The one missing helper: `session.local_today()`.** `date.today()` is the
machine's date (UTC on the box), not session's ET date. Mapping it to
`session_date_obj()` would change the box's output between 20:00 and 24:00 ET.
`local_today()` returns exactly what `date.today()` returns, since CPython's
`date.today()` is `date.fromtimestamp(time.time())`, but reads `utc_now()`, so a
pin reaches it. Moving any call site from it to the ET date is a behaviour
change, decided per site by a later paste.

**Imports.** A module with no top-level `session` import gained one: relative
inside altdata/ (`from . import session`, `from .. import session`), and
`from altdata import session` in alpha/ and register/. No function uses
`session` before a local import of its own (checked by AST).

**Commits, one per package:**

| Commit | Package | Reads |
|---|---|---|
| `a0142dc3` | `session.local_today()` | the helper |
| `fed9ba56` | alpha/ | 3 |
| `3ca49f80` | altdata/, top-level modules | 13 modules, 20 reads |
| `5402e154` | altdata/ledgers/ | 4 |
| `354a25fd` | altdata/loggers/auction.py | 5 |
| `78780d10` | altdata/report/ | 7 |
| `f9b5bfa5` | altdata/sources/ | 8 |
| `2cd07fb0` | register/heat.py | 1 |

**48 reads converted** in all: the 57 less the 10 in OUT modules, plus heat.py's
one.

**A note for a later paste.** `altdata/loggers/auction.py` and
`alpha/search.py` now take their deadlines from `session.utc_now().timestamp()`.
That is the same value as before, but a polling loop under a FIXED pin would
never reach its deadline. No gate runs the auction loop (it needs the IB
Gateway); `alpha/search.py`'s budget takes `now` and `started` as parameters in
its gate. A later paste may move both to `time.monotonic()`, which the scan does
not count.

### Before and after

Each converted module's gate was run on the unconverted tree, then on the
converted one, one at a time. All 25 tallies are identical:

| Gate | Before | After |
|---|---|---|
| validate_a55_box_fixes | 31/0 | 31/0 |
| validate_alpha | 257/0 | 257/0 |
| validate_alpha_lab_4 | 65/0 | 65/0 |
| validate_alpha_no_orders | 73/0 | 73/0 |
| validate_attribution | 85/0 | 85/0 |
| validate_audit_2 | 26/0 | 26/0 |
| validate_b48_scoreboard | 69/0 | 69/0 |
| validate_basis_proxy | 31/0 | 31/0 |
| validate_batch13 | 33/0 | 33/0 |
| validate_batch3_a | 79/0 | 79/0 |
| validate_claims | 18/0 | 18/0 |
| validate_crypto_basket | 93/0 | 93/0 |
| validate_crypto_sources | 117/0 | 117/0 |
| validate_events | 95/0 | 95/0 |
| validate_fred_history | 25/0 | 25/0 |
| validate_ledgers_b6 | 41/0 | 41/0 |
| validate_meme_ingest | 21/0 | 21/0 |
| validate_morning_anchor | 71/0 | 71/0 |
| validate_regime | 407/0 | 407/0 |
| validate_register | 180/0 | 180/0 |
| validate_secondary_notes | 88/0 | 88/0 |
| validate_security_master | 102/0 | 102/0 |
| validate_st_r5_t1_rest | 103/0 | 103/0 |
| validate_voices | 72/1 | 72/1 (the known date drift b101 pins; the same check fails on main) |
| validate_weekly_complete | 96/0 | 96/0 |

`altdata/sources/upcoming_auctions.py` has no gate that imports it. Its one
change is `date.today()` to `session.local_today()`, proved equal by the helper
itself.

### A116's gate against this tree

A116's `tools/validate_clock_reads.py` was run from its branch's copy, with its
allowlist, scanning this tree: 8 passed, 0 failed.
- **33 entries "burned down, remove from the allowlist":** every IN module
  except heat.py, which the gate does not scan.
- **10 direct reads remain,** in the 8 OUT files.
- **0 new.**

When A116 and A119 have both merged, the allowlist drops those 33 entries.

### Gates

| Gate | Result |
|---|---|
| the 25 above | identical before and after |
| validate_clock_reads (A116's copy, this tree) | 8 passed, 0 failed; 33 burned down |
| check_registry | OK |

### A122 (3 Nov 2026): durations onto the monotonic clock

Base `18a24e94`. Paste committed first as `docs/pastes/A122.md`.

**What was searched.** Every module A119 converted, for a deadline or an elapsed
time computed by subtracting two clock reads, session helpers included.
- **Found:** A119's two modules, three measurements, all converted.
- **Already right:** `altdata/fred_history.py` already times its run with
  `time.monotonic()`. `altdata/loggers/auction.py`'s `_seconds_until` is a
  duration to a fixed instant, read once, and stays on session.
- **Nothing else** measures elapsed time with the clock.

| Module | What it measured | Now |
|---|---|---|
| altdata/loggers/auction.py, `probe()` | the probe's window (`seconds`, default 12) | `deadline = time.monotonic() + seconds`; loop while `time.monotonic() < deadline` |
| altdata/loggers/auction.py, `sample()` | the sampler's window: `seconds`, or the time left to 16:00 ET | the length is read once (`seconds`, or `_seconds_until(16:00)` from session), then counted down on `time.monotonic()` |
| alpha/search.py, `step_budget()` | what the unit had spent: now less the unit's start (`CHESTER_UNIT_STARTED`, a wall epoch, else the process's start) | the pre-process part (`_T0 - started`, a wall difference read once at import) plus this process's elapsed time on `time.monotonic()` (`_T0_MONO`). With explicit `now` and `started` (the gate's grid) the arithmetic is unchanged |

**Timestamps did not move.** Every timestamp that is written, logged or printed
still comes from `altdata.session` as A119 left it: each auction row's
`observed_at`, the probe's `checked_at`, `_T0`. For the same instant the values
are the same; only how a duration is counted changed.

**The proof under a pinned clock.** A scratch runner, not committed, used the
b101 shape (`GATE_NOW`, `pin_clock()`) at 2026-11-16T20:55Z, with a fake
Gateway and `ib_async`. `session.utc_now()` was frozen, the same value 0.3 s
apart.
- `probe(seconds=1.5)` returned in 1.62 s.
- `sample(seconds=1.5)` returned in 1.62 s: 8 samples, 352 rows, every row
  stamped with the pinned session instant.
- `sample()` with 1.2 s left to 16:00 returned in 1.20 s.
- `step_budget`, uncapped, counted down 0.50 s over 0.5 s of wall time, and the
  gate's explicit `now=1300, started=1000` still gives 600.0.

Under A119's version each loop's condition compared a frozen clock with a fixed
deadline, so it could not end.

**The clock-reads gate.** A116's `validate_clock_reads`, from its branch's
copy, scanned this tree with the new `time.monotonic()` calls in it: 9 passed,
0 failed, 0 new. The gate does not count `time.monotonic()`.

| Gate | Result |
|---|---|
| validate_alpha_lab_4 | 65/0 |
| validate_audit_2 | 26/0 |
| validate_audit_3a | 88/0 |
| validate_alpha_no_orders | 73/0 |
| validate_clock_reads (A116's copy, this tree) | 9/0, 0 new |
| check_registry | OK |
