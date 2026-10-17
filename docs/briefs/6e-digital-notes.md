# 6e-digital: the Digital Assets addendum, Phase 1, and the index-event entries (17 Oct 2026)

**Branch and merge order.** `6e-digital`, session B, cut from the tip of `6e-releases`
(`0059d24`, its CI read and recorded). It carries the whole 6e line and **merges after
`6e-metric-lenses`, `6e-rest` and `6e-releases`, in the second stitched chain.** Built
against the Batch 8 order (`docs/change-order-signal-triage-batch-8-2026-10-17.md`, filed
on `docs-batch-8` by Part 0): items 49 and 51, sections 4, 5 and 6's placement, verify
items 2 and 5, filing notes 1-5 and 9-10.

**Rules kept.**
- Branch only: pushed, not merged, not deployed, nothing run on the box.
- Paper only, with no order path; the Brookfield blocklist is untouched.
- No secret and no real position figure in any fixture or test. The register fixture's
  notionals are round placeholders.
- Not touched: `.env`, the box's units, the decision register, the ledgers,
  `chester-meme`, session A's branches.
- The X pilot's ledgers on Drive were read once, read-only, to learn their columns.
  Nothing was written there.

## Part 0: Batch 8 filed

| Item | Result |
|---|---|
| File | `C:\Users\arich\Downloads\change-order-signal-triage-batch-8-2026-10-17.md`, 27,009 bytes, LF |
| SHA-256 over LF | `c0aa024ebe4d17b4364c338e644fae822b062283bc7ff78febf733e06314121e`: **matches** |
| Branch | `docs-batch-8` from `origin/main` (`1148c66`) |
| Commit | `1388967` "docs: Batch 8 change order, signal-triage round 6 part 3 (items 49-51, digital assets), filed 17 Oct 2026"; the staged blob hashes to the same SHA-256 |
| Merge | Ari's, with Monday's chain, after `docs-batch-7`. Not merged here. |

## Verify item 5: can the Sunday build carry a second page without change?

**No, not without a change; the change is small and is fixture-gated.**

The Weekly's publish path is `weekly_report._stacked`:
1. the consistency gate (exit 5);
2. `weekly_stack.produce`: prose, charts, budget, render, PDF;
3. `deliver.deliver`, which archives one HTML and one PDF and sends one message with the
   PDF attached.

Nothing in it knew of a second page, and `deliver()` took no attachment beyond the PDF.
These are the changes, and nothing else changed:

1. **`daily_cascade/deliver.py`:** `deliver()` gains `attachments=` (filename, data,
   subtype). They are sent beside the PDF through the existing `send_html` attachment
   path.
2. **`daily_cascade/weekly_report.py`:**
   - `_stacked` builds the addendum *before* the Weekly (`digital_addendum.produce`), so
     the link line knows its state.
   - It passes `attachments=digital_addendum.attachment(add)` on both sends: the live one
     and the mailed dry run.
   - The run's printout gains one status line.
3. **`daily_cascade/weekly_stack.py`:** when the payload carries an addendum, `render`
   prints **one line** under the header: "Digital Assets addendum, about N minutes:
   weekly_digital_<ending>.html, attached to this message." The archived edition says
   "beside this edition" instead. Without an addendum, the Weekly is byte-for-byte as
   before.

**The gates on it:**
- **`validate_digital_addendum.py` group I:**
  - the page archives beside the Weekly;
  - the message carries the PDF and the page;
  - the Weekly gains exactly one line;
  - a failed addendum costs only the addendum: nothing is attached, and the line says
    "not built this week".
- **`validate_weekly_stack.py`** gains two checks on the real fixture Weekly: no line
  without an addendum, exactly one with it. That gate renders the PDF, so it runs in CI.

**Archive layout, beside the Weekly:**
- `weekly_digital_<ending>.html`
- `weekly_digital_<ending>_edition.json`
- `weekly_digital_<ending>_appendix.md`

**First edition.** `config/digital_addendum.yaml` sets
`first_edition_week_ending: 2026-10-30`.
- A Sunday before it builds the page as a **dry run only**: archived under
  `reports/dryrun/`, not attached, no line in the Weekly. That covers the Weekly of 25 Oct,
  the order's "the Weekly of 25 Oct renders the addendum as a dry-run page".
