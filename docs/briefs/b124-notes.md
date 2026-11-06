# B124 notes: the heartbeat-caller gate on the laptop

Paste B124 (`docs/pastes/B124.md`), 2 Nov 2026. Branch `b100-hygiene`, from `72406edd`.

## Where the 300 seconds went

The gate has **no sleep, no timeout it waits out, and no loop on the real clock**.
It runs the heartbeat wrapper (`scripts/check_heartbeat_cron.sh`) about seventy
times, and on the laptop each run cost 2 to 14 s in process starts:

- **The repo's whole unit set, on every run.** The wrapper compares each unit in
  `deploy/systemd/` (59 files) with the installed copy, and asks systemctl about
  each `chester-*.service`. Each is a few processes. A unit-drift run cost 7–8 s
  and a `run_units` run 12–14 s; about 30 of the gate's runs are of these kinds.
- **Four checks no section asserts on:** the exceptions, listings, requirements
  and FOMC-audit checks. Each started an interpreter on every run, about 1 s a run.
- **The interpreter.** The wrapper looks for `.venv/bin/python` and otherwise takes
  `python3`. The laptop's venv is `.venv/Scripts/`, so the wrapper ran on the
  system Python, which lacks the repo's packages. The gate's own seeding already
  falls back to `.venv/Scripts/python.exe`, so the two used different
  interpreters, and **the feed section's three checks failed on the laptop**
  (feeds=stale where fresh was wanted). CI's `python3` has the packages, so CI never
  saw this.

## The knobs

Two new knobs in the wrapper, each unset on the box, so production is unchanged:

| Knob | Default (unset) | The gate sets |
|---|---|---|
| `CHESTER_STATE_PY` | as before: `.venv/bin/python`, else `python3`, else `python` | the venv it resolves (`.venv/bin/python`, else `.venv/Scripts/python.exe`, else `python3`) |
| `CHESTER_UNIT_SRC` | `$REPO/deploy/systemd`, as before | a sandbox copy of the repo's bytes for the eight units its checks name, plus `box-config.allow` |

The four existing skip switches, set in every gate run except the section that
tests that check:
- `CHESTER_SKIP_EXCEPTION_CHECK`: `run_exc` turns it back on.
- `CHESTER_SKIP_LISTINGS_CHECK`: `listings_run` turns it back on.
- `CHESTER_SKIP_REQUIREMENTS_CHECK` and `CHESTER_SKIP_FOMC_AUDIT`: no section tests
  either.

The one check about the repo's whole set, "installed units matching the repo, so
clean", still runs against all of `deploy/systemd/`.

Printed with both knobs unset: `UNIT_SRC = $REPO/deploy/systemd`, and `STATE_PY`
from the old lookup.

## Before and after

| | Run time | Checks |
|---|---|---|
| Before | 445 s | 110: 107 passed, 3 failed (the feed section, the interpreter) |
| After (three runs) | 152 s, 155 s | 110: 110 passed, the same check lines in the same order |

**Not under two minutes.** What remains is about 75 wrapper runs at 1–2 s each.
Each run does dozens of small `sed`, `date`, `cmp` and `basename` calls, about
60 ms each on Windows, plus the claims call (0.2 s), which has no skip switch.
None of that is a wait or a knob. Getting lower means fewer runs (fewer checks) or
a change to the wrapper's own logic, and the paste rules out both. The gate now
clears A105's 300 s cap with room to spare. CI is Linux, where a process starts in
a fraction of that time.

`bash -n` passes on both files. shellcheck is not installed.

## Gates

- validate_heartbeat_caller: 110 passed, 0 failed (155 s).
- validate_deploy: 154 passed, 0 failed.
- validate_gates: 32 passed, 0 failed.
- check_registry: OK.
