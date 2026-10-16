"""
The standing three-timeframe ES block: the read and the print. (ST-R6.45d;
Batch 6 item 45, ruled 15 Oct 2026; docs/briefs/st-r6-45-notes.md)

    from daily_cascade import es_read
    read = es_read.write(block, slot="morning")      # the read and its lean
    html = es_read.html(block, read)                 # the 07:00 anchor's section
    sub = es_read.subsection(block, read)            # the close's, in Mechanics
    sub = es_read.weekly_subsection(bst, sessions, cutoff)   # the Weekly's panel

PHONE-READABLE, READ FIRST. The read -- one paragraph tying the three
timeframes together and naming the levels that matter above and below -- then a
compact levels table (price now in the middle), then the windows table, then the
contract, any roll and the dealer row. No chart: the block adds none, so the
close's chart budget is unchanged.

THE READ IS WRITTEN BY THE EXISTING NARRATIVE STEP. narrative.generate(), the one
funnel every report's prose passes through -- print precision, the numeral audit,
markdown refused -- plus the stack's style rules and this block's forecast rule,
with one retry on an audit refusal, as every stacked section has. No new model,
client or prompt path: the anchor calls it inside its narrative scan and the close
inside its prose step, each under the model meter's scope. A withheld read prints
its reason; the tables print regardless.

THE LEAN IS STRUCTURED. The reply ends with one line, `LEAN: up`, `LEAN: down`
or `LEAN: none`; the split hook takes it off BEFORE the audit (it is not prose)
and the ledger records it from there -- the ledger never parses prose. A reply
without the line is withheld and retried like any audit refusal.

REPORT ONLY. Nothing here generates a setup, and the read never says a level
will hold or break: that is what the ledger measures.
"""

from __future__ import annotations

import html as _html
import re
from typing import Any, Optional

from altdata import es_block

TITLE = "ES — three timeframes"
LEAN_RE = re.compile(r"^\s*LEAN:\s*(up|down|none)\s*\.?\s*$", re.I | re.M)
MAX_CHARS = 1500
# A read that forecasts a level is the ledger's question answered in advance.
FORECAST = re.compile(r"\b(will|should|is likely to|is set to|is poised to|expect(?:s|ed)? to)"
                      r"\s+(?:\w+\s+){0,3}(hold|break|fail|bounce|reject|rally|fall|rise)\b",
                      re.I)

ES_RULES = """

THIS OVERRIDES THE ONE-PARAGRAPH FRAMING ABOVE ONLY IN WHAT FOLLOWS. You are
writing THE READ of the standing three-timeframe ES block ({when}). Write ONE
paragraph of at most 140 words that reads the three windows AGAINST EACH OTHER
-- session (5-minute bars{session_note}), swing (five sessions on 2-hour bars)
and position (three months on daily bars) -- and names the levels that matter
above and below the last price, copied exactly as `levels` prints them, with
their sources' words (POC, value-area high, high-volume node, VWAP, trend line).
Say where the windows agree and where they do not: price against VWAP and the
value areas, the MACD histogram's sign and turn, money flow, the trend lines'
slopes. Every figure from the data, exactly as given.

NEVER FORECAST. Do not say a level will hold, break, reject or attract price,
and do not predict the session: state where price sits against the levels and
what each window shows. Whether levels hold is what the ledger measures.
{dealer}
AFTER THE PARAGRAPH, on its own last line, write exactly one of `LEAN: up`,
`LEAN: down` or `LEAN: none` -- the direction the three windows point TOGETHER
for the next session, or none when they disagree. That line is data, not prose.
"""


def system_prompt(slot: str, base=None) -> str:
    from . import stack_prose                                   # noqa: PLC0415
    if base is None:
        from daily_cascade import narrative as base             # noqa: PLC0415
    when = ("the 07:00 morning anchor: the overnight session so far, the prior "
            "full session's value area and POC as reference, the day's levels"
            if slot == "morning" else
            "the 16:45 close: the full session, what changed since the 07:00 "
            "print (`since_07_00`, its levels' outcomes so far), the levels for "
            "tomorrow")
    return stack_prose.stack_system_prompt(base) + ES_RULES.format(
        when=when, session_note=", the overnight session so far" if slot == "morning"
        else ", the whole futures day",
        dealer=("\nThe dealer levels are not yet converted to ES; do not mention "
                "dealer gamma, walls or the flip in ES terms.\n"))


