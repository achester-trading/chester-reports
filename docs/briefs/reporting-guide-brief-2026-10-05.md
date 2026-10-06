# Brief — The Reporting System: A Reader's Guide (System shelf)

Commissioned 5 Oct 2026. Audience: the operator, reading on an iPhone or at a desk, who wants to know what each report is, where its numbers come from, what it may and may not say, and how the reports learn. Prose first; a cheat-sheet table after any taxonomy or matrix (library presentation standard, Sep 2026). ~10–12k words. Timeless body; everything dated (timers, thresholds, reading budgets, the current source list) in a dated appendix policed by the library gate. Cross-references by paper name, never numeral; Doctrine rules as "Doctrine Rule N". Numeral: the next free one on the System shelf per the library guide's roster.

Parts:

I. What the system is for — one regime, one store, one register; "code establishes facts and measures outcomes" (the organising principle, R-7); the reports as the operator's news consumption replaced.

II. The data the system holds — the store and its three clocks; the point-in-time and vintage rules; the feed families with what each contributes: prices (daily OHLC and intraday bars), FRED, the official writers (Treasury, Fed, TIC, CFTC, EIA, MoF, CFETS, SAFE…), external (UMich, French, Damodaran, Shiller, World Bank, LBMA, FINRA, AAII), loggers (retail sentiment, consensus, short interest, WallStreetBets, ZEC), prediction markets (Polymarket, Kalshi — rights and the calibration-archive gate), fed funds futures, the option chain capture and what is computed from it (GEX, DEX, walls, max pain, SPY's own IV and put/call), the voices scan. One table: family → series → cadence → which report reads it.

III. The market-state object — eight dimensions, three dials, the contradiction table (the gap z-score explained for a reader), exceptions, persistence rules; the dial-to-Doctrine regime mapping and Transition; why no report recomputes regime.

IV. The reports and the ten-section stack — the stack's ten sections and what each answers; the depth matrix per cadence and the computed "deep" triggers; the daily close (16:45), the Weekly (Sunday 05:00), the Monthly (1st) with Monthly v2's storyline, themes, voices and "where our read lands"; the Quarterly Structural; Disruptive Themes; Top & Bottom; the Thailand quarterly. For each: what it reads, what it writes (ledger entries, scorecard rows, change marks), reading budget, the charts it carries and the chart-and-prose rule.

V. How the prose is made honest — code computes, the model copies: the level list, the audits (numeral, label, ordinal, signed, scaled display, banned phrases, policy words, plain-language rule), withhold-with-reason and the one retry, "no stored source, not printed", attributions vs causes.

VI. The scans — what each is, when it runs, what it may do: the daily voices and news scan (06:15; public sources; extraction; the voices register and status computation; the four stories' evidence); the Monthly signal scan (25th; the signal-triage intake template and register, SR-nn; rights limited to narrow flag, modifier, base-rate row, voices entry); the quarterly read of J.P. Morgan's Guide to the Markets (6th of Jan/Apr/Jul/Oct; deltas against a reference table; borrow list → rulings → change order); the Saturday crypto mechanism scan; the AI-risk consensus-drift scan. The rule that none has decision rights and all route through rulings in chat.

VII. The register and the books — Decision Packets, supersession, Books A–D and Book Z (cash, SPY, 60/40), the gate at entry and the risk limits, rule breaks, reconciliation against Portfolio Truth, the heat view, P&L and currency rules (INC-6, INC-8 as lessons).

VIII. The intraday layer — DTH-1 as ruled: a tactics layer for Books B and C, at most two paper engines (dealer-positioning/0DTE first, scheduled-event second), the registration requirements (mechanism, base rate, N ≥ 40, the fixed kill criterion), engine trades as graded ledger entries never orders, the 6b state vector.

IX. How the system learns — the probability ledger and Brier against the coin's 0.25; base-rate outlooks as baselines; graded calls; the dealer scorecard and its flags; the five-tier change ladder with N = 20 and one tier per cadence; the Red Team's objective (v0 the packet rule; v1 gated); the attention budget (7 packets, one 2-hour sitting, the three counts); incidents into the Doctrine's dated appendix; the Doctrine monthly and the Audits as the sittings where values are ratified.

X. Reading the reports — the reading targets (5/20/40 minutes), change marks, collapse rule, "not yet tracked" footnotes, the glossary; a reading order for a busy week.

Appendix A (dated): timers and windows; the current thresholds and budgets (from config/reporting_stack.yaml, risk_limits.yaml); the current source list; the chart sets. Appendix B: the incident log to date. Appendix C: assumptions and falsifiers (standard chapter).

Figure 1: the data-flow diagram — feeds → store → state object → reports → register → ledger → grading → Doctrine — drawn as SVG under docs/figures/<slug>/ with an index.md.

Sources to read before writing: CLAUDE.md; docs/market-state.md; docs/briefs/reporting-stack-brief-2026-10-02.md; docs/briefs/monthly-v2-brief-2026-10-01.md; docs/briefs/metric-lenses-brief-2026-10-01.md; docs/change-order-enterprise-layer-2026-09-27.md; docs/change-order-jpm-gtm-2026-10-03.md; docs/briefs/doctrine-monthly-2026-10-minutes.md; docs/workplan-v3-2026-10-02.md; docs/incidents.md; config/*.yaml; deploy/systemd/README.md; the Doctrine and Daily Cascade papers for consistency. Where a scan's prompt is not in the repo (the Monthly signal scan, the GTM read, the crypto and AI-risk scans), describe it from this brief's Part VI and mark the appendix row "schedule per the scheduled task".
