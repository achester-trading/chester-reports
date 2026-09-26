# Change Order — Signal Triage, Consolidated (Batches 1–2, SR-1…SR-27)

**One register, one regime, one sequence**

| | |
|---|---|
| Status | **SIGNED 2026-09-26 (§13)** — all tranches approved; sequence and placements recorded in §13 |
| Date | 2026-09-25 (evening); **revision 2, 2026-09-26** — the 19 Sep Digital Asset Mechanism Watch order integrated as Thread D and register entry SR-10 |
| Proposed by | Ari Chester |
| Contents | Twenty-eight signal-triage entries (SR-1…SR-9 from Batch 1, 10–19 Sep; SR-10 the Mechanism Watch — Pearl (PRL) and the emerging-mechanism scan, 19 Sep; SR-12…SR-27 from Batch 2, 24–25 Sep; SR-11 reserved for the consensus-drift order of 19 Sep, carried in Appendix C), re-reviewed for coordination with each other and with the repository as it stands on 25–26 Sep 2026, and integrated into one governance section, six threads, one rights ledger, one data-feed table, one sequenced work order |
| Encoding | Post-Freeze Amendment #4 — Signal Triage and Mechanism Watch (single amendment). Encodes as the next free architecture Part; the Mechanism Watch adds no Part of its own (its 19 Sep draft's provisional "#5" label is retired). Amendment number to be confirmed at sign-off (G-1). |
| Precedence | Below Part 26 (Final Architecture Change Order), Part 28 (automation addendum), Part 30 (Track D and its standing rules 30.2–30.4) and the current change-orders edition. Consistent with Amendments #1–#3. **Binds to the repository's one-regime rule** (`docs/market-state.md`: "Nothing else in the system computes a regime") and to 30.4 (reports never fetch). |
| Supersedes | `post-freeze-amendment-4-signal-triage-batch-1.md` (19 Sep standalone, ≈71 h), Parts A and B of the 19 Sep batch draft (`change-orders-2026-09-19-batch.md`), `change-order-mechanism-watch-2026-09-19.md` (Draft 1, ≈35 h — integrated here as Thread D), and `change-order-signal-triage-batch-2-2026-09-25.md` (v3, ≈30 h). Part C of the 19 Sep batch (consensus drift) is **not** superseded — it stays in the deferred backlog by reference (Appendix C). |
| Filing state | **None of the three superseded drafts is in `docs/` on the laptop working copy** (listing taken 25 Sep 21:56 ET), nor is `docs/signal-triage-register.md`, `docs/templates/signal-intake.md` or `docs/prediction-market-spec-v1.1.md`. If any was committed from another machine, pull before filing this (CLAUDE.md upload discipline). Otherwise this order is the first filing of the signal-triage programme and ST-0 creates the register. |
| Binding on | Claude Code sessions executing §8 after §13 is signed |

---

## §0 Summary and coordination review

**Are Batches 1 and 2 coordinated?** Partly. Batch 2 was written to sit on Batch 1's work items and cites its rulings correctly (SR-1's break for SR-13, SR-4's tell as SR-14's exit, SR-6's block for SR-17, SR-7's table for SR-21's rows). But it cites a Batch 1 document that was never filed, and on re-review the two batches overlap in six places, collide in one, and neither is coordinated with the repository built since 19 Sep. Twelve findings, each with its fix:

| # | Finding | Fix | Where |
|---|---|---|---|
| 1 | Batch 2 depends on A-W1…A-W12 and Tranches 1–4 of the 19 Sep batch; the Batch 1 file supplied for this review is the earlier standalone (W1–W12, ≈71 h). None of the three is in the repo. | This order carries the tranching decisions itself; one ID scheme (ST-n) replaces W, A-W and W- IDs | §8, Appendix A |
| 2 | **Two regime tags for one thing**: SR-6 defines a two-state tag (path-driven-real vs. term-premium/supply); Batch 2 §3.4 defines a four-cell tag (growth / Fed path / term premium / mixed). Both would be a second regime, which `docs/market-state.md` forbids. | One object field, `rates.driver`, declared in `config/market_state.yaml`, computed by the close pass, read by every report. SR-6's two states map onto two of the four cells. | §2.1 |
| 3 | **Two stock-bond correlation readings** (SR-9's SB_corr_60 flag; §3.4's correlation column). | One `calc.corr_spy_tlt_60d` feature in `altdata/market_features.py`, one member of `rates.driver` | §2.1, §5 |
| 4 | **TIC built twice** (SR-3's China Treasury-holdings row; SR-20/26/27's holder, composition and official/private series). | One `tic.*` source family in `altdata/sources/tic.py`, both vintages, serving SR-3, SR-20, SR-26, SR-27 and the block's absorber side | §2.2, ST-2 |
| 5 | **Three candidates for the same T&B overlay** (Liquidity & Funding Stress: SR-2 yen unwind, SR-22 auction stress, SR-26/27 absorber fragility) with no ordering rule — and T&B is not yet built in this repo (Track D: "T&B full" comes after the D-steps and the intraday cadence). | Overlay intake queue with one-at-a-time champion/challenger; all T&B-facing work is offline calibration until T&B full, then one wiring session (ST-11) | §2.6, ST-9, ST-11 |
| 6 | **Warsh matrix edited in five places** (SR-6, 9, 17, 21, 24). | One by-hand edit list | §2.1, Tranche 4 |
| 7 | **Book A's rules split across three items** in three papers (SR-8 re-entry gate; SR-9 hedge substitution; Batch 2's 3.5 duration trigger). | One Book A rule table, owned by Portfolio Construction | §2.4 |
| 8 | **"Already held" lists were wrong in both batches.** The 59 FRED series in `altdata/config.py` hold T10YIE, T5YIFR, DGS2/10/30, WTI, Brent, VIX, IG/HY/BB/CCC OAS, DTWEXBGS, USDJPY, USDCNY, WALCL, RRP, TGA, NFCI — but **not** DFII10, DGS5, DTB3, FEDFUNDS, USREC, THREEFYTP10, TREAST, TOTALSL, AA/BBB OAS, nominal GDP. SR-6's real/breakeven cut needs DFII10 added. | Corrected feed table with a held/new column | §4 |
| 9 | **Every new feed is a new store writer.** Track D's D1c (SQLite WAL + busy_timeout + repo-wide write lock, "before any new writer ships") is a hard precondition neither batch named. And 30.4 (reports never fetch) means Batch 2's "by-hand file loaders" (AAII, MSCI, IEA, NIC, CBO) must be `manual_input` store writers with `available_at`, not report-side reads. | D1c listed as the precondition of ST-1/ST-2; a `manual_input` source class with a registry entry per series | §1.10, §8 |
| 10 | **Backtests vs. the store.** The migrated FRED history carries one `available_at` (30 May 2026) until ALFRED ingestion (O.16), so no as-of-correct replay reaches behind it. Every validation gate in both batches needs decades. | Gates run as offline calibration studies under `tools/calibration/`, pulling full history (and ALFRED vintages) directly, writing dated ledgers; only live flags read the store as-of | §1.10, ST-7/ST-8/ST-9 |
| 11 | **Daily and Sunday surfaces.** Both batches put flags in the 07:00 anchor, the 12:30 alert and the Sunday anchor. The anchors exist (both open on the WHAT CHANGED block) but D3 (numeral audit) and D4 (block payload builders) are open in Track D, D6 is the Sunday plan. | Daily/Sunday rendering is one session (ST-10) placed after D4/D6; Monthly rendering (built report) goes first | §7, ST-6, ST-10 |
| 12 | **Hours.** Standalone Batch 1 ≈71 h + Batch 2 ≈30 h = 101 h; as separately tranched ≈34 + 30 = 64 h. Integrated (Tranches 1–4 + L): **≈78 h of sessions + ≈5 h by hand**, of which the core (Tranche 1) is ≈33 h. Higher than 64 because the deferred Batch 1 panels keep their *feeds* (a fetcher is the reusable asset; rendering is what was deferred) and because Daily/T&B wiring is now its own later slot rather than folded in. Revision 2 adds the Mechanism Watch as Tranche 5: ≈30 h in its 19 Sep draft, ≈25.5 h here plus ≈4.5 h absorbed into ST-10, ST-12 and ST-L, for an order total of **≈108 h + ≈5.5 h by hand**. | Cut by tranche, not by item | §8 |

**What the integration produces.** Six threads (§2), each owned by one paper: **R** rates driver and duration absorption (SR-6, 9, 17, 21, 22, 23, 24); **X** external position and funding currencies (SR-2, 3, 4, 14, 20, 26, 27); **E** equity regime and cycle position (SR-1, 5, 7, 8, 13, 16, 19, 25); **A** Book A rules (SR-12, 15, plus SR-8's gate and SR-9's hedge rule); **C** the oil buffer (SR-18); **D** the digital asset mechanism watch (SR-10). The programme adds no report, no composite input, no paid feed and no decision rights; everything is REPORT_OK-class.

**Revision 2 — the Mechanism Watch, read against the repo.** The 19 Sep order is adopted in full (rulings MW-1…MW-10, signposts S1–S8, derived metrics D1–D6, both block layouts, the MW-7 exit criteria) with five coordination changes: (a) its emerging-mechanism scan does not get its own query runner — the query set is declared in `config/story_queries.yaml` (committed 25 Sep: "declared here, never composed at render") and run through `altdata/sources/news.py`, with CoinGecko recently-added and the hashrate trackers as the two non-RSS legs; (b) the CoinGecko source switch already exists in `altdata/config.py` (`ENABLED_SOURCES`, off) and is turned on rather than written; (c) the Security Master of Part 26 is, in this repo, the instrument table in `register/instruments.py` — the `crypto.watch` class goes there (G-24); (d) the Sunday block waits for D6 like every other Sunday surface, so the Monthly part renders first; (e) the two new fetchers are new writers and wait for D1c. Its LLM assessment step uses the existing gate plumbing (called only when a gate opens) and its narrative entries post to the existing graded narrative register. The interim Saturday scan (first run 26 Sep 2026) continues until MW-9 retires it.

| Tranche | Scope | Preconditions | Hours |
|---|---|---|---|
| 1 — Core: register, feeds, the rates driver, the Monthly blocks | ST-0, ST-1, ST-2, ST-3, ST-4, ST-6 | D1c before ST-1 | ≈33 |
| 2 — Book behaviour: funding-currency tells, false-bottom audit, rate-thread calibrations | ST-5, ST-9, ST-7 | Tranche 1 | ≈22 |
| 3 — Backtest before any panel: style, consumer credit, EM, yen/RMB thresholds | ST-8 | ST-1/ST-2 | ≈8 |
| 4 — Wiring at Track D milestones: Daily/Sunday lines (incl. the Mechanism Watch block), T&B, validate/redeploy, MW-9 parallel run | ST-10, ST-11, ST-12 | D4/D6; T&B full | ≈14 |
| 5 — Mechanism Watch: Security Master entry, PRL feeds and D1–D6, Monthly part and validators, emerging scan and LLM gate | ST-13, ST-14, ST-15 | D1c; independent of Tranches 1–3 | ≈25.5 |
| L — One library session, `library` worktree | ST-L | any time | ≈6.5 |
| By hand | Tranche H | any time | ≈5.5 once + recurring |
| Deferred backlog | Appendix C | — | (≈35, unscheduled) |

Total ≈108 h of sessions + ≈5.5 h by hand. Tranche 5 shares nothing with Tranches 1–3 but D1c and the register; it can run beside them or after, chosen at sign-off (§13).

---

## §1 Governance

**1.1 Signal Intake Template — six canonical fields.** Home (report(s); book A allocation / B swing / C tactical / D no fixed horizon; paper) · Mechanism (the edge or read; source and evidence; which existing pillar, overlay, dimension or input already covers it) · Data (source, cost, cadence, `available_at`, first-print availability; **where it lives** — source module and registry key) · Signal rights requested (narrow flag / composite input / confidence modifier / base rate only / none) · Validation (episodes, statistic, pass condition; falsifier; review date) · Disposition (adopt / defer / reject, with reason). File: `docs/templates/signal-intake.md`.

**1.2 Signal Triage Register.** `docs/signal-triage-register.md`, numbered, one record per proposal. Seeded by ST-0 with SR-1…SR-27; SR-10 is the Mechanism Watch (Thread D) — emerging-mechanism candidates live in the `mechanism_watch` store table and are referenced from SR-10, never duplicated into this register; SR-11 (consensus drift) is a reserved entry pointing at the 19 Sep batch's Part C in the backlog. The register is also the record of what was rejected and why (§12).

*Status vocabulary (ruled 26 Sep, after ST-0).* Every entry carries exactly one status, upper case, in the form `STATUS — qualifier`:

| Status | Meaning |
|---|---|
| `ADOPTED — pending build` | Ruled; nothing built yet |
| `ADOPTED — gate pending` | Built; its calibration study has not yet run or reported |
| `ADOPTED — rights live` | Gate passed; the flag or modifier carries the rights §6 grants it |
| `DEFERRED — gate failed` | Built and tested; did not pass; kept as a note, no rights (§9) |
| `DEFERRED — definition required` | Entered without its construction (§1.6); SR-19 |
| `MERGED — into ‹item›` | Absorbed into another entry's build; SR-17 into `rates.driver` |
| `REJECTED — as signal; ‹what was kept›` | The post is rejected; a named tell or note survives; SR-25 |
| `RESERVED` | Placeholder for an order carried elsewhere; SR-11 |

A session that writes to the register uses these strings and no others; the first session after ST-0 to touch the register normalises the labels ST-0 generated to this table.

**1.3 Third-party rule.** A chart's or post's own conclusion is recorded but never inherits rights. Rights come only from the mechanized version passing its gate.

**1.4 Point-in-time rule.** Every new feed carries `available_at`. Revised macro series are stored as first-print vintages where ALFRED offers them (G.19 consumer credit first); a signal that survives only on revised data is logged and gets no rights. Surveys, reports and papers are keyed on publication date, never fieldwork date. Manual inputs carry the date the operator entered them.

**1.5 Projection rule.** A third-party chart carrying a projected, estimated or scenario segment is entered with the date its actual data ends, the projection's stated assumption, and the label `PROJECTION (data to <date>; assumes <…>)`. A projection never becomes a print and never inherits the post's language. Fixture: SR-18.

**1.6 Definition rule.** No chart enters the register without its construction (numerator, denominator, window, source). A crop without one is `DEFERRED — definition required`. Fixture: SR-19.

**1.7 Rights boundary.** Everything in this order is REPORT_OK-class. No item can raise DECISION_BLOCKED, produce a Decision Packet, enter the Monthly composite or the Top & Bottom composite, or change a Disruptive Themes factor, scenario or theme text. Disruptive Themes stays permanently human-gated. Promotion beyond the ceilings in §6 goes through champion/challenger after the stated gate passes, one candidate per overlay at a time (§2.6).

**1.8 Named blocks.** A block is a Monthly section assembling several register items into one read, owned by one paper. This order creates two: **Duration Absorption** (owner: The Rate and Liquidity Machine; §2.1) and **Cheap-and-Unloved** (owner: Portfolio Construction when written, Base Rates meanwhile; §2.4). A block has no rights of its own.

**1.9 Reserve-composition scorecard.** Under Factor V: annual by hand at the Disruptive Themes refresh (COFER USD share at constant exchange rates; gold share of total reserves at market; holder-level split with mechanism tags), monthly automated proxies from the `tic.*` family and WGC, an event watch for regime steps. Gives Factor V a scoreable input; no rights; no scheduled task.

**1.10 Repository bindings (new; these are what make the two batches one programme).**

- *One regime.* No item computes or renders a regime, cell, tag or state of its own. Regime-like reads become declared members, sub-states or contradiction rows of the market-state object in `config/market_state.yaml`, computed by the 16:45 close pass in `regime.py`, read through `regime.latest()`. The rates driver (§2.1) is the first such sub-state; `tools/validate_regime.py` gates it.
- *One place for derived forms.* Deltas, percentiles and z-scores come from `altdata/derived.py` (`derived_forms`) with the registry's `units` deciding delta semantics. Every `*_z` in this order is that function's output, never a formula in a report.
- *Features are `calc.*`.* Series computed from stored observations live in `altdata/market_features.py`, are registered in `metrics_registry.yaml`, and carry `available_at` = the maximum across their inputs.
- *Reports never fetch (30.4).* Every new external source is a timer-driven writer in `altdata/sources/<name>.py` with a `source_registry.yaml` entry; every operator-entered figure is a `manual_input` writer (a small CLI that stamps `available_at` and `run_id`). No block reads a file.
- *D1c first.* No new writer ships before Track D's D1c (WAL, `busy_timeout`, repo-wide write lock) lands. ST-1 and ST-2 are gated on it.
- *Identity and time (30.2a).* Every new writer passes through `session_date()`, canonical microsecond UTC, `run_id`-on-write.
- *Calibration is offline.* Validation gates run as scripts under `tools/calibration/<sr-n>_*.py` that pull full history (FRED, ALFRED vintages, yfinance, Ken French, TIC archives) directly, and write dated ledgers to `docs/ledgers/` that the Base Rates paper cites in its dated appendix. They do not read the observation store as-of, because as-of history begins 30 May 2026 until O.16. Live flags read the store; ledgers do not.
- *Registry gate.* A metric or source without a registry entry fails `make validate`; every entry from this order carries `units`, `information_half_life`, `revision_policy`, `mechanism_group` and a `because` line where polarity applies.

**1.11 Library conventions.** Papers cited by short name; numerals are accession IDs only; dated content in dated appendices policed by `make library-check`; one library session for this whole order on the `library` worktree, merged by PR.

**1.12 Interim external scans.** Two scheduled Claude tasks run outside the pipeline: the weekly Pearl scan (Saturdays ~08:00 ET, first run 26 Sep 2026; S1–S8 deltas against a carried baseline plus the new-mechanism sweep, ≤700 words) and the bimonthly consensus-drift scan (20th of even months). The Pearl scan belongs to this order and retires under MW-9 (§2.7) once the Sunday Mechanism Watch block has published clean for four consecutive weeks, on Ari's confirmation; until then the pipeline is authoritative for stored data and the external scan for narrative. The consensus-drift scan belongs to Part C in the backlog.

---

## §2 Threads — the integration layer

### 2.1 Thread R — Rates driver and duration absorption (owner: The Rate and Liquidity Machine)

**2.1.1 `rates.driver` — one sub-state, four cells.** Declared in `config/market_state.yaml` under the `rates` dimension beside its level bands (high / mid / low stay as they are). Computed over a 60-session window on every close pass; carries `state`, `pending_state`, `persistence` (default 2 sessions), `supporting[]`, `contradicting`, `since`, and a trace string naming the members that decided it.

| Cell | Decided by (members) | Confirming shape | Correlation member | Bonds as Book A hedge | Book A duration |
|---|---|---|---|---|---|
| growth | Δ real path share ≥ 60% (DKW expected real short rate; KW/ACM expected-rate legs as tie-breakers) with breakevens flat or up | mild bear steepening; cyclicals over defensives | negative | yes | neutral |
| fed_path | Δ real path share ≥ 60% with breakevens down and the front end leading (Δ2y > Δ10y) | bear flattening | positive | no | wait for pivot |
| term_premium | Δ real term premium share ≥ 60% (DKW real TP; KW/ACM TP as tie-breakers) with the front end anchored | bear steepening; auction tails; new-issue concessions | positive | no, until absorption stress peaks | trigger candidate (§2.4) |
| mixed | neither ≥ 60%, or the four models disagree on sign | — | rule of SR-9 (level prior above ~5.25% → treat positive as persistent) | per SR-9 | neutral |

Members, in order: `fred.tips_10y` (DFII10, new), `fred.breakeven_10y` (held), `fred.yield_2y`/`fred.yield_10y` (held), `dkw.real_expected_path` and `dkw.real_term_premium` (new source), `fred.term_premium_kw` (THREEFYTP10, new), `acm.term_premium_10y` (new source), `calc.corr_spy_tlt_60d` (new feature), `calc.attr_real_share_20d` / `calc.attr_curve_share_20d` (new features: the two cuts of SR-6). SR-6's "path-driven-real" is `fed_path`; its "term-premium/supply" is `term_premium`. SR-9's flag is the correlation member, not a second flag. SR-17's DKW split is the arbiter when KW and ACM disagree on sign (R5 stands: no single model is fact).

Consumers: the Monthly's Rate machine summary and Duration Absorption block; the Sunday anchor line; the Rate Repricing Velocity overlay's hawkish/dovish tag when T&B is built (G-7); the Valuation trigger's ERP input; the Book A rule table (§2.4); the Warsh matrix (2.1.5).

**2.1.2 Duration Absorption block (Monthly, ≤18 lines).** Three parts, all read from the store.

*Supply* — `calc.net_supply_12m_gdp` (Treasury net marketable issuance − SOMA Treasury change, % GDP; SR-23), of which coupons ≥10y; `sifma.ig_issuance_10y_plus` with `calc.ai_long_share` (SR-16); G4 net supply (annual `manual_input`, SR-23); projection line `calc.net_supply_proj_12m` from a CBO `manual_input` plus announced runoff (SR-23).

*Absorbers* — Fed (`fred.soma_treasuries`, TREAST, new); foreign official and private (`tic.official_holdings`, `tic.private_holdings`, 12m changes; SR-20/27); foreign composition (`calc.foreign_ust_share_lt`, bills vs. coupons; SR-26); holder type (`calc.tic_official_share`, `calc.tic_custodial_share`, top movers with by-hand mechanism tags; SR-27); Japan's line explained by `calc.jp_hedged_carry` (SR-2 metric 3 — the block reads it, never recomputes it); China's line read with the custodial caveat (G-9) from the same `tic.*` family SR-3 uses; domestic price-sensitive residual `calc.priv_residual_12m`; note line: stablecoin bill float (Factor V) absorbs bills, not duration.

