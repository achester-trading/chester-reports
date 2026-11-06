# B95 notes: the Cboe hold (Part 2, D45)

Branch `b95-cboe-held`, from `origin/main` at `422ea697`. Paste B95, Part 2. Ruling D45 (31 Oct 2026, 10:33 ET): the two Cboe readers fail the 16 Oct sources rule on the terms' storage clause (the check of 30 Oct, `docs/briefs/cboe-terms-check-2026-10.md`). Their new pulls stop at the merge of 3 Nov, as a declared hold. The stored rows are kept, and Doctrine #2 (7–8 Nov) rules on what happens next.

## The declarations

In `source_registry.yaml`, both entries carry the same four fields:

```
  cboe:                      # the VX futures curve (altdata/loggers/vxcurve.py)
    held_since: "2026-11-03"
    held_reason: "Cboe terms, storage in a retrieval system forbidden (checked 30 Oct 2026); held pending Doctrine #2; held from 2026-11-03, the date of the merge"
    held_line: "held pending Doctrine #2 (Cboe terms)"
    status: held          # was: active (lift: status: active)

  cboe_indices:              # COR1M, COR3M, DSPX (altdata/sources/cboe_indices.py)
    held_since: "2026-11-03"
    held_reason: (the same)
    held_line: "held pending Doctrine #2 (Cboe terms)"
    status: held          # was: live (lift: status: live)
```

In `metrics_registry.yaml` `member_overrides`, ten keys are declared held, each with `held_source` and the reason as `gap_reason`:
- **cboe_indices:** `cboe.cor1m`, `cboe.cor3m`, `cboe.dspx`.
- **cboe:** `cfe.vx_settle`, `cfe.vx1`, `cfe.vx2`, `cfe.vx3`, `calc.vx_front_slope`, `calc.vx_front_ratio`, `calc.vx1_vix_basis`.
- **Not held:** `cfe.vx_probe`. It is written only when no contract answers, and a held logger no longer probes.

**The date.** The hold takes effect when the code reaches the box, which is the merge. `held_since` records 2026-11-03, the paste's merge date, and the reason says so. The hold does not test the date: if the branch merged earlier, it would hold from then.

## The pattern (a61b's, extended)

The new status follows a61b's refusals (`docs/briefs/a61b-feed-repair-notes.md`), with one difference: a refused source cannot be read, while a held source can be read but its terms forbid storing it.

| Piece | Where |
|---|---|
| `held` is a declared status, never stale | `altdata/derived.py` `DECLARED_STATUSES`; `tools/check_store_registry.py` `QUIET_STATUSES` |
| The helpers: `hold`, `held_text`, `key_hold`, `key_text`, `held_leg`, `last_stored` | `altdata/refusals.py` (not a writer, so reports may import it) |
| A held run asks nothing and returns `HELD` with the reason and the last stored date | `altdata/sources/_publication.py` `held()` |
| The readers check it before any request: no robots read, no file, no probe | `cboe_indices.pull`, `vxcurve.pull` |
| A HELD run is no writer failure | `altdata/feeds.py` `writer_failures` |
| The store check and the heartbeat's roster count the keys as declared | through `derived.declared_status`, as for a refusal |

`key_hold` needs both halves: the key declared held **and** its source held in the source registry. A gate that sets an empty source registry (`refusals.set_registry({"sources": {}})`) therefore sees no hold. That is how `validate_st_r4_t1b` groups A–G still test the reader and the panel on fixtures.

**Nothing is purged.** Neither reader deletes rows, and no purge is added.

## What goes dark, by report and block

Every block below prints "not tracked: held pending Doctrine #2 (Cboe terms)". Where it can read the store, it adds ", last stored <date>".

| Report | Block | What prints while held |
|---|---|---|
| **Weekly** (Sunday 05:00) | Mechanics, the dispersion panel (ST-R4.18a) | The DSPX, COR1M and COR3M rows print the line with their last stored date in the As-of column. The "dispersion regime" flag reads "withheld: DSPX not tracked: …". The high-dispersion/low-correlation line does not print. Yahoo's `^DSPX`/`^COR*` fallback is **not** used (see "Left for Doctrine #2"). |
| **Weekly** | Mechanics, "Vol term structure — the dual run" | The champion row (`calc.vx_front_ratio`, VX2/VX1) prints the line instead of a state and ratio. The basis prints "basis (VX1 less VIX): not tracked: …". The challenger and the published state print as before. |
| **Monthly** (stacked, 1st) | Mechanics, the dispersion panel | Same as the Weekly, through the same builder at cadence "monthly". |
| **Monthly** (v2 fallback) | The vol dial's term-structure lines | The champion prints the line, and so does the basis. |
| **Monthly** (v2) | The volatility theme's metric table (`cfe.vx1`, "Front-month VIX future") | Moves to "not yet tracked" with the line and the last stored date. |
| **Daily close** (16:45) and the next **07:00 anchor** | A fired volatility event's breadth lens (Batch 9 item 52) | "implied correlation (COR3M) not tracked: …; dispersion (DSPX) not tracked: …". The other eight lenses are unchanged. |
| **Narrative register** | The story "End of the bond bull, the active era" (linked to `cboe.dspx`, `cboe.cor3m`) | Its DSPX series evidence is not counted ("input held"). A forecast on it resolves to no outcome, reason "input held: cboe.dspx not tracked: …", so no grade is written while held. |
| **Store check, heartbeat** | Freshness | The ten keys are listed as declared (status `held`, newest date), never stale. The two writers' HELD runs are no failure. |

