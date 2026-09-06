# Building and Validating a Systematic Book

## Execution, Sizing, Validation, and the Mechanics That Sit Under the Doctrine

**Companion white paper — chester-reports library**
**Series placement:** Companion **XIX** — after *The Operating Doctrine* (XVIII), per the library guide. Cross-references in this paper are by name.
**Version:** 1.0 — Draft, 6 September 2026
**Status:** As-built with a forward section. Written after IBKR Gate 1 closed (5 September 2026) and the first tracked paper decision entered the register. Reread when Gate 2 (order construction) opens and again when the first hundred closed decisions exist.

---

### Reader's note

The library guide planned this paper "before IBKR Gate 1," as the specification the integration would be built to. The integration was built first, in a single weekend, and this paper is therefore written the other way round: it describes the systematic book as it *exists* — the register and its packets, the freshness gate, the expression check, the broker connection and what it refuses to do, the commission schedule verified by hand, the outcome loop — and then says what remains before the book can be trusted with an order it did not watch a human place.

That inversion is a feature. A specification written before contact with the broker would have carried the assumption, stated in an early docstring, that a client-side flag made the connection unable to trade. Contact with the broker showed the flag did no such thing; the real guarantee was the vendor's Read-Only setting plus the absence of order-placing code, and the docstring was corrected before anything was built on it. The paper records what was learned by building, because that is the only kind of validation this book believes in.

The *Operating Doctrine* is this paper's governing document. The doctrine says what the operator is to do: four books, three dials, a kill-switch ladder, twenty-nine rules. This paper says what the machinery is, how it enforces the parts of the doctrine that can be enforced mechanically, how it measures the parts that cannot, and how the whole thing is validated before, during, and after each expansion of its authority. Where the doctrine states a number — 0.35% of capital per Book C position, $1,050 on the $300,000 base — this paper says which line of code computes it and which check refuses an order that would exceed it.

The paper is long because the doctrine's rules are only as good as their enforcement, and enforcement is in the details. It is organized so that Parts I and II (the shape of the book and the register) can be read once; Parts III through V (execution, sizing, validation) are the operating reference; Parts VI and VII (tax, account and compliance mechanics) are read once and consulted when a rule bites; Part VIII is the gate ladder and the honest list of what is not yet built. Worked examples use the book's actual first decision and the actual figures from the build, because a paper about validation should not invent its evidence.

---

## Part I — The Shape of a Systematic Book

### 1.1 What "systematic" means here

A systematic book is not an automated one. The distinction is the doctrine's semi-automation contract (its Section 6.6): the machine computes, drafts, sizes, brackets, enforces, logs and measures; the operator allocates, approves, vetoes, and changes rules only at the monthly session. Every order this book has placed or will place for the foreseeable future is placed by a human hand. What makes the book systematic is that the hand cannot move without a Decision Packet, the packet cannot exist without fresh signals inside their declared half-lives, the size is computed rather than felt, the exit is written before the entry, and every outcome — including the outcome of doing nothing — is graded by the same code against the same six questions.

The architecture's own line (Part 25 of the architecture document, restated in the doctrine) is that *Claude writes the rules and does not sit in the execution path*. The systematic book takes that literally. The language model drafts packets and narrates reports; it never constructs an order, never holds a credential that could transmit one, and its outputs are gated by numeral audits before they reach the operator. The systematic part of the book is deterministic code with tests. The intelligent part of the book is a research assistant with no hands.

### 1.2 The four books as the register sees them

The doctrine's four books — Allocation, Swing, Tactical, Opportunistic — are, in the register, a single `book` field on every decision and a set of per-book constraints the code applies at write time. The field is not decoration. It selects the risk tier table, the permitted expressions, the loss-stop counters, the freshness thresholds, and the grading horizon. The same SPY position written into Book C carries a 0.35% risk figure, a five-session time stop, and a session-half-life freshness requirement on its dealer signals; written into Book B it carries 0.75%, a six-week window, and a weekly-half-life requirement on its trend signals. The register does not let a position change books after the fact. The doctrine's "behavioral fence" against the swing trade that becomes a day trade is, mechanically, the immutability of that field.

### 1.3 The capital base and what the numbers mean

The doctrine's figures are stated against $300,000 of capital at risk. The paper account the system currently observes carries a simulated $1,017,965 of NAV, because that is what IBKR's paper accounts are seeded with. The mismatch is deliberate and must be handled explicitly: **every dollar figure in the sizing calculator derives from a declared `CAPITAL_BASE` in configuration, not from the account's NAV**, so that paper trading rehearses the live book's sizes rather than a fictional one three times larger. When the live account is connected, the base becomes the live NAV, read from Portfolio Truth, and the doctrine's percentages produce the doctrine's dollars. A book that sized paper positions to $1 million of NAV would learn nothing about running $300,000.

---

## Part II — The Register: The Unit of Action and the Unit of Learning

### 2.1 What a decision is

The register's central object is a *decision*, not a trade. A decision is a recorded intention with a thesis, an edge type from the doctrine's nine-family taxonomy, a horizon from the closed set (intraday, swing, positional, strategic, structural), a direction, a size, an invalidation, and the signals it leans on. It has a status — `draft`, `active`, `closed`, `declined` — and an operator action — TAKE, DECLINE, MODIFY. A decision that is declined is still a decision. The doctrine's Rule 10, that doing nothing is a position, is enforced by the fact that a declined decision gets a row, a packet, and — as Part V describes — a graded outcome exactly as a taken one does.

The first decision in the register was written on Saturday 5 September 2026, against Friday's close, and it is used throughout this paper because it is real:

```
instrument      : SPY
direction       : long
horizon         : swing
edge_type       : positioning
size            : 100 shares
thesis          : Close pinned at flip 770.6 in negative gamma;
                  expect mean-revert toward call wall 780 early week
invalidation    : settled close below put wall 760
signals_used    : exposure.gamma_flip, exposure.call_wall_otm,
                  exposure.put_wall_otm
```

Everything that follows — the freshness check that let it through, the packet that pinned its inputs, the supersession that activated it, the expression warning it received, the commission it will pay, the shadow outcome it will be graded against — happened or will happen to that row.

### 2.2 The packet: what "immutable" means and why it matters

Every decision carries a Decision Packet, and the packet is immutable by database trigger — not by convention, not by the CLI being polite, but by an `UPDATE` or `DELETE` against the packets table aborting at the SQLite layer. The packet records the run identifier, the git commit of the code that computed the signals, whether that working tree was dirty, the `available_at` cutoff the as-of join used, a manifest of every input file with its hash and byte count, the versions of the metrics and source registries, and a hash of the canonicalized output with the volatile fields (computation timestamps) named so that a future reader can reproduce the hash rather than guess at it.

The reason for this rigor is validation, not bureaucracy. The acceptance test for the register was to replay Friday's run from its packet — same commit, same manifest, same output after canonicalization — and to prove the comparison was not vacuous by showing that a single changed input byte breaks the manifest hash. That test passed. What it buys is the ability, six months from now, to ask of any decision: *what did the system know, what code was it running, and would it produce the same recommendation today from the same inputs?* A decision whose inputs cannot be reproduced cannot be graded honestly, because the grade cannot distinguish a bad thesis from a changed input.

The first packet exposed a bug in its own construction that illustrates the standard. The manifest builder initially selected "the newest directory containing any chains," which on a Saturday pinned SPX and SPCX chain files into a SPY decision's manifest. The packet was *wrong in a way that looked identical to right* — a lineage claim for inputs the decision never used. It was fixed to walk back to the instrument's own chain, and the lesson is general: a packet that pins the wrong inputs is worse than one that pins none, because a false lineage cannot be told from a true one by inspection.

### 2.3 Supersession: how a decision changes without being edited

The doctrine's Part 7 principle — revision creates a new record, overwriting destroys the grading trail — is implemented as *supersession*. To activate the first decision (recorded as `draft`, because the register does not let the CLI create an active decision directly), the `set-status` command wrote a full new row with `status: active` and `operator_action: TAKE`, linked the original to it through `superseded_by`, and froze the original: a trigger refuses any further update to a superseded row. The successor inherited the original's data manifest by content hash — a status change consults no market data, so re-hashing that evening's chains would have pinned inputs the decision never saw — but took a fresh git commit and a fresh clock, because the operator acted now and against this code. The successor's packet recorded `code_dirty = 1`, honestly, because the CLI that wrote it was itself uncommitted at that moment.

Two consequences matter for validation. A no-op supersession is refused rather than recorded, because the doctrine counts revisions per cycle as a process metric and a record that changes nothing would inflate it. And activation *re-checks freshness*: a draft written in the morning on signals that went stale by evening cannot be activated at night. Without that re-check, `set-status` would have been a clean route around the DECISION_BLOCKED gate. The check was added when the route was noticed, which is how most of this book's guards were added.

### 2.4 DECISION_BLOCKED: the gate between report and trade

The architecture distinguishes `REPORT_OK` from `DECISION_BLOCKED`: a report can always publish with its data-quality flags shown, but a recommendation with stale or missing inputs is blocked while the report goes out. In the register this is a freshness check at write time. Every signal in `signals_used` is looked up in the metrics registry, its latest observation is fetched from the point-in-time store, and its age is compared with the registry's declared `half_life` for that metric. Session-half-life signals need the most recent completed session; intraday-half-life signals need an observation inside a declared window; macro series need an observation inside their release interval. Stale or missing signals do not prevent the decision from being *recorded* — the intention is still worth logging — but they hold its status at `draft` with a `blocked_reason`, and no supersession to `active` can proceed until the block clears.

The first Saturday dry run taught the check its first lesson in semantics. The author of this paper predicted that a Saturday decision on Friday's data would be blocked, on the theory that session-half-life signals need "today's" session. The implementer disagreed, and was right: a session half-life is assessed against the *most recent completed trading session*, which on a Saturday is Friday. Blocking would have forbidden the process the doctrine's Book B is built on — the Sunday session sets the swing thesis from Friday's close. What *did* block, correctly, was anything with an intraday half-life (portfolio NAV cannot describe a closed market) and the migrated FRED series (98 days old against a five-day release interval — the store's honest record that its imported history carries pull-time timestamps until the ALFRED backfill is done).

Two false-block bugs were also caught in that run, and they matter more than the true blocks: the lookup was passing the decision's ticker to every store, so FRED rows (which have no instrument) and portfolio rows (keyed on the account, not the traded symbol) all read as missing. A check that cries wolf is a check people learn to ignore; both were fixed before the first real decision.

### 2.5 The restriction: the one rule with two enforcement layers

Rule 25 of the doctrine — no Brookfield-family security, in any book, in any expression, for any reason — is the register's only rule enforced in two places on purpose. The Python insert path raises `RestrictedInstrumentError`. Behind it, a SQLite trigger on the decisions table refuses any row whose normalized instrument matches the restricted-instruments table, so that a raw insert from a script that never imported the register is refused too. "A schema constraint is a rule" is the architecture's phrase; the trigger is that phrase made literal.

