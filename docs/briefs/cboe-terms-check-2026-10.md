# The Cboe terms check, for Doctrine #2 (7–8 Nov 2026)

Paste B89 (`docs/pastes/B89.md`), 30 Oct 2026. Branch `b89-cboe-terms-check` from
`origin/main` at `422ea697`. **Docs only: no reader is switched off, and nothing
in code or config changes.** Ruling options are drafted D33-style, for the
operator at Doctrine #2.

## Why this check

D40 (27 Oct) ruled that Cboe's daily put/call fails the 16 Oct sources rule,
because Cboe's terms forbid storing the data "in an electronic retrieval system".
That is the clause CoinGecko was retired on. B79's notes
(`origin/b79-capitulation-count`, `docs/briefs/b79-capitulation-count-notes.md`,
needs-you 1) found that the two live Cboe readers carry only a robots record, and
named the terms URL that governs both. This file is that check.

## The pages read

All are public, read 30 Oct 2026 at 05:25 UTC with the project's generic
User-Agent. Each was read as a page; nothing was fetched from behind a refusal.
1. **https://www.cboe.com/terms**, "Terms and Conditions for Use of Cboe
   Websites", "Last Updated: November 16, 2022".
2. **https://www.cboe.com/use-of-content**, "Use of Cboe Content", linked from
   every page's footer, and the route Section 2 names for consent.
3. **https://www.cboe.com/global-disclaimers/**, "Disclaimers Related to Cboe
   Products and Services", footer "Disclaimers".
