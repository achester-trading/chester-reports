"""
B59 laid out: D15's one-day 10-year trigger and D26's three new sources (rulings
of 24 Oct 2026; b59-trigger-sources). The figures are altdata/oneday_10y.py's,
altdata/sources/gdelt.py's, altdata/sources/cpc_degree_days.py's and
altdata/sources/hf_releases.py's; this module computes nothing.

  THE CLOSE     Mechanics, the event area beside item 52's, item 65's and item
                73's events: D15's flag line on a trigger day (a line only); the
                event is kept in the section's data for the close to store.
  WEEKLY AND MONTHLY  Mechanics: D15's block over the edition's sessions, after
                the events; the degree days beside natural gas, after the
                oil-shock signature.
  THE WEEKLY    Narratives: GDELT's articles per story and the model-release
                line; Ahead (the tail register): GDELT's geopolitical line.
  THE MONTHLY   Narratives: GDELT's articles per story; Slow layers, after the
                Factor lines: Factor III's GDELT lines and Factor I-b's
                model-release block.

Tables and code-written lines only: no paragraph is asked for, so no prose word is
added to any budget. A builder that faults is logged and prints nothing. Report
only: nothing here enters a composite or the market-state object.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Optional

log = logging.getLogger(__name__)

ONEDAY_CLOSE_TITLE = "10-year one-day move"
GDELT_FACTOR_TITLE = "Factor III: geopolitical attention (GDELT)"
GDELT_STORIES_TITLE = "Attention by story (GDELT's event files)"


def _safe(fn: Callable, what: str, default: Any = None) -> Any:
    try:
        return fn()
    except Exception:                                           # noqa: BLE001
        log.warning("%s faulted", what, exc_info=True)
        return default


def _item(key: str, text: str, priority: int, value: Any = None) -> dict:
    from . import stack                                         # noqa: PLC0415
    return stack.item(key, text, priority, value)


# ---------------------------------------------------------------------------
# D15: the close's flag line, the ledger row, the Weekly's and Monthly's block
# ---------------------------------------------------------------------------
def close_extras(built: dict, st, day: str, cutoff: str) -> None:
    from altdata import oneday_10y                              # noqa: PLC0415
    from . import batch15_a_block                               # noqa: PLC0415
    mech = built.get("mechanics")
    if mech is None:
        return
    ev = _safe(lambda: oneday_10y.for_session(st, day, cutoff), "the one-day trigger")
    line = oneday_10y.flag_line(ev) if ev else None
    if not line:
        return
    mech.setdefault("data", {})["_oneday_event"] = ev
    subs = mech.setdefault("subsections", [])
    subs.insert(batch15_a_block._after_events(subs),           # noqa: SLF001
                {"title": ONEDAY_CLOSE_TITLE, "paragraph_wanted": False, "lines": [line]})
    mech["items"].append(_item("mech:oneday_10y", line, 1, line))


def store_rows(mech_data: dict, now: str) -> list[dict]:
    """The ledger row for the close to write on a trigger day (never on a dry run)."""
    from altdata import oneday_10y                              # noqa: PLC0415
    ev = mech_data.pop("_oneday_event", None)
    return [oneday_10y.ledger_row(ev, now)] if ev and ev.get("fired") else []


def mechanics_subsections(subs: list[dict], st, cutoff: str, first: str, last: str
                          ) -> list[dict]:
    """D15's block after the event blocks; the degree days after the oil-shock
    signature (else at the end)."""
    from altdata import oneday_10y                              # noqa: PLC0415
    from . import batch15_a_block, t1_rest_block                # noqa: PLC0415
    out = list(subs)
    od = _safe(lambda: oneday_10y.block(st, cutoff, first, last), "the one-day block")
    if od:
        titles = (batch15_a_block.EVENT_TITLES
                  + (batch15_a_block.GOLD_TITLE, batch15_a_block.DM_TITLE))
        at = [i for i, x in enumerate(out) if x.get("title") in titles]
        out.insert(at[-1] + 1 if at else len(out), od)
    dd = energy_subsection(st, cutoff)
    if dd:
        at = next((i for i, x in enumerate(out) if x.get("title") == t1_rest_block.OIL_TITLE),
                  None)
        out.insert(len(out) if at is None else at + 1, dd)
    return out


# ---------------------------------------------------------------------------
# D26: the three readers
# ---------------------------------------------------------------------------
def energy_subsection(st, cutoff: str) -> Optional[dict]:
    from altdata.sources import cpc_degree_days as cpc          # noqa: PLC0415
    r = _safe(lambda: cpc.read(st, cutoff), "the degree days")
    if r is None:
        return None
    return {"title": cpc.TITLE, "paragraph_wanted": False, "lines": cpc.lines(r)}


def _gdelt(st, cutoff: str) -> Optional[dict]:
    from altdata.sources import gdelt                           # noqa: PLC0415
    return _safe(lambda: gdelt.read(st, cutoff), "the GDELT read")


def stories_subsection(st, cutoff: str, r: Optional[dict] = None) -> Optional[dict]:
    """GDELT's articles per story, beside the narrative register."""
    from altdata.sources import gdelt                           # noqa: PLC0415
    r = r if r is not None else _gdelt(st, cutoff)
    if r is None:
        return None
    if r.get("state") != "computed":
        return {"title": GDELT_STORIES_TITLE, "paragraph_wanted": False,
                "lines": ["Articles per story: not read (gdelt.narrative_mentions; the "
                          "first daily pull has not run)."]}
    return {"title": GDELT_STORIES_TITLE, "paragraph_wanted": False,
            "table": gdelt.narrative_table(r),
            "lines": ["Distinct articles a day whose address carries one of the story's "
                      "declared phrases (config/gdelt.yaml), from GDELT's event files; "
                      "attention, not agreement. Report only (D26)."]}


