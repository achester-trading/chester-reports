"""
Signal freshness -- the input side of DECISION_BLOCKED (architecture 26.2 #7).

    "A report may publish degraded (REPORT_OK); a recommendation depending on
     missing or stale inputs is DECISION_BLOCKED."

Two different eligibilities, and this module is the one that decides the second.
A blocked decision is still RECORDED -- an abstention is a decision and the
register logs abstentions -- but it lands as `draft` with a `blocked_reason`
and can never be `active`.

-----------------------------------------------------------------------------
STALENESS IS MEASURED AGAINST THE SIGNAL'S OWN HALF-LIFE
-----------------------------------------------------------------------------

Not against one global timeout. 26.4 gives every metric an
information_half_life precisely so that "too old" means something different for
a portfolio snapshot and for a quarterly GDP print, and the registry already
holds the answer per metric.

    intraday            must be from the CURRENT session and recent. On a
                        non-session day nothing intraday can be fresh, because
                        nothing is trading -- a portfolio reading from Friday
                        afternoon does not describe Saturday.
    session             must be from the most recent COMPLETED trading session.
                        On a Saturday that is Friday, and Friday's close is
                        therefore current, not stale. Blocking it would be
                        wrong: Part 7 has the Friday session SET the swing
                        thesis, so a rule that blocked every weekend decision
                        would forbid the process the architecture is built on.
    until_next_release  bounded by the series' own frequency (from SeriesSpec):
                        a monthly print is current for about a month.
    week / month        a plain age bound.
    permanent           never stale. A graded outcome is history.

WHERE A SIGNAL'S AGE COMES FROM. Three stores hold different things, so the
lookup follows the registry key rather than assuming one home:

    exposure.* / gates.*  the newest computed profile (its session_date)
    pin.*                 the newest pin-log row for that session
    everything else       the point-in-time observation store

A signal nothing can locate is MISSING, which blocks exactly as staleness does
and for the better reason: a decision citing evidence the system cannot produce
is worse than one citing evidence that is merely old.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

from altdata import config, observations, session   # noqa: E402

# An intraday reading goes stale within the session, not at the end of it.
INTRADAY_MAX_AGE_H = 4.0

# until_next_release, bounded by the series' declared frequency. Generous by
# one release interval: a print is current until the next one is due, and being
# a few days past a due date is late data, not a broken pipeline.
FREQ_MAX_AGE_DAYS = {"daily": 5, "weekly": 16, "monthly": 45, "quarterly": 135}
AGE_BOUND_DAYS = {"week": 7, "month": 31}


def _registry() -> dict:
    import yaml  # noqa: PLC0415
    with (REPO / "metrics_registry.yaml").open(encoding="utf-8") as fp:
        return yaml.safe_load(fp) or {}


def _fred_freq(key: str) -> Optional[str]:
    leaf = key.split(".", 1)[-1]
    for spec in config.FRED_SERIES:
        if spec.key == leaf:
            return spec.freq
    return None


def _newest_profile_session(instrument: Optional[str]) -> Optional[str]:
    """Session date of the newest computed profile, for exposure/gates keys."""
    import exposure_compute as ec  # noqa: PLC0415
    root = Path(config.COMPUTED_DIR)
    if not root.exists():
        return None
    for day in sorted((p for p in root.iterdir() if p.is_dir()), reverse=True):
        pat = f"{instrument}_*" if instrument else "*"
        files = sorted(list(day.glob(f"{pat}_exposure.json"))
                       + list(day.glob(f"{pat}_gex.json")),
                       key=lambda q: q.stat().st_mtime, reverse=True)
        for f in files:
            try:
                rec = json.loads(f.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                continue
            if rec.get("error"):
                continue      # a deferred profile computed nothing
            if rec.get("session_date"):
                return rec["session_date"]
    return None


def _newest_pin_session(instrument: Optional[str]) -> Optional[str]:
    p = Path(config.PIN_LOG_PATH)
    if not p.exists():
        return None
    best = None
    with p.open(encoding="utf-8", newline="") as fp:
        for r in csv.DictReader(fp):
            if instrument and r.get("symbol") != instrument:
                continue
            d = r.get("date")
            if d and (best is None or d > best):
                best = d
    return best


def locate(key: str, instrument: Optional[str] = None) -> dict:
    """Where a signal's freshest value is, and how old it is."""
    out = {"key": key, "found": False, "where": None,
           "session_date": None, "as_of": None, "age_days": None}
    if key.startswith("exposure.") or key.startswith("gates."):
        sd = _newest_profile_session(instrument)
        out.update(where="computed profile", session_date=sd, found=bool(sd))
    elif key.startswith("pin."):
        sd = _newest_pin_session(instrument)
        out.update(where="pin log", session_date=sd, found=bool(sd))
    else:
        # Try the instrument-scoped row, then the unscoped one. Not every
        # signal is keyed on the decision's instrument: FRED macro rows carry
        # instrument=NULL, and a portfolio row is keyed on the ACCOUNT, not on
        # the symbol being traded. Passing the decision's ticker to both was
        # the first version of this and it reported every macro series as
        # missing -- a false block, which is the failure mode that teaches
        # people to ignore the check.
        row = None
        try:
            with observations.ObservationStore() as db:
                if instrument:
                    row = db.latest_as_of(key, instrument=instrument)
                if row is None:
                    row = db.latest_as_of(key, instrument=None)
        except Exception:  # noqa: BLE001
            row = None
        if row:
            out.update(where="observation store", found=True,
                       as_of=row.get("available_at"),
                       session_date=str(row.get("observed_at"))[:10])
    stamp = out["as_of"] or out["session_date"]
    if stamp:
        try:
            when = dt.datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
            if when.tzinfo is None:
                when = when.replace(tzinfo=dt.timezone.utc)
            out["age_days"] = round(
                (session.utc_now() - when).total_seconds() / 86400.0, 3)
        except ValueError:
            pass
    return out


