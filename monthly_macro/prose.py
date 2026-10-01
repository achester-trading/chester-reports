"""
Monthly v2: the prose, one audited model call per section. (Ari's revision, 1 Oct)

    The month in markets          3-4 paragraphs on what drove the month
    Looking back, one per theme   2-4 paragraphs each, six themes
    Looking ahead                 2-4 paragraphs
    Where our read lands          2-3 paragraphs, bounded to weights and books

WHY ONE CALL PER SECTION. The single paragraph over the whole payload read as a
summary of a summary: too abridged, insight hard to find, no account of where the
market went. A section's call sees ONLY that section's slice -- the opening sees
the scorecard and what changed; a theme sees its own items, its dimensions and its
scorecard rows -- so the model writes about the thing in front of it, at the length
it needs, and a failure costs that section alone.

THE AUDITS ARE THE CLOSE REPORT'S, per section. Every call goes through
daily_cascade.narrative.generate(): print precision, the precomputed percentile
ordinals, the numeral and label audit against THAT SECTION'S slice, the state audit
against the object, markdown refused. A section that fails is WITHHELD WITH ITS
REASON; the sections beside it publish.

THE SHAPE IS INSTITUTIONAL DESK COMMENTARY, insight first: each paragraph opens
with the claim, gives the evidence with numbers, and ends with what it implies for
positioning -- stated as what the evidence favours or argues against, never as an
instruction. The style reference is docs/briefs/monthly-style-reference.md when it
exists; until then the Monthly template carries the rules.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Callable, Optional

from .narrative import TEMPLATE_PATH

log = logging.getLogger("monthly_macro.prose")

REPO = Path(__file__).resolve().parent.parent
STYLE_REFERENCE = REPO / "docs" / "briefs" / "monthly-style-reference.md"

# 2-4 paragraphs of desk commentary run 250-600 words; this is the runaway guard,
# not a target. The opening asks for 3-4.
SECTION_MAX_CHARS = 5200

SECTION_RULES = """

THIS OVERRIDES THE ONE-PARAGRAPH, CLOSE-REPORT FRAMING ABOVE. You are writing ONE \
SECTION of the Monthly Regime & Allocation report, in the register of institutional \
desk commentary: a senior strategist's monthly note to a portfolio manager. Every \
other rule above -- every figure from the payload, signs as numerals, percentiles \
copied from their _ordinal field, no recommendation -- still holds.

THE SECTION: {title}. {scope}

SHAPE. Write {paragraphs} paragraphs of continuous prose, separated by one blank \
line. No headings, no bullet points, no numbered lists, no bold, no tables -- the \
tables are printed beside your text. Each paragraph is INSIGHT FIRST:
  1. open with the claim -- the one thing this paragraph says about the month;
  2. give the evidence, with the numbers from the payload that carry it;
  3. end with the implication for positioning: what the evidence favours, what it \
argues against, which risk it raises or lowers. State it as an observation about \
exposures, NEVER as an instruction -- buy, sell, add, trim, hold, overweight, \
underweight and their synonyms remain forbidden.

THE HORIZON IS THE MONTH named in the payload. The regime is the object's: name \
what the dials and dimensions read, never infer a regime of your own. Say plainly \
where the payload says something is not sourced; do not fill a gap with knowledge \
from outside the payload. Do not cite event, claim or row ids.