*Price* — the four term-premium members of 2.1.1; auction absorption (`auction.tail_bp`, `auction.bid_to_cover`, `auction.dealer_share` for the last four coupon auctions; SR-22); corporate absorption (`manual_input` median NIC quarterly; `calc.aa_bbb_oas_diff`; SR-16).

*Read* — the `rates.driver` cell and its trace; `ABS_STRESS` (SR-22) and `ABS_FRAGILITY` (SR-26/27) as candidate flags displayed with their gate status; the Book A duration trigger's conditions met/unmet (§2.4).

**2.1.3 Fed–market gap (SR-21).** `calc.fed_mkt_gap_m1/_m2/_12m` = market-implied rate minus the Fed's signalled path (SEP median as `manual_input` quarterly; last statement bias as a by-hand field). Market leg: CME FedWatch by hand until a free source is settled (G-4), Kalshi once PM-1 lands. `CRED_STRESS` narrow flag when ≥60% of a move is priced against the last signalled direction at the next meeting or the 12m gap exceeds 50 bp. `PM_DISAGREE_fed` = Kalshi − FedWatch on the same meeting, recorded for the disagreement layer, no rights.

**2.1.4 De-anchoring flag (SR-24).** `DEANCHOR` = `fred.breakeven_5y5y` above its 2022 high for 20 sessions, confirmed by `fedboard.cie` above its 2022 high or `umich.expect_5_10y` ≥ 3.5% for three months. Definition-only rights; rendered with `calc.be5y5y_range_pos` (percentile within 2010–2026). It is the consequence gauge for the `fed_path`-cell "Fed declines the priced hike" branch.

**2.1.5 Warsh matrix — one edit, by hand.** Add: `rates.driver` as a matrix variable (SR-6/17); the reaction-function variable "defends the front end or the long end", adjudicated by the driver in real time (SR-9); the cell "market prices a hike, Fed declines" with both branches — refuse → term premium repricing, gauged by DEANCHOR; concede → bear-flatten then resolve, 1994→1995 (SR-21/24). One session of Ari's time, ≈45 min.

### 2.2 Thread X — External position and funding currencies (owner: Currencies)

**2.2.1 One TIC family.** `altdata/sources/tic.py` writes `tic.holdings_by_country` (Major Foreign Holders, monthly, plus the annual benchmark as a second vintage), `tic.official_holdings` / `tic.private_holdings`, and the cross-border flows table (`tic.flow_*`, lines 1–22). Serves SR-3 (China row), SR-20 (monthly proxies), SR-26 (composition), SR-27 (holder shares) and the block's absorber side. Both vintages stored; the block prints which it renders (G-8).

**2.2.2 Funding-currency stack (SR-2, SR-4).** Yen: `calc.jp_front_diff` and its 60-day change, `calc.jpy_pos_z` (CFTC COT), `calc.jp_hedged_carry`, `calc.jpy_unwind` (5-day USDJPY move against a realized-vol spike). RMB: `calc.cny_fix_dev`, `calc.cnh_cny_gap`, `calc.uscn_10y_spread`, and the deliberate-devaluation tell (fix stops leaning against the prior close ∧ CNH–CNY gap widens with CNH weaker ∧ state banks stop selling dollars — the third leg a by-hand field until a source exists). Candidate contradiction rows for the object: `carry_vs_vol` (JPY positioning vs. realized vol) and `fix_vs_offshore` (fix deviation vs. CNH gap) — declared, computed, no rights (G-10).

**2.2.3 China external position (SR-3).** Panel assembly deferred (Appendix C); its inputs — SAFE reserves, IIP, TIC China row, CNY fix, CGB 10y, the spread, CNH–CNY, CNH HIBOR — are all fetched in ST-2 so the panel is a rendering task later. Tail-register edits by hand now (Tranche H).