def assess(key: str, half_life: str, instrument: Optional[str] = None,
           now: Optional[str] = None) -> dict:
    """Is this signal fresh enough to move a decision?

    Returns the verdict plus what would clear it, because "blocked" without a
    remedy is a dead end and the operator is the one who has to act on it.
    """
    info = locate(key, instrument)
    v = {**info, "half_life": half_life, "stale": True, "reason": "", "unblock": ""}

    if not info["found"]:
        v["reason"] = "no observation found"
        v["unblock"] = ("run the pipeline that produces it "
                        + ("(run_eod.py)" if key.startswith(("exposure.", "gates.", "pin."))
                           else "(the source's sync) and confirm it lands in the store"))
        return v

    today_session = session.session_date(now)
    is_session_today = session.is_trading_session(now)
    last_session = session.last_trading_session(now).isoformat()

    if half_life == "permanent":
        v.update(stale=False, reason="permanent -- a recorded outcome does not decay")
    elif half_life == "intraday":
        if not is_session_today:
            v["reason"] = (f"intraday signal on a non-session day "
                           f"({session.session_reason(now)}); nothing is trading, "
                           f"so no intraday reading can be current")
            v["unblock"] = "re-run the decision during a trading session"
        elif info["session_date"] != today_session:
            v["reason"] = (f"last reading is from {info['session_date']}, "
                           f"not today's session {today_session}")
            v["unblock"] = "run the sync so today's reading lands"
        elif (info["age_days"] or 0) * 24.0 > INTRADAY_MAX_AGE_H:
            v["reason"] = (f"{(info['age_days'] or 0) * 24:.1f}h old, past the "
                           f"{INTRADAY_MAX_AGE_H:.0f}h intraday bound")
            v["unblock"] = "re-run the sync"
        else:
            v.update(stale=False, reason=f"current session, "
                                         f"{(info['age_days'] or 0) * 24:.1f}h old")
    elif half_life == "session":
        # The most recent COMPLETED session, not the calendar day. On a
        # Saturday that is Friday, and Friday's close is the current vintage.
        if info["session_date"] == last_session:
            v.update(stale=False,
                     reason=f"from the latest completed session {last_session}")
        else:
            v["reason"] = (f"from session {info['session_date']}, but the latest "
                           f"completed session is {last_session}")
            v["unblock"] = f"run the EOD pass for {last_session}"
    elif half_life == "until_next_release":
        freq = _fred_freq(key) or "monthly"
        bound = FREQ_MAX_AGE_DAYS.get(freq, 45)
        if (info["age_days"] or 0) <= bound:
            v.update(stale=False,
                     reason=f"{info['age_days']:.0f}d old, inside the {freq} "
                            f"release interval ({bound}d)")
        else:
            v["reason"] = (f"{info['age_days']:.0f}d old, past the {freq} "
                           f"release interval ({bound}d)")
            v["unblock"] = "run the FRED pull; the series may also be deprecated"
    elif half_life in AGE_BOUND_DAYS:
        bound = AGE_BOUND_DAYS[half_life]
        if (info["age_days"] or 0) <= bound:
            v.update(stale=False, reason=f"{info['age_days']:.0f}d old, within {bound}d")
        else:
            v["reason"] = f"{info['age_days']:.0f}d old, past the {bound}d bound"
            v["unblock"] = "refresh the source"
    else:
        v["reason"] = f"unknown half_life {half_life!r}; treated as stale"
        v["unblock"] = "declare a known half_life in metrics_registry.yaml"
    return v


def check_signals(keys: list, instrument: Optional[str] = None,
                  now: Optional[str] = None) -> dict:
    """Assess every declared signal. Returns verdicts and a blocked_reason."""
    reg = _registry()
    metrics = reg.get("metrics") or {}
    fred_block = (reg.get("bulk_imports") or {}).get("fred_macro") or {}

    verdicts = []
    unknown = []
    for key in keys:
        m = metrics.get(key)
        if m:
            half = m.get("information_half_life")
        elif key.startswith("fred.") and _fred_freq(key):
            # Registered by the bulk block, but only if the series actually
            # exists in config.FRED_SERIES -- otherwise "fred.anything" would
            # pass the registry check and then fail as missing data, which
            # blames the pipeline for a typo.
            half = fred_block.get("information_half_life")
        else:
            unknown.append(key)
            verdicts.append({"key": key, "found": False, "stale": True,
                             "half_life": None, "where": None,
                             "session_date": None, "age_days": None,
                             "reason": "not in metrics_registry.yaml",
                             "unblock": "register it, or cite a registered signal"})
            continue
        verdicts.append(assess(key, half, instrument, now))

    stale = [v for v in verdicts if v["stale"]]
    reason = ""
    if stale:
        reason = "; ".join(f"{v['key']}: {v['reason']}" for v in stale)
    return {"verdicts": verdicts, "stale": stale, "unknown": unknown,
            "blocked": bool(stale), "blocked_reason": reason or None}
