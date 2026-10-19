"""
The open note, 09:50 ET every trading day (docs/change-order-secondary-notes-
2026-10-19.md section 1, ruled 19 Oct 2026, 14:14 ET).

    python -m daily_cascade.open_note [--date D] [--as-of ISO] [--dry-run] [--email]
        [--archive-dir DIR] [--db PATH] [--computed-dir DIR] [--no-narrative]
        [--no-wait]

What changed between the 07:00 anchor and the first fifteen minutes of the cash
session. It is the Doctrine's 1000 report: it may confirm or cancel Book C's
07:00 list and never add to it -- and today there is no list ("the 07:00 setup
list is not built"), so block 5 says so.

SIX BLOCKS, each with its as-of time: the 08:30 releases; the reaction (release
days); the open against the gauge and the levels; news since 07:00; Book C; what
the close will check. Every line is code-written. Prose (at most 250 words) is
written only when the gate opens: a tier-1 08:30 release, a gap or first-fifteen-
minute range beyond the gauge's implied one-session move, or a volatile-day
trigger the 07:00 anchor printed.

READS THE STORE ONLY: altdata/note_fetch.py `open` wrote it after the 09:45
capture. Before `live_from` (config secondary_notes) every run is a dry run.
"""

from __future__ import annotations

import argparse
import datetime as dt
import logging
import sys
import time
from pathlib import Path
from typing import Any, Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from daily_cascade import note_common as nc                       # noqa: E402

log = logging.getLogger("daily_cascade.open_note")

REPORT = "open_note"
BOOK_C_LINE = "No Book C drafts: the 07:00 setup list is not built."
CONSENSUS_GAP = ("No consensus: no free source serves a macro consensus, and the "
                 "surprise index stores none.")
# THE REACTION'S INSTRUMENTS (the order, block 2): id, label, how its move prints.
REACTION = (("es", "ES", "%"), ("y10", "10-year yield", "bp"), ("zn", "10-year note future", "%"),
            ("zt", "2-year note future", "%"), ("dxy", "Dollar index", "%"),
            ("vix", "VIX", "pts"))
# Lens 24's release ids, by the calendar's label.
LENS24 = {"CPI": "cpi", "Payrolls (employment situation)": "employment", "PPI": "ppi",
          "GDP": "gdp"}


# ---------------------------------------------------------------------------
# Block 1: the 08:30 releases
# ---------------------------------------------------------------------------
def releases_block(day: str, cutoff: str, db_path=None, rels=None) -> dict:
    from altdata import note_fetch, observations, releases     # noqa: PLC0415
    from altdata import derived                                # noqa: PLC0415
    from daily_cascade import weekly_stack as ws               # noqa: PLC0415
    cfg = nc.config()
    rels = rels if rels is not None else note_fetch.todays_0830(day, db_path, cutoff)
    out = {"title": "The 08:30 releases", "as_of": nc.hm_et(cutoff), "releases": [],
           "lines": []}
    if not rels:
        out["lines"] = ["No 08:30 release."]
        return out
    try:
        lens = {x.get("release"): x.get("line")
                for x in releases.release_day_lines(_store(db_path), cutoff)}
    except Exception:                                           # noqa: BLE001
        lens = {}
    with observations.ObservationStore(db_path) as st:
        for rel in rels:
            r = {"label": rel["label"], "tier": rel["tier"], "prints": []}
            heads = note_fetch.release_series(rel, cfg)
            if not heads:
                out["lines"].append(f"{rel['label']} (tier {rel['tier']}): no declared "
                                    "form in the release calendar; the print is not read.")
            for h in heads:
                key, form = h["key"], h.get("form") or "level"
                if not releases.released_today(st, key, cutoff):
                    r["prints"].append({"series": key, "state": "not yet stored"})
                    out["lines"].append(f"{rel['label']}: {h.get('label') or key}: not yet "
                                        "stored (FRED has not served today's print).")
                    continue
                pts = [p for p in st.as_of(key, cutoff) if p.get("value_num") is not None]
                pts.sort(key=lambda p: str(p["observed_at"]))
                got = ws.headline_form([p["value_num"] for p in pts], form)
                if not got:
                    continue
                naive = _naive(st, key, str(pts[-1]["observed_at"]), cutoff)
                units = derived.level_units_of(key)
                rec = {"series": key, "label": h.get("label"), "form": form,
                       "actual": round(got[0], 2),
                       "actual_text": ws.form_text(got[0], form, key),
                       "prior_text": ws.form_text(got[1], form, key),
                       "period": str(pts[-1]["observed_at"])[:7],
                       "naive_surprise": naive, "naive_units": units}
                r["prints"].append(rec)
                nv = (f"; naive surprise {naive:+.2f} ({units}, against the declared naive "
                      "expectation)" if naive is not None else "; naive surprise not stored")
                out["lines"].append(f"{rel['label']}, {rec['period']}: {h.get('label')} "
                                    f"{rec['actual_text']} (prior {rec['prior_text']}){nv}.")
            lid = LENS24.get(rel["label"])
            if lid and lens.get(lid):
                out["lines"].append(lens[lid])
            out["releases"].append(r)
    out["lines"].append(CONSENSUS_GAP)
    return out


