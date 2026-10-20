# After-hours earnings: continuation or fade — pre-registration (October 2026)

*Written and committed on 19 Oct 2026, before any of its scoring code, by session A on branch `a49-secondary-notes`. **Never edited.** A change is a new registration in a new dated file. The spec is the secondary-notes order (`docs/change-order-secondary-notes-2026-10-19.md`), section 4.2 and decision D4, ruled 19 Oct 2026, 14:14 ET.*

## The question

When a captured name reports after the close, does the first move continue or fade over the next session? This is report-only: it grants nothing and builds no composite.

## The names and the prints

- **The names:** the captured single names, the options universe (`altdata.config.chain_universe()`) less the index funds SPY, QQQ and IWM.
- **The prints:** each report whose stated time is after the 16:00 close.
  - The first edition reads report dates and times from Yahoo's earnings calendar (the one yfinance import): after the close means a stated time at or after 16:00 ET.
  - A print whose time is unknown is not scored and is counted as such.

## The measure

**Two samples, read apart and never pooled:**
1. **The first edition, a labelled proxy from five years of daily bars:**
   - the first move is **the report day's close to the next open**;
   - the follow-through is **the next open to the next close**.
2. **The evening note's own readings:**
   - the first move is **16:00 to 21:30**: the 16:00 close to the last after-hours trade the note sees by 21:30, from yfinance's pre- and post-market bars (key `calc.after_hours_move`);
   - the follow-through is **21:30 to the next close**: that price to the next session's 16:00 close.

**The outcomes:**
- **Continues:** the two moves have the same sign and the first is not zero.
- **Fades:** the two moves have opposite signs.
- **Not scored:** a print with a first move of zero or a missing price. It is counted as such.

## The pass rule

- **A sample passes** when the continuation share over all its scored prints has a Wilson 95% interval that excludes 50%, with **30 scored prints at least**.
- **The verdict:** INSUFFICIENT under 30, FAIL otherwise.
- **Per name:** the share and n print for each name as descriptive rows. No per-name test is made.
- **Alongside:** the mean follow-through after continuing and after fading prints too, with its n.

## The rights

**None.** A PASS is reported. It reaches the register only as a rule-31 draft, and it grants no reading, flag, dial or decision. The evening note's after-hours block prints the move against the implied move, never this ledger's verdict, unless Ari rules otherwise on the evidence.
