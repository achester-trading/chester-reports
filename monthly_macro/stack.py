"""
The ten-section stack on the Monthly, first half. (reporting-stack brief; Tranche T3)

    from monthly_macro import stack
    ed = stack.build(payload, prior=None, db_path=None)
    stack.apply_prose(ed, written)        # monthly_macro.prose.write_all(..., ed=ed)
    stack.enforce_budget(ed)

THE WEEKLY'S PATH, AT THE MONTHLY'S DEPTHS. The sections are built by the same
builders the Weekly uses (daily_cascade.weekly_stack: plumbing, positioning,
what's priced, what doesn't fit) over the MONTH's window, and assembled by the
one function every cadence uses (daily_cascade.stack.assemble, cadence
"monthly", reading the Monthly column of config/reporting_stack.yaml): the same
order, claim lines, change marks against the PRIOR MONTHLY, and collapse rule.

MONTHLY v2 PHASE A IS RECONCILED INTO THE TEN, each part printed once:

  the month in markets   its scorecard table is The tape's; its prose is The
                         read's paragraphs (claim = its first sentence)
  the one page           The read's sub-section: the five takeaways, as prose
                         when written, as lines when withheld
  looking back by theme  each theme a sub-section of Narratives -- its prose,
                         its series, its CONSENSUS and NEW developments; the
                         DISSENT and CORRECTION developments go to What doesn't
                         fit; "what changed" is the header's "Changed since last
                         Monthly", as the Weekly's is
  voices                 Narratives' sub-sections (the table, consensus against
                         contrarian, the four weeks by story)
  looking ahead          Ahead: its prose, the calendar by period, the scenario
                         weights with Brier and signposts; the month's graded
                         calls beside them
  where our read lands   The book: its prose, and the bound restated beneath it,
                         bounded as now

The Phase A "in one line each" summary is not carried: it was each theme's first
sentence printed a second time.

THE OLDER SECTIONS, in the brief's order. Slow layers (the matrix's last row, the
Monthly only) follows The book: valuation, base rates (Top & Bottom and the
bear-rally base rate), tails, themes (the alternative assets). The rest of the
old record prints after it as the DETAIL TABLES: the regime (dials and
dimensions; the open contradictions and exceptions are What doesn't fit's), the
scenario record (only the weights Ahead does not already print), the register's
month, and the appendix.

EVERY PRINTED PHASE A FACT CARRIES AN ID (`phase_a`), so the gate can hold the
edition to "nothing lost, nothing twice". Reads only. Never raises on a section:
a builder that fails prints its FAULT in that section's footnote.
"""

from __future__ import annotations

import copy
import datetime as dt
import json
import logging
import math
import re
from pathlib import Path
from typing import Any, Optional

from altdata import observations, session

from daily_cascade import readability as rd
from daily_cascade import stack as stack_mod
from daily_cascade.stack import item

from . import dealer as dealer_mod

log = logging.getLogger("monthly_macro.stack")

CADENCE = "monthly"
SLOW_ID = "slow"

# THE WEEKLY'S BUILDERS SPEAK OF A WEEK; over a month's window the same lines are
# the month's. Applied, in order, to every string those builders return. (RTAT10's
# "prior" is still the week before the window opens, and is labelled so.)
PERIOD_WORDS = (("on the week", "on the month"), ("this week", "this month"),
                ("This week", "This month"),
                ("the week before", "the week before the month"),
                ("Week or prior", "Month or prior"),
                ("the week's sector", "the month's sector"),
                ("at the week's end", "at the month's end"),
                ("At the week's end", "At the month's end"),
                ("week mean", "month mean"),
                ("since the prior report", "on the month"))


def edition_name(report_date: str) -> str:
    return f"monthly_macro_{report_date}_stack.json"


def load_prior(report_date: str, archive_dir: Optional[str]) -> Optional[dict]:
    """The newest stacked Monthly archived strictly before `report_date` -- the
    marks compare against the PRIOR MONTHLY, never a Weekly or a close."""
    if not archive_dir or not Path(archive_dir).exists():
        return None
    best = None
    for f in Path(archive_dir).glob("monthly_macro_*_stack.json"):
        m = re.match(r"monthly_macro_(\d{4}-\d{2}-\d{2})_stack\.json$", f.name)
        if m and m.group(1) < report_date and (best is None or m.group(1) > best[0]):
            best = (m.group(1), f)
    if not best:
        return None
    try:
        return json.loads(best[1].read_text(encoding="utf-8"))
    except ValueError:
        return None


def save_edition(ed: dict, archive_dir: Optional[str]) -> Optional[str]:
    from daily_cascade import deliver                            # noqa: PLC0415
    return deliver.archive(json.dumps(ed, indent=2, default=str, sort_keys=True),
                           edition_name(ed["report_date"]), archive_dir)


def window(p: dict) -> tuple[str, str, str, str]:
    """(first session day, month-end, then-cutoff, now-cutoff). The month is the
    one Phase A's scorecard reads (v2.month_bounds): the close on or before the
    prior month-end against the close on or before this month-end."""
    from . import v2                                             # noqa: PLC0415
    start, end = v2.month_bounds(p)
    now = str(p.get("as_of") or session.utc_iso())
    then = f"{start.isoformat()}T23:59:59+00:00"
    first = (start + dt.timedelta(days=1)).isoformat()
    return first, end.isoformat(), then, now


def _month_words(v: Any) -> Any:
    if isinstance(v, str):
        for a, b in PERIOD_WORDS:
            v = v.replace(a, b)
        return v
    if isinstance(v, list):
        return [_month_words(x) for x in v]
    if isinstance(v, tuple):
        return tuple(_month_words(x) for x in v)
    if isinstance(v, dict):
        out = {k: (_month_words(x) if k not in ("fingerprint", "key") else x)
               for k, x in v.items()}
        if isinstance(out.get("columns"), list):
            out["columns"] = ["The month" if c == "Week" else c
                              for c in out["columns"]]
        return out
    return v


def _fault(sid: str, exc: Exception) -> dict:
    log.warning("monthly stack: %s unavailable", sid, exc_info=True)
    return {"items": [], "not_tracked": [], "data": {},
            "notes": [f"FAULT (code, not data) -- {type(exc).__name__}: {exc}"]}


def _cell(v: Any) -> str:
    return str("—" if v in (None, "") else v).replace("\n", " ")


def _v(x: Any, dp: int = 2) -> str:
    if x is None:
        return "—"
    try:
        return f"{float(x):,.{dp}f}"
    except (TypeError, ValueError):
        return str(x)


def _cite(s: Optional[dict]) -> str:
    if not s:
        return "—"
    tier = f", tier {s['tier']}" if s.get("tier") is not None else ""
    title = f"{s.get('title')}, " if s.get("title") else ""
    return f"{title}{s.get('date')}{tier}"


# ---------------------------------------------------------------------------
# 1. The read: the month in markets' prose and the one page
# ---------------------------------------------------------------------------
def read_section(p: dict) -> dict:
    op = p.get("month_in_one_page") or {}
    takes = op.get("takeaways") or []
    items = [item(f"read:take:{t.get('n')}", str(t.get("text")), 1, t.get("text"))
             for t in takes]
    for it in items:
        it["show"] = False
    cites = "; ".join(_cite(s) for t in takes for s in (t.get("sources") or [])[:1])
    sub = {"title": "The month in one page", "phase": "month_in_one_page",
           "lines": [f"{t['n']}. {t['text']}" for t in takes],
           "not_tracked": ([] if takes else [op.get("reason") or
                                             "no takeaway this month"])}
    return {"items": items, "print_items": False, "subsections": [sub],
            "notes": ([f"The takeaways are built from: {cites}."] if cites else []),
            "phase_a": ["month_in_markets:prose"]
            + (["month_in_one_page:takeaways"] if takes else []),
            "data": {"takeaways": [t.get("text") for t in takes],
                     "month": (p.get("month_in_markets") or {}).get("month")}}