def _store(db_path):
    from altdata import observations                            # noqa: PLC0415
    return observations.ObservationStore(db_path)


def _naive(st, key: str, period: str, cutoff: str) -> Optional[float]:
    from altdata import surprise                                # noqa: PLC0415
    bare = key.split(".", 1)[1] if key.startswith("fred.") else key
    rows = [r for r in st.as_of(surprise.surprise_key(bare), cutoff)
            if str(r["observed_at"])[:10] == period[:10] and r.get("value_num") is not None]
    return round(float(rows[-1]["value_num"]), 2) if rows else None


# ---------------------------------------------------------------------------
# Block 2: the reaction
# ---------------------------------------------------------------------------
def reaction_block(day: str, cutoff: str, db_path=None) -> dict:
    t0, t1, t930 = nc.et(day, "08:30"), nc.et(day, "09:45"), nc.et(day, "09:30")
    out = {"title": "The reaction, from the last bar before 08:30 to the last before 09:45",
           "as_of": nc.hm_et(cutoff), "moves": {}, "lines": [
               "No intraday attribution: the rates attribution lens is daily."]}
    for inst, label, unit in REACTION:
        bars = nc.read_bars(inst, nc.et(day, "07:00"), t1, cutoff, db_path)
        a, b = nc.last_ending_by(bars, t0), nc.last_ending_by(bars, t1)
        note = ""
        if not bars:
            out["lines"].append(f"{label}: not tracked (no bars served)." if inst == "zt"
                                else f"{label}: no bars stored.")
            continue
        if a is None and inst == "vix":
            a, note = nc.first_from(bars, t930), " (from the 09:30 open: VIX bars do not cover 08:25)"
            a = {**a, "close": a["open"]} if a else None
        if a is None:
            out["lines"].append(f"{label}: its bars do not cover 08:25.")
            continue
        if b is None:
            out["lines"].append(f"{label}: no bar before 09:45.")
            continue
        if unit == "bp":
            mv = nc.bp(a["close"], b["close"])
        elif unit == "pts":
            mv = round(float(b["close"]) - float(a["close"]), 2)
        else:
            mv = nc.pct(a["close"], b["close"])
        out["moves"][inst] = {"from": a["close"], "to": b["close"], "move": mv, "unit": unit,
                              "from_at": nc.hm_et(a["observed_at"]),
                              "to_at": nc.hm_et(b["observed_at"])}
        extra = (f", {nc.signed(nc.pct(a['close'], b['close']))}" if unit == "pts" else "")
        out["lines"].append(f"{label}: {nc.signed(mv, unit, 1 if unit == 'bp' else 2)}"
                            f"{extra} ({a['close']:,.2f} to {b['close']:,.2f}){note}.")
    return out


# ---------------------------------------------------------------------------
# Block 3: the open
# ---------------------------------------------------------------------------
def capture_0945(day: str, computed_dir=None) -> Optional[dict]:
    from . import dealer_block                                  # noqa: PLC0415
    cfg = dealer_block.config()
    caps = [c for c in dealer_block.captures_on(day, "SPY", computed_dir)
            if not c.get("error") and dealer_block.slot_of(c, cfg) == "09:45"]
    return max(caps, key=lambda c: c.get("fetched_at") or "") if caps else None


def wait_for_capture(day: str, minutes: float, computed_dir=None) -> Optional[dict]:
    """The bounded wait (the order, block 3): poll every 20 s, then give up."""
    end = time.monotonic() + 60.0 * float(minutes)
    while True:
        c = capture_0945(day, computed_dir)
        if c or time.monotonic() >= end:
            return c
        time.sleep(20)


