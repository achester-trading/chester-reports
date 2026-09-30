# Push day 2026-10-01, step 5 -- G-33: xlrd into the box's venv, then confirm
# ACM reads fresh. WRITES the store (the official pull). Sent AFTER
# guard.inc.sh in one connection (see the runbook).

echo "== before"
.venv/bin/python -c 'import xlrd; print("xlrd already present", xlrd.__version__)' 2>/dev/null \
  || echo "xlrd absent (G-33)"

echo
echo "== install the requirements.txt pin only -- nothing else in the venv moves"
.venv/bin/python -m pip install --quiet 'xlrd>=2.0,<3.0'
.venv/bin/python -c 'import xlrd; print("xlrd", xlrd.__version__)'

echo
echo "== the official writers (ACM among them), through the feeds' own path"
s=$(date +%s)
.venv/bin/python -m altdata.feeds pull --only official 2>&1 | tail -n 25
echo "   official pull took $(( $(date +%s) - s ))s"

echo
echo "== ACM in the store (healthy: observed_at within the last few sessions, stale <= allowance)"
.venv/bin/python - <<'PY'
from altdata import derived
for k in ("acm.term_premium_10y", "acm.fitted_yield_10y"):
    d = derived.derived_forms(k)
    print("  %-26s observed %s  level %s  stale %s/%s sessions  n=%s" % (
        k, d["observed_at"], d["level"], d["staleness_sessions"],
        d["staleness_allowance_sessions"], d["n"]))
PY
echo
echo "== feeds check, official family"
.venv/bin/python -m altdata.feeds check 2>&1 | grep -iE 'official|acm' || true
