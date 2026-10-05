"""
The stacked close, end to end. (reporting-stack brief, Tranche T1)

    from daily_cascade import stack_close
    out = stack_close.produce(payload, archive_dir=..., dry_run=...)

ORDER, AND WHY. (1) Nothing is fetched: the tape set's bars were pulled by the
`bars` feed in the 16:10 eod run, and a short pull prints "bars incomplete (n=...)"
(brief 2.3; 30.4, ruled 2 Oct 2026). (2) The level list is computed once and
every later step reads it (2.2). (3) The outlooks are computed and, unless this
is a dry run, written to the ledger -- before anything prints them (1.3). (4) The
stack is assembled: items, depth and triggers, change marks against the prior
edition, the collapse rule (1, 1.1, 1.3). (5) The prose is written and audited,
section by section (2.1). (6) The budget is enforced (1.4). (7) The charts are
drawn from the same level list (3). (8) The dealer-scorecard row is stored for the
Monthly's retrospective (1.2). (9) The edition -- sections, level list, outlooks,
chart series -- is archived as JSON beside the HTML, so the next edition can mark
changes against it and any chart can be regenerated.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import math
from pathlib import Path
from typing import Any, Optional

from altdata import bars as bars_mod, levels as levels_mod, observations, session

from . import charts as charts_mod
from . import outlooks as outlooks_mod
from . import stack as stack_mod
from . import stack_prose, stack_render

log = logging.getLogger("daily_cascade.stack_close")

SCORECARD_KEY = "dealer.scorecard_day"


def edition_name(sess: str) -> str:
    return f"daily_close_{sess}_stack.json"


def load_prior(sess: str, archive_dir: str) -> Optional[dict]:
    """The newest stacked edition archived strictly before `sess`."""
    if not archive_dir:
        return None
    d = dt.date.fromisoformat(sess)
    for k in range(1, 10):
        p = Path(archive_dir) / edition_name((d - dt.timedelta(days=k)).isoformat())
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except ValueError:
                return None
    return None


def _contradiction_history(st, cid: str, cutoff: str) -> list[tuple[str, float]]:
    import regime                                              # noqa: PLC0415
    out = {}
    for r in st.as_of(regime.STORE_KEY, cutoff):
        try:
            obj = json.loads(r["value_text"])
        except (TypeError, ValueError):
            continue
        for c in obj.get("contradictions") or []:
            if c.get("id") == cid and isinstance(c.get("magnitude"), (int, float)):
                out[str(r["observed_at"])[:10]] = float(c["magnitude"])
    return sorted(out.items())


def _series(st, key: str, cutoff: str) -> list[tuple[str, float]]:
    rows = [(str(r["observed_at"])[:10], r["value_num"]) for r in st.as_of(key, cutoff)
            if r.get("value_num") is not None]
    return sorted(rows)


def scorecard_row(p: dict, book: dict, bstore, prior_profile: Optional[dict]) -> dict:
    """The fields the Monthly's dealer retrospective reads (brief 1.2), for SPY."""
    sess = p["session"]
    exp = next((r for r in p.get("exposure") or [] if r.get("symbol") == "SPY"), {})
    pin = next((r for r in p.get("pins") or [] if r.get("symbol") == "SPY"), {})
    spy = next((i for i in book.get("instruments") or [] if i["id"] == "spy"), {})
    intra = bars_mod.intraday(bstore, "spy", sess)
    b = intra["bars"]
    morning = (prior_profile or {})
    flip = morning.get("gamma_flip")
    hi = max((x["high"] for x in b), default=None)
    lo = min((x["low"] for x in b), default=None)
    prior_close = next((lv["value"] for lv in spy.get("levels") or []
                        if lv["type"] == "prior_close"), None)
    rets = [math.log(b[i]["close"] / b[i - 1]["close"]) for i in range(1, len(b))
            if b[i - 1]["close"]]
    rv = (math.sqrt(sum(r * r for r in rets) / len(rets)) * math.sqrt(78 * 252) * 100
          if len(rets) > 10 else None)
    row = {"session": sess, "symbol": "SPY",
           "gamma_regime": ("positive" if (exp.get("net_gex") or 0) > 0 else
                            "negative") if exp else None,
           "net_gex_close": exp.get("net_gex"),
           "net_gex_morning": morning.get("net_gex"),
           "flip_morning": flip,
           "flip_crossed": (bool(lo <= flip <= hi) if None not in (lo, hi, flip)
                            else None),
           "session_high": hi, "session_low": lo,
           "session_range_pct": (round(100 * (hi - lo) / prior_close, 3)
                                 if None not in (hi, lo) and prior_close else None),
           "session_return_pct": (spy.get("frame") or {}).get("session_change_pct"),
           "pin_max_pain_hit": pin.get("max_pain_hit"),
           "pin_peak_gex_hit": pin.get("peak_gex_hit"),
           "realized_vol_5m_ann_pct": round(rv, 2) if rv else None,
           "bars_complete": intra["complete"], "bars_n": intra["n"],
           # T2.2 (4 Oct 2026, item 18): what the Weekly's dealer table prints
           # per session -- the close's profile beside the morning's flip, and
           # the session's close. The flags are computed by the Weekly from
           # these, never stored as verdicts.
           "close": (spy.get("frame") or {}).get("last"),
           "prior_close": prior_close,
           "dex_close": exp.get("dex_notional"),
           "call_wall": exp.get("call_wall"), "put_wall": exp.get("put_wall"),
           "max_pain": exp.get("max_pain"), "flip_close": exp.get("gamma_flip"),
           # The walls IN FORCE during the session are the morning profile's
           # (the prior session's close); the held flags read these.
           "call_wall_morning": morning.get("call_wall"),
           "put_wall_morning": morning.get("put_wall")}
    return row