def open_block(day: str, prior: str, cutoff: str, db_path=None, computed_dir=None,
               cap: Optional[dict] = None, gauge: Optional[dict] = None) -> dict:
    from . import dealer_block, opening_setup                  # noqa: PLC0415
    out = {"title": "The open", "as_of": nc.hm_et(cutoff), "lines": [], "values": {}}
    v = out["values"]
    if gauge is None:
        c07 = nc.iso(nc.et(day, "07:00"))
        pm = opening_setup.premarket_from_store(day, c07, db_path)
        gauge = opening_setup.gauge_from_store(prior, c07, db_path,
                                               premarket=(pm.get("values") or {}).get("spy"))
    g = (gauge or {}).get("values") or {}
    sig = g.get("sigma_1_pct")
    v["sigma_1_pct"] = round(float(sig), 2) if sig is not None else None
    bars = nc.read_bars("spy", nc.et(day, "09:30"), nc.et(day, "09:45"), cutoff, db_path)
    first = nc.first_from(bars, nc.et(day, "09:30"))
    pc = nc.daily_close_before("yfinance.mkt_spy", day, cutoff, db_path)
    if not first or not pc:
        out["lines"].append("SPY: the 09:30 open or the prior close is not stored.")
    else:
        v["prior_close"], v["open"] = round(pc[1], 2), round(float(first["open"]), 2)
        v["gap_pct"] = nc.pct(pc[1], first["open"])
        f15 = [b for b in bars if nc.parse(b["observed_at"]) < nc.et(day, "09:45")]
        hi, lo = max(b["high"] for b in f15), min(b["low"] for b in f15)
        v["range_pct"] = round(100.0 * (hi - lo) / float(first["open"]), 2)
        v["high"], v["low"] = round(hi, 2), round(lo, 2)
        rel = ""
        if v["sigma_1_pct"] is not None:
            v["gap_outside"] = abs(v["gap_pct"]) > v["sigma_1_pct"]
            v["range_outside"] = v["range_pct"] > v["sigma_1_pct"]
            rel = (f" The gauge's implied one-session move, as the 07:00 anchor printed it: "
                   f"{v['sigma_1_pct']:.2f}%; the gap is "
                   f"{'outside' if v['gap_outside'] else 'inside'} it and the range "
                   f"{'outside' if v['range_outside'] else 'inside'} it.")
        else:
            rel = " The gauge's implied move is not stored."
        out["lines"].append(
            f"SPY opened {v['open']:,.2f}, {nc.signed(v['gap_pct'])} against the prior close "
            f"{v['prior_close']:,.2f} ({pc[0]}); the first fifteen minutes ran "
            f"{v['low']:,.2f} to {v['high']:,.2f}, a range of {v['range_pct']:.2f}%.{rel}")
    last = nc.last_ending_by(bars, nc.et(day, "09:45"))
    spot = float(last["close"]) if last else None
    v["spot"] = round(spot, 2) if spot else None
    prof = dealer_block.newest_settled(prior, "SPY", computed_dir)
    out["lines"].append(_levels_line("the 07:00 anchor's profile (" + prior + " close)",
                                     prof, spot, v, "anchor"))
    if cap is None:
        out["lines"].append("09:45 capture pending.")
        v["capture"] = "pending"
    else:
        out["lines"].append(_levels_line("the 09:45 capture", cap, spot, v, "c0945"))
        v["capture"] = "read"
    out["lines"].append(dealer_block.config().get("convention_line")
                        or "Sign convention: dealers-hand-v1.")
    out["lines"].append("Our own engine's levels; no vendor value is read or printed.")
    return out


def _levels_line(what: str, p: Optional[dict], spot: Optional[float], v: dict,
                 tag: str) -> str:
    if not p:
        return f"Levels from {what}: not stored."
    o = p.get("overall") or {}
    lv = {k: o.get(k) for k in ("gamma_flip", "call_wall_otm", "put_wall_otm")}
    v[f"levels_{tag}"] = {k: (round(float(x), 2) if x is not None else None)
                          for k, x in lv.items()}
    if spot is None:
        return f"Levels from {what}: SPY's 09:45 price is not stored."
    names = {"gamma_flip": "the flip", "call_wall_otm": "the call wall",
             "put_wall_otm": "the put wall"}
    parts = [f"{'above' if spot > float(x) else 'below'} {names[k]} {float(x):,.2f}"
             for k, x in lv.items() if x is not None]
    return (f"SPY {spot:,.2f} against {what}: " + ("; ".join(parts) if parts
                                                   else "no levels in the profile") + ".")