def split_lean(text: str) -> tuple[str, dict]:
    """(prose, {"lean": up|down|none} or {"lean": None, "error": ...})."""
    found = LEAN_RE.findall(text or "")
    prose = LEAN_RE.sub("", text or "").strip()
    if not found:
        return prose, {"lean": None, "error": "no LEAN line"}
    if len({f.lower() for f in found}) > 1:
        return prose, {"lean": None, "error": f"conflicting LEAN lines {found}"}
    return prose, {"lean": found[-1].lower()}


def payload(block: dict) -> dict:
    """What the read is handed: the windows' numbers, the levels and the
    contract -- never the bins."""
    w = block.get("windows") or {}

    def win(x: dict) -> dict:
        if not x or x.get("absent"):
            return {"absent": (x or {}).get("absent")}
        keep = ("sessions", "n_sessions", "sessions_wanted", "open", "high", "low",
                "last", "change", "vwap", "trend", "macd", "money_flow")
        out = {k: x[k] for k in keep if k in x}
        p = x.get("profile") or {}
        out["profile"] = {k: p[k] for k in ("poc", "vah", "val", "hvn", "lvn", "note",
                                             "absent") if k in p}
        if x.get("rolls"):
            out["rolls"] = x["rolls"]
        return out
    sm = block.get("since_morning")
    extra = ({"since_07_00": {"price_at_07_00": sm["ref_price"],
                              "change_since": sm["change"],
                              "morning_lean": sm["lean"],
                              "morning_lean_so_far": sm["lean_so_far"],
                              "morning_levels": [{"level": x["level"], "sources": x["label"],
                                                  "so_far": x["so_far"]}
                                                 for x in sm["levels"]]}}
             if sm else {})
    return {**extra, "block": "ES three timeframes", "slot": block.get("slot"),
            "session": block.get("session"), "last": block.get("last"),
            "contract": (block.get("contract") or {}).get("in_force"),
            "windows": {k: win(v) for k, v in w.items()},
            "levels": {side: [{"level": lv["price"], "sources": lv["label"],
                               "points_from_last": lv["distance"]}
                              for lv in (block.get("levels") or {}).get(side) or []]
                       for side in ("above", "below")}}


def forecast_faults(text: str) -> list[str]:
    return [f"forecast: '{m.group(0)}'" for m in FORECAST.finditer(text or "")]


def write(block: dict, slot: Optional[str] = None, client=None,
          model: Optional[str] = None, attempts: int = 2) -> dict:
    """The read and its lean, or the reason it was withheld. Never raises."""
    slot = slot or block.get("slot") or "close"
    if block.get("state") == "absent":
        return {"state": "absent", "published": False, "lean": None,
                "reason": block.get("reason") or "the block is absent"}
    from daily_cascade import narrative as base                 # noqa: PLC0415
    from . import stack_prose                                   # noqa: PLC0415
    from altdata import bars as bars_mod                        # noqa: PLC0415
    cfg = bars_mod.load_config()
    system = system_prompt(slot, base)
    pl = payload(block)
    res: dict[str, Any] = {}
    for k in range(1, max(1, attempts) + 1):
        sp = system if k == 1 else stack_prose.retry_prompt(
            system, res.get("retry_reason") or res.get("reason"), k, attempts)
        try:
            r = base.generate(pl, model=model, client=client, system_prompt=sp,
                              max_chars=MAX_CHARS, one_paragraph=True,
                              split=split_lean, guide_path=stack_prose.STACK_GUIDE,
                              unit_constants=stack_prose.UNIT_CONSTANTS)
        except Exception as exc:                                # noqa: BLE001
            return {"state": "fault", "published": False, "lean": None,
                    "reason": f"FAULT {type(exc).__name__}: {exc}", "attempts": k}
        extra = r.extra or {}
        if not r.published:
            res = {"state": r.state, "published": False, "lean": None,
                   "reason": r.withheld_note() or r.reason,
                   "rejected_text": getattr(r, "rejected_text", None), "attempts": k}
            if r.state in ("call_failed", "unavailable", "prompt_too_large", "empty",
                           "too_long"):
                return res
            continue
        faults = (stack_prose.style_faults(r.text, cfg) + forecast_faults(r.text)
                  + ([f"lean: {extra.get('error')}"] if extra.get("lean") is None else []))
        if faults:
            res = {"state": "es_rules", "published": False, "lean": None,
                   "reason": "withheld: " + "; ".join(faults[:4]),
                   "retry_reason": "withheld: " + "; ".join(faults),
                   "rejected_text": r.text, "attempts": k}
            continue
        return {"state": "published", "published": True, "text": r.text,
                "lean": extra["lean"], "model": r.model, "attempts": k}
    return res