Normalization does the derivative work rather than the list: `O:BN260918C00050000`, `BN 260918C50`, `bn.to` and `BN.PR.A` all normalize to `BN` and all block; `BEPC` deliberately does not collapse to `BEP`, because only dotted suffixes and option encodings are stripped, never trailing letters. Twenty-nine roots are listed across four tiers, generic tickers (`RA`, `INF`) route to manual review rather than hard-blocking a future unrelated issuer, and the list carries a `valid_from` on every row against the day an identity layer can resolve the 2022 rename (BAM meant the parent then and means the manager now). The list was built from the corporate structure, not a filing, and the paper says so: it needs quarterly verification against EDGAR, additions flagged, nothing ever auto-removed.

---

## Part III — Execution and Microstructure

### 3.1 The broker connection and what it refuses to do

The book is connected to Interactive Brokers through IB Gateway running headless on the production server, supervised by systemd, restarted daily at 01:00 Eastern by a timer pinned to the New York zone so that it never drifts into IBKR's 23:45–00:45 reset window, and watched by a port-level health check that distinguishes "not listening" from "listening but signed out." The connection is read-only in three separate senses, and it is worth being precise about which is which, because the build revealed that one of them was not what it claimed.

The first sense is the **absence of order-placing code**: no module in the repository calls the broker's `placeOrder`, and a test greps for it. The second is the **vendor's Read-Only API setting** in the Gateway, which causes the server to refuse order messages regardless of what any client sends. The third was supposed to be the client library's `readonly=True` flag. Reading the library showed that the flag does exactly one thing — skip fetching open orders at startup — and installs no check on order placement. A docstring had claimed otherwise. It was corrected, and the paper repeats the correction because it is the cleanest example the build produced of a safety claim that would have been *believed* until the day it mattered.

The Read-Only setting has a cost, discovered empirically: IBKR's What-If preview — commission, margin impact, buying-power delta for a contemplated order — is transmitted as an order message with a `whatIf` flag, and the server refuses it under Read-Only with the words *"The API interface is currently in Read-Only mode."* The doctrine's Gate 1.5 wanted those economics; the doctrine's Gate 1 wanted the guarantee. They cannot both be had from the vendor at once. The ruling: **Read-Only stays on through the hand-placed phase**, and the economics come from a schedule-derived estimate (Part IV) until Gate 2 lifts Read-Only by design and the code-side guards take over its job. The What-If module exists, tested against fixtures, and waits.

### 3.2 Portfolio Truth: the book observed

What the connection *does* do is observe. Every thirty minutes during the trading day, and once at the close, a sync reads NAV, cash, buying power, excess liquidity, margin requirements and every position from the paper account and writes them into the point-in-time store as observations with their own `available_at`, `source = ibkr_paper`, and a run identifier — nine rows on a flat account, thirteen once fills and commissions are added. This is the doctrine's "actual portfolio" made into data, and it is the only source in the system whose word is *authoritative* rather than *inferred*: the store's observation-type field records it as `observed`, `revision_policy: never`, invalidated only by a position change.

The first sync produced a small bug that belongs in a validation paper. The `run_id` was generated at second resolution, and a test asserting that two syncs in the same second get different identifiers failed. It was the second time that weekend a second-resolution identifier had failed the same test (the first was the store's `available_at` canonicalization), and the paper draws the general rule from it: **identity and time in this codebase are found wrong by tests, never by reading.** Every identifier and every timestamp is now microsecond UTC by construction.

### 3.3 Order placement, brackets, and the operator's three touches

Orders are placed by hand, and the doctrine's operating rhythm — a ten-minute 07:00 touch, a five-minute 10:00 touch, a five-minute close — depends on their being placeable in minutes from a prepared list with exits attached. Three mechanics make that possible and are the book's execution standard whether or not the broker ever places an order itself.

**Brackets are server-side.** A bracket is a parent order with an attached stop and an attached profit target, submitted together so that the exits exist on the broker's servers from the moment the entry fills. The operator's machine can be off; the doctrine's Rule 12 (defined risk when I cannot watch) is satisfied for equities by the bracket and for options by the structure itself. IBKR supports bracket orders natively and one-cancels-all groups for the two exits. The book's standard is that no Book B or Book C equity or futures position exists without a working bracket, and that a bracket's stop is never moved away from price (Rule 5 and the semi-automation contract's "neither" clause).

**Entries are limits, and the limit says something.** A market order tells the book nothing about the thesis; a limit is a statement about where the thesis is worth entering. The first decision illustrates the discipline and its first lapse: the registered thesis was *buy the mean-reversion from the flip toward the call wall*, and the order placed was a buy limit at 773.17 — above Friday's 770.24 close, which fills at Tuesday's open on any flat tape and is therefore, economically, a market order. The register's expression check will not catch that (it checks instrument shape, not price), but the shadow outcome will grade it: the decision's reference price is the decision-time price, and the fill's distance from it is the first entry in the execution-quality ledger. Rep one's first lesson is written into rep one.

**Good-til-canceled, staged into a closed market.** The doctrine's Sunday session stages the week's conditional orders; the paper account accepts GTC orders into a closed market and holds them `PreSubmitted` until the open. This is how a part-time book works at all: decisions are made at scheduled touches and orders rest until the market opens, rather than being placed live at the moment a thesis forms.

### 3.4 The session rule and the one-login constraint

A practical constraint surfaced on the first attempt to place an order: IBKR permits **one active session per username**, and the headless Gateway holds it. The browser's trading interface could not log in while Gateway was up; it logged in and was immediately bounced when the watchdog relaunched Gateway. The resolution was procedural and is now the standard: stop the watchdog and restart timers, stop Gateway, place the order in the browser, restart everything. The order rests on IBKR's servers throughout — Gateway is an observer, not the order's custodian — and when Gateway reconnects, Portfolio Truth catches the resting order on its next sync. The monitoring observing an event that happened during its own absence is the point-in-time store's reason for existing, and the first order proved it.

