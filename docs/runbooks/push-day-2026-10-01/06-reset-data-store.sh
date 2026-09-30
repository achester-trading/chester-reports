# Push day 2026-10-01, step 6 -- put the checkout's data_store/ back to the
# committed snapshot. DRY RUN unless CONFIRM=1. Sent AFTER guard.inc.sh in one
# connection (see the runbook). Deletes untracked files only after proving:
#   - the resolved store is ~/chester-data/data_store;
#   - the new store has been written since the migration and the repo copy has not;
#   - every file about to be reset or removed has a copy in the new store at
#     least as long as the repo's.

new_store="$HOME/chester-data/data_store"
m="$HOME/chester-data/.migrated"

resolved=$(.venv/bin/python -c 'from altdata import store; print(store.DEFAULT_STORE_DIR)')
echo "== the store resolves to: $resolved"
[ "$resolved" = "$new_store" ] || { echo "REFUSED: not the new store"; exit 20; }

n_new=$(find "$new_store" -type f -newer "$m" | wc -l)
n_old=$(find data_store -type f -newer "$m" | wc -l)
echo "== written since migration: new store $n_new, repo data_store $n_old"
[ "$n_new" -gt 0 ] || { echo "REFUSED: the new store has not been written since the migration"; exit 21; }
[ "$n_old" -eq 0 ] || { echo "REFUSED: something still writes the repo's data_store/"; exit 22; }

mapfile -t changed < <(git status --porcelain -uall data_store | cut -c4-)
echo "== ${#changed[@]} path(s) differ from the committed snapshot"
missing=0
for p in "${changed[@]}"; do
  rel=${p#data_store/}
  if [ ! -f "$new_store/$rel" ]; then
    echo "  NO COPY: $p"; missing=$((missing + 1))
  elif [ "$(wc -l < "$new_store/$rel")" -lt "$(wc -l < "$p")" ]; then
    echo "  SHORTER COPY: $p"; missing=$((missing + 1))
  fi
done
[ "$missing" -eq 0 ] || { echo "REFUSED: $missing path(s) have no complete copy in the new store"; exit 23; }
echo "  every one has a copy in the new store at least as long"

echo
echo "== would reset (tracked, modified):"
git status --porcelain data_store | grep -v '^??' | sed 's/^/  /' || true
echo "== would remove (untracked):"
git clean -nd -- data_store | sed 's/^/  /'

if [ "${CONFIRM:-0}" != "1" ]; then
  echo
  echo "DRY RUN -- nothing changed. Rerun as CONFIRM=1 (see the runbook)."
  exit 0
fi

git checkout -- data_store/
git clean -fd -- data_store/
echo
echo "== after: $(git status --porcelain -uall data_store | wc -l) path(s) differ (expect 0)"
git status -sb | head -n 1
