# chester-reports -- one entry point for every gate.
#
# WHY A MAKEFILE AND NOT A SHELL SCRIPT. The list of validators lived in two
# places -- registry-check.yml and whatever anyone happened to remember -- and
# four of them had drifted out of CI entirely while still passing locally. One
# list, referenced by both, is the fix. CI iterates VALIDATORS; a human runs
# `make validate`; neither can silently hold a shorter list than the other.
#
# `make validate` RUNS EVERY GATE AND THEN REPORTS. It does not stop at the
# first failure, because the question a human asks after a change is "what did
# I break", not "what did I break first". CI answers the same way, via
# fail-fast: false on the matrix.
#
#   make validate        every gate, keep going, summarise at the end
#   make validate-fast   stop at the first failure (for a tight edit loop)
#   make list            what would run
#   make library-check   the white paper library's gate, on its own
#   make html            rebuild docs/html/ from the papers' .md
#   make figures         redraw the Currencies charts into build/ and report
#   make figures ADOPT=1 ...and replace docs/figures/currencies/ with them
#
# PYTHON defaults to the venv, which is where PyYAML and pandas live. A bare
# `python` on this repo's authoring machine has neither, and the failure looks
# like a broken validator rather than a missing interpreter.

PYTHON ?= $(shell test -x .venv/bin/python && echo .venv/bin/python \
                  || (test -x .venv/Scripts/python.exe && echo .venv/Scripts/python.exe \
                  || echo python))

# THE ONE LIST. Adding a validator means adding it here; registry-check.yml
# reads this file rather than keeping its own copy.
PY_VALIDATORS := \
	tools/check_registry.py \
	tools/validate_register.py \
	tools/validate_packets.py \
	tools/validate_backup.py \
	tools/validate_ibkr_portfolio.py \
	tools/validate_ibkr_costs.py \
	tools/validate_ibkr_whatif.py \
	tools/validate_daily_close.py \
	tools/validate_morning_anchor.py \
	tools/validate_numeral_audit.py \
	tools/validate_deploy.py \
	tools/validate_derived.py \
	tools/validate_prices.py \
	tools/validate_horizon_charts.py \
	tools/validate_secrets.py \
	tools/validate_regime.py \
	tools/validate_base_rates.py \
	tools/validate_claims.py \
	tools/validate_structure_compare.py \
	tools/validate_weekly.py \
	tools/validate_monthly.py \
	tools/validate_events.py \
	tools/validate_grader.py \
	tools/validate_executions.py \
	tools/validate_exec_bits.py \
	tools/validate_systemd_units.py \
	tools/validate_official_sources.py \
	tools/validate_em_scorecard.py \
	tools/validate_imf_ifs.py \
	tools/validate_narratives.py \
	tools/validate_config_refs.py \
	tools/validate_enforce.py \
	tools/validate_rollup.py \
	tools/validate_benchmark.py \
	tools/validate_crypto_basket.py \
	tools/validate_stack.py \
	tools/validate_prediction_markets.py \
	tools/validate_weekly_stack.py \
	tools/validate_monthly_stack.py \
	tools/validate_quarterly_stack.py \
	tools/validate_quarterly_gates.py \
	tools/validate_alt_asset_scan.py \
	tools/validate_thesis_register.py \
	tools/validate_attribution.py \
	tools/validate_voices.py \
	tools/validate_weekly_edits.py \
	tools/validate_weekly_complete.py \
	tools/validate_feeds_scheduled.py \
	tools/validate_readability.py \
	tools/validate_stack_cadence.py \
	tools/validate_figure_budget.py \
	tools/validate_move_screen.py \
	tools/validate_no_filler.py \
	tools/validate_edition_consistency.py \
	tools/validate_audit_fixes.py \
	tools/validate_weekly_fixes_8.py \
	tools/validate_weekly_fixes_9.py \
	tools/validate_weekly_integrity.py \
	tools/validate_batch3_a.py \
	tools/validate_st_r5_rates.py \
	tools/validate_st_r5_index.py \
	tools/validate_st_r5_t1_rest.py \
	tools/validate_by_hand_audit.py \
	tools/validate_monthly_frames.py \
	tools/validate_weekly_storyline.py \
	tools/validate_weekly_opener.py \
	tools/validate_weekly_calendar.py \
	tools/validate_weekly_analytics.py \
	tools/validate_book_b_scanner.py \
	tools/validate_exposure_edges.py \
	tools/validate_dealer_block.py \
	tools/validate_vol_event.py \
	tools/validate_dealer_vendor.py \
	tools/validate_system_metrics.py \
	tools/validate_gtm.py \
	tools/validate_st_t1_rest.py \
	tools/validate_st_t2_rates.py \
	tools/validate_st_t3_calib.py \
	tools/validate_a43_render.py \
	tools/validate_opening_setup.py \
	tools/validate_a47_chain3.py \
	tools/validate_a48_batch11.py \
	tools/validate_secondary_notes.py \
	tools/validate_aq3_series.py \
	tools/validate_basis_proxy.py \
	tools/validate_rates_anchors.py \
	tools/validate_ai_fcf.py \
	tools/validate_sr38_inbox.py \
	tools/validate_correlation_layer.py \
	tools/validate_lenses.py \
	tools/validate_6e_rest.py \
	tools/validate_releases.py \
	tools/validate_releases_b.py \
	tools/validate_st_t5_prl.py \
	tools/validate_st_t5_render.py \
	tools/validate_digital_addendum.py \
	tools/validate_crypto_sources.py \
	tools/validate_audit_3a.py \
	tools/validate_audit_2.py \
	tools/validate_audit_1.py \
	tools/validate_backups.py \
	tools/validate_meme_ingest.py \
	tools/validate_ledgers_b6.py \
	tools/validate_outliers.py \
	tools/validate_quality.py \
	tools/validate_fred_history.py \
	tools/validate_alpha.py \
	tools/validate_alpha_no_orders.py \
	tools/validate_alpha_proposer.py \
	tools/validate_alpha_lab_3.py \
	tools/validate_volume_profile.py \
	tools/validate_es_block.py \
	tools/validate_st_r4_t1.py \
	tools/validate_st_r4_t1b.py \
	tools/validate_security_master.py \
	tools/check_library.py \
	tools/validate_gates.py