- From the Weekly of 1 Nov the page is attached.

## The page: each section, its source today, its Tranche A source

The page has nine code-written sections in the ruling's order
(`daily_cascade/digital_addendum.py`, `config/digital_addendum.yaml`). Where a source is
not yet stored, the cell reads **"awaiting Tranche A"**, never a guess.

| # | Section | Today (Phase 1) | Tranche A / later |
|---|---|---|---|
| 1 | The read | One paragraph, at most 120 words and 6 figures, **from this page's tables only**. It goes through the existing narrative step (`narrative.generate`: precision, the numeral audit), then the stack's style, id, excess, stance and figure audits; if it fails, it is withheld with its reason. No new model path. | unchanged |
| 2 | Tape | BTC, ETH, SOL and ZEC from Yahoo's stored daily closes (`yfinance.mkt_*_usd`). The weekly bar is built from the dailies; beside it, the day, the trailing 30 days, the week's range of closes and 30-day realised vol. | Awaiting: DVOL `deribit.dvol_btc`/`deribit.dvol_eth` (CD-2), funding `calc.funding_agg` and OI `calc.oi_usd` (CD-3). Basis and liquidations have no named key yet (Phase 2). |
| 3 | Flows | **Stablecoin supply prints today** (`llama.stable_total`, stored since the crypto basket pulled CD-1 forward). | Awaiting: the ETF weekly sums `farside.btc_total`/`farside.eth_total` (CD-4), exchange flows, and treasury-company purchases (49b). |
| 4 | Mechanics | MSTR's option-implied move to 11 Nov and 30 Nov, from the captured chains (`ahead.implied_move`); "not captured" otherwise. | Awaiting: skew and term structure (CD-2) and mNAV (49a). Crypto GEX prints "not built (EL-12)". |
| 5 | On-chain | Nothing stored. | Awaiting: the froth gauge `calc.froth_z` (CD-7) and exchange balances. SR-29's `btcdata.lth_supply_share` is CD-12 (Tranche C), printed "by hand until CD-12". |
| 6 | Narratives and attention | From the X pilot: the attention ledger (themes, days, peak volume, shock days, the representative post); the digests' disagreement pairs, printed only with both URLs; new voices from the voices ledger. Also the Saturday scan's stored items (`scan.crypto_basket_item`). A week with none prints **"no digest rows this week"**. | Item 50's Tranche 1 moves the ledgers into the store. |
| 7 | Incidents and regulation | The digests' section 2 items themed incident or regulation, each with its post URL; the calendar's regulatory dates. | unchanged |
| 8 | Ahead | `config/digital_asset_calendar.yaml` (item 49c), the FOMC dates from the events store, and Deribit's month-end expiries by rule, over a 45-day window. | unchanged |
| 9 | The book | Book D's active crypto paper decisions from the register, **opened `mode=ro`**, not through `Register()`, whose open runs migrations. Drafts are counted. The section says "the paper engine's view joins this section from mid-November". | the paper engine (mid-November) |

The page ends with the **dated line for the Digital Assets paper**. Code writes it from the
page: the week, the closes and weekly changes, the stablecoin change and the next dated
event. It is a draft for Ari's accept-all, never the model's.

## Item 49c: the index-event entries

The entries live in `config/digital_asset_calendar.yaml`, set by hand, each with its
source.
- The Weekly's Ahead reads the file as a hand calendar: class `crypto_index_event`,
  tier 2, session-set.
- The addendum's section 8 reads it over 45 days.
- `ahead.hand_rows` now prints an entry's `marker` beside the event.

