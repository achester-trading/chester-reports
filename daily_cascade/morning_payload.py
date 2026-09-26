"""
The 07:00 morning-anchor payload — plain data, read only from the store.

Same contract as the close payload and for the same reason (30.4): nothing here
opens a socket. altdata/sources/overnight.py fetches at 06:45 and this reads what
it wrote fifteen minutes later. A render that fetched would fail for transport
reasons and then report them as market facts.

WHAT THE 07:00 READER IS ASKING, AND THE ORDER THE BLOCKS ANSWER IT IN
----------------------------------------------------------------------
    1  Overnight    what moved while I was asleep, and where
    2  Exposure     what the dealer surface looked like at the prior settle
    3  Pins         whether yesterday's levels held
    4  Portfolio    what I am actually carrying into it

Two of those four are about YESTERDAY, deliberately. The prior close's exposure
state is the structure this morning's futures are moving inside, and yesterday's
pin verdicts are the only scored evidence available before the cash open. Neither
is recomputed here -- both come from the close run's own readers, so the 07:00
and 16:45 reports cannot disagree about a number they both print.

MISSING IS A VALUE, AND AT 07:00 IT IS THE COMMON CASE
------------------------------------------------------
The overnight fetch is the first thing in the chain that can fail, and it fails
for ordinary reasons: Yahoo rate-limits, a symbol goes stale, the box's network
drops at 06:45. So every block carries a state and, when it cannot be filled, the
reason by name -- and a block whose source is absent is ABSENT, not blank. A
blank cell and a missing source look identical in a rendered table and only one
of them is a problem.

STALENESS IS CHECKED, NOT ASSUMED. Overnight rows are useless once the cash
session opens; the payload therefore records how old the fetch is and flags rows
older than MAX_FETCH_AGE_MINUTES rather than printing yesterday's overnight read
as though it were this morning's. A report that silently shows stale levels is
worse than one that shows none.
"""

from __future__ import annotations

import json

import datetime as dt
import logging
import sys
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import regime  # noqa: E402
from altdata import observations, session          # noqa: E402
from altdata.sources import overnight as on        # noqa: E402
from . import events_block                         # noqa: E402
from daily_cascade import payload as close_payload  # noqa: E402

log = logging.getLogger("daily_cascade.morning_payload")

# Past this, an overnight row is not this morning's news. The fetch runs at 06:45
# and the render at 07:00, so anything over an hour old means the 06:45 timer did
# not run -- which the heartbeat also reports, but the report must not print the
# numbers as current while that is being sorted out.
MAX_FETCH_AGE_MINUTES = 75

# Display order, which is the order the question is asked in: US futures first
# because that is what the session will open on, then the vol and macro terms
# that explain them, then the sessions that already happened, then crypto.
DISPLAY_ORDER = ("ES=F", "NQ=F", "^VIX", "DX-Y.NYB", "^TNX", "JPY=X",
                 "^N225", "^STOXX50E", "^FTSE", "BTC-USD")

LABELS = {
    "ES=F": "S&P futures", "NQ=F": "Nasdaq futures", "^VIX": "VIX",
    "DX-Y.NYB": "Dollar index", "^TNX": "US 10y yield", "JPY=X": "USD/JPY",
    "^N225": "Nikkei 225", "^STOXX50E": "Euro Stoxx 50", "^FTSE": "FTSE 100",
    "BTC-USD": "Bitcoin",
}

# The windows, in the order they happened overnight, plus the residual last.
ATTRIB_ORDER = ("tokyo", "europe", "other")


# TWO DAYS AHEAD for the anchor: today's calendar and tomorrow's, which is what a
# 07:00 reader can act on. The Weekly asks the same table for nine.
EVENTS_AHEAD_DAYS = 2


def _age_minutes(available_at: Optional[str], now: Optional[str] = None):
    """Minutes between a row's available_at and now. None if unparseable."""
    if not available_at:
        return None
    try:
        a = dt.datetime.fromisoformat(available_at.replace("Z", "+00:00"))
        n = (dt.datetime.fromisoformat(now.replace("Z", "+00:00")) if now
             else dt.datetime.now(dt.timezone.utc))
    except (TypeError, ValueError):
        return None
    if a.tzinfo is None:
        a = a.replace(tzinfo=dt.timezone.utc)
    if n.tzinfo is None:
        n = n.replace(tzinfo=dt.timezone.utc)
    return (n - a).total_seconds() / 60.0