# DATA GATES -- a DIFFERENT KIND OF CHECK, and the distinction is the point.
#
# A code validator returns the same verdict forever given the same source, so a
# failure is unambiguously a regression in the commit under test. A DATA GATE's
# verdict depends on the data currently on this box: it reads a captured chain and
# reports what it finds, so the answer moves when the market moves and when a
# capture lands, with no code change at all.
#
# Running both under one exit code made this suite red for reasons outside the
# commit -- validate_iv_solver reporting median |IV diff| 0.02147 against a 0.02
# bound is a true finding about a real chain that no commit caused and none can
# fix. A suite that is red for reasons outside the change is a suite people stop
# reading, and then the code validators are worth nothing.
#
# So data gates run in their own pass and REPORT. They do not set the exit code.
# That is not a way to hide a failure: every one still runs, still prints its full
# verdict, and `make data-gates` exits on them for anyone who wants that. The
# THRESHOLD IS UNTOUCHED -- widening it would be the dishonest fix, since the bound
# is what keeps SPX out of the Greeks universe.
#
# Each gate here must also DECLARE itself with GATE_KIND = "data" in its own
# source, and tools/validate_gates.py asserts this list and those declarations
# agree. Without that, this list is just a place to quietly park a failing code
# validator.
DATA_GATES := \
	tools/validate_iv_solver.py \
	tools/validate_base_rates_store.py \
	tools/validate_monthly_store.py \
	tools/validate_regime_store.py \
	tools/validate_weekly_store.py \
	tools/validate_imf_china.py \
	tools/validate_vendor_divergence.py \
	tools/validate_backup_crypt.py

SH_VALIDATORS := \
	tools/validate_ibgateway_watchdog.sh \
	tools/validate_heartbeat_caller.sh \
	tools/validate_session_calendar.sh

EXTRA := smoke_test.py

.PHONY: validate validate-fast data-gates list list-code list-data library-check deploy html figures mechanism-register

# THE BUILT HTML EDITIONS. docs/html/ is output, not source: every file in it
# is generated from the .md by tools/build_paper_html.py, figures embedded.
# The editions used to be made by hand, which is how the repo ended up with a
# directory of HTML built from pre-audit .md files and a rule claiming the
# stale copy was canonical for reading. A built artifact cannot drift.
html:
	@$(PYTHON) tools/build_paper_html.py

# THE MECHANISM-WATCH REGISTER'S RENDERED VIEW (ST-15): from the store's
# mechanism_watch table; never edited by hand.
mechanism-register:
	@$(PYTHON) -m altdata.mechanism_watch render --out docs/mechanism-watch-register.md