| Date | Entry | Source |
|---|---|---|
| 28 Oct | Strategy (MSTR): STRC shareholder vote | Strategy's press release of 16 Oct (via the 17 Oct digest); the order |
| 30 Oct | FTSE Russell: rank day, December reconstitution | lseg.com Russell reconstitution page, read 17 Oct |
| 11 Nov | MSCI: November review announced, after the US close | the order (The Block, 15 Oct) |
| 13 Nov | FTSE Russell: preliminary lists (updates 20, 27 Nov, 4 Dec) | lseg.com, read 17 Oct |
| 15 Nov | SEC: VanEck JitoSOL ETF decision | the order only |
| 30 Nov | MSCI: the review takes effect at the close, **"30 Nov, to verify on MSCI's calendar"** | the order; verify item 2 open |
| 11 Dec | FTSE Russell: the reconstitution takes effect after the close | lseg.com, read 17 Oct |
| (undated) | S&P DJI's next S&P 500 rebalance: **"date not published"** | www.spglobal.com answers 403 to a keyless client, robots.txt included |
| (undated) | The next Nasdaq-100 review: **"date not published"** | no review calendar on nasdaq.com or indexes.nasdaqomx.com |

**Verify item 2 is not closed.**
- www.msci.com disallows `/en/*` in robots.txt.
- Its index-review page (`/indexes/index-resources/index-review`) answers with a browser
  challenge, a JavaScript proof-of-work page, so no keyless client can read it.
- Under the 16 Oct rule that is a gap, not something to work around. The marker stays
  until Ari reads the date in a browser and removes it.

## The sweep: folders added, inbox paths

`scripts/rclone_sync.sh` gains `pull_x_pilot`, after the GLD archive pull. It never sets the
sweep's exit.

| Drive | Box inbox |
|---|---|
| `chester-x-digest/x-digest-YYYY-MM-DD.md` (exact name only) | `~/chester-data/inbox/x-digest/` |
| `chester-vendor-checks/x-triage/x-attention-ledger.csv`, `x-voices-ledger.csv` | `~/chester-data/inbox/x-triage/` |

- **Each copy is `copyto` of a named file, never a sync.**
- **Each copied file gets a `<file>.copied_at` stamp.** It holds the UTC instant the file's
  bytes arrived, and is rewritten only when the bytes change.
  - The stamp is the file's `available_at`. `copyto` keeps Drive's modification time,
    which is not when the box could read the file.
  - A file without a stamp falls back to its mtime, and the section's footnote says so.
- **A file copied after the cutoff is not read.**
  - So a re-render of a past week, after the ledger has been re-copied, prints no ledger
    rows.
  - That is conservative, and it is the pilot's limit; item 50's Tranche 1 stores the rows
    point-in-time.
- **The sweep's unit,** `deploy/systemd/chester-backup.service`, adds
  `-%h/chester-data/inbox/x-triage -%h/chester-data/inbox/x-digest` to `ReadWritePaths`.
- **`tools/validate_backup.py`** holds the new pull and the five inboxes. It passes 66/66
  locally.

## Session-set values (for Ari)

| Value | Set at | Reason |
|---|---|---|
| Reading target | 5 minutes | the ruling |
| Word budget | 1,100 words, counting every printed word (tables, lines, the read, footnotes) | 4.4 minutes at the stack's 250 a minute, leaving a chart's room |
| Chart budget | 2, with **none drawn in Phase 1** | the tables carry every figure; a chart waits for Tranche A's series |
| The read | one paragraph, at most 120 words and 6 figures | five sentences' worth; the stack's paragraph figure cap |
| The monthly bar | the trailing 30 days, not the calendar month | the 1 Nov edition would otherwise read a one-day month |
| Realised vol | 30 daily log returns, annualised over 365 days | crypto trades every day |
| Ahead window | 45 days | the 25 Oct page already shows MSCI's effective date |
| Ahead class | `crypto_index_event`, tier 2 | passive flows in the proxies; below the macro tier-1 prints |
| Trim order | incidents, then attention, then ahead; the longest table's last row goes first, and the section is marked "(trimmed)" | the reference-like sections go first |
| Book D's crypto names | BTC, ETH, SOL, ZEC, IBIT, FBTC, ETHA, MSTR, COIN, BITO, GBTC, MSTU, MSTZ | the proxies in the stack today |
| Deribit expiries | the last Friday of the month, 08:00 UTC, **marked "to verify on Deribit's calendar"** | Deribit's own calendar was not read |

The full fixture week prints **888 words, about 4 minutes, 0 charts**.

## Item 6: keys, catalogue, families