def factor_iii_subsection(st, cutoff: str, r: Optional[dict] = None) -> Optional[dict]:
    from altdata.sources import gdelt                           # noqa: PLC0415
    r = r if r is not None else _gdelt(st, cutoff)
    if r is None:
        return None
    return {"title": GDELT_FACTOR_TITLE, "paragraph_wanted": False,
            "lines": gdelt.factor_lines(r)}


def tail_subsection(st, cutoff: str) -> Optional[dict]:
    """The Weekly's tail register: GDELT's geopolitical line."""
    from altdata.sources import gdelt                           # noqa: PLC0415
    r = _gdelt(st, cutoff)
    if r is None:
        return None
    return {"title": "Tail register: geopolitical attention", "paragraph_wanted": False,
            "lines": [gdelt.tail_line(r)]}


def releases_line(st, cutoff: str) -> Optional[str]:
    from altdata.sources import hf_releases as hf               # noqa: PLC0415
    r = _safe(lambda: hf.read(st, cutoff), "the model-release read")
    return hf.weekly_line(r) if r is not None else None


def releases_subsection(st, cutoff: str) -> Optional[dict]:
    from altdata.sources import hf_releases as hf               # noqa: PLC0415
    r = _safe(lambda: hf.read(st, cutoff), "the model-release read")
    return hf.factor_block(r) if r is not None else None


def weekly_narratives(sec: dict, st, cutoff: str) -> None:
    """The Weekly's narratives section: the stories' GDELT counts and the AI line."""
    subs = sec.setdefault("subsections", [])
    s = stories_subsection(st, cutoff)
    if s:
        subs.append(s)
    ln = releases_line(st, cutoff)
    if ln:
        subs.append({"title": "AI: open model releases", "paragraph_wanted": False,
                     "lines": [ln]})


def monthly_narratives(sec: dict, st, cutoff: str) -> None:
    s = stories_subsection(st, cutoff)
    if s:
        sec.setdefault("subsections", []).append(s)


def place_slow(subs: list[dict], st, cutoff: str) -> list[dict]:
    """Factor III's GDELT lines and Factor I-b's block right after the Factor
    lines (else at the end)."""
    from . import absorption_block                              # noqa: PLC0415
    add = [x for x in (factor_iii_subsection(st, cutoff), releases_subsection(st, cutoff))
           if x]
    if not add:
        return subs
    out = list(subs)
    at = next((i for i, x in enumerate(out)
               if x.get("title") == absorption_block.FACTOR_TITLE), None)
    at = len(out) if at is None else at + 1
    return out[:at] + add + out[at:]
