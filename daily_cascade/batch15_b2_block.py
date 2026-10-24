"""
Signal-triage Batch 15, session B's items (b56): where items 74, 77 and 78 print.
Item 75's lines ride the Monthly's Factor I lines (absorption_block.ai_lab_lines).

    positioning_subsection(st, now)    the Weekly's Positioning & flows: the hedge-
                                       fund positioning table, its gap lines and
                                       the squeeze-risk flag (item 74)
    es_squeeze_line(st, day, cutoff)   item 45's levels read on the close: one
                                       context line (item 74)
    cyber_subsection(st, now)          the Weekly's Ahead: the tail register's
                                       cyber-pressure line (item 77)
    incidents_note(st, now)            the Digital Assets addendum's incidents
                                       section: the cyber cross-reference and the
                                       active-protocol count (items 77 and 78)
    protocol_subsection(st, now)       the Monthly's digital chapter: the count and
                                       its listed gap (item 78)

Report only. Tables and code-written lines: no paragraph, no chart. Each read is
wrapped: a fault costs its own line, never the section.
"""

from __future__ import annotations

import logging
from typing import Optional

log = logging.getLogger(__name__)

HF_NOTE = ("CFTC Traders in Financial Futures, futures only, leveraged funds (net "
           "= long less short, contracts; the share is of the contract's open "
           "interest), weekly, the report Tuesday, released the Friday after. The "
           "percentile is of the net SHORT share: higher is more short. The squeeze "
           "flag pairs ES's with item 71's depth stand-in. Report only.")


def _safe(fn, what: str):
    try:
        return fn()
    except Exception:                                           # noqa: BLE001
        log.warning("%s faulted", what, exc_info=True)
        return None


def _depth(st, cutoff: str) -> Optional[dict]:
    """Item 71's depth read on the latest stored SPY session (a57's module)."""
    from altdata import fragility                               # noqa: PLC0415
    from altdata import st_r5_rates as rt                       # noqa: PLC0415
    spy = rt._pts(st, fragility.config()["spy"]["close"], cutoff)  # noqa: SLF001
    if not spy:
        return None
    return fragility.build(st, spy[-1][0], cutoff)["depth"]


def positioning_subsection(st, now: str) -> Optional[dict]:
    from altdata import hf_positioning as hf                    # noqa: PLC0415
    r = _safe(lambda: hf.read(st, now), "the hedge-fund positioning read")
    if not r:
        return None
    depth = _safe(lambda: _depth(st, now), "the depth read")
    f = hf.squeeze(r, depth)
    cfg = hf.config()
    return {"title": cfg.get("title") or "Hedge-fund positioning",
            "table": hf.table(r), "lines": hf.lines(r) + [f["line"]],
            "paragraph_wanted": False, "table_note": HF_NOTE,
            "data": {"hf_positioning": {"squeeze": f["state"],
                                        "as_of": [c.get("as_of") for c in r["contracts"]]}}}


def es_squeeze_line(st, day: str, cutoff: str) -> Optional[str]:
    """Item 45's levels read: the squeeze-risk context line, or None unread."""
    from altdata import hf_positioning as hf                    # noqa: PLC0415
    from altdata import fragility                               # noqa: PLC0415
    r = _safe(lambda: hf.read(st, cutoff), "the hedge-fund positioning read")
    if not r:
        return None
    depth = _safe(lambda: fragility.build(st, day, cutoff)["depth"], "the depth read")
    f = hf.squeeze(r, depth)
    return None if f["state"] == "not read" else hf.es_line(f)


def cyber_subsection(st, now: str) -> Optional[dict]:
    from altdata import cyber_pressure as cp                    # noqa: PLC0415
    r = _safe(lambda: cp.read(st, now), "the cyber-pressure read")
    if not r:
        return None
    cfg = cp.config()
    return {"title": cfg.get("title") or "Tail register: cyber pressure",
            "lines": cp.lines(r), "paragraph_wanted": False,
            "table_note": ("CISA's Known Exploited Vulnerabilities catalogue (entries "
                           "added in the week) and NVD's CVE API (CVEs published in "
                           "the week with a CVSS v3 score of 9.0 or higher), each "
                           "with its percentile over five years and the stored "
                           "history. A background-load measure for scenario 13 and "
                           "item 16, never a tripwire: scenario 13 keeps its "
                           "documented no-tripwire ruling."),
            "data": {"cyber_pressure": {"flag": r["flag"]["state"]}}}


def incidents_body(st, now: str) -> dict:
    """Items 77 and 78 in the addendum's incidents section (section 7), each with
    its full read and its table (D19/D20, 24 Oct 2026: the 52-line cap that kept
    them to one footnote line is retired). {tables, lines, data}."""
    from altdata import cyber_pressure as cp                    # noqa: PLC0415
    from altdata import protocol_breadth as pb                  # noqa: PLC0415
    tables, lines, data = [], [], {}
    c = _safe(lambda: cp.read(st, now), "the cyber-pressure read")
    if c:
        rows = []
        for lab, x in (("CISA known exploited vulnerabilities added", c["kev"]),
                       ("NVD critical CVEs published", c["nvd"])):
            rows.append([lab, x.get("week") or "—",
                         "—" if x.get("count") is None else f"{x['count']:,}",
                         x.get("lens_text") or "not read"])
        tables.append({"title": "Cyber pressure (item 77)",
                       "columns": ["Feed", "Week of", "Count", "Percentile"], "rows": rows})
        lines += cp.lines(c)
        data["cyber_flag"] = c["flag"]["state"]
    else:
        lines.append("Cyber pressure (item 77): not read.")
    p = _safe(lambda: pb.read(st, now), "the protocol count")
    if p and p.get("state") == "computed":
        tables.append({"title": "Protocol breadth (item 78)",
                       "columns": ["Day", "Active (TVL above zero)", "Listed, not dead",
                                   "30 days", "History from"],
                       "rows": [[p["day"], f"{p['active']:,}",
                                 "—" if p["listed"] is None else f"{p['listed']:,}",
                                 "—" if p["change_30d"] is None else f"{p['change_30d']:+,}",
                                 f"{p['start']} ({p['days']} snapshots)"]]})
    lines += [pb.line(p or {}), pb.HAND_COUNT_GAP + "."]
    data["protocols"] = (p or {}).get("state")
    return {"tables": tables, "lines": lines, "data": data}


def protocol_subsection(st, now: str) -> Optional[dict]:
    from altdata import protocol_breadth as pb                  # noqa: PLC0415
    r = _safe(lambda: pb.read(st, now), "the protocol count")
    if r is None:
        return None
    return {"title": "Digital assets: protocol breadth",
            "lines": [pb.line(r), pb.HAND_COUNT_GAP + "."],
            "paragraph_wanted": False,
            "table_note": ("DefiLlama's open API (api.llama.fi/protocols), read daily "
                           "in the crypto basket's run. The base rate against the "
                           "2018-19 and 2022-23 winters is a cited note, the crypto "
                           "winters base-rate note. Report only."),
            "data": {"protocol_breadth": r}}
