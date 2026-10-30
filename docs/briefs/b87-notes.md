# B87 notes: three follow-ups

Paste B87 (`docs/pastes/B87.md`, committed on `b85-crypto-derived-keys` as
`c082c7c2`), 29 Oct 2026.

Bases:
- `b86-chain-8-assembly` at `72b969f0` (Part 0);
- `b85-crypto-derived-keys` at `ea32b154` (Part 1);
- main at `422ea697` (Part 2, this branch: `b87-yields-direction`).

## Part 0: edgar_bdc on the assembly (D42.14), `4e6814df`

`altdata/sources/edgar_bdc.py` (b70) joins validate_secrets' `SEC_UA_CALLERS`.
- It reads data.sec.gov's company concepts and www.sec.gov's company_tickers.json.
- This is the same one-line registration A59 and A66 made, so the gate's rule
  is unchanged.
- b70 itself is not touched.
- validate_secrets passes; check_registry: OK.
- Recorded in `docs/briefs/b86-chain-8-notes.md` as a stitch fix.

## Part 1: the two keys (D42.9), `f864e8f6` on b85-crypto-derived-keys

The two keys B85's notes named are `calc.leverage_z` and `calc.oi_mcap_z`. They
share `calc.flag_leverage_crowded`'s missing input: 60 observations in 90 days of
an aggregate that began with the first pull.

Each now carries the flag's declaration in `member_overrides`:
- `status_extra: gap`;
- `declared_until: 2026-12-16`;
- the same `gap_reason`.

Group P of validate_crypto_sources checks that the two carry the flag's own date
and reason.

Gates:
- validate_crypto_sources: 123 passed;
- validate_a47_chain3: 42;
- check_registry: OK;
- validate_feed_repair: 50.

## Part 2: block:plumbing:yields, class (i)

**The evidence.** The Monthly's second dry run (29 Oct; the laptop's log, not
committed) withheld the block twice as tape_rules:

- **Attempt 1:** "The curve flattened as 2s10s narrowed −18 bp to 29 bp even as the
  long end backed up, a split between the front and the belly ...", withheld
  "direction audit failed on 1 clause: '... even as the long end backe': 'up'
  with a fall".
- **Attempt 2:** the same sentence with "the long end firmed", withheld
  "'firmed' with a fall".

**Why the draft is right.** "Backed up" and "firmed" describe the long end, which
rose: the draft's first sentence gives the 30-year at +11 bp. 2s10s narrowed by
18 bp, as written. Every figure and every direction is true, so the check misread
the sentence: class (i).

**Cause.** `daily_cascade/direction.py` splits a sentence into clauses at commas,
semicolons, colons, dashes, "while" and "whereas". It then reads each directional
word against the nearest signed change in its clause. "Even as" was not a split,
so the long end's word shared a clause with the spread's −18 bp and was read
against it.

**The fix, narrow.** `_CLAUSE` also splits at "even as", a contrastive clause
opener like "while".
- A word in an "even as" clause is read against a figure of its own clause.
- With none, it is not checked: the existing rule for any clause with no figure.
- No word, sign rule or lexicon entry changed.

**Fixtures** (`tools/validate_audit_fixes.py`, after the direction checks):
- **Must pass:** both dry-run drafts ("backed up" and "firmed"), against 2s10s
  −18 bp and the 30-year +11 bp.
- **Must still fail:**
  - "The 10-year rose −12 bp to 4.10% even as the curve flattened." (the 10-year
    said to rise when it fell);
  - "... as 2s10s widened −18 bp even as the long end backed up." (a word
    against its own clause's figure);
  - "The long end backed up even as the 10-year rose −12 bp." (the same, after
    the split).

**Gates:**
- **validate_audit_fixes:** 138 passed, 1 failed. The three B87 checks pass. The
  one failure is B84's looking_ahead check: the overlap of A88's role audit with
  B84's check, red on main at `422ea697` before this branch. A91's fix (on
  `a90-monthly-dryrun-2`, `f8819b62`) is not on this base.
- **validate_monthly:** 360 passed, 1 skipped (no bash and flock on the laptop).
- **validate_readability:** 67 passed.
- **validate_stack:** did not finish on the laptop inside 590 seconds,
  with no verdict; CI runs it.

**The next dry run:** the yields block's sentence publishes. A word that
disagrees with its own clause's figure is still withheld.