4. **The pages that link the files:**
   - https://www.cboe.com/us/indices/dashboard/dspx/ links
     `https://cdn-api.cboe.com/api/global/us_indices/daily_prices/DSPX_History.csv`,
     the very file the reader pulls.
   - https://www.cboe.com/us/indices/dashboard/cor3m/.
   - https://www.cboe.com/us/futures/market_statistics/historical_data/, the VX
     contract-history page.

   None of these pages carries terms of its own. Section 1 of the terms allows
   that a page may ("Certain sections of or pages on the Website may contain
   separate terms and conditions"), but these do not, so the site terms govern
   them and the files they link.

There is no robots refusal in the way. cdn.cboe.com and cdn-api.cboe.com answer
robots.txt with 403, which RFC 9309 reads as no rules. www.cboe.com's robots.txt
disallows `/book/` and the volume reports only. The question is the terms alone.

### The clauses, verbatim

**Terms, §2 "Copyrights, Trademarks, Service Marks, And Proprietary Rights"**:
what "Materials" covers.

> "The design and functionality of, as well as the materials and content contained in, the Website, including but not limited to documents, designs, logos, graphics, artwork, images, photographs, audio clips, video clips, databases, text, HTML and other material on the Website, including the selection and arrangement thereof, copyrights, trademarks, service marks and tradenames ("Materials") are owned, licensed, or controlled by Cboe or the party credited as the owner, licensor, or provider of such Materials."

**Terms, §2**, the operative clause:

> "You may view, print and download one copy of the Materials for your personal non-commercial use in connection with products and services offered by Cboe, provided that you maintain all copyright, trademark and other notices contained on the Materials. You may not otherwise copy, reproduce, alter, store either in hard copy or in an electronic retrieval system, license, transmit, display, broadcast, create a derivative work (for example, a financial product, service or index) from, use to verify or correct other data or information, publish, rent, sublicense, distribute, or otherwise use in whole or in part in any other manner the Materials without Cboe's prior written consent except to the extent that such use constitutes "fair use" under the "Copyright Act of 1976", as amended from time to time. To formally request such consent you must submit a Request to Use Cboe Content."

**Terms, §4 "Disclaimers"**, item (f):

> "the provision of certain portions of the Website is subject to the terms and conditions of other agreements to which Cboe is a party."

**"Use of Cboe Content"**:

> "In order to use any Cboe logo, data, photo/image or other content contained in Cboe websites (collectively "Cboe Content"), you must receive approval in advance from Cboe."

> "If Cboe approves your request, such approval will be contingent upon your execution of a license agreement. You are not approved to use Cboe Content until a license agreement has been signed by both you and Cboe."

**"Disclaimers Related to Cboe Products and Services"**, under "General":

> "No data, values, or other content contained in this document (including without limitation, index values or information, ratings, credit-related analyses and data, research, valuations, strategies, methodologies, and models) or any part thereof may be modified, reverse-engineered, reproduced, or distributed in any form or by any means, or stored in a database or retrieval system, without the prior written permission of Cboe."

### What the clauses say, for the store

The Materials include "databases" and the content linked from the site. The
"Use of Cboe Content" page names "data" outright. Read together:

| Use | Verdict | The words |
|---|---|---|
| **Storing** (the point-in-time store) | **Forbidden** without written consent | §2 "store … in an electronic retrieval system"; the disclaimers' "stored in a database or retrieval system" |
| **Redistributing** (printing values in reports that are emailed and archived) | **Forbidden** without written consent | §2 "publish … distribute … display"; the disclaimers' "reproduced, or distributed in any form" |
| **Deriving** (ratios, slopes, percentiles, flags) | **Forbidden** without written consent | §2 "create a derivative work … from, use to verify or correct other data or information … or otherwise use in whole or in part in any other manner" |
| **Allowed** | one copy, viewed or printed, for "personal non-commercial use in connection with products and services offered by Cboe", and fair use | §2 |

Fair use is a legal defence, not a permission, and no ruling has ever rested a
reader on it. The 16 Oct rule asks whether the terms allow the store, and these
do not. **Both live readers fail the rule on the same clause as the put/call
file.** The cure the terms name is a written licence (permissions@cboe.com), which
this check does not pursue: that is the operator's call (option (d) below).

## The readers

There are two live readers. A grep for `cboe.com` across `altdata/`, `config/`,
`daily_cascade/` and `tools/` finds no other code that fetches from a Cboe host.

Not live Cboe readers:
- `cboe_putcall` is on `b79-capitulation-count` only, built and switched off
  (D40).
- `yfinance_source.py`'s VIX, VIX3M, VIX9D, VIX6M, VVIX, SKEW and its ^COR1M,
  ^COR3M and ^DSPX are Yahoo reads. They are D33's matter, not Cboe readers.

### Reader 1: `altdata/sources/cboe_indices.py` (source `cboe_indices`)

- **Reads:** `https://cdn.cboe.com/api/global/us_indices/daily_prices/<SYM>_History.csv`,
  which answers 307 to `cdn-api.cboe.com`, for COR1M, COR3M and DSPX: the whole
  daily history per pull (COR from 3 Jan 2006, DSPX from 19 Jun 2014).
- **Writes:** `cboe.cor1m`, `cboe.cor3m` (CLOSE) and `cboe.dspx`. It is on
  `feeds.EXTERNAL_WRITERS` (`altdata/feeds.py:195`). Its record today is the
  robots check of 16 Oct 2026, with no terms reading.
- **Governing terms:** www.cboe.com/terms §2. The DSPX dashboard links the file
  itself.
- **Store / redistribute / derive:** forbidden / forbidden / forbidden.
- **What prints: the values.** `altdata/batch5b.py`'s dispersion panel prints
  DSPX, COR1M and COR3M as levels with dual percentiles, plus the "dispersion
  regime: high or low" flag. It appears in Mechanics, the slow layers and
  Positioning & flows. Derived figures (percentiles, the flag) print beside the
  values.

### Reader 2: `altdata/loggers/vxcurve.py` (source `cboe`)

- **Reads:** `https://cdn.cboe.com/data/us/futures/market_statistics/historical_data/VX/VX_<expiry>.csv`,
  the whole daily history of one monthly VX contract. It probes three more
  endpoints, which answer 403 and are recorded, never read around: the daily
  settlement file, the directory listing and the delayed quote.
- **Writes:**
  - `cfe.vx_settle` (per contract) and `cfe.vx1`, `cfe.vx2`, `cfe.vx3`;
  - derived: `calc.vx_front_slope` (VX2 − VX1), `calc.vx1_vix_basis` (VX1 − VIX)
    and `calc.vx_front_ratio` (VX2 / VX1);
  - `cfe.vx_probe`.

  It is a scheduled logger (`altdata/loggers/__init__.py:110`). Its record today
  is "no key, no account, no terms accepted in code", with no terms reading.
- **Governing terms:** www.cboe.com/terms §2. The historical-data page links the
  contract files and carries no terms of its own. The files are CFE's (Cboe
  Futures Exchange) data.