def overnight_block(as_of: Optional[str] = None,
                    db_path: Optional[str] = None) -> dict:
    """One row per instrument: level, prior settlement, change, and its age.

    Every read goes through the as-of cutoff, so the block can be rebuilt for a
    past morning and will show what was knowable then.
    """
    block: dict = {"state": "absent", "rows": [], "attribution": [],
                   "gap_attribution": None,
                   "reason": None, "fetched_at": None, "stale": []}
    try:
        store = observations.ObservationStore(db_path)
    except Exception as exc:  # noqa: BLE001 -- a report never dies on a block
        block["reason"] = f"store unreadable: {type(exc).__name__}: {exc}"
        return block

    try:
        newest_available: Optional[str] = None
        for symbol in DISPLAY_ORDER:
            slug = on.SYMBOLS.get(symbol)
            if not slug:
                continue
            got: dict = {"symbol": symbol, "label": LABELS.get(symbol, symbol)}
            found = False
            for field in ("last", "prior_settle", "chg", "chg_pct"):
                row = store.latest_as_of(on.registry_key(slug, field),
                                         as_of=as_of, instrument=symbol)
                if not row:
                    continue
                found = True
                got[field] = row.get("value_num")
                if field == "last":
                    got["observed_at"] = row.get("observed_at")
                    got["available_at"] = row.get("available_at")
                    if (newest_available is None
                            or (row.get("available_at") or "") > newest_available):
                        newest_available = row.get("available_at")
            if not found:
                continue
            age = _age_minutes(got.get("available_at"), as_of)
            got["age_minutes"] = age
            # A stale row is REPORTED AND MARKED, not dropped. Dropping it would
            # make a dead 06:45 timer look like a market with nothing to say.
            if age is not None and age > MAX_FETCH_AGE_MINUTES:
                got["stale"] = True
                block["stale"].append(symbol)
            block["rows"].append(got)

        for symbol in on.CONTINUOUS:
            slug = on.SYMBOLS.get(symbol)
            legs: dict = {"symbol": symbol, "label": LABELS.get(symbol, symbol)}
            any_leg = False
            for name in ATTRIB_ORDER:
                row = store.latest_as_of(on.registry_key(slug, f"attrib_{name}"),
                                         as_of=as_of, instrument=symbol)
                if row:
                    any_leg = True
                    legs[name] = row.get("value_num")
            if any_leg:
                block["attribution"].append(legs)

        # THE GAP-ATTRIBUTION RECORD, READ AND NOT DERIVED. 31.3(a)'s line names
        # the window that dominated, and that name is computed once by the 06:45
        # pass that wrote the legs. Deriving it here would make the anchor a second
        # producer of the same fact -- the thing the whole "read the object, never
        # recompute" rule exists to prevent -- and two producers of one label is
        # exactly how a report and a store come to disagree about last night.
        rec = store.latest_as_of(on.GAP_RECORD_KEY, as_of=as_of)
        if rec and rec.get("value_text"):
            try:
                block["gap_attribution"] = json.loads(rec["value_text"])
            except Exception as exc:                           # noqa: BLE001
                block["gap_attribution"] = {
                    "absent_reason": f"unparseable record: "
                                     f"{type(exc).__name__}: {exc}"}
        else:
            block["gap_attribution"] = {
                "absent_reason": ("the 06:45 pass wrote no attribution record for "
                                  "this cutoff -- it computes the record, and this "
                                  "anchor reads it rather than deriving a second "
                                  "one")}

        block["fetched_at"] = newest_available
        if block["rows"]:
            block["state"] = "stale" if block["stale"] else "ok"
        else:
            block["reason"] = (
                "no overnight rows in the store -- the 06:45 fetch has not run, "
                "or it ran and every symbol failed. "
                "`python -m altdata.sources.overnight --dry-run` says which.")
    except Exception as exc:  # noqa: BLE001
        block["state"] = "absent"
        block["reason"] = f"store unreadable: {type(exc).__name__}: {exc}"
    finally:
        try:
            store.close()
        except Exception:  # noqa: BLE001
            pass
    return block


