# Push day 2026-10-01, step 4 -- the method-9 regime backfill. WRITES the store.
# Sent AFTER guard.inc.sh in one connection (see the runbook). Resumable: an
# interrupted run recomputes only the sessions not yet at method-9.

echo "== box HEAD must contain the ST-3 commits"
git log --oneline -1
git merge-base --is-ancestor 1059b43 HEAD || { echo "REFUSED: deploy first (1059b43 not in HEAD)"; exit 12; }

echo "== method pin (must say match True)"
.venv/bin/python -m regime method | sed -n '1p;3,5p'
.venv/bin/python -m regime method | grep -q 'match *True' || { echo "REFUSED: method hash mismatch"; exit 13; }

echo
echo "== 1/3 features: writes the fifteen new calc.* series' history (first run is the long one)"
s=$(date +%s)
.venv/bin/python -m altdata.market_features compute 2>&1 | grep -E 'rows computed|attr_|corr_spy|infl_vol'
echo "   features took $(( $(date +%s) - s ))s"

echo
echo "== 2/3 backfill: default range (five years); about 6-7 min on this box"
s=$(date +%s)
.venv/bin/python -m regime backfill 2>&1 | tail -n 6
echo "   backfill took $(( $(date +%s) - s ))s"

echo
echo "== 3/3 the latest object's rates line and driver, then the gate"
.venv/bin/python -m regime show 2>&1 | grep -A3 '^    rates' || true
.venv/bin/python tools/validate_regime.py 2>&1 | grep -E 'FAIL|replays|passed,'