- **Store / redistribute / derive:** forbidden / forbidden / forbidden.
- **What prints: mostly derived figures, and one value.**
  - The vol dial's term-structure leg runs a dual (`config/market_state.yaml`,
    `term_structure`): `calc.vx_front_ratio` is the champion, beside
    `calc.vix3m_over_vix` as the challenger. The run lasts from 23 Sep to
    23 Dec 2026 with `published: challenger`. The Weekly and the Monthly print
    both legs' states and metrics (`daily_cascade/weekly_render.py:149`,
    `monthly_macro/payload.py:178`).
  - The Monthly's sentiment theme prints `cfe.vx1`, "Front-month VIX future", as
    a value (`config/monthly_themes.yaml:186`).

## Options for each, D33-style

**(a) Keep.** This option is open only if the terms allow storage for internal
use. They do not, for either reader, so (a) is **not available** under the
16 Oct rule without a licence. It is listed so the record shows it was weighed.

**(b) Keep the stored history only.** No new pulls from a date. Every Cboe key
then prints with a labelled gap: "not tracked from <date> (Cboe's terms: no
storage without a licence)".
- **Against it:** the stored rows were themselves stored against §2, so (b)
  keeps the breach's product and stops only its growth. It is the same position
  D40 rejected for CoinGecko ("its terms forbid the point-in-time store").
- **Cost:** the same as (c), delayed. Every percentile freezes, and every
  as-of read after the date goes stale.

**(c) Retire now, with substitutes.** Stop the pulls, and purge the stored rows
through the store's maintenance path (the `purge_synthetic` pattern: dry run
first, backup checked, the operator's command). Print the substitutes:

| Cboe key | Substitute | Its standing |
|---|---|---|
| `cboe.cor1m`, `cboe.cor3m` | `yfinance.mkt_cor1m`, `yfinance.mkt_cor3m`, already the panel's fallback (`config/batch5_tranche_1b.yaml:21-22`) | D33's ruling governs Yahoo. A quote with no history, so the percentiles fill from the first pull |
| `cboe.dspx` | `yfinance.mkt_dspx`, the fallback (from 22 May 2024); a realised dispersion computed from constituent prices (Batch 6 item 44's writer, "awaiting constituent prices") | Yahoo: D33's. Constituents: our own calculation from stored prices; the honest substitute, and a different measure (realised, not implied) |
| `cfe.vx1/2/3`, `calc.vx_front_ratio`, `calc.vx_front_slope` | the challenger `calc.vix3m_over_vix`, which is already published, and FRED's VIXCLS and VXVCLS (VIX and VIX3M; in the FRED pull since B79) | FRED's own terms, as every FRED series. The ratio is a proxy for the curve, as it was before 23 Sep |
| `calc.vx1_vix_basis` | **none.** The futures-to-index dislocation needs a futures price. IBKR market data on the paper account is the one keyed route, and it is not keyless | listed gap |

**(d) Ask for the licence.** This is the cure the terms name: a "Request to Use
Cboe Content" to permissions@cboe.com, with the use, display, distribution and
duration. Until a licence is signed by both parties, the readers sit under (b) or
(c). It is not a rule-30 by-hand line, but it is a third-party agreement, so it
is the operator's alone to start.

### Recommendations

- **`cboe_indices` (COR1M, COR3M, DSPX): (c), retire now.** The Yahoo fallbacks
  are already wired, so the panel keeps printing, at shorter windows. DSPX's
  honest long-run substitute is the constituent realised dispersion, which is
  already the panel's declared third leg. Pursue (d) only if the implied
  correlation's 2006 history is wanted enough to license.
- **`vxcurve` (the VX curve): (c), retire now, before 23 Dec.** The champion has
  never been published (`published: challenger`), so retiring it changes no
  printed state. The challenger, already the dial's reading, continues on FRED's
  VIXCLS and VXVCLS rather than Yahoo where both exist. The dual run ends with a
  stated reason rather than a promotion. `calc.vx1_vix_basis` becomes a listed
  gap. If the curve matters to Book C's volatility work, (d) or the IBKR route
  is the way back, not the open files.
- **Both: a dated purge of the stored rows.** It follows the same session as the
  stop, run as the operator's command after a backup, as D40's CoinGecko
  retirement implies. Recommended over (b) because (b) keeps what §2 forbids
  holding.

## The cost in the reports

What loses an input under (b) or (c):

**From `cboe_indices`:**
- **The dispersion panel** (`altdata/batch5b.py`; Mechanics, slow layers,
  Positioning & flows): falls back to Yahoo's quotes. The "dispersion regime"
  flag is withheld until Yahoo's DSPX history reaches the panel's minimum n,
  and percentiles shrink from 20-year and 12-year windows to about 2.5 years
  (DSPX) or zero (COR).
- **Item 52's volatility-event lenses** (`config/vol_event.yaml:48-49`, the
  implied-correlation and dispersion lenses): print "awaiting" (the existing line
  at `altdata/vol_event.py:439`), so each fired event's ledger row
  (`vol.event_ledger`) carries those two lenses blank. **A calibration input is
  lost, not a right.**
