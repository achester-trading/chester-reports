#!/usr/bin/env bash
# run_crypto_basket.sh -- the crypto basket's writers (the crypto basket brief,
# 12 Oct 2026), daily at 17:25 ET under chester-crypto-basket.service.
#
#   git pull --ff-only -> Yahoo closes and volume for the twelve
#   -> DefiLlama (the basket's protocols, caps and supply, S-1 and the chain,
#      DEX and perps series) -> the derived series (dilution, S-1 impulse)
#   -> Batch 4 Tranche A part 1 (17 Oct 2026): perp funding and OI
#      (Hyperliquid; OKX and Deribit), Bitcoin's network state, the
#      fear-and-greed index, Ethereum's gas, then S-1's share and S-3. They are
#      on feeds.EXTERNAL_WRITERS too (the weekday 16:10 pass and the freshness
#      roster); this daily run is what covers the weekend, when crypto still
#      trades. A second run the same weekday writes a later vintage of the day's
#      snapshots and nothing else (unchanged rows are dropped).
#
# After the 16:45 close capture and inside the evening window. A crypto bar is
# written once its UTC day has ended, so this run writes yesterday's; DefiLlama's
# days end at 00:00 UTC the same way. Each writer is isolated: a failure is
# logged, never fatal to the next, and the reports print what is missing by name.
# Reports never fetch: they read what this stored.
set -uo pipefail

REPO="${CHESTER_REPO:-$HOME/chester-reports}"
LOG_DIR="${CHESTER_LOG_DIR:-$HOME/logs}"
STATE_DIR="${CHESTER_STATE_DIR:-$HOME/.chester}"
mkdir -p "$LOG_DIR" "$STATE_DIR"
LOG="$LOG_DIR/crypto-basket-$(date +%Y-%m).log"
LOCK="$STATE_DIR/crypto-basket.lock"
log() { printf '%s %s\n' "$(date --iso-8601=seconds)" "$*" >>"$LOG"; }

exec 9>"$LOCK"
if ! flock -n 9; then
    log "SKIP another crypto-basket run holds the lock"
    exit 0
fi
cd "$REPO" || { log "FATAL cannot cd $REPO"; exit 1; }
git pull --ff-only >>"$LOG" 2>&1 || log "WARN git pull --ff-only failed -- running on the checked-out code"
PY="${CHESTER_PYTHON:-$REPO/.venv/bin/python}"
if [[ ! -x "$PY" ]]; then
    log "FATAL no interpreter at $PY"
    exit 1
fi

log "crypto basket at $(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
step() {
    local name="$1"; shift
    local out rc
    out="$("$@" 2>&1)"; rc=$?
    printf '%s\n' "$out" | grep -v '^INFO ' | tail -40 | sed 's/^/  /' >>"$LOG"
    [[ $rc -ne 0 ]] && log "WARN $name exited $rc"
    return 0
}
step prices "$PY" -c "from altdata.sources import yfinance_source as y; s = y.pull_crypto_basket(); print(s['success'], 'of', s['total'], 'failed', s['failed'])"
step llama  "$PY" -m altdata.sources.llama pull
step hl     "$PY" -m altdata.sources.hl
step fut    "$PY" -m altdata.sources.fut
step mempool "$PY" -m altdata.sources.mempool
step fng    "$PY" -m altdata.sources.fng
step blockscout "$PY" -m altdata.sources.blockscout
step s1_s3  "$PY" -m altdata.sources.crypto_derived
step derive "$PY" -m altdata.crypto_basket derive
log "crypto basket: done"
exit 0
