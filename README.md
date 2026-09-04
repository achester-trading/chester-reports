# chester-reports

A five-report market intelligence system: **Disruptive Themes**, **Monthly Macro**,
**Top & Bottom**, **Alternative Asset**, and **Daily Cascade**. Each report is an
independent generator that pulls data through the shared `altdata` ingestion
package, computes derived metrics, renders a Markdown and styled-HTML document,
and emits a compact state record to a Cloudflare Worker so a single dashboard can
show the health of all five at a glance. Monthly Macro is the pipeline that is
built today; the other four have their state keys reserved in `state/emit.py` and
are yet to be implemented.

To generate the Monthly Macro report, set `FRED_API_KEY` (and optionally
`ANTHROPIC_API_KEY` for the narrative step) and run
`python -m monthly_macro.run --verbose`; `python smoke_test.py` exercises the full
pipeline against a synthetic store with no network access. See
[CLAUDE.md](CLAUDE.md) for the repo layout, the standing rules, and the data
gotchas that bite in practice, and `docs/` for the architecture and planning
documents — `docs/architecture-v3.md` is the canonical planning document once it
is committed.
