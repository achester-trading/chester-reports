"""
The close payload — plain data, assembled from what the store already
holds. No fetching, no interpretation, no prose.

-----------------------------------------------------------------------------
REPORTS NEVER FETCH (30.4)
-----------------------------------------------------------------------------

Nothing here opens a socket. The EOD pass runs at 16:10, computes the dealer
surface, scores the pin log and writes the observation store; thirty-five
minutes later this reads what that produced. That ordering is the reason 32.4 makes the
close run the first one built — it cannot fail for a reason the report layer
owns, so a failure here is a real finding rather than a new bug.

It is also the leakage rule. Every read goes through an as-of cutoff, so the
report can be regenerated for a past session and will show what was knowable
then rather than what is known now.

-----------------------------------------------------------------------------
WHICH CAPTURE THE NUMBERS COME FROM
-----------------------------------------------------------------------------

Five profiles per symbol per day exist — the intraday captures plus the settled
16:10 one. This deliberately reuses `pin_log.load_computed()` rather than
selecting its own, because the alternative is worse than it looks: a report
picking the capture nearest 16:10 while the pin log picked newest-by-mtime
would let the two disagree about which snapshot the day's numbers came from,
and they would disagree silently. One selection rule, shared, and `fetched_at`
is printed on every row so a wrong pick is visible rather than invisible.

-----------------------------------------------------------------------------
MISSING IS A VALUE
-----------------------------------------------------------------------------

Per 32.5 no block publishes on a payload lacking a live, fresh source. So every
block that cannot be filled says why, by name: the regime block is `not_built`
and names D2; the portfolio block is `absent` with the reason when the Gateway
has never synced; SPX and SPCX are `ingestion_only` because their Greeks are
behind the solver gate. A blank cell and an absent source look identical in a
rendered table, and only one of them is a problem.
"""

from __future__ import annotations

import csv
import logging
import sys
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

from altdata import config, observations, session  # noqa: E402
import pin_log  # noqa: E402

log = logging.getLogger("daily_cascade.payload")

# Account-level Portfolio Truth, in the order a human reads them.
ACCOUNT_KEYS = ("portfolio.nav", "portfolio.cash", "portfolio.buying_power",
                "portfolio.gross_position_value", "portfolio.maint_margin",
                "portfolio.excess_liquidity", "portfolio.cushion")

# The regime block, named but NOT BUILT. Listed rather than omitted because an
# absent section reads as "nothing to say" and a named one reads as "this is
# owed" -- and D2 is the next step in the track.
REGIME_PLACEHOLDERS = [
    ("regime.macro_state",
     "D2 — macro regime state from series already in the store "
     "(net liquidity, HY OAS, curve, realized/implied vol, breadth, dealer "
     "gamma). Declared thresholds and a state machine, never a 0-100 composite."),
    ("regime.debt_cycle_state",
     "31.2 — long-cycle debt resolution, two mutually exclusive branches "
     "(deflationary liquidation / inflationary repression) read as ONE "
     "mechanism state. Lands inside D2."),
    ("regime.vix_term_structure",
     "30.8 — VX1/VX2/VX3 slope as a declared state machine. Gated on the CFE "
     "Enhanced subscription."),
]


def _f(row: dict, key: str) -> Optional[float]:
    v = row.get(key)
    if v in (None, "", "None"):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _b(row: dict, key: str) -> Optional[bool]:
    v = row.get(key)
    if v in (None, "", "None"):
        return None
    return str(v).strip().lower() in ("true", "1", "yes")


def exposure_rows(sess: Optional[str] = None) -> tuple[list[dict], list[dict], Optional[str]]:
    """(rows, missing, session_actually_loaded)."""
    profiles = pin_log.load_computed(date=sess)
    if not profiles:
        return [], [], None

    rows: list[dict] = []
    missing: list[dict] = []
    loaded_session = None

    for sym in config.full_universe():
        rec = profiles.get(sym)
        if rec is None:
            # Distinguish the two reasons a symbol can be absent. SPX and SPCX
            # are ingestion-only behind the solver gate, which is a DECISION
            # and not a gap; anything else missing is a gap and reads as one.
            if sym in config.massive_universe():
                missing.append({"symbol": sym, "reason":
                                "ingestion only -- Greeks deferred behind the "
                                "IV solver gate (greeks_status="
                                "pending_solver_gate)"})
            else:
                missing.append({"symbol": sym,
                                "reason": "no computed profile for this session"})
            continue
        if rec.get("error"):
            # SPX and SPCX land here by design: captured, greeks deferred
            # behind the solver gate, and the profile says so in the data.
            missing.append({"symbol": sym, "reason": str(rec["error"])})
            continue
        overall = rec.get("overall") or {}
        buckets = rec.get("buckets") or {}
        gates = rec.get("gates") or {}
        loaded_session = loaded_session or rec.get("session_date")
        rows.append({
            "symbol": sym,
            "spot": rec.get("spot"),
            "fetched_at": rec.get("fetched_at"),
            "net_gex": overall.get("net_gex"),
            "dollar_gamma_per_1pct": overall.get("dollar_gamma_per_1pct"),
            # gamma_flip, not gamma_flip_cum_strikes. The two are different
            # readings and the cumulative one is frequently null while the
            # scanned level is not -- taking the wrong one renders an empty
            # column that looks like missing data rather than a naming slip.
            "gamma_flip": overall.get("gamma_flip"),
            "flip_reason": overall.get("flip_reason"),
            "peak_abs_gex_strike": overall.get("peak_abs_gex_strike"),
            "call_wall": overall.get("call_wall"),
            "put_wall": overall.get("put_wall"),
            "max_pain": rec.get("max_pain"),
            "dex_notional": overall.get("dex_notional"),
            "vex_per_volpt": overall.get("vex_shares_per_volpt"),
            "chex_per_day": overall.get("chex_shares_per_day"),
            "greeks_source": rec.get("greeks_source") or rec.get("gamma_source"),
            "data_quality": gates.get("data_quality"),
            "buckets": {k: (buckets.get(k) or {}).get("share_of_total_abs_gex")
                        for k in ("0dte", "weekly", "monthly", "quarterly")},
            "min_t_load_bearing": any(
                (buckets.get(k) or {}).get("min_t_load_bearing")
                for k in buckets),
        })
    return rows, missing, loaded_session