# ---------------------------------------------------------------------------
# 2. The tape: the scorecard (light) and the long frame (brief 3.4)
# ---------------------------------------------------------------------------
def _move(r: dict) -> str:
    if r.get("change_unit") == "bps":
        return stack_mod._signed(r.get("change"), "bp")
    if r.get("change_unit") == "percent":
        return stack_mod._signed(r.get("change"), "%")
    return _v(r.get("change"), 4)


def _lvl(r: dict, which: str) -> str:
    v = r.get(f"{which}_level")
    return f"{_v(v)}%" if r.get("change_unit") == "bps" else _v(v)


def _closes(st, key: str, now: str) -> list[tuple[str, float]]:
    return sorted((str(r["observed_at"])[:10], float(r["value_num"]))
                  for r in st.as_of(key, now) if r.get("value_num") is not None)


def _ytd_fund(st, key: str, start: str, end: str, now: str) -> Optional[dict]:
    """Total return from the last close on or before `start` to the last on or
    before `end`, a dividend added on its ex-date and not reinvested."""
    px = [x for x in _closes(st, key, now) if x[0] <= end]
    p0 = [x for x in px if x[0] <= start]
    if not p0 or not px or px[-1][0] <= p0[-1][0]:
        return None
    (d0, v0), (d1, v1) = p0[-1], px[-1]
    div = sum(v for d, v in _closes(st, f"{key}_dividend", now) if d0 < d <= d1)
    return {"from": d0, "to": d1, "pct": round(100.0 * ((v1 + div) / v0 - 1.0), 2),
            "dividends": round(div, 4)}


def _ytd_bill(st, key: str, start: str, end: str, now: str) -> Optional[dict]:
    """Cash: the 3-month bill as Book Z accrues it, rate x calendar days / 360,
    each day at the latest rate observed before it."""
    rates = [x for x in _closes(st, key, now) if x[0] <= end]
    if not rates or rates[0][0] > start:
        return None
    d, stop = dt.date.fromisoformat(start), dt.date.fromisoformat(min(end, rates[-1][0]))
    if stop <= d:
        return None
    val, i, r = 1.0, 0, None
    while d < stop:
        while i < len(rates) and rates[i][0] <= d.isoformat():
            r = rates[i][1]
            i += 1
        val *= 1.0 + (r or 0.0) / 100.0 / 360.0
        d += dt.timedelta(days=1)
    return {"from": start, "to": stop.isoformat(),
            "pct": round(100.0 * (val - 1.0), 2), "dividends": None}


def cross_asset_ytd(st, last: str, now: str, cfg: dict) -> dict:
    """GTM-14: the quilt's current column, from the proxies the store holds,
    ranked. Code-written; a class without a proxy or without closes says why."""
    year = int(str(last)[:4])
    start, end = f"{year - 1}-12-31", str(last)[:10]
    got, nt = [], []
    for c in cfg.get("monthly_cross_asset_ytd") or []:
        if c.get("absent") or not c.get("key"):
            nt.append(f"{c['label']} year to date: {c.get('absent') or 'no proxy'}")
            continue
        fn = _ytd_bill if c.get("kind") == "bill" else _ytd_fund
        r = fn(st, c["key"], start, end, now)
        if r is None:
            nt.append(f"{c['label']} year to date ({c['proxy']}): the store holds no "
                      f"close at both {start} and the month end")
            continue
        got.append({**c, **r})
    got.sort(key=lambda r: -r["pct"])
    rows = [[n, r["label"], str(r["proxy"]), f"{r['pct']:+.2f}%"]
            for n, r in enumerate(got, start=1)]
    ends = sorted({r["to"] for r in got})
    note = (f"Total return from the {start} close to the {end} close"
            + (f" (latest close {ends[0]})" if ends and ends[0] != end else "")
            + ": a fund's dividends added on their ex-dates, not reinvested; cash "
              "at the 3-month bill, rate x days / 360. Proxies are funds, not the "
              "indices JPM's quilt uses (GTM-14).")
    return {"rows": rows, "not_tracked": nt, "note": note if rows else None,
            "data": [{"rank": n, "class": r["label"], "proxy": r["proxy"],
                      "ytd_pct": r["pct"], "from": r["from"], "to": r["to"]}
                     for n, r in enumerate(got, start=1)]}


def tape_section(p: dict, book: Optional[dict], st=None, last: Optional[str] = None,
                 now: Optional[str] = None, cfg: Optional[dict] = None) -> dict:
    m = p.get("month_in_markets") or {}
    rows = m.get("rows") or []
    items, trows = [], []
    for r in rows:
        items.append(item(f"tape:{r['id']}", f"{r['label']} {_lvl(r, 'end')}, "
                          f"{_move(r)} on the month.", 1 if r is rows[0] else 2,
                          (r.get("end_level"), r.get("change"))))
        trows.append([r["label"], _lvl(r, "start"), _lvl(r, "end"), _move(r),
                      _v(r.get("percentile"), 1)])
    table = {"columns": ["Market", f"Close, {m.get('start')}", f"Close, {m.get('end')}",
                         "Move", "Level, 5y percentile"], "rows": trows}
    # THE LONG FRAME: levels, never signals; a cross counts only after the
    # monthly close (item 10). The 40-week, 10-month and 20-month averages from
    # the level list, beside the month-end close and the drawdown.
    lf_rows, lf_data, nt = [], [], []
    for i in (book or {}).get("instruments") or []:
        lv = {x["type"]: x["value"] for x in i.get("levels") or []}
        if not any(k in lv for k in ("ma_40w", "ma_10m", "ma_20m")):
            continue
        close = (i.get("frame") or {}).get("last")
        dd = (i.get("row") or {}).get("drawdown_52w_pct")
        lf_rows.append([i["label"], _v(close), _v(lv.get("ma_40w")),
                        _v(lv.get("ma_10m")), _v(lv.get("ma_20m")),
                        "—" if dd is None else f"{dd:+.2f}%"])
        lf_data.append({"market": i["label"], "close": close,
                        "ma_40w": lv.get("ma_40w"), "ma_10m": lv.get("ma_10m"),
                        "ma_20m": lv.get("ma_20m"), "drawdown_52w_pct": dd})
    if not lf_rows:
        nt.append("the long-frame averages (40-week, 10-month, 20-month): the store "
                  "holds too few daily closes to resample")
    subs = [{"title": "The long frame: levels, never signals",
             "table": {"columns": ["Market", "Month-end close", "40-week average",
                                   "10-month average", "20-month average",
                                   "From the 52-week high"], "rows": lf_rows},
             "not_tracked": nt}]
    ytd = None
    if st is not None and last and now:
        try:
            ytd = cross_asset_ytd(st, last, now, cfg or {})
        except Exception as exc:                                # noqa: BLE001
            log.warning("cross-asset year to date unavailable", exc_info=True)
            nt.append(f"the cross-asset year to date: FAULT {exc}")
    if ytd is not None:
        subs.append({"title": "Across assets, year to date",
                     "table": {"columns": ["Rank", "Asset class", "Proxy",
                                           "Year to date"], "rows": ytd["rows"]},
                     "notes": [ytd["note"]] if ytd["note"] else [],
                     "not_tracked": ytd["not_tracked"]})
        items.extend(item(f"tape:ytd:{r['class']}", f"{r['class']} "
                          f"{r['ytd_pct']:+.2f}% year to date", 3,
                          (r["rank"], r["ytd_pct"])) for r in ytd["data"])
    levels = [{"symbol": i.get("symbol"), "name": i.get("label"),
               **{x["label"]: x["value"] for x in i.get("levels") or []
                  if x["type"] in ("ma_40w", "ma_10m", "ma_20m")}}
              for i in (book or {}).get("instruments") or []]
    return {"items": items, "print_items": False, "table": table,
            "subsections": subs,
            "not_tracked": [x.split(" (")[0] for x in m.get("missing") or []],
            "phase_a": [f"month_in_markets:row:{r['id']}" for r in rows],
            "data": {"month": m.get("month"), "from": m.get("start"),
                     "to": m.get("end"),
                     "moves": [{"market": r["label"], "move": _move(r),
                                "level_percentile_5y": r.get("percentile")}
                               for r in rows],
                     "long_frame": lf_data, "levels": levels,
                     "cross_asset_ytd": (ytd or {}).get("data") or []}}


