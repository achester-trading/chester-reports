"""
THE "WHAT TO SEE" LINE (W10-2; D46 decision 3, 31 Oct 2026).

Every chart the Weekly and the Monthly draw carries one line beneath it, "What
to see: ...": the observation the eye should find in the figure this week,
never a conclusion and never a recommendation.

  - ITS DATA BLOCK. A line reads only its chart's own data: the series, the
    window and the last values, derived here from what the chart returned (its
    `series`, its `stats`, or W3's `levels`). A chart that returned none of them
    has no block and carries no line.
  - ITS CALL. Both editions write their sections' prose before they draw their
    charts, so the section's prose call cannot see a chart. The lines come from
    one call per section after the drawing, fed only that section's charts'
    blocks (metered as `see:<section>`). The section's own prose is untouched.
  - ITS CHECKS, in order: at most 30 words (refused before the audit); none of
    the house's action words (buy, sell, long, short, add, trim); then the
    numeral audit against its own chart's block alone. A line that fails is
    revised once, told its reason; a second failure withholds it, and the chart
    prints without it.

The line is a reading aid, not a measure: no figure is computed here.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Optional

log = logging.getLogger(__name__)

CAP_WORDS = 30
PREFIX = "What to see: "
# The house rule: an observation, never a recommendation.
ACTION = re.compile(r"\b(?:buy|buys|buying|sell|sells|selling|long|longs|short|shorts|"
                    r"add|adds|adding|trim|trims|trimming)\b", re.I)
_LINE = re.compile(r"^\s*([A-Z]\d{1,2}):\s*(?:what to see:\s*)?(.+?)\s*$", re.I)

SYSTEM = (
    "You write one line beneath each chart of a market report: what the reader's "
    "eye should find in that chart this period. For each chart in the data, write "
    "exactly one line, \"<chart id>: <the observation>\", one line per chart, in "
    "the order given, nothing else. Each line is at most 30 words. Use only "
    "figures from that chart's own data block, copied as given; a line needs no "
    "figure at all. Say what the figure shows (where a series ends against its "
    "range, which line moved most, where two lines cross); never why, never what "
    "it means for policy or positioning, and never an action: no buy, sell, long, "
    "short, add or trim. No markdown.")

REVISE = ("\n\nTHESE LINES FAILED THEIR CHECK. Rewrite only them, one line each, "
          "\"<chart id>: <the observation>\", fixing exactly the fault named and "
          "using only that chart's data block:\n")


def _r(v: Any) -> Any:
    return round(float(v), 2) if isinstance(v, (int, float)) else v


def data_block(chart: Optional[dict]) -> Optional[dict]:
    """The chart's own data block, or None when it carries no data the line could
    read (or was not drawn)."""
    if not chart or chart.get("unavailable"):
        return None
    s = chart.get("series")
    rows: list[dict] = []
    if isinstance(s, dict):                          # label -> [{date, value}]
        for lab, pts in s.items():
            pts = [p for p in pts or [] if isinstance(p, dict) and p.get("value") is not None]
            if pts:
                vals = [float(p["value"]) for p in pts]
                rows.append({"series": lab, "from": str(pts[0]["date"])[:10],
                             "to": str(pts[-1]["date"])[:10], "first": _r(vals[0]),
                             "last": _r(vals[-1]), "change": _r(vals[-1] - vals[0]),
                             "high": _r(max(vals)), "low": _r(min(vals)),
                             "points": len(vals)})
    elif isinstance(s, list) and s and isinstance(s[0], dict) and "close" in s[0]:
        closes = [float(b["close"]) for b in s if b.get("close") is not None]
        if closes:
            rows.append({"series": "close", "from": str(s[0].get("observed_at"))[:10],
                         "to": str(s[-1].get("observed_at"))[:10], "first": _r(closes[0]),
                         "last": _r(closes[-1]), "change": _r(closes[-1] - closes[0]),
                         "high": _r(max(float(b["high"]) for b in s)),
                         "low": _r(min(float(b["low"]) for b in s)), "bars": len(s)})
    elif isinstance(s, list) and s and isinstance(s[0], dict) and "return_pct" in s[0]:
        rows = [{"series": r["name"], "return_pct": _r(r["return_pct"])} for r in s]
    elif isinstance(chart.get("stats"), dict):
        rows = [{"series": k, **{kk: _r(vv) for kk, vv in (v or {}).items()
                                 if isinstance(vv, (int, float, str))}}
                for k, v in chart["stats"].items()]
    elif isinstance(chart.get("levels"), list):
        rows = [{"series": x.get("series"), "last": _r(x.get("value")),
                 "as_of": x.get("as_of")} for x in chart["levels"]]
    if not rows:
        return None
    return {"chart": chart.get("id"), "title": (chart.get("titles") or [None])[0]
            or chart.get("title"), "series": rows}


def check_line(text: str, block: dict) -> tuple[bool, str, bool]:
    """(ok, reason, audited): the length first (refused before the audit), then
    the action words, then the numeral audit against the chart's block alone."""
    n = len(str(text or "").split())
    if n == 0:
        return False, "empty", False
    if n > CAP_WORDS:
        return False, f"{n} words; the cap is {CAP_WORDS}", False
    act = sorted({m.group(0).lower() for m in ACTION.finditer(text)})
    if act:
        return False, f"an action word ({', '.join(act)}): observation only", False
    from altdata import numeral_audit                           # noqa: PLC0415
    res = numeral_audit.audit(text, block)
    return (bool(res.passed), "" if res.passed else res.reason(), True)


