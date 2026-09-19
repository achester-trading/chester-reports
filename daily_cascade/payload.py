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
import re
import sys
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

from altdata import config, observations, session  # noqa: E402
from register import instruments            # noqa: E402
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


# A level inside an invalidation sentence. The register stores invalidation as
# PROSE by design -- "settled close below put wall 760" carries the mechanism,
# not just the number, and Part 7 wants the mechanism. So the level is parsed out
# for the distance arithmetic and the sentence is printed as written; when no
# number can be found the distance is absent and says so, rather than a zero
# standing in for "could not tell".
_LEVEL = re.compile(r"(\d[\d,]*(?:\.\d+)?)")


def invalidation_level(text: Optional[str]) -> Optional[float]:
    """The first number in an invalidation sentence, or None."""
    m = _LEVEL.search(str(text or ""))
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:
        return None


def _attach_register(positions: list[dict]) -> None:
    """Add the decision id, invalidation and distance to each held position.

    THE EXECUTION RECORD DOES NOT EXIST, and that is why fill price and
    commission are absent here rather than merely missing. Nothing in this repo
    reads IBKR executions: the three read-only services are Portfolio Truth
    (positions and balances), What-If (pre-trade) and Costs (estimates), and
    reqExecutions/ExecutionFilter appear nowhere. So there is no fill price and no
    commission to join, for any position, on any box. The fields are carried as
    None with a stated reason so the gap is visible in the report instead of
    looking like a position nobody filled.

    THE REGISTER MAY NOT BE HERE EITHER. It lives in the same database file as the
    observation store but its tables are created by the Register class, so a box
    that has never recorded a decision has no decisions table at all -- which is
    the VPS today. The block reports that by name too. Both absences are the kind
    that a blank cell would hide.
    """
    reason = None
    rows: list[dict] = []
    try:
        import sqlite3  # noqa: PLC0415
        from register import store as reg_store  # noqa: PLC0415
        conn = sqlite3.connect(reg_store.DEFAULT_DB)
        conn.row_factory = sqlite3.Row
        try:
            have = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name='decisions'").fetchone()
            if not have:
                reason = ("no decisions table in the store -- the register has "
                          "never been written on this box, so no decision id or "
                          "invalidation can be joined to a position")
            else:
                # The live head of each chain: active, and not yet superseded.
                rows = [dict(r) for r in conn.execute(
                    "SELECT id, instrument, instrument_norm, invalidation, "
                    "       status, thesis_state, note "
                    "  FROM decisions "
                    " WHERE superseded_by IS NULL AND status = 'active'")]
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001 -- a report never dies on a block
        reason = f"register unreadable: {type(exc).__name__}: {exc}"

    for p in positions:
        p["fill_price"] = None
        p["commission"] = None
        p["fill_reason"] = ("no execution record exists -- nothing in this "
                            "system reads IBKR executions (L2 builds it)")
        p["decision_id"] = None
        p["invalidation"] = None
        p["invalidation_level"] = None
        p["distance_points"] = None
        p["distance_pct"] = None
        p["thesis_state"] = None
        p["register_reason"] = reason

        if not rows:
            continue
        # MATCHING, AND WHY THE LOOSE FALLBACK IS CONDITIONAL.
        #
        # An exact instrument match is unambiguous and always wins. Falling back
        # to the normalised issuer root lets a decision written as `SPY` find a
        # holding keyed `SPY@ARCA.USD`, which is usually what is meant -- but it
        # is exactly wrong when the book holds TWO listings of one issuer, because
        # both normalise to `SPY` and the fallback would attach the same decision
        # to both. On the 17 September book that produced a peso short carrying a
        # dollar decision's 760 level and a distance of -1,628%: a number with no
        # meaning, printed in red, in the column a reader is meant to act on.
        #
        # So the fallback applies only when the root is unambiguous in the book.
        norm = instruments.normalise(p["instrument"])
        siblings = [q for q in positions
                    if instruments.normalise(q["instrument"]) == norm]
        hit = next((r for r in rows if r["instrument"] == p["instrument"]), None)
        if hit is None and len(siblings) == 1:
            hit = next((r for r in rows if r["instrument_norm"] == norm), None)
        if hit is None:
            # AMBIGUITY MEANS AN UNQUALIFIED DECISION OVER A MULTI-LISTING BOOK,
            # and nothing weaker. The test was "some active decision shares this
            # root", which was right while every decision named a bare ticker and
            # became wrong the moment one was re-designated: with an active
            # decision on SPY@ARCA.USD and a book holding SPY@ARCA.USD and
            # SPY@MEXI.MXN, the peso leg was told the register was ambiguous when
            # in fact the register was precise and simply said nothing about it.
            # Those are different facts and only one of them asks the operator to
            # go and disambiguate something.
            vague = [r for r in rows if r["instrument"] == norm]
            if len(siblings) > 1 and vague:
                p["register_reason"] = (
                    f"the register names {norm} without a listing, but the book "
                    f"holds {len(siblings)} of them "
                    f"({', '.join(q['instrument'] for q in siblings)}); which "
                    f"one the decision refers to cannot be inferred, so no "
                    f"level is attached rather than the wrong one")
            else:
                p["register_reason"] = ("no active decision in the register "
                                        "names this instrument")
            continue
        p["decision_id"] = hit["id"]
        p["invalidation"] = hit["invalidation"]
        p["thesis_state"] = hit["thesis_state"]
        lvl = invalidation_level(hit["invalidation"])
        p["invalidation_level"] = lvl
        mark = p.get("mark")
        if lvl is None:
            p["register_reason"] = ("the invalidation names no numeric level, "
                                    "so no distance can be computed")
        elif mark is None:
            p["register_reason"] = "no mark, so no distance can be computed"
        else:
            # SIGNED BY DIRECTION OF DANGER, not by arithmetic. A long is
            # invalidated BELOW its level, so the distance is mark - level and a
            # negative means the level is already breached. For a short the
            # relationship inverts, and quantity carries the direction.
            d = (mark - lvl) if (p.get("qty") or 0) >= 0 else (lvl - mark)
            p["distance_points"] = d
            p["distance_pct"] = 100.0 * d / lvl if lvl else None


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
                ccy = db.latest_as_of("portfolio.position_currency",
                                      as_of=as_of, instrument=inst)
                spot = (mv or {}).get("value_num")
                q = qty.get("value_num")
                block["positions"].append({
                    "instrument": inst,
                    "qty": q,
                    "market_value": spot,
                    "unrealized_pnl": (pnl or {}).get("value_num"),
                    # The contract's currency, not the account's. Without it a
                    # 1,313,769-peso short reads as a 1.3-million-dollar one.
                    "currency": (ccy or {}).get("value_text"),
                    "avg_cost": (db.latest_as_of("portfolio.position_avg_cost",
                                                 as_of=as_of, instrument=inst)
                                 or {}).get("value_num"),
                    "mark": (spot / q if spot is not None and q else None),
                    "observed_at": qty.get("observed_at"),
                })

        # THE REGISTER SIDE. Attached here rather than in the renderer because
        # the renderer computes nothing -- the distance to invalidation is a
        # number in the report and must therefore be a number in the payload.
        _attach_register(block["positions"])
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


