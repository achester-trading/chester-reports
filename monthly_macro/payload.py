"""
The Monthly's payload: six sections, deltas over levels. (Phase 4b; Audit #3 §G)

    python -m monthly_macro.payload --as-of 2026-09-23T21:00:00+00:00
    python -m monthly_macro.payload --narrative

THE HALVING IS STRUCTURAL, NOT EDITORIAL. The old report was ten pillar pages of
levels with a regime nobody stated; this is six sections of CHANGE with the regime
read from the object. The pillar pages survive as one delta table in the appendix,
which is where the length went.

  REGIME               the three dials and eight dimensions FROM THE OBJECT, what
                       changed since the previous Monthly, and the vol dial's two
                       legs. No pillar computes a state; pillars are inputs and
                       config/pillars.yaml says which dial each one feeds.
  SCENARIOS            every weight with its Brier beside it. A weight without its
                       score is a forecast nobody has marked.
  TOP & BOTTOM         a section, not a report: the verdict and composite as a
                       state variable, with the bear-rally base rate on the
                       top-side language.
  ALTERNATIVE ASSETS   a section, not a report: metals, energy and digital from the
                       store, absent-with-reason where no fetcher exists.
  REGISTER MONTH       grades, expectancy WITH ITS INTERVAL, Brier, rule breaks,
                       decisions opened and closed.
  APPENDIX             the old pillar pages, condensed to a delta table.

NO REPORT RECOMPUTES REGIME. Every dial and dimension here is read through
regime.latest(); a Monthly that derived its own regime from the pillars would be the
second answer to a question the close report already published, and the placeholder
that asked a model to characterise the regime from the pillars is deleted.

TYPES AND PRINT PRECISION ON EVERY FIGURE. The payload goes through
daily_cascade.precision on the way out, so the model never sees a figure the report
would not print, and every field name carries a type the numeral audit checks
against the unit word the prose uses.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
from typing import Any, Optional

from altdata import claims, observations, session

from daily_cascade import precision

from . import pillars

log = logging.getLogger("monthly_macro.payload")

SECTIONS = ("regime", "scenarios", "top_bottom", "alternative_assets",
            "register_month", "appendix")

# The object's dimensions, in the order the report prints them: the four the macro
# dial reads, then the two the vol dial reads, then the price-based pair.
DIMENSION_ORDER = ("growth", "inflation", "rates", "liquidity", "credit",
                   "volatility", "trend", "breadth")

# ALTERNATIVE ASSETS, by family, as store keys. Declared rather than discovered so
# a family with no fetcher is visible as a gap instead of an empty section.
ALT_FAMILIES: dict[str, dict[str, Any]] = {
    "metals": {"metrics": ["yfinance.mkt_gld", "yfinance.mkt_slv"],
               "note": "gold and silver funds; the store holds no spot metal"},
    "energy": {"metrics": ["yfinance.mkt_uso", "fred.wti"],
               "note": "the oil fund and WTI spot"},
    "digital": {"metrics": ["yfinance.mkt_btc_usd", "zec.price",
                            "zec.shielded_value_share",
                            "crypto.cap_share"],
                "note": "bitcoin from the price basket; the ZEC block from the "
                        "29.5 shielded-pool logger, including the shielded share "
                        "of SUPPLY (not of transactions -- see that module)"},
    "real_assets": {"metrics": [],
                    "not_yet_sourced": {
                        "needs": ["a REIT index series", "a farmland or "
                                  "infrastructure proxy"],
                        "why": "the chain-capture universe holds no REIT and the "
                               "store no real-asset series, so this family is "
                               "named and empty rather than quietly missing"}},
}


# ---------------------------------------------------------------------------
# 1. REGIME -- read, never recomputed
# ---------------------------------------------------------------------------
def previous_monthly(as_of: Optional[str] = None) -> Optional[str]:
    """The report date of the previous Monthly, from the committed snapshots.

    The snapshot directory IS the record of what the Monthly has published, so the
    previous edition is the newest snapshot strictly before this one -- the same
    rule snapshot.py uses so a same-day re-run still compares to last month.
    """
    from . import snapshot as snap
    today = (dt.date.fromisoformat(as_of[:10]) if as_of
             else session.session_date_obj())
    try:
        prior = snap.load_prior_snapshot(today)
    except Exception:                                          # noqa: BLE001
        return None
    return (prior or {}).get("report_date")


def regime_block(as_of: Optional[str] = None,
                 store: Optional[Any] = None) -> dict:
    """The dials and dimensions from the object, against the previous Monthly."""
    out: dict[str, Any] = {"state": "absent", "reason": ""}
    try:
        import regime
    except Exception as exc:                                   # noqa: BLE001
        out["reason"] = f"regime unavailable: {type(exc).__name__}: {exc}"
        return out
    now = regime.latest(as_of=as_of, store=store)
    if now is None:
        out["reason"] = ("no market-state object knowable at this cutoff -- the "
                         "close pass computes it and this report reads it, so its "
                         "absence means no close pass has run")
        return out
    prev_date = previous_monthly(as_of)
    was = (regime.latest(session_day=prev_date, store=store)
           if prev_date else None)
    out.update({
        "state": "ok",
        "session": now.get("session"),
        "config_version": now.get("config_version"),
        "method_version": now.get("method_version"),
        "previous_monthly": prev_date,
        "comparison": ("the previous Monthly's session" if was else
                       "no previous Monthly snapshot, so nothing is reported as "
                       "changed rather than everything being reported as new"),
    })

    # --- the three dials, with the pillars that feed each -------------------
    dials = []
    for name in ("macro", "vol", "gamma"):
        d = (now.get("dials") or {}).get(name) or {}
        prev = ((was or {}).get("dials") or {}).get(name) or {}
        row = {
            "dial": name,
            "state": d.get("state"),
            "previous_state": prev.get("state") if was else None,
            "changed": bool(was) and prev.get("state") != d.get("state"),
            "absent_reason": d.get("absent_reason"),
            "confidence": d.get("confidence"),
            "provisional": d.get("provisional"),
            # THE PILLARS ARE PRINTED BENEATH THE DIAL THEY FEED, which is the
            # whole point of the mapping: a reader sees one regime with its inputs
            # underneath, not eleven peers.
            "pillars": [
                {"number": p["number"], "name": p.get("name"),
                 "weight": p.get("weight"),
                 "reads_dimension": p.get("from_object"),
                 "absent_reason": p.get("from_object_absent_reason")}
                for p in pillars.for_dial(name)],
        }
        if name == "vol":
            ts = d.get("term_structure") or {}
            row["term_structure"] = {
                "published_by": ts.get("published_by"),
                "published_state": ts.get("state"),
                "champion": {k: (ts.get("champion") or {}).get(k)
                             for k in ("metric", "state", "ratio", "percentile")},
                "challenger": {k: (ts.get("challenger") or {}).get(k)
                               for k in ("metric", "state", "ratio",
                                         "percentile")},
                "legs_agree": ts.get("legs_agree"),
                "basis": (ts.get("basis") or {}).get("value"),
                "dual_run_until": ts.get("dual_run_until"),
            }
            row["realized_implied"] = {
                k: (d.get("realized_implied") or {}).get(k)
                for k in ("state", "ratio", "realized", "implied")}
        dials.append(row)
    out["dials"] = dials

    # --- the eight dimensions, with what changed ----------------------------
    cur_dims = now.get("dimensions") or {}
    prev_dims = (was or {}).get("dimensions") or {}
    rows = []
    for name in DIMENSION_ORDER:
        d = cur_dims.get(name) or {}
        p = prev_dims.get(name) or {}
        rows.append({
            "dimension": name,
            "state": d.get("state"),
            "previous_state": p.get("state") if was else None,
            "changed": bool(was) and p.get("state") != d.get("state"),
            "percentile": d.get("percentile"),
            "direction": d.get("direction"),
            "confidence": d.get("confidence"),
            "absent_reason": d.get("absent_reason"),
            "extremes": [m.get("metric") for m in (d.get("members") or [])
                         if m.get("extreme")],
        })
    out["dimensions"] = rows
    out["dimensions_changed"] = [r["dimension"] for r in rows if r["changed"]]

    # --- exceptions and contradictions --------------------------------------
    ids_now = set(regime.exception_ids(now))
    ids_was = set(regime.exception_ids(was)) if was else set()
    out["exceptions_open_now"] = sorted(ids_now)
    out["exceptions_opened"] = sorted(ids_now - ids_was)
    out["exceptions_closed"] = sorted(ids_was - ids_now)
    out["contradictions"] = [
        {k: r.get(k) for k in ("id", "legs", "open_state", "magnitude",
                               "threshold_z", "persistence_days", "since",
                               "exception", "absent_reason")}
        for r in (now.get("contradictions") or [])]
    return out


# ---------------------------------------------------------------------------
# 2. SCENARIOS -- every weight with its Brier beside it
# ---------------------------------------------------------------------------
FAMILY_MAP_PATH = "config/scenario_families.yaml"


def scenarios_block() -> dict:
    """Scenario weights and their Brier scores. Grouped by family if one exists."""
    out: dict[str, Any] = {"state": "absent", "reason": "",
                           "grouping": "scenario",
                           "family_map": FAMILY_MAP_PATH,
                           "family_map_exists": False}
    from pathlib import Path
    out["family_map_exists"] = (pillars.REPO / FAMILY_MAP_PATH).exists()
    if not out["family_map_exists"]:
        out["grouping_note"] = (
            f"grouped by SCENARIO, because {FAMILY_MAP_PATH} does not exist. The "
            f"collapse of the twenty-five scenarios into ~6 mechanism families is "
            f"6f in the phase plan and is not done; until the mapping is config, "
            f"grouping them here would be this report inventing a taxonomy that "
            f"the tail watch and the Brier ledger would then disagree with")
    try:
        from altdata import probability_ledger as pl
    except Exception as exc:                                   # noqa: BLE001
        out["reason"] = f"ledger unavailable: {type(exc).__name__}: {exc}"
        return out
    try:
        with pl.ProbabilityLedger() as ledger:
            rows = ledger.all_rows()
            by_source = ledger.score_by_source()
            due = ledger.due()
    except Exception as exc:                                   # noqa: BLE001
        out["reason"] = f"ledger unreadable: {type(exc).__name__}: {exc}"
        return out
    out["method_version"] = pl.METHOD_VERSION
    out["emitted"] = len(rows)
    out["resolved"] = sum(1 for r in rows if r.get("outcome") is not None)
    out["by_source"] = by_source
    out["due_unresolved"] = [
        {k: r.get(k) for k in ("claim", "probability", "resolve_by", "source")}
        for r in due]
    # EVERY WEIGHT WITH ITS SCORE BESIDE IT. A weight printed without its Brier is
    # a forecast nobody has marked, which is what the old Monthly printed.
    out["weights"] = [
        {"claim": r.get("claim"), "probability": r.get("probability"),
         "source": r.get("source"), "emitted_at": r.get("emitted_at"),
         "outcome": r.get("outcome"), "brier": r.get("brier"),
         "resolve_by": r.get("resolve_by")}
        for r in rows]
    out["state"] = "ok" if rows else "empty"
    if not rows:
        out["reason"] = (
            "no probability has been emitted. The ledger is seeded from a "
            "Monthly's own scenario table (probability_ledger.seed_from_monthly), "
            "so the first weights arrive when a Monthly with a scenario section is "
            "published -- and until one is, a Brier score would be a number about "
            "nothing")
    return out


# ---------------------------------------------------------------------------
# 3. TOP & BOTTOM -- a section, not a report
# ---------------------------------------------------------------------------
def top_bottom_block(store: Optional[Any] = None) -> dict:
    """The verdict and composite as a state variable, with the bear-rally rate."""
    out: dict[str, Any] = {"state": "absent", "reason": "", "verdict": None,
                           "composite": None}
    own = store is None
    db = store or observations.ObservationStore()
    try:
        # THE COMPOSITE AS A STATE VARIABLE, read from the store like any other.
        # It does not exist yet: the T&B harness is not built (CLAUDE.md's report
        # table says so), and this section does not compute one -- a composite
        # invented here would be a second top-and-bottom reading with no harness
        # behind it.
        rows = db.as_of("top_bottom.composite")
        if rows:
            out["state"] = "ok"
            out["composite"] = rows[-1].get("value_num")
            out["as_of"] = str(rows[-1].get("observed_at"))[:10]
            vr = db.as_of("top_bottom.verdict")
            out["verdict"] = (vr[-1].get("value_text") if vr else None)
        else:
            out["reason"] = (
                "top_bottom.composite is not in the store. The Top & Bottom "
                "harness is not built -- it is a report in the registry and an "
                "unbuilt pipeline -- and this section reads its state variable "
                "rather than computing one, because a composite invented here "
                "would have no harness behind it and no way to be calibrated")

        # --- THE BEAR-RALLY BASE RATE, on the top-side language (31.1) --------
        # Read from baserate.*, which is computed from the store, and cited beside
        # the claim that carries the archetype.
        try:
            from tools import base_rates as br
            table = br.latest("baserate.drawdown_by_depth", store=db)
        except Exception as exc:                               # noqa: BLE001
            table = None
            out["base_rate_error"] = f"{type(exc).__name__}: {exc}"
        rally = (br.dig(table, "bear_properties.largest_counter_trend_rally_pct")
                 if table else None)
        out["bear_rally_base_rate"] = {
            "source_metric": "baserate.drawdown_by_depth",
            "field": "bear_properties.largest_counter_trend_rally_pct",
            "p25": (rally or {}).get("p25"),
            "median": (rally or {}).get("median"),
            "p75": (rally or {}).get("p75"),
            "max": (rally or {}).get("max"),
            "n_bears": (rally or {}).get("n"),
            "method_version": (table or {}).get("method_version"),
            "why_it_is_here": (
                "31.1: the top-side language carries the bear-rally base rate, "
                "because that governs how a top call is HELD rather than how it is "
                "made. A short campaign inside a -20% decline faces three to five "
                "of these and each will look like the turn"),
            "absent_reason": (None if rally else
                              "baserate.drawdown_by_depth is not in the store -- "
                              "run tools/base_rates.py"),
        }
        # CITED BY ID, never retyped.
        cited = []
        for cid in ("br.episode_1929_32", "br.extended_tail_percentiles"):
            try:
                c = claims.cite(cid)
                cited.append({k: c.get(k) for k in
                              ("id", "value", "source", "as_of", "warnings")})
            except Exception as exc:                           # noqa: BLE001
                cited.append({"id": cid, "absent_reason": str(exc)[:120]})
        out["claims_cited"] = cited
        return out
    finally:
        if own:
            db.close()


# ---------------------------------------------------------------------------
# 4. ALTERNATIVE ASSETS -- a section, not a report
# ---------------------------------------------------------------------------
def alternative_assets_block(as_of: Optional[str] = None,
                             store: Optional[Any] = None) -> dict:
    """Metals, energy and digital from the store. Absent-with-reason otherwise."""
    from altdata import derived
    out: dict[str, Any] = {"state": "ok", "families": {}}
    own = store is None
    db = store or observations.ObservationStore()
    try:
        for family, spec in ALT_FAMILIES.items():
            rows = []
            for metric in spec.get("metrics") or []:
                d = derived.derived_forms(metric, as_of, store=db)
                rows.append({
                    "metric": metric,
                    "level": d.get("level"),
                    "observed_at": d.get("observed_at"),
                    "delta_20d": d.get("delta_20d"),
                    "delta_unit": d.get("delta_unit"),
                    "percentile": d.get("percentile"),
                    "confidence": d.get("confidence"),
                    "absent_reason": (None if d.get("level") is not None else
                                      f"{metric} has no observation knowable at "
                                      f"this cutoff"),
                })
            entry: dict[str, Any] = {"note": spec.get("note"), "metrics": rows}
            if spec.get("not_yet_sourced"):
                entry["state"] = "not_yet_sourced"
                entry.update(spec["not_yet_sourced"])
            elif any(r["level"] is not None for r in rows):
                entry["state"] = "ok"
            else:
                entry["state"] = "absent"
                entry["reason"] = ("no metric in this family has an observation "
                                   "knowable at this cutoff")
            out["families"][family] = entry
        out["note"] = (
            "A SECTION, NOT A REPORT. The Alternative Asset report is not produced "
            "by any pipeline here -- altdata/report/ is vendored content, nothing "
            "schedules it -- so this reads the store directly and says which "
            "families it cannot reach")
        return out
    finally:
        if own:
            db.close()


# ---------------------------------------------------------------------------
# 5. REGISTER MONTH
# ---------------------------------------------------------------------------
def register_month_block(as_of: Optional[str] = None) -> dict:
    """Grades with intervals, Brier, rule breaks, decisions opened and closed."""
    out: dict[str, Any] = {"state": "absent", "reason": ""}
    start = _month_start(as_of)
    end = (as_of or session.utc_iso())[:10]
    out["window"] = [start, end]
    try:
        import sys as _sys
        from pathlib import Path as _P
        _t = str(_P(__file__).resolve().parent.parent / "tools")
        if _t not in _sys.path:
            _sys.path.insert(0, _t)
        from altdata import grader
        import cuts
        from register.store import Register
    except Exception as exc:                                   # noqa: BLE001
        out["reason"] = f"unavailable: {type(exc).__name__}: {exc}"
        return out
    try:
        with grader.GradeStore() as gs:
            rows = gs.all_grades()
        month = [g for g in rows
                 if start <= str(g.get("graded_at") or "")[:10] <= end]
        out["graded_total"] = len(rows)
        out["graded_this_month"] = len(month)
        out["cuts"] = cuts.all_cuts()
        out["state"] = "ok" if rows else "empty"
        if not rows:
            out["reason"] = ("nothing has reached a horizon yet, which is the "
                             "expected state of a register days old")
    except Exception as exc:                                   # noqa: BLE001
        out["reason"] = f"grades unreadable: {type(exc).__name__}: {exc}"
    try:
        reg = Register()
        try:
            decisions = [dict(r) for r in reg.all()]
            attempts = [dict(a) for a in reg.blocked_attempts()]
        finally:
            reg.close()
        out["decisions_opened"] = [
            {"id": d.get("id"), "instrument": d.get("instrument"),
             "direction": d.get("direction"), "status": d.get("status"),
             "thesis_state": d.get("thesis_state"),
             "expression_family": d.get("expression_family"),
             "created_at": str(d.get("created_at"))[:10]}
            for d in decisions
            if start <= str(d.get("created_at") or "")[:10] <= end]
        out["decisions_closed"] = [
            {"id": d.get("id"), "instrument": d.get("instrument"),
             "status": d.get("status")}
            for d in decisions if d.get("status") == "closed"]
        out["open_now"] = sum(1 for d in decisions
                              if d.get("status") in ("active", "draft")
                              and not d.get("superseded_by"))
        out["rule_breaks"] = {
            "restricted_instrument_attempts_this_month": sum(
                1 for a in attempts
                if start <= str(a.get("attempted_at") or "")[:10] <= end),
            "restricted_instrument_attempts_total": len(attempts),
            "not_yet_sourced": ["allocation_floor_breach", "book_b_conversion",
                                "time_stop_passed"],
            "not_yet_sourced_why": (
                "each needs something the register does not carry -- a "
                "band-weighted stance, a book label and a closing reason, a time "
                "stop -- and a zero would read as 'no rule was broken'"),
        }
    except Exception as exc:                                   # noqa: BLE001
        out["register_reason"] = f"{type(exc).__name__}: {exc}"
    return out


def _month_start(as_of: Optional[str] = None) -> str:
    d = (dt.date.fromisoformat(as_of[:10]) if as_of else session.session_date_obj())
    return d.replace(day=1).isoformat()


# ---------------------------------------------------------------------------
# 6. APPENDIX -- the old pillar pages, condensed
# ---------------------------------------------------------------------------
def appendix_block(as_of: Optional[str] = None,
                   store: Optional[Any] = None) -> dict:
    """One delta row per series, grouped by pillar. THIS IS WHERE THE HALVING IS.

    The old report gave each pillar a page: a synthesis placeholder, a table of
    every series with its level, and a change note. Ten of those is most of the
    document's length and none of it answers what changed -- a level is where a
    series is, not that it moved.

    One row per series: the level, the change over a month in the metric's OWN
    delta unit, and its percentile. The pillar is a grouping, not a section.
    """
    from altdata import config, derived
    out: dict[str, Any] = {"state": "ok", "pillars": {}}
    own = store is None
    db = store or observations.ObservationStore()
    try:
        by_pillar: dict[str, list[dict]] = {}
        for spec in config.FRED_SERIES:
            metric = f"fred.{spec.key}"
            d = derived.derived_forms(metric, as_of, store=db)
            by_pillar.setdefault(str(spec.pillar), []).append({
                "metric": metric,
                "description": spec.description,
                "level": d.get("level"),
                "observed_at": d.get("observed_at"),
                "delta_20d": d.get("delta_20d"),
                "delta_unit": d.get("delta_unit"),
                "percentile": d.get("percentile"),
                "extreme": d.get("extreme"),
                "confidence": d.get("confidence"),
                "staleness_sessions": d.get("staleness_sessions"),
            })
        for num, rows in sorted(by_pillar.items()):
            try:
                p = pillars.get(num)
            except KeyError:
                p = {"name": f"(pillar {num} is not in config/pillars.yaml)"}
            out["pillars"][num] = {
                "name": p.get("name"),
                "dial": p.get("dial"),
                "weight": p.get("weight"),
                "reads_dimension": p.get("from_object"),
                "series": sorted(rows, key=lambda r: r["metric"]),
                "series_count": len(rows),
                "stale_count": sum(1 for r in rows
                                   if r.get("level") is None),
            }
        out["series_total"] = sum(v["series_count"]
                                  for v in out["pillars"].values())
        out["note"] = (
            "The old report's ten pillar pages, condensed to one delta row per "
            "series. A level says where a series is; the change says what it did, "
            "and the change is in the metric's OWN unit -- basis points for a "
            "spread, percent for a price, raw for a count -- taken from the "
            "registry rather than from one formula")
        return out
    finally:
        if own:
            db.close()


# ---------------------------------------------------------------------------
# The payload
# ---------------------------------------------------------------------------
def build(as_of: Optional[str] = None, run_id: Optional[str] = None) -> dict:
    """Every section. Reads only; never raises on a missing one."""
    cutoff = as_of or session.utc_iso(timespec="microseconds")
    db = observations.ObservationStore()
    try:
        out: dict[str, Any] = {
            "report": "monthly",
            "report_date": session.session_date(),
            "as_of": cutoff,
            "generated_at": session.utc_iso(),
            "run_id": run_id,
            "sections": list(SECTIONS),
            "pillar_mapping_version": pillars.load()["version"],
        }
        out["regime"] = regime_block(cutoff, store=db)
        out["scenarios"] = scenarios_block()
        out["top_bottom"] = top_bottom_block(store=db)
        out["alternative_assets"] = alternative_assets_block(cutoff, store=db)
        out["register_month"] = register_month_block(cutoff)
        out["appendix"] = appendix_block(cutoff, store=db)
        out["warnings"] = [
            f"{name}: {(out.get(name) or {}).get('state')} -- "
            f"{(out.get(name) or {}).get('reason') or 'no reason recorded'}"
            for name in SECTIONS
            if (out.get(name) or {}).get("state") not in
            ("ok", "empty", "not_yet_sourced")]
        return precision.apply(out)
    finally:
        db.close()


def narrative_payload(full: dict) -> dict:
    """What the Monthly's paragraph may cite. Narrower than the document.

    The appendix alone is 59 series with four figures each; a paragraph given all of
    them can cite an intermediate as a headline. What travels is the regime, the
    scenario scores, the two sections' verdicts, the register's month and the
    appendix's COUNTS rather than its rows.
    """
    rg = full.get("regime") or {}
    sc = full.get("scenarios") or {}
    tb = full.get("top_bottom") or {}
    alt = full.get("alternative_assets") or {}
    rm = full.get("register_month") or {}
    ap = full.get("appendix") or {}
    out = {
        "report_date": full.get("report_date"),
        "previous_monthly": rg.get("previous_monthly"),
        "regime": {
            "dials": [{k: d.get(k) for k in
                       ("dial", "state", "previous_state", "changed",
                        "absent_reason", "term_structure", "realized_implied")}
                      for d in (rg.get("dials") or [])],
            "dimensions": [{k: d.get(k) for k in
                            ("dimension", "state", "previous_state", "changed",
                             "percentile", "direction", "absent_reason",
                             "extremes")}
                           for d in (rg.get("dimensions") or [])],
            "dimensions_changed": rg.get("dimensions_changed"),
            "exceptions_open_now": rg.get("exceptions_open_now"),
            "exceptions_opened": rg.get("exceptions_opened"),
            "exceptions_closed": rg.get("exceptions_closed"),
            "contradictions": [r for r in (rg.get("contradictions") or [])
                               if r.get("open_state") != "absent"],
            "absent_reason": rg.get("reason"),
        },
        "scenarios": {"emitted": sc.get("emitted"), "resolved": sc.get("resolved"),
                      "weights": sc.get("weights"),
                      "by_source": sc.get("by_source"),
                      "grouping": sc.get("grouping"),
                      "absent_reason": sc.get("reason")},
        "top_bottom": {"verdict": tb.get("verdict"),
                       "composite": tb.get("composite"),
                       "bear_rally_base_rate": tb.get("bear_rally_base_rate"),
                       "claims_cited": tb.get("claims_cited"),
                       "absent_reason": tb.get("reason")},
        "alternative_assets": {
            fam: {"state": v.get("state"),
                  "metrics": [{k: m.get(k) for k in
                               ("metric", "level", "delta_20d", "delta_unit",
                                "percentile")}
                              for m in (v.get("metrics") or [])],
                  "reason": v.get("reason") or v.get("why")}
            for fam, v in (alt.get("families") or {}).items()},
        "register_month": {
            "graded_total": rm.get("graded_total"),
            "graded_this_month": rm.get("graded_this_month"),
            "overall": (rm.get("cuts") or {}).get("overall"),
            "open_now": rm.get("open_now"),
            "decisions_opened": rm.get("decisions_opened"),
            "rule_breaks": rm.get("rule_breaks"),
            "absent_reason": rm.get("reason"),
        },
        "appendix": {"series_total": ap.get("series_total"),
                     "pillars": {n: {"name": v.get("name"), "dial": v.get("dial"),
                                     "series_count": v.get("series_count"),
                                     "stale_count": v.get("stale_count")}
                                 for n, v in (ap.get("pillars") or {}).items()}},
        "absences": full.get("warnings"),
    }
    return precision.apply(out)


def _main(argv: list[str]) -> int:
    import argparse
    p = argparse.ArgumentParser(description="The Monthly's payload.")
    p.add_argument("--as-of", default=None)
    p.add_argument("--narrative", action="store_true")
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    full = build(a.as_of)
    print(json.dumps(narrative_payload(full) if a.narrative else full,
                     indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
