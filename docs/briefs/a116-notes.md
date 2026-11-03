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
