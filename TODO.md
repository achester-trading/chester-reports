# TODO

- Decide narrative thinking/effort config after first Opus 5 monthly render.

## Probe verdict, 4 Sep 2026

FlashAlpha key verified live on the `basic` plan (`/v1/account`), not from the
published tier table.

- **Basic serves**: `/v1/exposure/levels/{sym}` (aggregate levels only) and
  `/v1/options/{sym}` (expiry-keyed strike grid, no OI or exposure values).
  Plus `/v1/account` and `/health`.
- **Growth-gated**: per-strike exposure (`/v1/exposure/gex`), `/exposure/summary`,
  `/exposure/zero-dte`, `/flow/gex`, `/flow/dealer-risk`.
- **Alpha-gated**: `/flow/oi`, `/flow/signals`.
- **Not in the published API at all**: any Indic-module or liquidation endpoint.
- **Rate limit**: live `X-RateLimit-Limit: 250`/day, which settles the docs
  (100) vs SDK page (250) conflict in favour of 250.
- **OI staleness**: unmeasurable on Basic — no OI field is exposed on any
  reachable endpoint. A 60s intraday diff showed the strike grid frozen and
  `gamma_flip` moving only while spot also moved, which is consistent with
  recompute over a settled OI base rather than live OI.

Net: per-strike exposure, OI, and customer/dealer polarity all require Growth
or Alpha. **Upgrade decision pending price.** Until then FlashAlpha Basic is
the independent cross-check on our own computation, not a data source.
