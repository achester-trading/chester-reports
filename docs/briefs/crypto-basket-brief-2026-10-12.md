# Brief — monitoring the crypto long-shot basket across the Weekly, Monthly and Quarterly

| | |
|---|---|
| Status | **Ruled, 12 Oct 2026, 17:25 ET** — six as proposed; decision 3 as the alternative (the model restates odds each quarter beside the operator's original as the reference). Amends the Alternative Assets change order §4.6 (crypto tiers) and the Weekly's and Monthly's digital blocks. Built by session B, Tue 13 → Wed 14 Oct. |
| Owner | Ari Chester |
| Input | *Crypto long-shot basket*, 12 Oct 2026 (ten names plus Venice new and Pearl demoted; the odds of 10× and 100× over five to ten years; "what pays the token"; US exchange access; the case for and against each), itself drawn from the 10 Oct scan `docs/scans/crypto-outlook-2026-10-10.md`. |
| The ask | "In weekly, monthly, quarterly reporting, there should be some level of monitoring across this expanded box of crypto assets, in addition to the classics (Bitcoin, Solana, Ethereum, Zcash)." |

## 1. What the basket is, in the system's terms

Twelve names: SKY, LDO, SYRUP, AAVE, AERO, TAO, MORPHO, UNI, ONDO, KAS, VVV, PRL. Under the Alternative Assets change order §4.6, AAVE and TAO are already light tier (MW-6 promotions pending the operator's register writes), PRL is deep tier, and the other nine are scan tier — "no series, no page". The basket document changes two things: it names nine more tokens the operator wants watched, and it demotes PRL to a watch list on the strength of the June 2026 study (the mining does no useful AI work).

Each name in the document carries exactly what the system needs to monitor it without a model's judgment: a **measurable that pays the token** (Sky's net interest, Lido's staked ETH and buyback, Maple's AUM, Aave's revenue-to-buyback, Aerodrome's fees against its emissions, Bittensor's outside revenue against its $370M of issuance, Morpho's deposits and its unturned fee switch, Uniswap's burn, Ondo's AUM and its unproposed fee switch, Kaspa's fees, Venice's run-rate against its issuance, Pearl's one partner), a **falsifier** in the "if it fizzles" paragraph, and the operator's **odds**, which the document rightly calls judgment, not model output.

## 2. The design: a basket tier, measured not narrated

A fourth crypto tier between light and scan — **basket** — with three kinds of series per name and one hand-seeded file:

- **Price, market cap, circulating supply, drawdown from high** — daily. Prices from yfinance (the sanctioned exception; Yahoo lists all twelve as `-USD` pairs except possibly SYRUP and VVV, which fall back to the next source); market cap and supply from CoinGecko's public endpoint if its terms allow keyless reads at the basket's size (twelve calls a day), else from DefiLlama's coin price service.
- **What pays the token** — daily or weekly from DefiLlama's free API (fees, revenue, TVL per protocol — SKY, LDO, SYRUP, AAVE, AERO, MORPHO, UNI, ONDO are all listed there), with the emissions side from the same source where carried. This is CD-1 of the crypto data-sources order (`llama.py`), already ruled for the 23 Nov block — pulled forward.
- **Dilution** — annual issuance against buybacks or burns, as a ratio, from the two series above.
- **The operator's file** — `config/crypto_basket.yaml`: per name, the thesis in one line, the measurable's key, the falsifier as a measurable statement with a threshold and a date where the document gives one (Ondo's supply doubling by January 2029; Aerodrome's six-chain launch 21 October 2026; Morpho's fee switch; Kaspa's fees), US exchange access, and the odds of 10× and 100× **as the operator's prior, hand-seeded and dated** — the model never writes or revises odds. The document's case-for and case-against paragraphs are stored as the operator's thesis text, quoted, never paraphrased.

## 3. Where it prints

- **Weekly.** One table in the reference tier — the twelve names: price, week %, 30-day %, market cap, drawdown, the measurable's latest and its change — and one line in the read path only when something happened: a name past the move screen's 2.5σ, a falsifier's threshold crossed, a dated event due that week (the Aerodrome launch), or a scan item (exploit, listing, fee-switch vote). Silence otherwise; the Weekly is already long.
- **Monthly.** *Themes: digital* gains the basket block: the table at the month's resolution plus the dilution ratio, and a status line per name against its falsifier — holds / strained / failed — computed from the series where the falsifier is measurable, "not measured — <reason>" otherwise. The classics stay as they are.
- **Quarterly.** The crypto chapter's basket tier: a half-page per name — the operator's thesis and odds (quoted, dated), the measurables' quarter, the falsifier's state, dilution, US access, the scan's stories on the name — and the MW-7 promote / demote / remove criteria applied each quarter on executable depth and turnover, as §4.6 already rules for the light tier. Pearl keeps its S1–S8 signposts from SR-10 as its falsifier set, at basket tier not deep.

## 4. What this is not

Not a trade list. The basket is a five-to-ten-year judgment; its home in the books is Book A's digital sleeve, and whether the basket becomes a named sub-sleeve with its own band is a Doctrine #2 question (7–8 Nov), where the first `alt_asset` theses are seeded. Until then it is watched, measured and graded on its falsifiers, nothing more. No name enters Book B's scanner unless it is in the stored price basket and clears a pivotal point like anything else.

## 5. Decisions

1. **Create the basket tier** with the twelve names, series as §2 — yfinance prices, DefiLlama fees/revenue/TVL, market cap and supply from the free source the session verifies. **Yes — 12 Oct 2026.**
2. **Demote PRL from deep tier to basket**, keeping its SR-10 signposts as its falsifiers; the AQ change order's §4.6 is amended accordingly and no coin page is built for it. **Yes — 12 Oct 2026.**
3. **Odds: the original is the reference; the model restates each quarter.** The operator's odds of 12 Oct 2026 and the thesis text are hand-seeded, dated, and printed every quarter unchanged as the reference column. Beside them, each quarter, the model prints its own restated odds of 10× and 100× — **ruled as the alternative, 12 Oct 2026** ("re-state odds each quarter, though always include original as reference") — under three rules: a restatement may move only on a named change in a measurable or a falsifier's state (the fee switch turned on; the buyback run-rate; an exploit; a listing), with that reason in one clause; with no measurable change it prints "unchanged — no measurable moved"; and every restatement is written to the thesis register as an `alt_asset` entry under the name's family, labelled "model estimate", so the direction of each quarterly move is graded against the next quarter's measurables even though the 10× horizon itself is years out. The operator may add his own restatement as a third column at any quarter, hand-seeded. **Ruled — 12 Oct 2026.**
4. **The falsifiers are the kill conditions**: each name's "if it fizzles" becomes a measurable statement with a threshold and date where the document gives one, graded holds / strained / failed from the series; the rest print "not measured". **Yes — 12 Oct 2026.**
5. **Print as §3**: Weekly reference table plus an events-only read-path line; Monthly block in *Themes: digital* with status lines; Quarterly half-page per name with MW-7 applied quarterly. **Yes — 12 Oct 2026.**
6. **The basket's place in Book A is a Doctrine #2 decision**; until then watch and grade only. **Yes — 12 Oct 2026.**
7. **Build**: CD-1 (`llama.py`) pulled forward from the 23 Nov block and extended to the basket; session B, tomorrow night, ≈ 10 h; the basket document committed to `docs/scans/crypto-basket-summary-2026-10-12.md` as the thesis source. **Yes — 12 Oct 2026.**
