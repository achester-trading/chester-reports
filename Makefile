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
#   make figures         redraw the Currencies charts from live FX history
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
	tools/validate_iv_solver.py \
	tools/validate_daily_close.py \
	tools/validate_exec_bits.py \
	tools/validate_systemd_units.py \
	tools/check_library.py

SH_VALIDATORS := \
	tools/validate_ibgateway_watchdog.sh \
	tools/validate_heartbeat_caller.sh \
	tools/validate_session_calendar.sh

EXTRA := smoke_test.py

.PHONY: validate validate-fast list library-check html figures

# THE BUILT HTML EDITIONS. docs/html/ is output, not source: every file in it
# is generated from the .md by tools/build_paper_html.py, figures embedded.
# The editions used to be made by hand, which is how the repo ended up with a
# directory of HTML built from pre-audit .md files and a rule claiming the
# stale copy was canonical for reading. A built artifact cannot drift.
html:
	@$(PYTHON) tools/build_paper_html.py

# THE CURRENCIES CHARTS, REDRAWN FROM DATA. altdata/fx_charts.py fetches thirty
# years of FX history (or falls back to its packaged anchors under --offline)
# and draws the eight figures Part V carries. It writes fx_<key>.svg; the paper
# references fig-NN.svg, so the target renames them into place in the order the
# paper uses: comparative first, then the seven pairs.
#
# It needs matplotlib, pandas, and altdata/fx_anchors.py. Any of those missing
# is a skip, not a failure -- the committed figures under docs/figures/ are the
# fallback, and `make html` never depends on this target.
FX_FIGS := docs/figures/currencies
# One shell for the whole recipe: a skip has to skip the rename too, and make
# gives each recipe LINE its own shell, so an `exit 0` on line two would not
# stop line three from copying files that were never drawn.
figures:
	@if [ ! -f altdata/fx_charts.py ]; then \
	  echo "no altdata/fx_charts.py -- skipping"; \
	elif ! $(PYTHON) -m altdata.fx_charts --svg-dir $(FX_FIGS)/_fx; then \
	  echo "fx_charts did not run -- keeping the committed figures"; \
	  rm -rf $(FX_FIGS)/_fx; \
	else \
	  n=1; for k in comparative dxy eur jpy gbp chf cny thb; do \
	    cp "$(FX_FIGS)/_fx/fx_$$k.svg" "$$(printf '$(FX_FIGS)/fig-%02d.svg' $$n)" || exit 1; \
	    n=$$((n + 1)); \
	  done; \
	  rm -rf $(FX_FIGS)/_fx; \
	  echo "8 currency figures redrawn -- now run 'make html'"; \
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
	@echo "interpreter: $(PYTHON)"

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
	if [ $$fail -eq 0 ]; then echo "ALL GATES PASSED"; else echo "GATES FAILED"; fi; \
	exit $$fail

validate-fast:
	@set -e; \
	for v in $(PY_VALIDATORS) $(EXTRA); do echo "== $$v"; $(PYTHON) $$v >/dev/null; done; \
	for v in $(SH_VALIDATORS); do echo "== $$v"; bash $$v >/dev/null; done; \
	echo "ALL GATES PASSED"
