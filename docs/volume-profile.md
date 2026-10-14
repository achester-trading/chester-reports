# The volume profile

Ruled by the operator at 04:39 CT on 14 October 2026; built as VP-1. The code is
`altdata/volume_profile.py`, the settings are `config/volume_profile.yaml`, and
the gate is `tools/validate_volume_profile.py`.

A volume profile shows where volume traded, by price, over a window. The reports
print it as data: tables, one chart panel and listed levels. They do not claim
anything about what it predicts.

## What it is not

The profile describes where volume traded, and that is all it describes. No
report says a value-area edge will hold, that price will return to a point of
control, or that a low-volume node will be crossed quickly. Those are claims, and
they are pre-registered for the Alpha Lab as **H-006 to H-008**. Testing them is
the lab's job, so this repository runs no backtest of them. The Book B scanner
prints two daily-bar readings beside each candidate, and nothing reads them: not
the score, the gates, the timing or the grading. Whether they matter is H-006's
question.

## The definition

One module computes the profile, and every reader calls it. No reader bins
volume itself.

1. **Bins.** Prices sit on a fixed grid at whole multiples of the bin width. The
   width is `bin_bps` of the window's last close, rounded **down** to the nearest
   step of the ladder: 0.01, 0.02, 0.05, 0.10, 0.25, 0.50, 1, 2, 5, 10. `bin_bps`
   is 5 for profiles from 5-minute bars and 25 for profiles from daily bars.
   This is what "rounded to a round tick" means in H-006 to H-008.
2. **Volume at price.** Each bar's volume is spread evenly over its high-low
   range, and each bin takes the share of the range it covers. A high exactly on
   a bin edge covers none of the bin above it. A bar with high = low puts all its
   volume in its one bin.
3. **Point of control (POC).** The POC is the bin with the most volume, and its
   value is the bin's midpoint. A tie goes to the bin nearest the window's
   volume-weighted mean price; if two tied bins are equally near, the lower
   wins. The mean is the profile's own: each bin's midpoint, weighted by its
   volume.
4. **Value area.** The value area holds `value_area_share` (0.70) of the
   window's volume, and is built outward from the POC:
   - compare the next two bins above with the next two below (fewer where the
     profile ends);
   - add the pair with more volume, or both pairs on a tie;
   - repeat until the share is reached.

   **VAH** is the upper edge of the highest bin in the area, and **VAL** the
   lower edge of the lowest.
5. **Nodes.** The profile over the bins between the window's low and high is
   smoothed with a centred 5-bin mean, truncated at the ends.
   - A **high-volume node (HVN)** is a local maximum of the smoothed profile at
     or above its 80th percentile.
   - A **low-volume node (LVN)** is a local minimum at or below its 20th.

   Only interior bins can be nodes; the profile's tails are not. A plateau
   counts once, at its first bin.
6. **Completeness.** A window of 5-minute bars is computed only when its bars
   reach the bars table's `bars.complete_share` (0.90, in
   `config/reporting_stack.yaml`) of the expected count, in aggregate. Otherwise
   the window is absent, with a reason that names every session below the share,
   as VWAP's is: "bars incomplete (n=186 of 234); below the share: 2026-10-07
   (30 of 78)".
7. **One source per window.** If a window's bars come from more than one source,
   as when 6b's history lands beside Yahoo's, the window is absent with the
   reason. Sources are never mixed.
8. **As of.** Every read of 5-minute bars goes through `BarStore.read(as_of=...)`,
   and every read of daily bars through `ObservationStore.as_of` (rule 1 of
   `altdata/derived.py`). A bar the system could not have known at the cutoff
   cannot change a profile. A profile from daily bars prints "approximated from
   daily bars" wherever it appears.
9. **Instruments.** v1 covers spy, qqq and iwm: the tape instruments whose
   5-minute bars carry volume. The rest of the tape is out, each for a reason:
   - es, gold and oil are futures, which roll contracts;
   - Bitcoin's volume is an aggregate across venues;
   - the indices and the yields carry no volume.

## The windows

The level list carries six windows, as of the edition's session:

| Window | Sessions | Status |
|---|---|---|
| the session | the day itself | none |
| the prior session | the session before | held / broke / untested |
| the week | Monday of the week to the day | none |
| the prior week | the whole calendar week before | held / broke / untested |
| the month | the 1st of the month to the day | none |
| the prior month | the whole calendar month before | held / broke / untested |