The constraint will also be the reason a second username is eventually worth having, or the reason Gate 2 arrives: an order path that does not require standing the observer down.

### 3.5 Microstructure the book actually uses

The library's *Dealer's Hand* and *Daily Cascade* papers carry the microstructure theory; this paper records the pieces the execution layer consumes.

**The closing auction is where the book's most important prices form.** The settled 16:10 capture is timed to it; the pin log grades against it; the doctrine's Book C setups are entered from the 07:00 list and exited by bracket, but their *reference* — the pin, the wall, the flip — is a closing-auction price. Change Order #3 adds the auction's own flow (NYSE-family imbalance ticks through the Gateway, with a 15:50–16:00 sampler) as the other side of the picture: dealer gamma says how the close *reacts* to a move; the imbalance says what *pushes* it. For execution, the practical rule is the doctrine's: no Book C entry after 10:30 without the 10:00 report's confirmation, and no entry into the last ten minutes at all unless the packet is explicitly a closing-auction expression.

**Options spreads are a cost the packet must pay for.** Rule 13 says no trade whose expected R is less than three times its round-trip cost in commissions, spread and slippage. For a single-name option with a $0.10 wide market, a one-lot round trip costs $0.20 of spread before commission — which on a $2.00 contract is 10% of the premium, a cost that makes a 1.5R expectation impossible. The expression check's forward work (Gate 1.5) is to read the live spread from the chain and refuse the packet's R arithmetic when the spread makes it unattainable. Until then, the rule is applied by the operator from the chain the report shows.

**The data is fifteen minutes stale at the only time that matters most.** Massive's Starter tier, the book's chain source, is delayed; at the 09:45 intraday refresh — where the day's 0DTE structure is captured — fifteen minutes is the difference between a live quote and a memory. The OPRA real-time entitlement, subscribed on 5 September, exists for that window alone. The settled 16:10 capture does not need it; by then the quotes are, in the paper's own phrase, corpses.

### 3.6 The opportunistic book's execution rules

Book D — and specifically the meme lifecycle layer that Change Order #3 admitted on condition — has execution rules stricter than the other books, because it is the only book that ends in the operator's hand in the most reflexive corner of the market:

- **Shorts default to defined-risk.** A bare short in a name whose lifecycle state is anything but exhaustion-with-borrow-improving is flagged by the expression check with the unbounded-loss note. Puts and put spreads are the default expression; the flag is the rule that keeps the book alive through the one squeeze it will eventually be on the wrong side of.
- **Short invalidation includes borrow conditions, not only price.** A packet's invalidation for a meme short states a cost-to-borrow ceiling and an availability floor read from IBKR's borrow data through the Gateway. A short whose borrow is collapsing is wrong even if the price has not moved, and the packet says so before entry.
- **Attention signals have an intraday half-life.** DECISION_BLOCKED refuses a meme entry on yesterday's mentions. The edge, where it exists, decays in hours.
- **Fifteen minutes to a packet or a pass, never on a flagged day** (the doctrine's Book D cadence). An opportunity that cannot survive the wait to the next scheduled touch was a forced flow the operator was going to be on the wrong side of.

---

## Part IV — Sizing, Cost, and the Risk Ladder as Code

### 4.1 Where the numbers come from

Every size in the book is the output of one calculation: **risk dollars ÷ distance to invalidation**. Risk dollars are the book's tier figure (ordinary, good, exceptional) times the doctrine's regime multiplier (the product of the three dials' multipliers, halved on a volatile-protocol day) applied to the declared capital base. Distance to invalidation is the packet's invalidation price against the entry. The first decision's arithmetic, had it been sized by the calculator rather than by hand as "100 shares": Book B ordinary tier is 0.75% of $300,000, or $2,250; invalidation at 760 against an entry near 770.24 is $10.24 per share; $2,250 ÷ $10.24 = 219 shares. The operator sized at 100 — under the tier, which the doctrine permits and the register records as a size decision to be graded like any other. A hand-sized position above the tier would have been refused at write time, not warned.

The dial multipliers are the doctrine's regime card, and they are stamped on every packet at write time: Macro from the Monthly composite, Volatility from the volatility framework, Gamma from the exposure engine's regime classification (Positive above the flip, Flip-zone within the declared band, Negative below). The first decision was written in a Negative-gamma regime — SPY's close sat on the flip — which the doctrine's gamma card assigns a 0.75 multiplier and which, on a volatile-protocol day, would have halved again to 0.375. The register recorded the stamp; the sizing calculator that *applies* it is Track D work and is listed in Part VIII as not yet built. Until then the multiplier is applied by the operator from the stamp the report prints, and the paper is explicit that this is the weaker enforcement the doctrine's adoption sequence anticipated.

### 4.2 Cost: the Fixed schedule, verified by hand

Rule 13 needs the round-trip cost of every packet, and the cost model needs to be true. The account is on IBKR's **Fixed** pricing for US stocks — USD 0.005 per share, $1.00 minimum per order, 1% of trade value maximum, all-in — confirmed by the operator reading the Client Portal on 5 September, because the website refuses automated fetches (a 403 to the probe) and the API does not expose which pricing structure an account is on. The configuration records the schedule, the verification date, and `source: Client Portal, hand-read by operator`. A constant with provenance is the same standard applied to the restricted-instruments list and to the SPCX listing date: declared, dated, sourced, revisited.

Applied to the first decision: 100 shares × $0.005 = $0.50, floored to the $1.00 minimum, so the entry commission should be exactly $1.00 and the round trip $2.00. When the fill's actual commission arrives through Portfolio Truth, it either equals the estimate or it does not, and the execution-quality ledger (Part V) grades the cost model itself from trade one. The paper notes what Fixed pricing means for expression choice: a 100-share equity position costs $2 round trip; a one-lot option spread on the same thesis costs more in commission and, usually, far more in bid-ask spread. Rule 13's three-times-cost bar is, for small equity positions, easy; for small option structures it is the binding constraint, and the expression check's cost line exists to say so before the packet is written.

### 4.3 The kill-switch ladder as code, and what is enforced today

The doctrine's ladder — daily −2%, weekly −4%, monthly −7%, drawdown −12% and −20%, each with a scheduled re-entry — is the book's most important safety mechanism and the one the execution layer must eventually enforce by refusing orders. Today it is enforced by the register's rule-break count and the operator's discipline, which the doctrine's adoption sequence accepts as the weaker mechanism appropriate to the hand-placed phase. What exists in code is the measurement: Portfolio Truth's NAV series is the ladder's input, and the daily, weekly and monthly deltas and the drawdown from peak are computable from the store. What does not exist is the switch — a state that, once tripped, makes the register refuse an `active` supersession for the affected books until the next scheduled session. Part VIII lists it as Track D work preceding Book B and C activation, because the doctrine's Gate C requires "a book run to rule daily," and running to rule requires the rule to be checkable in code rather than in memory.

The heat and net-exposure caps (Rule 16: 6% total open risk across B, C, D; net beta-equivalent capped at Book A's band ceiling plus 15 points) are the same shape — computable from the register's open decisions and Portfolio Truth's positions; not yet a refusal. The correlated-positions-count-once rule needs the factor mapping the doctrine describes, which is the *Positioning & Flows* paper's territory.

### 4.4 Quarter-Kelly as a ceiling the book cannot see yet

The doctrine's Rule 15 says quarter-Kelly is the ceiling, not the target, and that it is a ceiling invisible until the register has measured the edge. This paper states the measurement dependency precisely: Kelly needs a hit rate and a payoff ratio per book per regime, with a sample large enough that the estimate's error is smaller than the gap between tiers. The doctrine's minimum samples — thirty decisions before a signal family's trust changes, fifty before a size tier changes, one hundred fifty before Phase 2 — are the sample sizes at which those estimates begin to be worth acting on. The register has one decision. The paper's position is that the doctrine's Phase 1 sizes are correct *because* the edge is unmeasured, and that the promotion gates are the mechanism by which measurement earns size. Nothing in the code will move a tier; a human does, at a monthly session, on the ledger's evidence, and the change is a commit with a reason.

---

## Part V — Validation: Before, During, and After

### 5.1 The book's theory of validation

The library's *Tops and Bottoms* paper carries the calibration lessons; the architecture's Change Order carries the completion gates. This paper's contribution is to say what validation means for a *book* rather than a report, and to record what the build taught about it.

A book is validated on three clocks. **Before** a component runs in production, it passes a gate: a deterministic test that can fail, run against a fixture that cannot pass vacuously. **During** production, it is watched: freshness stamps, heartbeats, port-level health, data-quality flags that render as GAP rather than as pretended values. **After** every decision, it is graded: a shadow outcome at the decision's horizon, reconciled to real fills where fills exist, decomposed by the six questions. The three clocks are not redundant. The weekend's evidence is that the *before* gates caught definitional errors (three in the exposure engine, all resolved by comparison against a vendor), the *during* watches caught silent failures (a systemd directive the daemon ignores without warning; a display that does not exist headless), and the *after* grades will catch the errors neither can see — a thesis that was wrong.

### 5.2 Gates that can fail, and the vacuous-pass problem

The book's gates share a discipline worth stating because it was learned by violation. **A gate must be verified to fail.** The registry gate was tested by seeding an unregistered column, a count drift, and a trigger-eligibility flag without rationale, and each broke the build with a message naming the fix. The systemd validator was tested by seeding an invalid `ProtectHome` value, a directive in the wrong section, a misspelled `Restart` value, and an unknown directive — because the daemon's failure mode for all four is to log a line nobody reads and proceed. **A gate must not pass on nothing.** The exposure drift check would have passed in continuous integration because the data directory is not committed and there were no chains to compare; it now falls back to a synthetic chain through the real engine and emits the identical ninety-three fields with and without stored data. A gate that passes because it examined nothing is the outcome a gate must never have.

The IV solver's gate is the fullest example. It passes five substantive checks on unchanged thresholds — solve rate, median IV agreement, gamma-flip agreement, exact wall agreement, and dollar-gamma agreement against the vendor's profile — and it took three rounds to get there honestly. The first round was passing only because the chain it examined had no 0DTE contracts (a snapshot selected by file modification time had been taken hours after the close). The second round failed on a net-gamma comparison that the diagnosis showed was *unstable by construction*: net gamma is a small difference of two large offsetting halves, so error divided by net is arbitrary — each stratum of the comparison was tighter than their combination, which no ordinary error budget produces. The fix was to compare against gross gamma at the same 10% tolerance, and to **print the net's absolute uncertainty every run** ("net dealer gamma could be out by $315,983,913; the ratio below does not say otherwise"), because anything downstream that acts on net — distance-to-flip sizing, most obviously — must carry that uncertainty rather than inherit a friendlier ratio. The third round moved the 0DTE check to N/A at a settled capture, on the ruling that same-day contracts at 16:09 are expired or minutes from it and their gamma is not a forward-looking exposure; 0DTE greeks belong to the intraday cadence, where the contracts have life. The gate got *stricter* each round and green only on the third. That is what earned green looks like.

### 5.3 The failure classes, named

Every failure the build produced belongs to one of five classes, and the paper names them because a validation regime that does not know its enemy's face cannot recognize it next time.

1. **UTC versus session date** (three instances). The box runs in UTC, the market in Eastern time; anything keyed on `date.today()` files the evening's data under tomorrow. Killed at the root by a single `session_date()` helper that every date-keying call site now uses.
2. **File fact versus observation fact** (two instances). "Newest file" answered a filesystem question when the pipeline asked an observation-time question; the newest chain file was a post-close verification snapshot with the day's 0DTE expired off it. Selection now keys on the observation timestamp carried inside the data.
3. **Silently ignored configuration** (five instances). systemd ignores a directive in the wrong section, an invalid value, or an unknown key, and logs a line. Every shipped directive is now asserted by a validator, with an unknown-directive trap.
4. **Precision collisions in identity and time** (two instances each). Second-resolution run identifiers collide; mixed-precision timestamps sort lexicographically wrong, so that a microsecond-stamped broker row is invisible to a second-resolution cutoff — not wrong, *invisible*. Canonical microsecond UTC everywhere, with regression tests.
5. **Safety claims that were not true** (one instance). The client-library flag that did not prevent trading. Corrected by reading the library, and the general rule is that a docstring's safety claim is a hypothesis until a test or the vendor's own refusal confirms it.

The common thread is that none of the five was found by reading the code. They were found by tests that asserted something specific, by deployment onto a machine that behaved differently, or by a second source arriving at a seam. The validation regime is built around that fact.

### 5.4 Validation in production: the watches

The production server watches itself on five timers. The end-of-day heartbeat carries the run's exit code, the git commit it ran, and its elapsed time; the heartbeat checker derives its allowance from the trading calendar rather than a fixed window, so that the Tuesday after a holiday weekend is not falsely stale and a genuinely missed Wednesday is caught hours after its window. The Gateway watchdog polls the API port and writes a state file whose vocabulary matches the sync script's exit codes, so that "signed out" means the same thing to both. The Portfolio Truth sync writes a last-success file whose age is the size of the hole in the portfolio series. Off-box backup — the server's own snapshots plus a nightly file-level sync to cloud storage — is Track D's first task, because as of this draft the point-in-time store lives on one disk, and the store is now the book's memory.

### 5.5 Grading: shadow outcomes for every decision

The doctrine's ledger needs an outcome for every decision, and the book's design decision is that **every decision gets a shadow outcome at its horizon from stored prices — taken, declined and draft alike.** A declined decision is graded as if taken, at the decision-time reference price, held to its horizon or its invalidation, whichever comes first. This is the mechanism behind the doctrine's insistence that doing nothing is a position: the register can report, thirteen weeks from now, the expectancy of the decisions the operator passed on, beside the expectancy of the ones he took, and the difference is the value of his judgment at the veto. Taken decisions additionally reconcile to Portfolio Truth's fills — actual entry, actual exit, actual commission — which separates the *forecast* grade from the *execution* grade.

The six questions of the doctrine (thesis, timing, expression, size, regime change, signal degradation) plus the rule-break field are the packet's post-mortem stamp, entered through `close_decision` and categorical so that they can be counted. The architecture's Part 26.7 error decomposition supplies the categories; the execution-quality ledger (slippage against decision-time price, implementation shortfall, fill against limit) supplies the *expression* and *execution* categories with numbers rather than judgment. The first decision's likely grade is already legible: if it fills at the open on Tuesday and the mean-reversion thesis plays out, the thesis grade is good and the expression grade is poor — a buy above the close for a dip-buy thesis — and the ledger will say so in its first row.

Hypotheses are graded the same way. Change Order #3 registers seven — four closing-auction strategies, three meme strategies — as dated hypotheses in a table with the same grading path as decisions, so that a strategy can be tested against six months of collected data without a dollar at risk, and its result recorded before anyone is tempted to trade it.

### 5.6 Backtesting: what is possible and what is not

The book's backtesting position is unusually constrained, and the paper states the constraints rather than working around them.

**Positioning history mostly does not exist.** Options open interest — the input to every dealer-exposure calculation — is served by every vendor probed as a live snapshot only; the probe that established this tried three routes and found that the snapshot endpoint silently ignores a requested date. Estimate-revision history is a vendor product. Short-interest history exists twice monthly from FINRA. Auction imbalance history does not exist at all outside the exchanges' own feeds. The consequence is that the pin log, the cohort decomposition, and the closing-auction hypotheses are **forward-only**: their base rates accumulate from the day the logger started (4 September 2026 for the pin log) and cannot be reconstructed earlier. The paper's rule, learned from a $3,588-per-year vendor tier that was declined: do not buy history that would shortcut this; log forward and wait.

**The exception is worth naming.** Nasdaq's retail-activity series carries history to 2016 — the one behavioral source the book has found with a decade of record — and its derived signals can be backtested against the 2021 retail peak and the 2022 trough before they are trusted. Price history is plentiful (Massive's bars, FRED's macro series, expired-contract price bars for two years). So a *price-based* backtest of a signal with a *price-based* definition is possible; a backtest of anything defined on positioning is not, and a paper that claimed otherwise would be citing evidence it does not have.

**Walk-forward is the only honest test on the data the book does have.** A rule proposed at a monthly session runs as a challenger — in paper for rules that change size, in production for rules that only restrict — for a defined period, and is promoted or withdrawn on the ledger's evidence (the doctrine's Section 9.3 applied to rules; the architecture's champion-and-challenger applied to reports). The point-in-time store's `available_at` discipline is what makes walk-forward honest: the as-of join returns only what was knowable at the decision time, and a leakage test asserts that a row stamped after the query time is invisible. A backtest that cannot prove it did not see the future is a story, not a test.

**Minimum samples are enforced before anything is acted on.** The doctrine's thirty/fifty/one-hundred-fifty thresholds are the book's, and the register prints every figure with its sample size beside it until the threshold is met. The paper's own contribution is the base-rate honesty of the pin log's first row: 0 of 13 hits on an OpEx Friday close, after a 7-of-13 reading was traced to a numerical floor planting fictional gamma at the money. A base rate that starts at zero, honestly, is worth more than one that starts at 54% by artifact and would have read as an edge for months.

---

## Part VI — Tax and Account Mechanics

*This part describes mechanics the book must know about to choose expressions and to measure after-cost returns. It is not tax advice; the figures and rules are as generally understood for a U.S. individual account in 2026 and should be confirmed with a tax professional before they drive a decision.*

### 6.1 Why tax is an expression decision

Rule 11 says the thesis and the instrument are two decisions. Tax is the third input to the second decision, and for an index thesis it can be decisive. A one-week trade in SPY shares or SPY options produces a short-term capital gain taxed as ordinary income. The same thesis expressed in SPX options — cash-settled, European-style index options — is a Section 1256 contract: gains are taxed 60% long-term and 40% short-term regardless of holding period, marked to market at year-end, and exempt from the wash-sale rule. For an operator in a high bracket running a Book C that turns over weekly, the after-tax difference between the two expressions of an identical thesis is material, and it is a difference the expression check can compute. The same applies to equity-index and Treasury futures (1256) versus the corresponding ETFs (not), and to VIX futures and options (1256) versus VIX-linked ETNs (not).

The book's rule, to be encoded in the expression table: **for index theses in Books B and C, the 1256 expression is the default unless the packet states a reason it is worse** — liquidity in the specific strike, the cash-settlement risk on a position held into expiration, or a spread cost that Rule 13 refuses. The paper does not claim the default is always right; it claims the choice should be made and recorded.

### 6.2 Mechanics the register must model

**Wash sales.** A loss on a stock or ETF (or an option on one) is disallowed if a substantially identical position is bought within thirty days before or after, across all accounts. For a book that trades SPY in Book C and holds SPY in Book A's beta sleeve, this is not hypothetical: a Book C loss can be disallowed by Book A's ordinary rebalance. The register's forward work is a wash-sale flag on any closed loss where the instrument (or its option) reappears within the window in any book. 1256 contracts are exempt, which is a second argument for the SPX expression of index theses.

**Settlement and cash.** U.S. equities settle T+1; options T+1; the buying-power figure Portfolio Truth reads already reflects this, but a book that sells a position to fund another the same day should know the cash is not settled until the next. In a margin account this is a financing question rather than a good-faith violation, but the paper notes it because the doctrine's Book A rebalance is a set of Monday limit orders that assume the capital is free.

**Pattern day trading.** A margin account that day-trades four or more times in five business days is designated a pattern day trader and must hold $25,000 of equity. At the book's capital base this is not a constraint, but Book C's rules — which permit intraday exits by bracket — mean the designation will be acquired, and the paper records that it carries no cost at this size.

**Margin.** The account is a Reg T margin account (buying power of four times cash on the paper account confirms it). Portfolio margin, available at IBKR above a $110,000 equity threshold, prices defined-risk option spreads far more efficiently and is worth a Phase 2 evaluation once Book C's spread expressions are the majority of its decisions; it is a capital-efficiency gain, not a risk-budget change, and the doctrine's dollar figures do not move with it.

**Assignment.** SPY, QQQ and IWM options are American-style and physically settled; a short call in a spread can be assigned early around an ex-dividend date, converting a defined-risk spread into a short-stock position overnight. SPX options cannot be. This is the second reason — after tax — that the index expression is the default for a book whose operator is not at a screen.

### 6.3 Measuring after-tax return

The ledger reports before-tax expectancy by book and by regime, as the doctrine specifies. This paper adds an after-tax line, computed from the expression's tax treatment and the operator's declared marginal rates, for one purpose: the doctrine's benchmark test — active Books B, C and D against Book A alone and against a static 60/40 over four trailing quarters — is only fair after tax, because Book A's long holds and the static allocation's rare rebalances enjoy long-term treatment that Book C's weekly turnover never will. An active book that beats the benchmark before tax and loses to it after has not earned its budget.

---

## Part VII — The Compliance Boundary

### 7.1 The restriction, and why it is the register's, not the operator's

The Brookfield-family exclusion is described in Part II as a two-layer enforcement. The paper adds the reasoning: the operator's employer sits inside that corporate family, and the restriction is a condition of employment, not a preference. It is therefore enforced where a preference would not be — at the database, by trigger, on every insert, with derivative normalization so that an option on a restricted root is refused as the root is. The tail watch may monitor restricted names freely (a property-preferred series is a named tell in the tail framework); the register's *trade path* is what is closed. Monitoring is not trading, and the code knows the difference.

### 7.2 What the book must confirm with the employer, once

Corporate personal-trading policies typically go beyond a restricted list: pre-clearance for certain trades, minimum holding periods, blackout windows around the employer's own reporting, restrictions on trading names under active coverage, and a prohibition on using employer devices or networks for personal trading. This paper cannot know which apply. It records the requirement: **before any book activates on the live account, the operator confirms the employer's personal-trading policy and any constraint it imposes is encoded in the register as a rule** — a holding-period minimum as a time-stop floor, a pre-clearance requirement as a `status: pending_clearance` gate, a blackout window as a calendar entry beside the exchange holidays. A constraint that lives in the operator's memory is the kind that fails on the day it matters.

### 7.3 Separation of environments

The book runs on the operator's personal laptop and a rented server; it is reachable from a personal phone. It is never installed on, accessed from, or SSH'd into from an employer's machine, and the repository never appears in a browser on one. The ruling was made early and has been kept: an SSH session from a corporate laptop is the trading system on the employer's hardware, whatever the intent, and the separation is worth more than the convenience of a lunchtime check. The phone, on cellular, is the office-hours interface.

### 7.4 Material non-public information

The book's sources are public: exchange data through vendors, regulatory filings, public prediction markets, aggregated social data. The compliance boundary the doctrine's Rule 24 implies — no new instrument, venue, book or strategy without a written rationale and a register entry — is also a boundary on *sources*: a source that is not public, or whose provenance the source registry cannot state, does not enter the system. The claims registry (architecture Part 26.5) exists for figures that arrive in prose — an analyst's holdings count, a listing date — and every such figure is a claim with a public source until verified against that source. The book's epistemics and its compliance are, in this respect, the same discipline.

---

## Part VIII — The Gate Ladder: What Is Built, What Is Next, and What Would Change This Paper

### 8.1 The gates as they stand

| Gate | Purpose | Status (6 Sep 2026) |
|---|---|---|
| **Gate 1** — read-only integration | Portfolio Truth in the store; Gateway supervised; no code path can transmit an order | **Closed 5 Sep.** Nine account rows syncing every 30 min; Read-Only enforced by vendor + absence of code; first hand-placed order observed by the monitor after its own restart |
| **Gate 1.5** — expression and execution analytics | Cost preview, expression check, execution-quality ledger | **Partially closed.** Expression check live (first warning fired on decision #1); cost from verified Fixed schedule; What-If refused under Read-Only, deferred to Gate 2; fills/commissions ingestion and execution ledger in Track D5 |
| **Gate 2** — order construction | Code builds orders from packets; operator transmits | Not started. Preconditions: Track D complete; kill-switch enforcement in the register; Read-Only lifted by design; the `placeOrder` grep becomes an allow-list of one module |
| **Gate 3** — supervised transmission | Code transmits within a bracketed, switch-enforced envelope; operator approves per order | Not started. Preconditions: Gate 2 plus fifty closed decisions per active book with a zero rule-break count |
| **Gate 4** — unsupervised within envelope | Code transmits without per-order approval, inside a fixed daily envelope | Not scheduled. Requires Phase 2 of the doctrine's promotion ladder |

### 8.2 What is not yet built, honestly

- **The sizing calculator that applies the dial multipliers** to the tier figure and refuses an over-sized packet. The stamps exist; the arithmetic is the operator's. Track D.
- **The kill-switch state** — a tripped switch that makes `set-status` refuse activation for the affected books until the next scheduled session. The measurement exists (Portfolio Truth's NAV series); the switch does not. Precedes Gate C in the doctrine's adoption sequence.
- **Heat and net-exposure as refusals** rather than figures. Needs the correlated-position factor map from *Positioning & Flows*.
- **The wash-sale flag** and the after-tax ledger line (Part VI).
- **Shadow outcomes and the hypotheses table** (Track D5) — the one link that closes the learning loop.
- **The numeral audit on LLM prose** (Session 4-lite, Track D3) — the anti-fabrication gate that must precede any published Daily narrative. Numbers in the store are gated; prose is not, yet.
- **Employer-policy constraints** encoded as register rules (Part VII), after the operator confirms them.
- **A second broker username or Gate 2**, whichever arrives first, so that placing an order no longer requires standing the observer down.

### 8.3 What would change this paper

The paper is as-built, and as-built changes. Three events would require a revision rather than an addendum. The first is Gate 2: when code constructs orders, Part III's "what the connection refuses to do" becomes "what the envelope permits," and the guarantees move from the vendor's setting to the book's own guards, which will need their own Part V treatment. The second is the first hundred closed decisions: Part IV's Kelly section is written for an unmeasured edge, and a measured one changes the tiers, the promotion arithmetic, and the paper's tone. The third is a failure class this paper does not list — the build weekend produced five, and a validation regime that has stopped finding new ones is more likely to have stopped looking than to have run out.

---

## Appendix — Decision #1, end to end

For the record, and because the paper's examples should be reproducible:

- **Fri 4 Sep, 16:10 ET** — settled chain capture; SPY close 770.24; gamma flip 770.63, put wall 760, call wall 780 (both walls matching the vendor exactly; flip within 0.13%).
- **Sat 5 Sep, 20:40 UTC** — `decide.py record`: SPY long, swing, positioning edge, invalidation "settled close below put wall 760," three exposure signals declared. Restriction check clear. Freshness: all three signals inside their session half-life against the most recent completed session. Packet `42806b99…` pinned Friday's SPY chain by hash; `code_dirty = 0`. Status `draft`.
- **Sat 5 Sep, ~21:00 UTC** — `set-status` supersedes to `active`/TAKE; freshness re-checked and passed; successor packet inherits the manifest by content, records fresh commit and `code_dirty = 1` (the CLI itself uncommitted). Expression check: one warning, *positioning edge outlives its structure* — the walls are made of open interest that expires with the September cycle.
- **Sat 5 Sep, 21:14 ET** — order placed by hand in the paper account after standing the Gateway down for the session: Buy 100 SPY, Limit 773.17, GTC, `PreSubmitted`, order 1009493520, account DUP735780. Gateway restarted; port 4002 listening; watchdog `state=ok`.
- **Expected** — fills at Tuesday's open on any flat tape (limit above Friday's close); commission $1.00 (Fixed minimum); Portfolio Truth catches the position on its first Tuesday sync. **Expected first grades:** thesis pending; expression *poor* (entry above the level the thesis wanted to buy toward); size *under tier* (100 vs a computed 219); cost model *verified or corrected* on the first fill.

That is one decision. The paper's claim is that it is graded from birth, that its inputs can be replayed, that its rule compliance is counted, and that the next one will be measured against it. Everything else in the book is the machinery that makes that claim true at scale.
