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
	tools/validate_systemd_units.py

SH_VALIDATORS := \
	tools/validate_ibgateway_watchdog.sh \
	tools/validate_heartbeat_caller.sh \
	tools/validate_session_calendar.sh

EXTRA := smoke_test.py

.PHONY: validate validate-fast list

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