- **The narrative story** on dispersion (`config/narratives.yaml:368-380`):
  - its evidence move and its implied outcome are both `cboe.dspx`, a 180-day
    horizon;
  - its grade cannot resolve on a retired key;
  - the story needs its metric re-pointed to `yfinance.mkt_dspx` (a register
    change, the operator's), or its grade is void.
- **Gates:** `tools/validate_st_r4_t1b.py` runs on fixtures and is not affected.
  `tools/check_store_registry.py` would list the keys as "registered, no rows"
  until they are marked retired.

**From `vxcurve`:**
- **The vol dial's term-structure dual** (`config/market_state.yaml`, v1.7): the
  champion leg prints "absent" with its reason. **No published state changes**,
  because the challenger is published. The 23 Dec promotion would not happen, and
  the state machine's planned champion is gone. That is a rules change: v1.13,
  the next config bump.
- **The basis** `calc.vx1_vix_basis`: gone, the one input the challenger cannot
  replace.
- **The Monthly's sentiment theme row** "Front-month VIX future": a listed gap.
- **Gates:** `tools/validate_regime.py` holds the dual on fixtures, unchanged.

**Not affected:** no pre-registered ledger in `docs/ledgers/` and no Alpha Lab
spec reads a Cboe key. Searching `docs/ledgers`, `alpha/`, `config/alpha*.yaml`
and `tools/calibration` for the keys finds none. No book's rights, no Top &
Bottom input and no order gate reads one.

## Decisions for Doctrine #2

1. **`cboe_indices`:** (c) retire, recommended; (b) freeze; or (d) licence.
2. **`vxcurve`:** (c) retire before 23 Dec, recommended, with the dual ended in a
   v1.13 note; (b); or (d).
3. **The stored rows:** purge after a backup, recommended; or keep them frozen
   under (b).
4. **The dispersion story's metric:** re-point to `yfinance.mkt_dspx`, or void
   its grade.
5. **D33's shadow.** Yahoo's ^VIX, ^VIX3M, ^COR1M, ^COR3M and ^DSPX are Cboe's
   index values relayed. Whatever D33 rules for Yahoo applies to them. Where FRED
   carries the series (VIXCLS, VXVCLS, VXNCLS), FRED's pull is the substitute of
   record.
