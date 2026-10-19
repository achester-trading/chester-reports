# Change Order — Signal Triage Batch 11: the opening setup and the dealer scorecard, amended (items 53–58)

| | |
|---|---|
| File | `docs/change-order-signal-triage-batch-11-2026-10-19.md` |
| Status | **RULED 19 Oct 2026, 13:05 ET.** Ari: "Accept all" (decisions D1–D7, section 3). |
| Encoding | Batch 11 of Amendment #4. Items 53–58 keep their numbers as IDs. They amend the opening setup (OS-2 to OS-11: decision D-3 of 18 Oct 2026, built on `a44-opening-setup` and `a45-opening-setup-2`) and the 6b dealer scorecard (pre-registered 17 Oct 2026, `docs/ledgers/dealer-scorecard-preregistration-2026-10.md`). One new item, the level clusters, enters as the scorecard's next registration (H6). |
| Source | A third-party premarket report of 19 Oct 2026 (SpotGamma's Opening Setup), read in a separate chat. This edition was reviewed against chain-2 on 19 Oct 2026. Under D2 it carries no figure from that report and no vendor figure. |
| Estimate | About 20 hours of sessions on session A's line (paste A48), plus about 4 if D4's backfill proves feasible. By hand: the flat-files key in `.env` if D4 proceeds, and a review of the first two weeks of cluster output with Ari. |
| Binding on | Claude Code sessions building on the third chain. |

---

## 0. What was already built

The draft asked for this check first. Most of the draft restates elements that the 18 Oct replication map (OS-1 to OS-12) ruled on and chain-2 already carries. Chain-2 merges on 20 Oct.

| Item | Already built or ruled (where) | Verdict |
|---|---|---|
| 53, two-week positioning gauge | OS-3: three daily vol lines (VIX less RV20, the term structure, VIX9D/VIX) from item 52's lenses. OS-4 and OS-5: the put-volume proxies, labelled "no side". OS-6: the 0–100 score rejected on 18 Oct (D-4), with DIP WATCH logged as a ledger candidate. The market-state object's vol dial is the one volatility regime (`docs/market-state.md`). | **Amend:** OS-6's ledger is built now, and the VIX premium is split into ATM and wings. The [−1,+1] VIX index is dropped. |
| 54, gamma index and conditional move table | OS-2: the expected-movement gauge (the engine's regime word, the ±1σ one-session band, the typical 5-session range by regime, "awaiting (n=k of 20)"). Scorecard H1 and H2: realised against implied by gamma sign. The words CALM / NORMAL / WILD are excluded by design (`daily_cascade/opening_setup.py`). Massive sells no open-interest history at any tier (found 12 Oct 2026). | **Amend:** the comparison becomes like-for-like, net GEX gets its own-history percentile, and the scorecard is backfilled. The index, the three words and the OI probe are dropped. |
| 55, sigma bands and level clusters | OS-2's one-session band around the last close. Ruling 4 of 19 Oct: the pre-market line from ES. Item 45: levels in ES terms. Scorecard H3 to H5: single walls, the pin and the flip. | **Amend** the bands. **Keep** the clusters as new registration H6. |
| 56, setup profiles | OS-8: four extremes, each ranked against the name's own history. OS-10: IV rank and IV percentile. The five per-name keys of a45. The 60-day `backfill-names`. | **Amend:** 30-day constant-maturity IV, the risk reversal, RV60 and a per-name table. The strategy labels are dropped. |
| 57, earnings cards | OS-11: the last three reactions and the elevated / in line / muted word, on a 20% band. The lab's engine 4 earnings base rates (alpha-lab-3). | **Amend:** up to eight reactions, the event-only implied move, one shared record per print, and the MSTR link. The behaviour tags are dropped. |
| 58, large new positions | OS-9: "Largest OI builds, side unknown". Eight rows, spreads with "legs equal", the mid premium (ruling 2 of 19 Oct), Black-Scholes chance in the money, and context tags. | **Amend:** a size floor, the OI-to-volume column, an outcome ledger and the December comparison. VWAP is dropped. |

---

## 1. Standing constraints

- **Universe.** The 17 captured names: the options universe (SPY, QQQ, IWM, AAPL, AMZN, GOOGL, META, MSFT, NVDA, TSLA, COIN, MSTR, ASTS) plus the paper bid's four. SPX is added wherever its chain is in and the solver gate admits it. No widening in this batch (ruled 19 Oct 2026); the universe is reviewed on 1 Dec 2026.
- **Data spend** is unchanged: Massive Options Starter and FlashAlpha Basic.
- **No manual data drops** (rule 30). The standing rule of 16 Oct 2026 on sources applies.
- **The sign convention.** dealers-hand-v1 is a convention, not observed positioning. Every printed read that depends on it says so once per section.
- **The one-regime rule.** Nothing outside the market-state object computes a regime. Regime words come only from the engine.
- **No vendor value** in any flag, tell, dial, decision or engine. The opening-setup modules never read the vendor, and a gate greps them for it. Vendor values appear only in the Weekly's vendor line and the divergence gate.
- **Report-only.** No composite and no weights until a passing ledger and Ari's ruling. Every rank prints its window and n.
- **Placement** is inside the existing anchors (07:00, 16:45, the Sunday Weekly, the Monthly). Every addition says what it displaces.

---

## 2. The items, as ruled

### Item 53: the positioning components, tested rather than weighted

1. **OS-6's ledger, built now** (DIP WATCH, generalised). This is a pre-registered calibration study under `tools/calibration/`.
   - **Inputs:** the OS-3 lenses (VIX less RV20 with its percentiles, VIX9D/VIX, VIX3M/VIX and VIX6M/VIX), VVIX, SKEW, and OS-4's put-volume share.
   - **Outcomes:** forward 5- and 10-session SPX returns, maximum drawdown and realised volatility.
   - **First edition:** from public sources for the VIX family (2007 on), labelled "laptop run, public sources". The put-volume component joins in the box edition, once its history allows (or from D4's backfill).
   - **Rules:** the pass rule is pre-registered in the first edition, and its rights are stated while granting nothing. No composite number prints before a passing ledger and Ari's ruling.
2. **The VIX premium, split.** OS-3's realised lens gains one line: VIX less RV20 = (SPY 30-day ATM IV less RV20) + (VIX less SPY 30-day ATM IV). The first part is the at-the-money premium and the second is the wings. The line is labelled "SPY's ATM IV as SPX's proxy", and it displaces nothing.
3. **Dropped:** the [−1,+1] VIX regime sub-index, which would be a second volatility regime.

### Item 54: the gauge compares like with like, and the scorecard gets its history

1. **Like for like.** OS-2 prints the implied move and the realised distribution on the same horizon and the same measure:
   - the implied one- and five-session moves: the close × the 30-day ATM IV × √(1/252) and × √(5/252);
   - beside each, the realised distribution of the absolute close-to-close move at that horizon, in the gated regime: the median, 80th and 95th percentiles, with n.

   The existing high-low range stays only if it is set against the implied expected range, and the line says which measure it uses.
2. **Net GEX's own-history percentile,** with its window and n, beside the regime word.
3. **The scorecard backfill.**
   - `dealer.scorecard_day` rows are rebuilt from the 16:10 captures on disk, back to the first, point in time. Each morning profile comes from the prior session's capture.
   - Every row is labelled backfilled.
   - The H1 to H5 rates print the test sample (sessions from 17 Oct 2026, the registration date) with the backfilled sample beside it, labelled "before registration, descriptive". The registration file is not edited.
   - OS-2's typical range reads both samples, with their counts.
4. **Dropped:** the normalised [−1,+1] index and CALM / NORMAL / WILD, both ruled out on 18 Oct. Also dropped: the open-interest probe (D4).

### Item 55: bands, and the clusters as H6

1. **Bands.** The gauge gains the five-session ±1σ band. Beside the pre-market line (ruling 4 of 19 Oct), both bands are also centred on the pre-market price. Each band is labelled by its horizon and its centre.
2. **H6, level clusters.** A new dated pre-registration, `docs/ledgers/dealer-scorecard-preregistration-2026-10-h6.md`, is written and committed before the first scored session and never edited.
   - **Families:**
     - positioning: the flip, the OTM call wall, the OTM put gamma wall, the peak-gamma strike and max pain;
     - implied bands: the ±1σ edges, one- and five-session;
     - volume profile: VP-1's POC, VAH, VAL and HVNs;
     - the prior session: its high, low and close, and the overnight high and low through item 45's conversion.
   - **A cluster** is levels from three or more families within 0.2% of each other (D3), frozen for 30 days.
   - **Eligibility and outcome:** a session approaches a cluster; the outcome is held, broke or not reached, in the session and over five sessions.
   - **Base rate and baseline:** the base rate is any single level approached. The baseline is the same test on round-number levels.
   - **Promotion** follows H1 to H5's rule.
   - **Instruments:** SPY, QQQ and IWM (SPX after the solver gate), shown in SPY, SPX and ES terms.
   - **Printing:** the 07:00 anchor shows at most two zones, one line each, with the families named. The 16:45 close adds one outcome line, and the Weekly carries the running rates.
3. **The vendor annotation.** In the Weekly's vendor line only, a note says whether the vendor's flip and walls fall inside each of the week's cluster zones. It is never counted, and the anchors stay vendor-free.

### Item 56: per-name volatility state

1. **New keys:**
   - `chain.iv30_atm`: 30-day constant-maturity ATM IV per name, by SPY's method (total variance between the two expiries bracketing 30 days, else "nearest");
   - `chain.rr_25d`: 25-delta put IV less 25-delta call IV;
   - 20- and 60-session realised volatility per name.

   `backfill-names` writes them from the stored chains.
2. **A per-name table** (17 rows) goes in the Weekly's technical appendix. It shows the 30-day IV with its IV rank and IV percentile, the 25-delta put skew and the risk reversal with their percentiles, IV less RV20, and RV20 and RV60, each with window and n. OS-8's four rows stay in Mechanics, now on the 30-day IV. Descriptive words only.
3. **Dropped:** profile labels that name a strategy, SpotGamma's thresholds, and a daily table at 16:45.

### Item 57: earnings, a larger sample and an event-only move

1. **The sample.** OS-11 uses up to eight reactions (in config), with n printed. The pricing word is computed on the median of those available: n ≥ 3, otherwise "n=k, no word". The band is unchanged (D5).
2. **The event-only implied move** applies where an expiry before the report exists. It is the post-event expiry's total variance, less the pre-event expiry's variance rate over the same time, on the straddle convention, and it is labelled. Otherwise the full straddle prints, labelled "includes non-event days".
3. **One stored record per print:** the implied move at the close before the report and the realised move after it, with the key named under AUD-3a. The close after the report writes it once. The Ahead rows read it, and it is offered to the lab's engine 4 (session B's line).
4. **The MSTR row** names the stored MSCI index events (item 49).
5. **Dropped:** the four behaviour tags.

### Item 58: the OI builds, filtered and scored

1. **A size floor** (D6): 2,000 contracts for SPY, QQQ and IWM, and 500 for single names. Provisional and session-set.
2. **A column:** the OI change as a percentage of the day's volume.
3. **An outcome ledger,** pre-registered and report-only. Each printed build's chance in the money is set against whether the contract finished in the money at expiry. A calibration table by decile is printed once 30 builds have resolved.
4. **The December comparison,** pre-registered with the vendor month's ledgers. During the SpotGamma month, OS-9's eight rows are compared with SpotGamma's large-activity table for the same names and days: the overlap of contracts, and how often a known side would have changed the read.
5. **The premium is unchanged:** the mid at the later capture (ruling 2 of 19 Oct). **Dropped:** VWAP pricing, because the 17 names' chains come from Yahoo, which serves none.

---

## 3. Decisions, as ruled 19 Oct 2026, 13:05 ET

- **D1, encoding:** Batch 11 of Amendment #4, filed as amendments to the opening setup and the dealer scorecard. Items 53–58 keep their numbers as IDs.
- **D2, SpotGamma:** its reports are read ad hoc in chat until December, and nothing from them enters the store, a report or the repository. In December the vendor-month capture ruled on 18 Oct governs: SpotGamma's values are stored for the comparison ledgers only. Committed ledger editions print agreement statistics, never SpotGamma's levels, and nothing of theirs prints in a report. No vendor figure, SpotGamma's or FlashAlpha's, appears in this file.
- **D3, clusters:** three or more families within 0.2%, frozen for 30 days. Vendor levels never count.
- **D4, history:**
  - There is no gamma backfill, because no open-interest history is available from anything we pay for.
  - Instead, one probe: whether Massive Starter's flat files carry two years of per-contract daily bars.
  - If they do, a resumable backfill writes, for the 17 names, puts' share of volume, and IV, skew and risk reversal from the day bars' closes. The closes are labelled "from last-trade closes, not mids", under a distinct source.
  - A rank uses that history only where its overlap with the captured history agrees within a pre-registered tolerance.
  - The flat-files key is Ari's, in `.env`, by name.
  - The December FlashAlpha choice between Growth and Alpha stays for November, and gamma history is the only reason left for Alpha.
- **D5, thresholds:** the session-set thresholds already built stay (OS-9's deciles, OS-11's 20% band). They are reviewed at the 25 Oct dry run and then by the ledgers. SpotGamma's numbers are not imported.
- **D6, OS-9's floor:** 2,000 contracts for SPY, QQQ and IWM, and 500 for single names, provisional. The OI-to-volume share is printed as a column instead of a 70% filter.
- **D7, the chat-side FlashAlpha tasks:** retired at chain-2's merge, not on 29 Oct.
  - Their only runs, 14 and 15 Oct, failed on the usage limit.
  - Once the backup is encrypted, they cannot read the box's files from Drive.
  - From the merge, the box's 16:25 vendor writer and its divergence gate are the check.
  - The chat retires both tasks on the morning after the merge.

---

## 4. Work order

| Part | Items | Hours |
|---|---|---|
| 0 | This file committed; D7 recorded in the box sheet's E6 and F-4's note | 0.5 |
| 1 | 54 (like for like, percentile, scorecard backfill) and 55's bands | 4 |
| 2 | 55's H6: registration first, then the detector, the lines, the ledger and the vendor annotation | 4 |
| 3 | 53: OS-6's ledger (first edition) and the VIX premium split | 4 |
| 4 | 56, 57 and 58 | 6 |
| 5 | D4's probe, and the backfill if feasible | 1 (+4) |

The work runs on session A's line (it owns the opening setup and the dealer engine), on a branch from `a47-chain3`. It merges in the third chain.

---

## Appendix A — the 19 Oct read that prompted the batch (dated; our own figures only)

On 19 Oct 2026 the box's 16 Oct settle placed SPY in short gamma (net-to-gross −0.30). Its flip and its weekly call wall sat within 0.1% of each other (7,774 and 7,778 in SPX terms, at Friday's SPX/SPY ratio of 10.036). SPX stalled near 7,708 beneath them, while its monthly put wall sat at 7,527 (SPY 750). The draft's other reads relied on vendor figures and are not reproduced here (D2).

The method question the read raised is the one item 54 settles. A one-session ±1σ band and a five-session high-low range are different measures on different horizons, so "realised over implied" is read only when both sides use the same measure and the same horizon.