**No new store key.**
- Phase 1 reads what is stored (the Yahoo closes, `llama.stable_total`,
  `scan.crypto_basket_item`) and the inbox files.
- The X ledgers enter the store only with item 50's Tranche 1.
- The Tranche A keys the page names (`deribit.dvol_btc` and the rest) are the crypto
  order's. Tranche A registers them when it writes them.

So `metrics_registry.yaml`, `source_registry.yaml`, the catalogue and the family
assignments are unchanged, and there is nothing to regenerate.
`config/catalogue_commands.yaml` lists `altdata/` modules only, and
`tools/validate_audit_3a.py` would reject a `daily_cascade` line there. The addendum's
command is printed below and in CLAUDE.md.

## The Digital Assets paper's dated appendix

`docs/whitepapers/digital-assets-whitepaper.md` gains **Appendix E: Dated Record**, a
draft for Ari's accept-all.
- **How the weekly lines enter:** code writes each from that week's page. A line waits
  beside the addendum in the archive until Ari accepts it.
- **Item 49's base-rate note** is written by hand.
- The appendix holds no line yet.

`docs/html/` was rebuilt for that paper only. `check_library` reports 0 failures and 0
warnings.

## A sample page, on fixtures

Rendered by the gate's own seeders: synthetic closes, a fixture inbox, a fixture register,
and the scripted writer for the read. No figure here is real.

**Digital Assets — the week to 2026-10-31** · as of 2026-11-01T09:00:00+00:00 · about 4 minutes · 888 words of a 1100 budget · 0 charts

*In the Weekly:* Digital Assets addendum, about 4 minutes: weekly_digital_2026-10-30.html, attached to this message.

**1. The read**

Bitcoin closed the week at $70,984, +0.7% on the week and +6.4% over 30 days, alongside ether at $3,549. Implied volatility, funding and open interest are not yet measured on this page.

<sub>One paragraph by the narrative step, from this page's figures only, under its numeral, style and figure audits.</sub>

**2. Tape**

| Coin | Close | Day | Week | 30 days | Realised vol (30d) |
|---|---|---|---|---|---|
| BTC | $70,984 | -0.5% | +0.7% | +6.4% | 11% |
| ETH | $3,549 | -0.5% | +0.7% | +6.4% | 11% |
| SOL | $177.46 | -0.5% | +0.7% | +6.4% | 11% |
| ZEC | $47.32 | -0.5% | +0.7% | +6.4% | 11% |

| Measure | Reading | As of |
|---|---|---|
| BTC implied vol (DVOL) | awaiting Tranche A | — |
| ETH implied vol (DVOL) | awaiting Tranche A | — |
| Funding, OI-weighted | awaiting Tranche A | — |
| Basis (futures over spot) | awaiting Tranche A | — |
| Open interest | awaiting Tranche A | — |
| Liquidations | awaiting Tranche A | — |

- BTC's week ran $69,766 to $71,336 on daily closes, to 31 Oct.
- ETH's week ran $3,488 to $3,567 on daily closes, to 31 Oct.
- SOL's week ran $174.41 to $178.34 on daily closes, to 31 Oct.
- ZEC's week ran $46.51 to $47.56 on daily closes, to 31 Oct.

<sub>Yahoo daily closes (UTC days); the week is the seven closes to the last stored day; realised vol is 30 daily log returns annualised over 365 days.</sub>

**3. Flows**

| Measure | Reading | As of |
|---|---|---|
| BTC ETF net flow, the week | awaiting Tranche A | — |
| ETH ETF net flow, the week | awaiting Tranche A | — |
| Exchange net flows | awaiting Tranche A | — |
| Stablecoin supply, change on the week | +$3.5bn | 31 Oct |
| Treasury-company purchases (item 49b) | awaiting Tranche A | — |

<sub>ETF totals are Farside's (CD-4); the stablecoin supply is DefiLlama's (llama.stable_total), stored since the crypto basket.</sub>

**4. Mechanics**

| Measure | Reading | As of |
|---|---|---|
| Deribit skew and term structure | awaiting Tranche A | — |
| MSTR mNAV (item 49a; lines 1.2 and 1.0) | awaiting Tranche A | — |
| Crypto GEX | not built (EL-12) | — |