# THE CURRENCIES CHARTS, REDRAWN FROM DATA -- INTO build/, NOT INTO docs/.
#
# altdata/fx_charts.py draws the eight figures Part V carries. It writes
# fx_<key>.svg; the paper references fig-NN.svg, so the target renames them in
# the order the paper uses -- comparative first, then the seven pairs.
#
# THE TARGET DOES NOT TOUCH docs/figures/. It renders into build/, prints what
# changed, and stops. That is not caution for its own sake: the repo's
# generator is behind the one that drew the committed figures (it ignores the
# anchor dataset's curated marks and defaults to live daily data where the
# committed set is the offline reconstruction the captions describe), so a
# plain refresh would silently replace a curated figure with a worse one and
# falsify its caption at the same time. See CLAUDE.md's Known cleanup.
#
#   make figures            render + report, docs/figures/ untouched
#   make figures ADOPT=1    render + report, then replace docs/figures/
#
# ADOPT=1 is a deliberate act with follow-on work: the captions in
# docs/figures/currencies/index.md and the paper's Part V note both describe
# the reconstruction, and a daily-data edition falsifies both.
#
# It needs matplotlib, pandas, and altdata/fx_anchors.py. Any of those missing
# is a skip, not a failure -- `make html` never depends on this target.
FX_FIGS := docs/figures/currencies
FX_BUILD := build/figures/currencies
# One shell for the whole recipe: a skip has to skip the rename too, and make
# gives each recipe LINE its own shell, so an `exit 0` on line two would not
# stop line three from copying files that were never drawn.
figures:
	@if [ ! -f altdata/fx_charts.py ]; then \
	  echo "no altdata/fx_charts.py -- skipping"; \
	elif ! $(PYTHON) -m altdata.fx_charts --svg-dir $(FX_BUILD)/_fx; then \
	  echo "fx_charts did not run -- nothing built, docs/figures/ untouched"; \
	  rm -rf $(FX_BUILD)/_fx; \
	else \
	  n=1; for k in comparative dxy eur jpy gbp chf cny thb; do \
	    cp "$(FX_BUILD)/_fx/fx_$$k.svg" "$$(printf '$(FX_BUILD)/fig-%02d.svg' $$n)" || exit 1; \
	    n=$$((n + 1)); \
	  done; \
	  rm -rf $(FX_BUILD)/_fx; \
	  echo; $(PYTHON) tools/diff_figures.py $(FX_FIGS) $(FX_BUILD); echo; \
	  if [ "$(ADOPT)" = "1" ]; then \
	    cp $(FX_BUILD)/fig-*.svg $(FX_FIGS)/; \
	    echo "ADOPTED -- $(FX_FIGS)/ replaced. Now reconcile the captions in"; \
	    echo "  $(FX_FIGS)/index.md and the paper's Part V note, then 'make html'."; \
	  else \
	    echo "$(FX_BUILD)/ built; $(FX_FIGS)/ untouched."; \
	    echo "  Re-run as 'make figures ADOPT=1' to replace the committed set."; \
	  fi; \
	fi

# The white paper library's own gate, on its own target because it is the one
# a human runs while editing a paper rather than while editing code. It is in
# PY_VALIDATORS too, so `make validate` and CI both run it without a second
# list to keep in step.
library-check:
	@$(PYTHON) tools/check_library.py

list:
	@echo "python:"; for v in $(PY_VALIDATORS) $(EXTRA); do echo "  $$v"; done
	@echo "shell:";  for v in $(SH_VALIDATORS); do echo "  $$v"; done
	@echo "data:";   for v in $(DATA_GATES); do echo "  $$v"; done
	@echo "interpreter: $(PYTHON)"

# The two lists CI needs separately: code gates decide the build, data gates
# report. Printed bare, one per line, so the workflow can build two matrices from
# them without parsing the human-readable `list` output.
list-code:
	@for v in $(PY_VALIDATORS) $(EXTRA) $(SH_VALIDATORS); do echo "$$v"; done

list-data:
	@for v in $(DATA_GATES); do echo "$$v"; done