def parse(reply: Optional[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for ln in str(reply or "").splitlines():
        m = _LINE.match(ln)
        if m and m.group(1).upper() not in out:
            out[m.group(1).upper()] = m.group(2).strip()
    return out


def _call(payload: dict, system: str, *, section: str, model=None, client=None) -> str:
    """One model call through the narrative step; its text, rejected or not (the
    lines are checked one by one below, each against its own block)."""
    from . import narrative                                     # noqa: PLC0415
    from altdata import model_meter                             # noqa: PLC0415
    with model_meter.scope(section=f"see:{section}"):
        r = narrative.generate(payload, model=model, client=client, system_prompt=system,
                               max_chars=4000, one_paragraph=False)
    return r.text or getattr(r, "rejected_text", None) or ""


def write_section(section: str, charts: dict, ids: list, *, model=None,
                  client=None, call=None) -> dict:
    """{chart id: {"see": line} or {"see_withheld": reason}} for the section's
    charts that carry a block. `call(payload, system) -> reply` stands in for the
    model in the gates."""
    blocks = {c: data_block(charts.get(c)) for c in ids}
    blocks = {c: b for c, b in blocks.items() if b}
    if not blocks:
        return {}
    call = call or (lambda pl, sy: _call(pl, sy, section=section, model=model,
                                         client=client))
    payload = {"charts": [{"id": c, **b} for c, b in blocks.items()]}
    try:
        got = parse(call(payload, SYSTEM))
    except Exception as exc:                                    # noqa: BLE001
        log.warning("what-to-see: %s faulted: %s", section, exc)
        return {}
    out, failed = {}, {}
    for c, b in blocks.items():
        line = got.get(c.upper())
        ok, why, _ = check_line(line, b) if line else (False, "no line written", False)
        (out.__setitem__(c, {"see": line}) if ok else failed.__setitem__(c, why))
    if failed:
        note = REVISE + "\n".join(f"- {c}: {got.get(c.upper()) or '(none)'} -- {why}"
                                  for c, why in failed.items())
        try:
            again = parse(call({"charts": [{"id": c, **blocks[c]} for c in failed]},
                               SYSTEM + note))
        except Exception:                                       # noqa: BLE001
            again = {}
        for c, why in failed.items():
            line = again.get(c.upper())
            ok, why2, _ = check_line(line, blocks[c]) if line else (False, why, False)
            if ok:
                out[c] = {"see": line}
            else:
                out[c] = {"see_withheld": why2 or why}
                log.warning("what-to-see: %s/%s withheld: %s", section, c, why2 or why)
    return out


def chart_ids(s: dict) -> list:
    ids = list(s.get("charts_rendered") or [])
    for ss in s.get("subsections") or []:
        if isinstance(ss, dict):
            ids += list(ss.get("charts_rendered") or [])
    return ids


def write(ed: dict, charts: dict, *, model=None, client=None, call=None) -> int:
    """Each section's charts' lines onto the charts (`see` or `see_withheld`);
    the number of lines written. Never raises."""
    n = 0
    for s in ed.get("sections") or []:
        ids = [c for c in chart_ids(s) if c in (charts or {})]
        if not ids:
            continue
        try:
            got = write_section(str(s.get("id")), charts, ids, model=model,
                                client=client, call=call)
        except Exception:                                       # noqa: BLE001
            log.warning("what-to-see: %s faulted", s.get("id"), exc_info=True)
            continue
        for c, v in got.items():
            charts[c].update(v)
            n += 1 if v.get("see") else 0
    return n