| Through the event window | Option-implied move |
|---|---|
| MSTR to 11 Nov | implied move not captured |
| MSTR to 30 Nov | implied move not captured |

<sub>The implied move is the at-the-money straddle on the first expiry on or after the date, over spot, from the newest captured MSTR chain.</sub>

**5. On-chain**

| Measure | Reading | As of |
|---|---|---|
| BTC long-term-holder supply share (SR-29) | not stored: SR-29 is by hand until CD-12 (Tranche C) | — |
| Froth gauge (memecoin launches, z) | awaiting Tranche A | — |
| Exchange balances | awaiting Tranche A | — |

<sub>SR-29's share is computed once CD-12 lands; the froth gauge is unscored until its gate (not before January 2027).</sub>

**6. Narratives and attention**

*The week's attention map*

| Theme | Days | Peak volume | Shock days | Post |
|---|---|---|---|---|
| flows | 2 | high | 1 | https://x.com/f/status/3 |
| treasury-co | 1 | medium | 1 | https://x.com/t/status/4 |
| privacy | 1 | low | 0 | no post URL in the row |

*Disagreement pairs*

| Date | Question | Side A | Side B |
|---|---|---|---|
| 27 Oct | Does an index exclusion force bitcoin sales? | https://x.com/side_a/status/2001 | https://x.com/side_b/status/2002 |
| 29 Oct | Does an index exclusion force bitcoin sales? | https://x.com/side_a/status/2001 | https://x.com/side_b/status/2002 |

*New voices (the voices ledger)*

| Handle | Role | Incentive |
|---|---|---|
| @newvoice | protocol team, official | protocol-team |

*The Saturday scan*