validate:
	@fail=0; \
	for v in $(PY_VALIDATORS) $(EXTRA); do \
	  printf '%-44s' "$$v"; \
	  if $(PYTHON) $$v >/tmp/chester-validate.$$$$ 2>&1; then echo "PASS"; \
	  else echo "FAIL"; fail=1; sed 's/^/    | /' /tmp/chester-validate.$$$$ | tail -12; fi; \
	  rm -f /tmp/chester-validate.$$$$; \
	done; \
	for v in $(SH_VALIDATORS); do \
	  printf '%-44s' "$$v"; \
	  if bash $$v >/tmp/chester-validate.$$$$ 2>&1; then echo "PASS"; \
	  else echo "FAIL"; fail=1; sed 's/^/    | /' /tmp/chester-validate.$$$$ | tail -12; fi; \
	  rm -f /tmp/chester-validate.$$$$; \
	done; \
	echo; \
	dfail=0; \
	for v in $(DATA_GATES); do \
	  printf '%-44s' "$$v"; \
	  if $(PYTHON) $$v >/tmp/chester-data.$$$$ 2>&1; then echo "PASS"; \
	  else echo "VERDICT  (data gate -- reported, not counted)"; dfail=1; \
	    sed 's/^/    | /' /tmp/chester-data.$$$$ | tail -14; fi; \
	  rm -f /tmp/chester-data.$$$$; \
	done; \
	echo; \
	if [ $$fail -eq 0 ]; then echo "ALL CODE GATES PASSED"; else echo "CODE GATES FAILED"; fi; \
	if [ $$dfail -ne 0 ]; then \
	  echo "A DATA GATE REPORTED A FINDING -- see above. This does NOT fail the"; \
	  echo "suite: its verdict is about the data on this box, not about the code."; \
	  echo "Run 'make data-gates' to exit non-zero on it."; \
	fi; \
	exit $$fail

# The data gates ALONE, exiting on them. For anyone who does want a non-zero on a
# data finding -- a nightly data-quality run, or an operator checking whether the
# solver has come back inside its bound -- without that verdict reddening every
# code change in between.
data-gates:
	@fail=0; \
	for v in $(DATA_GATES); do \
	  echo "== $$v"; \
	  $(PYTHON) $$v || fail=1; \
	done; \
	exit $$fail

# CODE gates only, stopping at the first failure. Data gates are deliberately
# absent: this target exists for a tight edit loop, and a finding about the box's
# chains is never what the current edit broke.
validate-fast:
	@set -e; \
	for v in $(PY_VALIDATORS) $(EXTRA); do echo "== $$v"; $(PYTHON) $$v >/dev/null; done; \
	for v in $(SH_VALIDATORS); do echo "== $$v"; bash $$v >/dev/null; done; \
	echo "ALL CODE GATES PASSED  (data gates: make data-gates)"

# ---------------------------------------------------------------------------
# THE DEPLOY -- ONE LINE, BECAUSE THE BODY IS scripts/deploy.sh.
# ---------------------------------------------------------------------------
#
# WHY THE TARGET EXISTS AT ALL. Deploying was a dozen ad-hoc ssh commands typed
# differently each time, which is both slow to approve and impossible to
# allowlist: you cannot grant "the safe deploy" permission to a shape that
# changes on every run. One fixed body can be granted once, and anything outside
# it stays behind a prompt. The narrowness IS the feature.
#
# WHY THE BODY IS NOT HERE. It was, and it could not run from either machine:
# `make` is absent on the laptop (a stock Windows box, as this file warns above)
# and the box is the only place make exists -- but the box cannot resolve `vps`,
# which is the LAPTOP's ssh alias for the box. Unrunnable in both directions.
# Moving it out also shed the make-escaping layer that hid a `set -o pipefail`
# under dash until the first real deploy died on it.
#
# EVERYTHING ELSE ABOUT THE DEPLOY IS DOCUMENTED IN THE SCRIPT -- and in
# scripts/deploy_remote.sh, the box half it ships over one ssh connection -- and
# asserted by
# tools/validate_deploy.py: the six steps and their order, the declared
# DEPLOY_TIMERS list (which omits the held-back ibgateway units), the fact that no
# stop, disable, restart or kill is ever executed, and the exit codes -- 0 clean,
# 3 a changed running unit needs the printed restart, 4 drift still reported after
# the copy, 1 the pull or copy failed.
#
# NOTHING ABOUT THE DEPLOY IS CONFIGURED HERE. DEPLOY_HOST, DEPLOY_REPO,
# DEPLOY_UNIT_DIR and DEPLOY_STATE_DIR used to be declared in this file and were
# quietly inert once the recipe became a delegation: make variables are not
# exported to a recipe's child process, so `make deploy DEPLOY_HOST=other` read
# like an override and still deployed to vps. They are ENVIRONMENT variables the
# script reads, with its own defaults:
#
#     DEPLOY_HOST=staging bash scripts/deploy.sh
#
# On a machine without make, run the script directly -- or
# `bash scripts/make.sh` for the gate and html targets above.
deploy:
	@bash scripts/deploy.sh