# ---------------------------------------------------------------------------
# 3. Mechanics: the dealer retrospective (brief 1.2)
# ---------------------------------------------------------------------------
def mechanics_section(st, first: str, last: str, now: str, cfg: dict) -> dict:
    r = dealer_mod.retrospective(st, first, last, now, cfg)
    c = r["counts"]
    items = [item("mech:sessions", f"SPY over {c['sessions']} scored session(s): "
                  f"{c['positive_gamma']} in positive net GEX, {c['negative_gamma']} "
                  f"in negative; the morning flip crossed on {c['flip_crossed']}.", 1,
                  (c["sessions"], c["positive_gamma"], c["flip_crossed"]))]
    for k, lab in dealer_mod.FLAGS:
        items.append(item(f"mech:{k}", f"{lab[0].upper() + lab[1:]} on {c[k]} of "
                          f"{c[k + '_scored']} session(s).", 2, (c[k], c[k + "_scored"])))
    subs = []
    if r["summary_table"]:
        subs.append({"title": "The month's counts and hit rates",
                     "table": r["summary_table"], "lines": r["lines"]})
    else:
        subs.append({"title": "The month's counts and hit rates", "lines": r["lines"]})
    if r["sessions"]:
        subs.append({"title": "Ranges and flags, by session",
                     "table": r["ranges_table"],
                     "table_note": "Flags are computed by the Weekly's rule "
                                   "(config/reporting_stack.yaml dealer_flags), "
                                   "never by the model."})
    return {"items": items, "print_items": False,
            "table": r["table"] if r["sessions"] else None,
            "subsections": subs,
            "not_tracked": ([] if r["sessions"] else
                            ["the dealer scorecard: the close stores one per session "
                             "from the first stacked close on"]),
            "prose_wanted": not r["insufficient"],
            "data": {"retrospective": {k: r[k] for k in ("counts", "rates",
                                                         "insufficient",
                                                         "min_sessions")},
                     "sessions": [{"session": x["session"],
                                   "gamma_regime": x["gamma_regime"],
                                   "flags": x["flags"], "iv_check": x["iv_check"]}
                                  for x in r["sessions"]]},
            "_retro": r}


# ---------------------------------------------------------------------------
# 4. What doesn't fit: the gaps, and Phase A's dissent and corrections
# ---------------------------------------------------------------------------
def month_in_state(p: dict) -> dict:
    """The Weekly's `week_in_state` shape, from the Monthly's regime block."""
    rg = p.get("regime") or {}
    return {"contradictions": [c for c in rg.get("contradictions") or []
                               if c.get("open_state") == "open"],
            "exceptions_opened": rg.get("exceptions_opened") or [],
            "exceptions_intraweek_only": [],
            "exceptions_open_now": rg.get("exceptions_open_now") or []}


MISFIT_TAGS = ("DISSENT", "CORRECTION")


def _dev_row(it: dict) -> list:
    corr = (f" (corrects: {it['corrects']['statement']})" if it.get("corrects") else "")
    return [str(it.get("text")) + corr, it.get("tag"),
            "; ".join(_cite(s) for s in (it.get("sources") or [])[:2])]


def misfit_section(p: dict, st, now: str, pmb: Optional[dict]) -> dict:
    from daily_cascade import weekly_stack as ws                 # noqa: PLC0415
    from daily_cascade.stack_close import _contradiction_history  # noqa: PLC0415
    mis = month_in_state(p)
    hist = {c["id"]: _contradiction_history(st, c["id"], now)
            for c in mis["contradictions"]}
    b = _month_words(ws.misfit_week(mis, pmb, hist))
    rows, ids = [], []
    for t in (p.get("looking_back") or {}).get("themes") or []:
        for n, it in enumerate(t.get("items") or []):
            if it.get("tag") in MISFIT_TAGS:
                rows.append([t.get("name")] + _dev_row(it))
                ids.append(f"looking_back:{t['theme']}:item:{n}")
                b["items"].append(item(f"misfit:dev:{t['theme']}:{n}",
                                       f"{it.get('tag')}: {it.get('text')}", 2,
                                       (it.get("tag"), it.get("text"))))
                b["items"][-1]["show"] = False
    b["items"] = [i for i in b["items"] if i["key"] != "misfit:none" or not rows]
    b.setdefault("subsections", []).append(
        {"title": "Dissent and corrections this month",
         "table": {"columns": ["Theme", "Development", "Tag", "Source"],
                   "rows": rows}})
    b["phase_a"] = ids
    return b


# ---------------------------------------------------------------------------
# 5-7. Plumbing, positioning, what's priced: the Weekly's builders, the month
# ---------------------------------------------------------------------------
def plumbing_section(st, now: str, then: str, on_tape: set) -> dict:
    """The Weekly's Plumbing over the month. A rate or spread the tape's
    scorecard already prints (its month-end level and move) is not printed a
    second time here; the footnote says where it is, and the prose still reads
    it."""
    from daily_cascade import weekly_stack as ws                 # noqa: PLC0415
    b = _month_words(ws.plumbing_week(st, now, then, None))
    names = {name: k for k, name in ws.PLUMB}
    rows = (b.get("table") or {}).get("rows") or []
    moved = [r[0] for r in rows if names.get(r[0]) in on_tape]
    if moved:
        b["table"]["rows"] = [r for r in rows if names.get(r[0]) not in on_tape]
        b.setdefault("notes", []).append(
            f"In The tape's table: {', '.join(moved)}.")
    b["_printed"] = [names[r[0]] for r in b["table"]["rows"] if r[0] in names]
    return b


def positioning_section(st, now: str, then: str) -> dict:
    from daily_cascade import weekly_stack as ws                 # noqa: PLC0415
    b = ws.positioning_week(st, now, then)
    b.pop("_cftc_series", None)
    b.pop("_leadership", None)
    return _month_words(b)


def priced_section(st, now: str, then: str, cfg: dict, pmb, fed, fed_then) -> dict:
    from daily_cascade import weekly_stack as ws                 # noqa: PLC0415
    b = ws.priced_week(st, now, then, cfg, pmb, fed, fed_then)
    # The Monthly's What's priced is deep by the matrix; no trigger deepens it.
    b["deep_reason"] = None
    return _month_words(b)


# ---------------------------------------------------------------------------
# 8. Narratives: the themes, the voices
# ---------------------------------------------------------------------------
def _series_rows(rows: list[dict]) -> list[list]:
    out = []
    for r in rows:
        if "latest_pct" in r:
            lvl = f"{_v(r['latest_pct'])}%"
            mv = (stack_mod._signed(r["change_bps"], "bp") if "change_bps" in r
                  else "—")
        else:
            lvl = r.get("latest_level_display") or _v(r.get("latest_level"))
            mv = (stack_mod._signed(r["change_pct"], "%") if "change_pct" in r else
                  r.get("change_display") or (_v(r["change"]) if "change" in r
                                              else "—"))
        out.append([r.get("label"), lvl, r.get("latest_date"), mv,
                    r.get("since") or "—"])
    return out


