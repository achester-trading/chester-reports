# Dealer scorecard — pre-registration H6, level clusters (Batch 11 item 55, October 2026)

*Written and committed on 19 Oct 2026, before the first scored session and before any of its scoring code, by session A on branch `a48-batch11`. **Never edited.** A change is a new registration in a new dated file; this one stays as written. The spec is signal-triage Batch 11 (`docs/change-order-signal-triage-batch-11-2026-10-19.md`), item 55 and decision D3, ruled 19 Oct 2026, 13:05 ET. It follows the form of the scorecard's first registration (`docs/ledgers/dealer-scorecard-preregistration-2026-10.md`, 17 Oct 2026), which it does not change.*

## What this registers

**One hypothesis, H6, as two tests:** the outcome in the session (H6s) and over five sessions (H6f). Each states:
- its mechanism, its eligibility and its outcome;
- the window in which the outcome is read;
- its base rate and its price-action baseline;
- the formation and test split, and the promotion rule.

**The source.** Every level is our own, read from the store and the computed profiles as of the morning the zone is found. **Vendor levels never count** (D3), and the detector reads no vendor key. The code is `altdata/level_clusters.py`; its thresholds are mirrored in `config/reporting_stack.yaml` under `level_clusters`, and `tools/validate_dealer_block.py` holds this file to its SHA-256.

**The instruments:** SPY, QQQ and IWM, each scored on its own levels. SPX joins after the IV solver's gate admits its chain, as a new registration. Zones are shown in SPY, SPX and ES terms. The SPX and ES figures are conversions for reading only, never scored.

## The definitions

**The four families of levels**, all as of the morning the zone is found:
1. **Positioning:** the prior session's settled 16:10 capture's gamma flip, OTM call wall, OTM put gamma wall, peak-gamma strike and max pain.
2. **Implied bands:** the ±1σ edges around the prior close, one-session and five-session. Each σ is the prior close × the instrument's 30-day ATM IV × √(h/252). The ATM IV is SPY's own 30-day IV for SPY, and each name's 30-day IV where it is stored for QQQ and IWM; otherwise the family has no members that morning.
3. **Volume profile:** VP-1's POC, VAH and VAL of the prior session and of the 20-session window, and the 20-session window's high-volume nodes, as `altdata/volume_profile.py` computes them.
4. **The prior session:** its high, low and close, and the overnight high and low. The overnight high and low are ES's, converted to the instrument at the 23-hour chart's session basis (item 45 and ruling 4 of 19 Oct). They count for SPY only.

**A cluster** is a set of levels from **three or more families** whose highest and lowest lie within **0.2%** of each other (highest ÷ lowest − 1 ≤ 0.002). Its **zone** is the interval from its lowest level to its highest. Two levels of one family count once. Overlapping clusters found the same morning merge into one zone.

**Frozen 30 days.** A zone found on a morning keeps its edges for **30 calendar days** and is scored on every session in them. A zone found later that overlaps a zone still in force is not registered again: the earlier zone stands.

**The side.** A zone wholly above the prior close is resistance; one wholly below is support. A zone that contains the prior close is "straddling" and is not scored.

## The tests

### H6s — a cluster holds within the session

- **Mechanism:** where independent families of levels agree, hedging, profile and memory meet, and price is more likely to turn there than at any one level.
- **Eligibility:** the session **approaches** the zone: for resistance, its high comes within **0.25%** of the zone's lower edge or trades inside the zone; for support, its low comes within 0.25% of the upper edge or trades inside it. This is the approach band of H3.
- **Outcome:**
  - **held:** resistance, the session closes at or below the zone's upper edge; support, it closes at or above the lower edge;
  - **broke:** otherwise;
  - **not reached:** an ineligible session. It is recorded as None, never as False.
- **Window:** the session itself.

### H6f — a cluster holds over five sessions

- **Eligibility:** as H6s, on the first approach of a zone in force (one per zone per five-session window).
- **Outcome:** **held** if no close in the five sessions from the approach is beyond the zone's far edge (above the upper edge for resistance, below the lower edge for support); **broke** otherwise. It is unresolved until the five sessions are stored.
- **Window:** the approach session and the four after it.

### For both tests

- **Base rate:** the same eligibility and outcome scored against **any single level** of the four families that is not part of a cluster, a zone of one level, on every session it is approached.
- **Baseline (price action, no dealer content):** the same test against **round-number levels**, the nearest grid level above and below the prior close: $5 for SPY and QQQ, $2.50 for IWM.

## How rates are printed

- **As H1 to H5's:** k/n with a Wilson 95% interval, the base rate and the baseline beside it with their n, sessions and episodes both counted.
- **The floors:** no count prints below 20 scored sessions; no rate is a decision below 120 eligible sessions.
- **The test sample** is the sessions from this registration's date, 19 Oct 2026. Earlier sessions, and rows rebuilt by the scorecard's backfill, are printed beside it as "before registration, descriptive" (Batch 11 item 54).

## Formation, test and promotion

- **The split, per test:** the first **120** eligible sessions form, and the next **120** test.
- **Promotion:** H1 to H5's rule. The test window's Wilson interval excludes both the base rate and the baseline, after a **Benjamini–Hochberg** control at **q = 0.10** across the registered family (now eight tests: H1, H2, H3a, H3b, H4, H5, H6s and H6f), with the formation estimate on the same side of the base rate as the test estimate.
- **Demotion:** when a rolling 120-session interval includes the base rate for two consecutive months.
- Nothing in this registration grants a reading before promotion.

## What this registration does not do

- It writes no register row, no order and no alert.
- It reads no vendor level.
- It prints, before promotion:
  - at most two zones in the 07:00 anchor, one line each, with the families named;
  - one outcome line in the 16:45 close;
  - H6's running rates beside the others in the Weekly.
- The Weekly's vendor line may say whether the vendor's flip and walls fall inside each of the week's zones. That note is never counted (item 55, D3).
