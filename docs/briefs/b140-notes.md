# B140: the DTH-1 day-trading rules order filed (Addendum A to Amendment #5, D63; 7 Nov 2026)

Paste B140 (`docs/pastes/B140.md`). The base is `origin/b129-five-filings` at
`fec1e5a3` (as expected), so the rulings file of 6 Nov is present.
`b140-dth1-rules` is a new branch from it, and merges Monday with the filings.

## What was filed

- **The order.** `docs/change-order-dth1-day-trading-rules-2026-11-06.md`, under
  "## 0. Filing (paste B140; ruled 6 Nov 2026, 09:17 ET, D63)", in B129's shape:
  - a header table: file, status, encoding, precedence, supersedes, totals, built by;
  - section 0: D1's encoding, D1 to D7 with D3 and D5 as ruled, D8, D9 and the
    placement;
  - then the order's body, unedited but for D9's redaction.
- **The attachment.** `docs/pastes/B140-attachment-dth1-rules.md`, with the same
  redaction.
- **The attachment's location.** It was not loose in Downloads. It was inside
  `weekend-pastes-2026-11-06.zip` and was extracted from there.
- **The index line** (`docs/change-orders.md`, 6 Nov 2026): "DTH-1 day-trading
  rules (Addendum A to Amendment #5, D63): thirteen execution rules plus the view
  line; the 07:00 plan block, the close's rule-by-rule check, the Weekly
  compliance scorecard; the Doctrine's DT rules section after Doctrine #2".
- **D63**, appended verbatim to `docs/briefs/rulings-2026-11-06.md`.
- **One attention-log row.**

## The redactions (D9)

Section 1 of the order and of the attachment copy had three figures, each
replaced in place:
- the loss in dollars on one ES, now "[dollar figure redacted, D9]";
- the exposure of one ES, now "[exposure figure redacted, D9]";
- the account value, now "[account value redacted, D9]".

The ES levels (7700, 7668, 7570, 7620) and "roughly 17% of the account" stay. No
committed file of this paste carries a dollar figure, an account value or an
exposure figure.

## The 30 Oct rules file

`docs/es-day-trading-rules-2026-10-30.md` is **not present** on main, nor on this
branch's base. No header line was added. The order's header records it as
superseded once W4 and W5 land, and notes that it is not in the repository.

## The gates

| Gate | Result |
|---|---|
| `check_registry` | OK |
| `check_library` | 27 papers, 0 failures, 0 warnings |
| `change_orders_index --check` | the index and the register cell agree with the tree |
| `check_master_guide` | 14 passed, 0 failed |

`check_master_guide` warns that the Guide is as of 29 Oct, older than the newest
change order. That is chain-13's refresh.

## CI

Read once after the push.