def narratives_section(p: dict, on_tape: Optional[set] = None,
                       in_plumbing: Optional[set] = None) -> dict:
    lb = p.get("looking_back") or {}
    items, subs, ids = [], [], []
    on_tape = on_tape or set()
    in_plumbing = in_plumbing or set()
    printed: list[str] = []
    # A SERIES TWO THEMES SHARE PRINTS ONCE, under the first theme that lists it;
    # the later theme's footnote names where it is (its prose still reads it).
    shown: dict[str, str] = {}
    for t in lb.get("themes") or []:
        devs = [(n, it) for n, it in enumerate(t.get("items") or [])
                if it.get("tag") not in MISFIT_TAGS]
        for n, it in devs:
            items.append(item(f"narr:{t['theme']}:{n}", str(it.get("text")), 2,
                              (it.get("tag"), it.get("text"))))
            items[-1]["show"] = False
        # The tape's scorecard markets print there, once.
        own = [r for r in t.get("rows") or [] if r.get("label") not in shown
               and r.get("metric") not in on_tape | in_plumbing]
        elsewhere = [f"{r.get('label')} (under {shown[r.get('label')]})"
                     for r in t.get("rows") or [] if r.get("label") in shown]
        elsewhere += [f"{r.get('label')} (in The tape)"
                      for r in t.get("rows") or [] if r.get("metric") in on_tape
                      and r.get("label") not in shown]
        elsewhere += [f"{r.get('label')} (in Plumbing & rates)"
                      for r in t.get("rows") or [] if r.get("metric") in in_plumbing
                      and r.get("metric") not in on_tape
                      and r.get("label") not in shown]
        printed += [r.get("metric") for r in own if r.get("metric")]
        for r in own:
            shown[r.get("label")] = t.get("name")
        subs.append({"title": t.get("name"), "phase": f"theme:{t['theme']}",
                     "table": {"columns": ["Series", "Latest", "Date", "Change",
                                           "Since"], "rows": _series_rows(own)},
                     "tables": [{"columns": ["Development", "Tag", "Source"],
                                 "rows": [_dev_row(it) for _, it in devs]}],
                     "notes": ([f"Also read here: {'; '.join(elsewhere)}."]
                               if elsewhere else []),
                     "not_tracked": list(t.get("not_yet_tracked") or [])})
        ids += [f"theme:{t['theme']}:prose"]
        ids += [f"looking_back:series:{r.get('label')}" for r in own]
        ids += [f"looking_back:{t['theme']}:item:{n}" for n, _ in devs]
    vb = p.get("voices") or {}
    nt = []
    if vb.get("state") in ("ok", "empty"):
        if vb.get("state") == "empty":
            nt.append(str(vb.get("reason") or "no voice stored this month"))
        if (vb.get("table") or {}).get("rows"):
            subs.append({"title": "Voices", "table": vb["table"],
                         "lines": ([f"Consensus against contrarian: "
                                    f"{vb.get('consensus')}"]
                                   if vb.get("consensus") else [])})
            ids += ["voices:table"] + (["voices:consensus"] if vb.get("consensus")
                                       else [])
            items.append(item("narr:voices", f"{len(vb['table']['rows'])} voice(s) "
                              f"this month.", 1, vb["table"]["rows"]))
            items[-1]["show"] = False
        if (vb.get("rollup") or {}).get("rows"):
            subs.append({"title": "The four weeks, by story (sourced items for "
                                  "and against)", "table": vb["rollup"]})
            ids.append("voices:rollup")
        if vb.get("unreachable"):
            nt.append(str(vb["unreachable"]).rstrip("."))
    else:
        nt.append(f"the voices: {vb.get('reason') or 'not read'}")
    return {"items": items or [item("narr:none", "No theme or voice this month.",
                                    1, "none")],
            "print_items": False, "subsections": subs, "not_tracked": nt,
            "phase_a": ids, "_printed": printed,
            "data": {"themes": [t.get("name") for t in lb.get("themes") or []],
                     "voices": (vb.get("table") or {}).get("rows"),
                     "consensus": vb.get("consensus")}}


# ---------------------------------------------------------------------------
# 9. Ahead: the look-ahead, the scenario weights, the month's graded calls
# ---------------------------------------------------------------------------
def ahead_section(p: dict, now: str, db_path: Optional[str]) -> dict:
    la = p.get("looking_ahead") or {}
    items, subs, ids = [], [], ["looking_ahead:prose"]
    for w in la.get("windows") or []:
        rows = [[c["date"], c["title"]] for c in w.get("calendar") or []]
        subs.append({"title": w["name"], "table": {"columns": ["Date", "Event"],
                                                   "rows": rows},
                     "lines": [] if rows else
                     ["Nothing on our calendar for this period yet."]})
        ids.append(f"looking_ahead:window:{w['name']}")
        for c in w.get("calendar") or []:
            items.append(item(f"ahead:{c['date']}:{c['title']}",
                              f"{c['date']}: {c['title']}.", 2, c["title"]))
    scen = la.get("scenarios") or []
    srows = []
    for n, s in enumerate(scen):
        mind = "; ".join(f"{sp['observable']} ({sp['date']})"
                         for sp in s.get("signposts") or [])
        srows.append([s.get("claim"), _v(s.get("probability"), 3),
                      _v(s.get("brier"), 4) if s.get("brier") is not None
                      else "pending", s.get("resolve_by") or "—", mind or "—"])
        ids.append(f"looking_ahead:scenario:{n}")
        items.append(item(f"ahead:scen:{n}", f"{s.get('claim')}: "
                          f"{_v(s.get('probability'), 3)}.", 1,
                          (s.get("claim"), s.get("probability"), s.get("brier"))))
    subs.append({"title": "Scenarios, and what would change our mind",
                 "table": {"columns": ["Scenario", "p", "Brier", "Resolves",
                                       "What would change our mind"], "rows": srows},
                 "lines": [] if srows else ["No live scenario weight this month."]})
    # THE MONTH'S GRADED CALLS (brief 1.3 rule 3: "the Monthly the month's").
    try:
        from daily_cascade import weekly_stack as ws             # noqa: PLC0415
        calls = ws.graded_calls(now, db_path)
        crows = [[ws.source_label(r["source"]), r["n"], f"{r['mean_brier']:.3f}",
                  f"{r['vs_coin']:+.3f}"] for r in calls["rows"]]
        subs.append({"title": "Graded calls, the month",
                     "table": {"columns": ["Source", "Resolved", "Mean Brier",
                                           "Against a coin"], "rows": crows},
                     "lines": [] if crows else ["No call resolved this month."]})
        items.append(item("ahead:calls", "Graded calls: " + ("; ".join(
            f"{r[0]} n={r[1]}, Brier {r[2]}" for r in crows) or "none") + ".", 1,
            crows))
    except Exception as exc:                                    # noqa: BLE001
        calls = None
        subs.append({"title": "Graded calls, the month",
                     "notes": [f"FAULT (code, not data) -- {type(exc).__name__}"]})
    for it in items:
        it["show"] = False
    return {"items": items, "print_items": False, "subsections": subs,
            "not_tracked": list(la.get("not_yet_tracked") or []),
            "phase_a": ids,
            "data": {"scenarios": [{"claim": s.get("claim"),
                                    "probability": s.get("probability"),
                                    "brier": s.get("brier")} for s in scen],
                     "graded_calls": calls}}


# ---------------------------------------------------------------------------
# 10. The book: where our read lands, bounded as now
# ---------------------------------------------------------------------------
def book_section(p: dict) -> dict:
    r = p.get("our_read") or {}
    rm = p.get("register_month") or {}
    rb = rm.get("rule_breaks") or {}
    rows = [["Open decisions now", _cell(rm.get("open_now"))],
            ["Opened this month", len(rm.get("decisions_opened") or [])],
            ["Closed this month", len(rm.get("decisions_closed") or [])],
            ["Restricted-instrument attempts this month",
             _cell(rb.get("restricted_instrument_attempts_this_month"))]]
    items = [item("book:counts", "; ".join(f"{a}: {b}" for a, b in rows) + ".", 1,
                  rows)]
    items[0]["show"] = False
    lines, ids = [], ["our_read:prose"]
    if r.get("state") == "ok" and r.get("paragraph"):
        lines.append(f"The bound, restated from the weights and the positions: "
                     f"{r['paragraph']}")
        ids.append("our_read:bound")
        items.append(item("book:bound", str(r["paragraph"]), 1, r["paragraph"]))
        items[-1]["show"] = False
    return {"items": items, "print_items": False,
            "table": {"columns": ["The register", "This month"], "rows": rows},
            "subsections": [{"title": "Where our read lands", "lines": lines}],
            "not_tracked": ([] if r.get("state") == "ok" else
                            [f"where our read lands: {r.get('reason')}"]),
            "phase_a": ids,
            "data": {"register": rows, "live_weights": r.get("live_weights"),
                     "active_decisions": r.get("active_decisions")}}


