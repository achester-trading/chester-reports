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
