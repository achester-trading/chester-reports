# B101 notes: two gates pinned to their fixtures' clocks

Paste B101 (`docs/pastes/B101.md`), 1 Nov 2026. Branch `b101-date-drift-gates`,
base origin/main at `422ea697`. It merges in Tuesday's first small PR with A91's
fix. In both gates only the clock changed; neither gate's checks did.

## validate_monthly

**The failing check on main (1 Nov 2026), verbatim:**

```
  FAIL  the refunding is expected only in a window holding February, May, August or November, and is never flagged missing from another ({'November': True, 'December–January': False})
359 passed, 1 failed, 1 skipped
```

**Where the clock entered.** The whole fixture month is dated from
`session.session_date()`, which reads `session.utc_now()`:
- the seeded month and its month-ends;
- the look-ahead's windows: the rest of this month, then the two after;
- group D's replay cutoff (`dt.date.today()`);
- the object's "seen" instant (`dt.datetime.now()`).

From 1 Nov the last window is "December–January". The renderer is right that no
refunding falls in it (`expected: False`).

**A latent gate defect, recorded and not changed.** The gate's own expectation
computes a window's months as `range(min(ms), max(ms) + 1)`, which for {12, 1}
is January through December. So it counts that window as due, and the gate
would fail every November. Changing that line would change what the gate checks,
which this paste rules out; the pin removes the dependence on the calendar
instead. If the pin is ever lifted, fix the wrap first.

**The pin.**
- `GATE_NOW = "2026-10-15T20:45:00+00:00"`, a Thursday close in mid-October.
  Its windows are "October" and "November–December", so the refunding check
  sees one window that is due and one that is not.
- `main()` sets `session.utc_now` to it for the gate's run.
- The two direct reads now go through the same session clock:
  - group D's cutoff is `session.session_date_obj()`;
  - the "seen" instant is `session.utc_now()`.

The Monthly's own code reads the clock only through `altdata.session`, so nothing
under test was touched.

## validate_st_t5_render

**The failing check on main (1 Nov 2026).** It crashed rather than reported a
FAIL, after 12 checks passed:

```
  File "tools/validate_st_t5_render.py", line 413, in group_d
    check(cand["table"]["rows"][0][1] == "Lumen" and "(draft)" in cand["table"]["rows"][0][4]
TypeError: 'NoneType' object is not subscriptable
```

That is the check "the Monthly part prints the month's candidates, status
changes and drafted entries from the register".

**Where the clock entered.**
- The fixture is fixed at `NOW = 2026-10-31T22:00Z`, and group D runs the scan
  with `now=NOW`.
- But `write_drafts` and `post_entries` stamp the draft with
  `mechanism_watch._now()`, the wall clock.
- From 1 Nov the candidate's `first_seen` lay outside the part's
  `(THEN, NOW]` month, so the candidates table was empty.

**Not a defect in the code under test.** In production `run` is never given a
`now`: the CLI and `scripts/run_crypto_basket.sh` call it bare, so `now` and the
wall clock are the same instant.

**The pin.** `pin_clock()`, called first in `main()`, sets `session.utc_now` to
NOW and `mechanism_watch._now` to NOW for the gate's run.

## The three runs per gate

The real clock was shifted with a scratch wrapper. It replaces `datetime.datetime`
and `datetime.date` before the gate is imported, so every read of the real clock
sees the target day. The same wrapper on the base reproduced both failures,
which shows it reaches the clock the gates read.

| Gate | 29 Oct | 1 Nov | 2 Dec |
|---|---|---|---|
| validate_monthly, base | 360 / 0 (1 skipped) | 359 / 1 (the real clock) | 360 / 0 (1 skipped) |
| validate_monthly, branch | 360 / 0 (1 skipped) | 360 / 0 (1 skipped) | 360 / 0 (1 skipped) |
| validate_st_t5_render, base | 46 / 0 | crash in group D (the real clock) | crash in group D |
| validate_st_t5_render, branch | 46 / 0 | 46 / 0 | 46 / 0 |

- **The real clock on the branch, unshifted:** validate_monthly 360/0 with 1
  skipped, and validate_st_t5_render 46/0.
- **Mid-November on the base:** validate_monthly also fails at 16 Nov, the same
  check, so its failure is the whole month of November and not one day.

## B101b: validate_voices pinned; the year-end wrap fixed

Paste B101b (`docs/pastes/B101b.md`), 1 Nov 2026, continuing on this branch
from `cc718cfb`.

### validate_voices

**The failing check on main (1 Nov 2026), verbatim:**

```
  FAIL  the Monthly's section 4: monthly status, 13F dated to its period of report, the weeks rolled up by story, the consensus line
72 passed, 1 failed
```

The failing part of the check is the 13F column: Kilo's row printed "—" where
"13F-HR for 2026-06-30" was expected.

**Where the clock entered.**
- The 13F pull (`voices_scan.pull_13f`) stamps `retrieved_at` with
  `session.utc_iso()`, the real clock. So do the store's other writes.
- The gate reads the Monthly's block as of a fixed `2026-11-01T12:00Z`.
- From that instant on, the filing was retrieved after the cutoff, and the block
  rightly left it out.

That is point-in-time behaviour, and it is correct, so there was nothing to
report as a defect. It is also why the base fails at 2 Dec.

**The pin.**
- `GATE_NOW = "2026-11-01T11:00:00+00:00"`. It falls after every fixture row and
  before the month block's cutoff, which is the last instant the base passed.
- `pin_clock()`, first in `main()`, sets `session.utc_now` to it for the gate's
  run only.
- Two cutoffs had been taken from the real clock so that they would follow the
  scan's stamp (T3.2): the daily line and the week section. They now read
  `session.utc_now()`, the same clock the scan stamps with.

| validate_voices | 29 Oct | 1 Nov | 2 Dec |
|---|---|---|---|
| base | 73 / 0 | 72 / 1 | 72 / 1 |
| branch | 73 / 0 | 73 / 0 | 73 / 0 |

The branch on the real clock, unshifted: 73 / 0.

### validate_monthly: the window-months helper

**Before**, inline in the refunding check:

```python
months_of = {w["name"]: {int(w["first"][5:7]), int(w["last"][5:7])} ...}
refund_due = {n for n, ms in months_of.items()
              if ms & {2, 5, 8, 11} or any(m in (2, 5, 8, 11) for m in
                                           range(min(ms), max(ms) + 1))}
```

For {12, 1} that range is January to December, so December–January counted as
due.

**After.** `window_months(first, last)` walks month by month from the first to
the last, across the year end. The due set is `window_months(...) ∩ {2, 5, 8,
11}`. The refunding rule is unchanged.

**The fixture case added.** One check, "a window across the year end holds
exactly its own months":
- December–January is `[12, 1]`, not due;
- November–January is `[11, 12, 1]`, due;
- a single October window is `[10]`.

**Tallies.** B101's pin is kept at `2026-10-15T20:45Z`.

| Run | Windows | Tally |
|---|---|---|
| pinned, as committed | October, November–December | 361 / 0 (1 skipped) |
| GATE_NOW set to 2026-11-16, a temporary copy, never committed | November, December–January | 361 / 0 (1 skipped) |

In the 16 Nov run, the refunding check printed
`{'November': True, 'December–January': False}` and passed.