# ---------------------------------------------------------------------------
# Slow layers (the matrix's last row) and the detail tables
# ---------------------------------------------------------------------------
def sourced_figures(now: Optional[str], db_path: Optional[str]) -> tuple[list, list, list]:
    """The scans' reference tables, as stored (altdata/scans.py): one sub-section
    per scan family, the newest edition readable at the cutoff. A figure prints
    only from the store -- no stored source, not printed -- and with its source
    beside it: the URL, the scan's own section (and slide, when the scan recorded
    one), the as-of date. Only reference-table rows were ever stored, so none of
    the publisher's recommendations can reach this table."""
    from altdata import scans                                    # noqa: PLC0415
    rows = scans.latest(now, db_path)
    subs, items, data = [], [], []
    by_fam: dict[str, list] = {}
    for r in rows:
        by_fam.setdefault(r["family"], []).append(r)
    for fam, rs in by_fam.items():
        r0 = rs[0]
        subs.append({
            "title": f"Sourced figures: {r0.get('edition') or r0['title']}",
            "table": {"columns": ["Metric", "Figure", "Long-run comparison",
                                  "Source"],
                      "rows": [[r["metric"], r["value"], r.get("comparison") or "—",
                                r["source_ref"]] for r in rs]},
            "notes": [f"Source: {r0['source_url']}, from the scan's "
                      f"{r0['section_ref']} reference table, data as of "
                      f"{r0['as_of']}, read {r0['read_on']}. Figures as "
                      f"published; the publisher's recommendations are not "
                      f"printed."]})
        for r in rs:
            items.append(item(f"slow:scan:{fam}:{r['metric']}",
                              f"{r['metric']} {r['value']}", 3,
                              (r["value"], r.get("comparison"), r["as_of"])))
            data.append({"family": fam, "metric": r["metric"], "figure": r["value"],
                         "comparison": r.get("comparison"),
                         "source": r["source_ref"], "url": r["source_url"],
                         "as_of": r["as_of"]})
    return subs, items, data


TRIPLE_COLUMNS = ["Latest (data as of)", "Long-run average (window)",
                  "Percentile (window)"]


def triple(st, key: str, now: str, window_days: int = 1825,
           instrument: Optional[str] = None) -> Optional[dict]:
    """Latest / long-run average / percentile for one stored series, each with
    its window (altdata.derived computes all three). None when the store holds
    nothing knowable at the cutoff."""
    from altdata import derived                                  # noqa: PLC0415
    f = derived.derived_forms(key, now, window=window_days, store=st,
                              instrument=instrument)
    if f.get("level") is None:
        return None
    lr = derived.long_run_average(key, now, store=st, instrument=instrument)
    full = (f.get("window_actual_days") or 0) >= window_days - 31
    yrs = window_days // 365
    pct_win = (f"{yrs} years, n={f['n']:,}" if full else
               f"since {f['first_observed']}, n={f['n']:,}; under {yrs} years")
    return {"key": key, "instrument": instrument, "latest": f["level"],
            "as_of": f["observed_at"], "mean": lr.get("mean"), "mean_n": lr.get("n"),
            "mean_since": lr.get("first_observed"), "percentile": f.get("percentile"),
            "percentile_window": pct_win, "percentile_n": f["n"],
            "percentile_since": f.get("first_observed"),
            "delta_20d": f.get("delta_20d"), "delta_unit": f.get("delta_unit")}


def triple_cells(t: dict, dp: int = 2) -> list[str]:
    return [f"{_v(t['latest'], dp)} ({t['as_of']})",
            (f"{_v(t['mean'], dp)} (full history since {t['mean_since']}, "
             f"n={t['mean_n']:,})" if t.get("mean") is not None else "—"),
            (f"{_v(t['percentile'], 0)} ({t['percentile_window']})"
             if t.get("percentile") is not None else "—")]


def slow_layers(p: dict, cfg: dict, st=None, now: Optional[str] = None,
                db_path: Optional[str] = None) -> dict:
    tb = p.get("top_bottom") or {}
    br = tb.get("bear_rally_base_rate") or {}
    base_rows = []
    if tb.get("state") == "ok":
        base_rows.append(["Top & Bottom verdict", tb.get("verdict") or "—",
                          _v(tb.get("composite")), tb.get("as_of") or "—"])
    if not br.get("absent_reason") and br:
        base_rows.append([f"Largest counter-trend rally inside a bear market "
                          f"(n={_v(br.get('n_bears'), 0)} bears)",
                          f"median {_v(br.get('median'))}%",
                          f"p25 {_v(br.get('p25'))}% to p75 {_v(br.get('p75'))}%",
                          f"extreme {_v(br.get('max'))}%"])
    base_nt = []
    if tb.get("state") != "ok":
        base_nt.append(f"the Top & Bottom verdict: {tb.get('reason')}")
    if br.get("absent_reason"):
        base_nt.append(f"the bear-rally base rate: {br['absent_reason']}")
    tcfg = cfg.get("monthly_slow_triple") or {}
    win = int(tcfg.get("percentile_window_days") or 1825)
    vrows, vdata, val_nt = [], [], list(tcfg.get("not_tracked") or [])
    for v in tcfg.get("valuation") or []:
        t = triple(st, v["key"], now, win, v.get("instrument")) if st and now else None
        if t is None:
            val_nt.append(f"{v['label']}: no observation knowable at this cutoff")
            continue
        vrows.append([v["label"], *triple_cells(t, 1)])
        vdata.append({"series": v["label"], **{k: t[k] for k in (
            "latest", "as_of", "mean", "mean_since", "mean_n", "percentile",
            "percentile_window")}})
    alt = p.get("alternative_assets") or {}
    arows, alt_nt, adata = [], [], []
    for fam, v in sorted((alt.get("families") or {}).items()):
        if v.get("state") == "not_yet_sourced":
            alt_nt.append(f"{fam}: needs {', '.join(v.get('needs') or [])}")
            continue
        for m in v.get("metrics") or []:
            t = triple(st, m["metric"], now, win) if st and now else None
            if m.get("level") is None or t is None:
                alt_nt.append(f"{fam}: {m['metric']}")
                continue
            cells = triple_cells(t)
            arows.append([fam, m["metric"], cells[0],
                          (f"{m['delta_20d']:+.2f} {m.get('delta_unit') or ''}".strip()
                           if isinstance(m.get("delta_20d"), (int, float)) else "—"),
                          cells[1], cells[2]])
            adata.append({"family": fam, "series": m["metric"], **{k: t[k] for k in (
                "latest", "as_of", "mean", "mean_since", "mean_n", "percentile",
                "percentile_window")}})
    subs = [{"title": "Valuation",
             "table": {"columns": ["Series", *TRIPLE_COLUMNS], "rows": vrows},
             "notes": ([f"Long-run average over the store's full history and "
                        f"percentile over {win // 365} years where the store holds "
                        f"them, until the metric lenses (6e) set each series' long "
                        f"window."] if vrows else []),
             "not_tracked": val_nt},
            {"title": "Base rates: Top & Bottom",
             "table": {"columns": ["Base rate", "Level", "Range", "As of or extreme"],
                       "rows": base_rows}, "not_tracked": base_nt},
            {"title": "Tails",
             "not_tracked": ["the 25 tail scenarios (not yet stored)"]},
            {"title": "Themes: alternative assets",
             "table": {"columns": ["Family", "Series", TRIPLE_COLUMNS[0],
                                   "20-day change", *TRIPLE_COLUMNS[1:]],
                       "rows": arows},
             "not_tracked": alt_nt + ["Disruptive Themes (quarterly; folded into "
                                      "the Quarterly Structural)"]}]
    try:
        src_subs, src_items, src_data = sourced_figures(now, db_path)
    except Exception as exc:                                    # noqa: BLE001
        log.warning("sourced figures unavailable", exc_info=True)
        src_subs, src_items, src_data = [], [], []
        subs[-1]["not_tracked"].append(f"the scans' sourced figures: FAULT {exc}")
    if not src_subs:
        subs[-1]["not_tracked"].append(
            "the scans' sourced figures: no scan ingested by this edition's cutoff")
    subs += src_subs
    items = [item(f"slow:base:{n}", " ".join(str(x) for x in r), 1, r)
             for n, r in enumerate(base_rows)]
    items += [item(f"slow:alt:{r[1]}", f"{r[1]} {r[2]}", 2, r) for r in arows]
    items += [item(f"slow:val:{r[0]}", f"{r[0]} {r[1]}", 1, r) for r in vrows]
    items += src_items
    for it in items:
        it["show"] = False
    return {"items": items, "print_items": False, "subsections": subs,
            "phase_a": (["top_bottom"] if base_rows else [])
            + [f"alternative_assets:{r[1]}" for r in arows],
            "data": {"valuation": vdata, "base_rates": base_rows,
                     "alternative_assets": adata, "sourced_figures": src_data}}


