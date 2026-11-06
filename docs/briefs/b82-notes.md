# B82 notes: the AAII bearish share through the existing writer (D40.3)

Paste B82 (`docs/pastes/B82.md`), 28 Oct 2026. Branch `b82-aaii-bearish-share`,
base origin/main at `8166d430`. Merges after the 1 Nov Monthly.

## What changed

- `altdata/sources/aaii.py` writes `aaii.bearish_share` beside
  `aaii.bull_bear_spread`: the Bearish share of respondents in percent (0-100), from
  the same rows, by the same date, percent-or-fraction, union and time rules.
  `KEYS` is `[aaii.bull_bear_spread, aaii.bearish_share]`. One helper,
  `_survey_rows()`, makes both keys' rows from one survey, so the two cannot drift.
  - The parsers take `keys`, defaulting to the spread alone, so every existing
    caller and gate check reads exactly what it read before. The pull asks for
    both keys (`_from_file`, `_produce`).
  - `union()` keys on (key, Reported Date): the history still wins on a shared
    date, now per key.
  - No new file, fetch, robots.txt behaviour or by-hand line: the `bearish` column
    is already in `aaii-weekly.csv` and in the history file (rule 30 holds; D40.3
    is the yes).
- `metrics_registry.yaml`: `aaii.bearish_share` beside the spread, the same source,
  group, cadence, half-life and revision policy, `units: percent_share`. In the
  `families` table it is `ratio`, as the spread is. The paste said "as a percent",
  but that table holds metric families (price, rate, spread, release, quantity,
  conditions, ratio), and check_registry refuses any other word; the percent is
  the entry's `units`.
- No report prints it.

## Gate

`tools/validate_official_sources.py` already covers aaii.py (groups S and T), so
no gate is added and no count moves. Group V, nine checks, on fixtures:

1. KEYS is the spread and the bearish share.
2. A row in percents and a row in fractions give the same bearish share (34.7).
3. A row that sums to neither about 1 nor about 100 is skipped for both keys.
4. Each bearish row carries its spread row's available_at and availability_kind.
5. The default read is still the spread alone, at the same values.
6. The history's row wins on a shared date for both keys (1 Oct: 46.1, not the
   weekly file's 47.0).
7. The xls history gives both keys from one row.
8. A pull with both files writes both keys, the bearish share's union as the
   spread's.
9. Without the history file, the weekly rows alone write both keys.

Run one at a time in the foreground, all passing: validate_official_sources
(349), check_registry, validate_lenses (49), validate_audit_3a (88),
validate_weekly_edits.

## B79's hookup at the stitch (not touched here)

`config/capitulation_count.yaml` on `b79-capitulation-count`, family `flows`:
`aaii_bearish_key: null` becomes `aaii_bearish_key: aaii.bearish_share`. With the
key set, `altdata/capitulation_count.py`'s gap ("AAII's bearish share is not
stored (aaii.bull_bear_spread only)") no longer fires. The family's comment
above the key then needs the AAII half dropped. Family 5 stays unscorable while
its flows leg is a gap (J4).

## The history

The key's history arrives on the box's next
`python -m altdata.sources.aaii --history`, which is the operator's command, run
after the merge. Until then, an ordinary pull writes the bearish share only for
dates inside the 400-day write window. The two inbox files differ:

- The weekly file's rows are recent, so all of them are written.
- The history file's rows are written only inside that window. The window is held
  back only for a key that already has rows, and `aaii.bearish_share` has none
  yet. So the first ordinary pull after the merge writes the history file's
  whole bearish series if that file is still in the inbox. `--history` is needed
  only if the file has gone from the inbox.