DO NO ARITHMETIC OF YOUR OWN. Quote each move exactly as the payload gives it. \
Never compute a difference, a spread between two moves, a ratio, a sum or a \
relative performance ("the Russell lagged by 4.36%") -- that number is in no \
field, and one such figure withholds the whole section. Say "lagged" and give \
both moves instead.
"""


def _style_guide() -> Path:
    return STYLE_REFERENCE if STYLE_REFERENCE.exists() else TEMPLATE_PATH


def system_prompt(title: str, scope: str, paragraphs: str = "2 to 4") -> str:
    from daily_cascade import narrative as base
    return base.SYSTEM_PROMPT + SECTION_RULES.format(
        title=title, scope=scope, paragraphs=paragraphs)


# ---------------------------------------------------------------------------
# The slices -- each section sees its own data and nothing else
# ---------------------------------------------------------------------------
def _dims(p: dict, names: Optional[list] = None) -> list[dict]:
    return [{k: d.get(k) for k in ("dimension", "state", "previous_state",
                                   "changed", "percentile", "direction",
                                   "absent_reason")}
            for d in ((p.get("regime") or {}).get("dimensions") or [])
            if names is None or d.get("dimension") in names]


def _dials(p: dict) -> list[dict]:
    return [{k: d.get(k) for k in ("dial", "state", "previous_state", "changed",
                                   "absent_reason")}
            for d in ((p.get("regime") or {}).get("dials") or [])]


def _scorecard(p: dict, ids: Optional[list] = None) -> dict:
    m = p.get("month_in_markets") or {}
    return {"month": m.get("month"), "from": m.get("start"), "to": m.get("end"),
            "moves": [{k: r.get(k) for k in ("label", "start_level", "end_level",
                                             "change", "change_unit", "percentile")}
                      for r in m.get("rows") or []
                      if ids is None or r.get("id") in ids],
            "not_sourced": m.get("missing") or []}


def _changed(p: dict, words: Optional[list] = None) -> list[dict]:
    rows = ((p.get("looking_back") or {}).get("what_changed") or {}).get("rows") or []
    return [{k: r.get(k) for k in ("what", "from", "to")} for r in rows
            if words is None or any(w in r.get("what", "") for w in words)]


def opening_slice(p: dict) -> dict:
    lb = p.get("looking_back") or {}
    releases = [{"theme": t["name"], "release": i["text"],
                 "date": (i.get("sources") or [{}])[0].get("date")}
                for t in lb.get("themes") or [] for i in t.get("items") or []
                if i.get("kind") == "release"]
    return {"scorecard": _scorecard(p), "dials": _dials(p),
            "dimensions": _dims(p),
            "exceptions_opened": (p.get("regime") or {}).get("exceptions_opened"),
            "what_changed": _changed(p), "releases_this_month": releases,
            "stories": [{"story": i.get("story"), "state": i.get("state"),
                         "headline_count": i.get("headlines_in_window"),
                         "tier12_headline_count": i.get("tier12_in_window")}
                        for t in lb.get("themes") or [] for i in t.get("items") or []
                        if i.get("kind") == "story"]}


def theme_slice(p: dict, theme: dict) -> dict:
    from . import v2
    cfg = (v2.load_themes().get("themes") or {}).get(theme["theme"]) or {}
    return {"theme": theme["name"], "month": (p.get("month_in_markets") or {})
            .get("month"),
            "dimensions": _dims(p, theme.get("dimensions") or []),
            "no_dimension_why": theme.get("no_dimension_why"),
            "items": [{"tag": i.get("tag"), "item": i.get("text"),
                       "date": (i.get("sources") or [{}])[0].get("date"),
                       "corrects": (i.get("corrects") or {}).get("statement"),
                       "tier12_headline_count": i.get("tier12_in_window")}
                      for i in theme.get("items") or []],
            "held": theme.get("held") or [],
            "scorecard": _scorecard(p, cfg.get("scorecard")),
            "what_changed": _changed(p, (theme.get("dimensions") or [])
                                     + (theme.get("stories") or []))}


def ahead_slice(p: dict) -> dict:
    la = p.get("looking_ahead") or {}
    return {"horizon": la.get("horizon"),
            "calendar": [{"date": c["date"], "event": c["title"]}
                         for c in la.get("calendar") or []],
            "calendar_stored_through": la.get("calendar_reach"),
            "scenarios": [{"claim": s.get("claim"),
                           "probability": s.get("probability"),
                           "brier": s.get("brier"), "resolves": s.get("resolve_by"),
                           "would_change_our_mind": [sp.get("observable")
                                                     for sp in s.get("signposts")
                                                     or []]}
                          for s in la.get("scenarios") or []],
            "dials": _dials(p)}


def our_read_slice(p: dict) -> dict:
    r = p.get("our_read") or {}
    la = p.get("looking_ahead") or {}
    return {"bounded_statement": r.get("paragraph"),
            "live_weights": [{"claim": s.get("claim"),
                              "probability": s.get("probability"),
                              "resolves": s.get("resolve_by")}
                             for s in la.get("scenarios") or []],
            "active_decisions": r.get("active_decisions"),
            "books_vs_benchmark": ((p.get("register_month") or {})
                                   .get("books_vs_benchmark") or {}).get("line"),
            "dials": _dials(p)}


def plan(p: dict) -> list[dict]:
    """Every section's call: its key, title, scope, paragraph count and slice."""
    out = [{"key": "month_in_markets", "title": "The month in markets",
            "scope": "What drove the month across asset classes: lead with the "
                     "biggest moves on the scorecard and what explains them, then "
                     "what the regime and the month's releases add.",
            "paragraphs": "3 to 4", "slice": opening_slice(p)}]
    for t in ((p.get("looking_back") or {}).get("themes") or []):
        out.append({"key": f"theme:{t['theme']}", "title": t["name"],
                    "scope": "This theme over the month: what its dimensions, "
                             "stories and releases say, and the moves on its "
                             "scorecard rows.",
                    "paragraphs": "2 to 4", "slice": theme_slice(p, t)})
    out.append({"key": "looking_ahead", "title": "Looking ahead, 2-3 months",
                "scope": "What the calendar tests next and what the scenario "
                         "weights say, with what would change our mind for each.",
                "paragraphs": "2 to 4", "slice": ahead_slice(p)})
    out.append({"key": "our_read", "title": "Where our read lands",
                "scope": "Our position against consensus, stated ONLY through the "
                         "scenario weights and the books in the payload. Restate "
                         "nothing they do not already hold; if they hold little, "
                         "say so.",
                "paragraphs": "2 to 3", "slice": our_read_slice(p)})
    return out


