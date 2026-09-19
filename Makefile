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
	tools/validate_backup.py \
	tools/validate_ibkr_portfolio.py \
	tools/validate_ibkr_costs.py \
	tools/validate_ibkr_whatif.py \
	tools/validate_daily_close.py \
	tools/validate_morning_anchor.py \
	tools/validate_numeral_audit.py \
	tools/validate_executions.py \
	tools/validate_exec_bits.py \
	tools/validate_systemd_units.py \
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
	tools/validate_iv_solver.py

SH_VALIDATORS := \
	tools/validate_ibgateway_watchdog.sh \
	tools/validate_heartbeat_caller.sh \
	tools/validate_session_calendar.sh

EXTRA := smoke_test.py

.PHONY: validate validate-fast data-gates list list-code list-data library-check html figures

# THE BUILT HTML EDITIONS. docs/html/ is output, not source: every file in it
# is generated from the .md by tools/build_paper_html.py, figures embedded.
# The editions used to be made by hand, which is how the repo ended up with a
# directory of HTML built from pre-audit .md files and a rule claiming the
# stale copy was canonical for reading. A built artifact cannot drift.
html:
	@$(PYTHON) tools/build_paper_html.py

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
