# The Letters' findings: the editions against themselves

The Monthly Letter and the Weekly Letter are chat-side readings of the editions.
They have no rights, and every figure in them is copied from the edition. When a
Letter finds a place where an edition contradicts itself, that is a defect in
the edition. It is fixed on the box, recorded here, and then dropped from the
Letter's prompt.

Each row is one of: **fixed** (with the commit and the check that holds it),
**not reproducible** (with the reason), or **defers to** a session (with the
reason).

## M: the Monthly of 1 Nov 2026 (fixed by A95, branch `a95-monthly-first-edition`)

| Row | The finding | Which side was right | The fix | The check |
|---|---|---|---|---|
| M1 | The executive summary's "What doesn't fit" said no contradiction was open; section 4 listed seven exceptions | Section 4 | The summary's frame carries section 4's open counts in words (`prose.summary_frame` `open_now`). A summary that says "no open contradiction / exception / gap" against a count of one or more is withheld, naming the count (`prose.misfit_count_faults`) | `validate_monthly_frames` G (M1) |
| M2 | One credit spread's month change printed three ways: the yields table, the Credit Cycle table, the pillar table | The Credit Cycle table: `v2.metric_month`, the scorecard's month, from the print on or before the previous month-end | The yields table's change read the prior as knowable at the month-end cutoff (30 Sep 23:59 UTC). FRED posts the OAS the next morning, so that prior was 29 Sep. It now reads the month-aligned prior (`weekly_stack.change_over(month_aligned=True)`, one rule: `v2.prior_target`). The pillar appendix's column is a 20-session change and is headed so; it is a different window, not a third month change, and is unchanged | `validate_monthly_frames` G (M2) |
| M3 | The header's forecast count against the scenario record's "No probability has been emitted" | Both counters are right. The header counted every forecast the probability ledger took that month (the close's outlooks, the narrative register's); the scenario record counts scenario weights only | The header line says what it counts and how many of those are scenario weights: "n forecasts emitted to the probability ledger (none of them a scenario weight)" (`stack.forecast_count_line`, the record's own filter, `SCENARIO_SOURCES`) | `validate_monthly_frames` G (M3); `validate_audit_fixes` J (M6's pinned line updated) |
| M4 | "vs cash / SPY / 60-40 since 1 Sep" printed Book Z's own ledgers as if they were the book's excess | "Against Book Z since 5 Sep" (`benchmark.book_line`), the line the Weekly prints | One sentence, `v2.book_z_sentence`, read by "Where our read lands" and the book section alike. Book Z's own ledgers, where they print alone, are labelled "each a return and not an excess". "Our read"'s slice carries the book's excess line under its own name | `validate_monthly_frames` G (M4) |
| M5 | The equity-credit gap's age differed from the Weekly's | The Weekly's: since-dates and sessions read from the stored objects (`weekly_sections.state_dates`) | The Monthly's gap table passes the same dates (`stack.misfit_section`). It had passed none and fallen back to the month object's persistence count | `validate_monthly_frames` G (M5) |
| M6 | CPI prose "rose to 4.0% from 4.1%" against a table prior of 3.7% | The date-based table | The release row's year-on-year counted 12 prints back. BLS never published October 2025, so across that gap every CPI year-on-year, and its prior, compared thirteen months. `weekly_stack.headline_form` now matches the same month a year back by date, and the month before by date for month-on-month, and prints n/a where that month was never published. Reproduced on the laptop's store copy: April 2026 reads 3.95% by position, 3.78% by date | `validate_monthly_frames` G (M6) |
| M7 | The VIX printed at two dates in one edition | Both prints are right; they were two series under one label. FRED's VIXCLS (a session behind) fed the scorecard and the themes; Yahoo's ^VIX fed the tape | The themes' FRED rows are labelled "VIX (FRED VIXCLS close, a session behind)". The new check also found "Dollar-yen" printed over FRED's DEXJPUS and Yahoo's JPY=X, now labelled the same way | `validate_monthly_frames` G (M7): no label prints two series |

## W: the Weekly of w/e 30 Oct 2026

Filed by A103 (branch `a103-weekly-consistency`).