# ---------------------------------------------------------------------------
# The print
# ---------------------------------------------------------------------------
def _f(v: Any, dp: int = 2) -> str:
    if v is None:
        return "–"
    try:
        return f"{float(v):,.{dp}f}"
    except (TypeError, ValueError):
        return str(v)


def _signed(v: Any) -> str:
    return "–" if v is None else f"{float(v):+,.2f}"


def levels_table(block: dict) -> dict:
    """Above (far to near), the price now, below (near to far)."""
    lv = block.get("levels") or {}
    rows = [[r["label"], _f(r["price"]), _signed(r["distance"])]
            for r in reversed(lv.get("above") or [])]
    rows.append(["price now", _f(block.get("last")), "–"])
    rows += [[r["label"], _f(r["price"]), _signed(r["distance"])]
             for r in lv.get("below") or []]
    return {"columns": ["Level", "ES", "From here"], "rows": rows}


def _macd_cell(m: dict) -> str:
    if not m or m.get("absent"):
        return "–"
    h, hp = m.get("hist"), m.get("hist_prev")
    turn = "" if hp is None or h is None else (" rising" if h > hp else " falling")
    return f"{_signed(h)}{turn}"


def windows_table(block: dict) -> dict:
    names = {"session": "Session (5-min)", "swing": "Swing (5 sessions, 2-hour)",
             "position": "Position (3 months, daily)",
             "prior_session": "Prior full session"}
    rows = []
    for wid in ("session", "swing", "position", "prior_session"):
        w = (block.get("windows") or {}).get(wid)
        if w is None:
            continue
        if w.get("absent"):
            rows.append([names[wid], "absent", "–", "–", "–", "–"])
            continue
        p = w.get("profile") or {}
        va = ("–" if p.get("absent") or p.get("val") is None else
              f"{_f(p['val'])}–{_f(p['vah'])} ({_f(p.get('poc'))})")
        t = w.get("trend") or {}
        vt = (f"VWAP {_f(w['vwap'])}" if w.get("vwap") is not None else
              f"trend {_f(t.get('value'))}, {_signed(t.get('slope'))}/bar"
              if t.get("value") is not None else "–")
        if wid == "position" and w.get("n_sessions") is not None:
            names_pos = f"{names[wid]}, n={w['n_sessions']} of {w['sessions_wanted']}"
        else:
            names_pos = names[wid]
        rows.append([names_pos, _f(w.get("last")), vt, va, _macd_cell(w.get("macd")),
                     _f(w.get("money_flow"), 1)])
    return {"columns": ["Window", "Last", "VWAP / trend", "Value area (POC)",
                        "MACD hist", "Money flow"], "rows": rows}


def lines(block: dict) -> list[str]:
    """The code-written lines under the tables."""
    out = []
    c = block.get("contract") or {}
    if c:
        src = "Yahoo's report" if c.get("source") == "yahoo" else "CME's roll rule"
        roll = (c.get("roll_date") if c.get("in_force") == c.get("rule")
                else None)
        out.append(f"Contract in force {c.get('in_force')} ({src}); rolls to "
                   f"{c.get('next')} on {roll or 'the date Yahoo switches'}."
                   + ("" if c.get("agree", True) else
                      f" CME's rule says {c.get('rule')}: Yahoo's switch differs."))
    for wid, w in (block.get("windows") or {}).items():
        for r in (w or {}).get("rolls") or []:
            out.append(f"{wid.replace('_', ' ').capitalize()} window spans the "
                       f"{r['from']} to {r['to']} roll on {r['session']}: earlier bars "
                       + (f"shifted {_signed(r['gap'])}." if r.get("gap") is not None
                          else "not adjusted (" + str(r.get("note")) + ")."))
        if (w or {}).get("absent"):
            out.append(f"{wid.replace('_', ' ').capitalize()} window absent: {w['absent']}.")
    sm = block.get("since_morning")
    if sm:
        out.insert(0, f"Since 07:00: {_signed(sm['change'])} from {_f(sm['ref_price'])}; "
                   f"the morning's lean {sm['lean'] or 'not stated'}"
                   + (f", {sm['lean_so_far']} so far." if sm.get("lean_so_far") else "."))
    pos = (block.get("windows") or {}).get("position") or {}
    if (pos.get("profile") or {}).get("note"):
        out.append(f"Position value area {pos['profile']['note']}.")
    out.append(block.get("dealer") or es_block.DEALER_PENDING)
    return out