def _market_states(p: dict) -> Optional[dict]:
    """The object's states, for the state audit. None if unreadable."""
    try:
        import regime
        from daily_cascade import story_block
        obj = regime.latest(session_day=(p.get("regime") or {}).get("session"))
        return story_block.market_states(obj) if obj else None
    except Exception:                                          # noqa: BLE001
        return None


# NO BULLET FRAGMENTS IN A NARRATIVE SECTION. The brief asks for prose; a reply
# that lists is withheld like any other failed audit rather than re-flowed.
_LIST_LINE = re.compile(r"^\s*(?:[-*•–]\s|\d+[.)]\s|#+\s)", re.M)


def list_lines(text: Optional[str]) -> list[str]:
    return [m.group(0).strip() for m in _LIST_LINE.finditer(text or "")]


def words(text: Optional[str]) -> int:
    return len(re.findall(r"\b[\w'.%$-]+\b", text or ""))


def write_all(p: dict, *, model: Optional[str] = None, client=None,
              only: Optional[Callable[[dict], bool]] = None) -> dict:
    """{section key: result}, one audited call each. Never raises."""
    from daily_cascade import narrative as base
    states = _market_states(p)
    out: dict[str, dict] = {}
    for sec in plan(p):
        if only and not only(sec):
            continue
        try:
            r = base.generate(sec["slice"], model=model, client=client,
                              system_prompt=system_prompt(sec["title"], sec["scope"],
                                                          sec["paragraphs"]),
                              guide_path=_style_guide(),
                              max_chars=SECTION_MAX_CHARS, one_paragraph=False,
                              citable_ids=[], market_states=states)
            published, state = bool(r.published), r.state
            reason = None if published else (r.withheld_note() or r.reason)
            lists = list_lines(r.text) if published else []
            if lists:
                published, state = False, "list_fragments"
                reason = (f"narrative withheld: the section came back as list "
                          f"fragments ({len(lists)} list line(s)), and a narrative "
                          f"section is prose")
            out[sec["key"]] = {
                "title": sec["title"], "state": state, "published": published,
                "text": r.text if published else None, "reason": reason,
                "words": words(r.text) if published else 0,
                # Kept for inspection, never printed: the operator can see what a
                # withheld section said and why the audit stopped it.
                "rejected_text": None if published else (
                    getattr(r, "rejected_text", None) or r.text),
                "model": r.model,
                "figures_checked": getattr(r, "figures_checked", None)}
        except Exception as exc:                               # noqa: BLE001
            out[sec["key"]] = {"title": sec["title"], "state": "fault",
                               "published": False, "text": None, "words": 0,
                               "reason": f"FAULT (code, not data) -- "
                                         f"{type(exc).__name__}: {exc}"}
        log.info("section %s: %s (%s words)", sec["key"], out[sec["key"]]["state"],
                 out[sec["key"]]["words"])
    return out