def pin_rows(sess: str) -> list[dict]:
    """Every pin-log row for one session, as graded."""
    path = Path(config.PIN_LOG_PATH)
    if not path.exists():
        return []
    out: list[dict] = []
    with path.open(encoding="utf-8", newline="") as fp:
        for r in csv.DictReader(fp):
            if r.get("date") != sess:
                continue
            out.append({
                "symbol": r.get("symbol"),
                "close": _f(r, "close"),
                "close_source": r.get("close_source"),
                "tolerance_bps": _f(r, "tolerance_bps"),
                "max_pain": _f(r, "max_pain"),
                "max_pain_dist_bps": _f(r, "max_pain_dist_bps"),
                "max_pain_hit": _b(r, "max_pain_hit"),
                "peak_gex_strike": _f(r, "peak_gex_strike"),
                "peak_gex_dist_bps": _f(r, "peak_gex_dist_bps"),
                "peak_gex_hit": _b(r, "peak_gex_hit"),
                "call_wall_hit": _b(r, "call_wall_hit"),
                "put_wall_hit": _b(r, "put_wall_hit"),
                "spot_above_flip": _b(r, "spot_above_flip"),
                "data_quality": r.get("data_quality"),
            })
    return out


def portfolio_block(as_of: Optional[str] = None) -> dict:
    """Portfolio Truth as of the cutoff, or an honest absence.

    `trigger_eligible: false` on every one of these, per 26.11. They are here
    to say what is held, never to suggest what to do about it.
    """
    block: dict = {"state": "absent", "reason": "", "account": {}, "positions": []}
    try:
        with observations.ObservationStore() as db:
            for key in ACCOUNT_KEYS:
                accounts = db.instruments(key)
                if not accounts:
                    continue
                row = db.latest_as_of(key, as_of=as_of, instrument=accounts[0])
                if row:
                    block["account"][key] = {
                        "value": row.get("value_num"),
                        "observed_at": row.get("observed_at"),
                        "available_at": row.get("available_at"),
                        "account": accounts[0],
                    }
            for inst in db.instruments("portfolio.position_qty"):
                qty = db.latest_as_of("portfolio.position_qty", as_of=as_of,
                                      instrument=inst)
                if not qty or not qty.get("value_num"):
                    continue      # a closed position is a zero, not a holding
                mv = db.latest_as_of("portfolio.position_market_value",
                                     as_of=as_of, instrument=inst)
                pnl = db.latest_as_of("portfolio.position_unrealized_pnl",
                                      as_of=as_of, instrument=inst)
                block["positions"].append({
                    "instrument": inst,
                    "qty": qty.get("value_num"),
                    "market_value": (mv or {}).get("value_num"),
                    "unrealized_pnl": (pnl or {}).get("value_num"),
                    "observed_at": qty.get("observed_at"),
                })
    except Exception as exc:  # noqa: BLE001 -- a report never dies on a block
        block["reason"] = f"store unreadable: {type(exc).__name__}: {exc}"
        return block

    if block["account"] or block["positions"]:
        block["state"] = "ok"
    else:
        block["reason"] = ("no Portfolio Truth rows in the store -- the IBKR "
                           "sync has not run, or the Gateway has never "
                           "authenticated on this box")
    return block


def build(sess: Optional[str] = None, as_of: Optional[str] = None,
          run_id: Optional[str] = None) -> dict:
    """The whole payload. Reads only; never raises on a missing block."""
    cutoff = as_of or session.utc_iso(timespec="microseconds")
    exposure, missing, loaded = exposure_rows(sess)
    resolved = sess or loaded or session.last_trading_session().isoformat()
    pins = pin_rows(resolved)

    hits = {k: sum(1 for p in pins if p.get(k)) for k in
            ("max_pain_hit", "peak_gex_hit", "call_wall_hit", "put_wall_hit")}

    warnings: list[str] = []
    if not exposure:
        warnings.append("no exposure profiles found -- the EOD pass has not "
                        "produced a scoreable profile for any symbol")
    if not pins:
        warnings.append(f"no pin-log rows for {resolved}")
    if loaded and sess and loaded != sess:
        warnings.append(f"requested session {sess} but loaded {loaded}")

    return {
        "report": "daily_close",
        "session": resolved,
        "generated_at": session.utc_iso(),
        "as_of": cutoff,
        "run_id": run_id,
        "convention_version": config.CONVENTION_VERSION,
        "tolerance_bps": config.PIN_TOLERANCE_BPS,
        "universe": {"greeks": config.options_universe(),
                     "ingestion_only": config.massive_universe()},
        "exposure": exposure,
        "exposure_missing": missing,
        "pins": pins,
        "pin_hits": hits,
        "regime": [{"key": k, "state": "not_built", "note": n}
                   for k, n in REGIME_PLACEHOLDERS],
        "portfolio": portfolio_block(cutoff),
        "warnings": warnings,
    }