def detail_tables(p: dict, ahead_claims: set) -> list[dict]:
    """The old record after the stack: the regime, the scenario record, the
    register's month, the appendix -- each fact once."""
    out = []
    rg = p.get("regime") or {}
    if rg.get("state") == "ok":
        drows = [[d["dial"], d.get("state") or "absent",
                  d.get("previous_state") or "—",
                  "changed" if d.get("changed") else "held"]
                 for d in rg.get("dials") or []]
        dims = [[d["dimension"], d.get("state") or "absent",
                 d.get("previous_state") or "—", _v(d.get("percentile"), 1),
                 d.get("direction") or "—", d.get("confidence") or "—"]
                for d in rg.get("dimensions") or []]
        closed = [c for c in rg.get("contradictions") or []
                  if c.get("open_state") not in ("open", "absent", None)]
        out.append({"id": "regime", "title": "The regime, read from the close",
                    "tables": [{"columns": ["Read", "State", "Previous Monthly",
                                            "Since"], "rows": drows},
                               {"columns": ["Dimension", "State", "Previous Monthly",
                                            "Percentile", "Direction", "Confidence"],
                                "rows": dims},
                               {"columns": ["Pair not open", "State", "z", "Since"],
                                "rows": [[c.get("id"), c.get("open_state"),
                                          _v(c.get("magnitude")), c.get("since") or "—"]
                                         for c in closed]}],
                    "lines": ([f"Exceptions closed this month: "
                               f"{', '.join(rg['exceptions_closed'])}."]
                              if rg.get("exceptions_closed") else []),
                    "notes": [f"Object session {rg.get('session')}, config "
                              f"{rg.get('config_version')}, method "
                              f"{rg.get('method_version')}; against "
                              f"{rg.get('previous_monthly') or 'no previous Monthly'}."],
                    "not_tracked": [f"{d['dimension']}: "
                                    f"{d.get('absent_reason') or 'no reason recorded'}"
                                    for d in rg.get("dimensions") or []
                                    if not d.get("state")],
                    "phase_a": ["regime:dials", "regime:dimensions"]})
    sc = p.get("scenarios") or {}
    rec = [w for w in sc.get("weights") or [] if w.get("claim") not in ahead_claims]
    out.append({"id": "scenarios", "title": "The scenario record",
                "tables": [{"columns": ["Claim", "p", "Outcome", "Brier",
                                        "Resolve by"],
                            "rows": [[w.get("claim"), _v(w.get("probability"), 3),
                                      "—" if w.get("outcome") is None else w["outcome"],
                                      _v(w.get("brier"), 4), w.get("resolve_by") or "—"]
                                     for w in rec]}],
                "lines": ([] if rec else
                          ["No weight beyond the live ones Ahead prints."
                           if sc.get("state") == "ok" else
                           f"No probability has been emitted. "
                           f"{sc.get('reason') or ''}".strip()]),
                "phase_a": [f"scenarios:{w.get('claim')}" for w in rec]})
    rm = p.get("register_month") or {}
    ov = ((rm.get("cuts") or {}).get("overall") or {})
    lines = []
    if rm.get("state") == "ok":
        lines.append(f"{rm.get('graded_total')} graded to date, "
                     f"{rm.get('graded_this_month')} this month. Expectancy, interval "
                     f"first: n={ov.get('n')}, {_v(ov.get('lo'), 3)} to "
                     f"{_v(ov.get('hi'), 3)}R, mean {_v(ov.get('mean'), 3)}R.")
    else:
        lines.append(f"Grades: {rm.get('reason') or 'unavailable'}")
    dec = [[d.get("instrument"), d.get("direction"), d.get("status"),
            d.get("expression_family") or "—", str(d.get("created_at"))[:10]]
           for d in rm.get("decisions_opened") or []]
    bz = rm.get("books_vs_benchmark") or {}
    out.append({"id": "register", "title": "The register's month",
                "tables": [{"columns": ["Opened", "Direction", "Status", "Expression",
                                        "On"], "rows": dec},
                           {"columns": ["Book", "Paper equity"],
                            "rows": [[f"Book {k}", v] for k, v in
                                     sorted((bz.get("books") or {}).items())]}],
                "lines": lines,
                "not_tracked": list((rm.get("rule_breaks") or {}).get("not_yet_sourced")
                                    or []),
                "phase_a": ["register_month"]})
    ap = p.get("appendix") or {}
    ptabs, pnames = [], []
    for num, v in sorted((ap.get("pillars") or {}).items(), key=lambda kv: int(kv[0])):
        pnames.append((num, v.get("name")))
        ptabs.append({"title": f"Pillar {num}: {v.get('name')}",
                      "phase": f"pillar:{num}",
                      "table": {"columns": ["Series", "Level", "20-day change",
                                            "Percentile", "Confidence"],
                                "rows": [[r["metric"], _v(r.get("level")),
                                          (f"{r['delta_20d']:+.2f} "
                                           f"{r.get('delta_unit') or ''}".strip()
                                           if isinstance(r.get("delta_20d"),
                                                         (int, float)) else "—"),
                                          _v(r.get("percentile"), 1),
                                          r.get("confidence") or "—"]
                                         for r in v.get("series") or []]}})
    macro = ap.get("derived_macro") or []
    gate = ap.get("pm_calibration_gate") or {}
    out.append({"id": "appendix", "title": "Appendix: the pillars, as one delta table",
                "tables": ([{"columns": ["Derived series", "Level", "20-day change",
                                         "Percentile", "Read by"],
                             "rows": [[m["metric"], _v(m.get("level")),
                                       (f"{m['delta_20d']:+.2f}"
                                        if isinstance(m.get("delta_20d"), (int, float))
                                        else "—"), _v(m.get("percentile"), 1),
                                       ", ".join(m.get("read_by") or []) or "—"]
                                      for m in macro]}] if macro else [])
                + ([{"columns": ["Prediction-market gate", "Have", "Need", "Met"],
                     "rows": [[c["condition"], c["have"], c["need"],
                               "yes" if c.get("met") else "no"]
                              for c in gate.get("conditions") or []]}]
                   if gate.get("state") == "ok" else []),
                "subsections": ptabs,
                "not_tracked": [f"pillar {g['pillar']} ({g.get('name')}): "
                                f"{g.get('reason')}"
                                for g in ap.get("pillars_without_series") or []]
                + ([] if ap.get("state") == "ok" else
                   [f"the appendix: {ap.get('reason')}"]),
                "phase_a": [f"appendix:pillar:{n}" for n, _ in pnames]})
    return out