def produce(p: dict, *, archive_dir: str, dry_run: bool = False,
            client=None, model: Optional[str] = None, narrative: bool = True,
            db_path: Optional[str] = None) -> dict:
    sess = p["session"]
    cutoff = p.get("as_of") or session.utc_iso()
    cfg = bars_mod.load_config()
    report: dict[str, Any] = {}
    with bars_mod.BarStore(db_path) as bst:
        book = levels_mod.compute(sess, p.get("exposure"), store=bst, as_of=None,
                                  tol_bps=float(p.get("tolerance_bps") or 25.0))
        outs = outlooks_mod.build(sess, bst)
        outs = outlooks_mod.record(outs, sess, dry_run=dry_run, db_path=db_path)
        if not dry_run:
            try:
                report["outlooks_resolved"] = outlooks_mod.resolve_due(cutoff, db_path)
            except Exception as exc:                            # noqa: BLE001
                report["outlooks_resolved"] = {"error": f"{type(exc).__name__}: {exc}"}
        prior = load_prior(sess, archive_dir)
        ed = stack_mod.build(p, book, outs, prior, db_path)
        if narrative:
            ms = None
            try:
                from daily_cascade import story_block           # noqa: PLC0415
                ms = story_block.market_states(p.get("market_state") or {})
            except Exception:                                   # noqa: BLE001
                pass
            stack_prose.write(ed, market_states=ms, client=client, model=model,
                              outlooks=outs)
        stack_mod.enforce_budget(ed)
        # THE CHARTS, from the same level list the prose was audited against.
        plan = stack_mod.chart_plan(ed, {})
        charts: dict[str, dict] = {}
        spy_intra = bars_mod.intraday(bst, "spy", sess, None,
                                      float((cfg.get("bars") or {}).get("complete_share")
                                            or 0.9))
        base_name = f"daily_close_{sess}"
        out_dir = None if dry_run and not archive_dir else archive_dir
        if "C1" in plan:
            charts["C1"] = charts_mod.c1(book, spy_intra["bars"], spy_intra["complete"],
                                         spy_intra["reason"], f"{base_name}_c1", out_dir)
        if "C2" in plan:
            with observations.ObservationStore(db_path) as _db:
                spy_daily = levels_mod.daily_bars(levels_mod.tape_spec("spy"), sess,
                                                  None, _db)[0]
            charts["C2"] = charts_mod.c2(book, spy_daily,
                                         f"{base_name}_c2", out_dir)
        with observations.ObservationStore(db_path) as st:
            if "C3" in plan:
                misfit = next(s for s in ed["sections"] if s["id"] == "misfit")
                oc = (misfit.get("data") or {}).get("open_contradictions") or []
                if oc:
                    top = max(oc, key=lambda c: abs(c.get("z") or 0))
                    charts["C3"] = charts_mod.c3_contradiction(
                        top["name"], _contradiction_history(st, top["_id"], cutoff),
                        float(top.get("threshold_z") or 2.0), f"{base_name}_c3",
                        out_dir)
                    misfit["charts_rendered"] = ["C3"]
                else:
                    charts["C3"] = charts_mod.c3_rates(
                        {"2-year": _series(st, "fred.yield_2y", cutoff),
                         "10-year": _series(st, "fred.yield_10y", cutoff),
                         "30-year": _series(st, "fred.yield_30y", cutoff)},
                        f"{base_name}_c3", out_dir)
                    next(s for s in ed["sections"] if s["id"] == "plumbing")[
                        "charts_rendered"] = ["C3"]
            tape = next(s for s in ed["sections"] if s["id"] == "tape")
            tape["charts_rendered"] = [c for c in ("C1", "C2") if c in charts]
            # THE DEALER SCORECARD ROW (1.2), for the Monthly's retrospective.
            import pin_log                                      # noqa: PLC0415
            prev = session.previous_trading_session(sess).isoformat()
            prof = ((pin_log.load_computed(date=prev) or {}).get("SPY") or {})
            # SPY'S OWN CHAIN (T2.2 rulings of 5 Oct): the ATM 30-day IV from
            # the chain solver and the volume put/call, stored per session; the
            # scorecard carries the IV for the Weekly's implied range.
            from altdata import chain_metrics                   # noqa: PLC0415
            chain = (chain_metrics.readings(sess) if dry_run
                     else chain_metrics.record_session(sess, st))
            report["chain_readings"] = chain
            card = scorecard_row(p, book, bst, (prof.get("overall") or {}))
            card["atm_iv_30d"] = (chain.get("atm_iv_30d") or {}).get("iv_pct")
            card["put_call_volume"] = (chain.get("put_call_volume") or {}).get("ratio")
            report["scorecard"] = card
            if not dry_run:
                st.write_many([{"registry_key": SCORECARD_KEY, "instrument": "SPY",
                                "observed_at": sess, "available_at": session.utc_iso(),
                                "value": json.dumps(card, sort_keys=True, default=str),
                                "source": "daily_close"}])
    ed["charts"] = {k: {kk: v for kk, v in c.items() if kk != "png"}
                    for k, c in charts.items()}
    ed["levels"] = book
    ed["outlooks"] = outs
    ed["chart_count"] = sum(1 for c in charts.values() if not c.get("unavailable"))
    html_email = stack_render.render(p, ed, charts, mode="email")
    html_archive = stack_render.render(p, ed, charts, mode="archive")
    images = [(stack_render.cid(k), c["png"]) for k, c in charts.items()
              if c.get("png")]
    return {"edition": ed, "charts": charts, "html_email": html_email,
            "html_archive": html_archive, "inline_images": images,
            "report": report}


def save_edition(ed: dict, sess: str, archive_dir: Optional[str]) -> Optional[str]:
    from . import deliver                                       # noqa: PLC0415
    return deliver.archive(json.dumps(ed, indent=2, default=str, sort_keys=True),
                           edition_name(sess), archive_dir)