The prior windows' levels carry a status by `levels.status_of`, because they were
known before the session. The current windows' levels carry none, like the
session high and low. Each level is labelled by its window ("prior week's
value-area high") and appended after the older level types, so every existing
line keeps its order. The flat row carries each level under its field name, for
example `vp_prior_week_vah`.

**The label audit.** It knows three names: point of control or POC; value-area
high or VAH; value-area low or VAL.
- A bare name binds to that field in any window, for the sentence's symbol.
- A qualified name binds to its own window only: "the session's", "the prior
  session's" or "yesterday's", "the week's", "the prior week's", "the month's",
  "the prior month's".

So a wrong figure beside "the prior week's value-area high" is withheld, as the
30 September put wall was.

## Where it prints

- **The close.** The tape section carries a table: Market | Value area (POC) |
  Prior session | Migration | Close vs value. C1 shades the prior session's value
  area, and returns its VAH and VAL in `drawn`.
- **The Weekly.** The same table compares the week with the prior week, in the
  tape section beside the levels table. W7 gains a volume-at-price panel on the
  same price axis, covering the sessions it draws:
  - this week's sessions in a darker step of one hue, the earlier sessions in a
    lighter step;
  - the week's POC marked and its value area shaded;
  - a legend, and a caption written from the data.

  W7 is still one chart, and the cap of ten charts is unchanged.
- **The Monthly.** The same table compares the month with the prior month, as a
  subsection of the month in markets.
- **Book B.** Each candidate line carries two readings from daily bars, labelled
  "approximated from daily bars":
  - the base's POC, from the base's own N sessions;
  - the nearest HVN between the entry and the +1R target, from the last 252
    sessions, with its price and distance, or "none".

**Migration** is set by declared rule, comparing the value area with the prior
one:

| Migration | Rule |
|---|---|
| higher | VAL above the prior VAH |
| lower | VAH below the prior VAL |
| unchanged | both edges equal |
| inside | within the prior area |
| outside | containing it |
| overlapping higher | both edges higher, still overlapping |
| overlapping lower | both edges lower, still overlapping |

**Close vs value** is above the VAH, inside, or below the VAL.

The prose cites the same levels as before: `figure_budget.tape_levels` does not
offer the profile's levels in v1.

## The stored series

For spy, qqq and iwm, the module writes six series each, eighteen in all:
- `calc.vp_<id>_session_poc`, `_vah` and `_val`, over the session;
- `calc.vp_<id>_20s_poc`, `_vah` and `_val`, over a rolling composite of the 20
  sessions ending at the session.

They exist for the Alpha Lab's rule grammar. Each is registered in
`metrics_registry.yaml` as derived_state, calculated, recomputed, price, daily,
with a half-life of a session, and none is trigger-eligible. Each row's
`available_at` is the latest `available_at` among its input bars.

`python -m altdata.volume_profile compute [--from DATE|first]` writes them, and
`scripts/run_eod_cron.sh` runs it after the derived-features step, on the same
never-fatal pattern. With no `--from`, the compute recomputes the last
`compute_lookback_days` of sessions. `--from first` starts at the earliest stored
5-minute bar.

## The measurements

Two read-only commands, for the box:

- `python -m altdata.volume_profile coverage --instrument spy --sessions 40`
  shows the share of each session's daily volume (the yfinance `_volume`
  companion) that its 5-minute bars carry.
- `python -m altdata.volume_profile compare --instrument spy --sessions 40`
  compares the 5-minute profile with the daily-bar approximation over the same
  windows, the 20-session composite ending at each session. It gives the POC
  distance in daily bins and the value areas' overlap (intersection over union).

## The settings

Every value in `config/volume_profile.yaml` is session-set: chosen when VP-1 was
written, not measured.

| Setting | Value |
|---|---|
| `instruments` | spy, qqq, iwm |
| `bin_bps.five_minute` | 5 |
| `bin_bps.daily` | 25 |
| `tick_ladder` | 0.01 … 10 |
| `value_area_share` | 0.70 |
| `node_smoothing_bins` | 5 |
| `hvn_percentile` | 80 |
| `lvn_percentile` | 20 |
| `composite_sessions` | 20 |
| `scanner_hvn_sessions` | 252 |
| `compute_lookback_days` | 7 |