**2.2.4 US-vs-rest-of-world and the dollar cycle (SR-14, SR-26).** `calc.em_rel` (EM/World from MSCI `manual_input` and daily ETF proxies), `calc.em_rel_flag`, `calc.em_fx_contrib`; the flow-side confirmation is `calc.us_foreign_net_12m` (US residents' net foreign-securities purchases, from the flows table). Exit = SR-4's tell. Flag only after the dollar-split gate (ST-8).

**2.2.5 Reserve composition (SR-20).** §1.9. The holder-level layer is the same `tic.holdings_by_country` table SR-27 tags.

### 2.3 Thread E — Equity regime and cycle position (owner: Equities; Base Rates for the ledgers)

**2.3.1 Style (SR-1, SR-13).** `calc.gv_z`, `calc.gv_break`; `calc.techdef_spread` (annual, Ken French) with sub-basket `calc.def_z`. Style panel and Book B pair rule only after the SR-1 gate (ST-8); SR-13's spread line rides with it.

**2.3.2 Consumer credit (SR-5).** `calc.cc_z` on first prints (ALFRED vintages pulled by the calibration script; store ingestion is O.16), `calc.cons_rs` (uses the held `calc.cyclical_over_defensive` where it fits). Bull-side trigger candidate for T&B's bottom side after the gate and after T&B full; bear side as a Monthly tilt; RS tell as a Sunday line.

**2.3.3 Hiking cycles (SR-7, SR-21).** Base-rate table 1955– by hand in `data/reference/fed_cycles.csv` and a dated Base Rates ledger; SR-21's rows (long end after the Fed conceded vs. refused) added to the same table.

**2.3.4 False bottoms (SR-8).** Offline audit (ST-9) producing the confirmation-set scores and the bottom-side gate spec; wired at T&B full (ST-11). Fuel feeds: FINRA short interest is **already in the registry** (`finra.short_interest*`), as are breadth (`calc.breadth_*`) and VIX term structure (`calc.vix3m_over_vix`, `cfe.vx*`); margin debt and leveraged-ETF AUM are new (ST-2). The "rally inside bear" Daily flag lands in ST-10.

**2.3.5 AI funding and the memory cycle (SR-16, SR-25).** `calc.self_fund_ratio` (five names, 4q), `calc.hs_netdebt_12m`, `calc.aa_bbb_oas_diff`, `calc.ai_long_share`; `calc.mu_inv_days`; by-hand HBM share, DRAM direction, NIC/cover. Factor I evidence-log entries; human-gated.

**2.3.6 One-factor market (SR-19).** Deferred pending definition; the house metric (rolling R² of SPX on an equal-weight top-10 AI basket; equal-weight-490 beta to it) is specified in Appendix C for when it is wanted.

### 2.4 Thread A — Book A rule table (owner: Portfolio Construction; Base Rates meanwhile)

One table, three rules, one block. All three are candidates until their gates pass; none changes a Book state before then.

| Rule | Condition | Action | Source items | Gate |
|---|---|---|---|---|
| A-1 Hedge substitution | `rates.driver` ∈ {fed_path, term_premium}, or correlation member positive and persistent (SR-9 level prior) | Book A hedge mix shifts from duration to T-bills, gold, commodities, trend-following and option structures | SR-6, SR-9 | SR-9 regression (backlog) or driver calibration (ST-3) |
| A-2 Bear-regime re-entry | T&B top side fired and price below a falling 200-day | Bottom threshold rises; two of the confirmation set required before Book A re-enters; rallies in that state are Book C material | SR-8 | SR-8 audit (ST-9); wired at T&B full |
| A-3 Duration tilt | Bond allocation bottom decile (SR-12) ∧ Treasuries z ≤ −0.5 (SR-15) ∧ `ABS_STRESS` active (SR-22) ∧ `rates.driver` = term_premium | Tilt sized by \|z\|; exit when the driver flips to fed_path, or `ABS_STRESS` clears with yields higher, or the supply projection rises with no absorber change | SR-12, 15, 22, 23 | SR-12 and SR-22 gates (ST-7) |

**Cheap-and-Unloved block (Monthly, ≤10 lines).** Positioning: `calc.bond_alloc` (Z.1 complement; AAII/ICI `manual_input`) with expanding-window percentile and the bond/cash split. Valuation strip: `calc.val_z_gold / _spx / _ust / _cmdty` (single metric per asset, expanding window, via `derived_forms`), `calc.cmdty_gold_ratio`. Read: A-3's conditions with met/unmet marks; gold's z reported with zero rebalancing weight while Factor V is active.

### 2.5 Thread C — Oil buffer (owner: Energy)

`eia.crude_stocks`, `eia.product_stocks` (weekly), `calc.oil_buffer_state` (vs. 5-year seasonal band), IEA days-of-cover and the global-visible figure as `manual_input`, `calc.brent_wti` from held series, prompt spreads from yfinance/CME (G-11). Factor III line; tail-register Hormuz modifier. Projection rule fixture.

### 2.6 Overlay and trigger intake queue (T&B; applies once T&B full lands)

| Overlay / side | Queue, in order | Rule |
|---|---|---|
| Liquidity & Funding Stress | SR-2 yen unwind → SR-22 auction stress → SR-26/27 absorber fragility | One candidate at a time; the next enters champion/challenger only after the previous is adopted or rejected, so the overlay never double-counts a deleveraging mechanism |
| HY Spread Acceleration | SR-16 ring-3 HY spreads | After the SR-16 gate |
| Bottom side (triggers and gates) | SR-8 gate first (it raises the threshold), then SR-5 bull trigger | Gate before trigger, so a new trigger is tested against the raised threshold |
| Rate Repricing Velocity tag | `rates.driver` replaces any local tag | On T&B full (G-7) |
| Concentration & Complacency | SR-1 style flag only if it adds information beyond top-10 weight; SR-19 house metric if adopted | After gates |

### 2.7 Thread D — Digital asset mechanism watch (owner: Digital Assets; register entry SR-10)

Two additions to ongoing reporting: systematic coverage of Pearl (PRL) — Pearl Research Labs' proof-of-useful-work Layer-1 — through a fixed signpost set, stored series and weekly/monthly reporting; and a standing weekly scan for new coin technologies of the same class with a materiality bar, a register and a human-gated intake path. Pearl sits at the intersection of Factor I (the network is a live experiment in monetizing idle GPU capacity; its difficulty-vs-price behaviour reads how much rented GPU capacity has nothing better to do) and Factor V (a compute-backed native-currency claim). Both are watch-level interests, not scored inputs.

**2.7.1 Definitions.** *Novel-mechanism coin:* consensus or issuance makes a technical claim not already in production — proof-of-useful-work and AI-compute-backed chains; verifiable-compute consensus; new proof-of-work primitives with a paper (memory-hard, VDF-based, ASIC-resistant by construction); compute- or energy-backed monetary designs; fair-launch L1s grounded in peer-reviewed cryptography; post-quantum-native chains (lower weight). Excluded: memecoins; forks and rebrands; GPU-marketplace tokens that merely sell compute (Render/Akash/io.net class) unless they add a mechanism; L2s and rollups without a consensus novelty; restaking and yield derivatives. *Materiality bar (all three):* (i) an identifiable team with checkable credentials, or a paper on arXiv/IACR/a peer-reviewed venue; (ii) a live mainnet, or a credible testnet with public code; (iii) at least one of — an enterprise partner, a tier-1 listing (Coinbase, Binance, Kraken, OKX, Bybit, Upbit), market cap > $50M, notable mining/hashrate interest (hashrate.no, Kryptex, Hashrate Index), or coverage by a serious outlet (CoinDesk, The Block, Blockworks, Tom's Hardware, FT/Bloomberg/WSJ). *Thesis status (PRL):* UNCHANGED / IMPROVED / DETERIORATED, computed by rule with a trace string, overridable by hand; an informational label with no decision rights — not a state of the market-state object.

**2.7.2 Rulings MW-1…MW-10.**

- **MW-1 Coverage.** PRL enters the instrument table (`register/instruments.py`, the Security Master of Part 26 in this repo — G-24) as class `crypto.watch`, not core Alternative Asset coverage, with disambiguation fields `coingecko_id = "pearl-2"`, `name = "Pearl"`, `issuer = "Pearl Research Labs"`, `chain = "pearl (native L1, btcd fork)"`, `explorer = "https://explorer.pearlresearch.ai"`, `mechanism_class = "PoUW / AI-compute"`. The ticker `PRL` is never a key — at least three other projects use it (Perle on Solana; "Pearl" on Polygon; pearl.finance on Tron; "Pearl Research" on Base). A loader test rejects any entry keyed by ticker.
- **MW-2 Rights.** Discovery, attention and flag rights only. No input to the Monthly composite, the Top & Bottom detector, any overlay, or any Disruptive Themes factor, scenario or theme text; the block may post a graded narrative-register entry tagged Factor I or V. One narrow flag: the idle-GPU flag (D6), which may appear in the Sunday anchor and the Monthly under Factor I with no scoring effect. No Decision Packets; never DECISION_BLOCKED.
- **MW-3 Placement.** (a) Sunday 05:00 anchor: a Mechanism Watch block ≤12 lines (2.7.6) — at D6. (b) Monthly Macro Report: a Digital Asset Mechanism Watch part inside the digital-assets material; when the Alternative Asset report folds into the Monthly this part is the sole home. (c) Alternative Asset dashboard, Surveillance tab: PRL as a watch instrument until the fold (G-6). (d) Daily Cascade: excluded, enforced by a grep gate; single exception — the 12:30 alert-only slot may carry a tier-1 listing announcement or a chain incident as an information line with no setup rights.
- **MW-4 Data.** Every series through the point-in-time store with `available_at` (30.4: fetchers are timers, the blocks read the store). CoinGecko is the price source of record (`/coins/pearl-2`, `/tickers`, `/market_chart`; Demo key from the environment, header `x-cg-demo-api-key`; weekly plus one daily close pull stays inside the free tier). Chain height and difficulty from the explorer — confirm a JSON endpoint, fall back to parsing the block page, else estimate height from time since genesis at the 194 s target and mark ESTIMATED (G-26). Emission and supply computed from the formula in Appendix E and stored as derived series. Pool composition (S4) from pool dashboards where published; otherwise NOT AVAILABLE, never a guess (G-27).
- **MW-5 Emerging scan.** Weekly, ahead of the Sunday anchor, deterministic first and LLM second. The query set is declared in `config/story_queries.yaml` under a `mechanism_watch` group (G-28) and run by `altdata/sources/news.py`; CoinGecko's recently-added list (categories Proof of Work, AI, Layer 1) and the hashrate.no / Kryptex new-coin listings are the two non-RSS legs. A rule-based materiality pre-filter runs first; the LLM assessment step (Appendix F) is called only when at least one candidate passes — the gate stays closed otherwise, per the Audit #3 ruling. Candidates are de-duplicated against the instrument table and the `mechanism_watch` register.
- **MW-6 Intake path.** A candidate passing the bar is written to the register with status CANDIDATE. Only a human changes status: PROMOTE to WATCH (creates a `crypto.watch` instrument entry and a signpost set) or REJECT (kept, so it is not re-surfaced). Nothing auto-promotes. Status changes go through a one-line CLI, never by editing rendered output.
- **MW-7 PRL exit and promotion.** PROMOTE to core Digital Assets coverage when all three hold: ≥2 paid-compute partners live; a tier-1 listing; week-one overhang ratio (D2) < 25%. DEMOTE to a quarterly note when two consecutive quarterly reviews show no new partner, no listing progress and market cap < $50M. REMOVE when the chain stops producing blocks for 7 days, or the Together AI endpoint is withdrawn with no replacement partner within a quarter. Changes are recorded in the register and the change-orders edition.
- **MW-8 Documentation.** Digital Assets receives a dated appendix entry ("Mechanism watch — Pearl and proof-of-useful-work, as of 2026-09") carrying the dated figures; the timeless body gets one mechanism paragraph on proof-of-useful-work as a class only if none exists. `make library-check` must pass.
- **MW-9 Decommission of the interim scan.** The external Saturday scan retires after the Sunday block has published clean (validators green, no STALE PRL series) for four consecutive weeks, on Ari's confirmation.
- **MW-10 Publish behaviour.** The Sunday anchor always publishes (Part 28). On any fetch failure the block prints the last good values with their `available_at` and a STALE marker; it never blocks the anchor.

**2.7.3 PRL signposts S1–S8** (baseline as of 2026-09-19; each reported as a delta from the stored prior value).

| ID | Signpost | Measurement | Source | Cadence | Baseline 2026-09-19 |
|---|---|---|---|---|---|
| S1 | Paid-compute partners beyond Together AI | Named providers with a live Pearl-instrumented paid endpoint; terms; whether customers can pay in PRL | pearlresearch.ai blog, Together AI blog, announcements, scan | Weekly (narrative, `manual_input`) | 1 (Together AI, Gemma-4-31B-it-pearl, >25% discount funded by emissions) |
| S2 | PRL demand sink | Marketplace / on-chain compute contracts shipped; any PRL-denominated payment path | Pearl docs and repo, blog | Weekly (narrative) | None; "future direction" in docs |
| S3 | Exchange access | Venue count on CoinGecko tickers; top-venue volume share; any tier-1 listing | CoinGecko tickers | Weekly (data) | 3 venues (CoinEx, BigONE, SafeTrade); top venue ~91% of volume; no tier-1 |
| S4 | Mining composition | Explorer difficulty trend (30d); official H100/H200 pool share vs. community consumer-GPU pools where published | Explorer; pool dashboards | Weekly (data) | Difficulty ~21.4M at block 113,770; official pool 20% fee, H100/H200 only; share NOT AVAILABLE |
| S5 | Holder structure | Week-one overhang ratio (D2); supply gap (D3); disclosure or movement of week-one coinbase outputs | Formula; CoinGecko; explorer | Weekly (data + narrative) | Overhang 38.9%; gap 57.7M PRL, unexplained |
| S6 | Price vs. emission | Price, market cap, 24h volume; emission-to-volume (D4) | CoinGecko | Weekly (data); daily close stored | ~$1.00–1.15; mcap ~$250–280M; volume $1–6M; emission ~1.04M PRL/day |
| S7 | Technical and chain integrity | Training workloads, FP8/mixed precision, non-Nvidia support, proof gaming, reorgs, 51% concerns, exploits | Repo, blog, Hashrate Index, security researchers | Weekly (narrative) | Inference only; Nvidia only; W7A7 quantization disclosed; no incidents known |
| S8 | Team, funding, regulatory | Funding, hiring, securities-status commentary, exchange due-diligence signals | Scan, press | Weekly (narrative) | Nvidia Inception (July 2026); no founder allocation claimed; no funding news known |

**2.7.4 Derived metrics D1–D6** (stored `calc.prl_*` series with `available_at`; K = 650,226; H = current height).

- **D1 code supply** — `supply_code(H) = 2.1e9 · H / (H + K)`.
- **D2 week-one overhang ratio** — `121.70e6 / supply_code(H)`; 38.9% at baseline, ~19% at ~626M supply (about Sep 2027), ~12% at block 650,226.
- **D3 supply gap** — `supply_code(H) − coingecko_circulating`; 57.7M at baseline.
- **D4 emission-to-volume** — `(reward(H) · 86400/194 · price) / volume_24h`; above 0.5 daily issuance is a large share of turnover; above 1.0 the market is not absorbing miner selling at that volume.
- **D5 venue concentration** — top-venue share of reported volume.
- **D6 idle-GPU flag** — ON when explorer difficulty is up >25% over 30 days while price is down >20% over the same 30 days: GPUs pointed at Pearl because they have no better use — a Factor I attention item. Initial thresholds; calibrate after 90 days of stored data.

**2.7.5 Thesis status rule** (informational, overridable, trace string required). IMPROVED if in the review period any of: S1 gains a named partner; S2 ships a PRL-denominated path; S3 gains a tier-1 listing; D5 falls below 60% with volume up. DETERIORATED if any of: S7 records an exploit, chain halt or reorg; the Together endpoint is withdrawn; D4 stays above 1.0 for four consecutive weekly reads; a top venue delists. UNCHANGED otherwise.

**2.7.6 Block layouts.** *Sunday 05:00 anchor — Mechanism Watch block (≤12 prose lines, no table):* header with the week; one PRL line (thesis status, price and weekly change, market cap, D4, venues and top share, 30-day difficulty change); "Signposts moved:" listing only those that moved; "Flags:" with the idle-GPU state; "Candidates:" from the scan; "Comparables:" ("—" when empty); a data-as-of line naming any STALE series. *Monthly — Digital Asset Mechanism Watch part:* (1) one paragraph — thesis status with the rule trace and what moved; (2) the S1–S8 table with baseline / prior month / now / change; (3) optional figure from the existing figure tooling — realized vs. designed supply with the overhang-ratio path; (4) candidates found this month with status and any status changes made; (5) narrative-register entries posted this month (`date · class=mechanism-watch · factor=I|V · grade · ≤60 words · source`). Dated figures stay in this part; nothing alters the Monthly composite.

**2.7.7 Emerging-scan specification.** Query set (past 14 days where the engine allows): `"proof of useful work"`; `"AI compute" cryptocurrency mainnet`; `"fair launch" layer 1 GPU mining`; `"verifiable compute" blockchain consensus`; `"new proof-of-work" cryptocurrency`; `"post-quantum" blockchain mainnet launch`; `site:hashrateindex.com`; `site:tomshardware.com mining`; `site:arxiv.org "proof of useful work"`; `site:eprint.iacr.org "proof of work"`; plus the CoinGecko recently-added filter and the hashrate.no / Kryptex listings. Pre-filter: drop anything already in the instrument table or the register (any status); drop exclusion classes by keyword with a manual override list; require at least one materiality-bar (iii) hit detectable by rule (a tier-1 exchange name, a market-cap figure above $50M, a serious-outlet domain, a hashrate-tracker listing). Survivors open the gate for the LLM step (Appendix F), which checks (i) and (ii) and writes the register fields. Register schema (`mechanism_watch` store table; `docs/mechanism-watch-register.md` is a rendered view from `make mechanism-register`): `id · name · canonical_id · mechanism_class · whats_new · team_or_paper · stage (paper / testnet / mainnet) · materiality_evidence · key_risk · grade (the narrative register's scale; CANDIDATE enters at the lowest grade) · status (CANDIDATE / WATCH / REJECTED / PROMOTED) · first_seen · last_reviewed · sources`. Comparables clause: developments at Bittensor, Gensyn, Ritual and Kaspa-style fair launches are reported only when they bear on the PoUW / AI-compute thesis, as one Sunday line; they are not register candidates. Prediction-market cross-link (optional, after PM-1): a Polymarket/Kalshi market naming Pearl or a register candidate appears as an attention item; no rights.

**2.7.8 Falsifiers and review.** Useful if, over 90 days, at least one signpost moved and was reported before it appeared in mainstream crypto press, or at least one register candidate earned a WATCH promotion; if neither, the scan cadence drops to monthly and PRL coverage is reviewed under MW-7. D4/D6 threshold review at the first Monthly with 90 days of stored data (target January 2027). Quarterly PRL review against MW-7 at each quarter-end Monthly from December 2026. The Annual Structural Review decides whether "novel-mechanism coins" remains a watch category or folds into Digital Assets coverage.

---
## §3 Rulings register (SR-1…SR-27)

Master table, by thread. Full entries follow in SR order. Batch 1 entries (SR-1…SR-9) are as ruled on 19 Sep with integration edits marked *[integ.]*; Batch 2 entries (SR-12…SR-27) are as ruled on 24–25 Sep with pointers updated.

| SR | Thread | Item (source, date) | Ruling | Rights class | Built in |
|---|---|---|---|---|---|
| 1 | E | Growth/Value relative performance (Weniger, 8 Sep) | Adopt mechanized; reject trendline | Narrow flag (after gate) | ST-8 → backlog panel |
| 2 | X | Yen carry stack (chat, 10 Sep) | Adopt four metrics; unwind tell + positioning first | Narrow flag → overlay queue #1 | ST-5, ST-10 |
| 3 | X | China external position (shadow-reserves post, 11 Sep) | Adopt panel inputs; reject conclusion; panel assembly deferred | Panel only | ST-2 feeds; tail edits by hand |
| 4 | X | US–China 10y spread / RMB funding (X post, 10 Sep) | Adopt as SR-2/3 inputs; devaluation tell in full; reject fade | Narrow flag (tell) | ST-5 |
| 5 | E | Consumer credit impulse (deGraaf/RenMac, 8 Sep) | Adopt bull side as trigger candidate, RS tell; bear side as tilt | Trigger candidate / modifier | ST-8; wired ST-11 |
| 6 | R | Yield move attribution (Runkevicius, 15 Sep) | Adopt block as `rates.driver` evidence; reject single-model reading | Confidence modifier | ST-3 |
| 7 | E | Hiking-cycle conditional table (Macrobond) | Adopt table by hand; reject unconditional average | None (base rate) | Tranche H |
| 8 | E/A | Bear-market rally structure (Lemand, 19 Sep) | Adopt audit + bottom gate + Doctrine rule candidate | Gate | ST-9; wired ST-11 |
| 9 | R/A | 5.25% and stock-bond correlation (Simon White, Sep) | Adopt as `rates.driver` correlation member and Book A rule A-1; reject level | Confidence modifier | ST-3 |
| 10 | D | Digital Asset Mechanism Watch — Pearl (PRL) signposts S1–S8 and the emerging-mechanism scan (19 Sep order, integrated 26 Sep) | Adopt; watch-level rights only (MW-2) | Narrow flag (idle-GPU D6); discovery/attention otherwise | ST-13, ST-14, ST-15; Sunday block at ST-10 |
| 11 | — | *Reserved:* Consensus drift (19 Sep batch Part C) | Backlog | — | Appendix C |
| 12 | A | Investor bond allocation (Topdown, 24 Sep) | Adopt Book A line + conditional base rate; reject unconditional contrarian read | Modifier (after gate) | ST-6, ST-7 |
| 13 | E | Tech vs. defensives valuation (Topdown/LSEG, 24 Sep) | Adopt as SR-1 anchor + base rate; reject rates channel | Modifier after SR-1 gate | ST-8 |
| 14 | X | EM absolute and relative (Topdown/LSEG, 24 Sep) | Adopt US-vs-RoW line + trend flag; reject "decadal turn" | Narrow flag (after gate) | ST-8 |
| 15 | A | Cross-asset valuation z-scores (Topdown/LSEG, 24 Sep) | Adopt light strip + rebalancing modifier; reject "cheap commodities" | Modifier (after gate) | ST-6, ST-7 |
| 16 | E | Hyperscaler debt supply / absorption (Bloomberg via Lemand, 24 Sep) | Adopt Factor I funding panel + flag; reject issuance headline | Narrow flag | ST-4/ST-6 |
| 17 | R | Real-yield-led selloff (Alpine Macro / Zhao, 24 Sep) | Merged into `rates.driver` (DKW arbiter); no new analysis | None new | ST-3 |
| 18 | C | Oil inventories vs. operational floor (JPM/Bloomberg; 15–25 Sep) | Adopt buffer state; reject chart as a print (projection fixture) | Narrow flag | ST-2, ST-6 |
| 19 | E | "3-month / 1-year beta" chart (Monchau) | DEFERRED — definition required | None | Appendix C |
| 20 | X | IMF COFER Q1 2026 + reserve tracker (25 Sep) | Adopt Factor V scorecard; reject level as signal | None | ST-2; Tranche H |
| 21 | R | Oct 28 hike probability 70–77% (Bianco, 24 Sep) | Adopt Fed–market gap, credibility flag, Warsh cell, PM case; reject political framing | Narrow flag | ST-4 |
| 22 | R | 5y auction 5.033%, TLT record low (Padley, 24 Sep) | Adopt auction absorption; reject "meltdown"; Doctrine note | Narrow flag; A-3 input | ST-1, ST-4, ST-7 |
| 23 | R | G4 issuance gap vs. real yields (Lustig, 24 Sep) | Adopt — highest value; US monthly + projection | Modifier | ST-4, ST-7 |
| 24 | R | 5y5y breakeven vs. commodity producers (Costa, chart 12 Sep) | Adopt de-anchoring flag (definition only); reject trendline and producers-as-lead | Narrow flag | ST-4 |
| 25 | E | Burry AI shorts (Monchau via Bull Theory, 24 Sep) | Reject as signal; adopt memory-cycle tell; narrative-register entry | None | ST-4 (+MU) |
| 26 | X/R | TIC flows, 12m to Jul 2026 (Riemann, 24 Sep) | Adopt composition read; reject "demand collapsed" | Absorber-fragility modifier (after gate) | ST-2, ST-4 |
| 27 | X/R | TIC Major Foreign Holders, 12m change (research note) | Adopt holder panel with mechanism tags; reject "China dumping" | Absorber-fragility modifier (after gate) | ST-2, ST-4 |

### SR-1 Growth vs. Value relative performance (Weniger, 8 Sep 2026) — Thread E

**Ruling.** Adopt the ratio, mechanized. Reject the 1980–2000 trendline as a rule: three touches in fifty years, and the line exists only on a linear axis (drawn through the same 1980 and 2000 points in log space, 2021 never touched it and 2026 has not). Defer any T&B overlay input until validation shows information beyond top-10 weight.

**Home.** Monthly style-regime panel; Book B pair trade; Book A tilt (cap-weight → value/equal-weight). Mechanism in Equities (concentration chapters); tactical expression in Positioning & Flows. Fills a real gap: the stack is heavier on top detection than on what leads next. *[integ.]* SR-13's tech/defensives spread is this panel's valuation anchor; the two are one backtest session (ST-8) and one panel.

**Rights.** Narrow flag: "Style regime — growth extreme / rotation triggered." Only after the gate.

**Rule to test.** Log Growth/Value total-return ratio, z-score vs. its 10-year trend > +2 (via `derived_forms`), followed by a break: ratio below its 40-week MA, or >8% off its 52-week high. Expression: long IVE / short IVW (or IWD/IWF), sized as a pair, hard stop on a new ratio high (2023 is the reason for the stop).

**Data.** IVW/IVE, IWF/IWD daily from 2000 via yfinance (total return; point-in-time). Ken French HML monthly from 1926 for long calibration (library revised occasionally — log the vintage). S&P's own index history is licensed; skip. *Lives in:* `yfinance.mkt_ivw` etc.; `calc.gv_z`, `calc.gv_break`.

**Validation gate.** Forward 3/6/12-month value-minus-growth after each trigger, HML from 1963 and ETFs from 2000; hit rate and asymmetry; check the late 1990s for early fires and 2023 for the reversal. Ledger in Base Rates. Pass: positive expectancy after costs at 6 and 12 months across ≥6 non-overlapping episodes. Offline (ST-8).

### SR-2 Yen carry stack (chat question, 10 Sep 2026) — Thread X

**Ruling.** Adopt. Confirmed gap: the yen section of the Alt Asset build carries carry-trade prose with `[LIVE DATA REQUIRED]` placeholders; the Monthly and the June 2026 rate-expectations spec pull only the US legs. Currencies and The Rate and Liquidity Machine explain the mechanism; nothing computes it.

**Home.** Monthly Factor IV panel; T&B Liquidity & Funding Stress overlay input after the gate (an unwind is a deleveraging mechanism) — **queue position #1** (§2.6); Daily Cascade risk-off flag in the 07:00 anchor, with the 12:30 alert if the unwind tell trips intraday. Books A and C. *[integ.]* Metric 3 (hedged carry) is consumed by the Duration Absorption block as the explanation of Japan's holdings line (SR-27) — computed once here.

**Metrics (four, not one).** (1) Front-end differential: US 2y (or 3m) minus Japan, plus its 60-day change — velocity mattered in Aug 2024, not level. (2) Positioning: CFTC yen net non-commercial position, z-scored — the fuel. (3) Hedged carry for Japanese investors: 10y UST − (3m USD − 3m JPY); negative means hedged Treasury buying stops — the Treasury-demand / term-premium channel. (4) Unwind tell: USDJPY 5-day move against a realized-vol spike.

**Rights.** Narrow flag at launch; overlay input after the gate, in queue order.

**Data.** FRED Japan 10y and 3m (monthly); Japan MoF daily JGB yield CSV; CFTC COT weekly (Tuesday positions, Friday release — `available_at` = release); USDJPY held (`fred.usd_jpy`, plus yfinance daily). JPY implied vol and risk reversals are not free; use realized. *Lives in:* `altdata/sources/cftc.py`, `mof_jgb.py`; `calc.jp_front_diff`, `calc.jpy_pos_z`, `calc.jp_hedged_carry`, `calc.jpy_unwind`; candidate contradiction row `carry_vs_vol`.

**Validation gate.** Anatomy check on Oct 1998, 2007–08, Jan–Feb 2016, Aug 2024 (narrowing differential + crowded shorts + vol spike). Pass: all four flagged with ≤2 false positives 1998–2026 at the chosen thresholds. Offline (ST-8); thresholds then set in `config/market_state.yaml`.

### SR-3 China external position (shadow-reserves post, 11 Sep 2026) — Thread X

**Ruling.** Adopt as a Monthly China panel. The post's facts are accepted (Setser: ~$6T state-controlled foreign assets — SAFE's ~$3.4T plus state commercial banks, policy banks and CIC; NIIP north of $3T; the PBOC's balance sheet is FX and bank loans, not government debt). Its conclusion is rejected: external creditor status and an RMB-denominated debt deflation coexist (Japan 1990). "Hidden" overstates it — the assets appear in the quarterly IIP; they are not classified as reserves, and much of the shadow layer is illiquid. *[integ.]* Panel **assembly** is deferred (Appendix C, as tranched on 19 Sep); its inputs are fetched in ST-2 so assembly is a rendering task; the China Treasury-holdings row comes from the shared `tic.*` family with SR-27's custodial caveat (G-9).

**Home.** Monthly (Alt Asset folds into the Monthly per the 7 Sep ruling); tail register; Factor V thread (reserve diversification, official gold bid; explains why China's Treasury holdings fell without dollar selling).

**Panel.** SAFE reserves (monthly); banks' net foreign assets from the quarterly IIP; TIC China Treasury holdings (monthly, both vintages); CNY fix vs. band (daily); from SR-4: CGB 10y level, US–China 10y spread, CNH–CNY gap, CNH HIBOR.

**Tail register edits (by hand, Tranche H).** CNY balance-of-payments crisis: score low — the state controls the capital account and official reserves alone cover external debt; any sharp devaluation is a choice, not a forced event. Domestic deflation / balance-sheet recession: keep fully live (the Koo case in the Debt Cycles brief). New scenario: deliberate devaluation to export deflation — Factor III/IV cross; hits commodities, EM FX and US inflation expectations together; tell defined in SR-4.

**Rights.** Panel only.

**Data.** SAFE (reserves, IIP, BoP); US Treasury TIC; CFETS central parity. All free. *Lives in:* `altdata/sources/safe.py`, `tic.py`, `cfets.py`.

### SR-4 US–China 10-year spread and RMB as funding currency (X post, 10 Sep 2026) — Thread X

**Ruling.** Adopt as inputs to SR-2 and SR-3. Reject "widest ever" as a fade signal: a 24-year record set inside a four-year inverted regime (US above China through much of the 2000s, China above the US ~2010–2022, inversion since April 2022), and the two legs price off unrelated regimes; Japan–US stayed wide for two decades. The devaluation tell is built in full now (ST-5); it is also SR-14's exit.

**Home.** China panel (spread and CGB level as regime context; CGB below 2% is the Japanification gauge on its own). Funding-currency stack: the RMB leg beside JPY in SR-2 — panda-bond issuance, CNH HIBOR, CNH–CNY gap — with the note that the PBOC controls offshore CNH liquidity (overnight CNH HIBOR reached 66% in January 2016), so RMB carry unwinds are policy-driven and abrupt.

**Rights.** One narrow flag — the deliberate-devaluation tell: the fix stops leaning against the previous close, the CNH–CNY gap widens with CNH weaker, and state banks stop selling dollars (third leg a by-hand field until sourced).

**Data.** DGS10 (held); FRED China 10y monthly (IRLTLT01CNM156N) and ChinaBond daily; CFETS fix; CNH=X (yfinance); HK TMA CNH HIBOR; panda-bond volumes as a monthly `manual_input`. *Lives in:* `calc.cny_fix_dev`, `calc.cnh_cny_gap`, `calc.uscn_10y_spread`, `calc.deval_tell`; candidate contradiction row `fix_vs_offshore`.

**Validation gate.** Calibrate fix-deviation and CNH–CNY thresholds on Aug 2015–Jan 2017 and Sep 2022–Sep 2023. Base rate for spread persistence from Japan–US 1998–2022. Offline (ST-8).

### SR-5 Consumer credit impulse (deGraaf / RenMac, G.19 July print, 8 Sep 2026) — Thread E

**Ruling.** Adopt the bull side (bottom decile of the 6-month-average net-change rolling z-score: 84% W/L, ≈+9% six-month expectancy, double the base rate) as a T&B bottom-confirmation candidate — same asymmetry as the existing calibration, stronger at bottoms than tops. Log the bear side (top decile: 59% W/L, ≈−0.5% expectancy against ≈+4.5% unconditional) as a Monthly tilt only. Adopt the consumer-dependent relative-strength tell. Reject as a standalone top signal. *[integ.]* Enters T&B's bottom side **after** SR-8's gate (§2.6), so it is tested against the raised threshold.

**Mechanism notes for the register.** Late-cycle borrowing sustains spending income no longer supports; the clean historical hits (1969, 1973, 1979, 2000, 2007) were inflation-and-tightening peaks; 1994–95 was the loud miss. ~70 overlapping observations reduce to ~12 episodes; rolling z-scores inflate after quiet stretches (2023–25); composition matters (revolving spike = distress, nonrevolving spike may be auto pull-forward).

**Home.** T&B bottom side; Monthly consumer/credit pillar; weekly Book B tell (XLY/XLP — the held `calc.cyclical_over_defensive` where its definition matches; equal-weight discretionary vs. SPY; homebuilders).

**Rights.** Bull side: trigger candidate after gate. Bear side: confidence modifier. RS tell: narrow flag.

**Data.** TOTALSL, REVOLSL, NONREVSL (FRED) with ALFRED first-print vintages. G.19 lag ≈5 weeks; heavily revised. *Lives in:* `fred.consumer_credit*` (new, with vintages once O.16 lands; the calibration script pulls ALFRED directly meanwhile); `calc.cc_z`, `calc.cons_rs`.

**Validation gate.** Replicate at 5- and 10-year z windows; count non-overlapping episodes; run the revolving-only variant; rerun everything on first prints. Bull side passes if first-print six-month expectancy stays ≥2× unconditional across ≥8 episodes. Offline (ST-8).

### SR-6 Yield move attribution (Runkevicius, SF Fed decomposition, 10y at 5%, 15 Sep 2026) — Thread R

**Ruling.** Adopt an attribution block. Reject the single-model conclusion: term-premium models (SF Fed Christensen–Rudebusch, NY Fed ACM, Board Kim–Wright) disagree on level and can disagree on the sign of a change over months; the "expected short rate" leg is a residual, not a survey; ACM in particular pushes short-run shocks into term premium. *[integ.]* **The block is the evidence set of `rates.driver` (§2.1.1), not a tag of its own.** The two-state regime tag in the 19 Sep ruling (path-driven-real; term-premium/supply) becomes the `fed_path` and `term_premium` cells; `growth` and `mixed` are added; SR-17's DKW real-side split joins as the fourth model and the sign arbiter; SR-9's correlation is a member.

**Home.** The Rate and Liquidity Machine; `rates.driver` in the market-state object; feeds the Rate Repricing Velocity overlay's hawkish/dovish tag when T&B is built (G-7) and the Valuation trigger's ERP input; Book A rule A-1; Warsh matrix.

**Block.** For 1-week, 1-month and since-event windows: Δ10y = Δbreakeven + Δreal (`fred.breakeven_10y`, `fred.tips_10y`); Δ10y = Δ2y + Δ(10s–2s) (held series); model term premia as tie-breakers — Kim–Wright (THREEFYTP10), ACM, SF Fed, DKW real term premium. Cell rule as in §2.1.1.

**Rights.** Confidence modifier: `fed_path` → weight the valuation-compression channel up in T&B. The 5% level itself is logged as a valuation input (ERP; earnings yield below bond yield at a >20× forward multiple), not an event.

**Data.** DGS2/DGS10/T10YIE/T5YIFR (held); **DFII10 (new — not among the 59)**; THREEFYTP10 (new); ACM CSV (NY Fed, new source); SF Fed Treasury Yield Premiums (per publication, new source); DKW (Fed Board Excel, new source); SPY, TLT (yfinance). *Lives in:* `fred.tips_10y`, `fred.term_premium_kw`, `acm.*`, `sffed.*`, `dkw.*`; `calc.attr_*`, `calc.corr_spy_tlt_60d`; `rates.driver`.

**Validation gate.** Run the four models side by side over Feb–Sep 2026; where they disagree on sign, the curve decomposition arbitrates. Calibrate forward equity returns and stock-bond correlation on the bear-flattening set (1994, Q4 2018, 2022) vs. the bear-steepening set (2013, Aug–Oct 2023), plus SR-17's four DKW episodes. Offline ledger (ST-3); cell thresholds then declared in config.

### SR-7 S&P returns during Fed hiking cycles (Macrobond, five cycles since 1994) — Thread E

**Ruling.** Adopt a conditional base-rate table. Reject the unconditional average: the chart measures first hike → first cut, which is the calm window; three of the five were followed by 25–55% declines after the endpoint (2001, 2007, 2020); the sample is Great Moderation only, and the one "coincidence" (1999–2000, CAPE 44) is the only cycle that began at current valuations. *[integ.]* Built by hand (as tranched); SR-21's rows join the same table.

**Home.** Base Rates (table); Debt Cycles brief, tops-from-inside Part (hiking into a bubble: 1929, 1937, 1973, 2000, 2018); Bull Rebuttal gate entry for "stocks rise during hiking cycles." Book A.

**Table spec.** All cycles since 1955 (~15 rows): first hike, last hike, first cut; returns first hike→last hike, last hike→first cut, first cut→+12m; max drawdown inside the cycle and within 12 months after the last hike; conditioned on starting CAPE (>30 vs. <25) and on supply-shock inflation; cut type (insurance vs. recession); **plus SR-21's columns: whether the Fed conceded to or refused market pricing at the turn, and the long end's 3m move after.** Monthly note: a cycle starting at CAPE ~40 has n=2 analogs (1999, 2022), both with drawdowns first.

**Rights.** None (base rate).

**Data.** FEDFUNDS, USREC (FRED, new); Shiller data; yfinance; hand-coded cycle-date table `data/reference/fed_cycles.csv`.

### SR-8 Bear-market rallies as structure (Lemand, Nasdaq 2000–02, 19 Sep 2026) — Threads E and A

**Ruling.** Adopt a T&B false-bottom audit, a bottom-side gate and a Doctrine rule candidate. The bottom side was calibrated on real bottoms; the false ones (five rallies of 12–45% inside a 78% decline, each a "bottom" in real time) are the untaken test. *[integ.]* The audit is offline (ST-9) and produces the gate spec; wiring waits for T&B full (ST-11). The gate is Book A rule A-2 (§2.4) and precedes SR-5's trigger in the bottom-side queue.

**Home.** T&B; Operating Doctrine; Positioning & Flows (fuel metrics); operator behavioral paper (behavioral inventory: the dip-buying cohort, the rally trap); Daily "rally inside bear" flag (ST-10).

**Confirmation set.** Breadth thrust in the first weeks; leadership by new groups rather than the most-shorted prior leaders; HY spreads tightening through the rally; VIX term structure back in contango; a successful retest. Time prior: bears off valuation peaks run two to three years, so a bottom four months in is a low-probability call by base rate alone.

**Gate.** Once the T&B top side has fired and price is below a falling 200-day, the bottom threshold rises and two of the confirmation set are required before Book A re-enters; rallies in that state are Book C material.

**Doctrine rule candidate (number to be assigned).** "In a declared bear regime a rally is a mechanism, not a signal. Book A re-entry requires the bottom composite plus confirmation. Size on the assumption that a bear rally and a new bull are indistinguishable in real time."

**Fuel metrics.** FINRA margin debt (monthly, new); leveraged-ETF AUM from issuer daily files (new); FINRA short interest (**already registered**: `finra.short_interest`, `finra.short_interest_days_to_cover`); breadth (**already registered**: `calc.breadth_*`); VIX term structure (**already registered**: `calc.vix3m_over_vix`, `cfe.vx1/2/3`).

**Validation gate.** Replay the bottom side rally-by-rally through 2000–02, 2007–09 (Mar 2008), 1973–74 and 2022 (Mar; Jun–Aug); count false bottoms. Score each confirmation element on whether it separates those from Oct 2002, Mar 2009, Oct 1974 and Oct 2022. Elements that discriminate enter the gate; elements that don't are dropped.

### SR-9 5.25% and stock-bond correlation (Simon White, Sep 2026) — Threads R and A

**Ruling.** Adopt as the correlation member of `rates.driver` and as Book A rule A-1. Reject 5.25% as a line: it is an era effect — the 10y sat above 5.25% almost continuously 1973–98 and below it 2001–23, and the correlation flipped negative around 1998–2000 when growth shocks replaced inflation shocks as the dominant driver. Yield level is a proxy for the inflation regime, not a cause. *[integ.]* The scatter regression is deferred (Appendix C, as tranched); the level prior stays a by-hand note; the correlation itself is `calc.corr_spy_tlt_60d`, computed once.

**Home.** The Rate and Liquidity Machine; Book A hedge-substitution rule (A-1); Market Structure & Cascades (risk-parity and target-vol de-levering as a named cascade channel); Warsh matrix — the reaction-function variable "does the Fed defend the front end or the long end," which `rates.driver` adjudicates in real time (10y rising through breakevens/term premium with the front end anchored = the long end is lost; rising through the expected path = tight but credible).

**Rule.** Yield-level prior: above ~5.25%, treat a positive correlation reading as persistent rather than transient. When the driver is `fed_path` or `term_premium` (or the correlation member is positive and persistent), Book A's hedge mix shifts from duration to T-bills, gold, commodities, trend-following and option structures (defined-outcome work applies here).

**Rights.** Confidence modifier.

**Data.** ^GSPC daily; constant-maturity 10y return proxy built from DGS10 (1962–); SPY, IEF/TLT for the live reading; core CPI (held) and its rolling volatility as the regime variable. *Lives in:* `calc.corr_spy_tlt_60d`, `calc.infl_vol`.

**Validation gate (backlog).** Reproduce the scatter (2-year rolling correlation of weekly changes vs. 10y level). Regress next-6-month correlation on yield level and inflation volatility. If level adds nothing, inflation vol is the lever and 5.25% stays a heuristic.

### SR-10 Digital Asset Mechanism Watch — Pearl (PRL) and the emerging-mechanism scan (change order of 19 Sep 2026; integrated 26 Sep) — Thread D

**Ruling.** Adopt. PRL under systematic coverage as a `crypto.watch` instrument with signposts S1–S8, derived metrics D1–D6 and a rule-based thesis status; a weekly emerging-mechanism scan with a materiality bar, a store-backed register and a human-gated intake path. Full specification in §2.7.

**Home.** Sunday 05:00 anchor (Mechanism Watch block, at D6); Monthly Macro Report (Digital Asset Mechanism Watch part); Alternative Asset dashboard Surveillance tab until the fold; Disruptive Themes narrative register (Factor I or V entries, graded); Digital Assets (dated appendix). Excluded from the Daily Cascade except the 12:30 information line.

**Mechanism.** Factor I: difficulty-vs-price behaviour reads idle GPU capacity seeking yield — the idle-GPU flag. Factor V: a compute-backed native-currency claim. Thesis for the coin itself: paid compute must overtake speculative mining, a PRL demand sink must ship, and the week-one overhang (38.9% of supply minted in the first 5.9 days at difficulty 1) must dilute before a tier-1 listing is plausible; the 57.7M PRL gap between code-derived and reported circulating supply is unexplained; three small venues with one at ~91% of volume; Nvidia-only mining. Evidence: Hashrate Index (2 Jun), Together AI announcement (15 May), Tom's Hardware (31 May), Alea Research, the Pearl repo and explorer, the Komargodski–Weinstein paper (arXiv 2504.09971).

**Data.** CoinGecko (`pearl-2`; price, market cap, 24h volume, circulating, tickers) weekly plus a daily close; explorer height/difficulty weekly with the MW-4 fallbacks; emission and supply from the Appendix E formula; S1, S2, S7, S8 as `manual_input` narrative fields fed by the scan. *Lives in:* `altdata/sources/coingecko.py` (existing switch turned on), `altdata/sources/pearl_explorer.py`; `calc.prl_supply_code`, `calc.prl_overhang`, `calc.prl_supply_gap`, `calc.prl_emission_to_volume`, `calc.prl_venue_conc`, `calc.prl_idle_gpu_flag`, `calc.prl_thesis_status`; `mechanism_watch` store table.

**Rights.** Narrow flag (D6) under Factor I; discovery and attention otherwise; graded narrative-register entries; no scoring, no theme changes, no overlay path (MW-2). Candidates: register status only, human PROMOTE/REJECT (MW-6).

**Validation.** Formula unit tests (block 1 ≈ 3,229.6 PRL; block 113,770 ≈ 2,339.4 PRL; supply at 113,770 ≈ 312.72M); D4/D6 thresholds calibrated after 90 days; the 2.7.8 usefulness test at 90 days; quarterly MW-7 review from December 2026. Falsifiers: the DETERIORATED conditions of 2.7.5; MW-7's demotion and removal rules.

**Disposition.** Adopt as Tranche 5 (ST-13, ST-14, ST-15; Sunday block in ST-10; dated appendix in ST-L; parallel run and decommission in ST-12). ≈25.5 h of sessions plus the shared items. The interim Saturday scan runs until MW-9.

### SR-11 *Reserved* — Consensus drift — 19 Sep batch Part C

Register entry points to the Part C specification and its backlog status (Appendix C). The interim bimonthly scan (§1.12) continues.

### SR-12 Investor bond allocation (Topdown Charts, AAII + ICI + Fed FoF blend, 24 Sep 2026) — Thread A

**Ruling.** Adopt as a Book A positioning line plus a conditional base-rate table; reject the unconditional "classic contrarian play." No T&B or composite rights.

**Home.** Monthly Cheap-and-Unloved block (§2.4); Portfolio Construction (the duration-vs-commodities barbell; rule A-3); Base Rates (the table).

**Mechanism.** The series is mostly the complement of two things already scored — the equity share (a price artifact carried by CAPE ~40 and the Complacency overlay) and the cash share built when bills paid 4–5% — so the ~18.5% trough is correlated confirmation of late-cycle positioning, not independent information, and would double-count Valuation in T&B. The one independent piece is the bond-vs-cash split: cash rotating into duration as bill yields fall is a testable flow mechanism and the real catalyst behind the contrarian case. Regime caveat is the whole game: the 1987 start makes the sample disinflation-only, and both prior troughs (2000, 2007) resolved through recession-driven bond rallies under negative stock-bond correlation. In an inflation regime a low allocation is a persistent condition, not a setup (Z.1 equivalents in the late 1960s/1972 were followed by a decade of real losses). "Underowned" pays only in the `growth` or `term_premium` cell.

**Data.** AAII allocation survey (monthly from Nov 1987; three numbers a month as `manual_input`); ICI fund assets by type (monthly, free); Fed Z.1 via FRED (quarterly, ~10-week lag) — the Z.1 complement extends the window to the early 1950s and adds inflation-regime episodes. *Lives in:* `manual.aaii_*`, `fred.z1_*`; `calc.bond_alloc`, `calc.bond_cash_split`.

**Rights.** Base rate; confidence modifier for Book A duration sizing only after the gate; input to rule A-3.

**Validation gate.** Episodes: bottom-decile readings (AAII 2000, 2007, 2024–26; Z.1 adds late 1960s/1972). Statistic: forward 12m and 36m 10y Treasury total return, nominal and real, vs. cash, split by trailing CPI ≥4% / <4% and by 1y stock-bond correlation sign. Pass for the modifier: in the growth/term-premium cell, median real return beats unconditional with ≥2/3 hit rate. If the split does not separate, table only. Falsifier: bonds lose to cash over 12m from a bottom-decile print in an inflation regime. Offline (ST-7).

### SR-13 Tech (TMT) vs. defensives relative valuation (Topdown Charts / LSEG, 24 Sep 2026) — Thread E

**Ruling.** Adopt as the valuation anchor for SR-1's style panel plus a base-rate table; reject the standalone rates-channel read. No T&B or composite rights.

**Home.** SR-1 style panel; Book A tilt; Book B pair note; Base Rates; Equities (concentration chapter).

**Mechanism.** The object is the spread, not either line: ≈+115% tech vs. a record ≈−38% defensives, ≈150 pp — widest since 2000–01, though 2000 peaked near 210 pp and sat above today's level for about two years first. Level is magnitude, not timing; timing comes from the relative-performance break SR-1 mechanizes. The tech leg is the concentration story already carried (Complacency overlay, Factor I, Equities) — adding it to T&B double-counts. The incremental piece is the defensives leg: a record discount is the unloved-asset condition, mirror of SR-12. Two construction checks: the basket is internally dispersed (utilities re-rated on the AI-power bid; healthcare's discount is partly policy-driven and does not revert on the cycle) — show staples / healthcare / utilities separately; and 1972 is the counterexample where defensives were the expensive one-decision leg. The rates mechanism is misassigned: mega-cap tech is cash-rich; the duration channel bites the unprofitable growth tier, and only when real yields drive the move (`rates.driver`). The 2003–10 path is the quiet falsifier: the premium fell from ≈160% to ≈20% largely through earnings catch-up with flat relative prices — spread reversion ≠ tech crash ≠ defensives rally.

**Data.** Kenneth French industry portfolios (annual sum-BE/sum-ME for relative P/B by industry from 1926; monthly returns for the forward test); Damodaran industry multiples (annual since ~1998) as cross-check; sector ETF trailing multiples via yfinance for the current print (sector ETFs are already fetched). *Lives in:* `calc.techdef_spread`, `calc.def_z` by sub-basket.

**Rights.** Base rate; Book A tilt modifier gated on SR-1's break; no new flag.

**Validation gate.** Episodes: top-decile spread (1929, 1968–72, 1983, 1999–2000, 2020–21, 2024–26). Statistic: forward 12/36/60m relative return of defensives vs. tech, (a) on spread alone, (b) on spread plus negative 12m tech relative momentum. Pass for the tilt modifier: defensives' 36m relative return positive in ≥4 of 5 completed episodes in cell (b). Falsifier: reversion via earnings with flat relative prices. Runs in SR-1's session (ST-8).

### SR-14 EM equities, absolute and relative to DM (Topdown Charts / LSEG; MSCI EM from 1987, 24 Sep 2026) — Thread X

**Ruling.** Adopt as a Book A US-vs-rest-of-world allocation line with one mechanized trend flag; reject "decadal turning point" as a standing claim. No T&B or composite rights.

**Home.** Monthly Factor IV / dollar panel (US-vs-RoW block: EM/World and ACWX/SPY, USD and local); Book A tilt; Currencies; Equities; Base Rates. Flow-side confirmation from SR-26's `calc.us_foreign_net_12m`.

**Mechanism.** Two objects: the absolute line at all-time highs in USD and the relative line at a 25-year low with a one-year uptick — the 2010–24 relative bear was US outperformance, not EM decline. The relative cycle is the equity expression of the dollar cycle: every completed turn (1988, 1994, 2001, 2010) sat within about a year of a dollar turn; 2016–18 is the instructive false start. Operational version: stay tilted while the dollar-down regime holds, exit on the flip; the decadal framing is unfalsifiable at its own horizon. Composition contaminates the evidence: Taiwan, Korea and China tech are roughly 40% of MSCI EM, so the absolute breakout is substantially the AI-semis trade — decomposition needed (USD vs. local; EM ex-China alongside; semis share noted). Callum Thomas's "neutral" is recorded as a pattern, not a call: valuation and positioning signals fade early in regime trades; only the trend flag closes the tilt. SR-4's devaluation tell is the kill switch (2015 precedent).

**Data.** MSCI end-of-month levels, free (EM from Dec 1987, World from 1969; USD and local) — quarterly `manual_input`; daily proxies via yfinance (EEM/VWO, ACWX, EMXC from 2017); real broad dollar index (`fred.dxy` is the nominal broad index — add the real index, DTWEXBGS vs. RTWEXBGS, G-12). *Lives in:* `manual.msci_*`, `yfinance.mkt_eem` etc.; `calc.em_rel`, `calc.em_rel_flag`, `calc.em_fx_contrib`, `calc.emxc_rel`.

**Rights.** Narrow flag (relative trend break: 12m EM/World relative return > 0 and ratio above its 24m average); Book A tilt modifier conditioned on the dollar regime tag; SR-4 tell as exit.

**Validation gate.** Episodes: 1988, 2001, 2016 (false), 2024. Statistic: forward 36m EM/World relative return after the flag fires, split by real-dollar 12m change sign. Pass: the dollar cell discriminates (2016 in the dollar-up failure cell). If not, flag only. Falsifier for the current instance: the turn proceeds with a flat or strong dollar — then it is the AI trade and the tilt earns no credit. Offline (ST-8).
### SR-15 Cross-asset valuation z-scores — gold, S&P 500, Treasuries, commodities (Topdown Charts / LSEG, 1994–, 24 Sep 2026) — Thread A

**Ruling.** Adopt as a Monthly cross-asset valuation strip and a Book A rebalancing modifier; reject "cheap commodities" — the chart shows them at zero, average. No T&B change.

**Home.** Monthly Cheap-and-Unloved block (§2.4); Portfolio Construction (rebalancing rule; A-3 input); Metals (gold window fragility); Base Rates.

**Mechanism.** The value is the common scale: four assets on one z-axis lets Book A rank diversifiers instead of judging each alone, and SR-12's barbell needs exactly this to pick and size legs. Read correctly: gold rich (+1.7 after a +2.9 spike), stocks moderately rich (+1), Treasuries cheap (−0.8), commodities average — commodities are cheap only relative to gold and stocks, and the commodity/gold ratio at multi-decade lows is the cleaner object. Three cautions. Z-scores assume a stable anchor, and the four anchors differ in kind (cash flows, monetary reference, marginal cost). Gold is the problem child: a 1994-start window treats the official-sector bid as an anomaly when Factor V frames it as regime change — gold's z is reported with zero rebalancing weight while Factor V is active. The S&P at +1 vs. CAPE ~40 (nearer +2 on the same window) is model disagreement of the SR-6 kind — a confidence cross-check on the Valuation pillar, not a replacement. Magnitude for tilts, not timing: every asset has held above +1 for years at a stretch.

**Data.** Light house version, all free: CAPE plus ERP (Shiller, FRED); 10y real yield (`fred.tips_10y`, new) and ACM term premium; real gold vs. long trend (LBMA via Stooq/yfinance, CPI held); World Bank Pink Sheet commodity index vs. trend (monthly since 1960 — extends past 1994). Expanding-window z-scores only, through `derived_forms`. Full four-metric composites deferred (Appendix C). *Lives in:* `calc.val_z_gold/_spx/_ust/_cmdty`, `calc.cmdty_gold_ratio`.

**Rights.** Book A rebalancing modifier (tilt toward the lowest-z diversifier, sized by |z|, gated by `rates.driver`); confidence modifier on the Valuation pillar.

**Validation gate.** Cross-asset rank test — forward 3y real return of the cheapest-tercile asset vs. the richest, paired by date; per-asset forward 3y/5y real returns conditional on z > +1.5 and z < −1. Pass: cheap beats rich in ≥2/3 of paired observations. Window-fragility test on gold: if its conclusion flips between 1971-start and 1994-start windows, gold drops to base-rate rights only. Falsifier: an anchor-shift regime in which "expensive" persists for a decade. Offline (ST-7).

### SR-16 Hyperscaler debt supply and AI credit absorption (Bloomberg chart via Lemand, 24 Sep 2026) — Thread E (supply side of Thread R)

**Ruling.** Adopt as a Factor I funding panel with one narrow flag; reject the headline ("four companies borrowed more in nine months than fifteen years") as a signal. No T&B input yet.

**Home.** Disruptive Themes Factor I evidence log (human-gated); Monthly Duration Absorption block (supply side, §2.1.2); Credit; Equities (rings chapter); Debt Cycles brief (analog set).

**Mechanism.** The transition from self-funded to debt-funded capex is the classic late-stage marker of a capex boom (telecom 1998–2001, shale 2012–15, merchant power 2000–02). The post's real evidence is absorption, not issuance: new-issue concessions 2→12 bp, cover 3.2×→2.5×, 78 of 91 bonds wider than launch — the marginal buyer charging. Two objects the panel keeps apart: the hyperscaler unsecured leg, where solvency is not the question (≈1.8× leverage) and the signal is price (concession, spread, long-end appetite); and rings 2–3 (neocloud HY, GPU-backed ABS, SPV/private-credit and vendor financing), where the signal is default risk and where marginal financing has migrated. The mechanism variable is free and quarterly: aggregate self-funding ratio (operating cash flow ÷ capex) for AMZN, GOOGL, MSFT, META, ORCL, with net debt change — below 1 for two quarters is the regime line. The long-end supply share (42% of 15y+ issuance) is the bridge to SR-23. One daily tell falls out of the quality mix: hyperscalers are AA-class and a fifth of supply, so AA OAS widening relative to BBB (quality unchanged, supply changed) reads as supply pressure. A hike into this (SR-21) is the 1999–2000 sequence; this panel deteriorates first.

**Data.** yfinance quarterly cash-flow statements (free); ICE BofA AA and BBB OAS via FRED (new — IG/HY/BB/CCC are held, AA and BBB are not); SIFMA issuance by maturity (monthly); NIC/cover figures are Bloomberg-only — `manual_input` quarterly, three numbers. *Lives in:* `yfinance.fund_*`, `fred.aa_oas`, `fred.bbb_oas`, `sifma.*`; `calc.self_fund_ratio`, `calc.hs_netdebt_12m`, `calc.aa_bbb_oas_diff`, `calc.ai_long_share`.

**Rights.** Narrow flag: self-funding ratio < 1 for two quarters, or AA–BBB differential compressing past a gate-set threshold → Factor I refresh input (human-gated). Ring-3 HY spreads as a HY Spread Acceleration overlay candidate only after gate (§2.6).

**Validation gate.** Episodes: telecom, shale, merchant power. Statistic: lead time from (a) sector self-funding < 1 and (b) NIC/cover deterioration to the sector's equity relative peak and to its spread blowout. Pass: (a) or (b) led the equity peak by 6–24 months in ≥2 of 3. Falsifier: AI revenue catch-up returns the ratio above 1 by 2027.

### SR-17 Real-yield-led bond selloff, breakevens falling (Alpine Macro via Chen Zhao, 24 Sep 2026) — Thread R

**Ruling.** No new analysis — SR-6's block reading a live print. **Merged into `rates.driver`**: the DKW real-side decomposition (expected real short rate, real term premium, TIPS liquidity premium — Fed Board, monthly, free) is the fourth term-premium model and the sign arbiter when Kim–Wright and ACM disagree; the growth / Fed-path / term-premium distinction is the cell rule of §2.1.1.

**Mechanism (kept for the register).** "Real, not inflation" is half the attribution. Real yields rise for three reasons with opposite equity implications: growth (benign, correlation negative), Fed path (hawkish, correlation positive), real term premium (supply/fiscal — SR-23's channel, correlation positive). Breakevens falling while oil rises is anchored expectations — which makes 10y TIPS near 2.75% the SR-12 buy case if the term-premium cell drives, and a wait-for-the-pivot case if it is the Fed-path cell. Gold holding at these real yields is the Factor V scorecard metric (gold-vs-TIPS residual, already in Metals).

**Data.** Fed Board DKW output (monthly Excel). *Lives in:* `dkw.real_expected_path`, `dkw.real_term_premium`, `dkw.tips_liquidity`.

**Rights.** None new. **Validation.** Rides on SR-6's ledger; adds a four-episode calibration table (2013, Q4 2018, 2022, H2 2023) of forward 6m equity outcomes by cell — base rate only.

### SR-18 Global visible oil inventories vs. operational floor (JPM via Bloomberg; Brimberg 15 Sep, Monchau) — Thread C

**Ruling.** Adopt the mechanism (physical buffer state as a Factor III / Energy input); reject the chart as a current reading — §1.5 fixture.

**Home.** Monthly Factor III / Energy panel; Energy (buffer-market frame — this is the buffer variable); tail register (Hormuz).

**Mechanism.** The actual series on the chart ends around April 2026 (~8.0 bn bbl); the orange segment is JPM's June-published projection "assuming no resolution in June" with 5.6 mb/d of demand destruction. Tankers were transiting Hormuz by June 24 and WTI fell below $70, so "6.8 by September" is a counterfactual path, circulated on 15 Sep as "free fall." The mechanism is live again and the stack lacks it: price (`fred.wti`, `fred.brent` — held) conflates risk premium with physical tightness; inventory relative to the operational floor decides whether a second disruption spikes or shrugs. As of 25 Sep the strait is not fully open (Iran conditioning full reopening), product flows lag, and Brent $106.6 vs. WTI $94.5 — a $12 spread — is the tell: seaborne risk premium, not US physical tightness. The current level is required and is not on the chart.

**Data.** EIA weekly US stocks (free); IEA OMR OECD days-of-cover (monthly headline, `manual_input`); JODI non-OECD (free, 2-month lag); global-visible figure monthly `manual_input`; Brent–WTI from held series; prompt time-spreads via yfinance/CME (G-11). *Lives in:* `eia.crude_stocks`, `eia.product_stocks`, `manual.oecd_days_cover`, `manual.global_visible_stocks`; `calc.oil_buffer_state`, `calc.brent_wti`, `calc.oil_prompt_spread`.

**Rights.** Narrow flag (buffer above / at / below stress level) into Factor III; tail-register modifier for the Hormuz scenario.

**Validation gate.** Episodes: 1990, 2008, 2022. Statistic: forward 6m price change conditional on days-of-cover bottom decile × disruption event vs. none. Falsifier: demand destruction rebuilds stocks faster than the floor (2008 H2).

### SR-19 "3-month / 1-year beta" chart (Monchau, undated crop) — Thread E

**Ruling.** DEFERRED — definition required (§1.6 fixture). The 0–45% scale and the "3-month daily / 1-year weekly" labels rule out a plain market beta; the spike pattern (1994, 1999–2001, 2018, 2020, 2024–26) is the signature of a one-factor market. Two readings, two homes: index beta/R² to the AI cohort or momentum → Concentration & Complacency overlay; index beta to yields → `rates.driver`'s correlation member, already covered. Timing lesson either way: the 1-year line peaked in 2001, after the top; a 63-day window is dominated by a handful of AI days — fragility state, not timing signal. House version in Appendix C. **Action:** register entry `DEFERRED — definition required`; request the full post text.

### SR-20 IMF COFER Q1 2026 and the reserve-composition tracker (FintechNews infographic; extension, 25 Sep 2026) — Thread X

**Ruling.** Adopt as the Factor V scorecard of §1.9; reject the level as a signal in either direction.

**Home.** Disruptive Themes Factor V (scoreable input); Currencies; Duration Absorption block, absorber side (§2.1.2), through the shared `tic.*` family.

**Mechanism.** USD 57.1% (≈$7.5 tn of ≈$13.1 tn allocated) is near the post-1995 low (~71% in 2000, ~65% in 2015), but two things matter more than the level. The share is valuation-distorted — a weaker dollar mechanically lowers it; the ECB's constant-exchange-rate series shows slower, steadier erosion. And COFER excludes gold, which is where the shift is going: at market value official gold now rivals euro reserves, so the dollar's share of total reserves including gold is well below 57% and falling faster than the table shows — Factor V's official gold bid seen from the other side. Two narrative falsifiers sit in the table: CNY at 1.99%, down from ~2.8% in 2022, kills "RMB replacing the dollar" and supports SR-3/4 (funding currency, not reserve currency); growth is in CAD/AUD/other (~11% vs. ~2% in 2000) — diversification into liquid high-yielding sovereigns, a different story from de-dollarization. Base rate for expectations: sterling's displacement took roughly thirty years and two devaluations; the dollar's own share went from ~85% in the 1970s to the mid-40s by 1990 and back to 71% by 2000. Shares move ~1 pp/year on trend and by step at regime events; the tracker's job is regime classification once a year, not forecasting a number.

**Regimes and signposts.**

| Regime | Reads as | Signposts |
|---|---|---|
| Slow diversification (base) | Constant-FX USD share drifting down < 1 pp/yr; gains to CAD/AUD/KRW and gold | Nothing changes — that is the point |
| Sanctions-driven fragmentation | Gold share accelerating past ~25% of total reserves; CNY rising in *trade* settlement (SWIFT/CIPS, invoicing) while its *reserve* share stays flat (the SR-3/4 pattern) | A new large asset freeze; a major Gulf or Asian holder publicly shifting |
| Dollar re-consolidation | Official holdings falling while private foreign holdings and stablecoin T-bill float rise — the absorber changes, the currency doesn't | Stablecoin issuers as a new private absorber (already Factor V); crisis dollar demand |

**Data.** COFER quarterly (`manual_input`, ~3-month lag); WGC central-bank holdings and net purchases (monthly, new source); ECB constant-FX series (annual, `manual_input`); TIC official vs. private holdings (`tic.*`). *Lives in:* `manual.cofer_*`, `wgc.cb_gold_*`, `tic.official_holdings`, `tic.private_holdings`; `calc.cb_gold_12m`, `calc.tic_official_12m`, `calc.tic_private_12m`.

**Rights.** None. Scorecard; SR-23 absorber-side input.

**Disposition.** Annual by hand (three numbers plus the holder split, ≈30 min at each DT refresh); monthly proxies automated in ST-2/ST-4. G-13: whether Factor V already carries the gold-share line.

### SR-21 October 28 FOMC hike probability 70–77% (Bianco Research / Bloomberg WIRP, 24 Sep 2026) — Thread R

**Ruling.** The probability itself is presumed already read in the Daily (G-4); adopt the derived object — the Fed–market gap — plus a Warsh-matrix scenario and a prediction-market disagreement case. Reject the political framing as mechanism.

**Home.** Daily 07:00 (FOMC weeks, ST-10); Sunday anchor; Rate machine; Warsh matrix (§2.1.5); the prediction-market spec's disagreement layer.

**Mechanism.** What is new is the configuration: a market pricing a hike against a Fed that has been easing, under a chair whose appointer wants cuts, a week before midterms. Three encodable consequences. (1) The gap between the market-implied path and the Fed's signalled path is a credibility variable with two branches: refuse, and the long end reprices through term premium (Bianco's "off the top of the page"; the `term_premium` cell; gauged by SR-24's flag); concede, and the curve bear-flattens then the `fed_path` cell resolves — 1994→1995, when hikes crushed bonds and the credibility they bought made 1995 the best bond year in a generation. Bianco prices only the first branch. (2) Sequencing with SR-16: a hike into debt-financed capex is the 1999–2000 sequence; SR-16's absorption metrics deteriorate first. (3) Kalshi's Fed-decision market vs. FedWatch on the same meeting is the cleanest test the disagreement layer will get. Base-rate note: "long yields rose during an easing cycle for the first time in 50+ years" was already true by January 2025; the useful base rate is what the long end did after the Fed conceded to market pricing (1994, 2022) vs. refused — into SR-7's table by hand.

**Data.** CME FedWatch (by hand until a free source is settled, G-4); fed funds futures via a free source; Kalshi Fed markets once PM-1 lands; SEP dots (`manual_input`, quarterly). *Lives in:* `manual.fedwatch_*`, `manual.sep_median_*`, later `kalshi.fed_*`; `calc.fed_mkt_gap_m1/_m2/_12m`, `CRED_STRESS`, `calc.pm_disagree_fed`.

**Rights.** Derived metric; narrow flag "policy-credibility stress" (≥60% of a move priced against the last signalled direction at the next meeting, or 12m gap > 50 bp); Warsh-matrix scenario ruling; PM disagreement record. No Book rights.

**Validation gate.** Episodes of ≥50 bp divergence within 3 months (1994, 1998, 2007, 2013, 2018, 2022, 2024). Statistic: forward 3m 10y change and equity return split by conceded / refused. Pass: the split separates the long-end outcome. First live test: 28 Oct 2026. Offline (ST-7).

### SR-22 5-year auction at 5.033%, TLT record low, "meltdown" (Padley, 24 Sep 2026) — Thread R

**Ruling.** Adopt auction-absorption metrics — the one usable object in the post; reject the meltdown and cash-stance framing; add a Doctrine note that an ETF's record low is arithmetic.

**Home.** Daily 07:00 (auction days, ST-10); Monthly Duration Absorption block (price side); T&B Liquidity & Funding Stress overlay — **queue position #2** (§2.6); Book A rule A-3 (input); Operating Doctrine (note).

**Mechanism.** A 5-year at 5.03% with funds at 3.75–4.00% and a hike priced is the `fed_path` cell printed on a coupon — the same event as SR-17/21, not a new one. Ten basis points across global 10-years is a bad day, not a meltdown. TLT −50% from 2020 is what ~16 years of duration does when yields go from 1% to 5%; RSI 33 weekly is not oversold. The usable object hides behind "demand wasn't good": tail vs. when-issued, bid-to-cover, and dealer/direct/indirect takedown — free per auction, and the high-frequency symptom of SR-23's gap and SR-16's concessions. The base rate cuts against the post: the worst auctions of the last cycle (the 5 bp 30-year tail, Nov 2023) marked the top in yields, because a bad auction is the moment price-sensitive buyers finally get paid. The candidate flag is therefore a contrarian bottom-in-bonds tell, to be tested — and for Book A it is A-3's missing trigger.

**Data.** TreasuryDirect auction results API (free, per auction; `available_at` 13:00 ET auction day). Note: the registry's existing `ibkr.auction_*` keys are the equity closing auction; the new family is `auction.*` (Treasury). *Lives in:* `altdata/sources/treasury_auctions.py`; `auction.tail_bp`, `auction.bid_to_cover`, `auction.dealer_share`; `ABS_STRESS`.

**Rights.** Narrow flag "absorption stress" (tail ≥2 bp on two consecutive coupon auctions, or dealer takedown >20%) → overlay queue #2 after gate; A-3 input after gate.

**Validation gate.** ~1,000 coupon auctions 2009–2026; forward 1m and 3m 10y change conditional on top-decile tails. Pass for the contrarian read: median forward 3m change negative with ≥60% hit rate. Otherwise stress flag only. Offline (ST-7).

**Doctrine note (by hand).** Drawdown of a constant-duration fund is yield arithmetic; a "record low" in price is not a level that means anything. Candidate rule, not a rule.

### SR-23 G4 issuance gap vs. real yields (Lustig, corr 0.71, 24 Sep 2026) — Thread R

**Ruling.** Adopt — the highest-value item in either batch. It is the causal variable for the `term_premium` cell that the DKW split only measures, and it can be projected a year ahead.

**Home.** Monthly Duration Absorption block (supply side); Factor IV panel; Rate machine; Portfolio Construction (A-3's exit condition); Debt Cycles brief (supply regimes).

**Mechanism.** Net duration supply to price-sensitive private hands (issuance minus central-bank net purchases) is the preferred-habitat driver of the real term premium; G4 net supply at ≈7% of combined GDP is the highest since 2010 and the average 10y real yield has followed (−1.4% in 2020 to ≈+1.0% in 2025). Three cautions, one extension. The correlation is 16 annual points with both series trending on the QE regime — half of it is one dummy, so the test needs the pre-2008 sample and a funds-rate control (2019 is the tell: gap up, real yields down, because the Fed cut). It is projectable: CBO deficits plus announced QT paths give next year's bar before it prints — the only leading input in either batch. The extension is SR-16: AI-related IG long paper is additional supply competing for the same buyers. SR-20, SR-26 and SR-27 are the absorber-side symptoms; SR-22 the price-side symptom.

**Data.** US monthly house version, all free: Treasury net marketable issuance (Fiscal Data API, MSPD — field mapping G-14), Fed SOMA Treasury holdings (TREAST, new), nominal GDP (new); targets `fred.tips_10y` and ACM; CBO baseline as `manual_input`; SIFMA for IG issuance by maturity. G4 version annually by hand from Lustig's substack, cited. *Lives in:* `fiscaldata.mspd_*`, `fred.soma_treasuries`, `fred.gdp_nominal`, `manual.cbo_deficit_path`; `calc.net_supply_12m_gdp`, `calc.net_supply_proj_12m`, `calc.priv_residual_12m`.

**Rights.** Confidence modifier on the `rates.driver` cell assignment; Factor IV panel input; Book A duration-timing modifier via the projection, with refunding announcements as Daily events (`events.scheduled` already exists in the registry).

**Validation gate.** 2003–2026 monthly; regress the 12m change in ACM term premium (and `fred.tips_10y`) on the 12m change in net supply/GDP with a funds-rate-path control. Pass: positive, significant coefficient in both pre- and post-2008 subsamples. If only post-2008 → descriptive, no modifier. Falsifier: 2010–13 consistent; 2018–19 inconsistent without the Fed control. Offline (ST-7).

### SR-24 5y5y forward breakeven vs. MSCI World Commodity Producers (Costa / Azuria Capital, chart as of 12 Sep 2026) — Thread R

**Ruling.** Adopt a defined inflation-expectations de-anchoring flag as a rider on `rates.driver` and SR-21; reject the hand-drawn trendline breakout as a rule (the SR-1 lesson: three touches on a chosen axis) and the commodity-producers index as an expectations lead.

**Home.** Rate machine (breakeven anchoring); Factor IV; Warsh matrix (consequence gauge for the SR-21 "refuse" branch); Debt Cycles brief (fiscal-dominance lens, already carried); Energy and Metals (producers-vs-spot note).

**Mechanism.** The observation underneath is real and the stack has no defined version of it: 5y5y forward breakevens have made lower highs for twenty years (≈3.0% 2005, ≈2.9% 2011, ≈2.65% 2022). That sequence is Fed credibility as the market prices it, and a break above the 2022 high would be the first de-anchoring event of the TIPS era. The chart is dated 12 Sep with 5y5y at 2.31% "on the verge"; SR-17's chart shows the sequel — it failed at the line and fell toward 2.25% by 23 Sep while oil surged. The right wiring: the de-anchoring flag is what the "refuse" branch costs, and it feeds the inflation-risk-premium component of the `term_premium` cell. The producers index at an all-time high (8,114, above the 2008 and 2011 peaks) is a different object: substantially gold miners plus energy on a USD net-return basis, re-rating on scarcity and capex discipline, not a forecast of breakevens. The producers-vs-spot ratio at a high is a capital-cycle note (the market paying for discipline; 2011 shows what follows) — base rate for Energy and Metals. Costa's "policymakers pushed toward more inflation" is the fiscal-dominance thesis the Debt Cycles brief treats as one lens among several; his conclusion is his book (§1.3). Honest limit: there is no completed de-anchoring episode in market data since 2003, so the flag cannot be gated — its meaning comes from 1965–80 via the Livingston survey, and it carries definition-only rights.

**Flag definition.** `DEANCHOR` = `fred.breakeven_5y5y` above its 2022 high (≈2.65%, verify at build) for 20 consecutive sessions, confirmed by either the Fed Board's Common Inflation Expectations index above its 2022 high or UMich 5–10y expectations ≥3.5% for three consecutive months. Rendered with `calc.be5y5y_range_pos`.

**Data.** `fred.breakeven_5y5y` (held); Fed Board CIE (quarterly, new source); UMich 5–10y (monthly, new); NY Fed SCE 3y/5y (monthly, new); Livingston history (by hand, base rate); GUNR as the producers proxy (G-15). *Lives in:* `fedboard.cie`, `umich.expect_5_10y`, `nyfed.sce_*`; `DEANCHOR`, `calc.be5y5y_range_pos`, `calc.producers_spot_ratio`.

**Rights.** Narrow flag, definition only; Warsh-matrix consequence gauge. **Validation.** None possible on market data; Livingston 1965–80 base-rate note by hand.

### SR-25 Burry adding to AI shorts — Micron, Nebius, SOXX, Palantir (Monchau via Bull Theory, 24 Sep 2026) — Thread E

**Ruling.** Reject as a signal; adopt one memory-cycle tell from the evidence cited; record as a narrative-register entry graded "notable participant, low weight."

**Home.** Factor I evidence log (memory line); Equities (semiconductor fulcrum chapter, base-rate table); narrative register. No Daily or T&B surface.

**Mechanism.** Famous-investor positioning is low-information by construction: disclosures are lagged and partial, "in some size" is unquantified, and the public bearish calls since 2019 have marked local bottoms as often as tops; the cloning literature finds value in concentrated long-only managers at a 45-day lag, not in macro shorts. The information is in the evidence, not the position: the Acer CEO's comment that memory inventories are building while Chinese suppliers (CXMT, YMTC) add supply is the classic memory-downcycle trigger, and memory is the most cyclical part of the semiconductor fulcrum the Equities paper already treats as the AI trade's pivot — memory prices led SOX peaks by 0–2 quarters in 2000, 2008, 2018 and 2022. The nuance that decides whether the Micron short is right: the memory market is bifurcated — HBM (AI, supply-constrained, three producers) vs. commodity DRAM/NAND (consumer, where Chinese entry lands). Testable from filings: Micron inventory days and HBM revenue share, plus DRAM contract-price direction. The long list (QXO, Build-A-Bear, Sprouts, Birkenstock, MercadoLibre) is his book; no rights.

**Data.** MU quarterly balance sheet via yfinance (inventory ÷ COGS × 91 → inventory days; MU added to SR-16's fundamentals pull); HBM share (`manual_input`, quarterly); DRAM contract-price direction (`manual_input`, monthly). *Lives in:* `calc.mu_inv_days`, `manual.mu_hbm_share`, `manual.dram_dir`.

**Rights.** None. Base-rate table (memory downcycles 1996, 2001, 2008, 2011, 2018–19, 2022–23 → SOX peak lead) in Equities; quarterly line in the Factor I evidence log. Register entry records the rejection (R25).

### SR-26 TIC cross-border flows, 12 months through July 2026 — "foreign demand for U.S. debt collapsed 80%" (Riemann, 24 Sep 2026) — Threads X and R

**Ruling.** Adopt the composition read as the absorber-side detail of §2.1.2; reject the headline. Read whole, the same table shows net foreign acquisition of US long-term securities *rising* in the window (1,182.6 → 1,276.9 bn, +8%). What fell is the Treasury share of it.

**Home.** Monthly Duration Absorption block; Factor IV (external-financing composition); Currencies; Rate machine.

**Mechanism.** Private foreign net purchases of Treasury bonds and notes fell 506 → 263; official net selling slowed (−50 → −17); bills 251 → 49. But private foreign purchases of US equities rose 606 → 802, corporate bonds 305 → 392, agencies 127 → 142, and official accounts turned net buyers overall (−76 → +155) through equities (+140) and corporates (+60). Foreigners funded the US as much as before — through the equity market (largely the AI trade) and credit instead of Treasuries. Treasury share of net foreign long-term purchases: 39% → 19%. US residents meanwhile bought more foreign securities (−286 → −478): SR-14's US-vs-RoW turn in flow form. Three implications. (1) Treasury supply is landing on domestic price-sensitive buyers — SR-23's residual, now measurable from the same source. (2) The external financing mix has shifted from debt (sticky, price-insensitive) to equity (pro-cyclical): a US equity bear removes the marginal foreign funding just as Treasury supply peaks — the mechanism that links SR-13/SR-16 (the AI trade) to the `term_premium` cell and to the dollar. (3) Foreign bill demand fell as Treasury shifted issuance toward bills that MMFs and stablecoins absorb domestically (Factor V) — bills are not the constraint. TIC monthly flows are not seasonally adjusted, noisy, custodially biased and benchmark-revised; a single-row percentage change is not evidence (R26).

**Data.** TIC monthly cross-border flows table (free, ~6-week lag), first-print and revised vintages (G-8). *Lives in:* `tic.flow_*`; `calc.foreign_ust_share_lt`, `calc.foreign_eq_12m`, `calc.foreign_bill_12m`, `calc.us_foreign_net_12m`.

**Rights.** Absorber-fragility modifier on the block's read (after gate, jointly with SR-27); Factor IV panel input. No Book rights.

**Validation gate.** Episodes when the Treasury share of net foreign long-term purchases stayed below 25% for 12 months (check 2013–14, 2018–19, 2020–21); forward 12m change in ACM term premium and in the real broad dollar index. Small n; if no separation, descriptive line only.

### SR-27 TIC Major Foreign Holders — "who sold and who bought," 12-month change by reported holder, June 2025 to June 2026 (research note, Figure 3) — Threads X and R

**Ruling.** Adopt as the holder-level absorber panel (§2.1.2; layer 1 of §1.9); reject "China dumping Treasuries" as a signal without the custodial adjustment.

**Home.** Monthly Duration Absorption block; Factor V scorecard (holder split); Currencies; T&B Liquidity & Funding Stress overlay — **queue position #3** with SR-26 (§2.6).

**Mechanism.** The buyers are custodial and fund-management centres (UK +84, Belgium +52, Ireland +43, Luxembourg +31, Cayman +12) — private and often levered holders (basis-trade funds via Cayman, European asset managers via Ireland and Luxembourg) — plus Gulf and Asian financial centres (Singapore +31, UAE +18, Hong Kong +14, Saudi Arabia +12). The sellers are official reserve holders, for three different reasons the panel tags separately: reserve diversification (China −98 — though Euroclear in Belgium has historically custodied Chinese holdings, so the true China change is smaller than −98 and part of Belgium's +52 may be China); FX defense (India −41, Brazil −47 — reserves sold to defend the rupee and the real; SR-3's external-position mechanism, not de-dollarization); hedged-carry economics (Japan −38, Switzerland −16 — SR-2's `calc.jp_hedged_carry` turning negative stops Japanese hedged Treasury buying). Net: custodial/private ≈+220, official ≈−245 — roughly flat in total, but the marginal holder has changed from a central bank that holds to maturity to a levered fund that hedges and can unwind. That is the fragility the Liquidity & Funding Stress overlay is built to catch — March 2020 and April 2025 were basis-trade unwinds — and it is measurable.

**Data.** TIC Major Foreign Holders table (monthly, free; annual benchmark as a second vintage, G-8); TIC's official/private split. *Lives in:* `tic.holdings_by_country`, `tic.official_holdings`, `tic.private_holdings`; `calc.tic_official_share`, `calc.tic_custodial_share`, by-hand mechanism tags; `ABS_FRAGILITY` (candidate rule: Treasury share falling ∧ custodial share rising ∧ official share falling, 12m).

**Rights.** Absorber-fragility modifier with SR-26 (after gate); overlay queue #3 after gate; Factor V holder line (none).

**Validation gate.** Custodial share and official share versus the severity of Treasury liquidity events (Oct 2014 flash rally, Sep 2019 repo, Mar 2020, Apr 2025), severity measured by MOVE and dealer balance-sheet metrics. n = 4; base rate only unless the ordering is monotonic.

---
## §4 Consolidated data feeds

Held = among the 59 FRED series in `altdata/config.py` or the 27 yfinance symbols on 25 Sep 2026. Every new row is a timer-driven writer (30.4) with a registry entry; `manual_input` rows are operator-entered through the CLI with `available_at` stamped. All free.

| Feed | Source / module | Cadence | Held? | `available_at` / notes | Used by |
|---|---|---|---|---|---|
| DGS2, DGS10, DGS30, T10YIE, T5YIFR | `fred.*` | daily | **held** | — | R |
| DFII10 (`fred.tips_10y`) | FRED | daily | new | same day | SR-6, 15, 17, 23 |
| DGS5, DTB3 | FRED | daily | new | same day | SR-2 (3m leg), SR-22 |
| THREEFYTP10 (`fred.term_premium_kw`) | FRED | daily | new | same day | SR-6 |
| ACM term premium (`acm.*`) | NY Fed CSV, `altdata/sources/acm.py` | daily | new | same day | SR-6, 15, 23 |
| SF Fed Treasury Yield Premiums (`sffed.*`) | SF Fed data page | per publication | new | publication | SR-6 |
| DKW TIPS decomposition (`dkw.*`) | Fed Board Excel, `altdata/sources/dkw.py` | monthly | new | publication | SR-6/17, §2.1.1 |
| FEDFUNDS, USREC | FRED | monthly | new | publication | SR-7, 21, 23 |
| TREAST (`fred.soma_treasuries`), GDP nominal | FRED | weekly; quarterly | new | Thursday; publication | SR-23 |
| AA and BBB OAS (`fred.aa_oas`, `fred.bbb_oas`) | FRED (ICE BofA) | daily | new (IG/HY/BB/CCC held) | same day | SR-16 |
| TOTALSL, REVOLSL, NONREVSL (+ ALFRED vintages) | FRED/ALFRED | monthly | new | ~5-week lag; first prints | SR-5 |
| Real broad dollar index (RTWEXBGS) | FRED | monthly | new (nominal DTWEXBGS held) | publication | SR-14 (G-12) |
| Core CPI, CPI, PCE, sticky | `fred.*` | monthly | **held** | — | SR-9, 12 |
| WTI, Brent | `fred.wti`, `fred.brent` | daily | **held** | — | SR-18 |
| Treasury auction results (`auction.*`) | TreasuryDirect API, `altdata/sources/treasury_auctions.py` | per auction | new | 13:00 ET | SR-22 |
| MSPD net marketable issuance (`fiscaldata.*`) | Fiscal Data API | monthly | new | publication (G-14) | SR-23 |
| TIC family (`tic.holdings_by_country`, `tic.official_holdings`, `tic.private_holdings`, `tic.flow_*`) | US Treasury TIC, `altdata/sources/tic.py` | monthly + annual benchmark | new | ~6-week lag; both vintages (G-8) | SR-3, 20, 26, 27 |
| CFTC COT (JPY; USD index) | cftc.gov, `altdata/sources/cftc.py` | weekly | new (source switch exists, off) | Tuesday positions, Friday release | SR-2 |
| JGB yields daily; Japan 10y/3m monthly | MoF CSV; FRED | daily; monthly | new | same day; publication | SR-2 |
| USDJPY, USDCNY | `fred.usd_jpy`, `fred.usd_cny` (+ yfinance daily) | daily | **held** | — | SR-2, 4 |
| CNH=X; CNY central parity; CNH HIBOR | yfinance; CFETS; HK TMA | daily | new | same day; 09:15 Beijing | SR-3, 4 |
| China 10y (FRED monthly; ChinaBond daily) | FRED; ChinaBond | monthly; daily | new | publication | SR-4 |
| SAFE reserves; IIP; BoP | SAFE | monthly; quarterly | new | publication | SR-3 |
| WGC central-bank gold (`wgc.*`) | World Gold Council | monthly | new | publication | SR-20 |
| COFER; ECB constant-FX shares | IMF; ECB | quarterly; annual | `manual_input` | release | SR-20 |
| EIA weekly petroleum stocks (`eia.*`) | EIA (source switch exists, off) | weekly | new | Wed 10:30 ET | SR-18 |
| IEA days of cover; JODI; global-visible figure | IEA; JODI; published | monthly | `manual_input` / new | publication | SR-18 |
| Fed Board CIE; UMich 5–10y; NY Fed SCE | Fed Board; UMich; NY Fed | quarterly; monthly | new | publication | SR-24 |
| SEP median dots; FedWatch probabilities | Fed; CME | quarterly; daily | `manual_input` (G-4) | FOMC day; same day | SR-21 |
| Kalshi Fed markets | Kalshi API | daily | after PM-1 | same day | SR-21 |
| Z.1 household holdings; AAII allocations; ICI assets | FRED; AAII; ICI | quarterly; monthly | new; `manual_input`; new | publication | SR-12 |
| Shiller CAPE / ERP inputs | Yale | monthly | new | publication | SR-7, 15 |
| LBMA gold; World Bank Pink Sheet | Stooq/yfinance; World Bank | daily; monthly | new | publication | SR-15, 24 |
| Ken French industry portfolios, HML | Ken French library | annual/monthly | new | file date; log vintage | SR-1, 13 |
| Damodaran industry multiples | NYU | annual | new | file date | SR-13 |
| MSCI EM / World / ACWI ex-US (USD, local) | MSCI end-of-month | monthly | `manual_input`, quarterly file | publication | SR-14 |
| IVW, IVE, IWF, IWD; EEM, VWO, ACWX, EMXC; GUNR; GLD | yfinance | daily | new symbols (sector ETFs, SPY, QQQ, IWM held) | same day | SR-1, 14, 15, 24 |
| Quarterly fundamentals: AMZN, GOOGL, MSFT, META, ORCL, MU | yfinance | quarterly | new | filing date | SR-16, 25 |
| SIFMA corporate issuance by maturity | SIFMA | monthly | new | publication | SR-16, 23 |
| FINRA margin debt; leveraged-ETF AUM | FINRA; issuer files | monthly; daily | new | ~3-week lag; same day | SR-8 |
| FINRA short interest; breadth; VIX term structure; sector ETFs | registry | — | **held** (`finra.*`, `calc.breadth_*`, `calc.vix3m_over_vix`, `cfe.vx*`) | — | SR-8, 5, 13 |
| NIC / cover; HBM share; DRAM direction; CBO deficit path; Livingston; G4 gap | press; MU release; TrendForce; CBO; Phila. Fed; Lustig | quarterly / monthly / annual | `manual_input` | entry date | SR-16, 25, 23, 24 |
| PRL price, market cap, 24h volume, circulating, tickers (`coingecko.pearl_*`) | CoinGecko `pearl-2`, Demo key from env; `altdata/sources/coingecko.py` (existing switch, off → on) | weekly + daily close | new (switch exists) | fetch time; inside the free tier | SR-10 |
| PRL height, difficulty, last block time (`pearl.chain_*`) | explorer.pearlresearch.ai, `altdata/sources/pearl_explorer.py` | weekly | new | fetch time; ESTIMATED marker on fallback (G-26) | SR-10 |
| PRL pool composition | pool dashboards | weekly | `manual_input` / NOT AVAILABLE (G-27) | entry date | SR-10 (S4) |
| PRL narrative signposts S1, S2, S7, S8 | scan output, `manual_input` | weekly | `manual_input` | entry date | SR-10 |
| Mechanism-scan candidates | `config/story_queries.yaml` (`mechanism_watch` group) via `news.py`; CoinGecko recently-added; hashrate.no; Kryptex | weekly | new (news pipeline exists) | fetch time | SR-10 (MW-5) |

---

## §5 Consolidated derived metrics — and where each lives

| Kind | Lives in | Metrics |
|---|---|---|
| Object sub-state | `config/market_state.yaml`, `regime.py` | `rates.driver` (cells, members, persistence, trace) |
| Object members (features) | `altdata/market_features.py` → `calc.*` | `calc.attr_real_share_20d`, `calc.attr_curve_share_20d`, `calc.corr_spy_tlt_60d`, `calc.infl_vol` |
| Candidate contradiction rows (declared, no rights) | `config/market_state.yaml`, `contradictions.py` | `carry_vs_vol` (SR-2), `fix_vs_offshore` (SR-4) (G-10) |
| Duration Absorption features | `calc.*` | `calc.net_supply_12m_gdp`, `calc.net_supply_proj_12m`, `calc.priv_residual_12m`, `calc.foreign_ust_share_lt`, `calc.foreign_eq_12m`, `calc.foreign_bill_12m`, `calc.us_foreign_net_12m`, `calc.tic_official_share`, `calc.tic_custodial_share`, `calc.tic_official_12m`, `calc.tic_private_12m`, `calc.cb_gold_12m`, `calc.aa_bbb_oas_diff`, `calc.ai_long_share`, `calc.self_fund_ratio`, `calc.hs_netdebt_12m`, `calc.mu_inv_days` |
| Rates flags | `calc.*` boolean series with trace | `ABS_STRESS` (SR-22), `ABS_FRAGILITY` (SR-26/27, candidate), `CRED_STRESS` (SR-21), `DEANCHOR` (SR-24), `calc.fed_mkt_gap_m1/_m2/_12m`, `calc.pm_disagree_fed`, `calc.be5y5y_range_pos` |
| Funding-currency features and tells | `calc.*` | `calc.jp_front_diff`, `calc.jp_front_diff_60d`, `calc.jpy_pos_z`, `calc.jp_hedged_carry`, `calc.jpy_unwind`, `calc.cny_fix_dev`, `calc.cnh_cny_gap`, `calc.uscn_10y_spread`, `calc.deval_tell` |
| Style / EM / consumer features | `calc.*` | `calc.gv_z`, `calc.gv_break`, `calc.techdef_spread`, `calc.def_z[…]`, `calc.em_rel`, `calc.em_rel_flag`, `calc.em_fx_contrib`, `calc.emxc_rel`, `calc.cc_z`, `calc.cons_rs` |
| Book A block features | `calc.*` via `derived_forms` | `calc.bond_alloc`, `calc.bond_cash_split`, `calc.val_z_gold/_spx/_ust/_cmdty`, `calc.cmdty_gold_ratio` |
| Oil buffer | `calc.*` | `calc.oil_buffer_state`, `calc.brent_wti`, `calc.oil_prompt_spread`, `calc.producers_spot_ratio` |
| SR-8 audit outputs | `docs/ledgers/`, then T&B config at ST-11 | confirmation-set scores; `BREADTH_thrust`, `VIX_TS`, `HY_conf`, `RETEST`, `MARGIN_z`, `LEVETF_AUM`, `SI_z` (SI and VIX TS from held keys) |
| Mechanism Watch (SR-10) | `calc.*` with trace; `mechanism_watch` store table | `calc.prl_supply_code` (D1), `calc.prl_overhang` (D2), `calc.prl_supply_gap` (D3), `calc.prl_emission_to_volume` (D4), `calc.prl_venue_conc` (D5), `calc.prl_idle_gpu_flag` (D6), `calc.prl_thesis_status` (rule of 2.7.5, informational label, not an object state); register rows with status |
| Report-layer only (no series) | Monthly renderers | block layouts, met/unmet marks, scorecard tables |

---

## §6 Rights ledger (unified)

All entries REPORT_OK-class. None can raise DECISION_BLOCKED. Overlay promotion follows the §2.6 queue.

| Name | Class | Home | Promotion path |
|---|---|---|---|
| `rates.driver` | Object sub-state (regime tag) | Market-state object; every reader | Feeds RRV tag at T&B full (G-7); never a composite input |
| Attribution regime modifier (SR-6) | Confidence modifier | T&B valuation-compression channel (at T&B full) | None |
| Correlation member / hedge rule A-1 (SR-9) | Confidence modifier | Book A hedge mix | None |
| Style regime flag (SR-1) | Narrow flag (after gate) | Monthly; Sunday (Book B) | Overlay input only if it adds information beyond top-10 weight |
| Tech/defensives tilt (SR-13) | Modifier (after SR-1 gate) | Book A tilt | None |
| Yen carry flag (SR-2) | Narrow flag | Monthly; Daily 07:00; 12:30 on unwind tell | Liquidity & Funding Stress queue #1 |
| Devaluation tell (SR-4) | Narrow flag | China panel; Sunday; 12:30 | Stays a tell; SR-14's exit |
| EM relative trend flag (SR-14) | Narrow flag (after gate) | Monthly Factor IV; Sunday (Book A) | Stays a flag |
| Consumer-credit bull (SR-5) | Trigger candidate | T&B bottom side | After SR-5 gate and SR-8 gate, at T&B full |
| Consumer-credit bear; RS tell (SR-5) | Modifier; narrow flag | Monthly consumer pillar; Sunday (Book B) | None |
| Bear-regime bottom gate / rule A-2 (SR-8) | Gate | T&B bottom side; Book A | Active at T&B full once the audit selects elements |
| Bond-allocation modifier (SR-12) | Modifier (after gate) | Book A; Cheap-and-Unloved block | A-3 input |
| Cross-asset rebalancing modifier; Valuation cross-check (SR-15) | Modifier (after gate); modifier | Book A; Monthly Valuation note | Gold zero-weighted while Factor V active |
| Hyperscaler funding flag (SR-16) | Narrow flag | Factor I evidence log (human-gated); block | Ring-3 HY → HY Spread Acceleration after gate |
| Oil buffer flag (SR-18) | Narrow flag | Monthly Factor III; tail register | Stays a flag |
| Reserve scorecard (SR-20) | None | Factor V | None |
| Policy-credibility stress `CRED_STRESS` (SR-21) | Narrow flag | Daily 07:00 (FOMC weeks); Sunday | Stays a flag; Warsh cell |
| Absorption stress `ABS_STRESS` (SR-22) | Narrow flag | Daily 07:00 (auction days); block | Queue #2; A-3 input after gate |
| Net-supply modifier (SR-23) | Confidence modifier | `rates.driver` cell assignment; Factor IV | A-3 exit condition after gate |
| De-anchoring `DEANCHOR` (SR-24) | Narrow flag (definition only) | Rate machine summary; Warsh gauge | No gate available |
| Memory-cycle line (SR-25) | None (base rate) | Factor I evidence log; Equities | None |
| Absorber fragility `ABS_FRAGILITY` (SR-26/27) | Modifier (after gate) | Block read; Factor IV | Queue #3 |
| Book A duration trigger A-3 | Candidate | Sunday (Book A) | Live only after SR-12 and SR-22 gates; champion/challenger |
| Idle-GPU flag D6 (SR-10) | Narrow flag | Sunday Mechanism Watch block; Monthly, under Factor I | Stays a flag; thresholds reviewed Jan 2027 |
| PRL thesis status; narrative-register entries (Factor I/V) (SR-10) | Informational label; graded narrative entries | Sunday block; Monthly part | None; theme text stays human-written |
| Mechanism-watch candidates (SR-10) | Register status CANDIDATE | `mechanism_watch` table; Monthly part | Human PROMOTE / REJECT only (MW-6) |

---

## §7 Report template edit map

Each surface is edited once, in the session that owns it. Surfaces that do not yet exist in the repo are marked with the Track D step they wait for.

| Surface | Additions | Session |
|---|---|---|
| Market-state object (`config/market_state.yaml`, `regime.py`, `validate_regime.py`) | `rates.driver` sub-state with members and persistence; candidate contradiction rows `carry_vs_vol`, `fix_vs_offshore` (declared, report-only) | ST-3, ST-5 |
| Monthly Macro Report (built) | Duration Absorption block (≤18 lines); Cheap-and-Unloved block (≤10 lines); Rate machine summary (`rates.driver`, `DEANCHOR` status, `CRED_STRESS`); Factor I funding panel (SR-16, SR-25 line); Factor III buffer line (SR-18); Factor IV: yen stack status (SR-2), US-vs-RoW lines (SR-14, display only until gate), external-financing composition (SR-26); Factor V reserve scorecard line (SR-20); China panel status lines (SR-3/4 inputs, assembly deferred); consumer/credit tilt line (SR-5, after gate); hiking-cycle note while a cycle is active (SR-7); **Digital Asset Mechanism Watch part (2.7.6) inside the digital-assets material (SR-10)**. No composite changes. | ST-6 (+ST-8 panels after gates); ST-14 for the Mechanism Watch part |
| Instrument table (`register/instruments.py`, the Security Master) | `crypto.watch` class; PRL entry with the MW-1 fields; loader test rejecting ticker keys | ST-13 |
| `config/story_queries.yaml` | `mechanism_watch` query group (2.7.7), committed and dated ahead of the first run | ST-15 |
| Narrative register | Mechanism-watch entries (`class=mechanism-watch`, factor I or V, graded) | ST-15 |
| Alternative Asset dashboard, Surveillance tab | PRL as a watch instrument until the fold (MW-3c, G-6) | ST-14 |
| Daily Cascade 07:00 anchor (exists; block builders at D4) | Auction line on coupon-auction days (SR-22); Fed–market gap line in FOMC and refunding weeks (SR-21/23); yen carry flag (SR-2); "rally inside bear" flag (SR-8, after audit) | ST-10, after D4 |
| Daily 12:30 alert-only (D4) | Yen unwind tell intraday (SR-2); devaluation tell trip (SR-4); a PRL tier-1 listing or chain incident as an information line only (MW-3d). Nothing else. Grep gate: no other Daily output contains "PRL" or "Pearl". | ST-10 |
| Sunday 05:00 anchor (D6) | One line: `rates.driver` + `ABS_STRESS` + `CRED_STRESS`; Book A status (A-1/A-2/A-3 conditions met/unmet); Book B tells (SR-1 style, SR-5 RS, once live); devaluation tell status; EM flag status once live; **Mechanism Watch block ≤12 lines (2.7.6) with STALE handling (MW-10)** | ST-10, after D6 |
| Top & Bottom (T&B full, later in Track D) | Bottom-side gate (SR-8, A-2); SR-5 bull trigger candidate; overlay intake queue (§2.6); RRV tag read from `rates.driver`; Valuation ERP input. No reweighting. | ST-11 |
| Disruptive Themes (human-gated) | Factor I evidence log: funding transition (SR-16), memory line (SR-25); Factor V: reserve scorecard as scoreable input (§1.9) | Tranche H |
| Warsh scenario matrix | §2.1.5 edit list | Tranche H |
| Prediction-market spec | Disagreement-layer test case, Kalshi vs. FedWatch on the same FOMC (SR-21) | Tranche H (spec note); PM-1 (data) |
| Signal Triage Register; intake template | SR-1…SR-27; §1.3–1.6 rules | ST-0 |
| Base Rates dated appendix; `docs/ledgers/` | Every calibration ledger | ST-7, ST-8, ST-9, ST-L |

---

## §8 Sequenced work order

One ID scheme: **ST-n**. Each item is one Claude Code session pasted from the laptop with a VPS redeploy after each push. Hours are rough and tight. Preconditions name Track D steps and TODO items by their own names.

**Dependency order.** ST-0 → [D1c] → ST-1, ST-2 → ST-3 → ST-4 → ST-6 → ST-7 → ST-5 → ST-9 → ST-8 → [D4/D6] → ST-10 → [T&B full] → ST-11 → ST-12. Tranche 5: ST-0 → [D1c] → ST-13 → ST-14 → ST-15 → (Sunday block inside ST-10; parallel run inside ST-12). ST-L any time after ST-3. Tranche H any time. **Signed sequence (§13, 26 Sep):** ST-0 now; ST-1/ST-2 after D1c and after Phase 6c completes; Tranche 5 after Tranche 1; ST-L as a separate session after Tranches 1–2; Tranche 4 at its milestones.

**Tranche 1 — Core (≈33 h).** Register, feeds, the rates driver, the Monthly blocks. Answers the live question (10y at a 19-year high, 28 Oct FOMC) and gives every later item its inputs.

| ID | Item | h | Preconditions |
|---|---|---|---|
| ST-0 | Governance: `docs/templates/signal-intake.md` (six fields + §1.3–1.6 rules); `docs/signal-triage-register.md` seeded SR-1…SR-27 from §3 verbatim (SR-10/11 reserved; SR-19 DEFERRED; SR-25 rejected-with-tell); `docs/ledgers/README.md`; `tools/calibration/README.md` stating the offline rule (§1.10) | 2 | none (docs only) |
| ST-1 | Sources I — rates and Treasury: FRED additions (DFII10, DGS5, DTB3, THREEFYTP10, FEDFUNDS, USREC, TREAST, GDP, AA/BBB OAS, TOTALSL/REVOLSL/NONREVSL, RTWEXBGS, Z.1 rows); ACM CSV; SF Fed; DKW Excel; TreasuryDirect auctions; Fiscal Data MSPD (G-14); `manual_input` CLI (`tools/manual_input.py`: key, value, observed_at, note → store with `available_at`, `run_id`) and its first keys (SEP median, FedWatch, CBO path, NIC/cover); registry entries for all; `make validate` green | 5 | **D1c**; the scheduled FRED pull (TODO, G-20) |
| ST-2 | Sources II — external and FX: `tic.py` (three tables, both vintages); CFTC COT (turn the existing switch on); MoF JGB; FRED Japan/China monthly; CFETS fix; CNH HIBOR; SAFE; WGC; EIA weekly (existing switch); CIE/UMich/SCE; Ken French, Damodaran, Shiller, Pink Sheet, LBMA loaders; yfinance symbol additions (IVW/IVE/IWF/IWD, EEM/VWO/ACWX/EMXC, GUNR, GLD, CNH=X) and quarterly fundamentals (AMZN, GOOGL, MSFT, META, ORCL, MU); SIFMA parse; FINRA margin debt; leveraged-ETF AUM; `manual_input` keys (AAII, MSCI, IEA/global stocks, COFER/ECB, HBM/DRAM, G4 gap, Livingston) | 6 | D1c; ST-1's CLI |
| ST-3 | Object — `rates.driver`: `calc.attr_*` (two cuts, 1w/1m/since-event), `calc.corr_spy_tlt_60d`, `calc.infl_vol`; four model term premia registered; cell rules, persistence and trace in `config/market_state.yaml`; `validate_regime.py` gates (cell never computed outside the close pass; trace present; models' sign disagreement surfaces); offline calibration ledger `tools/calibration/sr06_09_17_driver.py` (bear-flattening vs. bear-steepening sets; DKW four episodes; correlation by cell) → `docs/ledgers/rates-driver-2026-09.md` | 7 | ST-1 |
| ST-4 | Features — Duration Absorption and rates flags: `calc.net_supply_*`, `calc.priv_residual_12m`; `auction.*` features and `ABS_STRESS`; TIC composition and holder shares, `ABS_FRAGILITY` (display only); `calc.fed_mkt_gap_*`, `CRED_STRESS`, `calc.pm_disagree_fed` (FedWatch by hand until G-4); `DEANCHOR`, `calc.be5y5y_range_pos`, `calc.producers_spot_ratio`; `calc.self_fund_ratio`, `calc.hs_netdebt_12m`, `calc.aa_bbb_oas_diff`, `calc.ai_long_share`, `calc.mu_inv_days`; `calc.cb_gold_12m`, `calc.tic_official_12m`, `calc.tic_private_12m` | 6 | ST-1, ST-2, ST-3 |
| ST-6 | Monthly rendering: the two blocks; Rate machine summary; Factor I/III/IV/V lines per §7; China panel status lines; `tools/validate_monthly.py` extended (no block fetches; every line populated or `NOT AVAILABLE` with source; block line caps) | 7 | ST-4 |

**Tranche 2 — Book behaviour (≈22 h).**

| ID | Item | h | Preconditions |
|---|---|---|---|
| ST-7 | Calibration studies I (offline, `tools/calibration/`): SR-12 bond allocation (regime × correlation split); SR-15 rank test and gold window test; SR-22 auction tails 2009–2026; SR-23 net-supply regression with subsamples and funds-rate control; SR-21 divergence episodes; ledgers to `docs/ledgers/`; A-3 gate status written back to the register | 6 | ST-4 |
| ST-5 | Features — funding currencies: `calc.jp_*` (four metrics), `calc.jpy_unwind`; `calc.cny_fix_dev`, `calc.cnh_cny_gap`, `calc.uscn_10y_spread`, `calc.deval_tell` (third leg as `manual_input`, G-21); candidate contradiction rows declared (G-10); Monthly Factor IV lines updated | 6 | ST-2, ST-3 |
| ST-9 | SR-8 false-bottom audit (offline): replay 2000–02, 2007–09, 1973–74, 2022; confirmation-set scoring with held breadth/VIX-TS/SI keys plus margin debt and leveraged-ETF AUM; gate spec written to `docs/ledgers/false-bottom-audit-2026.md` and a T&B config stub; Doctrine rule proposal text | 10 | ST-2 |

**Tranche 3 — Backtest before any panel (≈8 h).** Panels ship only if gates pass; otherwise one line each and a register update.

| ID | Item | h | Preconditions |
|---|---|---|---|
| ST-8 | Calibration studies II: SR-1 Growth/Value (HML 1963–, ETFs 2000–) with SR-13 spread episodes; SR-5 on ALFRED first prints (script pulls vintages directly); SR-14 EM/dollar split; SR-2 unwind anatomy (1998, 2007–08, 2016, 2024) and SR-4 fix thresholds → thresholds into config; panels rendered for passing items only | 8 | ST-2, ST-5 |

**Tranche 4 — Wiring at Track D milestones (≈10 h).**

| ID | Item | h | Preconditions |
|---|---|---|---|
| ST-10 | Daily/Sunday rendering per §7: 07:00 lines (auction, FOMC-week gap, yen flag, rally-inside-bear); 12:30 hooks (yen unwind, devaluation trip, PRL information line); Sunday line and Book A/B status; **Sunday Mechanism Watch block renderer with STALE handling (MW-10; was Pearl WO-5)**; Daily grep gate for "PRL"/"Pearl"; numeral audit passes (D3) | 7 | **D4** (block builders), **D6** (Sunday), ST-4, ST-5, ST-9, ST-13 |
| ST-11 | T&B wiring: A-2 gate; SR-5 bull trigger candidate; overlay intake queue with champion/challenger stubs; RRV tag from `rates.driver`; ERP input; no reweighting | 4 | **T&B full**; ST-7, ST-8, ST-9 |
| ST-12 | `make validate`, `make library-check`, VPS redeploy; register dispositions updated; **start the four-week parallel run of the Sunday block against the interim Saturday scan and decommission it on confirmation (MW-9; was Pearl WO-11)** | 3 | all above |

**Tranche 5 — Mechanism Watch (≈25.5 h).** Independent of Tranches 1–3 except ST-0 and D1c; the same ingestion → store → block shape as PM-1, so it can reuse that scaffolding if PM-1 lands first, and needs nothing from it otherwise.

| ID | Item | h | Preconditions |
|---|---|---|---|
| ST-13 | PRL data layer (was Pearl WO-1…WO-4): `crypto.watch` class in `register/instruments.py` and the PRL entry with the MW-1 fields, loader test rejecting ticker keys (G-24); `altdata/sources/coingecko.py` switch on and extended to `pearl-2` price/mcap/volume/circulating/tickers → PIT series, key from env; `pearl_explorer.py` with the MW-4 fallbacks and ESTIMATED marker (G-26); emission calculator from Appendix E; D1–D6 as `calc.prl_*`; thesis-status rule with trace; formula unit tests (block 1 ≈ 3,229.6; block 113,770 ≈ 2,339.4; supply ≈ 312.72M); registry entries | 11.5 | ST-0; **D1c**; G-24, G-25 |
| ST-14 | Monthly part renderer (2.7.6): thesis paragraph with trace, S1–S8 table, optional supply figure via the existing figure tooling, candidates and status changes, narrative entries; Surveillance-tab watch instrument (G-6); validators (was Pearl WO-9): `coingecko_id == "pearl-2"` and `name == "Pearl"` guard, supply within 2% of formula for the stored height, `available_at` present, STALE-not-empty render test, the Daily grep gate | 7 | ST-13 |
| ST-15 | Emerging scan (was Pearl WO-7/WO-8, ≈4 h saved by reusing the news pipeline): `mechanism_watch` query group in `config/story_queries.yaml` run by `news.py`; CoinGecko recently-added and hashrate-tracker legs; dedupe against the instrument table and register; rule pre-filter; `mechanism_watch` store table; `make mechanism-register` renderer; CLI `promote` / `reject` / `review`; LLM assessment step behind the existing gate (Appendix F prompt verbatim) writing register fields and a graded narrative-register entry (G-29) | 7 | ST-13; the events/news pipeline (committed 25 Sep, `01b496b`); existing LLM gate plumbing |

**Slot L — one library session on the `library` worktree (≈6.5 h).** ST-L: Digital Assets dated appendix "Mechanism watch — Pearl and proof-of-useful-work, as of 2026-09" and one timeless mechanism paragraph on proof-of-useful-work if none exists (MW-8; was Pearl WO-10); The Rate and Liquidity Machine (rates driver, Duration Absorption chapter note, auction base rate, de-anchoring definition, Livingston note, hedge substitution); Equities (Growth/Value mechanism and pair, tech/defensives, memory-cycle table, one-factor-market note); Currencies (funding-currency stack, China position, devaluation tell, US-vs-RoW and the dollar cycle, reserve scorecard and regimes, external-financing composition and holder fragility); Metals and Energy (gold window fragility, buffer variable, producers-vs-spot); Credit (capex funding transition and rings); Base Rates ledgers (SR-1, 2, 5, 6, 7, 12, 13, 15, 21, 22, 25) as dated appendices; Debt Cycles brief (hiking into a bubble; Koo case for China; supply regimes; fiscal-dominance cross-reference); Market Structure & Cascades brief (risk-parity/target-vol de-levering; leveraged-ETF rebalancing); Positioning & Flows (fuel metrics); Operating Doctrine (candidate rules from SR-8 and SR-22); operator behavioral paper (dip-buying cohort, rally trap); Portfolio Construction brief (Book A rule table, barbell, Cheap-and-Unloved block); Warsh matrix variables. Dated content in dated appendices; `make library-check` once at the end; merge by PR.

**Tranche H — by hand (Ari; ≈5 h once, then recurring).**

| Item | Once | Recurring |
|---|---|---|
| Hiking-cycle table 1955– (`data/reference/fed_cycles.csv`) with SR-21's conceded/refused rows | 90 min | — |
| Warsh matrix single edit (§2.1.5) | 45 min | — |
| Tail-register edits (SR-3); 5.25% note (SR-9); Doctrine notes (SR-8, SR-22); projection-rule rationale (SR-18) | 45 min | — |
| SR-20 scorecard first entry (USD share, constant-FX share, gold share, holder split with SR-27 tags) | 30 min | 30 min at each DT refresh; 5 min/quarter |
| Livingston 1965–80 base-rate note (SR-24) | 30 min | — |
| `manual_input` entries: SEP median, FedWatch (until G-4), NIC/cover (SR-16), HBM share and DRAM direction (SR-25), global-visible inventory and IEA days of cover (SR-18), AAII three numbers (SR-12), MSCI end-of-month file (SR-14), CBO path and G4 gap (SR-23), panda-bond volume (SR-4) | 20 min | ≈25 min/month + ≈30 min/quarter |
| Mechanism Watch by hand (SR-10): weekly review of the Sunday block and any CANDIDATE rows (`promote` / `reject` / `review`); S1/S2/S7/S8 narrative entries where the scan missed them; the MW-9 confirmation after four clean weeks; quarterly MW-7 review | 10 min | ≈10 min/week; ≈20 min/quarter |

**Deferred backlog (Appendix C, ≈35 h, not trigger-based).**

**Totals.** Tranche 1 ≈33 · Tranche 2 ≈22 · Tranche 3 ≈8 · Tranche 4 ≈14 · Tranche 5 ≈25.5 · Slot L ≈6.5 → **≈108 h of sessions** (≈109 with rounding), plus ≈5.5 h by hand once. Cut lines: Tranche 1 alone answers the live question; Tranches 1–2 change Book behaviour; Tranche 3 decides which panels exist; Tranche 4 cannot run before its Track D milestones regardless; Tranche 5 is severable and can run beside Tranche 1 or after it.

**Session 1 paste prompt (ST-0; docs only, safe before D1c). Estimated run time 15–25 minutes; session ≈1 h including review.**

```
Read CLAUDE.md, docs/market-state.md, and docs/change-order-signal-triage-2026-09-25.md in full before acting. Execute ST-0 from §8 of that order and nothing else:
1. Create docs/templates/signal-intake.md with the six canonical fields (§1.1) and the four rules §1.3–1.6 as a checklist.
2. Create docs/signal-triage-register.md seeded with SR-1…SR-27, copying each entry's Ruling / Home / Mechanism / Data / Rights / Validation / Disposition text from §3 of the order verbatim; SR-10 in full (the Mechanism Watch, pointing at §2.7 for the specification and noting that candidates live in the mechanism_watch store table, not in this register); SR-11 as a reserved entry pointing to Appendix C; SR-19 as "DEFERRED — definition required"; SR-25 as "REJECTED as signal — memory-cycle tell adopted". Add a "Built in" column from the §3 master table.
3. Create docs/ledgers/README.md and tools/calibration/README.md stating the offline-calibration rule from §1.10 (scripts pull full history directly; they never read the observation store as-of; ledgers are dated; only live flags read the store).
4. Do not touch config/, altdata/, regime.py or any source; do not add registry entries; do not create any writer.
Run make library-check and make validate (on Windows: & "C:\Program Files\Git\bin\bash.exe" scripts/make.sh validate); report both. Commit once: "governance: signal triage register SR-1–27, intake template, calibration rule". Report GAP G-3 status: whether git log shows any earlier commit of post-freeze-amendment-4-signal-triage-batch-1.md, change-orders-2026-09-19-batch.md or a signal-triage register.
```

Session 2 (ST-1) is written only after D1c has landed and the FRED pull is scheduled (G-20); its prompt will name both as checks it must perform before creating a writer.

---

## §9 Validators and acceptance criteria

**Order-wide.** No change in any composite score, dial or dimension state after every item lands, except the new `rates.driver` sub-state. `make validate` and `make library-check` green. Every new series has a registry entry with `units`, `information_half_life`, `revision_policy`, `mechanism_group`, and `available_at` on every row. No report module fetches (30.4) — `validate_monthly.py` group E extended to the new blocks. No module outside `regime.py` computes a cell, tag or state — `validate_regime.py` asserts it. All flags REPORT_OK-class; no path to DECISION_BLOCKED.

**ST-3.** `rates.driver` renders with a trace string on every object; the four models' sign disagreement is surfaced, never averaged; persistence engages (test: a one-session flip does not move the published cell); the ledger reproduces SR-6's episode sets and SR-17's four episodes.

**ST-4/ST-6.** DKW fetch renders STALE-not-empty on a simulated failure; `ABS_STRESS` and `ABS_FRAGILITY` display as candidates and cannot flip any Book state; TIC-derived metrics carry the vintage they were computed on; the Duration Absorption block renders in ≤18 lines and the Cheap-and-Unloved block in ≤10, every line populated or `NOT AVAILABLE` with source; `DEANCHOR` cannot fire on `fred.breakeven_5y5y` alone.

**ST-7/ST-8/ST-9.** Each ledger states its data source, sample, statistic and pass/fail against the gate written in §3; a passed gate sets the register status to `ADOPTED — rights live` and a failed one to `DEFERRED — gate failed`, each with the statistic (§1.2 vocabulary); a signal that survives only on revised data is logged and gets no rights.

**ST-10/ST-11.** The numeral audit (D3) passes on every new Daily line; T&B composite weights unchanged; only one overlay candidate is in champion/challenger at a time per §2.6; the Sunday Mechanism Watch block renders STALE-not-empty on a simulated fetch failure and never blocks the anchor.

**Tranche 5.** ST-14's validators pass (`coingecko_id == "pearl-2"`, `name == "Pearl"`, supply within 2% of formula, `available_at` present, STALE-not-empty, Daily grep gate); formula unit tests pass; no path from any `calc.prl_*` series or register row to a composite, overlay, trigger, dial or dimension; `calc.prl_thesis_status` is registered as an informational label and `validate_regime.py` confirms it is not read by `regime.py`; the LLM step is not called when the pre-filter passes nothing (test with an empty candidate set); the CoinGecko key is absent from the repo (`validate_secrets.py`).

**Library.** Dated content confined to dated appendices; every paper touched passes `make library-check`.

---

## §10 GAP register

| ID | Gap | Owner | Resolve before |
|---|---|---|---|
| G-1 | Amendment number and architecture Part for this order | §13 | sign-off |
| G-2 | The current change-orders edition: `docs/` holds the 10 Sep consolidated edition; the audit record cites a 13 Sep edition — confirm which is current and where | ST-0 | sign-off |
| G-3 | Whether any of the three superseded drafts, or a register, was committed from another machine (pull first) | ST-0 (git log) | filing |
| G-4 | Free source for FedWatch / fed funds futures probabilities; `manual_input` until settled | ST-4 | `calc.fed_mkt_gap_*` |
| G-5 | Whether the Monthly already carries an AAII equity-allocation line | ST-6 | block build |
| G-6 | Status of the Alt Asset fold into the Monthly (7 Sep ruling) and whether EEM is among its 18 | ST-6 | Factor IV lines |
| G-7 | Whether the June 2026 Rate Repricing Velocity overlay exists in the T&B code that will be ported; if not, `rates.driver` feeds T&B directly as a modifier | ST-11 | T&B wiring |
| G-8 | TIC vintages: which vintage the block renders by default; both stored | ST-2 | first TIC metric |
| G-9 | Belgium/Euroclear attribution for China; China's −98 treated as an upper bound until the benchmark survey prints | Tranche H tags | holder tags |
| G-10 | Whether `carry_vs_vol` and `fix_vs_offshore` belong in the contradiction table (a divergence with a z magnitude) or stay as flags; declare, compute, decide at the first Monthly after ST-5 | ST-5 | — |
| G-11 | Whether prompt time-spreads and Brent–WTI are already computed anywhere (the Daily's Backdrop) | ST-2 | oil feeds |
| G-12 | Real broad dollar index (RTWEXBGS) vs. the held nominal DTWEXBGS for SR-14's split | ST-1 | SR-14 test |
| G-13 | Whether Factor V already carries a gold-share-of-reserves line | Tranche H | first scorecard entry |
| G-14 | Fiscal Data MSPD field mapping for "net marketable issuance" (verify against the refunding tables) | ST-1 | `calc.net_supply_*` |
| G-15 | GUNR adequacy as the commodity-producers proxy (four MSCI points by hand) | ST-4 | ratio note |
| G-16 | SR-19 chart definition (request full post) | — | SR-19 adoption |
| G-17 | Global visible inventory figure: JPM's is not free; IEA OMR headline as substitute | ST-2 | Factor III line |
| G-18 | Source of the "who sold and who bought" figure (research note, Figure 3); the TIC table is public regardless | ST-0 | register citation |
| G-19 | The Batch 1 tranche scope (≈34 h) is taken from the 19 Sep record, not from a filed document; confirm the deferrals in Appendix C match the ruling | §13 | sign-off |
| G-20 | The scheduled FRED pull (TODO open item) — without it the new FRED series land only when the Monthly runs, and every dimension reports absent-stale | ST-1 precondition | ST-1 |
| G-21 | Source for "state banks stop selling dollars" (the devaluation tell's third leg) | ST-5 | tell definition |
| G-22 | PM-1 (Kalshi ingestion) timing in Track D ("Sessions 8–9 with Part 27 v1"); FedWatch by hand until then | ST-4 | `calc.pm_disagree_fed` |
| G-23 | ALFRED store ingestion (O.16) timing; calibration scripts pull vintages directly meanwhile, and no first-print live flag reads the store before O.16 | ST-8, ST-11 | live first-print flags |
| G-24 | Whether `register/instruments.py` is the Security Master of Part 26 or an interim table to migrate from; the `crypto.watch` class goes where the instruments live | ST-13 | PRL entry |
| G-25 | State of the existing `altdata/sources/coingecko.py` behind the `ENABLED_SOURCES` switch (stub or working fetcher); extend rather than rewrite | ST-13 | CoinGecko fetcher |
| G-26 | Explorer JSON endpoint unknown; fallback mandatory; record the discovered endpoint in the fetcher docstring | ST-13 | first stored height |
| G-27 | Pool-composition share has no published source; S4 prints NOT AVAILABLE (carry) | ST-13 | — |
| G-28 | Whether `story_queries.yaml`'s loader accepts a second group (`mechanism_watch`) with its own cadence and cap, or the mechanism queries need a sibling file using the same loader | ST-15 | scan build |
| G-29 | The narrative register's grade scale and schema (Audit #3 §I) — confirm before CANDIDATE rows and mechanism-watch entries are written at its lowest grade | ST-15 | first register write |

---

## §11 Review calendar

| When | What |
|---|---|
| 28 Oct 2026 (FOMC) | First live test of SR-21 (conceded / refused recorded); PM disagreement case recorded by hand |
| Early Nov 2026 (Q4 refunding) | First supply-calendar event (SR-23); auction lines live if ST-10 has landed |
| First Monthly after ST-6 | Duration Absorption and Cheap-and-Unloved blocks first render; `rates.driver` reviewed against the SR-17 print set; G-10 decided |
| Next Disruptive Themes refresh | SR-20 scorecard first entry; SR-16 and SR-25 evidence-log entries |
| Dec 2026 Monthly | ST-7 gate results (SR-12, 15, 21, 22, 23); A-3 status |
| Jan 2027 Monthly | ST-8 gate results (SR-1/13, 5, 14, 2, 4); thresholds into config; first calibration of SR-2/SR-4 thresholds |
| T&B full (Track D) | ST-11; overlay queue opens with SR-2 |
| Weekly (Sat / Sun) | Interim Saturday Pearl scan until MW-9; Sunday Mechanism Watch block once ST-10 lands; CANDIDATE rows reviewed by hand |
| Four clean Sunday blocks after ST-10 | MW-9: retire the interim Saturday scan on Ari's confirmation |
| Dec 2026 quarter-end Monthly | First PRL MW-7 review |
| Jan 2027 Monthly | D4/D6 threshold review (90 days of stored data); 2.7.8 usefulness test |
| Annual Structural Review | SR-20 regime classification; SR-7 table refresh; SR-13/SR-15 window tests; Base Rates ledgers; §1.5–1.6 fixture review; SR-19 definition status; whether "novel-mechanism coins" stays a watch category (2.7.8) |

---

## §12 Explicit rejections (do not re-propose)

- R1 — The 1980–2000 Growth/Value trendline as a rule.
- R2 — "Widest-ever" US–China 10y spread as a mean-reversion signal.
- R3 — "Domestic debt is a false narrative" as a conclusion from shadow reserves.
- R4 — Consumer-credit top decile as a standalone top signal.
- R5 — Single-model term-premium attribution treated as fact.
- R6 — Unconditional "stocks rise in hiking cycles" base rate.
- R7 — 5.25% as a causal level for stock-bond correlation.
- R8 — Any composite or trigger rights for SR-1…9 before the stated gate passes.
- R9 — PRL as a composite, overlay, trigger or factor input; auto-promotion of any mechanism-watch candidate; `PRL` as a key anywhere; PRL or Pearl content in the Daily Cascade outside the 12:30 information line; a thesis status treated as a market state.
- R10 — Carried from the 19 Sep batch Part C (consensus drift) unchanged.
- R11 — "Bonds are a classic contrarian play" from allocation alone, unconditional on regime.
- R12 — The rates channel as the mechanism for mega-cap tech's premium.
- R13 — "Decadal turning point" for EM as a standing claim.
- R14 — "Cheap commodities" from a zero z-score.
- R15 — Hyperscaler issuance level as a signal; absorption is the signal.
- R16 — Any projection segment read as a print (SR-18).
- R17 — Any chart entered without its definition (SR-19).
- R18 — COFER USD share level as a signal in either direction.
- R19 — Pre-midterm political framing as a mechanism for Fed behaviour.
- R20 — An ETF's record low, or a 10 bp global yield day, as a "meltdown" signal; the cash-stance conclusion.
- R21 — The 0.71 annual correlation as evidence without the pre-2008 subsample and funds-rate control.
- R22 — Any composite or trigger rights for SR-12…27 before the stated gate passes; A-3 before both its gates.
- R23 — A hand-drawn trendline on 5y5y breakevens as a breakout rule.
- R24 — The commodity-producers equity index as a lead on inflation expectations.
- R25 — Famous-investor positioning or "doubling down" disclosures as a signal in either direction.
- R26 — A single-row TIC flow change read as a collapse in foreign demand for US assets.
- R27 — "China dumping Treasuries" from the Major Foreign Holders table without the custodial adjustment and the benchmark vintage.
- **R28 (new, from the integration) — Any second regime, cell or tag computed outside the market-state object**, including the two-state tag of the 19 Sep SR-6 ruling and the four-cell table of the 25 Sep batch as standalone constructs.

---

## §13 Sign-off

| Field | Tranche 1 | Tranche 2 | Tranche 3 | Tranche 4 | Tranche 5 | Slot L | Tranche H |
|---|---|---|---|---|---|---|---|
| Decision | ☒ Approved | ☒ Approved | ☒ Approved | ☒ Approved | ☒ Approved | ☒ Approved | ☒ Approved |
| Amendment number / Part (G-1) | #4 · Part: next free, assigned when consolidated into the change-orders edition | | | | | | |
| Placement | ☒ ST-0 now; **ST-1/ST-2 after D1c has landed and Phase 6c is complete** (no two sessions editing `altdata/sources/` at once) | ☒ after Tranche 1 | ☒ after ST-5 | ☒ at D4/D6 and T&B full (pre-authorised; nothing runs before its milestone) | ☒ **after Tranche 1**; the interim Saturday scan covers Pearl meanwhile | ☒ **separate session after Tranches 1–2 land**, so the papers describe blocks that exist | ☒ now |
| Batch 1 deferrals confirmed (G-19) | ☒ as Appendix C | | | | | | |
| Changes noted | Sequence of sessions: ST-0 → [D1c, 6c complete] → ST-1 → ST-2 → ST-3 → ST-4 → ST-6 → Tranche 2 (ST-7, ST-5, ST-9) → Tranche 5 (ST-13 → ST-14 → ST-15) → Tranche 3 (ST-8) → ST-L → Tranche 4 at its milestones. The false-bottom audit (ST-9) is the item that may slide if hours must be cut. | | | | | | |

Signed: Ari Chester — date: 2026-09-26 (decisions taken in chat, recorded here; approved as revision 2)

On sign-off: §1 and the §3 rulings consolidate into the next `docs/change-orders-<date>.md` edition; §8 becomes its work-order addendum; the four superseded drafts, if ever committed, move to `docs/archive/`; Appendix C is carried in that edition's backlog appendix beside the 19 Sep Part C.

---

## Appendix A — ID and numbering map

**Register numbers.** Batch 1 chat labels #1–#9 → SR-1…SR-9. SR-10 → the Mechanism Watch (19 Sep Part B, its Appendix B intake entry re-mapped to the six canonical fields in §3). SR-11 → reserved (19 Sep Part C). Batch 2 chat labels SR-10…SR-21 (24–25 Sep transcript) → SR-12…SR-23; SR-24…SR-27 filed directly.

**Mechanism Watch work items.** Pearl order WO-1…WO-4 → ST-13; WO-5 → ST-10; WO-6 and WO-9 → ST-14; WO-7 and WO-8 → ST-15; WO-10 → ST-L; WO-11 → ST-12. Its rulings keep their MW-n names; its gaps GAP-3/GAP-4 (19 Sep batch) → G-26/G-27.

**Work items.** Batch 1 standalone W1…W12 and 19 Sep batch A-W1…A-W12 → ST-0 (W1/A-W1), ST-1 and ST-2 (W2/A-W2 and the feed halves of W4–W9), ST-3 (W3/A-W3 + Batch 2 W-1), ST-5 (tells from W4/A-W4, W5/A-W5), ST-8 (backtests from W6/A-W6, W7/A-W7, W10/A-W10 partial), Tranche H (W8/A-W8), ST-9 (W9/A-W9), ST-L (W11/A-W11), ST-12 (W12/A-W12). Batch 2 W-0…W-12 → ST-0 (W-0), ST-1/ST-2 (feed halves of W-2…W-5, W-8, W-12), ST-4 (W-2…W-6, W-12 features), ST-6 (W-6, W-7 rendering), ST-7 (W-2/W-3/W-7 backtests), ST-8 (W-9, W-10), ST-4 (W-4 incl. MU), ST-L (W-11).

**Governance clauses.** 19 Sep §1.1–1.4 → §1.1–1.4; Batch 2 §1.8–1.12 → §1.5–1.9 and §1.7; §1.10 is new. 19 Sep GAP-1…7 and Batch 2 GAP-8…24 → G-1…G-23 (renumbered; the Part B/C gaps stay with their Parts).

---

## Appendix B — Current readings (dated 2026-09-25; not part of any timeless text)

| Item | Reading | Source |
|---|---|---|
| 10-year Treasury | 19-year high on 23 Sep; SR-6's block was ruled with the 10y at 5% (15 Sep) | CNBC; Runkevicius |
| 5-year auction | $70 bn at 5.033% (highest since 2006); TLT 80.46 weekly, >50% below 2020 peak; global 10y +≈10 bp | Padley |
| Real yields / breakevens | 10y TIPS ≈2.75% (from ≈2.0% at start of 2026); 5y5y ≈2.25% by 23 Sep after 2.31% on 12 Sep | Alpine Macro; Azuria |
| Oct 28 FOMC | Funds 3.75–4.00%; hike probability 26.6% (10 Sep) → 77.5% peak / 70.9% close (24 Sep) | Bianco / WIRP |
| G4 issuance gap | ≈7.0% of GDP (2025); avg 10y real yield ≈+1.0%; corr 0.71 | Lustig |
| TIC flows 12m to Jul 2026 | Net foreign LT purchases 1,276.9 (vs. 1,182.6); private Treasury 263.4 (vs. 506.3); official Treasury −16.8 (vs. −50.3); private equities 802.3 (vs. 606.1); official equities 139.6 (vs. −8.0); bills 49.4 (vs. 250.5); Treasury share ≈19% (vs. ≈39%); July net LT −27.9 | TIC via Riemann |
| TIC holders Jun 2025→Jun 2026 ($ bn) | UK +84, Belgium +52, Ireland +43, Luxembourg +31, Singapore +31, Canada +21, UAE +18, France +16, HK +14, Cayman +12, Saudi +12, Israel +9, Korea +8, Norway +8, Taiwan −5, Switzerland −16, Japan −38, India −41, Brazil −47, China −98 | TIC via research note (G-18) |
| Hyperscaler issuance | ≈$200 bn YTD vs. ≈$80 bn 2025; AI ≈18% of IG supply H1, 42% of ≥15y; NIC 2→12 bp; Amazon July deal 18–21 bp, cover 2.5× vs. 3.2×; 78/91 wider; net debt +≈190% y/y; leverage ≈1.8× | Bloomberg via Lemand |
| Investor bond allocation | ≈18.5%, lowest since 2007 | Topdown Charts |
| Tech vs. defensives | Tech ≈+115%, defensives ≈−38% record; spread ≈150 pp vs. ≈210 pp in 2000 | Topdown / LSEG |
| EM relative to DM | ≈1.7 vs. 4.5 peaks; absolute at all-time high in USD | Topdown / LSEG |
| Cross-asset z | Gold +1.7 (spike +2.9); S&P +1.0; Treasuries −0.8; commodities ≈0 | Topdown Charts |
| Oil | Brent $106.60, WTI $94.51 (25 Sep); Hormuz not fully reopened; JPM chart data to ≈Apr 2026, projection thereafter | Gulf News; Bloomberg/JPM |
| COFER Q1 2026 | USD 57.13%; EUR 20.03%; JPY 5.44%; GBP 4.40%; CAD 2.48%; AUD 2.11%; CNY 1.99%; CHF 0.24%; other 6.18% | IMF via FintechNews |
| Commodity producers | MSCI World Commodity Producers NTR 8,113.76, all-time high | Azuria |
| Burry disclosures | Shorts added: MU, NBIS, SOXX, PLTR; longs: QXO, BBW, SFM, BIRK, MELI; Acer CEO on memory inventories | Monchau via Bull Theory |
| China (SR-3 facts) | ≈$6 T state-controlled foreign assets; NIIP > $3 T | Setser via post |
| PRL (SR-10, baseline 19 Sep) | ~$1.00–1.15 after a +70% week; mcap ~$250–280M; FDV ~$2.3B; 3 venues, top ~91% of volume; block 113,770 (15 Sep): 312.72M mined, difficulty ~21.4M; week-one overhang 38.9%; supply gap 57.7M; one paid-compute partner (Together AI); full fact sheet in Appendix E | Hashrate Index, CoinGecko, explorer, Together AI |
| `rates.driver` (presumed, pre-build) | fed_path with a term-premium component pending the DKW split; A-3 not met; `DEANCHOR` not met; `ABS_FRAGILITY` reads "rising" on the TIC prints, candidate only | this order |

---

## Appendix C — Deferred backlog (not trigger-based; carried with full specification so future sessions need nothing else)

**Batch 1 deferrals (per the 19 Sep tranching, G-19).** SR-3 China panel assembly as a Monthly section (inputs fetched in ST-2; ≈3 h); SR-2 overlay-input wiring beyond the flag (queue #1, at T&B full — in ST-11's scope only if the gate passed; else ≈2 h later); SR-1 Monthly style panel and Book B pair rule (ships in ST-8 only if the gate passes; else ≈3 h later); SR-5 RS tell and Monthly panel (same; ≈2 h); SR-9 scatter reproduction and regression (≈4 h); SR-7 table automation (by hand suffices; ≈3 h if ever); SR-8 fuel-metric automation beyond margin debt and leveraged-ETF AUM (≈2 h).

**Batch 2 deferrals.** SR-19 house metric — rolling 63d R² of SPX daily returns on an equal-weight top-10 AI basket, and the equal-weight index's beta to it; gate on 2000 and 2021 (forward 6m drawdown conditional on R² top decile); Concentration & Complacency candidate (≈2 h, after G-16). SR-20 monthly automation of COFER/ECB constant-FX (≈2 h). SR-15 full four-metric composites per asset (≈4 h). G4 issuance-gap automation from national sources — DMO/BoE, MoF/BoJ, ECB/national issuers (≈6 h).

**19 Sep batch Part C (by reference; register SR-11).** Consensus drift — sixth I-b input "consensus drift" (unscored prose line), Foundations evidence log, ESPAI point-in-time fixture, LEAP as a source (≈6.5 h). Its interim bimonthly scan continues (§1.12). Part B (the Mechanism Watch) is no longer backlog — it is Thread D and Tranche 5 of this order.

**Mechanism Watch deferrals (from Thread D).** Prediction-market cross-link for Pearl or register candidates (after PM-1, ≈1 h); a daily intraday PRL series (re-check the CoinGecko monthly call budget first; ≈1 h); automation of the S1/S2/S7/S8 narrative fields beyond the scan (not planned — they stay `manual_input` by design).

**Total backlog ≈35 h.**

---

## Appendix D — Sources

Batch 1 (10–19 Sep 2026): J. Weniger, Growth/Value chart (8 Sep) · chat question on the yen carry stack (10 Sep) · shadow-reserves post citing B. Setser (11 Sep) · X post on the US–China 10y spread (10 Sep) · J. deGraaf / RenMac, consumer credit (8 Sep) · L. Runkevicius, SF Fed decomposition (15 Sep) · Macrobond hiking-cycle chart · R. Lemand, Nasdaq 2000–02 rallies (19 Sep) · S. White, 5.25% and stock-bond correlation (Sep). Batch 2 (24–25 Sep 2026): Topdown Charts, "10 Charts to Watch in 2026 [update]" · Bloomberg, "Hyperscaler Debt Sales Skyrocket" via R. Lemand · Alpine Macro via Chen Zhao · JPMorgan Commodities Research / Bloomberg oil-inventory chart via F. Brimberg and C.-H. Monchau · C.-H. Monchau, beta chart (undated) · IMF COFER Q1 2026 via FintechNews · Bianco Research / Bloomberg WIRP · M. Padley · H. Lustig · O. Costa / Azuria Capital · C.-H. Monchau, Burry disclosures via Bull Theory · US Treasury TIC via J. Riemann · TIC Major Foreign Holders via an unidentified research note (G-18). Context: Gulf News (25 Sep) · Wikipedia 2026–2028 oil market chronology · Blab Business (10 Jun) · Bloomberg (10 Sep) · CNBC (23 Sep). Mechanism Watch (19 Sep 2026): Hashrate Index, "Pearl (PRL): The AI-Compute Cryptocurrency, Explained" (2 Jun 2026) · Phemex Academy, "What Is Pearl (PRL)?" (updated 17 Sep 2026) · Together AI, "Together AI and Pearl Research Labs Team Up to Reduce the Cost of AI Inference" (15 May 2026) · Tom's Hardware, "New AI-compute cryptocurrency Pearl sparks a GPU mining rush but profitability is already sliding" (31 May 2026) · Alea Research, "Pearl — Proof of Useful Work for AI Compute" · CoinGabbar, Pearl joins Nvidia Inception (23 Jul 2026, updated 19 Aug) · CoinGecko, Pearl (`pearl-2`) · Bybit price page, Pearl · Pearl Research Labs, "Proof of Useful Work" · Komargodski & Weinstein, arXiv 2504.09971 · Pearl node code, block subsidy function (`node/blockchain/validate.go`). Repository state: `CLAUDE.md`, `TODO.md`, `docs/market-state.md`, `config/market_state.yaml`, `metrics_registry.yaml`, `source_registry.yaml`, `altdata/config.py`, `docs/change-orders-consolidated-2026-09-10.md`, as read from the laptop working copy on 25 Sep 2026 21:56 ET; `altdata/events_ingest.py`, `altdata/sources/news.py`, `config/story_queries.yaml` as committed in `01b496b`.

---

## Appendix E — PRL baseline fact sheet (as of 2026-09-19; dated content)

**Identity.** Pearl (PRL). Pearl Research Labs; CEO Omri Weinstein (complexity theorist; Princeton PhD; Hebrew University; lists ex-Nvidia, ex-Vast Data). Mechanism paper: Komargodski & Weinstein, "Proofs of Useful Work from Arbitrary Matrix Multiplication," arXiv 2504.09971 (April 2025). Repo `github.com/pearl-research-labs/pearl`; node `pearld` (btcd fork, Go); GPU miner built on vLLM; ships a zero-knowledge proof-of-work circuit and XMSS post-quantum signatures. Genesis 2026-04-27 09:00 UTC; block target 194 s; difficulty adjusts by exponential filter with a one-week half-life. CoinGecko id `pearl-2`. Explorer `explorer.pearlresearch.ai`. Team X: @prlnet; CEO: @WeinsteinOmri.

**Emission.** No halvings. Max supply 2.1e9. Reward at height h: `2.1e9 · K / ((h + K) · (h − 1 + K))`, K = 650,226 (194 s blocks in four years). Cumulative: `supply(H) = 2.1e9 · H / (H + K)`; half the supply at block 650,226. Block 1 ≈ 3,229.6 PRL; block 113,770 ≈ 2,339.4 PRL. At block 113,770 (2026-09-15 23:53 UTC): 312.72M mined (14.9% of cap); ~1.04M PRL/day at target pace; supply ≈ 626M one year on.

**Launch distortion.** Difficulty started at 1; the first 40,000 blocks arrived in 5.9 days (~12.7 s each vs. 194 s target); 121.70M PRL (38.9% of all supply mined to 2026-09-15) was minted by 2026-05-03 06:31 UTC. Roughly 127M PRL exist ahead of the design schedule. Block pace has matched target since early September 2026. No vesting; holders anonymous.

**Supply gap.** Code-derived 312.72M vs. CoinGecko circulating 255.05M (2026-09-16): 57.67M PRL (18.4%) unexplained.

**Market.** Price ~$1.00–1.15 on 2026-09-18/19 after a +70% week (+57% in one day on ~$5–6M volume). July 22 low $0.23; Sep 15 close $0.5597; late-May peak ~$1.65 per Hashrate Index (aggregator ATH figures conflict because CoinGecko's series starts 2026-06-22). Market cap ~$250–280M; FDV ~$2.3B; rank ~#150–160. Venues: CoinEx (most active), BigONE, SafeTrade; one venue ~91% of reported volume; no tier-1 listing.

**Demand side.** Together AI partnership announced 2026-05-15: Gemma-4-31B-it-pearl inference endpoint priced >25% below standard, discount offset by PRL emissions; Together states more Pearl-powered products and a way for customers to obtain a share of emissions are planned. No PRL-denominated marketplace exists; Pearl's docs describe on-chain compute contracts as a future direction. Nvidia Inception acceptance (July 2026). W7A7 quantization technique disclosed (unverified independently).

**Mining.** Nvidia-only. Official Pearl Research pool: 20% fee, H100/H200 only. Community pools support consumer GPUs down to Volta. RTX 5090 estimated revenue fell from ~$33.80 to ~$17.19/day within weeks of the late-May rush. Luxor (Hashrate Index) characterises inbound interest as VCs, private financial firms and miners rather than retail, front-loaded over the first 2–3 months; natural hardware fit is GPUs lacking back-end networking for training clusters.

**Ticker collisions.** Perle (Solana, PRL; AI data-labeling; Upbit/Bithumb listed); "Pearl" (Polygon, PEARL); pearl.finance (Tron, PEARL); "Pearl Research" (Base, PRL; 100B supply — unrelated). Phemex's "PRL" is Perle and is delisted.

---

## Appendix F — LLM assessment prompt (gate step, ST-15)

Use verbatim as the system/task prompt for the candidate-assessment call; substitute the bracketed fields from the pre-filter output.

> You are assessing candidate cryptocurrency projects for Ari Chester's mechanism-watch register. Ari is an experienced trader and P&C reinsurance executive; write densely, bottom line first, no beginner explanations, no disclaimers.
>
> A candidate qualifies only if ALL of the following hold: (i) an identifiable team with checkable credentials, or a paper on arXiv, IACR ePrint, or a peer-reviewed venue; (ii) a live mainnet, or a credible testnet with public code; (iii) at least one of: an enterprise partner, a tier-1 listing (Coinbase, Binance, Kraken, OKX, Bybit, Upbit), market cap above $50M, notable mining or hashrate interest, or coverage by a serious outlet. Exclude memecoins, forks and rebrands, GPU-marketplace tokens without a novel mechanism, L2s and rollups without a consensus novelty, and restaking or yield derivatives. Inclusion classes: proof-of-useful-work and AI-compute-backed chains; verifiable-compute consensus; new proof-of-work primitives with a paper; compute- or energy-backed monetary designs; fair-launch L1s grounded in peer-reviewed cryptography; post-quantum-native chains.
>
> Candidates: [list of name, links, pre-filter evidence].
>
> For each candidate, return JSON with: `qualifies` (true/false), `name`, `canonical_id` (CoinGecko id or chain+contract; null if unknown), `mechanism_class`, `whats_new` (one line: what is new mechanically), `team_or_paper` (link), `stage` (paper/testnet/mainnet), `materiality_evidence` (which of i–iii, with links), `key_risk` (one line), `why_it_could_matter` (one line), `sources` (links used). If a candidate fails, say which criterion failed in `fail_reason`. Do not pad; if nothing qualifies, return an empty list. Verify claims against the linked sources; if a claim cannot be verified, mark it `unverified` rather than asserting it.