# ---------------------------------------------------------------------------
# The payload
# ---------------------------------------------------------------------------
def build(day: Optional[str] = None, as_of: Optional[str] = None, db_path=None,
          computed_dir=None, run_id: Optional[str] = None, wait_minutes: float = 0.0,
          rels=None) -> dict:
    from altdata import session                                 # noqa: PLC0415
    from . import morning_payload                               # noqa: PLC0415
    day = day or session.session_date()
    cutoff = as_of or session.utc_iso(timespec="seconds")
    prior = session.previous_trading_session(day).isoformat()
    cfg = nc.config()
    ocfg = cfg.get("open") or {}
    cap = wait_for_capture(day, wait_minutes, computed_dir) if wait_minutes else \
        capture_0945(day, computed_dir)
    b1 = releases_block(day, cutoff, db_path, rels)
    rel_day = bool(b1["releases"])
    b2 = reaction_block(day, cutoff, db_path) if rel_day else None
    b3 = open_block(day, prior, cutoff, db_path, computed_dir, cap)
    nw = nc.news(nc.et(day, ocfg.get("news_after") or "07:00"), cutoff,
                 max_n=int(ocfg.get("news_max") or 5), db_path=db_path)
    b4 = {"title": "News since 07:00", "as_of": nc.hm_et(cutoff),
          "lines": nc.news_lines(nw, "No stored item published since 07:00.")}
    b5 = {"title": "Book C", "as_of": nc.hm_et(cutoff), "lines": [BOOK_C_LINE]}
    b6 = {"title": "What the close will check", "as_of": nc.hm_et(cutoff),
          "lines": [close_check(b2, b3)]}
    vol = morning_payload.stored_vol_event(prior, nc.iso(nc.et(day, "07:00")), db_path)
    v3 = b3["values"]
    gate = {"tier1_release": any(r["tier"] == 1 for r in b1["releases"]),
            "gap_outside": bool(v3.get("gap_outside")),
            "range_outside": bool(v3.get("range_outside")),
            "vol_trigger": bool((vol or {}).get("fired"))}
    blocks = [b for b in (b1, b2, b3, b4, b5, b6) if b]
    return {"report": REPORT, "session": day, "prior_session": prior, "as_of": cutoff,
            "run_id": run_id, "blocks": blocks, "releases": b1["releases"],
            "reaction": (b2 or {}).get("moves") or {}, "open": v3, "news": nw,
            "gate": gate, "gate_open": any(gate.values()),
            "vol_trigger_line": (vol or {}).get("trigger_line") if gate["vol_trigger"] else None,
            "budget": (cfg.get("budget") or {}).get("open_note") or {"words": 250, "charts": 1},
            "reading_target_minutes": (cfg.get("reading") or {}).get("open_note", 2)}


def close_check(b2: Optional[dict], b3: dict) -> str:
    v = b3.get("values") or {}
    lv = v.get("levels_c0945") or v.get("levels_anchor") or {}
    parts = []
    if lv.get("gamma_flip") is not None:
        parts.append(f"SPY against the flip {lv['gamma_flip']:,.2f}")
    walls = [f"{lv[k]:,.2f}" for k in ("put_wall_otm", "call_wall_otm") if lv.get(k) is not None]
    if walls:
        parts.append("the walls " + " and ".join(walls))
    if b2 and b2.get("moves"):
        parts.append("the release reactions for " + ", ".join(
            {"es": "ES", "y10": "the 10-year", "zn": "ZN", "zt": "ZT", "dxy": "the dollar",
             "vix": "VIX"}[k] for k in b2["moves"]) + " from 09:45 to the 16:00 close")
    return ("The 16:45 close re-reads " + "; ".join(parts) + ".") if parts else \
        "The 16:45 close re-reads the session whole; nothing here is carried."


def subject_of(p: dict) -> tuple[str, str]:
    """(the code-written subject, its figure-free fallback)."""
    parts = []
    for r in p.get("releases") or []:
        pr = next((x for x in r["prints"] if x.get("actual_text")), None)
        if pr:
            parts.append(f"{r['label'].split(' (')[0]} {pr['actual_text']}"
                         + (" m/m" if pr.get("form") == "mom" else ""))
            break
    y = (p.get("reaction") or {}).get("y10")
    if y and y.get("move") is not None:
        parts.append(f"10-year {y['move']:+.1f}bp since {y['from_at'][:5]}")
    o = p.get("open") or {}
    if o.get("gap_outside") is not None:
        out = o.get("gap_outside") or o.get("range_outside")
        parts.append(f"open {'outside' if out else 'inside'} the expected move")
    txt = "Open note: " + ("; ".join(parts) if parts else "the open, no release")
    return txt, "Open note: " + ("release day" if p.get("releases") else "the open")