**Unchanged:**
- **The vol dial.** It reads `yfinance.mkt_vix` (primary), `fred.vix` (FRED's VIXCLS) and `calc.vol_spy_realized_20d` (`config/market_state.yaml`, `dimensions.volatility.members`).
- **The published term-structure state.** It reads the challenger, `calc.vix3m_over_vix` (`dials.vol.term_structure`, `published: challenger`). `altdata/market_features.py` computes it as `yfinance.mkt_vix3m` over `yfinance.mkt_vix` (lines 107–108 and 808–811).
- **The paste assumed FRED's VIXCLS and VXVCLS; the code does not read VXVCLS.** The VIX3M leg is Yahoo's `^VIX3M`, and `VXVCLS` appears nowhere in the registry. FRED's VIXCLS is a member of the volatility dimension, not the primary. No hold touches any of them; `validate_feed_repair` group I checks that.

**The market-state object is not changed.** `regime.py` is hash-pinned (`METHOD_SOURCE_SHA`), and changing what the object says needs a method bump and a re-backfill. The hold is applied where the term-structure leg is printed (`weekly_payload`, `monthly_macro/payload`, through `refusals.held_leg`), and the stored object is read as it is.

**The consequence: the dual run's count.** Until the champion's own staleness allowance passes, the object can still compute a champion state from the last settlements, so `legs_agree` may be recorded for a few sessions after the hold. After that the champion is absent and every session counts "not comparable". The dual run ends 23 Dec 2026, so Doctrine #2 should rule on it with the substitutes.

## Lifting the hold, if Doctrine #2 rules to keep the readers

The one-line change per reader in `source_registry.yaml`:

```
cboe_indices:   status: held   ->   status: live
cboe:           status: held   ->   status: active
```

That alone resumes the pulls and every block, because `key_hold` needs the source held. Tidying the store check also means deleting the ten `member_overrides` lines under "HELD (D45 …)" in `metrics_registry.yaml`. Until they go, the keys are listed as declared rather than checked for staleness. `validate_st_r4_t1b` group G's status check and groups H and I would flip with the status, and are edited at the same time.

## Left for Doctrine #2 (from D45, with what the code shows)

1. **Retention** of the stored rows: nothing was purged. `altdata/purge_synthetic.py`'s maintenance path is the pattern if a purge is ruled.
2. **The substitutes.**
   - VIX3M/VIX is already the published leg, from Yahoo, not FRED.
   - The VX1-VIX basis becomes a listed gap.
   - The dispersion panel's own configured fallback is Yahoo's `^DSPX` (from May 2024) and `^COR1M`/`^COR3M` (quotes without history), and the panel does **not** use it while held. Whether Yahoo's copy of a Cboe index is an acceptable substitute is the sitting's question, not this branch's.
3. **The dispersion story's regrading.** It reads "input held" until ruled.
4. **Whether to ask Cboe for a licence.**
5. **The dual run** (item above): end it early, or extend it once the curve has a source.

## Gates (local, one at a time, foreground)

| Gate | Result |
|---|---|
| validate_st_r4_t1b (the reader and the panel; group H new, 10 checks) | 71 passed, 0 failed |
| validate_feed_repair (group I new, 9 checks: the logger, the store check, the registry, the legs, the dial untouched) | 59 passed, 0 failed |
| validate_official_sources | 340 passed, 0 failed |
| check_registry | OK |
| validate_regime | 407 passed, 0 failed |
| validate_vol_event | 50 passed, 0 failed |
| validate_feeds_scheduled | 19 passed, 0 failed |
| validate_narratives | 103 passed, 0 failed |
| validate_b51_registry_html | 25 passed, 0 failed |
| validate_audit_3a | 88 passed, 0 failed |
| validate_weekly | 101 passed, 0 failed, 1 skipped |
| validate_weekly_complete | 96 passed, 0 failed |
| validate_weekly_analytics | 35 passed, 0 failed |
| validate_monthly | 360 passed, 0 failed, 1 skipped |
| validate_monthly_stack | 267 passed, 0 failed |
| validate_stack_cadence | 99 passed, 0 failed |
| validate_lenses | 49 passed, 0 failed |
| validate_weekly_store, validate_monthly_store | data gates: no store on the laptop, so no tally |

No gate was added: both new groups extend existing gates, so the gate count is unchanged.

## The CI run

Read once after the push; see the report.