# ---------------------------------------------------------------------------
# Changed since last Monthly: Phase A's "what changed", in the header
# ---------------------------------------------------------------------------
def changed_since(p: dict) -> tuple[list[str], list[str]]:
    wc = (p.get("looking_back") or {}).get("what_changed") or {}
    lines, ids = [], []
    for n, r in enumerate(wc.get("rows") or []):
        lines.append(f"{r.get('what')}: {r.get('from') or '—'} to {r.get('to') or '—'}"
                     f" ({_cite(r.get('source'))}).")
        ids.append(f"looking_back:what_changed:{n}")
    return lines, ids


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------
def build(p: dict, prior: Optional[dict] = None, db_path: Optional[str] = None,
          book: Optional[dict] = None) -> dict:
    """The edition's data, at Monthly depth, before any prose."""
    cfg = stack_mod.config()
    first, last, then, now = window(p)
    built: dict[str, dict] = {}
    retro = None
    # THE SCORECARD'S MARKETS PRINT IN THE TAPE, once: the themes and Plumbing
    # leave them out of their tables (each fact once, T2.5 item 1).
    on_tape = {r.get("metric") for r in (p.get("month_in_markets") or {})
               .get("rows") or [] if r.get("metric")}
    with observations.ObservationStore(db_path) as st:
        try:
            pmb, fed, _ = stack_mod.venues_and_path(last, now, st)
        except Exception:                                       # noqa: BLE001
            pmb, fed = None, None
        try:
            from altdata import fed_funds                       # noqa: PLC0415
            fed_then = fed_funds.path_as_of(then, st)
        except Exception:                                       # noqa: BLE001
            fed_then = None
        steps = {
            "read": lambda: read_section(p),
            "tape": lambda: tape_section(p, book, st, last, now, cfg),
            "mechanics": lambda: mechanics_section(st, first, last, now, cfg),
            "misfit": lambda: misfit_section(p, st, now, pmb),
            "plumbing": lambda: plumbing_section(st, now, then, on_tape),
            "positioning": lambda: positioning_section(st, now, then),
            "priced": lambda: priced_section(st, now, then, cfg, pmb, fed, fed_then),
            "narratives": lambda: narratives_section(
                p, on_tape, set(built.get("plumbing", {}).get("_printed") or [])),
            "ahead": lambda: ahead_section(p, now, db_path),
            "book": lambda: book_section(p),
        }
        for sid, fn in steps.items():
            try:
                built[sid] = fn()
            except Exception as exc:                            # noqa: BLE001
                built[sid] = _fault(sid, exc)
        retro = built["mechanics"].pop("_retro", None)
        printed = [(k, "tape") for k in sorted(on_tape)]
        for sid in ("plumbing", "narratives"):
            printed += [(k, sid) for k in built[sid].pop("_printed", None) or []]
        slow = slow_layers(p, cfg, st, now, db_path)
    sections = stack_mod.assemble(built, cfg, prior, CADENCE)
    specs = {s["id"]: s for s in cfg.get("sections") or []}
    for s in sections:
        b = built[s["id"]]
        s["period"] = "month"
        s["subtitle"] = specs[s["id"]].get("monthly_subtitle") or s.get("subtitle")
        s["depth_note"] = specs[s["id"]].get("monthly_note")
        s["phase_a"] = list(b.get("phase_a") or [])
        s["notes"] = list(b.get("notes") or [])
        s["prose_wanted"] = b.get("prose_wanted", True)
    sl = cfg.get("monthly_slow_layers") or {"id": SLOW_ID, "title": "Slow layers",
                                            "monthly": "deep"}
    pr = {x["id"]: x for x in (prior or {}).get("sections") or []}.get(SLOW_ID) or {}
    pmarks = {i["key"]: i["fingerprint"] for i in pr.get("items") or []}
    for it in slow["items"]:
        it["changed"] = bool(prior) and pmarks.get(it["key"]) != it["fingerprint"]
    fp = stack_mod._fp([(i["key"], i["fingerprint"]) for i in slow["items"]])
    collapsed = bool(prior) and pr.get("fingerprint") == fp
    sections.append({"id": SLOW_ID, "title": sl["title"], "subtitle": sl.get("subtitle"),
                     "depth": sl.get("monthly") or "deep", "depth_reason": None,
                     "items": slow["items"], "table": None, "charts": [],
                     "data": slow["data"], "not_tracked": [], "legend": None,
                     "print_items": False, "subsections": slow["subsections"],
                     "fingerprint": fp, "collapsed": collapsed,
                     "unchanged_since": ((pr.get("unchanged_since") or
                                          (prior or {}).get("report_date"))
                                         if collapsed else None),
                     "prior_claim": pr.get("claim") if collapsed else None,
                     "claim": None, "paragraphs": [], "trimmed": False,
                     "period": "month", "phase_a": slow["phase_a"], "notes": [],
                     "prose_wanted": True})
    rd.mark_empty(sections, "month")
    mech = next(s for s in sections if s["id"] == "mechanics")
    if retro and retro.get("insufficient") and not mech.get("empty"):
        # BELOW THE THRESHOLD THE SECTION'S CLAIM IS THE COUNT, written by code,
        # and no paragraph is asked for (brief 1.2; T3 item 3).
        mech["claim"] = (f"Insufficient sessions (n={len(retro['sessions'])}) for "
                         f"the month's dealer retrospective.")
    claims = {s.get("claim") for s in (p.get("looking_ahead") or {}).get("scenarios")
              or []}
    changed, changed_ids = changed_since(p)
    targets = cfg.get("reading_targets_minutes") or {}
    ed = {"report": "monthly_stack", "report_date": p.get("report_date"),
          "session": last, "month": (p.get("month_in_markets") or {}).get("month"),
          "window": {"first": first, "last": last, "then": then, "now": now},
          "config_version": cfg.get("version"), "as_of": now,
          "prior_session": (prior or {}).get("report_date"),
          "sections": sections, "detail": detail_tables(p, claims),
          "changed_since": changed, "changed_since_phase_a": changed_ids,
          "budget": (cfg.get("budget") or {}).get(CADENCE),
          "reading_target_minutes": targets.get(CADENCE),
          "chart_count": 0, "charts": {}, "run_id": p.get("run_id"),
          # Which section's table prints each series' month: the gate holds
          # every series to one.
          "printed_metrics": printed}
    ed["_retro"] = retro
    return ed


# ---------------------------------------------------------------------------
# The prose onto the edition
# ---------------------------------------------------------------------------
def _sentences(text: str) -> list[str]:
    return [x for x in re.split(r"(?<=[.!?])\s+", (text or "").strip()) if x]


def _paras(text: Optional[str]) -> list[str]:
    return [re.sub(r"\s+", " ", x).strip() for x in (text or "").split("\n\n")
            if x.strip()]


def _claim_and_rest(text: str) -> tuple[Optional[str], list[str]]:
    """The first sentence is the claim; the rest of its paragraph and every
    paragraph after it follow -- the claim is never printed twice."""
    paras = _paras(text)
    if not paras:
        return None, []
    sents = _sentences(paras[0])
    claim = sents[0] if sents else paras[0]
    rest = " ".join(sents[1:]).strip()
    return claim, ([rest] if rest else []) + paras[1:]


# Where each Phase A prose call lands: (section, sub-section phase or None).
PHASE_A_PROSE = {"month_in_markets": ("read", None),
                 "month_in_one_page": ("read", "month_in_one_page"),
                 "looking_ahead": ("ahead", None),
                 "our_read": ("book", None)}


