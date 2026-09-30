#!/usr/bin/env bash
#
# One-time move of the live CSV store out of the checkout (30 Sep 2026).
# deploy/systemd/README.md section 11 holds the why; this is its migration body,
# verbatim, so it can be shipped over ONE ssh connection from the laptop:
#
#   bash -c "ssh vps 'bash -s' < scripts/migrate_store.sh"
#
# RUN IT AFTER THE PUSH AND DEPLOY -- the units' sandboxes must already allow
# -%h/chester-data and altdata/store.py must already read ALTDATA_STORE from
# .env -- and at a quiet time (not 06:45-07:05 or 16:05-17:00 ET, when the
# passes write).
#
# It COPIES and never moves or deletes: data_store/ in the repo is left as it
# is, and data/, chester.db and ~/state are not touched. Safe to re-run: cp -n
# overwrites nothing, and the .env line is appended only when absent.
set -euo pipefail
cd ~/chester-reports
echo "== units that write the store (all should be inactive)"
for u in chester-overnight chester-daily-close chester-eod chester-monthly; do
  printf '  %-22s %s\n' "$u" "$(systemctl --user is-active "$u.service" || true)"
done
echo "== before: $(find data_store -type f | wc -l) files, $(git status --porcelain data_store | wc -l) untracked/changed"
mkdir -p ~/chester-data
cp -a -n data_store ~/chester-data/
diff -rq data_store ~/chester-data/data_store && echo "== copy identical to the source"
if grep -q '^ALTDATA_STORE=' .env; then
  echo "== ALTDATA_STORE already in .env; left unchanged:"
else
  printf 'ALTDATA_STORE=%s\n' "$HOME/chester-data/data_store" >> .env
  echo "== appended to .env:"
fi
grep '^ALTDATA_STORE=' .env
touch ~/chester-data/.migrated
echo "== resolves to: $(.venv/bin/python -c 'from altdata import store; print(store.DEFAULT_STORE_DIR)')"