def build(sess: Optional[str] = None, as_of: Optional[str] = None,
          run_id: Optional[str] = None, db_path: Optional[str] = None) -> dict:
    """The whole morning payload. Reads only; never raises on a missing block."""
    cutoff = as_of or session.utc_iso(timespec="microseconds")

    # The morning of session S reports on the close of S-1. `sess` names the
    # session being opened, so the backward-looking blocks read the one before.
    this_session = sess or session.session_date()
    try:
        prior = session.previous_trading_session(this_session).isoformat()
    except Exception:  # noqa: BLE001
        prior = session.last_trading_session().isoformat()

    overnight = overnight_block(as_of=cutoff, db_path=db_path)
    exposure, exposure_missing, loaded = close_payload.exposure_rows(prior)
    pins = close_payload.pin_rows(prior)
    portfolio = close_payload.portfolio_block(as_of=cutoff)

    hits = {k: sum(1 for p in pins if p.get(k)) for k in
            ("max_pain_hit", "peak_gex_hit", "call_wall_hit", "put_wall_hit")}

    # THE OBJECT FOR THE PRIOR SESSION'S CLOSE. READ, NEVER RECOMPUTED -- the
    # Phase 2 order is explicit, and the reason is that an anchor computing its own
    # object could disagree with the close report's, leaving the system holding two
    # regimes and no way to say which one a decision was made under. The morning of
    # session S reports on the close of S-1, so the object read is S-1's.
    # THE EVENTS BLOCK, READ FROM THE TABLE THE INGEST PASSES FILL.
    #
    # `since` is the PRIOR SESSION'S CLOSE -- 20:00 UTC, the 16:00 ET bell -- because
    # "what happened overnight" means since the market last closed, not since
    # midnight. An item that happened inside the window but was ingested after this
    # cutoff is correctly absent: that is what the anchor would have had in front of
    # it, which is what makes this edition replayable.
    events = events_block.build(f"{prior}T20:00:00+00:00", as_of=cutoff,
                                ahead_days=EVENTS_AHEAD_DAYS)


    state_obj = regime.latest(session_day=prior)
    changed = None
    if state_obj is not None:
        changed = regime.what_changed(state_obj,
                                     regime.previous_object(state_obj))

    warnings: list[str] = []
    if state_obj is None:
        warnings.append(
            f"no market_state object for the prior session {prior} -- the close "
            f"pass computes it at 16:45 and this anchor does not recompute it, so "
            f"its absence means last night's close pass did not run")
    if overnight["state"] == "absent":
        warnings.append(f"overnight block absent: {overnight['reason']}")
    elif overnight["state"] == "stale":
        warnings.append(
            f"overnight rows older than {MAX_FETCH_AGE_MINUTES} minutes "
            f"({', '.join(overnight['stale'])}) -- the 06:45 fetch is late or "
            f"did not run; the levels shown are not this morning's")
    if events.get("state") != "ok":
        warnings.append(f"events block {events.get('state')}: "
                        f"{events.get('reason')}")
    elif events.get("dormant"):
        # NOT A WARNING ABOUT THE PASS. A dormant source is configuration, and
        # saying so here is how the anchor's own reader learns that two of the six
        # sources are waiting on a variable rather than broken.
        warnings.append(
            "events sources dormant by configuration: "
            + "; ".join(f"{k} ({v})" for k, v in events["dormant"].items()))
    if not overnight["attribution"]:
        warnings.append("no session attribution -- 5-minute bars were "
                        "unavailable for the index futures")
    if not exposure:
        warnings.append(f"no exposure profiles for the prior session {prior}")
    if not pins:
        warnings.append(f"no pin-log rows for the prior session {prior}")
    if portfolio.get("state") != "ok":
        warnings.append(f"portfolio block {portfolio.get('state')}: "
                        f"{portfolio.get('reason')}")

    return {
        "report": "morning_anchor",
        "session": this_session,
        "prior_session": prior,
        "as_of": cutoff,
        "generated_at": session.utc_iso(),
        "run_id": run_id,
        "overnight": overnight,
        "events": events,
        "exposure": exposure,
        "exposure_missing": exposure_missing,
        "exposure_session": loaded or prior,
        "pins": pins,
        "pin_hits": hits,
        "portfolio": portfolio,
        "market_state": state_obj,
        "what_changed": changed,
        "warnings": warnings,
    }