def apply_prose(ed: dict, written: dict) -> dict:
    """Every published text onto its section; every withheld one's reason into
    its footnote. Phase A prose keeps its paragraphs (it is long form); a stack
    section's call gives the claim and its one paragraph."""
    secs = {s["id"]: s for s in ed["sections"]}
    subs = {}
    for s in ed["sections"]:
        for ss in s.get("subsections") or []:
            if ss.get("phase"):
                subs[ss["phase"]] = (s, ss)
    for d in ed.get("detail") or []:
        for ss in d.get("subsections") or []:
            if ss.get("phase"):
                subs[ss["phase"]] = (d, ss)
    for key, r in written.items():
        ok = bool(r.get("published") and r.get("text"))
        why = r.get("reason") or r.get("state")
        if key.startswith("stack:"):
            s = secs.get(key.split(":", 1)[1])
            if s is None:
                continue
            if ok:
                s["claim"], s["paragraphs"] = _claim_and_rest(r["text"])
                s["paragraphs"] = s["paragraphs"][:1] if s.get("depth") in (
                    "deep", "medium") else []
            else:
                s["withheld"] = why
            continue
        sid, phase = PHASE_A_PROSE.get(key, (None, None))
        if sid is None and key in subs:
            owner, ss = subs[key]
            if ok:
                ss["paragraphs"] = _paras(r["text"])
            else:
                ss.setdefault("notes", []).append(
                    f"Commentary withheld by the audit: {why}")
            continue
        s = secs.get(sid)
        if s is None:
            continue
        if phase:
            ss = next((x for x in s.get("subsections") or []
                       if x.get("phase") == phase), None)
            if ss is None:
                continue
            if ok:
                ss["paragraphs"] = _paras(r["text"])
                # The takeaways now print as their prose: the lines are its data.
                ss["lines"] = []
            else:
                ss.setdefault("notes", []).append(
                    f"Commentary withheld by the audit: {why}")
            continue
        if ok:
            s["claim"], s["paragraphs"] = _claim_and_rest(r["text"])
        else:
            s["withheld"] = why
    ed["prose"] = {k: {kk: v.get(kk) for kk in ("state", "published", "reason",
                                                 "attempts", "first_reason", "words")}
                   for k, v in written.items()}
    return ed


# ---------------------------------------------------------------------------
# The budget: prose only
# ---------------------------------------------------------------------------
def _w(text: Optional[str]) -> int:
    return stack_mod.words(text)


def section_words(s: dict) -> int:
    """PROSE ONLY (ruled 4 Oct 2026, every report): the claim, the paragraphs and
    every sub-section's paragraphs. Items, lines and tables are data."""
    if s.get("empty"):
        return 0
    n = _w(s.get("claim")) + sum(_w(x) for x in s.get("paragraphs") or [])
    for ss in s.get("subsections") or []:
        n += sum(_w(x) for x in ss.get("paragraphs") or [])
    return n


def edition_words(ed: dict) -> int:
    return (sum(section_words(s) for s in ed.get("sections") or [])
            + sum(section_words(d) for d in ed.get("detail") or []))


def reading_minutes(ed: dict) -> int:
    """The Weekly's estimate (readability.reading_minutes): prose words at 250 a
    minute plus 20 seconds a chart, rounded up -- over the Monthly's prose, which
    includes its sub-sections' paragraphs."""
    charts = int(ed.get("chart_count") or 0)
    return max(1, math.ceil(edition_words(ed) / rd.WORDS_PER_MINUTE
                            + charts * rd.SECONDS_PER_CHART / 60.0))


def enforce_budget(ed: dict) -> dict:
    """Over 7,000 prose words, the lowest-priority paragraphs go first -- the
    appendix pillars' paragraphs, then the last paragraph of each long block from
    the back of the edition forward -- and the section prints "(trimmed)". A
    claim, an item, a line and a table are never cut; the model never
    summarises to fit. Then The read's sentences are not repeated elsewhere."""
    rd.withhold_duplicates(ed)
    budget = int((ed.get("budget") or {}).get("words") or 7000)
    order: list[tuple[dict, dict]] = []
    for d in ed.get("detail") or []:
        for ss in d.get("subsections") or []:
            order.append((d, ss))
    blocks = []
    for s in reversed(ed["sections"]):
        for ss in reversed(s.get("subsections") or []):
            blocks.append((s, ss))
        blocks.append((s, s))
    while edition_words(ed) > budget:
        cut = False
        for owner, blk in order:
            if blk.get("paragraphs"):
                blk["paragraphs"] = []
                blk["trimmed"] = owner["trimmed"] = True
                cut = True
                break
        if not cut:
            for owner, blk in blocks:
                if len(blk.get("paragraphs") or []) > 1:
                    blk["paragraphs"] = blk["paragraphs"][:-1]
                    blk["trimmed"] = owner["trimmed"] = True
                    cut = True
                    break
        if not cut:
            for owner, blk in blocks:
                if blk.get("paragraphs"):
                    blk["paragraphs"] = blk["paragraphs"][:-1]
                    blk["trimmed"] = owner["trimmed"] = True
                    cut = True
                    break
        if not cut:
            break
    ed["words"] = edition_words(ed)
    ed["reading_minutes"] = reading_minutes(ed)
    return ed


# ---------------------------------------------------------------------------
# The book of levels for the tape's long frame
# ---------------------------------------------------------------------------
def level_book(p: dict, db_path: Optional[str] = None) -> Optional[dict]:
    """The level list at the month-end session, for the long frame. None when the
    bars store cannot be read -- the tape then says so."""
    try:
        from altdata import bars as bars_mod, levels as levels_mod  # noqa: PLC0415
        _, last, _, now = window(p)
        with bars_mod.BarStore(db_path) as bst:
            return levels_mod.compute(last, [], store=bst, as_of=now)
    except Exception:                                           # noqa: BLE001
        log.warning("level list unavailable", exc_info=True)
        return None


def public(ed: dict) -> dict:
    """The edition as archived: private keys dropped."""
    out = copy.copy(ed)
    out.pop("_retro", None)
    return out


def polish(ed: dict) -> dict:
    """The stacked reports' formatting pass (readability.polish_edition, T2.5
    item 6), and the same over what only the Monthly carries: a sub-section's
    paragraphs and extra tables, and the detail tables."""
    rd.polish_edition(ed)
    try:
        year = dt.date.fromisoformat(str(ed.get("session"))[:10]).year
    except ValueError:
        year = None

    def blk(b: dict) -> None:
        b["paragraphs"] = [rd.polish(x, year) for x in b.get("paragraphs") or []]
        b["lines"] = [rd.polish(x, year) for x in b.get("lines") or []]
        b["notes"] = [rd.polish(x, year) for x in b.get("notes") or []]
        b["not_tracked"] = [rd.polish(x, year) for x in b.get("not_tracked") or []]
        rd._polish_table(b.get("table"))
        for t in b.get("tables") or []:
            rd._polish_table(t)
        b.pop("paragraph", None)
    for s in ed.get("sections") or []:
        for ss in s.get("subsections") or []:
            blk(ss)
    for d in ed.get("detail") or []:
        blk(d)
        for ss in d.get("subsections") or []:
            blk(ss)
    return ed


def produce(p: dict, *, archive_dir: Optional[str], client=None,
            model: Optional[str] = None, narrative: bool = True,
            db_path: Optional[str] = None, write=None) -> dict:
    """Build, write, budget, polish and render the stacked Monthly. Archives
    nothing -- run.py does, through deliver.archive, as for every report.
    `write(ed) -> {key: result}` replaces the default prose step (run.py passes
    its own, which logs and records the prose on the payload)."""
    from . import prose as prose_mod                             # noqa: PLC0415
    from .writer import render_stack                             # noqa: PLC0415
    prior = load_prior(str(p.get("report_date")), archive_dir)
    ed = build(p, prior, db_path, book=level_book(p, db_path))
    if not narrative:
        written = {}
    elif write is not None:
        written = write(ed)
    else:
        written = prose_mod.write_all(p, model=model, client=client, ed=ed)
    apply_prose(ed, written)
    enforce_budget(ed)
    polish(ed)
    stamp = p.get("report_date")
    ed["archive_path"] = (str(Path(archive_dir) / f"monthly_macro_{stamp}.html")
                          if archive_dir else None)
    return {"edition": public(ed), "written": written,
            "html_email": render_stack.html(ed, mode="email"),
            "html_archive": render_stack.html(ed, mode="archive"),
            "markdown": render_stack.markdown(ed)}