SYSTEM_EXTRA = ("The open note covers 07:00 to 09:45: the 08:30 releases with no "
                "consensus (say so if you cite a print), the market's reaction, the open "
                "against the gauge's implied move and our own engine's levels, and the "
                "news. It may not suggest a Book C draft.")


def render(p: dict, prose_text: Optional[str], chart_src: Optional[str]) -> tuple[str, str]:
    intro = [f"Session {p['session']}; as of {nc.hm_et(p['as_of'])}. Secondary: the 07:00 "
             "anchor and the 16:45 close remain the reports of record.",
             "Sources: Yahoo 5-minute bars (delayed by up to 15 minutes for some "
             "exchanges); FRED; the agencies' feeds; the voices scan."]
    footer = [f"Reading target {p['reading_target_minutes']} minutes; estimated "
              f"{p.get('reading_minutes', 'n/a')}. Prose: {p.get('prose_state')}."]
    title = f"Open note, {p['session']}"
    return (nc.page(title, intro, p["blocks"], prose_text, footer, chart_src),
            nc.text_page(title, intro, p["blocks"], prose_text, footer))


def main(argv=None) -> int:
    from altdata import session                                 # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m daily_cascade.open_note")
    ap.add_argument("--date")
    ap.add_argument("--as-of")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--email", action="store_true",
                    help="mail a dry run (a dry run before live_from is mailed anyway)")
    ap.add_argument("--archive-dir")
    ap.add_argument("--db")
    ap.add_argument("--computed-dir")
    ap.add_argument("--no-narrative", action="store_true")
    ap.add_argument("--no-wait", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO if a.verbose else logging.WARNING)
    day = a.date or session.session_date()
    cfg = nc.config()
    forced = a.dry_run
    dry = nc.is_dry(day, forced, cfg)
    email = a.email or (dry and not forced)
    archive_dir = nc.dryrun_dir(a.archive_dir, dry)
    run_id = session.new_run_id(REPORT)
    wait = 0.0 if a.no_wait else float((cfg.get("open") or {}).get("capture_wait_minutes") or 0)
    p = build(day, a.as_of, a.db, a.computed_dir, run_id, wait)
    return finish(p, cfg, dry=dry, email=email, archive_dir=archive_dir,
                  narrative=not a.no_narrative, run_id=run_id, db_path=a.db)


def finish(p: dict, cfg: dict, *, dry: bool, email: bool, archive_dir, narrative: bool,
           run_id: str, prose_fn=None, db_path=None) -> int:
    budget = p["budget"]
    pr = {"state": "gate closed", "text": None, "reason": "no gate opened"}
    if p["gate_open"] and narrative:
        pr = (prose_fn or nc.prose)(p, report=REPORT, words_cap=int(budget["words"]),
                                    run_id=run_id, extra=SYSTEM_EXTRA,
                                    model=(cfg.get("open") or {}).get("model"))
    elif p["gate_open"]:
        pr = {"state": "skipped", "text": None, "reason": "--no-narrative"}
    p["prose_state"] = pr["state"] + (f" ({pr['reason']})" if pr.get("reason") else "")
    ch = None
    if p["releases"] and int(budget.get("charts") or 0) >= 1:
        bars = nc.read_bars("es", nc.et(p["session"], "08:25"), nc.et(p["session"], "09:45"),
                            p["as_of"], db_path)
        ch = nc.chart(bars, "ES since 08:25 (5-minute)", f"open_note_{p['session']}_es")
    p["reading_minutes"] = nc.reading_minutes(p["blocks"], pr.get("text"), 1 if ch else 0)
    subj, fb = subject_of(p)
    subj, audited = nc.subject(subj, p, fb)
    p["subject_audited"] = audited
    name = f"open_note_{p['session']}.html"
    mail, text = render(p, pr.get("text"), f"cid:{ch['cid']}" if ch else None)
    arch, _ = render(p, pr.get("text"), nc.data_uri(ch["png"]) if ch else None)
    if pr["state"] not in ("published", "gate closed", "skipped"):
        from altdata import withheld_log                         # noqa: PLC0415
        withheld_log.record(REPORT, name, [("prose", f"{pr['state']}: {pr['reason']}")],
                            archive_dir)
    p.pop("budget", None)
    out = nc.ship(name=name, subject_line=subj, payload=p, mail_html=mail, archive_html=arch,
                  text=text, dry=dry, email=email, archive_dir=archive_dir, chart_obj=ch)
    print(f"open note {p['session']}: {out.get('delivery')} -> {out.get('archive_path')}; "
          f"subject {out.get('subject')!r}; prose {p['prose_state']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