# The figures the narrative may use, and NOTHING else. A narrow payload is a
# narrow surface for invention -- a number the model was never shown has to be
# fabricated to be printed, and the audit checks against exactly this set, so what
# it was shown is matchable and what it was not is not.
#
# The reference instrument is SPY because the paragraph's first job is the regime
# and the regime is read off the index. Per-symbol detail stays in the tables.
NARRATIVE_SYMBOL = "SPY"

# Part of what the metrics MEAN rather than claims about the market: the hedge
# flow is denominated per 1% move. Declared so a correct paragraph is not withheld
# over a unit. See numeral_audit.audit()'s docstring.
NARRATIVE_UNIT_CONSTANTS = [1.0]


def narrative_payload(full: dict, prior: Optional[dict] = None) -> dict:
    """The structured figures for the close paragraph, per the template's coverage.

    Built from the already-assembled close payload rather than re-reading the
    store, so the paragraph and the tables below it cannot disagree about a
    number: there is one source and the prose is downstream of it.

    `prior` is the previous session's payload when it can be built. The deltas the
    template asks for -- hedge flow versus yesterday, wall movement -- are computed
    HERE and carried as values, because the renderer computes nothing and the model
    must not either. A delta the model derived would be a figure with no payload
    counterpart, and the audit would correctly reject the paragraph for it.
    """
    def row_of(payload: Optional[dict]) -> dict:
        for r in (payload or {}).get("exposure") or []:
            if r.get("symbol") == NARRATIVE_SYMBOL:
                return r
        return {}

    now, was = row_of(full), row_of(prior)

    def delta(key: str):
        a, b = now.get(key), was.get(key)
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return round(a - b, 6)
        return None

    out: dict = {
        "session": full.get("session"),
        "prior_session": (prior or {}).get("session"),
        "symbol": NARRATIVE_SYMBOL,
        "spot": now.get("spot"),
        "prior_spot": was.get("spot") or None,
        "spot_change": delta("spot"),
        "gamma_flip": now.get("gamma_flip"),
        "spot_above_flip": (None if now.get("spot") is None
                            or now.get("gamma_flip") is None
                            else now["spot"] > now["gamma_flip"]),
        "dollar_gamma_per_1pct": now.get("dollar_gamma_per_1pct"),
        "prior_dollar_gamma_per_1pct": was.get("dollar_gamma_per_1pct") or None,
        "dollar_gamma_change": delta("dollar_gamma_per_1pct"),
        "call_wall": now.get("call_wall"),
        "prior_call_wall": was.get("call_wall") or None,
        "call_wall_change": delta("call_wall"),
        "put_wall": now.get("put_wall"),
        "prior_put_wall": was.get("put_wall") or None,
        "put_wall_change": delta("put_wall"),
        "peak_abs_gex_strike": now.get("peak_abs_gex_strike"),
        "max_pain": now.get("max_pain"),
        "net_gex": now.get("net_gex"),
        # The pin tally to date, which is the system's own scorecard.
        "pin_rows_today": len(full.get("pins") or []),
        "pin_hits_today": full.get("pin_hits"),
        # Positions, from the register join the portfolio block already did.
        "positions": [
            {k: v for k, v in pos.items()
             if k in ("instrument", "qty", "currency", "avg_cost", "mark",
                      "fill_price", "commission", "decision_id",
                      "invalidation", "invalidation_level",
                      "distance_points", "distance_pct", "thesis_state",
                      "unrealized_pnl")}
            for pos in (full.get("portfolio") or {}).get("positions") or []
        ],
        # Absences travel WITH the figures, so the paragraph can say what the
        # system does not know instead of quietly omitting it.
        "absences": [w for w in full.get("warnings") or []],
    }
    return {k: v for k, v in out.items() if v is not None and v != []}


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