def subsection(block: dict, read: Optional[dict]) -> dict:
    """The close's Mechanics sub-section: the read first, then the tables."""
    r = read or {}
    lead = (r.get("text") if r.get("published") else
            f"The read was withheld: {r.get('reason')}" if r else None)
    data = {"es_block": payload(block), "lean": r.get("lean")}
    if block.get("state") == "absent":
        return {"title": TITLE, "lead": f"ES block absent: {block.get('reason')}",
                "lines": [block.get("dealer") or es_block.DEALER_PENDING],
                "paragraph_wanted": False, "data": data}
    tables = [windows_table(block)]
    sm = block.get("since_morning")
    if sm and sm.get("levels"):
        tables.append({"columns": ["The 07:00 levels", "ES", "So far"],
                       "rows": [[x["label"], _f(x["level"]), x["so_far"]]
                                for x in sm["levels"]]})
    return {"title": TITLE, "lead": lead, "table": levels_table(block),
            "tables": tables, "lines": lines(block),
            "paragraph_wanted": False, "data": data}


def html(block: dict, read: Optional[dict]) -> str:
    """The 07:00 anchor's section body (its heading is the anchor's)."""
    from . import stack_render                                  # noqa: PLC0415
    ss = subsection(block, read)
    out = []
    if ss.get("lead"):
        out.append(f'<p style="{stack_render.PARA}">{_html.escape(ss["lead"])}</p>')
    out.append(stack_render.tables_html(ss, True))
    for ln in ss.get("lines") or []:
        out.append(f'<p style="{stack_render.FOOT}">{_html.escape(ln)}</p>')
    return "".join(out)


def text_lines(block: dict, read: Optional[dict]) -> list[str]:
    ss = subsection(block, read)
    out = [TITLE]
    if ss.get("lead"):
        out.append(ss["lead"])
    for t in [ss.get("table")] + list(ss.get("tables") or []):
        for row in (t or {}).get("rows") or []:
            out.append("  " + " | ".join(str(c) for c in row))
    out += ss.get("lines") or []
    return out + [""]


def weekly_subsection(store, sessions: list[str], cutoff: str, conn=None) -> dict:
    """The Weekly's position panel and the week's ledger summary."""
    cfg = es_block.load_config()
    from altdata import volume_profile as vp                   # noqa: PLC0415
    day = sessions[-1]
    pos = es_block.position_window(store, day, cutoff, cfg, vp.load_config(),
                                   vp.complete_share(), conn or getattr(store, "conn", None))
    blk = {"windows": {"position": pos}}
    wt = windows_table(blk)
    summ = es_block.ledger_summary(conn or store.conn, sessions)
    lv, ln = summ["levels"], summ["leans"]
    led = {"columns": ["The week's ES ledger", "Count"],
           "rows": [["levels held", lv.get("held", 0)], ["levels broke", lv.get("broke", 0)],
                    ["levels untested", lv.get("untested", 0)],
                    ["leans resolved", ln.get("resolved", 0)],
                    ["leans unresolved", ln.get("unresolved", 0)],
                    ["leans none or not scored", ln.get("not_scored", 0)],
                    ["pending", lv.get("pending", 0) + ln.get("pending", 0)]]}
    out_lines = []
    if pos.get("absent"):
        out_lines.append(f"Position window absent: {pos['absent']}.")
    elif (pos.get("profile") or {}).get("note"):
        out_lines.append(f"Position value area {pos['profile']['note']}.")
    out_lines.append(f"{summ['n_prints']} block(s) printed this week; each level and "
                     "lean is scored on the next session by config/es_block.yaml's rules.")
    return {"title": "ES — the position panel and the week's ledger",
            "table": wt, "tables": [led], "lines": out_lines,
            "paragraph_wanted": False,
            "data": {"es_position": pos, "es_ledger_week": summ}}