| Date | Name | Kind | Item |
|---|---|---|---|
| 31 Oct | PRL | listing | PRL listed on a venue (https://example.invalid/prl) |

<sub>The X pilot's ledgers and digests (item 50, Tranche 0), from the box's inbox after the nightly sweep; available as of the sweep's copy time. A theme prints from its ledger rows; a disagreement pair only with both posts' URLs. Grok retrieves; nothing here is its judgement.</sub>

**7. Incidents and regulation**

*From the week's digests*

| Date | Account | Theme | As posted | Post |
|---|---|---|---|---|
| 27 Oct | @acct_one | incident | An exchange paused withdrawals for two hours | https://x.com/acct_one/status/1001 |
| 27 Oct | @acct_two | regulation | The SEC published a custody proposal | https://x.com/acct_two/status/1002 |

*Regulatory calendar*

| Date | Who | Event |
|---|---|---|
| 15 Nov | SEC | VanEck JitoSOL ETF decision |

<sub>Items as the digests record them, each with its post's URL; the claim is the account's, not checked here.</sub>

**8. Ahead**

| Date | Event | Time / status |
|---|---|---|
| 11 Nov | MSCI: November 2026 Index Review announced, the first under the non-operating company rules (Strategy's inclusion decided) | after the US close |
| 13 Nov | FTSE Russell: Russell US December reconstitution: preliminary lists published (updates 20 Nov, 27 Nov, 4 Dec) | — |
| 15 Nov | SEC: VanEck JitoSOL ETF decision | — |
| 27 Nov | Deribit: month-end options expiry | 08:00 UTC; Deribit's last-Friday rule; to verify on Deribit's calendar |
| 30 Nov | MSCI: November 2026 Index Review takes effect at the close | at the US close; 30 Nov, to verify on MSCI's calendar |
| 9 Dec | Federal Reserve: FOMC meeting | statement 14:00 ET |
| 11 Dec | FTSE Russell: Russell US December reconstitution takes effect | after the US close |

- S&P Dow Jones Indices: next S&P 500 rebalance (the broad-exclusion watch) — date not published (www.spglobal.com refuses a keyless client (403, robots.txt included)).
- Nasdaq: next Nasdaq-100 review (the broad-exclusion watch) — date not published (no review calendar on nasdaq.com or indexes.nasdaqomx.com).

<sub>Dated events to 16 Dec from config/digital_asset_calendar.yaml (by hand, each with its source), the FOMC dates from the events store and Deribit's monthly expiries by rule. A date marked "to verify" is not yet confirmed at its source.</sub>

**9. The book**

| Instrument | Direction | Notional (paper) | Vega (paper) | Since |
|---|---|---|---|---|
| IBIT | long | $1,000 | not recorded | 20 Oct |
| MSTR 2026-11-20 C 150 | long | $2,000 | not recorded | 21 Oct |

- 1 crypto draft in Book D awaits the operator.
- The paper engine's view joins this section from mid-November.

<sub>Book D's paper decisions from the register, opened read-only. Paper only: no order path exists.</sub>

**For the Digital Assets paper (draft):** **Week to 31 Oct 2026.** BTC $70,984 (+0.7% on the week); ETH $3,549 (+0.7% on the week); SOL $177.46 (+0.7% on the week); ZEC $47.32 (+0.7% on the week). Stablecoin supply +$3.5bn on the week. Next dated event: MSCI, November 2026 Index Review announced, the first under the non-operating company rules (Strategy's inclusion decided), 11 Nov.

## Box commands, for Ari (printed, not run; inside a window)

Run them on weekdays 09:05-15:40 or 17:20-23:30 ET, or on a weekend clear of Sunday 05:00.

```
# 0. After the second chain merges, the self-deploy copies chester-backup.service
#    (the new ReadWritePaths) and daemon-reloads. The unit is a oneshot, so no restart
#    is needed unless the heartbeat names it.
systemctl --user list-timers chester-backup.timer

# 1. Once, before the first sweep that should copy the pilot's files, create the two
#    inboxes. The unit's leading "-" skips a missing directory, so they must exist.
mkdir -p ~/chester-data/inbox/x-triage ~/chester-data/inbox/x-digest

# 2. The sweep's first copy: tonight's timer run, or start it now (this runs the
#    whole sweep).
systemctl --user start chester-backup.service
grep "x pilot" ~/logs/rclone_sync-$(date +%F).log
ls -la ~/chester-data/inbox/x-triage ~/chester-data/inbox/x-digest
cat ~/chester-data/inbox/x-triage/x-attention-ledger.csv.copied_at

# 3. The first render, a dry run that sends nothing; it writes
#    reports/dryrun/weekly_digital_2026-10-16.html
cd ~/chester-reports
.venv/bin/python -m daily_cascade.digital_addendum render --week-ending 2026-10-16 --no-narrative
# and with the read (one model call):
.venv/bin/python -m daily_cascade.digital_addendum render --week-ending 2026-10-16
```

The Weekly of 25 Oct builds the page as a dry run on its own, under `reports/dryrun/`. The
Weekly of 1 Nov is the first edition, attached.

## Gates

| Gate | Result |
|---|---|
| `tools/validate_digital_addendum.py` (new; groups A-J) | **74/74** locally |
| `tools/validate_backup.py` (extended: the X pilot pull, five inboxes) | 66/66 locally |
| `tools/validate_audit_3a.py` (CLAUDE.md's counts: seventy-nine code gates, seventy-six Python) | 83/83 locally |
| `tools/check_library.py` (CLAUDE.md's paths; the paper's appendix) | 0 failures, 0 warnings |
| `tools/validate_weekly_stack.py` (extended: the link line) | CI (it renders the PDF) |
| `tools/validate_weekly_calendar.py` (extended: the calendar's marker) | CI (it renders the PDF); its hand-rows logic was exercised alone, outside the gate |
| everything else | CI |

## Files this branch shares with open branches

**Session A's chain** (`st-r5-audit` and the branches stitched under it):
- **`scripts/rclone_sync.sh`:** `alpha-lab-2` adds `pull_lab_inbox` after
  `pull_etf_archive || true`, the same anchor as `pull_x_pilot`. Keep both blocks.
- **`deploy/systemd/chester-backup.service`:** the `ReadWritePaths` line. The union is
  `... -%h/chester-data/inbox/etf -%h/backups/chains -%h/chester-data/inbox/lab -%h/chester-data/inbox/x-triage -%h/chester-data/inbox/x-digest`.
- **`tools/validate_backup.py`:** the `inboxes` tuple and its message take the union of the
  six inboxes: aaii, spdji, etf, lab, x-triage, x-digest. `len(pulls) == 3` stands only
  while the lab pull still uses `rclone copy` and not `copyto`.
- **`daily_cascade/deliver.py`:** AUD-1 changes `send_html`. The change here is
  `deliver()`'s signature and its `send_html` call, so the two should merge cleanly.
- **`daily_cascade/weekly_report.py` (AUD-2) and `daily_cascade/weekly_stack.py`
  (ST-R5):** the insertions here sit at their own anchors: before `weekly_stack.produce`,
  at the two `pdf=out.get("pdf")` sends, and under `render`'s header.
- **`tools/validate_weekly_stack.py`:** VP-1 and ST-R5 edit it. The two checks here follow
  the Content-ID check.

**The 6e line:**
- `Makefile`: one gate line after `validate_releases.py`.
- `CLAUDE.md`: the gate count, and one paragraph after the release lenses' paragraph.

**No open branch touches** `config/weekly_ahead.yaml`, `daily_cascade/ahead.py`,
`tools/validate_weekly_calendar.py` or the paper.

## Needs you

1. **Verify item 2: MSCI's effective date.**
   - MSCI's site cannot be read keylessly: robots.txt disallows the path, and the page
     answers with a browser challenge.
   - Read the November 2026 review dates in a browser.
   - Then remove the marker from the 30 Nov entry in `config/digital_asset_calendar.yaml`,
     correcting the date if it moved.
2. **How the page reaches you.**
   - It is attached to the Weekly's message as an HTML file and linked by one line. On a
     phone it opens as an attachment.
   - If you would rather have it as its own message ("[chester] Digital Assets: w/e ..."),
     say so. That is a second `deliver` call in `_stacked`.
3. **The session-set values above:** the budgets, the 30-day monthly bar, the 45-day
   window, the tier-2 class, and Book D's crypto names.
4. **The stablecoin supply prints from today.** Your list put it under "awaiting Tranche
   A", but `llama.stable_total` has been stored since the crypto basket. Keep it, or hold
   it until Tranche A?
5. **S&P DJI and Nasdaq print "date not published".** Neither publishes a review calendar a
   keyless client can read. Give me a date by hand if you want one in the calendar.
6. **Two dates rest on unread sources.** Deribit's expiries come from its rule, and the
   rows say "to verify". The 15 Nov VanEck JitoSOL date comes from the order alone.
7. **Drafts for your accept-all:** Appendix E of the Digital Assets paper, and each week's
   dated line.
8. **The pilot's limit.**
   - The ledgers are read as whole files, stamped with the sweep's copy time.
   - So a re-render of a past week, after a later copy, prints no ledger rows.
   - Item 50's Tranche 1, which moves the ledgers into the store, is the fix.

## CI

The runs on this branch's push and on `docs-batch-8` are read once and recorded here.

| Run | Branch, commit | Result |
|---|---|---|
| 39031045828 (Gates, push) | `docs-batch-8`, `1388967` | green: 84 of 84 jobs, read 17 Oct 2026 |
| 39032637251 (Gates, push) | `6e-digital`, `aff064f` | **failed: 85 of 87 jobs passed.** `tools/validate_config_refs.py` failed. `config/digital_addendum.yaml` names `calc.froth_z`, `calc.funding_agg` and `calc.oi_usd`, three Tranche A keys under a registered namespace that were not registered yet. The second failed job, `gates-passed`, only rolls up that one failure. |

**The fix, on this branch.** The three keys are registered as `status_extra: not_yet_sourced` (declared, never written), the registry's form for a planned series. `tools/validate_audit_3a.py` counts them among the keys registered one by one. Gates run locally after the fix:

| Gate | Result |
|---|---|
| `validate_config_refs` | 55/55 |
| `check_registry` | OK |
| `validate_lenses` | 49/49 |
| `validate_audit_3a` | 83/83 |

`crypto-tranche-a-1` (Tranche A part 1) then registers `calc.funding_agg` and `calc.oi_usd` for real. The CI run on this fix is recorded on that branch's notes.
